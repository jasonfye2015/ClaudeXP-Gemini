"""Claude and Magic's sky, carried over: the clock, the season's daylight, the moon, the weather's events, the flood
below, and what the weather does to play."""
from claudenites.game.sky import CLOCK, DAYLIGHT, WX, Sky
from claudenites.game.world import Game, Input, Monster


def test_the_clock_and_the_moon():
    s = Sky(1, season="summer")
    assert s.time_figures() == "6:00" and s.day == 0
    s.tick(6 * 60)
    assert s.time_figures() == "12:00" and not s.night
    s.tick(11 * 60)
    assert s.night                                      # (23:00, past summer's dusk at 22)
    phases = set()
    for _ in range(CLOCK["moon"]):
        s.tick(24 * 60)
        phases.add(s.moon_phase)
    assert phases == set(range(8))
    for season, (dawn, dusk) in DAYLIGHT.items():
        t = Sky(2, season=season)
        d = t.dial()
        assert -180 <= d["sun"] <= 180 and abs(((d["moon"] - d["sun"]) % 360) - 180) < 1e-6


def test_the_weather_comes_and_goes():
    seen = set()
    for season in ("spring", "summer", "autumn", "winter"):
        s = Sky(7, season=season)
        for _ in range(24 * 40):                         # (forty days, an hour at a time)
            s.tick(60)
            c = s.cur
            assert c["kind"] in WX["kinds"] and c["from"] <= s.clock < c["until"]
            if c["kind"] != "clear":
                assert 60 <= c["until"] - c["from"] <= 360
            n = s.now()
            assert 0 <= n["strength"] <= 1 and 0 < n["wind"][0] <= 1.0
            seen.add(c["kind"])
        if season == "winter":
            assert "snow" in seen
    assert {"rain", "storm", "mist", "wind", "snow", "cloud", "heat"} <= seen


def test_a_storm_floods_the_first_floors():
    s = Sky(3, season="spring")
    s.cur = {"kind": "storm", "strength": 1.0, "from": s.clock, "until": s.clock + 300}
    said = s.tick(30)
    assert s.flood == 1.0 and ("flood", 1) in said
    s.cur = {"kind": "clear", "strength": 1.0, "from": s.clock, "until": s.clock + 5000}
    s.next = None
    s.tick(12 * 60)
    assert 0.4 < s.flood < 0.6
    s.tick(13 * 60)
    assert s.flood == 0
    g = Game.new(seed=4)
    g.go_floor(2)
    g.sky.flood_level, g.sky.flood_at = 1.0, g.sky.clock
    g.sky.cur = {"kind": "storm", "strength": 1.0, "from": g.sky.clock, "until": g.sky.clock + 300}
    g.step(0.02, Input())
    sunk = [(x, y) for (x, y) in g.level.open_squares() if g.level.floor[y, x] < -0.1]
    if sunk:
        assert g.flooded(*sunk[0])


def test_the_weather_in_play():
    s = Sky(5, season="spring")
    s.cur = {"kind": "rain", "strength": 1.0, "from": s.clock - 60, "until": s.clock + 300}
    e = s.effects(True, 0)
    assert e["element"]["fire"] < 1 < e["element"]["storm"]
    assert s.effects(False, 40)["element"] == {}                 # (the Deep's own air, below the first floors)
    s.cur = {"kind": "mist", "strength": 1.0, "from": s.clock - 60, "until": s.clock + 300}
    assert s.effects(True, 0)["sight"] < 0.6
    s.cur = {"kind": "storm", "strength": 1.0, "from": s.clock - 60, "until": s.clock + 300}
    assert s.effects(True, 0)["lightning"] > 0
    # a fire bolt in the rain does less than in the clear
    g = Game.new(seed=6)
    m = Monster("Wolf", g.x + 3, g.z, 5, __import__("random").Random(1))
    g.monsters = [m]
    g.wx = Sky(6, season="spring").effects(True, 0)
    g.rng.seed(1)
    hp = m.hp
    g._hit(m, 10, "fire")
    clear_hit = hp - m.hp
    m.hp = hp
    g.wx = e
    g.rng.seed(1)
    g._hit(m, 10, "fire")
    assert hp - m.hp < clear_hit


def test_a_tornado_crosses_the_wood():
    s = Sky(8, season="autumn")
    s.cur = {"kind": "tornado", "strength": 1.0, "from": s.clock, "until": s.clock + 120, "twister": (1.0, 0.0)}
    a = s.twister(176)
    s.clock += 60
    b = s.twister(176)
    assert b[0] > a[0] and abs(b[1] - a[1]) < 1e-6


def test_the_sky_is_saved():
    g = Game.new(seed=9)
    g.sky.tick(1234)
    d = g.to_json()
    h = Game.from_json(d)
    assert abs(h.sky.clock - g.sky.clock) < 1e-6 and h.sky.cur["kind"] == g.sky.cur["kind"]
    g.go_floor(1)
    before = g.sky.clock
    g.descend()
    assert g.sky.clock - before >= 60                            # (the stairs take an hour)
