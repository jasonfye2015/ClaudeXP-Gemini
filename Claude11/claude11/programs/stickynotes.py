"""Sticky Notes: yellow (or blue, green, pink, purple, white) notes on the desktop. + for a new note, x to delete,
drag the top strip, pull the corner to resize, right-click for the colour. They stay where you left them between
log-ons (data/stickynotes.json)."""
import json
import uuid

from PySide6.QtCore import QPoint, QRect, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPen
from PySide6.QtWidgets import QMenu, QTextEdit, QWidget
from shiboken6 import isValid

from .. import sound
from ..paths import DATA

NOTES_FILE = DATA / "stickynotes.json"
COLORS = {"Blue": ("#CFE7FA", "#B6D8F2"), "Green": ("#D6F5C0", "#BEEBA2"), "Pink": ("#FAD0DE", "#F5B8CE"),
          "Purple": ("#E0D3F3", "#CFBCEC"), "White": ("#FFFFFF", "#EDEDED"), "Yellow": ("#FFF7A6", "#F8E97A")}
STRIP = 22
MIN_W, MIN_H = 150, 150
_controller = None


class Note(QWidget):
    def __init__(self, notes, data):
        super().__init__(notes.desktop)
        self.notes = notes
        self.data = data
        self.hover = False
        self.drag = None
        self.resizing = None
        self.setMouseTracking(True)
        self.setMinimumSize(MIN_W, MIN_H)
        self.edit = QTextEdit(self)
        self.edit.setFrameShape(QTextEdit.NoFrame)
        self.edit.setAcceptRichText(False)
        f = QFont("Segoe Print")
        f.setPixelSize(15)
        self.edit.setFont(f)
        self.edit.setPlainText(data.get("text", ""))
        self.edit.setStyleSheet("QTextEdit { background: transparent; color: #1E1E1E; }")
        self.edit.textChanged.connect(self._changed)
        self.edit.setContextMenuPolicy(Qt.CustomContextMenu)
        self.edit.customContextMenuRequested.connect(lambda pos: self._menu(self.edit.mapToGlobal(pos)))
        self.save_timer = QTimer(self)
        self.save_timer.setSingleShot(True)
        self.save_timer.timeout.connect(self.notes.save)
        self.setGeometry(data.get("x", 40), data.get("y", 40), max(MIN_W, data.get("w", 190)),
                         max(MIN_H, data.get("h", 190)))

    def resizeEvent(self, event):
        self.edit.setGeometry(6, STRIP + 2, self.width() - 12, self.height() - STRIP - 10)

    def colours(self):
        return COLORS.get(self.data.get("color", "Yellow"), COLORS["Yellow"])

    def _changed(self):
        self.data["text"] = self.edit.toPlainText()
        self.save_timer.start(800)

    def _plus_rect(self):
        return QRect(4, 2, 18, STRIP - 4)

    def _x_rect(self):
        return QRect(self.width() - 22, 2, 18, STRIP - 4)

    def _grip_rect(self):
        return QRect(self.width() - 14, self.height() - 14, 14, 14)

    def enterEvent(self, event):
        self.hover = True
        self.update()

    def leaveEvent(self, event):
        self.hover = False
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            self._menu(event.globalPosition().toPoint())
            return
        pos = event.position().toPoint()
        self.raise_()
        if self._plus_rect().contains(pos):
            self.notes.new_note(near=self)
        elif self._x_rect().contains(pos):
            self.notes.delete(self)
        elif self._grip_rect().contains(pos):
            self.resizing = (event.globalPosition().toPoint(), self.size())
        elif pos.y() < STRIP:
            self.drag = event.globalPosition().toPoint() - self.pos()

    def mouseMoveEvent(self, event):
        gp = event.globalPosition().toPoint()
        if self.drag is not None:
            area = self.notes.desktop.work_area()
            p = gp - self.drag
            p.setX(max(-self.width() + 40, min(p.x(), area.width() - 40)))
            p.setY(max(0, min(p.y(), area.height() - STRIP)))
            self.move(p)
        elif self.resizing is not None:
            start, size = self.resizing
            self.resize(max(MIN_W, size.width() + gp.x() - start.x()), max(MIN_H, size.height() + gp.y() - start.y()))
        else:
            pos = event.position().toPoint()
            self.setCursor(Qt.SizeFDiagCursor if self._grip_rect().contains(pos) else
                           Qt.SizeAllCursor if pos.y() < STRIP and not self._plus_rect().contains(pos)
                           and not self._x_rect().contains(pos) else Qt.ArrowCursor)

    def mouseReleaseEvent(self, event):
        if self.drag is not None or self.resizing is not None:
            self.drag = self.resizing = None
            self.data.update(x=self.x(), y=self.y(), w=self.width(), h=self.height())
            self.notes.save()

    def _menu(self, gp):
        from ..shims import MENU_CSS
        menu = QMenu(self)
        menu.setStyleSheet(MENU_CSS)
        for name in COLORS:
            a = menu.addAction(name, lambda n=name: self.set_color(n))
            a.setCheckable(True)
            a.setChecked(self.data.get("color", "Yellow") == name)
        menu.addSeparator()
        menu.addAction("Delete Note", lambda: self.notes.delete(self))
        menu.popup(gp)

    def set_color(self, name):
        self.data["color"] = name
        self.notes.save()
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        body, strip = self.colours()
        p.fillRect(self.rect(), QColor(body))
        g = QLinearGradient(0, 0, 0, STRIP)
        g.setColorAt(0, QColor(strip).lighter(104))
        g.setColorAt(1, QColor(strip))
        p.fillRect(QRect(0, 0, self.width(), STRIP), g)
        p.setPen(QPen(QColor(0, 0, 0, 40), 1))
        p.drawRect(QRectF(0.5, 0.5, self.width() - 1, self.height() - 1))
        if self.hover:
            f = QFont("Segoe UI")
            f.setPixelSize(16)
            p.setFont(f)
            p.setPen(QColor("#4A4A4A"))
            p.drawText(self._plus_rect(), Qt.AlignCenter, "+")
            p.drawText(self._x_rect(), Qt.AlignCenter, "×")
        p.setPen(QPen(QColor(0, 0, 0, 50), 1))
        gr = self._grip_rect()
        for i in (3, 7, 11):
            p.drawLine(gr.right() - i, gr.bottom(), gr.right(), gr.bottom() - i)


class StickyNotes:
    def __init__(self, desktop):
        self.desktop = desktop
        self.notes = []
        self.loaded = False

    def load(self):
        if self.loaded:
            return
        self.loaded = True
        try:
            data = json.loads(NOTES_FILE.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            data = {}
        for d in data.get("notes", []):
            self.notes.append(Note(self, d))

    def save(self):
        try:
            NOTES_FILE.parent.mkdir(parents=True, exist_ok=True)
            NOTES_FILE.write_text(json.dumps({"notes": [n.data for n in self.notes if isValid(n)]}, indent=2),
                                  encoding="utf-8")
        except OSError:
            pass

    def live(self):
        self.notes = [n for n in self.notes if isValid(n)]
        return self.notes

    def new_note(self, near=None):
        x, y = (near.x() + near.width() + 12, near.y()) if near is not None else (60, 60)
        area = self.desktop.work_area()
        if x + MIN_W > area.width():
            x, y = near.x(), near.y() + near.height() + 12
        d = {"id": uuid.uuid4().hex[:8], "text": "", "color": near.data.get("color", "Yellow") if near else "Yellow",
             "x": x, "y": min(y, area.height() - MIN_H), "w": 190, "h": 190}
        n = Note(self, d)
        self.notes.append(n)
        n.show()
        n.raise_()
        n.edit.setFocus()
        self.save()
        return n

    def delete(self, note):
        if note in self.notes:
            self.notes.remove(note)
        note.hide()
        note.deleteLater()
        sound.play("recycle")
        self.save()

    def show_all(self):
        for n in self.live():
            n.show()
            n.raise_()

    def hide_all(self):
        for n in self.live():
            n.hide()


def _get(desktop):
    global _controller
    if _controller is None or _controller.desktop is not desktop:
        _controller = StickyNotes(desktop)
    _controller.load()
    return _controller


def launch(desktop):
    c = _get(desktop)
    sound.play("navigate")
    if not c.live():
        c.new_note()
    else:
        c.show_all()


def start_at_logon(desktop):
    c = _get(desktop)
    if c.live():
        c.show_all()


def hide_all(desktop):
    if _controller is not None:
        _controller.save()
        _controller.hide_all()


def shutdown():
    if _controller is not None:
        _controller.save()
