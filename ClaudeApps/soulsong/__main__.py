"""Soul and Song on its own, outside the Timeline's computers:  python -m soulsong  (from ClaudeApps)."""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
for extra in (HERE.parents[1] / "ClaudeCore", HERE.parent):      # claudecore, kithylinai and ourselves
    if extra.is_dir() and str(extra) not in sys.path:
        sys.path.insert(0, str(extra))


def main():
    from PySide6.QtWidgets import QApplication, QMainWindow
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("Soul and Song")
    from soulsong import soulsong_icon
    from soulsong.app import SoulAndSong
    win = QMainWindow()
    win.setWindowTitle("Soul and Song")
    win.setWindowIcon(soulsong_icon())
    content = SoulAndSong(None)
    content.frame = win
    win.setCentralWidget(content)
    win.resize(1100, 740)
    app.aboutToQuit.connect(content.shutdown)
    win.show()
    content.composer.setFocus()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
