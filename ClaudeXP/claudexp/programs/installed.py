"""What's installed and how much it's used: the bookkeeping behind Add or Remove Programs and the Desktop Cleanup
Wizard.

- data/program_usage.json: {key: {"last": unix time, "count": n, "recent": [unix times in the last 30 days]}}
- data/removed_programs.json: the programs you've removed (they vanish from the desktop, the Start menu and Run, and
  can be put back from Add New Programs). Nothing is deleted: removing is reversible, as a reinstall from CD was.
"""
import hashlib
import time
from datetime import datetime

from ..paths import DATA
from .people import load_json, save_json

USAGE_FILE = DATA / "program_usage.json"
REMOVED_FILE = DATA / "removed_programs.json"
MONTH = 30 * 86400

# Parts of Windows (removed, if at all, through Add/Remove Windows Components) and things that hold ClaudeXP up.
WINDOWS = {"notepad", "mycomputer", "calc", "paint", "cmd", "taskmgr", "wordpad", "charmap", "cleanmgr", "msinfo",
           "sysrestore", "sndrec", "tour", "search", "helpctr", "winupdate", "outlook", "wab", "wmp", "iexplore",
           "defrag", "connect", "antivirus", "solitaire", "spider", "freecell", "hearts", "minesweeper", "pinball",
           "zone", "ibackgammon", "icheckers", "ihearts", "ireversi", "ispades", "moviemaker", "winmsgr",
           "hotmail", "livejournal", "mediaarchive", "tvmovies", "activate", "arp"}
# publishers and sizes for the list (anything else gets a made-up but stable size)
PUBLISHERS = {"aim": "ClaudeAIM", "navigator": "Netscape Communications", "msn": "Microsoft Corporation",
              "yim": "Yahoo! Inc.", "icq": "ICQ Inc.", "trillian": "Cerulean Studios", "skype": "Skype Technologies",
              "kik": "Kik Interactive", "stylexp": "TGTSoft", "nero": "Ahead Software AG", "alcohol120": "Alcohol Soft",
              "winrar": "RARLAB", "winzip": "WinZip Computing", "flash": "Macromedia", "adaware": "Lavasoft",
              "realplayer": "RealNetworks", "quicktime": "Apple Computer, Inc.", "doom": "id Software",
              "doom2": "id Software", "wolf3d": "id Software", "heretic": "Raven Software", "hexen": "Raven Software"}
SIZES_MB = {"aim": 9.8, "navigator": 21.4, "msn": 4.2, "yim": 6.9, "icq": 8.1, "trillian": 3.6, "skype": 11.2,
            "kik": 2.4, "nero": 28.7, "alcohol120": 12.3, "winrar": 2.1, "winzip": 2.8, "flash": 1.4, "adaware": 3.9,
            "realplayer": 14.6, "quicktime": 18.2, "stylexp": 5.3, "doom": 12.4, "doom2": 14.6}


def removable(program):
    return program.listed and program.key not in WINDOWS


# ---- usage ----------------------------------------------------------------------------------------------------------

def record(key):
    usage = load_json(USAGE_FILE, {})
    now = time.time()
    u = usage.setdefault(key, {"last": 0, "count": 0, "recent": []})
    u["last"] = now
    u["count"] = u.get("count", 0) + 1
    u["recent"] = [t for t in u.get("recent", []) if now - t < MONTH][-60:] + [now]
    save_json(USAGE_FILE, usage)


def usage(key):
    return load_json(USAGE_FILE, {}).get(key, {})


def last_used(key):
    """The date it was last used (in ClaudeXP's 2001), or None."""
    ts = usage(key).get("last")
    if not ts:
        return None
    real = datetime.fromtimestamp(ts)
    return real.replace(year=2001, day=min(real.day, 28) if real.month == 2 else real.day)


def frequency(key):
    """'frequently', 'occasionally' or 'rarely' - as Add or Remove Programs put it."""
    now = time.time()
    n = sum(1 for t in usage(key).get("recent", []) if now - t < MONTH)
    return "frequently" if n >= 10 else "occasionally" if n >= 3 else "rarely"


def size_mb(key):
    if key in SIZES_MB:
        return SIZES_MB[key]
    h = int(hashlib.md5(key.encode()).hexdigest()[:6], 16)
    return round(1.5 + (h % 4000) / 100, 2)


# ---- removing --------------------------------------------------------------------------------------------------------

def removed():
    return set(load_json(REMOVED_FILE, []))


def is_removed(key):
    return key in removed()


def set_removed(key, gone=True):
    keys = removed()
    (keys.add if gone else keys.discard)(key)
    save_json(REMOVED_FILE, sorted(keys))
