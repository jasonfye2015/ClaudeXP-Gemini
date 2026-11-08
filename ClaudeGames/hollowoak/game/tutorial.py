"""The first night (phase 7e): the oak, learned. The letter leads him from one lesson to the next; at each, a note in
his own hand in the margin, and then it's his to do - shown, then tried. A gentler night than the others: her hunger
rises, but she won't hunt him; if something gives out, she lets him up ("Not tonight, little wizard. Learn first.");
one bite, safe, to learn her venom by. Enter skips a lesson; F9 lets the letter lead him through the rest.

    tut = Tutorial(night)
    tut.step(dt, night, events, model=False) -> requests: ("travel", task) for the guide, ("call", act), ...
    tut.note          the margin note now, or None;  tut.prompt  what to do (once it's his turn)
    tut.his_turn      whether he has the night in his hands now (else the letter's leading him)
    tut.skip()        on to the next lesson
    tut.done
Plain Python: the tests take the lessons."""
import math

from .spells import mark_at
from .web import Bridge

# (id, act it waits for, where the letter leads him first, the margin note, "try" or "see", what he's to do)
LESSONS = (
    ("walk", "threshold", None,
     "Look about: the mouse. Walk: W A S D - slowly. She feels every step.", "try", "Walk a little way."),
    ("lantern", "threshold", None,
     "The lantern's gone out. A shake (E) usually brings it back. Usually.", "try", "Shake the lantern: E."),
    ("light", "threshold", ("light_spot",),
     "Light (1) shows what the dark hides - and old marks cut in the wood. It hurts her eyes.", "try",
     "Cast Light: 1."),
    ("take", "threshold", ("ring_spot",),
     "Something glints in the mud. Look at it - F takes it.", "try", "Look at the ring, and press F."),
    ("satchel", "threshold", None,
     "Tab opens your satchel. The mouse wheel puts a thing in your hand; G sets it down. It holds four.", "try",
     "Open your satchel (Tab), then close it."),
    ("orbs", "threshold", None,
     "Red, my health - green, poison rising under it. Blue, my mind - yellow, stupor. If they meet, she has me.",
     "see", None),
    ("small", "threshold", None,
     "Her small ones. When two run over my face, I swipe them off without thinking.", "see", None),
    ("loom", "threshold", ("loom_edge",),
     "Her loom. Onto it slowly - every step hums through her web, and she feels it.", "try",
     "Step onto her loom."),
    ("words", "audience", None,
     "Her words, and mine. What I'd truly say pleases her best - honest, curious. Flattery doesn't. Lies don't.",
     "see", None),
    ("guests", "gallery", ("orrin_spot",),
     "Her guests, wrapped. Look closer (F) - and what they brought lies under them.", "try",
     "Look closer at the one before you: F."),
    ("notebook", "gallery", None,
     "What I learn is written in my notebook. Esc lifts it - the night doesn't stop while I read. P truly pauses.",
     "try", "Lift your notebook (Esc), then put it away."),
    ("strand", "gallery", ("strand_end",),
     "A strand: a short way up, and a test of nerve. Sway too far and I'm off - A and D lean against it.", "try",
     "Step out onto the strand."),
    ("warmth", "gallery", None,
     "Warmth (2): a small comfort. Never on her silk.", "try", "Cast Warmth (2), on solid wood."),
    ("save", "gallery", None,
     "F5 saves wherever I stand. Each act saves itself, too.", "try", "Save: F5."),
    ("supper", "supper", ("larder_door",),
     "She calls me to supper. Offer her what she hungers for - what a thing's worth changes with her mood, and the "
     "hour.", "try", "Go into her larder."),
    ("venom", "crown", None,
     "Her bite. I live - but her venom stays, and sometimes I see through her eyes.", "see", None),
    ("antidote", "crown", ("antidote_spot",),
     "The phial her eyes showed me. F takes it; Q drinks it.", "try", "Take the phial (F), and drink it (Q)."),
    ("crown", "crown", ("crown_edge",),
     "The crown, under the moon. Her last words of the night - then T waits with her for the light.", "try",
     "Step onto her web under the moon."),
)
SEE_FOR = 7.0


class Tutorial:
    def __init__(self, night):
        self.at = 0
        self.phase = "travel"
        self.t = 0.0
        self.since = 0.0
        self.note = None
        self.prompt = None
        self.his_turn = False
        self.done = False
        self.mark = {}

    def skip(self):
        if not self.done:
            self._next()

    def _next(self):
        self.at += 1
        self.phase, self.since = "travel", 0.0
        self.note = self.prompt = None
        self.his_turn = False
        self.mark = {}
        if self.at >= len(LESSONS):
            self.done = True

    @property
    def lesson(self):
        return LESSONS[self.at] if self.at < len(LESSONS) else None

    def step(self, dt, n, events, ui):
        """ui: what the view saw him do - {"satchel": opened and shut, "notebook": ..., "saved": ...}"""
        out = []
        if self.done:
            return out
        self.t += dt
        self.since += dt
        lid, act, travel, note, how, prompt = self.lesson
        order = ("threshold", "audience", "gallery", "supper", "crown", "dawn")
        if order.index(n.acts.act) < order.index(act):
            if act == "supper" and n.acts.act == "gallery":
                out.append(("call", "supper"))                 # (the lessons before it done: she calls him down)
            self.his_turn = True                                 # (until it's time: the night's his)
            self.note = None
            return out
        if self.phase == "travel":
            if travel and lid not in ("venom",):
                out.append(("travel", travel[0]))
                self.his_turn = False
                if not self.mark.get("asked"):
                    self.mark["asked"] = True
                return out
            self._begin(n)
        if self.phase == "travel_done":
            self._begin(n)
        if self.phase == "show":
            self.note = note
            if how == "see":
                self.his_turn = True
                if self.since > SEE_FOR + 0.25 * len(note.split()) and (lid != "venom" or n.venom.vision is None and
                                                                        "larder" in n.venom.seen):
                    self._next()
                return out
            self.phase, self.since = "try", 0.0
        if self.phase == "try":
            self.note, self.prompt, self.his_turn = note, prompt, True
            if self._tried(lid, n, events, ui):
                self.prompt = "Yes."
                self.phase, self.since = "learned", 0.0
        if self.phase == "learned" and self.since > 1.4:
            self._next()
        return out

    def arrived(self):
        """The guide got him there."""
        if self.phase == "travel":
            self.phase = "travel_done"

    def _begin(self, n):
        lid = self.lesson[0]
        self.phase, self.since = "show", 0.0
        self.mark["moved"] = n.moved
        if lid == "lantern":
            n.lamp.state, n.lamp.level = "out", 0.0                 # (it gutters, as it does)
        elif lid == "small":
            n.crawlers.scurry(0.0)
            n.crawlers.scurry(0.15)
        elif lid == "venom" and not n.venom.active:
            n.bitten()                                             # (one bite, safe: to learn it by)
            n.venom.next = n.venom.t + 4.0

    def _tried(self, lid, n, events, ui):
        kinds = [e for e in events]
        if lid == "walk":
            return n.moved - self.mark.get("moved", 0.0) > 2.0
        if lid == "lantern":
            return n.lamp.state != "out"
        if lid == "light":
            return "mark_roots" in n.spells.marks_seen or any(e[:3] == ("spell", "light", "cast") for e in kinds)
        if lid == "take":
            return "ring" in n.pack
        if lid == "satchel":
            return ui.get("satchel")
        if lid == "loom":
            return n.on is n.web.loom or n.acts.act != "threshold"
        if lid == "guests":
            return "orrin" in n.cocoons.burst
        if lid == "notebook":
            return ui.get("notebook")
        if lid == "strand":
            return isinstance(n.on, Bridge)
        if lid == "warmth":
            return any(e[:3] == ("spell", "warmth", "cast") for e in kinds)
        if lid == "save":
            return ui.get("saved")
        if lid == "supper":
            return "supper" in n.acts.outcomes or n.where() == "larder"
        if lid == "antidote":
            return not n.venom.active
        if lid == "crown":
            return n.on is n.web.crown or "crown" in n.acts.outcomes
        return True


def travel_task(name, n, nav):
    """Where the letter leads him for a lesson: a director task."""
    if name == "light_spot":
        return {"do": "go", "at": ("tunnel", 6.6, 0.0), "look": mark_at(n.tree, "tunnel", 6.5)}
    if name == "ring_spot":
        return {"do": "go", "at": ("tunnel", 4.4, 0.0), "look": n.finds.spots["ring"]}
    if name == "loom_edge":
        x, _y, z = nav.ledge_pt(nav.s_loom - 0.5, 0.5)
        return {"do": "go", "at": ("ledge", nav.s_loom - 0.5, x, z), "look": (0.0, 4.2, 0.0)}
    if name == "orrin_spot":
        spot = n.cocoons.spots[0]
        x, y, z = spot["pos"]
        r = math.hypot(x, z)
        k = 1.0 - 1.4 / r
        return {"do": "go", "at": ("floor", x * k, z * k), "look": spot["pos"]}
    if name == "strand_end":
        b = n.web.bridges[0]
        s = nav.s_at(b.a[0], b.a[2], b.a[1])
        x, _y, z = nav.ledge_pt(s, 0.75)
        return {"do": "go", "at": ("ledge", s, x, z), "look": b.point(0.3)}
    if name == "larder_door":
        s = nav.landing_s("larder", 0.05)
        x, _y, z = nav.ledge_pt(s - 0.35, 0.5)
        return {"do": "go", "at": ("ledge", s - 0.35, x, z), "look": nav.ledge_pt(nav.landing_s("larder"), -0.3)}
    if name == "antidote_spot":
        x, y, z = n.finds.spots["antidote"]
        r = math.hypot(x, z)
        k = 1.0 - 1.0 / r
        s = nav.s_at(x * k, z * k, y)
        return {"do": "go", "at": ("ledge", s, x * k, z * k), "look": (x, y, z)}
    if name == "crown_edge":
        s = nav.s_crown
        x, _y, z = nav.ledge_pt(s, 0.6)
        return {"do": "go", "at": ("ledge", s, x, z), "look": (0.0, n.tree.landing_h["crown"] - 0.3, 0.0)}
    return None
