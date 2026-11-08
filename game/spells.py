"""Claude's four spells (phase 4c): conversation moves as much as tools.

    light       a bright orb, up from his hand, hanging a while: the den lit; old marks in the wood that only it shows;
                her small ones scattering. It hurts her eyes: near her, her doubt and her patience both suffer.
    warmth      a small flame in his palm: a comfort (his sanity, his stupor eased). She likes it at a distance and
                distrusts it close. On her silk, the silk smoulders - one slip, and the night may end (the blaze: 4f).
    illusion    he seems grander - or, in the den, her small ones lose him a while. In her scenes she may be dazzled,
                or see straight through it, and her suspicion jumps.
    memory      a true memory of his own, shown to her: his most intimate gift; she keeps what she sees. Each once a
                night. Alone, remembering steadies him.

    spells = Spells(rng)
    spells.cast(name, night)          in the den: -> events ("spell", name, ...), ("smoulder",), ("mark", id) ...
    spells.ready(name), spells.rest   when it can be cast again
    spells.lit                        [(kind, position, when, how long)] - what's shining, for the renderer
    in_scene(name, night, memory=None) -> (tier, her answer in the script, how it's said to a model)
Plain Python: the tests cast them."""
import math

REST = {"light": 25.0, "warmth": 12.0, "illusion": 30.0, "memory": 6.0}
LIGHT_FOR, WARMTH_FOR = 7.0, 9.0
MEMORIES = {
    "hands": ("My mother's hands, floured to the wrist, the winter before she died.",
              "He shows you a memory: his mother's hands, floured to the wrist, the winter before she died."),
    "candle": ("The first spell I ever cast: a candle that would not go out for a week.",
               "He shows you a memory: the first spell he ever cast - a candle, as a boy, that would not go out for a "
               "week, and how frightened and proud he was."),
    "thrown": ("The night Thornwick's academy threw me out - and I did not cry until the road.",
               "He shows you a memory: the night they threw him out of the academy at Thornwick - the masters' faces, "
               "the cold road home, and how he did not cry until he was alone on it."),
}
# old marks in the wood that only Light shows: (id, where - angle, height - and how near he must be)
MARKS = (("mark_roots", "tunnel", 6.5, 0.8), ("mark_tally", "gallery", 0.0, 1.6), ("mark_crown", "crown", 0.0, 1.0))


class Spells:
    def __init__(self, rng):
        self.rng = rng
        self.rest = {k: 0.0 for k in REST}
        self.t = 0.0
        self.lit = []
        self.illusion_until = -1.0
        self.shown = set()                  # (memories shown her tonight)
        self.marks_seen = set()

    def ready(self, name):
        return self.t >= self.rest[name]

    def unshown(self):
        """The memories he hasn't yet given her tonight."""
        return [k for k in MEMORIES if k not in self.shown]

    def shining(self, kind):
        """How bright a spell of that kind is now, 0..1 (rising quickly, fading at the end)."""
        best = 0.0
        for k, _p, when, length in self.lit:
            if k == kind:
                age = self.t - when
                best = max(best, min(1.0, age / 0.35, (length - age) / 1.5))
        return max(0.0, best)

    @property
    def illusion(self):
        return self.t < self.illusion_until

    def step(self, dt):
        self.t += dt
        self.lit = [x for x in self.lit if self.t - x[2] < x[3]]

    def cast(self, name, night):
        """In the den."""
        if not self.ready(name):
            return [("spell", name, "resting")]
        self.rest[name] = self.t + REST[name]
        venom = getattr(night, "venom", None)
        if venom is not None and venom.misses():                    # (his hands shaking: it comes apart)
            return [("spell", name, "missed")]
        ex, ey, ez = night.eye
        fx, fz = math.sin(night.yaw), -math.cos(night.yaw)            # (before him, and a little to his right)
        rx, rz = math.cos(night.yaw), math.sin(night.yaw)
        her_d = math.dist(night.her.at(), night.eye)
        out = [("spell", name, "cast")]
        if name == "light":
            self.lit.append(("light", (ex + fx * 0.9, ey + 0.45, ez + fz * 0.9), self.t, LIGHT_FOR))
            night.body.sanity = min(100.0, night.body.sanity + 5.0)
            for sp in night.brood.spiders:                         # (her small ones, scattering from it)
                if math.dist(night.brood.pos(sp), night.eye) < 9.0:
                    sp["state"], sp["until"], sp["speed"] = "flee", 2.5, 2.6
                    sp["head"] = night.brood._away(sp, night.brood.pos(sp), night.eye)
            if her_d < 9.0:                                        # (it hurts her eyes)
                night.moods.heard("light")
                night.her.state, night.her.until = "withdraw", night.her.t + 6.0
                out.append(("her", "hurt"))
            out += self._marks(night)
        elif name == "warmth":
            self.lit.append(("warmth", (ex + fx * 0.42 + rx * 0.12, ey - 0.2, ez + fz * 0.42 + rz * 0.12), self.t,
                             WARMTH_FOR))
            night.body.sanity = min(100.0, night.body.sanity + 4.0)
            night.body.stupor = max(0.0, night.body.stupor - 5.0)
            if night.on is not None:                               # (on her silk: it smoulders under his hand)
                night.moods.suspicion = min(100.0, night.moods.suspicion + 15.0)
                night.moods.patience = max(0.0, night.moods.patience - 20.0)
                night.tremor += 3.0
                night.flags["smouldered"] = night.flags.get("smouldered", 0) + 1
                self.lit.append(("ember", (ex + fx * 0.4, night.y + 0.03, ez + fz * 0.4), self.t, 5.0))
                out.append(("smoulder", getattr(night.on, "name", "silk")))
            elif her_d > 6.0:
                night.moods.fascination = min(100.0, night.moods.fascination + 3.0)
            elif her_d < 4.0:
                night.moods.suspicion = min(100.0, night.moods.suspicion + 4.0)
                night.moods.patience = max(0.0, night.moods.patience - 4.0)
        elif name == "illusion":
            self.illusion_until = self.t + 15.0                    # (her small ones lose him a while)
            self.lit.append(("illusion", (ex, ey, ez), self.t, 2.5))
        elif name == "memory":
            night.body.sanity = min(100.0, night.body.sanity + 8.0)
            self.lit.append(("memory", (ex, ey, ez), self.t, 2.0))
        return out

    def _marks(self, night):
        """Old marks in the wood, that only this light shows him."""
        out = []
        for mid, where, along, reach in MARKS:
            p = mark_at(night.tree, where, along)
            if math.dist(p, night.eye) < 4.5 and mid not in self.marks_seen:
                self.marks_seen.add(mid)
                out.append(("mark", mid))
        return out

    def in_scene(self, name, night, memory=None):
        """Cast before her, in a scene: -> (tier, her answer in the script, how it's said to a model)."""
        m = night.moods
        if name != "memory":
            self.rest[name] = self.t + REST[name]
        venom = getattr(night, "venom", None)
        if venom is not None and venom.misses():
            return "plain", "Your hands are shaking. Whatever that was meant to be, it fell apart in them.", \
                "He tries a spell, but his hands shake with your venom and it comes to nothing"
        if name == "light":
            m.heard("light")
            m.heard("light")
            return "insult", "Put it out. Put it out - you are in my house, and that light is a knife.", \
                "He throws a hard white light right into your eyes. It hurts"
        if name == "warmth":
            if night.on is not None:
                m.suspicion = min(100.0, m.suspicion + 15.0)
                m.patience = max(0.0, m.patience - 20.0)
                night.flags["smouldered"] = night.flags.get("smouldered", 0) + 1
                return "insult", "Fire. On my silk. Close your hand. Close it now, or I will close it for you.", \
                    "He opens his hand and there is fire in it - on your silk. You are terrified, and furious"
            m.fascination = min(100.0, m.fascination + 2.0)
            return "plain", "Warmth. From over there, it is almost kind. Do not bring it closer.", \
                "He holds a small flame in his palm, a little way off. You like it, from there - and do not trust it"
        if name == "illusion":
            see = 0.25 + m.suspicion / 150.0
            if self.rng.random() < see:
                m.suspicion = min(100.0, m.suspicion + 15.0)
                m.regard = max(0.0, m.regard - 4.0)
                return "insult", "Take that off. I can see you under it, little wizard, and you look smaller for it.", \
                    "He wraps himself in an illusion to seem grander. You see straight through it, and despise it"
            m.heard("magic")
            return "delight", "Oh. That is pretty. Is any of it true?", \
                "He wraps himself in an illusion to seem grander - a cloak of stars. It dazzles you, a little"
        if name == "memory" and memory in MEMORIES and memory not in self.shown:
            self.shown.add(memory)
            for k in ("memory", "honest", "deep"):
                m.heard(k)
            m.regard = min(100.0, m.regard + 6.0)
            line, said = MEMORIES[memory]
            answers = {"hands": "Floured to the wrist. You loved her. I will keep her hands, little wizard; they are "
                                "safe with me.",
                       "candle": "A week. Your first light, and it would not die. I know a little of that.",
                       "thrown": "They threw you out, and you did not cry until the road. I will remember the road."}
            return "delight", answers[memory], said + ". It moves you"
        return "plain", "Hm.", "He does something you do not follow"


def mark_side(tree, where, along, p):
    """Along the wood where the mark is cut (for drawing it): the tunnel's run, or round the hollow's wall."""
    if where == "tunnel":
        a, b = tree.tunnel_point(along - 0.1, 0.0), tree.tunnel_point(along + 0.1, 0.0)
        d = (b[0] - a[0], b[1] - a[1])
        k = math.hypot(*d) or 1.0
        return (d[0] / k, 0.0, d[1] / k)
    a = math.atan2(p[2], p[0])
    return (-math.sin(a), 0.0, math.cos(a))


def mark_at(tree, where, along):
    """Where an old mark is cut: low in the root tunnel; on the gallery's back wall; under the crown."""
    from . import tree as T
    if where == "tunnel":
        x, z = tree.tunnel_point(along, -T.TUNNEL_HALF + 0.02)
        return (x, tree.tunnel_floor(along) + 0.5, z)
    start, run = next((s, r) for n, s, r in T.LANDINGS if n == where)
    h = tree.landing_h[where]
    th = tree.theta_of(start + run / 2) + along
    r = tree.wall_r(th, h + 1.3) - 0.06
    return (math.cos(th) * r, h + (1.3 if where == "gallery" else 2.2), math.sin(th) * r)
