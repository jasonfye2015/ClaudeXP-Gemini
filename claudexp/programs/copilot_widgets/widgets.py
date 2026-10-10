"""The desktop widgets: Clock, Calendar, Weather, TV Guide, Almanac, System Monitor and Sticky Note."""
import calendar
import ctypes
import os
import shutil
from datetime import date, datetime, timedelta
from time import monotonic

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QFontMetrics, QLinearGradient, QPainter, QPen
from PySide6.QtWidgets import QMenu, QPlainTextEdit, QPushButton, QWidget

from ... import clock
from ...paths import DATA
from . import art, weather as wx

WHITE = QColor("white")
GOLD = QColor("#FFE070")
SOFT = QColor("#C9DAFF")
DIM = QColor("#93AAD8")
MENU_STYLE = ("QMenu { background: white; border: 1px solid #ACA899; font-family: Tahoma; font-size: 11px; }"
              "QMenu::item { padding: 4px 24px 4px 20px; }"
              "QMenu::item:selected { background: #316AC5; color: white; }")


def _font(px, bold=False):
    f = QFont("Tahoma")
    f.setPixelSize(px)
    f.setBold(bold)
    return f


def _text(p, x, y, w, h, text, px, color=WHITE, bold=False, align=Qt.AlignLeft | Qt.AlignVCenter, elide=True):
    p.setFont(_font(px, bold))
    p.setPen(color)
    if elide:
        text = QFontMetrics(p.font()).elidedText(text, Qt.ElideRight, int(w))
    p.drawText(QRectF(x, y, w, h), align, text)


def _bar(p, rect, frac, color):
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(0, 0, 0, 90))
    p.drawRoundedRect(rect, rect.height() / 2, rect.height() / 2)
    frac = max(0.0, min(1.0, frac))
    if frac > 0:
        p.setBrush(color)
        p.drawRoundedRect(QRectF(rect.x(), rect.y(), max(rect.height(), rect.width() * frac), rect.height()),
                          rect.height() / 2, rect.height() / 2)


class WidgetBase(QWidget):
    """A floating translucent panel on the desktop. Unlocked widgets can be dragged; locked ones stay put."""
    KEY = ""
    TITLE = ""
    SIZE = (240, 120)
    REFRESH_MS = 1000

    def __init__(self, controller):
        super().__init__(controller.desktop)
        self.c = controller
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.resize(*self.SIZE)
        self._press = None
        self._origin = None
        self._moved = False
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.refresh)

    def start(self):
        self.refresh()
        self._timer.start(self.REFRESH_MS)

    def stop(self):
        self._timer.stop()

    def refresh(self):
        self.update()

    def clicked(self, pos):
        pass

    def alpha(self):
        return int(self.c.settings["opacity"] * 2.55)

    def background(self, p, r):
        a = self.alpha()
        grad = QLinearGradient(r.topLeft(), r.bottomLeft())
        grad.setColorAt(0, QColor(46, 101, 214, a))
        grad.setColorAt(1, QColor(14, 46, 128, a))
        p.setPen(QPen(QColor(255, 255, 255, min(255, a // 2 + 50)), 1))
        p.setBrush(grad)
        p.drawRoundedRect(r, 10, 10)

    def draw(self, p, r):
        pass

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        self.background(p, r)
        self.draw(p, r)
        if not self.c.settings["locked"]:
            pen = QPen(GOLD, 1.5, Qt.DashLine)
            p.setPen(pen)
            p.setBrush(Qt.NoBrush)
            p.drawRoundedRect(r.adjusted(1, 1, -1, -1), 9, 9)
            _text(p, r.right() - 70, r.bottom() - 16, 66, 14, "drag me", 10, GOLD, align=Qt.AlignRight)

    # ---- mouse --------------------------------------------------------------------------------------------
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._press = event.globalPosition().toPoint()
            self._origin = self.pos()
            self._moved = False

    def mouseMoveEvent(self, event):
        if self._press is None or self.c.settings["locked"]:
            return
        delta = event.globalPosition().toPoint() - self._press
        if not self._moved and delta.manhattanLength() < 4:
            return
        self._moved = True
        self.move(self.c.clamp(self, self._origin + delta))

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.LeftButton or self._press is None:
            return
        moved, self._press = self._moved, None
        if moved:
            self.c.remember(self)
        else:
            self.clicked(event.position())

    def contextMenuEvent(self, event):
        self.c.widget_menu(self, event.globalPos())


# ---- clock -------------------------------------------------------------------------------------------------
class ClockWidget(WidgetBase):
    KEY, TITLE, SIZE = "clock", "Digital Clock", (250, 104)

    def draw(self, p, r):
        now = clock.now()
        if self.c.settings["clock_24h"]:
            main, suffix = f"{now:%H:%M}", ""
        else:
            main, suffix = f"{now.hour % 12 or 12}:{now:%M}", "AM" if now.hour < 12 else "PM"
        p.setFont(_font(46, True))
        width = QFontMetrics(p.font()).horizontalAdvance(main)
        p.setPen(QColor(0, 0, 0, 90))
        p.drawText(QPointF(17, 57), main)
        p.setPen(WHITE)
        p.drawText(QPointF(16, 56), main)
        x = 16 + width + 6
        _text(p, x, 24, 60, 20, f":{now:%S}", 20, GOLD, True)
        if suffix:
            _text(p, x, 44, 40, 16, suffix, 13, SOFT, True)
        _text(p, 16, 66, r.width() - 28, 18, clock.long_date_text(now), 13, GOLD)
        week = now.isocalendar()[1]
        _text(p, 16, 82, r.width() - 28, 16, f"Week {week}  \u00B7  Day {now.timetuple().tm_yday} of 365", 11, DIM)

    def clicked(self, pos):
        self.c.settings["clock_24h"] = not self.c.settings["clock_24h"]
        self.c.save()
        self.update()


# ---- calendar ----------------------------------------------------------------------------------------------
def _nth(year, month, weekday, n):
    d = date(year, month, 1)
    return d + timedelta((weekday - d.weekday()) % 7 + 7 * (n - 1))


def _last(year, month, weekday):
    d = date(year + (month == 12), month % 12 + 1, 1) - timedelta(1)
    return d - timedelta((d.weekday() - weekday) % 7)


def _easter(year):
    a, b, c = year % 19, year // 100, year % 100
    d, e = b // 4, b % 4
    g = (8 * b + 13) // 25
    h = (19 * a + b - d - g + 15) % 30
    j, k = c // 4, c % 4
    m = (a + 11 * h) // 319
    r = (2 * e + 2 * j - k - h + m + 32) % 7
    month = (h - m + r + 90) // 25
    return date(year, month, (h - m + r + month + 19) % 32)


def holidays(year):
    return {
        date(year, 1, 1): "New Year's Day", _nth(year, 1, 0, 3): "Martin Luther King Jr. Day",
        date(year, 2, 14): "Valentine's Day", _nth(year, 2, 0, 3): "Presidents' Day",
        _easter(year): "Easter", _last(year, 5, 0): "Memorial Day", date(year, 7, 4): "Independence Day",
        _nth(year, 9, 0, 1): "Labor Day", date(year, 10, 31): "Halloween", date(year, 11, 11): "Veterans Day",
        _nth(year, 11, 3, 4): "Thanksgiving", date(year, 12, 25): "Christmas Day",
        date(year, 12, 31): "New Year's Eve",
    }


class CalendarWidget(WidgetBase):
    KEY, TITLE, SIZE, REFRESH_MS = "calendar", "Calendar", (240, 232), 30000

    def __init__(self, controller):
        super().__init__(controller)
        self.offset = 0
        self._hits = []

    def _month(self):
        today = clock.now().date()
        index = today.year * 12 + today.month - 1 + self.offset
        return index // 12, index % 12 + 1

    def draw(self, p, r):
        today = clock.now().date()
        year, month = self._month()
        self._hits = []
        _text(p, 12, 6, r.width() - 24, 24, f"{calendar.month_name[month]} {year}", 15, WHITE, True,
              Qt.AlignHCenter | Qt.AlignVCenter)
        for label, x, step in (("\u25C0", 8, -1), ("\u25B6", r.width() - 30, 1)):
            rect = QRectF(x, 8, 22, 20)
            _text(p, rect.x(), rect.y(), rect.width(), rect.height(), label, 12, GOLD, align=Qt.AlignCenter)
            self._hits.append((rect, step))
        self._hits.append((QRectF(40, 6, r.width() - 80, 24), 0))
        cell_w = (r.width() - 16) / 7
        for i, name in enumerate(("Su", "Mo", "Tu", "We", "Th", "Fr", "Sa")):
            _text(p, 8 + i * cell_w, 32, cell_w, 16, name, 11, GOLD, True, Qt.AlignCenter)
        days = list(calendar.Calendar(firstweekday=6).itermonthdates(year, month))
        marks = {**holidays(year - 1), **holidays(year), **holidays(year + 1)}
        for n, d in enumerate(days[:42]):
            row, col = divmod(n, 7)
            rect = QRectF(8 + col * cell_w, 50 + row * 22, cell_w, 22)
            inside = d.month == month
            if d == today:
                p.setPen(QPen(QColor("#B8860B"), 1))
                p.setBrush(QColor("#FFD23C"))
                p.drawRoundedRect(rect.adjusted(2, 1, -2, -1), 5, 5)
            _text(p, rect.x(), rect.y(), rect.width(), rect.height(), str(d.day), 12,
                  QColor("#1A2A5C") if d == today else (WHITE if inside else QColor(255, 255, 255, 80)),
                  d == today, Qt.AlignCenter)
            if d in marks and inside:
                p.setPen(Qt.NoPen)
                p.setBrush(QColor("#FF7B6B"))
                p.drawEllipse(QPointF(rect.center().x(), rect.bottom() - 3), 1.8, 1.8)
        upcoming = sorted((d, name) for d, name in marks.items() if d >= today)
        if upcoming:
            d, name = upcoming[0]
            gap = (d - today).days
            when = "today" if gap == 0 else "tomorrow" if gap == 1 else f"in {gap} days"
            _text(p, 12, r.height() - 24, r.width() - 24, 18, f"{name} \u2013 {when}", 11, SOFT,
                  align=Qt.AlignCenter)

    def clicked(self, pos):
        for rect, step in self._hits:
            if rect.contains(pos):
                self.offset = self.offset + step if step else 0
                self.update()
                return


# ---- weather -----------------------------------------------------------------------------------------------
class WeatherWidget(WidgetBase):
    KEY, TITLE, SIZE, REFRESH_MS = "weather", "Weather", (300, 240), 30000

    def draw(self, p, r):
        s = self.c.settings
        model = self.c.weather()
        now = clock.now()
        cur = model.at(now)
        days = model.forecast(now, 5)
        fahrenheit = s["fahrenheit"]
        _text(p, 14, 8, r.width() - 28, 16, f"{wx.season(now, s['hemisphere'])}  \u00B7  {s['climate']} climate",
              11, GOLD, True)
        art.draw_condition(p, QRectF(10, 28, 72, 72), cur.cond, cur.night)
        _text(p, 88, 24, 110, 50, wx.temp_text(cur.temp_c, fahrenheit), 40, WHITE, True)
        _text(p, 90, 72, 120, 16, wx.LABELS[cur.cond], 13, GOLD, True)
        _text(p, 90, 88, 120, 14, f"Feels like {wx.temp_text(cur.feels_c, fahrenheit)}", 11, SOFT)
        lines = (f"High {wx.temp_text(days[0].hi_c, fahrenheit)}   Low {wx.temp_text(days[0].lo_c, fahrenheit)}",
                 f"Humidity {cur.humidity}%", f"Wind {wx.wind_text(cur.wind_kph, fahrenheit)} {cur.wind_dir}",
                 f"Pressure {cur.pressure} mb", f"Rain chance {days[0].precip}%")
        for i, line in enumerate(lines):
            _text(p, 196, 28 + i * 15, 100, 14, line, 10, WHITE if i == 0 else SOFT, i == 0)
        p.setPen(QPen(QColor(255, 255, 255, 60), 1))
        p.drawLine(14, 118, int(r.width() - 14), 118)
        col = (r.width() - 20) / 5
        for i, day in enumerate(days):
            x = 10 + i * col
            name = "Today" if i == 0 else f"{day.date:%a}"
            _text(p, x, 122, col, 14, name, 11, GOLD, True, Qt.AlignCenter)
            art.draw_condition(p, QRectF(x + (col - 36) / 2, 138, 36, 36), day.cond, False)
            _text(p, x, 178, col, 14, wx.temp_text(day.hi_c, fahrenheit), 12, WHITE, True, Qt.AlignCenter)
            _text(p, x, 192, col, 14, wx.temp_text(day.lo_c, fahrenheit), 11, DIM, False, Qt.AlignCenter)
            _text(p, x, 206, col, 14, f"{day.precip}%" if day.precip else "", 10, QColor("#7FBCFF"),
                  False, Qt.AlignCenter)
        _text(p, 14, r.height() - 20, r.width() - 28, 14, "Generated locally from the date and season",
              9, DIM, align=Qt.AlignCenter)

    def clicked(self, pos):
        self.c.settings["fahrenheit"] = not self.c.settings["fahrenheit"]
        self.c.save()
        self.update()


# ---- TV guide ----------------------------------------------------------------------------------------------
def _clock_text(dt):
    return f"{dt.hour % 12 or 12}:{dt.minute:02d}{'am' if dt.hour < 12 else 'pm'}"


def _program_title(slot):
    try:
        from ..tv.tuner import describe
        return describe(slot)[0]
    except Exception:
        return slot.media.label()


class TVGuideWidget(WidgetBase):
    """What's on right now, straight from ClaudeTV's own schedule (the same one the tuner and TV Guide use)."""
    KEY, TITLE, SIZE, REFRESH_MS = "tv", "TV Guide", (320, 96), 15000
    ROW = 64
    HEAD = 30

    def __init__(self, controller):
        super().__init__(controller)
        self.channels = None
        self.rows = []
        self._asked = False
        self._hits = []

    def start(self):
        super().start()
        if not self._asked:
            self._asked = True
            from ..tv import lineup
            lineup.get(self._lineup)

    def _lineup(self, channels):
        self.channels = [ch for ch in channels if not ch.dead]
        self.refresh()

    def refresh(self):
        if self.channels is not None:
            from ..tv import schedule
            t = (clock.now() - schedule.EPOCH).total_seconds()
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
            height = self.HEAD + max(1, len(rows)) * self.ROW + 8
            if height != self.height():
                self.resize(self.width(), height)
                self.c.place_all()
        self.update()

    def draw(self, p, r):
        _text(p, 14, 6, 190, 22, "TV Guide \u2013 On Now", 14, WHITE, True)
        _text(p, r.width() - 94, 6, 82, 22, clock.time_text(), 12, GOLD, True, Qt.AlignRight | Qt.AlignVCenter)
        self._hits = [(QRectF(0, 0, r.width(), self.HEAD), None)]
        if self.channels is None:
            _text(p, 14, 36, r.width() - 28, 40, "Reading the channel lineup\u2026", 12, SOFT)
            return
        if not self.rows:
            _text(p, 14, 36, r.width() - 28, 40, "No channels are on the air. Open ClaudeTV to set up the "
                  "video archive.", 11, SOFT, elide=False)
            return
        for i, (ch, cur, nxt, t) in enumerate(self.rows):
            y = self.HEAD + i * self.ROW
            self._hits.append((QRectF(0, y, r.width(), self.ROW), ch))
            p.setPen(QPen(QColor(255, 255, 255, 45), 1))
            p.drawLine(12, y, int(r.width() - 12), y)
            _text(p, 14, y + 4, 80, 16, ch.label(), 12, GOLD, True)
            if cur is not None:
                _text(p, 14, y + 20, 70, 14, "ON NOW", 9, QColor("#7DFF9A"), True)
                _text(p, 90, y + 4, r.width() - 102, 16, _program_title(cur), 12, WHITE, True)
                _text(p, 90, y + 20, r.width() - 102, 14, f"{_clock_text(cur.when())} \u2013 {_clock_text(cur.until())}",
                      10, SOFT)
                _bar(p, QRectF(90, y + 37, r.width() - 104, 5), (t - cur.start) / max(1, cur.end - cur.start),
                     QColor("#7DFF9A"))
                if nxt is not None:
                    _text(p, 90, y + 45, r.width() - 102, 14, f"Next: {_program_title(nxt)} ({_clock_text(nxt.when())})",
                          10, DIM)
            elif nxt is not None:
                _text(p, 14, y + 20, 70, 14, "BREAK", 9, QColor("#FFB27A"), True)
                _text(p, 90, y + 4, r.width() - 102, 16, f"Up next: {_program_title(nxt)}", 12, WHITE, True)
                _text(p, 90, y + 20, r.width() - 102, 14, f"Starts {_clock_text(nxt.when())}", 10, SOFT)
            else:
                _text(p, 90, y + 4, r.width() - 102, 16, "Off the air", 12, DIM)

    def clicked(self, pos):
        for rect, ch in self._hits:
            if rect.contains(pos):
                try:
                    from ..tv import guide, tuner
                    if ch is None:
                        guide.open_guide(self.c.desktop)
                    else:
                        tuner.open_tv(self.c.desktop)
                        body = tuner.current()
                        if body is not None:
                            body.tune(ch)
                except Exception as exc:
                    self.c.say("TV Guide", f"Could not open ClaudeTV: {exc}")
                return


# ---- almanac -----------------------------------------------------------------------------------------------
class AlmanacWidget(WidgetBase):
    KEY, TITLE, SIZE, REFRESH_MS = "almanac", "Sun and Moon", (250, 142), 60000

    def draw(self, p, r):
        s = self.c.settings
        now = clock.now()
        name, lit, age = wx.moon(now)
        rise, sset = wx.sun_times(now, s["latitude"])
        length = sset - rise
        art.draw_moon(p, 40, 52, 24, age, s["hemisphere"])
        _text(p, 14, 82, 56, 14, f"{round(lit * 100)}% lit", 10, SOFT, align=Qt.AlignHCenter)
        _text(p, 76, 10, r.width() - 88, 18, name, 14, WHITE, True)
        for i, (label, value) in enumerate((("Sunrise", wx.hours_text(rise)), ("Sunset", wx.hours_text(sset)),
                                            ("Daylight", f"{int(length)}h {round((length % 1) * 60)}m"))):
            _text(p, 76, 34 + i * 18, 60, 16, label, 11, DIM)
            _text(p, 130, 34 + i * 18, r.width() - 142, 16, value, 12, WHITE, True)
        change = [d for d in (date(now.year, 3, 20), date(now.year, 6, 21), date(now.year, 9, 22),
                              date(now.year, 12, 21), date(now.year + 1, 3, 20)) if d > now.date()][0]
        _text(p, 14, r.height() - 38, r.width() - 28, 16,
              f"{wx.season(now, s['hemisphere'])} \u2013 {wx.season(datetime.combine(change, now.time()), s['hemisphere'])} "
              f"in {(change - now.date()).days} days", 11, GOLD, True, Qt.AlignCenter)


# ---- system monitor ----------------------------------------------------------------------------------------
class _MemoryStatus(ctypes.Structure):
    _fields_ = [("length", ctypes.c_ulong), ("load", ctypes.c_ulong), ("total", ctypes.c_ulonglong),
                ("avail", ctypes.c_ulonglong), ("total_page", ctypes.c_ulonglong),
                ("avail_page", ctypes.c_ulonglong), ("total_virtual", ctypes.c_ulonglong),
                ("avail_virtual", ctypes.c_ulonglong), ("avail_extended", ctypes.c_ulonglong)]


class _FileTime(ctypes.Structure):
    _fields_ = [("low", ctypes.c_ulong), ("high", ctypes.c_ulong)]

    def value(self):
        return (self.high << 32) | self.low


class _IfRow(ctypes.Structure):
    """MIB_IFROW from iphlpapi (the 32-bit per-adapter byte counters)."""
    _fields_ = [("name", ctypes.c_wchar * 256), ("index", ctypes.c_ulong), ("type", ctypes.c_ulong),
                ("mtu", ctypes.c_ulong), ("speed", ctypes.c_ulong), ("physlen", ctypes.c_ulong),
                ("phys", ctypes.c_ubyte * 8), ("admin", ctypes.c_ulong), ("oper", ctypes.c_ulong),
                ("lastchange", ctypes.c_ulong), ("inoctets", ctypes.c_ulong), ("inucast", ctypes.c_ulong),
                ("innucast", ctypes.c_ulong), ("indiscards", ctypes.c_ulong), ("inerrors", ctypes.c_ulong),
                ("inunknown", ctypes.c_ulong), ("outoctets", ctypes.c_ulong), ("outucast", ctypes.c_ulong),
                ("outnucast", ctypes.c_ulong), ("outdiscards", ctypes.c_ulong), ("outerrors", ctypes.c_ulong),
                ("outqlen", ctypes.c_ulong), ("desclen", ctypes.c_ulong), ("descr", ctypes.c_ubyte * 256)]


class _DiskPerf(ctypes.Structure):
    """DISK_PERFORMANCE from IOCTL_DISK_PERFORMANCE."""
    _fields_ = [("read", ctypes.c_longlong), ("written", ctypes.c_longlong), ("read_time", ctypes.c_longlong),
                ("write_time", ctypes.c_longlong), ("idle_time", ctypes.c_longlong), ("read_count", ctypes.c_ulong),
                ("write_count", ctypes.c_ulong), ("queue", ctypes.c_ulong), ("split", ctypes.c_ulong),
                ("query_time", ctypes.c_longlong), ("device", ctypes.c_ulong), ("manager", ctypes.c_wchar * 8)]


def _net_counters():
    """{adapter index: (bytes in, bytes out)} for connected ethernet / wifi adapters, plus the fastest link speed."""
    try:
        api = ctypes.windll.iphlpapi
        size = ctypes.c_ulong(0)
        api.GetIfTable(None, ctypes.byref(size), False)
        buf = ctypes.create_string_buffer(size.value)
        if api.GetIfTable(buf, ctypes.byref(size), False):
            return {}, 0
        rows = (_IfRow * ctypes.c_ulong.from_buffer(buf).value).from_buffer(buf, 4)
    except (AttributeError, OSError, ValueError):
        return {}, 0
    live = [r for r in rows if r.type in (6, 71) and r.oper in (4, 5) and r.speed]
    return {r.index: (r.inoctets, r.outoctets) for r in live}, max((r.speed for r in live), default=0)


def _disk_counters():
    """(bytes read, bytes written) summed over the physical drives, or None when Windows won't say."""
    try:
        kernel = ctypes.windll.kernel32
        kernel.CreateFileW.restype = ctypes.c_void_p
        kernel.CloseHandle.argtypes = [ctypes.c_void_p]
        kernel.DeviceIoControl.argtypes = [ctypes.c_void_p, ctypes.c_ulong, ctypes.c_void_p, ctypes.c_ulong,
                                           ctypes.c_void_p, ctypes.c_ulong, ctypes.c_void_p, ctypes.c_void_p]
    except (AttributeError, OSError):
        return None
    total, found = [0, 0], False
    for n in range(8):
        handle = kernel.CreateFileW(rf"\\.\PhysicalDrive{n}", 0, 3, None, 3, 0, None)
        if handle in (None, 0, ctypes.c_void_p(-1).value):
            continue
        perf, got = _DiskPerf(), ctypes.c_ulong()
        if kernel.DeviceIoControl(handle, 0x70020, None, 0, ctypes.byref(perf), ctypes.sizeof(perf),
                                  ctypes.byref(got), None):
            total[0] += perf.read
            total[1] += perf.written
            found = True
        kernel.CloseHandle(handle)
    return tuple(total) if found else None


def _rate(value):
    for unit in ("B/s", "KB/s", "MB/s"):
        if value < 1024 or unit == "MB/s":
            return f"{value:.0f} {unit}" if unit == "B/s" else f"{value:.1f} {unit}"
        value /= 1024


def _uptime(seconds):
    days, rest = divmod(int(seconds), 86400)
    hours, rest = divmod(rest, 3600)
    return (f"{days}d " if days else "") + f"{hours}h {rest // 60:02d}m"


def _image_generating():
    try:
        from .. import imagegen
        return imagegen.generating()
    except Exception:
        return False


class SystemWidget(WidgetBase):
    KEY, TITLE, SIZE, REFRESH_MS = "system", "System Monitor", (260, 330), 1000
    GRAPH = 60

    def __init__(self, controller):
        super().__init__(controller)
        self._last = None
        self.cpu = None
        self._net = None
        self._disk = None
        self._stamp = None
        self.down = self.up = self.read = self.write = 0.0
        self.link = 0
        self.has_disk = True
        self.history = []
        self.blink = False
        self.gen = self.llm_busy = False
        self._blinker = QTimer(self)
        self._blinker.timeout.connect(self._blink)

    def start(self):
        super().start()
        self._blinker.start(450)

    def stop(self):
        super().stop()
        self._blinker.stop()

    def _blink(self):
        self.blink = not self.blink
        if self.gen or self.llm_busy:
            self.update()

    def _broker(self):
        try:
            from ... import broker
            return broker.get()
        except Exception:
            return None

    def _read_cpu(self):
        try:
            idle, kernel, user = _FileTime(), _FileTime(), _FileTime()
            if not ctypes.windll.kernel32.GetSystemTimes(ctypes.byref(idle), ctypes.byref(kernel), ctypes.byref(user)):
                return None
            now = (idle.value(), kernel.value() + user.value())
        except (AttributeError, OSError):
            return None
        last, self._last = self._last, now
        if last is None or now[1] == last[1]:
            return self.cpu
        return 1 - (now[0] - last[0]) / (now[1] - last[1])

    def refresh(self):
        self.cpu = self._read_cpu()
        now = monotonic()
        net, self.link = _net_counters()
        disk = _disk_counters() if self.has_disk else None
        if self.has_disk and disk is None:
            self.has_disk = False
        if self._stamp is not None and now > self._stamp:
            dt = now - self._stamp
            wrap = 1 << 32
            self.down = sum((v[0] - self._net[k][0]) % wrap for k, v in net.items() if k in self._net) / dt
            self.up = sum((v[1] - self._net[k][1]) % wrap for k, v in net.items() if k in self._net) / dt
            if disk and self._disk:
                self.read = max(0, disk[0] - self._disk[0]) / dt
                self.write = max(0, disk[1] - self._disk[1]) / dt
            self.history.append((self.down, self.up))
            del self.history[:-self.GRAPH]
        self._net, self._disk, self._stamp = net, disk, now
        self.gen = _image_generating()
        broker = self._broker()
        self.llm_busy = bool(broker and broker.busy())
        self.update()

    def _led(self, p, x, y, colour, on):
        p.setPen(QPen(QColor(0, 0, 0, 120), 1))
        p.setBrush(colour if on else QColor(colour.red() // 4, colour.green() // 4, colour.blue() // 4))
        p.drawEllipse(QRectF(x, y, 11, 11))
        if on:
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(255, 255, 255, 150))
            p.drawEllipse(QRectF(x + 2.5, y + 2, 3, 3))

    def _graph(self, p, rect):
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(0, 0, 0, 70))
        p.drawRoundedRect(rect, 4, 4)
        if not self.history:
            return
        top = max(max(d + u for d, u in self.history), 16 * 1024)
        step = rect.width() / (self.GRAPH - 1)
        x0 = rect.right() - step * (len(self.history) - 1)
        for i, (down, up) in enumerate(self.history):
            x = x0 + i * step - step / 2
            h_down, h_up = (rect.height() - 2) * down / top, (rect.height() - 2) * up / top
            p.setBrush(QColor("#7DFF9A"))
            p.drawRect(QRectF(x, rect.bottom() - 1 - h_down, max(1.0, step - 0.5), h_down))
            p.setBrush(QColor("#FFB27A"))
            p.drawRect(QRectF(x, rect.bottom() - 1 - h_down - h_up, max(1.0, step - 0.5), h_up))

    def draw(self, p, r):
        w = r.width()
        _text(p, 14, 6, w - 28, 20, "System Monitor", 13, WHITE, True)
        mem = _MemoryStatus()
        mem.length = ctypes.sizeof(_MemoryStatus)
        try:
            ok = ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(mem))
        except (AttributeError, OSError):
            ok = False
        try:
            disk = shutil.disk_usage(os.path.abspath(os.sep))
        except OSError:
            disk = None
        rows = (("CPU", self.cpu, "n/a" if self.cpu is None else f"{round(self.cpu * 100)}%"),
                ("Memory", mem.load / 100 if ok else None,
                 f"{(mem.total - mem.avail) / 2 ** 30:.1f} / {mem.total / 2 ** 30:.1f} GB" if ok else "n/a"),
                ("Disk", disk.used / disk.total if disk else None,
                 f"{disk.free / 2 ** 30:.0f} GB free" if disk else "n/a"))
        for i, (label, frac, text) in enumerate(rows):
            y = 30 + i * 26
            _text(p, 14, y, 60, 14, label, 11, SOFT, True)
            _text(p, 100, y, w - 114, 14, text, 11, WHITE, align=Qt.AlignRight | Qt.AlignVCenter)
            _bar(p, QRectF(14, y + 15, w - 28, 6), frac or 0, self._tint(frac or 0))

        y = 110
        _text(p, 14, y, 60, 14, "Network", 11, SOFT, True)
        link = f"{self.link / 1e6:.0f} Mbps link" if self.link else "offline"
        _text(p, 80, y, w - 94, 14, link, 10, DIM, align=Qt.AlignRight | Qt.AlignVCenter)
        self._graph(p, QRectF(14, y + 17, w - 28, 34))
        _text(p, 14, y + 54, (w - 28) / 2, 14, "\u2193 " + _rate(self.down), 11, QColor("#7DFF9A"), True)
        _text(p, w / 2, y + 54, w / 2 - 14, 14, "\u2191 " + _rate(self.up), 11, QColor("#FFB27A"), True,
              align=Qt.AlignRight | Qt.AlignVCenter)

        y = 184
        _text(p, 14, y, 60, 14, "Disk I/O", 11, SOFT, True)
        if self.has_disk:
            _text(p, 14, y + 16, (w - 28) / 2, 14, "R " + _rate(self.read), 11, QColor("#7DFF9A"), True)
            _text(p, w / 2, y + 16, w / 2 - 14, 14, "W " + _rate(self.write), 11, QColor("#FFB27A"), True,
                  align=Qt.AlignRight | Qt.AlignVCenter)
        else:
            _text(p, 14, y + 16, w - 28, 14, "unavailable (needs permission)", 10, DIM)

        broker = self._broker()
        waiting = max(0, (broker.pending() if broker else 0) - (1 if broker and broker.running else 0))
        background = broker.background_pending() if broker else 0
        busy = max(self.cpu or 0, min(1.0, ((broker.pending() if broker else 0) + (1 if self.gen else 0)) / 4))
        word = "Idle" if busy < 0.15 else "Light" if busy < 0.45 else "Busy" if busy < 0.8 else "Swamped"
        y = 224
        _text(p, 14, y, 80, 14, "Workload", 11, SOFT, True)
        _text(p, 100, y, w - 114, 14, word, 11, WHITE, True, align=Qt.AlignRight | Qt.AlignVCenter)
        _bar(p, QRectF(14, y + 15, w - 28, 6), busy, self._tint(busy))

        y = 254
        on = self.blink
        self._led(p, 14, y + 2, QColor("#FF5A4A"), self.gen and on)
        _text(p, 32, y, 100, 14, "Image gen", 11, SOFT, True)
        _text(p, 140, y, w - 154, 14, "Generating\u2026" if self.gen else "Idle", 11,
              QColor("#FF9A8F") if self.gen else DIM, self.gen, align=Qt.AlignRight | Qt.AlignVCenter)
        y = 272
        self._led(p, 14, y + 2, QColor("#7DFF9A"), self.llm_busy and on)
        _text(p, 32, y, 100, 14, "LLM", 11, SOFT, True)
        if not self.llm_busy:
            llm = "Idle"
        else:
            llm = "Working" + (f", {waiting} waiting" if waiting else "") + (f" ({background} bg)" if background else "")
        _text(p, 100, y, w - 114, 14, llm, 11, WHITE if self.llm_busy else DIM, self.llm_busy,
              align=Qt.AlignRight | Qt.AlignVCenter)

        y = 300
        _text(p, 14, y, 80, 14, "Uptime", 11, SOFT, True)
        try:
            up = _uptime(ctypes.windll.kernel32.GetTickCount64() / 1000)
        except (AttributeError, OSError):
            up = "n/a"
        _text(p, 100, y, w - 114, 14, up, 11, WHITE, align=Qt.AlignRight | Qt.AlignVCenter)

    @staticmethod
    def _tint(frac):
        return QColor("#7DFF9A") if frac < 0.7 else QColor("#FFB27A") if frac < 0.9 else QColor("#FF6B6B")


# ---- sticky notes ------------------------------------------------------------------------------------------
NOTES_DIR = DATA / "sticky_notes"
NOTE_FILE = DATA / "sticky_note.txt"
NOTE_MIN = (160, 110)


class _Grip(QWidget):
    """The little resize corner (QSizeGrip would resize the whole desktop window, so this does it by hand)."""

    def __init__(self, note):
        super().__init__(note)
        self.note = note
        self.setFixedSize(16, 16)
        self.setCursor(Qt.SizeFDiagCursor)
        self._start = None

    def paintEvent(self, event):
        p = QPainter(self)
        p.setPen(QPen(QColor(150, 115, 20, 200), 1.4))
        for i in (4, 8, 12):
            p.drawLine(self.width() - 2, i, i, self.height() - 2)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._start = (event.globalPosition().toPoint(), self.note.size())

    def mouseMoveEvent(self, event):
        if self._start is None:
            return
        pos, size = self._start
        d = event.globalPosition().toPoint() - pos
        area = self.note.c.desktop.work_area()
        w = max(NOTE_MIN[0], min(area.width() - self.note.x(), size.width() + d.x()))
        h = max(NOTE_MIN[1], min(area.bottom() + 1 - self.note.y(), size.height() + d.y()))
        self.note.resize(w, h)

    def mouseReleaseEvent(self, event):
        if self._start is not None:
            self._start = None
            self.note.c.remember_note_size(self.note)


class NoteWidget(WidgetBase):
    """A yellow sticky note you type straight into. Resizable, scrolls when the text outgrows it, saves itself,
    and Save / Load keep named copies of important notes (data/sticky_notes)."""
    KEY, TITLE, SIZE, REFRESH_MS = "note", "Sticky Notes", (260, 220), 60000
    INTERACTIVE = True                      # takes the mouse even when the other widgets are click-through
    HEADER = 26

    def __init__(self, controller):
        super().__init__(controller)
        size = controller.settings.get("note_size")
        if size:
            self.resize(max(NOTE_MIN[0], size[0]), max(NOTE_MIN[1], size[1]))
        self.setMinimumSize(*NOTE_MIN)
        self.status = ""
        self.edit = QPlainTextEdit(self)
        self.edit.setFrameShape(QPlainTextEdit.NoFrame)
        self.edit.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.edit.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.edit.setPlaceholderText("Type a note here...")
        self.edit.setStyleSheet(
            "QPlainTextEdit { background: transparent; color: #4A3B00; font-family: 'Comic Sans MS', Tahoma;"
            " font-size: 13px; selection-background-color: #E0B020; }"
            "QScrollBar:vertical { background: rgba(190,150,30,40); width: 10px; margin: 0; border-radius: 4px; }"
            "QScrollBar::handle:vertical { background: rgba(160,120,20,170); min-height: 24px; border-radius: 4px; }"
            "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }"
            "QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }")
        self.edit.setPlainText(self._initial_text())
        self.edit.textChanged.connect(self._changed)
        self.save_btn, self.load_btn = QPushButton("Save", self), QPushButton("Load", self)
        for b in (self.save_btn, self.load_btn):
            b.setFixedSize(46, 19)
            b.setCursor(Qt.PointingHandCursor)
            b.setFocusPolicy(Qt.NoFocus)
            b.setStyleSheet("QPushButton { background: rgba(255,255,255,150); border: 1px solid #B8921E;"
                            " border-radius: 3px; color: #4A3B00; font-family: Tahoma; font-size: 11px; }"
                            "QPushButton:hover { background: rgba(255,255,255,230); }"
                            "QPushButton:pressed { background: #F0D060; }")
        self.save_btn.clicked.connect(self.save_as)
        self.load_btn.clicked.connect(self.load_menu)
        self.grip = _Grip(self)
        self._autosave = QTimer(self)
        self._autosave.setSingleShot(True)
        self._autosave.setInterval(600)
        self._autosave.timeout.connect(self.flush)
        self._status_timer = QTimer(self)
        self._status_timer.setSingleShot(True)
        self._status_timer.timeout.connect(lambda: self._say(""))
        self._layout()

    # ---- the text ----------------------------------------------------------------------------------------------
    def _initial_text(self):
        try:
            return NOTE_FILE.read_text(encoding="utf-8")
        except OSError:
            return str(self.c.settings.get("note") or "")        # the old one-box note

    def _changed(self):
        self._autosave.start()

    def flush(self):
        self._autosave.stop()
        try:
            NOTE_FILE.parent.mkdir(parents=True, exist_ok=True)
            NOTE_FILE.write_text(self.edit.toPlainText(), encoding="utf-8")
        except OSError as exc:
            self._say(f"Couldn't save: {exc.strerror or exc}")

    def stop(self):
        super().stop()
        self.flush()

    def _say(self, text):
        self.status = text
        if text:
            self._status_timer.start(2500)
        self.update()

    # ---- Save / Load ---------------------------------------------------------------------------------------------
    @staticmethod
    def _safe(name):
        name = "".join(ch for ch in name.strip() if ch not in '\\/:*?"<>|')[:60].strip(" .")
        return name

    def saved_notes(self):
        try:
            return sorted(NOTES_DIR.glob("*.txt"), key=lambda f: f.stat().st_mtime, reverse=True)
        except OSError:
            return []

    def save_as(self):
        from ..claudeai.app import ask_text
        first = next((ln.strip() for ln in self.edit.toPlainText().splitlines() if ln.strip()), "")
        ask_text(self.c.desktop, "Save sticky note", "Save this note as:", self._safe(first)[:30] or "My note",
                 self._save_named)

    def _save_named(self, name):
        name = self._safe(name)
        if not name:
            self._say("Give it a name first")
            return
        try:
            NOTES_DIR.mkdir(parents=True, exist_ok=True)
            (NOTES_DIR / f"{name}.txt").write_text(self.edit.toPlainText(), encoding="utf-8")
        except OSError as exc:
            self._say(f"Couldn't save: {exc.strerror or exc}")
            return
        self.flush()
        self._say(f"Saved \"{name}\"")

    def load_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet(MENU_STYLE)
        notes = self.saved_notes()
        if not notes:
            menu.addAction("(no saved notes yet - use Save)").setEnabled(False)
        for f in notes[:30]:
            menu.addAction(f.stem, lambda _=False, f=f: self.load_file(f))
        if notes:
            menu.addSeparator()
            delete = menu.addMenu("Delete a saved note")
            for f in notes[:30]:
                delete.addAction(f.stem, lambda _=False, f=f: self._delete(f))
        menu.exec(self.load_btn.mapToGlobal(self.load_btn.rect().bottomLeft()))

    def load_file(self, f):
        try:
            text = f.read_text(encoding="utf-8")
        except OSError as exc:
            self._say(f"Couldn't load: {exc.strerror or exc}")
            return
        if self.edit.toPlainText().strip() and self.edit.toPlainText() != text:
            self.flush()                                    # what was here is still in sticky_note.txt's last save
            self._backup_current()
        self.edit.setPlainText(text)
        self.flush()
        self._say(f"Loaded \"{f.stem}\"")

    def _backup_current(self):
        """Loading replaces the note, so keep what was on it as 'Previous note' rather than lose it."""
        try:
            NOTES_DIR.mkdir(parents=True, exist_ok=True)
            (NOTES_DIR / "Previous note.txt").write_text(self.edit.toPlainText(), encoding="utf-8")
        except OSError:
            pass

    def _delete(self, f):
        try:
            f.unlink()
            self._say(f"Deleted \"{f.stem}\"")
        except OSError as exc:
            self._say(f"Couldn't delete: {exc.strerror or exc}")

    # ---- layout and painting ------------------------------------------------------------------------------------
    def _layout(self):
        w, h = self.width(), self.height()
        self.save_btn.move(w - 8 - 46 * 2 - 4, 4)
        self.load_btn.move(w - 8 - 46, 4)
        self.edit.setGeometry(8, self.HEADER, w - 16, h - self.HEADER - 14)
        self.grip.move(w - 16, h - 16)
        self.grip.raise_()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._layout()

    def background(self, p, r):
        a = max(self.alpha(), 150)                           # a note you type on stays readable
        grad = QLinearGradient(r.topLeft(), r.bottomLeft())
        grad.setColorAt(0, QColor(255, 240, 140, a))
        grad.setColorAt(1, QColor(255, 220, 90, a))
        p.setPen(QPen(QColor(190, 150, 30, min(255, a)), 1))
        p.setBrush(grad)
        p.drawRoundedRect(r, 4, 4)
        p.setPen(QPen(QColor(190, 150, 30, 120), 1))
        p.drawLine(QPointF(6, self.HEADER - 2), QPointF(r.width() - 6, self.HEADER - 2))

    def draw(self, p, r):
        _text(p, 10, 4, r.width() - 110, 20, self.status or "Sticky Note", 11, QColor("#7A5F00"), bold=not self.status)


WIDGETS = (ClockWidget, CalendarWidget, WeatherWidget, TVGuideWidget, AlmanacWidget, SystemWidget, NoteWidget)
