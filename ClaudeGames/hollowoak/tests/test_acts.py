"""The night's shape: the acts in order, her calling him on, her later scenes (every way through them), guest or meal,
what he chooses at the crown - and how dawn ends it."""
import math
import random

from hollowoak.game import acts as A
from hollowoak.game import dialogue as D
from hollowoak.game import moods as M
from hollowoak.game import night as N
from hollowoak.game import script as S
from hollowoak.game import sky as SK
from hollowoak.game import tree as T


def _calm(n):
    n.lamp.next_out = 1e9
    n.danglers.next = n.crawlers.next = 1e9
    return n


def test_the_acts_in_order_and_her_calls():
    n = _calm(N.Night(seed=1))
    a = n.acts
    assert a.act == "threshold" and "loom" in a.request
    n.sky.clock = SK.DUSK + A.CALL_AT["threshold"] + 1                      # (late, and not come to her loom)
    calls = []
    for _ in range(int(10 / 0.05)):
        n.step(0.05, N.Input())
        calls += [e for e in n.events if e[0] == "call"]
        n.events.clear()
    assert calls == [("call", "threshold")]
    a.scene_over("audience", "done", n)
    assert a.act == "gallery"
    n.sky.clock = SK.DUSK + A.CALL_AT["supper"] + 1                          # (midnight: she calls him down)
    n.step(0.05, N.Input())
    assert a.act == "supper" and ("act", "supper") in n.events and "larder" in a.request
    t = n.tree
    start, run = next((s, r) for nm, s, r in T.LANDINGS if nm == "larder")
    th = t.theta_of(start + run / 2)
    r = t.wall_r(th, t.landing_h["larder"] + 1.0) - 0.6
    n.x, n.z, n.y = math.cos(th) * r, math.sin(th) * r, t.landing_h["larder"]
    assert n.where() == "larder" and a.scene_for(n) == "supper"
    a.scene_over("supper", "guest", n)
    assert a.act == "crown" and a.scene_for(n) is None
    n.x, n.z = 0.5, 0.3
    n.y = n.web.crown.height(0.5, 0.3)
    n.on = n.web.crown
    assert a.scene_for(n) == "crown"
    a.scene_over("crown", "done", n)
    n.sky.clock = 1440 + SK.DAWN + 0.5                                       # (and the light comes)
    n.events.clear()
    n.step(0.05, N.Input())
    assert a.act == "dawn" and n.ending is not None and n.ending.name == "Dawn"
    while not n.ending.done:
        n.step(0.05, N.Input())
    assert any(e[:2] == ("ending", "line") for e in n.events)


def test_every_way_through_supper_and_the_crown():
    for scene in ("supper", "crown"):
        nodes = S.SCENES[scene]["nodes"]
        for nid, node in nodes.items():
            for c in node.get("choices", []):
                assert c[2] in nodes and all(k in M.HEARD for k in c[1])
            if "next" in node:
                assert node["next"] in nodes
        ends = set()
        for seed in range(50):
            rng = random.Random(seed)
            n = N.Night(seed=seed)
            n.moods.hunger = rng.choice((20.0, 95.0))
            talk = D.Conversation(n, None, rng=rng)
            out = []
            talk.open(scene, lambda t, ch: out.append((t, ch)))
            for _ in range(20):
                if out[-1][1] is None:
                    break
                talk.choose(rng.randrange(len(out[-1][1])), lambda t, ch: out.append((t, ch)))
            assert out[-1][1] is None
            ends.add(talk.ended)
        assert ends == ({"guest", "meal"} if scene == "supper" else {"done"}), (scene, ends)


def test_guest_or_meal_and_what_he_chooses():
    n = N.Night(seed=3)
    talk = D.Conversation(n, None)
    n.moods.hunger, n.moods.fascination, n.moods.regard = 50, 60, 30
    assert talk.supper() == "guest"
    n.moods.hunger, n.moods.fascination, n.moods.regard = 90, 20, 0
    assert talk.supper() == "meal"
    out = []
    talk.open("crown", lambda t, ch: out.append((t, ch)))
    talk.choose(1, lambda t, ch: out.append((t, ch)))                       # ("To stay. Here, with you.")
    talk.choose(0, lambda t, ch: out.append((t, ch)))                       # ("I know. I want it.")
    assert n.flags.get("stay") and out[-1][1] is None


def test_how_dawn_ends_it():
    n = N.Night(seed=4)
    a, m = n.acts, n.moods
    m.regard, m.bites = 10, 1
    assert a.decide(n) == "Cast out"
    m.bites, m.regard = 0, 70
    n.flags["stay"] = True
    assert a.decide(n) == "Bound"
    n.flags.clear()
    m.fascination, n.lies = 70, 0
    assert a.decide(n) == "The gift"
    n.lies = 1
    assert a.decide(n) == "Dawn"
    m.regard = 30
    assert a.decide(n) == "Dawn"
