"""Auto-play (game/autoplay.py): Claude playing himself - a floor cleared and home again, his things seen to - and the
endless Deep past the hundredth floor."""
import random

from claudenites.game import autoplay, data as D, items as I, levels
from claudenites.game.world import Game, Input


def test_auto_play_clears_a_floor_and_goes_on():
    g = Game.new(seed=21)
    g.go_floor(1)
    inp, bot = Input(), autoplay.Autopilot()
    depths = []
    for _ in range(9000):                                   # (seven and a half minutes of play)
        bot.drive(g, inp, 0.05)
        g.step(0.05, inp)
        g.events.clear()
        if not depths or depths[-1] != g.depth:
            depths.append(g.depth)
        if len(depths) >= 3:
            break
    assert depths[:3] == [1, 0, 2], depths                  # (floor 1, home, floor 2)
    assert g.player.stats["kills"] > 15 and g.player.level >= 2
    assert g.run_floor == 2


def test_seeing_to_his_things():
    g = Game.new(seed=22)
    p = g.player
    rng = random.Random(5)
    p.level, p.skill_points, p.gold = 20, 6, 20000
    p.inventory = [I.make_wand("crystal", 20, rarity=2), I.make_part("lens", 3, rarity=2),
                   I.make_part("core", 3, "fire", 1), I.make_part("quickener", 3), I.make_gear("robe", 20, 3, rng),
                   I.make_gear("hat", 1, 0, rng)]
    p.larder.update({"raw:meat": 2, "raw:potato": 1, "raw:carrot": 1, "seed:carrot": 3})
    before = I.wand_stats(p.wand())["dps"]
    said = autoplay.housekeeping(g, rng)
    assert said and I.wand_stats(p.wand())["dps"] > before * 2         # (the crystal wand, its parts set)
    assert p.gear["robe"] and p.gear["robe"]["rarity"] == 3
    assert not [it for it in p.inventory if it.get("type") in ("gear", "wand", "part")]   # (the rest sold)
    assert p.skill_points == 0 and p.skills
    assert p.potions["health"] >= 6 and p.potions["mana"] >= 4
    assert any(g.farm.plots) and p.cookbook                            # (planted, and something cooked)
    assert len(p.buffs) >= 1


def test_the_best_wand_is_built():
    birch, crystal = I.make_wand("birch"), I.make_wand("crystal", 10)
    parts = [I.make_part("lens", 2), I.make_part("core", 2, "storm"), I.make_part("splitter", 2)]
    body, chosen = autoplay.best_wand([birch, crystal], parts)
    assert body is crystal and any(chosen)
    assert I.wand_stats(dict(body, parts=chosen))["dps"] >= max(I.wand_stats(birch)["dps"], I.wand_stats(crystal)["dps"])


def test_endless():
    assert D.band_of(101) is D.BANDS[0] and D.band_of(195) is D.BANDS[9] and D.band_of(100) is D.BANDS[9]
    g = Game.new(seed=23)
    g.go_floor(150)
    assert g.depth == 100                                   # (not yet: the bottom first)
    g.player.stats["won"] = True
    g.depth = 100
    g.stairs_home()
    assert g.run_floor == 101
    g.go_floor(101)
    assert g.depth == 101 and g.level.name.startswith(D.BANDS[0]["name"])
    assert I.depth_scale(101) > I.depth_scale(100)
    L = levels.dungeon(110, 3)
    assert L.guardian == D.BANDS[0]["guardian"]               # (the guardians come round again too)


def test_auto_play_sped_up():
    """The view steps the game several times a frame at speed (as ui/view.py does): the same play, sooner."""
    g = Game.new(seed=24)
    g.go_floor(1)
    inp, bot = Input(), autoplay.Autopilot()
    for _frame in range(250):                             # (250 frames at x8: a hundred seconds of play)
        for _ in range(8):
            bot.drive(g, inp, 0.05)
            g.step(0.05, inp)
        g.events.clear()
    assert g.time > 99 and g.player.stats["kills"] > 5
