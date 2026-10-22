"""The Snipping Tool: New, drag around a piece of the screen, and the snip opens in the tool's window - pen,
highlighter, eraser, copy, and Save As into your Pictures."""
from PySide6.QtCore import QPoint, QRect, Qt
from PySide6.QtGui import QColor, QGuiApplication, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QHBoxLayout, QInputDialog, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget
from shiboken6 import isValid

from .. import sound
from ..wm import MicaWindow

TOOL = ("QPushButton { background: transparent; border: 1px solid transparent; border-radius: 3px;"
        " font-family: 'Segoe UI'; font-size: 12px; padding: 3px 10px; }"
        "QPushButton:hover { border: 1px solid #7DA2CE; background: #E8F0FA; }"
        "QPushButton:checked { border: 1px solid #7DA2CE; background: #CCE4F7; }")
_open = {}


class Overlay(QWidget):
    """The whitened screen you drag a rectangle on."""

    def __init__(self, desktop, on_done):
        super().__init__(desktop)
        self.on_done = on_done
        self.start = None
        self.cur = None
        self.setGeometry(desktop.rect())
        self.setCursor(Qt.CrossCursor)
        self.setFocusPolicy(Qt.StrongFocus)
        self.show()
        self.raise_()
        self.setFocus()

    def mousePressEvent(self, event):
        self.start = self.cur = event.position().toPoint()
        self.update()

    def mouseMoveEvent(self, event):
        if self.start is not None:
            self.cur = event.position().toPoint()
            self.update()

    def mouseReleaseEvent(self, event):
        if self.start is None:
            return
        rect = QRect(self.start, self.cur).normalized()
        self.hide()
        self.deleteLater()
        self.on_done(rect if rect.width() > 2 and rect.height() > 2 else None)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.hide()
            self.deleteLater()
            self.on_done(None)

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(255, 255, 255, 110))
        if self.start is not None:
            r = QRect(self.start, self.cur).normalized()
            p.setCompositionMode(QPainter.CompositionMode_Clear)
            p.fillRect(r, Qt.transparent)
            p.setCompositionMode(QPainter.CompositionMode_SourceOver)
            p.setPen(QPen(QColor("#E3242B"), 2))
            p.setBrush(Qt.NoBrush)
            p.drawRect(r)


class Canvas(QLabel):
    def __init__(self, pixmap):
        super().__init__()
        self.original = pixmap
        self.strokes = []
        self.tool = None
        self.current = None
        self.setFixedSize(pixmap.size())
        self.render()

    def render(self):
        pm = QPixmap(self.original)
        p = QPainter(pm)
        p.setRenderHint(QPainter.Antialiasing)
        for tool, pts in self.strokes + ([self.current] if self.current else []):
            if tool == "pen":
                p.setPen(QPen(QColor("#E3242B"), 2.5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            else:
                p.setPen(QPen(QColor(255, 240, 0, 110), 14, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            for a, b in zip(pts, pts[1:]):
                p.drawLine(a, b)
        p.end()
        self.setPixmap(pm)

    def mousePressEvent(self, event):
        pos = event.position().toPoint()
        if self.tool in ("pen", "highlighter"):
            self.current = (self.tool, [pos])
        elif self.tool == "eraser":
            self.strokes = [s for s in self.strokes if not any((pt - pos).manhattanLength() < 12 for pt in s[1])]
            self.render()

    def mouseMoveEvent(self, event):
        if self.current:
            self.current[1].append(event.position().toPoint())
            self.render()

    def mouseReleaseEvent(self, event):
        if self.current:
            self.strokes.append(self.current)
            self.current = None
            self.render()


class Editor(QWidget):
    def __init__(self, desktop, pixmap):
        super().__init__()
        self.desktop = desktop
        self.setStyleSheet("background: #F0F0F0;")
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        bar = QWidget()
        bar.setStyleSheet("background: #F7F9FC; border-bottom: 1px solid #DDE3EA;")
        bar.setAttribute(Qt.WA_StyledBackground, True)
        hl = QHBoxLayout(bar)
        hl.setContentsMargins(6, 4, 6, 4)
        hl.setSpacing(2)
        self.canvas = Canvas(pixmap)
        tools = []
        for text, slot, check in (("New", lambda: new_snip(desktop), False), ("Save As", self.save, False),
                                  ("Copy", self.copy, False), ("Pen", lambda: self.set_tool("pen"), True),
                                  ("Highlighter", lambda: self.set_tool("highlighter"), True),
                                  ("Eraser", lambda: self.set_tool("eraser"), True)):
            b = QPushButton(text)
            b.setStyleSheet(TOOL)
            b.setCheckable(check)
            b.clicked.connect(lambda _c=False, s=slot: s())
            hl.addWidget(b)
            if check:
                tools.append(b)
        self.tools = tools
        hl.addStretch()
        root.addWidget(bar)
        scroll = QScrollArea()
        scroll.setWidgetResizable(False)
        scroll.setStyleSheet("background: #FFFFFF;")
        scroll.setWidget(self.canvas)
        root.addWidget(scroll, 1)

    def set_tool(self, name):
        self.canvas.tool = None if self.canvas.tool == name else name
        for b in self.tools:
            b.setChecked(b.text().lower() == (self.canvas.tool or ""))

    def copy(self):
        QGuiApplication.clipboard().setPixmap(self.canvas.pixmap())
        sound.play("default")

    def save(self):
        from .. import vfs
        from ..dialogs import msgbox
        name, ok = QInputDialog.getText(self, "Save As", "File name:", text="Capture")
        if not ok or not name.strip():
            return
        folder = vfs.my_pictures()
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / (name.strip() + ".png")
        n = 2
        while path.exists():
            path = folder / f"{name.strip()} ({n}).png"
            n += 1
        self.canvas.pixmap().save(str(path), "PNG")
        msgbox(self.desktop, "Snipping Tool", f"Saved as {path.name} in your Pictures.", "info")


class ToolBody(QWidget):
    def __init__(self, desktop):
        super().__init__()
        self.setStyleSheet("background: #F0F0F0;")
        v = QVBoxLayout(self)
        v.setContentsMargins(8, 6, 8, 8)
        row = QHBoxLayout()
        for text, slot in (("New", lambda: new_snip(desktop)), ("Cancel", lambda: None),
                           ("Options", lambda: None)):
            b = QPushButton(text)
            b.setStyleSheet(TOOL)
            b.clicked.connect(lambda _c=False, s=slot: s())
            row.addWidget(b)
        row.addStretch()
        v.addLayout(row)
        lab = QLabel("Drag the cursor around the area you want to capture.")
        lab.setStyleSheet("font-family: 'Segoe UI'; font-size: 12px; color: #1E1E1E; padding: 10px;")
        lab.setWordWrap(True)
        v.addWidget(lab)
        v.addStretch()


def _icon():
    from . import scissors_icon
    return scissors_icon()


def launch(desktop):
    win = _open.get("tool")
    if win is None or not isValid(win) or win not in desktop.windows:
        win = MicaWindow(desktop, "Snipping Tool", ToolBody(desktop), _icon(), (360, 130), buttons=("min", "close"))
        win.resizable = False
        _open["tool"] = win
    desktop.open_window(win)
    sound.play("navigate")


def new_snip(desktop):
    tool = _open.get("tool")
    if tool is not None and isValid(tool) and tool.isVisible():
        tool.hide()

    def done(rect):
        if tool is not None and isValid(tool) and tool in desktop.windows:
            tool.show()
        if rect is None:
            return
        from PySide6.QtWidgets import QApplication
        QApplication.processEvents()
        shot = desktop.grab(rect)
        editor = MicaWindow(desktop, "Snipping Tool", Editor(desktop, shot), _icon(),
                            (min(desktop.width() - 60, rect.width() + 40), min(desktop.height() - 80, rect.height() + 90)))
        _open.setdefault("editors", []).append(editor)
        desktop.open_window(editor)
        sound.play("default")
    Overlay(desktop, done)


def shutdown():
    for key in ("tool",):
        win = _open.get(key)
        if win is not None and isValid(win):
            win.request_close()
    for win in _open.get("editors", []):
        if isValid(win):
            win.request_close()
    _open.clear()
