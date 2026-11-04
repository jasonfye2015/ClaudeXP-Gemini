"""Claude Timeline - the SYSTEC Multi-Boot Manager: pick a computer and boot it."""
import sys

from PySide6.QtWidgets import QApplication

from systec.ui import Systec


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("SYSTEC Multi-Boot Manager")
    try:
        from claudecore import relocate
        relocate.fix_shared()          # the drive changed letter (another PC): the shared saves and settings follow it
    except Exception as exc:
        if sys.stderr is not None:
            sys.stderr.write(f"Relocation check failed: {exc}\n")
    try:
        from claudecore import macfonts
        macfonts.apply()               # on a Mac: Mac fonts for the Windows ones
    except ImportError:
        pass
    win = Systec()
    win.resize(1408, 768)
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
