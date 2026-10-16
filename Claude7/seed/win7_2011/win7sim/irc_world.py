"""The supplied FurNet network, simulated locally without opening IRC sockets."""

from dataclasses import dataclass, field
from datetime import datetime
import json
from pathlib import Path
import random
import re

from .clock import LOCKED_YEAR
from .mush_world import MushWorld, _stable_fraction

IRC_ASSETS = Path(__file__).resolve().parent.parent / "assets" / "irc"


class IRCWorldError(ValueError):
    pass


def nick_key(value):
    return value.casefold().translate(str.maketrans("[]\\^", "{}|~"))


def valid_nick(value):
    return bool(re.fullmatch(r"[A-Za-z_\[\]\\`^{}|][A-Za-z0-9_\-\[\]\\`^{}|]{0,29}", value))


@dataclass
class IRCActor:
    nick: str
    realname: str
    ident: str
    persona: str
    channels: tuple
    ops: tuple = ()
    hours: tuple | None = None
    chance: float = 0.25
    bot: bool = False
    idle: bool = False
    supplied_regular: bool = False
    age_verified: bool = False
    profile_text: str = ""
    contacts: list = field(default_factory=list)
    online: bool = False
    memberships: set = field(default_factory=set)


class IRCWorld:
    def __init__(self, account, presence=None, *, root=IRC_ASSETS, now=None, rng=None):
        self.account = account
        self.now = now or datetime.now
        self.rng = rng or random.Random()
        self.connected = False
        self.profile_id = ""
        self.nick = ""
        self.away = ""
        self.joined = set()
        self.actors = {}
        self.excluded_minor_names = set()
        self.excluded_unverified_names = set()
        try:
            self.network = json.loads((Path(root) / "network.json").read_text("utf-8-sig"))
            regulars = json.loads((Path(root) / "regulars.json").read_text("utf-8-sig"))["regulars"]
            self.channels = dict(self.network["channels"])
            if (
                not isinstance(regulars, list) or not self.channels
                or not all(key in self.network for key in ("network", "server", "port", "autojoin", "motd"))
                or any(name not in self.channels for name in self.network["autojoin"])
            ):
                raise ValueError("Invalid network or autojoin configuration.")
            for name, channel in self.channels.items():
                if not name.startswith("#") or float(channel.get("popularity", 1)) <= 0:
                    raise ValueError("Invalid channel configuration.")
        except (OSError, UnicodeError, ValueError, TypeError, KeyError) as exc:
            raise IRCWorldError(f"Cannot load the supplied FurNet data: {exc}") from exc

        community = MushWorld(account, presence)
        for item in regulars:
            name = str(item["nick"])
            bot = bool(item.get("bot"))
            canonical = community.find_resident(name)
            profile_text = canonical.profile_text if canonical else ""
            age = MushWorld._age_assessment(str(item.get("persona", "")), profile_text)
            if not bot and (age is None or age < 21):
                target = self.excluded_unverified_names if age is None else self.excluded_minor_names
                target.add(name)
                continue
            actor = IRCActor(
                nick=name, realname=str(item.get("realname", name)),
                ident=str(item.get("ident", name.lower())),
                persona=str(item.get("persona", "")),
                channels=tuple(c for c in item["channels"] if c in self.channels),
                ops=tuple(c for c in item.get("ops", []) if c in self.channels),
                hours=tuple(item["hours"]) if item.get("hours") else None,
                chance=max(0, min(1, float(item.get("start_chance", 0.25)))),
                bot=bot, idle=bool(item.get("idle", False)),
                supplied_regular=True,
                age_verified=not bot and age is not None and age >= 21,
                profile_text=profile_text,
                contacts=list(canonical.contacts) if canonical else [],
            )
            if not actor.channels or not valid_nick(name) or nick_key(name) in self.actors:
                raise IRCWorldError(f"Invalid or duplicate regular: {name}")
            self.actors[nick_key(name)] = actor

        # Decorative lurkers never receive model-driven replies. Only verified
        # adult identities and explicitly named service bots enter this world.
        for channel, details in self.channels.items():
            for name in details.get("lurkers", []):
                key = nick_key(name)
                if key in self.actors:
                    actor = self.actors[key]
                    actor.channels = tuple(dict.fromkeys((*actor.channels, channel)))
                    continue
                base = re.split(r"[|^]", name)[0]
                if base in self.excluded_minor_names:
                    continue
                canonical = community.find_resident(base)
                regular = self.actors.get(nick_key(base))
                bot = name == "HelpBot"
                if not bot and canonical is None and regular is None:
                    self.excluded_unverified_names.add(name)
                    continue
                self.actors[key] = IRCActor(
                    nick=name, realname="FurNet help service" if bot else name,
                    ident="helpbot" if bot else base.lower(),
                    persona="", channels=(channel,), bot=bot, idle=not bot,
                    chance=1 if bot else 0.65,
                )

    def connect(self):
        profile = self.account.active_profile
        if profile is None:
            raise IRCWorldError("Select a Windows fursona before connecting.")
        self.profile_id = profile.profile_id
        self.nick = re.sub(r"[^A-Za-z0-9_\-\[\]\\`^{}|]", "_", profile.fursona_name)[:30]
        if not valid_nick(self.nick):
            self.nick = "_" + self.nick[:29]
        self.connected = True
        self.away = ""
        self.joined = set(self.network["autojoin"])
        stamp = f"{LOCKED_YEAR}-{self.now().strftime('%m-%d')}"
        for actor in self.actors.values():
            actor.online = (
                nick_key(actor.nick) != nick_key(self.nick)
                and (actor.bot or (
                    MushWorld._in_hours(actor.hours, self.now())
                    and _stable_fraction(f"irc:{stamp}:{actor.nick}") < actor.chance
                ))
            )
            actor.memberships = self._pick_channels(actor) if actor.online else set()

    def _pick_channels(self, actor):
        if actor.bot:
            return set(actor.channels)
        weights = [float(self.channels[c].get("popularity", 1)) for c in actor.channels]
        primary = self.rng.choices(actor.channels, weights=weights, k=1)[0]
        return {primary} | {
            channel for channel in actor.channels
            if self.rng.random() < float(self.channels[channel].get("popularity", 1)) / 10
        }

    def disconnect(self):
        self.connected = False
        self.joined.clear()
        self.away = ""
        for actor in self.actors.values():
            actor.online = False
            actor.memberships.clear()

    def channel_name(self, query):
        return next((c for c in self.channels if c.casefold() == query.casefold()), None)

    def members(self, channel):
        return sorted(
            (a for a in self.actors.values() if a.online and channel in a.memberships),
            key=lambda a: (channel not in a.ops, nick_key(a.nick)),
        )

    def conversation_candidates(self, joined_channels=None):
        """Return verified supplied regulars who can receive a simulated chat."""
        joined = self.joined if joined_channels is None else set(joined_channels)
        return [
            (actor, channel)
            for actor in self.actors.values()
            if (
                actor.online and actor.supplied_regular and actor.age_verified
                and not actor.bot and not actor.idle
            )
            for channel in sorted(actor.memberships & joined)
            if channel in self.channels
        ]

    def find(self, nick):
        actor = self.actors.get(nick_key(nick))
        return actor if actor and actor.online else None

    def rename(self, value):
        if not valid_nick(value):
            raise IRCWorldError("Use a valid IRC nickname of 1–30 characters, without spaces.")
        if self.find(value) and nick_key(value) != nick_key(self.nick):
            raise IRCWorldError("That nickname is already in use.")
        previous, self.nick = self.nick, value
        return previous

    def tick(self):
        """One active-session step, never a catch-up for time spent closed."""
        events = []
        if not self.connected:
            return events
        for actor in self.actors.values():
            if actor.bot or nick_key(actor.nick) == nick_key(self.nick):
                continue
            awake = MushWorld._in_hours(actor.hours, self.now())
            old = set(actor.memberships)
            if actor.online and (not awake or self.rng.random() < 0.008):
                actor.online = False
                actor.memberships.clear()
            elif not actor.online and awake and self.rng.random() < actor.chance * 0.012:
                actor.online = True
                actor.memberships = self._pick_channels(actor)
            elif actor.online and self.rng.random() < 0.06:
                actor.memberships = self._pick_channels(actor)
            for channel in old - actor.memberships:
                events.append((channel, f"* {actor.nick} has left {channel}."))
            for channel in actor.memberships - old:
                events.append((channel, f"* {actor.nick} ({actor.ident}@users.FurNet.IRC) has joined {channel}."))
        return events
