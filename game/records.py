"""What's kept between nights, in the game's saves folder (records.json): the endings found, what the nights have come
to, what's been unlocked, and the options.

    rec = Records(folder)
    rec.ending("Supper")               an ending reached (the first time, remembered with the date)
    rec.night_over(stats)              a night done: add its tallies to the totals
    rec.options["volume"] ...          the options; rec.save() keeps them
Plain Python: the tests give it a scratch folder, never the real one."""
import json
import time
from pathlib import Path

ENDINGS = 7                     # (how many there are: their names are found, not told)
OPTIONS = {"volume": 80, "look": 50, "heart": True, "heartbeat": True, "orbs": True}
TALLIES = ("nights", "endings", "seconds", "longest", "bites", "slips", "falls", "swipes", "shakes")


class Records:
    def __init__(self, folder):
        self.path = Path(folder) / "records.json"
        self.found = {}                     # {ending: when first found}
        self.totals = {k: 0 for k in TALLIES}
        self.unlocks = []
        self.options = dict(OPTIONS)
        try:
            d = json.loads(self.path.read_text(encoding="utf-8"))
            self.found = dict(d.get("found", {}))
            self.totals.update({k: v for k, v in d.get("totals", {}).items() if k in self.totals})
            self.unlocks = list(d.get("unlocks", []))
            self.options.update({k: v for k, v in d.get("options", {}).items() if k in OPTIONS})
        except (OSError, ValueError):
            pass

    def save(self):
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.path.with_suffix(".tmp")
            tmp.write_text(json.dumps({"found": self.found, "totals": self.totals, "unlocks": self.unlocks,
                                       "options": self.options}, indent=1), encoding="utf-8")
            tmp.replace(self.path)
        except OSError:
            pass

    def ending(self, name):
        first = name not in self.found
        if first:
            self.found[name] = time.strftime("%Y-%m-%d")
        self.totals["endings"] += 1
        self.save()
        return first

    def night_over(self, stats):
        """A night done (an ending, or left): its tallies into the totals."""
        self.totals["nights"] += 1
        secs = int(stats.get("seconds", 0))
        self.totals["seconds"] += secs
        self.totals["longest"] = max(self.totals["longest"], secs)
        for k in ("bites", "slips", "falls", "swipes", "shakes"):
            self.totals[k] += int(stats.get(k, 0))
        self.save()
