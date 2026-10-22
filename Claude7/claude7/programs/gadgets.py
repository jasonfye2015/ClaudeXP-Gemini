"""Desktop gadgets, Windows 7 style: the clock, the calendar, the CPU meter, the weather and a slide show, sitting
on the desktop under the windows. Drag them anywhere; the close button shows when you point at one. The Desktop
Gadget Gallery adds them, and they come back where you left them (data/gadgets.json)."""
import datetime
import json
import math
import random

from PySide6.QtCore import QPointF, QRect, QRectF, QSize, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QIcon, QLinearGradient, QPainter, QPen, QPixmap, QRadialGradient
from PySide6.QtWidgets import QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QPushButton, QVBoxLayout, QWidget
from shiboken6 import isValid

from .. import clock, sound
from ..paths import DATA
from ..wm import AeroWindow

GADGETS_FILE = DATA / "gadgets.json"
_controller = None


class Gadget(QWidget):
    SIZE = (130, 130)
    NAME = "Gadget"
    TICK = 1000

    def __init__(self, gadgets, data):
        super().__init__(gadgets.desktop)
        self.gadgets = gadgets
        self.data = data
        self.hover = False
        self.drag = None
        self.setMouseTracking(True)
        self.resize(*self.SIZE)
        self.move(data.get("x", 40), data.get("y", 40))
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(self.TICK)

    def _x_rect(self):
        return QRect(self.width() - 16, 2, 14, 14)

    def enterEvent(self, event):
        self.hover = True
        self.update()

    def leaveEvent(self, event):
        self.hover = False
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            from ..shims import MENU_CSS
            from PySide6.QtWidgets import QMenu
            menu = QMenu(self)
            menu.setStyleSheet(MENU_CSS)
            menu.addAction("Add gadgets...", lambda: open_gallery(self.gadgets.desktop))
            menu.addAction("Close gadget", lambda: self.gadgets.remove(self))
            menu.popup(event.globalPosition().toPoint())
            return
        if self._x_rect().contains(event.position().toPoint()):
            self.gadgets.remove(self)
            return
        self.drag = event.globalPosition().toPoint() - self.pos()

    def mouseMoveEvent(self, event):
        if self.drag is not None:
            area = self.gadgets.desktop.work_area()
            p = event.globalPosition().toPoint() - self.drag
            p.setX(max(0, min(p.x(), area.width() - self.width())))
            p.setY(max(0, min(p.y(), area.height() - self.height())))
            self.move(p)

    def mouseReleaseEvent(self, event):
        if self.drag is not None:
            self.drag = None
            self.data.update(x=self.x(), y=self.y())
            self.gadgets.save()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        self.draw(p)
        if self.hover:
            r = self._x_rect()
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(0, 0, 0, 120))
            p.drawRoundedRect(QRectF(r), 3, 3)
            p.setPen(QPen(QColor("white"), 1.5))
            p.drawLine(r.x() + 4, r.y() + 4, r.right() - 3, r.bottom() - 3)
            p.drawLine(r.right() - 3, r.y() + 4, r.x() + 4, r.bottom() - 3)

    def draw(self, p):
        pass

    @staticmethod
    def glass(p, rect, radius=8, dark=False):
        g = QLinearGradient(rect.topLeft(), rect.bottomLeft())
        if dark:
            g.setColorAt(0, QColor(60, 60, 60, 230))
            g.setColorAt(1, QColor(20, 20, 20, 230))
        else:
            g.setColorAt(0, QColor(255, 255, 255, 235))
            g.setColorAt(1, QColor(225, 230, 238, 235))
        p.setPen(QPen(QColor(0, 0, 0, 90), 1))
        p.setBrush(g)
        p.drawRoundedRect(rect, radius, radius)


class ClockGadget(Gadget):
    SIZE = (130, 130)
    NAME = "Clock"

    def draw(self, p):
        now = clock.now()
        r = QRectF(self.rect()).adjusted(6, 6, -6, -6)
        g = QRadialGradient(r.center(), r.width() / 2)
        g.setColorAt(0, QColor("#FFFFFF"))
        g.setColorAt(0.85, QColor("#E6ECF4"))
        g.setColorAt(1, QColor("#9CA8B8"))
        p.setPen(QPen(QColor("#2E3A48"), 3))
        p.setBrush(g)
        p.drawEllipse(r)
        c = r.center()
        rad = r.width() / 2
        p.setPen(QPen(QColor("#2E3A48"), 2))
        for i in range(12):
            a = math.radians(i * 30)
            inner = rad - (10 if i % 3 == 0 else 6)
            p.drawLine(QPointF(c.x() + math.sin(a) * inner, c.y() - math.cos(a) * inner),
                       QPointF(c.x() + math.sin(a) * (rad - 3), c.y() - math.cos(a) * (rad - 3)))
        for length, width, angle, colour in ((rad * 0.5, 4, (now.hour % 12 + now.minute / 60) * 30, "#1E2835"),
                                             (rad * 0.72, 3, now.minute * 6 + now.second / 10, "#1E2835"),
                                             (rad * 0.8, 1, now.second * 6, "#D23B2E")):
            a = math.radians(angle)
            p.setPen(QPen(QColor(colour), width, Qt.SolidLine, Qt.RoundCap))
            p.drawLine(c, QPointF(c.x() + math.sin(a) * length, c.y() - math.cos(a) * length))
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#1E2835"))
        p.drawEllipse(c, 4, 4)


class CalendarGadget(Gadget):
    SIZE = (150, 150)
    NAME = "Calendar"
    TICK = 60000

    def draw(self, p):
        now = clock.now()
        r = QRectF(self.rect()).adjusted(2, 2, -2, -2)
        self.glass(p, r)
        p.fillRect(QRectF(r.x() + 1, r.y() + 1, r.width() - 2, 22), QColor("#C0392B"))
        f = QFont("Segoe UI")
        f.setPixelSize(12)
        f.setBold(True)
        p.setFont(f)
        p.setPen(QColor("white"))
        p.drawText(QRectF(r.x(), r.y() + 1, r.width(), 22), Qt.AlignCenter, now.strftime("%B %Y"))
        f.setBold(False)
        f.setPixelSize(10)
        p.setFont(f)
        cell_w = (r.width() - 8) / 7
        y = r.y() + 28
        for i, d in enumerate("SMTWTFS"):
            p.setPen(QColor("#6D6D6D"))
            p.drawText(QRectF(r.x() + 4 + i * cell_w, y, cell_w, 14), Qt.AlignCenter, d)
        first = now.replace(day=1)
        start_col = (first.weekday() + 1) % 7
        days = (first.replace(month=first.month % 12 + 1, day=1, year=first.year + (first.month == 12)) -
                datetime.timedelta(days=1)).day
        y += 16
        for day in range(1, days + 1):
            col = (start_col + day - 1) % 7
            row = (start_col + day - 1) // 7
            cell = QRectF(r.x() + 4 + col * cell_w, y + row * 15, cell_w, 15)
            if day == now.day:
                p.setPen(Qt.NoPen)
                p.setBrush(QColor("#C0392B"))
                p.drawRoundedRect(cell.adjusted(1, 0, -1, 0), 3, 3)
                p.setPen(QColor("white"))
            else:
                p.setPen(QColor("#1E1E1E"))
            p.drawText(cell, Qt.AlignCenter, str(day))


class CpuGadget(Gadget):
    SIZE = (150, 90)
    NAME = "CPU Meter"

    def __init__(self, gadgets, data):
        super().__init__(gadgets, data)
        self.cpu, self.ram = 12.0, 38.0

    def _sample(self):
        try:
            import psutil
            self.cpu = psutil.cpu_percent(interval=None)
            self.ram = psutil.virtual_memory().percent
        except Exception:
            self.cpu = max(2.0, min(95.0, self.cpu + random.uniform(-8, 8)))
            self.ram = max(20.0, min(90.0, self.ram + random.uniform(-1, 1)))

    def draw(self, p):
        self._sample()
        r = QRectF(self.rect()).adjusted(2, 2, -2, -2)
        self.glass(p, r, dark=True)
        for i, (label, value) in enumerate((("CPU", self.cpu), ("RAM", self.ram))):
            cx = r.x() + 40 + i * 72
            cy = r.center().y() + 4
            rad = 28
            p.setPen(QPen(QColor(255, 255, 255, 60), 6))
            p.setBrush(Qt.NoBrush)
            p.drawArc(QRectF(cx - rad, cy - rad, 2 * rad, 2 * rad), 225 * 16, -270 * 16)
            p.setPen(QPen(QColor("#4FC3F7") if i == 0 else QColor("#81C784"), 6))
            p.drawArc(QRectF(cx - rad, cy - rad, 2 * rad, 2 * rad), 225 * 16, int(-270 * 16 * value / 100))
            f = QFont("Segoe UI")
            f.setPixelSize(12)
            p.setFont(f)
            p.setPen(QColor("white"))
            p.drawText(QRectF(cx - rad, cy - 10, 2 * rad, 20), Qt.AlignCenter, f"{int(value)}%")
            f.setPixelSize(9)
            p.setFont(f)
            p.drawText(QRectF(cx - rad, cy + 12, 2 * rad, 14), Qt.AlignCenter, label)


class WeatherGadget(Gadget):
    SIZE = (150, 90)
    NAME = "Weather"
    TICK = 60000
    CONDITIONS = ["Sunny", "Partly Cloudy", "Cloudy", "Showers", "Clear"]

    def draw(self, p):
        now = clock.now()
        seed = now.timetuple().tm_yday * 24 + now.hour
        rnd = random.Random(seed)
        cond = rnd.choice(self.CONDITIONS)
        temp = 48 + int(10 * math.sin(now.hour / 24 * 2 * math.pi - 1.5)) + rnd.randint(-3, 3)
        r = QRectF(self.rect()).adjusted(2, 2, -2, -2)
        g = QLinearGradient(r.topLeft(), r.bottomLeft())
        g.setColorAt(0, QColor("#58A6E8"))
        g.setColorAt(1, QColor("#1F5FA8"))
        p.setPen(QPen(QColor(0, 0, 0, 90), 1))
        p.setBrush(g)
        p.drawRoundedRect(r, 8, 8)
        cx, cy = r.x() + 34, r.center().y()
        if cond in ("Sunny", "Clear"):
            p.setPen(Qt.NoPen)
            p.setBrush(QColor("#FFD54F"))
            p.drawEllipse(QPointF(cx, cy), 16, 16)
        else:
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(255, 255, 255, 230))
            p.drawEllipse(QPointF(cx - 8, cy + 2), 11, 11)
            p.drawEllipse(QPointF(cx + 4, cy - 4), 14, 14)
            p.drawEllipse(QPointF(cx + 12, cy + 4), 10, 10)
            if cond == "Showers":
                p.setPen(QPen(QColor("#BBDEFB"), 2))
                for i in range(3):
                    p.drawLine(QPointF(cx - 6 + i * 9, cy + 16), QPointF(cx - 9 + i * 9, cy + 24))
        f = QFont("Segoe UI")
        f.setPixelSize(24)
        p.setFont(f)
        p.setPen(QColor("white"))
        p.drawText(QRectF(r.x() + 64, r.y() + 10, 80, 32), Qt.AlignLeft | Qt.AlignVCenter, f"{temp}°F")
        f.setPixelSize(11)
        p.setFont(f)
        p.drawText(QRectF(r.x() + 64, r.y() + 42, 84, 16), Qt.AlignLeft, cond)
        p.drawText(QRectF(r.x() + 64, r.y() + 58, 84, 16), Qt.AlignLeft, "Seattle, WA")


class SlideShowGadget(Gadget):
    SIZE = (160, 120)
    NAME = "Slide Show"
    TICK = 8000

    def __init__(self, gadgets, data):
        super().__init__(gadgets, data)
        self.index = 0
        self.pixmaps = None

    def _pictures(self):
        if self.pixmaps is None:
            from ..controlpanel import _found_pictures
            self.pixmaps = [QPixmap(str(path)) for path in _found_pictures()[:40]]
            self.pixmaps = [pm for pm in self.pixmaps if not pm.isNull()]
        return self.pixmaps

    def draw(self, p):
        r = QRectF(self.rect()).adjusted(2, 2, -2, -2)
        self.glass(p, r)
        pics = self._pictures()
        inner = r.adjusted(6, 6, -6, -6)
        if not pics:
            f = QFont("Segoe UI")
            f.setPixelSize(11)
            p.setFont(f)
            p.setPen(QColor("#6D6D6D"))
            p.drawText(inner, Qt.AlignCenter | Qt.TextWordWrap, "No pictures in your Pictures library yet.")
            return
        self.index = (self.index + 1) % len(pics)
        pm = pics[self.index].scaled(inner.size().toSize(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        p.drawPixmap(int(inner.x() + (inner.width() - pm.width()) / 2), int(inner.y() + (inner.height() - pm.height()) / 2), pm)


class FeedGadget(Gadget):
    """Feed Headlines: the latest from your friends' journals and Facebook walls."""
    SIZE = (200, 150)
    NAME = "Feed Headlines"
    TICK = 60000

    def __init__(self, gadgets, data):
        super().__init__(gadgets, data)
        self.items = []
        self.setCursor(Qt.PointingHandCursor)

    def _refresh(self):
        try:
            from claudexp.life import get, lj
            sim = get()
            found = []
            for name in (sorted(sim.people) if sim is not None else []):
                entries = lj.resident_entries(name)
                if entries:
                    found.append((entries[0]["id"], name, entries[0]["text"]))
            found.sort(reverse=True)
            self.items = found[:5]
        except Exception:
            self.items = []

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and not self._x_rect().contains(event.position().toPoint()) \
                and self.drag is None and event.position().y() > 24:
            try:
                from claudexp.programs import navigator
                navigator.open_url(self.gadgets.desktop, "http://www.facebook.com/")
            except Exception:
                pass
            return
        super().mousePressEvent(event)

    def draw(self, p):
        if not self.items or self.data.get("_ticks", 0) % 5 == 0:
            self._refresh()
        self.data["_ticks"] = self.data.get("_ticks", 0) + 1
        r = QRectF(self.rect()).adjusted(2, 2, -2, -2)
        self.glass(p, r, dark=True)
        f = QFont("Segoe UI")
        f.setPixelSize(12)
        f.setBold(True)
        p.setFont(f)
        p.setPen(QColor("#FFB347"))
        p.drawText(QRectF(r.x() + 10, r.y() + 6, r.width() - 20, 18), Qt.AlignLeft | Qt.AlignVCenter, "Feed Headlines")
        f.setBold(False)
        f.setPixelSize(11)
        p.setFont(f)
        y = r.y() + 28
        if not self.items:
            p.setPen(QColor("#CCCCCC"))
            p.drawText(QRectF(r.x() + 10, y, r.width() - 20, 40), Qt.TextWordWrap, "Nothing new yet. Your friends' "
                       "updates appear here.")
            return
        fm = p.fontMetrics()
        for _id, name, text in self.items:
            line = fm.elidedText(f"{name}: {text.strip().splitlines()[0] if text.strip() else ''}", Qt.ElideRight,
                                 int(r.width() - 20))
            p.setPen(QColor("#FFFFFF"))
            p.drawText(QRectF(r.x() + 10, y, r.width() - 20, 16), Qt.AlignLeft | Qt.AlignVCenter, line)
            y += 22
            if y > r.bottom() - 16:
                break


KINDS = {"Clock": ClockGadget, "Calendar": CalendarGadget, "CPU Meter": CpuGadget, "Weather": WeatherGadget,
         "Slide Show": SlideShowGadget, "Feed Headlines": FeedGadget}


class Gadgets:
    def __init__(self, desktop):
        self.desktop = desktop
        self.gadgets = []
        self.loaded = False

    def load(self):
        if self.loaded:
            return
        self.loaded = True
        try:
            data = json.loads(GADGETS_FILE.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            data = {}
        for d in data.get("gadgets", []):
            cls = KINDS.get(d.get("kind"))
            if cls is not None:
                self.gadgets.append(cls(self, d))

    def save(self):
        try:
            GADGETS_FILE.parent.mkdir(parents=True, exist_ok=True)
            GADGETS_FILE.write_text(json.dumps({"gadgets": [g.data for g in self.live()]}, indent=2),
                                    encoding="utf-8")
        except OSError:
            pass

    def live(self):
        self.gadgets = [g for g in self.gadgets if isValid(g)]
        return self.gadgets

    def add(self, kind):
        cls = KINDS[kind]
        area = self.desktop.work_area()
        x = area.width() - cls.SIZE[0] - 20
        y = 20 + sum(g.height() + 12 for g in self.live())
        if y + cls.SIZE[1] > area.height():
            y = 20
            x -= cls.SIZE[0] + 20
        g = cls(self, {"kind": kind, "x": x, "y": y})
        self.gadgets.append(g)
        g.show()
        self.restack()
        self.save()
        sound.play("default")

    def remove(self, gadget):
        if gadget in self.gadgets:
            self.gadgets.remove(gadget)
        gadget.hide()
        gadget.deleteLater()
        self.save()

    def restack(self):
        """Gadgets sit over the icons and under every window."""
        for g in self.live():
            g.lower()
        self.desktop.icons.stack_below_windows()

    raise_all = restack

    def on_resize(self):
        area = self.desktop.work_area()
        for g in self.live():
            g.move(max(0, min(g.x(), area.width() - g.width())), max(0, min(g.y(), area.height() - g.height())))

    def show_all(self):
        self.load()
        for g in self.live():
            g.show()
        self.restack()

    def hide_all(self):
        for g in self.live():
            g.hide()


def install(desktop):
    global _controller
    _controller = Gadgets(desktop)
    desktop.gadgets = _controller
    return _controller


def _get(desktop):
    if _controller is None or _controller.desktop is not desktop:
        install(desktop)
    _controller.load()
    return _controller


def start_at_logon(desktop):
    _get(desktop).show_all()


def hide_all(desktop):
    if _controller is not None:
        _controller.hide_all()


def shutdown():
    if _controller is not None:
        _controller.save()


def gadget_pixmap(kind, size=64):
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    colours = {"Clock": "#E6ECF4", "Calendar": "#C0392B", "CPU Meter": "#2E2E2E", "Weather": "#58A6E8",
               "Slide Show": "#F5F5F5", "Feed Headlines": "#3A3A3A"}
    p.setPen(QPen(QColor(0, 0, 0, 90), 1))
    p.setBrush(QColor(colours.get(kind, "#CCCCCC")))
    p.drawRoundedRect(QRectF(4, 8, size - 8, size - 16), 8, 8)
    f = QFont("Segoe UI")
    f.setPixelSize(11)
    p.setFont(f)
    p.setPen(QColor("white" if kind in ("Calendar", "CPU Meter", "Weather", "Feed Headlines") else "#1E1E1E"))
    p.drawText(QRectF(4, 8, size - 8, size - 16), Qt.AlignCenter | Qt.TextWordWrap, kind)
    p.end()
    return pm


_gallery = {}


def open_gallery(desktop):
    win = _gallery.get("win")
    if win is not None and isValid(win) and win in desktop.windows:
        desktop.activate(win)
        return
    body = QWidget()
    body.setStyleSheet("background: white;")
    v = QVBoxLayout(body)
    v.setContentsMargins(10, 8, 10, 8)
    lst = QListWidget()
    lst.setViewMode(QListWidget.IconMode)
    lst.setIconSize(QSize(64, 64))
    lst.setGridSize(QSize(100, 96))
    lst.setMovement(QListWidget.Static)
    lst.setStyleSheet("QListWidget { border: none; font-family: 'Segoe UI'; font-size: 12px; }")
    for kind in KINDS:
        it = QListWidgetItem(QIcon(gadget_pixmap(kind)), kind)
        lst.addItem(it)
    v.addWidget(lst, 1)
    row = QHBoxLayout()
    hint = QLabel("Double-click a gadget to add it to the desktop.")
    hint.setStyleSheet("font-family: 'Segoe UI'; font-size: 12px; color: #6D6D6D;")
    row.addWidget(hint, 1)
    add = QPushButton("Add")
    add.setStyleSheet("QPushButton { font-family: 'Segoe UI'; font-size: 12px; padding: 4px 16px; }")
    row.addWidget(add)
    v.addLayout(row)

    def add_current(*_):
        it = lst.currentItem()
        if it is not None:
            _get(desktop).add(it.text())
    lst.itemDoubleClicked.connect(add_current)
    add.clicked.connect(add_current)
    from . import gadget_icon
    win = AeroWindow(desktop, "Desktop Gadget Gallery", body, gadget_icon(), (560, 380))
    _gallery["win"] = win
    desktop.open_window(win)
    sound.play("navigate")
