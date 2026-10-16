from datetime import datetime

LOCKED_YEAR = 2011


def format_locked_date(now: datetime) -> str:
    """Keep the live local weekday/month/day, but pin the displayed year."""
    return f"{now.strftime('%A, %B')} {now.day}, {LOCKED_YEAR}"


def format_locked_time(now: datetime) -> str:
    """Format the real local clock in the 12-hour style used by Windows 7."""
    return now.strftime("%I:%M %p").lstrip("0")
