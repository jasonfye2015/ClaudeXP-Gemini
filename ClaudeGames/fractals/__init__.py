"""Claude Fractal Generator: an escape-time fractal explorer in the spirit of Fractint.

Mandelbrot, Julia (with the famous constants, or your own), Burning Ship, Tricorn, Multibrot (z^p + c) and Newton's
z^3 - 1, coloured with a choice of palettes (shifted to taste, smoothly shaded or in classic bands). Left-click zooms
in 2x where you click, right-click zooms out. The picture is worked out on a background thread and fills in as it
goes, so the window never freezes. 'Save Image' puts it in E:\\Created Files\\Claude Fractal Generator."""
import math
import threading
import time

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QIcon, QImage, QPainter, QPixmap
from PySide6.QtWidgets import (QCheckBox, QComboBox, QFormLayout, QHBoxLayout, QLabel, QPushButton, QSlider, QWidget)
from shiboken6 import isValid

from claudecore import host

W, H = 640, 440
TYPES = ["Mandelbrot", "Julia", "Burning Ship", "Tricorn", "Multibrot", "Newton (z³ - 1)"]
HOME = {"Mandelbrot": (-0.6, 0.0, 3.4), "Julia": (0.0, 0.0, 3.4), "Burning Ship": (-0.45, -0.5, 3.6),
        "Tricorn": (-0.3, 0.0, 4.0), "Multibrot": (0.0, 0.0, 3.4), "Newton (z³ - 1)": (0.0, 0.0, 3.4)}
JULIAS = {"Dendrite": (0.0, 1.0), "Douady Rabbit": (-0.123, 0.745), "San Marco": (-0.75, 0.0),
          "Siegel Disk": (-0.391, -0.587), "Spiral Galaxy": (-0.8, 0.156), "Lightning": (-0.7269, 0.1889),
          "Custom": None}
PALETTES = {
    "Fractint": [(0, 0, 0), (0, 0, 170), (0, 170, 0), (0, 170, 170), (170, 0, 0), (170, 0, 170), (170, 85, 0),
                 (170, 170, 170), (85, 85, 255), (85, 255, 85), (85, 255, 255), (255, 85, 85), (255, 85, 255),
                 (255, 255, 85), (255, 255, 255)],
    "Fire": [(0, 0, 0), (120, 0, 0), (230, 60, 0), (255, 170, 0), (255, 255, 120), (255, 255, 255)],
    "Ocean": [(0, 7, 40), (10, 50, 120), (30, 130, 190), (140, 220, 240), (255, 255, 255), (20, 70, 140)],
    "Rainbow": [(255, 0, 0), (255, 160, 0), (255, 255, 0), (0, 200, 0), (0, 120, 255), (100, 0, 200),
                (255, 0, 160)],
    "Electric": [(0, 0, 0), (40, 0, 90), (130, 0, 255), (0, 220, 255), (255, 255, 255), (255, 0, 200)],
    "Grayscale": [(0, 0, 0), (255, 255, 255)],
}
NEWTON_ROOTS = [complex(1, 0), complex(-0.5, math.sqrt(3) / 2), complex(-0.5, -math.sqrt(3) / 2)]
NEWTON_HUES = [(220, 60, 60), (60, 200, 80), (70, 110, 230)]


def fractal_icon():
    pm = QPixmap(32, 32)
    pm.fill(QColor("#000020"))
    img = QImage(32, 32, QImage.Format_RGB32)
    for y in range(32):
        for x in range(32):
            c = complex(-2.1 + x * 2.8 / 32, -1.4 + y * 2.8 / 32)
            z, n = 0j, 0
            while n < 24 and abs(z) < 2:
                z = z * z + c
                n += 1
            img.setPixel(x, y, 0x000000 if n == 24 else QColor.fromHsv((200 + n * 12) % 360, 220, 120 + n * 5).rgb())
    p = QPainter(pm)
    p.drawImage(0, 0, img)
    p.end()
    return QIcon(pm)


def palette(name, shift, size=512):
    stops = PALETTES[name]
    out = []
    for i in range(size):
        t = ((i / size) * len(stops) + shift / 100 * len(stops)) % len(stops)
        a, b = stops[int(t)], stops[(int(t) + 1) % len(stops)]
        f = t - int(t)
        out.append(bytes((int(a[2] + (b[2] - a[2]) * f), int(a[1] + (b[1] - a[1]) * f),
                          int(a[0] + (b[0] - a[0]) * f), 255)))
    return out


def draw_rows(job, buf, rows_done, cancelled):
    """Works out the picture a row at a time into buf (BGRA), counting finished rows; stops if cancelled()."""
    kind, cx, cy, width, iters, jc, power, colours, smooth = job
    scale = width / W
    top = cy - H / 2 * scale
    left = cx - W / 2 * scale
    ncol = len(colours)
    black = bytes((0, 0, 0, 255))
    log_power = math.log(power if kind == "Multibrot" else 2)
    bail = 256.0 if smooth else 4.0
    for py in range(H):
        if cancelled():
            return
        im = top + py * scale
        row = bytearray(W * 4)
        for px in range(W):
            re = left + px * scale
            if kind == "Newton (z³ - 1)":
                z = complex(re, im)
                n = 0
                colour = black
                while n < iters:
                    if z == 0:
                        break
                    z2 = z * z
                    z -= (z2 * z - 1) / (3 * z2)
                    n += 1
                    for k, root in enumerate(NEWTON_ROOTS):
                        if abs(z - root) < 1e-4:
                            r, g, b = NEWTON_HUES[k]
                            fade = max(0.25, 1 - n / 40)
                            colour = bytes((int(b * fade), int(g * fade), int(r * fade), 255))
                            n = iters + 1
                            break
                row[px * 4:px * 4 + 4] = colour
                continue
            if kind == "Julia":
                z, c = complex(re, im), jc
            else:
                z, c = 0j, complex(re, im)
                if kind == "Mandelbrot":                                  # skip the main cardioid and bulb
                    q = (re - 0.25) ** 2 + im * im
                    if q * (q + (re - 0.25)) <= 0.25 * im * im or (re + 1) ** 2 + im * im <= 0.0625:
                        row[px * 4:px * 4 + 4] = black
                        continue
            n = 0
            if kind in ("Mandelbrot", "Julia"):
                while n < iters and z.real * z.real + z.imag * z.imag <= bail:
                    z = z * z + c
                    n += 1
            elif kind == "Burning Ship":
                while n < iters and z.real * z.real + z.imag * z.imag <= bail:
                    z = complex(abs(z.real), abs(z.imag))
                    z = z * z + c
                    n += 1
            elif kind == "Tricorn":
                while n < iters and z.real * z.real + z.imag * z.imag <= bail:
                    z = z.conjugate()
                    z = z * z + c
                    n += 1
            else:
                while n < iters and z.real * z.real + z.imag * z.imag <= bail:
                    z = z ** power + c
                    n += 1
            if n >= iters:
                colour = black
            else:
                v = float(n)
                if smooth:
                    mod = abs(z)
                    if mod > 1:
                        v = n + 1 - math.log(math.log(mod)) / log_power
                colour = colours[int(v * 8) % ncol]
            row[px * 4:px * 4 + 4] = colour
        buf[py * W * 4:(py + 1) * W * 4] = row
        rows_done[0] = py + 1


class FractalGenerator(QWidget):
    def __init__(self, desktop):
        super().__init__()
        self.desktop = desktop
        self.frame = None
        self.view_at = dict(HOME)
        self.buf = bytearray(W * H * 4)
        self.rows = [0]
        self.generation = 0
        self.started = 0.0
        self.job = None
        lay = QHBoxLayout(self)
        lay.setContentsMargins(6, 6, 6, 6)
        panel = QWidget()
        panel.setFixedWidth(230)
        form = QFormLayout(panel)
        form.setContentsMargins(0, 0, 0, 0)
        self.kind = QComboBox()
        self.kind.addItems(TYPES)
        self.kind.currentIndexChanged.connect(lambda _i: self.start())
        form.addRow("Fractal", self.kind)
        self.iters = self._slider(form, "Max iterations", 20, 1000, 150)
        self.power = self._slider(form, "Multibrot power", 3, 8, 3)
        self.preset = QComboBox()
        self.preset.addItems(list(JULIAS))
        self.preset.setCurrentText("Douady Rabbit")
        self.preset.currentIndexChanged.connect(self._preset)
        form.addRow("Julia preset", self.preset)
        self.jre = self._slider(form, "Julia c (real)", -1500, 1500, -123)
        self.jim = self._slider(form, "Julia c (imag.)", -1500, 1500, 745)
        self.pal = QComboBox()
        self.pal.addItems(list(PALETTES))
        self.pal.currentIndexChanged.connect(lambda _i: self.start())
        form.addRow("Palette", self.pal)
        self.shift = self._slider(form, "Colour shift", 0, 100, 0)
        self.smooth = QCheckBox("Smooth shading")
        self.smooth.setChecked(True)
        self.smooth.toggled.connect(lambda _b: self.start())
        form.addRow(self.smooth)
        reset = QPushButton("Reset View")
        reset.clicked.connect(self.reset_view)
        save = QPushButton("Save Image...")
        save.clicked.connect(self.save)
        form.addRow(reset)
        form.addRow(save)
        hint = QLabel("Left-click: zoom in\nRight-click: zoom out")
        hint.setStyleSheet("color: #606060;")
        form.addRow(hint)
        self.status = QLabel()
        self.status.setWordWrap(True)
        self.status.setStyleSheet("color: #303030;")
        form.addRow(self.status)
        lay.addWidget(panel)
        self.view = QLabel()
        self.view.setFixedSize(W, H)
        self.view.setStyleSheet("background: black; border: 2px inset #808080;")
        self.view.setCursor(Qt.CrossCursor)
        self.view.mousePressEvent = self._clicked
        lay.addWidget(self.view, 0, Qt.AlignTop)
        self.debounce = QTimer(self, singleShot=True, interval=300, timeout=self.start)
        self.poll = QTimer(self, interval=120, timeout=self._update)
        QTimer.singleShot(50, self.start)

    def _slider(self, form, label, lo, hi, start):
        s = QSlider(Qt.Horizontal)
        s.setRange(lo, hi)
        s.setValue(start)
        s.valueChanged.connect(lambda _v: self.debounce.start())
        form.addRow(label, s)
        return s

    def _preset(self, _i):
        c = JULIAS[self.preset.currentText()]
        if c is not None:
            for s, v in ((self.jre, c[0]), (self.jim, c[1])):
                s.blockSignals(True)
                s.setValue(int(v * 1000))
                s.blockSignals(False)
        self.start()

    def reset_view(self):
        self.view_at[self.kind.currentText()] = HOME[self.kind.currentText()]
        self.start()

    def _clicked(self, event):
        kind = self.kind.currentText()
        cx, cy, width = self.view_at[kind]
        scale = width / W
        x, y = event.position().x(), event.position().y()
        nx, ny = cx + (x - W / 2) * scale, cy + (y - H / 2) * scale
        if event.button() == Qt.LeftButton:
            self.view_at[kind] = (nx, ny, width / 2)
        elif event.button() == Qt.RightButton:
            self.view_at[kind] = (cx, cy, min(width * 2, 8.0))
        self.start()

    def start(self):
        kind = self.kind.currentText()
        cx, cy, width = self.view_at[kind]
        self.job = (kind, cx, cy, width, self.iters.value(), complex(self.jre.value() / 1000, self.jim.value() / 1000),
                    self.power.value(), palette(self.pal.currentText(), self.shift.value()), self.smooth.isChecked())
        self.generation += 1
        mine = self.generation
        self.buf = bytearray(W * H * 4)
        self.rows = [0]
        self.started = time.time()
        threading.Thread(target=draw_rows, args=(self.job, self.buf, self.rows, lambda: self.generation != mine),
                         daemon=True).start()
        self.poll.start()

    def picture(self):
        return QImage(bytes(self.buf), W, H, W * 4, QImage.Format_RGB32).copy()

    def _update(self):
        if not isValid(self):
            return
        done = self.rows[0]
        self.view.setPixmap(QPixmap.fromImage(self.picture()))
        kind, cx, cy, width = self.job[:4]
        zoom = HOME[kind][2] / width
        where = f"Centre {cx:.10g}, {cy:.10g}i  -  zoom {zoom:,.0f}x"
        if done >= H:
            self.poll.stop()
            self.status.setText(f"{kind}\n{where}\nDrawn in {time.time() - self.started:.1f} s")
        else:
            self.status.setText(f"{kind}\n{where}\nDrawing... {done * 100 // H}%")

    def save(self):
        if self.rows[0] < H:
            host.message(self.desktop, "Claude Fractal Generator", "Let the picture finish drawing first.", "info")
            return
        folder = host.local_storage() / "Created Files" / "Claude Fractal Generator"
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"{self.job[0].split(' ')[0]} {time.strftime('%Y-%m-%d %H.%M.%S')}.png"
        if self.picture().save(str(path), "PNG"):
            host.message(self.desktop, "Claude Fractal Generator",
                         f"Saved as E:\\{path.relative_to(host.local_storage())}", "info")
        else:
            host.message(self.desktop, "Claude Fractal Generator", "The picture couldn't be saved.", "error")

    def closeEvent(self, event):
        self.generation += 1                                  # stops the drawing thread
        self.poll.stop()
        super().closeEvent(event)


_open = {}


def open_fractals(desktop):
    win = _open.get("win")
    if win is None or not isValid(win):
        body = FractalGenerator(desktop)
        win = host.window(desktop, "Claude Fractal Generator", body, fractal_icon(), (W + 260, H + 20))
        body.frame = win
        _open["win"] = win
    desktop.open_window(win)
    return win


def shutdown():
    win = _open.get("win")
    if win is not None and isValid(win):
        win.content.generation += 1
