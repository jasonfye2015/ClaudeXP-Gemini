"""Her babies, close to him.

Danglers: now and then one drops on a single thread from the dark overhead, a little way before him, and stops at the
height of his face - and hangs there, turning, bobbing on its thread. Walk into it and the thread is gone and it's on
his face, and off across his eyes. Left alone a while, it climbs back up into the dark.

The lantern: when it goes out they come - one up the wand and onto the lantern a few seconds after, then another every
ten to twenty seconds, until five to seven are crawling all over it. A shake that lights it again and they let go, each
hanging a moment from the lantern on a thread of white silk, swinging, before it falls away; a shake that doesn't
light it throws one or two off.

    danglers = Danglers(rng);  danglers.step(dt, night) -> events;  danglers.active()
    swarm = Swarm(rng);        swarm.step(dt, lamp_state, lamp_events) -> events;  swarm.babies
Plain Python: the renderer places the swarm on the wand and lantern (engine/held.py's axes); the tests watch both."""
import math

DROP_EVERY = (25.0, 45.0)
SWARM_FIRST = (2.0, 4.0)
SWARM_EVERY = (10.0, 20.0)
SWARM_MOST = (5, 7)
LANTERN_R = 0.05                # (round the lantern, just outside its posts)
CAP = -0.03                     # (the highest a baby climbs on it: its cap; and its foot, below)
FOOT = -0.195


class Danglers:
    def __init__(self, rng):
        self.rng = rng
        self.t = 0.0
        self.next = rng.uniform(*DROP_EVERY)
        self.hanging = []

    def step(self, dt, night):
        self.t += dt
        rng = self.rng
        events = []
        if self.t >= self.next and len(self.hanging) < 2:
            d = self._drop(night)
            if d is None:
                self.next = self.t + 1.0                          # (nowhere to hang just now: soon)
            else:
                self.hanging.append(d)
                self.next = self.t + rng.uniform(*DROP_EVERY)
                events.append(("dangler", "drop"))
        ex, ey, ez = night.eye
        keep = []
        for d in self.hanging:
            if d["state"] == "drop":
                d["y"] -= max(0.3, min(2.4, (d["y"] - d["stop"]) * 3.0)) * dt     # (fast, slowing as it comes)
                if d["y"] <= d["stop"]:
                    d["y"], d["state"], d["until"] = d["stop"], "hang", rng.uniform(10, 22)
            elif d["state"] == "hang":
                d["until"] -= dt
                if d["until"] <= 0:
                    d["state"] = "climb"
            else:
                d["y"] += 0.7 * dt
                if d["y"] >= d["top"] - 0.05:
                    continue                                      # (gone up into the dark)
            if math.hypot(d["x"] - ex, d["z"] - ez) < 0.36 and abs(d["y"] - ey) < 0.45:
                night.crawlers.scurry(d["size"])                  # (walked into: on his face, and away)
                events.append(("dangler", "face"))
                continue
            keep.append(d)
        self.hanging = keep
        return events

    def _drop(self, night):
        """Somewhere a little before him, at his own level, with room overhead to have come down from."""
        rng, t = self.rng, night.tree
        ex, ey, ez = night.eye
        for _ in range(12):
            a = night.yaw + rng.uniform(-0.45, 0.45)
            r = rng.uniform(1.3, 2.8)
            x, z = ex + math.sin(a) * r, ez - math.cos(a) * r
            feet = night.floor_at(x, z, night.y + 0.3)
            if abs(feet - night.y) > 0.5 or not t.can_stand(x, z, feet, 0.12):
                continue
            ceil = t.ceiling_at(x, z, feet)
            top = min(ey + 5.0, ceil if ceil is not None else ey + 5.0)
            if top < ey + 0.5:
                continue
            stop = ey + rng.uniform(-0.1, 0.05)
            return {"x": x, "z": z, "top": top, "y": top, "stop": stop, "state": "drop",
                    "size": rng.uniform(0.12, 0.18), "phase": rng.uniform(0, math.tau)}
        return None

    def active(self):
        """[(x, y, z, top, size, phase)] - each one where it hangs, and where its thread goes up to."""
        return [(d["x"], d["y"], d["z"], d["top"], d["size"], d["phase"]) for d in self.hanging]


class Swarm:
    def __init__(self, rng):
        self.rng = rng
        self.t = 0.0
        self.next = None
        self.most = 0
        self.dark = False           # (the lantern out: they're coming)
        self.babies = []            # {state: wand|lantern|hang|fall, ...}

    def crawling(self):
        return [b for b in self.babies if b["state"] in ("wand", "lantern")]

    def step(self, dt, lamp_state, lamp_events):
        self.t += dt
        rng = self.rng
        events = []
        if lamp_state == "out":
            if not self.dark:
                self.dark = True
                self.next = self.t + rng.uniform(*SWARM_FIRST)
                self.most = rng.randint(*SWARM_MOST)
            if self.t >= self.next and len(self.crawling()) < self.most:
                self.babies.append({"state": "wand", "s": 0.0, "speed": rng.uniform(0.09, 0.16),
                                    "size": rng.uniform(0.03, 0.046), "phi": 0.0, "h": 0.0, "head": 0.0,
                                    "anim": rng.uniform(0, 3), "rest": 0.0, "seed": rng.random()})
                self.next = self.t + rng.uniform(*SWARM_EVERY)
                events.append(("swarm", "up"))
        else:
            self.dark = False
        if "relit" in lamp_events:                                  # (light: they let go)
            for b in self.crawling():
                self._let_go(b)
            if self.babies:
                events.append(("swarm", "off"))
        elif "failed" in lamp_events:                               # (thrown about: one or two let go)
            for b in self.crawling()[:rng.randint(1, 2)]:
                self._let_go(b)
        keep = []
        for b in self.babies:
            st = b["state"]
            if st == "wand":                                       # (up the wand from his hand to its crook)
                b["s"] += b["speed"] * dt / 0.4
                b["anim"] += dt * 9
                if b["s"] >= 1.0:
                    b["state"], b["phi"], b["h"], b["head"] = "lantern", rng.uniform(0, math.tau), CAP, -math.pi / 2
            elif st == "lantern":                                  # (all over it: about, up and down, in fits)
                if b["rest"] > 0:
                    b["rest"] -= dt
                    b["anim"] += dt * 0.5
                else:
                    v = b["speed"] * 0.6
                    b["head"] += rng.gauss(0, 2.5) * dt
                    b["phi"] += math.cos(b["head"]) * v * dt / LANTERN_R
                    b["h"] += math.sin(b["head"]) * v * dt
                    if not FOOT <= b["h"] <= CAP:
                        b["h"] = max(FOOT, min(CAP, b["h"]))
                        b["head"] = -b["head"]
                    b["anim"] += dt * 9
                    if rng.random() < dt * 0.6:
                        b["rest"] = rng.uniform(0.3, 1.5)
            elif st == "hang":                                     # (on its thread, swinging, letting it out)
                b["len"] = min(b["reach"], b["len"] + dt * 0.6)
                b["until"] -= dt
                b["anim"] += dt * 2
                if b["until"] <= 0:
                    b["state"], b["fall"], b["vy"] = "fall", 0.0, 0.0
            else:                                                  # (and away, thread and all)
                b["vy"] += 9.0 * dt
                b["fall"] += b["vy"] * dt
                if b["fall"] > 3.0:
                    continue
            keep.append(b)
        self.babies = keep
        return events

    def _let_go(self, b):
        b["state"], b["len"], b["reach"] = "hang", 0.0, self.rng.uniform(0.05, 0.14)
        b["until"] = self.rng.uniform(1.5, 4.0)
        if b.get("s", 1.0) < 1.0:                                  # (still on the wand: it lets go from there)
            b["phi"], b["h"] = None, b["s"]
