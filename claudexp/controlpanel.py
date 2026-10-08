"""Control Panel, Display Properties (desktop background) and User Accounts (name and picture)."""
from pathlib import Path

from PySide6.QtCore import QRectF, QSize, Qt
from PySide6.QtGui import QColor, QFont, QIcon, QLinearGradient, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QGridLayout, QGroupBox, QHBoxLayout, QLabel,
                               QLineEdit, QListWidget, QListWidgetItem, QPushButton, QSpinBox, QStackedWidget, QStyle,
                               QTabWidget, QVBoxLayout, QWidget)
from shiboken6 import isValid

from . import display, sound, user
from .wm import XPWindow


def std(which):
    return QApplication.style().standardIcon(which)


def _single(desktop, attr, make):
    """One window of each kind: reuse it if it's still open."""
    win = _open.get(attr)
    if win is not None and isValid(win):
        desktop.open_window(win)
        return win
    win = make()
    _open[attr] = win
    return win


_open = {}


# ---- Display Properties ------------------------------------------------------------------------

def monitor_icon(size=32):
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    s = size / 32
    p.setPen(QPen(QColor("#505050"), max(1.0, s)))
    p.setBrush(QColor("#D8D8D8"))
    p.drawRoundedRect(QRectF(3 * s, 4 * s, 26 * s, 19 * s), 2 * s, 2 * s)
    g = QLinearGradient(0, 6 * s, 0, 21 * s)
    g.setColorAt(0, QColor("#5DA2F5"))
    g.setColorAt(1, QColor("#3E9B32"))
    p.setBrush(g)
    p.setPen(Qt.NoPen)
    p.drawRect(QRectF(5.5 * s, 6.5 * s, 21 * s, 14 * s))
    p.setBrush(QColor("#9A9A9A"))
    p.drawRect(QRectF(13 * s, 23 * s, 6 * s, 3 * s))
    p.drawRoundedRect(QRectF(9 * s, 26 * s, 14 * s, 3 * s), 1, 1)
    p.end()
    return pm


class MonitorPreview(QWidget):
    """The little monitor in Display Properties showing the chosen background (or a live screen saver)."""
    SCREEN = QRectF(22, 15, 156, 112)

    def __init__(self, saver=None):
        super().__init__()
        self.settings = dict(display.get().data)
        self.setFixedSize(200, 165)
        self.saver_widget = None
        if saver is not None:
            self.show_saver(saver)

    def show_saver(self, name):
        from . import screensaver
        if self.saver_widget is not None:
            self.saver_widget.deleteLater()
        self.saver_widget = screensaver.make(name, self)
        if self.saver_widget is not None:
            self.saver_widget.setGeometry(self.SCREEN.toRect())
            self.saver_widget.show()
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        bezel = QRectF(10, 4, 180, 132)
        g = QLinearGradient(0, bezel.top(), 0, bezel.bottom())
        g.setColorAt(0, QColor("#F2F1EC"))
        g.setColorAt(1, QColor("#C9C6BA"))
        p.setPen(QPen(QColor("#8A877C"), 1))
        p.setBrush(g)
        p.drawRoundedRect(bezel, 8, 8)
        screen = self.SCREEN
        if self.saver_widget is None:
            p.drawPixmap(screen, display.get().render(1024, 738, self.settings), QRectF(0, 0, 1024, 738))
        p.setPen(QPen(QColor("#5A5850"), 1))
        p.setBrush(Qt.NoBrush)
        p.drawRect(screen)
        p.setBrush(QColor("#B8B5A8"))
        p.drawRect(QRectF(85, 136, 30, 12))
        p.drawRoundedRect(QRectF(60, 147, 80, 9), 3, 3)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#3BB54A"))
        p.drawEllipse(QRectF(168, 129, 5, 4))


def _thumb(path):
    pm = QPixmap(str(path)) if path else QPixmap()
    out = QPixmap(32, 24)
    out.fill(QColor("white"))
    if not pm.isNull():
        p = QPainter(out)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        p.drawPixmap(QRectF(0, 0, 32, 24), pm, QRectF(pm.rect()))
        p.end()
    return QIcon(out)


def _found_pictures():
    """Pictures in My Pictures, Shared Pictures and on the E: drive, for 'Browse...'."""
    from .explorer import vfs
    found = []
    for folder in (vfs.my_pictures(), vfs.shared_documents() / "Shared Pictures", vfs.local_storage()):
        if folder.exists():
            for f in sorted(folder.rglob("*"))[:300]:
                if f.suffix.lower() in display.IMAGE_EXTS and f.is_file():
                    found.append(f)
    return found


def display_properties(desktop):
    return _single(desktop, "display", lambda: _make_display(desktop))


def _make_display(desktop):
    from .network import DialogBody, _fixed_window
    disp = display.get()
    body = DialogBody()
    root = QVBoxLayout(body)
    root.setContentsMargins(8, 8, 8, 8)
    tabs = QTabWidget()
    tabs.setStyleSheet("QTabWidget::pane { background: #FCFCFE; border: 1px solid #919B9C; }"
                       "QTabBar::tab { background: #F0EFE6; border: 1px solid #919B9C; padding: 3px 8px;"
                       " font-family: Tahoma; font-size: 11px; }"
                       "QTabBar::tab:selected { background: #FCFCFE; border-bottom-color: #FCFCFE; }")
    for name, text in (("Themes", "A theme is a background plus a set of sounds, icons, and other elements to "
                                  "help you personalize your computer with one click.\n\nTheme:  Windows XP"),):
        tabs.addTab(_info_page(text), name)

    page = QWidget()
    v = QVBoxLayout(page)
    preview = MonitorPreview()
    v.addWidget(preview, 0, Qt.AlignHCenter)
    bg_label = QLabel("&Background:")
    v.addWidget(bg_label)
    row = QHBoxLayout()
    lst = QListWidget()
    lst.setIconSize(QSize(32, 24))
    lst.setFixedHeight(130)
    lst.setStyleSheet("QListWidget { background: white; }")
    entries = display.wallpapers()
    current = disp.data["wallpaper"]
    if current and all(str(p) != current for _l, p in entries if p):
        entries.append((Path(current).stem.replace("_", " "), Path(current)))
    for label, path in entries:
        item = QListWidgetItem(_thumb(path) if path else std(QStyle.SP_DialogCancelButton), label)
        item.setData(Qt.UserRole, str(path) if path else "")
        lst.addItem(item)
        if (str(path) if path else "") == current:
            lst.setCurrentItem(item)
    bg_label.setBuddy(lst)   # the & becomes an Alt+B shortcut, like XP
    row.addWidget(lst, 1)
    side = QVBoxLayout()
    browse = QPushButton("B&rowse...")
    side.addWidget(browse)
    pos_label = QLabel("P&osition:")
    side.addWidget(pos_label)
    position = QComboBox()
    pos_label.setBuddy(position)
    position.addItems(display.POSITIONS)
    position.setCurrentText(disp.data["position"])
    side.addWidget(position)
    color_label = QLabel("&Color:")
    side.addWidget(color_label)
    color = QComboBox()
    color_label.setBuddy(color)
    for name, hexcode in display.COLORS:
        sw = QPixmap(14, 14)
        sw.fill(QColor(hexcode))
        color.addItem(QIcon(sw), name, hexcode)
    idx = next((i for i, (_n, h) in enumerate(display.COLORS) if h.lower() == disp.data["color"].lower()), 0)
    color.setCurrentIndex(idx)
    side.addWidget(color)
    side.addStretch()
    row.addLayout(side)
    v.addLayout(row)
    custom = QPushButton("Customize &Desktop...")
    custom.clicked.connect(lambda: customize_desktop(desktop))
    v.addWidget(custom, 0, Qt.AlignLeft)
    tabs.addTab(page, "Desktop")
    saver_tab, saver_values = _saver_tab(desktop, lambda: apply_btn.setEnabled(True))
    tabs.addTab(saver_tab, "Screen Saver")
    tabs.addTab(_info_page("Windows and buttons:  Windows XP style\nColor scheme:  Default (blue)\n"
                           "Font size:  Normal"), "Appearance")
    tabs.addTab(_info_page("Display:  Plug and Play Monitor on NVIDIA GeForce2 MX\n\nScreen resolution:  "
                           "1024 by 768 pixels\nColor quality:  Highest (32 bit)"), "Settings")
    tabs.setCurrentIndex(1)
    root.addWidget(tabs)
    buttons = QHBoxLayout()
    buttons.addStretch()
    ok, cancel, apply_btn = QPushButton("OK"), QPushButton("Cancel"), QPushButton("&Apply")
    for b in (ok, cancel, apply_btn):
        b.setFixedSize(75, 23)
        buttons.addWidget(b)
    root.addLayout(buttons)
    body.setFixedWidth(410)
    apply_btn.setEnabled(False)
    holder = {}

    def chosen():
        item = lst.currentItem()
        return {"wallpaper": item.data(Qt.UserRole) if item else "", "position": position.currentText(),
                "color": color.currentData()}

    def changed(*_):
        preview.settings = chosen()
        preview.update()
        apply_btn.setEnabled(True)

    def apply():
        s = chosen()
        disp.apply(s["wallpaper"], s["position"], s["color"])
        disp.set_screensaver(**saver_values())
        apply_btn.setEnabled(False)

    def close():
        win = holder.pop("win", None)
        if win is not None and isValid(win):
            desktop.close_window(win)

    def pick_browsed():
        files = _found_pictures()
        if not files:
            from .explorer.dialogs import msgbox
            msgbox(desktop, "Browse", "No pictures were found in My Pictures, Shared Pictures or on the "
                                      "External Drive (E:).", "info")
            return
        _picture_chooser(desktop, files, add_entry)

    def add_entry(path):
        item = QListWidgetItem(_thumb(path), Path(path).stem.replace("_", " "))
        item.setData(Qt.UserRole, str(path))
        lst.addItem(item)
        lst.setCurrentItem(item)

    lst.currentItemChanged.connect(changed)
    position.currentIndexChanged.connect(changed)
    color.currentIndexChanged.connect(changed)
    browse.clicked.connect(pick_browsed)
    apply_btn.clicked.connect(apply)
    ok.clicked.connect(lambda: (apply(), close()))
    cancel.clicked.connect(close)
    win = _fixed_window(desktop, "Display Properties", body, close)
    win.icon = QIcon(monitor_icon(16))
    holder["win"] = win
    desktop.open_window(win)
    return win


def _saver_tab(desktop, on_change):
    """Display Properties' Screen Saver tab. Returns (widget, function giving the chosen settings)."""
    from . import screensaver
    s = screensaver.settings()
    page = QWidget()
    v = QVBoxLayout(page)
    monitor = MonitorPreview(saver=s["saver"])
    v.addWidget(monitor, 0, Qt.AlignHCenter)
    group = QGroupBox("Screen saver")
    g = QGridLayout(group)
    combo = QComboBox()
    combo.addItems(list(screensaver.SAVERS))
    combo.setCurrentText(s["saver"])
    g.addWidget(combo, 0, 0, 1, 2)
    settings_btn = QPushButton("Se&ttings")
    preview_btn = QPushButton("Pre&view")
    g.addWidget(settings_btn, 0, 2)
    g.addWidget(preview_btn, 0, 3)
    wait_row = QHBoxLayout()
    wait_label = QLabel("&Wait:")
    wait = QSpinBox()
    wait.setRange(1, 9999)
    wait.setValue(int(s["wait"]))
    wait_label.setBuddy(wait)
    wait_row.addWidget(wait_label)
    wait_row.addWidget(wait)
    wait_row.addWidget(QLabel("minutes"))
    resume = QCheckBox("On &resume, display Welcome screen")
    resume.setChecked(bool(s["resume_welcome"]))
    wait_row.addSpacing(10)
    wait_row.addWidget(resume)
    wait_row.addStretch()
    g.addLayout(wait_row, 1, 0, 1, 4)
    v.addWidget(group)
    power = QGroupBox("Monitor power")
    pv = QHBoxLayout(power)
    pv.addWidget(QLabel("To adjust monitor power settings and save energy, click Power."), 1)
    power_btn = QPushButton("P&ower...")
    power_btn.setEnabled(False)
    pv.addWidget(power_btn)
    v.addWidget(power)
    state = {"marquee": s["marquee"]}

    def update_enabled():
        none = combo.currentText() == "(None)"
        for w in (settings_btn, preview_btn, wait, resume):
            w.setEnabled(not none)

    def changed(*_):
        monitor.show_saver(combo.currentText())
        update_enabled()
        on_change()

    def open_settings():
        from .explorer.dialogs import msgbox
        if combo.currentText() == "Marquee":
            from .programs.claudeai.app import ask_text

            def set_text(text):
                if text.strip():
                    state["marquee"] = text.strip()
                    on_change()

            ask_text(desktop, "Marquee Setup", "Text:", state["marquee"], set_text)
        else:
            msgbox(desktop, "Display Properties", "This screen saver has no options that you can set.", "info")

    def preview():
        if combo.currentText() != "(None)":
            if combo.currentText() == "Marquee":
                display.get().data["marquee"] = state["marquee"]   # preview the new text
            desktop.window().screensaver.start(combo.currentText())

    combo.currentIndexChanged.connect(changed)
    wait.valueChanged.connect(lambda _v: on_change())
    resume.toggled.connect(lambda _v: on_change())
    settings_btn.clicked.connect(open_settings)
    preview_btn.clicked.connect(preview)
    update_enabled()

    def values():
        return {"saver": combo.currentText(), "wait": wait.value(), "resume_welcome": resume.isChecked(),
                "marquee": state["marquee"]}

    return page, values


def customize_desktop(desktop):
    """Desktop Items: tick which built-in icons appear on the desktop."""
    from .desktop_icons import builtins
    from .network import DialogBody, _fixed_window
    mgr = desktop.icons
    body = DialogBody()
    v = QVBoxLayout(body)
    v.setContentsMargins(14, 12, 14, 12)
    group = QGroupBox("Desktop icons")
    g = QVBoxLayout(group)
    boxes = {}
    for key, label, icon in builtins():
        box = QCheckBox(mgr.state["labels"].get(key, label))
        box.setIcon(icon())
        box.setChecked(key not in mgr.state["hidden"])
        g.addWidget(box)
        boxes[key] = box
    v.addWidget(group)
    row = QHBoxLayout()
    restore = QPushButton("Restore Default")
    row.addWidget(restore)
    row.addStretch()
    ok, cancel = QPushButton("OK"), QPushButton("Cancel")
    for b in (ok, cancel):
        b.setFixedSize(75, 23)
        row.addWidget(b)
    v.addLayout(row)
    body.setFixedWidth(300)
    holder = {}

    def close():
        if holder.get("win") is not None:
            desktop.close_window(holder.pop("win"))

    def accept():
        mgr.set_hidden([k for k, b in boxes.items() if not b.isChecked()])
        close()

    restore.clicked.connect(lambda: [b.setChecked(True) for b in boxes.values()])
    ok.clicked.connect(accept)
    cancel.clicked.connect(close)
    holder["win"] = _fixed_window(desktop, "Desktop Items", body, close)
    desktop.open_window(holder["win"])


def _info_page(text):
    page = QWidget()
    v = QVBoxLayout(page)
    label = QLabel(text)
    label.setWordWrap(True)
    label.setStyleSheet("font-family: Tahoma; font-size: 11px;")
    v.addWidget(label)
    v.addStretch()
    return page


def _picture_chooser(desktop, files, on_pick):
    from .explorer import vfs
    from .network import DialogBody, _fixed_window
    body = DialogBody()
    v = QVBoxLayout(body)
    v.addWidget(QLabel("Pictures on this computer:"))
    lst = QListWidget()
    lst.setIconSize(QSize(32, 24))
    lst.setFixedHeight(220)
    lst.setStyleSheet("QListWidget { background: white; }")
    for f in files:
        item = QListWidgetItem(_thumb(f), vfs.to_virtual(f) or f.name)
        item.setData(Qt.UserRole, str(f))
        lst.addItem(item)
    v.addWidget(lst)
    row = QHBoxLayout()
    row.addStretch()
    ok, cancel = QPushButton("Open"), QPushButton("Cancel")
    for b in (ok, cancel):
        b.setFixedSize(75, 23)
        row.addWidget(b)
    v.addLayout(row)
    body.setFixedWidth(420)
    holder = {}

    def close():
        if holder.get("win") is not None:
            desktop.close_window(holder.pop("win"))

    def pick():
        item = lst.currentItem()
        if item is not None:
            path = item.data(Qt.UserRole)
            close()
            on_pick(path)

    ok.clicked.connect(pick)
    lst.itemDoubleClicked.connect(lambda _i: pick())
    cancel.clicked.connect(close)
    holder["win"] = _fixed_window(desktop, "Browse", body, close)
    desktop.open_window(holder["win"])


# ---- User Accounts ----------------------------------------------------------------------------------------

HEADER = "font-family: 'Trebuchet MS'; font-size: 20px; color: #2154AF;"
LINK = ("QPushButton { color: #0B5BC6; font-family: Tahoma; font-size: 12px; text-align: left; border: none;"
        " background: transparent; padding: 4px; } QPushButton:hover { text-decoration: underline; }")


def accounts_icon(size=32):
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    s = size / 32
    for dx, col in ((8, "#5B8DD6"), (0, "#3C6FC1")):
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(col))
        p.drawEllipse(QRectF((9 + dx) * s, 4 * s, 9 * s, 9 * s))
        p.drawRoundedRect(QRectF((5 + dx) * s, 14 * s, 17 * s, 14 * s), 6 * s, 6 * s)
    p.end()
    return pm


class UserAccounts(QWidget):
    def __init__(self, desktop):
        super().__init__()
        self.desktop = desktop
        self.frame = None
        self.setObjectName("ua")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("QWidget#ua { background: white; } QLabel { font-family: Tahoma; font-size: 11px; }")
        self.pages = QStackedWidget()
        self.pages.addWidget(self._home_page())
        self.pages.addWidget(self._picture_page())
        self.pages.addWidget(self._name_page())
        self.pages.addWidget(self._online_page())
        self.pages.addWidget(self._password_page("windows"))
        self.pages.addWidget(self._password_page("online"))
        side = QWidget()
        side.setObjectName("uaside")
        side.setAttribute(Qt.WA_StyledBackground, True)
        side.setStyleSheet("QWidget#uaside { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #7BA2E7,"
                           " stop:1 #6375D6); }")
        side.setFixedWidth(170)
        sv = QVBoxLayout(side)
        sv.setContentsMargins(10, 10, 10, 10)
        box = QLabel("<b style='color:#215DC6'>Related Tasks</b><br><br>"
                     "<span style='color:#215DC6'>Change the desktop background</span>")
        box.setStyleSheet("background: #D6DFF7; border: 1px solid white; padding: 6px; font-family: Tahoma;"
                          " font-size: 11px;")
        box.setWordWrap(True)
        box.setCursor(Qt.PointingHandCursor)
        box.mousePressEvent = lambda _e: display_properties(self.desktop)
        sv.addWidget(box)
        sv.addStretch()
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(side)
        root.addWidget(self.pages, 1)
        user.account().changed.connect(self._refresh)
        self._refresh()

    def _card(self):
        row = QHBoxLayout()
        self.card_pic = QLabel()
        self.card_pic.setFixedSize(52, 52)
        self.card_pic.setStyleSheet("border: 2px solid #E0E0E0;")
        row.addWidget(self.card_pic)
        self.card_text = QLabel()
        row.addWidget(self.card_text, 1)
        return row

    def _home_page(self):
        page = QWidget()
        v = QVBoxLayout(page)
        v.setContentsMargins(24, 18, 24, 18)
        title = QLabel("User Accounts")
        title.setStyleSheet(HEADER)
        v.addWidget(title)
        v.addSpacing(10)
        v.addLayout(self._card())
        v.addSpacing(16)
        sub = QLabel("What do you want to change about your account?")
        sub.setStyleSheet("font-family: 'Trebuchet MS'; font-size: 14px; color: #2154AF;")
        v.addWidget(sub)
        self.links = {}
        for key, text, idx in (("name", "Change my name", 2), ("picture", "Change my picture", 1),
                               ("online", "Change my online name", 3), ("winpw", "Create a password", 4),
                               ("onlinepw", "Create an online password", 5)):
            b = QPushButton("▸  " + text)
            b.setStyleSheet(LINK)
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(lambda _c=False, i=idx: self._go(i))
            v.addWidget(b)
            self.links[key] = b
        v.addStretch()
        return page

    def _page_shell(self, title_text):
        page = QWidget()
        v = QVBoxLayout(page)
        v.setContentsMargins(24, 18, 24, 18)
        title = QLabel(title_text)
        title.setStyleSheet(HEADER)
        title.setWordWrap(True)
        v.addWidget(title)
        v.addSpacing(8)
        return page, v

    def _buttons(self, v, ok_text, ok_slot):
        v.addStretch()
        row = QHBoxLayout()
        row.addStretch()
        ok, cancel = QPushButton(ok_text), QPushButton("Cancel")
        for b in (ok, cancel):
            b.setFixedHeight(23)
            row.addWidget(b)
        ok.clicked.connect(ok_slot)
        cancel.clicked.connect(lambda: self._go(0))
        v.addLayout(row)
        return ok

    def _online_page(self):
        from .accounts import OnlineNameForm
        page, v = self._page_shell("What name do you want to use online?")
        self.online_form = OnlineNameForm(user.user_name)
        v.addWidget(self.online_form)
        note = QLabel("Your buddies will simply know you by the new name.")
        note.setWordWrap(True)
        v.addWidget(note)
        ok = self._buttons(v, "Change Online Name", self._change_online)
        self.online_form.changed.connect(lambda: ok.setEnabled(self.online_form.valid()))
        return page

    def _password_page(self, kind):
        from .accounts import PRETEND_NOTE, PasswordForm
        title = "Your Windows password" if kind == "windows" else "Your online password"
        page, v = self._page_shell(title)
        explain = QLabel("The Welcome screen asks for this password when you log on." if kind == "windows" else
                         "This password is filled in for you when you sign on to America Online and AIM.")
        explain.setWordWrap(True)
        v.addWidget(explain)
        v.addSpacing(6)
        form = PasswordForm("", "Don't use a Windows password" if kind == "windows" else
                            "Don't use an online password")
        v.addWidget(form)
        note = QLabel(PRETEND_NOTE)
        note.setWordWrap(True)
        note.setStyleSheet("color: #606060;")
        v.addWidget(note)
        ok = self._buttons(v, "Save", lambda: self._save_password(kind, form))
        form.changed.connect(lambda: ok.setEnabled(form.valid()))
        setattr(self, f"{kind}_pw_form", form)
        return page

    def _change_online(self):
        if not self.online_form.valid():
            return
        user.set_online(self.online_form.value(), self.online_form.linked(), self.online_form.is_same())
        from .programs import aim
        try:
            aim.apply_identity()
        except Exception:
            pass
        sound.play("navigate")
        self._go(0)

    def _save_password(self, kind, form):
        if not form.valid():
            return
        if kind == "windows":
            user.set_windows_password(form.value())
        else:
            user.set_online_password(form.value())
            from .programs import aim
            try:
                aim.apply_identity()
            except Exception:
                pass
        sound.play("navigate")
        self._go(0)

    def _picture_page(self):
        page = QWidget()
        v = QVBoxLayout(page)
        v.setContentsMargins(24, 18, 24, 18)
        title = QLabel("Pick a new picture for your account")
        title.setStyleSheet(HEADER)
        v.addWidget(title)
        head = QHBoxLayout()
        self.big_pic = QLabel()
        self.big_pic.setFixedSize(52, 52)
        self.big_pic.setStyleSheet("border: 2px solid #E0E0E0;")
        head.addWidget(self.big_pic)
        caption = QLabel("The picture you choose will appear on the Welcome screen and on the Start menu.")
        caption.setWordWrap(True)
        head.addWidget(caption, 1)
        v.addLayout(head)
        self.grid = QListWidget()
        self.grid.setViewMode(QListWidget.IconMode)
        self.grid.setIconSize(QSize(48, 48))
        self.grid.setGridSize(QSize(62, 62))
        self.grid.setMovement(QListWidget.Static)
        self.grid.setResizeMode(QListWidget.Adjust)
        self.grid.setStyleSheet("QListWidget { background: white; border: 1px solid #7F9DB9; }")
        for pic_id, label, pm in user.pictures():
            item = QListWidgetItem(QIcon(pm), "")
            item.setToolTip(label)
            item.setData(Qt.UserRole, pic_id)
            self.grid.addItem(item)
        self.grid.currentItemChanged.connect(lambda cur, _p: cur and self.big_pic.setPixmap(
            cur.icon().pixmap(48, 48)))
        self.grid.itemDoubleClicked.connect(lambda _i: self._change_picture())
        v.addWidget(self.grid, 1)
        row = QHBoxLayout()
        row.addStretch()
        change, cancel = QPushButton("Change Picture"), QPushButton("Cancel")
        for b in (change, cancel):
            b.setFixedHeight(23)
            row.addWidget(b)
        change.clicked.connect(self._change_picture)
        cancel.clicked.connect(lambda: self._go(0))
        v.addLayout(row)
        return page

    def _name_page(self):
        page = QWidget()
        v = QVBoxLayout(page)
        v.setContentsMargins(24, 18, 24, 18)
        title = QLabel("Provide a new name for your account")
        title.setStyleSheet(HEADER)
        v.addWidget(title)
        v.addSpacing(10)
        v.addWidget(QLabel("Type a new name:"))
        self.name_edit = QLineEdit()
        self.name_edit.setMaxLength(20)
        self.name_edit.returnPressed.connect(self._change_name)
        v.addWidget(self.name_edit)
        v.addWidget(QLabel("This name will appear on the Welcome screen and on the Start menu."))
        v.addStretch()
        row = QHBoxLayout()
        row.addStretch()
        change, cancel = QPushButton("Change Name"), QPushButton("Cancel")
        for b in (change, cancel):
            b.setFixedHeight(23)
            row.addWidget(b)
        change.clicked.connect(self._change_name)
        cancel.clicked.connect(lambda: self._go(0))
        v.addLayout(row)
        return page

    def _go(self, index):
        if index == 1:
            for i in range(self.grid.count()):
                if self.grid.item(i).data(Qt.UserRole) == user.picture_id():
                    self.grid.setCurrentRow(i)
        if index == 2:
            self.name_edit.setText(user.user_name())
            self.name_edit.selectAll()
            self.name_edit.setFocus()
        if index == 3:
            self.online_form.set_values(user.online_handle(), user.linked(), user.same_as_windows())
        if index in (4, 5):
            form = self.windows_pw_form if index == 4 else self.online_pw_form
            has = user.has_windows_password() if index == 4 else bool(user.online_password())
            form.none.setChecked(not has)
            form.pw.clear()
            form.confirm.clear()
        self.pages.setCurrentIndex(index)

    def _change_picture(self):
        item = self.grid.currentItem()
        if item is not None:
            user.set_picture(item.data(Qt.UserRole))
            sound.play("navigate")
        self._go(0)

    def _change_name(self):
        name = self.name_edit.text().strip()
        if name:
            user.set_name(name)
            sound.play("navigate")
        self._go(0)

    def _refresh(self):
        pm = user.picture_pixmap()
        if pm is not None:
            scaled = pm.scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.card_pic.setPixmap(scaled)
            self.big_pic.setPixmap(scaled)
        online = user.online_handle()
        everywhere = "used for all accounts" if user.linked() else "programs ask separately"
        locks = ("Password protected" if user.has_windows_password() else "No password")
        self.card_text.setText(f"<span style='font-size:15px; font-family:Trebuchet MS;'><b>{user.user_name()}</b>"
                               f"</span><br>Computer administrator<br>{locks}<br>Online: <b>{online}</b> "
                               f"({everywhere})")
        if hasattr(self, "links"):
            self.links["winpw"].setText("▸  " + ("Change my password" if user.has_windows_password()
                                                 else "Create a password"))
            self.links["onlinepw"].setText("▸  " + ("Change my online password" if user.online_password()
                                                    else "Create an online password"))


def user_accounts(desktop, page=0):
    def make():
        content = UserAccounts(desktop)
        win = XPWindow(desktop, "User Accounts", content, QIcon(accounts_icon(16)), size=(640, 470))
        content.frame = win
        desktop.open_window(win)
        return win

    win = _single(desktop, "accounts", make)
    win.content._go(page)
    return win


# ---- Control Panel -------------------------------------------------------------------------------------------

def _printer_icon():
    from .printing import printer_icon
    return QIcon(printer_icon(32))


def _printers(desktop):
    from .printing import printers_and_faxes
    printers_and_faxes(desktop)


def control_panel(desktop):
    def make():
        from . import network, programs
        from .explorer.dialogs import msgbox
        body = QWidget()
        body.setObjectName("cp")
        body.setAttribute(Qt.WA_StyledBackground, True)
        body.setStyleSheet("QWidget#cp { background: white; }")
        v = QVBoxLayout(body)
        v.setContentsMargins(0, 0, 0, 0)
        banner = QLabel("  Control Panel")
        banner.setFixedHeight(46)
        banner.setStyleSheet("color: white; font-family: 'Trebuchet MS'; font-size: 20px; font-weight: bold;"
                             " background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2154AF, stop:1 #7BA2E7);")
        v.addWidget(banner)
        grid = QListWidget()
        grid.setViewMode(QListWidget.IconMode)
        grid.setIconSize(QSize(32, 32))
        grid.setGridSize(QSize(110, 78))
        grid.setWordWrap(True)
        grid.setMovement(QListWidget.Static)
        grid.setResizeMode(QListWidget.Adjust)
        grid.setStyleSheet("QListWidget { border: none; font-family: Tahoma; font-size: 11px; }")

        def not_here(name):
            return lambda: msgbox(desktop, name, f"{name} isn't available on this computer yet.", "info")

        def system():
            from .explorer.dialogs import system_info
            system_info(desktop)

        items = [
            ("Display", QIcon(monitor_icon(32)), lambda: display_properties(desktop)),
            ("User Accounts", QIcon(accounts_icon(32)), lambda: user_accounts(desktop)),
            ("Network Connections", programs.get("connect").icon(), lambda: programs.launch(desktop, "connect")),
            ("System", std(QStyle.SP_ComputerIcon), system),
            ("Windows Update", programs.get("winupdate").icon(), lambda: programs.launch(desktop, "winupdate")),
            ("Add or Remove Programs", std(QStyle.SP_DialogApplyButton), not_here("Add or Remove Programs")),
            ("Date and Time", std(QStyle.SP_FileDialogInfoView), not_here("Date and Time")),
            ("Sounds and Audio Devices", std(QStyle.SP_MediaVolume), not_here("Sounds and Audio Devices")),
            ("Internet Options", std(QStyle.SP_BrowserReload), not_here("Internet Options")),
            ("Printers and Faxes", _printer_icon(), lambda: _printers(desktop)),
            ("Scheduled Tasks", std(QStyle.SP_FileDialogDetailedView), not_here("Scheduled Tasks")),
            ("Fonts", std(QStyle.SP_FileDialogListView), not_here("Fonts")),
        ]
        actions = {}
        for name, icon, action in items:
            it = QListWidgetItem(icon, name)
            grid.addItem(it)
            actions[name] = action
        grid.itemActivated.connect(lambda it: actions[it.text()]())
        v.addWidget(grid, 1)
        win = XPWindow(desktop, "Control Panel", body, std(QStyle.SP_DesktopIcon), size=(620, 420))
        desktop.open_window(win)
        sound.play("navigate")
        return win

    return _single(desktop, "controlpanel", make)
