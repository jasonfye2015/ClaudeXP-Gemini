"""The fog in the Hollow Oak, as things to draw: low layers of it lying over the floor of the hollow, and wisps of mist
hanging in the air - thick low down, thinner as the tree climbs - turning slowly round the hollow on air that barely
moves. (The fog in the light itself - everything fading with distance, the dark pooled low - is the renderer's.)

    LAYERS                          the ground fog: (height, how thick)
    wisps(tree, n, seed)            -> [dict]: where each wisp hangs and how it drifts
    wisp_at(w, t)                   -> its position at time t (seconds)
Plain Python: the tests can look at it."""
import math
import random

from ..game import tree as T

LAYERS = ((0.12, 0.34), (0.38, 0.28), (0.72, 0.2), (1.15, 0.12), (1.7, 0.06))


def wisps(tree, n=56, seed=7):
    rng = random.Random(seed)
    out = []
    for k in range(n):
        y = min(T.TOP - 3.0, rng.expovariate(1 / 4.5))          # (most of them low; a few far up)
        a = rng.uniform(0, math.tau)
        r = math.sqrt(rng.random()) * (tree.base_r(a, y) - 1.4)
        out.append({"r": r, "a": a, "y": y, "size": rng.uniform(1.6, 3.6) * (1.25 if y < 2 else 1.0),
                    "speed": rng.uniform(0.006, 0.02) * rng.choice((-1, 1)), "bob": rng.uniform(0, math.tau),
                    "alpha": rng.uniform(0.12, 0.26) * (1.0 if y < 6 else 0.7), "seed": rng.random()})
    for k in range(9):                                      # (and low along the root tunnel, so it runs on into the hollow)
        along = -0.8 + k * (T.TUNNEL_LEN - 0.5) / 8
        x, z = tree.tunnel_point(along, rng.uniform(-0.3, 0.3))
        out.append({"r": math.hypot(x, z), "a": math.atan2(z, x), "y": rng.uniform(0.2, 0.45), "size": rng.uniform(0.9, 1.3),
                    "speed": 0.0, "bob": rng.uniform(0, math.tau), "alpha": rng.uniform(0.16, 0.26), "seed": rng.random()})
    return out


def wisp_at(w, t):
    a = w["a"] + w["speed"] * t
    return (math.cos(a) * w["r"], w["y"] + 0.18 * math.sin(t * 0.07 + w["bob"]), math.sin(a) * w["r"])
