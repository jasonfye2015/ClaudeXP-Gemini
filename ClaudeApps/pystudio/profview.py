"""The report window for Copilot Python Studio's profiler: FPS numbers, a frame-time graph and the slowest functions."""
import json
import os

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (QCheckBox, QHBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout,
                               QWidget)


def load(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def is_user_code(report, row):
    f = os.path.normcase(row["file"])
    return f.startswith(os.path.normcase(report["script_dir"])) and "<" not in row["file"]


def verdict(report):
    """One plain sentence about how the game ran."""
    if not report.get("frames"):
        return "No frames were drawn. FPS is measured when the program calls pygame.display.flip() or update()."
    fps = report["avg_fps"]
    if fps >= 55:
        text = "Smooth: it holds about 60 FPS."
    elif fps >= 30:
        text = "Playable, but below 60 FPS. The slowest functions below are the place to look."
    else:
        text = "Slow: under 30 FPS. Fix the top item in the list first."
    if report["slow"] and fps >= 30:
        text += f" {report['slow']} frames dipped under 30 FPS, which shows up as stutter."
    return text


def summary_for_ai(report, limit=8):
    rows = [r for r in report["functions"] if is_user_code(report, r)][:limit] or report["functions"][:limit]
    lines = []
    for r in rows:
        lines.append(f"- {r['name']} ({os.path.basename(r['file'])}:{r['line']}): {r['calls']} calls, "
                     f"{r['own'] * 1000:.0f} ms own time, {r['cum'] * 1000:.0f} ms total")
    head = ""
    if report.get("frames"):
        head = (f"It averages {report['avg_fps']:.0f} FPS (1% low {report['low1']:.0f} FPS, worst frame "
                f"{report['worst_ms']:.0f} ms).\n")
    return head + "Profiler results, slowest first:\n" + "\n".join(lines)


class Graph(QWidget):
    def __init__(self):
        super().__init__()
        self.times = []
        self.setMinimumHeight(90)

    def paintEvent(self, _event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor("#101010"))
        w, h = self.width(), self.height()
        top_ms = 50.0
        for ms, color in ((16.7, "#2E7D32"), (33.3, "#B58900")):
            y = h - ms / top_ms * h
            p.setPen(QPen(QColor(color), 1, Qt.DashLine))
            p.drawLine(0, int(y), w, int(y))
            p.setPen(QColor(color))
            p.drawText(4, int(y) - 2, f"{1000 / ms:.0f} FPS")
        if not self.times:
            p.setPen(QColor("#808080"))
            p.drawText(self.rect(), Qt.AlignCenter, "no frame data")
            return
        n = len(self.times)
        bar = max(1.0, w / n)
        for i, t in enumerate(self.times):
            ms = t * 1000
            color = "#50DC50" if ms < 20 else "#E6C83C" if ms < 33.4 else "#E64646"
            height = min(h, ms / top_ms * h)
            p.fillRect(QRectF(i * bar, h - height, max(1.0, bar - 0.5), height), QColor(color))


class ProfileReport(QWidget):
    """`ask_ai(text)` and `open_at(path, line)` are supplied by the studio."""

    def __init__(self, ask_ai, open_at):
        super().__init__()
        self.ask_ai, self.open_at = ask_ai, open_at
        self.report = None
        root = QVBoxLayout(self)
        root.setContentsMargins(6, 6, 6, 6)
        self.headline = QLabel("Run a program with Run > Profile to see a report here.")
        self.headline.setWordWrap(True)
        self.numbers = QLabel("")
        self.graph = Graph()
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Function", "Calls", "Own time (ms)", "Total (ms)", "Where"])
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.verticalHeader().hide()
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setColumnWidth(0, 220)
        self.table.cellDoubleClicked.connect(self._open_row)
        self.mine = QCheckBox("Only my code")
        self.mine.setChecked(True)
        self.mine.toggled.connect(self._fill)
        self.ask = QPushButton("Ask the AI how to speed this up")
        self.ask.clicked.connect(self._ask)
        self.ask.setEnabled(False)
        row = QHBoxLayout()
        row.addWidget(self.mine)
        row.addStretch()
        row.addWidget(self.ask)
        hint = QLabel("Double-click a row to jump to that function. Own time is time spent inside the function itself.")
        hint.setStyleSheet("QLabel { color: #606060; }")
        for wdg in (self.headline, self.numbers, self.graph):
            root.addWidget(wdg)
        root.addWidget(self.table, 1)
        root.addLayout(row)
        root.addWidget(hint)
        self.rows = []

    def show_report(self, report):
        self.report = report
        self.headline.setText("<b>" + verdict(report) + "</b>")
        if report.get("frames"):
            self.numbers.setText(
                f"{report['avg_fps']:.1f} FPS average   |   1% low {report['low1']:.1f} FPS   |   "
                f"worst frame {report['worst_ms']:.0f} ms   |   {report['frames']} frames in {report['seconds']:.1f} s"
                + ("" if report.get("final") else "   (program was still running)"))
        else:
            self.numbers.setText(f"Ran for {report['seconds']:.1f} s.")
        self.graph.times = report.get("times", [])
        self.graph.update()
        self.ask.setEnabled(bool(report.get("functions")))
        self._fill()

    def _fill(self, *_):
        self.table.setRowCount(0)
        if not self.report:
            return
        rows = self.report["functions"]
        if self.mine.isChecked():
            mine = [r for r in rows if is_user_code(self.report, r)]
            rows = mine or rows
        self.rows = rows[:25]
        for r in self.rows:
            i = self.table.rowCount()
            self.table.insertRow(i)
            where = f"{os.path.basename(r['file'])}:{r['line']}" if "<" not in r["file"] else "(built in)"
            for c, v in enumerate((r["name"], f"{r['calls']}", f"{r['own'] * 1000:.1f}", f"{r['cum'] * 1000:.1f}", where)):
                item = QTableWidgetItem(v)
                if c in (1, 2, 3):
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.table.setItem(i, c, item)

    def _open_row(self, row, _col):
        if 0 <= row < len(self.rows):
            r = self.rows[row]
            if os.path.isfile(r["file"]):
                self.open_at(r["file"], r["line"])

    def _ask(self):
        if self.report:
            self.ask_ai("This program is too slow. Using these profiler results, say which parts are the bottleneck "
                        "and show the smallest changes that make it faster.\n\n" + summary_for_ai(self.report))
