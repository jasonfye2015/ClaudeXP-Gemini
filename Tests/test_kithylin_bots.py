"""Kithylin AI on Telegram and Discord - its own bots, in its own words, with stand-ins for Telegram and Discord and
for the model: nothing goes online and no model is started. Linking; each person a chat of their own, answered by the
model in turn (after a reply the window already had under way); a guest told it's an AI model of Kithylin, not
Kithylin, and the model told who it's talking with; pictures and voice messages get a note; the Discord window and
its How to connect; and, on its own, waiting in the notification area while a bot listens."""
import json

import support

from PySide6.QtCore import QTimer

from claudecore.messengers import discordlink, telegram
from test_discord import FakeDiscord, FakeSocket, SOCKETS, dm             # (FakeSocket: the gateway, stood in)
from test_discord import TOKEN as DISCORD_TOKEN
from test_telegram import GUEST, OWNER, STRANGER, TOKEN, FakeTelegram, message, photo

support.qapp()
discordlink.make_socket = FakeSocket


def _window(links):
    """Kithylin AI's window, on scratch data (support: KITHYLINAI_DATA), with a stand-in model and these bots."""
    support.no_engines()
    from kithylinai.app import KithylinAI
    w = KithylinAI(None)
    for which, link in links.items():
        w.links[which] = link
    asked = []

    def chat(messages, temperature=0.9, max_tokens=600, extra=None):
        asked.append(messages)
        n = len(asked)
        QTimer.singleShot(150, lambda: w.engine.done.emit(f"Reply {n}", ""))
    w.engine.ready = True
    w.engine.chat = chat
    w.resize(1000, 700)
    w.show()
    support.pump(0.6)                                          # (it starts listening)
    return w, asked


def test_kithylin_on_telegram():
    """Kithylin AI on Telegram: linked by a code; each person a chat of their own, answered in turn after the
    window's own reply; a guest welcomed as talking with an AI model of Kithylin, and the model told who they are;
    a stranger turned away; pictures on their own and voice messages get a note"""
    caught = support.catch_errors()
    from kithylinai import bots, store
    from kithylinai.paths import DATA
    api = FakeTelegram()
    telegram.Link(DATA, api=api, words=bots.WORDS).connect(TOKEN)
    said = {m: p for m, p in api.calls if m.startswith("setMy")}
    assert "Kithylin AI" in said["setMyDescription"]["description"], "the bot doesn't say it's Kithylin AI"
    assert "not by Kithylin" in said["setMyDescription"]["description"], "the bot doesn't say it isn't Kithylin"
    w, asked = _window({"telegram": telegram.Link(DATA, api=api, words=bots.WORDS)})
    assert w._listening("telegram"), "it isn't listening"
    link = w.links["telegram"]

    def answered(chat, n):
        assert support.pump(10, until=lambda: len(api.to(chat)) > n), f"nothing was sent to {chat}"
        return api.to(chat)[-1]
    api.inbox.append(message(OWNER, link.code("owner")))
    assert answered(OWNER, 0) == bots.WORDS["linked"]
    assert "Telegram is linked" in json.dumps(w.chat.messages)
    # the window's reply first, then Telegram's - one at a time
    w.composer.setPlainText("Hello from the window")
    w.send()
    api.inbox.append(message(OWNER, "Hello from my phone"))
    assert answered(OWNER, 1) == "Reply 2", api.to(OWNER)
    assert asked[0][-1]["content"] == "Hello from the window" and asked[1][-1]["content"] == "Hello from my phone"
    assert asked[1][0] == {"role": "system", "content": w.settings.system_prompt()}, "the owner's prompt isn't the window's"
    kept = json.loads((store.CHATS_DIR / f"telegram-{OWNER}.json").read_text(encoding="utf-8"))
    assert kept["title"] == "Jason on Telegram" and [m["content"] for m in kept["messages"]] == [
        "Hello from my phone", "Reply 2"], kept
    assert "Jason is talking with Kithylin on Telegram" in json.dumps(w.chat.messages)
    assert [m["content"] for m in w.chat.spoken()] == ["Hello from the window", "Reply 1"], "the chats got mixed up"
    # a guest: welcomed as talking with an AI, and the model told who they are
    api.inbox.append(message(GUEST, link.code("guest", "Sam"), first="Samuel"))
    welcome = answered(GUEST, 0)
    for bit in ("Hello, Sam", "Kithylin AI", "AI language model", "not by Kithylin", "Jason invited you"):
        assert bit in welcome, (bit, welcome)
    api.inbox.append(message(GUEST, "Hi Kithylin!", first="Samuel"))
    assert answered(GUEST, 1) == "Reply 3"
    prompt = asked[2][0]["content"]
    assert "with Sam, someone invited" in prompt and "They know you're an AI" in prompt, prompt[-300:]
    # a stranger; a picture on its own; a voice message
    api.inbox.append(message(STRANGER, "who's this?", first="Eve"))
    assert answered(STRANGER, 0) == bots.WORDS["private"]
    api.inbox.append(photo(OWNER))
    assert answered(OWNER, 2) == bots.WORDS["cant"].format(what="pictures")
    voice = message(OWNER, "")
    del voice["message"]["text"]
    voice["message"]["voice"] = {"file_id": "v1", "duration": 2}
    api.inbox.append(voice)
    assert answered(OWNER, 3) == bots.WORDS["cant"].format(what="voice messages") and len(asked) == 3
    # the conversation, shown in the window
    w._show_conversation("telegram", link.owner)
    assert w.chat.data["id"] == f"telegram-{OWNER}" and "Reply 2" in json.dumps(w.chat.messages)
    listener = w.listeners["telegram"]
    w.shutdown()
    listener.thread.join(5)
    assert not listener.thread.is_alive(), "it was still listening after it closed"
    support.no_errors(caught)


def test_kithylin_on_discord_and_its_windows():
    """Kithylin AI on Discord: a direct message answered; the Discord window and How to connect in Kithylin AI's
    words; and, on its own, closing the window while a bot listens leaves it in the notification area"""
    caught = support.catch_errors()
    from PySide6.QtWidgets import QDialog, QLabel, QPushButton, QTextBrowser
    import kithylinai.app as K
    from kithylinai import bots
    from kithylinai.paths import DATA
    api = FakeDiscord()
    discordlink.Link(DATA, api=api, words=bots.WORDS).connect(DISCORD_TOKEN)
    said = next(body for method, path, body in api.calls if method == "PATCH")
    assert "Kithylin AI" in said["description"] and len(said["description"]) <= 400, said
    n = len(SOCKETS)
    w, asked = _window({"discord": discordlink.Link(DATA, api=api, words=bots.WORDS)})
    assert w._listening("discord") and len(SOCKETS) == n + 1, "it isn't listening"
    ws = SOCKETS[-1]
    ws.feed(10, {"heartbeat_interval": 45000})
    ws.feed(0, {"session_id": "S", "resume_gateway_url": "wss://r"}, "READY", 1)
    chat = f"dm-{OWNER}"
    ws.feed(0, dm(OWNER, w.links["discord"].code("owner")), "MESSAGE_CREATE", 2)
    assert support.pump(5, until=lambda: api.to(chat)) and api.to(chat)[-1] == bots.WORDS["linked"]
    ws.feed(0, dm(OWNER, "Hi from Discord"), "MESSAGE_CREATE", 3)
    assert support.pump(5, until=lambda: len(api.to(chat)) > 1) and api.to(chat)[-1].startswith("Reply")
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
    assert seen.get("title") == "Kithylin AI on Discord" and "Talk with Kithylin on Discord" in seen["text"], seen
    assert {"Add it to a server...", "Unlink", "Show our conversation"} <= set(seen["buttons"]), seen["buttons"]
    title, steps = seen["how"]
    assert title == "How to connect Kithylin AI to Discord", title
    assert "name it Kithylin AI" in steps and "find Kithylin AI in that server" in steps, steps[:400]
    assert "Soul and Song" not in steps, "Kithylin AI's steps talk about Soul and Song"
    # on its own: closing the window while a bot listens waits in the notification area
    real, shown = K.QSystemTrayIcon, []

    class Tray:
        @staticmethod
        def isSystemTrayAvailable():
            return True
    K.QSystemTrayIcon = Tray
    w._tray_show = lambda: shown.append(True)
    try:
        assert w.close_to_tray() and shown == [True] and not w.isVisible(), "it didn't wait in the notification area"
        w.show_again()
        assert w.isVisible(), "it didn't come back"
        w._quitting = True
        assert not w.close_to_tray(), "Stop listening and quit didn't quit"
    finally:
        K.QSystemTrayIcon = real
    w.shutdown()
    assert not w._listening("discord")
    support.no_errors(caught)


if __name__ == "__main__":
    support.main(globals())
