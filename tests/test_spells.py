"""Spells: Light, Warmth, Illusion, Memory - in her house, and before her in her scenes."""
import math
import random

from hollowoak.game import dialogue as D
from hollowoak.game import night as N
from hollowoak.game import notes
from hollowoak.game import spells as S


def _step(n, secs, dt=0.05):
    inp = N.Input()
    inp.yaw, inp.pitch = n.yaw, n.pitch
    for _ in range(int(secs / dt)):
        n.step(dt, inp)
        n.events.clear()


def test_resting_between():
    n = N.Night(seed=3)
    assert n.cast("warmth")[0] == ("spell", "warmth", "cast")
    assert n.cast("warmth")[0] == ("spell", "warmth", "resting")
    _step(n, S.REST["warmth"] + 0.2)
    assert n.spells.ready("warmth")


def test_light_lights_and_hurts_her_eyes():
    n = N.Night(seed=4)
    n.her.at = lambda *a: n.eye                                    # (right by him)
    before = n.moods.suspicion
    out = n.cast("light")
    assert ("her", "hurt") in out and n.her.state == "withdraw"
    assert n.moods.suspicion > before
    n.spells.step(0.5)
    assert n.spells.shining("light") > 0.9
    n.spells.step(S.LIGHT_FOR)
    assert n.spells.shining("light") == 0.0 and not n.spells.lit


def test_light_shows_the_old_marks():
    n = N.Night(seed=5)
    mx, my, mz = S.mark_at(n.tree, "tunnel", 6.5)
    assert math.isfinite(mx + my + mz)
    for _mid, where, along, _r in S.MARKS:                         # (each in the wood, where he can come)
        p = S.mark_at(n.tree, where, along)
        assert math.isfinite(sum(p))
    n.x, n.z = mx, mz
    n.y = n.tree.floor_at(mx, mz, my)
    out = n.cast("light")
    assert ("mark", "mark_roots") in out
    assert notes.unlock_for(("mark", "mark_roots")) == ["mark_roots"]
    assert "mark_roots" in notes.PAGES and notes.PAGES["mark_roots"][0] in notes.SECTIONS


def test_warmth_on_her_silk_smoulders():
    n = N.Night(seed=6)
    n.on = n.web.loom
    s0, p0 = n.moods.suspicion, n.moods.patience
    out = n.cast("warmth")
    assert out[-1][0] == "smoulder"
    assert n.moods.suspicion > s0 and n.moods.patience < p0 and n.flags["smouldered"] == 1
    assert notes.unlock_for(out[-1]) == ["smoulder"]
    assert any(k == "ember" for k, *_ in n.spells.lit)


def test_illusion_hides_him_from_the_small_ones():
    n = N.Night(seed=7)
    n.cast("illusion")
    assert n.spells.illusion
    _step(n, 10.0)
    assert not n.crawlers.runs and not n.danglers.hanging
    _step(n, 6.0)
    assert not n.spells.illusion


def test_illusion_before_her_can_be_seen_through():
    seen = dazzled = 0
    for k in range(40):
        n = N.Night(seed=k)
        n.spells.rng = random.Random(k)
        n.moods.suspicion = 60
        tier, line, said = n.spells.in_scene("illusion", n)
        if tier == "insult":
            seen += 1
            assert n.moods.suspicion >= 75
        else:
            dazzled += 1
    assert seen and dazzled


def test_memory_is_hers_once():
    n = N.Night(seed=8)
    talk = D.Conversation(n, None)
    talk.open("audience", lambda *a: None)
    r0 = n.moods.regard
    got = []
    talk.cast("memory", lambda t, ch: got.append(t), "hands")
    assert got and "hands" in got[0] and n.moods.regard > r0
    assert any("floured" in m for m in talk.memory)                 # (she keeps what she sees)
    assert "hands" not in n.spells.unshown()
    tier, _line, _said = n.spells.in_scene("memory", n, "hands")
    assert tier == "plain"                                          # (already given)


def test_light_before_her_insults():
    n = N.Night(seed=9)
    talk = D.Conversation(n, None)
    talk.open("audience", lambda *a: None)
    got = []
    talk.cast("light", lambda t, ch: got.append((t, ch)))
    assert "knife" in got[0][0] and got[0][1]                       # (her answer, and the talk goes on)
    assert not n.spells.ready("light")
