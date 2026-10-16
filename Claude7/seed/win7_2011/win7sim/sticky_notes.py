"""Persistent Sticky Notes for the currently selected Windows profile."""

from __future__ import annotations

import json
import os
import re
import tempfile
from pathlib import Path
from uuid import uuid4

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from . import config

NOTE_COLORS = {
    "Yellow": "#fff4a8",
    "Blue": "#bfe8ff",
    "Green": "#c9f7c5",
    "Pink": "#ffd6e5",
}
_PROFILE_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,80}$")


def sticky_notes_path(profile_id: str) -> Path:
    if not _PROFILE_ID_RE.fullmatch(profile_id):
        raise ValueError("Sticky Notes needs a valid Windows profile ID.")
    return config.STICKY_NOTES / f"{profile_id}.json"


def load_notes(profile_id: str) -> list[dict[str, str]]:
    path = sticky_notes_path(profile_id)
    if not path.exists():
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"Could not read Sticky Notes data: {exc}") from exc
    if not isinstance(raw, list):
        raise ValueError("Sticky Notes data has an invalid format.")
    notes: list[dict[str, str]] = []
    for note in raw:
        if (
            not isinstance(note, dict)
            or not isinstance(note.get("id"), str)
            or not isinstance(note.get("text"), str)
            or note.get("color") not in NOTE_COLORS.values()
        ):
            raise ValueError("Sticky Notes data contains an invalid note.")
        notes.append(
            {"id": note["id"], "text": note["text"], "color": note["color"]}
        )
    return notes


def save_notes(profile_id: str, notes: list[dict[str, str]]) -> None:
    path = sticky_notes_path(profile_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.stem}-",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
            json.dump(notes, temporary, ensure_ascii=False, indent=2)
            temporary.write("\n")
            temporary.flush()
            os.fsync(temporary.fileno())
        os.replace(temporary_path, path)
    except OSError:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
        raise


class StickyNotesApp(QWidget):
    """A small note organizer that saves automatically per selected fursona."""

    def __init__(self, profile_id: str, profile_name: str) -> None:
        super().__init__()
        if not profile_id:
            raise ValueError("Sticky Notes requires an active Windows profile.")
        self.profile_id = profile_id
        self.notes: list[dict[str, str]] = []
        self._active_note_id: str | None = None
        self._load_error = False
        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(500)
        self._save_timer.timeout.connect(self._save_now)

        self.note_list = QListWidget()
        self.note_list.setObjectName("sticky-note-list")
        self.note_list.setMinimumWidth(160)
        self.editor = QTextEdit()
        self.editor.setObjectName("sticky-note-editor")
        self.editor.setPlaceholderText("Write a note…")
        self.editor.setStyleSheet(
            "QTextEdit { background: #fff4a8; color: #28261f; "
            "border: 1px solid #d5c66b; padding: 10px; font-size: 11pt; }"
        )
        self.color_box = QComboBox()
        self.color_box.setObjectName("sticky-note-color")
        for name, color in NOTE_COLORS.items():
            self.color_box.addItem(name, color)
            self.color_box.setItemData(
                self.color_box.count() - 1, QColor(color), Qt.ItemDataRole.BackgroundRole
            )

        self.new_button = QPushButton("New note")
        self.delete_button = QPushButton("Delete")
        self.status = QLabel(f"Notes save for {profile_name} on this computer.")
        self.status.setWordWrap(True)

        list_controls = QHBoxLayout()
        list_controls.addWidget(self.new_button)
        list_controls.addWidget(self.delete_button)
        left = QVBoxLayout()
        left.addWidget(QLabel("Notes"))
        left.addWidget(self.note_list, 1)
        left.addLayout(list_controls)
        right = QVBoxLayout()
        right.addWidget(self.color_box, 0, Qt.AlignmentFlag.AlignRight)
        right.addWidget(self.editor, 1)
        right.addWidget(self.status)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.addLayout(left)
        layout.addLayout(right, 1)

        self.new_button.clicked.connect(self.create_note)
        self.delete_button.clicked.connect(self.delete_note)
        self.note_list.currentRowChanged.connect(self._select_row)
        self.editor.textChanged.connect(self._schedule_save)
        self.color_box.currentIndexChanged.connect(self._schedule_save)

        try:
            self.notes = load_notes(profile_id)
        except ValueError as exc:
            self._load_error = True
            self.status.setText(str(exc) + " The file was left unchanged.")
            self.status.setStyleSheet("color: #a00000;")
            self.new_button.setEnabled(False)
            self.delete_button.setEnabled(False)
            self.editor.setEnabled(False)
            self.color_box.setEnabled(False)
            return
        self._refresh_list()
        if self.notes:
            self.note_list.setCurrentRow(0)
        else:
            self.editor.setEnabled(False)
            self.color_box.setEnabled(False)

    def create_note(self) -> None:
        if self._load_error:
            return
        self._save_now()
        note = {
            "id": uuid4().hex,
            "text": "",
            "color": NOTE_COLORS["Yellow"],
        }
        self.notes.append(note)
        self._refresh_list()
        self.note_list.setCurrentRow(len(self.notes) - 1)
        self._save_now()

    def delete_note(self) -> None:
        row = self.note_list.currentRow()
        if row < 0 or row >= len(self.notes):
            return
        answer = QMessageBox.question(
            self,
            "Delete note?",
            "Delete this note permanently?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self._save_now()
        self.notes.pop(row)
        self._active_note_id = None
        self._refresh_list()
        if self.notes:
            self.note_list.setCurrentRow(min(row, len(self.notes) - 1))
        else:
            self.editor.clear()
            self.editor.setEnabled(False)
            self.color_box.setEnabled(False)
        self._save_now()

    def _refresh_list(self) -> None:
        self.note_list.blockSignals(True)
        self.note_list.clear()
        for note in self.notes:
            item = QListWidgetItem(self._note_title(note["text"]))
            item.setData(Qt.ItemDataRole.UserRole, note["id"])
            item.setBackground(QColor(note["color"]))
            self.note_list.addItem(item)
        self.note_list.blockSignals(False)

    @staticmethod
    def _note_title(text: str) -> str:
        title = next((line.strip() for line in text.splitlines() if line.strip()), "")
        return (title[:42] + "…") if len(title) > 43 else (title or "Untitled note")

    def _select_row(self, row: int) -> None:
        self._save_now()
        if row < 0 or row >= len(self.notes):
            self._active_note_id = None
            self.editor.clear()
            return
        note = self.notes[row]
        self._active_note_id = note["id"]
        self.editor.blockSignals(True)
        self.color_box.blockSignals(True)
        self.editor.setPlainText(note["text"])
        color_index = self.color_box.findData(note["color"])
        self.color_box.setCurrentIndex(max(0, color_index))
        self.editor.blockSignals(False)
        self.color_box.blockSignals(False)
        self.editor.setEnabled(True)
        self.color_box.setEnabled(True)

    def _schedule_save(self, *_args) -> None:
        if self._active_note_id is not None:
            self._save_timer.start()

    def _save_now(self) -> bool:
        self._save_timer.stop()
        if self._load_error:
            return False
        active = next(
            (note for note in self.notes if note["id"] == self._active_note_id),
            None,
        )
        if active is not None:
            active["text"] = self.editor.toPlainText()
            active["color"] = self.color_box.currentData()
            row = next(
                (
                    index
                    for index, note in enumerate(self.notes)
                    if note["id"] == self._active_note_id
                ),
                -1,
            )
            if row >= 0:
                item = self.note_list.item(row)
                item.setText(self._note_title(active["text"]))
                item.setBackground(QColor(active["color"]))
        try:
            save_notes(self.profile_id, self.notes)
        except (OSError, ValueError) as exc:
            self.status.setText(f"Could not save Sticky Notes: {exc}")
            self.status.setStyleSheet("color: #a00000;")
            return False
        self.status.setText("All notes saved.")
        self.status.setStyleSheet("")
        return True

    def closeEvent(self, event) -> None:  # noqa: N802 - Qt event name
        if self._save_now():
            event.accept()
        else:
            event.ignore()
