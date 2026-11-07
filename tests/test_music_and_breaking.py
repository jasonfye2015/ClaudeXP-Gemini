"""ClaudeRPG's music, made here; and the things a bolt can break."""
import numpy as np

from claudenites.engine.music import PLACES, STYLES, Synth
from claudenites.game import levels
from claudenites.game.world import Bolt, Game


def test_every_place_has_its_music():
    """The town, the forest and every band: ClaudeRPG's styles, calm and in a guardian's fight, never silent, never
    clipping, and a fight is faster than the calm."""
    for key in ["title", "town", "forest"] + list(range(10)):
        style, root = PLACES[key]
        assert style is None or style in STYLES
        for boss in (False, True):
            s = Synth(16000, seed=3)
            s.place(key, boss)
            out = np.concatenate([s.render(800) for _ in range(20 * 12)])
            assert np.isfinite(out).all() and np.abs(out).max() < 0.999, (key, boss)
            assert np.sqrt((out ** 2).mean()) > 0.01, (key, boss)
    calm, fight = Synth(16000), Synth(16000)
    calm.place(0)
    fight.place(0, boss=True)
    calm.render(16000 * 4)
    fight.render(16000 * 4)
    assert fight.step > calm.step * 2


def test_the_waltz_and_the_drums():
    """The Old Foundry waltzes in threes (ClaudeRPG's Clockwork City); the Ember Deep has its kick drums."""
    s = Synth(16000, seed=1)
    s.place(5)
    assert STYLES["city"]["waltz"] and s.style is STYLES["city"]
    s.render(16000 * 3)
    s2 = Synth(16000, seed=1)
    s2.place(7)
    s2.render(16000 * 6)
    assert s2.style.get("drums")


def test_a_barrel_breaks():
    g = Game.new(seed=8)
    for d in range(1, 30):
        g.go_floor(d)
        L = g.level
        found = [t for v in L.breakables().values() for t in v if t[0].get("model") == "barrel"]
        if found:
            break
    thing, x, z, y, r, h = found[0]
    assert not L.can_stand(x, z, 0.24, y)
    n = len(L.props)
    for _ in range(30):                                   # (bolts straight at it, until it gives)
        g.bolts = [Bolt(x - 0.6, y + h * 0.5, z, 12, 0, 0, 10, "fire")]
        for _ in range(10):
            g._bolts(1 / 60)
        if thing not in L.props:
            break
    assert thing not in L.props and len(L.props) == n - 1
    assert L.can_stand(x, z, 0.24, y)                     # (where it stood is clear now)
    assert any(e[0] == "break" for e in g.events)
    assert sum(1 for f in g.fx if f.get("kind") == "debris") >= 5


def test_racks_and_shelves_break_too():
    L = levels.dungeon(3, 4)
    names = {t[0].get("name") or t[0].get("model") for v in L.breakables().values() for t in v}
    assert names & {"fu.rack", "fu.shelf", "barrel", "crate"}
