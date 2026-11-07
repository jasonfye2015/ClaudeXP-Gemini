"""The panels laid over the view: the title (three save slots), the pause menu, Claude's pack (gear, wands and the
parts in them), the vendors, and the choices at the stairs and the Deep's mouth."""
import math

from PySide6.QtCore import QEasingCurve, QPointF, QRectF, QSize, Qt, QTimer, QVariantAnimation, Signal
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPen, QRadialGradient
from PySide6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget

from shiboken6 import isValid

from ..game import data as D
from ..game import items as I
from ..game import shop

from . import theme
from .icons import icon, rarity_colour

CSS = theme.CSS


def tooltip(it, player=None):
    name = I.item_name(it)
    col = rarity_colour(it).name()
    lines = []
    t = it.get("type")
    if t == "gear":
        lines = [f"{it['slot'].title()}, item level {it['level']}"] + I.gear_lines(it)
    elif t == "wand":
        b = D.WAND_BODIES[it["body"]]
        lines = [f"{b['slots']} slots, level {it.get('level', 1)}"] + I.wand_lines(it, player.bonus() if player else None)
        parts = [I.part_name(p) for p in it["parts"] if p]
        if parts:
            lines.append("Set with: " + ", ".join(parts))
    elif t == "part":
        e = I.part_effects(it)
        lines = [f"A wand part ({it['kind']})"]
        if it.get("element"):
            lines.append(f"Makes its bolts {D.ELEMENT_WORD[it['element']]}")
        words = {"damage": "{:+.0%} damage", "rate": "{:+.0%} shots a second", "speed": "{:+.0%} bolt speed",
                 "mana": "{:+.0%} mana a shot", "bullets": "+{:.0f} bolts a shot", "spread": "{:+.0f} degrees spread",
                 "homing": "Bolts seek their target", "bounce": "Bolts bounce {:.0f} times", "pierce": "Bolts pass through {:.0f}"}
        for k, v in e.items():
            if v:
                lines.append(words[k].format(v) if "{" in words[k] else words[k])
    lines.append(f"Worth {I.sell_price(it)} gold to a vendor")
    return f"<b style='color:{col}'>{name}</b><br>" + "<br>".join(lines)


class Tile(QPushButton):
    """An item's square: a sunken slot, the item's rarity glowing behind its picture, a light when the mouse is on it,
    a pulsing gold edge when chosen (and a pulsing blue one where a chosen thing can go)."""
    _pulse = None

    def __init__(self, item=None, empty="", size=60, parent=None):
        super().__init__(parent)
        self.item, self.empty, self.size_ = item, empty, size
        self.selected = False
        self.hot = False
        self.count = 0
        self.hover = 0.0
        self.setFixedSize(size, size)
        self.setCursor(Qt.PointingHandCursor)
        self.setAttribute(Qt.WA_Hover, True)
        self._anim = QVariantAnimation(self)
        self._anim.setDuration(140)
        self._anim.valueChanged.connect(self._set_hover)

    def _set_hover(self, v):
        self.hover = float(v)
        self.update()

    def enterEvent(self, e):
        self._anim.stop()
        self._anim.setStartValue(self.hover)
        self._anim.setEndValue(1.0)
        self._anim.start()
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._anim.stop()
        self._anim.setStartValue(self.hover)
        self._anim.setEndValue(0.0)
        self._anim.start()
        super().leaveEvent(e)

    def sizeHint(self):
        return QSize(self.size_, self.size_)

    def showEvent(self, e):
        if (self.selected or self.hot) and not getattr(self, "_t", None):
            self._t = QTimer(self)
            self._t.timeout.connect(self.update)
            self._t.start(50)
        super().showEvent(e)

    def paintEvent(self, _e):
        import time as _time
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(1.5, 1.5, self.width() - 3, self.height() - 3)
        g = QLinearGradient(r.topLeft(), r.bottomLeft())
        g.setColorAt(0, QColor(12, 9, 6))
        g.setColorAt(1, QColor(40, 31, 22))
        p.setPen(Qt.NoPen)
        p.setBrush(g)
        p.drawRoundedRect(r, 7, 7)
        rc = rarity_colour(self.item) if self.item else QColor(90, 72, 50)
        if self.item:                                           # (its rarity, glowing behind it)
            glow = QRadialGradient(r.center(), r.width() * 0.62)
            c0 = QColor(rc)
            c0.setAlpha(int(70 + 60 * self.hover))
            c1 = QColor(rc)
            c1.setAlpha(0)
            glow.setColorAt(0, c0)
            glow.setColorAt(1, c1)
            p.setBrush(glow)
            p.drawRoundedRect(r, 7, 7)
        if self.hover > 0:
            hl = QColor(255, 230, 170, int(40 * self.hover))
            p.setBrush(hl)
            p.drawRoundedRect(r, 7, 7)
        pulse = 0.5 + 0.5 * math.sin(_time.perf_counter() * 5)
        if self.selected:
            frame, width = QColor(255, 236, 170, int(170 + 85 * pulse)), 2.5
        elif self.hot:
            frame, width = QColor(110, 210, 255, int(140 + 115 * pulse)), 2.2
        elif self.item:
            frame, width = rc, 1.6
        else:
            frame, width = QColor(90, 72, 50), 1.0
        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(QColor(6, 4, 2, 200), 3))
        p.drawRoundedRect(r, 7, 7)
        p.setPen(QPen(frame, width))
        p.drawRoundedRect(r.adjusted(1, 1, -1, -1), 6, 6)
        if self.item:
            sz = self.size_ - 10
            lift = int(round(self.hover * 2))
            p.drawPixmap(5, 5 - lift, icon(self.item, sz))
            if self.count:
                from PySide6.QtGui import QFontMetricsF
                f = QFont(theme.BODY, 10, QFont.Bold)
                w = QFontMetricsF(f).horizontalAdvance(str(self.count))
                theme.outlined(p, self.width() - 7 - w, self.height() - 7, str(self.count), f, QColor(255, 240, 200))
        elif self.empty:
            p.setPen(QColor(150, 128, 96))
            f = QFont(theme.HEAD, 8)
            f.setItalic(True)
            p.setFont(f)
            p.drawText(r, Qt.AlignCenter | Qt.TextWordWrap, self.empty)
        p.end()


def _panel(width=None):
    f = QFrame()
    f.setObjectName("panel")
    if width:
        f.setFixedWidth(width)
    return f


def _label(text, name=None, wrap=True):
    lab = QLabel(text)
    if name:
        lab.setObjectName(name)
    lab.setWordWrap(wrap)
    return lab


class Overlay(QWidget):
    """The layer over the view: a vignette darkening in, and one panel in its middle, fading and rising in (or, full,
    a panel that is the whole screen: the title)."""

    def __init__(self, parent, panel, full=False):
        super().__init__(parent)
        self.setObjectName("overlayfull" if full else "overlay")
        self.setStyleSheet(CSS)
        self.panel = panel
        self.full = full
        self.dark = 0.0
        lay = QVBoxLayout(self)
        if full:
            lay.setContentsMargins(0, 0, 0, 0)
            lay.addWidget(panel)
            return
        lay.addStretch(1)
        row = QHBoxLayout()
        row.addStretch(1)
        row.addWidget(panel)
        row.addStretch(1)
        lay.addLayout(row)
        lay.addStretch(1)
        self._a = QVariantAnimation(self)
        self._a.setDuration(260)
        self._a.setStartValue(0.0)
        self._a.setEndValue(1.0)
        self._a.setEasingCurve(QEasingCurve.OutCubic)
        self._a.valueChanged.connect(self._step)
        self._a.start()
        theme.fade_in(panel, 240)

    def _step(self, v):
        self.dark = float(v)
        self.update()

    def paintEvent(self, e):
        if self.full:
            return
        p = QPainter(self)
        W, H = self.width(), self.height()
        g = QRadialGradient(QPointF(W / 2, H / 2), max(W, H) * 0.7)
        g.setColorAt(0, QColor(8, 6, 4, int(120 * self.dark)))
        g.setColorAt(1, QColor(0, 0, 0, int(225 * self.dark)))
        p.fillRect(self.rect(), g)
        p.end()


# ---- the menu -------------------------------------------------------------------------------------------------
class PausePanel(theme.Ornate):
    def __init__(self, shell):
        super().__init__()
        self.setFixedWidth(420)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(30, 24, 30, 24)
        lay.addWidget(_label("Paused", "heading"))
        g = shell.view.game
        st = g.player.stats
        lay.addWidget(_label(f"{st['kills']} slain, deepest floor {st['deepest']}, fallen {st['deaths']} times.", "sub"))
        for text, fn in (("Back to it", shell.close_panel), ("The pack", lambda: shell.open_dialog(("pack",))),
                         ("Save and go to the title", shell.quit_to_title)):
            b = QPushButton(text)
            b.clicked.connect(fn)
            lay.addWidget(b)
        for key, name in (("music", "Music"), ("sound", "Sound")):
            on_ = shell.settings.get(key, True)
            b = QPushButton(f"{name}: {'on' if on_ else 'off'}")
            b.clicked.connect(lambda _=False, k=key, v=on_: (shell.set_setting(k, not v), shell.pause(), shell.pause()))
            lay.addWidget(b)
        sp = shell.speech
        on = shell.settings.get("speech", True)
        talk = QPushButton(("The townsfolk speak: on" + (f" ({sp.model})" if on and sp.available() else
                            " (no language model found)" if on else "")) if on else "The townsfolk speak: off")
        talk.setToolTip("When on, Thornwick's people talk through a language model (llama.cpp, from the Timeline's "
                        "LLM Models): you can say anything to them at their stalls. Off, they have their own lines.")
        talk.clicked.connect(lambda: (shell.set_setting("speech", not on), shell.pause(), shell.pause()))
        lay.addWidget(talk)
        lay.addSpacing(8)
        lay.addWidget(_label("WASD move, Shift run, mouse look, left button cast, Space jump (higher running), F talk or use, Q health potion, "
                             "E mana potion, T Scroll of Return, 1-4 or the wheel change wand, Tab the pack, M the map.",
                             "small"))


class ChoicePanel(theme.Ornate):
    def __init__(self, title, text, choices, width=480):
        super().__init__()
        self.setFixedWidth(width)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(30, 24, 30, 24)
        lay.addWidget(_label(title, "heading"))
        if text:
            lay.addWidget(_label(text, "sub"))
        lay.addSpacing(6)
        for label, fn in choices:
            b = QPushButton(label)
            b.clicked.connect(fn)
            lay.addWidget(b)


# ---- the pack -------------------------------------------------------------------------------------------------
class PackPanel(theme.Ornate):
    changed = Signal()

    def __init__(self, shell):
        super().__init__()
        self.setFixedSize(1040, 660)
        self.shell = shell
        self.player = shell.view.game.player
        self.sel = None                         # ("pack", item) / ("gear", slot) / ("wand", i) / ("socket", i, k)
        self.tab = "armor"                      # / ("larder", key) / ("misc", kind)
        self.root = QHBoxLayout(self)
        self.root.setContentsMargins(22, 18, 22, 18)
        self.build()

    def build(self):
        while self.root.count():
            it = self.root.takeAt(0)
            if it.widget():
                it.widget().deleteLater()
            elif it.layout():
                _clear(it.layout())
        P = self.player
        left = QVBoxLayout()
        left.addWidget(_label("Worn", "heading"))
        grid = QGridLayout()
        for k, slot in enumerate(D.GEAR_SLOTS):
            t = Tile(P.gear[slot], slot.title())
            t.selected = self.sel == ("gear", slot)
            t.hot = bool(self.sel and self.sel[0] == "pack" and self.sel[1].get("slot") == slot and self.sel[1].get("type") == "gear")
            if P.gear[slot]:
                t.setToolTip(tooltip(P.gear[slot], P))
            t.clicked.connect(lambda _=False, s=slot: self.pick(("gear", s)))
            grid.addWidget(t, k // 3, k % 3)
        left.addLayout(grid)
        left.addSpacing(8)
        left.addWidget(_label("Wands (1-4)", "heading"))
        part_sel = self.sel and self.sel[0] == "pack" and self.sel[1].get("type") == "part"
        for i, w in enumerate(P.wands):
            row = QHBoxLayout()
            t = Tile(w, f"Wand {i + 1}")
            t.selected = self.sel == ("wand", i)
            t.hot = bool(self.sel and ((self.sel[0] == "pack" and self.sel[1].get("type") == "wand") or
                                       (self.sel[0] == "wand" and self.sel[1] != i)))
            if w:
                t.setToolTip(tooltip(w, P))
            t.clicked.connect(lambda _=False, i=i: self.pick(("wand", i)))
            row.addWidget(t)
            if w:
                for k, part in enumerate(w["parts"]):
                    s = Tile(part, "slot", 44)
                    s.hot = bool(part_sel)
                    s.selected = self.sel == ("socket", i, k)
                    if part:
                        s.setToolTip(tooltip(part, P))
                    s.clicked.connect(lambda _=False, i=i, k=k: self.pick(("socket", i, k)))
                    row.addWidget(s)
            star = QLabel("  active" if i == P.active and w else "")
            star.setObjectName("small")
            row.addWidget(star)
            row.addStretch(1)
            left.addLayout(row)
        left.addStretch(1)
        stats = QLabel(self._stats_text())
        stats.setObjectName("small")
        stats.setTextFormat(Qt.RichText)
        left.addWidget(stats)
        lw = QWidget()
        lw.setLayout(left)
        lw.setFixedWidth(430)
        self.root.addWidget(lw)
        # the pack, and what's chosen
        right = QVBoxLayout()
        head = QHBoxLayout()
        head.addWidget(_label(f"The pack ({len(P.inventory)}/48)", "heading"))
        head.addStretch(1)
        head.addWidget(_label(f"{P.gold} gold", "heading"))
        close = QPushButton("Close")
        close.clicked.connect(self.shell.close_panel)
        head.addWidget(close)
        right.addLayout(head)
        from . import home
        counts = {k: len(home.entries(P.inventory, P.larder, P.potions, k)) for k, _n in home.TABS}
        right.addLayout(home.tab_row(self.tab, self._tab, counts))
        shown = home.entries(P.inventory, P.larder, P.potions, self.tab)
        grid, _ = home.grid(shown, self.sel, self.pick, cols=8, rows=5, size=60)
        right.addLayout(grid)
        right.addWidget(self._detail())
        right.addStretch(1)
        rw = QWidget()
        rw.setLayout(right)
        self.root.addWidget(rw, 1)

    def _stats_text(self):
        P = self.player
        b = P.bonus()
        s = P.wand_stats()
        out = [f"<b>Claude</b>, level {P.level} - {P.xp}/{I.xp_to_next(P.level)} xp - {P.skill_points} skill points",
               f"Life {P.max_life()}, Mana {P.max_mana()} (+{P.mana_regen():.1f}/s), Armour {P.armour()}"]
        if s:
            out.append(f"Wand: {s['dps']:.0f} damage a second ({D.ELEMENT_WORD[s['element']]})")
        extra = [f"{D.AFFIXES[k][0].format(v=v)}" for k, v in b.items() if k in D.AFFIXES and k not in ("life", "mana", "armour")]
        if extra:
            out.append(", ".join(extra))
        return "<br>".join(out)

    def _detail(self):
        box = QFrame()
        box.setObjectName("card")
        lay = QVBoxLayout(box)
        P = self.player
        if self.sel and self.sel[0] in ("larder", "misc"):
            return self._food_detail(box, lay)
        it = self._selected_item()
        if it is None and self.tab in ("seeds", "raw", "cooked", "misc"):
            lay.addWidget(_label({"seeds": "Seeds go in the farm plot by the cabin: read the sign there.",
                                  "raw": "Raw things: eat one as it is, or cook it at the cabin's hearth into a meal.",
                                  "cooked": "A meal is good for hours (real hours): up to three at once.",
                                  "misc": "Potions and the Scroll of Return."}[self.tab], "sub"))
            if self.tab == "cooked":
                row = QHBoxLayout()
                self._button(row, "The cookbook", self._cookbook)
                row.addStretch(1)
                lay.addLayout(row)
            return box
        if it is None:
            hint = ("Choose a thing to see it. A wand, then a wand slot (1-4), readies it there; a ready wand, then "
                    "another slot, swaps them; a part, then a wand's empty socket, sets it; gear, then its slot, wears it.")
            if self.sel and self.sel[0] == "socket":
                hint = "An empty slot: choose a part in the pack, then this slot."
            lay.addWidget(_label(hint, "sub"))
            return box
        lab = QLabel(tooltip(it, P))
        lab.setTextFormat(Qt.RichText)
        lab.setWordWrap(True)
        lay.addWidget(lab)
        row = QHBoxLayout()
        kind = self.sel[0]
        t = it.get("type")
        if kind == "pack" and t == "gear":
            self._button(row, "Wear it", lambda: (P.equip(it), self.pick(None)))
        if kind == "pack" and t == "wand":
            row.addWidget(_label("Ready in slot", "small", False))
            for i in range(D.WAND_SLOTS):
                b = QPushButton(str(i + 1))
                b.setFixedWidth(40)
                b.setStyleSheet("padding: 6px 0px;")
                b.clicked.connect(lambda _=False, i=i: (P.ready_wand(it, i), setattr(P, "active", i), self.pick(None)))
                row.addWidget(b)
        if kind == "pack" and t == "part":
            row.addWidget(_label("Now choose a wand's slot (lit blue).", "small"))
        if kind == "pack":
            self._button(row, "Throw away", lambda: (P.inventory.remove(it), self.pick(None)), danger=True)
        if kind == "gear":
            self._button(row, "Take it off", lambda: (P.unequip(self.sel[1]), self.pick(None)))
        if kind == "wand":
            i = self.sel[1]
            if i != P.active:
                self._button(row, "Hold this one", lambda: (setattr(P, "active", i), self.pick(None)))
            if sum(1 for w in P.wands if w) > 1:
                self._button(row, "Put it in the pack", lambda: self._unready(i))
        if kind == "socket":
            i, k = self.sel[1], self.sel[2]
            self._button(row, "Take it out", lambda: (P.set_part(P.wands[i], k, None), self.pick(None)))
        row.addStretch(1)
        lay.addLayout(row)
        return box

    def _tab(self, k):
        self.tab = k
        self.sel = None if self.sel and self.sel[0] in ("pack", "larder", "misc") else self.sel
        self.build()

    def _cookbook(self):
        from .home import CookbookPanel
        self.shell.set_panel(CookbookPanel(self.shell))

    def _food_detail(self, box, lay):
        from . import home
        from ..game import food as F
        P = self.player
        kind, key = self.sel
        row = QHBoxLayout()
        if kind == "misc":
            lab = QLabel(f"<b>{D.CONSUMABLES[key]['name']}</b> x{P.potions.get(key, 0)}<br>{D.CONSUMABLES[key]['what']}")
            if key in ("health", "mana"):
                self._button(row, "Drink it", lambda: self._drink(key))
        else:
            lab = QLabel(f"<b style='color:#F6D98A'>{F.name_of(key)}</b> x{P.larder.get(key, 0)}<br>"
                         + "<br>".join(home.larder_lines(key)))
            if not key.startswith("seed:"):
                self._button(row, "Eat it", lambda: self._eat(key))
            if key.startswith("cooked:"):
                self._button(row, "The cookbook", self._cookbook)
        lab.setTextFormat(Qt.RichText)
        lab.setWordWrap(True)
        lay.addWidget(lab)
        row.addStretch(1)
        lay.addLayout(row)
        return box

    def _eat(self, key):
        import time as _t
        said = self.player.eat(key)
        if said:
            self.shell.sounds.play("drink", 0.5)
            self.shell.view.toasts.append((said, (0.9, 0.85, 0.6), _t.perf_counter()))
        if self.player.larder.get(key, 0) <= 0:
            self.sel = None
        self.build()

    def _drink(self, key):
        self.shell.view.game.drink(key)
        if self.player.potions.get(key, 0) <= 0:
            self.sel = None
        self.build()

    def _unready(self, i):
        P = self.player
        if len(P.inventory) < 48 and P.wands[i]:
            P.inventory.append(P.wands[i])
            P.wands[i] = None
            if P.active == i:
                P.active = next(k for k, w in enumerate(P.wands) if w)
        self.pick(None)

    def _button(self, row, text, fn, danger=False):
        b = QPushButton(text)
        if danger:
            b.setObjectName("danger")
        b.clicked.connect(fn)
        row.addWidget(b)

    def _selected_item(self):
        s, P = self.sel, self.player
        if not s:
            return None
        if s[0] == "pack":
            return s[1] if s[1] in P.inventory else None
        if s[0] == "gear":
            return P.gear.get(s[1])
        if s[0] == "wand":
            return P.wands[s[1]]
        if s[0] == "socket":
            w = P.wands[s[1]]
            return w["parts"][s[2]] if w else None
        return None

    def pick(self, sel):
        P = self.player
        cur = self.sel
        # a wand from the pack, then a wand's slot: ready it there (what was there goes back to the pack)
        if sel and sel[0] == "wand" and cur and cur[0] == "pack" and cur[1].get("type") == "wand":
            P.ready_wand(cur[1], sel[1])
            P.active = sel[1]
            self.shell.sounds.play("click", 0.5)
            self.sel = None
            self.build()
            return
        # one ready wand, then another slot: they change places (an empty slot: it moves there)
        if sel and sel[0] == "wand" and cur and cur[0] == "wand" and cur[1] != sel[1] and P.wands[cur[1]] is not None:
            a, b = cur[1], sel[1]
            P.wands[a], P.wands[b] = P.wands[b], P.wands[a]
            if P.active in (a, b):
                P.active = b if P.active == a else a
            if P.wands[P.active] is None:
                P.active = next(k for k, w in enumerate(P.wands) if w)
            self.shell.sounds.play("click", 0.5)
            self.sel = None
            self.build()
            return
        # a piece of gear from the pack, then its slot: wear it
        if sel and sel[0] == "gear" and cur and cur[0] == "pack" and cur[1].get("type") == "gear" and cur[1]["slot"] == sel[1]:
            P.equip(cur[1])
            self.shell.sounds.play("click", 0.5)
            self.sel = None
            self.build()
            return
        # a part chosen, then a slot: set it
        if sel and sel[0] == "socket" and self.sel and self.sel[0] == "pack" and self.sel[1].get("type") == "part":
            w = P.wands[sel[1]]
            if w is not None:
                P.set_part(w, sel[2], self.sel[1])
                self.shell.sounds.play("click", 0.5)
            sel = None
        self.sel = None if sel == self.sel else sel
        self.build()


def _clear(layout):
    while layout.count():
        it = layout.takeAt(0)
        if it.widget():
            it.widget().deleteLater()
        elif it.layout():
            _clear(it.layout())


# ---- the vendors ----------------------------------------------------------------------------------------------
GREETINGS = {
    "apothecary": "\"Red for the bleeding, blue for the empty head, and the scroll for when you've had enough. Pay first.\"",
    "wandwright": "\"A wand's only a stick until you set something in it. Mind the slots - more slots, more trouble.\"",
    "outfitter": "\"Cloth won't stop a claw, but the right cloth makes the claw think twice. Try it on.\"",
    "woodcutter": "\"Sit by the fire a while. The wood's quiet today.\"",
    "sage": "\"Three schools, child: Evocation, Warding and Arcana. What you learn of them stays learned, whatever the Deep does to you.\"",
}


class VendorPanel(theme.Ornate):
    def __init__(self, shell, key):
        super().__init__()
        self.setFixedSize(1040, 700 if key == "sage" else 640)
        self.shell, self.key = shell, key
        self.g = shell.view.game
        self.player = self.g.player
        self.v = D.VENDORS[key]
        self.stock = shell.stock(key)
        self.sel = None
        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(24, 18, 24, 18)
        self.build()

    def build(self):
        _clear(self.root)
        P = self.player
        head = QHBoxLayout()
        head.addWidget(_label(f"{self.v['name']}, {self.v['title']}", "heading"))
        head.addStretch(1)
        head.addWidget(_label(f"{P.gold} gold", "heading"))
        close = QPushButton("Goodbye")
        close.clicked.connect(self.shell.close_panel)
        head.addWidget(close)
        self.root.addLayout(head)
        self.greet = _label("", "sub")
        self.greet.setTextFormat(Qt.RichText)
        self.root.addWidget(self.greet)
        row = QHBoxLayout()
        self.entry = QLineEdit()
        self.entry.setStyleSheet("QLineEdit { background: #221C16; color: #F0E4C8; border: 1px solid #6A5638; "
                                 "border-radius: 5px; padding: 6px; font-family: Georgia; font-size: 14px; }")
        speaks = self.shell.speech.available()
        self.entry.setPlaceholderText(f"Say something to {self.v['name']}..." if speaks else
                                      f"(No language model in LLM Models: {self.v['name']} has only her own lines.)"
                                      if self.key in ("apothecary", "wandwright", "sage") else
                                      f"(No language model in LLM Models: {self.v['name']} has only his own lines.)")
        self.entry.setEnabled(speaks)
        self.entry.returnPressed.connect(self._say)
        row.addWidget(self.entry, 1)
        say = QPushButton("Say")
        say.setEnabled(speaks)
        say.clicked.connect(self._say)
        row.addWidget(say)
        self.root.addLayout(row)
        self.shell.greeting(self.key)
        self.show_talk()
        body = QHBoxLayout()
        # what's for sale
        sale = QVBoxLayout()
        if self.key != "woodcutter":
            sale.addWidget(_label("Her teaching" if self.key == "sage" else "For sale", "heading"))
        if self.key == "apothecary":
            for kind, c in D.CONSUMABLES.items():
                row = QHBoxLayout()
                t = Tile({"type": "potion" if kind != "return" else "scroll", "kind": kind, "name": c["name"], "id": kind}, "", 52)
                t.setToolTip(f"<b>{c['name']}</b><br>{c['what']}")
                row.addWidget(t)
                row.addWidget(_label(f"{c['name']} - {c['price']} gold<br><span style='color:#B8A888'>you have "
                                     f"{P.potions.get(kind, 0)}</span>"), 1)
                b = QPushButton("Buy")
                b.setEnabled(P.gold >= c["price"])
                b.clicked.connect(lambda _=False, k=kind: self._buy_consumable(k))
                row.addWidget(b)
                sale.addLayout(row)
            g = self.shell.view.game
            sale.addSpacing(6)
            sale.addWidget(_label("Seeds (click to buy one)", "heading"))
            from ..game import food as F
            seeds = QGridLayout()
            seeds.setSpacing(5)
            for k, crop in enumerate(shop.seed_stock(g.seed, g.visits, max(g.run_floor, P.stats["deepest"]))):
                key = f"seed:{crop}"
                t = Tile({"type": "larder", "key": key, "id": "l:" + key}, "", 46)
                t.count = P.larder.get(key, 0)
                c = F.CROPS[crop]
                t.setToolTip(f"<b>{c[0]} Seeds</b> - {c[4]} gold<br>Grows in {c[1]:g} days, watered.<br>You have {t.count}.")
                t.setEnabled(P.gold >= c[4])
                t.clicked.connect(lambda _=False, c=crop: (shop.buy_seed(P, c), self.shell.sounds.play("coin", 0.5), self.build()))
                seeds.addWidget(t, k // 5, k % 5)
            sale.addLayout(seeds)
        elif self.key == "sage":
            sale.addWidget(_label(f"Claude has {P.skill_points} skill points to spend.", None))
            from . import skills_panel
            sale.addWidget(skills_panel.SkillsWidget(self.shell, self.build))
        elif self.key == "woodcutter":
            sale.addWidget(_label("Rook sells nothing. He cuts wood, and talks to whoever comes by his fire.", "sub"))
        else:
            grid = QGridLayout()
            for k, it in enumerate(self.stock):
                t = Tile(it, "")
                t.selected = self.sel == ("buy", it)
                t.setToolTip(tooltip(it, P) + f"<br><b>Price: {I.price(it)} gold</b>")
                t.clicked.connect(lambda _=False, it=it: self.pick(("buy", it)))
                grid.addWidget(t, k // 5, k % 5)
            sale.addLayout(grid)
        sale.addStretch(1)
        sw = QWidget()
        sw.setLayout(sale)
        body.addWidget(sw, 1)
        # the pack, to sell from
        if self.key not in ("sage", "woodcutter"):
            pack = QVBoxLayout()
            pack.addWidget(_label(f"Sell from the pack ({len(P.inventory)}/48)", "heading"))
            grid = QGridLayout()
            grid.setSpacing(4)
            for k, it in enumerate(P.inventory):
                t = Tile(it, "", 50)
                t.selected = self.sel == ("sell", it)
                t.setToolTip(tooltip(it, P))
                t.clicked.connect(lambda _=False, it=it: self.pick(("sell", it)))
                grid.addWidget(t, k // 8, k % 8)
            pack.addLayout(grid)
            pack.addStretch(1)
            pw = QWidget()
            pw.setLayout(pack)
            body.addWidget(pw, 1)
        self.root.addLayout(body, 1)
        # the deal
        if self.sel:
            box = QFrame()
            box.setObjectName("card")
            row = QHBoxLayout(box)
            what, it = self.sel
            lab = QLabel(tooltip(it, P))
            lab.setTextFormat(Qt.RichText)
            lab.setWordWrap(True)
            row.addWidget(lab, 1)
            if what == "buy":
                b = QPushButton(f"Buy for {I.price(it)} gold")
                b.setEnabled(P.gold >= I.price(it) and len(P.inventory) < 48)
                b.clicked.connect(lambda: self._buy(it))
            else:
                b = QPushButton(f"Sell for {I.sell_price(it)} gold")
                b.clicked.connect(lambda: self._sell(it))
            row.addWidget(b)
            self.root.addWidget(box)

    def pick(self, sel):
        self.sel = None if sel == self.sel else sel
        self.build()

    def show_talk(self):
        """The last few things said at the stall."""
        if not isValid(self.greet):
            return
        lines = []
        for who, text in self.shell.talk.get(self.key, [])[-4:]:
            esc = text.replace("&", "&amp;").replace("<", "&lt;")
            lines.append(f"<span style='color:#9FB8D8'>Claude: {esc}</span>" if who == "claude" else f"\"{esc}\"")
        if self.shell.speech.busy:
            lines.append(f"<span style='color:#8A7A60'>{self.v['name']} thinks...</span>")
        self.greet.setText("<br>".join(lines) or GREETINGS[self.key])

    def _say(self):
        text = self.entry.text().strip()
        if not text:
            return
        self.entry.clear()
        self.shell.say_to(self.key, text)
        self.show_talk()

    def _buy(self, it):
        if shop.buy(self.player, it):
            self.stock.remove(it)
            self.shell.sounds.play("coin", 0.6)
            self.sel = None
            self.build()

    def _sell(self, it):
        if shop.sell(self.player, it):
            self.shell.sounds.play("coin", 0.6)
            self.sel = None
            self.build()

    def _buy_consumable(self, kind):
        if shop.buy_consumable(self.player, kind):
            self.shell.sounds.play("coin", 0.6)
            self.build()

