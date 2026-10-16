"""The Claude Timeline's residents, as one era sees them.

    from residents import load
    r = load("RedFawks", 2011)        # who RedFawks is in October 2011 - or None if he isn't around then

The future is kept out structurally: only era files up to the requested year are ever opened, history entries that
haven't started yet are dropped, and something that ends after the era is shown as still ongoing. Earlier eras
reach a later one only as "used to be on ..." lines. See Residents/README.txt for the files.
"""
import json
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

TIMELINE = Path(__file__).resolve().parents[2]
RESIDENTS = TIMELINE / "Residents"
SNAPSHOT_MONTH, SNAPSHOT_DAY = 10, 15            # every era is a snapshot of October
SERVICE_NAMES = {"aim": "AIM", "irc": "FurNet IRC", "muck": "PawPrints MUCK", "msn": "MSN Messenger",
                 "yim": "Yahoo! Messenger", "icq": "ICQ", "skype": "Skype", "livejournal": "LiveJournal"}


def _load(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def era_years(name):
    """The eras a resident has files for (just the years, nothing opened)."""
    folder = RESIDENTS / name / "eras"
    return sorted(int(p.stem) for p in folder.glob("*.json") if p.stem.isdigit()) if folder.is_dir() else []


def names(year=None, tier=None):
    """Everyone in Residents (optionally: around in that era, of that tier)."""
    out = []
    for d in sorted(RESIDENTS.iterdir(), key=lambda p: p.name.lower()) if RESIDENTS.is_dir() else []:
        if not (d / "resident.json").exists():
            continue
        if year is not None and year not in era_years(d.name):
            continue
        if tier is not None and (_load(d / "resident.json") or {}).get("tier") != tier:
            continue
        out.append(d.name)
    return out


@dataclass
class Resident:
    name: str
    year: int
    core: dict                       # resident.json
    era: dict                        # eras/<year>.json
    history: list = field(default_factory=list)     # what has started by this era, as it stood then
    used_to: list = field(default_factory=list)     # accounts from earlier eras
    media: list = field(default_factory=list)       # media folders this era may use, newest first

    @property
    def tier(self):
        return self.core.get("tier", "background")

    @property
    def born(self):
        try:
            return date.fromisoformat(self.core.get("born", ""))
        except ValueError:
            return None

    @property
    def age(self):
        b = self.born
        if b is None:
            return None
        snap = date(self.year, SNAPSHOT_MONTH, SNAPSHOT_DAY)
        return snap.year - b.year - ((snap.month, snap.day) < (b.month, b.day))

    @property
    def persona(self):
        return self.era.get("persona", "")

    def service(self, key):
        return (self.era.get("services") or {}).get(key)

    def history_lines(self):
        """The visible history as plain sentences for a prompt."""
        out = []
        for h in self.history:
            if h.get("at") is not None:
                out.append(f"{h['text']} (in {h['at']}).")
            elif h.get("to") is not None:
                out.append(f"{h['text']} ({h['from']}-{h['to']}).")
            else:
                out.append(f"{h['text']} (since {h['from']}).")
        return out


def _visible_history(items, year):
    out = []
    for h in items or []:
        start = h.get("at", h.get("from"))          # "at": a one-time event; "from"/"to": something that lasted
        if not isinstance(start, int) or start > year:
            continue                             # hasn't happened yet
        end = h.get("to")
        shown = dict(h)
        if isinstance(end, int) and end >= year:
            shown.pop("to", None)                # still going on, as far as this era knows
        out.append(shown)
    return out


def _accounts(era):
    out = []
    for key, data in (era.get("services") or {}).items():
        if key == "directory" or not isinstance(data, dict):
            continue
        handle = data.get("screen_name") or data.get("nick") or data.get("name") or data.get("handle") or ""
        out.append((SERVICE_NAMES.get(key, key), handle))
    return out


def load(name, year):
    """The resident as the era of `year` knows them, or None if they aren't around in that era."""
    folder = RESIDENTS / name
    core = _load(folder / "resident.json")
    if core is None or year not in era_years(name):
        return None
    era = _load(folder / "eras" / f"{year}.json") or {}
    used_to = []
    current = {svc for svc, _h in _accounts(era)}
    for past in [y for y in era_years(name) if y < year]:            # never a later era
        for svc, handle in _accounts(_load(folder / "eras" / f"{past}.json") or {}):
            if svc not in current:
                used_to.append(f"used to be on {svc}" + (f" as {handle}" if handle else "") + f" (in {past})")
    media_root = folder / "media"
    media = [media_root / str(y) for y in sorted((int(p.name) for p in media_root.iterdir() if p.name.isdigit()),
                                                 reverse=True) if y <= year] if media_root.is_dir() else []
    return Resident(name=name, year=year, core=core, era=era, history=_visible_history(core.get("history"), year),
                    used_to=used_to, media=media)
