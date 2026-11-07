"""Claudenites 3-D in the Timeline (ClaudeGames/claudenites, a subtree of jasonfye2015/claudenites-3d): its own suite
of rules passes here as it does on GitHub; and its window opens through the stand-in host on a scratch save folder
(the real saves are never touched, and no language model is loaded), goes from the title into Thornwick and down to a floor, draws a frame when the
machine gives it OpenGL, saves the slot, and closes."""
import importlib.util
import json
import os

import support

os.environ["CLAUDE_STANDALONE_DATA"] = str(support.scratch("standalone data"))
os.environ["CLAUDE_STANDALONE_STORAGE"] = str(support.scratch("empty Local Storage"))
support.qapp()
from claudecore import standalone as S  # noqa: E402

S.install()
support.no_model_server()                    # (the townsfolk keep to their own lines: no model is loaded in a test)
import claudenites as N  # noqa: E402

GAME = support.TIMELINE / "ClaudeGames" / "claudenites"


def test_its_own_rules():
    """The game's own tests (tests/run.py: the floors, the fights, the wands, the pack, the skills, the saves)"""
    spec = importlib.util.spec_from_file_location("claudenites_tests_run", GAME / "tests" / "run.py")
    run = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(run)
    assert run.main([]) == 0, "the game's own tests failed (see above)"


def test_the_window():
    """Opens on the title, plays slot 1 into Thornwick, goes down to floor 1, saves, and closes"""
    from PySide6.QtWidgets import QApplication
    saves = support.scratch("claudenites saves")
    N.SAVES = saves
    caught = support.catch_errors()
    desktop = S.Desktop()
    S.open_app("claudenites", desktop)
    assert support.pump(10, until=lambda: desktop.main is not None and desktop.main.isVisible()), "no window opened"
    shell = desktop.main.content
    support.pump(1.0)
    assert shell.panel_open() and shell.slot is None                     # (the title, over Thornwick)
    shell.play(0)
    support.pump(0.5)
    g = shell.view.game
    assert g.depth == 0 and not shell.panel_open()
    g.go_floor(1)
    support.pump(1.0)
    assert g.depth == 1 and g.monsters
    shell.save()
    data = json.loads((saves / "slot1.json").read_text(encoding="utf-8"))
    assert data["player"]["level"] == 1 and data["run_floor"] >= 1
    main = desktop.main
    main.request_close()
    assert support.pump(10, until=lambda: main not in desktop.windows), "it didn't close"
    assert QApplication.activeModalWidget() is None
    support.pump(0.3)
    support.no_errors(caught)


if __name__ == "__main__":
    support.main(globals())
