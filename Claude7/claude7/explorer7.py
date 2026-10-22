"""Windows Explorer, Windows 7 style, on top of ClaudeXP's file manager: the menus hidden, Back and Forward beside
a breadcrumb address bar with a search box, the command bar (Organize, Include in library, Share with, Burn, New
folder, the view changer), the navigation pane on the left (Favorites, Libraries, Computer, Network) instead of XP's
blue task panes, and the details pane along the bottom. Everything behind it - the views, the drives, the Recycle Bin,
drag and drop, properties - is the XP code, unchanged."""
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QLineEdit, QMenu, QPushButton, QStyle, QToolButton,
                               QTreeWidget, QTreeWidgetItem, QWidget)

from . import sound, vfs
from .wm import AeroWindow

STYLE7 = """
QWidget { font-family: 'Segoe UI'; font-size: 12px; }
QMenu { background: #F0F0F0; border: 1px solid #979797; }
QMenu::item { padding: 4px 24px 4px 28px; }
QMenu::item:selected { background: #CCE8FF; border: 1px solid #99D1FF; }
QMenu::separator { height: 1px; background: #D7D7D7; margin: 3px 2px; }
QWidget#addrrow { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #F6F8FB, stop:1 #E9EEF5);
                  border-bottom: 1px solid #D9E1EA; }
QWidget#cmdbar { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #F4F7FB, stop:1 #DCE6F1);
                 border-bottom: 1px solid #C7D3E0; }
QToolButton#nav { border: 1px solid transparent; border-radius: 12px; padding: 1px; }
QToolButton#nav:hover { border: 1px solid #7DA2CE; background: #E8F0FA; }
QToolButton#cmd { border: 1px solid transparent; border-radius: 3px; padding: 3px 8px; color: #1E395B; }
QToolButton#cmd:hover { border: 1px solid #7DA2CE; background: #E8F0FA; }
QToolButton#cmd::menu-indicator { image: none; }
QComboBox#crumbs { background: white; border: 1px solid #ABADB3; padding: 2px 6px; min-height: 20px; }
QLineEdit#search { background: white; border: 1px solid #ABADB3; padding: 2px 6px; color: #6D6D6D; min-height: 20px; }
QLineEdit#search:focus { color: black; }
QListView, QTreeView, QListWidget, QTreeWidget { background: white; border: none; }
QTreeWidget#navpane { background: #FFFFFF; border-right: 1px solid #E3E3E3; outline: none; }
QTreeWidget#navpane::item { height: 22px; }
QTreeWidget#navpane::item:hover { background: #E5F3FB; }
QTreeWidget#navpane::item:selected { background: #CCE8FF; color: black; border: 1px solid #99D1FF; }
QWidget#details { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #F4F7FB, stop:1 #DCE6F1);
                  border-top: 1px solid #C7D3E0; }
QLabel#detailtext { color: #1E395B; background: transparent; }
QLabel#statusbar { color: #6D6D6D; background: transparent; border: none; padding: 2px 6px; }
QHeaderView::section { background: white; border: none; border-right: 1px solid #E5E5E5; border-bottom: 1px solid #E5E5E5;
                       padding: 3px 6px; color: #4C607A; }
QScrollBar:vertical { background: #F0F0F0; width: 16px; }
QScrollBar::handle:vertical { background: #CDCDCD; border-radius: 3px; min-height: 24px; margin: 2px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
"""
_xp = None


def _window():
    global _xp
    if _xp is None:
        from claudexp.explorer import window
        _xp = window
    return _xp


class RecordingPane:
    """What XP's Explorer hands its task pane (the sections and the details HTML), kept for the details pane."""

    def __init__(self):
        self.details = ""
        self.on_change = None

    def set_sections(self, sections, details):
        self.details = details
        if self.on_change:
            self.on_change(details)

    # the XP code adds it to a layout and may hide/show it: a hidden widget stands in
    def widget(self):
        w = QWidget()
        w.hide()
        return w


def std(which):
    from PySide6.QtWidgets import QApplication
    return QApplication.style().standardIcon(which)


def _make_explorer7(desktop, location):
    """XP's Explorer, then the Windows 7 dress over it."""
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
    """Re-dress an XP Explorer as a Windows 7 one."""
    ex.setStyleSheet(STYLE7)
    root = ex.layout()
    bar = root.menuBar()
    if bar is not None:
        bar.hide()                                     # Windows 7 hides the menus (Alt shows them; here they're gone)
    # XP's toolbar and address bar are the first two widgets in the root layout
    old = [root.itemAt(i).widget() for i in range(root.count()) if root.itemAt(i).widget() is not None]
    for w in old[:2]:
        w.hide()
    # ---- the address row: Back, Forward, the breadcrumb, the search box ----
    addr = QWidget()
    addr.setObjectName("addrrow")
    addr.setAttribute(Qt.WA_StyledBackground, True)
    row = QHBoxLayout(addr)
    row.setContentsMargins(6, 4, 6, 4)
    row.setSpacing(4)
    for icon, slot, tip in ((QStyle.SP_ArrowBack, ex.back, "Back"), (QStyle.SP_ArrowForward, ex.forward, "Forward")):
        b = QToolButton()
        b.setObjectName("nav")
        b.setIcon(std(icon))
        b.setIconSize(QSize(18, 18))
        b.setFixedSize(26, 26)
        b.setToolTip(tip)
        b.clicked.connect(lambda _c=False, s=slot: s())
        row.addWidget(b)
    up = QToolButton()
    up.setObjectName("nav")
    up.setIcon(std(QStyle.SP_FileDialogToParent))
    up.setIconSize(QSize(16, 16))
    up.setFixedSize(26, 26)
    up.setToolTip("Up")
    up.clicked.connect(lambda _c=False: ex.up())
    row.addWidget(up)
    ex.address.setObjectName("crumbs")
    old_row = ex.address.parentWidget().layout() if ex.address.parentWidget() else None
    if old_row is not None:
        old_row.removeWidget(ex.address)
    ex.address.setParent(addr)
    row.addWidget(ex.address, 1)
    search = QLineEdit()
    search.setObjectName("search")
    search.setFixedWidth(200)
    search.setPlaceholderText("Search " + ex.title_text())
    search.textChanged.connect(lambda text: _filter(ex, text))
    row.addWidget(search)
    ex.search7 = search
    root.insertWidget(0, addr)
    # ---- the command bar ----
    cmd = QWidget()
    cmd.setObjectName("cmdbar")
    cmd.setAttribute(Qt.WA_StyledBackground, True)
    crow = QHBoxLayout(cmd)
    crow.setContentsMargins(8, 2, 8, 2)
    crow.setSpacing(2)

    def command(text, menu=None, slot=None):
        b = QToolButton()
        b.setObjectName("cmd")
        b.setText(text + ("  ▾" if menu is not None else ""))
        if menu is not None:
            b.setMenu(menu)
            b.setPopupMode(QToolButton.InstantPopup)
        if slot is not None:
            b.clicked.connect(lambda _c=False: slot())
        crow.addWidget(b)
        return b

    organize = QMenu(ex)
    organize.addAction("Cut", lambda: ex.copy_selected(move=True))
    organize.addAction("Copy", lambda: ex.copy_selected(move=False))
    organize.addAction("Paste", ex.paste)
    organize.addSeparator()
    organize.addAction("Select all", lambda: ex.active_view().selectAll())
    organize.addSeparator()
    organize.addAction("Delete", ex.delete_selected)
    organize.addAction("Rename", ex.rename_selected)
    organize.addSeparator()
    organize.addAction("Properties", ex.properties_selected)
    organize.addSeparator()
    organize.addAction("Folder and search options", lambda: _folder_options(ex))
    organize.addAction("Close", lambda: ex.frame.request_close() if ex.frame else ex.close())
    command("Organize", organize)
    library = QMenu(ex)
    for name in ("Documents", "Music", "Pictures", "Videos"):
        library.addAction(name, lambda n=name: ex.status.setText(f"Included in the {n} library."))
    library.addSeparator()
    library.addAction("Create new library", lambda: ex.status.setText("Libraries gather folders from anywhere."))
    command("Include in library", library)
    share = QMenu(ex)
    share.addAction("Nobody", lambda: None)
    share.addAction("Homegroup (Read)", lambda: ex.status.setText("There is no homegroup on this network."))
    share.addAction("Homegroup (Read/Write)", lambda: ex.status.setText("There is no homegroup on this network."))
    share.addAction("Specific people...", lambda: ex.status.setText("This is the only account on this computer."))
    command("Share with", share)
    command("Burn", slot=lambda: ex._not_here("Burn to disc"))
    command("New folder", slot=ex.new_folder)
    crow.addStretch()
    from claudexp.explorer import thumbs
    views = QMenu(ex)
    for mode, label, _size in thumbs.VIEWS:
        views.addAction(label.replace("&", ""), lambda m=mode: ex.set_view(m))
    v = QToolButton()
    v.setObjectName("cmd")
    v.setIcon(std(QStyle.SP_FileDialogListView))
    v.setText("▾")
    v.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
    v.setMenu(views)
    v.setPopupMode(QToolButton.InstantPopup)
    v.setToolTip("Change your view")
    crow.addWidget(v)
    helpb = QToolButton()
    helpb.setObjectName("cmd")
    helpb.setIcon(std(QStyle.SP_MessageBoxQuestion))
    helpb.setToolTip("Get help")
    helpb.clicked.connect(lambda _c=False: _help(ex))
    crow.addWidget(helpb)
    root.insertWidget(1, cmd)
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
    # ---- the details pane (XP's status label moves into it) ----
    details = QWidget()
    details.setObjectName("details")
    details.setAttribute(Qt.WA_StyledBackground, True)
    details.setFixedHeight(62)
    drow = QHBoxLayout(details)
    drow.setContentsMargins(12, 6, 12, 6)
    drow.setSpacing(12)
    ex.detail_icon = QLabel()
    ex.detail_icon.setFixedSize(48, 48)
    drow.addWidget(ex.detail_icon)
    ex.detail_text = QLabel()
    ex.detail_text.setObjectName("detailtext")
    ex.detail_text.setTextFormat(Qt.RichText)
    drow.addWidget(ex.detail_text, 1)
    root.removeWidget(ex.status)
    ex.status.setParent(details)
    ex.status.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
    drow.addWidget(ex.status)
    root.addWidget(details)

    def on_details(html):
        ex.detail_text.setText(html.replace("My Computer", "Computer").replace("My Documents", "Documents"))
        ex.detail_icon.setPixmap(ex.title_icon().pixmap(48, 48))
        ex.navpane.sync(ex)
        if hasattr(ex, "search7"):
            ex.search7.setPlaceholderText("Search " + ex.title_text())
    pane.on_change = on_details
    on_details(pane.details)
    # Windows 7 names
    _rename(ex)


def _rename(ex):
    """'My Computer' is 'Computer' now, 'My Documents' is 'Documents'."""
    old_title, old_addr = ex.title_text, ex.address_text

    def title_text():
        return {"My Computer": "Computer", "My Documents": "Documents"}.get(old_title(), old_title())

    def address_text():
        return {"My Computer": "Computer"}.get(old_addr(), old_addr())
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
    open_help(ex.desktop, "libraries")


class NavPane(QTreeWidget):
    """Favorites, Libraries, Computer and Network down the left."""

    def __init__(self, ex):
        super().__init__()
        self.ex = ex
        self.setObjectName("navpane")
        self.setHeaderHidden(True)
        self.setFixedWidth(190)
        self.setIndentation(14)
        self.setRootIsDecorated(True)
        win = _window()
        home = vfs.user_home()
        fav = self._section("Favorites", std(QStyle.SP_DirLinkIcon))
        self._leaf(fav, "Desktop", std(QStyle.SP_DesktopIcon), home / "Desktop")
        self._leaf(fav, "Downloads", std(QStyle.SP_DirIcon), vfs.downloads())
        self._leaf(fav, "Recent Places", std(QStyle.SP_DirOpenIcon), home)
        lib = self._section("Libraries", std(QStyle.SP_DirHomeIcon))
        self._leaf(lib, "Documents", std(QStyle.SP_DirIcon), vfs.my_documents())
        self._leaf(lib, "Music", std(QStyle.SP_DirIcon), vfs.my_music())
        self._leaf(lib, "Pictures", std(QStyle.SP_DirIcon), vfs.my_pictures())
        self._leaf(lib, "Videos", std(QStyle.SP_DirIcon), vfs.my_videos())
        self._leaf(self.invisibleRootItem(), vfs.user_home().name, std(QStyle.SP_DirHomeIcon), home)
        comp = self._section("Computer", std(QStyle.SP_ComputerIcon), target=win.MY_COMPUTER)
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
        f = it.font(0)
        f.setBold(True)
        it.setFont(0, f)
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
    """Open a Windows Explorer window at Computer, the Recycle Bin, or a folder."""
    win = _window()
    if location is None:
        location = win.MY_COMPUTER
    content = _make_explorer7(desktop, location)
    try:                                   # (the external drive may still be waking up: no location yet)
        title, icon = content.title_text(), content.title_icon()
    except AttributeError:
        title, icon = getattr(location, "name", None) or "Computer", std(QStyle.SP_DirOpenIcon)
    frame = AeroWindow(desktop, title, content, icon, size=(820, 560))
    content.frame = frame
    desktop.open_window(frame)
    sound.play("navigate")
    return frame


def install():
    """Every 'explorer.launch' in the XP code opens the Windows 7 Explorer."""
    import claudexp.explorer as pkg
    win = _window()
    pkg.launch = launch
    win.launch = launch
    # the search box needs the proxy to honour a name filter as well as XP's hidden-file rule
    proxy = win.FileProxy
    if not getattr(proxy, "_seven", False):
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
        proxy._seven = True
