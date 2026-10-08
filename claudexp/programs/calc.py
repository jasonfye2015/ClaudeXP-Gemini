"""Calculator (Standard view), like Windows XP's: the '0.' display, Backspace/CE/C, memory (MC MR MS M+),
sqrt, %, 1/x, +/-, repeated '=' and keyboard input. Edit > Copy/Paste."""
from decimal import Decimal, DivisionByZero, InvalidOperation, getcontext

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QIcon, QKeySequence, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (QApplication, QGridLayout, QLabel, QLineEdit, QMenuBar, QPushButton, QVBoxLayout,
                               QWidget)

from .. import sound
from ..wm import XPWindow
from .notepad import MENU_STYLE

getcontext().prec = 32

STYLE = MENU_STYLE + """
QWidget#calc { background: #ECE9D8; }
QLineEdit { font-family: Tahoma; font-size: 13px; background: white; border: 1px solid #7F9DB9; padding: 2px 4px; }
QPushButton { font-family: Tahoma; font-size: 11px; min-height: 26px; }
QPushButton[kind="op"], QPushButton[kind="clear"], QPushButton[kind="mem"] { color: #D00000; }
QPushButton[kind="digit"] { color: #0000C0; }
QLabel#mem { border: 1px solid #ACA899; background: #ECE9D8; font-family: Tahoma; font-size: 11px; }
"""


def fmt(value):
    """XP shows integers with a trailing point: '0.', '42.'."""
    if value == value.to_integral_value() and abs(value) < Decimal(10) ** 32:
        return f"{int(value)}."
    text = format(value.normalize(), "f")
    if len(text.replace("-", "").replace(".", "")) > 32:
        text = format(value, ".31e").replace("e", "e")
    return text


class Calculator(QWidget):
    def __init__(self, desktop):
        super().__init__()
        self.desktop = desktop
        self.frame = None
        self.setObjectName("calc")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(STYLE)
        self.acc = None            # left operand
        self.op = None             # pending operator
        self.entry = "0"           # what's being typed (as text)
        self.typing = False        # True while digits are being entered
        self.last = None           # (op, operand) for repeated '='
        self.memory = Decimal(0)
        self.error = False

        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 6)
        v.setSpacing(6)
        bar = QMenuBar()
        bar.triggered.connect(lambda _a: sound.play("menu"))
        edit = bar.addMenu("&Edit")
        edit.addAction("&Copy", self.copy, QKeySequence("Ctrl+C"))
        edit.addAction("&Paste", self.paste, QKeySequence("Ctrl+V"))
        view = bar.addMenu("&View")
        std = view.addAction("S&tandard")
        std.setCheckable(True)
        std.setChecked(True)
        bar.addMenu("&Help").addAction("&About Calculator", self.about)
        v.addWidget(bar)
        self.display = QLineEdit("0.")
        self.display.setReadOnly(True)
        self.display.setAlignment(Qt.AlignRight)
        self.display.setFocusPolicy(Qt.NoFocus)
        body = QVBoxLayout()
        body.setContentsMargins(8, 0, 8, 0)
        body.addWidget(self.display)
        grid = QGridLayout()
        grid.setHorizontalSpacing(5)
        grid.setVerticalSpacing(5)
        self.mem_label = QLabel("")
        self.mem_label.setObjectName("mem")
        self.mem_label.setAlignment(Qt.AlignCenter)
        self.mem_label.setFixedSize(36, 26)
        grid.addWidget(self.mem_label, 0, 0)
        for col, (text, slot) in enumerate((("Backspace", self.backspace), ("CE", self.clear_entry), ("C", self.clear))):
            b = self._button(text, "clear", slot)
            grid.addWidget(b, 0, 1 + col * 2, 1, 2 if col < 2 else 3)
        rows = [("MC", "7", "8", "9", "/", "sqrt"), ("MR", "4", "5", "6", "*", "%"),
                ("MS", "1", "2", "3", "-", "1/x"), ("M+", "0", "+/-", ".", "+", "=")]
        for r, row in enumerate(rows, start=1):
            for c, text in enumerate(row):
                kind = "mem" if c == 0 else "digit" if text.isdigit() or text in "+/-." and c in (2, 3) and r == 4 \
                    else "op"
                b = self._button(text, kind, lambda _=False, t=text: self.press(t))
                b.setFixedWidth(36 if c != 0 else 36)
                grid.addWidget(b, r, c if c == 0 else c + 0, 1, 1)
        grid.setColumnMinimumWidth(0, 36)
        for c in range(1, 6):
            grid.setColumnMinimumWidth(c, 36)
        body.addLayout(grid)
        v.addLayout(body)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setFixedSize(self.sizeHint())

    def _button(self, text, kind, slot):
        b = QPushButton(text)
        b.setProperty("kind", kind)
        b.setFocusPolicy(Qt.NoFocus)
        b.clicked.connect(slot)
        return b

    # ---- the engine -----------------------------------------------------------------------------------------
    def value(self):
        try:
            return Decimal(self.entry)
        except InvalidOperation:
            return Decimal(0)

    def put(self, value=None, text=None):
        if text is not None:
            self.display.setText(text)
            return
        if value is None:
            value = self.value()
        self.display.setText(fmt(value) if not self.typing else
                             (self.entry if "." in self.entry else self.entry + "."))

    def fail(self, message):
        self.error = True
        self.acc, self.op, self.typing, self.last = None, None, False, None
        self.entry = "0"
        self.put(text=message)

    @staticmethod
    def apply(op, a, b):
        if op == "+":
            return a + b
        if op == "-":
            return a - b
        if op == "*":
            return a * b
        if b == 0:
            raise DivisionByZero
        return a / b

    def press(self, key):
        if self.error and key not in ("C", "CE"):
            self.clear()
        if key.isdigit():
            if not self.typing:
                self.entry, self.typing = "0", True
            if len(self.entry.replace("-", "").replace(".", "")) < 32:
                self.entry = key if self.entry == "0" else self.entry + key
            self.put()
        elif key == ".":
            if not self.typing:
                self.entry, self.typing = "0", True
            if "." not in self.entry:
                self.entry += "."
            self.put()
        elif key in "+-*/":
            try:
                if self.op is not None and self.typing:
                    self.acc = self.apply(self.op, self.acc, self.value())
                elif self.acc is None or self.typing or self.op is None:
                    self.acc = self.value()
            except DivisionByZero:
                self.fail("Cannot divide by zero.")
                return
            self.op, self.typing, self.last = key, False, None
            self.entry = str(self.acc)
            self.put(self.acc)
        elif key == "=":
            try:
                if self.op is not None:
                    b = self.value()
                    result = self.apply(self.op, self.acc, b)
                    self.last = (self.op, b)
                elif self.last is not None:
                    result = self.apply(self.last[0], self.value(), self.last[1])
                else:
                    result = self.value()
            except DivisionByZero:
                self.fail("Cannot divide by zero.")
                return
            self.acc, self.op, self.typing = None, None, False
            self.entry = str(result)
            self.put(result)
        elif key == "+/-":
            v = -self.value()
            if self.typing:
                self.entry = self.entry[1:] if self.entry.startswith("-") else "-" + self.entry
                self.put()
            else:
                self.entry = str(v)
                self.put(v)
        elif key in ("sqrt", "1/x", "%"):
            v = self.value()
            if key == "sqrt":
                if v < 0:
                    self.fail("Invalid input for function.")
                    return
                v = v.sqrt()
            elif key == "1/x":
                if v == 0:
                    self.fail("Cannot divide by zero.")
                    return
                v = 1 / v
            else:
                v = (self.acc or Decimal(0)) * v / 100
            self.entry, self.typing = str(v), False
            self.put(v)
        elif key == "MC":
            self.memory = Decimal(0)
        elif key == "MR":
            self.entry, self.typing = str(self.memory), False
            self.put(self.memory)
        elif key == "MS":
            self.memory = self.value()
        elif key == "M+":
            self.memory += self.value()
        self.mem_label.setText("M" if self.memory != 0 else "")

    def backspace(self):
        if self.typing and not self.error:
            self.entry = self.entry[:-1] or "0"
            if self.entry in ("-", "-0"):
                self.entry = "0"
            self.put()

    def clear_entry(self):
        self.error = False
        self.entry, self.typing = "0", False
        self.put(Decimal(0))

    def clear(self):
        self.error = False
        self.acc, self.op, self.last = None, None, None
        self.clear_entry()

    def copy(self):
        QApplication.clipboard().setText(self.display.text().rstrip("."))

    def paste(self):
        for ch in QApplication.clipboard().text().strip():
            if ch.isdigit() or ch in ".+-*/=":
                self.press(ch)

    def about(self):
        from ..explorer.dialogs import msgbox
        msgbox(self.desktop, "About Calculator", "Microsoft Calculator\nVersion 5.1 (Build 2600)\n\n"
               "This product is licensed to the user of this computer.", "info")

    def keyPressEvent(self, event):
        key, text = event.key(), event.text()
        if key in (Qt.Key_Return, Qt.Key_Enter) or text == "=":
            self.press("=")
        elif key == Qt.Key_Escape:
            self.clear()
        elif key == Qt.Key_Delete:
            self.clear_entry()
        elif key == Qt.Key_Backspace:
            self.backspace()
        elif key == Qt.Key_F9:
            self.press("+/-")
        elif text == "@":
            self.press("sqrt")
        elif text in ("r", "R"):
            self.press("1/x")
        elif text == ",":
            self.press(".")
        elif text and (text.isdigit() or text in "+-*/.%"):
            self.press(text)
        else:
            super().keyPressEvent(event)


def calc_icon():
    pm = QPixmap(32, 32)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(QPen(QColor("#404040"), 1))
    p.setBrush(QColor("#D8D4C4"))
    p.drawRoundedRect(QRectF(5.5, 2.5, 21, 27), 2, 2)
    p.setBrush(QColor("#C8F0C0"))
    p.drawRect(QRectF(8.5, 5.5, 15, 6))
    for r in range(3):
        for c in range(3):
            p.setBrush(QColor("#E04040") if c == 2 else QColor("white"))
            p.drawRect(QRectF(8.5 + c * 5.3, 14 + r * 4.8, 3.6, 3.4))
    p.end()
    return QIcon(pm)


def open_calc(desktop):
    body = Calculator(desktop)
    win = XPWindow(desktop, "Calculator", body, calc_icon(), size=(260, 260), buttons=("min", "close"))
    body.frame = win
    win.fit_fixed_content()
    desktop.open_window(win)
    body.setFocus()
    return win
