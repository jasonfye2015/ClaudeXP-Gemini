"""File Explorer, Windows 11 style, on top of ClaudeXP's file manager: a tab row, Back/Forward/Up beside the
breadcrumb address bar and the search box, the command bar (New, Cut, Copy, Paste, Rename, Share, Delete, Sort,
View, Filter, ...), the navigation pane on the left (Home, Gallery, your folders, This PC, Network) and the status
bar along the bottom. Everything behind it - the views, the drives, the Recycle Bin, drag and drop, properties - is
the XP code, unchanged."""
from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QLineEdit, QMenu, QStyle, QToolButton, QTreeWidget,
                               QTreeWidgetItem, QWidget)

from . import sound, vfs
from .wm import MicaWindow

STYLE11 = """
QWidget { font-family: 'Segoe UI Variable Text', 'Segoe UI'; font-size: 12px; color: #1A1A1A; }
QMenu { background: #F9F9F9; border: 1px solid #E0E0E0; border-radius: 8px; padding: 4px; }
QMenu::item { padding: 6px 28px 6px 12px; border-radius: 4px; margin: 1px 2px; }
QMenu::item:selected { background: #EAEAEA; }
QMenu::separator { height: 1px; background: #E5E5E5; margin: 4px 8px; }
QWidget#tabrow { background: #DEE4EB; }
QToolButton#tab { background: #F3F3F3; border: none; border-top-left-radius: 8px; border-top-right-radius: 8px;
                  padding: 6px 14px; min-width: 160px; text-align: left; }
QToolButton#newtab { border: none; padding: 2px 8px; font-size: 15px; color: #5C5C5C; border-radius: 4px; }
QToolButton#newtab:hover { background: rgba(0, 0, 0, 16); }
QWidget#addrrow { background: #F3F3F3; }
QWidget#cmdbar { background: #F3F3F3; border-bottom: 1px solid #E5E5E5; }
QToolButton#nav { border: none; border-radius: 4px; padding: 2px; }
QToolButton#nav:hover { background: rgba(0, 0, 0, 16); }
QToolButton#nav:disabled { color: #9A9A9A; }
QToolButton#cmd { border: none; border-radius: 4px; padding: 5px 10px; color: #1A1A1A; }
QToolButton#cmd:hover { background: rgba(0, 0, 0, 16); }
QToolButton#cmd::menu-indicator { image: none; }
QComboBox#crumbs { background: #FFFFFF; border: 1px solid #E0E0E0; border-radius: 4px; padding: 4px 8px;
                   min-height: 22px; }
QComboBox#crumbs::drop-down { border: none; width: 20px; }
QLineEdit#search { background: #FFFFFF; border: 1px solid #E0E0E0; border-radius: 4px; padding: 4px 8px;
                   color: #5C5C5C; min-height: 22px; }
QLineEdit#search:focus { color: #1A1A1A; border-bottom: 2px solid #0067C0; }
QListView, QTreeView, QListWidget, QTreeWidget { background: white; border: none; outline: none; }
QListView::item:hover, QTreeView::item:hover { background: #F0F0F0; }
QListView::item:selected, QTreeView::item:selected { background: #E5E5E5; color: #1A1A1A; }
QTreeWidget#navpane { background: #F3F3F3; border: none; border-right: 1px solid #E5E5E5; outline: none; }
QTreeWidget#navpane::item { height: 30px; border-radius: 4px; }
QTreeWidget#navpane::item:hover { background: rgba(0, 0, 0, 14); }
QTreeWidget#navpane::item:selected { background: rgba(0, 0, 0, 24); color: #1A1A1A; }
QTreeWidget#navpane::branch { background: transparent; }
QWidget#status { background: #F3F3F3; border-top: 1px solid #E5E5E5; }
QLabel#statusbar { color: #5C5C5C; background: transparent; border: none; padding: 2px 8px; }
QHeaderView::section { background: white; border: none; border-bottom: 1px solid #E5E5E5; padding: 6px 8px;
                       color: #5C5C5C; }
QScrollBar:vertical { background: transparent; width: 12px; margin: 2px; }
QScrollBar::handle:vertical { background: rgba(0, 0, 0, 60); border-radius: 4px; min-height: 24px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal { background: transparent; height: 12px; margin: 2px; }
QScrollBar::handle:horizontal { background: rgba(0, 0, 0, 60); border-radius: 4px; min-width: 24px; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
"""
NAMES = {"My Computer": "This PC", "My Documents": "Documents", "Computer": "This PC"}
_xp = None


def _window():
    global _xp
    if _xp is None:
        from claudexp.explorer import window
        _xp = window
    return _xp


class RecordingPane:
    """What XP's Explorer hands its task pane (the sections and the details HTML), kept for the status bar."""

    def __init__(self):
        self.details = ""
        self.on_change = None

    def set_sections(self, sections, details):
        self.details = details
        if self.on_change:
            self.on_change(details)

    def widget(self):
        w = QWidget()
        w.hide()
        return w


def std(which):
    from PySide6.QtWidgets import QApplication
    return QApplication.style().standardIcon(which)


def _make_explorer11(desktop, location):
    """XP's Explorer, then the Windows 11 dress over it."""
    win = _window()
    real_pane = win.TaskPane
    pane = RecordingPane()

    class _Pane(QWidget):            # the task pane XP's __init__ builds: records, never shows
        def __init__(self):
            super().__init__()
            self.hide()

        def set_sections(self, sections, details):
            pane.set_sections(sections, details)

    win.TaskPane = _Pane
    try:
        content = win.Explorer(desktop, location)
    finally:
        win.TaskPane = real_pane
    _dress(content, pane)
    return content


def _dress(ex, pane):
    """Re-dress an XP Explorer as a Windows 11 one."""
    ex.setStyleSheet(STYLE11)
    root = ex.layout()
    bar = root.menuBar()
    if bar is not None:
        bar.hide()
    old = [root.itemAt(i).widget() for i in range(root.count()) if root.itemAt(i).widget() is not None]
    for w in old[:2]:
        w.hide()
    # ---- the tab row ----
    tabrow = QWidget()
    tabrow.setObjectName("tabrow")
    tabrow.setAttribute(Qt.WA_StyledBackground, True)
    trow = QHBoxLayout(tabrow)
    trow.setContentsMargins(8, 6, 8, 0)
    trow.setSpacing(2)
    ex.tab11 = QToolButton()
    ex.tab11.setObjectName("tab")
    ex.tab11.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
    ex.tab11.setIconSize(QSize(16, 16))
    trow.addWidget(ex.tab11)
    newtab = QToolButton()
    newtab.setObjectName("newtab")
    newtab.setText("+")
    newtab.setToolTip("Add new tab (Ctrl+T)")
    newtab.clicked.connect(lambda _c=False: ex.status.setText("Tabs: one at a time on this computer."))
    trow.addWidget(newtab)
    trow.addStretch()
    root.insertWidget(0, tabrow)
    # ---- the address row: Back, Forward, Recent, Up, the breadcrumb, the search box ----
    addr = QWidget()
    addr.setObjectName("addrrow")
    addr.setAttribute(Qt.WA_StyledBackground, True)
    row = QHBoxLayout(addr)
    row.setContentsMargins(8, 6, 8, 4)
    row.setSpacing(2)
    for icon, slot, tip in ((QStyle.SP_ArrowBack, ex.back, "Back"), (QStyle.SP_ArrowForward, ex.forward, "Forward")):
        b = QToolButton()
        b.setObjectName("nav")
        b.setIcon(std(icon))
        b.setIconSize(QSize(16, 16))
        b.setFixedSize(30, 30)
        b.setToolTip(tip)
        b.clicked.connect(lambda _c=False, s=slot: s())
        row.addWidget(b)
    recent = QToolButton()
    recent.setObjectName("nav")
    recent.setText("⌄")
    recent.setFixedSize(30, 30)
    recent.setToolTip("Recent locations")
    row.addWidget(recent)
    up = QToolButton()
    up.setObjectName("nav")
    up.setIcon(std(QStyle.SP_FileDialogToParent))
    up.setIconSize(QSize(16, 16))
    up.setFixedSize(30, 30)
    up.setToolTip("Up")
    up.clicked.connect(lambda _c=False: ex.up())
    row.addWidget(up)
    row.addSpacing(6)
    ex.address.setObjectName("crumbs")
    old_row = ex.address.parentWidget().layout() if ex.address.parentWidget() else None
    if old_row is not None:
        old_row.removeWidget(ex.address)
    ex.address.setParent(addr)
    row.addWidget(ex.address, 1)
    row.addSpacing(6)
    search = QLineEdit()
    search.setObjectName("search")
    search.setFixedWidth(220)
    search.setPlaceholderText("Search " + NAMES.get(ex.title_text(), ex.title_text()))
    search.textChanged.connect(lambda text: _filter(ex, text))
    row.addWidget(search)
    ex.search11 = search
    root.insertWidget(1, addr)
    # ---- the command bar ----
    cmd = QWidget()
    cmd.setObjectName("cmdbar")
    cmd.setAttribute(Qt.WA_StyledBackground, True)
    crow = QHBoxLayout(cmd)
    crow.setContentsMargins(10, 2, 10, 6)
    crow.setSpacing(2)

    def command(text, menu=None, slot=None, tip=None):
        b = QToolButton()
        b.setObjectName("cmd")
        b.setText(text + ("  ⌄" if menu is not None else ""))
        if tip:
            b.setToolTip(tip)
        if menu is not None:
            b.setMenu(menu)
            b.setPopupMode(QToolButton.InstantPopup)
        if slot is not None:
            b.clicked.connect(lambda _c=False: slot())
        crow.addWidget(b)
        return b

    def sep():
        s = QLabel("|")
        s.setStyleSheet("color: #C8C8C8; padding: 0 4px;")
        crow.addWidget(s)

    new = QMenu(ex)
    new.addAction("Folder", ex.new_folder)
    new.addAction("Shortcut", lambda: ex._not_here("New shortcut"))
    new.addSeparator()
    new.addAction("Text Document", lambda: ex.new_item("text") if hasattr(ex, "new_item") else ex._not_here("New text document"))
    command("＋ New", new)
    sep()
    command("Cut", slot=lambda: ex.copy_selected(move=True))
    command("Copy", slot=lambda: ex.copy_selected(move=False))
    command("Paste", slot=ex.paste)
    command("Rename", slot=ex.rename_selected)
    command("Share", slot=lambda: ex.status.setText("Nearby sharing is off. Turn it on in Settings > System."))
    command("Delete", slot=ex.delete_selected)
    sep()
    sort = QMenu(ex)
    for label in ("Name", "Date modified", "Type", "Size"):
        sort.addAction(label, lambda: None)
    command("Sort", sort)
    from claudexp.explorer import thumbs
    views = QMenu(ex)
    for mode, label, _size in thumbs.VIEWS:
        views.addAction(label.replace("&", ""), lambda m=mode: ex.set_view(m))
    views.addSeparator()
    views.addAction("Show > Navigation pane", lambda: ex.navpane.setVisible(not ex.navpane.isVisible()))
    command("View", views)
    filt = QMenu(ex)
    filt.addAction("Clear filter", lambda: ex.search11.clear())
    command("Filter", filt)
    more = QMenu(ex)
    more.addAction("Select all", lambda: ex.active_view().selectAll())
    more.addAction("Properties", ex.properties_selected)
    more.addSeparator()
    more.addAction("Options", lambda: _folder_options(ex))
    more.addAction("Help", lambda: _help(ex))
    more.addAction("Close", lambda: ex.frame.request_close() if ex.frame else ex.close())
    command("…", more, tip="See more")
    crow.addStretch()
    details = QToolButton()
    details.setObjectName("cmd")
    details.setText("Details")
    details.setToolTip("Details pane")
    details.clicked.connect(lambda _c=False: ex.status.setText(_plain(pane.details)))
    crow.addWidget(details)
    root.insertWidget(2, cmd)
    # ---- the navigation pane ----
    body = None
    for i in range(root.count()):
        item = root.itemAt(i)
        if item.layout() is not None:
            body = item.layout()
            break
    nav = NavPane(ex)
    if body is not None:
        body.insertWidget(0, nav)
    ex.navpane = nav
    # ---- the status bar (XP's status label moves into it) ----
    status = QWidget()
    status.setObjectName("status")
    status.setAttribute(Qt.WA_StyledBackground, True)
    status.setFixedHeight(26)
    srow = QHBoxLayout(status)
    srow.setContentsMargins(8, 0, 8, 0)
    root.removeWidget(ex.status)
    ex.status.setParent(status)
    ex.status.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    srow.addWidget(ex.status, 1)
    for mode, glyph, tip in (("details", "≡", "Details view"), ("large", "▦", "Large icons")):
        b = QToolButton()
        b.setObjectName("nav")
        b.setText(glyph)
        b.setFixedSize(24, 22)
        b.setToolTip(tip)
        target = next((m for m, label, _s in thumbs.VIEWS if (mode == "details" and "etails" in label) or
                       (mode == "large" and ("humb" in label or "arge" in label))), None)
        if target is not None:
            b.clicked.connect(lambda _c=False, m=target: ex.set_view(m))
        srow.addWidget(b)
    root.addWidget(status)

    def on_details(html):
        title = NAMES.get(ex.title_text(), ex.title_text())
        ex.tab11.setText(title)
        try:
            ex.tab11.setIcon(ex.title_icon())
        except Exception:
            pass
        ex.navpane.sync(ex)
        if hasattr(ex, "search11"):
            ex.search11.setPlaceholderText("Search " + title)
    pane.on_change = on_details
    on_details(pane.details)
    _rename(ex)


def _plain(html):
    import re
    return re.sub(r"<[^>]+>", " ", html or "").replace("&nbsp;", " ").strip()[:160]


def _rename(ex):
    """'My Computer' is 'This PC' now, 'My Documents' is 'Documents'."""
    old_title, old_addr = ex.title_text, ex.address_text

    def title_text():
        return NAMES.get(old_title(), old_title())

    def address_text():
        return NAMES.get(old_addr(), old_addr())
    ex.title_text = title_text
    ex.address_text = address_text
    if ex.frame is not None:
        ex.frame.set_title(title_text())
    try:
        ex.address.setEditText(address_text())
    except Exception:
        pass


def _filter(ex, text):
    """The search box: show only the names containing the text (in the current folder)."""
    proxy = ex.proxy
    proxy.name_filter = text.lower()
    proxy.invalidateFilter()


def _folder_options(ex):
    try:
        from claudexp import cpl_extra
        cpl_extra.folder_options(ex.desktop)
    except Exception:
        ex._not_here("Folder Options")


def _help(ex):
    from .programs.helpctr import open_help
    open_help(ex.desktop, "explorer")


class NavPane(QTreeWidget):
    """Home, Gallery, your folders, This PC and Network down the left."""

    def __init__(self, ex):
        super().__init__()
        self.ex = ex
        self.setObjectName("navpane")
        self.setHeaderHidden(True)
        self.setFixedWidth(200)
        self.setIndentation(14)
        self.setRootIsDecorated(True)
        self.setIconSize(QSize(16, 16))
        win = _window()
        home = vfs.user_home()
        self._leaf(self.invisibleRootItem(), "Home", std(QStyle.SP_DirHomeIcon), home)
        self._leaf(self.invisibleRootItem(), "Gallery", std(QStyle.SP_FileDialogContentsView), vfs.my_pictures())
        for name, icon, target in (("Desktop", QStyle.SP_DesktopIcon, home / "Desktop"),
                                   ("Downloads", QStyle.SP_ArrowDown, vfs.downloads()),
                                   ("Documents", QStyle.SP_DirIcon, vfs.my_documents()),
                                   ("Pictures", QStyle.SP_DirIcon, vfs.my_pictures()),
                                   ("Music", QStyle.SP_DirIcon, vfs.my_music()),
                                   ("Videos", QStyle.SP_DirIcon, vfs.my_videos())):
            self._leaf(self.invisibleRootItem(), name, std(icon), target)
        comp = self._section("This PC", std(QStyle.SP_ComputerIcon), target=win.MY_COMPUTER)
        for d in vfs.drives():
            self._leaf(comp, f"{d.name}", win.drive_icon(d), ("drive", d))
        self._section("Network", std(QStyle.SP_DriveNetIcon), target="network")
        self._leaf(self.invisibleRootItem(), "Recycle Bin", std(QStyle.SP_TrashIcon), win.RECYCLE_BIN)
        self.expandAll()
        self.itemClicked.connect(self._clicked)

    def _section(self, name, icon, target=None):
        it = QTreeWidgetItem([name])
        it.setIcon(0, icon)
        it.setData(0, Qt.UserRole, target)
        self.addTopLevelItem(it)
        return it

    def _leaf(self, parent, name, icon, target):
        it = QTreeWidgetItem([name])
        it.setIcon(0, icon)
        it.setData(0, Qt.UserRole, target)
        if parent is self.invisibleRootItem():
            self.addTopLevelItem(it)
        else:
            parent.addChild(it)
        return it

    def _clicked(self, item, _col):
        target = item.data(0, Qt.UserRole)
        if target is None:
            item.setExpanded(not item.isExpanded())
            return
        sound.play("navigate")
        if target == "network":
            self.ex._not_here("Network")
        elif isinstance(target, tuple) and target[0] == "drive":
            self.ex.open_drive(target[1])
        else:
            self.ex.navigate(target)

    def sync(self, ex):
        """Highlight where the window is."""
        self.blockSignals(True)
        self.clearSelection()
        loc = ex.location
        for i in range(self.topLevelItemCount()):
            top = self.topLevelItem(i)
            for it in [top] + [top.child(j) for j in range(top.childCount())]:
                t = it.data(0, Qt.UserRole)
                same = t == loc if not isinstance(t, tuple) else (t[1].root is not None and loc not in
                                                                   (_window().MY_COMPUTER, _window().RECYCLE_BIN)
                                                                   and _same(t[1].root, loc))
                if same:
                    it.setSelected(True)
        self.blockSignals(False)


def _same(a, b):
    try:
        return a.resolve() == b.resolve()
    except (OSError, AttributeError):
        return False


def launch(desktop, location=None):
    """Open a File Explorer window at This PC, the Recycle Bin, or a folder."""
    win = _window()
    if location is None:
        location = win.MY_COMPUTER
    content = _make_explorer11(desktop, location)
    try:                                   # (the external drive may still be waking up: no location yet)
        title, icon = content.title_text(), content.title_icon()
    except AttributeError:
        title, icon = getattr(location, "name", None) or "This PC", std(QStyle.SP_DirOpenIcon)
    frame = MicaWindow(desktop, title, content, icon, size=(900, 600))
    content.frame = frame
    desktop.open_window(frame)
    sound.play("navigate")
    return frame


def install():
    """Every 'explorer.launch' in the XP code opens the Windows 11 File Explorer."""
    import claudexp.explorer as pkg
    win = _window()
    pkg.launch = launch
    win.launch = launch
    # while E: spins up the window has no folder yet (location None): the skin asks for its title meanwhile
    cls = win.Explorer
    if not getattr(cls, "_waking_guard", False):
        def guarded(name, fallback):
            original = getattr(cls, name)

            def call(self, *a, **kw):
                if getattr(self, "location", None) is None:
                    return fallback()
                return original(self, *a, **kw)
            setattr(cls, name, call)
        guarded("title_text", lambda: "Opening...")
        guarded("address_text", lambda: "")
        guarded("title_icon", lambda: std(QStyle.SP_DirOpenIcon))
        cls._waking_guard = True
    proxy = win.FileProxy
    if not getattr(proxy, "_eleven", False):
        original = proxy.filterAcceptsRow

        def filterAcceptsRow(self, row, parent):
            if not original(self, row, parent):
                return False
            text = getattr(self, "name_filter", "")
            if not text:
                return True
            index = self.fs.index(row, 0, parent)
            return text in self.fs.fileName(index).lower()
        proxy.filterAcceptsRow = filterAcceptsRow
        proxy._eleven = True
