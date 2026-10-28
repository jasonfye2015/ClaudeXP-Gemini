"""The screen savers, offscreen, on a scratch data folder: every one of XP's runs and paints for a few seconds of its
own time, and the Claude Entertainment System plays each NES game in turn (on a fake clock, so five games' minutes
take no time at all). The NES games need their sprite sheets in Local Storage; without them they're skipped."""
import sys

import support

sys.path.insert(0, str(support.XP))
support.qapp()
import claudexp.paths as P  # noqa: E402

P.DATA = support.scratch("xp data")                       # (before anything reads the display settings)
from claudexp import ces, screensaver  # noqa: E402

NES = [name for name, _module, _title in ces.GAMES]


def _exercise(cls, seconds=4):
    w = cls()
    w.resize(640, 480)
    w.show()
    for i in range(int(seconds * w.FPS)):
        w.t += 1 / w.FPS
        w.step()
        if i % w.FPS == 0:
            w.grab()                                    # (paints it)
    w.grab()
    w.close()
    w.deleteLater()


def _make(name, cls):
    def test():
        if name in NES and not ces.available(name):
            support.skip("its sprite sheets aren't in Local Storage")
        caught = support.catch_errors()
        _exercise(cls)
        support.no_errors(caught)
    test.__doc__ = f"{name} runs and paints"
    return test


for _name, _cls in screensaver.SAVERS.items():
    if _cls is not None and _name != "Claude Entertainment System":
        globals()["test_" + "".join(ch if ch.isalnum() else "_" for ch in _name.lower())] = _make(_name, _cls)


class _Clock:
    def __init__(self):
        self.now = 1000.0

    def monotonic(self):
        return self.now


def test_claude_entertainment_system():
    """The Claude Entertainment System: a title card, then each game for its minutes, in order, then round again"""
    playable = [n for n in NES if ces.available(n)]
    if not playable:
        support.skip("no NES sprite sheets in Local Storage")
    caught = support.catch_errors()
    clock = _Clock()
    real_time, ces.time = ces.time, clock
    try:
        w = screensaver.SAVERS["Claude Entertainment System"]()
        w.resize(640, 480)
        w.show()
        for name in playable + playable[:1]:
            assert w.name == name and w.card, f"expected {name}'s title card, got {w.name}"
            w.grab()
            clock.now += ces.CARD + 0.1
            w.step()
            assert isinstance(w.game, screensaver.SAVERS[name]), f"{name} didn't start"
            for _i in range(30):
                w.game.step()
            w.grab()
            clock.now += int(w.cfg["minutes"][name]) * 60 + 1
            w.step()
        w.close()
    finally:
        ces.time = real_time
    support.no_errors(caught)


def test_ces_is_the_default_everywhere():
    """The Claude Entertainment System is the default screen saver on all three computers"""
    assert screensaver.DEFAULTS["saver"] == "Claude Entertainment System", screensaver.DEFAULTS["saver"]
    for path in (support.W7 / "claude7" / "display.py", support.W11 / "claude11" / "display.py"):
        assert "Claude Entertainment System" in path.read_text(encoding="utf-8"), f"not the default in {path.name}"


if __name__ == "__main__":
    support.main(globals())
