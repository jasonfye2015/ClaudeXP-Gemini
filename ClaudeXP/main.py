"""ClaudeXP - a virtual Windows XP desktop that will host ClaudeAIM and friends."""
import os
import subprocess
import sys

from PySide6.QtCore import QCoreApplication, Qt, QtMsgType, qInstallMessageHandler
from PySide6.QtWidgets import QApplication

from claudexp import setup, sound, spellcheck, style
from claudexp.app import ClaudeXP

_crash_log = None


def _log_crashes():
    """If ClaudeXP ever crashes outright, logs/crash.log says where: the Python stack of every thread, and Qt's
    last serious complaint. (Kept outside data/, which Setup moves away while ClaudeXP is still running.)"""
    global _crash_log
    import faulthandler
    import time
    try:
        folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
        os.makedirs(folder, exist_ok=True)
        _crash_log = open(os.path.join(folder, "crash.log"), "a", encoding="utf-8")
        _crash_log.write(f"\n=== ClaudeXP started {time.strftime('%Y-%m-%d %H:%M:%S')} (pid {os.getpid()}) ===\n")
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
        if sys.stderr is not None:                       # (none under pythonw)
            try:
                sys.stderr.write(message + "\n")
            except (OSError, ValueError):
                pass
    qInstallMessageHandler(qt_message)
    _log_errors(folder)


def _log_errors(folder):
    """Every Python error that doesn't crash ClaudeXP - one in a Qt callback, a timer, a thread - goes to
    logs/errors.log (and the Furry Log), instead of vanishing: under pythonw there's no console to print it to."""
    import threading
    import time
    import traceback
    path = os.path.join(folder, "errors.log")

    def hook(kind, value, tb):
        text = "".join(traceback.format_exception(kind, value, tb))
        try:
            with open(path, "a", encoding="utf-8") as f:
                f.write(f"\n{time.strftime('%Y-%m-%d %H:%M:%S')} (pid {os.getpid()})\n{text}")
        except OSError:
            pass
        try:
            from claudecore.ai import llmlog
            llmlog.event("ERROR", text.strip().splitlines()[-1] + "\n" + text)
        except Exception:
            pass
        if sys.stderr is not None:
            try:
                sys.stderr.write(text)
            except (OSError, ValueError):
                pass
    sys.excepthook = hook
    threading.excepthook = lambda a: hook(a.exc_type, a.exc_value, a.exc_traceback)


def main():
    _log_crashes()
    try:
        from claudecore import relocate
        from claudexp.paths import DATA
        relocate.fix(DATA)             # the Timeline moved (e.g. onto the external SSD): saved paths follow it
    except Exception as exc:
        if sys.stderr is not None:
            sys.stderr.write(f"Relocation check failed: {exc}\n")
    try:
        from claudexp import residents_sync
        residents_sync.sync()          # in the Claude Timeline, the cast comes from Residents/
    except Exception as exc:           # never stop ClaudeXP from starting over it
        if sys.stderr is not None:
            sys.stderr.write(f"Residents sync failed: {exc}\n")
    QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)     # before the app exists, for the Flash Player's web view
    qapp = QApplication(sys.argv)
    qapp.setApplicationName("ClaudeXP")
    try:
        from claudecore import selfcheck
        selfcheck.at_start("xp")    # quick start-up self-check: logs\selfcheck.log
    except Exception:
        pass
    try:
        from claudecore import macfonts
        macfonts.apply()               # on a Mac: Mac fonts for the Windows ones
    except ImportError:
        pass
    style.apply(qapp)
    spellcheck.install(qapp)
    sound.preload()
    try:
        from claudexp import persona_style
        persona_style.apply()          # a frozen Contact Persona Style prompts the way it always did
    except Exception as exc:
        if sys.stderr is not None:
            sys.stderr.write(f"Persona style failed: {exc}\n")
    app = ClaudeXP()
    from claudexp import timeline
    app.start(recovery=timeline.format_requested())      # the Claude Timeline launcher's 'Load and Format'
    code = qapp.exec()
    if code == setup.RESTART:
        # Windows Setup is rebooting the PC: erase C: now that nothing is running, then start again.
        app.hide()
        setup.finish_reboot()
        sys.stdout.flush()
        if os.environ.get("CLAUDEXP_RESTARTED"):
            os._exit(code)            # the first ClaudeXP process is waiting to start the next one
        code = _run_again()
    # Exit right away: everything is saved as it happens, and a buddy's model may still be
    # mid-reply in a background thread, which would otherwise keep the process alive.
    sys.stdout.flush()
    os._exit(code)


def _run_again():
    """Start ClaudeXP in a fresh process (as many times as Setup reboots) and wait for it, so whatever
    launched us (Thonny, ClaudeXP.bat) still sees one program running."""
    env = dict(os.environ, CLAUDEXP_RESTARTED="1")
    script = os.path.abspath(__file__)
    while True:
        code = subprocess.call([sys.executable, script], env=env, cwd=os.path.dirname(script))
        if code != setup.RESTART:
            return code
        # (the child already did its wipe before exiting)


if __name__ == "__main__":
    main()
