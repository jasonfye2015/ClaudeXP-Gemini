"""Alt+Tab, Windows 11 style: a light rounded panel of big window thumbnails, each with its icon and title above it.
The keyboard hook that catches Alt+Tab while Claude11 is fullscreen is ClaudeXP's."""
import os

from PySide6.QtCore import QRect, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QApplication, QStyle, QWidget

from . import sound
from . import theme11 as T

CELL_W, CELL_H, COLS = 232, 180, 5


class AltTab(QWidget):
    def __init__(self, desktop):
        super().__init__(desktop)
        self.desktop = desktop
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setFocusPolicy(Qt.NoFocus)
        self.wins = []
        self.shots = {}
        self.index = 0
        self.hide()

    def _order(self):
        d = self.desktop
        shown = [w for w in reversed(d.windows) if w.on_taskbar and w.isVisible()]
        hidden = [w for w in reversed(d.windows) if w.on_taskbar and not w.isVisible()]
        return shown + hidden

    def tab(self, backwards=False):
        if not self.isVisible():
            self.wins = self._order()
            if not self.wins:
                return
            self.shots = {}
            for w in self.wins:
                try:
                    self.shots[id(w)] = w.grab() if w.isVisible() else QPixmap()
                except Exception:
                    self.shots[id(w)] = QPixmap()
            n = len(self.wins)
            self.index = (n - 1 if backwards else 1) % n
            self.desktop.hide_start_menu()
            self._place()
            self.show()
            self.raise_()
        else:
            self.wins = [w for w in self.wins if w in self.desktop.windows]
            if not self.wins:
                self.cancel()
                return
            self.index = (self.index + (-1 if backwards else 1)) % len(self.wins)
        self.update()

    def commit(self):
        if not self.isVisible():
            return
        self.hide()
        if 0 <= self.index < len(self.wins):
            win = self.wins[self.index]
            if win in self.desktop.windows:
                if not win.isVisible():
                    sound.play("restore")
                self.desktop.activate(win)
                self.desktop.taskbar.update()

    def cancel(self):
        self.hide()

    def _place(self):
        n = len(self.wins)
        cols = min(COLS, n)
        rows = (n + COLS - 1) // COLS
        w = cols * CELL_W + 48
        h = rows * CELL_H + 48
        self.resize(w, h)
        self.move((self.desktop.width() - w) // 2, (self.desktop.height() - h) // 2)

    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        from . import display
        accent = display.get().accent()
        r = QRectF(0.5, 0.5, self.width() - 1, self.height() - 1)
        p.setPen(QPen(T.hover(50), 1))
        p.setBrush(T.base_alpha(240))
        p.drawRoundedRect(r, 10, 10)
        from .style import font
        f = font(12)
        p.setFont(f)
        n = len(self.wins)
        cols = min(COLS, n)
        x0 = (self.width() - cols * CELL_W) // 2
        fallback = QApplication.style().standardIcon(QStyle.SP_DesktopIcon)
        for i, win in enumerate(self.wins):
            r_, c = divmod(i, COLS)
            cell = QRect(x0 + c * CELL_W, 24 + r_ * CELL_H, CELL_W, CELL_H)
            if i == self.index:
                p.setPen(Qt.NoPen)
                p.setBrush(T.hover(14))
                p.drawRoundedRect(QRectF(cell).adjusted(4, 4, -4, -4), 8, 8)
            icon = win.icon if not win.icon.isNull() else fallback
            p.drawPixmap(cell.x() + 16, cell.y() + 14, icon.pixmap(16, 16))
            p.setPen(T.text())
            p.drawText(QRect(cell.x() + 40, cell.y() + 12, CELL_W - 56, 20), Qt.AlignVCenter | Qt.AlignLeft,
                       QFontMetrics(f).elidedText(win.title, Qt.ElideRight, CELL_W - 60))
            box = cell.adjusted(16, 40, -16, -16)
            shot = self.shots.get(id(win))
            p.setPen(QPen(accent if i == self.index else T.hover(30), 2 if i == self.index else 1))
            p.setBrush(T.card(255))
            p.drawRoundedRect(QRectF(box).adjusted(-3, -3, 3, 3), 6, 6)
            if shot is not None and not shot.isNull():
                s = shot.scaled(box.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                p.drawPixmap(box.x() + (box.width() - s.width()) // 2, box.y() + (box.height() - s.height()) // 2, s)
            else:
                p.fillRect(box, T.hover(20))
                p.drawPixmap(box.center().x() - 16, box.center().y() - 16, icon.pixmap(32, 32))


def install(main):
    switcher = AltTab(main.desktop)
    if os.name != "nt":
        return switcher
    try:
        from claudexp.alttab import KeyHook
        hook = KeyHook(main, switcher)
    except Exception:
        return switcher
    app = QApplication.instance()

    def state(st):
        if st == Qt.ApplicationActive:
            hook.install()
        else:
            hook.uninstall()
    app.applicationStateChanged.connect(state)
    app.aboutToQuit.connect(hook.uninstall)
    if app.applicationState() == Qt.ApplicationActive:
        hook.install()
    switcher.hook = hook
    return switcher
