"""Default programs (Set Program Access and Defaults, Internet Options > Programs): which browser opens links from
other programs, and which player opens music and video files."""
from .paths import DATA
from .programs.people import load_json, save_json

FILE = DATA / "defaults.json"
CHOICES = {"browser": [("iexplore", "Internet Explorer"), ("navigator", "Netscape Navigator")],
           "media": [("wmp", "Windows Media Player"), ("realplayer", "RealPlayer"), ("quicktime", "QuickTime Player")]}
FALLBACK = {"browser": "iexplore", "media": "wmp"}


def get(kind):
    value = load_json(FILE, {}).get(kind, FALLBACK[kind])
    from .programs import installed
    if installed.is_removed(value):                 # the chosen one was removed: back to Windows' own
        return FALLBACK[kind]
    return value


def set(kind, value):        # noqa: A001 (as in 'set a default')
    data = load_json(FILE, {})
    data[kind] = value
    save_json(FILE, data)
