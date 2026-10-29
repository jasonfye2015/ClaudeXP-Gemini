"""Kithylin AI on its own, outside the Timeline's computers:  python -m kithylinai  (from ClaudeApps)."""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
for extra in (HERE.parents[1] / "ClaudeCore", HERE.parent):      # the codes module, and ourselves
    if extra.is_dir() and str(extra) not in sys.path:
        sys.path.insert(0, str(extra))


def main():
    from PySide6.QtWidgets import QApplication, QMainWindow
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("Kithylin AI")
    try:
        from claudecore import single           # one copy at a time: started again, the one running comes forward
    except ImportError:
        single = None                           # (lifted out of the Timeline: no claudecore)
    if single is not None and single.ask_to_show("kithylinai"):
        return 0
    try:
        from claudecore import macfonts
        macfonts.apply()               # on a Mac: Mac fonts for the Windows ones
    except ImportError:
        pass
    from kithylinai.app import KithylinAI, app_icon

    class Window(QMainWindow):
        """Closed while a bot listens (Telegram, Discord): Kithylin AI waits in the notification area instead."""

        def closeEvent(self, event):
            content = self.centralWidget()
            if content is not None and content.close_to_tray():
                event.ignore()
                return
            super().closeEvent(event)
    win = Window()
    win.setWindowTitle("Kithylin AI")
    win.setWindowIcon(app_icon())
    content = KithylinAI(None)
    content.frame = win
    win.setCentralWidget(content)
    win.resize(1000, 720)
    app.aboutToQuit.connect(content.shutdown)
    win.show()
    content.composer.setFocus()
    listening = single.listen("kithylinai", lambda: single.come_forward(win, content)) if single is not None else None
    code = app.exec()
    if listening is not None:
        listening.close()
    return code


if __name__ == "__main__":
    sys.exit(main())
