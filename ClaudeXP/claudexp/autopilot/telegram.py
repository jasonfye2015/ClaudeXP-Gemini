"""Kithylin on Telegram: the AIM legs (chatting and roleplay, legs.py) played in Telegram Desktop instead - for a
computer without ClaudeAIM (WORKSTATION-2025). The legs don't change: TelegramApp shows them Telegram the way they
know AIM - the world with its buddies (their presence, their conversation), the 'new message' signal, an open chat
with its input box and Send - so everything they do (answering, saying hello, greeting a love interest, the RP
tracks, his interests and his day) works as it does on AIM. The buddies are the same people, with the same ids.

Telegram is one window with a chat list, not a window per buddy: 'the IM window' is the chat that's open, and
letting a conversation rest just leaves it (Telegram stays open)."""
from shiboken6 import isValid

from .. import programs
from .legs import Messengers, Roleplay


def _presence(word):
    from claudeaim.engine import Presence
    return {"online": Presence.ONLINE, "busy": Presence.ONLINE, "away": Presence.AWAY}.get(word, Presence.OFFLINE)


class _History:
    def __init__(self, buddy):
        self.buddy = buddy

    @property
    def messages(self):
        return self.buddy.history


class _Buddy:
    """A Telegram buddy as the AIM legs see one."""

    def __init__(self, buddy):
        self.b = buddy
        self.history = _History(buddy)

    @property
    def id(self):
        return self.b.contact.id

    @property
    def name(self):
        return self.b.name

    @property
    def contact(self):
        return self.b.contact

    @property
    def presence(self):
        return _presence(self.b.presence)


class _World:
    def __init__(self, network):
        self.net = network
        self.message_added = network.message_added           # (buddy id, entry): the same as AIM's
        self._wrapped = {}

    @property
    def running(self):
        return self.net.signed_in

    @property
    def buddies(self):
        out = {}
        for bid, b in self.net.buddies.items():
            w = self._wrapped.get(bid)
            if w is None or w.b is not b:
                w = self._wrapped[bid] = _Buddy(b)
            out[bid] = w
        return out

    @property
    def settings(self):
        return {"screen_name": self.net.my_handle()}

    def set_user_away(self, away, message=""):
        from ..programs.messengers.core import AWAY, ONLINE
        self.net.my_status = AWAY if away else ONLINE


class _Chat:
    """The open chat, as an IM window: its input box, Send, and the window it's in."""

    def __init__(self, body):
        self.input = body.entry
        self._send = body.send
        self._xp_frame = body.frame


class TelegramApp:
    def __init__(self, body):
        self.body = body
        self.world = _World(body.network)

    def open_im(self, bid):
        frame = self.body.frame
        if frame is not None and isValid(frame) and not frame.isVisible():
            self.body.desktop.open_window(frame)
        if self.body.pages.currentIndex() != 1:
            self.body.start_messaging()
        self.body.open_chat(bid)

    @property
    def im_windows(self):
        bid = self.body.current
        if bid is None or self.body.frame is None or not isValid(self.body.frame):
            return {}
        return {bid: _Chat(self.body)}


def _window():
    from ..programs.messengers import telegram
    win = telegram._holder.get("win")
    return win if win is not None and isValid(win) else None


class TelegramChat(Messengers):
    """Telegram, open the whole session: he answers whoever messages him and now and then says hello."""
    key, title = "messengers", "Telegram"
    blurb = "answer messages, say hello to friends who are online (nearly always on)"
    doing = "chatting on Telegram"

    def messenger(self):
        win = _window()
        return TelegramApp(win.content) if win is not None else None

    def open_messenger(self, ctx):
        ctx.status("Opening Telegram...")
        programs.launch(ctx.desktop, "telegram")
        yield (lambda: _window() is not None, 30)
        win = _window()
        if win is None:
            return
        body = win.content
        if body.pages.currentIndex() != 1:                   # the welcome page: START MESSAGING
            yield from ctx.hands.take(self.key)
            try:
                yield 1.0 * ctx.pace
                body.start_messaging()
            finally:
                ctx.hands.release(self.key)
        elif not body.network.signed_in:
            body.network.sign_in()
        yield (lambda: body.network.signed_in, 30)

    def close_im(self, ctx, app, bid):
        """Letting a conversation rest: Telegram stays open (it's every chat at once)."""
        return
        yield


class TelegramRoleplay(Roleplay):
    """A proper scene with one buddy on Telegram, the chat leg standing aside for them."""
    title = "Roleplay on Telegram"
    blurb = "a proper scene with one buddy, led along one of your RP tracks"
    doing = "roleplaying with a friend on Telegram"
    CHAT = TelegramChat


IM_NOTE = ("\n\nYou're on Telegram on your Windows 11 computer in {year}. Reply with one short message: a line or two, "
           "casual, the way you really type. No narration, no name prefix.")
RP_NOTE = ("\n\nYou're on Telegram in {year}, roleplaying with {name}. This is a roleplay scene, not a quick chat: "
           "forget short messages, goodbyes and BRBs. Actions go in *asterisks*, speech plain. Stay in the scene, two "
           "to four sentences, move it along, and leave {name} something to respond to. No name prefix.")
