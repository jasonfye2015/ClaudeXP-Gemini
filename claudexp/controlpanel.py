"""Control Panel, Display Properties (desktop background) and User Accounts (name and picture)."""
from pathlib import Path

from PySide6.QtCore import QRect, QRectF, QSize, Qt
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


def display_properties(desktop, theme_file=None, tab=None):
    """Display Properties; theme_file opens a .theme file in the Themes tab (double-clicked in Explorer)."""
    win = _open.get("display")
    if (theme_file is not None or tab is not None) and win is not None and isValid(win):
        desktop.close_window(win)
    return _single(desktop, "display", lambda: _make_display(desktop, theme_file, tab))


def _make_display(desktop, theme_file=None, tab=None):
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
    dirty = set()
    themes_tab, theme_choice, refresh_themes = _themes_tab(desktop, lambda: mark("theme"), theme_file)
    tabs.addTab(themes_tab, "Themes")

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
    saver_tab, saver_values = _saver_tab(desktop, lambda: mark("saver"))
    tabs.addTab(saver_tab, "Screen Saver")
    look_tab, look_choice, refresh_look = _appearance_tab(lambda: mark("appearance"))
    tabs.addTab(look_tab, "Appearance")
    tabs.addTab(_info_page("Display:  Plug and Play Monitor on NVIDIA GeForce2 MX\n\nScreen resolution:  "
                           "1024 by 768 pixels\nColor quality:  Highest (32 bit)"), "Settings")
    tabs.setCurrentIndex({"themes": 0, "appearance": 3}.get(tab, 0 if theme_file else 1))
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

    def mark(what):
        dirty.add(what)
        apply_btn.setEnabled(True)

    def changed(*_):
        preview.settings = chosen()
        preview.update()
        mark("desktop")

    def show_desktop_settings():
        """After a theme changed the background: select it in the Desktop tab (without marking it changed)."""
        d = disp.data
        for w in (lst, position, color):
            w.blockSignals(True)
        found = None
        for i in range(lst.count()):
            if lst.item(i).data(Qt.UserRole) == (d["wallpaper"] or ""):
                found = lst.item(i)
        if found is None and d["wallpaper"]:
            found = QListWidgetItem(_thumb(d["wallpaper"]), Path(d["wallpaper"]).stem.replace("_", " "))
            found.setData(Qt.UserRole, d["wallpaper"])
            lst.addItem(found)
        lst.setCurrentItem(found)
        position.setCurrentText(d["position"])
        idx = next((i for i in range(color.count()) if color.itemData(i).lower() == d["color"].lower()), -1)
        if idx < 0:
            sw = QPixmap(14, 14)
            sw.fill(QColor(d["color"]))
            color.addItem(QIcon(sw), "Custom", d["color"])
            idx = color.count() - 1
        color.setCurrentIndex(idx)
        for w in (lst, position, color):
            w.blockSignals(False)
        preview.settings = dict(disp.data)
        preview.update()

    def apply():
        from . import theme, themes
        todo = set(dirty)
        dirty.clear()
        apply_btn.setEnabled(False)
        st = theme.state()
        before = (st["style"], st["scheme"], st.get("font", "normal"))
        pick = theme_choice() if "theme" in todo else None
        new_look = look_choice() if "appearance" in todo else None

        def work():
            if pick is not None:
                name, cfg = pick
                themes.apply(desktop, cfg, name)
                if cfg.get("font"):
                    theme.set_state(font=cfg["font"])
                show_desktop_settings()
                refresh_look()
            if "desktop" in todo:
                s = chosen()
                disp.apply(s["wallpaper"], s["position"], s["color"])
                theme.set_state(name="Modified Theme")
            if "saver" in todo:
                disp.set_screensaver(**saver_values())
            if new_look is not None:
                style, scheme, font = new_look
                old = theme.state()
                if (style, scheme, font) != (old["style"], old["scheme"], old.get("font", "normal")):
                    theme.set_state(style=style, scheme=scheme, font=font, name="Modified Theme")
                    desk = theme.current().desktop_color()
                    if desk and old["scheme"] != scheme:
                        disp.apply(disp.data["wallpaper"], disp.data["position"], desk)
                        show_desktop_settings()
            if todo & {"theme", "appearance", "desktop"}:
                refresh_themes()

        restyle = (pick is not None and (pick[1].get("style"), pick[1].get("scheme")) != before[:2]) or \
            (new_look is not None and new_look != before)
        if restyle:
            themes.with_please_wait(desktop, work)
        else:
            work()

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
    ok.clicked.connect(lambda: (apply(), close()) if dirty else close())
    cancel.clicked.connect(close)
    win = _fixed_window(desktop, "Display Properties", body, close)
    win.icon = QIcon(monitor_icon(16))
    holder["win"] = win
    desktop.open_window(win)
    return win


class ThemePreview(QWidget):
    """Display Properties' sample: the theme's background, a window in its visual style and its taskbar."""

    def __init__(self, size=(360, 190)):
        super().__init__()
        self.setFixedSize(*size)
        self.cfg = None

    def show_settings(self, cfg):
        self.cfg = cfg
        self.update()

    def paintEvent(self, event):
        from . import theme, themes
        cfg = self.cfg or {}
        st = theme.make_style(cfg.get("style", "luna"), cfg.get("scheme", "blue"), cfg.get("font", "normal"))
        p = QPainter(self)
        w, h = self.width(), self.height()
        d = dict(display.get().data)
        wall = themes.resolve_wallpaper(cfg.get("wallpaper"))
        if wall is not None:
            d.update(wallpaper=wall or "", position=cfg.get("position", "Stretch"), color=cfg.get("color", d["color"]))
        p.drawPixmap(QRectF(0, 0, w, h), display.get().render(1024, 738, d), QRectF(0, 0, 1024, 738))
        ww, wh = w - 70, h - 66
        p.save()
        p.translate(22, 12)
        st.paint_frame(p, ww, wh, "Active Window", QIcon(monitor_icon(16)), True, ("min", "max", "close"))
        pal = st.palette()
        face = pal.window().color() if pal is not None else QColor("#ECE9D8")
        p.fillRect(st.border, st.title_h, ww - 2 * st.border, wh - st.title_h - st.border, face)
        p.fillRect(QRectF(st.border + 8, st.title_h + 8, ww - 2 * st.border - 16, wh - st.title_h - 20),
                   QColor("#000000" if face.value() < 60 else "#FFFFFF"))
        p.setPen(QColor("#FFFFFF" if face.value() < 60 else "#000000"))
        p.setFont(QFont("Tahoma", 8))
        p.drawText(st.border + 14, st.title_h + 24, "Window Text")
        p.restore()
        p.save()
        p.translate(0, h - 30)
        st.paint_taskbar(p, QRect(0, 0, w, 30), QRect(0, 0, st.start_width(), 30), False)
        p.restore()
        p.setPen(QPen(QColor("#7F9DB9"), 1))
        p.setBrush(Qt.NoBrush)
        p.drawRect(self.rect().adjusted(0, 0, -1, -1))


def _theme_entries():
    """[(label, name, cfg, file)] for the Theme list: the built-ins, then .theme files the user saved."""
    from . import themes
    from .explorer import vfs
    out = [(name, name, cfg, None) for name, cfg in themes.THEMES.items()]
    for folder in (vfs.my_documents(), vfs.user_home() / "Desktop"):
        if folder.is_dir():
            for f in sorted(folder.glob("*.theme")):
                got = themes.read_file(f)
                if got:
                    where = "My Documents" if folder == vfs.my_documents() else "Desktop"
                    out.append((f"{got[0]} ({where})", got[0], got[1], f))
    return out


def _themes_tab(desktop, on_change, theme_file=None):
    """Display Properties' Themes tab. Returns (widget, chosen() -> (name, cfg) or None, refresh())."""
    from . import theme, themes
    themes.install_files()
    page = QWidget()
    v = QVBoxLayout(page)
    intro = QLabel("A theme is a background plus a set of sounds, icons, and other elements to help you "
                   "personalize your computer with one click.")
    intro.setWordWrap(True)
    v.addWidget(intro)
    theme_label = QLabel("&Theme:")
    v.addWidget(theme_label)
    row = QHBoxLayout()
    combo = QComboBox()
    theme_label.setBuddy(combo)
    row.addWidget(combo, 1)
    save = QPushButton("&Save As...")
    delete = QPushButton("&Delete")
    row.addWidget(save)
    row.addWidget(delete)
    v.addLayout(row)
    v.addWidget(QLabel("Sample:"))
    sample = ThemePreview()
    v.addWidget(sample, 0, Qt.AlignHCenter)
    v.addStretch()
    extra = {}                                   # themes opened with Browse... or from Explorer: name -> (cfg, file)

    def fill(select=None):
        combo.blockSignals(True)
        combo.clear()
        cur = theme.state().get("name", "Windows XP")
        entries = _theme_entries()
        if cur not in [e[1] for e in entries] and cur not in extra:
            combo.addItem(cur, (cur, None, None))
        for label, name, cfg, f in entries:
            combo.addItem(label, (name, cfg, str(f) if f else None))
        for name, (cfg, f) in extra.items():
            combo.addItem(name, (name, cfg, f))
        combo.addItem("Browse...", ("__browse__", None, None))
        target = select or cur
        for i in range(combo.count()):
            if combo.itemData(i)[0] == target:
                combo.setCurrentIndex(i)
                break
        combo.blockSignals(False)
        show()

    def show():
        data = combo.currentData()
        if not data:
            return
        _name, cfg, f = data
        sample.show_settings(cfg if cfg else themes.current_settings())
        delete.setEnabled(bool(f) and str(themes.themes_dir()) not in str(f))

    def picked(i):
        data = combo.itemData(i)
        if data and data[0] == "__browse__":
            from .programs.opendialog import open_dialog

            def got(path):
                res = themes.read_file(path)
                if res:
                    extra[res[0]] = (res[1], str(path))
                    fill(select=res[0])
                    on_change()
            fill()
            open_dialog(desktop, "Open Theme", {".theme"}, got, QIcon(monitor_icon(16)), themes.themes_dir())
            return
        show()
        if data and data[1] is not None:
            on_change()

    def save_as():
        from .explorer import vfs
        from .network import DialogBody, _fixed_window
        body = DialogBody()
        lay = QVBoxLayout(body)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.addWidget(QLabel("Save the current theme in My Documents as:"))
        name = QLineEdit("My Theme")
        lay.addWidget(name)
        r = QHBoxLayout()
        r.addStretch()
        ok, cancel = QPushButton("Save"), QPushButton("Cancel")
        for b in (ok, cancel):
            b.setFixedSize(75, 23)
            r.addWidget(b)
        lay.addLayout(r)
        body.setFixedWidth(300)
        holder = {}

        def close():
            w = holder.pop("win", None)
            if w is not None and isValid(w):
                desktop.close_window(w)

        def do_save():
            bad = set('\\/:*?"<>|')
            label = "".join(c for c in name.text().strip() if c not in bad) or "My Theme"
            themes.write_file(vfs.my_documents() / f"{label}.theme", label, themes.current_settings())
            theme.set_state(name=label)
            close()
            fill(select=label)
        ok.clicked.connect(do_save)
        cancel.clicked.connect(close)
        holder["win"] = _fixed_window(desktop, "Save Theme", body, close)
        desktop.open_window(holder["win"])
        name.selectAll()
        name.setFocus()

    def remove():
        from .explorer import vfs
        data = combo.currentData()
        if data and data[2] and Path(data[2]).exists():
            vfs.recycle(Path(data[2]))
            extra.pop(data[0], None)
            fill()

    combo.currentIndexChanged.connect(picked)
    save.clicked.connect(save_as)
    delete.clicked.connect(remove)
    res = themes.read_file(theme_file) if theme_file is not None else None
    if res:
        from PySide6.QtCore import QTimer
        extra[res[0]] = (res[1], str(theme_file))
        fill(select=res[0])
        QTimer.singleShot(0, on_change)            # once the dialog (and its Apply button) exists
    else:
        fill()

    def chosen():
        data = combo.currentData()
        if not data or data[1] is None:
            return None
        return data[0], data[1]
    return page, chosen, fill


class AppearancePreview(QWidget):
    """Appearance tab sample: an inactive window, an active one and a message box."""

    def __init__(self):
        super().__init__()
        self.setFixedSize(360, 170)
        self.look = ("luna", "blue", "normal")

    def paintEvent(self, event):
        from . import theme
        st = theme.make_style(*self.look)
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(st.desktop_color() or "#5A7EC8"))
        pal = st.palette()
        face = pal.window().color() if pal is not None else QColor("#ECE9D8")
        ink = QColor("#FFFFFF" if face.value() < 60 else "#000000")
        for x, y, ww, wh, title, active in ((10, 8, 250, 100, "Inactive Window", False),
                                             (40, 40, 310, 122, "Active Window", True)):
            p.save()
            p.translate(x, y)
            st.paint_frame(p, ww, wh, title, QIcon(monitor_icon(16)), active, ("min", "max", "close"))
            p.fillRect(st.border, st.title_h, ww - 2 * st.border, wh - st.title_h - st.border, face)
            if active:
                p.setFont(QFont("Tahoma", 8))
                p.setPen(ink)
                p.drawText(st.border + 8, st.title_h + 16, "Window Text")
                sel = pal.highlight().color() if pal is not None else QColor("#316AC5")
                p.fillRect(QRectF(st.border + 90, st.title_h + 5, 56, 15), sel)
                p.setPen(QColor("white"))
                p.drawText(st.border + 94, st.title_h + 16, "Selected")
                p.save()
                p.translate(80, st.title_h + 26)
                st.paint_frame(p, 170, 56, "Message Box", None, True, ("close",))
                p.fillRect(st.border, st.title_h, 170 - 2 * st.border, 56 - st.title_h - st.border, face)
                p.setFont(QFont("Tahoma", 8))
                p.setPen(ink)
                p.drawText(st.border + 6, st.title_h + 14, "Message Text")
                p.restore()
            p.restore()
        p.setPen(QPen(QColor("#7F9DB9"), 1))
        p.setBrush(Qt.NoBrush)
        p.drawRect(self.rect().adjusted(0, 0, -1, -1))


def _appearance_tab(on_change):
    """Display Properties' Appearance tab. Returns (widget, chosen() -> (style, scheme, font), refresh())."""
    from . import theme
    page = QWidget()
    v = QVBoxLayout(page)
    sample = AppearancePreview()
    v.addWidget(sample, 0, Qt.AlignHCenter)
    grid = QGridLayout()
    styles, schemes, fonts = QComboBox(), QComboBox(), QComboBox()
    for row, (text, box) in enumerate((("&Windows and buttons:", styles), ("Color s&cheme:", schemes),
                                       ("Font si&ze:", fonts))):
        label = QLabel(text)
        label.setBuddy(box)
        grid.addWidget(label, row * 2, 0)
        grid.addWidget(box, row * 2 + 1, 0)
    for key, label in theme.FONT_SIZES:
        fonts.addItem(label, key)
    v.addLayout(grid)
    note = QLabel()
    note.setWordWrap(True)
    v.addWidget(note)
    v.addStretch()

    def fill_schemes(style, select=None):
        schemes.blockSignals(True)
        schemes.clear()
        for key, label in theme.schemes(style):
            schemes.addItem(label, key)
        schemes.setCurrentIndex(max(0, schemes.findData(select)) if select is not None else 0)
        schemes.blockSignals(False)

    def chosen():
        return styles.currentData() or "luna", schemes.currentData() or "blue", fonts.currentData() or "normal"

    def update():
        sample.look = chosen()
        sample.update()
        note.setText("This visual style isn't from Microsoft: it loads because StyleXP has patched uxtheme.dll."
                     if styles.currentData() in theme.HACKED else "")

    def refresh():
        s = theme.state()
        for w in (styles, fonts):
            w.blockSignals(True)
        styles.clear()
        for key, label in theme.all_styles():
            styles.addItem(label, key)
        styles.setCurrentIndex(max(0, styles.findData(s["style"])))
        fonts.setCurrentIndex(max(0, fonts.findData(s.get("font", "normal"))))
        for w in (styles, fonts):
            w.blockSignals(False)
        fill_schemes(s["style"], s["scheme"])
        update()

    def style_changed(_i):
        fill_schemes(styles.currentData())
        update()
        on_change()

    styles.currentIndexChanged.connect(style_changed)
    schemes.currentIndexChanged.connect(lambda _i: (update(), on_change()))
    fonts.currentIndexChanged.connect(lambda _i: (update(), on_change()))
    refresh()
    return page, chosen, refresh


def _scheme_dialog(desktop, title, icon, label, choices, current, preview, on_apply):
    """A one-tab properties box with a scheme drop-down (Sounds and Audio Devices / Mouse)."""
    from .network import DialogBody, _fixed_window
    body = DialogBody()
    v = QVBoxLayout(body)
    v.setContentsMargins(10, 10, 10, 10)
    v.addWidget(QLabel(label))
    combo = QComboBox()
    combo.addItems(choices)
    combo.setCurrentText(current)
    v.addWidget(combo)
    v.addWidget(preview)
    row = QHBoxLayout()
    row.addStretch()
    ok, cancel, apply_btn = QPushButton("OK"), QPushButton("Cancel"), QPushButton("&Apply")
    for b in (ok, cancel, apply_btn):
        b.setFixedSize(75, 23)
        row.addWidget(b)
    v.addLayout(row)
    body.setFixedWidth(340)
    holder = {}

    def close():
        w = holder.pop("win", None)
        if w is not None and isValid(w):
            desktop.close_window(w)
    apply_btn.clicked.connect(lambda: on_apply(combo.currentText()))
    ok.clicked.connect(lambda: (on_apply(combo.currentText()), close()))
    cancel.clicked.connect(close)
    combo.currentTextChanged.connect(lambda t: preview.show_scheme(t))
    preview.show_scheme(combo.currentText())
    win = _fixed_window(desktop, title, body, close)
    win.icon = icon
    holder["win"] = win
    desktop.open_window(win)
    return win


class _SoundList(QListWidget):
    """Program events: double-click one to hear it in the chosen scheme."""

    EVENTS = [("Default Beep", "default"), ("Critical Stop", "error"), ("Exclamation", "exclamation"),
              ("Asterisk", "info"), ("Menu Command", "menu"), ("Minimize", "minimize"), ("Restore Up", "restore"),
              ("Windows Logon", "logon"), ("Windows Logoff", "logoff"), ("Notify", "notify"),
              ("Empty Recycle Bin", "recycle")]

    def __init__(self):
        super().__init__()
        self.setFixedHeight(170)
        self.scheme = "Windows Default"
        for label, ev in self.EVENTS:
            it = QListWidgetItem(std(QStyle.SP_MediaVolume), label)
            it.setData(Qt.UserRole, ev)
            self.addItem(it)
        self.itemDoubleClicked.connect(self._play)

    def show_scheme(self, name):
        self.scheme = name

    def _play(self, item):
        from PySide6.QtMultimedia import QSoundEffect
        from PySide6.QtCore import QUrl
        from . import themes
        from .paths import SOUNDS
        ev = item.data(Qt.UserRole)
        if sound.is_muted() or self.scheme == "No Sounds":
            return
        if self.scheme in ("Aquarium", "Da Vinci", "Nature", "Space"):
            path = themes.sound_file(self.scheme, ev)
        else:
            path = SOUNDS / sound.EVENTS[ev]
        fx = QSoundEffect(self)
        fx.setSource(QUrl.fromLocalFile(str(path)))
        fx.play()
        self._fx = fx


def sound_properties(desktop):
    from . import theme, themes

    def apply(name):
        theme.set_state(sounds=name, name="Modified Theme")
        themes.apply_sounds(name)
    return _single(desktop, "sounds", lambda: _scheme_dialog(
        desktop, "Sounds and Audio Devices Properties", std(QStyle.SP_MediaVolume),
        "Sound scheme:  (double-click an event below to hear it)", themes.SOUND_SCHEMES,
        theme.state().get("sounds", "Windows Default"), _SoundList(), apply))


class _PointerPreview(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(300, 90)
        self.scheme = "Windows Default"

    def show_scheme(self, name):
        self.scheme = name
        self.update()

    def paintEvent(self, event):
        from . import themes
        p = QPainter(self)
        p.fillRect(self.rect(), QColor("white"))
        p.setPen(QColor("#7F9DB9"))
        p.drawRect(self.rect().adjusted(0, 0, -1, -1))
        p.setRenderHint(QPainter.Antialiasing)
        if self.scheme == "Windows Default":                    # the standard white arrow
            from PySide6.QtCore import QPointF
            from PySide6.QtGui import QPolygonF
            p.setPen(QPen(QColor("black"), 1))
            p.setBrush(QColor("white"))
            p.drawPolygon(QPolygonF([QPointF(32 + x, 28 + y) for x, y in
                                     ((0, 0), (0, 22), (6, 16), (10, 25), (13, 24), (9, 15), (17, 15))]))
        else:
            p.drawPixmap(30, 28, themes.cursor_pixmap(self.scheme))
        p.setPen(QColor("black"))
        p.setFont(QFont("Tahoma", 8))
        p.drawText(QRect(80, 0, 210, self.height()), Qt.AlignVCenter | Qt.AlignLeft,
                   f"Normal Select\n({self.scheme})")


def mouse_properties(desktop):
    from . import theme, themes

    def apply(name):
        theme.set_state(cursors=name, name="Modified Theme")
        themes.apply_cursors(desktop, name)
    return _single(desktop, "mouse", lambda: _scheme_dialog(
        desktop, "Mouse Properties", std(QStyle.SP_ArrowUp), "Pointers - Scheme:", themes.CURSOR_SCHEMES,
        theme.state().get("cursors", "Windows Default"), _PointerPreview(), apply))


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
        from . import fursonas
        if fursonas.locked():
            b = QPushButton("▸  View my fursona's card in The Fur Directory")
            b.setStyleSheet(LINK)
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(self._my_card)
            v.addWidget(b)
            note = QLabel(f"Your name, picture and online name belong to your fursona, "
                          f"{fursonas.chosen().name}. To choose a different fursona, reinstall Windows.")
            note.setWordWrap(True)
            note.setStyleSheet("color: #505050; font-family: Tahoma; font-size: 11px; margin-top: 8px;")
            v.addWidget(note)
        v.addStretch()
        return page

    def _my_card(self):
        from .programs import furdir
        furdir.open_furdir(self.desktop, show_me=True)

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
        from . import fursonas
        if index in (1, 2, 3) and fursonas.locked():
            from .explorer.dialogs import msgbox
            msgbox(self.desktop, "User Accounts", f"Your name, picture and online name come with your fursona, "
                   f"{fursonas.chosen().name}.\n\nTo choose a different fursona, you need to reinstall Windows.",
                   "info")
            index = 0
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

def _ai_icon():
    from .aimodels_cpl import ai_icon
    return ai_icon(32)


def _ai_models(desktop):
    from .aimodels_cpl import ai_models_properties
    return ai_models_properties(desktop)


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
            ("Sounds and Audio Devices", std(QStyle.SP_MediaVolume), lambda: sound_properties(desktop)),
            ("Mouse", std(QStyle.SP_ArrowUp), lambda: mouse_properties(desktop)),
            ("AI Models", QIcon(_ai_icon()), lambda: _ai_models(desktop)),
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
