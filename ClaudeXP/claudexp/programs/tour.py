"""Tour Windows XP: an animated slideshow (drifting light, text that glides in, the Windows XP logo) with music,
like the tour that came with XP. After Setup, a tray icon pops XP's 'Take a tour of Windows XP' balloon."""
import math
import random

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QIcon, QLinearGradient, QPainter, QPen, QPixmap, QRadialGradient
from PySide6.QtWidgets import QWidget

from .. import sound
from ..wm import XPWindow

SLIDES = [
    ("Welcome to Windows XP", "Take a few minutes to see what your new computer can do.",
     ["Click Next to begin, or let the tour play by itself."]),
    ("Windows XP Basics", "Your desktop and the Start menu",
     ["Click start for your programs: the ones you use most appear first.",
      "All Programs holds everything, from Accessories to Games.",
      "Right-click the desktop to arrange icons, or to pick a new background and screen saver."]),
    ("Best for Staying in Touch", "Your friends are always around",
     ["ClaudeAIM tells you which buddies are online.",
      "FurNet IRC and PawPrints MUCK are busy around the clock.",
      "Outlook Express brings their e-mail, and they'll answer yours."]),
    ("Best for the Internet", "The Web at 56K",
     ["Connect with America Online and listen to that modem sing.",
      "Explore the Web with Netscape Navigator.",
      "Print anything you find, straight to your external drive."]),
    ("Best for Digital Media", "Music, pictures and sound",
     ["Windows Media Player plays your music with visualizations that move to the beat.",
      "Paint turns your ideas into pictures.",
      "Sound Recorder captures your voice."]),
    ("Best for Fun", "Games for every mood",
     ["Solitaire, FreeCell, Spider Solitaire, Minesweeper and Hearts.",
      "Play your buddies in Internet Checkers, Reversi, Backgammon, Hearts and Spades.",
      "And, of course, 3D Pinball - Space Cadet."]),
    ("Reliable and Safe", "Windows XP takes care of itself",
     ["Windows Update and ClaudeShield AntiVirus keep you protected.",
      "System Restore undoes changes that went wrong, without touching your files.",
      "Task Manager (Ctrl+Alt+End) shows everything that's running."]),
    ("You're Ready!", "Enjoy Windows XP", ["To see this tour again, look in Help and Support.",
                                           "Click Exit Tour to get started."]),
]
SLIDE_SECONDS = 14


def tour_icon():
    pm = QPixmap(32, 32)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    for (x, y), c in zip(((5, 5), (17, 5), (5, 17), (17, 17)), ("#F25022", "#7FBA00", "#00A4EF", "#FFB900")):
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(c))
        p.drawRoundedRect(QRectF(x, y, 10, 10), 2, 2)
    p.end()
    return QIcon(pm)


class Tour(QWidget):
    def __init__(self, desktop):
        super().__init__()
        self.desktop = desktop
        self.frame = None
        self.slide = 0
        self.t = 0.0
        self.slide_t = 0.0
        self.hover = None
        self.orbs = [(random.uniform(0, 1), random.uniform(0, 1), random.uniform(30, 120), random.uniform(0.02, 0.06),
                      random.uniform(0, 6.28)) for _ in range(14)]
        self.logo = None
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.player = sound.play_file("oobe_music.mp3")
        if self.player is not None and self.player.audioOutput() is not None:
            self.player.audioOutput().setVolume(0.45)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(33)

    def _tick(self):
        self.t += 0.033
        self.slide_t += 0.033
        if self.slide_t > SLIDE_SECONDS and self.slide < len(SLIDES) - 1:
            self.go(self.slide + 1)
        self.update()

    def go(self, i):
        self.slide = max(0, min(len(SLIDES) - 1, i))
        self.slide_t = 0.0

    def buttons(self):
        w, h = self.width(), self.height()
        out = {"exit": QRectF(w - 110, h - 40, 96, 28)}
        if self.slide > 0:
            out["back"] = QRectF(w - 330, h - 40, 96, 28)
        if self.slide < len(SLIDES) - 1:
            out["next"] = QRectF(w - 220, h - 40, 96, 28)
        return out

    def mouseMoveEvent(self, event):
        self.hover = next((k for k, r in self.buttons().items() if r.contains(event.position())), None)

    def mousePressEvent(self, event):
        for key, r in self.buttons().items():
            if r.contains(event.position()):
                sound.play("menu")
                if key == "exit":
                    self.frame.request_close()
                else:
                    self.go(self.slide + (1 if key == "next" else -1))

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Right, Qt.Key_Space, Qt.Key_Return):
            self.go(self.slide + 1)
        elif event.key() == Qt.Key_Left:
            self.go(self.slide - 1)
        elif event.key() == Qt.Key_Escape:
            self.frame.request_close()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        g = QLinearGradient(0, 0, w, h)
        g.setColorAt(0, QColor("#0B2A86"))
        g.setColorAt(0.6, QColor("#2D63D3"))
        g.setColorAt(1, QColor("#5B92F0"))
        p.fillRect(self.rect(), g)
        # drifting light
        for x, y, r, speed, phase in self.orbs:
            cx = (x * w + math.sin(self.t * speed * 6 + phase) * 60) % w
            cy = (y * h + math.cos(self.t * speed * 5 + phase) * 40) % h
            rg = QRadialGradient(QPointF(cx, cy), r)
            rg.setColorAt(0, QColor(255, 255, 255, 40))
            rg.setColorAt(1, QColor(255, 255, 255, 0))
            p.setPen(Qt.NoPen)
            p.setBrush(rg)
            p.drawEllipse(QPointF(cx, cy), r, r)
        # a sweeping green band, like the XP hills
        p.setBrush(QColor(120, 200, 80, 60))
        p.drawEllipse(QRectF(-w * 0.3, h * 0.78 + math.sin(self.t * 0.6) * 8, w * 1.6, h * 0.6))
        title, subtitle, lines = SLIDES[self.slide]
        ease = min(1.0, self.slide_t / 0.9)
        ease = 1 - (1 - ease) ** 3
        x = 50 + (1 - ease) * 80
        tf = QFont("Franklin Gothic Medium")
        tf.setPixelSize(int(h * 0.075))
        p.setFont(tf)
        p.setPen(QColor(255, 255, 255, int(255 * ease)))
        p.drawText(QRectF(x, h * 0.12, w - 100, h * 0.12), Qt.AlignLeft | Qt.AlignVCenter, title)
        sf = QFont("Tahoma")
        sf.setPixelSize(int(h * 0.035))
        sf.setItalic(True)
        p.setFont(sf)
        p.setPen(QColor(255, 220, 120, int(255 * ease)))
        p.drawText(QRectF(x + 4, h * 0.24, w - 100, h * 0.06), Qt.AlignLeft | Qt.AlignVCenter, subtitle)
        bf = QFont("Tahoma")
        bf.setPixelSize(int(h * 0.032))
        p.setFont(bf)
        for i, line in enumerate(lines):
            appear = max(0.0, min(1.0, (self.slide_t - 0.8 - i * 0.9) / 0.6))
            if appear <= 0:
                continue
            ly = h * 0.38 + i * h * 0.1
            lx = 70 + (1 - appear) * 40
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(255, 255, 255, int(200 * appear)))
            p.drawEllipse(QPointF(lx - 16, ly + h * 0.03), 4, 4)
            p.setPen(QColor(255, 255, 255, int(255 * appear)))
            p.drawText(QRectF(lx, ly, w - lx - 60, h * 0.08), Qt.AlignLeft | Qt.TextWordWrap, line)
        if self.slide == 0:
            self._draw_logo(p, w, h)
        # progress dots
        for i in range(len(SLIDES)):
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(255, 255, 255, 230 if i == self.slide else 80))
            p.drawEllipse(QPointF(30 + i * 16, h - 26), 4.5, 4.5)
        # buttons
        labels = {"back": "◀  Back", "next": "Next  ▶", "exit": "Exit Tour"}
        f = QFont("Tahoma")
        f.setPixelSize(12)
        f.setBold(True)
        p.setFont(f)
        for key, r in self.buttons().items():
            p.setPen(QPen(QColor(255, 255, 255, 180), 1))
            p.setBrush(QColor(255, 255, 255, 70 if self.hover == key else 30))
            p.drawRoundedRect(r, 13, 13)
            p.setPen(QColor("white"))
            p.drawText(r, Qt.AlignCenter, labels[key])

    def _draw_logo(self, p, w, h):
        if self.logo is None:
            from ..setup.gui import _logo
            self.logo = _logo()
        if self.logo.isNull():
            return
        appear = max(0.0, min(1.0, (self.slide_t - 0.3) / 1.2))
        lw = w * 0.34
        lh = lw * self.logo.height() / self.logo.width()
        p.setOpacity(appear)
        p.drawPixmap(QRectF(w - lw - 40, h * 0.55 - lh / 2 + (1 - appear) * 20, lw, lh), self.logo,
                     QRectF(self.logo.rect()))
        p.setOpacity(1.0)

    def closeEvent(self, event):
        self.timer.stop()
        if self.player is not None:
            from shiboken6 import isValid
            if isValid(self.player):
                self.player.stop()
        event.accept()


def open_tour(desktop):
    body = Tour(desktop)
    win = XPWindow(desktop, "Windows XP Tour", body, tour_icon(), (760, 520))
    body.frame = win
    desktop.open_window(win)
    body.setFocus()
    return win


def offer_tour(desktop):
    """XP's balloon after Setup: 'Take a tour of Windows XP'. The tray icon goes away after a while."""
    from ..tray import TrayIcon
    icon = TrayIcon(desktop, tour_icon(), desktop)
    icon.setToolTip("Take a tour of Windows XP")
    icon.show()
    icon.showMessage("Take a tour of Windows XP", "To learn about the exciting new features in Windows XP, click "
                     "here.", None, 20000)

    def start():
        icon.hide()
        icon.deleteLater()
        open_tour(desktop)
    icon.messageClicked.connect(start)
    icon.activated.connect(lambda _r: start())
    QTimer.singleShot(5 * 60 * 1000, lambda: (icon.hide(), icon.deleteLater()) if icon.isVisible() else None)
