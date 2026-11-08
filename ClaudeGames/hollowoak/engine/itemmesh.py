"""The things he carries, as small objects: in his left hand, or put down on the wood. Plain numpy triangles, about an
origin with axes (forward, up, right) - the same little boxes and blobs her guests' keepsakes are made of.

    build(item, origin, axes, now, state) -> [(position, normal, colour)]
"""
import math

import numpy as np

from . import cocoonmesh as C


def build(item, origin, axes, now, state=None, scale=1.0):
    state = state or {}
    f, up, r = (np.asarray(a, float) for a in axes)
    o = np.asarray(origin, float)
    out = []
    if scale != 1.0:                                              # (made at its size, then shrunk about its origin)
        made = build(item, (0.0, 0.0, 0.0), axes, now, state)
        return [(*(np.array(v[:3]) * scale + o), *v[3:]) for v in made]
    if item == "ring":
        for k in range(12):
            a = k / 12 * math.tau
            d = f * math.cos(a) + r * math.sin(a)
            C._box(out, o + d * 0.028 + up * 0.004, (0.009, 0.004, 0.005), (np.cross(up, d), up, d), (0.78, 0.79, 0.84))
    elif item == "mouse":
        still = state.get("still")
        kick = 0.0 if still else math.sin(now * 17.0)
        body_up = up if not still else -up                              # (dead: on its back)
        C._blob(out, o + up * 0.03, (0.045, 0.028, 0.03), (f, body_up, r), (0.3, 0.27, 0.25), seg=6)
        C._blob(out, o + f * 0.05 + up * 0.035, (0.022, 0.018, 0.018), (f, body_up, r), (0.32, 0.28, 0.26), seg=5)
        for s in (-1, 1):                                               # (ears)
            C._blob(out, o + f * 0.058 + up * 0.052 + r * s * 0.012, (0.006, 0.009, 0.009), (f, up, r),
                    (0.55, 0.4, 0.4), seg=4)
        for k in range(6):                                              # (its tail, flicking - or not)
            t = 0.05 + k * 0.022
            wag = 0.012 * kick * (k / 5) + (0.0 if not still else 0.004 * k)
            C._box(out, o - f * t + r * wag + up * 0.015, (0.012, 0.003, 0.003), (f, up, r), (0.5, 0.38, 0.36))
        for s in (-1, 1):                                               # (its legs, kicking)
            for fb in (-1, 1):
                C._box(out, o + f * fb * 0.022 + r * s * 0.026 + up * (0.012 + 0.008 * kick * s * fb),
                       (0.005, 0.012, 0.004), (f, up, r), (0.5, 0.38, 0.36))
    elif item == "moths":
        left = state.get("moths", 6)
        for k in range(max(0, left)):                                   # (beating about his cupped fingers)
            a = now * (1.3 + 0.2 * k) + k * 2.1
            c = o + up * (0.05 + 0.025 * math.sin(a * 1.7)) + f * 0.035 * math.cos(a) + r * 0.035 * math.sin(a)
            flap = 0.9 * math.sin(now * 38 + k * 1.3)
            for s in (-1, 1):
                w = r * math.cos(flap) * s + up * math.sin(flap) * 0.6
                w = w / (np.linalg.norm(w) or 1)
                C._box(out, c + w * 0.009, (0.009, 0.0012, 0.006), (w, np.cross(f, w), f), (0.62, 0.58, 0.5))
            C._box(out, c, (0.002, 0.002, 0.006), (r, up, f), (0.3, 0.26, 0.2))
    elif item == "honey":
        for i in range(-1, 2):
            for j in range(0, 2):
                c = o + r * (i * 0.034 + (0.017 if j else 0)) + up * (0.018 + j * 0.03)
                C._box(out, c, (0.016, 0.015, 0.012), (r, up, f), (0.78, 0.48, 0.09))
    elif item == "string":
        for k in range(10):                                             # (a curl of gut string, and its peg)
            a = k / 10 * math.tau * 1.4
            c = o + up * 0.008 + f * 0.03 * math.cos(a) + r * 0.03 * math.sin(a)
            d = -f * math.sin(a) + r * math.cos(a)
            C._box(out, c, (0.012, 0.0015, 0.0015), (d, up, np.cross(d, up)), (0.82, 0.76, 0.6))
        C._box(out, o + f * 0.04 + up * 0.01, (0.006, 0.006, 0.02), (f, up, r), (0.35, 0.2, 0.1))
    elif item == "journal":
        C._box(out, o + up * 0.012, (0.05, 0.012, 0.038), (f, up, r), (0.93, 0.89, 0.78))         # (the pages)
        C._box(out, o + up * 0.026, (0.053, 0.003, 0.041), (f, up, r), (0.32, 0.17, 0.09))        # (the covers)
        C._box(out, o - up * 0.001, (0.053, 0.003, 0.041), (f, up, r), (0.32, 0.17, 0.09))
        C._box(out, o + up * 0.012 - r * 0.04, (0.053, 0.015, 0.004), (f, up, r), (0.28, 0.14, 0.07))
    elif item == "eye":
        C._blob(out, o + up * 0.03, (0.026, 0.026, 0.026), (f, up, r), (0.86, 0.84, 0.8), seg=8)
        C._blob(out, o + up * 0.052, (0.013, 0.006, 0.013), (f, up, r), (0.34, 0.22, 0.12), seg=6)  # (iris: looking up at him)
        C._blob(out, o + up * 0.057, (0.006, 0.003, 0.006), (f, up, r), (0.03, 0.02, 0.02), seg=5)  # (pupil)
        for k in range(4):                                       # (what held it in, red)
            a = k * 1.6
            C._box(out, o + up * 0.022 - f * (0.026 + 0.01 * k) + r * 0.006 * math.sin(a),
                   (0.008, 0.0025, 0.0025), (f, up, r), (0.45, 0.04, 0.04))
        C._blob(out, o + up * 0.008, (0.04, 0.004, 0.034), (f, up, r), (0.38, 0.02, 0.02), seg=6)
    elif item == "antidote":
        C._blob(out, o + up * 0.035, (0.022, 0.035, 0.022), (f, up, r), (0.25, 0.8, 0.32), seg=7)
        C._box(out, o + up * 0.078, (0.007, 0.012, 0.007), (f, up, r), (0.25, 0.75, 0.3))
        C._box(out, o + up * 0.094, (0.009, 0.006, 0.009), (f, up, r), (0.42, 0.28, 0.16))
    return out


def held_at(night, now, centred=0.0, lift=0.0):
    """His left hand, held low on the left, palm up, cupping what he carries: -> (wrist, hand axes), (palm, item axes)."""
    yaw, pitch = night.yaw, night.pitch
    F = np.array((math.sin(yaw) * math.cos(pitch), math.sin(pitch), -math.cos(yaw) * math.cos(pitch)))
    R = np.array((math.cos(yaw), 0.0, math.sin(yaw)))
    U = np.cross(R, F)
    eye = np.array(night.eye)
    bob = 0.008 * math.sin(night.moved * 2.8 + 1.0)
    wrist = eye - R * (0.27 - centred) - U * (0.24 + bob - lift) + F * (0.42 - 0.08 * lift / 0.12 if lift else 0.42)
    x = F * 0.55 + R * 0.75 + U * 0.08                         # (fingers in across him, a little forward)
    x /= np.linalg.norm(x)
    y = -U + F * 0.9                                            # (the back of his hand down and away: palm up, to him)
    y = y - x * float(np.dot(y, x))
    y /= np.linalg.norm(y)
    z = np.cross(x, y)
    palm = wrist + x * 0.06 - y * 0.014
    up = -y                                                     # (what he holds sits on his palm)
    fwd = x
    side = np.cross(fwd, up)
    return (wrist, (x, y, z)), (palm, (fwd, up, side))
