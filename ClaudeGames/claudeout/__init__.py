"""Claudeout 4: a first-person game after the opening of Fallout 4, in two parts.

Part One - Out of the Vault: you wake in a cryo pod in Vault 111. Find your way through the vault - the radroaches
have had the run of it - pick up a weapon, unlock the way with the terminals, take the Pip-Boy from the skeleton by
the door, open the great gear door and ride the elevator up.
Part Two - The Neighbourhood: down the hill to Serenity Hills, the old cul-de-sac two centuries after the bombs.
Your house is still standing, more or less; so is the robot who kept it, and he has an errand for you before he
points you at the bridge out of town.

WASD walk, mouse look (click to capture the mouse, Esc to let go), Shift sprint, left click attack, E use / pick up
/ loot / talk, 1-3 weapons, Q stimpak, Tab the Pip-Boy (once you have it; eat and heal from its INV tab - meat heals
but gives you rads, which eat into your health until RadAway clears them). Three save slots; it saves as it goes.

Drawn with OpenGL through Qt, like ClaudeCraft: the vault is in vault.py, the surface in surface.py, what changes in
world.py, the textures in art.py, the soundscape in sound.py."""
import json
import math
import time
from array import array

from PySide6.QtCore import QPointF, QRect, QRectF, Qt, QTimer
from PySide6.QtGui import (QColor, QCursor, QFont, QIcon, QLinearGradient, QMatrix4x4, QPainter, QPainterPath, QPen,
                           QPixmap, QPolygonF, QRadialGradient, QSurfaceFormat, QVector3D, QVector4D)
from PySide6.QtOpenGL import QOpenGLBuffer, QOpenGLShader, QOpenGLShaderProgram, QOpenGLTexture
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from shiboken6 import isValid

from claudecore import host

from . import art
from . import surface as S
from . import vault as V
from .sound import Audio
from .world import AID, ITEM_NAMES, KINDS, OBJECTIVES, PLAYER_HP, QUESTS, WEAPONS, World

TITLE = "Claudeout 4"
GL_DEPTH_TEST, GL_BLEND, GL_CULL_FACE = 0x0B71, 0x0BE2, 0x0B44
GL_TRIANGLES, GL_FLOAT = 0x0004, 0x1406
GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT = 0x4000, 0x0100
STRIDE = 6 * 4
EYE = 1.6
WALK, SPRINT = 3.1, 5.0
FOG = {"vault": ((0.015, 0.018, 0.022), 6.0, 26.0), "surface": ((0.64, 0.60, 0.46), 24.0, 80.0)}
SUN = QVector3D(0.55, 0.42, -0.72).normalized()
GREEN = "#36E07A"
AMBER = "#F2C14E"
SLOTS = 3
PIP_TABS = ["STAT", "INV", "DATA", "MAP", "RADIO"]
SPECIAL = [("Strength", 4), ("Perception", 5), ("Endurance", 4), ("Charisma", 6), ("Intelligence", 5),
           ("Agility", 4), ("Luck", 3)]
MAP_COLOURS = {"g": (60, 95, 50), "d": (115, 88, 55), "r": (75, 75, 80), "p": (120, 120, 110), "c": (130, 130, 120),
               "w": (45, 85, 115), "b": (120, 90, 50), "k": (85, 80, 72), "f": (165, 130, 60), "e": (210, 200, 80)}

VERT = """
attribute vec3 pos;
attribute vec2 uv;
attribute float shade;
uniform mat4 mvp;
uniform vec3 eye;
uniform vec3 offset;
varying vec2 v_uv;
varying float v_shade;
varying float v_dist;
void main() {
    vec3 p = pos + offset;
    gl_Position = mvp * vec4(p, 1.0);
    v_uv = uv;
    v_shade = shade;
    v_dist = distance(p, eye);
}
"""
FRAG = """
uniform sampler2D atlas;
uniform vec3 fog;
uniform float fogStart;
uniform float fogEnd;
varying vec2 v_uv;
varying float v_shade;
varying float v_dist;
void main() {
    vec4 c = texture2D(atlas, v_uv);
    if (c.a < 0.15) discard;
    vec3 rgb = c.rgb * v_shade;
    float f = clamp((v_dist - fogStart) / (fogEnd - fogStart), 0.0, 1.0);
    gl_FragColor = vec4(mix(rgb, fog, f), 1.0);
}
"""


def out_icon(size=32):
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    s = size / 32
    p.setPen(QPen(QColor("#1A1E22"), max(1.0, s)))
    g = QRadialGradient(QPointF(16 * s, 16 * s), 15 * s)
    g.setColorAt(0, QColor("#8A949C"))
    g.setColorAt(1, QColor("#3A4248"))
    p.setBrush(g)
    path = QPainterPath()
    for k in range(24):
        a = k * math.pi / 12
        rad = (15 if k % 2 == 0 else 12) * s
        pt = QPointF(16 * s + math.cos(a) * rad, 16 * s + math.sin(a) * rad)
        path.moveTo(pt) if k == 0 else path.lineTo(pt)
    path.closeSubpath()
    p.drawPath(path)
    p.setBrush(QColor(AMBER))
    p.drawEllipse(QPointF(16 * s, 16 * s), 8 * s, 8 * s)
    f = QFont("Arial Black")
    f.setPixelSize(int(8 * s))
    p.setFont(f)
    p.setPen(QColor("#1E1E1E"))
    p.drawText(QRectF(4 * s, 4 * s, 24 * s, 24 * s), Qt.AlignCenter, "111")
    p.end()
    return QIcon(pm)


def _font(size, bold=True, family="Consolas"):
    f = QFont(family)
    f.setPixelSize(size)
    f.setBold(bold)
    return f


def _mins(secs):
    return f"{int(secs // 60)} min {int(secs % 60)} s"


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
        self.setMinimumSize(800, 500)
        self.settings = self._load("settings.json") or {}
        self.music_on = self.settings.get("music", True)
        self.sfx_on = self.settings.get("sfx", True)
        self.audio = Audio(self, self.music_on, self.sfx_on)
        # title, slots, intro, card, intro2, playing, paused, pipboy, terminal, talk, dead, end
        self.state = "title"
        self.world = None
        self.slot = 1
        self.slot_purpose = "new"
        self.pos = [V.START[0], V.START[1]]
        self.yaw, self.pitch = V.START[2], 0.0
        self.keys = set()
        self.captured = False
        self.buttons = []
        self.program = None
        self.atlas_img = art.atlas()
        self.static = None
        self.n_static = 0
        self.area_built = None
        self.doors = {}                      # id -> (buffer, count)
        self.bill = None
        self.last = time.monotonic()
        self.t = 0.0
        self.fps = 0.0
        self.intro_t = 0.0
        self.swing = 0.0
        self.cooldown = 0.0
        self.flash = 0.0
        self.hurt = 0.0
        self.bob = 0.0
        self.step_t = 0.0
        self.step_k = 0
        self.message = None                  # (text, until)
        self.objective_at = 0.0
        self.pip_tab = 0
        self.radio = False
        self.terminal = None                 # [id, selected, typed, reply]
        self.talk = None                     # [node, selected, typed]
        self.cards = []                      # [(title, lines, seconds)]
        self.card_t = 0.0
        self.after_cards = None
        self.checkpoint = None
        self.end_t = 0.0
        self.buzz_at = 0.0
        self.saved_at = time.monotonic()
        self.map_pix = None
        self.map_key = None
        self.map_seen = {"vault": set(), "surface": set()}
        self.map_done = {"vault": set(), "surface": set()}
        self.timer = QTimer(self)
        self.timer.setTimerType(Qt.PreciseTimer)
        self.timer.timeout.connect(self._tick)
        self.timer.start(16)

    # ---- saving: three slots ----
    def _load(self, name):
        try:
            return json.loads((host.saves(TITLE) / name).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None

    def _write(self, name, data):
        try:
            path = host.saves(TITLE) / name
            if data is None:
                path.unlink(missing_ok=True)
            else:
                path.write_text(json.dumps(data), encoding="utf-8")
        except OSError:
            pass

    def slot_meta(self, n):
        d = self._load(f"slot{n}.json")
        return d.get("meta") if isinstance(d, dict) else None

    def latest_slot(self):
        best, when = None, ""
        for n in range(1, SLOTS + 1):
            m = self.slot_meta(n)
            if m and m.get("saved", "") > when:
                best, when = n, m["saved"]
        return best

    def save_slot(self, n=None):
        if self.world is None:
            return
        n = n or self.slot
        self.slot = n
        w = self.world
        meta = {"part": w.part(), "objective": w.goal_text(), "time": round(w.time), "hp": w.hp, "area": w.area,
                "saved": time.strftime("%Y-%m-%d %H:%M:%S"), "done": w.goal() == "done"}
        self._write(f"slot{n}.json", {"world": w.to_json(), "pos": [*self.pos, self.yaw, self.pitch],
                                      "checkpoint": self.checkpoint, "radio": self.radio, "meta": meta})
        self.saved_at = time.monotonic()

    def _save_settings(self):
        self._write("settings.json", {"music": self.music_on, "sfx": self.sfx_on})

    def _mark_checkpoint(self):
        self.checkpoint = {"world": self.world.to_json(), "pos": [*self.pos, self.yaw, self.pitch]}

    # ---- OpenGL ----
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
        self.bill = QOpenGLBuffer(QOpenGLBuffer.VertexBuffer)
        self.bill.create()
        if self.world is not None:
            self.area_built = None
            self._build_area()

    def _upload(self, data, buf=None):
        if buf is None:
            buf = QOpenGLBuffer(QOpenGLBuffer.VertexBuffer)
            buf.create()
        buf.bind()
        raw = data.tobytes()
        buf.allocate(raw, len(raw))
        buf.release()
        return buf

    def _build_area(self):
        """The meshes of wherever you are (the context must be current)."""
        area = self.world.area
        mesh = V.static_mesh() if area == "vault" else S.static_mesh()
        self.static = self._upload(mesh, self.static)
        self.n_static = len(mesh) // 6
        if area == "vault" and not self.doors:
            for did in V.DOORS:
                m = V.door_mesh(did)
                self.doors[did] = (self._upload(m), len(m) // 6)
        self.area_built = area
        self.map_pix = None

    def _ensure_area(self):
        if self.world is not None and self.area_built != self.world.area and self.program is not None:
            self.makeCurrent()
            self._build_area()
            self.doneCurrent()

    def _draw_buffer(self, buf, count):
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
        self.gl.glDrawArrays(GL_TRIANGLES, 0, count)
        buf.release()

    def _ground(self, x, z):
        return self.world.height(x, z) if self.world is not None else 0.0

    def _eye_y(self):
        y = self._ground(*self.pos) + EYE + math.sin(self.bob) * 0.04
        w = self.world
        if w is not None and w.area == "vault" and w.elevator is not None:
            y += max(0.0, w.elevator - 1.0) * 1.2
        return y

    def _mvp(self):
        proj = QMatrix4x4()
        proj.perspective(72.0, max(1, self.width()) / max(1, self.height()), 0.05, 160.0)
        view = QMatrix4x4()
        view.rotate(-self.pitch, 1, 0, 0)
        view.rotate(-self.yaw, 0, 1, 0)
        view.translate(-self.pos[0], -self._eye_y(), -self.pos[1])
        return proj * view

    def _door_offset(self, did):
        k = self.world.doors[did]
        if V.DOORS[did][1] == "gear":
            push = min(1.0, k / 0.25) * 0.9
            roll = max(0.0, (k - 0.25) / 0.75) * 5.6
            return QVector3D(push, 0.0, roll)
        return QVector3D(0.0, k * 2.75, 0.0)

    def _billboards(self):
        """Quads facing the camera: creatures, items, the skeleton and the pod's figure, the robot, the marker."""
        w = self.world
        yaw = math.radians(self.yaw)
        rx, rz = math.cos(yaw), -math.sin(yaw)
        buf = array("f")

        def sprite(name, x, y, z, width, height, shade=1.0):
            u0, v0, u1, v1 = art.uv(name)
            a = (x - rx * width / 2, y, z - rz * width / 2)
            b = (x + rx * width / 2, y, z + rz * width / 2)
            c = (x + rx * width / 2, y + height, z + rz * width / 2)
            d = (x - rx * width / 2, y + height, z - rz * width / 2)
            for pt, uu in ((a, (u0, v1)), (b, (u1, v1)), (c, (u1, v0)), (a, (u0, v1)), (c, (u1, v0)), (d, (u0, v0))):
                buf.extend(pt)
                buf.extend(uu)
                buf.append(shade)

        for c in w.creatures:
            if c.area != w.area:
                continue
            k = KINDS[c.kind]
            g = self._ground(c.x, c.z)
            if c.alive:
                if k["fly"]:
                    y = g + 1.1 + math.sin(self.t * 5 + c.wobble) * 0.25
                else:
                    y = g + (abs(math.sin(self.t * 9 + c.wobble)) * 0.05 if c.aggro else 0.0)
                sprite(c.kind, c.x, y, c.z, k["w"], k["h"], 1.9 if c.hurt > 0 else 1.0)
            else:
                sprite(f"{c.kind}_dead", c.x, g + 0.01, c.z, k["w"], k["h"] * 0.7, 0.8)
        for kind, x, z in w.items[w.area].values():
            y = self._rest_height(x, z) + 0.05 + math.sin(self.t * 2 + x) * 0.03
            sprite(kind, x, y, z, 0.5, 0.5, 1.1)
        if w.area == "vault":
            sx, sz = V.SKELETON
            sprite("skeleton", sx, 0.0, sz, 0.85, 1.1, 0.95)
            sp = V.SPOUSE_POD
            sprite("spouse", sp[0] + 0.5, 0.3, sp[1] + 1.06, 0.5, 1.5, 0.9)
        else:
            rx_, rz_ = S.ROBOT
            sprite("robot", rx_, self._ground(rx_, rz_) + 0.7 + math.sin(self.t * 1.7) * 0.12, rz_, 1.6, 1.6, 1.0)
        target = w.target()
        if target is not None and self.state == "playing":
            tx, tz = target
            if math.hypot(tx - self.pos[0], tz - self.pos[1]) > 2.5:
                sprite("marker", tx, self._ground(tx, tz) + 2.1 + math.sin(self.t * 3) * 0.12, tz, 0.45, 0.45, 1.3)
        return buf

    def _rest_height(self, x, z):
        base = self._ground(x, z)
        boxes = V.BOXES if self.world.area == "vault" else S.BOXES
        for b in boxes:
            x0, z0, x1, z1, h = b[:5]
            if x0 <= x <= x1 and z0 <= z <= z1 and (len(b) < 8 or b[7] < 1.0):
                return base + h
        return base

    def paintGL(self):
        gl = self.gl
        w = self.world
        area = w.area if w is not None else "vault"
        fog, f0, f1 = FOG[area]
        gl.glClearColor(*fog, 1.0)
        gl.glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        if w is not None and self.static is not None and self.area_built == area and self.state not in ("title", "slots"):
            gl.glEnable(GL_DEPTH_TEST)
            gl.glDisable(GL_CULL_FACE)
            p = self.program
            p.bind()
            self.texture.bind(0)
            p.setUniformValue1i(p.uniformLocation("atlas"), 0)
            p.setUniformValue(p.uniformLocation("mvp"), self._mvp())
            p.setUniformValue(p.uniformLocation("eye"), QVector3D(self.pos[0], self._eye_y(), self.pos[1]))
            p.setUniformValue(p.uniformLocation("fog"), QVector3D(*fog))
            p.setUniformValue1f(p.uniformLocation("fogStart"), f0)
            p.setUniformValue1f(p.uniformLocation("fogEnd"), f1)
            p.setUniformValue(p.uniformLocation("offset"), QVector3D(0, 0, 0))
            self._draw_buffer(self.static, self.n_static)
            if area == "vault":
                for did, (buf, n) in self.doors.items():
                    p.setUniformValue(p.uniformLocation("offset"), self._door_offset(did))
                    self._draw_buffer(buf, n)
                p.setUniformValue(p.uniformLocation("offset"), QVector3D(0, 0, 0))
            bb = self._billboards()
            if bb:
                self._upload(bb, self.bill)
                self._draw_buffer(self.bill, len(bb) // 6)
            self.texture.release()
            p.release()
            gl.glDisable(GL_DEPTH_TEST)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)
        self._overlay(painter)
        painter.end()

    # ---- the overlay ----
    def _overlay(self, p):
        w, h = self.width(), self.height()
        self.buttons = []
        if self.state == "title":
            self._title(p)
            return
        if self.state == "slots":
            self._slots(p)
            return
        wd = self.world
        if wd.area == "surface" and self.state != "card":
            self._sun(p)
        if self.state == "intro":
            self._weapon_view(p)
            k = self.intro_t
            white = 1.0 if k < 2.0 else max(0.0, 1 - (k - 2.0) / 2.5)
            p.fillRect(self.rect(), QColor(235, 245, 255, int(255 * white)))
            if k < 3.2:
                a = int(255 * min(1.0, k / 0.6) * (1.0 if k < 2.2 else max(0.0, 1 - (k - 2.2))))
                p.setFont(_font(22))
                p.setPen(QColor(40, 60, 80, a))
                p.drawText(QRect(0, h // 2 - 60, w, 40), Qt.AlignCenter, "VAULT 111")
                p.setFont(_font(14, False))
                p.drawText(QRect(0, h // 2 - 10, w, 30), Qt.AlignCenter, "Cryogenic stasis: ending.")
                p.drawText(QRect(0, h // 2 + 20, w, 30), Qt.AlignCenter, "Elapsed: 210 years, 0 months, 23 days.")
            self._frost(p, min(1.0, max(0.0, 1 - (k - 1.5) / 4.0)))
            return
        if self.state == "card":
            self._card(p)
            return
        if self.state == "intro2":
            self._weapon_view(p)
            p.fillRect(self.rect(), QColor(255, 250, 235, int(255 * max(0.0, 1 - self.intro_t / 2.8))))
            return
        self._weapon_view(p)
        if self.hurt > 0:
            self._vignette(p, QColor(200, 20, 20), self.hurt)
        if wd.hp < 30:
            self._vignette(p, QColor(200, 20, 20), 0.25 + 0.15 * math.sin(self.t * 6))
        # crosshair
        p.setPen(QPen(QColor(GREEN), 2))
        c = QPointF(w / 2, h / 2)
        p.drawLine(c + QPointF(-8, 0), c + QPointF(-3, 0))
        p.drawLine(c + QPointF(3, 0), c + QPointF(8, 0))
        p.drawLine(c + QPointF(0, -8), c + QPointF(0, -3))
        p.drawLine(c + QPointF(0, 3), c + QPointF(0, 8))
        # HP (with the rads eating into it), aid, the weapon
        p.fillRect(QRect(18, h - 44, 250, 26), QColor(0, 0, 0, 140))
        p.setFont(_font(13))
        p.setPen(QColor(GREEN))
        p.drawText(QRect(24, h - 44, 40, 26), Qt.AlignVCenter, "HP")
        p.fillRect(QRect(58, h - 37, 200, 12), QColor(20, 40, 28))
        p.fillRect(QRect(58, h - 37, int(200 * max(0, wd.hp) / PLAYER_HP), 12), QColor(GREEN))
        if wd.rads:
            p.fillRect(QRect(58 + int(200 * wd.max_hp() / PLAYER_HP), h - 37, int(200 * wd.rads / PLAYER_HP), 12),
                       QColor("#C0402A"))
            p.setPen(QColor("#F08060"))
            p.drawText(QRect(18, h - 70, 250, 22), Qt.AlignLeft | Qt.AlignVCenter, f"RADS {wd.rads}")
        p.setPen(QColor(GREEN))
        stims = wd.aid.get("stimpak", 0)
        if stims:
            p.drawText(QRect(18, h - 94 if wd.rads else h - 70, 250, 22), Qt.AlignLeft | Qt.AlignVCenter,
                       f"Stimpaks {stims}  (Q)")
        name = WEAPONS[wd.weapon][0]
        p.fillRect(QRect(w - 248, h - 44, 230, 26), QColor(0, 0, 0, 140))
        p.drawText(QRect(w - 242, h - 44, 220, 26), Qt.AlignRight | Qt.AlignVCenter,
                   f"{name}" + (f"   {wd.ammo} rounds" if wd.weapon == "pistol" else ""))
        # the objective, and how far
        p.setFont(_font(12))
        since = self.t - self.objective_at
        glow = 1.0 if since > 3 else 0.5 + 0.5 * abs(math.sin(since * 6))
        target = wd.target()
        dist = f"   {math.hypot(target[0] - self.pos[0], target[1] - self.pos[1]):.0f} m" if target else ""
        p.fillRect(QRect(18, 16, 480, 24), QColor(0, 0, 0, 140))
        p.setPen(QColor(255, 255, 255, int(255 * glow)) if since < 3 else QColor(GREEN))
        p.drawText(QRect(26, 16, 470, 24), Qt.AlignLeft | Qt.AlignVCenter, "▶ " + wd.goal_text() + dist)
        hint = self._hint()
        if hint:
            p.setFont(_font(14))
            p.setPen(QColor("#FFFFFF"))
            p.fillRect(QRect(w // 2 - 170, h // 2 + 30, 340, 26), QColor(0, 0, 0, 150))
            p.drawText(QRect(w // 2 - 170, h // 2 + 30, 340, 26), Qt.AlignCenter, hint)
        if self.message and self.t < self.message[1]:
            p.setFont(_font(14))
            a = min(1.0, (self.message[1] - self.t) / 0.5)
            p.fillRect(QRect(w // 2 - 260, h // 2 + 70, 520, 30), QColor(0, 0, 0, int(160 * a)))
            p.setPen(QColor(255, 255, 255, int(255 * a)))
            p.drawText(QRect(w // 2 - 260, h // 2 + 70, 520, 30), Qt.AlignCenter, self.message[0])
        if self.state == "playing" and not self.captured and wd.elevator is None:
            p.setFont(_font(13))
            p.setPen(QColor("#FFFFFF"))
            p.drawText(QRect(0, h // 2 + 110, w, 24), Qt.AlignCenter, "Click to play")
        if wd.elevator is not None:
            fade = max(0.0, min(1.0, (wd.elevator - 3.0) / 3.0))
            p.fillRect(self.rect(), QColor(255, 250, 235, int(255 * fade)))
        if self.state == "paused":
            self._pause_menu(p)
        elif self.state == "pipboy":
            self._pipboy(p)
        elif self.state == "terminal":
            self._terminal_screen(p)
        elif self.state == "talk":
            self._talk_screen(p)
        elif self.state == "dead":
            self._dead(p)
        elif self.state == "end":
            self._end(p)
        p.setFont(_font(10, False))
        p.setPen(QColor(255, 255, 255, 110))
        p.drawText(8, h - 6, f"{self.fps:.0f} fps")

    def _sun(self, p):
        """The sun through the haze: a glow where it would be, if it's in front of you."""
        eye = QVector3D(self.pos[0], self._eye_y(), self.pos[1])
        v = self._mvp().map(QVector4D(eye + SUN * 50.0, 1.0))
        if v.w() <= 0.1:
            return
        x, y = (v.x() / v.w() + 1) / 2 * self.width(), (1 - v.y() / v.w()) / 2 * self.height()
        g = QRadialGradient(QPointF(x, y), 220)
        g.setColorAt(0, QColor(255, 245, 200, 150))
        g.setColorAt(0.3, QColor(255, 230, 160, 60))
        g.setColorAt(1, QColor(255, 220, 140, 0))
        p.fillRect(self.rect(), g)

    def _hint(self):
        """What E would do right now."""
        wd = self.world
        if self.state != "playing" or wd.elevator is not None:
            return ""
        px, pz = self.pos
        fx, fz = -math.sin(math.radians(self.yaw)), -math.cos(math.radians(self.yaw))

        def facing(x, z, reach):
            dx, dz = x - px, z - pz
            d = math.hypot(dx, dz)
            return d < reach and (dx * fx + dz * fz) / max(d, 0.01) > 0.5
        for kind, x, z in wd.items[wd.area].values():
            if facing(x, z, 1.9):
                return f"E  Take {ITEM_NAMES[kind]}"
        for c in wd.creatures:
            if not c.alive and not c.looted and c.area == wd.area and facing(c.x, c.z, 1.9):
                return f"E  Take {AID[KINDS[c.kind]['meat']][0]}"
        if wd.area == "vault":
            for tid, (x, z, title, _l) in V.TERMINALS.items():
                if facing(x, z, 2.0):
                    return f"E  Use {title.title()}"
            for cid, (x, z) in V.CONTROLS.items():
                if facing(x, z, 2.2):
                    return "E  Door control" if cid == "door" else "E  Elevator"
            if facing(V.SKELETON[0], V.SKELETON[1], 1.9) and "pipboy" in wd.items["vault"]:
                return "E  Search the skeleton"
        elif facing(S.ROBOT[0], S.ROBOT[1], 2.8):
            return f"E  Talk to {S.ROBOT_NAME}"
        return ""

    def _vignette(self, p, colour, strength):
        g = QRadialGradient(QPointF(self.width() / 2, self.height() / 2), max(self.width(), self.height()) * 0.7)
        c0, c1 = QColor(colour), QColor(colour)
        c0.setAlpha(0)
        c1.setAlpha(int(200 * min(1.0, strength)))
        g.setColorAt(0.35, c0)
        g.setColorAt(1.0, c1)
        p.fillRect(self.rect(), g)

    def _frost(self, p, strength):
        if strength <= 0:
            return
        g = QRadialGradient(QPointF(self.width() / 2, self.height() / 2), max(self.width(), self.height()) * 0.65)
        g.setColorAt(0.2, QColor(220, 240, 255, 0))
        g.setColorAt(1.0, QColor(220, 240, 255, int(230 * strength)))
        p.fillRect(self.rect(), g)

    def _weapon_view(self, p):
        """Your hands, the baton or the pistol, down at the bottom right."""
        wd = self.world
        w, h = self.width(), self.height()
        k = 1 - self.swing / 0.3 if self.swing > 0 else 0.0
        punch = math.sin(k * math.pi) if k else 0.0
        bobx, boby = math.sin(self.bob) * 6, abs(math.cos(self.bob)) * 5
        p.save()
        p.translate(w * 0.72 + bobx, h + boby)
        sleeve = QColor("#2E4A7A")
        skin = QColor("#E2B68A")
        if wd.weapon == "fists":
            p.translate(-punch * 60, -punch * 90)
            p.setPen(QPen(QColor("#1A2230"), 2))
            p.setBrush(sleeve)
            p.drawRoundedRect(QRectF(-20, -150, 90, 170), 20, 20)
            p.setBrush(skin)
            p.drawRoundedRect(QRectF(-10, -200, 72, 66), 22, 22)
            p.setPen(QPen(QColor("#A07050"), 1.5))
            for x in (8, 25, 42):
                p.drawLine(QPointF(x, -196), QPointF(x, -170))
            p.restore()
            p.save()
            p.translate(w * 0.28 - bobx, h + boby)
            p.translate(0, -punch * 10)
            p.setPen(QPen(QColor("#1A2230"), 2))
            p.setBrush(sleeve)
            p.drawRoundedRect(QRectF(-70, -130, 90, 150), 20, 20)
            p.setBrush(skin)
            p.drawRoundedRect(QRectF(-62, -175, 72, 60), 22, 22)
            if wd.pipboy:                                 # the Pip-Boy on your left wrist
                p.setBrush(QColor("#5A6A4A"))
                p.drawRoundedRect(QRectF(-78, -126, 100, 46), 12, 12)
                p.setBrush(QColor("#0A1A10"))
                p.drawRoundedRect(QRectF(-66, -118, 60, 30), 4, 4)
                p.setPen(QPen(QColor(GREEN), 2))
                for i, ww in enumerate((40, 26, 34)):
                    p.drawLine(QPointF(-60, -111 + i * 7), QPointF(-60 + ww, -111 + i * 7))
        elif wd.weapon == "baton":
            p.rotate(-25 - punch * 50)
            p.translate(0, -punch * 20)
            p.setPen(QPen(QColor("#1A2230"), 2))
            p.setBrush(sleeve)
            p.drawRoundedRect(QRectF(-20, -120, 80, 150), 20, 20)
            p.setBrush(skin)
            p.drawRoundedRect(QRectF(-8, -160, 56, 50), 16, 16)
            p.setBrush(QColor("#2A2A2A"))
            p.drawRoundedRect(QRectF(8, -330, 22, 190), 8, 8)
            p.setBrush(QColor("#555555"))
            p.drawRoundedRect(QRectF(5, -165, 28, 40), 6, 6)
            p.setBrush(QColor("#4AA0FF"))
            p.drawEllipse(QPointF(19, -322), 7, 7)
        else:
            p.translate(0, punch * 22)
            p.rotate(-punch * 9)
            p.setPen(QPen(QColor("#1A2230"), 2))
            p.setBrush(sleeve)
            p.drawRoundedRect(QRectF(-10, -110, 90, 140), 20, 20)
            p.setBrush(skin)
            p.drawRoundedRect(QRectF(0, -150, 60, 56), 16, 16)
            p.setPen(QPen(QColor("#111111"), 2))
            p.setBrush(QColor("#4A4A4A"))
            p.drawRoundedRect(QRectF(10, -240, 36, 120), 8, 8)
            p.drawRoundedRect(QRectF(-40, -250, 90, 36), 6, 6)
            p.setBrush(QColor("#2A2A2A"))
            p.drawRect(QRectF(-40, -244, 20, 14))
            p.drawRoundedRect(QRectF(-30, -222, 18, 8), 3, 3)
            if self.flash > 0:
                g = QRadialGradient(QPointF(-52, -232), 60)
                g.setColorAt(0, QColor(255, 240, 180, 230))
                g.setColorAt(1, QColor(255, 160, 40, 0))
                p.setPen(Qt.NoPen)
                p.setBrush(g)
                p.drawEllipse(QPointF(-52, -232), 60, 60)
        p.restore()

    def _button(self, p, rect, label, colour="#2A6A3A", size=15, key=None):
        hover = rect.contains(self.mapFromGlobal(QCursor.pos()))
        c = QColor(colour)
        p.setPen(QPen(c.lighter(150) if hover else c, 2))
        p.setBrush(c.darker(200) if not hover else c.darker(140))
        p.drawRect(rect)
        p.setFont(_font(size))
        p.setPen(QColor(GREEN))
        p.drawText(rect.adjusted(10, 0, -10, 0), Qt.AlignCenter, label)
        self.buttons.append((rect, key or label))

    def _title(self, p):
        w, h = self.width(), self.height()
        g = QLinearGradient(0, 0, 0, h)
        g.setColorAt(0, QColor("#0A1A10"))
        g.setColorAt(1, QColor("#020604"))
        p.fillRect(self.rect(), g)
        p.setPen(QPen(QColor(54, 224, 122, 25), 1))
        for y in range(0, h, 3):
            p.drawLine(0, y, w, y)
        pm = QPixmap.fromImage(art.tile_image("gear", self.atlas_img)).scaled(180, 180, Qt.KeepAspectRatio,
                                                                            Qt.FastTransformation)
        p.save()
        p.translate(w / 2, h * 0.3)
        p.rotate(self.t * 8)
        p.setOpacity(0.5)
        p.drawPixmap(-90, -90, pm)
        p.restore()
        p.setFont(_font(54, True, "Arial Black"))
        p.setPen(QColor(0, 0, 0, 160))
        p.drawText(QRect(3, int(h * 0.3) - 40 + 3, w, 80), Qt.AlignCenter, "CLAUDEOUT 4")
        p.setPen(QColor(AMBER))
        p.drawText(QRect(0, int(h * 0.3) - 40, w, 80), Qt.AlignCenter, "CLAUDEOUT 4")
        p.setFont(_font(15))
        p.setPen(QColor(GREEN))
        p.drawText(QRect(0, int(h * 0.3) + 44, w, 30), Qt.AlignCenter,
                   "PART ONE: OUT OF THE VAULT   -   PART TWO: THE NEIGHBOURHOOD")
        y = int(h * 0.54)
        latest = self.latest_slot()
        if latest:
            m = self.slot_meta(latest)
            self._button(p, QRect(w // 2 - 190, y, 380, 40), f"Continue  (slot {latest}: {m['objective'][:34]})",
                         size=13, key="Continue")
            y += 50
        self._button(p, QRect(w // 2 - 190, y, 380, 40), "New Game", key="New Game")
        y += 50
        if latest:
            self._button(p, QRect(w // 2 - 190, y, 380, 40), "Load Game", key="Load Game")
            y += 50
        self._button(p, QRect(w // 2 - 190, y, 380, 40), "Quit", "#5A3A2A", key="Quit")
        self._button(p, QRect(w - 230, 14, 100, 28), "Music: " + ("On" if self.music_on else "Off"), "#3A4A3A", 12, "Music")
        self._button(p, QRect(w - 122, 14, 108, 28), "Sound: " + ("On" if self.sfx_on else "Off"), "#3A4A3A", 12, "Sound")
        p.setFont(_font(12, False))
        p.setPen(QColor(GREEN))
        p.drawText(QRect(0, h - 70, w, 60), Qt.AlignCenter,
                   "WASD walk  -  mouse look  -  Shift sprint  -  left click attack  -  E use / loot / talk  -  "
                   "1-3 weapons  -  Q stimpak\nTab Pip-Boy (eat, heal, map, radio)  -  Esc pause")

    def _slots(self, p):
        w, h = self.width(), self.height()
        p.fillRect(self.rect(), QColor("#061208"))
        p.setPen(QPen(QColor(54, 224, 122, 25), 1))
        for y in range(0, h, 3):
            p.drawLine(0, y, w, y)
        p.setFont(_font(22))
        p.setPen(QColor(AMBER))
        title = {"new": "NEW GAME: CHOOSE A SLOT", "load": "LOAD GAME", "save": "SAVE GAME: CHOOSE A SLOT"}[self.slot_purpose]
        p.drawText(QRect(0, int(h * 0.2), w, 40), Qt.AlignCenter, title)
        y = int(h * 0.34)
        for n in range(1, SLOTS + 1):
            m = self.slot_meta(n)
            if m:
                label = (f"Slot {n}   Part {m['part']}{' (complete)' if m.get('done') else ''}: {m['objective'][:40]}"
                         f"   {_mins(m['time'])}   {m['saved'][:16]}")
                if self.slot_purpose == "new":
                    label += "   (overwrite)"
            else:
                label = f"Slot {n}   Empty"
            usable = bool(m) or self.slot_purpose != "load"
            self._button(p, QRect(w // 2 - 360, y, 720, 44), label, "#2A6A3A" if usable else "#3A3A3A", 13,
                         f"slot{n}" if usable else "none")
            y += 56
        self._button(p, QRect(w // 2 - 100, y + 20, 200, 40), "Back", "#5A3A2A", key="Back")

    def _card(self, p):
        w, h = self.width(), self.height()
        title, lines, secs = self.cards[0]
        k = self.card_t
        fade = min(1.0, k / 0.8) * min(1.0, max(0.0, (secs - k) / 0.8))
        p.fillRect(self.rect(), QColor("#060A08"))
        p.setOpacity(fade)
        p.setFont(_font(36, True, "Arial Black"))
        p.setPen(QColor(AMBER))
        p.drawText(QRect(0, int(h * 0.3), w, 60), Qt.AlignCenter, title)
        p.setFont(_font(15, False))
        p.setPen(QColor(GREEN))
        for i, s in enumerate(lines):
            p.drawText(QRect(0, int(h * 0.3) + 80 + i * 30, w, 28), Qt.AlignCenter, s)
        p.setOpacity(1.0)

    def _pause_menu(self, p):
        w, h = self.width(), self.height()
        p.fillRect(self.rect(), QColor(0, 0, 0, 150))
        p.setFont(_font(22))
        p.setPen(QColor(GREEN))
        p.drawText(QRect(0, int(h * 0.16), w, 40), Qt.AlignCenter, "PAUSED")
        back = "Back to the Vault" if self.world.area == "vault" else "Back outside"
        y = int(h * 0.28)
        rows = [(back, "#2A6A3A", "Back"), (f"Save  (slot {self.slot})", "#2A5A6A", "Save"),
                ("Save to another slot...", "#2A5A6A", "SaveAs"), ("Load game...", "#2A5A6A", "LoadMenu"),
                ("Music: " + ("On" if self.music_on else "Off"), "#3A4A3A", "Music"),
                ("Sound: " + ("On" if self.sfx_on else "Off"), "#3A4A3A", "Sound"),
                ("Save and Quit to Title", "#5A3A2A", "QuitTitle")]
        for label, colour, key in rows:
            self._button(p, QRect(w // 2 - 160, y, 320, 38), label, colour, 14, key)
            y += 46

    def _dead(self, p):
        w, h = self.width(), self.height()
        p.fillRect(self.rect(), QColor(60, 0, 0, 170))
        p.setFont(_font(34, True, "Arial Black"))
        p.setPen(QColor("#E04040"))
        p.drawText(QRect(0, int(h * 0.3), w, 60), Qt.AlignCenter, "YOU DIED")
        p.setFont(_font(14, False))
        p.setPen(QColor("#FFFFFF"))
        p.drawText(QRect(0, int(h * 0.3) + 64, w, 30), Qt.AlignCenter, "The wasteland is not kind.")
        self._button(p, QRect(w // 2 - 150, int(h * 0.52), 300, 40), "Load last checkpoint", key="Checkpoint")
        self._button(p, QRect(w // 2 - 150, int(h * 0.52) + 50, 300, 40), "Load game...", "#2A5A6A", key="LoadMenu")
        self._button(p, QRect(w // 2 - 150, int(h * 0.52) + 100, 300, 40), "Quit to Title", "#5A3A2A", key="QuitTitle")

    def _end(self, p):
        w, h = self.width(), self.height()
        wd = self.world
        k = min(1.0, self.end_t / 2.0)
        p.fillRect(self.rect(), QColor(255, 250, 235))
        p.fillRect(self.rect(), QColor(10, 20, 14, int(235 * k)))
        p.setFont(_font(34, True, "Arial Black"))
        p.setPen(QColor(AMBER))
        p.drawText(QRect(0, int(h * 0.26), w, 60), Qt.AlignCenter, "PART TWO COMPLETE")
        p.setFont(_font(15, False))
        p.setPen(QColor(GREEN))
        lines = [f"You crossed the bridge out of {S.TOWN}.",
                 f"Time awake: {_mins(wd.time)}     Creatures: {wd.kills}     Rads: {wd.rads}",
                 "Concord is somewhere past the filling station. That's for another day."]
        for i, s in enumerate(lines):
            p.drawText(QRect(0, int(h * 0.26) + 80 + i * 30, w, 28), Qt.AlignCenter, s)
        self._button(p, QRect(w // 2 - 150, int(h * 0.62), 300, 40), "Keep exploring", key="Roam")
        self._button(p, QRect(w // 2 - 150, int(h * 0.62) + 50, 300, 40), "Back to Title", "#5A3A2A", key="QuitTitle")

    # the Pip-Boy
    def _pipboy(self, p):
        w, h = self.width(), self.height()
        wd = self.world
        p.fillRect(self.rect(), QColor(0, 0, 0, 120))
        pw, ph = min(760, w - 60), min(500, h - 60)
        r = QRect((w - pw) // 2, (h - ph) // 2, pw, ph)
        p.setPen(QPen(QColor("#3A4030"), 8))
        p.setBrush(QColor("#5A6A4A"))
        p.drawRoundedRect(r.adjusted(-18, -18, 18, 18), 24, 24)
        p.setPen(QPen(QColor("#1A2A1A"), 3))
        p.setBrush(QColor("#061A0C"))
        p.drawRoundedRect(r, 8, 8)
        p.save()
        p.setClipRect(r)
        p.setPen(QPen(QColor(54, 224, 122, 22), 1))
        for y in range(r.top(), r.bottom(), 3):
            p.drawLine(r.left(), y, r.right(), y)
        g = QRadialGradient(QPointF(r.center()), pw * 0.7)
        g.setColorAt(0, QColor(54, 224, 122, 18))
        g.setColorAt(1, QColor(0, 0, 0, 0))
        p.fillRect(r, g)
        p.setFont(_font(15))
        tw = pw // len(PIP_TABS)
        for i, name in enumerate(PIP_TABS):
            tr = QRect(r.left() + i * tw, r.top() + 6, tw, 28)
            p.setPen(QColor(GREEN) if i == self.pip_tab else QColor(54, 224, 122, 120))
            p.drawText(tr, Qt.AlignCenter, name)
            if i == self.pip_tab:
                p.fillRect(QRect(tr.left() + 10, tr.bottom() - 2, tw - 20, 2), QColor(GREEN))
            self.buttons.append((tr, f"tab{i}"))
        body = r.adjusted(24, 48, -24, -40)
        p.setPen(QColor(GREEN))
        tab = PIP_TABS[self.pip_tab]
        if tab == "STAT":
            p.setFont(_font(14))
            p.drawText(QRect(body.left(), body.top(), 300, 24), Qt.AlignLeft, "Sole Survivor      Level 1")
            p.drawText(QRect(body.left(), body.top() + 30, 300, 24), Qt.AlignLeft, f"HP  {max(0, wd.hp)} / {wd.max_hp()}")
            p.fillRect(QRect(body.left(), body.top() + 56, 300, 10), QColor(20, 50, 30))
            p.fillRect(QRect(body.left(), body.top() + 56, int(300 * max(0, wd.hp) / PLAYER_HP), 10), QColor(GREEN))
            if wd.rads:
                p.fillRect(QRect(body.left() + int(300 * wd.max_hp() / PLAYER_HP), body.top() + 56,
                                 int(300 * wd.rads / PLAYER_HP), 10), QColor("#C0402A"))
            p.drawText(QRect(body.left(), body.top() + 74, 300, 24), Qt.AlignLeft, f"Rads  {wd.rads}       AP  70 / 70")
            p.setFont(_font(13, False))
            for i, (name, val) in enumerate(SPECIAL):
                y = body.top() + 110 + i * 24
                p.drawText(QRect(body.left(), y, 150, 22), Qt.AlignLeft, name)
                p.drawText(QRect(body.left() + 150, y, 30, 22), Qt.AlignLeft, str(val))
                p.fillRect(QRect(body.left() + 190, y + 6, 10 * val, 10), QColor(GREEN))
            xs = body.left() + 400
            where = "Vault 111" if wd.area == "vault" else S.TOWN
            p.drawText(QRect(xs, body.top(), 300, 24), Qt.AlignLeft, where)
            p.drawText(QRect(xs, body.top() + 26, 300, 24), Qt.AlignLeft, f"Creatures killed  {wd.kills}")
            p.drawText(QRect(xs, body.top() + 52, 300, 24), Qt.AlignLeft,
                       f"Time awake  {int(wd.time // 60)}:{int(wd.time % 60):02d}")
            p.drawText(QRect(xs, body.top() + 78, 300, 24), Qt.AlignLeft,
                       "Condition  " + ("Irradiated" if wd.rads >= 20 else "Thawed"))
        elif tab == "INV":
            p.setFont(_font(14))
            p.drawText(QRect(body.left(), body.top(), 300, 24), Qt.AlignLeft, "WEAPONS")
            y = body.top() + 30
            for key in ("fists", "baton", "pistol"):
                if key not in wd.have:
                    continue
                name, dmg, _reach, _rate = WEAPONS[key]
                rr = QRect(body.left(), y, 330, 26)
                sel = wd.weapon == key
                if sel:
                    p.fillRect(rr, QColor(54, 224, 122, 50))
                p.setFont(_font(13, sel))
                p.drawText(rr.adjusted(8, 0, 0, 0), Qt.AlignLeft | Qt.AlignVCenter,
                           f"{name}    DMG {dmg}" + (f"    {wd.ammo} rounds" if key == "pistol" else ""))
                self.buttons.append((rr, f"equip:{key}"))
                y += 30
            p.setFont(_font(14))
            p.drawText(QRect(body.left(), y + 16, 300, 24), Qt.AlignLeft, "AID   (click to use)")
            y += 46
            any_aid = False
            for kind, (name, heal, rads) in AID.items():
                n = wd.aid.get(kind, 0)
                if n <= 0:
                    continue
                any_aid = True
                rr = QRect(body.left(), y, 330, 24)
                p.setFont(_font(13, False))
                effect = (f"+{heal} HP" if heal else "") + (f"  +{rads} rads" if rads > 0 else f"  {rads} rads" if rads < 0 else "")
                p.drawText(rr.adjusted(8, 0, 0, 0), Qt.AlignLeft | Qt.AlignVCenter, f"{name}  x{n}    {effect}")
                self.buttons.append((rr, f"eat:{kind}"))
                y += 26
            if not any_aid:
                p.setFont(_font(13, False))
                p.drawText(QRect(body.left() + 8, y, 330, 24), Qt.AlignLeft | Qt.AlignVCenter, "Nothing.")
                y += 26
            p.setFont(_font(14))
            p.drawText(QRect(body.left(), y + 16, 300, 24), Qt.AlignLeft, "AMMO")
            p.setFont(_font(13, False))
            p.drawText(QRect(body.left() + 8, y + 42, 300, 24), Qt.AlignLeft, f"10mm  x{wd.ammo}")
            p.setFont(_font(12, False))
            p.drawText(QRect(body.left() + 400, body.top(), 300, 160), Qt.AlignLeft | Qt.TextWordWrap,
                       "Click a weapon to equip it (or press 1, 2, 3). Meat and Nuka-Cola heal, but give you rads: "
                       "every rad is a point off your top health until RadAway clears them. Stimpaks are clean (Q).")
        elif tab == "DATA":
            y = body.top()
            for part in (1, 2):
                if part == 2 and wd.part() < 2:
                    continue
                p.setFont(_font(14))
                p.setPen(QColor(GREEN))
                p.drawText(QRect(body.left(), y, 400, 24), Qt.AlignLeft, f"QUEST: {QUESTS[part]}")
                y += 30
                for pt, key, text in OBJECTIVES:
                    if pt != part:
                        continue
                    done = key in wd.done
                    current = wd.goal() == key
                    if not done and not current:
                        continue
                    p.setPen(QColor(54, 224, 122, 140) if done else QColor(GREEN))
                    p.setFont(_font(13, current))
                    p.drawText(QRect(body.left(), y, 650, 22), Qt.AlignLeft,
                               ("☑  " if done else "☐  ") + (wd.goal_text(key) if current else text))
                    y += 24
                y += 14
        elif tab == "MAP":
            self._map(p, body)
        elif tab == "RADIO":
            p.setFont(_font(14))
            p.drawText(QRect(body.left(), body.top(), 400, 24), Qt.AlignLeft, "RADIO")
            rr = QRect(body.left(), body.top() + 34, 360, 26)
            if self.radio:
                p.fillRect(rr, QColor(54, 224, 122, 50))
            p.setFont(_font(13, self.radio))
            p.drawText(rr.adjusted(8, 0, 0, 0), Qt.AlignLeft | Qt.AlignVCenter,
                       "Vault 111 Radio" + ("   ♪ playing" if self.radio else ""))
            self.buttons.append((rr, "radio"))
            p.setFont(_font(12, False))
            p.drawText(QRect(body.left(), body.top() + 80, 500, 60), Qt.AlignLeft | Qt.TextWordWrap,
                       "A tape of the old swing hour, still looping on the vault's station.")
            if self.radio:
                p.setPen(QPen(QColor(GREEN), 2))
                pts = [QPointF(body.left() + i * 6, body.top() + 190 + math.sin(self.t * 7 + i * 0.5) * 18
                               * math.sin(i * 0.17)) for i in range(60)]
                for i in range(1, len(pts)):
                    p.drawLine(pts[i - 1], pts[i])
        p.restore()
        p.setFont(_font(12, False))
        p.setPen(QColor(GREEN))
        p.drawText(QRect(r.left(), r.bottom() - 30, r.width(), 24), Qt.AlignCenter,
                   "Tab closes   -   1-5 or click the tabs")

    def _map(self, p, body):
        """The local map: what you've seen of wherever you are."""
        wd = self.world
        area = wd.area
        seen, done = self.map_seen[area], self.map_done[area]
        for cx, cz in wd.visited[area] - done:
            done.add((cx, cz))
            if area == "vault":
                room = V.room_at(cx, cz)
                for dx in range(-2, 3):
                    for dz in range(-2, 3):
                        x, z = cx + dx, cz + dz
                        if V.cell(x, z) != "#" and V.room_at(x, z) == room:
                            seen.add((x, z))
            else:
                for dx in range(-6, 7):
                    for dz in range(-6, 7):
                        if dx * dx + dz * dz <= 36:
                            seen.add((cx + dx, cz + dz))
        scale = 9 if area == "vault" else 3
        key = (area, len(seen))
        if self.map_key != key or self.map_pix is None:
            self.map_key = key
            size = (V.W, V.H) if area == "vault" else (S.SW, S.SH)
            pm = QPixmap(size[0] * scale, size[1] * scale)
            pm.fill(Qt.transparent)
            q = QPainter(pm)
            q.setPen(Qt.NoPen)
            for x, z in seen:
                if area == "vault":
                    col = QColor(54, 224, 122, 70)
                else:
                    c = MAP_COLOURS.get(S.cell(x, z), (60, 60, 60))
                    col = QColor(c[0], c[1], c[2], 190)
                q.fillRect(QRectF(x * scale, z * scale, scale, scale), col)
            if area == "vault":
                for did, (cells, _k) in V.DOORS.items():
                    for x, z in cells:
                        if any(abs(x - sx) <= 2 and abs(z - sz) <= 2 for sx, sz in seen):
                            q.fillRect(QRectF(x * scale, z * scale, scale, scale),
                                       QColor(AMBER) if wd.doors[did] < 0.5 else QColor(54, 224, 122, 160))
            q.end()
            self.map_pix = pm
        pm = self.map_pix
        ox = body.center().x() - pm.width() / 2
        oz = body.center().y() - pm.height() / 2 - 10
        p.drawPixmap(QPointF(ox, oz), pm)
        target = wd.target()
        if target:
            tx, tz = ox + target[0] * scale, oz + target[1] * scale
            p.setPen(QPen(QColor("#5ADCFF"), 2))
            p.setBrush(Qt.NoBrush)
            p.drawPolygon(QPolygonF([QPointF(tx, tz - 7), QPointF(tx + 7, tz), QPointF(tx, tz + 7), QPointF(tx - 7, tz)]))
        px, pz = ox + self.pos[0] * scale, oz + self.pos[1] * scale
        a = math.radians(self.yaw)
        fx, fz = -math.sin(a), -math.cos(a)
        tri = QPolygonF([QPointF(px + fx * 9, pz + fz * 9), QPointF(px - fx * 5 + fz * 5, pz - fz * 5 - fx * 5),
                         QPointF(px - fx * 5 - fz * 5, pz - fz * 5 + fx * 5)])
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#FFFFFF"))
        p.drawPolygon(tri)
        p.setFont(_font(12, False))
        p.setPen(QColor(GREEN))
        where = "Vault 111" if area == "vault" else S.TOWN
        p.drawText(QRect(body.left(), body.bottom() - 20, 500, 20), Qt.AlignLeft,
                   f"Local map: {where} (what you've seen so far)")

    def _terminal_screen(self, p):
        w, h = self.width(), self.height()
        tid, selected, typed, reply = self.terminal
        _x, _z, title, lines = V.TERMINALS[tid]
        p.fillRect(self.rect(), QColor(0, 0, 0, 150))
        r = QRect(w // 2 - 320, h // 2 - 200, 640, 400)
        p.setPen(QPen(QColor("#1A2A1A"), 3))
        p.setBrush(QColor("#041008"))
        p.drawRoundedRect(r, 6, 6)
        p.setPen(QPen(QColor(54, 224, 122, 22), 1))
        for y in range(r.top(), r.bottom(), 3):
            p.drawLine(r.left(), y, r.right(), y)
        p.setFont(_font(15))
        p.setPen(QColor(GREEN))
        y = r.top() + 24
        p.drawText(QRect(r.left() + 24, y, 600, 24), Qt.AlignLeft, "ROBCO INDUSTRIES (TM) TERMLINK PROTOCOL")
        y += 30
        p.drawText(QRect(r.left() + 24, y, 600, 24), Qt.AlignLeft, title)
        y += 40
        budget = int(typed)
        opts = []
        for ln in lines:
            if budget <= 0:
                break
            text = ln[:budget]
            budget -= len(ln) + 1
            is_opt = ln.startswith("> ")
            rr = QRect(r.left() + 24, y, 592, 26)
            if is_opt:
                opts.append(rr)
                if len(opts) - 1 == selected:
                    p.fillRect(rr, QColor(54, 224, 122, 50))
                self.buttons.append((rr, f"opt{len(opts) - 1}"))
            p.setFont(_font(14, is_opt))
            p.drawText(rr.adjusted(8, 0, 0, 0), Qt.AlignLeft | Qt.AlignVCenter, text)
            y += 30
        if reply:
            y += 10
            p.setFont(_font(14))
            p.drawText(QRect(r.left() + 32, y, 592, 26), Qt.AlignLeft | Qt.AlignVCenter, reply)
        cursor = "█" if int(self.t * 3) % 2 == 0 else " "
        p.setFont(_font(14, False))
        p.drawText(QRect(r.left() + 24, r.bottom() - 40, 600, 24), Qt.AlignLeft,
                   f"{cursor}   up/down + Enter, or click   -   Esc leaves")

    def _talk_screen(self, p):
        w, h = self.width(), self.height()
        node, selected, typed = self.talk
        text, choices = S.DIALOGUE[node]
        r = QRect(40, h - 250, w - 80, 220)
        p.setPen(QPen(QColor("#3A4030"), 3))
        p.setBrush(QColor(6, 18, 10, 225))
        p.drawRoundedRect(r, 8, 8)
        p.setFont(_font(15))
        p.setPen(QColor(AMBER))
        p.drawText(QRect(r.left() + 20, r.top() + 12, 300, 24), Qt.AlignLeft, S.ROBOT_NAME.upper())
        p.setFont(_font(14, False))
        p.setPen(QColor("#EDE6DA"))
        p.drawText(QRect(r.left() + 20, r.top() + 40, r.width() - 40, 80), Qt.AlignLeft | Qt.TextWordWrap,
                   text[:int(typed)])
        if typed >= len(text):
            y = r.top() + 126
            for i, (label, _nxt) in enumerate(choices):
                rr = QRect(r.left() + 20, y, r.width() - 40, 26)
                if i == selected:
                    p.fillRect(rr, QColor(54, 224, 122, 50))
                p.setFont(_font(14, i == selected))
                p.setPen(QColor(GREEN))
                p.drawText(rr.adjusted(8, 0, 0, 0), Qt.AlignLeft | Qt.AlignVCenter, f"{i + 1}.  {label}")
                self.buttons.append((rr, f"say{i}"))
                y += 28
        else:
            p.setFont(_font(12, False))
            p.setPen(QColor(54, 224, 122, 160))
            p.drawText(QRect(r.left() + 20, r.bottom() - 28, 400, 22), Qt.AlignLeft, "E or Enter: skip ahead")

    # ---- the loop ----
    def _tick(self):
        now = time.monotonic()
        dt = min(0.05, now - self.last)
        self.last = now
        self.t += dt
        if dt > 0:
            self.fps = self.fps * 0.9 + (1 / dt) * 0.1
        wd = self.world
        if self.state == "intro":
            self.intro_t += dt
            if self.intro_t >= 4.6:
                self.state = "playing"
                wd.advance("leave_cryo")
                self._drain_events()
        elif self.state == "intro2":
            self.intro_t += dt
            if self.intro_t >= 2.8:
                self.state = "playing"
        elif self.state == "card":
            self.card_t += dt
            if self.cards and self.card_t >= self.cards[0][2]:
                self.cards.pop(0)
                self.card_t = 0.0
                if not self.cards:
                    cb, self.after_cards = self.after_cards, None
                    if cb:
                        cb()
        elif self.state == "playing" and wd is not None:
            self._physics(dt, now)
            wd.update(dt, self.pos[0], self.pos[1], now)
            self._drain_events()
            self.cooldown = max(0.0, self.cooldown - dt)
            self.swing = max(0.0, self.swing - dt)
            self.flash = max(0.0, self.flash - dt * 6)
            self.hurt = max(0.0, self.hurt - dt * 1.5)
            if wd.hp <= 0 and self.state == "playing":
                self.state = "dead"
                self._capture(False)
                self.audio.play("death")
            if self.state == "playing" and now - self.saved_at > 15:
                self.save_slot()
        elif self.state == "talk":
            self.talk[2] = min(len(S.DIALOGUE[self.talk[0]][0]), self.talk[2] + dt * 45)
        elif self.state == "terminal":
            self.terminal[2] += dt * 60
        elif self.state == "end":
            self.end_t += dt
        if wd is not None:
            near = any(c.alive and c.aggro and c.area == wd.area and math.hypot(c.x - self.pos[0], c.z - self.pos[1]) < 14
                       for c in wd.creatures)
            busy = self.state in ("playing", "pipboy", "terminal", "talk")
            self.audio.want["combat"] = 1.0 if near and busy else 0.0
            self.audio.want["radio"] = 1.0 if self.radio and self.state not in ("title", "slots", "card", "end") else 0.0
            amb = 0.0 if self.state in ("title", "slots", "card", "end") else (0.45 if self.radio else 1.0)
            self.audio.want["vault"] = amb if wd.area == "vault" else 0.0
            self.audio.want["surface"] = amb if wd.area == "surface" else 0.0
            if near and wd.area == "surface" and self.t - self.buzz_at > 2.2 and busy:
                if any(c.alive and c.aggro and c.kind == "bloatfly" and c.area == wd.area
                       and math.hypot(c.x - self.pos[0], c.z - self.pos[1]) < 8 for c in wd.creatures):
                    self.buzz_at = self.t
                    self.audio.play("buzz", 0.6)
        else:
            self.audio.want.update(vault=0.0, surface=0.0, combat=0.0, radio=0.0)
        self.audio.tick(dt)
        self.update()

    def _physics(self, dt, now):
        wd = self.world
        if wd.elevator is not None:
            return
        y = math.radians(self.yaw)
        fwd = (-math.sin(y), -math.cos(y))
        right = (math.cos(y), -math.sin(y))
        mx = mz = 0.0
        k = self.keys
        if Qt.Key_W in k or Qt.Key_Up in k:
            mx += fwd[0]
            mz += fwd[1]
        if Qt.Key_S in k or Qt.Key_Down in k:
            mx -= fwd[0]
            mz -= fwd[1]
        if Qt.Key_D in k:
            mx += right[0]
            mz += right[1]
        if Qt.Key_A in k:
            mx -= right[0]
            mz -= right[1]
        if Qt.Key_Left in k:
            self.yaw = (self.yaw + 110 * dt) % 360
        if Qt.Key_Right in k:
            self.yaw = (self.yaw - 110 * dt) % 360
        n = math.hypot(mx, mz)
        if n:
            speed = SPRINT if Qt.Key_Shift in k else WALK
            mx, mz = mx / n * speed * dt, mz / n * speed * dt
            self.pos[0], self.pos[1] = wd.move(self.pos[0], self.pos[1], mx, mz)
            self.bob += dt * (11 if speed > WALK else 8)
            self.step_t += dt
            if self.step_t > (0.33 if speed > WALK else 0.46):
                self.step_t = 0.0
                self.step_k ^= 1
                self.audio.play(f"step{self.step_k}", 0.5)
        else:
            self.bob *= 0.9

    def _drain_events(self):
        wd = self.world
        for kind, detail in wd.events:
            if kind == "objective":
                self.objective_at = self.t
                self.audio.play("objective")
                self._mark_checkpoint()
            elif kind == "door":
                self.audio.play("door", 0.7)
            elif kind == "creatures":
                if "molerat" in detail:
                    self.audio.play("emerge")
                elif "bloatfly" in detail:
                    self.audio.play("buzz")
                else:
                    self.audio.play("chitter")
            elif kind == "aggro":
                self.audio.play({"roach": "chitter", "bloatfly": "buzz", "molerat": "squeak"}[detail], 0.7)
            elif kind == "bite":
                self.hurt = 1.0
                self.audio.play("sting" if detail == "bloatfly" else "bite")
            elif kind == "say":
                self.say(detail)
                self.audio.play("locked")
            elif kind == "surface":
                self._to_surface()
            elif kind == "end":
                self._finish_part_two()
        wd.events = []

    def say(self, text, secs=3.0):
        self.message = (text, self.t + secs)

    # ---- the parts ----
    def _to_surface(self):
        wd = self.world
        self.pos = [S.START[0], S.START[1]]
        self.yaw, self.pitch = S.START_YAW, -4.0
        self._capture(False)
        self._ensure_area()
        self.cards = [("PART ONE COMPLETE", [f"Out of the vault in {_mins(wd.time)}.",
                                             f"Radroaches: {wd.kills}     Stimpaks: {wd.aid.get('stimpak', 0)}     "
                                             f"10mm rounds: {wd.ammo}"], 5.0),
                      ("PART TWO", ["THE NEIGHBOURHOOD", "", f"{S.TOWN}, 210 years on."], 3.5)]
        self.card_t = 0.0
        self.state = "card"
        self.after_cards = self._surface_intro
        self.save_slot()

    def _surface_intro(self):
        self.state = "intro2"
        self.intro_t = 0.0
        self.audio.play("wind")
        self.objective_at = self.t
        self._mark_checkpoint()

    def _finish_part_two(self):
        self.state = "end"
        self.end_t = 0.0
        self._capture(False)
        self.audio.play("win")
        self.save_slot()

    # ---- doing things ----
    def _attack(self, now):
        wd = self.world
        if self.cooldown > 0 or wd.elevator is not None:
            return
        name, dmg, reach, rate = WEAPONS[wd.weapon]
        res = wd.attack(self.pos[0], self.pos[1], self.yaw, now)
        if res == "empty":
            self.audio.play("empty")
            self.say("Out of 10mm rounds.", 1.5)
            self.cooldown = 0.3
            return
        self.cooldown = rate
        self.swing = 0.3
        if wd.weapon == "pistol":
            self.flash = 1.0
            self.audio.play("shot")
        else:
            self.audio.play("baton" if wd.weapon == "baton" else "swing", 0.8)
        if res == "hit":
            self.audio.play("hit")
        elif res == "kill":
            self.audio.play("kill")

    def _use(self):
        wd = self.world
        if wd.elevator is not None:
            return
        out = wd.interact(self.pos[0], self.pos[1], self.yaw)
        self._drain_events()
        if out is None:
            return
        kind, detail = out
        if kind == "pickup":
            label = ITEM_NAMES[detail] + (" (8 rounds)" if detail == "pistol" else "")
            self.say(f"Picked up: {label}", 2.5)
            self.audio.play("pipboy" if detail == "pipboy" else "pickup")
            if detail == "pipboy":
                self.say("Pip-Boy equipped. Press Tab to use it.", 4.0)
        elif kind == "loot":
            self.say(f"Took: {AID[detail][0]}", 2.0)
            self.audio.play("loot")
        elif kind == "terminal":
            self.terminal = [detail, 0, 0.0, ""]
            self.state = "terminal"
            self._capture(False)
            self.audio.play("beep")
        elif kind == "say":
            self.say(detail)
            self.audio.play("locked")
        elif kind == "gear":
            self.say("Vault door cycling. Stand clear.", 4.0)
            self.audio.play("alarm")
            self.audio.play("gear")
        elif kind == "elevator":
            self.audio.play("elevator")
            self._capture(False)
        elif kind == "talk":
            self.talk = [detail, 0, 0.0]
            self.state = "talk"
            self._capture(False)
            self.audio.play("robot")

    def _choose_terminal(self):
        tid, selected, typed, reply = self.terminal
        opts = [ln for ln in V.TERMINALS[tid][3] if ln.startswith("> ")]
        if not opts:
            return
        opt = opts[selected % len(opts)]
        self.audio.play("key")
        if opt.startswith("> Unlock") or opt.startswith("> Unseal"):
            self.terminal[3] = self.world.use_terminal(tid)
            self._drain_events()
            self.audio.play("door", 0.5)
        else:
            self._close_terminal()

    def _close_terminal(self):
        self.terminal = None
        self.state = "playing"
        self._capture(True)

    def _talk_pick(self, i):
        node, _sel, typed = self.talk
        text, choices = S.DIALOGUE[node]
        if typed < len(text):
            self.talk[2] = len(text)
            return
        if not 0 <= i < len(choices):
            return
        nxt = self.world.choose(choices[i][1])
        self._drain_events()
        self.audio.play("talk")
        if nxt is None:
            self._close_talk()
        else:
            self.talk = [nxt, 0, 0.0]
            self.audio.play("robot", 0.6)

    def _close_talk(self):
        self.talk = None
        self.state = "playing"
        self._capture(True)

    def _equip(self, key):
        wd = self.world
        if key in wd.have and wd.weapon != key:
            wd.weapon = key
            self.audio.play("tab")

    def _eat(self, kind):
        wd = self.world
        before = wd.rads
        if wd.eat(kind):
            self.audio.play("stimpak" if kind in ("stimpak", "radaway") else "fizz" if kind == "cola" else "eat")
            if wd.rads > before:
                self.audio.play("geiger", 0.6)
            self.say(f"{AID[kind][0]} used.", 1.5)

    def _toggle_pipboy(self):
        wd = self.world
        if not wd.pipboy:
            return
        if self.state == "pipboy":
            self.state = "playing"
            self._capture(True)
        elif self.state == "playing":
            self.state = "pipboy"
            self._capture(False)
        self.audio.play("tab")

    # ---- starting ----
    def start_new(self, slot):
        self.slot = slot
        self.world = World()
        self.pos = [V.START[0], V.START[1]]
        self.yaw, self.pitch = V.START[2], -5.0
        self.radio = False
        self.map_seen = {"vault": set(), "surface": set()}
        self.map_done = {"vault": set(), "surface": set()}
        self.terminal = self.talk = None
        self.state = "intro"
        self.intro_t = 0.0
        self.audio.play("pod")
        self._mark_checkpoint()
        self._ensure_area()
        self.objective_at = self.t
        self.save_slot(slot)

    def load_slot(self, slot):
        data = self._load(f"slot{slot}.json")
        if not data:
            return False
        try:
            self.world = World.from_json(data["world"])
            x, z, self.yaw, self.pitch = data["pos"]
            self.pos = [x, z]
            self.checkpoint = data.get("checkpoint")
            self.radio = data.get("radio", False)
        except (KeyError, TypeError, ValueError):
            self.world = None
            return False
        self.slot = slot
        self.map_seen = {"vault": set(), "surface": set()}
        self.map_done = {"vault": set(), "surface": set()}
        self.terminal = self.talk = None
        self._ensure_area()
        self.objective_at = self.t
        self.state = "playing"
        self._capture(True)
        return True

    def _restore_checkpoint(self):
        cp = self.checkpoint
        if not cp:
            self.start_new(self.slot)
            return
        self.world = World.from_json(cp["world"])
        x, z, self.yaw, self.pitch = cp["pos"]
        self.pos = [x, z]
        self.world.hp = max(self.world.hp, min(60, self.world.max_hp()))
        self._ensure_area()
        self.state = "playing"
        self._capture(True)

    def _to_title(self, save=True):
        if save and self.world is not None and self.state != "end":
            self.save_slot()
        self.state = "title"
        self.world = None
        self._capture(False)

    # ---- input ----
    def _capture(self, on):
        self.captured = on
        if on:
            self.setCursor(Qt.BlankCursor)
            QCursor.setPos(self.mapToGlobal(self.rect().center()))
            self.setFocus()
        else:
            self.unsetCursor()
            self.keys.clear()

    def _click_button(self, pos):
        for rect, key in self.buttons:
            if key == "none" or not rect.contains(pos):
                continue
            if key == "Continue":
                self.load_slot(self.latest_slot())
            elif key == "New Game":
                self.slot_purpose = "new"
                self.state = "slots"
            elif key in ("Load Game", "LoadMenu"):
                self.slot_purpose = "load"
                self.state = "slots"
            elif key == "Quit":
                if self.frame:
                    self.frame.request_close()
            elif key == "Music":
                self.music_on = not self.music_on
                self.audio.music_on = self.music_on
                self._save_settings()
            elif key == "Sound":
                self.sfx_on = not self.sfx_on
                self.audio.sfx_on = self.sfx_on
                self._save_settings()
            elif key == "Back":
                if self.state == "slots":
                    self.state = "title" if self.world is None else ("dead" if self.world.hp <= 0 else "paused")
                else:
                    self.state = "playing"
                    self._capture(True)
            elif key == "Save":
                self.save_slot()
                self.say(f"Saved to slot {self.slot}.", 2.0)
                self.state = "playing"
                self._capture(True)
            elif key == "SaveAs":
                self.slot_purpose = "save"
                self.state = "slots"
            elif key.startswith("slot"):
                n = int(key[4:])
                if self.slot_purpose == "new":
                    self.start_new(n)
                elif self.slot_purpose == "load":
                    if not self.load_slot(n):
                        self.state = "title"
                else:
                    self.save_slot(n)
                    self.say(f"Saved to slot {n}.", 2.0)
                    self.state = "playing"
                    self._capture(True)
            elif key == "QuitTitle":
                self._to_title(save=self.state == "paused")
            elif key == "Checkpoint":
                self._restore_checkpoint()
            elif key == "Roam":
                self.state = "playing"
                self._capture(True)
            elif key.startswith("tab"):
                self.pip_tab = int(key[3:])
                self.audio.play("key")
            elif key.startswith("equip:"):
                self._equip(key[6:])
            elif key.startswith("eat:"):
                self._eat(key[4:])
            elif key == "radio":
                self.radio = not self.radio
                self.audio.play("key")
            elif key.startswith("opt"):
                self.terminal[1] = int(key[3:])
                self._choose_terminal()
            elif key.startswith("say"):
                self._talk_pick(int(key[3:]))
            return True
        return False

    def mousePressEvent(self, e):
        if self.state in ("title", "slots", "paused", "dead", "end", "pipboy", "terminal", "talk"):
            hit = self._click_button(e.position().toPoint())
            if self.state == "talk" and not hit:
                self._talk_pick(-1)                       # (a click anywhere finishes the typing)
            return
        if self.state != "playing":
            return
        if not self.captured:
            self._capture(True)
            return
        if e.button() == Qt.LeftButton:
            self._attack(time.monotonic())
        elif e.button() == Qt.RightButton:
            self._use()

    def mouseMoveEvent(self, e):
        if not self.captured:
            self.update()
            return
        center = self.rect().center()
        d = e.position().toPoint() - center
        if d.manhattanLength() == 0:
            return
        self.yaw = (self.yaw - d.x() * 0.14) % 360
        self.pitch = max(-80.0, min(80.0, self.pitch - d.y() * 0.14))
        QCursor.setPos(self.mapToGlobal(center))

    def keyPressEvent(self, e):
        key = e.key()
        if e.isAutoRepeat():
            return
        if key == Qt.Key_Escape:
            if self.state == "playing":
                self.state = "paused"
                self._capture(False)
            elif self.state == "paused":
                self.state = "playing"
                self._capture(True)
            elif self.state == "pipboy":
                self._toggle_pipboy()
            elif self.state == "terminal":
                self._close_terminal()
            elif self.state == "talk":
                self._close_talk()
            elif self.state == "slots":
                self.state = "title" if self.world is None else "paused"
            return
        if self.state == "terminal":
            tid = self.terminal[0]
            n = len([ln for ln in V.TERMINALS[tid][3] if ln.startswith("> ")])
            if key in (Qt.Key_Up, Qt.Key_W):
                self.terminal[1] = (self.terminal[1] - 1) % max(1, n)
                self.audio.play("key")
            elif key in (Qt.Key_Down, Qt.Key_S):
                self.terminal[1] = (self.terminal[1] + 1) % max(1, n)
                self.audio.play("key")
            elif key in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_E, Qt.Key_Space):
                self._choose_terminal()
            return
        if self.state == "talk":
            n = len(S.DIALOGUE[self.talk[0]][1])
            if key in (Qt.Key_Up, Qt.Key_W):
                self.talk[1] = (self.talk[1] - 1) % max(1, n)
            elif key in (Qt.Key_Down, Qt.Key_S):
                self.talk[1] = (self.talk[1] + 1) % max(1, n)
            elif Qt.Key_1 <= key <= Qt.Key_9:
                self._talk_pick(key - Qt.Key_1)
            elif key in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_E, Qt.Key_Space):
                self._talk_pick(self.talk[1])
            return
        if key == Qt.Key_Tab:
            self._toggle_pipboy()
            return
        if self.state == "pipboy":
            if Qt.Key_1 <= key <= Qt.Key_5:
                self.pip_tab = key - Qt.Key_1
                self.audio.play("key")
            return
        if self.state != "playing":
            return
        if key == Qt.Key_E:
            self._use()
        elif key == Qt.Key_Q:
            self._eat("stimpak")
        elif key == Qt.Key_1:
            self._equip("fists")
        elif key == Qt.Key_2:
            self._equip("baton")
        elif key == Qt.Key_3:
            self._equip("pistol")
        elif key == Qt.Key_Space:
            self._attack(time.monotonic())
        self.keys.add(key)

    def keyReleaseEvent(self, e):
        if not e.isAutoRepeat():
            self.keys.discard(e.key())

    def event(self, e):
        if e.type() == e.Type.KeyPress and e.key() == Qt.Key_Tab:     # (Tab would move focus otherwise)
            self.keyPressEvent(e)
            return True
        return super().event(e)

    def focusOutEvent(self, e):
        if self.captured:
            self._capture(False)
        super().focusOutEvent(e)

    def shutdown(self):
        if self.world is not None and self.state not in ("title", "slots", "end"):
            self.save_slot()
        self.timer.stop()
        self.audio.stop()

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
    win = host.window(desktop, "Claudeout 4", body, out_icon(), size=(1024, 640))
    body.frame = win
    _open["win"] = win
    desktop.open_window(win)
    return win


def shutdown():
    win = _open.get("win")
    if win is not None and isValid(win):
        win.content.shutdown()
