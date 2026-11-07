"""The game's view: an OpenGL widget that runs the loop (step the Game, draw it, paint the HUD over it), takes the
mouse (look) and the keys, and hands the window's panels what the game asks for (a vendor, the stairs, death).

Keys: WASD move, mouse look, left button cast, Space jump, F talk / use, Q health potion, E mana potion, T scroll
of return, 1-4 or the wheel to change wand, Tab the pack, M the map, Esc the menu."""
import math
import time

import numpy as np
from PySide6.QtCore import QPoint, QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QCursor, QFont, QPainter, QPen, QRadialGradient, QSurfaceFormat
from PySide6.QtOpenGLWidgets import QOpenGLWidget

from ..engine.render import Renderer, project
from ..game import data as D
from ..game import items as I
from ..game.world import Input

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
            if Qt.Key_Left in k:
                self.inp.yaw -= 2.2 * dt
            if Qt.Key_Right in k:
                self.inp.yaw += 2.2 * dt
            ox, oz = g.x, g.z
            g.step(dt, self.inp)
            g._speed_seen = math.hypot(g.x - ox, g.z - oz) / max(dt, 1e-4)
            self._explore()
            self._music(g)
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
                if it.get("type") == "gear" and it["rarity"] >= 2:
                    self.toasts.append((f"Found: {I.item_name(it)}", D.RARITIES[it["rarity"]][2], now))
            elif kind == "kill":
                snd.play("kill", 0.5)
            elif kind == "piece":
                self.toasts.append((e[1], (1.0, 0.86, 0.55), now))
                for line in _wrap(e[2], 90):
                    self.toasts.append((line, (0.85, 0.82, 0.74), now + 0.3))
            elif kind == "chest":
                snd.play("coin", 0.7)
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
        # hurt: red at the edges
        if g.hurt > 0:
            rg = QRadialGradient(QPointF(W / 2, H / 2), max(W, H) * 0.7)
            rg.setColorAt(0.55, QColor(0, 0, 0, 0))
            rg.setColorAt(1.0, QColor(170, 10, 10, int(170 * min(1, g.hurt))))
            p.fillRect(self.rect(), rg)
        # the cross
        if g.depth:
            p.setPen(QPen(QColor(255, 255, 255, 170), 1.5))
            cx, cy = W / 2, H / 2
            for a, b in (((-9, 0), (-3, 0)), ((3, 0), (9, 0)), ((0, -9), (0, -3)), ((0, 3), (0, 9))):
                p.drawLine(QPointF(cx + a[0], cy + a[1]), QPointF(cx + b[0], cy + b[1]))
        # life and mana
        self._orb(p, 70, H - 70, 52, pl.life / max(1, pl.max_life()), QColor("#C0262A"), f"{int(pl.life)}/{pl.max_life()}")
        self._orb(p, W - 70, H - 70, 52, pl.mana / max(1, pl.max_mana()), QColor("#2A50D0"), f"{int(pl.mana)}/{pl.max_mana()}")
        # the wands
        n = len(pl.wands)
        bw = 64
        x0 = W / 2 - (n * (bw + 8)) / 2
        y0 = H - 92
        f = QFont("Segoe UI", 8)
        p.setFont(f)
        for i, w in enumerate(pl.wands):
            r = QRectF(x0 + i * (bw + 8), y0, bw, 52)
            p.setPen(QPen(QColor("#F0D080") if i == pl.active else QColor(255, 255, 255, 60), 2 if i == pl.active else 1))
            p.setBrush(QColor(10, 10, 16, 170))
            p.drawRoundedRect(r, 6, 6)
            p.setPen(QColor(255, 255, 255, 140))
            p.drawText(r.adjusted(4, 2, 0, 0), Qt.AlignLeft | Qt.AlignTop, str(i + 1))
            if w:
                from .icons import icon
                p.drawPixmap(int(r.x() + 12), int(r.y() + 4), icon(w, 40))
        # potions
        p.setFont(QFont("Segoe UI", 9, QFont.Bold))
        bx = W / 2 - 140
        for k, (key, kind, col) in enumerate((("Q", "health", "#E04040"), ("E", "mana", "#4070F0"), ("T", "return", "#C8A060"))):
            r = QRectF(bx + k * 96, H - 32, 88, 24)
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(10, 10, 16, 170))
            p.drawRoundedRect(r, 5, 5)
            p.setBrush(QColor(col))
            p.drawEllipse(QRectF(r.x() + 6, r.y() + 5, 14, 14))
            p.setPen(QColor("#E8E8E8"))
            p.drawText(r.adjusted(26, 0, 0, 0), Qt.AlignVCenter, f"{key}  x{pl.potions.get(kind, 0)}")
        # experience
        need = I.xp_to_next(pl.level)
        r = QRectF(W / 2 - 200, H - 100 - 10, 400, 5)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(0, 0, 0, 150))
        p.drawRect(r)
        p.setBrush(QColor("#D8B040"))
        p.drawRect(QRectF(r.x(), r.y(), r.width() * min(1, pl.xp / need), r.height()))
        # where, and gold
        p.setFont(QFont("Georgia", 13, QFont.Bold))
        where = D.TOWN_NAME if g.depth == 0 else f"Floor {g.depth} - {g.level.name}"
        self._shadow_text(p, QPointF(18, 30), where, QColor("#F0E0C0"))
        p.setFont(QFont("Segoe UI", 10))
        self._shadow_text(p, QPointF(18, 52), f"Level {pl.level}    {pl.gold} gold", QColor("#E8D088"))
        if g.depth == 0:
            self._shadow_text(p, QPointF(18, 72), f"The Deep's mouth goes down to floor {g.run_floor}", QColor("#B8B8D8"))
        # the guardian's bar
        boss = next((m for m in g.monsters if m.guardian and not m.dead and m.awake), None)
        if boss:
            r = QRectF(W / 2 - 260, 54, 520, 14)
            p.setPen(QPen(QColor("#2A1010"), 2))
            p.setBrush(QColor(20, 0, 0, 200))
            p.drawRect(r)
            p.setPen(Qt.NoPen)
            p.setBrush(QColor("#C03020"))
            p.drawRect(QRectF(r.x() + 2, r.y() + 2, (r.width() - 4) * max(0, boss.hp / boss.max_hp), r.height() - 4))
            p.setFont(QFont("Georgia", 12, QFont.Bold))
            self._shadow_text(p, QPointF(W / 2 - p.fontMetrics().horizontalAdvance(boss.name) / 2, 46), boss.name, QColor("#F0C0A0"))
        # floating numbers and loot
        pv = self.renderer.proj_view if self.renderer else None
        if pv is not None:
            for pos, text, col, born, size in self.floaters:
                age = now - born
                if age < 0:
                    continue
                s = project(pv, (pos[0], pos[1] + age * 0.5, pos[2]), W, H)
                if not s:
                    continue
                p.setFont(QFont("Segoe UI", size, QFont.Bold))
                a = int(255 * max(0, 1 - age / 1.4))
                c = QColor.fromRgbF(*col)
                c.setAlpha(a)
                tw = p.fontMetrics().horizontalAdvance(text)
                self._shadow_text(p, QPointF(s[0] - tw / 2, s[1]), text, c, a)
        # the townsfolk's names over their heads
        if pv is not None and g.level.npcs:
            p.setFont(QFont("Georgia", 11, QFont.Bold))
            for n in g.level.npcs:
                d = math.hypot(n["x"] - g.x, n["z"] - g.z)
                if d > 9:
                    continue
                s = project(pv, (n["x"], g.level.floor_at(n["x"], n["z"]) + 0.98, n["z"]), W, H)
                if not s:
                    continue
                v = D.VENDORS[n["vendor"]]
                a = int(255 * max(0.0, min(1.0, (9 - d) / 3)))
                for k, (text, col) in enumerate(((v["name"], QColor(248, 232, 176, a)), (v["title"], QColor(200, 190, 170, a)))):
                    tw = p.fontMetrics().horizontalAdvance(text)
                    self._shadow_text(p, QPointF(s[0] - tw / 2, s[1] - 18 + k * 17), text, col, a)
        # toasts
        p.setFont(QFont("Georgia", 12))
        for i, (text, col, born) in enumerate(self.toasts):
            age = now - born
            a = int(255 * max(0, min(1, (5 - age) / 1.0)))
            c = QColor.fromRgbF(*col)
            c.setAlpha(a)
            tw = p.fontMetrics().horizontalAdvance(text)
            self._shadow_text(p, QPointF(W / 2 - tw / 2, 104 + i * 24), text, c, a)
        # what F does here
        what, label = g.near()
        if label:
            p.setFont(QFont("Segoe UI", 12, QFont.Bold))
            text = label if what and what[0] == "sealed" else f"[F]  {label}"
            tw = p.fontMetrics().horizontalAdvance(text)
            r = QRectF(W / 2 - tw / 2 - 14, H * 0.62, tw + 28, 32)
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(0, 0, 0, 150))
            p.drawRoundedRect(r, 6, 6)
            p.setPen(QColor("#F8E8B0"))
            p.drawText(r, Qt.AlignCenter, text)
        # the map
        self._minimap(p, W, H, big=self.show_map)
        if not self.captured and not self.shell.panel_open():
            p.setFont(QFont("Segoe UI", 11))
            text = "Click to take the mouse (Esc gives it back)"
            tw = p.fontMetrics().horizontalAdvance(text)
            self._shadow_text(p, QPointF(W / 2 - tw / 2, H / 2 + 40), text, QColor(255, 255, 255, 200))

    def _shadow_text(self, p, at, text, colour, alpha=255):
        p.setPen(QColor(0, 0, 0, int(alpha * 0.8)))
        p.drawText(at + QPointF(1.5, 1.5), text)
        p.setPen(colour)
        p.drawText(at, text)

    def _orb(self, p, x, y, r, frac, colour, label):
        p.setPen(QPen(QColor("#1A1410"), 3))
        p.setBrush(QColor(12, 10, 10, 220))
        p.drawEllipse(QPointF(x, y), r, r)
        frac = max(0.0, min(1.0, frac))
        p.save()
        p.setClipRect(QRectF(x - r, y + r - 2 * r * frac, 2 * r, 2 * r * frac))
        rg = QRadialGradient(QPointF(x - r * 0.3, y - r * 0.3), r * 1.3)
        rg.setColorAt(0, colour.lighter(170))
        rg.setColorAt(1, colour.darker(160))
        p.setPen(Qt.NoPen)
        p.setBrush(rg)
        p.drawEllipse(QPointF(x, y), r - 3, r - 3)
        p.restore()
        p.setPen(QPen(QColor("#8A7050"), 2))
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(QPointF(x, y), r, r)
        p.setFont(QFont("Segoe UI", 9, QFont.Bold))
        tw = p.fontMetrics().horizontalAdvance(label)
        self._shadow_text(p, QPointF(x - tw / 2, y + 5), label, QColor("#FFFFFF"))

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
        p.setPen(QPen(QColor("#8A7050"), 1.5))
        p.setBrush(Qt.NoBrush)
        p.drawRect(QRectF(x0, y0, size, size))
