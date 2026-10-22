"""Widgets, Windows 11 style: the board that slides in from the left (the weather button at the taskbar's left
corner, or Win+W) with its cards - Weather, Calendar, Outlook (your inbox), the TV Guide, Top stories (your friends'
posts), Photos, Performance and a Clock. 'Add widgets' picks which cards you keep (data/widgets.json)."""
import datetime
import json
import math
import random

from PySide6.QtCore import QPointF, QRect, QRectF, QSize, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QIcon, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap, QRadialGradient
from PySide6.QtWidgets import (QGridLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QMenu, QPushButton,
                               QScrollArea, QVBoxLayout, QWidget)
from shiboken6 import isValid

from .. import clock, sound
from ..paths import DATA
from ..wm import MicaWindow

WIDGETS_FILE = DATA / "widgets.json"
CARD_W, SMALL_H, LARGE_H, GAP = 300, 150, 316, 16
DEFAULT_CARDS = ["Weather", "Calendar", "Outlook", "TV Guide", "Top stories", "Photos"]
_controller = None
CONDITIONS = ["Sunny", "Partly Cloudy", "Cloudy", "Showers", "Clear"]


def _font(size=12, bold=False):
    from ..style import font
    return font(size, QFont.DemiBold if bold else QFont.Normal)


def weather_now():
    """(temperature F, condition) for this hour: the same make-believe forecast everywhere on the computer."""
    now = clock.now()
    seed = now.timetuple().tm_yday * 24 + now.hour
    rnd = random.Random(seed)
    cond = rnd.choice(CONDITIONS)
    temp = 48 + int(10 * math.sin(now.hour / 24 * 2 * math.pi - 1.5)) + rnd.randint(-3, 3)
    return temp, cond


class Card(QWidget):
    """A widget card: a white rounded tile with its title row (icon, name, the '...' menu) and a drawn body."""
    NAME = "Card"
    LARGE = False
    TICK = 1000
    COLOUR = "#0067C0"

    def __init__(self, board, data):
        super().__init__()
        self.board = board
        self.data = data
        self.hover_menu = False
        self.setMouseTracking(True)
        self.setFixedSize(CARD_W, LARGE_H if self.LARGE else SMALL_H)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(self.TICK)

    @property
    def desktop(self):
        return self.board.desktop

    def body_rect(self):
        return QRectF(0, 36, self.width(), self.height() - 36)

    def _menu_rect(self):
        return QRect(self.width() - 36, 6, 28, 24)

    def icon_pixmap(self, size=16):
        return kind_pixmap(self.NAME, size)

    def mouseMoveEvent(self, event):
        hot = self._menu_rect().contains(event.position().toPoint())
        if hot != self.hover_menu:
            self.hover_menu = hot
            self.update()

    def leaveEvent(self, event):
        self.hover_menu = False
        self.update()

    def mousePressEvent(self, event):
        pos = event.position().toPoint()
        if event.button() == Qt.RightButton or (event.button() == Qt.LeftButton and self._menu_rect().contains(pos)):
            from ..shims import MENU_CSS
            menu = QMenu(self)
            menu.setStyleSheet(MENU_CSS)
            menu.addAction("Unpin widget", lambda: self.board.remove(self))
            menu.addAction("Add widgets...", lambda: open_gallery(self.desktop))
            menu.popup(event.globalPosition().toPoint())
            return
        if event.button() == Qt.LeftButton and self.body_rect().contains(QPointF(pos)):
            self.clicked(pos)

    def clicked(self, pos):
        pass

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        p.setPen(QPen(QColor(0, 0, 0, 26), 1))
        p.setBrush(QColor(255, 255, 255, 236))
        p.drawRoundedRect(r, 8, 8)
        p.drawPixmap(14, 10, self.icon_pixmap(16))
        p.setFont(_font(12, bold=True))
        p.setPen(QColor("#1A1A1A"))
        p.drawText(QRect(38, 6, self.width() - 80, 24), Qt.AlignVCenter | Qt.AlignLeft, self.NAME)
        mr = self._menu_rect()
        if self.hover_menu:
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(0, 0, 0, 16))
            p.drawRoundedRect(QRectF(mr), 4, 4)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#5C5C5C"))
        for dx in (-5, 0, 5):
            p.drawEllipse(QPointF(mr.center().x() + dx, mr.center().y()), 1.5, 1.5)
        p.save()
        p.setClipRect(self.body_rect())
        self.draw(p, self.body_rect())
        p.restore()

    def draw(self, p, r):
        pass


class ClockCard(Card):
    NAME = "Clock"
    COLOUR = "#2E3A48"

    def draw(self, p, r):
        now = clock.now()
        d = min(r.width(), r.height()) - 16
        face = QRectF(r.x() + 20, r.y() + (r.height() - d) / 2, d, d)
        g = QRadialGradient(face.center(), d / 2)
        g.setColorAt(0, QColor("#FFFFFF"))
        g.setColorAt(1, QColor("#E6ECF4"))
        p.setPen(QPen(QColor("#2E3A48"), 2))
        p.setBrush(g)
        p.drawEllipse(face)
        c = face.center()
        rad = d / 2
        p.setPen(QPen(QColor("#2E3A48"), 1.5))
        for i in range(12):
            a = math.radians(i * 30)
            inner = rad - (8 if i % 3 == 0 else 4)
            p.drawLine(QPointF(c.x() + math.sin(a) * inner, c.y() - math.cos(a) * inner),
                       QPointF(c.x() + math.sin(a) * (rad - 2), c.y() - math.cos(a) * (rad - 2)))
        for length, width, angle, colour in ((rad * 0.5, 3, (now.hour % 12 + now.minute / 60) * 30, "#1E2835"),
                                             (rad * 0.72, 2, now.minute * 6 + now.second / 10, "#1E2835"),
                                             (rad * 0.8, 1, now.second * 6, "#D23B2E")):
            a = math.radians(angle)
            p.setPen(QPen(QColor(colour), width, Qt.SolidLine, Qt.RoundCap))
            p.drawLine(c, QPointF(c.x() + math.sin(a) * length, c.y() - math.cos(a) * length))
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#1E2835"))
        p.drawEllipse(c, 3, 3)
        from ..style import display_family
        f = QFont(display_family())
        f.setPixelSize(34)
        f.setWeight(QFont.Light)
        p.setFont(f)
        p.setPen(QColor("#1A1A1A"))
        p.drawText(QRectF(face.right() + 16, r.y() + 10, r.width() - face.right() - 20, 44), Qt.AlignLeft | Qt.AlignVCenter,
                   clock.time_text(now))
        p.setFont(_font(12))
        p.setPen(QColor("#5C5C5C"))
        p.drawText(QRectF(face.right() + 18, r.y() + 56, r.width() - face.right() - 20, 20), Qt.AlignLeft,
                   clock.long_date_text(now))


class CalendarCard(Card):
    NAME = "Calendar"
    LARGE = True
    TICK = 60000
    COLOUR = "#0067C0"

    def draw(self, p, r):
        import calendar
        now = clock.now()
        p.setFont(_font(13, bold=True))
        p.setPen(QColor("#1A1A1A"))
        p.drawText(QRectF(r.x() + 16, r.y() + 2, r.width() - 32, 24), Qt.AlignLeft | Qt.AlignVCenter,
                   f"{now:%A, %B} {now.day}")
        cell_w = (r.width() - 32) / 7
        y = r.y() + 34
        p.setFont(_font(11))
        for i, d in enumerate(("Su", "Mo", "Tu", "We", "Th", "Fr", "Sa")):
            p.setPen(QColor("#5C5C5C"))
            p.drawText(QRectF(r.x() + 16 + i * cell_w, y, cell_w, 18), Qt.AlignCenter, d)
        first = now.replace(day=1)
        start_col = (first.weekday() + 1) % 7
        days = calendar.monthrange(now.year, now.month)[1]
        y += 22
        row_h = 32
        p.setFont(_font(12))
        for day in range(1, days + 1):
            col = (start_col + day - 1) % 7
            row = (start_col + day - 1) // 7
            cell = QRectF(r.x() + 16 + col * cell_w, y + row * row_h, cell_w, row_h)
            if day == now.day:
                from .. import display
                p.setPen(Qt.NoPen)
                p.setBrush(display.get().accent())
                p.drawEllipse(cell.center(), 14, 14)
                p.setPen(QColor("white"))
            else:
                p.setPen(QColor("#1A1A1A"))
            p.drawText(cell, Qt.AlignCenter, str(day))
        p.setFont(_font(11))
        p.setPen(QColor("#5C5C5C"))
        p.drawText(QRectF(r.x() + 16, r.bottom() - 26, r.width() - 32, 18), Qt.AlignLeft | Qt.AlignVCenter,
                   p.fontMetrics().elidedText("No events today. Sign in to Outlook to see your calendar.",
                                              Qt.ElideRight, int(r.width() - 32)))


class PerformanceCard(Card):
    NAME = "Performance"
    COLOUR = "#2E2E2E"

    def __init__(self, board, data):
        super().__init__(board, data)
        self.cpu, self.ram = 9.0, 34.0

    def _sample(self):
        try:
            import psutil
            self.cpu = psutil.cpu_percent(interval=None)
            self.ram = psutil.virtual_memory().percent
        except Exception:
            self.cpu = max(2.0, min(95.0, self.cpu + random.uniform(-6, 6)))
            self.ram = max(20.0, min(90.0, self.ram + random.uniform(-1, 1)))

    def draw(self, p, r):
        self._sample()
        from .. import display
        accent = display.get().accent()
        for i, (label, value, colour) in enumerate((("CPU", self.cpu, accent), ("Memory", self.ram, QColor("#10893E")))):
            cx = r.x() + 70 + i * 150
            cy = r.center().y() + 2
            rad = 38
            p.setPen(QPen(QColor(0, 0, 0, 20), 7))
            p.setBrush(Qt.NoBrush)
            p.drawArc(QRectF(cx - rad, cy - rad, 2 * rad, 2 * rad), 225 * 16, -270 * 16)
            p.setPen(QPen(colour, 7, Qt.SolidLine, Qt.RoundCap))
            p.drawArc(QRectF(cx - rad, cy - rad, 2 * rad, 2 * rad), 225 * 16, int(-270 * 16 * value / 100))
            p.setFont(_font(16, bold=True))
            p.setPen(QColor("#1A1A1A"))
            p.drawText(QRectF(cx - rad, cy - 12, 2 * rad, 24), Qt.AlignCenter, f"{int(value)}%")
            p.setFont(_font(11))
            p.setPen(QColor("#5C5C5C"))
            p.drawText(QRectF(cx - rad, cy + 14, 2 * rad, 16), Qt.AlignCenter, label)
        p.setFont(_font(11))
        p.setPen(QColor("#5C5C5C"))
        p.drawText(QRectF(r.x() + 16, r.bottom() - 22, r.width() - 32, 16), Qt.AlignLeft,
                   "Ryzen 7 7800X3D  ·  32 GB DDR5")


class WeatherCard(Card):
    NAME = "Weather"
    COLOUR = "#58A6E8"

    def draw(self, p, r):
        temp, cond = weather_now()
        from ..taskbar import weather_glyph
        g = QLinearGradient(r.topLeft(), r.bottomLeft())
        g.setColorAt(0, QColor("#58A6E8"))
        g.setColorAt(1, QColor("#1F5FA8"))
        path = QPainterPath()
        path.addRoundedRect(QRectF(r.x() + 0.5, r.y(), r.width() - 1, r.height() - 0.5), 8, 8)
        path.addRect(QRectF(r.x() + 0.5, r.y(), r.width() - 1, 12))
        p.setPen(Qt.NoPen)
        p.setBrush(g)
        p.drawPath(path.simplified())
        p.save()
        p.scale(1.8, 1.8)
        weather_glyph(p, QRect(int((r.x() + 20) / 1.8), int((r.y() + 26) / 1.8), 32, 32), cond)
        p.restore()
        from ..style import display_family
        f = QFont(display_family())
        f.setPixelSize(40)
        f.setWeight(QFont.Light)
        p.setFont(f)
        p.setPen(QColor("white"))
        p.drawText(QRectF(r.x() + 110, r.y() + 14, 160, 48), Qt.AlignLeft | Qt.AlignVCenter, f"{temp}°F")
        p.setFont(_font(13))
        p.drawText(QRectF(r.x() + 112, r.y() + 58, 170, 16), Qt.AlignLeft, cond)
        p.setFont(_font(11))
        p.setPen(QColor(255, 255, 255, 210))
        p.drawText(QRectF(r.x() + 112, r.y() + 76, 170, 14), Qt.AlignLeft, "Seattle, WA  ·  Updated just now")
        hi, lo = temp + 6, temp - 9
        p.drawText(QRectF(r.x() + 16, r.bottom() - 18, r.width() - 32, 14), Qt.AlignLeft,
                   f"H {hi}°  L {lo}°   ·   Tomorrow: {CONDITIONS[(CONDITIONS.index(cond) + 1) % 5]}")


class PhotosCard(Card):
    NAME = "Photos"
    TICK = 8000
    COLOUR = "#F5F5F5"

    def __init__(self, board, data):
        super().__init__(board, data)
        self.index = 0
        self.pixmaps = None

    def _pictures(self):
        if self.pixmaps is None:
            try:
                from ..controlpanel import _found_pictures
                self.pixmaps = [QPixmap(str(path)) for path in _found_pictures()[:40]]
            except Exception:
                self.pixmaps = []
            self.pixmaps = [pm for pm in self.pixmaps if not pm.isNull()]
        return self.pixmaps

    def clicked(self, pos):
        try:
            from claudexp import programs
            programs.launch(self.desktop, "photos")
        except Exception:
            pass

    def draw(self, p, r):
        pics = self._pictures()
        inner = r.adjusted(12, 4, -12, -12)
        if not pics:
            p.setFont(_font(12))
            p.setPen(QColor("#5C5C5C"))
            p.drawText(inner, Qt.AlignCenter | Qt.TextWordWrap, "Your Pictures library is empty. Add pictures and "
                       "they show up here, one at a time.")
            return
        self.index = (self.index + 1) % len(pics)
        pm = pics[self.index].scaled(inner.size().toSize(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        path = QPainterPath()
        path.addRoundedRect(inner, 6, 6)
        p.setClipPath(path)
        p.drawPixmap(int(inner.x() + (inner.width() - pm.width()) / 2), int(inner.y() + (inner.height() - pm.height()) / 2), pm)


class FeedCard(Card):
    """Top stories: the latest from your friends' journals and walls."""
    NAME = "Top stories"
    LARGE = True
    TICK = 60000
    COLOUR = "#3A3A3A"

    def __init__(self, board, data):
        super().__init__(board, data)
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
            self.items = found[:7]
        except Exception:
            self.items = []

    def clicked(self, pos):
        try:
            from .browsers import open_url
            open_url(self.desktop, "http://www.facebook.com/")
        except Exception:
            pass

    def draw(self, p, r):
        if not self.items or self.data.get("_ticks", 0) % 5 == 0:
            self._refresh()
        self.data["_ticks"] = self.data.get("_ticks", 0) + 1
        y = r.y() + 4
        if not self.items:
            p.setFont(_font(12))
            p.setPen(QColor("#5C5C5C"))
            p.drawText(QRectF(r.x() + 16, y + 8, r.width() - 32, 60), Qt.TextWordWrap,
                       "Nothing new yet. Your friends' posts appear here as they write them.")
            return
        for _id, name, text in self.items:
            row = QRectF(r.x() + 12, y, r.width() - 24, 38)
            p.setFont(_font(12, bold=True))
            p.setPen(QColor("#1A1A1A"))
            p.drawText(QRectF(row.x() + 4, row.y(), row.width() - 8, 18), Qt.AlignLeft | Qt.AlignVCenter, name)
            p.setFont(_font(11))
            p.setPen(QColor("#5C5C5C"))
            line = text.strip().splitlines()[0] if text.strip() else ""
            p.drawText(QRectF(row.x() + 4, row.y() + 18, row.width() - 8, 16), Qt.AlignLeft | Qt.AlignVCenter,
                       p.fontMetrics().elidedText(line, Qt.ElideRight, int(row.width() - 8)))
            p.setPen(QPen(QColor(0, 0, 0, 16), 1))
            p.drawLine(QPointF(row.x(), row.bottom() + 1), QPointF(row.right(), row.bottom() + 1))
            y += 40
            if y + 36 > r.bottom():
                break


class MailCard(Card):
    """Outlook: the unread count and the newest mail; click one to read it in Outlook."""
    NAME = "Outlook"
    TICK = 15000
    COLOUR = "#0F6CBD"
    ROW = 28

    def __init__(self, board, data):
        super().__init__(board, data)
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
        self.items = msgs[:3]

    def _arrived(self):
        if isValid(self):
            self._refresh()
            self.update()

    def clicked(self, pos):
        message = None
        for rect, m in self._hits:
            if rect.contains(QPointF(pos)):
                message = m
        try:
            from claudexp.programs import outlook
            win = outlook.open_outlook(self.desktop)
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

    def draw(self, p, r):
        self.data["_ticks"] = self.data.get("_ticks", 0) + 1
        if self.data["_ticks"] % 2 == 0:
            self._refresh()
        p.setFont(_font(11))
        p.setPen(QColor("#5C5C5C"))
        p.drawText(QRectF(r.x() + 16, r.y() - 2, r.width() - 32, 18), Qt.AlignLeft | Qt.AlignVCenter,
                   f"Inbox  ·  {self.unread} unread" if self.unread else "Inbox  ·  no new mail")
        self._hits = []
        y = r.y() + 18
        if not self.items:
            p.setPen(QColor("#5C5C5C"))
            p.drawText(QRectF(r.x() + 16, y + 10, r.width() - 32, 60), Qt.TextWordWrap,
                       "Your inbox is empty. Mail from your friends shows up here - click to open Outlook.")
            return
        for m in self.items:
            row = QRectF(r.x() + 10, y, r.width() - 20, self.ROW)
            self._hits.append((row, m))
            unread = not m.get("read")
            if unread:
                from .. import display
                p.setPen(Qt.NoPen)
                p.setBrush(display.get().accent())
                p.drawRoundedRect(QRectF(row.x(), row.y() + 7, 3, row.height() - 14), 1.5, 1.5)
            p.setFont(_font(12, bold=unread))
            p.setPen(QColor("#1A1A1A"))
            sender = p.fontMetrics().elidedText(str(m.get("from", "")), Qt.ElideRight, 100)
            p.drawText(QRectF(row.x() + 10, row.y(), 104, row.height()), Qt.AlignLeft | Qt.AlignVCenter, sender)
            p.setFont(_font(11))
            p.setPen(QColor("#1A1A1A" if unread else "#5C5C5C"))
            subject = p.fontMetrics().elidedText(str(m.get("subject", "")) or "(no subject)", Qt.ElideRight,
                                                 int(row.width() - 124))
            p.drawText(QRectF(row.x() + 118, row.y(), row.width() - 124, row.height()), Qt.AlignLeft | Qt.AlignVCenter,
                       subject)
            y += self.ROW


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


class TVCard(Card):
    """TV Guide: what's on each ClaudeTV channel now and next; click a channel to watch it."""
    NAME = "TV Guide"
    LARGE = True
    TICK = 15000
    COLOUR = "#1B2A41"
    ROW = 44

    def __init__(self, board, data):
        super().__init__(board, data)
        self.channels = None
        self.rows = []
        self.offset = 0
        self._hits = []
        self.setCursor(Qt.PointingHandCursor)
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
        return max(1, int((self.body_rect().height() - 8) // self.ROW))

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

    def wheelEvent(self, event):
        if len(self.rows) > self._shown():
            self.offset = max(0, min(self.offset + (-1 if event.angleDelta().y() > 0 else 1),
                                     len(self.rows) - self._shown()))
            self.update()
            event.accept()

    def clicked(self, pos):
        target = None
        for rect, ch in self._hits:
            if rect.contains(QPointF(pos)):
                target = ch
        try:
            from claudetv import guide, tuner
            if target is None:
                guide.open_guide(self.desktop)
            else:
                tuner.open_tv(self.desktop)
                body = tuner.current()
                if body is not None:
                    body.tune(target)
        except Exception:
            pass

    def draw(self, p, r):
        self._refresh()
        self._hits = []
        y = r.y() + 2
        if self.channels is None:
            p.setFont(_font(12))
            p.setPen(QColor("#5C5C5C"))
            p.drawText(QRectF(r.x() + 16, y + 8, r.width() - 32, 40), Qt.TextWordWrap, "Reading the channel lineup…")
            return
        if not self.rows:
            p.setFont(_font(12))
            p.setPen(QColor("#5C5C5C"))
            p.drawText(QRectF(r.x() + 16, y + 8, r.width() - 32, 60), Qt.TextWordWrap,
                       "No channels are on the air. Open ClaudeTV to set up the video archive.")
            return
        from .. import display
        accent = display.get().accent()
        for ch, cur, nxt, t in self.rows[self.offset:self.offset + self._shown()]:
            row = QRectF(r.x() + 10, y, r.width() - 20, self.ROW)
            self._hits.append((row, ch))
            p.setPen(QPen(QColor(0, 0, 0, 16), 1))
            p.drawLine(QPointF(row.x(), row.y()), QPointF(row.right(), row.y()))
            p.setFont(_font(12, bold=True))
            p.setPen(QColor("#1A1A1A"))
            p.drawText(QRectF(row.x() + 4, row.y() + 4, 64, 18), Qt.AlignLeft | Qt.AlignVCenter,
                       p.fontMetrics().elidedText(ch.label(), Qt.ElideRight, 62))
            w = int(row.width() - 80)
            p.setFont(_font(12))
            if cur is not None:
                p.setPen(QColor("#1A1A1A"))
                p.drawText(QRectF(row.x() + 74, row.y() + 4, w, 18), Qt.AlignLeft | Qt.AlignVCenter,
                           p.fontMetrics().elidedText(_program_title(cur), Qt.ElideRight, w))
                bar = QRectF(row.x() + 74, row.y() + 25, w, 3)
                p.setPen(Qt.NoPen)
                p.setBrush(QColor(0, 0, 0, 24))
                p.drawRoundedRect(bar, 1.5, 1.5)
                done = max(0.0, min(1.0, (t - cur.start) / max(1, cur.end - cur.start)))
                p.setBrush(accent)
                p.drawRoundedRect(QRectF(bar.x(), bar.y(), bar.width() * done, bar.height()), 1.5, 1.5)
                p.setFont(_font(10))
                p.setPen(QColor("#5C5C5C"))
                nxt_text = f"   Next: {_program_title(nxt)}" if nxt is not None else ""
                p.drawText(QRectF(row.x() + 74, row.y() + 29, w, 14), Qt.AlignLeft | Qt.AlignVCenter,
                           p.fontMetrics().elidedText(f"until {_tv_clock(cur.until())}" + nxt_text, Qt.ElideRight, w))
            elif nxt is not None:
                p.setPen(QColor("#1A1A1A"))
                p.drawText(QRectF(row.x() + 74, row.y() + 4, w, 18), Qt.AlignLeft | Qt.AlignVCenter,
                           p.fontMetrics().elidedText(f"Up next: {_program_title(nxt)}", Qt.ElideRight, w))
                p.setFont(_font(10))
                p.setPen(QColor("#C05621"))
                p.drawText(QRectF(row.x() + 74, row.y() + 24, w, 16), Qt.AlignLeft | Qt.AlignVCenter,
                           f"Commercial break – starts {_tv_clock(nxt.when())}")
            else:
                p.setPen(QColor("#8A8A8A"))
                p.drawText(QRectF(row.x() + 74, row.y() + 4, w, 18), Qt.AlignLeft | Qt.AlignVCenter, "Off the air")
            y += self.ROW


KINDS = {"Weather": WeatherCard, "Calendar": CalendarCard, "Outlook": MailCard, "TV Guide": TVCard,
         "Top stories": FeedCard, "Photos": PhotosCard, "Performance": PerformanceCard, "Clock": ClockCard}


def kind_pixmap(kind, size=16):
    """A little coloured tile with the widget's initial, for its title row and the gallery."""
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    cls = KINDS.get(kind)
    colour = QColor(cls.COLOUR if cls else "#0067C0")
    p.setPen(Qt.NoPen)
    p.setBrush(colour)
    p.drawRoundedRect(QRectF(0, 0, size, size), size * 0.25, size * 0.25)
    f = QFont("Segoe UI")
    f.setPixelSize(int(size * 0.6))
    f.setBold(True)
    p.setFont(f)
    light = colour.lightness() > 170
    p.setPen(QColor("#1A1A1A") if light else QColor("white"))
    p.drawText(pm.rect(), Qt.AlignCenter, kind[0])
    p.end()
    return pm


class Board(QWidget):
    """The Widgets board: a tall rounded panel at the left of the screen with the cards in two columns."""

    def __init__(self, widgets):
        super().__init__(widgets.desktop)
        self.widgets = widgets
        self.desktop = widgets.desktop
        self.hover_add = False
        self.setMouseTracking(True)
        self.area = QScrollArea(self)
        self.area.setWidgetResizable(True)
        self.area.setFrameShape(QScrollArea.NoFrame)
        self.area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.area.setStyleSheet("QScrollArea { background: transparent; } QWidget#cards { background: transparent; }"
                                "QScrollBar:vertical { background: transparent; width: 10px; margin: 2px; }"
                                "QScrollBar::handle:vertical { background: rgba(0,0,0,60); border-radius: 3px; min-height: 24px; }"
                                "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }")
        self.container = QWidget()
        self.container.setObjectName("cards")
        self.grid = QGridLayout(self.container)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setHorizontalSpacing(GAP)
        self.grid.setVerticalSpacing(GAP)
        self.grid.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.area.setWidget(self.container)
        self.hide()

    def place(self):
        from ..taskbar import TASKBAR_H
        w = min(2 * CARD_W + GAP + 64, self.desktop.width() - 24)
        h = self.desktop.height() - TASKBAR_H - 24
        self.setGeometry(12, 12, w, h)
        self.area.setGeometry(24, 72, w - 36, h - 84)

    def _add_rect(self):
        return QRect(self.width() - 24 - 110, 20, 110, 32)

    def relayout(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget() is not None:
                item.widget().setParent(None)
        occupied = set()
        row = col = 0
        for card in self.widgets.live():
            span = 2 if card.LARGE else 1
            while (row, col) in occupied:
                col += 1
                if col >= 2:
                    col, row = 0, row + 1
            self.grid.addWidget(card, row, col, span, 1)
            for i in range(span):
                occupied.add((row + i, col))
            card.show()
        self.grid.setRowStretch(row + 3, 1)

    def mouseMoveEvent(self, event):
        hot = self._add_rect().contains(event.position().toPoint())
        if hot != self.hover_add:
            self.hover_add = hot
            self.update()

    def mousePressEvent(self, event):
        if self._add_rect().contains(event.position().toPoint()):
            open_gallery(self.desktop)

    def paintEvent(self, event):
        from ..taskbar import draw_panel
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        draw_panel(p, self.rect(), radius=8, alpha=242)
        now = clock.now()
        greeting = "Good morning" if now.hour < 12 else "Good afternoon" if now.hour < 18 else "Good evening"
        from ..user import draw_user_picture, user_name
        draw_user_picture(p, QRect(24, 20, 32, 32), circle=True)
        p.setFont(_font(16, bold=True))
        p.setPen(QColor("#1A1A1A"))
        p.drawText(QRect(68, 20, 300, 32), Qt.AlignVCenter | Qt.AlignLeft, f"{greeting}, {user_name()}")
        ar = self._add_rect()
        p.setPen(QPen(QColor(0, 0, 0, 30), 1))
        p.setBrush(QColor(255, 255, 255, 220 if self.hover_add else 160))
        p.drawRoundedRect(QRectF(ar).adjusted(0.5, 0.5, -0.5, -0.5), 4, 4)
        p.setFont(_font(12))
        p.setPen(QColor("#1A1A1A"))
        p.drawText(ar, Qt.AlignCenter, "+  Add widgets")


class Widgets:
    def __init__(self, desktop):
        self.desktop = desktop
        self.cards = []
        self.board = None
        self.loaded = False

    def _ensure_board(self):
        if self.board is None:
            self.board = Board(self)
        return self.board

    def load(self):
        if self.loaded:
            return
        self.loaded = True
        self._ensure_board()
        try:
            data = json.loads(WIDGETS_FILE.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            data = {}
        kinds = data.get("cards", DEFAULT_CARDS)
        for kind in kinds:
            cls = KINDS.get(kind)
            if cls is not None:
                self.cards.append(cls(self.board, {"kind": kind}))
        self.board.relayout()

    def save(self):
        try:
            WIDGETS_FILE.parent.mkdir(parents=True, exist_ok=True)
            WIDGETS_FILE.write_text(json.dumps({"cards": [c.NAME for c in self.live()]}, indent=2), encoding="utf-8")
        except OSError:
            pass

    def live(self):
        self.cards = [c for c in self.cards if isValid(c)]
        return self.cards

    def kinds(self):
        return [c.NAME for c in self.live()]

    def add(self, kind):
        cls = KINDS[kind]
        self.load()
        if kind in self.kinds():
            return
        self.cards.append(cls(self.board, {"kind": kind}))
        self.board.relayout()
        self.save()
        sound.play("default")

    def remove(self, card):
        if isinstance(card, str):
            card = next((c for c in self.live() if c.NAME == card), None)
            if card is None:
                return
        if card in self.cards:
            self.cards.remove(card)
        card.hide()
        card.setParent(None)
        card.deleteLater()
        if self.board is not None:
            self.board.relayout()
        self.save()

    # ---- the board ----
    def toggle_board(self):
        self.load()
        if self.board.isVisible():
            self.hide_board()
        else:
            self.board.place()
            self.board.show()
            self.board.raise_()
            self.desktop.taskbar.update()

    def hide_board(self):
        if self.board is not None and self.board.isVisible():
            self.board.hide()
            self.desktop.taskbar.update()

    def raise_all(self):
        if self.board is not None and self.board.isVisible():
            self.board.raise_()

    restack = raise_all

    def on_resize(self):
        if self.board is not None and self.board.isVisible():
            self.board.place()

    def show_all(self):
        self.load()

    def hide_all(self):
        self.hide_board()


def install(desktop):
    global _controller
    _controller = Widgets(desktop)
    desktop.widgets = _controller
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
    return kind_pixmap(kind, size)


_gallery = {}


def open_gallery(desktop):
    """Add widgets: the list of cards, with Add and Remove."""
    win = _gallery.get("win")
    if win is not None and isValid(win) and win in desktop.windows:
        desktop.activate(win)
        return
    ctl = _get(desktop)
    body = QWidget()
    body.setStyleSheet("background: #F3F3F3;")
    v = QVBoxLayout(body)
    v.setContentsMargins(16, 12, 16, 12)
    head = QLabel("Add widgets")
    head.setStyleSheet("font-family: 'Segoe UI Variable Text', 'Segoe UI'; font-size: 18px; font-weight: 600;")
    v.addWidget(head)
    lst = QListWidget()
    lst.setIconSize(QSize(32, 32))
    lst.setStyleSheet("QListWidget { border: none; background: white; border-radius: 6px; font-family: 'Segoe UI'; "
                      "font-size: 13px; } QListWidget::item { height: 44px; padding-left: 6px; }"
                      "QListWidget::item:selected { background: #E5E5E5; color: #1A1A1A; }")
    for kind in KINDS:
        it = QListWidgetItem(QIcon(kind_pixmap(kind, 32)), kind + ("   (pinned)" if kind in ctl.kinds() else ""))
        it.setData(Qt.UserRole, kind)
        lst.addItem(it)
    v.addWidget(lst, 1)
    row = QHBoxLayout()
    hint = QLabel("Pick a widget, then Add or Remove it from the board.")
    hint.setStyleSheet("font-family: 'Segoe UI'; font-size: 12px; color: #5C5C5C;")
    row.addWidget(hint, 1)
    css = ("QPushButton { font-family: 'Segoe UI'; font-size: 12px; padding: 5px 18px; border-radius: 4px; "
           "background: #FBFBFB; border: 1px solid #D0D0D0; } QPushButton:hover { background: #F0F0F0; }")
    add, remove = QPushButton("Add"), QPushButton("Remove")
    for b in (add, remove):
        b.setStyleSheet(css)
        row.addWidget(b)
    v.addLayout(row)

    def refresh():
        for i in range(lst.count()):
            it = lst.item(i)
            kind = it.data(Qt.UserRole)
            it.setText(kind + ("   (pinned)" if kind in ctl.kinds() else ""))

    def add_current(*_):
        it = lst.currentItem()
        if it is not None:
            ctl.add(it.data(Qt.UserRole))
            refresh()

    def remove_current(*_):
        it = lst.currentItem()
        if it is not None:
            ctl.remove(it.data(Qt.UserRole))
            refresh()
    lst.itemDoubleClicked.connect(add_current)
    add.clicked.connect(add_current)
    remove.clicked.connect(remove_current)
    from . import widget_icon
    win = MicaWindow(desktop, "Widgets", body, widget_icon(), (480, 440))
    _gallery["win"] = win
    desktop.open_window(win)
    sound.play("navigate")
