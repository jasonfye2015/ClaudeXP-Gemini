"""Clippy on the desktop, and his yellow speech balloon (text, clickable options, and the 'What would you like
to do?' box)."""
from PySide6.QtCore import QPoint, QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QCursor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QMenu, QPushButton, QVBoxLayout, QWidget

from . import art

FPS = 30


class ClippyWidget(QWidget):
    clicked = Signal()
    menu_requested = Signal(QPoint)
    moved = Signal()

    def __init__(self, desktop):
        super().__init__(desktop)
        self.desktop = desktop
        self.scale = 1.0
        self.setFixedSize(art.W, art.H)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip("Clippy - click me for help! (right-click for options)")
        self.anim = art.Animator()
        self.pose = art.Pose()
        self._press = None
        self._dragged = False
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.hide()

    def showEvent(self, event):
        self.timer.start(1000 // FPS)
        super().showEvent(event)

    def hideEvent(self, event):
        self.timer.stop()
        super().hideEvent(event)

    def set_scale(self, scale):
        self.scale = scale
        self.setFixedSize(int(art.W * scale), int(art.H * scale))

    def set_style(self, mood, wire, accessory):
        self.anim.set_style(mood, wire, accessory)

    def _tick(self):
        if self.anim.name == "idle" and not self.anim.busy():
            follow = self.anim.face["follow"]
            if follow > 0.5:
                # idle: follow the mouse pointer with his eyes
                s = self.scale
                c = self.mapFromGlobal(QCursor.pos()) - QPoint(self.width() // 2, int(60 * s))
                dist = max(1.0, (c.x() ** 2 + c.y() ** 2) ** 0.5)
                reach = min(1.0, dist / (160 * s))
                self.anim.look_target = (c.x() / dist * reach, c.y() / dist * reach)
            else:                                                  # glum moods barely bother
                self.anim.look_target = self.anim.face["look"]
        self.pose = self.anim.step(1 / FPS)
        self.update()

    def play(self, name):
        self.anim.play(name)

    def paintEvent(self, event):
        p = QPainter(self)
        art.paint(p, self.pose, QRectF(self.rect()))

    # dragging him around, clicking him
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._press = event.globalPosition().toPoint() - self.pos()
            self._dragged = False
        elif event.button() == Qt.RightButton:
            self.menu_requested.emit(event.globalPosition().toPoint())

    def mouseMoveEvent(self, event):
        if self._press is None:
            return
        new = event.globalPosition().toPoint() - self._press
        if (new - self.pos()).manhattanLength() > 3 or self._dragged:
            self._dragged = True
            area = self.desktop.work_area()
            self.move(max(0, min(area.width() - self.width(), new.x())),
                      max(0, min(area.height() - self.height(), new.y())))
            self.moved.emit()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self._press is not None:
            self._press = None
            if not self._dragged:
                self.clicked.emit()


class SpeechBalloon(QWidget):
    """The pale-yellow balloon above Clippy."""
    option_chosen = Signal(str)
    asked = Signal(str)
    closed = Signal()
    chat_requested = Signal()
    WIDTH = 236
    TAIL = 14

    def __init__(self, desktop):
        super().__init__(desktop)
        self.desktop = desktop
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.tail_down = True
        self.tail_x = self.WIDTH - 50
        self.colours = ("#FFFFCC", "#000000", "#000000", "#0033AA")
        self.lay =  QVBoxLayout(self)
        self.lay.setSpacing(6)
        self.text = QLabel()
        self.text.setWordWrap(True)
        self.text.setTextFormat(Qt.PlainText)
        self.text.setStyleSheet("font-family: Tahoma; font-size: 11px; color: black; background: transparent;")
        self.lay.addWidget(self.text)
        self.options = QVBoxLayout()
        self.options.setSpacing(2)
        self.lay.addLayout(self.options)
        self.ask_row = QWidget()
        r = QHBoxLayout(self.ask_row)
        r.setContentsMargins(0, 2, 0, 0)
        r.setSpacing(4)
        self.edit = QLineEdit()
        self.edit.setPlaceholderText("Type your question here")
        self.edit.setStyleSheet("font-family: Tahoma; font-size: 11px; background: white; color: black;"
                                " border: 1px solid #7F9DB9; padding: 2px;")
        self.edit.returnPressed.connect(self._ask)
        search = QPushButton("Search")
        search.setFixedHeight(21)
        search.clicked.connect(self._ask)
        r.addWidget(self.edit, 1)
        r.addWidget(search)
        self.lay.addWidget(self.ask_row)
        self.bottom = QWidget()
        b = QHBoxLayout(self.bottom)
        b.setContentsMargins(0, 2, 0, 0)
        self.options_btn = QPushButton("Options")
        self.chat_btn = QPushButton("Chat...")
        self.close_btn = QPushButton("Close")
        for btn in (self.options_btn, self.chat_btn, self.close_btn):
            btn.setFixedHeight(21)
        self.close_btn.clicked.connect(self._close)
        self.chat_btn.clicked.connect(self.chat_requested.emit)
        b.addWidget(self.options_btn)
        b.addWidget(self.chat_btn)
        b.addStretch()
        b.addWidget(self.close_btn)
        self.lay.addWidget(self.bottom)
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self._timeout)
        self.hide()

    def set_theme(self, colours):
        """colours: (fill, border, text, link)."""
        self.colours = tuple(colours)
        self.text.setStyleSheet(f"font-family: Tahoma; font-size: 11px; color: {colours[2]};"
                                " background: transparent;")
        self.update()

    def say(self, text, options=(), ask=False, buttons=False, thinking=False):
        self.text.setText(text)
        link = self.colours[3]
        while self.options.count():
            w = self.options.takeAt(0).widget()
            if w is not None:
                w.hide()
                w.deleteLater()
        for opt in options:
            btn = QPushButton(f"●  {opt}")
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFlat(True)
            btn.setStyleSheet("QPushButton { text-align: left; border: none; background: transparent;"
                              " font-family: Tahoma; font-size: 11px; color: " + link + "; padding: 1px; }"
                              "QPushButton:hover { text-decoration: underline; }")
            btn.clicked.connect(lambda _c=False, o=opt: self.option_chosen.emit(o))
            self.options.addWidget(btn)
        self.ask_row.setVisible(ask)
        self.bottom.setVisible(buttons or ask)
        self.thinking = thinking
        if ask:
            self.edit.clear()
        self.adjust()
        self.show()
        self.raise_()
        if ask:
            self.edit.setFocus()
        # long enough to read, longer when there's something to click
        self.timer.stop()
        if not ask and not thinking:
            self.timer.start(int(min(26000, 7000 + 55 * len(text) + (6000 if options else 0))))

    def adjust(self):
        self.text.setFixedWidth(self.WIDTH - 24)
        top, bottom = (10, 10 + self.TAIL) if self.tail_down else (10 + self.TAIL, 10)
        self.lay.setContentsMargins(12, top, 12, bottom)
        self.setFixedWidth(self.WIDTH)
        self.lay.invalidate()
        self.lay.activate()
        h = self.lay.totalHeightForWidth(self.WIDTH) if self.lay.hasHeightForWidth() else -1
        self.setFixedHeight(max(h, self.lay.totalSizeHint().height()))

    def place(self, clippy):
        """Above Clippy, or below him when he's near the top of the screen."""
        self.tail_down = clippy.y() - self.height() > 0
        self.adjust()
        area = self.desktop.work_area()
        x = clippy.x() + clippy.width() // 2 - self.WIDTH + 46
        x = max(4, min(area.width() - self.WIDTH - 4, x))
        y = clippy.y() + int(44 * clippy.width() / art.W) - self.height() if self.tail_down else clippy.y() + clippy.height() - 6
        self.move(x, max(0, y))
        self.tail_x = max(20, min(self.WIDTH - 20, clippy.x() + clippy.width() // 2 - x))
        self.update()

    def enterEvent(self, event):
        self.timer.stop()                      # reading it: don't vanish

    def leaveEvent(self, event):
        if self.isVisible() and not self.ask_row.isVisible() and not getattr(self, "thinking", False):
            self.timer.start(4000)

    def _timeout(self):
        self.hide()
        self.closed.emit()

    def _close(self):
        self.timer.stop()
        self.hide()
        self.closed.emit()

    def _ask(self):
        text = self.edit.text().strip()
        if text:
            self.asked.emit(text)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        body = r.adjusted(0, 0, 0, -self.TAIL) if self.tail_down else r.adjusted(0, self.TAIL, 0, 0)
        path = QPainterPath()
        path.addRoundedRect(body, 10, 10)
        tail = QPainterPath()
        tx = self.tail_x
        if self.tail_down:
            tail.moveTo(tx - 14, body.bottom() - 2)
            tail.lineTo(tx + 6, r.bottom())
            tail.lineTo(tx - 2, body.bottom() - 2)
        else:
            tail.moveTo(tx - 14, body.top() + 2)
            tail.lineTo(tx + 6, r.top())
            tail.lineTo(tx - 2, body.top() + 2)
        tail.closeSubpath()
        path = path.united(tail)
        p.setPen(QPen(QColor(0, 0, 0, 60), 3))
        p.translate(2, 2)
        p.drawPath(path)                       # a soft shadow
        p.translate(-2, -2)
        p.setPen(QPen(QColor(self.colours[1]), 1))
        p.setBrush(QColor(self.colours[0]))
        p.drawPath(path)


def context_menu(parent, pos, actions):
    """actions: [(label, callback) or None for a separator]."""
    menu = QMenu(parent)
    for item in actions:
        if item is None:
            menu.addSeparator()
        else:
            menu.addAction(item[0], item[1])
    menu.exec(pos)
