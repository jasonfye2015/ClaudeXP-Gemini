"""Sprite and map tools for Copilot Python Studio: a sprite-sheet slicer with an animation previewer, a tilemap
editor and a pixel-art editor. Everything is saved under <Python Programs>\\Assets so programs can load it."""
from pathlib import Path

from PySide6.QtCore import QPoint, QRect, QSize, QTimer, Qt, Signal
from PySide6.QtGui import QColor, QImage, QImageReader, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (QButtonGroup, QCheckBox, QColorDialog, QComboBox, QGridLayout, QHBoxLayout, QLabel,
                               QLineEdit, QListWidget, QListWidgetItem, QPushButton, QScrollArea, QSpinBox,
                               QSplitter, QTabWidget, QToolButton, QVBoxLayout, QWidget)

PALETTE = ["#000000", "#1D2B53", "#7E2553", "#008751", "#AB5236", "#5F574F", "#C2C3C7", "#FFF1E8",
           "#FF004D", "#FFA300", "#FFEC27", "#00E436", "#29ADFF", "#83769C", "#FF77A8", "#FFCCAA",
           "#FFFFFF", "#3A2A1A", "#6B4423", "#C08A4E", "#2E6F40", "#9BD770", "#1E3A8A", "#7DD3FC"]
IMAGE_SUFFIXES = {".png", ".gif", ".bmp", ".jpg", ".jpeg"}


def assets_root():
    from .assets import assets_dir
    return assets_dir()


def sprites_dir():
    return assets_root() / "My Sprites"


def maps_dir():
    return assets_root() / "Maps"


# ---- pure helpers (also used by the tests) ----------------------------------------------------------------------

def grid_size(width, height, fw, fh, margin=0, spacing=0):
    """(columns, rows) of frames of fw x fh in a sheet."""
    cols = max(0, (width - margin + spacing) // max(1, fw + spacing))
    rows = max(0, (height - margin + spacing) // max(1, fh + spacing))
    return cols, rows


def guess_grid(width, height):
    """A likely (tile size, spacing) for a sheet: tiles that divide the picture evenly, with or without a 1 px gap."""
    sizes = (16, 32, 8, 24, 18, 12, 48, 64)
    for size in sizes:
        if width % size == 0 and height % size == 0:
            return size, 0
    for size in sizes:
        if (width + 1) % (size + 1) == 0 and (height + 1) % (size + 1) == 0:
            return size, 1
    return 16, 0


def cut_frames(image, fw, fh, margin=0, spacing=0):
    cols, rows = grid_size(image.width(), image.height(), fw, fh, margin, spacing)
    return [image.copy(margin + c * (fw + spacing), margin + r * (fh + spacing), fw, fh)
            for r in range(rows) for c in range(cols)]


def flood(width, height, start, same, paint):
    """Fill the connected area around start. same(x, y) says a cell matches; paint(x, y) changes it."""
    seen, todo = set(), [start]
    while todo:
        x, y = todo.pop()
        if (x, y) in seen or not (0 <= x < width and 0 <= y < height) or not same(x, y):
            continue
        seen.add((x, y))
        paint(x, y)
        todo += [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]


def line_points(x0, y0, x1, y1):
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err, points = dx + dy, []
    while True:
        points.append((x0, y0))
        if (x0, y0) == (x1, y1):
            return points
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


FRAMES_HELPER = '''import pygame


def load_frames(path, frame_w, frame_h, margin=0, spacing=0, scale=1):
    """Cut a sprite sheet into a list of frames, left to right, top to bottom."""
    sheet = pygame.image.load(path).convert_alpha()
    frames = []
    for y in range(margin, sheet.get_height() - frame_h + 1, frame_h + spacing):
        for x in range(margin, sheet.get_width() - frame_w + 1, frame_w + spacing):
            frame = sheet.subsurface((x, y, frame_w, frame_h))
            if scale != 1:
                frame = pygame.transform.scale(frame, (frame_w * scale, frame_h * scale))
            frames.append(frame)
    return frames


class Animation:
    """Call update(dt_seconds) every frame, then screen.blit(anim.image, pos)."""
    def __init__(self, frames, fps=8, loop=True):
        self.frames, self.fps, self.loop = frames, fps, loop
        self.time = 0.0

    def update(self, dt):
        self.time += dt

    @property
    def image(self):
        index = int(self.time * self.fps)
        index = index % len(self.frames) if self.loop else min(index, len(self.frames) - 1)
        return self.frames[index]
'''


def frames_snippet(path, fw, fh, margin, spacing, indexes, fps, name="WALK"):
    lines = [FRAMES_HELPER, f'FRAMES = load_frames("{path}", {fw}, {fh}, {margin}, {spacing}, scale=3)']
    if indexes:
        lines.append(f"{name} = Animation([FRAMES[i] for i in {list(indexes)}], fps={fps})")
        lines.append(f"# in your game loop:  {name}.update(dt)   then   screen.blit({name}.image, (x, y))")
    return "\n".join(lines) + "\n"


MAP_HELPER = '''

def load_map(path):
    """A saved map as rows of tile numbers (-1 means empty)."""
    with open(path) as f:
        return [[int(v) for v in line.split(",")] for line in f.read().split()]


def draw_map(screen, grid, tiles, tile_size, camera=(0, 0)):
    for y, row in enumerate(grid):
        for x, number in enumerate(row):
            if number >= 0:
                screen.blit(tiles[number], (x * tile_size - camera[0], y * tile_size - camera[1]))
'''


def map_snippet(tileset, tile, margin, spacing, map_path, scale=3):
    return (FRAMES_HELPER + MAP_HELPER +
            f'\nTILE_SIZE = {tile * scale}\n'
            f'TILES = load_frames("{tileset}", {tile}, {tile}, {margin}, {spacing}, scale={scale})\n'
            f'GRID = load_map("{map_path}")\n'
            f"# in your game loop:  draw_map(screen, GRID, TILES, TILE_SIZE)\n")


# ---- a picture with a frame grid drawn over it ---------------------------------------------------------------------

class SheetView(QWidget):
    cell_clicked = Signal(int)                         # the frame number

    def __init__(self):
        super().__init__()
        self.image = QImage()
        self.zoom, self.fw, self.fh, self.margin, self.spacing = 2, 16, 16, 0, 0
        self.marks = {}                                # frame number -> text shown on it
        self.current = -1
        self.setCursor(Qt.PointingHandCursor)
        self._resize()

    def set_image(self, image):
        self.image = image
        self.marks, self.current = {}, -1
        self._resize()

    def set_grid(self, fw, fh, margin, spacing):
        self.fw, self.fh, self.margin, self.spacing = fw, fh, margin, spacing
        self.update()

    def set_zoom(self, zoom):
        self.zoom = zoom
        self._resize()

    def counts(self):
        return grid_size(self.image.width(), self.image.height(), self.fw, self.fh, self.margin, self.spacing)

    def cell_rect(self, index):
        cols, _rows = self.counts()
        c, r = index % max(1, cols), index // max(1, cols)
        return QRect(self.margin + c * (self.fw + self.spacing), self.margin + r * (self.fh + self.spacing),
                     self.fw, self.fh)

    def _resize(self):
        size = self.image.size() * self.zoom if not self.image.isNull() else QSize(200, 80)
        self.setFixedSize(size)
        self.update()

    def paintEvent(self, _event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor("#C8C8C8"))
        if self.image.isNull():
            p.drawText(self.rect(), Qt.AlignCenter, "Pick a picture")
            return
        p.drawImage(QRect(QPoint(0, 0), self.image.size() * self.zoom), self.image)
        cols, rows = self.counts()
        p.setPen(QPen(QColor(255, 0, 255, 150), 1))
        z = self.zoom
        for i in range(cols * rows):
            r = self.cell_rect(i)
            p.drawRect(r.x() * z, r.y() * z, r.width() * z - 1, r.height() * z - 1)
        for i, text in self.marks.items():
            if i < cols * rows:
                r = self.cell_rect(i)
                p.fillRect(r.x() * z, r.y() * z, r.width() * z, r.height() * z, QColor(255, 220, 0, 90))
                p.setPen(QColor("#000000"))
                p.drawText(r.x() * z + 2, r.y() * z + 12, text)
        if 0 <= self.current < cols * rows:
            r = self.cell_rect(self.current)
            p.setPen(QPen(QColor("#FF0000"), 2))
            p.drawRect(r.x() * z, r.y() * z, r.width() * z, r.height() * z)

    def mousePressEvent(self, event):
        cols, rows = self.counts()
        x, y = int(event.position().x()) // self.zoom, int(event.position().y()) // self.zoom
        for i in range(cols * rows):
            if self.cell_rect(i).contains(x, y):
                self.cell_clicked.emit(i)
                return


def scrolled(widget):
    area = QScrollArea()
    area.setWidget(widget)
    area.setWidgetResizable(False)
    return area


def spin(low, high, value, tip=""):
    box = QSpinBox()
    box.setRange(low, high)
    box.setValue(value)
    box.setToolTip(tip)
    return box


# ---- choosing a picture from the asset folders ----------------------------------------------------------------------

class Picker(QWidget):
    picked = Signal(str)

    def __init__(self, min_area=48 * 48):
        super().__init__()
        self.min_area, self.paths = min_area, []
        box = QVBoxLayout(self)
        box.setContentsMargins(0, 0, 0, 0)
        self.filter = QLineEdit()
        self.filter.setPlaceholderText("Find a picture (try: tilemap, sheet, character)")
        self.filter.textChanged.connect(self._fill)
        self.list = QListWidget()
        self.list.setMaximumHeight(110)
        self.list.itemActivated.connect(self._chosen)
        self.list.itemClicked.connect(self._chosen)
        box.addWidget(self.filter)
        box.addWidget(self.list)
        QTimer.singleShot(0, self.refresh)

    def refresh(self):
        root, found = assets_root(), []
        if root.is_dir():
            for f in root.rglob("*"):
                if f.suffix.lower() not in IMAGE_SUFFIXES:
                    continue
                size = QImageReader(str(f)).size()
                if "My Sprites" in f.parts or size.width() * size.height() >= self.min_area:
                    found.append(f)
        self.paths = sorted(found, key=lambda f: str(f).lower())
        self._fill()

    def _fill(self, *_):
        want = self.filter.text().strip().lower()
        self.list.clear()
        root = assets_root()
        for f in self.paths:
            name = f.relative_to(root).as_posix()
            if want in name.lower():
                item = QListWidgetItem(name)
                item.setData(Qt.UserRole, str(f))
                self.list.addItem(item)
                if self.list.count() >= 400:
                    break

    def _chosen(self, item):
        self.picked.emit(item.data(Qt.UserRole))


def relative_to_programs(path):
    from .app import projects_dir
    try:
        return Path(path).relative_to(projects_dir()).as_posix()
    except ValueError:
        return str(path).replace("\\", "/")


# ---- tab 1: sprite sheets and animation -----------------------------------------------------------------------

class SpriteTab(QWidget):
    def __init__(self, insert, note):
        super().__init__()
        self.insert, self.note = insert, note
        self.path, self.frames, self.sequence, self.step = "", [], [], 0
        outer = QHBoxLayout(self)
        left = QVBoxLayout()
        self.picker = Picker()
        self.picker.picked.connect(self.load)
        left.addWidget(self.picker)
        form = QGridLayout()
        self.fw, self.fh = spin(1, 512, 16, "Width of one frame"), spin(1, 512, 16, "Height of one frame")
        self.margin, self.spacing = spin(0, 64, 0, "Gap around the whole sheet"), spin(0, 64, 0, "Gap between frames")
        self.zoom = spin(1, 8, 2, "Zoom")
        for row, (label, box) in enumerate((("Frame width", self.fw), ("Frame height", self.fh),
                                            ("Sheet margin", self.margin), ("Gap between", self.spacing),
                                            ("Zoom", self.zoom))):
            form.addWidget(QLabel(label), row, 0)
            form.addWidget(box, row, 1)
            if box is not self.zoom:
                box.valueChanged.connect(self._grid)
        self.zoom.valueChanged.connect(lambda v: self.view.set_zoom(v))
        left.addLayout(form)
        self.info = QLabel("")
        left.addWidget(self.info)
        left.addStretch()
        outer.addLayout(left, 0)

        self.view = SheetView()
        self.view.cell_clicked.connect(self.clicked)
        outer.addWidget(scrolled(self.view), 1)

        right = QVBoxLayout()
        right.addWidget(QLabel("<b>Animation</b> (click frames in order)"))
        self.preview = QLabel()
        self.preview.setFixedSize(150, 150)
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setStyleSheet("QLabel { background: #E0E0E0; border: 1px solid #808080; }")
        right.addWidget(self.preview)
        self.order = QLabel("No frames picked")
        self.order.setWordWrap(True)
        right.addWidget(self.order)
        row = QHBoxLayout()
        row.addWidget(QLabel("Speed (fps)"))
        self.fps = spin(1, 30, 8)
        self.fps.valueChanged.connect(self._timer_speed)
        row.addWidget(self.fps)
        right.addLayout(row)
        for text, slot in (("Remove last", self.remove_last), ("Clear", self.clear_sequence),
                           ("Insert code", self.insert_code), ("Save frames as pictures", self.save_frames)):
            b = QPushButton(text)
            b.clicked.connect(slot)
            right.addWidget(b)
        right.addStretch()
        outer.addLayout(right, 0)
        self.timer = QTimer(self, interval=125)
        self.timer.timeout.connect(self._tick)

    def load(self, path):
        image = QImage(path)
        if image.isNull():
            self.note("That picture could not be opened.")
            return
        self.path = path
        size, gap = guess_grid(image.width(), image.height())
        for box, value in ((self.fw, size), (self.fh, size), (self.spacing, gap), (self.margin, 0)):
            box.blockSignals(True)
            box.setValue(value)
            box.blockSignals(False)
        self.view.set_image(image)
        self.clear_sequence()
        self._grid()
        self.note(f"Loaded {Path(path).name}. Set the frame size, then click frames to build an animation.")

    def _grid(self, *_):
        self.view.set_grid(self.fw.value(), self.fh.value(), self.margin.value(), self.spacing.value())
        cols, rows = self.view.counts()
        self.info.setText(f"{cols} x {rows} = {cols * rows} frames")
        self.frames = cut_frames(self.view.image, self.fw.value(), self.fh.value(), self.margin.value(),
                                 self.spacing.value()) if not self.view.image.isNull() else []
        self.sequence = [i for i in self.sequence if i < len(self.frames)]
        self._refresh()

    def clicked(self, index):
        self.view.current = index
        self.sequence.append(index)
        self._refresh()

    def remove_last(self):
        if self.sequence:
            self.sequence.pop()
            self._refresh()

    def clear_sequence(self):
        self.sequence = []
        self._refresh()

    def _refresh(self):
        marks = {}
        for n, i in enumerate(self.sequence, 1):
            marks[i] = (marks[i] + "," if i in marks else "") + str(n)
        self.view.marks = marks
        self.view.update()
        self.order.setText("Frames: " + ", ".join(map(str, self.sequence)) if self.sequence else "No frames picked")
        self.step = 0
        if self.sequence:
            self._timer_speed()
            self.timer.start()
            self._tick()
        else:
            self.timer.stop()
            self.preview.clear()

    def _timer_speed(self, *_):
        self.timer.setInterval(max(20, 1000 // self.fps.value()))

    def _tick(self):
        if not self.sequence or not self.frames:
            return
        index = self.sequence[self.step % len(self.sequence)]
        self.step += 1
        if index < len(self.frames):
            scale = max(1, min(150 // max(1, self.fw.value()), 150 // max(1, self.fh.value())))
            self.preview.setPixmap(QPixmap.fromImage(self.frames[index]).scaled(
                self.fw.value() * scale, self.fh.value() * scale, Qt.KeepAspectRatio, Qt.FastTransformation))

    def snippet(self):
        return frames_snippet(relative_to_programs(self.path), self.fw.value(), self.fh.value(), self.margin.value(),
                              self.spacing.value(), self.sequence, self.fps.value())

    def insert_code(self):
        if not self.path:
            self.note("Pick a sprite sheet first.")
            return
        self.insert(self.snippet())
        self.note("Code inserted: it cuts the sheet into FRAMES and builds your animation.")

    def save_frames(self):
        if not self.frames:
            self.note("Pick a sprite sheet first.")
            return
        indexes = self.sequence or range(len(self.frames))
        folder = sprites_dir() / Path(self.path).stem
        folder.mkdir(parents=True, exist_ok=True)
        for n, i in enumerate(indexes):
            self.frames[i].save(str(folder / f"frame_{n:02d}.png"))
        self.note(f"Saved {len(list(indexes))} pictures in Assets\\My Sprites\\{folder.name}.")

    def shutdown(self):
        self.timer.stop()


# ---- tab 2: tilemap editor ---------------------------------------------------------------------------------

class MapView(QWidget):
    changed = Signal()

    def __init__(self):
        super().__init__()
        self.grid = [[-1] * 20 for _ in range(12)]
        self.tiles, self.ts, self.zoom = [], 16, 2
        self.tile, self.tool, self.show_grid = 0, "paint", True
        self.undo, self._stroke = [], False
        self._pix = {}
        self._resize()

    def set_tiles(self, frames, ts):
        self.tiles, self.ts, self._pix = frames, ts, {}
        self._resize()

    def set_zoom(self, zoom):
        self.zoom = zoom
        self._resize()

    def size_cells(self):
        return len(self.grid[0]), len(self.grid)

    def resize_map(self, w, h):
        self.grid = [[(self.grid[y][x] if y < len(self.grid) and x < len(self.grid[0]) else -1) for x in range(w)]
                     for y in range(h)]
        self._resize()

    def _resize(self):
        w, h = self.size_cells()
        self.setFixedSize(w * self.ts * self.zoom, h * self.ts * self.zoom)
        self.update()

    def snapshot(self):
        self.undo.append([row[:] for row in self.grid])
        del self.undo[:-40]

    def undo_last(self):
        if self.undo:
            self.grid = self.undo.pop()
            self._resize()
            self.changed.emit()

    def clear(self):
        self.snapshot()
        self.grid = [[-1] * len(self.grid[0]) for _ in self.grid]
        self.update()
        self.changed.emit()

    def pixmap(self, number):
        if number not in self._pix and 0 <= number < len(self.tiles):
            self._pix[number] = QPixmap.fromImage(self.tiles[number]).scaled(
                self.ts * self.zoom, self.ts * self.zoom, Qt.IgnoreAspectRatio, Qt.FastTransformation)
        return self._pix.get(number)

    def set_zoom_cache(self, zoom):
        self._pix = {}

    def paintEvent(self, _event):
        p = QPainter(self)
        step = self.ts * self.zoom
        p.fillRect(self.rect(), QColor("#B8C4D8"))
        for y, row in enumerate(self.grid):
            for x, number in enumerate(row):
                pix = self.pixmap(number) if number >= 0 else None
                if pix is not None:
                    p.drawPixmap(x * step, y * step, pix)
        if self.show_grid:
            p.setPen(QColor(0, 0, 0, 60))
            for x in range(len(self.grid[0]) + 1):
                p.drawLine(x * step, 0, x * step, self.height())
            for y in range(len(self.grid) + 1):
                p.drawLine(0, y * step, self.width(), y * step)

    def _cell(self, event):
        step = self.ts * self.zoom
        return int(event.position().x()) // step, int(event.position().y()) // step

    def _apply(self, x, y, erase):
        w, h = self.size_cells()
        if not (0 <= x < w and 0 <= y < h):
            return
        value = -1 if erase or self.tool == "erase" else self.tile
        if self.tool == "fill" and not self._stroke:
            target = self.grid[y][x]
            if target != value:
                flood(w, h, (x, y), lambda a, b: self.grid[b][a] == target,
                      lambda a, b: self.grid[b].__setitem__(a, value))
        elif self.tool != "fill":
            self.grid[y][x] = value
        self.update()
        self.changed.emit()

    def mousePressEvent(self, event):
        self.snapshot()
        self._stroke = False
        x, y = self._cell(event)
        self._apply(x, y, event.button() == Qt.RightButton)
        self._stroke = True

    def mouseMoveEvent(self, event):
        if self._stroke and self.tool != "fill":
            x, y = self._cell(event)
            self._apply(x, y, bool(event.buttons() & Qt.RightButton))

    def mouseReleaseEvent(self, _event):
        self._stroke = False


class MapTab(QWidget):
    def __init__(self, insert, note):
        super().__init__()
        self.insert, self.note = insert, note
        self.path, self.tileset_image = "", QImage()
        outer = QHBoxLayout(self)
        split = QSplitter()
        outer.addWidget(split)
        left = QWidget()
        lbox = QVBoxLayout(left)
        self.picker = Picker()
        self.picker.picked.connect(self.load_tileset)
        lbox.addWidget(self.picker)
        row = QHBoxLayout()
        self.tile = spin(4, 128, 16, "Tile size in pixels")
        self.margin = spin(0, 32, 0, "Margin")
        self.spacing = spin(0, 32, 0, "Gap between tiles")
        for label, box in (("Tile", self.tile), ("Margin", self.margin), ("Gap", self.spacing)):
            row.addWidget(QLabel(label))
            row.addWidget(box)
            box.valueChanged.connect(self._tiles_changed)
        lbox.addLayout(row)
        self.sheet = SheetView()
        self.sheet.cell_clicked.connect(self.choose_tile)
        lbox.addWidget(scrolled(self.sheet), 1)
        self.chosen = QLabel("Tile: none")
        lbox.addWidget(self.chosen)
        split.addWidget(left)

        right = QWidget()
        rbox = QVBoxLayout(right)
        bar = QHBoxLayout()
        self.tools = QButtonGroup(self)
        for name, label in (("paint", "Paint"), ("erase", "Erase"), ("fill", "Fill")):
            b = QToolButton()
            b.setText(label)
            b.setCheckable(True)
            b.setChecked(name == "paint")
            b.clicked.connect(lambda _c=False, n=name: setattr(self.map, "tool", n))
            self.tools.addButton(b)
            bar.addWidget(b)
        self.map_w, self.map_h = spin(1, 200, 20, "Map width in tiles"), spin(1, 200, 12, "Map height in tiles")
        bar.addWidget(QLabel("Map"))
        bar.addWidget(self.map_w)
        bar.addWidget(QLabel("x"))
        bar.addWidget(self.map_h)
        size_button = QPushButton("Resize")
        size_button.clicked.connect(lambda: self.map.resize_map(self.map_w.value(), self.map_h.value()))
        bar.addWidget(size_button)
        self.zoom = spin(1, 6, 2, "Zoom")
        self.zoom.valueChanged.connect(self._zoom)
        bar.addWidget(QLabel("Zoom"))
        bar.addWidget(self.zoom)
        grid_box = QCheckBox("Grid")
        grid_box.setChecked(True)
        grid_box.toggled.connect(lambda on: (setattr(self.map, "show_grid", on), self.map.update()))
        bar.addWidget(grid_box)
        undo = QPushButton("Undo")
        undo.clicked.connect(lambda: self.map.undo_last())
        clear = QPushButton("Clear")
        clear.clicked.connect(lambda: self.map.clear())
        bar.addWidget(undo)
        bar.addWidget(clear)
        bar.addStretch()
        rbox.addLayout(bar)
        self.map = MapView()
        rbox.addWidget(scrolled(self.map), 1)
        files = QHBoxLayout()
        self.name = QLineEdit("level1")
        self.name.setMaximumWidth(140)
        files.addWidget(QLabel("Map name"))
        files.addWidget(self.name)
        for text, slot in (("Save map", self.save_map), ("Insert code", self.insert_code)):
            b = QPushButton(text)
            b.clicked.connect(slot)
            files.addWidget(b)
        self.saved = QComboBox()
        self.saved.setMinimumWidth(110)
        files.addWidget(self.saved)
        open_button = QPushButton("Open")
        open_button.clicked.connect(self.open_map)
        files.addWidget(open_button)
        files.addStretch()
        rbox.addLayout(files)
        split.addWidget(right)
        split.setStretchFactor(1, 1)
        self.refresh_saved()

    def load_tileset(self, path):
        image = QImage(path)
        if image.isNull():
            self.note("That picture could not be opened.")
            return
        self.path, self.tileset_image = path, image
        size, gap = guess_grid(image.width(), image.height())
        for box, value in ((self.tile, size), (self.spacing, gap), (self.margin, 0)):
            box.blockSignals(True)
            box.setValue(value)
            box.blockSignals(False)
        self.sheet.set_image(image)
        self._tiles_changed()
        self.choose_tile(0)
        self.note(f"Tileset {Path(path).name}: pick a tile on the left, paint on the map (right-click erases).")

    def _tiles_changed(self, *_):
        t = self.tile.value()
        self.sheet.set_grid(t, t, self.margin.value(), self.spacing.value())
        frames = cut_frames(self.tileset_image, t, t, self.margin.value(), self.spacing.value()) \
            if not self.tileset_image.isNull() else []
        self.map.set_tiles(frames, t)

    def _zoom(self, value):
        self.map.zoom, self.map._pix = value, {}
        self.map._resize()
        self.sheet.set_zoom(max(1, value))

    def choose_tile(self, index):
        self.map.tile = index
        self.sheet.current = index
        self.sheet.marks = {index: "*"}
        self.sheet.update()
        self.chosen.setText(f"Tile: {index}")

    def map_path(self):
        name = "".join(c for c in self.name.text().strip() if c.isalnum() or c in "-_ ") or "level1"
        return maps_dir() / f"{name}.csv"

    def save_map(self):
        path = self.map_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(",".join(str(v) for v in row) for row in self.map.grid) + "\n", encoding="utf-8")
        meta = {"tileset": relative_to_programs(self.path), "tile": self.tile.value(),
                "margin": self.margin.value(), "spacing": self.spacing.value()}
        import json
        path.with_suffix(".json").write_text(json.dumps(meta), encoding="utf-8")
        self.refresh_saved(path.name)
        self.note(f"Saved Assets\\Maps\\{path.name}")

    def refresh_saved(self, select=None):
        self.saved.clear()
        if maps_dir().is_dir():
            self.saved.addItems(sorted(p.name for p in maps_dir().glob("*.csv")))
        if select:
            self.saved.setCurrentText(select)

    def open_map(self):
        import json
        name = self.saved.currentText()
        if not name:
            return
        path = maps_dir() / name
        rows = [[int(v) for v in line.split(",")] for line in path.read_text(encoding="utf-8").split()]
        meta_file = path.with_suffix(".json")
        if meta_file.exists():
            try:
                meta = json.loads(meta_file.read_text(encoding="utf-8"))
                from .app import projects_dir
                tileset = projects_dir() / meta["tileset"]
                if tileset.exists():
                    self.load_tileset(str(tileset))
                    for box, key in ((self.tile, "tile"), (self.margin, "margin"), (self.spacing, "spacing")):
                        box.setValue(int(meta.get(key, box.value())))
            except (ValueError, KeyError, OSError):
                pass
        self.map.snapshot()
        self.map.grid = rows
        self.map._resize()
        self.map_w.setValue(len(rows[0]))
        self.map_h.setValue(len(rows))
        self.name.setText(path.stem)
        self.note(f"Opened {name}")

    def insert_code(self):
        if not self.path:
            self.note("Pick a tileset first.")
            return
        self.save_map()
        self.insert(map_snippet(relative_to_programs(self.path), self.tile.value(), self.margin.value(),
                                self.spacing.value(), relative_to_programs(self.map_path())))
        self.note("Map saved and code inserted: it loads the tiles and draws your map.")

    def shutdown(self):
        pass


# ---- tab 3: pixel art -------------------------------------------------------------------------------------

class PixelView(QWidget):
    changed = Signal()

    def __init__(self):
        super().__init__()
        self.image = QImage(16, 16, QImage.Format_ARGB32)
        self.image.fill(Qt.transparent)
        self.color, self.tool, self.mirror, self.show_grid = QColor("#000000"), "pencil", False, True
        self.undo, self._last, self.scale = [], None, 16
        self.picked = None
        self.setMinimumSize(256, 256)
        self.setMouseTracking(False)

    def new(self, size):
        self.image = QImage(size, size, QImage.Format_ARGB32)
        self.image.fill(Qt.transparent)
        self.undo.clear()
        self.update()
        self.changed.emit()

    def set_image(self, image):
        self.image = image.convertToFormat(QImage.Format_ARGB32)
        self.undo.clear()
        self.update()
        self.changed.emit()

    def snapshot(self):
        self.undo.append(self.image.copy())
        del self.undo[:-40]

    def undo_last(self):
        if self.undo:
            self.image = self.undo.pop()
            self.update()
            self.changed.emit()

    def flip(self, horizontal):
        self.snapshot()
        self.image = self.image.mirrored(horizontal, not horizontal)
        self.update()
        self.changed.emit()

    def clear(self):
        self.snapshot()
        self.image.fill(Qt.transparent)
        self.update()
        self.changed.emit()

    def _geometry(self):
        s = max(1, min(self.width() // self.image.width(), self.height() // self.image.height()))
        return s, (self.width() - s * self.image.width()) // 2, (self.height() - s * self.image.height()) // 2

    def paintEvent(self, _event):
        s, ox, oy = self._geometry()
        p = QPainter(self)
        p.fillRect(self.rect(), QColor("#707070"))
        w, h = self.image.width(), self.image.height()
        for y in range(h):
            for x in range(w):
                shade = "#FFFFFF" if (x + y) % 2 == 0 else "#D8D8D8"
                p.fillRect(ox + x * s, oy + y * s, s, s, QColor(shade))
        p.drawImage(QRect(ox, oy, s * w, s * h), self.image)
        if self.show_grid and s >= 8:
            p.setPen(QColor(0, 0, 0, 50))
            for x in range(w + 1):
                p.drawLine(ox + x * s, oy, ox + x * s, oy + h * s)
            for y in range(h + 1):
                p.drawLine(ox, oy + y * s, ox + w * s, oy + y * s)

    def _pixel(self, event):
        s, ox, oy = self._geometry()
        return (int(event.position().x()) - ox) // s, (int(event.position().y()) - oy) // s

    def _inside(self, x, y):
        return 0 <= x < self.image.width() and 0 <= y < self.image.height()

    def _put(self, x, y, color):
        points = [(x, y)]
        if self.mirror:
            points.append((self.image.width() - 1 - x, y))
        for px, py in points:
            if self._inside(px, py):
                self.image.setPixelColor(px, py, color)

    def mousePressEvent(self, event):
        x, y = self._pixel(event)
        if not self._inside(x, y):
            return
        erase = event.button() == Qt.RightButton
        if self.tool == "picker":
            self.picked = self.image.pixelColor(x, y)
            self.changed.emit()
            return
        self.snapshot()
        if self.tool == "fill" and not erase:
            target = self.image.pixel(x, y)
            new = self.color.rgba()
            if target != new:
                flood(self.image.width(), self.image.height(), (x, y), lambda a, b: self.image.pixel(a, b) == target,
                      lambda a, b: self._put(a, b, self.color))
        else:
            self._last = (x, y)
            self._put(x, y, QColor(0, 0, 0, 0) if erase or self.tool == "eraser" else self.color)
        self.update()
        self.changed.emit()

    def mouseMoveEvent(self, event):
        if self._last is None or self.tool in ("fill", "picker"):
            return
        x, y = self._pixel(event)
        erase = bool(event.buttons() & Qt.RightButton) or self.tool == "eraser"
        for px, py in line_points(self._last[0], self._last[1], x, y):
            self._put(px, py, QColor(0, 0, 0, 0) if erase else self.color)
        self._last = (x, y)
        self.update()
        self.changed.emit()

    def mouseReleaseEvent(self, _event):
        self._last = None


class PixelTab(QWidget):
    def __init__(self, insert, note):
        super().__init__()
        self.insert, self.note = insert, note
        outer = QHBoxLayout(self)
        left = QVBoxLayout()
        self.canvas = PixelView()
        self.canvas.changed.connect(self._changed)
        top = QHBoxLayout()
        self.tools = QButtonGroup(self)
        for name, label in (("pencil", "Pencil"), ("eraser", "Eraser"), ("fill", "Fill"), ("picker", "Pick colour")):
            b = QToolButton()
            b.setText(label)
            b.setCheckable(True)
            b.setChecked(name == "pencil")
            b.clicked.connect(lambda _c=False, n=name: setattr(self.canvas, "tool", n))
            self.tools.addButton(b)
            top.addWidget(b)
        mirror = QCheckBox("Mirror")
        mirror.setToolTip("Draw both sides at once (good for characters)")
        mirror.toggled.connect(lambda on: setattr(self.canvas, "mirror", on))
        top.addWidget(mirror)
        for text, slot in (("Undo", lambda: self.canvas.undo_last()), ("Flip \u2194", lambda: self.canvas.flip(True)),
                           ("Flip \u2195", lambda: self.canvas.flip(False)), ("Clear", lambda: self.canvas.clear())):
            b = QPushButton(text)
            b.clicked.connect(slot)
            top.addWidget(b)
        top.addStretch()
        left.addLayout(top)
        left.addWidget(self.canvas, 1)
        outer.addLayout(left, 1)

        right = QVBoxLayout()
        size_row = QHBoxLayout()
        size_row.addWidget(QLabel("New"))
        self.size = QComboBox()
        self.size.addItems(["8", "16", "24", "32", "48", "64"])
        self.size.setCurrentText("16")
        size_row.addWidget(self.size)
        new = QPushButton("New picture")
        new.clicked.connect(lambda: self.canvas.new(int(self.size.currentText())))
        size_row.addWidget(new)
        right.addLayout(size_row)
        right.addWidget(QLabel("Colours (right-click draws transparent)"))
        palette = QGridLayout()
        palette.setSpacing(2)
        for i, hexcode in enumerate(PALETTE):
            b = QToolButton()
            b.setFixedSize(22, 22)
            b.setStyleSheet(f"QToolButton {{ background: {hexcode}; border: 1px solid #404040; }}")
            b.clicked.connect(lambda _c=False, h=hexcode: self.set_color(QColor(h)))
            palette.addWidget(b, i // 6, i % 6)
        right.addLayout(palette)
        self.swatch = QLabel()
        self.swatch.setFixedHeight(22)
        more = QPushButton("More colours...")
        more.clicked.connect(self.more_colours)
        right.addWidget(self.swatch)
        right.addWidget(more)
        right.addWidget(QLabel("Actual size / x4"))
        self.small = QLabel()
        self.big = QLabel()
        for lab in (self.small, self.big):
            lab.setAlignment(Qt.AlignCenter)
            lab.setStyleSheet("QLabel { background: #E8E8E8; border: 1px solid #808080; }")
        self.big.setFixedSize(132, 132)
        self.small.setFixedHeight(70)
        right.addWidget(self.small)
        right.addWidget(self.big)
        self.name = QLineEdit("hero")
        right.addWidget(QLabel("Name"))
        right.addWidget(self.name)
        for text, slot in (("Save picture", self.save), ("Insert load line", self.insert_line)):
            b = QPushButton(text)
            b.clicked.connect(slot)
            right.addWidget(b)
        self.saved = QComboBox()
        right.addWidget(self.saved)
        open_button = QPushButton("Open saved picture")
        open_button.clicked.connect(self.open_saved)
        right.addWidget(open_button)
        right.addStretch()
        outer.addLayout(right, 0)
        self.set_color(QColor(PALETTE[8]))
        self.refresh_saved()
        self._changed()

    def set_color(self, color):
        self.canvas.color = color
        self.swatch.setStyleSheet(f"QLabel {{ background: {color.name()}; border: 1px solid #202020; }}")

    def more_colours(self):
        color = QColorDialog.getColor(self.canvas.color, self, "Pick a colour")
        if color.isValid():
            self.set_color(color)

    def _changed(self):
        if self.canvas.picked is not None:
            picked, self.canvas.picked = self.canvas.picked, None
            if picked.alpha():
                self.set_color(picked)
        pix = QPixmap.fromImage(self.canvas.image)
        self.small.setPixmap(pix)
        self.big.setPixmap(pix.scaled(pix.size() * 4, Qt.KeepAspectRatio, Qt.FastTransformation)
                           if pix.width() * 4 <= 132 else pix.scaled(128, 128, Qt.KeepAspectRatio, Qt.FastTransformation))

    def file(self):
        name = "".join(c for c in self.name.text().strip() if c.isalnum() or c in "-_ ") or "hero"
        return sprites_dir() / f"{name}.png"

    def save(self):
        path = self.file()
        path.parent.mkdir(parents=True, exist_ok=True)
        self.canvas.image.save(str(path))
        self.refresh_saved(path.name)
        self.note(f"Saved Assets\\My Sprites\\{path.name}")

    def refresh_saved(self, select=None):
        self.saved.clear()
        if sprites_dir().is_dir():
            self.saved.addItems(sorted(p.name for p in sprites_dir().glob("*.png")))
        if select:
            self.saved.setCurrentText(select)

    def open_saved(self):
        name = self.saved.currentText()
        image = QImage(str(sprites_dir() / name)) if name else QImage()
        if image.isNull():
            return
        self.canvas.set_image(image)
        self.name.setText(Path(name).stem)
        self.note(f"Opened {name}")

    def insert_line(self):
        self.save()
        path = relative_to_programs(self.file())
        self.insert(f'{self.file().stem.replace(" ", "_")} = pygame.image.load("{path}").convert_alpha()\n')
        self.note("Saved and inserted a load line.")

    def shutdown(self):
        pass


class GameTools(QWidget):
    """The tool window: Sprite Sheets, Tile Maps and Pixel Art."""

    def __init__(self, insert):
        super().__init__()
        root = QVBoxLayout(self)
        root.setContentsMargins(4, 4, 4, 4)
        self.tabs = QTabWidget()
        root.addWidget(self.tabs, 1)
        self.message = QLabel("")
        self.message.setWordWrap(True)
        root.addWidget(self.message)
        self.sprites = SpriteTab(insert, self.message.setText)
        self.maps = MapTab(insert, self.message.setText)
        self.pixels = PixelTab(insert, self.message.setText)
        self.tabs.addTab(self.sprites, "Sprite Sheets && Animation")
        self.tabs.addTab(self.maps, "Tile Map Editor")
        self.tabs.addTab(self.pixels, "Pixel Art")

    def shutdown(self):
        self.sprites.shutdown()
