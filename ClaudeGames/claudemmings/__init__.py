"""Claudemmings - guide the lemmings from the trapdoor to the exit. In the spirit of Lemmings (DMA Design, 1991).

The twelve Fun levels, played on the original maps, sprites, sound effects and music from Local Storage\\Lemmings
(your own copy: it isn't part of the Timeline's code). Pick a skill at the bottom, then click a lemming to give it.

Mouse: choose a skill, click a lemming. Scroll: move the mouse to the edge of the view, the arrow keys, or click
the minimap. Keys: 1-8 skills, + / - release rate, Space or P pause, F fast forward, N twice to nuke, M music,
S sound effects, Esc back to the menu, F3 timing overlay.
"""
import json
import time
from pathlib import Path

from PySide6.QtCore import QPointF, QRect, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QIcon, QImage, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QWidget
from shiboken6 import isValid

from claudecore import host

from . import levels as L

VW, VH = 960, 600                 # the whole window in logical pixels
SCALE = 3                         # map pixels -> logical pixels (the maps are 160 high: 480 on screen)
MAP_H = 160 * SCALE
VIEW_W = VW // SCALE              # map pixels across the view (320, the original's screen)
STATUS_Y = MAP_H
PANEL_Y = MAP_H + 24
BTN_W, BTN_H = 62, 88
SKILLS = list(L.ALL)
SKILL_ANIM = {"climber": "climb", "floater": "float", "bomber": "ohno", "blocker": "block", "builder": "build",
              "basher": "bash", "miner": "mine", "digger": "dig"}
GREEN, BLUE, SKIN = "#00B000", "#4040E0", "#F0D0D0"
STEP = 1.0 / 17


def root():
    return Path(host.local_storage()) / "Lemmings"


def _progress_file():
    return host.saves("claudemmings") / "progress.json"


def claudemmings_icon():
    """A lemming: green hair, blue robe, pink hands."""
    rows = ["..GG....", ".GGGG...", "..GSS...", "..SS....", ".BBBS...", "SBBB....", ".BBB....", ".BBB....",
            ".S.S....", "SS.SS..."]
    colours = {"G": QColor(GREEN), "B": QColor(BLUE), "S": QColor(SKIN)}
    ic = QIcon()
    for sz in (16, 32, 48):
        pm = QPixmap(sz, sz)
        pm.fill(Qt.transparent)
        p = QPainter(pm)
        cell = sz / 11
        ox = (sz - 6 * cell) / 2
        for y, row in enumerate(rows):
            for x, ch in enumerate(row):
                if ch in colours:
                    p.fillRect(QRectF(ox + x * cell, cell * 0.5 + y * cell, cell + 0.4, cell + 0.4), colours[ch])
        p.end()
        ic.addPixmap(pm)
    return ic


class Claudemmings(QWidget):
    def __init__(self, desktop):
        super().__init__()
        self.desktop = desktop
        self.frame = None
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMouseTracking(True)
        self.setAttribute(Qt.WA_OpaquePaintEvent, True)
        self.setMinimumSize(480, 300)
        self.state = "menu"
        self.level = None
        self.index = 0
        self.skill = None
        self.cam = 0                     # map x at the left of the view
        self.mouse = QPointF(-1, -1)
        self.paused = False
        self.fast = False
        self.nuke_armed = 0.0
        self.overlay = False
        self.stats = [0, 0, 0.0, 0.0]    # frames, steps, step ms, paint ms (for F3)
        self.progress = self._load_progress()
        self.map_images = {}
        self.sprites = None
        self.problem = ""
        from .audio import Audio
        self.audio = Audio(self, root())
        try:
            from .sprites import Sprites
            self.sprites = Sprites(root() / "sprites" / "LEM 1.png", SCALE)
        except Exception as exc:
            self.problem = f"The Lemmings media isn't on this computer's external drive:\n{root()}\n\n({exc})"
        self.acc = 0.0
        self.last = time.monotonic()
        self.timer = QTimer(self)
        self.timer.setTimerType(Qt.PreciseTimer)
        self.timer.timeout.connect(self._tick)
        self.timer.start(16)
        if not self.problem:
            self.audio.music(L.TITLE_MUSIC)

    # ---- progress -----------------------------------------------------------------------------------------------
    def _load_progress(self):
        try:
            data = json.loads(_progress_file().read_text(encoding="utf-8"))
            if isinstance(data, dict):
                data.setdefault("unlocked", 1)
                data.setdefault("best", {})
                return data
        except (OSError, ValueError):
            pass
        return {"unlocked": 1, "best": {}}

    def _save_progress(self):
        try:
            _progress_file().write_text(json.dumps(self.progress, indent=1), encoding="utf-8")
        except OSError:
            pass

    # ---- levels -------------------------------------------------------------------------------------------------
    def _map(self, n):
        if n not in self.map_images:
            path = next(iter((root() / "background Images").glob(f"*-{n:02d}-pc-map.webp")), None)
            self.map_images[n] = QImage(str(path)) if path else QImage()
        return self.map_images[n]

    def brief(self, index):
        self.index = index
        self.state = "brief"
        self.level = None
        self.audio.music(L.INTRO_MUSIC, loop=False)
        self.update()

    def start(self):
        from .engine import Level
        spec = L.LEVELS[self.index]
        img = self._map(spec["map"])
        if img.isNull():
            self.problem = f"Level {self.index + 1}'s map is missing from {root() / 'background Images'}."
            self.state = "menu"
            return
        self.level = Level(spec, img)
        tx, _ty = spec["trapdoor"]
        self.cam = max(0, min(self.level.W - VIEW_W, tx + 22 - VIEW_W // 2))
        self.skill = next((s for s in SKILLS if self.level.skills[s] > 0), None)
        self.paused = self.fast = False
        self.state = "play"
        self.acc = 0.0
        self.audio.play("letsgo")
        self.audio.music(L.level_music(self.index))
        self.setFocus()

    def finish(self):
        lv = self.level
        self.state = "result"
        key = str(self.index + 1)
        if lv.percent() > self.progress["best"].get(key, -1):
            self.progress["best"][key] = lv.percent()
        if lv.won:
            self.progress["unlocked"] = max(self.progress["unlocked"], min(len(L.LEVELS), self.index + 2))
        self._save_progress()
        self.audio.music(L.CLEAR_MUSIC if lv.won else L.FAIL_MUSIC, loop=False)
        self.update()

    # ---- the loop -----------------------------------------------------------------------------------------------
    def _tick(self):
        now = time.monotonic()
        dt = min(0.25, now - self.last)
        self.last = now
        if self.state == "play" and self.level is not None:
            self._scroll_edges()
            if not self.paused:
                self.acc += dt * (3 if self.fast else 1)
                t0 = time.perf_counter()
                steps = 0
                while self.acc >= STEP and steps < (12 if self.fast else 4):
                    self.acc -= STEP
                    self.level.step()
                    for e in self.level.events:
                        self.audio.play(e)
                    steps += 1
                    if self.level.done:
                        break
                if steps == (12 if self.fast else 4):
                    self.acc = 0.0                   # too far behind: don't spiral
                self.stats[1] += steps
                self.stats[2] = (time.perf_counter() - t0) * 1000
                if self.level.done:
                    self.finish()
        self.update()

    def _scroll_edges(self):
        lv = self.level
        mx, my = self.mouse.x(), self.mouse.y()
        if 0 <= my < MAP_H and self.underMouse():
            if 0 <= mx < 24:
                self.cam = max(0, self.cam - 4)
            elif VW - 24 <= mx <= VW:
                self.cam = min(max(0, lv.W - VIEW_W), self.cam + 4)

    # ---- coordinates ---------------------------------------------------------------------------------------------
    def _xf(self):
        sc = min(self.width() / VW, self.height() / VH)
        ox, oy = (self.width() - VW * sc) / 2, (self.height() - VH * sc) / 2
        return sc, ox, oy

    def _logical(self, pos):
        sc, ox, oy = self._xf()
        return QPointF((pos.x() - ox) / sc, (pos.y() - oy) / sc)

    def _map_point(self, p):
        return int(p.x() // SCALE) + self.cam, int(p.y() // SCALE)

    # ---- painting ------------------------------------------------------------------------------------------------
    def paintEvent(self, _e):
        t0 = time.perf_counter()
        p = QPainter(self)
        p.fillRect(self.rect(), QColor("#000000"))
        sc, ox, oy = self._xf()
        p.translate(ox, oy)
        p.scale(sc, sc)
        p.setClipRect(QRectF(0, 0, VW, VH))
        if self.problem and self.state != "play":
            self._paint_problem(p)
        elif self.state == "menu":
            self._paint_menu(p)
        elif self.state == "brief":
            self._paint_brief(p)
        else:
            self._paint_level(p)
            self._paint_panel(p)
            if self.state == "result":
                self._paint_result(p)
        if self.overlay:
            self._paint_overlay(p)
        p.end()
        self.stats[0] += 1
        self.stats[3] = (time.perf_counter() - t0) * 1000

    def _font(self, size, bold=True, family="Courier New"):
        f = QFont(family)
        f.setPixelSize(size)
        f.setBold(bold)
        return f

    def _paint_problem(self, p):
        p.setPen(QColor("#FFFFFF"))
        p.setFont(self._font(18, False, "Arial"))
        p.drawText(QRectF(60, 160, VW - 120, 300), Qt.AlignCenter | Qt.TextWordWrap, self.problem)

    def _paint_title(self, p, y):
        p.setFont(self._font(54))
        for dx, dy, col in ((4, 4, "#003000"), (0, 0, GREEN)):
            p.setPen(QColor(col))
            p.drawText(QRectF(dx, y + dy, VW, 70), Qt.AlignHCenter, "CLAUDEMMINGS")
        p.setFont(self._font(14, False, "Arial"))
        p.setPen(QColor("#A0A0FF"))
        p.drawText(QRectF(0, y + 66, VW, 20), Qt.AlignHCenter, "Fun levels - pick one to play")

    def _menu_rows(self):
        rows = []
        for i in range(len(L.LEVELS)):
            col, row = divmod(i, 6)
            rows.append((i, QRectF(70 + col * 420, 162 + row * 62, 400, 54)))
        return rows

    def _paint_menu(self, p):
        self._paint_title(p, 30)
        if self.sprites:
            for k in range(6):
                pm, (ax, ay) = self.sprites.frame("walk", int(time.monotonic() * 10) + k, 1)
                p.drawPixmap(int((time.monotonic() * 40 + k * 160) % (VW + 60)) - 30 - ax, 150 - ay, pm)
        for i, r in self._menu_rows():
            spec = L.LEVELS[i]
            open_ = i < self.progress["unlocked"]
            hover = r.contains(self.mouse) and open_
            p.setPen(QPen(QColor(GREEN if open_ else "#404040"), 2))
            p.setBrush(QColor("#102810" if hover else "#081008"))
            p.drawRoundedRect(r, 6, 6)
            p.setPen(QColor("#FFFFFF" if open_ else "#606060"))
            p.setFont(self._font(15))
            p.drawText(r.adjusted(14, 6, -10, -26), Qt.AlignLeft | Qt.AlignVCenter, f"{i + 1:2d}. {spec['name']}")
            p.setFont(self._font(12, False, "Arial"))
            p.setPen(QColor("#A0E0A0" if open_ else "#505050"))
            best = self.progress["best"].get(str(i + 1))
            sub = ("locked" if not open_ else
                   f"{spec['lemmings']} lemmings, save {spec['save']}%" + (f"   best {best}%" if best is not None else ""))
            p.drawText(r.adjusted(40, 28, -10, -4), Qt.AlignLeft | Qt.AlignVCenter, sub)
        p.setPen(QColor("#808080"))
        p.setFont(self._font(12, False, "Arial"))
        p.drawText(QRectF(0, VH - 30, VW, 20), Qt.AlignHCenter,
                   "M music on/off   S sound on/off   In a level: 1-8 skills, F fast forward, Space pause, N N nuke")

    def _paint_brief(self, p):
        spec = L.LEVELS[self.index]
        img = self._map(spec["map"])
        if not img.isNull():
            w = min(VW - 80, img.width() * 2)
            h = int(img.height() * w / img.width())
            p.drawImage(QRectF((VW - w) / 2, 40, w, h), img)
        p.setPen(QColor(GREEN))
        p.setFont(self._font(26))
        p.drawText(QRectF(0, 260, VW, 36), Qt.AlignHCenter, f"Level {self.index + 1}")
        p.setPen(QColor("#FFFFFF"))
        p.drawText(QRectF(0, 296, VW, 36), Qt.AlignHCenter, spec["name"])
        p.setFont(self._font(20))
        lines = [f"Number of Lemmings {spec['lemmings']}", f"{spec['save']}% To Be Saved",
                 f"Release Rate {spec['rate']}", f"Time {spec['minutes']} Minutes", "Rating FUN"]
        colours = ["#4060FF", "#00C000", "#FFFF40", "#40E0E0", "#E040E0"]
        for k, (t, c) in enumerate(zip(lines, colours)):
            p.setPen(QColor(c))
            p.drawText(QRectF(0, 350 + k * 30, VW, 30), Qt.AlignHCenter, t)
        p.setPen(QColor("#A0A0A0"))
        p.setFont(self._font(14, False, "Arial"))
        p.drawText(QRectF(0, VH - 40, VW, 24), Qt.AlignHCenter, "Click to start   -   Esc for the menu")

    def _paint_level(self, p):
        lv = self.level
        view = QRectF(0, 0, VW, MAP_H)
        src = QRectF(self.cam, 0, VIEW_W, 160)
        p.save()
        p.setClipRect(view)
        p.drawImage(view, lv.decor, src)
        p.drawImage(view, lv.terrain, src)
        if self.sprites:
            tx, ty = lv.trap
            ox, oy = self.sprites.trap_offset
            p.drawPixmap(int((tx - ox - self.cam) * SCALE), int((ty - oy) * SCALE), self.sprites.trap[lv.trap_frame])
        hovered = None
        if 0 <= self.mouse.y() < MAP_H and self.state == "play":
            mx, my = self._map_point(self.mouse)
            hovered = lv.lemming_at(mx, my, self.skill)
        for lem in lv.lemmings:
            if lem.gone:
                continue
            sx = (lem.x - self.cam) * SCALE
            if sx < -60 or sx > VW + 60:
                continue
            self._paint_lemming(p, lem, sx, lem.y * SCALE)
        for x, y, _vx, _vy, life, rgb in lv.particles:
            p.fillRect(QRectF((x - self.cam) * SCALE, y * SCALE, SCALE, SCALE), QColor(rgb))
        if hovered is not None:
            p.setPen(QPen(QColor("#FFFFFF"), 2))
            p.setBrush(Qt.NoBrush)
            p.drawRect(QRectF((hovered.x - self.cam - 5) * SCALE, (hovered.y - 13) * SCALE, 11 * SCALE, 14 * SCALE))
        p.restore()
        # the status line
        p.fillRect(QRectF(0, STATUS_Y, VW, 24), QColor("#000000"))
        p.setFont(self._font(18))
        under = ""
        if 0 <= self.mouse.y() < MAP_H:
            mx, my = self._map_point(self.mouse)
            lems = lv.lemmings_under(mx, my)
            if lems:
                under = f"{lems[0].label().upper()} {len(lems)}"
        secs = lv.time_left // 17
        p.setPen(QColor(GREEN))
        p.drawText(QRectF(8, STATUS_Y, 260, 24), Qt.AlignVCenter | Qt.AlignLeft, under)
        p.drawText(QRectF(260, STATUS_Y, 200, 24), Qt.AlignVCenter | Qt.AlignLeft, f"OUT {lv.alive_count}")
        p.drawText(QRectF(440, STATUS_Y, 200, 24), Qt.AlignVCenter | Qt.AlignLeft, f"IN {lv.percent()}%")
        p.drawText(QRectF(620, STATUS_Y, 220, 24), Qt.AlignVCenter | Qt.AlignLeft, f"TIME {secs // 60}-{secs % 60:02d}")
        flags = ("PAUSED " if self.paused else "") + (">>" if self.fast else "")
        p.setPen(QColor("#FFFF40"))
        p.drawText(QRectF(VW - 110, STATUS_Y, 104, 24), Qt.AlignVCenter | Qt.AlignRight, flags)

    def _paint_lemming(self, p, lem, sx, sy):
        sp = self.sprites
        if sp is None:
            p.fillRect(QRectF(sx - 3, sy - 30, 6, 30), QColor(BLUE))
            return
        anim = lem.state
        if anim == "fall" and lem.floater and lem.fall >= 12:
            anim = "open"
        frame = lem.frame
        if anim == "walk":
            frame = lem.frame
        elif anim in ("mine",):
            frame = lem.work
        pm, (ax, ay) = sp.frame(anim, frame, lem.dir)
        p.drawPixmap(int(sx - ax), int(sy - ay), pm)
        if lem.bomb is not None:
            p.setPen(QColor("#FFFFFF"))
            p.setFont(self._font(16))
            p.drawText(QRectF(sx - 20, sy - 54, 40, 20), Qt.AlignCenter, str(lem.bomb // 17 + 1))

    def _buttons(self):
        keys = ["rate-", "rate+"] + SKILLS + ["pause", "nuke"]
        return [(k, QRectF(4 + i * BTN_W, PANEL_Y + 4, BTN_W - 4, BTN_H)) for i, k in enumerate(keys)]

    def _paint_panel(self, p):
        lv = self.level
        p.fillRect(QRectF(0, PANEL_Y, VW, VH - PANEL_Y), QColor("#101010"))
        for key, r in self._buttons():
            sel = key == self.skill or (key == "pause" and self.paused) or (key == "nuke" and lv.nuking)
            p.setPen(QPen(QColor("#FFFFFF" if sel else "#4848A8"), 3 if sel else 1))
            p.setBrush(QColor("#2A2A60" if sel else "#181838"))
            p.drawRect(r)
            p.setFont(self._font(18))
            p.setPen(QColor("#FFFFFF"))
            top = QRectF(r.x(), r.y() + 2, r.width(), 22)
            if key in SKILLS:
                n = lv.skills.get(key, 0)
                p.drawText(top, Qt.AlignCenter, str(n) if n else "")
                if self.sprites:
                    pm, (ax, ay) = self.sprites.frame(SKILL_ANIM[key], 3, 1)
                    p.drawPixmap(int(r.center().x() - ax), int(r.bottom() - 10 - ay), pm)
            elif key in ("rate-", "rate+"):
                p.drawText(top, Qt.AlignCenter, str(lv.min_rate if key == "rate-" else lv.rate))
                p.setFont(self._font(34))
                p.drawText(r.adjusted(0, 26, 0, 0), Qt.AlignCenter, "-" if key == "rate-" else "+")
            elif key == "pause":
                p.setBrush(QColor("#E0E0E0"))
                p.setPen(Qt.NoPen)
                p.drawRect(QRectF(r.center().x() - 12, r.y() + 30, 8, 36))
                p.drawRect(QRectF(r.center().x() + 4, r.y() + 30, 8, 36))
            else:
                p.setBrush(QColor("#E0E0E0"))
                p.setPen(Qt.NoPen)
                c = QPointF(r.center().x(), r.y() + 44)
                p.drawEllipse(c, 18, 12)
                p.drawRect(QRectF(c.x() - 5, c.y(), 10, 26))
        # the minimap
        mm = self._minimap_rect()
        p.fillRect(mm.adjusted(-2, -2, 2, 2), QColor("#303030"))
        p.drawImage(mm, lv.terrain)
        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(QColor("#FFFFFF"), 1))
        k = mm.width() / lv.W
        p.drawRect(QRectF(mm.x() + self.cam * k, mm.y(), VIEW_W * k, mm.height()))
        for lem in lv.lemmings:
            if not lem.gone:
                p.fillRect(QRectF(mm.x() + lem.x * k - 1, mm.y() + lem.y * mm.height() / 160 - 2, 2, 2), QColor("#FFFF00"))

    def _minimap_rect(self):
        lv = self.level
        x0 = 4 + 12 * BTN_W + 6
        w = VW - x0 - 6
        h = min(BTN_H - 8, w * 160 / max(1, lv.W))
        return QRectF(x0, PANEL_Y + 4 + (BTN_H - h) / 2, w, h)

    def _result_buttons(self):
        keys = ["Retry", "Next level", "Menu"] if self.level and self.level.won and self.index + 1 < len(L.LEVELS) \
            else ["Retry", "Menu"]
        w = 180
        x0 = (VW - len(keys) * (w + 20)) / 2
        return [(k, QRectF(x0 + i * (w + 20), 380, w, 44)) for i, k in enumerate(keys)]

    def _paint_result(self, p):
        lv = self.level
        p.fillRect(QRectF(0, 0, VW, VH), QColor(0, 0, 0, 200))
        p.setFont(self._font(26))
        p.setPen(QColor(GREEN if lv.won else "#FF6060"))
        head = "All lemmings accounted for." if lv.time_left > 0 else "Time is up!"
        p.drawText(QRectF(0, 150, VW, 36), Qt.AlignHCenter, head)
        p.setPen(QColor("#FFFFFF"))
        p.setFont(self._font(22))
        p.drawText(QRectF(0, 210, VW, 30), Qt.AlignHCenter, f"You rescued {lv.percent()}%")
        p.drawText(QRectF(0, 244, VW, 30), Qt.AlignHCenter, f"You needed {lv.spec['save']}%")
        p.setPen(QColor("#FFFF40"))
        verdict = ("Superb! You rescued every lemming." if lv.percent() == 100 else
                   "Well done - on to the next level!" if lv.won else
                   "So close... try again?" if lv.percent() >= lv.spec["save"] - 10 else "Better luck next time.")
        p.drawText(QRectF(0, 300, VW, 30), Qt.AlignHCenter, verdict)
        for k, r in self._result_buttons():
            p.setPen(QPen(QColor(GREEN), 2))
            p.setBrush(QColor("#183018" if r.contains(self.mouse) else "#0A180A"))
            p.drawRoundedRect(r, 6, 6)
            p.setPen(QColor("#FFFFFF"))
            p.setFont(self._font(18))
            p.drawText(r, Qt.AlignCenter, k)

    def _paint_overlay(self, p):
        p.fillRect(QRectF(VW - 250, 4, 246, 54), QColor(0, 0, 0, 180))
        p.setPen(QColor("#00FF00"))
        p.setFont(self._font(12, False))
        p.drawText(QRectF(VW - 244, 6, 240, 50), Qt.AlignLeft,
                   f"step {self.stats[2]:.2f} ms  paint {self.stats[3]:.2f} ms\nsteps {self.stats[1]}  frames {self.stats[0]}")

    # ---- input ---------------------------------------------------------------------------------------------------
    def mouseMoveEvent(self, e):
        self.mouse = self._logical(e.position())
        if e.buttons() & Qt.LeftButton and self.state == "play" and self._minimap_rect().contains(self.mouse):
            self._minimap_jump()

    def leaveEvent(self, _e):
        self.mouse = QPointF(-1, -1)

    def mousePressEvent(self, e):
        self.mouse = pos = self._logical(e.position())
        if self.problem and self.state != "play":
            return
        if self.state == "menu":
            for i, r in self._menu_rows():
                if r.contains(pos) and i < self.progress["unlocked"]:
                    self.audio.play("select")
                    self.brief(i)
            return
        if self.state == "brief":
            self.start()
            return
        if self.state == "result":
            for k, r in self._result_buttons():
                if r.contains(pos):
                    if k == "Retry":
                        self.brief(self.index)
                    elif k == "Next level":
                        self.brief(self.index + 1)
                    else:
                        self.state = "menu"
                        self.audio.music(L.TITLE_MUSIC)
            return
        lv = self.level
        if pos.y() < MAP_H:
            mx, my = self._map_point(pos)
            if self.skill and not self.paused:
                lv.assign(lv.lemming_at(mx, my, self.skill), self.skill)
                for ev in lv.events:
                    self.audio.play(ev)
                lv.events = []
            return
        if self._minimap_rect().contains(pos):
            self._minimap_jump()
            return
        for key, r in self._buttons():
            if r.contains(pos):
                self._button(key)

    def _minimap_jump(self):
        mm = self._minimap_rect()
        x = (self.mouse.x() - mm.x()) / mm.width() * self.level.W
        self.cam = int(max(0, min(self.level.W - VIEW_W, x - VIEW_W / 2)))

    def _button(self, key):
        lv = self.level
        if key in SKILLS:
            self.skill = key
            self.audio.play("select")
        elif key == "rate-":
            if lv.change_rate(-5):
                self.audio.play("rate")
        elif key == "rate+":
            if lv.change_rate(5):
                self.audio.play("rate")
        elif key == "pause":
            self.paused = not self.paused
        elif key == "nuke":
            now = time.monotonic()
            if now - self.nuke_armed < 0.6:
                lv.nuke()
                for ev in lv.events:
                    self.audio.play(ev)
                lv.events = []
            self.nuke_armed = now

    def keyPressEvent(self, e):
        k = e.key()
        if k == Qt.Key_F3:
            self.overlay = not self.overlay
        elif k == Qt.Key_M:
            self.audio.toggle_music()
        elif k == Qt.Key_S:
            self.audio.toggle_sfx()
        elif k == Qt.Key_Escape:
            if self.state in ("play", "result", "brief"):
                self.state = "menu"
                self.level = None
                self.audio.music(L.TITLE_MUSIC)
        elif self.state == "brief" and k in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space):
            self.start()
        elif self.state == "play":
            if Qt.Key_1 <= k <= Qt.Key_8:
                self._button(SKILLS[k - Qt.Key_1])
            elif k in (Qt.Key_Space, Qt.Key_P):
                self._button("pause")
            elif k == Qt.Key_F:
                self.fast = not self.fast
            elif k in (Qt.Key_Plus, Qt.Key_Equal):
                self._button("rate+")
            elif k == Qt.Key_Minus:
                self._button("rate-")
            elif k == Qt.Key_N:
                self._button("nuke")
            elif k == Qt.Key_Left:
                self.cam = max(0, self.cam - 16)
            elif k == Qt.Key_Right:
                self.cam = min(max(0, self.level.W - VIEW_W), self.cam + 16)
            else:
                super().keyPressEvent(e)
        else:
            super().keyPressEvent(e)

    def shutdown(self):
        self.timer.stop()
        self.audio.close()


_open = {}


def launch(desktop):
    win = _open.get("win")
    if win is not None and isValid(win):
        desktop.open_window(win)
        return win
    body = Claudemmings(desktop)
    win = host.window(desktop, "Claudemmings", body, claudemmings_icon(), (VW + 10, VH + 36))
    body.frame = win
    _open["win"] = win
    win.destroyed.connect(lambda *_: body.shutdown() if isValid(body) else None)
    desktop.open_window(win)
    body.setFocus()
    return win


def shutdown():
    win = _open.get("win")
    if win is not None and isValid(win):
        win.content.shutdown()
