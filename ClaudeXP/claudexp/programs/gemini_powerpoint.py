"""Gemini PowerPoint: create, edit, save, present, and print slide decks."""
import base64
import json
from pathlib import Path

from PySide6.QtCore import QBuffer, QIODevice, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QIcon, QKeySequence, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (QGraphicsItem, QGraphicsPixmapItem, QGraphicsScene, QGraphicsTextItem,
                               QGraphicsView, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
                               QMenuBar, QPushButton, QVBoxLayout, QWidget)

from .. import sound
from ..wm import XPWindow
from .notepad import MENU_STYLE, SaveAsDialog
from .opendialog import open_dialog

SLIDE_WIDTH, SLIDE_HEIGHT = 960, 540
IMAGE_EXTENSIONS = {".bmp", ".gif", ".jpg", ".jpeg", ".png"}
MAX_IMAGE_BYTES = 20 * 1024 * 1024
MAX_IMAGE_PIXELS = 40_000_000
MAX_PRESENTATION_BYTES = 100 * 1024 * 1024
MAX_EMBEDDED_IMAGE_DATA = 70 * 1024 * 1024
MAX_PRESENTATION_TEXT = 5 * 1024 * 1024
MAX_SLIDES = 250
MAX_OBJECTS = 500
MAX_TEXT_LENGTH = 20_000
STYLE = MENU_STYLE + """
QWidget#geminiPowerPoint { background: #ECE9D8; }
QWidget#slideBar { background: #ECE9D8; border-bottom: 1px solid #ACA899; }
QListWidget { background: white; border: 1px solid #7F9DB9; font-family: Tahoma; font-size: 11px; }
QGraphicsView { background: #777777; border: 1px solid #7F9DB9; }
QLabel#slideStatus { border-top: 1px solid #ACA899; padding: 2px 6px; font-family: Tahoma; font-size: 11px; }
"""


def gemini_powerpoint_icon():
    from .office_icons import office_icon
    icon = office_icon("powerpoint")
    if not icon.isNull():
        return icon
    pixmap = QPixmap(32, 32)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(QPen(QColor("#4B3D63"), 1))
    painter.setBrush(QColor("#FFFFFF"))
    painter.drawRoundedRect(QRectF(3.5, 4.5, 25, 20), 2, 2)
    painter.setBrush(QColor("#8BA8D3"))
    painter.drawRect(QRectF(6, 7, 20, 15))
    painter.setPen(QPen(QColor("#FFFFFF"), 1))
    painter.drawLine(8, 18, 13, 12)
    painter.drawLine(13, 12, 18, 17)
    painter.drawLine(18, 17, 22, 13)
    painter.setPen(QPen(QColor("#4B3D63"), 2))
    painter.drawLine(16, 25, 16, 28)
    painter.drawLine(11, 29, 21, 29)
    painter.setPen(QPen(QColor("#184B78"), 1))
    painter.setBrush(QColor("#F5C451"))
    painter.drawEllipse(QRectF(18, 18, 13, 13))
    painter.drawText(QRectF(18, 18, 13, 13), Qt.AlignCenter, "G")
    painter.end()
    return QIcon(pixmap)


def _image_bytes(pixmap):
    buffer = QBuffer()
    buffer.open(QIODevice.WriteOnly)
    if not pixmap.save(buffer, "PNG"):
        raise OSError("The image could not be encoded.")
    return bytes(buffer.data())


class Slide:
    def __init__(self):
        self.scene = QGraphicsScene(0, 0, SLIDE_WIDTH, SLIDE_HEIGHT)
        self.scene.setBackgroundBrush(QColor("#FFFFFF"))


class EditableTextItem(QGraphicsTextItem):
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


class MovablePixmapItem(QGraphicsPixmapItem):
    def __init__(self, pixmap, changed):
        super().__init__(pixmap)
        self._changed = changed
        self.setFlags(self.GraphicsItemFlag.ItemIsMovable | self.GraphicsItemFlag.ItemIsSelectable |
                      self.GraphicsItemFlag.ItemSendsGeometryChanges)

    def itemChange(self, change, value):
        result = super().itemChange(change, value)
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self._changed()
        return result


class SlideView(QGraphicsView):
    def __init__(self, scene):
        super().__init__(scene)
        self.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing |
                            QPainter.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setAlignment(Qt.AlignCenter)
        self.setBackgroundBrush(QColor("#777777"))
        self.setStyleSheet("QGraphicsView { border: 1px solid #7F9DB9; }")
        self.fitInView(scene.sceneRect(), Qt.KeepAspectRatio)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.fitInView(self.scene().sceneRect(), Qt.KeepAspectRatio)


class SlideShow(QWidget):
    def __init__(self, slides, start):
        super().__init__()
        self.slides = slides
        self.index = max(0, min(start, len(slides) - 1))
        self.setStyleSheet("background: #202020; color: white;")
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        self.view = QGraphicsView()
        self.view.setStyleSheet("QGraphicsView { border: 0; background: #202020; }")
        self.view.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing |
                                 QPainter.SmoothPixmapTransform)
        self.view.setAlignment(Qt.AlignCenter)
        root.addWidget(self.view, 1)
        controls = QHBoxLayout()
        self.previous_button = QPushButton("&Previous")
        self.next_button = QPushButton("&Next")
        self.counter = QLabel()
        close = QPushButton("&Close Show")
        controls.addWidget(self.previous_button)
        controls.addWidget(self.next_button)
        controls.addWidget(self.counter)
        controls.addStretch()
        controls.addWidget(close)
        root.addLayout(controls)
        self.previous_button.clicked.connect(lambda: self.step(-1))
        self.next_button.clicked.connect(lambda: self.step(1))
        close.clicked.connect(self.close)
        self.show_slide()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.view.fitInView(self.view.scene().sceneRect(), Qt.KeepAspectRatio)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Right, Qt.Key_Space, Qt.Key_PageDown):
            self.step(1)
        elif event.key() in (Qt.Key_Left, Qt.Key_PageUp):
            self.step(-1)
        elif event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

    def step(self, amount):
        self.index = max(0, min(len(self.slides) - 1, self.index + amount))
        self.show_slide()

    def show_slide(self):
        self.view.setScene(self.slides[self.index].scene)
        self.view.fitInView(self.slides[self.index].scene.sceneRect(), Qt.KeepAspectRatio)
        self.counter.setText(f"Slide {self.index + 1} of {len(self.slides)}")
        self.previous_button.setEnabled(self.index > 0)
        self.next_button.setEnabled(self.index < len(self.slides) - 1)


class GeminiPowerPoint(QWidget):
    def __init__(self, desktop, path=None):
        super().__init__()
        self.desktop = desktop
        self.frame = None
        self.path = None
        self.modified = False
        self._loading = False
        self.slides = []
        self.setObjectName("geminiPowerPoint")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(STYLE)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._menu())

        bar = QWidget()
        bar.setObjectName("slideBar")
        bar.setAttribute(Qt.WA_StyledBackground, True)
        tools = QHBoxLayout(bar)
        tools.setContentsMargins(5, 3, 5, 3)
        for label, callback in (("New Slide", self.add_slide), ("Text Box", self.add_text),
                                ("Picture", self.add_picture), ("Delete Object", self.delete_object),
                                ("Slide Show", self.start_show)):
            button = QPushButton(label)
            button.clicked.connect(callback)
            tools.addWidget(button)
        tools.addStretch()
        root.addWidget(bar)

        work = QHBoxLayout()
        work.setContentsMargins(6, 6, 6, 4)
        work.setSpacing(6)
        self.slide_list = QListWidget()
        self.slide_list.setFixedWidth(155)
        self.slide_list.currentRowChanged.connect(self.select_slide)
        work.addWidget(self.slide_list)
        self.view = SlideView(QGraphicsScene(self))
        work.addWidget(self.view, 1)
        side = QVBoxLayout()
        up = QPushButton("Move Up")
        down = QPushButton("Move Down")
        remove = QPushButton("Delete Slide")
        up.clicked.connect(lambda: self.move_slide(-1))
        down.clicked.connect(lambda: self.move_slide(1))
        remove.clicked.connect(self.delete_slide)
        side.addWidget(up)
        side.addWidget(down)
        side.addWidget(remove)
        side.addStretch()
        work.addLayout(side)
        root.addLayout(work, 1)
        self.status = QLabel("Ready")
        self.status.setObjectName("slideStatus")
        root.addWidget(self.status)

        if path is None:
            self.add_slide()
            self.modified = False
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
        file_menu.addAction("&Print Slides...", self.print_slides, QKeySequence("Ctrl+P"))
        file_menu.addSeparator()
        file_menu.addAction("E&xit", lambda: self.frame.request_close())
        slide_menu = menu.addMenu("&Slide")
        slide_menu.addAction("&New Slide", self.add_slide, QKeySequence("Ctrl+M"))
        slide_menu.addAction("Move &Up", lambda: self.move_slide(-1))
        slide_menu.addAction("Move &Down", lambda: self.move_slide(1))
        slide_menu.addAction("&Delete Slide", self.delete_slide)
        insert = menu.addMenu("&Insert")
        insert.addAction("&Text Box", self.add_text)
        insert.addAction("&Picture...", self.add_picture)
        show = menu.addMenu("&Slide Show")
        show.addAction("&View Show", self.start_show, QKeySequence("F5"))
        menu.addMenu("&Help").addAction("&About Gemini PowerPoint", self.about)
        return menu

    def current_index(self):
        return max(0, self.slide_list.currentRow())

    def current_slide(self):
        return self.slides[self.current_index()] if self.slides else None

    def select_slide(self, index):
        if 0 <= index < len(self.slides):
            self.view.setScene(self.slides[index].scene)
            self.view.fitInView(self.slides[index].scene.sceneRect(), Qt.KeepAspectRatio)
            self.status.setText(f"Slide {index + 1} of {len(self.slides)}")

    def add_slide(self):
        if len(self.slides) >= MAX_SLIDES:
            return self._message("Gemini PowerPoint", f"A presentation can contain at most {MAX_SLIDES} slides.",
                                 "warning")
        slide = Slide()
        title = EditableTextItem(f"Slide {len(self.slides) + 1}", self._mark_modified)
        slide.scene.addItem(title)
        title.setDefaultTextColor(QColor("#1B3455"))
        font = title.font()
        font.setPointSize(30)
        title.setFont(font)
        title.setTextWidth(800)
        title.setPos(80, 65)
        self.slides.append(slide)
        self.slide_list.addItem(QListWidgetItem(f"Slide {len(self.slides)}"))
        self.slide_list.setCurrentRow(len(self.slides) - 1)
        self.modified = True
        self._update_title()

    def add_text(self):
        slide = self.current_slide()
        if slide is None:
            return
        if len(slide.scene.items()) >= MAX_OBJECTS:
            return self._message("Gemini PowerPoint", f"A slide can contain at most {MAX_OBJECTS} objects.",
                                 "warning")
        item = EditableTextItem("Double-click to edit", self._mark_modified)
        slide.scene.addItem(item)
        item.setDefaultTextColor(QColor("#202020"))
        font = item.font()
        font.setPointSize(24)
        item.setFont(font)
        item.setTextWidth(520)
        item.setPos(100, 210)
        self.view.setFocus()
        item.setSelected(True)
        self.modified = True

    def add_picture(self):
        open_dialog(self.desktop, "Insert Picture", IMAGE_EXTENSIONS, self._insert_picture,
                    icon=gemini_powerpoint_icon())

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
            return self._message("Gemini PowerPoint", f"Cannot insert {path.name}.\n{error}", "error")
        slide = self.current_slide()
        if slide is None:
            return
        if len(slide.scene.items()) >= MAX_OBJECTS:
            return self._message("Gemini PowerPoint", f"A slide can contain at most {MAX_OBJECTS} objects.",
                                 "warning")
        pixmap = pixmap.scaled(480, 360, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        item = MovablePixmapItem(pixmap, self._mark_modified)
        item.setData(0, base64.b64encode(data).decode("ascii"))
        item.setData(1, path.suffix.lower())
        item.setPos(240, 120)
        slide.scene.addItem(item)
        item.setSelected(True)
        self.view.setFocus()
        self.modified = True

    def delete_object(self):
        slide = self.current_slide()
        if slide is not None:
            selected = slide.scene.selectedItems()
            for item in selected:
                slide.scene.removeItem(item)
                del item
            if selected:
                self._mark_modified()

    def _mark_modified(self):
        if not self._loading:
            self.modified = True
            self._update_title()

    def move_slide(self, offset):
        index = self.slide_list.currentRow()
        target = index + offset
        if not (0 <= index < len(self.slides) and 0 <= target < len(self.slides)):
            return
        self.slides[index], self.slides[target] = self.slides[target], self.slides[index]
        self._loading = True
        self.slide_list.blockSignals(True)
        item = self.slide_list.takeItem(index)
        self.slide_list.insertItem(target, item)
        self.slide_list.setCurrentRow(target)
        self.slide_list.blockSignals(False)
        self._loading = False
        self.select_slide(target)
        self.modified = True

    def delete_slide(self):
        if len(self.slides) <= 1:
            return self._message("Gemini PowerPoint", "A presentation must contain at least one slide.", "info")
        index = self.slide_list.currentRow()
        if index < 0:
            return
        self._loading = True
        self.slide_list.blockSignals(True)
        self.slide_list.takeItem(index)
        self.slides.pop(index)
        self.slide_list.blockSignals(False)
        self._loading = False
        self.slide_list.setCurrentRow(min(index, len(self.slides) - 1))
        self._renumber()
        self.modified = True

    def _renumber(self):
        for index in range(self.slide_list.count()):
            self.slide_list.item(index).setText(f"Slide {index + 1}")
        self.select_slide(self.slide_list.currentRow())

    def start_show(self):
        if not self.slides:
            return
        show = SlideShow(self.slides, self.current_index())
        window = XPWindow(self.desktop, f"{self.name()} - Slide Show", show, gemini_powerpoint_icon(),
                          (900, 560))
        self.desktop.open_window(window)
        show.setFocus()

    def presentation_data(self):
        result = []
        image_bytes = 0
        text_bytes = 0
        for slide in self.slides:
            objects = []
            for item in reversed(slide.scene.items()):
                if isinstance(item, QGraphicsTextItem):
                    font = item.font()
                    text_bytes += len(item.toPlainText().encode("utf-8"))
                    if text_bytes > MAX_PRESENTATION_TEXT:
                        raise ValueError("The presentation text exceeds the 5 MB limit.")
                    objects.append({"type": "text", "text": item.toPlainText(),
                                    "x": item.pos().x(), "y": item.pos().y(),
                                    "width": item.textWidth(), "font": font.family(),
                                    "size": font.pointSizeF(), "bold": font.bold(),
                                    "color": item.defaultTextColor().name()})
                elif isinstance(item, QGraphicsPixmapItem):
                    image = item.data(0)
                    if not image:
                        image = base64.b64encode(_image_bytes(item.pixmap())).decode("ascii")
                    if len(image) > MAX_IMAGE_BYTES * 4 // 3 + 16:
                        raise ValueError("A slide image exceeds the 20 MB image limit.")
                    image_bytes += len(image)
                    if image_bytes > MAX_EMBEDDED_IMAGE_DATA:
                        raise ValueError("The presentation images exceed the 70 MB embedded-image limit.")
                    objects.append({"type": "image", "data": image, "format": item.data(1) or ".png",
                                    "x": item.pos().x(), "y": item.pos().y(),
                                    "width": item.pixmap().width(), "height": item.pixmap().height()})
            result.append({"objects": objects})
        return {"format": "Gemini PowerPoint Presentation", "version": 1,
                "active_slide": self.current_index(), "slides": result}

    def load(self, path):
        path = Path(path)
        try:
            if path.stat().st_size > MAX_PRESENTATION_BYTES:
                raise ValueError(f"Choose a presentation smaller than {MAX_PRESENTATION_BYTES // (1024 * 1024)} MB.")
            data = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(data, dict) or data.get("format") != "Gemini PowerPoint Presentation" or data.get(
                    "version") != 1:
                raise ValueError("This is not a supported Gemini PowerPoint presentation.")
            content = data.get("slides")
            if not isinstance(content, list) or not content or len(content) > MAX_SLIDES:
                raise ValueError(f"A presentation must contain between 1 and {MAX_SLIDES} slides.")
            active = data.get("active_slide", 0)
            if not isinstance(active, int):
                active = 0
            self._validate_presentation(content)
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError, TypeError) as error:
            return self._message("Gemini PowerPoint", f"Cannot open {path.name}.\n{error}", "error")

        self._loading = True
        self.slides.clear()
        self.slide_list.clear()
        try:
            for slide_data in content:
                slide = Slide()
                for obj in slide_data["objects"]:
                    if obj["type"] == "text":
                        item = EditableTextItem(obj["text"], self._mark_modified)
                        slide.scene.addItem(item)
                        item.setTextWidth(obj["width"])
                        item.setDefaultTextColor(QColor(obj["color"]))
                        font = item.font()
                        font.setFamily(obj["font"])
                        font.setPointSizeF(obj["size"])
                        font.setBold(obj["bold"])
                        item.setFont(font)
                        item.setPos(obj["x"], obj["y"])
                    else:
                        image_data = base64.b64decode(obj["data"], validate=True)
                        pixmap = QPixmap()
                        if not pixmap.loadFromData(image_data):
                            raise ValueError("A presentation image could not be decoded.")
                        item = MovablePixmapItem(pixmap, self._mark_modified)
                        item.setData(0, obj["data"])
                        item.setData(1, obj["format"])
                        item.setPos(obj["x"], obj["y"])
                        slide.scene.addItem(item)
                self.slides.append(slide)
                self.slide_list.addItem(f"Slide {len(self.slides)}")
        except (ValueError, TypeError, KeyError) as error:
            self._loading = False
            self._reset_slides()
            return self._message("Gemini PowerPoint", f"Cannot open {path.name}.\n{error}", "error")
        self.slide_list.setCurrentRow(max(0, min(active, len(self.slides) - 1)))
        self._loading = False
        self.path = path
        self.modified = False
        self._update_title()

    def _validate_presentation(self, slides):
        image_total = 0
        text_total = 0
        for slide in slides:
            if not isinstance(slide, dict) or not isinstance(slide.get("objects"), list):
                raise ValueError("The presentation contains an invalid slide.")
            if len(slide["objects"]) > MAX_OBJECTS:
                raise ValueError(f"A slide can contain at most {MAX_OBJECTS} objects.")
            for obj in slide["objects"]:
                if not isinstance(obj, dict) or obj.get("type") not in ("text", "image"):
                    raise ValueError("The presentation contains an invalid slide object.")
                for coordinate in ("x", "y"):
                    value = obj.get(coordinate)
                    if not isinstance(value, (int, float)) or not (-100_000 <= value <= 100_000):
                        raise ValueError("A slide object has an invalid position.")
                if obj["type"] == "text":
                    if not isinstance(obj.get("text"), str) or len(obj["text"]) > MAX_TEXT_LENGTH:
                        raise ValueError("A slide contains invalid or oversized text.")
                    text_total += len(obj["text"].encode("utf-8"))
                    if text_total > MAX_PRESENTATION_TEXT:
                        raise ValueError("The presentation text exceeds the 5 MB limit.")
                    if not isinstance(obj.get("width"), (int, float)) or not 20 <= obj["width"] <= 100_000:
                        raise ValueError("A text object has an invalid width.")
                    if not isinstance(obj.get("size"), (int, float)) or not 1 <= obj["size"] <= 200:
                        raise ValueError("A text object has an invalid font size.")
                    if not isinstance(obj.get("font"), str) or not isinstance(obj.get("bold"), bool):
                        raise ValueError("A text object has invalid font settings.")
                    if not isinstance(obj.get("color"), str) or not QColor(obj["color"]).isValid():
                        raise ValueError("A text object has an invalid color.")
                else:
                    encoded = obj.get("data")
                    if not isinstance(encoded, str) or len(encoded) > MAX_IMAGE_BYTES * 4 // 3 + 16:
                        raise ValueError("A presentation image is missing or too large.")
                    image_total += len(encoded)
                    if image_total > MAX_EMBEDDED_IMAGE_DATA:
                        raise ValueError("The presentation images exceed the 70 MB embedded-image limit.")
                    image = base64.b64decode(encoded, validate=True)
                    pixmap = QPixmap()
                    if len(image) > MAX_IMAGE_BYTES or not pixmap.loadFromData(image) or (
                            pixmap.width() * pixmap.height() > MAX_IMAGE_PIXELS):
                        raise ValueError("A presentation image is invalid or too large.")

    def _reset_slides(self):
        self._loading = True
        self.slides.clear()
        self.slide_list.clear()
        self._loading = False
        self.path = None
        self.add_slide()
        self.modified = False

    def new(self):
        self._maybe_save(self._reset_slides)

    def save(self, then=None):
        if self.path is None:
            self.save_as(then)
            return
        try:
            self.path.write_text(json.dumps(self.presentation_data(), ensure_ascii=False, indent=2),
                                 encoding="utf-8")
        except (OSError, UnicodeError, TypeError, ValueError) as error:
            return self._message("Gemini PowerPoint", f"Cannot save {self.path.name}.\n{error}", "error")
        self.modified = False
        self._update_title()
        if callable(then):
            then()

    def save_as(self, then=None):
        name = self.path.name if self.path else "Presentation.gpp"
        folder = self.path.parent if self.path else None

        def saved(path):
            if path.suffix.lower() != ".gpp":
                path = path.with_suffix(".gpp")
            self.path = path
            self.save(then)

        SaveAsDialog(self.desktop, name, folder, saved)

    def open_dialog(self):
        self._maybe_save(lambda: open_dialog(self.desktop, "Open Presentation", {".gpp"}, self.load,
                                             icon=gemini_powerpoint_icon()))

    def print_slides(self):
        from PySide6.QtGui import QTextDocument
        from ..printing import print_document

        pages = []
        for slide in self.slides:
            image = QPixmap(SLIDE_WIDTH, SLIDE_HEIGHT)
            image.fill(Qt.white)
            painter = QPainter(image)
            slide.scene.render(painter)
            painter.end()
            data = base64.b64encode(_image_bytes(image)).decode("ascii")
            pages.append(f"<p style='page-break-after:always'><img width='700' "
                         f"src='data:image/png;base64,{data}'></p>")
        document = QTextDocument()
        document.setHtml("".join(pages))
        print_document(self.desktop, self.name(), document)

    def about(self):
        self._message("About Gemini PowerPoint", "Gemini PowerPoint\nVersion 1.0")

    def name(self):
        return self.path.name if self.path else "Presentation"

    def _update_title(self):
        if self.frame is not None:
            self.frame.set_title(f"{self.name()} - Gemini PowerPoint")

    def _message(self, title, text, icon="info", buttons=("OK",), on_button=None):
        from ..explorer.dialogs import msgbox
        return msgbox(self.desktop, title, text, icon, buttons, on_button)

    def closeEvent(self, event):
        if not self.modified:
            event.accept()
            return
        event.ignore()

        def answer(button):
            if button == "Yes":
                self.save(self._close_after_save)
            elif button == "No":
                self._close_after_save()

        self._message("Gemini PowerPoint", f"Save changes to {self.name()}?", "warning",
                      ("Yes", "No", "Cancel"), answer)

    def _close_after_save(self):
        if self.frame is not None:
            self.desktop.close_window(self.frame)

    def _maybe_save(self, proceed):
        if not self.modified:
            proceed()
            return

        def answer(button):
            if button == "Yes":
                self.save(proceed)
            elif button == "No":
                proceed()

        self._message("Gemini PowerPoint", f"Save changes to {self.name()}?", "warning",
                      ("Yes", "No", "Cancel"), answer)


def open_gemini_powerpoint(desktop, path=None):
    body = GeminiPowerPoint(desktop, path)
    window = XPWindow(desktop, f"{body.name()} - Gemini PowerPoint", body, gemini_powerpoint_icon(),
                      (930, 620))
    body.frame = window
    desktop.open_window(window)
    body.view.setFocus()
    return window
