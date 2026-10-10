"""Furry Proximity Locator: a world map with a pin dropped wherever a Fur Directory resident lives.

Pins come only from what the directory's own records say: a resident's hand-written "personal" -> "location" (see
The Fur Directory's README). The text is matched against a small offline gazetteer (furlocator_places.py); exact
"latitude" / "longitude" values in the record win over the text. Nobody's location is guessed: residents with no
Location aren't pinned, and a Location the gazetteer doesn't know is listed as "couldn't place". The map itself is
Natural Earth country outlines (public domain), stored locally, so nothing is downloaded.

Drag to pan, wheel to zoom, click a pin to select it, double-click (or Open Card) to open the resident's card."""
import json
import math
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QElapsedTimer, QPointF, QRectF, QSize, Qt, QTimer, Signal
from PySide6.QtGui import (QBrush, QColor, QFont, QIcon, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap,
                           QPolygonF, QTransform)
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QMenu, QPushButton, QToolTip,
                               QVBoxLayout, QWidget)
from shiboken6 import isValid

from ..wm import XPWindow
from . import furlocator_places

TITLE = "Furry Proximity Locator"
WORLD_FILE = Path(__file__).with_name("furlocator_world.json")
LAND = ("#CFE3B4", "#E3DDB0", "#D8E8C0", "#EAD9B0", "#C9DDB0")
MAX_K = 600.0                     # pixels per degree at full zoom
DROP_MS, STAGGER_MS = 650, 110


def locator_icon(size=32):
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    s = size / 32.0
    g = QLinearGradient(0, 3 * s, 0, 29 * s)
    g.setColorAt(0, QColor("#7FB8F0"))
    g.setColorAt(1, QColor("#2D6FC4"))
    p.setPen(QPen(QColor("#1F4E8C"), max(1.0, s)))
    p.setBrush(g)
    p.drawEllipse(QRectF(2 * s, 4 * s, 26 * s, 26 * s))
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#7CC25A"))
    p.drawEllipse(QRectF(7 * s, 10 * s, 9 * s, 8 * s))
    p.drawEllipse(QRectF(15 * s, 18 * s, 8 * s, 7 * s))
    path = QPainterPath()                                                   # the pin
    path.moveTo(23 * s, 17 * s)
    path.cubicTo(20 * s, 12 * s, 18 * s, 9 * s, 18 * s, 6.5 * s)
    path.arcTo(QRectF(18 * s, 0.5 * s, 10 * s, 10 * s), 180, -180)
    path.cubicTo(28 * s, 9 * s, 26 * s, 12 * s, 23 * s, 17 * s)
    p.setPen(QPen(QColor("#7A1B0E"), max(1.0, s)))
    p.setBrush(QColor("#E0442A"))
    p.drawPath(path)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("white"))
    p.drawEllipse(QRectF(21 * s, 3.5 * s, 4 * s, 4 * s))
    p.end()
    return QIcon(pm)


@dataclass
class Pin:
    resident: object
    lat: float
    lon: float
    place: str                  # the Location text as written in the record

    @property
    def name(self):
        return self.resident.name


def _number(value):
    try:
        return float(str(value).strip())
    except ValueError:
        return None


def locate(resident):
    """(Pin or None, text) for a resident: a pin when the record's location can be placed."""
    pers = (resident.record or {}).get("personal") or {}
    text = str(pers.get("location") or "").strip()
    lat, lon = _number(pers.get("latitude", "")), _number(pers.get("longitude", ""))
    if lat is not None and lon is not None and abs(lat) <= 90 and abs(lon) <= 180:
        return Pin(resident, lat, lon, text or f"{lat:g}, {lon:g}"), text
    hit = furlocator_places.find(text)
    if hit:
        return Pin(resident, hit[0], hit[1], text), text
    return None, text


def survey(residents):
    """(pins, couldn't place [(resident, text)], residents with no location at all)."""
    pins, unknown, none = [], [], []
    for r in residents:
        pin, text = locate(r)
        if pin:
            pins.append(pin)
        elif text:
            unknown.append((r, text))
        else:
            none.append(r)
    return pins, unknown, none


def _world():
    try:
        with open(WORLD_FILE, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return []
    out = []
    for country in data:
        polys = []
        for ring in country["r"]:
            polys.append(QPolygonF([QPointF(ring[i], ring[i + 1]) for i in range(0, len(ring) - 1, 2)]))
        out.append((country["n"], polys))
    return out


def _bounce(t):
    """Ease-out bounce: 0 -> 1 with a couple of small rebounds, like a pin dropping onto a map."""
    if t <= 0:
        return 0.0
    if t >= 1:
        return 1.0
    if t < 1 / 2.75:
        return 7.5625 * t * t
    if t < 2 / 2.75:
        t -= 1.5 / 2.75
        return 7.5625 * t * t + 0.75
    if t < 2.5 / 2.75:
        t -= 2.25 / 2.75
        return 7.5625 * t * t + 0.9375
    t -= 2.625 / 2.75
    return 7.5625 * t * t + 0.984375


def _pin_path():
    path = QPainterPath()
    path.moveTo(0, 0)
    path.cubicTo(-3, -6, -8, -10, -8, -17)
    path.arcTo(QRectF(-8, -25, 16, 16), 180, -180)
    path.cubicTo(8, -10, 3, -6, 0, 0)
    return path


class MapView(QWidget):
    selected = Signal(int)
    opened = Signal(int)

    def __init__(self):
        super().__init__()
        self.world = _world()
        self.pins = []
        self.sel = -1
        self.cx, self.cy, self.k = 0.0, 15.0, 1.0
        self.drag = None
        self.moved = False
        self.clusters = []
        self.clock = QElapsedTimer()
        self.clock.start()
        self.drop_start = -10_000
        self.ticker = QTimer(self)
        self.ticker.timeout.connect(self._tick)
        self.setMouseTracking(True)
        self.setMinimumSize(420, 300)
        self.pin_path = _pin_path()
        self.fitted = False

    # ---- view ---------------------------------------------------------------------------------------------------
    def min_k(self):
        return max(self.width() / 360.0, 0.5)

    def clamp(self):
        self.k = max(self.min_k(), min(MAX_K, self.k))
        half_w, half_h = self.width() / 2 / self.k, self.height() / 2 / self.k
        self.cx = max(-180 + half_w, min(180 - half_w, self.cx)) if half_w < 180 else 0.0
        self.cy = max(-90 + half_h, min(90 - half_h, self.cy)) if half_h < 90 else 0.0

    def to_screen(self, lon, lat):
        return QPointF(self.width() / 2 + (lon - self.cx) * self.k, self.height() / 2 - (lat - self.cy) * self.k)

    def to_world(self, x, y):
        return self.cx + (x - self.width() / 2) / self.k, self.cy - (y - self.height() / 2) / self.k

    def set_pins(self, pins):
        self.pins, self.sel = list(pins), -1
        self.fit_pins()
        self.replay()

    def fit_pins(self):
        if not self.pins:
            self.show_world()
            return
        lons, lats = [p.lon for p in self.pins], [p.lat for p in self.pins]
        span_lon, span_lat = max(max(lons) - min(lons), 1.0), max(max(lats) - min(lats), 1.0)
        self.cx, self.cy = (max(lons) + min(lons)) / 2, (max(lats) + min(lats)) / 2
        self.k = min(self.width() * 0.6 / span_lon, self.height() * 0.6 / span_lat, 14.0)
        self.clamp()
        self.update()

    def show_world(self):
        self.cx, self.cy, self.k = 0.0, 15.0, self.min_k()
        self.clamp()
        self.update()

    def focus(self, i, zoom=9.0):
        pin = self.pins[i]
        self.sel = i
        self.cx, self.cy, self.k = pin.lon, pin.lat, max(self.k, zoom)
        self.clamp()
        self.update()

    def select(self, i):
        self.sel = i
        self.update()

    def replay(self):
        self.drop_start = self.clock.elapsed()
        self.ticker.start(16)

    def _tick(self):
        if self.clock.elapsed() - self.drop_start > DROP_MS + STAGGER_MS * len(self.pins) + 100:
            self.ticker.stop()
        self.update()

    def resizeEvent(self, event):
        if not self.fitted and self.width() > 50:
            self.fitted = True
            self.fit_pins()
        else:
            self.clamp()
        super().resizeEvent(event)

    # ---- painting -----------------------------------------------------------------------------------------------
    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        g = QLinearGradient(0, 0, 0, self.height())
        g.setColorAt(0, QColor("#9CCBF0"))
        g.setColorAt(1, QColor("#5FA3DC"))
        p.fillRect(self.rect(), g)
        self._graticule(p)
        p.save()
        p.setTransform(QTransform(self.k, 0, 0, -self.k, self.width() / 2 - self.cx * self.k,
                                  self.height() / 2 + self.cy * self.k))
        pen = QPen(QColor("#7C8F62"), 0.8)
        pen.setCosmetic(True)
        p.setPen(pen)
        for name, polys in self.world:
            p.setBrush(QColor(LAND[sum(map(ord, name)) % len(LAND)]))
            for poly in polys:
                p.drawPolygon(poly)
        p.restore()
        self._pins(p)
        if not self.pins:
            p.setPen(QColor("#10305A"))
            p.setFont(QFont("Tahoma", 10, QFont.Bold))
            p.drawText(self.rect().adjusted(20, 0, -20, -10), Qt.AlignHCenter | Qt.AlignBottom | Qt.TextWordWrap,
                       "No pins yet: no resident has a Location in their record.")
        p.end()

    def _graticule(self, p):
        pen = QPen(QColor(255, 255, 255, 70), 1)
        p.setPen(pen)
        for lon in range(-180, 181, 30):
            x = self.to_screen(lon, 0).x()
            p.drawLine(QPointF(x, 0), QPointF(x, self.height()))
        for lat in range(-60, 91, 30):
            y = self.to_screen(0, lat).y()
            p.drawLine(QPointF(0, y), QPointF(self.width(), y))

    def _cluster(self, points):
        """Group pins that are within a pin's width of each other on screen."""
        groups = []
        for i, pt in enumerate(points):
            for grp in groups:
                q = points[grp[0]]
                if abs(q.x() - pt.x()) < 20 and abs(q.y() - pt.y()) < 22:
                    grp.append(i)
                    break
            else:
                groups.append([i])
        return groups

    def _pins(self, p):
        points = [self.to_screen(pin.lon, pin.lat) for pin in self.pins]
        self.clusters = [(g, points[g[0]]) for g in self._cluster(points)]
        now = self.clock.elapsed()
        for grp, pt in sorted(self.clusters, key=lambda c: c[1].y()):
            lead = min(grp)
            t = (now - self.drop_start - STAGGER_MS * lead) / DROP_MS
            if t <= 0 and now - self.drop_start < 5000:
                continue
            fall = (1 - _bounce(t)) * 150 if t < 1 else 0
            chosen = self.sel in grp
            you = any(getattr(self.pins[i].resident, "is_you", False) for i in grp)
            p.save()
            p.setPen(Qt.NoPen)                                              # shadow on the map
            p.setBrush(QColor(0, 0, 0, 70))
            shrink = max(0.4, 1 - fall / 150)
            p.drawEllipse(QPointF(pt.x(), pt.y()), 7 * shrink, 3 * shrink)
            p.translate(pt.x(), pt.y() - fall)
            scale = 1.25 if chosen else 1.0
            p.scale(scale, scale)
            p.setPen(QPen(QColor("#5E1409"), 1.2))
            p.setBrush(QColor("#2D78D2" if you else "#F2A30F" if chosen else "#E0442A"))
            p.drawPath(self.pin_path)
            p.setPen(Qt.NoPen)
            p.setBrush(QColor("white"))
            p.drawEllipse(QPointF(0, -17), 3.2, 3.2)
            p.restore()
            if len(grp) > 1:
                p.setPen(QPen(QColor("#5E1409"), 1))
                p.setBrush(QColor("#FFFBE0"))
                badge = QRectF(pt.x() + 5, pt.y() - 36 - fall, 16, 14)
                p.drawRoundedRect(badge, 6, 6)
                p.setPen(QColor("#5E1409"))
                p.setFont(QFont("Tahoma", 7, QFont.Bold))
                p.drawText(badge, Qt.AlignCenter, str(len(grp)))
            if chosen and fall == 0:
                self._callout(p, pt, self.pins[self.sel] if self.sel in grp else self.pins[lead], len(grp))

    def _callout(self, p, pt, pin, count):
        p.setFont(QFont("Tahoma", 8, QFont.Bold))
        title = pin.name + (f"  (+{count - 1} more here)" if count > 1 else "")
        sub = pin.place
        width = max(p.fontMetrics().horizontalAdvance(title), p.fontMetrics().horizontalAdvance(sub)) + 16
        box = QRectF(pt.x() - width / 2, pt.y() - 72, width, 36)
        box.moveLeft(max(4, min(self.width() - width - 4, box.left())))
        box.moveTop(max(4, box.top()))
        p.setPen(QPen(QColor("#6B5B2A"), 1))
        p.setBrush(QColor("#FFFBE0"))
        p.drawRoundedRect(box, 4, 4)
        p.setPen(QColor("black"))
        p.drawText(box.adjusted(8, 3, -8, -18), Qt.AlignLeft | Qt.AlignVCenter, title)
        p.setFont(QFont("Tahoma", 8))
        p.setPen(QColor("#555555"))
        p.drawText(box.adjusted(8, 18, -8, -3), Qt.AlignLeft | Qt.AlignVCenter, sub)

    # ---- mouse --------------------------------------------------------------------------------------------------
    def _hit(self, pos):
        for grp, pt in reversed(sorted(self.clusters, key=lambda c: c[1].y())):
            if abs(pos.x() - pt.x()) <= 10 and -28 <= pos.y() - pt.y() <= 4:
                return grp
        return None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag = event.position()
            self.moved = False

    def mouseMoveEvent(self, event):
        pos = event.position()
        if self.drag is not None and event.buttons() & Qt.LeftButton:
            if (pos - self.drag).manhattanLength() > 3:
                self.moved = True
            if self.moved:
                self.cx -= (pos.x() - self.drag.x()) / self.k
                self.cy += (pos.y() - self.drag.y()) / self.k
                self.drag = pos
                self.clamp()
                self.update()
            return
        grp = self._hit(pos)
        if grp:
            names = ", ".join(self.pins[i].name for i in grp[:6]) + ("..." if len(grp) > 6 else "")
            QToolTip.showText(event.globalPosition().toPoint(), f"{names}\n{self.pins[grp[0]].place}", self)
            self.setCursor(Qt.PointingHandCursor)
        else:
            QToolTip.hideText()
            self.setCursor(Qt.OpenHandCursor)

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.LeftButton or self.drag is None:
            return
        self.drag = None
        if self.moved:
            return
        grp = self._hit(event.position())
        if grp:
            self._click_group(grp, event.globalPosition().toPoint())

    def mouseDoubleClickEvent(self, event):
        grp = self._hit(event.position())
        if grp and len(grp) == 1:
            self.opened.emit(grp[0])

    def _click_group(self, grp, where):
        if len(grp) == 1:
            self.select(grp[0])
            self.selected.emit(grp[0])
            return
        spots = {(round(self.pins[i].lat, 4), round(self.pins[i].lon, 4)) for i in grp}
        if len(spots) > 1 and self.k < MAX_K * 0.7:                         # spread out: zoom in on them
            lons, lats = [self.pins[i].lon for i in grp], [self.pins[i].lat for i in grp]
            self.cx, self.cy = (max(lons) + min(lons)) / 2, (max(lats) + min(lats)) / 2
            span = max(max(lons) - min(lons), max(lats) - min(lats), 0.01)
            self.k = min(MAX_K, max(self.k * 1.8, min(self.width(), self.height()) * 0.4 / span))
            self.clamp()
            self.update()
            return
        menu = QMenu(self)                                                  # the same spot: pick one
        for i in grp:
            menu.addAction(self.pins[i].name, lambda i=i: (self.select(i), self.selected.emit(i)))
        menu.exec(where)

    def wheelEvent(self, event):
        pos = event.position()
        lon, lat = self.to_world(pos.x(), pos.y())
        self.k *= 1.25 if event.angleDelta().y() > 0 else 0.8
        self.k = max(self.min_k(), min(MAX_K, self.k))
        self.cx = lon - (pos.x() - self.width() / 2) / self.k
        self.cy = lat + (pos.y() - self.height() / 2) / self.k
        self.clamp()
        self.update()

    def zoom(self, factor):
        self.k = max(self.min_k(), min(MAX_K, self.k * factor))
        self.clamp()
        self.update()


class Locator(QWidget):
    def __init__(self, desktop):
        super().__init__()
        self.desktop = desktop
        self.frame = None
        self.setObjectName("fl")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("QWidget#fl { background: #F4ECD8; } QLabel { font: 11px Tahoma; }"
                           "QListWidget { background: #FFFBF0; border: 1px solid #C8B890; font: 11px Tahoma; }"
                           "QListWidget::item:selected { background: #E8D4A8; color: black; }"
                           "QPushButton { font: 11px Tahoma; padding: 3px 8px; }")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(8, 8, 8, 8)
        left = QVBoxLayout()
        bar = QHBoxLayout()
        for label, tip, fn in (("Fit Pins", "Zoom to show every pin", lambda: self.map.fit_pins()),
                               ("World", "Show the whole world", lambda: self.map.show_world()),
                               ("+", "Zoom in", lambda: self.map.zoom(1.6)),
                               ("-", "Zoom out", lambda: self.map.zoom(1 / 1.6)),
                               ("Drop Pins Again", "Replay the pin drop", lambda: self.map.replay()),
                               ("Refresh", "Re-read the Fur Directory", self.reload)):
            b = QPushButton(label)
            b.setToolTip(tip)
            if label in "+-":
                b.setFixedWidth(28)
            b.clicked.connect(fn)
            bar.addWidget(b)
        bar.addStretch()
        left.addLayout(bar)
        self.map = MapView()
        self.map.selected.connect(self._map_selected)
        self.map.opened.connect(self.open_card)
        left.addWidget(self.map, 1)
        self.status = QLabel()
        left.addWidget(self.status)
        lay.addLayout(left, 1)
        right = QVBoxLayout()
        right.addWidget(QLabel("<b>Furs on the map</b>"))
        self.list = QListWidget()
        self.list.setIconSize(QSize(32, 32))
        self.list.setFixedWidth(210)
        self.list.currentRowChanged.connect(self._list_selected)
        self.list.itemActivated.connect(lambda _i: self.open_card(self.list.currentRow()))
        right.addWidget(self.list, 1)
        self.open_btn = QPushButton("Open Card")
        self.open_btn.clicked.connect(lambda: self.open_card(self.list.currentRow()))
        right.addWidget(self.open_btn)
        self.notes = QLabel()
        self.notes.setWordWrap(True)
        self.notes.setFixedWidth(210)
        self.notes.setStyleSheet("color: #6A5A3A; font: 10px Tahoma; padding-top: 4px;")
        right.addWidget(self.notes)
        lay.addLayout(right)
        self.pins = []
        self.reload()

    def reload(self):
        from .furdir import avatar, residents
        everyone = residents()
        self.pins, unknown, none = survey(everyone)
        self.pins.sort(key=lambda pin: pin.name.lower())
        self.list.blockSignals(True)
        self.list.clear()
        for pin in self.pins:
            item = QListWidgetItem(QIcon(QPixmap.fromImage(avatar(pin.resident, 32))),
                                   f"{pin.name}{'  (you)' if pin.resident.is_you else ''}\n{pin.place}")
            self.list.addItem(item)
        self.list.blockSignals(False)
        self.open_btn.setEnabled(False)
        self.map.set_pins(self.pins)
        self.status.setText(f"{len(self.pins)} of {len(everyone)} residents pinned.   Drag to pan, wheel to zoom.")
        text = (f"{len(none)} resident{'s' if len(none) != 1 else ''} have no Location on file, so they aren't "
                "pinned. Fill in \"location\" in a record (Program Files\\The Fur Directory\\residents) to add one.")
        if unknown:
            text += "\nCouldn't place: " + "; ".join(f"{r.name} ({t})" for r, t in unknown[:8])
            text += "..." if len(unknown) > 8 else ""
        self.notes.setText(text)

    def _list_selected(self, row):
        self.open_btn.setEnabled(row >= 0)
        if 0 <= row < len(self.pins):
            self.map.focus(row)

    def _map_selected(self, i):
        self.list.blockSignals(True)
        self.list.setCurrentRow(i)
        self.list.blockSignals(False)
        self.open_btn.setEnabled(True)

    def open_card(self, i):
        if 0 <= i < len(self.pins):
            from .furdir import open_furdir
            open_furdir(self.desktop, rid=self.pins[i].resident.id)


_open = {}


def open_furlocator(desktop):
    win = _open.get("win")
    if win is None or not isValid(win):
        body = Locator(desktop)
        win = XPWindow(desktop, TITLE, body, locator_icon(16), (900, 600))
        body.frame = win
        _open["win"] = win
    desktop.open_window(win)
    return win
