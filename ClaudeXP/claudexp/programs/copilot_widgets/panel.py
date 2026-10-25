"""The Copilot Desktop Widgets control panel: which widgets to show, locking, and the options."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QCheckBox, QComboBox, QDoubleSpinBox, QFormLayout, QGroupBox, QHBoxLayout, QLabel,
                               QPushButton, QSlider, QVBoxLayout, QWidget)
from shiboken6 import isValid

from ...wm import XPWindow
from . import art, weather as wx
from .widgets import WIDGETS

_open = {}


class Panel(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.c = controller
        self.frame = None
        root = QVBoxLayout(self)
        intro = QLabel("Widgets float on the desktop. Unlock them to drag them where you like, then lock "
                       "them again. Left-click the tray icon to open this window; right-click it for the menu.")
        intro.setWordWrap(True)
        root.addWidget(intro)

        top = QHBoxLayout()
        self.lock = QCheckBox("Lock widgets in place")
        self.lock.toggled.connect(lambda on: self.c.set("locked", on))
        self.visible = QCheckBox("Show widgets")
        self.visible.toggled.connect(lambda on: self.c.set("visible", on))
        top.addWidget(self.lock)
        top.addWidget(self.visible)
        root.addLayout(top)

        box = QGroupBox("Widgets")
        grid = QVBoxLayout(box)
        self.boxes = {}
        for cls in WIDGETS:
            check = QCheckBox(cls.TITLE)
            check.toggled.connect(lambda on, k=cls.KEY: self.c.set_enabled(k, on))
            grid.addWidget(check)
            self.boxes[cls.KEY] = check
        root.addWidget(box)

        form_box = QGroupBox("Options")
        form = QFormLayout(form_box)
        self.opacity = QSlider(Qt.Horizontal)
        self.opacity.setRange(20, 100)
        self.opacity.valueChanged.connect(lambda v: self.c.set("opacity", v))
        form.addRow("Opacity", self.opacity)
        self.climate = QComboBox()
        self.climate.addItems(list(wx.CLIMATES))
        self.climate.currentTextChanged.connect(lambda t: self.c.set("climate", t) if t else None)
        form.addRow("Weather climate", self.climate)
        self.hemisphere = QComboBox()
        self.hemisphere.addItems(wx.HEMISPHERES)
        self.hemisphere.currentTextChanged.connect(lambda t: self.c.set("hemisphere", t) if t else None)
        form.addRow("Hemisphere", self.hemisphere)
        self.latitude = QDoubleSpinBox()
        self.latitude.setRange(-66, 66)
        self.latitude.setSuffix("\u00B0")
        self.latitude.valueChanged.connect(lambda v: self.c.set("latitude", float(v)))
        form.addRow("Latitude (sunrise/sunset)", self.latitude)
        self.longitude = QDoubleSpinBox()
        self.longitude.setRange(-180, 180)
        self.longitude.setSuffix("\u00B0")
        self.longitude.setToolTip("West is negative: New York is about -74, London 0, Sydney 151. With it, sunrise "
                                  "and sunset land at the right clock time for your time zone.")
        self.longitude.valueChanged.connect(lambda v: self.c.set("longitude", float(v)))
        form.addRow("Longitude (sunrise/sunset)", self.longitude)
        self.real_moon = QCheckBox("Tonight's real moon, not the moon of this computer's year")
        self.real_moon.setToolTip("The sun's times barely change from year to year, but the moon's phase does: "
                                  "ticked, the Day and Night and Sun and Moon widgets show the moon as it is outside "
                                  "your window tonight.")
        self.real_moon.toggled.connect(lambda on: self.c.set("real_moon", on))
        form.addRow("Moon", self.real_moon)
        self.fahrenheit = QCheckBox("Fahrenheit and mph")
        self.fahrenheit.toggled.connect(lambda on: self.c.set("fahrenheit", on))
        form.addRow("Units", self.fahrenheit)
        self.h24 = QCheckBox("24-hour clock")
        self.h24.toggled.connect(lambda on: self.c.set("clock_24h", on))
        form.addRow("Clock", self.h24)
        self.through = QCheckBox("Locked widgets pass clicks through")
        self.through.toggled.connect(lambda on: self.c.set("click_through", on))
        form.addRow("Locking", self.through)
        self.logon = QCheckBox("Start with ClaudeXP")
        self.logon.toggled.connect(lambda on: self.c.set("start_at_logon", on))
        form.addRow("Startup", self.logon)
        root.addWidget(form_box)

        buttons = QHBoxLayout()
        reset = QPushButton("Reset Positions")
        reset.clicked.connect(self.c.reset_layout)
        close = QPushButton("Close")
        close.clicked.connect(lambda: self.frame.close() if self.frame is not None else None)
        buttons.addStretch(1)
        buttons.addWidget(reset)
        buttons.addWidget(close)
        root.addLayout(buttons)

        self.c.changed.connect(self.sync)
        self.sync()

    def sync(self):
        s = self.c.settings
        pairs = ((self.lock, s["locked"]), (self.visible, s["visible"]), (self.fahrenheit, s["fahrenheit"]),
                 (self.h24, s["clock_24h"]), (self.through, s["click_through"]), (self.logon, s["start_at_logon"]),
                 (self.real_moon, s["real_moon"]),
                 *((box, s["enabled"][key]) for key, box in self.boxes.items()))
        for box, value in pairs:
            box.blockSignals(True)
            box.setChecked(value)
            box.blockSignals(False)
        for control, value in ((self.opacity, s["opacity"]), (self.latitude, s["latitude"]),
                               (self.longitude, s["longitude"])):
            control.blockSignals(True)
            control.setValue(value)
            control.blockSignals(False)
        for combo, value in ((self.climate, s["climate"]), (self.hemisphere, s["hemisphere"])):
            combo.blockSignals(True)
            combo.setCurrentText(value)
            combo.blockSignals(False)


def open_panel(controller):
    win = _open.get("win")
    if win is None or not isValid(win):
        body = Panel(controller)
        win = XPWindow(controller.desktop, "Copilot Widgets", body, art.widgets_icon(16), (400, 600))
        body.frame = win
        _open["win"] = win
    controller.desktop.open_window(win)
    return win
