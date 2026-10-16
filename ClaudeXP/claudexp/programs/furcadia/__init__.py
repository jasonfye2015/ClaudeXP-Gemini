"""Claudecadia (a Furcadia clone): the furry graphical chat world of 2001, simulated, with your AIM buddies as the other players.

Isometric maps (Willowmere Commons and 13 dreams to discover through portals), furres painted in code and recoloured
from each buddy's description, hopping, sitting, speech balloons, emotes and whispers. Art can be swapped for your
own files in assets/furcadia/ (see art.py). Needs the Internet connection, like the MUCK and IRC.
"""
import math
import random
import time
import traceback

from PySide6.QtCore import QPointF, QRect, QRectF, Qt, QTimer
from PySide6.QtGui import (QBrush, QColor, QCursor, QFont, QFontMetrics, QLinearGradient, QPainter, QPen, QPixmap,
                           QRadialGradient, QTextCharFormat, QTextCursor)
from PySide6.QtWidgets import (QCheckBox, QComboBox, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QMenuBar,
                               QPushButton, QTextBrowser, QTextEdit, QToolButton, QVBoxLayout, QWidget)
from shiboken6 import isValid

from ... import network, sound
from ...wm import XPWindow
from ..placeholder import open_placeholder
from . import art

HOST, PORT = "lightbringer.claudecadia.com", 6500
CHAT = {
    "say": ("#F0F0F0", False, False), "me": ("#FFE9A0", False, False), "emote": ("#9AE89A", False, True),
    "whisper": ("#8AD8FF", False, True), "system": ("#E8C860", False, False), "arrive": ("#A0A0B0", False, True),
    "dream": ("#D8A8FF", True, False), "look": ("#F0D0A0", False, False), "found": ("#FFE070", True, False), "note": ("#80C0FF", False, False),
}
MENU_STYLE = """
QMenuBar { background: #ECE9D8; font-family: Tahoma; font-size: 11px; }
QMenuBar::item { padding: 3px 7px; background: transparent; }
QMenuBar::item:selected { background: #316AC5; color: white; }
QMenu { background: white; border: 1px solid #ACA899; font-family: Tahoma; font-size: 11px; }
QMenu::item { padding: 4px 24px 4px 20px; }
QMenu::item:selected { background: #316AC5; color: white; }
"""
PANEL_STYLE = """
QWidget#panel { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #4A3A6A, stop:1 #2A1E44);
                border-top: 2px solid #8A72C0; }
QToolButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #7A62A8, stop:1 #4A3A78);
              color: #F4ECFF; border: 1px solid #1E1430; border-radius: 4px; font-family: Tahoma; font-size: 11px;
              font-weight: bold; padding: 2px 4px; }
QToolButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #9A82C8, stop:1 #5A4A90); }
QToolButton:pressed { background: #3A2A60; }
QTextBrowser { background: #120C1E; color: #E0E0E0; border: 2px inset #6A5A90; font-family: Tahoma;
               font-size: 11px; }
QLineEdit { background: #FFFDF4; color: black; border: 2px inset #6A5A90; font-family: Tahoma; font-size: 11px;
            padding: 1px 3px; }
"""
KEYS_TO_FACING = {Qt.Key_Up: art.NE, Qt.Key_Right: art.SE, Qt.Key_Down: art.SW, Qt.Key_Left: art.NW,
                  Qt.Key_9: art.NE, Qt.Key_3: art.SE, Qt.Key_1: art.SW, Qt.Key_7: art.NW,
                  Qt.Key_PageUp: art.NE, Qt.Key_PageDown: art.SE, Qt.Key_End: art.SW, Qt.Key_Home: art.NW}


def furc_icon():
    return art.icon()


def _centre(x, y):
    """A tile's middle in map pixels (before the camera)."""
    return (x - y) * art.TW / 2, (x + y) * art.TH / 2 + art.TH / 2


class MapView(QWidget):
    """The game screen: the current map, its objects and furres, balloons, and the connecting splash."""

    def __init__(self, client):
        super().__init__()
        self.client = client
        self.world = None
        self.tiles, self.objects, self.furres = art.Tiles(), art.Objects(), art.Furres()
        self.floor_cache = {}
        self.cam = None
        self.frame = 0
        self.hover = None
        self.banner = ("", 0.0)
        self.setMouseTracking(True)
        self.setMinimumSize(640, 340)
        self.setFocusPolicy(Qt.ClickFocus)
        self.fireflies = [(random.uniform(0, 1), random.uniform(0, 1), random.uniform(0, 6.3)) for _ in range(40)]
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animate)
        self.timer.start(40)

    def _animate(self):
        self.frame += 1
        if self.isVisible():
            self.update()

    # ---- the floor of a whole map, painted once ------------------------------------------------------------
    def _floor(self, m):
        if m.id not in self.floor_cache:
            ox = m.h * art.TW / 2
            pm = QPixmap(int((m.w + m.h) * art.TW / 2) + 2, int((m.w + m.h) * art.TH / 2) + 2)
            pm.fill(Qt.transparent)
            p = QPainter(pm)
            for y in range(m.h):
                for x in range(m.w):
                    cx, cy = _centre(x, y)
                    p.drawPixmap(int(ox + cx - art.TW / 2), int(cy - art.TH / 2),
                                 self.tiles.get(m.floor[y][x], (x * 7 + y * 13) % 3))
            p.end()
            self.floor_cache[m.id] = (pm, ox)
        return self.floor_cache[m.id]

    def _offset(self, now):
        """Screen = map pixels + offset, keeping the player in the middle."""
        me = self.world.me
        fx, fy, _b = me.position(now)
        cx, cy = _centre(fx, fy)
        return self.width() / 2 - cx, self.height() / 2 + 30 - cy

    def show_banner(self, text):
        self.banner = (text, time.monotonic() + 4.0)

    # ---- painting ------------------------------------------------------------------------------------------
    def paintEvent(self, _e):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor("#000000"))
        w = self.world
        if w is None or not w.logged_in:
            self._splash(p)
            p.end()
            return
        now = time.monotonic()
        m = w.here
        ox, oy = self._offset(now)
        floor, fox = self._floor(m)
        p.drawPixmap(int(ox - fox), int(oy), floor)
        self._water(p, m, ox, oy)
        p.setRenderHint(QPainter.Antialiasing)
        # objects and furres, back to front
        items = []
        for (x, y), name in m.obj.items():
            items.append((x + y, 0, x, y, name))
        people = w.everyone_in(m.id)
        for f in people:
            fx, fy, bounce = f.position(now)
            items.append((max(f.x + f.y, fx + fy) + 0.5, 1, fx, fy, (f, bounce)))
        items.sort(key=lambda it: (it[0], it[1]))
        frame = self.frame // 3
        boxes = []
        for _d, kind, x, y, thing in items:
            cx, cy = _centre(x, y)
            sx, sy = ox + cx, oy + cy
            if sx < -120 or sx > self.width() + 120 or sy < -40 or sy > self.height() + 160:
                continue
            if kind == 0:
                pm, anchor = self.objects.get(thing, frame, x * 3 + y)
                p.drawPixmap(QPointF(sx - anchor.x(), sy - anchor.y()), pm)
            else:
                f, bounce = thing
                lift = 7 if f.pose == "sit" and m.seat(f.x, f.y) and f.hop_from is None and \
                    m.obj.get((f.x, f.y)) in ("bench", "chair", "stool") else 0
                pm = self.furres.get(f.look, f.pose, f.facing)
                top = QPointF(sx - art.FW / 2, sy - art.FOOT - bounce - lift)
                p.drawPixmap(top, pm)
                boxes.append((QRectF(top.x() + 8, top.y() + 4, art.FW - 16, art.FOOT - 2), f))
        self.boxes = boxes
        if m.tint or m.particles:
            self._ambience(p, m, ox, oy)
        # names on hover, then balloons on top of everything
        if self.hover is not None:
            for r, f in boxes:
                if f is self.hover:
                    self._name_tag(p, r, f.name)
        for r, f in boxes:
            if f.balloon and f.balloon[1] > now:
                self._balloon(p, r, f.balloon[0], f.balloon[1] - now)
            elif f.balloon:
                f.balloon = None
        self._hud(p, m, now)
        p.end()

    def _water(self, p, m, ox, oy):
        p.setPen(QPen(QColor(255, 255, 255, 70), 1))
        t = self.frame
        for y in range(m.h):
            for x in range(m.w):
                if m.floor[y][x] in ("water", "deepwater"):
                    cx, cy = _centre(x, y)
                    sx, sy = ox + cx, oy + cy
                    if -40 < sx < self.width() + 40 and -20 < sy < self.height() + 20:
                        k = (t // 4 + x * 3 + y * 5) % 12
                        p.drawLine(QPointF(sx - 12 + k, sy - 4 + (k % 3)), QPointF(sx - 6 + k, sy - 4 + (k % 3)))
                        k2 = (t // 5 + x * 7 + y) % 14
                        p.drawLine(QPointF(sx + 2 - k2 * 0.6, sy + 5), QPointF(sx + 8 - k2 * 0.6, sy + 5))

    def _ambience(self, p, m, ox, oy):
        """Night, cave dark or underwater blue over the map, glowing lights, and drifting particles."""
        p.setPen(Qt.NoPen)
        if m.tint:
            p.fillRect(self.rect(), QColor(*m.tint))
            p.setCompositionMode(QPainter.CompositionMode_Plus)
            for (x, y), name in m.obj.items():
                if name not in art.LIGHTS:
                    continue
                cx, cy = _centre(x, y)
                sx, sy = ox + cx, oy + cy - 10
                r, (cr, cg, cb) = art.LIGHTS[name]
                if not (-r < sx < self.width() + r and -r < sy < self.height() + r):
                    continue
                r += math.sin(self.frame * 0.4 + x) * 4 if name in ("campfire", "torch", "fireplace") else 0
                g = QRadialGradient(QPointF(sx, sy), r)
                g.setColorAt(0, QColor(cr, cg, cb, 150))
                g.setColorAt(1, QColor(0, 0, 0, 0))
                p.setBrush(QBrush(g))
                p.drawEllipse(QPointF(sx, sy), r, r * 0.7)
            p.setCompositionMode(QPainter.CompositionMode_SourceOver)
        t = self.frame * 0.05
        kind = m.particles
        w, h = max(1, self.width()), max(1, self.height())
        for fx, fy, ph in self.fireflies:
            if kind == "fireflies":
                x = (fx * w + math.sin(t + ph) * 30) % w
                y = (fy * h + math.cos(t * 0.7 + ph) * 20) % h
                a = int(120 + 120 * math.sin(t * 3 + ph * 2))
                if a > 40:
                    p.setBrush(QColor(230, 255, 140, max(0, min(255, a))))
                    p.drawEllipse(QPointF(x, y), 1.8, 1.8)
            elif kind == "snow":
                x = (fx * w + math.sin(t * 0.8 + ph) * 18 + t * 8) % w
                y = (fy * h + t * (30 + ph * 6)) % h
                p.setBrush(QColor(255, 255, 255, 220))
                p.drawEllipse(QPointF(x, y), 1.6 + ph % 1.2, 1.6 + ph % 1.2)
            elif kind == "bubbles":
                x = (fx * w + math.sin(t * 1.5 + ph) * 8) % w
                y = h - (fy * h + t * (25 + ph * 5)) % h
                p.setPen(QPen(QColor(220, 240, 255, 160), 1))
                p.setBrush(QColor(255, 255, 255, 40))
                p.drawEllipse(QPointF(x, y), 2 + ph % 2.5, 2 + ph % 2.5)
                p.setPen(Qt.NoPen)
            elif kind == "stars":
                x, y = fx * w, fy * h * 0.45
                a = int(140 + 110 * math.sin(t * 2 + ph * 3))
                p.setBrush(QColor(255, 250, 220, max(0, min(255, a))))
                p.drawEllipse(QPointF(x, y), 1.3, 1.3)

    def _name_tag(self, p, r, name):
        p.setFont(QFont("Tahoma", 8, QFont.Bold))
        fm = QFontMetrics(p.font())
        w = fm.horizontalAdvance(name) + 10
        box = QRectF(r.center().x() - w / 2, r.bottom() + 4, w, 15)
        p.setPen(QPen(QColor("#1E1430"), 1))
        p.setBrush(QColor(40, 28, 70, 210))
        p.drawRoundedRect(box, 4, 4)
        p.setPen(QColor("#F4ECFF"))
        p.drawText(box, Qt.AlignCenter, name)

    def _balloon(self, p, r, text, left):
        p.setFont(QFont("Tahoma", 8))
        fm = QFontMetrics(p.font())
        bound = fm.boundingRect(QRect(0, 0, 170, 400), Qt.TextWordWrap, text[:180])
        w, h = bound.width() + 12, bound.height() + 8
        x = max(4, min(self.width() - w - 4, r.center().x() - w / 2))
        y = max(4, r.top() - h - 10)
        alpha = 255 if left > 1 else int(255 * left)
        p.setPen(QPen(QColor(30, 30, 30, alpha), 1))
        p.setBrush(QColor(255, 255, 250, int(alpha * 0.94)))
        p.drawRoundedRect(QRectF(x, y, w, h), 7, 7)
        tip = r.center().x()
        from PySide6.QtGui import QPolygonF
        p.drawPolygon(QPolygonF([QPointF(tip - 5, y + h - 1), QPointF(tip + 5, y + h - 1), QPointF(tip, y + h + 7)]))
        p.setPen(Qt.NoPen)
        p.drawRect(QRectF(tip - 4, y + h - 2, 8, 2))
        p.setPen(QColor(20, 20, 20, alpha))
        p.drawText(QRectF(x + 6, y + 4, w - 12, h - 8), Qt.TextWordWrap, text[:180])

    def _hud(self, p, m, now):
        text, until = self.banner
        if until > now:
            p.setFont(QFont("Georgia", 15, QFont.Bold))
            alpha = 255 if until - now > 1 else int(255 * (until - now))
            p.setPen(QColor(0, 0, 0, alpha))
            p.drawText(QRect(2, 14, self.width(), 30), Qt.AlignHCenter, text)
            p.setPen(QColor(255, 236, 170, alpha))
            p.drawText(QRect(0, 12, self.width(), 30), Qt.AlignHCenter, text)
        p.setFont(QFont("Tahoma", 8))
        p.setPen(QColor(0, 0, 0, 160))
        label = f"{m.name}  -  {len(self.world.people_in(m.id)) + 1} here"
        p.drawText(QRect(9, self.height() - 19, 400, 16), Qt.AlignLeft, label)
        p.setPen(QColor("#F4ECFF"))
        p.drawText(QRect(8, self.height() - 20, 400, 16), Qt.AlignLeft, label)

    def _splash(self, p):
        g = QLinearGradient(0, 0, 0, self.height())
        g.setColorAt(0, QColor("#2A1A5A"))
        g.setColorAt(1, QColor("#0A0618"))
        p.fillRect(self.rect(), QBrush(g))
        strip = 54                                   # room for the Enter... button
        pm = art.splash_pixmap(self.width(), self.height() - strip)
        if pm is not None:
            p.fillRect(self.rect(), QColor("#000000"))
            p.drawPixmap((self.width() - pm.width()) // 2, (self.height() - strip - pm.height()) // 2, pm)
        else:
            p.setRenderHint(QPainter.Antialiasing)
            rnd = random.Random(7)
            for _ in range(90):
                a = int(90 + 120 * abs(math.sin(self.frame * 0.03 + rnd.random() * 6)))
                p.setPen(QColor(255, 255, 255, a))
                p.drawPoint(rnd.randrange(max(1, self.width())), rnd.randrange(max(1, self.height())))
            p.setFont(QFont("Georgia", 40, QFont.Bold, True))
            r = QRect(0, self.height() // 2 - 90, self.width(), 60)
            p.setPen(QColor("#120830"))
            p.drawText(r.translated(3, 3), Qt.AlignCenter, "Claudecadia")
            p.setPen(QColor("#E8C8FF"))
            p.drawText(r, Qt.AlignCenter, "Claudecadia")
            p.setFont(QFont("Georgia", 11, QFont.Normal, True))
            p.setPen(QColor("#B8A0E0"))
            p.drawText(QRect(0, self.height() // 2 - 30, self.width(), 20), Qt.AlignCenter,
                       "The Dreaming awaits")
            look = art.Look("canine", "#E07A30", "#F8F0E0", "#3AA040", "#3050B0")
            for i, (lk, facing) in enumerate(((look, art.SE),
                                              (art.Look("feline", "#7A7A88", "#F2F0EA", "#5EA040"), art.SW))):
                p.drawPixmap(self.width() // 2 - 70 + i * 92, self.height() // 2 + 4, self.furres.get(lk, "stand",
                                                                                                    facing))
        self._enter_button(p, strip)

    def _enter_button(self, p, strip):
        """The 'Enter...' button under the title picture (or what's happening, once you've clicked it)."""
        p.setRenderHint(QPainter.Antialiasing)
        busy = self.client.connecting
        r = QRectF(self.width() / 2 - 80, self.height() - strip + 9, 160, 34)
        self.enter_rect = None if busy else r
        hot = not busy and self.underMouse() and r.contains(QPointF(self.mapFromGlobal(QCursor.pos())))
        g = QLinearGradient(r.topLeft(), r.bottomLeft())
        g.setColorAt(0, QColor("#B49CF0" if hot else "#9A82D8"))
        g.setColorAt(1, QColor("#4A3488" if hot else "#3A2870"))
        p.setPen(QPen(QColor("#E8DCFF"), 1.5))
        p.setBrush(QBrush(g))
        p.drawRoundedRect(r, 16, 16)
        p.setFont(QFont("Georgia", 13, QFont.Bold, True))
        p.setPen(QColor("#1A1030"))
        p.drawText(r.translated(1, 1), Qt.AlignCenter, "Connecting..." if busy else "Enter...")
        p.setPen(QColor("#F6F0FF"))
        p.drawText(r, Qt.AlignCenter, "Connecting..." if busy else "Enter...")
        p.setFont(QFont("Tahoma", 8))
        p.setPen(QColor("#B8A8D8"))
        status = self.client.status_text()
        p.drawText(QRectF(r.right() + 14, r.top(), self.width() - r.right() - 20, r.height()),
                   Qt.AlignVCenter | Qt.AlignLeft | Qt.TextWordWrap, status)

    # ---- the mouse -------------------------------------------------------------------------------------------
    def _furre_at(self, pos):
        for r, f in reversed(getattr(self, "boxes", [])):
            if r.contains(QPointF(pos)):
                return f
        return None

    def mouseMoveEvent(self, e):
        if self.world is None or not self.world.logged_in:
            return
        f = self._furre_at(e.position())
        if f is not self.hover:
            self.hover = f
            self.update()

    def mousePressEvent(self, e):
        w = self.world
        if w is None or not w.logged_in:
            r = getattr(self, "enter_rect", None)
            if e.button() == Qt.LeftButton and r is not None and r.contains(e.position()):
                sound.play("menu")
                self.client.connect_world()
            return
        f = self._furre_at(e.position())
        if f is not None and (e.button() == Qt.RightButton or e.modifiers() & Qt.ShiftModifier or f is not w.me):
            w.look_at(f)
            return
        if e.button() != Qt.LeftButton:
            return
        ox, oy = self._offset(time.monotonic())
        mx, my = e.position().x() - ox, e.position().y() - oy - art.TH / 2
        gx = (mx / (art.TW / 2) + my / (art.TH / 2)) / 2
        gy = (my / (art.TH / 2) - mx / (art.TW / 2)) / 2
        x, y = round(gx), round(gy)
        if w.here.signs.get((x, y)) and w.read_sign((x, y)):
            return
        if w.here.obj.get((x, y)) == "chest" and w.open_chest((x, y)):
            return
        w.walk_to(x, y)
        self.client.input.setFocus()

    def leaveEvent(self, _e):
        self.hover = None


class FurreEditor(QWidget):
    """Claudecadia's character editor: name, species, colours, description, with a live preview."""

    def __init__(self, data, on_done):
        super().__init__()
        self.on_done = on_done
        self.frame = None
        self.look = art.Look.from_json(data.get("look"))
        self.setStyleSheet("QWidget { font-family: Tahoma; font-size: 11px; }")
        grid = QGridLayout(self)
        grid.addWidget(QLabel("Furre name:"), 0, 0)
        self.name = QLineEdit(data.get("name", ""))
        self.name.setMaxLength(20)
        grid.addWidget(self.name, 0, 1, 1, 2)
        grid.addWidget(QLabel("Species:"), 1, 0)
        self.kind = QComboBox()
        for k in art.KIND_ORDER:
            self.kind.addItem(art.KINDS[k][0], k)
        self.kind.setCurrentIndex(max(0, art.KIND_ORDER.index(self.look.kind)))
        self.kind.currentIndexChanged.connect(self._changed)
        grid.addWidget(self.kind, 1, 1)
        self.wings = QCheckBox("Wings")
        self.wings.setChecked(self.look.wings)
        self.wings.toggled.connect(self._changed)
        grid.addWidget(self.wings, 1, 2)
        grid.addWidget(QLabel("Described as:"), 2, 0)
        self.species = QLineEdit(data.get("species", ""))
        self.species.setPlaceholderText("e.g. red fox")
        grid.addWidget(self.species, 2, 1, 1, 2)
        row = 3
        self.swatches = {}
        for part, label in (("fur", "Fur"), ("markings", "Markings"), ("eyes", "Eyes"), ("clothes", "Clothes")):
            grid.addWidget(QLabel(label + ":"), row, 0)
            line = QHBoxLayout()
            line.setSpacing(2)
            for c in art.PALETTE[part]:
                b = QToolButton()
                b.setFixedSize(18, 18)
                b.setToolTip("none" if not c else c)
                b.setStyleSheet(f"QToolButton {{ background: {c or '#FFFFFF'}; border: 1px solid #404040; }}"
                                if c else "QToolButton { background: white; border: 1px solid #404040; color: red; }")
                if not c:
                    b.setText("X")
                b.clicked.connect(lambda _=False, part=part, c=c: self._pick(part, c))
                line.addWidget(b)
            line.addStretch(1)
            grid.addLayout(line, row, 1, 1, 2)
            row += 1
        grid.addWidget(QLabel("Description:"), row, 0, Qt.AlignTop)
        self.desc = QTextEdit(data.get("desc", ""))
        self.desc.setFixedHeight(60)
        grid.addWidget(self.desc, row, 1, 1, 2)
        row += 1
        self.preview = QLabel()
        self.preview.setFixedHeight(80)
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setStyleSheet("background: #5E9A3A; border: 1px solid #405030;")
        grid.addWidget(self.preview, row, 0, 1, 3)
        row += 1
        buttons = QHBoxLayout()
        buttons.addStretch(1)
        ok, cancel = QPushButton("OK"), QPushButton("Cancel")
        ok.setDefault(True)
        ok.clicked.connect(self._save)
        cancel.clicked.connect(self._cancel)
        buttons.addWidget(ok)
        buttons.addWidget(cancel)
        grid.addLayout(buttons, row, 0, 1, 3)
        self.data = dict(data)
        self.furres = art.Furres()
        self._changed()

    def _pick(self, part, colour):
        setattr(self.look, part, colour)
        self._changed()

    def _changed(self, *_):
        self.look.kind = self.kind.currentData()
        self.look.wings = self.wings.isChecked()
        pm = QPixmap(5 * 56, 70)
        pm.fill(QColor("#5E9A3A"))
        p = QPainter(pm)
        for i, (pose, facing) in enumerate((("stand", art.SE), ("stand", art.SW), ("stand", art.NE),
                                            ("sit", art.SE), ("lie", art.SW))):
            p.drawPixmap(i * 56 + 4, 2, self.furres.get(self.look, pose, facing))
        p.end()
        self.preview.setPixmap(pm)

    def _save(self):
        name = self.name.text().strip() or "Guest"
        self.data.update(name=name, look=self.look.to_json(), desc=self.desc.toPlainText().strip(),
                         species=self.species.text().strip() or art.KINDS[self.look.kind][0].lower())
        self.on_done(self.data)
        self._close()

    def _cancel(self):
        self.on_done(None)
        self._close()

    def _close(self):
        if self.frame is not None and isValid(self.frame):
            self.frame.desktop.close_window(self.frame)


def default_player():
    """A first furre from the account's fursona (Setup), or a friendly fox."""
    from ... import fursonas, user
    name = user.muck_name() if user.linked() else user.user_name()
    pre = fursonas.chosen()
    if pre is not None:
        species = pre.get("fursona", "species") or "fox"
        text = " ".join(str(pre.get("fursona", k)) for k in ("colors", "markings", "description", "eyes"))
        look = art.look_from_text(species, text, pre.name)
        desc = pre.get("fursona", "description") or pre.get("summary")
        sp = species.lower().replace("anthropomorphic ", "")
        return {"name": pre.handle or name, "look": look.to_json(), "species": sp, "desc": desc}
    desc = fursonas.muck_desc() or ""
    return {"name": name or "Guest", "look": art.Look().to_json(), "species": "fox", "desc": desc}


class FurcClient(QWidget):
    def __init__(self, desktop):
        super().__init__()
        from .world import World
        self.desktop = desktop
        self.frame = None
        self.world = World(self)
        self.connected = self.connecting = False
        self.editor = None
        self.setStyleSheet(MENU_STYLE + PANEL_STYLE)
        self.world.line.connect(self.show_line)
        self.world.moved.connect(self._moved)
        self.world.discovered.connect(lambda _mid: sound.play("ding"))

        bar = QMenuBar()
        file_menu = bar.addMenu("&File")
        file_menu.addAction("&Connect", self.connect_world)
        file_menu.addAction("&Disconnect", self.disconnect_world)
        file_menu.addSeparator()
        file_menu.addAction("E&xit", lambda: self.frame.request_close() if self.frame else self.close())
        furre = bar.addMenu("F&urre")
        furre.addAction("&Edit Furre...", self.edit_furre)
        furre.addAction("&Look at Me", lambda: self.world.look_at(self.world.me) if self.world.me else None)
        furre.addSeparator()
        for label, pose in (("&Sit", "sit"), ("&Lie Down", "lie"), ("S&tand", "stand")):
            furre.addAction(label, lambda pose=pose: self.world.set_pose(pose))
        go = bar.addMenu("&Dreams")
        go.addAction("&Who's Online", lambda: self.world.who())
        go.addAction("Dreams &Discovered", lambda: self.world.list_dreams() if self.world.logged_in else None)
        go.addAction("Go to &Willowmere Commons", lambda: self.world.go_home() if self.world.logged_in else None)
        help_menu = bar.addMenu("&Help")
        help_menu.addAction("&Commands", lambda: self.world._command("help", ""))
        help_menu.addAction("&About Claudecadia", self._about)
        bar.triggered.connect(lambda _a: sound.play("menu"))

        self.view = MapView(self)
        self.view.world = self.world

        panel = QWidget()
        panel.setObjectName("panel")
        row = QHBoxLayout(panel)
        row.setContentsMargins(6, 6, 6, 6)
        row.setSpacing(8)
        picture = art.sidebar_pixmap()
        self.sidebar = Sidebar(self, picture) if picture is not None else None
        pad = QGridLayout()
        pad.setSpacing(2)
        for (r, c), facing, text in (((0, 0), art.NW, "↖"), ((0, 2), art.NE, "↗"),
                                     ((2, 0), art.SW, "↙"), ((2, 2), art.SE, "↘")):
            b = QToolButton()
            b.setText(text)
            b.setFixedSize(30, 26)
            b.setAutoRepeat(True)
            b.setAutoRepeatInterval(330)
            b.clicked.connect(lambda _=False, f=facing: self.world.step(f))
            pad.addWidget(b, r, c)
        turn = QToolButton()
        turn.setText("↻")
        turn.setToolTip("Turn")
        turn.setFixedSize(30, 26)
        turn.clicked.connect(lambda: self.world.turn())
        pad.addWidget(turn, 1, 1)
        if self.sidebar is None:                  # no sidebar picture: the plain buttons instead
            row.addLayout(pad)
        acts = QGridLayout()
        acts.setSpacing(3)
        for i, (label, slot) in enumerate((("Sit", lambda: self.world.set_pose("sit")),
                                           ("Lie", lambda: self.world.set_pose("lie")),
                                           ("Who", lambda: self.world.who()),
                                           ("Look", lambda: self.world.look_at(self.world.me) if self.world.me else None),
                                           ("Furre", self.edit_furre),
                                           ("Home", lambda: self.world.go_home() if self.world.logged_in else None))):
            b = QToolButton()
            b.setText(label)
            b.setFixedSize(52, 24)
            b.clicked.connect(slot)
            b.clicked.connect(lambda: self.input.setFocus())
            acts.addWidget(b, i // 2, i % 2)
        if self.sidebar is None:
            row.addLayout(acts)
        else:
            for i in range(pad.count()):
                pad.itemAt(i).widget().hide()
            for i in range(acts.count()):
                acts.itemAt(i).widget().hide()
        chat = QVBoxLayout()
        chat.setSpacing(3)
        self.output = QTextBrowser()
        self.output.setFocusPolicy(Qt.ClickFocus)
        self.output.document().setMaximumBlockCount(3000)
        self.output.setFixedHeight(104)
        self.input = QLineEdit()
        self.input.returnPressed.connect(self._send)
        self.input.installEventFilter(self)
        chat.addWidget(self.output)
        chat.addWidget(self.input)
        row.addLayout(chat, 1)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.setMenuBar(bar)
        body = QHBoxLayout()
        body.setSpacing(0)
        left = QVBoxLayout()
        left.setSpacing(0)
        left.addWidget(self.view, 1)
        left.addWidget(panel)
        body.addLayout(left, 1)
        if self.sidebar is not None:
            body.addWidget(self.sidebar)
        root.addLayout(body, 1)
        self.status = ""
        self.side_timer = QTimer(self)                 # keep the name plate and pose highlight current
        self.side_timer.timeout.connect(lambda: self.sidebar.update() if self.sidebar is not None else None)
        self.side_timer.start(400)

    # ---- keys: arrows and the keypad move, even while typing ------------------------------------------------
    def eventFilter(self, obj, e):
        from PySide6.QtCore import QEvent
        if obj is self.input and e.type() == QEvent.KeyPress:
            return self._key(e)
        return super().eventFilter(obj, e)

    def keyPressEvent(self, e):
        if not self._key(e):
            super().keyPressEvent(e)

    def _key(self, e):
        k = e.key()
        keypad = bool(e.modifiers() & Qt.KeypadModifier)
        typing = bool(self.input.text())
        if k in (Qt.Key_Up, Qt.Key_Down) or (k in (Qt.Key_Left, Qt.Key_Right) and not typing) or \
                (keypad and k in KEYS_TO_FACING):
            if k in KEYS_TO_FACING:
                self.world.step(KEYS_TO_FACING[k])
                return True
        if k == Qt.Key_F3 or keypad and k == Qt.Key_5:
            self.world.set_pose("sit")
            return True
        if k == Qt.Key_F4:
            self.world.set_pose("lie")
            return True
        if e.modifiers() & Qt.ControlModifier and k in (Qt.Key_L, Qt.Key_U, Qt.Key_G):
            {Qt.Key_L: lambda: self.world.set_pose("lie"), Qt.Key_U: self.world.use,
             Qt.Key_G: self.world.get}[k]()
            return True
        return False

    # ---- chat ---------------------------------------------------------------------------------------------
    def show_line(self, kind, text):
        colour, bold, italic = CHAT.get(kind, CHAT["system"])
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(colour))
        fmt.setFontWeight(QFont.Bold if bold else QFont.Normal)
        fmt.setFontItalic(italic)
        bar = self.output.verticalScrollBar()
        at_bottom = bar.value() >= bar.maximum() - 4
        cur = QTextCursor(self.output.document())
        cur.movePosition(QTextCursor.End)
        if not self.output.document().isEmpty():
            cur.insertBlock()
        if kind in ("say", "me") and ": " in text:
            name, _, rest = text.partition(": ")
            nf = QTextCharFormat(fmt)
            nf.setFontWeight(QFont.Bold)
            nf.setForeground(QColor("#FFD27A" if kind == "me" else "#C8B0FF"))
            cur.insertText(name + ": ", nf)
            cur.insertText(rest, fmt)
        else:
            cur.insertText(text, fmt)
        if at_bottom:
            bar.setValue(bar.maximum())
        if kind == "whisper" and "to you" in text:
            sound.play("notify")
        if kind in ("say", "emote", "whisper") and self.frame is not None and not self.desktop.is_active(self.frame):
            self.frame.flash()

    def note(self, text):
        self.show_line("note", text)

    def _send(self):
        text = self.input.text()
        self.input.clear()
        if not text.strip():
            if not self.connected:
                self.connect_world()           # Enter on the title screen goes in
            return
        if not self.connected:
            self.note("You aren't connected. (File > Connect)")
            return
        self.world.command(text)

    def _moved(self):
        self.view.show_banner(self.world.here.name)

    # ---- connecting -----------------------------------------------------------------------------------------
    def status_text(self):
        if self.connecting:
            return self.status or "Connecting..."
        return self.status or ""

    def start(self):
        self.note("Welcome to Claudecadia! Click Enter... (or press Enter) to connect to the Dreaming.")

    def connect_world(self):
        if self.connected or self.connecting:
            return
        self.connecting = True
        self.status = f"Connecting to {HOST}..."
        if not network.is_connected():
            self.status = "Waiting for your Internet connection..."
        network.connect(self.desktop, then=self._online)
        QTimer.singleShot(200, self._check_dial_cancelled)

    def _check_dial_cancelled(self):
        net = network.get(self.desktop)
        if self.connecting and not net.connected and net.connect_win is None and net.progress_win is None:
            self.connecting = False
            self.status = "Couldn't connect: no Internet connection. Click Enter... to try again."
        elif self.connecting and not net.connected:
            QTimer.singleShot(500, self._check_dial_cancelled)

    def _online(self):
        self.status = "Downloading dream files..."
        QTimer.singleShot(random.randint(900, 1800), self._logged_in)

    def _logged_in(self):
        if not self.connecting:
            return
        if not self.world.has_player():
            self.status = "Create your furre to begin."
            self.edit_furre(first=True)
            return
        self.connecting = False
        self.connected = True
        self.status = ""
        self.note(f"Connected to {HOST}:{PORT}.")
        self.world.connect_session()
        self.input.setFocus()

    def edit_furre(self, first=False):
        if self.editor is not None and isValid(self.editor):
            self.desktop.open_window(self.editor)
            return
        data = dict(self.world.player_data or default_player())

        def done(new):
            self.editor = None
            if new is None and first:
                new = data                    # cancelling the first time still gives you a furre
            if new is None:
                return
            self.world.make_player(new)
            if self.world.me is not None:
                from .art import Look
                self.world.me.name = new["name"]
                self.world.me.look = Look.from_json(new["look"])
                self.world.me.desc, self.world.me.species = new.get("desc", ""), new.get("species", "")
                self.world.save_player()
                self.note("Your furre has been updated.")
            if first:
                self._logged_in()

        body = FurreEditor(data, done)
        win = XPWindow(self.desktop, "Claudecadia - Edit Furre", body, furc_icon(), size=(470, 400))
        body.frame = win
        self.editor = win
        self.desktop.open_window(win)

    def disconnect_world(self):
        if self.connecting:
            self.connecting = False
            self.status = "Connection cancelled."
        if self.connected:
            self.world.disconnect_session()
            self.connected = False
            self.status = "Disconnected. Click Enter... to go back in."
            self.note("Disconnected from Claudecadia.")

    def network_lost(self):
        if self.connected:
            self.world.disconnect_session()
            self.connected = False
            self.status = "Connection lost: your modem hung up."
            self.note("Connection lost.")
        self.connecting = False

    def _about(self):
        self.note("Claudecadia for ClaudeXP - the furry graphical chat world, with your AIM buddies dreaming along. "
                  "Art is drawn by the program; your own can go in assets\\furcadia.")

    def shutdown(self):
        if self.connected:
            self.world.disconnect_session()
        self.connected = self.connecting = False
        self.view.timer.stop()
        self.side_timer.stop()

    def closeEvent(self, e):
        self.shutdown()
        e.accept()


# The sidebar picture's clickable spots, in the picture's own pixels (392 x 1024).
HOTSPOTS = {
    "help": ((148, 148, 104, 96), "Help!"),
    "name": ((38, 277, 327, 33), "Your furre"),
    "portrait": ((27, 345, 207, 206), "Your AIM buddy icon"),
    "tab_b": ((82, 592, 72, 58), "Who's online"),
    "tab_c": ((158, 592, 72, 58), "Dreams discovered"),
    "tab_d": ((234, 592, 72, 58), "Edit your furre"),
    "tab_e": ((312, 592, 74, 58), "Commands"),
    "stand": ((18, 660, 72, 160), "Stand"),
    "sit": ((92, 705, 70, 115), "Sit (F3)"),
    "lie": ((20, 840, 140, 80), "Lie down (Ctrl+L)"),
    "n7": ((170, 665, 85, 85), "Move up-left (7)"),
    "n9": ((282, 665, 85, 85), "Move up-right (9)"),
    "n1": ((170, 765, 85, 85), "Move down-left (1)"),
    "n3": ((282, 765, 85, 85), "Move down-right (3)"),
    "use": ((162, 902, 96, 96), "Use what's beside you (Ctrl+U)"),
    "get": ((288, 898, 90, 104), "Get / pick up (Ctrl+G)"),
    "exit": ((12, 958, 92, 54), "Exit to the title screen"),
}
SIDEBAR_W, SIDEBAR_H = 392, 1024


class Sidebar(QWidget):
    """Claudecadia's side panel: the sidebar picture (assets/furcadia/sidebar.jpg) with live parts painted on - your
    furre's name on the name plate and your AIM buddy icon in the portrait frame - and every button clickable."""

    def __init__(self, client, picture):
        super().__init__()
        self.client = client
        self.picture = picture
        self.scaled = None
        self.hover = self.pressed = None
        self.icon = None
        self.setMouseTracking(True)
        self.setMinimumHeight(420)
        self.repeat = QTimer(self)
        self.repeat.setInterval(330)
        self.repeat.timeout.connect(lambda: self._act(self.pressed) if self.pressed in MOVES else None)

    def sizeHint(self):
        from PySide6.QtCore import QSize
        return QSize(int(self.height() * SIDEBAR_W / SIDEBAR_H) or 210, 560)

    def resizeEvent(self, e):
        self.setFixedWidth(max(160, int(self.height() * SIDEBAR_W / SIDEBAR_H)))
        self.scaled = None
        super().resizeEvent(e)

    def _scale(self):
        return self.height() / SIDEBAR_H

    def _rect(self, key):
        (x, y, w, h), _tip = HOTSPOTS[key]
        s = self._scale()
        return QRectF(x * s, y * s, w * s, h * s)

    def _at(self, pos):
        for key in HOTSPOTS:
            if self._rect(key).contains(QPointF(pos)):
                return key
        return None

    def buddy_icon(self):
        if self.icon is None:
            pm = QPixmap()
            try:
                from ..aim import ensure_aim_path
                ensure_aim_path()
                from claudeaim import paths as aim_paths
                from claudeaim.storage import Settings
                path = aim_paths.resolve_icon(Settings()["buddy_icon"])
                if path:
                    pm = QPixmap(str(path))
            except Exception:
                pm = QPixmap()
            if pm.isNull():
                from ... import user
                pm = user.picture_pixmap()
            self.icon = pm
        return self.icon

    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        if self.scaled is None or self.scaled.height() != self.height():
            self.scaled = self.picture.scaled(self.width(), self.height(), Qt.IgnoreAspectRatio,
                                              Qt.SmoothTransformation)
        p.drawPixmap(0, 0, self.scaled)
        # the portrait: your AIM buddy icon
        r = self._rect("portrait")
        icon = self.buddy_icon()
        if icon is not None and not icon.isNull():
            fit = icon.scaled(int(r.width()), int(r.height()), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            p.fillRect(r, QColor("#FFFFFF"))
            p.drawPixmap(QPointF(r.center().x() - fit.width() / 2, r.center().y() - fit.height() / 2), fit)
        # the name plate
        world = self.client.world
        name = world.me.name if world.me is not None else (world.player_data or {}).get("name", "")
        if name:
            r = self._rect("name")
            font = QFont("Georgia", max(7, int(r.height() * 0.5)), QFont.Bold)
            p.setFont(font)
            p.setPen(QColor(255, 255, 255, 120))
            p.drawText(r.translated(1, 1), Qt.AlignCenter, name)
            p.setPen(QColor("#2A1450"))
            p.drawText(r, Qt.AlignCenter, name)
        # the pose you're in, and whatever the mouse is over
        p.setRenderHint(QPainter.Antialiasing)
        if world.me is not None and world.logged_in:
            pose = world.me.pose
            r = self._rect(pose if pose in ("stand", "sit", "lie") else "stand")
            p.setPen(QPen(QColor(255, 240, 160, 200), 2))
            p.setBrush(QColor(255, 240, 160, 40))
            p.drawRoundedRect(r.adjusted(2, 2, -2, -2), 8, 8)
        if self.hover and self.hover not in ("name", "portrait"):
            r = self._rect(self.hover)
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(0, 0, 0, 60) if self.pressed == self.hover else QColor(255, 255, 255, 45))
            p.drawRoundedRect(r.adjusted(3, 3, -3, -3), 10, 10)
        p.end()

    def event(self, e):
        from PySide6.QtCore import QEvent
        from PySide6.QtWidgets import QToolTip
        if e.type() == QEvent.ToolTip:
            key = self._at(e.pos())
            if key:
                QToolTip.showText(e.globalPos(), HOTSPOTS[key][1], self)
            else:
                QToolTip.hideText()
            return True
        return super().event(e)

    def mouseMoveEvent(self, e):
        key = self._at(e.position())
        if key != self.hover:
            self.hover = key
            self.setCursor(Qt.PointingHandCursor if key and key not in ("name",) else Qt.ArrowCursor)
            self.update()

    def leaveEvent(self, _e):
        self.hover = None
        self.update()

    def mousePressEvent(self, e):
        if e.button() != Qt.LeftButton:
            return
        self.pressed = self._at(e.position())
        if self.pressed:
            sound.play("menu") if self.pressed not in MOVES else None
            self._act(self.pressed)
            if self.pressed in MOVES:
                self.repeat.start()
        self.update()

    def mouseReleaseEvent(self, _e):
        self.pressed = None
        self.repeat.stop()
        self.update()

    def _act(self, key):
        c, w = self.client, self.client.world
        if key in MOVES:
            w.step(MOVES[key])
        elif key in ("stand", "sit", "lie"):
            if w.me is not None:
                w.me.path = []
                w.me.pose = key
        elif key == "help":
            w._command("help", "")
        elif key == "portrait":
            if w.me is not None:
                w.look_at(w.me)
        elif key == "tab_b":
            w.who()
        elif key == "tab_c":
            w.list_dreams() if w.logged_in else None
        elif key == "tab_d":
            c.edit_furre()
        elif key == "tab_e":
            w._command("help", "")
        elif key == "use":
            w.use()
        elif key == "get":
            w.get()
        elif key == "exit":
            c.disconnect_world()
        c.input.setFocus()
        self.update()


MOVES = {"n7": art.NW, "n9": art.NE, "n1": art.SW, "n3": art.SE}


_frame = None
_listening = False


def launch(desktop):
    global _frame, _listening
    if _frame is not None and isValid(_frame):
        desktop.open_window(_frame)
        return _frame
    try:
        client = FurcClient(desktop)
    except Exception:
        open_placeholder(desktop, "Claudecadia", furc_icon(),
                         "Claudecadia couldn't start.\n\n" + traceback.format_exc(limit=3), sound_event="error")
        return None
    if not _listening:
        network.on_disconnect(desktop, _network_lost)
        _listening = True
    _frame = XPWindow(desktop, "Claudecadia", client, furc_icon(), size=(900, 620))
    client.frame = _frame
    _frame.destroyed.connect(_forget)
    desktop.open_window(_frame)
    client.input.setFocus()
    client.start()
    return _frame


def _forget(*_):
    global _frame
    _frame = None


def _network_lost(quiet):
    if _frame is not None and isValid(_frame):
        _frame.content.network_lost()


def shutdown():
    if _frame is not None and isValid(_frame):
        _frame.content.shutdown()
        _frame.desktop.close_window(_frame)
