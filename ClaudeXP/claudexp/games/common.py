"""Shared bits for the games: their window (menu bar + play area + status bar), saved stats, icons."""
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QHBoxLayout, QLabel, QMenuBar, QVBoxLayout, QWidget
from shiboken6 import isValid

from .. import sound
from ..paths import DATA
from ..programs.people import load_json, save_json
from ..wm import XPWindow

STATS_FILE = DATA / "games.json"
MENU_STYLE = """
QMenuBar { background: #ECE9D8; font-family: Tahoma; font-size: 11px; }
QMenuBar::item { padding: 3px 7px; background: transparent; }
QMenuBar::item:selected { background: #316AC5; color: white; }
QMenu { background: white; border: 1px solid #ACA899; font-family: Tahoma; font-size: 11px; }
QMenu::item { padding: 4px 24px 4px 20px; }
QMenu::item:selected { background: #316AC5; color: white; }
QLabel#gamestatus { background: #ECE9D8; border-top: 1px solid #ACA899; padding: 2px 8px; font-family: Tahoma; font-size: 11px; }
"""


def stats(game):
    return load_json(STATS_FILE, {}).get(game, {})


def save_stats(game, values):
    data = load_json(STATS_FILE, {})
    data[game] = values
    save_json(STATS_FILE, data)


class GameWindow(QWidget):
    """A game's window body: menu bar, the play area, and a status bar."""

    def __init__(self, desktop, make_play, status=True):
        """make_play(window) builds the play area (it can use window.status and window.desktop)."""
        super().__init__()
        self.desktop = desktop
        self.frame = None
        self.setStyleSheet(MENU_STYLE)
        self.menu = QMenuBar()
        self.menu.triggered.connect(lambda _a: sound.play("menu"))
        self.status = QLabel(" ")
        self.status.setObjectName("gamestatus")
        play_area = self.play = make_play(self)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.setMenuBar(self.menu)
        root.addWidget(play_area, 1)
        if status:
            root.addWidget(self.status)
        else:
            self.status.hide()

    def fit(self):
        """Lock the window to its contents' size (Minesweeper's board changes size with the level)."""
        self.layout().activate()
        self.setFixedSize(self.sizeHint())
        if self.frame is not None:
            self.frame.fit_fixed_content()

    def closeEvent(self, event):
        stop = getattr(self.play, "stop", None)
        if stop:
            stop()
        event.accept()


_open = {}


def open_game(desktop, key, title, make, icon, size):
    """Open (or bring back) a game window. make() returns a GameWindow."""
    win = _open.get(key)
    if win is not None and isValid(win):
        desktop.open_window(win)
        return win
    body = make()
    win = XPWindow(desktop, title, body, icon, size=size or (300, 300))
    body.frame = win
    if size is None:
        body.fit()
    _open[key] = win
    desktop.open_window(win)
    return win


def message(desktop, title, text, buttons=("OK",), on_button=None, icon="info"):
    from ..explorer.dialogs import msgbox
    return msgbox(desktop, title, text, icon, buttons, on_button)


# ---- icons for the Start menu ----------------------------------------------------------------------

def card_icon(suit="S", color="#000000", back=False):
    pm = QPixmap(32, 32)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(QPen(QColor("#404040"), 1))
    p.setBrush(QColor("#2A5DD6"))
    p.drawRoundedRect(QRectF(4, 2, 18, 25), 2, 2)
    p.setBrush(QColor("white"))
    p.drawRoundedRect(QRectF(11, 5, 18, 25), 2, 2)
    p.setPen(QColor(color))
    font = QFont("Segoe UI Symbol")
    font.setPixelSize(16)
    p.setFont(font)
    p.drawText(QRectF(11, 5, 18, 25), Qt.AlignCenter, {"S": "♠", "H": "♥", "C": "♣", "D": "♦"}[suit])
    p.end()
    return QIcon(pm)


def mine_icon():
    pm = QPixmap(32, 32)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(QPen(QColor("black"), 2))
    for a in range(0, 180, 45):
        import math
        dx, dy = 13 * math.cos(math.radians(a)), 13 * math.sin(math.radians(a))
        p.drawLine(int(16 - dx), int(16 - dy), int(16 + dx), int(16 + dy))
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("black"))
    p.drawEllipse(QRectF(8, 8, 16, 16))
    p.setBrush(QColor("white"))
    p.drawEllipse(QRectF(11, 11, 4, 4))
    p.end()
    return QIcon(pm)
