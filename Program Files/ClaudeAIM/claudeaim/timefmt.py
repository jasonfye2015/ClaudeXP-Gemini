"""Clock helpers. Everything the user sees happens in 2001 (matching the ClaudeXP clock).

A tz of None means the computer's own time zone. Buddies with a "timezone" pass
their ZoneInfo, so their clock (and their timestamps) are their local time.
"""
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

YEAR = 2001


def zone(name: str):
    """ZoneInfo for an IANA name like 'Europe/London', or None for blank."""
    if not name:
        return None
    try:
        return ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError):
        raise ValueError(f"unknown timezone {name!r} (use names like 'Europe/London' "
                         "or 'America/New_York')") from None


def local_now(tz=None) -> datetime:
    """The current time, time-zone aware, in tz (or the computer's zone)."""
    return datetime.now(tz) if tz else datetime.now().astimezone()


def shifted(dt: datetime | None = None) -> datetime:
    dt = dt or datetime.now()
    try:
        return dt.replace(year=YEAR)
    except ValueError:  # Feb 29: 2001 had none
        return dt.replace(year=YEAR, day=28)


def stamp(iso: str, tz=None) -> str:
    """'10/7/2001 9:15:02 AM' for a saved ISO timestamp, shown in tz."""
    dt = datetime.fromisoformat(iso)
    if dt.tzinfo is None:
        dt = dt.astimezone()  # older entries were saved in the computer's local time
    dt = dt.astimezone(tz) if tz else dt.astimezone()
    s = shifted(dt)
    return f"{s.month}/{s.day}/{s.year} {s.strftime('%I:%M:%S %p').lstrip('0')}"


def now_text(tz=None) -> str:
    s = shifted(local_now(tz))
    return f"{s.strftime('%A, %B')} {s.day}, {s.year}, {s.strftime('%I:%M %p').lstrip('0')}"


def clock_text(tz=None) -> str:
    """Just the time and weekday, e.g. 'Sunday 9:40 PM'."""
    s = shifted(local_now(tz))
    return f"{s.strftime('%A')} {s.strftime('%I:%M %p').lstrip('0')}"
