"""WinZip: The classic Windows Zip file utility for ClaudeXP."""
import os
import random
import shutil
import tempfile
import time
import zipfile
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, QSize, Qt
from PySide6.QtGui import (QBrush, QColor, QFont, QIcon, QLinearGradient, QPainter,
                          QPen, QPixmap)
from PySide6.QtWidgets import (QAbstractItemView, QCheckBox, QComboBox, QDialog,
                               QFileDialog, QFrame, QGridLayout, QGroupBox,
                               QHBoxLayout, QHeaderView, QLabel, QLineEdit,
                               QListWidget, QListWidgetItem, QMenu, QProgressBar,
                               QPushButton, QRadioButton, QSplitter, QStyle,
                               QTableWidget, QTableWidgetItem, QToolBar,
                               QVBoxLayout, QWidget)

from .. import sound
from ..explorer import dialogs, viewers, vfs
from ..paths import DATA, ROOT
from ..wm import XPWindow
from .notepad import MENU_STYLE
from .utility_icons import winzip_icon

TIPS = [
    "Did you know you can drag and drop files directly from Windows Explorer into WinZip?",
    "You can easily create self-extracting zip files with WinZip Self-Extractor!",
    "Use the WinZip Wizard if you prefer step-by-step guidance when opening or creating zip files.",
    "WinZip automatically determines the best compression method for each file you add.",
    "You can quickly view pictures and documents inside a zip file without extracting them all.",
    "WinZip was first released for Windows in 1991 and became the standard zip utility for Windows XP!"
]


def _fmt_size(num_bytes):
    if num_bytes is None:
        return ""
    if num_bytes < 1024:
        return f"{num_bytes} B"
    elif num_bytes < 1024 * 1024:
        return f"{num_bytes / 1024:.1f} KB"
    return f"{num_bytes / (1024 * 1024):.1f} MB"


class WinZipTipDialog(QWidget):
    """Classic WinZip Tip of the Day dialog."""

    def __init__(self, desktop):
        super().__init__()
        self.desktop = desktop
        self.frame = None
        self.tip_idx = random.randint(0, len(TIPS) - 1)

        self.setWindowTitle("WinZip Tip of the Day")
        self.setFixedSize(440, 220)
        self.setStyleSheet("""
            QWidget { background: #ECE9D8; font-family: Tahoma; font-size: 11px; }
            QPushButton { min-height: 23px; min-width: 75px; }
            QFrame#tip_box { background: white; border: 1px solid #7F9DB9; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 10)

        top_row = QHBoxLayout()
        tip_box = QFrame()
        tip_box.setObjectName("tip_box")
        tb_v = QVBoxLayout(tip_box)
        tb_v.setContentsMargins(10, 10, 10, 10)

        head = QLabel("Did you know...")
        head.setFont(QFont("Tahoma", 10, QFont.Bold))
        head.setStyleSheet("color: #0A246A;")
        tb_v.addWidget(head)

        self.tip_lbl = QLabel(TIPS[self.tip_idx])
        self.tip_lbl.setWordWrap(True)
        self.tip_lbl.setFont(QFont("Tahoma", 9))
        tb_v.addWidget(self.tip_lbl, 1)

        top_row.addWidget(tip_box, 1)

        btn_v = QVBoxLayout()
        next_btn = QPushButton("Next Tip")
        next_btn.clicked.connect(self._next_tip)
        btn_v.addWidget(next_btn)

        close_btn = QPushButton("Close")
        close_btn.setDefault(True)
        close_btn.clicked.connect(self._close)
        btn_v.addWidget(close_btn)
        btn_v.addStretch()
        top_row.addLayout(btn_v)

        layout.addLayout(top_row, 1)

        self.chk = QCheckBox("Show Tips at Startup")
        self.chk.setChecked(True)
        layout.addWidget(self.chk)

    def _next_tip(self):
        self.tip_idx = (self.tip_idx + 1) % len(TIPS)
        self.tip_lbl.setText(TIPS[self.tip_idx])

    def _close(self):
        if self.frame:
            self.desktop.close_window(self.frame)


class WinZipWindow(QWidget):
    """WinZip main application window: toolbar, zip entry table, compression stats."""

    def __init__(self, desktop, initial_archive=None):
        super().__init__()
        self.desktop = desktop
        self.frame = None
        self.current_archive = Path(initial_archive) if initial_archive else None
        self.entries = []

        self.setWindowTitle(f"WinZip - {self.current_archive.name}" if self.current_archive else "WinZip")
        self.setMinimumSize(720, 460)
        self.setStyleSheet(MENU_STYLE + """
            QWidget#winzip { background: #ECE9D8; }
            QToolBar { background: #ECE9D8; border-bottom: 1px solid #ACA899; spacing: 3px; padding: 2px; }
            QToolButton { font-family: Tahoma; font-size: 11px; padding: 3px 6px; }
            QToolButton:hover { background: #B6BDD2; border: 1px solid #0A246A; }
            QTableWidget { background: white; border: 1px solid #7F9DB9; font-family: Tahoma; font-size: 11px; }
            QHeaderView::section { background: #ECE9D8; border: 1px solid #ACA899; padding: 2px; font-size: 11px; }
            QLabel#status { background: #ECE9D8; border-top: 1px solid #ACA899; padding: 2px 4px; font-family: Tahoma; font-size: 11px; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toolbar
        tb = QToolBar()
        tb.setIconSize(QSize(24, 24))
        style = self.style()

        tb.addAction(style.standardIcon(QStyle.SP_FileIcon), "New", self.action_new)
        tb.addAction(style.standardIcon(QStyle.SP_DialogOpenButton), "Open", self.action_open)
        tb.addAction(style.standardIcon(QStyle.SP_DriveNetIcon), "Favorites", self.action_favorites)
        tb.addSeparator()

        tb.addAction(style.standardIcon(QStyle.SP_FileDialogNewFolder), "Add", self.action_add)
        tb.addAction(style.standardIcon(QStyle.SP_FileDialogToParent), "Extract", self.action_extract)
        tb.addAction(style.standardIcon(QStyle.SP_FileDialogDetailedView), "View", self.action_view)
        tb.addSeparator()

        tb.addAction(style.standardIcon(QStyle.SP_DialogApplyButton), "CheckOut", self.action_checkout)
        tb.addAction(style.standardIcon(QStyle.SP_DialogHelpButton), "Wizard", self.action_wizard)
        layout.addWidget(tb)

        # File List Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["Name", "Date", "Time", "Size", "Ratio", "Packed", "Path"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.itemDoubleClicked.connect(self._item_double_clicked)
        layout.addWidget(self.table, 1)

        # Status Bar
        self.status = QLabel("Ready")
        self.status.setObjectName("status")
        layout.addWidget(self.status)

        if self.current_archive:
            self.load_archive(self.current_archive)

    def load_archive(self, archive_path):
        self.current_archive = Path(archive_path)
        self.setWindowTitle(f"WinZip - {self.current_archive.name}")
        self.entries.clear()
        self.table.setRowCount(0)
        style = self.style()

        if not self.current_archive.exists() or not zipfile.is_zipfile(self.current_archive):
            self.status.setText("Invalid or empty zip archive")
            return

        total_sz = 0
        total_packed = 0

        try:
            with zipfile.ZipFile(self.current_archive, "r") as zf:
                infos = zf.infolist()
                self.table.setRowCount(len(infos))
                for row, info in enumerate(infos):
                    dt = time.struct_time(info.date_time + (0, 0, -1))
                    d_str = time.strftime("%m/%d/%Y", dt)
                    t_str = time.strftime("%I:%M %p", dt)
                    ratio_num = int((1.0 - info.compress_size / max(1, info.file_size)) * 100) if info.file_size else 0
                    ratio_str = f"{ratio_num}%"

                    total_sz += info.file_size
                    total_packed += info.compress_size

                    p_obj = Path(info.filename)
                    fn = p_obj.name
                    fpath = str(p_obj.parent) if str(p_obj.parent) != "." else ""

                    name_it = QTableWidgetItem(fn)
                    name_it.setIcon(style.standardIcon(QStyle.SP_DirIcon if info.is_dir() else QStyle.SP_FileIcon))
                    name_it.setData(Qt.UserRole, info.filename)
                    self.table.setItem(row, 0, name_it)
                    self.table.setItem(row, 1, QTableWidgetItem(d_str))
                    self.table.setItem(row, 2, QTableWidgetItem(t_str))
                    self.table.setItem(row, 3, QTableWidgetItem(f"{info.file_size:,}"))
                    self.table.setItem(row, 4, QTableWidgetItem(ratio_str))
                    self.table.setItem(row, 5, QTableWidgetItem(f"{info.compress_size:,}"))
                    self.table.setItem(row, 6, QTableWidgetItem(fpath))

                overall_ratio = int((1.0 - total_packed / max(1, total_sz)) * 100) if total_sz else 0
                self.status.setText(f"{len(infos)} files, {_fmt_size(total_sz)} ({overall_ratio}% saved)")
        except Exception:
            self.status.setText("Error reading zip archive")

    def _item_double_clicked(self, table_item):
        if not self.current_archive:
            return
        row = table_item.row()
        fname = self.table.item(row, 0).data(Qt.UserRole)
        if not fname:
            return

        temp_dir = DATA / "temp_winzip"
        temp_dir.mkdir(parents=True, exist_ok=True)
        try:
            with zipfile.ZipFile(self.current_archive, "r") as zf:
                zf.extract(fname, temp_dir)
                out = temp_dir / fname
                if out.exists():
                    viewers.open_file(self.desktop, out)
        except Exception:
            pass

    def action_new(self):
        target = vfs.my_documents() / "New Archive.zip"
        with zipfile.ZipFile(target, "w") as zf:
            pass
        self.load_archive(target)
        dialogs.msgbox(self.desktop, "WinZip", "Created new zip archive in My Documents.", "info")

    def action_open(self):
        from .opendialog import open_dialog
        open_dialog(self.desktop, "Open Zip File", {".zip", ".cbz"}, self.load_archive)

    def action_favorites(self):
        dialogs.msgbox(self.desktop, "WinZip Favorites", "WinZip Favorites: Quick list of recently opened zip archives.", "info")

    def action_add(self):
        if not self.current_archive:
            self.action_new()
        from .opendialog import open_dialog
        def on_add(p):
            with zipfile.ZipFile(self.current_archive, "a", zipfile.ZIP_DEFLATED) as zf:
                zf.write(p, p.name)
            sound.play("default")
            self.load_archive(self.current_archive)
        open_dialog(self.desktop, "Add Files to Zip", {".txt", ".png", ".jpg", ".doc", ".rtf", ".exe", ".pdf"}, on_add)

    def action_extract(self):
        if not self.current_archive:
            dialogs.msgbox(self.desktop, "WinZip", "Please open a zip archive first.", "info")
            return
        dest = vfs.my_documents() / self.current_archive.stem
        dest.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(self.current_archive, "r") as zf:
            zf.extractall(dest)
        sound.play("default")
        dialogs.msgbox(self.desktop, "WinZip Extract", f"Extracted all files to:\n{vfs.to_virtual(dest) or dest}", "info")

    def action_view(self):
        r = self.table.currentRow()
        if r >= 0:
            self._item_double_clicked(self.table.item(r, 0))

    def action_checkout(self):
        dialogs.msgbox(self.desktop, "WinZip CheckOut", "CheckOut: WinZip creates temporary icons for all files in this archive.", "info")

    def action_wizard(self):
        self.action_extract()


_frame = None


def open_winzip(desktop, archive_path=None):
    global _frame
    from shiboken6 import isValid
    if _frame is not None and isValid(_frame):
        if archive_path:
            _frame.content.load_archive(archive_path)
        desktop.open_window(_frame)
        return _frame
    body = WinZipWindow(desktop, archive_path)
    _frame = XPWindow(desktop, "WinZip", body, winzip_icon(), (720, 460))
    body.frame = _frame
    desktop.open_window(_frame)

    if archive_path is None:
        tip_body = WinZipTipDialog(desktop)
        tip_win = XPWindow(desktop, "WinZip Tip of the Day", tip_body, winzip_icon(), (440, 220), buttons=("close",))
        tip_body.frame = tip_win
        tip_win.fit_fixed_content()
        try:
            area = desktop.work_area()
            tip_win.move(area.center() - tip_win.rect().center())
            tip_win.placed = True
        except Exception:
            pass
        desktop.open_window(tip_win)

    return _frame

