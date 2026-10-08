"""Windows Explorer: My Computer, folders on C: and E:, and the Recycle Bin."""
import shutil
from pathlib import Path

from PySide6.QtCore import QDir, QSize, QSortFilterProxyModel, Qt, QTimer
from PySide6.QtGui import QAction, QColor, QFont, QIcon, QKeySequence
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QComboBox, QFileIconProvider, QFileSystemModel,
                               QHBoxLayout, QHeaderView, QLabel, QListView, QListWidget, QListWidgetItem, QMenu,
                               QMenuBar, QPushButton, QScrollArea, QStackedWidget, QStyle, QToolBar, QToolButton,
                               QTreeView, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget)
from shiboken6 import isValid

from .. import sound
from ..wm import XPWindow
from . import vfs
from .dialogs import date_2001, msgbox, properties, short_date_2001, size_text
from .viewers import open_file

MY_COMPUTER, RECYCLE_BIN = "mycomputer", "recycle"
EXTERNAL_SLEEP = 10 * 60      # seconds idle before the external drive spins down
_external_last_used = None    # when E: was last opened (None = still asleep since boot)

# What XP called each kind of file.
FILE_TYPES = {
    ".exe": "Application", ".dll": "Application Extension", ".ini": "Configuration Settings",
    ".txt": "Text Document", ".log": "Text Document", ".jpg": "JPEG Image", ".jpeg": "JPEG Image",
    ".gif": "GIF Image", ".png": "PNG Image", ".bmp": "Bitmap Image", ".wav": "Wave Sound",
    ".mp3": "MP3 Format Sound", ".htm": "HTML Document", ".html": "HTML Document", ".bat": "MS-DOS Batch File",
    ".sys": "System file", ".ttf": "TrueType Font file", ".json": "JSON File", ".zip": "Compressed (zipped) Folder",
    ".doc": "Microsoft Word Document", ".pdf": "Adobe Acrobat Document", ".mid": "MIDI Sequence",
}


def xp_type(path, is_dir):
    if is_dir:
        return "File Folder"
    ext = Path(path).suffix.lower()
    return FILE_TYPES.get(ext, f"{ext[1:].upper()} File" if ext else "File")


def xp_size(n):
    """Explorer's Size column: whole KB, rounded up."""
    return f"{max(1, -(-n // 1024)):,} KB" if n else "0 KB"

STYLE = """
QMenuBar { background: #ECE9D8; font-family: Tahoma; font-size: 11px; }
QMenuBar::item { padding: 3px 7px; background: transparent; }
QMenuBar::item:selected { background: #316AC5; color: white; }
QMenu { background: white; border: 1px solid #ACA899; font-family: Tahoma; font-size: 11px; }
QMenu::item { padding: 4px 24px 4px 20px; }
QMenu::item:selected { background: #316AC5; color: white; }
QToolBar { background: #ECE9D8; border: none; border-bottom: 1px solid #ACA899; spacing: 2px; padding: 1px; }
QToolButton { font-family: Tahoma; font-size: 11px; padding: 2px 5px; border: 1px solid transparent; }
QToolButton:hover { border: 1px solid #ACA899; background: #F4F2E8; }
QWidget#address { background: #ECE9D8; border-bottom: 1px solid #ACA899; }
QListView, QTreeView, QListWidget, QTreeWidget { background: white; border: none; font-family: Tahoma; font-size: 11px; }
QLabel#statusbar { background: #ECE9D8; border-top: 1px solid #ACA899; padding: 2px 6px; font-family: Tahoma; font-size: 11px; }
QWidget#taskpane { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #7BA2E7, stop:1 #6375D6); }
QLabel#taskhead { color: #215DC6; font-family: Tahoma; font-size: 11px; font-weight: bold; padding: 4px 8px;
                  background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #FFFFFF, stop:1 #C6D3F7);
                  border-top-left-radius: 4px; border-top-right-radius: 4px; }
QWidget#taskbox { background: #D6DFF7; border: 1px solid #FFFFFF; border-top: none; }
QPushButton#tasklink { color: #215DC6; font-family: Tahoma; font-size: 11px; text-align: left; border: none;
                       background: transparent; padding: 2px 4px; }
QPushButton#tasklink:hover { color: #428EFF; text-decoration: underline; }
QLabel#taskdetails { color: black; font-family: Tahoma; font-size: 11px; padding: 4px 8px; }
QLabel#grouphead { color: #3D5A9C; font-family: Tahoma; font-size: 12px; font-weight: bold; padding: 6px 4px 2px 4px; }
"""


def std(which):
    return QApplication.style().standardIcon(which)


def drive_icon(d):
    return std({"hdd": QStyle.SP_DriveHDIcon, "external": QStyle.SP_DriveHDIcon, "cd": QStyle.SP_DriveCDIcon,
                "floppy": QStyle.SP_DriveFDIcon}[d.kind])


# ---- file model: hides internal files, shows dates in 2001, protects system folders ------------------------

class FileProxy(QSortFilterProxyModel):
    def __init__(self, model):
        super().__init__()
        self.setSourceModel(model)
        self.fs = model

    def filterAcceptsRow(self, row, parent):
        index = self.fs.index(row, 0, parent)
        return not vfs.hidden(self.fs.filePath(index))

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and index.column() in (1, 2, 3):
            src = self.mapToSource(index)
            info = self.fs.fileInfo(src)
            if index.column() == 1:
                return "" if info.isDir() else xp_size(info.size())
            if index.column() == 2:
                return xp_type(info.fileName(), info.isDir())
            return short_date_2001(info.lastModified().toSecsSinceEpoch())
        return super().data(index, role)

    def flags(self, index):
        flags = super().flags(index)
        if index.isValid() and vfs.protected(self.fs.filePath(self.mapToSource(index))):
            flags &= ~Qt.ItemIsEditable
        return flags

    def lessThan(self, left, right):
        # Folders first, like Explorer.
        a, b = self.fs.isDir(left), self.fs.isDir(right)
        if a != b:
            return a
        return super().lessThan(left, right)


class DropMixin:
    """Files dragged in from the real Windows are always copied (never moved) into the folder shown."""

    def setup_drops(self, explorer):
        self.explorer = explorer
        self.setAcceptDrops(True)
        self.viewport().setAcceptDrops(True)
        self.setDragEnabled(False)
        self.setDropIndicatorShown(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls() and self.explorer.current_folder() is not None:
            event.setDropAction(Qt.CopyAction)
            event.accept()

    dragMoveEvent = dragEnterEvent

    def dropEvent(self, event):
        paths = [Path(u.toLocalFile()) for u in event.mimeData().urls() if u.isLocalFile()]
        if paths:
            event.setDropAction(Qt.CopyAction)
            event.accept()
            self.explorer.paste_paths(paths, move=False)


class IconView(DropMixin, QListView):
    pass


class DetailView(DropMixin, QTreeView):
    pass


# ---- the blue task pane ------------------------------------------------------------------------------------

class TaskPane(QScrollArea):
    def __init__(self):
        super().__init__()
        self.setFixedWidth(200)
        self.setWidgetResizable(True)
        self.setFrameShape(QScrollArea.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.inner = QWidget()
        self.inner.setObjectName("taskpane")
        self.inner.setAttribute(Qt.WA_StyledBackground, True)
        self.layout_ = QVBoxLayout(self.inner)
        self.layout_.setContentsMargins(10, 10, 10, 10)
        self.layout_.setSpacing(12)
        self.setWidget(self.inner)

    def set_sections(self, sections, details):
        while self.layout_.count():
            item = self.layout_.takeAt(0)
            if item.widget():
                item.widget().hide()          # hide now so old boxes never flash on screen
                item.widget().deleteLater()
        for title, links in sections:
            self.layout_.addWidget(self._box(title, links)[0])
        if details:
            box, inner = self._box("Details", [])
            label = QLabel(details)
            label.setObjectName("taskdetails")
            label.setWordWrap(True)
            inner.addWidget(label)
            self.layout_.addWidget(box)
        self.layout_.addStretch()

    def _box(self, title, links):
        outer = QWidget()
        v = QVBoxLayout(outer)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)
        head = QLabel(title)
        head.setObjectName("taskhead")
        v.addWidget(head)
        box = QWidget()
        box.setObjectName("taskbox")
        box.setAttribute(Qt.WA_StyledBackground, True)
        bv = QVBoxLayout(box)
        bv.setContentsMargins(4, 6, 4, 6)
        bv.setSpacing(1)
        for text, icon, slot in links:
            b = QPushButton(text)
            b.setObjectName("tasklink")
            b.setCursor(Qt.PointingHandCursor)
            if icon is not None:
                b.setIcon(icon)
            b.clicked.connect(slot)
            bv.addWidget(b)
        v.addWidget(box)
        return outer, bv


# ---- the Explorer window -------------------------------------------------------------------------------------

class Explorer(QWidget):
    clipboard = {"paths": [], "move": False}   # shared by all Explorer windows

    def __init__(self, desktop, location):
        super().__init__()
        self.desktop = desktop
        self.frame = None
        self.location = None
        self.back_stack, self.fwd_stack = [], []
        self.view_mode = "icons"
        self.setStyleSheet(STYLE)
        vfs.setup_c()
        self.icons = QFileIconProvider()

        # ---- menus ----
        bar = QMenuBar()
        file_menu = bar.addMenu("&File")
        new_menu = file_menu.addMenu("Ne&w")
        new_menu.addAction(std(QStyle.SP_DirIcon), "&Folder", self.new_folder)
        new_menu.addAction(std(QStyle.SP_FileIcon), "Text Document", self.new_text_file)
        file_menu.addSeparator()
        file_menu.addAction("&Delete", self.delete_selected)
        file_menu.addAction("Rena&me", self.rename_selected)
        file_menu.addAction("P&roperties", self.properties_selected)
        file_menu.addSeparator()
        file_menu.addAction("&Close", lambda: self.frame.request_close() if self.frame else self.close())
        edit_menu = bar.addMenu("&Edit")
        edit_menu.addAction("Cu&t", lambda: self.copy_selected(move=True), QKeySequence.Cut)
        edit_menu.addAction("&Copy", lambda: self.copy_selected(move=False), QKeySequence.Copy)
        edit_menu.addAction("&Paste", self.paste, QKeySequence.Paste)
        edit_menu.addSeparator()
        edit_menu.addAction("Select &All", lambda: self.active_view().selectAll(), QKeySequence.SelectAll)
        view_menu = bar.addMenu("&View")
        for label, mode in (("Ic&ons", "icons"), ("&List", "list"), ("&Details", "details")):
            view_menu.addAction(label, lambda m=mode: self.set_view(m))
        view_menu.addSeparator()
        view_menu.addAction("&Refresh", self.refresh, QKeySequence("F5"))
        bar.addMenu("F&avorites").addAction("(empty)").setEnabled(False)
        tools = bar.addMenu("&Tools")
        tools.addAction("Map &Network Drive...", lambda: self._not_here("Map Network Drive"))
        tools.addAction("Folder &Options...", lambda: self._not_here("Folder Options"))
        help_menu = bar.addMenu("&Help")
        help_menu.addAction("About Windows", self._about)
        bar.triggered.connect(lambda _a: sound.play("menu"))

        # ---- toolbar ----
        tb = QToolBar()
        tb.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.back_act = tb.addAction(std(QStyle.SP_ArrowBack), "Back", self.back)
        self.fwd_act = tb.addAction(std(QStyle.SP_ArrowForward), "", self.forward)
        self.up_act = tb.addAction(std(QStyle.SP_FileDialogToParent), "", self.up)
        tb.addSeparator()
        tb.addAction(std(QStyle.SP_FileDialogContentsView), "Search", lambda: self._not_here("Search Companion"))
        tb.addAction(std(QStyle.SP_DirOpenIcon), "Folders", lambda: self._not_here("the Folders bar"))
        tb.addSeparator()
        views = QToolButton()
        views.setIcon(std(QStyle.SP_FileDialogListView))
        views.setPopupMode(QToolButton.InstantPopup)
        vmenu = QMenu(views)
        for label, mode in (("Icons", "icons"), ("List", "list"), ("Details", "details")):
            vmenu.addAction(label, lambda m=mode: self.set_view(m))
        views.setMenu(vmenu)
        tb.addWidget(views)

        # ---- address bar ----
        addr = QWidget()
        addr.setObjectName("address")
        addr.setAttribute(Qt.WA_StyledBackground, True)
        arow = QHBoxLayout(addr)
        arow.setContentsMargins(4, 2, 4, 2)
        lab = QLabel("Address")
        lab.setStyleSheet("color: #808080; font-family: Tahoma; font-size: 11px;")
        arow.addWidget(lab)
        self.address = QComboBox()
        self.address.setEditable(True)
        self.address.setStyleSheet("QComboBox { background: white; font-family: Tahoma; font-size: 11px; }")
        self.address.lineEdit().returnPressed.connect(lambda: self.go_address(self.address.currentText()))
        arow.addWidget(self.address, 1)
        go = QPushButton("Go")
        go.setIcon(std(QStyle.SP_ArrowRight))
        go.clicked.connect(lambda: self.go_address(self.address.currentText()))
        arow.addWidget(go)

        # ---- views ----
        self.fs = QFileSystemModel(self)
        self.fs.setReadOnly(False)
        self.fs.setFilter(QDir.AllEntries | QDir.NoDotAndDotDot | QDir.System)
        self.fs.setRootPath(str(vfs.DRIVE_C.parent))
        self.proxy = FileProxy(self.fs)
        self.proxy.setDynamicSortFilter(True)
        self.proxy.sort(0)

        self.icon_view = IconView()
        self.icon_view.setModel(self.proxy)
        self.icon_view.setup_drops(self)
        self.detail_view = DetailView()
        self.detail_view.setModel(self.proxy)
        self.detail_view.setup_drops(self)
        self.detail_view.setRootIsDecorated(False)
        self.detail_view.setSortingEnabled(True)
        self.detail_view.sortByColumn(0, Qt.AscendingOrder)
        self.detail_view.header().setSectionResizeMode(0, QHeaderView.Interactive)
        self.detail_view.setColumnWidth(0, 220)
        for view in (self.icon_view, self.detail_view):
            view.setSelectionMode(QAbstractItemView.ExtendedSelection)
            view.setEditTriggers(QAbstractItemView.EditKeyPressed | QAbstractItemView.SelectedClicked)
            view.activated.connect(self._activated)
            view.setContextMenuPolicy(Qt.CustomContextMenu)
            view.customContextMenuRequested.connect(lambda pos, v=view: self._context_menu(v, pos))
            view.selectionModel().selectionChanged.connect(lambda *_: self._update_tasks())
        self.mycomputer = self._build_mycomputer()
        self.recycle_view = QTreeWidget()
        self.recycle_view.setHeaderLabels(["Name", "Original Location", "Date Deleted", "Size"])
        self.recycle_view.setRootIsDecorated(False)
        self.recycle_view.setColumnWidth(0, 180)
        self.recycle_view.setColumnWidth(1, 220)
        self.recycle_view.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.recycle_view.itemSelectionChanged.connect(self._update_tasks)
        self.recycle_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.recycle_view.customContextMenuRequested.connect(self._recycle_menu)

        self.stack = QStackedWidget()
        for w in (self.mycomputer, self.icon_view, self.detail_view, self.recycle_view):
            self.stack.addWidget(w)
        self.tasks = TaskPane()
        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        body.addWidget(self.tasks)
        body.addWidget(self.stack, 1)
        self.status = QLabel()
        self.status.setObjectName("statusbar")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.setMenuBar(bar)
        root.addWidget(tb)
        root.addWidget(addr)
        root.addLayout(body, 1)
        root.addWidget(self.status)

        for key, slot in ((QKeySequence.Delete, self.delete_selected), (QKeySequence("F2"), self.rename_selected),
                          (QKeySequence("Backspace"), self.up), (QKeySequence("Alt+Return"), self.properties_selected)):
            act = QAction(self)
            act.setShortcut(key)
            act.setShortcutContext(Qt.WidgetWithChildrenShortcut)
            act.triggered.connect(slot)
            self.addAction(act)
        self.navigate(location, remember=False)

    # ---- My Computer view -----------------------------------------------------------------------------
    def _build_mycomputer(self):
        area = QScrollArea()
        area.setWidgetResizable(True)
        area.setFrameShape(QScrollArea.NoFrame)
        inner = QWidget()
        inner.setStyleSheet("background: white;")
        v = QVBoxLayout(inner)
        v.setContentsMargins(10, 6, 10, 6)
        self.mc_lists = []
        from ..user import user_name
        groups = [
            ("Files Stored on This Computer", [("Shared Documents", std(QStyle.SP_DirIcon), vfs.shared_documents()),
                                              (f"{user_name()}'s Documents", std(QStyle.SP_DirIcon), vfs.my_documents())]),
            ("Hard Disk Drives", [(d.name, drive_icon(d), d) for d in vfs.drives() if d.kind in ("hdd", "external")]),
            ("Devices with Removable Storage", [(d.name, drive_icon(d), d) for d in vfs.drives()
                                               if d.kind in ("floppy", "cd")]),
        ]
        for title, items in groups:
            head = QLabel(title)
            head.setObjectName("grouphead")
            v.addWidget(head)
            line = QWidget()
            line.setFixedHeight(1)
            line.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7EA0D8, stop:1 white);")
            v.addWidget(line)
            lst = QListWidget()
            lst.setViewMode(QListWidget.IconMode)
            lst.setIconSize(QSize(32, 32))
            lst.setGridSize(QSize(130, 70))
            lst.setMovement(QListWidget.Static)
            lst.setResizeMode(QListWidget.Adjust)
            lst.setWordWrap(True)
            lst.setFixedHeight(80)
            lst.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            for name, icon, target in items:
                it = QListWidgetItem(icon, name)
                it.setData(Qt.UserRole, target)
                lst.addItem(it)
            lst.itemActivated.connect(lambda it: self._mc_open(it.data(Qt.UserRole)))
            lst.itemSelectionChanged.connect(self._update_tasks)
            lst.setContextMenuPolicy(Qt.CustomContextMenu)
            lst.customContextMenuRequested.connect(lambda pos, l=lst: self._mc_menu(l, pos))
            v.addWidget(lst)
            self.mc_lists.append(lst)
        v.addStretch()
        area.setWidget(inner)
        return area

    def _mc_selected(self):
        for lst in self.mc_lists:
            items = lst.selectedItems()
            if items:
                return items[0].data(Qt.UserRole)
        return None

    def _mc_open(self, target):
        if isinstance(target, vfs.Drive):
            self.open_drive(target)
        else:
            self.navigate(Path(target))

    def _mc_menu(self, lst, pos):
        item = lst.itemAt(pos)
        if item is None:
            return
        target = item.data(Qt.UserRole)
        menu = QMenu(self)
        menu.addAction("&Open", lambda: self._mc_open(target))
        menu.addAction("&Explore", lambda: self._mc_open(target))
        menu.addSeparator()
        menu.addAction("P&roperties", lambda: self.drive_properties(target) if isinstance(target, vfs.Drive)
                       else self.file_properties(Path(target)))
        menu.exec(lst.viewport().mapToGlobal(pos))

    def open_drive(self, d):
        import random
        if d.kind == "floppy":
            QApplication.setOverrideCursor(Qt.BusyCursor)
            sound.play_clip(random.choice(["floppydrive_reading1.mp3", "floppydrive_reading2.mp3"]), 3500)

            def fail():
                QApplication.restoreOverrideCursor()
                msgbox(self.desktop, "Windows", f"{d.letter}:\\ is not accessible.\n\nThe device is not ready.",
                       "error", ("Retry", "Cancel"), lambda b: b == "Retry" and self.open_drive(d))

            QTimer.singleShot(3500, fail)   # the floppy drive grinds for a bit first
        elif d.kind == "cd":
            QApplication.setOverrideCursor(Qt.BusyCursor)
            sound.play_clip(random.choice(["cdrom_startup1.mp3", "cdrom_startup2.mp3"]), 4000)

            def empty():
                QApplication.restoreOverrideCursor()
                msgbox(self.desktop, "Insert Disk", f"Please insert a disk into drive {d.letter}:.", "info",
                       ("Cancel", "Try Again"), lambda b: b == "Try Again" and self.open_drive(d))

            QTimer.singleShot(4000, empty)  # the CD spins up and finds nothing
        else:
            self.navigate(d.root)

    # ---- navigation -------------------------------------------------------------------------------------
    def current_folder(self):
        return self.location if isinstance(self.location, Path) else None

    def navigate(self, location, remember=True, awake=False):
        if isinstance(location, str) and location not in (MY_COMPUTER, RECYCLE_BIN):
            location = Path(location)
        if isinstance(location, Path) and not awake and self._wake_external(location, remember):
            return
        if isinstance(location, Path):
            if location.is_file():
                open_file(self.desktop, location)
                return
            if not location.is_dir():
                msgbox(self.desktop, "Windows", f"Windows cannot find '{vfs.to_virtual(location) or location}'.",
                       "error")
                return
        if remember and self.location is not None and location != self.location:
            self.back_stack.append(self.location)
            self.fwd_stack.clear()
        self.location = location
        if location == MY_COMPUTER:
            self.stack.setCurrentWidget(self.mycomputer)
        elif location == RECYCLE_BIN:
            self._fill_recycle()
            self.stack.setCurrentWidget(self.recycle_view)
        else:
            src = self.fs.index(str(location))
            root = self.proxy.mapFromSource(src)
            for view in (self.icon_view, self.detail_view):
                view.setRootIndex(root)
            self.set_view(self.view_mode)
        self.address.setEditText(self.address_text())
        self.back_act.setEnabled(bool(self.back_stack))
        self.fwd_act.setEnabled(bool(self.fwd_stack))
        self.up_act.setEnabled(location != MY_COMPUTER)
        if self.frame is not None:
            self.frame.set_title(self.title_text())
            self.frame.icon = self.title_icon()
            self.frame.update()
        self._update_tasks()

    def _wake_external(self, location, remember):
        """Opening E: after it has been idle: it spins up (sound + busy cursor) before showing files."""
        global _external_last_used
        import random
        import time
        ext = vfs.local_storage().resolve()
        try:
            inside = location.resolve() == ext or ext in location.resolve().parents
        except OSError:
            inside = False
        if not inside:
            return False
        now = time.monotonic()
        asleep = _external_last_used is None or now - _external_last_used > EXTERNAL_SLEEP
        _external_last_used = now
        if not asleep:
            return False
        sound.play_clip(random.choice(["externalHD_start1.mp3", "externalHD_start2.mp3"]), 5000)
        QApplication.setOverrideCursor(Qt.BusyCursor)

        def ready():
            QApplication.restoreOverrideCursor()
            if isValid(self):
                self.navigate(location, remember, awake=True)

        QTimer.singleShot(2500, ready)
        return True

    def address_text(self):
        if self.location == MY_COMPUTER:
            return "My Computer"
        if self.location == RECYCLE_BIN:
            return "Recycle Bin"
        return vfs.to_virtual(self.location) or str(self.location)

    def title_text(self):
        if self.location == MY_COMPUTER:
            return "My Computer"
        if self.location == RECYCLE_BIN:
            return "Recycle Bin"
        for d in vfs.drives():
            if d.root is not None and self.location.resolve() == d.root.resolve():
                return d.name
        if self.location.resolve() == vfs.my_documents().resolve():
            return "My Documents"
        return self.location.name

    def title_icon(self):
        if self.location == MY_COMPUTER:
            return std(QStyle.SP_ComputerIcon)
        if self.location == RECYCLE_BIN:
            return std(QStyle.SP_TrashIcon)
        for d in vfs.drives():
            if d.root is not None and self.location.resolve() == d.root.resolve():
                return drive_icon(d)
        return std(QStyle.SP_DirOpenIcon)

    def go_address(self, text):
        text = text.strip()
        low = text.lower()
        if low in ("my computer", ""):
            self.navigate(MY_COMPUTER)
        elif low == "recycle bin":
            self.navigate(RECYCLE_BIN)
        elif low in ("my documents",):
            self.navigate(vfs.my_documents())
        elif len(text) >= 2 and text[1] == ":":
            d = vfs.drive(text[0])
            if d is not None and d.kind in ("floppy", "cd"):
                self.open_drive(d)
                return
            real = vfs.to_real(text)
            if real is None or not real.exists():
                msgbox(self.desktop, "Windows", f"Windows cannot find '{text}'. Check the spelling and try again.",
                       "error")
            else:
                self.navigate(real)
        else:
            msgbox(self.desktop, "Windows", f"Windows cannot find '{text}'. Check the spelling and try again.",
                   "error")

    def back(self):
        if self.back_stack:
            self.fwd_stack.append(self.location)
            self.navigate(self.back_stack.pop(), remember=False)

    def forward(self):
        if self.fwd_stack:
            self.back_stack.append(self.location)
            self.navigate(self.fwd_stack.pop(), remember=False)

    def up(self):
        loc = self.location
        if loc in (MY_COMPUTER, RECYCLE_BIN):
            if loc == RECYCLE_BIN:
                self.navigate(MY_COMPUTER)
            return
        for d in vfs.drives():
            if d.root is not None and loc.resolve() == d.root.resolve():
                self.navigate(MY_COMPUTER)
                return
        self.navigate(loc.parent)

    def refresh(self):
        if self.location == RECYCLE_BIN:
            self._fill_recycle()
        self._update_tasks()

    # ---- views -------------------------------------------------------------------------------------------
    def set_view(self, mode):
        self.view_mode = mode
        if self.current_folder() is None:
            return
        if mode == "details":
            self.stack.setCurrentWidget(self.detail_view)
            return
        v = self.icon_view
        if mode == "icons":
            v.setViewMode(QListView.IconMode)
            v.setIconSize(QSize(32, 32))
            v.setGridSize(QSize(90, 72))
            v.setWordWrap(True)
            v.setFlow(QListView.LeftToRight)
            v.setWrapping(True)
        else:
            v.setViewMode(QListView.ListMode)
            v.setIconSize(QSize(16, 16))
            v.setGridSize(QSize())
            v.setFlow(QListView.TopToBottom)
            v.setWrapping(True)
        v.setResizeMode(QListView.Adjust)
        v.setMovement(QListView.Static)
        self.stack.setCurrentWidget(v)

    def active_view(self):
        return self.detail_view if self.view_mode == "details" else self.icon_view

    def selected_paths(self):
        if self.current_folder() is None:
            return []
        view = self.active_view()
        rows = view.selectionModel().selectedRows(0) if view is self.detail_view else view.selectionModel().selectedIndexes()
        paths = [Path(self.fs.filePath(self.proxy.mapToSource(i))) for i in rows if i.column() == 0]
        return [p for p in paths if p.exists()]   # a just-deleted file can linger in the selection briefly

    def _activated(self, index):
        path = Path(self.fs.filePath(self.proxy.mapToSource(index)))
        if path.is_dir():
            self.navigate(path)
        else:
            open_file(self.desktop, path)

    # ---- task pane and status bar ---------------------------------------------------------------------------
    def _update_tasks(self):
        loc = self.location
        my_docs = ("My Documents", std(QStyle.SP_DirIcon), lambda: self.navigate(vfs.my_documents()))
        shared = ("Shared Documents", std(QStyle.SP_DirIcon), lambda: self.navigate(vfs.shared_documents()))
        my_comp = ("My Computer", std(QStyle.SP_ComputerIcon), lambda: self.navigate(MY_COMPUTER))
        network = ("My Network Places", std(QStyle.SP_DriveNetIcon), lambda: self._not_here("My Network Places"))
        control = ("Control Panel", std(QStyle.SP_DesktopIcon), lambda: self._not_here("Control Panel"))
        if loc == MY_COMPUTER:
            target = self._mc_selected()
            details = "<b>My Computer</b><br>System Folder"
            if isinstance(target, vfs.Drive):
                details = f"<b>{target.name}</b><br>{target.label}"
                usage = target.usage()
                if usage:
                    total, free = usage
                    details += (f"<br><br>File System: NTFS<br>Free Space: {size_text(free)}"
                                f"<br>Total Size: {size_text(total)}")
            self.tasks.set_sections([
                ("System Tasks", [("View system information", std(QStyle.SP_ComputerIcon), self._system_info),
                                  ("Add or remove programs", std(QStyle.SP_DialogApplyButton),
                                   lambda: self._not_here("Add or Remove Programs")),
                                  ("Change a setting", std(QStyle.SP_DesktopIcon), lambda: self._not_here("Control Panel"))]),
                ("Other Places", [network, my_docs, shared, control]),
            ], details)
            n = sum(lst.count() for lst in self.mc_lists)
            self.status.setText(f"{n} objects")
        elif loc == RECYCLE_BIN:
            sel = self.recycle_view.selectedItems()
            self.tasks.set_sections([
                ("Recycle Bin Tasks", [("Empty the Recycle Bin", std(QStyle.SP_TrashIcon), self.empty_recycle),
                                       ("Restore this item" if len(sel) == 1 else "Restore all items",
                                        std(QStyle.SP_BrowserReload), self.restore_selected)]),
                ("Other Places", [my_docs, my_comp, network]),
            ], "<b>Recycle Bin</b><br>System Folder")
            self.status.setText(f"{self.recycle_view.topLevelItemCount()} objects")
        else:
            sel = self.selected_paths()
            file_tasks = [("Make a new folder", std(QStyle.SP_FileDialogNewFolder), self.new_folder)]
            if sel:
                what = "folder" if sel[0].is_dir() else "file"
                if len(sel) > 1:
                    what = "selected items"
                if len(sel) == 1:
                    file_tasks.append((f"Rename this {what}", std(QStyle.SP_FileDialogDetailedView), self.rename_selected))
                file_tasks.append((f"Copy this {what}", std(QStyle.SP_FileLinkIcon), lambda: self.copy_selected(False)))
                file_tasks.append((f"Delete this {what}", std(QStyle.SP_TrashIcon), self.delete_selected))
            parent = loc.parent
            places = []
            if vfs.to_virtual(parent) and loc.resolve() not in [d.root.resolve() for d in vfs.drives() if d.root]:
                places.append((self._name_of(parent), std(QStyle.SP_DirIcon), lambda: self.navigate(parent)))
            places += [my_docs, shared, my_comp, network]
            if sel and len(sel) == 1:
                p = sel[0]
                st = p.stat()
                details = f"<b>{p.name}</b><br>{'File Folder' if p.is_dir() else self._type_of(p)}"
                details += f"<br>Date Modified: {date_2001(st.st_mtime)}"
                if p.is_file():
                    details += f"<br>Size: {size_text(st.st_size)}"
            elif sel:
                details = f"{len(sel)} items selected."
            else:
                details = f"<b>{self.title_text()}</b><br>File Folder"
            self.tasks.set_sections([("File and Folder Tasks", file_tasks), ("Other Places", places)], details)
            try:
                count = sum(1 for p in loc.iterdir() if not vfs.hidden(p))
            except OSError:
                count = 0
            d = next((d for d in vfs.drives() if d.root is not None and
                      (loc.resolve() == d.root.resolve() or d.root.resolve() in loc.resolve().parents)), None)
            free = f" (Disk free space: {size_text(d.usage()[1])})" if d and d.usage() else ""
            self.status.setText(f"{len(sel)} objects selected" if sel else f"{count} objects{free}")

    def _name_of(self, path):
        for d in vfs.drives():
            if d.root is not None and path.resolve() == d.root.resolve():
                return d.name
        return path.name

    def _type_of(self, path):
        return xp_type(path, path.is_dir())

    # ---- file operations ----------------------------------------------------------------------------------------
    def _unique(self, folder, name):
        target = folder / name
        if not target.exists():
            return target
        stem, suffix = Path(name).stem, Path(name).suffix
        n = 2
        while (folder / f"{stem} ({n}){suffix}").exists():
            n += 1
        return folder / f"{stem} ({n}){suffix}"

    def _edit_new(self, path):
        def start():
            idx = self.proxy.mapFromSource(self.fs.index(str(path)))
            if idx.isValid():
                view = self.active_view()
                view.setCurrentIndex(idx)
                view.edit(idx)
        QTimer.singleShot(250, start)

    def new_folder(self):
        folder = self.current_folder()
        if folder is None:
            return
        target = self._unique(folder, "New Folder")
        target.mkdir()
        self._edit_new(target)

    def new_text_file(self):
        folder = self.current_folder()
        if folder is None:
            return
        target = self._unique(folder, "New Text Document.txt")
        target.write_text("", encoding="utf-8")
        self._edit_new(target)

    def rename_selected(self):
        view = self.active_view()
        idx = view.currentIndex()
        if self.current_folder() is None or not idx.isValid():
            return
        if not (self.proxy.flags(idx) & Qt.ItemIsEditable):
            msgbox(self.desktop, "Error Renaming File or Folder",
                   f"Cannot rename {Path(self.fs.filePath(self.proxy.mapToSource(idx))).name}: Access is denied.", "error")
            return
        view.edit(idx.siblingAtColumn(0))

    def delete_selected(self):
        if self.location == RECYCLE_BIN:
            return
        paths = self.selected_paths()
        if not paths:
            return
        locked = [p for p in paths if vfs.protected(p)]
        if locked:
            msgbox(self.desktop, "Error Deleting File or Folder", f"Cannot delete {locked[0].name}: Access is denied.\n\n"
                   "Make sure the disk is not full or write-protected and that the file is not currently in use.", "error")
            return
        text = (f"Are you sure you want to send '{paths[0].name}' to the Recycle Bin?" if len(paths) == 1
                else f"Are you sure you want to send these {len(paths)} items to the Recycle Bin?")
        title = "Confirm Folder Delete" if len(paths) == 1 and paths[0].is_dir() else (
            "Confirm File Delete" if len(paths) == 1 else "Confirm Multiple File Delete")

        def answer(button):
            if button == "Yes":
                for p in paths:
                    try:
                        vfs.recycle(p)
                    except OSError as e:
                        msgbox(self.desktop, "Error Deleting File or Folder", f"Cannot delete {p.name}: {e.strerror}", "error")
                        break
                sound.play("navigate")
                self._update_tasks()

        msgbox(self.desktop, title, text, "question", ("Yes", "No"), answer,
               window_icon=std(QStyle.SP_TrashIcon))

    def copy_selected(self, move=False):
        paths = self.selected_paths()
        if paths:
            if move and any(vfs.protected(p) for p in paths):
                msgbox(self.desktop, "Error Moving File or Folder", "Access is denied.", "error")
                return
            Explorer.clipboard = {"paths": paths, "move": move}

    def paste(self):
        clip = Explorer.clipboard
        if clip["paths"]:
            self.paste_paths(clip["paths"], clip["move"])
            if clip["move"]:
                Explorer.clipboard = {"paths": [], "move": False}

    def paste_paths(self, paths, move=False):
        folder = self.current_folder()
        if folder is None:
            return
        for src in paths:
            if not src.exists():
                continue
            if src.is_dir() and (folder.resolve() == src.resolve() or src.resolve() in folder.resolve().parents):
                msgbox(self.desktop, "Error Copying File or Folder",
                       f"Cannot copy {src.name}: The destination folder is a subfolder of the source folder.", "error")
                continue
            target = folder / src.name
            if target.exists():
                if move and target.resolve() == src.resolve():
                    continue
                target = self._unique(folder, f"Copy of {src.name}")
            try:
                if move:
                    shutil.move(str(src), str(target))
                elif src.is_dir():
                    shutil.copytree(src, target)
                else:
                    shutil.copy2(src, target)
            except OSError as e:
                msgbox(self.desktop, "Error Copying File or Folder", f"Cannot copy {src.name}: {e.strerror}", "error")
                break
        self._update_tasks()

    # ---- properties -------------------------------------------------------------------------------------------------
    def properties_selected(self):
        if self.location == MY_COMPUTER:
            target = self._mc_selected()
            if isinstance(target, vfs.Drive):
                self.drive_properties(target)
            else:
                self._system_info()
            return
        paths = self.selected_paths() or ([self.current_folder()] if self.current_folder() else [])
        if paths:
            self.file_properties(paths[0])

    def drive_properties(self, d):
        usage = d.usage()
        if usage is None:
            self.open_drive(d)
            return
        total, free = usage
        properties(self.desktop, d.name, [("Type:", d.label if d.kind != "external" else "External Disk"),
                                          ("File system:", "NTFS"), ("-", "")],
                   usage=(total - free, free), icon=drive_icon(d))

    def file_properties(self, path):
        st = path.stat()
        if path.is_dir():
            files = [f for f in path.rglob("*") if f.is_file() and not vfs.hidden(f)]
            folders = sum(1 for f in path.rglob("*") if f.is_dir())
            size = sum(f.stat().st_size for f in files)
            rows = [("Type:", "File Folder"), ("Location:", vfs.to_virtual(path.parent) or ""),
                    ("Size:", f"{size_text(size)} ({size:,} bytes)"),
                    ("Contains:", f"{len(files)} Files, {folders} Folders"), ("-", ""),
                    ("Created:", date_2001(st.st_ctime))]
            icon = std(QStyle.SP_DirIcon)
        else:
            rows = [("Type of file:", self._type_of(path)), ("Location:", vfs.to_virtual(path.parent) or ""),
                    ("Size:", f"{size_text(st.st_size)} ({st.st_size:,} bytes)"), ("-", ""),
                    ("Created:", date_2001(st.st_ctime)), ("Modified:", date_2001(st.st_mtime)),
                    ("Accessed:", date_2001(st.st_atime))]
            icon = self.icons.icon(self.fs.fileInfo(self.fs.index(str(path))))
        properties(self.desktop, path.name, rows, icon=icon)

    def _system_info(self):
        from ..user import user_name
        properties(self.desktop, "System", [
            ("System:", "Microsoft Windows XP"), ("", "Home Edition"), ("", "Version 2002"), ("-", ""),
            ("Registered to:", user_name()), ("", "55274-OEM-0011903-00102"), ("-", ""),
            ("Computer:", "Intel(R) Pentium(R) III processor"), ("", "866 MHz"), ("", "256 MB of RAM")],
            icon=std(QStyle.SP_ComputerIcon))

    # ---- context menus --------------------------------------------------------------------------------------------
    def _context_menu(self, view, pos):
        idx = view.indexAt(pos)
        menu = QMenu(self)
        if idx.isValid():
            if not view.selectionModel().isSelected(idx):
                view.setCurrentIndex(idx)
            path = Path(self.fs.filePath(self.proxy.mapToSource(idx)))
            menu.addAction("&Open", lambda: self._activated(idx)).setFont(QFont("Tahoma", 8, QFont.Bold))
            menu.addSeparator()
            menu.addAction("Cu&t", lambda: self.copy_selected(True))
            menu.addAction("&Copy", lambda: self.copy_selected(False))
            if path.is_dir() and Explorer.clipboard["paths"]:
                menu.addAction("&Paste", lambda: self._paste_into(path))
            menu.addSeparator()
            menu.addAction("&Delete", self.delete_selected)
            menu.addAction("Rena&me", self.rename_selected)
            menu.addSeparator()
            menu.addAction("P&roperties", lambda: self.file_properties(path))
        else:
            view.clearSelection()
            vm = menu.addMenu("&View")
            for label, mode in (("Ic&ons", "icons"), ("&List", "list"), ("&Details", "details")):
                vm.addAction(label, lambda m=mode: self.set_view(m))
            menu.addAction("R&efresh", self.refresh)
            menu.addSeparator()
            paste = menu.addAction("&Paste", self.paste)
            paste.setEnabled(bool(Explorer.clipboard["paths"]))
            menu.addSeparator()
            nm = menu.addMenu("Ne&w")
            nm.addAction(std(QStyle.SP_DirIcon), "&Folder", self.new_folder)
            nm.addAction(std(QStyle.SP_FileIcon), "Text Document", self.new_text_file)
            menu.addSeparator()
            menu.addAction("P&roperties", lambda: self.file_properties(self.current_folder()))
        menu.exec(view.viewport().mapToGlobal(pos))

    def _paste_into(self, folder):
        old = self.location
        self.location = folder
        try:
            self.paste()
        finally:
            self.location = old

    # ---- Recycle Bin ------------------------------------------------------------------------------------------------
    def _fill_recycle(self):
        self.recycle_view.clear()
        for stored, original, when in sorted(vfs.recycled(), key=lambda r: -r[2]):
            size = sum(f.stat().st_size for f in stored.rglob("*") if f.is_file()) if stored.is_dir() \
                else stored.stat().st_size
            item = QTreeWidgetItem([original.name, vfs.to_virtual(original.parent) or str(original.parent),
                                    short_date_2001(when), xp_size(size)])
            item.setIcon(0, self.icons.icon(self.fs.fileInfo(self.fs.index(str(stored)))) if stored.exists()
                         else std(QStyle.SP_FileIcon))
            item.setData(0, Qt.UserRole, str(stored))
            self.recycle_view.addTopLevelItem(item)
        self._update_tasks()

    def _recycle_menu(self, pos):
        if self.recycle_view.itemAt(pos) is None:
            return
        menu = QMenu(self)
        menu.addAction("R&estore", self.restore_selected)
        menu.exec(self.recycle_view.viewport().mapToGlobal(pos))

    def restore_selected(self):
        items = self.recycle_view.selectedItems() or [self.recycle_view.topLevelItem(i)
                                                      for i in range(self.recycle_view.topLevelItemCount())]
        for item in items:
            vfs.restore(Path(item.data(0, Qt.UserRole)))
        self._fill_recycle()

    def empty_recycle(self):
        n = len(vfs.recycled())
        if not n:
            return

        def answer(button):
            if button == "Yes":
                vfs.empty_recycle_bin()
                sound.play("navigate")
                self._fill_recycle()

        msgbox(self.desktop, "Confirm Multiple File Delete",
               f"Are you sure you want to delete these {n} items?" if n > 1 else
               "Are you sure you want to delete this item?", "question", ("Yes", "No"), answer,
               window_icon=std(QStyle.SP_TrashIcon))

    # ---- misc ---------------------------------------------------------------------------------------------------------
    def _not_here(self, what):
        msgbox(self.desktop, "Windows", f"{what} isn't available on this computer yet.", "info")

    def _about(self):
        msgbox(self.desktop, "About Windows", "Microsoft (R) Windows\nVersion 5.1 (Build 2600.xpclient.010817-1148)\n"
               "Copyright (C) 1981-2001 Microsoft Corporation\n\nThis product is licensed to:\n"
               f"{self.frame.title if self.frame else ''}", "info")


def launch(desktop, location=MY_COMPUTER):
    """Open an Explorer window at My Computer, the Recycle Bin, or a real folder path."""
    content = Explorer(desktop, location)
    frame = XPWindow(desktop, content.title_text(), content, content.title_icon(), size=(760, 520))
    content.frame = frame
    desktop.open_window(frame)
    sound.play("navigate")
    return frame
