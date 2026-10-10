"""Gemini Draw: a lightweight vector illustration editor for ClaudeXP."""
import json
import math
from pathlib import Path

from PySide6.QtCore import QLineF, QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QKeySequence, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import (QApplication, QColorDialog, QGraphicsEllipseItem, QGraphicsItem,
                               QGraphicsLineItem, QGraphicsPathItem, QGraphicsRectItem,
                               QGraphicsScene, QGraphicsTextItem, QGraphicsView, QButtonGroup, QHBoxLayout,
                               QLabel, QMenuBar, QPushButton, QSpinBox, QStyle, QVBoxLayout, QWidget)

from .. import sound
from ..wm import XPWindow
from .notepad import MENU_STYLE, SaveAsDialog
from .office_icons import office_icon
from .opendialog import open_dialog

CANVAS_WIDTH, CANVAS_HEIGHT = 1000, 700
MAX_DOCUMENT_BYTES = 20 * 1024 * 1024
MAX_OBJECTS = 2000
MAX_TEXT_LENGTH = 100_000
MAX_PATH_POINTS = 20_000
MAX_COORDINATE = 100_000
TOOLS = ("select", "rect", "ellipse", "line", "pen", "text")
STYLE = MENU_STYLE + """
QWidget#geminiDraw { background: #ECE9D8; }
QWidget#drawBar { background: #ECE9D8; border-bottom: 1px solid #ACA899; }
QGraphicsView { background: #777777; border: 1px solid #7F9DB9; }
QLabel#drawStatus { border-top: 1px solid #ACA899; padding: 2px 6px; font-family: Tahoma; font-size: 11px; }
"""


def _finite(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


def _item_flags():
    return (QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemIsSelectable |
            QGraphicsItem.ItemSendsGeometryChanges)


class _ModifiedItem:
    def _init_modified(self, changed):
        self._changed = changed
        self.setFlags(_item_flags())

    def itemChange(self, change, value):
        result = super().itemChange(change, value)
        if change == QGraphicsItem.ItemPositionHasChanged:
            self._changed()
        return result


class DrawRectItem(_ModifiedItem, QGraphicsRectItem):
    def __init__(self, rect, changed):
        QGraphicsRectItem.__init__(self, rect)
        self._init_modified(changed)


class DrawEllipseItem(_ModifiedItem, QGraphicsEllipseItem):
    def __init__(self, rect, changed):
        QGraphicsEllipseItem.__init__(self, rect)
        self._init_modified(changed)


class DrawLineItem(_ModifiedItem, QGraphicsLineItem):
    def __init__(self, line, changed):
        QGraphicsLineItem.__init__(self, line)
        self._init_modified(changed)


class DrawPathItem(_ModifiedItem, QGraphicsPathItem):
    def __init__(self, path, changed):
        QGraphicsPathItem.__init__(self, path)
        self._init_modified(changed)


class DrawTextItem(_ModifiedItem, QGraphicsTextItem):
    def __init__(self, text, changed):
        super().__init__(text)
        self._changed = changed
        self.setFlags(_item_flags() | QGraphicsItem.ItemIsFocusable)
        self.setTextInteractionFlags(Qt.TextEditorInteraction)
        self.document().contentsChanged.connect(changed)


class DrawView(QGraphicsView):
    def __init__(self, owner, scene):
        super().__init__(scene)
        self.owner = owner
        self.start = None
        self.preview = None
        self.path = None
        self.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setAlignment(Qt.AlignCenter)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.fitInView(self.scene().sceneRect(), Qt.KeepAspectRatio)

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton or self.owner.tool == "select":
            return super().mousePressEvent(event)
        point = self.mapToScene(event.position().toPoint())
        if self.owner.tool == "text":
            self.owner.add_text(point)
            event.accept()
            return
        if len(self.owner.scene.items()) >= MAX_OBJECTS:
            self.owner._message("Gemini Draw", f"A drawing can contain at most {MAX_OBJECTS} objects.", "warning")
            event.accept()
            return
        self.start = point
        self.owner.scene.clearSelection()
        if self.owner.tool == "rect":
            item = DrawRectItem(QRectF(point, point), self.owner._mark_modified)
        elif self.owner.tool == "ellipse":
            item = DrawEllipseItem(QRectF(point, point), self.owner._mark_modified)
        elif self.owner.tool == "line":
            item = DrawLineItem(QLineF(point, point), self.owner._mark_modified)
        else:
            self.path = QPainterPath(point)
            item = DrawPathItem(self.path, self.owner._mark_modified)
        self.owner._style_item(item)
        self.owner.scene.addItem(item)
        self.preview = item
        event.accept()

    def mouseMoveEvent(self, event):
        if self.start is None or self.preview is None:
            return super().mouseMoveEvent(event)
        point = self.mapToScene(event.position().toPoint())
        if self.owner.tool == "rect":
            self.preview.setRect(QRectF(self.start, point).normalized())
        elif self.owner.tool == "ellipse":
            self.preview.setRect(QRectF(self.start, point).normalized())
        elif self.owner.tool == "line":
            self.preview.setLine(self.start.x(), self.start.y(), point.x(), point.y())
        else:
            self.path.lineTo(point)
            self.preview.setPath(self.path)
        event.accept()

    def mouseReleaseEvent(self, event):
        if self.start is None or self.preview is None:
            return super().mouseReleaseEvent(event)
        item = self.preview
        self.start = self.preview = self.path = None
        if isinstance(item, (QGraphicsRectItem, QGraphicsEllipseItem)) and (
                item.rect().width() < 2 or item.rect().height() < 2):
            self.owner.scene.removeItem(item)
        elif isinstance(item, QGraphicsLineItem) and item.line().length() < 2:
            self.owner.scene.removeItem(item)
        elif isinstance(item, QGraphicsPathItem) and item.path().elementCount() < 2:
            self.owner.scene.removeItem(item)
        else:
            item.setSelected(True)
            self.owner._mark_modified()
        event.accept()


class GeminiDraw(QWidget):
    def __init__(self, desktop, path=None):
        super().__init__()
        self.desktop = desktop
        self.frame = None
        self.path = None
        self.modified = False
        self._loading = False
        self.tool = "select"
        self.draw_color = QColor("#2B579A")
        self.fill_color = QColor("#DCE6F1")
        self.line_width = 3
        self.setObjectName("geminiDraw")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(STYLE)
        self.scene = QGraphicsScene(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT)
        self.scene.setBackgroundBrush(QColor("white"))

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._menu())
        bar = QWidget()
        bar.setObjectName("drawBar")
        tools = QHBoxLayout(bar)
        tools.setContentsMargins(5, 3, 5, 3)
        tool_group = QButtonGroup(self)
        tool_group.setExclusive(True)
        self.tool_buttons = {}
        for label, tool in (("Select", "select"), ("Rectangle", "rect"), ("Ellipse", "ellipse"),
                            ("Line", "line"), ("Freehand", "pen"), ("Text", "text")):
            button = QPushButton(label)
            button.setCheckable(True)
            button.setChecked(tool == self.tool)
            self.tool_buttons[tool] = button
            tool_group.addButton(button)
            button.clicked.connect(lambda _checked=False, key=tool: self.set_tool(key))
            tools.addWidget(button)
        self.fill_button = QPushButton("Fill")
        self.fill_button.clicked.connect(self.choose_fill)
        tools.addWidget(self.fill_button)
        self.stroke_button = QPushButton("Stroke")
        self.stroke_button.clicked.connect(self.choose_stroke)
        tools.addWidget(self.stroke_button)
        tools.addWidget(QLabel("Width:"))
        self.width_spin = QSpinBox()
        self.width_spin.setRange(1, 50)
        self.width_spin.setValue(self.line_width)
        self.width_spin.valueChanged.connect(self._line_width_changed)
        tools.addWidget(self.width_spin)
        for label, callback in (("Front", self.bring_forward), ("Back", self.send_backward),
                                ("Delete", self.delete_selected)):
            button = QPushButton(label)
            button.clicked.connect(callback)
            tools.addWidget(button)
        tools.addStretch()
        root.addWidget(bar)

        self.view = DrawView(self, self.scene)
        root.addWidget(self.view, 1)
        self.status = QLabel("Select a tool, then draw or move objects.")
        self.status.setObjectName("drawStatus")
        root.addWidget(self.status)
        self.scene.selectionChanged.connect(self._selection_changed)
        if path is None:
            self._update_title()
        else:
            self.load(Path(path))

    def _menu(self):
        menu = QMenuBar()
        menu.triggered.connect(lambda _action: sound.play("menu"))
        file_menu = menu.addMenu("&File")
        file_menu.addAction("&New", self.new, QKeySequence("Ctrl+N"))
        file_menu.addAction("&Open...", self.open_dialog, QKeySequence("Ctrl+O"))
        file_menu.addAction("&Save", self.save, QKeySequence("Ctrl+S"))
        file_menu.addAction("Save &As...", self.save_as)
        file_menu.addSeparator()
        file_menu.addAction("&Export PNG...", self.export_png)
        file_menu.addAction("&Print...", self.print_artboard, QKeySequence("Ctrl+P"))
        file_menu.addSeparator()
        file_menu.addAction("E&xit", lambda: self.frame.request_close())
        edit = menu.addMenu("&Edit")
        edit.addAction("Select &All", self.select_all, QKeySequence("Ctrl+A"))
        edit.addAction("&Delete", self.delete_selected, QKeySequence("Del"))
        arrange = menu.addMenu("&Arrange")
        arrange.addAction("Bring &Forward", self.bring_forward)
        arrange.addAction("Send &Backward", self.send_backward)
        insert = menu.addMenu("&Insert")
        insert.addAction("&Text", self.add_text, QKeySequence("T"))
        insert.addAction("&Rectangle", lambda: self.set_tool("rect"))
        insert.addAction("&Ellipse", lambda: self.set_tool("ellipse"))
        insert.addAction("&Line", lambda: self.set_tool("line"))
        insert.addAction("&Freehand", lambda: self.set_tool("pen"))
        menu.addMenu("&Help").addAction("&About Gemini Draw", self.about)
        return menu

    def name(self):
        return self.path.name if self.path else "Drawing"

    def _update_title(self):
        if self.frame is not None:
            prefix = "*" if self.modified else ""
            self.frame.set_title(f"{prefix}{self.name()} - Gemini Draw")

    def _message(self, title, text, icon="info", buttons=("OK",), on_button=None):
        from ..explorer.dialogs import msgbox
        return msgbox(self.desktop, title, text, icon, buttons, on_button)

    def set_tool(self, tool):
        self.tool = tool
        if tool in self.tool_buttons:
            self.tool_buttons[tool].setChecked(True)
        self.view.setDragMode(QGraphicsView.RubberBandDrag if tool == "select" else QGraphicsView.NoDrag)
        self.status.setText("Click and drag to draw." if tool in ("rect", "ellipse", "line", "pen")
                            else "Click to add editable text." if tool == "text"
                            else "Select, move, resize, or edit objects.")

    def _style_item(self, item):
        pen = QPen(self.draw_color, self.line_width)
        pen.setJoinStyle(Qt.RoundJoin)
        pen.setCapStyle(Qt.RoundCap)
        item.setPen(pen)
        item.setBrush(self.fill_color if isinstance(item, (QGraphicsRectItem, QGraphicsEllipseItem))
                      else Qt.NoBrush)

    def _mark_modified(self):
        if not self._loading:
            self.modified = True
            self._update_title()

    def _line_width_changed(self, value):
        self.line_width = value
        for item in self.scene.selectedItems():
            pen = item.pen()
            pen.setWidthF(value)
            item.setPen(pen)
        if self.scene.selectedItems():
            self._mark_modified()

    def _selection_changed(self):
        count = len(self.scene.selectedItems())
        if count:
            self.status.setText(f"{count} object(s) selected.")

    def choose_fill(self):
        color = QColorDialog.getColor(self.fill_color, self, "Fill Color")
        if not color.isValid():
            return
        self.fill_color = color
        for item in self.scene.selectedItems():
            if isinstance(item, (QGraphicsRectItem, QGraphicsEllipseItem)):
                item.setBrush(color)
        self._mark_modified()

    def choose_stroke(self):
        color = QColorDialog.getColor(self.draw_color, self, "Stroke Color")
        if not color.isValid():
            return
        self.draw_color = color
        for item in self.scene.selectedItems():
            pen = item.pen()
            pen.setColor(color)
            item.setPen(pen)
            if isinstance(item, QGraphicsTextItem):
                item.setDefaultTextColor(color)
        self._mark_modified()

    def add_text(self, position=None):
        if len(self.scene.items()) >= MAX_OBJECTS:
            return self._message("Gemini Draw", f"A drawing can contain at most {MAX_OBJECTS} objects.", "warning")
        item = DrawTextItem("Double-click to edit", self._mark_modified)
        item.setDefaultTextColor(self.draw_color)
        item.setTextWidth(360)
        item.setPos(position if position is not None else
                    QPointF(CANVAS_WIDTH / 2 - 180, CANVAS_HEIGHT / 2 - 30))
        self.scene.addItem(item)
        item.setSelected(True)
        self.set_tool("select")
        self._mark_modified()

    def delete_selected(self):
        for item in self.scene.selectedItems():
            self.scene.removeItem(item)
        self._mark_modified()

    def select_all(self):
        for item in self.scene.items():
            if item.flags() & QGraphicsItem.ItemIsSelectable:
                item.setSelected(True)

    def bring_forward(self):
        selected = self.scene.selectedItems()
        if selected:
            selected[0].setZValue(selected[0].zValue() + 1)
            self._mark_modified()

    def send_backward(self):
        selected = self.scene.selectedItems()
        if selected:
            selected[0].setZValue(selected[0].zValue() - 1)
            self._mark_modified()

    def drawing_data(self):
        objects = []
        for item in sorted(self.scene.items(), key=lambda entry: entry.zValue()):
            if isinstance(item, DrawTextItem):
                font = item.font()
                obj = {"x": item.pos().x(), "y": item.pos().y(), "stroke": item.defaultTextColor().name(),
                       "line_width": 0, "z": item.zValue(), "type": "text", "text": item.toPlainText(),
                       "color": item.defaultTextColor().name(),
                       "width": item.textWidth() if item.textWidth() > 0 else item.boundingRect().width(),
                       "font": font.family(), "size": font.pointSizeF(), "bold": font.bold()}
                objects.append(obj)
                continue
            else:
                pen = item.pen()
                common = {"x": item.pos().x(), "y": item.pos().y(), "stroke": pen.color().name(),
                          "line_width": pen.widthF(), "z": item.zValue()}
            if isinstance(item, DrawRectItem):
                rect = item.mapRectToScene(item.rect())
                obj = {**common, "x": rect.x(), "y": rect.y(), "type": "rectangle",
                       "width": rect.width(), "height": rect.height(),
                       "fill": item.brush().color().name()}
            elif isinstance(item, DrawEllipseItem):
                rect = item.mapRectToScene(item.rect())
                obj = {**common, "x": rect.x(), "y": rect.y(), "type": "ellipse",
                       "width": rect.width(), "height": rect.height(),
                       "fill": item.brush().color().name()}
            elif isinstance(item, DrawLineItem):
                line = item.line()
                start = item.mapToScene(line.p1())
                end = item.mapToScene(line.p2())
                obj = {**common, "x": start.x(), "y": start.y(), "type": "line",
                       "x2": end.x() - start.x(), "y2": end.y() - start.y()}
            elif isinstance(item, DrawPathItem):
                path = item.path()
                obj = {**common, "type": "path",
                       "points": [[path.elementAt(i).x, path.elementAt(i).y]
                                  for i in range(path.elementCount())]}
            else:
                continue
            objects.append(obj)
        return {"format": "Gemini Draw Vector", "version": 1, "width": CANVAS_WIDTH,
                "height": CANVAS_HEIGHT, "objects": objects}

    def _validate(self, data):
        if (not isinstance(data, dict) or data.get("format") != "Gemini Draw Vector"
                or data.get("version") != 1 or data.get("width") != CANVAS_WIDTH
                or data.get("height") != CANVAS_HEIGHT or not isinstance(data.get("objects"), list)):
            raise ValueError("This is not a supported Gemini Draw project.")
        objects = data["objects"]
        if len(objects) > MAX_OBJECTS:
            raise ValueError(f"A drawing can contain at most {MAX_OBJECTS} objects.")
        text_total = 0
        for obj in objects:
            if not isinstance(obj, dict) or obj.get("type") not in ("text", "rectangle", "ellipse", "line", "path"):
                raise ValueError("The drawing contains an invalid object.")
            for key in ("x", "y", "z"):
                if not _finite(obj.get(key)) or abs(obj[key]) > MAX_COORDINATE:
                    raise ValueError("An object has an invalid position or layer.")
            width = obj.get("line_width")
            if not _finite(width) or not 0 <= width <= 100:
                raise ValueError("An object has an invalid stroke width.")
            if not isinstance(obj.get("stroke"), str) or not QColor(obj["stroke"]).isValid():
                raise ValueError("An object has an invalid stroke color.")
            if obj["type"] in ("rectangle", "ellipse"):
                for key in ("width", "height"):
                    if not _finite(obj.get(key)) or not 0 < obj[key] <= MAX_COORDINATE:
                        raise ValueError("A shape has invalid dimensions.")
                if not isinstance(obj.get("fill"), str) or not QColor(obj["fill"]).isValid():
                    raise ValueError("A shape has an invalid fill color.")
            elif obj["type"] == "line":
                if not _finite(obj.get("x2")) or not _finite(obj.get("y2")) or (
                        abs(obj["x2"]) > MAX_COORDINATE or abs(obj["y2"]) > MAX_COORDINATE):
                    raise ValueError("A line has an invalid endpoint.")
            elif obj["type"] == "path":
                points = obj.get("points")
                if not isinstance(points, list) or not 2 <= len(points) <= MAX_PATH_POINTS:
                    raise ValueError("A freehand path has an invalid number of points.")
                if any(not isinstance(point, list) or len(point) != 2
                       or not all(_finite(value) and abs(value) <= MAX_COORDINATE for value in point)
                       for point in points):
                    raise ValueError("A freehand path contains invalid points.")
            else:
                text = obj.get("text")
                if not isinstance(text, str) or len(text) > MAX_TEXT_LENGTH:
                    raise ValueError("A text object is invalid or too long.")
                text_total += len(text.encode("utf-8"))
                if text_total > MAX_DOCUMENT_BYTES:
                    raise ValueError("The drawing text is too large.")
                if (not _finite(obj.get("width")) or not 1 <= obj["width"] <= MAX_COORDINATE
                        or not _finite(obj.get("size")) or not 1 <= obj["size"] <= 200
                        or not isinstance(obj.get("font"), str) or len(obj["font"]) > 256
                        or not isinstance(obj.get("bold"), bool)
                        or not isinstance(obj.get("color"), str) or not QColor(obj["color"]).isValid()):
                    raise ValueError("A text object contains invalid formatting.")

    def load(self, path):
        path = Path(path)
        try:
            if path.stat().st_size > MAX_DOCUMENT_BYTES:
                raise ValueError("The drawing file is larger than the 20 MB limit.")
            data = json.loads(path.read_text(encoding="utf-8"))
            self._validate(data)
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
            return self._message("Gemini Draw", f"Cannot open {path.name}.\n{error}", "error")

        self._loading = True
        self.scene.clear()
        try:
            for obj in data["objects"]:
                item_type = obj["type"]
                if item_type == "rectangle":
                    item = DrawRectItem(QRectF(0, 0, obj["width"], obj["height"]), self._mark_modified)
                    item.setBrush(QColor(obj["fill"]))
                elif item_type == "ellipse":
                    item = DrawEllipseItem(QRectF(0, 0, obj["width"], obj["height"]), self._mark_modified)
                    item.setBrush(QColor(obj["fill"]))
                elif item_type == "line":
                    item = DrawLineItem(QLineF(0, 0, obj["x2"], obj["y2"]), self._mark_modified)
                elif item_type == "path":
                    path_item = QPainterPath(QPointF(*obj["points"][0]))
                    for x, y in obj["points"][1:]:
                        path_item.lineTo(x, y)
                    item = DrawPathItem(path_item, self._mark_modified)
                else:
                    item = DrawTextItem(obj["text"], self._mark_modified)
                    item.setTextWidth(obj["width"])
                    item.setDefaultTextColor(QColor(obj["color"]))
                    font = item.font()
                    font.setFamily(obj["font"])
                    font.setPointSizeF(obj["size"])
                    font.setBold(obj["bold"])
                    item.setFont(font)
                if not isinstance(item, DrawTextItem):
                    pen = QPen(QColor(obj["stroke"]))
                    pen.setWidthF(obj["line_width"])
                    item.setPen(pen)
                item.setPos(obj["x"], obj["y"])
                item.setZValue(obj["z"])
                self.scene.addItem(item)
        except (ValueError, TypeError, KeyError) as error:
            self._loading = False
            self.scene.clear()
            return self._message("Gemini Draw", f"Cannot open {path.name}.\n{error}", "error")
        self._loading = False
        self.path = path
        self.modified = False
        self._update_title()
        self.status.setText(f"Opened {len(data['objects'])} vector object(s).")

    def save(self, then=None):
        if self.path is None:
            self.save_as(then)
            return
        try:
            payload = json.dumps(self.drawing_data(), ensure_ascii=False, indent=2)
            if len(payload.encode("utf-8")) > MAX_DOCUMENT_BYTES:
                raise ValueError("The drawing would exceed the 20 MB file limit.")
            self.path.write_text(payload, encoding="utf-8")
        except (OSError, UnicodeError, ValueError) as error:
            return self._message("Gemini Draw", f"Cannot save {self.path.name}.\n{error}", "error")
        self.modified = False
        self._update_title()
        if callable(then):
            then()

    def save_as(self, then=None):
        name = self.path.name if self.path else "Drawing.gdraw"
        folder = self.path.parent if self.path else None

        def saved(path):
            if path.suffix.lower() != ".gdraw":
                path = path.with_suffix(".gdraw")
            self.path = path
            self.save(then)

        SaveAsDialog(self.desktop, name, folder, saved)

    def open_dialog(self):
        self._maybe_save(lambda: open_dialog(self.desktop, "Open Drawing", {".gdraw"}, self.load,
                                             icon=gemini_draw_icon()))

    def new(self):
        self._maybe_save(self._reset)

    def _reset(self):
        self.scene.clear()
        self.path = None
        self.modified = False
        self._update_title()
        self.status.setText("Select a tool, then draw or move objects.")

    def export_png(self):
        from ..explorer import vfs
        from .notepad import SaveAsDialog

        def saved(path):
            if path.suffix.lower() != ".png":
                path = path.with_suffix(".png")
            pixmap = QPixmap(CANVAS_WIDTH, CANVAS_HEIGHT)
            pixmap.fill(Qt.white)
            painter = QPainter(pixmap)
            self.scene.render(painter)
            painter.end()
            if not pixmap.save(str(path), "PNG"):
                return self._message("Gemini Draw", f"Cannot export {path.name}.", "error")

        SaveAsDialog(self.desktop, "Drawing.png", vfs.my_pictures(), saved)

    def print_artboard(self):
        from ..printing import print_image
        from ..explorer import vfs
        temp = vfs.DRIVE_C / "WINDOWS" / "Temp"
        temp.mkdir(parents=True, exist_ok=True)
        path = temp / f"{Path(self.name()).stem}.png"
        pixmap = QPixmap(CANVAS_WIDTH, CANVAS_HEIGHT)
        pixmap.fill(Qt.white)
        painter = QPainter(pixmap)
        self.scene.render(painter)
        painter.end()
        if pixmap.save(str(path), "PNG"):
            print_image(self.desktop, path)
        else:
            self._message("Gemini Draw", "Could not render the artboard for printing.", "error")

    def about(self):
        self._message("About Gemini Draw", "Gemini Draw\nVersion 1.0\n\n"
                      "A vector illustration editor. Projects use the Gemini-specific .gdraw format.")

    def _maybe_save(self, proceed):
        if not self.modified:
            proceed()
            return

        def answer(button):
            if button == "Yes":
                self.save(proceed)
            elif button == "No":
                proceed()

        self._message("Gemini Draw", f"Save changes to {self.name()}?", "warning",
                      ("Yes", "No", "Cancel"), answer)

    def closeEvent(self, event):
        if not self.modified:
            event.accept()
            return
        event.ignore()
        self._maybe_save(lambda: self.desktop.close_window(self.frame) if self.frame is not None else None)


def gemini_draw_icon():
    icon = office_icon("draw")
    if not icon.isNull():
        return icon
    return QApplication.style().standardIcon(QStyle.SP_FileDialogDetailedView)


def open_gemini_draw(desktop, path=None):
    body = GeminiDraw(desktop, path)
    window = XPWindow(desktop, f"{body.name()} - Gemini Draw", body, gemini_draw_icon(), (1000, 720))
    body.frame = window
    desktop.open_window(window)
    return window
