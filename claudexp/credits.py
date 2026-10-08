"""The credits window shown after logging on: the text of Thanks.txt (in the ClaudeXP folder), laid out nicely,
with OK and 'Don't show this window again'. Thanks.txt is read each time, so edits show up at the next logon."""
import html

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QIcon, QLinearGradient, QPainter, QPixmap
from PySide6.QtWidgets import QCheckBox, QHBoxLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget
from shiboken6 import isValid

from .paths import DATA, ROOT
from .programs.people import load_json, save_json
from .wm import XPWindow

THANKS_FILE = ROOT / "Thanks.txt"
SETTINGS = DATA / "credits.json"
_open = {}


def credits_icon():
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


def _read():
    try:
        return THANKS_FILE.read_text(encoding="utf-8-sig").strip()
    except OSError:
        return ""


def to_html(text):
    """'Label: value' lines become a two-column list; a comma list of names is wrapped nicely."""
    lines = [line.strip() for line in text.splitlines()]
    title = lines[0] if lines else ""
    rows, extra = [], []
    for line in lines[1:]:
        if not line:
            continue
        label, sep, value = line.partition(":")
        if sep and value.strip():
            names = [n.strip() for n in value.split(",") if n.strip()]
            if len(names) > 3:
                rows.append((label.strip(), "<br>".join(html.escape(n) for n in names)))
            else:
                rows.append((label.strip(), html.escape(value.strip())))
        else:
            extra.append(html.escape(line))
    table = "".join(
        f"<tr><td valign='top' style='padding: 4px 14px 4px 0; color: #1C3D91; white-space: nowrap;'>"
        f"<b>{html.escape(label)}</b></td><td valign='top' style='padding: 4px 0;'>{value}</td></tr>"
        for label, value in rows)
    more = "".join(f"<p>{line}</p>" for line in extra)
    return (f"<div style='font-family: Tahoma; font-size: 12px;'>"
            f"<p style='font-family: \"Trebuchet MS\"; font-size: 15px; color: #1C3D91;'><b>{html.escape(title)}</b></p>"
            f"<table cellspacing='0'>{table}</table>{more}</div>")


class Banner(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedHeight(64)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        g = QLinearGradient(0, 0, self.width(), 0)
        g.setColorAt(0, QColor("#0A2A7A"))
        g.setColorAt(1, QColor("#3A72DA"))
        p.fillRect(self.rect(), g)
        p.drawPixmap(16, 12, credits_icon().pixmap(40, 40))
        f = QFont("Franklin Gothic Medium")
        f.setPixelSize(24)
        p.setFont(f)
        p.setPen(QColor("white"))
        p.drawText(QRectF(66, 8, self.width() - 80, 30), Qt.AlignVCenter | Qt.AlignLeft, "ClaudeXP")
        f = QFont("Tahoma")
        f.setPixelSize(11)
        p.setFont(f)
        p.setPen(QColor("#D6E2FF"))
        p.drawText(QRectF(67, 36, self.width() - 80, 18), Qt.AlignVCenter | Qt.AlignLeft,
                   "Windows XP, the way you remember it")
        p.fillRect(QRectF(0, self.height() - 2, self.width(), 2), QColor("#F99736"))


def show(desktop):
    win = _open.get("win")
    if win is not None and isValid(win):
        desktop.open_window(win)
        return win
    text = _read()
    if not text:
        return None
    body = QWidget()
    body.setObjectName("credits")
    body.setAttribute(Qt.WA_StyledBackground, True)
    body.setStyleSheet("QWidget#credits { background: white; } QWidget#bottom { background: #ECE9D8; "
                       "border-top: 1px solid #ACA899; } QCheckBox, QPushButton { font-family: Tahoma; font-size: 11px; }")
    v = QVBoxLayout(body)
    v.setContentsMargins(0, 0, 0, 0)
    v.setSpacing(0)
    v.addWidget(Banner())
    label = QLabel(to_html(text))
    label.setTextFormat(Qt.RichText)
    label.setWordWrap(True)
    label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
    label.setContentsMargins(22, 14, 22, 14)
    label.setStyleSheet("background: white;")
    scroll = QScrollArea()
    scroll.setWidget(label)
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QScrollArea.NoFrame)
    v.addWidget(scroll, 1)
    bottom = QWidget()
    bottom.setObjectName("bottom")
    bottom.setAttribute(Qt.WA_StyledBackground, True)
    row = QHBoxLayout(bottom)
    row.setContentsMargins(12, 8, 12, 8)
    dont = QCheckBox("Don't show this window again")
    dont.setChecked(not load_json(SETTINGS, {}).get("show", True))
    ok = QPushButton("Ok")
    ok.setFixedSize(75, 23)
    ok.setDefault(True)
    row.addWidget(dont)
    row.addStretch()
    row.addWidget(ok)
    v.addWidget(bottom)
    win = XPWindow(desktop, "Thanks", body, credits_icon(), (440, 420), buttons=("close",))
    body.frame = win

    def close():
        save_json(SETTINGS, {"show": not dont.isChecked()})
        if isValid(win):
            desktop.close_window(win)
    ok.clicked.connect(close)
    body.closeEvent = lambda e: (save_json(SETTINGS, {"show": not dont.isChecked()}), e.accept())
    _open["win"] = win
    area = desktop.work_area()
    win.move(area.center() - win.rect().center())
    win.placed = True
    desktop.open_window(win)
    ok.setFocus()
    return win


def maybe_show(desktop):
    """At logon, unless 'Don't show this window again' was ticked."""
    if load_json(SETTINGS, {}).get("show", True):
        show(desktop)
