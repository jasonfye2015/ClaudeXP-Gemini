"""The launcher's APPS: Soul and Song, ClaudeRPG and the two code studios open and close on their own through the
stand-in host (claudecore.standalone), on scratch folders and an empty Local Storage; Kithylin AI and Soul and Song
run their own engine there, not a computer's; each runs once (started again, the one open comes forward); and the
APPS window starts each with the right command - or brings forward the one already open - refusing the ones that
share files with a computer while one runs."""
import os
import subprocess
import sys
import time

import support

os.environ["CLAUDE_STANDALONE_DATA"] = str(support.scratch("standalone data"))
os.environ["CLAUDE_STANDALONE_STORAGE"] = str(support.scratch("empty Local Storage"))
os.environ["KITHYLINAI_DATA"] = str(support.scratch("Kithylin AI data"))
support.qapp()
from claudecore import standalone as S  # noqa: E402

S.install()


def _open_and_close(key):
    from PySide6.QtWidgets import QApplication
    caught = support.catch_errors()
    desktop = S.Desktop()
    S.open_app(key, desktop)
    assert support.pump(10, until=lambda: desktop.main is not None and desktop.main.isVisible()), "no window opened"
    main = desktop.main
    support.pump(0.5)
    asked = []
    support.pump(0.1)
    main.request_close()

    def gone():
        modal = QApplication.activeModalWidget()
        if modal is not None:                                    # (closing it untouched: nothing to ask)
            asked.append(modal.windowTitle())
            modal.reject()
        return main not in desktop.windows
    assert support.pump(10, until=gone), "it didn't close"
    support.pump(0.5)
    assert not asked, f"closing it untouched asked something: {asked}"
    support.no_errors(caught)


def test_soulsong():
    """Soul and Song opens and closes on its own"""
    _open_and_close("soulsong")


def test_rpg():
    """ClaudeRPG opens and closes on its own"""
    _open_and_close("rpg")


def test_pystudio():
    """Copilot Python Studio opens and closes on its own"""
    _open_and_close("pystudio")


def test_qbstudio():
    """Claude QBasic Studio opens and closes on its own"""
    _open_and_close("qbstudio")


def test_their_own_engine():
    """On their own, Kithylin AI and Soul and Song run an engine of their own; inside a computer they share its"""
    from claudecore import host
    from kithylinai.paths import hosted
    assert not hosted(), "the stand-in host was taken for a computer"
    real = host._host
    try:
        host._host = type("AComputer", (host.Host,), {"data_dir": lambda self: support.scratch("pc")})()
        assert hosted(), "a computer's host wasn't recognised"
    finally:
        host._host = real


def test_settings_live_in_their_own_folder():
    """The code studios' model settings on their own are kept apart from every computer's"""
    from claudecore.ai import ai_models
    assert ai_models.CONFIG.parent == S.DATA, ai_models.CONFIG


def test_check_from_the_command_line():
    """python -m claudecore.standalone qbstudio --check opens it and closes it again"""
    env = dict(os.environ)
    env.pop("TIMELINE_TEST_RUNNER", None)
    done = subprocess.run([sys.executable, "-m", "claudecore.standalone", "qbstudio", "--check"],
                          cwd=str(support.CORE), env=env, capture_output=True, text=True, timeout=120)
    assert done.returncode == 0 and "ok" in done.stdout, (done.returncode, done.stdout[-500:], done.stderr[-1500:])


LISTENER = ("import sys; sys.path.insert(0, {core!r}); from PySide6.QtCore import QCoreApplication, QTimer; "
            "from claudecore import single; app = QCoreApplication([]); "
            "s = single.listen({key!r}, lambda: (print('shown', flush=True), QTimer.singleShot(1000, app.quit))); "
            "print('listening' if s else 'no', flush=True); QTimer.singleShot(20000, app.quit); app.exec()")


POPEN = subprocess.Popen                  # (the real one: the APPS window's test stands one in for it)


def _listener(key):
    """A program that's open - in a process of its own, as it really would be: it says when it's asked to come
    forward (and stops a second later)."""
    env = dict(os.environ)
    env.pop("TIMELINE_TEST_RUNNER", None)
    p = POPEN([sys.executable, "-c", LISTENER.format(core=str(support.CORE), key=key)], env=env,
              stdout=subprocess.PIPE, text=True)
    assert p.stdout.readline().strip() == "listening", "the stand-in program didn't listen"
    return p


def test_one_copy_at_a_time():
    """One copy at a time: the one running listens, and a second start asks it to come forward (from the command
    line, the second start just stops); a window comes back out of hiding, or the program's own show_again does"""
    from PySide6.QtWidgets import QWidget
    from claudecore import single
    key = f"selftest-{os.getpid()}"
    assert not single.running(key) and not single.ask_to_show(key), "something was listening already"
    other = _listener(key)
    try:
        assert single.running(key), "it isn't listening"
        assert single.ask_to_show(key), "it wasn't there to ask"
        assert "shown" in other.communicate(timeout=20)[0], "it wasn't asked to come forward"
    finally:
        if other.poll() is None:
            other.kill()
    assert not single.running(key), "it was still listening after it stopped"
    win = QWidget()
    win.show()
    win.hide()                                                   # (closed to the notification area, say)
    single.come_forward(win)
    assert win.isVisible(), "the window didn't come back"

    class Content:
        calls = 0

        def show_again(self):
            self.calls += 1
    content = Content()
    single.come_forward(win, content)
    assert content.calls == 1, "the program's own show_again wasn't used"
    win.close()
    env = dict(os.environ)
    env.pop("TIMELINE_TEST_RUNNER", None)
    start = [sys.executable, "-m", "claudecore.standalone", "qbstudio"]
    first = subprocess.Popen(start, cwd=str(support.CORE), env=env, stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)
    try:
        deadline = time.monotonic() + 60
        while not single.running("qbstudio") and first.poll() is None and time.monotonic() < deadline:
            time.sleep(0.2)
        assert single.running("qbstudio"), f"the first copy didn't start listening ({first.poll()})"
        second = subprocess.run(start, cwd=str(support.CORE), env=env, capture_output=True, text=True, timeout=60)
        assert second.returncode == 0, (second.returncode, second.stderr[-1000:])
        assert first.poll() is None, "the first copy stopped"
    finally:
        first.kill()
        first.wait(10)


def test_the_apps_window():
    """The launcher's APPS window: five apps with icons, each started the right way, once - and one already open
    brought forward instead"""
    sys.path.insert(0, str(support.TIMELINE / "ClaudeLauncher"))
    from systec import ui
    ui.Systec._first_run = lambda self: None
    ui.Systec._start_selfcheck = lambda self: None
    started = []

    class Running:
        def poll(self):
            return None
    real_popen = ui.subprocess.Popen
    ui.subprocess.Popen = lambda args, **kw: started.append((args[1:], os.path.basename(kw["cwd"]))) or Running()
    try:
        w = ui.Systec()
        w.apps_window()
        a = w._apps
        support.pump(0.3)
        assert list(a.tiles) == ["kithylinai", "soulsong", "rpg", "pystudio", "qbstudio"], list(a.tiles)
        assert all(not t.icon().isNull() for t in a.tiles.values()), "an app has no icon"
        a.start("qbstudio")
        a.start("kithylinai")
        a.start("qbstudio")
        assert "already open" in a.status.text(), a.status.text()
        assert started == [(["-m", "claudecore.standalone", "qbstudio"], "ClaudeCore"),
                           (["-m", "kithylinai"], "ClaudeApps")], started
        w.process, w.running = Running(), ui.SYSTEMS[0]            # (a computer is running)
        a.start("soulsong")
        assert "Not while" in a.status.text() and len(started) == 2, a.status.text()
        a.start("pystudio")                                       # (the code studios share nothing with it)
        assert len(started) == 3, started
        s = ui.AppsSettingsDialog(a)
        assert s.model.count() >= 1 and s.engine.itemData(0) == "" and s.context.currentData() == 16384
        w.process = None
        other = _listener("soulsong")                             # (one open already, out of sight)
        try:
            a.start("soulsong")
            assert a.tiles["soulsong"].isChecked(), "its tile doesn't say it's open"
            assert "shown" in other.communicate(timeout=20)[0], "the one open wasn't asked to come forward"
            assert "in front now" in a.status.text() and len(started) == 3, (a.status.text(), started)
        finally:
            if other.poll() is None:
                other.kill()
        a.close()
        w.close()
    finally:
        ui.subprocess.Popen = real_popen


if __name__ == "__main__":
    support.main(globals())
