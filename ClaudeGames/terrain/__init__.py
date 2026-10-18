"""Claude Terrain Generator: a fractal landscape maker in the spirit of VistaPro and the early Terragen - more tech
demo than tool. A random heightmap (diamond-square, the roughness you choose) is lit by the sun, flooded to the water
level, capped with snow above the snow line and planted with forests, then drawn as a voxel landscape (one ray per
screen column, near to far, fog toward the horizon) from wherever the camera is. A little map shows where you're
standing. 'Save Image' puts the picture in E:\\Created Files\\Claude Terrain Generator (Local Storage)."""
import math
import random
import time

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QIcon, QImage, QPainter, QPen, QPixmap, QPolygonF
from PySide6.QtWidgets import (QComboBox, QFormLayout, QHBoxLayout, QLabel, QPushButton, QSlider, QVBoxLayout,
                               QWidget)
from shiboken6 import isValid

from claudecore import host

N = 257                                  # heightmap size (2^8 + 1)
W, H = 640, 400                          # the picture
TREES = {"Pine": ((34, 78, 40), 7.0), "Oak": ((58, 104, 44), 6.0), "Autumn": ((176, 92, 34), 6.0),
         "Palm": ((70, 130, 52), 5.0), "None": (None, 0.0)}
SKIES = {"Day": ((70, 120, 200), (200, 220, 240), (1.0, 1.0, 1.0)),
         "Sunset": ((60, 50, 110), (250, 150, 90), (1.05, 0.85, 0.7)),
         "Night": ((5, 8, 24), (30, 40, 70), (0.35, 0.4, 0.6))}


def terrain_icon():
    pm = QPixmap(32, 32)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.fillRect(QRectF(1, 1, 30, 30), QColor("#6A9ADA"))
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#6E6A60"))
    p.drawPolygon(QPolygonF([QPointF(1, 24), QPointF(12, 7), QPointF(19, 16), QPointF(24, 10), QPointF(31, 22),
                             QPointF(31, 31), QPointF(1, 31)]))
    p.setBrush(QColor("white"))
    p.drawPolygon(QPolygonF([QPointF(9, 11.5), QPointF(12, 7), QPointF(15, 11.5), QPointF(12, 10)]))
    p.drawPolygon(QPolygonF([QPointF(22, 13), QPointF(24, 10), QPointF(26.5, 13.5)]))
    p.setBrush(QColor("#2E6A2E"))
    p.drawRect(QRectF(1, 24, 30, 4))
    p.setBrush(QColor("#2A5CC8"))
    p.drawRect(QRectF(1, 28, 30, 3))
    p.end()
    return QIcon(pm)


# ---- the world --------------------------------------------------------------------------------------------------
def heightmap(seed, roughness):
    """Diamond-square, normalised to 0..1, with one smoothing pass (gentle erosion)."""
    rnd = random.Random(seed)
    h = [[0.0] * N for _ in range(N)]
    for x, y in ((0, 0), (0, N - 1), (N - 1, 0), (N - 1, N - 1)):
        h[y][x] = rnd.random()
    step, scale = N - 1, 1.0
    while step > 1:
        half = step // 2
        for y in range(half, N, step):
            for x in range(half, N, step):
                h[y][x] = (h[y - half][x - half] + h[y - half][x + half] + h[y + half][x - half] +
                           h[y + half][x + half]) / 4 + (rnd.random() - 0.5) * scale
        for y in range(0, N, half):
            for x in range((y + half) % step, N, step):
                total, n = 0.0, 0
                for dx, dy in ((-half, 0), (half, 0), (0, -half), (0, half)):
                    if 0 <= x + dx < N and 0 <= y + dy < N:
                        total += h[y + dy][x + dx]
                        n += 1
                h[y][x] = total / n + (rnd.random() - 0.5) * scale
        step, scale = half, scale * (0.35 + roughness * 0.4)
    smooth = [row[:] for row in h]
    for y in range(1, N - 1):
        for x in range(1, N - 1):
            smooth[y][x] = (h[y][x] * 4 + h[y - 1][x] + h[y + 1][x] + h[y][x - 1] + h[y][x + 1]) / 8
    lo = min(min(r) for r in smooth)
    hi = max(max(r) for r in smooth)
    return [[(v - lo) / (hi - lo or 1) for v in row] for row in smooth]


def colour_map(h, seed, water, snow, tree_kind, density, sky):
    """Per cell: (colour, height in world units) - lit, flooded, snowed and planted."""
    rnd = random.Random(seed * 7 + 1)
    jitter = [[rnd.random() for _ in range(N)] for _ in range(N)]
    forest = heightmap(seed + 99, 0.5)                    # where the woods grow (clumps, not salt and pepper)
    tree_rgb, tree_height = TREES[tree_kind]
    light = SKIES[sky][2]
    cells = []
    for y in range(N):
        row = []
        for x in range(N):
            v = h[y][x]
            nx = h[y][min(x + 1, N - 1)] - h[y][max(x - 1, 0)]
            ny = h[min(y + 1, N - 1)][x] - h[max(y - 1, 0)][x]
            shade = max(0.35, min(1.25, 1.0 + (-nx * 6 + ny * 4)))   # the sun is to the west-south-west
            j = jitter[y][x]
            lift = 0.0
            if v <= water:
                depth = (water - v) / max(water, 0.01)
                rgb = (int(40 - 30 * depth), int(110 - 60 * depth), int(170 - 50 * depth))
                v, shade = water, 1.0
            elif v < water + 0.025:
                rgb = (194, 178, 128)                                  # beach
            elif v > snow - 0.04 * j:
                rgb = (235, 238, 245)
            elif v > snow - 0.12:
                rgb = (118, 108, 96)                                   # bare rock below the snow
            else:
                t = (v - water) / max(snow - water, 0.01)
                rgb = (int(70 + 60 * t), int(120 - 10 * t), int(50 + 20 * t))
                palm_ok = tree_kind != "Palm" or v < water + 0.08
                if tree_rgb and palm_ok and forest[y][x] > 1 - density and j < 0.75 and v < snow - 0.14:
                    rgb = tuple(int(c * (0.8 + 0.4 * j)) for c in tree_rgb)
                    lift = tree_height * (0.7 + 0.6 * j)
            r, g, b = (min(255, int(c * shade * l)) for c, l in zip(rgb, light))
            row.append(((r, g, b), v, lift))
        cells.append(row)
    return cells


def render(cells, relief, cam, sky):
    """The voxel landscape: for each screen column, march out from the camera and draw what rises above what's
    already drawn, fading into the sky's horizon colour with distance."""
    top, horizon, _light = SKIES[sky]
    buf = bytearray(W * H * 4)
    for y in range(H):                                            # the sky
        t = min(1.0, y / (H * 0.55))
        c = bytes((int(top[2] + (horizon[2] - top[2]) * t), int(top[1] + (horizon[1] - top[1]) * t),
                   int(top[0] + (horizon[0] - top[0]) * t), 255))
        buf[y * W * 4:(y + 1) * W * 4] = c * W
    cx, cy, heading, alt, pitch = cam
    sin_h, cos_h = math.sin(heading), math.cos(heading)
    far, fov = 330.0, 0.9
    horizon_y = H * 0.35 + pitch
    cam_h = alt
    ybuf = [H] * W
    z, dz = 1.0, 0.6
    while z < far:
        fog = (z / far) ** 1.6
        # the row of the map z away, across the field of view
        lx, ly = cx + (sin_h - fov * cos_h) * z, cy - (cos_h + fov * sin_h) * z
        rx, ry = cx + (sin_h + fov * cos_h) * z, cy - (cos_h - fov * sin_h) * z
        sx, sy = (rx - lx) / W, (ry - ly) / W
        px, py = lx, ly
        scale = 240.0 / z
        for col in range(W):
            ix, iy = int(px), int(py)
            px += sx
            py += sy
            if not (0 <= ix < N and 0 <= iy < N):
                continue
            rgb, v, lift = cells[iy][ix]
            top_y = int((cam_h - v * relief - lift) * scale + horizon_y)
            if top_y < ybuf[col]:
                r = int(rgb[0] + (horizon[0] - rgb[0]) * fog)
                g = int(rgb[1] + (horizon[1] - rgb[1]) * fog)
                b = int(rgb[2] + (horizon[2] - rgb[2]) * fog)
                pixel = bytes((b, g, r, 255))
                for y in range(max(top_y, 0), ybuf[col]):
                    i = (y * W + col) * 4
                    buf[i:i + 4] = pixel
                ybuf[col] = max(top_y, 0)
        z += dz
        dz *= 1.012
    return QImage(bytes(buf), W, H, W * 4, QImage.Format_RGB32).copy()


# ---- the program --------------------------------------------------------------------------------------------------
class TerrainGenerator(QWidget):
    def __init__(self, desktop):
        super().__init__()
        self.desktop = desktop
        self.frame = None
        self.seed = random.randrange(1, 99999)
        self.heights = self.cells = None
        self.picture = None
        lay = QHBoxLayout(self)
        lay.setContentsMargins(6, 6, 6, 6)
        panel = QWidget()
        panel.setFixedWidth(230)
        form = QFormLayout(panel)
        form.setContentsMargins(0, 0, 0, 0)
        self.sliders = {}
        for key, label, lo, hi, start in (("rough", "Roughness", 0, 100, 55), ("relief", "Mountain height", 20, 200, 110),
                                          ("water", "Water level", 0, 60, 28), ("snow", "Snow line", 40, 101, 78),
                                          ("density", "Tree density", 0, 100, 45), ("heading", "Camera heading", -180, 180, 0),
                                          ("alt", "Camera altitude", 40, 260, 140), ("pitch", "Camera pitch", -80, 120, 30)):
            s = QSlider(Qt.Horizontal)
            s.setRange(lo, hi)
            s.setValue(start)
            s.valueChanged.connect(lambda _v, k=key: self._changed(k))
            form.addRow(label, s)
            self.sliders[key] = s
        self.trees = QComboBox()
        self.trees.addItems(list(TREES))
        self.trees.currentIndexChanged.connect(lambda _i: self._changed("trees"))
        form.addRow("Tree type", self.trees)
        self.sky = QComboBox()
        self.sky.addItems(list(SKIES))
        self.sky.currentIndexChanged.connect(lambda _i: self._changed("sky"))
        form.addRow("Sky", self.sky)
        self.map = QLabel()
        self.map.setFixedSize(160, 160)
        self.map.setStyleSheet("border: 1px solid #808080; background: black;")
        form.addRow(self.map)
        new = QPushButton("New Landscape")
        new.clicked.connect(self.new_landscape)
        save = QPushButton("Save Image...")
        save.clicked.connect(self.save)
        form.addRow(new)
        form.addRow(save)
        self.status = QLabel()
        self.status.setWordWrap(True)
        self.status.setStyleSheet("color: #404040;")
        form.addRow(self.status)
        lay.addWidget(panel)
        self.view = QLabel()
        self.view.setFixedSize(W, H)
        self.view.setStyleSheet("background: black; border: 2px inset #808080;")
        lay.addWidget(self.view, 0, Qt.AlignTop)
        self.timer = QTimer(self, singleShot=True, interval=350, timeout=self.redraw)
        self.dirty = {"map"}
        QTimer.singleShot(50, self.redraw)

    def _changed(self, key):
        if key == "rough":
            self.dirty.add("map")
        elif key in ("water", "snow", "density", "trees", "sky"):
            self.dirty.add("colours")
        self.timer.start()

    def new_landscape(self):
        self.seed = random.randrange(1, 99999)
        self.dirty.add("map")
        self.redraw()

    def redraw(self):
        self.setCursor(Qt.WaitCursor)
        self.status.setText("Generating...")
        self.status.repaint()
        started = time.time()
        v = {k: s.value() for k, s in self.sliders.items()}
        if "map" in self.dirty or self.heights is None:
            self.heights = heightmap(self.seed, v["rough"] / 100)
            self.dirty.add("colours")
        if "colours" in self.dirty or self.cells is None:
            self.cells = colour_map(self.heights, self.seed, v["water"] / 100, v["snow"] / 100,
                                    self.trees.currentText(), v["density"] / 100 * 0.6, self.sky.currentText())
        self.dirty.clear()
        heading = math.radians(v["heading"])
        cx = N / 2 - math.sin(heading) * N * 0.45
        cy = N / 2 + math.cos(heading) * N * 0.45
        cam = (cx, cy, heading, v["alt"], v["pitch"])
        self.picture = render(self.cells, v["relief"], cam, self.sky.currentText())
        self.view.setPixmap(QPixmap.fromImage(self.picture))
        self._draw_map(cx, cy, heading)
        self.status.setText(f"Landscape #{self.seed} - drawn in {time.time() - started:.1f} s")
        self.unsetCursor()

    def _draw_map(self, cx, cy, heading):
        img = QImage(N, N, QImage.Format_RGB32)
        for y in range(N):
            for x in range(N):
                r, g, b = self.cells[y][x][0]
                img.setPixel(x, y, (r << 16) | (g << 8) | b)
        pm = QPixmap.fromImage(img.scaled(160, 160, Qt.IgnoreAspectRatio, Qt.SmoothTransformation))
        p = QPainter(pm)
        p.setRenderHint(QPainter.Antialiasing)
        k = 160 / N
        at = QPointF(cx * k, cy * k)
        tip = QPointF(at.x() + math.sin(heading) * 14, at.y() - math.cos(heading) * 14)
        p.setPen(QPen(QColor("#FF3030"), 2))
        p.drawLine(at, tip)
        p.setBrush(QColor("#FF3030"))
        p.drawEllipse(at, 3, 3)
        p.end()
        self.map.setPixmap(pm)

    def save(self):
        if self.picture is None:
            return
        folder = host.local_storage() / "Created Files" / "Claude Terrain Generator"
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"Landscape {self.seed} {time.strftime('%Y-%m-%d %H.%M.%S')}.png"
        if self.picture.save(str(path), "PNG"):
            rel = path.relative_to(host.local_storage())
            host.message(self.desktop, "Claude Terrain Generator", f"Saved as E:\\{rel}", "info")
        else:
            host.message(self.desktop, "Claude Terrain Generator", "The picture couldn't be saved.", "error")


_open = {}


def open_terrain(desktop):
    win = _open.get("win")
    if win is None or not isValid(win):
        body = TerrainGenerator(desktop)
        win = host.window(desktop, "Claude Terrain Generator", body, terrain_icon(), (W + 260, H + 20))
        body.frame = win
        _open["win"] = win
    desktop.open_window(win)
    return win
