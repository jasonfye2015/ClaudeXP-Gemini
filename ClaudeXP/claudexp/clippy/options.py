"""Control Panel > Office Assistant: Clippy's real off switch, how annoying he is, and what he watches."""
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (QCheckBox, QComboBox, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QPushButton, QSlider,
                               QVBoxLayout)
from shiboken6 import isValid

from . import LEVELS, art, get, moods, save, settings

_open = {}


def office_assistant_properties(desktop):
    win = _open.get("win")
    if win is not None and isValid(win):
        desktop.open_window(win)
        return win
    from ..network import DialogBody, _fixed_window
    cfg = settings()
    body = DialogBody()
    v = QVBoxLayout(body)
    v.setContentsMargins(12, 12, 12, 10)
    top = QHBoxLayout()
    pic = QLabel()
    pic.setPixmap(art.icon_pixmap(48))
    top.addWidget(pic, 0, Qt.AlignTop)
    intro = QLabel("Clippy, the Office Assistant, offers help, tips and opinions while you work. "
                   "Hiding him only lasts so long; to really turn him off, clear the box below.")
    intro.setWordWrap(True)
    intro.setFixedWidth(300)
    top.addWidget(intro, 1)
    v.addLayout(top)
    enabled = QCheckBox("&Use the Office Assistant")
    enabled.setChecked(cfg["enabled"])
    v.addWidget(enabled)

    level_box = QGroupBox("How helpful should he be?")
    lv = QVBoxLayout(level_box)
    slider = QSlider(Qt.Horizontal)
    slider.setRange(1, 5)
    slider.setTickPosition(QSlider.TicksBelow)
    slider.setValue(int(cfg["level"]))
    level_name = QLabel()
    ends = QHBoxLayout()
    ends.addWidget(QLabel("Barely there"))
    ends.addStretch()
    ends.addWidget(QLabel("Unbearable"))

    def show_level(n):
        level_name.setText(f"<b>{LEVELS[n]}</b>")
    slider.valueChanged.connect(show_level)
    show_level(slider.value())
    lv.addWidget(slider)
    lv.addLayout(ends)
    lv.addWidget(level_name, 0, Qt.AlignHCenter)
    v.addWidget(level_box)

    watch_box = QGroupBox("Show tips about")
    wv = QVBoxLayout(watch_box)
    boxes = {}
    for key, label in (("desktop", "What I do on the &desktop (programs, errors, the Recycle Bin...)"),
                       ("typing", "What I &type in Notepad, WordPad and other documents"),
                       ("chats", "My &chats with buddies on AIM, IRC and the MUCK"),
                       ("random", "&Random tips out of nowhere")):
        cb = QCheckBox(label)
        cb.setChecked(cfg["watch"].get(key, True))
        wv.addWidget(cb)
        boxes[key] = cb
    v.addWidget(watch_box)
    look_box = QGroupBox("Personality and looks")
    grid = QGridLayout(look_box)
    combos = {}
    rows = (("mood", "&Mood:", [(k, f"{i['label']} - {i['blurb']}") for k, i in moods.MOODS.items()]
             + [(moods.MOODY, "Moody - drifts between moods by itself")]),
            ("wire", "&Wire:", [(k, v[0]) for k, v in moods.WIRES.items()]),
            ("accessory", "&Accessory:", list(moods.ACCESSORIES.items())),
            ("size", "S&ize:", [(k, v[0]) for k, v in moods.SIZES.items()]))
    for r, (key, label, items) in enumerate(rows):
        box = QComboBox()
        for k, text in items:
            box.addItem(text, k)
        box.setCurrentIndex(max(0, box.findData(cfg.get(key))))
        lab = QLabel(label)
        lab.setBuddy(box)
        grid.addWidget(lab, r, 0)
        grid.addWidget(box, r, 1)
        combos[key] = box
    grid.setColumnStretch(1, 1)
    llm = QCheckBox("Let the language model &write his lines (fresh wording)")
    llm.setChecked(cfg.get("llm", True))
    roam = QCheckBox("Let him &wander around the desktop")
    roam.setChecked(cfg.get("roam", False))
    tray = QCheckBox("Show his icon in the &notification area")
    tray.setChecked(cfg.get("tray", True))
    for r, cb in enumerate((llm, roam, tray), start=len(rows)):
        grid.addWidget(cb, r, 0, 1, 2)
    v.addWidget(look_box)
    sounds = QCheckBox("Make &sounds")
    sounds.setChecked(cfg.get("sounds", True))
    v.addWidget(sounds)
    reset_row = QHBoxLayout()
    reset_label = QLabel(f"Tips you've turned off: {len(cfg['muted'])}")
    reset = QPushButton("&Reset my tips")
    reset.setEnabled(bool(cfg["muted"]))
    reset_row.addWidget(reset_label, 1)
    reset_row.addWidget(reset)
    v.addLayout(reset_row)
    cleared = {"muted": False}

    def do_reset():
        cleared["muted"] = True
        reset_label.setText("Tips you've turned off: 0")
        reset.setEnabled(False)
    reset.clicked.connect(do_reset)

    buttons = QHBoxLayout()
    buttons.addStretch()
    ok, cancel = QPushButton("OK"), QPushButton("Cancel")
    for b in (ok, cancel):
        b.setFixedSize(75, 23)
        buttons.addWidget(b)
    ok.setDefault(True)
    v.addLayout(buttons)
    holder = {}

    def close():
        w = holder.pop("win", None)
        if w is not None and isValid(w):
            desktop.close_window(w)

    def apply():
        data = settings()
        data["enabled"] = enabled.isChecked()
        data["level"] = slider.value()
        data["watch"] = {k: cb.isChecked() for k, cb in boxes.items()}
        data["sounds"] = sounds.isChecked()
        for key, box in combos.items():
            data[key] = box.currentData()
        data["llm"], data["roam"], data["tray"] = llm.isChecked(), roam.isChecked(), tray.isChecked()
        if cleared["muted"]:
            data["muted"] = []
        save(data)
        if get() is not None:
            get().reload()
        close()

    ok.clicked.connect(apply)
    cancel.clicked.connect(close)
    win = _fixed_window(desktop, "Office Assistant", body, close)
    win.icon = QIcon(art.icon_pixmap(16))
    holder["win"] = win
    _open["win"] = win
    desktop.open_window(win)
    return win
