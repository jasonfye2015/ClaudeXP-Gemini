"""Add or Remove Programs (Control Panel), as in Windows XP:

- Change or Remove Programs: everything you've installed, with its size, how often it's used and when it was last
  used. Remove takes it off the desktop, the Start menu and Run (programs/installed.py) - nothing is deleted.
- Add New Programs: put back anything you removed ('reinstall'), or look for a setup disk.
- Add/Remove Windows Components: Windows Messenger, the Games, MSN Explorer and friends; Messenger and Games really go.
- Set Program Access and Defaults: your default web browser and media player (defaults.py).
"""
import random

from PySide6.QtCore import QSize, Qt, QTimer
from PySide6.QtGui import QColor, QIcon, QLinearGradient, QPainter, QPixmap
from PySide6.QtWidgets import (QButtonGroup, QCheckBox, QComboBox, QFrame, QHBoxLayout, QLabel, QProgressBar,
                               QPushButton, QRadioButton, QScrollArea, QStackedWidget, QToolButton, QVBoxLayout,
                               QWidget)
from shiboken6 import isValid

from .. import sound
from ..wm import XPWindow
from . import installed

STYLE = """
QWidget#arp { background: #FFFFFF; }
QWidget#side { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #7A96DF, stop:1 #4A6EC8); }
QToolButton#nav { color: white; font-family: Tahoma; font-size: 11px; border: 1px solid transparent; padding: 6px 2px;
                  background: transparent; }
QToolButton#nav:hover { border: 1px solid #C8D6F5; }
QToolButton#nav:checked { background: #FFFFFF; color: #000000; border: 1px solid #FFFFFF; }
QLabel, QCheckBox, QRadioButton, QComboBox, QPushButton { font-family: Tahoma; font-size: 11px; }
QFrame#row { background: #FFFFFF; }
QFrame#rowsel { background: #E0E8F8; border: 1px solid #ACC0EC; }
QLabel#head { font-size: 12px; font-weight: bold; }
"""

# (key, name, description, size MB, is it something ClaudeXP can really take away?)
COMPONENTS = [
    ("accessories", "Accessories and Utilities", "Includes Windows Accessories and Utilities for your computer.", 17.4),
    ("games", "Games", "Solitaire, Spider, FreeCell, Hearts, Minesweeper, Pinball and the Internet games.", 9.1),
    ("fax", "Fax Services", "Sends and receives faxes, using fax devices installed on your computer.", 3.7),
    ("indexing", "Indexing Service", "Indexes documents for fast searching.", 0.0),
    ("ie", "Internet Explorer", "Adds or removes access to Internet Explorer from the Start menu and desktop.", 0.0),
    ("iis", "Internet Information Services (IIS)", "Web and FTP support, FrontPage and transactions.", 15.6),
    ("mgmt", "Management and Monitoring Tools", "Tools for monitoring and improving network performance.", 1.9),
    ("msmq", "Message Queuing", "Network communication services.", 0.0),
    ("msnexplorer", "MSN Explorer", "MSN Explorer - get the most out of the Web.", 13.4),
    ("networking", "Networking Services", "Specialized network-related services and protocols.", 0.3),
    ("printserv", "Other Network File and Print Services", "Shares files and printers with other computers.", 0.0),
    ("winmsgr", "Windows Messenger", "Instant messages, voice and video with friends who use .NET Passport.", 0.6),
]
GAMES = ["solitaire", "spider", "freecell", "hearts", "minesweeper", "pinball", "zone", "ibackgammon", "icheckers",
         "ihearts", "ireversi", "ispades"]


def arp_icon(size=32):
    """A CD and a box: Add or Remove Programs."""
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    s = size / 32
    from PySide6.QtCore import QRectF
    g = QLinearGradient(0, 0, 0, size)
    g.setColorAt(0, QColor("#F6D27A"))
    g.setColorAt(1, QColor("#C28A2A"))
    p.setPen(QColor("#7A5418"))
    p.setBrush(g)
    p.drawRect(QRectF(3 * s, 12 * s, 18 * s, 16 * s))
    cd = QLinearGradient(12 * s, 2 * s, 30 * s, 22 * s)
    cd.setColorAt(0, QColor("#F4F4FF"))
    cd.setColorAt(0.5, QColor("#B8D0F8"))
    cd.setColorAt(1, QColor("#E8C8F0"))
    p.setPen(QColor("#6A7A9A"))
    p.setBrush(cd)
    p.drawEllipse(QRectF(12 * s, 3 * s, 18 * s, 18 * s))
    p.setBrush(QColor("#FFFFFF"))
    p.drawEllipse(QRectF(19 * s, 10 * s, 4 * s, 4 * s))
    p.end()
    return pm


def _progress(desktop, title, lines, done):
    """The little 'Uninstalling...' / 'Installing...' window."""
    from ..network import DialogBody, _fixed_window
    body = DialogBody()
    v = QVBoxLayout(body)
    v.setContentsMargins(16, 14, 16, 14)
    label = QLabel(lines[0])
    label.setFixedWidth(330)
    v.addWidget(label)
    bar = QProgressBar()
    bar.setTextVisible(False)
    v.addWidget(bar)
    win = _fixed_window(desktop, title, body, lambda: None)
    desktop.open_window(win)
    state = {"n": 0}
    timer = QTimer(body)

    def tick():
        state["n"] += random.randint(3, 9)
        bar.setValue(min(100, state["n"]))
        label.setText(lines[min(len(lines) - 1, state["n"] * len(lines) // 100)])
        if state["n"] >= 100:
            timer.stop()
            if isValid(win):
                desktop.close_window(win)
            done()
    timer.timeout.connect(tick)
    timer.start(160)


class AddRemove(QWidget):
    def __init__(self, desktop, page=0):
        super().__init__()
        self.desktop = desktop
        self.frame = None
        self.setObjectName("arp")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(STYLE)
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(0)
        side = QWidget()
        side.setObjectName("side")
        side.setAttribute(Qt.WA_StyledBackground, True)
        side.setFixedWidth(104)
        sv = QVBoxLayout(side)
        sv.setContentsMargins(4, 8, 4, 8)
        self.group = QButtonGroup(self)
        style = self.style()
        from PySide6.QtWidgets import QStyle
        icons = [QIcon(arp_icon(32)), style.standardIcon(QStyle.SP_DriveCDIcon),
                 style.standardIcon(QStyle.SP_ComputerIcon), style.standardIcon(QStyle.SP_DialogApplyButton)]
        for i, text in enumerate(("Change or\nRemove\nPrograms", "Add New\nPrograms", "Add/Remove\nWindows\nComponents",
                                  "Set Program\nAccess and\nDefaults")):
            b = QToolButton()
            b.setObjectName("nav")
            b.setText(text)
            b.setIcon(icons[i])
            b.setIconSize(QSize(32, 32))
            b.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            b.setCheckable(True)
            b.setFixedWidth(94)
            self.group.addButton(b, i)
            sv.addWidget(b)
        sv.addStretch()
        row.addWidget(side)
        self.pages = QStackedWidget()
        row.addWidget(self.pages, 1)
        self.group.idClicked.connect(self.show_page)
        self.show_page(page)
        self.group.button(page).setChecked(True)

    def show_page(self, i):
        while self.pages.count():
            w = self.pages.widget(0)
            self.pages.removeWidget(w)
            w.deleteLater()
        self.pages.addWidget([self._installed_page, self._add_page, self._components_page, self._defaults_page][i]())

    # ---- Change or Remove Programs ----
    def _installed_page(self):
        from . import PROGRAMS
        page = QWidget()
        v = QVBoxLayout(page)
        v.setContentsMargins(10, 8, 10, 8)
        top = QHBoxLayout()
        top.addWidget(QLabel("<b>Currently installed programs:</b>"))
        top.addStretch()
        top.addWidget(QLabel("Sort by:"))
        sort = QComboBox()
        sort.addItems(["Name", "Size", "Frequency of use", "Date last used"])
        top.addWidget(sort)
        v.addLayout(top)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: 1px solid #7F9DB9; background: white; }")
        holder = QWidget()
        holder.setStyleSheet("background: white;")
        lv = QVBoxLayout(holder)
        lv.setContentsMargins(2, 2, 2, 2)
        lv.setSpacing(1)
        scroll.setWidget(holder)
        v.addWidget(scroll, 1)
        gone = installed.removed()
        progs = [p for p in PROGRAMS if installed.removable(p) and p.key not in gone]
        total = QLabel()
        v.addWidget(total)
        self._rows = []
        self._selected = None

        def fill():
            for r in self._rows:
                r.deleteLater()
            self._rows = []
            key = sort.currentText()
            order = {"Name": lambda p: p.name.lower(), "Size": lambda p: -installed.size_mb(p.key),
                     "Frequency of use": lambda p: -len(installed.usage(p.key).get("recent", [])),
                     "Date last used": lambda p: -(installed.usage(p.key).get("last") or 0)}[key]
            for p in sorted(progs, key=order):
                r = self._row(p, fill)
                lv.insertWidget(lv.count() - 1 if lv.count() else 0, r)
                self._rows.append(r)
            total.setText(f"{len(progs)} programs, {sum(installed.size_mb(p.key) for p in progs):.1f} MB in all")
        lv.addStretch()
        sort.currentIndexChanged.connect(lambda _i: fill())
        fill()
        return page

    def _row(self, prog, refill):
        frame = QFrame()
        frame.setObjectName("row")
        frame.setAttribute(Qt.WA_StyledBackground, True)
        v = QVBoxLayout(frame)
        v.setContentsMargins(6, 4, 6, 4)
        top = QHBoxLayout()
        icon = QLabel()
        icon.setPixmap(prog.icon().pixmap(24, 24))
        top.addWidget(icon)
        top.addWidget(QLabel(prog.name), 1)
        top.addWidget(QLabel(f"Size&nbsp;&nbsp;&nbsp;<b>{installed.size_mb(prog.key):.2f}MB</b>"))
        v.addLayout(top)
        details = QWidget()
        dv = QHBoxLayout(details)
        dv.setContentsMargins(30, 0, 0, 0)
        last = installed.last_used(prog.key)
        pub = installed.PUBLISHERS.get(prog.key, "")
        info = QLabel(f"<a href='#'>Click here for support information.</a>"
                      f"{'<br>Publisher: ' + pub if pub else ''}")
        info.linkActivated.connect(lambda _l: self._support(prog))
        dv.addWidget(info, 1)
        stats = QLabel(f"Used&nbsp;&nbsp;<b>{installed.frequency(prog.key)}</b><br>Last Used On&nbsp;&nbsp;"
                       f"<b>{last.month}/{last.day}/{last.year}</b>" if last else
                       "Used&nbsp;&nbsp;<b>rarely</b><br>Last Used On&nbsp;&nbsp;<b>never</b>")
        stats.setAlignment(Qt.AlignRight)
        dv.addWidget(stats)
        remove = QPushButton("Change/Remove")
        remove.setFixedSize(100, 23)
        remove.clicked.connect(lambda: self._remove(prog, refill))
        dv.addWidget(remove, 0, Qt.AlignBottom)
        details.hide()
        v.addWidget(details)

        def select(_e=None):
            if self._selected is not None and isValid(self._selected[0]):
                old, old_details = self._selected
                old.setObjectName("row")
                old_details.hide()
                old.setStyleSheet(old.styleSheet())
            frame.setObjectName("rowsel")
            frame.setStyleSheet(frame.styleSheet())
            details.show()
            self._selected = (frame, details)
        frame.mousePressEvent = select
        return frame

    def _support(self, prog):
        from ..explorer.dialogs import msgbox
        pub = installed.PUBLISHERS.get(prog.key, prog.name)
        msgbox(self.desktop, "Support Info", f"{prog.name}\n\nPublisher: {pub}\nVersion: 1.0\n"
               f"Size: {installed.size_mb(prog.key):.2f} MB\n\nUse the following information to get technical "
               "support for this program.", "info")

    def _remove(self, prog, refill):
        from ..explorer.dialogs import msgbox

        def answer(button):
            if button != "Yes":
                return
            lines = [f"Preparing to remove {prog.name}...", f"Removing {prog.name} files...",
                     "Removing shortcuts...", "Updating the registry...", "Finishing..."]

            def done():
                if prog.shutdown:
                    try:
                        prog.shutdown()
                    except Exception:
                        pass
                installed.set_removed(prog.key)
                self.desktop.icons.rescan()
                sound.play("default")
                msgbox(self.desktop, f"{prog.name} Uninstall", f"{prog.name} was successfully removed from your "
                       "computer.", "info")
                if isValid(self):
                    self.show_page(0)
            _progress(self.desktop, f"{prog.name} Uninstall", lines, done)

        msgbox(self.desktop, "Confirm Uninstall", f"Are you sure you want to completely remove '{prog.name}' and all "
               "of its components?", "question", ("Yes", "No"), answer)

    # ---- Add New Programs ----
    def _add_page(self):
        from . import PROGRAMS
        page = QWidget()
        v = QVBoxLayout(page)
        v.setContentsMargins(14, 10, 14, 10)
        v.addWidget(QLabel("<b>Add a program from CD-ROM or floppy disk</b>"))
        row = QHBoxLayout()
        row.addWidget(QLabel("To add a program from a CD-ROM or floppy disk, click CD or Floppy."), 1)
        cd = QPushButton("CD or Floppy")
        cd.setFixedSize(100, 23)
        cd.clicked.connect(self._cd)
        row.addWidget(cd)
        v.addLayout(row)
        v.addSpacing(10)
        v.addWidget(QLabel("<b>Add programs from Microsoft</b>"))
        row = QHBoxLayout()
        row.addWidget(QLabel("To add new Windows features, device drivers, and system updates over the Internet, "
                             "click Windows Update."), 1)
        wu = QPushButton("Windows Update")
        wu.setFixedSize(100, 23)
        from . import launch
        wu.clicked.connect(lambda: launch(self.desktop, "winupdate"))
        row.addWidget(wu)
        v.addLayout(row)
        v.addSpacing(10)
        gone = [p for p in PROGRAMS if p.key in installed.removed()]
        v.addWidget(QLabel("<b>Reinstall programs you removed</b>"))
        if not gone:
            v.addWidget(QLabel("You haven't removed any programs."))
        for prog in gone:
            r = QHBoxLayout()
            ic = QLabel()
            ic.setPixmap(prog.icon().pixmap(24, 24))
            r.addWidget(ic)
            r.addWidget(QLabel(prog.name), 1)
            b = QPushButton("Add")
            b.setFixedSize(75, 23)
            b.clicked.connect(lambda _c=False, p=prog: self._reinstall(p))
            r.addWidget(b)
            v.addLayout(r)
        v.addStretch()
        return page

    def _cd(self):
        from ..explorer.dialogs import msgbox
        msgbox(self.desktop, "Install Program From Floppy Disk or CD-ROM",
               "Insert the product's first installation floppy disk or CD-ROM, and then click Next.\n\n"
               "Windows was unable to locate the installation program. Click Back to try again, or click Browse to "
               "search for the installation program.", "info")

    def _reinstall(self, prog):
        lines = [f"Welcome to the {prog.name} Setup program...", "Copying files...", "Creating shortcuts...",
                 "Registering components...", "Setup is complete."]

        def done():
            installed.set_removed(prog.key, False)
            self.desktop.icons.rescan()
            sound.play("default")
            from ..explorer.dialogs import msgbox
            msgbox(self.desktop, f"{prog.name} Setup", f"{prog.name} has been successfully installed.", "info")
            if isValid(self):
                self.show_page(1)
        _progress(self.desktop, f"{prog.name} Setup", lines, done)

    # ---- Windows Components ----
    def _components_page(self):
        page = QWidget()
        v = QVBoxLayout(page)
        v.setContentsMargins(14, 10, 14, 10)
        v.addWidget(QLabel("<span style='font-size:13px'><b>Windows Components</b></span><br>You can add or remove "
                           "components of Windows XP.<br><br>To add or remove a component, click the checkbox. A "
                           "shaded box means that only part of the component will be installed."))
        box = QWidget()
        box.setStyleSheet("background: white; border: 1px solid #7F9DB9;")
        bv = QVBoxLayout(box)
        bv.setContentsMargins(4, 4, 4, 4)
        bv.setSpacing(1)
        state = self._component_state()
        checks = {}
        desc = QLabel(" ")
        desc.setWordWrap(True)
        for key, name, text, mb in COMPONENTS:
            r = QHBoxLayout()
            c = QCheckBox(name)
            c.setStyleSheet("border: none;")
            c.setChecked(state.get(key, True))
            c.toggled.connect(lambda _on, t=text: desc.setText(f"Description: {t}"))
            r.addWidget(c, 1)
            size = QLabel(f"{mb:.1f} MB")
            size.setStyleSheet("border: none;")
            r.addWidget(size)
            bv.addLayout(r)
            checks[key] = c
        v.addWidget(box)
        v.addWidget(desc)
        row = QHBoxLayout()
        row.addStretch()
        apply = QPushButton("Next >")
        apply.setFixedSize(75, 23)
        row.addWidget(apply)
        v.addLayout(row)
        v.addStretch()

        def go():
            new = {k: c.isChecked() for k, c in checks.items()}

            def done():
                self._save_components(new)
                sound.play("default")
                from ..explorer.dialogs import msgbox
                msgbox(self.desktop, "Windows Components Wizard", "You have successfully completed the Windows "
                       "Components Wizard.", "info")
            _progress(self.desktop, "Windows Components Wizard",
                      ["Configuring Components", "Please wait while Setup configures the components...",
                       "Copying files...", "Updating the registry...", "Completing configuration..."], done)
        apply.clicked.connect(go)
        return page

    def _component_state(self):
        gone = installed.removed()
        from .people import load_json
        from ..paths import DATA
        saved = load_json(DATA / "components.json", {})
        saved["winmsgr"] = "winmsgr" not in gone
        saved["games"] = not any(g in gone for g in GAMES)
        return saved

    def _save_components(self, new):
        from .people import save_json
        from ..paths import DATA
        save_json(DATA / "components.json", new)
        installed.set_removed("winmsgr", not new.get("winmsgr", True))
        if not new.get("winmsgr", True):
            from .messengers import winmsgr
            winmsgr.shutdown()
        for g in GAMES:
            installed.set_removed(g, not new.get("games", True))
        self.desktop.icons.rescan()

    # ---- Set Program Access and Defaults ----
    def _defaults_page(self):
        from .. import defaults
        page = QWidget()
        v = QVBoxLayout(page)
        v.setContentsMargins(14, 10, 14, 10)
        v.addWidget(QLabel("<span style='font-size:13px'><b>Set Program Access and Defaults</b></span><br>"
                           "A program configuration specifies default programs for certain activities, such as "
                           "Web browsing or playing media."))
        v.addSpacing(8)
        combos = {}
        for kind, label in (("browser", "Choose a default Web browser:"), ("media", "Choose a default media player:")):
            v.addWidget(QLabel(f"<b>{label}</b>"))
            group = QButtonGroup(page)
            for key, name in defaults.CHOICES[kind]:
                rb = QRadioButton(name)
                rb.setChecked(defaults.get(kind) == key)
                group.addButton(rb)
                rb.toggled.connect(lambda on, k=kind, val=key: on and defaults.set(k, val))
                v.addWidget(rb)
            combos[kind] = group
            v.addSpacing(8)
        v.addWidget(QLabel("<span style='color:#555'>Links from other programs open in the default Web browser; "
                           "music and video files you open from My Computer play in the default media player."
                           "</span>"))
        v.addStretch()
        return page


_open = {}


def open_arp(desktop, page=0):
    win = _open.get("win")
    if win is not None and isValid(win):
        desktop.open_window(win)
        win.content.group.button(page).click()
        return win
    body = AddRemove(desktop, page)
    win = XPWindow(desktop, "Add or Remove Programs", body, QIcon(arp_icon(16)), size=(640, 480))
    body.frame = win
    _open["win"] = win
    desktop.open_window(win)
    return win


def arp_qicon():
    return QIcon(arp_icon(32))

