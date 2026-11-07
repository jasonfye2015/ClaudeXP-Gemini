"""The traps, the Gauntlet (a boss rush), the hidden rooms, and the secrets that can be found."""
from claudenites.game import data as D
from claudenites.game import eggs, features, levels
from claudenites.game.world import Bolt, Game


def _game_on(L):
    g = Game.new(seed=11)
    g.depth = L.depth
    g._enter(L)
    g.monsters = []
    return g


def test_traps_are_laid_fairly():
    total = 0
    for d in range(2, D.FLOORS + 1, 3):
        L = levels.dungeon(d, 99)
        start = L.rooms[0]
        total += len(L.traps)
        assert len(L.traps) <= 8
        for t in L.traps:
            assert L.open_at(t["x"], t["y"]) and (t["x"], t["y"]) not in L.water
            assert not (start.x <= t["x"] < start.x + start.w and start.y <= t["y"] < start.y + start.h)
            assert abs(t["x"] + 0.5 - L.stairs[0]) >= 1.5 or abs(t["y"] + 0.5 - L.stairs[1]) >= 1.5
            assert any(f[4] == features.TRAPS[t["kind"]] for f in L.flats)        # (a plate or a vent to see)
    assert total > 60
    assert not levels.dungeon(1, 99).traps                                     # (the first floor: none)


def test_the_spikes_the_darts_and_the_fire():
    L = next(levels.dungeon(d, 99) for d in range(2, 60) if {t["kind"] for t in levels.dungeon(d, 99).traps} >= {"spikes", "darts", "fire"})
    g = _game_on(L)
    p = g.player
    spikes = next(t for t in L.traps if t["kind"] == "spikes")
    g.x, g.z, g.y = spikes["x"] + 0.5, spikes["y"] + 0.5, spikes["f"]
    life = p.life
    g._traps(0.02)
    assert p.life < life
    hurt = p.life
    g._traps(0.02)
    assert p.life == hurt                                                      # (it doesn't spring again at once)
    darts = next(t for t in L.traps if t["kind"] == "darts")
    g.x, g.z, g.y = darts["x"] + 0.5, darts["y"] + 0.5, darts["f"]
    g._traps(0.02)
    assert any(b.foe and b.element == "venom" for b in g.bolts)
    fire = next(t for t in L.traps if t["kind"] == "fire")
    g.x, g.z, g.y = fire["x"] + 0.5, fire["y"] + 0.5, fire["f"]
    g.time = features.FIRE_CYCLE * 10 - fire["phase"] + features.FIRE_CYCLE - 0.3     # (between bursts: safe)
    life = p.life
    g._traps(0.02)
    assert p.life == life and not fire["on"]
    g.time += 0.5                                                              # (now it breathes)
    g._traps(0.02)
    assert fire["on"] and p.life < life


def test_the_gauntlet():
    seed, d = next((s, d) for s in (99, "0:0", "a", "b", "c", "d") for d in range(12, 100)
                   if features.special_of(d, s) == "rush")
    L = levels.dungeon(d, seed)
    bi = (d - 1) // 10
    assert L.rush == [b["guardian"] for b in D.BANDS[:bi]][-4:] and L.arena and L.guardian
    g = _game_on(L)
    ax, ay, aw, ah = L.arena
    assert not any(ax <= m.x < ax + aw and ay <= m.z < ay + ah for m in g.monsters)
    g.x, g.z = ax + 0.5, ay + 0.5
    g._gauntlet()
    seen = []
    for wave in range(len(L.rush)):
        boss = g.rush_boss
        assert boss and boss.guardian and boss.name == L.rush[wave] and not g.guardian_down
        seen.append(boss.name)
        g._kill(boss)
        g.time += 5
        g._gauntlet()
    assert seen == L.rush and g.guardian_down
    assert L.chests[-1].get("legendary")
    before = list(g.player.inventory)
    g.open_chest(len(L.chests) - 1)
    new = [it for it in g.player.inventory if it not in before]
    assert any(it.get("rarity") == 4 for it in new)


def test_hidden_rooms_and_their_walls():
    L = levels.dungeon(1, 99)
    (wx, wy), sw = next(iter(L.secret_walls.items()))
    assert sw["what"] == "workshop" and not L.open_at(wx, wy)
    chest = next(c for c in L.chests if c.get("secret"))
    assert L.distances(int(L.start[0]), int(L.start[1]))[int(chest["z"]), int(chest["x"])] < 0
    g = _game_on(L)
    v = L.mesh_version
    front = next((wx + dx, wy + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)) if L.open_at(wx + dx, wy + dy))
    ox, oz = front[0] + 0.5, front[1] + 0.5
    b = Bolt(ox, L.floor[front[1], front[0]] + 0.9, oz, (wx - front[0]) * 9, 0, (wy - front[1]) * 9, 10, "fire")
    g.bolts = [b]
    for _ in range(20):
        g._bolts(0.02)
    assert L.open_at(wx, wy) and L.mesh_version == v + 1
    assert L.distances(int(L.start[0]), int(L.start[1]))[int(chest["z"]), int(chest["x"])] >= 0
    hidden = sum(bool(levels.dungeon(d, 99).secret_walls) for d in range(2, 100) if d != 42)
    assert 5 <= hidden <= 30
    assert levels.dungeon(42, 99).secret_walls                                 # (the quiet room: always)


def test_the_secrets():
    g = Game.new(seed=12)
    gold = g.player.gold
    assert "forty-two" in eggs.phrase(g, "apothecary", "xyzzy") and g.player.gold == gold + 42
    assert "only works the once" in eggs.phrase(g, "outfitter", "XYZZY") and g.player.gold == gold + 42
    assert eggs.phrase(g, "sage", "tell me about the lich king")
    assert eggs.phrase(g, "apothecary", "hello") is None
    # the moon, three times, at night, from home
    g.sky.tick(((22 - g.sky.hour) % 24) * 60)
    assert g.sky.night and g.depth == 0
    mv = eggs.moon_vector(g.sky)
    import math
    g.yaw, g.pitch = math.atan2(mv[0], -mv[2]), math.asin(mv[1])
    for _ in range(3):
        g.cool = 0
        g.player.mana = g.player.max_mana()
        g._fire()
    assert any(it.get("base") == "Moonkissed Band" for it in g.player.inventory)
    # the quiet room's towel, and the workshop's line
    L = levels.dungeon(42, 99)
    g2 = _game_on(L)
    towel = next(p for p in L.pickups if p["kind"] == "egg")
    L.pickups.remove(towel)
    g2._take(towel)
    assert any(it.get("base") == "Well-Travelled Towel" and it["rarity"] == 4 for it in g2.player.inventory)
    L1 = levels.dungeon(1, 99)
    g3 = _game_on(L1)
    piece = next(pc for pc in L1.pieces if pc.get("egg") == "workshop")
    assert "Jason and Claude" in piece["line"]
    g3.x, g3.z = piece["x0"] + 0.5, piece["y0"] + 0.5
    g3._places()
    assert "workshop" in g3.player.stats["eggs"]
    assert set(eggs.TOTAL * [None]) and len(features.EGGS) == eggs.TOTAL
