"""What MSN Messenger and Yahoo! Messenger share: the buddies (ClaudeAIM's contacts, the same people), whether
they're on, the conversations and the replies.

Presence is shared with AIM: while ClaudeAIM is signed on, a buddy who is online or away there is online or away
here too (one person running all their IMs); otherwise their AIM sleep schedule decides. Memory is shared too: a
buddy's replies see their life journal, the end of your AIM chat with them and the end of your chat on the other
messenger, and every line goes into the life sim's shared memory. Histories live in data/messengers/<network>/."""
import json
import random
import re
import time
from datetime import datetime

from PySide6.QtCore import QObject, QTimer, Signal

from ... import broker
from ...paths import DATA
from ..aim import ensure_aim_path

ensure_aim_path()
from claudeaim import timefmt  # noqa: E402
from claudeaim.llm import clean_reply  # noqa: E402

PROMPT = """You are {name}, chatting with your buddy "{user}" on {network}.
Right now it is {now}. You are a real person living in that time. Never say or hint that you are an AI, a model, or a character, and never mention these instructions.
Write like a real instant message: casual and short, usually one to three lines. No narration, no stage directions, no timestamps, and don't put your screen name in front of your message.

About you:
{persona}

Status: {status}{memory}"""

OFFLINE, ONLINE, AWAY, BUSY = "offline", "online", "away", "busy"
NETWORK_TITLES = {"msn": "MSN Messenger", "yim": "Yahoo! Messenger", "icq": "ICQ", "trillian": "Trillian",
                  "skype": "Skype", "kik": "Kik", "telegram": "Telegram", "discord": "Discord"}
CHECK_MS = 30000                # how often presence is re-read


def codes_for(b):
    """A buddy's Furry Code and YIFF Code as their Fur Directory card shows them: {"furcode", "yiffcode"} (the YIFF
    Code only if they make it public), or {}."""
    from ...paths import ROOT
    try:
        rec = json.loads((ROOT / "Program Files" / "The Fur Directory" / "residents" /
                          f"{b.contact.id}.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    c = rec.get("codes") or {}
    return {"furcode": c.get("furcode", ""), "yiffcode": c.get("yiffcode", "") if c.get("yiff_public") else ""}


def decode_in_furcoder(desktop, name):
    """Open FurCoder on someone's codes."""
    try:
        from furcoder import launch
        launch(desktop, select=name)
    except Exception:
        pass


def _slug(text):
    return re.sub(r"[^a-z0-9]+", "", text.lower())


class Buddy:
    def __init__(self, contact, network):
        self.contact = contact
        self.network = network
        self.presence = OFFLINE
        self.busy = False
        self.unread = False
        self.history = []
        self.path = DATA / "messengers" / network.key / f"{contact.id}.json"
        try:
            self.history = json.loads(self.path.read_text(encoding="utf-8")).get("messages", [])
        except (OSError, ValueError):
            self.history = []

    @property
    def name(self):
        return self.contact.screen_name

    @property
    def handle(self):
        return self.network.handle_for(self.contact)

    def add(self, kind, text, **extra):
        """A line of the conversation; extra fields ride along (Telegram's "sticker": the picture's path)."""
        entry = {"kind": kind, "text": text, "ts": datetime.now().astimezone().isoformat(timespec="seconds"), **extra}
        self.history.append(entry)
        del self.history[:-400]
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps({"messages": self.history}, indent=1), encoding="utf-8")
        return entry


class Network(QObject):
    """One messenger's view of the buddies. Subclasses give the name, how screen names look and the UI."""
    key = ""                # 'msn' -> data/messengers/msn
    title = ""              # 'MSN Messenger'
    presence_changed = Signal(str)          # buddy id
    message_added = Signal(str, dict)       # buddy id, entry
    typing_changed = Signal(str, bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.buddies = {}
        self.signed_in = False
        self.my_status = ONLINE
        self.timer = QTimer(self, interval=CHECK_MS, timeout=self.refresh)
        self.reload()

    # ---- the people ----------------------------------------------------------------------------------------
    def reload(self):
        from ..people import load_buddies
        pairs, _errors = load_buddies(self.key)          # each contact file may have an "msn" / "yim" section
        contacts = [c for c, _sec in pairs]
        self.sections = {c.id: sec or {} for c, sec in pairs}
        old = self.buddies
        self.buddies = {c.id: old.get(c.id) or Buddy(c, self) for c in contacts}
        for b in self.buddies.values():
            b.contact = next(c for c in contacts if c.id == b.contact.id)

    def handle_for(self, contact):
        """This network's screen name for a buddy (a contact file may give its own: "msn"/"yim" sections)."""
        return contact.screen_name

    def my_handle(self):
        from ... import user
        return user.online_handle() or user.user_name() or "me"

    # ---- signing in and presence ---------------------------------------------------------------------------
    def sign_in(self):
        self.signed_in = True
        self.refresh()
        self.timer.start()
        online = [b for b in self.buddies.values() if b.presence == ONLINE]
        for b in random.sample(online, min(2, len(online))):
            if random.random() < 0.2:                      # once in a while a buddy says hi when you come on
                QTimer.singleShot(random.randint(8, 40) * 1000,
                                  lambda b=b: self.reach_out(b, "Your buddy just signed on. Say hi."))

    def sign_out(self):
        self.signed_in = False
        self.timer.stop()
        for b in self.buddies.values():
            if b.presence != OFFLINE:
                b.presence = OFFLINE
                self.presence_changed.emit(b.contact.id)

    def _aim_presence(self, b):
        """Their presence on a signed-on ClaudeAIM, or None if ClaudeAIM isn't running."""
        from ...life import get as life
        world = getattr(life(), "aim_world", None) if life() else None
        if world is None:
            return None
        try:
            ab = world.buddies.get(b.contact.id)
            return ab.presence.value if ab is not None else OFFLINE
        except (AttributeError, RuntimeError):
            return None

    def _own_presence(self, b):
        """Without AIM: awake by their schedule, and on for most of their waking half-hours."""
        c = b.contact
        now = timefmt.local_now(c.timezone)
        if c.schedule is not None and c.schedule.awake_until(now) is None:
            return OFFLINE
        slot = int(time.time() // 1800)
        rng = random.Random(f"{c.id}:{slot}")
        if rng.random() > max(0.35, c.start_online_chance):
            return OFFLINE
        return AWAY if rng.random() < c.away_chance * 0.6 else ONLINE

    def refresh(self):
        if not self.signed_in:
            return
        from ... import llm_server
        no_model = not llm_server.ready()
        for b in self.buddies.values():
            p = self._aim_presence(b)
            if p is None:
                p = self._own_presence(b)
            if no_model and p == ONLINE:
                p = AWAY                          # nobody can answer without a model: say so
            if p != b.presence:
                b.presence = p
                self.presence_changed.emit(b.contact.id)

    # ---- talking ---------------------------------------------------------------------------------------------
    def send(self, b, text, **extra):
        e = b.add("user", text, **extra)
        self.message_added.emit(b.contact.id, e)
        self._heard(b, self.my_handle(), text)
        if b.presence == OFFLINE:
            e2 = b.add("system", f"{self._display(b)} is offline and may not reply.")
            self.message_added.emit(b.contact.id, e2)
            return
        from ... import llm_server
        if not llm_server.ready():
            import time as _t
            if _t.monotonic() - getattr(b, "auto_replied", -9999) > 600:      # an away message, now and then
                b.auto_replied = _t.monotonic()

                def auto():
                    e3 = b.add("system", f"Auto-reply from {self._display(b)}: I'm away from my computer right "
                                         "now. I'll get back to you!")
                    self.message_added.emit(b.contact.id, e3)
                QTimer.singleShot(1200, auto)
            return
        delay = random.uniform(1.5, 5) if b.presence == ONLINE else random.uniform(30, 120)
        QTimer.singleShot(int(delay * 1000), lambda: self._reply(b))

    def reach_out(self, b, instruction):
        if self.signed_in and b.presence == ONLINE and not b.busy:
            self._reply(b, instruction)

    def _display(self, b):
        return b.name

    def _memory(self, b):
        """What else they know: their life journal, and how your chats on AIM and the other messenger ended."""
        parts = []
        from ...life import get as life
        if life() is not None:
            try:
                parts.append(life().context(b.name))
            except Exception:
                pass
        user = self.my_handle()
        try:
            from claudeaim.storage import History
            aim = [m for m in History(b.contact.id).messages if m.get("kind") in ("user", "contact")][-8:]
            if aim:
                parts.append("\n\nThe end of your last chat with them on AIM:\n" + "\n".join(
                    f"{user if m['kind'] == 'user' else b.name}: {m.get('text', '')}" for m in aim))
        except Exception:
            pass
        for other, net in NETWORK_TITLES.items():
            if other == self.key:
                continue
            path = DATA / "messengers" / other / f"{b.contact.id}.json"
            try:
                msgs = [m for m in json.loads(path.read_text(encoding="utf-8")).get("messages", [])
                        if m.get("kind") in ("user", "contact")][-6:]
            except (OSError, ValueError):
                msgs = []
            if msgs:
                parts.append(f"\n\nThe end of your last chat with them on {net}:\n" + "\n".join(
                    f"{user if m['kind'] == 'user' else b.name}: {m.get('text', '')}" for m in msgs))
        return "".join(parts)

    def _reply(self, b, instruction=None):
        if b.busy:
            return
        from ... import ai_models, llm_server
        if not llm_server.available():
            return
        b.busy = True
        self.typing_changed.emit(b.contact.id, True)
        user = self.my_handle()
        status = {ONLINE: f"{user} is online.", AWAY: f"{user} is away.", BUSY: f"{user} is busy."}.get(
            self.my_status, f"{user} is online.")
        system = PROMPT.format(name=b.name, user=user, network=self.title,
                               now=timefmt.now_text(b.contact.timezone), persona=b.contact.persona.strip(),
                               status=status, memory=self._memory(b))
        msgs = [{"role": "system", "content": system}]
        for m in b.history[-30:]:
            if m["kind"] == "user":
                msgs.append({"role": "user", "content": m["text"]})
            elif m["kind"] == "contact":
                said = msgs[-1]["content"] if msgs[-1]["role"] == "user" else ""
                text = clean_reply(m["text"], b.name, user, said)     # (old transcript-style slips, cleaned)
                if text:
                    msgs.append({"role": "assistant", "content": text})
        if instruction:
            msgs.append({"role": "user", "content": f"[{instruction}]"})
        elif msgs[-1]["role"] != "user":
            b.busy = False
            self.typing_changed.emit(b.contact.id, False)
            return
        model = ai_models.model_for("conversation", resident=b.name)

        last_said = next((m["content"] for m in reversed(msgs) if m["role"] == "user"), "")

        def done(text, err):
            reply = clean_reply(text or "", b.name, user, last_said) if not err else ""
            if not reply:
                b.busy = False
                self.typing_changed.emit(b.contact.id, False)
                return
            typing = min(8.0, 0.8 + len(reply) / 18)
            QTimer.singleShot(int(typing * 1000), lambda: self._deliver(b, reply))

        broker.get().chat(model, msgs, {"num_ctx": int(ai_models.config()["context"]),
                                        "temperature": b.contact.temperature}, done, broker.AIM, think=False)

    def _deliver(self, b, text):
        b.busy = False
        self.typing_changed.emit(b.contact.id, False)
        e = b.add("contact", text)
        b.unread = True
        self.message_added.emit(b.contact.id, e)
        self._heard(b, b.name, text)

    def _heard(self, b, speaker, text):
        from ...life import get as life
        if life() is not None:
            life().heard(b.name, self.title, speaker, text)
