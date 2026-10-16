"""Studio side of the debugger: a local socket the runner (dbg_runner.py) connects to, and the Debug panel."""
import json

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtNetwork import QHostAddress, QTcpServer
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QSplitter, QTreeWidget,
                               QTreeWidgetItem, QVBoxLayout, QWidget)


class DebugSession(QObject):
    stopped = Signal(dict)            # file, line, func, locals, globals, stack
    evaluated = Signal(str, str)
    raised = Signal(str)
    ended = Signal()

    def __init__(self):
        super().__init__()
        self.server = QTcpServer(self)
        self.server.listen(QHostAddress.LocalHost, 0)
        self.server.newConnection.connect(self._connected)
        self.sock = None
        self.buffer = b""
        self.paused = False
        self.finished = False

    def port(self):
        return self.server.serverPort()

    def _connected(self):
        self.sock = self.server.nextPendingConnection()
        self.sock.readyRead.connect(self._read)
        self.sock.disconnected.connect(self._gone)
        self.server.close()

    def _read(self):
        self.buffer += bytes(self.sock.readAll())
        while b"\n" in self.buffer:
            line, self.buffer = self.buffer.split(b"\n", 1)
            try:
                msg = json.loads(line.decode("utf-8"))
            except ValueError:
                continue
            kind = msg.pop("ev", "")
            if kind == "stop":
                self.paused = True
                self.stopped.emit(msg)
            elif kind == "eval":
                self.evaluated.emit(msg["expr"], msg["result"])
            elif kind == "exception":
                self.raised.emit(msg["text"])
            elif kind == "end":
                self._gone()

    def _gone(self):
        if not self.finished:
            self.finished = True
            self.paused = False
            self.ended.emit()

    def command(self, cmd, **extra):
        if self.sock is None or self.finished:
            return
        if cmd in ("continue", "step", "next", "out", "quit"):
            self.paused = False
        self.sock.write((json.dumps(dict(cmd=cmd, **extra)) + "\n").encode("utf-8"))
        self.sock.flush()

    def close(self):
        self.finished = True
        self.server.close()
        if self.sock is not None:
            self.sock.abort()


class DebugPanel(QWidget):
    """Variables, call stack and an 'evaluate' box. `on_frame(file, line)` is called when a stack row is clicked."""

    def __init__(self, evaluate, on_frame):
        super().__init__()
        self.evaluate_fn, self.on_frame = evaluate, on_frame
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        split = QSplitter(Qt.Horizontal)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Name", "Type", "Value"])
        self.tree.setColumnWidth(0, 130)
        self.tree.setColumnWidth(1, 70)
        self.stack = QListWidget()
        self.stack.itemClicked.connect(self._frame_clicked)
        split.addWidget(self.tree)
        split.addWidget(self.stack)
        split.setSizes([420, 200])
        root.addWidget(split, 1)
        row = QHBoxLayout()
        row.setContentsMargins(4, 2, 4, 2)
        self.expr = QLineEdit()
        self.expr.setPlaceholderText("Evaluate an expression while paused, e.g. player.x + 5, then press Enter")
        self.expr.returnPressed.connect(self._submit)
        self.result = QLabel("")
        self.result.setStyleSheet("QLabel { font-family: Consolas; color: #1A4F9C; }")
        row.addWidget(self.expr, 2)
        row.addWidget(self.result, 1)
        root.addLayout(row)
        self.stack_rows = []

    def _submit(self):
        text = self.expr.text().strip()
        if text:
            self.evaluate_fn(text)

    def _frame_clicked(self, item):
        self.on_frame(*item.data(Qt.UserRole))

    def show_stop(self, info):
        self.tree.clear()
        for title, rows in (("Locals", info.get("locals", [])), ("Globals", info.get("globals", []))):
            top = QTreeWidgetItem([title])
            top.setFirstColumnSpanned(True)
            self.tree.addTopLevelItem(top)
            for row in rows:
                top.addChild(QTreeWidgetItem(row))
            top.setExpanded(title == "Locals" or not info.get("locals"))
        self.stack.clear()
        for file, line, func in info.get("stack", []):
            item = QListWidgetItem(f"{func}   line {line}")
            item.setData(Qt.UserRole, (file, line))
            self.stack.addItem(item)

    def clear(self):
        self.tree.clear()
        self.stack.clear()
        self.result.setText("")
