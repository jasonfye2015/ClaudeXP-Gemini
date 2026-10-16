"""ClaudeCraft - a block-building game (a Minecraft-style clone) for ClaudeXP's Games folder.

A world of 160 x 160 blocks, 64 high, generated from a seed (world.py), drawn with OpenGL through Qt (no other
libraries): each 16 x 16 chunk is one vertex buffer of its visible faces, with a texture atlas painted in code,
face shading and distance fog. First person: WASD to walk, mouse to look (click to capture the mouse, Esc to let go),
Space to jump (double-tap to fly, Space/Shift up and down while flying), Ctrl to sprint. Left click breaks a block,
right click places the one picked in the hotbar (1-9 or the mouse wheel). Creative mode: every block, no limits.
Your world and where you stood are saved in data/claudecraft/world.json.
"""
import math
import time
from array import array

from PySide6.QtCore import QPointF, QRect, Qt, QTimer
from PySide6.QtGui import (QColor, QCursor, QFont, QIcon, QLinearGradient, QMatrix4x4, QPainter, QPen, QPixmap,
                           QPolygonF, QSurfaceFormat, QVector3D)
from PySide6.QtOpenGL import QOpenGLBuffer, QOpenGLShaderProgram, QOpenGLShader, QOpenGLTexture
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from shiboken6 import isValid

from claudecore import host
from . import world as W

SAVE = host.saves("claudecraft") / "world.json"        # shared by every era
GL_DEPTH_TEST, GL_BLEND, GL_CULL_FACE = 0x0B71, 0x0BE2, 0x0B44
GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA = 0x0302, 0x0303
GL_TRIANGLES, GL_LINES, GL_FLOAT = 0x0004, 0x0001, 0x1406
GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT = 0x4000, 0x0100
SKY = QColor("#86B6F5")
FOG = (0.53, 0.71, 0.96)
STRIDE = 6 * 4
EYE = 1.62
WALK, SPRINT, FLY = 4.3, 6.5, 11.0
GRAVITY, JUMP = 28.0, 8.6

VERT = """
attribute vec3 pos;
attribute vec2 uv;
attribute float shade;
uniform mat4 mvp;
uniform vec3 eye;
varying vec2 v_uv;
varying float v_shade;
varying float v_dist;
void main() {
    gl_Position = mvp * vec4(pos, 1.0);
    v_uv = uv;
    v_shade = shade;
    v_dist = distance(pos, eye);
}
"""
FRAG = """
uniform sampler2D atlas;
uniform vec3 fog;
uniform float fogStart;
uniform float fogEnd;
uniform float lines;
varying vec2 v_uv;
varying float v_shade;
varying float v_dist;
void main() {
    if (lines > 0.5) { gl_FragColor = vec4(0.0, 0.0, 0.0, 0.85); return; }
    vec4 c = texture2D(atlas, v_uv);
    if (c.a < 0.1) discard;
    vec3 rgb = c.rgb * v_shade;
    float f = clamp((v_dist - fogStart) / (fogEnd - fogStart), 0.0, 1.0);
    gl_FragColor = vec4(mix(rgb, fog, f), c.a);
}
"""


def craft_pixmap(size=32):
    """The program icon: a grass block, drawn in isometric."""
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    s = size / 32
    top = QPolygonF([QPointF(16 * s, 3 * s), QPointF(29 * s, 9.5 * s), QPointF(16 * s, 16 * s), QPointF(3 * s, 9.5 * s)])
    left = QPolygonF([QPointF(3 * s, 9.5 * s), QPointF(16 * s, 16 * s), QPointF(16 * s, 30 * s), QPointF(3 * s, 23.5 * s)])
    right = QPolygonF([QPointF(16 * s, 16 * s), QPointF(29 * s, 9.5 * s), QPointF(29 * s, 23.5 * s),
                       QPointF(16 * s, 30 * s)])
    p.setPen(QPen(QColor("#2A2A2A"), max(0.8, 0.8 * s)))
    p.setBrush(QColor("#6DB33F"))
    p.drawPolygon(top)
    p.setBrush(QColor("#8B6542"))
    p.drawPolygon(left)
    p.setBrush(QColor("#6E4F33"))
    p.drawPolygon(right)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#5A9A32"))
    p.drawPolygon(QPolygonF([QPointF(3 * s, 9.5 * s), QPointF(16 * s, 16 * s), QPointF(16 * s, 19 * s),
                             QPointF(3 * s, 12.5 * s)]))
    p.setBrush(QColor("#4A8228"))
    p.drawPolygon(QPolygonF([QPointF(16 * s, 16 * s), QPointF(29 * s, 9.5 * s), QPointF(29 * s, 12.5 * s),
                             QPointF(16 * s, 19 * s)]))
    p.end()
    return pm


def craft_icon():
    icon = QIcon()
    for sz in (16, 32, 48):
        icon.addPixmap(craft_pixmap(sz))
    return icon


class Chunk:
    def __init__(self):
        self.opaque = None
        self.water = None
        self.n_opaque = 0
        self.n_water = 0


class Game(QOpenGLWidget):
    def __init__(self, desktop):
        super().__init__()
        self.desktop = desktop
        self.frame = None
        fmt = QSurfaceFormat()
        fmt.setDepthBufferSize(24)
        self.setFormat(fmt)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMouseTracking(True)
        self.setMinimumSize(640, 400)
        self.state = "title"                # title, loading, playing, paused
        self.world = None
        self.chunks = {}
        self.dirty = []
        self.pos = [0.0, 40.0, 0.0]
        self.vel = [0.0, 0.0, 0.0]
        self.yaw, self.pitch = 0.0, 0.0
        self.on_ground = False
        self.flying = False
        self.keys = set()
        self.captured = False
        self.slot = 0
        self.target = (None, None)
        self.last = time.monotonic()
        self.last_space = 0.0
        self.fps = 0.0
        self.saved_at = time.monotonic()
        self.program = None
        self.atlas_img = W.atlas()
        self.hotbar_pix = [QPixmap.fromImage(W.tile_image(b, self.atlas_img)).scaled(
            32, 32, Qt.IgnoreAspectRatio, Qt.FastTransformation) for b in W.HOTBAR]
        self.buttons = []
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(16)

    # ---- OpenGL --------------------------------------------------------------------------------------------
    def initializeGL(self):
        self.gl = self.context().functions()
        self.program = QOpenGLShaderProgram(self)
        self.program.addShaderFromSourceCode(QOpenGLShader.Vertex, VERT)
        self.program.addShaderFromSourceCode(QOpenGLShader.Fragment, FRAG)
        self.program.bindAttributeLocation("pos", 0)
        self.program.bindAttributeLocation("uv", 1)
        self.program.bindAttributeLocation("shade", 2)
        self.program.link()
        self.texture = QOpenGLTexture(self.atlas_img.mirrored(False, False))
        self.texture.setMinificationFilter(QOpenGLTexture.Nearest)
        self.texture.setMagnificationFilter(QOpenGLTexture.Nearest)
        self.texture.setWrapMode(QOpenGLTexture.ClampToEdge)
        self.outline = QOpenGLBuffer(QOpenGLBuffer.VertexBuffer)
        self.outline.create()

    def _upload(self, data, buf=None):
        if buf is None:
            buf = QOpenGLBuffer(QOpenGLBuffer.VertexBuffer)
            buf.create()
        buf.bind()
        raw = data.tobytes()
        buf.allocate(raw, len(raw))
        buf.release()
        return buf

    def _build(self, cx, cz):
        opaque, water = self.world.mesh_chunk(cx, cz)
        ch = self.chunks.setdefault((cx, cz), Chunk())
        ch.opaque = self._upload(opaque, ch.opaque)
        ch.water = self._upload(water, ch.water)
        ch.n_opaque, ch.n_water = len(opaque) // 6, len(water) // 6

    def _draw_buffer(self, buf, count, mode=GL_TRIANGLES):
        if not count:
            return
        p = self.program
        buf.bind()
        p.enableAttributeArray(0)
        p.enableAttributeArray(1)
        p.enableAttributeArray(2)
        p.setAttributeBuffer(0, GL_FLOAT, 0, 3, STRIDE)
        p.setAttributeBuffer(1, GL_FLOAT, 12, 2, STRIDE)
        p.setAttributeBuffer(2, GL_FLOAT, 20, 1, STRIDE)
        self.gl.glDrawArrays(mode, 0, count)
        buf.release()

    def paintGL(self):
        gl = self.gl
        gl.glClearColor(SKY.redF(), SKY.greenF(), SKY.blueF(), 1.0)
        gl.glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        if self.state in ("playing", "paused") and self.world is not None:
            gl.glEnable(GL_DEPTH_TEST)
            gl.glDisable(GL_CULL_FACE)
            p = self.program
            p.bind()
            self.texture.bind(0)
            p.setUniformValue1i(p.uniformLocation("atlas"), 0)
            p.setUniformValue(p.uniformLocation("mvp"), self._mvp())
            eye = QVector3D(self.pos[0], self.pos[1] + EYE, self.pos[2])
            p.setUniformValue(p.uniformLocation("eye"), eye)
            p.setUniformValue(p.uniformLocation("fog"), QVector3D(*FOG))
            p.setUniformValue1f(p.uniformLocation("fogStart"), 40.0)
            p.setUniformValue1f(p.uniformLocation("fogEnd"), 90.0)
            p.setUniformValue1f(p.uniformLocation("lines"), 0.0)
            for ch in self.chunks.values():
                self._draw_buffer(ch.opaque, ch.n_opaque)
            gl.glEnable(GL_BLEND)
            gl.glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            gl.glDepthMask(False)
            for ch in self.chunks.values():
                self._draw_buffer(ch.water, ch.n_water)
            gl.glDepthMask(True)
            hit = self.target[0]
            if hit is not None:
                p.setUniformValue1f(p.uniformLocation("lines"), 1.0)
                self._draw_buffer(self._upload(self._outline_lines(hit), self.outline), 24, GL_LINES)
            gl.glDisable(GL_BLEND)
            self.texture.release()
            p.release()
            gl.glDisable(GL_DEPTH_TEST)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        self._hud(painter)
        painter.end()

    def _mvp(self):
        proj = QMatrix4x4()
        proj.perspective(70.0, max(1, self.width()) / max(1, self.height()), 0.05, 200.0)
        view = QMatrix4x4()
        view.rotate(-self.pitch, 1, 0, 0)
        view.rotate(-self.yaw, 0, 1, 0)
        view.translate(-self.pos[0], -(self.pos[1] + EYE), -self.pos[2])
        return proj * view

    def _outline_lines(self, hit):
        x, y, z = hit
        e = 0.003
        c = [(x - e, y - e, z - e), (x + 1 + e, y - e, z - e), (x + 1 + e, y - e, z + 1 + e), (x - e, y - e, z + 1 + e),
             (x - e, y + 1 + e, z - e), (x + 1 + e, y + 1 + e, z - e), (x + 1 + e, y + 1 + e, z + 1 + e),
             (x - e, y + 1 + e, z + 1 + e)]
        out = array("f")
        for a, b in ((0, 1), (1, 2), (2, 3), (3, 0), (4, 5), (5, 6), (6, 7), (7, 4), (0, 4), (1, 5), (2, 6), (3, 7)):
            out.extend(c[a] + (0.0, 0.0, 1.0))
            out.extend(c[b] + (0.0, 0.0, 1.0))
        return out

    # ---- the HUD and menus ------------------------------------------------------------------------------------
    def _hud(self, p):
        w, h = self.width(), self.height()
        self.buttons = []
        if self.state == "title":
            self._dirt_background(p)
            self._logo(p, h * 0.22)
            has_save = SAVE.exists()
            labels = (["Continue World"] if has_save else []) + ["New World", "Quit Game"]
            for i, label in enumerate(labels):
                self._button(p, label, QRect(w // 2 - 150, int(h * 0.45) + i * 50, 300, 40))
            p.setPen(QColor("#E0E0E0"))
            p.setFont(QFont("Tahoma", 9))
            p.drawText(QRect(0, h - 70, w, 60), Qt.AlignCenter,
                       "WASD walk  -  mouse look  -  Space jump (twice to fly)  -  Ctrl sprint  -  left click break  -  "
                       "right click place\n1-9 or the mouse wheel pick a block  -  Esc pauses")
            return
        if self.state == "loading":
            self._dirt_background(p)
            done = sum(1 for c in self.chunks.values() if c.opaque is not None)
            total = W.CHUNKS * W.CHUNKS
            p.setPen(QColor("white"))
            p.setFont(QFont("Tahoma", 14, QFont.Bold))
            p.drawText(QRect(0, h // 2 - 50, w, 30), Qt.AlignCenter, "Building terrain")
            p.fillRect(QRect(w // 2 - 150, h // 2, 300, 8), QColor("#404040"))
            p.fillRect(QRect(w // 2 - 150, h // 2, int(300 * done / total), 8), QColor("#7FD46A"))
            return
        # crosshair
        p.setPen(QPen(QColor(255, 255, 255, 220), 2))
        p.drawLine(w // 2 - 9, h // 2, w // 2 + 9, h // 2)
        p.drawLine(w // 2, h // 2 - 9, w // 2, h // 2 + 9)
        # hotbar
        slot_w = 44
        x0 = w // 2 - slot_w * len(W.HOTBAR) // 2
        y0 = h - slot_w - 10
        p.fillRect(QRect(x0 - 4, y0 - 4, slot_w * len(W.HOTBAR) + 8, slot_w + 8), QColor(0, 0, 0, 130))
        for i, pix in enumerate(self.hotbar_pix):
            r = QRect(x0 + i * slot_w, y0, slot_w, slot_w)
            p.setPen(QPen(QColor("#FFFFFF") if i == self.slot else QColor("#808080"), 3 if i == self.slot else 1))
            p.drawRect(r.adjusted(1, 1, -1, -1))
            p.drawPixmap(r.x() + 6, r.y() + 6, pix)
        p.setFont(QFont("Tahoma", 10, QFont.Bold))
        p.setPen(QColor("white"))
        p.drawText(QRect(0, y0 - 26, w, 20), Qt.AlignCenter, W.NAMES[W.HOTBAR[self.slot]])
        p.setFont(QFont("Tahoma", 8))
        p.setPen(QColor(255, 255, 255, 220))
        p.drawText(8, 16, f"ClaudeCraft  {self.fps:.0f} fps   XYZ {self.pos[0]:.1f} / {self.pos[1]:.1f} / "
                          f"{self.pos[2]:.1f}" + ("   (flying)" if self.flying else ""))
        if self.state == "playing" and not self.captured:
            p.drawText(QRect(0, h // 2 + 20, w, 20), Qt.AlignCenter, "Click to play")
        if self.state == "paused":
            p.fillRect(self.rect(), QColor(0, 0, 0, 120))
            p.setPen(QColor("white"))
            p.setFont(QFont("Tahoma", 16, QFont.Bold))
            p.drawText(QRect(0, int(h * 0.22), w, 40), Qt.AlignCenter, "Game Menu")
            for i, label in enumerate(("Back to Game", "Save and Quit to Title")):
                self._button(p, label, QRect(w // 2 - 150, int(h * 0.38) + i * 50, 300, 40))

    def _dirt_background(self, p):
        dirt = QPixmap.fromImage(W.tile_image(W.DIRT, self.atlas_img)).scaled(64, 64)
        p.drawTiledPixmap(self.rect(), dirt)
        p.fillRect(self.rect(), QColor(0, 0, 0, 110))

    def _logo(self, p, y):
        f = QFont("Arial Black", 40)
        f.setBold(True)
        p.setFont(f)
        r = QRect(0, int(y) - 40, self.width(), 80)
        p.setPen(QColor("#202020"))
        p.drawText(r.translated(4, 4), Qt.AlignCenter, "ClaudeCraft")
        g = QLinearGradient(0, r.top(), 0, r.bottom())
        g.setColorAt(0, QColor("#E8E8E8"))
        g.setColorAt(1, QColor("#8A8A8A"))
        p.setPen(QPen(g, 1))
        p.drawText(r, Qt.AlignCenter, "ClaudeCraft")
        p.setFont(QFont("Tahoma", 11, QFont.Bold))
        p.setPen(QColor("#FFFF55"))
        p.save()
        p.translate(self.width() / 2 + 190, y + 26)
        p.rotate(-18)
        p.drawText(QRect(-110, -14, 220, 28), Qt.AlignCenter, "Now on Windows XP!")
        p.restore()

    def _button(self, p, label, rect):
        hover = rect.contains(self.mapFromGlobal(QCursor.pos()))
        p.fillRect(rect, QColor("#7C7C7C") if not hover else QColor("#8C96C8"))
        p.setPen(QPen(QColor("#000000"), 2))
        p.drawRect(rect)
        p.setPen(QColor("#FFFFFF"))
        p.setFont(QFont("Tahoma", 11, QFont.Bold))
        p.drawText(rect, Qt.AlignCenter, label)
        self.buttons.append((rect, label))

    def _menu_click(self, pos):
        for rect, label in self.buttons:
            if rect.contains(pos):
                if label == "Continue World":
                    self.start(load=True)
                elif label == "New World":
                    self.start(load=False)
                elif label == "Quit Game":
                    if self.frame:
                        self.frame.request_close()
                elif label == "Back to Game":
                    self.state = "playing"
                    self._capture(True)
                elif label == "Save and Quit to Title":
                    self.save()
                    self.state = "title"
                    self._capture(False)
                return True
        return False

    # ---- starting a world ---------------------------------------------------------------------------------------
    def start(self, load):
        import json
        self.state = "loading"
        self.update()
        data = None
        if load and SAVE.exists():
            try:
                data = json.loads(SAVE.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                data = None
        self.world = W.World.from_json(data) if data else W.World()
        QTimer.singleShot(30, lambda: self._generate(data))

    def _generate(self, data):
        self.world.generate()
        if data and data.get("player"):
            px, py, pz, self.yaw, self.pitch = data["player"][:5]
            self.pos = [px, py, pz]
            self.slot = int(data["player"][5]) if len(data["player"]) > 5 else 0
        else:
            self.pos = list(self.world.spawn())
            self.yaw, self.pitch = 45.0, -10.0
        self.vel = [0.0, 0.0, 0.0]
        self.flying = False
        self.makeCurrent()
        for ch in self.chunks.values():
            for buf in (ch.opaque, ch.water):
                if buf is not None:
                    buf.destroy()
        self.chunks = {}
        pcx, pcz = int(self.pos[0]) // W.CHUNK, int(self.pos[2]) // W.CHUNK
        self.pending = sorted(((cx, cz) for cx in range(W.CHUNKS) for cz in range(W.CHUNKS)),
                              key=lambda c: (c[0] - pcx) ** 2 + (c[1] - pcz) ** 2)
        for c in self.pending:
            self.chunks[c] = Chunk()
        self.doneCurrent()

    def save(self):
        if self.world is not None:
            W.save_json(SAVE, self.world, [*self.pos, self.yaw, self.pitch, self.slot])
            self.saved_at = time.monotonic()

    # ---- the loop -------------------------------------------------------------------------------------------------
    def _tick(self):
        now = time.monotonic()
        dt = min(0.05, now - self.last)
        self.last = now
        if dt > 0:
            self.fps = self.fps * 0.9 + (1 / dt) * 0.1
        if self.state == "loading" and getattr(self, "pending", None) is not None:
            self.makeCurrent()
            t0 = time.monotonic()
            while self.pending and time.monotonic() - t0 < 0.04:
                self._build(*self.pending.pop(0))
            self.doneCurrent()
            if not self.pending:
                self.pending = None
                self.state = "playing"
        elif self.state == "playing":
            self._physics(dt)
            self.target = self.world.raycast(self._eye(), self._look())
            if self.dirty:
                self.makeCurrent()
                for c in set(self.dirty):
                    self._build(*c)
                self.dirty = []
                self.doneCurrent()
            if now - self.saved_at > 60:
                self.save()
        self.update()

    def _eye(self):
        return (self.pos[0], self.pos[1] + EYE, self.pos[2])

    def _look(self):
        y, p = math.radians(self.yaw), math.radians(self.pitch)
        return (-math.sin(y) * math.cos(p), math.sin(p), -math.cos(y) * math.cos(p))

    def _physics(self, dt):
        y = math.radians(self.yaw)
        fwd = (-math.sin(y), -math.cos(y))
        right = (math.cos(y), -math.sin(y))
        mx = mz = 0.0
        k = self.keys
        if Qt.Key_W in k:
            mx += fwd[0]
            mz += fwd[1]
        if Qt.Key_S in k:
            mx -= fwd[0]
            mz -= fwd[1]
        if Qt.Key_D in k:
            mx += right[0]
            mz += right[1]
        if Qt.Key_A in k:
            mx -= right[0]
            mz -= right[1]
        n = math.hypot(mx, mz)
        speed = FLY if self.flying else (SPRINT if Qt.Key_Control in k else WALK)
        in_water = self.world.get(int(math.floor(self.pos[0])), int(math.floor(self.pos[1] + 0.5)),
                                  int(math.floor(self.pos[2]))) == W.WATER
        if in_water and not self.flying:
            speed *= 0.55
        if n:
            mx, mz = mx / n * speed, mz / n * speed
        self.vel[0], self.vel[2] = mx, mz
        if self.flying:
            self.vel[1] = (FLY * 0.8 if Qt.Key_Space in k else 0) - (FLY * 0.8 if Qt.Key_Shift in k else 0)
        else:
            self.vel[1] -= GRAVITY * dt * (0.3 if in_water else 1)
            if in_water:
                self.vel[1] = max(self.vel[1], -3.0)
                if Qt.Key_Space in k:
                    self.vel[1] = 3.5
            elif Qt.Key_Space in k and self.on_ground:
                self.vel[1] = JUMP
        self.on_ground = False
        for axis in (0, 2, 1):
            self.pos[axis] += self.vel[axis] * dt
            if self._collides():
                self.pos[axis] -= self.vel[axis] * dt
                if axis == 1:
                    if self.vel[1] < 0:
                        self.on_ground = True
                        if self.flying:
                            self.flying = False
                    self.vel[1] = 0.0
        if self.pos[1] < -10:                  # fell off the world
            self.pos = list(self.world.spawn())

    def _collides(self):
        x, y, z = self.pos
        r = 0.3
        for bx in range(int(math.floor(x - r)), int(math.floor(x + r)) + 1):
            for by in range(int(math.floor(y)), int(math.floor(y + 1.8)) + 1):
                for bz in range(int(math.floor(z - r)), int(math.floor(z + r)) + 1):
                    if self.world.get(bx, by, bz) in W.SOLID:
                        return True
        return False

    def _changed(self, x, z):
        cx, cz = x // W.CHUNK, z // W.CHUNK
        self.dirty.append((cx, cz))
        for nx, nz in ((x - 1, z), (x + 1, z), (x, z - 1), (x, z + 1)):
            ncx, ncz = nx // W.CHUNK, nz // W.CHUNK
            if (ncx, ncz) != (cx, cz) and (ncx, ncz) in self.chunks:
                self.dirty.append((ncx, ncz))

    # ---- input ------------------------------------------------------------------------------------------------------
    def _capture(self, on):
        self.captured = on
        if on:
            self.setCursor(Qt.BlankCursor)
            QCursor.setPos(self.mapToGlobal(self.rect().center()))
            self.setFocus()
        else:
            self.unsetCursor()
            self.keys.clear()

    def mousePressEvent(self, e):
        if self.state in ("title", "paused"):
            self._menu_click(e.position().toPoint())
            return
        if self.state != "playing":
            return
        if not self.captured:
            self._capture(True)
            return
        hit, before = self.target
        if e.button() == Qt.LeftButton and hit is not None:
            if self.world.get(*hit) != W.BEDROCK:
                self.world.set(*hit, W.AIR)
                self._changed(hit[0], hit[2])
        elif e.button() == Qt.RightButton and before is not None:
            block = W.HOTBAR[self.slot]
            self.world.set(*before, block)
            if self._collides():                         # don't build inside yourself
                self.world.set(*before, W.AIR)
            else:
                self._changed(before[0], before[2])

    def mouseMoveEvent(self, e):
        if not self.captured:
            self.update()
            return
        center = self.rect().center()
        d = e.position().toPoint() - center
        if d.manhattanLength() == 0:
            return
        self.yaw = (self.yaw - d.x() * 0.15) % 360
        self.pitch = max(-89.0, min(89.0, self.pitch - d.y() * 0.15))
        QCursor.setPos(self.mapToGlobal(center))

    def wheelEvent(self, e):
        if self.state == "playing":
            self.slot = (self.slot + (1 if e.angleDelta().y() < 0 else -1)) % len(W.HOTBAR)

    def keyPressEvent(self, e):
        if e.isAutoRepeat():
            return
        if e.key() == Qt.Key_Escape:
            if self.state == "playing":
                self.state = "paused"
                self._capture(False)
            elif self.state == "paused":
                self.state = "playing"
                self._capture(True)
            return
        if self.state != "playing":
            return
        if Qt.Key_1 <= e.key() <= Qt.Key_9:
            self.slot = e.key() - Qt.Key_1
            return
        if e.key() == Qt.Key_Space:
            now = time.monotonic()
            if now - self.last_space < 0.3:
                self.flying = not self.flying
                self.vel[1] = 0.0
            self.last_space = now
        if e.key() == Qt.Key_F:
            self.flying = not self.flying
        self.keys.add(e.key())

    def keyReleaseEvent(self, e):
        if not e.isAutoRepeat():
            self.keys.discard(e.key())

    def focusOutEvent(self, e):
        if self.captured:
            self._capture(False)
        super().focusOutEvent(e)

    def shutdown(self):
        if self.state in ("playing", "paused"):
            self.save()
        self.timer.stop()

    def closeEvent(self, e):
        self.shutdown()
        super().closeEvent(e)


_open = {}


def launch(desktop):
    win = _open.get("win")
    if win is not None and isValid(win):
        desktop.open_window(win)
        return win
    body = Game(desktop)
    win = host.window(desktop, "ClaudeCraft", body, craft_icon(), size=(880, 540))
    body.frame = win
    _open["win"] = win
    desktop.open_window(win)
    return win


def shutdown():
    win = _open.get("win")
    if win is not None and isValid(win):
        win.content.shutdown()

