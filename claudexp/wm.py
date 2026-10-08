"""XPWindow: a Luna-style window frame living inside the virtual desktop."""
from PySide6.QtCore import QEvent, QPoint, QRect, QRectF, QSize, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QIcon, QLinearGradient, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QApplication, QVBoxLayout, QWidget
from shiboken6 import isValid

TITLE_H = 30
BORDER = 4
RESIZE_MARGIN = 6
LEFT, RIGHT, TOP, BOTTOM = 1, 2, 4, 8


def _top_rounded_path(w, h, rad):
    path = QPainterPath()
    path.moveTo(0, h)
    path.lineTo(0, rad)
    path.quadTo(0, 0, rad, 0)
    path.lineTo(w - rad, 0)
    path.quadTo(w, 0, w, rad)
    path.lineTo(w, h)
    path.closeSubpath()
    return path


class XPWindow(QWidget):
    def __init__(self, desktop, title, content, icon=None, size=(480, 360),
                 buttons=("min", "max", "close"), on_taskbar=True):
        super().__init__(desktop)
        self.desktop = desktop
        self.title = title
        self.icon = icon or QIcon()
        self.content = content
        self.buttons = buttons
        self.on_taskbar = on_taskbar
        self.adopted = False     # content belongs to a hosted program (see hosting.py)
        self.placed = False      # position already chosen; don't cascade
        self.resizable = True
        self.flashing = False
        self.flash_ticks = 0
        self.active = False
        self.maximized = False
        self._normal_geom = None
        self._drag = None
        self._resize = None
        self._hover_btn = None
        self._press_btn = None
        self.setMouseTracking(True)
        self.setMinimumSize(220, 120)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(BORDER, TITLE_H, BORDER, BORDER)
        layout.setSpacing(0)
        layout.addWidget(content)
        self.resize(*size)

    def set_title(self, title):
        self.title = title
        self.update()
        self.desktop.taskbar.update()

    # ---- hosted content ---------------------------------------------------
    def adopt_content(self):
        """Follow the content's own show/hide/title/size changes (for hosted programs)."""
        self.adopted = True
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
        """A fixed-size program window gets a fixed-size frame around it."""
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
        """Give keyboard focus back to whatever had it in this window last."""
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
        """Flash this window's taskbar button orange until it's activated."""
        if self.active and self.isVisible():
            return
        self.flashing = True
        self.flash_ticks = 0
        self.desktop.taskbar.start_flashing()

    def request_close(self):
        """The X button: ask the content to close, like a real window manager would."""
        c = self.content
        c._host_user_close = True
        try:
            accepted = c.close()
        finally:
            if isValid(c):
                c._host_user_close = False
        if accepted and not self.adopted:
            self.desktop.close_window(self)

    # ---- geometry helpers -------------------------------------------------
    def _button_rects(self):
        s = 21
        y = (TITLE_H - s) // 2 + 1
        x = self.width() - BORDER - 2 - s
        rects = {}
        for kind in ("close", "max", "min"):
            if kind in self.buttons:
                rects[kind] = QRect(x, y, s, s)
                x -= s + 2
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

    # ---- actions ----------------------------------------------------------
    def toggle_maximize(self):
        if not self.resizable or "max" not in self.buttons:
            return
        if self.maximized:
            self.maximized = False
            self.setGeometry(self._normal_geom)
        else:
            self._normal_geom = self.geometry()
            self.maximized = True
            self.setGeometry(self.desktop.work_area())
        self.update()

    def _do_button(self, kind):
        if kind == "min":
            self.desktop.minimize(self)
        elif kind == "max":
            self.toggle_maximize()
        elif kind == "close":
            self.request_close()

    # ---- mouse ------------------------------------------------------------
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
        elif pos.y() < TITLE_H and not self.maximized:
            self._drag = pos

    def mouseMoveEvent(self, event):
        gp = event.globalPosition().toPoint()
        if self._drag is not None:
            new = self.parentWidget().mapFromGlobal(gp) - self._drag
            bottom = self.desktop.work_area().bottom() - TITLE_H
            new.setY(max(0, min(new.y(), bottom)))
            self.move(new)
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

    def mouseReleaseEvent(self, event):
        if self._press_btn:
            kind = self._press_btn
            self._press_btn = None
            self.update()
            if self._button_at(event.position().toPoint()) == kind:
                self._do_button(kind)
        self._drag = None
        self._resize = None

    def mouseDoubleClickEvent(self, event):
        pos = event.position().toPoint()
        if pos.y() < TITLE_H and not self._button_at(pos):
            self.toggle_maximize()

    def leaveEvent(self, event):
        if self._hover_btn:
            self._hover_btn = None
            self.update()

    # ---- painting ---------------------------------------------------------
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        rad = 0 if self.maximized else 8
        path = _top_rounded_path(w, h, rad)

        p.fillPath(path, QColor("#0831D9") if self.active else QColor("#7B97E0"))
        # Client area: what a real window would have under its content.
        p.fillRect(BORDER, TITLE_H, w - 2 * BORDER, h - TITLE_H - BORDER, self.palette().window())
        grad = QLinearGradient(0, 0, 0, TITLE_H)
        if self.active:
            stops = [(0, "#3D95FF"), (0.1, "#0A62F4"), (0.5, "#0055E5"), (0.9, "#0047D7"), (1, "#003DB6")]
        else:
            stops = [(0, "#B9CEF6"), (0.15, "#9DB9EB"), (0.6, "#94AFE8"), (1, "#7B97E0")]
        for at, color in stops:
            grad.setColorAt(at, QColor(color))
        p.save()
        p.setClipPath(path)
        p.fillRect(0, 0, w, TITLE_H, grad)
        p.restore()

        x = BORDER + 4
        if not self.icon.isNull():
            p.drawPixmap(x, (TITLE_H - 16) // 2, self.icon.pixmap(16, 16))
            x += 21
        font = QFont("Trebuchet MS", 10)
        font.setBold(True)
        p.setFont(font)
        rects = self._button_rects()
        text_w = min(r.left() for r in rects.values()) - x - 4 if rects else self.width() - x - BORDER
        text = p.fontMetrics().elidedText(self.title, Qt.ElideRight, text_w)
        trect = QRect(x, 0, text_w, TITLE_H)
        if self.active:
            p.setPen(QColor("#0A1F7A"))
            p.drawText(trect.translated(1, 1), Qt.AlignVCenter | Qt.AlignLeft, text)
        p.setPen(QColor("white") if self.active else QColor("#E2EAFA"))
        p.drawText(trect, Qt.AlignVCenter | Qt.AlignLeft, text)

        for kind, rect in self._button_rects().items():
            self._draw_button(p, rect, kind)

    def _draw_button(self, p, rect, kind):
        hover = self._hover_btn == kind
        down = hover and self._press_btn == kind
        if kind == "close":
            top, bot = ("#F09A7C", "#D2502E") if hover else ("#E8795A", "#C5371A")
        else:
            top, bot = ("#6FA6FF", "#2C6CF0") if hover else ("#4C8DFF", "#1E5EE6")
        if down:
            top, bot = bot, top
        if not self.active:
            top, bot = ("#C4D3F5", "#9DB2E8") if kind != "close" else ("#E7A894", "#D07A63")
        grad = QLinearGradient(0, rect.top(), 0, rect.bottom())
        grad.setColorAt(0, QColor(top))
        grad.setColorAt(1, QColor(bot))
        p.setPen(QPen(QColor("white"), 1))
        p.setBrush(grad)
        p.drawRoundedRect(QRectF(rect).adjusted(0.5, 0.5, -0.5, -0.5), 3, 3)

        x, y = rect.x(), rect.y()
        p.setBrush(Qt.NoBrush)
        if kind == "min":
            p.setPen(QPen(QColor("white"), 3))
            p.drawLine(x + 6, y + 14, x + 12, y + 14)
        elif kind == "max":
            p.setPen(QPen(QColor("white"), 1))
            p.drawRect(x + 5, y + 5, 10, 10)
            p.setPen(QPen(QColor("white"), 2))
            p.drawLine(x + 5, y + 6, x + 15, y + 6)
            if self.maximized:
                p.setPen(QPen(QColor("white"), 1))
                p.drawRect(x + 8, y + 3, 8, 8)
        else:
            p.setPen(QPen(QColor("white"), 2))
            p.drawLine(QPoint(x + 6, y + 6), QPoint(x + 14, y + 14))
            p.drawLine(QPoint(x + 14, y + 6), QPoint(x + 6, y + 14))
