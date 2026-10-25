"""Locally generated weather that follows the seasons. Nothing is downloaded.

Everything is worked out from the ClaudeXP clock (real month/day/time, always 2001) with seeded smooth noise, so
the weather is continuous through the day, changes gradually from day to day, and is identical on every launch.
A climate picks the yearly temperature curve, and the hemisphere decides which half of the year is summer."""
import math
import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import lru_cache

# mean annual temp C, seasonal swing C, day/night swing C, wetness 0..1
CLIMATES = {
    "Temperate": (12.0, 13.0, 5.0, 0.50),
    "Tropical": (27.0, 2.5, 4.0, 0.72),
    "Desert": (22.0, 11.0, 10.0, 0.10),
    "Cold": (1.0, 16.0, 4.0, 0.50),
}
HEMISPHERES = ("Northern", "Southern")

CLEAR, PARTLY, CLOUDY, OVERCAST, FOG, RAIN, THUNDER, SNOW = (
    "clear", "partly", "cloudy", "overcast", "fog", "rain", "thunder", "snow")
LABELS = {CLEAR: "Clear", PARTLY: "Partly Cloudy", CLOUDY: "Mostly Cloudy", OVERCAST: "Overcast", FOG: "Foggy",
          RAIN: "Rain", THUNDER: "Thunderstorms", SNOW: "Snow"}
SEVERITY = {CLEAR: 0, PARTLY: 1, CLOUDY: 2, OVERCAST: 3, FOG: 3, RAIN: 4, SNOW: 5, THUNDER: 6}
PRECIP = {RAIN, THUNDER, SNOW}
COMPASS = ("N", "NE", "E", "SE", "S", "SW", "W", "NW")


@lru_cache(maxsize=8192)
def _knot(key, i):
    return random.Random(f"{key}:{i}").uniform(-1.0, 1.0)


def noise(key, x):
    """Smooth value noise in -1..1."""
    i = math.floor(x)
    f = (1 - math.cos((x - i) * math.pi)) / 2
    return _knot(key, i) * (1 - f) + _knot(key, i + 1) * f


@dataclass
class Sample:
    when: datetime
    temp_c: float
    feels_c: float
    cond: str
    humidity: int
    wind_kph: float
    wind_dir: str
    pressure: int
    night: bool


@dataclass
class Day:
    date: datetime
    hi_c: float
    lo_c: float
    cond: str
    precip: int


def to_f(c):
    return c * 9 / 5 + 32


def temp_text(c, fahrenheit):
    return f"{round(to_f(c) if fahrenheit else c)}\N{DEGREE SIGN}"


def wind_text(kph, fahrenheit):
    return f"{round(kph * 0.621371)} mph" if fahrenheit else f"{round(kph)} km/h"


def _doy(when):
    return when.timetuple().tm_yday + (when.hour + when.minute / 60) / 24


def season(when, hemisphere="Northern"):
    key = (when.month, when.day)
    if key >= (12, 21) or key < (3, 20):
        name = "Winter"
    elif key < (6, 21):
        name = "Spring"
    elif key < (9, 22):
        name = "Summer"
    else:
        name = "Autumn"
    if hemisphere == "Southern":
        name = {"Winter": "Summer", "Summer": "Winter", "Spring": "Autumn", "Autumn": "Spring"}[name]
    return name


def sun_times(when, latitude=40.0, longitude=None):
    """(sunrise, sunset) in local clock hours, from the day's solar declination. With a longitude the times are
    placed properly in the time zone (solar noon isn't 12:00) and corrected for the equation of time and the
    refraction at the horizon: within a few minutes of the almanac. Without one, solar noon is taken as 12:00."""
    n = when.timetuple().tm_yday
    decl = math.radians(23.44) * math.sin(2 * math.pi * (n - 81) / 365)
    if longitude is None:
        arg = -math.tan(math.radians(latitude)) * math.tan(decl)
        noon = 12.0
    else:
        lat = math.radians(latitude)
        arg = (math.cos(math.radians(90.833)) - math.sin(lat) * math.sin(decl)) / (math.cos(lat) * math.cos(decl))
        b = 2 * math.pi * (n - 81) / 364
        eot = 9.87 * math.sin(2 * b) - 7.53 * math.cos(b) - 1.5 * math.sin(b)       # minutes, sundial ahead of clock
        noon = 12 + utc_offset_hours(when) - longitude / 15 - eot / 60
    half = math.degrees(math.acos(max(-1.0, min(1.0, arg)))) / 15
    return noon - half, noon + half


def utc_offset_hours(when):
    """The real PC's offset from UTC, in hours, for that month and day (daylight saving follows the real calendar)."""
    import time as _time
    try:
        stamp = _time.mktime(when.replace(year=_time.localtime().tm_year).timetuple())
        return _time.localtime(stamp).tm_gmtoff / 3600
    except (OverflowError, ValueError, AttributeError):
        return -_time.timezone / 3600


def moon_times(when, latitude=40.0, longitude=None, age=None):
    """(moonrise, moonset) in local hours, roughly: the moon follows the sun's path about 50 minutes later each day
    of its age, so its rise and set are the sun's shifted by that. Good to about half an hour; a widget's worth.
    `age` is the moon's age in days (from moon()); without it, the moon of `when` is used."""
    if age is None:
        _name, _lit, age = moon(when)
    rise, sset = sun_times(when, latitude, longitude)
    shift = age / 29.530588853 * 24
    return (rise + shift) % 24, (sset + shift) % 24


def hours_text(h):
    h %= 24
    hh, mm = int(h), int(round((h - int(h)) * 60))
    if mm == 60:
        hh, mm = (hh + 1) % 24, 0
    suffix = "am" if hh < 12 else "pm"
    return f"{hh % 12 or 12}:{mm:02d} {suffix}"


def moon(when):
    """(phase name, illuminated fraction, age in days)."""
    synodic = 29.530588853
    age = ((when - datetime(2000, 1, 6, 18, 14)).total_seconds() / 86400) % synodic
    lit = (1 - math.cos(2 * math.pi * age / synodic)) / 2
    step = int((age / synodic * 8) + 0.5) % 8
    names = ("New Moon", "Waxing Crescent", "First Quarter", "Waxing Gibbous",
             "Full Moon", "Waning Gibbous", "Last Quarter", "Waning Crescent")
    return names[step], lit, age


class Weather:
    def __init__(self, climate="Temperate", hemisphere="Northern", latitude=40.0):
        self.climate, self.hemisphere, self.latitude = climate, hemisphere, latitude

    def _params(self):
        return CLIMATES.get(self.climate, CLIMATES["Temperate"])

    def at(self, when):
        mean, swing, diurnal, wet = self._params()
        t_days = _doy(when)
        shift = 182.5 if self.hemisphere == "Southern" else 0
        seasonal = mean + swing * math.cos(2 * math.pi * (t_days - 201 - shift) / 365)

        cloud = 0.5 + 0.6 * noise("cloud", t_days * 1.1) + (wet - 0.5) * 0.6
        if self.climate == "Desert":
            cloud -= 0.2
        cloud = max(0.0, min(1.0, cloud))
        precip_level = noise("precip", t_days * 1.6)
        threshold = 0.72 - wet * 0.9

        hour = when.hour + when.minute / 60
        rise, sset = sun_times(when, self.latitude)
        night = not (rise <= hour <= sset)
        daily = seasonal + 3.5 * noise("temp", t_days / 3.0)
        temp = daily + diurnal * math.cos(2 * math.pi * (hour - 15) / 24) * (1 - 0.4 * cloud)
        if self.climate != "Tropical":
            temp -= 2.5 * max(0.0, cloud - 0.7)

        cond = CLEAR if cloud < 0.25 else PARTLY if cloud < 0.5 else CLOUDY if cloud < 0.72 else OVERCAST
        if cloud > 0.62 and precip_level > threshold:
            if temp <= 0.5:
                cond = SNOW
            elif temp > 17 and precip_level > threshold + 0.25 and 12 <= hour <= 22:
                cond = THUNDER
            else:
                cond = RAIN
        elif (3 <= hour <= 9.5 and 0.35 < cloud < 0.72 and wet > 0.3 and noise("fog", t_days) > 0.7
              and -2 < temp < 16):
            cond = FOG

        humidity = 38 + 34 * cloud + 12 * (cond in PRECIP or cond == FOG) + 8 * math.cos(2 * math.pi * (hour - 5) / 24)
        humidity = max(8.0, min(100.0, humidity - (35 if self.climate == "Desert" else 0)))
        wind = max(0.0, 8 + 12 * abs(noise("wind", t_days * 2.2)) + (10 if cond == THUNDER else 0)
                   + 4 * (1 - cloud) * math.sin(math.pi * hour / 24))
        direction = COMPASS[int((noise("dir", t_days * 0.8) + 1) / 2 * 8) % 8]
        pressure = 1013 + 14 * noise("front", t_days * 0.5) - (cloud - 0.5) * 14

        feels = temp
        if temp <= 10 and wind > 5:
            feels = 13.12 + 0.6215 * temp - 11.37 * wind ** 0.16 + 0.3965 * temp * wind ** 0.16
        elif temp >= 27 and humidity > 40:
            feels = temp + (humidity - 40) * 0.1 * (temp - 26) / 4
        return Sample(when, temp, feels, cond, round(humidity), wind, direction, round(pressure), night)

    def forecast(self, when, days=5):
        out = []
        for d in range(days):
            day = (when + timedelta(days=d)).replace(hour=0, minute=0, second=0, microsecond=0)
            samples = [self.at(day + timedelta(hours=h)) for h in range(0, 24, 2)]
            daytime = [s for s in samples if 6 <= s.when.hour <= 20]
            wet = [s for s in daytime if s.cond in PRECIP]
            if len(wet) >= 2:
                cond = max((s.cond for s in wet), key=SEVERITY.get)
            else:
                counts = {}
                for s in daytime:
                    counts[s.cond] = counts.get(s.cond, 0) + 1
                cond = max(counts, key=lambda c: (counts[c], -SEVERITY[c]))
            out.append(Day(day, max(s.temp_c for s in samples), min(s.temp_c for s in samples), cond,
                           round(100 * len(wet) / max(1, len(daytime)))))
        return out
