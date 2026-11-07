"""The title, as Claude and Magic has one: first a title card - the name painted large over Thornwick at dusk,
turning slowly, the music already playing - and then, at a key or a click, the title's one page: a header, and tabs
for Play (the three save slots as cards: where each stands, Continue or New Game), Records (what each Claude has
done), Options (music, sound, the townsfolk's voices, the mouse), Keys and Credits. Nothing scrolls.

Keys: on the card any key; on the page 1-3 choose a slot, Enter plays it, Tab / Q / E change the tab, Esc goes
back to the card."""
import math
import time

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPainterPath, QPen, QRadialGradient
from PySide6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QStackedLayout, QVBoxLayout, QWidget

from ..game import data as D
from . import theme
from .icons import icon

VERSION = "v0.17"
TAGLINE = "Before he was the Lich King, he was an apprentice with a birch wand - and a hundred floors to go down."

CSS = theme.CSS + """
QWidget#title { background: transparent; }
QFrame#slot { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(50,38,26,235), stop:1 rgba(24,18,12,235));
              border: 2px solid #5A4630; border-radius: 10px; }
QFrame#slot[on="true"] { border: 2px solid #F0C868;
              background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(84,62,34,240), stop:1 rgba(36,26,14,240)); }
QFrame#slot:hover { border-color: #B89048; }
QLabel#where { color: #F6D98A; font-size: 19px; font-weight: bold; }
QLabel#slotn { color: #B8A078; font-size: 12px; letter-spacing: 2px; }
QLabel#dim { color: #C0B090; font-size: 13px; }
QLabel#h2 { color: #F6D98A; font-size: 19px; font-weight: bold; }
QPushButton#tab { min-width: 110px; }
QPushButton#tab[on="true"] { border-color: #FFD878; color: #FFF0C0;
              background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #9A7438, stop:1 #4A3218); }
QPushButton#big { font-size: 19px; padding: 10px 34px; border-color: #F0C868;
              background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #A07838, stop:0.5 #6A4A20, stop:1 #3A2810); }
"""


RAINBOW = {"on": False}                                   # (an old code, remembered: the name in every colour)
OLD_CODE = [Qt.Key_Up, Qt.Key_Up, Qt.Key_Down, Qt.Key_Down, Qt.Key_Left, Qt.Key_Right, Qt.Key_Left, Qt.Key_Right,
            Qt.Key_B, Qt.Key_A]


def paint_logo(p, cx, cy, scale=1.0, t=0.0):
    """The name, painted: CLAUDENITES in gold with a dark edge and a glow, 3-D in the wand's violet, and the wand
    across it with its light."""
    p.save()
    p.setRenderHint(QPainter.Antialiasing)
    f = QFont("Georgia", int(64 * scale), QFont.Bold)
    f.setLetterSpacing(QFont.PercentageSpacing, 108)
    path = QPainterPath()
    path.addText(0, 0, f, "CLAUDENITES")
    br = path.boundingRect()
    path.translate(cx - br.width() / 2 - br.x(), cy + br.height() / 2 - 12 * scale)
    br = path.boundingRect()
    # its glow
    glow = QRadialGradient(QPointF(cx, br.center().y()), br.width() * 0.62)
    glow.setColorAt(0, QColor(255, 190, 90, 70))
    glow.setColorAt(1, QColor(255, 190, 90, 0))
    p.setPen(Qt.NoPen)
    p.setBrush(glow)
    p.drawEllipse(QPointF(cx, br.center().y()), br.width() * 0.62, br.width() * 0.62)
    p.setPen(QPen(QColor(20, 12, 6, 230), 9 * scale, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    p.drawPath(path)
    g = QLinearGradient(0, br.top(), 0, br.bottom())
    g.setColorAt(0, QColor("#FFF2C0"))
    g.setColorAt(0.45, QColor("#F2C860"))
    g.setColorAt(1, QColor("#9A6420"))
    if RAINBOW["on"]:
        g = QLinearGradient(br.left(), 0, br.right(), 0)
        for k in range(7):
            g.setColorAt(k / 6, QColor.fromHsvF(((k / 7) + t * 0.15) % 1.0, 0.65, 1.0))
    p.setPen(QPen(QColor("#5A3A12"), 1.5 * scale))
    p.setBrush(g)
    p.drawPath(path)
    # 3-D, below to the right, in the wand's light
    f2 = QFont("Georgia", int(30 * scale), QFont.Bold)
    p2 = QPainterPath()
    p2.addText(0, 0, f2, "3 - D")
    b2 = p2.boundingRect()
    p2.translate(br.right() - b2.width() - b2.x(), br.bottom() + b2.height() + 6 * scale)
    pulse = 0.75 + 0.25 * math.sin(t * 2.2)
    p.setPen(QPen(QColor(20, 8, 30, 220), 6 * scale, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    p.drawPath(p2)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor.fromRgbF(0.78, 0.6 * pulse + 0.2, 1.0))
    p.drawPath(p2)
    # the wand, under the name, its tip burning
    y = br.bottom() + 18 * scale
    x0, x1 = br.left() + br.width() * 0.08, br.left() + br.width() * 0.62
    p.setPen(QPen(QColor("#6A4424"), 7 * scale, Qt.SolidLine, Qt.RoundCap))
    p.drawLine(QPointF(x0, y + 4 * scale), QPointF(x1, y - 4 * scale))
    p.setPen(QPen(QColor("#B07A44"), 3 * scale, Qt.SolidLine, Qt.RoundCap))
    p.drawLine(QPointF(x0, y + 3 * scale), QPointF(x1, y - 5 * scale))
    tip = QRadialGradient(QPointF(x1 + 4 * scale, y - 5 * scale), 26 * scale * (0.85 + 0.15 * pulse))
    tip.setColorAt(0, QColor(255, 255, 255, 255))
    tip.setColorAt(0.25, QColor(190, 140, 255, 220))
    tip.setColorAt(1, QColor(160, 100, 255, 0))
    p.setPen(Qt.NoPen)
    p.setBrush(tip)
    p.drawEllipse(QPointF(x1 + 4 * scale, y - 5 * scale), 26 * scale, 26 * scale)
    p.restore()
    return br


class TitleCard(QWidget):
    """The name over Thornwick; any key or click goes on."""

    def __init__(self, title):
        super().__init__()
        self.title = title
        self.t0 = time.perf_counter()
        self.setFocusPolicy(Qt.StrongFocus)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(33)

    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        W, H = self.width(), self.height()
        t = time.perf_counter() - self.t0
        v = QRadialGradient(QPointF(W / 2, H * 0.45), max(W, H) * 0.75)
        v.setColorAt(0, QColor(0, 0, 0, 30))
        v.setColorAt(0.6, QColor(0, 0, 0, 110))
        v.setColorAt(1, QColor(0, 0, 0, 220))
        p.fillRect(self.rect(), v)
        scale = max(0.55, min(1.4, W / 1300))
        br = paint_logo(p, W / 2, H * 0.36, scale, t)
        f = QFont("Georgia", int(15 * scale))
        f.setItalic(True)
        p.setFont(f)
        p.setPen(QColor(232, 220, 192, 230))
        p.drawText(QRectF(0, br.bottom() + 70 * scale, W, 40), Qt.AlignHCenter, TAGLINE)
        a = int(140 + 110 * (0.5 + 0.5 * math.sin(t * 2.6)))
        p.setFont(QFont("Georgia", int(14 * scale)))
        p.setPen(QColor(240, 214, 140, a))
        p.drawText(QRectF(0, H * 0.78, W, 40), Qt.AlignHCenter, "Press any key, or click, to begin")
        p.setFont(QFont("Segoe UI", 9))
        p.setPen(QColor(200, 190, 170, 150))
        p.drawText(QRectF(0, H - 30, W - 16, 24), Qt.AlignRight, f"Claudenites 3-D {VERSION} - a Claude Timeline game")
        p.drawText(QRectF(16, H - 30, W, 24), Qt.AlignLeft, "Music: ClaudeRPG's, made as it plays - art: Claude and Magic's")
        p.end()

    def keyPressEvent(self, e):
        self.title.to_sheet()

    def mousePressEvent(self, e):
        self.title.to_sheet()


class TitleScreen(QWidget):
    def __init__(self, shell):
        super().__init__()
        self.setObjectName("title")
        self.setStyleSheet(CSS)
        self.shell = shell
        RAINBOW["on"] = bool(shell.settings.get("konami"))
        from PySide6.QtWidgets import QApplication
        QApplication.instance().installEventFilter(self)
        self.chosen = self._latest()
        self.tab = "play"
        self.confirm = None
        self.stack = QStackedLayout(self)
        self.card = TitleCard(self)
        self.stack.addWidget(self.card)
        self.page = QWidget()
        self.stack.addWidget(self.page)
        self.page_lay = QVBoxLayout(self.page)
        self.page_lay.setContentsMargins(40, 24, 40, 20)
        QTimer.singleShot(0, self.card.setFocus)

    def _latest(self):
        best, when = 0, -1
        for s in range(3):
            d = self.shell.saves.load(s)
            if d and d.get("saved", 0) > when:
                best, when = s, d.get("saved", 0)
        return best

    # ---- the card and the page ------------------------------------------------------------------------------
    def to_sheet(self):
        self.shell.sounds.play("click", 0.5)
        self.build()
        self.stack.setCurrentWidget(self.page)
        self.page.setFocus()

    def to_card(self):
        self.stack.setCurrentWidget(self.card)
        self.card.setFocus()

    def build(self):
        _clear(self.page_lay)
        head = QHBoxLayout()
        head.addStretch(1)
        logo = _Logo()
        logo.setFixedSize(520, 120)
        head.addWidget(logo)
        head.addStretch(1)
        self.page_lay.addLayout(head)
        tabs = QHBoxLayout()
        tabs.addStretch(1)
        for key, name in (("play", "Play"), ("records", "Records"), ("options", "Options"), ("keys", "Keys"), ("credits", "Credits")):
            b = QPushButton(name)
            b.setObjectName("tab")
            b.setProperty("on", key == self.tab)
            b.clicked.connect(lambda _=False, k=key: self.set_tab(k))
            tabs.addWidget(b)
        tabs.addStretch(1)
        self.page_lay.addLayout(tabs)
        sheet = theme.Ornate()
        lay = QVBoxLayout(sheet)
        lay.setContentsMargins(26, 20, 26, 20)
        getattr(self, "_" + self.tab)(lay)
        row = QHBoxLayout()
        row.addStretch(1)
        row.addWidget(sheet, 0)
        row.addStretch(1)
        sheet.setFixedWidth(min(1120, max(760, self.width() - 80)))
        self.page_lay.addLayout(row, 1)
        foot = QLabel(f"Claudenites 3-D {VERSION}  -  1-3 choose a slot, Enter plays, Tab changes the page, Esc the title card")
        foot.setObjectName("dim")
        foot.setAlignment(Qt.AlignCenter)
        self.page_lay.addWidget(foot)

    def set_tab(self, key):
        self.tab = key
        self.confirm = None
        self.build()

    # ---- Play ---------------------------------------------------------------------------------------------
    def _play(self, lay):
        h = QLabel("Choose a Claude")
        h.setObjectName("h2")
        lay.addWidget(h)
        grid = QHBoxLayout()
        grid.setSpacing(14)
        for slot in range(3):
            grid.addWidget(self._slot_card(slot))
        lay.addLayout(grid)
        lay.addSpacing(10)
        row = QHBoxLayout()
        row.addStretch(1)
        info = self.shell.saves.summary(self.chosen)
        go = QPushButton("Continue" if info else "New Game")
        go.setObjectName("big")
        go.clicked.connect(lambda: self.shell.play(self.chosen))
        row.addWidget(go)
        if info:
            d = QPushButton("Are you sure? Delete it" if self.confirm == self.chosen else "Delete this Claude")
            d.setObjectName("danger")
            d.clicked.connect(self._delete)
            row.addWidget(d)
        row.addStretch(1)
        lay.addLayout(row)
        lay.addSpacing(6)
        note = QLabel("Saves keep themselves: on going home, on the stairs, and on leaving. A fallen Claude keeps "
                      "everything but the run.")
        note.setObjectName("dim")
        note.setAlignment(Qt.AlignCenter)
        note.setWordWrap(True)
        lay.addWidget(note)

    def _slot_card(self, slot):
        info = self.shell.saves.summary(slot)
        card = QFrame()
        card.setObjectName("slot")
        card.setProperty("on", slot == self.chosen)
        card.setCursor(Qt.PointingHandCursor)
        card.setMinimumHeight(190)
        v = QVBoxLayout(card)
        n = QLabel(f"SLOT {slot + 1}")
        n.setObjectName("slotn")
        v.addWidget(n)
        if info:
            band = D.band_of(info["floor"])["name"]
            w = QLabel(f"Floor {info['floor']} open")
            w.setObjectName("where")
            v.addWidget(w)
            for line in (band, f"Claude, level {info['level']} - {info['gold']} gold",
                         f"Deepest floor {info['deepest']} - {info['kills']} slain - fallen {info['deaths']}",
                         f"Saved {info['when']}"):
                lab = QLabel(line)
                lab.setObjectName("dim")
                v.addWidget(lab)
            d = self.shell.saves.load(slot) or {}
            wands = [w for w in (d.get("player", {}).get("wands") or []) if w]
            if wands:
                icons = QHBoxLayout()
                for wd in wands:
                    lab = QLabel()
                    try:
                        lab.setPixmap(icon(wd, 34))
                    except Exception:
                        pass
                    icons.addWidget(lab)
                icons.addStretch(1)
                v.addLayout(icons)
        else:
            w = QLabel("Empty")
            w.setObjectName("where")
            v.addWidget(w)
            lab = QLabel("A new apprentice, a birch wand, and the Deep under the square.")
            lab.setObjectName("dim")
            lab.setWordWrap(True)
            v.addWidget(lab)
        v.addStretch(1)
        card.mousePressEvent = lambda _e, s=slot: self._choose(s)
        card.mouseDoubleClickEvent = lambda _e, s=slot: self.shell.play(s)
        return card

    def _choose(self, slot):
        self.chosen = slot
        self.confirm = None
        self.shell.sounds.play("click", 0.4)
        self.build()

    def _delete(self):
        if self.confirm != self.chosen:
            self.confirm = self.chosen
        else:
            self.shell.saves.delete(self.chosen)
            self.confirm = None
        self.build()

    # ---- Records ------------------------------------------------------------------------------------------
    def _records(self, lay):
        h = QLabel("What each Claude has done")
        h.setObjectName("h2")
        lay.addWidget(h)
        grid = QGridLayout()
        for slot in range(3):
            d = self.shell.saves.load(slot)
            box = QFrame()
            box.setObjectName("slot")
            v = QVBoxLayout(box)
            n = QLabel(f"SLOT {slot + 1}")
            n.setObjectName("slotn")
            v.addWidget(n)
            if not d:
                v.addWidget(QLabel("Nobody yet."))
            else:
                pl = d.get("player", {})
                st = pl.get("stats", {})
                lines = [f"Level {pl.get('level', 1)}, {pl.get('gold', 0)} gold",
                         f"Deepest floor: {st.get('deepest', 0)}", f"Slain: {st.get('kills', 0)}",
                         f"Fallen in the Deep: {st.get('deaths', 0)}",
                         f"Skills learned: {sum((pl.get('skills') or {}).values())}"]
                for line in lines:
                    v.addWidget(QLabel(line))
                g = st.get("guardians") or []
                lab = QLabel("Guardians felled: " + (", ".join(g) if g else "none yet"))
                lab.setObjectName("dim")
                lab.setWordWrap(True)
                v.addWidget(lab)
            v.addStretch(1)
            grid.addWidget(box, 0, slot)
        lay.addLayout(grid)

    # ---- Options ------------------------------------------------------------------------------------------
    def _options(self, lay):
        S = self.shell
        h = QLabel("Options")
        h.setObjectName("h2")
        lay.addWidget(h)
        rows = [
            ("Music (ClaudeRPG's, made as it plays)", "On" if S.settings.get("music", True) else "Off",
             lambda: S.set_setting("music", not S.settings.get("music", True))),
            ("Music volume", f"{int(round(S.settings.get('music_volume', 0.8) * 100))}%",
             lambda: S.set_setting("music_volume", round((S.settings.get("music_volume", 0.8) + 0.2) % 1.2, 1) or 0.2)),
            ("Sound", "On" if S.settings.get("sound", True) else "Off",
             lambda: S.set_setting("sound", not S.settings.get("sound", True))),
            ("The townsfolk speak (a language model)", "On" if S.settings.get("speech", True) else "Off",
             lambda: S.set_setting("speech", not S.settings.get("speech", True))),
            ("Ground blending (the grounds meet softly, worn ways, dappled light)", "On" if S.settings.get("blend", True) else "Off",
             lambda: S.set_setting("blend", not S.settings.get("blend", True))),
            ("Mouse sensitivity", f"{S.settings.get('mouse', 1.0):.1f}",
             lambda: S.set_setting("mouse", round(S.settings.get("mouse", 1.0) + 0.25, 2) if S.settings.get("mouse", 1.0) < 2.0 else 0.5)),
        ]
        for label, value, fn in rows:
            r = QHBoxLayout()
            r.addWidget(QLabel(label), 1)
            b = QPushButton(value)
            b.setFixedWidth(120)
            b.clicked.connect(lambda _=False, fn=fn: (fn(), self.build()))
            r.addWidget(b)
            lay.addLayout(r)
        lab = QLabel("The computer's own mute silences both music and sound.")
        lab.setObjectName("dim")
        lay.addWidget(lab)
        lay.addStretch(1)

    def _keys(self, lay):
        h = QLabel("Keys")
        h.setObjectName("h2")
        lay.addWidget(h)
        grid = QGridLayout()
        keys = [("W A S D", "walk"), ("Shift", "run (and jump higher and further)"), ("Mouse", "look (click to take it, Esc gives it back)"), ("Left button", "cast"),
                ("Space", "jump"), ("F", "talk, open, take the stairs"), ("Q / E", "health / mana potion"),
                ("T", "read a Scroll of Return"), ("1-4, wheel", "change wand"), ("Tab", "the pack"), ("M", "the big map"),
                ("K", "the Calendar"), ("P", "auto-play on/off (or the button over the life orb)"), ("Esc", "the menu")]
        for i, (k, what) in enumerate(keys):
            a = QLabel(f"<b>{k}</b>")
            a.setTextFormat(Qt.RichText)
            grid.addWidget(a, i // 2, (i % 2) * 2)
            b = QLabel(what)
            b.setObjectName("dim")
            grid.addWidget(b, i // 2, (i % 2) * 2 + 1)
        lay.addLayout(grid)
        lay.addStretch(1)

    def _credits(self, lay):
        h = QLabel("Credits")
        h.setObjectName("h2")
        lay.addWidget(h)
        lines = [
            ("Claudenites 3-D", "a Claude Timeline game, made in Python, PySide6 and OpenGL"),
            ("Music", "ClaudeRPG's own engine and its worlds' music (by Kithylin, MIT), carried over note for note"),
            ("Figures", "KayKit Adventurers and Skeletons (Kay Lousberg, CC0); Quaternius' animals, monsters, dinosaurs (CC0)"),
            ("Plants and props", "Quaternius Ultimate Nature Pack; Kenney Pirate Kit (CC0)"),
            ("Stone", "ambientCG (CC0)"),
            ("Items", "Dungeon Crawl Stone Soup's tiles; Henrique Lazarini (7Soul1)'s 496 RPG icons (both CC0)"),
            ("The farm", "[LPC] Crops (bluecarrot16, Daniel Eddeland, Joshua Taylor, Richard Kettering; CC-BY-SA 3.0 / GPL 3.0); "
                         "Joshua Taylor's Fruit and Veggie Inventory (CC-BY-SA 3.0 / GPL 3.0); josehzz's Farming Crops (CC0)"),
            ("Painted art, the set pieces", "Claude and Magic's own"),
            ("Voices", "llama.cpp, with a model from the Timeline's LLM Models"),
        ]
        for who, what in lines:
            lab = QLabel(f"<b>{who}</b> - <span style='color:#B8A888'>{what}</span>")
            lab.setTextFormat(Qt.RichText)
            lab.setWordWrap(True)
            lay.addWidget(lab)
        lay.addStretch(1)

    # ---- keys -----------------------------------------------------------------------------------------------
    def old_code(self, k):
        self._code = (getattr(self, "_code", []) + [k])[-len(OLD_CODE):]
        if self._code == OLD_CODE:
            self._code = []
            RAINBOW["on"] = not RAINBOW["on"]
            self.shell.set_setting("konami", RAINBOW["on"])
            self.shell.sounds.play("levelup", 0.6)

    def eventFilter(self, obj, e):                         # (every key pressed while the title is up, wherever it goes)
        from PySide6.QtCore import QEvent
        if e.type() == QEvent.KeyPress and not e.isAutoRepeat() and self.isVisible():
            stamp = (e.timestamp(), e.key())
            if stamp != getattr(self, "_last_key", None):          # (the same press, passed up from widget to widget)
                self._last_key = stamp
                self.old_code(e.key())
        return False

    def keyPressEvent(self, e):
        k = e.key()
        if self.stack.currentWidget() is self.card:
            self.to_sheet()
            return
        if k == Qt.Key_Escape:
            self.to_card()
        elif k in (Qt.Key_1, Qt.Key_2, Qt.Key_3):
            self.tab = "play"
            self._choose(k - Qt.Key_1)
        elif k in (Qt.Key_Return, Qt.Key_Enter) and self.tab == "play":
            self.shell.play(self.chosen)
        elif k in (Qt.Key_Tab, Qt.Key_E, Qt.Key_Q):
            order = ["play", "records", "options", "keys", "credits"]
            i = order.index(self.tab) + (-1 if k == Qt.Key_Q else 1)
            self.set_tab(order[i % len(order)])

    def event(self, e):                                   # (Tab changes the page, not the focus)
        from PySide6.QtCore import QEvent
        if e.type() == QEvent.KeyPress and e.key() == Qt.Key_Tab:
            self.keyPressEvent(e)
            return True
        return super().event(e)


class _Logo(QWidget):
    def paintEvent(self, _e):
        p = QPainter(self)
        paint_logo(p, self.width() / 2, self.height() * 0.32, 0.62, time.perf_counter())
        p.end()


def _clear(layout):
    while layout.count():
        it = layout.takeAt(0)
        if it.widget():
            it.widget().deleteLater()
        elif it.layout():
            _clear(it.layout())
