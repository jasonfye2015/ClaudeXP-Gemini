"""The fog: it lies low and thins as the tree climbs, it hangs inside the hollow (never in the wood), and it drifts."""
import math

from hollowoak.engine import fogfx
from hollowoak.game import tree as T


def test_the_fog_lies_low_and_inside():
    t = T.Tree()
    ws = fogfx.wisps(t)
    low = [w for w in ws if w["y"] < 3]
    assert len(low) > len(ws) / 2                                   # (most of it pooled low)
    assert all(0 < y < 2.0 and thick > 0 for y, thick in fogfx.LAYERS)
    assert [thick for _y, thick in fogfx.LAYERS] == sorted((thick for _y, thick in fogfx.LAYERS), reverse=True)
    for w in ws:
        x, y, z = fogfx.wisp_at(w, 0.0)
        a = math.atan2(z, x)
        assert math.hypot(x, z) < t.wall_r(a, w["y"]) or t.in_tunnel(x, z), w   # (in the air, not in the wood)


def test_the_fog_drifts():
    w = next(w for w in fogfx.wisps(T.Tree()) if w["speed"] and w["r"] > 2.0)
    a, b = fogfx.wisp_at(w, 0.0), fogfx.wisp_at(w, 10.0)
    assert 0.05 < math.dist(a, b) < 1.5                              # (slowly: barely moving air)
