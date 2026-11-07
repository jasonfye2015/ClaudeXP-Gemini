"""The sky over Thornwick, as Claude and Magic keeps it (its 24-clock, 24b-calendar, 24f-events and 69zzq-below),
carried over: the game's own clock, the season (the real date's), the day's length by the season, the moon on a
twenty-nine day month, and the weather as live events - clear, cloud, rain, storm, mist, wind, snow, heat, an
aurora, a tornado - each two to six hours, coming in and going out over twenty minutes, rolled by the season, the
hour and the day's leaning. And what the sky does reaches down the shaft: a heavy storm floods the low halls of the
first floors, draining over a day; rain drips, a gale draws a draft, lightning comes down through the grates.

The clock: a minute of the game is a second of play (a day is twenty-four minutes); the stairs take an hour.

    Sky(seed) / Sky.from_json(d)          the run's sky (saved with the game)
    sky.tick(minutes)                      time goes by: the weather and the flood follow
    sky.hour, sky.day, sky.season, sky.night, sky.moon_phase, sky.dial()
    sky.now()  -> {kind, strength 0..1, word, wind: (speed, (dx, dz))}
    sky.flood  -> 0..1                     the floodwater in the first floors' sunken rooms
    sky.effects(outdoors, depth) -> {...}  what it does to play: sight, speed, the elements, lightning, the forest"""
import datetime
import math
import random

CLOCK = {"start": 6 * 60, "day": 24 * 60, "stair": 60, "moon": 29}
DAYLIGHT = {"spring": (5, 21), "summer": (4, 22), "autumn": (6, 20), "winter": (7, 18)}
MOON_WORDS = ["a new moon", "a waxing crescent", "the first quarter", "a waxing gibbous", "a full moon",
              "a waning gibbous", "the last quarter", "a waning crescent"]
WEATHER_ODDS = {"spring": ["clear", "rain", "rain", "mist", "wind"], "summer": ["clear", "clear", "clear", "wind", "rain"],
                "autumn": ["clear", "mist", "mist", "rain", "wind"], "winter": ["clear", "snow", "snow", "mist", "wind"]}
WX = {
    "kinds": ["clear", "cloud", "rain", "storm", "mist", "wind", "snow", "heat", "aurora", "tornado"],
    "tornado": (60, 120), "clear": (60, 360), "event": (120, 360), "ramp": 20, "night_clear": 0.8, "after_rain": 90,
    "odds": {"spring": {"cloud": 3, "rain": 4, "storm": 1, "mist": 2, "wind": 2, "snow": 0, "heat": 0, "tornado": 0.15},
             "summer": {"cloud": 2, "rain": 2, "storm": 2, "mist": 1, "wind": 2, "snow": 0, "heat": 3, "tornado": 0.3},
             "autumn": {"cloud": 3, "rain": 3, "storm": 1, "mist": 3, "wind": 3, "snow": 0, "heat": 0, "tornado": 0.4},
             "winter": {"cloud": 3, "rain": 1, "storm": 0, "mist": 2, "wind": 3, "snow": 4, "heat": 0, "tornado": 0}},
    "word": {"clear": "clear", "cloud": "clear", "rain": "rain", "storm": "rain", "mist": "mist", "wind": "wind",
             "snow": "snow", "heat": "clear", "aurora": "clear", "tornado": "wind"},
    "wind": {"clear": 0.15, "cloud": 0.25, "rain": 0.45, "storm": 0.85, "mist": 0.05, "wind": 1.0, "snow": 0.35,
             "heat": 0.1, "aurora": 0.1, "tornado": 1.0},
}
NAMES = {"clear": "Clear", "cloud": "Cloud", "rain": "Rain", "storm": "Storm", "mist": "Mist", "wind": "Wind",
         "snow": "Snow", "heat": "Heat", "aurora": "Aurora", "tornado": "Tornado"}
FLOOD = {"from": 0.75, "drain": 24 * 60, "floors": range(1, 4)}


def season_of_date(d=None):
    m = (d or datetime.date.today()).month - 1
    return "spring" if 2 <= m <= 4 else "summer" if 5 <= m <= 7 else "autumn" if 8 <= m <= 10 else "winter"


def _hash(text):
    h = 2166136261
    for ch in str(text).encode():
        h = ((h ^ ch) * 16777619) & 0xFFFFFFFF
    return h


def hour_word(h):
    return ("night" if h >= 21 or h < 1 else "the small hours" if h < 5 else "dawn" if h < 7 else "morning" if h < 11
            else "noon" if h < 13 else "afternoon" if h < 17 else "dusk" if h < 19 else "evening")


class Sky:
    def __init__(self, seed, clock=0.0, season=None):
        self.seed = seed
        self.clock = float(clock)                       # minutes since the run's first dawn (six in the morning)
        self.fixed_season = season
        self.cur = None
        self.next = None
        self.prev = None
        self.flood_level = 0.0
        self.flood_at = None
        self.rng = random.Random(_hash(f"{seed}:sky"))
        self.step()

    # ---- the clock -------------------------------------------------------------------------------------------
    @property
    def minute(self):
        return (CLOCK["start"] + self.clock) % CLOCK["day"]

    @property
    def hour(self):
        return self.minute / 60

    @property
    def day(self):
        return int((CLOCK["start"] + self.clock) // CLOCK["day"])

    @property
    def season(self):
        return self.fixed_season or season_of_date()

    @property
    def daylight(self):
        return DAYLIGHT[self.season]

    @property
    def night(self):
        dawn, dusk = self.daylight
        return self.hour >= dusk or self.hour < dawn

    @property
    def moon_phase(self):
        return round(((self.day % CLOCK["moon"]) / CLOCK["moon"]) * 8) % 8

    def time_figures(self):
        m = int(self.minute)
        return f"{m // 60}:{m % 60:02d}"

    def dial(self):
        """Angles from straight up, clockwise: -90 the eastern horizon, 90 the western; the moon opposite the sun."""
        h = self.hour
        dawn, dusk = self.daylight
        long = dusk - dawn
        up = dawn <= h < dusk
        norm = lambda a: ((a + 180) % 360 + 360) % 360 - 180   # noqa: E731
        sun = norm(-90 + 180 * (h - dawn) / long if up else 90 + 180 * ((h - dusk + 24) % 24) / (24 - long))
        sky = "night" if not up else "dawn" if h - dawn < 1 else "dusk" if dusk - h < 1 else "day"
        return {"hour": h, "sun": sun, "moon": norm(sun + 180), "night": not up, "sky": sky, "phase": self.moon_phase,
                "day": self.day, "moon_day": self.day % CLOCK["moon"] + 1}

    def sun_dir(self):
        """Where the sun's light comes from, and its strength (0 at night); the moon's when the sun is down."""
        d = self.dial()
        a = math.radians(d["sun"])
        elev = math.cos(a)                               # 1 straight up, 0 at the horizons
        if not d["night"] and elev > -0.05:
            return (math.sin(a), max(0.05, elev), 0.35), max(0.0, min(1.0, elev * 1.6))
        m = math.radians(d["moon"])
        return (math.sin(m), max(0.05, math.cos(m)), 0.35), 0.0

    # ---- the weather -------------------------------------------------------------------------------------------
    def day_word(self, day=None):
        odds = WEATHER_ODDS[self.season]
        return odds[_hash(f"{self.seed}:weather:{self.day if day is None else day}") % len(odds)]

    def _night_at(self, at):
        h = ((CLOCK["start"] + at) % CLOCK["day"]) / 60
        dawn, dusk = self.daylight
        return h >= dusk or h < dawn

    def _pick(self, at):
        odds = dict(WX["odds"][self.season])
        lean = self.day_word()
        h = ((CLOCK["start"] + at) % CLOCK["day"]) / 60
        night = self._night_at(at)
        if lean == "rain":
            odds["rain"] *= 2
            odds["storm"] = (odds["storm"] or 0.5) * 2
        elif lean in odds:
            odds[lean] *= 2
        if not 12 <= h < 17:
            odds["heat"] = 0
        if night:
            odds["heat"] = 0
            odds["storm"] *= 0.5
            odds["tornado"] = 0
        if night and self.season == "winter" and self.rng.random() < 0.3:
            return "aurora"
        total = sum(odds.values())
        r = self.rng.random() * total
        for k, w in odds.items():
            r -= w
            if r < 0:
                return k
        return "cloud"

    def _roll(self, at, after):
        night = self._night_at(at)
        if after != "clear" or (night and self.rng.random() < WX["night_clear"]):
            n = round(self.rng.uniform(*WX["clear"]) * (1.6 if night else 1))
            return {"kind": "clear", "strength": 1.0, "from": at, "until": at + n}
        kind = self._pick(at)
        n = round(self.rng.uniform(*(WX["tornado"] if kind == "tornado" else WX["event"])))
        strength = self.rng.uniform(0.5, 1) if kind == "aurora" else min(1.0, self.rng.uniform(0.45, 1.05))
        ev = {"kind": kind, "strength": strength, "from": at, "until": at + n}
        if kind == "tornado":
            a = self.rng.uniform(0, math.tau)
            ev["twister"] = (math.cos(a), math.sin(a))
        return ev

    def step(self):
        t = self.clock
        if self.cur is None:
            self.cur = {"kind": "clear", "strength": 1.0, "from": t, "until": t + round(self.rng.uniform(30, 120))}
            self.next = self._roll(self.cur["until"], "clear")
        guard = 0
        while t >= self.cur["until"] and guard < 200:
            guard += 1
            self.prev = self.cur
            self.cur = self.next if self.next and self.next["from"] == self.cur["until"] else self._roll(self.cur["until"], self.cur["kind"])
            self.next = self._roll(self.cur["until"], self.cur["kind"])

    def now(self):
        c = self.cur
        t = self.clock
        k = 0.0 if c["kind"] == "clear" else max(0.0, min(1.0, (t - c["from"]) / WX["ramp"], (c["until"] - t) / WX["ramp"])) * c["strength"]
        a = (_hash(f"{self.seed}:wind:{self.day}") % 360) * math.pi / 180
        speed = 0.12 + (WX["wind"][c["kind"]] - 0.12) * (1 if c["kind"] == "clear" else max(0.2, k))
        return {"kind": c["kind"], "strength": k, "word": WX["word"][c["kind"]], "from": c["from"], "until": c["until"],
                "wind": (speed, (math.cos(a), math.sin(a)))}

    def after_rain(self):
        p = self.prev
        if not p or p["kind"] not in ("rain", "storm") or self.cur["kind"] != "clear":
            return 0.0
        m = self.clock - p["until"]
        return 0.0 if m < 0 else max(0.0, 1 - m / WX["after_rain"])

    def rainbow(self):
        """A rainy day's sun-shower: in the second hour after dawn, and the late afternoon."""
        w = self.now()
        if w["kind"] not in ("rain",) or self.night:
            return 0.0
        dawn, dusk = self.daylight
        h = self.hour
        bell = lambda c: max(0.0, min(1.0, 1 - abs(h - c) / 0.75))   # noqa: E731
        return max(bell(dawn + 1.5), bell(min(dusk - 1.5, 16.5)))

    def snow_depth(self):
        """How deep the snow lies, 0..1: it builds over the days it falls and melts on the days it doesn't."""
        if self.season != "winter":
            return 0.0
        d = self.day
        depth = 0.0
        for n in range(max(0, d - 5), d):
            depth = min(1.0, max(0.0, depth + (0.45 if self.day_word(n) == "snow" else -0.22)))
        frac = (self.minute % CLOCK["day"]) / CLOCK["day"]
        depth = min(1.0, max(0.0, depth + (0.45 if self.now()["kind"] == "snow" else -0.22) * frac))
        return round(depth * 20) / 20

    def ground_frost(self):
        if self.season not in ("winter", "autumn") or self.now()["kind"] not in ("clear", "wind") or self.snow_depth() > 0.3:
            return 0.0
        dawn = self.daylight[0]
        h = self.hour
        k = 1.0 if self.season == "winter" else 0.7
        return k * (0.0 if h < dawn - 1 else h - (dawn - 1) if h < dawn else max(0.0, min(1.0, 1 - (h - dawn) / 2)))

    def twister(self, size):
        """A tornado's place on the town's map: in from the edge on its way, across the middle (squares a minute 0.5)."""
        c = self.cur
        if c["kind"] != "tornado":
            return None
        dx, dz = c["twister"]
        t = self.clock - c["from"]
        cx = cz = size / 2
        R = size * 0.55
        d = min(t * 0.5, size * 1.1)
        return (cx - dx * R + dx * d, cz - dz * R + dz * d, self.now()["strength"])

    # ---- time going by -----------------------------------------------------------------------------------------
    def tick(self, minutes):
        if minutes <= 0:
            return []
        self.clock += minutes
        was = self.cur["kind"]
        self.step()
        said = []
        if self.cur["kind"] != was:
            said.append(("weather", self.cur["kind"]))
        # the flood below
        w = self.now()
        if w["kind"] == "storm" and w["strength"] >= FLOOD["from"]:
            if self.flood_level < 1:
                said.append(("flood", 1))
            self.flood_level, self.flood_at = 1.0, self.clock
        elif self.flood_at is not None:
            was_f = self.flood_level
            self.flood_level = max(0.0, 1 - (self.clock - self.flood_at) / FLOOD["drain"])
            if was_f > 0 and self.flood_level == 0:
                self.flood_at = None
                said.append(("flood", 0))
        return said

    @property
    def flood(self):
        return self.flood_level

    # ---- what it does to play ------------------------------------------------------------------------------------
    def effects(self, outdoors, depth):
        """{sight (how far monsters notice him, x), speed (x), element: {element: x damage}, lightning (chance a
        second of a strike near him), flood (0..1 here), night}"""
        w = self.now()
        k, kind = w["strength"], w["kind"]
        out = {"sight": 1.0, "speed": 1.0, "element": {}, "lightning": 0.0, "flood": 0.0, "night": self.night,
               "kind": kind, "strength": k}
        if outdoors:
            if kind == "mist":
                out["sight"] = 1 - 0.55 * k                       # (the beasts and Claude find each other late)
            if kind in ("rain", "storm"):
                out["element"] = {"fire": 1 - 0.25 * k, "storm": 1 + 0.25 * k, "frost": 1 + 0.1 * k}
            if kind == "storm":
                out["lightning"] = 0.04 * k
            if kind == "snow" or self.snow_depth() >= 0.3:
                out["speed"] = 0.85
                out["element"] = {"frost": 1 + 0.2 * max(k, self.snow_depth()), "fire": 1 - 0.1 * k}
            if kind == "heat":
                out["element"] = {"fire": 1 + 0.2 * k, "frost": 1 - 0.15 * k}
            if kind == "wind":
                out["sight"] = 1 + 0.2 * k                        # (the beasts smell him from further downwind)
        elif depth in FLOOD["floors"]:
            out["flood"] = self.flood_level
        return out

    # ---- saving -------------------------------------------------------------------------------------------------
    def to_json(self):
        return {"clock": self.clock, "cur": self.cur, "next": self.next, "prev": self.prev,
                "flood": self.flood_level, "flood_at": self.flood_at}

    @classmethod
    def from_json(cls, seed, d):
        s = cls(seed, (d or {}).get("clock", 0.0))
        if d and d.get("cur"):
            s.cur, s.next, s.prev = d["cur"], d.get("next"), d.get("prev")
            s.flood_level, s.flood_at = d.get("flood", 0.0), d.get("flood_at")
            s.step()
        return s
