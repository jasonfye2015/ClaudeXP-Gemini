"""FurCoder: encode and decode Furry Codes (2.0) and YIFF Codes (3.0).

Type or paste a code to read it in words, or build one with the encoder (every category, species, sub-option and
WIXXX interest). The list on the left looks up your own codes and every resident's (their YIFF Code only if they
show it). 'Make these my codes' changes how the residents treat you, from the next time the computer starts - the
same as changing them in the launcher's profile."""
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
                               QPushButton, QVBoxLayout, QWidget)
from shiboken6 import isValid

from claudecore import host

TITLE = "FurCoder"
MINE = "__mine__"


def furcoder_icon():
    pm = QPixmap(32, 32)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#3B2A6E"))
    p.drawRoundedRect(QRectF(1, 3, 30, 26), 5, 5)
    p.setBrush(QColor("#F2C14E"))                       # a paw
    p.drawEllipse(QRectF(11, 14, 10, 9))
    for x, y in ((8, 9), (12.5, 6.5), (17.5, 6.5), (22, 9)):
        p.drawEllipse(QRectF(x - 2, y, 4, 5))
    p.setPen(QColor("#FFFFFF"))
    f = QFont("Courier New")
    f.setPixelSize(9)
    f.setBold(True)
    p.setFont(f)
    p.drawText(QRectF(1, 21, 30, 9), Qt.AlignCenter, "{ FC }")
    p.end()
    return QIcon(pm)


def _residents():
    """[(name, tier, codes)] of this era's residents who have codes, main furs first."""
    try:
        import residents
    except ImportError:
        return []
    from claudecore.furcodes import furcode, yiff_public
    year = host.era()
    out = []
    for name in residents.names(year):
        r = residents.load(name, year)
        codes = dict((r.core.get("codes") or {}) if r else {})
        if not codes.get("furcode") and not codes.get("yiffcode"):
            continue
        codes["furcode"] = furcode.with_age(codes.get("furcode", ""), r.age)
        if not yiff_public(name, codes.get("yiffcode", ""), codes.get("show_yiff")):
            codes["yiffcode"] = ""                     # (they keep it to themselves)
        out.append((r.core.get("fur_name") or name, r.tier, codes, name))
    order = {"main": 0, "support": 1, "background": 2}
    out.sort(key=lambda t: (order.get(t[1], 3), t[0].lower()))
    return out


class FurCoder(QWidget):
    def __init__(self, desktop):
        super().__init__()
        self.desktop = desktop
        self.frame = None
        from claudecore.furcodes import user_codes
        from claudecore.furcodes.editor import CodesEditor
        row = QHBoxLayout(self)
        row.setContentsMargins(6, 6, 6, 6)
        left = QVBoxLayout()
        left.addWidget(QLabel("Look up"))
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search names")
        self.search.textChanged.connect(self._filter)
        left.addWidget(self.search)
        self.people = QListWidget()
        self.people.setFixedWidth(200)
        self.people.currentItemChanged.connect(lambda item, _o: self._look_up(item))
        left.addWidget(self.people, 1)
        row.addLayout(left)
        right = QVBoxLayout()
        self.whose = QLabel()
        self.whose.setWordWrap(True)
        right.addWidget(self.whose)
        self.editor = CodesEditor()
        right.addWidget(self.editor, 1)
        buttons = QHBoxLayout()
        for text, slot in (("Copy Furry Code", lambda: self._copy("furcode")),
                           ("Copy YIFF Code", lambda: self._copy("yiffcode")),
                           ("New (blank)", self._blank)):
            b = QPushButton(text)
            b.clicked.connect(slot)
            buttons.addWidget(b)
        buttons.addStretch(1)
        mine = QPushButton("Make these my codes")
        mine.setToolTip("The residents go by your codes: who's attracted to you, who's up for roleplay, what you "
                        "have in common")
        mine.clicked.connect(self._make_mine)
        buttons.addWidget(mine)
        right.addLayout(buttons)
        row.addLayout(right, 1)
        self.mine = user_codes()
        item = QListWidgetItem("Your codes")
        item.setData(Qt.UserRole, (MINE, self.mine))
        f = item.font()
        f.setBold(True)
        item.setFont(f)
        self.people.addItem(item)
        for shown, tier, codes, name in _residents():
            it = QListWidgetItem(shown)
            it.setData(Qt.UserRole, (name, codes))
            it.setToolTip(f"{tier.title()} fur")
            self.people.addItem(it)
        self.people.setCurrentRow(0)

    def select(self, name):
        for i in range(self.people.count()):
            item = self.people.item(i)
            if item.data(Qt.UserRole)[0].lower() == str(name).lower():
                self.search.clear()
                self.people.setCurrentRow(i)
                self.people.scrollToItem(item)
                return

    def _filter(self, text):
        want = text.strip().lower()
        for i in range(self.people.count()):
            item = self.people.item(i)
            item.setHidden(bool(want) and want not in item.text().lower() and i > 0)

    def _look_up(self, item):
        if item is None:
            return
        name, codes = item.data(Qt.UserRole)
        self.editor.set_codes(codes)
        if name == MINE:
            self.whose.setText("Your codes, from your Timeline profile. Change them here or in the launcher.")
        else:
            private = "" if codes.get("yiffcode") else "  They keep their YIFF Code to themselves."
            self.whose.setText(f"{item.text()}'s codes, as they show them.{private}")

    def _blank(self):
        self.people.blockSignals(True)
        self.people.clearSelection()
        self.people.setCurrentRow(-1)
        self.people.blockSignals(False)
        self.editor.set_codes({})
        self.whose.setText("A new code: build it with the encoder, or paste one in.")

    def _copy(self, key):
        code = self.editor.codes().get(key, "")
        if code:
            QApplication.clipboard().setText(code)

    def _make_mine(self):
        from claudecore.furcodes import save_user_codes
        codes = self.editor.codes()

        def answer(button):
            if button != "Yes":
                return
            if save_user_codes(codes):
                self.mine = codes
                self.people.item(0).setData(Qt.UserRole, (MINE, codes))
                host.message(self.desktop, TITLE, "These are your codes now. The residents go by them from the next "
                             "time Windows starts.", "info")
            else:
                host.message(self.desktop, TITLE, "There's no Timeline profile to save them to.", "warning")
        host.message(self.desktop, TITLE, "Make these your Furry Code and YIFF Code?\n\nThe residents will treat you "
                     "by them: who's attracted to you, who's up for roleplay, what you have in common.", "question",
                     ("Yes", "No"), answer)


_open = {}


def launch(desktop, select=None):
    """select: a resident's name to look up straight away."""
    win = _open.get("win")
    if win is None or not isValid(win):
        body = FurCoder(desktop)
        win = host.window(desktop, TITLE, body, furcoder_icon(), (1080, 680))
        body.frame = win
        _open["win"] = win
    if select:
        win.content.select(select)
    desktop.open_window(win)
    return win
