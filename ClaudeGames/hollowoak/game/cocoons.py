"""Her guests: the suitors before him, wrapped in silk where she hung them - four against the wall of the hollow's floor,
two in the gallery's chamber, and one high by the crown that she will not speak of. Each has what he brought lying
beneath him. Look closer (F) and the silk splits, and her small ones pour out of it - and he learns who it was (a page of
his notes).

    cocoons = Cocoons(tree)
    cocoons.spots            [{"id", "top" (where it hangs from), "pos" (its middle), "lean", "keepsake", "floor"}]
    cocoons.near(night)      the one he's close to and looking at, or None
    cocoons.examine(night, spot)   -> events: ("cocoon", id, pos) - the burst; the rest is the night's to do
Plain Python: the tests walk up to them."""
import math

from . import tree as T

LENGTH = 0.85                    # (a man, wrapped: a little taller than he is)
REACH = 1.7                      # (close enough to look at, and touch)
# where each hangs: (id, how it's placed, angle or chamber, keepsake)
PLACES = (("orrin", "floor", 1.55, "lute"), ("aldric", "floor", 2.95, "sword"), ("wick", "floor", 4.35, "picks"),
          ("isolde", "floor", 5.75, "arrows"),                        # (the four on the floor: between the fungus)
          ("maudren", "gallery", -0.12, "book"), ("fennick", "gallery", 0.14, "beads"),
          ("unnamed", "crown", 0.0, None))


class Cocoons:
    def __init__(self, tree):
        self.tree = tree
        self.spots = [self._place(*p) for p in PLACES]
        self.burst = set()                     # (tonight: split already)
        self.burst_at = {}                     # (when: for the silk torn loose, drifting)

    def _place(self, sid, where, a, keepsake):
        t = self.tree
        if where == "floor":                   # (against the wall of the hollow's floor, hung from it)
            r = t.base_r(a, 0.6) - 0.5
            ground = t.ground(math.cos(a) * r, math.sin(a) * r)
            mid = (math.cos(a) * r, ground + 0.12 + LENGTH / 2, math.sin(a) * r)
            top = (math.cos(a) * (r + 0.35), ground + 2.4, math.sin(a) * (r + 0.35))
            floor = ground
        else:
            name = "gallery" if where == "gallery" else "crown"
            start, run = next((s, n) for nm, s, n in T.LANDINGS if nm == name)
            h = t.landing_h[name]
            th = t.theta_of(start + run / 2) + a
            back = t.wall_r(th, h + 1.4) - (0.55 if where == "gallery" else 0.6)
            mid = (math.cos(th) * back, h + 0.12 + LENGTH / 2 + (0.8 if where == "crown" else 0.0), math.sin(th) * back)
            top = (math.cos(th) * (back + 0.3), h + (2.4 if where == "gallery" else 3.4), math.sin(th) * (back + 0.3))
            a, floor = th, h
        return {"id": sid, "pos": mid, "top": top, "angle": a, "keepsake": keepsake, "floor": floor,
                "lean": 0.18 if where != "crown" else 0.05}

    def near(self, night):
        ex, ey, ez = night.eye
        look = (math.sin(night.yaw) * math.cos(night.pitch), math.sin(night.pitch),
                -math.cos(night.yaw) * math.cos(night.pitch))
        best = None
        for s in self.spots:
            x, y, z = s["pos"]
            d = math.dist((x, y, z), (ex, ey, ez))
            if d > REACH:
                continue
            to = ((x - ex) / d, (y - ey) / d, (z - ez) / d)
            facing = sum(a * b for a, b in zip(look, to))
            if facing > 0.75 and (best is None or d < best[0]):
                best = (d, s)
        return best[1] if best else None

    def examine(self, night, spot):
        """He touches it: if it's whole, it splits, and they pour out."""
        if spot["id"] in self.burst:
            return [("cocoon", spot["id"], spot["pos"], False)]
        self.burst.add(spot["id"])
        self.burst_at[spot["id"]] = night.time
        return [("cocoon", spot["id"], spot["pos"], True)]
