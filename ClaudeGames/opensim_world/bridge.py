"""The bridge between the Furry Hollow's regions and the Timeline: a small web server on 127.0.0.1 that every region's
Hollow Keeper (the script in it) polls every few seconds.

    GET  /poll?region=..&here=1&x=..&y=..&z=..   a Keeper asks what to do: lines like spawn|ArcticFox|Furlong|130|126|22
    POST /heard    region|name|x|y|z|text           someone said something in that region's local chat
    POST /spawned  region|first|key                 an NPC is in the world

The first time the user's avatar is in a region, a few residents are already about there; each region gets its own
crowd, and they stay put when the user moves on. Whoever is spoken to by name (or was last talking with the user)
answers, written by the language model from that resident's own persona for this computer's year - the same people
and the same memories as on the messengers. Now and then they wander, and when the user has been quiet a while
someone nearby says something of their own."""
import math
import random
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from PySide6.QtCore import QObject, QTimer, Signal

from opensim_world import BRIDGE_PORT, REGION

PRESENT = 5                       # residents in each region
HISTORY = 12                      # lines of local chat each reply sees
IDLE_SECONDS = 150                # quiet this long and someone starts a conversation
WANDER_SECONDS = 40


class _Signals(QObject):
    """The web server runs on its own thread: everything it starts happens on the Qt thread through these."""
    heard = Signal(str, str, float, float, float, str)
    arrived = Signal(str)
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
        self.populated = set()                 # regions that have their crowd
        self.spawned = set()
        self.pending = {}                      # first -> (region, spawn line) not confirmed yet (sent until it is)
        self.chat = {}                         # region -> [(speaker, text)]
        self.last_partner = None
        self.last_user_line = time.time()
        self.user_region = None
        self.user_at = (128.0, 128.0, 22.0)
        self.busy = set()
        self.signals = _Signals()
        self.signals.heard.connect(self._heard)
        self.signals.arrived.connect(self._populate)
        self.signals.status.connect(on_status or (lambda text: None))
        self.on_status = self.signals.status.emit
        self.server = None
        self.wander = QTimer()
        self.wander.timeout.connect(self._tick)
        self.cast = self._cast()
        self.looks = self._looks()

    # ---- who's around ----
    def _looks(self):
        """resident name -> the notecard asset of the furry avatar they picked (wardrobe.json), for the looks the
        Tailor has saved in this world (world.json "outfits")."""
        import json
        from opensim_world import HERE, world_file
        try:
            picks = json.loads((HERE / "wardrobe.json").read_text(encoding="utf-8"))["picks"]
            saved = json.loads(world_file().read_text(encoding="utf-8")).get("outfits", {})
        except (OSError, ValueError, KeyError):
            return {}
        try:                                    # each resident's own whole look, clothes and all (tailor.py)
            dressed = json.loads(world_file().read_text(encoding="utf-8")).get("dressed", {})
        except (OSError, ValueError):
            dressed = {}
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
            try:
                from claudexp.programs.secondlife.residents import surname
                last = surname(name)
            except Exception:
                last = "Resident"
            out.append((name, first, last))
        return out

    def _persona(self, name):
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
        self.wander.start(5000)

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
        with self.lock:
            box = self.outbox.get(region, [])
            lines, self.outbox[region] = box[:20], box[20:]
        return "\n".join(lines)

    def _populate(self, region):
        """The user just came into a region: the first time, a handful of residents are already about there."""
        if region in self.populated or not self.cast:
            return
        self.populated.add(region)
        free = [c for c in self.cast if c[1] not in self.present]
        if not free:
            return
        rnd = random.Random()
        chosen = rnd.sample(free, k=min(PRESENT, len(free)))
        ux, uy, uz = self.user_at
        for i, (name, first, last) in enumerate(chosen):
            angle = i * (6.283 / max(1, len(chosen)))
            x = max(5, min(250, ux + math.cos(angle) * rnd.uniform(4, 9)))
            y = max(5, min(250, uy + math.sin(angle) * rnd.uniform(4, 9)))
            self.present[first] = name
            self.where[first] = region
            line = f"spawn|{first}|{last}|{x:.1f}|{y:.1f}|{uz:.1f}|{self.looks.get(name, '')}"
            with self.lock:
                self.pending[first] = (region, line)
            self._send(region, line)
        self.on_status(", ".join(n for n, _f, _l in chosen) + " " + ("are" if len(chosen) > 1 else "is") +
                       f" in {region}.")
        QTimer.singleShot(9000, lambda: self._greet(chosen[0][1]))

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
        addressed = [f for f in near if f.lower() in low or self.present[f].lower() in low]
        responders = addressed or ([self.last_partner] if self.last_partner in near else [])
        if not responders and near:
            responders = [random.choice(near)]
        for first in responders[:2]:
            self.last_partner = first
            self._ask(first, None)
        try:
            from claudexp.life import get
            sim = get()
            if sim is not None and responders:
                sim.heard(self.present[responders[0]], "Second Life", self.user_first, text)
        except Exception:
            pass

    def _ask(self, first, situation):
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
        system = (self._persona(name) + f"\n\nRight now you're in Second Life, standing in a region called "
                  f"{region}, with {here}. This is local chat: everyone near you sees it. Reply with ONE short chat "
                  "line as yourself (no name prefix, no quotation marks, no stage directions longer than a quick "
                  "*emote*). Keep it natural and brief.")
        prompt = situation or ("Here's the local chat so far:\n" + log + "\n\nWrite your next line in the chat.")
        try:
            from claudecore.ai import ai_models, broker
            model = ai_models.model_for("conversation", resident=name)
            ctx = int(ai_models.config()["context"])
            self.busy.add(first)

            def done(reply, err, first=first, name=name, region=region):
                self.busy.discard(first)
                if err or not reply:
                    return
                line = reply.strip().splitlines()[0].strip().strip('"')
                if line.lower().startswith(first.lower() + ":"):
                    line = line.split(":", 1)[1].strip()
                if not line:
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
        """Every few seconds: unconfirmed residents are asked for again, someone near the user wanders a little, and
        after a long quiet someone starts talking."""
        with self.lock:
            retry = list(self.pending.values())
        self._resend = getattr(self, "_resend", 0) + 1
        if retry and self._resend % 3 == 0:            # every 15 seconds until each one is in
            for region, line in retry:
                self._send(region, line)
        near = self.near_user()
        if not near:
            return
        if random.random() < 5 / WANDER_SECONDS:
            first = random.choice(near)
            ux, uy, uz = self.user_at
            self._send(self.user_region, f"move|{first}|{max(5, min(250, ux + random.uniform(-10, 10))):.1f}|"
                                         f"{max(5, min(250, uy + random.uniform(-10, 10))):.1f}|{uz:.1f}")
        if time.time() - self.last_user_line > IDLE_SECONDS and not self.busy:
            self.last_user_line = time.time()
            first = random.choice(near)
            self._ask(first, f"It's gone quiet in {self.user_region}. Say something to {self.user_first} or the "
                             "others - about your day, something you're up to, or something you can see around you.")
