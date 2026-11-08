"""The window: the view, and over it (when one is up) the title or the pause.

The title stands at the foot of the hollow, turning slowly, looking up into the dark (and whatever is up there
looking back): the name, a line, Begin. Begin goes to Before the night (ui/menu.py): begin the night, the endings
found, the records, saved nights, unlocks, the options. Esc in the night pauses it: Resume, or back to the title.
What's kept between nights is the Records (game/records.py) in the saves folder."""
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter
from PySide6.QtWidgets import QPushButton, QVBoxLayout, QWidget

from ..game.night import Night
from ..game.records import Records
from .view import SERIF, GameView

BUTTONS = """QPushButton { color: #E6D8C2; background: rgba(20, 14, 12, 170); border: 1px solid #5C4632;
    border-radius: 4px; padding: 9px 30px; font-family: Georgia; font-size: 15px; }
QPushButton:hover { background: rgba(60, 36, 26, 210); border-color: #A07A54; color: #FFF0DA; }"""


class Panel(QWidget):
    """A layer over the view: dark at the edges, words painted in the middle, a column of buttons below them."""

    def __init__(self, shell, title, line, buttons, small=False):
        super().__init__(shell)
        self.shell, self.title, self.line, self.small = shell, title, line, small
        self.setStyleSheet(BUTTONS)
        lay = QVBoxLayout(self)
        lay.addStretch(3 if not small else 2)
        for text, fn in buttons:
            b = QPushButton(text)
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(fn)
            b.setFixedWidth(240)
            lay.addWidget(b, 0, Qt.AlignHCenter)
        lay.addStretch(1)

    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        W, H = self.width(), self.height()
        g = QLinearGradient(0, 0, 0, H)
        g.setColorAt(0, QColor(0, 0, 0, 60 if not self.small else 150))
        g.setColorAt(0.5, QColor(0, 0, 0, 30 if not self.small else 150))
        g.setColorAt(1, QColor(0, 0, 0, 200))
        p.fillRect(self.rect(), g)
        p.setPen(QColor(232, 220, 200))
        f = QFont(SERIF, 54 if not self.small else 32)
        f.setLetterSpacing(QFont.PercentageSpacing, 112)
        p.setFont(f)
        p.drawText(QRectF(0, H * (0.2 if not self.small else 0.28), W, 90), Qt.AlignHCenter, self.title)
        f2 = QFont(SERIF, 15)
        f2.setItalic(True)
        p.setFont(f2)
        p.setPen(QColor(196, 184, 166))
        p.drawText(QRectF(0, H * (0.2 if not self.small else 0.28) + 92, W, 40), Qt.AlignHCenter, self.line)
        p.end()


class Shell(QWidget):
    def __init__(self, saves_dir, muted=lambda: False):
        super().__init__()
        self.setMinimumSize(800, 520)
        self.saves_dir = saves_dir
        self.muted = muted
        self.records = Records(saves_dir)
        self.view = GameView(self)
        self.panel = None
        self.frame = None
        self.show_title()

    def resizeEvent(self, e):
        self.view.setGeometry(self.rect())
        if self.panel:
            self.panel.setGeometry(self.rect())
        super().resizeEvent(e)

    def panel_open(self):
        return self.panel is not None

    def set_panel(self, panel):
        if self.panel is not None:
            self.panel.hide()
            self.panel.deleteLater()
        self.panel = panel
        if panel is not None:
            panel.setGeometry(self.rect())
            panel.show()
            panel.raise_()

    def show_title(self):
        self.view.release()
        self.view.night_done()                                  # (a night left part-way: its tallies kept)
        self.view.backdrop(Night())
        self.set_panel(Panel(self, "The Hollow Oak", "One night. One host. Get to dawn.",
                             [("Begin", self.show_menu), ("Leave", self.leave)]))

    def show_menu(self):
        from .menu import NightMenu
        self.set_panel(NightMenu(self))

    def begin(self):
        self.set_panel(None)
        self.view.begin(Night())

    def pause(self):
        if not self.view.playing:
            return
        if self.panel:
            self.resume()
            return
        self.set_panel(Panel(self, "The night waits", f"It is {self.view.night.clock_words()}.",
                             [("Go on", self.resume), ("Back to the title", self.show_title)], small=True))

    def resume(self):
        self.set_panel(None)
        self.view.setFocus()
        self.view.capture()

    def leave(self):
        w = self.frame or self.window()
        try:
            w.close()
        except Exception:
            pass

    def close_down(self):
        self.view.release()
        self.view.night_done()
        if self.view.audio is not None:
            self.view.audio.stop()
