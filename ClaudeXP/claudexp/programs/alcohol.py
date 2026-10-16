"""Alcohol 120%: CD/DVD burning and virtual drive emulation for ClaudeXP."""
import json
import os
import shutil
import subprocess
import time
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, QSize, Qt, QTimer
from PySide6.QtGui import (QBrush, QColor, QFont, QIcon, QLinearGradient, QPainter,
                          QPainterPath, QPen, QPixmap)
from PySide6.QtWidgets import (QAbstractItemView, QComboBox, QDialog, QFileDialog,
                               QFrame, QGridLayout, QGroupBox, QHBoxLayout,
                               QHeaderView, QLabel, QLineEdit, QListWidget,
                               QListWidgetItem, QMenu, QProgressBar, QPushButton,
                               QRadioButton, QSplitter, QStyle, QTableWidget,
                               QTableWidgetItem, QTreeWidget, QTreeWidgetItem,
                               QVBoxLayout, QWidget)

from .. import sound
from ..explorer import dialogs, vfs
from ..paths import DATA, ROOT
from ..wm import XPWindow
from .comix.library import seven_zip
from .notepad import MENU_STYLE
from .utility_icons import alcohol_icon, burn_icon, virtual_drive_icon

STATE_FILE = DATA / "alcohol.json"
VIRTUAL_F_DIR = DATA / "virtual_disc_f"
IMAGE_EXTS = {".iso", ".bin", ".cue", ".nrg", ".mdf", ".mds", ".ccd", ".img"}


def _fmt_size(num_bytes):
    if num_bytes < 1024:
        return f"{num_bytes} B"
    elif num_bytes < 1024 * 1024:
        return f"{num_bytes / 1024:.1f} KB"
    elif num_bytes < 1024 * 1024 * 1024:
        return f"{num_bytes / (1024 * 1024):.1f} MB"
    return f"{num_bytes / (1024 * 1024 * 1024):.2f} GB"


def _load_state():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text("utf-8"))
        except Exception:
            pass
    return {
        "virtual_drives": 1,
        "mounted_image": None,
        "mounted_name": "",
        "images": [],
        "emulation": {"safedisc": True, "securom": True, "rmps": True, "laserlock": False}
    }


def _save_state(state):
    try:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")
    except Exception:
        pass


def virtual_drive():
    """Drive definition for Alcohol 120% virtual drive (F:), exposed in vfs.drives()."""
    st = _load_state()
    if st.get("virtual_drives", 1) <= 0:
        return None
    mounted = st.get("mounted_image")
    root_path = VIRTUAL_F_DIR if (mounted and VIRTUAL_F_DIR.exists() and any(VIRTUAL_F_DIR.iterdir())) else None
    label = f"Alcohol Virtual CD" if not st.get("mounted_name") else f"Alcohol CD ({st.get('mounted_name')[:12]})"
    return vfs.Drive("F", label, "cd", root_path)


class TaskPaneButton(QPushButton):
    """Button styled for the Alcohol 120% blue task pane sidebar."""

    def __init__(self, text, icon=None, parent=None):
        super().__init__(text, parent)
        if icon:
            self.setIcon(icon)
        self.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                text-align: left;
                padding: 4px 8px;
                color: #0A246A;
                font-family: Tahoma;
                font-size: 11px;
            }
            QPushButton:hover {
                text-decoration: underline;
                color: #0044BB;
            }
        """)


class AlcoholWindow(QWidget):
    """Alcohol 120% main window: task sidebar, image list, physical/virtual devices."""

    def __init__(self, desktop):
        super().__init__()
        self.desktop = desktop
        self.frame = None
        self.state = _load_state()

        self.setWindowTitle("Alcohol 120%")
        self.setMinimumSize(800, 520)
        self.setStyleSheet(MENU_STYLE + """
            QWidget#alcohol { background: #ECE9D8; }
            QTreeWidget, QTableWidget { background: white; border: 1px solid #7F9DB9; font-family: Tahoma; font-size: 11px; }
            QHeaderView::section { background: #ECE9D8; border: 1px solid #ACA899; padding: 2px; font-size: 11px; }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Left Task Pane
        task_pane = QWidget()
        task_pane.setFixedWidth(200)
        task_pane.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6B8EC6, stop:1 #4971B7);")
        tp_v = QVBoxLayout(task_pane)
        tp_v.setContentsMargins(6, 6, 6, 6)
        tp_v.setSpacing(8)

        # Section: Main Options
        sec1 = self._build_section("Main Options", [
            ("Image Making Wizard", QStyle.SP_FileDialogDetailedView, self.image_making_wizard),
            ("Image Burning Wizard", QStyle.SP_DriveCDIcon, self.image_burning_wizard),
            ("Copy Wizard", QStyle.SP_FileDialogDetailedView, self.copy_wizard),
            ("Image Finder", QStyle.SP_FileDialogListView, self.image_finder),
            ("CD/DVD Manager", QStyle.SP_DriveCDIcon, self.device_manager),
            ("Erase Wizard", QStyle.SP_DialogResetButton, self.erase_wizard),
        ])
        tp_v.addWidget(sec1)

        # Section: Options
        sec2 = self._build_section("Options", [
            ("Virtual Drive Settings", QStyle.SP_DriveCDIcon, self.virtual_drive_settings),
            ("Emulation Settings", QStyle.SP_MessageBoxInformation, self.emulation_settings),
            ("Recording Preferences", QStyle.SP_FileDialogDetailedView, self.recording_preferences),
        ])
        tp_v.addWidget(sec2)

        # Section: Information
        sec3 = self._build_section("Information", [
            ("Registered: ClaudeXP", QStyle.SP_DialogApplyButton, None),
            (f"Virtual Drives: {self.state.get('virtual_drives', 1)}", QStyle.SP_DriveCDIcon, None),
            ("About Alcohol 120%", QStyle.SP_MessageBoxInformation, self.about_alcohol),
        ])
        tp_v.addWidget(sec3)
        tp_v.addStretch()
        layout.addWidget(task_pane)

        # Right Splitter: Image List (Top) & Device List (Bottom)
        right_splitter = QSplitter(Qt.Vertical)
        right_splitter.setStyleSheet("QSplitter::handle { background: #ACA899; }")

        # Top: Image File List
        top_box = QWidget()
        tb_v = QVBoxLayout(top_box)
        tb_v.setContentsMargins(6, 6, 6, 4)
        top_head = QHBoxLayout()
        th_lbl = QLabel("Image File List:")
        th_lbl.setFont(QFont("Tahoma", 9, QFont.Bold))
        top_head.addWidget(th_lbl)
        top_head.addStretch()

        mount_btn = QPushButton("Mount on Device (F:)")
        mount_btn.setIcon(virtual_drive_icon(16))
        mount_btn.clicked.connect(self._mount_selected)
        top_head.addWidget(mount_btn)

        add_btn = QPushButton("Add Image...")
        add_btn.setIcon(self.style().standardIcon(QStyle.SP_FileDialogNewFolder))
        add_btn.clicked.connect(self.add_image_dialog)
        top_head.addWidget(add_btn)

        rem_btn = QPushButton("Remove")
        rem_btn.clicked.connect(self.remove_image)
        top_head.addWidget(rem_btn)
        tb_v.addLayout(top_head)

        self.img_table = QTableWidget()
        self.img_table.setColumnCount(5)
        self.img_table.setHorizontalHeaderLabels(["Name", "Format", "Size", "File Path", "Modified"])
        self.img_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.img_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.img_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.img_table.itemDoubleClicked.connect(lambda _it: self._mount_selected())
        self.img_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.img_table.customContextMenuRequested.connect(self._img_menu)
        tb_v.addWidget(self.img_table, 1)
        right_splitter.addWidget(top_box)

        # Bottom: Device List
        bot_box = QWidget()
        bb_v = QVBoxLayout(bot_box)
        bb_v.setContentsMargins(6, 4, 6, 6)
        bot_head = QLabel("Device List (Physical & Virtual Drives):")
        bot_head.setFont(QFont("Tahoma", 9, QFont.Bold))
        bb_v.addWidget(bot_head)

        self.dev_tree = QTreeWidget()
        self.dev_tree.setHeaderLabels(["Device", "Type", "Status / Mounted Image"])
        self.dev_tree.header().resizeSection(0, 240)
        self.dev_tree.header().resizeSection(1, 140)
        self.dev_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.dev_tree.customContextMenuRequested.connect(self._dev_menu)
        bb_v.addWidget(self.dev_tree, 1)
        right_splitter.addWidget(bot_box)

        right_splitter.setSizes([280, 220])
        layout.addWidget(right_splitter, 1)

        self._refresh_images()
        self._refresh_devices()

    def _build_section(self, title, items):
        frame = QFrame()
        frame.setStyleSheet("QFrame { background: white; border: 1px solid #7F9DB9; border-radius: 3px; }")
        v = QVBoxLayout(frame)
        v.setContentsMargins(4, 4, 4, 6)
        v.setSpacing(2)

        head = QLabel(f" {title}")
        head.setFont(QFont("Tahoma", 8, QFont.Bold))
        head.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #8BB3EA, stop:1 #CBDFF8); "
                           "color: #0C2C6A; padding: 3px; font-weight: bold; border-radius: 2px;")
        v.addWidget(head)

        style = self.style()
        for label, icon_kind, slot in items:
            btn = TaskPaneButton(f" {label}")
            if icon_kind:
                btn.setIcon(style.standardIcon(icon_kind))
            if slot:
                btn.clicked.connect(slot)
            else:
                btn.setEnabled(False)
            v.addWidget(btn)
        return frame

    # ---- Image list management ----
    def _refresh_images(self):
        self.img_table.setRowCount(0)
        style = self.style()
        # Seed images from state
        paths = [Path(p) for p in self.state.get("images", []) if Path(p).exists()]
        self.img_table.setRowCount(len(paths))
        for row, p in enumerate(paths):
            sz = p.stat().st_size
            mtime = time.strftime("%Y-%m-%d %H:%M", time.localtime(p.stat().st_mtime))
            name_it = QTableWidgetItem(p.stem)
            name_it.setIcon(style.standardIcon(QStyle.SP_DriveCDIcon))
            name_it.setData(Qt.UserRole, str(p))
            self.img_table.setItem(row, 0, name_it)
            self.img_table.setItem(row, 1, QTableWidgetItem(p.suffix.upper().lstrip(".")))
            self.img_table.setItem(row, 2, QTableWidgetItem(_fmt_size(sz)))
            self.img_table.setItem(row, 3, QTableWidgetItem(str(p)))
            self.img_table.setItem(row, 4, QTableWidgetItem(mtime))

    def _refresh_devices(self):
        self.dev_tree.clear()
        style = self.style()

        # Physical drive D:
        d_item = QTreeWidgetItem(self.dev_tree)
        d_item.setText(0, "(D:) ATAPI CD-RW 52x32x52")
        d_item.setText(1, "IDE CD/DVD-RW")
        from .nero import VIRTUAL_CD_DIR
        if VIRTUAL_CD_DIR.exists() and any(VIRTUAL_CD_DIR.iterdir()):
            d_item.setText(2, "Disc inserted (CD-ROM)")
        else:
            d_item.setText(2, "Empty")
        d_item.setIcon(0, style.standardIcon(QStyle.SP_DriveCDIcon))
        d_item.setData(0, Qt.UserRole, "D")

        # Virtual drive F:
        if self.state.get("virtual_drives", 1) > 0:
            f_item = QTreeWidgetItem(self.dev_tree)
            f_item.setText(0, "(F:) [AXV] CD/DVD-ROM (Virtual Drive)")
            f_item.setText(1, "Alcohol Virtual SCSI")
            mounted = self.state.get("mounted_image")
            if mounted and Path(mounted).exists():
                f_item.setText(2, f"Mounted: {Path(mounted).name}")
            else:
                f_item.setText(2, "Empty")
            f_item.setIcon(0, virtual_drive_icon(16))
            f_item.setData(0, Qt.UserRole, "F")

    def _mount_selected(self):
        row = self.img_table.currentRow()
        if row < 0:
            return
        item = self.img_table.item(row, 0)
        if not item:
            return
        self.mount_image_path(Path(item.data(Qt.UserRole)))

    def mount_image_path(self, path):
        if not path or not path.exists():
            return
        # Extract/prepare virtual drive F:
        try:
            VIRTUAL_F_DIR.mkdir(parents=True, exist_ok=True)
            for sub in VIRTUAL_F_DIR.iterdir():
                shutil.rmtree(sub, ignore_errors=True) if sub.is_dir() else sub.unlink(missing_ok=True)

            exe = seven_zip()
            ext = path.suffix.lower()
            if exe and ext in (".iso", ".rar", ".7z", ".zip", ".tar"):
                # Unpack ISO / archive contents into virtual disc folder
                subprocess.run([exe, "x", str(path), f"-o{VIRTUAL_F_DIR}", "-y"],
                               capture_output=True, text=True,
                               creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
            else:
                # Mirror / create placeholder disc files
                (VIRTUAL_F_DIR / "AUTORUN.INF").write_text(f"[autorun]\nlabel={path.stem}\n", encoding="utf-8")
                (VIRTUAL_F_DIR / f"{path.name}").write_bytes(path.read_bytes()[:1024 * 1024])
        except Exception:
            pass

        self.state["mounted_image"] = str(path)
        self.state["mounted_name"] = path.stem
        _save_state(self.state)
        sound.play_clip("cdrom_startup2.mp3", 3500)
        self._refresh_devices()
        dialogs.msgbox(self.desktop, "Alcohol 120%", f"Image '{path.name}' mounted successfully to Drive (F:).", "info")

    def unmount_virtual_drive(self):
        self.state["mounted_image"] = None
        self.state["mounted_name"] = ""
        _save_state(self.state)
        if VIRTUAL_F_DIR.exists():
            for sub in VIRTUAL_F_DIR.iterdir():
                shutil.rmtree(sub, ignore_errors=True) if sub.is_dir() else sub.unlink(missing_ok=True)
        sound.play("default")
        self._refresh_devices()
        dialogs.msgbox(self.desktop, "Alcohol 120%", "Virtual Drive (F:) unmounted.", "info")

    def add_image_dialog(self):
        from .opendialog import open_dialog
        def on_open(p):
            if str(p) not in self.state["images"]:
                self.state["images"].append(str(p))
                _save_state(self.state)
                self._refresh_images()
        open_dialog(self.desktop, "Select Disc Image", IMAGE_EXTS, on_open)

    def remove_image(self):
        row = self.img_table.currentRow()
        if row >= 0:
            p_str = self.img_table.item(row, 0).data(Qt.UserRole)
            self.state["images"] = [x for x in self.state["images"] if x != p_str]
            _save_state(self.state)
            self._refresh_images()

    def _img_menu(self, pos):
        item = self.img_table.itemAt(pos)
        if not item:
            return
        row = item.row()
        path = Path(self.img_table.item(row, 0).data(Qt.UserRole))
        menu = QMenu(self)
        menu.addAction("Mount on Virtual Drive (F:)", lambda: self.mount_image_path(path))
        menu.addAction("Burn with Alcohol 120%...", lambda: self._burn_image_file(path))
        menu.addSeparator()
        menu.addAction("Remove from List", self.remove_image)
        menu.exec(self.img_table.viewport().mapToGlobal(pos))

    def _dev_menu(self, pos):
        item = self.dev_tree.itemAt(pos)
        if not item:
            return
        drive_letter = item.data(0, Qt.UserRole)
        menu = QMenu(self)
        if drive_letter == "F":
            menu.addAction("Mount Image...", self.add_image_dialog)
            menu.addAction("Unmount Image", self.unmount_virtual_drive)
            menu.addSeparator()
            menu.addAction("Eject Tray", lambda: sound.play_clip("cdrom_startup1.mp3", 2000))
        elif drive_letter == "D":
            menu.addAction("Eject Tray", lambda: sound.play_clip("cdrom_startup1.mp3", 2000))
            menu.addAction("Disc Properties", self.device_manager)
        menu.exec(self.dev_tree.viewport().mapToGlobal(pos))

    # ---- Wizards ----
    def image_finder(self):
        """Scans C: and E: (Local Storage, My Documents) for disc images."""
        found = []
        for root_dir in (vfs.user_home(), vfs.local_storage()):
            if root_dir.exists():
                for ext in IMAGE_EXTS:
                    found.extend(list(root_dir.rglob(f"*{ext}")))
        count = 0
        for p in found:
            p_str = str(p)
            if p_str not in self.state["images"]:
                self.state["images"].append(p_str)
                count += 1
        _save_state(self.state)
        self._refresh_images()
        dialogs.msgbox(self.desktop, "Image Finder",
                       f"Image Finder scan complete.\nFound {len(found)} disc images ({count} newly added to list).", "info")

    def image_making_wizard(self):
        dialogs.msgbox(self.desktop, "Image Making Wizard",
                       "Image Making Wizard is ready.\nSelect a disc or folder on your system to dump into an ISO or MDF/MDS image.", "info")

    def image_burning_wizard(self):
        row = self.img_table.currentRow()
        if row >= 0:
            p = Path(self.img_table.item(row, 0).data(Qt.UserRole))
            self._burn_image_file(p)
        else:
            self.add_image_dialog()

    def _burn_image_file(self, path):
        dialogs.msgbox(self.desktop, "Image Burning Wizard",
                       f"Burning '{path.name}' to (D:) ATAPI CD-RW at 48x (RAW DAO mode with RMPS Emulation).\n"
                       "Ready to burn.", "info")

    def copy_wizard(self):
        dialogs.msgbox(self.desktop, "Copy Wizard", "Copy Wizard: Copy directly from Drive D: to disc image or second writer.", "info")

    def device_manager(self):
        dialogs.msgbox(self.desktop, "CD/DVD Device Manager",
                       "Drive: (D:) ATAPI CD-RW 52x32x52\n"
                       "Firmware: 1.04\n"
                       "Supported Reading: CD-ROM, CD-R, CD-RW, DVD-ROM\n"
                       "Supported Writing: CD-R, CD-RW (Burn-Proof Enabled)\n\n"
                       "Drive: (F:) [AXV] CD/DVD-ROM (Alcohol Virtual SCSI)\n"
                       "Emulation: Sub-Channel, SecuROM, SafeDisc 2/3, LaserLock, RMPS", "info")

    def erase_wizard(self):
        from .nero import VIRTUAL_CD_DIR
        def on_btn(b):
            if b == "Erase":
                if VIRTUAL_CD_DIR.exists():
                    shutil.rmtree(VIRTUAL_CD_DIR, ignore_errors=True)
                sound.play_clip("cdrom_startup1.mp3", 3000)
                dialogs.msgbox(self.desktop, "Alcohol 120%", "Erase Wizard: Disc in drive D: erased successfully.", "info")
        dialogs.msgbox(self.desktop, "Erase Wizard", "Erase CD-RW in drive (D:) ATAPI CD-RW?", "question", ("Erase", "Cancel"), on_btn)

    def virtual_drive_settings(self):
        vd = self.state.get("virtual_drives", 1)
        dialogs.msgbox(self.desktop, "Virtual Drive Settings",
                       f"Virtual Drives enabled: {vd}\nVirtual Drive Letter: (F:)\n"
                       "Auto-mount images at startup: Enabled", "info")

    def emulation_settings(self):
        dialogs.msgbox(self.desktop, "Emulation Settings",
                       "Emulation Options:\n"
                       "✓ RMPS (Recordable Media Physical Signature)\n"
                       "✓ SafeDisc 2/3 Sub-Channel Emulation\n"
                       "✓ SecuROM Data Position Emulation\n"
                       "✓ LaserLock Bad Sector Emulation", "info")

    def recording_preferences(self):
        dialogs.msgbox(self.desktop, "Recording Preferences",
                       "Memory Buffer Size: 128 MB\n"
                       "Sound Notifications: Enabled\n"
                       "Write Method: RAW DAO / SAO+SUB", "info")

    def about_alcohol(self):
        dialogs.msgbox(self.desktop, "About Alcohol 120%",
                       "Alcohol 120% Version 1.9.5 (Build 3105)\n"
                       "Copyright (C) 2002-2005 Alcohol Soft development team\n"
                       "Licensed to: ClaudeXP Registered User", "info")


_frame = None


def open_alcohol(desktop):
    global _frame
    from shiboken6 import isValid
    if _frame is not None and isValid(_frame):
        desktop.open_window(_frame)
        return _frame
    body = AlcoholWindow(desktop)
    _frame = XPWindow(desktop, "Alcohol 120%", body, alcohol_icon(), (800, 520))
    body.frame = _frame
    desktop.open_window(_frame)
    return _frame

