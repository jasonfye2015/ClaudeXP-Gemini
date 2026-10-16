"""Run History tab for Python Studio."""
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QComboBox, QHBoxLayout, QLabel, QListWidget, QPlainTextEdit, QPushButton, QSplitter,
                               QVBoxLayout, QWidget)

from . import runhistory


class HistoryPanel(QWidget):
    """open_version(title, text) opens code in a new tab; ask(text) asks the AI Helper;
    current_source(path) returns the open text of a file or None."""

    def __init__(self, open_version, ask, current_source):
        super().__init__()
        self.open_version, self.ask, self.current_source = open_version, ask, current_source
        self.records = []
        self.list = QListWidget()
        self.list.setMaximumWidth(260)
        self.list.currentRowChanged.connect(self._show)
        self.view = QComboBox()
        for text in ("What it printed", "Code changes since the run before", "Code changes compared with now"):
            self.view.addItem(text)
        self.view.currentIndexChanged.connect(lambda _i: self._show(self.list.currentRow()))
        self.text = QPlainTextEdit()
        self.text.setReadOnly(True)
        self.text.setProperty("nospell", True)
        self.text.setFont(QFont("Consolas", 10))
        self.text.setStyleSheet("QPlainTextEdit { background: white; color: black; border: none; }")
        self.note = QLabel("")
        self.open_btn = QPushButton("Open code")
        self.open_btn.setToolTip("Open the code as it was in this run, in a new tab")
        self.why_btn = QPushButton("\u2728 Why?")
        self.clear_btn = QPushButton("Clear")
        self.open_btn.clicked.connect(self.open_selected)
        self.why_btn.clicked.connect(self.ask_why)
        self.clear_btn.clicked.connect(self.clear)
        row = QHBoxLayout()
        for w in (self.open_btn, self.why_btn, self.clear_btn):
            row.addWidget(w)
        row.addStretch()
        right = QWidget()
        box = QVBoxLayout(right)
        box.setContentsMargins(0, 0, 0, 0)
        box.addWidget(self.view)
        box.addWidget(self.text, 1)
        box.addWidget(self.note)
        box.addLayout(row)
        split = QSplitter()
        split.addWidget(self.list)
        split.addWidget(right)
        split.setStretchFactor(1, 1)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(split)
        self.refresh()

    def refresh(self):
        self.records = runhistory.load()
        self.list.blockSignals(True)
        self.list.clear()
        for rec in reversed(self.records):
            self.list.addItem(runhistory.label(rec))
        self.list.blockSignals(False)
        if self.records:
            self.list.setCurrentRow(0)
        else:
            self._show(-1)

    def index(self):
        row = self.list.currentRow()
        return len(self.records) - 1 - row if row >= 0 else None

    def _show(self, _row):
        i = self.index()
        failing = False
        if i is None:
            self.text.setPlainText("Nothing has been run yet. Run a program and it appears here.")
            self.note.setText("")
        else:
            rec = self.records[i]
            mode = self.view.currentIndex()
            if mode == 0:
                self.text.setPlainText(rec["output"] or "(it printed nothing)")
                self.note.setText(f"{rec['kind']} of {rec['file']}")
            elif mode == 1:
                j = runhistory.previous_same(self.records, i)
                diff = runhistory.code_diff(self.records[j]["source"], rec["source"], "run before", "this run") \
                    if j is not None else ""
                self.text.setPlainText(diff or ("No earlier run of this file to compare with." if j is None
                                                else "The code is the same as the run before."))
                self.note.setText("")
            else:
                now = self.current_source(rec["file"])
                diff = runhistory.code_diff(rec["source"], now, "this run", "now") if now is not None else ""
                self.text.setPlainText(diff or ("That file isn't open." if now is None
                                                else "The code is the same as it was in this run."))
                self.note.setText("")
            failing = runhistory.why_prompt(self.records, i) is not None
        self.open_btn.setEnabled(i is not None)
        self.why_btn.setEnabled(failing)
        self.why_btn.setToolTip("Ask the AI what changed since it last worked" if failing else
                                "Needs a failed run and an earlier successful run of the same file")
        self.clear_btn.setEnabled(bool(self.records))

    def open_selected(self):
        i = self.index()
        if i is not None:
            rec = self.records[i]
            self.open_version(f"{rec['file']} ({rec['time']})", rec["source"])

    def ask_why(self):
        i = self.index()
        prompt = runhistory.why_prompt(self.records, i) if i is not None else None
        if prompt:
            self.ask(prompt)

    def clear(self):
        runhistory.clear()
        self.refresh()
