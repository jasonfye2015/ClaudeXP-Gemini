"""What the sky looks like this moment (game/sky.py's state, made into colours and light), as Claude and Magic's
renderer sees it: the hour's sky (night, dawn, day, dusk), the sun and the moon on their arc (the moon in its phase),
clouds as many as the weather brings, stars on clear nights, an aurora on some winter nights, a rainbow in a
sun-shower, lightning; the light the land gets (the sun's colour and strength, the ambient, the moon's), the fog
(mist thickens it, rain greys it), and the snow and frost on the ground. Below, only a little reaches: a storm's
flash through the grates, the damp."""
import math

COVER = {"clear": 0.0, "cloud": 0.55, "rain": 0.75, "storm": 0.95, "mist": 0.5, "wind": 0.35, "snow": 0.8,
         "heat": 0.0, "aurora": 0.0, "tornado": 0.85}


def _mix(a, b, k):
    return tuple(x + (y - x) * k for x, y in zip(a, b))


def _smooth(e0, e1, x):
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


def look(sky, outdoor, base_fog=0.042):
    """-> dict for the renderer: sky_top, sky_horizon (linear-ish 0..1 sRGB), sun_dir (toward the sun), sun_col,
    ambient, fog (colour, density), stars, moon (dir, phase), cloud, wind, aurora, rainbow, snow, frost, rain, snowfall."""
    d = sky.dial()
    w = sky.now()
    kind, k = w["kind"], w["strength"]
    sa = math.radians(d["sun"])
    sun_v = (math.sin(sa) * 0.94, math.cos(sa), 0.34)                     # (east to west, a little to the south)
    ma = math.radians(d["moon"])
    moon_v = (math.sin(ma) * 0.94, math.cos(ma), -0.3)
    elev = sun_v[1]
    day = _smooth(-0.12, 0.22, elev)
    twilight = max(0.0, 1 - abs(elev - 0.02) / 0.22) * (1 - 0.6 * day)
    cover = COVER.get(kind, 0) * (k if kind != "clear" else 0)
    top = _mix((0.012, 0.018, 0.045), (0.16, 0.30, 0.56), day)
    hor = _mix((0.035, 0.045, 0.085), (0.55, 0.66, 0.78), day)
    hor = _mix(hor, (0.88, 0.52, 0.32), twilight * 0.8)
    top = _mix(top, (0.28, 0.24, 0.42), twilight * 0.5)
    grey = _mix((0.05, 0.055, 0.065), (0.44, 0.47, 0.5), day)
    if kind == "storm":
        grey = tuple(g * 0.62 for g in grey)
    top = _mix(top, grey, cover * 0.85)
    hor = _mix(hor, _mix(grey, (0.6, 0.62, 0.64), 0.3 * day), cover * 0.7)
    if kind == "heat":
        hor = _mix(hor, (0.85, 0.75, 0.55), 0.35 * k * day)
    if kind == "tornado":
        hor = _mix(hor, (0.42, 0.45, 0.3), 0.4 * k)
    moonlight = (1 - abs(d["phase"] - 4) / 4) * 0.08
    sun_col = _mix((1.0, 0.55, 0.3), (0.95, 0.88, 0.75), _smooth(0.0, 0.35, elev))
    sun_k = day * (1 - 0.75 * cover)
    amb = 0.1 + moonlight * (1 - cover) + 0.45 * day * (1 - 0.3 * cover)
    if kind == "aurora":
        amb += 0.05 * k
    fog_d = base_fog
    if kind == "mist":
        fog_d += 0.09 * k
    elif kind in ("rain", "snow"):
        fog_d += 0.025 * k
    elif kind in ("storm", "tornado"):
        fog_d += 0.035 * k
    fog_c = _mix(hor, (0.62, 0.66, 0.7), 0.5 * k if kind == "mist" else 0.0)
    snow = sky.snow_depth()
    return {
        "sky_top": top, "sky_horizon": hor, "sun_v": sun_v, "sun_col": tuple(c * sun_k for c in sun_col),
        "sun_disc": day * (1 - cover * 0.9), "ambient": amb, "fog": (fog_c, fog_d),
        "stars": (1 - day) * (1 - cover) * (0.3 if kind == "mist" else 1.0), "moon_v": moon_v, "phase": d["phase"],
        "moon_disc": (1 - day * 0.85) * (1 - cover * 0.9), "cloud": max(0.12, cover) if kind != "clear" else 0.12,
        "wind": w["wind"], "aurora": k if kind == "aurora" else 0.0, "rainbow": sky.rainbow(),
        "snow": snow, "frost": sky.ground_frost(),
        "rain": k if kind in ("rain", "storm") else 0.0, "storm": k if kind == "storm" else 0.0,
        "snowfall": k if kind == "snow" else 0.0, "leaves": k if kind in ("wind", "tornado") else 0.0,
        "kind": kind, "strength": k, "night": d["night"],
        "mud": max(k if kind in ("rain", "storm") else 0.0, sky.after_rain()),
        "autumn": 1.0 if sky.season == "autumn" else 0.0,
    }
