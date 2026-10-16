"""ClaudeXP time: the real local month, day and time, but it's always 2001."""
from datetime import datetime

YEAR = 2001


def now():
    """Local time with the year set to 2001 (Feb 29 becomes Feb 28; 2001 had no leap day)."""
    real = datetime.now()
    day = 28 if (real.month, real.day) == (2, 29) else real.day
    return real.replace(year=YEAR, day=day)


def time_text(t=None):
    t = t or now()
    return t.strftime("%I:%M %p").lstrip("0")


def date_text(t=None):
    t = t or now()
    return f"{t.month}/{t.day}/{t.year}"


def long_date_text(t=None):
    t = t or now()
    return f"{t:%A, %B} {t.day}, {t.year}"
