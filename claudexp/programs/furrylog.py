"""Furry Log: reads the plain-text diary of everything the language model does (see claudexp/furlog.py)."""
import re
from datetime import date, datetime

from PySide6.QtCore import QRectF, Qt, QTimer
from PySide6.QtGui import (QColor, QFont, QFontDatabase, QGuiApplication, QIcon, QPainter, QPen, QPixmap,
                           QSyntaxHighlighter, QTextCharFormat, QTextCursor)
from PySide6.QtWidgets import (QCheckBox, QComboBox, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPlainTextEdit,
                               QPushButton, QSpinBox, QVBoxLayout, QWidget)
from shiboken6 import isValid

from .. import furlog
from ..wm import XPWindow

MAX_LOAD = 4_000_000        # a day bigger than this shows only its last 4 MB
HEADER = re.compile(r"^==== (\S+ \S+)\s+(?:#(\d+)\s+)?(\w+)")


def furlog_icon(size=32):
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    s = size / 32.0
    p.setPen(QPen(QColor("#6B5B2A"), max(1.0, s)))
    p.setBrush(QColor("#FFF8D6"))
    p.drawRoundedRect(QRectF(5 * s, 2 * s, 22 * s, 28 * s), 2 * s, 2 * s)
    p.setPen(QPen(QColor("#9DB4DA"), max(1.0, 1.2 * s)))
    for y in (7, 11, 15):
        p.drawLine(int(9 * s), int(y * s), int(23 * s), int(y * s))
    p.setPen(QPen(QColor("#5A3545"), max(1.0, s)))
    p.setBrush(QColor("#F59AB5"))
    p.drawEllipse(QRectF(11 * s, 21 * s, 10 * s, 7 * s))
    for x, y in ((8.5, 18), (12.5, 15.5), (17.5, 15.5), (21.5, 18)):
        p.drawEllipse(QRectF(x * s, y * s, 3 * s, 4 * s))
    p.end()
    return QIcon(pm)


class Highlighter(QSyntaxHighlighter):
    def __init__(self, doc):
        super().__init__(doc)
        self.formats = {}
        for kind, color in (("REQUEST", "#0B4FB8"), ("RESPONSE", "#177A2E"), ("EVENT", "#8A4B00"),
                            ("SESSION", "#6A2C91")):
            fmt = QTextCharFormat()
            fmt.setForeground(QColor(color))
            fmt.setFontWeight(QFont.Bold)
            self.formats[kind] = fmt
        self.error = QTextCharFormat()
        self.error.setForeground(QColor("#C0261A"))
        self.error.setFontWeight(QFont.Bold)
        self.role = QTextCharFormat()
        self.role.setForeground(QColor("#777777"))
        self.role.setFontWeight(QFont.Bold)
        self.meta = QTextCharFormat()
        self.meta.setForeground(QColor("#555555"))

    def highlightBlock(self, text):
        if text.startswith("===="):
            m = HEADER.match(text)
            self.setFormat(0, len(text), self.formats.get(m.group(3) if m else "", self.role))
            if "ERROR" in text:
                self.setFormat(0, len(text), self.error)
        elif text.startswith("--- ") and text.endswith(" ---"):
            self.setFormat(0, len(text), self.role)
        elif text.startswith(("mode:", "options:", "messages:")):
            self.setFormat(0, len(text), self.meta)


def _blocks(text):
    """The log split into entries, each starting at a '====' header line."""
    parts = re.split(r"(?m)^(?=\={4} )", text)
    return [p for p in parts if p]


class FurryLog(QWidget):
    def __init__(self, desktop):
        super().__init__()
        self.desktop = desktop
        self.frame = None
        self._signature = None
        self.text = ""

        self.day = QComboBox()
        self.day.setMinimumWidth(160)
        self.day.currentIndexChanged.connect(lambda _i: self.reload(force=True))
        self.find = QLineEdit()
        self.find.setPlaceholderText("Show only entries containing...")
        self.find.setClearButtonEnabled(True)
        self.find.textChanged.connect(self._render)
        self.live = QCheckBox("Live")
        self.live.setChecked(True)
        self.live.setToolTip("Follow new entries as they are written")
        self.recording = QCheckBox("Recording")
        self.recording.setToolTip("Turn the log on or off")
        self.recording.toggled.connect(self._set_recording)
        self.full = QCheckBox("Full prompts and replies")
        self.full.setToolTip("Off: only times, models and sizes are logged, not the text")
        self.full.toggled.connect(self._set_full)
        self.keep = QSpinBox()
        self.keep.setRange(1, 3650)
        self.keep.setSuffix(" days")
        self.keep.setToolTip("Older daily logs are deleted when ClaudeXP starts")
        self.keep.valueChanged.connect(self._set_keep)

        top = QHBoxLayout()
        top.addWidget(QLabel("Day:"))
        top.addWidget(self.day)
        top.addWidget(self.find, 1)
        top.addWidget(self.live)
        options = QHBoxLayout()
        options.addWidget(self.recording)
        options.addWidget(self.full)
        options.addWidget(QLabel("Keep"))
        options.addWidget(self.keep)
        options.addStretch(1)
        for label, slot in (("Refresh", lambda: self.reload(force=True)), ("Copy", self.copy),
                            ("Go to End", self.to_end), ("Delete This Day", self.delete_day)):
            button = QPushButton(label)
            button.clicked.connect(slot)
            options.addWidget(button)

        self.view = QPlainTextEdit()
        self.view.setReadOnly(True)
        self.view.setLineWrapMode(QPlainTextEdit.WidgetWidth)
        font = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        font.setPointSize(9)
        self.view.setFont(font)
        self.highlighter = Highlighter(self.view.document())
        self.status = QLabel()

        root = QVBoxLayout(self)
        root.addLayout(top)
        root.addLayout(options)
        root.addWidget(self.view, 1)
        root.addWidget(self.status)

        self._load_settings()
        self._fill_days()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(1500)
        self.reload(force=True)
        self.to_end()

    # ---- settings -----------------------------------------------------------------------------------------
    def _load_settings(self):
        s = furlog.settings()
        for box, value in ((self.recording, s["enabled"]), (self.full, s["full_text"])):
            box.blockSignals(True)
            box.setChecked(value)
            box.blockSignals(False)
        self.keep.blockSignals(True)
        self.keep.setValue(s["keep_days"])
        self.keep.blockSignals(False)

    def _set_recording(self, on):
        if not on:
            furlog.event("LOGGING TURNED OFF", "")
        furlog.settings()["enabled"] = on
        furlog.save_settings()
        if on:
            furlog.event("LOGGING TURNED ON", "")
        self.reload(force=True)

    def _set_full(self, on):
        furlog.settings()["full_text"] = on
        furlog.save_settings()

    def _set_keep(self, days):
        furlog.settings()["keep_days"] = days
        furlog.save_settings()

    # ---- days and loading ---------------------------------------------------------------------------------
    def _fill_days(self, keep=None):
        keep = keep if keep is not None else self.day.currentData()
        days = furlog.log_days()
        today = date.today()
        if today not in days:
            days.insert(0, today)
        self.day.blockSignals(True)
        self.day.clear()
        for d in days:
            self.day.addItem(f"{d:%Y-%m-%d}" + ("  (today)" if d == today else ""), d)
        index = max(0, self.day.findData(keep)) if keep is not None else 0
        self.day.setCurrentIndex(index)
        self.day.blockSignals(False)

    def _path(self):
        d = self.day.currentData()
        return furlog.path_for(d) if d else None

    def _tick(self):
        if not isValid(self):
            return
        days = furlog.log_days()
        if date.today() not in days:
            days.insert(0, date.today())
        if len(days) != self.day.count():
            self._fill_days()
        self.reload()

    def reload(self, force=False):
        path = self._path()
        try:
            stat = path.stat() if path is not None else None
        except OSError:
            stat = None
        signature = (str(path), stat.st_size, stat.st_mtime_ns) if stat else (str(path), None, None)
        if not force and signature == self._signature:
            return
        self._signature = signature
        text, clipped = "", False
        if stat:
            try:
                with open(path, "rb") as f:
                    if stat.st_size > MAX_LOAD:
                        f.seek(stat.st_size - MAX_LOAD)
                        clipped = True
                    text = f.read().decode("utf-8", "replace")
            except OSError as exc:
                text = f"Could not read {path}: {exc}"
        if clipped:
            text = "[This day's log is large; showing only the last 4 MB.]\n\n" + text
        self.text = text
        self._render()

    def _render(self, *_):
        bar = self.view.verticalScrollBar()
        at_end = bar.value() >= bar.maximum() - 4
        follow = self.live.isChecked() and at_end
        old = bar.value()
        needle = self.find.text().strip().lower()
        blocks = _blocks(self.text)
        shown = [b for b in blocks if needle in b.lower()] if needle else blocks
        if not self.text:
            body = ("Nothing has been logged on this day.\n\nWhenever a program asks the language model for "
                    "something, the prompt, the reply, the model and the time are written here."
                    if furlog.enabled() else "Recording is turned off.")
        elif needle and not shown:
            body = "No entries contain that text."
        else:
            body = "".join(shown)
        self.view.setUpdatesEnabled(False)
        self.view.setPlainText(body)
        bar.setValue(bar.maximum() if follow else min(old, bar.maximum()))
        self.view.setUpdatesEnabled(True)
        self._summary(blocks, len(shown), bool(needle))

    def _summary(self, blocks, shown, filtered):
        requests = errors = 0
        models = set()
        for b in blocks:
            head = b.split("\n", 1)[0]
            m = HEADER.match(head)
            if not m:
                continue
            if m.group(3) == "REQUEST":
                requests += 1
                found = re.search(r"model: (\S+)", head)
                if found:
                    models.add(found.group(1))
            if "ERROR" in head:
                errors += 1
        path = self._path()
        size = path.stat().st_size if path is not None and path.exists() else 0
        bits = [f"{requests} request{'s' if requests != 1 else ''}", f"{errors} error{'s' if errors != 1 else ''}",
                f"models: {', '.join(sorted(models)) or 'none'}", f"{size / 1024:.0f} KB"]
        if filtered:
            bits.insert(0, f"showing {shown} of {len(blocks)} entries")
        bits.append("recording is ON" if furlog.enabled() else "recording is OFF")
        self.status.setText("   |   ".join(bits))
        self.status.setToolTip(str(path) if path else "")

    # ---- actions ------------------------------------------------------------------------------------------
    def to_end(self):
        self.view.moveCursor(QTextCursor.End)
        bar = self.view.verticalScrollBar()
        bar.setValue(bar.maximum())

    def copy(self):
        text = self.view.textCursor().selectedText().replace("\u2029", "\n") or self.view.toPlainText()
        QGuiApplication.clipboard().setText(text)
        self.status.setText("Copied to the clipboard.")

    def delete_day(self):
        path = self._path()
        if path is None or not path.exists():
            return
        if QMessageBox.question(self, "Furry Log", f"Delete the log for {self.day.currentText().strip()}?",
                                QMessageBox.Yes | QMessageBox.No, QMessageBox.No) != QMessageBox.Yes:
            return
        try:
            path.unlink()
        except OSError as exc:
            QMessageBox.warning(self, "Furry Log", f"Could not delete the log:\n{exc}")
            return
        self._fill_days(keep=date.today())
        self.reload(force=True)

    def closeEvent(self, event):
        self.timer.stop()
        event.accept()


_open = {}


def open_furlog(desktop):
    win = _open.get("win")
    if win is None or not isValid(win):
        body = FurryLog(desktop)
        win = XPWindow(desktop, "Furry Log", body, furlog_icon(16), (760, 560))
        body.frame = win
        _open["win"] = win
    desktop.open_window(win)
    return win
