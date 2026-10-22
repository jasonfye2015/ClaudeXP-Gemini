"""Control Panel, the classic view Windows 11 still carries: the category view with its green headings and blue tasks, 'View by: Large
icons' for everything at once, Personalization (themes, desktop background, window colour, sounds, screen saver),
User Accounts, Default Programs - and the applets ClaudeXP brought (Date and Time, Folder Options, Fonts, Power
Options, Region, Keyboard, Internet Options, Administrative Tools...). Stands in for claudexp.controlpanel."""
from PySide6.QtCore import QRectF, QSize, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (QCheckBox, QComboBox, QFileDialog, QFrame, QGridLayout, QHBoxLayout, QInputDialog,
                               QLabel, QLineEdit, QListWidget, QListWidgetItem, QPushButton, QScrollArea, QSlider,
                               QSpinBox, QStackedWidget, QStyle, QVBoxLayout, QWidget)
from shiboken6 import isValid

from . import display, sound, user
from .paths import BACKGROUNDS, icon as asset_icon
from .wm import MicaWindow

LINK = ("QPushButton { color: #0066CC; text-align: left; border: none; background: transparent;"
        " font-family: 'Segoe UI'; font-size: 12px; padding: 1px 0; }"
        "QPushButton:hover { color: #3399FF; text-decoration: underline; }")
HEAD = "font-family: 'Segoe UI'; font-size: 19px; color: #003399; font-weight: 300; background: transparent;"
SUB = "font-family: 'Segoe UI'; font-size: 12px; color: #1E1E1E; background: transparent;"
GREY = "font-family: 'Segoe UI'; font-size: 12px; color: #6D6D6D; background: transparent;"
BUTTON = ("QPushButton { font-family: 'Segoe UI'; font-size: 12px; padding: 4px 16px; min-width: 70px;"
          " background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #F6F6F6, stop:1 #DDDDDD);"
          " border: 1px solid #707070; border-radius: 3px; }"
          "QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #EAF6FD, stop:1 #BEE6FD);"
          " border: 1px solid #3C7FB1; }")
def _themes():
    """Windows 11's themes: each wallpaper the real PC ships with, paired with an accent colour."""
    from .display import wallpapers
    colours = ["#0067C0", "#C239B3", "#CA5010", "#107C10", "#2D7D9A", "#744DA9", "#D13438", "#4A5459"]
    out = []
    for i, (label, path) in enumerate(w for w in wallpapers() if w[1] is not None):
        out.append((label, path, colours[i % len(colours)]))
    return out


THEMES = []
SOLIDS = ["#000000", "#1F5FA8", "#3A6EA5", "#008080", "#2E8B57", "#6D4C9F", "#A0522D", "#5A5A5A", "#F0F0F0"]
_open = {}


def std(which):
    from PySide6.QtWidgets import QApplication
    return QApplication.style().standardIcon(which)


def _single(desktop, key, make):
    win = _open.get(key)
    if win is not None and isValid(win) and win in desktop.windows:
        desktop.activate(win)
        return win
    win = make()
    _open[key] = win
    return win


def _link(text, slot):
    b = QPushButton(text)
    b.setStyleSheet(LINK)
    b.setCursor(Qt.PointingHandCursor)
    b.clicked.connect(lambda _c=False: slot())
    return b


def _button(text, slot=None):
    b = QPushButton(text)
    b.setStyleSheet(BUTTON)
    if slot is not None:
        b.clicked.connect(lambda _c=False: slot())
    return b


def _white(widget):
    widget.setAttribute(Qt.WA_StyledBackground, True)
    widget.setStyleSheet("background: white;")
    return widget


def _thumb(path, w=96, h=72):
    from .display import load_image
    pm = load_image(path, max(w, h) * 4) if path is not None else QPixmap()
    if pm.isNull():
        pm = QPixmap(w, h)
        pm.fill(QColor("#6BA4D9"))
    return pm.scaled(w, h, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation).copy(0, 0, w, h)


def _found_pictures():
    """Pictures for the Photos screen saver: everything in your Pictures library."""
    from . import vfs
    try:
        return [p for p in sorted(vfs.my_pictures().rglob("*")) if p.suffix.lower() in display.IMAGE_EXTS][:400]
    except OSError:
        return []


def _ai_models(desktop):
    from claudexp.aimodels_cpl import ai_models_properties
    ai_models_properties(desktop)


def _placeholder(desktop, title, text):
    from .dialogs import msgbox
    msgbox(desktop, title, text, "info")


# ---- the Control Panel window -------------------------------------------------------------------------------------
def _categories(desktop):
    from claudexp import cpl_extra as cx, programs
    from claudexp.printing import printers_and_faxes
    from .dialogs import system_info
    from .tray import customize_notifications

    def launch(key):
        return lambda: programs.launch(desktop, key)

    def gadgets():
        from .programs import widgets as g
        g.open_gallery(desktop)

    def network():
        from . import network as net
        net.get(desktop)._show_status()

    def resolution():
        _placeholder(desktop, "Screen Resolution", f"Resolution: {desktop.width()} x {desktop.height()} "
                     "(recommended)\nOrientation: Landscape\n\nThis is the size of the Claude11 window: press F11 for "
                     "full screen.")

    return [
        ("System and Security", std(QStyle.SP_ComputerIcon), [
            ("Review your computer's status", lambda: desktop.taskbar._action_center()),
            ("Back up your computer", lambda: _placeholder(desktop, "Backup and Restore",
                                                            "Windows Backup has not been set up.")),
            ("Find and fix problems", lambda: _placeholder(desktop, "Troubleshooting",
                                                            "No problems were found on this computer.")),
            ("Windows Update", launch("winupdate")), ("System", lambda: system_info(desktop)),
            ("Windows Defender", launch("antivirus")), ("Power Options", lambda: cx.power_options(desktop)),
            ("Administrative Tools", lambda: cx.admin_tools(desktop))]),
        ("User Accounts and Family Safety", QIcon(accounts_icon(32)), [
            ("Change your account picture", lambda: user_accounts(desktop, page=1)),
            ("Add or remove user accounts", lambda: user_accounts(desktop)),
            ("Set up parental controls for any user", lambda: _placeholder(desktop, "Parental Controls",
                                                                           "There are no other accounts.")),
            ("Credential Manager", lambda: _placeholder(desktop, "Credential Manager",
                                                        "No credentials are stored."))]),
        ("Network and Internet", std(QStyle.SP_DriveNetIcon), [
            ("View network status and tasks", network), ("Internet Options", lambda: cx.internet_options(desktop)),
            ("Choose homegroup and sharing options", lambda: _placeholder(desktop, "HomeGroup",
                                                                          "There is currently no homegroup on the "
                                                                          "network."))]),
        ("Appearance and Personalization", QIcon(monitor_icon(32)), [
            ("Personalization", lambda: display_properties(desktop)),
            ("Change desktop background", lambda: display_properties(desktop, tab="background")),
            ("Adjust screen resolution", resolution), ("Taskbar and Start Menu", lambda: cx.taskbar_start(desktop)),
            ("Notification Area Icons", lambda: customize_notifications(desktop)),
            ("Desktop Gadgets", gadgets), ("Folder Options", lambda: cx.folder_options(desktop)),
            ("Fonts", lambda: cx.fonts(desktop)), ("Ease of Access Center", lambda: cx.accessibility(desktop))]),
        ("Hardware and Sound", QIcon(_printer_icon()), [
            ("View devices and printers", lambda: printers_and_faxes(desktop)),
            ("Sound", lambda: sound_properties(desktop)), ("Mouse", lambda: mouse_properties(desktop)),
            ("Keyboard", lambda: cx.keyboard(desktop)), ("Phone and Modem", lambda: cx.phone_modem(desktop)),
            ("Game Controllers", lambda: cx.game_controllers(desktop)), ("AI Models", lambda: _ai_models(desktop)),
            ("Speech Recognition", lambda: cx.speech(desktop))]),
        ("Clock, Language, and Region", std(QStyle.SP_FileDialogInfoView), [
            ("Date and Time", lambda: cx.date_and_time(desktop)), ("Region and Language", lambda: cx.regional(desktop))]),
        ("Programs", std(QStyle.SP_DirIcon), [
            ("Uninstall a program", launch("arp")), ("Default Programs", lambda: default_programs(desktop)),
            ("Desktop Gadgets", gadgets), ("Turn Windows features on or off",
                                           lambda: _placeholder(desktop, "Windows Features",
                                                                "All Windows features are turned on."))]),
        ("Ease of Access", std(QStyle.SP_MessageBoxInformation), [
            ("Ease of Access Center", lambda: cx.accessibility(desktop)),
            ("Speech Recognition", lambda: cx.speech(desktop))]),
    ]


def control_panel(desktop):
    def make():
        body = _white(QWidget())
        root = QVBoxLayout(body)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        bar = QWidget()
        bar.setStyleSheet("background: #F7F9FC; border-bottom: 1px solid #DDE3EA;")
        bar.setAttribute(Qt.WA_StyledBackground, True)
        bl = QHBoxLayout(bar)
        bl.setContentsMargins(12, 6, 12, 6)
        crumb = QLabel("Control Panel  ▸  All Control Panel Items")
        crumb.setStyleSheet(SUB)
        bl.addWidget(crumb, 1)
        view_label = QLabel("View by:")
        view_label.setStyleSheet(SUB)
        bl.addWidget(view_label)
        view = QComboBox()
        view.addItems(["Category", "Large icons", "Small icons"])
        bl.addWidget(view)
        root.addWidget(bar)
        split = QHBoxLayout()
        split.setContentsMargins(0, 0, 0, 0)
        split.setSpacing(0)
        nav = QWidget()
        nav.setFixedWidth(190)
        nav.setStyleSheet("background: #FFFFFF; border-right: 1px solid #E5E5E5;")
        nav.setAttribute(Qt.WA_StyledBackground, True)
        nl = QVBoxLayout(nav)
        nl.setContentsMargins(12, 14, 8, 8)
        nl.setSpacing(4)
        home = QLabel("Control Panel Home")
        home.setStyleSheet("font-family: 'Segoe UI'; font-size: 12px; color: #1E1E1E; font-weight: bold;")
        nl.addWidget(home)
        stack = QStackedWidget()
        cats = _categories(desktop)
        for name, _icon, _links in cats:
            nl.addWidget(_link(name, lambda n=name: _show_category(stack, cats, n)))
        nl.addStretch()
        split.addWidget(nav)
        # category view
        catview = QScrollArea()
        catview.setWidgetResizable(True)
        catview.setFrameShape(QFrame.NoFrame)
        inner = _white(QWidget())
        grid = QGridLayout(inner)
        grid.setContentsMargins(20, 16, 20, 16)
        grid.setHorizontalSpacing(30)
        grid.setVerticalSpacing(18)
        head = QLabel("Adjust your computer's settings")
        head.setStyleSheet(HEAD)
        grid.addWidget(head, 0, 0, 1, 2)
        for i, (name, icon, links) in enumerate(cats):
            card = QWidget()
            cl = QHBoxLayout(card)
            cl.setContentsMargins(0, 0, 0, 0)
            pic = QLabel()
            pic.setPixmap(icon.pixmap(48, 48))
            pic.setAlignment(Qt.AlignTop)
            cl.addWidget(pic)
            col = QVBoxLayout()
            col.setSpacing(2)
            title = _link(name, lambda n=name: _show_category(stack, cats, n))
            title.setStyleSheet(LINK.replace("font-size: 12px", "font-size: 14px"))
            col.addWidget(title)
            for text, slot in links[:4]:
                col.addWidget(_link(text, slot))
            cl.addLayout(col, 1)
            grid.addWidget(card, 1 + i // 2, i % 2)
        grid.setRowStretch(1 + len(cats) // 2 + 1, 1)
        catview.setWidget(inner)
        stack.addWidget(catview)
        # icon view
        icons = QListWidget()
        icons.setViewMode(QListWidget.IconMode)
        icons.setIconSize(QSize(48, 48))
        icons.setGridSize(QSize(150, 92))
        icons.setWordWrap(True)
        icons.setMovement(QListWidget.Static)
        icons.setResizeMode(QListWidget.Adjust)
        icons.setStyleSheet("QListWidget { border: none; font-family: 'Segoe UI'; font-size: 12px; }")
        actions = {}
        seen = set()
        for name, icon, links in cats:
            for text, slot in links:
                label = text
                if label in seen:
                    continue
                seen.add(label)
                it = QListWidgetItem(icon, label)
                icons.addItem(it)
                actions[label] = slot
        icons.sortItems()
        icons.itemActivated.connect(lambda it: actions[it.text()]())
        stack.addWidget(icons)
        # one category's page
        page = QScrollArea()
        page.setWidgetResizable(True)
        page.setFrameShape(QFrame.NoFrame)
        stack.addWidget(page)
        stack.page = page
        split.addWidget(stack, 1)
        root.addLayout(split, 1)
        view.currentIndexChanged.connect(lambda i: stack.setCurrentIndex(0 if i == 0 else 1))
        win = MicaWindow(desktop, "Control Panel", body, std(QStyle.SP_DesktopIcon), size=(860, 580))
        desktop.open_window(win)
        sound.play("navigate")
        return win
    return _single(desktop, "controlpanel", make)


def _show_category(stack, cats, name):
    for cname, icon, links in cats:
        if cname != name:
            continue
        inner = _white(QWidget())
        v = QVBoxLayout(inner)
        v.setContentsMargins(24, 16, 24, 16)
        v.setSpacing(6)
        head = QLabel(cname)
        head.setStyleSheet(HEAD)
        v.addWidget(head)
        for text, slot in links:
            v.addWidget(_link(text, slot))
        v.addStretch()
        stack.page.setWidget(inner)
        stack.setCurrentWidget(stack.page)
        return


# ---- icons ------------------------------------------------------------------------------------------------------------
def monitor_icon(size=32):
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    s = size / 32
    p.setPen(QPen(QColor("#3A4A5A"), 1.5 * s))
    p.setBrush(QColor("#1F5FA8"))
    p.drawRoundedRect(QRectF(3 * s, 4 * s, 26 * s, 18 * s), 2 * s, 2 * s)
    p.setBrush(QColor("#6D7B88"))
    p.drawRect(QRectF(13 * s, 22 * s, 6 * s, 4 * s))
    p.drawRect(QRectF(9 * s, 26 * s, 14 * s, 2 * s))
    p.end()
    return pm


def accounts_icon(size=32):
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    s = size / 32
    p.setPen(QPen(QColor("#2F5F8F"), 1.2 * s))
    p.setBrush(QColor("#6FAEE8"))
    p.drawEllipse(QRectF(11 * s, 4 * s, 10 * s, 10 * s))
    p.drawRoundedRect(QRectF(6 * s, 16 * s, 20 * s, 13 * s), 5 * s, 5 * s)
    p.end()
    return pm


def _printer_icon():
    from claudexp.printing import printer_icon
    return printer_icon(32)


# ---- Personalization ---------------------------------------------------------------------------------------------------
def display_properties(desktop, theme_file=None, tab=None):
    def make():
        body = _white(QWidget())
        root = QHBoxLayout(body)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        nav = QWidget()
        nav.setFixedWidth(200)
        nav.setStyleSheet("background: #FFFFFF; border-right: 1px solid #E5E5E5;")
        nav.setAttribute(Qt.WA_StyledBackground, True)
        nl = QVBoxLayout(nav)
        nl.setContentsMargins(12, 14, 8, 8)
        nl.setSpacing(6)
        stack = QStackedWidget()
        nl.addWidget(_link("Control Panel Home", lambda: control_panel(desktop)))
        nl.addSpacing(10)
        nl.addWidget(_link("Change desktop icons", lambda: _desktop_icons_dialog(desktop)))
        nl.addWidget(_link("Change mouse pointers", lambda: mouse_properties(desktop)))
        nl.addWidget(_link("Change your account picture", lambda: user_accounts(desktop, page=1)))
        nl.addStretch()
        root.addWidget(nav)
        root.addWidget(stack, 1)
        d = display.get()
        # the main page: themes and the four buttons
        main = QScrollArea()
        main.setWidgetResizable(True)
        main.setFrameShape(QFrame.NoFrame)
        inner = _white(QWidget())
        v = QVBoxLayout(inner)
        v.setContentsMargins(20, 14, 20, 14)
        head = QLabel("Change the visuals and sounds on your computer")
        head.setStyleSheet(HEAD)
        v.addWidget(head)
        sub = QLabel("Click a theme to change the desktop background, window color, sounds, and screen saver all at "
                     "once.")
        sub.setStyleSheet(SUB)
        sub.setWordWrap(True)
        v.addWidget(sub)
        aero = QLabel("Windows 11 themes")
        aero.setStyleSheet("font-family: 'Segoe UI'; font-size: 13px; color: #1E1E1E; font-weight: bold;")
        v.addWidget(aero)
        themes = QListWidget()
        themes.setViewMode(QListWidget.IconMode)
        themes.setIconSize(QSize(120, 90))
        themes.setGridSize(QSize(140, 122))
        themes.setFixedHeight(260)
        themes.setMovement(QListWidget.Static)
        themes.setStyleSheet("QListWidget { border: 1px solid #DDE3EA; font-family: 'Segoe UI'; font-size: 11px; }")
        for name, wall, colour in _themes():
            it = QListWidgetItem(QIcon(_thumb(wall, 120, 90)), name)
            it.setData(Qt.UserRole, (str(wall), colour))
            themes.addItem(it)

        def pick_theme(it):
            wall, colour = it.data(Qt.UserRole)
            d.apply(wall, "Fill", d.data.get("color", "#000000"))
            d.set_aero(colour)
            _repaint(desktop)
            sound.play("navigate")
        themes.itemClicked.connect(pick_theme)
        v.addWidget(themes)
        row = QHBoxLayout()
        for text, key in (("Desktop Background", "background"), ("Window Color", "color"), ("Sounds", "sounds"),
                          ("Screen Saver", "saver")):
            b = QPushButton(text)
            b.setStyleSheet(LINK + "QPushButton { font-size: 12px; }")
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(lambda _c=False, k=key: stack.setCurrentIndex(PAGES[k]))
            row.addWidget(b)
        row.addStretch()
        v.addLayout(row)
        v.addStretch()
        main.setWidget(inner)
        stack.addWidget(main)
        PAGES = {"main": 0}

        def page(title):
            w = _white(QWidget())
            pv = QVBoxLayout(w)
            pv.setContentsMargins(20, 14, 20, 14)
            pv.setSpacing(8)
            back = _link("◄ Personalization", lambda: stack.setCurrentIndex(0))
            pv.addWidget(back)
            h = QLabel(title)
            h.setStyleSheet(HEAD)
            pv.addWidget(h)
            return w, pv

        # desktop background
        w, pv = page("Choose your desktop background")
        PAGES["background"] = stack.count()
        walls = QListWidget()
        walls.setViewMode(QListWidget.IconMode)
        walls.setIconSize(QSize(120, 90))
        walls.setGridSize(QSize(134, 104))
        walls.setMovement(QListWidget.Static)
        walls.setStyleSheet("QListWidget { border: 1px solid #DDE3EA; }")
        for label, path in display.wallpapers():
            if path is None:
                continue
            it = QListWidgetItem(QIcon(_thumb(path, 120, 90)), "")
            it.setToolTip(label)
            it.setData(Qt.UserRole, str(path))
            walls.addItem(it)
        pv.addWidget(walls, 1)
        opts = QHBoxLayout()
        opts.addWidget(QLabel("Position:"))
        pos = QComboBox()
        pos.addItems(list(display.POSITIONS))
        pos.setCurrentText(d.data.get("position", "Fill"))
        opts.addWidget(pos)
        opts.addSpacing(20)
        opts.addWidget(QLabel("Solid colors:"))
        chosen = {"color": d.data.get("color", "#000000"), "wall": d.data.get("wallpaper", "")}
        for c in SOLIDS:
            sw = QPushButton()
            sw.setFixedSize(22, 22)
            sw.setStyleSheet(f"background: {c}; border: 1px solid #707070;")
            sw.clicked.connect(lambda _c=False, col=c: (chosen.update(color=col, wall=""), walls.clearSelection()))
            opts.addWidget(sw)
        browse = _button("Browse...")

        def browse_pic():
            path, _f = QFileDialog.getOpenFileName(body, "Browse", "", "Pictures (*.jpg *.jpeg *.png *.bmp *.gif)")
            if path:
                chosen["wall"] = path
                walls.clearSelection()
        browse.clicked.connect(lambda _c=False: browse_pic())
        opts.addWidget(browse)
        opts.addStretch()
        pv.addLayout(opts)
        walls.itemClicked.connect(lambda it: chosen.update(wall=it.data(Qt.UserRole)))
        btns = QHBoxLayout()
        btns.addStretch()

        def save_bg():
            d.apply(chosen["wall"], pos.currentText(), chosen["color"])
            _repaint(desktop)
            stack.setCurrentIndex(0)
        btns.addWidget(_button("Save changes", save_bg))
        btns.addWidget(_button("Cancel", lambda: stack.setCurrentIndex(0)))
        pv.addLayout(btns)
        stack.addWidget(w)
        # window colour
        w, pv = page("Change the color of your window borders, Start menu, and taskbar")
        PAGES["color"] = stack.count()
        grid = QGridLayout()
        picked = {"aero": d.aero_color()}
        for i, (name, colour) in enumerate(display.AERO_COLORS):
            b = QPushButton()
            b.setFixedSize(40, 40)
            b.setToolTip(name)
            b.setStyleSheet(f"background: {colour}; border: 1px solid #707070;")

            def choose(_c=False, col=colour):
                picked["aero"] = col
                d.set_aero(col)
                _repaint(desktop)
            b.clicked.connect(choose)
            grid.addWidget(b, i // 8, i % 8)
        pv.addLayout(grid)
        trans = QCheckBox("Enable transparency")
        trans.setChecked(d.aero_intensity() < 0.99)
        pv.addWidget(trans)
        pv.addWidget(QLabel("Color intensity:"))
        intensity = QSlider(Qt.Horizontal)
        intensity.setRange(20, 100)
        intensity.setValue(int(d.aero_intensity() * 100))
        intensity.setFixedWidth(260)
        pv.addWidget(intensity)

        def live(_v=None):
            d.set_aero(picked["aero"], 1.0 if not trans.isChecked() else intensity.value() / 100)
            _repaint(desktop)
        intensity.valueChanged.connect(live)
        trans.toggled.connect(live)
        pv.addStretch()
        btns = QHBoxLayout()
        btns.addStretch()
        btns.addWidget(_button("Save changes", lambda: stack.setCurrentIndex(0)))
        btns.addWidget(_button("Cancel", lambda: stack.setCurrentIndex(0)))
        pv.addLayout(btns)
        stack.addWidget(w)
        # sounds
        w, pv = page("Sounds")
        PAGES["sounds"] = stack.count()
        pv.addWidget(QLabel("A sound theme is a set of sounds applied to events in Windows and programs."))
        scheme = QComboBox()
        scheme.addItems(["Windows Default", "No Sounds"])
        scheme.setCurrentIndex(1 if sound.is_muted() else 0)
        scheme.currentIndexChanged.connect(lambda i: (sound.set_muted(i == 1), desktop.taskbar.update()))
        pv.addWidget(scheme)
        events = QListWidget()
        events.setStyleSheet("QListWidget { border: 1px solid #ABADB3; font-family: 'Segoe UI'; font-size: 12px; }")
        for key, name in sorted(sound.EVENTS.items()):
            it = QListWidgetItem(name.replace(".wav", ""))
            it.setData(Qt.UserRole, key)
            events.addItem(it)
        pv.addWidget(events, 1)
        test = _button("Test", lambda: sound.play(events.currentItem().data(Qt.UserRole)) if events.currentItem() else None)
        startup = QCheckBox("Play Windows Startup sound")
        startup.setChecked(True)
        rowx = QHBoxLayout()
        rowx.addWidget(startup)
        rowx.addStretch()
        rowx.addWidget(test)
        pv.addLayout(rowx)
        stack.addWidget(w)
        # screen saver
        w, pv = page("Screen Saver")
        PAGES["saver"] = stack.count()
        from . import screensaver
        saver = QComboBox()
        saver.addItems(list(screensaver.SAVERS))
        saver.setCurrentText(d.data.get("saver", "Bubbles"))
        pv.addWidget(saver)
        rowy = QHBoxLayout()
        rowy.addWidget(QLabel("Wait:"))
        wait = QSpinBox()
        wait.setRange(1, 120)
        wait.setValue(int(d.data.get("wait", 10)))
        wait.setSuffix(" minutes")
        rowy.addWidget(wait)
        resume = QCheckBox("On resume, display logon screen")
        resume.setChecked(bool(d.data.get("resume_welcome")))
        rowy.addWidget(resume)
        rowy.addStretch()
        pv.addLayout(rowy)
        rowz = QHBoxLayout()
        rowz.addWidget(_button("Preview", lambda: desktop.window().screensaver.start(saver.currentText())))
        rowz.addStretch()
        pv.addLayout(rowz)
        pv.addStretch()
        btns = QHBoxLayout()
        btns.addStretch()

        def save_saver():
            d.set_screensaver(saver=saver.currentText(), wait=wait.value(), resume_welcome=resume.isChecked())
            stack.setCurrentIndex(0)
        btns.addWidget(_button("Save changes", save_saver))
        btns.addWidget(_button("Cancel", lambda: stack.setCurrentIndex(0)))
        pv.addLayout(btns)
        stack.addWidget(w)
        if tab in PAGES:
            stack.setCurrentIndex(PAGES[tab])
        win = MicaWindow(desktop, "Personalization", body, QIcon(monitor_icon(32)), size=(820, 580))
        desktop.open_window(win)
        sound.play("navigate")
        return win
    return _single(desktop, "personalization", make)


def _repaint(desktop):
    desktop.update()
    desktop.taskbar.update()
    desktop.start_menu.update()
    for win in desktop.windows:
        win.update()


def _desktop_icons_dialog(desktop):
    from .network import DialogBody, _fixed_window
    body = DialogBody()
    v = QVBoxLayout(body)
    v.addWidget(QLabel("Desktop icons"))
    boxes = {}
    hidden = set(desktop.icons.state.get("hidden", []))
    for key, label in desktop.icons.builtins():
        cb = QCheckBox(label)
        cb.setChecked(key not in hidden)
        boxes[key] = cb
        v.addWidget(cb)
    row = QHBoxLayout()
    row.addStretch()
    win = {}

    def ok():
        desktop.icons.set_hidden([k for k, cb in boxes.items() if not cb.isChecked()])
        win["w"].request_close()
    row.addWidget(_button("OK", ok))
    row.addWidget(_button("Cancel", lambda: win["w"].request_close()))
    v.addLayout(row)
    win["w"] = _fixed_window(desktop, "Desktop Icon Settings", body, lambda: None)
    desktop.open_window(win["w"])


# ---- User Accounts -----------------------------------------------------------------------------------------------------
def user_accounts(desktop, page=0):
    def make():
        body = _white(QWidget())
        root = QHBoxLayout(body)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        stack = QStackedWidget()
        nav = QWidget()
        nav.setFixedWidth(190)
        nav.setStyleSheet("background: #FFFFFF; border-right: 1px solid #E5E5E5;")
        nav.setAttribute(Qt.WA_StyledBackground, True)
        nl = QVBoxLayout(nav)
        nl.setContentsMargins(12, 14, 8, 8)
        nl.addWidget(_link("Control Panel Home", lambda: control_panel(desktop)))
        nl.addStretch()
        root.addWidget(nav)
        root.addWidget(stack, 1)
        card = QLabel()
        card.setFixedSize(220, 110)

        def paint_card(_e):
            p = QPainter(card)
            p.setRenderHint(QPainter.Antialiasing)
            user.draw_user_picture(p, card.rect().adjusted(8, 8, -132, -8))
            from PySide6.QtGui import QFont
            f = QFont("Segoe UI")
            f.setPixelSize(14)
            p.setFont(f)
            p.setPen(QColor("#1E1E1E"))
            p.drawText(110, 40, user.user_name())
            f.setPixelSize(12)
            p.setFont(f)
            p.setPen(QColor("#6D6D6D"))
            p.drawText(110, 60, "Administrator")
            p.drawText(110, 78, "Password protected" if user.has_windows_password() else "")
            p.end()
        card.paintEvent = paint_card
        # home
        home = _white(QWidget())
        hv = QVBoxLayout(home)
        hv.setContentsMargins(20, 14, 20, 14)
        hv.setSpacing(6)
        h = QLabel("Make changes to your user account")
        h.setStyleSheet(HEAD)
        hv.addWidget(h)
        row = QHBoxLayout()
        col = QVBoxLayout()
        col.setSpacing(4)
        col.addWidget(_link("Create a password for your account" if not user.has_windows_password()
                            else "Change your password", lambda: stack.setCurrentIndex(1)))
        col.addWidget(_link("Remove your password", lambda: (user.set_windows_password(""), card.update())))
        col.addWidget(_link("Change your picture", lambda: stack.setCurrentIndex(2)))
        col.addWidget(_link("Change your account name", lambda: stack.setCurrentIndex(3)))
        col.addWidget(_link("Change your account type", lambda: _placeholder(desktop, "User Accounts",
                                                                             "This is the computer's administrator "
                                                                             "account.")))
        col.addWidget(_link("Manage another account", lambda: _placeholder(desktop, "User Accounts",
                                                                           "There are no other accounts on this "
                                                                           "computer.")))
        col.addWidget(_link("Change User Account Control settings",
                            lambda: _placeholder(desktop, "User Account Control",
                                                 "Notify me only when programs try to make changes to my computer "
                                                 "(default).")))
        col.addStretch()
        row.addLayout(col, 1)
        row.addWidget(card, 0, Qt.AlignTop)
        hv.addLayout(row, 1)
        stack.addWidget(home)

        def page(title):
            w = _white(QWidget())
            pv = QVBoxLayout(w)
            pv.setContentsMargins(20, 14, 20, 14)
            pv.setSpacing(8)
            pv.addWidget(_link("◄ User Accounts", lambda: stack.setCurrentIndex(0)))
            hh = QLabel(title)
            hh.setStyleSheet(HEAD)
            pv.addWidget(hh)
            return w, pv
        # password
        w, pv = page("Create a password for your account")
        pw, pw2, hint = QLineEdit(), QLineEdit(), QLineEdit()
        pw.setEchoMode(QLineEdit.Password)
        pw2.setEchoMode(QLineEdit.Password)
        for label, edit in (("New password", pw), ("Confirm new password", pw2), ("Type a password hint", hint)):
            pv.addWidget(QLabel(label))
            edit.setFixedWidth(260)
            pv.addWidget(edit)
        note = QLabel("")
        note.setStyleSheet(GREY)
        pv.addWidget(note)

        def set_pw():
            if pw.text() != pw2.text():
                note.setText("The passwords you typed do not match.")
                return
            user.set_windows_password(pw.text())
            user.set_password_hint(hint.text())
            pw.clear()
            pw2.clear()
            card.update()
            stack.setCurrentIndex(0)
        rowp = QHBoxLayout()
        rowp.addStretch()
        rowp.addWidget(_button("Create password", set_pw))
        rowp.addWidget(_button("Cancel", lambda: stack.setCurrentIndex(0)))
        pv.addStretch()
        pv.addLayout(rowp)
        stack.addWidget(w)
        # picture
        w, pv = page("Choose a new picture for your account")
        pics = QListWidget()
        pics.setViewMode(QListWidget.IconMode)
        pics.setIconSize(QSize(48, 48))
        pics.setGridSize(QSize(60, 60))
        pics.setMovement(QListWidget.Static)
        pics.setStyleSheet("QListWidget { border: 1px solid #DDE3EA; }")
        for pic_id, _label, pm in user.pictures():
            it = QListWidgetItem(QIcon(pm), "")
            it.setData(Qt.UserRole, pic_id)
            pics.addItem(it)
        pv.addWidget(pics, 1)

        def browse():
            path, _f = QFileDialog.getOpenFileName(body, "Open", "", "Pictures (*.jpg *.jpeg *.png *.bmp *.gif)")
            if path:
                user.set_picture(path)
                card.update()
                desktop.start_menu.update()
                stack.setCurrentIndex(0)
        pv.addWidget(_link("Browse for more pictures...", browse))

        def change_pic():
            it = pics.currentItem()
            if it is not None:
                user.set_picture(it.data(Qt.UserRole))
                card.update()
                desktop.start_menu.update()
                stack.setCurrentIndex(0)
        rowq = QHBoxLayout()
        rowq.addStretch()
        rowq.addWidget(_button("Change Picture", change_pic))
        rowq.addWidget(_button("Cancel", lambda: stack.setCurrentIndex(0)))
        pv.addLayout(rowq)
        stack.addWidget(w)
        # name
        w, pv = page("Type a new account name")
        name = QLineEdit(user.user_name())
        name.setFixedWidth(260)
        pv.addWidget(name)

        def change_name():
            user.set_user_name(name.text())
            card.update()
            desktop.start_menu.update()
            desktop.icons.rescan()
            stack.setCurrentIndex(0)
        rowr = QHBoxLayout()
        rowr.addStretch()
        rowr.addWidget(_button("Change Name", change_name))
        rowr.addWidget(_button("Cancel", lambda: stack.setCurrentIndex(0)))
        pv.addStretch()
        pv.addLayout(rowr)
        stack.addWidget(w)
        stack.setCurrentIndex(2 if page == 1 else 0)
        win = MicaWindow(desktop, "User Accounts", body, QIcon(accounts_icon(32)), size=(720, 480))
        desktop.open_window(win)
        sound.play("navigate")
        return win
    win = _single(desktop, "accounts", make)
    return win


# ---- the small ones --------------------------------------------------------------------------------------------------
def default_programs(desktop):
    from .network import DialogBody, _fixed_window
    from claudexp.programs.people import load_json, save_json
    from .paths import DATA
    body = DialogBody()
    v = QVBoxLayout(body)
    v.addWidget(QLabel("Choose the programs that Windows uses by default"))
    file = DATA / "cpl.json"
    data = load_json(file, {})
    combos = {}
    for label, key, options in (("Web browser:", "default_browser", ["Internet Explorer"]),
                                ("E-mail:", "default_mail", ["Windows Live Mail", "Windows Live Hotmail"]),
                                ("Media player:", "default_media", ["Windows Media Player", "ClaudeAmp", "RealPlayer",
                                                                    "QuickTime Player"]),
                                ("Instant messaging:", "default_im", ["Windows Live Messenger", "AIM", "Skype",
                                                                      "Yahoo! Messenger", "Trillian"])):
        row = QHBoxLayout()
        lab = QLabel(label)
        lab.setFixedWidth(120)
        row.addWidget(lab)
        c = QComboBox()
        c.addItems(options)
        c.setCurrentText(data.get(key, options[0]))
        combos[key] = c
        row.addWidget(c, 1)
        v.addLayout(row)
    win = {}

    def ok():
        for key, c in combos.items():
            data[key] = c.currentText()
        save_json(file, data)
        win["w"].request_close()
    row = QHBoxLayout()
    row.addStretch()
    row.addWidget(_button("OK", ok))
    row.addWidget(_button("Cancel", lambda: win["w"].request_close()))
    v.addLayout(row)
    win["w"] = _fixed_window(desktop, "Default Programs", body, lambda: None)
    desktop.open_window(win["w"])


def sound_properties(desktop):
    display_properties(desktop, tab="sounds")


def mouse_properties(desktop):
    from claudexp import cpl_extra as cx
    try:
        tabs = [("Buttons", cx.page(cx.check("Switch primary and secondary buttons", "mouse_swap"),
                                    cx.group("Double-click speed", cx.slider("mouse_dclick", 5)),
                                    cx.check("Turn on ClickLock", "mouse_clicklock"))),
                ("Pointers", cx.page(cx.combo(["Windows Aero (system scheme)", "Windows Standard (large)",
                                               "Magnified", "(None)"], "mouse_scheme", "Windows Aero (system scheme)"))),
                ("Pointer Options", cx.page(cx.group("Motion", cx.slider("mouse_speed", 6),
                                                     cx.check("Enhance pointer precision", "mouse_precision", True)),
                                            cx.check("Display pointer trails", "mouse_trails"),
                                            cx.check("Show location of pointer when I press the CTRL key",
                                                     "mouse_locate"))),
                ("Wheel", cx.page(cx.group("Vertical Scrolling", cx.slider("mouse_wheel", 3, 1, 10))))]
        cx.sheet(desktop, "Mouse Properties", std(QStyle.SP_ArrowUp), tabs)
    except Exception as exc:
        _placeholder(desktop, "Mouse Properties", f"Mouse Properties couldn't open: {exc}")
