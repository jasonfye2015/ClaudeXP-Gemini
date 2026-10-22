"""The Settings app: the categories down the left under your account, and pages of cards on the right - System
(About, Display, Sound, Notifications, Power, Recovery), Bluetooth & devices, Network & internet, Personalization
(Background, Colors, Lock screen, Themes, Taskbar), Apps, Accounts, Time & language, Gaming, Accessibility, Privacy
& security and Windows Update. The deeper dialogs are the Control Panel's, which Windows 11 still carries."""
import json

from PySide6.QtCore import QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (QComboBox, QFrame, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
                               QPushButton, QScrollArea, QStackedWidget, QVBoxLayout, QWidget)
from shiboken6 import isValid

from . import clock, display, sound, user
from .paths import DATA, lock_images
from .wm import MicaWindow

CPL_FILE = DATA / "cpl.json"
CATEGORIES = [("system", "System", "#0067C0"), ("bluetooth", "Bluetooth & devices", "#0F6CBD"),
              ("network", "Network & internet", "#0078D4"), ("personalization", "Personalization", "#C239B3"),
              ("apps", "Apps", "#CA5010"), ("accounts", "Accounts", "#107C10"), ("time", "Time & language", "#2D7D9A"),
              ("gaming", "Gaming", "#4A5459"), ("accessibility", "Accessibility", "#0067C0"),
              ("privacy", "Privacy & security", "#5D5A58"), ("update", "Windows Update", "#0078D4")]
ALIASES = {"about": "system", "display": "system", "sound": "system", "notifications": "system", "power": "system",
           "taskbar": "personalization", "background": "personalization", "colors": "personalization",
           "lock": "personalization", "start": "personalization", "themes": "personalization"}
STYLE = """
QWidget { font-family: 'Segoe UI Variable Text', 'Segoe UI'; font-size: 12px; color: #1A1A1A; }
QWidget#settings { background: #F3F3F3; }
QListWidget#nav { background: transparent; border: none; outline: none; font-size: 13px; }
QListWidget#nav::item { height: 36px; padding-left: 8px; border-radius: 4px; margin: 1px 0; }
QListWidget#nav::item:hover { background: rgba(0, 0, 0, 14); }
QListWidget#nav::item:selected { background: rgba(0, 0, 0, 20); color: #1A1A1A; }
QLineEdit#find { background: #FFFFFF; border: 1px solid #E0E0E0; border-bottom: 1px solid #8A8A8A; border-radius: 4px;
                 padding: 5px 10px; }
QLineEdit#find:focus { border-bottom: 2px solid #0067C0; }
QScrollArea { background: transparent; border: none; }
QWidget#page { background: transparent; }
QLabel#title { font-size: 26px; font-weight: 600; }
QLabel#crumb { font-size: 12px; color: #5C5C5C; }
QLabel#section { font-size: 14px; font-weight: 600; margin-top: 8px; }
QFrame#card { background: #FBFBFB; border: 1px solid #E5E5E5; border-radius: 6px; }
QFrame#card:hover { background: #F6F6F6; }
QLabel#cardtitle { font-size: 13px; }
QLabel#cardsub { font-size: 11px; color: #5C5C5C; }
QPushButton { background: #FBFBFB; border: 1px solid #D0D0D0; border-radius: 4px; padding: 5px 14px; min-height: 20px; }
QPushButton:hover { background: #F0F0F0; }
QPushButton#accent { background: #0067C0; color: white; border-color: #0067C0; }
QPushButton#accent:hover { background: #1975C5; }
QComboBox { background: #FBFBFB; border: 1px solid #D0D0D0; border-radius: 4px; padding: 4px 10px; min-width: 140px; }
QScrollBar:vertical { background: transparent; width: 10px; margin: 2px; }
QScrollBar::handle:vertical { background: rgba(0, 0, 0, 60); border-radius: 3px; min-height: 24px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
"""
_open = {}


def cpl_settings():
    try:
        return json.loads(CPL_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save_cpl(**changes):
    data = cpl_settings()
    data.update(changes)
    CPL_FILE.parent.mkdir(parents=True, exist_ok=True)
    CPL_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


class Toggle(QWidget):
    """Windows 11's switch: a pill with a knob, On or Off."""
    toggled = Signal(bool)

    def __init__(self, on=False, on_change=None):
        super().__init__()
        self.on = bool(on)
        self.setFixedSize(92, 22)
        self.setCursor(Qt.PointingHandCursor)
        if on_change:
            self.toggled.connect(on_change)

    def mousePressEvent(self, event):
        self.on = not self.on
        self.update()
        self.toggled.emit(self.on)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        pill = QRectF(self.width() - 44, 1, 42, 20)
        accent = display.get().accent()
        if self.on:
            p.setPen(Qt.NoPen)
            p.setBrush(accent)
            p.drawRoundedRect(pill, 10, 10)
            p.setBrush(QColor("white"))
            p.drawEllipse(QRectF(pill.right() - 17, 4, 14, 14))
        else:
            p.setPen(QPen(QColor("#8A8A8A"), 1))
            p.setBrush(QColor(0, 0, 0, 10))
            p.drawRoundedRect(pill, 10, 10)
            p.setPen(Qt.NoPen)
            p.setBrush(QColor("#5C5C5C"))
            p.drawEllipse(QRectF(pill.left() + 4, 5, 12, 12))
        p.setPen(QColor("#1A1A1A"))
        from .style import font
        p.setFont(font(12))
        p.drawText(QRectF(0, 0, self.width() - 50, self.height()), Qt.AlignRight | Qt.AlignVCenter, "On" if self.on else "Off")


def _cat_icon(colour, letter, size=18):
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(colour))
    p.drawRoundedRect(QRectF(0, 0, size, size), 4, 4)
    from .style import font
    p.setFont(font(11, 600))
    p.setPen(QColor("white"))
    p.drawText(pm.rect(), Qt.AlignCenter, letter)
    p.end()
    return QIcon(pm)


class SettingsBody(QWidget):
    def __init__(self, desktop):
        super().__init__()
        self.desktop = desktop
        self.setObjectName("settings")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(STYLE)
        self.frame = None
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        # ---- the left column ----
        left = QWidget()
        left.setFixedWidth(280)
        lv = QVBoxLayout(left)
        lv.setContentsMargins(16, 16, 8, 16)
        lv.setSpacing(8)
        head = QWidget()
        head.setFixedHeight(64)
        head.paintEvent = lambda e, w=head: self._paint_head(w)
        head.setCursor(Qt.PointingHandCursor)
        head.mousePressEvent = lambda e: self.show_page("accounts")
        lv.addWidget(head)
        self.find = QLineEdit()
        self.find.setObjectName("find")
        self.find.setPlaceholderText("Find a setting")
        self.find.textChanged.connect(self._filter_nav)
        lv.addWidget(self.find)
        self.nav = QListWidget()
        self.nav.setObjectName("nav")
        self.nav.setIconSize(QSize(18, 18))
        for key, name, colour in CATEGORIES:
            it = QListWidgetItem(_cat_icon(colour, name[0]), name)
            it.setData(Qt.UserRole, key)
            self.nav.addItem(it)
        self.nav.currentRowChanged.connect(self._nav_changed)
        lv.addWidget(self.nav, 1)
        root.addWidget(left)
        # ---- the pages ----
        self.stack = QStackedWidget()
        root.addWidget(self.stack, 1)
        self.pages = {}
        for key, name, _c in CATEGORIES:
            self.pages[key] = self._build_page(key, name)
            self.stack.addWidget(self.pages[key])
        self.nav.setCurrentRow(0)

    def _paint_head(self, w):
        p = QPainter(w)
        p.setRenderHint(QPainter.Antialiasing)
        user.draw_user_picture(p, QRectF(4, 4, 56, 56).toRect(), circle=True)
        from .style import font
        p.setFont(font(14, 600))
        p.setPen(QColor("#1A1A1A"))
        p.drawText(QRectF(72, 10, w.width() - 72, 22), Qt.AlignLeft | Qt.AlignVCenter, user.user_name())
        p.setFont(font(11))
        p.setPen(QColor("#5C5C5C"))
        p.drawText(QRectF(72, 34, w.width() - 72, 18), Qt.AlignLeft | Qt.AlignVCenter, user.email_address())
        p.end()

    def _filter_nav(self, text):
        q = text.strip().lower()
        for i in range(self.nav.count()):
            it = self.nav.item(i)
            it.setHidden(bool(q) and q not in it.text().lower() and q not in self._page_text(it.data(Qt.UserRole)))

    def _page_text(self, key):
        page = self.pages.get(key)
        return " ".join(l.text().lower() for l in page.findChildren(QLabel)) if page is not None else ""

    def _nav_changed(self, row):
        if row < 0:
            return
        key = self.nav.item(row).data(Qt.UserRole)
        self.stack.setCurrentWidget(self.pages[key])

    def show_page(self, key):
        key = ALIASES.get(key, key)
        for i in range(self.nav.count()):
            if self.nav.item(i).data(Qt.UserRole) == key:
                self.nav.setCurrentRow(i)
                return

    # ---- building pages ----
    def _build_page(self, key, name):
        area = QScrollArea()
        area.setWidgetResizable(True)
        page = QWidget()
        page.setObjectName("page")
        v = QVBoxLayout(page)
        v.setContentsMargins(28, 20, 28, 20)
        v.setSpacing(6)
        crumb = QLabel(f"Settings  ›  {name}" if key != "system" else "Settings")
        crumb.setObjectName("crumb")
        v.addWidget(crumb)
        title = QLabel(name)
        title.setObjectName("title")
        v.addWidget(title)
        builder = getattr(self, f"_page_{key}")
        builder(v)
        v.addStretch()
        area.setWidget(page)
        return area

    def _card(self, v, title, sub="", control=None, slot=None):
        card = QFrame()
        card.setObjectName("card")
        h = QHBoxLayout(card)
        h.setContentsMargins(16, 10, 16, 10)
        text = QVBoxLayout()
        text.setSpacing(2)
        t = QLabel(title)
        t.setObjectName("cardtitle")
        text.addWidget(t)
        if sub:
            s = QLabel(sub)
            s.setObjectName("cardsub")
            s.setWordWrap(True)
            text.addWidget(s)
        h.addLayout(text, 1)
        if control is not None:
            h.addWidget(control)
        elif slot is not None:
            arrow = QLabel("›")
            arrow.setStyleSheet("font-size: 18px; color: #5C5C5C;")
            h.addWidget(arrow)
        if slot is not None:
            card.setCursor(Qt.PointingHandCursor)
            card.mousePressEvent = lambda e: slot()
        v.addWidget(card)
        return card

    def _section(self, v, text):
        lab = QLabel(text)
        lab.setObjectName("section")
        v.addWidget(lab)

    def _button(self, text, slot, accent=False):
        b = QPushButton(text)
        if accent:
            b.setObjectName("accent")
        b.clicked.connect(lambda _c=False: slot())
        return b

    def _cpl(self, func, *args, **kwargs):
        def go():
            from . import controlpanel
            getattr(controlpanel, func)(self.desktop, *args, **kwargs)
        return go

    def _launch(self, key):
        def go():
            from claudexp import programs
            programs.launch(self.desktop, key)
        return go

    # ---- System ----
    def _page_system(self, v):
        from .user import computer_name
        card = QFrame()
        card.setObjectName("card")
        h = QHBoxLayout(card)
        h.setContentsMargins(16, 14, 16, 14)
        pc = QLabel()
        pm = self.desktop.display.render(96, 54)
        pc.setPixmap(pm)
        h.addWidget(pc)
        info = QVBoxLayout()
        self.pc_name = QLabel(computer_name())
        self.pc_name.setStyleSheet("font-size: 15px; font-weight: 600;")
        info.addWidget(self.pc_name)
        spec = QLabel("ASUS TUF GAMING B650-PLUS WIFI  ·  Rename")
        spec.setObjectName("cardsub")
        info.addWidget(spec)
        h.addLayout(info, 1)
        rename = self._button("Rename", self._rename_pc)
        h.addWidget(rename)
        v.addWidget(card)
        self._card(v, "Display", "Monitors, brightness, night light, display profile",
                   slot=self._cpl("display_properties", tab="background"))
        self._card(v, "Sound", "Volume levels, output, input, sound devices", slot=self._cpl("sound_properties"))
        self._card(v, "Notifications", "Alerts from apps and system, do not disturb", slot=self._notifications)
        self._card(v, "Power", "Screen and sleep, power mode", control=self._power_combo())
        self._card(v, "Storage", "Storage space, drives, configuration rules", slot=self._launch("mycomputer"))
        self._card(v, "Multitasking", "Snap windows, desktops, task switching", control=Toggle(
            cpl_settings().get("snap_layouts", True), lambda on: save_cpl(snap_layouts=on)))
        self._card(v, "Recovery", "Reset this PC, advanced startup", slot=self._recovery)
        self._section(v, "About")
        now = clock.now()
        rows = [("Device name", computer_name()), ("Processor", "AMD Ryzen 7 7800X3D 8-Core Processor  4.20 GHz"),
                ("Installed RAM", "32.0 GB (31.7 GB usable)"), ("Device ID", "7A3F1C2E-2025-4B11-9C0D-WORKSTATION"),
                ("System type", "64-bit operating system, x64-based processor"),
                ("Pen and touch", "No pen or touch input is available for this display")]
        for k, val in rows:
            self._card(v, k, val)
        self._section(v, "Windows specifications")
        for k, val in (("Edition", "Windows 11 Home"), ("Version", "25H2"),
                       ("Installed on", f"{now:%m}/01/{now.year}"), ("OS build", "26200.6899"),
                       ("Experience", "Windows Feature Experience Pack 1000.26100.265.0")):
            self._card(v, k, val)

    def _rename_pc(self):
        from PySide6.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(self, "Rename your PC", "New name:", text=user.computer_name())
        if ok and name.strip():
            a = user.account()
            a.data["computer"] = name.strip().upper()
            user._save(a.data)
            a.changed.emit()
            self.pc_name.setText(user.computer_name())

    def _power_combo(self):
        combo = QComboBox()
        choices = [("Never", 0), ("5 minutes", 5), ("10 minutes", 10), ("15 minutes", 15), ("30 minutes", 30)]
        for label, mins in choices:
            combo.addItem("Screen off after " + label if mins else "Screen never turns off", mins)
        current = int(cpl_settings().get("screen_off", 10))
        combo.setCurrentIndex(max(0, next((i for i, c in enumerate(choices) if c[1] == current), 2)))
        combo.currentIndexChanged.connect(lambda i: save_cpl(screen_off=combo.itemData(i)))
        return combo

    def _notifications(self):
        from .tray import customize_notifications
        customize_notifications(self.desktop)

    def _recovery(self):
        from .dialogs import msgbox

        def go(answer):
            if answer == "Reset":
                main = self.desktop.window()
                if hasattr(main, "_install_windows"):
                    main._install_windows()
        msgbox(self.desktop, "Reset this PC", "This restarts the PC into the installation of Windows 11. Setup lets you "
               "keep or remove your files. Nothing is truly erased: what Setup removes goes to Claude11\\Recovery "
               "Backups.", "warning", ("Reset", "Cancel"), go)

    # ---- Bluetooth & devices ----
    def _page_bluetooth(self, v):
        self._card(v, "Bluetooth", "Discoverable as \"" + user.computer_name() + "\"", control=Toggle(True))
        self._section(v, "Devices")
        for name, sub in (("Wireless Mouse", "Connected"), ("Gaming Keyboard", "Connected"),
                          ("Headphones", "Connected, 80% battery")):
            self._card(v, name, sub)
        self._card(v, "Printers & scanners", "Preferences, troubleshoot", slot=self._printers)
        self._card(v, "Mouse", "Buttons, mouse pointer speed, scrolling", slot=self._cpl("mouse_properties"))
        self._card(v, "Autoplay", "Defaults for media and devices", control=Toggle(True))

    def _printers(self):
        try:
            from claudexp.printing import printers_and_faxes
            printers_and_faxes(self.desktop)
        except Exception:
            pass

    # ---- Network & internet ----
    def _page_network(self, v):
        from . import network
        self._card(v, "Wi-Fi", "HomeNetwork  ·  Connected, secured  ·  Wi-Fi 6E",
                   slot=lambda: network.get(self.desktop)._show_status())
        self._card(v, "Ethernet", "Not connected")
        self._card(v, "VPN", "Add, connect, manage")
        self._card(v, "Mobile hotspot", "Share your internet connection", control=Toggle(False))
        self._card(v, "Airplane mode", "Stop wireless communication", control=Toggle(False))
        self._card(v, "Advanced network settings", "View all network adapters, network reset",
                   slot=lambda: network.get(self.desktop)._show_status())

    # ---- Personalization ----
    def _page_personalization(self, v):
        preview = QLabel()
        preview.setPixmap(self.desktop.display.render(320, 180))
        preview.setStyleSheet("border-radius: 6px;")
        v.addWidget(preview)
        self._card(v, "Background", "Background image, color, slideshow",
                   slot=self._cpl("display_properties", tab="background"))
        self._section(v, "Colors")
        self._colour_grid(v)
        self._card(v, "Themes", "Install, create, manage", slot=self._cpl("display_properties"))
        self._card(v, "Lock screen", "Lock screen images, apps, animations", control=self._lock_combo())
        self._section(v, "Taskbar")
        s = cpl_settings()
        self._card(v, "Taskbar alignment", "Where the Start button and the pinned apps sit",
                   control=self._align_combo())
        self._card(v, "Search", "Show the search box on the taskbar",
                   control=Toggle(s.get("show_search", True), lambda on: self._taskbar_set(show_search=on)))
        self._card(v, "Task view", "", control=Toggle(s.get("show_taskview", True),
                                                      lambda on: self._taskbar_set(show_taskview=on)))
        self._card(v, "Widgets", "The weather button at the left corner",
                   control=Toggle(s.get("show_widgets", True), lambda on: self._taskbar_set(show_widgets=on)))
        self._card(v, "Other system tray icons", "Which icons stay on the taskbar", slot=self._notifications)
        self._card(v, "Start", "Which programs are pinned: right-click one in Start to pin or unpin it")
        self._card(v, "Screen saver", "Bubbles, Ribbons, Mystify, Photos...",
                   slot=self._cpl("display_properties", tab="saver"))

    def _taskbar_set(self, **changes):
        save_cpl(**changes)
        self.desktop.taskbar._cpl_cache = (0.0, {})
        self.desktop.taskbar.update()

    def _align_combo(self):
        combo = QComboBox()
        combo.addItem("Center", "center")
        combo.addItem("Left", "left")
        combo.setCurrentIndex(1 if cpl_settings().get("taskbar_align", "center") == "left" else 0)
        combo.currentIndexChanged.connect(lambda i: self._taskbar_set(taskbar_align=combo.itemData(i)))
        return combo

    def _lock_combo(self):
        combo = QComboBox()
        images = lock_images()
        current = str(self.desktop.display.lock_image() or "")
        for i, path in enumerate(images):
            combo.addItem(f"Windows spotlight {i + 1}" if "Screen" in str(path.parent) else path.stem, str(path))
            if str(path) == current:
                combo.setCurrentIndex(i)
        combo.currentIndexChanged.connect(lambda i: self.desktop.display.set_lock_image(combo.itemData(i)))
        return combo

    def _colour_grid(self, v):
        grid = QWidget()
        from PySide6.QtWidgets import QGridLayout
        g = QGridLayout(grid)
        g.setContentsMargins(0, 0, 0, 0)
        g.setSpacing(6)
        d = self.desktop.display
        for i, (name, colour) in enumerate(display.ACCENT_COLORS[:24]):
            b = QPushButton()
            b.setFixedSize(34, 34)
            b.setToolTip(name)
            b.setStyleSheet(f"QPushButton {{ background: {colour}; border: 2px solid "
                            f"{'#1A1A1A' if d.accent().name().lower() == colour.lower() else 'transparent'}; "
                            f"border-radius: 4px; }} QPushButton:hover {{ border: 2px solid #5C5C5C; }}")
            b.clicked.connect(lambda _c=False, col=colour: self._pick_accent(col))
            g.addWidget(b, i // 12, i % 12)
        v.addWidget(grid)

    def _pick_accent(self, colour):
        self.desktop.display.set_accent(colour)
        self.desktop.update()
        self.desktop.taskbar.update()
        for w in self.desktop.windows:
            w.update()
        # redraw the swatch borders
        page = self.pages["personalization"]
        for b in page.findChildren(QPushButton):
            if b.toolTip() in dict(display.ACCENT_COLORS):
                col = dict(display.ACCENT_COLORS)[b.toolTip()]
                b.setStyleSheet(f"QPushButton {{ background: {col}; border: 2px solid "
                                f"{'#1A1A1A' if col.lower() == colour.lower() else 'transparent'}; border-radius: 4px; }}"
                                f" QPushButton:hover {{ border: 2px solid #5C5C5C; }}")

    # ---- Apps ----
    def _page_apps(self, v):
        self._card(v, "Installed apps", "Uninstall and manage apps on your PC", slot=self._launch("arp"))
        self._card(v, "Default apps", "Defaults for file and link types, other defaults",
                   slot=self._cpl("default_programs"))
        self._card(v, "Startup", "Apps that start automatically when you sign in", slot=self._launch("msconfig"))
        self._card(v, "Optional features", "Extra functionality for your device")
        self._card(v, "Apps for websites", "Open links in an app instead of a browser")

    # ---- Accounts ----
    def _page_accounts(self, v):
        self._card(v, "Your info", "Accounts used by email, calendar and contacts; your picture",
                   slot=self._cpl("user_accounts", page=1))
        self._card(v, "Email & accounts", f"{user.email_address()}  ·  Microsoft account")
        self._card(v, "Sign-in options", "PIN, password, Windows Hello", slot=self._cpl("user_accounts", page=0))
        self._card(v, "Windows backup", "Back up your files, apps, preferences to restore them across devices",
                   control=Toggle(False))
        self._card(v, "Family", "Manage your family group", slot=self._launch("furdir"))

    # ---- Time & language ----
    def _page_time(self, v):
        now = clock.now()
        self._card(v, "Date & time", f"{clock.long_date_text(now)}  ·  {clock.time_text(now)}  ·  Set automatically",
                   slot=self._date_time)
        self._card(v, "Language & region", "English (United States)  ·  United States")
        self._card(v, "Typing", "Touch keyboard, text suggestions, preferences")
        self._card(v, "Speech", "Speech language, voices for apps", slot=self._launch("copilotvoice"))

    def _date_time(self):
        try:
            from claudexp.cpl_extra import date_and_time
            date_and_time(self.desktop)
        except Exception:
            pass

    # ---- Gaming ----
    def _page_gaming(self, v):
        self._card(v, "Game Bar", "Controller and PC shortcuts", control=Toggle(False))
        self._card(v, "Captures", "Save location, recording preferences", slot=self._launch("snipping"))
        self._card(v, "Game Mode", "Optimize your PC for play", control=Toggle(True))
        self._card(v, "Your games", "Every game on this PC is in Start > All > Games",
                   slot=lambda: self.desktop.toggle_start_menu())

    # ---- Accessibility ----
    def _page_accessibility(self, v):
        self._card(v, "Text size", "Text size that appears throughout Windows and your apps")
        self._card(v, "Visual effects", "Scroll bars, transparency, animations", control=Toggle(True))
        self._card(v, "Mouse pointer and touch", "Mouse pointer color, size", slot=self._cpl("mouse_properties"))
        self._card(v, "Narrator", "Voice, verbosity, keyboard, braille", control=Toggle(False))
        self._card(v, "Magnifier", "Magnifier reading, zoom increment", control=Toggle(False))
        self._card(v, "Captions", "Caption style", control=Toggle(False))

    # ---- Privacy & security ----
    def _page_privacy(self, v):
        self._card(v, "Windows Security", "Antivirus, browser, firewall, and network protection for your device",
                   slot=self._launch("antivirus"))
        self._card(v, "Find my device", "Track your device if you think you've lost it", control=Toggle(False))
        self._card(v, "For developers", "These settings are intended for development use only",
                   slot=self._launch("pystudio"))
        self._card(v, "Diagnostics & feedback", "Send optional diagnostic data", control=Toggle(False))
        self._card(v, "Activity history", "Clear history, and choose what Windows keeps",
                   slot=self._launch("furlog"))

    # ---- Windows Update ----
    def _page_update(self, v):
        card = QFrame()
        card.setObjectName("card")
        h = QHBoxLayout(card)
        h.setContentsMargins(16, 18, 16, 18)
        ok = QLabel("✔")
        ok.setStyleSheet("font-size: 28px; color: #10893E;")
        h.addWidget(ok)
        text = QVBoxLayout()
        t = QLabel("You're up to date")
        t.setStyleSheet("font-size: 18px; font-weight: 600;")
        text.addWidget(t)
        s = QLabel(f"Last checked: Today, {clock.time_text()}")
        s.setObjectName("cardsub")
        text.addWidget(s)
        h.addLayout(text, 1)
        h.addWidget(self._button("Check for updates", self._launch("winupdate"), accent=True))
        v.addWidget(card)
        self._card(v, "Pause updates", "Pause for 1 week", control=Toggle(False))
        self._card(v, "Update history", "2025-10 Cumulative Update for Windows 11 Version 25H2 (KB5066835)",
                   slot=self._launch("winupdate"))
        self._card(v, "Advanced options", "Delivery optimization, optional updates, active hours")
        self._card(v, "Windows Insider Program", "Get preview builds of Windows")


def settings_icon():
    from .programs import settings_icon as _si
    return _si()


def open_settings(desktop, page=None):
    win = _open.get("win")
    if win is not None and isValid(win) and win in desktop.windows:
        desktop.activate(win)
        if page:
            win.content.show_page(page)
        return win
    body = SettingsBody(desktop)
    win = MicaWindow(desktop, "Settings", body, settings_icon(), (1000, 660))
    body.frame = win
    _open["win"] = win
    desktop.open_window(win)
    if page:
        body.show_page(page)
    sound.play("navigate")
    return win
