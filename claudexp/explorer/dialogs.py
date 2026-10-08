"""XP-style message boxes and the Properties window (with the drive pie chart)."""
from datetime import datetime

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QStyle, QVBoxLayout, QWidget

from .. import clock, sound

ICONS = {"error": QStyle.SP_MessageBoxCritical, "warning": QStyle.SP_MessageBoxWarning,
         "info": QStyle.SP_MessageBoxInformation, "question": QStyle.SP_MessageBoxQuestion}
SOUNDS = {"error": "error", "warning": "exclamation", "question": "exclamation", "info": "default"}


def msgbox(desktop, title, text, icon="error", buttons=("OK",), on_button=None, window_icon=None):
    """Show a message box; on_button(label) is called with the button pressed (or 'Cancel' for the X)."""
    from ..network import DialogBody, _fixed_window
    body = DialogBody()
    root = QVBoxLayout(body)
    root.setContentsMargins(14, 14, 14, 12)
    row = QHBoxLayout()
    pic = QLabel()
    pic.setPixmap(body.style().standardIcon(ICONS[icon]).pixmap(32, 32))
    pic.setAlignment(Qt.AlignTop)
    row.addWidget(pic)
    label = QLabel(text)
    label.setWordWrap(True)
    label.setMinimumWidth(260)
    label.setMaximumWidth(420)
    row.addWidget(label, 1)
    root.addLayout(row)
    brow = QHBoxLayout()
    brow.addStretch()
    holder = {}

    def press(name):
        win = holder.get("win")
        holder["win"] = None
        if win is not None:
            desktop.close_window(win)
        if on_button:
            on_button(name)

    for i, name in enumerate(buttons):
        b = QPushButton(name)
        b.setFixedSize(75, 23)
        b.clicked.connect(lambda _c=False, n=name: press(n))
        if i == 0:
            b.setDefault(True)
        brow.addWidget(b)
    brow.addStretch()
    root.addLayout(brow)
    win = _fixed_window(desktop, title, body, lambda: press("Cancel"))
    if window_icon is not None:
        win.icon = window_icon
    holder["win"] = win
    desktop.open_window(win)
    sound.play(SOUNDS[icon])
    return win


def system_info(desktop):
    """System Properties: the 'About this PC' box."""
    from PySide6.QtWidgets import QApplication
    from ..user import registered_owner
    owner, organization = registered_owner()
    registered = [("Registered to:", owner)] + ([("", organization)] if organization else [])
    properties(desktop, "System", [
        ("System:", "Microsoft Windows XP"), ("", "Home Edition"), ("", "Version 2002"), ("-", ""),
        *registered, ("", "55274-OEM-0011903-00102"), ("-", ""),
        ("Computer:", "Intel(R) Pentium(R) III processor"), ("", "866 MHz"), ("", "256 MB of RAM")],
        icon=QApplication.style().standardIcon(QStyle.SP_ComputerIcon))


def size_text(n):
    if n >= 2**30:
        return f"{n / 2**30:.2f} GB"
    if n >= 2**20:
        return f"{n / 2**20:.1f} MB"
    if n >= 1024:
        return f"{max(1, round(n / 1024)):,} KB"
    return f"{n} bytes"


def date_2001(timestamp):
    """A real file time, shown in ClaudeXP's always-2001 calendar."""
    dt = datetime.fromtimestamp(timestamp)
    try:
        dt = dt.replace(year=clock.YEAR)
    except ValueError:
        dt = dt.replace(year=clock.YEAR, day=28)
    return f"{dt:%A, %B} {dt.day}, {dt.year}, {clock.time_text(dt)}"


def short_date_2001(timestamp):
    """Explorer's Date Modified column: 8/1/2001 5:32 AM."""
    dt = datetime.fromtimestamp(timestamp)
    try:
        dt = dt.replace(year=clock.YEAR)
    except ValueError:
        dt = dt.replace(year=clock.YEAR, day=28)
    return f"{dt.month}/{dt.day}/{dt.year} {clock.time_text(dt)}"


class Pie(QWidget):
    def __init__(self, used, free):
        super().__init__()
        self.used, self.free = used, free
        self.setFixedSize(150, 90)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        total = max(1, self.used + self.free)
        rect = QRectF(10, 8, 130, 60)
        depth = 14
        used_angle = int(360 * 16 * self.used / total)
        for dy in range(depth, 0, -1):   # the 3D edge
            r = rect.translated(0, dy)
            p.setPen(Qt.NoPen)
            p.setBrush(QColor("#00007F"))
            p.drawPie(r, 90 * 16, -used_angle)
            p.setBrush(QColor("#7F007F"))
            p.drawPie(r, 90 * 16 - used_angle, -(360 * 16 - used_angle))
        p.setPen(QPen(QColor("black"), 1))
        p.setBrush(QColor("#0000FF"))
        p.drawPie(rect, 90 * 16, -used_angle)
        p.setBrush(QColor("#FF00FF"))
        p.drawPie(rect, 90 * 16 - used_angle, -(360 * 16 - used_angle))


def properties(desktop, title, rows, usage=None, icon=None):
    """A General-tab style Properties window. rows: [(label, value)]; usage: (used, free) for a drive."""
    from ..network import DialogBody, _fixed_window
    body = DialogBody()
    root = QVBoxLayout(body)
    root.setContentsMargins(14, 12, 14, 12)
    tab = QLabel("  General  ")
    tab.setStyleSheet("background: white; border: 1px solid #919B9C; border-bottom: none; padding: 2px;")
    tab.setFixedWidth(70)
    root.addWidget(tab)
    page = QFrame()
    page.setStyleSheet("QFrame { background: #FCFCFE; border: 1px solid #919B9C; } QLabel { border: none; }")
    grid = QGridLayout(page)
    grid.setContentsMargins(12, 12, 12, 12)
    r = 0
    if icon is not None:
        pic = QLabel()
        pic.setPixmap(icon.pixmap(32, 32))
        grid.addWidget(pic, r, 0)
        name = QLabel(title)
        name.setStyleSheet("border: 1px solid #7F9DB9; background: white; padding: 2px;")
        grid.addWidget(name, r, 1, 1, 2)
        r += 1
    for label, value in rows:
        if label == "-":
            line = QFrame()
            line.setFrameShape(QFrame.HLine)
            line.setStyleSheet("border-top: 1px solid #D0D0BF;")
            grid.addWidget(line, r, 0, 1, 3)
        else:
            grid.addWidget(QLabel(label), r, 0)
            v = QLabel(value)
            v.setTextInteractionFlags(Qt.TextSelectableByMouse)
            grid.addWidget(v, r, 1, 1, 2)
        r += 1
    if usage is not None:
        used, free = usage
        for color, label, value in (("#0000FF", "Used space:", used), ("#FF00FF", "Free space:", free)):
            sw = QLabel()
            sw.setFixedSize(14, 14)
            sw.setStyleSheet(f"background: {color}; border: 1px solid black;")
            row = QHBoxLayout()
            row.addWidget(sw)
            row.addWidget(QLabel(label))
            grid.addLayout(row, r, 0)
            grid.addWidget(QLabel(f"{value:,} bytes"), r, 1)
            grid.addWidget(QLabel(size_text(value)), r, 2)
            r += 1
        grid.addWidget(QLabel("Capacity:"), r, 0)
        grid.addWidget(QLabel(f"{used + free:,} bytes"), r, 1)
        grid.addWidget(QLabel(size_text(used + free)), r, 2)
        r += 1
        pie = Pie(used, free)
        grid.addWidget(pie, r, 0, 1, 3, Qt.AlignCenter)
    root.addWidget(page)
    brow = QHBoxLayout()
    brow.addStretch()
    ok = QPushButton("OK")
    ok.setFixedSize(75, 23)
    brow.addWidget(ok)
    root.addLayout(brow)
    body.setFixedWidth(360)
    holder = {}

    def close():
        if holder.get("win") is not None:
            desktop.close_window(holder.pop("win"))

    ok.clicked.connect(close)
    holder["win"] = _fixed_window(desktop, f"{title} Properties", body, close)
    if icon is not None:
        holder["win"].icon = icon
    desktop.open_window(holder["win"])
