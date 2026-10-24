"""The Expie's body: six parts that bruise, bleed, break, get infected and heal; the vitals the brainchip watches
(blood, heart, oxygen, temperature, hunger, thirst, exhaustion, mood, brain); the traits that grow with a run.

Everything is per real second (step(dt)). The brainchip's only game over is brain health at 0."""
import random

PARTS = ("head", "torso", "l_arm", "r_arm", "l_leg", "r_leg")
PART_NAMES = {"head": "Head", "torso": "Torso", "l_arm": "Left arm", "r_arm": "Right arm", "l_leg": "Left leg",
              "r_leg": "Right leg"}


class Part:
    __slots__ = ("bleed", "fracture", "infection", "shard", "bandage", "splint", "bruise", "disfigured", "healing")

    def __init__(self):
        self.bleed = 0.0           # 0..1 how hard it bleeds
        self.fracture = False
        self.infection = 0.0       # 0..1
        self.shard = False         # glass in the wound: bleeds until it's out
        self.bandage = 0.0         # 0..1 how much bandage is left on it
        self.splint = False
        self.bruise = 0.0          # pain, fades
        self.disfigured = 0        # the head: 0..3
        self.healing = 0.0         # a fracture mends while splinted

    def hurt(self):
        return self.bleed > 0 or self.fracture or self.infection > 0.15 or self.shard or self.bruise > 0.3

    def status(self):
        words = []
        if self.shard:
            words.append("glass in it")
        if self.bleed > 0.6:
            words.append("bleeding badly")
        elif self.bleed > 0:
            words.append("bleeding")
        if self.fracture:
            words.append("broken" + (" (splinted)" if self.splint else ""))
        if self.infection > 0.6:
            words.append("badly infected")
        elif self.infection > 0.15:
            words.append("infected")
        if self.bandage > 0:
            words.append("bandaged")
        if self.bruise > 0.3 and not words:
            words.append("bruised")
        return ", ".join(words) if words else "fine"


class Body:
    def __init__(self, preset):
        self.preset = preset
        self.parts = {p: Part() for p in PARTS}
        self.blood = 100.0
        self.heart = 70.0
        self.o2 = 98.0
        self.temp = 37.0
        self.hunger = 10.0          # 0 fed .. 100 starving
        self.thirst = 10.0
        self.exhaustion = 0.0       # 0 fresh .. 100 collapsing
        self.mood = 75.0            # 100 content .. 0 despair
        self.brain = 100.0
        self.immunity = 60.0
        self.arrest = False         # cardiac arrest: the AED or death
        self.conscious = True
        self.wet = 0.0              # seconds of water on the fur left
        self.pain = 0.0
        self.painkiller = 0.0       # seconds left
        self.str, self.res, self.int = 1.0, 1.0, 1.0
        self.alive = True
        self.cause = ""
        self.events = []            # ("event", detail) for sounds and speech
        self.rng = random.Random()
        self.t = 0.0

    # ---- what happens to it -----------------------------------------------------------------------------------
    def fall(self, tiles):
        """Landed after falling `tiles` tiles."""
        danger = self.preset["danger"]
        safe = 4 + self.str * 0.6
        if tiles <= safe:
            return None
        over = (tiles - safe) * danger
        self.events.append(("land", tiles))
        if over < 1.5:
            part = self.rng.choice(("l_leg", "r_leg"))
            self.parts[part].bruise = min(1.0, self.parts[part].bruise + 0.5)
            self.pain += 10
            self.events.append(("hurt", f"That hurt. The {PART_NAMES[part].lower()} is bruised."))
            return "bruise"
        if over < 4:
            part = self.rng.choice(("l_leg", "r_leg", "l_leg", "r_leg", "l_arm", "r_arm"))
            self._fracture(part)
            return "fracture"
        if over < 7:
            leg = self.rng.choice(("l_leg", "r_leg"))
            self._fracture(leg)
            other = self.rng.choice(("l_arm", "r_arm", "torso"))
            self.parts[other].bleed = min(1.0, self.parts[other].bleed + 0.5)
            self.pain += 25
            self.events.append(("bleed", f"The {PART_NAMES[other].lower()} is torn open."))
            return "bad"
        self.parts["head"].bleed = 1.0
        self.parts["head"].disfigured = min(3, self.parts["head"].disfigured + 2)
        self.brain -= 40 * danger
        self.pain += 40
        self.events.append(("bleed", "Head first. Everything goes white for a moment."))
        self.conscious = False
        return "head"

    def _fracture(self, part):
        p = self.parts[part]
        if not p.fracture:
            p.fracture = True
            p.splint = False
            p.healing = 0.0
            self.pain += 20
            self.events.append(("crack", f"Something snapped in the {PART_NAMES[part].lower()}."))
        else:
            p.bleed = min(1.0, p.bleed + 0.4)
            self.pain += 15
            self.events.append(("bleed", f"The broken {PART_NAMES[part].lower()} tears."))

    def glass(self):
        part = self.rng.choice(("l_leg", "r_leg", "l_leg", "r_leg"))
        p = self.parts[part]
        if not p.shard:
            p.shard = True
            p.bleed = max(p.bleed, 0.35)
            self.pain += 12
            self.events.append(("cut", f"Glass. It's in the {PART_NAMES[part].lower()}."))
            return True
        return False

    def soak(self, cold):
        self.wet = 25.0
        self.temp -= cold * 0.9
        for p in self.parts.values():
            if p.bandage > 0:
                p.bandage = max(0.0, p.bandage - 0.3)
            if p.bleed > 0 and p.bandage <= 0:
                p.infection = min(1.0, p.infection + 0.08)

    # ---- treatment ----------------------------------------------------------------------------------------------
    def treat(self, part, item):
        """Use an item on a body part. Returns a message, or None if it does nothing there."""
        p = self.parts[part]
        name = PART_NAMES[part].lower()
        if item == "gauze":
            if p.bleed <= 0 and p.bandage > 0:
                return None
            p.bandage = 1.0
            p.bleed *= 0.1 if not p.shard else 0.6
            if p.bleed < 0.08:
                p.bleed = 0.0
            self.events.append(("bandage", ""))
            return f"Bandaged the {name}." + (" The glass is still in there." if p.shard else "")
        if item == "medkit":
            if not p.hurt():
                return None
            p.bleed, p.infection, p.shard, p.bruise = 0.0, 0.0, False, 0.0
            p.bandage = 1.0
            if p.fracture:
                p.splint = True
            if part == "head" and p.disfigured:
                p.disfigured = -p.disfigured          # healed scars
            self.events.append(("bandage", ""))
            self.res += 0.15
            return f"Cleaned, closed and dressed the {name}."
        if item == "splint":
            if not p.fracture or p.splint:
                return None
            p.splint = True
            self.events.append(("bandage", ""))
            self.int += 0.05
            return f"Splinted the {name}. Keep the weight off it."
        if item in ("acidfruit", "disinfectant"):
            if p.infection <= 0.05 and p.bleed <= 0:
                return None
            p.infection = max(0.0, p.infection - (0.5 if item == "acidfruit" else 0.9))
            self.pain += 8 if item == "acidfruit" else 2
            self.events.append(("yelp", "")) if item == "acidfruit" else None
            self.immunity = min(100.0, self.immunity + 5)
            return f"Cleaned the {name}." + (" It stings." if item == "acidfruit" else "")
        if item in ("tweezers", "knife"):
            if not p.shard:
                return None
            p.shard = False
            p.bleed = min(1.0, p.bleed + (0.2 if item == "tweezers" else 0.45))
            self.pain += 10 if item == "tweezers" else 20
            self.events.append(("cut", ""))
            return f"Got the glass out of the {name}." + (" Rough work, with a knife." if item == "knife" else "")
        return None

    def consume(self, item):
        """Eat, drink or take something. Returns a message or None."""
        if item in ("bread", "banana", "cheese", "pancakes", "meat", "tin", "candy", "sweet"):
            gain = {"bread": 35, "banana": 20, "cheese": 25, "pancakes": 45, "meat": 50, "tin": 40, "candy": 10, "sweet": 10}[item]
            self.hunger = max(0.0, self.hunger - gain)
            self.mood = min(100.0, self.mood + (8 if item in ("candy", "sweet", "pancakes") else 3))
            if item == "meat" and self.rng.random() < 0.25 * self.preset["danger"]:
                self.parts["torso"].infection = min(1.0, self.parts["torso"].infection + 0.25)
                self.events.append(("eat", "That meat was off."))
                return "Ate the meat. It tasted wrong."
            self.events.append(("eat", ""))
            return f"Ate the {item}."
        if item in ("water", "canteen", "bottle", "jar"):
            self.thirst = max(0.0, self.thirst - (40 if item != "jar" else 25))
            self.events.append(("drink", ""))
            return "Drank. Better."
        if item == "pills":
            self.painkiller = 120.0
            self.pain = max(0.0, self.pain - 30)
            self.mood = min(100.0, self.mood + 6)
            self.events.append(("drink", ""))
            return "Took the painkillers."
        if item == "syringe":
            self.immunity = min(100.0, self.immunity + 40)
            for p in self.parts.values():
                p.infection *= 0.3
            self.events.append(("drink", ""))
            return "Antibiotics. The fever should break."
        if item == "vial":
            self.mood = min(100.0, self.mood + 25)
            self.exhaustion = max(0.0, self.exhaustion - 30)
            self.brain = max(0.0, self.brain - 3)
            self.events.append(("drink", ""))
            return "Whatever that was, the world feels lighter. Your head doesn't."
        if item == "blanket":
            self.temp = min(37.5, self.temp + 2.5)
            self.wet = 0.0
            self.mood = min(100.0, self.mood + 4)
            return "Wrapped up and warmed through."
        return None

    def defibrillate(self, success):
        if not self.arrest:
            return "The heart's beating. Don't."
        self.events.append(("shock", ""))
        if success:
            self.arrest = False
            self.heart = 110.0
            self.brain = max(1.0, self.brain)
            self.res += 0.3
            return "A jolt - and a pulse."
        self.brain -= 6
        return "Nothing. Again."

    def rest(self, dt):
        self.exhaustion = max(0.0, self.exhaustion - 6 * dt)
        self.mood = min(100.0, self.mood + 0.3 * dt)
        if self.temp < 36.5 and self.wet <= 0:
            self.temp += 0.05 * dt

    # ---- time --------------------------------------------------------------------------------------------------
    def step(self, dt, moving=False, dark=False, in_water=False, light=True):
        if not self.alive:
            return
        self.t += dt
        d = self.preset["danger"]
        rng = self.rng
        # the parts
        bleeding = 0.0
        infection = 0.0
        for name, p in self.parts.items():
            if p.bleed > 0:
                rate = p.bleed * (0.25 if p.bandage > 0 else 1.0)
                bleeding += rate
                if p.bandage <= 0 and not p.shard:
                    p.bleed = max(0.0, p.bleed - 0.004 * dt)      # a clean wound clots, slowly
                if p.bandage > 0:
                    p.bandage = max(0.0, p.bandage - 0.004 * dt * (2 if p.shard else 1))
                    if p.bandage <= 0:
                        self.events.append(("soaked", f"The bandage on the {PART_NAMES[name].lower()} is soaked through."))
                if rng.random() < 0.0015 * d * dt * 60 and p.bandage <= 0:
                    p.infection = min(1.0, p.infection + 0.1)
            if p.infection > 0:
                grow = 0.0025 * d * (1.6 - self.immunity / 100) * dt
                if p.bandage > 0:
                    grow *= 0.6
                p.infection = min(1.0, p.infection + grow)
                infection += p.infection
                if p.infection >= 1.0 and rng.random() < 0.002 * dt * 60:
                    p.disfigured = min(3, max(p.disfigured, 1)) if name == "head" else p.disfigured
            if p.fracture and p.splint:
                p.healing += dt / (240.0 / max(0.5, self.res))
                if p.healing >= 1.0:
                    p.fracture = p.splint = False
                    self.events.append(("healed", f"The {PART_NAMES[name].lower()} can take weight again."))
            if p.fracture and moving and not p.splint and name.endswith("leg"):
                self.pain += 2 * dt
                if rng.random() < 0.002 * dt * 60:
                    p.bleed = min(1.0, p.bleed + 0.15)
            p.bruise = max(0.0, p.bruise - 0.01 * dt)
        self.blood = max(0.0, min(100.0, self.blood - bleeding * 0.9 * dt + (0.02 if self.hunger < 60 and self.thirst < 60 else 0.0) * dt))
        # vitals
        self.hunger = min(100.0, self.hunger + (0.045 + (0.03 if moving else 0)) * dt)
        self.thirst = min(100.0, self.thirst + (0.07 + (0.05 if moving else 0) + (0.05 if self.temp > 38 else 0)) * dt)
        self.exhaustion = min(100.0, self.exhaustion + ((0.35 if moving else 0.04) + (0.2 if self.blood < 50 else 0)) * dt)
        fever = infection * 1.6
        if in_water:
            self.wet = 25.0
        self.wet = max(0.0, self.wet - dt)
        if self.wet > 0:
            self.temp -= 0.02 * d * dt
        elif self.temp < 37.0:
            self.temp += (0.012 + (0.02 if moving else 0)) * dt
        if fever > 0:
            self.temp = min(41.0, self.temp + 0.01 * fever * dt)
        elif self.temp > 37.0:
            self.temp -= 0.01 * dt
        want_heart = 70 + (100 - self.blood) * 1.2 + (40 if moving else 0) + fever * 10 + self.pain * 0.3
        if self.temp < 34:
            want_heart -= (34 - self.temp) * 8
        self.heart += (want_heart - self.heart) * min(1.0, 0.5 * dt)
        want_o2 = 98 - max(0, 50 - self.blood) * 0.8 - (8 if in_water else 0)
        self.o2 += (want_o2 - self.o2) * min(1.0, 0.3 * dt)
        self.pain = max(0.0, self.pain - (1.5 if self.painkiller > 0 else 0.4) * dt)
        self.painkiller = max(0.0, self.painkiller - dt)
        self.immunity = max(5.0, min(100.0, self.immunity + ((0.02 if self.hunger < 50 else -0.03) - 0.02 * fever) * dt))
        # the brain
        drain = 0.0
        if self.blood < 25:
            drain += (25 - self.blood) * 0.04
        if self.o2 < 85:
            drain += (85 - self.o2) * 0.05
        if self.temp < 32:
            drain += (32 - self.temp) * 0.1
        if self.temp > 40:
            drain += (self.temp - 40) * 0.3
        if self.hunger >= 100 or self.thirst >= 100:
            drain += 0.15
        if self.arrest:
            drain += 2.5
        if self.exhaustion >= 100:
            drain += 0.05
        self.brain = max(0.0, min(100.0, self.brain - drain * d * dt + (0.01 * dt if drain == 0 and self.mood > 50 else 0)))
        # the heart stopping
        if not self.arrest and (self.blood < 15 or (self.temp < 30) or (self.heart > 185 and rng.random() < 0.01 * dt)):
            if rng.random() < 0.06 * dt * d or self.blood < 8:
                self.arrest = True
                self.conscious = False
                self.events.append(("arrest", "The heart stops."))
        # consciousness
        if not self.conscious and not self.arrest and self.blood > 20 and self.o2 > 80 and rng.random() < 0.05 * dt:
            self.conscious = True
            self.events.append(("wake", "...coming round."))
        # mood
        mood_drift = 0.0
        if dark and not light:
            mood_drift -= 0.3
        mood_drift -= self.pain * 0.004 + bleeding * 0.3 + infection * 0.15
        mood_drift -= 0.08 if self.hunger > 70 else 0
        mood_drift -= 0.08 if self.thirst > 70 else 0
        mood_drift -= 0.06 if self.exhaustion > 80 else 0
        mood_drift -= 0.1 if self.temp < 34 else 0
        if mood_drift == 0.0 and self.hunger < 50 and self.thirst < 50 and self.pain < 5:
            mood_drift = 0.05
        self.mood = max(0.0, min(100.0, self.mood + mood_drift * self.preset.get("mood", 1.0) * dt))
        if self.brain <= 0:
            self.alive = False
            self.cause = self._cause()
            self.events.append(("die", self.cause))

    def _cause(self):
        if self.arrest:
            return "cardiac arrest" + (" after blood loss" if self.blood < 25 else "")
        if self.blood < 25:
            return "blood loss"
        if self.o2 < 85:
            return "asphyxiation"
        if self.temp < 32:
            return "hypothermia"
        if self.temp > 40:
            return "sepsis"
        if self.thirst >= 100:
            return "dehydration"
        if self.hunger >= 100:
            return "starvation"
        return "head trauma"

    # ---- what the chip shows ----------------------------------------------------------------------------------
    def moodles(self):
        """Status icons to show: (key, severity 0..3)."""
        out = []
        bleed = sum(p.bleed * (0.25 if p.bandage else 1) for p in self.parts.values())
        if bleed > 0.5:
            out.append(("bleeding2", 3))
        elif bleed > 0:
            out.append(("bleeding", 2))
        if any(p.shard for p in self.parts.values()):
            out.append(("shard", 2))
        if any(p.fracture for p in self.parts.values()):
            out.append(("fracture", 2 if any(p.fracture and not p.splint for p in self.parts.values()) else 1))
        inf = max(p.infection for p in self.parts.values())
        if inf > 0.6:
            out.append(("fever", 3))
        elif inf > 0.15:
            out.append(("infection", 2))
        if self.arrest:
            out.append(("arrest", 3))
        if self.blood < 40:
            out.append(("lowblood", 3 if self.blood < 20 else 2))
        if self.o2 < 90:
            out.append(("oxygen", 2))
        if self.temp < 35:
            out.append(("cold", 3 if self.temp < 33 else 2))
        if self.temp > 38.5:
            out.append(("hot", 2))
        if self.wet > 0:
            out.append(("wet", 1))
        if self.hunger > 60:
            out.append(("hungry", 3 if self.hunger > 90 else 2))
        if self.thirst > 60:
            out.append(("thirsty", 3 if self.thirst > 90 else 2))
        if self.exhaustion > 60:
            out.append(("tired", 3 if self.exhaustion > 90 else 1))
        if self.mood < 25:
            out.append(("depressed", 3 if self.mood < 10 else 2))
        elif self.mood < 45:
            out.append(("gloomy", 1))
        if self.pain > 30:
            out.append(("pain", 2))
        if self.brain < 50:
            out.append(("brain", 3 if self.brain < 25 else 2))
        if self.painkiller > 0:
            out.append(("pills", 0))
        if not self.conscious:
            out.append(("unconscious", 3))
        return out

    def speed(self):
        """How fast the Expie can move, 0..1."""
        legs = sum(1 for n in ("l_leg", "r_leg") if self.parts[n].fracture and not self.parts[n].splint)
        s = 1.0 - 0.35 * legs
        s -= 0.25 * sum(1 for n in ("l_leg", "r_leg") if self.parts[n].fracture and self.parts[n].splint)
        if self.exhaustion > 80:
            s *= 0.6
        if self.temp < 34:
            s *= 0.7
        if self.wet > 0:
            s *= 0.85
        if self.blood < 40:
            s *= 0.75
        return max(0.15, s)

    def refuses(self):
        """Low mood: will the Expie ignore this order?"""
        if self.mood >= 25:
            return False
        return self.rng.random() < (0.5 if self.mood < 10 else 0.15)
