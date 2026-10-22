"""Sticky Notes, Windows 11 style: pastel notes (yellow, green, pink, purple, blue, gray or charcoal) with a coloured
strip along the top - + for a new note, the ... menu for the colour, x to close - a formatting bar along the bottom
(bold, italic, underline, strikethrough, bullets), a soft shadow, drag the strip, pull the corner to resize. They
stay where you left them between sign-ins (data/stickynotes.json)."""
import json
import uuid

from PySide6.QtCore import QPoint, QRect, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QPixmap, QTextCharFormat, QTextCursor, QTextListFormat
from PySide6.QtWidgets import QMenu, QTextEdit, QWidget
from shiboken6 import isValid

from .. import sound
from ..paths import DATA

NOTES_FILE = DATA / "stickynotes.json"
# body, strip, text
COLORS = {"Yellow": ("#FFF7D1", "#FFE66D", "#1A1A1A"), "Green": ("#E4F9E0", "#B9E8B0", "#1A1A1A"),
          "Pink": ("#FFE4F1", "#FFC3DE", "#1A1A1A"), "Purple": ("#F0E6FF", "#D8C8F7", "#1A1A1A"),
          "Blue": ("#E2F1FF", "#B9DBFF", "#1A1A1A"), "Gray": ("#F3F2F1", "#DADADA", "#1A1A1A"),
          "Charcoal": ("#696969", "#4E4E4E", "#FFFFFF")}
SHADOW = 6
STRIP = 34
BAR = 30
MIN_W, MIN_H = 160, 160
_controller = None


def _swatch(colour, size=14):
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(QPen(QColor(0, 0, 0, 40), 1))
    p.setBrush(QColor(colour))
    p.drawEllipse(QRectF(0.5, 0.5, size - 1, size - 1))
    p.end()
    return pm


class Note(QWidget):
    def __init__(self, notes, data):
        super().__init__(notes.desktop)
        self.notes = notes
        self.data = data
        self.hover = False
        self.hover_btn = None
        self.drag = None
        self.resizing = None
        self.setMouseTracking(True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setMinimumSize(MIN_W + 2 * SHADOW, MIN_H + 2 * SHADOW)
        self.edit = QTextEdit(self)
        self.edit.setFrameShape(QTextEdit.NoFrame)
        self.edit.setAcceptRichText(True)
        f = QFont("Segoe UI")
        f.setPixelSize(14)
        self.edit.setFont(f)
        self.edit.document().setDefaultFont(f)
        if data.get("html"):
            self.edit.setHtml(data["html"])
        else:
            self.edit.setPlainText(data.get("text", ""))
        self.edit.setPlaceholderText("Take a note...")
        self.edit.textChanged.connect(self._changed)
        self.edit.setContextMenuPolicy(Qt.CustomContextMenu)
        self.edit.customContextMenuRequested.connect(lambda pos: self._menu(self.edit.mapToGlobal(pos)))
        self.edit.setMouseTracking(True)
        self.save_timer = QTimer(self)
        self.save_timer.setSingleShot(True)
        self.save_timer.timeout.connect(self.notes.save)
        self._restyle()
        self.setGeometry(data.get("x", 40) - SHADOW, data.get("y", 40) - SHADOW,
                         max(MIN_W, data.get("w", 220)) + 2 * SHADOW, max(MIN_H, data.get("h", 220)) + 2 * SHADOW)

    def _restyle(self):
        body, _strip, text = self.colours()
        self.edit.setStyleSheet(f"QTextEdit {{ background: transparent; color: {text}; selection-background-color: "
                                f"rgba(0, 103, 192, 90); }}")
        self.edit.viewport().setStyleSheet("background: transparent;")

    def frame_rect(self):
        return self.rect().adjusted(SHADOW, SHADOW, -SHADOW, -SHADOW)

    def resizeEvent(self, event):
        fr = self.frame_rect()
        self.edit.setGeometry(fr.x() + 10, fr.y() + STRIP + 6, fr.width() - 20, fr.height() - STRIP - BAR - 8)

    def colours(self):
        return COLORS.get(self.data.get("color", "Yellow"), COLORS["Yellow"])

    def _changed(self):
        self.data["text"] = self.edit.toPlainText()
        self.data["html"] = self.edit.toHtml()
        self.save_timer.start(800)

    # ---- the strip's buttons and the formatting bar ----
    def _buttons(self):
        fr = self.frame_rect()
        return {"plus": QRect(fr.x() + 4, fr.y() + 3, 28, STRIP - 6),
                "menu": QRect(fr.right() - 60, fr.y() + 3, 28, STRIP - 6),
                "close": QRect(fr.right() - 31, fr.y() + 3, 28, STRIP - 6)}

    def _format_buttons(self):
        fr = self.frame_rect()
        y = fr.bottom() - BAR + 3
        return {name: QRect(fr.x() + 8 + i * 30, y, 26, BAR - 6)
                for i, name in enumerate(("bold", "italic", "underline", "strike", "bullets"))}

    def _grip_rect(self):
        fr = self.frame_rect()
        return QRect(fr.right() - 14, fr.bottom() - 14, 15, 15)

    def _button_at(self, pos):
        for name, r in list(self._buttons().items()) + list(self._format_buttons().items()):
            if r.contains(pos):
                return name
        return None

    def enterEvent(self, event):
        self.hover = True
        self.update()

    def leaveEvent(self, event):
        self.hover = False
        self.hover_btn = None
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            self._menu(event.globalPosition().toPoint())
            return
        pos = event.position().toPoint()
        self.raise_()
        btn = self._button_at(pos)
        if btn == "plus":
            self.notes.new_note(near=self)
        elif btn == "close":
            self.notes.close_note(self)
        elif btn == "menu":
            r = self._buttons()["menu"]
            self._menu(self.mapToGlobal(r.bottomLeft()))
        elif btn in ("bold", "italic", "underline", "strike", "bullets"):
            self._format(btn)
        elif self._grip_rect().contains(pos):
            self.resizing = (event.globalPosition().toPoint(), self.size())
        elif pos.y() < self.frame_rect().y() + STRIP:
            self.drag = event.globalPosition().toPoint() - self.pos()

    def mouseMoveEvent(self, event):
        gp = event.globalPosition().toPoint()
        if self.drag is not None:
            area = self.notes.desktop.work_area()
            p = gp - self.drag
            p.setX(max(-self.width() + 60, min(p.x(), area.width() - 60)))
            p.setY(max(-SHADOW, min(p.y(), area.height() - STRIP)))
            self.move(p)
        elif self.resizing is not None:
            start, size = self.resizing
            self.resize(max(MIN_W + 2 * SHADOW, size.width() + gp.x() - start.x()),
                        max(MIN_H + 2 * SHADOW, size.height() + gp.y() - start.y()))
        else:
            pos = event.position().toPoint()
            btn = self._button_at(pos)
            if btn != self.hover_btn:
                self.hover_btn = btn
                self.update()
            fr = self.frame_rect()
            self.setCursor(Qt.SizeFDiagCursor if self._grip_rect().contains(pos) else
                           Qt.SizeAllCursor if pos.y() < fr.y() + STRIP and btn is None else Qt.ArrowCursor)

    def mouseReleaseEvent(self, event):
        if self.drag is not None or self.resizing is not None:
            self.drag = self.resizing = None
            fr = self.frame_rect()
            self.data.update(x=self.x() + SHADOW, y=self.y() + SHADOW, w=fr.width(), h=fr.height())
            self.notes.save()

    def _format(self, what):
        cursor = self.edit.textCursor()
        if what == "bullets":
            lst = cursor.currentList()
            if lst is not None:
                fmt = cursor.blockFormat()
                fmt.setIndent(0)
                lst.remove(cursor.block())
                cursor.setBlockFormat(fmt)
            else:
                cursor.createList(QTextListFormat.ListDisc)
            self.edit.setFocus()
            return
        fmt = QTextCharFormat()
        current = cursor.charFormat()
        if what == "bold":
            fmt.setFontWeight(QFont.Normal if current.fontWeight() > QFont.Normal else QFont.Bold)
        elif what == "italic":
            fmt.setFontItalic(not current.fontItalic())
        elif what == "underline":
            fmt.setFontUnderline(not current.fontUnderline())
        elif what == "strike":
            fmt.setFontStrikeOut(not current.fontStrikeOut())
        if cursor.hasSelection():
            cursor.mergeCharFormat(fmt)
        self.edit.mergeCurrentCharFormat(fmt)
        self.edit.setFocus()

    def _menu(self, gp):
        from ..shims import MENU_CSS
        menu = QMenu(self)
        menu.setStyleSheet(MENU_CSS)
        for name, (body, _strip, _text) in COLORS.items():
            a = menu.addAction(_swatch(body), name, lambda n=name: self.set_color(n))
            a.setCheckable(True)
            a.setChecked(self.data.get("color", "Yellow") == name)
        menu.addSeparator()
        menu.addAction("Notes list", lambda: self.notes.show_all())
        menu.addAction("Delete note", lambda: self.notes.delete(self))
        menu.popup(gp)

    def set_color(self, name):
        self.data["color"] = name
        self._restyle()
        self.notes.save()
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        body, strip, text = self.colours()
        fr = self.frame_rect()
        for i in range(SHADOW, 0, -1):
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(0, 0, 0, int(18 * (1 - i / SHADOW) ** 1.5) + 1))
            p.drawRoundedRect(QRectF(fr).adjusted(-i, -i + 2, i, i + 2), 4 + i, 4 + i)
        p.setBrush(QColor(body))
        p.drawRoundedRect(QRectF(fr), 4, 4)
        p.setBrush(QColor(strip))
        p.drawRoundedRect(QRectF(fr.x(), fr.y(), fr.width(), STRIP + 4), 4, 4)
        p.fillRect(QRect(fr.x(), fr.y() + STRIP - 2, fr.width(), 6), QColor(body))
        p.fillRect(QRect(fr.x(), fr.y() + STRIP - 2, fr.width(), 2), QColor(strip))
        p.setPen(QPen(QColor(0, 0, 0, 30), 1))
        p.setBrush(Qt.NoBrush)
        p.drawRoundedRect(QRectF(fr).adjusted(0.5, 0.5, -0.5, -0.5), 4, 4)
        dark = QColor(text).lightness() > 128
        glyph = QColor("#FFFFFF") if dark else QColor("#1A1A1A")
        f = QFont("Segoe UI")
        f.setPixelSize(18)
        p.setFont(f)
        for name, r in self._buttons().items():
            if name != "plus" and not self.hover:
                continue
            if self.hover_btn == name:
                p.setPen(Qt.NoPen)
                p.setBrush(QColor(0, 0, 0, 20) if not dark else QColor(255, 255, 255, 40))
                p.drawRoundedRect(QRectF(r), 4, 4)
            p.setPen(glyph)
            p.drawText(r, Qt.AlignCenter, {"plus": "+", "menu": "…", "close": "×"}[name])
        # the formatting bar
        f.setPixelSize(13)
        p.setFont(f)
        cf = self.edit.currentCharFormat()
        for name, r in self._format_buttons().items():
            on = {"bold": cf.fontWeight() > QFont.Normal, "italic": cf.fontItalic(), "underline": cf.fontUnderline(),
                  "strike": cf.fontStrikeOut(), "bullets": self.edit.textCursor().currentList() is not None}[name]
            if on or self.hover_btn == name:
                p.setPen(Qt.NoPen)
                p.setBrush(QColor(0, 0, 0, 36 if on else 20) if not dark else QColor(255, 255, 255, 60 if on else 40))
                p.drawRoundedRect(QRectF(r), 4, 4)
            p.setPen(glyph)
            label = {"bold": "B", "italic": "I", "underline": "U", "strike": "S", "bullets": "•≡"}[name]
            lf = QFont("Segoe UI")
            lf.setPixelSize(13)
            lf.setBold(name == "bold")
            lf.setItalic(name == "italic")
            lf.setUnderline(name == "underline")
            lf.setStrikeOut(name == "strike")
            p.setFont(lf)
            p.drawText(r, Qt.AlignCenter, label)
        p.setPen(QPen(QColor(0, 0, 0, 50) if not dark else QColor(255, 255, 255, 90), 1))
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
        x, y = (near.x() + near.width() + 4, near.y() + SHADOW) if near is not None else (60, 60)
        area = self.desktop.work_area()
        if x + MIN_W > area.width():
            x, y = near.x() + SHADOW, near.y() + near.height() + 4
        d = {"id": uuid.uuid4().hex[:8], "text": "", "color": near.data.get("color", "Yellow") if near else "Yellow",
             "x": x, "y": min(y, area.height() - MIN_H), "w": 220, "h": 220}
        n = Note(self, d)
        self.notes.append(n)
        n.show()
        n.raise_()
        n.edit.setFocus()
        self.save()
        return n

    def close_note(self, note):
        """x on a note: an empty note is deleted, one with text is just closed (hidden) until the next sign-in."""
        if not note.data.get("text", "").strip():
            self.delete(note)
            return
        note.hide()
        self.save()

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
