"""Claudeggle - aim, shoot, and watch the ball pinball down through the pegs. In the spirit of Peggle.

Clear every orange peg in ten balls. Green pegs set off the level's power, the purple peg is worth 500 and moves
each shot, the bucket at the bottom gives the ball back, and hitting the last orange peg sets off Extreme Fever.

Mouse to aim, click (or Space) to shoot, Esc to pause.
"""
import json
import math
import random
import time

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import (QBrush, QColor, QFont, QIcon, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap,
                           QRadialGradient, QTransform)
from PySide6.QtWidgets import QWidget
from shiboken6 import isValid

from ... import sound
from ...paths import DATA
from ...wm import XPWindow
from . import game as G

PROGRESS = DATA / "claudeggle" / "progress.json"
VW, VH = 980, 640                        # the whole screen in logical pixels
FX, FY = 110, 32                         # where the field sits in it
PEG_RGB = {"blue": "#2C7CF4", "orange": "#FF8A1C", "green": "#36CC4C", "purple": "#B24CF0"}
THEMES = [("#0B1A3A", "#2A5A8A", "#E8E0B0"), ("#2A0A3A", "#7A3A8A", "#F0C0E0"), ("#08262A", "#1A6A6A", "#C0F0E0"),
          ("#0A1C40", "#2070B0", "#FFFFFF"), ("#1A1208", "#6A4A1A", "#F0D080"), ("#3A0818", "#A03050", "#FFD0E0"),
          ("#14202A", "#4A6A7A", "#F0E8C8"), ("#0A2A10", "#3A8A3A", "#E0FFC0"), ("#2A1A06", "#B07A20", "#FFF0C0"),
          ("#02020E", "#16163A", "#C0D0FF"), ("#2A2006", "#C09020", "#FFFFE0"), ("#1A0430", "#5020A0", "#FFE0A0")]
FEVER_RGB = ["#3070F0", "#30C050", "#F0C020", "#30C050", "#3070F0"]


def peggle_icon():
    ic = QIcon()
    for sz in (16, 32, 48):
        pm = QPixmap(sz, sz)
        pm.fill(Qt.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.Antialiasing)
        s = sz / 32
        g = QLinearGradient(0, 0, 0, sz)
        g.setColorAt(0, QColor("#1A3A7A"))
        g.setColorAt(1, QColor("#3A7AC0"))
        p.setPen(QPen(QColor("#0A1A3A"), max(1.0, s)))
        p.setBrush(QBrush(g))
        p.drawRoundedRect(QRectF(1 * s, 1 * s, 30 * s, 30 * s), 6 * s, 6 * s)
        for (x, y, c) in ((9, 12, "orange"), (19, 9, "blue"), (24, 19, "orange"), (13, 22, "blue"), (6, 26, "green")):
            _peg(p, QPointF(x * s, y * s), 3.6 * s, PEG_RGB[c], False)
        _ball(p, QPointF(18 * s, 16 * s), 3 * s)
        p.end()
        ic.addPixmap(pm)
    return ic


def _peg(p, c, r, colour, lit):
    base = QColor(colour)
    if lit:
        glow = QRadialGradient(c, r * 2.2)
        glow.setColorAt(0, QColor(base.red(), base.green(), base.blue(), 160))
        glow.setColorAt(1, QColor(base.red(), base.green(), base.blue(), 0))
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(glow))
        p.drawEllipse(c, r * 2.2, r * 2.2)
        base = base.lighter(150)
    g = QRadialGradient(QPointF(c.x() - r * 0.35, c.y() - r * 0.4), r * 1.3)
    g.setColorAt(0, base.lighter(170))
    g.setColorAt(0.5, base)
    g.setColorAt(1, base.darker(170))
    p.setPen(QPen(base.darker(220), max(0.6, r * 0.12)))
    p.setBrush(QBrush(g))
    p.drawEllipse(c, r, r)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(255, 255, 255, 200 if lit else 150))
    p.drawEllipse(QPointF(c.x() - r * 0.32, c.y() - r * 0.38), r * 0.3, r * 0.22)


def _ball(p, c, r, fire=False, spooky=False):
    if fire:
        glow = QRadialGradient(c, r * 3)
        glow.setColorAt(0, QColor(255, 220, 80, 220))
        glow.setColorAt(1, QColor(255, 60, 0, 0))
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(glow))
        p.drawEllipse(c, r * 3, r * 3)
    g = QRadialGradient(QPointF(c.x() - r * 0.35, c.y() - r * 0.4), r * 1.4)
    if spooky:
        g.setColorAt(0, QColor(230, 255, 240, 230))
        g.setColorAt(1, QColor(80, 160, 120, 200))
    else:
        g.setColorAt(0, QColor("#FFFFFF"))
        g.setColorAt(0.6, QColor("#B8C0CC"))
        g.setColorAt(1, QColor("#5A6070"))
    p.setPen(QPen(QColor(40, 40, 50), max(0.6, r * 0.12)))
    p.setBrush(QBrush(g))
    p.drawEllipse(c, r, r)


def load_progress():
    try:
        d = json.loads(PROGRESS.read_text(encoding="utf-8"))
        return {"unlocked": int(d.get("unlocked", 1)), "best": {int(k): v for k, v in d.get("best", {}).items()}}
    except (OSError, ValueError):
        return {"unlocked": 1, "best": {}}


class Peggle(QWidget):
    def __init__(self, desktop):
        super().__init__()
        self.desktop = desktop
        self.frame = None
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMinimumSize(VW * 3 // 4, VH * 3 // 4)
        self.state = "title"                  # title, levels, play, paused
        self.progress = load_progress()
        self.game = None
        self.mouse = QPointF(-1, -1)          # in logical coordinates
        self.buttons = []
        self.particles = []                   # [x, y, vx, vy, life, colour, size] in field coordinates
        self.popups = []                      # [x, y, text, age, colour, size]
        self.banner = None                    # [text, age, colour]
        self.bg = {}
        self.fireworks_t = 0.0
        self.t = 0.0
        self.last = time.monotonic()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(16)

    # ---- coordinates -----------------------------------------------------------------------------------------
    def _xf(self):
        sc = min(self.width() / VW, self.height() / VH)
        t = QTransform()
        t.translate((self.width() - VW * sc) / 2, (self.height() - VH * sc) / 2)
        t.scale(sc, sc)
        return t

    def _logical(self, pos):
        inv, _ok = self._xf().inverted()
        return inv.map(pos)

    # ---- a level -------------------------------------------------------------------------------------------
    def start_level(self, index):
        self.game = G.Game(index)
        self.state = "play"
        self.particles, self.popups = [], []
        name, desc = G.POWERS[self.game.power]
        self.banner = [f"Level {index + 1}: {self.game.name}", 0.0, "#FFFFFF", f"Green pegs: {name} - {desc}"]
        self.recorded = False
        self.setFocus()

    def _record(self):
        g = self.game
        if self.recorded:
            return
        self.recorded = True
        if g.state == "won":
            self.progress["unlocked"] = max(self.progress["unlocked"], min(len(G.LEVELS), g.index + 2))
            if g.score > self.progress["best"].get(g.index, 0):
                self.progress["best"][g.index] = g.score
            sound.play("notify")
        else:
            sound.play("exclamation")
        try:
            PROGRESS.parent.mkdir(parents=True, exist_ok=True)
            PROGRESS.write_text(json.dumps({"unlocked": self.progress["unlocked"],
                                            "best": {str(k): v for k, v in self.progress["best"].items()}}),
                                encoding="utf-8")
        except OSError:
            pass

    # ---- the loop -------------------------------------------------------------------------------------------
    def _tick(self):
        now = time.monotonic()
        dt = min(0.04, now - self.last)
        self.last = now
        self.t += dt
        g = self.game
        if self.state == "play" and g is not None:
            g.step(dt)
            for e in g.events:
                self._event(e)
            if g.state in ("won", "lost"):
                self._record()
            if g.fever and g.state in ("clearing", "won"):
                self.fireworks_t -= dt
                if self.fireworks_t <= 0:
                    self.fireworks_t = 0.25
                    self._firework(random.uniform(80, G.W - 80), random.uniform(80, 300))
        for pt in self.particles:
            pt[0] += pt[2] * dt
            pt[1] += pt[3] * dt
            pt[3] += 300 * dt
            pt[4] -= dt
        self.particles = [pt for pt in self.particles if pt[4] > 0]
        for pp in self.popups:
            pp[3] += dt
        self.popups = [pp for pp in self.popups if pp[3] < 1.2]
        if self.banner:
            self.banner[1] += dt
            if self.banner[1] > (4.0 if len(self.banner) > 3 else 2.0):
                self.banner = None
        self.update()

    def _event(self, e):
        kind = e[0]
        if kind == "hit":
            p, pts = e[1], e[2]
            x, y = p.centre()
            self.popups.append([x, y - 12, str(pts), 0.0, PEG_RGB[p.colour], 10 if pts < 500 else 13])
        elif kind == "pop":
            p = e[1]
            x, y = p.centre()
            for _ in range(7):
                a = random.uniform(0, math.tau)
                sp = random.uniform(40, 170)
                self.particles.append([x, y, math.cos(a) * sp, math.sin(a) * sp - 60, random.uniform(0.35, 0.7),
                                       QColor(PEG_RGB[p.colour]).lighter(140), random.uniform(1.5, 3)])
        elif kind == "free":
            self.banner = [e[1], 0.0, "#80FF80"]
            sound.play("ding")
        elif kind == "fever":
            self.banner = ["EXTREME FEVER!", 0.0, "#FFE040"]
            sound.play("notify")
        elif kind == "power":
            name = G.POWERS[e[1]][0]
            self.popups.append([e[2], e[3] - 24, name + "!", 0.0, "#60FF70", 15])
        elif kind == "style":
            self.banner = [e[1], 0.0, "#FFB0F0"]
        elif kind == "spooky":
            self.popups.append([e[1], 30, "Spooky!", 0.0, "#C0FFD0", 15])
        elif kind == "fever_slot":
            v = G.FEVER_SLOTS[e[1]]
            self.banner = [f"+{v:,}!", 0.0, "#FFFFFF"]
            for _ in range(5):
                self._firework(random.uniform(80, G.W - 80), random.uniform(80, 320))

    def _firework(self, x, y):
        col = QColor.fromHsv(random.randrange(360), 180, 255)
        for i in range(28):
            a = i / 28 * math.tau
            sp = random.uniform(110, 190)
            self.particles.append([x, y, math.cos(a) * sp, math.sin(a) * sp, random.uniform(0.7, 1.1), col, 2.4])

    # ---- input ----------------------------------------------------------------------------------------------
    def mouseMoveEvent(self, e):
        self.mouse = self._logical(e.position())

    def mousePressEvent(self, e):
        self.setFocus()
        pos = self._logical(e.position())
        self.mouse = pos
        for rect, action in reversed(self.buttons):
            if rect.contains(pos):
                sound.play("menu")
                action()
                return
        if self.state == "play" and e.button() == Qt.LeftButton:
            self._shoot()

    def _shoot(self):
        g = self.game
        if g and g.state == "aim":
            g.shoot(self._angle())

    def _angle(self):
        return self.game.aim_angle(self.mouse.x() - FX, self.mouse.y() - FY)

    def keyPressEvent(self, e):
        k = e.key()
        if self.state == "play":
            if k == Qt.Key_Escape:
                self.state = "paused"
            elif k == Qt.Key_Space:
                self._shoot()
        elif self.state == "paused" and k in (Qt.Key_Escape, Qt.Key_Space):
            self._resume()
        elif self.state == "title" and k in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space):
            self.state = "levels"

    def _resume(self):
        self.state = "play"
        self.last = time.monotonic()

    # ---- painting --------------------------------------------------------------------------------------------
    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor("#05060C"))
        p.setTransform(self._xf())
        self.buttons = []
        if self.state == "title":
            self._draw_title(p)
        elif self.state == "levels":
            self._draw_levels(p)
        else:
            self._draw_play(p)
            g = self.game
            if self.state == "paused":
                self._overlay(p, "Paused", [f"{g.name} - score {g.score:,}"],
                              [("Resume", self._resume, "#3A8A3A"), ("Restart Level", lambda: self.start_level(g.index), "#7A5A20"),
                               ("Level Select", lambda: setattr(self, "state", "levels"), "#3A4A7A")])
            elif g.state == "won":
                lines = [f"Score: {g.score:,}", f"Shots taken: {g.shots}",
                         f"Balls left: {g.balls_left} (+{g.balls_left * 10000:,})"]
                best = self.progress["best"].get(g.index, 0)
                if best == g.score:
                    lines.append("A new best for this level!")
                buttons = []
                if g.index + 1 < len(G.LEVELS):
                    buttons.append(("Next Level", lambda: self.start_level(g.index + 1), "#3A8A3A"))
                buttons += [("Replay", lambda: self.start_level(g.index), "#7A5A20"),
                            ("Level Select", lambda: setattr(self, "state", "levels"), "#3A4A7A")]
                self._overlay(p, "Level Complete!" if g.index + 1 < len(G.LEVELS) else "You beat Claudeggle!", lines,
                              buttons)
            elif g.state == "lost":
                self._overlay(p, "Out of Balls!", [f"{g.oranges_left()} orange pegs left", f"Score: {g.score:,}"],
                              [("Try Again", lambda: self.start_level(g.index), "#A04020"),
                               ("Level Select", lambda: setattr(self, "state", "levels"), "#3A4A7A")])
        p.end()

    def _button(self, p, r, text, action, colour="#3A4A8A", size=13):
        hot = r.contains(self.mouse)
        c = QColor(colour)
        g = QLinearGradient(r.topLeft(), r.bottomLeft())
        g.setColorAt(0, c.lighter(170 if hot else 140))
        g.setColorAt(0.5, c)
        g.setColorAt(1, c.darker(150))
        p.setPen(QPen(QColor("#FFF0A0") if hot else QColor("#D0D8F0"), 2))
        p.setBrush(QBrush(g))
        p.drawRoundedRect(r, r.height() / 2.4, r.height() / 2.4)
        p.setFont(QFont("Comic Sans MS", size, QFont.Bold))
        p.setPen(QColor("white"))
        p.drawText(r, Qt.AlignCenter, text)
        self.buttons.append((r, action))

    def _logo(self, p, r, size):
        f = QFont("Comic Sans MS", size, QFont.Bold)
        p.setFont(f)
        p.setPen(QColor(10, 20, 60, 220))
        p.drawText(r.translated(4, 4), Qt.AlignCenter, "Claudeggle")
        g = QLinearGradient(r.topLeft(), r.bottomLeft())
        g.setColorAt(0.25, QColor("#FFF4A0"))
        g.setColorAt(0.6, QColor("#FF9A20"))
        g.setColorAt(0.9, QColor("#D04010"))
        p.setPen(QPen(QBrush(g), 1))
        p.drawText(r, Qt.AlignCenter, "Claudeggle")

    def _sky(self, p, theme=0):
        top, mid, _hi = THEMES[theme % len(THEMES)]
        g = QLinearGradient(0, 0, 0, VH)
        g.setColorAt(0, QColor(top))
        g.setColorAt(1, QColor(mid))
        p.fillRect(QRectF(0, 0, VW, VH), QBrush(g))

    def _draw_title(self, p):
        self._sky(p, 3)
        rnd = random.Random(3)
        for i in range(60):                               # a rain of pegs behind the logo
            x = rnd.uniform(0, VW)
            y = (rnd.uniform(0, VH) + self.t * (20 + i % 7 * 6)) % (VH + 40) - 20
            _peg(p, QPointF(x, y), rnd.uniform(5, 10), PEG_RGB[rnd.choice(["blue", "blue", "orange", "green", "purple"])],
                 i % 9 == 0)
        self._logo(p, QRectF(0, 90, VW, 120), 70)
        p.setFont(QFont("Comic Sans MS", 14))
        p.setPen(QColor("#E0F0FF"))
        p.drawText(QRectF(0, 205, VW, 30), Qt.AlignHCenter, "Aim. Shoot. Clear the orange pegs.")
        self._button(p, QRectF(VW / 2 - 130, 290, 260, 58), "Play!", lambda: setattr(self, "state", "levels"),
                     "#D06010", 22)
        self._button(p, QRectF(VW / 2 - 90, 370, 180, 40), "Quit",
                     lambda: self.frame.request_close() if self.frame else None, "#404A60", 13)
        done = sum(1 for i in range(len(G.LEVELS)) if i in self.progress["best"])
        p.setFont(QFont("Comic Sans MS", 11))
        p.setPen(QColor("#C0D0F0"))
        p.drawText(QRectF(0, 440, VW, 22), Qt.AlignHCenter, f"{done} of {len(G.LEVELS)} levels cleared")

    def _draw_levels(self, p):
        self._sky(p, 9)
        p.setFont(QFont("Comic Sans MS", 30, QFont.Bold))
        p.setPen(QColor("#FFD060"))
        p.drawText(QRectF(0, 20, VW, 50), Qt.AlignHCenter, "Choose a Level")
        tw, th = 200, 130
        for i, (name, _m, power) in enumerate(G.LEVELS):
            col, row = i % 4, i // 4
            r = QRectF(VW / 2 - 2 * tw - 30 + col * (tw + 20), 100 + row * (th + 22), tw, th)
            locked = i + 1 > self.progress["unlocked"]
            hot = r.contains(self.mouse) and not locked
            top, mid, hi = THEMES[i]
            g = QLinearGradient(r.topLeft(), r.bottomLeft())
            g.setColorAt(0, QColor(mid).lighter(130 if hot else 100))
            g.setColorAt(1, QColor(top))
            p.setPen(QPen(QColor("#FFF0A0") if hot else QColor(hi), 2))
            p.setBrush(QBrush(g))
            p.drawRoundedRect(r, 12, 12)
            if locked:
                p.setBrush(QColor(0, 0, 0, 150))
                p.setPen(Qt.NoPen)
                p.drawRoundedRect(r, 12, 12)
            p.setFont(QFont("Comic Sans MS", 22, QFont.Bold))
            p.setPen(QColor("white") if not locked else QColor("#707080"))
            p.drawText(QRectF(r.x(), r.y() + 8, r.width(), 36), Qt.AlignHCenter, str(i + 1))
            p.setFont(QFont("Comic Sans MS", 12, QFont.Bold))
            p.drawText(QRectF(r.x(), r.y() + 46, r.width(), 24), Qt.AlignHCenter, name if not locked else "Locked")
            p.setFont(QFont("Comic Sans MS", 9))
            if not locked:
                p.setPen(QColor("#90FF90"))
                p.drawText(QRectF(r.x(), r.y() + 72, r.width(), 18), Qt.AlignHCenter, G.POWERS[power][0])
                best = self.progress["best"].get(i)
                p.setPen(QColor("#FFE080"))
                p.drawText(QRectF(r.x(), r.y() + 96, r.width(), 20), Qt.AlignHCenter,
                           f"Best: {best:,}" if best else "Not cleared yet")
                self.buttons.append((r, lambda i=i: self.start_level(i)))
        self._button(p, QRectF(30, VH - 60, 140, 40), "Back", lambda: setattr(self, "state", "title"), "#404A60", 12)

    # the playfield ---------------------------------------------------------------------------------------------
    def _field_bg(self, index):
        if index in self.bg:
            return self.bg[index]
        top, mid, hi = THEMES[index % len(THEMES)]
        pm = QPixmap(G.W, G.H)
        q = QPainter(pm)
        q.setRenderHint(QPainter.Antialiasing)
        g = QLinearGradient(0, 0, 0, G.H)
        g.setColorAt(0, QColor(top))
        g.setColorAt(1, QColor(mid))
        q.fillRect(pm.rect(), QBrush(g))
        rnd = random.Random(index * 7 + 1)
        q.setPen(Qt.NoPen)
        for _ in range(70):
            q.setBrush(QColor(255, 255, 255, rnd.randrange(40, 160)))
            q.drawEllipse(QPointF(rnd.uniform(0, G.W), rnd.uniform(0, G.H * 0.6)), 1, 1)
        mx, my, mr = rnd.uniform(100, G.W - 100), rnd.uniform(80, 200), rnd.uniform(40, 80)
        moon = QRadialGradient(QPointF(mx, my), mr * 2.2)
        c = QColor(hi)
        c.setAlpha(110)
        moon.setColorAt(0, c)
        c.setAlpha(0)
        moon.setColorAt(1, c)
        q.setBrush(QBrush(moon))
        q.drawEllipse(QPointF(mx, my), mr * 2.2, mr * 2.2)
        c.setAlpha(170)
        q.setBrush(c)
        q.drawEllipse(QPointF(mx, my), mr, mr)
        for layer in range(3):                            # rolling hills
            path = QPainterPath(QPointF(0, G.H))
            base = G.H - 60 - layer * 40 + 60
            ph = rnd.uniform(0, 6)
            for x in range(0, G.W + 1, 10):
                path.lineTo(x, base - 30 - math.sin(x / (120 + layer * 40) + ph) * (25 + layer * 10))
            path.lineTo(G.W, G.H)
            path.closeSubpath()
            q.setBrush(QColor(top).darker(110 + (2 - layer) * 30))
            q.drawPath(path)
        q.end()
        self.bg[index] = pm
        return pm

    def _draw_play(self, p):
        g = self.game
        self._sky(p, g.index)
        p.fillRect(QRectF(0, 0, VW, VH), QColor(0, 0, 0, 90))
        # the field
        p.save()
        p.translate(FX, FY)
        p.setClipRect(QRectF(0, 0, G.W, G.H))
        p.drawPixmap(0, 0, self._field_bg(g.index))
        if g.fever and g.state in ("flying", "clearing", "won"):
            # rainbow wash and Extreme Fever's buckets
            hue = int(self.t * 120) % 360
            p.fillRect(QRectF(0, 0, G.W, G.H), QColor.fromHsv(hue, 160, 255, 40))
            sw = G.W / 5
            for i, v in enumerate(G.FEVER_SLOTS):
                r = QRectF(i * sw + 3, G.H - 34, sw - 6, 34)
                c = QColor(FEVER_RGB[i])
                if g.fever_slot == i:
                    c = c.lighter(140 + int(40 * math.sin(self.t * 12)))
                p.setPen(QPen(c.lighter(150), 2))
                p.setBrush(c)
                p.drawRoundedRect(r, 6, 6)
                p.setFont(QFont("Comic Sans MS", 12, QFont.Bold))
                p.setPen(QColor("white"))
                p.drawText(r, Qt.AlignCenter, f"{v:,}")
        # the aim guide
        if g.state == "aim" and self.state == "play":
            ang = self._angle()
            pts = g.guide(ang, bounces=3 if g.guide_shots else 1, steps=150 if g.guide_shots else 34)
            p.setPen(Qt.NoPen)
            for i, (x, y) in enumerate(pts[::2]):
                a = max(30, 230 - i * (3 if g.guide_shots else 9))
                p.setBrush(QColor(120, 255, 140, a) if g.guide_shots else QColor(255, 255, 255, a))
                p.drawEllipse(QPointF(x, y), 2.2, 2.2)
        # pegs
        for peg in g.pegs:
            if peg.gone:
                continue
            col = PEG_RGB[peg.colour]
            if peg.brick:
                base = QColor(col).lighter(150 if peg.lit else 100)
                if peg.lit:
                    p.setPen(QPen(QColor(base.red(), base.green(), base.blue(), 90), 20, Qt.SolidLine, Qt.RoundCap))
                    p.drawLine(QPointF(peg.x, peg.y), QPointF(peg.x2, peg.y2))
                p.setPen(QPen(base.darker(200), 13, Qt.SolidLine, Qt.RoundCap))
                p.drawLine(QPointF(peg.x, peg.y), QPointF(peg.x2, peg.y2))
                p.setPen(QPen(base, 10, Qt.SolidLine, Qt.RoundCap))
                p.drawLine(QPointF(peg.x, peg.y), QPointF(peg.x2, peg.y2))
                p.setPen(QPen(base.lighter(160), 3, Qt.SolidLine, Qt.RoundCap))
                p.drawLine(QPointF(peg.x, peg.y - 2), QPointF(peg.x2, peg.y2 - 2))
            else:
                _peg(p, QPointF(peg.x, peg.y), G.PEG_R, col, peg.lit)
        # the bucket
        if not g.fever:
            bx, by = g.bucket_x, G.BUCKET_Y
            path = QPainterPath(QPointF(bx - G.BUCKET_HALF, by))
            path.lineTo(bx + G.BUCKET_HALF, by)
            path.lineTo(bx + G.BUCKET_HALF - 10, by + 24)
            path.lineTo(bx - G.BUCKET_HALF + 10, by + 24)
            path.closeSubpath()
            bg = QLinearGradient(bx - G.BUCKET_HALF, 0, bx + G.BUCKET_HALF, 0)
            bg.setColorAt(0, QColor("#6A7080"))
            bg.setColorAt(0.4, QColor("#E0E4F0"))
            bg.setColorAt(1, QColor("#5A6070"))
            p.setPen(QPen(QColor("#303040"), 1.5))
            p.setBrush(QBrush(bg))
            p.drawPath(path)
            for ex in (-G.BUCKET_HALF, G.BUCKET_HALF):
                p.setBrush(QColor("#C0C8D8"))
                p.drawEllipse(QPointF(bx + ex, by), 5, 5)
        # the launcher
        ang = self._angle() if g.state == "aim" else getattr(self, "_last_angle", math.pi / 2)
        self._last_angle = ang
        lx, ly = G.LAUNCH
        p.save()
        p.translate(lx, ly)
        p.rotate(math.degrees(ang) - 90)
        p.setPen(QPen(QColor("#202838"), 1.5))
        bar = QLinearGradient(-9, 0, 9, 0)
        bar.setColorAt(0, QColor("#5A6478"))
        bar.setColorAt(0.5, QColor("#D8E0F0"))
        bar.setColorAt(1, QColor("#4A5468"))
        p.setBrush(QBrush(bar))
        p.drawRoundedRect(QRectF(-9, 0, 18, 34), 4, 4)
        if g.state == "aim" and g.balls_left > 0:
            _ball(p, QPointF(0, 30), G.BALL_R)
        p.restore()
        dome = QRadialGradient(QPointF(lx - 6, ly - 8), 26)
        dome.setColorAt(0, QColor("#FFE8A0"))
        dome.setColorAt(1, QColor("#A06010"))
        p.setPen(QPen(QColor("#402000"), 1.5))
        p.setBrush(QBrush(dome))
        p.drawChord(QRectF(lx - 26, ly - 26, 52, 52), 0, 360 * 16)
        # balls
        for b in g.balls:
            for i, (x, y) in enumerate(b.trail):
                a = int(140 * i / max(1, len(b.trail)))
                p.setPen(Qt.NoPen)
                p.setBrush(QColor(255, 160, 40, a) if b.fire else QColor(255, 255, 255, a // 2))
                p.drawEllipse(QPointF(x, y), G.BALL_R * 0.6 * i / max(1, len(b.trail)), G.BALL_R * 0.6 * i / max(1, len(b.trail)))
            _ball(p, QPointF(b.x, b.y), G.BALL_R, b.fire, b.spooky)
        # particles and points
        p.setPen(Qt.NoPen)
        for x, y, _vx, _vy, life, col, sz in self.particles:
            c = QColor(col)
            c.setAlpha(int(255 * min(1.0, life * 2)))
            p.setBrush(c)
            p.drawEllipse(QPointF(x, y), sz, sz)
        for x, y, text, age, col, size in self.popups:
            p.setFont(QFont("Comic Sans MS", size, QFont.Bold))
            a = int(255 * max(0.0, 1 - age / 1.2))
            r = QRectF(x - 100, y - 20 - age * 30, 200, 24)
            p.setPen(QColor(0, 0, 0, a // 2))
            p.drawText(r.translated(1.5, 1.5), Qt.AlignCenter, text)
            c = QColor(col).lighter(130)
            c.setAlpha(a)
            p.setPen(c)
            p.drawText(r, Qt.AlignCenter, text)
        if g.state == "clearing" and g.shot_score:
            p.setFont(QFont("Comic Sans MS", 18, QFont.Bold))
            p.setPen(QColor("#FFF0A0"))
            p.drawText(QRectF(0, 70, G.W, 30), Qt.AlignHCenter, f"Shot: {g.shot_score:,}")
        p.restore()
        # frame around the field
        p.setPen(QPen(QColor("#C8A060"), 4))
        p.setBrush(Qt.NoBrush)
        p.drawRoundedRect(QRectF(FX - 3, FY - 3, G.W + 6, G.H + 6), 6, 6)
        self._draw_side(p)
        self._draw_banner(p)

    def _draw_side(self, p):
        g = self.game
        # top: level name and score
        p.setFont(QFont("Comic Sans MS", 13, QFont.Bold))
        p.setPen(QColor("#FFE6A0"))
        p.drawText(QRectF(FX, 4, 400, 26), Qt.AlignLeft | Qt.AlignVCenter,
                   f"{g.index + 1}. {g.name}  -  {G.POWERS[g.power][0]}" + (f" ({g.guide_shots})" if g.guide_shots else ""))
        p.setFont(QFont("Comic Sans MS", 16, QFont.Bold))
        p.setPen(QColor("white"))
        p.drawText(QRectF(FX + G.W - 300, 2, 300, 28), Qt.AlignRight | Qt.AlignVCenter, f"{g.score:,}")
        # left: the ball tube
        tube = QRectF(32, FY + 40, 46, G.H - 80)
        p.setPen(QPen(QColor("#A0B0D0"), 2))
        tg = QLinearGradient(tube.topLeft(), tube.topRight())
        tg.setColorAt(0, QColor(40, 60, 100, 200))
        tg.setColorAt(0.5, QColor(120, 150, 210, 120))
        tg.setColorAt(1, QColor(30, 40, 80, 200))
        p.setBrush(QBrush(tg))
        p.drawRoundedRect(tube, 22, 22)
        shown = min(g.balls_left, 14)
        for i in range(shown):
            _ball(p, QPointF(tube.center().x(), tube.bottom() - 26 - i * 34), 13)
        p.setFont(QFont("Comic Sans MS", 22, QFont.Bold))
        p.setPen(QColor("white"))
        p.drawText(QRectF(0, FY, FX, 36), Qt.AlignCenter, str(g.balls_left))
        p.setFont(QFont("Comic Sans MS", 9))
        p.drawText(QRectF(0, tube.bottom() + 4, FX, 20), Qt.AlignCenter, "balls")
        # right: the orange meter and the multiplier
        rx = FX + G.W + 24
        meter = QRectF(rx + 10, FY + 70, 34, G.H - 120)
        p.setPen(QPen(QColor("#D0A060"), 2))
        p.setBrush(QColor(20, 10, 0, 180))
        p.drawRoundedRect(meter, 8, 8)
        total = g.total_oranges
        hit = total - g.oranges_left()
        seg = (meter.height() - 8) / total
        for i in range(total):
            r = QRectF(meter.x() + 4, meter.bottom() - 4 - (i + 1) * seg + 1, meter.width() - 8, seg - 2)
            p.setPen(Qt.NoPen)
            p.setBrush(QColor("#FF9A20") if i < hit else QColor(80, 40, 10, 160))
            p.drawRoundedRect(r, 2, 2)
        p.setFont(QFont("Comic Sans MS", 8, QFont.Bold))
        for frac, label in ((0.4, "x2"), (0.6, "x3"), (0.76, "x5"), (0.88, "x10")):
            y = meter.bottom() - 4 - frac * (meter.height() - 8)
            p.setPen(QPen(QColor("#FFF0C0"), 1))
            p.drawLine(QPointF(meter.x() - 4, y), QPointF(meter.x(), y))
            p.drawText(QRectF(meter.right() + 2, y - 8, 30, 16), Qt.AlignLeft | Qt.AlignVCenter, label)
        p.setFont(QFont("Comic Sans MS", 22, QFont.Bold))
        p.setPen(QColor("#FFB040"))
        p.drawText(QRectF(FX + G.W + 6, FY, VW - FX - G.W - 6, 36), Qt.AlignCenter, f"x{g.multiplier()}")
        p.setFont(QFont("Comic Sans MS", 9))
        p.setPen(QColor("white"))
        p.drawText(QRectF(FX + G.W + 6, meter.bottom() + 4, VW - FX - G.W - 6, 34), Qt.AlignHCenter | Qt.TextWordWrap,
                   f"{g.oranges_left()} orange left")
        if self.state == "play":
            self._button(p, QRectF(18, VH - 44, 76, 30), "Menu", lambda: setattr(self, "state", "paused"), "#404A60", 10)

    def _draw_banner(self, p):
        if not self.banner:
            return
        text, age, col = self.banner[:3]
        life = 4.0 if len(self.banner) > 3 else 2.0
        a = int(255 * max(0.0, min(1.0, (life - age) / 0.5)))
        k = min(1.0, age / 0.18)
        big = text == "EXTREME FEVER!"
        f = QFont("Comic Sans MS", int((44 if big else 30) * (0.5 + 0.5 * k)), QFont.Bold)
        p.setFont(f)
        r = QRectF(FX, FY + G.H * 0.36, G.W, 70)
        p.setPen(QColor(0, 0, 0, int(a * 0.7)))
        p.drawText(r.translated(3, 3), Qt.AlignCenter, text)
        c = QColor.fromHsv(int(self.t * 300) % 360, 120, 255, a) if big else QColor(col)
        c.setAlpha(a)
        p.setPen(c)
        p.drawText(r, Qt.AlignCenter, text)
        if len(self.banner) > 3:
            p.setFont(QFont("Comic Sans MS", 13, QFont.Bold))
            r2 = QRectF(FX + 40, r.bottom(), G.W - 80, 50)
            p.setPen(QColor(0, 0, 0, int(a * 0.7)))
            p.drawText(r2.translated(2, 2), Qt.AlignHCenter | Qt.TextWordWrap, self.banner[3])
            p.setPen(QColor(150, 255, 160, a))
            p.drawText(r2, Qt.AlignHCenter | Qt.TextWordWrap, self.banner[3])

    def _overlay(self, p, title, lines, buttons):
        r = QRectF(FX + G.W / 2 - 200, FY + G.H / 2 - 160, 400, 320)
        p.setPen(QPen(QColor("#E0B060"), 3))
        g = QLinearGradient(r.topLeft(), r.bottomLeft())
        g.setColorAt(0, QColor(30, 40, 90, 240))
        g.setColorAt(1, QColor(10, 15, 40, 240))
        p.setBrush(QBrush(g))
        p.drawRoundedRect(r, 18, 18)
        p.setFont(QFont("Comic Sans MS", 24, QFont.Bold))
        p.setPen(QColor("#FFD060"))
        p.drawText(QRectF(r.x(), r.y() + 14, r.width(), 40), Qt.AlignHCenter, title)
        p.setFont(QFont("Comic Sans MS", 12))
        p.setPen(QColor("white"))
        for i, line in enumerate(lines):
            p.drawText(QRectF(r.x(), r.y() + 66 + i * 24, r.width(), 22), Qt.AlignHCenter, line)
        y = r.bottom() - 18 - 44 * len(buttons)
        for text, action, colour in buttons:
            self._button(p, QRectF(r.x() + 90, y, r.width() - 180, 36), text, action, colour, 13)
            y += 44

    def shutdown(self):
        self.timer.stop()


_open = {}


def launch(desktop):
    win = _open.get("win")
    if win is not None and isValid(win):
        desktop.open_window(win)
        return win
    body = Peggle(desktop)
    win = XPWindow(desktop, "Claudeggle", body, peggle_icon(), size=(VW + 10, VH + 36))
    body.frame = win
    _open["win"] = win
    desktop.open_window(win)
    body.setFocus()
    return win


def shutdown():
    win = _open.get("win")
    if win is not None and isValid(win):
        win.content.shutdown()
