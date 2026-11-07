"""What he holds: the crooked wand out before him, the lantern hung from its crook; and the fungus breathing, each
patch on its own cycle."""
import math

import numpy as np

from hollowoak.engine import held, treemesh
from hollowoak.game import night as N


def test_the_lantern_hangs_from_the_wands_crook():
    n = N.Night(seed=6)
    (grip, waxes), (ring, laxes) = held.hold(n, 0.0)
    eye = np.array(n.eye)
    parts, tip = held.wand_parts()
    assert len(parts) > 300 and abs(float(np.linalg.norm(tip)) - held.WAND_LEN) < 0.2
    crook = grip + waxes[0] * tip[0] + waxes[1] * tip[1] + waxes[2] * tip[2]
    assert np.allclose(crook, ring)                                       # (the ring is on the crook)
    assert grip[1] < eye[1] and ring[1] > grip[1]                         # (the grip low; the crook raised before him)
    f = held.flame(ring, laxes)
    assert f[1] < ring[1] - 0.05                                           # (the lantern hangs below the crook)
    look = np.array((math.sin(n.yaw), 0, -math.cos(n.yaw)))
    assert float(np.dot(f - eye, look)) > 0.3                              # (out in front of him)


def test_a_shake_swings_the_lantern():
    n = N.Night(seed=7)
    (_g, _w), (_r, still) = held.hold(n, 0.0)
    n.lamp.shake()
    n.lamp.step(0.2)
    (_g, _w), (_r, shaken) = held.hold(n, 0.0)
    tilt = math.degrees(math.acos(max(-1.0, min(1.0, float(np.dot(still[1], shaken[1]))))))
    assert tilt > 8


def test_each_patch_of_fungus_breathes_on_its_own():
    cycles = {treemesh.breath(k) for k in range(17)}
    assert len(cycles) == 17                                               # (no two alike)
    levels = [treemesh.glow_level(t * 0.5, 9.0, 1.0) for t in range(40)]
    assert min(levels) < 0.25 and max(levels) > 0.95                       # (fading almost out, and growing back)
