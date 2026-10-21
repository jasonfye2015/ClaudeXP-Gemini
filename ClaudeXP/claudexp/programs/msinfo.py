"""System Information (msinfo32): the PC as Windows sees it in 2001. System Summary, Hardware Resources,
Components (display, sound, modem, drives...), Software Environment (running tasks, startup programs)."""
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (QHBoxLayout, QHeaderView, QLabel, QMenuBar, QSplitter, QTreeWidget, QTreeWidgetItem,
                               QVBoxLayout, QWidget)

from .. import clock, network
from ..wm import XPWindow
from .notepad import MENU_STYLE


def msinfo_icon():
    pm = QPixmap(32, 32)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(QPen(QColor("#404040"), 1))
    p.setBrush(QColor("#D8D4C4"))
    p.drawRoundedRect(QRectF(3.5, 5.5, 22, 17), 2, 2)
    p.fillRect(QRectF(6, 8, 17, 12), QColor("#2A5DD6"))
    p.setPen(QPen(QColor("#1C5FC4"), 1))
    p.setBrush(QColor("white"))
    p.drawEllipse(QRectF(17.5, 15.5, 13, 13))
    p.setPen(QPen(QColor("#1C5FC4"), 2))
    p.drawLine(24, 20, 24, 26)
    p.drawPoint(24, 18)
    p.end()
    return QIcon(pm)


def _summary():
    from .. import user
    data = user.account().data
    now = clock.now()
    mem_free = 108 + (now.minute % 30)
    return [("OS Name", "Microsoft Windows XP Home Edition"), ("Version", "5.1.2600 Build 2600"),
            ("OS Manufacturer", "Microsoft Corporation"), ("System Name", data.get("computer") or "HOME-XP"),
            ("System Manufacturer", "ClaudeXP Computer Corp."), ("System Model", "CX-866 Desktop"),
            ("System Type", "X86-based PC"),
            ("Processor", "x86 Family 6 Model 8 Stepping 6 GenuineIntel ~866 Mhz"),
            ("BIOS Version/Date", "American Megatrends Inc. 1007, 9/14/2001"), ("SMBIOS Version", "2.3"),
            ("Windows Directory", "C:\\WINDOWS"), ("System Directory", "C:\\WINDOWS\\System32"),
            ("Boot Device", "\\Device\\HarddiskVolume1"), ("Locale", "United States"),
            ("Hardware Abstraction Layer", "Version = \"5.1.2600.0 (xpclient.010817-1148)\""),
            ("User Name", f"{data.get('computer') or 'HOME-XP'}\\{data.get('name', 'User')}"),
            ("Time Zone", "Eastern Daylight Time"), ("Total Physical Memory", "256.00 MB"),
            ("Available Physical Memory", f"{mem_free}.27 MB"), ("Total Virtual Memory", "868.48 MB"),
            ("Available Virtual Memory", f"{mem_free + 520}.16 MB"), ("Page File Space", "612.48 MB"),
            ("Page File", "C:\\pagefile.sys")]


def _drives():
    from ..explorer import vfs
    from ..explorer.dialogs import size_text
    rows = []
    for d in vfs.drives():
        usage = d.usage()
        kind = {"hdd": "Local Fixed Disk", "external": "Removable Disk", "floppy": "3 1/2 Inch Floppy Drive",
                "cd": "CD-ROM Disc"}[d.kind]
        rows += [("Drive", f"{d.letter}:"), ("Description", kind)]
        if usage:
            rows += [("Size", size_text(usage[0])), ("Free Space", size_text(usage[1])),
                     ("File System", "NTFS" if d.kind == "hdd" else "FAT32")]
        else:
            rows.append(("Media Loaded", "No"))
        rows.append(("", ""))
    return rows


def _tasks():
    rows = []
    try:
        from .taskmgr import SYSTEM
        for img, user_, mem in SYSTEM:
            if img != "System Idle Process":
                rows.append((img.lower(), f"c:\\windows\\system32\\{img.lower()}" if img != "System" else ""))
    except ImportError:
        pass
    return rows


SECTIONS = {
    "System Summary": _summary,
    "Hardware Resources/IRQs": lambda: [("IRQ 0", "System timer"), ("IRQ 1", "Standard 101/102-Key Keyboard"),
                                        ("IRQ 3", "U.S. Robotics 56K Voice INT"), ("IRQ 5", "Creative SB Live! (WDM)"),
                                        ("IRQ 6", "Standard floppy disk controller"), ("IRQ 8", "System CMOS/real time clock"),
                                        ("IRQ 11", "NVIDIA RIVA TNT2 Model 64"), ("IRQ 12", "PS/2 Compatible Mouse"),
                                        ("IRQ 14", "Primary IDE Channel"), ("IRQ 15", "Secondary IDE Channel")],
    "Hardware Resources/Memory": lambda: [("0xA0000-0xBFFFF", "PCI bus"), ("0xD0000000-0xD7FFFFFF",
                                                                           "NVIDIA RIVA TNT2 Model 64"),
                                          ("0xFFFE0000-0xFFFFFFFF", "System board")],
    "Components/Display": lambda: [("Name", "NVIDIA RIVA TNT2 Model 64"), ("Adapter RAM", "32.00 MB (33,554,432 bytes)"),
                                   ("Driver Version", "6.13.10.2832"), ("Resolution", "1152 x 864 x 60 hertz"),
                                   ("Bits/Pixel", "32")],
    "Components/Sound Device": lambda: [("Name", "Creative SB Live! (WDM)"), ("Manufacturer", "Creative Technology Ltd."),
                                        ("Status", "OK")],
    "Components/Modem": lambda: [("Name", "U.S. Robotics 56K Voice INT"), ("Attached To", "COM3"),
                                 ("Max Baud Rate", "115200"), ("Status", "Connected" if network.is_connected() else "OK")],
    "Components/Storage/Drives": _drives,
    "Components/Ports/Serial": lambda: [("Name", "Communications Port (COM1)"), ("Status", "OK")],
    "Components/USB": lambda: [("Name", "VIA Rev 5 or later USB Universal Host Controller"),
                               ("Device", "USB Mass Storage Device (External Drive)")],
    "Software Environment/Running Tasks": _tasks,
    "Software Environment/Startup Programs": lambda: [("ctfmon", "C:\\WINDOWS\\System32\\ctfmon.exe"),
                                                      ("ClaudeShield", "C:\\Program Files\\ClaudeShield AntiVirus\\shieldtray.exe"),
                                                      ("ClaudeAIM", "C:\\Program Files\\ClaudeAIM\\ClaudeAIM.exe /min")],
    "Internet Settings": lambda: [("Connection", "America Online (dial-up)"), ("Browser", "Netscape Navigator 4.79"),
                                  ("E-mail", "Outlook Express 6")],
}


def open_msinfo(desktop):
    body = QWidget()
    body.setObjectName("mi")
    body.setAttribute(Qt.WA_StyledBackground, True)
    body.setStyleSheet(MENU_STYLE + "QWidget#mi { background: #ECE9D8; } QTreeWidget { font-family: Tahoma; "
                                    "font-size: 11px; background: white; }")
    v = QVBoxLayout(body)
    v.setContentsMargins(0, 0, 0, 0)
    menu = QMenuBar()
    menu.addMenu("&File").addAction("E&xit", lambda: win.request_close())
    for name in ("&Edit", "&View", "&Tools", "&Help"):
        menu.addMenu(name)
    v.addWidget(menu)
    split = QSplitter(Qt.Horizontal)
    tree = QTreeWidget()
    tree.setHeaderHidden(True)
    nodes = {}
    for path in SECTIONS:
        parent = None
        parts = path.split("/")
        for depth in range(len(parts)):
            key = "/".join(parts[:depth + 1])
            if key not in nodes:
                item = QTreeWidgetItem([parts[depth]])
                item.setData(0, Qt.UserRole, key)
                (parent.addChild(item) if parent else tree.addTopLevelItem(item))
                nodes[key] = item
            parent = nodes[key]
    tree.expandAll()
    table = QTreeWidget()
    table.setRootIsDecorated(False)
    table.setHeaderLabels(["Item", "Value"])
    table.header().setSectionResizeMode(1, QHeaderView.Stretch)
    table.setColumnWidth(0, 200)

    def show(item, _prev=None):
        if item is None:
            return
        key = item.data(0, Qt.UserRole)
        table.clear()
        fn = SECTIONS.get(key)
        if fn is None:
            return
        for k, val in fn():
            table.addTopLevelItem(QTreeWidgetItem([k, val]))

    tree.currentItemChanged.connect(show)
    split.addWidget(tree)
    split.addWidget(table)
    split.setSizes([200, 480])
    v.addWidget(split, 1)
    win = XPWindow(desktop, "System Information", body, msinfo_icon(), (720, 480))
    body.frame = win
    desktop.open_window(win)
    tree.setCurrentItem(nodes["System Summary"])
    return win
