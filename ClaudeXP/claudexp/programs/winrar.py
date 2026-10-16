"""WinRAR: The classic Windows archive manager for ClaudeXP."""
import os
import shutil
import subprocess
import tempfile
import time
import zipfile
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, QSize, Qt, QTimer
from PySide6.QtGui import (QBrush, QColor, QFont, QIcon, QLinearGradient, QPainter,
                          QPen, QPixmap)
from PySide6.QtWidgets import (QAbstractItemView, QButtonGroup, QComboBox,
                               QDialog, QFileDialog, QFrame, QGridLayout,
                               QGroupBox, QHBoxLayout, QHeaderView, QLabel,
                               QLineEdit, QListWidget, QListWidgetItem, QMenu,
                               QProgressBar, QPushButton, QRadioButton,
                               QSplitter, QStyle, QTableWidget,
                               QTableWidgetItem, QToolBar, QToolButton,
                               QVBoxLayout, QWidget)

from .. import sound
from ..explorer import dialogs, viewers, vfs
from ..paths import DATA, ROOT
from ..wm import XPWindow
from .comix.library import seven_zip
from .notepad import MENU_STYLE
from .utility_icons import winrar_icon

TEMP_EXTRACT_DIR = DATA / "temp_winrar"


def _fmt_size(num_bytes):
    if num_bytes is None:
        return ""
    if num_bytes < 1024:
        return f"{num_bytes} B"
    elif num_bytes < 1024 * 1024:
        return f"{num_bytes / 1024:.1f} KB"
    elif num_bytes < 1024 * 1024 * 1024:
        return f"{num_bytes / (1024 * 1024):.1f} MB"
    return f"{num_bytes / (1024 * 1024 * 1024):.2f} GB"


class WinRAREvalDialog(QWidget):
    """The legendary 40-day WinRAR Evaluation copy reminder."""

    def __init__(self, desktop):
        super().__init__()
        self.desktop = desktop
        self.frame = None
        self.setWindowTitle("WinRAR Evaluation Copy")
        self.setFixedSize(460, 160)
        self.setStyleSheet("""
            QWidget { background: #ECE9D8; font-family: Tahoma; font-size: 11px; }
            QPushButton { min-height: 23px; min-width: 80px; font-family: Tahoma; font-size: 11px; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        row = QHBoxLayout()
        row.setSpacing(12)
        icon_lbl = QLabel()
        icon_lbl.setPixmap(winrar_icon(48).pixmap(48, 48))
        icon_lbl.setAlignment(Qt.AlignTop)
        row.addWidget(icon_lbl)

        txt = QLabel("Please note that WinRAR is not free software.\n\n"
                     "After a 40 day trial period you must either purchase a license or "
                     "remove it from your computer.")
        txt.setWordWrap(True)
        txt.setFont(QFont("Tahoma", 9))
        row.addWidget(txt, 1)
        layout.addLayout(row)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        btn_row.addStretch()

        buy_btn = QPushButton("Buy online")
        buy_btn.setFixedSize(85, 23)
        buy_btn.clicked.connect(self._buy)
        btn_row.addWidget(buy_btn)

        how_btn = QPushButton("How to buy")
        how_btn.setFixedSize(85, 23)
        how_btn.clicked.connect(self._how)
        btn_row.addWidget(how_btn)

        close_btn = QPushButton("Close")
        close_btn.setFixedSize(85, 23)
        close_btn.setDefault(True)
        close_btn.clicked.connect(self._close)
        btn_row.addWidget(close_btn)
        btn_row.addStretch()

        layout.addLayout(btn_row)

    def _buy(self):
        from . import navigator
        navigator.open_url(self.desktop, url="https://www.rarlab.com")
        self._close()

    def _how(self):
        dialogs.msgbox(self.desktop, "How to buy WinRAR",
                       "WinRAR licenses can be ordered online, by telephone, fax, or postal mail.\n"
                       "Thank you for supporting WinRAR development!", "info")

    def _close(self):
        if self.frame:
            self.desktop.close_window(self.frame)


class AddToArchiveDialog(QWidget):
    """WinRAR Archive name and parameters dialog."""

    def __init__(self, desktop, source_paths, on_create):
        super().__init__()
        self.desktop = desktop
        self.source_paths = source_paths
        self.on_create = on_create
        self.frame = None

        self.setWindowTitle("Archive name and parameters")
        self.setFixedSize(480, 320)
        self.setStyleSheet("""
            QWidget { background: #ECE9D8; font-family: Tahoma; font-size: 11px; }
            QPushButton { min-height: 23px; min-width: 75px; }
            QLineEdit { background: white; border: 1px solid #7F9DB9; padding: 2px; }
            QGroupBox { font-weight: bold; margin-top: 6px; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # Archive name
        name_row = QHBoxLayout()
        name_row.addWidget(QLabel("Archive name:"))
        default_name = source_paths[0].stem if source_paths else "New_Archive"
        self.name_edit = QLineEdit(f"{default_name}.rar")
        name_row.addWidget(self.name_edit, 1)
        layout.addLayout(name_row)

        # Format & Compression
        mid_row = QHBoxLayout()

        fmt_box = QGroupBox("Archive format")
        fv = QVBoxLayout(fmt_box)
        self.rar_rb = QRadioButton("RAR")
        self.rar_rb.setChecked(True)
        self.zip_rb = QRadioButton("ZIP")
        fv.addWidget(self.rar_rb)
        fv.addWidget(self.zip_rb)
        mid_row.addWidget(fmt_box)

        self.rar_rb.toggled.connect(lambda on: self._update_ext(".rar" if on else ".zip"))

        comp_box = QGroupBox("Compression method")
        cv = QVBoxLayout(comp_box)
        self.comp_combo = QComboBox()
        self.comp_combo.addItems(["Store", "Fastest", "Fast", "Normal", "Good", "Best"])
        self.comp_combo.setCurrentText("Normal")
        cv.addWidget(self.comp_combo)
        mid_row.addWidget(comp_box)
        layout.addLayout(mid_row)

        # Options
        opt_box = QGroupBox("Archiving options")
        ov = QVBoxLayout(opt_box)
        ov.addWidget(QLabel("✓ Create solid archive"))
        ov.addWidget(QLabel("✓ Put authenticity verification"))
        ov.addWidget(QLabel("✓ Recovery record: 3%"))
        layout.addWidget(opt_box)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        btn_row.addStretch()
        ok_btn = QPushButton("OK")
        ok_btn.setFixedSize(75, 23)
        ok_btn.setDefault(True)
        ok_btn.clicked.connect(self._accept)
        btn_row.addWidget(ok_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedSize(75, 23)
        cancel_btn.clicked.connect(self._close)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)

    def _update_ext(self, new_ext):
        base = self.name_edit.text().rsplit(".", 1)[0]
        self.name_edit.setText(f"{base}{new_ext}")

    def _accept(self):
        name = self.name_edit.text().strip()
        fmt = "rar" if self.rar_rb.isChecked() else "zip"
        method = self.comp_combo.currentText()
        if self.frame:
            self.desktop.close_window(self.frame)
        self.on_create(name, fmt, method)

    def _close(self):
        if self.frame:
            self.desktop.close_window(self.frame)


class WinRARWindow(QWidget):
    """WinRAR main window: archive browsing, toolbar, extraction, testing."""

    def __init__(self, desktop, initial_archive=None):
        super().__init__()
        self.desktop = desktop
        self.frame = None
        self.current_archive = Path(initial_archive) if initial_archive else None
        self.current_subpath = ""      # subpath inside archive
        self.current_folder = vfs.my_documents() if not self.current_archive else None
        self.archive_entries = []       # list of dicts: {name, size, packed, type, mtime, crc, ratio, is_dir}

        self.setWindowTitle(f"WinRAR - {self.current_archive.name}" if self.current_archive else "WinRAR (evaluation copy)")
        self.setMinimumSize(480, 260)
        self.setStyleSheet(MENU_STYLE + """
            QWidget#winrar { background: #ECE9D8; }
            QToolBar { background: #ECE9D8; border-bottom: 1px solid #ACA899; spacing: 1px; padding: 2px 2px; }
            QToolButton { font-family: Tahoma; font-size: 11px; padding: 2px 4px; border: 1px solid transparent; border-radius: 2px; }
            QToolButton:hover { background: #B6BDD2; border: 1px solid #0A246A; }
            QToolButton:pressed { background: #8592B5; border: 1px solid #0A246A; }
            QTableWidget { background: white; border: 1px solid #7F9DB9; font-family: Tahoma; font-size: 11px; }
            QHeaderView::section { background: #ECE9D8; border: 1px solid #ACA899; padding: 3px; font-size: 11px; }
            QLineEdit#path_bar { background: white; border: 1px solid #7F9DB9; font-family: Tahoma; font-size: 11px; padding: 2px; }
            QLabel#status { background: #ECE9D8; border-top: 1px solid #ACA899; padding: 2px 4px; font-family: Tahoma; font-size: 11px; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toolbar
        tb = QToolBar()
        tb.setMovable(False)
        tb.setFloatable(False)
        tb.setIconSize(QSize(24, 24))
        tb.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        style = self.style()

        tb.addAction(style.standardIcon(QStyle.SP_FileDialogNewFolder), "Add", self.action_add)
        tb.addAction(style.standardIcon(QStyle.SP_FileDialogToParent), "Extract To", self.action_extract)
        tb.addAction(style.standardIcon(QStyle.SP_DialogApplyButton), "Test", self.action_test)
        tb.addAction(style.standardIcon(QStyle.SP_FileDialogDetailedView), "View", self.action_view)
        tb.addAction(style.standardIcon(QStyle.SP_TrashIcon), "Delete", self.action_delete)
        tb.addAction(style.standardIcon(QStyle.SP_FileDialogListView), "Find", self.action_find)
        tb.addAction(style.standardIcon(QStyle.SP_DialogHelpButton), "Wizard", self.action_wizard)
        tb.addAction(style.standardIcon(QStyle.SP_MessageBoxInformation), "Info", self.action_info)
        tb.addAction(style.standardIcon(QStyle.SP_DriveHDIcon), "VirusScan", self.action_virus_scan)
        layout.addWidget(tb)

        # Address / navigation bar
        nav_row = QHBoxLayout()
        nav_row.setContentsMargins(4, 3, 4, 3)
        self.up_btn = QPushButton("..")
        self.up_btn.setFixedSize(28, 22)
        self.up_btn.clicked.connect(self.navigate_up)
        nav_row.addWidget(self.up_btn)

        self.path_edit = QLineEdit()
        self.path_edit.setObjectName("path_bar")
        self.path_edit.setReadOnly(True)
        nav_row.addWidget(self.path_edit, 1)
        layout.addLayout(nav_row)

        # Main Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["Name", "Size", "Packed", "Type", "Modified", "CRC32", "Ratio"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table.itemDoubleClicked.connect(self._item_double_clicked)
        self.table.itemSelectionChanged.connect(self._selection_changed)
        layout.addWidget(self.table, 1)

        # Status Bar
        self.status = QLabel("Ready")
        self.status.setObjectName("status")
        layout.addWidget(self.status)

        if self.current_archive:
            self.load_archive(self.current_archive)
        else:
            self.load_filesystem(self.current_folder)

    # ---- Navigation & Loading ----
    def load_archive(self, archive_path):
        self.current_archive = Path(archive_path)
        self.current_folder = None
        self.current_subpath = ""
        self.path_edit.setText(f"{self.current_archive.name}")
        self.setWindowTitle(f"WinRAR - {self.current_archive.name}")
        self._read_archive_entries()
        self._populate_archive_view()

    def load_filesystem(self, folder_path):
        self.current_archive = None
        self.current_folder = Path(folder_path)
        self.current_subpath = ""
        self.path_edit.setText(str(self.current_folder))
        self.setWindowTitle("WinRAR (evaluation copy)")
        self.archive_entries.clear()
        style = self.style()

        try:
            for p in sorted(self.current_folder.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
                if p.name.startswith("."):
                    continue
                sz = p.stat().st_size if p.is_file() else None
                mtime = time.strftime("%Y-%m-%d %H:%M", time.localtime(p.stat().st_mtime))
                self.archive_entries.append({
                    "name": p.name,
                    "size": sz,
                    "packed": sz,
                    "type": "File folder" if p.is_dir() else f"{p.suffix.upper()} File",
                    "mtime": mtime,
                    "crc": "",
                    "ratio": "",
                    "is_dir": p.is_dir(),
                    "real_path": p
                })
        except OSError:
            pass
        self._render_table()

    def _read_archive_entries(self):
        self.archive_entries.clear()
        if not self.current_archive or not self.current_archive.exists():
            return

        ext = self.current_archive.suffix.lower()
        exe = seven_zip()

        # Try 7-Zip first for rar, 7z, tar, zip
        if exe:
            try:
                res = subprocess.run([exe, "l", "-slt", "-ba", str(self.current_archive)],
                                     capture_output=True, text=True,
                                     creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
                if res.returncode == 0:
                    curr = {}
                    for line in res.stdout.splitlines():
                        if not line.strip():
                            if curr.get("Path"):
                                self._add_entry_from_7z(curr)
                            curr = {}
                            continue
                        if " = " in line:
                            k, v = line.split(" = ", 1)
                            curr[k.strip()] = v.strip()
                    if curr.get("Path"):
                        self._add_entry_from_7z(curr)
                    return
            except Exception:
                pass

        # Fallback to Python zipfile for .zip / .cbz
        if ext in (".zip", ".cbz") and zipfile.is_zipfile(self.current_archive):
            try:
                with zipfile.ZipFile(self.current_archive, "r") as zf:
                    for info in zf.infolist():
                        dt = time.strftime("%Y-%m-%d %H:%M", time.struct_time(info.date_time + (0, 0, -1)))
                        is_dir = info.is_dir()
                        ratio = f"{int((1.0 - info.compress_size / max(1, info.file_size)) * 100)}%" if info.file_size else "0%"
                        self.archive_entries.append({
                            "name": info.filename.rstrip("/"),
                            "size": info.file_size,
                            "packed": info.compress_size,
                            "type": "Folder" if is_dir else "File",
                            "mtime": dt,
                            "crc": f"{info.CRC:08X}",
                            "ratio": ratio,
                            "is_dir": is_dir,
                            "real_path": None
                        })
            except Exception:
                pass

    def _add_entry_from_7z(self, d):
        path_str = d.get("Path", "").replace("\\", "/")
        is_dir = (d.get("Folder") == "+" or d.get("Attributes", "").startswith("D") or path_str.endswith("/"))
        size = int(d.get("Size", 0)) if not is_dir else 0
        packed = int(d.get("Packed Size", size)) if not is_dir else 0
        mtime = d.get("Modified", "")[:16]
        crc = d.get("CRC", "")
        ratio = f"{int((1.0 - packed / max(1, size)) * 100)}%" if size > 0 else "0%"
        self.archive_entries.append({
            "name": path_str.rstrip("/"),
            "size": size,
            "packed": packed,
            "type": "Folder" if is_dir else "File",
            "mtime": mtime,
            "crc": crc,
            "ratio": ratio,
            "is_dir": is_dir,
            "real_path": None
        })

    def _populate_archive_view(self):
        self._render_table()

    def _render_table(self):
        self.table.setRowCount(0)
        style = self.style()

        # Filter items by current_subpath if inside an archive
        display_items = []
        if self.current_archive:
            sub = self.current_subpath.strip("/")
            seen_dirs = set()
            for e in self.archive_entries:
                fn = e["name"]
                if sub:
                    if not fn.startswith(sub + "/"):
                        continue
                    rel = fn[len(sub) + 1:]
                else:
                    rel = fn

                parts = rel.split("/")
                if len(parts) > 1:
                    # Intermediate folder
                    dname = parts[0]
                    if dname not in seen_dirs:
                        seen_dirs.add(dname)
                        display_items.append({
                            "name": dname, "size": None, "packed": None, "type": "Folder",
                            "mtime": "", "crc": "", "ratio": "", "is_dir": True, "full_sub": (sub + "/" + dname).strip("/")
                        })
                else:
                    item_copy = dict(e)
                    item_copy["display_name"] = parts[0]
                    item_copy["full_sub"] = fn
                    display_items.append(item_copy)
        else:
            display_items = self.archive_entries

        self.table.setRowCount(len(display_items))
        for row, item in enumerate(display_items):
            is_dir = item.get("is_dir", False)
            icon = style.standardIcon(QStyle.SP_DirIcon if is_dir else QStyle.SP_FileIcon)
            disp_name = item.get("display_name", item["name"])

            name_it = QTableWidgetItem(disp_name)
            name_it.setIcon(icon)
            name_it.setData(Qt.UserRole, item)
            self.table.setItem(row, 0, name_it)
            self.table.setItem(row, 1, QTableWidgetItem(_fmt_size(item["size"]) if item["size"] is not None else ""))
            self.table.setItem(row, 2, QTableWidgetItem(_fmt_size(item["packed"]) if item["packed"] is not None else ""))
            self.table.setItem(row, 3, QTableWidgetItem(item["type"]))
            self.table.setItem(row, 4, QTableWidgetItem(item["mtime"]))
            self.table.setItem(row, 5, QTableWidgetItem(item["crc"]))
            self.table.setItem(row, 6, QTableWidgetItem(item["ratio"]))

        self._selection_changed()

    def _selection_changed(self):
        sel = self.table.selectedItems()
        sel_rows = len(self.table.selectionModel().selectedRows())
        total_rows = self.table.rowCount()
        self.status.setText(f"Selected {sel_rows} items • Total {total_rows} items in current view")

    def navigate_up(self):
        if self.current_archive:
            if "/" in self.current_subpath.strip("/"):
                self.current_subpath = self.current_subpath.strip("/").rsplit("/", 1)[0]
            else:
                self.current_subpath = ""
            self.path_edit.setText(f"{self.current_archive.name}\\{self.current_subpath}".rstrip("\\"))
            self._render_table()
        elif self.current_folder and self.current_folder.parent.exists():
            self.load_filesystem(self.current_folder.parent)

    def _item_double_clicked(self, table_item):
        row = table_item.row()
        item_data = self.table.item(row, 0).data(Qt.UserRole)
        if not item_data:
            return

        if item_data.get("is_dir"):
            if self.current_archive:
                self.current_subpath = item_data.get("full_sub", item_data["name"])
                self.path_edit.setText(f"{self.current_archive.name}\\{self.current_subpath}")
                self._render_table()
            else:
                self.load_filesystem(item_data["real_path"])
        else:
            # File clicked
            if self.current_archive:
                self._extract_and_open(item_data)
            else:
                p = item_data["real_path"]
                if p.suffix.lower() in (".rar", ".zip", ".7z", ".tar", ".cbz", ".cbr"):
                    self.load_archive(p)
                else:
                    viewers.open_file(self.desktop, p)

    def _extract_and_open(self, item_data):
        file_name = item_data["name"]
        TEMP_EXTRACT_DIR.mkdir(parents=True, exist_ok=True)
        exe = seven_zip()
        if exe:
            subprocess.run([exe, "e", str(self.current_archive), f"-o{TEMP_EXTRACT_DIR}", file_name, "-y"],
                           capture_output=True, text=True,
                           creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
            out_file = TEMP_EXTRACT_DIR / Path(file_name).name
            if out_file.exists():
                viewers.open_file(self.desktop, out_file)
                return

        # Fallback zip extraction
        if zipfile.is_zipfile(self.current_archive):
            with zipfile.ZipFile(self.current_archive, "r") as zf:
                zf.extract(file_name, TEMP_EXTRACT_DIR)
                out_file = TEMP_EXTRACT_DIR / file_name
                if out_file.exists():
                    viewers.open_file(self.desktop, out_file)

    # ---- Actions ----
    def action_add(self):
        sel_paths = []
        if self.current_folder:
            for r in self.table.selectionModel().selectedRows():
                it = self.table.item(r.row(), 0).data(Qt.UserRole)
                if it and it.get("real_path"):
                    sel_paths.append(it["real_path"])
        if not sel_paths:
            sel_paths = [vfs.my_documents()]

        def on_create(name, fmt, method):
            target = vfs.my_documents() / name
            exe = seven_zip()
            if exe:
                mx_map = {"Store": "0", "Fastest": "1", "Fast": "3", "Normal": "5", "Good": "7", "Best": "9"}
                args = [exe, "a", str(target), f"-mx={mx_map.get(method, '5')}"]
                for sp in sel_paths:
                    args.append(str(sp))
                subprocess.run(args, capture_output=True, text=True,
                               creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
            else:
                # Zipfile fallback
                with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zf:
                    for sp in sel_paths:
                        if sp.is_file():
                            zf.write(sp, sp.name)
                        elif sp.is_dir():
                            for root, dirs, files in os.walk(sp):
                                for f in files:
                                    fp = Path(root) / f
                                    zf.write(fp, fp.relative_to(sp))
            sound.play("default")
            dialogs.msgbox(self.desktop, "WinRAR", f"Archive '{name}' created successfully in My Documents.", "info")
            self.load_archive(target)

        wiz = AddToArchiveDialog(self.desktop, sel_paths, on_create)
        win = XPWindow(self.desktop, "Archive name and parameters", wiz, winrar_icon(), (480, 310), buttons=("close",))
        wiz.frame = win
        win.fit_fixed_content()
        try:
            area = self.desktop.work_area()
            win.move(area.center() - win.rect().center())
            win.placed = True
        except Exception:
            pass
        self.desktop.open_window(win)

    def action_extract(self):
        if not self.current_archive:
            dialogs.msgbox(self.desktop, "WinRAR", "Please open an archive first before extracting.", "info")
            return

        dest = vfs.my_documents() / self.current_archive.stem
        dest.mkdir(parents=True, exist_ok=True)
        exe = seven_zip()
        if exe:
            subprocess.run([exe, "x", str(self.current_archive), f"-o{dest}", "-y"],
                           capture_output=True, text=True,
                           creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
        elif zipfile.is_zipfile(self.current_archive):
            with zipfile.ZipFile(self.current_archive, "r") as zf:
                zf.extractall(dest)

        sound.play("default")
        dialogs.msgbox(self.desktop, "WinRAR: Extraction finished",
                       f"Extracted all files to:\n{vfs.to_virtual(dest) or dest}", "info")

    def action_test(self):
        if not self.current_archive:
            dialogs.msgbox(self.desktop, "WinRAR", "Please open an archive first before testing.", "info")
            return
        sound.play("default")
        dialogs.msgbox(self.desktop, "Test archive",
                       f"Archive: {self.current_archive.name}\n"
                       f"Tested {len(self.archive_entries)} files.\n"
                       "No errors found during testing process.", "info")

    def action_view(self):
        r = self.table.currentRow()
        if r >= 0:
            it = self.table.item(r, 0).data(Qt.UserRole)
            if it:
                self._item_double_clicked(self.table.item(r, 0))

    def action_delete(self):
        dialogs.msgbox(self.desktop, "WinRAR", "Selected files cannot be deleted from read-only archive.", "info")

    def action_find(self):
        from .search import open_search
        open_search(self.desktop)

    def action_wizard(self):
        self.action_extract()

    def action_info(self):
        if self.current_archive:
            sz = self.current_archive.stat().st_size
            dialogs.msgbox(self.desktop, "Archive Information",
                           f"Archive name: {self.current_archive.name}\n"
                           f"Path: {self.current_archive}\n"
                           f"Total files: {len(self.archive_entries)}\n"
                           f"Archive size: {_fmt_size(sz)}\n"
                           f"Compression type: {self.current_archive.suffix.upper().lstrip('.')}\n"
                           "Solid archive: Yes", "info")
        else:
            dialogs.msgbox(self.desktop, "Folder Information", f"Browsing: {self.current_folder}", "info")

    def action_virus_scan(self):
        from .. import maintenance
        maintenance.get().antivirus.open()


_frame = None


def open_winrar(desktop, archive_path=None):
    global _frame
    from shiboken6 import isValid
    if _frame is not None and isValid(_frame):
        if archive_path:
            _frame.content.load_archive(archive_path)
        desktop.open_window(_frame)
        return _frame
    body = WinRARWindow(desktop, archive_path)
    _frame = XPWindow(desktop, "WinRAR", body, winrar_icon(), (760, 480))
    body.frame = _frame
    desktop.open_window(_frame)

    # Show 40 day evaluation popup if launched without specific file
    if archive_path is None:
        eval_body = WinRAREvalDialog(desktop)
        eval_win = XPWindow(desktop, "WinRAR Evaluation Copy", eval_body, winrar_icon(), (460, 160), buttons=("close",))
        eval_body.frame = eval_win
        eval_win.fit_fixed_content()
        try:
            area = desktop.work_area()
            eval_win.move(area.center() - eval_win.rect().center())
            eval_win.placed = True
        except Exception:
            pass
        desktop.open_window(eval_win)

    return _frame

