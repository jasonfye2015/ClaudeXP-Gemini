"""MicaWindow: a Windows 11 window frame living inside the virtual desktop.

The same interface as ClaudeXP's XPWindow (it is exported under that name too, so the period programs' windows come
out in Windows 11's frame here): title, icon, min/max/close, dragging, resizing from any edge, maximize, flashing on
the taskbar, adopted content for hosted programs - plus Snap (drag a window to the top to maximize it, to a side to
fill that half, or rest on the maximize button for Snap layouts) and the frame itself: rounded corners, a Mica
caption that lets a little of the wallpaper's colour through, Fluent caption buttons and a soft shadow.

The widget is a little larger than the frame you see: a transparent margin (SHADOW) all round carries the shadow and
is where the invisible resize grips live, as on Windows 11."""
from PySide6.QtCore import QEvent, QPoint, QRect, QRectF, QSize, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPainterPath, QPalette, QPen, QRegion
from PySide6.QtWidgets import QApplication, QVBoxLayout, QWidget
from shiboken6 import isValid

SHADOW = 10
TITLE_H = 32
BORDER = 1
RESIZE_MARGIN = 5
RADIUS = 8
LEFT, RIGHT, TOP, BOTTOM = 1, 2, 4, 8
BTN_W = 46
BTN_H = TITLE_H
BTN_W_MAP = {"min": BTN_W, "max": BTN_W, "close": BTN_W}
CLIENT = QColor("#F3F3F3")
launching = None          # the program key being launched right now (programs.launch sets it): windows tag themselves
# Snap layouts: each layout is a list of zones (x, y, w, h) as fractions of the work area
SNAP_LAYOUTS = [
    [(0, 0, 0.5, 1), (0.5, 0, 0.5, 1)],
    [(0, 0, 2 / 3, 1), (2 / 3, 0, 1 / 3, 1)],
    [(0, 0, 1 / 3, 1), (1 / 3, 0, 1 / 3, 1), (2 / 3, 0, 1 / 3, 1)],
    [(0, 0, 0.25, 1), (0.25, 0, 0.5, 1), (0.75, 0, 0.25, 1)],
    [(0, 0, 0.5, 1), (0.5, 0, 0.5, 0.5), (0.5, 0.5, 0.5, 0.5)],
    [(0, 0, 0.5, 0.5), (0.5, 0, 0.5, 0.5), (0, 0.5, 0.5, 0.5), (0.5, 0.5, 0.5, 0.5)],
]


def _font(size=12, bold=False):
    from . import style
    return style.font(size, QFont.DemiBold if bold else QFont.Normal)


def _rounded(rect, radius=RADIUS):
    path = QPainterPath()
    path.addRoundedRect(QRectF(rect), radius, radius)
    return path


def _accent():
    from . import display
    return display.get().accent()


def _tint(active):
    """The caption and frame colour: Mica, a whisper of the wallpaper in the light grey."""
    try:
        from . import display
        wall = display.get().mica_tint()
    except Exception:
        wall = QColor("#F3F3F3")
    base = QColor(CLIENT)
    k = 0.08 if active else 0.04
    return QColor(int(base.red() * (1 - k) + wall.red() * k), int(base.green() * (1 - k) + wall.green() * k),
                  int(base.blue() * (1 - k) + wall.blue() * k))


class SnapLayouts(QWidget):
    """The little panel of layouts that drops from the maximize button; click a zone to put the window there."""
    CELL_W, CELL_H, GAP = 66, 44, 8

    def __init__(self, desktop):
        super().__init__(desktop)
        self.desktop = desktop
        self.win = None
        self.hover = None
        self.setMouseTracking(True)
        self.hide()
        cols, rows = 3, 2
        self.resize(cols * self.CELL_W + (cols + 1) * self.GAP, rows * self.CELL_H + (rows + 1) * self.GAP)

    def show_for(self, win, button_rect_global):
        self.win = win
        self.hover = None
        x = button_rect_global.center().x() - self.width() // 2
        x = max(4, min(x, self.desktop.width() - self.width() - 4))
        y = button_rect_global.bottom() + 4
        self.move(x, y)
        self.show()
        self.raise_()

    def _cells(self):
        out = []
        for i, layout in enumerate(SNAP_LAYOUTS):
            col, row = i % 3, i // 3
            cell = QRect(self.GAP + col * (self.CELL_W + self.GAP), self.GAP + row * (self.CELL_H + self.GAP),
                         self.CELL_W, self.CELL_H)
            zones = []
            for j, (fx, fy, fw, fh) in enumerate(layout):
                zones.append(((i, j), QRect(int(cell.x() + fx * cell.width()) + 1, int(cell.y() + fy * cell.height()) + 1,
                                            int(fw * cell.width()) - 2, int(fh * cell.height()) - 2)))
            out.append((cell, zones))
        return out

    def _zone_at(self, pos):
        for cell, zones in self._cells():
            for key, r in zones:
                if r.contains(pos):
                    return key
        return None

    def mouseMoveEvent(self, event):
        key = self._zone_at(event.position().toPoint())
        if key != self.hover:
            self.hover = key
            self.update()

    def leaveEvent(self, event):
        self.hover = None
        self.update()
        QTimer.singleShot(300, self._maybe_hide)

    def _maybe_hide(self):
        if not self.underMouse():
            self.hide()

    def mousePressEvent(self, event):
        key = self._zone_at(event.position().toPoint())
        self.hide()
        if key is not None and self.win is not None and isValid(self.win):
            i, j = key
            self.win.snap(SNAP_LAYOUTS[i][j])
            self.desktop.activate(self.win)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        p.setPen(QPen(QColor(0, 0, 0, 40), 1))
        p.setBrush(QColor(249, 249, 249, 245))
        p.drawRoundedRect(r, 8, 8)
        accent = _accent()
        for cell, zones in self._cells():
            for key, zr in zones:
                hot = self.hover == key
                p.setPen(QPen(QColor(0, 0, 0, 30), 1))
                p.setBrush(accent if hot else QColor(0, 0, 0, 22))
                p.drawRoundedRect(QRectF(zr), 3, 3)


class MicaWindow(QWidget):
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
        self._layouts_timer = QTimer(self)
        self._layouts_timer.setSingleShot(True)
        self._layouts_timer.timeout.connect(self._show_layouts)
        self.setMouseTracking(True)
        self.setMinimumSize(240 + 2 * SHADOW, 140 + 2 * SHADOW)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.addWidget(content)
        self._apply_margins()
        if not content.testAttribute(Qt.WA_SetCursor):
            content.setCursor(Qt.ArrowCursor)
        self.resize(size[0] + 2 * (SHADOW + BORDER), size[1] + TITLE_H + 2 * SHADOW + BORDER)
        if not self.skinned:
            pal = self.palette()
            pal.setColor(QPalette.Window, CLIENT)
            self.setPalette(pal)

    def _apply_margins(self):
        m = 0 if self.maximized else SHADOW
        self.layout().setContentsMargins(m + BORDER, m + TITLE_H, m + BORDER, m + BORDER)

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
            m = 0 if self.maximized else SHADOW
            want = c.minimumSize() + QSize(2 * (m + BORDER), TITLE_H + 2 * m + BORDER)
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
    def frame_rect(self):
        """The visible frame (the widget minus the shadow margin)."""
        if self.maximized:
            return self.rect()
        return self.rect().adjusted(SHADOW, SHADOW, -SHADOW, -SHADOW)

    def _button_rects(self):
        rects = {}
        fr = self.frame_rect()
        x = fr.right() + 1 - BORDER
        for kind in ("close", "max", "min"):
            if kind in self.buttons:
                w = BTN_W_MAP[kind]
                x -= w
                rects[kind] = QRect(x, fr.top() + BORDER, w, BTN_H - BORDER)
        return rects

    def _button_at(self, pos):
        for kind, rect in self._button_rects().items():
            if rect.contains(pos):
                return kind
        return None

    def _edges_at(self, pos):
        if self.maximized or not self.resizable:
            return 0
        fr = self.frame_rect()
        m = RESIZE_MARGIN
        edges = 0
        if pos.x() < fr.left() + m:
            edges |= LEFT
        elif pos.x() > fr.right() - m:
            edges |= RIGHT
        if pos.y() < fr.top() + m:
            edges |= TOP
        elif pos.y() > fr.bottom() - m:
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
        self._apply_mask()

    def _apply_mask(self):
        if self.maximized:
            self.clearMask()
            return
        fr = self.frame_rect()
        region = QRegion(self.rect()) - QRegion(fr)
        region += QRegion(_rounded(fr).toFillPolygon().toPolygon())
        self.setMask(region)

    # ---- actions ----------------------------------------------------------------------------------------------
    def _set_maximized(self, on):
        self.maximized = on
        self._apply_margins()
        self._apply_mask()

    def toggle_maximize(self):
        if not self.resizable or "max" not in self.buttons:
            return
        if self.maximized:
            self._set_maximized(False)
            self.snapped = None
            self.setGeometry(self._normal_geom)
        else:
            self._normal_geom = self.geometry()
            self._set_maximized(True)
            self.setGeometry(self.desktop.work_area())
        self.update()

    def snap(self, zone):
        """Snap: 'left' or 'right' for a half, or a (x, y, w, h) fraction zone from Snap layouts."""
        if not self.resizable:
            return
        area = self.desktop.work_area()
        if self.snapped is None and not self.maximized:
            self._normal_geom = self.geometry()
        self._set_maximized(False)
        if zone == "left":
            zone = (0, 0, 0.5, 1)
        elif zone == "right":
            zone = (0.5, 0, 0.5, 1)
        self.snapped = tuple(zone)
        fx, fy, fw, fh = zone
        x = area.left() + round(fx * area.width()) - SHADOW
        y = area.top() + round(fy * area.height()) - SHADOW
        w = round(fw * area.width()) + 2 * SHADOW
        h = round(fh * area.height()) + 2 * SHADOW
        self.setGeometry(QRect(x, y, w, h))
        self.update()

    def _unsnap_for_drag(self, pos):
        """Dragging a snapped or maximized window pulls it back to its normal size under the cursor."""
        if self._normal_geom is None:
            return pos
        frac = pos.x() / max(1, self.width())
        g = self._normal_geom
        self._set_maximized(False)
        self.snapped = None
        self.resize(g.size())
        local = QPoint(int(frac * g.width()), min(pos.y(), SHADOW + TITLE_H - 4))
        self.update()
        return local

    def _do_button(self, kind):
        if kind == "min":
            self.desktop.minimize(self)
        elif kind == "max":
            self.toggle_maximize()
        elif kind == "close":
            self.request_close()

    def _show_layouts(self):
        if self._hover_btn == "max" and self.resizable and "max" in self.buttons and self.isVisible():
            panel = getattr(self.desktop, "snap_layouts", None)
            if panel is not None:
                r = self._button_rects()["max"]
                panel.show_for(self, QRect(self.mapToParent(r.topLeft()), r.size()))

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
        elif pos.y() < self.frame_rect().top() + TITLE_H:
            if self.maximized or self.snapped:
                pos = self._unsnap_for_drag(pos)
                self.move(self.parentWidget().mapFromGlobal(event.globalPosition().toPoint()) - pos)
            self._drag = pos

    def mouseMoveEvent(self, event):
        gp = event.globalPosition().toPoint()
        if self._drag is not None:
            new = self.parentWidget().mapFromGlobal(gp) - self._drag
            area = self.desktop.work_area()
            new.setY(max(-SHADOW, min(new.y(), area.bottom() - TITLE_H)))
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
                r.setTop(max(-SHADOW, min(g.top() + d.y(), g.bottom() - mh + 1)))
            if edges & BOTTOM:
                r.setBottom(max(g.bottom() + d.y(), g.top() + mh - 1))
            self.setGeometry(r)
            return
        pos = event.position().toPoint()
        btn = self._button_at(pos)
        if btn != self._hover_btn:
            self._hover_btn = btn
            self.update()
            if btn == "max":
                self._layouts_timer.start(650)
            else:
                self._layouts_timer.stop()
        cursor = self._cursor_for(self._edges_at(pos))
        if cursor is None:
            self.unsetCursor()
        else:
            self.setCursor(cursor)

    def _snap_target(self, desktop_pos):
        """Which Snap the cursor is asking for while dragging: 'max', 'left', 'right' or None."""
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
                self._set_maximized(True)
                self.setGeometry(self.desktop.work_area())
                self.update()
            elif target in ("left", "right"):
                self.snap(target)
        self._resize = None

    def mouseDoubleClickEvent(self, event):
        pos = event.position().toPoint()
        if pos.y() < self.frame_rect().top() + TITLE_H and not self._button_at(pos) and not self._edges_at(pos):
            self.toggle_maximize()

    def leaveEvent(self, event):
        if self._resize is None:
            self.unsetCursor()
        self._layouts_timer.stop()
        if self._hover_btn:
            self._hover_btn = None
            self.update()

    def _title_h(self):
        return TITLE_H

    # ---- painting ---------------------------------------------------------------------------------------------
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        active = self.active
        fr = self.frame_rect()
        if not self.maximized:
            # the shadow: soft rings in the transparent margin, deeper for the active window
            for i in range(SHADOW, 0, -1):
                alpha = int((22 if active else 12) * (1 - i / SHADOW) ** 1.6) + 1
                p.setPen(Qt.NoPen)
                p.setBrush(QColor(0, 0, 0, alpha))
                p.drawRoundedRect(QRectF(fr).adjusted(-i, -i + 2, i, i + 2), RADIUS + i, RADIUS + i)
        frame_path = _rounded(fr) if not self.maximized else QPainterPath()
        if self.maximized:
            frame_path.addRect(QRectF(fr))
        p.setPen(Qt.NoPen)
        p.setBrush(_tint(active))
        p.drawPath(frame_path)
        # the client area
        client = QRect(fr.left() + BORDER, fr.top() + TITLE_H, fr.width() - 2 * BORDER, fr.height() - TITLE_H - BORDER)
        p.save()
        p.setClipPath(frame_path)
        p.fillRect(client, self.palette().window())
        p.restore()
        # the frame's outline
        p.setPen(QPen(QColor(0, 0, 0, 70 if active else 45), 1))
        p.setBrush(Qt.NoBrush)
        if self.maximized:
            p.drawRect(QRectF(fr).adjusted(0.5, 0.5, -0.5, -0.5))
        else:
            p.drawRoundedRect(QRectF(fr).adjusted(0.5, 0.5, -0.5, -0.5), RADIUS, RADIUS)
        # the caption: icon, title, buttons
        x = fr.left() + 16
        if not self.icon.isNull():
            p.drawPixmap(x, fr.top() + (TITLE_H - 16) // 2, self.icon.pixmap(16, 16))
            x += 28
        rects = self._button_rects()
        right = min((r.left() for r in rects.values()), default=fr.right()) - 8
        p.setFont(_font(12))
        fm = p.fontMetrics()
        text = fm.elidedText(self.title, Qt.ElideRight, max(10, right - x))
        p.setPen(QColor("#1A1A1A") if active else QColor("#8A8A8A"))
        p.drawText(QRect(x, fr.top(), right - x, TITLE_H), Qt.AlignVCenter | Qt.AlignLeft, text)
        for kind, r in rects.items():
            self._paint_button(p, r, kind, active)

    def _paint_button(self, p, r, kind, active):
        hot = self._hover_btn == kind
        down = self._press_btn == kind
        rr = QRectF(r)
        if kind == "close" and (hot or down):
            p.setPen(Qt.NoPen)
            p.setBrush(QColor("#C42B1C") if not down else QColor("#C84031"))
            if self.maximized:
                p.drawRect(rr)
            else:
                path = QPainterPath()
                path.addRect(rr)
                path = path.intersected(_rounded(self.frame_rect()))
                p.drawPath(path)
        elif hot or down:
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(0, 0, 0, 24 if down else 16))
            p.drawRect(rr)
        c = rr.center()
        colour = QColor("#FFFFFF") if (kind == "close" and (hot or down)) else \
            QColor("#1A1A1A") if active else QColor("#9D9D9D")
        pen = QPen(colour, 1)
        pen.setCapStyle(Qt.FlatCap)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)
        if kind == "min":
            p.drawLine(QRectF(c.x() - 5, c.y() + 0.5, 10, 0).topLeft(), QRectF(c.x() + 5, c.y() + 0.5, 0, 0).topLeft())
        elif kind == "max":
            if self.maximized:
                p.drawRoundedRect(QRectF(c.x() - 5, c.y() - 3, 8, 8), 1, 1)
                path = QPainterPath()
                path.moveTo(c.x() - 3, c.y() - 3)
                path.lineTo(c.x() - 3, c.y() - 5)
                path.quadTo(c.x() - 3, c.y() - 6, c.x() - 2, c.y() - 6)
                path.lineTo(c.x() + 4, c.y() - 6)
                path.quadTo(c.x() + 5, c.y() - 6, c.x() + 5, c.y() - 5)
                path.lineTo(c.x() + 5, c.y() + 1)
                path.quadTo(c.x() + 5, c.y() + 2, c.x() + 4, c.y() + 2)
                path.lineTo(c.x() + 3, c.y() + 2)
                p.drawPath(path)
            else:
                p.drawRoundedRect(QRectF(c.x() - 5, c.y() - 5, 10, 10), 1.5, 1.5)
        else:
            p.drawLine(QRectF(c.x() - 5, c.y() - 5, 0, 0).topLeft(), QRectF(c.x() + 5, c.y() + 5, 0, 0).topLeft())
            p.drawLine(QRectF(c.x() + 5, c.y() - 5, 0, 0).topLeft(), QRectF(c.x() - 5, c.y() + 5, 0, 0).topLeft())


XPWindow = MicaWindow            # the period programs ask for XP's window class: they get Windows 11's frame
AeroWindow = MicaWindow


def _top_rounded_path(w, h, rad):
    return _rounded(QRect(0, 0, w, h), rad)
