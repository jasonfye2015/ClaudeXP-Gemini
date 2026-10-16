"""ClaudeCity - a SimCity Classic-style city builder for ClaudeXP's Games folder.

Zone land for homes, shops and factories, run roads, rail and power lines, add police and fire stations, parks, a
stadium, a seaport and an airport, and keep the budget, the traffic, the pollution and the crime in check while your
village grows into a Megalopolis. Disasters (and Claudezilla) strike now and then, or whenever you pick them from the
menu. Six scenarios start you in a city in trouble with a goal and a deadline.

The title sign's buttons work. In the city: pick a tool on the left palette, click or drag on the map; right-drag or
the arrow keys scroll, the mouse wheel zooms. Budget, Evaluation and Graphs open as their own windows (Windows menu),
and the map overlays show power, traffic, pollution, crime, land value and police/fire coverage.
Cities are saved in data/claudecity/cities/.
"""
import math
from pathlib import Path
import re
import time

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import QActionGroup, QBrush, QColor, QFont, QPainter, QPen, QPixmap, \
    QPolygonF
from PySide6.QtWidgets import (QCheckBox, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QMenuBar, QPushButton, QSlider,
                               QSpinBox, QVBoxLayout, QWidget)
from shiboken6 import isValid

from claudecore import host
from . import art
from . import sim as S

CITIES = host.saves("claudecity") / "cities"           # shared by every era
TITLE = Path(__file__).resolve().parent / "assets" / "title.jpg"
TOP_H = 34
PALETTE_W = 66
SIGN_BUTTONS = {"new": (367, 407, 628, 442), "load": (640, 407, 843, 442), "scenario": (465, 457, 746, 492)}
TOOL_ORDER = ["bulldozer", "query", "road", "rail", "wire", "park", "res", "com", "ind", "police", "fire",
              "stadium", "seaport", "coal", "nuclear", "airport"]
OVERLAYS = ["City Form", "Power Grid", "Traffic", "Pollution", "Crime", "Land Value", "Police Coverage",
            "Fire Coverage"]
MENU_STYLE = """
QMenuBar { background: #ECE9D8; font-family: Tahoma; font-size: 11px; }
QMenuBar::item { padding: 3px 7px; background: transparent; }
QMenuBar::item:selected { background: #316AC5; color: white; }
QMenu { background: white; border: 1px solid #ACA899; font-family: Tahoma; font-size: 11px; }
QMenu::item { padding: 4px 24px 4px 20px; }
QMenu::item:selected { background: #316AC5; color: white; }
"""


def city_icon():
    return art.icon()


def _font(size, bold=False, family="Tahoma"):
    f = QFont(family, size)
    f.setBold(bold)
    return f


def _money(v):
    return f"${v:,}" if v >= 0 else f"-${-v:,}"


class CityGame(QWidget):
    """Everything inside the ClaudeCity window: the title sign, setup pages and the city itself."""

    def __init__(self, desktop):
        super().__init__()
        self.desktop = desktop
        self.frame = None
        self.state = "title"
        self.city = None
        self.city_file = None
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMinimumSize(820, 600)
        self.mouse = QPointF(-1, -1)
        self.buttons = []
        self.title_pm = QPixmap(str(TITLE)) if TITLE.exists() else QPixmap()
        self.cache = {}
        # setup pages
        self.level = "Easy"
        self.preview = None
        self.preview_seed = None
        self.name_edit = QLineEdit(self)
        self.name_edit.setMaxLength(20)
        self.name_edit.setText("Claudeville")
        self.name_edit.setStyleSheet("QLineEdit { background: white; border: 2px solid #1E5A2A; font-family: Georgia; "
                                     "font-size: 15px; padding: 2px 6px; }")
        self.name_edit.hide()
        self.saves = []
        # play
        self.menubar = QMenuBar(self)
        self.menubar.setStyleSheet(MENU_STYLE)
        self.menubar.hide()
        self.tool = "res"
        self.zoom = 24
        self.ox, self.oy = 0.0, 0.0                # top-left map tile shown
        self.overlay = None
        self.dragging_pan = None
        self.last_applied = None
        self.left_down = False
        self.frame_n = 0
        self.last = time.monotonic()
        self.minimap = None
        self.minimap_t = 0.0
        self.msg_index = 0
        self.windows = {}
        self.shown_scenario = False
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(50)
        self._build_menus()

    # ---- the loop -------------------------------------------------------------------------------------------
    def _tick(self):
        now = time.monotonic()
        dt = min(0.2, now - self.last)
        self.last = now
        self.frame_n += 1
        c = self.city
        if self.state == "play" and c is not None:
            month = c.tick(dt)
            if month:
                self.minimap = None
                if c.budget_due:
                    self.open_budget()
                for win in ("evaluation", "graphs"):
                    w = self.windows.get(win)
                    if w is not None and isValid(w):
                        w.content.refresh()
                if c.scenario and c.scenario.get("done") and not c.scenario.get("told"):
                    c.scenario["told"] = True
                    self._message("ClaudeCity", c.messages[-1][0])
            if len(c.messages) > self.msg_index:
                self.msg_index = len(c.messages)
                kind = c.messages[-1][1]
                if kind == "bad":
                    host.sound("exclamation")
            self._keyscroll(dt)
        self.update()

    # ---- menus ----------------------------------------------------------------------------------------------
    def _build_menus(self):
        mb = self.menubar
        f = mb.addMenu("&File")
        f.addAction("&New City...", self._to_new)
        f.addAction("&Load City...", self._to_load)
        f.addSeparator()
        f.addAction("&Save City", self.save)
        f.addAction("Save City &As...", self._save_as)
        f.addSeparator()
        f.addAction("&Quit to Title", self._quit_title)
        o = mb.addMenu("&Options")
        self.act_budget = o.addAction("Auto-&Budget")
        self.act_budget.setCheckable(True)
        self.act_budget.toggled.connect(lambda on: setattr(self.city, "auto_budget", on) if self.city else None)
        self.act_bulldoze = o.addAction("Auto-B&ulldoze")
        self.act_bulldoze.setCheckable(True)
        self.act_bulldoze.toggled.connect(lambda on: setattr(self.city, "auto_bulldoze", on) if self.city else None)
        self.act_disasters = o.addAction("&Disasters")
        self.act_disasters.setCheckable(True)
        self.act_disasters.toggled.connect(lambda on: setattr(self.city, "disasters_on", on) if self.city else None)
        sp = mb.addMenu("&Speed")
        group = QActionGroup(self)
        self.speed_actions = {}
        for name in S.SPEEDS:
            a = sp.addAction(name)
            a.setCheckable(True)
            group.addAction(a)
            a.triggered.connect(lambda _=False, name=name: setattr(self.city, "speed", name) if self.city else None)
            self.speed_actions[name] = a
        d = mb.addMenu("&Disasters")
        for label, fn in (("&Fire", "disaster_fire"), ("F&lood", "disaster_flood"), ("&Tornado", "disaster_tornado"),
                          ("&Earthquake", "disaster_quake"), ("&Monster", "disaster_monster"),
                          ("&Air Crash", "disaster_crash"), ("&Nuclear Meltdown", "disaster_meltdown")):
            d.addAction(label, lambda fn=fn: self._disaster(fn))
        w = mb.addMenu("&Windows")
        w.addAction("&Budget...", self.open_budget)
        w.addAction("&Evaluation...", self.open_evaluation)
        w.addAction("&Graphs...", self.open_graphs)
        maps = w.addMenu("&Map Overlay")
        mg = QActionGroup(self)
        for name in OVERLAYS:
            a = maps.addAction(name)
            a.setCheckable(True)
            a.setChecked(name == "City Form")
            mg.addAction(a)
            a.triggered.connect(lambda _=False, name=name: self._set_overlay(name))
        h = mb.addMenu("&Help")
        h.addAction("&How to Play", self._help)
        h.addAction("&About ClaudeCity", lambda: self._message(
            "About ClaudeCity", "ClaudeCity for ClaudeXP - build a city from dust to Megalopolis. Inspired by "
                                "SimCity Classic."))
        mb.triggered.connect(lambda _a: host.sound("menu"))

    def _sync_menus(self):
        c = self.city
        if c is None:
            return
        self.act_budget.setChecked(c.auto_budget)
        self.act_bulldoze.setChecked(c.auto_bulldoze)
        self.act_disasters.setChecked(c.disasters_on)
        self.speed_actions[c.speed].setChecked(True)

    def _set_overlay(self, name):
        self.overlay = None if name == "City Form" else name

    def _disaster(self, fn):
        if self.city:
            getattr(self.city, fn)()
            self.minimap = None
            last = self.city.messages[-1] if self.city.messages else None
            if last and last[2]:
                self.centre_on(*last[2])

    # ---- moving between pages ----------------------------------------------------------------------------------
    def _to_title(self):
        self.state = "title"
        self.menubar.hide()
        self.name_edit.hide()

    def _to_new(self):
        self.state = "new"
        self.menubar.hide()
        self.name_edit.show()
        self.name_edit.setFocus()
        if self.preview is None:
            self._new_terrain()

    def _new_terrain(self):
        import random
        self.preview_seed = random.randint(1, 10 ** 8)
        c = S.City("preview", seed=self.preview_seed, blank=True)
        c.generate_terrain()
        self.preview = self._render_mini(c, 2)

    def _to_load(self):
        self.state = "load"
        self.menubar.hide()
        self.name_edit.hide()
        self.saves = sorted(CITIES.glob("*.json"), key=lambda p: -p.stat().st_mtime) if CITIES.exists() else []

    def _to_scenarios(self):
        self.state = "scenario"
        self.menubar.hide()
        self.name_edit.hide()

    def _start_city(self, city, path=None):
        self.city = city
        self.city_file = path
        self.state = "play"
        self.name_edit.hide()
        self.menubar.show()
        self.menubar.setGeometry(0, 0, self.width(), self.menubar.sizeHint().height())
        self.minimap = None
        self.msg_index = len(city.messages)
        self._sync_menus()
        # start the view on the city (or the middle)
        if city.buildings:
            xs = [b.x for b in city.buildings.values()]
            ys = [b.y for b in city.buildings.values()]
            self.centre_on(sum(xs) / len(xs), sum(ys) / len(ys))
        else:
            self.centre_on(S.MAP_W / 2, S.MAP_H / 2)
        if city.scenario and not city.scenario.get("intro_shown"):
            city.scenario["intro_shown"] = True
            self._message(f"ClaudeCity - {city.scenario['name']}", city.scenario["text"])
        self.setFocus()

    def _begin_new(self):
        name = re.sub(r"[^\w '\-]", "", self.name_edit.text()).strip() or "Claudeville"
        c = S.City(name, seed=self.preview_seed, level=self.level, year=1900)
        c.say(f"Welcome to {name}! Start with a power plant, then zone some land and connect it with roads and "
              "power lines.", "info")
        self._start_city(c)

    def _quit_title(self):
        if self.city is not None:
            self.save()
        self._close_windows()
        self.city = None
        self._to_title()

    def _close_windows(self):
        for w in list(self.windows.values()):
            if w is not None and isValid(w):
                self.desktop.close_window(w)
        self.windows = {}

    # ---- saving --------------------------------------------------------------------------------------------
    def save(self):
        if self.city is None:
            return
        if self.city_file is None:
            safe = re.sub(r"[^\w\- ]", "", self.city.name).strip() or "city"
            self.city_file = CITIES / f"{safe}.json"
        S.save_city(self.city, self.city_file)
        self.city.say(f"{self.city.name} saved.", "info")

    def _save_as(self):
        if self.city is None:
            return
        body = QWidget()
        v = QVBoxLayout(body)
        v.addWidget(QLabel("Save the city as:"))
        edit = QLineEdit(self.city.name)
        v.addWidget(edit)
        row = QHBoxLayout()
        row.addStretch()
        ok, cancel = QPushButton("Save"), QPushButton("Cancel")
        row.addWidget(ok)
        row.addWidget(cancel)
        v.addLayout(row)
        win = host.window(self.desktop, "Save City As", body, city_icon(), size=(320, 130))

        def go():
            name = re.sub(r"[^\w '\-]", "", edit.text()).strip() or self.city.name
            self.city.name = name
            self.city_file = CITIES / f"{name}.json"
            self.save()
            self.desktop.close_window(win)
        ok.clicked.connect(go)
        cancel.clicked.connect(lambda: self.desktop.close_window(win))
        self.desktop.open_window(win)

    def shutdown(self):
        if self.city is not None:
            self.save()
        self._close_windows()
        self.timer.stop()

    # ---- coordinates ---------------------------------------------------------------------------------------
    def map_rect(self):
        top = (self.menubar.sizeHint().height() if self.state == "play" else 0) + TOP_H
        return QRectF(PALETTE_W, top, self.width() - PALETTE_W, self.height() - top)

    def tile_at(self, pos):
        r = self.map_rect()
        x = self.ox + (pos.x() - r.x()) / self.zoom
        y = self.oy + (pos.y() - r.y()) / self.zoom
        return int(math.floor(x)), int(math.floor(y))

    def centre_on(self, x, y):
        r = self.map_rect()
        self.ox = x - r.width() / self.zoom / 2
        self.oy = y - r.height() / self.zoom / 2
        self._clamp()

    def _clamp(self):
        r = self.map_rect()
        vw, vh = r.width() / self.zoom, r.height() / self.zoom
        self.ox = max(-2, min(S.MAP_W - vw + 2, self.ox))
        self.oy = max(-2, min(S.MAP_H - vh + 2, self.oy))

    def resizeEvent(self, e):
        if self.state == "play":
            self.menubar.setGeometry(0, 0, self.width(), self.menubar.sizeHint().height())
        super().resizeEvent(e)

    # ---- input -------------------------------------------------------------------------------------------------
    def keyPressEvent(self, e):
        k = e.key()
        if self.state == "new" and k in (Qt.Key_Return, Qt.Key_Enter):
            self._begin_new()
            return
        if self.state != "play":
            return
        if k in (Qt.Key_Plus, Qt.Key_Equal):
            self._zoom(1)
        elif k == Qt.Key_Minus:
            self._zoom(-1)
        elif k == Qt.Key_Escape:
            self.tool = "query"
        else:
            self.keys = getattr(self, "keys", set())
            self.keys.add(k)

    def keyReleaseEvent(self, e):
        getattr(self, "keys", set()).discard(e.key())

    def _keyscroll(self, dt):
        keys = getattr(self, "keys", set())
        sp = 30 * dt
        dx = (Qt.Key_Right in keys or Qt.Key_D in keys) - (Qt.Key_Left in keys or Qt.Key_A in keys)
        dy = (Qt.Key_Down in keys or Qt.Key_S in keys) - (Qt.Key_Up in keys or Qt.Key_W in keys)
        if dx or dy:
            self.ox += dx * sp
            self.oy += dy * sp
            self._clamp()

    def _zoom(self, d, at=None):
        sizes = [16, 24, 32]
        i = sizes.index(self.zoom)
        ni = max(0, min(2, i + d))
        if ni == i:
            return
        r = self.map_rect()
        at = at or QPointF(r.center())
        tx = self.ox + (at.x() - r.x()) / self.zoom
        ty = self.oy + (at.y() - r.y()) / self.zoom
        self.zoom = sizes[ni]
        self.ox = tx - (at.x() - r.x()) / self.zoom
        self.oy = ty - (at.y() - r.y()) / self.zoom
        self._clamp()

    def wheelEvent(self, e):
        if self.state == "play":
            self._zoom(1 if e.angleDelta().y() > 0 else -1, e.position())

    def mouseMoveEvent(self, e):
        self.mouse = e.position()
        if self.state != "play":
            return
        if self.dragging_pan is not None:
            p0, ox, oy = self.dragging_pan
            self.ox = ox - (e.position().x() - p0.x()) / self.zoom
            self.oy = oy - (e.position().y() - p0.y()) / self.zoom
            self._clamp()
        elif self.left_down and self.tool in ("road", "rail", "wire", "bulldozer", "park") and \
                self.map_rect().contains(e.position()):
            self._apply_line(self.tile_at(e.position()))

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.RightButton:
            self.dragging_pan = None
        if e.button() == Qt.LeftButton:
            self.left_down = False
            self.last_applied = None

    def mousePressEvent(self, e):
        pos = e.position()
        self.mouse = pos
        self.setFocus()
        for rect, action in reversed(self.buttons):
            if rect.contains(pos):
                if e.button() == Qt.LeftButton:
                    host.sound("menu")
                    action()
                return
        if self.state != "play":
            return
        if e.button() == Qt.RightButton:
            self.dragging_pan = (pos, self.ox, self.oy)
            return
        if e.button() != Qt.LeftButton:
            return
        if self._minimap_click(pos):
            return
        if not self.map_rect().contains(pos):
            return
        x, y = self.tile_at(pos)
        if self.tool == "query":
            self._query(x, y)
            return
        self.left_down = True
        self._use_tool(x, y)
        self.last_applied = (x, y)

    def _use_tool(self, x, y):
        c = self.city
        cost, size, kind = S.TOOLS[self.tool]
        if kind:
            off = size // 2 if size > 1 else 0
            x, y = x - off, y - off
        err = c.apply(self.tool, x, y)
        if err:
            if err == "Insufficient funds.":
                host.sound("default")
            c.say(err, "advice")
        else:
            self.minimap = None

    def _apply_line(self, tile):
        """Dragging a road / rail / wire: fill in every tile between the last one and this (no gaps)."""
        if self.last_applied is None:
            self._use_tool(*tile)
            self.last_applied = tile
            return
        x0, y0 = self.last_applied
        x1, y1 = tile
        if (x0, y0) == (x1, y1):
            return
        # walk in L-shaped steps so networks connect with straight pieces
        x, y = x0, y0
        while (x, y) != (x1, y1):
            if x != x1 and (abs(x1 - x) >= abs(y1 - y)):
                x += 1 if x1 > x else -1
            else:
                y += 1 if y1 > y else -1
            self._use_tool(x, y)
        self.last_applied = tile

    def _minimap_click(self, pos):
        r = getattr(self, "mini_rect", None)
        if r is None or not r.contains(pos):
            return False
        mx = (pos.x() - r.x()) / r.width() * S.MAP_W
        my = (pos.y() - r.y()) / r.height() * S.MAP_H
        self.centre_on(mx, my)
        return True

    # ---- painting --------------------------------------------------------------------------------------------
    def paintEvent(self, _e):
        p = QPainter(self)
        self.buttons = []
        if self.state == "play" and self.city:
            self._draw_play(p)
        elif self.state == "new":
            self._draw_new(p)
        elif self.state == "load":
            self._draw_load(p)
        elif self.state == "scenario":
            self._draw_scenarios(p)
        else:
            self._draw_title(p)
        p.end()

    # title -------------------------------------------------------------------------------------------------------
    def _draw_title(self, p):
        p.fillRect(self.rect(), QColor("#000000"))
        if self.title_pm.isNull():
            p.setFont(_font(40, True, "Georgia"))
            p.setPen(QColor("white"))
            p.drawText(self.rect(), Qt.AlignCenter, "ClaudeCity")
            actions = [("Start New City", self._to_new), ("Load a City", self._to_load),
                       ("Select Scenario", self._to_scenarios)]
            for i, (t, a) in enumerate(actions):
                self._button(p, QRectF(self.width() / 2 - 100, self.height() / 2 + 60 + i * 44, 200, 36), t, a)
            return
        key = ("title", self.width(), self.height())
        if key not in self.cache:
            self.cache[key] = self.title_pm.scaled(self.width(), self.height(), Qt.KeepAspectRatio,
                                                   Qt.SmoothTransformation)
        pm = self.cache[key]
        x0, y0 = (self.width() - pm.width()) / 2, (self.height() - pm.height()) / 2
        p.drawPixmap(int(x0), int(y0), pm)
        sx = pm.width() / self.title_pm.width()
        sy = pm.height() / self.title_pm.height()
        for name, (a, b, c, d) in SIGN_BUTTONS.items():
            r = QRectF(x0 + a * sx, y0 + b * sy, (c - a) * sx, (d - b) * sy)
            if r.contains(self.mouse):
                p.setPen(Qt.NoPen)
                p.setBrush(QColor(255, 255, 255, 60))
                p.drawRect(r)
            self.buttons.append((r, {"new": self._to_new, "load": self._to_load, "scenario": self._to_scenarios}[name]))

    def _sign(self, p, r, title):
        """A green road sign, like the title's."""
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(QPen(QColor("#E8E8E8"), 4))
        p.setBrush(QColor("#1E7A34"))
        p.drawRoundedRect(r, 10, 10)
        p.setPen(QPen(QColor("#E8E8E8"), 1.5))
        p.setBrush(Qt.NoBrush)
        p.drawRoundedRect(r.adjusted(8, 8, -8, -8), 6, 6)
        p.setFont(_font(24, True, "Georgia"))
        p.setPen(QColor("#103A18"))
        p.drawText(QRectF(r.x() + 2, r.y() + 16, r.width(), 40), Qt.AlignHCenter, title)
        p.setPen(QColor("#FFFFFF"))
        p.drawText(QRectF(r.x(), r.y() + 14, r.width(), 40), Qt.AlignHCenter, title)

    def _sky(self, p):
        from PySide6.QtGui import QLinearGradient
        g = QLinearGradient(0, 0, 0, self.height())
        g.setColorAt(0, QColor("#30C8F0"))
        g.setColorAt(0.55, QColor("#A8E8F8"))
        g.setColorAt(0.56, QColor("#6A9A3A"))
        g.setColorAt(1, QColor("#4A7A2A"))
        p.fillRect(self.rect(), QBrush(g))

    def _button(self, p, r, text, action, small=False):
        hot = r.contains(self.mouse)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(QPen(QColor("#E8E8E8"), 2))
        p.setBrush(QColor("#2E9A44") if hot else QColor("#1E7A34"))
        p.drawRect(r)
        p.setFont(_font(9 if small else 11, True))
        p.setPen(QColor("white"))
        p.drawText(r, Qt.AlignCenter, text)
        self.buttons.append((r, action))

    def _draw_new(self, p):
        self._sky(p)
        w, h = self.width(), self.height()
        r = QRectF(w / 2 - 300, 30, 600, h - 70)
        self._sign(p, r, "Start New City")
        p.setFont(_font(11, True))
        p.setPen(QColor("white"))
        p.drawText(QRectF(r.x() + 40, r.y() + 72, 200, 20), Qt.AlignLeft, "City name:")
        self.name_edit.setGeometry(int(r.x() + 150), int(r.y() + 68), 250, 30)
        p.drawText(QRectF(r.x() + 40, r.y() + 118, 200, 20), Qt.AlignLeft, "Game level:")
        for i, lvl in enumerate(S.LEVELS):
            br = QRectF(r.x() + 150 + i * 110, r.y() + 112, 100, 30)
            on = lvl == self.level
            p.setPen(QPen(QColor("#FFFFFF"), 2 if on else 1))
            p.setBrush(QColor("#3AB054") if on else QColor("#165A28"))
            p.drawRect(br)
            p.setPen(QColor("white"))
            p.setFont(_font(10, on))
            p.drawText(br, Qt.AlignCenter, f"{lvl} (${S.LEVELS[lvl] // 1000}k)")
            self.buttons.append((br, lambda lvl=lvl: setattr(self, "level", lvl)))
        if self.preview is not None:
            pr = QRectF(r.center().x() - self.preview.width() / 2, r.y() + 160, self.preview.width(),
                        self.preview.height())
            p.setPen(QPen(QColor("white"), 2))
            p.drawRect(pr.adjusted(-2, -2, 2, 2))
            p.drawPixmap(pr.topLeft(), self.preview)
            self._button(p, QRectF(r.center().x() - 110, pr.bottom() + 12, 220, 30), "Generate New Terrain",
                         self._new_terrain, small=True)
        self._button(p, QRectF(r.x() + 60, r.bottom() - 60, 200, 36), "Back", self._to_title)
        self._button(p, QRectF(r.right() - 260, r.bottom() - 60, 200, 36), "Start", self._begin_new)

    def _draw_load(self, p):
        self._sky(p)
        w, h = self.width(), self.height()
        r = QRectF(w / 2 - 280, 30, 560, h - 70)
        self._sign(p, r, "Load a City")
        y = r.y() + 76
        if not self.saves:
            p.setFont(_font(11))
            p.setPen(QColor("white"))
            p.drawText(QRectF(r.x(), y + 20, r.width(), 40), Qt.AlignHCenter, "No saved cities yet.")
        for path in self.saves[:9]:
            br = QRectF(r.x() + 50, y, r.width() - 100, 36)
            try:
                import json
                d = json.loads(path.read_text(encoding="utf-8"))
                info = f"{d['name']}  -  {S.MONTHS[d['month']]} {d['year']}  -  {_money(d['funds'])}"
            except Exception:
                info = path.stem
            self._button(p, br, info, lambda path=path: self._load(path))
            y += 44
        self._button(p, QRectF(r.center().x() - 100, r.bottom() - 60, 200, 36), "Back", self._to_title)

    def _load(self, path):
        try:
            c = S.load_city(path)
        except Exception as exc:
            self._message("ClaudeCity", f"That city couldn't be loaded: {exc}")
            return
        self._start_city(c, path)

    def _draw_scenarios(self, p):
        self._sky(p)
        w, h = self.width(), self.height()
        r = QRectF(w / 2 - 330, 20, 660, h - 50)
        self._sign(p, r, "Select Scenario")
        y = r.y() + 72
        for sc in S.SCENARIOS:
            br = QRectF(r.x() + 40, y, r.width() - 80, 30)
            self._button(p, br, sc["name"], lambda sc=sc: self._start_scenario(sc))
            hovered = br.contains(self.mouse)
            if hovered:
                self.hover_scenario = sc
            y += 38
        sc = getattr(self, "hover_scenario", None)
        if sc:
            p.setFont(_font(9))
            p.setPen(QColor("white"))
            p.drawText(QRectF(r.x() + 40, y + 6, r.width() - 80, 90), Qt.TextWordWrap, sc["text"])
        self._button(p, QRectF(r.center().x() - 100, r.bottom() - 56, 200, 34), "Back", self._to_title)

    def _start_scenario(self, sc):
        city = S.build_scenario(sc)
        self._start_city(city)

    # the city ---------------------------------------------------------------------------------------------------
    def _tile_pm(self, key, make):
        pm = self.cache.get(key)
        if pm is None:
            pm = make()
            self.cache[key] = pm
            if len(self.cache) > 3000:
                for k in list(self.cache)[:500]:
                    del self.cache[k]
        return pm

    def _mask(self, x, y, part):
        c = self.city
        m = 0
        for bit, (dx, dy) in ((1, (0, -1)), (2, (1, 0)), (4, (0, 1)), (8, (-1, 0))):
            nx, ny = x + dx, y + dy
            if c.has(nx, ny, part):
                m |= bit
            elif part == "wire" and c.inside(nx, ny) and c.owner[ny][nx] is not None:
                m |= bit
            elif part == "road" and c.inside(nx, ny) and c.owner[ny][nx] is not None and False:
                m |= bit
        return m

    def _draw_play(self, p):
        c = self.city
        mr = self.map_rect()
        t = self.zoom
        shake = 0
        if any(s["kind"] == "shake" for s in c.sprites):
            shake = math.sin(self.frame_n * 1.7) * 4
        p.fillRect(self.rect(), QColor("#000000"))
        p.save()
        p.setClipRect(mr)
        x0, y0 = int(math.floor(self.ox)), int(math.floor(self.oy))
        x1 = int(math.ceil(self.ox + mr.width() / t)) + 1
        y1 = int(math.ceil(self.oy + mr.height() / t)) + 1

        def sx(x):
            return mr.x() + (x - self.ox) * t + shake

        def sy(y):
            return mr.y() + (y - self.oy) * t
        drawn = set()
        fire_frame = (self.frame_n // 3) % 4
        for y in range(max(0, y0 - 6), min(S.MAP_H, y1)):
            for x in range(max(0, x0 - 6), min(S.MAP_W, x1)):
                bid = c.owner[y][x]
                if bid is not None:
                    if bid in drawn:
                        continue
                    b = c.buildings.get(bid)
                    if b is None:
                        continue
                    drawn.add(bid)
                    blink = not b.powered and (self.frame_n // 10) % 2 == 0
                    if b.kind in ("res", "com", "ind"):
                        pm = self._tile_pm(("z", b.kind, b.level, b.variant, t, blink),
                                           lambda b=b, blink=blink: art.zone(b.kind, b.level, b.variant, t, not blink))
                    else:
                        pm = self._tile_pm(("s", b.kind, t, blink), lambda b=b, blink=blink: art.special(b.kind, t,
                                                                                                       not blink))
                    p.drawPixmap(QPointF(sx(b.x), sy(b.y)), pm)
                    continue
                if x < x0 or y < y0:
                    continue
                if (x, y) in c.burning:
                    p.drawPixmap(QPointF(sx(x), sy(y)), self._tile_pm(("fire", t, fire_frame),
                                                                     lambda: art.fire(t, fire_frame)))
                    continue
                tl = c.tile[y][x]
                ter = c.terrain[y][x]
                if tl is None:
                    v = (x * 7 + y * 13) % 4
                    pm = self._tile_pm(("l", ter, v, t), lambda ter=ter, v=v: art.land(t, v, ter))
                elif tl in S.NETWORK:
                    base = tl.split("_")[0]
                    mask = self._mask(x, y, base)
                    water = ter == S.WATER
                    pm = self._tile_pm(("n", tl, mask, water, t), lambda tl=tl, mask=mask, water=water:
                                       art.network(tl, mask, t, water))
                else:
                    pm = self._tile_pm(("m", tl, (x + y) % 3, t), lambda tl=tl: art.misc(tl, t, (x + y) % 3))
                p.drawPixmap(QPointF(sx(x), sy(y)), pm)
        self._draw_life(p, x0, y0, x1, y1, sx, sy)
        if self.overlay:
            self._draw_overlay(p, x0, y0, x1, y1, sx, sy)
        for s in c.sprites:
            if s["kind"] == "monster":
                art.monster(p, sx(s["x"]), sy(s["y"]), t, self.frame_n)
            elif s["kind"] == "tornado":
                art.tornado(p, sx(s["x"]), sy(s["y"]), t, self.frame_n)
        self._draw_cursor(p, sx, sy)
        p.restore()
        self._draw_topbar(p)
        self._draw_palette(p)
        self._draw_minimap(p)

    def _draw_life(self, p, x0, y0, x1, y1, sx, sy):
        """Cars on busy roads and smoke from factories."""
        c = self.city
        t = self.zoom
        p.setRenderHint(QPainter.Antialiasing)
        now = time.monotonic()
        p.setPen(Qt.NoPen)
        for y in range(max(0, y0), min(S.MAP_H, y1)):
            row = c.traffic[y]
            for x in range(max(0, x0), min(S.MAP_W, x1)):
                tr = row[x]
                if tr < 25 or not c.has(x, y, "road"):
                    continue
                cars = min(4, int(tr // 40) + 1)
                mask = self._mask(x, y, "road")
                horiz = bool(mask & (2 | 8)) or not (mask & (1 | 4))
                for i in range(cars):
                    f = ((now * (0.6 + 0.1 * i) + i / cars + (x * 0.37 + y * 0.53)) % 1.0)
                    if horiz:
                        cx, cy = sx(x) + f * t, sy(y) + t * (0.35 if i % 2 else 0.65)
                    else:
                        cx, cy = sx(x) + t * (0.35 if i % 2 else 0.65), sy(y) + f * t
                    p.setBrush(QColor(["#E03030", "#F0F0F0", "#3060E0", "#F0C020"][(i + x + y) % 4]))
                    p.drawRect(QRectF(cx - t * 0.09, cy - t * 0.09, t * 0.18, t * 0.18))
        for b in c.buildings.values():
            if not (x0 - 4 <= b.x <= x1 and y0 - 4 <= b.y <= y1):
                continue
            if (b.kind == "ind" and b.level >= 3) or b.kind == "coal":
                n = 2 if b.kind == "coal" else b.level - 2
                for i in range(n):
                    bx = sx(b.x) + (t * (0.95 + i * 1.6) if b.kind == "coal" else t * (0.67 + i * 0.9))
                    by = sy(b.y) + t * 0.1
                    for k in range(3):
                        ph = (now * 0.5 + k / 3 + i * 0.2) % 1.0
                        p.setBrush(QColor(110, 110, 110, int(150 * (1 - ph))))
                        p.drawEllipse(QPointF(bx + ph * t * 0.6, by - ph * t * 1.2), t * (0.15 + ph * 0.25),
                                      t * (0.15 + ph * 0.25))

    def _draw_overlay(self, p, x0, y0, x1, y1, sx, sy):
        c = self.city
        t = self.zoom
        name = self.overlay
        p.setPen(Qt.NoPen)
        if name == "Power Grid":
            for y in range(max(0, y0), min(S.MAP_H, y1)):
                for x in range(max(0, x0), min(S.MAP_W, x1)):
                    if c.conducts(x, y):
                        p.setBrush(QColor(255, 230, 0, 110) if (x, y) in c.powered else QColor(220, 30, 30, 120))
                        p.drawRect(QRectF(sx(x), sy(y), t, t))
            return
        if name == "Traffic":
            for y in range(max(0, y0), min(S.MAP_H, y1)):
                for x in range(max(0, x0), min(S.MAP_W, x1)):
                    v = c.traffic[y][x]
                    if v > 5:
                        p.setBrush(QColor(255, int(max(0, 220 - v)), 0, min(200, 60 + v)))
                        p.drawRect(QRectF(sx(x), sy(y), t, t))
            return
        grid, colour, scale = {"Pollution": (c.pollution, (140, 100, 40), 1.0), "Crime": (c.crime, (220, 30, 30), 1.2),
                               "Land Value": (c.landvalue, (40, 200, 60), 1.0),
                               "Police Coverage": (c.police_cov, (40, 90, 230), 1.4),
                               "Fire Coverage": (c.fire_cov, (230, 90, 30), 1.4)}[name]
        hw, hh = c.half
        for gy in range(max(0, y0 // 2), min(hh, y1 // 2 + 1)):
            for gx in range(max(0, x0 // 2), min(hw, x1 // 2 + 1)):
                v = grid[gy][gx] * scale
                if v > 6:
                    p.setBrush(QColor(colour[0], colour[1], colour[2], int(min(190, v))))
                    p.drawRect(QRectF(sx(gx * 2), sy(gy * 2), t * 2, t * 2))

    def _draw_cursor(self, p, sx, sy):
        if not self.map_rect().contains(self.mouse):
            return
        c = self.city
        x, y = self.tile_at(self.mouse)
        cost, size, kind = S.TOOLS[self.tool]
        if kind:
            off = size // 2
            x, y = x - off, y - off
            ok = c.can_place(self.tool, x, y) and c.funds >= cost
        else:
            ok = c.inside(x, y)
        t = self.zoom
        r = QRectF(sx(x), sy(y), size * t, size * t)
        p.setPen(QPen(QColor("#FFFFFF") if ok else QColor("#FF3030"), 2))
        p.setBrush(QColor(255, 255, 255, 40) if ok else QColor(255, 0, 0, 50))
        p.drawRect(r)
        if cost and self.tool != "query":
            p.setFont(_font(8, True))
            p.setPen(QColor("white"))
            p.drawText(QRectF(r.x(), r.bottom() + 2, 120, 14), Qt.AlignLeft, f"${cost:,}")

    def _draw_topbar(self, p):
        c = self.city
        top = self.menubar.sizeHint().height()
        r = QRectF(0, top, self.width(), TOP_H)
        p.fillRect(r, QColor("#ECE9D8"))
        p.setPen(QPen(QColor("#ACA899"), 1))
        p.drawLine(QPointF(0, r.bottom() - 0.5), QPointF(self.width(), r.bottom() - 0.5))

        def box(x, w, text, bold=False, colour="#000000"):
            br = QRectF(x, r.y() + 5, w, 22)
            p.setPen(QPen(QColor("#7F9DB9"), 1))
            p.setBrush(QColor("#FFFFFF"))
            p.drawRect(br)
            p.setFont(_font(8, bold))
            p.setPen(QColor(colour))
            p.drawText(br.adjusted(5, 0, -5, 0), Qt.AlignVCenter | Qt.AlignLeft, text)
            return br
        box(6, 150, f"Funds: {_money(c.funds)}", True, "#000000" if c.funds >= 0 else "#C00000")
        box(162, 82, c.date_text(), True)
        msg = c.messages[-1] if c.messages else ("", "info", None)
        colour = {"bad": "#C00000", "good": "#006000", "win": "#006000", "lose": "#C00000"}.get(msg[1], "#000000")
        mb = box(250, self.width() - 250 - 190, msg[0], msg[1] in ("bad", "win", "lose"), colour)
        if msg[2]:
            self.buttons.append((mb, lambda where=msg[2]: self.centre_on(*where)))
        box(self.width() - 184, 90, f"Pop: {c.population:,}", True)
        # the R/C/I demand gauge
        g = QRectF(self.width() - 88, r.y() + 3, 82, 28)
        p.setPen(QPen(QColor("#7F9DB9"), 1))
        p.setBrush(QColor("#FFFFFF"))
        p.drawRect(g)
        mid = g.center().y()
        p.setPen(QPen(QColor("#808080"), 1))
        p.drawLine(QPointF(g.x() + 2, mid), QPointF(g.right() - 2, mid))
        for i, k in enumerate(("res", "com", "ind")):
            v = c.demand[k]
            bx = g.x() + 8 + i * 25
            h = v * 12
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(art.ZONE_C[k]))
            p.drawRect(QRectF(bx, mid - max(0, h), 12, abs(h)))
            p.setFont(_font(6, True))
            p.setPen(QColor("#202020"))
            p.drawText(QRectF(bx, g.bottom() - 9 if v >= 0 else g.y(), 12, 9), Qt.AlignCenter, k[0].upper())

    def _draw_palette(self, p):
        top = self.menubar.sizeHint().height() + TOP_H
        r = QRectF(0, top, PALETTE_W, self.height() - top)
        p.fillRect(r, QColor("#ECE9D8"))
        p.setPen(QPen(QColor("#ACA899"), 1))
        p.drawLine(QPointF(PALETTE_W - 0.5, top), QPointF(PALETTE_W - 0.5, self.height()))
        p.setFont(_font(8, True))
        p.setPen(QColor("#000000"))
        p.drawText(QRectF(0, top + 2, PALETTE_W, 14), Qt.AlignCenter, "Edit")
        for i, tool in enumerate(TOOL_ORDER):
            col, row = i % 2, i // 2
            br = QRectF(4 + col * 30, top + 18 + row * 32, 28, 30)
            on = tool == self.tool
            p.setPen(QPen(QColor("#316AC5") if on else QColor("#ACA899"), 2 if on else 1))
            p.setBrush(QColor("#C8D8F8") if on else QColor("#F8F8F4"))
            p.drawRect(br)
            key = ("icon", tool)
            if key not in self.cache:
                self.cache[key] = art.tool_icon(tool, 24)
            p.drawPixmap(QPointF(br.x() + 2, br.y() + 3), self.cache[key])
            self.buttons.append((br, lambda tool=tool: setattr(self, "tool", tool)))
        y = top + 18 + 8 * 32 + 6
        cost = S.TOOLS[self.tool][0]
        p.setFont(_font(7))
        p.setPen(QColor("#000000"))
        p.drawText(QRectF(2, y, PALETTE_W - 4, 44), Qt.TextWordWrap | Qt.AlignHCenter,
                   S.TOOL_NAMES[self.tool] + (f"\n${cost:,}" if cost else ""))

    def _render_mini(self, c, k=1):
        img = QPixmap(S.MAP_W * k, S.MAP_H * k)
        img.fill(QColor(art.LAND_C))
        p = QPainter(img)
        cols = {S.WATER: QColor(art.WATER_C), S.TREES: QColor("#1E6A1E")}
        for y in range(S.MAP_H):
            for x in range(S.MAP_W):
                colour = None
                bid = c.owner[y][x]
                if bid is not None:
                    b = c.buildings.get(bid)
                    if b is not None:
                        colour = QColor(art.ZONE_C.get(b.kind, "#A0A0A8"))
                        if b.kind in ("res", "com", "ind") and b.level:
                            colour = colour.darker(100 + b.level * 15)
                elif c.tile[y][x] in S.NETWORK:
                    colour = QColor("#404044") if "road" in c.tile[y][x] else QColor("#7A5A3A") if "rail" in \
                        c.tile[y][x] else QColor("#E0D040")
                elif c.tile[y][x] == "park":
                    colour = QColor("#3E9A3A")
                elif (x, y) in c.burning:
                    colour = QColor("#FF6020")
                else:
                    colour = cols.get(c.terrain[y][x])
                if colour is not None:
                    p.fillRect(x * k, y * k, k, k, colour)
        p.end()
        return img

    def _draw_minimap(self, p):
        c = self.city
        if self.minimap is None:
            self.minimap = self._render_mini(c, 1)
        w, h = 180, 150
        r = QRectF(self.width() - w - 10, self.height() - h - 10, w, h)
        self.mini_rect = r
        p.setPen(QPen(QColor("#ECE9D8"), 3))
        p.drawRect(r.adjusted(-2, -2, 2, 2))
        p.drawPixmap(r, self.minimap, QRectF(self.minimap.rect()))
        mr = self.map_rect()
        kx, ky = w / S.MAP_W, h / S.MAP_H
        p.setPen(QPen(QColor("#FFFFFF"), 1.5))
        p.setBrush(Qt.NoBrush)
        p.drawRect(QRectF(r.x() + self.ox * kx, r.y() + self.oy * ky, mr.width() / self.zoom * kx,
                          mr.height() / self.zoom * ky))

    # ---- windows ------------------------------------------------------------------------------------------------
    def _window(self, key, title, body, size):
        old = self.windows.get(key)
        if old is not None and isValid(old):
            self.desktop.open_window(old)
            return old
        win = host.window(self.desktop, title, body, city_icon(), size=size)
        body.frame = win
        self.windows[key] = win
        self.desktop.open_window(win)
        return win

    def _message(self, title, text):
        body = QWidget()
        body.setStyleSheet("QLabel { font-family: Georgia; font-size: 12px; }")
        v = QVBoxLayout(body)
        head = QLabel(f"<b style='color:#A00000; font-size:15px; font-family:Georgia'>{title}</b>")
        head.setAlignment(Qt.AlignCenter)
        v.addWidget(head)
        lab = QLabel(text)
        lab.setWordWrap(True)
        v.addWidget(lab, 1)
        ok = QPushButton("OK")
        ok.setFixedWidth(80)
        row = QHBoxLayout()
        row.addStretch()
        row.addWidget(ok)
        row.addStretch()
        v.addLayout(row)
        win = host.window(self.desktop, "ClaudeCity", body, city_icon(), size=(420, 260))
        ok.clicked.connect(lambda: self.desktop.close_window(win))
        self.desktop.open_window(win)

    def open_budget(self):
        if self.city is None:
            return
        self._window("budget", f"Budget - {self.city.name}", BudgetPanel(self), (380, 330))

    def open_evaluation(self):
        if self.city is None:
            return
        self._window("evaluation", f"{self.city.year} City Evaluation for {self.city.name}", EvalPanel(self),
                     (520, 300))

    def open_graphs(self):
        if self.city is None:
            return
        self._window("graphs", f"Graphs - {self.city.name}", GraphPanel(self), (480, 320))

    def _query(self, x, y):
        c = self.city
        if not c.inside(x, y):
            return
        b = c.building_at(x, y)
        lines = []
        if b is not None:
            names = {"res": "Residential", "com": "Commercial", "ind": "Industrial"}
            if b.kind in names:
                dens = ["Empty lot", "Low", "Low-medium", "Medium", "High", "Very high"][b.level]
                lines.append(f"Zone: {names[b.kind]} ({dens})")
                if b.kind == "res":
                    lines.append(f"Residents: {S.R_PEOPLE[b.level]:,}")
                else:
                    lines.append(f"Jobs: {(S.C_JOBS if b.kind == 'com' else S.I_JOBS)[min(b.level, 4 if b.kind == 'ind' else 5)]:,}")
            else:
                lines.append(f"Building: {S.TOOL_NAMES.get(b.kind, b.kind)}")
            lines.append("Power: " + ("yes" if b.powered else "NO"))
        else:
            tl = c.tile[y][x]
            ter = {S.LAND: "Clear land", S.WATER: "Water", S.TREES: "Trees"}[c.terrain[y][x]]
            lines.append(f"Tile: {tl.replace('_', ' and ').replace('wire', 'power line') if tl else ter}")
            if c.has(x, y, "road"):
                tr = c.traffic[y][x]
                lines.append("Traffic: " + ("None" if tr < 10 else "Light" if tr < 60 else "Medium" if tr < 140
                                            else "Heavy"))
        def level(v):
            return "Low" if v < 40 else "Medium" if v < 100 else "High" if v < 170 else "Very high"
        lines.append(f"Land value: {level(c.at_half(c.landvalue, x, y))}")
        lines.append(f"Pollution: {level(c.at_half(c.pollution, x, y))}")
        lines.append(f"Crime: {level(c.at_half(c.crime, x, y))}")
        self._message("Query", "\n".join(lines))

    def _help(self):
        self._message("How to Play", (
            "Build a power plant first, then zone Residential (green), Commercial (blue) and Industrial (yellow) "
            "land and connect everything with roads and power lines. Zones touching each other pass power along, "
            "but roads don't - cross them with power lines. A zone needs a road within three tiles to grow.\n\n"
            "Watch the R/C/I gauge in the top right: bars above the line mean people want more of that zone. "
            "Parks, water and trees raise land value; pollution and crime lower it. Police and fire stations "
            "cover the area around them. Big cities need a stadium, a seaport and an airport.\n\n"
            "Drag to build roads, rail and power lines. Right-drag or the arrow keys scroll; the wheel zooms. "
            "Click the message bar to jump to what it's about. The budget comes due every January."))


class BudgetPanel(QWidget):
    def __init__(self, game):
        super().__init__()
        self.game = game
        self.frame = None
        c = game.city
        self.setStyleSheet("QWidget { font-family: Tahoma; font-size: 11px; }")
        nums = c.budget_numbers()
        grid = QGridLayout(self)
        grid.addWidget(QLabel("<b>Taxes collected</b>"), 0, 0)
        grid.addWidget(QLabel(_money(nums["taxes"])), 0, 2)
        grid.addWidget(QLabel("Tax rate"), 1, 0)
        self.tax = QSpinBox()
        self.tax.setRange(0, 20)
        self.tax.setSuffix(" %")
        self.tax.setValue(c.tax)
        grid.addWidget(self.tax, 1, 1)
        grid.addWidget(QLabel("<b>Funding</b>"), 2, 0)
        grid.addWidget(QLabel("<b>Requested</b>"), 2, 2)
        self.sliders = {}
        for i, (k, label) in enumerate((("road", "Transportation"), ("police", "Police"), ("fire", "Fire"))):
            grid.addWidget(QLabel(label), 3 + i, 0)
            s = QSlider(Qt.Horizontal)
            s.setRange(0, 100)
            s.setValue(c.funding[k])
            grid.addWidget(s, 3 + i, 1)
            grid.addWidget(QLabel(_money(nums[k])), 3 + i, 2)
            self.sliders[k] = s
        self.flow = QLabel()
        grid.addWidget(QLabel("<b>Cash flow</b>"), 7, 0)
        grid.addWidget(self.flow, 7, 2)
        grid.addWidget(QLabel("Current funds"), 8, 0)
        grid.addWidget(QLabel(_money(c.funds)), 8, 2)
        self.auto = QCheckBox("Auto-budget")
        self.auto.setChecked(c.auto_budget)
        grid.addWidget(self.auto, 9, 0, 1, 2)
        ok = QPushButton("Go With These Figures")
        ok.clicked.connect(self._done)
        grid.addWidget(ok, 10, 0, 1, 3)
        self.nums = nums
        for w in [self.tax] + list(self.sliders.values()):
            (w.valueChanged).connect(self._update)
        self._update()

    def _update(self):
        c = self.game.city
        taxes = int(self.nums["taxes"] * self.tax.value() / max(1, c.tax)) if c.tax else 0
        spend = sum(int(self.nums[k] * self.sliders[k].value() / 100) for k in self.sliders)
        self.flow.setText(_money(taxes - spend))

    def _done(self):
        c = self.game.city
        c.tax = self.tax.value()
        for k, s in self.sliders.items():
            c.funding[k] = s.value()
        c.auto_budget = self.auto.isChecked()
        self.game.act_budget.setChecked(c.auto_budget)
        c.budget_due = False
        if self.frame is not None and isValid(self.frame):
            self.game.desktop.close_window(self.frame)


class EvalPanel(QWidget):
    def __init__(self, game):
        super().__init__()
        self.game = game
        self.frame = None
        self.setStyleSheet("QLabel { font-family: Tahoma; font-size: 11px; }")
        row = QHBoxLayout(self)
        self.left, self.right = QLabel(), QLabel()
        for lab in (self.left, self.right):
            lab.setAlignment(Qt.AlignTop | Qt.AlignLeft)
            lab.setStyleSheet("QLabel { background: #FFFFF0; border: 2px solid #1E7A34; padding: 8px; "
                              "font-family: Tahoma; font-size: 11px; }")
            row.addWidget(lab, 1)
        self.refresh()

    def refresh(self):
        c = self.game.city
        if c is None:
            return
        probs = "".join(f"<tr><td>{v}%</td><td>&nbsp;{k}</td></tr>" for k, v in list(c.problems.items())[:4])
        self.left.setText(f"<b style='color:#1E5A2A'>Is the mayor doing a good job?</b><br>"
                          f"<table><tr><td>{c.approval}%</td><td>&nbsp;YES</td></tr>"
                          f"<tr><td>{100 - c.approval}%</td><td>&nbsp;NO</td></tr></table><br>"
                          f"<b style='color:#1E5A2A'>What are the worst problems?</b><table>{probs}</table>")
        change = c.population - c.last_pop
        self.right.setText(f"<b style='color:#1E5A2A'>STATISTICS</b><table>"
                           f"<tr><td>Population</td><td align=right>{c.population:,}</td></tr>"
                           f"<tr><td>Net migration (this year)</td><td align=right>{change:+,}</td></tr>"
                           f"<tr><td>Assessed value</td><td align=right>{_money(getattr(c, 'assessed', 0))}</td></tr>"
                           f"<tr><td>Category</td><td align=right>{c.category().upper()}</td></tr>"
                           f"<tr><td>Game level</td><td align=right>{c.level}</td></tr></table><br>"
                           f"<b>Overall city score (0-1000)</b><br>Current score: {c.score}")


class GraphPanel(QWidget):
    SERIES = [("res", "Residential", "#30A030"), ("com", "Commercial", "#3060D0"), ("ind", "Industrial", "#C8A010"),
              ("funds", "Cash", "#20A0A0"), ("crime", "Crime", "#D02020"), ("pollution", "Pollution", "#8A6A20")]

    def __init__(self, game):
        super().__init__()
        self.game = game
        self.frame = None
        self.on = {"res", "com", "ind"}
        self.setMinimumSize(420, 260)

    def refresh(self):
        self.update()

    def mousePressEvent(self, e):
        for i, (k, _n, _c) in enumerate(self.SERIES):
            if QRectF(8 + i * 76, 6, 72, 18).contains(e.position()):
                self.on ^= {k}
                self.update()

    def paintEvent(self, _e):
        c = self.game.city
        p = QPainter(self)
        p.fillRect(self.rect(), QColor("#FFFFFF"))
        if c is None:
            return
        p.setRenderHint(QPainter.Antialiasing)
        for i, (k, name, col) in enumerate(self.SERIES):
            r = QRectF(8 + i * 76, 6, 72, 18)
            p.setPen(QPen(QColor(col), 1))
            p.setBrush(QColor(col) if k in self.on else QColor("#FFFFFF"))
            p.drawRect(QRectF(r.x(), r.y() + 4, 10, 10))
            p.setFont(_font(8))
            p.setPen(QColor("#000000"))
            p.drawText(r.adjusted(14, 0, 0, 0), Qt.AlignVCenter | Qt.AlignLeft, name)
        area = QRectF(30, 32, self.width() - 40, self.height() - 50)
        p.setPen(QPen(QColor("#C0C0C0"), 1))
        p.drawRect(area)
        for k, _name, col in self.SERIES:
            if k not in self.on:
                continue
            vals = c.history.get(k, [])
            if len(vals) < 2:
                continue
            lo, hi = min(min(vals), 0), max(vals) or 1
            pts = [QPointF(area.x() + i / (len(vals) - 1) * area.width(),
                           area.bottom() - (v - lo) / max(1e-6, hi - lo) * area.height()) for i, v in enumerate(vals)]
            p.setPen(QPen(QColor(col), 2))
            p.drawPolyline(QPolygonF(pts))
        p.setFont(_font(7))
        p.setPen(QColor("#606060"))
        n = len(c.history.get("res", []))
        p.drawText(QRectF(area.x(), area.bottom() + 2, area.width(), 14), Qt.AlignRight,
                   f"last {n // 12} years {n % 12} months")


# ---- the window --------------------------------------------------------------------------------------------------
_open = {}


def launch(desktop):
    win = _open.get("win")
    if win is not None and isValid(win):
        desktop.open_window(win)
        return win
    body = CityGame(desktop)
    win = host.window(desktop, "ClaudeCity", body, city_icon(), size=(1000, 720))
    body.frame = win
    _open["win"] = win
    desktop.open_window(win)
    body.setFocus()
    return win


def shutdown():
    win = _open.get("win")
    if win is not None and isValid(win):
        win.content.shutdown()
