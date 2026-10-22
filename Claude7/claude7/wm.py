"""AeroWindow: a Windows 7 Aero glass window frame living inside the virtual desktop.

The same interface as ClaudeXP's XPWindow (it is exported under that name too, so the period programs' windows come
out in glass here): title, icon, min/max/close, dragging, resizing from any edge, maximize, flashing on the taskbar,
adopted content for hosted programs - plus Aero Snap (drag a window to the top to maximize it, to a side to fill
that half) and the glass itself: a translucent, colour-tinted frame over whatever is behind it."""
from PySide6.QtCore import QEvent, QPoint, QPointF, QRect, QRectF, QSize, Qt, QTimer
from PySide6.QtGui import (QColor, QFont, QIcon, QLinearGradient, QPainter, QPainterPath, QPalette, QPen, QRegion)
from PySide6.QtWidgets import QApplication, QVBoxLayout, QWidget
from shiboken6 import isValid

TITLE_H = 30
BORDER = 8
RESIZE_MARGIN = 7
RADIUS = 7
LEFT, RIGHT, TOP, BOTTOM = 1, 2, 4, 8
BTN_H = 18
BTN_W = {"min": 27, "max": 27, "close": 45}
CLIENT = QColor("#F0F0F0")
launching = None          # the program key being launched right now (programs.launch sets it): windows tag themselves


def _aero():
    from . import display
    d = display.get()
    return d.aero_color(), d.aero_intensity()


def _frame_path(w, h, r=RADIUS):
    path = QPainterPath()
    path.moveTo(0, h)
    path.lineTo(0, r)
    path.quadTo(0, 0, r, 0)
    path.lineTo(w - r, 0)
    path.quadTo(w, 0, w, r)
    path.lineTo(w, h)
    path.closeSubpath()
    return path


class AeroWindow(QWidget):
    skinned = False

    def __init__(self, desktop, title, content, icon=None, size=(480, 360),
                 buttons=("min", "max", "close"), on_taskbar=True):
        super().__init__(desktop)
        self.desktop = desktop
        self.title = title
        self.icon = icon or QIcon()
        self.content = content
        self.buttons = buttons
        self.on_taskbar = on_taskbar
        self.program = launching
        self.adopted = False
        self.placed = False
        self.resizable = True
        self.flashing = False
        self.flash_ticks = 0
        self.active = False
        self.maximized = False
        self.snapped = None
        self._normal_geom = None
        self._drag = None
        self._resize = None
        self._hover_btn = None
        self._press_btn = None
        self._shake_track = []
        self.setMouseTracking(True)
        self.setMinimumSize(220, 120)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(BORDER, TITLE_H, BORDER, BORDER)
        layout.setSpacing(0)
        layout.addWidget(content)
        if not content.testAttribute(Qt.WA_SetCursor):
            content.setCursor(Qt.ArrowCursor)
        self.resize(size[0] + 2 * BORDER, size[1] + TITLE_H + BORDER)
        if not self.skinned:
            pal = self.palette()
            pal.setColor(QPalette.Window, CLIENT)
            self.setPalette(pal)

    def set_title(self, title):
        self.title = title
        self.update()
        self.desktop.taskbar.update()

    # ---- hosted content ---------------------------------------------------------------------------------------
    def adopt_content(self):
        self.adopted = True
        self.setPalette(QPalette())
        self.content.installEventFilter(self)
        self.content.windowTitleChanged.connect(self.set_title)
        self.content.destroyed.connect(self._content_destroyed)
        self.fit_fixed_content()

    def eventFilter(self, obj, event):
        if obj is self.content:
            kind = event.type()
            if kind == QEvent.ShowToParent:
                self.desktop.open_window(self)
            elif kind == QEvent.HideToParent:
                self.desktop.withdraw(self)
            elif kind == QEvent.Resize:
                self.fit_fixed_content()
        return False

    def _content_destroyed(self, *_):
        QTimer.singleShot(0, lambda: self.desktop.close_window(self) if isValid(self) else None)

    def fit_fixed_content(self):
        c = self.content
        fixed = c.minimumSize() == c.maximumSize()
        self.resizable = not fixed
        if fixed:
            self.buttons = tuple(b for b in self.buttons if b != "max")
            want = c.minimumSize() + QSize(2 * BORDER, TITLE_H + BORDER)
            if self.size() != want:
                self.setFixedSize(want)

    def notify_activation(self):
        if self.adopted and isValid(self.content):
            QApplication.sendEvent(self.content, QEvent(QEvent.ActivationChange))

    def focus_content(self):
        c = self.content
        fw = c.focusWidget()
        if fw is not None and (fw is c or c.isAncestorOf(fw)) and fw.isVisible():
            fw.setFocus()
            return
        for child in c.findChildren(QWidget):
            if child.isVisible() and child.isEnabled() and child.focusPolicy() & Qt.TabFocus:
                child.setFocus()
                return
        c.setFocus()

    def flash(self):
        if self.active and self.isVisible():
            return
        self.flashing = True
        self.flash_ticks = 0
        self.desktop.taskbar.start_flashing()

    def request_close(self):
        c = self.content
        c._host_user_close = True
        try:
            accepted = c.close()
        finally:
            if isValid(c):
                c._host_user_close = False
        if accepted and not self.adopted:
            self.desktop.close_window(self)

    # ---- geometry ---------------------------------------------------------------------------------------------
    def _button_rects(self):
        rects = {}
        x = self.width() - BORDER
        for kind in ("close", "max", "min"):
            if kind in self.buttons:
                w = BTN_W[kind]
                x -= w
                rects[kind] = QRect(x, 0, w, BTN_H + 1)
        return rects

    def _button_at(self, pos):
        for kind, rect in self._button_rects().items():
            if rect.contains(pos):
                return kind
        return None

    def _edges_at(self, pos):
        if self.maximized or not self.resizable:
            return 0
        m = RESIZE_MARGIN
        edges = 0
        if pos.x() < m:
            edges |= LEFT
        elif pos.x() >= self.width() - m:
            edges |= RIGHT
        if pos.y() < m:
            edges |= TOP
        elif pos.y() >= self.height() - m:
            edges |= BOTTOM
        return edges

    @staticmethod
    def _cursor_for(edges):
        if edges in (LEFT | TOP, RIGHT | BOTTOM):
            return Qt.SizeFDiagCursor
        if edges in (RIGHT | TOP, LEFT | BOTTOM):
            return Qt.SizeBDiagCursor
        if edges & (LEFT | RIGHT):
            return Qt.SizeHorCursor
        if edges & (TOP | BOTTOM):
            return Qt.SizeVerCursor
        return None

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.maximized:
            self.clearMask()
        else:
            path = _frame_path(self.width(), self.height())
            self.setMask(QRegion(path.toFillPolygon().toPolygon()))

    # ---- actions ----------------------------------------------------------------------------------------------
    def toggle_maximize(self):
        if not self.resizable or "max" not in self.buttons:
            return
        if self.maximized:
            self.maximized = False
            self.snapped = None
            self.setGeometry(self._normal_geom)
        else:
            self._normal_geom = self.geometry()
            self.maximized = True
            self.setGeometry(self.desktop.work_area())
        self.update()

    def snap(self, side):
        """Aero Snap: fill the left or right half of the screen."""
        if not self.resizable:
            return
        area = self.desktop.work_area()
        if self.snapped is None and not self.maximized:
            self._normal_geom = self.geometry()
        self.maximized = False
        self.snapped = side
        half = area.width() // 2
        self.setGeometry(QRect(area.left() if side == "left" else area.left() + half, area.top(), half, area.height()))
        self.update()

    def _unsnap_for_drag(self, pos):
        """Dragging a snapped or maximized window pulls it back to its normal size under the cursor."""
        if self._normal_geom is None:
            return pos
        frac = pos.x() / max(1, self.width())
        g = self._normal_geom
        self.maximized = False
        self.snapped = None
        self.resize(g.size())
        local = QPoint(int(frac * g.width()), min(pos.y(), TITLE_H - 4))
        self.update()
        return local

    def _do_button(self, kind):
        if kind == "min":
            self.desktop.minimize(self)
        elif kind == "max":
            self.toggle_maximize()
        elif kind == "close":
            self.request_close()

    # ---- mouse ------------------------------------------------------------------------------------------------
    def mousePressEvent(self, event):
        self.desktop.activate(self)
        if event.button() != Qt.LeftButton:
            return
        pos = event.position().toPoint()
        btn = self._button_at(pos)
        if btn:
            self._press_btn = btn
            self.update()
            return
        edges = self._edges_at(pos)
        if edges:
            self._resize = (edges, event.globalPosition().toPoint(), QRect(self.geometry()))
        elif pos.y() < TITLE_H:
            if self.maximized or self.snapped:
                pos = self._unsnap_for_drag(pos)
                self.move(self.parentWidget().mapFromGlobal(event.globalPosition().toPoint()) - pos)
            self._drag = pos
            self._shake_track = []

    def mouseMoveEvent(self, event):
        gp = event.globalPosition().toPoint()
        if self._drag is not None:
            new = self.parentWidget().mapFromGlobal(gp) - self._drag
            area = self.desktop.work_area()
            new.setY(max(0, min(new.y(), area.bottom() - TITLE_H)))
            self.move(new)
            self.desktop.snap_hint(self._snap_target(self.parentWidget().mapFromGlobal(gp)))
            return
        if self._resize:
            edges, start, g = self._resize
            d = gp - start
            r = QRect(g)
            mw, mh = self.minimumWidth(), self.minimumHeight()
            if edges & LEFT:
                r.setLeft(min(g.left() + d.x(), g.right() - mw + 1))
            if edges & RIGHT:
                r.setRight(max(g.right() + d.x(), g.left() + mw - 1))
            if edges & TOP:
                r.setTop(max(0, min(g.top() + d.y(), g.bottom() - mh + 1)))
            if edges & BOTTOM:
                r.setBottom(max(g.bottom() + d.y(), g.top() + mh - 1))
            self.setGeometry(r)
            return
        pos = event.position().toPoint()
        btn = self._button_at(pos)
        if btn != self._hover_btn:
            self._hover_btn = btn
            self.update()
        cursor = self._cursor_for(self._edges_at(pos))
        if cursor is None:
            self.unsetCursor()
        else:
            self.setCursor(cursor)

    def _snap_target(self, desktop_pos):
        """Which Aero Snap the cursor is asking for while dragging: 'max', 'left', 'right' or None."""
        if not self.resizable:
            return None
        area = self.desktop.work_area()
        if desktop_pos.y() <= area.top() + 2:
            return "max"
        if desktop_pos.x() <= area.left() + 2:
            return "left"
        if desktop_pos.x() >= area.right() - 2:
            return "right"
        return None

    def mouseReleaseEvent(self, event):
        if self._press_btn:
            kind = self._press_btn
            self._press_btn = None
            self.update()
            if self._button_at(event.position().toPoint()) == kind:
                self._do_button(kind)
        if self._drag is not None:
            self._drag = None
            self.desktop.snap_hint(None)
            target = self._snap_target(self.parentWidget().mapFromGlobal(event.globalPosition().toPoint()))
            if target == "max" and "max" in self.buttons:
                self._normal_geom = self.geometry()
                self.maximized = True
                self.setGeometry(self.desktop.work_area())
                self.update()
            elif target in ("left", "right"):
                self.snap(target)
        self._resize = None

    def mouseDoubleClickEvent(self, event):
        pos = event.position().toPoint()
        if pos.y() < TITLE_H and not self._button_at(pos):
            self.toggle_maximize()

    def leaveEvent(self, event):
        if self._resize is None:
            self.unsetCursor()
        if self._hover_btn:
            self._hover_btn = None
            self.update()

    def _title_h(self):
        return TITLE_H

    # ---- painting ---------------------------------------------------------------------------------------------
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        color, intensity = _aero()
        active = self.active
        # the glass: the window colour over what's behind, lighter when inactive
        tint = QColor(color)
        alpha = int(255 * (0.55 + 0.4 * intensity)) if active else 150
        tint.setAlpha(alpha)
        path = _frame_path(w, h) if not self.maximized else QPainterPath()
        if self.maximized:
            path.addRect(QRectF(0, 0, w, h))
        p.setPen(Qt.NoPen)
        p.setBrush(tint)
        p.drawPath(path)
        sheen = QLinearGradient(0, 0, 0, TITLE_H + 10)
        sheen.setColorAt(0, QColor(255, 255, 255, 140 if active else 110))
        sheen.setColorAt(0.5, QColor(255, 255, 255, 50))
        sheen.setColorAt(1, QColor(255, 255, 255, 25))
        p.setBrush(sheen)
        p.drawPath(path)
        # a soft highlight streak across the caption, as the Aero glass has
        streak = QPainterPath()
        streak.moveTo(w * 0.15, 0)
        streak.cubicTo(w * 0.35, TITLE_H * 0.9, w * 0.55, TITLE_H * 0.2, w * 0.95, TITLE_H * 0.8)
        streak.lineTo(w * 0.95, 0)
        streak.closeSubpath()
        p.setBrush(QColor(255, 255, 255, 38 if active else 20))
        p.drawPath(streak)
        # the client area and its sunken edge
        b, th = BORDER, TITLE_H
        client = QRect(b, th, w - 2 * b, h - th - b)
        p.fillRect(client, self.palette().window())
        p.setPen(QPen(QColor(0, 0, 0, 90), 1))
        p.setBrush(Qt.NoBrush)
        p.drawRect(QRectF(client).adjusted(-0.5, -0.5, 0.5, 0.5))
        p.setPen(QPen(QColor(255, 255, 255, 110), 1))
        p.drawRect(QRectF(client).adjusted(-1.5, -1.5, 1.5, 1.5))
        # the frame's outline: dark outside, light inside
        p.setPen(QPen(QColor(0, 0, 0, 170 if active else 110), 1))
        p.drawPath(_frame_path(w - 1, h - 1).translated(0.5, 0.5) if not self.maximized else path)
        p.setPen(QPen(QColor(255, 255, 255, 120), 1))
        p.drawPath(_frame_path(w - 3, h - 3, RADIUS - 1).translated(1.5, 1.5) if not self.maximized
                   else QPainterPath())
        # the caption: icon, title with its glow, buttons
        x = b + 2
        if not self.icon.isNull():
            p.drawPixmap(x, (TITLE_H - 16) // 2, self.icon.pixmap(16, 16))
            x += 22
        rects = self._button_rects()
        right = min((r.left() for r in rects.values()), default=w - b) - 6
        font = QFont("Segoe UI")
        font.setPixelSize(12)
        p.setFont(font)
        fm = p.fontMetrics()
        text = fm.elidedText(self.title, Qt.ElideRight, max(10, right - x))
        tw = fm.horizontalAdvance(text)
        glow = QRectF(x - 6, 3, tw + 12, TITLE_H - 6)
        gg = QLinearGradient(glow.topLeft(), glow.bottomLeft())
        gg.setColorAt(0, QColor(255, 255, 255, 0))
        gg.setColorAt(0.5, QColor(255, 255, 255, 150 if active else 90))
        gg.setColorAt(1, QColor(255, 255, 255, 0))
        p.setPen(Qt.NoPen)
        p.setBrush(gg)
        p.drawRoundedRect(glow, 8, 8)
        p.setPen(QColor("#000000") if active else QColor("#404040"))
        p.drawText(QRect(x, 0, right - x, TITLE_H), Qt.AlignVCenter | Qt.AlignLeft, text)
        for kind, r in rects.items():
            self._paint_button(p, r, kind, active)

    def _paint_button(self, p, r, kind, active):
        hot = self._hover_btn == kind
        down = self._press_btn == kind
        rr = QRectF(r).adjusted(0.5, 0.5, -0.5, -0.5)
        first = kind == ("min" if "min" in self.buttons else "max" if "max" in self.buttons else "close")
        last = kind == "close"
        path = QPainterPath()
        path.addRoundedRect(rr, 4, 4)
        if not (first and last):
            square = QPainterPath()
            if first:
                square.addRect(rr.adjusted(rr.width() / 2, 0, 0, 0))
            elif last:
                square.addRect(rr.adjusted(0, 0, -rr.width() / 2, 0))
            else:
                square.addRect(rr)
            path = path.united(square)
        g = QLinearGradient(rr.topLeft(), rr.bottomLeft())
        if kind == "close":
            if down:
                g.setColorAt(0, QColor("#E8A69E"))
                g.setColorAt(1, QColor("#9B2A24"))
            elif hot:
                g.setColorAt(0, QColor("#F2B3AB"))
                g.setColorAt(0.5, QColor("#DC5B4E"))
                g.setColorAt(1, QColor("#C7352A"))
            else:
                g.setColorAt(0, QColor("#E7A59B") if active else QColor(220, 190, 185))
                g.setColorAt(0.5, QColor("#CB5147") if active else QColor(200, 150, 145))
                g.setColorAt(1, QColor("#B6362B") if active else QColor(180, 130, 125))
        else:
            if down:
                g.setColorAt(0, QColor(180, 200, 220))
                g.setColorAt(1, QColor(120, 150, 185))
            elif hot:
                g.setColorAt(0, QColor(220, 235, 250))
                g.setColorAt(0.5, QColor(150, 190, 235))
                g.setColorAt(1, QColor(110, 160, 220))
            else:
                g.setColorAt(0, QColor(255, 255, 255, 120))
                g.setColorAt(0.5, QColor(255, 255, 255, 45))
                g.setColorAt(1, QColor(255, 255, 255, 60))
        p.setPen(QPen(QColor(0, 0, 0, 150), 1))
        p.setBrush(g)
        p.drawPath(path)
        p.setPen(QPen(QColor(255, 255, 255, 140), 1))
        p.setBrush(Qt.NoBrush)
        inner = QPainterPath()
        inner.addRoundedRect(rr.adjusted(1, 1, -1, -1), 3, 3)
        p.drawPath(inner)
        # the glyph
        c = rr.center()
        pen = QPen(QColor("#FFFFFF") if (kind == "close" or hot or down) else QColor("#F8F8F8"), 1.6)
        pen.setCapStyle(Qt.FlatCap)
        p.setPen(QPen(QColor(0, 0, 0, 120), 2.4))
        glyph = QPainterPath()
        if kind == "min":
            glyph.moveTo(c.x() - 4, c.y() + 3)
            glyph.lineTo(c.x() + 4, c.y() + 3)
        elif kind == "max":
            if self.maximized:
                glyph.addRect(QRectF(c.x() - 3, c.y() - 2, 7, 6))
                glyph.moveTo(c.x() - 1, c.y() - 4)
                glyph.lineTo(c.x() + 6, c.y() - 4)
                glyph.lineTo(c.x() + 6, c.y() + 2)
            else:
                glyph.addRect(QRectF(c.x() - 4.5, c.y() - 3.5, 9, 7))
        else:
            glyph.moveTo(c.x() - 4, c.y() - 4)
            glyph.lineTo(c.x() + 4, c.y() + 4)
            glyph.moveTo(c.x() + 4, c.y() - 4)
            glyph.lineTo(c.x() - 4, c.y() + 4)
        p.drawPath(glyph)
        p.setPen(pen)
        p.drawPath(glyph)


XPWindow = AeroWindow            # the period programs ask for XP's window class: they get Aero glass


def _top_rounded_path(w, h, rad):
    return _frame_path(w, h, rad)
