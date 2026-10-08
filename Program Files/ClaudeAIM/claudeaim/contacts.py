"""Loading contact definitions from contacts/*.json (see README for the format)."""
import json
from dataclasses import dataclass, field

from . import paths, timefmt
from .pictures import SHARING_MODES, PictureSet
from .schedule import Schedule, parse_time

TRIGGER_EVENTS = {"signon", "user_signon", "idle", "user_away", "user_back"}
SLOW_DAYS = ("all", "weekdays", "weekends")


def _range(value, default):
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return (float(value), float(value))
    lo, hi = value
    return (float(lo), float(hi))


@dataclass
class Trigger:
    on: str
    prompt: str = ""
    text: str = ""
    delay_minutes: tuple = (0.0, 0.0)
    minutes: float = 30.0          # idle triggers: quiet time before firing
    chance: float = 1.0
    if_user_away: str = "send"     # send | skip | wait
    once: bool = False             # at most once per sign-on
    share_picture: bool = False    # send one of their pictures the user hasn't seen yet

    @classmethod
    def from_dict(cls, d):
        on = d.get("on", "")
        if on not in TRIGGER_EVENTS:
            raise ValueError(f"trigger 'on' must be one of {sorted(TRIGGER_EVENTS)}, got {on!r}")
        if not (d.get("prompt") or d.get("text") or d.get("share_picture")):
            raise ValueError("trigger needs a 'prompt', a 'text', or \"share_picture\": true")
        if_away = d.get("if_user_away", "send")
        if if_away not in ("send", "skip", "wait"):
            raise ValueError("if_user_away must be send, skip or wait")
        return cls(
            on=on,
            prompt=d.get("prompt", ""),
            text=d.get("text", ""),
            delay_minutes=_range(d.get("delay_minutes"), (0.0, 0.0)),
            minutes=float(d.get("minutes", 30)),
            chance=float(d.get("chance", 1.0)),
            if_user_away=if_away,
            once=bool(d.get("once", False)),
            share_picture=bool(d.get("share_picture", False)),
        )


@dataclass
class SlowReplies:
    minutes: tuple = (0.0, 0.0)
    chance: float = 1.0
    days: str = "all"
    hours: tuple | None = None     # (start, end) in minutes after midnight, their local time

    @classmethod
    def from_dict(cls, d):
        days = d.get("days", "all")
        if days not in SLOW_DAYS:
            raise ValueError(f"slow_replies 'days' must be one of {', '.join(SLOW_DAYS)}")
        hours = d.get("hours")
        if hours is not None:
            if not (isinstance(hours, list) and len(hours) == 2):
                raise ValueError('slow_replies "hours" must look like ["08:00", "16:00"]')
            hours = (parse_time(hours[0]), parse_time(hours[1]))
        return cls(minutes=_range(d.get("minutes"), (1.0, 10.0)),
                   chance=float(d.get("chance", 1.0)), days=days, hours=hours)


@dataclass
class Contact:
    id: str
    screen_name: str
    persona: str
    model: str = ""
    icon: str = ""
    profile: str = ""
    temperature: float = 0.8
    away_message: str = "I'm away from my computer right now."
    start_online_chance: float = 0.5
    online_minutes: tuple = (20.0, 90.0)
    offline_minutes: tuple = (10.0, 60.0)
    away_chance: float = 0.25
    away_minutes: tuple = (5.0, 20.0)
    schedule: Schedule | None = None
    stay_while_chatting: bool = False
    slow_replies: SlowReplies | None = None
    pictures: PictureSet | None = None
    picture_sharing: str = "when_asked"
    unanswered_limit: int = 3      # first messages in a row with no reply before they back off
    cooldown_hours: float = 24.0   # how long they back off for
    timezone: object = None        # ZoneInfo, or None for the computer's time zone
    triggers: list = field(default_factory=list)

    @classmethod
    def from_dict(cls, cid, d):
        if not d.get("screen_name"):
            raise ValueError("missing 'screen_name'")
        presence = d.get("presence", {})
        sharing = d.get("pictures", "when_asked")
        if sharing not in SHARING_MODES:
            raise ValueError(f"'pictures' must be one of {', '.join(SHARING_MODES)}")
        return cls(
            id=cid,
            screen_name=d["screen_name"],
            persona=d.get("persona", ""),
            model=d.get("model", ""),
            icon=d.get("icon", ""),
            profile=d.get("profile", ""),
            temperature=float(d.get("temperature", 0.8)),
            away_message=d.get("away_message") or cls.away_message,
            start_online_chance=float(presence.get("start_online_chance", 0.5)),
            online_minutes=_range(presence.get("online_minutes"), (20.0, 90.0)),
            offline_minutes=_range(presence.get("offline_minutes"), (10.0, 60.0)),
            away_chance=float(presence.get("away_chance", 0.25)),
            away_minutes=_range(presence.get("away_minutes"), (5.0, 20.0)),
            schedule=Schedule.from_dict(presence["schedule"]) if presence.get("schedule") else None,
            stay_while_chatting=bool(presence.get("stay_while_chatting", False)),
            slow_replies=SlowReplies.from_dict(d["slow_replies"]) if d.get("slow_replies") else None,
            pictures=PictureSet(paths.CONTACTS / cid),
            picture_sharing=sharing,
            unanswered_limit=max(1, int(d.get("unanswered_limit", 3))),
            cooldown_hours=float(d.get("cooldown_hours", 24)),
            timezone=timefmt.zone(d.get("timezone", "")),
            triggers=[Trigger.from_dict(t) for t in d.get("triggers", [])],
        )


def load_contacts():
    """Returns (contacts, errors). Files starting with '_' are ignored."""
    contacts, errors = [], []
    if not paths.CONTACTS.exists():
        return contacts, errors
    for path in sorted(paths.CONTACTS.glob("*.json"), key=lambda p: paths.natural_key(p.name)):
        if path.name.startswith("_"):
            continue
        try:
            with open(path, encoding="utf-8") as f:
                contacts.append(Contact.from_dict(path.stem, json.load(f)))
        except Exception as e:
            errors.append(f"{path.name}: {e}")
    return contacts, errors
