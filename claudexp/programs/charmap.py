"""Character Map: every character a font has, in a grid. Click to magnify, Select to add it to 'Characters to
copy', Copy to put them on the clipboard. The status bar names the character (U+00E9: Latin Small Letter E...)."""
import unicodedata

from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import QColor, QFont, QFontMetrics, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (QApplication, QFontComboBox, QHBoxLayout, QLabel, QLineEdit, QPushButton, QScrollArea,
                               QVBoxLayout, QWidget)

from ..wm import XPWindow

RANGES = [(0x21, 0x7E), (0xA1, 0x24F), (0x370, 0x3FF), (0x400, 0x45F), (0x2010, 0x205E), (0x20A0, 0x20AF),
          (0x2100, 0x2153), (0x2190, 0x21FF), (0x2200, 0x22FF), (0x2300, 0x23FF), (0x2460, 0x24FF),
          (0x2500, 0x25FF), (0x2600, 0x26FF), (0x2700, 0x27BF), (0xFB00, 0xFB06)]
COLS, CELL = 20, 24


def charmap_icon():
    pm = QPixmap(32, 32)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setPen(QPen(QColor("#505050"), 1))
    p.setBrush(QColor("white"))
    p.drawRect(QRectF(3.5, 5.5, 25, 22))
    p.setPen(QColor("#A0A0A0"))
    for i in range(1, 3):
        p.drawLine(4, 5 + i * 7, 28, 5 + i * 7)
        p.drawLine(3 + i * 8, 6, 3 + i * 8, 27)
    f = QFont("Times New Roman")
    f.setPixelSize(10)
    f.setBold(True)
    p.setFont(f)
    p.setPen(QColor("#1040A0"))
    for (x, y), ch in zip(((4, 6), (12, 6), (20, 6), (4, 13), (12, 13), (20, 13)), "Aé©Ω¶æ"):
        p.drawText(QRectF(x, y, 8, 7), Qt.AlignCenter, ch)
    p.end()
    return QIcon(pm)


class Grid(QWidget):
    picked = Signal(str)
    chosen = Signal(str)

    def __init__(self):
        super().__init__()
        self.font_ = QFont("Arial")
        self.chars = []
        self.current = 0
        self.setFocusPolicy(Qt.StrongFocus)
        self.set_font(self.font_)

    def set_font(self, font):
        self.font_ = QFont(font)
        self.font_.setPixelSize(15)
        fm = QFontMetrics(self.font_)
        self.chars = [chr(c) for a, b in RANGES for c in range(a, b + 1) if fm.inFont(chr(c))]
        self.current = 0
        rows = (len(self.chars) + COLS - 1) // COLS
        self.setFixedSize(COLS * CELL + 1, rows * CELL + 1)
        self.update()
        if self.chars:
            self.picked.emit(self.chars[0])

    def mousePressEvent(self, event):
        i = int(event.position().y() // CELL) * COLS + int(event.position().x() // CELL)
        if 0 <= i < len(self.chars):
            self.current = i
            self.picked.emit(self.chars[i])
            self.update()

    def mouseDoubleClickEvent(self, event):
        self.mousePressEvent(event)
        if 0 <= self.current < len(self.chars):
            self.chosen.emit(self.chars[self.current])

    def keyPressEvent(self, event):
        moves = {Qt.Key_Left: -1, Qt.Key_Right: 1, Qt.Key_Up: -COLS, Qt.Key_Down: COLS}
        if event.key() in moves:
            self.current = max(0, min(len(self.chars) - 1, self.current + moves[event.key()]))
            self.picked.emit(self.chars[self.current])
            self.update()
        elif event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space):
            self.chosen.emit(self.chars[self.current])
        else:
            super().keyPressEvent(event)

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor("white"))
        p.setFont(self.font_)
        p.setPen(QColor("#A0A0A0"))
        rows = (len(self.chars) + COLS - 1) // COLS
        for r in range(rows + 1):
            p.drawLine(0, r * CELL, COLS * CELL, r * CELL)
        for c in range(COLS + 1):
            p.drawLine(c * CELL, 0, c * CELL, rows * CELL)
        p.setPen(QColor("black"))
        clip = event.rect()
        for i, ch in enumerate(self.chars):
            rect = QRectF((i % COLS) * CELL, (i // COLS) * CELL, CELL, CELL)
            if rect.bottom() < clip.top() or rect.top() > clip.bottom():
                continue
            if i == self.current:
                p.fillRect(rect.adjusted(1, 1, 0, 0), QColor("#316AC5"))
                p.setPen(QColor("white"))
                p.drawText(rect, Qt.AlignCenter, ch)
                p.setPen(QColor("black"))
            else:
                p.drawText(rect, Qt.AlignCenter, ch)


class CharacterMap(QWidget):
    def __init__(self, desktop):
        super().__init__()
        self.desktop = desktop
        self.frame = None
        self.setObjectName("cm")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("QWidget#cm { background: #ECE9D8; } QLabel, QPushButton { font-family: Tahoma; "
                           "font-size: 11px; } QLabel#status { border-top: 1px solid #ACA899; padding: 2px 6px; }")
        v = QVBoxLayout(self)
        v.setContentsMargins(8, 8, 8, 0)
        row = QHBoxLayout()
        row.addWidget(QLabel("Font :"))
        self.font_box = QFontComboBox()
        self.font_box.setCurrentFont(QFont("Arial"))
        row.addWidget(self.font_box, 1)
        v.addLayout(row)
        self.grid = Grid()
        scroll = QScrollArea()
        scroll.setWidget(self.grid)
        scroll.setFixedHeight(10 * CELL + 4)
        scroll.setFixedWidth(COLS * CELL + 22)
        v.addWidget(scroll)
        row = QHBoxLayout()
        row.addWidget(QLabel("Characters to copy :"))
        self.to_copy = QLineEdit()
        row.addWidget(self.to_copy, 1)
        select, copy = QPushButton("Select"), QPushButton("Copy")
        for b in (select, copy):
            b.setFixedSize(70, 23)
            row.addWidget(b)
        v.addLayout(row)
        self.big = QLabel()
        self.big.setFixedSize(64, 64)
        self.big.setAlignment(Qt.AlignCenter)
        self.big.setStyleSheet("background: white; border: 1px solid #7F9DB9; font-size: 40px;")
        self.status = QLabel("")
        self.status.setObjectName("status")
        bottom = QHBoxLayout()
        bottom.addWidget(self.status, 1)
        bottom.addWidget(self.big)
        v.addLayout(bottom)
        self.font_box.currentFontChanged.connect(self._font_changed)
        self.grid.picked.connect(self._picked)
        self.grid.chosen.connect(lambda ch: self.to_copy.insert(ch))
        select.clicked.connect(lambda: self.grid.chars and self.to_copy.insert(self.grid.chars[self.grid.current]))
        copy.clicked.connect(lambda: QApplication.clipboard().setText(self.to_copy.text()))
        self._picked(self.grid.chars[0] if self.grid.chars else "")

    def _font_changed(self, font):
        self.grid.set_font(font)
        f = QFont(font)
        f.setPixelSize(40)
        self.big.setFont(f)
        self.to_copy.setFont(QFont(font.family(), 11))

    def _picked(self, ch):
        if not ch:
            return
        self.big.setText(ch)
        try:
            name = unicodedata.name(ch).title()
        except ValueError:
            name = "Unknown"
        self.status.setText(f"U+{ord(ch):04X}: {name}")


def open_charmap(desktop):
    body = CharacterMap(desktop)
    win = XPWindow(desktop, "Character Map", body, charmap_icon(), (560, 420), buttons=("min", "close"))
    body.frame = win
    body.setFixedSize(body.sizeHint())
    win.fit_fixed_content()
    desktop.open_window(win)
    return win
