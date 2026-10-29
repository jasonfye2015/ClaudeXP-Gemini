"""Soul and Song on Discord (discordlink.py) - with stand-ins for Discord's REST API and its gateway: nothing goes
online. Linking (and the app described as an AI), who may talk (the user and invited guests by code, anyone else told
once; a server's channels and bots never), the gateway (who it is, heartbeats, a dead connection noticed, picking up
after a drop, a refused token), reading back what came while it was away, Discord-sized pieces, and the window:
answered on Discord, pictures, writing first where the user last wrote from, and the Discord window with its How to
connect."""
import json
import time
from datetime import datetime, timedelta, timezone

import support

from PySide6.QtCore import QObject, QTimer, Signal

from soulsong import companion as C
from soulsong import discordlink
from soulsong import interlink as I
from soulsong import paths
from soulsong.paths import project

TEMPLATES = project()
support.needs(TEMPLATES / "Mind L1 - Mind Resources.txt", "the Companion Project's mind files in Local Storage")
TOKEN = "TEST.TOKEN.NOT-A-REAL-ONE"
OWNER, GUEST, STRANGER = "111", "222", "333"
support.qapp()


class FakeDiscord:
    """Discord's REST API as the tests see it: what's sent is kept, and each conversation's past can be read back."""

    def __init__(self):
        self.calls, self.sent, self.past = [], [], {}

    def __call__(self, token, method, path, body=None, timeout=20):
        self.calls.append((method, path, body))
        if token != TOKEN:
            raise discordlink.DiscordError("401: Unauthorized")
        if (method, path) == ("GET", "/users/@me"):
            return {"id": "5000", "username": "soul-and-song", "global_name": "Soul and Song", "bot": True}
        if (method, path) == ("GET", "/applications/@me"):
            return {"id": "5001", "name": "Soul and Song"}
        if (method, path) == ("PATCH", "/applications/@me"):
            return {"id": "5001", "description": body["description"]}
        if method == "POST" and path.endswith("/messages"):
            assert len(body["content"]) <= 2000 and body["allowed_mentions"] == {"parse": []}, body
            self.sent.append((path.split("/")[2], body["content"]))
            return {"id": "9"}
        if method == "POST" and path.endswith("/typing"):
            return None
        if method == "GET" and "/messages?after=" in path:
            chat, after = path.split("/")[2], int(path.split("after=")[1].split("&")[0])
            return [m for m in reversed(self.past.get(chat, [])) if int(m["id"]) > after]    # (newest first)
        raise AssertionError(f"unexpected {method} {path}")

    def to(self, chat):
        return [text for c, text in list(self.sent) if c == chat]


SOCKETS = []


class FakeSocket(QObject):
    """The gateway's WebSocket, as a test sees it: what's sent is kept; a test says what Discord says. Heartbeats
    are answered unless it's told not to (a dead connection)."""
    connected = Signal()
    disconnected = Signal()
    textMessageReceived = Signal(str)

    def __init__(self):
        super().__init__()
        self.urls, self.out, self.code, self.answers = [], [], 1000, True
        SOCKETS.append(self)

    def open(self, url):
        self.urls.append(url.toString())

    def sendTextMessage(self, text):
        msg = json.loads(text)
        self.out.append(msg)
        if msg["op"] == 1 and self.answers:
            QTimer.singleShot(0, lambda: self.feed(11))

    def close(self, *_a):
        pass

    def closeCode(self):
        return self.code

    def feed(self, op, d=None, t=None, s=None):
        self.textMessageReceived.emit(json.dumps({"op": op, "d": d, "t": t, "s": s}))

    def drop(self, code):
        self.code = code
        self.disconnected.emit()


discordlink.make_socket = FakeSocket
_ids = [1000]


def dm(user, text, name="Jason", when=None, **more):
    """A direct message to the bot, as the gateway delivers it."""
    _ids[0] += 1
    m = {"id": str(_ids[0]), "channel_id": f"dm-{user}", "content": text, "flags": 0, "attachments": [],
         "author": {"id": user, "username": name.lower(), "global_name": name},
         "timestamp": (when or datetime.now(timezone.utc)).isoformat()}
    m.update(more)
    return m


def _link(name, api=None, files=None):
    link = discordlink.Link(support.scratch("discord", name), api=api or FakeDiscord(), files=files)
    link.connect(TOKEN)
    return link


def test_linking_says_its_an_ai():
    """Linking: the token checked with Discord and kept, the app described as an AI, its page for adding it to a
    server; a wrong token isn't kept"""
    api = FakeDiscord()
    folder = support.scratch("discord", "link")
    link = discordlink.Link(folder, api=api)
    try:
        link.connect("WRONG")
        raise AssertionError("a wrong token was accepted")
    except discordlink.DiscordError:
        pass
    assert not link.ready() and not (folder / "discord.json").exists(), "a wrong token was kept"
    assert link.connect(f" {TOKEN} ") == "Soul and Song" and link.ready()
    said = next(body for method, path, body in api.calls if method == "PATCH")
    assert "AI" in said["description"] and "not by a person" in said["description"], said
    assert len(said["description"]) <= 400, "too long for Discord's description"
    assert "client_id=5001&scope=bot" in link.invite_url(), link.invite_url()
    kept = json.loads((folder / "discord.json").read_text(encoding="utf-8"))
    assert kept["token"] == TOKEN and kept["bot"]["app"] == "5001", kept
    link.forget()
    assert not discordlink.Link(folder, api=api).ready(), "unlinking didn't forget the token"


def test_who_may_talk():
    """Who may talk: the user by their code, a guest by theirs; anyone else told once; never a server's channel or
    a bot; pictures, stickers, and a note for voice messages"""
    link = _link("who")
    kind = lambda m: (link.classify(m) or {}).get("kind")                       # noqa: E731
    assert kind(dm(OWNER, "hi")) == "stranger" and kind(dm(OWNER, "hi again")) is None
    assert link.classify(dm(OWNER, link.code("owner")))["kind"] == "linked"
    assert link.owner == {"id": OWNER, "name": "Jason", "chat": f"dm-{OWNER}"}, link.owner
    talk = link.classify(dm(OWNER, "How are you?"))
    assert talk["kind"] == "owner" and talk["text"] == "How are you?" and talk["date"] > 0, talk
    joined = link.classify(dm(GUEST, link.code("guest", "Sam"), name="Samuel"))
    assert joined["kind"] == "invited" and joined["name"] == "Sam", joined
    assert link.classify(dm(GUEST, "Hello", name="Samuel"))["name"] == "Sam"
    assert kind(dm(OWNER, "in a server", guild_id="77")) is None, "a server's channel was answered"
    bot = dm("999", "beep")
    bot["author"]["bot"] = True
    assert kind(bot) is None, "a bot was answered"
    pic = link.classify(dm(OWNER, "Look!", attachments=[{"id": "a1", "content_type": "image/png", "size": 9000,
                                                         "url": "https://cdn.discordapp.com/a1.png"}]))
    assert pic["picture"]["url"].endswith("a1.png") and pic["text"] == "Look!", pic
    sticker = link.classify(dm(OWNER, "", sticker_items=[{"id": "s1", "name": "wave", "format_type": 1}]))
    assert sticker["text"] == "(a sticker: wave)" and sticker["picture"]["url"].endswith("/s1.png"), sticker
    voice = link.classify(dm(OWNER, "", flags=1 << 13, attachments=[{"id": "v1", "content_type": "audio/ogg",
                                                                      "size": 100, "url": "https://x/v1.ogg"}]))
    assert voice["other"] == "voice messages" and not voice["picture"], voice
    assert link.data["read"][f"dm-{OWNER}"] == str(_ids[0]), "it doesn't know how far it has read"


def test_sending_and_reading_back():
    """Long replies in pieces Discord takes, broken between paragraphs; a picture fetched from its address; and
    what came while it was away read back, oldest first, from where it had read to"""
    api, fetched = FakeDiscord(), []
    link = _link("send", api, files=lambda url: fetched.append(url) or b"PNG")
    link.classify(dm(OWNER, link.code("owner")))
    reply = "\n\n".join(f"Paragraph {i}. " + "words " * 60 for i in range(12))
    link.send(f"dm-{OWNER}", reply)
    pieces = api.to(f"dm-{OWNER}")
    assert len(pieces) >= 3 and all(p.startswith("Paragraph") for p in pieces), [p[:12] for p in pieces]
    assert " ".join(pieces).split() == reply.split(), "words were lost between the pieces"
    assert link.download({"url": "https://cdn.discordapp.com/x.png"}) == b"PNG" and fetched
    read = link.data["read"][f"dm-{OWNER}"]
    missed = [dm(OWNER, "while you were away"), dm(OWNER, "and this")]
    api.past[f"dm-{OWNER}"] = [{"id": str(int(read) - 1), "content": "old"}] + missed
    got = []
    link.catch_up(got.append)
    assert [m["content"] for m in got] == ["while you were away", "and this"], got


def test_the_gateway():
    """The gateway: it says who it is (direct messages only), beats, hands on messages, notices a dead connection,
    picks up where it was after a drop - and stops, saying why, when Discord refuses the token"""
    api = FakeDiscord()
    link = _link("gateway", api)
    got, said = [], []
    listener = discordlink.Listener(link, got.append, on_status=said.append)
    listener.pause = 0.05
    n = len(SOCKETS)
    listener.start()
    ws = SOCKETS[-1]
    assert len(SOCKETS) == n + 1 and ws.urls == [discordlink.GATEWAY], ws.urls
    ws.feed(10, {"heartbeat_interval": 60})
    ident = ws.out[0]
    assert ident["op"] == 2 and ident["d"]["token"] == TOKEN and ident["d"]["intents"] == 1 << 12, ident
    ws.feed(0, {"session_id": "S1", "resume_gateway_url": "wss://resume.example"}, "READY", 1)
    assert support.pump(2, until=lambda: sum(o["op"] == 1 for o in ws.out) >= 2), "it doesn't beat"
    ws.feed(0, dm(OWNER, "hello"), "MESSAGE_CREATE", 2)
    assert got and got[-1]["content"] == "hello"
    assert any(o == {"op": 1, "d": 2} for o in ws.out[-3:]) or support.pump(
        1, until=lambda: {"op": 1, "d": 2} in ws.out), "a beat didn't say how far it had heard"
    ws.answers = False                                         # (the connection dies quietly: no answer to a beat)
    assert support.pump(2, until=lambda: len(SOCKETS) > n + 1), "a dead connection wasn't noticed"
    ws2 = SOCKETS[-1]
    assert ws2.urls[-1].startswith("wss://resume.example/?v=10"), ws2.urls
    ws2.feed(10, {"heartbeat_interval": 60})
    resume = ws2.out[0]
    assert resume["op"] == 6 and resume["d"]["session_id"] == "S1" and resume["d"]["seq"] == 2, resume
    ws2.feed(0, None, "RESUMED", 3)
    ws2.drop(1006)                                             # (dropped: it comes back by itself)
    assert support.pump(2, until=lambda: len(SOCKETS) > n + 2), "it didn't come back after a drop"
    ws3 = SOCKETS[-1]
    ws3.feed(10, {"heartbeat_interval": 60})
    ws3.drop(4004)                                             # (the token refused: no more tries)
    support.pump(0.3)
    assert not listener.alive() and said and "token" in said[-1], said
    assert len(SOCKETS) == n + 3, "it kept trying with a refused token"
    listener.stop()


def test_the_window_on_discord():
    """The window: the Discord window and How to connect; linking; answered on Discord; a picture; writing first
    where the user last wrote from (Telegram or Discord); the window's own answers stay in the window"""
    caught = support.catch_errors()
    from PySide6.QtWidgets import QDialog, QLabel, QPushButton, QTextBrowser
    import soulsong.app as A
    from soulsong import automation
    support.no_engines()                                      # (before the window: it opens the Companion)
    base = support.scratch("discord window")
    A.companions = paths.companions = automation.companions = I.companions = lambda: base
    folder = base / "companion-test"
    C.create(folder, TEMPLATES, "Tester", "Lyra")
    cfg = json.loads((folder / "companion.json").read_text(encoding="utf-8"))
    cfg.update(first_boot_done=True, last_day="2099-01-01", dreams=False, time_checks=False, free_time=False)
    (folder / "companion.json").write_text(json.dumps(cfg), encoding="utf-8")
    api, fetched = FakeDiscord(), []
    discordlink.Link(base, api=api).connect(TOKEN)
    asked = []

    def ask(messages, done, chunk=None, max_tokens=700, temperature=0.8):
        asked.append(messages[-1]["content"])
        QTimer.singleShot(10, lambda: done("Here, on Discord too.", ""))

    from test_pictures import _picture                          # (a picture to send)
    png = _picture(base / "sent.png", "teal").read_bytes()
    w = A.SoulAndSong(None)
    w.links["discord"] = discordlink.Link(base, api=api, files=lambda url: fetched.append(url) or png)
    w.load_model = lambda *a, **k: None
    w.brain.ask = ask
    w.brain.engine.ready = True
    w.brain.engine.vision = True
    w.resize(1280, 800)
    w.show()
    w.fill_companions(select=str(folder))
    n = len(SOCKETS)
    support.pump(0.6)
    assert w.comp is not None and w._listening("discord") and len(SOCKETS) == n + 1, "it isn't listening"
    ws, seq = SOCKETS[-1], [1]

    def say(m):
        seq[0] += 1
        ws.feed(0, m, "MESSAGE_CREATE", seq[0])

    def answered(chat, k):
        assert support.pump(10, until=lambda: len(api.to(chat)) > k), f"nothing was sent to {chat}"
        return api.to(chat)[-1]
    ws.feed(10, {"heartbeat_interval": 45000})
    ws.feed(0, {"session_id": "S", "resume_gateway_url": "wss://r"}, "READY", 1)
    chat = f"dm-{OWNER}"
    say(dm(OWNER, w.links["discord"].code("owner")))
    assert answered(chat, 0) == discordlink.LINKED.format(companion="Lyra")
    assert w.comp.reach is not None and "Discord is linked" in w.chat.toPlainText()
    say(dm(OWNER, "Hello from Discord!"))
    assert answered(chat, 1) == "Here, on Discord too."
    assert "writing to you on Discord" in asked[-1] and w.comp.cfg["messenger"] == "discord", asked[-1]
    # a picture
    say(dm(OWNER, "Look", attachments=[{"id": "a1", "content_type": "image/png", "size": 999,
                                        "url": "https://cdn.discordapp.com/a1.png"}]))
    assert answered(chat, 2) and support.pump(5, until=lambda: w.comp.idle())
    assert fetched == ["https://cdn.discordapp.com/a1.png"] and list((folder / "Pictures").glob("* Discord.jpg"))
    assert any(isinstance(a, list) for a in asked), "the model wasn't shown the picture"
    # writing first: where they last wrote from
    class Telegram:                                            # (Telegram linked too)
        data, owner, sent = {"background": True}, {"id": 1, "name": "Jason", "chat": 1}, []

        def ready(self):
            return True

        def send(self, chat, text):
            self.sent.append(text)
    w.links["telegram"] = tg = Telegram()
    w._msg_wire()
    k = len(api.to(chat))
    w.comp.reach("From Lyra, on Discord.")
    assert answered(chat, k) == "From Lyra, on Discord." and w.comp.reach_where() == "Discord"
    w.comp.cfg["messenger"] = "telegram"
    w.comp.reach("From Lyra, on Telegram.")
    assert support.pump(3, until=lambda: tg.sent == ["From Lyra, on Telegram."]) and w.comp.reach_where() == "Telegram"
    del w.links["telegram"]
    w._msg_wire()
    # back at the window: its answer stays here
    k = len(api.to(chat))
    w.composer.setPlainText("Back at the desk.")
    w.send()
    assert support.pump(10, until=lambda: w.comp.idle() and "back at the computer" in str(asked[-1]))
    support.pump(0.3)
    assert len(api.to(chat)) == k and w.comp.cfg["channel"] == "window", "the window's answer went to Discord"
    # a server's channel and a stranger
    say(dm(STRANGER, "hey", name="Eve"))
    assert answered(f"dm-{STRANGER}", 0) == discordlink.PRIVATE
    say(dm(OWNER, "in a server", guild_id="77"))
    support.pump(0.3)
    assert len(api.to(chat)) == k, "a server's channel was answered"
    # the Discord window, and How to connect
    seen = {}

    def look():
        d = next(x for x in w.findChildren(QDialog) if x.isVisible())
        seen["title"] = d.windowTitle()
        seen["text"] = " ".join(label.text() for label in d.findChildren(QLabel))
        seen["buttons"] = [b.text() for b in d.findChildren(QPushButton) if b.isVisibleTo(d)]
        next(b for b in d.findChildren(QPushButton) if b.text() == "How to connect...").click()
        how = next(x for x in d.findChildren(QDialog) if x.isVisible())
        seen["how"] = (how.windowTitle(), how.findChild(QTextBrowser).toPlainText())
        d.accept()
    QTimer.singleShot(300, look)
    w._msg_dialog("discord")
    assert seen.get("title") == "Soul and Song on Discord" and "Jason's account" in seen["text"], seen
    assert "Add it to a server..." in seen["buttons"] and "Unlink" in seen["buttons"], seen["buttons"]
    title, steps = seen["how"]
    assert title == "How to connect Soul and Song to Discord", title
    for bit in ("Developer Portal", "New Application", "Reset Token", "Add it to a server", "Authorize", "code"):
        assert bit in steps, f"How to connect doesn't say {bit!r}"
    sock = SOCKETS[-1]
    w.shutdown()
    assert not w._listening("discord") and sock.out, "it was still listening after it closed"
    support.no_errors(caught)


if __name__ == "__main__":
    support.main(globals())
