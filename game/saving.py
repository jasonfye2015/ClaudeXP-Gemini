"""Saving the night (phase 4e): at the start of each act, and a quick save anywhere outside a conversation (F5, or
"Save here" in the pause). A save keeps where he is, her moods, the clock and the weather, how he's holding up, what
he's found and carries and given, her guests opened, what he's chosen, what's been said and what she remembers of
him tonight, her venom, his spells' memories given. What's alive in the den - her small ones, the lantern's mood, she
herself - starts fresh about him.

    saves = Saves(folder)
    saves.save(kind, night, talk)          kind: "act" or "quick"
    saves.list()                           -> [(kind, label)]: what there is to go on from, newest first
    saves.load(kind)                       -> (night, talk state) or None
    saves.clear()                          a new night begun: the old one's saves gone
    why_not(night, scene=False)            -> why a quick save can't be made here, or None
Plain JSON, one file a kind. The tests give it a scratch folder, never the real one."""
import json
import time
from pathlib import Path

VERSION = 1
KINDS = ("act", "quick")
FIELDS = {
    "": ("x", "y", "z", "yaw", "pitch", "time", "seen", "place", "moved", "pack", "taken", "given", "silk", "flags",
         "lies", "met", "items", "items_left", "held"),
    "finds": ("dropped",),
    "afflict": ("eye_lost", "bloodied", "coat", "down", "cycle_until", "said", "puddles", "t"),
    "moods": ("fascination", "patience", "hunger", "suspicion", "regard", "bites"),
    "body": ("health", "poison", "sanity", "stupor"),
    "acts": ("act", "request", "calling", "next_call", "t", "found", "outcomes"),
    "sky": ("clock", "weather", "strength", "next_weather", "target", "t", "puddles", "snow", "next_thunder"),
    "venom": ("active", "cured", "t", "next", "seen"),
    "spells": ("shown", "marks_seen"),
    "cocoons": ("burst", "burst_at"),
}
SETS = {("afflict", "said"), ("", "seen"), ("", "taken"), ("spells", "shown"), ("spells", "marks_seen"), ("cocoons", "burst")}
TUPLES = {("sky", "target")}
ACT_WORDS = {"threshold": "The way in", "audience": "Her loom", "gallery": "Her guests", "supper": "Supper",
             "crown": "The crown"}


def _plain(v):
    if isinstance(v, (set, tuple, list)):
        return [_plain(x) for x in (sorted(v, key=str) if isinstance(v, set) else v)]
    if isinstance(v, dict):
        return {str(k): _plain(x) for k, x in v.items()}
    return v


def capture(night, talk=None):
    """What's kept of the night now: a plain dict."""
    d = {"version": VERSION}
    for part, names in FIELDS.items():
        obj = getattr(night, part) if part else night
        d[part or "night"] = {k: _plain(getattr(obj, k)) for k in names}
    d["talk"] = {"memory": list(talk.memory), "lies": talk.lies} if talk is not None else {"memory": [], "lies": 0}
    return d


def restore(d, night=None):
    """A night made from a save. -> (night, talk state)."""
    from .night import Night
    if d.get("version") != VERSION:
        raise ValueError("a save from another version")
    n = night or Night()
    for part, names in FIELDS.items():
        obj = getattr(n, part) if part else n
        vals = d[part or "night"]
        for k in names:
            if k not in vals:
                continue
            v = vals[k]
            if (part, k) in SETS:
                v = set(v)
            elif (part, k) in TUPLES:
                v = tuple(v)
            elif (part, k) == ("", "given"):
                v = [tuple(x) for x in v]
            setattr(obj, k, v)
    n.vy, n.on, n._fall_from = 0.0, None, n.y
    n.her.state, n.her.until = "watch", n.her.t + 4.0       # (she's somewhere in the dark, watching, as she was)
    return n, dict(d.get("talk", {}))


def why_not(night, scene=False):
    """Why a quick save can't be made just now - or None, if it can."""
    if scene:
        return "Not while she's talking to you."
    if night.dying is not None or night.ending is not None:
        return "Not now."
    if night.venom.vision is not None:
        return "Not through her eyes."
    if abs(night.vy) > 1e-6 or night.teetering:
        return "Not while you're falling - or swaying."
    if night.her.state in ("hunt", "strike"):
        return "Not with her coming for you."
    return None


class Saves:
    def __init__(self, folder):
        self.folder = Path(folder)

    def _path(self, kind):
        return self.folder / f"night_{kind}.json"

    def save(self, kind, night, talk=None):
        d = capture(night, talk)
        d["saved"] = time.strftime("%Y-%m-%d %H:%M")
        d["label"] = self.label(kind, night)
        try:
            self.folder.mkdir(parents=True, exist_ok=True)
            tmp = self._path(kind).with_suffix(".tmp")
            tmp.write_text(json.dumps(d), encoding="utf-8")
            tmp.replace(self._path(kind))
            return True
        except OSError:
            return False

    @staticmethod
    def label(kind, night):
        act = ACT_WORDS.get(night.acts.act, night.acts.act.title())
        return f"{'The act begun' if kind == 'act' else 'Your quick save'}:  {act},  {night.clock_words()}"

    def read(self, kind):
        try:
            d = json.loads(self._path(kind).read_text(encoding="utf-8"))
            return d if d.get("version") == VERSION else None
        except (OSError, ValueError):
            return None

    def list(self):
        out = []
        for kind in KINDS:
            d = self.read(kind)
            if d is not None:
                out.append((d.get("saved", ""), kind, d.get("label", kind)))
        return [(kind, label) for _when, kind, label in sorted(out, reverse=True)]

    def load(self, kind):
        d = self.read(kind)
        if d is None:
            return None
        try:
            return restore(d)
        except (KeyError, TypeError, ValueError):
            return None

    def clear(self):
        for kind in KINDS:
            try:
                self._path(kind).unlink()
            except OSError:
                pass
