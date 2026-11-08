"""The forest's sky: an hour of night, ten minutes of day, two of dusk and dawn; the date; the weather and what it
leaves in the den; thunder."""
import random

from hollowoak.game import sky as S


def _run(sky, seconds, dt=0.5):
    out = []
    for _ in range(int(seconds / dt)):
        out += sky.step(dt)
    return out


def test_the_long_night_and_the_short_day():
    sky = S.Sky(random.Random(1))
    assert sky.hour_words() == "7:00 pm" and sky.phase()[0] == "dusk"
    assert sky.date_words() == "Saturday, 31st of October"
    _run(sky, 120)
    assert sky.phase()[0] == "night" and sky.hour_words() == "7:30 pm"
    _run(sky, 3600)
    assert sky.phase()[0] == "dawn" and sky.hour_words() == "6:30 am"
    assert sky.date_words() == "Sunday, 1st of November"
    _run(sky, 120)
    assert sky.phase()[0] == "day"
    lit = sky.light()
    assert lit["beam_k"] > 0.15 and lit["stars"] == 0 and lit["sun_up"] == 1.0
    _run(sky, 600)
    assert sky.phase()[0] == "dusk"


def test_dusk_and_dawn_colour_the_den():
    sky = S.Sky(random.Random(2))
    sky.weather, sky.strength, sky.target = "clear", 0.0, ("clear", 0.0)
    sky.clock = S.DUSK + 15
    dusk = sky.light()
    assert dusk["beam"][0] > dusk["beam"][2] * 2 and dusk["beam_k"] > 0.5        # (warm: orange)
    sky.clock = S.DAWN + 15 + 1440
    dawn = sky.light()
    assert dawn["beam_k"] > 0.5 and dawn["sky_low"][0] > dawn["sky_low"][2]
    sky.clock = 1440 + 2 * 60
    night = sky.light()
    assert night["beam_k"] == 0.0 and night["aurora"] == 1.0                     # (a clear night: the aurora)
    sky.weather, sky.strength = "overcast", 1.0
    assert sky.light()["aurora"] < 0.05                                           # (overcast: grey, no aurora)


def test_weather_and_what_it_leaves():
    sky = S.Sky(random.Random(3))
    sky.weather, sky.strength = "rain", 1.0
    sky.target, sky.next_weather = ("rain", 1.0), 1e9
    sky.puddles = 0.0
    _run(sky, 200)
    assert sky.puddles > 0.4
    sky.weather, sky.target = "snow", ("snow", 1.0)
    _run(sky, 200)
    assert sky.snow > 0.3
    sky.weather, sky.target = "storm", ("storm", 1.0)
    thunder = [e for e in _run(sky, 120) if e[0] == "thunder"]
    assert len(thunder) >= 2
    sky.target = ("clear", 0.0)
    turned = _run(sky, 60)
    assert ("weather", "clear") in turned and sky.weather == "clear"
    seen = set()
    for seed in range(40):
        seen.add(S.Sky(random.Random(seed)).weather)
    assert seen == set(S.KINDS)
