"""The Claude Entertainment System - one screen saver that plays all the NES clock games in turn.

Super Claude Bros, Super Claude Bros. 3, The Legend of Claude, Zelda II: The Adventure of Claude and Metroid:
Claude's Mission, each for as long as you like (a few minutes is the default), in order or shuffled. Between games
the console shows its title card with the next cartridge's name, the way a menu cartridge would. Settings: which
games are in, how long each one plays, and the order. A game whose sprite sheets aren't in Local Storage is
skipped.

Each game is the screen saver it already is (screensaver.SAVERS), hosted inside this one."""
import random
import time

from PySide6.QtCore import QRect, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QImage, QPainter

NAME = "Claude Entertainment System"
# (the screen saver it is, the module with its sprite sheets, how it's billed on the title card)
GAMES = [("Super Claude Bros", "supercb", "SUPER CLAUDE BROS."),
         ("Super Claude Bros. 3", "smb3cb", "SUPER CLAUDE BROS. 3"),
         ("The Legend of Claude", "zeldacb", "THE LEGEND OF CLAUDE"),
         ("Zelda II: The Adventure of Claude", "zelda2cb", "ZELDA II - THE ADVENTURE OF CLAUDE"),
         ("Metroid: Claude's Mission", "metroidcb", "METROID - CLAUDE'S MISSION")]
ORDERS = ["In order", "Shuffle"]
MINUTES = [1, 2, 3, 5, 10, 15, 30, 60]
DEFAULTS = {"games": {name: True for name, _m, _t in GAMES}, "minutes": {name: 5 for name, _m, _t in GAMES},
            "order": "In order"}
CARD = 2.5                                      # seconds the title card shows between games


def settings():
    from . import display
    data = display.get().data.get("ces") or {}
    out = {}
    for k, v in DEFAULTS.items():
        got = data.get(k, v)
        out[k] = {**v, **got} if isinstance(v, dict) and isinstance(got, dict) else got
    return out


def save_settings(values):
    from . import display
    d = display.get()
    d.data["ces"] = {k: values.get(k, v) for k, v in DEFAULTS.items()}
    d._save()


def available(name):
    """Whether a game's pictures are there to play it with."""
    module = next((m for n, m, _t in GAMES if n == name), None)
    if module is None:
        return False
    try:
        mod = __import__(f"{__package__}.{module}", fromlist=["available"])
        return bool(mod.available())
    except Exception:
        return False


def make_saver_class(Saver, savers):
    """savers: the screen saver classes by name (screensaver.SAVERS, looked up when a game starts)."""

    class ClaudeEntertainmentSystem(Saver):
        """The console: a title card, then a game for its minutes, then the next card."""
        FPS = 60

        def __init__(self, parent=None):
            super().__init__(parent)
            self.cfg = settings()
            self.playlist = []
            self.game = None                     # the hosted saver widget
            self.name = None
            self.until = 0.0                     # when this game's minutes are up (time.monotonic)
            self.card = 0.0                      # when the title card ends, while it shows
            self._queue_next()

        def _choices(self):
            on = [n for n, _m, _t in GAMES if self.cfg["games"].get(n, True) and savers.get(n) is not None
                  and available(n)]
            return on

        def _queue_next(self):
            if not self.playlist:
                self.playlist = self._choices()
                if self.cfg["order"] == "Shuffle":
                    random.shuffle(self.playlist)
                    if len(self.playlist) > 1 and self.playlist[0] == self.name:   # (not the same game twice)
                        self.playlist.append(self.playlist.pop(0))
            if self.game is not None:
                self.game.hide()
                self.game.deleteLater()
                self.game = None
            self.name = self.playlist.pop(0) if self.playlist else None
            self.card = time.monotonic() + CARD if self.name else 0.0

        def _start_game(self):
            cls = savers.get(self.name)
            if cls is None:
                self._queue_next()
                return
            self.game = cls(self)
            self.game.setAttribute(Qt.WA_TransparentForMouseEvents)
            self.game.setGeometry(self.rect())
            self.game.show()
            self.until = time.monotonic() + int(self.cfg["minutes"].get(self.name, 5) or 5) * 60

        def _tick(self):
            self.t += 1 / self.FPS
            self.step()
            if self.card or self.name is None or self.game is None:
                self.update()                    # (a game paints itself: repainting under it would paint it twice)

        def resizeEvent(self, event):
            if self.game is not None:
                self.game.setGeometry(self.rect())
            super().resizeEvent(event)

        def step(self):
            if self.name is None:
                return
            now = time.monotonic()
            if self.card:
                if now >= self.card:
                    self.card = 0.0
                    self._start_game()
                return
            if now >= self.until:
                self._queue_next()

        # ---- the title card ----
        def _card_image(self):
            """The card at the NES's own size: the console's name, the cartridge, a blinking prompt."""
            w = max(256, int(round(240 * self.width() / max(1, self.height()))))
            img = QImage(w, 240, QImage.Format_ARGB32)
            img.fill(QColor("black"))
            p = QPainter(img)
            p.setRenderHint(QPainter.TextAntialiasing, False)
            f = QFont("Courier New")
            f.setBold(True)
            f.setStyleStrategy(QFont.NoAntialias)
            f.setPixelSize(12)
            p.setFont(f)
            p.setPen(QColor(228, 0, 88))                 # the NES's red stripe
            p.fillRect(QRect(0, 44, w, 3), QColor(228, 0, 88))
            p.fillRect(QRect(0, 196, w, 3), QColor(228, 0, 88))
            p.setPen(QColor(252, 252, 252))
            p.drawText(QRect(0, 22, w, 16), Qt.AlignCenter, "CLAUDE ENTERTAINMENT SYSTEM")
            title = next((t for n, _m, t in GAMES if n == self.name), self.name or "")
            f.setPixelSize(16 if len(title) <= 24 else 12)
            p.setFont(f)
            p.setPen(QColor(252, 216, 168))
            p.drawText(QRect(8, 90, w - 16, 40), Qt.AlignCenter | Qt.TextWordWrap, title)
            f.setPixelSize(10)
            p.setFont(f)
            if int(time.monotonic() * 3) % 2:
                p.setPen(QColor(188, 188, 188))
                p.drawText(QRect(0, 156, w, 14), Qt.AlignCenter, "PUSH START")
            p.setPen(QColor(124, 124, 124))
            mins = int(self.cfg["minutes"].get(self.name, 5) or 5)
            p.drawText(QRect(0, 206, w, 14), Qt.AlignCenter, f"{mins} MINUTE{'S' if mins != 1 else ''}")
            p.end()
            return img

        def paintEvent(self, event):
            p = QPainter(self)
            p.fillRect(self.rect(), QColor("black"))
            if self.name is None:
                p.setPen(QColor("white"))
                f = QFont("Tahoma")
                f.setPixelSize(max(9, self.height() // 30))
                p.setFont(f)
                p.drawText(self.rect(), Qt.AlignCenter, "The Claude Entertainment System has no games to play:\n"
                           "tick some in its Settings, or put their sprite sheets in Local Storage.")
                return
            if self.card:
                img = self._card_image()
                scale = min(self.width() / img.width(), self.height() / img.height())
                w, h = img.width() * scale, img.height() * scale
                p.drawImage(QRectF((self.width() - w) / 2, (self.height() - h) / 2, w, h), img)

    return ClaudeEntertainmentSystem


def settings_dialog(desktop, on_done=None):
    """Screen Saver > Settings for the Claude Entertainment System: which games, how long each, what order."""
    from PySide6.QtWidgets import (QCheckBox, QComboBox, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QPushButton,
                                   QVBoxLayout)
    from .network import DialogBody, _fixed_window
    s = settings()
    body = DialogBody()
    col = QVBoxLayout(body)
    group = QGroupBox("Cartridges")
    grid = QGridLayout(group)
    grid.addWidget(QLabel("Play"), 0, 0)
    grid.addWidget(QLabel("For"), 0, 1)
    rows = {}
    for r, (name, _m, _t) in enumerate(GAMES, start=1):
        tick = QCheckBox(name.replace("&", "&&"))
        tick.setChecked(bool(s["games"].get(name, True)))
        here = available(name)
        if not here:
            tick.setText(tick.text() + "  (no sprite sheets)")
        mins = QComboBox()
        mins.addItems([f"{m} minute{'s' if m != 1 else ''}" for m in MINUTES])
        cur = int(s["minutes"].get(name, 5) or 5)
        mins.setCurrentIndex(MINUTES.index(cur) if cur in MINUTES else MINUTES.index(5))
        tick.toggled.connect(mins.setEnabled)
        mins.setEnabled(tick.isChecked())
        grid.addWidget(tick, r, 0)
        grid.addWidget(mins, r, 1)
        rows[name] = (tick, mins)
    col.addWidget(group)
    order_row = QHBoxLayout()
    order_label = QLabel("&Order:")
    order = QComboBox()
    order.addItems(ORDERS)
    order.setCurrentText(s["order"] if s["order"] in ORDERS else ORDERS[0])
    order_label.setBuddy(order)
    order_row.addWidget(order_label)
    order_row.addWidget(order)
    order_row.addStretch(1)
    smb = QPushButton("Super Claude Bros &options...")
    order_row.addWidget(smb)
    col.addLayout(order_row)
    row = QHBoxLayout()
    row.addStretch(1)
    ok, cancel = QPushButton("OK"), QPushButton("Cancel")
    for b in (ok, cancel):
        b.setFixedSize(75, 23)
        row.addWidget(b)
    col.addLayout(row)
    body.setMinimumWidth(420)
    holder = {}

    def close():
        win = holder.get("win")
        if win is not None:
            desktop.close_window(win)

    def accept():
        save_settings({"games": {n: t.isChecked() for n, (t, _m) in rows.items()},
                       "minutes": {n: MINUTES[m.currentIndex()] for n, (_t, m) in rows.items()},
                       "order": order.currentText()})
        close()
        if on_done:
            on_done()

    def smb_options():
        from .supercb import settings_dialog as smb_dialog
        smb_dialog(desktop)

    smb.clicked.connect(smb_options)
    ok.clicked.connect(accept)
    cancel.clicked.connect(close)
    win = _fixed_window(desktop, "Claude Entertainment System Setup", body, close)
    holder["win"] = win
    desktop.open_window(win)
    return win
