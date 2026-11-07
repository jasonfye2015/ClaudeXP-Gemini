"""The three save slots: slot1.json .. slot3.json in the game's Saves folder (host.saves("claudenites")), each written
whole to a .tmp first and then moved into place, so a slot is never half-written."""
import json
import os
import time
from pathlib import Path

SLOTS = 3


class Saves:
    def __init__(self, folder):
        self.folder = Path(folder)

    def path(self, slot):
        return self.folder / f"slot{slot + 1}.json"

    def load(self, slot):
        try:
            return json.loads(self.path(slot).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None

    def save(self, slot, game_json):
        self.folder.mkdir(parents=True, exist_ok=True)
        data = dict(game_json)
        data["saved"] = time.time()
        data["played"] = data.get("played", 0)
        tmp = self.path(slot).with_suffix(".tmp")
        tmp.write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
        os.replace(tmp, self.path(slot))

    def delete(self, slot):
        try:
            self.path(slot).unlink()
        except OSError:
            pass

    def summary(self, slot):
        """A line or two for the slot's card, or None when it's empty."""
        d = self.load(slot)
        if not d:
            return None
        p = d.get("player", {})
        st = p.get("stats", {})
        when = time.strftime("%d %b %Y, %H:%M", time.localtime(d.get("saved", 0)))
        return {"level": p.get("level", 1), "gold": p.get("gold", 0), "floor": d.get("run_floor", 1),
                "deepest": st.get("deepest", 0), "deaths": st.get("deaths", 0), "kills": st.get("kills", 0),
                "when": when}
