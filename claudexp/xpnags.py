"""The things Windows XP nagged you about in 2001:

- Activation: a key in the notification area and 'Activate Windows now - N days left' at logon, until you go through
  the Activation Wizard (over the Internet, or 'by phone' with the installation ID). It never locks you out.
- The Desktop Cleanup Wizard: every 60 days, 'There are unused icons on your desktop', and a wizard that moves the
  shortcuts you haven't used into an 'Unused Desktop Shortcuts' folder.
- Windows Messenger's sign-in reminders (programs/messengers/winmsgr.py) start from here too.

Called once per logon from app.show_desktop.
"""
import random
import time

from PySide6.QtCore import QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QIcon, QLinearGradient, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (QButtonGroup, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QPushButton,
                               QRadioButton, QStackedWidget, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget)
from shiboken6 import isValid

from . import sound
from .paths import DATA
from .programs.people import load_json, save_json

ACTIVATION = DATA / "activation.json"
CLEANUP = DATA / "desktop_cleanup.json"
GRACE_DAYS = 30
CLEANUP_DAYS = 60
FIRST_CLEANUP_DAYS = 7            # the first reminder comes a week after Windows was set up
UNUSED_DAYS = 60
UNUSED_FOLDER = "Unused Desktop Shortcuts"
DAY = 86400
_state = {"key_tray": None, "cleanup_tray": None}


# ---- art ------------------------------------------------------------------------------------------------------------

def key_pixmap(size=16):
    """The activation key: gold, with a little Windows flag."""
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    s = size / 16
    g = QLinearGradient(0, 0, size, size)
    g.setColorAt(0, QColor("#FFE58A"))
    g.setColorAt(1, QColor("#C89418"))
    p.setPen(QPen(QColor("#7A5810"), max(0.8, 0.8 * s)))
    p.setBrush(g)
    p.drawEllipse(QRectF(1 * s, 1 * s, 7 * s, 7 * s))
    p.drawRect(QRectF(6.5 * s, 4 * s, 8 * s, 2 * s))
    p.drawRect(QRectF(11 * s, 6 * s, 1.6 * s, 2.6 * s))
    p.drawRect(QRectF(13.2 * s, 6 * s, 1.6 * s, 2 * s))
    p.setPen(Qt.NoPen)
    for (x, y), c in zip(((3, 3), (4.6, 3), (3, 4.6), (4.6, 4.6)), ("#F25022", "#7FBA00", "#00A4EF", "#FFB900")):
        p.setBrush(QColor(c))
        p.drawRect(QRectF(x * s, y * s, 1.4 * s, 1.4 * s))
    p.end()
    return pm


def cleanup_pixmap(size=16):
    """A desktop with a broom."""
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    s = size / 16
    p.setPen(QPen(QColor("#2A4A8A"), max(0.8, 0.8 * s)))
    p.setBrush(QColor("#5A8AE0"))
    p.drawRect(QRectF(1 * s, 2 * s, 12 * s, 9 * s))
    p.setPen(QPen(QColor("#8A5A20"), 1.4 * s))
    p.drawLine(int(14 * s), int(1 * s), int(8 * s), int(12 * s))
    p.setPen(QPen(QColor("#D8A840"), 1.2 * s))
    for dx in (-2, -1, 0, 1, 2):
        p.drawLine(int(8 * s), int(12 * s), int((7 + dx) * s), int(15 * s))
    p.end()
    return pm


def _days_left():
    st = load_json(ACTIVATION, {})
    first = st.get("first") or time.time()
    return max(0, GRACE_DAYS - int((time.time() - first) // DAY))


def activated():
    return bool(load_json(ACTIVATION, {}).get("activated"))


# ---- at logon -------------------------------------------------------------------------------------------------------

def at_logon(desktop):
    for name, delay in (("activation", 6000), ("cleanup", 20000)):
        QTimer.singleShot(delay, lambda name=name: _safely(name, desktop))
    from .programs.messengers import winmsgr
    QTimer.singleShot(3000, lambda: winmsgr.start_at_logon(desktop))
    from .programs import players
    QTimer.singleShot(12000, lambda: desktop.isVisible() and players.at_logon(desktop))   # RealTray and qttask


def _safely(name, desktop):
    if not desktop.isVisible():
        return
    (_activation_nag if name == "activation" else _cleanup_nag)(desktop)


def _activation_nag(desktop):
    st = load_json(ACTIVATION, {})
    if st.get("activated"):
        return
    st.setdefault("first", time.time())
    left = _days_left()
    from .tray import TrayIcon
    tray = _state["key_tray"]
    if tray is None:
        tray = _state["key_tray"] = TrayIcon(desktop, QIcon(key_pixmap(16)), desktop)
        tray.activated.connect(lambda _r: open_activation(desktop))
        tray.messageClicked.connect(lambda: open_activation(desktop))
        tray.show()
    tray.setToolTip(f"{left} days left for activation\nClick this icon to activate Windows now"
                    if left else "Windows must be activated\nClick this icon to activate Windows now")
    if time.time() - st.get("last_nag", 0) > DAY / 2:          # at most twice a day
        st["last_nag"] = time.time()
        if left:
            tray.showMessage("Activate Windows now", f"{left} days left for activation. Click this message to start "
                             "activation.", None, 9000)
        else:
            tray.showMessage("Windows must be activated now", "Your activation period has expired. Click this "
                             "message to activate Windows.", None, 9000)
    save_json(ACTIVATION, st)


def _cleanup_nag(desktop):
    st = load_json(CLEANUP, {})
    if st.get("off"):
        return
    now = time.time()
    st.setdefault("first", now)
    due = st.get("last", st["first"] - (CLEANUP_DAYS - FIRST_CLEANUP_DAYS) * DAY) + CLEANUP_DAYS * DAY
    save_json(CLEANUP, st)
    if now < due or not _unused(desktop):
        return
    from .tray import TrayIcon
    tray = _state["cleanup_tray"]
    if tray is None:
        tray = _state["cleanup_tray"] = TrayIcon(desktop, QIcon(cleanup_pixmap(16)), desktop)
        tray.setToolTip("Unused desktop icons")
        tray.activated.connect(lambda _r: open_cleanup(desktop))
        tray.messageClicked.connect(lambda: open_cleanup(desktop))
        tray.show()
    tray.showMessage("Unused desktop icons", "There are unused icons on your desktop. Click this balloon to run "
                     "the Desktop Cleanup Wizard.", None, 10000)


# ---- the Activation Wizard -------------------------------------------------------------------------------------------

WIZ_STYLE = """
QWidget#wiz { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #5A7EDC, stop:1 #3557C4); }
QLabel { color: white; font-family: Tahoma; font-size: 12px; }
QLabel#title { font-family: 'Franklin Gothic Medium', 'Trebuchet MS'; font-size: 24px; }
QRadioButton { color: white; font-family: Tahoma; font-size: 12px; }
QLineEdit { font-family: 'Lucida Console'; font-size: 13px; }
QPushButton { font-family: Tahoma; font-size: 11px; }
"""


def _installation_id():
    rnd = random.Random(str(load_json(ACTIVATION, {}).get("first", 1)))
    return [f"{rnd.randint(0, 999999):06d}" for _ in range(9)]


def open_activation(desktop):
    from .wm import XPWindow
    win = _state.get("act_win")
    if win is not None and isValid(win):
        desktop.open_window(win)
        return
    body = QWidget()
    body.setObjectName("wiz")
    body.setAttribute(Qt.WA_StyledBackground, True)
    body.setStyleSheet(WIZ_STYLE)
    v = QVBoxLayout(body)
    v.setContentsMargins(40, 26, 40, 18)
    pages = QStackedWidget()
    v.addWidget(pages, 1)
    nav = QHBoxLayout()
    nav.addStretch()
    back, nxt, cancel = QPushButton("< Back"), QPushButton("Next >"), QPushButton("Cancel")
    for b in (back, nxt, cancel):
        b.setFixedSize(80, 24)
        nav.addWidget(b)
    v.addLayout(nav)

    def page(title, *widgets):
        w = QWidget()
        pv = QVBoxLayout(w)
        t = QLabel(title)
        t.setObjectName("title")
        pv.addWidget(t)
        pv.addSpacing(10)
        for x in widgets:
            if isinstance(x, str):
                x = QLabel(x)
                x.setWordWrap(True)
            pv.addWidget(x)
        pv.addStretch()
        pages.addWidget(w)
        return w

    if activated():
        page("Windows is already activated", "Windows is already activated. Click OK to exit.")
        back.hide()
        cancel.hide()
        nxt.setText("OK")
        nxt.clicked.connect(lambda: desktop.close_window(win))
        win = XPWindow(desktop, "Activate Windows", body, QIcon(key_pixmap(16)), size=(620, 440))
        _state["act_win"] = win
        desktop.open_window(win)
        return

    left = _days_left()
    choice = QButtonGroup(body)
    options = QWidget()
    ov = QVBoxLayout(options)
    for i, text in enumerate(("Yes, let's activate Windows over the Internet now",
                              "Yes, I want to telephone a customer service representative to activate Windows",
                              "No, remind me every few days")):
        rb = QRadioButton(text)
        rb.setChecked(i == 0)
        choice.addButton(rb, i)
        ov.addWidget(rb)
    page("Let's activate Windows",
         "Microsoft requires you to activate your copy of Windows. Activation helps reduce software piracy and "
         "ensures that you're getting genuine Microsoft software.",
         f"<b>You have {left} days left to activate.</b>" if left else "<b>Your activation period has expired.</b>",
         "Do you want to activate Windows now?", options,
         "<span style='font-size:11px'>Activation is not registration: Microsoft doesn't collect personal "
         "information.</span>")
    status = QLabel("Connecting to the Internet...")
    page("Activating Windows", "Please wait while Windows contacts Microsoft over the Internet to activate.", status)
    iid = _installation_id()
    groups = QWidget()
    gv = QHBoxLayout(groups)
    boxes = []
    for letter in "ABCDEFG":
        col = QVBoxLayout()
        lab = QLabel(letter)
        lab.setAlignment(Qt.AlignCenter)
        col.addWidget(lab)
        e = QLineEdit()
        e.setMaxLength(6)
        e.setFixedWidth(62)
        col.addWidget(e)
        gv.addLayout(col)
        boxes.append(e)
    page("Activate Windows by telephone",
         "<b>Step 1:</b> Call 1-888-571-2048 (toll free).",
         "<b>Step 2:</b> Give the customer service representative your installation ID:",
         "<span style='font-family: Lucida Console; font-size: 14px'>" + " ".join(iid) + "</span>",
         "<b>Step 3:</b> Type the confirmation ID the representative gives you:", groups)
    page("Thank you!", "You have successfully activated your copy of Windows.",
         "Windows activation helps to reduce software piracy and ensures that you are using genuine Microsoft "
         "software.", "To exit, click OK.")
    win = XPWindow(desktop, "Activate Windows", body, QIcon(key_pixmap(16)), size=(620, 440))
    _state["act_win"] = win

    def show(i):
        pages.setCurrentIndex(i)
        back.setEnabled(i in (1, 2))
        nxt.setText("OK" if i == 3 else "Next >")
        cancel.setVisible(i != 3)

    def done():
        st = load_json(ACTIVATION, {})
        st["activated"] = True
        save_json(ACTIVATION, st)
        tray = _state.get("key_tray")
        if tray is not None:
            tray.hide()
            _state["key_tray"] = None
        sound.play("default")
        show(3)

    def online():
        status.setText("Activating Windows...")
        QTimer.singleShot(2500, lambda: (status.setText("Activation succeeded."), QTimer.singleShot(800, done)))

    def go_next():
        i = pages.currentIndex()
        if i == 0:
            c = choice.checkedId()
            if c == 2:
                desktop.close_window(win)
                return
            if c == 0:
                show(1)
                from . import network
                if network.is_connected():
                    QTimer.singleShot(1500, online)
                else:
                    network.connect(desktop, then=lambda: QTimer.singleShot(1500, online))
            else:
                show(2)
        elif i == 2:
            if all(len(b.text().strip()) == 6 and b.text().strip().isdigit() for b in boxes):
                done()
            else:
                from .explorer.dialogs import msgbox
                msgbox(desktop, "Activate Windows", "The confirmation ID you typed is not valid. Please make sure "
                       "you typed six digits in each box.", "warning")
        elif i == 3:
            desktop.close_window(win)

    back.clicked.connect(lambda: show(0))
    nxt.clicked.connect(go_next)
    cancel.clicked.connect(lambda: desktop.close_window(win))
    show(0)
    desktop.open_window(win)


def activation_icon():
    return QIcon(key_pixmap(32))


def launch_activation(desktop):
    open_activation(desktop)


# ---- the Desktop Cleanup Wizard ------------------------------------------------------------------------------------

def _unused(desktop):
    """[(key, label, icon, last used date or None)] of the desktop's program shortcuts not used in 60 days."""
    from .programs import installed
    out = []
    now = time.time()
    for icon in desktop.icons.icons:
        if not icon.key.startswith("prog:") or icon.key in ("prog:connect",):
            continue
        key = icon.key.split(":", 1)[1]
        last = _last_use(key)
        if last and now - last < UNUSED_DAYS * DAY:
            continue
        out.append((icon.key, icon.label, icon.icon, installed.last_used(key)))
    return out


def _last_use(key):
    """When a program was last used - counting from when ClaudeXP started keeping track, so nothing looks
    'unused' just because it was used before then."""
    from .programs import installed
    st = load_json(CLEANUP, {})
    return installed.usage(key).get("last") or st.get("first") or time.time()


def open_cleanup(desktop):
    from .wm import XPWindow
    st = load_json(CLEANUP, {})
    st["last"] = time.time()
    save_json(CLEANUP, st)
    tray = _state.get("cleanup_tray")
    if tray is not None:
        tray.hide()
        _state["cleanup_tray"] = None
    body = QWidget()
    body.setObjectName("dcw")
    body.setAttribute(Qt.WA_StyledBackground, True)
    body.setStyleSheet("QWidget#dcw { background: #FFFFFF; } QLabel, QPushButton, QCheckBox { font-family: Tahoma;"
                       " font-size: 11px; } QLabel#big { font-size: 16px; font-weight: bold; }")
    v = QVBoxLayout(body)
    v.setContentsMargins(0, 0, 0, 0)
    pages = QStackedWidget()
    v.addWidget(pages, 1)
    nav_box = QWidget()
    nav_box.setStyleSheet("background: #ECE9D8; border-top: 1px solid #ACA899;")
    nav = QHBoxLayout(nav_box)
    nav.addStretch()
    back, nxt, cancel = QPushButton("< Back"), QPushButton("Next >"), QPushButton("Cancel")
    for b in (back, nxt, cancel):
        b.setFixedSize(75, 23)
        nav.addWidget(b)
    v.addWidget(nav_box)

    def welcome_page():
        w = QWidget()
        row = QHBoxLayout(w)
        row.setContentsMargins(0, 0, 0, 0)
        art = QLabel()
        art.setFixedWidth(160)
        art.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2D5ABE, stop:1 #7AA2EA);")
        art.setPixmap(cleanup_pixmap(96))
        art.setAlignment(Qt.AlignCenter)
        row.addWidget(art)
        col = QVBoxLayout()
        col.setContentsMargins(16, 20, 16, 16)
        t = QLabel("Welcome to the Desktop Cleanup Wizard")
        t.setObjectName("big")
        t.setWordWrap(True)
        col.addWidget(t)
        col.addSpacing(12)
        txt = QLabel("This wizard helps you clean up your desktop by moving unused desktop shortcuts to a desktop "
                     f"folder called {UNUSED_FOLDER}.\n\nShortcuts you haven't used in {UNUSED_DAYS} days are "
                     "selected on the next page, but you can choose which ones to move.\n\nTo continue, click Next.")
        txt.setWordWrap(True)
        col.addWidget(txt)
        col.addStretch()
        row.addLayout(col, 1)
        pages.addWidget(w)

    welcome_page()
    sc = QWidget()
    sv = QVBoxLayout(sc)
    sv.setContentsMargins(16, 12, 16, 12)
    t = QLabel("<b>Shortcuts</b><br>The shortcuts you select will be moved to the Unused Desktop Shortcuts folder.")
    sv.addWidget(t)
    tree = QTreeWidget()
    tree.setRootIsDecorated(False)
    tree.setHeaderLabels(["Shortcuts", "Date Last Used"])
    tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
    now = time.time()
    from .programs import installed
    for icon in desktop.icons.icons:
        if not icon.key.startswith("prog:") or icon.key == "prog:connect":
            continue
        key = icon.key.split(":", 1)[1]
        last = installed.last_used(key)
        ts = _last_use(key)
        item = QTreeWidgetItem([icon.label, f"{last.month}/{last.day}/{last.year}" if last else "Never"])
        item.setIcon(0, icon.icon)
        item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
        item.setCheckState(0, Qt.Unchecked if ts and now - ts < UNUSED_DAYS * DAY else Qt.Checked)
        item.setData(0, Qt.UserRole, icon.key)
        tree.addTopLevelItem(item)
    sv.addWidget(tree, 1)
    row = QHBoxLayout()
    for label, state in (("Select All", Qt.Checked), ("Clear All", Qt.Unchecked)):
        b = QPushButton(label)
        b.setFixedSize(75, 23)
        b.clicked.connect(lambda _c=False, s=state: [tree.topLevelItem(i).setCheckState(0, s)
                                                     for i in range(tree.topLevelItemCount())])
        row.addWidget(b)
    row.addStretch()
    sv.addLayout(row)
    pages.addWidget(sc)
    fin = QWidget()
    fv = QVBoxLayout(fin)
    fv.setContentsMargins(16, 20, 16, 16)
    t2 = QLabel("Completing the Desktop Cleanup Wizard")
    t2.setObjectName("big")
    fv.addWidget(t2)
    summary = QLabel()
    summary.setWordWrap(True)
    fv.addWidget(summary)
    fv.addStretch()
    pages.addWidget(fin)
    win = XPWindow(desktop, "Desktop Cleanup Wizard", body, QIcon(cleanup_pixmap(16)), size=(520, 400))

    def chosen():
        return [(tree.topLevelItem(i).data(0, Qt.UserRole), tree.topLevelItem(i).text(0))
                for i in range(tree.topLevelItemCount()) if tree.topLevelItem(i).checkState(0) == Qt.Checked]

    def show(i):
        pages.setCurrentIndex(i)
        back.setEnabled(i > 0)
        nxt.setText("Finish" if i == 2 else "Next >")
        if i == 2:
            names = [n for _k, n in chosen()]
            summary.setText((f"The following {len(names)} shortcut{'s' if len(names) != 1 else ''} will be moved "
                             f"to the {UNUSED_FOLDER} folder:\n\n" + "\n".join(f"   {n}" for n in names)
                             + "\n\nTo close this wizard, click Finish.") if names else
                            "No shortcuts were selected, so your desktop won't change.\n\nTo close this wizard, "
                            "click Finish.")

    def finish():
        move_to_unused(desktop, [k for k, _n in chosen()])
        desktop.close_window(win)

    back.clicked.connect(lambda: show(pages.currentIndex() - 1))
    nxt.clicked.connect(lambda: finish() if pages.currentIndex() == 2 else show(pages.currentIndex() + 1))
    cancel.clicked.connect(lambda: desktop.close_window(win))
    show(0)
    desktop.open_window(win)


def move_to_unused(desktop, keys):
    """Each desktop program shortcut in keys becomes a shortcut in the Unused Desktop Shortcuts folder."""
    if not keys:
        return
    from .explorer import shortcuts
    from . import programs
    mgr = desktop.icons
    folder = mgr.folder() / UNUSED_FOLDER
    folder.mkdir(parents=True, exist_ok=True)
    for icon_key in keys:
        key = icon_key.split(":", 1)[1]
        try:
            prog = programs.get(key)
        except StopIteration:
            continue
        shortcuts.make(folder / f"{prog.name}.lnk", program=key)
        if icon_key not in mgr.state["hidden"]:
            mgr.state["hidden"].append(icon_key)
    mgr.rescan()
    mgr.save()


def cleanup_settings():
    return {"off": False, **load_json(CLEANUP, {})}


def set_cleanup_every_60_days(on):
    st = load_json(CLEANUP, {})
    st["off"] = not on
    save_json(CLEANUP, st)

