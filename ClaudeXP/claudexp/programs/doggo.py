"""Doggo, a desktop dog in the spirit of Neko - drawn from the Rover sprite sheet in Local Storage\\Rover.

He trots in from the distance when you start him and sits on the desktop. Three ways to be:
- Follow me: he sniffs his way over to the mouse pointer and sits beside it, now and then greeting you or panting;
- Play by himself (the default): he wanders the desktop, and every so often does one of his tricks - digs, fetches,
  reads the paper or a book, chews a bone, throws a party, shows you a picture, takes notes, brings the mail;
- Stay put: he stays where he is and does his tricks there.
Left alone a few minutes he mopes, then lies down and falls asleep; move the pointer near him (or click him) and he
wakes up. Click him for a pat, double-click for a game of fetch, drag him somewhere else, right-click for his menu -
the same as his icon in the notification area. The frames are cut from the sheet as he needs them (doggo_art)."""
import json
import math
import random
import time
import warnings

from PySide6.QtCore import QPoint, Qt, QTimer
from PySide6.QtGui import QAction, QActionGroup, QCursor, QPainter
from PySide6.QtWidgets import QMenu, QMessageBox, QSystemTrayIcon, QToolTip, QWidget

from ..paths import DATA
from ..tray import TrayIcon
from . import doggo_art as art

SETTINGS_FILE = DATA / "doggo.json"
DEFAULT_SETTINGS = {"start_at_logon": False, "mode": "play", "speed": "normal", "size": 2, "bubbles": True}
SIZES = {1: 1.5, 2: 2.0, 3: 3.0}                # menu size -> scale of the 38-pixel frames
SPEEDS = {"slow": 3, "normal": 5, "fast": 8}    # pixels per step at scale 1
TICK_MS = 100                                   # ten frames a second, as the sheet was drawn
MOPE_AFTER, SLEEP_AFTER = 120, 200              # seconds without you before he mopes, then naps
WAKE_DISTANCE = 160                             # the pointer this near a sleeping doggo wakes him


class DoggoWidget(QWidget):
    """The dog himself: a borderless sprite on the desktop, playing a queue of frames."""

    def __init__(self, desktop, controller):
        super().__init__(desktop)
        self.desktop = desktop
        self.controller = controller
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setMouseTracking(False)
        self.state = "sit"                      # sit, walk, act, sleep, leave
        self.queue = []                         # [(frame, mirrored)] still to play
        self.after = None                       # what happens when the queue runs out
        self.current = (art.SIT, False)
        self.facing_right = False
        self.target = None                      # where he's walking to (his top-left corner)
        self.walk_i = 0
        self.next_think = time.monotonic() + random.uniform(4, 8)
        self.last_you = time.monotonic()        # the last time the pointer moved (or you touched him)
        self.moped = False
        self._last_pointer = self._pointer()
        self._pressed_at = None
        self._dragging = False
        self._drag_offset = QPoint()
        self._apply_size()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(TICK_MS)
        self._place_default()
        self.show()
        self.raise_()
        self.play(art.ARRIVE, then=lambda: self.say(random.choice(["Woof! I'm here!", "Hi! I'm Doggo!"])))

    # ---- size and place -------------------------------------------------------------------------------------------
    def _apply_size(self):
        self.scale = SIZES.get(self.controller.settings["size"], 2.0)
        side = int(art.CELL * self.scale)
        bottom = self.y() + self.height() if self.isVisible() else None
        self.resize(side, side)
        if bottom is not None:
            self.move(self.x(), bottom - side)
        self.update()

    def _area(self):
        return self.desktop.work_area()

    def _clamp(self, point):
        area = self._area()
        return QPoint(max(area.left(), min(point.x(), area.right() - self.width())),
                      max(area.top(), min(point.y(), area.bottom() - self.height())))

    def _place_default(self):
        """On the floor of the desktop, a little right of the middle."""
        area = self._area()
        self.move(self._clamp(QPoint(area.left() + int(area.width() * 0.62), area.bottom() - self.height() - 6)))

    def _pointer(self):
        return self.desktop.mapFromGlobal(QCursor.pos())

    def _centre(self):
        return self.pos() + QPoint(self.width() // 2, self.height() // 2)

    # ---- playing frames -------------------------------------------------------------------------------------------
    def play(self, frames, mirrored=False, then=None, state="act"):
        self.queue = [(k, mirrored) for k in frames]
        self.after = None
        self.state = state
        if self.queue:
            self.after = then
        elif then is not None:                  # (nothing to play: straight on)
            then()

    def say(self, text):
        if not self.controller.settings["bubbles"] or not self.isVisible():
            return
        QToolTip.showText(self.mapToGlobal(QPoint(self.width() // 2, -6)), text, self)

    def trick(self, name, chatty=True):
        """One of his tricks, from wherever he is (standing up first if he's asleep)."""
        label, frames, lines = art.ACTIONS[name]
        lead = art.WAKE if self.state == "sleep" else []
        self.target = None
        self.play(lead + frames, then=self._sat)
        if chatty and lines and random.random() < 0.7:
            QTimer.singleShot(len(lead) * TICK_MS + 600, lambda: self.isVisible() and self.say(random.choice(lines)))

    def _sat(self):
        self.state = "sit"
        self.current = (art.SIT, False)
        self.next_think = time.monotonic() + random.uniform(6, 16)

    # ---- walking --------------------------------------------------------------------------------------------------
    def walk_to(self, point):
        """Sniff along to `point` (his top-left corner), turning to his side first."""
        point = self._clamp(point)
        if (point - self.pos()).manhattanLength() < 12:
            return
        self.facing_right = point.x() > self.x()
        self.target = point
        if self.state == "walk":
            return
        lead = art.WAKE if self.state == "sleep" else []
        self.play(lead, then=lambda: self.play(art.WALK_START, self.facing_right, then=self._start_walking))

    def _start_walking(self):
        self.state = "walk"
        self.walk_i = 0

    def _follow_spot(self, pointer):
        """Where he sits when he's following you: beside the pointer, on the side he came from."""
        side = 1 if self.x() + self.width() // 2 > pointer.x() else -1
        return self._clamp(QPoint(pointer.x() - self.width() // 2 + side * int(self.width() * 0.7),
                                  pointer.y() - int(self.height() * 0.75)))

    def _step(self):
        if self.target is not None and self.controller.settings["mode"] == "follow":
            self.target = self._follow_spot(self._pointer())     # (you moved on: so does he)
        if self.target is None:
            self.play(art.WALK_END, self.facing_right, then=self._sat)
            return
        step = SPEEDS.get(self.controller.settings["speed"], 5) * self.scale
        d = self.target - self.pos()
        dist = math.hypot(d.x(), d.y())
        if dist <= step:
            self.move(self.target)
            self.target = None
            self.play(art.WALK_END, self.facing_right, then=self._arrived)
            return
        if (d.x() > 0) != self.facing_right and abs(d.x()) > self.width() // 2:
            self.facing_right = d.x() > 0          # (the pointer went the other way)
        self.move(self.pos() + QPoint(round(d.x() / dist * step), round(d.y() / dist * step)))
        self.current = (art.WALK[self.walk_i % len(art.WALK)], self.facing_right)
        self.walk_i += 1

    def _arrived(self):
        self._sat()
        if self.controller.settings["mode"] == "follow" and random.random() < 0.35:
            self.trick(random.choice(["greet", "pant", "happy", "bark"]))

    # ---- the clock ------------------------------------------------------------------------------------------------
    def _tick(self):
        now = time.monotonic()
        pointer = self._pointer()
        if (pointer - self._last_pointer).manhattanLength() > 3:
            self._last_pointer = pointer
            self.last_you = now
            self.moped = False
            if self.state == "sleep":                # (breathing away, curled up)
                d = pointer - self._centre()
                if math.hypot(d.x(), d.y()) < WAKE_DISTANCE * self.scale / 2 \
                        or self.controller.settings["mode"] == "follow":
                    self._wake()
        if self._dragging:
            return
        if self.queue:
            self.current = self.queue.pop(0)
            if not self.queue and self.after is not None:
                after, self.after = self.after, None
                after()
        elif self.state == "walk":
            self._step()
        elif self.state == "sleep":
            self.play(art.SLEEP, state="sleep")
            if random.random() < 0.05:
                self.say(random.choice(["Zzz...", "*snore*", "*dreams of bones*"]))
        elif self.state == "leave":
            self.controller.hide()
            return
        else:
            self._think(now, pointer)
        self.update()

    def _think(self, now, pointer):
        """Sitting: what next?"""
        mode = self.controller.settings["mode"]
        idle = now - self.last_you
        if idle > SLEEP_AFTER:
            self._nap()
            return
        if idle > MOPE_AFTER and not self.moped:
            self.moped = True
            self.trick("sad")
            return
        if mode == "follow":
            spot = self._follow_spot(pointer)
            if (spot - self.pos()).manhattanLength() > self.width() * 1.2:
                self.walk_to(spot)
                return
        if now < self.next_think:
            return
        roll = random.random()
        if mode == "play" and roll < 0.4:
            area = self._area()
            self.walk_to(QPoint(random.randint(area.left(), area.right() - self.width()),
                                random.randint(area.top() + area.height() // 3, area.bottom() - self.height())))
        elif roll < 0.8:
            self.trick(random.choice(art.TRICKS))
        else:
            self.play(random.choice(art.FIDGETS), then=self._sat)

    def _nap(self):
        self.target = None
        self.play(art.LIE_DOWN + art.FALL_ASLEEP, state="act",
                  then=lambda: setattr(self, "state", "sleep"))
        self.say("*yawn*")

    def _wake(self):
        self.last_you = time.monotonic()
        self.play(art.WAKE, then=self._sat)

    def leave(self):
        """Off he goes into the distance (then he's gone)."""
        self.target = None
        self.say(random.choice(["Bye bye!", "See you later!", "Woof! Bye!"]))
        self.play(art.LEAVE, then=lambda: setattr(self, "state", "leave"), state="act")

    # ---- you and him ----------------------------------------------------------------------------------------------
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._pressed_at = event.globalPosition().toPoint()
            self._drag_offset = event.pos()
            self.raise_()
        elif event.button() == Qt.RightButton:
            self.controller.menu.exec(event.globalPosition().toPoint())

    def mouseMoveEvent(self, event):
        if self._pressed_at is None:
            return
        if not self._dragging and (event.globalPosition().toPoint() - self._pressed_at).manhattanLength() > 4:
            self._dragging = True
            self.queue, self.after, self.target = [], None, None
            self.current = (art.HELD, False)
            self.update()
        if self._dragging:
            new = self.pos() + event.pos() - self._drag_offset
            self.move(max(0, min(new.x(), self.desktop.width() - self.width())),
                      max(0, min(new.y(), self.desktop.height() - self.height())))

    def mouseReleaseEvent(self, event):
        if self._pressed_at is None:
            return
        self._pressed_at = None
        self.last_you = time.monotonic()
        if self._dragging:                          # put down
            self._dragging = False
            self.move(self._clamp(self.pos()))
            self.state = "act"
            self.play(art.ACTIONS["happy"][1], then=self._sat)
            self.say(random.choice(["Wheee!", "Again! Again!", "Nice view from here."]))
            if self.controller.settings["mode"] == "follow":
                self.controller.settings["mode"] = "stay"     # (you put him there: he stays)
                self.controller._save()
        elif self.state == "sleep":
            self._wake()
            self.say("Huh? I'm up! I'm up!")
        else:                                       # a pat on the head
            self.trick(random.choice(["happy", "pant"]), chatty=False)
            self.say(random.choice(["*wags tail*", "Good doggo? Good doggo!", "Hehe, that tickles!"]))
        self.update()

    def mouseDoubleClickEvent(self, event):
        self.last_you = time.monotonic()
        self.trick("fetch")

    def paintEvent(self, event):
        k, mirrored = self.current
        p = QPainter(self)
        p.drawPixmap(0, 0, art.frame(k, self.scale, mirrored))


_controller = None


class DoggoController:
    """His settings, his icon in the notification area and its menu, and whether he's out."""

    def __init__(self, desktop):
        self.desktop = desktop
        self.settings = dict(DEFAULT_SETTINGS)
        try:
            data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        except FileNotFoundError:
            data = {}
        except (OSError, ValueError) as exc:
            warnings.warn(f"Could not read Doggo's settings from {SETTINGS_FILE}: {exc}")
            data = {}
        if isinstance(data, dict):
            self.settings.update({k: v for k, v in data.items()
                                  if k in DEFAULT_SETTINGS and isinstance(v, type(DEFAULT_SETTINGS[k]))})
        if self.settings["mode"] not in ("follow", "play", "stay"):
            self.settings["mode"] = "play"
        if self.settings["speed"] not in SPEEDS:
            self.settings["speed"] = "normal"
        if self.settings["size"] not in SIZES:
            self.settings["size"] = 2
        self.widget = None
        self.tray = TrayIcon(desktop, art.doggo_icon(32), desktop)
        self.tray.setToolTip("Doggo")
        self.menu = QMenu(desktop)
        self.tray.setContextMenu(self.menu)
        self.tray.activated.connect(self._tray_activated)
        self._build_menu()

    def _save(self):
        try:
            SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
            SETTINGS_FILE.write_text(json.dumps(self.settings, indent=2), encoding="utf-8")
        except OSError as exc:
            QMessageBox.warning(self.desktop, "Doggo", f"Could not save Doggo's settings:\n{exc}")

    def _choice_menu(self, title, key, options):
        sub = self.menu.addMenu(title)
        group = QActionGroup(sub)
        group.setExclusive(True)
        for value, label in options:
            action = QAction(label, sub)
            action.setCheckable(True)
            action.setChecked(self.settings[key] == value)
            action.triggered.connect(lambda _checked=False, v=value: self._set(key, v))
            group.addAction(action)
            sub.addAction(action)
        return sub

    def _build_menu(self):
        self.menu.clear()
        self.show_action = QAction("Show Doggo", self.menu)
        self.show_action.setCheckable(True)
        self.show_action.toggled.connect(lambda on: self.show() if on else self.dismiss())
        self.menu.addAction(self.show_action)
        start = QAction("Start Doggo when Windows starts", self.menu)
        start.setCheckable(True)
        start.setChecked(self.settings["start_at_logon"])
        start.toggled.connect(lambda on: self._set("start_at_logon", on))
        self.menu.addAction(start)
        self.menu.addSeparator()
        tricks = self.menu.addMenu("Do a trick")
        for key in art.ACTIONS:
            tricks.addAction(art.ACTIONS[key][0], lambda k=key: self._do(lambda w: w.trick(k)))
        self.menu.addAction("Give Doggo a treat", self._treat)
        self.menu.addAction("Time for a nap", lambda: self._do(lambda w: w._nap()))
        self.menu.addSeparator()
        self._choice_menu("Behavior", "mode", [("follow", "Follow me"), ("play", "Play by himself"),
                                               ("stay", "Stay put")])
        self._choice_menu("Speed", "speed", [("slow", "Slow"), ("normal", "Normal"), ("fast", "Fast")])
        self._choice_menu("Size", "size", [(1, "Small"), (2, "Normal"), (3, "Big")])
        bubbles = QAction("Chatty bubbles", self.menu)
        bubbles.setCheckable(True)
        bubbles.setChecked(self.settings["bubbles"])
        bubbles.toggled.connect(lambda on: self._set("bubbles", on))
        self.menu.addAction(bubbles)
        self.menu.addSeparator()
        self.menu.addAction("About Doggo...", self._about)
        self.menu.addAction("Say goodbye", self.dismiss)
        self.menu.aboutToShow.connect(self._refresh_menu)

    def _refresh_menu(self):
        self.show_action.blockSignals(True)
        self.show_action.setChecked(self.widget is not None and self.widget.isVisible())
        self.show_action.blockSignals(False)

    def _set(self, key, value):
        self.settings[key] = value
        self._save()
        w = self.widget
        if w is None:
            return
        if key == "size":
            w._apply_size()
            w.move(w._clamp(w.pos()))
        elif key == "mode":
            w.target = None
            w.last_you = time.monotonic()

    def _do(self, what):
        if self.widget is None or not self.widget.isVisible():
            self.show()
        self.widget.last_you = time.monotonic()
        what(self.widget)

    def show(self):
        if not art.available():
            from ..explorer.dialogs import msgbox
            msgbox(self.desktop, "Doggo", "Doggo can't find his sprite sheet.\n\nPut it in the Rover folder on "
                   "drive E: (Local Storage\\Rover) and try again.", icon="warning", window_icon=art.doggo_icon(16))
            return
        if self.widget is None:
            self.widget = DoggoWidget(self.desktop, self)
            self.widget.destroyed.connect(lambda *_: setattr(self, "widget", None))
        elif not self.widget.isVisible():
            self.widget._place_default()
            self.widget.show()
            self.widget._timer.start(TICK_MS)
            self.widget.play(art.ARRIVE, then=self.widget._sat)
        self.widget.raise_()
        self.desktop.doggo = self.widget
        self.tray.show()

    def dismiss(self):
        """Say goodbye: he trots off into the distance."""
        if self.widget is not None and self.widget.isVisible() and self.widget.state != "leave":
            self.widget.leave()

    def hide(self):
        if self.widget is not None:
            self.widget._timer.stop()
            self.widget.hide()
        self.tray.hide()
        if getattr(self.desktop, "doggo", None) is self.widget:
            self.desktop.doggo = None

    def _treat(self):
        def give(w):
            w.trick("pant", chatty=False)
            w.say(random.choice(["A treat! Thank you!", "*crunch crunch* Yum!", "Best. Human. Ever."]))
        self._do(give)

    def _about(self):
        from ..explorer.dialogs import msgbox
        msgbox(self.desktop, "About Doggo",
               "Doggo - a desktop dog, in the spirit of Neko.\n\n"
               "He follows you, plays by himself or stays put; he digs, fetches, reads, chews his bone, throws "
               "parties and naps when you leave him be. Click him for a pat, double-click for fetch, drag him "
               "anywhere, right-click for his menu.\n\nHis frames come from the Rover sprite sheet by thenoahguy1, "
               "in Local Storage\\Rover.", icon="info", window_icon=art.doggo_icon(16))

    def _tray_activated(self, reason):
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            if self.widget is not None and self.widget.isVisible():
                self.dismiss()
            else:
                self.show()


def _controller_for(desktop):
    global _controller
    if _controller is None or _controller.desktop is not desktop:
        if _controller is not None:
            _controller.tray.hide()
            _controller.tray.deleteLater()
        _controller = DoggoController(desktop)
    return _controller


def start_at_logon(desktop):
    controller = _controller_for(desktop)
    if controller.settings["start_at_logon"] and art.available():
        controller.show()


def launch(desktop):
    controller = _controller_for(desktop)
    controller.show()
    return controller.widget


def shutdown():
    if _controller is not None:
        if _controller.widget is not None:
            _controller.widget.close()
        _controller.widget = None
        _controller.tray.hide()


def doggo_icon(size=32):
    return art.doggo_icon(size)
