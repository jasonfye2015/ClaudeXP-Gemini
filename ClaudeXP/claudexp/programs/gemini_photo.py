"""Gemini Photo: a branded raster editor built on ClaudeXP's Paint canvas."""
import base64
import json
from pathlib import Path

from PySide6.QtCore import QBuffer, QIODevice, Qt
from PySide6.QtGui import QImage, QImageReader, QPainter
from PySide6.QtWidgets import (QDialog, QDialogButtonBox, QHBoxLayout, QLabel, QListWidget,
                               QListWidgetItem, QPushButton, QSlider, QVBoxLayout)

from ..wm import XPWindow
from .office_icons import office_icon
from .paint import Paint
from .notepad import SaveAsDialog


def gemini_photo_icon():
    return office_icon("photo")


class GeminiPhoto(Paint):
    def __init__(self, desktop, path=None):
        project_path = Path(path) if path is not None and Path(path).suffix.lower() == ".gphoto" else None
        super().__init__(desktop, None if project_path else path,
                         app_name="Gemini Photo", app_icon=gemini_photo_icon())
        self.layers = [{"name": "Background", "visible": True, "opacity": 1.0,
                        "image": self.canvas.image.convertToFormat(QImage.Format_ARGB32)}]
        self.active_layer = 0
        if project_path is not None:
            self.load(project_path)

    def _menus(self):
        super()._menus()
        photo = self.menu.addMenu("&Photo")
        photo.addAction("&Crop to Selection", self.crop_to_selection)
        filters = photo.addMenu("&Filters")
        filters.addAction("&Grayscale", self.grayscale)
        filters.addAction("&Brighten", lambda: self.adjust_brightness(32))
        filters.addAction("&Darken", lambda: self.adjust_brightness(-32))
        photo.addSeparator()
        photo.addAction("&Layers...", self.manage_layers)
        photo.addAction("Open Layered &Project...", self.open_layered)
        photo.addAction("Save Layered Pro&ject As...", self.save_layered_as)

    def display_image(self):
        self.layers[self.active_layer]["image"] = self.canvas.image
        result = QImage(self.canvas.image.size(), QImage.Format_ARGB32)
        result.fill(Qt.transparent)
        painter = QPainter(result)
        for layer in self.layers:
            if layer["visible"]:
                painter.setOpacity(layer["opacity"])
                painter.drawImage(0, 0, layer["image"])
        painter.end()
        return result

    def flattened_image(self):
        image = QImage(self.canvas.image.size(), QImage.Format_RGB32)
        image.fill(Qt.white)
        painter = QPainter(image)
        painter.drawImage(0, 0, self.display_image())
        painter.end()
        return image

    def _activate_layer(self, index):
        self.layers[self.active_layer]["image"] = self.canvas.image
        self.active_layer = index
        self.canvas.image = self.layers[index]["image"]
        self.canvas.sel = None
        self.canvas.undo_stack.clear()
        self.canvas.redo_stack.clear()
        self.canvas._fit()
        self.canvas.update()
        self.modified = True
        self.update_title()

    def manage_layers(self):
        self.canvas.commit_text()
        self.canvas.commit_selection()
        self.layers[self.active_layer]["image"] = self.canvas.image
        dialog = QDialog(self)
        dialog.setWindowTitle("Gemini Photo - Layers")
        dialog.setMinimumSize(370, 360)
        root = QVBoxLayout(dialog)
        root.addWidget(QLabel("Visible layers combine from bottom to top."))
        listing = QListWidget()
        root.addWidget(listing, 1)
        actions = QHBoxLayout()
        controls = {}
        for label in ("New", "Duplicate", "Delete", "Up", "Down"):
            controls[label] = QPushButton(label)
            actions.addWidget(controls[label])
        root.addLayout(actions)
        opacity_row = QHBoxLayout()
        opacity_row.addWidget(QLabel("Opacity"))
        opacity = QSlider(Qt.Horizontal)
        opacity.setRange(0, 100)
        opacity_row.addWidget(opacity, 1)
        root.addLayout(opacity_row)
        close = QDialogButtonBox(QDialogButtonBox.Close)
        close.rejected.connect(dialog.reject)
        root.addWidget(close)

        def refresh():
            listing.blockSignals(True)
            listing.clear()
            for index in reversed(range(len(self.layers))):
                layer = self.layers[index]
                item = QListWidgetItem(layer["name"])
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsEditable)
                item.setCheckState(Qt.Checked if layer["visible"] else Qt.Unchecked)
                item.setData(Qt.UserRole, index)
                listing.addItem(item)
            listing.setCurrentRow(len(self.layers) - 1 - self.active_layer)
            listing.blockSignals(False)
            opacity.blockSignals(True)
            opacity.setValue(round(self.layers[self.active_layer]["opacity"] * 100))
            opacity.blockSignals(False)

        def current_index():
            item = listing.currentItem()
            return item.data(Qt.UserRole) if item is not None else self.active_layer

        def current_changed(item):
            index = item.data(Qt.UserRole)
            self.layers[index]["name"] = item.text().strip() or "Layer"
            self.layers[index]["visible"] = item.checkState() == Qt.Checked
            if index != self.active_layer:
                self._activate_layer(index)
            else:
                self.canvas.update()

        def add_layer(duplicate=False):
            if len(self.layers) >= 20:
                return self._message("Gemini Photo", "A project can contain at most 20 layers.", "warning")
            source = self.canvas.image.copy()
            if not duplicate:
                source.fill(Qt.transparent)
            index = self.active_layer + 1
            self.layers.insert(index, {"name": f"Layer {len(self.layers) + 1}", "visible": True,
                                       "opacity": 1.0, "image": source})
            self._activate_layer(index)
            refresh()

        def delete_layer():
            if len(self.layers) <= 1:
                return self._message("Gemini Photo", "A project must keep at least one layer.", "warning")
            index = current_index()
            self.layers.pop(index)
            self.active_layer = min(index, len(self.layers) - 1)
            self.canvas.image = self.layers[self.active_layer]["image"]
            self.canvas._fit()
            self.modified = True
            self.update_title()
            refresh()

        def move_layer(offset):
            index = current_index()
            target = index + offset
            if not 0 <= target < len(self.layers):
                return
            self.layers[index], self.layers[target] = self.layers[target], self.layers[index]
            self.active_layer = target
            self.canvas.image = self.layers[target]["image"]
            self.canvas.update()
            self.modified = True
            self.update_title()
            refresh()

        def set_opacity(value):
            self.layers[self.active_layer]["opacity"] = value / 100
            self.modified = True
            self.update_title()
            self.canvas.update()

        def select_layer(*_):
            index = current_index()
            if index != self.active_layer:
                self._activate_layer(index)
            opacity.blockSignals(True)
            opacity.setValue(round(self.layers[self.active_layer]["opacity"] * 100))
            opacity.blockSignals(False)

        listing.currentItemChanged.connect(select_layer)
        listing.itemChanged.connect(current_changed)
        controls["New"].clicked.connect(lambda: add_layer())
        controls["Duplicate"].clicked.connect(lambda: add_layer(True))
        controls["Delete"].clicked.connect(delete_layer)
        controls["Up"].clicked.connect(lambda: move_layer(1))
        controls["Down"].clicked.connect(lambda: move_layer(-1))
        opacity.valueChanged.connect(set_opacity)
        refresh()
        dialog.exec()

    def open_layered(self):
        from .opendialog import open_dialog
        open_dialog(self.desktop, "Open Gemini Photo Project", {".gphoto"}, self.load, icon=gemini_photo_icon())

    def save_layered_as(self):
        folder = self.path.parent if self.path else None

        def saved(path):
            self.path = path if path.suffix.lower() == ".gphoto" else path.with_suffix(".gphoto")
            self.save()

        SaveAsDialog(self.desktop, self.path.name if self.path else "Photo.gphoto", folder, saved)

    def _project_data(self):
        self.canvas.commit_text()
        self.canvas.commit_selection()
        self.layers[self.active_layer]["image"] = self.canvas.image
        records = []
        for layer in self.layers:
            buffer = QBuffer()
            buffer.open(QIODevice.WriteOnly)
            if not layer["image"].save(buffer, "PNG"):
                raise ValueError("A layer could not be encoded.")
            records.append({"name": layer["name"], "visible": layer["visible"], "opacity": layer["opacity"],
                            "png": base64.b64encode(bytes(buffer.data())).decode("ascii")})
        return {"format": "Gemini Photo Layered", "version": 1, "active": self.active_layer, "layers": records}

    def _read_project(self, path):
        if path.stat().st_size > 20 * 1024 * 1024:
            raise ValueError("The layered project exceeds the 20 MB limit.")
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("This is not a valid Gemini Photo project.")
        records = data.get("layers")
        active = data.get("active")
        if (data.get("format") != "Gemini Photo Layered" or data.get("version") != 1
                or not isinstance(records, list) or not 1 <= len(records) <= 20
                or isinstance(active, bool) or not isinstance(active, int) or not 0 <= active < len(records)):
            raise ValueError("This is not a supported Gemini Photo layered project.")
        layers, dimensions, total_pixels = [], None, 0
        for record in records:
            if (not isinstance(record, dict) or not isinstance(record.get("name"), str)
                    or not 1 <= len(record["name"]) <= 128 or not isinstance(record.get("visible"), bool)
                    or isinstance(record.get("opacity"), bool)
                    or not isinstance(record.get("opacity"), (int, float))
                    or not 0 <= record["opacity"] <= 1 or not isinstance(record.get("png"), str)):
                raise ValueError("A layer has invalid metadata.")
            raw = base64.b64decode(record["png"], validate=True)
            buffer = QBuffer()
            buffer.setData(raw)
            buffer.open(QIODevice.ReadOnly)
            reader = QImageReader(buffer, b"PNG")
            size = reader.size()
            if size.isEmpty() or size.width() > 8192 or size.height() > 8192:
                raise ValueError("A layer has invalid image dimensions.")
            if dimensions is None:
                dimensions = size
            elif size != dimensions:
                raise ValueError("All layers must have matching dimensions.")
            total_pixels += size.width() * size.height()
            if total_pixels > 32_000_000:
                raise ValueError("The project contains too many pixels.")
            image = reader.read()
            if image.isNull():
                raise ValueError("A layer image is damaged.")
            layers.append({"name": record["name"], "visible": record["visible"],
                           "opacity": float(record["opacity"]), "image": image.convertToFormat(QImage.Format_ARGB32)})
        return layers, active

    def load(self, path):
        path = Path(path)
        if path.suffix.lower() != ".gphoto":
            super().load(path)
            if self.path == path and hasattr(self, "layers"):
                self.layers = [{"name": "Background", "visible": True, "opacity": 1.0,
                                "image": self.canvas.image.convertToFormat(QImage.Format_ARGB32)}]
                self.active_layer = 0
            return
        try:
            layers, active = self._read_project(path)
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
            return self._message("Gemini Photo", f"Cannot open {path.name}.\n{error}", "error")
        self.layers, self.active_layer = layers, active
        self.canvas.image = layers[active]["image"]
        self.canvas._fit()
        self.canvas.undo_stack.clear()
        self.canvas.redo_stack.clear()
        self.path, self.modified = path, False
        self.update_title()

    def save(self, then=None):
        if self.path is not None and self.path.suffix.lower() == ".gphoto":
            try:
                payload = json.dumps(self._project_data(), ensure_ascii=False)
                if len(payload.encode("utf-8")) > 20 * 1024 * 1024:
                    raise ValueError("The layered project exceeds the 20 MB limit.")
                self.path.write_text(payload, encoding="utf-8")
            except (OSError, UnicodeError, ValueError) as error:
                return self._message("Gemini Photo", f"Cannot save {self.path.name}.\n{error}", "error")
            self.modified = False
            self.update_title()
            if callable(then):
                then()
            return
        if self.path is None:
            return self.save_as(then)
        try:
            self.canvas.commit_text()
            self.canvas.commit_selection()
            image = self.flattened_image()
            image_format = {".jpg": "JPG", ".jpeg": "JPG", ".png": "PNG", ".gif": "GIF"}.get(
                self.path.suffix.lower(), "BMP")
            if image_format == "GIF":
                image = image.convertToFormat(QImage.Format_Indexed8)
            if not image.save(str(self.path), image_format):
                raise OSError(f"Cannot save {self.path.name} in that image format.")
        except (OSError, ValueError) as error:
            return self._message("Gemini Photo", str(error), "error")
        self.modified = False
        self.update_title()
        if callable(then):
            then()

    def new(self):
        super().new()
        self.layers = [{"name": "Background", "visible": True, "opacity": 1.0,
                        "image": self.canvas.image.convertToFormat(QImage.Format_ARGB32)}]
        self.active_layer = 0

    def resize_image(self, size):
        self.layers[self.active_layer]["image"] = self.canvas.image
        resized = []
        for layer in self.layers:
            image = QImage(size, QImage.Format_ARGB32)
            image.fill(Qt.transparent)
            painter = QPainter(image)
            painter.drawImage(0, 0, layer["image"])
            painter.end()
            resized.append({**layer, "image": image})
        self.layers = resized
        self.canvas.image = self.layers[self.active_layer]["image"]
        self.canvas.sel = None
        self.canvas._fit()
        self.modified = True
        self.update_title()

    def print_(self):
        from ..explorer import vfs
        from ..printing import print_image
        self.canvas.commit_text()
        self.canvas.commit_selection()
        temp = vfs.DRIVE_C / "WINDOWS" / "Temp"
        temp.mkdir(parents=True, exist_ok=True)
        path = temp / (Path(self.name()).stem + ".png")
        if not self.flattened_image().save(str(path), "PNG"):
            return self._message("Gemini Photo", "Could not render the layered image for printing.", "error")
        print_image(self.desktop, path)

    def crop_to_selection(self):
        self.canvas.commit_text()
        selection = self.canvas.selection_rect()
        if selection is None:
            return self._message("Gemini Photo", "Select an area of the picture first.", "info")
        self.canvas.commit_selection()
        selection = selection.intersected(self.canvas.image.rect())
        if selection.isEmpty():
            return self._message("Gemini Photo", "The selection is outside the picture.", "warning")
        self.layers[self.active_layer]["image"] = self.canvas.image
        for layer in self.layers:
            layer["image"] = layer["image"].copy(selection)
        self.canvas.image = self.layers[self.active_layer]["image"]
        self.canvas._fit()
        self.modified = True
        self.update_title()

    def grayscale(self):
        self.canvas.commit_text()
        kind, image = self._target()
        result = image.convertToFormat(QImage.Format_Grayscale8).convertToFormat(QImage.Format_RGB32)
        self._apply(kind, result)

    def adjust_brightness(self, amount):
        self.canvas.commit_text()
        kind, image = self._target()
        result = image.convertToFormat(QImage.Format_RGB32).copy()
        painter = QPainter(result)
        color = Qt.white if amount > 0 else Qt.black
        painter.setOpacity(min(1.0, abs(amount) / 255))
        painter.fillRect(result.rect(), color)
        painter.end()
        self._apply(kind, result)


def open_gemini_photo(desktop, path=None):
    body = GeminiPhoto(desktop, path)
    window = XPWindow(desktop, f"{body.name()} - Gemini Photo", body, gemini_photo_icon(), (760, 600))
    body.frame = window
    desktop.open_window(window)
    return window
