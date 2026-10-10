"""ClaudeXP - a virtual Windows XP desktop that will host ClaudeAIM and friends."""
import os
import subprocess
import sys

from PySide6.QtCore import QCoreApplication, Qt
from PySide6.QtWidgets import QApplication

from claudexp import setup, sound, spellcheck, style
from claudexp.app import ClaudeXP


def main():
    QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)     # before the app exists, for the Flash Player's web view
    qapp = QApplication(sys.argv)
    qapp.setApplicationName("ClaudeXP")
    style.apply(qapp)
    spellcheck.install(qapp)
    sound.preload()
    app = ClaudeXP()
    app.start()
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
