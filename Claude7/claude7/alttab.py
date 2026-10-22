"""Alt+Tab, Windows 7 style: a glass box of window thumbnails with the chosen one's title above. The keyboard hook
that catches Alt+Tab while Claude7 is fullscreen is ClaudeXP's."""
import os

from PySide6.QtCore import QRect, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QFontMetrics, QLinearGradient, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QApplication, QStyle, QWidget

from . import sound

CELL_W, CELL_H, COLS = 170, 128, 6


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
        w = cols * CELL_W + 40
        h = rows * CELL_H + 70
        self.resize(w, h)
        self.move((self.desktop.width() - w) // 2, (self.desktop.height() - h) // 2)

    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        from . import display
        tint = QColor(display.get().aero_color()).darker(150)
        tint.setAlpha(225)
        r = QRectF(0.5, 0.5, self.width() - 1, self.height() - 1)
        p.setPen(QPen(QColor(0, 0, 0, 170), 1))
        p.setBrush(tint)
        p.drawRoundedRect(r, 8, 8)
        sheen = QLinearGradient(0, 0, 0, self.height())
        sheen.setColorAt(0, QColor(255, 255, 255, 80))
        sheen.setColorAt(1, QColor(255, 255, 255, 20))
        p.setBrush(sheen)
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(r, 8, 8)
        p.setPen(QPen(QColor(255, 255, 255, 110), 1))
        p.setBrush(Qt.NoBrush)
        p.drawRoundedRect(r.adjusted(1, 1, -1, -1), 7, 7)
        f = QFont("Segoe UI")
        f.setPixelSize(13)
        p.setFont(f)
        title = self.wins[self.index].title if self.wins else ""
        p.setPen(QColor(0, 0, 0, 120))
        p.drawText(QRect(21, 11, self.width() - 40, 22), Qt.AlignCenter,
                   QFontMetrics(f).elidedText(title, Qt.ElideRight, self.width() - 60))
        p.setPen(QColor("white"))
        p.drawText(QRect(20, 10, self.width() - 40, 22), Qt.AlignCenter,
                   QFontMetrics(f).elidedText(title, Qt.ElideRight, self.width() - 60))
        n = len(self.wins)
        cols = min(COLS, n)
        x0 = (self.width() - cols * CELL_W) // 2
        fallback = QApplication.style().standardIcon(QStyle.SP_DesktopIcon)
        for i, win in enumerate(self.wins):
            r_, c = divmod(i, COLS)
            cell = QRect(x0 + c * CELL_W, 44 + r_ * CELL_H, CELL_W, CELL_H)
            if i == self.index:
                p.setPen(QPen(QColor(255, 255, 255, 200), 2))
                p.setBrush(QColor(255, 255, 255, 60))
                p.drawRoundedRect(QRectF(cell).adjusted(3, 3, -3, -3), 4, 4)
            shot = self.shots.get(id(win))
            box = cell.adjusted(12, 10, -12, -34)
            if shot is not None and not shot.isNull():
                s = shot.scaled(box.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                p.drawPixmap(box.x() + (box.width() - s.width()) // 2, box.y() + (box.height() - s.height()) // 2, s)
            else:
                p.fillRect(box, QColor(0, 0, 0, 60))
            icon = win.icon if not win.icon.isNull() else fallback
            p.drawPixmap(cell.x() + (CELL_W - 24) // 2, cell.bottom() - 30, icon.pixmap(24, 24))


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
