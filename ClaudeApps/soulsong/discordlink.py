"""Soul and Song on Discord: a bot of the user's own (an application made in Discord's Developer Portal, named
"Soul and Song"), answered by whichever Companion is open - just as on Telegram (telegram.py), and the same people
may talk with it: the user, linked by a code sent to it in a direct message, and the people they invite.

Discord keeps a connection open instead of being asked (its gateway, a WebSocket - Qt's own QtWebSockets, nothing to
install). Soul and Song says who it is, asking only for direct messages (no privileged intents to switch on), keeps
the connection alive with heartbeats, and picks up where it was after a drop. Discord doesn't hold messages for a
bot that's away, so once connected it reads back, from each conversation it knows, what came since it last looked.
Only one copy of Soul and Song can listen to a bot at a time. A bot can only be messaged by someone who shares a
server with it: the user adds it to one they're in (a private one of their own is fine).

Everything is labelled AI: Discord marks the account as an app, Soul and Song sets the application's description to
say it's an AI, and anyone invited is told before anything else. Kept in Companions/discord.json (in Local Storage,
never in git): the token - a secret: whoever has it controls the bot - who's linked, the invitation codes, and how
far each conversation has been read."""
import json
import random
import sys
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QObject, QTimer, QUrl

from .telegram import CANT, DESCRIPTION, LINKED, PICTURE_LIMIT, PRIVATE, WELCOME, chunks, fetch   # noqa: F401

NAME = "Discord"
API = "https://discord.com/api/v10"
GATEWAY = "wss://gateway.discord.gg/?v=10&encoding=json"
AGENT = "DiscordBot (soul-and-song, 1.0)"
LIMIT = 1990                     # (Discord's limit is 2,000 characters a message)
INTENTS = 1 << 12                # direct messages - and nothing else
VOICE = 1 << 13                  # (a message's flags: a voice message)
FATAL = {4004: "Discord refused the bot's token - link it again with a new one (Developer Portal > Bot > Reset "
               "Token).", 4010: "", 4011: "", 4012: "", 4013: "", 4014: ""}
INTRO = ("Talk with your Companion on Discord - on your phone or any computer - through a bot of your own: make it "
         "in Discord's <b>Developer Portal</b> (<b>How to connect...</b> below walks you through it), name it "
         "<b>Soul and Song</b>, and paste its token here. Discord marks it as an app, and its description and its "
         "first words to anyone say it's an AI.")
TOKEN_HINT = "The bot's token, from Discord's Developer Portal (keep it secret)"
HOW_HINT = "The setup, step by step: making the bot in Discord's Developer Portal, and linking it here"
SETUP = """<h3>Connecting Soul and Song to Discord</h3>
<ol>
<li>In your browser, open Discord's <b>Developer Portal</b> - discord.com/developers/applications - and sign in
with your Discord account.</li>
<li>Click <b>New Application</b>, name it <b>Soul and Song</b>, agree to Discord's terms and click <b>Create</b>.
(If you like, give it a picture: <b>App Icon</b>, on the page that opens.)</li>
<li>Click <b>Bot</b> in the menu on the left, then <b>Reset Token</b> (and yes), then <b>Copy</b>. That's the bot's
<b>token</b>: keep it to yourself - whoever has it controls the bot. Discord shows it only once; if you lose it,
reset it again.</li>
<li>Back in Soul and Song's Discord window, paste the token and click <b>Link</b>. Soul and Song checks it with
Discord and sets the app's description to say it's an AI.</li>
<li>Discord only lets you message a bot you share a server with: click <b>Add it to a server...</b> - your browser
opens Discord's page for it. Pick a server you're in (a private one of your own is fine: the <b>+</b> at the
bottom of Discord's list of servers makes one) and click <b>Authorize</b>.</li>
<li>In Discord, find <b>Soul and Song</b> in that server's member list, click it, and send it a message: the
six-figure code the window shows. It answers "Linked."</li>
<li>Now just message it - words, or pictures. To invite someone, add them to that server, click <b>Invite
someone...</b> here, and give them the code to send the bot in a direct message.</li>
</ol>
<p><b>Good to know:</b> only one Soul and Song can listen to a bot at a time - don't run it on its own and inside a
computer together. For it to write to you first, Discord must let that server's members message you (your privacy
settings for the server). To keep it listening with the window closed, run Soul and Song on its own (the launcher's
<b>APPS</b>): closing the window leaves an icon in the notification area - click it, or start Soul and Song again, to
bring the window back. Direct messages on Discord aren't end-to-end encrypted - Discord's servers carry them.</p>
<p>(If you'd rather nobody else could add the bot to a server: in the Developer Portal, set <b>Installation >
Install Link</b> to None, then turn <b>Bot > Public Bot</b> off. It talks only with you and the people you invite
either way.)</p>"""


class DiscordError(Exception):
    pass


def call(token, method, path, body=None, timeout=20):
    """A REST call -> its JSON (None for an empty answer). Raises DiscordError with Discord's own words; a "slow
    down" is waited out (briefly) and tried again."""
    data = None if body is None else json.dumps(body).encode("utf-8")
    headers = {"Authorization": f"Bot {token}", "User-Agent": AGENT}
    if data is not None:
        headers["Content-Type"] = "application/json"
    for _try in range(3):
        req = urllib.request.Request(API + path, data=data, method=method, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                raw = r.read()
            return json.loads(raw) if raw else None
        except urllib.error.HTTPError as e:
            try:
                said = json.loads(e.read().decode("utf-8", "replace"))
            except ValueError:
                said = {}
            if e.code == 429:
                time.sleep(min(10.0, float(said.get("retry_after") or 1)))
                continue
            raise DiscordError(said.get("message") or f"HTTP {e.code}") from None
    raise DiscordError("Discord asked it to slow down")


def _epoch(stamp):
    try:
        return datetime.fromisoformat(str(stamp).replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def picture_of(m):
    """A message's picture: {"file_id", "url", "emoji"} - its first picture attachment, or a sticker that's a
    still picture - or None."""
    for att in m.get("attachments") or []:
        if str(att.get("content_type", "")).startswith("image/") and att.get("size", 0) <= PICTURE_LIMIT:
            return {"file_id": att["id"], "url": att["url"], "emoji": ""}
    for st in m.get("sticker_items") or []:
        if st.get("format_type") == 1:                   # (PNG; the others move)
            return {"file_id": st["id"], "url": f"https://media.discordapp.net/stickers/{st['id']}.png",
                    "emoji": st.get("name", "")}
    return None


def other_of(m):
    """What a message without words or a picture is, in words - or None."""
    if int(m.get("flags") or 0) & VOICE:
        return "voice messages"
    for att in m.get("attachments") or []:
        kind = str(att.get("content_type", ""))
        return "videos" if kind.startswith("video/") else "audio" if kind.startswith("audio/") else "files"
    return "polls" if m.get("poll") else None


class Link:
    """The bot and who's linked to it (discord.json); reading, sending, and what each message is."""

    def __init__(self, folder, api=None, files=None):
        self.path = Path(folder) / "discord.json"
        self.api = api or call
        self.files = files or fetch
        self.lock = threading.RLock()            # (the read-back thread and the window's both write it)
        try:
            self.data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            self.data = {}
        for key, empty in (("guests", []), ("codes", {}), ("told", []), ("read", {})):
            self.data.setdefault(key, empty)

    def save(self):
        with self.lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.path.with_suffix(".tmp")
            tmp.write_text(json.dumps(self.data, indent=1, ensure_ascii=False), encoding="utf-8")
            tmp.replace(self.path)

    @property
    def token(self):
        return self.data.get("token") or ""

    @property
    def bot(self):
        return self.data.get("bot") or {}

    @property
    def owner(self):
        return self.data.get("owner")

    def ready(self):
        return bool(self.token and self.bot)

    # ---- setting it up ----
    def connect(self, token):
        """Check a token with Discord, keep it, and describe the app as an AI. Returns the bot's name."""
        token = token.strip()
        me = self.api(token, "GET", "/users/@me")
        try:
            app = self.api(token, "GET", "/applications/@me") or {}
        except Exception:
            app = {}
        with self.lock:
            self.data.update(token=token, bot={"id": me["id"], "username": me.get("username", ""),
                                               "name": me.get("global_name") or me.get("username", ""),
                                               "app": app.get("id") or me["id"]})
            self.save()
        self.label()
        return self.bot["name"] or self.bot["username"]

    def label(self):
        """The application's description: it's an AI (best effort - the bot works either way)."""
        try:
            self.api(self.token, "PATCH", "/applications/@me", {"description": DESCRIPTION})
        except Exception:
            pass

    def invite_url(self):
        """Discord's page for adding the bot to a server (it needs no permissions there: it talks in direct
        messages)."""
        return f"https://discord.com/oauth2/authorize?client_id={self.bot.get('app') or self.bot.get('id')}" \
               "&scope=bot&permissions=0"

    def forget(self):
        with self.lock:
            self.data = {"guests": [], "codes": {}, "told": [], "read": {}}
            self.save()

    def code(self, kind, name=""):
        c = f"{random.randint(0, 999999):06d}"
        with self.lock:
            self.data["codes"][c] = {"for": kind, "name": name, "made": time.time()}
            self.save()
        return c

    def remove_guest(self, gid):
        with self.lock:
            self.data["guests"] = [g for g in self.data["guests"] if g["id"] != gid]
            self.save()

    # ---- what came in ----
    def classify(self, m):
        """One message -> {"kind", "chat", "user", "name", "text", "date", "picture", "other"}, as telegram.Link's:
        kind "owner" or "guest" (talk), "linked" or "invited" (a code just used), "stranger" (told once it's
        private), or None. Only direct messages count - a server's channels aren't for it - and never a bot's."""
        with self.lock:
            return self._classify(m)

    def _classify(self, m):
        author = (m or {}).get("author") or {}
        if not m or m.get("guild_id") or author.get("bot") or not author.get("id") or not m.get("channel_id"):
            return None
        uid, chat = author["id"], m["channel_id"]
        if m.get("id"):
            self.data["read"][chat] = m["id"]            # (read up to here: after a time away, it reads on from it)
        text = (m.get("content") or "").strip()
        picture = picture_of(m)
        stickers = m.get("sticker_items") or []
        if not text and stickers:
            text = f"(a sticker: {stickers[0].get('name', '')})"
        other = None if text or picture else other_of(m)
        if not text and not picture and not other:
            self.save()
            return None
        name = author.get("global_name") or author.get("username") or "someone"
        out = {"chat": chat, "user": uid, "name": name, "text": text, "date": _epoch(m.get("timestamp")),
               "picture": picture, "other": other}
        word = text.split()[-1] if text.split() else ""
        code = self.data["codes"].get(word)
        if code and time.time() - code["made"] < 7 * 86400:
            del self.data["codes"][word]
            if code["for"] == "owner":
                self.data["owner"] = {"id": uid, "name": name, "chat": chat}
                kind = "linked"
            else:
                guest = {"id": uid, "name": code.get("name") or name, "chat": chat, "since": time.time()}
                self.data["guests"] = [g for g in self.data["guests"] if g["id"] != uid] + [guest]
                out["name"] = guest["name"]
                kind = "invited"
            self.save()
            return dict(out, kind=kind)
        self.save()
        if self.owner and uid == self.owner["id"]:
            return dict(out, kind="owner")
        guest = next((g for g in self.data["guests"] if g["id"] == uid), None)
        if guest:
            return dict(out, kind="guest", name=guest["name"])
        if uid in self.data["told"]:
            return None
        self.data["told"] = (self.data["told"] + [uid])[-200:]
        self.save()
        return dict(out, kind="stranger")

    def catch_up(self, deliver):
        """What came in each known conversation while it was away (read back from where it last read), oldest
        first, to deliver(message). Run on a thread of its own: it asks Discord."""
        with self.lock:
            chats = [p["chat"] for p in ([self.owner] if self.owner else []) + self.data["guests"]]
            read = dict(self.data["read"])
        for chat in chats:
            if not read.get(chat):
                continue                                 # (nothing read there yet: nothing to catch up on)
            try:
                found = self.api(self.token, "GET", f"/channels/{chat}/messages?after={read[chat]}&limit=50") or []
            except Exception:
                continue
            for m in sorted(found, key=lambda x: int(x["id"])):
                deliver(m)

    # ---- what goes out ----
    def send(self, chat, text):
        for piece in chunks(text, LIMIT):
            self.api(self.token, "POST", f"/channels/{chat}/messages",
                     {"content": piece, "allowed_mentions": {"parse": []}})

    def typing(self, chat):
        try:
            self.api(self.token, "POST", f"/channels/{chat}/typing")
        except Exception:
            pass

    def download(self, picture):
        """A picture someone sent, as bytes (Discord gives its address)."""
        return self.files(picture["url"])


# ---- the Discord window's words ----
def waiting_text(link, code):
    return (f"Linked to <b>{link.bot['name']}</b>. Now add it to a server you're in (<b>Add it to a server...</b>), "
            f"then send it this code in a direct message to link your account: <b>{code}</b>")


def linked_text(link):
    return f"Linked to <b>{link.bot['name']}</b> - {link.owner['name']}'s account."


def invite_text(link, name, code):
    return (f"Give {name} this code: {code}\n\nThey need to share a server with {link.bot['name']} (add them to "
            "yours), then send it the code in a direct message. It works once, for a week. They'll be told it's an "
            "AI, and that you can read the conversation.")


# ---- the gateway: the connection kept open --------------------------------------------------------------------------
def make_socket():
    """A WebSocket (Qt's own; the tests stand one in)."""
    from PySide6.QtWebSockets import QWebSocket
    return QWebSocket()


class Listener(QObject):
    """Discord's gateway, kept open: who Soul and Song is, heartbeats, picking up after a drop - each direct message
    to deliver(message); once connected, what came while it was away (read back on a thread of its own)."""

    def __init__(self, link, deliver, on_status=None):
        super().__init__()
        self.link, self.deliver = link, deliver
        self.on_status = on_status or (lambda text: None)
        self.ws = None
        self.seq = self.session = self.resume_url = None
        self.stopped = False
        self.acked = True
        self.pause = 2.0                         # seconds before trying again, doubling to two minutes
        self.beat = QTimer(self)
        self.beat.timeout.connect(self._heartbeat)
        self.retry = QTimer(self)
        self.retry.setSingleShot(True)
        self.retry.timeout.connect(self._connect)
        self.hello = QTimer(self)                # (no Hello in time: try again)
        self.hello.setSingleShot(True)
        self.hello.timeout.connect(lambda: self._reconnect(resume=True))

    def start(self):
        self.stopped = False
        self._connect()

    def stop(self):
        self.stopped = True
        for timer in (self.beat, self.retry, self.hello):
            timer.stop()
        self._drop_socket()

    def alive(self):
        return not self.stopped

    # ---- the connection ----
    def _connect(self):
        if self.stopped or not self.link.ready():
            return
        self._drop_socket()
        self.ws = make_socket()
        self.ws.textMessageReceived.connect(self._received)
        self.ws.disconnected.connect(self._dropped)
        resume = self.session and self.resume_url and self.seq is not None
        self.ws.open(QUrl(f"{self.resume_url}/?v=10&encoding=json" if resume else GATEWAY))
        self.hello.start(30000)

    def _drop_socket(self):
        ws, self.ws = self.ws, None
        if ws is not None:
            try:
                ws.disconnected.disconnect(self._dropped)
                ws.textMessageReceived.disconnect(self._received)
            except (RuntimeError, TypeError):
                pass
            ws.close()
            ws.deleteLater()

    def _send(self, op, d):
        if self.ws is not None:
            self.ws.sendTextMessage(json.dumps({"op": op, "d": d}))

    def _reconnect(self, resume=True, wait=0.5):
        if not resume:
            self.session = self.seq = None
        self.beat.stop()
        self.hello.stop()
        self._drop_socket()
        if not self.stopped:
            self.retry.start(int(wait * 1000))

    def _dropped(self):
        ws = self.ws
        code = ws.closeCode() if ws is not None else 1000
        code = int(getattr(code, "value", code))
        self.beat.stop()
        self.hello.stop()
        self._drop_socket()
        if self.stopped:
            return
        if code in FATAL:
            self.stopped = True
            self.on_status(FATAL[code] or f"Discord closed the connection ({code}) - Soul and Song stopped listening "
                                          "there.")
            return
        if code in (4007, 4009):                         # (the session can't be picked up: start afresh)
            self.session = self.seq = None
        self.retry.start(int(self.pause * 1000))
        self.pause = min(120.0, self.pause * 2)

    # ---- what Discord says ----
    def _received(self, text):
        try:
            msg = json.loads(text)
        except ValueError:
            return
        op, d = msg.get("op"), msg.get("d")
        if msg.get("s") is not None:
            self.seq = msg["s"]
        if op == 10:                                     # Hello: say who it is (or pick up), and keep beating
            self.hello.stop()
            interval = int((d or {}).get("heartbeat_interval") or 41250)
            self.acked = True
            self.beat.start(interval)
            if self.session and self.seq is not None:
                self._send(6, {"token": self.link.token, "session_id": self.session, "seq": self.seq})
            else:
                self._send(2, {"token": self.link.token, "intents": INTENTS,
                               "properties": {"os": sys.platform, "browser": "Soul and Song",
                                              "device": "Soul and Song"}})
        elif op == 11:                                   # (a heartbeat heard)
            self.acked = True
        elif op == 1:                                    # (Discord asks for one now)
            self._heartbeat(force=True)
        elif op == 7:                                    # (asked to reconnect: it picks up where it was)
            self._reconnect(resume=True)
        elif op == 9:                                    # (the session's gone: afresh, unless it can be picked up)
            self._reconnect(resume=bool(d), wait=random.uniform(1, 5))
        elif op == 0:
            kind = msg.get("t")
            if kind == "READY":
                self.session = (d or {}).get("session_id")
                self.resume_url = ((d or {}).get("resume_gateway_url") or "").rstrip("/") or None
                self.pause = 2.0
                link, deliver = self.link, self.deliver
                threading.Thread(target=link.catch_up, args=(deliver,), name="soulsong-discord-catch-up",
                                 daemon=True).start()
            elif kind == "RESUMED":
                self.pause = 2.0
            elif kind == "MESSAGE_CREATE" and d:
                self.deliver(d)

    def _heartbeat(self, force=False):
        if self.ws is None:
            return
        if not self.acked and not force:                 # (no answer to the last one: the connection's dead)
            self._reconnect(resume=True)
            return
        self.acked = False
        self._send(1, self.seq)
