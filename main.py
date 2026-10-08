"""ClaudeXP - a virtual Windows XP desktop that will host ClaudeAIM and friends."""
import os
import sys

from PySide6.QtWidgets import QApplication

from claudexp import sound, style
from claudexp.app import ClaudeXP


def main():
    qapp = QApplication(sys.argv)
    qapp.setApplicationName("ClaudeXP")
    style.apply(qapp)
    sound.preload()
    app = ClaudeXP()
    app.start()
    code = qapp.exec()
    # Exit right away: everything is saved as it happens, and a buddy's model may still be
    # mid-reply in a background thread, which would otherwise keep the process alive.
    sys.stdout.flush()
    os._exit(code)


if __name__ == "__main__":
    main()
