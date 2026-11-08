"""The forest's sky over the oak: its clock and its weather. The forest is a magical one: its nights are long - many
times the day. In real time a night lasts an hour, the day ten minutes, dusk and dawn two minutes each, and they
colour the den as they pass.

    sky = Sky(rng)
    sky.step(dt)                     -> events: ("thunder", strength), ("weather", kind)
    sky.clock                        minutes since midnight of the first day (a night begins at dusk, 7 pm)
    sky.hour_words(), sky.date_words()
    sky.phase()                      -> (name, 0..1 through it): "dusk", "night", "dawn", "day"
    sky.light()                      what the den gets from above, now: {"beam": (r,g,b) of the light down through the
                                     crown and the knot-holes, "beam_k", "sky_top", "sky_low", "stars", "aurora",
                                     "sun" (direction), "flash"}
    sky.weather, sky.strength        "clear", "overcast", "rain", "storm" (rain and thunder), "snow"; 0..1
    sky.puddles, sky.snow            what's lying in the den from it (0..1): growing while it falls, going after
    sky.dark_minutes(...)            (for tests) how many real seconds each part lasts

Plain Python: the tests run it."""
import math

DUSK, NIGHT, DAWN, DAY = 19 * 60, 19 * 60 + 30, 6 * 60 + 30, 7 * 60           # (minutes of the day they begin)
# real seconds each part lasts: the night an hour, the day ten minutes, dusk and dawn two each
SECONDS = {"dusk": 120.0, "night": 3600.0, "dawn": 120.0, "day": 600.0}
MINUTES = {"dusk": 30.0, "night": 660.0, "dawn": 30.0, "day": 720.0}
START = DUSK                                                                    # (he comes at dusk)
WEEKDAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
FIRST = (5, 31, "October")                                                      # (a Saturday, the last of October)
MONTHS = (("October", 31), ("November", 30), ("December", 31))
KINDS = ("clear", "overcast", "rain", "storm", "snow")
CHANCE = (0.34, 0.26, 0.2, 0.1, 0.1)
NAMES = {"clear": ("Clear", "Clear night"), "overcast": ("Overcast", "Overcast"), "rain": ("Rain", "Rain"),
         "storm": ("Thunderstorm", "Thunderstorm"), "snow": ("Snow", "Snow")}


def phase_of(minute):
    m = minute % 1440
    if DUSK <= m < NIGHT:
        return "dusk", (m - DUSK) / MINUTES["dusk"]
    if m >= NIGHT or m < DAWN:
        return "night", ((m - NIGHT) % 1440) / MINUTES["night"]
    if DAWN <= m < DAY:
        return "dawn", (m - DAWN) / MINUTES["dawn"]
    return "day", (m - DAY) / MINUTES["day"]


def _mix(a, b, k):
    return tuple(x + (y - x) * k for x, y in zip(a, b))


class Sky:
    def __init__(self, rng, clock=START):
        self.rng = rng
        self.clock = float(clock)
        self.weather = self._pick()
        self.strength = self.rng.uniform(0.4, 1.0) if self.weather != "clear" else 0.0
        self.next_weather = self.rng.uniform(300, 900)
        self.target = (self.weather, self.strength)
        self.t = 0.0
        self.puddles = 0.15 if self.weather in ("rain", "storm") else 0.0
        self.snow = 0.2 if self.weather == "snow" else 0.0
        self.flash = 0.0
        self.next_thunder = self.rng.uniform(8, 25)

    def _pick(self):
        r, acc = self.rng.random(), 0.0
        for k, c in zip(KINDS, CHANCE):
            acc += c
            if r < acc:
                return k
        return "clear"

    # ---- the clock -------------------------------------------------------------------------------------------------
    def rate(self):
        """Minutes of the day that pass in a real second, now."""
        name, _k = phase_of(self.clock)
        return MINUTES[name] / SECONDS[name]

    def phase(self):
        return phase_of(self.clock)

    def day(self):
        return int(self.clock // 1440)

    def hour_words(self):
        m = int(self.clock) % 1440
        h = m // 60
        return f"{(h - 1) % 12 + 1}:{m % 60:02d} {'pm' if 12 <= h < 24 else 'am'}"

    def date_words(self):
        wd, d, month = FIRST
        n = self.day()
        i = next(k for k, (name, _) in enumerate(MONTHS) if name == month)
        d += n
        while d > MONTHS[i][1]:
            d -= MONTHS[i][1]
            i = (i + 1) % len(MONTHS)
        suffix = "th" if 10 <= d % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(d % 10, "th")
        return f"{WEEKDAYS[(wd + n) % 7]}, {d}{suffix} of {MONTHS[i][0]}"

    def weather_words(self):
        name, _k = self.phase()
        return NAMES[self.weather][1 if name in ("night", "dusk") else 0]

    # ---- a step -----------------------------------------------------------------------------------------------------
    def step(self, dt):
        out = []
        self.clock += self.rate() * dt
        self.t += dt
        if self.t >= self.next_weather:                       # (the weather turns)
            self.next_weather = self.t + self.rng.uniform(420, 1200)
            kind = self._pick()
            self.target = (kind, self.rng.uniform(0.4, 1.0) if kind != "clear" else 0.0)
        kind, strength = self.target
        if kind != self.weather:                              # (the old weather dies away, then the new comes in)
            self.strength = max(0.0, self.strength - dt / 40.0)
            if self.strength <= 0.0:
                self.weather = kind
                out.append(("weather", kind))
        else:
            self.strength += (strength - self.strength) * min(1.0, dt / 30.0)
        wet = self.strength if self.weather in ("rain", "storm") else 0.0
        self.puddles = min(1.0, max(0.0, self.puddles + (wet * 0.004 - 0.0012) * dt))
        name, _k = self.phase()
        melt = 0.002 if name == "day" else 0.0004
        snowing = self.strength if self.weather == "snow" else 0.0
        self.snow = min(1.0, max(0.0, self.snow + (snowing * 0.003 - melt - wet * 0.003) * dt))
        self.flash = max(0.0, self.flash - dt * 3.5)
        if self.weather == "storm" and self.strength > 0.3:
            if self.t >= self.next_thunder:
                self.next_thunder = self.t + self.rng.uniform(9, 28) / self.strength
                k = self.rng.uniform(0.5, 1.0) * self.strength
                self.flash = k
                out.append(("thunder", k))
        return out

    # ---- what the den gets from above -------------------------------------------------------------------------------
    def light(self):
        name, k = self.phase()
        over = self.strength if self.weather in ("overcast", "rain", "storm", "snow") else 0.0
        night_top, night_low = (0.0015, 0.002, 0.004), (0.003, 0.0045, 0.01)
        day_top, day_low = (0.12, 0.22, 0.42), (0.45, 0.58, 0.72)
        dusk_top, dusk_low = (0.08, 0.05, 0.16), (0.85, 0.36, 0.16)
        dawn_top, dawn_low = (0.16, 0.12, 0.3), (0.95, 0.55, 0.45)
        if name == "night":
            top, low, beam, beam_k = night_top, night_low, (0.0, 0.0, 0.0), 0.0
        elif name == "day":
            top, low, beam, beam_k = day_top, day_low, (1.0, 0.93, 0.78), 1.0
        else:                                                 # (dusk and dawn: the colours come and go)
            warm_top, warm_low = (dusk_top, dusk_low) if name == "dusk" else (dawn_top, dawn_low)
            beam = (1.0, 0.45, 0.2) if name == "dusk" else (1.0, 0.6, 0.55)
            arc = math.sin(math.pi * k)
            if name == "dusk":
                frm_top, frm_low, to_top, to_low = day_top, day_low, night_top, night_low
            else:
                frm_top, frm_low, to_top, to_low = night_top, night_low, day_top, day_low
            base_top, base_low = _mix(frm_top, to_top, k), _mix(frm_low, to_low, k)
            top, low = _mix(base_top, warm_top, arc), _mix(base_low, warm_low, arc)
            beam_k = (1.0 - k if name == "dusk" else k) * 0.6 + arc * 0.9
        grey = (0.12, 0.13, 0.15) if name == "day" else (0.02, 0.022, 0.026)
        top, low = _mix(top, grey, over * 0.85), _mix(low, grey, over * 0.9)
        beam_k *= 1.0 - 0.8 * over
        if name in ("day", "dawn", "dusk") and over > 0.3:
            beam = _mix(beam, (0.75, 0.78, 0.82), over)
        night_k = 1.0 if name == "night" else (k if name == "dusk" else (1.0 - k if name == "dawn" else 0.0))
        clear = 1.0 - over
        hour = (self.clock % 1440) / 60.0
        sun_a = (hour - 6.0) / 12.0 * math.pi                  # (east at six, overhead at noon, west at six)
        sun = (math.cos(sun_a), max(0.15, math.sin(sun_a)), 0.35)
        n = math.sqrt(sum(c * c for c in sun))
        return {"sky_top": top, "sky_low": low, "beam": beam, "beam_k": beam_k * (1.0 - night_k * 0.0),
                "stars": night_k * clear, "aurora": night_k * clear, "sun": tuple(c / n for c in sun),
                "sun_up": 0.0 if name == "night" else (1.0 - night_k), "flash": self.flash, "phase": name}
