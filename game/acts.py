"""The night's shape (phase 4a): six acts on a clock that never stops. He finds his own way in; then she calls him on.

    threshold   in through the roots, up into the hollow, to her loom                (she calls him up to her loom)
    audience    the first conversation, on her loom                                   (a scene)
    gallery     her guests, wrapped; what they were; what's to be found              (sent up to look at them)
    supper      in her larder - her hunger at its height; guest, or meal?           (she calls him down; a scene)
    crown       the deepest conversation, on the moonlit web at the top of the oak    (she calls him up; a scene)
    dawn        the light comes; the night ends - how, decided by all of it

    acts = Acts()
    acts.step(dt, night)     -> events: ("act", name), ("call", act) - her calling him on, now and then
    acts.act                 which act it is
    acts.request             what she's asked of him, in his words ("Go up to her loom.") - for the pause, and his notes
    acts.scene_for(night)    -> the scene that should begin where he is now, or None
    acts.scene_over(name, how, night)   a scene ended: on to the next act
    acts.decide(night)       -> the ending dawn brings: "Dawn", "Cast out", "Bound", "The gift"
Plain Python: the tests walk a night through it."""
from . import sky as S

ORDER = ("threshold", "audience", "gallery", "supper", "crown", "dawn")
REQUEST = {"threshold": "She waits on her loom, in the great hollow. Go to her.",
           "audience": "Answer her.",
           "gallery": "She sent me up to the gallery, to look at her guests.",
           "supper": "She has called me down to her larder. It is time to eat, she says.",
           "crown": "She has gone up to the crown of the oak, to the web under the moon. She wants me there.",
           "dawn": "Dawn is coming."}
NOTES = {"gallery": "req_gallery", "supper": "req_larder", "crown": "req_crown"}
# when she calls, if he hasn't come of his own accord: (minutes of the night past dusk, then again every so often)
CALL_AT = {"threshold": 75, "supper": 300, "crown": 480}           # (8:15 pm; half past midnight; 3 am)
CALL_EVERY = 3.0 * 60.0                                            # (real seconds between her calls, once she's calling)


def night_minutes(clock):
    """Minutes since the dusk the night began."""
    return clock - S.DUSK


class Acts:
    def __init__(self):
        self.act = "threshold"
        self.request = REQUEST["threshold"]
        self.calling = False
        self.next_call = 0.0
        self.t = 0.0
        self.found = 0                       # (how many of her guests he's looked at)
        self.outcomes = {}                   # (each scene: how it ended)

    def _go(self, act, out):
        self.act = act
        self.request = REQUEST[act]
        self.calling = False
        out.append(("act", act))

    def step(self, dt, night):
        self.t += dt
        out = []
        m = night_minutes(night.sky.clock)
        if self.act != "dawn" and night.sky.phase()[0] == "dawn" and m > 600:
            self._go("dawn", out)                          # (the light comes, whatever else)
            return out
        if self.act == "gallery" and (m >= CALL_AT["supper"] or (self.found >= 3 and m >= 200)):
            self._go("supper", out)
        want = CALL_AT.get(self.act)
        if want is not None and m >= want and not self.calling:
            self.calling, self.next_call = True, self.t
        if self.calling and self.t >= self.next_call:
            self.next_call = self.t + CALL_EVERY
            out.append(("call", self.act))
        return out

    def scene_for(self, night):
        """The scene that begins where he stands, at this point in the night."""
        place = night.where()
        if self.act == "threshold" and night.on is night.web.loom:
            return "audience"
        if self.act in ("gallery", "supper") and place == "larder" and "supper" not in self.outcomes:
            return "supper"
        if self.act == "crown" and night.on is night.web.crown:
            return "crown"
        return None

    def scene_over(self, name, how, night):
        self.outcomes[name] = how
        out = []
        if name == "audience":
            self._go("gallery", out)
        elif name == "supper":
            if how == "meal":                                # (she ate - or began to)
                out.append(("meal",))
            self._go("crown", out)
        elif name == "crown":
            self.request = "Wait with her for the light."
        return out

    def decide(self, night):
        """At dawn: how it ends. Bitten and little thought of - cast out; held dear and staying - bound; held dear, still
        fascinating, never caught in a lie - the gift; otherwise dawn, and she lets him go."""
        m = night.moods
        talk_lies = getattr(night, "lies", 0)
        stay = night.flags.get("stay", False)
        if night.flags.get("led") and not night.flags.get("woke"):   # (led by her letter, all night: game/autoplay.py)
            return "Spellbound"
        if night.flags.get("named"):                       # (her true name, found and spoken: game/hidden.py)
            return "The hidden"
        if m.bites >= 1 and m.regard < 30:
            return "Cast out"
        if stay and m.regard >= 55:
            return "Bound"
        if m.regard >= 65 and m.fascination >= 55 and talk_lies == 0 and m.bites == 0:
            return "The gift"
        return "Dawn"
