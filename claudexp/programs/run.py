"""Start > Run...: type a program, folder, document or web address, and Windows opens it."""
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QComboBox, QGridLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy

from .. import sound
from ..paths import DATA
from .people import load_json, save_json

HISTORY_FILE = DATA / "run.json"
_open = {}


def run_icon():
    pm = QPixmap(32, 32)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(QPen(QColor("#405070"), 1))
    p.setBrush(QColor("#F4F4F4"))
    p.drawRect(QRectF(3.5, 6.5, 25, 19))
    p.setBrush(QColor("#2A5DD6"))
    p.drawRect(QRectF(3.5, 6.5, 25, 4))
    p.setPen(QPen(QColor("#2A9A2A"), 2.5))
    p.drawLine(9, 21, 20, 14)
    p.drawLine(20, 14, 15, 14)
    p.drawLine(20, 14, 19, 19)
    p.end()
    return QIcon(pm)


def open_run(desktop, title="Run"):
    from shiboken6 import isValid
    from ..explorer.dialogs import msgbox
    from ..network import DialogBody, _fixed_window
    from .commands import resolve
    win = _open.get("win")
    if win is not None and isValid(win):
        desktop.open_window(win)
        return win
    body = DialogBody()
    grid = QGridLayout(body)
    grid.setContentsMargins(12, 12, 12, 12)
    grid.setHorizontalSpacing(10)
    pic = QLabel()
    pic.setPixmap(run_icon().pixmap(32, 32))
    pic.setAlignment(Qt.AlignTop)
    grid.addWidget(pic, 0, 0)
    text = QLabel("Type the name of a program, folder, document, or Internet resource, and Windows will open it for you.")
    text.setWordWrap(True)
    grid.addWidget(text, 0, 1, 1, 2)
    label = QLabel("&Open:")
    combo = QComboBox()
    combo.setEditable(True)
    combo.setInsertPolicy(QComboBox.NoInsert)
    combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    history = load_json(HISTORY_FILE, [])
    combo.addItems(history)
    combo.setEditText(history[0] if history else "")
    label.setBuddy(combo)
    grid.addWidget(label, 1, 0)
    grid.addWidget(combo, 1, 1, 1, 2)
    row = QHBoxLayout()
    row.addStretch()
    ok, cancel, browse = QPushButton("OK"), QPushButton("Cancel"), QPushButton("&Browse...")
    browse.setEnabled(False)
    for b in (ok, cancel, browse):
        b.setFixedSize(75, 23)
        row.addWidget(b)
    grid.addLayout(row, 2, 0, 1, 3)
    body.setFixedWidth(350)

    def close():
        w = _open.pop("win", None)
        if w is not None and isValid(w):
            desktop.close_window(w)

    def accept():
        typed = combo.currentText().strip()
        if not typed:
            return
        action = resolve(desktop, typed)
        if action is None:
            msgbox(desktop, typed, f"Windows cannot find '{typed}'. Make sure you typed the name correctly, and "
                   "then try again. To search for a file, click the Start button, and then click Search.", "error")
            return
        items = [typed] + [h for h in load_json(HISTORY_FILE, []) if h.lower() != typed.lower()]
        save_json(HISTORY_FILE, items[:26])
        close()
        action()

    ok.clicked.connect(accept)
    combo.lineEdit().returnPressed.connect(accept)
    cancel.clicked.connect(close)
    combo.editTextChanged.connect(lambda t: ok.setEnabled(bool(t.strip())))
    ok.setEnabled(bool(combo.currentText().strip()))
    win = _fixed_window(desktop, title, body, close)
    win.icon = run_icon()
    area = desktop.work_area()
    win.move(8, area.bottom() - win.height() - 8)    # XP opens Run just above the Start button
    _open["win"] = win
    desktop.open_window(win)
    sound.play("navigate")
    combo.setFocus()
    combo.lineEdit().selectAll()
    return win
