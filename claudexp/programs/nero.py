"""Nero Burning ROM: classic CD/DVD burning software for ClaudeXP."""
import os
import shutil
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
                               QTableWidgetItem, QTabWidget, QToolBar,
                               QTreeWidget, QTreeWidgetItem, QVBoxLayout,
                               QWidget)

from .. import sound
from ..explorer import dialogs, vfs
from ..paths import DATA, ROOT
from ..wm import XPWindow
from .notepad import MENU_STYLE
from .opendialog import places
from .utility_icons import burn_icon, nero_icon

VIRTUAL_CD_DIR = DATA / "virtual_disc_d"


def _fmt_size(num_bytes):
    if num_bytes < 1024:
        return f"{num_bytes} B"
    elif num_bytes < 1024 * 1024:
        return f"{num_bytes / 1024:.1f} KB"
    elif num_bytes < 1024 * 1024 * 1024:
        return f"{num_bytes / (1024 * 1024):.1f} MB"
    return f"{num_bytes / (1024 * 1024 * 1024):.2f} GB"


class CapacityRuler(QWidget):
    """Classic Nero Capacity meter showing 650 MB (74 min) yellow line and 700 MB red line."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(34)
        self.used_bytes = 0
        self.max_bytes = 800 * 1024 * 1024      # 800 MB ruler
        self.cd74_bytes = 650 * 1024 * 1024     # 650 MB (74 min)
        self.cd80_bytes = 700 * 1024 * 1024     # 700 MB (80 min)

    def set_used_bytes(self, num_bytes):
        self.used_bytes = num_bytes
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        # Background
        p.fillRect(0, 0, w, h, QColor("#D8D4C8"))
        p.setPen(QPen(QColor("#808080"), 1))
        p.drawRect(0, 0, w - 1, h - 1)

        # Meter area
        meter_y = 12
        meter_h = 16
        meter_w = w - 16
        p.fillRect(8, meter_y, meter_w, meter_h, QColor("#101010"))

        # Progress fill
        ratio = min(1.0, max(0.0, self.used_bytes / self.max_bytes))
        fill_w = int(meter_w * ratio)

        if fill_w > 0:
            fill_rect = QRectF(8, meter_y, fill_w, meter_h)
            fg = QLinearGradient(0, meter_y, 0, meter_y + meter_h)
            if self.used_bytes > self.cd80_bytes:
                fg.setColorAt(0.0, QColor("#FF6060"))
                fg.setColorAt(1.0, QColor("#D01010"))
            elif self.used_bytes > self.cd74_bytes:
                fg.setColorAt(0.0, QColor("#FFE060"))
                fg.setColorAt(1.0, QColor("#D0A010"))
            else:
                fg.setColorAt(0.0, QColor("#60E060"))
                fg.setColorAt(1.0, QColor("#209020"))
            p.fillRect(fill_rect, fg)

        # Scale tick marks & labels
        p.setFont(QFont("Tahoma", 7))
        p.setPen(QColor("#404040"))
        ticks = [
            (0, "0MB"), (100, "100"), (200, "200"), (300, "300"), (400, "400"),
            (500, "500"), (600, "600"), (650, "650MB"), (700, "700MB"), (800, "800MB")
        ]
        for mb, label in ticks:
            x = 8 + int(meter_w * (mb / 800.0))
            p.drawLine(x, 1, x, 6)
            p.drawText(x - 12, 10, 24, 10, Qt.AlignCenter, label)

        # Markers: Yellow line at 650 MB (74 min), Red line at 700 MB (80 min)
        x74 = 8 + int(meter_w * (650.0 / 800.0))
        p.setPen(QPen(QColor("#FFCC00"), 2))
        p.drawLine(x74, meter_y - 2, x74, meter_y + meter_h + 2)

        x80 = 8 + int(meter_w * (700.0 / 800.0))
        p.setPen(QPen(QColor("#FF2020"), 2))
        p.drawLine(x80, meter_y - 2, x80, meter_y + meter_h + 2)

        # Text in bottom center
        mb_used = self.used_bytes / (1024 * 1024)
        minutes = int(mb_used / 700.0 * 80.0)
        seconds = int((mb_used / 700.0 * 80.0 * 60) % 60)
        p.setFont(QFont("Tahoma", 8, QFont.Bold))
        p.setPen(QColor("white"))
        stat_text = f"{mb_used:.1f} MB / 700 MB ({minutes:02d}:{seconds:02d})"
        p.drawText(QRectF(8, meter_y, meter_w, meter_h), Qt.AlignCenter, stat_text)
        p.end()


class BurnProgressDialog(QWidget):
    """Nero Burn Progress dialog with animated write stats, buffer meters, and log."""

    def __init__(self, desktop, files, disc_name, recorder_name, speed, on_finished):
        super().__init__()
        self.desktop = desktop
        self.files = files
        self.disc_name = disc_name
        self.recorder_name = recorder_name
        self.speed = speed
        self.on_finished = on_finished
        self.frame = None

        self.setWindowTitle(f"Writing to CD - {recorder_name}")
        self.setFixedSize(540, 420)
        self.setStyleSheet("""
            QWidget { background: #ECE9D8; font-family: Tahoma; font-size: 11px; }
            QProgressBar { border: 1px solid #7F9DB9; background: white; text-align: center; height: 16px; }
            QProgressBar::chunk { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #86C458, stop:1 #4E9525); }
            QListWidget { background: white; border: 1px solid #7F9DB9; }
            QPushButton { min-height: 22px; min-width: 75px; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Header with Nero burning flame icon and status
        top_row = QHBoxLayout()
        flame_lbl = QLabel()
        flame_lbl.setPixmap(nero_icon(48).pixmap(48, 48))
        top_row.addWidget(flame_lbl)

        info_v = QVBoxLayout()
        self.status_lbl = QLabel(f"Preparing to write compilation '{disc_name}' at {speed}...")
        self.status_lbl.setFont(QFont("Tahoma", 9, QFont.Bold))
        info_v.addWidget(self.status_lbl)
        self.detail_lbl = QLabel(f"Target: {recorder_name} • Buffer Protection: Burn-Proof Enabled")
        info_v.addWidget(self.detail_lbl)
        top_row.addLayout(info_v, 1)
        layout.addLayout(top_row)

        # Progress bars
        bars_box = QGroupBox("Progress")
        bars_v = QVBoxLayout(bars_box)
        bars_v.setContentsMargins(10, 8, 10, 8)
        bars_v.setSpacing(6)

        bars_v.addWidget(QLabel("Track Progress:"))
        self.track_bar = QProgressBar()
        self.track_bar.setRange(0, 100)
        self.track_bar.setValue(0)
        bars_v.addWidget(self.track_bar)

        bars_v.addWidget(QLabel("Total Progress:"))
        self.total_bar = QProgressBar()
        self.total_bar.setRange(0, 100)
        self.total_bar.setValue(0)
        bars_v.addWidget(self.total_bar)

        buf_row = QHBoxLayout()
        buf_row.addWidget(QLabel("Used Read Buffer:"))
        self.read_buf = QProgressBar()
        self.read_buf.setRange(0, 100)
        self.read_buf.setValue(98)
        buf_row.addWidget(self.read_buf)

        buf_row.addWidget(QLabel("Recorder Buffer:"))
        self.rec_buf = QProgressBar()
        self.rec_buf.setRange(0, 100)
        self.rec_buf.setValue(99)
        buf_row.addWidget(self.rec_buf)
        bars_v.addLayout(buf_row)

        layout.addWidget(bars_box)

        # Log box
        layout.addWidget(QLabel("Events:"))
        self.log_list = QListWidget()
        layout.addWidget(self.log_list, 1)

        # Bottom buttons
        btn_row = QHBoxLayout()
        self.verify_check = QLabel("Verify written data: Enabled")
        btn_row.addWidget(self.verify_check)
        btn_row.addStretch()
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self._close)
        btn_row.addWidget(self.cancel_btn)
        layout.addLayout(btn_row)

        self.step = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(150)

    def _log(self, msg):
        t_str = time.strftime("%H:%M:%S")
        self.log_list.addItem(f"{t_str}  {msg}")
        self.log_list.scrollToBottom()

    def _tick(self):
        self.step += 1
        pct = min(100, int((self.step / 35.0) * 100))
        self.track_bar.setValue(pct)
        self.total_bar.setValue(pct)

        # Fluctuating buffers
        import random
        self.read_buf.setValue(random.randint(95, 100))
        self.rec_buf.setValue(random.randint(96, 100))

        if self.step == 1:
            self._log("Caching files to temporary storage image...")
        elif self.step == 4:
            self._log(f"Burn process started at {self.speed} (DAO Mode)")
            sound.play_clip("cdrom_startup1.mp3", 3000)
        elif self.step == 8:
            self._log("Writing lead-in at 48x (7,200 KB/s)...")
        elif self.step == 15:
            self._log(f"Writing data track: '{self.disc_name}'...")
            self.status_lbl.setText(f"Writing data at {self.speed} (7,200 KB/s)...")
        elif self.step == 26:
            self._log("Writing lead-out...")
            self.status_lbl.setText("Writing lead-out...")
        elif self.step == 31:
            self._log("Closing session and finalizing disc...")
        elif self.step >= 35:
            self.timer.stop()
            self._log("Verifying written data against compilation...")
            self._log("Data verification successful. 0 errors found.")
            self._log(f"Burn process completed successfully at {self.speed}!")
            self.status_lbl.setText("Burn process completed successfully!")
            self.detail_lbl.setText("Disc finalized. Ready for reading in drive.")
            sound.play("default")
            self.cancel_btn.setText("Done")
            self.cancel_btn.clicked.disconnect()
            self.cancel_btn.clicked.connect(self._close)
            if self.on_finished:
                self.on_finished()

    def _close(self):
        self.timer.stop()
        if self.frame is not None:
            self.desktop.close_window(self.frame)


class NewCompilationDialog(QWidget):
    """Nero New Compilation wizard with CD/DVD format presets and tabs."""

    def __init__(self, desktop, on_create):
        super().__init__()
        self.desktop = desktop
        self.on_create = on_create
        self.frame = None
        self.setWindowTitle("New Compilation")
        self.setFixedSize(540, 400)
        self.setStyleSheet("""
            QWidget { background: #ECE9D8; font-family: Tahoma; font-size: 11px; }
            QTabWidget::pane { border: 1px solid #7F9DB9; top: -1px; background: #ECE9D8; }
            QTabBar::tab { background: #E0DEC8; border: 1px solid #7F9DB9; padding: 4px 10px; margin-right: 2px; }
            QTabBar::tab:selected { background: #ECE9D8; border-bottom-color: #ECE9D8; font-weight: bold; }
            QPushButton { min-height: 22px; min-width: 75px; }
            QListWidget { background: white; border: 1px solid #7F9DB9; }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # Left: Compilation types list
        left_v = QVBoxLayout()
        left_v.addWidget(QLabel("Disc Type:"))
        self.types_list = QListWidget()
        self.types_list.setFixedWidth(140)
        items = [
            ("CD-ROM (ISO)", QStyle.SP_DriveCDIcon),
            ("Audio CD", QStyle.SP_MediaPlay),
            ("Mixed Mode CD", QStyle.SP_DriveCDIcon),
            ("CD Copy", QStyle.SP_FileDialogDetailedView),
            ("Video CD (VCD)", QStyle.SP_MediaPlay),
            ("Super Video CD", QStyle.SP_MediaPlay),
            ("DVD-ROM (ISO)", QStyle.SP_DriveDVDIcon),
        ]
        style = self.style()
        for title, icon_kind in items:
            it = QListWidgetItem(style.standardIcon(icon_kind), title)
            self.types_list.addItem(it)
        self.types_list.setCurrentRow(0)
        left_v.addWidget(self.types_list, 1)
        layout.addLayout(left_v)

        # Right: Tabs
        right_v = QVBoxLayout()
        tabs = QTabWidget()

        # Tab: Multisession
        multi_page = QWidget()
        mv = QVBoxLayout(multi_page)
        mv.addWidget(QRadioButton("Start Multisession disc"))
        mv.addWidget(QRadioButton("Continue Multisession disc"))
        no_multi = QRadioButton("No Multisession")
        no_multi.setChecked(True)
        mv.addWidget(no_multi)
        mv.addStretch()
        tabs.addTab(multi_page, "Multisession")

        # Tab: ISO
        iso_page = QWidget()
        iv = QVBoxLayout(iso_page)
        iv.addWidget(QLabel("File name length: Max. of 31 chars (ISO Level 2)"))
        iv.addWidget(QLabel("Format: Mode 1"))
        iv.addWidget(QLabel("Character set: ISO 9660 + Joliet (Unicode)"))
        iv.addStretch()
        tabs.addTab(iso_page, "ISO")

        # Tab: Label
        label_page = QWidget()
        lv = QVBoxLayout(label_page)
        lv.addWidget(QLabel("Volume label (Disc Name):"))
        self.vol_edit = QLineEdit("NEW_DISC")
        lv.addWidget(self.vol_edit)
        lv.addWidget(QLabel("System Identifier: Win32"))
        lv.addWidget(QLabel("Application: Nero Burning ROM 6.6"))
        lv.addStretch()
        tabs.addTab(label_page, "Label")

        # Tab: Burn
        burn_page = QWidget()
        bv = QVBoxLayout(burn_page)
        bv.addWidget(QLabel("Write Speed:"))
        self.speed_combo = QComboBox()
        self.speed_combo.addItems(["52x (7,800 KB/s)", "48x (7,200 KB/s)", "32x (4,800 KB/s)", "24x (3,600 KB/s)", "16x (2,400 KB/s)", "8x (1,200 KB/s)"])
        bv.addWidget(self.speed_combo)
        bv.addWidget(QLabel("Write Method: DAO (Disc-At-Once)"))
        bv.addWidget(QLabel("Buffer Underrun Protection: Burn-Proof (Enabled)"))
        bv.addStretch()
        tabs.addTab(burn_page, "Burn")

        right_v.addWidget(tabs, 1)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        new_btn = QPushButton("New")
        new_btn.setDefault(True)
        new_btn.clicked.connect(self._accept)
        btn_row.addWidget(new_btn)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self._close)
        btn_row.addWidget(cancel_btn)
        right_v.addLayout(btn_row)

        layout.addLayout(right_v, 1)

    def _accept(self):
        disc_type = self.types_list.currentItem().text() if self.types_list.currentItem() else "CD-ROM (ISO)"
        disc_label = self.vol_edit.text().strip() or "NEW_DISC"
        speed = self.speed_combo.currentText()
        if self.frame:
            self.desktop.close_window(self.frame)
        self.on_create(disc_type, disc_label, speed)

    def _close(self):
        if self.frame:
            self.desktop.close_window(self.frame)


class NeroWindow(QWidget):
    """Nero Burning ROM 6 main window with dual-pane compilation/browser and capacity ruler."""

    def __init__(self, desktop):
        super().__init__()
        self.desktop = desktop
        self.frame = None
        self.disc_name = "NEW_DISC"
        self.disc_type = "CD-ROM (ISO)"
        self.write_speed = "48x (7,200 KB/s)"
        self.compilation_files = []   # list of (name, size, Path or None, is_dir)

        self.setWindowTitle("Nero Burning ROM")
        self.setMinimumSize(480, 280)
        self.setStyleSheet(MENU_STYLE + """
            QWidget#nero { background: #ECE9D8; }
            QToolBar { background: #ECE9D8; border-bottom: 1px solid #ACA899; spacing: 4px; padding: 2px; }
            QToolButton { font-family: Tahoma; font-size: 11px; padding: 3px 6px; }
            QToolButton:hover { background: #B6BDD2; border: 1px solid #0A246A; }
            QSplitter::handle { background: #D4D0C8; }
            QTreeWidget, QListWidget { background: white; border: 1px solid #7F9DB9; font-family: Tahoma; font-size: 11px; }
            QHeaderView::section { background: #ECE9D8; border: 1px solid #ACA899; padding: 2px; font-size: 11px; font-weight: normal; }
            QLabel#status { background: #ECE9D8; border-top: 1px solid #ACA899; padding: 2px 4px; font-family: Tahoma; font-size: 11px; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toolbar
        tb = QToolBar()
        tb.setIconSize(QSize(20, 20))
        style = self.style()

        act_new = tb.addAction(style.standardIcon(QStyle.SP_FileIcon), "New", self.new_compilation)
        act_open = tb.addAction(style.standardIcon(QStyle.SP_DialogOpenButton), "Open", self.open_compilation)
        act_save = tb.addAction(style.standardIcon(QStyle.SP_DialogSaveButton), "Save", self.save_compilation)
        tb.addSeparator()

        act_mkdir = tb.addAction(style.standardIcon(QStyle.SP_DirIcon), "New Folder", self.add_folder)
        act_del = tb.addAction(style.standardIcon(QStyle.SP_TrashIcon), "Delete", self.delete_selected)
        tb.addSeparator()

        act_info = tb.addAction(style.standardIcon(QStyle.SP_MessageBoxInformation), "Disc Info", self.disc_info)
        act_erase = tb.addAction(style.standardIcon(QStyle.SP_DialogResetButton), "Erase Disc", self.erase_disc)
        tb.addSeparator()

        tb.addWidget(QLabel(" Recorder: "))
        self.recorder_combo = QComboBox()
        self.recorder_combo.addItems(["[D:] ATAPI CD-R/RW 52x24x52", "[Image Recorder] Virtual ISO Writer"])
        tb.addWidget(self.recorder_combo)

        tb.addWidget(QLabel(" Speed: "))
        self.speed_combo = QComboBox()
        self.speed_combo.addItems(["52x (7,800 KB/s)", "48x (7,200 KB/s)", "32x (4,800 KB/s)", "24x (3,600 KB/s)", "16x (2,400 KB/s)"])
        tb.addWidget(self.speed_combo)

        tb.addSeparator()
        self.burn_btn = QPushButton(" Burn Now")
        self.burn_btn.setIcon(burn_icon(18))
        self.burn_btn.setStyleSheet("QPushButton { font-weight: bold; color: #B02000; padding: 3px 12px; }")
        self.burn_btn.clicked.connect(self.burn_now)
        tb.addWidget(self.burn_btn)

        layout.addWidget(tb)

        # Splitter: Left (Compilation) / Right (File Browser)
        splitter = QSplitter(Qt.Horizontal)

        # Left: Compilation Pane
        left_box = QWidget()
        left_v = QVBoxLayout(left_box)
        left_v.setContentsMargins(4, 4, 2, 4)
        left_head = QLabel("Disc Compilation Content:")
        left_head.setFont(QFont("Tahoma", 9, QFont.Bold))
        left_v.addWidget(left_head)

        self.comp_tree = QTreeWidget()
        self.comp_tree.setHeaderLabels(["Name", "Size", "Type", "Modified"])
        self.comp_tree.header().resizeSection(0, 180)
        self.comp_tree.header().resizeSection(1, 80)
        self.comp_tree.header().resizeSection(2, 80)
        self.comp_tree.setSelectionMode(QAbstractItemView.ExtendedSelection)
        left_v.addWidget(self.comp_tree, 1)
        splitter.addWidget(left_box)

        # Right: File Browser Pane
        right_box = QWidget()
        right_v = QVBoxLayout(right_box)
        right_v.setContentsMargins(2, 4, 4, 4)

        browse_head = QHBoxLayout()
        browse_lbl = QLabel("File Browser - Look in:")
        browse_lbl.setFont(QFont("Tahoma", 9, QFont.Bold))
        browse_head.addWidget(browse_lbl)

        self.place_combo = QComboBox()
        for label, path in places():
            self.place_combo.addItem(style.standardIcon(QStyle.SP_DirIcon), label, str(path))
        self.place_combo.currentIndexChanged.connect(self._browse_dir_changed)
        browse_head.addWidget(self.place_combo, 1)

        self.up_btn = QPushButton("Up")
        self.up_btn.setFixedWidth(40)
        self.up_btn.clicked.connect(self._browse_up)
        browse_head.addWidget(self.up_btn)
        right_v.addLayout(browse_head)

        self.browser_list = QListWidget()
        self.browser_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.browser_list.itemDoubleClicked.connect(self._browser_double_click)
        right_v.addWidget(self.browser_list, 1)

        add_row = QHBoxLayout()
        add_btn = QPushButton("<- Add to Compilation")
        add_btn.setStyleSheet("font-weight: bold;")
        add_btn.clicked.connect(self.add_selected_from_browser)
        add_row.addWidget(add_btn)
        add_row.addStretch()
        right_v.addLayout(add_row)

        splitter.addWidget(right_box)
        splitter.setSizes([420, 360])
        layout.addWidget(splitter, 1)

        # Capacity Ruler
        self.ruler = CapacityRuler()
        layout.addWidget(self.ruler)

        # Status Bar
        self.status = QLabel("Ready • Track 01 • Mode 1 (ISO 9660)")
        self.status.setObjectName("status")
        layout.addWidget(self.status)

        # Initialize
        self.current_browse_dir = Path(self.place_combo.currentData()) if self.place_combo.count() else vfs.user_home()
        self._populate_browser()
        self._refresh_compilation_view()

    # ---- Browser handling ----
    def _browse_dir_changed(self):
        data = self.place_combo.currentData()
        if data:
            self.current_browse_dir = Path(data)
            self._populate_browser()

    def _browse_up(self):
        if self.current_browse_dir and self.current_browse_dir.parent.exists():
            self.current_browse_dir = self.current_browse_dir.parent
            self._populate_browser()

    def _populate_browser(self):
        self.browser_list.clear()
        if not self.current_browse_dir or not self.current_browse_dir.exists():
            return
        style = self.style()
        try:
            for p in sorted(self.current_browse_dir.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
                if p.name.startswith("."):
                    continue
                icon = style.standardIcon(QStyle.SP_DirIcon) if p.is_dir() else style.standardIcon(QStyle.SP_FileIcon)
                sz_str = f" [{_fmt_size(p.stat().st_size)}]" if p.is_file() else " [Folder]"
                it = QListWidgetItem(icon, f"{p.name}{sz_str}")
                it.setData(Qt.UserRole, str(p))
                self.browser_list.addItem(it)
        except OSError:
            pass

    def _browser_double_click(self, item):
        path_str = item.data(Qt.UserRole)
        if not path_str:
            return
        p = Path(path_str)
        if p.is_dir():
            self.current_browse_dir = p
            self._populate_browser()
        else:
            self._add_path_to_comp(p)

    def add_selected_from_browser(self):
        for item in self.browser_list.selectedItems():
            path_str = item.data(Qt.UserRole)
            if path_str:
                self._add_path_to_comp(Path(path_str))

    def _add_path_to_comp(self, path):
        if path.is_file():
            size = path.stat().st_size
            self.compilation_files.append((path.name, size, path, False))
        elif path.is_dir():
            size = sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
            self.compilation_files.append((path.name, size, path, True))
        self._refresh_compilation_view()

    # ---- Compilation management ----
    def _refresh_compilation_view(self):
        self.comp_tree.clear()
        style = self.style()

        # Root disc item
        root_it = QTreeWidgetItem(self.comp_tree)
        root_it.setText(0, f"CD ({self.disc_name})")
        root_it.setIcon(0, style.standardIcon(QStyle.SP_DriveCDIcon))
        root_it.setExpanded(True)

        total_bytes = 0
        for name, sz, path, is_dir in self.compilation_files:
            total_bytes += sz
            item = QTreeWidgetItem(root_it)
            item.setText(0, name)
            item.setText(1, _fmt_size(sz))
            item.setText(2, "Folder" if is_dir else "File")
            mtime = time.strftime("%Y-%m-%d %H:%M", time.localtime(path.stat().st_mtime)) if path and path.exists() else "-"
            item.setText(3, mtime)
            item.setIcon(0, style.standardIcon(QStyle.SP_DirIcon if is_dir else QStyle.SP_FileIcon))
            item.setData(0, Qt.UserRole, name)

        self.ruler.set_used_bytes(total_bytes)
        self.status.setText(f"Compilation: {len(self.compilation_files)} items • Total: {_fmt_size(total_bytes)} • Format: {self.disc_type}")

    def add_folder(self):
        folder_name = f"New Folder {len([f for f in self.compilation_files if f[3]]) + 1}"
        self.compilation_files.append((folder_name, 0, None, True))
        self._refresh_compilation_view()

    def delete_selected(self):
        selected_names = {it.data(0, Qt.UserRole) for it in self.comp_tree.selectedItems()}
        self.compilation_files = [f for f in self.compilation_files if f[0] not in selected_names]
        self._refresh_compilation_view()

    def new_compilation(self):
        def on_create(disc_type, disc_name, speed):
            self.disc_type = disc_type
            self.disc_name = disc_name
            self.write_speed = speed
            self.compilation_files.clear()
            self._refresh_compilation_view()
            if self.frame:
                self.frame.setWindowTitle(f"Nero Burning ROM - [{disc_name}]")

        wiz = NewCompilationDialog(self.desktop, on_create)
        win = XPWindow(self.desktop, "New Compilation", wiz, nero_icon(), (540, 400), buttons=("close",))
        wiz.frame = win
        win.fit_fixed_content()
        try:
            area = self.desktop.work_area()
            win.move(area.center() - win.rect().center())
            win.placed = True
        except Exception:
            pass
        self.desktop.open_window(win)

    def open_compilation(self):
        dialogs.msgbox(self.desktop, "Nero Burning ROM", "Open Compilation (.nrg / .iso) is ready. Use 'Add' to import files.", "info")

    def save_compilation(self):
        dialogs.msgbox(self.desktop, "Nero Burning ROM", f"Compilation saved as '{self.disc_name}.nrg'.", "info")

    def disc_info(self):
        rec = self.recorder_combo.currentText()
        used = sum(f[1] for f in self.compilation_files)
        dialogs.msgbox(self.desktop, "Disc Information",
                       f"Recorder: {rec}\n"
                       f"Disc Status: CD-R (Blank / Rewritable)\n"
                       f"Available Capacity: 703.1 MB (80:00:00)\n"
                       f"Compilation Size: {_fmt_size(used)}\n"
                       f"Sessions: 1\n"
                       f"Burn-Proof / Seamless Link: Supported", "info")

    def erase_disc(self):
        def on_btn(b):
            if b == "Erase":
                if VIRTUAL_CD_DIR.exists():
                    shutil.rmtree(VIRTUAL_CD_DIR, ignore_errors=True)
                sound.play_clip("cdrom_startup1.mp3", 3000)
                dialogs.msgbox(self.desktop, "Nero Burning ROM", "Disc in drive D: was erased successfully.", "info")

        dialogs.msgbox(self.desktop, "Erase Rewritable Disc",
                       "Do you want to quick-erase the rewritable CD in drive [D:]?\n"
                       "All existing data on the disc will be permanently erased.",
                       "question", ("Erase", "Cancel"), on_btn)

    def burn_now(self):
        if not self.compilation_files:
            dialogs.msgbox(self.desktop, "Nero Burning ROM",
                           "The compilation is empty.\nPlease add files or folders to the compilation before burning.",
                           "warning")
            return

        rec = self.recorder_combo.currentText()
        speed = self.speed_combo.currentText()

        def on_done():
            # Actually burn files to virtual CD drive D:
            try:
                VIRTUAL_CD_DIR.mkdir(parents=True, exist_ok=True)
                for name, sz, src_path, is_dir in self.compilation_files:
                    target = VIRTUAL_CD_DIR / name
                    if src_path and src_path.exists():
                        if is_dir:
                            shutil.copytree(src_path, target, dirs_exist_ok=True)
                        else:
                            shutil.copy2(src_path, target)
                    else:
                        if is_dir:
                            target.mkdir(parents=True, exist_ok=True)
                        else:
                            target.write_bytes(b"NERO_CD_DATA")
            except Exception:
                pass

        burn_win = BurnProgressDialog(self.desktop, self.compilation_files, self.disc_name, rec, speed, on_done)
        win = XPWindow(self.desktop, f"Writing to CD - {rec}", burn_win, nero_icon(), (540, 420), buttons=("close",))
        burn_win.frame = win
        win.fit_fixed_content()
        try:
            area = self.desktop.work_area()
            win.move(area.center() - win.rect().center())
            win.placed = True
        except Exception:
            pass
        self.desktop.open_window(win)


_frame = None


def open_nero(desktop):
    global _frame
    from shiboken6 import isValid
    if _frame is not None and isValid(_frame):
        desktop.open_window(_frame)
        return _frame
    body = NeroWindow(desktop)
    _frame = XPWindow(desktop, "Nero Burning ROM", body, nero_icon(), (780, 520))
    body.frame = _frame
    desktop.open_window(_frame)
    return _frame

