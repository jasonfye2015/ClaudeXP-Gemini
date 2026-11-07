"""The panels laid over the view: the title (three save slots), the pause menu, Claude's pack (gear, wands and the
parts in them), the vendors, and the choices at the stairs and the Deep's mouth."""
from PySide6.QtCore import QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget

from shiboken6 import isValid

from ..game import data as D
from ..game import items as I
from ..game import shop

from .icons import icon, rarity_colour

CSS = """
QWidget#overlay { background: rgba(6, 6, 10, 165); }
QFrame#panel { background: #17130F; border: 2px solid #6A5638; border-radius: 10px; }
QFrame#card { background: #221C16; border: 1px solid #4A3C2A; border-radius: 8px; }
QLabel { color: #E8DCC0; font-family: Georgia; font-size: 14px; }
QLabel#title { color: #F2D68A; font-size: 34px; font-weight: bold; }
QLabel#heading { color: #F2D68A; font-size: 20px; font-weight: bold; }
QLabel#sub { color: #B8A888; font-size: 13px; font-style: italic; }
QLabel#small { color: #C8BCA0; font-size: 12px; font-family: 'Segoe UI'; }
QPushButton { background: #3A2E20; color: #F0E4C8; border: 1px solid #7A6440; border-radius: 6px; padding: 7px 16px;
              font-family: Georgia; font-size: 14px; }
QPushButton:hover { background: #4E3E2A; border-color: #C8A860; }
QPushButton:disabled { color: #7A7060; border-color: #4A4030; background: #2A2418; }
QPushButton#danger { background: #4A2018; border-color: #8A4030; }
QScrollArea { background: transparent; border: none; }
QScrollArea > QWidget > QWidget { background: transparent; }
QToolTip { background: #1E1912; color: #F0E4C8; border: 1px solid #8A7048; font-family: 'Segoe UI'; font-size: 12px; }
"""


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
    """An item's square: its picture in its rarity's frame (or an empty slot's word)."""

    def __init__(self, item=None, empty="", size=60, parent=None):
        super().__init__(parent)
        self.item, self.empty, self.size_ = item, empty, size
        self.selected = False
        self.hot = False
        self.setFixedSize(size, size)
        self.setCursor(Qt.PointingHandCursor)

    def sizeHint(self):
        return QSize(self.size_, self.size_)

    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(1, 1, self.width() - 2, self.height() - 2)
        p.setBrush(QColor("#2A221A") if not self.underMouse() else QColor("#3A3024"))
        frame = rarity_colour(self.item) if self.item else QColor("#4A3C2A")
        if self.hot:
            frame = QColor("#80E0FF")
        if self.selected:
            frame = QColor("#FFFFFF")
        p.setPen(QPen(frame, 2 if (self.item or self.hot) else 1))
        p.drawRoundedRect(r, 6, 6)
        if self.item:
            s = self.size_ - 10
            p.drawPixmap(5, 5, icon(self.item, s))
        elif self.empty:
            p.setPen(QColor("#7A6A50"))
            f = p.font()
            f.setPointSize(7)
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
    """The dimmed layer over the view, holding one panel in its middle."""

    def __init__(self, parent, panel):
        super().__init__(parent)
        self.setObjectName("overlay")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(CSS)
        lay = QVBoxLayout(self)
        lay.addStretch(1)
        row = QHBoxLayout()
        row.addStretch(1)
        row.addWidget(panel)
        row.addStretch(1)
        lay.addLayout(row)
        lay.addStretch(1)
        self.panel = panel


# ---- the title ------------------------------------------------------------------------------------------------
class TitlePanel(QFrame):
    def __init__(self, shell):
        super().__init__()
        self.setObjectName("panel")
        self.setFixedWidth(760)
        self.shell = shell
        lay = QVBoxLayout(self)
        lay.setContentsMargins(34, 28, 34, 28)
        lay.addWidget(_label("Claudenites 3-D", "title"))
        lay.addWidget(_label("Before he was anything else, Claude was an apprentice with a birch wand, and the forest "
                             "town of Thornwick sat over a hole nobody had seen the bottom of. A hundred floors down, "
                             "something waits. He means to see it.", "sub"))
        lay.addSpacing(12)
        for slot in range(3):
            lay.addWidget(self._card(slot))
        lay.addSpacing(10)
        lay.addWidget(_label("WASD move  -  mouse look  -  left button cast  -  Space jump  -  F talk / use  -  "
                             "Q / E potions  -  T Scroll of Return  -  1-4 or wheel: wands  -  Tab the pack  -  M map  -  "
                             "Esc menu", "small"))

    def _card(self, slot):
        card = QFrame()
        card.setObjectName("card")
        row = QHBoxLayout(card)
        row.setContentsMargins(16, 12, 16, 12)
        info = self.shell.saves.summary(slot)
        if info:
            text = (f"<b>Slot {slot + 1}</b> - Claude, level {info['level']}<br>"
                    f"<span style='color:#B8A888'>{info['gold']} gold - the Deep open to floor {info['floor']} - "
                    f"deepest {info['deepest']} - {info['kills']} slain, {info['deaths']} times fallen<br>"
                    f"saved {info['when']}</span>")
        else:
            text = f"<b>Slot {slot + 1}</b> - <span style='color:#B8A888'>empty</span>"
        lab = QLabel(text)
        lab.setTextFormat(Qt.RichText)
        row.addWidget(lab, 1)
        play = QPushButton("Continue" if info else "New game")
        play.clicked.connect(lambda: self.shell.play(slot))
        row.addWidget(play)
        if info:
            dele = QPushButton("Delete")
            dele.setObjectName("danger")
            dele.clicked.connect(lambda: self._confirm_delete(slot, dele))
            row.addWidget(dele)
        return card

    def _confirm_delete(self, slot, button):
        if button.text() == "Delete":
            button.setText("Sure?")
            return
        self.shell.saves.delete(slot)
        self.shell.show_title()


# ---- the menu -------------------------------------------------------------------------------------------------
class PausePanel(QFrame):
    def __init__(self, shell):
        super().__init__()
        self.setObjectName("panel")
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
        sp = shell.speech
        on = shell.settings.get("speech", True)
        talk = QPushButton(("The townsfolk speak: on" + (f" ({sp.model})" if on and sp.available() else
                            " (no language model found)" if on else "")) if on else "The townsfolk speak: off")
        talk.setToolTip("When on, Thornwick's people talk through a language model (llama.cpp, from the Timeline's "
                        "LLM Models): you can say anything to them at their stalls. Off, they have their own lines.")
        talk.clicked.connect(lambda: (shell.set_setting("speech", not on), shell.pause(), shell.pause()))
        lay.addWidget(talk)
        lay.addSpacing(8)
        lay.addWidget(_label("WASD move, mouse look, left button cast, Space jump, F talk or use, Q health potion, "
                             "E mana potion, T Scroll of Return, 1-4 or the wheel change wand, Tab the pack, M the map.",
                             "small"))


class ChoicePanel(QFrame):
    def __init__(self, title, text, choices, width=480):
        super().__init__()
        self.setObjectName("panel")
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
class PackPanel(QFrame):
    changed = Signal()

    def __init__(self, shell):
        super().__init__()
        self.setObjectName("panel")
        self.setFixedSize(1040, 660)
        self.shell = shell
        self.player = shell.view.game.player
        self.sel = None                         # ("pack", item) / ("gear", slot) / ("wand", i) / ("socket", i, k)
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
        grid = QGridLayout()
        grid.setSpacing(6)
        for k in range(48):
            it = P.inventory[k] if k < len(P.inventory) else None
            t = Tile(it, "")
            t.selected = bool(it) and self.sel == ("pack", it)
            if it:
                t.setToolTip(tooltip(it, P))
                t.clicked.connect(lambda _=False, it=it: self.pick(("pack", it)))
            grid.addWidget(t, k // 8, k % 8)
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
        it = self._selected_item()
        if it is None:
            hint = "Choose a thing to see it. Choose a wand part, then a wand's empty slot, to set it."
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
            for i in range(D.WAND_SLOTS):
                self._button(row, f"Ready as {i + 1}", lambda i=i: (P.ready_wand(it, i), self.pick(None)))
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


class VendorPanel(QFrame):
    def __init__(self, shell, key):
        super().__init__()
        self.setObjectName("panel")
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

