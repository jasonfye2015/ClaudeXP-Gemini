"""The view: the night drawn in first person, and over it as little as possible - a place's name when he first comes
into it, the fade in from black, a word about the mouse, and his own state in two orbs (ui/orbs.py): health and
poison, sanity and stupor. What she thinks of him has no meter: that will show in the den itself.

Keys: W A S D walk, Shift hurry, the mouse looks (click to take it, Esc gives it back and pauses), E (or L) shake the
lantern when it gutters out. On a strand, A and D lean against its sway.

The sound (ui/audio.py) hears what the night does, and follows the computer's mute."""
import math
import time

from PySide6.QtCore import QPoint, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QCursor, QFont, QPainter, QSurfaceFormat
from PySide6.QtOpenGLWidgets import QOpenGLWidget

from ..game.night import Input
from . import orbs
from ..game.death import ENDING

SENS = 0.0022
SERIF = "Georgia"


class GameView(QOpenGLWidget):
    def __init__(self, shell):
        super().__init__(shell)
        self.shell = shell
        fmt = QSurfaceFormat()
        fmt.setVersion(3, 3)
        fmt.setProfile(QSurfaceFormat.CoreProfile)
        fmt.setDepthBufferSize(24)
        fmt.setSamples(4)
        fmt.setSwapInterval(1)
        self.setFormat(fmt)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMouseTracking(True)
        self.night = None
        self.playing = False
        self.renderer = None
        self.gl_error = None
        self.keys = set()
        self.inp = Input()
        self.captured = False
        self.cards = []                          # (title, line, born)
        self.outs = 0                            # (how often the lantern has gone out: the hint shows the first times)
        self.whisper = None                      # (a few small words low on the screen: (words, when, how long))
        self.teeters = 0                         # (how often he's teetered on a strand: the hint shows the first times)
        self.tally = None                        # (this night's tallies, for the records)
        self.first_ending = False
        self.audio = None
        self.fade = None                         # (born): in from black
        self.last = time.perf_counter()
        self.t0 = self.last
        self.timer = QTimer(self)
        self.timer.setTimerType(Qt.PreciseTimer)
        self.timer.timeout.connect(self.tick)
        self.timer.start(0)

    # ---- GL ----------------------------------------------------------------------------------------------------
    def initializeGL(self):
        try:
            from ..engine.render import Renderer
            self.renderer = Renderer()
        except Exception as exc:                  # (shown on the view, not lost)
            import traceback
            traceback.print_exc()
            self.gl_error = str(exc)

    def paintGL(self):
        now = time.perf_counter() - self.t0
        if self.renderer and self.night:
            try:
                dpr = self.devicePixelRatioF()
                self.renderer.draw(self.night, int(self.width() * dpr), int(self.height() * dpr), now)
            except Exception as exc:
                import traceback
                traceback.print_exc()
                self.gl_error = repr(exc)
        p = QPainter(self)
        try:
            if self.gl_error:
                p.fillRect(self.rect(), QColor(8, 6, 10))
                p.setPen(QColor(220, 200, 190))
                p.drawText(self.rect().adjusted(30, 30, -30, -30), Qt.TextWordWrap, "The den couldn't be drawn:\n\n" + self.gl_error)
            elif self.playing:
                self.hud(p, now)
        finally:
            p.end()

    # ---- the loop ----------------------------------------------------------------------------------------------
    def begin(self, night):
        self.night = night
        self.playing = True
        night.show_lantern = True
        self.outs = 0
        self.teeters = 0
        self.whisper = None
        self.tally = {"bites": 0, "slips": 0, "falls": 0, "swipes": 0, "shakes": 0, "done": False}
        self.first_ending = False
        self.inp.yaw, self.inp.pitch = night.yaw, night.pitch
        self.inp.strafe = self.inp.forward = 0.0
        if self.audio is None:
            from .audio import DenAudio
            self.audio = DenAudio(self.shell.muted)
        self.fade = time.perf_counter()
        self.cards = []
        self.setFocus()

    def backdrop(self, night):
        """The title's backdrop: standing at the foot of the hollow, turning slowly, looking up into the dark."""
        self.night = night
        self.playing = False
        night.show_lantern = False                   # (no hand in the title's view)
        night.x, night.z = 0.8, 0.4
        night.y = night.tree.ground(0.8, 0.4)

    def tick(self):
        now = time.perf_counter()
        dt = min(0.05, now - self.last)
        self.last = now
        n = self.night
        if n is None:
            return
        if self.audio is not None:
            o = self.shell.records.options
            self.audio.volume = o["volume"] / 100.0
            self.audio.heartbeat = bool(o["heartbeat"])
        if self.playing and n.dying is not None and not self.shell.panel_open():      # (the end of him: no hands on it)
            n.step(dt, self.inp)
            if self.audio is not None:
                self.audio.hear(n, n.events)
            if n.dying.done:
                self.release()
                if self.tally is not None and not self.tally["done"]:
                    self.first_ending = self.shell.records.ending(ENDING[0].split(": ")[1])
                    self.night_done()
            n.events.clear()
        elif self.playing and not self.shell.panel_open():
            k = self.keys
            self.inp.forward = (1 if Qt.Key_W in k or Qt.Key_Up in k else 0) - (1 if Qt.Key_S in k or Qt.Key_Down in k else 0)
            self.inp.strafe = (1 if Qt.Key_D in k else 0) - (1 if Qt.Key_A in k else 0)
            self.inp.hurry = Qt.Key_Shift in k
            if Qt.Key_Left in k:
                self.inp.yaw -= 1.8 * dt
            if Qt.Key_Right in k:
                self.inp.yaw += 1.8 * dt
            n.step(dt, self.inp)
            if self.audio is not None:
                self.audio.hear(n, n.events)
            self._count(n.events)
            for e in n.events:
                if e[0] == "place":
                    self.cards.append((e[1], e[2], now))
                elif e[0] == "lantern" and e[1] == "out":
                    self.outs += 1
                elif e[0] == "lantern" and e[1] == "failed":
                    self.whisper = ("It won't catch.", now, 2.5)
                elif e[0] == "silk" and e[1] == "first":
                    self.whisper = ("The silk gives under you, and hums. Somewhere, something feels it.", now, 5.0)
                elif e[0] == "silk" and e[1] == "teeter":
                    self.teeters += 1
                elif e[0] == "silk" and e[1] == "caught":
                    self.whisper = ("Caught in her silk. Everything in the oak felt that.", now, 4.0)
                elif e[0] == "bitten":
                    self.whisper = ("Bitten." if e[1] == "face" else "Something bit your hand.", now, 2.5)
                elif e[0] == "hurt" and e[1] > 20:
                    self.whisper = ("You hit the wood hard.", now, 2.5)
            n.events.clear()
        elif not self.playing:
            n.time += dt
            n.yaw = (now - self.t0) * 0.06
            n.pitch = 0.62 + 0.08 * math.sin((now - self.t0) * 0.1)
            n.her.step(dt, n)                            # (and her, up there, watching the title)
        self.update()

    def _count(self, events):
        t = self.tally
        if t is None:
            return
        for e in events:
            if e[0] == "bitten":
                t["bites"] += 1
            elif e[0] == "silk" and e[1] == "slip":
                t["slips"] += 1
            elif e[0] == "hurt":
                t["falls"] += 1
            elif e[0] == "swipe":
                t["swipes"] += e[1]
            elif e[0] == "lantern" and e[1] == "shake":
                t["shakes"] += 1

    def night_done(self):
        """The night over (an ending, or left part-way): its tallies into the records, once."""
        t, n = self.tally, self.night
        if t is None or t["done"] or n is None or not self.playing:
            return
        t["done"] = True
        self.shell.records.night_over(dict(t, seconds=n.time))

    # ---- what's drawn over it ----------------------------------------------------------------------------------
    def hud(self, p, now):
        W, H = self.width(), self.height()
        t = time.perf_counter()
        p.setRenderHint(QPainter.Antialiasing)
        # a place's name, the first time he comes into it: it rises out of the dark and goes again
        self.cards = [c for c in self.cards if t - c[2] < 8.0]
        if self.cards:
            title, line, born = self.cards[-1]
            age = t - born
            a = max(0.0, min(1.0, age / 1.4, (8.0 - age) / 1.8))
            p.setPen(QColor(226, 212, 190, int(235 * a)))
            p.setFont(QFont(SERIF, 26))
            p.drawText(QRectF(0, H * 0.70, W, 44), Qt.AlignHCenter, title)
            p.setPen(QColor(200, 190, 176, int(200 * a)))
            f = QFont(SERIF, 13)
            f.setItalic(True)
            p.setFont(f)
            p.drawText(QRectF(W * 0.2, H * 0.70 + 48, W * 0.6, 60), Qt.AlignHCenter | Qt.TextWordWrap, line)
        n = self.night
        o = self.shell.records.options
        if n.dying is not None:
            if o["orbs"]:
                orbs.draw_orbs(p, W, H, n.body, t, max(0.0, 1.0 - n.dying.t / 1.2))
            orbs.draw_death(p, W, H, n.dying, t, self.first_ending)
            if o["heart"] and n.dying.black < 0.98:
                orbs.draw_heart(p, W, H, n.body, 1.0 - n.dying.black)       # (to the last beat, and the flat line)
            return
        if o["orbs"]:
            orbs.draw_danger(p, W, H, n.body, t)
            orbs.draw_orbs(p, W, H, n.body, t)
        if o["heart"]:
            orbs.draw_heart(p, W, H, n.body)
        if n.lamp.state == "out" and self.outs <= 3:             # (the lantern out: what to do, the first few times)
            a = int(150 + 60 * math.sin(t * 2.4))
            p.setPen(QColor(220, 200, 170, a))
            p.setFont(QFont(SERIF, 13))
            p.drawText(QRectF(0, H * 0.6, W, 30), Qt.AlignHCenter, "E   -   shake the lantern")
        if n.teetering and self.teeters <= 3:                    # (swaying on a strand: what to do, the first few times)
            p.setPen(QColor(220, 200, 170, int(150 + 60 * math.sin(t * 3.0))))
            p.setFont(QFont(SERIF, 13))
            p.drawText(QRectF(0, H * 0.6, W, 30), Qt.AlignHCenter, "A   D   -   lean against the sway")
        if self.whisper and t - self.whisper[1] < self.whisper[2]:
            p.setPen(QColor(210, 190, 170, int(220 * min(1.0, 1.6 * max(0.0, 1 - (t - self.whisper[1]) / self.whisper[2])))))
            f = QFont(SERIF, 13)
            f.setItalic(True)
            p.setFont(f)
            p.drawText(QRectF(0, H * 0.6 + 28, W, 30), Qt.AlignHCenter, self.whisper[0])
        if self.fade is not None:
            age = t - self.fade
            if age > 3.0:
                self.fade = None
            else:
                p.fillRect(self.rect(), QColor(0, 0, 0, int(255 * max(0.0, 1 - age / 3.0))))
        if not self.captured and not self.shell.panel_open():
            p.setPen(QColor(220, 208, 190, 170))
            p.setFont(QFont(SERIF, 12))
            p.drawText(QRectF(0, H * 0.5 + 40, W, 30), Qt.AlignHCenter, "Click to take the mouse   (Esc gives it back)")

    # ---- input -------------------------------------------------------------------------------------------------
    def capture(self):
        if self.captured or not self.playing:
            return
        self.captured = True
        self.setCursor(Qt.BlankCursor)
        self.grabMouse()
        self._centre()
        self.setFocus()

    def release(self):
        if not self.captured:
            return
        self.captured = False
        self.releaseMouse()
        self.unsetCursor()

    def _centre(self):
        c = self.mapToGlobal(QPoint(self.width() // 2, self.height() // 2))
        self._centre_at = c
        QCursor.setPos(c)

    def mousePressEvent(self, e):
        if self.playing and self.night is not None and self.night.dying is not None:
            if self.night.dying.done and self.night.dying.t > 26.0:
                self.shell.show_title()                          # (it's over: back to the start)
            return
        if self.playing and not self.captured:
            self.capture()

    def mouseMoveEvent(self, e):
        if not self.captured:
            return
        c = getattr(self, "_centre_at", None)
        gp = e.globalPosition().toPoint()
        if c is None or gp == c:
            return
        dx, dy = gp.x() - c.x(), gp.y() - c.y()
        sens = SENS * (0.35 + 1.3 * self.shell.records.options["look"] / 100.0)
        self.inp.yaw += dx * sens
        self.inp.pitch = max(-1.45, min(1.45, self.inp.pitch - dy * sens))
        self._centre()

    def keyPressEvent(self, e):
        if e.isAutoRepeat():
            return
        k = e.key()
        if k == Qt.Key_Escape:
            self.release()
            self.shell.pause()
            return
        if not self.playing:
            return
        self.keys.add(k)
        if k in (Qt.Key_E, Qt.Key_L) and self.night:             # (a shake of the lantern)
            self.night.lamp.shake()

    def keyReleaseEvent(self, e):
        if not e.isAutoRepeat():
            self.keys.discard(e.key())

    def focusOutEvent(self, e):
        self.keys.clear()
        super().focusOutEvent(e)
