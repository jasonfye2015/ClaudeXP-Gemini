"""The Windows 11 taskbar: everything centered - Start (the four squares), Search, Task View, the pinned and open
programs as icons with their little indicator lines, thumbnails on hover - the Widgets weather button at the left
corner, and at the right the hidden-icons chevron, the system tray (network and volume: Quick Settings), the clock
(the notification center and calendar) and the Show desktop sliver."""
import json
import time

from PySide6.QtCore import QEvent, QPoint, QPointF, QRect, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import QMenu, QSlider, QToolTip, QWidget
from shiboken6 import isValid

from . import clock, sound
from .paths import DATA

TASKBAR_H = 48
BTN = 40
ICON = 24
GAP = 4
SEARCH_W = 150
WIDGETS_W = 170
TRAY_SLOT = 28
SYS_W = 68
CLOCK_W = 96
CHEVRON_W = 24
SHOW_DESKTOP_W = 8
FLASHES = 7
PINNED_FILE = DATA / "taskbar.json"
DEFAULT_PINNED = ["iexplore", "mycomputer", "outlook", "wmp"]


def _settings():
    try:
        return json.loads(PINNED_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _save_settings(data):
    PINNED_FILE.parent.mkdir(parents=True, exist_ok=True)
    PINNED_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def pinned():
    return list(_settings().get("pinned", DEFAULT_PINNED))


def set_pinned(keys):
    data = _settings()
    data["pinned"] = list(keys)
    _save_settings(data)


def _font(size=12, bold=False):
    from .style import font
    return font(size, QFont.DemiBold if bold else QFont.Normal)


def _accent():
    from . import display
    return display.get().accent()


def _panel_colour(alpha=236):
    from .wm import _tint
    c = QColor(_tint(True))
    c.setAlpha(alpha)
    return c


def draw_panel(p, rect, radius=8, alpha=245):
    """A Windows 11 flyout's surface: light Mica, a hairline border, rounded corners."""
    r = QRectF(rect).adjusted(0.5, 0.5, -0.5, -0.5)
    p.setPen(QPen(QColor(0, 0, 0, 40), 1))
    p.setBrush(_panel_colour(alpha))
    p.drawRoundedRect(r, radius, radius)


def wifi_glyph(p, cx, cy, colour, scale=1.0):
    pen = QPen(colour, 1.5 * scale)
    pen.setCapStyle(Qt.RoundCap)
    p.setPen(pen)
    p.setBrush(Qt.NoBrush)
    for rad in (3.5, 6.5, 9.5):
        r = rad * scale
        p.drawArc(QRectF(cx - r, cy + 3 * scale - r, 2 * r, 2 * r), 45 * 16, 90 * 16)
    p.setPen(Qt.NoPen)
    p.setBrush(colour)
    p.drawEllipse(QPointF(cx, cy + 3.5 * scale), 1.4 * scale, 1.4 * scale)


def speaker_glyph(p, cx, cy, colour, muted=False, level=1.0, scale=1.0):
    pen = QPen(colour, 1.4 * scale)
    pen.setJoinStyle(Qt.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.NoBrush)
    s = scale
    path = QPainterPath()
    path.moveTo(cx - 7 * s, cy - 3 * s)
    path.lineTo(cx - 4 * s, cy - 3 * s)
    path.lineTo(cx, cy - 7 * s)
    path.lineTo(cx, cy + 7 * s)
    path.lineTo(cx - 4 * s, cy + 3 * s)
    path.lineTo(cx - 7 * s, cy + 3 * s)
    path.closeSubpath()
    p.drawPath(path)
    if muted:
        p.drawLine(QPointF(cx + 3 * s, cy - 3 * s), QPointF(cx + 8 * s, cy + 3 * s))
        p.drawLine(QPointF(cx + 8 * s, cy - 3 * s), QPointF(cx + 3 * s, cy + 3 * s))
    else:
        waves = 2 if level > 0.5 else 1 if level > 0 else 0
        for i in range(waves):
            r = (4 + i * 3.5) * s
            p.drawArc(QRectF(cx - r + 2 * s, cy - r, 2 * r, 2 * r), -40 * 16, 80 * 16)


def weather_glyph(p, rect, cond):
    """A small sun or cloud for the Widgets button."""
    p.setRenderHint(QPainter.Antialiasing)
    c = rect.center()
    if cond in ("Sunny", "Clear"):
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#F7B500"))
        p.drawEllipse(QPointF(c.x(), c.y()), 7, 7)
        p.setPen(QPen(QColor("#F7B500"), 1.6))
        for i in range(8):
            from math import cos, radians, sin
            a = radians(i * 45)
            p.drawLine(QPointF(c.x() + cos(a) * 9, c.y() + sin(a) * 9), QPointF(c.x() + cos(a) * 12, c.y() + sin(a) * 12))
        return
    if cond == "Partly Cloudy":
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#F7B500"))
        p.drawEllipse(QPointF(c.x() - 4, c.y() - 4), 6, 6)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#9AA7B8") if cond == "Cloudy" else QColor("#C9D3DF"))
    p.drawEllipse(QPointF(c.x() - 4, c.y() + 3), 6, 6)
    p.drawEllipse(QPointF(c.x() + 3, c.y() + 1), 7, 7)
    p.drawEllipse(QPointF(c.x() + 8, c.y() + 4), 5, 5)
    p.drawRect(QRectF(c.x() - 4, c.y() + 3, 12, 6))
    if cond == "Showers":
        p.setPen(QPen(QColor("#4FA3E3"), 1.6))
        for i in range(3):
            p.drawLine(QPointF(c.x() - 3 + i * 5, c.y() + 10), QPointF(c.x() - 5 + i * 5, c.y() + 14))


class Thumbnail(QWidget):
    """The preview card that pops up above a window's button."""

    def __init__(self, desktop):
        super().__init__(desktop)
        self.desktop = desktop
        self.win = None
        self.hover_close = False
        self.hide()
        self.setMouseTracking(True)

    def show_for(self, win, button_rect):
        if not isValid(win):
            return
        self.win = win
        self.resize(232, 176)
        bar = self.desktop.taskbar
        x = bar.x() + button_rect.center().x() - self.width() // 2
        x = max(4, min(x, self.desktop.width() - self.width() - 4))
        self.move(x, bar.y() - self.height() - 8)
        self.show()
        self.raise_()
        self.update()

    def mousePressEvent(self, event):
        if self.win is None or not isValid(self.win):
            self.hide()
            return
        if self._close_rect().contains(event.position().toPoint()):
            self.win.request_close()
            self.hide()
            return
        self.hide()
        self.desktop.activate(self.win)

    def mouseMoveEvent(self, event):
        hot = self._close_rect().contains(event.position().toPoint())
        if hot != self.hover_close:
            self.hover_close = hot
            self.update()

    def leaveEvent(self, event):
        QTimer.singleShot(250, self._maybe_hide)

    def _maybe_hide(self):
        if not self.underMouse() and not self.desktop.taskbar.underMouse():
            self.hide()

    def _close_rect(self):
        return QRect(self.width() - 34, 8, 24, 24)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        draw_panel(p, self.rect())
        win = self.win
        if win is None or not isValid(win):
            return
        p.setFont(_font(12))
        p.setPen(QColor("#1A1A1A"))
        x = 12
        if not win.icon.isNull():
            p.drawPixmap(x, 12, win.icon.pixmap(16, 16))
            x += 22
        p.drawText(QRect(x, 8, self.width() - x - 40, 24), Qt.AlignVCenter | Qt.AlignLeft,
                   p.fontMetrics().elidedText(win.title, Qt.ElideRight, self.width() - x - 44))
        c = self._close_rect()
        if self.hover_close:
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(0, 0, 0, 18))
            p.drawRoundedRect(QRectF(c), 4, 4)
        p.setPen(QPen(QColor("#1A1A1A"), 1.2))
        p.drawLine(c.x() + 8, c.y() + 8, c.right() - 7, c.bottom() - 7)
        p.drawLine(c.right() - 7, c.y() + 8, c.x() + 8, c.bottom() - 7)
        shot = win.grab() if win.isVisible() else QPixmap()
        box = QRect(12, 40, self.width() - 24, self.height() - 52)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(0, 0, 0, 12))
        p.drawRoundedRect(QRectF(box), 4, 4)
        if shot.isNull():
            return
        shot = shot.scaled(box.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        p.drawPixmap(box.x() + (box.width() - shot.width()) // 2, box.y() + (box.height() - shot.height()) // 2, shot)


class Flyout(QWidget):
    """A panel that drops from the taskbar's right corner and goes away when you click elsewhere."""
    WIDTH, HEIGHT = 360, 400

    def __init__(self, desktop):
        super().__init__(desktop)
        self.desktop = desktop
        self.hover = None
        self.setMouseTracking(True)
        self.resize(self.WIDTH, self.HEIGHT)
        self.hide()

    def open(self):
        self.desktop.hide_start_menu()
        for other in self.desktop.taskbar.flyout_widgets():
            if other is not self:
                other.hide()
        avail = self.desktop.height() - TASKBAR_H - 24
        self.resize(self.WIDTH, min(self.HEIGHT, avail))
        self.move(self.desktop.width() - self.width() - 12, self.desktop.taskbar.y() - self.height() - 12)
        self.refresh()
        self.show()
        self.raise_()

    def refresh(self):
        pass

    def toggle(self):
        if self.isVisible():
            self.hide()
        else:
            self.open()

    def leaveEvent(self, event):
        self.hover = None
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        draw_panel(p, self.rect())
        self.draw(p)

    def draw(self, p):
        pass


SLIDER_CSS = """
QSlider { background: transparent; }
QSlider::groove:horizontal { height: 4px; background: #BDBDBD; border-radius: 2px; }
QSlider::sub-page:horizontal { background: %s; border-radius: 2px; }
QSlider::handle:horizontal { width: 10px; height: 10px; margin: -8px 0; border-radius: 10px; background: white;
                             border: 5px solid %s; }
"""


class QuickSettings(Flyout):
    """Wi-Fi, Bluetooth, Airplane mode, Night light, Accessibility and Cast tiles; brightness and volume."""
    WIDTH, HEIGHT = 360, 338
    TILES = ["Wi-Fi", "Bluetooth", "Airplane mode", "Night light", "Accessibility", "Cast"]

    def __init__(self, desktop):
        super().__init__(desktop)
        self.state = {"Wi-Fi": True, "Bluetooth": True}
        accent = _accent().name()
        self.brightness = QSlider(Qt.Horizontal, self)
        self.brightness.setRange(10, 100)
        self.brightness.setValue(80)
        self.volume = QSlider(Qt.Horizontal, self)
        self.volume.setRange(0, 100)
        for s in (self.brightness, self.volume):
            s.setStyleSheet(SLIDER_CSS % (accent, accent))
        self.volume.valueChanged.connect(self._volume_changed)
        self._placing = False

    def refresh(self):
        from . import volume
        accent = _accent().name()
        for s in (self.brightness, self.volume):
            s.setStyleSheet(SLIDER_CSS % (accent, accent))
        self._placing = True
        self.volume.setValue(int(round(volume.levels()["master"] * 100)))
        self._placing = False
        self.brightness.setGeometry(64, 196, self.width() - 88, 24)
        self.volume.setGeometry(64, 240, self.width() - 88, 24)

    def _volume_changed(self, v):
        if self._placing:
            return
        from . import volume
        volume.save(master=v / 100)
        if sound.is_muted() and v > 0:
            sound.set_muted(False)
        self.desktop.taskbar.update()

    def _tile_rects(self):
        out = []
        for i, name in enumerate(self.TILES):
            col, row = i % 3, i // 3
            out.append((name, QRect(16 + col * 112, 16 + row * 72, 104, 56)))
        return out

    def _footer_rects(self):
        return {"edit": QRect(16, self.height() - 48, 36, 32), "settings": QRect(self.width() - 52, self.height() - 48, 36, 32),
                "mute": QRect(16, 236, 40, 32)}

    def mouseMoveEvent(self, event):
        pos = event.position().toPoint()
        hover = next((n for n, r in self._tile_rects() if r.contains(pos)), None)
        if hover is None:
            hover = next((n for n, r in self._footer_rects().items() if r.contains(pos)), None)
        if hover != self.hover:
            self.hover = hover
            self.update()

    def mousePressEvent(self, event):
        pos = event.position().toPoint()
        for name, r in self._tile_rects():
            if r.contains(pos):
                if name == "Accessibility":
                    self.hide()
                    _open_settings(self.desktop, "accessibility")
                    return
                self.state[name] = not self.state.get(name, False)
                if name == "Airplane mode" and self.state[name]:
                    self.state["Wi-Fi"] = self.state["Bluetooth"] = False
                self.update()
                return
        foot = self._footer_rects()
        if foot["settings"].contains(pos):
            self.hide()
            _open_settings(self.desktop, "system")
        elif foot["mute"].contains(pos):
            sound.set_muted(not sound.is_muted())
            self.desktop.taskbar.update()
            self.update()
        elif foot["edit"].contains(pos):
            self.hide()
            _open_settings(self.desktop, "taskbar")

    def draw(self, p):
        accent = _accent()
        p.setFont(_font(11))
        for name, r in self._tile_rects():
            on = self.state.get(name, False)
            hot = self.hover == name
            p.setPen(QPen(QColor(0, 0, 0, 30), 1))
            if on:
                p.setBrush(accent.lighter(105) if hot else accent)
            else:
                p.setBrush(QColor(255, 255, 255, 230 if hot else 190))
            p.drawRoundedRect(QRectF(r).adjusted(0.5, 0.5, -0.5, -0.5), 6, 6)
            colour = QColor("white") if on else QColor("#1A1A1A")
            cx, cy = r.center().x(), r.y() + 20
            if name == "Wi-Fi":
                wifi_glyph(p, cx, cy, colour)
            elif name == "Bluetooth":
                pen = QPen(colour, 1.5)
                pen.setJoinStyle(Qt.RoundJoin)
                p.setPen(pen)
                path = QPainterPath()
                path.moveTo(cx - 4, cy - 4)
                path.lineTo(cx + 4, cy + 4)
                path.lineTo(cx, cy + 8)
                path.lineTo(cx, cy - 8)
                path.lineTo(cx + 4, cy - 4)
                path.lineTo(cx - 4, cy + 4)
                p.drawPath(path)
            elif name == "Airplane mode":
                pen = QPen(colour, 1.5)
                p.setPen(pen)
                p.drawLine(QPointF(cx, cy - 8), QPointF(cx, cy + 6))
                p.drawLine(QPointF(cx - 9, cy), QPointF(cx + 9, cy))
                p.drawLine(QPointF(cx - 4, cy + 7), QPointF(cx + 4, cy + 7))
            elif name == "Night light":
                p.setPen(QPen(colour, 1.5))
                p.setBrush(Qt.NoBrush)
                p.drawArc(QRectF(cx - 7, cy - 7, 14, 14), 30 * 16, 300 * 16)
            elif name == "Accessibility":
                p.setPen(QPen(colour, 1.5))
                p.setBrush(colour)
                p.drawEllipse(QPointF(cx, cy - 6), 1.8, 1.8)
                p.setBrush(Qt.NoBrush)
                p.drawLine(QPointF(cx - 6, cy - 2), QPointF(cx + 6, cy - 2))
                p.drawLine(QPointF(cx, cy - 2), QPointF(cx, cy + 3))
                p.drawLine(QPointF(cx, cy + 3), QPointF(cx - 4, cy + 9))
                p.drawLine(QPointF(cx, cy + 3), QPointF(cx + 4, cy + 9))
            else:
                p.setPen(QPen(colour, 1.5))
                p.setBrush(Qt.NoBrush)
                p.drawRoundedRect(QRectF(cx - 9, cy - 6, 18, 12), 2, 2)
                p.drawArc(QRectF(cx - 10, cy - 1, 10, 10), 270 * 16, 90 * 16)
            p.setPen(colour)
            p.drawText(QRect(r.x(), r.y() + 34, r.width(), 18), Qt.AlignCenter,
                       p.fontMetrics().elidedText(name, Qt.ElideRight, r.width() - 8))
        # the sliders' glyphs
        colour = QColor("#1A1A1A")
        p.setPen(QPen(colour, 1.5))
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(QPointF(36, 208), 5, 5)
        from math import cos, radians, sin
        for i in range(8):
            a = radians(i * 45)
            p.drawLine(QPointF(36 + cos(a) * 7.5, 208 + sin(a) * 7.5), QPointF(36 + cos(a) * 10, 208 + sin(a) * 10))
        from . import volume
        speaker_glyph(p, 36, 252, colour, sound.is_muted(), volume.levels()["master"])
        # the footer
        p.setPen(QPen(QColor(0, 0, 0, 20), 1))
        p.drawLine(0, self.height() - 56, self.width(), self.height() - 56)
        foot = self._footer_rects()
        for name, r in foot.items():
            if name == "mute":
                continue
            if self.hover == name:
                p.setPen(Qt.NoPen)
                p.setBrush(QColor(0, 0, 0, 16))
                p.drawRoundedRect(QRectF(r), 4, 4)
            p.setPen(QPen(colour, 1.4))
            p.setBrush(Qt.NoBrush)
            c = r.center()
            if name == "edit":
                p.drawLine(QPointF(c.x() - 5, c.y() + 5), QPointF(c.x() + 5, c.y() - 5))
                p.drawLine(QPointF(c.x() - 6, c.y() + 6), QPointF(c.x() - 3, c.y() + 5))
            else:
                p.drawEllipse(QPointF(c.x(), c.y()), 3, 3)
                p.drawEllipse(QPointF(c.x(), c.y()), 7, 7)
        p.setPen(QColor("#5C5C5C"))
        p.setFont(_font(11))
        p.drawText(QRect(60, self.height() - 48, self.width() - 120, 32), Qt.AlignCenter, "Workstation-2025 · Plugged in")


class NotificationCenter(Flyout):
    """Notifications on top (what the toasts said), the calendar underneath."""
    WIDTH, HEIGHT = 360, 640

    def __init__(self, desktop):
        super().__init__(desktop)
        self.month = None

    def refresh(self):
        self.month = None
        self.hover = None

    def _clear_rect(self):
        return QRect(self.width() - 90, 14, 74, 24)

    def _notes_height(self):
        n = len(self.desktop.notifications)
        return 56 + (max(1, min(n, 4)) * 70 if n else 90)

    def _cal_rect(self):
        top = self._notes_height() + 12
        return QRect(12, top, self.width() - 24, self.height() - top - 12)

    def mouseMoveEvent(self, event):
        pos = event.position().toPoint()
        hover = "clear" if self._clear_rect().contains(pos) and self.desktop.notifications else None
        cal = self._cal_rect()
        if QRect(cal.right() - 60, cal.y() + 8, 24, 24).contains(pos):
            hover = "prev"
        elif QRect(cal.right() - 32, cal.y() + 8, 24, 24).contains(pos):
            hover = "next"
        if hover != self.hover:
            self.hover = hover
            self.update()

    def mousePressEvent(self, event):
        pos = event.position().toPoint()
        if self._clear_rect().contains(pos):
            self.desktop.notifications.clear()
            self.update()
            return
        cal = self._cal_rect()
        now = clock.now()
        y, m = self.month or (now.year, now.month)
        if QRect(cal.right() - 60, cal.y() + 8, 24, 24).contains(pos):
            m -= 1
            if m == 0:
                y, m = y - 1, 12
            self.month = (y, m)
            self.update()
        elif QRect(cal.right() - 32, cal.y() + 8, 24, 24).contains(pos):
            m += 1
            if m == 13:
                y, m = y + 1, 1
            self.month = (y, m)
            self.update()
        elif QRect(cal.x(), cal.y(), cal.width() - 70, 40).contains(pos):
            self.month = None
            self.update()

    def draw(self, p):
        notes = self.desktop.notifications
        p.setFont(_font(14, bold=True))
        p.setPen(QColor("#1A1A1A"))
        p.drawText(QRect(16, 12, 200, 28), Qt.AlignVCenter | Qt.AlignLeft, "Notifications")
        if notes:
            cr = self._clear_rect()
            if self.hover == "clear":
                p.setPen(Qt.NoPen)
                p.setBrush(QColor(0, 0, 0, 16))
                p.drawRoundedRect(QRectF(cr), 4, 4)
            p.setFont(_font(12))
            p.setPen(QColor("#1A1A1A"))
            p.drawText(cr, Qt.AlignCenter, "Clear all")
        y = 48
        if not notes:
            p.setPen(QPen(QColor("#8A8A8A"), 1.4))
            p.setBrush(Qt.NoBrush)
            cx = self.width() / 2
            path = QPainterPath()
            path.moveTo(cx - 10, y + 30)
            path.lineTo(cx - 8, y + 16)
            path.quadTo(cx, y + 2, cx + 8, y + 16)
            path.lineTo(cx + 10, y + 30)
            path.closeSubpath()
            p.drawPath(path)
            p.drawLine(QPointF(cx - 3, y + 34), QPointF(cx + 3, y + 34))
            p.setFont(_font(12))
            p.setPen(QColor("#5C5C5C"))
            p.drawText(QRect(0, y + 44, self.width(), 24), Qt.AlignCenter, "No new notifications")
        else:
            for note in notes[:4]:
                r = QRect(12, y, self.width() - 24, 62)
                p.setPen(QPen(QColor(0, 0, 0, 22), 1))
                p.setBrush(QColor(255, 255, 255, 200))
                p.drawRoundedRect(QRectF(r).adjusted(0.5, 0.5, -0.5, -0.5), 6, 6)
                x = r.x() + 12
                icon = note.get("icon")
                if icon is not None and not icon.isNull():
                    p.drawPixmap(x, r.y() + 10, icon.pixmap(16, 16))
                p.setFont(_font(11))
                p.setPen(QColor("#5C5C5C"))
                p.drawText(QRect(x + 22, r.y() + 6, r.width() - 110, 20), Qt.AlignVCenter | Qt.AlignLeft, note["app"])
                p.drawText(QRect(r.right() - 70, r.y() + 6, 60, 20), Qt.AlignVCenter | Qt.AlignRight, note["time"])
                p.setFont(_font(12, bold=True))
                p.setPen(QColor("#1A1A1A"))
                p.drawText(QRect(x, r.y() + 26, r.width() - 24, 18), Qt.AlignVCenter | Qt.AlignLeft,
                           p.fontMetrics().elidedText(note["title"], Qt.ElideRight, r.width() - 24))
                p.setFont(_font(11))
                p.setPen(QColor("#5C5C5C"))
                p.drawText(QRect(x, r.y() + 42, r.width() - 24, 16), Qt.AlignVCenter | Qt.AlignLeft,
                           p.fontMetrics().elidedText(note["message"].replace("\n", " "), Qt.ElideRight, r.width() - 24))
                y += 70
        self._draw_calendar(p, self._cal_rect())

    def _draw_calendar(self, p, r):
        import calendar
        import datetime
        now = clock.now()
        y, m = self.month or (now.year, now.month)
        p.setPen(QPen(QColor(0, 0, 0, 22), 1))
        p.setBrush(QColor(255, 255, 255, 200))
        p.drawRoundedRect(QRectF(r).adjusted(0.5, 0.5, -0.5, -0.5), 8, 8)
        p.setFont(_font(13, bold=True))
        p.setPen(QColor("#1A1A1A"))
        p.drawText(QRect(r.x() + 16, r.y() + 8, r.width() - 100, 24), Qt.AlignVCenter | Qt.AlignLeft,
                   f"{now:%A, %B} {now.day}" if self.month is None else datetime.date(y, m, 1).strftime("%B %Y"))
        for name, dx, glyph in (("prev", 60, "∧"), ("next", 32, "∨")):
            br = QRect(r.right() - dx, r.y() + 8, 24, 24)
            if self.hover == name:
                p.setPen(Qt.NoPen)
                p.setBrush(QColor(0, 0, 0, 16))
                p.drawRoundedRect(QRectF(br), 4, 4)
            p.setPen(QColor("#1A1A1A"))
            p.setFont(_font(11))
            p.drawText(br, Qt.AlignCenter, glyph)
        cell_w = (r.width() - 24) / 7
        top = r.y() + 44
        p.setFont(_font(11))
        for i, d in enumerate(("Su", "Mo", "Tu", "We", "Th", "Fr", "Sa")):
            p.setPen(QColor("#5C5C5C"))
            p.drawText(QRectF(r.x() + 12 + i * cell_w, top, cell_w, 18), Qt.AlignCenter, d)
        first = datetime.date(y, m, 1)
        start_col = (first.weekday() + 1) % 7
        days = calendar.monthrange(y, m)[1]
        row_h = min(34, (r.bottom() - top - 24) / 6)
        yy = top + 22
        p.setFont(_font(12))
        for day in range(1, days + 1):
            col = (start_col + day - 1) % 7
            row = (start_col + day - 1) // 7
            cell = QRectF(r.x() + 12 + col * cell_w, yy + row * row_h, cell_w, row_h)
            today = (y, m, day) == (now.year, now.month, now.day)
            if today:
                p.setPen(Qt.NoPen)
                p.setBrush(_accent())
                d = min(cell.width(), cell.height()) - 4
                p.drawEllipse(QPointF(cell.center().x(), cell.center().y()), d / 2, d / 2)
                p.setPen(QColor("white"))
            else:
                p.setPen(QColor("#1A1A1A"))
            p.drawText(cell, Qt.AlignCenter, str(day))


class HiddenIcons(Flyout):
    """The hidden icon menu behind the chevron."""
    WIDTH, HEIGHT = 160, 60

    def open(self):
        shown, hidden = self.desktop.taskbar._tray_split()
        n = max(1, len(hidden))
        cols = min(4, n)
        rows = (n + cols - 1) // cols
        self.WIDTH, self.HEIGHT = cols * 40 + 16, rows * 40 + 16
        super().open()
        chev = self.desktop.taskbar.chevron_rect()
        x = self.desktop.taskbar.x() + chev.center().x() - self.width() // 2
        self.move(max(4, min(x, self.desktop.width() - self.width() - 4)), self.desktop.taskbar.y() - self.height() - 8)

    def _cells(self):
        _shown, hidden = self.desktop.taskbar._tray_split()
        out = []
        for i, icon in enumerate(hidden):
            out.append((icon, QRect(8 + (i % 4) * 40, 8 + (i // 4) * 40, 40, 40)))
        return out

    def mouseMoveEvent(self, event):
        pos = event.position().toPoint()
        hover = next((id(ic) for ic, r in self._cells() if r.contains(pos)), None)
        if hover != self.hover:
            self.hover = hover
            self.update()

    def event(self, event):
        if event.type() == QEvent.ToolTip:
            for ic, r in self._cells():
                if r.contains(event.pos()):
                    QToolTip.showText(event.globalPos(), ic.toolTip(), self)
                    return True
            QToolTip.hideText()
            return True
        return super().event(event)

    def mousePressEvent(self, event):
        from PySide6.QtWidgets import QSystemTrayIcon
        pos = event.position().toPoint()
        for ic, r in self._cells():
            if r.contains(pos):
                ic.touch()
                if event.button() == Qt.RightButton and ic.contextMenu() is not None:
                    self.hide()
                    ic.contextMenu().popup(event.globalPosition().toPoint())
                else:
                    self.hide()
                    ic.activated.emit(QSystemTrayIcon.Trigger)
                return

    def draw(self, p):
        for ic, r in self._cells():
            if self.hover == id(ic):
                p.setPen(Qt.NoPen)
                p.setBrush(QColor(0, 0, 0, 16))
                p.drawRoundedRect(QRectF(r).adjusted(2, 2, -2, -2), 4, 4)
            p.drawPixmap(r.x() + 12, r.y() + 12, ic.icon().pixmap(16, 16))


def _open_settings(desktop, page):
    try:
        from .settings import open_settings
        open_settings(desktop, page)
    except Exception:
        from .controlpanel import control_panel
        control_panel(desktop)


class Taskbar(QWidget):
    def __init__(self, desktop):
        super().__init__(desktop)
        self.desktop = desktop
        self.tray_icons = []
        self.flash_on = False
        self.setFixedHeight(TASKBAR_H)
        self.clock = QTimer(self)
        self.clock.timeout.connect(self.update)
        self.clock.start(1000)
        self.flasher = QTimer(self)
        self.flasher.timeout.connect(self._flash_tick)
        self.hover = None
        self.pressed = None
        self.thumb = Thumbnail(desktop)
        self.thumb_timer = QTimer(self)
        self.thumb_timer.setSingleShot(True)
        self.thumb_timer.timeout.connect(self._show_thumbnail)
        self.quick = QuickSettings(desktop)
        self.center = NotificationCenter(desktop)
        self.hidden_menu = HiddenIcons(desktop)
        self._cpl_cache = (0.0, {})
        self.start_down = False
        self.setMouseTracking(True)

    # ---- settings from Settings > Personalization > Taskbar ----
    def _setting(self, key, default):
        stamp, data = self._cpl_cache
        if time.monotonic() - stamp > 2:
            try:
                data = json.loads((DATA / "cpl.json").read_text(encoding="utf-8"))
            except (OSError, ValueError):
                data = {}
            self._cpl_cache = (time.monotonic(), data)
        return data.get(key, default)

    def flyout_widgets(self):
        return [self.quick, self.center, self.hidden_menu, self.thumb]

    def hide_flyouts(self):
        for f in self.flyout_widgets():
            f.hide()

    def raise_flyouts(self):
        for f in self.flyout_widgets():
            if f.isVisible():
                f.raise_()

    # ---- tray icons ----
    def add_tray_icon(self, icon):
        if icon not in self.tray_icons:
            self.tray_icons.append(icon)
            self.update()

    def remove_tray_icon(self, icon):
        if icon in self.tray_icons:
            self.tray_icons.remove(icon)
            self.update()

    def _live_tray_icons(self):
        return [i for i in self.tray_icons if isValid(i)]

    def _hidden(self, icon, data, now):
        from .tray import INACTIVE_SECONDS, behaviour
        mode = behaviour(icon.key, data) if icon.key else "auto"
        if mode == "show" or (self.desktop.balloon.isVisible() and self.desktop.balloon.owner is icon):
            return False
        if mode == "hide":
            return True
        return now - icon.last_used > INACTIVE_SECONDS

    def _tray_split(self):
        """(icons on show, the hidden ones)."""
        from .tray import tray_settings
        icons = self._live_tray_icons()
        if not icons:
            return [], []
        now = time.monotonic()
        data = tray_settings() if not hasattr(self, "_tray_data") or now - self._tray_data[0] > 2 else \
            self._tray_data[1]
        self._tray_data = (now, data)
        hidden = [i for i in icons if self._hidden(i, data, now)]
        return [i for i in icons if i not in hidden], hidden

    def _shown_tray_icons(self):
        return self._tray_split()[0]

    def tray_icon_rects(self):
        tray = self.tray_rect()
        y = (TASKBAR_H - 16) // 2
        x0 = tray.left() + 4 + (CHEVRON_W if self._tray_split()[1] else 0)
        return [(icon, QRect(x0 + i * TRAY_SLOT + 6, y, 16, 16)) for i, icon in enumerate(self._shown_tray_icons())]

    def chevron_rect(self):
        if not self._tray_split()[1]:
            return QRect()
        tray = self.tray_rect()
        return QRect(tray.left() + 4, (TASKBAR_H - 24) // 2, CHEVRON_W, 24)

    def tray_icon_center(self, icon):
        for ic, rect in self.tray_icon_rects():
            if ic is icon:
                return self.mapToParent(rect.center())
        return self.mapToParent(self.chevron_rect().center()) if self.chevron_rect().isValid() else None

    def _tray_icon_at(self, pos):
        for icon, rect in self.tray_icon_rects():
            if rect.contains(pos):
                return icon
        return None

    # ---- flashing ----
    def start_flashing(self):
        if not self.flasher.isActive():
            self.flash_on = True
            self.flasher.start(500)

    def _flash_tick(self):
        self.flash_on = not self.flash_on
        live = False
        for win in self.desktop.task_order:
            if win.flashing:
                win.flash_ticks += 1
                if win.flash_ticks < FLASHES * 2:
                    live = True
        if not live:
            self.flasher.stop()
            self.flash_on = True
        self.update()

    # ---- geometry ----
    def widgets_rect(self):
        return QRect(8, 0, WIDGETS_W, TASKBAR_H) if self._setting("show_widgets", True) else QRect()

    def tray_rect(self):
        shown = len(self._shown_tray_icons())
        w = 8 + (CHEVRON_W if self._tray_split()[1] else 0) + shown * TRAY_SLOT + SYS_W
        right = self.width() - SHOW_DESKTOP_W - CLOCK_W
        return QRect(right - w, 0, w, TASKBAR_H)

    def system_rect(self):
        """The network and volume pill (Quick Settings)."""
        tray = self.tray_rect()
        return QRect(tray.right() - SYS_W + 2, (TASKBAR_H - 36) // 2, SYS_W - 4, 36)

    def clock_rect(self):
        return QRect(self.width() - SHOW_DESKTOP_W - CLOCK_W, 0, CLOCK_W, TASKBAR_H)

    def show_desktop_rect(self):
        return QRect(self.width() - SHOW_DESKTOP_W, 0, SHOW_DESKTOP_W, TASKBAR_H)

    def speaker_rect(self):
        return self.system_rect()

    def items(self):
        """What sits in the middle after Start, Search and Task View: ("pinned", key) and ("win", window)."""
        out = []
        wins = [w for w in self.desktop.task_order if isValid(w)]
        used = set()
        for key in pinned():
            mine = [w for w in wins if getattr(w, "program", None) == key]
            if mine:
                for w in mine:
                    out.append(("win", w))
                    used.add(w)
            else:
                out.append(("pinned", key))
        for w in wins:
            if w not in used:
                out.append(("win", w))
        return out

    def button_rects(self):
        """[(rect, kind, payload)] for everything in the centre group, Start first."""
        items = self.items()
        show_search = self._setting("show_search", True)
        show_taskview = self._setting("show_taskview", True)
        total = BTN + GAP
        if show_search:
            total += SEARCH_W + GAP
        if show_taskview:
            total += BTN + GAP
        total += len(items) * (BTN + GAP)
        left_limit = (self.widgets_rect().right() + 12) if self.widgets_rect().isValid() else 8
        right_limit = self.tray_rect().left() - 8
        if self._setting("taskbar_align", "center") == "left":
            x = left_limit
        else:
            x = (self.width() - total) // 2
        x = max(left_limit, min(x, right_limit - total))
        y = (TASKBAR_H - BTN) // 2
        out = [(QRect(x, y, BTN, BTN), "start", None)]
        x += BTN + GAP
        if show_search:
            out.append((QRect(x, (TASKBAR_H - 32) // 2, SEARCH_W, 32), "search", None))
            x += SEARCH_W + GAP
        if show_taskview:
            out.append((QRect(x, y, BTN, BTN), "taskview", None))
            x += BTN + GAP
        for kind, payload in items:
            out.append((QRect(x, y, BTN, BTN), kind, payload))
            x += BTN + GAP
        return out

    def start_rect(self):
        return self.button_rects()[0][0]

    def _item_at(self, pos):
        for rect, kind, payload in self.button_rects():
            if rect.contains(pos):
                return rect, kind, payload
        return None

    # ---- events ----
    def event(self, event):
        if event.type() == QEvent.ToolTip:
            pos = event.pos()
            icon = self._tray_icon_at(pos)
            text = ""
            if icon is not None:
                text = icon.toolTip()
            elif self.show_desktop_rect().contains(pos):
                text = "Show desktop"
            elif self.clock_rect().contains(pos):
                text = clock.long_date_text()
            elif self.widgets_rect().contains(pos):
                text = "Widgets"
            elif self.system_rect().contains(pos):
                from . import volume
                text = "HomeNetwork\nInternet access\nSpeakers: " + \
                       ("Muted" if sound.is_muted() else f"{int(volume.levels()['master'] * 100)}%")
            elif self.chevron_rect().contains(pos):
                text = "Show hidden icons"
            else:
                hit = self._item_at(pos)
                if hit:
                    kind, payload = hit[1], hit[2]
                    if kind == "start":
                        text = "Start"
                    elif kind == "search":
                        text = "Search"
                    elif kind == "taskview":
                        text = "Task View"
                    elif kind == "pinned":
                        from claudexp import programs
                        try:
                            text = programs.get(payload).name
                        except StopIteration:
                            text = payload
            if text:
                QToolTip.showText(event.globalPos(), text, self)
            else:
                QToolTip.hideText()
            return True
        return super().event(event)

    def mousePressEvent(self, event):
        pos = event.position().toPoint()
        self.thumb.hide()
        hit = self._item_at(pos)
        if hit and hit[1] == "start":
            if event.button() == Qt.LeftButton:
                self.desktop.toggle_start_menu()
            elif event.button() == Qt.RightButton:
                self._start_menu(event.globalPosition().toPoint())
            return
        self.desktop.hide_start_menu()
        if event.button() == Qt.LeftButton:
            if self.widgets_rect().contains(pos):
                self.desktop.toggle_widgets()
                return
            if self.show_desktop_rect().contains(pos):
                self._show_desktop()
                return
            if self.clock_rect().contains(pos):
                self.center.toggle()
                return
            if self.chevron_rect().contains(pos):
                self.hidden_menu.toggle()
                return
            if self.system_rect().contains(pos):
                self.quick.toggle()
                return
            icon = self._tray_icon_at(pos)
            if icon is not None:
                icon.touch()
                from PySide6.QtWidgets import QSystemTrayIcon
                icon.activated.emit(QSystemTrayIcon.Trigger)
                return
            if hit:
                rect, kind, payload = hit
                if kind == "search":
                    self.desktop.toggle_start_menu()
                    self.desktop.start_menu.focus_search()
                elif kind == "taskview":
                    self._task_view()
                elif kind == "pinned":
                    from claudexp import programs
                    sound.play("navigate")
                    programs.launch(self.desktop, payload)
                else:
                    self.desktop.taskbar_clicked(payload)
                self.update()
        elif event.button() == Qt.RightButton:
            gp = event.globalPosition().toPoint()
            icon = self._tray_icon_at(pos)
            if icon is not None and icon.contextMenu() is not None:
                icon.touch()
                icon.contextMenu().popup(gp)
                return
            if self.system_rect().contains(pos):
                self._system_menu(gp)
                return
            if hit and hit[1] in ("pinned", "win"):
                self._item_menu(hit, gp)
            else:
                self._context_menu(gp)
        elif event.button() == Qt.MiddleButton:
            if hit and hit[1] == "win" and hit[2].program:
                from claudexp import programs
                programs.launch(self.desktop, hit[2].program)

    def mouseMoveEvent(self, event):
        pos = event.position().toPoint()
        hit = self._item_at(pos)
        key = (hit[1], id(hit[2])) if hit else None
        if key is None:
            for name, rect in (("widgets", self.widgets_rect()), ("system", self.system_rect()),
                               ("clock", self.clock_rect()), ("chevron", self.chevron_rect()),
                               ("sliver", self.show_desktop_rect())):
                if rect.isValid() and rect.contains(pos):
                    key = (name, 0)
        if key != self.hover:
            self.hover = key
            self.update()
            if hit and hit[1] == "win":
                self._hover_hit = hit
                self.thumb_timer.start(450)
            else:
                self.thumb_timer.stop()
                QTimer.singleShot(200, lambda: self.thumb.hide() if not self.thumb.underMouse() else None)

    def leaveEvent(self, event):
        self.hover = None
        self.thumb_timer.stop()
        QTimer.singleShot(250, lambda: self.thumb.hide() if not self.thumb.underMouse() else None)
        self.update()

    def _show_thumbnail(self):
        hit = getattr(self, "_hover_hit", None)
        if hit and self.hover == (hit[1], id(hit[2])) and isValid(hit[2]):
            self.thumb.show_for(hit[2], hit[0])

    # ---- menus and actions ----
    def _menu(self):
        from .shims import MENU_CSS
        menu = QMenu(self)
        menu.setStyleSheet(MENU_CSS)
        return menu

    def _start_menu(self, gp):
        """Win+X: the quick link menu behind a right-click on Start."""
        from claudexp import programs
        menu = self._menu()
        menu.addAction("Installed apps", lambda: _open_settings(self.desktop, "apps"))
        menu.addAction("Power Options", lambda: _open_settings(self.desktop, "system"))
        menu.addAction("System", lambda: _open_settings(self.desktop, "about"))
        menu.addSeparator()
        menu.addAction("Network Connections", lambda: __import__("claude11.network", fromlist=["get"]).get(self.desktop)._show_status())
        menu.addAction("Disk Management", lambda: programs.launch(self.desktop, "mycomputer"))
        menu.addAction("Task Manager", lambda: programs.launch(self.desktop, "taskmgr"))
        menu.addAction("Settings", lambda: _open_settings(self.desktop, "system"))
        menu.addAction("File Explorer", lambda: programs.launch(self.desktop, "mycomputer"))
        menu.addAction("Terminal", lambda: programs.launch(self.desktop, "cmd"))
        menu.addSeparator()
        power = menu.addMenu("Shut down or sign out")
        power.addAction("Sign out", self.desktop.log_off)
        power.addAction("Sleep", self.desktop.sleep)
        power.addAction("Shut down", self.desktop.turn_off)
        power.addAction("Restart", self.desktop.restart)
        menu.addAction("Desktop", self._show_desktop)
        menu.popup(gp)

    def _item_menu(self, hit, gp):
        from claudexp import programs
        rect, kind, payload = hit
        menu = self._menu()
        key = payload if kind == "pinned" else getattr(payload, "program", None)
        if key:
            try:
                prog = programs.get(key)
                menu.addAction(prog.icon(), prog.name, lambda: programs.launch(self.desktop, key))
                menu.addSeparator()
                if key in pinned():
                    menu.addAction("Unpin from taskbar", lambda: self._pin(key, False))
                else:
                    menu.addAction("Pin to taskbar", lambda: self._pin(key, True))
            except StopIteration:
                pass
        if kind == "win":
            menu.addAction("Close window", payload.request_close)
        menu.popup(gp)

    def _pin(self, key, on):
        keys = pinned()
        if on and key not in keys:
            keys.append(key)
        elif not on and key in keys:
            keys.remove(key)
        set_pinned(keys)
        self.update()

    def _system_menu(self, gp):
        menu = self._menu()
        from .volume import open_volume_control
        menu.addAction("Open volume mixer", lambda: open_volume_control(self.desktop))
        menu.addAction("Sound settings", lambda: _open_settings(self.desktop, "sound"))
        menu.addSeparator()
        from . import network
        menu.addAction("Network and Internet settings", lambda: network.get(self.desktop)._show_status())
        menu.addAction("Diagnose network problems", lambda: network.get(self.desktop)._troubleshoot())
        menu.popup(gp)

    def _context_menu(self, global_pos):
        from claudexp import programs
        menu = self._menu()
        menu.addAction("Task Manager", lambda: programs.launch(self.desktop, "taskmgr"))
        menu.addSeparator()
        menu.addAction("Taskbar settings", lambda: _open_settings(self.desktop, "taskbar"))
        menu.popup(global_pos)

    def _task_view(self):
        """Task View: Alt+Tab's switcher, left open until you pick a window."""
        from PySide6.QtWidgets import QApplication
        switcher = getattr(QApplication.instance(), "claude11_alttab", None) or getattr(self.window(), "alttab", None)
        if switcher is None:
            return
        if switcher.isVisible():
            switcher.commit()
        else:
            switcher.tab()
            switcher.index = 0
            switcher.update()

    def _visible_windows(self):
        return [w for w in self.desktop.windows if w.isVisible() and w.on_taskbar]

    def _show_desktop(self):
        self.desktop.toggle_show_desktop()

    # ---- painting ----
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        p.fillRect(self.rect(), _panel_colour(236))
        p.setPen(QPen(QColor(0, 0, 0, 24), 1))
        p.drawLine(0, 0, w, 0)
        accent = _accent()
        # the Widgets weather button
        wr = self.widgets_rect()
        if wr.isValid():
            self._hover_bg(p, QRect(wr.x(), (h - BTN) // 2, wr.width(), BTN), self.hover == ("widgets", 0))
            temp, cond = _weather()
            weather_glyph(p, QRect(wr.x() + 8, (h - 32) // 2, 32, 32), cond)
            p.setFont(_font(13))
            p.setPen(QColor("#1A1A1A"))
            p.drawText(QRect(wr.x() + 46, 8, wr.width() - 50, 18), Qt.AlignVCenter | Qt.AlignLeft, f"{temp}°F")
            p.setFont(_font(11))
            p.setPen(QColor("#5C5C5C"))
            p.drawText(QRect(wr.x() + 46, 25, wr.width() - 50, 16), Qt.AlignVCenter | Qt.AlignLeft, cond)
        # the centre group
        menu_open = self.desktop.start_menu.isVisible()
        for rect, kind, payload in self.button_rects():
            if kind == "start":
                self._hover_bg(p, rect, self.hover == ("start", id(None)) or menu_open or self.start_down)
                from .bios import draw_logo
                draw_logo(p, rect.center().x() + 0.5, rect.center().y() + 0.5, 9, accent.name(), glow=False)
            elif kind == "search":
                self._draw_search(p, rect)
            elif kind == "taskview":
                self._hover_bg(p, rect, self.hover == ("taskview", id(None)))
                c = rect.center()
                p.setPen(QPen(QColor("#1A1A1A"), 1.4))
                p.setBrush(Qt.NoBrush)
                p.drawRoundedRect(QRectF(c.x() - 8, c.y() - 4, 12, 10), 2, 2)
                p.setBrush(_panel_colour(255))
                p.drawRoundedRect(QRectF(c.x() - 3, c.y() - 7, 12, 10), 2, 2)
            else:
                self._paint_item(p, rect, kind, payload)
        # the tray
        chev = self.chevron_rect()
        if chev.isValid():
            self._hover_bg(p, chev, self.hover == ("chevron", 0), radius=4)
            p.setPen(QPen(QColor("#1A1A1A"), 1.3))
            cx, cy = chev.center().x(), chev.center().y()
            p.drawPolyline([QPointF(cx - 3.5, cy + 2), QPointF(cx, cy - 1.5), QPointF(cx + 3.5, cy + 2)])
        for icon, rect in self.tray_icon_rects():
            p.drawPixmap(rect, icon.icon().pixmap(16, 16))
        sr = self.system_rect()
        self._hover_bg(p, sr, self.hover == ("system", 0))
        wifi_glyph(p, sr.x() + 20, sr.center().y() - 2, QColor("#1A1A1A"))
        from . import volume
        speaker_glyph(p, sr.x() + 46, sr.center().y(), QColor("#1A1A1A"), sound.is_muted(), volume.levels()["master"])
        # the clock
        cr = self.clock_rect()
        self._hover_bg(p, QRect(cr.x(), (h - BTN) // 2, cr.width() - 4, BTN), self.hover == ("clock", 0) or
                       self.center.isVisible())
        p.setFont(_font(12))
        p.setPen(QColor("#1A1A1A"))
        p.drawText(QRect(cr.x(), 7, cr.width() - 12, 17), Qt.AlignVCenter | Qt.AlignRight, clock.time_text())
        p.drawText(QRect(cr.x(), 24, cr.width() - 12, 17), Qt.AlignVCenter | Qt.AlignRight, clock.date_text())
        # Show desktop
        sd = self.show_desktop_rect()
        if self.hover == ("sliver", 0):
            p.setPen(QPen(QColor(0, 0, 0, 90), 1))
            p.drawLine(sd.left(), 8, sd.left(), h - 8)

    def _hover_bg(self, p, rect, on, radius=6):
        if not on:
            return
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(0, 0, 0, 20))
        p.drawRoundedRect(QRectF(rect), radius, radius)

    def _draw_search(self, p, rect):
        r = QRectF(rect).adjusted(0.5, 0.5, -0.5, -0.5)
        hot = self.hover == ("search", id(None))
        p.setPen(QPen(QColor(0, 0, 0, 36), 1))
        p.setBrush(QColor(255, 255, 255, 235 if hot else 200))
        p.drawRoundedRect(r, 16, 16)
        c = QPointF(rect.x() + 20, rect.center().y())
        p.setPen(QPen(QColor("#1A1A1A"), 1.5))
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(QPointF(c.x() - 1, c.y() - 1), 5, 5)
        p.drawLine(QPointF(c.x() + 3, c.y() + 3), QPointF(c.x() + 6.5, c.y() + 6.5))
        p.setFont(_font(12))
        p.setPen(QColor("#5C5C5C"))
        p.drawText(QRect(rect.x() + 36, rect.y(), rect.width() - 44, rect.height()), Qt.AlignVCenter | Qt.AlignLeft,
                   "Search")

    def _paint_item(self, p, rect, kind, payload):
        active = kind == "win" and payload is self.desktop.active and payload.isVisible()
        hovered = self.hover == (kind, id(payload))
        flashing = kind == "win" and payload.flashing and self.flash_on
        icon = None
        if kind == "pinned":
            from claudexp import programs
            try:
                icon = programs.get(payload).icon()
            except StopIteration:
                icon = None
        else:
            icon = payload.icon if not payload.icon.isNull() else None
        if flashing:
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(255, 180, 60, 150))
            p.drawRoundedRect(QRectF(rect), 6, 6)
        elif active:
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(0, 0, 0, 30 if hovered else 20))
            p.drawRoundedRect(QRectF(rect), 6, 6)
        else:
            self._hover_bg(p, rect, hovered)
        if icon is not None:
            pm = icon.pixmap(ICON, ICON)
            p.drawPixmap(rect.x() + (rect.width() - pm.width()) // 2, rect.y() + (rect.height() - pm.height()) // 2 - 1,
                         pm)
        if kind == "win":
            p.setPen(Qt.NoPen)
            if active:
                p.setBrush(_accent())
                p.drawRoundedRect(QRectF(rect.center().x() - 8, rect.bottom() - 3, 16, 3), 1.5, 1.5)
            else:
                p.setBrush(QColor("#8A8A8A"))
                p.drawRoundedRect(QRectF(rect.center().x() - 3, rect.bottom() - 3, 6, 3), 1.5, 1.5)


def _weather():
    try:
        from .programs.widgets import weather_now
        return weather_now()
    except Exception:
        return 52, "Partly Cloudy"


def _menu_css():
    from .shims import MENU_CSS
    return MENU_CSS
