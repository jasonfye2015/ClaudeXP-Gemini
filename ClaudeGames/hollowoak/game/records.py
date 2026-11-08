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

ENDINGS = 8                     # (how many there are: their names are found, not told)
OPTIONS = {"volume": 80, "music": 70, "look": 50, "heart": True, "heartbeat": True, "orbs": True,
           "voice": "",                # (her words: a model's name, or "none"; "" - not chosen yet: the best there is)
           "aloud": True,              # (her voice, heard: Kathleen, rasping - where the Timeline's voice runtime is)
           "her_size": 100, "his_size": 100,     # (the size of her words and his, in percent)
           "venom_fx": True,            # (her venom: the edges of his sight darkening and pulsing)
           "steady": False,             # (steadier light: the lantern's flicker and the lightning calmed)
           "text_speed": 50}            # (how fast her words come)            # (her venom: the edges of his sight darkening and pulsing)
TALLIES = ("nights", "endings", "seconds", "longest", "bites", "slips", "falls", "swipes", "shakes")


class Records:
    def __init__(self, folder):
        self.path = Path(folder) / "records.json"
        self.found = {}                     # {ending: when first found}
        self.totals = {k: 0 for k in TALLIES}
        self.unlocks = []
        self.reputation = {"met": 0, "summary": ""}  # (what she remembers of him, from other nights)
        self.notes = {}                     # (his notebook: page -> when first written; kept across deaths)
        self.learned = {}                   # (what she made of each gift: item -> [lines]; kept across nights)
        self.options = dict(OPTIONS)
        try:
            d = json.loads(self.path.read_text(encoding="utf-8"))
            self.found = dict(d.get("found", {}))
            self.totals.update({k: v for k, v in d.get("totals", {}).items() if k in self.totals})
            self.unlocks = list(d.get("unlocks", []))
            self.reputation.update(d.get("reputation", {}))
            self.notes = dict(d.get("notes", {}))
            self.learned = {k: list(v) for k, v in d.get("learned", {}).items()}
            self.options.update({k: v for k, v in d.get("options", {}).items() if k in OPTIONS})
        except (OSError, ValueError):
            pass

    def save(self):
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.path.with_suffix(".tmp")
            tmp.write_text(json.dumps({"found": self.found, "totals": self.totals, "unlocks": self.unlocks,
                                       "reputation": self.reputation, "notes": self.notes, "learned": self.learned,
                                       "options": self.options}, indent=1), encoding="utf-8")
            tmp.replace(self.path)
        except OSError:
            pass

    def note(self, page):
        """A page of his notebook written (once): -> True the first time."""
        if page in self.notes:
            return False
        self.notes[page] = time.strftime("%Y-%m-%d")
        self.save()
        return True

    def learn(self, item, line):
        """Written beside a thing in his satchel: what she made of it (once). -> True the first time."""
        have = self.learned.setdefault(item, [])
        if line in have:
            return False
        have.append(line)
        self.save()
        return True

    def ending(self, name):
        first = name not in self.found
        if first:
            self.found[name] = time.strftime("%Y-%m-%d")
        self.totals["endings"] += 1
        self.save()
        return first

    def night_over(self, stats):
        """A night done (an ending, or left): its tallies into the totals. A night gone on with from a save is the same
        night: its time and its tallies count, but not as another night, nor another meeting."""
        if not stats.get("resumed"):
            self.totals["nights"] += 1
        secs = int(stats.get("seconds", 0))
        self.totals["seconds"] += secs
        self.totals["longest"] = max(self.totals["longest"], secs)
        for k in ("bites", "slips", "falls", "swipes", "shakes"):
            self.totals[k] += int(stats.get(k, 0))
        self.remembered(stats)
        self.save()

    def remembered(self, stats):
        """What she keeps of him from a night, for the next: how it ended, how he went, whether he lied."""
        r = self.reputation
        if not stats.get("resumed"):
            r["met"] = int(r.get("met", 0)) + 1
        bits = []
        end = stats.get("ending")
        bits.append(f"Last time, it ended in {end}." if end else "Last time, he left before the night was out.")
        if stats.get("lies"):
            bits.append(f"He lied to you {stats['lies']} time{'s' if stats['lies'] != 1 else ''}.")
        manner = stats.get("manner", 0.0)
        if manner > 0.5:
            bits.append("He walked your silk with care.")
        elif manner < -0.3:
            bits.append("He scrambled on your silk like prey.")
        if stats.get("kept"):
            bits.append("You kept this of him: " + stats["kept"])
        r["summary"] = " ".join(bits)
