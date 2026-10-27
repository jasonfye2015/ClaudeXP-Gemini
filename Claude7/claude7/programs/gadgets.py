"""Desktop gadgets, Windows 7 style: the clock, the calendar, the CPU meter, the weather, a slide show, Feed
Headlines, your e-mail inbox and the TV Guide, sitting on the desktop under the windows. Drag them anywhere; the
close button shows when you point at one. The Desktop Gadget Gallery adds them, and they come back where you left
them (data/gadgets.json)."""
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
        p.drawPixmap(int(inner.x() + (inner.width() - int(pm.deviceIndependentSize().width())) / 2), int(inner.y() + (inner.height() - int(pm.deviceIndependentSize().height())) / 2), pm)


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


class MailGadget(Gadget):
    """E-mail: your inbox at a glance - the unread count and the latest messages. Click one to read it in
    Windows Live Mail."""
    SIZE = (220, 160)
    NAME = "E-mail"
    TICK = 15000
    HEAD = 26
    ROW = 31

    def __init__(self, gadgets, data):
        super().__init__(gadgets, data)
        self.items = []
        self.unread = 0
        self._hits = []
        self._listening = False
        self.setCursor(Qt.PointingHandCursor)
        self._refresh()

    def _sim(self):
        try:
            from claudexp.life import get
            return get()
        except Exception:
            return None

    def _refresh(self):
        sim = self._sim()
        if sim is None:
            self.items, self.unread = [], 0
            return
        if not self._listening:
            try:
                sim.mail_arrived.connect(self._arrived)
                self._listening = True
            except Exception:
                pass
        try:
            msgs = [m for m in sim.mailbox.messages() if m.get("folder", "inbox") == "inbox"]
        except Exception:
            msgs = []
        msgs.sort(key=lambda m: (m.get("ts", 0), m.get("id", 0)), reverse=True)
        self.unread = sum(1 for m in msgs if not m.get("read"))
        self.items = msgs[:4]

    def _arrived(self):
        if isValid(self):
            self._refresh()
            self.update()

    def _open(self, message=None):
        desktop = self.gadgets.desktop
        try:
            from claudexp.programs import outlook
            win = outlook.open_outlook(desktop)
        except Exception:
            return
        if message is None or win is None:
            return

        def select():
            body = getattr(win, "content", None)
            lst = getattr(body, "list", None)
            if body is None or lst is None or not isValid(lst):
                return
            for i in range(lst.topLevelItemCount()):
                item = lst.topLevelItem(i)
                m = item.data(0, Qt.UserRole)
                if isinstance(m, dict) and m.get("kind") == "in" and m.get("id") == message.get("id"):
                    lst.setCurrentItem(item)
                    return
        QTimer.singleShot(0, select)

    def mousePressEvent(self, event):
        pos = event.position().toPoint()
        if event.button() == Qt.LeftButton and not self._x_rect().contains(pos) and self.drag is None:
            for rect, message in self._hits:
                if rect.contains(pos):
                    self._open(message)
                    return
        super().mousePressEvent(event)

    def draw(self, p):
        self.data["_ticks"] = self.data.get("_ticks", 0) + 1
        if self.data["_ticks"] % 2 == 0:
            self._refresh()
        r = QRectF(self.rect()).adjusted(2, 2, -2, -2)
        self.glass(p, r)
        head = QRectF(r.x() + 1, r.y() + 1, r.width() - 2, self.HEAD)
        g = QLinearGradient(head.topLeft(), head.bottomLeft())
        g.setColorAt(0, QColor("#4C8ED9"))
        g.setColorAt(1, QColor("#2E6DB8"))
        p.setPen(Qt.NoPen)
        p.setBrush(g)
        p.drawRoundedRect(head, 7, 7)
        p.drawRect(QRectF(head.x(), head.y() + 12, head.width(), head.height() - 12))
        # the envelope
        ex, ey = head.x() + 10, head.y() + 7
        p.setPen(QPen(QColor("#24497A"), 1))
        p.setBrush(QColor("#FFF6D0"))
        p.drawRect(QRectF(ex, ey, 16, 11))
        p.setBrush(Qt.NoBrush)
        p.drawLine(QPointF(ex, ey), QPointF(ex + 8, ey + 6.5))
        p.drawLine(QPointF(ex + 16, ey), QPointF(ex + 8, ey + 6.5))
        f = QFont("Segoe UI")
        f.setPixelSize(12)
        f.setBold(True)
        p.setFont(f)
        p.setPen(QColor("white"))
        p.drawText(QRectF(head.x() + 32, head.y(), 100, head.height()), Qt.AlignLeft | Qt.AlignVCenter, "Inbox")
        f.setBold(False)
        f.setPixelSize(11)
        p.setFont(f)
        count = f"{self.unread} unread" if self.unread else "No new mail"
        p.drawText(QRectF(head.x(), head.y(), head.width() - 22, head.height()), Qt.AlignRight | Qt.AlignVCenter,
                   count)
        self._hits = [(QRectF(r.x(), r.y(), r.width(), self.HEAD + 2), None)]
        y = r.y() + self.HEAD + 4
        if not self.items:
            p.setPen(QColor("#6D6D6D"))
            p.drawText(QRectF(r.x() + 10, y + 6, r.width() - 20, 60), Qt.TextWordWrap,
                       "Your inbox is empty. Mail from your friends shows up here - click to open Windows Live Mail.")
            self._hits.append((QRectF(r.x(), y, r.width(), r.height() - self.HEAD), None))
            return
        fm_w = int(r.width() - 24)
        for m in self.items:
            row = QRectF(r.x() + 4, y, r.width() - 8, self.ROW)
            self._hits.append((row, m))
            unread = not m.get("read")
            if unread:
                p.setPen(Qt.NoPen)
                p.setBrush(QColor("#FFF4C2"))
                p.drawRoundedRect(row.adjusted(2, 0, -2, -2), 3, 3)
            f.setBold(unread)
            f.setPixelSize(11)
            p.setFont(f)
            fm = p.fontMetrics()
            p.setPen(QColor("#1E1E1E"))
            sender = fm.elidedText(str(m.get("from", "")), Qt.ElideRight, fm_w - 46)
            p.drawText(QRectF(row.x() + 8, row.y() + 1, fm_w - 46, 15), Qt.AlignLeft | Qt.AlignVCenter, sender)
            f.setBold(False)
            f.setPixelSize(9)
            p.setFont(f)
            p.setPen(QColor("#6D6D6D"))
            p.drawText(QRectF(row.right() - 50, row.y() + 2, 42, 13), Qt.AlignRight | Qt.AlignVCenter,
                       _mail_when(m))
            f.setPixelSize(10)
            p.setFont(f)
            fm = p.fontMetrics()
            p.setPen(QColor("#1E1E1E" if unread else "#55606E"))
            subject = fm.elidedText(str(m.get("subject", "")) or "(no subject)", Qt.ElideRight, fm_w)
            p.drawText(QRectF(row.x() + 8, row.y() + 15, fm_w, 14), Qt.AlignLeft | Qt.AlignVCenter, subject)
            y += self.ROW
            if y + self.ROW > r.bottom():
                break


def _mail_when(m):
    """Mail from today shows its time, older mail its day (like the Received column)."""
    try:
        when = datetime.datetime.fromtimestamp(int(m.get("ts", 0)))
        now = datetime.datetime.now()
        when = when.replace(year=clock.YEAR)
        if (when.month, when.day) == (now.month, now.day):
            return clock.time_text(when)
        return f"{when.month}/{when.day}"
    except (ValueError, OSError, OverflowError):
        return ""


def _program_title(slot):
    try:
        from claudetv.tuner import describe
        return describe(slot)[0]
    except Exception:
        try:
            return slot.media.label()
        except Exception:
            return "Program"


def _tv_clock(dt):
    suffix = "am" if dt.hour < 12 else "pm"
    return f"{dt.hour % 12 or 12}:{dt.minute:02d}{suffix}"


class TVGadget(Gadget):
    """TV Guide: what's on each ClaudeTV channel right now and what's next. Click a channel to watch it, or the
    heading for the full TV Guide. The wheel (or the arrows) scrolls through the channels."""
    SIZE = (220, 170)
    NAME = "TV Guide"
    TICK = 15000
    HEAD = 26
    ROW = 34

    def __init__(self, gadgets, data):
        super().__init__(gadgets, data)
        self.channels = None
        self.rows = []
        self.offset = 0
        self._hits = []
        self._asked = False
        self.setCursor(Qt.PointingHandCursor)
        self._ask()

    def _ask(self):
        if self._asked:
            return
        self._asked = True
        try:
            from claudetv import lineup
            lineup.get(self._lineup)
        except Exception:
            self.channels = []

    def _lineup(self, channels):
        if not isValid(self):
            return
        self.channels = [ch for ch in channels if not getattr(ch, "dead", False)]
        self._refresh()
        self.update()

    def _shown(self):
        return max(1, int((self.height() - self.HEAD - 10) // self.ROW))

    def _refresh(self):
        if self.channels is None:
            return
        try:
            from claudetv import schedule
            t = (clock.now() - schedule.EPOCH).total_seconds()
        except Exception:
            self.rows = []
            return
        rows = []
        for ch in self.channels:
            try:
                progs = ch.programs(t, t + 6 * 3600)
            except Exception:
                progs = []
            cur = nxt = None
            if progs and progs[0].start <= t:
                cur, nxt = progs[0], (progs[1] if len(progs) > 1 else None)
            elif progs:
                nxt = progs[0]
            rows.append((ch, cur, nxt, t))
        self.rows = rows
        self.offset = max(0, min(self.offset, len(rows) - self._shown()))

    def scroll(self, way):
        self.offset = max(0, min(self.offset + way, len(self.rows) - self._shown()))
        self.update()

    def wheelEvent(self, event):
        if len(self.rows) > self._shown():
            self.scroll(-1 if event.angleDelta().y() > 0 else 1)
            event.accept()

    def _open(self, target):
        desktop = self.gadgets.desktop
        try:
            from claudetv import guide, tuner
            if target is None:
                guide.open_guide(desktop)
            else:
                tuner.open_tv(desktop)
                body = tuner.current()
                if body is not None:
                    body.tune(target)
        except Exception:
            pass

    def mousePressEvent(self, event):
        pos = event.position().toPoint()
        if event.button() == Qt.LeftButton and not self._x_rect().contains(pos) and self.drag is None:
            for rect, target in self._hits:
                if rect.contains(pos):
                    if isinstance(target, int):
                        self.scroll(target)
                    else:
                        self._open(target)
                    return
        super().mousePressEvent(event)

    def draw(self, p):
        self._refresh()
        r = QRectF(self.rect()).adjusted(2, 2, -2, -2)
        self.glass(p, r, dark=True)
        f = QFont("Segoe UI")
        f.setPixelSize(12)
        f.setBold(True)
        p.setFont(f)
        p.setPen(QColor("#FFD35C"))
        p.drawText(QRectF(r.x() + 10, r.y() + 5, 120, 18), Qt.AlignLeft | Qt.AlignVCenter, "TV Guide")
        f.setBold(False)
        f.setPixelSize(10)
        p.setFont(f)
        p.setPen(QColor("#CCCCCC"))
        self._hits = []
        shown = self._shown()
        if len(self.rows) > shown:
            arrows = (("▲", -1, self.offset > 0), ("▼", 1, self.offset + shown < len(self.rows)))
            for i, (arrow, way, ok) in enumerate(arrows):
                box = QRectF(r.right() - 60 + i * 20, r.y() + 5, 18, 18)
                p.setPen(QColor("#FFD35C" if ok else "#777777"))
                p.drawText(box, Qt.AlignCenter, arrow)
                self._hits.append((box, way))
        else:
            p.drawText(QRectF(r.x() + 10, r.y() + 5, r.width() - 32, 18), Qt.AlignRight | Qt.AlignVCenter,
                       clock.time_text())
        self._hits.append((QRectF(r.x(), r.y(), r.width(), self.HEAD), None))
        y = r.y() + self.HEAD + 2
        f.setPixelSize(11)
        p.setFont(f)
        if self.channels is None:
            p.setPen(QColor("#CCCCCC"))
            p.drawText(QRectF(r.x() + 10, y + 6, r.width() - 20, 40), Qt.TextWordWrap, "Reading the channel lineup…")
            return
        if not self.rows:
            p.setPen(QColor("#CCCCCC"))
            p.drawText(QRectF(r.x() + 10, y + 6, r.width() - 20, 60), Qt.TextWordWrap,
                       "No channels are on the air. Open ClaudeTV to set up the video archive.")
            self._hits.append((QRectF(r.x(), y, r.width(), r.height() - self.HEAD), None))
            return
        for ch, cur, nxt, t in self.rows[self.offset:self.offset + shown]:
            row = QRectF(r.x() + 4, y, r.width() - 8, self.ROW)
            self._hits.append((row, ch))
            p.setPen(QPen(QColor(255, 255, 255, 40), 1))
            p.drawLine(QPointF(row.x() + 4, row.y()), QPointF(row.right() - 4, row.y()))
            f.setBold(True)
            f.setPixelSize(11)
            p.setFont(f)
            p.setPen(QColor("#FFD35C"))
            label = p.fontMetrics().elidedText(ch.label(), Qt.ElideRight, 54)
            p.drawText(QRectF(row.x() + 6, row.y() + 3, 54, 15), Qt.AlignLeft | Qt.AlignVCenter, label)
            f.setBold(False)
            p.setFont(f)
            fm = p.fontMetrics()
            w = int(row.width() - 70)
            if cur is not None:
                p.setPen(QColor("#FFFFFF"))
                p.drawText(QRectF(row.x() + 64, row.y() + 3, w, 15), Qt.AlignLeft | Qt.AlignVCenter,
                           fm.elidedText(_program_title(cur), Qt.ElideRight, w))
                bar = QRectF(row.x() + 64, row.y() + 19, w, 3)
                p.setPen(Qt.NoPen)
                p.setBrush(QColor(255, 255, 255, 50))
                p.drawRoundedRect(bar, 1.5, 1.5)
                done = max(0.0, min(1.0, (t - cur.start) / max(1, cur.end - cur.start)))
                p.setBrush(QColor("#7DFF9A"))
                p.drawRoundedRect(QRectF(bar.x(), bar.y(), bar.width() * done, bar.height()), 1.5, 1.5)
                f.setPixelSize(9)
                p.setFont(f)
                fm = p.fontMetrics()
                until = f"until {_tv_clock(cur.until())}"
                nxt_text = f"   Next: {_program_title(nxt)}" if nxt is not None else ""
                p.setPen(QColor("#BBBBBB"))
                p.drawText(QRectF(row.x() + 64, row.y() + 22, w, 12), Qt.AlignLeft | Qt.AlignVCenter,
                           fm.elidedText(until + nxt_text, Qt.ElideRight, w))
            elif nxt is not None:
                p.setPen(QColor("#FFFFFF"))
                p.drawText(QRectF(row.x() + 64, row.y() + 3, w, 15), Qt.AlignLeft | Qt.AlignVCenter,
                           fm.elidedText(f"Up next: {_program_title(nxt)}", Qt.ElideRight, w))
                f.setPixelSize(9)
                p.setFont(f)
                p.setPen(QColor("#FFB27A"))
                p.drawText(QRectF(row.x() + 64, row.y() + 19, w, 13), Qt.AlignLeft | Qt.AlignVCenter,
                           f"Commercial break – starts {_tv_clock(nxt.when())}")
            else:
                p.setPen(QColor("#888888"))
                p.drawText(QRectF(row.x() + 64, row.y() + 3, w, 15), Qt.AlignLeft | Qt.AlignVCenter, "Off the air")
            f.setPixelSize(11)
            p.setFont(f)
            y += self.ROW


# ---- XP's Copilot Widgets that 7 had no gadget for ------------------------------------------------------------------
# The same widgets as XP's (claudexp.programs.copilot_widgets.widgets) - their readings and their drawing - each in a
# gadget: a hidden XP widget keeps sampling, and the gadget draws it on Windows 7's dark glass in 7's colours (put in
# the XP widgets' module only while it draws, so XP's own Copilot Widgets on this computer keep their theme).
SEVEN = {"top": "#3C3C3C", "bottom": "#141414", "edge": "#FFFFFF", "text": "#FFFFFF", "accent": "#7FD0FF",
         "soft": "#D6E2EE", "dim": "#9AA7B4", "in": "#FF6E6E", "out": "#6EE89A"}
_COLOURS = ("THEME", "WHITE", "GOLD", "SOFT", "DIM", "IN_RED", "OUT_GREEN")


class _WidgetHost:
    """What an XP widget asks of its controller: the desktop, the settings (Copilot Widgets' own on this computer -
    where you are, the hemisphere - with the gadget's few choices on top), and saving them."""

    def __init__(self, gadget):
        from claudexp.programs.copilot_widgets import DEFAULTS, SETTINGS_FILE
        from claudexp.programs.people import load_json
        self.gadget = gadget
        self.desktop = gadget                      # (the XP widget's parent: it goes when the gadget does)
        saved = load_json(SETTINGS_FILE, {})
        self.settings = {**DEFAULTS, **{k: v for k, v in (saved if isinstance(saved, dict) else {}).items()
                                        if k in DEFAULTS}}
        self.settings.update(locked=True, opacity=100, **(gadget.data.get("settings") or {}))

    def save(self):
        self.gadget.data["settings"] = {"real_moon": self.settings.get("real_moon", True)}
        self.gadget.gadgets.save()

    def clamp(self, widget, pos):
        return pos

    def remember(self, widget):
        pass

    def widget_menu(self, widget, pos):
        pass


class XPWidgetGadget(Gadget):
    XP = ""                                        # the XP widget's class name in copilot_widgets.widgets

    def __init__(self, gadgets, data):
        from claudexp.programs.copilot_widgets import widgets as W
        super().__init__(gadgets, data)
        self.W = W
        self.host = _WidgetHost(self)
        self.inner = getattr(W, self.XP)(self.host)
        self.inner.hide()                          # (it samples; the gadget shows it)
        self.inner.start()

    def deleteLater(self):                         # (closed: its sampling stops - the AI widget's thread too)
        if isValid(self.inner):
            self.inner.stop()
        super().deleteLater()

    def draw(self, p):
        W = self.W
        before = {k: getattr(W, k) for k in _COLOURS}
        W.THEME = SEVEN
        W.WHITE, W.GOLD, W.SOFT, W.DIM = (QColor(SEVEN[k]) for k in ("text", "accent", "soft", "dim"))
        W.IN_RED, W.OUT_GREEN = QColor(SEVEN["in"]), QColor(SEVEN["out"])
        try:
            r = QRectF(self.rect()).adjusted(1, 1, -1, -1)
            self.glass(p, r, dark=True)
            p.save()
            self.inner.draw(p, QRectF(self.rect()))
            p.restore()
        finally:
            for k, v in before.items():
                setattr(W, k, v)

    def mousePressEvent(self, event):
        self._pressed_at = self.pos()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        clicked = event.button() == Qt.LeftButton and self.drag is not None \
            and self.pos() == getattr(self, "_pressed_at", None)
        super().mouseReleaseEvent(event)
        if clicked:                                 # (a click, not a drag: the widget's own click - the sky's year)
            self.inner.clicked(event.position())
            self.update()


class SkyGadget(XPWidgetGadget):
    NAME, XP, SIZE, TICK = "Day and Night", "SkyWidget", (330, 190), 30000


class AlmanacGadget(XPWidgetGadget):
    NAME, XP, SIZE, TICK = "Sun and Moon", "AlmanacWidget", (250, 142), 60000


class SystemGadget(XPWidgetGadget):
    NAME, XP, SIZE, TICK = "System Monitor", "SystemWidget", (260, 330), 1000


class NetworkGadget(XPWidgetGadget):
    NAME, XP, SIZE, TICK = "Network Meter", "NetworkWidget", (250, 100), 1000


class AIGadget(XPWidgetGadget):
    NAME, XP, SIZE, TICK = "LLM Activity", "LLMWidget", (250, 100), 1000


KINDS = {"Clock": ClockGadget, "Calendar": CalendarGadget, "CPU Meter": CpuGadget, "Weather": WeatherGadget,
         "Slide Show": SlideShowGadget, "Feed Headlines": FeedGadget, "E-mail": MailGadget,
         "TV Guide": TVGadget, "Day and Night": SkyGadget, "Sun and Moon": AlmanacGadget,
         "System Monitor": SystemGadget, "Network Meter": NetworkGadget, "LLM Activity": AIGadget}


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

    def spot(self, size):
        """The first free place for a gadget of this size: down the right-hand column, then the next column left."""
        area = self.desktop.work_area()
        w, h = size
        x = area.width() - w - 20
        while x >= 0:
            column = sorted((g for g in self.live() if g.x() < x + w and g.x() + g.width() > x), key=lambda g: g.y())
            y = 20
            for g in column:
                if y + h <= g.y():
                    break
                y = max(y, g.y() + g.height() + 12)
            if y + h <= area.height() - 8:
                return x, y
            x -= w + 20
        return 20, 20

    def add(self, kind):
        cls = KINDS[kind]
        x, y = self.spot(cls.SIZE)
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
               "Slide Show": "#F5F5F5", "Feed Headlines": "#3A3A3A", "E-mail": "#3B78C9", "TV Guide": "#1B2A41",
               "Day and Night": "#1F3A6E", "Sun and Moon": "#2B2B44", "System Monitor": "#2A2A2A",
               "Network Meter": "#22313A", "LLM Activity": "#33263F"}
    p.setPen(QPen(QColor(0, 0, 0, 90), 1))
    p.setBrush(QColor(colours.get(kind, "#CCCCCC")))
    p.drawRoundedRect(QRectF(4, 8, size - 8, size - 16), 8, 8)
    f = QFont("Segoe UI")
    f.setPixelSize(11)
    p.setFont(f)
    white = ("Calendar", "CPU Meter", "Weather", "Feed Headlines", "E-mail", "TV Guide", "Day and Night",
             "Sun and Moon", "System Monitor", "Network Meter", "LLM Activity")
    p.setPen(QColor("white" if kind in white else "#1E1E1E"))
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
