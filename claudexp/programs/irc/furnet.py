"""FurNet, simulated: the server, channels, people coming and going, FurBot, and IRC commands.

The client sees only signals: line(window, kind, text) where window is "" for Status,
"#channel" or a nick (private query), plus joined/parted/names/topic/query_opened.
"""
import random
import time
import zlib
from collections import deque
from dataclasses import dataclass, field
from datetime import timedelta

from PySide6.QtCore import QObject, QTimer, Signal

from ... import clock
from ...paths import ROOT
from ..people import aim_screen_name, available, load_buddies, load_json, mentions, parse_hours, save_json
from .brain import PRIORITY_CHATTER, PRIORITY_REPLY, Brain

IRC_DIR = ROOT / "Program Files" / "ClaudeIRC"
DATA_DIR = IRC_DIR / "data"
QUERY_DIR = DATA_DIR / "queries"

TICK_MS = 5000
SESSION_MINUTES = (40, 200)
OFFLINE_MINUTES = (15, 120)
MOVE_MINUTES = (8, 40)            # how often someone joins/parts another channel
LURKER_MINUTES = (30, 150)        # how often an idle lurker quits and comes back
AMBIENT_SECONDS = (50, 160)       # quiet time before someone talks in the channel you're looking at
BACKGROUND_FACTOR = 3             # channels you're not looking at are this much quieter
TYPING = (1.5, 4.5)
GUEST_MINUTES = (12, 40)          # the occasional 'asl?' guest in #furnet
SPEED = 1.0

ISPS = ["dialup.aol.com", "ipt.aol.com", "earthlink.net", "mindspring.com", "dsl.verizon.net",
        "cable.rr.com", "client.attbi.com", "dialup.prodigy.net", "dial.juno.com", "netzero.net"]
QUIT_REASONS = ["Quit: Leaving", "Ping timeout", "Read error: Connection reset by peer", "Quit: brb",
                "Quit: night all!", "Quit: mIRC v6.02", "Quit: *poof*", "Quit: gotta go, mom needs the phone",
                "Ping timeout", "Quit: Leaving"]
EIGHT_BALL = ["Yes.", "No.", "Ask again later.", "Outlook not so good.", "Without a doubt.",
              "My sources say no.", "Signs point to yes.", "Reply hazy, try again.", "Don't count on it.",
              "It is decidedly so.", "Concentrate and ask again.", "Very doubtful."]
GUEST_LINES = ["asl?", "any1 wanna cyber", "a/s/l plz", "hi any girls here?", "asl", "where r all the hot fems"]
KICK_REASONS = ["No ASL here. Read the topic.", "Not that kind of channel.", "Bye!", "Read the topic, please."]

HELP = """\
ClaudeIRC commands:
  /join #channel        join a channel             /part [#channel]     leave it
  /msg <nick> <text>    private message            /query <nick>        open a private window
  /me <action>          do an action               /nick <newnick>      change your nick
  /whois <nick>         who is that?               /names [#channel]    who's in a channel
  /list                 list channels              /topic [#channel]    show the topic
  /away [message]       set or clear away          /ctcp <nick> version
  /clear                clear this window          /quit [message]      disconnect
Double-click a nick in the nick list to open a private window.
FurBot answers: !rules !hug <nick> !8ball <question> !seen <nick> !time !help"""


def _now():
    return time.monotonic() * SPEED


def _heard(p, program, speaker, text):
    """Tell the shared memory about a line of conversation with a buddy."""
    from ...life import get as life
    if p is not None and p.contact is not None and life() is not None:
        life().heard(p.contact.screen_name, program, speaker, text)


def _minutes(lo_hi):
    return random.uniform(*lo_hi) * 60


@dataclass
class Person:
    nick: str
    ident: str = ""
    realname: str = ""
    persona: str = ""
    channels: list = field(default_factory=list)   # favourite channels
    ops: set = field(default_factory=set)
    hours: tuple = None
    start_chance: float = 0.6
    temperature: float = 0.9
    contact: object = None
    bot: bool = False
    lurker: bool = False
    # state
    online: bool = False
    joined: set = field(default_factory=set)
    on_since: float = 0.0
    last_active: float = 0.0
    session_end: float = 0.0
    next_online: float = 0.0
    next_move: float = 0.0
    thinking: bool = False
    last_seen: float = 0.0

    @property
    def host(self):
        h = zlib.crc32(self.nick.lower().encode())
        return f"{self.ident or self.nick.lower()[:9]}@furnet-{h & 0xFFFF:04X}{(h >> 16) & 0xFF:02X}.{ISPS[h % len(ISPS)]}"

    @property
    def talks(self):
        return not (self.lurker or self.bot)

    def available(self):
        return available(self.contact, self.hours)


@dataclass
class Channel:
    name: str
    topic: str = ""
    topic_by: str = "FurNet"
    topic_age_days: int = 3
    modes: str = "+nt"
    popularity: float = 1.0
    log: deque = field(default_factory=lambda: deque(maxlen=30))
    next_ambient: float = 0.0


class FurNet(QObject):
    line = Signal(str, str, str)       # window ("" = status), kind, text
    joined = Signal(str)               # you joined a channel
    parted = Signal(str)               # you left a channel
    names = Signal(str)                # a channel's nick list changed
    topic = Signal(str)
    query_opened = Signal(str)         # someone messaged you privately
    nick_changed = Signal(str)
    closed = Signal(str)               # you quit / were disconnected

    def __init__(self, parent=None):
        super().__init__(parent)
        data = load_json(IRC_DIR / "network.json", {})
        self.network_name = data.get("network", "FurNet")
        self.server = data.get("server", "FurNet.IRC")
        self.port = int(data.get("port", 6667))
        self.server_version = data.get("server_version", "Unreal3.1.1")
        self.created = data.get("created", "")
        self.motd = data.get("motd", [])
        self.default_autojoin = data.get("autojoin", ["#furnet"])
        self.channels = {}
        lurkers = {}
        for name, c in data.get("channels", {}).items():
            self.channels[name.lower()] = Channel(name, c.get("topic", ""), c.get("topic_by", "FurNet"),
                                                  random.randint(1, 20), c.get("modes", "+nt"),
                                                  float(c.get("popularity", 1)))
            for nick in c.get("lurkers", []):
                lurkers.setdefault(nick, []).append(name)
        self.load_errors = []
        self.people = []
        for r in load_json(IRC_DIR / "regulars.json", {}).get("regulars", []):
            try:
                self.people.append(Person(
                    nick=r["nick"], ident=r.get("ident", ""), realname=r.get("realname", r["nick"]),
                    persona=r.get("persona", ""), channels=self._known(r.get("channels", [])),
                    ops={c.lower() for c in r.get("ops", [])}, hours=parse_hours(r.get("hours")),
                    start_chance=float(r.get("start_chance", 0.6)), bot=bool(r.get("bot")),
                    temperature=float(r.get("temperature", 0.9))))
            except (KeyError, ValueError) as e:
                self.load_errors.append(f"regulars.json: {e}")
        buddies, errors = load_buddies("irc")
        self.load_errors += errors
        for contact, irc in buddies:
            favs = self._known(irc.get("channels", [])) or ["#furnet"] + random.sample(
                [c.name for c in self.channels.values() if c.name.lower() != "#furnet"], 1)
            self.people.append(Person(
                nick=irc.get("nick", contact.screen_name), ident=irc.get("ident", contact.screen_name.lower()[:9]),
                realname=irc.get("realname", (contact.profile or contact.screen_name)[:40]),
                persona=contact.persona, channels=favs, ops={c.lower() for c in irc.get("ops", [])},
                start_chance=contact.start_online_chance, temperature=contact.temperature, contact=contact))
        taken = {p.nick.lower() for p in self.people}
        for nick, chans in lurkers.items():
            if nick.lower() not in taken:
                self.people.append(Person(nick=nick, ident=nick.lower().strip("_^|")[:9] or "user",
                                          realname="...", channels=chans, lurker=True, start_chance=0.85))
        self.brain = Brain(self)
        self.connected = False
        self.nick = ""
        self.realname = ""
        self.away = ""
        self.my_channels = []           # channel names you're in, in join order
        self.last_channels = []
        self.on_since = 0.0
        self.last_active = 0.0
        self.active_window = ""
        self.next_guest = 0.0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)

    def _known(self, names):
        return [self.channels[n.lower()].name for n in names if n.lower() in self.channels]

    # ---- lookups --------------------------------------------------------------------
    @property
    def aim_name(self):
        """The user's AIM screen name, read fresh so renames show up at once."""
        return aim_screen_name()

    def person(self, nick, online_only=True):
        nick = nick.lower()
        for p in self.people:
            if p.nick.lower() == nick and (p.online or not online_only):
                return p
        return None

    def in_channel(self, name):
        return name.lower() in [c.lower() for c in self.my_channels]

    def members(self, name):
        key = name.lower()
        return [p for p in self.people if p.online and key in {c.lower() for c in p.joined}]

    def member_nicks(self, name):
        nicks = [p.nick for p in self.members(name)]
        if self.in_channel(name):
            nicks.append(self.nick)
        return nicks

    def nicklist(self, name):
        """Display names for the nick list: @ops first, then everyone else, alphabetically."""
        key = name.lower()
        entries = [("@" if key in p.ops else "") + p.nick for p in self.members(name)]
        if self.in_channel(name):
            entries.append(self.nick)
        return sorted(entries, key=lambda e: (0 if e.startswith("@") else 1, e.lstrip("@").lower()))

    def channel(self, name):
        return self.channels.get(name.lower())

    def out(self, window, kind, text):
        self.line.emit(window, kind, text)

    def _chan_out(self, chan, kind, text, log=None):
        chan.log.append(log or text)
        if self.in_channel(chan.name):
            self.out(chan.name, kind, text)

    # ---- connecting -------------------------------------------------------------------
    def connect_session(self, nick, alt, realname):
        self.connected = True
        self.realname = realname
        self.nick = nick
        if self.person(nick, online_only=False) and self.person(nick):
            self.out("", "info", f"* Nickname {nick} is already in use, trying {alt}")
            self.nick = alt
        now = _now()
        self.on_since = self.last_active = now
        self._populate()
        s = self.server
        users = 300 + random.randint(0, 140)
        for text in [f"Welcome to the {self.network_name} IRC Network {self.nick}!{self.nick.lower()}@furnet-user",
                     f"Your host is {s}, running version {self.server_version}",
                     f"This server was created {self.created}",
                     f"There are {users} users and {random.randint(30, 90)} invisible on 6 servers",
                     f"{random.randint(14, 22)} :operator(s) online",
                     f"{len(self.channels) + random.randint(90, 160)} :channels formed",
                     f"I have {random.randint(80, 140)} clients and 1 servers",
                     f"Current Local Users: {users // 3}  Max: 214"]:
            self.out("", "server", text)
        for text in self.motd:
            self.out("", "server", text)
        self.out("", "server", "End of /MOTD command.")
        self.out("", "mode", f"* {self.nick} sets mode: +i")
        self.next_guest = now + _minutes(GUEST_MINUTES)
        self.timer.start(TICK_MS)
        from ...life import get as life
        if life() is not None:
            life().irc = self
        for p in self.people:
            if p.contact is not None and p.online and random.random() < 0.3:
                QTimer.singleShot(random.randint(20, 120) * 1000, lambda p=p: self._buddy_says_hi(p))

    def autojoin(self, channels):
        for name in channels:
            self.join(name)

    def disconnect_session(self, reason=""):
        if not self.connected:
            return
        self.timer.stop()
        from ...life import get as life
        if life() is not None and life().irc is self:
            life().irc = None
        self.last_channels = list(self.my_channels)   # rejoined on the next connect
        self.my_channels.clear()
        self.connected = False
        self.closed.emit(reason)

    def _populate(self):
        now = _now()
        for p in self.people:
            p.joined = set()
            if p.available() and random.random() < p.start_chance:
                p.online = True
                p.on_since = now - random.uniform(5, 300) * 60
                p.last_active = now - (random.uniform(1, 9) * 3600 if p.lurker else random.uniform(0, 25) * 60)
                p.session_end = now + (_minutes(LURKER_MINUTES) if p.lurker else _minutes(SESSION_MINUTES))
                p.next_move = now + _minutes(MOVE_MINUTES)
                p.joined = set(self._pick_channels(p))
            else:
                p.online = False
                p.next_online = now + _minutes((2, 40))

    def _pick_channels(self, p):
        favs = p.channels or ["#furnet"]
        if p.bot or p.lurker:
            return favs
        picked = [favs[0]] if random.random() < 0.85 else []
        for c in favs[1:]:
            if random.random() < 0.5:
                picked.append(c)
        return picked or [random.choice(favs)]

    # ---- the clock ----------------------------------------------------------------------
    def _tick(self):
        now = _now()
        for p in self.people:
            if p.online and now >= p.session_end and (p.lurker or not p.bot):
                self._quit(p)
            elif p.online and not p.lurker and not p.bot and not p.available():
                self._quit(p, "Quit: night all!")
            elif not p.online and now >= p.next_online:
                if p.lurker or p.available():
                    self._come_online(p)
                else:
                    p.next_online = now + _minutes((15, 45))
            elif p.online and p.talks and now >= p.next_move and not p.thinking:
                self._wander(p)
        for name in list(self.my_channels):
            chan = self.channel(name)
            if chan is None or now < chan.next_ambient:
                continue
            factor = 1 if name.lower() == self.active_window.lower() else BACKGROUND_FACTOR
            chan.next_ambient = now + random.uniform(*AMBIENT_SECONDS) * factor
            talkers = [p for p in self.members(name) if p.talks and not p.thinking]
            if talkers:
                self._ask_channel(random.choice(talkers), chan,
                                  "Say something in the channel if you feel like it (chat with the others, "
                                  "react to what was said, or start a new topic), or PASS.")
        if now >= self.next_guest:
            self.next_guest = now + _minutes(GUEST_MINUTES)
            if self.in_channel("#furnet"):
                self._guest_visit()

    def _come_online(self, p):
        now = _now()
        p.online = True
        p.on_since = p.last_active = now
        p.session_end = now + (_minutes(LURKER_MINUTES) if p.lurker else _minutes(SESSION_MINUTES))
        p.next_move = now + _minutes(MOVE_MINUTES)
        for name in self._pick_channels(p):
            self._join(p, self.channel(name))

    def _join(self, p, chan):
        if chan is None or chan.name in p.joined:
            return
        p.joined.add(chan.name)
        self._chan_out(chan, "join", f"* {p.nick} ({p.host}) has joined {chan.name}",
                       log=f"*** {p.nick} has joined {chan.name}")
        self.names.emit(chan.name)
        if p.talks and self.in_channel(chan.name) and random.random() < 0.35:
            self._ask_channel(p, chan, f"You just joined {chan.name}. Say hi to the channel if you want, or PASS.")

    def _part(self, p, chan, reason=""):
        if chan.name not in p.joined:
            return
        p.joined.discard(chan.name)
        extra = f" ({reason})" if reason else ""
        self._chan_out(chan, "part", f"* {p.nick} ({p.host}) has left {chan.name}{extra}",
                       log=f"*** {p.nick} has left {chan.name}")
        self.names.emit(chan.name)

    def _quit(self, p, reason=None):
        reason = reason or random.choice(QUIT_REASONS)
        for name in list(p.joined):
            chan = self.channel(name)
            self._chan_out(chan, "quit", f"* {p.nick} ({p.host}) Quit ({reason})",
                           log=f"*** {p.nick} has quit ({reason})")
            self.names.emit(name)
        p.joined = set()
        p.online = False
        p.last_seen = _now()
        p.next_online = _now() + (_minutes((1, 4)) if "Ping" in reason or "Read error" in reason
                                  else _minutes(OFFLINE_MINUTES))

    def _wander(self, p):
        p.next_move = _now() + _minutes(MOVE_MINUTES)
        not_in = [c for c in p.channels if c not in p.joined] or \
                 [c.name for c in self.channels.values() if c.name not in p.joined]
        if len(p.joined) > 1 and random.random() < 0.5:
            self._part(p, self.channel(random.choice(sorted(p.joined))))
        elif not_in:
            weights = [max(0.05, self.channel(c).popularity) for c in not_in]
            self._join(p, self.channel(random.choices(not_in, weights=weights)[0]))

    # ---- people talking --------------------------------------------------------------------
    def _ask_channel(self, p, chan, nudge, priority=PRIORITY_CHATTER):
        if p.thinking or not p.talks:
            return
        if priority == PRIORITY_CHATTER and self.brain.busy():
            return  # don't pile background chatter up behind other replies
        p.thinking = True

        def done(result):
            p.thinking = False
            if result is None or not self.connected:
                return
            delay = random.uniform(*TYPING) + min(len(result[1]) / 30, 5)
            QTimer.singleShot(int(delay * 1000), lambda: self._say_in(p, chan, result))

        self.brain.channel_line(p, chan, nudge, done, priority)

    def _say_in(self, p, chan, result):
        if not (p.online and chan.name in p.joined):
            return
        kind, text = result
        p.last_active = _now()
        if self.in_channel(chan.name):
            _heard(p, f"IRC {chan.name}", p.nick, f"* {p.nick} {text}" if kind == "action" else text)
        if kind == "action":
            self._chan_out(chan, "action", f"* {p.nick} {text}")
        else:
            highlight = self.nick and mentions(self.nick, text)
            self._chan_out(chan, "highlight" if highlight else "msg", f"<{p.nick}> {text}")
        self._bot_command(chan, p.nick, text)
        others = [o for o in self.members(chan.name) if o is not p and o.talks]
        addressed = [o for o in others if mentions(o.nick, text)]
        if mentions(self.nick, text):
            pass  # they talked to you: your turn to answer
        elif addressed and random.random() < 0.85:
            self._ask_channel(addressed[0], chan, f"{p.nick} just said something to you. Answer if it makes sense, or PASS.")
        elif others and random.random() < 0.25:
            self._ask_channel(random.choice(others), chan, "Join in if you have something to add, or PASS.")

    def _player_said(self, chan, text):
        present = [p for p in self.members(chan.name) if p.talks]
        addressed = [p for p in present if mentions(p.nick, text, prefix=True)]
        if addressed:
            responders = addressed[:2]
        else:
            chance = 0.7 if len(present) <= 2 else 0.3
            responders = [p for p in random.sample(present, len(present)) if random.random() < chance][:2]
        for p in responders:
            self._ask_channel(p, chan, f"{self.nick} is talking to you. Answer." if p in addressed
                              else "Answer if it makes sense to, or PASS.", PRIORITY_REPLY)
        chan.next_ambient = _now() + random.uniform(*AMBIENT_SECONDS)

    # ---- private messages ----------------------------------------------------------------------
    def _history_path(self, p):
        safe = "".join(ch if ch.isalnum() else "_" for ch in p.nick)
        return QUERY_DIR / f"{safe}.json"

    def _history(self, p):
        return load_json(self._history_path(p), [])

    def _remember(self, p, role, text):
        history = self._history(p)
        history.append({"role": role, "content": text})
        save_json(self._history_path(p), history[-60:])

    def reach_out(self, p, instruction):
        """The life simulation wants this buddy to message the user first."""
        self._ask_query(p, f"({instruction})", remember_nudge=False)

    def _buddy_says_hi(self, p):
        if not (self.connected and p.online):
            return
        self._ask_query(p, f"(Your buddy {self.nick} just connected to FurNet. Send them a short private "
                           "message to say hi, or PASS.)", remember_nudge=False)

    def _ask_query(self, p, nudge=None, remember_nudge=True):
        if p.thinking:
            QTimer.singleShot(3000, lambda: self._ask_query(p, nudge, remember_nudge))
            return
        p.thinking = True
        history = self._history(p)

        def done(result):
            p.thinking = False
            if result is None or not self.connected or not p.online:
                return
            delay = random.uniform(*TYPING) + min(len(result[1]) / 30, 5)
            QTimer.singleShot(int(delay * 1000), lambda: self._query_from(p, result))

        self.brain.query_line(p, history, None if remember_nudge else nudge, done)

    def _query_from(self, p, result):
        if not (self.connected and p.online):
            return
        kind, text = result
        p.last_active = _now()
        _heard(p, "IRC (private messages)", p.nick, text)
        self._remember(p, "assistant", f"/me {text}" if kind == "action" else text)
        self.query_opened.emit(p.nick)
        self.out(p.nick, "action" if kind == "action" else "msg",
                 f"* {p.nick} {text}" if kind == "action" else f"<{p.nick}> {text}")

    def privmsg(self, nick, text, action=False):
        p = self.person(nick)
        self.query_opened.emit(p.nick if p else nick)
        window = p.nick if p else nick
        self.out(window, "action" if action else "own", f"* {self.nick} {text}" if action else f"<{self.nick}> {text}")
        if p is None:
            self.out(window, "info", f"{nick} No such nick/channel")
            return
        if p.lurker:
            if "|" in p.nick or "away" in p.nick.lower():
                self.out(window, "info", f"{p.nick} is away: {p.nick.split('|')[-1] or 'away'}")
            return
        if p.bot:
            self.out(window, "notice", f"-{p.nick}- I'm a bot! Try !help in a channel.")
            return
        self._remember(p, "user", f"/me {text}" if action else text)
        _heard(p, "IRC (private messages)", self.nick, text)
        self._ask_query(p)

    # ---- FurBot --------------------------------------------------------------------------------
    def _bot(self, chan):
        for p in self.members(chan.name):
            if p.bot:
                return p
        return None

    def _bot_command(self, chan, who, text):
        bot = self._bot(chan)
        if bot is None or not text.startswith("!"):
            return
        cmd, _, arg = text[1:].partition(" ")
        cmd, arg = cmd.lower(), arg.strip()
        reply = None
        if cmd == "rules":
            reply = ("say", f"{chan.name} rules: be nice, no drama, no ASL, no flooding. Topic: {chan.topic}")
        elif cmd == "hug":
            reply = ("action", f"hugs {arg or who} tightly!")
        elif cmd == "8ball":
            reply = ("say", f"{who}: {random.choice(EIGHT_BALL)}" if arg else f"{who}: ask me a question!")
        elif cmd == "seen" and arg:
            p = self.person(arg, online_only=False)
            if arg.lower() == self.nick.lower() or (p and p.online):
                reply = ("say", f"{arg} is online right now!")
            elif p and p.last_seen:
                mins = int((_now() - p.last_seen) / 60)
                reply = ("say", f"I last saw {p.nick} {mins} minute{'s' if mins != 1 else ''} ago.")
            else:
                reply = ("say", f"Sorry {who}, I haven't seen {arg}.")
        elif cmd == "time":
            now = clock.now()
            reply = ("say", f"It's {clock.time_text(now)} on {clock.long_date_text(now)} (server time).")
        elif cmd == "help":
            reply = ("say", "FurBot commands: !rules !hug <nick> !8ball <question> !seen <nick> !time")
        if reply:
            QTimer.singleShot(700, lambda: self._say_in(bot, chan, reply))

    def _guest_visit(self):
        chan = self.channel("#furnet")
        if chan is None:
            return
        guest = Person(nick=f"Guest{random.randint(1000, 9999)}", ident="guest", lurker=True)
        guest.online = True
        guest.joined = {chan.name}
        self._chan_out(chan, "join", f"* {guest.nick} ({guest.host}) has joined {chan.name}",
                       log=f"*** {guest.nick} has joined {chan.name}")
        self.people.append(guest)
        self.names.emit(chan.name)

        def speak():
            if self.connected:
                self._chan_out(chan, "msg", f"<{guest.nick}> {random.choice(GUEST_LINES)}")
                QTimer.singleShot(random.randint(3000, 7000), kick)

        def kick():
            ops = [p for p in self.members(chan.name) if chan.name.lower() in p.ops and p is not guest]
            op = next((p for p in ops if not p.bot), ops[0] if ops else None)
            if op is not None:
                self._chan_out(chan, "kick", f"* {guest.nick} was kicked by {op.nick} ({random.choice(KICK_REASONS)})",
                               log=f"*** {op.nick} kicked {guest.nick} for asking ASL")
            else:
                self._chan_out(chan, "quit", f"* {guest.nick} ({guest.host}) Quit (Quit: Leaving)")
            guest.online = False
            guest.joined = set()
            self.people.remove(guest)
            self.names.emit(chan.name)

        QTimer.singleShot(random.randint(3000, 8000), speak)

    # ---- your commands -------------------------------------------------------------------------
    def join(self, name):
        if not name.startswith("#"):
            name = "#" + name
        chan = self.channel(name)
        if chan is None:
            # A new, empty channel, like on real IRC.
            chan = Channel(name, "", self.nick, 0, "+nt", 0.0)
            self.channels[name.lower()] = chan
        if self.in_channel(chan.name):
            self.joined.emit(chan.name)
            return
        self.my_channels.append(chan.name)
        self.joined.emit(chan.name)
        self.out(chan.name, "join", f"* Now talking in {chan.name}")
        if chan.topic:
            self.out(chan.name, "topic", f"* Topic is '{chan.topic}'")
            when = clock.now() - timedelta(days=chan.topic_age_days, minutes=random.randint(0, 1400))
            self.out(chan.name, "topic", f"* Set by {chan.topic_by} on {when:%a %b %d %H:%M:%S}")
        chan.log.append(f"*** {self.nick} has joined {chan.name}")
        self.names.emit(chan.name)
        self.topic.emit(chan.name)
        chan.next_ambient = _now() + random.uniform(*AMBIENT_SECONDS) / 2
        bot = self._bot(chan)
        if bot is not None:
            QTimer.singleShot(1500, lambda: self.out(chan.name, "notice",
                                                     f"-{bot.nick}- Welcome to {chan.name}, {self.nick}! "
                                                     "Type !rules for the channel rules.") if self.in_channel(chan.name) else None)
        greeters = [p for p in self.members(chan.name) if p.talks]
        for p in greeters:
            chance = 0.5 if p.contact is not None else 0.2
            if random.random() < chance:
                self._ask_channel(p, chan, f"{self.nick} just joined {chan.name}. Greet them if you want, or PASS.",
                                  PRIORITY_REPLY)
                break

    def part(self, name, reason=""):
        chan = self.channel(name)
        if chan is None or not self.in_channel(name):
            return
        self.my_channels = [c for c in self.my_channels if c.lower() != name.lower()]
        chan.log.append(f"*** {self.nick} has left {chan.name}")
        self.parted.emit(chan.name)
        self.names.emit(chan.name)

    def input(self, window, text):
        """Something typed in a window: a /command, or chat for that channel/query."""
        if not text.strip():
            return
        self.last_active = _now()
        if text.startswith("/") and not text.startswith("//"):
            self._command(window, text[1:])
            return
        if text.startswith("//"):
            text = text[1:]
        if not window:
            self.out("", "info", "* You're not on a channel. (Try /join #furnet)")
        elif window.startswith("#"):
            chan = self.channel(window)
            self.out(window, "own", f"<{self.nick}> {text}")
            chan.log.append(f"<{self.nick}> {text}")
            for p in self.members(chan.name):
                _heard(p, f"IRC {chan.name}", self.nick, text)
            self._bot_command(chan, self.nick, text)
            self._player_said(chan, text)
        else:
            self.privmsg(window, text)

    def _command(self, window, text):
        cmd, _, rest = text.partition(" ")
        cmd, rest = cmd.lower(), rest.strip()
        args = rest.split()
        if cmd in ("join", "j"):
            if not args:
                self.out(window, "info", "* /join: insufficient parameters")
            for name in args[0].split(",") if args else []:
                self.join(name)
        elif cmd in ("part", "leave"):
            target = args[0] if args and args[0].startswith("#") else window
            if target.startswith("#"):
                self.part(target)
            else:
                self.out(window, "info", "* /part: you're not on a channel")
        elif cmd in ("msg", "m"):
            if len(args) < 2:
                self.out(window, "info", "* /msg: insufficient parameters")
            elif args[0].startswith("#"):
                if self.in_channel(args[0]):
                    self.input(self.channel(args[0]).name, rest.split(" ", 1)[1])
                else:
                    self.out(window, "info", f"{args[0]} Cannot send to channel")
            else:
                self.privmsg(args[0], rest.split(" ", 1)[1])
        elif cmd == "query":
            if args:
                p = self.person(args[0])
                self.query_opened.emit(p.nick if p else args[0])
                if len(args) > 1:
                    self.privmsg(args[0], rest.split(" ", 1)[1])
        elif cmd in ("me", "action", "describe"):
            if not rest:
                self.out(window, "info", "* /me: insufficient parameters")
            elif window.startswith("#"):
                chan = self.channel(window)
                self.out(window, "action", f"* {self.nick} {rest}")
                chan.log.append(f"* {self.nick} {rest}")
                self._player_said(chan, rest)
            elif window:
                self.privmsg(window, rest, action=True)
            else:
                self.out("", "info", "* /me: you're not on a channel")
        elif cmd == "nick":
            self._nick(window, args[0] if args else "")
        elif cmd == "whois":
            self._whois(window, args[0] if args else "")
        elif cmd == "names":
            target = args[0] if args else window
            if target.startswith("#") and self.channel(target):
                self.out(window, "info", f"{target} : {' '.join(self.nicklist(target))}")
                self.out(window, "info", f"{target} End of /NAMES list.")
        elif cmd == "list":
            self.out("", "info", "* Listing channels...")
            for c in sorted(self.channels.values(), key=lambda c: -len(self.member_nicks(c.name))):
                self.out("", "info", f"{c.name}  {len(self.member_nicks(c.name))}  {c.topic}")
            self.out("", "info", "* End of /LIST")
        elif cmd == "topic":
            target = args[0] if args and args[0].startswith("#") else window
            chan = self.channel(target) if target else None
            if chan is None:
                self.out(window, "info", "* /topic: you're not on a channel")
            elif (args and not args[0].startswith("#")) or len(args) > 1:
                self.out(window, "info", f"{chan.name} You're not channel operator")
            else:
                self.out(window, "topic", f"* Topic is '{chan.topic}'" if chan.topic else f"* {chan.name} has no topic")
        elif cmd == "away":
            if rest:
                self.away = rest
                self.out(window, "info", f"* You have been marked as being away ({rest})")
            else:
                self.away = ""
                self.out(window, "info", "* You are no longer marked as being away")
        elif cmd == "ctcp":
            if len(args) >= 2:
                p = self.person(args[0])
                what = args[1].upper()
                self.out(window, "ctcp", f"-> [{args[0]}] {what}")
                if p is not None:
                    reply = "mIRC v6.02 Khaled Mardam-Bey" if what == "VERSION" else \
                        (f"{random.randint(1, 4)}secs" if what == "PING" else clock.now().strftime("%a %b %d %H:%M:%S 2001"))
                    QTimer.singleShot(random.randint(400, 1500),
                                      lambda: self.out(window, "ctcp", f"[{p.nick} {what} reply]: {reply}"))
        elif cmd == "help":
            for line in HELP.splitlines():
                self.out(window, "info", line)
        elif cmd in ("quit", "exit", "bye"):
            self.disconnect_session(rest or "Leaving")
        elif cmd in ("notice",):
            if len(args) >= 2:
                self.out(window, "notice", f"-> -{args[0]}- {rest.split(' ', 1)[1]}")
        else:
            self.out(window, "info", f"{cmd.upper()} Unknown command")

    def _nick(self, window, new):
        if not new:
            self.out(window, "info", f"* Your nick is {self.nick}")
            return
        if self.person(new) or not all(ch.isalnum() or ch in "_-[]{}|^`\\" for ch in new) or len(new) > 30:
            self.out(window, "info", f"{new} Nickname is already in use" if self.person(new)
                     else f"{new} Erroneous Nickname")
            return
        old, self.nick = self.nick, new
        for name in self.my_channels:
            chan = self.channel(name)
            self._chan_out(chan, "nick", f"* {old} is now known as {new}", log=f"*** {old} is now known as {new}")
            self.names.emit(name)
        if not self.my_channels:
            self.out("", "nick", f"* Your nick is now {new}")
        self.nick_changed.emit(new)

    def _whois(self, window, nick):
        if not nick:
            self.out(window, "info", "* /whois: insufficient parameters")
            return
        now = _now()
        if nick.lower() == self.nick.lower():
            rows = [f"{self.nick} is {self.nick.lower()}@furnet-user * {self.realname}",
                    f"{self.nick} on {' '.join(self.my_channels)}" if self.my_channels else None,
                    f"{self.nick} using {self.server} {self.network_name} IRC server",
                    f"{self.nick} is away: {self.away}" if self.away else None,
                    f"{self.nick} has been idle {int(now - self.last_active)}secs"]
        else:
            p = self.person(nick)
            if p is None:
                self.out(window, "info", f"{nick} No such nick/channel")
                return
            idle = int(now - p.last_active)
            signon = clock.now() - timedelta(seconds=now - p.on_since)
            chans = " ".join(("@" if c.lower() in p.ops else "") + c for c in sorted(p.joined))
            rows = [f"{p.nick} is {p.host} * {p.realname}",
                    f"{p.nick} on {chans}" if chans else None,
                    f"{p.nick} using {self.server} {self.network_name} IRC server",
                    f"{p.nick} is away: {p.nick.split('|')[-1]}" if p.lurker and "|" in p.nick else None,
                    f"{p.nick} has been idle {idle // 60}mins {idle % 60}secs, signed on {signon:%a %b %d %H:%M:%S}"]
        for row in rows:
            if row:
                self.out(window, "whois", row)
        self.out(window, "whois", f"{nick} End of /WHOIS list.")
