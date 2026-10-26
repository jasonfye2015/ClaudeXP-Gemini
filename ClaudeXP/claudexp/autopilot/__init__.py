"""Kithylin Autopilot on EPOCH-2001: the program with what Kithylin may do, how long he stays, his pace and his
voice, the Start button, and a Legs tab to start any one activity now. The engine is claudecore.autopilot; this
computer's legs are in legs.py (the messengers, mail, the Web, TV, games, the MUCK) and content.py (Local Storage:
comics, portfolios, pictures, stories, old chat logs, Explorer, Kiwix, music, LiveJournal). While he's at it the
screen has a sky-blue glow, his own cursor, and a banner with Pause and Stop; your own mouse or keyboard pauses him.
The Day and Threads tabs (daytabs.py) steer his day: the week's schedule, today's story, and what he brings up."""
import json
import traceback

from PySide6.QtCore import QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap, QPolygonF
from PySide6.QtCore import QPointF
from PySide6.QtWidgets import (QCheckBox, QComboBox, QFormLayout, QGridLayout, QGroupBox, QHBoxLayout, QLabel,
                               QListWidget, QPushButton, QTabWidget, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget)
from shiboken6 import isValid

from ..paths import DATA
from ..wm import XPWindow

SETTINGS_FILE = DATA / "autopilot.json"
DAY_FILE = DATA / "autopilot_day.json"
TITLE = "Kithylin Autopilot"
HOURS = [("Until I stop him", 0), ("Half an hour", 0.5), ("An hour", 1), ("Two hours", 2), ("Four hours", 4),
         ("Eight hours", 8)]
PACES = [("Relaxed", 1.4), ("Normal", 1.0), ("Quick", 0.7)]
KINDS = {"always": "Always on", "background": "In the background", "foreground": "In front"}
_pilot = None
_frame = None
_day = None


def leg_classes():
    """Every leg this computer has, in the order the panel lists them."""
    from .content import CONTENT_LEGS
    from .legs import LEGS
    return list(LEGS) + list(CONTENT_LEGS)


def day():
    """His day on this computer (claudecore.autopilot.day), shared by the engine and the panel."""
    global _day
    if _day is None:
        from claudecore.autopilot.day import Day
        _day = Day(DAY_FILE)
    return _day


def autopilot_icon():
    pm = QPixmap(32, 32)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(QPen(QColor("#2A7DB8"), 1.2))
    p.setBrush(QColor("#8FD3FF"))
    p.drawRoundedRect(QRectF(2, 2, 28, 28), 7, 7)
    p.setPen(QPen(QColor("#1A4A70"), 1.4))
    p.setBrush(QColor("white"))
    p.drawPolygon(QPolygonF([QPointF(10, 7), QPointF(10, 24), QPointF(14.5, 20), QPointF(17.5, 26.5),
                             QPointF(20.5, 25), QPointF(17.5, 18.5), QPointF(23, 18.5)]))
    p.end()
    return QIcon(pm)


def load_settings():
    """The saved settings; a leg added since they were saved is allowed by default (unticking it sticks)."""
    from claudecore.autopilot.engine import Autopilot
    s = dict(Autopilot.DEFAULTS)
    try:
        saved = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        if isinstance(saved, dict):
            s.update({k: v for k, v in saved.items() if k in s})
    except (OSError, ValueError):
        pass
    keys = [cls.key for cls in leg_classes()]
    offered = set(s.get("offered") or [])
    if not offered and SETTINGS_FILE.exists():           # saved before the panel kept track: the first eight legs
        offered = {"messengers", "mail", "browse", "tv", "rpg", "muck", "roleplay", "idle"}
    s["allowed"] = list(dict.fromkeys(list(s.get("allowed", [])) + [k for k in keys if k not in offered]))
    s["offered"] = keys
    return s


def save_settings(s):
    try:
        SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        SETTINGS_FILE.write_text(json.dumps(s, indent=2), encoding="utf-8")
    except OSError:
        pass


class XPAdapter:
    def __init__(self, desktop):
        self.desktop = desktop

    def legs(self):
        return [cls() for cls in leg_classes()]

    def keep_awake(self):
        import time
        self.desktop.last_input = time.monotonic()      # (the screen saver watches this)

    def day(self):
        return day()

    def set_away(self, away, message=""):
        """Asleep or out: his AIM away message (AIM answers IMs with it); back: away no longer."""
        from ..programs import aim
        app = aim._app
        if app is not None and app.world is not None:
            app.world.set_user_away(away, message)


def pilot():
    return _pilot


class Panel(QWidget):
    """Four tabs: what he may do and how (the settings); the Legs - every activity he knows, to start one now; his
    Day - the week's schedule, today, right now; and the Threads he brings up, with his style card."""

    def __init__(self, desktop):
        super().__init__()
        self.desktop = desktop
        self.frame = None
        self.settings = load_settings()
        save_settings(self.settings)
        root = QVBoxLayout(self)
        intro = QLabel("Let Kithylin take over this computer. He'll use its programs the way you would, two to four "
                       "at a time, for as long as you let him. Your own mouse or keyboard pauses him; the banner at "
                       "the top has Pause and Stop.")
        intro.setWordWrap(True)
        root.addWidget(intro)
        self.tabs = QTabWidget()
        self.tabs.addTab(self._settings_tab(), "What he does")
        self.tabs.addTab(self._legs_tab(), "Legs")
        from .daytabs import DayTab, ThreadsTab
        self.tabs.addTab(DayTab(day(), leg_classes(), pilot), "Day")
        self.tabs.addTab(ThreadsTab(day(), leg_classes(), pilot), "Threads")
        root.addWidget(self.tabs, 1)
        row = QHBoxLayout()
        self.go = QPushButton("Let Kithylin take over")
        self.go.setMinimumHeight(32)
        self.go.clicked.connect(self._toggle)
        self.pause_btn = QPushButton("Pause")
        self.pause_btn.clicked.connect(lambda: _pilot and _pilot.toggle_pause())
        row.addWidget(self.go, 1)
        row.addWidget(self.pause_btn)
        root.addLayout(row)
        self.status = QLabel("Kithylin isn't at the computer.")
        root.addWidget(self.status)
        self.log = QListWidget()
        self.log.setMaximumHeight(100)
        root.addWidget(self.log)
        self.timer = QTimer(self, interval=1000, timeout=self._refresh)
        self.timer.start()
        self._refresh()

    # ---- the settings tab ---------------------------------------------------------------------------------------
    def _settings_tab(self):
        page = QWidget()
        col = QVBoxLayout(page)
        box = QGroupBox("What he may do (hover for what each is)")
        grid = QGridLayout(box)
        grid.setHorizontalSpacing(14)
        self.boxes = {}
        legs = leg_classes()
        half = (len(legs) + 1) // 2
        for i, cls in enumerate(legs):
            cb = QCheckBox(cls.title)
            cb.setToolTip(cls.blurb or cls.title)
            cb.setChecked(cls.key in self.settings["allowed"])
            cb.toggled.connect(self._save)
            grid.addWidget(cb, i % half, i // half)
            self.boxes[cls.key] = cb
        col.addWidget(box)
        extras = QGroupBox("Also")
        ev = QVBoxLayout(extras)
        self.movies = QCheckBox("Whole movies on ClaudeTV (two hours or more at a stretch)")
        self.movies.setChecked(bool(self.settings.get("whole_movies", True)))
        self.movies.toggled.connect(self._save)
        ev.addWidget(self.movies)
        self.adult_web = QCheckBox("The adult sites on the Furry Web too (Hardblush, SexyFur, YiffStar)")
        self.adult_web.setChecked(bool(self.settings.get("adult_web", False)))
        self.adult_web.toggled.connect(self._save)
        ev.addWidget(self.adult_web)
        col.addWidget(extras)
        opts = QGroupBox("How")
        form = QFormLayout(opts)
        self.hours = QComboBox()
        for label, value in HOURS:
            self.hours.addItem(label, value)
        self.hours.setCurrentIndex(max(0, next((i for i, (_l, v) in enumerate(HOURS)
                                                if v == self.settings.get("hours", 0)), 0)))
        self.hours.currentIndexChanged.connect(self._save)
        form.addRow("For how long:", self.hours)
        self.pace = QComboBox()
        for label, value in PACES:
            self.pace.addItem(label, value)
        self.pace.setCurrentIndex(max(0, next((i for i, (_l, v) in enumerate(PACES)
                                               if abs(v - self.settings.get("pace", 1.0)) < 0.01), 1)))
        self.pace.currentIndexChanged.connect(self._save)
        form.addRow("His pace:", self.pace)
        self.voice = QComboBox()
        try:
            from claudecore.autopilot.voice import choices
            for key, label in choices():
                self.voice.addItem(label, key)
        except Exception:
            self.voice.addItem("The buddies' own model, asked to be Kithylin", "plain")
        i = self.voice.findData(self.settings.get("voice", "auto"))
        self.voice.setCurrentIndex(i if i >= 0 else 0)
        self.voice.currentIndexChanged.connect(self._save)
        form.addRow("His voice:", self.voice)
        self.pause_input = QCheckBox("Pause him when I touch the mouse or keyboard")
        self.pause_input.setChecked(bool(self.settings.get("pause_on_input", True)))
        self.pause_input.toggled.connect(self._save)
        form.addRow("", self.pause_input)
        col.addWidget(opts)
        col.addStretch(1)
        return page

    # ---- the legs tab -------------------------------------------------------------------------------------------
    def _legs_tab(self):
        page = QWidget()
        col = QVBoxLayout(page)
        note = QLabel("Everything he knows how to do. Pick one and he starts it now - taking over the computer first "
                      "if he isn't already. Whatever was in front makes way for it.")
        note.setWordWrap(True)
        col.addWidget(note)
        self.leg_list = QTreeWidget()
        self.leg_list.setHeaderLabels(["Leg", "Where", "How long", "What he does"])
        self.leg_list.setRootIsDecorated(False)
        self.leg_list.setAlternatingRowColors(True)
        for cls in leg_classes():
            lo, hi = cls.minutes
            length = "all session" if cls.kind == "always" else f"{lo}-{hi} min"
            item = QTreeWidgetItem([cls.title, KINDS.get(cls.kind, cls.kind), length, cls.blurb])
            item.setData(0, Qt.UserRole, cls.key)
            item.setToolTip(3, cls.blurb)
            self.leg_list.addTopLevelItem(item)
        for c, w in enumerate((150, 110, 80)):
            self.leg_list.setColumnWidth(c, w)
        self.leg_list.itemDoubleClicked.connect(lambda item, _c: self._run_leg(item.data(0, Qt.UserRole)))
        col.addWidget(self.leg_list, 1)
        row = QHBoxLayout()
        row.addStretch(1)
        self.now_btn = QPushButton("Do this now")
        self.now_btn.clicked.connect(lambda: self.leg_list.currentItem() is not None and
                                     self._run_leg(self.leg_list.currentItem().data(0, Qt.UserRole)))
        row.addWidget(self.now_btn)
        col.addLayout(row)
        return page

    def _run_leg(self, key):
        if not key:
            return
        if _pilot is None or not _pilot.running:
            if not self._start(minimize=False):
                return
        _pilot.run_now(key)
        if self.frame is not None and isValid(self.frame):
            self.desktop.minimize(self.frame)

    # ---- running --------------------------------------------------------------------------------------------------
    def _save(self, *_):
        s = self.settings
        s["allowed"] = [k for k, cb in self.boxes.items() if cb.isChecked()]
        s["whole_movies"] = self.movies.isChecked()
        s["adult_web"] = self.adult_web.isChecked()
        s["hours"] = self.hours.currentData()
        s["pace"] = self.pace.currentData()
        s["voice"] = self.voice.currentData()
        s["pause_on_input"] = self.pause_input.isChecked()
        save_settings(s)

    def _toggle(self):
        if _pilot is not None and _pilot.running:
            _pilot.stop()
            return
        self._start()

    def _start(self, minimize=True):
        global _pilot
        self._save()
        if not self.settings["allowed"]:
            self.status.setText("Tick something for him to do first.")
            return False
        from claudecore.autopilot.engine import Autopilot
        try:
            _pilot = Autopilot(self.desktop, XPAdapter(self.desktop), self.settings)
            _pilot.changed.connect(self._refresh)
            _pilot.start()
        except Exception:
            self.status.setText("Couldn't start: " + traceback.format_exc(limit=1).strip().splitlines()[-1])
            _pilot = None
            return False
        if minimize and self.frame is not None and isValid(self.frame):
            self.desktop.minimize(self.frame)              # out of his way
        return True

    def _refresh(self, *_):
        p = _pilot
        running = p is not None and p.running
        self.go.setText("Stop" if running else "Let Kithylin take over")
        self.pause_btn.setEnabled(running)
        self.pause_btn.setText("Resume" if running and p.paused else "Pause")
        for cb in list(self.boxes.values()) + [self.movies, self.adult_web, self.hours, self.pace, self.voice,
                                                 self.pause_input]:
            cb.setEnabled(not running)
        for i in range(self.leg_list.topLevelItemCount()):
            item = self.leg_list.topLevelItem(i)
            on = running and item.data(0, Qt.UserRole) in p.tasks
            f = item.font(0)
            if f.bold() != on:
                f.setBold(on)
                for c in range(4):
                    item.setFont(c, f)
        if running:
            self.status.setText(("Paused. " if p.paused else "") + p.banner.status.text())
        else:
            self.status.setText("Kithylin isn't at the computer.")
        if p is not None and self.log.count() != min(60, len(p.recent)):
            self.log.clear()
            for when, text in p.recent[-60:]:
                self.log.addItem(f"{when}  {text}")
            self.log.scrollToBottom()


def launch(desktop):
    global _frame
    if _frame is not None and isValid(_frame):
        desktop.open_window(_frame)
        return
    body = Panel(desktop)
    _frame = XPWindow(desktop, TITLE, body, autopilot_icon(), size=(780, 780))
    body.frame = _frame
    desktop.open_window(_frame)


def shutdown():
    global _pilot
    if _pilot is not None and _pilot.running:
        _pilot.stop()
    _pilot = None
