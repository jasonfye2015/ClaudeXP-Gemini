"""The score, and Supper's last moments: the music follows the night and her moods; she leans in, and speaks."""
import numpy as np

from hollowoak.engine.music import CODAS, Music
from hollowoak.game import death as Dh
from hollowoak.game import night as N

R = 22050


def _play(m, secs):
    return np.concatenate([m.render(R // 20) for _ in range(int(secs * 20))])


def test_every_mode_plays_cleanly():
    for mode in ("explore", "scene", "crown", "silence") + tuple("coda:" + c for c in CODAS):
        m = Music(R, seed=1)
        m.set(mode, venom=True, hunger=90)
        x = _play(m, 8)
        assert np.isfinite(x).all() and np.abs(x).max() < 1.5


def test_the_waltz_follows_her_moods():
    def notes(**mood):
        m = Music(R, seed=2)
        m.set("scene", **mood)
        count = 0
        for _ in range(int(30 * 20)):
            before = len(m.notes)
            m.render(R // 20)
            count += max(0, len(m.notes) - before)
        return count
    calm = notes(patience=90, suspicion=10, fascination=50)
    assert notes(patience=5, suspicion=10, fascination=50) < calm             # (patience thin: notes dropped)
    assert notes(patience=90, suspicion=95, fascination=50) > calm            # (suspicion: a second voice)


def test_hunger_and_silence():
    m = Music(R, seed=3)
    m.set("explore", hunger=10)
    _play(m, 3)
    assert not any(n[0] is m._thump for n in m.notes)
    m.set("explore", hunger=95)
    _play(m, 3)
    assert any(n[0] is m._thump for n in m.notes)                            # (her hunger: a heartbeat under it)
    m.set("silence")
    tail = _play(m, 12)[-R:]
    assert np.abs(tail).max() < 0.01                                          # (Supper ends in silence)


def test_her_last_words_and_her_lean():
    n = N.Night(seed=31)
    n.collapse("bite")
    d = n.dying
    assert Dh.last_words(n) == "Only a little bite. Only a little more. Sleep."
    assert "keep you, every time" in Dh.last_words(n, {"met": 2})
    assert "truth of you" in Dh.last_words(n, {"met": 2}, lies=1)
    n.moods.regard = 70
    assert "didn't want it to be you" in Dh.last_words(n, {"met": 2}, lies=1)
    d.her_line = Dh.last_words(n)
    seen = []
    inp = N.Input()
    while not d.done:
        n.step(0.05, inp)
        seen += n.events
        n.events.clear()
    assert ("death", "line", d.her_line) in seen
    assert d.her_at is not None and n.her.staged is not None                  # (she came down to him)
