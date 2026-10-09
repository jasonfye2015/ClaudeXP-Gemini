"""StyleXP 1.0 by TGTSoft (trial): patches uxtheme.dll so Windows will load visual styles Microsoft didn't sign,
and comes with three of them - Watercolor (the theme cut from the Whistler betas), Aqua X and Chrome Hex.

It's a 30-day trial, and it nags: every start-up shows the countdown with a Continue button that waits five
seconds, and now and then applying a style reminds you to register. When the trial runs out the unsigned styles
stop loading (Windows falls back to the Windows XP style) until StyleXP is registered - which it can't be, since
TGTSoft's key server isn't answering in 2001. State lives in data/stylexp.json."""
from datetime import datetime

from PySide6.QtCore import QRect, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QIcon, QLinearGradient, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QPushButton,
                               QVBoxLayout, QWidget)
from shiboken6 import isValid

from .. import clock, sound, theme
from ..paths import DATA
from ..wm import XPWindow
from .people import load_json, save_json

STATE_FILE = DATA / "stylexp.json"
TRIAL_DAYS = 30
STYLES = [("luna", "blue", "Luna (Windows XP)"), ("luna", "olive", "Luna Olive Green"), ("luna", "silver", "Luna Silver"),
          ("watercolor", "Default", "Watercolor"), ("aquax", "Default", "Aqua X"), ("chromehex", "Default", "Chrome Hex")]


def stylexp_icon():
    pm = QPixmap(32, 32)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    g = QLinearGradient(0, 0, 32, 32)
    g.setColorAt(0, QColor("#7FC8FF"))
    g.setColorAt(1, QColor("#1A4AB0"))
    p.setPen(QPen(QColor("#0A2A70"), 1))
    p.setBrush(g)
    p.drawRoundedRect(QRectF(2.5, 4.5, 27, 23), 4, 4)
    p.fillRect(QRectF(5, 7, 22, 5), QColor(255, 255, 255, 120))          # a little title bar
    p.setBrush(QColor("#E8261C"))
    p.setPen(Qt.NoPen)
    p.drawEllipse(QRectF(21, 7.5, 4, 4))
    p.setPen(QPen(QColor("white"), 1))
    f = QFont("Arial Black", 9)
    p.setFont(f)
    p.drawText(QRectF(2, 12, 28, 15), Qt.AlignCenter, "XP")
    p.end()
    return QIcon(pm)


def _state():
    return load_json(STATE_FILE, {})


def installed_on():
    st = _state()
    if not st.get("installed"):
        st["installed"] = clock.now().date().isoformat()
        save_json(STATE_FILE, st)
    return datetime.fromisoformat(st["installed"]).date()


def days_left():
    st = _state()
    if not st.get("installed"):
        return TRIAL_DAYS
    used = (clock.now().date() - datetime.fromisoformat(st["installed"]).date()).days
    return max(0, TRIAL_DAYS - used)


def patched():
    """True while uxtheme.dll is patched and the trial is still running."""
    st = _state()
    return bool(st.get("patched")) and days_left() > 0


# ---- the nag ------------------------------------------------------------------------------------------------------

def nag(desktop, then=None, reminder=False):
    """The 'unregistered' screen. then() runs on Continue (not when the trial is over)."""
    from ..network import DialogBody, _fixed_window
    left = days_left()
    body = DialogBody()
    v = QVBoxLayout(body)
    v.setContentsMargins(0, 0, 0, 12)
    banner = QLabel()
    banner.setFixedSize(380, 64)
    pm = QPixmap(380, 64)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    g = QLinearGradient(0, 0, 380, 0)
    g.setColorAt(0, QColor("#0A2A70"))
    g.setColorAt(1, QColor("#3A8AE8"))
    p.fillRect(pm.rect(), g)
    p.drawPixmap(14, 16, stylexp_icon().pixmap(32, 32))
    p.setPen(QColor("white"))
    p.setFont(QFont("Arial Black", 16))
    p.drawText(QRect(56, 6, 300, 34), Qt.AlignVCenter | Qt.AlignLeft, "StyleXP")
    p.setFont(QFont("Tahoma", 8))
    p.drawText(QRect(58, 36, 300, 18), Qt.AlignVCenter | Qt.AlignLeft, "by TGTSoft  -  Unregistered trial version")
    p.end()
    banner.setPixmap(pm)
    v.addWidget(banner)
    if left > 0:
        text = (f"Thank you for trying StyleXP!\n\nYou have <b>{left} day{'s' if left != 1 else ''}</b> left in your "
                "free 30-day trial.").replace("\n", "<br>")
        if reminder:
            text = (f"StyleXP is not registered. {left} day{'s' if left != 1 else ''} remain in your trial.<br><br>"
                    "Registering removes these reminders and keeps your visual styles working after the trial.")
    else:
        text = ("Your 30-day StyleXP trial has <b>expired</b>.<br><br>Third-party visual styles have been "
                "turned off. Please register StyleXP to keep using them.")
    msg = QLabel(text)
    msg.setTextFormat(Qt.RichText)
    msg.setWordWrap(True)
    msg.setContentsMargins(16, 10, 16, 6)
    v.addWidget(msg)
    price = QLabel("Register online at www.tgtsoft.com - only $19.95.")
    price.setContentsMargins(16, 0, 16, 8)
    price.setStyleSheet("color: #404040;")
    v.addWidget(price)
    row = QHBoxLayout()
    row.setContentsMargins(16, 0, 16, 0)
    row.addStretch()
    reg = QPushButton("&Register...")
    go = QPushButton()
    for b in (reg, go):
        b.setFixedSize(96, 23)
        row.addWidget(b)
    v.addLayout(row)
    body.setFixedWidth(380)
    holder = {}

    def close():
        win = holder.pop("win", None)
        if win is not None and isValid(win):
            desktop.close_window(win)
        tick.stop()

    wait = [0 if reminder else 5]
    tick = QTimer(body, interval=1000)

    def count():
        if wait[0] > 0:
            go.setText(f"Continue ({wait[0]})")
            go.setEnabled(False)
            wait[0] -= 1
        else:
            go.setText("&Continue")
            go.setEnabled(True)
            tick.stop()
    if left > 0:
        tick.timeout.connect(count)
        count()
        tick.start()
        go.clicked.connect(lambda: (close(), then() if then else None))
    else:
        go.setText("E&xit")
        go.clicked.connect(close)
    reg.clicked.connect(lambda: register(desktop))
    win = _fixed_window(desktop, "StyleXP - Unregistered", body, close)
    win.icon = stylexp_icon()
    holder["win"] = win
    desktop.open_window(win)
    sound.play("exclamation")
    return win


def register(desktop):
    from ..explorer.dialogs import msgbox
    from ..network import DialogBody, _fixed_window
    body = DialogBody()
    v = QVBoxLayout(body)
    v.setContentsMargins(14, 12, 14, 12)
    v.addWidget(QLabel("Enter the name and registration key from your TGTSoft receipt:"))
    name, key = QLineEdit(), QLineEdit()
    name.setPlaceholderText("Name")
    key.setPlaceholderText("XXXX-XXXX-XXXX-XXXX")
    v.addWidget(name)
    v.addWidget(key)
    row = QHBoxLayout()
    row.addStretch()
    ok, cancel = QPushButton("OK"), QPushButton("Cancel")
    for b in (ok, cancel):
        b.setFixedSize(75, 23)
        row.addWidget(b)
    v.addLayout(row)
    body.setFixedWidth(330)
    holder = {}

    def close():
        win = holder.pop("win", None)
        if win is not None and isValid(win):
            desktop.close_window(win)

    def check():
        close()
        msgbox(desktop, "StyleXP", "That registration key is not valid.\n\nIf you bought StyleXP, check the key "
                                   "in your receipt e-mail, or contact support@tgtsoft.com.", "error")
    ok.clicked.connect(check)
    cancel.clicked.connect(close)
    win = _fixed_window(desktop, "Register StyleXP", body, close)
    win.icon = stylexp_icon()
    holder["win"] = win
    desktop.open_window(win)


# ---- the main window ----------------------------------------------------------------------------------------------

class Preview(QWidget):
    """A window drawn in the chosen style over a slice of desktop."""

    def __init__(self):
        super().__init__()
        self.style_obj = theme.make_style("luna", "blue")
        self.setFixedSize(300, 200)

    def show_style(self, key, scheme):
        self.style_obj = theme.make_style(key, scheme)
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        g = QLinearGradient(0, 0, 0, self.height())
        g.setColorAt(0, QColor("#5A8ED8"))
        g.setColorAt(1, QColor("#3A7A30"))
        p.fillRect(self.rect(), g)
        st = self.style_obj
        p.save()
        p.translate(20, 18)
        w, h = 260, 140
        st.paint_frame(p, w, h, "Active Window", stylexp_icon(), True, ("min", "max", "close"))
        p.fillRect(st.border, st.title_h, w - 2 * st.border, h - st.title_h - st.border, QColor("white"))
        p.setPen(QColor("black"))
        p.setFont(QFont("Tahoma", 8))
        p.drawText(QRect(st.border + 8, st.title_h + 6, 200, 20), Qt.AlignLeft, "Window Text")
        p.restore()
        p.save()
        p.translate(0, self.height() - 30)
        bar = QRect(0, 0, self.width(), 30)
        start = QRect(0, 0, st.start_width(), 30)
        st.paint_taskbar(p, bar, start, False)
        p.restore()
        p.setPen(QPen(QColor("#404040"), 1))
        p.setBrush(Qt.NoBrush)
        p.drawRect(self.rect().adjusted(0, 0, -1, -1))


class StyleXP(QWidget):
    def __init__(self, desktop):
        super().__init__()
        self.desktop = desktop
        self.frame = None
        self.setObjectName("sxp")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("QWidget#sxp { background: #F4F6FA; } QLabel#head { font: bold 14px 'Trebuchet MS';"
                           " color: #0A2A70; } QListWidget { background: white; font: 11px Tahoma; }")
        v = QVBoxLayout(self)
        v.setContentsMargins(12, 10, 12, 10)
        head = QLabel("Visual Styles")
        head.setObjectName("head")
        v.addWidget(head)
        row = QHBoxLayout()
        self.list = QListWidget()
        self.list.setFixedWidth(170)
        for key, scheme, label in STYLES:
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, (key, scheme))
            self.list.addItem(item)
        row.addWidget(self.list)
        right = QVBoxLayout()
        self.preview = Preview()
        right.addWidget(self.preview)
        self.apply_btn = QPushButton("&Apply Visual Style")
        self.apply_btn.clicked.connect(self.apply)
        right.addWidget(self.apply_btn)
        right.addStretch()
        row.addLayout(right)
        v.addLayout(row)
        self.status = QLabel()
        self.status.setWordWrap(True)
        v.addWidget(self.status)
        bottom = QHBoxLayout()
        self.patch_btn = QPushButton("&Patch uxtheme.dll")
        self.patch_btn.clicked.connect(self.patch)
        bottom.addWidget(self.patch_btn)
        bottom.addStretch()
        reg = QPushButton("&Register...")
        reg.clicked.connect(lambda: register(desktop))
        bottom.addWidget(reg)
        v.addLayout(bottom)
        self.list.currentItemChanged.connect(self._chosen)
        cur = theme.state()
        for i in range(self.list.count()):
            if self.list.item(i).data(Qt.UserRole) == (cur["style"], cur["scheme"]) or (
                    cur["style"] in theme.GLOSS and self.list.item(i).data(Qt.UserRole)[0] == cur["style"]):
                self.list.setCurrentRow(i)
        if self.list.currentRow() < 0:
            self.list.setCurrentRow(0)
        self._update_status()

    def _chosen(self, item, _prev=None):
        if item is not None:
            self.preview.show_style(*item.data(Qt.UserRole))
            self._update_status()

    def _update_status(self):
        st = _state()
        left = days_left()
        item = self.list.currentItem()
        third_party = item is not None and item.data(Qt.UserRole)[0] in theme.HACKED
        if st.get("patched"):
            self.patch_btn.setEnabled(False)
            self.patch_btn.setText("uxtheme.dll patched")
        if left <= 0:
            self.status.setText("Your trial has expired. Third-party visual styles are turned off.")
            self.apply_btn.setEnabled(not third_party)
        elif not st.get("patched"):
            self.status.setText("Windows XP only loads visual styles signed by Microsoft. Patch uxtheme.dll to use "
                                "third-party styles like Watercolor.")
            self.apply_btn.setEnabled(not third_party)
        else:
            self.status.setText(f"uxtheme.dll is patched: any visual style can be used.  Trial: {left} day"
                                f"{'s' if left != 1 else ''} left.")
            self.apply_btn.setEnabled(True)

    def patch(self):
        from ..explorer.dialogs import msgbox
        self.status.setText("Backing up uxtheme.dll... patching... replacing the file in use...")
        self.patch_btn.setEnabled(False)

        def done():
            st = _state()
            st["patched"] = True
            save_json(STATE_FILE, st)
            if isValid(self):
                self._update_status()
            msgbox(self.desktop, "Windows File Protection",
                   "Files that are required for Windows to run properly have been replaced by unrecognized "
                   "versions. To maintain system stability, Windows must restore the original versions of these "
                   "files.\n\n(StyleXP has told Windows File Protection to leave uxtheme.dll alone.)", "warning")
        QTimer.singleShot(1500, done)

    def apply(self):
        item = self.list.currentItem()
        if item is None:
            return
        key, scheme = item.data(Qt.UserRole)
        if key in theme.HACKED and not patched():
            return
        from .. import themes
        themes.with_please_wait(self.desktop, lambda: theme.set_state(style=key, scheme=scheme,
                                                                       name="Modified Theme"))
        import random
        if random.random() < 0.35:
            QTimer.singleShot(1600, lambda: nag(self.desktop, reminder=True))


_open = {}


def open_stylexp(desktop):
    win = _open.get("win")
    if win is not None and isValid(win):
        desktop.open_window(win)
        return win
    installed_on()

    def show():
        body = StyleXP(desktop)
        w = XPWindow(desktop, "StyleXP", body, stylexp_icon(), (520, 400))
        body.frame = w
        _open["win"] = w
        desktop.open_window(w)
    nag(desktop, then=show)
