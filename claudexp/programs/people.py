"""Helpers shared by the programs whose people are simulated (ClaudeMUCK, ClaudeIRC).

The cast is ClaudeAIM's buddies plus each program's own regulars. A buddy can have a
per-program section in their AIM contact file (e.g. "muck": {...} or "irc": {...}).
"""
import json
import re

from .aim import ensure_aim_path

ensure_aim_path()
from claudeaim import paths as aim_paths  # noqa: E402
from claudeaim import timefmt  # noqa: E402
from claudeaim.contacts import load_contacts  # noqa: E402


def load_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    tmp.replace(path)


def mentions(name, text, prefix=False):
    """Does text name this person as a word ('Ink' isn't in 'think')? prefix=True also counts the first five
    letters of a long name ('Tessel' for Tessellate)."""
    low, name = text.lower(), name.lower()
    if re.search(rf"(?<![a-z0-9]){re.escape(name)}(?![a-z0-9])", low):
        return True
    return prefix and len(name) > 4 and re.search(rf"(?<![a-z0-9]){re.escape(name[:5])}", low) is not None


def clock_minutes(text):
    """'22:30' -> minutes after midnight ('25:00' = 1am the next day)."""
    h, _, m = str(text).partition(":")
    return int(h) * 60 + int(m or 0)


def parse_hours(hours):
    return (clock_minutes(hours[0]), clock_minutes(hours[1])) if hours else None


def available(contact=None, hours=None):
    """Is this person awake and free to be online? Buddies follow their AIM sleep schedule
    (in their own time zone); regulars follow an hours window in local time."""
    if contact is not None:
        sched = contact.schedule
        return sched is None or sched.awake_until(timefmt.local_now(contact.timezone)) is not None
    if hours is None:
        return True
    now = timefmt.local_now()
    m = now.hour * 60 + now.minute
    start, end = hours
    return start <= m < end or start <= m + 1440 < end


def load_buddies(section):
    """(contacts with their per-program section dicts, load errors)."""
    contacts, errors = load_contacts()
    out = []
    for c in contacts:
        raw = load_json(aim_paths.CONTACTS / f"{c.id}.json", {})
        out.append((c, raw.get(section, {})))
    return out, errors


def aim_screen_name():
    from claudeaim.storage import Settings
    return Settings()["screen_name"] or ""
