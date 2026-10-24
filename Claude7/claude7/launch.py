"""Starting Claude7: the compatibility layer first, then the residents, then Qt and the main window. Setup's
restarts come back through here (exit code 3 starts a fresh process, like ClaudeXP)."""
import os
import subprocess
import sys

from PySide6.QtCore import QCoreApplication, Qt, QtMsgType, qInstallMessageHandler
from PySide6.QtWidgets import QApplication

from .paths import DATA, ROOT

_crash_log = None


def _log_crashes():
    global _crash_log
    import faulthandler
    import time
    try:
        folder = ROOT / "logs"
        folder.mkdir(parents=True, exist_ok=True)
        _crash_log = open(folder / "crash.log", "a", encoding="utf-8")
        _crash_log.write(f"\n=== Claude7 started {time.strftime('%Y-%m-%d %H:%M:%S')} (pid {os.getpid()}) ===\n")
        _crash_log.flush()
        faulthandler.enable(file=_crash_log, all_threads=True)
    except OSError:
        return

    def qt_message(kind, context, message):
        if kind in (QtMsgType.QtCriticalMsg, QtMsgType.QtFatalMsg):
            try:
                _crash_log.write(f"{time.strftime('%H:%M:%S')} Qt {kind.name}: {message}\n")
                _crash_log.flush()
            except (OSError, ValueError):
                pass
        if sys.stderr is not None:
            try:
                sys.stderr.write(message + "\n")
            except (OSError, ValueError):
                pass
    qInstallMessageHandler(qt_message)


def _warn(text):
    if sys.stderr is not None:
        sys.stderr.write(text + "\n")


def main():
    _log_crashes()
    from . import xpcompat
    xpcompat.install()
    xpcompat.program_files_ready()
    try:
        from claudecore import relocate
        relocate.fix(DATA)
    except Exception as exc:
        _warn(f"Relocation check failed: {exc}")
    try:
        from . import residents_sync
        residents_sync.sync()
    except Exception as exc:
        _warn(f"Residents sync failed: {exc}")
    QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
    qapp = QApplication(sys.argv)
    qapp.setApplicationName("Claude7")
    try:
        from claudecore import selfcheck
        selfcheck.at_start("w7")    # quick start-up self-check: logs\selfcheck.log
    except Exception:
        pass
    try:
        from claudecore import macfonts
        macfonts.apply()               # on a Mac: Mac fonts for the Windows ones
    except ImportError:
        pass
    from . import setup, sound, style
    style.apply(qapp)
    try:
        from claudexp import spellcheck
        spellcheck.install(qapp)
    except Exception as exc:
        _warn(f"Spell check failed: {exc}")
    sound.preload()
    from . import programs  # noqa: F401  (installs Claude7's registry)
    from .app import Claude7
    from . import timeline
    app = Claude7()
    if timeline.format_requested():
        app.show()
        app._install_windows()
    else:
        app.start()
    code = qapp.exec()
    if code == setup.RESTART:
        app.hide()
        setup.finish_reboot()
        sys.stdout.flush()
        if os.environ.get("CLAUDE7_RESTARTED"):
            os._exit(code)
        code = _run_again()
    sys.stdout.flush()
    os._exit(code)


def _run_again():
    env = dict(os.environ, CLAUDE7_RESTARTED="1")
    script = str(ROOT / "main.py")
    while True:
        code = subprocess.call([sys.executable, script], env=env, cwd=str(ROOT))
        if code != setup.RESTART:
            return code
