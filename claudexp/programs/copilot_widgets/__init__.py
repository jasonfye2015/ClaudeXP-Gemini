"""Copilot Desktop Widgets: a clock, calendar, weather, TV guide, Hotmail inbox and more floating on the desktop."""
import json
import warnings

from PySide6.QtCore import QObject, QPoint, QTimer, Qt, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu, QMessageBox, QSystemTrayIcon
from shiboken6 import isValid

from ..people import load_json
from ...paths import DATA
from ...tray import TrayIcon
from . import art, weather as wx
from .widgets import WIDGETS

SETTINGS_FILE = DATA / "copilot_widgets.json"
DEFAULT_ON = {"clock", "weather", "calendar", "tv", "mail"}
DEFAULTS = {
    "visible": True, "locked": True, "click_through": True, "start_at_logon": True, "opacity": 80,
    "fahrenheit": True, "clock_24h": False, "climate": "Temperate", "hemisphere": "Northern",
    "latitude": 40.0, "note": "",
}
MENU_STYLE = ("QMenu { background: white; border: 1px solid #ACA899; font-family: Tahoma; font-size: 11px; }"
              "QMenu::item { padding: 4px 24px 4px 20px; }"
              "QMenu::item:selected { background: #316AC5; color: white; }")
_controller = None


class WidgetsController(QObject):
    changed = Signal()

    def __init__(self, desktop):
        super().__init__(desktop)
        self.desktop = desktop
        self.settings = dict(DEFAULTS)
        self.settings["enabled"] = {cls.KEY: cls.KEY in DEFAULT_ON for cls in WIDGETS}
        self.settings["positions"] = {}
        self._load()
        self.widgets = {}
        self.panel = None
        self.tray = TrayIcon(desktop, art.widgets_icon(32, self.settings["locked"]), desktop)
        self.tray.activated.connect(self._tray_activated)
        self.menu = QMenu(desktop)
        self.menu.setStyleSheet(MENU_STYLE)
        self.tray.setContextMenu(self.menu)
        self.tray.show()
        self.apply()

    # ---- settings -----------------------------------------------------------------------------------------
    def _load(self):
        data = load_json(SETTINGS_FILE, {})
        if not isinstance(data, dict):
            warnings.warn(f"Ignoring unreadable Copilot Widgets settings in {SETTINGS_FILE}")
            return
        s = self.settings
        for key, default in DEFAULTS.items():
            value = data.get(key)
            if isinstance(default, bool):
                if isinstance(value, bool):
                    s[key] = value
            elif isinstance(default, float):
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    s[key] = max(-66.0, min(66.0, float(value)))
            elif isinstance(default, int):
                if isinstance(value, int) and not isinstance(value, bool):
                    s[key] = max(20, min(100, value))
            elif isinstance(value, str):
                s[key] = value[:600]
        if s["climate"] not in wx.CLIMATES:
            s["climate"] = DEFAULTS["climate"]
        if s["hemisphere"] not in wx.HEMISPHERES:
            s["hemisphere"] = DEFAULTS["hemisphere"]
        enabled = data.get("enabled")
        if isinstance(enabled, dict):
            for key in s["enabled"]:
                if isinstance(enabled.get(key), bool):
                    s["enabled"][key] = enabled[key]
        positions = data.get("positions")
        size = data.get("note_size")
        if isinstance(size, list) and len(size) == 2 and all(isinstance(v, int) and not isinstance(v, bool)
                                                              for v in size):
            s["note_size"] = [max(160, min(4000, size[0])), max(110, min(4000, size[1]))]
        if isinstance(positions, dict):
            for key, pos in positions.items():
                if key in s["enabled"] and isinstance(pos, list) and len(pos) == 2 \
                        and all(isinstance(v, int) and not isinstance(v, bool) for v in pos):
                    s["positions"][key] = pos

    def save(self):
        try:
            SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
            SETTINGS_FILE.write_text(json.dumps(self.settings, indent=2), encoding="utf-8")
        except OSError as exc:
            self.say("Copilot Widgets", f"Could not save the widget settings:\n{exc}")

    def say(self, title, text):
        QMessageBox.warning(self.desktop, title, text)

    def set(self, key, value):
        self.settings[key] = value
        self.save()
        self.apply()

    def set_enabled(self, key, on):
        self.settings["enabled"][key] = on
        self.save()
        self.apply()

    def weather(self):
        s = self.settings
        return wx.Weather(s["climate"], s["hemisphere"], s["latitude"])

    # ---- widgets ------------------------------------------------------------------------------------------
    def apply(self):
        s = self.settings
        passthrough = s["locked"] and s["click_through"]
        for cls in WIDGETS:
            want = s["visible"] and s["enabled"][cls.KEY]
            w = self.widgets.get(cls.KEY)
            if want and w is None:
                w = self.widgets[cls.KEY] = cls(self)
            if w is None:
                continue
            w.setAttribute(Qt.WA_TransparentForMouseEvents, passthrough and not getattr(w, "INTERACTIVE", False))
            if want:
                if w.isHidden():
                    w.show()
                    w.lower()
                    w.start()
                w.update()
            elif not w.isHidden():
                w.stop()
                w.hide()
        self.place_all()
        self.tray.setIcon(art.widgets_icon(32, s["locked"]))
        self.tray.setToolTip("Copilot Widgets \u2013 " + ("locked" if s["locked"] else "unlocked (drag to move)"))
        QTimer.singleShot(0, self._build_menu)
        self.changed.emit()

    def clamp(self, widget, pos):
        area = self.desktop.work_area()
        return QPoint(max(0, min(pos.x(), max(0, area.width() - widget.width()))),
                      max(0, min(pos.y(), max(0, area.bottom() + 1 - widget.height()))))

    def place_all(self):
        """Saved positions are kept; the rest flow down the right edge, then leftwards in more columns."""
        area = self.desktop.work_area()
        x_right, y, col_w = area.right() - 16, area.top() + 16, 0
        shown = {k: w for k, w in self.widgets.items() if not w.isHidden()}
        positions = self.settings["positions"]
        for cls in WIDGETS:
            w = shown.get(cls.KEY)
            if w is None:
                continue
            saved = positions.get(cls.KEY)
            if saved:
                w.move(self.clamp(w, QPoint(*saved)))
                continue
            under = shown.get(getattr(cls, "UNDER", ""))
            if under is not None and cls.UNDER in positions:
                # the one it belongs under was put somewhere by hand: follow it there
                w.move(self.clamp(w, QPoint(under.x(), under.y() + under.height() + 12)))
                continue
            # a widget and the ones that sit under it stay together in a column
            need = w.height() + sum(f.height() + 12 for f in shown.values()
                                    if getattr(f, "UNDER", "") == cls.KEY and f.KEY not in positions)
            if y + need > area.bottom() - 90 and col_w:
                x_right -= col_w + 12
                y, col_w = area.top() + 16, 0
            w.move(self.clamp(w, QPoint(x_right - w.width() + 1, y)))
            y += w.height() + 12
            col_w = max(col_w, w.width())

    def remember(self, widget):
        """Dragging one widget pins every shown widget where it is, so the others don't shuffle."""
        for key, w in self.widgets.items():
            if not w.isHidden():
                self.settings["positions"][key] = [w.x(), w.y()]
        self.save()

    def remember_note_size(self, note):
        self.settings["note_size"] = [note.width(), note.height()]
        self.save()

    def reset_layout(self):
        self.settings["positions"] = {}
        self.save()
        self.place_all()

    def desktop_resized(self):
        self.place_all()

    def shutdown(self):
        for w in self.widgets.values():
            if isValid(w):
                w.stop()
                w.close()
        self.widgets.clear()
        self.tray.hide()

    # ---- menus ----------------------------------------------------------------------------------------------
    def _check(self, menu, text, checked, slot):
        action = QAction(text, menu)
        action.setCheckable(True)
        action.setChecked(checked)
        action.triggered.connect(lambda state, f=slot: f(state))
        menu.addAction(action)
        return action

    def fill_menu(self, menu, widget=None):
        s = self.settings
        if widget is not None:
            menu.addAction(f"Hide {widget.TITLE}", lambda: self.set_enabled(widget.KEY, False))
            menu.addSeparator()
        self._check(menu, "Lock widgets in place", s["locked"], lambda on: self.set("locked", on))
        self._check(menu, "Widgets visible", s["visible"], lambda on: self.set("visible", on))
        shown = menu.addMenu("Widgets")
        for cls in WIDGETS:
            self._check(shown, cls.TITLE, s["enabled"][cls.KEY], lambda on, k=cls.KEY: self.set_enabled(k, on))
        opacity = menu.addMenu("Opacity")
        for pct in (100, 90, 80, 70, 60, 50, 40):
            self._check(opacity, f"{pct}%", s["opacity"] == pct, lambda _on, v=pct: self.set("opacity", v))
        place = menu.addMenu("Weather")
        for name in wx.CLIMATES:
            self._check(place, f"{name} climate", s["climate"] == name, lambda _on, v=name: self.set("climate", v))
        place.addSeparator()
        for name in wx.HEMISPHERES:
            self._check(place, f"{name} Hemisphere", s["hemisphere"] == name,
                        lambda _on, v=name: self.set("hemisphere", v))
        place.addSeparator()
        self._check(place, "Fahrenheit and mph", s["fahrenheit"], lambda on: self.set("fahrenheit", on))
        self._check(menu, "24-hour clock", s["clock_24h"], lambda on: self.set("clock_24h", on))
        self._check(menu, "Locked widgets pass clicks through", s["click_through"],
                    lambda on: self.set("click_through", on))
        self._check(menu, "Start with ClaudeXP", s["start_at_logon"], lambda on: self.set("start_at_logon", on))
        menu.addSeparator()
        menu.addAction("Reset widget positions", self.reset_layout)
        menu.addAction("Open Copilot Widgets\u2026", self.open_panel)

    def _build_menu(self):
        if not isValid(self.menu):
            return
        self.menu.clear()
        self.fill_menu(self.menu)

    def widget_menu(self, widget, pos):
        menu = QMenu(self.desktop)
        menu.setStyleSheet(MENU_STYLE)
        self.fill_menu(menu, widget)
        menu.popup(pos)

    def _tray_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self.open_panel()

    def toggle_lock(self):
        self.set("locked", not self.settings["locked"])

    def open_panel(self):
        from .panel import open_panel
        self.panel = open_panel(self)


def controller_for(desktop):
    global _controller
    if _controller is None or _controller.desktop is not desktop or not isValid(_controller):
        if _controller is not None and isValid(_controller):
            _controller.shutdown()
            _controller.deleteLater()
        _controller = WidgetsController(desktop)
    return _controller


def start_at_logon(desktop):
    """Create the tray icon at logon. The widgets themselves show up if they were left on."""
    probe = load_json(SETTINGS_FILE, {})
    if isinstance(probe, dict) and probe.get("start_at_logon") is False:
        return
    controller_for(desktop)


def on_resize(desktop):
    if _controller is not None and _controller.desktop is desktop and isValid(_controller):
        _controller.desktop_resized()


def launch(desktop):
    controller = controller_for(desktop)
    if not controller.settings["visible"]:
        controller.set("visible", True)
    controller.open_panel()
    return controller.panel


def shutdown():
    global _controller
    if _controller is not None and isValid(_controller):
        _controller.shutdown()
    _controller = None


def widgets_icon(size=32):
    return art.widgets_icon(size)
