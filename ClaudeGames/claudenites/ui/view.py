"""The game's view: an OpenGL widget that runs the loop (step the Game, draw it, paint the HUD over it), takes the
mouse (look) and the keys, and hands the window's panels what the game asks for (a vendor, the stairs, death).

Keys: WASD move, mouse look, left button cast, Space jump, F talk / use, Q health potion, E mana potion, T scroll
of return, 1-4 or the wheel to change wand, Tab the pack, M the map, Esc the menu."""
import math
import time

import numpy as np
from PySide6.QtCore import QPoint, QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import (QColor, QCursor, QFont, QFontMetrics, QLinearGradient, QPainter, QPen, QRadialGradient,
                           QSurfaceFormat)
from PySide6.QtOpenGLWidgets import QOpenGLWidget

from ..engine.render import Renderer, project
from ..game import data as D
from ..game import items as I
from ..game.world import Input
from . import theme

SENS = 0.0024


def _wrap(text, width):
    words, lines, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > width and cur:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        lines.append(cur)
    return lines


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
        self.game = None
        self.renderer = None
        self.keys = set()
        self.inp = Input()
        self.captured = False
        self.running = False
        self.last = time.perf_counter()
        self.floaters = []                        # (world pos, text, colour, born, size)
        self.toasts = []                          # (text, colour, born)
        self.explored = None
        self.show_map = False
        self.fps = 0.0
        self.gl_error = None
        self.timer = QTimer(self)
        self.timer.setTimerType(Qt.PreciseTimer)
        self.timer.timeout.connect(self.tick)
        self.timer.start(0)

    # ---- GL ----------------------------------------------------------------------------------------------------
    def initializeGL(self):
        try:
            self.renderer = Renderer()
        except Exception as exc:                  # (shown on the view rather than lost)
            self.gl_error = str(exc)
            import traceback
            traceback.print_exc()

    def paintGL(self):
        self.paints = getattr(self, "paints", 0) + 1
        dt = getattr(self, "_frame_dt", 0.016)
        if self.renderer and self.game:
            try:
                dpr = self.devicePixelRatioF()
                self.renderer.ground_blend = bool(self.shell.settings.get("blend", True))
                self.renderer.draw(self.game, int(self.width() * dpr), int(self.height() * dpr), dt)
            except Exception as exc:
                self.gl_error = repr(exc)
                import traceback
                traceback.print_exc()
                self.game = None
        from OpenGL import GL
        GL.glBindVertexArray(0)
        GL.glUseProgram(0)
        GL.glDisable(GL.GL_DEPTH_TEST)
        GL.glDisable(GL.GL_BLEND)
        GL.glDepthMask(GL.GL_TRUE)
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.TextAntialiasing)
        try:
            if self.gl_error:
                p.fillRect(self.rect(), QColor("#100808"))
                p.setPen(QColor("#F0C0B0"))
                p.drawText(self.rect().adjusted(30, 30, -30, -30), Qt.TextWordWrap,
                           "The picture couldn't be drawn:\n\n" + self.gl_error)
            elif self.game:
                if self.running:
                    self.hud(p)
        finally:
            p.end()

    # ---- the loop ----------------------------------------------------------------------------------------------
    def start(self, game):
        self.game = game
        self.running = True
        self.floaters, self.toasts = [], []
        self.explored = None
        self.last = time.perf_counter()
        self.setFocus()

    def tick(self):
        now = time.perf_counter()
        dt = min(0.05, now - self.last)
        self.last = now
        self._frame_dt = dt
        if dt > 0:
            self.fps = self.fps * 0.95 + (1 / dt) * 0.05
        g = self.game
        if g and self.running and not self.shell.panel_open():
            k = self.keys
            self.inp.forward = (1 if Qt.Key_W in k or Qt.Key_Up in k else 0) - (1 if Qt.Key_S in k or Qt.Key_Down in k else 0)
            self.inp.strafe = (1 if Qt.Key_D in k else 0) - (1 if Qt.Key_A in k else 0)
            self.inp.run = Qt.Key_Shift in k
            if Qt.Key_Left in k:
                self.inp.yaw -= 2.2 * dt
            if Qt.Key_Right in k:
                self.inp.yaw += 2.2 * dt
            ox, oz = g.x, g.z
            g.step(dt, self.inp)
            g._speed_seen = math.hypot(g.x - ox, g.z - oz) / max(dt, 1e-4)
            self._explore()
            self._music(g)
            self._sound_of_weather(g)
        elif g and not self.running:                       # (the title's backdrop: Thornwick, the camera circling the square)
            g.time += dt
            a = g.time * 0.045
            cx, cz = g.level.portal
            g.x, g.z = cx + math.cos(a) * 8.5, cz + math.sin(a) * 8.5
            g.y = 1.1
            g.yaw = math.atan2(cx - g.x, -(cz - g.z))
            g.pitch = -0.2
        if g:
            self._events()
        self.update()

    def _sound_of_weather(self, g):
        w = g.sky.now()
        out = g.level.outdoor
        kb = 0.0 if out else max(0.0, 1 - (g.depth - 1) / 10) * 0.25          # (below: heard far off, the first floors only)
        rain = w["strength"] if w["kind"] in ("rain", "storm") else 0.0
        wind = max(w["wind"][0] - 0.2, 0.0) * 0.9 if w["kind"] != "clear" else 0.0
        self.shell.sounds.loop("rain", rain * (0.55 if out else kb))
        self.shell.sounds.loop("wind", wind * (0.5 if out else kb))

    def _music(self, g):
        """The music follows him: the town, the forest, the band he's in, and a guardian's fight."""
        if g.depth:
            key = (g.depth - 1) // 10
            boss = any(m.guardian and m.awake and not m.dead for m in g.monsters)
        else:
            key = "town" if g.in_town() else "forest"
            boss = False
        self.shell.music.place(key, boss)

    def _explore(self):
        g = self.game
        L = g.level
        if self.explored is None or self.explored.shape != L.solid.shape or getattr(self, "_explored_for", None) is not L:
            self.explored = np.zeros(L.solid.shape, bool)
            self._explored_for = L
        cx, cy = int(g.x), int(g.z)
        r = 7 if not L.outdoor else 12
        y0, y1, x0, x1 = max(0, cy - r), min(L.h, cy + r + 1), max(0, cx - r), min(L.w, cx + r + 1)
        self.explored[y0:y1, x0:x1] = True

    def _events(self):
        g = self.game
        ev, g.events = g.events, []
        now = time.perf_counter()
        snd = self.shell.sounds
        for e in ev:
            kind = e[0]
            if kind == "toast":
                self.toasts.append((e[1], e[2], now))
            elif kind == "dmg":
                _, pos, n, el, crit = e
                c = D.ELEMENT_COLOUR.get(el, (1, 1, 1))
                self.floaters.append((pos, f"{n}!" if crit else str(n), c, now, 22 if crit else 16))
                snd.play("hit", 0.35)
            elif kind == "loot":
                _, pos, got = e
                for i, line in enumerate(got):
                    self.floaters.append(((pos[0], pos[1] + 0.25 + i * 0.18, pos[2]), line,
                                          (1.0, 0.85, 0.35) if "gold" in line else (0.8, 0.95, 1.0), now + i * 0.15, 15))
                snd.play("coin", 0.5)
            elif kind == "found":
                it = e[1]
                rk = int(it.get("rarity", 0))
                if rk >= 2:                                             # (Rare and up: said; Epic and up: heard; Legendary: shown)
                    self.toasts.append((f"{D.RARITIES[rk][0]}: {I.item_name(it)}", D.RARITIES[rk][2], now))
                if rk >= 3:
                    snd.play("levelup", 0.35 if rk == 3 else 0.6)
                if rk >= 4:
                    self.banner = ("LEGENDARY", now, I.item_name(it))
            elif kind == "kill":
                snd.play("kill", 0.5)
            elif kind == "piece":
                self.toasts.append((e[1], (1.0, 0.86, 0.55), now))
                for line in _wrap(e[2], 90):
                    self.toasts.append((line, (0.85, 0.82, 0.74), now + 0.3))
            elif kind == "chest":
                snd.play("coin", 0.7)
            elif kind == "pickup":
                snd.play("coin" if e[1] == "gold" else "drink" if e[1] in ("health", "mana") else "levelup", 0.45)
            elif kind == "lightning":
                if self.renderer:
                    self.renderer.lightning(1.0)
                QTimer.singleShot(int(400 + 1200 * self.shell.rng.random()), lambda: self.shell.sounds.play("thunder", 0.8))
            elif kind == "lightning_below":
                if self.renderer:
                    self.renderer.lightning(0.35 * e[1])
                QTimer.singleShot(900, lambda v=e[1]: self.shell.sounds.play("thunder", 0.35 * v))
            elif kind == "weather":
                pass
            elif kind == "break":
                snd.play("break", 0.7)
            elif kind == "thud":
                snd.play("thud", 0.5)
            elif kind == "cast":
                snd.play("cast_" + e[1], 0.32)
                if self.renderer:
                    self.renderer.kick()
            elif kind == "foecast":
                snd.play("foecast", 0.3)
            elif kind == "hurt":
                snd.play("hurt", 0.55)
            elif kind == "levelup":
                snd.play("levelup", 0.6)
                self.banner = (f"LEVEL {e[1]}", now)
            elif kind == "drink":
                snd.play("drink", 0.5)
            elif kind == "nomana":
                if not self.toasts or self.toasts[-1][0] != "Out of mana":
                    self.toasts.append(("Out of mana", (0.5, 0.65, 1.0), now))
                snd.play("nomana", 0.4)
            elif kind == "arc" and self.renderer:
                self.renderer.arc(e[1], e[2])
            elif kind == "level":
                snd.play("stairs", 0.5)
                self.explored = None
                L = e[1]
                came = getattr(self, "_last_kind", None)
                self._last_kind = L.kind
                if L.depth:
                    self.card = (f"FLOOR {L.depth}", L.name, L.line, now + 0.2)
                elif L.kind == "cabin":
                    self.card = ("HOME", L.name, L.line, now + 0.1)
                elif came == "cabin":
                    pass
                elif self.running:
                    self.card = ("HOME", D.TOWN_NAME, "A clearing in the forest, a ring of roofs, and the Deep under the old stones.", now + 0.2)
            elif kind == "sleep":
                self.sleep_fade = now
                snd.play("levelup", 0.35)
            elif kind == "trap":
                snd.play({"spikes": "hit", "darts": "foecast", "fire": "cast_fire"}[e[1]], 0.6)
                if e[1] == "spikes":
                    self.toasts.append(("Spikes!", (1.0, 0.5, 0.45), now))
            elif kind == "rush":
                if e[1]:
                    self.banner = (f"CHAMPION {e[1]} OF {e[2]}", now, e[3])
                    snd.play("levelup", 0.5)
                else:
                    self.banner = ("THE GAUNTLET IS RUN", now, "A Legendary waits in the hall")
            elif kind == "secret":
                self.toasts.append((f"A secret! ({e[2]} of {e[3]} found)", (0.85, 0.75, 1.0), now))
                snd.play("levelup", 0.45)
            elif kind == "door":
                snd.play("break", 0.5)
                snd.play("levelup", 0.3)
            elif kind == "lever":
                snd.play("thud", 0.7)
            elif kind == "brazier":
                snd.play("cast_fire", 0.6)
            elif kind == "trial":
                snd.play("levelup" if e[1] else "nomana", 0.6)
            elif kind == "save":
                self.shell.save()
            elif kind == "died":
                self.shell.on_death(e[1])
            elif kind == "victory":
                self.shell.on_victory()
        self.toasts = [t for t in self.toasts if now - t[2] < 7.0][-7:]
        self.floaters = [f for f in self.floaters if now - f[3] < 1.4]
        if g.dialog:
            what, g.dialog = g.dialog, None
            self.release()
            self.shell.open_dialog(what)

    # ---- input -------------------------------------------------------------------------------------------------
    def capture(self):
        if self.captured or not self.game:
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
        self.inp.fire = False
        self.releaseMouse()
        self.unsetCursor()

    def _centre(self):
        c = self.mapToGlobal(QPoint(self.width() // 2, self.height() // 2))
        self._centre_at = c
        QCursor.setPos(c)

    def mouseMoveEvent(self, e):
        if not self.captured:
            return
        c = getattr(self, "_centre_at", None)
        gp = e.globalPosition().toPoint()
        if c is None or gp == c:
            return
        dx, dy = gp.x() - c.x(), gp.y() - c.y()
        sens = SENS * float(self.shell.settings.get("mouse", 1.0))
        self.inp.yaw += dx * sens
        self.inp.pitch = max(-1.4, min(1.4, self.inp.pitch - dy * sens))
        self._centre()

    def mousePressEvent(self, e):
        if not self.captured:
            self.capture()
            return
        if e.button() == Qt.LeftButton:
            self.inp.fire = True

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.inp.fire = False

    def wheelEvent(self, e):
        g = self.game
        if not g:
            return
        step = -1 if e.angleDelta().y() > 0 else 1
        self._switch(step)

    def _switch(self, step=None, to=None):
        p = self.game.player
        ready = [i for i, w in enumerate(p.wands) if w]
        if not ready:
            return
        if to is not None:
            if p.wands[to]:
                p.active = to
        else:
            i = ready.index(p.active) if p.active in ready else 0
            p.active = ready[(i + step) % len(ready)]
        self.shell.sounds.play("click", 0.4)

    def keyPressEvent(self, e):
        k = e.key()
        if e.isAutoRepeat():
            return
        g = self.game
        if k == Qt.Key_Escape:
            self.release()
            self.shell.pause()
            return
        if not g:
            return
        self.keys.add(k)
        if k == Qt.Key_Space:
            self.inp.jump = True
        elif k == Qt.Key_F:
            g.interact()
        elif k == Qt.Key_Q:
            g.drink("health")
        elif k == Qt.Key_E:
            g.drink("mana")
        elif k == Qt.Key_T:
            if g.depth and not g.read_return():
                self.toasts.append(("No Scroll of Return to read.", (0.9, 0.7, 0.6), time.perf_counter()))
        elif k in (Qt.Key_1, Qt.Key_2, Qt.Key_3, Qt.Key_4):
            self._switch(to=k - Qt.Key_1)
        elif k in (Qt.Key_Tab, Qt.Key_I):
            self.release()
            self.shell.open_dialog(("pack",))
        elif k == Qt.Key_M:
            self.show_map = not self.show_map
        elif k == Qt.Key_K:
            self.release()
            self.shell.open_dialog(("calendar",))

    def keyReleaseEvent(self, e):
        if not e.isAutoRepeat():
            self.keys.discard(e.key())

    def focusOutEvent(self, e):
        self.keys.clear()
        self.inp.fire = False
        super().focusOutEvent(e)

    def event(self, e):                          # (Tab would move focus away: keep it for the pack)
        from PySide6.QtCore import QEvent
        if e.type() == QEvent.KeyPress and e.key() == Qt.Key_Tab:
            self.keyPressEvent(e)
            return True
        return super().event(e)

    # ---- the HUD -----------------------------------------------------------------------------------------------
    def hud(self, p):
        g = self.game
        pl = g.player
        W, H = self.width(), self.height()
        now = time.perf_counter()
        T = theme
        # hurt: red at the edges
        if g.hurt > 0:
            rg = QRadialGradient(QPointF(W / 2, H / 2), max(W, H) * 0.7)
            rg.setColorAt(0.55, QColor(0, 0, 0, 0))
            rg.setColorAt(1.0, QColor(170, 10, 10, int(170 * min(1, g.hurt))))
            p.fillRect(self.rect(), rg)
        # the cross: a ring and a dot, in the wand's element
        if g.depth or not g.in_town():
            s = pl.wand_stats()
            c = QColor.fromRgbF(*D.ELEMENT_COLOUR[s["element"]]) if s else QColor(255, 255, 255)
            c.setAlpha(190)
            cx, cy = W / 2, H / 2
            p.setRenderHint(QPainter.Antialiasing)
            p.setPen(QPen(QColor(0, 0, 0, 140), 3))
            p.setBrush(Qt.NoBrush)
            p.drawEllipse(QPointF(cx, cy), 7, 7)
            p.setPen(QPen(c, 1.5))
            p.drawEllipse(QPointF(cx, cy), 7, 7)
            p.setPen(Qt.NoPen)
            p.setBrush(c)
            p.drawEllipse(QPointF(cx, cy), 1.6, 1.6)
        # the plate along the bottom: the wands, the potions, the experience
        n = len(pl.wands)
        bw, gap = 62, 8
        pw = n * (bw + gap) + 60
        plate_r = QRectF(W / 2 - pw / 2, H - 112, pw, 106)
        T.plate(p, plate_r, 14)
        need = I.xp_to_next(pl.level)
        T.bar(p, QRectF(plate_r.x() + 18, plate_r.y() + 9, plate_r.width() - 36, 8), pl.xp / need,
              QColor("#C8962C"), QColor("#FFE9A0"), now)
        x0 = W / 2 - (n * (bw + gap) - gap) / 2
        y0 = plate_r.y() + 24
        from .icons import icon
        for i, w in enumerate(pl.wands):
            r = QRectF(x0 + i * (bw + gap), y0, bw, 50)
            active = i == pl.active
            gr = QLinearGradient(r.topLeft(), r.bottomLeft())
            gr.setColorAt(0, QColor(10, 8, 5, 230))
            gr.setColorAt(1, QColor(42, 32, 22, 230))
            p.setPen(Qt.NoPen)
            p.setBrush(gr)
            p.drawRoundedRect(r, 8, 8)
            if active and w:
                el = QColor.fromRgbF(*D.ELEMENT_COLOUR[I.wand_stats(w)["element"]])
                k = 0.6 + 0.4 * math.sin(now * 3.2)
                glow = QRadialGradient(r.center(), r.width() * 0.7)
                el.setAlpha(int(110 * k))
                glow.setColorAt(0, el)
                el2 = QColor(el)
                el2.setAlpha(0)
                glow.setColorAt(1, el2)
                p.setBrush(glow)
                p.drawRoundedRect(r, 8, 8)
            p.setBrush(Qt.NoBrush)
            p.setPen(T.gold_pen(r, 2.2) if active else QPen(QColor(120, 96, 62, 160), 1.2))
            p.drawRoundedRect(r, 8, 8)
            if w and w.get("rarity", 0) >= 1:                          # (its rarity, a line round the inside)
                rc = QColor.fromRgbF(*D.RARITIES[w["rarity"]][2])
                rc.setAlpha(int(150 + 80 * math.sin(now * 2.5)) if w["rarity"] >= 3 else 170)
                p.setPen(QPen(rc, 1.6))
                p.drawRoundedRect(r.adjusted(3, 3, -3, -3), 6, 6)
            if w:
                p.drawPixmap(int(r.x() + 11), int(r.y() + 5), icon(w, 40))
            T.outlined(p, r.x() + 5, r.y() + 13, str(i + 1), QFont(T.BODY, 9, QFont.Bold),
                       QColor("#FFE9A0") if active else QColor(200, 186, 160), width=2.5)
        # the potions and the scroll, on the plate's foot
        bx = W / 2 - 3 * 88 / 2
        for k, (key, kind) in enumerate((("Q", "health"), ("E", "mana"), ("T", "return"))):
            r = QRectF(bx + k * 88 + 4, plate_r.bottom() - 30, 80, 24)
            pic = icon({"type": "potion" if kind != "return" else "scroll", "kind": kind, "id": "hud:" + kind}, 22)
            p.drawPixmap(int(r.x()), int(r.y() + 1), pic)
            T.outlined(p, r.x() + 26, r.y() + 17, key, QFont(T.BODY, 9, QFont.Bold), QColor("#FFE9A0"), width=2.5)
            T.outlined(p, r.x() + 40, r.y() + 17, f"x{pl.potions.get(kind, 0)}", QFont(T.BODY, 10, QFont.Bold),
                       QColor("#F0E4C8"), width=2.5)
        # life and mana, in their orbs at the plate's ends
        T.orb(p, 78, H - 78, 56, pl.life / max(1, pl.max_life()), QColor("#C8242A"),
              f"{int(pl.life)}/{pl.max_life()}", now, warn=pl.life < pl.max_life() * 0.3)
        T.orb(p, W - 78, H - 78, 56, pl.mana / max(1, pl.max_mana()), QColor("#2E58E0"),
              f"{int(pl.mana)}/{pl.max_mana()}", now)
        # where, and gold
        where = D.TOWN_NAME if g.depth == 0 else f"Floor {g.depth}  -  {g.level.name}"
        if g.depth == 0 and not g.in_town():
            where = f"The wood round {D.TOWN_NAME}"
        if g.level.kind == "cabin":
            where = g.level.name
        T.outlined(p, 18, 32, where, QFont(T.HEAD, 15, QFont.Bold), QColor("#F6E2B0"))
        T.outlined(p, 18, 54, f"Level {pl.level}", QFont(T.BODY, 10, QFont.Bold), QColor("#E8D8B8"), width=2.5)
        T.outlined(p, 90, 54, f"{pl.gold} gold", QFont(T.BODY, 10, QFont.Bold), QColor("#FFD86A"), width=2.5)
        if g.depth == 0:
            T.outlined(p, 18, 74, f"The Deep's mouth goes down to floor {g.run_floor}", QFont(T.HEAD, 10),
                       QColor("#C8C4E0"), width=2.5)
        # the guardian's bar
        boss = next((m for m in g.monsters if m.guardian and not m.dead and m.awake), None)
        if boss:
            r = QRectF(W / 2 - 270, 52, 540, 16)
            T.plate(p, r.adjusted(-10, -26, 10, 8), 8, 180)
            T.bar(p, r, max(0.0, boss.hp / boss.max_hp), QColor("#A01810"), QColor("#FF7050"), now)
            T.outlined(p, W / 2, 44, boss.name, QFont(T.HEAD, 13, QFont.Bold), QColor("#FFD0A8"), centre=True)
        # floating numbers and loot: they pop, then rise and fade
        pv = self.renderer.proj_view if self.renderer else None
        if pv is not None:
            for pos, text, col, born, size in self.floaters:
                age = now - born
                if age < 0:
                    continue
                s = project(pv, (pos[0], pos[1] + age * 0.5, pos[2]), W, H)
                if not s:
                    continue
                pop = 1.0 + 0.45 * max(0.0, 1 - age / 0.15)
                a = int(255 * max(0, 1 - age / 1.4))
                T.outlined(p, s[0], s[1], text, QFont(T.BODY, int(size * pop), QFont.Bold), QColor.fromRgbF(*col), a,
                           centre=True)
        # the farm's sign, named over it
        sign = g.level.spots.get("sign")
        if pv is not None and sign:
            d = math.hypot(sign[0] - g.x, sign[1] - g.z)
            s = project(pv, (sign[0], 1.45, sign[1]), W, H) if d < 12 else None
            if s:
                a = int(255 * max(0.0, min(1.0, (12 - d) / 3)))
                T.outlined(p, s[0], s[1], "The farm", QFont(T.HEAD, 12, QFont.Bold), QColor(200, 236, 150), a, centre=True)
        # the meals at work, under the place's name: each its picture and the time it has left
        self._buffs(p, pl)
        if getattr(g, "keys", None):                                    # (the keys he holds on this floor)
            from .icons import _sprite
            from ..engine.itempics import ITEMS
            for k, colour in enumerate(sorted(g.keys)):
                pm = _sprite("s7_I_Key03.png" if colour == "gold" else f"key_{colour}.png", 30)
                r = QRectF(18 + k * 40, 126, 36, 36)
                T.plate(p, r, 8, 190)
                if pm is not None:
                    p.drawPixmap(int(r.x() + 3), int(r.y() + 3), pm)
            _ = ITEMS
        # the townsfolk's names over their heads
        if pv is not None and g.level.npcs:
            for n in g.level.npcs:
                d = math.hypot(n["x"] - g.x, n["z"] - g.z)
                if d > 9:
                    continue
                s = project(pv, (n["x"], g.level.floor_at(n["x"], n["z"]) + 0.98, n["z"]), W, H)
                if not s:
                    continue
                v = D.VENDORS[n["vendor"]]
                a = int(255 * max(0.0, min(1.0, (9 - d) / 3)))
                T.outlined(p, s[0], s[1] - 18, v["name"], QFont(T.HEAD, 12, QFont.Bold), QColor(250, 226, 160), a, centre=True)
                T.outlined(p, s[0], s[1] - 2, v["title"], QFont(T.HEAD, 10), QColor(210, 198, 176), a, centre=True)
        # toasts, on ribbons
        for i, (text, col, born) in enumerate(self.toasts):
            age = now - born
            if age < 0:
                continue
            a = int(255 * max(0, min(1, (6.5 - age) / 1.0, age / 0.25)))
            y = 104 + i * 26 - max(0.0, 0.25 - age) * 40
            T.ribbon(p, W / 2, y - 17, min(W - 60, 30 + 8.2 * len(text)), 24, a)
            T.outlined(p, W / 2, y, text, QFont(T.HEAD, 12), QColor.fromRgbF(*col), a, centre=True, width=2.5)
        # what F does here
        what, label = g.near()
        if label:
            text = label if what and what[0] == "sealed" else label
            f = QFont(T.HEAD, 13, QFont.Bold)
            tw = QFontMetrics(f).horizontalAdvance(text)
            r = QRectF(W / 2 - tw / 2 - 46, H * 0.62, tw + 70, 36)
            T.plate(p, r, 18, 200)
            if not (what and what[0] == "sealed"):
                key = QRectF(r.x() + 10, r.y() + 7, 22, 22)
                p.setPen(T.gold_pen(key, 1.5))
                p.setBrush(QColor(60, 44, 24))
                p.drawRoundedRect(key, 4, 4)
                T.outlined(p, key.center().x(), key.y() + 16, "F", QFont(T.BODY, 10, QFont.Bold), QColor("#FFE9A0"),
                           centre=True, width=2)
            T.outlined(p, r.x() + 40 + tw / 2, r.y() + 24, text, f, QColor("#F8E8B8"), centre=True)
        # the map, and the dial under it
        self._minimap(p, W, H, big=self.show_map)
        if not self.show_map:
            from .dial import paint_dial
            paint_dial(p, QRectF(W - 196, 204, 180, 112), g.sky, g.level.outdoor, g.depth)
        T_ = getattr(g.level, "trial", None)                            # (the brazier trial: how many, how long)
        if T_ and T_["until"] and not T_["done"]:
            left = max(0.0, T_["until"] - g.time)
            n = sum(b["lit"] for b in g.level.braziers)
            r = QRectF(W / 2 - 150, 170, 300, 40)
            T.plate(p, r, 10, 210)
            T.bar(p, QRectF(r.x() + 14, r.y() + 27, r.width() - 28, 6), left / 12.0, QColor("#C8501C"), QColor("#FFC060"), now)
            T.outlined(p, W / 2, r.y() + 20, f"Braziers lit: {n} of {len(g.level.braziers)}  -  {left:.0f}s",
                       QFont(T.HEAD, 12, QFont.Bold), QColor("#FFD890"), centre=True, width=2.5)
        if getattr(g.level, "special", None) == "dream":                 # (the Dreaming: colour washing over the eyes)
            for k, col in enumerate(((255, 40, 60), (40, 255, 90), (60, 90, 255))):
                cx = W * (0.5 + 0.45 * math.sin(now * 0.31 + k * 2.1))
                cy = H * (0.5 + 0.4 * math.cos(now * 0.23 + k * 1.7))
                rg = QRadialGradient(QPointF(cx, cy), max(W, H) * 0.55)
                rg.setColorAt(0, QColor(*col, int(58 + 22 * math.sin(now * 0.9 + k))))
                rg.setColorAt(1, QColor(*col, 0))
                p.fillRect(self.rect(), rg)
        # a new floor's card, and a level's banner
        self._cards(p, W, H, now)
        fade = getattr(self, "sleep_fade", None)                        # (to sleep: dark, then the morning)
        if fade is not None:
            age = now - fade
            if age > 3.0:
                self.sleep_fade = None
            else:
                a = min(1.0, age / 0.4) if age < 0.4 else max(0.0, 1 - (age - 1.2) / 1.8) if age > 1.2 else 1.0
                p.fillRect(self.rect(), QColor(4, 3, 8, int(250 * a)))
                if 0.3 < age < 2.4:
                    T.outlined(p, W / 2, H / 2, "Morning.", QFont(T.HEAD, 26, QFont.Bold), QColor(250, 226, 170),
                               int(255 * min(1.0, (age - 0.3) / 0.4, (2.4 - age) / 0.4)), centre=True)
        if not self.captured and not self.shell.panel_open():
            T.outlined(p, W / 2, H / 2 + 44, "Click to take the mouse  (Esc gives it back)", QFont(T.HEAD, 12),
                       QColor(255, 248, 230), 220, centre=True, width=2.5)

    def _buffs(self, p, pl):
        import time as _t
        from ..game import food as F
        from .icons import icon
        T = theme
        live = F.active(pl.buffs, _t.time())
        for k, (key, end) in enumerate(live):
            x, y = 18 + k * 128, 86
            r = QRectF(x, y, 122, 34)
            T.plate(p, r, 8, 190)
            p.drawPixmap(int(x + 4), int(y + 3), icon({"type": "larder", "key": "cooked:" + key, "id": "l:cooked:" + key}, 28))
            left = max(0, int(end - _t.time()))
            T.outlined(p, x + 36, y + 15, F.RECIPES[key][0][:15], QFont(T.BODY, 8, QFont.Bold), QColor("#F6D98A"), width=2)
            T.outlined(p, x + 36, y + 29, f"{left // 3600}:{left % 3600 // 60:02d}:{left % 60:02d} left", QFont(T.BODY, 8),
                       QColor("#E0D4B8"), width=2)

    def _cards(self, p, W, H, now):
        T = theme
        card = getattr(self, "card", None)
        if card:
            title, sub, line, born = card
            age = now - born
            if age > 5.0:
                self.card = None
            else:
                a = max(0.0, min(1.0, age / 0.6, (5.0 - age) / 1.0))
                A = int(255 * a)
                y = H * 0.28 - (1 - min(1.0, age / 0.6)) * 14
                T.ribbon(p, W / 2, y - 62, min(W - 40, 760), 118, A)
                T.outlined(p, W / 2, y - 30, title, QFont(T.BODY, 12, QFont.Bold), QColor(232, 192, 104), A, centre=True)
                T.outlined(p, W / 2, y + 12, sub, QFont(T.HEAD, 32, QFont.Bold), QColor(250, 236, 200), A, centre=True,
                           width=4)
                if line:
                    T.outlined(p, W / 2, y + 42, line, QFont(T.HEAD, 12, -1, True),
                               QColor(220, 208, 184), A, centre=True, width=2.5)
        ban = getattr(self, "banner", None)
        if ban:
            text, born = ban[:2]
            sub = ban[2] if len(ban) > 2 else "A skill point to spend with Mother Wren"
            age = now - born
            if age > 3.0:
                self.banner = None
            else:
                a = int(255 * max(0.0, min(1.0, age / 0.2, (3.0 - age) / 0.8)))
                scale = 1.0 + 0.25 * max(0.0, 1 - age / 0.35)
                cy = H * 0.42
                burst = QRadialGradient(QPointF(W / 2, cy - 10), 220 * scale)
                burst.setColorAt(0, QColor(255, 220, 120, int(a * 0.45)))
                burst.setColorAt(1, QColor(255, 220, 120, 0))
                p.setPen(Qt.NoPen)
                p.setBrush(burst)
                p.drawEllipse(QPointF(W / 2, cy - 10), 260 * scale, 120 * scale)
                T.outlined(p, W / 2, cy, text, QFont(T.HEAD, int(30 * scale), QFont.Bold), QColor(255, 226, 130), a,
                           centre=True, width=5)
                T.outlined(p, W / 2, cy + 30, sub, QFont(T.HEAD, 12), QColor(240, 228, 200),
                           a, centre=True, width=2.5)

    def _map_image(self, L):
        """The explored squares as a little picture, made again only when more has been seen."""
        key = (id(L), int(self.explored.sum()))
        if getattr(self, "_map_key", None) != key:
            from PySide6.QtGui import QImage
            arr = np.zeros((L.h, L.w, 4), np.uint8)
            seen = self.explored & ~L.solid
            arr[seen] = (90, 140, 80, 210) if L.outdoor else (150, 140, 120, 210)
            raised = seen & (L.floor > 0.1)
            arr[raised] = (175, 165, 140, 220)
            sunk = seen & (L.floor < -0.1)
            arr[sunk] = (110, 100, 90, 220)
            self._map_buf = arr
            self._map_img = QImage(arr.data, L.w, L.h, L.w * 4, QImage.Format_RGBA8888).copy()
            self._map_key = key
        return self._map_img

    def _minimap(self, p, W, H, big=False):
        g = self.game
        L = g.level
        if self.explored is None:
            return
        cell = 6 if big else 4
        size = (min(W, H) - 120) if big else 180
        x0, y0 = (W - size) / 2 if big else W - size - 16, (H - size) / 2 if big else 16
        p.save()
        p.setClipRect(QRectF(x0, y0, size, size))
        p.fillRect(QRectF(x0, y0, size, size), QColor(0, 0, 0, 150 if not big else 200))
        ox, oy = x0 + size / 2 - g.x * cell, y0 + size / 2 - g.z * cell
        p.drawImage(QRectF(ox, oy, L.w * cell, L.h * cell), self._map_image(L))
        p.setPen(Qt.NoPen)
        if L.stairs and not L.outdoor and self.explored[int(L.stairs[1]), int(L.stairs[0])]:
            p.setBrush(QColor("#70A0FF"))
            p.drawEllipse(QPointF(ox + L.stairs[0] * cell, oy + L.stairs[1] * cell), cell, cell)
        if L.outdoor and L.portal:
            p.setBrush(QColor("#9070FF"))
            p.drawEllipse(QPointF(ox + L.portal[0] * cell, oy + L.portal[1] * cell), cell * 1.2, cell * 1.2)
        for n in L.npcs:
            p.setBrush(QColor("#F0D060"))
            p.drawEllipse(QPointF(ox + n["x"] * cell, oy + n["z"] * cell), cell * 0.8, cell * 0.8)
        for m in g.monsters:
            if not m.dead and m.awake and self.explored[int(m.z), int(m.x)]:
                p.setBrush(QColor("#E04030"))
                p.drawEllipse(QPointF(ox + m.x * cell, oy + m.z * cell), cell * 0.5, cell * 0.5)
        # him, and which way he looks
        cx, cy = x0 + size / 2, y0 + size / 2
        p.setBrush(QColor("#FFFFFF"))
        p.drawEllipse(QPointF(cx, cy), 3, 3)
        p.setPen(QPen(QColor("#FFFFFF"), 1.5))
        p.drawLine(QPointF(cx, cy), QPointF(cx + math.sin(g.yaw) * 10, cy - math.cos(g.yaw) * 10))
        p.restore()
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(QPen(QColor(8, 5, 2, 220), 4))
        p.setBrush(Qt.NoBrush)
        p.drawRoundedRect(QRectF(x0, y0, size, size), 6, 6)
        p.setPen(theme.gold_pen(QRectF(x0, y0, size, size), 2))
        p.drawRoundedRect(QRectF(x0, y0, size, size), 6, 6)
