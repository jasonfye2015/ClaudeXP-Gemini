"""The Hollow Oak in the Timeline (ClaudeGames/hollowoak, a subtree of jasonfye2015/the-hollow-oak): its own suite of
rules passes here as it does on GitHub; and its window opens through the stand-in host on a scratch save folder (the
real saves are never touched), shows its title, begins the night in the root tunnel, walks a little way in, pauses,
goes back to the title, and closes."""
import importlib.util
import os

import support

os.environ["CLAUDE_STANDALONE_DATA"] = str(support.scratch("standalone data"))
os.environ["CLAUDE_STANDALONE_STORAGE"] = str(support.scratch("empty Local Storage"))
support.qapp()
from claudecore import standalone as S  # noqa: E402

S.install()
import hollowoak as O  # noqa: E402

GAME = support.TIMELINE / "ClaudeGames" / "hollowoak"


def test_its_own_rules():
    """The game's own tests (tests/run.py: the tree's shape, its ledge to the crown, the way in, the walls, the clock)"""
    spec = importlib.util.spec_from_file_location("hollowoak_tests_run", GAME / "tests" / "run.py")
    run = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(run)
    assert run.main([]) == 0, "the game's own tests failed (see above)"


def test_the_window():
    """Opens on the title, begins the night out in the glade at dusk, walks toward the oak, pauses, goes back to the title, closes"""
    O.SAVES = support.scratch("hollowoak saves")
    caught = support.catch_errors()
    desktop = S.Desktop()
    S.open_app("hollowoak", desktop)
    assert support.pump(10, until=lambda: desktop.main is not None and desktop.main.isVisible()), "no window opened"
    shell = desktop.main.content
    support.pump(1.0)
    assert shell.panel_open() and not shell.view.playing                     # (the title, over the hollow)
    shell.begin()
    support.pump(0.3)
    view = shell.view
    n = view.night
    assert view.playing and not shell.panel_open() and n.where() == "outside"           # (the walk to the oak)
    view.inp.yaw, view.inp.forward = n.yaw, 1.0
    for _ in range(20):
        n.step(0.05, view.inp)
    assert n.where() in ("outside", "tunnel")
    shell.pause()
    support.pump(0.2)
    assert shell.panel_open()
    shell.show_title()
    support.pump(0.2)
    assert shell.panel_open() and not view.playing
    if view.renderer is None and view.gl_error is None:
        support.pump(1.0)
    assert view.gl_error is None, view.gl_error
    O.shutdown()
    desktop.main.close()
    support.pump(0.3)
    assert not caught, caught
