"""ClaudeQuest - a wolf pack survival game for ClaudeXP's Games folder (in the spirit of WolfQuest).

Lead a wolf pack through the seasons in a valley of meadows, forests, a river and mountains: hunt elk, deer, hares
(and bison, if you dare) with your packmates, raise the spring pups by carrying food back to the den, mark your
territory, stand up to rival packs, bears and cougars, and get through winter's deep snow and blizzards.

Keys: WASD/arrows move, Shift run, C sneak, Space bite, F (hold) eat at a kill, E scent view, M scent mark,
H howl (gathers the pack), R (hold) rest, Tab names, Esc pause. Saved in data/claudequest/save.json.
"""
import json
import math
import random
import time

from PySide6.QtCore import QPointF, QRect, QRectF, Qt, QTimer
from PySide6.QtGui import (QBrush, QColor, QFont, QFontMetrics, QIcon, QLinearGradient, QPainter, QPen, QPixmap,
                           QPolygonF, QRadialGradient)
from PySide6.QtWidgets import QLineEdit, QWidget
from shiboken6 import isValid

from claudecore import host
from . import art
from . import world as W

SAVE = host.saves("claudequest") / "save.json"         # shared by every era
CHUNK = 8                       # tiles per terrain chunk
GOLD = QColor("#F2C12E")


def quest_icon():
    ic = QIcon()
    for sz in (16, 32, 48):
        ic.addPixmap(art.icon_pixmap(sz))
    return ic


def _font(size, bold=False, family="Georgia"):
    f = QFont(family, size)
    f.setBold(bold)
    return f


class Game(QWidget):
    def __init__(self, desktop):
        super().__init__()
        self.desktop = desktop
        self.frame = None
        self.state = "title"
        self.world = None
        self.keys = set()
        self.pressed = set()
        self.scent = False
        self.show_names = False
        self.last = time.monotonic()
        self.buttons = []
        self.title_pm = QPixmap(str(art.TITLE)) if art.TITLE.exists() else QPixmap()
        self.tiles = {}
        self.chunks = {}
        self.decor_pm = {}
        self.minimap = None
        self.snow = [(random.random(), random.random(), random.random()) for _ in range(160)]
        self.coat = "gray"
        self.sex = "male"
        self.help = False
        self.saved_day = -1
        self.name_edit = QLineEdit(self)
        self.name_edit.setMaxLength(14)
        self.name_edit.setText(self._default_name())
        self.name_edit.setStyleSheet("QLineEdit { background: rgba(255,255,255,230); border: 2px solid #8A6A20; "
                                     "border-radius: 4px; font-family: Georgia; font-size: 16px; padding: 3px 6px; }")
        self.name_edit.hide()
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMouseTracking(True)
        self.setMinimumSize(800, 560)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(16)

    def _default_name(self):
        try:
            return host.user_name()[:14] or "Shadow"
        except Exception:
            return "Shadow"

    # ---- the loop -------------------------------------------------------------------------------------------
    def _tick(self):
        now = time.monotonic()
        dt = min(0.05, now - self.last)
        self.last = now
        if self.state == "play" and self.world is not None and not self.help:
            k = self.keys
            dx = (1 if (Qt.Key_D in k or Qt.Key_Right in k) else 0) - (1 if (Qt.Key_A in k or Qt.Key_Left in k) else 0)
            dy = (1 if (Qt.Key_S in k or Qt.Key_Down in k) else 0) - (1 if (Qt.Key_W in k or Qt.Key_Up in k) else 0)
            ctl = {"move": (dx, dy), "run": Qt.Key_Shift in k, "sneak": Qt.Key_C in k,
                   "bite": Qt.Key_Space in self.pressed or Qt.Key_Space in k,
                   "eat": Qt.Key_F in k, "mark": Qt.Key_M in self.pressed, "howl": Qt.Key_H in k,
                   "rest": Qt.Key_R in k}
            self.pressed.clear()
            self.world.update(dt, ctl)
            if self.world.over:
                self.state = "over"
                self._delete_save()
            elif self.world.day != self.saved_day:
                self.saved_day = self.world.day
                self.save()
        self.update()

    # ---- saving ---------------------------------------------------------------------------------------------
    def save(self):
        if self.world is None or self.world.over:
            return
        try:
            SAVE.parent.mkdir(parents=True, exist_ok=True)
            tmp = SAVE.with_suffix(".tmp")
            tmp.write_text(json.dumps(self.world.to_json()), encoding="utf-8")
            tmp.replace(SAVE)
        except OSError:
            pass

    def _delete_save(self):
        try:
            SAVE.unlink()
        except OSError:
            pass

    def _continue(self):
        try:
            self.world = W.World.from_json(json.loads(SAVE.read_text(encoding="utf-8")))
        except Exception:
            self._delete_save()
            return
        self._enter_play()

    def _begin(self):
        name = self.name_edit.text().strip() or "Shadow"
        self.name_edit.hide()
        self.world = W.World(random.randint(1, 10 ** 6), (name, self.coat, self.sex))
        self._enter_play()

    def _enter_play(self):
        self.state = "play"
        self.chunks.clear()
        self.minimap = None
        self.saved_day = self.world.day
        self.save()
        self.setFocus()

    def shutdown(self):
        if self.state in ("play", "pause"):
            self.save()
        self.timer.stop()

    # ---- input -------------------------------------------------------------------------------------------------
    def keyPressEvent(self, e):
        k = e.key()
        if self.state == "create":
            if k in (Qt.Key_Return, Qt.Key_Enter):
                self._begin()
            return
        if self.state == "play":
            if self.world.prompt and k in (Qt.Key_Y, Qt.Key_N):
                self.world.answer(k == Qt.Key_Y)
                return
            if k == Qt.Key_Escape:
                if self.help:
                    self.help = False
                else:
                    self.state = "pause"
                    self.save()
                return
            if k == Qt.Key_E and not e.isAutoRepeat():
                self.scent = not self.scent
            if k == Qt.Key_Tab:
                self.show_names = not self.show_names
            if k == Qt.Key_F1:
                self.help = not self.help
            if not e.isAutoRepeat():
                self.pressed.add(k)
            self.keys.add(k)
            return
        if self.state == "pause" and k == Qt.Key_Escape:
            self.state = "play"
            return
        if self.state == "title" and self.help and k == Qt.Key_Escape:
            self.help = False

    def keyReleaseEvent(self, e):
        if not e.isAutoRepeat():
            self.keys.discard(e.key())

    def focusOutEvent(self, e):
        self.keys.clear()
        super().focusOutEvent(e)

    def mousePressEvent(self, e):
        pos = e.position()
        for rect, action in self.buttons:
            if rect.contains(pos):
                action()
                return
        if self.state == "create":
            for rect, coat in getattr(self, "coat_rects", []):
                if rect.contains(pos):
                    self.coat = coat
            for rect, sex in getattr(self, "sex_rects", []):
                if rect.contains(pos):
                    self.sex = sex
        self.setFocus()

    def mouseMoveEvent(self, e):
        self.mouse = e.position()

    # ---- painting --------------------------------------------------------------------------------------------
    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        self.buttons = []
        if self.state in ("play", "pause", "over") and self.world is not None:
            self._draw_world(p)
            self._draw_hud(p)
            if self.help:
                self._draw_help(p)
            if self.state == "pause":
                self._draw_pause(p)
            if self.state == "over":
                self._draw_over(p)
        elif self.state == "create":
            self._draw_create(p)
        else:
            self._draw_title(p)
        p.end()

    def _button(self, p, rect, text, action, small=False):
        hot = rect.contains(getattr(self, "mouse", QPointF(-1, -1)))
        g = QLinearGradient(rect.topLeft(), rect.bottomLeft())
        g.setColorAt(0, QColor("#FFE27A") if hot else QColor("#F2C12E"))
        g.setColorAt(1, QColor("#C8861A") if hot else QColor("#A8680E"))
        p.setPen(QPen(QColor("#3A2408"), 2))
        p.setBrush(QBrush(g))
        p.drawRoundedRect(rect, 10, 10)
        p.setFont(_font(12 if small else 15, True))
        p.setPen(QColor("#3A2408"))
        p.drawText(rect, Qt.AlignCenter, text)
        self.buttons.append((rect, action))

    # title ------------------------------------------------------------------------------------------------------
    def _draw_title(self, p):
        w, h = self.width(), self.height()
        p.fillRect(self.rect(), QColor("#0A0E18"))
        strip = 96
        if not self.title_pm.isNull():
            pm = self.title_pm.scaled(w, h - strip, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            p.drawPixmap((w - pm.width()) // 2, 0, pm)
        else:
            p.setFont(_font(48, True))
            p.setPen(GOLD)
            p.drawText(QRect(0, 0, w, h - strip), Qt.AlignCenter, "ClaudeQuest")
        labels = []
        if SAVE.exists():
            labels.append(("Continue", self._continue))
        labels += [("New Pack", self._to_create), ("How to Play", self._toggle_help),
                   ("Quit", lambda: self.frame.request_close() if self.frame else None)]
        bw, gap = 170, 14
        x0 = (w - (len(labels) * bw + (len(labels) - 1) * gap)) // 2
        for i, (text, act) in enumerate(labels):
            self._button(p, QRectF(x0 + i * (bw + gap), h - strip + 24, bw, 46), text, act)
        if self.help:
            self._draw_help(p)

    def _toggle_help(self):
        self.help = not self.help

    def _to_create(self):
        self.state = "create"
        self.help = False
        self.name_edit.show()
        self.name_edit.setFocus()
        self.name_edit.selectAll()

    # creating your wolf ---------------------------------------------------------------------------------------------
    def _draw_create(self, p):
        w, h = self.width(), self.height()
        g = QLinearGradient(0, 0, 0, h)
        g.setColorAt(0, QColor("#3A6AA8"))
        g.setColorAt(0.55, QColor("#9AC0E0"))
        g.setColorAt(0.56, QColor("#A89A58"))
        g.setColorAt(1, QColor("#6A7A38"))
        p.fillRect(self.rect(), QBrush(g))
        p.setFont(_font(30, True))
        p.setPen(QColor("#3A2408"))
        p.drawText(QRect(2, 22, w, 50), Qt.AlignHCenter, "Your Wolf")
        p.setPen(GOLD)
        p.drawText(QRect(0, 20, w, 50), Qt.AlignHCenter, "Your Wolf")
        p.setFont(_font(12))
        p.setPen(QColor("#10203A"))
        p.drawText(QRect(0, 80, w, 20), Qt.AlignHCenter, "Name:")
        self.name_edit.setGeometry(w // 2 - 120, 102, 240, 34)
        # the coats
        coats = list(art.COATS)
        cw = 118
        x0 = (w - len(coats) * cw) // 2
        self.coat_rects = []
        for i, coat in enumerate(coats):
            r = QRectF(x0 + i * cw + 4, 160, cw - 8, 120)
            sel = coat == self.coat
            p.setPen(QPen(GOLD if sel else QColor(255, 255, 255, 90), 3 if sel else 1))
            p.setBrush(QColor(255, 255, 255, 60 if sel else 25))
            p.drawRoundedRect(r, 10, 10)
            p.save()
            p.translate(r.center().x() - 4, r.bottom() - 26)
            art.draw_wolf(p, coat, 1.15, "stand", time.monotonic() * 2 if sel else 0)
            p.restore()
            p.setFont(_font(10, True))
            p.setPen(QColor("#10203A"))
            p.drawText(QRectF(r.x(), r.bottom() - 22, r.width(), 20), Qt.AlignCenter, coat.title())
            self.coat_rects.append((r, coat))
        self.sex_rects = []
        for i, sex in enumerate(("male", "female")):
            r = QRectF(w / 2 - 130 + i * 140, 300, 120, 34)
            sel = sex == self.sex
            p.setPen(QPen(GOLD if sel else QColor(255, 255, 255, 120), 2))
            p.setBrush(QColor(0, 0, 0, 90 if sel else 40))
            p.drawRoundedRect(r, 8, 8)
            p.setPen(QColor("white"))
            p.setFont(_font(12, True))
            p.drawText(r, Qt.AlignCenter, sex.title())
            self.sex_rects.append((r, sex))
        p.save()
        p.translate(w / 2, 470)
        art.draw_wolf(p, self.coat, 2.2, "trot", time.monotonic() * 6)
        p.restore()
        p.setFont(_font(11))
        p.setPen(QColor("#10200A"))
        p.drawText(QRect(0, 500, w, 40), Qt.AlignHCenter | Qt.TextWordWrap,
                   "You'll lead the pack with your mate and two packmates. Pups are due this spring.")
        self._button(p, QRectF(w / 2 - 190, h - 76, 170, 46), "Back", self._back_to_title)
        self._button(p, QRectF(w / 2 + 20, h - 76, 170, 46), "Begin", self._begin)

    def _back_to_title(self):
        self.name_edit.hide()
        self.state = "title"

    # the world ---------------------------------------------------------------------------------------------------
    def _camera(self):
        me = self.world.player
        cx, cy = (me.x, me.y) if me is not None else self.world.map.den
        w, h = self.width(), self.height()
        cx = min(W.WORLD - w / 2, max(w / 2, cx))
        cy = min(W.WORLD - h / 2, max(h / 2, cy))
        return cx - w / 2, cy - h / 2

    def _tile(self, name, season, v):
        key = (name, season, v)
        if key not in self.tiles:
            self.tiles[key] = art.tile_pixmap(name, season, v)
        return self.tiles[key]

    def _chunk(self, cx, cy, season):
        key = (cx, cy, season)
        pm = self.chunks.get(key)
        if pm is None:
            size = CHUNK * W.TILE
            pm = QPixmap(size, size)
            pm.fill(QColor("#556B2F"))
            q = QPainter(pm)
            m = self.world.map
            for ty in range(CHUNK):
                for tx in range(CHUNK):
                    gx, gy = cx * CHUNK + tx, cy * CHUNK + ty
                    if gx < W.MAP_TILES and gy < W.MAP_TILES:
                        q.drawPixmap(tx * W.TILE, ty * W.TILE, self._tile(m.tiles[gy][gx], season, (gx * 7 + gy * 13) % 3))
            q.end()
            if len(self.chunks) > 70:
                self.chunks.pop(next(iter(self.chunks)))
            self.chunks[key] = pm
        return pm

    def _decor(self, kind, season, v):
        key = (kind, season, v)
        if key not in self.decor_pm:
            self.decor_pm[key] = art.decor_pixmap(kind, season, v)
        return self.decor_pm[key]

    def _draw_world(self, p):
        wd = self.world
        season = wd.season
        winter = season == "winter"
        ox, oy = self._camera()
        w, h = self.width(), self.height()
        size = CHUNK * W.TILE
        for cy in range(int(oy // size), int((oy + h) // size) + 1):
            for cx in range(int(ox // size), int((ox + w) // size) + 1):
                if 0 <= cx * CHUNK < W.MAP_TILES and 0 <= cy * CHUNK < W.MAP_TILES:
                    p.drawPixmap(int(cx * size - ox), int(cy * size - oy), self._chunk(cx, cy, season))
        self._water_shimmer(p, ox, oy, winter)
        # everything standing on the ground, back to front
        items = []
        t0x, t0y = int(ox // W.TILE) - 2, int(oy // W.TILE) - 1
        t1x, t1y = int((ox + w) // W.TILE) + 2, int((oy + h) // W.TILE) + 4
        for ty in range(t0y, t1y):
            for tx in range(t0x, t1x):
                for d in wd.map.grid.get((tx, ty), ()):
                    items.append((d[2], 0, d))
        for m in wd.markers:
            items.append((m.y - 1, 1, m))
        for c in wd.carcasses:
            items.append((c.y, 2, c))
        live = [x for x in wd.prey + wd.beasts if not x.dead]
        wolves = [x for x in wd.pack if not x.dead]
        for rp in wd.rivals:
            wolves += [x for x in rp.wolves if not x.dead]
        for c in live + wolves:
            if ox - 80 < c.x < ox + w + 80 and oy - 60 < c.y < oy + h + 100:
                items.append((c.y, 3, c))
        items.sort(key=lambda it: (it[0], it[1]))
        for y, kind, thing in items:
            if kind == 0:
                k, x, yy, _r = thing
                pm, anchor = self._decor(k, season, int(x * 7 + yy) % 4)
                p.drawPixmap(QPointF(x - ox - anchor.x(), yy - oy - anchor.y()), pm)
            elif kind == 1:
                pm, anchor = self._decor("marker", season, 0)
                p.setOpacity(0.35 + 0.65 * thing.strength)
                p.drawPixmap(QPointF(thing.x - ox - anchor.x(), thing.y - oy - anchor.y()), pm)
                p.setOpacity(1.0)
            elif kind == 2:
                p.save()
                p.translate(thing.x - ox, thing.y - oy)
                if thing.kind == "wolf":
                    art.draw_wolf(p, "gray", 1.0, "dead")
                else:
                    art.draw_carcass(p, thing.kind, thing.meat / max(1, thing.maxmeat), winter)
                p.restore()
            else:
                self._draw_creature(p, thing, ox, oy, winter)
        self._weather(p, wd, winter)
        if self.scent:
            self._draw_scent(p, ox, oy)

    def _water_shimmer(self, p, ox, oy, winter):
        if winter:
            return
        t = time.monotonic()
        p.setPen(QPen(QColor(255, 255, 255, 60), 1))
        m = self.world.map
        for ty in range(int(oy // W.TILE), int((oy + self.height()) // W.TILE) + 1):
            for tx in range(int(ox // W.TILE), int((ox + self.width()) // W.TILE) + 1):
                if 0 <= tx < W.MAP_TILES and 0 <= ty < W.MAP_TILES and m.tiles[ty][tx] == "water":
                    k = (t * 9 + tx * 7 + ty * 3) % 30
                    x, y = tx * W.TILE - ox + k, ty * W.TILE - oy + (tx * 13 + ty * 7) % 34
                    p.drawLine(QPointF(x, y), QPointF(x + 7, y))

    def _draw_creature(self, p, c, ox, oy, winter):
        wd = self.world
        p.save()
        p.translate(c.x - ox, c.y - oy)
        if c.facing < 0:
            p.scale(-1, 1)
        if isinstance(c, W.Wolf):
            s = 0.55 + 0.45 * min(1.0, c.age / 300) if c.pup else 1.0
            art.draw_wolf(p, c.coat, s, c.pose, c.phase, hurt=c.hurt_t > 0 or c.hp < 35)
        elif isinstance(c, W.Prey):
            art.draw_animal(p, c.kind, c.phase, c.moving, 1.0, bull=c.bull, calf=c.calf, winter=winter)
        else:
            art.draw_animal(p, c.kind, c.phase, c.moving, 1.0)
        p.restore()
        if isinstance(c, W.Wolf):
            x, y = c.x - ox, c.y - oy
            if c is wd.player:
                bob = math.sin(time.monotonic() * 4) * 2
                p.setPen(QPen(QColor("#3A2408"), 1))
                p.setBrush(GOLD)
                p.drawPolygon(QPolygonF([QPointF(x - 6, y - 72 + bob), QPointF(x + 6, y - 72 + bob),
                                         QPointF(x, y - 64 + bob)]))
            if (self.show_names or self.scent) and c.pack == "player":
                self._label(p, x, y + 14, c.name, QColor("#FFFFFF"))
            elif (self.show_names or self.scent) and c.pack != "player":
                self._label(p, x, y + 14, wd.rivals[c.pack].name.split()[1], QColor("#FF8A7A"))
            if c.carried > 0:
                p.setPen(Qt.NoPen)
                p.setBrush(QColor("#C04030"))
                p.drawEllipse(QPointF(x + 26 * c.facing, y - 34), 4, 3)

    def _label(self, p, x, y, text, colour):
        p.setFont(QFont("Tahoma", 8, QFont.Bold))
        fm = QFontMetrics(p.font())
        tw = fm.horizontalAdvance(text) + 8
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(0, 0, 0, 130))
        p.drawRoundedRect(QRectF(x - tw / 2, y, tw, 14), 4, 4)
        p.setPen(colour)
        p.drawText(QRectF(x - tw / 2, y, tw, 14), Qt.AlignCenter, text)

    def _weather(self, p, wd, winter):
        w, h = self.width(), self.height()
        tod = wd.time_of_day
        # night and dusk
        if tod < 0.22 or tod > 0.82:
            depth = 1.0 if (tod < 0.18 or tod > 0.88) else (0.22 - tod) / 0.04 if tod < 0.22 else (tod - 0.82) / 0.06
            depth = max(0.0, min(1.0, depth))
            me = wd.player
            cx, cy = self._camera()
            px, py = (me.x - cx, me.y - cy) if me else (w / 2, h / 2)
            g = QRadialGradient(QPointF(px, py - 20), max(w, h) * 0.6)
            g.setColorAt(0, QColor(10, 18, 50, int(70 * depth)))
            g.setColorAt(0.5, QColor(10, 18, 50, int(150 * depth)))
            g.setColorAt(1, QColor(6, 10, 30, int(210 * depth)))
            p.fillRect(self.rect(), QBrush(g))
        elif 0.22 <= tod < 0.28 or 0.76 < tod <= 0.82:
            a = int(60 * (1 - abs((tod - (0.25 if tod < 0.5 else 0.79)) / 0.03)))
            p.fillRect(self.rect(), QColor(255, 140, 60, max(0, a)))
        blizzard = wd.blizzard_until > wd.t
        if winter or blizzard:
            t = time.monotonic()
            n = len(self.snow) if blizzard else 70
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(255, 255, 255, 220))
            wind = 160 if blizzard else 20
            for i, (fx, fy, sp) in enumerate(self.snow[:n]):
                x = (fx * w + t * (wind + sp * 40)) % w
                y = (fy * h + t * (40 + sp * 60)) % h
                r = 1.2 + sp * (2.2 if blizzard else 1.4)
                p.drawEllipse(QPointF(x, y), r, r)
            if blizzard:
                p.fillRect(self.rect(), QColor(235, 240, 250, 95))

    def _draw_scent(self, p, ox, oy):
        """Scent view: the world dims and what the nose knows glows."""
        wd = self.world
        w, h = self.width(), self.height()
        p.fillRect(self.rect(), QColor(20, 10, 40, 120))
        me = wd.player
        if me is None:
            return
        t = time.monotonic()

        def glow(x, y, colour, r):
            sx, sy = x - ox, y - oy
            pulse = 1 + 0.12 * math.sin(t * 3 + x * 0.01)
            g = QRadialGradient(QPointF(sx, sy - 15), r * pulse)
            c = QColor(colour)
            g.setColorAt(0, QColor(c.red(), c.green(), c.blue(), 170))
            g.setColorAt(1, QColor(c.red(), c.green(), c.blue(), 0))
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(g))
            p.drawEllipse(QPointF(sx, sy - 15), r * pulse, r * pulse * 0.8)

        far = []
        for prey in wd.prey:
            if not prey.dead:
                glow(prey.x, prey.y, "#7DFF6A", 26 if prey.kind != "hare" else 14)
                far.append((prey, "#7DFF6A"))
        for c in wd.carcasses:
            glow(c.x, c.y, "#FFD24A", 34)
            far.append((c, "#FFD24A"))
        for b in wd.beasts:
            glow(b.x, b.y, "#FF9A3A", 40)
            far.append((b, "#FF9A3A"))
        for rp in wd.rivals:
            for x in rp.wolves:
                glow(x.x, x.y, "#FF4A4A", 30)
            # their territory's edge
            p.setPen(QPen(QColor(255, 80, 80, 140), 2, Qt.DashLine))
            p.setBrush(Qt.NoBrush)
            p.drawEllipse(QPointF(rp.den[0] - ox, rp.den[1] - oy), W.RIVAL_TERRITORY_R, W.RIVAL_TERRITORY_R)
        for m in wd.markers:
            p.setPen(QPen(QColor(120, 190, 255, int(60 + 120 * m.strength)), 2))
            p.setBrush(QColor(120, 190, 255, int(20 * m.strength)))
            p.drawEllipse(QPointF(m.x - ox, m.y - oy), W.TERRITORY_R, W.TERRITORY_R)
        den = wd.map.den
        glow(den[0], den[1], "#FFFFFF", 30)
        far.append((type("D", (), {"x": den[0], "y": den[1]})(), "#FFFFFF"))
        # arrows at the edge of the screen for what's out of sight (within a long sniff)
        cx, cy = me.x - ox, me.y - oy
        shown = 0
        for thing, colour in sorted(far, key=lambda it: math.hypot(it[0].x - me.x, it[0].y - me.y)):
            sx, sy = thing.x - ox, thing.y - oy
            d = math.hypot(thing.x - me.x, thing.y - me.y)
            if 0 < sx < w and 0 < sy < h or d > 2600:
                continue
            ang = math.atan2(sy - cy, sx - cx)
            ex = cx + math.cos(ang) * 2000
            ey = cy + math.sin(ang) * 2000
            # clip to the screen border
            k = min(abs((w / 2 - 24) / (math.cos(ang) or 1e-6)), abs((h / 2 - 24) / (math.sin(ang) or 1e-6)))
            ax, ay = w / 2 + math.cos(ang) * k, h / 2 + math.sin(ang) * k
            del ex, ey
            p.save()
            p.translate(ax, ay)
            p.rotate(math.degrees(ang))
            p.setPen(QPen(QColor(0, 0, 0, 160), 1))
            p.setBrush(QColor(colour))
            p.drawPolygon(QPolygonF([QPointF(10, 0), QPointF(-6, -7), QPointF(-6, 7)]))
            p.restore()
            shown += 1
            if shown > 10:
                break

    # the HUD ------------------------------------------------------------------------------------------------------
    def _draw_hud(self, p):
        wd = self.world
        w, h = self.width(), self.height()
        # the pack
        rows = [x for x in wd.pack if not x.dead]
        box = QRectF(8, 8, 236, 22 + 21 * len(rows))
        p.setPen(QPen(QColor(255, 255, 255, 60), 1))
        p.setBrush(QColor(10, 14, 24, 170))
        p.drawRoundedRect(box, 8, 8)
        p.setFont(_font(10, True))
        p.setPen(GOLD)
        p.drawText(QRectF(16, 10, 200, 18), Qt.AlignVCenter, f"Your pack ({len(rows)})")
        for i, x in enumerate(rows):
            y = 31 + i * 21
            if x is wd.player:
                p.setPen(Qt.NoPen)
                p.setBrush(QColor(242, 193, 46, 50))
                p.drawRoundedRect(QRectF(12, y - 1, 228, 20), 4, 4)
            p.setBrush(QColor(art.COATS[x.coat][0]))
            p.setPen(QPen(QColor(0, 0, 0, 120), 1))
            p.drawEllipse(QPointF(22, y + 9), 6, 6)
            p.setFont(QFont("Tahoma", 8, QFont.Bold if x is wd.player else QFont.Normal))
            p.setPen(QColor("white"))
            tag = ("pup " if x.pup else "") + ("♂" if x.sex == "male" else "♀")
            extra = " G" if x.guard else ""
            extra += " M" if x.mange else ""
            p.drawText(QRectF(32, y, 100, 18), Qt.AlignVCenter, f"{x.name} {tag}{extra}")
            self._bar(p, QRectF(136, y + 3, 46, 5), x.hp / x.maxhp, QColor("#E04848"))
            self._bar(p, QRectF(136, y + 10, 46, 5), x.hunger / 100, QColor("#F0A030"))
            self._bar(p, QRectF(188, y + 6, 46, 6), x.stamina / 100, QColor("#58B8F0")) if x is wd.player else None
        p.setFont(QFont("Tahoma", 7))
        p.setPen(QColor(255, 255, 255, 150))
        p.drawText(QRectF(16, box.bottom() + 2, 230, 12), Qt.AlignLeft,
                   "red: health  orange: hunger  blue: stamina")
        # the season and time
        s_box = QRectF(w - 236, 8, 228, 48)
        p.setPen(QPen(QColor(255, 255, 255, 60), 1))
        p.setBrush(QColor(10, 14, 24, 170))
        p.drawRoundedRect(s_box, 8, 8)
        colour = {"spring": "#8AE06A", "summer": "#F2D04A", "autumn": "#F0903A", "winter": "#A8D8FF"}[wd.season]
        p.setFont(_font(13, True))
        p.setPen(QColor(colour))
        p.drawText(QRectF(s_box.x() + 10, 10, 210, 22), Qt.AlignLeft | Qt.AlignVCenter,
                   f"{wd.season.title()}, day {wd.day_of_season}")
        p.setFont(QFont("Tahoma", 8))
        p.setPen(QColor("white"))
        p.drawText(QRectF(s_box.x() + 10, 32, 210, 18), Qt.AlignLeft | Qt.AlignVCenter,
                   f"Year {wd.year}  -  {wd.clock_text()}" + ("  -  Blizzard!" if wd.blizzard_until > wd.t else ""))
        # food carried
        me = wd.player
        if me is not None and me.carried > 0:
            p.setFont(QFont("Tahoma", 8, QFont.Bold))
            p.setPen(QColor("white"))
            p.drawText(QRectF(12, h - 44, 200, 14), Qt.AlignLeft, "Food for the den")
            self._bar(p, QRectF(12, h - 28, 160, 8), me.carried / 40, QColor("#C04030"))
        self._draw_minimap(p)
        # messages
        now = wd.t
        recent = [(text, kind, t) for text, kind, t in wd.messages if now - t < 9]
        y = h - 160 - 22 * len(recent)
        for text, kind, t in recent:
            fade = max(0.0, min(1.0, (9 - (now - t)) / 2))
            col = {"bad": QColor("#FF8A7A"), "good": QColor("#9CF08A"), "big": GOLD, "pack": QColor("#BCD8FF")}.get(
                kind, QColor("#FFFFFF"))
            col.setAlphaF(fade)
            f = _font(12 if kind == "big" else 10, kind in ("big", "bad"))
            p.setFont(f)
            fm = QFontMetrics(f)
            tw = min(w - 300, fm.horizontalAdvance(text) + 20)
            r = QRectF((w - tw) / 2, y, tw, 20)
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(0, 0, 0, int(140 * fade)))
            p.drawRoundedRect(r, 6, 6)
            p.setPen(col)
            p.drawText(r, Qt.AlignCenter, fm.elidedText(text, Qt.ElideRight, int(tw - 12)))
            y += 22
        if wd.prompt:
            r = QRectF(w / 2 - 220, h / 2 - 50, 440, 100)
            p.setPen(QPen(GOLD, 2))
            p.setBrush(QColor(10, 14, 24, 220))
            p.drawRoundedRect(r, 10, 10)
            p.setFont(_font(12, True))
            p.setPen(QColor("white"))
            lone = wd.prompt[1]
            p.drawText(r.adjusted(14, 8, -14, -40), Qt.AlignCenter | Qt.TextWordWrap,
                       f"{lone.name}, a lone {lone.sex} wolf, wants to join your pack.")
            p.setFont(_font(11))
            p.setPen(GOLD)
            p.drawText(r.adjusted(14, 50, -14, -8), Qt.AlignCenter, "Y - welcome them      N - send them away")
        # keys
        p.setFont(QFont("Tahoma", 8))
        p.setPen(QColor(255, 255, 255, 170))
        p.drawText(QRectF(0, h - 16, w - 200, 14), Qt.AlignHCenter,
                   "WASD move - Shift run - C sneak - Space bite - F eat - E scent - M mark - H howl - R rest - "
                   "Tab names - F1 help - Esc pause")

    def _bar(self, p, r, frac, colour):
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(0, 0, 0, 150))
        p.drawRoundedRect(r, 2, 2)
        p.setBrush(colour)
        p.drawRoundedRect(QRectF(r.x(), r.y(), r.width() * max(0.0, min(1.0, frac)), r.height()), 2, 2)

    def _draw_minimap(self, p):
        wd = self.world
        size = 170
        if self.minimap is None or self.minimap[0] != wd.season:
            img = QPixmap(W.MAP_TILES, W.MAP_TILES)
            q = QPainter(img)
            for ty in range(W.MAP_TILES):
                for tx in range(W.MAP_TILES):
                    q.setPen(QColor(art.TERRAIN[wd.map.tiles[ty][tx]][wd.season][0]))
                    q.drawPoint(tx, ty)
            q.end()
            self.minimap = (wd.season, img.scaled(size, size, Qt.IgnoreAspectRatio, Qt.FastTransformation))
        x0, y0 = self.width() - size - 10, self.height() - size - 24
        p.setPen(QPen(QColor(255, 255, 255, 120), 2))
        p.setBrush(Qt.NoBrush)
        p.drawPixmap(x0, y0, self.minimap[1])
        p.drawRect(QRectF(x0, y0, size, size))
        k = size / W.WORLD

        def dot(x, y, colour, r=2.5):
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(colour))
            p.drawEllipse(QPointF(x0 + x * k, y0 + y * k), r, r)
        for m in wd.markers:
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(120, 190, 255, int(70 * m.strength)))
            p.drawEllipse(QPointF(x0 + m.x * k, y0 + m.y * k), W.TERRITORY_R * k, W.TERRITORY_R * k)
        for rp in wd.rivals:
            p.setPen(QPen(QColor(255, 80, 80, 150), 1, Qt.DashLine))
            p.setBrush(Qt.NoBrush)
            p.drawEllipse(QPointF(x0 + rp.den[0] * k, y0 + rp.den[1] * k), W.RIVAL_TERRITORY_R * k,
                          W.RIVAL_TERRITORY_R * k)
        den = wd.map.den
        dot(den[0], den[1], "#FFFFFF", 4)
        if self.scent:
            for c in wd.carcasses:
                dot(c.x, c.y, "#FFD24A", 2.5)
        for x in wd.pack:
            if not x.dead:
                dot(x.x, x.y, "#BCD8FF", 2)
        if wd.player is not None:
            dot(wd.player.x, wd.player.y, GOLD.name(), 3.5)

    def _draw_help(self, p):
        w, h = self.width(), self.height()
        r = QRectF(w / 2 - 330, 50, 660, h - 120)
        p.setPen(QPen(GOLD, 2))
        p.setBrush(QColor(10, 14, 24, 235))
        p.drawRoundedRect(r, 12, 12)
        p.setFont(_font(18, True))
        p.setPen(GOLD)
        p.drawText(r.adjusted(0, 12, 0, 0), Qt.AlignHCenter, "How to Play")
        text = (
            "Lead your pack through the seasons. Keep everyone fed, raise the pups, and hold your ground.\n\n"
            "HUNTING  Find prey (press E for scent view: green = prey, gold = a kill, red = rival wolves, orange = "
            "bears and cougars). Sneak up with C, then run (Shift) and bite (Space). Your packmates join in. Tired, "
            "young and hurt animals are easiest; bulls and bison fight back. Hold F at a kill to eat.\n\n"
            "PUPS  In spring your mate has pups at the den and stays to guard them. Eat your fill at a kill, keep "
            "holding F to carry extra food, then go back to the den to feed them. In autumn they travel with you, and "
            "next spring they're full members of the pack.\n\n"
            "TERRITORY  Press M to leave scent marks. Marks fade over time; a well-marked home keeps rival raids "
            "away. Stay out of rival territory (red dashed circles) unless you're spoiling for a fight.\n\n"
            "SEASONS  Summer is good hunting. Autumn brings the elk rut and migrating herds. Winter brings deep snow "
            "(it slows elk even more than wolves), thin herds, hungry rivals and blizzards - shelter in the forest "
            "or at the den.\n\n"
            "H howls to gather the pack, R rests, Tab shows names. If your wolf dies you carry on as another; the "
            "game ends when no grown wolves are left. The game saves every day.")
        p.setFont(QFont("Tahoma", 9))
        p.setPen(QColor("white"))
        p.drawText(r.adjusted(26, 54, -26, -50), Qt.TextWordWrap, text)
        self._button(p, QRectF(r.center().x() - 70, r.bottom() - 46, 140, 36), "Close", self._toggle_help, True)

    def _draw_pause(self, p):
        w, h = self.width(), self.height()
        p.fillRect(self.rect(), QColor(0, 0, 0, 130))
        p.setFont(_font(28, True))
        p.setPen(GOLD)
        p.drawText(QRect(0, h // 2 - 120, w, 50), Qt.AlignHCenter, "Paused")
        self._button(p, QRectF(w / 2 - 110, h / 2 - 50, 220, 44), "Back to the Valley", self._resume)
        self._button(p, QRectF(w / 2 - 110, h / 2 + 4, 220, 44), "How to Play", self._toggle_help)
        self._button(p, QRectF(w / 2 - 110, h / 2 + 58, 220, 44), "Save and Quit to Title", self._quit_title)

    def _resume(self):
        self.state = "play"
        self.help = False
        self.setFocus()

    def _quit_title(self):
        self.save()
        self.world = None
        self.state = "title"
        self.help = False

    def _draw_over(self, p):
        wd = self.world
        w, h = self.width(), self.height()
        p.fillRect(self.rect(), QColor(0, 0, 0, 170))
        r = QRectF(w / 2 - 260, h / 2 - 170, 520, 330)
        p.setPen(QPen(GOLD, 2))
        p.setBrush(QColor(10, 14, 24, 235))
        p.drawRoundedRect(r, 12, 12)
        p.setFont(_font(22, True))
        p.setPen(GOLD)
        p.drawText(r.adjusted(0, 16, 0, 0), Qt.AlignHCenter, "The Pack's Story")
        st = wd.stats
        kills = ", ".join(f"{n} {k}" for k, n in st["kills"].items()) or "none"
        lines = [f"Survived until {wd.season} of year {wd.year}",
                 f"Pups born: {st['pups_born']}    Pups raised to yearlings: {st['pups_raised']}",
                 f"Largest pack: {st['max_pack']} wolves",
                 f"Hunts: {kills}",
                 f"Rival wolves driven off: {st['rivals_beaten']}"]
        p.setFont(_font(12))
        p.setPen(QColor("white"))
        for i, line in enumerate(lines):
            p.drawText(QRectF(r.x() + 20, r.y() + 70 + i * 30, r.width() - 40, 26), Qt.AlignHCenter, line)
        self._button(p, QRectF(r.center().x() - 90, r.bottom() - 60, 180, 42), "Back to Title", self._quit_title)


# ---- the window ----------------------------------------------------------------------------------------------------
_open = {}


def launch(desktop):
    win = _open.get("win")
    if win is not None and isValid(win):
        desktop.open_window(win)
        return win
    body = Game(desktop)
    win = host.window(desktop, "ClaudeQuest", body, quest_icon(), size=(980, 700))
    body.frame = win
    _open["win"] = win
    desktop.open_window(win)
    body.setFocus()
    return win


def shutdown():
    win = _open.get("win")
    if win is not None and isValid(win):
        win.content.shutdown()
