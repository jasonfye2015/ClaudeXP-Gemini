"""The bridge between the Furry Hollow and the Timeline: a small web server on 127.0.0.1 that the Hollow Keeper (the
script in the region) polls every few seconds.

    GET  /poll?here=1&x=..&y=..&z=..   the Keeper asks what to do: lines like spawn|ArcticFox|Furlong|130|126|22
    POST /heard   name|x|y|z|text        someone said something in local chat
    POST /spawned first|key              an NPC is in the world

When the user's avatar is in the region a few residents appear around them; whoever is spoken to by name (or was
last talking with the user) answers, written by the language model from that resident's own persona for this
computer's year - the same people and the same memories as on the messengers. Now and then they wander, and when
the user has been quiet a while someone says something of their own."""
import json
import random
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from PySide6.QtCore import QObject, QTimer, Signal

from opensim_world import BRIDGE_PORT, REGION

PRESENT = 5                       # residents in the Hollow at once
HISTORY = 12                      # lines of local chat each reply sees
IDLE_SECONDS = 150                # quiet this long and someone starts a conversation
WANDER_SECONDS = 40


class _Signals(QObject):
    """The web server runs on its own thread: everything it starts happens on the Qt thread through these."""
    heard = Signal(str, float, float, float, str)
    arrived = Signal()
    status = Signal(str)


class Bridge:
    """Runs inside the computer that launched the world (a Qt app): the web server on a thread, the replies through
    the language model broker on the Qt thread."""

    def __init__(self, user_first, era=2025, on_status=None):
        self.user_first = user_first
        self.era = era
        self.lock = threading.Lock()
        self.outbox = []                       # lines for the Keeper
        self.present = {}                      # first name -> resident name
        self.spawned = set()
        self.pending = {}                      # spawn lines not confirmed yet (sent again until they are)
        self.chat = []                         # (speaker, text)
        self.last_partner = None
        self.last_user_line = time.time()
        self.user_at = (128.0, 128.0, 22.0)
        self.user_here = False
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

    # ---- who's around ----
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
                    parts = body.split("|", 4)
                    if len(parts) == 5:
                        try:
                            x, y, z = float(parts[1]), float(parts[2]), float(parts[3])
                        except ValueError:
                            x = y = z = 0.0
                        bridge.signals.heard.emit(parts[0], x, y, z, parts[4])
                elif url.path == "/spawned":
                    first = body.split("|")[0]
                    with bridge.lock:
                        bridge.spawned.add(first)
                        bridge.pending.pop(first, None)
                    bridge.on_status(f"{first} is in the {REGION}.")
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

    def _send(self, line):
        with self.lock:
            self.outbox.append(line.replace("\n", " "))

    def _poll(self, q):
        here = q.get("here") == "1"
        try:
            at = (float(q.get("x", 128)), float(q.get("y", 128)), float(q.get("z", 22)))
        except ValueError:
            at = self.user_at
        arrived = here and not self.user_here
        self.user_here = here
        if here:
            self.user_at = at
        if arrived:
            self.signals.arrived.emit()
        with self.lock:
            lines, self.outbox = self.outbox[:20], self.outbox[20:]
        return "\n".join(lines)

    def _populate(self):
        """The user just arrived: a handful of residents are already about, a few metres away."""
        if not self.cast:
            return
        rnd = random.Random()
        chosen = rnd.sample(self.cast, k=min(PRESENT, len(self.cast)))
        ux, uy, uz = self.user_at
        for i, (name, first, last) in enumerate(chosen):
            angle = i * (6.283 / max(1, len(chosen)))
            import math
            x = max(5, min(250, ux + math.cos(angle) * rnd.uniform(4, 9)))
            y = max(5, min(250, uy + math.sin(angle) * rnd.uniform(4, 9)))
            self.present[first] = name
            self.pending[first] = f"spawn|{first}|{last}|{x:.1f}|{y:.1f}|{uz:.1f}"
            self._send(self.pending[first])
        self.on_status(", ".join(n for n, _f, _l in chosen) + " " + ("are" if len(chosen) > 1 else "is") +
                       " in the Hollow.")
        QTimer.singleShot(9000, lambda: self._greet(chosen[0][1]))

    # ---- conversation ----
    def _greet(self, first):
        if first in self.present and self.user_here:
            self._ask(first, f"{self.user_first} just arrived in the {REGION}, right near you. Say hello the way you "
                             "would to an old friend.")

    def _heard(self, speaker, x, y, z, text):
        self.chat.append((speaker, text))
        del self.chat[:-HISTORY]
        if not speaker.lower().startswith(self.user_first.lower()):
            return
        self.last_user_line = time.time()
        low = text.lower()
        addressed = [f for f in self.present if f.lower() in low or self.present[f].lower() in low]
        responders = addressed or ([self.last_partner] if self.last_partner in self.present else [])
        if not responders and self.present:
            responders = [random.choice(list(self.present))]
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
        if not name:
            return
        log = "\n".join(f"{s}: {t}" for s, t in self.chat[-HISTORY:]) or "(nobody has said anything yet)"
        others = ", ".join(n for f, n in self.present.items() if f != first)
        system = (self._persona(name) + f"\n\nRight now you're in Second Life, standing in a region called the "
                  f"{REGION} with {self.user_first} (your buddy) and {others or 'nobody else'} nearby. This is "
                  "local chat: everyone near you sees it. Reply with ONE short chat line as yourself (no name prefix, "
                  "no quotation marks, no stage directions longer than a quick *emote*). Keep it natural and brief.")
        prompt = (situation or "Here's the local chat so far:\n" + log + f"\n\nWrite your next line in the chat.")
        try:
            from claudecore.ai import ai_models, broker
            model = ai_models.model_for("conversation", resident=name)
            ctx = int(ai_models.config()["context"])
            self.busy.add(first)

            def done(reply, err, first=first, name=name):
                self.busy.discard(first)
                if err or not reply:
                    return
                line = reply.strip().splitlines()[0].strip().strip('"')
                if line.lower().startswith(first.lower() + ":"):
                    line = line.split(":", 1)[1].strip()
                if not line:
                    return
                self.chat.append((name, line))
                del self.chat[:-HISTORY]
                self._send(f"face|{first}|{self.user_at[0]:.1f}|{self.user_at[1]:.1f}|{self.user_at[2]:.1f}")
                self._send(f"say|{first}|{line[:900]}")
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
        """Every few seconds: someone wanders a little; after a long quiet, someone starts talking."""
        if not self.user_here or not self.present:
            return
        with self.lock:
            retry = list(self.pending.values())
        self._resend = getattr(self, "_resend", 0) + 1
        if retry and self._resend % 3 == 0:            # every 15 seconds until each one is in
            for line in retry:
                self._send(line)
        if random.random() < 5 / WANDER_SECONDS:
            first = random.choice(list(self.present))
            ux, uy, uz = self.user_at
            self._send(f"move|{first}|{max(5, min(250, ux + random.uniform(-10, 10))):.1f}|"
                       f"{max(5, min(250, uy + random.uniform(-10, 10))):.1f}|{uz:.1f}")
        if time.time() - self.last_user_line > IDLE_SECONDS and not self.busy:
            self.last_user_line = time.time()
            first = random.choice(list(self.present))
            self._ask(first, f"It's gone quiet in the {REGION}. Say something to {self.user_first} or the others - "
                             "about your day, something you're up to, or something you can see around you.")
