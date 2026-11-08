"""Her venom: it stays; his hands shake; his words slur; he sees through her eyes; the antidote, drunk or given."""
import math
import random

from hollowoak.game import dialogue as D
from hollowoak.game import night as N
from hollowoak.game import notes
from hollowoak.game import venom as V


def _step(n, secs, dt=0.05):
    seen = []
    inp = N.Input()
    inp.yaw, inp.pitch = n.yaw, n.pitch
    for _ in range(int(secs / dt)):
        n.step(dt, inp)
        seen += n.events
        n.events.clear()
    return seen


def _calm(n):
    n.lamp.next_out = 1e9
    n.danglers.next = n.crawlers.next = 1e9
    n.moods.hunger = 0.0
    n.her.at = lambda *a: (0.0, 40.0, 0.0)                         # (far off, up in the dark)


def test_her_bite_stays_and_a_second_ends_it():
    n = N.Night(seed=1)
    _calm(n)
    assert not n.bitten() and n.venom.active and n.dying is None
    assert ("venom", "in") in n.events
    _step(n, 30.0)
    assert n.venom.active and n.body.poison >= V.FLOOR             # (it doesn't wear off)
    assert n.bitten() and n.dying is not None and n.dying.cause == "bite"


def test_through_her_eyes():
    n = N.Night(seed=2)
    _calm(n)
    n.bitten()
    x0, z0 = n.x, n.z
    seen = _step(n, V.FIRST_VISION + 1.0)
    assert ("vision", "larder") in seen and n.venom.vision is not None
    assert n.camera is not None and all(math.isfinite(c) for c in n.camera[0])
    inp = N.Input()
    inp.forward = 1.0
    n.step(0.05, inp)
    assert (n.x, n.z) == (x0, z0) or math.dist((n.x, n.z), (x0, z0)) < 1e-6    # (he stands still, seeing)
    seen = _step(n, V.VISION_FOR)
    assert ("vision_end", "larder") in seen and n.camera is None and n.venom.revealed
    assert notes.unlock_for(("vision", "larder")) == ["antidote"]
    for vid in V.ORDER:
        assert V.VISIONS[vid][1] in notes.PAGES


def test_the_phial_hidden_then_found_and_drunk():
    n = N.Night(seed=3)
    _calm(n)
    ax, ay, az = n.finds.spots["antidote"]
    th = math.atan2(az, ax)
    sx, sz = ax - math.cos(th) * 0.9, az - math.sin(th) * 0.9       # (stand before it, look down at it)
    n.x, n.z = sx, sz
    n.y = n.floor_at(sx, sz, ay + 0.3)
    ex, ey, ez = n.eye
    n.yaw = math.atan2(ax - ex, -(az - ez))
    n.pitch = math.atan2(ay - ey, math.hypot(ax - ex, az - ez))
    assert n.finds.near(n) != "antidote"                            # (in the dark: he doesn't know it's there)
    n.venom.seen.append("larder")
    assert n.finds.near(n) == "antidote"
    n.examine()
    assert "antidote" in n.pack
    assert not n.drink()                                            # (nothing to cure yet)
    n.bitten()
    n.her.at = lambda *a: n.eye                                     # (and she's watching)
    assert n.drink() and not n.venom.active and n.venom.cured == "drunk"
    assert n.flags.get("stole_antidote") and "antidote" not in n.pack
    assert not n.bitten() and n.dying is None                       # (out of him: a bite is the first again)


def test_shaking_hands():
    n = N.Night(seed=4)
    n.venom.start()
    n.venom.rng = random.Random(0)
    missed = 0
    for _ in range(60):
        n.spells.rest = {k: 0.0 for k in n.spells.rest}
        if n.cast("warmth")[0][2] == "missed":
            missed += 1
    assert 5 < missed < 35


def test_slurred():
    rng = random.Random(5)
    said = "I came because I wanted to see something nobody else has seen, and this is it"
    outs = {V.slur(said, rng) for _ in range(10)}
    assert len(outs) > 5 and all(o != said for o in outs)


def test_she_chooses_to_give_it():
    for regard, given in ((70, True), (20, False)):
        n = N.Night(seed=6)
        n.bitten()
        n.moods.regard, n.moods.suspicion = regard, 20
        talk = D.Conversation(n, None)
        talk.open("audience", lambda *a: None)
        got = []
        talk.ask_cure(lambda t, ch: got.append(t))
        assert got and talk.flags["asked_cure"]
        assert n.venom.active is (not given)
        assert n.flags.get("given_antidote", False) is given
