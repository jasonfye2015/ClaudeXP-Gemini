"""Test results for Copilot Python Studio: parses pytest's JUnit XML and shows pass/fail per test."""
import os
import re
import xml.etree.ElementTree as ET

from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QPlainTextEdit, QPushButton, QSplitter, QTreeWidget, QTreeWidgetItem,
                               QVBoxLayout, QWidget)

COLORS = {"passed": "#1B7F1B", "failed": "#C00000", "error": "#C00000", "skipped": "#808080"}
MARK = {"passed": "PASS", "failed": "FAIL", "error": "ERROR", "skipped": "skip"}


def parse(xml_path):
    """A list of dicts: name, status, time, message, detail, file, line. None if the file can't be read."""
    try:
        root = ET.parse(xml_path).getroot()
    except (OSError, ET.ParseError):
        return None
    tests = []
    for case in root.iter("testcase"):
        status, message, detail = "passed", "", ""
        for tag in ("failure", "error", "skipped"):
            node = case.find(tag)
            if node is not None:
                status = "failed" if tag == "failure" else tag
                message = (node.get("message") or "").strip()
                detail = (node.text or "").strip()
                break
        cls = case.get("classname") or ""
        tests.append({"name": f"{cls}.{case.get('name')}" if cls else case.get("name"), "status": status,
                      "time": float(case.get("time") or 0), "message": message, "detail": detail,
                      "module": cls.split(".")[-1] if cls else ""})
    return tests


def locate(test, folder):
    """(path, line) of the last project-file line in the traceback, or the test module itself."""
    folder = os.path.normcase(os.path.abspath(folder))
    hit = None
    for m in re.finditer(r"^(?:[A-Za-z]:)?[^\s:<>|?*\"]*\.py:(\d+):", test["detail"], re.M):
        text = m.group(0)[: m.group(0).rfind(":", 0, -1)]
        path = os.path.abspath(os.path.join(folder, text))
        if os.path.normcase(path).startswith(folder) and os.path.isfile(path):
            hit = (path, int(m.group(1)))
    return hit


def counts(tests):
    c = {"passed": 0, "failed": 0, "error": 0, "skipped": 0}
    for t in tests:
        c[t["status"]] += 1
    return c


def headline(tests):
    if not tests:
        return "No tests were found."
    c = counts(tests)
    bad = c["failed"] + c["error"]
    parts = [f"{c['passed']} passed"]
    if bad:
        parts.insert(0, f"{bad} failed")
    if c["skipped"]:
        parts.append(f"{c['skipped']} skipped")
    return ("All tests pass: " if not bad else "Problems: ") + ", ".join(parts) + f" ({len(tests)} total)."


def failures_for_ai(tests, limit=4, chars=1200):
    out = []
    for t in tests:
        if t["status"] in ("failed", "error"):
            out.append(f"Test {t['name']} {t['status']}:\n{(t['detail'] or t['message'])[:chars]}")
        if len(out) >= limit:
            break
    return "\n\n".join(out)


class TestResults(QWidget):
    """`rerun()`, `open_at(path, line)` and `ask_ai(text)` come from the studio."""

    def __init__(self, rerun, open_at, ask_ai):
        super().__init__()
        self.rerun, self.open_at, self.ask_ai = rerun, open_at, ask_ai
        self.tests, self.folder = [], ""
        root = QVBoxLayout(self)
        root.setContentsMargins(6, 6, 6, 6)
        self.headline = QLabel("Run > Run Tests to see results here.")
        self.headline.setWordWrap(True)
        root.addWidget(self.headline)
        split = QSplitter(Qt.Vertical)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Test", "Result", "Time"])
        self.tree.setRootIsDecorated(False)
        self.tree.setColumnWidth(0, 360)
        self.tree.currentItemChanged.connect(self._show)
        self.tree.itemDoubleClicked.connect(lambda *_: self._open())
        self.detail = QPlainTextEdit()
        self.detail.setReadOnly(True)
        self.detail.setProperty("nospell", True)
        self.detail.setPlaceholderText("Select a test to see why it failed. Double-click to jump to the line.")
        split.addWidget(self.tree)
        split.addWidget(self.detail)
        split.setSizes([260, 200])
        root.addWidget(split, 1)
        row = QHBoxLayout()
        self.again = QPushButton("Run again")
        self.again.clicked.connect(lambda: self.rerun())
        self.fix = QPushButton("Ask the AI to fix the failures")
        self.fix.clicked.connect(self._ask)
        row.addWidget(self.again)
        row.addStretch()
        row.addWidget(self.fix)
        root.addLayout(row)

    def show_results(self, tests, folder, note=""):
        self.tests, self.folder = tests or [], folder
        self.headline.setText("<b>" + headline(self.tests) + "</b>" + (f"<br>{note}" if note else ""))
        self.tree.clear()
        order = {"failed": 0, "error": 0, "passed": 1, "skipped": 2}
        first_bad = None
        for t in sorted(self.tests, key=lambda t: order[t["status"]]):
            item = QTreeWidgetItem([t["name"], MARK[t["status"]], f"{t['time'] * 1000:.0f} ms"])
            item.setData(0, Qt.UserRole, t)
            item.setForeground(1, QBrush(QColor(COLORS[t["status"]])))
            self.tree.addTopLevelItem(item)
            if first_bad is None and t["status"] in ("failed", "error"):
                first_bad = item
        if first_bad is not None:
            self.tree.setCurrentItem(first_bad)
        else:
            self.detail.clear()
        self.fix.setEnabled(first_bad is not None)

    def _show(self, item, _old=None):
        t = item.data(0, Qt.UserRole) if item is not None else None
        self.detail.setPlainText((t["detail"] or t["message"] or "Passed.") if t else "")

    def _open(self):
        item = self.tree.currentItem()
        t = item.data(0, Qt.UserRole) if item is not None else None
        spot = locate(t, self.folder) if t else None
        if spot:
            self.open_at(*spot)

    def _ask(self):
        text = failures_for_ai(self.tests)
        if text:
            self.ask_ai("These pytest tests fail. Explain the cause of each and show the corrected code. If the "
                        "tests themselves are wrong say so.\n\n" + text)
