"""Gemini Publisher: design and print page-layout documents for ClaudeXP."""
import base64
import json
import math
from pathlib import Path

from PySide6.QtCore import QBuffer, QIODevice, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QIcon, QKeySequence, QPainter, QPen, QPixmap, QTextDocument
from PySide6.QtWidgets import (QColorDialog, QGraphicsItem, QGraphicsPixmapItem, QGraphicsRectItem,
                               QGraphicsScene, QGraphicsTextItem, QGraphicsView, QHBoxLayout,
                               QLabel, QListWidget, QListWidgetItem, QMenuBar, QPushButton, QSplitter,
                               QVBoxLayout, QWidget)

from .. import sound
from ..wm import XPWindow
from .notepad import MENU_STYLE, SaveAsDialog
from .opendialog import open_dialog

PAGE_WIDTH, PAGE_HEIGHT = 816, 1056
IMAGE_EXTENSIONS = {".bmp", ".gif", ".jpg", ".jpeg", ".png"}
MAX_IMAGE_BYTES = 20 * 1024 * 1024
MAX_IMAGE_PIXELS = 40_000_000
MAX_DOCUMENT_BYTES = 100 * 1024 * 1024
MAX_EMBEDDED_IMAGE_DATA = 70 * 1024 * 1024
MAX_DOCUMENT_TEXT = 5 * 1024 * 1024
MAX_PAGES = 100
MAX_OBJECTS = 500
MAX_TEXT_LENGTH = 20_000
STYLE = MENU_STYLE + """
QWidget#geminiPublisher { background: #ECE9D8; }
QWidget#publisherBar { background: #ECE9D8; border-bottom: 1px solid #ACA899; }
QListWidget { background: white; border: 1px solid #7F9DB9; font-family: Tahoma; font-size: 11px; }
QGraphicsView { background: #777777; border: 1px solid #7F9DB9; }
QLabel#publisherStatus { border-top: 1px solid #ACA899; padding: 2px 6px; font-family: Tahoma; font-size: 11px; }
"""


def _image_bytes(pixmap):
    buffer = QBuffer()
    buffer.open(QIODevice.WriteOnly)
    if not pixmap.save(buffer, "PNG"):
        raise OSError("The image could not be encoded.")
    return bytes(buffer.data())


def _finite_number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


class Page:
    def __init__(self, background="#FFFFFF"):
        self.scene = QGraphicsScene(0, 0, PAGE_WIDTH, PAGE_HEIGHT)
        self.background = QColor(background)
        self.scene.setBackgroundBrush(self.background)


class PublisherTextItem(QGraphicsTextItem):
    def __init__(self, text, changed):
        super().__init__(text)
        self._changed = changed
        self.setFlags(self.GraphicsItemFlag.ItemIsMovable | self.GraphicsItemFlag.ItemIsSelectable |
                      self.GraphicsItemFlag.ItemIsFocusable | self.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.setTextInteractionFlags(Qt.TextEditorInteraction)
        self.document().contentsChanged.connect(changed)

    def itemChange(self, change, value):
        result = super().itemChange(change, value)
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self._changed()
        return result


class PublisherImageItem(QGraphicsPixmapItem):
    def __init__(self, pixmap, changed, encoded="", image_format=".png"):
        super().__init__(pixmap)
        self._changed = changed
        self.encoded = encoded
        self.image_format = image_format
        self.setFlags(self.GraphicsItemFlag.ItemIsMovable | self.GraphicsItemFlag.ItemIsSelectable |
                      self.GraphicsItemFlag.ItemSendsGeometryChanges)

    def itemChange(self, change, value):
        result = super().itemChange(change, value)
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self._changed()
        return result


class PublisherShapeItem(QGraphicsRectItem):
    def __init__(self, rect, changed):
        super().__init__(rect)
        self._changed = changed
        self.setBrush(QColor("#D6E5F5"))
        self.setPen(QPen(QColor("#3A6EA5"), 3))
        self.setFlags(self.GraphicsItemFlag.ItemIsMovable | self.GraphicsItemFlag.ItemIsSelectable |
                      self.GraphicsItemFlag.ItemSendsGeometryChanges)

    def itemChange(self, change, value):
        result = super().itemChange(change, value)
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self._changed()
        return result


class PageView(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing |
                            QPainter.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setAlignment(Qt.AlignCenter)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.scene() is not None:
            self.fitInView(self.scene().sceneRect(), Qt.KeepAspectRatio)


class GeminiPublisher(QWidget):
    def __init__(self, desktop, path=None):
        super().__init__()
        self.desktop = desktop
        self.frame = None
        self.path = None
        self.pages = []
        self.modified = False
        self._loading = False
        self.setObjectName("geminiPublisher")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(STYLE)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._menu())
        toolbar = QWidget()
        toolbar.setObjectName("publisherBar")
        tools = QHBoxLayout(toolbar)
        tools.setContentsMargins(5, 3, 5, 3)
        for label, callback in (("New Page", self.add_page), ("Heading", self.add_heading),
                                ("Text Box", self.add_text), ("Picture", self.add_picture),
                                ("Rectangle", self.add_shape), ("Page Color", self.choose_background),
                                ("Delete Object", self.delete_object)):
            button = QPushButton(label)
            button.clicked.connect(callback)
            tools.addWidget(button)
        tools.addStretch()
        root.addWidget(toolbar)

        split = QSplitter(Qt.Horizontal)
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(4, 4, 4, 4)
        left_layout.addWidget(QLabel("Pages"))
        self.page_list = QListWidget()
        self.page_list.currentRowChanged.connect(self.select_page)
        left_layout.addWidget(self.page_list, 1)
        page_controls = QHBoxLayout()
        previous, next_page, delete = QPushButton("Up"), QPushButton("Down"), QPushButton("Delete")
        previous.setToolTip("Move page up")
        next_page.setToolTip("Move page down")
        previous.clicked.connect(lambda: self.move_page(-1))
        next_page.clicked.connect(lambda: self.move_page(1))
        delete.clicked.connect(self.delete_page)
        page_controls.addWidget(previous)
        page_controls.addWidget(next_page)
        page_controls.addWidget(delete)
        left_layout.addLayout(page_controls)
        split.addWidget(left)
        self.view = PageView()
        split.addWidget(self.view)
        split.setSizes([180, 720])
        root.addWidget(split, 1)
        self.status = QLabel("Ready")
        self.status.setObjectName("publisherStatus")
        root.addWidget(self.status)

        if path is not None:
            self.load(Path(path))
        else:
            self._append_page()
            self.modified = False
            self.select_page(0)

    def _menu(self):
        menu = QMenuBar()
        menu.triggered.connect(lambda _action: sound.play("menu"))
        file_menu = menu.addMenu("&File")
        file_menu.addAction("&New", self.new, QKeySequence("Ctrl+N"))
        file_menu.addAction("&Open...", self.open_dialog, QKeySequence("Ctrl+O"))
        file_menu.addAction("&Save", self.save, QKeySequence("Ctrl+S"))
        file_menu.addAction("Save &As...", self.save_as)
        file_menu.addSeparator()
        file_menu.addAction("&Print...", self.print_document, QKeySequence("Ctrl+P"))
        file_menu.addSeparator()
        file_menu.addAction("E&xit", lambda: self.frame.request_close())
        insert = menu.addMenu("&Insert")
        insert.addAction("&Heading", self.add_heading)
        insert.addAction("&Text Box", self.add_text)
        insert.addAction("&Picture...", self.add_picture)
        insert.addAction("&Rectangle", self.add_shape)
        page_menu = menu.addMenu("&Page")
        page_menu.addAction("&New Page", self.add_page, QKeySequence("Ctrl+Shift+N"))
        page_menu.addAction("Move Page &Up", lambda: self.move_page(-1))
        page_menu.addAction("Move Page &Down", lambda: self.move_page(1))
        page_menu.addAction("&Delete Page", self.delete_page)
        page_menu.addAction("Page &Color...", self.choose_background)
        menu.addMenu("&Help").addAction("&About Gemini Publisher", self.about)
        return menu

    def name(self):
        return self.path.name if self.path else "Publication"

    def _update_title(self):
        if self.frame is not None:
            prefix = "*" if self.modified else ""
            self.frame.set_title(f"{prefix}{self.name()} - Gemini Publisher")

    def _message(self, title, text, icon="info", buttons=("OK",), on_button=None):
        from ..explorer.dialogs import msgbox
        return msgbox(self.desktop, title, text, icon, buttons, on_button)

    def current_index(self):
        return max(0, self.page_list.currentRow())

    def current_page(self):
        index = self.page_list.currentRow()
        return self.pages[index] if 0 <= index < len(self.pages) else None

    def _append_page(self, page=None):
        if len(self.pages) >= MAX_PAGES:
            return self._message("Gemini Publisher", f"A publication can contain at most {MAX_PAGES} pages.",
                                 "warning")
        page = page or Page()
        self.pages.append(page)
        self.page_list.addItem(QListWidgetItem(f"Page {len(self.pages)}"))
        self.page_list.setCurrentRow(len(self.pages) - 1)
        return page

    def select_page(self, index):
        if not 0 <= index < len(self.pages):
            return
        page = self.pages[index]
        self.view.setScene(page.scene)
        self.view.fitInView(page.scene.sceneRect(), Qt.KeepAspectRatio)
        self.status.setText(f"Page {index + 1} of {len(self.pages)}    Letter (8.5 x 11 in)")

    def add_page(self):
        if len(self.pages) >= MAX_PAGES:
            return self._message("Gemini Publisher", f"A publication can contain at most {MAX_PAGES} pages.",
                                 "warning")
        self._append_page()
        self._mark_modified()

    def move_page(self, offset):
        index = self.page_list.currentRow()
        target = index + offset
        if not (0 <= index < len(self.pages) and 0 <= target < len(self.pages)):
            return
        self.pages[index], self.pages[target] = self.pages[target], self.pages[index]
        self._loading = True
        self.page_list.blockSignals(True)
        item = self.page_list.takeItem(index)
        self.page_list.insertItem(target, item)
        self.page_list.setCurrentRow(target)
        self.page_list.blockSignals(False)
        self._loading = False
        self._renumber_pages()
        self._mark_modified()

    def delete_page(self):
        if len(self.pages) <= 1:
            return self._message("Gemini Publisher", "A publication must contain at least one page.", "info")
        index = self.page_list.currentRow()
        if index < 0:
            return
        self._loading = True
        self.page_list.blockSignals(True)
        self.page_list.takeItem(index)
        self.pages.pop(index)
        self.page_list.blockSignals(False)
        self._loading = False
        self.page_list.setCurrentRow(min(index, len(self.pages) - 1))
        self._renumber_pages()
        self._mark_modified()

    def _renumber_pages(self):
        for index in range(self.page_list.count()):
            self.page_list.item(index).setText(f"Page {index + 1}")
        self.select_page(self.page_list.currentRow())

    def _add_text_item(self, text, position, size, color, width):
        page = self.current_page()
        if page is None:
            return
        if len(page.scene.items()) >= MAX_OBJECTS:
            return self._message("Gemini Publisher", f"A page can contain at most {MAX_OBJECTS} objects.",
                                 "warning")
        item = PublisherTextItem(text, self._mark_modified)
        page.scene.addItem(item)
        item.setDefaultTextColor(QColor(color))
        font = item.font()
        font.setPointSize(size)
        item.setFont(font)
        item.setTextWidth(width)
        item.setPos(*position)
        item.setSelected(True)
        self.view.setFocus()
        self._mark_modified()
        return item

    def add_heading(self):
        self._add_text_item("Your Heading", (68, 70), 32, "#1B3455", 680)

    def add_text(self):
        self._add_text_item("Double-click to edit this text.", (68, 190), 14, "#202020", 680)

    def add_shape(self):
        page = self.current_page()
        if page is None:
            return
        if len(page.scene.items()) >= MAX_OBJECTS:
            return self._message("Gemini Publisher", f"A page can contain at most {MAX_OBJECTS} objects.",
                                 "warning")
        item = PublisherShapeItem(QRectF(0, 0, 250, 110), self._mark_modified)
        page.scene.addItem(item)
        item.setPos(90, 330)
        item.setSelected(True)
        self.view.setFocus()
        self._mark_modified()

    def add_picture(self):
        open_dialog(self.desktop, "Insert Picture", IMAGE_EXTENSIONS, self._insert_picture,
                    icon=gemini_publisher_icon())

    def _insert_picture(self, path):
        path = Path(path)
        try:
            if path.stat().st_size > MAX_IMAGE_BYTES:
                raise ValueError(f"Choose an image smaller than {MAX_IMAGE_BYTES // (1024 * 1024)} MB.")
            data = path.read_bytes()
            pixmap = QPixmap()
            if not pixmap.loadFromData(data) or pixmap.width() * pixmap.height() > MAX_IMAGE_PIXELS:
                raise ValueError("The selected file is not a supported image or its dimensions are too large.")
        except (OSError, ValueError) as error:
            return self._message("Gemini Publisher", f"Cannot insert {path.name}.\n{error}", "error")
        page = self.current_page()
        if page is None:
            return
        if len(page.scene.items()) >= MAX_OBJECTS:
            return self._message("Gemini Publisher", f"A page can contain at most {MAX_OBJECTS} objects.",
                                 "warning")
        pixmap = pixmap.scaled(440, 440, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        item = PublisherImageItem(pixmap, self._mark_modified, base64.b64encode(data).decode("ascii"),
                                 path.suffix.lower())
        item.setPos(180, 310)
        page.scene.addItem(item)
        item.setSelected(True)
        self.view.setFocus()
        self._mark_modified()

    def choose_background(self):
        page = self.current_page()
        if page is None:
            return
        color = QColorDialog.getColor(page.background, self, "Page Color")
        if color.isValid():
            page.background = color
            page.scene.setBackgroundBrush(color)
            self._mark_modified()

    def delete_object(self):
        page = self.current_page()
        if page is not None:
            selected = page.scene.selectedItems()
            for item in selected:
                page.scene.removeItem(item)
            if selected:
                self._mark_modified()

    def _mark_modified(self):
        if not self._loading:
            self.modified = True
            self._update_title()

    def document_data(self):
        pages = []
        image_total = 0
        text_total = 0
        for page in self.pages:
            objects = []
            for item in reversed(page.scene.items()):
                position = item.pos()
                if isinstance(item, QGraphicsTextItem):
                    font = item.font()
                    text = item.toPlainText()
                    text_total += len(text.encode("utf-8"))
                    if text_total > MAX_DOCUMENT_TEXT:
                        raise ValueError("The publication text exceeds the 5 MB limit.")
                    objects.append({"type": "text", "text": text, "x": position.x(), "y": position.y(),
                                    "width": item.textWidth(), "font": font.family(),
                                    "size": font.pointSizeF(), "bold": font.bold(),
                                    "color": item.defaultTextColor().name()})
                elif isinstance(item, PublisherImageItem):
                    encoded = item.encoded or base64.b64encode(_image_bytes(item.pixmap())).decode("ascii")
                    image_total += len(encoded)
                    if len(encoded) > MAX_IMAGE_BYTES * 4 // 3 + 16:
                        raise ValueError("A publication image exceeds the 20 MB image limit.")
                    if image_total > MAX_EMBEDDED_IMAGE_DATA:
                        raise ValueError("The publication images exceed the 70 MB embedded-image limit.")
                    objects.append({"type": "image", "data": encoded, "format": item.image_format,
                                    "x": position.x(), "y": position.y(),
                                    "width": item.pixmap().width(), "height": item.pixmap().height()})
                elif isinstance(item, PublisherShapeItem):
                    objects.append({"type": "rectangle", "x": position.x(), "y": position.y(),
                                    "width": item.rect().width(), "height": item.rect().height(),
                                    "fill": item.brush().color().name(), "outline": item.pen().color().name(),
                                    "line_width": item.pen().widthF()})
            pages.append({"background": page.background.name(), "objects": objects})
        return {"format": "Gemini Publisher Document", "version": 1, "pages": pages}

    def load(self, path):
        path = Path(path)
        try:
            if path.stat().st_size > MAX_DOCUMENT_BYTES:
                raise ValueError("The publication file is larger than the 100 MB limit.")
            data = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise ValueError("This is not a supported Gemini Publisher document.")
            pages = data.get("pages")
            if (data.get("format") != "Gemini Publisher Document" or data.get("version") != 1
                    or not isinstance(pages, list) or not 1 <= len(pages) <= MAX_PAGES):
                raise ValueError("This is not a supported Gemini Publisher document.")
            self._validate_pages(pages)
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError, TypeError) as error:
            return self._message("Gemini Publisher", f"Cannot open {path.name}.\n{error}", "error")

        self._loading = True
        self.pages.clear()
        self.page_list.clear()
        try:
            for page_data in pages:
                page = Page(page_data["background"])
                for obj in page_data["objects"]:
                    if obj["type"] == "text":
                        item = PublisherTextItem(obj["text"], self._mark_modified)
                        item.setTextWidth(obj["width"])
                        item.setDefaultTextColor(QColor(obj["color"]))
                        font = item.font()
                        font.setFamily(obj["font"])
                        font.setPointSizeF(obj["size"])
                        font.setBold(obj["bold"])
                        item.setFont(font)
                        item.setPos(obj["x"], obj["y"])
                    elif obj["type"] == "image":
                        encoded = obj["data"]
                        raw = base64.b64decode(encoded, validate=True)
                        pixmap = QPixmap()
                        if not pixmap.loadFromData(raw):
                            raise ValueError("A publication image could not be decoded.")
                        pixmap = pixmap.scaled(round(obj["width"]), round(obj["height"]),
                                               Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
                        item = PublisherImageItem(pixmap, self._mark_modified, encoded, obj["format"])
                        item.setPos(obj["x"], obj["y"])
                    else:
                        item = PublisherShapeItem(QRectF(0, 0, obj["width"], obj["height"]),
                                                  self._mark_modified)
                        item.setBrush(QColor(obj["fill"]))
                        item.setPen(QPen(QColor(obj["outline"]), obj["line_width"]))
                        item.setPos(obj["x"], obj["y"])
                    page.scene.addItem(item)
                self.pages.append(page)
                self.page_list.addItem(f"Page {len(self.pages)}")
        except (ValueError, TypeError, KeyError) as error:
            self._loading = False
            self._reset_pages()
            return self._message("Gemini Publisher", f"Cannot open {path.name}.\n{error}", "error")
        self.page_list.setCurrentRow(0)
        self._loading = False
        self.path = path
        self.modified = False
        self.select_page(0)
        self._update_title()

    def _validate_pages(self, pages):
        image_total = 0
        text_total = 0
        for page in pages:
            if not isinstance(page, dict) or not isinstance(page.get("objects"), list):
                raise ValueError("The publication contains an invalid page.")
            if not isinstance(page.get("background"), str) or not QColor(page["background"]).isValid():
                raise ValueError("A page has an invalid background color.")
            if len(page["objects"]) > MAX_OBJECTS:
                raise ValueError(f"A page can contain at most {MAX_OBJECTS} objects.")
            for obj in page["objects"]:
                if not isinstance(obj, dict) or obj.get("type") not in ("text", "image", "rectangle"):
                    raise ValueError("The publication contains an invalid page object.")
                for coordinate in ("x", "y"):
                    value = obj.get(coordinate)
                    if not _finite_number(value) or not -100_000 <= value <= 100_000:
                        raise ValueError("A page object has an invalid position.")
                if obj["type"] == "text":
                    text = obj.get("text")
                    if not isinstance(text, str) or len(text) > MAX_TEXT_LENGTH:
                        raise ValueError("A page contains invalid or oversized text.")
                    text_total += len(text.encode("utf-8"))
                    if text_total > MAX_DOCUMENT_TEXT:
                        raise ValueError("The publication text exceeds the 5 MB limit.")
                    if (not _finite_number(obj.get("width")) or not 20 <= obj["width"] <= 100_000
                            or not _finite_number(obj.get("size")) or not 1 <= obj["size"] <= 200
                            or not isinstance(obj.get("font"), str) or len(obj["font"]) > 256
                            or not isinstance(obj.get("bold"), bool) or not isinstance(obj.get("color"), str)
                            or not QColor(obj["color"]).isValid()):
                        raise ValueError("A text object contains invalid formatting.")
                elif obj["type"] == "image":
                    encoded = obj.get("data")
                    if not isinstance(encoded, str) or len(encoded) > MAX_IMAGE_BYTES * 4 // 3 + 16:
                        raise ValueError("A publication image is missing or too large.")
                    image_total += len(encoded)
                    if image_total > MAX_EMBEDDED_IMAGE_DATA:
                        raise ValueError("The publication images exceed the 70 MB embedded-image limit.")
                    if obj.get("format") not in IMAGE_EXTENSIONS:
                        raise ValueError("A publication image has an unsupported format.")
                    if (not _finite_number(obj.get("width")) or not 1 <= obj["width"] <= PAGE_WIDTH * 4
                            or not _finite_number(obj.get("height"))
                            or not 1 <= obj["height"] <= PAGE_HEIGHT * 4):
                        raise ValueError("A publication image has invalid dimensions.")
                    raw = base64.b64decode(encoded, validate=True)
                    pixmap = QPixmap()
                    if (len(raw) > MAX_IMAGE_BYTES or not pixmap.loadFromData(raw)
                            or pixmap.width() * pixmap.height() > MAX_IMAGE_PIXELS):
                        raise ValueError("A publication image is invalid or too large.")
                else:
                    for key in ("width", "height"):
                        value = obj.get(key)
                        limit = PAGE_WIDTH if key == "width" else PAGE_HEIGHT
                        if not _finite_number(value) or not 1 <= value <= limit * 4:
                            raise ValueError("A rectangle has invalid dimensions.")
                    for key in ("fill", "outline"):
                        if not isinstance(obj.get(key), str) or not QColor(obj[key]).isValid():
                            raise ValueError("A rectangle has an invalid color.")
                    line_width = obj.get("line_width")
                    if not _finite_number(line_width) or not 0 <= line_width <= 100:
                        raise ValueError("A rectangle has an invalid outline width.")

    def _reset_pages(self):
        self._loading = True
        self.pages.clear()
        self.page_list.clear()
        self._loading = False
        self.path = None
        self._append_page()
        self.modified = False
        self.select_page(0)

    def new(self):
        self._maybe_save(self._reset_pages)

    def save(self, then=None):
        if self.path is None:
            self.save_as(then)
            return
        try:
            data = self.document_data()
            self._validate_pages(data["pages"])
            payload = json.dumps(data, ensure_ascii=False, indent=2)
            if len(payload.encode("utf-8")) > MAX_DOCUMENT_BYTES:
                raise ValueError("The publication would exceed the 100 MB file limit.")
            self.path.write_text(payload, encoding="utf-8")
        except (OSError, UnicodeError, TypeError, ValueError) as error:
            return self._message("Gemini Publisher", f"Cannot save {self.path.name}.\n{error}", "error")
        self.modified = False
        self._update_title()
        if callable(then):
            then()

    def save_as(self, then=None):
        name = self.path.name if self.path else "Publication.gpub"
        folder = self.path.parent if self.path else None

        def saved(path):
            if path.suffix.lower() != ".gpub":
                path = path.with_suffix(".gpub")
            self.path = path
            self.save(then)

        SaveAsDialog(self.desktop, name, folder, saved)

    def open_dialog(self):
        self._maybe_save(lambda: open_dialog(self.desktop, "Open Publication", {".gpub"}, self.load,
                                             icon=gemini_publisher_icon()))

    def print_document(self):
        from ..printing import print_document
        parts = []
        for page in self.pages:
            pixmap = QPixmap(PAGE_WIDTH, PAGE_HEIGHT)
            pixmap.fill(page.background)
            painter = QPainter(pixmap)
            page.scene.render(painter)
            painter.end()
            image = base64.b64encode(_image_bytes(pixmap)).decode("ascii")
            parts.append(f"<div style='page-break-after:always'><img width='540' "
                         f"src='data:image/png;base64,{image}'></div>")
        document = QTextDocument()
        document.setHtml("".join(parts))
        print_document(self.desktop, self.name(), document)

    def about(self):
        self._message("About Gemini Publisher", "Gemini Publisher\nVersion 1.0\n\n"
                      "Create page-layout publications and save them in the Gemini .gpub format.")

    def _maybe_save(self, proceed):
        if not self.modified:
            proceed()
            return

        def answer(button):
            if button == "Yes":
                self.save(proceed)
            elif button == "No":
                proceed()

        self._message("Gemini Publisher", f"Save changes to {self.name()}?", "warning",
                      ("Yes", "No", "Cancel"), answer)

    def closeEvent(self, event):
        if not self.modified:
            event.accept()
            return
        event.ignore()
        self._maybe_save(lambda: self.desktop.close_window(self.frame) if self.frame is not None else None)


def gemini_publisher_icon():
    from .office_icons import office_icon
    icon = office_icon("publisher")
    if not icon.isNull():
        return icon
    from PySide6.QtCore import QRectF
    from PySide6.QtGui import QColor, QPen

    pixmap = QPixmap(32, 32)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(QPen(QColor("#5C405F"), 1))
    painter.setBrush(QColor("#FFFFFF"))
    painter.drawRoundedRect(QRectF(5, 3, 21, 26), 2, 2)
    painter.setPen(QPen(QColor("#9B7A9F"), 1))
    painter.drawLine(9, 9, 22, 9)
    painter.drawLine(9, 13, 22, 13)
    painter.setPen(QPen(QColor("#184B78"), 1))
    painter.setBrush(QColor("#F5C451"))
    painter.drawEllipse(QRectF(18, 18, 13, 13))
    painter.drawText(QRectF(18, 18, 13, 13), Qt.AlignCenter, "G")
    painter.end()
    return QIcon(pixmap)


def open_gemini_publisher(desktop, path=None):
    body = GeminiPublisher(desktop, path)
    window = XPWindow(desktop, f"{body.name()} - Gemini Publisher", body, gemini_publisher_icon(),
                      (920, 700))
    body.frame = window
    desktop.open_window(window)
    return window
