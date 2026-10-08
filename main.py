"""ClaudeXP - a virtual Windows XP desktop that will host ClaudeAIM and friends."""
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
    sys.exit(qapp.exec())


if __name__ == "__main__":
    main()
