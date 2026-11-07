"""The clock made visible, as Claude and Magic draws it (its 73b-clock): a dial under the map - the sky's colour of
the hour, the sun and the moon on their arc over a strip of ground, the hour in figures and words, the day and the
season, the weather (and in the Deep, the weather above, and the floodwater), and the moon's face drawn large - and
the Calendar (K): the moon's month, the seasons' daylight, the weather now and what comes next."""
import math

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from ..engine.atmosphere import look
from . import theme
from ..game.sky import CLOCK, DAYLIGHT, MOON_WORDS, NAMES, hour_word

ICONS = {"clear": "sun", "cloud": "cloud", "rain": "rain", "storm": "storm", "mist": "mist", "wind": "wind",
         "snow": "snow", "heat": "sun", "aurora": "aurora", "tornado": "wind"}


def _q(rgb, a=255):
    return QColor(int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255), a)


def paint_moon(p, c, r, phase, lit=QColor("#ECE8D6"), dark=QColor(40, 44, 60)):
    """The moon in its phase: 0 new, 4 full; the lit part on the right while it waxes, the left while it wanes."""
    p.save()
    p.setPen(Qt.NoPen)
    p.setBrush(dark)
    p.drawEllipse(c, r, r)
    if phase == 0:
        p.restore()
        return
    path = QPainterPath()
    k = math.cos(phase / 4 * math.pi) if phase <= 4 else math.cos((phase - 4) / 4 * math.pi)
    waxing = phase <= 4
    steps = 40
    pts = []
    for i in range(steps + 1):                       # the outer limb
        a = -math.pi / 2 + math.pi * i / steps
        x = math.cos(a) * r
        pts.append(QPointF(c.x() + (x if waxing else -x), c.y() + math.sin(a) * r))
    for i in range(steps, -1, -1):                   # the terminator
        a = -math.pi / 2 + math.pi * i / steps
        x = math.cos(a) * r * k
        pts.append(QPointF(c.x() + (x if waxing else -x), c.y() + math.sin(a) * r))
    path.moveTo(pts[0])
    for q in pts[1:]:
        path.lineTo(q)
    p.setBrush(lit)
    p.drawPath(path)
    p.restore()


def paint_weather_icon(p, c, s, kind):
    p.save()
    p.setRenderHint(QPainter.Antialiasing)
    icon = ICONS.get(kind, "sun")
    if icon == "sun":
        p.setPen(QPen(QColor("#F8D060"), 1.5))
        p.setBrush(QColor("#F8D060") if kind != "heat" else QColor("#FF9040"))
        p.drawEllipse(c, s * 0.35, s * 0.35)
        for i in range(8):
            a = i * math.pi / 4
            p.drawLine(QPointF(c.x() + math.cos(a) * s * 0.5, c.y() + math.sin(a) * s * 0.5),
                       QPointF(c.x() + math.cos(a) * s * 0.7, c.y() + math.sin(a) * s * 0.7))
    elif icon in ("cloud", "rain", "storm", "snow"):
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#C8CED8") if icon != "storm" else QColor("#7A808C"))
        for dx, dy, r in ((-0.25, 0.05, 0.3), (0.1, -0.12, 0.38), (0.35, 0.08, 0.26)):
            p.drawEllipse(QPointF(c.x() + dx * s, c.y() + dy * s), r * s, r * s)
        if icon == "rain" or icon == "storm":
            p.setPen(QPen(QColor("#80B0F0"), 1.5))
            for dx in (-0.25, 0.0, 0.25):
                p.drawLine(QPointF(c.x() + dx * s, c.y() + 0.4 * s), QPointF(c.x() + (dx - 0.08) * s, c.y() + 0.65 * s))
        if icon == "storm":
            p.setPen(QPen(QColor("#FFE860"), 2))
            p.drawPolyline([QPointF(c.x() + 0.05 * s, c.y() + 0.3 * s), QPointF(c.x() - 0.08 * s, c.y() + 0.5 * s),
                            QPointF(c.x() + 0.06 * s, c.y() + 0.5 * s), QPointF(c.x() - 0.06 * s, c.y() + 0.72 * s)])
        if icon == "snow":
            p.setBrush(QColor("#FFFFFF"))
            for dx in (-0.25, 0.0, 0.25):
                p.drawEllipse(QPointF(c.x() + dx * s, c.y() + 0.55 * s), 2.2, 2.2)
    elif icon == "mist":
        p.setPen(QPen(QColor("#C0C8D0"), 2.2))
        for dy in (-0.25, 0.0, 0.25):
            p.drawLine(QPointF(c.x() - 0.5 * s, c.y() + dy * s), QPointF(c.x() + 0.5 * s, c.y() + dy * s))
    elif icon == "wind":
        p.setPen(QPen(QColor("#D0D8E0"), 2))
        p.setBrush(Qt.NoBrush)
        for dy, ln in ((-0.2, 0.8), (0.05, 1.0), (0.3, 0.6)):
            path = QPainterPath(QPointF(c.x() - 0.5 * s, c.y() + dy * s))
            path.quadTo(QPointF(c.x() + (ln - 0.5) * s, c.y() + dy * s), QPointF(c.x() + (ln - 0.45) * s, c.y() + (dy - 0.15) * s))
            p.drawPath(path)
    elif icon == "aurora":
        g = QLinearGradient(c.x() - s * 0.5, 0, c.x() + s * 0.5, 0)
        g.setColorAt(0, QColor(60, 230, 140, 220))
        g.setColorAt(1, QColor(150, 80, 230, 220))
        p.setPen(QPen(g, 3))
        for dy in (-0.15, 0.1):
            p.drawLine(QPointF(c.x() - 0.5 * s, c.y() + dy * s), QPointF(c.x() + 0.5 * s, c.y() + (dy - 0.2) * s))
    p.restore()


def paint_dial(p, r, sky, outdoors, depth):
    """The dial in the HUD (r: its rectangle)."""
    p.save()
    p.setRenderHint(QPainter.Antialiasing)
    a = look(sky, True)
    d = sky.dial()
    w = sky.now()
    theme.plate(p, r, 8, 200)
    # the sky of the hour, and the arc
    band = QRectF(r.x() + 6, r.y() + 6, r.width() - 52, 46)
    g = QLinearGradient(0, band.top(), 0, band.bottom())
    g.setColorAt(0, _q(a["sky_top"]))
    g.setColorAt(1, _q(a["sky_horizon"]))
    p.setPen(Qt.NoPen)
    p.setBrush(g)
    p.drawRoundedRect(band, 4, 4)
    p.setBrush(QColor(52, 70, 40) if sky.snow_depth() < 0.3 else QColor(210, 214, 222))
    p.drawRect(QRectF(band.x(), band.bottom() - 7, band.width(), 7))
    cx, base, R = band.center().x(), band.bottom() - 7, min(band.width() / 2 - 8, band.height() - 12)
    p.setPen(QPen(QColor(255, 255, 255, 50), 1, Qt.DashLine))
    p.setBrush(Qt.NoBrush)
    p.drawArc(QRectF(cx - R, base - R, 2 * R, 2 * R), 0, 180 * 16)
    p.setClipRect(QRectF(band.x(), band.y(), band.width(), band.height() - 7))
    for ang, is_sun in ((d["sun"], True), (d["moon"], False)):
        t = math.radians(ang)
        pos = QPointF(cx + math.sin(t) * R, base - math.cos(t) * R)
        if is_sun:
            p.setPen(Qt.NoPen)
            p.setBrush(QColor("#FFE070"))
            p.drawEllipse(pos, 5, 5)
        else:
            paint_moon(p, pos, 4.5, d["phase"])
    p.setClipping(False)
    # the moon's face, large
    paint_moon(p, QPointF(r.right() - 24, r.y() + 29), 17, d["phase"])
    # the words
    p.setPen(QColor("#F0E4C8"))
    p.setFont(QFont("Georgia", 11, QFont.Bold))
    p.drawText(QPointF(r.x() + 8, r.y() + 70), f"{sky.time_figures()}  {hour_word(sky.hour)}")
    p.setFont(QFont("Segoe UI", 8))
    p.setPen(QColor("#C8BCA0"))
    flooded = not outdoors and sky.flood > 0 and 1 <= depth <= 3
    p.drawText(QPointF(r.x() + 8, r.y() + 85), f"Day {sky.day + 1} - {sky.season}" + (" - flooded!" if flooded else ""))
    label = NAMES[w["kind"]] if w["kind"] != "clear" else ("Clear night" if d["night"] else "Clear")
    if not outdoors:
        label = "Above: " + label
    paint_weather_icon(p, QPointF(r.x() + 16, r.y() + 99), 16, w["kind"])
    p.setPen(QColor("#E0D8C0"))
    p.drawText(QPointF(r.x() + 30, r.y() + 103), label)
    if w["kind"] != "clear":
        for i in range(5):
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(230, 210, 150, 230) if w["strength"] > i / 5 + 0.05 else QColor(255, 255, 255, 40))
            p.drawRect(QRectF(r.right() - 48 + i * 8, r.y() + 96, 6, 6))
    p.restore()


class CalendarPanel(theme.Ornate):
    """The Calendar (K): the moon's month, the seasons' daylight, the weather now and next."""

    def __init__(self, shell):
        super().__init__()
        self.setFixedSize(760, 520)
        self.shell = shell
        sky = shell.view.game.sky
        lay = QVBoxLayout(self)
        lay.setContentsMargins(26, 20, 26, 20)
        head = QHBoxLayout()
        t = QLabel("The Calendar")
        t.setObjectName("heading")
        head.addWidget(t)
        head.addStretch(1)
        close = QPushButton("Close")
        close.clicked.connect(shell.close_panel)
        head.addWidget(close)
        lay.addLayout(head)
        d = sky.dial()
        sub = QLabel(f"{sky.time_figures()}, {hour_word(sky.hour)} - day {sky.day + 1} - {sky.season} "
                     f"(dawn at {DAYLIGHT[sky.season][0]}, dusk at {DAYLIGHT[sky.season][1]}) - {MOON_WORDS[d['phase']]}")
        sub.setObjectName("sub")
        lay.addWidget(sub)
        lay.addWidget(_MoonMonth(sky))
        w = sky.now()
        nxt = sky.next
        lines = [f"<b>Now:</b> {NAMES[w['kind']]}" + (f" ({int(w['strength'] * 100)}%), until "
                                                      f"{_at(w['until'])}" if w["kind"] != "clear" else f", until {_at(w['until'])}")]
        if nxt:
            mins = max(0, int(nxt["from"] - sky.clock))
            lines.append(f"<b>Next:</b> {NAMES[nxt['kind']]}, in {mins // 60} h {mins % 60:02d} m")
        lines.append(f"<b>The day leans to:</b> {sky.day_word()}")
        if sky.flood > 0:
            lines.append(f"<b>Floodwater</b> stands in the low halls of floors 1 to 3 ({int(sky.flood * 100)}%), draining.")
        lines.append("<span style='color:#B8A888'>A minute of Thornwick's day is a second of play; the stairs take an hour. "
                     "Rain dulls fire and feeds storm, snow feeds frost and slows the walk, mist hides you, a storm's "
                     "lightning strikes in the wood, the wood is fiercer at night - and a heavy storm floods the first "
                     "floors' sunken rooms.</span>")
        for line in lines:
            lab = QLabel(line)
            lab.setTextFormat(Qt.RichText)
            lab.setWordWrap(True)
            lay.addWidget(lab)
        lay.addStretch(1)


def _at(clock):
    m = int((CLOCK["start"] + clock) % CLOCK["day"])
    return f"{m // 60}:{m % 60:02d}"


class _MoonMonth(QWidget):
    def __init__(self, sky):
        super().__init__()
        self.sky = sky
        self.setFixedHeight(120)

    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        today = self.sky.day % CLOCK["moon"]
        n = CLOCK["moon"]
        cell = self.width() / 15
        for i in range(n):
            row, col = divmod(i, 15)
            c = QPointF(cell * (col + 0.5), 30 + row * 52)
            phase = round((i / n) * 8) % 8
            if i == today:
                p.setPen(QPen(QColor("#F2D68A"), 2))
                p.setBrush(Qt.NoBrush)
                p.drawEllipse(c, 16, 16)
            paint_moon(p, c, 11, phase)
            p.setPen(QColor("#A89878"))
            p.setFont(QFont("Segoe UI", 7))
            p.drawText(QRectF(c.x() - 15, c.y() + 13, 30, 12), Qt.AlignCenter, str(i + 1))
        p.end()
