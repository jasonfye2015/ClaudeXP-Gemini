"""Daily sleep schedules: the hours a buddy is awake and able to be online."""
import random
from datetime import datetime, time, timedelta

from . import timefmt


def parse_time(text) -> float:
    """'22:30' -> minutes after midnight. Hours past 24 mean after midnight ('25:00' = 1am)."""
    hours, _, minutes = str(text).strip().partition(":")
    value = int(hours) * 60 + int(minutes or 0)
    if not 0 <= value <= 36 * 60:
        raise ValueError(f"time {text!r} is out of range")
    return float(value)


def _range(value, what):
    if isinstance(value, str):
        value = [value, value]
    if not (isinstance(value, list) and len(value) == 2):
        raise ValueError(f"schedule '{what}' must be a time or [earliest, latest]")
    lo, hi = parse_time(value[0]), parse_time(value[1])
    return (min(lo, hi), max(lo, hi))


class Schedule:
    """Each day the buddy wakes at a random time in `wake` and sleeps at a random time in `sleep`.

    Weekend wake times apply on Saturday and Sunday mornings; weekend bedtimes apply on
    Friday and Saturday nights. Days of the week follow the in-game (2001) calendar.
    All times are in the buddy's own time zone: pass `now` already in that zone.
    """

    def __init__(self, weekday, weekend):
        self.weekday = weekday
        self.weekend = weekend
        self._plans = {}

    @classmethod
    def from_dict(cls, d):
        def part(key, fallback=None):
            src = d.get(key)
            if src is None:
                if fallback is None:
                    raise ValueError(f"schedule needs a '{key}' section")
                return fallback
            return {"wake": _range(src["wake"], "wake"), "sleep": _range(src["sleep"], "sleep")}

        weekday = part("weekday")
        return cls(weekday, part("weekend", weekday))

    def _plan(self, day, tzinfo):
        if day not in self._plans:
            midnight = datetime.combine(day, time(), tzinfo=tzinfo)
            dow = timefmt.shifted(midnight).weekday()  # Monday = 0
            wake = random.uniform(*(self.weekend if dow >= 5 else self.weekday)["wake"])
            sleep = random.uniform(*(self.weekend if dow in (4, 5) else self.weekday)["sleep"])
            sleep = max(sleep, wake + 30)
            self._plans[day] = (midnight + timedelta(minutes=wake), midnight + timedelta(minutes=sleep))
        return self._plans[day]

    def awake_until(self, now: datetime):
        """When the buddy goes to bed, or None if they're asleep right now."""
        for offset in (-1, 0):  # last night's bedtime may run past midnight
            wake, sleep = self._plan(now.date() + timedelta(days=offset), now.tzinfo)
            if wake <= now < sleep:
                return sleep
        return None

    def next_wake(self, now: datetime) -> datetime:
        for offset in range(3):
            wake, _ = self._plan(now.date() + timedelta(days=offset), now.tzinfo)
            if wake > now:
                return wake
        return now + timedelta(hours=8)
