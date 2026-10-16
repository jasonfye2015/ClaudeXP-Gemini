"""Scorched Claude - an artillery game in the spirit of Scorched Earth ("The Mother of All Games").

2 to 10 tanks, people or computer players, take turns lobbing shells over a mountain range that blows apart and
caves in. Between rounds, spend your winnings in the shop on nukes, MIRVs, Death's Heads, napalm, rollers, dirt
bombs, shields, parachutes, batteries and fuel.

Keys in battle: Left/Right angle (Shift for big steps), Up/Down power (Page Up/Down for big steps), Tab / W next
weapon, Space or Enter fire, A/D drive (needs Fuel), 1 shield, 2 battery.
"""
import math
import random
import time

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import (QBrush, QColor, QFont, QFontMetrics, QIcon, QLinearGradient, QPainter, QPainterPath, QPen,
                           QPixmap, QPolygonF, QRadialGradient)
from PySide6.QtWidgets import QWidget
from shiboken6 import isValid

from ... import sound
from ...wm import XPWindow
from . import game as G

HUD_H = 64
SKIES = {"night": ("#000010", "#101040"), "dusk": ("#100830", "#C05030"), "day": ("#2060D0", "#A0D0F0"),
         "storm": ("#202028", "#606070"), "sunset": ("#301050", "#F0A040")}
LANDS = {"classic": ("#4A9A2A", "#2A5A1A", "#6A4A20"), "desert": ("#E0B060", "#B07A30", "#7A4A20"),
         "snow": ("#F0F4FA", "#A0B0C8", "#6A6A7A"), "lava": ("#5A2A1A", "#2A0A06", "#E04010"),
         "grass": ("#7AC040", "#3A7A20", "#4A3A20")}


def tank_pixmap(colour, size=32):
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.scale(size / 32, size / 32)
    p.translate(16, 22)
    _tank(p, colour, 60, 1.4)
    p.end()
    return pm


def scorched_icon():
    ic = QIcon()
    for sz in (16, 32, 48):
        pm = QPixmap(sz, sz)
        pm.fill(Qt.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.Antialiasing)
        s = sz / 32
        g = QLinearGradient(0, 0, 0, sz)
        g.setColorAt(0, QColor("#100830"))
        g.setColorAt(1, QColor("#C05030"))
        p.setPen(QPen(QColor("#300810"), max(1.0, s)))
        p.setBrush(QBrush(g))
        p.drawRoundedRect(QRectF(1 * s, 1 * s, 30 * s, 30 * s), 4 * s, 4 * s)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#3A7A20"))
        p.drawPolygon(QPolygonF([QPointF(1 * s, 26 * s), QPointF(10 * s, 18 * s), QPointF(18 * s, 23 * s),
                                 QPointF(31 * s, 15 * s), QPointF(31 * s, 31 * s), QPointF(1 * s, 31 * s)]))
        fl = QRadialGradient(QPointF(22 * s, 10 * s), 8 * s)
        fl.setColorAt(0, QColor("#FFF0A0"))
        fl.setColorAt(1, QColor(255, 120, 20, 0))
        p.setBrush(QBrush(fl))
        p.drawEllipse(QPointF(22 * s, 10 * s), 8 * s, 8 * s)
        p.translate(9 * s, 21 * s)
        p.scale(s * 0.9, s * 0.9)
        _tank(p, "#E03030", 50, 1.0)
        p.end()
        ic.addPixmap(pm)
    return ic


def _tank(p, colour, angle, scale=1.0):
    """A tank sitting on (0, 0): tracks, a dome and the gun at angle (degrees, 0 = right)."""
    c = QColor(colour)
    p.save()
    p.scale(scale, scale)
    a = math.radians(angle)
    p.setPen(QPen(c.lighter(140), 2.4, Qt.SolidLine, Qt.RoundCap))
    p.drawLine(QPointF(0, -7), QPointF(math.cos(a) * 13, -7 - math.sin(a) * 13))
    p.setPen(QPen(QColor(0, 0, 0, 160), 1))
    p.setBrush(c)
    p.drawChord(QRectF(-6, -12, 12, 11), 0, 180 * 16)
    p.setBrush(c.darker(130))
    p.drawRoundedRect(QRectF(-10, -6, 20, 5), 2, 2)
    p.setBrush(QColor("#303030"))
    p.drawRoundedRect(QRectF(-9, -2, 18, 3), 1.5, 1.5)
    p.restore()


class Scorched(QWidget):
    def __init__(self, desktop):
        super().__init__()
        self.desktop = desktop
        self.frame = None
        self.state = "title"
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMinimumSize(G.W, G.H + HUD_H)
        self.mouse = QPointF(-1, -1)
        self.buttons = []
        # setup
        self.slots = [["Human", 0], ["Cyborg", 1], ["Poolshark", 2], ["Shooter", 3]]
        self.rounds = 5
        self.wind_max = 10
        # game
        self.tanks = []
        self.round = 0
        self.battle = None
        self.shop_queue = []
        self.shopper = None
        self.land_pm = None
        self.ai_wait = 0.0
        self.round_winner = None
        self.keys = set()
        self.stars = [(random.random(), random.random() * 0.7, random.random()) for _ in range(120)]
        self.last = time.monotonic()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(16)

    # ---- loop -----------------------------------------------------------------------------------------------
    def _tick(self):
        now = time.monotonic()
        dt = min(0.04, now - self.last)
        self.last = now
        b = self.battle
        if self.state == "battle" and b is not None:
            b.step(dt)
            t = b.current
            if not b.busy and not b.over():
                if t.ai:
                    self.ai_wait -= dt
                    if self.ai_wait <= 0:
                        b.ai_aim(t)
                        b.fire(t)
                        self.ai_wait = 1.0
                else:
                    self._held_keys(t, dt)
            if b.over() and not b.busy and not b.shots and not b.blasts:
                self._end_round()
        self.update()

    def _held_keys(self, t, dt):
        k = self.keys
        big = Qt.Key_Shift in k
        if Qt.Key_Left in k:
            t.angle = min(180.0, t.angle + (60 if big else 18) * dt)
        if Qt.Key_Right in k:
            t.angle = max(0.0, t.angle - (60 if big else 18) * dt)
        if Qt.Key_Up in k:
            t.power = min(t.max_power, t.power + (400 if big else 120) * dt)
        if Qt.Key_Down in k:
            t.power = max(0.0, t.power - (400 if big else 120) * dt)
        if Qt.Key_A in k:
            self.battle.drive(t, -1, dt)
        if Qt.Key_D in k:
            self.battle.drive(t, 1, dt)

    # ---- input ---------------------------------------------------------------------------------------------
    def keyPressEvent(self, e):
        k = e.key()
        self.keys.add(k)
        if self.state != "battle" or self.battle is None:
            if self.state in ("round_over", "title") and k in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space):
                self._advance()
            return
        b = self.battle
        t = b.current
        if t.ai or b.busy:
            return
        if k in (Qt.Key_Space, Qt.Key_Return, Qt.Key_Enter):
            self._fire()
        elif k in (Qt.Key_Tab, Qt.Key_W):
            self._cycle_weapon(1)
        elif k == Qt.Key_Q:
            self._cycle_weapon(-1)
        elif k == Qt.Key_PageUp:
            t.power = min(t.max_power, t.power + 100)
        elif k == Qt.Key_PageDown:
            t.power = max(0.0, t.power - 100)
        elif k == Qt.Key_1:
            b.use_item(t, "Heavy Shield") or b.use_item(t, "Shield")
        elif k == Qt.Key_2:
            b.use_item(t, "Battery")

    def keyReleaseEvent(self, e):
        self.keys.discard(e.key())

    def focusOutEvent(self, e):
        self.keys.clear()
        super().focusOutEvent(e)

    def mouseMoveEvent(self, e):
        self.mouse = e.position()

    def mousePressEvent(self, e):
        self.setFocus()
        for rect, action in reversed(self.buttons):
            if rect.contains(e.position()):
                sound.play("menu")
                action()
                return

    def _fire(self):
        b = self.battle
        t = b.current
        if t.power > t.max_power:
            t.power = t.max_power
        b.fire(t)

    def _cycle_weapon(self, d):
        t = self.battle.current
        owned = t.owned()
        if not owned:
            return
        i = owned.index(t.weapon) if t.weapon in owned else 0
        t.weapon = owned[(i + d) % len(owned)]

    # ---- the flow of a game -----------------------------------------------------------------------------------
    def _advance(self):
        if self.state == "title":
            self.state = "setup"
        elif self.state == "round_over":
            if self.round >= self.rounds:
                self.state = "game_over"
            else:
                self._start_shopping()

    def _start_game(self):
        ai_names = {}
        self.tanks = []
        humans = 0
        for kind, colour in self.slots:
            if kind == "Human":
                humans += 1
                name = f"Player {humans}"
                ai = None
            else:
                ai_names[kind] = ai_names.get(kind, 0) + 1
                name = kind if ai_names[kind] == 1 else f"{kind} {ai_names[kind]}"
                ai = kind
            self.tanks.append(G.Tank(name, G.COLOURS[colour % len(G.COLOURS)], ai))
        self.round = 0
        self._start_shopping()

    def _start_shopping(self):
        self.round += 1
        rnd = random.Random()
        for t in self.tanks:
            if t.ai:
                G.ai_shop(t, rnd)
        self.shop_queue = [t for t in self.tanks if not t.ai]
        self._next_shopper()

    def _next_shopper(self):
        if self.shop_queue:
            self.shopper = self.shop_queue.pop(0)
            self.state = "shop"
        else:
            self._start_battle()

    def _start_battle(self):
        for t in self.tanks:
            t.reset()                              # full health, keeping cash and inventory
        self.battle = G.Battle(self.tanks, wind_max=self.wind_max)
        self.land_pm = None
        self.ai_wait = 1.2
        self.state = "battle"
        self.setFocus()

    def _end_round(self):
        b = self.battle
        winner = b.alive()[0] if b.alive() else None
        if winner:
            winner.cash += 3000
            winner.score += 1
        for t in self.tanks:
            t.cash += 1000                          # everyone's pay for showing up
        self.round_winner = winner
        self.state = "round_over"

    def _buy(self, name):
        t = self.shopper
        if name in G.WEAPONS:
            price, qty = G.WEAPONS[name][0], G.WEAPONS[name][1]
        else:
            price, qty = G.ITEMS[name][0], G.ITEMS[name][1]
        if t.cash >= price:
            t.cash -= price
            t.inventory[name] = t.inventory.get(name, 0) + qty
        else:
            sound.play("default")

    # ---- painting --------------------------------------------------------------------------------------------
    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        self.buttons = []
        if self.state == "battle" and self.battle is not None:
            self._draw_battle(p)
        elif self.state == "setup":
            self._draw_setup(p)
        elif self.state == "shop":
            self._draw_shop(p)
        elif self.state == "round_over":
            self._draw_battle(p)
            self._draw_round_over(p)
        elif self.state == "game_over":
            self._draw_game_over(p)
        else:
            self._draw_title(p)
        p.end()

    def _button(self, p, r, text, action, colour="#3A3A8A", small=False):
        hot = r.contains(self.mouse)
        p.setPen(QPen(QColor("#E8E8F0"), 1.5))
        g = QLinearGradient(r.topLeft(), r.bottomLeft())
        c = QColor(colour)
        g.setColorAt(0, c.lighter(150 if hot else 125))
        g.setColorAt(1, c.darker(110))
        p.setBrush(QBrush(g))
        p.drawRoundedRect(r, 5, 5)
        p.setFont(QFont("Arial", 9 if small else 12, QFont.Bold))
        p.setPen(QColor("white"))
        p.drawText(r, Qt.AlignCenter, text)
        self.buttons.append((r, action))

    def _backdrop(self, p, sky="dusk"):
        top, bottom = SKIES[sky]
        g = QLinearGradient(0, 0, 0, self.height())
        g.setColorAt(0, QColor(top))
        g.setColorAt(1, QColor(bottom))
        p.fillRect(self.rect(), QBrush(g))
        if sky in ("night", "dusk", "sunset"):
            t = time.monotonic()
            p.setPen(Qt.NoPen)
            for x, y, s in self.stars:
                a = int(120 + 120 * math.sin(t * (1 + s) + s * 10))
                p.setBrush(QColor(255, 255, 255, max(30, a)))
                p.drawEllipse(QPointF(x * self.width(), y * self.height()), 0.8 + s, 0.8 + s)

    def _draw_title(self, p):
        self._backdrop(p, "dusk")
        w, h = self.width(), self.height()
        path = QPainterPath(QPointF(0, h))
        for i in range(0, 41):
            x = i / 40 * w
            path.lineTo(x, h * 0.7 - math.sin(i * 0.5) * 40 - math.sin(i * 1.3) * 25)
        path.lineTo(w, h)
        path.closeSubpath()
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#2A5A1A"))
        p.drawPath(path)
        f = QFont("Impact", 54)
        f.setItalic(True)
        p.setFont(f)
        for dx, dy, col in ((4, 4, "#200000"), (0, 0, None)):
            r = QRectF(dx, h * 0.12 + dy, w, 80)
            if col:
                p.setPen(QColor(col))
            else:
                g = QLinearGradient(0, h * 0.12, 0, h * 0.12 + 70)
                g.setColorAt(0, QColor("#FFF0A0"))
                g.setColorAt(0.5, QColor("#F08020"))
                g.setColorAt(1, QColor("#C02010"))
                p.setPen(QPen(QBrush(g), 1))
            p.drawText(r, Qt.AlignHCenter, "SCORCHED CLAUDE")
        p.setFont(QFont("Arial", 13, QFont.Bold))
        p.setPen(QColor("#F0D0A0"))
        p.drawText(QRectF(0, h * 0.12 + 86, w, 24), Qt.AlignHCenter, "The Mother of All Games... for ClaudeXP")
        t = time.monotonic()
        for i, (x, col) in enumerate(((0.25, "#E03030"), (0.72, "#3060F0"))):
            p.save()
            p.translate(w * x, h * 0.7 - 8 - math.sin((x * 40) * 0.5) * 40)
            _tank(p, col, 50 if i == 0 else 130, 2.0)
            p.restore()
        # a shell arcing between them
        ph = (t * 0.4) % 1.0
        sx = w * 0.25 + (w * 0.47) * ph
        sy = h * 0.6 - math.sin(ph * math.pi) * h * 0.35
        g = QRadialGradient(QPointF(sx, sy), 8)
        g.setColorAt(0, QColor("#FFFFFF"))
        g.setColorAt(1, QColor(255, 160, 40, 0))
        p.setBrush(QBrush(g))
        p.drawEllipse(QPointF(sx, sy), 8, 8)
        self._button(p, QRectF(w / 2 - 110, h * 0.47, 220, 46), "Start", self._advance, "#8A2A1A")
        self._button(p, QRectF(w / 2 - 110, h * 0.47 + 56, 220, 40), "Quit",
                     lambda: self.frame.request_close() if self.frame else None, "#3A3A4A")

    def _draw_setup(self, p):
        self._backdrop(p, "night")
        w, h = self.width(), self.height()
        p.setFont(QFont("Impact", 30))
        p.setPen(QColor("#F0A040"))
        p.drawText(QRectF(0, 18, w, 44), Qt.AlignHCenter, "Players")
        y = 78
        kinds = ["Human"] + list(G.AI_TYPES)
        for i, (kind, colour) in enumerate(self.slots):
            r = QRectF(w / 2 - 260, y, 520, 34)
            p.setPen(QPen(QColor("#5A5A8A"), 1))
            p.setBrush(QColor(20, 20, 50, 200))
            p.drawRoundedRect(r, 5, 5)
            p.drawPixmap(QPointF(r.x() + 8, r.y() + 2), tank_pixmap(G.COLOURS[colour % len(G.COLOURS)], 30))
            self.buttons.append((QRectF(r.x() + 4, r.y(), 40, 34),
                                 lambda i=i: self.slots[i].__setitem__(1, (self.slots[i][1] + 1) % len(G.COLOURS))))
            p.setFont(QFont("Arial", 11, QFont.Bold))
            p.setPen(QColor("white"))
            p.drawText(QRectF(r.x() + 52, r.y(), 120, 34), Qt.AlignVCenter, f"Tank {i + 1}")
            self._button(p, QRectF(r.x() + 170, r.y() + 4, 190, 26), kind,
                         lambda i=i: self.slots[i].__setitem__(0, kinds[(kinds.index(self.slots[i][0]) + 1) % len(kinds)]),
                         "#2A5A9A" if kind == "Human" else "#6A3A8A", small=True)
            if len(self.slots) > 2:
                self._button(p, QRectF(r.right() - 70, r.y() + 4, 62, 26), "Remove",
                             lambda i=i: self.slots.pop(i), "#7A2A2A", small=True)
            y += 40
        if len(self.slots) < 10:
            self._button(p, QRectF(w / 2 - 260, y, 160, 30), "+ Add Tank",
                         lambda: self.slots.append(["Shooter", len(self.slots)]), "#2A6A3A", small=True)
        y = max(y + 44, h - 150)
        p.setFont(QFont("Arial", 11, QFont.Bold))
        p.setPen(QColor("white"))
        p.drawText(QRectF(w / 2 - 260, y, 120, 30), Qt.AlignVCenter, "Rounds:")
        for i, n in enumerate((3, 5, 10, 20)):
            self._button(p, QRectF(w / 2 - 150 + i * 70, y, 60, 30), str(n), lambda n=n: setattr(self, "rounds", n),
                         "#C06020" if self.rounds == n else "#3A3A6A", small=True)
        p.drawText(QRectF(w / 2 - 260, y + 40, 120, 30), Qt.AlignVCenter, "Wind:")
        for i, (label, v) in enumerate((("None", 0), ("Breezy", 5), ("Windy", 10), ("Gale", 20))):
            self._button(p, QRectF(w / 2 - 150 + i * 70, y + 40, 60, 30), label,
                         lambda v=v: setattr(self, "wind_max", v), "#C06020" if self.wind_max == v else "#3A3A6A",
                         small=True)
        self._button(p, QRectF(w / 2 + 150, y + 10, 120, 56), "Begin!", self._start_game, "#8A2A1A")

    def _draw_shop(self, p):
        self._backdrop(p, "storm")
        t = self.shopper
        w, h = self.width(), self.height()
        p.setFont(QFont("Impact", 24))
        p.setPen(QColor(t.colour))
        p.drawText(QRectF(20, 10, w - 40, 36), Qt.AlignLeft, f"{t.name}'s Shopping Spree")
        p.setFont(QFont("Arial", 13, QFont.Bold))
        p.setPen(QColor("#F8D040"))
        p.drawText(QRectF(20, 10, w - 40, 36), Qt.AlignRight | Qt.AlignVCenter,
                   f"Cash: ${t.cash:,}    Round {self.round} of {self.rounds}")
        rows = [(n, v[0], v[1], v[4]) for n, v in G.WEAPONS.items() if n != "Baby Missile"] + \
               [(n, v[0], v[1], v[2]) for n, v in G.ITEMS.items()]
        rows.insert(0, ("Baby Missile", 0, 0, "Unlimited - always in stock."))
        col_w = (w - 50) / 2
        for i, (name, price, qty, desc) in enumerate(rows):
            col, row = i // 11, i % 11
            r = QRectF(20 + col * (col_w + 10), 56 + row * 38, col_w, 34)
            hot = r.contains(self.mouse)
            can = price and t.cash >= price
            p.setPen(QPen(QColor("#6A6A9A"), 1))
            p.setBrush(QColor(60, 60, 110, 220) if hot and can else QColor(20, 20, 40, 210))
            p.drawRoundedRect(r, 4, 4)
            p.setFont(QFont("Arial", 10, QFont.Bold))
            p.setPen(QColor("white") if can or not price else QColor("#8080A0"))
            p.drawText(QRectF(r.x() + 8, r.y() + 1, 170, 18), Qt.AlignLeft, name)
            p.setFont(QFont("Arial", 8))
            p.setPen(QColor("#B0B0D0"))
            p.drawText(QRectF(r.x() + 8, r.y() + 17, col_w - 160, 16), Qt.AlignLeft,
                       QFontMetrics(p.font()).elidedText(desc, Qt.ElideRight, int(col_w - 170)))
            if price:
                p.setFont(QFont("Arial", 9, QFont.Bold))
                p.setPen(QColor("#F8D040") if can else QColor("#806040"))
                p.drawText(QRectF(r.right() - 150, r.y() + 2, 80, 16), Qt.AlignRight, f"${price:,}")
                p.setPen(QColor("#A0A0C0"))
                p.drawText(QRectF(r.right() - 150, r.y() + 18, 80, 16), Qt.AlignRight, f"x{qty}")
            have = t.inventory.get(name, 0)
            p.setFont(QFont("Arial", 9, QFont.Bold))
            p.setPen(QColor("#80F080"))
            p.drawText(QRectF(r.right() - 64, r.y(), 56, 34), Qt.AlignRight | Qt.AlignVCenter,
                       "inf" if name == "Baby Missile" else str(have))
            if price:
                self.buttons.append((r, lambda name=name: self._buy(name)))
        self._button(p, QRectF(w - 200, h - 56, 180, 42), "Done - To Battle!", self._next_shopper, "#8A2A1A")
        p.setFont(QFont("Arial", 9))
        p.setPen(QColor("#C0C0E0"))
        p.drawText(QRectF(20, h - 52, w - 240, 40), Qt.TextWordWrap,
                   "Click an item to buy it. Green numbers are what you already own. In battle: Tab picks a "
                   "weapon, 1 raises a shield, 2 uses a battery, A/D drive with fuel. Parachutes open by themselves.")

    # the battlefield -------------------------------------------------------------------------------------------
    def _render_land(self):
        b = self.battle
        pm = QPixmap(G.W, G.H)
        pm.fill(Qt.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.Antialiasing)
        top, mid, deep = LANDS[b.palette]
        path = QPainterPath(QPointF(0, G.H))
        for x in range(0, G.W + 1):
            path.lineTo(x, G.H - b.height[x])
        path.lineTo(G.W, G.H)
        path.closeSubpath()
        g = QLinearGradient(0, G.H - 400, 0, G.H)
        g.setColorAt(0, QColor(top))
        g.setColorAt(0.45, QColor(mid))
        g.setColorAt(1, QColor(deep))
        p.setPen(QPen(QColor(top).lighter(130), 1.5))
        p.setBrush(QBrush(g))
        p.drawPath(path)
        p.end()
        self.land_pm = pm
        b.dirty = False

    def _view(self):
        """Where the battlefield sits: scaled to fit below the HUD, centred, standing on the bottom edge."""
        w, h = self.width(), self.height() - HUD_H
        sc = max(0.2, min(w / G.W, h / G.H))
        return (w - G.W * sc) / 2, HUD_H + h - G.H * sc, sc

    def _draw_battle(self, p):
        b = self.battle
        ox, oy, sc = self._view()
        top, bottom = SKIES[b.sky]
        g = QLinearGradient(0, HUD_H, 0, self.height())
        g.setColorAt(0, QColor(top))
        g.setColorAt(1, QColor(bottom))
        p.fillRect(QRectF(0, HUD_H, self.width(), self.height() - HUD_H), QBrush(g))
        if b.sky in ("night", "dusk", "sunset"):
            p.setPen(Qt.NoPen)
            for x, y, s in self.stars:
                p.setBrush(QColor(255, 255, 255, int(100 + 100 * s)))
                p.drawEllipse(QPointF(x * self.width(), HUD_H + y * (self.height() - HUD_H) * 0.6),
                              0.6 + s * 0.8, 0.6 + s * 0.8)
        if self.land_pm is None or b.dirty:
            self._render_land()
        if ox > 0.5:                                       # the hills carry on past the edges of the field
            top, mid, low = LANDS[b.palette]
            deep = QLinearGradient(0, oy + (G.H - 400) * sc, 0, oy + G.H * sc)
            deep.setColorAt(0, QColor(top))
            deep.setColorAt(0.45, QColor(mid))
            deep.setColorAt(1, QColor(low))
            deep = QBrush(deep)
            p.fillRect(QRectF(0, oy + (G.H - b.height[0]) * sc, ox + 1, b.height[0] * sc), deep)
            p.fillRect(QRectF(ox + G.W * sc - 1, oy + (G.H - b.height[G.W]) * sc, ox + 1, b.height[G.W] * sc), deep)
        p.save()
        p.translate(ox, oy)
        p.scale(sc, sc)
        p.drawPixmap(0, 0, self.land_pm)
        now = time.monotonic()
        # napalm
        for x, y, life, _o in b.flames:
            fl = math.sin(now * 20 + x) * 2
            for col, sc in (("#E03010", 1.0), ("#F8A020", 0.65), ("#FFF080", 0.3)):
                p.setPen(Qt.NoPen)
                p.setBrush(QColor(col))
                hgt = (10 + fl) * sc * min(1.0, life)
                p.drawEllipse(QPointF(x, y - hgt / 2), 3.5 * sc + 1, hgt / 2 + 1)
        # tanks
        for t in self.tanks:
            if not t.alive:
                continue
            p.save()
            p.translate(t.x, t.y)
            if t.falling and getattr(t, "parachute", False):
                p.setPen(QPen(QColor("#E0E0E0"), 1))
                p.setBrush(QColor("#E05050"))
                p.drawChord(QRectF(-14, -40, 28, 20), 0, 180 * 16)
                p.drawLine(QPointF(-14, -30), QPointF(-5, -8))
                p.drawLine(QPointF(14, -30), QPointF(5, -8))
            _tank(p, t.colour, t.angle)
            if t.shield > 0:
                a = int(60 + 60 * min(1.0, t.shield / 100))
                p.setPen(QPen(QColor(120, 200, 255, a + 60), 1.5))
                p.setBrush(QColor(120, 200, 255, a // 2))
                p.drawEllipse(QPointF(0, -5), 16, 14)
            if t is b.current and not b.busy and self.state == "battle":
                bob = math.sin(now * 5) * 2
                p.setPen(Qt.NoPen)
                p.setBrush(QColor(t.colour))
                p.drawPolygon(QPolygonF([QPointF(-5, -30 + bob), QPointF(5, -30 + bob), QPointF(0, -22 + bob)]))
            p.setBrush(QColor(0, 0, 0, 150))
            p.drawRect(QRectF(-11, 4, 22, 3))
            p.setBrush(QColor("#40E040") if t.health > 50 else QColor("#E0C040") if t.health > 25 else QColor("#E04040"))
            p.drawRect(QRectF(-11, 4, 22 * t.health / 100, 3))
            p.restore()
        # shots and their trails
        for s in b.shots:
            if len(s.trail) > 1:
                col = QColor(getattr(s, "funky_colour", None) or s.owner.colour)
                col.setAlpha(150 if G.WEAPONS[s.weapon][3] != "tracer" else 230)
                p.setPen(QPen(col, 1.2))
                p.drawPolyline(QPolygonF([QPointF(x, y) for x, y in s.trail[-120:]]))
            p.setPen(Qt.NoPen)
            p.setBrush(QColor("#FFFFFF"))
            p.drawEllipse(QPointF(s.x, s.y), 2.6, 2.6)
        # explosions
        for x, y, r, age, colour in b.blasts:
            f = min(1.0, age / 0.25)
            fade = max(0.0, 1 - (age - 0.25) / 0.35) if age > 0.25 else 1.0
            rr = r * (0.3 + 0.7 * f) + 4
            gg = QRadialGradient(QPointF(x, y), rr)
            c = QColor(colour)
            gg.setColorAt(0, QColor(255, 255, 220, int(255 * fade)))
            gg.setColorAt(0.5, QColor(c.red(), c.green(), c.blue(), int(230 * fade)))
            gg.setColorAt(1, QColor(c.red(), c.green() // 2, 0, 0))
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(gg))
            p.drawEllipse(QPointF(x, y), rr, rr)
        p.setFont(QFont("Arial", 9, QFont.Bold))
        for x, y, txt, age in b.texts:
            p.setPen(QColor(255, 255, 160, int(255 * max(0.0, 1 - age / 1.4))))
            p.drawText(QPointF(x - 8, y - age * 22), txt)
        p.restore()
        for t in self.tanks:
            if t.say:                                  # taunts, and last words
                self._bubble(p, t.x, t.y - 34, t.say[0])
        self._draw_hud(p)

    def _bubble(self, p, x, y, text):
        ox, oy, sc = self._view()
        x, y = ox + x * sc, oy + y * sc
        p.setFont(QFont("Arial", 8, QFont.Bold))
        fm = QFontMetrics(p.font())
        tw = fm.horizontalAdvance(text) + 12
        r = QRectF(max(4, min(self.width() - tw - 4, x - tw / 2)), y - 22, tw, 18)
        p.setPen(QPen(QColor("#202020"), 1))
        p.setBrush(QColor("#FFFFF0"))
        p.drawRoundedRect(r, 6, 6)
        p.drawPolygon(QPolygonF([QPointF(x - 4, r.bottom()), QPointF(x + 4, r.bottom()), QPointF(x, r.bottom() + 6)]))
        p.setPen(QColor("#101010"))
        p.drawText(r, Qt.AlignCenter, text)

    def _draw_hud(self, p):
        b = self.battle
        t = b.current
        w = self.width()
        g = QLinearGradient(0, 0, 0, HUD_H)
        g.setColorAt(0, QColor("#3A3A5A"))
        g.setColorAt(1, QColor("#18182A"))
        p.fillRect(QRectF(0, 0, w, HUD_H), QBrush(g))
        p.setPen(QPen(QColor("#8A8AB0"), 1))
        p.drawLine(QPointF(0, HUD_H - 0.5), QPointF(w, HUD_H - 0.5))
        p.setFont(QFont("Arial", 12, QFont.Bold))
        p.setPen(QColor(t.colour))
        p.drawText(QRectF(10, 4, 220, 22), Qt.AlignLeft | Qt.AlignVCenter,
                   t.name + ("  (thinking...)" if t.ai and not b.busy else ""))
        p.setFont(QFont("Arial", 10, QFont.Bold))
        p.setPen(QColor("white"))
        p.drawText(QRectF(10, 28, 120, 18), Qt.AlignLeft, f"Angle: {int(round(t.angle))}")
        p.drawText(QRectF(10, 44, 200, 18), Qt.AlignLeft,
                   f"Power: {int(min(t.power, t.max_power))} / {int(t.max_power)}")
        qty = "inf" if t.weapon == "Baby Missile" else t.inventory.get(t.weapon, 0)
        wr = QRectF(240, 8, 230, 24)
        self._button(p, QRectF(wr.x(), wr.y(), 24, 24), "<", lambda: self._cycle_weapon(-1), small=True)
        self._button(p, QRectF(wr.right() - 24, wr.y(), 24, 24), ">", lambda: self._cycle_weapon(1), small=True)
        p.setPen(QColor("#F8D040"))
        p.drawText(QRectF(wr.x() + 26, wr.y(), wr.width() - 52, 24), Qt.AlignCenter, f"{t.weapon} ({qty})")
        p.setFont(QFont("Arial", 9))
        p.setPen(QColor("#C0C0E0"))
        items = []
        for it in ("Shield", "Heavy Shield", "Battery", "Parachute", "Fuel"):
            if t.inventory.get(it, 0):
                items.append(f"{it} {t.inventory[it]}")
        p.drawText(QRectF(240, 36, 330, 22), Qt.AlignLeft | Qt.AlignVCenter,
                   ("  ".join(items) or "No gadgets") + (f"   Shield: {int(t.shield)}" if t.shield > 0 else ""))
        if not t.ai and not b.busy and self.state == "battle":
            self._button(p, QRectF(480, 8, 80, 46), "FIRE!", self._fire, "#A02010")
        # the wind
        p.setFont(QFont("Arial", 10, QFont.Bold))
        p.setPen(QColor("white"))
        cx = w - 200
        p.drawText(QRectF(cx - 60, 6, 120, 18), Qt.AlignCenter, f"Wind: {abs(b.wind)}" if b.wind else "No wind")
        if b.wind:
            n = abs(b.wind) * 4
            d = 1 if b.wind > 0 else -1
            p.setPen(QPen(QColor("#A0E0FF"), 3))
            p.drawLine(QPointF(cx - d * n, 34), QPointF(cx + d * n, 34))
            p.drawLine(QPointF(cx + d * n, 34), QPointF(cx + d * (n - 7), 28))
            p.drawLine(QPointF(cx + d * n, 34), QPointF(cx + d * (n - 7), 40))
        p.setPen(QColor("#C0C0E0"))
        p.setFont(QFont("Arial", 9))
        p.drawText(QRectF(cx - 80, 42, 160, 18), Qt.AlignCenter, f"Round {self.round} of {self.rounds}")
        p.setFont(QFont("Arial", 9, QFont.Bold))
        p.setPen(QColor("#F8D040"))
        p.drawText(QRectF(w - 100, 6, 92, 18), Qt.AlignRight, f"${t.cash:,}")

    def _draw_round_over(self, p):
        w, h = self.width(), self.height()
        r = QRectF(w / 2 - 230, h / 2 - 160, 460, 320)
        p.setPen(QPen(QColor("#F0A040"), 2))
        p.setBrush(QColor(10, 10, 30, 230))
        p.drawRoundedRect(r, 10, 10)
        win = self.round_winner
        p.setFont(QFont("Impact", 22))
        p.setPen(QColor(win.colour) if win else QColor("white"))
        p.drawText(QRectF(r.x(), r.y() + 14, r.width(), 34), Qt.AlignHCenter,
                   f"{win.name} wins round {self.round}!" if win else "Nobody survived!")
        p.setFont(QFont("Arial", 10, QFont.Bold))
        y = r.y() + 64
        p.setPen(QColor("#C0C0E0"))
        p.drawText(QRectF(r.x() + 30, y, 400, 18), Qt.AlignLeft, "Tank                      Score   Kills   Cash")
        y += 22
        for t in sorted(self.tanks, key=lambda t: (-t.score, -t.cash)):
            p.setPen(QColor(t.colour))
            p.drawText(QRectF(r.x() + 30, y, 180, 18), Qt.AlignLeft, t.name)
            p.setPen(QColor("white"))
            p.drawText(QRectF(r.x() + 200, y, 50, 18), Qt.AlignRight, str(t.score))
            p.drawText(QRectF(r.x() + 260, y, 50, 18), Qt.AlignRight, str(t.kills))
            p.drawText(QRectF(r.x() + 310, y, 100, 18), Qt.AlignRight, f"${t.cash:,}")
            y += 20
        label = "Final Results" if self.round >= self.rounds else "To the Shop"
        self._button(p, QRectF(r.center().x() - 90, r.bottom() - 54, 180, 40), label, self._advance, "#8A2A1A")

    def _draw_game_over(self, p):
        self._backdrop(p, "sunset")
        w, h = self.width(), self.height()
        ranked = sorted(self.tanks, key=lambda t: (-t.score, -t.cash))
        p.setFont(QFont("Impact", 34))
        p.setPen(QColor(ranked[0].colour))
        p.drawText(QRectF(0, 30, w, 50), Qt.AlignHCenter, f"{ranked[0].name} is the Champion!")
        p.setFont(QFont("Arial", 12, QFont.Bold))
        y = 110
        for i, t in enumerate(ranked):
            p.drawPixmap(QPointF(w / 2 - 210, y - 6), tank_pixmap(t.colour, 30))
            p.setPen(QColor("white"))
            p.drawText(QRectF(w / 2 - 170, y, 380, 24), Qt.AlignLeft,
                       f"{i + 1}. {t.name}  -  score {t.score}, {t.kills} kills, ${t.cash:,}")
            y += 34
        self._button(p, QRectF(w / 2 - 220, h - 90, 200, 44), "Play Again", self._start_game, "#8A2A1A")
        self._button(p, QRectF(w / 2 + 20, h - 90, 200, 44), "Main Menu", lambda: setattr(self, "state", "title"),
                     "#3A3A6A")

    def shutdown(self):
        self.timer.stop()


_open = {}


def launch(desktop):
    win = _open.get("win")
    if win is not None and isValid(win):
        desktop.open_window(win)
        return win
    body = Scorched(desktop)
    win = XPWindow(desktop, "Scorched Claude", body, scorched_icon(), size=(G.W + 20, G.H + HUD_H + 40))
    body.frame = win
    _open["win"] = win
    desktop.open_window(win)
    body.setFocus()
    return win


def shutdown():
    win = _open.get("win")
    if win is not None and isValid(win):
        win.content.shutdown()
