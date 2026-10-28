"""Soul and Song on Telegram (telegram.py) - with a stand-in for Telegram: nothing goes online. Linking a bot (and
labelling it an AI), who may talk with it (the user by a code, the people they invite by theirs, anyone else told once
that it's private), listening and sending, a Companion writing first (and when it may not), guests' conversations kept
out of retraining, and the window: each message to the open Companion and its reply back, the window and Telegram
taking turns, and - on its own - listening on with the window closed."""
import json
import threading
import time
from datetime import datetime, timedelta

import support

from soulsong import companion as C
from soulsong import interlink as I
from soulsong import paths, telegram
from soulsong.paths import project

TEMPLATES = project()
support.needs(TEMPLATES / "Mind L1 - Mind Resources.txt", "the Companion Project's mind files in Local Storage")
TOKEN = "123456:TEST-TOKEN-NOT-A-REAL-ONE"
OWNER, GUEST, STRANGER = 1111, 2222, 3333


class FakeTelegram:
    """Telegram's Bot API as the tests see it: messages waiting are handed out to getUpdates (from where the offset
    says), what's sent is kept, and the first few getUpdates can be made to fail."""

    def __init__(self):
        self.calls, self.sent, self.inbox = [], [], []
        self.fail = 0

    def __call__(self, token, method, params=None, timeout=20):
        params = params or {}
        self.calls.append((method, params))
        if token != TOKEN:
            raise telegram.TelegramError("Unauthorized")
        if method == "getMe":
            return {"id": 5000, "is_bot": True, "first_name": "Soul and Song", "username": "SoulAndSongTestBot"}
        if method == "getUpdates":
            if self.fail:
                self.fail -= 1
                raise telegram.TelegramError("Bad Gateway")
            time.sleep(0.02)                            # (a long poll, very short)
            return [u for u in list(self.inbox) if u["update_id"] >= params.get("offset", 0)]
        if method == "getFile":
            return {"file_id": params["file_id"], "file_path": f"photos/{params['file_id']}.jpg"}
        if method == "sendMessage":
            assert len(params["text"]) <= 4096, "a message longer than Telegram takes"
            self.sent.append((params["chat_id"], params["text"]))
        return True

    def to(self, chat):
        return [text for c, text in list(self.sent) if c == chat]


_ids = [100]


def jpeg(colour="tomato", size=(320, 240)):
    """A picture as Telegram's file server would send it."""
    support.qapp()
    from PySide6.QtCore import QBuffer, QByteArray, QIODevice
    from PySide6.QtGui import QColor, QImage
    img = QImage(size[0], size[1], QImage.Format_RGB32)
    img.fill(QColor(colour))
    data = QByteArray()
    buf = QBuffer(data)
    buf.open(QIODevice.WriteOnly)
    img.save(buf, "JPG")
    buf.close()
    return bytes(data)


def photo(user, caption="", first="Jason"):
    """A photo message: Telegram sends each size it has, smallest first."""
    u = message(user, "", first)
    del u["message"]["text"]
    u["message"]["photo"] = [{"file_id": f"small-{u['update_id']}", "width": 90, "height": 60, "file_size": 900},
                             {"file_id": f"big-{u['update_id']}", "width": 1280, "height": 853, "file_size": 99000}]
    if caption:
        u["message"]["caption"] = caption
    return u


def message(user, text, first="Jason", chat_type="private", date=None):
    _ids[0] += 1
    return {"update_id": _ids[0], "message": {
        "message_id": _ids[0], "date": int(date or time.time()), "text": text,
        "chat": {"id": user, "type": chat_type}, "from": {"id": user, "is_bot": False, "first_name": first}}}


def test_linking_labels_it_an_ai():
    """Linking: the token checked with Telegram and kept, the bot described as an AI; a wrong token isn't kept"""
    api = FakeTelegram()
    folder = support.scratch("link")
    link = telegram.Link(folder, api=api)
    assert not link.ready()
    try:
        link.connect("654321:WRONG")
        raise AssertionError("a wrong token was accepted")
    except telegram.TelegramError:
        pass
    assert not link.ready() and not (folder / "telegram.json").exists(), "a wrong token was kept"
    assert link.connect(f"  {TOKEN} ") == "SoulAndSongTestBot" and link.ready()
    said = {method: params for method, params in api.calls if method.startswith("setMy")}
    long, short = said["setMyDescription"]["description"], said["setMyShortDescription"]["short_description"]
    assert "AI" in long and "not by a person" in long and len(long) <= 512, long
    assert "AI" in short and "not a person" in short and len(short) <= 120, short
    kept = json.loads((folder / "telegram.json").read_text(encoding="utf-8"))
    assert kept["token"] == TOKEN and kept["bot"]["username"] == "SoulAndSongTestBot", kept
    again = telegram.Link(folder, api=api)
    assert again.ready(), "the link wasn't remembered"
    again.forget()
    assert not telegram.Link(folder, api=api).ready(), "unlinking didn't forget the token"


def test_who_may_talk():
    """Who may talk: the user by their code, a guest by theirs (once, for a week); anyone else told once; no groups"""
    link = telegram.Link(support.scratch("who"), api=FakeTelegram())
    link.connect(TOKEN)
    kind = lambda u: (link.classify(u) or {}).get("kind")                       # noqa: E731
    assert kind(message(OWNER, "hi")) == "stranger", "someone unknown wasn't told it's private"
    assert kind(message(OWNER, "hi again")) is None, "someone unknown was told twice"
    code = link.code("owner")
    linked = link.classify(message(OWNER, code))
    assert linked["kind"] == "linked" and link.owner == {"id": OWNER, "name": "Jason", "chat": OWNER}, link.owner
    assert kind(message(OWNER, "/start")) is None, "/start on its own went to the Companion"
    talk = link.classify(message(OWNER, "How are you?"))
    assert talk["kind"] == "owner" and talk["text"] == "How are you?", talk
    assert kind(message(OWNER, code)) == "owner", "a code worked twice"
    invite = link.code("guest", "Sam")
    joined = link.classify(message(GUEST, f"/start {invite}", first="Samuel"))
    assert joined["kind"] == "invited" and joined["name"] == "Sam", joined          # (the name the user gave)
    hello = link.classify(message(GUEST, "Hello there", first="Samuel"))
    assert hello["kind"] == "guest" and hello["name"] == "Sam" and hello["text"] == "Hello there", hello
    old = link.code("guest", "Old")
    link.data["codes"][old]["made"] -= 8 * 86400
    assert kind(message(STRANGER, old)) == "stranger", "a code older than a week still worked"
    assert kind(message(OWNER, "in a group", chat_type="group")) is None, "a group chat was answered"
    photo = message(OWNER, "x")
    del photo["message"]["text"]
    assert kind(photo) is None, "a message without words went to the Companion"
    link.remove_guest(GUEST)
    assert kind(message(GUEST, "Still here?")) == "stranger", "a removed guest could still talk"


def test_pictures_and_other_things():
    """Pictures: a photo (its biggest size) and its caption, a picture sent as a file, a sticker (a still one as a
    picture); fetched from Telegram's file server; voice messages and the like get a note instead"""
    fetched = []
    link = telegram.Link(support.scratch("pictures"), api=FakeTelegram(),
                         files=lambda url: fetched.append(url) or b"JPEG")
    link.connect(TOKEN)
    link.classify(message(OWNER, link.code("owner")))
    seen = link.classify(photo(OWNER, "Look!"))
    assert seen["kind"] == "owner" and seen["text"] == "Look!", seen
    assert seen["picture"]["file_id"].startswith("big-") and seen["other"] is None, seen
    assert link.classify(photo(OWNER))["text"] == "", "a photo without words"
    doc = message(OWNER, "")
    del doc["message"]["text"]
    doc["message"]["document"] = {"file_id": "doc-1", "mime_type": "image/png", "file_size": 5000}
    assert link.classify(doc)["picture"]["file_id"] == "doc-1"
    doc["message"]["document"] = {"file_id": "doc-2", "mime_type": "application/pdf", "file_size": 5000}
    assert link.classify(doc)["other"] == "files" and link.classify(doc)["picture"] is None
    sticker = message(OWNER, "")
    del sticker["message"]["text"]
    sticker["message"]["sticker"] = {"file_id": "st-1", "emoji": "\U0001F431", "is_animated": False, "is_video": False}
    still = link.classify(sticker)
    assert still["picture"]["file_id"] == "st-1" and still["text"] == "(a sticker: \U0001F431)", still
    sticker["message"]["sticker"]["is_animated"] = True
    moving = link.classify(sticker)
    assert moving["picture"] is None and moving["text"] == "(a sticker: \U0001F431)", moving
    voice = message(OWNER, "")
    del voice["message"]["text"]
    voice["message"]["voice"] = {"file_id": "v-1", "duration": 3}
    said = link.classify(voice)
    assert said["kind"] == "owner" and said["other"] == "voice messages" and not said["picture"], said
    assert link.download("big-1") == b"JPEG"
    assert fetched == [f"https://api.telegram.org/file/bot{TOKEN}/photos/big-1.jpg"], fetched


def test_listening_and_sending():
    """Listening: new messages in order, where it's up to kept (nothing twice), errors waited out; long replies in
    pieces Telegram takes, broken between paragraphs"""
    api = FakeTelegram()
    folder = support.scratch("poll")
    link = telegram.Link(folder, api=api)
    link.connect(TOKEN)
    first, second = message(OWNER, "one"), message(OWNER, "two")
    api.inbox += [first, second]
    api.fail = 1
    got, stop = [], threading.Event()

    def deliver(update):
        got.append(update["message"]["text"])
        if len(got) == 2:
            stop.set()
    t = threading.Thread(target=link.poll, args=(deliver, stop), kwargs={"wait": 1}, daemon=True)
    t.start()
    t.join(15)
    assert not t.is_alive() and got == ["one", "two"], got
    assert telegram.Link(folder, api=api).data["offset"] == second["update_id"] + 1, "where it's up to wasn't kept"
    asked = [p for m, p in api.calls if m == "getUpdates"]
    assert asked[-1]["allowed_updates"] == ["message"] and asked[-1]["timeout"] == 1, asked[-1]
    again, stop2 = [], threading.Event()
    t = threading.Thread(target=telegram.Link(folder, api=api).poll, args=(again.append, stop2), kwargs={"wait": 1},
                         daemon=True)
    t.start()
    time.sleep(0.3)
    stop2.set()
    t.join(5)
    assert again == [], "a message was handed on twice"
    reply = "\n\n".join(f"Paragraph {i}. " + "words " * 150 for i in range(12))
    link.send(OWNER, reply)
    pieces = api.to(OWNER)
    assert len(pieces) >= 3 and all(p.startswith("Paragraph") for p in pieces), [p[:20] for p in pieces]
    assert " ".join(pieces).split() == reply.split(), "words were lost between the pieces"


class Scripted:
    """The model, scripted: free time's choice and thoughts, and - in turn - whether to write to the user."""

    def __init__(self, reach_replies):
        self.reach_replies, self.asked = list(reach_replies), []

    def ask(self, messages, done, chunk=None, max_tokens=700, temperature=0.8):
        last = messages[-1]["content"]
        self.asked.append(last)
        if "on Telegram now" in last:
            return done(self.reach_replies.pop(0), None)
        if "This hour is your own" in last:
            return done("THINK: the sea", None)
        return done("The sea keeps its own time.", None)

    def stop(self):
        pass


def test_writing_first():
    """Writing first: only when linked and allowed, the user away an hour, outside quiet hours, three hours apart and
    twice a day at most; NO sends nothing; what's sent is kept in the conversation; after free time it may write"""
    clock = {"t": datetime(2026, 10, 28, 12, 0)}
    folder = support.scratch("reach", "Lyra")
    C.create(folder, TEMPLATES, "Tester", "Lyra", "", "test")
    brain = Scripted(["NO", "Thinking of you - the tide's going out.", "Telegram is down?", "Me again.",
                      "I spent an hour thinking about the sea."])
    c = C.Companion(folder, brain, now=lambda: clock["t"], recall=False)
    c.cfg.update(first_boot_done=True, last_day=c.day_key(), time_checks=False, dreams=False, free_per_day=99)
    sent = []

    def away(hours=2):
        c.cfg["last_seen"] = (clock["t"] - timedelta(hours=hours)).isoformat()
    away()
    assert not c.reach_ok(), "it could write without Telegram linked"
    c.reach = sent.append
    away(0.5)
    assert not c.reach_ok(), "it wrote with the user only just away"
    for hour, ok in ((23, False), (3, False), (7, False), (8, True), (21, True), (22, False), (12, True)):
        clock["t"] = datetime(2026, 10, 28, hour, 0)
        away()
        assert c.reach_ok() is ok, f"at {hour}:00 (quiet from 22:00 to 8:00)"
    c.cfg["reach_out"] = False
    assert not c.reach_ok(), "it wrote with writing first switched off"
    c.cfg["reach_out"] = True
    c._push(lambda n: c._reach_out(n, "you read about tide pools"))
    assert c.idle() and sent == [], "NO was sent"
    assert "Just now you read about tide pools." in brain.asked[-1], brain.asked[-1]
    c._push(lambda n: c._reach_out(n, "you read about tide pools"))
    assert sent == ["Thinking of you - the tide's going out."], sent
    assert c.history[-1] == {"role": "assistant", "content": sent[0], "t": "2026-10-28 12:00"}, c.history[-1]
    raw = [json.loads(ln) for ln in (folder / "Raw Logs" / "2026-10-28.jsonl").read_text("utf-8").splitlines()]
    assert [(e["kind"], e["text"]) for e in raw[-2:]] == [("system", "Lyra wrote to Tester on Telegram:"),
                                                          ("companion", sent[0])], raw[-2:]
    clock["t"] += timedelta(hours=2)
    away()
    assert not c.reach_ok(), "it wrote again within three hours"

    def down(_text):
        raise telegram.TelegramError("Bad Gateway")
    clock["t"] += timedelta(hours=1, minutes=1)
    away()
    c.reach = down
    c._push(lambda n: c._reach_out(n, "you rested"))
    assert c.cfg["reach_by_day"] == {"2026-10-28": 1}, "a message that didn't go was counted"
    c.reach = sent.append
    c._push(lambda n: c._reach_out(n, "you rested"))
    assert sent[-1] == "Me again." and c.cfg["reach_by_day"] == {"2026-10-28": 2}, c.cfg["reach_by_day"]
    clock["t"] += timedelta(hours=3, minutes=1)
    away()
    assert not c.reach_ok(), "it wrote more than twice in a day"
    clock["t"] = datetime(2026, 10, 29, 12, 0)                  # (a new day: free time, and then a message)
    away()
    c._push(c._free_time)
    assert c.idle() and sent[-1] == "I spent an hour thinking about the sea.", sent
    assert "Just now you thought about the sea" in brain.asked[-1], brain.asked[-1]


def test_guests_stay_out_of_retraining():
    """Retraining: conversations with people the user invited are left out - unless the user says otherwise"""
    from soulsong import retrain
    folder = support.scratch("retrain guests", "Lyra")
    C.create(folder, TEMPLATES, "Tester", "Lyra", "", "test")
    c = C.Companion(folder, None, recall=False)
    c.cfg.update(first_boot_done=True)
    rows = [{"t": "2026-10-28 09:00", "kind": "user", "who": "Tester", "text": "Good morning, Lyra."},
            {"t": "2026-10-28 09:01", "kind": "companion", "who": "Lyra", "text": "Good morning! The sea was loud."},
            {"t": "2026-10-28 18:00", "kind": "other", "who": "Sam (on Telegram)", "text": "Hi Lyra, I'm Sam."},
            {"t": "2026-10-28 18:01", "kind": "companion", "who": "Lyra", "text": "Hello, Sam - welcome."}]
    (folder / "Raw Logs").mkdir(exist_ok=True)
    (folder / "Raw Logs" / "2026-10-28.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows),
                                                          encoding="utf-8")
    text = json.dumps(retrain._talk(c))
    assert "Good morning, Lyra." in text and "Sam" not in text, "a guest's conversation would be trained on"
    c.cfg["retrain_guests"] = True
    assert "Sam (on Telegram): Hi Lyra, I'm Sam." in json.dumps(retrain._talk(c)), "allowed, it was still left out"


def test_the_window_on_telegram():
    """The window: linking, the user and a guest talking from Telegram (and answered there), the window and Telegram
    taking turns, a stranger turned away, messages waiting for the model, the settings and How to connect, and
    listening on when closed"""
    support.qapp()
    caught = support.catch_errors()
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QCheckBox, QDialog, QLabel, QPushButton, QSpinBox, QTextBrowser
    import soulsong.app as A
    from soulsong import automation
    support.no_engines()                              # (before the window: it opens the Companion, and its model)
    base = support.scratch("telegram window")
    A.companions = paths.companions = automation.companions = I.companions = lambda: base
    folder = base / "companion-test"
    C.create(folder, TEMPLATES, "Tester", "Lyra")
    cfg = json.loads((folder / "companion.json").read_text(encoding="utf-8"))
    cfg.update(first_boot_done=True, last_day="2099-01-01", dreams=False, time_checks=False, free_time=False)
    (folder / "companion.json").write_text(json.dumps(cfg), encoding="utf-8")
    api = FakeTelegram()
    telegram.Link(base, api=api).connect(TOKEN)        # (the bot made and linked; the user not yet)
    asked = []

    def ask(messages, done, chunk=None, max_tokens=700, temperature=0.8):
        asked.append(messages[-1]["content"])
        QTimer.singleShot(10, lambda: done("I'm here, and glad you are too.", ""))

    w = A.SoulAndSong(None)
    fetched = []
    w.tg = telegram.Link(base, api=api, files=lambda url: fetched.append(url) or jpeg())   # (the stand-in Telegram,
    #                                                                                   before it starts listening)
    w.load_model = lambda *a, **k: None
    w.brain.ask = ask
    w.brain.engine.ready = True
    w.resize(1280, 800)
    w.show()
    w.fill_companions(select=str(folder))
    support.pump(0.6)
    assert w.comp is not None and w.comp.name == "Lyra", "the Companion didn't open"
    assert w._tg_thread is not None and w._tg_thread.is_alive(), "it isn't listening"
    assert w.comp.reach is None, "it could write first before the user was linked"
    w.comp.cfg["last_day"] = w.comp.day_key()

    def answered(chat, n):
        assert support.pump(10, until=lambda: len(api.to(chat)) > n), f"nothing was sent to {chat}"
        return api.to(chat)[-1]
    # linking the user's own account
    api.inbox.append(message(OWNER, w.tg.code("owner")))
    assert answered(OWNER, 0) == telegram.LINKED.format(companion="Lyra")
    assert w.comp.reach is not None and "Telegram is linked" in w.chat.toPlainText()
    # the user, from their phone
    api.inbox.append(message(OWNER, "Hello from my phone!"))
    assert answered(OWNER, 1) == "I'm here, and glad you are too."
    assert "writing to you on Telegram" in asked[-1] and "Hello from my phone!" in asked[-1], asked[-1]
    assert w.comp.cfg["channel"] == "telegram" and any(m == "sendChatAction" for m, _p in api.calls)
    # back at the computer: the window's answer stays in the window
    w.composer.setPlainText("I'm back at the desk.")
    w.send()
    assert support.pump(10, until=lambda: w.comp.idle() and len(asked) == 2), "the window's message wasn't answered"
    support.pump(0.2)
    assert "back at the computer" in asked[-1] and w.comp.cfg["channel"] == "window", asked[-1]
    assert len(api.to(OWNER)) == 2, "the window's answer went to Telegram"
    # a guest, invited
    api.inbox.append(message(GUEST, w.tg.code("guest", "Sam"), first="Samuel"))
    welcome = answered(GUEST, 0)
    assert all(bit in welcome for bit in ("Sam", "Lyra", "AI", "Tester", "not by a person")), welcome
    api.inbox.append(message(GUEST, "Hi Lyra, I'm Sam.", first="Samuel"))
    assert answered(GUEST, 1) == "I'm here, and glad you are too."
    assert "someone Tester invited" in asked[-1] and "Sam (on Telegram)" in w.chat.toPlainText(), asked[-1]
    raw = (folder / "Raw Logs" / f"{w.comp.day_key()}.jsonl").read_text(encoding="utf-8")
    assert '"who": "Sam (on Telegram)"' in raw and w.comp.cfg["guests_met"] == [GUEST]
    # a stranger: told it's private, and the Companion never hears it
    n = len(asked)
    api.inbox.append(message(STRANGER, "Who are you?", first="Eve"))
    assert answered(STRANGER, 0) == telegram.PRIVATE and len(asked) == n
    # sent hours ago, while Soul and Song was closed
    api.inbox.append(message(OWNER, "Sent this earlier.", date=time.time() - 3 * 3600))
    answered(OWNER, 2)
    assert "sent 3 hours ago, while Soul and Song was closed" in asked[-1], asked[-1]
    # a message while the model's loading waits for it
    w.brain.engine.ready = False
    api.inbox.append(message(OWNER, "Are you there?"))
    assert support.pump(5, until=lambda: w._tg_waiting), "the message didn't wait for the model"
    assert len(api.to(OWNER)) == 3, "it answered before the model was ready"
    w.brain.engine.ready = True
    w._ready(True)
    assert answered(OWNER, 3) == "I'm here, and glad you are too." and not w._tg_waiting
    # pictures: a photo with words, fetched and kept - and words sent right after it still come after it
    w.brain.engine.vision = True                      # (as if its vision add-on were loaded)
    n, before = len(api.to(OWNER)), len(asked)
    api.inbox += [photo(OWNER, "Look at this!"), message(OWNER, "Isn't it red?")]
    assert support.pump(10, until=lambda: len(api.to(OWNER)) >= n + 2 and w.comp.idle()), "the photo wasn't answered"
    kept = list((folder / "Pictures").glob("* Telegram.jpg"))
    assert len(kept) == 1 and len(fetched) == 1 and "/photos/big-" in fetched[0], (kept, fetched)
    said = [m for m in w.comp.history if m["role"] == "user"][-2:]
    assert said[0]["content"] == "Look at this!" and said[0].get("picture") and said[1]["content"] == "Isn't it red?"
    assert isinstance(asked[before], list) and asked[before][1]["type"] == "image_url", "the model wasn't shown it"
    assert "<img" in w.chat.toHtml()
    # a voice message: a note back, and the Companion isn't bothered
    n, before = len(api.to(OWNER)), len(asked)
    voice = message(OWNER, "")
    del voice["message"]["text"]
    voice["message"]["voice"] = {"file_id": "v-1", "duration": 3}
    api.inbox.append(voice)
    assert answered(OWNER, n) == telegram.CANT.format(what="voice messages") and len(asked) == before
    w.brain.engine.vision = False
    # writing first, and a new Companion announced
    n = len(api.to(OWNER))
    w.comp.reach("A message from Lyra.")
    assert answered(OWNER, n) == "A message from Lyra."
    w.tg.data["last_companion"] = "Brook"
    w._tg_wire(announce=True)
    assert answered(OWNER, n + 1) == "(You're talking with Lyra now.)" and w.tg.data["last_companion"] == "Lyra"
    # the settings
    seen = {}

    def settle():
        d = next(x for x in w.findChildren(QDialog) if x.isVisible())
        seen["text"] = " ".join(label.text() for label in d.findChildren(QLabel))
        next(b for b in d.findChildren(QCheckBox) if b.text().startswith("Lyra may write to me first")).setChecked(False)
        next(s for s in d.findChildren(QSpinBox) if s.suffix() == " a day at most").setValue(3)
        next(b for b in d.findChildren(QPushButton) if b.text() == "How to connect...").click()
        seen["how"] = next(x for x in d.findChildren(QDialog) if x.isVisible())
        seen["steps"] = seen["how"].findChild(QTextBrowser).toPlainText()
        d.accept()
    QTimer.singleShot(300, settle)
    w._tg_dialog()
    assert "@SoulAndSongTestBot" in seen.get("text", "") and "Jason's account" in seen["text"], seen
    assert w.comp.cfg["reach_out"] is False and w.comp.cfg["reach_per_day"] == 3, "the settings weren't kept"
    assert all(bit in seen.get("steps", "") for bit in ("@BotFather", "/newbot", "Soul and Song", "token", "Link",
                                                        "Invite someone...")), seen.get("steps")
    assert not seen["how"].isVisible(), "How to connect stayed open after the Telegram window closed"
    # closed on its own, it listens on from the notification area; inside a computer, closing closes it
    real_tray, shown = A.QSystemTrayIcon, []

    class Tray:
        @staticmethod
        def isSystemTrayAvailable():
            return True
    A.QSystemTrayIcon = Tray
    w._tray_show = lambda: shown.append(True)
    w._inside_computer = lambda: False
    try:
        w.close()
        assert shown == [True] and not w.isVisible() and w._tg_thread.is_alive(), "it stopped listening"
        n = len(api.to(OWNER))
        api.inbox.append(message(OWNER, "Still there?"))
        answered(OWNER, n)
        w._tray_open()
        assert w.isVisible()
        w._inside_computer = lambda: True
        w.close()
        assert shown == [True] and not w.isVisible(), "inside a computer, it went to the notification area"
        w.show()
        w._inside_computer = lambda: False
        w._tray_quit()
        assert shown == [True] and not w.isVisible(), "Stop listening and quit didn't close it"
    finally:
        A.QSystemTrayIcon = real_tray
    w.shutdown()
    w._tg_thread.join(5)
    assert not w._tg_thread.is_alive(), "it was still listening after it closed"
    support.no_errors(caught)


if __name__ == "__main__":
    support.main(globals())
