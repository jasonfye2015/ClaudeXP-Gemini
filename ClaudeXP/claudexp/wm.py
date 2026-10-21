"""XPWindow: a Luna-style window frame living inside the virtual desktop."""
from PySide6.QtCore import QEvent, QPoint, QRect, QRectF, QSize, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QIcon, QLinearGradient, QPainter, QPainterPath, QPalette, QPen
from PySide6.QtWidgets import QApplication, QVBoxLayout, QWidget
from shiboken6 import isValid

TITLE_H = 30            # Luna's; the current visual style's are theme.title_h() / theme.border()
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
    skinned = False          # True for windows that draw their own frame (ClaudeAmp)

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
        from . import theme
        st = theme.current()
        layout.setContentsMargins(st.border, st.title_h, st.border, st.border)
        layout.setSpacing(0)
        layout.addWidget(content)
        if not content.testAttribute(Qt.WA_SetCursor):
            # the frame shows resize arrows near its edges; without its own cursor, the content would inherit them
            # (the frame stops hearing the mouse once it's over the content, so it can't put the arrow back)
            content.setCursor(Qt.ArrowCursor)
        self.resize(size[0] + 2 * (st.border - BORDER), size[1] + st.title_h - TITLE_H)
        if not self.skinned and st.palette() is not None:
            self.setPalette(st.palette())

    def set_title(self, title):
        self.title = title
        self.update()
        self.desktop.taskbar.update()

    # ---- hosted content ---------------------------------------------------
    def adopt_content(self):
        """Follow the content's own show/hide/title/size changes (for hosted programs)."""
        self.adopted = True
        self.setPalette(QPalette())            # hosted programs keep their own colours
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
            from . import theme
            want = c.minimumSize() + QSize(2 * theme.border(), theme.title_h() + theme.border())
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
        from . import theme
        return theme.current().button_rects(self.width(), self.buttons)

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
        elif pos.y() < self._title_h() and not self.maximized:
            self._drag = pos

    def mouseMoveEvent(self, event):
        gp = event.globalPosition().toPoint()
        if self._drag is not None:
            new = self.parentWidget().mapFromGlobal(gp) - self._drag
            bottom = self.desktop.work_area().bottom() - self._title_h()
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
        if pos.y() < self._title_h() and not self._button_at(pos):
            self.toggle_maximize()

    def leaveEvent(self, event):
        if self._resize is None:
            self.unsetCursor()
        if self._hover_btn:
            self._hover_btn = None
            self.update()

    def _title_h(self):
        from . import theme
        return theme.title_h()

    # ---- painting ---------------------------------------------------------
    def paintEvent(self, event):
        from . import theme
        st = theme.current()
        p = QPainter(self)
        w, h = self.width(), self.height()
        st.paint_frame(p, w, h, self.title, self.icon, self.active, self.buttons, self.maximized,
                       self._hover_btn, self._press_btn)
        # Client area: what a real window would have under its content.
        b, th = st.border, st.title_h
        p.fillRect(b, th, w - 2 * b, h - th - b, self.palette().window())
