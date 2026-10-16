"""Per-fursona transcript of requests sent to local language models."""

from __future__ import annotations

from datetime import datetime
import json
import os
from pathlib import Path
import re
import shutil

from PySide6.QtCore import QObject, QSize, QTimer, Qt, Signal
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QFileDialog, QHBoxLayout, QLabel, QLineEdit, QListWidget, QMessageBox,
    QPlainTextEdit, QPushButton, QSizePolicy, QToolButton, QVBoxLayout, QWidget,
)
from PySide6.QtGui import QTextCursor

from . import config
from .ai_settings import ROLE_LABELS


class LLMActivityLog(QObject):
    """Private append-only log file and signals for an open viewer window."""

    contentsChanged = Signal(str)
    errorChanged = Signal(str)
    VIEW_MAX_BYTES = 2_000_000

    def __init__(self, profile_id: str, parent=None):
        super().__init__(parent)
        if not isinstance(profile_id, str) or not re.fullmatch(
            r"[A-Za-z0-9_-]+", profile_id
        ):
            raise ValueError("The LLM activity log needs a valid fursona profile ID.")
        self.path = config.USER_PROFILES / profile_id / "llm-activity.txt"
        self.error = ""
        self._models_by_request = {}

    def connect_service(self, service):
        service.llmRequestSent.connect(self.record_request)
        service.llmResponseCaptured.connect(self.record_response)

    @staticmethod
    def _timestamp():
        return datetime.now().astimezone().isoformat(timespec="seconds")

    def _append(self, event, request_id, role, model, content):
        label = ROLE_LABELS.get(role, role)
        header = json.dumps({
            "time": self._timestamp(),
            "event": event,
            "request_id": request_id,
            "role": label,
            "model": model,
        }, ensure_ascii=False)
        if event == "PROMPT SENT":
            body = ["--- exact messages sent to the model ---"]
            for index, message in enumerate(content, 1):
                body.append(f"[Message {index} | {message.get('role', 'unknown')}]\n")
                body.append(str(message.get("content", "")))
                body.append(f"\n[End message {index}]\n")
            body = "\n".join(body)
        else:
            body = str(content)
        entry = f"{header}\n{body}\n\n"
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            if self.path.parent.is_symlink() or self.path.is_symlink():
                raise OSError("Refusing to access an activity log through a symbolic link.")
            with self.path.open("a", encoding="utf-8", newline="\n") as stream:
                stream.write(entry)
                stream.flush()
                os.fsync(stream.fileno())
            try:
                self.path.chmod(0o600)
            except OSError:
                pass
        except (OSError, UnicodeError, ValueError) as exc:
            self._set_error(f"Could not write the private LLM activity log: {exc}")
            return
        self._set_error("")
        self.contentsChanged.emit(entry)

    def record_request(self, request_id, role, model, messages):
        self._models_by_request[request_id] = (role, model)
        self._append("PROMPT SENT", request_id, role, model, messages)

    def record_response(self, request_id, role, success, response):
        recorded_role, model = self._models_by_request.pop(request_id, (role, ""))
        self._append(
            "MODEL OUTPUT" if success else "REQUEST ERROR",
            request_id, recorded_role, model, response,
        )

    def _set_error(self, message):
        if self.error != message:
            self.error = message
            self.errorChanged.emit(message)

    def read_recent_text(self):
        try:
            if self.path.parent.is_symlink() or self.path.is_symlink():
                raise OSError("Refusing to read an activity log through a symbolic link.")
            if not self.path.exists():
                return ""
            size = self.path.stat().st_size
            with self.path.open("rb") as stream:
                if size > self.VIEW_MAX_BYTES:
                    stream.seek(size - self.VIEW_MAX_BYTES)
                    data = stream.read()
                    lines = data.splitlines(keepends=True)
                    start = next(
                        (index for index, line in enumerate(lines)
                         if line.startswith(b'{"time":')),
                        len(lines),
                    )
                    data = b"".join(lines[start:])
                    prefix = "[Earlier log entries omitted in this view; export the full file.]\n"
                else:
                    data = stream.read()
                    prefix = ""
            self._set_error("")
            return prefix + data.decode("utf-8", errors="replace")
        except (OSError, UnicodeError, ValueError) as exc:
            self._set_error(f"Could not read the private LLM activity log: {exc}")
            return ""

    def search(self, query):
        """Find matching log entries without loading the complete file into memory."""
        needle = str(query).strip().casefold()
        if not needle:
            return []
        try:
            if self.path.parent.is_symlink() or self.path.is_symlink():
                raise OSError("Refusing to search an activity log through a symbolic link.")
            if not self.path.exists():
                self._set_error("")
                return []

            matches = []
            current = None
            with self.path.open("rb") as stream:
                at_line_start = True
                line_tail = ""
                while True:
                    chunk_start = stream.tell()
                    chunk = stream.readline(64 * 1024)
                    if not chunk:
                        break
                    if at_line_start and chunk.startswith(b'{"time":'):
                        try:
                            header = json.loads(chunk.decode("utf-8", errors="replace"))
                        except (json.JSONDecodeError, UnicodeError):
                            header = {}
                        current = {
                            "offset": chunk_start,
                            "event": str(header.get("event", "LLM activity")),
                            "time": str(header.get("time", "")),
                            "model": str(header.get("model", "")),
                            "request_id": str(header.get("request_id", "")),
                        }

                    text = chunk.decode("utf-8", errors="replace")
                    combined = line_tail + text
                    folded = combined.casefold()
                    match_position = folded.find(needle)
                    if match_position >= 0 and current is not None:
                        # Casefold can expand some Unicode characters. The excerpt
                        # is only for display, so use a bounded nearby slice.
                        start = max(0, match_position - 100)
                        end = min(len(combined), match_position + len(needle) + 180)
                        excerpt = combined[start:end].strip()
                        if start:
                            excerpt = "…" + excerpt
                        if end < len(combined):
                            excerpt += "…"
                        if not current.get("snippet"):
                            current["snippet"] = excerpt
                            matches.append(current)

                    if chunk.endswith(b"\n"):
                        at_line_start = True
                        line_tail = ""
                    else:
                        at_line_start = False
                        line_tail = combined[-max(0, len(needle) - 1):]

            self._set_error("")
            return matches
        except (OSError, UnicodeError, ValueError) as exc:
            self._set_error(f"Could not search the private LLM activity log: {exc}")
            return []

    def clear(self):
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            if self.path.parent.is_symlink() or self.path.is_symlink():
                raise OSError("Refusing to clear an activity log through a symbolic link.")
            config._atomic_write_private_json(self.path, "")
        except (OSError, UnicodeError, ValueError) as exc:
            self._set_error(f"Could not clear the private LLM activity log: {exc}")
            return False
        self._set_error("")
        self.contentsChanged.emit("")
        return True

    def export(self, destination):
        destination = Path(destination)
        try:
            if destination.resolve() == self.path.resolve():
                raise ValueError("Choose a separate file so the private activity log stays in place.")
            if destination.is_symlink():
                raise OSError("Refusing to overwrite a symbolic link.")
            if self.path.parent.is_symlink() or self.path.is_symlink():
                raise OSError("Refusing to export an activity log through a symbolic link.")
            if not self.path.exists():
                self.path.parent.mkdir(parents=True, exist_ok=True)
                self.path.touch()
            shutil.copyfile(self.path, destination)
        except (OSError, UnicodeError, ValueError) as exc:
            self._set_error(f"Could not export the LLM activity log: {exc}")
            return False
        self._set_error("")
        return True


class LLMActivityApp(QWidget):
    """Review, export, and deliberately clear the fursona's model activity log."""

    def __init__(self, activity_log: LLMActivityLog, parent=None):
        super().__init__(parent)
        self.activity_log = activity_log
        self.setObjectName("llmActivityLog")
        self.setMinimumSize(620, 440)
        root = QVBoxLayout(self)
        heading = QLabel("Local LLM Activity")
        heading.setStyleSheet("font-size: 17pt; font-weight: 600; color: #274f70;")
        root.addWidget(heading)
        root.addWidget(QLabel(
            "Full prompts and model outputs, kept locally for this fursona. "
            "The viewer shows a recent portion; search and export include the entire log."
        ))
        search_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setObjectName("llmActivitySearch")
        self.search_input.setPlaceholderText("Search prompts, outputs, and errors in the full log")
        self.search_input.returnPressed.connect(self._search)
        search_row.addWidget(self.search_input, 1)
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self._search)
        search_row.addWidget(self.search_button)
        root.addLayout(search_row)
        self.matches = QListWidget()
        self.matches.setObjectName("llmActivitySearchResults")
        self.matches.setMaximumHeight(110)
        self.matches.itemClicked.connect(self._show_selected_match)
        root.addWidget(self.matches)
        navigation = QHBoxLayout()
        self.match_status = QLabel("Enter a word or phrase to search the full log.")
        navigation.addWidget(self.match_status, 1)
        self.previous_button = QPushButton("Previous match")
        self.previous_button.clicked.connect(lambda: self._move_match(-1))
        navigation.addWidget(self.previous_button)
        self.next_button = QPushButton("Next match")
        self.next_button.clicked.connect(lambda: self._move_match(1))
        navigation.addWidget(self.next_button)
        root.addLayout(navigation)
        self.text = QPlainTextEdit()
        self.text.setObjectName("llmActivityText")
        self.text.setReadOnly(True)
        self.text.setPlaceholderText("No LLM activity has been recorded yet.")
        self.text.setMaximumBlockCount(20_000)
        root.addWidget(self.text, 1)
        self._search_matches = []
        self._selected_match = -1
        self._search_active = False
        self._update_navigation()
        actions = QHBoxLayout()
        self.status = QLabel(str(activity_log.path))
        self.status.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.status.setToolTip(str(activity_log.path))
        self.status.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        actions.addWidget(self.status, 1)
        self.export_button = QPushButton("Export to text…")
        self.export_button.clicked.connect(self._export)
        actions.addWidget(self.export_button)
        self.clear_button = QPushButton("Clear log…")
        self.clear_button.clicked.connect(self._clear)
        actions.addWidget(self.clear_button)
        root.addLayout(actions)
        activity_log.contentsChanged.connect(self._entries_changed)
        activity_log.errorChanged.connect(self._error_changed)
        self.text.setPlainText(activity_log.read_recent_text())
        self._error_changed(activity_log.error)

    def _entries_changed(self, entry):
        if not entry:
            self._search_matches = []
            self._selected_match = -1
            self._search_active = False
            self.matches.clear()
            self.match_status.setText("Enter a word or phrase to search the full log.")
            self._update_navigation()
            self.text.clear()
            return
        if self._search_active:
            return
        self.text.moveCursor(QTextCursor.MoveOperation.End)
        self.text.insertPlainText(entry)
        self.text.ensureCursorVisible()

    def _search(self):
        query = self.search_input.text()
        if not query.strip():
            self._search_matches = []
            self._selected_match = -1
            self._search_active = False
            self.matches.clear()
            self.match_status.setText("Enter a word or phrase to search the full log.")
            self.text.setPlainText(self.activity_log.read_recent_text())
            self._update_navigation()
            return
        self._search_matches = self.activity_log.search(query)
        self._search_active = True
        self._selected_match = -1
        self.matches.clear()
        for match in self._search_matches:
            label = f"{match['event']} · {match['time']} · {match['model']}"
            self.matches.addItem(label)
        if self._search_matches:
            self.match_status.setText(
                f"{len(self._search_matches)} matching log entries. Select one or use Previous/Next."
            )
            self._select_match(0)
        elif self.activity_log.error:
            self.match_status.setText("Search could not be completed.")
            self.text.setPlainText(self.activity_log.error)
        else:
            self.match_status.setText("No matching prompts, outputs, or errors.")
            self.text.setPlainText("No matching log entries.")
        self._update_navigation()

    def _show_selected_match(self, item):
        row = self.matches.row(item)
        if 0 <= row < len(self._search_matches):
            self._select_match(row)

    def _select_match(self, index):
        if not self._search_matches:
            return
        self._selected_match = index % len(self._search_matches)
        match = self._search_matches[self._selected_match]
        self.matches.setCurrentRow(self._selected_match)
        self.text.setPlainText(
            f"{match['event']}  |  {match['time']}  |  {match['model']}\n"
            f"Request: {match['request_id']}\n"
            f"Log byte offset: {match['offset']}\n\n"
            f"{match['snippet']}"
        )
        self._update_navigation()

    def _move_match(self, direction):
        if self._search_matches:
            self._select_match(self._selected_match + direction)

    def _update_navigation(self):
        has_matches = bool(self._search_matches)
        self.previous_button.setEnabled(has_matches)
        self.next_button.setEnabled(has_matches)

    def _error_changed(self, error):
        if error:
            self.status.setText(error)
            self.status.setStyleSheet("color: #a82222;")
        else:
            self.status.setText("Local, fursona-specific activity log")
            self.status.setToolTip(str(self.activity_log.path))
            self.status.setStyleSheet("")

    def _export(self):
        destination, _ = QFileDialog.getSaveFileName(
            self, "Export LLM activity", "llm-activity.txt", "Text files (*.txt)"
        )
        if not destination:
            return
        if not self.activity_log.export(destination):
            QMessageBox.warning(self, "Export failed", self.activity_log.error)
            return
        QMessageBox.information(self, "Export complete", f"Full LLM activity exported to:\n{destination}")

    def _clear(self):
        answer = QMessageBox.question(
            self, "Clear LLM activity log",
            "Permanently delete every recorded prompt and model output for this fursona? "
            "This cannot be undone. Export a copy first if you want to keep it.",
            QMessageBox.StandardButton.Cancel | QMessageBox.StandardButton.Yes,
            QMessageBox.StandardButton.Cancel,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        if not self.activity_log.clear():
            QMessageBox.warning(self, "Clear failed", self.activity_log.error)


class LLMActivityMonitor(QToolButton):
    """Blinking simulated hard-drive activity light and shortcut to its log."""

    openRequested = Signal()
    COLORS = {"sending": "#44d261", "generating": "#ffd338", "output": "#ef4444"}
    LABELS = {
        "sending": "Sending prompt",
        "generating": "Calculating model output",
        "output": "Delivering model output",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("llmActivityMonitor")
        self.setAccessibleName("Local LLM activity monitor")
        self.setFixedSize(32, 30)
        self.setIconSize(QSize(26, 26))
        self.phase = "idle"
        self.role = ""
        self.request_id = None
        self._led_on = False
        self.log_error = ""
        self.blink_timer = QTimer(self)
        self.blink_timer.setInterval(280)
        self.blink_timer.timeout.connect(self._blink)
        self.output_timer = QTimer(self)
        self.output_timer.setSingleShot(True)
        self.output_timer.setInterval(850)
        self.output_timer.timeout.connect(self._clear_phase)
        self.clicked.connect(lambda _checked=False: self.openRequested.emit())
        self._refresh()

    def set_phase(self, request_id, role, phase):
        if phase == "idle":
            if self.request_id == request_id and self.phase == "output":
                return
            if self.request_id in (None, request_id):
                self._clear_phase()
            return
        if phase not in self.COLORS:
            return
        self.request_id, self.role, self.phase = request_id, role, phase
        self._led_on = True
        self.output_timer.stop()
        self.blink_timer.start()
        if phase == "output":
            self.output_timer.start()
        self._refresh()

    def set_log_error(self, message):
        self.log_error = message
        self._refresh()

    def _blink(self):
        self._led_on = not self._led_on
        self._refresh()

    def _clear_phase(self):
        self.phase = "idle"
        self.role = ""
        self.request_id = None
        self._led_on = False
        self.blink_timer.stop()
        self.output_timer.stop()
        self._refresh()

    def _refresh(self):
        pixmap = QPixmap(26, 26)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(QColor("#253440"), 1.3))
        painter.setBrush(QColor("#728594"))
        painter.drawRoundedRect(3, 5, 20, 15, 2, 2)
        painter.setPen(QPen(QColor("#adbac4"), 1))
        painter.drawLine(5, 9, 21, 9)
        painter.setPen(QPen(QColor("#40515f"), 1))
        painter.drawLine(6, 13, 18, 13)
        led = QColor(self.COLORS.get(self.phase, "#6a737a"))
        if not self._led_on:
            led = QColor("#424b50")
        painter.setPen(QPen(QColor("#253440"), 1))
        painter.setBrush(led)
        painter.drawEllipse(18, 15, 5, 5)
        painter.end()
        self.setIcon(QIcon(pixmap))
        label = self.LABELS.get(self.phase, "Idle")
        if self.role:
            label += f" · {ROLE_LABELS.get(self.role, self.role)}"
        tooltip = f"Local LLM activity — {label}\nClick to open the activity log."
        if self.log_error:
            tooltip += f"\n{self.log_error}"
        self.setToolTip(tooltip)
