"""What you see while Kithylin has the computer: a sky-blue glow around the screen, a banner saying what he's doing
with Pause / Resume / Stop, and his own cursor - a second pointer that travels to what he's about to use. All of
them are children of the desktop widget, kept on top of the windows; only the banner takes the mouse."""
import math
import random

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPainterPath, QPen, QPolygonF, QRadialGradient
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget

SKY = QColor("#8FD3FF")                 # Kithylin's colour
SKY_DEEP = QColor("#3FA9F5")
INK = QColor(10, 24, 40, 215)


class Glow(QWidget):
    """A soft sky-blue glow along the four edges of the desktop, breathing slowly. Transparent to the mouse."""

    def __init__(self, desktop):
        super().__init__(desktop)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.phase = 0.0
        self.paused = False
        self.timer = QTimer(self, interval=50, timeout=self._tick)

    def start(self):
        self.setGeometry(self.parentWidget().rect())
        self.show()
        self.raise_()
        self.timer.start()

    def stop(self):
        self.timer.stop()
        self.hide()

    def _tick(self):
        self.phase += 0.05 if not self.paused else 0.015
        if self.geometry() != self.parentWidget().rect():
            self.setGeometry(self.parentWidget().rect())
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        w, h = self.width(), self.height()
        breath = 0.65 + 0.35 * math.sin(self.phase)
        alpha = int((70 if self.paused else 150) * breath)
        depth = 34
        colour = QColor(SKY) if not self.paused else QColor("#B8C8D8")
        for rect, start, end in ((QRectF(0, 0, w, depth), QPointF(0, 0), QPointF(0, depth)),
                                 (QRectF(0, h - depth, w, depth), QPointF(0, h), QPointF(0, h - depth)),
                                 (QRectF(0, 0, depth, h), QPointF(0, 0), QPointF(depth, 0)),
                                 (QRectF(w - depth, 0, depth, h), QPointF(w, 0), QPointF(w - depth, 0))):
            g = QLinearGradient(start, end)
            c0 = QColor(colour)
            c0.setAlpha(alpha)
            c1 = QColor(colour)
            c1.setAlpha(0)
            g.setColorAt(0, c0)
            g.setColorAt(1, c1)
            p.fillRect(rect, g)
        pen = QPen(QColor(colour.red(), colour.green(), colour.blue(), min(255, alpha + 60)), 3)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)
        p.drawRect(1, 1, w - 3, h - 3)


class Banner(QWidget):
    """The pill at the top of the screen: 'Kithylin is using this computer', how long, what he's doing, and the
    Pause / Resume and Stop buttons. The one piece of the HUD that takes the mouse."""

    def __init__(self, desktop, on_pause, on_stop):
        super().__init__(desktop)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_StyledBackground, False)
        self.paused = False
        lay = QHBoxLayout(self)
        lay.setContentsMargins(18, 8, 12, 8)
        lay.setSpacing(12)
        self.title = QLabel("Kithylin is using this computer")
        f = QFont("Tahoma")
        f.setPixelSize(13)
        f.setBold(True)
        self.title.setFont(f)
        self.title.setStyleSheet(f"color: {SKY.name()}; background: transparent;")
        self.status = QLabel("")
        f2 = QFont("Tahoma")
        f2.setPixelSize(12)
        self.status.setFont(f2)
        self.status.setStyleSheet("color: #E6F4FF; background: transparent;")
        self.status.setMinimumWidth(260)
        lay.addWidget(self.title)
        lay.addWidget(self.status, 1)
        self.setFixedWidth(820)                 # a fixed width: the buttons stay put while the status text changes
        css = ("QPushButton { background: rgba(143, 211, 255, 40); color: #E6F4FF; border: 1px solid rgba(143, 211, 255, 160);"
               " border-radius: 4px; padding: 3px 12px; font-family: Tahoma; font-size: 12px; }"
               "QPushButton:hover { background: rgba(143, 211, 255, 90); }")
        self.pause_btn = QPushButton("Pause")
        self.pause_btn.setStyleSheet(css)
        self.pause_btn.clicked.connect(on_pause)
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setStyleSheet(css)
        self.stop_btn.clicked.connect(on_stop)
        lay.addWidget(self.pause_btn)
        lay.addWidget(self.stop_btn)
        self.adjustSize()

    def set_status(self, text):
        from PySide6.QtGui import QFontMetrics
        room = max(80, self.width() - self.title.width() - self.pause_btn.width() - self.stop_btn.width() - 70)
        self.status.setText(QFontMetrics(self.status.font()).elidedText(text, Qt.ElideRight, room))
        self.place()

    def set_paused(self, paused, why=""):
        self.paused = paused
        self.pause_btn.setText("Resume" if paused else "Pause")
        self.title.setText("Kithylin is paused" + (f" - {why}" if why else "") if paused else "Kithylin is using this computer")
        self.title.setStyleSheet(f"color: {'#D8E4F0' if paused else SKY.name()}; background: transparent;")
        self.place()
        self.update()

    def place(self):
        parent = self.parentWidget()
        self.move((parent.width() - self.width()) // 2, 6)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        p.setBrush(INK)
        colour = QColor("#B8C8D8") if self.paused else SKY
        p.setPen(QPen(QColor(colour.red(), colour.green(), colour.blue(), 190), 1.2))
        p.drawRoundedRect(r, 14, 14)


class Cursor(QWidget):
    """Kithylin's pointer: a sky-blue arrow with a white edge and a soft halo, moved by Hands."""
    SIZE = 34

    def __init__(self, desktop):
        super().__init__(desktop)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(self.SIZE, self.SIZE)
        self.pressed = False
        self.pos_f = QPointF(desktop.width() / 2, desktop.height() / 2)
        self.set_pos(self.pos_f)

    def set_pos(self, point):
        self.pos_f = QPointF(point)
        self.move(int(point.x()) - 4, int(point.y()) - 3)        # the hot spot is the arrow's tip
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        halo = QRadialGradient(QPointF(6, 5), 18)
        halo.setColorAt(0, QColor(143, 211, 255, 120 if self.pressed else 70))
        halo.setColorAt(1, QColor(143, 211, 255, 0))
        p.setPen(Qt.NoPen)
        p.setBrush(halo)
        p.drawEllipse(QPointF(6, 5), 18, 18)
        arrow = QPolygonF([QPointF(4, 3), QPointF(4, 24), QPointF(9.5, 19), QPointF(13.5, 27.5), QPointF(17, 26),
                           QPointF(13, 18), QPointF(20, 18)])
        p.setPen(QPen(QColor("white"), 1.6))
        p.setBrush(SKY_DEEP if self.pressed else SKY)
        p.drawPolygon(arrow)


class Hands:
    """Kithylin's cursor and typing, as generator steps for the engine: `yield from hands.move_to(widget)` moves the
    pointer there over half a second or so; `yield from hands.type_into(editor, text)` types at human speed. One
    thing at a time: a leg takes the hands with `yield from hands.take(key)` and gives them back with release()."""

    def __init__(self, desktop, cursor, pace=1.0):
        self.desktop, self.cursor, self.pace = desktop, cursor, pace
        self.owner = None

    # ---- sharing ---------------------------------------------------------------------------------------------
    def take(self, key):
        while self.owner not in (None, key):
            yield 0.25
        self.owner = key

    def release(self, key):
        if self.owner == key:
            self.owner = None

    # ---- where things are --------------------------------------------------------------------------------------
    def point_of(self, target):
        """A point on the desktop for a widget (its centre, a little off), a (widget, QPoint) pair, or a QPointF."""
        if isinstance(target, QPointF):
            return target
        if isinstance(target, tuple):
            widget, local = target
            return QPointF(widget.mapTo(self.desktop, local))
        rect = target.rect()
        local = rect.center()
        jitter_x = int(rect.width() * random.uniform(-0.18, 0.18)) if rect.width() > 40 else 0
        jitter_y = int(rect.height() * random.uniform(-0.18, 0.18)) if rect.height() > 24 else 0
        return QPointF(target.mapTo(self.desktop, local + type(local)(jitter_x, jitter_y)))

    # ---- moving and clicking -------------------------------------------------------------------------------------
    def move_to(self, target, secs=None):
        start = QPointF(self.cursor.pos_f)
        end = self.point_of(target)
        dist = math.hypot(end.x() - start.x(), end.y() - start.y())
        if secs is None:
            secs = min(1.4, 0.25 + dist / 900) * self.pace
        steps = max(4, int(secs / 0.03))
        bulge = QPointF(-(end.y() - start.y()), end.x() - start.x()) * random.uniform(-0.12, 0.12)
        for i in range(1, steps + 1):
            t = i / steps
            e = t * t * (3 - 2 * t)                               # ease in and out
            pt = start + (end - start) * e + bulge * math.sin(math.pi * t)
            self.cursor.set_pos(pt)
            yield 0.03
        self.cursor.set_pos(end)

    def click(self, target, action=None):
        """Move to the target and 'click': the action runs (or the button's click()), with the pointer pressing."""
        yield from self.move_to(target)
        yield random.uniform(0.08, 0.2) * self.pace
        self.cursor.pressed = True
        self.cursor.update()
        yield 0.09
        self.cursor.pressed = False
        self.cursor.update()
        try:
            if action is not None:
                action()
            elif hasattr(target, "click"):
                target.click()
        except Exception:
            pass
        yield random.uniform(0.2, 0.5) * self.pace

    def type_into(self, editor, text, speed=9.0):
        """Type text into a QLineEdit / QTextEdit / QPlainTextEdit a few characters at a time, with pauses at spaces
        and punctuation. speed: characters a second, before the pace."""
        yield from self.move_to(editor)
        try:
            editor.setFocus()
        except Exception:
            pass
        yield random.uniform(0.3, 0.8) * self.pace
        cps = speed / max(self.pace, 0.05)
        i = 0
        while i < len(text):
            n = random.randint(1, 3)
            chunk = text[i:i + n]
            i += n
            _insert(editor, chunk)
            delay = len(chunk) / cps * random.uniform(0.6, 1.5)
            if chunk.strip() and chunk[-1] in ".,!?":
                delay += random.uniform(0.15, 0.45) * self.pace
            elif chunk.endswith(" ") and random.random() < 0.08:
                delay += random.uniform(0.3, 1.2) * self.pace            # thinking of the next word
            yield delay
        yield random.uniform(0.3, 0.9) * self.pace


def _insert(editor, text):
    if hasattr(editor, "insertPlainText"):
        editor.insertPlainText(text)
    elif hasattr(editor, "insert"):
        editor.insert(text)
    elif hasattr(editor, "setText"):
        editor.setText(editor.text() + text)
