"""Second Life: a 3D world in four regions, where the 34 residents hang out as furry avatars.

The viewer (this) draws the world with Qt Quick 3D (scene.qml) and wraps it in Second Life's floaters: local
chat, IMs, Friends, Inventory, Appearance, Profiles (with Furry Codes), the Map, Build tools and Land. The grid
itself - the residents, chat, objects and land - runs in world.py, inside the viewer.

Walk with W/S or the arrow keys (A/D turn, Shift runs), F flies (E up, C down), double-click the ground to walk
there, drag the mouse to look around, scroll to zoom. Enter starts typing; Escape goes back to walking."""
import math
import time
import traceback

from PySide6.QtCore import Q_ARG, Q_RETURN_ARG, QEvent, QMetaObject, QObject, QPointF, QRectF, Qt, QTimer, QUrl, Signal, Slot
from PySide6.QtGui import QColor, QFont, QIcon, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtQuickWidgets import QQuickWidget
from PySide6.QtWidgets import (QCheckBox, QColorDialog, QComboBox, QFormLayout, QFrame, QGridLayout, QHBoxLayout,
                               QInputDialog, QLabel, QLineEdit, QListWidget, QListWidgetItem, QMenu, QPushButton,
                               QScrollArea, QSlider, QTabWidget, QTextBrowser, QToolButton, QTreeWidget,
                               QTreeWidgetItem, QVBoxLayout, QWidget)
from shiboken6 import isValid

from ... import network
from ...wm import XPWindow
from ..placeholder import open_placeholder
from . import catalog, residents
from .avatar import BODY_ORDER, PRESETS, avatar_qml, esc
from .sims import BOOTH_SLOTS, SIM_ORDER
from .world import FLY, RUN, WALK, World

TITLE = "Second Life"
SCENE = __file__.replace("__init__.py", "scene.qml")
STYLE = """
QFrame#floater { background: rgba(26, 32, 42, 238); border: 1px solid #5A6A80; border-radius: 6px; }
QFrame#bar { background: rgba(18, 22, 30, 225); border: none; }
QLabel { color: #E0E8F0; }
QLabel#title { color: #FFFFFF; font-weight: bold; }
QLabel#dim { color: #9AA8B8; }
QPushButton, QToolButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #52627A, stop:1 #3A485C);
    color: #F0F4F8; border: 1px solid #222E3C; border-radius: 4px; padding: 4px 10px; }
QPushButton:hover, QToolButton:hover { background: #5E7494; }
QPushButton:checked, QToolButton:checked { background: #3A6AA8; }
QPushButton:disabled { color: #7A8898; background: #343E4C; }
QLineEdit, QTextBrowser, QTreeWidget, QListWidget, QComboBox { background: rgba(12, 16, 22, 230); color: #E8EEF4;
    border: 1px solid #44546A; border-radius: 3px; selection-background-color: #3A6AA8; }
QComboBox QAbstractItemView { background: #1A2230; color: #E8EEF4; selection-background-color: #3A6AA8; }
QTabWidget::pane { border: 1px solid #44546A; }
QTabBar::tab { background: #2E3A4A; color: #D0D8E0; padding: 4px 10px; }
QTabBar::tab:selected { background: #3A6AA8; color: white; }
QCheckBox { color: #E0E8F0; }
QScrollArea { background: transparent; border: none; }
QMenu { background: #222A36; color: #E8EEF4; border: 1px solid #5A6A80; }
QMenu::item:selected { background: #3A6AA8; }
"""
SWATCHES = ["#F4F4F2", "#C8C8C8", "#8A8A90", "#3A3A3E", "#1A1A1E", "#F2D2B6", "#E8C890", "#D8A050", "#C8642E",
            "#A8703A", "#6A4A30", "#3A2A1A", "#E85A5A", "#C02A2A", "#F2C230", "#E8783A", "#6AC86A", "#3A8A3A",
            "#4AB8E8", "#3A5AA8", "#7A4FA8", "#E88AB0", "#2A9AC8", "#3A8A8A"]


def sl_icon():
    pm = QPixmap(32, 32)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    g = QLinearGradient(0, 0, 0, 32)
    g.setColorAt(0, QColor("#4AD8E8"))
    g.setColorAt(1, QColor("#1A6A9A"))
    p.setBrush(g)
    p.setPen(QPen(QColor("#0E3A5A"), 1))
    p.drawRoundedRect(QRectF(1, 1, 30, 30), 7, 7)
    eye = QPainterPath()
    eye.moveTo(5, 16)
    eye.quadTo(16, 5, 27, 16)
    eye.quadTo(16, 27, 5, 16)
    p.setBrush(QColor("#FFFFFF"))
    p.setPen(Qt.NoPen)
    p.drawPath(eye)
    p.setBrush(QColor("#1A4A7A"))
    p.drawEllipse(QPointF(16, 16), 5, 5)
    p.setBrush(QColor("#FFFFFF"))
    p.drawEllipse(QPointF(17.5, 14.5), 1.6, 1.6)
    p.end()
    return QIcon(pm)


class Bridge(QObject):
    """What the 3D scene tells Python (see scene.qml's MouseArea)."""
    clicked = Signal(str, float, float, float, float, float, int)
    double = Signal(str, float, float, float)
    drag = Signal(float, float, int)
    zoom = Signal(int)

    def __init__(self):
        super().__init__()
        self.travel = 0.0

    @Slot(float, float, int)
    def pressed(self, x, y, button):
        self.travel = 0.0

    @Slot(float, float, int)
    def dragged(self, dx, dy, buttons):
        self.travel += abs(dx) + abs(dy)
        if self.travel > 4:
            self.drag.emit(dx, dy, buttons)

    @Slot(str, float, float, float, float, float, int)
    def released(self, tag, x, y, z, sx, sy, button):
        if self.travel <= 4:
            self.clicked.emit(tag, x, y, z, sx, sy, button)

    @Slot(str, float, float, float)
    def doubleClicked(self, tag, x, y, z):
        self.double.emit(tag, x, y, z)

    @Slot(int)
    def wheel(self, delta):
        self.zoom.emit(delta)


class Floater(QFrame):
    """A Second Life floater: a little window inside the viewer, dragged by its title."""

    def __init__(self, viewer, title, w, h):
        super().__init__(viewer)
        self.setObjectName("floater")
        self.viewer = viewer
        self.resize(w, h)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 6, 10, 10)
        lay.setSpacing(6)
        bar = QHBoxLayout()
        self.title = QLabel(title)
        self.title.setObjectName("title")
        close = QToolButton()
        close.setText("✕")
        close.clicked.connect(self.hide)
        bar.addWidget(self.title)
        bar.addStretch(1)
        bar.addWidget(close)
        lay.addLayout(bar)
        self.body = QVBoxLayout()
        lay.addLayout(self.body, 1)
        self._grab = None
        self.hide()

    def mousePressEvent(self, e):
        if e.position().y() < 30:
            self._grab = e.globalPosition() - QPointF(self.pos())

    def mouseMoveEvent(self, e):
        if self._grab is not None:
            p = e.globalPosition() - self._grab
            par = self.parentWidget()
            self.move(int(max(0, min(par.width() - 60, p.x()))), int(max(26, min(par.height() - 60, p.y()))))

    def mouseReleaseEvent(self, e):
        self._grab = None

    def popup(self, x=None, y=None):
        if not self.isVisible():
            par = self.parentWidget()
            if x is None:
                x = (par.width() - self.width()) / 2
                y = (par.height() - self.height()) / 2
            self.move(int(x), int(y))
        self.show()
        self.raise_()


class ChatOverlay(QWidget):
    """Recent local chat over the world, fading after a while (as in the real viewer)."""

    def __init__(self, parent):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.lines = []

    def add(self, text, colour):
        self.lines.append((text, colour, time.monotonic()))
        del self.lines[:-12]
        self.update()

    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.TextAntialiasing)
        f = QFont("Segoe UI")
        f.setPixelSize(14)
        p.setFont(f)
        now = time.monotonic()
        y = self.height() - 6
        for text, colour, t in reversed(self.lines[-9:]):
            age = now - t
            alpha = 1.0 if age < 20 else max(0.0, 1 - (age - 20) / 5)
            if alpha <= 0:
                continue
            rect = p.fontMetrics().boundingRect(0, 0, self.width() - 16, 400, Qt.TextWordWrap, text)
            y -= rect.height() + 3
            box = QRectF(4, y - 1, rect.width() + 12, rect.height() + 4)
            p.setOpacity(alpha)
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(10, 14, 20, 150))
            p.drawRoundedRect(box, 4, 4)
            p.setPen(QColor(colour))
            p.drawText(QRectF(10, y + 1, self.width() - 16, rect.height() + 2), Qt.TextWordWrap, text)
            p.setOpacity(1.0)
            if y < 0:
                break


class Viewer(QWidget):
    def __init__(self, desktop):
        super().__init__()
        self.desktop = desktop
        self.frame = None
        self.setStyleSheet(STYLE)
        self.setMinimumSize(1000, 660)
        self.world = World(self)
        self.world.chat.connect(self._on_chat)
        self.world.im.connect(self._on_im)
        self.world.notice.connect(self._toast)
        self.world.land_changed.connect(self._land_changed)
        self.bridge = Bridge()
        self.bridge.clicked.connect(self._clicked)
        self.bridge.double.connect(self._double)
        self.bridge.drag.connect(self._dragged)
        self.bridge.zoom.connect(self._zoomed)
        self.quick = QQuickWidget(self)
        self.quick.rootContext().setContextProperty("bridge", self.bridge)
        self.quick.setResizeMode(QQuickWidget.SizeRootObjectToView)
        self.quick.setSource(QUrl.fromLocalFile(SCENE))
        self.root = self.quick.rootObject()
        if self.root is None:
            raise RuntimeError("The 3D scene didn't load: " + "; ".join(e.toString() for e in self.quick.errors()))
        self.quick.installEventFilter(self)
        self.keys = set()
        self.logged_in = False
        self.loaded = None                # the region in the scene
        self.spawned = {}                 # avatar tag -> version
        self.obj_seen = {}                # object tag -> (edits, selected)
        self.world_version = -1
        self.selected = None              # an object you're editing
        self.walk_to = None
        self.cam_orbit = 0.0
        self.cam_pitch = 14.0
        self.cam_dist = 420.0
        self.cam = None
        self.unread = 0
        self.t = 0.0
        self.last = time.perf_counter()
        self._build_chrome()
        self._build_floaters()
        self.timer = QTimer(self)
        self.timer.setTimerType(Qt.PreciseTimer)
        self.timer.setInterval(16)
        self.timer.timeout.connect(self._tick)
        self.timer.start()
        self._show_login()

    # ---- the 3D scene ----
    def call(self, name, *args):
        return QMetaObject.invokeMethod(self.root, name, Q_RETURN_ARG("QVariant"), *[Q_ARG("QVariant", a) for a in args])

    def _spawn(self, qml, tag, where):
        err = self.call("spawn", qml, tag, where)
        if err:
            print(f"Second Life: couldn't build {tag}: {err}")
        return not err

    def load_sim(self, key):
        s = self.world.sims[key]
        self.call("dropAll")
        self.spawned.clear()
        self.obj_seen.clear()
        self.selected = None
        self._spawn(catalog.scenery_qml(s.prims, s.tags), "scenery", "world")
        if s.extra:
            self._spawn("import QtQuick\nimport QtQuick3D\nNode {\n" + s.extra + "\n}", "lights", "world")
        for i, (item, x, y, z, yaw) in enumerate(s.mannequins):
            it = catalog.ITEMS[item]
            tag = f"vend:{item}"
            if self._spawn(avatar_qml(it["spec"], [], tag=tag, hover=f"{it['name']}\nFREE - click"), tag, "people"):
                self.call("place", tag, float(x), float(y), float(z), 0.0, float(yaw), 0.0)
        self.call("setEnv", s.env)
        self.loaded = key
        self.world_version = -1

    def _sync(self):
        w = self.world
        me = w.me
        present = {f"av:{a.name}": a for a in w.people if a.online and a.sim == me.sim}
        present["av:@me"] = me
        for tag, a in present.items():
            if self.spawned.get(tag) != a.version:
                label = a.full
                if self._spawn(avatar_qml(a.look, a.worn(), tag=tag, label=label, title=a.title or " "), tag,
                               "people"):
                    self.spawned[tag] = a.version
        for tag in [t for t in self.spawned if t not in present]:
            self.call("drop", tag)
            del self.spawned[tag]
        rows = [[tag, float(a.x), float(a.y), float(a.z), float(a.yaw), a.state == "walk",
                 a.dance if a.state == "dance" else 0, a.state == "sit", a.state == "fly", bool(a.typing)]
                for tag, a in present.items()]
        self.call("apply", rows)
        if w.version != self.world_version:
            self.world_version = w.version
            self._sync_objects()

    def _sync_objects(self):
        w = self.world
        here = {f"obj:{o['id']}": o for o in w.objects if o["sim"] == w.me.sim}
        for tag, o in here.items():
            state = (o.get("edits", 0), o["id"] == self.selected)
            if self.obj_seen.get(tag) != state:
                if self._spawn(catalog.object_qml(o, tag, state[1]), tag, "things"):
                    self.obj_seen[tag] = state
            self.call("place", tag, float(o["x"]), float(o["y"]), float(o["z"]), 0.0, float(o["yaw"]), 0.0)
        for tag in [t for t in self.obj_seen if t not in here]:
            self.call("drop", tag)
            del self.obj_seen[tag]

    # ---- the clock ----
    def _tick(self):
        now = time.perf_counter()
        dt = min(0.1, now - self.last)
        self.last = now
        self.t += dt
        if not self.logged_in:
            self._login_camera()
            return
        self.world.tick(dt)
        self._move(dt)
        if self.loaded != self.world.me.sim:
            self._teleport_screen(self.world.sim().name)
            self.load_sim(self.world.me.sim)
        self._sync()
        self._camera(dt)
        if int(self.t * 4) != int((self.t - dt) * 4):
            self._status()
            self.chat_overlay.update()
            if self.friends.isVisible():
                self._fill_friends()

    def _login_camera(self):
        if self.loaded is None:
            self.load_sim("bazaar")
        a = self.t * 0.06
        c = 3200
        self.call("camera", c + math.sin(a) * 2400, 700.0, c + math.cos(a) * 2400, -12.0, math.degrees(a))

    def _move(self, dt):
        w = self.world
        me = w.me
        k = self.keys
        fwd = (Qt.Key_W in k or Qt.Key_Up in k) - (Qt.Key_S in k or Qt.Key_Down in k)
        turn = (Qt.Key_A in k or Qt.Key_Left in k) - (Qt.Key_D in k or Qt.Key_Right in k)
        up = (Qt.Key_E in k or Qt.Key_PageUp in k) - (Qt.Key_C in k or Qt.Key_PageDown in k)
        flying = me.state == "fly"
        if (fwd or up) and me.state in ("sit", "dance"):
            w.me_stand()
        if fwd or turn or up:
            self.walk_to = None
        me.yaw = (me.yaw + turn * 120 * dt) % 360
        if self.walk_to is not None and not flying:
            tx, tz = self.walk_to
            dx, dz = tx - me.x, tz - me.z
            d = math.hypot(dx, dz)
            if d < 30:
                self.walk_to = None
            else:
                me.yaw = math.degrees(math.atan2(dx, dz))
                fwd = 1
        speed = FLY if flying else (RUN if Qt.Key_Shift in k else WALK)
        if fwd:
            a = math.radians(me.yaw)
            nx = me.x + math.sin(a) * fwd * speed * dt
            nz = me.z + math.cos(a) * fwd * speed * dt
            if flying and me.y > 450:
                me.x, me.z = nx, nz
            elif not self._blocked(nx, nz):
                me.x, me.z = nx, nz
            elif not self._blocked(nx, me.z):
                me.x = nx
            elif not self._blocked(me.x, nz):
                me.z = nz
            else:
                self.walk_to = None
            me.x = min(max(me.x, 80.0), 6320.0)
            me.z = min(max(me.z, 80.0), 6320.0)
            self.cam_orbit *= math.exp(-dt * 2.5)
        if flying:
            me.y = max(0.0, me.y + up * 450 * dt)
            if me.y <= 0 and up < 0:
                me.state = "stand"
        elif me.state not in ("sit", "dance"):
            me.state = "walk" if fwd else "stand"
            if up > 0:
                self._fly()

    def _blocked(self, x, z):
        r = 28
        for x0, z0, x1, z1 in self.world.sim().walls:
            if x0 - r < x < x1 + r and z0 - r < z < z1 + r:
                return True
        return False

    def _camera(self, dt):
        me = self.world.me
        yaw = me.yaw + self.cam_orbit
        pitch = math.radians(self.cam_pitch)
        tx, ty, tz = me.x, me.y + 150 * me.look.get("height", 1.0), me.z
        a = math.radians(yaw)
        want = (tx - math.sin(a) * self.cam_dist * math.cos(pitch), ty + self.cam_dist * math.sin(pitch),
                tz - math.cos(a) * self.cam_dist * math.cos(pitch))
        if self.cam is None:
            self.cam = list(want)
        k = 1 - math.exp(-dt * 10)
        for i in range(3):
            self.cam[i] += (want[i] - self.cam[i]) * k
        self.cam[1] = max(self.cam[1], 30.0)
        dx, dy, dz = tx - self.cam[0], ty - self.cam[1], tz - self.cam[2]
        cyaw = math.degrees(math.atan2(-dx, -dz))
        cpitch = math.degrees(math.atan2(dy, math.hypot(dx, dz)))
        self.call("camera", float(self.cam[0]), float(self.cam[1]), float(self.cam[2]), float(cpitch), float(cyaw))

    # ---- input ----
    def eventFilter(self, obj, e):
        if obj is self.quick:
            if e.type() == QEvent.KeyPress:
                self.keyPressEvent(e)
                return True
            if e.type() == QEvent.KeyRelease:
                self.keyReleaseEvent(e)
                return True
            if e.type() == QEvent.FocusOut:
                self.keys.clear()
        return False

    def keyPressEvent(self, e):
        if not self.logged_in:
            return
        k = e.key()
        if k in (Qt.Key_Return, Qt.Key_Enter):
            self.chat_line.setFocus()
            return
        if k == Qt.Key_F and not e.isAutoRepeat():
            self._fly()
            return
        if k == Qt.Key_Escape:
            self.selected = None
            self.world_version = -1
            return
        if k == Qt.Key_Shift:
            self.keys.add(k)
        self.keys.add(k)

    def keyReleaseEvent(self, e):
        if not e.isAutoRepeat():
            self.keys.discard(e.key())

    def _dragged(self, dx, dy, buttons):
        self.cam_orbit -= dx * 0.35
        self.cam_pitch = max(-5.0, min(75.0, self.cam_pitch + dy * 0.25))

    def _zoomed(self, delta):
        self.cam_dist = max(120.0, min(2500.0, self.cam_dist * (0.88 ** (delta / 120))))

    def _clicked(self, tag, x, y, z, sx, sy, button):
        if not self.logged_in:
            return
        self.quick.setFocus()
        if button == 2:
            self._context_menu(tag, x, z)
            return
        self._touch(tag, x, z)

    def _double(self, tag, x, y, z):
        if self.logged_in and tag == "ground":
            self.walk_to = (x, z)

    def _touch(self, tag, x, z):
        """A left click on something in the world (Second Life's 'touch')."""
        w = self.world
        s = w.sim()
        if tag.startswith("av:"):
            name = tag[3:]
            self.show_profile(w.me.name if name == "@me" else name)
        elif tag.startswith("vend:"):
            self._vendor_body(tag[5:])
        elif tag.startswith("booth:"):
            self.show_booth(tag[6:])
        elif tag in s.dance:
            w.me_dance(s.dance[tag])
        elif tag in s.seats:
            w.me_sit(tag)
        elif tag in s.teleports:
            w.teleport(s.teleports[tag])
        elif tag.startswith("parcel:"):
            self.show_land(int(tag.split(":")[1]))
        elif tag.startswith("obj:"):
            o = w.obj(int(tag[4:]))
            if o is None:
                return
            if self.build.isVisible() and o.get("owner") == "@player":
                self._select(o)
            elif o["obj"] == "danceball":
                w.me_dance(1 + o["id"] % 4)
            elif "sit" in catalog.OBJECTS[o["obj"]][2]:
                self._sit_on(o)
            elif o.get("owner") == "@player":
                self.build.popup(self.width() - 330, 80)
                self._select(o)

    def _sit_on(self, o):
        me = self.world.me
        sx, sy, sz, syaw = catalog.OBJECTS[o["obj"]][2]["sit"]
        a = math.radians(o["yaw"])
        sc = o.get("scale", 1.0)
        self.world.me_stand()
        me.x = o["x"] + (sx * math.cos(a) + sz * math.sin(a)) * sc
        me.z = o["z"] + (-sx * math.sin(a) + sz * math.cos(a)) * sc
        me.y = o["y"] + sy * sc
        me.yaw = o["yaw"] + syaw
        me.state = "sit"

    def _context_menu(self, tag, x, z):
        w = self.world
        menu = QMenu(self)
        if tag.startswith("av:") and tag != "av:@me":
            name = tag[3:]
            menu.addAction("Profile...", lambda: self.show_profile(name))
            menu.addAction("Send IM...", lambda: self.open_im(name))
            a = w.find(name)
            if a and a.state == "dance":
                menu.addAction("Dance with them", lambda: w.me_dance(a.dance))
        elif tag == "av:@me":
            menu.addAction("Appearance...", lambda: self.appearance.popup(self.width() - 420, 40))
            menu.addAction("Stand up", w.me_stand)
            menu.addAction("Stop flying" if w.me.state == "fly" else "Fly", self._fly)
            for k in range(1, 5):
                menu.addAction(f"Dance {k}", lambda k=k: w.me_dance(k))
        elif tag.startswith("obj:"):
            o = w.obj(int(tag[4:]))
            if o is not None:
                info = catalog.OBJECTS[o["obj"]][2]
                if "sit" in info:
                    menu.addAction("Sit here", lambda: self._sit_on(o))
                if o.get("owner") == "@player":
                    menu.addAction("Edit...", lambda: (self.build.popup(self.width() - 330, 80), self._select(o)))
                    menu.addAction("Take", lambda: self._take(o))
                    menu.addAction("Take Copy", lambda: w.copy_object(o))
                    menu.addAction("Delete", lambda: self._delete(o))
                else:
                    menu.addAction(f"Owner: {o.get('owner')}").setEnabled(False)
        elif tag.startswith("vend:"):
            key = tag[5:]
            menu.addAction("Get it (free)", lambda: self._get(key))
            menu.addAction("Get and wear", lambda: self._get(key, wear=True))
        elif tag in w.sim().seats:
            menu.addAction("Sit here", lambda: w.me_sit(tag))
        else:
            menu.addAction("Walk here", lambda: setattr(self, "walk_to", (x, z)))
            ok, _why = w.can_build(x, z)
            if ok:
                menu.addAction("Build...", lambda: self.build.popup(self.width() - 330, 80))
        from PySide6.QtGui import QCursor
        menu.exec(QCursor.pos())

    def _fly(self):
        me = self.world.me
        if me.state == "fly":
            me.state = "stand"
            me.y = 0.0
        else:
            self.world.me_stand()
            me.state = "fly"
            me.y = max(me.y, 60.0)
        self.fly_btn.setText("Land" if me.state == "fly" else "Fly")

    # ---- the frame around the world ----
    def _build_chrome(self):
        self.top = QFrame(self)
        self.top.setObjectName("bar")
        tl = QHBoxLayout(self.top)
        tl.setContentsMargins(10, 2, 10, 2)
        self.where = QLabel("")
        self.clock = QLabel("")
        self.clock.setObjectName("dim")
        tl.addWidget(self.where)
        tl.addStretch(1)
        tl.addWidget(self.clock)
        self.bottom = QFrame(self)
        self.bottom.setObjectName("bar")
        bl = QHBoxLayout(self.bottom)
        bl.setContentsMargins(8, 4, 8, 4)
        bl.setSpacing(4)
        self.chat_line = QLineEdit()
        self.chat_line.setPlaceholderText("Click here to chat (Enter), /me to emote")
        self.chat_line.returnPressed.connect(self._send_chat)
        self.chat_line.installEventFilter(self)
        bl.addWidget(self.chat_line, 3)
        say = QPushButton("Say")
        say.clicked.connect(self._send_chat)
        bl.addWidget(say)
        self.buttons = {}
        for label, slot in (("Chat", self._toggle_history), ("IM", self._toggle_im), ("Friends", self._toggle_friends),
                            ("Inventory", self._toggle_inventory), ("Appearance", self._toggle_appearance),
                            ("Map", self._toggle_map), ("Build", self._toggle_build), ("Fly", self._fly),
                            ("Stand", lambda: self.world.me_stand()), ("Help", self._toggle_help)):
            b = QPushButton(label)
            b.clicked.connect(slot)
            b.setFocusPolicy(Qt.NoFocus)
            bl.addWidget(b)
            self.buttons[label] = b
        self.fly_btn = self.buttons["Fly"]
        self.chat_overlay = ChatOverlay(self)
        self.toast = QLabel(self)
        self.toast.setStyleSheet("background: rgba(20, 60, 100, 220); color: white; padding: 6px 12px; "
                                 "border-radius: 5px; border: 1px solid #6AA8E8;")
        self.toast.hide()
        self.toast_timer = QTimer(self)
        self.toast_timer.setSingleShot(True)
        self.toast_timer.timeout.connect(self.toast.hide)
        self.tp_screen = QLabel(self)
        self.tp_screen.setAlignment(Qt.AlignCenter)
        self.tp_screen.setStyleSheet("background: #101820; color: #CFE8FF; font-size: 22px;")
        self.tp_screen.hide()

    def resizeEvent(self, e):
        w, h = self.width(), self.height()
        self.quick.setGeometry(0, 0, w, h)
        self.top.setGeometry(0, 0, w, 26)
        self.bottom.setGeometry(0, h - 40, w, 40)
        self.chat_overlay.setGeometry(6, h - 40 - 230, min(620, w - 20), 226)
        self.tp_screen.setGeometry(0, 0, w, h)
        if hasattr(self, "login_panel"):
            self.login_panel.move((w - self.login_panel.width()) // 2, (h - self.login_panel.height()) // 2)

    def _status(self):
        w = self.world
        me = w.me
        s = w.sim()
        place = ""
        if s.key == "estates":
            n = w.parcel_at(me.x, me.z)
            if n is not None:
                who = w.owner_label(n)
                place = f" - {who}'s land" if who else " - land for claim"
        self.where.setText(f"<b>{s.name}</b> ({int(me.x / 100)}, {int(me.z / 100)}, {int(me.y / 100)}){place}"
                           f"   •   {len(w.here()) - 1} nearby   •   L$ 0")
        self.clock.setText(time.strftime("%I:%M %p").lstrip("0") + " SLT")
        self.buttons["IM"].setText(f"IM ({self.unread})" if self.unread else "IM")

    def _toast(self, text):
        if not self.logged_in:
            return
        self.toast.setText(text)
        self.toast.adjustSize()
        self.toast.move(self.width() - self.toast.width() - 14, 36)
        self.toast.show()
        self.toast.raise_()
        self.toast_timer.start(4000)

    def _teleport_screen(self, name):
        self.tp_screen.setText(f"Teleporting to {name}...")
        self.tp_screen.show()
        self.tp_screen.raise_()
        QTimer.singleShot(700, self.tp_screen.hide)

    # ---- chat ----
    def _on_chat(self, kind, who, text):
        if kind == "say":
            line, colour = f"{who}: {text}", "#FFFFFF" if who != self.world.me.name else "#D8F0FF"
        elif kind == "emote":
            line, colour = f"{who} {text}", "#FFFFFF"
        else:
            line, colour = text, "#A8D8A8"
        self.chat_overlay.add(line, colour)
        self.history_text.append(f'<span style="color:{colour}">{esc_html(line)}</span>')

    def _send_chat(self):
        text = self.chat_line.text().strip()
        self.chat_line.clear()
        if text and self.logged_in:
            self.world.say(text)
        self.quick.setFocus()

    def _on_im(self, who, text, mine):
        tab = self._im_tab(who)
        speaker = "You" if mine else who
        colour = "#D8F0FF" if mine else "#FFFFFF"
        tab.log.append(f'<span style="color:{colour}"><b>{esc_html(speaker)}:</b> {esc_html(text)}</span>')
        if not mine:
            if not self.ims.isVisible():
                self.unread += 1
                self._toast(f"IM from {who}: {text[:60]}")

    # ---- floaters ----
    def _build_floaters(self):
        # chat history
        self.history = Floater(self, "Local Chat", 460, 320)
        self.history_text = QTextBrowser()
        self.history.body.addWidget(self.history_text)
        # instant messages
        self.ims = Floater(self, "Instant Messages", 460, 360)
        self.im_tabs = QTabWidget()
        self.im_tabs.setTabsClosable(True)
        self.im_tabs.tabCloseRequested.connect(self.im_tabs.removeTab)
        self.ims.body.addWidget(self.im_tabs)
        self.im_widgets = {}
        # friends
        self.friends = Floater(self, "Friends", 330, 440)
        self.friend_list = QListWidget()
        self.friend_list.itemDoubleClicked.connect(lambda it: self.open_im(it.data(Qt.UserRole)))
        self.friends.body.addWidget(self.friend_list)
        row = QHBoxLayout()
        for label, fn in (("IM", self.open_im), ("Profile", self.show_profile), ("Teleport To", self._tp_to)):
            b = QPushButton(label)
            b.clicked.connect(lambda _c=False, fn=fn: self._with_friend(fn))
            row.addWidget(b)
        self.friends.body.addLayout(row)
        # inventory
        self.inv = Floater(self, "Inventory", 380, 470)
        self.inv_tree = QTreeWidget()
        self.inv_tree.setHeaderHidden(True)
        self.inv_tree.itemDoubleClicked.connect(self._inv_activate)
        self.inv_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.inv_tree.customContextMenuRequested.connect(self._inv_menu)
        self.inv.body.addWidget(self.inv_tree)
        hint = QLabel("Double-click to wear or rez; right-click for more.")
        hint.setObjectName("dim")
        self.inv.body.addWidget(hint)
        # appearance
        self.appearance = Floater(self, "Appearance", 400, 600)
        self._build_appearance()
        # profile
        self.prof = Floater(self, "Profile", 420, 560)
        self._build_profile()
        # map
        self.map = Floater(self, "World Map", 460, 360)
        self._build_map()
        # build
        self.build = Floater(self, "Build", 320, 520)
        self._build_build()
        # land
        self.land = Floater(self, "About Land", 340, 220)
        self.land_text = QLabel()
        self.land_text.setWordWrap(True)
        self.land.body.addWidget(self.land_text)
        self.land_row = QHBoxLayout()
        self.land.body.addLayout(self.land_row)
        self.land.body.addStretch(1)
        # vendors
        self.vendor = Floater(self, "Vendor", 360, 440)
        self.vendor_list = QListWidget()
        self.vendor_list.itemDoubleClicked.connect(lambda it: self._get(it.data(Qt.UserRole), wear=True))
        self.vendor.body.addWidget(self.vendor_list)
        row = QHBoxLayout()
        get = QPushButton("Get (free)")
        get.clicked.connect(lambda: self._vendor_pick(False))
        wear = QPushButton("Get and Wear")
        wear.clicked.connect(lambda: self._vendor_pick(True))
        row.addWidget(get)
        row.addWidget(wear)
        self.vendor.body.addLayout(row)
        # help
        self.help = Floater(self, "Quick Help", 420, 380)
        help_text = QLabel(
            "<b>Moving</b><br>W / S or the arrow keys: walk (Shift runs) &nbsp; A / D: turn<br>"
            "F: fly (E up, C down) &nbsp; Double-click the ground: walk there<br>"
            "Drag the mouse: look around &nbsp; Scroll: zoom<br><br>"
            "<b>Doing things</b><br>Click people for their profile, a dance ball to dance, a seat to sit, a body or "
            "a stall at the Bazaar to get free stuff, a teleport board to travel. Right-click anything for more.<br>"
            "<br><b>Chat</b><br>Enter to type in local chat (everyone nearby hears it); /me for an emote. "
            "IMs are private.<br><br><b>Building</b><br>Build on Sandbox Isle's deck, or on land you claim in "
            "Pawprint Estates.")
        help_text.setWordWrap(True)
        help_text.setTextFormat(Qt.RichText)
        self.help.body.addWidget(help_text)
        self.help.body.addStretch(1)

    def _toggle(self, f, x=None, y=None):
        if f.isVisible():
            f.hide()
        else:
            f.popup(x, y)

    def _toggle_history(self):
        self._toggle(self.history, 10, 60)

    def _toggle_im(self):
        self.unread = 0
        self._toggle(self.ims, 30, 80)

    def _toggle_friends(self):
        self._fill_friends()
        self._toggle(self.friends, self.width() - 350, 60)

    def _toggle_inventory(self):
        self._fill_inventory()
        self._toggle(self.inv, self.width() - 400, 50)

    def _toggle_appearance(self):
        self._load_appearance()
        self._toggle(self.appearance, self.width() - 420, 34)

    def _toggle_map(self):
        self._fill_map()
        self._toggle(self.map)

    def _toggle_build(self):
        self._fill_build()
        self._toggle(self.build, self.width() - 340, 80)

    def _toggle_help(self):
        self._toggle(self.help)

    # IMs
    def _im_tab(self, name):
        tab = self.im_widgets.get(name)
        if tab is None or not isValid(tab):
            tab = QWidget()
            lay = QVBoxLayout(tab)
            tab.log = QTextBrowser()
            line = QLineEdit()
            line.setPlaceholderText(f"IM {name}...")
            line.returnPressed.connect(lambda: self._send_im(name, line))
            lay.addWidget(tab.log)
            lay.addWidget(line)
            tab.line = line
            self.im_widgets[name] = tab
        if self.im_tabs.indexOf(tab) < 0:
            self.im_tabs.addTab(tab, name)
        return tab

    def open_im(self, name):
        a = self.world.find(name)
        if a is None:
            return
        tab = self._im_tab(a.name)
        self.im_tabs.setCurrentWidget(tab)
        self.unread = 0
        self.ims.popup(30, 80)
        tab.line.setFocus()

    def _send_im(self, name, line):
        text = line.text().strip()
        line.clear()
        if text:
            self.world.send_im(name, text)

    # friends
    def _fill_friends(self):
        cur = self.friend_list.currentItem()
        keep = cur.data(Qt.UserRole) if cur else None
        self.friend_list.clear()
        people = sorted(self.world.people, key=lambda a: (not a.online, a.name.lower()))
        for a in people:
            where = f" - {self.world.sims[a.sim].name}" if a.online and a.sim else ""
            it = QListWidgetItem(("● " if a.online else "○ ") + a.name + where)
            it.setForeground(QColor("#7FE07A" if a.online else "#7A8898"))
            it.setData(Qt.UserRole, a.name)
            self.friend_list.addItem(it)
            if a.name == keep:
                self.friend_list.setCurrentItem(it)

    def _with_friend(self, fn):
        it = self.friend_list.currentItem()
        if it:
            fn(it.data(Qt.UserRole))

    def _tp_to(self, name):
        a = self.world.find(name)
        if a is None or not a.online:
            self._toast(f"{name} isn't online.")
            return
        w = self.world
        if a.sim != w.me.sim:
            w.teleport(a.sim)
        w.me.x, w.me.z = a.x + 120, a.z + 120
        w.me.yaw = math.degrees(math.atan2(a.x - w.me.x, a.z - w.me.z))

    # inventory
    def _fill_inventory(self):
        self.inv_tree.clear()
        folders = {}
        order = ["Body Parts", "Clothing", "Accessories", "Outfits", "Objects", "Lost and Found"]
        for name in order:
            f = QTreeWidgetItem([name])
            f.setForeground(0, QColor("#F2D27A"))
            self.inv_tree.addTopLevelItem(f)
            folders[name] = f
        for it in sorted(self.world.inventory(), key=lambda i: i["name"].lower()):
            f = folders.get(it["folder"]) or folders["Objects"]
            label = it["name"] + ("  (worn)" if self.world.wearing(it) else "")
            node = QTreeWidgetItem([label])
            node.setData(0, Qt.UserRole, it["id"])
            f.addChild(node)
        for f in folders.values():
            f.setText(0, f"{f.text(0)} ({f.childCount()})")
            f.setExpanded(f.childCount() < 12)

    def _inv_item(self, node):
        iid = node.data(0, Qt.UserRole) if node else None
        return self.world.item(iid) if iid else None

    def _inv_activate(self, node):
        it = self._inv_item(node)
        if it is None:
            return
        if it["kind"] == "object":
            self._rez(it)
        else:
            self.world.wear(it)
            self._fill_inventory()

    def _inv_menu(self, pos):
        it = self._inv_item(self.inv_tree.itemAt(pos))
        if it is None:
            return
        w = self.world
        menu = QMenu(self)
        if it["kind"] == "object":
            menu.addAction("Rez in front of me", lambda: self._rez(it))
        elif it["kind"] in ("clothing", "accessory"):
            if w.wearing(it):
                menu.addAction("Take Off", lambda: (w.take_off(catalog.ITEMS[it["key"]]["slot"]),
                                                    self._fill_inventory()))
            else:
                menu.addAction("Wear", lambda: (w.wear(it), self._fill_inventory()))
        else:
            menu.addAction("Wear", lambda: (w.wear(it), self._fill_inventory()))
        menu.addAction("Rename...", lambda: self._rename(it))
        menu.addAction("Delete", lambda: (w.delete_item(it), self._fill_inventory()))
        menu.exec(self.inv_tree.viewport().mapToGlobal(pos))

    def _rename(self, it):
        name, ok = QInputDialog.getText(self, "Rename", "New name:", text=it["name"])
        if ok and name.strip():
            self.world.rename_item(it, name.strip())
            self._fill_inventory()

    def _rez(self, it):
        o, why = self.world.rez(it)
        if o is None:
            self._toast(why)
        else:
            self._toast(f"Rezzed {o['name']}.")
            if self.build.isVisible():
                self._select(o)

    # vendors and freebies
    def _get(self, key, wear=False):
        it = self.world.take(key)
        if wear and it["kind"] != "object":
            self.world.wear(it)
            self._toast(f"You got {it['name']} and put it on.")
        else:
            self._toast(f"{it['name']} is in your inventory.")
        if self.inv.isVisible():
            self._fill_inventory()

    def _vendor_body(self, key):
        it = catalog.ITEMS[key]
        menu = QMenu(self)
        menu.addAction(f"{it['name']} - FREE").setEnabled(False)
        menu.addAction("Get it", lambda: self._get(key))
        menu.addAction("Get it and wear it now", lambda: self._get(key, wear=True))
        from PySide6.QtGui import QCursor
        menu.exec(QCursor.pos())

    def show_booth(self, booth):
        self.vendor.title.setText(f"{booth} - everything FREE")
        self.vendor_list.clear()
        if booth in BOOTH_SLOTS:
            items = [i for i in catalog.ITEMS.values() if i.get("slot") in BOOTH_SLOTS[booth]]
        elif booth == "Home & Garden":
            items = catalog.by_booth("Home & Garden")
        else:
            items = catalog.by_booth("Basics")
        for i in items:
            li = QListWidgetItem(i["name"])
            li.setData(Qt.UserRole, i["key"])
            if i.get("colour"):
                pm = QPixmap(14, 14)
                pm.fill(QColor(i["colour"]))
                li.setIcon(QIcon(pm))
            self.vendor_list.addItem(li)
        self.vendor.popup(60, 60)

    def _vendor_pick(self, wear):
        li = self.vendor_list.currentItem()
        if li:
            self._get(li.data(Qt.UserRole), wear=wear and catalog.ITEMS[li.data(Qt.UserRole)]["kind"] != "object")

    # profiles
    def _build_profile(self):
        top = QHBoxLayout()
        self.prof_pic = QLabel()
        self.prof_pic.setFixedSize(128, 128)
        self.prof_pic.setStyleSheet("background: #101820; border: 1px solid #44546A;")
        self.prof_pic.setAlignment(Qt.AlignCenter)
        top.addWidget(self.prof_pic)
        self.prof_head = QLabel()
        self.prof_head.setWordWrap(True)
        self.prof_head.setTextFormat(Qt.RichText)
        top.addWidget(self.prof_head, 1)
        self.prof.body.addLayout(top)
        self.prof_tabs = QTabWidget()
        self.prof_about = QTextBrowser()
        self.prof_fursona = QTextBrowser()
        self.prof_codes = QTextBrowser()
        self.prof_tabs.addTab(self.prof_about, "2nd Life")
        self.prof_tabs.addTab(self.prof_fursona, "Fursona")
        self.prof_tabs.addTab(self.prof_codes, "Codes")
        self.prof.body.addWidget(self.prof_tabs, 1)
        self.prof_row = QHBoxLayout()
        self.prof.body.addLayout(self.prof_row)
        self.prof_name = None

    def show_profile(self, name):
        w = self.world
        p = w.profile(name)
        self.prof_name = name
        self.prof.title.setText(f"Profile - {p['full']}")
        pic = QPixmap(str(p["picture"])) if p.get("picture") else QPixmap()
        if not pic.isNull():
            self.prof_pic.setPixmap(pic.scaled(126, 126, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.prof_pic.setText("(no picture)")
        status = ""
        if not p.get("me"):
            status = (f"<span style='color:#7FE07A'>Online - {p.get('where', '')}</span>" if p.get("online")
                      else "<span style='color:#8A98A8'>Offline</span>")
        self.prof_head.setText(f"<span style='font-size:16px'><b>{esc_html(p['full'])}</b></span><br>"
                               f"<i>{esc_html(p.get('title', ''))}</i><br>Born {esc_html(p['born'])}<br>"
                               f"{esc_html(p.get('species', ''))}<br>{status}")
        about = esc_html(p.get("about") or "(nothing here yet)").replace("\n", "<br>")
        extra = ""
        if p.get("partner"):
            extra += f"<br><br><b>Partner:</b> {esc_html(p['partner'])}"
        if p.get("home") is not None:
            extra += f"<br><b>Home:</b> Pawprint Estates, lot {p['home'] + 1}"
        self.prof_about.setHtml(f"{about}{extra}")
        self.prof_fursona.setHtml(f"<b>{esc_html(p.get('species', ''))}</b><br>{esc_html(p.get('look', ''))}<br><br>"
                                  f"<b>Pronouns:</b> {esc_html(p.get('pronouns', '') or '-')}<br><br>"
                                  f"<b>Interests</b><br>{esc_html(p.get('interests', '') or '-')}")
        codes = f"<b>Furry Code</b><br><tt>{esc_html(p.get('furcode') or '(none)')}</tt><br><br>"
        codes += f"<b>YIFF Code</b><br><tt>{esc_html(p.get('yiffcode') or '(not public)')}</tt>"
        self.prof_codes.setHtml(codes)
        while self.prof_row.count():
            item = self.prof_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        if p.get("me"):
            b = QPushButton("Edit About...")
            b.clicked.connect(self._edit_about)
            self.prof_row.addWidget(b)
        else:
            for label, fn in (("IM", lambda: self.open_im(name)), ("Teleport To", lambda: self._tp_to(name))):
                b = QPushButton(label)
                b.clicked.connect(fn)
                self.prof_row.addWidget(b)
        if p.get("furcode") or p.get("yiffcode"):
            b = QPushButton("Decode in FurCoder")
            b.clicked.connect(lambda: self._furcoder(p["name"]))
            self.prof_row.addWidget(b)
        self.prof.popup(40, 40)

    def _edit_about(self):
        text, ok = QInputDialog.getMultiLineText(self, "About you", "Your 2nd Life:",
                                                 self.world.player.get("about", ""))
        if ok:
            self.world.set_about(text)
            self.show_profile(self.world.me.name)

    def _furcoder(self, name):
        try:
            from ..messengers.core import decode_in_furcoder
            decode_in_furcoder(self.desktop, name)
        except Exception:
            pass

    # the map
    def _build_map(self):
        grid = QGridLayout()
        self.map_buttons = {}
        colours = {"bazaar": "#B8783A", "club": "#7A3A9A", "estates": "#4A8A3A", "sandbox": "#2A7AA8"}
        for k, key in enumerate(SIM_ORDER):
            b = QPushButton()
            b.setMinimumSize(200, 130)
            b.setStyleSheet(f"QPushButton {{ background: {colours[key]}; text-align: left; padding: 10px; "
                            f"font-size: 13px; }} QPushButton:hover {{ background: {QColor(colours[key]).lighter(120).name()}; }}")
            b.clicked.connect(lambda _c=False, key=key: (self.world.teleport(key), self.map.hide()))
            grid.addWidget(b, k // 2, k % 2)
            self.map_buttons[key] = b
        self.map.body.addLayout(grid)
        hint = QLabel("Click a region to teleport there.")
        hint.setObjectName("dim")
        self.map.body.addWidget(hint)

    def _fill_map(self):
        w = self.world
        for key, b in self.map_buttons.items():
            s = w.sims[key]
            n = sum(1 for a in w.people if a.online and a.sim == key) + (1 if w.me.sim == key else 0)
            here = "  (you are here)" if w.me.sim == key else ""
            b.setText(f"{s.name}{here}\n\n{n} avatar{'s' if n != 1 else ''} here")

    # land
    def show_land(self, n):
        w = self.world
        who = w.owner_label(n)
        self.land.title.setText(f"About Land - Pawprint Estates, lot {n + 1}")
        if who:
            self.land_text.setText(f"<b>Owner:</b> {esc_html(who)}<br><br>" +
                                   ("This is your land: you can rez and build anything here." if who == w.player_name
                                    else "Private land."))
        else:
            self.land_text.setText("This lot is free. Claim it and it's yours to build on (one lot each).")
        while self.land_row.count():
            item = self.land_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        if not who:
            b = QPushButton("Claim this land (free)")
            b.clicked.connect(lambda: self._claim(n))
            self.land_row.addWidget(b)
        elif who == w.player_name:
            b = QPushButton("Abandon land")
            b.clicked.connect(self._abandon)
            self.land_row.addWidget(b)
        self.land.popup()

    def _claim(self, n):
        err = self.world.claim(n)
        self._toast(err or "The land is yours! Open Build to start building.")
        self.land.hide()

    def _abandon(self):
        self.world.abandon()
        self._toast("You've given up your land; your things there went back to your inventory.")
        self.land.hide()

    def _land_changed(self):
        if self.loaded == "estates":
            self.load_sim("estates")

    # building
    def _build_build(self):
        b = self.build.body
        lab = QLabel("<b>Create</b>")
        b.addWidget(lab)
        row = QHBoxLayout()
        for key in ("cube", "sphere", "cylinder", "cone"):
            btn = QPushButton(key.title())
            btn.clicked.connect(lambda _c=False, key=key: self._create(key))
            row.addWidget(btn)
        b.addLayout(row)
        row = QHBoxLayout()
        self.rez_pick = QComboBox()
        row.addWidget(self.rez_pick, 1)
        btn = QPushButton("Rez")
        btn.clicked.connect(self._rez_picked)
        row.addWidget(btn)
        b.addLayout(row)
        self.edit_label = QLabel("<b>Edit</b> - click one of your objects")
        b.addWidget(self.edit_label)
        grid = QGridLayout()
        moves = [("← X", (-25, 0, 0)), ("X →", (25, 0, 0)), ("↑ Z", (0, 0, -25)), ("Z ↓", (0, 0, 25)),
                 ("Up", (0, 15, 0)), ("Down", (0, -15, 0))]
        for k, (label, d) in enumerate(moves):
            btn = QPushButton(label)
            btn.clicked.connect(lambda _c=False, d=d: self._nudge(d))
            grid.addWidget(btn, k // 2, k % 2)
        for k, (label, fn) in enumerate((("↶ Turn", lambda: self._turn(-15)), ("Turn ↷", lambda: self._turn(15)),
                                         ("Smaller", lambda: self._scale(0.9)), ("Bigger", lambda: self._scale(1.1)))):
            btn = QPushButton(label)
            btn.clicked.connect(fn)
            grid.addWidget(btn, 3 + k // 2, k % 2)
        b.addLayout(grid)
        sw = QGridLayout()
        for k, c in enumerate(SWATCHES[:16]):
            btn = QToolButton()
            btn.setFixedSize(28, 22)
            btn.setStyleSheet(f"background: {c}; border: 1px solid #222;")
            btn.clicked.connect(lambda _c=False, c=c: self._colour(c))
            sw.addWidget(btn, k // 8, k % 8)
        b.addWidget(QLabel("Colour (plain prims)"))
        b.addLayout(sw)
        self.hover_line = QLineEdit()
        self.hover_line.setPlaceholderText("Hover text (floats over it)")
        self.hover_line.returnPressed.connect(self._hover)
        b.addWidget(self.hover_line)
        row = QHBoxLayout()
        for label, fn in (("Take", lambda: self._sel(self._take)), ("Copy", lambda: self._sel(self.world.copy_object)),
                          ("Delete", lambda: self._sel(self._delete))):
            btn = QPushButton(label)
            btn.clicked.connect(fn)
            row.addWidget(btn)
        b.addLayout(row)
        b.addStretch(1)

    def _fill_build(self):
        self.rez_pick.clear()
        for it in self.world.inventory():
            if it["kind"] == "object":
                self.rez_pick.addItem(it["name"], it["id"])

    def _create(self, key):
        it = {"id": 0, "key": f"obj:{key}", "name": catalog.OBJECTS[key][0], "kind": "object", "data": {"obj": key}}
        self._rez(it)

    def _rez_picked(self):
        it = self.world.item(self.rez_pick.currentData())
        if it:
            self._rez(it)

    def _select(self, o):
        self.selected = o["id"]
        self.world_version = -1
        self.edit_label.setText(f"<b>Edit:</b> {esc_html(o['name'])}")
        self.hover_line.setText(o.get("hover") or "")

    def _sel(self, fn):
        o = self.world.obj(self.selected) if self.selected else None
        if o is not None:
            fn(o)

    def _nudge(self, d):
        self._sel(lambda o: self.world.edit(o, x=o["x"] + d[0], y=max(0.0, o["y"] + d[1]), z=o["z"] + d[2]))

    def _turn(self, deg):
        self._sel(lambda o: self.world.edit(o, yaw=(o["yaw"] + deg) % 360))

    def _scale(self, k):
        self._sel(lambda o: self.world.edit(o, scale=max(0.2, min(5.0, o.get("scale", 1.0) * k))))

    def _colour(self, c):
        self._sel(lambda o: self.world.edit(o, colour=c))

    def _hover(self):
        text = self.hover_line.text().strip() or None
        self._sel(lambda o: self.world.edit(o, hover=text))

    def _take(self, o):
        it = self.world.take_object(o)
        self.selected = None
        self._toast(f"{it['name']} is back in your inventory.")

    def _delete(self, o):
        self.world.delete_object(o)
        self.selected = None

    # appearance
    def _build_appearance(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        inner = QWidget()
        inner.setStyleSheet("background: transparent;")
        form = QFormLayout(inner)
        form.setLabelAlignment(Qt.AlignRight)
        self.ap = {}
        self.ap_loading = False

        def combo(key, values, label):
            c = QComboBox()
            for v in values:
                c.addItem(str(v).title() if v else "None", v)
            c.currentIndexChanged.connect(self._ap_changed)
            form.addRow(label, c)
            self.ap[key] = c

        self.ap_preset = QComboBox()
        self.ap_preset.addItem("(start from a body...)", None)
        for name in BODY_ORDER:
            self.ap_preset.addItem(name, name)
        self.ap_preset.currentIndexChanged.connect(self._ap_preset)
        form.addRow("Body", self.ap_preset)
        combo("head", ["canine", "feline", "rodent", "ursine", "bird", "reptile", "bovine", "deer", "alpaca",
                       "amphibian", "insect", "fish", "golem"], "Head")
        combo("ears", ["pointed", "round", "long", "tufted", "floppy", "small", "fin", "none"], "Ears")
        combo("tail", ["fluffy", "thin", "thick", "ringed", "feathers", "puff", "stub", "fin", None], "Tail")
        combo("legs", ["digi", "plant", "hoof"], "Legs")
        combo("wings", [None, "feather", "bat", "insect"], "Wings")
        combo("horns", [None, "small", "curved", "antlers", "dragon"], "Horns")
        combo("surface", ["fur", "scales", "feathers", "skin", "metal", "spirit"], "Skin")
        combo("frame", ["m", "f", "n"], "Frame")
        for key, label, lo, hi in (("height", "Height", 80, 125), ("build", "Build", 80, 140),
                                   ("head_size", "Head size", 80, 130), ("snout", "Snout", 20, 160),
                                   ("ear_size", "Ear size", 50, 160), ("tail_size", "Tail size", 50, 160)):
            s = QSlider(Qt.Horizontal)
            s.setRange(lo, hi)
            s.valueChanged.connect(self._ap_changed)
            form.addRow(label, s)
            self.ap[key] = s
        self.ap_colours = {}
        for key, label in (("fur", "Fur"), ("belly", "Belly / muzzle"), ("accent", "Markings"), ("eyes", "Eyes"),
                           ("nose", "Nose / beak"), ("horn", "Horns")):
            b = QPushButton()
            b.setFixedHeight(22)
            b.clicked.connect(lambda _c=False, key=key: self._ap_pick_colour(key))
            form.addRow(label, b)
            self.ap_colours[key] = b
        self.ap_marks = {}
        grid = QGridLayout()
        for k, mark in enumerate(["belly", "muzzle", "socks", "eartips", "tailtip", "mask", "blaze", "saddle",
                                  "stripes", "spots", "speckles", "cheeks"]):
            c = QCheckBox(mark)
            c.toggled.connect(self._ap_changed)
            grid.addWidget(c, k // 3, k % 3)
            self.ap_marks[mark] = c
        form.addRow("Markings", grid)
        self.ap_extras = {}
        grid = QGridLayout()
        for k, extra in enumerate(["whiskers", "mane", "ruff", "hair", "crest", "antennae", "quills", "longneck",
                                   "lure", "fins", "glowcore", "plates"]):
            c = QCheckBox(extra)
            c.toggled.connect(self._ap_changed)
            grid.addWidget(c, k // 3, k % 3)
            self.ap_extras[extra] = c
        form.addRow("Extras", grid)
        self.ap_worn = QVBoxLayout()
        form.addRow("Wearing", self.ap_worn)
        scroll.setWidget(inner)
        self.appearance.body.addWidget(scroll, 1)
        row = QHBoxLayout()
        for label, fn in (("Save Body...", self._ap_save_body), ("Save Outfit...", self._ap_save_outfit)):
            b = QPushButton(label)
            b.clicked.connect(fn)
            row.addWidget(b)
        self.appearance.body.addLayout(row)
        self.ap_timer = QTimer(self)
        self.ap_timer.setSingleShot(True)
        self.ap_timer.timeout.connect(self._ap_apply)

    def _load_appearance(self):
        s = self.world.me.look
        self.ap_loading = True
        for key in ("head", "ears", "tail", "legs", "wings", "horns", "surface", "frame"):
            c = self.ap[key]
            i = c.findData(s.get(key))
            c.setCurrentIndex(max(0, i))
        for key in ("height", "build", "head_size", "snout", "ear_size", "tail_size"):
            self.ap[key].setValue(int(round(s.get(key, 1.0) * 100)))
        for key, b in self.ap_colours.items():
            col = s.get(key, "#888888")
            b.setStyleSheet(f"background: {col}; border: 1px solid #222;")
            b.setProperty("colour", col)
        for mark, c in self.ap_marks.items():
            c.setChecked(mark in s.get("markings", []))
        for extra, c in self.ap_extras.items():
            c.setChecked(extra in s.get("extras", []))
        self.ap_preset.setCurrentIndex(0)
        self.ap_loading = False
        self._fill_worn()

    def _fill_worn(self):
        while self.ap_worn.count():
            item = self.ap_worn.takeAt(0)
            if item.layout():
                while item.layout().count():
                    w_ = item.layout().takeAt(0).widget()
                    if w_:
                        w_.deleteLater()
            elif item.widget():
                item.widget().deleteLater()
        if not self.world.me.wear:
            self.ap_worn.addWidget(QLabel("(nothing)"))
        for wr in self.world.me.wear:
            it = catalog.ITEMS.get(wr["key"])
            if not it:
                continue
            row = QHBoxLayout()
            row.addWidget(QLabel(it["name"]), 1)
            b = QPushButton("Take Off")
            b.clicked.connect(lambda _c=False, slot=it["slot"]: (self.world.take_off(slot), self._fill_worn()))
            row.addWidget(b)
            self.ap_worn.addLayout(row)

    def _ap_preset(self):
        name = self.ap_preset.currentData()
        if name and not self.ap_loading:
            import copy
            self.world.me.look = copy.deepcopy(PRESETS[name])
            self.world.me.version += 1
            self.world.save()
            self._load_appearance()

    def _ap_pick_colour(self, key):
        b = self.ap_colours[key]
        col = QColorDialog.getColor(QColor(b.property("colour") or "#888888"), self, "Choose a colour")
        if col.isValid():
            b.setProperty("colour", col.name())
            b.setStyleSheet(f"background: {col.name()}; border: 1px solid #222;")
            self._ap_changed()

    def _ap_changed(self, *_):
        if not self.ap_loading:
            self.ap_timer.start(120)

    def _ap_apply(self):
        s = self.world.me.look
        for key in ("head", "ears", "tail", "legs", "wings", "horns", "surface", "frame"):
            s[key] = self.ap[key].currentData()
        for key in ("height", "build", "head_size", "snout", "ear_size", "tail_size"):
            s[key] = self.ap[key].value() / 100
        for key, b in self.ap_colours.items():
            s[key] = b.property("colour") or s.get(key)
        s["markings"] = [m for m, c in self.ap_marks.items() if c.isChecked()]
        s["extras"] = [x for x, c in self.ap_extras.items() if c.isChecked()] + \
            [x for x in s.get("extras", []) if x not in self.ap_extras]
        self.world.me.version += 1
        self.world.save()

    def _ap_save_body(self):
        name, ok = QInputDialog.getText(self, "Save Body", "Name this body:", text=f"My {self.world.me.look['species']}")
        if ok and name.strip():
            self.world.save_body(name.strip())
            self._toast(f"Saved '{name.strip()}' to Body Parts.")

    def _ap_save_outfit(self):
        name, ok = QInputDialog.getText(self, "Save Outfit", "Name this outfit:", text="My outfit")
        if ok and name.strip():
            self.world.save_outfit(name.strip())
            self._toast(f"Saved '{name.strip()}' to Outfits.")

    # ---- logging in ----
    def _show_login(self):
        w = self.world
        self.login_panel = QFrame(self)
        self.login_panel.setObjectName("floater")
        self.login_panel.resize(420, 330)
        lay = QVBoxLayout(self.login_panel)
        logo = QLabel("<span style='font-size:28px; color:#7FD8FF'><b>Second Life</b></span><br>"
                      "<span style='color:#9AA8B8'>Your world. Your imagination.</span>")
        logo.setAlignment(Qt.AlignCenter)
        lay.addWidget(logo)
        form = QFormLayout()
        if w.has_account():
            name = f"{w.player['first']} {w.player['last']}"
            form.addRow("Name", QLabel(f"<b>{esc_html(name)}</b>"))
            self.login_start = QComboBox()
            self.login_start.addItem("My last location", None)
            for key in SIM_ORDER:
                self.login_start.addItem(w.sims[key].name, key)
            form.addRow("Start at", self.login_start)
        else:
            default = ""
            try:
                from ... import timeline
                prof = timeline.profile() or {}
                default = prof.get("handle") or prof.get("name") or ""
            except Exception:
                pass
            default = (default or w.aim_name or "Newbie").split()[0][:31]
            self.login_first = QLineEdit(default)
            self.login_last = QComboBox()
            for s_ in residents.SURNAMES:
                self.login_last.addItem(s_)
            self.login_body = QComboBox()
            for b in BODY_ORDER:
                self.login_body.addItem(b)
            form.addRow("First name", self.login_first)
            form.addRow("Last name", self.login_last)
            form.addRow("Starting body", self.login_body)
        lay.addLayout(form)
        self.login_status = QLabel("")
        self.login_status.setObjectName("dim")
        self.login_status.setAlignment(Qt.AlignCenter)
        lay.addWidget(self.login_status)
        go = QPushButton("Connect" if w.has_account() else "Create Account and Connect")
        go.setMinimumHeight(34)
        go.clicked.connect(self._connect)
        lay.addWidget(go)
        self.login_panel.show()
        self.resizeEvent(None)

    def _connect(self):
        if not self.world.has_account():
            first = "".join(ch for ch in self.login_first.text().strip() if ch.isalnum())[:31]
            if not first:
                self.login_status.setText("Pick a first name.")
                return
        if self.desktop is not None and not network.is_connected():
            self.login_status.setText("Connecting to the Internet...")
            network.connect(self.desktop, then=self._enter)
            return
        self._enter()

    def _enter(self):
        w = self.world
        if not w.has_account():
            first = "".join(ch for ch in self.login_first.text().strip() if ch.isalnum())[:31]
            w.create_account(first, self.login_last.currentText(), self.login_body.currentText())
        else:
            start = self.login_start.currentData()
            if start:
                w.me.sim = start
                w.me.x, w.me.z, w.me.yaw = w.sims[start].landing
        self.login_panel.hide()
        self.logged_in = True
        self.loaded = None
        w.login()
        self.quick.setFocus()
        self._toast(f"Welcome to Second Life, {w.me.full}!")

    def network_lost(self):
        if self.logged_in:
            self.world.save()
            self.logged_in = False
            self.login_status.setText("You were logged out: the Internet connection was lost.")
            self.login_panel.show()
            self.login_panel.raise_()

    def shutdown(self):
        try:
            if self.world.me:
                self.world.save()
        finally:
            self.timer.stop()

    def closeEvent(self, e):
        self.shutdown()
        e.accept()


def esc_html(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


_frame = None
_listening = False


def launch(desktop):
    global _frame, _listening
    if _frame is not None and isValid(_frame):
        desktop.open_window(_frame)
        return _frame
    try:
        viewer = Viewer(desktop)
    except Exception:
        open_placeholder(desktop, TITLE, sl_icon(), "Second Life couldn't start.\n\n" + traceback.format_exc(limit=3),
                         sound_event="error")
        return None
    if not _listening:
        network.on_disconnect(desktop, _network_lost)
        _listening = True
    _frame = XPWindow(desktop, TITLE, viewer, sl_icon(), size=(1180, 760))
    viewer.frame = _frame
    _frame.destroyed.connect(_forget)
    desktop.open_window(_frame)
    return _frame


def _forget(*_):
    global _frame
    _frame = None


def _network_lost(quiet):
    if _frame is not None and isValid(_frame):
        _frame.content.network_lost()


def shutdown():
    if _frame is not None and isValid(_frame):
        _frame.content.shutdown()
        _frame.desktop.close_window(_frame)


__all__ = ["launch", "shutdown", "sl_icon", "esc"]
