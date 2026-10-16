"""Local desktop shortcuts, drive browsing, and a recoverable Recycle Bin."""

from __future__ import annotations

from datetime import datetime
import json
import os
from pathlib import Path
import shutil
from tempfile import NamedTemporaryFile
from uuid import uuid4

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView, QHBoxLayout, QInputDialog, QLabel, QListWidget,
    QListWidgetItem, QMenu, QMessageBox, QPushButton, QStackedWidget,
    QStyle, QTableWidget, QTableWidgetItem, QToolButton, QVBoxLayout, QWidget,
)
from PySide6.QtCore import QObject

from .config import STORAGE_ROOT, USER_DOCUMENTS

DESKTOP_ASSETS = Path(__file__).resolve().parent.parent / "assets" / "desktop"
RECYCLE_ROOT = STORAGE_ROOT / "UserData" / "Recycle Bin"
RECYCLE_INDEX = RECYCLE_ROOT / "index.json"
DRIVES = (
    ("D:", "CD Rom Drive", DESKTOP_ASSETS / "CD Rom Drive.ico", STORAGE_ROOT / "Media" / "CD-ROM", False),
    ("E:", "DVD Drive", DESKTOP_ASSETS / "DVD Drive.ico", STORAGE_ROOT / "Media" / "Movies", False),
    ("A:", "Floppy Drive", DESKTOP_ASSETS / "Floppy Drive.png", STORAGE_ROOT / "Drives" / "Floppy", False),
    ("F:", "External HD", DESKTOP_ASSETS / "External HD.ico", STORAGE_ROOT / "External HD", False),
    ("C:", "Internal HD", DESKTOP_ASSETS / "Internal HD.ico", STORAGE_ROOT, True),
)


class RecycleBinError(RuntimeError):
    pass


class RecycleBinStore(QObject):
    """Move eligible user files into local trash and restore them without overwriting."""

    changed = Signal(bool)
    protected_roots = (
        STORAGE_ROOT / "System",
        STORAGE_ROOT / "Runtime",
        STORAGE_ROOT / "Models",
        STORAGE_ROOT / "Profiles",
        STORAGE_ROOT / "UserData" / "Messenger",
        RECYCLE_ROOT,
    )
    allowed_roots = (
        USER_DOCUMENTS,
        STORAGE_ROOT / "Media",
        STORAGE_ROOT / "ROMs",
        STORAGE_ROOT / "External HD",
        STORAGE_ROOT / "Drives",
    )

    def __init__(self, parent=None, *, bin_root=RECYCLE_ROOT, allowed_roots=None):
        super().__init__(parent)
        self.bin_root = Path(bin_root)
        self.index_path = self.bin_root / "index.json"
        self.items_root = self.bin_root / "items"
        self.allowed_roots = tuple(Path(root) for root in (allowed_roots or self.allowed_roots))

    def _safe_path(self, path, roots):
        candidate = Path(path)
        if candidate.is_symlink():
            raise RecycleBinError("Symbolic links cannot be moved to the Recycle Bin.")
        resolved = candidate.resolve(strict=False)
        if any(resolved == Path(r).resolve() or Path(r).resolve() in resolved.parents for r in self.protected_roots):
            raise RecycleBinError("Windows, profile, model, chat, and Recycle Bin data is protected.")
        if not any(resolved == Path(root).resolve() or Path(root).resolve() in resolved.parents for root in roots):
            raise RecycleBinError("Only files in personal Documents, Media, ROMs, or removable drives can be moved.")
        return resolved

    def _write_index(self, index):
        self.bin_root.mkdir(parents=True, exist_ok=True)
        try:
            with NamedTemporaryFile("w", encoding="utf-8", dir=self.bin_root, delete=False) as stream:
                json.dump(index, stream, ensure_ascii=False, indent=2)
                stream.flush()
                os.fsync(stream.fileno())
                temporary = Path(stream.name)
            os.replace(temporary, self.index_path)
        except OSError as exc:
            try:
                temporary.unlink(missing_ok=True)
            except (UnboundLocalError, OSError):
                pass
            raise RecycleBinError(f"Could not save Recycle Bin information: {exc}") from exc

    def entries(self):
        if not self.index_path.exists():
            return []
        try:
            data = json.loads(self.index_path.read_text(encoding="utf-8"))
            if not isinstance(data, list) or not all(
                isinstance(entry, dict) and set(("id", "name", "original", "deleted")) <= entry.keys()
                for entry in data
            ):
                raise ValueError("Unexpected Recycle Bin index format.")
            for entry in data:
                entry_id = str(entry["id"])
                if not entry_id.isalnum():
                    raise ValueError("Invalid Recycle Bin item ID.")
            return data
        except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
            raise RecycleBinError(f"The Recycle Bin index could not be read: {exc}") from exc

    def move_to_bin(self, path):
        path = self._safe_path(path, self.allowed_roots)
        if not path.exists():
            raise RecycleBinError(f"This item no longer exists: {path.name}")
        self.bin_root.mkdir(parents=True, exist_ok=True)
        entry_id = uuid4().hex
        stored = self.items_root / entry_id
        stored.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "id": entry_id,
            "name": path.name,
            "original": str(path),
            "deleted": datetime.now().astimezone().isoformat(timespec="seconds"),
        }
        entries = self.entries()
        try:
            os.replace(path, stored)
        except OSError as exc:
            raise RecycleBinError(f"Could not move {path.name} to the Recycle Bin: {exc}") from exc
        try:
            self._write_index([*entries, entry])
        except RecycleBinError:
            try:
                os.replace(stored, path)
            except OSError as restore_error:
                raise RecycleBinError(
                    f"Index save failed and automatic restore also failed: {restore_error}. "
                    f"The file remains safe in {stored}."
                )
            raise
        self.changed.emit(True)
        return entry

    def restore(self, entry_id):
        entries = self.entries()
        entry = next((item for item in entries if item["id"] == entry_id), None)
        if not entry:
            raise RecycleBinError("That Recycle Bin item no longer exists.")
        original = self._safe_path(entry["original"], self.allowed_roots)
        stored = (self.items_root / entry_id).resolve()
        if not stored.is_relative_to(self.items_root.resolve()) or not stored.exists():
            raise RecycleBinError("The stored Recycle Bin item is missing or invalid.")
        destination = original
        suffix = 2
        while destination.exists():
            destination = original.with_name(f"{original.stem} ({suffix}){original.suffix}")
            suffix += 1
        destination.parent.mkdir(parents=True, exist_ok=True)
        try:
            os.replace(stored, destination)
            self._write_index([item for item in entries if item["id"] != entry_id])
        except OSError as exc:
            if destination.exists() and not original.exists():
                try:
                    os.replace(destination, stored)
                except OSError:
                    pass
            raise RecycleBinError(f"Could not restore {original.name}: {exc}") from exc
        except RecycleBinError:
            if destination.exists() and not original.exists():
                try:
                    os.replace(destination, stored)
                except OSError:
                    pass
            raise
        self.changed.emit(bool(len(entries) > 1))
        return destination

    def empty(self, entry_ids=None):
        entries = self.entries()
        chosen = set(entry_ids) if entry_ids is not None else {entry["id"] for entry in entries}
        kept, errors = [], []
        for entry in entries:
            if entry["id"] not in chosen:
                kept.append(entry)
                continue
            target = (self.items_root / entry["id"]).resolve()
            if not target.is_relative_to(self.items_root.resolve()):
                errors.append(f"Skipped unsafe item {entry['name']}.")
                kept.append(entry)
                continue
            try:
                if target.is_dir():
                    shutil.rmtree(target)
                else:
                    target.unlink(missing_ok=True)
            except OSError as exc:
                errors.append(f"{entry['name']}: {exc}")
                kept.append(entry)
        self._write_index(kept)
        self.changed.emit(bool(kept))
        if errors:
            raise RecycleBinError("Some items could not be permanently deleted:\n" + "\n".join(errors))


class DesktopShortcut(QToolButton):
    openRequested = Signal()

    def __init__(self, label, icon_path, parent=None):
        super().__init__(parent)
        self.setObjectName("desktop-shortcut-" + label.casefold().replace(" ", "-"))
        self.setText(label)
        self.setAccessibleName(label)
        icon = QIcon(str(icon_path))
        if icon.isNull():
            raise FileNotFoundError(f"Required Windows desktop icon is missing: {icon_path}")
        pixmap = QPixmap(str(icon_path))
        if not pixmap.isNull() and max(pixmap.width(), pixmap.height()) < 64:
            icon = QIcon(
                pixmap.scaled(
                    QSize(64, 64),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        self.setIcon(icon)
        self.setIconSize(QSize(64, 64))
        self.setFixedSize(122, 86)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setStyleSheet(
            "QToolButton { color: white; background: transparent; border: 1px solid transparent; "
            "padding: 1px; font-size: 9pt; }"
            "QToolButton:hover, QToolButton:focus { background: rgba(40,105,175,100); "
            "border: 1px solid rgba(195,230,255,210); }"
            "QToolButton::menu-indicator { image: none; }"
        )

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.openRequested.emit()
            event.accept()
            return
        super().mouseDoubleClickEvent(event)


class RecycleBinApp(QWidget):
    changed = Signal()

    def __init__(self, store, parent=None):
        super().__init__(parent)
        self.store = store
        self.store.changed.connect(self.refresh)
        root = QVBoxLayout(self)
        root.addWidget(QLabel("Recycle Bin"))
        root.addWidget(QLabel("Restore items to their original folder, or empty the bin to permanently delete them."))
        self.items = QTableWidget(0, 4)
        self.items.setHorizontalHeaderLabels(("Name", "Original location", "Date deleted", "Type"))
        self.items.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.items.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.items.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.items.horizontalHeader().setStretchLastSection(True)
        self.items.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.items.customContextMenuRequested.connect(self.show_context_menu)
        self.items.itemDoubleClicked.connect(lambda _item: self.restore_selected())
        root.addWidget(self.items, 1)
        buttons = QHBoxLayout()
        self.restore_button = QPushButton("Restore selected")
        self.restore_button.clicked.connect(self.restore_selected)
        self.empty_button = QPushButton("Empty Recycle Bin")
        self.empty_button.clicked.connect(self.empty_bin)
        buttons.addWidget(self.restore_button)
        buttons.addWidget(self.empty_button)
        buttons.addStretch(1)
        root.addLayout(buttons)
        self.refresh()

    def refresh(self):
        entries = self.store.entries()
        self.items.setRowCount(len(entries))
        for row, entry in enumerate(entries):
            source = Path(entry["original"])
            item_type = (
                "Folder" if (self.store.items_root / entry["id"]).is_dir() else "File"
            )
            values = (entry["name"], str(source.parent), entry["deleted"], item_type)
            for col, value in enumerate(values):
                cell = QTableWidgetItem(value)
                if col == 0:
                    cell.setData(Qt.ItemDataRole.UserRole, entry["id"])
                self.items.setItem(row, col, cell)
        self.restore_button.setEnabled(bool(entries))
        self.empty_button.setEnabled(bool(entries))
        self.changed.emit()

    def _selected_ids(self):
        return [
            self.items.item(row, 0).data(Qt.ItemDataRole.UserRole)
            for row in sorted({index.row() for index in self.items.selectionModel().selectedRows()})
        ]

    def restore_selected(self):
        selected = self._selected_ids()
        if not selected:
            return
        try:
            for entry_id in selected:
                self.store.restore(entry_id)
            self.refresh()
        except RecycleBinError as exc:
            QMessageBox.warning(self, "Recycle Bin", str(exc))

    def delete_selected_permanently(self):
        selected = self._selected_ids()
        if not selected:
            return
        answer = QMessageBox.question(
            self, "Delete permanently",
            f"Permanently delete {len(selected)} selected item(s)? This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            self.store.empty(selected)
            self.refresh()
        except RecycleBinError as exc:
            QMessageBox.warning(self, "Recycle Bin", str(exc))

    def empty_bin(self):
        if not self.store.entries():
            return
        answer = QMessageBox.question(
            self, "Empty Recycle Bin",
            "Permanently delete every item in the Recycle Bin? This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            self.store.empty()
            self.refresh()
        except RecycleBinError as exc:
            QMessageBox.warning(self, "Recycle Bin", str(exc))

    def show_context_menu(self, pos):
        menu = QMenu(self)
        restore = menu.addAction("Restore")
        restore.setEnabled(bool(self._selected_ids()))
        restore.triggered.connect(self.restore_selected)
        delete = menu.addAction("Delete permanently")
        delete.setEnabled(bool(self._selected_ids()))
        delete.triggered.connect(self.delete_selected_permanently)
        menu.addSeparator()
        empty = menu.addAction("Empty Recycle Bin")
        empty.setEnabled(self.items.rowCount() > 0)
        empty.triggered.connect(self.empty_bin)
        menu.popup(self.items.viewport().mapToGlobal(pos))


class WindowsComputerApp(QWidget):
    """Computer/drive browser backed only by the simulator's local Storage tree."""

    openFileRequested = Signal(str)
    recycleBinRequested = Signal()

    def __init__(self, recycle_store, window_name="Computer", parent=None):
        super().__init__(parent)
        self.recycle_store = recycle_store
        self.window_name = window_name
        self.drive = None
        self.current_path = None
        self.history = []
        self.ejected = set()
        root = QVBoxLayout(self)
        root.addWidget(QLabel(window_name))
        navigation = QHBoxLayout()
        self.back_button = QPushButton("Back")
        self.back_button.clicked.connect(self.go_back)
        self.up_button = QPushButton("Up")
        self.up_button.clicked.connect(self.go_up)
        self.address = QLabel("Computer")
        self.address.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        navigation.addWidget(self.back_button)
        navigation.addWidget(self.up_button)
        navigation.addWidget(self.address, 1)
        root.addLayout(navigation)
        self.stack = QStackedWidget()
        self.drive_list = QListWidget()
        self.drive_list.setViewMode(QListWidget.ViewMode.IconMode)
        self.drive_list.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.drive_list.setIconSize(QSize(72, 72))
        self.drive_list.setGridSize(QSize(158, 118))
        self.drive_list.itemDoubleClicked.connect(self._open_drive)
        self.drive_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.drive_list.customContextMenuRequested.connect(self._drive_menu)
        self.file_list = QListWidget()
        self.file_list.setViewMode(QListWidget.ViewMode.ListMode)
        self.file_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.file_list.customContextMenuRequested.connect(self._file_menu)
        self.file_list.itemDoubleClicked.connect(self._open_item)
        self.stack.addWidget(self.drive_list)
        self.stack.addWidget(self.file_list)
        root.addWidget(self.stack, 1)
        self._populate_drives()

    def _populate_drives(self):
        self.drive_list.clear()
        for drive, name, icon_path, path, fixed in DRIVES:
            label = f"{name} ({drive})"
            if drive in self.ejected:
                label += " — Ejected"
            item = QListWidgetItem(QIcon(str(icon_path)), label)
            item.setData(Qt.ItemDataRole.UserRole, (drive, name, str(path), fixed))
            item.setToolTip(f"Local simulated drive: {path}")
            self.drive_list.addItem(item)
        self.stack.setCurrentWidget(self.drive_list)
        self.address.setText(self.window_name)
        self.back_button.setEnabled(bool(self.history))
        self.up_button.setEnabled(False)

    def _open_drive(self, item):
        drive, name, path, fixed = item.data(Qt.ItemDataRole.UserRole)
        path = Path(path)
        if drive in self.ejected:
            QMessageBox.information(self, name, "This drive is ejected. Use its menu to reconnect it.")
            return
        if drive in ("D:", "E:", "A:") and not path.exists():
            QMessageBox.information(self, name, "No media is inserted in this drive.")
            return
        if not path.exists():
            try:
                path.mkdir(parents=True, exist_ok=True)
            except OSError as exc:
                QMessageBox.warning(self, name, f"Could not open this drive:\n{exc}")
                return
        self.drive = (drive, name, path, fixed)
        self.current_path = path
        self.history.clear()
        self._show_folder(path)

    def _drive_menu(self, pos):
        item = self.drive_list.itemAt(pos)
        if not item:
            return
        drive, name, path, fixed = item.data(Qt.ItemDataRole.UserRole)
        menu = QMenu(self)
        menu.addAction("Open", lambda: self._open_drive(item))
        menu.addAction("Explore", lambda: self._open_drive(item))
        menu.addSeparator()
        eject = menu.addAction(
            "Insert media" if drive in self.ejected else
            ("Safely Remove" if drive == "F:" else "Eject")
        )
        eject.setEnabled(not fixed)
        eject.triggered.connect(lambda: self._toggle_ejected(drive, item))
        menu.addSeparator()
        menu.addAction("Properties", lambda: self._show_drive_properties(item))
        format_action = menu.addAction("Format…")
        format_action.setEnabled(False)
        format_action.setToolTip("Drive formatting is not implemented; no files will be erased.")
        menu.popup(self.drive_list.viewport().mapToGlobal(pos))

    def _toggle_ejected(self, drive, item):
        if drive in self.ejected:
            self.ejected.remove(drive)
        else:
            self.ejected.add(drive)
        drive_id, name, path, fixed = item.data(Qt.ItemDataRole.UserRole)
        item.setText(f"{name} ({drive_id})" + (" — Ejected" if drive in self.ejected else ""))
        item.setToolTip(
            "Media ejected. Your archived files remain unchanged."
            if drive in self.ejected else f"Local simulated drive: {path}"
        )

    def _show_drive_properties(self, item):
        drive, name, path, fixed = item.data(Qt.ItemDataRole.UserRole)
        media = "Ejected" if drive in self.ejected else ("Present" if Path(path).exists() else "No media inserted")
        QMessageBox.information(
            self, f"{name} Properties",
            f"Drive: {drive}\\\nType: {'Local disk' if fixed else 'Removable'}\nStatus: {media}",
        )

    def _show_folder(self, path):
        self.current_path = Path(path)
        self.file_list.clear()
        try:
            entries = sorted(self.current_path.iterdir(), key=lambda p: (not p.is_dir(), p.name.casefold()))
        except OSError as exc:
            QMessageBox.warning(self, "Windows Explorer", f"Could not list this folder:\n{exc}")
            return
        folder_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon)
        file_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon)
        for entry in entries:
            if entry == RECYCLE_ROOT or entry.name.startswith("."):
                continue
            item = QListWidgetItem(folder_icon if entry.is_dir() else file_icon, entry.name)
            item.setData(Qt.ItemDataRole.UserRole, str(entry))
            item.setToolTip(str(entry))
            self.file_list.addItem(item)
        self.stack.setCurrentWidget(self.file_list)
        self.address.setText(f"{self.drive[0]}\\  {self.current_path}")
        self.back_button.setEnabled(bool(self.history))
        self.up_button.setEnabled(self.current_path != self.drive[2])

    def _open_item(self, item):
        path = Path(item.data(Qt.ItemDataRole.UserRole))
        if path.is_dir():
            self.history.append(self.current_path)
            self._show_folder(path)
        elif path.suffix.casefold() in (
            ".txt", ".md", ".log", ".ini", ".json", ".csv", ".html", ".htm",
            ".png", ".jpg", ".jpeg", ".bmp",
        ):
            self.openFileRequested.emit(str(path))
        else:
            QMessageBox.information(self, "Windows Explorer", f"Installed media and application files are managed by their own programs.\n\n{path.name}")

    def _file_menu(self, pos):
        item = self.file_list.itemAt(pos)
        menu = QMenu(self)
        if item:
            path = Path(item.data(Qt.ItemDataRole.UserRole))
            open_action = menu.addAction("Open")
            open_action.triggered.connect(lambda: self._open_item(item))
            delete_action = menu.addAction("Delete")
            delete_action.setEnabled(self._is_recyclable(path))
            delete_action.triggered.connect(lambda: self.delete_item(path))
            menu.addSeparator()
            properties = menu.addAction("Properties")
            properties.triggered.connect(lambda: self._show_properties(path))
        if self.current_path:
            create = menu.addAction("New folder…")
            create.setEnabled(self._is_recyclable(self.current_path))
            create.triggered.connect(self.create_folder)
            recycle = menu.addAction("Open Recycle Bin")
            recycle.triggered.connect(lambda: self.recycleBinRequested.emit())
        menu.popup(self.file_list.viewport().mapToGlobal(pos))

    def _is_recyclable(self, path):
        try:
            self.recycle_store._safe_path(path, self.recycle_store.allowed_roots)
            return True
        except RecycleBinError:
            return False

    def delete_item(self, path):
        path = Path(path)
        if not self._is_recyclable(path):
            QMessageBox.warning(self, "Windows Explorer", "This Windows, model, profile, or chat data is protected.")
            return
        answer = QMessageBox.question(
            self, "Delete item",
            f"Move “{path.name}” to the Recycle Bin?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            self.recycle_store.move_to_bin(path)
            self._show_folder(self.current_path)
        except RecycleBinError as exc:
            QMessageBox.warning(self, "Windows Explorer", str(exc))

    def create_folder(self):
        name, accepted = QInputDialog.getText(self, "New Folder", "Folder name:")
        if not accepted:
            return
        name = name.strip()
        if not name or name in (".", "..") or any(c in name for c in ("/", "\\", "\0")):
            QMessageBox.warning(self, "New Folder", "Enter a valid folder name.")
            return
        candidate = self.current_path / name
        if not self._is_recyclable(candidate):
            QMessageBox.warning(self, "New Folder", "Folders cannot be created in protected Windows/model locations.")
            return
        try:
            candidate.mkdir()
            self._show_folder(self.current_path)
        except OSError as exc:
            QMessageBox.warning(self, "New Folder", f"Could not create this folder:\n{exc}")

    def go_back(self):
        if self.history:
            self._show_folder(self.history.pop())

    def go_up(self):
        if self.current_path and self.drive and self.current_path != self.drive[2]:
            parent = self.current_path.parent
            if parent == self.drive[2] or parent.is_relative_to(self.drive[2]):
                self.history.append(self.current_path)
                self._show_folder(parent)

    def _show_properties(self, path):
        kind = "Folder" if path.is_dir() else "File"
        QMessageBox.information(self, f"{path.name} Properties", f"Name: {path.name}\nType: {kind}\nLocation: {path.parent}")

    def open_recycle_bin(self):
        self.recycleBinRequested.emit()
