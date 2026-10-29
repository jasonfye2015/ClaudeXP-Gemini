"""Telegram, for a program's bot (Soul and Song's, Kithylin AI's): a bot of the user's own, made with Telegram's
@BotFather and given the program's name, answered by the program - so the user can talk to it from their phone.

The program asks Telegram for new messages while it's open (long polling over HTTPS - no server, nothing to
install, no port opened); Telegram keeps messages for a day, so ones sent while the PC was off are answered when
it's back. Only one copy of a program can listen to its bot at a time.

Who may talk to it: the user, linked by sending the bot a code the program shows; and anyone the user invites with
a code of their own. A guest is told, before anything else, that this is an AI and that its owner can read the
conversation; anyone else gets one line - private - and nothing more. Everything is labelled AI: the bot's
description and short description (the program's words) say so.

Kept in the program's folder (never in git), in telegram.json: the bot's token - a secret: whoever has it controls
the bot - who's linked, the invitation codes, and where the polling is up to."""
import json
import random
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

API = "https://api.telegram.org/bot{token}/{method}"
FILE = "https://api.telegram.org/file/bot{token}/{path}"
LIMIT = 4000                     # (Telegram's limit is 4096 characters a message)
PICTURE_LIMIT = 20 * 2**20       # (the most a bot may download; a phone's photo is far less)
OTHER = (("voice", "voice messages"), ("audio", "audio"), ("video_note", "video messages"), ("video", "videos"),
         ("animation", "GIFs"), ("document", "files"), ("location", "locations"), ("contact", "contacts"),
         ("poll", "polls"))
NAME = "Telegram"
INTRO = ("Talk with {who} from your phone, through a Telegram bot of your own - make it with Telegram's "
         "<b>@BotFather</b> (<b>How to connect...</b> below walks you through it), name it <b>{app}</b>, and "
         "paste the token it gives you here. The bot says it's an AI, in its description and to anyone who writes.")
TOKEN_HINT = "The bot's token, from @BotFather (keep it secret)"
HOW_HINT = "The setup, step by step: making the bot with @BotFather, and linking it here"
SETUP = """<h3>Connecting {app} to Telegram</h3>
<ol>
<li>In Telegram, search for <b>@BotFather</b> (the one with the blue tick) and press <b>Start</b>.</li>
<li>Send <b>/newbot</b>. When it asks for a name, send <b>{app}</b>.</li>
<li>It then asks for a username: one nobody else has, ending in "bot" - {handle}<i>YourName</i>Bot, say.</li>
<li>BotFather replies with a <b>token</b>: a long line of numbers and letters. Copy it, and keep it to yourself -
whoever has it controls the bot. (If you like, send <b>/setuserpic</b> to give the bot a picture.)</li>
<li>Back in {app}'s Telegram window, paste the token and click <b>Link</b>. {app} checks it with
Telegram, and sets the bot's description to say it's an AI.</li>
<li>The window then shows your bot's address (t.me/...) and a six-figure code. Open the bot, press <b>Start</b> and
send it the code. It answers "Linked."</li>
<li>Now just write to it - {sends}. To invite someone, click <b>Invite someone...</b> and give them
the code it shows.</li>
</ol>
<p><b>Good to know:</b> only one {app} can listen to a bot at a time - don't run it on its own and inside a
computer together. To keep it listening with the window closed, run {app} on its own (the launcher's
<b>APPS</b>): closing the window leaves an icon in the notification area - click it, or start {app}
again, to bring the window back. Chats with a bot aren't end-to-end encrypted - Telegram's servers carry them, as
with its ordinary chats.</p>"""


def setup(app, sends="words, or pictures"):
    """How to connect, step by step, for this program's bot."""
    return SETUP.format(app=app, handle=app.replace(" ", ""), sends=sends)


def intro(app, who):
    """The Telegram window's opening words: talking with who, through this program's bot."""
    return INTRO.format(app=app, who=who)


class TelegramError(Exception):
    pass


def call(token, method, params=None, timeout=20):
    """A Bot API method -> its result (raises TelegramError with Telegram's own words when it says no)."""
    data = json.dumps(params or {}).encode("utf-8")
    req = urllib.request.Request(API.format(token=token, method=method), data=data,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = json.loads(r.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        try:
            body = json.loads(e.read().decode("utf-8", "replace"))
        except ValueError:
            raise TelegramError(f"HTTP {e.code}") from None
    if not body.get("ok"):
        raise TelegramError(body.get("description") or "Telegram said no")
    return body.get("result")


def fetch(url, timeout=60):
    """A file from Telegram's file server, as bytes (a picture someone sent)."""
    with urllib.request.urlopen(url, timeout=timeout) as r:
        data = r.read(PICTURE_LIMIT + 1)
    if len(data) > PICTURE_LIMIT:
        raise TelegramError("too big")
    return data


def picture_of(m):
    """A message's picture: {"file_id", "emoji"} - a photo (its biggest size), a picture sent as a file, or a
    sticker that's a still picture - or None."""
    if m.get("photo"):
        biggest = max(m["photo"], key=lambda p: (p.get("width", 0) * p.get("height", 0), p.get("file_size", 0)))
        return {"file_id": biggest["file_id"], "emoji": ""}
    doc = m.get("document") or {}
    if str(doc.get("mime_type", "")).startswith("image/") and doc.get("file_size", 0) <= PICTURE_LIMIT:
        return {"file_id": doc["file_id"], "emoji": ""}
    sticker = m.get("sticker") or {}
    if sticker and not sticker.get("is_animated") and not sticker.get("is_video"):
        return {"file_id": sticker["file_id"], "emoji": sticker.get("emoji", "")}
    return None


def chunks(text, limit=LIMIT):
    """A long reply in pieces Telegram takes, broken at paragraphs or lines where it can."""
    text = (text or "").strip()
    out = []
    while len(text) > limit:
        cut = max(text.rfind("\n\n", 0, limit), text.rfind("\n", 0, limit))
        cut = cut if cut > limit // 2 else text.rfind(" ", 0, limit)
        cut = cut if cut > 0 else limit
        out.append(text[:cut].strip())
        text = text[cut:].strip()
    return out + ([text] if text else [])


class Link:
    """The bot and who's linked to it (telegram.json); polling, sending, and what each message is."""

    def __init__(self, folder, api=None, files=None, words=None):
        self.path = Path(folder) / "telegram.json"
        self.words = words or {}                 # (the program's: what its bot says it is - "description", "short")
        self.api = api or call
        self.files = files or fetch
        self.lock = threading.RLock()            # (the listener's thread and the window's both write it)
        try:
            self.data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            self.data = {}
        self.data.setdefault("guests", [])
        self.data.setdefault("codes", {})
        self.data.setdefault("told", [])
        self.data.setdefault("offset", 0)

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
        """Check a token with Telegram (getMe), keep it, and label the bot as an AI. Returns the bot's @username."""
        me = self.api(token.strip(), "getMe")
        with self.lock:
            self.data.update(token=token.strip(), bot={"id": me["id"], "username": me.get("username", ""),
                                                       "name": me.get("first_name", "")})
            self.save()
        self.label()
        return self.bot["username"]

    def label(self):
        """The bot's description and short description: it's an AI (best effort - the bot works either way)."""
        for method, key, text in (("setMyDescription", "description", self.words.get("description")),
                                  ("setMyShortDescription", "short_description", self.words.get("short"))):
            if not text:
                continue
            try:
                self.api(self.token, method, {key: text})
            except Exception:
                pass

    def forget(self):
        """Unlink: the token, the bot and everyone linked are forgotten (the bot itself is the user's, in Telegram)."""
        with self.lock:
            self.data = {"guests": [], "codes": {}, "told": [], "offset": 0}
            self.save()

    def code(self, kind, name=""):
        """A one-time code: "owner" links the user's own account, "guest" someone they invite (valid a week)."""
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
    def classify(self, update):
        """One update -> {"kind", "chat", "user", "name", "text", "date"}: kind is "owner" or "guest" (talk),
        "linked" or "invited" (a code just used), "stranger" (told once it's private), or None (nothing to do)."""
        with self.lock:
            return self._classify(update)

    def _classify(self, update):
        m = update.get("message") or update.get("edited_message")
        if not m or m.get("chat", {}).get("type") != "private":
            return None
        text = (m.get("text") or m.get("caption") or "").strip()
        picture = picture_of(m)
        sticker = (m.get("sticker") or {}).get("emoji")
        if not text and sticker is not None:
            text = f"(a sticker: {sticker})" if sticker else "(a sticker)"
        other = None if text or picture else next((what for key, what in OTHER if key in m), None)
        if not text and not picture and not other:
            return None
        sender = m.get("from") or {}
        uid = sender.get("id")
        name = " ".join(x for x in (sender.get("first_name"), sender.get("last_name")) if x) or \
            sender.get("username") or "someone"
        out = {"chat": m["chat"]["id"], "user": uid, "name": name, "text": text, "date": m.get("date"),
               "picture": picture, "other": other}
        word = text.split()[-1] if text.split() else ""
        code = self.data["codes"].get(word)
        if code and time.time() - code["made"] < 7 * 86400:
            del self.data["codes"][word]
            if code["for"] == "owner":
                self.data["owner"] = {"id": uid, "name": name, "chat": out["chat"]}
                kind = "linked"
            else:
                guest = {"id": uid, "name": code.get("name") or name, "chat": out["chat"], "since": time.time()}
                self.data["guests"] = [g for g in self.data["guests"] if g["id"] != uid] + [guest]
                out["name"] = guest["name"]
                kind = "invited"
            self.save()
            return dict(out, kind=kind)
        if text.startswith("/start") or text.startswith("/help"):
            text = ""
        said = text or picture or other
        if self.owner and uid == self.owner["id"]:
            return dict(out, kind="owner", text=text) if said else None
        guest = next((g for g in self.data["guests"] if g["id"] == uid), None)
        if guest:
            return dict(out, kind="guest", name=guest["name"], text=text) if said else None
        if uid in self.data["told"]:
            return None
        self.data["told"] = (self.data["told"] + [uid])[-200:]
        self.save()
        return dict(out, kind="stranger")

    def poll(self, deliver, stop, wait=25):
        """Until stop is set: Telegram's new messages, each to deliver(update) - on this thread (the caller passes
        them back to the window's). Errors wait and try again, longer each time."""
        pause = 2
        while not stop.is_set():
            if not self.ready():
                stop.wait(2)
                continue
            try:
                updates = self.api(self.token, "getUpdates", {"offset": self.data["offset"], "timeout": wait,
                                                              "allowed_updates": ["message"]}, timeout=wait + 15)
                pause = 2
            except Exception:
                stop.wait(pause)
                pause = min(120, pause * 2)
                continue
            for u in updates or []:
                with self.lock:
                    self.data["offset"] = u["update_id"] + 1
                deliver(u)
            if updates:
                self.save()

    # ---- what goes out ----
    def send(self, chat, text):
        for piece in chunks(text):
            self.api(self.token, "sendMessage", {"chat_id": chat, "text": piece})

    def download(self, picture):
        """A file someone sent (a picture: picture_of's, or its file_id), as bytes - asked of Telegram (getFile),
        then fetched."""
        file_id = picture["file_id"] if isinstance(picture, dict) else picture
        found = self.api(self.token, "getFile", {"file_id": file_id})
        if not found or not found.get("file_path"):
            raise TelegramError("Telegram didn't say where the file is")
        return self.files(FILE.format(token=self.token, path=found["file_path"]))

    def typing(self, chat):
        try:
            self.api(self.token, "sendChatAction", {"chat_id": chat, "action": "typing"})
        except Exception:
            pass


class Listener:
    """Telegram's messages, on a thread of its own (long polling), each to deliver(update)."""

    def __init__(self, link, deliver, on_status=None):
        self.link, self.deliver = link, deliver
        self.stopping = threading.Event()
        self.thread = threading.Thread(target=link.poll, args=(deliver, self.stopping), name="telegram-listener",
                                       daemon=True)

    def start(self):
        self.thread.start()

    def stop(self):
        self.stopping.set()

    def alive(self):
        return self.thread.is_alive() and not self.stopping.is_set()


# ---- the Telegram window's words ----
def waiting_text(link, code):
    name = link.bot["username"]
    return (f"Linked to <b>@{name}</b>. Now open it in Telegram (t.me/{name}), press Start, and send it this code to "
            f"link your account: <b>{code}</b>")


def linked_text(link):
    return f"Linked to <b>@{link.bot['username']}</b> - {link.owner['name']}'s account."


def invite_text(link, name, code):
    return (f"Give {name} this code: {code}\n\nThey open @{link.bot['username']} in Telegram, press Start and send "
            "it. It works once, for a week. They'll be told it's an AI, and that you can read the conversation.")
