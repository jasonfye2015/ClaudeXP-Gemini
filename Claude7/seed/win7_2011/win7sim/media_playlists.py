"""Per-fursona storage and management UI for Windows Media Player playlists."""

from __future__ import annotations

import json
import os
import re
import uuid
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from . import config

_PROFILE_ID_PATTERN = re.compile(r"[A-Za-z0-9_-]+\Z")
_PLAYLIST_ID_PATTERN = re.compile(r"[a-f0-9]{32}\Z")
_PLAYLIST_VERSION = 1
_MAX_NAME_LENGTH = 80


@dataclass(frozen=True)
class SavedPlaylist:
    playlist_id: str
    name: str
    media_paths: tuple[str, ...]


class SavedPlaylistStore:
    """Atomic JSON store for one profile's named playlists."""

    def __init__(self, profile_id: str) -> None:
        if not isinstance(profile_id, str) or not _PROFILE_ID_PATTERN.fullmatch(
            profile_id
        ):
            raise ValueError("The Windows profile ID is not valid.")
        self.profile_id = profile_id
        self.path = config.MEDIA_PLAYLISTS / f"{profile_id}.json"

    def load_all(self) -> list[SavedPlaylist]:
        self._refuse_symlinked_path()
        if not self.path.exists():
            return []
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError("The saved playlist file contains invalid JSON.") from exc
        if (
            not isinstance(raw, dict)
            or raw.get("version") != _PLAYLIST_VERSION
            or raw.get("profile_id") != self.profile_id
            or not isinstance(raw.get("playlists"), list)
        ):
            raise ValueError("The saved playlist file has an unsupported format.")

        playlists: list[SavedPlaylist] = []
        seen_ids: set[str] = set()
        for record in raw["playlists"]:
            if not isinstance(record, dict):
                raise ValueError("A saved playlist entry is malformed.")
            playlist_id = record.get("id")
            name = record.get("name")
            media_paths = record.get("media_paths")
            if (
                not isinstance(playlist_id, str)
                or not _PLAYLIST_ID_PATTERN.fullmatch(playlist_id)
                or playlist_id in seen_ids
                or not isinstance(name, str)
                or not name.strip()
                or len(name) > _MAX_NAME_LENGTH
                or not isinstance(media_paths, list)
                or any(not isinstance(path, str) or not path for path in media_paths)
            ):
                raise ValueError("A saved playlist entry is malformed.")
            seen_ids.add(playlist_id)
            playlists.append(
                SavedPlaylist(playlist_id, name, tuple(media_paths))
            )
        return playlists

    def save_new(
        self, name: str, media_paths: Iterable[str | Path]
    ) -> SavedPlaylist:
        cleaned_name = _clean_name(name)
        paths = _normalize_paths(media_paths)
        if not paths:
            raise ValueError("Add at least one media file before saving a playlist.")
        playlists = self.load_all()
        if any(record.name.casefold() == cleaned_name.casefold() for record in playlists):
            raise ValueError("A playlist with that name already exists.")
        saved = SavedPlaylist(uuid.uuid4().hex, cleaned_name, paths)
        self._write([*playlists, saved])
        return saved

    def rename(self, playlist_id: str, new_name: str) -> SavedPlaylist:
        cleaned_name = _clean_name(new_name)
        playlists = self.load_all()
        selected = self._find(playlists, playlist_id)
        if any(
            record.playlist_id != playlist_id
            and record.name.casefold() == cleaned_name.casefold()
            for record in playlists
        ):
            raise ValueError("A playlist with that name already exists.")
        renamed = SavedPlaylist(
            selected.playlist_id, cleaned_name, selected.media_paths
        )
        self._write(
            [renamed if record.playlist_id == playlist_id else record
             for record in playlists]
        )
        return renamed

    def delete(self, playlist_id: str) -> None:
        playlists = self.load_all()
        self._find(playlists, playlist_id)
        self._write(
            [record for record in playlists if record.playlist_id != playlist_id]
        )

    def _write(self, playlists: list[SavedPlaylist]) -> None:
        self._refuse_symlinked_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": _PLAYLIST_VERSION,
            "profile_id": self.profile_id,
            "playlists": [
                {
                    "id": record.playlist_id,
                    "name": record.name,
                    "media_paths": list(record.media_paths),
                }
                for record in playlists
            ],
        }
        temporary = self.path.with_name(
            f".{self.path.name}.{uuid.uuid4().hex}.tmp"
        )
        try:
            temporary.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            os.replace(temporary, self.path)
        finally:
            temporary.unlink(missing_ok=True)

    def _refuse_symlinked_path(self) -> None:
        storage_root = config.STORAGE_ROOT.absolute()
        try:
            relative_path = self.path.parent.absolute().relative_to(storage_root)
        except ValueError as exc:
            raise OSError(
                f"Refusing to access playlists outside {storage_root}."
            ) from exc
        current = storage_root
        if current.is_symlink():
            raise OSError(
                "Refusing to access saved playlists through a symbolic link: "
                f"{current}"
            )
        for component in relative_path.parts:
            current /= component
            if current.is_symlink():
                raise OSError(
                    "Refusing to access saved playlists through a symbolic link: "
                    f"{current}"
                )
        if self.path.is_symlink():
            raise OSError(
                f"Refusing to access saved playlists through a symbolic link: "
                f"{self.path}"
            )

    @staticmethod
    def _find(
        playlists: list[SavedPlaylist], playlist_id: str
    ) -> SavedPlaylist:
        for record in playlists:
            if record.playlist_id == playlist_id:
                return record
        raise KeyError("That saved playlist no longer exists.")


def _clean_name(name: str) -> str:
    if not isinstance(name, str):
        raise ValueError("Enter a playlist name.")
    cleaned = name.strip()
    if not cleaned or len(cleaned) > _MAX_NAME_LENGTH:
        raise ValueError(
            f"Playlist names must be 1 to {_MAX_NAME_LENGTH} characters."
        )
    return cleaned


def _normalize_paths(paths: Iterable[str | Path]) -> tuple[str, ...]:
    normalized: list[str] = []
    seen: set[str] = set()
    for value in paths:
        if not str(value).strip():
            raise ValueError("Playlist entries must point to media files.")
        path = str(Path(value).expanduser().resolve())
        key = os.path.normcase(path)
        if key not in seen:
            normalized.append(path)
            seen.add(key)
    return tuple(normalized)


class PlaylistManagerDialog(QDialog):
    """Dialog for saving, opening, renaming, and deleting saved playlists."""

    openRequested = Signal(object)

    def __init__(
        self,
        store: SavedPlaylistStore,
        current_media_paths: Callable[[], list[Path]],
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.store = store
        self.current_media_paths = current_media_paths
        self.records: list[SavedPlaylist] = []
        self.setWindowTitle("Media Player Playlists")
        self.setMinimumSize(440, 380)

        self.playlist_list = QListWidget()
        self.playlist_list.itemSelectionChanged.connect(self._selection_changed)
        self.playlist_list.itemDoubleClicked.connect(
            lambda _item: self.open_selected()
        )
        self.status = QLabel(
            "Saved playlists refer to local files; missing files stay in the saved list."
        )
        self.status.setWordWrap(True)

        self.save_button = QPushButton("Save Current…")
        self.open_button = QPushButton("Open")
        self.rename_button = QPushButton("Rename…")
        self.delete_button = QPushButton("Delete")
        self.close_button = QPushButton("Close")
        self.save_button.clicked.connect(self.save_current)
        self.open_button.clicked.connect(self.open_selected)
        self.rename_button.clicked.connect(self.rename_selected)
        self.delete_button.clicked.connect(self.delete_selected)
        self.close_button.clicked.connect(self.reject)

        row = QHBoxLayout()
        row.addWidget(self.save_button)
        row.addWidget(self.open_button)
        row.addWidget(self.rename_button)
        row.addWidget(self.delete_button)
        row.addStretch(1)
        row.addWidget(self.close_button)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Saved playlists"))
        layout.addWidget(self.playlist_list, 1)
        layout.addWidget(self.status)
        layout.addLayout(row)
        self.refresh()

    def refresh(self, select_id: str | None = None) -> None:
        self.playlist_list.clear()
        try:
            self.records = sorted(
                self.store.load_all(), key=lambda record: record.name.casefold()
            )
        except (OSError, ValueError) as exc:
            self.records = []
            self.status.setText(f"Could not read saved playlists: {exc}")
            self._selection_changed()
            return

        for record in self.records:
            missing = sum(
                not Path(media_path).is_file()
                for media_path in record.media_paths
            )
            label = record.name
            if missing:
                label += f" — {missing} missing file(s)"
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, record.playlist_id)
            item.setToolTip(
                "\n".join(record.media_paths)
            )
            self.playlist_list.addItem(item)
        if select_id:
            for row in range(self.playlist_list.count()):
                item = self.playlist_list.item(row)
                if item.data(Qt.ItemDataRole.UserRole) == select_id:
                    self.playlist_list.setCurrentRow(row)
                    break
        elif self.playlist_list.count():
            self.playlist_list.setCurrentRow(0)
        self._selection_changed()

    def save_current(self) -> None:
        paths = self.current_media_paths()
        if not paths:
            self.status.setText("Add at least one media file before saving a playlist.")
            return
        name, accepted = QInputDialog.getText(
            self, "Save Current Playlist", "Playlist name:"
        )
        if not accepted:
            return
        try:
            saved = self.store.save_new(name, paths)
        except (OSError, ValueError) as exc:
            self.status.setText(str(exc))
            return
        self.refresh(saved.playlist_id)
        self.status.setText(f"Saved playlist “{saved.name}”.")

    def open_selected(self) -> None:
        record = self._selected_record()
        if record is None:
            self.status.setText("Select a saved playlist to open.")
            return
        self.openRequested.emit(record)
        self.accept()

    def rename_selected(self) -> None:
        record = self._selected_record()
        if record is None:
            self.status.setText("Select a saved playlist to rename.")
            return
        name, accepted = QInputDialog.getText(
            self, "Rename Playlist", "Playlist name:", text=record.name
        )
        if not accepted:
            return
        try:
            renamed = self.store.rename(record.playlist_id, name)
        except (OSError, ValueError, KeyError) as exc:
            self.status.setText(str(exc))
            return
        self.refresh(renamed.playlist_id)
        self.status.setText(f"Renamed playlist to “{renamed.name}”.")

    def delete_selected(self) -> None:
        record = self._selected_record()
        if record is None:
            self.status.setText("Select a saved playlist to delete.")
            return
        result = QMessageBox.question(
            self,
            "Delete Playlist",
            f"Delete the saved playlist “{record.name}”? "
            "The media files themselves will not be changed.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if result != QMessageBox.StandardButton.Yes:
            return
        try:
            self.store.delete(record.playlist_id)
        except (OSError, ValueError, KeyError) as exc:
            self.status.setText(str(exc))
            return
        self.refresh()
        self.status.setText(f"Deleted playlist “{record.name}”.")

    def _selected_record(self) -> SavedPlaylist | None:
        item = self.playlist_list.currentItem()
        if item is None:
            return None
        playlist_id = item.data(Qt.ItemDataRole.UserRole)
        return next(
            (
                record
                for record in self.records
                if record.playlist_id == playlist_id
            ),
            None,
        )

    def _selection_changed(self) -> None:
        selected = self._selected_record() is not None
        self.open_button.setEnabled(selected)
        self.rename_button.setEnabled(selected)
        self.delete_button.setEnabled(selected)
