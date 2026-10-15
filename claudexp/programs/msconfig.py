"""System Configuration Utility (msconfig): General, SYSTEM.INI, WIN.INI, BOOT.INI, Services and Startup.

The Startup tab really decides what ClaudeXP starts at log on, and /NOGUIBOOT and /SOS on the BOOT.INI tab really
change the boot screen (see startup.py). Saving changes asks to restart, and while Windows is in Selective or
Diagnostic Startup mode, XP's 'You have used the System Configuration Utility...' notice appears at every log on.
"""
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (QButtonGroup, QCheckBox, QHBoxLayout, QHeaderView, QLabel, QPushButton, QRadioButton,
                               QSpinBox, QTextEdit, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget)

from .. import startup
from ..cpl_extra import group, sheet

SERVICES = [  # (service, essential, manufacturer, status)
    ("Alerter", "", "Microsoft Corporation", "Stopped"),
    ("Automatic Updates", "", "Microsoft Corporation", "Running"),
    ("ClaudeXP Language Model", "", "ClaudeXP", "Running"),
    ("DHCP Client", "", "Microsoft Corporation", "Running"),
    ("Event Log", "Yes", "Microsoft Corporation", "Running"),
    ("Fast User Switching Compatibility", "", "Microsoft Corporation", "Running"),
    ("Help and Support", "", "Microsoft Corporation", "Running"),
    ("Messenger", "", "Microsoft Corporation", "Running"),
    ("Print Spooler", "", "Microsoft Corporation", "Running"),
    ("QuickTime Updater", "", "Apple Computer, Inc.", "Stopped"),
    ("RealNetworks Scheduler", "", "RealNetworks, Inc.", "Running"),
    ("Remote Access Connection Manager", "", "Microsoft Corporation", "Running"),
    ("System Restore Service", "", "Microsoft Corporation", "Running"),
    ("Themes", "", "Microsoft Corporation", "Running"),
    ("Windows Audio", "", "Microsoft Corporation", "Running"),
    ("Windows Time", "", "Microsoft Corporation", "Running"),
]
SYSTEM_INI = {
    "[drivers]": ["wave=mmdrv.dll", "timer=timer.drv"],
    "[mci]": [],
    "[driver32]": [],
    "[386enh]": ["woafont=dosapp.FON", "EGA80WOA.FON=EGA80WOA.FON", "EGA40WOA.FON=EGA40WOA.FON",
                 "CGA80WOA.FON=CGA80WOA.FON", "CGA40WOA.FON=CGA40WOA.FON"],
}
WIN_INI = {
    "[fonts]": [],
    "[extensions]": [],
    "[mci extensions]": [],
    "[files]": [],
    "[Mail]": ["MAPI=1", "CMCDLLNAME32=mapi32.dll", "CMC=1", "MAPIX=1", "MAPIXVER=1.0.0.1", "OLEMessaging=1"],
    "[MCI Extensions.BAK]": ["aif=MPEGVideo", "aifc=MPEGVideo", "aiff=MPEGVideo", "asf=MPEGVideo", "m3u=MPEGVideo",
                             "mid=MPEGVideo", "mp3=MPEGVideo", "wma=MPEGVideo"],
}


def msconfig_pixmap(size=32):
    """A computer with a gear, msconfig's icon."""
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    s = size / 32
    p.setPen(QPen(QColor("#2A3A5A"), max(1.0, s)))
    p.setBrush(QColor("#D8DEE8"))
    p.drawRoundedRect(QRectF(3 * s, 4 * s, 22 * s, 16 * s), 2 * s, 2 * s)
    p.setBrush(QColor("#3A6AC8"))
    p.drawRect(QRectF(5 * s, 6 * s, 18 * s, 12 * s))
    p.setBrush(QColor("#A8B0C0"))
    p.drawRect(QRectF(10 * s, 20 * s, 8 * s, 3 * s))
    p.drawRect(QRectF(6 * s, 23 * s, 16 * s, 2 * s))
    p.setBrush(QColor("#F0C030"))
    p.setPen(QPen(QColor("#7A5A10"), max(1.0, s)))
    import math
    c = QPointF(23 * s, 22 * s)
    pts = []
    for i in range(16):
        a = math.pi * 2 * i / 16
        r = (8 if i % 2 == 0 else 5.6) * s
        pts.append(QPointF(c.x() + math.cos(a) * r, c.y() + math.sin(a) * r))
    from PySide6.QtGui import QPolygonF
    p.drawPolygon(QPolygonF(pts))
    p.setBrush(QColor("#FFFFFF"))
    p.drawEllipse(c, 2.4 * s, 2.4 * s)
    p.end()
    return pm


def msconfig_icon():
    ic = QIcon()
    for sz in (16, 32):
        ic.addPixmap(msconfig_pixmap(sz))
    return ic


def _checked_tree(headers, rows, checked):
    """A tree of checkable rows: rows [(texts...)], checked(texts) -> bool."""
    tree = QTreeWidget()
    tree.setRootIsDecorated(False)
    tree.setHeaderLabels(headers)
    tree.header().setSectionResizeMode(QHeaderView.ResizeToContents)
    tree.setStyleSheet("QTreeWidget { background: white; font-family: Tahoma; font-size: 11px; }")
    for texts in rows:
        it = QTreeWidgetItem(list(texts))
        it.setFlags(it.flags() | Qt.ItemIsUserCheckable)
        it.setCheckState(0, Qt.Checked if checked(texts) else Qt.Unchecked)
        tree.addTopLevelItem(it)
    return tree


def _all(tree, on):
    for i in range(tree.topLevelItemCount()):
        it = tree.topLevelItem(i)
        if not it.isDisabled():
            it.setCheckState(0, Qt.Checked if on else Qt.Unchecked)


def _ini_tab(sections, enabled):
    tree = QTreeWidget()
    tree.setHeaderHidden(True)
    tree.setStyleSheet("QTreeWidget { background: white; font-family: Tahoma; font-size: 11px; }")
    for head, lines in sections.items():
        top = QTreeWidgetItem([head])
        top.setFlags(top.flags() | Qt.ItemIsUserCheckable)
        top.setCheckState(0, Qt.Checked if enabled else Qt.Unchecked)
        for line in lines:
            it = QTreeWidgetItem([line])
            it.setFlags(it.flags() | Qt.ItemIsUserCheckable)
            it.setCheckState(0, Qt.Checked if enabled else Qt.Unchecked)
            top.addChild(it)
        tree.addTopLevelItem(top)
        top.setExpanded(True)
    w = QWidget()
    row = QHBoxLayout(w)
    row.addWidget(tree, 1)
    col = QVBoxLayout()
    buttons = {}
    for label in ("Move Up", "Move Down", "Enable", "Disable", "Find...", "New", "Edit", "Enable All",
                  "Disable All"):
        b = QPushButton(label)
        b.setFixedWidth(90)
        b.setEnabled(label in ("Enable All", "Disable All"))
        col.addWidget(b)
        buttons[label] = b
    col.addStretch()
    row.addLayout(col)

    def set_all(on):
        for i in range(tree.topLevelItemCount()):
            top = tree.topLevelItem(i)
            top.setCheckState(0, Qt.Checked if on else Qt.Unchecked)
            for j in range(top.childCount()):
                top.child(j).setCheckState(0, Qt.Checked if on else Qt.Unchecked)
    buttons["Enable All"].clicked.connect(lambda: set_all(True))
    buttons["Disable All"].clicked.connect(lambda: set_all(False))

    def any_on():
        return any(tree.topLevelItem(i).checkState(0) == Qt.Checked for i in range(tree.topLevelItemCount()))
    return w, any_on, set_all


def _boot_ini_text(data):
    flags = " ".join(f"/{f}" + (f":{data['safeboot']}" if f == "SAFEBOOT" else "") for f in startup.BOOT_FLAGS
                     if f in data["boot"])
    return ("[boot loader]\n"
            f"timeout={data['timeout']}\n"
            "default=multi(0)disk(0)rdisk(0)partition(1)\\WINDOWS\n"
            "[operating systems]\n"
            'multi(0)disk(0)rdisk(0)partition(1)\\WINDOWS="Microsoft Windows XP Professional" /fastdetect'
            + (f" {flags}" if flags else ""))


def open_msconfig(desktop):
    data = startup.load()

    # ---- General ----
    general = QWidget()
    gv = QVBoxLayout(general)
    choice = QButtonGroup(general)
    normal = QRadioButton("Normal Startup - load all device drivers and services")
    diag = QRadioButton("Diagnostic Startup - load basic devices and services only")
    sel = QRadioButton("Selective Startup")
    for i, r in enumerate((normal, diag, sel)):
        choice.addButton(r, i)
    sub = QWidget()
    sv = QVBoxLayout(sub)
    sv.setContentsMargins(22, 0, 0, 0)
    c_sys = QCheckBox("Process SYSTEM.INI File")
    c_win = QCheckBox("Process WIN.INI File")
    c_svc = QCheckBox("Load System Services")
    c_start = QCheckBox("Load Startup Items")
    boot_orig = QRadioButton("Use Original BOOT.INI")
    boot_mod = QRadioButton("Use Modified BOOT.INI")
    for w in (c_sys, c_win, c_svc, c_start, boot_orig, boot_mod):
        sv.addWidget(w)
    gv.addWidget(group("Startup Selection", normal, diag, sel, sub))
    row = QHBoxLayout()
    row.addStretch()
    restore = QPushButton("Launch System Restore")
    expand = QPushButton("Expand File...")
    row.addWidget(restore)
    row.addWidget(expand)
    gv.addLayout(row)
    gv.addStretch()

    # ---- SYSTEM.INI / WIN.INI ----
    sys_tab, sys_on, sys_all = _ini_tab(SYSTEM_INI, data["system_ini"])
    win_tab, win_on, win_all = _ini_tab(WIN_INI, data["win_ini"])

    # ---- BOOT.INI ----
    boot = QWidget()
    bv = QVBoxLayout(boot)
    text = QTextEdit()
    text.setReadOnly(True)
    text.setFixedHeight(96)
    text.setStyleSheet("QTextEdit { background: white; font-family: 'Courier New'; font-size: 11px; }")
    bv.addWidget(text)
    brow = QHBoxLayout()
    for label in ("Check All Boot Paths", "Set as Default", "Move Up", "Move Down"):
        b = QPushButton(label)
        b.setEnabled(label == "Check All Boot Paths")
        brow.addWidget(b)
    bv.addLayout(brow)
    flags = {f: QCheckBox(f"/{f}") for f in startup.BOOT_FLAGS}
    safe_modes = {m: QRadioButton(m.title() if m != "DSREPAIR" else "DSREPAIR")
                  for m in ("MINIMAL", "NETWORK", "DSREPAIR")}
    opts = QWidget()
    ov = QVBoxLayout(opts)
    ov.setContentsMargins(0, 0, 0, 0)
    ov.addWidget(flags["SAFEBOOT"])
    safe_row = QHBoxLayout()
    safe_row.addSpacing(22)
    for r in safe_modes.values():
        safe_row.addWidget(r)
    safe_row.addStretch()
    ov.addLayout(safe_row)
    for f in ("NOGUIBOOT", "BOOTLOG", "BASEVIDEO", "SOS"):
        ov.addWidget(flags[f])
    timeout = QSpinBox()
    timeout.setRange(3, 999)
    timeout.setSuffix(" sec.")
    timeout.setValue(int(data["timeout"]))
    trow = QHBoxLayout()
    trow.addWidget(QLabel("Timeout:"))
    trow.addWidget(timeout)
    trow.addStretch()
    bv.addWidget(group("Boot Options", opts, trow))
    note = QLabel("/NOGUIBOOT boots to a black screen without the Windows logo; /SOS lists the drivers as they "
                  "load.")
    note.setWordWrap(True)
    note.setStyleSheet("color: #555;")
    bv.addWidget(note)
    bv.addStretch()

    # ---- Services ----
    services = QWidget()
    svv = QVBoxLayout(services)
    svc_tree = _checked_tree(["Service", "Essential", "Manufacturer", "Status"], SERVICES,
                             lambda t: t[0] not in data["services_off"])
    for i in range(svc_tree.topLevelItemCount()):
        it = svc_tree.topLevelItem(i)
        if it.text(1) == "Yes":
            it.setDisabled(True)
    svv.addWidget(svc_tree)
    srow = QHBoxLayout()
    hide_ms = QCheckBox("Hide All Microsoft Services")
    srow.addWidget(hide_ms)
    srow.addStretch()
    s_on, s_off = QPushButton("Enable All"), QPushButton("Disable All")
    srow.addWidget(s_on)
    srow.addWidget(s_off)
    svv.addLayout(srow)
    s_on.clicked.connect(lambda: _all(svc_tree, True))
    s_off.clicked.connect(lambda: _all(svc_tree, False))
    hide_ms.toggled.connect(lambda on: [svc_tree.topLevelItem(i).setHidden(
        on and svc_tree.topLevelItem(i).text(2) == "Microsoft Corporation") for i in range(svc_tree.topLevelItemCount())])

    # ---- Startup ----
    start = QWidget()
    stv = QVBoxLayout(start)
    keys = list(startup.ITEMS)
    st_tree = _checked_tree(["Startup Item", "Command", "Location"], [startup.ITEMS[k] for k in keys],
                            lambda t: keys[[startup.ITEMS[k] for k in keys].index(t)] not in data["off"])
    stv.addWidget(st_tree)
    strow = QHBoxLayout()
    strow.addStretch()
    a_on, a_off = QPushButton("Enable All"), QPushButton("Disable All")
    strow.addWidget(a_on)
    strow.addWidget(a_off)
    stv.addLayout(strow)
    a_on.clicked.connect(lambda: _all(st_tree, True))
    a_off.clicked.connect(lambda: _all(st_tree, False))

    # ---- keeping the tabs in step ----
    state = {"busy": False}

    def collect():
        d = dict(data)
        d["off"] = [keys[i] for i in range(st_tree.topLevelItemCount())
                    if st_tree.topLevelItem(i).checkState(0) != Qt.Checked]
        d["services_off"] = [svc_tree.topLevelItem(i).text(0) for i in range(svc_tree.topLevelItemCount())
                             if svc_tree.topLevelItem(i).checkState(0) != Qt.Checked]
        d["boot"] = [f for f, c in flags.items() if c.isChecked()]
        d["safeboot"] = next((m for m, r in safe_modes.items() if r.isChecked()), "MINIMAL")
        d["timeout"] = timeout.value()
        d["system_ini"], d["win_ini"] = sys_on(), win_on()
        return d

    def refresh_general():
        state["busy"] = True
        d = collect()
        m = startup.mode(d)
        {"normal": normal, "diagnostic": diag, "selective": sel}[m].setChecked(True)
        c_sys.setChecked(d["system_ini"])
        c_win.setChecked(d["win_ini"])
        c_svc.setChecked(len(d["services_off"]) < len(SERVICES) - 1)
        c_start.setChecked(len(d["off"]) < len(keys))
        c_start.setTristate(False)
        (boot_mod if d["boot"] else boot_orig).setChecked(True)
        for w in (c_sys, c_win, c_svc, c_start, boot_orig, boot_mod):
            w.setEnabled(m == "selective")
        text.setPlainText(_boot_ini_text(d))
        for r in safe_modes.values():
            r.setEnabled(flags["SAFEBOOT"].isChecked())
        state["busy"] = False

    def pick_mode(i):
        if state["busy"]:
            return
        if i == 0:                         # Normal: everything back on
            _all(st_tree, True)
            _all(svc_tree, True)
            for c in flags.values():
                c.setChecked(False)
            sys_all(True)
            win_all(True)
        elif i == 1:                       # Diagnostic: no startup items, only essential services
            _all(st_tree, False)
            _all(svc_tree, False)
        refresh_general()

    def general_box(box, on):
        if state["busy"]:
            return
        if box is c_start:
            _all(st_tree, on)
        elif box is c_svc:
            _all(svc_tree, on)
        elif box is c_sys:
            sys_all(on)
        elif box is c_win:
            win_all(on)
        refresh_general()

    choice.idClicked.connect(pick_mode)
    for box in (c_sys, c_win, c_svc, c_start):
        box.clicked.connect(lambda on, box=box: general_box(box, on))
    boot_orig.clicked.connect(lambda: ([c.setChecked(False) for c in flags.values()], refresh_general()))
    for c in flags.values():
        c.toggled.connect(lambda _on: refresh_general() if not state["busy"] else None)
    for m, r in safe_modes.items():
        r.setChecked(m == data["safeboot"])
        r.toggled.connect(lambda _on: refresh_general() if not state["busy"] else None)
    for f, c in flags.items():
        state["busy"] = True
        c.setChecked(f in data["boot"])
        state["busy"] = False
    timeout.valueChanged.connect(lambda _v: refresh_general())
    st_tree.itemChanged.connect(lambda *_: refresh_general() if not state["busy"] else None)
    svc_tree.itemChanged.connect(lambda *_: refresh_general() if not state["busy"] else None)
    restore.clicked.connect(lambda: __import__("claudexp.programs", fromlist=["launch"]).launch(desktop, "sysrestore"))
    expand.clicked.connect(lambda: _message(desktop, "Expand One File", "Insert your Windows XP CD to expand files "
                                                                       "from it."))
    refresh_general()

    def save():
        d = collect()
        if d == data:
            return
        d["nag_off"] = False                   # new changes: the log-on notice comes back
        startup.save(d)
        data.update(d)
        _ask_restart(desktop)

    return sheet(desktop, "System Configuration Utility", msconfig_icon(),
                 [("General", general), ("SYSTEM.INI", sys_tab), ("WIN.INI", win_tab), ("BOOT.INI", boot),
                  ("Services", services), ("Startup", start)], save, width=560)


def _message(desktop, title, text):
    from ..network import DialogBody, _fixed_window
    body = DialogBody()
    v = QVBoxLayout(body)
    lab = QLabel(text)
    lab.setWordWrap(True)
    v.addWidget(lab)
    row = QHBoxLayout()
    row.addStretch()
    ok = QPushButton("OK")
    ok.setFixedSize(75, 23)
    row.addWidget(ok)
    v.addLayout(row)
    holder = {}
    holder["win"] = win = _fixed_window(desktop, title, body, lambda: desktop.close_window(holder["win"]))
    ok.clicked.connect(lambda: desktop.close_window(win))
    desktop.open_window(win)


def _ask_restart(desktop):
    """XP's 'You must restart your computer for some of the changes to take effect.'"""
    from ..network import DialogBody, _fixed_window
    body = DialogBody()
    v = QVBoxLayout(body)
    lab = QLabel("You must restart your computer for some of the changes made by System Configuration to take "
                 "effect.\n\nAfter restarting, a message will be displayed, and the System Configuration utility "
                 "will start.")
    lab.setWordWrap(True)
    lab.setFixedWidth(330)
    v.addWidget(lab)
    row = QHBoxLayout()
    row.addStretch()
    restart, later = QPushButton("Restart"), QPushButton("Exit Without Restart")
    row.addWidget(restart)
    row.addWidget(later)
    v.addLayout(row)
    holder = {}
    holder["win"] = win = _fixed_window(desktop, "System Configuration", body,
                                        lambda: desktop.close_window(holder["win"]))
    restart.clicked.connect(lambda: (desktop.close_window(win), desktop.restart_requested.emit()))
    later.clicked.connect(lambda: desktop.close_window(win))
    desktop.open_window(win)


def at_logon(desktop):
    """In Selective or Diagnostic Startup, XP nags at every log on and opens msconfig."""
    data = startup.load()
    if startup.mode(data) == "normal" or data.get("nag_off"):
        return
    from ..network import DialogBody, _fixed_window
    body = DialogBody()
    v = QVBoxLayout(body)
    lab = QLabel("You have used the System Configuration Utility to make changes to the way Windows starts.\n\n"
                 "The System Configuration Utility is currently in Diagnostic or Selective Startup mode, causing "
                 "this message to be displayed and the utility to run every time Windows starts.\n\n"
                 "Choose the Normal Startup mode on the General tab to start Windows normally and undo the changes "
                 "you made using the System Configuration Utility.")
    lab.setWordWrap(True)
    lab.setFixedWidth(380)
    v.addWidget(lab)
    dont = QCheckBox("Don't show this message or launch the System Configuration Utility when Windows starts.")
    dont.setStyleSheet("font-family: Tahoma; font-size: 11px;")
    v.addWidget(dont)
    row = QHBoxLayout()
    row.addStretch()
    ok = QPushButton("OK")
    ok.setFixedSize(75, 23)
    row.addWidget(ok)
    v.addLayout(row)
    holder = {}

    def done():
        desktop.close_window(holder["win"])
        if dont.isChecked():
            d = startup.load()
            d["nag_off"] = True
            startup.save(d)
        else:
            open_msconfig(desktop)
    holder["win"] = _fixed_window(desktop, "System Configuration Utility", body, done)
    ok.clicked.connect(done)
    desktop.open_window(holder["win"])
