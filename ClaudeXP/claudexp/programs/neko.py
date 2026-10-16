"""Copilot Neko, the classic desktop cat.

Neko behaves like the original (neko.com for the NEC PC-9801, Kenji Gotoh's Neko DA for the Mac, IBM's OS/2 Cat
and Mouse): it chases the mouse pointer around the desktop in eight directions. When it catches up it stops, licks
itself, scratches, yawns and falls asleep; move the pointer and it jolts awake and runs after it again. If the
pointer leaves the desktop, Neko scratches at that edge of the screen. In 'Play by itself' mode it wanders on its own
instead (like desktopPet's Neko). The sprites are the classic 32x32 frames - see neko_art.py.
"""
import json
import math
import random
import time
import warnings

from PySide6.QtCore import QPoint, QRect, Qt, QTimer
from PySide6.QtGui import QAction, QActionGroup, QCursor, QPainter
from PySide6.QtWidgets import QMenu, QMessageBox, QSystemTrayIcon, QToolTip, QWidget

from ..paths import DATA
from ..tray import TrayIcon
from . import neko_art as art

SETTINGS_FILE = DATA / "copilot_neko.json"
DEFAULT_SETTINGS = {"start_at_logon": True, "palette": "white", "bubbles": True, "mode": "chase",
                    "speed": "normal", "size": 1}
# Neko DA's speed buttons: (milliseconds per step, pixels per step at size 1)
SPEEDS = {"slow": (160, 9), "normal": (125, 13), "fast": (90, 16)}
WAKE_DISTANCE = 16            # how far the pointer must move to wake a resting Neko
# how many steps each resting pose lasts, as in the original
STOP_STEPS, LICK_STEPS, SCRATCH_STEPS, YAWN_STEPS, AWAKE_STEPS, WALL_STEPS = 4, 10, 4, 3, 3, 10
RESTING = {"stop", "lick", "scratch", "yawn", "sleep", "wall"}


class NekoWidget(QWidget):
    """The cat itself: a borderless sprite that runs about on the desktop."""

    def __init__(self, desktop, controller):
        super().__init__(desktop)
        self.desktop = desktop
        self.controller = controller
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self._palette = controller.palette()
        self.state = "sleep"
        self.count = 0                        # steps spent in this state
        self.tick_no = 0
        self.direction = "down"
        self.wall = None
        self.rest_point = None                # where the pointer was when Neko settled down
        self.roam_target = None
        self.next_roam = time.monotonic() + random.uniform(20, 60)
        self._dragging = False
        self._pressed_at = None
        self._moved_by_user = False
        self._roamed = False                  # Neko has left its spot by Clippy
        self._drag_offset = QPoint()
        self._last_balloon = 0.0
        self._apply_size()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self.start_timer()
        self._place_default()
        self.rest_point = self._pointer()
        self.show()
        QTimer.singleShot(1500, self._place_default)          # again once the desktop icons have been laid out

    def start_timer(self):
        self._timer.start(SPEEDS.get(self.controller.settings["speed"], SPEEDS["normal"])[0])

    def _apply_size(self):
        self.scale = 2 if self.controller.settings["size"] == 2 else 1
        self.resize(art.CELL * self.scale, art.CELL * self.scale)

    # ---- where things are -----------------------------------------------------------------------------------------
    def _obstacles(self):
        """What Neko shouldn't sit on: desktop icons, Clippy, the desktop widgets (not windows or the taskbar)."""
        from ..desktop_icons import DesktopIcon
        from ..wm import XPWindow
        skip = {self, getattr(self.desktop, "taskbar", None), getattr(self.desktop, "start_menu", None),
                getattr(self.desktop, "balloon", None), getattr(self.desktop, "hdd", None)}
        return [w.geometry() for w in self.desktop.children()
                if isinstance(w, QWidget) and w.isVisible() and w not in skip and not isinstance(w, XPWindow)
                and (isinstance(w, DesktopIcon) or w.width() < self.desktop.width() // 2)]

    def _clippy_rect(self):
        """Where Clippy stands (or would stand: his saved spot, else the bottom-right corner)."""
        c = getattr(self.desktop, "clippy", None)
        if c is not None and c.widget.isVisible():
            return c.widget.geometry()
        from ..clippy import art as clippy_art, settings
        area = self.desktop.work_area()
        w, h = clippy_art.W, clippy_art.H
        pos = settings().get("pos")
        x, y = pos if pos else (area.width() - w - 24, area.height() - h - 10)
        return QRect(int(x), int(y), w, h)

    def _place_default(self):
        """Just left of Clippy, sitting on the same line (or the nearest free spot further left), until Neko has
        gone off on its own or you've moved it."""
        rect = self.desktop.work_area()
        if self._moved_by_user or self._roamed:
            self.move(max(0, min(self.x(), rect.right() - self.width())),
                      max(0, min(self.y(), rect.bottom() - self.height())))
            return
        clip = self._clippy_rect()
        y = max(0, min(rect.bottom() - self.height(), clip.bottom() - self.height() - 2))
        clippy = getattr(self.desktop, "clippy", None)
        mine = {clippy.widget.geometry(), clippy.balloon.geometry()} if clippy is not None else set()
        taken = [g.adjusted(-6, -6, 6, 6) for g in self._obstacles() if g not in mine]
        x = start = max(0, clip.left() - self.width() + 6)
        while x >= 0:
            if not any(QRect(x, y, self.width(), self.height()).intersects(g) for g in taken):
                break
            x -= 8
        else:
            x = start                                          # nowhere free: next to Clippy anyway
        self.move(x, y)

    def _pointer(self):
        return self.desktop.mapFromGlobal(QCursor.pos())

    def _target(self):
        """Where Neko wants its feet: just above the pointer's tip (or its own wandering spot). Also returns the
        wall it would have to scratch at, if the target is off the desktop."""
        if self.controller.settings["mode"] == "roam":
            point = self.roam_target or self.pos() + QPoint(self.width() // 2, self.height())
        else:
            point = self._pointer()
        area = self.desktop.work_area()            # (the pointer on the taskbar: Neko scratches at the floor)
        x, y = point.x() - self.width() // 2, point.y() - self.height() - 2
        wall = None
        if point.x() < area.left():
            wall = "left"
        elif point.x() > area.right():
            wall = "right"
        elif point.y() < area.top():
            wall = "up"
        elif point.y() > area.bottom():
            wall = "down"
        x = max(0, min(area.width() - self.width(), x))
        y = max(0, min(area.height() - self.height(), y))
        return QPoint(x, y), wall

    # ---- the original Neko's state machine -----------------------------------------------------------------------
    def _set(self, state):
        self.state = state
        self.count = 0
        if state == "stop":
            self.rest_point = self._pointer() if self.controller.settings["mode"] == "chase" else None

    def _woken(self):
        """Has the pointer moved away from where Neko settled down?"""
        if self.controller.settings["mode"] == "roam":
            return self.roam_target is not None
        if self.rest_point is None:
            return True
        p = self._pointer()
        return abs(p.x() - self.rest_point.x()) > WAKE_DISTANCE or abs(p.y() - self.rest_point.y()) > WAKE_DISTANCE

    def _tick(self):
        if self._dragging or not self.isVisible():
            return
        self.tick_no += 1
        self.count += 1
        if self.controller.settings["mode"] == "roam":
            self._roam_think()
        if self.state in RESTING and self._woken():
            self._set("awake")
        elif self.state == "stop":
            if self.count >= STOP_STEPS:
                _t, wall = self._target()
                if wall and self.controller.settings["mode"] == "chase":
                    self.wall = wall
                    self._set("wall")
                else:
                    self._set("lick")
        elif self.state == "lick" and self.count >= LICK_STEPS:
            self._set("scratch")
        elif self.state == "scratch" and self.count >= SCRATCH_STEPS:
            self._set("yawn")
        elif self.state == "yawn" and self.count >= YAWN_STEPS:
            self._set("sleep")
            self._chatter()
        elif self.state == "wall" and self.count >= WALL_STEPS:
            self._set("scratch")
        elif self.state == "awake" and self.count >= AWAKE_STEPS:
            self._set("run")
        elif self.state == "run":
            self._run()
        self.update()

    def _run(self):
        target, _wall = self._target()
        dx, dy = target.x() - self.x(), target.y() - self.y()
        dist = math.hypot(dx, dy)
        step = SPEEDS.get(self.controller.settings["speed"], SPEEDS["normal"])[1] * self.scale
        if dist <= step:
            self.move(target)
            self.roam_target = None
            self._set("stop")
            return
        mx, my = dx * step / dist, dy * step / dist
        # eight directions, as the sprites have them
        angle = math.degrees(math.atan2(-my, mx)) % 360
        self.direction = ("right", "ur", "up", "ul", "left", "dl", "down", "dr")[int((angle + 22.5) // 45) % 8]
        self.move(round(self.x() + mx), round(self.y() + my))
        self._roamed = True
        self.raise_()                          # Neko runs over the windows, as it always did

    def _roam_think(self):
        """Play by itself: every so often pick somewhere to run to (sometimes an edge, to scratch at it)."""
        now = time.monotonic()
        if self.roam_target is None and self.state in RESTING and now >= self.next_roam:
            area = self.desktop.work_area()
            if random.random() < 0.2:
                side = random.choice(("left", "right", "up"))
                point = {"left": QPoint(-50, random.randint(40, area.height() - 40)),
                         "right": QPoint(area.width() + 50, random.randint(40, area.height() - 40)),
                         "up": QPoint(random.randint(40, area.width() - 40), -50)}[side]
                self.wall = side
            else:
                point = QPoint(random.randint(20, area.width() - 20), random.randint(60, area.height() - 10))
                self.wall = None
            self.roam_target = point
            self.next_roam = now + random.uniform(25, 90)
        elif self.state == "stop" and self.wall and self.count >= STOP_STEPS - 1:
            self._set("wall")

    def _frame(self):
        alt = self.tick_no % 2
        s = self.state
        if s == "run":
            return art.RUN[self.direction][alt]
        if s == "stop":
            return art.SIT
        if s == "lick":
            return (art.LICK, art.SIT)[alt]
        if s == "scratch":
            return art.SCRATCH[alt]
        if s == "yawn":
            return art.YAWN
        if s == "sleep":
            return art.SLEEP[(self.tick_no // 4) % 2]          # slow breathing
        if s == "awake":
            return art.AWAKE
        if s == "wall":
            return art.WALL[self.wall or "up"][alt]
        if s == "dangle":
            return art.DANGLE[alt]
        return art.SIT

    # ---- you and Neko --------------------------------------------------------------------------------------------
    def _chatter(self):
        now = time.monotonic()
        if self.controller.settings["bubbles"] and now - self._last_balloon > 60 and random.random() < 0.25:
            self._bubble(random.choice(["Zzz...", "Mrrrrow...", "Prrr...", "*curls up*"]))
            self._last_balloon = now

    def _bubble(self, text):
        if not self.isVisible():
            return
        pos = self.mapToGlobal(self.rect().topLeft() + QPoint(self.width() // 2, -8))
        QToolTip.showText(pos, text, self)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._pressed_at = event.globalPosition().toPoint()
            self._drag_offset = event.pos()
            self.raise_()

    def mouseMoveEvent(self, event):
        if self._pressed_at is None:
            return
        if not self._dragging and (event.globalPosition().toPoint() - self._pressed_at).manhattanLength() > 4:
            self._dragging = True
            self._set("dangle")
        if self._dragging:
            new_pos = self.pos() + event.pos() - self._drag_offset
            self.move(max(0, min(new_pos.x(), self.desktop.width() - self.width())),
                      max(0, min(new_pos.y(), self.desktop.height() - self.height())))
            self.tick_no += 1
            self.update()

    def mouseReleaseEvent(self, event):
        if self._pressed_at is None:
            return
        self._pressed_at = None
        if self._dragging:                      # put down: it sits where you left it
            self._dragging = False
            self._moved_by_user = self._roamed = True
            self._set("stop")
        else:                                   # a pat on the head
            self._set("lick")
            if self.controller.settings["bubbles"]:
                self._bubble(random.choice(["Mrrrp!", "Purr...", "Neko likes that."]))
        self.rest_point = self._pointer()
        self.update()

    def mouseDoubleClickEvent(self, event):
        self._set("sleep")
        self.rest_point = self._pointer()
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.drawPixmap(0, 0, art.frame(self._frame(), self._palette, self.scale))


_controller = None


class NekoController:
    def __init__(self, desktop):
        self.desktop = desktop
        self.settings = dict(DEFAULT_SETTINGS)
        try:
            data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        except FileNotFoundError:
            data = {}
        except (OSError, json.JSONDecodeError) as exc:
            warnings.warn(f"Could not read Copilot Neko settings from {SETTINGS_FILE}: {exc}")
            data = {}
        if isinstance(data, dict):
            self.settings.update({key: value for key, value in data.items()
                                  if key in DEFAULT_SETTINGS and isinstance(value, type(DEFAULT_SETTINGS[key]))})
        if self.settings["palette"] != "random" and self.settings["palette"] not in art.PALETTES:
            self.settings["palette"] = "white"          # (the old hand-drawn cat's colours)
        if self.settings["mode"] not in ("chase", "roam"):
            self.settings["mode"] = "chase"
        if self.settings["speed"] not in SPEEDS:
            self.settings["speed"] = "normal"
        self.tray = TrayIcon(desktop, art.paw_icon(32), desktop)
        self.tray.setToolTip("Copilot Neko")
        self.menu = QMenu(desktop)
        self.menu.setStyleSheet("QMenu { background: white; border: 1px solid #ACA899; "
                                "font-family: Tahoma; font-size: 11px; }"
                                "QMenu::item { padding: 4px 24px 4px 20px; }"
                                "QMenu::item:selected { background: #316AC5; color: white; }")
        self.tray.setContextMenu(self.menu)
        self.tray.activated.connect(self._tray_activated)
        self.widget = None
        self._build_menu()
        self.tray.show()
        if self.settings["start_at_logon"]:
            self.show()

    def _save(self):
        try:
            SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
            SETTINGS_FILE.write_text(json.dumps(self.settings, indent=2), encoding="utf-8")
        except OSError as exc:
            QMessageBox.warning(self.desktop, "Copilot Neko Settings",
                                f"Could not save Neko's settings:\n{exc}")

    def palette(self):
        selected = self.settings["palette"]
        return random.choice(list(art.PALETTES)) if selected == "random" else selected

    def _choice_menu(self, title, key, options):
        sub = self.menu.addMenu(title)
        group = QActionGroup(sub)
        group.setExclusive(True)
        for value, label in options:
            if value is None:
                sub.addSeparator()
                continue
            action = QAction(label, sub)
            action.setCheckable(True)
            action.setChecked(self.settings[key] == value)
            action.triggered.connect(lambda _checked=False, v=value: self._set(key, v))
            group.addAction(action)
            sub.addAction(action)
        return sub

    def _build_menu(self):
        self.menu.clear()
        self.start_action = QAction("Start Copilot Neko with ClaudeXP", self.menu)
        self.start_action.setCheckable(True)
        self.start_action.setChecked(self.settings["start_at_logon"])
        self.start_action.toggled.connect(lambda on: self._set("start_at_logon", on))
        self.menu.addAction(self.start_action)

        self.show_action = QAction("Show Copilot Neko", self.menu)
        self.show_action.setCheckable(True)
        self.show_action.setChecked(self.widget is not None and self.widget.isVisible())
        self.show_action.toggled.connect(self._set_visible)
        self.menu.addAction(self.show_action)
        self.menu.addSeparator()

        self._choice_menu("Behavior", "mode", [("chase", "Chase the mouse pointer"), ("roam", "Play by itself")])
        self._choice_menu("Speed", "speed", [("slow", "Slow"), ("normal", "Normal"), ("fast", "Fast")])
        self._choice_menu("Size", "size", [(1, "Classic (32 x 32)"), (2, "Large (64 x 64)")])
        self._choice_menu("Fur Color", "palette", [("random", "Random each time"), (None, "")]
                          + [(k, v["name"]) for k, v in art.PALETTES.items()])

        bubbles = QAction("Chatty desktop bubbles", self.menu)
        bubbles.setCheckable(True)
        bubbles.setChecked(self.settings["bubbles"])
        bubbles.toggled.connect(lambda on: self._set("bubbles", on))
        self.menu.addAction(bubbles)
        self.menu.addAction("Give Neko a treat", self._treat)
        self.menu.addSeparator()
        self.menu.addAction("About Neko...", self._about)
        self.menu.addAction("Close Neko", self.hide)
        self.menu.aboutToShow.connect(self._refresh_menu)

    def _refresh_menu(self):
        self.show_action.setChecked(self.widget is not None and self.widget.isVisible())

    def _set(self, key, value):
        self.settings[key] = value
        self._save()
        w = self.widget
        if w is None:
            return
        if key == "palette":
            w._palette = self.palette()
        elif key == "speed":
            w.start_timer()
        elif key == "size":
            w._apply_size()
            w._place_default()
        elif key == "mode":
            w.roam_target = None
            w._set("stop")
        w.update()

    def _set_visible(self, visible):
        self.show() if visible else self.hide()

    def show(self):
        if self.widget is None:
            self.widget = NekoWidget(self.desktop, self)
        else:
            self.widget.show()
            self.widget.start_timer()
        self.desktop.neko = self.widget
        self.widget.raise_()
        self._refresh_menu()

    def hide(self):
        if self.widget is not None:
            self.widget._timer.stop()
            self.widget.hide()
        if self.desktop.neko is self.widget:
            self.desktop.neko = None
        self._refresh_menu()

    def _treat(self):
        if self.widget is None:
            self.show()
        self.widget._set("lick")
        self.widget.rest_point = self.widget._pointer()
        if self.settings["bubbles"]:
            self.widget._bubble("A treat! Prrrr...")
        self.widget.update()

    def _about(self):
        from ..explorer.dialogs import msgbox
        msgbox(self.desktop, "About Copilot Neko",
               "Copilot Neko - the classic desktop cat.\n\n"
               "After neko.com for the NEC PC-9801, Neko DA by Kenji Gotoh (1989) and IBM's Cat and Mouse "
               "for OS/2.\n\nSprites from webneko.net, via desktopPet's Neko by Adriano Petrucci "
               "(github.com/Adrianotiger/desktopPet, MIT licence).",
               icon="info", window_icon=art.neko_icon(16))

    def _tray_activated(self, reason):
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self._set_visible(self.widget is None or not self.widget.isVisible())


def install(desktop):
    return _controller_for(desktop).widget


def start_at_logon(desktop):
    controller = _controller_for(desktop)
    if controller.settings["start_at_logon"]:
        controller.show()


def _controller_for(desktop):
    global _controller
    if _controller is None or _controller.desktop is not desktop:
        if _controller is not None:
            _controller.tray.hide()
            _controller.tray.deleteLater()
        _controller = NekoController(desktop)
    return _controller


def launch(desktop):
    controller = _controller_for(desktop)
    controller.show()
    if controller.settings["bubbles"]:
        controller.widget._bubble("Copilot Neko is here to keep you company.")
    return controller.widget


def shutdown():
    if _controller is not None:
        if _controller.widget is not None:
            _controller.widget.close()
            _controller.desktop.neko = None
        _controller.widget = None


def neko_icon(size=32):
    return art.neko_icon(size)
