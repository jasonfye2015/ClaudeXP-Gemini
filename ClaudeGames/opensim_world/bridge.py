"""The bridge between the Furry Hollow's regions and the Timeline: a small web server on 127.0.0.1 that every region's
Hollow Keeper (the script in it) polls every few seconds.

    GET  /poll?region=..&here=1&x=..&y=..&z=..[&seat=..&seatname=..]   a Keeper asks what to do; lines come back:
         spawn|First|Last|x|y|z|look   say|First|text   move|First|x|y|z   face|First|x|y|z   remove|First
         sit|First|object   stand|First   dance|First|animation   still|First   im|First|text
    POST /heard    region|name|x|y|z|text           someone said something in that region's local chat
    POST /spawned  region|first|key                 an NPC is in the world

The residents come and go by their Second Life personas (personas.py, edited in the Persona Studio): whoever is
online by their own schedule is in the world, each in a region their habits draw them to, roaming between regions
now and then, drawn to or away from company as they are. Whoever is spoken to by name (or was last talking with the
user) answers, written by the language model from that resident's own persona for this computer's year - the same
people and the same memories as on the messengers - and coloured by how they are in the world. An invitation to
sit, cuddle or dance is taken up or turned down by how receptive they are; the adults' regions and what happens
there follow each one's adult settings. The residents who'd rather IM than talk in local chat do: a line addressed
by name to someone online elsewhere in the world is an IM conversation (their reply arrives as an IM from them),
an IM-preferrer nearby answers group chat by IM, and now and then one of them IMs the user from wherever they are."""
import math
import random
import re
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from PySide6.QtCore import QObject, QTimer, Signal

from opensim_world import BRIDGE_PORT, REGION, REGIONS, personas

CAP = 7                           # residents in one region at most
HISTORY = 12                      # lines of local chat each reply sees
IDLE_SECONDS = 150                # quiet this long and someone starts a conversation
WANDER_SECONDS = 40               # a little wander this often, on average
ROAM_SECONDS = 2400               # a change of region this often, on average, per resident
TICK = 5
# what the user says that's an invitation (checked on lines addressed to a resident, or to whoever's nearest)
JOIN = re.compile(r"\b(join|sit|come|lie|lay|cuddle|snuggle|hop|climb|get)\b.*\b(me|with|here|over)\b|\bjoin me\b", re.I)
DANCE = re.compile(r"\bdanc(e|ing)\b", re.I)
STOP = re.compile(r"\b(stand up|get up|stop dancing|stop|let'?s go|that'?s enough|enough)\b", re.I)


class _Signals(QObject):
    """The web server runs on its own thread: everything it starts happens on the Qt thread through these."""
    heard = Signal(str, str, float, float, float, str)
    arrived = Signal(str)
    stood = Signal()
    status = Signal(str)


class Bridge:
    """Runs inside the computer that launched the world (a Qt app): the web server on a thread, the replies through
    the language model broker on the Qt thread."""

    def __init__(self, user_first, era=2025, on_status=None):
        self.user_first = user_first
        self.era = era
        self.lock = threading.Lock()
        self.outbox = {}                       # region -> lines for its Keeper
        self.present = {}                      # first name -> resident name
        self.where = {}                        # first name -> region
        self.spawned = set()
        self.pending = {}                      # first -> (region, spawn line) not confirmed yet (sent until it is)
        self.chat = {}                         # region -> [(speaker, text)]
        self.ims = {}                          # first name -> [(speaker, text)]: IM conversations with the user
        self.last_partner = None
        self.last_user_line = time.time()
        self.user_region = None
        self.user_at = (128.0, 128.0, 22.0)
        self.busy = set()
        self.seat = None                       # (object key, its name) the user's sitting on, or None
        self.joined = {}                       # first name -> the seat they took with the user
        self.dancing = set()
        self.rnd = random.Random()
        self.signals = _Signals()
        self.signals.heard.connect(self._heard)
        self.signals.arrived.connect(self._user_arrived)
        self.signals.stood.connect(self._user_stood)
        self.signals.status.connect(on_status or (lambda text: None))
        self.on_status = self.signals.status.emit
        self.server = None
        self.wander = QTimer()
        self.wander.timeout.connect(self._tick)
        self.cast = self._cast()               # [(resident name, first, last)]
        self.personas = {name: self._load_persona(name) for name, _f, _l in self.cast}
        self.looks = self._looks()
        self.ticks = 0

    # ---- who's around ----
    def _looks(self):
        """resident name -> the notecard asset of the look they wear: their whole fitted look (clothes and all) if the
        Tailor has saved one, else their furry avatar's."""
        import json
        from opensim_world import HERE, world_file
        try:
            picks = json.loads((HERE / "wardrobe.json").read_text(encoding="utf-8"))["picks"]
            world = json.loads(world_file().read_text(encoding="utf-8"))
        except (OSError, ValueError, KeyError):
            return {}
        saved, dressed = world.get("outfits", {}), world.get("dressed", {})
        looks = {name: saved[look]["notecard"] for name, look in picks.items()
                 if look in saved and saved[look].get("notecard", "").strip("0-")}
        looks.update({name: card for name, card in dressed.items() if card.strip("0-")})
        return looks

    def _cast(self):
        """The main residents who exist in this era: (resident name, first name, last name)."""
        out = []
        try:
            import residents
            names = residents.names(self.era, tier="main")
        except Exception:
            names = []
        for name in names:
            first = "".join(ch for ch in name if ch.isalnum())[:31]
            out.append((name, first, personas.surname(name)))
        return out

    def _load_persona(self, name):
        try:
            import residents
            r = residents.load(name, self.era)
        except Exception:
            r = None
        try:
            from opensim_world import dress
            wardrobe = dress.wardrobe()
        except Exception:
            wardrobe = None
        return personas.get(name, r, wardrobe)

    def _persona_text(self, name):
        try:
            import residents
            r = residents.load(name, self.era)
            text = r.persona if r is not None else ""
            try:
                from claudexp.residents_sync import about_you
                text += about_you(r, buddy=True)
            except Exception:
                pass
            return text
        except Exception:
            return f"You are {name}, a furry."

    def near_user(self):
        """The residents in the region the user is in."""
        return [f for f, r in self.where.items() if r == self.user_region]

    def crowd(self, region):
        return sum(1 for r in self.where.values() if r == region) + (1 if region == self.user_region else 0)

    # ---- the web server ----
    def start(self):
        bridge = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def _reply(self, text):
                data = text.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def do_GET(self):
                url = urlparse(self.path)
                if url.path == "/poll":
                    q = {k: v[0] for k, v in parse_qs(url.query).items()}
                    self._reply(bridge._poll(q))
                else:
                    self._reply("")

            def do_POST(self):
                body = self.rfile.read(int(self.headers.get("Content-Length") or 0)).decode("utf-8", "replace")
                url = urlparse(self.path)
                if url.path == "/heard":
                    parts = body.split("|", 5)
                    if len(parts) == 6:
                        try:
                            x, y, z = float(parts[2]), float(parts[3]), float(parts[4])
                        except ValueError:
                            x = y = z = 0.0
                        bridge.signals.heard.emit(parts[0], parts[1], x, y, z, parts[5])
                elif url.path == "/spawned":
                    parts = body.split("|")
                    if len(parts) >= 2:
                        first = parts[1]
                        with bridge.lock:
                            bridge.spawned.add(first)
                            bridge.pending.pop(first, None)
                        bridge.on_status(f"{first} is in {parts[0]}.")
                self._reply("")

        self.server = ThreadingHTTPServer(("127.0.0.1", BRIDGE_PORT), Handler)
        threading.Thread(target=self.server.serve_forever, name="hollow-bridge", daemon=True).start()
        self.wander.start(TICK * 1000)
        self.log_on_off()

    def stop(self):
        self.wander.stop()
        if self.server is not None:
            self.server.shutdown()
            self.server.server_close()
            self.server = None

    def _send(self, region, line):
        with self.lock:
            self.outbox.setdefault(region, []).append(line.replace("\n", " "))

    def _poll(self, q):
        region = q.get("region") or REGION
        if q.get("here") == "1":
            try:
                self.user_at = (float(q.get("x", 128)), float(q.get("y", 128)), float(q.get("z", 22)))
            except ValueError:
                pass
            if region != self.user_region:
                self.user_region = region
                self.signals.arrived.emit(region)
            seat = (q["seat"], q.get("seatname", "")) if q.get("seat") else None
            if self.seat and not seat:
                self.signals.stood.emit()
            self.seat = seat
        with self.lock:
            box = self.outbox.get(region, [])
            lines, self.outbox[region] = box[:20], box[20:]
        return "\n".join(lines)

    # ---- coming and going ----
    def _spawn(self, name, first, last, region, near=None):
        """Put a resident in a region: by the user if they're there, else somewhere around the region's middle
        (z 0: the Keeper sets them down on the ground)."""
        if near is not None:
            ux, uy, uz = near
            angle = self.rnd.uniform(0, 6.283)
            x = max(5, min(250, ux + math.cos(angle) * self.rnd.uniform(4, 9)))
            y = max(5, min(250, uy + math.sin(angle) * self.rnd.uniform(4, 9)))
            z = uz
        else:
            x, y, z = self.rnd.uniform(110, 146), self.rnd.uniform(110, 146), 0
        self.present[first] = name
        self.where[first] = region
        line = f"spawn|{first}|{last}|{x:.1f}|{y:.1f}|{z:.1f}|{self.looks.get(name, '')}"
        with self.lock:
            self.pending[first] = (region, line)
        self._send(region, line)

    def _despawn(self, first):
        region = self.where.pop(first, None)
        self.present.pop(first, None)
        self.spawned.discard(first)
        self.joined.pop(first, None)
        self.dancing.discard(first)
        with self.lock:
            self.pending.pop(first, None)
        if region:
            self._send(region, f"remove|{first}")

    def _room(self, persona, avoid=None):
        """A region for them with room in it, by their persona."""
        for _ in range(6):
            region = personas.pick_region(persona, self.rnd)
            if region != avoid and self.crowd(region) < CAP:
                return region
        return None

    def log_on_off(self):
        """Whoever's online by their schedule is in the world; whoever isn't, isn't."""
        came, went = [], []
        for name, first, last in self.cast:
            on = personas.online(self.personas[name], name)
            if on and first not in self.present:
                region = self._room(self.personas[name])
                if region:
                    self._spawn(name, first, last, region)
                    came.append((name, region))
            elif not on and first in self.present:
                self._despawn(first)
                went.append(name)
        if came:
            self.on_status("Logged on: " + ", ".join(f"{n} ({r})" for n, r in came) + ".")
        if went:
            self.on_status("Logged off: " + ", ".join(went) + ".")

    def _roam(self):
        """Now and then someone moves to another region, as their habits take them; the sociable drift towards
        company (the user), the solitary leave a crowd."""
        if not self.present:
            return
        first = self.rnd.choice(list(self.present))
        if first in self.joined or first in self.busy:
            return
        name, here = self.present[first], self.where[first]
        p = self.personas[name]
        crowds = p.get("social", {}).get("crowds", 0)
        chance = TICK / ROAM_SECONDS * len(self.present)
        target = None
        if crowds > 0.3 and self.user_region and here != self.user_region and self.rnd.random() < chance * 2:
            if self.user_region in personas.allowed_regions(p) and self.crowd(self.user_region) < CAP:
                target = self.user_region
        elif crowds < -0.3 and self.crowd(here) > 3 and self.rnd.random() < chance * 2:
            target = self._room(p, avoid=here)
        elif self.rnd.random() < chance:
            target = self._room(p, avoid=here)
        if target and target != here:
            last = next(l for n, _f, l in self.cast if n == name)
            self._despawn(first)
            near = self.user_at if target == self.user_region else None
            self._spawn(name, first, last, target, near)
            self.on_status(f"{name} went to {target}.")

    def _user_arrived(self, region):
        """The user came into a region: someone there who starts conversations says hello."""
        here = [f for f, r in self.where.items() if r == region]
        if not here:
            return
        starters = sorted(here, key=lambda f: -self.personas[self.present[f]].get("social", {}).get("initiates", 0.5))
        first = starters[0]
        if self.personas[self.present[first]].get("social", {}).get("initiates", 0.5) >= 0.35:
            QTimer.singleShot(9000, lambda: self._greet(first))

    # ---- sitting and dancing together ----
    @staticmethod
    def seat_words(name):
        """What the user's sitting on, in words: "missionary1-m" -> "missionary", "Sofa Snuggle (FP)" -> "sofa snuggle"."""
        words = re.sub(r"\(.*?\)|full ?perm\w*|poseball|pose ?ball|[-_]?[mf]\b|\d+|[-_#]", " ", name, flags=re.I)
        return re.sub(r"\s+", " ", words).strip().lower() or "a seat"

    def _act(self, first, text):
        """The user's line to a resident might be an invitation: take it up (or not, as they are) and return the
        situation for their reply."""
        region = self.where.get(first)
        if region != self.user_region:
            return None
        p = self.personas.get(self.present.get(first, ""), {})
        if STOP.search(text) and (first in self.joined or first in self.dancing):
            self._send(region, f"stand|{first}" if first in self.joined else f"still|{first}")
            self.joined.pop(first, None)
            self.dancing.discard(first)
            return f"{self.user_first} said: \"{text}\" - and you've stopped and stood up. Reply in character."
        if JOIN.search(text) and self.seat and first not in self.joined:
            key, name = self.seat
            adult = personas.is_adult_seat(name)
            if personas.accepts(p, "adult" if adult else "sit", rnd=self.rnd):
                self.joined[first] = key
                self._send(region, f"sit|{first}|{key}")
                return (f"{self.user_first} is sitting on {self.seat_words(name)!r} (a poseball set for two, or a seat) "
                        f"and said: \"{text}\". You accepted and joined them - the animation for it is playing on both "
                        "of you now. Reply in character, as yourself, to being there with them.")
            return (f"{self.user_first} is sitting on {self.seat_words(name)!r} and said: \"{text}\", asking you to "
                    f"join them. You'd rather not{' - that is more than you do with them' if adult else ' right now'}. "
                    "Turn it down kindly, in character, in one line.")
        if DANCE.search(text):
            if personas.accepts(p, "dance", rnd=self.rnd):
                from opensim_world.oar import DANCES
                self._send(region, f"dance|{first}|{self.rnd.choice(DANCES)}")
                self.dancing.add(first)
                return (f"{self.user_first} said: \"{text}\" - and you're dancing with them now. Reply in character, "
                        "as yourself, while you dance.")
            return (f"{self.user_first} said: \"{text}\", asking you to dance. You're not in the mood for dancing; "
                    "say so kindly, in character, in one line.")
        return None

    def _user_stood(self):
        """The user got up: whoever joined them gets up too."""
        for first in list(self.joined):
            region = self.where.get(first)
            if region:
                self._send(region, f"stand|{first}")
        self.joined.clear()

    # ---- conversation ----
    def _greet(self, first):
        region = self.where.get(first)
        if region is not None and region == self.user_region:
            self._ask(first, f"{self.user_first} just arrived in {region}, right near you. Say hello the way you "
                             "would to an old friend.")

    def _heard(self, region, speaker, x, y, z, text):
        log = self.chat.setdefault(region, [])
        log.append((speaker, text))
        del log[:-HISTORY]
        if not speaker.lower().startswith(self.user_first.lower()):
            return
        self.last_user_line = time.time()
        near = [f for f, r in self.where.items() if r == region]
        low = text.lower()
        named = [f for f in self.present if re.search(r"\b" + re.escape(f.lower()) + r"\b", low) or
                 re.search(r"\b" + re.escape(self.present[f].lower()) + r"\b", low)]
        addressed = [f for f in named if f in near]
        for first in [f for f in named if f not in near][:2]:      # someone online elsewhere: that's an IM to them
            self.ims.setdefault(first, []).append((speaker, text))
            del self.ims[first][:-HISTORY]
            self._ask(first, None, via="im")
        responders = addressed or ([self.last_partner] if self.last_partner in near else [])
        if not responders and near and not named:
            responders = [self._talker(near)]
        for first in responders[:2]:
            self.last_partner = first
            prefers_im = (first not in addressed and
                          self.personas[self.present[first]].get("social", {}).get("im_over_local", 0) > 0.6)
            self._ask(first, self._act(first, text), via="im" if prefers_im else "local")
        try:
            from claudexp.life import get
            sim = get()
            if sim is not None and responders:
                sim.heard(self.present[responders[0]], "Second Life", self.user_first, text)
        except Exception:
            pass

    def _im_out_of_the_blue(self):
        """Every few minutes, maybe: someone online elsewhere who likes IMs and starts conversations sends the user one."""
        if not self.user_region or self.busy:
            return
        far = [f for f, r in self.where.items() if r != self.user_region]
        keen = [f for f in far if self.personas[self.present[f]].get("social", {}).get("im_over_local", 0) > 0.5]
        if not keen:
            return
        first = self.rnd.choice(keen)
        if self.rnd.random() < 0.15 + 0.5 * self.personas[self.present[first]].get("social", {}).get("initiates", 0.5):
            self._ask(first, f"Send {self.user_first} a short IM out of the blue: what you're up to over in "
                             f"{self.where[first]}, or asking how they are, or inviting them over.", via="im")

    def _talker(self, firsts):
        """Of these, who speaks up: the chatty more often."""
        weights = [0.1 + self.personas[self.present[f]].get("social", {}).get("chattiness", 0.5) for f in firsts]
        return self.rnd.choices(firsts, weights)[0]

    def _ask(self, first, situation, via="local"):
        """Have a resident write their next line: in local chat, or (via="im") as an IM to the user."""
        if first in self.busy:
            return
        name = self.present.get(first)
        region = self.where.get(first)
        if not name or not region:
            return
        chat = self.chat.get(region, [])
        log = "\n".join(f"{s}: {t}" for s, t in chat[-HISTORY:]) or "(nobody has said anything yet)"
        others = ", ".join(self.present[f] for f, r in self.where.items() if r == region and f != first)
        here = (f"{self.user_first} (your buddy) and {others or 'nobody else'} nearby"
                if region == self.user_region else f"{others or 'nobody else'} nearby")
        flavour = personas.flavour(self.personas.get(name, {}), region)
        if via == "im":
            ims = "\n".join(f"{s}: {t}" for s, t in self.ims.get(first, [])[-HISTORY:]) or "(nothing yet)"
            where_user = (f"{self.user_first} is over in {self.user_region}" if self.user_region and
                          self.user_region != region else f"{self.user_first} is nearby, but you two are IMing")
            system = (self._persona_text(name) + f"\n\nRight now you're in Second Life, in a region called {region}, "
                      f"with {others or 'nobody else'} nearby; {where_user}. You're writing an IM (a private instant "
                      f"message) to {self.user_first}. Reply with ONE short IM as yourself (no name prefix, no quotation "
                      "marks). Keep it natural and brief.\n\nHow you are in the world:\n" + flavour)
            heard = ("\n\nWhat they just said in local chat, which you'd rather answer by IM:\n" + log.splitlines()[-1]
                     if self.user_region == region and chat else "")
            prompt = situation or ("Your IMs with them so far:\n" + ims + heard + "\n\nWrite your next IM.")
        else:
            system = (self._persona_text(name) + f"\n\nRight now you're in Second Life, standing in a region called "
                      f"{region}, with {here}. This is local chat: everyone near you sees it. Reply with ONE short chat "
                      "line as yourself (no name prefix, no quotation marks, no stage directions longer than a quick "
                      "*emote*). Keep it natural and brief.\n\nHow you are in the world:\n" + flavour)
            prompt = situation or ("Here's the local chat so far:\n" + log + "\n\nWrite your next line in the chat.")
        try:
            from claudecore.ai import ai_models, broker
            model = ai_models.model_for("conversation", resident=name)
            ctx = int(ai_models.config()["context"])
            self.busy.add(first)

            def done(reply, err, first=first, name=name, region=region, via=via):
                self.busy.discard(first)
                if err or not reply:
                    return
                line = reply.strip().splitlines()[0].strip().strip('"')
                if line.lower().startswith(first.lower() + ":"):
                    line = line.split(":", 1)[1].strip()
                if not line:
                    return
                if via == "im":
                    ims = self.ims.setdefault(first, [])
                    ims.append((name, line))
                    del ims[:-HISTORY]
                    if self.user_region:                    # the Keeper where the user is delivers it, as from them
                        self._send(self.user_region, f"im|{first}|{line[:900]}")
                    self.on_status(f"IM from {name}: {line[:80]}")
                    return
                log = self.chat.setdefault(region, [])
                log.append((name, line))
                del log[:-HISTORY]
                if region == self.user_region:
                    ux, uy, uz = self.user_at
                    self._send(region, f"face|{first}|{ux:.1f}|{uy:.1f}|{uz:.1f}")
                self._send(region, f"say|{first}|{line[:900]}")
                try:
                    from claudexp.life import get
                    sim = get()
                    if sim is not None:
                        sim.heard(name, "Second Life", name, line)
                except Exception:
                    pass
            broker.get().chat(model, [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
                              {"num_ctx": ctx, "temperature": 0.85}, done, broker.FOREGROUND, think=False)
        except Exception as exc:
            self.busy.discard(first)
            self.on_status(f"The residents can't talk right now: {exc}")

    def _tick(self):
        """Every few seconds: unconfirmed residents are asked for again; someone near the user wanders a little;
        someone may move to another region; after a long quiet someone chatty starts talking; and every few minutes
        the schedules are checked for who's logged on or off."""
        self.ticks += 1
        with self.lock:
            retry = list(self.pending.values())
        if retry and self.ticks % 3 == 0:              # every 15 seconds until each one is in
            for region, line in retry:
                self._send(region, line)
        if self.ticks % (300 // TICK) == 0:
            self.log_on_off()
            self._im_out_of_the_blue()
        self._roam()
        near = self.near_user()
        if not near:
            return
        if self.rnd.random() < TICK / WANDER_SECONDS:
            first = self.rnd.choice([f for f in near if f not in self.joined] or near)
            if first not in self.joined:
                ux, uy, uz = self.user_at
                self._send(self.user_region, f"move|{first}|{max(5, min(250, ux + self.rnd.uniform(-10, 10))):.1f}|"
                                             f"{max(5, min(250, uy + self.rnd.uniform(-10, 10))):.1f}|{uz:.1f}")
        if time.time() - self.last_user_line > IDLE_SECONDS and not self.busy:
            self.last_user_line = time.time()
            first = self._talker(near)
            if self.rnd.random() < 0.3 + self.personas[self.present[first]].get("social", {}).get("chattiness", 0.5):
                self._ask(first, f"It's gone quiet in {self.user_region}. Say something to {self.user_first} or the "
                                 "others - about your day, something you're up to, or something you can see around you.")
