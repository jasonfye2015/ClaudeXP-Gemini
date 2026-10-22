"""Windows 7 message boxes and Properties windows - the same functions as ClaudeXP's explorer.dialogs, which the
period programs call for their boxes (the date helpers keep their old names: they show this computer's 2011)."""
from datetime import datetime

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QStyle, QTabWidget, QVBoxLayout,
                               QWidget)

from . import clock, sound

ICONS = {"error": QStyle.SP_MessageBoxCritical, "warning": QStyle.SP_MessageBoxWarning,
         "info": QStyle.SP_MessageBoxInformation, "question": QStyle.SP_MessageBoxQuestion}
SOUNDS = {"error": "critical", "warning": "exclamation", "question": "exclamation", "info": "default"}


def msgbox(desktop, title, text, icon="error", buttons=("OK",), on_button=None, window_icon=None):
    """Show a message box; on_button(label) is called with the button pressed (or 'Cancel' for the X)."""
    from .network import DialogBody, _fixed_window
    body = DialogBody()
    root = QVBoxLayout(body)
    root.setContentsMargins(0, 0, 0, 0)
    root.setSpacing(0)
    top = QWidget()
    top.setStyleSheet("background: white;")
    top.setAttribute(Qt.WA_StyledBackground, True)
    row = QHBoxLayout(top)
    row.setContentsMargins(16, 18, 16, 18)
    row.setSpacing(14)
    pic = QLabel()
    pic.setPixmap(body.style().standardIcon(ICONS.get(icon, QStyle.SP_MessageBoxInformation)).pixmap(32, 32))
    pic.setAlignment(Qt.AlignTop)
    row.addWidget(pic)
    label = QLabel(text)
    label.setWordWrap(True)
    label.setMinimumWidth(280)
    label.setMaximumWidth(440)
    label.setStyleSheet("font-size: 12px; background: white;")
    row.addWidget(label, 1)
    root.addWidget(top)
    footer = QWidget()
    footer.setAttribute(Qt.WA_StyledBackground, True)
    footer.setStyleSheet("background: #F0F0F0; border-top: 1px solid #DFDFDF;")
    brow = QHBoxLayout(footer)
    brow.setContentsMargins(12, 10, 12, 10)
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
        b.setMinimumWidth(80)
        b.setFixedHeight(24)
        b.clicked.connect(lambda _c=False, n=name: press(n))
        if i == 0:
            b.setDefault(True)
        brow.addWidget(b)
    root.addWidget(footer)
    win = _fixed_window(desktop, title, body, lambda: press("Cancel"))
    if window_icon is not None:
        win.icon = window_icon
    holder["win"] = win
    desktop.open_window(win)
    sound.play(SOUNDS.get(icon, "default"))
    return win


def system_info(desktop):
    """Control Panel > System: the 'View basic information about your computer' page."""
    from PySide6.QtWidgets import QApplication
    from .user import computer_name, registered_owner
    owner, _org = registered_owner()
    properties(desktop, "System", [
        ("Windows edition", ""), ("", "Windows 7 Home Premium"),
        ("", "Copyright © 2009 Microsoft Corporation.  All rights reserved."), ("", "Service Pack 1"), ("-", ""),
        ("System", ""), ("Rating:", "7.4  Windows Experience Index"),
        ("Processor:", "Intel(R) Core(TM) i5-2500K CPU @ 3.30GHz  3.30 GHz"),
        ("Installed memory (RAM):", "8.00 GB"), ("System type:", "64-bit Operating System"),
        ("Pen and Touch:", "No Pen or Touch Input is available for this Display"), ("-", ""),
        ("Computer name, domain, and workgroup settings", ""), ("Computer name:", computer_name()),
        ("Full computer name:", computer_name()), ("Workgroup:", "WORKGROUP"), ("-", ""),
        ("Windows activation", ""), ("", "Windows is activated"),
        ("Product ID:", "00359-OEM-8992687-00010"), ("Registered to:", owner)],
        icon=QApplication.style().standardIcon(QStyle.SP_ComputerIcon), tab=None)


def size_text(n):
    if n >= 2**30:
        return f"{n / 2**30:.2f} GB"
    if n >= 2**20:
        return f"{n / 2**20:.1f} MB"
    if n >= 1024:
        return f"{max(1, round(n / 1024)):,} KB"
    return f"{n} bytes"


def date_2001(timestamp):
    """A real file time, shown on this computer's calendar (it's 2011 here; the name is ClaudeXP's)."""
    dt = datetime.fromtimestamp(timestamp)
    try:
        dt = dt.replace(year=clock.YEAR)
    except ValueError:
        dt = dt.replace(year=clock.YEAR, day=28)
    return f"{dt:%A, %B} {dt.day}, {dt.year}, {clock.time_text(dt)}"


def short_date_2001(timestamp):
    dt = datetime.fromtimestamp(timestamp)
    try:
        dt = dt.replace(year=clock.YEAR)
    except ValueError:
        dt = dt.replace(year=clock.YEAR, day=28)
    return f"{dt.month}/{dt.day}/{dt.year} {clock.time_text(dt)}"


date_2011 = date_2001
short_date_2011 = short_date_2001


class Pie(QWidget):
    """Windows 7's drive usage: a flat blue/white ring."""

    def __init__(self, used, free):
        super().__init__()
        self.used, self.free = used, free
        self.setFixedSize(150, 100)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        total = max(1, self.used + self.free)
        rect = QRectF(35, 10, 80, 80)
        used_angle = int(360 * 16 * self.used / total)
        p.setPen(QPen(QColor("#7F7F7F"), 1))
        p.setBrush(QColor("#2E5FCE"))
        p.drawPie(rect, 90 * 16, -used_angle)
        p.setBrush(QColor("#F0F0F0"))
        p.drawPie(rect, 90 * 16 - used_angle, -(360 * 16 - used_angle))
        p.setBrush(QColor("#F0F0F0"))
        p.setPen(Qt.NoPen)
        p.drawEllipse(rect.adjusted(22, 22, -22, -22))


def properties(desktop, title, rows, usage=None, icon=None, tab="General"):
    """A Properties window; rows: [(label, value)] ('-' is a separator, a label with no value a heading);
    usage: (used, free) for a drive."""
    from .network import DialogBody, _fixed_window
    body = DialogBody()
    root = QVBoxLayout(body)
    root.setContentsMargins(12, 10, 12, 12)
    page = QWidget()
    page.setStyleSheet("background: white;")
    page.setAttribute(Qt.WA_StyledBackground, True)
    grid = QGridLayout(page)
    grid.setContentsMargins(14, 14, 14, 14)
    grid.setHorizontalSpacing(18)
    r = 0
    if icon is not None:
        pic = QLabel()
        pic.setPixmap(icon.pixmap(32, 32))
        grid.addWidget(pic, r, 0)
        name = QLabel(title)
        name.setStyleSheet("font-size: 14px; color: #1E3B5A;")
        grid.addWidget(name, r, 1, 1, 2)
        r += 1
    for label, value in rows:
        if label == "-":
            line = QFrame()
            line.setFrameShape(QFrame.HLine)
            line.setStyleSheet("color: #D5D5D5;")
            grid.addWidget(line, r, 0, 1, 3)
        elif label and not value:
            head = QLabel(label)
            head.setStyleSheet("font-size: 13px; color: #1E3B5A; margin-top: 4px;")
            grid.addWidget(head, r, 0, 1, 3)
        else:
            lab = QLabel(label)
            lab.setStyleSheet("color: #5A5A5A;")
            grid.addWidget(lab, r, 0)
            v = QLabel(value)
            v.setTextInteractionFlags(Qt.TextSelectableByMouse)
            grid.addWidget(v, r, 1, 1, 2)
        r += 1
    if usage is not None:
        used, free = usage
        for color, label, value in (("#2E5FCE", "Used space:", used), ("#F0F0F0", "Free space:", free)):
            sw = QLabel()
            sw.setFixedSize(14, 14)
            sw.setStyleSheet(f"background: {color}; border: 1px solid #7F7F7F;")
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
        grid.addWidget(Pie(used, free), r, 0, 1, 3, Qt.AlignCenter)
    if tab:
        tabs = QTabWidget()
        tabs.addTab(page, tab)
        root.addWidget(tabs)
    else:
        root.addWidget(page)
    brow = QHBoxLayout()
    brow.addStretch()
    ok = QPushButton("OK")
    ok.setFixedSize(80, 24)
    brow.addWidget(ok)
    root.addLayout(brow)
    body.setFixedWidth(420)
    holder = {}

    def close():
        if holder.get("win") is not None:
            desktop.close_window(holder.pop("win"))

    ok.clicked.connect(close)
    holder["win"] = _fixed_window(desktop, f"{title} Properties" if tab else title, body, close)
    if icon is not None:
        holder["win"].icon = icon
    desktop.open_window(holder["win"])
