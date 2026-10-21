"""ClaudePit: a slot machine at the bottom of a pit, a debt, and a trapdoor - after CloverPit.

Buy spins with the coins in your pocket and pull the lever (or press Space); matching symbols in rows, columns,
diagonals and bigger shapes pay out. Put coins in the ATM - only those count, and they earn interest - before the
deadline's third round is spent, or the trapdoor opens. 6-6-6 takes everything in your pocket. Clover Tickets buy
charms from the machine on the wall; the phone rings after every deadline paid. Pay ten deadlines to climb out.
(The rules are in game.py; the soundscape - all synthesized - is in sound.py, and the music and the sound effects can
each be switched off.) The run saves itself as you go."""
import json
import math
import random
import time

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import (QColor, QFont, QIcon, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap,
                           QPolygonF, QRadialGradient)
from PySide6.QtWidgets import QWidget
from shiboken6 import isValid

from claudecore import host

from .game import (CHARMS, COIN, COLS, FINAL, PATTERNS, ROUNDS, ROWS, SHAPE_OF, SIX, SYMBOL_NAME, SYMBOLS, Run,
                   fmt)
from .sound import Audio

TITLE = "ClaudePit"
UI = "Segoe UI"
SYMBOL_FONT = "Segoe UI Symbol"
GOLD = "#F2C14E"
GREEN = "#6BD48A"
RED = "#E0463A"
DIM = "#9A8F84"
SCREEN = "#7CF29A"
CELL_W, CELL_H = 104, 92
SPEEDS = (1, 2, 4)
GLYPH = {"horseshoe": "∩", "rabbit_foot": "☘", "fortune_cookie": "✉", "piggy_bank": "$", "golden_lever": "⚙",
         "magnifier": "◎", "plumb_bob": "▼", "slide_rule": "◢", "ribbon": "≋", "crown": "♛", "rosary": "✝",
         "hourglass": "⌛", "coupon": "✂", "die": "⚅", "weighted_reels": "⚖", "fruit_basket": "❀",
         "lucky_cat": "☺", "snake_eyes": "⚀", "coin_purse": "¤", "rope_ladder": "☰", "mirror": "◐",
         "abacus": "∷", "wishing_well": "Ω", "clover_field": "✿", "red_phone": "☎", "magnet": "⚡"}
VALUE_CHARM = {"lemon_zest": "lemon", "cherry_pit": "cherry", "clover_pot": "clover", "brass_bell": "bell",
               "loupe": "diamond", "pirate_map": "treasure", "lucky_seven": "seven"}
PRICE_COLOUR = {1: "#6E7F6A", 2: "#4F8A5B", 3: "#3D6FA8", 4: "#7A4FA8", 5: "#B8862E"}
KIND_COLOUR = {"normal": "#4A6A8A", "holy": "#D9B64A", "evil": "#A8322A"}

_fonts = {}


def font(size, bold=True, family=UI):
    key = (int(size), bold, family)
    f = _fonts.get(key)
    if f is None:
        f = QFont(family)
        f.setPixelSize(max(1, int(size)))
        f.setBold(bold)
        _fonts[key] = f
    return f


def text(p, rect, s, size, colour="#EDE6DA", align=Qt.AlignCenter, bold=True, shadow=True, family=UI):
    p.setFont(font(size, bold, family))
    if shadow:
        p.setPen(QColor(0, 0, 0, 150))
        p.drawText(rect.translated(1.2, 1.6), align, s)
    p.setPen(QColor(colour))
    p.drawText(rect, align, s)


def panel(p, rect, fill="#1C1815", border="#4A3F35", radius=8, width=2.0):
    p.setPen(QPen(QColor(border), width) if border else Qt.NoPen)
    p.setBrush(QColor(fill))
    p.drawRoundedRect(rect, radius, radius)


# ---- the symbols -------------------------------------------------------------------------------------------------
_cache = {}


def paint_symbol(p, r, sym):
    """A reel symbol, drawn once per size and kept."""
    key = (sym, int(r.width()), int(r.height()))
    pm = _cache.get(key)
    if pm is None:
        pm = QPixmap(int(r.width()) * 2, int(r.height()) * 2)
        pm.setDevicePixelRatio(2)
        pm.fill(Qt.transparent)
        q = QPainter(pm)
        q.setRenderHint(QPainter.Antialiasing)
        _symbol(q, QRectF(0, 0, r.width(), r.height()), sym)
        q.end()
        _cache[key] = pm
    p.drawPixmap(r.topLeft(), pm)


def _symbol(p, r, sym):
    s = min(r.width(), r.height())
    cx, cy = r.center().x(), r.center().y()
    u = s / 100.0
    outline = QPen(QColor(0, 0, 0, 170), max(1.0, 2.2 * u))
    if sym == "lemon":
        p.save()
        p.translate(cx, cy)
        p.rotate(-25)
        p.setPen(outline)
        g = QRadialGradient(QPointF(-10 * u, -10 * u), 40 * u)
        g.setColorAt(0, QColor("#FFF6A0"))
        g.setColorAt(1, QColor("#E8C21C"))
        p.setBrush(g)
        path = QPainterPath()
        path.moveTo(-38 * u, 0)
        path.quadTo(-30 * u, -28 * u, 0, -27 * u)
        path.quadTo(30 * u, -28 * u, 38 * u, 0)
        path.quadTo(30 * u, 28 * u, 0, 27 * u)
        path.quadTo(-30 * u, 28 * u, -38 * u, 0)
        p.drawPath(path)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(255, 255, 255, 110))
        p.drawEllipse(QRectF(-16 * u, -18 * u, 16 * u, 8 * u))
        p.restore()
    elif sym == "cherry":
        p.setPen(QPen(QColor("#3F7A2A"), 3.2 * u, Qt.SolidLine, Qt.RoundCap))
        p.setBrush(Qt.NoBrush)
        top = QPointF(cx + 6 * u, cy - 34 * u)
        for x in (-16, 16):
            path = QPainterPath(QPointF(cx + x * u, cy + 8 * u))
            path.quadTo(QPointF(cx + x * 0.3 * u, cy - 18 * u), top)
            p.drawPath(path)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#4E9A33"))
        leaf = QPainterPath(top)
        leaf.quadTo(QPointF(cx + 30 * u, cy - 44 * u), QPointF(cx + 34 * u, cy - 26 * u))
        leaf.quadTo(QPointF(cx + 18 * u, cy - 26 * u), top)
        p.drawPath(leaf)
        for x in (-16, 16):
            g = QRadialGradient(QPointF(cx + (x - 6) * u, cy + 14 * u), 20 * u)
            g.setColorAt(0, QColor("#FF6A5E"))
            g.setColorAt(1, QColor("#A3151B"))
            p.setPen(outline)
            p.setBrush(g)
            p.drawEllipse(QPointF(cx + x * u, cy + 20 * u), 15 * u, 15 * u)
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(255, 255, 255, 120))
            p.drawEllipse(QPointF(cx + (x - 6) * u, cy + 14 * u), 4 * u, 3 * u)
    elif sym == "clover":
        p.setPen(QPen(QColor("#2D6A2A"), 4 * u, Qt.SolidLine, Qt.RoundCap))
        path = QPainterPath(QPointF(cx, cy + 4 * u))
        path.quadTo(QPointF(cx + 6 * u, cy + 26 * u), QPointF(cx + 18 * u, cy + 38 * u))
        p.drawPath(path)
        for ang in (45, 135, 225, 315):
            p.save()
            p.translate(cx, cy)
            p.rotate(ang)
            g = QRadialGradient(QPointF(0, -14 * u), 18 * u)
            g.setColorAt(0, QColor("#8BE07A"))
            g.setColorAt(1, QColor("#2E8B3A"))
            p.setPen(outline)
            p.setBrush(g)
            leaf = QPainterPath(QPointF(0, 0))
            leaf.cubicTo(QPointF(-26 * u, -14 * u), QPointF(-14 * u, -34 * u), QPointF(0, -22 * u))
            leaf.cubicTo(QPointF(14 * u, -34 * u), QPointF(26 * u, -14 * u), QPointF(0, 0))
            p.drawPath(leaf)
            p.restore()
    elif sym == "bell":
        g = QLinearGradient(QPointF(cx - 30 * u, 0), QPointF(cx + 30 * u, 0))
        g.setColorAt(0, QColor("#B8862E"))
        g.setColorAt(0.4, QColor("#FFE08A"))
        g.setColorAt(1, QColor("#A8741E"))
        p.setPen(outline)
        p.setBrush(g)
        path = QPainterPath(QPointF(cx - 34 * u, cy + 22 * u))
        path.quadTo(QPointF(cx - 24 * u, cy + 14 * u), QPointF(cx - 24 * u, cy - 6 * u))
        path.cubicTo(QPointF(cx - 24 * u, cy - 38 * u), QPointF(cx + 24 * u, cy - 38 * u), QPointF(cx + 24 * u, cy - 6 * u))
        path.quadTo(QPointF(cx + 24 * u, cy + 14 * u), QPointF(cx + 34 * u, cy + 22 * u))
        path.closeSubpath()
        p.drawPath(path)
        p.setBrush(QColor("#8A5A14"))
        p.drawEllipse(QPointF(cx, cy + 28 * u), 7 * u, 7 * u)
        p.drawEllipse(QPointF(cx, cy - 36 * u), 5 * u, 5 * u)
    elif sym == "diamond":
        top, mid, bot = cy - 26 * u, cy - 8 * u, cy + 34 * u
        pts = [QPointF(cx - 22 * u, top), QPointF(cx + 22 * u, top), QPointF(cx + 38 * u, mid), QPointF(cx, bot),
               QPointF(cx - 38 * u, mid)]
        g = QLinearGradient(QPointF(cx, top), QPointF(cx, bot))
        g.setColorAt(0, QColor("#E6FCFF"))
        g.setColorAt(0.5, QColor("#5FD3F0"))
        g.setColorAt(1, QColor("#1B7FB8"))
        p.setPen(outline)
        p.setBrush(g)
        p.drawPolygon(QPolygonF(pts))
        p.setPen(QPen(QColor(255, 255, 255, 150), 1.4 * u))
        p.drawLine(QPointF(cx - 38 * u, mid), QPointF(cx + 38 * u, mid))
        for x0, x1 in ((-22, -10), (0, -10), (0, 10), (22, 10)):
            p.drawLine(QPointF(cx + x0 * u, top), QPointF(cx + x1 * u, mid))
        p.drawLine(QPointF(cx - 10 * u, mid), QPointF(cx, bot))
        p.drawLine(QPointF(cx + 10 * u, mid), QPointF(cx, bot))
    elif sym == "treasure":
        body = QRectF(cx - 36 * u, cy - 4 * u, 72 * u, 36 * u)
        lid = QRectF(cx - 36 * u, cy - 30 * u, 72 * u, 30 * u)
        p.setPen(outline)
        p.setBrush(QColor("#FFD54A"))                 # coins spilling over
        for k, x in enumerate((-22, -8, 6, 20)):
            p.drawEllipse(QPointF(cx + x * u, cy - 6 * u - (k % 2) * 4 * u), 9 * u, 6 * u)
        g = QLinearGradient(body.topLeft(), body.bottomLeft())
        g.setColorAt(0, QColor("#9A5A2A"))
        g.setColorAt(1, QColor("#5A3014"))
        p.setBrush(g)
        p.drawRect(body)
        path = QPainterPath()
        path.moveTo(lid.bottomLeft())
        path.lineTo(lid.left(), lid.top() + 12 * u)
        path.quadTo(QPointF(cx, lid.top() - 8 * u), QPointF(lid.right(), lid.top() + 12 * u))
        path.lineTo(lid.bottomRight())
        p.save()
        p.translate(0, -8 * u)
        p.rotate(0)
        p.drawPath(path)
        p.restore()
        p.setBrush(QColor("#E0B040"))
        for x in (-26, 22):
            p.drawRect(QRectF(cx + x * u, cy - 36 * u, 6 * u, 68 * u))
        p.drawRoundedRect(QRectF(cx - 7 * u, cy - 2 * u, 14 * u, 16 * u), 3 * u, 3 * u)
    elif sym in ("seven", SIX):
        ch = "7" if sym == "seven" else "6"
        f = QFont("Arial Black")
        f.setPixelSize(int(80 * u))
        f.setBold(True)
        path = QPainterPath()
        path.addText(0, 0, f, ch)
        br = path.boundingRect()
        path.translate(cx - br.center().x(), cy - br.center().y())
        if sym == "seven":
            g = QLinearGradient(QPointF(cx, cy - 36 * u), QPointF(cx, cy + 36 * u))
            g.setColorAt(0, QColor("#FF7A5A"))
            g.setColorAt(1, QColor("#B0121A"))
            p.setPen(QPen(QColor("#2A0505"), 3.5 * u))
        else:
            glow = QRadialGradient(QPointF(cx, cy), 46 * u)
            glow.setColorAt(0, QColor(255, 30, 30, 120))
            glow.setColorAt(1, QColor(255, 0, 0, 0))
            p.setPen(Qt.NoPen)
            p.setBrush(glow)
            p.drawEllipse(QPointF(cx, cy), 46 * u, 46 * u)
            g = QLinearGradient(QPointF(cx, cy - 36 * u), QPointF(cx, cy + 36 * u))
            g.setColorAt(0, QColor("#5A0000"))
            g.setColorAt(1, QColor("#1A0000"))
            p.setPen(QPen(QColor("#FF3A2A"), 2.5 * u))
        p.setBrush(g)
        p.drawPath(path)


def paint_charm(p, r, key, owned=False):
    """A charm's token: its symbol, or its sign on a badge."""
    price = CHARMS[key][1]
    col = QColor(PRICE_COLOUR.get(price, "#555555"))
    p.setPen(QPen(col.lighter(140), 2))
    g = QRadialGradient(r.center(), r.width() * 0.6)
    g.setColorAt(0, col.lighter(130))
    g.setColorAt(1, col.darker(160))
    p.setBrush(g)
    p.drawEllipse(r)
    if key in VALUE_CHARM:
        paint_symbol(p, r.adjusted(r.width() * 0.16, r.height() * 0.16, -r.width() * 0.16, -r.height() * 0.16),
                     VALUE_CHARM[key])
    else:
        text(p, r, GLYPH.get(key, "?"), r.height() * 0.5, "#FFF6E0", family=SYMBOL_FONT)


def paint_shape(p, r, key, colour):
    """A little 5 x 3 grid with a pattern's cells lit."""
    cells = set(map(tuple, SHAPE_OF[key]))
    cw, ch = r.width() / COLS, r.height() / ROWS
    p.setPen(Qt.NoPen)
    for rr in range(ROWS):
        for c in range(COLS):
            p.setBrush(QColor(colour) if (rr, c) in cells else QColor(255, 255, 255, 28))
            p.drawRoundedRect(QRectF(r.x() + c * cw + 1, r.y() + rr * ch + 1, cw - 2, ch - 2), 1.5, 1.5)


# ---- the game ----------------------------------------------------------------------------------------------------
class Pit(QWidget):
    def __init__(self, desktop):
        super().__init__()
        self.desktop = desktop
        self.frame = None
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMinimumSize(1120, 740)
        self.settings = self._load("settings.json", {}) or {}
        self.speed = self.settings.get("speed", 1) if self.settings.get("speed") in SPEEDS else 1
        self.music_on = self.settings.get("music", True)
        self.sfx_on = self.settings.get("sfx", True)
        self.audio = Audio(self, self.music_on, self.sfx_on)
        self.stats = self._load("stats.json", {}) or {}
        self.run = None
        saved = self._load("run.json", None)
        if saved:
            try:
                self.run = Run.from_json(saved)
            except (KeyError, TypeError, ValueError, IndexError):
                self.run = None
        self.screen = "title"
        self.anim = None                # a spin on its way
        self.view = None                # what the counters show while a spin is on its way
        self.auto = False
        self.answered = False           # the phone has been picked up
        self.ring_at = 0.0
        self.fall = None                # when the trapdoor opened
        self.sold = None                # a charm picked to sell
        self.toast = None
        self.flash = None               # (colour, until)
        self.recorded = False
        self.mouse = QPointF(-1, -1)
        self.hits, self.tips = [], []
        self.strips = [[random.choice(SYMBOLS) for _k in range(24)] for _c in range(COLS)]
        self.t = 0.0
        self.last = time.perf_counter()
        self.timer = QTimer(self)
        self.timer.setTimerType(Qt.PreciseTimer)
        self.timer.setInterval(16)
        self.timer.timeout.connect(self._tick)
        self.timer.start()

    # ---- saving ----
    def _load(self, name, default):
        try:
            return json.loads((host.saves(TITLE) / name).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return default

    def _write(self, name, data):
        try:
            path = host.saves(TITLE) / name
            if data is None:
                path.unlink(missing_ok=True)
            else:
                path.write_text(json.dumps(data), encoding="utf-8")
        except OSError:
            pass

    def _save(self):
        run = self.run
        if run is None or self.anim:
            return
        self._write("run.json", None if run.stage == "dead" else run.to_json())

    def _save_settings(self):
        self._write("settings.json", {"speed": self.speed, "music": self.music_on, "sfx": self.sfx_on})

    def _record(self):
        if self.recorded or self.run is None:
            return
        self.recorded = True
        s, run = self.stats, self.run
        s["runs"] = s.get("runs", 0) + 1
        s["best_deadline"] = max(s.get("best_deadline", 0), run.deadline - (0 if run.stage == "dead" else 1))
        s["best_spin"] = max(s.get("best_spin", 0), run.best_spin)
        if run.won:
            s["escapes"] = s.get("escapes", 0) + 1
        self._write("stats.json", s)

    # ---- the clock ----
    def _tick(self):
        now = time.perf_counter()
        dt = min(0.1, now - self.last)
        self.last = now
        self.t += dt
        if self.anim:
            self._step_anim(dt)
        run = self.run
        if run and self.screen == "game" and not self.anim and self.fall is None:
            if run.stage == "phone" and not self.answered and self.t >= self.ring_at:
                self.sfx("ring")
                self.ring_at = self.t + 2.4
            if self.auto:
                if run.stage == "spin":
                    self._pull()
                else:
                    self.auto = False
        self.audio.mood = self._mood()
        self.audio.tick(dt)
        if self.toast and self.t > self.toast[1]:
            self.toast = None
        self.update()

    def _mood(self):
        run = self.run
        if self.screen != "game" or run is None or run.stage not in ("spin", "package"):
            return "pit"
        short = run.bank + run.pocket < run.debt
        return "tension" if short and run.round == ROUNDS else "pit"

    def sfx(self, name):
        self.audio.play(name)

    def say(self, msg, secs=2.6):
        if msg:
            self.toast = (msg, self.t + secs)

    # ---- pulling the lever ----
    def _pull(self):
        run = self.run
        if run is None or self.anim or run.stage != "spin" or self.fall is not None:
            return
        before = {"pocket": run.pocket, "bank": run.bank, "tickets": run.tickets, "spins": run.spins - 1,
                  "round": run.round, "deadline": run.deadline, "debt": run.debt}
        res = run.spin()
        if res is None:
            return
        self.sold = None
        self.view = before
        self.anim = {"res": res, "clock": 0.0, "phase": "reels", "shown": 0, "k": 0, "next_tick": 0.0,
                     "stopped": 0}
        for c in range(COLS):
            random.shuffle(self.strips[c])
        self.sfx("lever")

    def _step_anim(self, dt):
        a = self.anim
        res = a["res"]
        a["clock"] += dt * self.speed
        if a["phase"] == "reels":
            if a["clock"] >= a["next_tick"] and a["stopped"] < COLS:
                self.sfx("tick")
                a["next_tick"] = a["clock"] + 0.07
            stops = [0.55 + 0.22 * c for c in range(COLS)]
            while a["stopped"] < COLS and a["clock"] >= stops[a["stopped"]]:
                self.sfx(f"stop{a['stopped']}")
                a["stopped"] += 1
            if a["stopped"] >= COLS and a["clock"] >= stops[-1] + 0.25:
                a["phase"], a["clock"] = "pay", 0.0
                if res["six"]:
                    self.sfx("six")
                    self.flash = ("#C00000", self.t + 1.4)
                    self.view["pocket"] = 0
                    a["phase"] = "six"
                elif not res["wins"]:
                    a["phase"] = "extras"
        elif a["phase"] == "six":
            if a["clock"] >= 1.6:
                a["phase"], a["clock"] = "extras", 0.0
        elif a["phase"] == "pay":
            wins = res["wins"]
            k = a["k"]
            if k < len(wins) and a["clock"] >= 0.5 * k:
                w = wins[k]
                self.sfx("jackpot" if w["key"] == "jackpot" else f"win{min(11, k)}")
                self.view["pocket"] += w["coins"]
                a["shown"] += w["coins"]
                a["k"] += 1
            if a["k"] >= len(wins) and a["clock"] >= 0.5 * len(wins) + 0.35:
                a["phase"], a["clock"] = "extras", 0.0
        elif a["phase"] == "extras":
            if res["extras"] and not a.get("chimed"):
                a["chimed"] = True
                self.sfx("coin")
            if a["clock"] >= (0.7 if res["extras"] else 0.0):
                if res["total"] >= 40 * self.run.growth() and not res["six"]:
                    self.sfx("pour")
                self._finish_anim()

    def _finish_anim(self):
        res = self.anim["res"]
        self.anim = None
        self.view = None
        run = self.run
        if res.get("tickets"):
            self.sfx("ticket")
        if res.get("interest"):
            self.say(f"Round {run.round} of {ROUNDS}. The ATM paid {fmt(res['interest'])} interest.")
            self.sfx("interest")
        elif run.stage == "package" and "deadline" not in res:
            self.say(f"Round {run.round} of {ROUNDS}: buy your spins.")
        out = res.get("deadline")
        if out:
            self._deadline_done(out)
        self._save()

    def _deadline_done(self, out):
        run = self.run
        if out.get("dead"):
            self.auto = False
            self.toast = None
            self.fall = self.t
            self.sfx("trapdoor")
            self._record()
            self._write("run.json", None)
            return
        if out.get("ladder"):
            self.say("The Rope Ladder snapped - but it held long enough. The debt is forgiven, just this once.", 4)
        elif out.get("paid"):
            extra = f" (+{out['bonus']} tickets for paying early)" if out.get("bonus") else ""
            self.say(f"Deadline {run.deadline} paid: {fmt(out['debt'])} coins{extra}. The phone is ringing...", 4)
            self.sfx("paid")
        self.answered = False
        self.ring_at = self.t + 0.8

    # ---- painting ----
    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        p.setRenderHint(QPainter.TextAntialiasing)
        self.hits, self.tips = [], []
        if self.screen == "title" or self.run is None:
            self._background(p)
            self._draw_title(p)
        elif self.fall is not None:
            self._draw_fall(p)
        else:
            self._background(p)
            self._draw_game(p)
        if self.flash and self.t < self.flash[1]:
            c = QColor(self.flash[0])
            c.setAlpha(int(110 * (self.flash[1] - self.t) / 1.4))
            p.fillRect(self.rect(), c)
        self._draw_toast(p)
        self._draw_tip(p)
        self._sound_buttons(p)
        p.end()

    def _background(self, p):
        w, h = self.width(), self.height()
        g = QLinearGradient(0, 0, 0, h)
        g.setColorAt(0, QColor("#2A221C"))
        g.setColorAt(0.75, QColor("#15110E"))
        g.setColorAt(1, QColor("#0A0807"))
        p.fillRect(self.rect(), g)
        p.setPen(QPen(QColor(0, 0, 0, 70), 2))      # the stone blocks of the walls
        bh = 46
        for row in range(int(h * 0.78 / bh) + 1):
            y = row * bh
            p.drawLine(QPointF(0, y), QPointF(w, y))
            off = 0 if row % 2 else 60
            for x in range(-off, w, 120):
                p.drawLine(QPointF(x, y), QPointF(x, y + bh))
        floor = h * 0.8
        p.fillRect(QRectF(0, floor, w, h - floor), QColor("#0E0B09"))
        p.setPen(QPen(QColor("#2A221C"), 2))
        p.drawLine(QPointF(0, floor), QPointF(w, floor))
        flicker = 0.85 + 0.15 * math.sin(self.t * 13) * math.sin(self.t * 3.1)
        glow = QRadialGradient(QPointF(w / 2, 0), h * 0.9)
        glow.setColorAt(0, QColor(255, 210, 140, int(70 * flicker)))
        glow.setColorAt(1, QColor(255, 200, 120, 0))
        p.fillRect(self.rect(), glow)
        p.setPen(QPen(QColor("#111111"), 2))        # the bulb on its wire
        p.drawLine(QPointF(w / 2, 0), QPointF(w / 2, 22))
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(255, 230, 170, int(255 * flicker)))
        p.drawEllipse(QPointF(w / 2, 30), 8, 10)
        vig = QRadialGradient(QPointF(w / 2, h / 2), max(w, h) * 0.75)
        vig.setColorAt(0.55, QColor(0, 0, 0, 0))
        vig.setColorAt(1, QColor(0, 0, 0, 200))
        p.fillRect(self.rect(), vig)

    def _layout(self):
        w, h = self.width(), self.height()
        mw = CELL_W * COLS + 70
        mx = (w - mw) / 2 - 24                          # (room on the right for the lever)
        top = 54 + CELL_H * ROWS + 200
        return {"w": w, "h": h, "machine": QRectF(mx, 54, mw, CELL_H * ROWS + 190),
                "reels": QRectF(mx + 35, 128, CELL_W * COLS, CELL_H * ROWS),
                "left": QRectF(18, 54, mx - 36, h - 72), "right": QRectF(mx + mw + 66, 54, w - mx - mw - 84, h - 72),
                "bottom": QRectF(mx, top, mw, h * 0.8 - 6 - top)}

    def _btn(self, p, rect, label, colour, action, enabled=True, size=14):
        hover = enabled and rect.contains(self.mouse)
        c = QColor(colour) if enabled else QColor("#3A3430")
        p.setPen(Qt.NoPen)
        p.setBrush(c.darker(170))
        p.drawRoundedRect(rect.translated(0, 3), 6, 6)
        r2 = rect.translated(0, 2) if hover else rect
        p.setBrush(c.lighter(115) if hover else c)
        p.drawRoundedRect(r2, 6, 6)
        text(p, r2, label, size, "#FFFFFF" if enabled else "#7A706A", Qt.AlignCenter | Qt.TextWordWrap)
        if enabled and action:
            self.hits.append((rect, action))

    def _tip(self, rect, title, lines):
        self.tips.append((rect, title, [ln for ln in lines if ln]))

    def _shown(self):
        """The counters: as they were when the lever was pulled, while the reels are still going."""
        run = self.run
        if self.view:
            return self.view
        return {"pocket": run.pocket, "bank": run.bank, "tickets": run.tickets, "spins": run.spins,
                "round": run.round, "deadline": run.deadline, "debt": run.debt}

    def _draw_game(self, p):
        L = self._layout()
        self._draw_machine(p, L)
        self._draw_atm(p, L)
        self._draw_store(p, L)
        self._draw_table(p, L)
        self._draw_trapdoor(p, L, 0.0)
        run = self.run
        if self.anim is None:
            if run.stage == "package":
                self._draw_packages(p, L)
            elif run.stage == "phone":
                self._draw_phone(p, L)
            elif run.stage == "won":
                self._draw_won(p, L)

    # the machine
    def _draw_machine(self, p, L):
        m, reels = L["machine"], L["reels"]
        run = self.run
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(0, 0, 0, 120))
        p.drawRoundedRect(m.translated(8, 12), 22, 22)
        g = QLinearGradient(m.topLeft(), m.topRight())
        g.setColorAt(0, QColor("#4A1414"))
        g.setColorAt(0.5, QColor("#7A2020"))
        g.setColorAt(1, QColor("#3A0E0E"))
        p.setPen(QPen(QColor("#C9A040"), 3))
        p.setBrush(g)
        p.drawRoundedRect(m, 22, 22)
        marquee = QRectF(m.x() + 40, m.y() + 12, m.width() - 80, 52)
        panel(p, marquee, "#1A0A0A", "#C9A040", 10, 2)
        for k in range(14):                          # the bulbs round the sign, chasing
            x = marquee.x() + 14 + k * (marquee.width() - 28) / 13
            on = (int(self.t * 6) + k) % 3 == 0 or bool(self.anim and self.anim["phase"] == "pay")
            p.setBrush(QColor("#FFE9A0") if on else QColor("#5A4A2A"))
            p.setPen(Qt.NoPen)
            p.drawEllipse(QPointF(x, marquee.y() + 6), 3, 3)
            p.drawEllipse(QPointF(x, marquee.bottom() - 6), 3, 3)
        text(p, marquee, "C L A U D E P I T", 26, GOLD)
        frame = reels.adjusted(-10, -10, 10, 10)
        panel(p, frame, "#0A0606", "#C9A040", 10, 3)
        p.save()
        p.setClipRect(reels)
        self._draw_reels(p, reels)
        p.restore()
        glass = QLinearGradient(reels.topLeft(), reels.bottomLeft())
        glass.setColorAt(0, QColor(255, 255, 255, 40))
        glass.setColorAt(0.25, QColor(255, 255, 255, 0))
        glass.setColorAt(1, QColor(0, 0, 0, 60))
        p.fillRect(reels, glass)
        # under the reels: what's left of this round, and the odds
        v = self._shown()
        strip = QRectF(m.x() + 30, reels.bottom() + 20, m.width() - 60, 34)
        panel(p, strip, "#140808", "#6A4A2A", 6, 1.5)
        stage = run.stage if not self.anim else "spin"
        msg = (f"SPINS {v['spins']}" if stage == "spin" else "BUY SPINS" if stage == "package" else "")
        text(p, QRectF(strip.x() + 10, strip.y(), 260, strip.height()), f"{msg}   ROUND {v['round']}/{ROUNDS}", 15,
             SCREEN, Qt.AlignLeft | Qt.AlignVCenter, family="Consolas")
        odds = f"LUCK {run.total_luck()}  666: {run.chance_666() * 100:.1f}%"
        text(p, QRectF(strip.right() - 230, strip.y(), 220, strip.height()), odds, 14, "#E08A7A",
             Qt.AlignRight | Qt.AlignVCenter, family="Consolas")
        self._tip(QRectF(strip.right() - 230, strip.y(), 220, strip.height()), "Luck and 666",
                  ["Luck makes symbols copy their neighbours, so patterns come up more often.",
                   "6-6-6 across the middle takes every coin in your pocket. Coins in the ATM are safe."])
        # the lever
        lever_x = m.right() + 4
        base_y = reels.top() + 40
        pulled = 0.0
        if self.anim and self.anim["phase"] == "reels":
            pulled = max(0.0, 1 - self.anim["clock"] / 0.45)
        top_y = base_y - 70 + pulled * 150
        p.setPen(QPen(QColor("#888888"), 7, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(QPointF(lever_x + 10, base_y + 40), QPointF(lever_x + 22, top_y))
        p.setPen(QPen(QColor("#222222"), 1.5))
        p.setBrush(QColor("#555555"))
        p.drawRoundedRect(QRectF(lever_x - 2, base_y + 26, 24, 40), 5, 5)
        ball = QRadialGradient(QPointF(lever_x + 18, top_y - 6), 16)
        ball.setColorAt(0, QColor("#FF8A7A"))
        ball.setColorAt(1, QColor("#9A1010"))
        p.setBrush(ball)
        p.drawEllipse(QPointF(lever_x + 22, top_y), 15, 15)
        can = run.stage == "spin" and not self.anim
        lever = QRectF(lever_x - 6, top_y - 20, 50, base_y + 70 - top_y + 20)
        if can:
            self.hits.append((lever, self._pull))
            self.hits.append((reels, self._pull))
            self._tip(lever, "Pull the lever", ["Or click the reels, or press Space."])
        # buttons under the strip
        by = strip.bottom() + 14
        bw = (m.width() - 60 - 20) / 3
        self._btn(p, QRectF(m.x() + 30, by, bw, 36), "Pull (Space)", "#9A2A1A", self._pull, can)
        label = "Auto: On" if self.auto else "Auto-spin"
        self._btn(p, QRectF(m.x() + 40 + bw, by, bw, 36), label, "#6A4A1A", self._toggle_auto,
                  run.stage == "spin" or self.auto)
        self._btn(p, QRectF(m.x() + 50 + 2 * bw, by, bw, 36), f"Speed x{self.speed}", "#3A3A4A", self._cycle_speed)

    def _draw_reels(self, p, reels):
        a = self.anim
        run = self.run
        grid = a["res"]["grid"] if a else run.grid
        lit = set()
        current = None
        if a and a["phase"] in ("pay", "extras"):
            wins = a["res"]["wins"]
            for w in wins[:a["k"]]:
                lit.update(map(tuple, w["cells"]))
            if a["phase"] == "pay" and a["k"]:
                current = wins[a["k"] - 1]
        six = a and a["res"]["six"] and a["phase"] in ("six", "extras")
        for c in range(COLS):
            x = reels.x() + c * CELL_W
            spinning = a and a["phase"] == "reels" and c >= a["stopped"]
            p.fillRect(QRectF(x + 1, reels.y(), CELL_W - 2, reels.height()), QColor("#F4ECDD"))
            if spinning:
                speed = 14.0
                pos = a["clock"] * speed + c * 1.7
                off = (pos - int(pos)) * CELL_H
                strip = self.strips[c]
                for k in range(-1, ROWS + 1):
                    sym = strip[(int(pos) - k) % len(strip)]
                    r = QRectF(x + 8, reels.y() + k * CELL_H + off + 6, CELL_W - 16, CELL_H - 12)
                    p.setOpacity(0.75)
                    paint_symbol(p, r, sym)
                    p.setOpacity(1.0)
                p.fillRect(QRectF(x + 1, reels.y(), CELL_W - 2, reels.height()), QColor(255, 255, 255, 50))
                continue
            bounce = 0.0
            if a and a["phase"] == "reels":
                since = a["clock"] - (0.55 + 0.22 * c)
                if 0 <= since < 0.15:
                    bounce = math.sin(since / 0.15 * math.pi) * 8
            for r_ in range(ROWS):
                cell = QRectF(x, reels.y() + r_ * CELL_H + bounce, CELL_W, CELL_H)
                sym = grid[r_][c]
                if (r_, c) in lit:
                    pulse = 0.5 + 0.5 * math.sin(self.t * 8)
                    hl = QColor(GOLD)
                    hl.setAlpha(int(90 + 80 * pulse))
                    p.fillRect(cell.adjusted(2, 2, -2, -2), hl)
                if six and sym == SIX:
                    p.fillRect(cell.adjusted(2, 2, -2, -2), QColor(120, 0, 0, 160))
                paint_symbol(p, cell.adjusted(8, 6, -8, -6), sym)
            p.setPen(QPen(QColor("#2A1A10"), 2))
            p.drawLine(QPointF(x, reels.y()), QPointF(x, reels.bottom()))
        if current:                                  # what this pattern paid
            cells = current["cells"]
            r_, c = cells[len(cells) // 2]
            centre = QPointF(reels.x() + (c + 0.5) * CELL_W, reels.y() + (r_ + 0.5) * CELL_H)
            box = QRectF(centre.x() - 95, centre.y() - 26, 190, 52)
            panel(p, box, "#1A0A0A", GOLD, 8, 2)
            text(p, QRectF(box.x(), box.y() + 2, box.width(), 22), f"{current['name']}  x{current['mult']}", 14, GOLD)
            text(p, QRectF(box.x(), box.y() + 24, box.width(), 24), f"+{fmt(current['coins'])}", 18, "#FFFFFF")
        if six:
            box = QRectF(reels.center().x() - 170, reels.center().y() - 40, 340, 80)
            panel(p, box, "#200000", "#FF3A2A", 10, 3)
            lost = a["res"]["lost"]
            text(p, QRectF(box.x(), box.y() + 6, box.width(), 36), "6 6 6", 30, "#FF3A2A")
            text(p, QRectF(box.x(), box.y() + 42, box.width(), 30),
                 f"Your pocket is empty. ({fmt(lost)} coins gone)" if lost else "Your pocket was already empty.", 14,
                 "#FFB0A0")
        if a and a["phase"] == "extras" and a["res"]["extras"]:
            lines = "   ".join(f"{n} {v}" for n, v in a["res"]["extras"])
            box = QRectF(reels.x() + 20, reels.bottom() - 40, reels.width() - 40, 32)
            panel(p, box, "#1A120A", "#8A6A3A", 6, 1.5)
            text(p, box, lines, 13, GOLD)

    # the ATM
    def _draw_atm(self, p, L):
        r = L["left"]
        run = self.run
        v = self._shown()
        box = QRectF(r.x(), r.y(), r.width(), 300)
        g = QLinearGradient(box.topLeft(), box.topRight())
        g.setColorAt(0, QColor("#4A4E52"))
        g.setColorAt(0.5, QColor("#6A6E72"))
        g.setColorAt(1, QColor("#3A3E42"))
        p.setPen(QPen(QColor("#22262A"), 2))
        p.setBrush(g)
        p.drawRoundedRect(box, 10, 10)
        text(p, QRectF(box.x(), box.y() + 6, box.width(), 22), "A T M", 15, "#DDE4EA")
        scr = QRectF(box.x() + 14, box.y() + 32, box.width() - 28, 148)
        panel(p, scr, "#061208", "#102A14", 6, 2)
        owed = max(0, v["debt"] - v["bank"])
        lines = [(f"DEADLINE {v['deadline']}" + (f" OF {FINAL}" if not run.endless else " (ENDLESS)"), SCREEN),
                 (f"DEBT       {fmt(v['debt']):>9}", SCREEN), (f"DEPOSITED  {fmt(v['bank']):>9}", SCREEN),
                 (f"STILL OWED {fmt(owed):>9}" if owed else "DEBT COVERED", "#F2D27A" if owed else "#9AF2B0"),
                 (f"INTEREST   {run.interest_rate() * 100:>7.0f}% /RND", "#5AC27A")]
        for k, (s, col) in enumerate(lines):
            text(p, QRectF(scr.x() + 10, scr.y() + 8 + k * 27, scr.width() - 20, 24), s, 15, col,
                 Qt.AlignLeft | Qt.AlignVCenter, bold=True, shadow=False, family="Consolas")
        self._tip(scr, "The ATM", ["Only coins in the ATM count towards the debt - and they're safe from 666.",
                                   f"It pays {run.interest_rate() * 100:.0f}% interest at the start of every round.",
                                   "What's left after a deadline is paid stays in, still earning."])
        busy = self.anim is not None or run.stage in ("dead", "won", "phone")
        by = scr.bottom() + 12
        self._btn(p, QRectF(box.x() + 14, by, box.width() - 28, 32), "Deposit everything", "#2A6A3A", self._deposit_all,
                  not busy and run.pocket > 0)
        keep = run.spin_money()
        self._btn(p, QRectF(box.x() + 14, by + 40, box.width() - 28, 32),
                  f"Deposit, keep {fmt(keep)} for spins", "#2A5A6A", self._deposit_keep,
                  not busy and run.pocket > keep)
        self._tip(QRectF(box.x() + 14, by + 40, box.width() - 28, 32), "Keep spin money",
                  ["Deposits all but what the next round's seven spins will cost."])
        # the pocket, the tickets
        y = box.bottom() + 16
        pocket = QRectF(r.x(), y, r.width(), 64)
        panel(p, pocket, "#1C1612", "#5A4630", 8, 1.5)
        text(p, QRectF(pocket.x() + 12, pocket.y() + 4, pocket.width(), 20), "IN YOUR POCKET", 12, DIM, Qt.AlignLeft)
        text(p, QRectF(pocket.x() + 12, pocket.y() + 22, pocket.width() - 24, 38), f"{fmt(v['pocket'])} coins", 26,
             GOLD, Qt.AlignLeft | Qt.AlignVCenter)
        tk = QRectF(r.x(), y + 74, r.width(), 54)
        panel(p, tk, "#121C14", "#2E5A36", 8, 1.5)
        text(p, QRectF(tk.x() + 12, tk.y() + 4, tk.width(), 18), "CLOVER TICKETS", 12, DIM, Qt.AlignLeft)
        text(p, QRectF(tk.x() + 12, tk.y() + 20, tk.width() - 24, 30), f"☘ {v['tickets']}", 22, GREEN,
             Qt.AlignLeft | Qt.AlignVCenter, family=SYMBOL_FONT)
        self._tip(tk, "Clover Tickets", ["Spend them on charms. You get one with the three-spin package, two for every "
                                         "round you don't need when you pay a deadline early - and from some charms."])
        # the abilities from the phone
        ab = QRectF(r.x(), y + 140, r.width(), max(40, r.bottom() - y - 140))
        panel(p, ab, "#16120F", "#3A3028", 8, 1.5)
        text(p, QRectF(ab.x() + 12, ab.y() + 4, ab.width(), 18), "FROM THE PHONE", 12, DIM, Qt.AlignLeft)
        rows = int((ab.height() - 26) // 17)
        shown = run.abilities[-rows:] if rows > 0 else []
        for k, (kind, name) in enumerate(shown):
            text(p, QRectF(ab.x() + 14, ab.y() + 24 + k * 17, ab.width() - 20, 16), f"• {name}", 12,
                 {"holy": GOLD, "evil": "#E07060"}.get(kind, "#C8BEB2"), Qt.AlignLeft, bold=False)
        if not run.abilities:
            text(p, QRectF(ab.x() + 14, ab.y() + 24, ab.width() - 20, 16), "Nothing yet.", 12, "#6A6058", Qt.AlignLeft,
                 bold=False)

    # the charm machine
    def _draw_store(self, p, L):
        r = L["right"]
        run = self.run
        box = QRectF(r.x(), r.y(), r.width(), 330)
        g = QLinearGradient(box.topLeft(), box.bottomLeft())
        g.setColorAt(0, QColor("#1E3A2A"))
        g.setColorAt(1, QColor("#10201A"))
        p.setPen(QPen(QColor("#C9A040"), 2))
        p.setBrush(g)
        p.drawRoundedRect(box, 10, 10)
        text(p, QRectF(box.x(), box.y() + 6, box.width(), 22), "LUCKY CHARMS", 15, GOLD)
        busy = self.anim is not None or run.stage in ("dead", "won")
        cw, chh = (box.width() - 36) / 2, 118
        for i, key in enumerate(run.store):
            cell = QRectF(box.x() + 12 + (i % 2) * (cw + 12), box.y() + 36 + (i // 2) * (chh + 10), cw, chh)
            panel(p, cell, "#0C1610", "#2E5A36", 6, 1.5)
            if key is None:
                text(p, cell, "SOLD", 14, "#3A5A40")
                continue
            name, price, desc = CHARMS[key]
            paint_charm(p, QRectF(cell.center().x() - 24, cell.y() + 8, 48, 48), key)
            text(p, QRectF(cell.x() + 4, cell.y() + 58, cell.width() - 8, 20), name, 12, "#EDE6DA",
                 Qt.AlignCenter | Qt.TextWordWrap)
            ok = not busy and run.tickets >= price and len(run.charms) < run.slots
            self._btn(p, QRectF(cell.x() + 10, cell.bottom() - 32, cell.width() - 20, 26), f"☘ {price}",
                      "#2E7A3E" if ok else "#3A3430", lambda i=i: self._buy(i), not busy, 13)
            self._tip(cell, name, [desc, f"Costs {price} Clover Ticket{'s' if price > 1 else ''}."])
        self._btn(p, QRectF(box.x() + 12, box.bottom() - 42, box.width() - 24, 30),
                  f"New charms (☘ {run.reroll_cost})", "#5A4A1A", self._reroll, not busy and run.tickets >= run.reroll_cost,
                  13)
        # what you have
        y = box.bottom() + 14
        own = QRectF(r.x(), y, r.width(), r.bottom() - y)
        panel(p, own, "#16120F", "#3A3028", 8, 1.5)
        text(p, QRectF(own.x() + 12, own.y() + 4, own.width(), 18), f"YOUR CHARMS  {len(run.charms)}/{run.slots}", 12,
             DIM, Qt.AlignLeft)
        size = 54
        per = max(1, int((own.width() - 16) // (size + 8)))
        for i, key in enumerate(run.charms):
            cx = own.x() + 12 + (i % per) * (size + 8)
            cy = own.y() + 26 + (i // per) * (size + 8)
            tok = QRectF(cx, cy, size, size)
            if self.sold == i:
                p.setPen(QPen(QColor(GOLD), 2.5))
                p.setBrush(Qt.NoBrush)
                p.drawEllipse(tok.adjusted(-3, -3, 3, 3))
            paint_charm(p, tok, key, True)
            name, price, desc = CHARMS[key]
            self._tip(tok, name, [desc, f"Click to sell it for {price // 2} ticket{'s' if price // 2 != 1 else ''}."])
            if not busy:
                self.hits.append((tok, lambda i=i: self._pick_sell(i)))
        if self.sold is not None and self.sold < len(run.charms) and not busy:
            key = run.charms[self.sold]
            back = CHARMS[key][1] // 2
            self._btn(p, QRectF(own.x() + 12, own.bottom() - 40, own.width() - 24, 30),
                      f"Sell {CHARMS[key][0]} (+☘ {back})", "#7A3A2A", self._sell, True, 12)
        if not run.charms:
            text(p, QRectF(own.x() + 12, own.y() + 26, own.width() - 24, 40), "Buy charms with Clover Tickets.", 12,
                 "#6A6058", Qt.AlignLeft | Qt.TextWordWrap, bold=False)

    # what pays
    def _draw_table(self, p, L):
        r = L["bottom"]
        run = self.run
        if r.height() < 60:
            return
        panel(p, r, "#16120F", "#3A3028", 8, 1.5)
        g = run.growth() * run.payout_mult() * COIN
        n = len(SYMBOLS)
        sw = (r.width() - 20) / n
        for k, s in enumerate(SYMBOLS):
            cell = QRectF(r.x() + 10 + k * sw, r.y() + 6, sw, 36)
            paint_symbol(p, QRectF(cell.x() + 4, cell.y(), 34, 34), s)
            worth = max(1, round(run.value(s) * g))
            text(p, QRectF(cell.x() + 40, cell.y(), sw - 40, 34), fmt(worth), 14, GOLD, Qt.AlignLeft | Qt.AlignVCenter)
            self._tip(cell, SYMBOL_NAME[s], [f"Pays {fmt(worth)} coins in a pattern, times the pattern's multiplier.",
                                             f"Comes up {run.weight(s)} times in {sum(run.weight(x) for x in SYMBOLS)}."])
        keys = list(PATTERNS)
        pw = (r.width() - 20) / len(keys)
        y = r.y() + 48
        if y + 40 > r.bottom():
            return
        for k, key in enumerate(keys):
            cell = QRectF(r.x() + 10 + k * pw, y, pw, r.bottom() - y - 6)
            paint_shape(p, QRectF(cell.x() + 6, cell.y() + 2, pw - 12, min(26, (pw - 12) * 0.6)), key, GOLD)
            text(p, QRectF(cell.x(), cell.y() + 30, pw, 18), f"x{run.mult(key)}", 13, "#EDE6DA")
            self._tip(cell, PATTERNS[key][0], [f"Multiplier x{run.mult(key)}. Patterns stack: a column inside an "
                                               "Eye pays for both."])

    def _draw_trapdoor(self, p, L, open_):
        m = L["machine"]
        h = self.height()
        y = h * 0.8 + 8
        door = QRectF(m.center().x() - 120, y, 240, min(54, h - y - 6))
        if door.height() < 20:
            return
        p.setPen(QPen(QColor("#050403"), 2))
        p.setBrush(QColor("#000000"))
        p.drawRect(door)
        if open_ >= 1:
            return
        g = QLinearGradient(door.topLeft(), door.bottomLeft())
        g.setColorAt(0, QColor("#4A3420"))
        g.setColorAt(1, QColor("#2A1C10"))
        p.setBrush(g)
        half = door.width() / 2 * (1 - open_)
        for x0 in (door.x(), door.right() - half):
            p.drawRect(QRectF(x0, door.y(), half, door.height()))
        p.setPen(QPen(QColor(0, 0, 0, 90), 1.5))
        for k in range(1, 6):
            yy = door.y() + k * door.height() / 6
            p.drawLine(QPointF(door.x(), yy), QPointF(door.x() + half, yy))
            p.drawLine(QPointF(door.right() - half, yy), QPointF(door.right(), yy))

    # buying spins
    def _draw_packages(self, p, L):
        run = self.run
        reels = L["reels"]
        box = QRectF(reels.center().x() - 250, reels.center().y() - 120, 500, 240)
        p.fillRect(reels.adjusted(-10, -10, 10, 10), QColor(0, 0, 0, 150))
        panel(p, box, "#1A0E0A", GOLD, 10, 2.5)
        text(p, QRectF(box.x(), box.y() + 10, box.width(), 28), f"Round {run.round} of {ROUNDS}: buy your spins", 19,
             GOLD)
        owed = max(0, run.debt - run.bank)
        sub = (f"Still owed: {fmt(owed)}  -  in your pocket: {fmt(run.pocket)}" if owed
               else "The debt is covered - you can pay it now.")
        text(p, QRectF(box.x(), box.y() + 40, box.width(), 20), sub, 13, "#D8CBB8", bold=False)
        opts = run.packages()
        y = box.y() + 72
        for i, (label, n, t, cost) in enumerate(opts):
            ok = cost <= run.pocket
            extra = f" + ☘{t}" if t else ""
            self._btn(p, QRectF(box.x() + 30, y, box.width() - 60, 40),
                      f"{label}  ({n} spins{extra})  -  {fmt(cost)} coins" if cost else f"{label}",
                      "#8A2A1A" if i == 0 else "#2A6A3A", lambda i=i: self._choose(i), ok, 14)
            y += 48
        if run.can_pay_early():
            unused = ROUNDS - run.round + 1
            self._btn(p, QRectF(box.x() + 30, y, box.width() - 60, 40),
                      f"Pay the debt now (+☘ {2 * unused} for the rounds you don't need)", "#B8862E", self._pay_early,
                      True, 14)

    # the phone
    def _draw_phone(self, p, L):
        run = self.run
        self.hits, self.tips = [], []                    # (nothing underneath while this is up)
        p.fillRect(self.rect(), QColor(0, 0, 0, 150))
        cx, cy = self.width() / 2, self.height() / 2
        if not self.answered:
            box = QRectF(cx - 200, cy - 130, 400, 260)
            panel(p, box, "#140C0A", "#8A2A1A", 12, 2.5)
            shake = math.sin(self.t * 60) * 4 if (self.ring_at - self.t) > 1.3 else 0
            ph = QRectF(cx - 60 + shake, box.y() + 30, 120, 90)
            p.setPen(QPen(QColor("#000000"), 2))
            p.setBrush(QColor("#1A1A1A"))
            p.drawRoundedRect(QRectF(ph.x(), ph.y() + 30, ph.width(), 60), 10, 10)
            p.setBrush(QColor("#2A2A2A"))
            p.drawRoundedRect(QRectF(ph.x() - 10, ph.y() + 10, ph.width() + 20, 24), 12, 12)
            p.setBrush(QColor("#C9A040"))
            p.drawEllipse(QPointF(ph.center().x(), ph.y() + 62), 18, 18)
            text(p, QRectF(box.x(), box.y() + 128, box.width(), 30), "The phone is ringing.", 20, "#EDE6DA")
            self._btn(p, QRectF(cx - 90, box.bottom() - 70, 180, 44), "Pick up", "#8A2A1A", self._pick_up, True, 16)
            return
        offers = run.offers
        n = len(offers)
        cw, chh = 230, 250
        total = n * cw + (n - 1) * 18
        text(p, QRectF(0, cy - chh / 2 - 70, self.width(), 30), "\"You paid. Here's something for the next one.\"", 18,
             "#D8CBB8", bold=False)
        text(p, QRectF(0, cy - chh / 2 - 40, self.width(), 24), "Choose one.", 14, DIM, bold=False)
        for i, o in enumerate(offers):
            card = QRectF(cx - total / 2 + i * (cw + 18), cy - chh / 2, cw, chh)
            col = KIND_COLOUR[o["kind"]]
            hover = card.contains(self.mouse)
            panel(p, card.translated(0, -4) if hover else card, "#140E0C", col, 10, 3 if hover else 2)
            card = card.translated(0, -4) if hover else card
            label = {"normal": "", "holy": "HOLY", "evil": "EVIL"}[o["kind"]]
            if label:
                text(p, QRectF(card.x(), card.y() + 10, card.width(), 18), label, 13, col)
            text(p, QRectF(card.x() + 10, card.y() + 34, card.width() - 20, 50), o["name"], 18, "#EDE6DA",
                 Qt.AlignCenter | Qt.TextWordWrap)
            text(p, QRectF(card.x() + 14, card.y() + 90, card.width() - 28, 100), o["desc"], 14, "#C8BEB2",
                 Qt.AlignHCenter | Qt.AlignTop | Qt.TextWordWrap, bold=False)
            self._btn(p, QRectF(card.x() + 30, card.bottom() - 52, card.width() - 60, 38), "Take it", col,
                      lambda i=i: self._answer(i), True, 14)
        self._btn(p, QRectF(cx - 80, cy + chh / 2 + 24, 160, 34), "Hang up", "#3A3430", self._hang_up, True, 13)

    def _draw_won(self, p, L):
        run = self.run
        self.hits, self.tips = [], []                    # (nothing underneath while this is up)
        p.fillRect(self.rect(), QColor(0, 0, 0, 170))
        cx, cy = self.width() / 2, self.height() / 2
        box = QRectF(cx - 260, cy - 170, 520, 340)
        panel(p, box, "#1A140A", GOLD, 12, 3)
        text(p, QRectF(box.x(), box.y() + 20, box.width(), 40), "You climbed out of the pit.", 26, GOLD)
        lines = [f"Ten deadlines paid.", f"Spins pulled: {run.spins_pulled}   Best spin: {fmt(run.best_spin)}",
                 f"Coins won: {fmt(run.total_won)}   Times 666 came up: {run.sixes}"]
        for k, s in enumerate(lines):
            text(p, QRectF(box.x(), box.y() + 80 + k * 28, box.width(), 24), s, 15, "#D8CBB8", bold=False)
        self._btn(p, QRectF(cx - 200, box.bottom() - 70, 190, 44), "Stay down here", "#5A2A1A", self._endless, True, 15)
        self._btn(p, QRectF(cx + 10, box.bottom() - 70, 190, 44), "New run", "#2A6A3A", self._new_run, True, 15)

    def _draw_fall(self, p):
        """The trapdoor opens, the room goes up and away, and it's dark."""
        k = (self.t - self.fall) / 2.4
        L = self._layout()
        p.fillRect(self.rect(), QColor("#000000"))      # (what's below the room)
        if k < 1:
            open_ = min(1.0, k * 5)
            p.save()
            drop = max(0.0, k - 0.25) / 0.75
            p.translate(0, -drop * drop * self.height() * 1.2)
            self._background(p)
            self._draw_machine(p, L)
            self._draw_atm(p, L)
            self._draw_store(p, L)
            self._draw_table(p, L)
            self._draw_trapdoor(p, L, open_)
            p.restore()
            self.hits, self.tips = [], []
            p.fillRect(self.rect(), QColor(0, 0, 0, int(255 * min(1.0, drop * 1.3))))
            return
        p.fillRect(self.rect(), QColor("#000000"))
        run = self.run
        cx, cy = self.width() / 2, self.height() / 2
        fade = min(1.0, (k - 1) * 2)
        p.setOpacity(fade)
        text(p, QRectF(0, cy - 150, self.width(), 50), "The trapdoor opened.", 30, "#C04030")
        lines = [f"Deadline {run.deadline}: the ATM wanted {fmt(run.debt)} and had {fmt(run.bank)}.",
                 f"Deadlines paid: {run.deadline - 1}   Spins pulled: {run.spins_pulled}   Best spin: {fmt(run.best_spin)}",
                 f"Best ever: deadline {self.stats.get('best_deadline', 0)} paid   Escapes: {self.stats.get('escapes', 0)}"]
        for k2, s in enumerate(lines):
            text(p, QRectF(0, cy - 80 + k2 * 28, self.width(), 24), s, 15, "#9A8F84", bold=False)
        self._btn(p, QRectF(cx - 200, cy + 40, 190, 44), "Try again", "#8A2A1A", self._new_run, True, 15)
        self._btn(p, QRectF(cx + 10, cy + 40, 190, 44), "Title", "#3A3430", self._to_title, True, 15)
        p.setOpacity(1.0)

    def _draw_title(self, p):
        w, h = self.width(), self.height()
        box = QRectF(w / 2 - 330, 70, 660, 120)
        panel(p, box, "#1A0A0A", "#C9A040", 14, 3)
        for k in range(22):
            x = box.x() + 16 + k * (box.width() - 32) / 21
            on = (int(self.t * 5) + k) % 3 == 0
            p.setPen(Qt.NoPen)
            p.setBrush(QColor("#FFE9A0") if on else QColor("#5A4A2A"))
            p.drawEllipse(QPointF(x, box.y() + 9), 4, 4)
            p.drawEllipse(QPointF(x, box.bottom() - 9), 4, 4)
        text(p, box, "C L A U D E P I T", 54, GOLD)
        syms = QRectF(w / 2 - 280, 214, 560, 80)
        for k, s in enumerate(SYMBOLS):
            paint_symbol(p, QRectF(syms.x() + k * 80, syms.y(), 72, 72), s)
        about = ("You wake at the bottom of a pit with a slot machine, an ATM and a debt. Buy spins, pull the lever, "
                 "and put what you win in the ATM before each deadline - or the trapdoor opens. 6-6-6 takes your "
                 "pocket. Lucky charms cost Clover Tickets; the phone rings when you pay. Pay ten deadlines to "
                 "climb out.")
        text(p, QRectF(w / 2 - 330, 310, 660, 110), about, 15, "#C8BEB2", Qt.AlignHCenter | Qt.AlignTop | Qt.TextWordWrap,
             bold=False)
        y = 440
        run = self.run
        if run and run.stage not in ("dead",):
            self._btn(p, QRectF(w / 2 - 150, y, 300, 48), f"Continue (deadline {run.deadline})", "#8A2A1A",
                      self._continue, True, 17)
            y += 60
        self._btn(p, QRectF(w / 2 - 150, y, 300, 48), "New run", "#2A6A3A", self._new_run, True, 17)
        s = self.stats
        if s.get("runs"):
            text(p, QRectF(0, y + 70, w, 22), f"Runs: {s.get('runs', 0)}   Best: deadline {s.get('best_deadline', 0)} "
                 f"paid   Escapes: {s.get('escapes', 0)}   Best spin: {fmt(s.get('best_spin', 0))}", 13, DIM, bold=False)

    def _sound_buttons(self, p):
        w = self.width()
        self._btn(p, QRectF(w - 214, 10, 100, 28), "Music: " + ("On" if self.music_on else "Off"), "#3A3430",
                  self._toggle_music, True, 12)
        self._btn(p, QRectF(w - 108, 10, 96, 28), "Sound: " + ("On" if self.sfx_on else "Off"), "#3A3430",
                  self._toggle_sfx, True, 12)
        if self.screen == "game" and self.fall is None:
            self._btn(p, QRectF(12, 10, 90, 28), "Title", "#3A3430", self._to_title, self.anim is None, 12)

    def _draw_toast(self, p):
        if not self.toast:
            return
        msg = self.toast[0]
        p.setFont(font(15))
        width = min(self.width() - 80, p.fontMetrics().horizontalAdvance(msg) + 40)
        box = QRectF((self.width() - width) / 2, self.height() - 64, width, 40)
        panel(p, box, "#1A120E", "#8A6A3A", 8, 1.5)
        text(p, box, msg, 15, "#EDE6DA", Qt.AlignCenter | Qt.TextWordWrap)

    def _draw_tip(self, p):
        for rect, title, lines in reversed(self.tips):
            if rect.contains(self.mouse):
                break
        else:
            return
        width = 300
        p.setFont(font(13, False))
        fm = p.fontMetrics()
        body = [fm.boundingRect(QRectF(0, 0, width - 20, 400).toRect(), Qt.TextWordWrap, ln).height() for ln in lines]
        height = 34 + sum(body) + 4 * len(lines)
        x = min(self.mouse.x() + 16, self.width() - width - 8)
        y = min(self.mouse.y() + 16, self.height() - height - 8)
        box = QRectF(x, y, width, height)
        panel(p, box, "#0E0B09", "#8A6A3A", 6, 1.5)
        text(p, QRectF(x + 10, y + 6, width - 20, 22), title, 14, GOLD, Qt.AlignLeft)
        yy = y + 30
        for ln, bh in zip(lines, body):
            text(p, QRectF(x + 10, yy, width - 20, bh), ln, 13, "#D8CBB8", Qt.AlignLeft | Qt.TextWordWrap, bold=False,
                 shadow=False)
            yy += bh + 4

    # ---- actions ----
    def _new_run(self):
        self.run = Run()
        self.screen = "game"
        self.fall = None
        self.anim = self.view = None
        self.auto = False
        self.recorded = False
        self.answered = False
        self.sold = None
        self.say(f"Deadline 1: {fmt(self.run.debt)} coins, in {ROUNDS} rounds. Buy your spins.", 4)
        self._save()

    def _continue(self):
        self.screen = "game"
        self.fall = None
        if self.run and self.run.stage == "phone":
            self.answered = False
            self.ring_at = self.t + 0.5

    def _to_title(self):
        if self.anim:
            return
        self._save()
        self.screen = "title"
        self.auto = False
        if self.fall is not None:
            self.fall = None
            self.run = None

    def _endless(self):
        self.run.keep_going()
        self.say(f"Deadline {self.run.deadline}: {fmt(self.run.debt)} coins. The pit goes on.", 4)
        self._save()

    def _toggle_music(self):
        self.music_on = not self.music_on
        self.audio.music_on = self.music_on
        self._save_settings()

    def _toggle_sfx(self):
        self.sfx_on = not self.sfx_on
        self.audio.sfx_on = self.sfx_on
        self._save_settings()

    def _cycle_speed(self):
        self.speed = SPEEDS[(SPEEDS.index(self.speed) + 1) % len(SPEEDS)]
        self._save_settings()

    def _toggle_auto(self):
        self.auto = not self.auto and self.run.stage == "spin"

    def _choose(self, i):
        opts = self.run.packages()
        if self.run.choose(i):
            self.sfx("package")
            if opts[i][2]:
                self.sfx("ticket")
            self._save()
        else:
            self.sfx("nope")

    def _pay_early(self):
        out = self.run.pay_early()
        if out:
            self._deadline_done(out)
            self._save()

    def _deposit_all(self):
        got = self.run.deposit()
        if got:
            self.sfx("deposit")
            self._save()

    def _deposit_keep(self):
        run = self.run
        got = run.deposit(run.pocket - run.spin_money())
        if got:
            self.sfx("deposit")
            self._save()

    def _buy(self, i):
        res = self.run.buy(i)
        if res == "ok":
            self.sfx("buy")
            self._save()
        else:
            self.sfx("nope")
            self.say({"tickets": "Not enough Clover Tickets.", "full": "No room for another charm - sell one first."}
                     .get(res, ""))

    def _reroll(self):
        if self.run.reroll():
            self.sfx("reroll")
            self._save()

    def _pick_sell(self, i):
        self.sold = None if self.sold == i else i

    def _sell(self):
        if self.sold is None:
            return
        self.run.sell(self.sold)
        self.sold = None
        self.sfx("sell")
        self._save()

    def _pick_up(self):
        self.answered = True
        self.sfx("pickup")

    def _answer(self, i):
        kind = self.run.offers[i]["kind"] if i < len(self.run.offers) else "normal"
        if self.run.answer(i):
            self.sfx({"holy": "holy", "evil": "evil"}.get(kind, "ability"))
            self.sfx("hangup")
            self._after_call()

    def _hang_up(self):
        self.run.hang_up()
        self.sfx("hangup")
        self._after_call()

    def _after_call(self):
        run = self.run
        self.answered = False
        if run.stage == "won":
            self.sfx("escape")
            self._record()
        else:
            self.say(f"Deadline {run.deadline}: {fmt(run.debt)} coins, in {ROUNDS} rounds.", 4)
        self._save()

    # ---- input ----
    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Space:
            if self.screen == "game" and self.run and self.run.stage == "spin":
                self._pull()
            return
        if e.key() == Qt.Key_D and self.screen == "game" and self.run and not self.anim:
            self._deposit_all()
            return
        super().keyPressEvent(e)

    def mouseMoveEvent(self, e):
        self.mouse = e.position()

    def mousePressEvent(self, e):
        self.mouse = e.position()
        if e.button() == Qt.RightButton:
            self.sold = None
            return
        if e.button() != Qt.LeftButton:
            return
        for rect, action in reversed(self.hits):
            if rect.contains(e.position()):
                self.sfx("click")
                action()
                return

    def closeEvent(self, event):
        if self.anim:
            self.anim = None
            self.view = None
        self._save()
        self.timer.stop()
        self.audio.stop()
        event.accept()


def pit_icon():
    pm = QPixmap(32, 32)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(QPen(QColor("#2A0A0A"), 1))
    p.setBrush(QColor("#8A2020"))
    p.drawRoundedRect(QRectF(3, 5, 22, 24), 4, 4)
    p.setBrush(QColor("#F4ECDD"))
    p.drawRect(QRectF(6, 11, 16, 11))
    _symbol(p, QRectF(5, 10, 18, 13), "clover")
    p.setPen(QPen(QColor("#888888"), 2))
    p.drawLine(QPointF(26, 22), QPointF(28, 8))
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#D02020"))
    p.drawEllipse(QPointF(28, 7), 3, 3)
    p.end()
    return QIcon(pm)


_open = {}


def launch(desktop):
    win = _open.get("win")
    if win is None or not isValid(win):
        body = Pit(desktop)
        win = host.window(desktop, TITLE, body, pit_icon(), (1240, 800))
        body.frame = win
        _open["win"] = win
    desktop.open_window(win)
    return win


def shutdown():
    win = _open.get("win")
    if win is not None and isValid(win):
        win.content.close()
