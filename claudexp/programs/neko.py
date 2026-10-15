"""Copilot Neko, the classic desktop cat."""
import json
import random
import time
import warnings

from PySide6.QtCore import QPoint, QRect, Qt, QTimer
from PySide6.QtGui import QAction, QActionGroup
from PySide6.QtWidgets import QMenu, QMessageBox, QSystemTrayIcon, QToolTip, QWidget

from ..paths import DATA
from ..tray import TrayIcon
from . import neko_art

SETTINGS_FILE = DATA / "copilot_neko.json"
DEFAULT_SETTINGS = {"start_at_logon": True, "palette": "random", "bubbles": True}


class NekoWidget(QWidget):
    """A tiny floating cat that lounges on the desktop and reacts to user activity."""

    def __init__(self, desktop, controller):
        super().__init__(desktop)
        self.desktop = desktop
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setAttribute(Qt.WA_StyledBackground, False)
        self.resize(72, 72)
        self._pose = "sit"
        self._frame = 0
        self._frame_tick = 0
        self._dragging = False
        self._moved_by_user = False
        self._drag_offset = QPoint()
        self._idle_since = time.monotonic()
        self._last_balloon = 0.0
        self._palette = controller.palette()
        self.controller = controller
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(240)
        self._place_default()
        self.show()
        QTimer.singleShot(1500, self._place_default)          # again once the desktop icons have been laid out

    def _obstacles(self):
        """What Neko shouldn't sit on: desktop icons, Clippy, the desktop widgets (not windows or the taskbar)."""
        from ..desktop_icons import DesktopIcon
        from ..wm import XPWindow
        skip = {self, getattr(self.desktop, "taskbar", None), getattr(self.desktop, "start_menu", None),
                getattr(self.desktop, "balloon", None), getattr(self.desktop, "hdd", None)}
        return [w.geometry() for w in self.desktop.children()
                if isinstance(w, QWidget) and w.isVisible() and w not in skip and not isinstance(w, XPWindow)
                and (isinstance(w, DesktopIcon) or w.width() < self.desktop.width() // 2)]

    def _place_default(self):
        """Bottom left, or the first free spot to the right of it (unless you've moved Neko yourself)."""
        rect = self.desktop.work_area()
        if self._moved_by_user:
            self.move(max(0, min(self.x(), rect.right() - self.width())),
                      max(0, min(self.y(), rect.bottom() - self.height())))
            return
        y = max(0, rect.bottom() - self.height() - 18)
        taken = [g.adjusted(-6, -6, 6, 6) for g in self._obstacles()]
        x = start = max(0, rect.left() + 24)
        while x + self.width() <= rect.right():
            if not any(QRect(x, y, self.width(), self.height()).intersects(g) for g in taken):
                break
            x += 8
        else:
            x = start                                          # nowhere free: back to the corner
        self.move(x, y)

    def _tick(self):
        if self._dragging:
            return

        self._frame = (self._frame + 1) % 8
        self._frame_tick += 1
        now = time.monotonic()

        if self._frame_tick % 5 == 0:
            if self._pose == "sit":
                if random.random() < 0.16:
                    self._pose = random.choice(["sleep", "scratch", "yawn", "pet"])
                    self._idle_since = now
            elif self._pose in {"sleep", "scratch", "yawn", "pet"} and now - self._idle_since > 5:
                self._pose = "sit"

        if self.controller.settings["bubbles"] and now - self._last_balloon > 24 and random.random() < 0.08:
            self._bubble(random.choice([
                "Mrrrrow!",
                "Copilot Neko is keeping watch.",
                "Prrr... you are doing well.",
                "The desktop is cozy today.",
            ]))
            self._last_balloon = now

        self.update()

    def _bubble(self, text):
        if not self.isVisible():
            return
        pos = self.mapToGlobal(self.rect().topLeft() + QPoint(12, -8))
        QToolTip.showText(pos, text, self)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._dragging = True
            self._drag_offset = event.pos()
            self.raise_()
            self._pose = "alert"
            self.update()

    def mouseMoveEvent(self, event):
        if self._dragging:
            new_pos = self.pos() + event.pos() - self._drag_offset
            max_x = max(0, self.desktop.width() - self.width())
            max_y = max(0, self.desktop.height() - self.height())
            self.move(max(0, min(new_pos.x(), max_x)), max(0, min(new_pos.y(), max_y)))

    def mouseReleaseEvent(self, event):
        if self._dragging:
            self._dragging = False
            self._moved_by_user = True
            self._pose = "pet"
            self._idle_since = time.monotonic()
            self.update()
            if event.button() == Qt.LeftButton and self.controller.settings["bubbles"]:
                self._bubble(random.choice(["Mrrrp!", "Purr...", "Neko likes that."]))

    def enterEvent(self, event):
        self._pose = "alert"
        self.update()

    def leaveEvent(self, event):
        self._pose = "sit"
        self.update()

    def mouseDoubleClickEvent(self, event):
        self._pose = "sleep" if self._pose != "sleep" else "sit"
        self._idle_since = time.monotonic()
        self.update()

    def paintEvent(self, event):
        from PySide6.QtGui import QPainter

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        pixmap = neko_art.render_sprite(self._pose, self._frame, self._palette, 72)
        painter.drawPixmap(self.rect(), pixmap)


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
        if self.settings["palette"] != "random" and self.settings["palette"] not in neko_art.PALETTES:
            self.settings["palette"] = "random"
        self.tray = TrayIcon(desktop, neko_art.paw_icon(32), desktop)
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
        return random.choice(list(neko_art.PALETTES)) if selected == "random" else selected

    def _build_menu(self):
        self.menu.clear()
        self.start_action = QAction("Start Copilot Neko with ClaudeXP", self.menu)
        self.start_action.setCheckable(True)
        self.start_action.setChecked(self.settings["start_at_logon"])
        self.start_action.toggled.connect(self._set_start_at_logon)
        self.menu.addAction(self.start_action)

        self.show_action = QAction("Show Copilot Neko", self.menu)
        self.show_action.setCheckable(True)
        self.show_action.setChecked(self.widget is not None and self.widget.isVisible())
        self.show_action.toggled.connect(self._set_visible)
        self.menu.addAction(self.show_action)

        colors = self.menu.addMenu("Fur Color")
        color_group = QActionGroup(colors)
        color_group.setExclusive(True)
        random_color = QAction("Random each time", colors)
        random_color.setCheckable(True)
        random_color.setChecked(self.settings["palette"] == "random")
        random_color.triggered.connect(lambda: self._set_palette("random"))
        color_group.addAction(random_color)
        colors.addAction(random_color)
        colors.addSeparator()
        for key, palette in neko_art.PALETTES.items():
            action = QAction(palette["name"], colors)
            action.setCheckable(True)
            action.setChecked(self.settings["palette"] == key)
            action.triggered.connect(lambda _checked=False, value=key: self._set_palette(value))
            color_group.addAction(action)
            colors.addAction(action)

        bubbles = QAction("Chatty desktop bubbles", self.menu)
        bubbles.setCheckable(True)
        bubbles.setChecked(self.settings["bubbles"])
        bubbles.toggled.connect(self._set_bubbles)
        self.menu.addAction(bubbles)
        self.menu.addAction("Give Neko a treat", self._treat)
        self.menu.addSeparator()
        self.menu.addAction("Close Neko", self.hide)
        self.menu.aboutToShow.connect(self._refresh_menu)

    def _refresh_menu(self):
        self.show_action.setChecked(self.widget is not None and self.widget.isVisible())

    def _set_start_at_logon(self, enabled):
        self.settings["start_at_logon"] = enabled
        self._save()

    def _set_bubbles(self, enabled):
        self.settings["bubbles"] = enabled
        self._save()

    def _set_palette(self, palette):
        self.settings["palette"] = palette
        if self.widget is not None:
            self.widget._palette = self.palette()
            self.widget.update()
        self._save()

    def _set_visible(self, visible):
        self.show() if visible else self.hide()

    def show(self):
        if self.widget is None:
            self.widget = NekoWidget(self.desktop, self)
        else:
            self.widget.show()
            self.widget._timer.start(240)
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
        self.widget._pose = "pet"
        self.widget._idle_since = time.monotonic()
        if self.settings["bubbles"]:
            self.widget._bubble("A treat! Prrrr...")
        self.widget.update()

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
    return neko_art.neko_icon(size)
