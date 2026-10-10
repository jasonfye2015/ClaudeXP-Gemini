"""Paint, like Windows XP's mspaint: the 16-tool box with its options, the 28-colour palette (left click =
foreground, right click = background, double click = Edit Colors), 3 levels of Undo, selections you can move,
cut, copy and paste, text, curves and polygons, zoom with a grid, Image > Flip/Rotate, Stretch, Invert Colors,
Attributes, and File > Set As Background. Saves .bmp (the default), .png, .jpg and .gif to My Pictures."""
import math
import random
from array import array
from pathlib import Path

from PySide6.QtCore import QPoint, QPointF, QRect, QRectF, QSize, Qt, QTimer, Signal
from PySide6.QtGui import (QAction, QActionGroup, QBrush, QColor, QFont, QIcon, QImage, QKeySequence, QPainter,
                           QPainterPath, QPen, QPixmap, QPolygon, QPolygonF, QTextDocument, QTextOption)
from PySide6.QtWidgets import (QApplication, QButtonGroup, QCheckBox, QColorDialog, QComboBox, QFontComboBox,
                               QGridLayout, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QMenuBar,
                               QPlainTextEdit, QPushButton, QRadioButton, QScrollArea, QSpinBox, QStyle,
                               QToolButton, QVBoxLayout, QWidget)

from .. import sound
from ..wm import XPWindow
from .notepad import MENU_STYLE

STYLE = MENU_STYLE + """
QWidget#paint { background: #ECE9D8; }
QLabel#status { border-top: 1px solid #ACA899; padding: 2px 6px; font-family: Tahoma; font-size: 11px; }
QLabel#statuscell { border: 1px solid #ACA899; padding: 1px 6px; font-family: Tahoma; font-size: 11px; }
QScrollArea { background: #808080; border: 1px solid #7F9DB9; }
"""
PALETTE = ["#000000", "#808080", "#800000", "#808000", "#008000", "#008080", "#000080", "#800080", "#808040",
           "#004040", "#0080FF", "#004080", "#8000FF", "#804000",
           "#FFFFFF", "#C0C0C0", "#FF0000", "#FFFF00", "#00FF00", "#00FFFF", "#0000FF", "#FF00FF", "#FFFF80",
           "#00FF80", "#80FFFF", "#8080FF", "#FF0080", "#FF8040"]
TOOLS = [("freeform", "Free-Form Select"), ("select", "Select"), ("eraser", "Eraser/Color Eraser"),
         ("fill", "Fill With Color"), ("pick", "Pick Color"), ("magnifier", "Magnifier"), ("pencil", "Pencil"),
         ("brush", "Brush"), ("airbrush", "Airbrush"), ("text", "Text"), ("line", "Line"), ("curve", "Curve"),
         ("rect", "Rectangle"), ("polygon", "Polygon"), ("ellipse", "Ellipse"), ("rrect", "Rounded Rectangle")]
HINTS = {"freeform": "Selects a free-form part of the picture to move, copy, or edit.",
         "select": "Selects a rectangular part of the picture to move, copy, or edit.",
         "eraser": "Erases a portion of the picture, using the selected eraser shape.",
         "fill": "Fills an area with the current drawing color.",
         "pick": "Picks up a color from the picture for drawing.",
         "magnifier": "Changes the magnification.", "pencil": "Draws a free-form line one pixel wide.",
         "brush": "Draws using a brush with the selected shape and size.",
         "airbrush": "Draws using an airbrush of the selected size.", "text": "Inserts text into the picture.",
         "line": "Draws a straight line with the selected line width.",
         "curve": "Draws a curved line with the selected line width.",
         "rect": "Draws a rectangle with the selected fill style.",
         "polygon": "Draws a polygon with the selected fill style.",
         "ellipse": "Draws an ellipse with the selected fill style.",
         "rrect": "Draws a rounded rectangle with the selected fill style."}
DEFAULT_HINT = "For Help, click Help Topics on the Help Menu."
UNDO_LEVELS = 3          # XP Paint remembered three
HANDLE = 3


# ---- tool icons ------------------------------------------------------------------------------------------------

def tool_icon(name):
    pm = QPixmap(16, 16)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing, name in ("ellipse", "magnifier", "curve", "airbrush", "rrect"))
    black = QPen(QColor("black"), 1)
    p.setPen(black)
    if name == "freeform":
        p.setPen(QPen(QColor("black"), 1, Qt.DashLine))
        p.drawPolygon(QPolygon([QPoint(3, 2), QPoint(13, 4), QPoint(11, 13), QPoint(5, 10), QPoint(2, 12)]))
    elif name == "select":
        p.setPen(QPen(QColor("black"), 1, Qt.DashLine))
        p.drawRect(2, 3, 11, 9)
    elif name == "eraser":
        p.setBrush(QColor("#F0E68C"))
        p.drawPolygon(QPolygon([QPoint(2, 10), QPoint(8, 4), QPoint(13, 7), QPoint(7, 13)]))
        p.setBrush(QColor("white"))
        p.drawPolygon(QPolygon([QPoint(2, 10), QPoint(5, 7), QPoint(10, 10), QPoint(7, 13)]))
    elif name == "fill":
        p.setBrush(QColor("#C0C0C0"))
        p.drawPolygon(QPolygon([QPoint(3, 7), QPoint(8, 2), QPoint(13, 7), QPoint(8, 12)]))
        p.setBrush(QColor("#0000FF"))
        p.setPen(Qt.NoPen)
        p.drawRect(11, 9, 3, 5)
    elif name == "pick":
        p.setBrush(QColor("#C0C0C0"))
        p.drawPolygon(QPolygon([QPoint(2, 14), QPoint(9, 7), QPoint(10, 8), QPoint(3, 15)]))
        p.setBrush(QColor("black"))
        p.drawEllipse(9, 2, 5, 5)
    elif name == "magnifier":
        p.setPen(QPen(QColor("black"), 1.5))
        p.setBrush(QColor(200, 230, 255))
        p.drawEllipse(QRectF(2, 2, 8, 8))
        p.setPen(QPen(QColor("#804000"), 2.5))
        p.drawLine(9, 9, 14, 14)
    elif name == "pencil":
        p.setBrush(QColor("#FFD700"))
        p.drawPolygon(QPolygon([QPoint(3, 13), QPoint(4, 10), QPoint(12, 2), QPoint(14, 4), QPoint(6, 12)]))
        p.drawLine(3, 13, 5, 11)
    elif name == "brush":
        p.setBrush(QColor("#804000"))
        p.drawPolygon(QPolygon([QPoint(9, 7), QPoint(13, 2), QPoint(14, 3), QPoint(10, 8)]))
        p.setBrush(QColor("#2050C0"))
        p.drawEllipse(3, 8, 7, 6)
    elif name == "airbrush":
        p.setBrush(QColor("#A0A0A0"))
        p.drawRect(8, 6, 5, 8)
        p.drawRect(9, 3, 2, 3)
        p.setPen(QColor("#2050C0"))
        for x, y in ((2, 3), (4, 5), (3, 7), (5, 2), (2, 9), (6, 4)):
            p.drawPoint(x, y)
    elif name == "text":
        f = QFont("Times New Roman")
        f.setPixelSize(15)
        f.setBold(True)
        p.setFont(f)
        p.drawText(QRect(0, 0, 16, 16), Qt.AlignCenter, "A")
    elif name == "line":
        p.drawLine(2, 13, 13, 2)
    elif name == "curve":
        path = QPainterPath(QPointF(2, 13))
        path.cubicTo(QPointF(2, 2), QPointF(13, 14), QPointF(13, 3))
        p.drawPath(path)
    elif name == "rect":
        p.drawRect(2, 4, 11, 8)
    elif name == "polygon":
        p.drawPolygon(QPolygon([QPoint(2, 13), QPoint(4, 3), QPoint(9, 7), QPoint(13, 2), QPoint(13, 13)]))
    elif name == "ellipse":
        p.drawEllipse(QRectF(2, 4, 12, 8))
    elif name == "rrect":
        p.drawRoundedRect(QRectF(2, 4, 12, 8), 3, 3)
    p.end()
    return QIcon(pm)


def paint_icon():
    pm = QPixmap(32, 32)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(QPen(QColor("#6A4A20"), 1))
    p.setBrush(QColor("#E8C890"))
    p.drawEllipse(QRectF(3, 7, 24, 18))
    p.setBrush(QColor("#ECE9D8"))
    p.drawEllipse(QRectF(9, 17, 5, 4))
    for color, (x, y) in zip(("#E02020", "#20A020", "#2040E0", "#F0D020"), ((8, 10), (14, 9), (20, 11), (21, 17))):
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(color))
        p.drawEllipse(QRectF(x, y, 4.5, 4))
    p.setPen(QPen(QColor("#804000"), 2.5))
    p.drawLine(18, 26, 29, 4)
    p.setPen(QPen(QColor("#303030"), 3))
    p.drawLine(16, 30, 18, 26)
    p.end()
    return QIcon(pm)


# ---- image helpers ----------------------------------------------------------------------------------------------

def flood_fill(img, x, y, color):
    """Scanline flood fill straight on the image's pixels."""
    w, h = img.width(), img.height()
    if not (0 <= x < w and 0 <= y < h):
        return False
    stride = img.bytesPerLine() // 4
    px = img.bits().cast("I")
    target, new = px[y * stride + x], QColor(color).rgb() & 0xFFFFFFFF
    if target == new:
        return False
    stack = [(x, y)]
    while stack:
        x, y = stack.pop()
        row = y * stride
        if px[row + x] != target:
            continue
        lx = x
        while lx > 0 and px[row + lx - 1] == target:
            lx -= 1
        rx = x
        while rx < w - 1 and px[row + rx + 1] == target:
            rx += 1
        px[row + lx: row + rx + 1] = array("I", [new]) * (rx - lx + 1)
        for ny in (y - 1, y + 1):
            if 0 <= ny < h:
                nrow = ny * stride
                i = lx
                while i <= rx:
                    if px[nrow + i] == target:
                        stack.append((i, ny))
                        while i <= rx and px[nrow + i] == target:
                            i += 1
                    i += 1
    return True


def line_points(a, b):
    """Every pixel from a to b (for stamping brushes and erasers)."""
    x0, y0, x1, y1 = a.x(), a.y(), b.x(), b.y()
    n = max(abs(x1 - x0), abs(y1 - y0), 1)
    return [QPoint(round(x0 + (x1 - x0) * i / n), round(y0 + (y1 - y0) * i / n)) for i in range(n + 1)]


def constrain(a, b):
    """Shift held: lines snap to 45 degrees, shapes become squares and circles."""
    dx, dy = b.x() - a.x(), b.y() - a.y()
    ang = round(math.atan2(dy, dx) / (math.pi / 4)) * (math.pi / 4)
    length = math.hypot(dx, dy)
    return QPoint(a.x() + round(math.cos(ang) * length), a.y() + round(math.sin(ang) * length))


def square(a, b):
    dx, dy = b.x() - a.x(), b.y() - a.y()
    s = max(abs(dx), abs(dy))
    return QPoint(a.x() + (s if dx >= 0 else -s), a.y() + (s if dy >= 0 else -s))


# ---- the drawing surface ---------------------------------------------------------------------------------------------

class Canvas(QWidget):
    moved = Signal(QPoint)
    sized = Signal(QSize)

    def __init__(self, paint):
        super().__init__()
        self.paint = paint
        self.image = QImage(480, 360, QImage.Format_RGB32)
        self.image.fill(QColor("white"))
        self.zoom = 1
        self.grid = False
        self.undo_stack, self.redo_stack = [], []
        self.drag = None              # what the mouse is doing
        self.points = []              # polygon / curve points
        self.points_button = Qt.LeftButton
        self.curve_stage = 0
        self.sel = None               # {"rect", "float": QImage, "mask": QImage|None, "pos"}
        self.text_box = None
        self.resizing = None
        self.spray = QTimer(self)
        self.spray.timeout.connect(self._spray)
        self.setMouseTracking(True)
        self.setCursor(Qt.CrossCursor)
        self._fit()

    # ---- geometry ------------------------------------------------------------------------------------------
    def _fit(self):
        self.setFixedSize(self.image.width() * self.zoom + 6, self.image.height() * self.zoom + 6)
        self.update()

    def to_image(self, pos):
        return QPoint(int(pos.x() // self.zoom), int(pos.y() // self.zoom))

    def handles(self):
        w, h = self.image.width() * self.zoom, self.image.height() * self.zoom
        return {"right": QRect(w, h // 2 - 1, HANDLE, HANDLE), "bottom": QRect(w // 2 - 1, h, HANDLE, HANDLE),
                "corner": QRect(w, h, HANDLE, HANDLE)}

    def set_zoom(self, zoom):
        self.commit_text()
        self.zoom = zoom
        self._fit()

    # ---- undo ---------------------------------------------------------------------------------------------------------
    def checkpoint(self):
        self.undo_stack.append(self.image.copy())
        del self.undo_stack[:-UNDO_LEVELS]
        self.redo_stack.clear()
        self.paint.modified = True

    def undo(self):
        if self.text_box is not None:
            return self.cancel_text()
        self.sel = None              # a lifted or pasted selection goes back with the picture
        if not self.undo_stack:
            return
        self.redo_stack.append(self.image)
        self.image = self.undo_stack.pop()
        self.sel = None
        self._fit()

    def redo(self):
        if not self.redo_stack:
            return
        self.undo_stack.append(self.image)
        self.image = self.redo_stack.pop()
        self.sel = None
        self._fit()

    def set_image(self, img, checkpoint=True):
        if checkpoint:
            self.checkpoint()
        self.image = img.convertToFormat(QImage.Format_RGB32)
        self.sel = None
        self._fit()
        self.sized.emit(self.image.size())

    # ---- colours --------------------------------------------------------------------------------------------------
    def colors(self, button):
        fg, bg = self.paint.fg, self.paint.bg
        return (fg, bg) if button == Qt.LeftButton else (bg, fg)

    def pen(self, color, width=1):
        pen = QPen(color, width)
        pen.setCapStyle(Qt.RoundCap if width > 1 else Qt.SquareCap)
        pen.setJoinStyle(Qt.RoundJoin)
        return pen

    # ---- shapes (drawn the same way for the preview and the real thing) -------------------------------------------------
    def draw_shape(self, p, tool, a, b, button):
        line, fill = self.colors(button)
        width = self.paint.line_width
        if tool == "line":
            p.setPen(self.pen(line, width))
            p.drawLine(a, b)
            return
        mode = self.paint.fill_mode
        r = QRect(a, b).normalized()
        outline_w = width if tool != "polygon" else width
        p.setPen(self.pen(line, outline_w) if mode in (0, 1) else Qt.NoPen)
        p.setBrush(Qt.NoBrush if mode == 0 else QBrush(fill if mode == 1 else line))
        if mode == 2:
            r = r.adjusted(0, 0, 1, 1)
        if tool == "rect":
            p.drawRect(r)
        elif tool == "ellipse":
            p.drawEllipse(r)
        elif tool == "rrect":
            p.drawRoundedRect(QRectF(r), 8, 8)

    def draw_curve(self, p, pts, button):
        line, _ = self.colors(button)
        p.setPen(self.pen(line, self.paint.line_width))
        p.setBrush(Qt.NoBrush)
        if len(pts) == 2:
            p.drawLine(pts[0], pts[1])
            return
        c1 = pts[2]
        c2 = pts[3] if len(pts) > 3 else pts[2]
        path = QPainterPath(QPointF(pts[0]))
        path.cubicTo(QPointF(c1), QPointF(c2), QPointF(pts[1]))
        p.drawPath(path)

    def draw_polygon(self, p, pts, button, closed):
        line, fill = self.colors(button)
        mode = self.paint.fill_mode
        if not closed:
            p.setPen(self.pen(line, self.paint.line_width))
            p.drawPolyline(QPolygon(pts))
            return
        p.setPen(self.pen(line, self.paint.line_width) if mode in (0, 1) else Qt.NoPen)
        p.setBrush(Qt.NoBrush if mode == 0 else QBrush(fill if mode == 1 else line))
        p.drawPolygon(QPolygon(pts))

    def image_painter(self):
        p = QPainter(self.image)
        p.setRenderHint(QPainter.Antialiasing, False)
        return p

    # ---- brushes, erasers, airbrush -----------------------------------------------------------------------------------
    def stamp(self, p, pt, color):
        shape, size = self.paint.brush
        p.setPen(Qt.NoPen)
        p.setBrush(color)
        if shape == "round":
            if size == 1:
                p.fillRect(pt.x(), pt.y(), 1, 1, color)
            else:
                p.drawEllipse(QPointF(pt) + QPointF(0.5, 0.5), size / 2, size / 2)
        elif shape == "square":
            p.fillRect(pt.x() - size // 2, pt.y() - size // 2, size, size, color)
        else:
            p.setPen(QPen(color, 1))
            d = size // 2
            if shape == "slash":
                p.drawLine(pt.x() - d, pt.y() + d, pt.x() + d, pt.y() - d)
            else:
                p.drawLine(pt.x() - d, pt.y() - d, pt.x() + d, pt.y() + d)

    def erase(self, pt, button):
        s = self.paint.eraser
        r = QRect(pt.x() - s // 2, pt.y() - s // 2, s, s).intersected(self.image.rect())
        if r.isEmpty():
            return
        if button == Qt.LeftButton:
            p = self.image_painter()
            p.fillRect(r, self.paint.bg)
            p.end()
        else:
            # Color eraser: only the foreground colour turns into the background colour
            fg, bg = self.paint.fg.rgb(), self.paint.bg.rgb()
            for y in range(r.top(), r.bottom() + 1):
                for x in range(r.left(), r.right() + 1):
                    if self.image.pixel(x, y) == fg:
                        self.image.setPixel(x, y, bg)

    def _spray(self):
        if not self.drag or self.drag.get("tool") != "airbrush":
            return
        color, _ = self.colors(self.drag["button"])
        radius = self.paint.airbrush
        p = self.image_painter()
        p.setPen(QPen(color, 1))
        c = self.drag["pos"]
        for _ in range(radius * 2):
            ang, dist = random.uniform(0, math.tau), radius * math.sqrt(random.random())
            p.drawPoint(round(c.x() + math.cos(ang) * dist), round(c.y() + math.sin(ang) * dist))
        p.end()
        self.update()

    # ---- selection --------------------------------------------------------------------------------------------------------
    def lift(self):
        """Pick the selected pixels up off the picture (leaving the background colour behind)."""
        s = self.sel
        if s is None or s.get("float") is not None:
            return
        self.checkpoint()
        r = s["rect"].intersected(self.image.rect())
        if r.isEmpty():
            self.sel = None
            return
        piece = self.image.copy(r)
        mask = s.get("mask")
        p = self.image_painter()
        if mask is None:
            p.fillRect(r, self.paint.bg)
        else:
            p.setClipPath(s["path"])
            p.fillRect(r, self.paint.bg)
        p.end()
        s.update(rect=r, float=piece, pos=r.topLeft(), lifted_from=r.topLeft())

    def float_image(self):
        """The floating piece as it'll be stamped (transparent mode drops the background colour)."""
        s = self.sel
        piece = s["float"].convertToFormat(QImage.Format_ARGB32)
        if s.get("mask") is not None:
            p = QPainter(piece)
            p.setCompositionMode(QPainter.CompositionMode_DestinationIn)
            p.drawImage(0, 0, s["mask"])
            p.end()
        if self.paint.transparent:
            bg = self.paint.bg.rgb()
            px = piece.bits().cast("I")
            for i in range(piece.width() * piece.height()):
                if (px[i] | 0xFF000000) == bg and px[i] >> 24:
                    px[i] = 0
        return piece

    def commit_selection(self):
        s, self.sel = self.sel, None
        if s is not None and s.get("float") is not None:
            p = self.image_painter()
            p.drawImage(s["pos"], self._float_cache(s))
            p.end()
        self.update()

    def _float_cache(self, s):
        key = (self.paint.transparent, self.paint.bg.rgb())
        if s.get("cache_key") != key:
            s["cache"], s["cache_key"] = self.float_image(), key
        return s["cache"]

    def selection_rect(self):
        s = self.sel
        if s is None:
            return None
        if s.get("float") is not None:
            return QRect(s["pos"], s["float"].size())
        return s["rect"]

    def select_all(self):
        self.commit_selection()
        self.paint.set_tool("select")
        self.sel = {"rect": self.image.rect(), "float": None, "mask": None}
        self.update()

    def delete_selection(self):
        if self.sel is None:
            return
        if self.sel.get("float") is None:
            self.lift()
        self.sel = None
        self.update()

    def copy_selection(self):
        if self.sel is None:
            return False
        if self.sel.get("float") is not None:
            img = self.float_image()
        else:
            img = self.image.copy(self.sel["rect"].intersected(self.image.rect()))
        QApplication.clipboard().setImage(img)
        return True

    def cut_selection(self):
        if self.copy_selection():
            self.delete_selection()

    def paste(self, img=None):
        img = img if img is not None else QApplication.clipboard().image()
        if img.isNull():
            return
        self.commit_selection()
        self.commit_text()
        if img.width() > self.image.width() or img.height() > self.image.height():
            bigger = QImage(max(img.width(), self.image.width()), max(img.height(), self.image.height()),
                            QImage.Format_RGB32)
            bigger.fill(self.paint.bg)
            QPainter(bigger).drawImage(0, 0, self.image)
            self.set_image(bigger)
        else:
            self.checkpoint()
        self.paint.set_tool("select")
        self.sel = {"rect": QRect(QPoint(0, 0), img.size()), "float": img.convertToFormat(QImage.Format_RGB32),
                    "mask": None, "pos": QPoint(0, 0)}
        self.update()

    # ---- text -------------------------------------------------------------------------------------------------------------
    def start_text(self, rect):
        self.commit_text()
        edit = QPlainTextEdit(self)
        edit.setProperty("nospell", True)
        edit.setFrameStyle(0)
        edit.setFont(self.paint.text_font())
        edit.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        edit.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        bg = "transparent" if self.paint.transparent else self.paint.bg.name()
        edit.setStyleSheet(f"QPlainTextEdit {{ background: {bg}; color: {self.paint.fg.name()}; "
                           f"border: 1px dashed #000080; }}")
        edit.setGeometry(QRect(rect.topLeft() * self.zoom, rect.size() * self.zoom))
        edit.document().setDocumentMargin(1)
        edit.show()
        edit.setFocus()
        self.text_box = {"edit": edit, "rect": rect}
        self.paint.show_fonts(True)

    def restyle_text(self):
        if self.text_box is not None:
            e = self.text_box["edit"]
            font = self.paint.text_font()
            if self.zoom != 1:
                font.setPixelSize(font.pixelSize() * self.zoom)
            e.setFont(font)
            bg = "transparent" if self.paint.transparent else self.paint.bg.name()
            e.setStyleSheet(f"QPlainTextEdit {{ background: {bg}; color: {self.paint.fg.name()}; "
                            f"border: 1px dashed #000080; }}")

    def commit_text(self):
        tb, self.text_box = self.text_box, None
        if tb is None:
            return
        text = tb["edit"].toPlainText()
        tb["edit"].deleteLater()
        self.paint.show_fonts(False)
        if not text.strip():
            return
        self.checkpoint()
        r = tb["rect"]
        p = self.image_painter()
        p.setRenderHint(QPainter.TextAntialiasing, False)
        if not self.paint.transparent:
            p.fillRect(r, self.paint.bg)
        p.setPen(self.paint.fg)
        p.setFont(self.paint.text_font())
        p.drawText(r.adjusted(2, 1, -1, -1), Qt.TextWordWrap | Qt.AlignLeft | Qt.AlignTop, text)
        p.end()
        self.update()

    def cancel_text(self):
        tb, self.text_box = self.text_box, None
        if tb is not None:
            tb["edit"].deleteLater()
            self.paint.show_fonts(False)

    # ---- mouse ------------------------------------------------------------------------------------------------------------
    def mousePressEvent(self, event):
        pos = event.position().toPoint()
        button = event.button()
        if button not in (Qt.LeftButton, Qt.RightButton):
            return
        for edge, r in self.handles().items():
            if r.adjusted(-2, -2, 2, 2).contains(pos) and button == Qt.LeftButton:
                self.commit_selection()
                self.commit_text()
                self.resizing = {"edge": edge, "size": QSize(self.image.size())}
                return
        pt = self.to_image(pos)
        tool = self.paint.tool
        shift = bool(event.modifiers() & Qt.ShiftModifier)
        if tool != "text":
            self.commit_text()
        if tool in ("select", "freeform"):
            r = self.selection_rect()
            if r is not None and r.contains(pt):
                self.lift()
                if self.sel is None:
                    return
                if event.modifiers() & Qt.ControlModifier:
                    # Ctrl-drag leaves a copy behind
                    p = self.image_painter()
                    p.drawImage(self.sel["pos"], self._float_cache(self.sel))
                    p.end()
                self.drag = {"tool": "move", "start": pt, "origin": QPoint(self.sel["pos"]), "button": button}
                return
            self.commit_selection()
            self.drag = {"tool": tool, "start": pt, "pos": pt, "button": button, "path": [pt]}
            return
        self.commit_selection()
        if tool == "polygon" and self.points:
            self.points.append(pt)
            self.drag = {"tool": "polygon", "start": pt, "pos": pt, "button": self.points_button}
            self.update()
            return
        if tool == "curve" and self.curve_stage in (1, 2):
            self.points = self.points[:2 + self.curve_stage - 1] + [pt]
            self.drag = {"tool": "curve", "start": pt, "pos": pt, "button": self.points_button}
            self.update()
            return
        self.drag = {"tool": tool, "start": pt, "pos": pt, "button": button, "last": pt, "shift": shift}
        if tool in ("pencil", "brush", "eraser", "airbrush"):
            self.checkpoint()
            self._paint_stroke(pt, pt, button)
            if tool == "airbrush":
                self._spray()
                self.spray.start(25)
        elif tool == "fill":
            self.drag = None
            if self.image.rect().contains(pt):
                self.checkpoint()
                flood_fill(self.image, pt.x(), pt.y(), self.colors(button)[0])
                self.update()
        elif tool == "pick":
            self.drag = None
            if self.image.rect().contains(pt):
                self.paint.set_color(QColor(self.image.pixel(pt)), button == Qt.LeftButton)
                self.paint.set_tool(self.paint.previous_tool)
        elif tool == "magnifier":
            self.drag = None
            self.paint.magnify(pt)
        elif tool == "polygon":
            self.points = [pt, pt]
            self.points_button = button
        elif tool == "curve":
            self.points = [pt, pt]
            self.points_button = button
            self.curve_stage = 0
        self.update()

    def _paint_stroke(self, a, b, button):
        tool = self.paint.tool
        color, _ = self.colors(button)
        if tool == "pencil":
            p = self.image_painter()
            p.setPen(QPen(color, 1))
            if a == b:
                p.drawPoint(a)
            else:
                p.drawLine(a, b)
            p.end()
        elif tool == "brush":
            p = self.image_painter()
            for pt in line_points(a, b):
                self.stamp(p, pt, color)
            p.end()
        elif tool == "eraser":
            for pt in line_points(a, b):
                self.erase(pt, button)
        self.update()

    def mouseMoveEvent(self, event):
        pos = event.position().toPoint()
        pt = self.to_image(pos)
        self.moved.emit(pt)
        if self.resizing:
            w = max(1, pos.x() // self.zoom) if self.resizing["edge"] in ("right", "corner") else self.image.width()
            h = max(1, pos.y() // self.zoom) if self.resizing["edge"] in ("bottom", "corner") else self.image.height()
            self.resizing["size"] = QSize(w, h)
            self.update()
            return
        cursor = Qt.CrossCursor
        for edge, r in self.handles().items():
            if r.adjusted(-2, -2, 2, 2).contains(pos):
                cursor = {"right": Qt.SizeHorCursor, "bottom": Qt.SizeVerCursor, "corner": Qt.SizeFDiagCursor}[edge]
        r = self.selection_rect()
        if r is not None and r.contains(pt) and self.paint.tool in ("select", "freeform"):
            cursor = Qt.SizeAllCursor
        self.setCursor(cursor)
        d = self.drag
        if d is None:
            return
        if d["tool"] == "move":
            self.sel["pos"] = d["origin"] + (pt - d["start"])
        elif d["tool"] in ("pencil", "brush", "eraser"):
            self._paint_stroke(d["last"], pt, d["button"])
            d["last"] = pt
        elif d["tool"] == "freeform":
            d["path"].append(pt)
        elif d["tool"] == "polygon" or d["tool"] == "curve":
            if event.modifiers() & Qt.ShiftModifier and d["tool"] == "polygon":
                pt = constrain(self.points[-2], pt)
            self.points[-1] = pt
        if d["tool"] in ("line",) and event.modifiers() & Qt.ShiftModifier:
            pt = constrain(d["start"], pt)
        elif d["tool"] in ("rect", "ellipse", "rrect") and event.modifiers() & Qt.ShiftModifier:
            pt = square(d["start"], pt)
        d["pos"] = pt
        if d["tool"] in ("line", "rect", "ellipse", "rrect", "select", "text"):
            size = QRect(d["start"], pt).normalized().size()
            self.paint.show_size(size)
        self.update()

    def mouseReleaseEvent(self, event):
        if self.resizing:
            size, self.resizing = self.resizing["size"], None
            self.paint.resize_image(size)
            return
        d, self.drag = self.drag, None
        self.spray.stop()
        self.paint.show_size(None)
        if d is None:
            return
        tool, a, b, button = d["tool"], d["start"], d["pos"], d["button"]
        if tool in ("line", "rect", "ellipse", "rrect"):
            if a == b and tool != "line":
                self.update()
                return
            self.checkpoint()
            p = self.image_painter()
            self.draw_shape(p, tool, a, b, button)
            p.end()
        elif tool == "select":
            r = QRect(a, b).normalized().intersected(self.image.rect())
            if r.width() > 1 and r.height() > 1:
                self.sel = {"rect": r, "float": None, "mask": None}
        elif tool == "freeform":
            pts = d["path"]
            if len(pts) > 2:
                path = QPainterPath()
                path.addPolygon(QPolygonF([QPointF(p) for p in pts]))
                path.closeSubpath()
                r = path.boundingRect().toAlignedRect().intersected(self.image.rect())
                if r.width() > 1 and r.height() > 1:
                    mask = QImage(r.size(), QImage.Format_ARGB32)
                    mask.fill(Qt.transparent)
                    mp = QPainter(mask)
                    mp.translate(-r.topLeft())
                    mp.fillPath(path, QColor("black"))
                    mp.end()
                    self.sel = {"rect": r, "float": None, "mask": mask, "path": path}
        elif tool == "text":
            r = QRect(a, b).normalized()
            if r.width() < 20 or r.height() < 12:
                r = QRect(a, QSize(160, 40))
            self.start_text(r.intersected(self.image.rect()))
        elif tool == "curve":
            if self.curve_stage < 2:
                self.curve_stage += 1
                if self.curve_stage == 1 and self.points[0] == self.points[1]:
                    self.points, self.curve_stage = [], 0
            else:
                self.checkpoint()
                p = self.image_painter()
                self.draw_curve(p, self.points, button)
                p.end()
                self.points, self.curve_stage = [], 0
        elif tool == "polygon":
            if len(self.points) > 2 and (self.points[-1] - self.points[0]).manhattanLength() <= 3:
                self.finish_polygon()
        self.update()

    def mouseDoubleClickEvent(self, event):
        if self.paint.tool == "polygon" and len(self.points) > 2:
            self.finish_polygon()
        else:
            self.mousePressEvent(event)

    def finish_polygon(self):
        self.checkpoint()
        p = self.image_painter()
        self.draw_polygon(p, self.points, self.points_button, True)
        p.end()
        self.points = []
        self.drag = None
        self.update()

    def cancel_shape(self):
        self.points, self.curve_stage, self.drag = [], 0, None
        self.update()

    # ---- painting -----------------------------------------------------------------------------------------------------------
    def paintEvent(self, event):
        p = QPainter(self)
        z = self.zoom
        w, h = self.image.width() * z, self.image.height() * z
        display_image = getattr(self.paint, "display_image", None)
        image = display_image() if callable(display_image) else self.image
        p.drawImage(QRect(0, 0, w, h), image)
        p.save()
        p.scale(z, z)
        d = self.drag
        if d is not None and d["tool"] in ("line", "rect", "ellipse", "rrect"):
            p.setClipRect(self.image.rect())
            self.draw_shape(p, d["tool"], d["start"], d["pos"], d["button"])
        if self.points:
            p.setClipRect(self.image.rect())
            if self.paint.tool == "curve":
                self.draw_curve(p, self.points, self.points_button)
            else:
                self.draw_polygon(p, self.points, self.points_button, False)
        if self.sel is not None and self.sel.get("float") is not None:
            p.drawImage(self.sel["pos"], self._float_cache(self.sel))
        p.restore()
        # marquees
        marquee = QPen(QColor("#000080"), 1, Qt.DashLine)
        if d is not None and d["tool"] in ("select", "text"):
            p.setPen(marquee)
            p.setBrush(Qt.NoBrush)
            r = QRect(d["start"], d["pos"]).normalized()
            p.drawRect(QRect(r.topLeft() * z, r.size() * z))
        if d is not None and d["tool"] == "freeform" and len(d["path"]) > 1:
            p.setPen(QPen(QColor("black"), 1))
            p.drawPolyline(QPolygon([QPoint(q.x() * z, q.y() * z) for q in d["path"]]))
        r = self.selection_rect()
        if r is not None:
            p.setPen(marquee)
            p.setBrush(Qt.NoBrush)
            p.drawRect(QRect(r.topLeft() * z, r.size() * z).adjusted(0, 0, -1, -1))
        if self.grid and z >= 4:
            p.setPen(QPen(QColor(128, 128, 128, 140), 1))
            for x in range(0, w, z):
                p.drawLine(x, 0, x, h)
            for y in range(0, h, z):
                p.drawLine(0, y, w, y)
        # resize handles (and the outline while dragging one)
        p.setPen(QPen(QColor("#000080"), 1))
        p.setBrush(QColor("#000080"))
        for r in self.handles().values():
            p.drawRect(r.adjusted(0, 0, -1, -1))
        if self.resizing:
            s = self.resizing["size"]
            p.setPen(QPen(QColor("black"), 1, Qt.DotLine))
            p.setBrush(Qt.NoBrush)
            p.drawRect(0, 0, s.width() * z, s.height() * z)


# ---- the tool box, options, colour box --------------------------------------------------------------------------------------

class ToolOptions(QWidget):
    """The sunken box under the tools: brush shapes, line widths, fill styles, zoom levels..."""
    changed = Signal()

    def __init__(self, paint):
        super().__init__()
        self.paint = paint
        self.setFixedSize(44, 70)

    def items(self):
        t = self.paint.tool
        if t in ("select", "freeform", "text"):
            return [("opaque", r) for r in ([QRect(4, 6, 36, 26)])] + [("transparent", QRect(4, 36, 36, 26))]
        if t == "eraser":
            return [(s, QRect(4, 4 + i * 16, 36, 15)) for i, s in enumerate((4, 6, 8, 10))]
        if t == "magnifier":
            return [(z, QRect(4, 4 + i * 16, 36, 15)) for i, z in enumerate((1, 2, 6, 8))]
        if t == "brush":
            shapes = [("round", 7), ("round", 4), ("round", 1), ("square", 8), ("square", 5), ("square", 2),
                      ("slash", 8), ("slash", 5), ("slash", 2), ("back", 8), ("back", 5), ("back", 2)]
            return [(s, QRect(4 + (i % 3) * 12, 6 + (i // 3) * 15, 12, 14)) for i, s in enumerate(shapes)]
        if t == "airbrush":
            return [(r, QRect(4 + i * 12 if i < 2 else 10, 6 if i < 2 else 36, 18 if i == 2 else 16, 26)) for i, r in
                    enumerate((4, 8, 12))]
        if t in ("line", "curve"):
            return [(w, QRect(4, 4 + i * 12, 36, 11)) for i, w in enumerate((1, 2, 3, 4, 5))]
        if t in ("rect", "polygon", "ellipse", "rrect"):
            return [(m, QRect(4, 4 + i * 21, 36, 20)) for i, m in enumerate((0, 1, 2))]
        return []

    def current(self):
        t, pt = self.paint.tool, self.paint
        return {"eraser": pt.eraser, "magnifier": pt.canvas.zoom, "brush": pt.brush, "airbrush": pt.airbrush,
                "line": pt.line_width, "curve": pt.line_width, "rect": pt.fill_mode, "polygon": pt.fill_mode,
                "ellipse": pt.fill_mode, "rrect": pt.fill_mode,
                }.get(t, "transparent" if pt.transparent else "opaque")

    def mousePressEvent(self, event):
        for value, r in self.items():
            if r.contains(event.position().toPoint()):
                self.paint.set_option(value)
                self.update()
                return

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor("#ECE9D8"))
        p.setPen(QColor("#808080"))
        p.drawRect(self.rect().adjusted(0, 0, -1, -1))
        cur = self.current()
        fg = QColor("black")
        for value, r in self.items():
            selected = value == cur
            if selected:
                p.fillRect(r, QColor("#000080"))
            ink = QColor("white") if selected else fg
            t = self.paint.tool
            p.setPen(QPen(ink, 1))
            p.setBrush(Qt.NoBrush)
            c = r.center()
            if t in ("select", "freeform", "text"):
                p.fillRect(r.adjusted(6, 4, -6, -4), QColor("#C0C0C0") if value == "opaque" else Qt.transparent)
                p.setBrush(QColor("#FF8040"))
                p.drawEllipse(r.adjusted(10, 7, -10, -5))
                p.setBrush(QColor("#2060E0"))
                p.drawRect(r.adjusted(8, 4, -16, -12))
            elif t in ("eraser",):
                p.fillRect(QRect(0, 0, value, value).translated(c - QPoint(value // 2, value // 2)), ink)
            elif t == "magnifier":
                p.drawText(r, Qt.AlignCenter, f"{value}x")
            elif t == "brush":
                shape, size = value
                s = max(1, size // 2 + 1)
                if shape == "round":
                    p.setBrush(ink)
                    p.drawEllipse(c, s // 2 + (1 if size > 1 else 0), s // 2 + (1 if size > 1 else 0))
                elif shape == "square":
                    p.fillRect(QRect(c.x() - s // 2, c.y() - s // 2, s, s), ink)
                elif shape == "slash":
                    p.drawLine(c.x() - s // 2, c.y() + s // 2, c.x() + s // 2, c.y() - s // 2)
                else:
                    p.drawLine(c.x() - s // 2, c.y() - s // 2, c.x() + s // 2, c.y() + s // 2)
            elif t == "airbrush":
                rnd = random.Random(value)
                for _ in range(value * 3):
                    ang, dist = rnd.uniform(0, math.tau), value * 0.9 * math.sqrt(rnd.random())
                    p.drawPoint(round(c.x() + math.cos(ang) * dist), round(c.y() + math.sin(ang) * dist))
            elif t in ("line", "curve"):
                p.fillRect(QRect(r.x() + 4, c.y() - value // 2, r.width() - 8, value), ink)
            else:
                box = r.adjusted(7, 4, -7, -4)
                if value == 0:
                    p.drawRect(box)
                elif value == 1:
                    p.setBrush(QColor("#808080"))
                    p.drawRect(box)
                else:
                    p.fillRect(box.adjusted(0, 0, 1, 1), QColor("#808080") if not selected else QColor("#C0C0C0"))


class ColorBox(QWidget):
    def __init__(self, paint):
        super().__init__()
        self.paint = paint
        self.colors = [QColor(c) for c in PALETTE]
        self.setFixedHeight(40)

    def swatch(self, i):
        col, row = i % 14, i // 14
        return QRect(34 + col * 16, 4 + row * 16, 15, 15)

    def index_at(self, pos):
        for i in range(len(self.colors)):
            if self.swatch(i).contains(pos):
                return i
        return None

    def mousePressEvent(self, event):
        i = self.index_at(event.position().toPoint())
        if i is not None:
            self.paint.set_color(self.colors[i], event.button() == Qt.LeftButton)

    def mouseDoubleClickEvent(self, event):
        i = self.index_at(event.position().toPoint())
        if i is not None and event.button() == Qt.LeftButton:
            self.paint.edit_colors(i)

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor("#ECE9D8"))

        def sunken(r, color):
            p.fillRect(r, color)
            p.setPen(QColor("#808080"))
            p.drawLine(r.topLeft(), r.topRight())
            p.drawLine(r.topLeft(), r.bottomLeft())
            p.setPen(QColor("white"))
            p.drawLine(r.bottomLeft(), r.bottomRight())
            p.drawLine(r.topRight(), r.bottomRight())

        well = QRect(2, 4, 31, 31)
        sunken(well, QColor("#ECE9D8"))
        sunken(QRect(14, 16, 15, 15), self.paint.bg)
        sunken(QRect(6, 8, 15, 15), self.paint.fg)
        for i, c in enumerate(self.colors):
            sunken(self.swatch(i), c)


# ---- the window ------------------------------------------------------------------------------------------------------------------

class Paint(QWidget):
    def __init__(self, desktop, path=None, app_name="Paint", app_icon=None):
        super().__init__()
        self.desktop = desktop
        self.frame = None
        self.path = None
        self.app_name = app_name
        self.app_icon = app_icon or paint_icon()
        self.modified = False
        self.closing = False
        self.tool, self.previous_tool = "pencil", "pencil"
        self.fg, self.bg = QColor("black"), QColor("white")
        self.brush = ("round", 4)
        self.eraser = 8
        self.airbrush = 8
        self.line_width = 1
        self.fill_mode = 0
        self.transparent = False
        self.magnify_level = 4
        self.font_family, self.font_size = "Arial", 12
        self.font_bold = self.font_italic = self.font_underline = False
        self.setObjectName("paint")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(STYLE)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        self.menu = QMenuBar()
        self.menu.triggered.connect(lambda _a: sound.play("menu"))
        root.addWidget(self.menu)
        middle = QHBoxLayout()
        middle.setContentsMargins(2, 2, 2, 2)
        middle.setSpacing(3)
        # tool box
        box = QVBoxLayout()
        box.setSpacing(2)
        grid = QGridLayout()
        grid.setSpacing(0)
        self.tool_buttons = {}
        group = QButtonGroup(self)
        for i, (name, tip) in enumerate(TOOLS):
            b = QToolButton()
            b.setIcon(tool_icon(name))
            b.setCheckable(True)
            b.setFixedSize(25, 25)
            b.setToolTip(tip)
            b.setStyleSheet("QToolButton { border: 1px solid #ECE9D8; background: #ECE9D8; }"
                            "QToolButton:checked { border: 1px solid #808080; background: #FFFFFF; }"
                            "QToolButton:hover { border: 1px solid #ACA899; }")
            b.clicked.connect(lambda _c=False, n=name: self.set_tool(n))
            group.addButton(b)
            grid.addWidget(b, i // 2, i % 2)
            self.tool_buttons[name] = b
        box.addLayout(grid)
        self.options = ToolOptions(self)
        box.addWidget(self.options, alignment=Qt.AlignHCenter)
        box.addStretch()
        self.toolbox = QWidget()
        self.toolbox.setLayout(box)
        middle.addWidget(self.toolbox)
        # the picture
        right = QVBoxLayout()
        right.setSpacing(2)
        self.fonts = self._font_bar()
        right.addWidget(self.fonts)
        self.canvas = Canvas(self)
        self.scroll = QScrollArea()
        self.scroll.setWidget(self.canvas)
        self.scroll.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.scroll.setStyleSheet("QScrollArea { background: #808080; } QScrollArea > QWidget > QWidget { background: #808080; }")
        self.scroll.viewport().setStyleSheet("background: #808080;")
        right.addWidget(self.scroll, 1)
        middle.addLayout(right, 1)
        root.addLayout(middle, 1)
        self.colorbox = ColorBox(self)
        root.addWidget(self.colorbox)
        status = QHBoxLayout()
        status.setContentsMargins(0, 0, 0, 0)
        status.setSpacing(2)
        self.hint = QLabel(DEFAULT_HINT)
        self.hint.setObjectName("status")
        self.coords = QLabel("")
        self.coords.setObjectName("statuscell")
        self.coords.setFixedWidth(90)
        self.size_cell = QLabel("")
        self.size_cell.setObjectName("statuscell")
        self.size_cell.setFixedWidth(90)
        status.addWidget(self.hint, 1)
        status.addWidget(self.coords)
        status.addWidget(self.size_cell)
        self.status_bar = QWidget()
        self.status_bar.setLayout(status)
        root.addWidget(self.status_bar)
        self.canvas.moved.connect(lambda pt: self.coords.setText(f"{pt.x()},{pt.y()}" if self.canvas.image.rect().contains(pt) else ""))
        self._menus()
        self.set_tool("pencil")
        if path is not None:
            self.load(Path(path))

    # ---- menus ------------------------------------------------------------------------------------------------------
    def _menus(self):
        m = self.menu
        f = m.addMenu("&File")
        f.addAction("&New", lambda: self._maybe_save(self.new), QKeySequence("Ctrl+N"))
        f.addAction("&Open...", lambda: self._maybe_save(self.open_dialog), QKeySequence("Ctrl+O"))
        f.addAction("&Save", self.save, QKeySequence("Ctrl+S"))
        f.addAction("Save &As...", self.save_as)
        f.addSeparator()
        f.addAction("&Print...", self.print_, QKeySequence("Ctrl+P"))
        f.addSeparator()
        f.addAction("Set As &Background (Tiled)", lambda: self.set_background("Tile"))
        f.addAction("Set As Bac&kground (Centered)", lambda: self.set_background("Center"))
        f.addSeparator()
        f.addAction("E&xit", lambda: self.frame.request_close())
        e = m.addMenu("&Edit")
        e.addAction("&Undo", self.canvas.undo, QKeySequence("Ctrl+Z"))
        e.addAction("&Repeat", self.canvas.redo, QKeySequence("Ctrl+Y"))
        e.addSeparator()
        e.addAction("Cu&t", self.canvas.cut_selection, QKeySequence("Ctrl+X"))
        e.addAction("&Copy", self.canvas.copy_selection, QKeySequence("Ctrl+C"))
        e.addAction("&Paste", lambda: self.canvas.paste(), QKeySequence("Ctrl+V"))
        e.addAction("C&lear Selection", self.canvas.delete_selection, QKeySequence("Del"))
        e.addAction("Select &All", self.canvas.select_all, QKeySequence("Ctrl+A"))
        v = m.addMenu("&View")
        for label, widget, key in (("&Tool Box", self.toolbox, "Ctrl+T"), ("&Color Box", self.colorbox, "Ctrl+L"),
                                   ("&Status Bar", self.status_bar, None)):
            act = QAction(label, self, checkable=True, checked=True)
            if key:
                act.setShortcut(QKeySequence(key))
            act.toggled.connect(widget.setVisible)
            v.addAction(act)
        v.addSeparator()
        zoom = v.addMenu("&Zoom")
        zoom.addAction("&Normal Size", lambda: self.canvas.set_zoom(1), QKeySequence("Ctrl+PgUp"))
        zoom.addAction("&Large Size", lambda: self.canvas.set_zoom(4), QKeySequence("Ctrl+PgDown"))
        zoom.addAction("C&ustom...", self.custom_zoom)
        zoom.addSeparator()
        self.grid_act = QAction("Show &Grid", self, checkable=True)
        self.grid_act.setShortcut(QKeySequence("Ctrl+G"))
        self.grid_act.toggled.connect(lambda on: (setattr(self.canvas, "grid", on), self.canvas.update()))
        zoom.addAction(self.grid_act)
        i = m.addMenu("&Image")
        i.addAction("&Flip/Rotate...", self.flip_rotate, QKeySequence("Ctrl+R"))
        i.addAction("&Stretch/Skew...", self.stretch, QKeySequence("Ctrl+W"))
        i.addAction("&Invert Colors", self.invert, QKeySequence("Ctrl+I"))
        i.addAction("&Attributes...", self.attributes, QKeySequence("Ctrl+E"))
        i.addAction("&Clear Image", self.clear_image, QKeySequence("Ctrl+Shift+N"))
        self.draw_opaque = QAction("&Draw Opaque", self, checkable=True, checked=True)
        self.draw_opaque.toggled.connect(lambda on: self.set_option("opaque" if on else "transparent"))
        i.addAction(self.draw_opaque)
        c = m.addMenu("&Colors")
        c.addAction("&Edit Colors...", lambda: self.edit_colors(None))
        h = m.addMenu("&Help")
        h.addAction("&Help Topics", lambda: self._message(self.app_name, HELP_TEXT))
        h.addSeparator()
        h.addAction(f"&About {self.app_name}",
                    lambda: self._message(f"About {self.app_name}", f"{self.app_name}\nVersion 1.0"))

    def _font_bar(self):
        bar = QWidget()
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(4, 2, 4, 2)
        lay.addWidget(QLabel("Fonts:"))
        self.font_combo = QFontComboBox()
        self.font_combo.setCurrentFont(QFont(self.font_family))
        self.font_combo.currentFontChanged.connect(lambda f: self._font_changed(family=f.family()))
        lay.addWidget(self.font_combo)
        self.size_combo = QComboBox()
        self.size_combo.setEditable(True)
        self.size_combo.addItems([str(s) for s in (8, 9, 10, 11, 12, 14, 16, 18, 20, 22, 24, 26, 28, 36, 48, 72)])
        self.size_combo.setCurrentText(str(self.font_size))
        self.size_combo.currentTextChanged.connect(lambda t: t.isdigit() and self._font_changed(size=int(t)))
        lay.addWidget(self.size_combo)
        for label, attr in (("B", "font_bold"), ("I", "font_italic"), ("U", "font_underline")):
            b = QToolButton()
            b.setText(label)
            b.setCheckable(True)
            b.setFixedSize(22, 22)
            f = b.font()
            f.setBold(label == "B")
            f.setItalic(label == "I")
            f.setUnderline(label == "U")
            b.setFont(f)
            b.toggled.connect(lambda on, a=attr: self._font_changed(**{a: on}))
            lay.addWidget(b)
        lay.addStretch()
        bar.hide()
        return bar

    def _font_changed(self, **values):
        for k, v in values.items():
            setattr(self, "font_" + k if not k.startswith("font_") else k, v)
        self.canvas.restyle_text()

    def text_font(self):
        f = QFont(self.font_family)
        f.setPixelSize(max(6, round(self.font_size * 96 / 72)))
        f.setBold(self.font_bold)
        f.setItalic(self.font_italic)
        f.setUnderline(self.font_underline)
        f.setStyleStrategy(QFont.NoAntialias)
        return f

    def show_fonts(self, on):
        self.fonts.setVisible(on)

    # ---- tools and colours ----------------------------------------------------------------------------------------------
    def set_tool(self, name):
        if name != "text":
            self.canvas.commit_text()
        if name not in ("select", "freeform"):
            self.canvas.commit_selection()
        self.canvas.cancel_shape()
        if name != "pick":
            self.previous_tool = name
        self.tool = name
        self.tool_buttons[name].setChecked(True)
        self.hint.setText(HINTS.get(name, DEFAULT_HINT))
        self.options.update()

    def set_option(self, value):
        t = self.tool
        if t in ("select", "freeform", "text") or value in ("opaque", "transparent"):
            self.transparent = value == "transparent"
            self.draw_opaque.blockSignals(True)
            self.draw_opaque.setChecked(not self.transparent)
            self.draw_opaque.blockSignals(False)
            self.canvas.restyle_text()
        elif t == "eraser":
            self.eraser = value
        elif t == "magnifier":
            self.canvas.set_zoom(value)
        elif t == "brush":
            self.brush = value
        elif t == "airbrush":
            self.airbrush = value
        elif t in ("line", "curve"):
            self.line_width = value
        else:
            self.fill_mode = value
        self.options.update()
        self.canvas.update()

    def set_color(self, color, foreground=True):
        if foreground:
            self.fg = QColor(color)
        else:
            self.bg = QColor(color)
        self.colorbox.update()
        self.canvas.restyle_text()

    def magnify(self, pt):
        if self.canvas.zoom == 1:
            self.canvas.set_zoom(self.magnify_level)
            QTimer.singleShot(0, lambda: self.scroll.ensureVisible(pt.x() * self.canvas.zoom,
                                                                  pt.y() * self.canvas.zoom, 150, 150))
        else:
            self.canvas.set_zoom(1)
        self.options.update()

    def show_size(self, size):
        self.size_cell.setText(f"{size.width()}x{size.height()}" if size is not None else "")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.canvas.cancel_shape()
            self.canvas.cancel_text()
        elif event.key() in (Qt.Key_Delete,):
            self.canvas.delete_selection()
        else:
            super().keyPressEvent(event)

    # ---- files ------------------------------------------------------------------------------------------------------------
    def name(self):
        return self.path.name if self.path else "untitled"

    def update_title(self):
        if self.frame is not None:
            self.frame.set_title(f"{self.name()} - {self.app_name}")

    def new(self):
        img = QImage(480, 360, QImage.Format_RGB32)
        img.fill(QColor("white"))
        self.canvas.set_image(img, checkpoint=False)
        self.canvas.undo_stack.clear()
        self.path, self.modified = None, False
        self.update_title()

    def load(self, path):
        img = QImage(str(path))
        if img.isNull():
            self._message("Paint", f"Paint cannot read this file.\n{path.name}\nThis is not a valid bitmap file, or "
                                   "its format is not currently supported.", "error")
            return
        self.canvas.set_image(img, checkpoint=False)
        self.canvas.undo_stack.clear()
        self.path, self.modified = Path(path), False
        self.update_title()

    def save(self, then=None):
        if self.path is None:
            self.save_as(then)
            return
        self.canvas.commit_text()
        self.canvas.commit_selection()
        fmt = {".jpg": "JPG", ".jpeg": "JPG", ".png": "PNG", ".gif": "GIF"}.get(self.path.suffix.lower(), "BMP")
        img = self.canvas.image
        if fmt == "GIF":
            img = img.convertToFormat(QImage.Format_Indexed8)
        if not img.save(str(self.path), fmt):
            self._message("Paint", f"Paint cannot save this file in that format.\n{self.path.name}", "error")
            return
        self.modified = False
        self.update_title()
        if callable(then):
            then()

    def save_as(self, then=None):
        from ..explorer import vfs
        from .notepad import SaveAsDialog
        folder = self.path.parent if self.path else vfs.my_pictures()
        name = self.path.name if self.path else "untitled.bmp"

        def saved(path):
            if path.suffix.lower() not in (".bmp", ".png", ".jpg", ".jpeg", ".gif"):
                path = path.with_suffix(".bmp")
            self.path = path
            self.save(then)
        vfs.my_pictures().mkdir(parents=True, exist_ok=True)
        SaveAsDialog(self.desktop, name, folder, saved)

    def open_dialog(self):
        open_picture_dialog(self.desktop, self.load)

    def _maybe_save(self, proceed):
        if not self.modified:
            proceed()
            return

        def answer(button):
            if button == "Yes":
                self.save(proceed)
            elif button == "No":
                proceed()
        self._message("Paint", f"Save changes to {self.name()}?", "warning", ("Yes", "No", "Cancel"), answer)

    def print_(self):
        from ..explorer import vfs
        from ..printing import print_image
        self.canvas.commit_text()
        self.canvas.commit_selection()
        temp = vfs.DRIVE_C / "WINDOWS" / "Temp"
        temp.mkdir(parents=True, exist_ok=True)
        path = temp / (Path(self.name()).stem + ".png")
        self.canvas.image.save(str(path), "PNG")
        print_image(self.desktop, path)

    def set_background(self, position):
        from .. import display
        if self.path is None or self.modified:
            self._message("Paint", "Save the picture first, then choose Set As Background again.", "info")
            self.save()
            return
        d = display.get()
        d.apply(str(self.path), position, d.data["color"])

    def closeEvent(self, event):
        if self.closing or not self.modified:
            event.accept()
            return
        event.ignore()

        def really_close():
            self.closing = True
            if self.frame is not None:
                self.desktop.close_window(self.frame)
        self._maybe_save(really_close)

    # ---- the Image menu ---------------------------------------------------------------------------------------------------
    def _target(self):
        """Image commands work on the selection if there is one, else the whole picture."""
        c = self.canvas
        c.commit_text()
        if c.sel is not None:
            c.lift()
            return "sel", c.sel["float"]
        return "image", c.image

    def _apply(self, kind, img):
        c = self.canvas
        if kind == "sel":
            c.sel.update(float=img.convertToFormat(QImage.Format_RGB32), mask=None, cache_key=None)
            c.update()
        else:
            c.set_image(img)

    def invert(self):
        kind, img = self._target()
        img = img.copy()
        img.invertPixels()
        self._apply(kind, img)

    def flip_rotate(self):
        def go(choice, angle):
            kind, img = self._target()
            if choice == "h":
                img = img.mirrored(True, False)
            elif choice == "v":
                img = img.mirrored(False, True)
            else:
                from PySide6.QtGui import QTransform
                img = img.transformed(QTransform().rotate(angle))
            self._apply(kind, img)
        flip_dialog(self.desktop, go)

    def stretch(self):
        def go(h_pct, v_pct):
            kind, img = self._target()
            w = max(1, round(img.width() * h_pct / 100))
            h = max(1, round(img.height() * v_pct / 100))
            self._apply(kind, img.scaled(w, h, Qt.IgnoreAspectRatio, Qt.FastTransformation))
        stretch_dialog(self.desktop, go)

    def attributes(self):
        attributes_dialog(self.desktop, self.canvas.image.size(), self.resize_image)

    def resize_image(self, size):
        img = QImage(size, QImage.Format_RGB32)
        img.fill(self.bg)
        p = QPainter(img)
        p.drawImage(0, 0, self.canvas.image)
        p.end()
        self.canvas.set_image(img)

    def clear_image(self):
        c = self.canvas
        c.commit_text()
        c.sel = None
        img = QImage(c.image.size(), QImage.Format_RGB32)
        img.fill(self.bg)
        c.set_image(img)

    def custom_zoom(self):
        def go(level):
            self.canvas.set_zoom(level)
        zoom_dialog(self.desktop, self.canvas.zoom, go)

    def edit_colors(self, index):
        start = self.colorbox.colors[index] if index is not None else self.fg

        def chosen(color):
            if index is not None:
                self.colorbox.colors[index] = color
            self.set_color(color, True)
        color_dialog(self.desktop, start, chosen)

    def _message(self, title, text, icon="info", buttons=("OK",), on_button=None):
        from ..explorer.dialogs import msgbox
        title = title.replace("Paint", self.app_name)
        return msgbox(self.desktop, title, text, icon, buttons, on_button)


HELP_TEXT = ("Pick a tool on the left, a color at the bottom (left-click for the drawing color, right-click for the "
             "background color), and draw.\n\nHold Shift to draw straight lines, squares and circles. "
             "Curve: drag a line, then click twice to bend it. Polygon: click each corner, double-click to finish. "
             "Ctrl-drag a selection to copy it. Double-click a color to change it.")


# ---- dialogs ----------------------------------------------------------------------------------------------------------------------

def _dialog(desktop, title, body, on_ok, focus=None):
    from ..network import DialogBody, _fixed_window
    outer = DialogBody()
    v = QVBoxLayout(outer)
    v.setContentsMargins(12, 12, 12, 12)
    v.addWidget(body)
    row = QHBoxLayout()
    row.addStretch()
    ok, cancel = QPushButton("OK"), QPushButton("Cancel")
    for b in (ok, cancel):
        b.setFixedSize(75, 23)
        row.addWidget(b)
    v.addLayout(row)
    holder = {}

    def close():
        w = holder.pop("win", None)
        if w is not None:
            desktop.close_window(w)

    def accept():
        if on_ok() is not False:
            close()
    ok.clicked.connect(accept)
    cancel.clicked.connect(close)
    ok.setDefault(True)
    holder["win"] = _fixed_window(desktop, title, outer, close)
    holder["win"].icon = paint_icon()
    desktop.open_window(holder["win"])
    if focus is not None:
        focus.setFocus()
    return holder["win"]


def flip_dialog(desktop, go):
    body = QWidget()
    v = QVBoxLayout(body)
    v.addWidget(QLabel("Flip or rotate"))
    radios = {}
    group = QButtonGroup(body)
    for key, text in (("h", "&Flip horizontal"), ("v", "Flip &vertical"), ("r", "&Rotate by angle")):
        r = QRadioButton(text)
        group.addButton(r)
        radios[key] = r
        v.addWidget(r)
    radios["h"].setChecked(True)
    angles = {}
    ag = QButtonGroup(body)
    for a in (90, 180, 270):
        r = QRadioButton(f"{a}°")
        r.setContentsMargins(20, 0, 0, 0)
        r.setEnabled(False)
        ag.addButton(r)
        angles[a] = r
        row = QHBoxLayout()
        row.addSpacing(22)
        row.addWidget(r)
        v.addLayout(row)
    angles[90].setChecked(True)
    radios["r"].toggled.connect(lambda on: [r.setEnabled(on) for r in angles.values()])
    _dialog(desktop, "Flip and Rotate", body,
            lambda: go(next(k for k, r in radios.items() if r.isChecked()),
                       next(a for a, r in angles.items() if r.isChecked())))


def stretch_dialog(desktop, go):
    body = QWidget()
    g = QGridLayout(body)
    g.addWidget(QLabel("Stretch"), 0, 0, 1, 3)
    h, v = QSpinBox(), QSpinBox()
    for i, (label, spin) in enumerate((("&Horizontal:", h), ("&Vertical:", v))):
        spin.setRange(1, 500)
        spin.setValue(100)
        lab = QLabel(label)
        lab.setBuddy(spin)
        g.addWidget(lab, i + 1, 0)
        g.addWidget(spin, i + 1, 1)
        g.addWidget(QLabel("%"), i + 1, 2)
    _dialog(desktop, "Stretch and Skew", body, lambda: go(h.value(), v.value()), h)


def attributes_dialog(desktop, size, go):
    body = QWidget()
    g = QGridLayout(body)
    w, h = QSpinBox(), QSpinBox()
    for i, (label, spin, value) in enumerate((("&Width:", w, size.width()), ("&Height:", h, size.height()))):
        spin.setRange(1, 4000)
        spin.setValue(value)
        lab = QLabel(label)
        lab.setBuddy(spin)
        g.addWidget(lab, i, 0)
        g.addWidget(spin, i, 1)
    g.addWidget(QLabel("Units: Pixels"), 2, 0, 1, 2)
    _dialog(desktop, "Attributes", body, lambda: go(QSize(w.value(), h.value())), w)


def zoom_dialog(desktop, current, go):
    body = QWidget()
    v = QVBoxLayout(body)
    v.addWidget(QLabel(f"Current zoom:  {current * 100}%"))
    group = QButtonGroup(body)
    radios = {}
    for z in (1, 2, 4, 6, 8):
        r = QRadioButton(f"{z * 100}%")
        group.addButton(r)
        radios[z] = r
        v.addWidget(r)
    radios.get(current, radios[1]).setChecked(True)
    _dialog(desktop, "Custom Zoom", body, lambda: go(next(z for z, r in radios.items() if r.isChecked())))


def color_dialog(desktop, start, chosen):
    picker = QColorDialog(start)
    picker.setWindowFlags(Qt.Widget)
    picker.setOptions(QColorDialog.NoButtons | QColorDialog.DontUseNativeDialog)
    _dialog(desktop, "Edit Colors", picker, lambda: chosen(picker.currentColor()))


def open_picture_dialog(desktop, on_open):
    """Open: pick a folder, then a picture in it."""
    from ..explorer import vfs
    places = [("My Pictures", vfs.my_pictures()), ("My Documents", vfs.my_documents()),
              ("Desktop", vfs.user_home() / "Desktop"), ("Shared Pictures", vfs.shared_documents() / "Shared Pictures"),
              ("Wallpaper", vfs.DRIVE_C / "WINDOWS" / "Web" / "Wallpaper"), ("External Drive (E:)", vfs.local_storage())]
    body = QWidget()
    g = QGridLayout(body)
    g.addWidget(QLabel("Look &in:"), 0, 0)
    where = QComboBox()
    for label, path in places:
        where.addItem(QApplication.style().standardIcon(QStyle.SP_DirIcon), label, str(path))
    g.addWidget(where, 0, 1)
    files = QListWidget()
    files.setMinimumSize(360, 200)
    g.addWidget(files, 1, 0, 1, 2)
    g.addWidget(QLabel("File &name:"), 2, 0)
    name = QLineEdit()
    g.addWidget(name, 2, 1)
    exts = (".bmp", ".png", ".jpg", ".jpeg", ".gif")

    def fill():
        files.clear()
        folder = Path(where.currentData())
        if folder.is_dir():
            for p in sorted(folder.iterdir(), key=lambda p: p.name.lower()):
                if p.suffix.lower() in exts:
                    item = QListWidgetItem(QApplication.style().standardIcon(QStyle.SP_FileIcon), p.name)
                    item.setData(Qt.UserRole, str(p))
                    files.addItem(item)
    where.currentIndexChanged.connect(fill)
    files.currentItemChanged.connect(lambda item, _p: item and name.setText(item.text()))
    fill()
    holder = {}

    def accept():
        path = Path(where.currentData()) / name.text().strip()
        if not name.text().strip() or not path.is_file():
            return False
        on_open(path)
    win = _dialog(desktop, "Open", body, accept, name)
    files.itemDoubleClicked.connect(lambda item: (accept() is not False) and desktop.close_window(win))
    holder["win"] = win


def open_paint(desktop, path=None):
    body = Paint(desktop, path)
    win = XPWindow(desktop, f"{body.name()} - Paint", body, paint_icon(), (720, 560))
    body.frame = win
    desktop.open_window(win)
    return win
