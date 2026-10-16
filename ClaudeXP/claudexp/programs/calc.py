"""Calculator, like Windows XP's. Standard view: the '0.' display, Backspace/CE/C, memory (MC MR MS M+), sqrt,
%, 1/x, +/-, repeated '=', worked left to right (2+3*4 = 20). Scientific view: operator precedence and brackets
(2+3*4 = 14), Hex/Dec/Oct/Bin, Degrees/Radians/Grads, Inv and Hyp, sin/cos/tan, ln/log, x^y, x^2, x^3, n!, dms,
Exp, F-E, pi, Mod, And/Or/Xor/Lsh/Not, Int. Edit > Copy/Paste, View > Digit grouping, keyboard input."""
import math
from decimal import Decimal, DivisionByZero, InvalidOperation, getcontext

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QAction, QActionGroup, QColor, QIcon, QKeySequence, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (QApplication, QButtonGroup, QCheckBox, QGridLayout, QHBoxLayout, QLabel, QLineEdit,
                               QMenuBar, QPushButton, QRadioButton, QVBoxLayout, QWidget)

from .. import sound
from ..paths import DATA
from ..wm import XPWindow
from .notepad import MENU_STYLE
from .people import load_json, save_json

getcontext().prec = 32
SETTINGS = DATA / "calc.json"

STYLE = MENU_STYLE + """
QWidget#calc { background: #ECE9D8; }
QLineEdit { font-family: Tahoma; font-size: 13px; background: white; border: 1px solid #7F9DB9; padding: 2px 4px; }
QPushButton { font-family: Tahoma; font-size: 11px; min-height: 24px; }
QPushButton[kind="op"], QPushButton[kind="clear"], QPushButton[kind="mem"] { color: #D00000; }
QPushButton[kind="digit"] { color: #0000C0; }
QPushButton[kind="fn"] { color: #800080; }
QPushButton:disabled { color: #A0A0A0; }
QLabel#mem, QLabel#paren { border: 1px solid #ACA899; background: #ECE9D8; font-family: Tahoma; font-size: 11px; }
QRadioButton, QCheckBox { font-family: Tahoma; font-size: 11px; }
"""
# precedence in the Scientific view (Standard works strictly left to right)
PREC = {"Or": 1, "Xor": 2, "And": 3, "Lsh": 4, "+": 5, "-": 5, "*": 6, "/": 6, "Mod": 6, "^": 7, "yroot": 7}
BINARY = set(PREC)
BITS = 64
BASES = {"Hex": 16, "Dec": 10, "Oct": 8, "Bin": 2}


class CalcError(Exception):
    pass


def fmt_dec(value, grouping=False, sci=False):
    """XP shows integers with a trailing point: '0.', '42.'."""
    if sci or (value != 0 and (abs(value) >= Decimal(10) ** 32 or abs(value) < Decimal(10) ** -30)):
        mant, _, exp = f"{value:.15e}".partition("e")
        mant = mant.rstrip("0")
        return f"{mant if '.' in mant else mant + '.'}e{'+' if int(exp) >= 0 else '-'}{abs(int(exp))}"
    if value == value.to_integral_value():
        text = f"{int(value):,}" if grouping else f"{int(value)}"
        return text + "."
    text = format(value.normalize(), "f")
    if grouping:
        whole, _, frac = text.partition(".")
        sign = "-" if whole.startswith("-") else ""
        text = f"{sign}{int(whole.lstrip('-') or 0):,}.{frac}"
    return text


def to_int(value):
    """Integer modes use 64-bit two's complement like XP's Qword."""
    n = int(value)
    n &= (1 << BITS) - 1
    return n - (1 << BITS) if n >= 1 << (BITS - 1) else n


class Calculator(QWidget):
    def __init__(self, desktop):
        super().__init__()
        self.desktop = desktop
        self.frame = None
        self.setObjectName("calc")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(STYLE)
        settings = load_json(SETTINGS, {})
        self.scientific = bool(settings.get("scientific", False))
        self.grouping = bool(settings.get("grouping", False))
        self.base = "Dec"
        self.angle = "Degrees"
        self.sci_notation = False
        self.vals, self.ops = [], []
        self.entry, self.typing, self.after_op = "0", False, False
        self.last = None            # (op, operand) for repeated '='
        self.memory = Decimal(0)
        self.error = False
        self.buttons = {}           # label -> [QPushButton] (both views)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 6)
        root.setSpacing(6)
        bar = QMenuBar()
        bar.triggered.connect(lambda _a: sound.play("menu"))
        edit = bar.addMenu("&Edit")
        edit.addAction("&Copy", self.copy, QKeySequence("Ctrl+C"))
        edit.addAction("&Paste", self.paste, QKeySequence("Ctrl+V"))
        view = bar.addMenu("&View")
        group = QActionGroup(self)
        self.std_act = QAction("S&tandard", self, checkable=True, checked=not self.scientific)
        self.sci_act = QAction("&Scientific", self, checkable=True, checked=self.scientific)
        for act, sci in ((self.std_act, False), (self.sci_act, True)):
            act.triggered.connect(lambda _c=False, s=sci: self.set_view(s))
            group.addAction(act)
            view.addAction(act)
        view.addSeparator()
        grp = QAction("Digit &grouping", self, checkable=True, checked=self.grouping)
        grp.toggled.connect(self._set_grouping)
        view.addAction(grp)
        bar.addMenu("&Help").addAction("&About Calculator", self.about)
        root.addWidget(bar)
        self.display = QLineEdit("0.")
        self.display.setReadOnly(True)
        self.display.setAlignment(Qt.AlignRight)
        self.display.setFocusPolicy(Qt.NoFocus)
        body = QVBoxLayout()
        body.setContentsMargins(8, 0, 8, 0)
        body.setSpacing(6)
        body.addWidget(self.display)
        self.std_panel = self._standard_panel()
        self.sci_panel = self._scientific_panel()
        body.addWidget(self.std_panel)
        body.addWidget(self.sci_panel)
        root.addLayout(body)
        self.setFocusPolicy(Qt.StrongFocus)
        self.set_view(self.scientific, save=False)

    # ---- panels ---------------------------------------------------------------------------------------------
    def _button(self, text, kind, slot=None, width=36):
        b = QPushButton(text)
        b.setProperty("kind", kind)
        b.setFocusPolicy(Qt.NoFocus)
        b.setFixedWidth(width)
        b.clicked.connect(slot or (lambda _=False, t=text: self.press(t)))
        self.buttons.setdefault(text, []).append(b)
        return b

    def _mem_label(self, name="mem"):
        lab = QLabel("")
        lab.setObjectName(name)
        lab.setAlignment(Qt.AlignCenter)
        lab.setFixedSize(36, 24)
        return lab

    def _standard_panel(self):
        w = QWidget()
        grid = QGridLayout(w)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(5)
        grid.setVerticalSpacing(5)
        self.mem_std = self._mem_label()
        grid.addWidget(self.mem_std, 0, 0)
        for col, (text, slot) in enumerate((("Backspace", self.backspace), ("CE", self.clear_entry), ("C", self.clear))):
            grid.addWidget(self._button(text, "clear", slot, 77 if col < 2 else 77), 0, 1 + col * 2, 1, 2)
        rows = [("MC", "7", "8", "9", "/", "sqrt"), ("MR", "4", "5", "6", "*", "%"),
                ("MS", "1", "2", "3", "-", "1/x"), ("M+", "0", "+/-", ".", "+", "=")]
        for r, row in enumerate(rows, start=1):
            for c, text in enumerate(row):
                kind = "mem" if c == 0 else "digit" if (text.isdigit() or (r == 4 and c in (2, 3))) else "op"
                grid.addWidget(self._button(text, kind), r, c)
        return w

    def _scientific_panel(self):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(5)
        top = QHBoxLayout()
        self.base_group = QButtonGroup(self)
        for name in BASES:
            r = QRadioButton(name)
            r.setChecked(name == "Dec")
            r.setFocusPolicy(Qt.NoFocus)
            r.toggled.connect(lambda on, n=name: on and self.set_base(n))
            self.base_group.addButton(r)
            top.addWidget(r)
        top.addSpacing(16)
        self.angle_group = QButtonGroup(self)
        self.angle_radios = {}
        for name in ("Degrees", "Radians", "Grads"):
            r = QRadioButton(name)
            r.setChecked(name == "Degrees")
            r.setFocusPolicy(Qt.NoFocus)
            r.toggled.connect(lambda on, n=name: on and setattr(self, "angle", n))
            self.angle_group.addButton(r)
            self.angle_radios[name] = r
            top.addWidget(r)
        top.addStretch()
        v.addLayout(top)
        row = QHBoxLayout()
        self.inv = QCheckBox("Inv")
        self.hyp = QCheckBox("Hyp")
        for box in (self.inv, self.hyp):
            box.setFocusPolicy(Qt.NoFocus)
            row.addWidget(box)
        row.addStretch()
        self.paren_label = self._mem_label("paren")
        row.addWidget(self.paren_label)
        for text, slot in (("Backspace", self.backspace), ("CE", self.clear_entry), ("C", self.clear)):
            row.addWidget(self._button(text, "clear", slot, 70))
        v.addLayout(row)
        grid = QGridLayout()
        grid.setHorizontalSpacing(4)
        grid.setVerticalSpacing(4)
        fn_rows = [("F-E", "(", ")"), ("dms", "Exp", "ln"), ("sin", "x^y", "log"), ("cos", "x^3", "n!"),
                   ("tan", "x^2", "1/x")]
        for r, labels in enumerate(fn_rows):
            for c, text in enumerate(labels):
                grid.addWidget(self._button(text, "fn"), r, c)
        self.mem_sci = self._mem_label()
        grid.addWidget(self.mem_sci, 0, 3)
        for r, text in enumerate(("MC", "MR", "MS", "M+"), start=1):
            grid.addWidget(self._button(text, "mem"), r, 3)
        pad = [("7", "8", "9", "/", "Mod", "And"), ("4", "5", "6", "*", "Or", "Xor"),
               ("1", "2", "3", "-", "Lsh", "Not"), ("0", "+/-", ".", "+", "=", "Int"),
               ("A", "B", "C ", "D", "E", "F")]
        for r, labels in enumerate(pad):
            for c, text in enumerate(labels):
                kind = "digit" if (text.strip().isalnum() and len(text.strip()) == 1) or text in ("+/-", ".") else "op"
                key = text.strip()
                grid.addWidget(self._button(text, kind, lambda _=False, t=key: self.press(t)), r, 4 + c)
        grid.addWidget(self._button("pi", "fn"), 4, 3)
        v.addLayout(grid)
        return w

    def set_view(self, scientific, save=True):
        self.scientific = scientific
        self.std_panel.setVisible(not scientific)
        self.sci_panel.setVisible(scientific)
        if not scientific and self.base != "Dec":
            self.base_group.buttons()[1].setChecked(True)
        self.clear()
        self.setMinimumSize(0, 0)
        self.setMaximumSize(16777215, 16777215)
        self.adjustSize()
        self.setFixedSize(self.sizeHint())
        if self.frame is not None:
            self.frame.fit_fixed_content()
        if save:
            self._save()
        self._update_buttons()

    def _set_grouping(self, on):
        self.grouping = on
        self._save()
        self.put()

    def _save(self):
        save_json(SETTINGS, {"scientific": self.scientific, "grouping": self.grouping})

    def _update_buttons(self):
        base = BASES[self.base]
        decimal_only = {".", "sin", "cos", "tan", "dms", "Exp", "ln", "log", "F-E", "pi", "1/x", "sqrt", "%"}
        for label, buttons in self.buttons.items():
            if label in ("C", "CE", "Backspace"):       # the clear keys ('C ' with a space is the hex digit)
                continue
            key = label.strip()
            if len(key) == 1 and key.isalnum():
                enabled = int(key, 16) < base
            else:
                enabled = self.base == "Dec" or key not in decimal_only
            for b in buttons:
                b.setEnabled(enabled)
        for r in self.angle_radios.values():
            r.setEnabled(self.base == "Dec")

    # ---- the engine ----------------------------------------------------------------------------------------------
    def value(self):
        try:
            if self.base != "Dec":
                return Decimal(to_int(int(self.entry or "0", BASES[self.base])))
            return Decimal(self.entry)
        except (InvalidOperation, ValueError):
            return Decimal(0)

    def text_for(self, value):
        if self.base != "Dec":
            n = to_int(value) & ((1 << BITS) - 1)
            return {"Hex": f"{n:X}", "Oct": f"{n:o}", "Bin": f"{n:b}"}[self.base]
        return fmt_dec(value, self.grouping, self.sci_notation)

    def put(self, value=None, text=None):
        if text is not None:
            self.display.setText(text)
            return
        if self.typing:
            shown = self.entry
            if self.base == "Dec" and "e" not in shown.lower():
                if self.grouping:
                    whole, dot, frac = shown.partition(".")
                    sign = "-" if whole.startswith("-") else ""
                    shown = f"{sign}{int(whole.lstrip('-') or 0):,}" + (dot + frac)
                if "." not in shown:
                    shown += "."
            self.display.setText(shown)
        else:
            self.display.setText(self.text_for(self.value() if value is None else value))
        self.paren_label.setText(f"(={self.ops.count('(')}" if self.ops.count("(") else "")

    def fail(self, message):
        self.error = True
        self.vals, self.ops, self.last = [], [], None
        self.entry, self.typing, self.after_op = "0", False, False
        self.put(text=message)

    def set_result(self, v):
        if self.base != "Dec":
            v = Decimal(to_int(v))
        self.entry = (format(to_int(v) & ((1 << BITS) - 1), {"Hex": "X", "Oct": "o", "Bin": "b"}[self.base])
                      if self.base != "Dec" else str(v))
        self.typing = False
        self.put(v)

    def apply(self, op, a, b):
        ints = self.base != "Dec" or op in ("And", "Or", "Xor", "Lsh")
        if op == "+":
            r = a + b
        elif op == "-":
            r = a - b
        elif op == "*":
            r = a * b
        elif op == "/":
            if b == 0:
                raise DivisionByZero
            r = a / b
            if self.base != "Dec":
                r = Decimal(int(r))
        elif op == "Mod":
            if b == 0:
                raise DivisionByZero
            r = a % b
        elif op == "^":
            try:
                r = Decimal(str(float(a) ** float(b))) if b != b.to_integral_value() or abs(b) > 500 else a ** int(b)
            except (OverflowError, ValueError, ZeroDivisionError):
                raise CalcError("Invalid input for function.")
            if isinstance(r, complex):
                raise CalcError("Invalid input for function.")
        elif op == "yroot":
            if b == 0 or (a < 0 and int(b) % 2 == 0):
                raise CalcError("Invalid input for function.")
            r = Decimal(str((-1 if a < 0 else 1) * abs(float(a)) ** (1 / float(b))))
        else:
            x, y = to_int(a), to_int(b)
            r = Decimal({"And": x & y, "Or": x | y, "Xor": x ^ y, "Lsh": x << y if y >= 0 else x >> -y}[op])
        return Decimal(to_int(r)) if ints else r

    def prec(self, op):
        return PREC[op] if self.scientific else 1

    def reduce(self, stop_at_paren=True, until_prec=None, right_assoc=False):
        while self.ops and self.ops[-1] != "(":
            top = self.ops[-1]
            if until_prec is not None:
                p = self.prec(top)
                if p < until_prec or (p == until_prec and right_assoc):
                    break
            self.ops.pop()
            b = self.vals.pop()
            a = self.vals.pop()
            self.vals.append(self.apply(top, a, b))

    def binary(self, op):
        if self.after_op and self.ops and self.ops[-1] != "(":
            self.ops[-1] = op                    # changed their mind about the operator
            return
        self.vals.append(self.value())
        self.reduce(until_prec=self.prec(op), right_assoc=op in ("^", "yroot"))
        self.ops.append(op)
        self.after_op, self.typing = True, False
        self.last = None
        self.set_result(self.vals[-1])
        self.after_op = True

    def equals(self):
        if not self.ops and self.last is not None:
            op, b = self.last
            self.set_result(self.apply(op, self.value(), b))
            return
        if not self.ops:
            self.set_result(self.value())
            return
        b = self.value()
        self.vals.append(b)
        last_op = next((o for o in reversed(self.ops) if o != "("), None)
        while self.ops:
            if self.ops[-1] == "(":
                self.ops.pop()
                continue
            self.reduce()
        result = self.vals.pop()
        self.vals, self.ops = [], []
        self.last = (last_op, b) if last_op else None
        self.after_op = False
        self.set_result(result)

    def unary(self, key):
        v = self.value()
        inv, hyp = self.inv.isChecked(), self.hyp.isChecked()
        f = float(v)
        to_rad = {"Degrees": math.pi / 180, "Radians": 1, "Grads": math.pi / 200}[self.angle]
        try:
            if key == "sqrt":
                if v < 0:
                    raise CalcError("Invalid input for function.")
                r = v.sqrt()
            elif key == "%":
                r = (self.vals[-1] if self.vals else Decimal(0)) * v / 100
            elif key == "1/x":
                if v == 0:
                    raise DivisionByZero
                r = 1 / v
            elif key in ("sin", "cos", "tan"):
                if hyp:
                    fn = {"sin": (math.sinh, math.asinh), "cos": (math.cosh, math.acosh), "tan": (math.tanh, math.atanh)}[key]
                    r = fn[1](f) if inv else fn[0](f)
                elif inv:
                    r = {"sin": math.asin, "cos": math.acos, "tan": math.atan}[key](f) / to_rad
                else:
                    r = {"sin": math.sin, "cos": math.cos, "tan": math.tan}[key](f * to_rad)
                    if abs(r) < 1e-15:
                        r = 0.0
                r = Decimal(repr(round(r, 15)))
            elif key == "ln":
                r = Decimal(repr(math.exp(f))) if inv else v.ln() if v > 0 else self._bad()
            elif key == "log":
                r = Decimal(10) ** v if inv else v.log10() if v > 0 else self._bad()
            elif key == "x^2":
                r = v.sqrt() if inv else v * v
            elif key == "x^3":
                r = Decimal(repr(math.copysign(abs(f) ** (1 / 3), f))) if inv else v * v * v
            elif key == "n!":
                if v != v.to_integral_value() or v < 0 or v > 3000:
                    self._bad()
                r = Decimal(math.factorial(int(v)))
            elif key == "dms":
                if inv:
                    deg = int(v)
                    rest = (abs(v) - abs(deg)) * 100
                    minutes = int(rest)
                    seconds = (rest - minutes) * 100
                    r = Decimal(deg) + (Decimal(minutes) / 60 + seconds / 3600) * (1 if v >= 0 else -1)
                else:
                    deg = int(v)
                    frac = abs(v - deg) * 60
                    minutes = int(frac)
                    seconds = (frac - minutes) * 60
                    r = Decimal(deg) + (Decimal(minutes) + seconds / 100) / 100 * (1 if v >= 0 else -1)
            elif key == "Int":
                r = v - int(v) if inv else Decimal(int(v))
            elif key == "Not":
                r = Decimal(~to_int(v))
            elif key == "pi":
                r = Decimal("6.283185307179586476925286766559") if inv else Decimal("3.1415926535897932384626433832795")
            else:
                return
        except DivisionByZero:
            return self.fail("Cannot divide by zero.")
        except (CalcError, ValueError, OverflowError, InvalidOperation):
            return self.fail("Invalid input for function.")
        self.inv.setChecked(False)
        self.hyp.setChecked(False)
        self.after_op = False
        self.set_result(r)

    @staticmethod
    def _bad():
        raise CalcError

    def press(self, key):
        if self.error and key not in ("C", "CE"):
            self.clear()
        base = BASES[self.base]
        try:
            if len(key) == 1 and key.isalnum() and int(key, 16) < base:
                if not self.typing:
                    self.entry, self.typing, self.after_op = "0", True, False
                limit = 32 if self.base == "Dec" else {16: 16, 8: 22, 2: 64}[base]
                digits = self.entry.replace("-", "").replace(".", "").split("e")[0]
                if len(digits) < limit:
                    self.entry = key if self.entry == "0" else self.entry + key
                self.put()
            elif key == "." and self.base == "Dec":
                if not self.typing:
                    self.entry, self.typing, self.after_op = "0", True, False
                if "." not in self.entry and "e" not in self.entry:
                    self.entry += "."
                self.put()
            elif key == "Exp" and self.base == "Dec":
                if "e" not in self.entry:
                    self.entry = (self.entry if self.typing else self.text_for(self.value()).rstrip(".")) + "e+0"
                    self.entry = self.entry.replace("e+0", "e+")
                    self.typing = True
                self.put()
            elif key == "x^y":
                self.binary("yroot" if self.inv.isChecked() else "^")
                self.inv.setChecked(False)
            elif key in BINARY:
                self.binary(key)
            elif key == "=":
                self.equals()
            elif key == "(":
                self.ops.append("(")
                self.entry, self.typing, self.after_op = "0", False, False
                self.put(Decimal(0))
            elif key == ")":
                if "(" not in self.ops:
                    return
                self.vals.append(self.value())
                self.reduce()
                self.ops.pop()
                self.after_op = False
                self.set_result(self.vals.pop())
            elif key == "+/-":
                if self.typing and "e" in self.entry:
                    m, _, e = self.entry.partition("e")
                    self.entry = m + "e" + ("-" + e[1:] if e.startswith("+") else "+" + e[1:])
                    self.put()
                elif self.typing:
                    self.entry = self.entry[1:] if self.entry.startswith("-") else "-" + self.entry
                    self.put()
                else:
                    self.set_result(-self.value())
            elif key == "F-E":
                self.sci_notation = not self.sci_notation
                self.put()
            elif key in ("sqrt", "%", "1/x", "sin", "cos", "tan", "ln", "log", "x^2", "x^3", "n!", "dms", "Int",
                         "Not", "pi"):
                self.unary(key)
            elif key == "MC":
                self.memory = Decimal(0)
            elif key == "MR":
                self.after_op = False
                self.set_result(self.memory)
            elif key == "MS":
                self.memory = self.value()
            elif key == "M+":
                self.memory += self.value()
        except DivisionByZero:
            return self.fail("Cannot divide by zero.")
        except (CalcError, InvalidOperation, OverflowError):
            return self.fail("Invalid input for function.")
        for lab in (self.mem_std, self.mem_sci):
            lab.setText("M" if self.memory != 0 else "")

    def set_base(self, name):
        v = self.value()
        self.base = name
        if name != "Dec":
            v = Decimal(to_int(v))
        self.vals, self.ops = [], []
        self.after_op = False
        self.set_result(v)
        self._update_buttons()

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
        self.vals, self.ops, self.last = [], [], None
        self.after_op = False
        self.clear_entry()

    def copy(self):
        QApplication.clipboard().setText(self.display.text().rstrip(".").replace(",", ""))

    def paste(self):
        for ch in QApplication.clipboard().text().strip():
            if ch.isalnum() or ch in ".+-*/=()":
                self.press(ch.upper() if ch.isalpha() else ch)

    def about(self):
        from ..explorer.dialogs import msgbox
        msgbox(self.desktop, "About Calculator", "Microsoft Calculator\nVersion 5.1 (Build 2600)\n\n"
               "This product is licensed to the user of this computer.", "info")

    def keyPressEvent(self, event):
        key, text = event.key(), event.text()
        mapping = {"@": "sqrt", "r": "1/x", "R": "1/x", ",": ".", "(": "(", ")": ")", "^": "x^y", "!": "n!",
                   "%": "Mod" if self.scientific else "%", "&": "And", "|": "Or", "~": "Not", "<": "Lsh",
                   "s": "sin", "o": "cos", "t": "tan", "n": "ln", "l": "log", "p": "pi", ";": "Int"}
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
        elif text and text.upper() in "ABCDEF" and self.base == "Hex":
            self.press(text.upper())
        elif text in mapping and (self.scientific or mapping[text] in ("sqrt", "1/x", ".", "%")):
            self.press(mapping[text])
        elif text and (text.isdigit() or text in "+-*/."):
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
