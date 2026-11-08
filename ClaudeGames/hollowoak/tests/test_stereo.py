"""Sound from where it is: left and right, and the space he's in."""
import numpy as np

from hollowoak.engine.sound import RATE, Synth
from hollowoak.game import night as N


def _quiet():
    s = Synth()
    s.music_gain = 0.0
    s.set(height=0.0)
    s.render(RATE)                                 # (the wind settles)
    return s


def test_left_and_right():
    for pan, louder in ((-1.0, 0), (1.0, 1)):
        s = _quiet()
        s.play("thud", 1.0, pan)
        x = np.concatenate([s.render(1102) for _ in range(8)])
        e = np.sqrt((x ** 2).mean(axis=0))
        assert e[louder] > e[1 - louder] * 1.8, (pan, e)


def test_her_from_where_she_is():
    s = _quiet()
    s.set(her=1.0, her_pan=0.9)
    x = np.concatenate([s.render(1102) for _ in range(20)])
    e = np.sqrt((x ** 2).mean(axis=0))
    assert e[1] > e[0] * 1.3


def test_the_space_he_is_in():
    def tail(room):
        s = _quiet()
        s.set(room=room)
        for _ in range(30):
            s.reverb.run(np.zeros(1102))           # (settled into the room)
        s.play("thud", 1.0)
        x = np.concatenate([s.render(1102) for _ in range(30)])
        return np.sqrt((x[RATE // 2:] ** 2).mean())   # (what's left after half a second: the echo)
    assert tail("hollow") > tail("tunnel") * 1.3


def test_where_a_sound_is_heard():
    from hollowoak.engine.sound import heard_pan
    n = N.Night(seed=1)
    ex, ey, ez = n.eye
    rx, rz = np.cos(n.yaw), np.sin(n.yaw)
    assert heard_pan(n, (ex + rx * 3, ey, ez + rz * 3)) > 0.9          # (to his right)
    assert heard_pan(n, (ex - rx * 3, ey, ez - rz * 3)) < -0.9         # (to his left)
