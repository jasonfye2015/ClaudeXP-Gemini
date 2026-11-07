"""Home's panels: the pack's tabs (Armor, Wands, Seeds, Raw, Cooked, Misc), the cabin's chest (the pack on one side,
the chest on the other), the farm sign (planting, watering, harvesting, the automation), the hearth (cooking what's
known, or trying something new) and the cookbook."""
import random
import time

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from ..game import data as D
from ..game import food as F
from ..game import items as I
from ..game.farm import UPGRADES
from . import theme

TABS = [("armor", "Armor"), ("wands", "Wands"), ("seeds", "Seeds"), ("raw", "Raw"), ("cooked", "Cooked"), ("misc", "Misc")]
MISC = [("health", "Health Potion", "potion"), ("mana", "Mana Potion", "potion"), ("return", "Scroll of Return", "scroll")]


def entries(items, larder, potions, tab):
    """What a tab shows: [(selection, tile item, count)]; selection is ("pack", item), ("larder", key), ("misc", kind)."""
    if tab == "armor":
        return [(("pack", it), it, 0) for it in items if it.get("type") == "gear"]
    if tab == "wands":
        return [(("pack", it), it, 0) for it in items if it.get("type") in ("wand", "part")]
    if tab in ("seeds", "raw", "cooked"):
        pre = {"seeds": "seed:", "raw": "raw:", "cooked": "cooked:"}[tab]
        keys = sorted(k for k, n in larder.items() if k.startswith(pre) and n > 0)
        return [(("larder", k), {"type": "larder", "key": k, "id": "l:" + k}, larder[k]) for k in keys]
    if potions is None:
        return []
    return [(("misc", k), {"type": kind, "kind": k, "id": "hud:" + k}, potions.get(k, 0)) for k, _n, kind in MISC
            if potions.get(k, 0) > 0]


def larder_lines(key):
    kind, _, k = key.partition(":")
    if kind == "seed":
        c = F.CROPS[k]
        return [f"Plant it at the farm sign. Grows in {c[1]:g} days, watered.", f"Gives {c[2][0]}-{c[2][1]} {c[0].lower()}s."]
    if kind == "raw":
        uses = sorted({F.RECIPES[r][0] for r in F.RECIPES if k in F.RECIPES[r][2]})
        out = ["Eaten raw, it does a little good."]
        return out + ([f"Cooks into: {', '.join(uses[:4])}{'...' if len(uses) > 4 else ''}"] if uses else [])
    r = F.RECIPES[k]
    return [r[5], ", ".join(F.buff_lines(r[3])) + f" - for {r[4]} hour{'s' if r[4] != 1 else ''} (real time)"]


def tab_row(current, choose, counts=None):
    row = QHBoxLayout()
    row.setSpacing(4)
    for key, name in TABS:
        b = QPushButton(name + (f" {counts[key]}" if counts and counts.get(key) else ""))
        b.setCheckable(True)
        b.setChecked(key == current)
        b.setStyleSheet("QPushButton { padding: 5px 10px; font-size: 13px; } QPushButton:checked { border-color: #FFD878;"
                        " color: #FFF0C0; background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #9A7438, stop:1 #4A3218); }")
        b.clicked.connect(lambda _=False, k=key: choose(k))
        row.addWidget(b)
    row.addStretch(1)
    return row


def grid(tiles_of, sel, pick, cols=8, rows=6, size=60):
    """A grid of tiles for entries (tiles_of), the chosen one marked; pick(selection) when one is clicked."""
    from .panels import Tile, tooltip
    g = QGridLayout()
    g.setSpacing(6)
    rows = max(rows, -(-len(tiles_of) // cols))
    for k in range(cols * rows):
        if k < len(tiles_of):
            selection, item, count = tiles_of[k]
            t = Tile(item, "", size)
            t.count = count
            t.selected = selection == sel
            t.setToolTip(_tip(item))
            t.clicked.connect(lambda _=False, s=selection: pick(s))
        else:
            t = Tile(None, "", size)
        g.addWidget(t, k // cols, k % cols)
    return g, tooltip


def _tip(item):
    from .panels import tooltip
    if item.get("type") == "larder":
        return f"<b style='color:#E8D8A0'>{F.name_of(item['key'])}</b><br>" + "<br>".join(larder_lines(item["key"]))
    if item.get("type") in ("potion", "scroll"):
        return f"<b>{next(n for k, n, _ in MISC if k == item['kind'])}</b>"
    return tooltip(item)


# ---- the cabin's chest ----------------------------------------------------------------------------------------
class StashPanel(theme.Ornate):
    def __init__(self, shell):
        super().__init__()
        self.setFixedSize(1120, 640)
        self.shell = shell
        self.P = shell.view.game.player
        self.tab = "armor"
        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(26, 20, 26, 20)
        self.build()

    def build(self):
        from .panels import _clear, _label
        _clear(self.root)
        P = self.P
        head = QHBoxLayout()
        head.addWidget(_label("Your chest", "heading"))
        head.addStretch(1)
        close = QPushButton("Close")
        close.clicked.connect(self.shell.close_panel)
        head.addWidget(close)
        self.root.addLayout(head)
        self.root.addWidget(_label("Click a thing to move it across (a stack moves whole). The chest keeps what the Deep "
                                   "can't take: it stays here whatever happens to Claude.", "sub"))
        self.root.addLayout(tab_row(self.tab, self._tab))
        body = QHBoxLayout()
        for side, items, larder, potions in (("pack", P.inventory, P.larder, None),
                                             ("stash", P.stash, P.stash_larder, None)):
            col = QVBoxLayout()
            n = len(items)
            col.addWidget(_label(("The pack" if side == "pack" else "The chest") + (f" ({n}/48)" if side == "pack" else f" ({n})"),
                                 "heading"))
            g, _ = grid(entries(items, larder, potions, self.tab), None, lambda s, side=side: self._move(side, s),
                        cols=8, rows=6, size=56)
            col.addLayout(g)
            col.addStretch(1)
            w = QWidget()
            w.setLayout(col)
            body.addWidget(w)
        self.root.addLayout(body, 1)

    def _tab(self, k):
        self.tab = k
        self.build()

    def _move(self, side, sel):
        P = self.P
        kind, what = sel
        if kind == "pack":
            src, dst = (P.inventory, P.stash) if side == "pack" else (P.stash, P.inventory)
            if dst is P.inventory and len(P.inventory) >= 48:
                return
            src.remove(what)
            dst.append(what)
        elif kind == "larder":
            src, dst = (P.larder, P.stash_larder) if side == "pack" else (P.stash_larder, P.larder)
            n = src.get(what, 0)
            F.add(src, what, -n)
            F.add(dst, what, n)
        self.shell.sounds.play("click", 0.5)
        self.build()


# ---- the farm sign ------------------------------------------------------------------------------------------
class FarmPanel(theme.Ornate):
    def __init__(self, shell):
        super().__init__()
        self.setFixedSize(1040, 660)
        self.shell = shell
        self.g = shell.view.game
        self.seed = None
        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(26, 20, 26, 20)
        self.build()

    def build(self):
        from .panels import Tile, _clear, _label
        _clear(self.root)
        g, P, farm = self.g, self.g.player, self.g.farm
        day = g.sky.day
        head = QHBoxLayout()
        head.addWidget(_label("The farm", "heading", False))
        head.addStretch(1)
        head.addWidget(_label(f"{P.gold} gold", "heading"))
        close = QPushButton("Close")
        close.clicked.connect(self.shell.close_panel)
        head.addWidget(close)
        self.root.addLayout(head)
        rain = g.sky.now()["kind"] in ("rain", "storm")
        self.root.addWidget(_label(f"Day {day + 1}, {g.sky.time_figures()}. A crop grows only on a day it's been watered"
                                   + (" - and the rain is watering it now." if rain else ".") +
                                   " Choose a seed, then a plot (or Plant all).", "sub"))
        body = QHBoxLayout()
        # the plots
        plots = QGridLayout()
        plots.setSpacing(6)
        for i in range(20):
            if i < len(farm.plots):
                p = farm.plots[i]
                if p:
                    st = farm.stage(i)
                    t = Tile({"type": "crop", "crop": p["crop"], "stage": st, "id": f"c{i}{p['crop']}{st}"}, "", 66)
                    t.count = 0
                    wet = p["watered"] == day
                    t.setToolTip(f"<b>{F.CROPS[p['crop']][0]}</b><br>{'Ripe - harvest it' if st == 4 else f'{int(p['growth'] * 100)}% grown'}"
                                 f"<br>{'Watered today' if wet else 'Dry: water it'}")
                    t.hot = st == 4
                    t.selected = not wet and st != 4
                else:
                    t = Tile(None, "empty", 66)
                    t.hot = self.seed is not None
                t.clicked.connect(lambda _=False, i=i: self._plot(i))
            else:
                t = Tile(None, "for later", 66)
                t.setEnabled(False)
            plots.addWidget(t, i // 5, i % 5)
        left = QVBoxLayout()
        left.addWidget(_label("The plots  (gold: ripe - blue: plant here - white: dry)", "small"))
        left.addLayout(plots)
        row = QHBoxLayout()
        for text, fn in (("Water all", self._water), ("Harvest all", self._harvest), ("Plant all", self._plant_all)):
            b = QPushButton(text)
            b.clicked.connect(fn)
            row.addWidget(b)
        left.addLayout(row)
        left.addStretch(1)
        lw = QWidget()
        lw.setLayout(left)
        body.addWidget(lw)
        # the seeds, and the automation
        right = QVBoxLayout()
        right.addWidget(_label("Your seeds", "heading"))
        seeds = entries([], P.larder, None, "seeds")
        if seeds:
            g2, _ = grid(seeds, ("larder", self.seed) if self.seed else None, self._choose, cols=6, rows=2, size=54)
            right.addLayout(g2)
        else:
            right.addWidget(_label("None. Monsters drop them, chests hold them, and Hesper sells them.", "sub"))
        right.addSpacing(8)
        right.addWidget(_label("Automation", "heading"))
        for key, (name, cost, what) in UPGRADES.items():
            r = QHBoxLayout()
            have = farm.upgrades.get(key) or (key == "expand" and len(farm.plots) >= 20)
            lab = QLabel(f"<b>{name}</b> - <span style='color:#C8B898'>{what}</span>")
            lab.setTextFormat(Qt.RichText)
            lab.setWordWrap(True)
            r.addWidget(lab, 1)
            b = QPushButton("Have it" if have and key != "expand" else ("Full" if have else f"{cost} gold"))
            b.setEnabled(not have and P.gold >= cost)
            b.clicked.connect(lambda _=False, k=key: (farm.buy(k, P), self.shell.sounds.play("coin", 0.6), self.build()))
            r.addWidget(b)
            right.addLayout(r)
        if farm.upgrades.get("farmhand"):
            r = QHBoxLayout()
            b = QPushButton("Replanting: on" if farm.replant else "Replanting: off")
            b.clicked.connect(lambda: (setattr(farm, "replant", not farm.replant), self.build()))
            r.addWidget(b)
            n = sum(farm.basket.values())
            take = QPushButton(f"Take the basket ({n})")
            take.setEnabled(n > 0)
            take.clicked.connect(self._basket)
            r.addWidget(take)
            right.addLayout(r)
            right.addWidget(_label("The farmhand plants from the seeds in your cabin's chest.", "small"))
        right.addStretch(1)
        rw = QWidget()
        rw.setLayout(right)
        body.addWidget(rw, 1)
        self.root.addLayout(body, 1)
        _ = Tile

    def _choose(self, sel):
        self.seed = sel[1] if self.seed != sel[1] else None
        self.build()

    def _plot(self, i):
        g, farm, P = self.g, self.g.farm, self.g.player
        if farm.ripe(i):
            self._take(farm.harvest(i, g.rng))
        elif farm.plots[i] is None and self.seed and P.larder.get(self.seed, 0) > 0:
            farm.plant(i, self.seed.split(":", 1)[1], g.sky.day)
            F.add(P.larder, self.seed, -1)
            if P.larder.get(self.seed, 0) <= 0:
                self.seed = None
            self.shell.sounds.play("click", 0.5)
        elif farm.plots[i]:
            farm.plots[i]["watered"] = g.sky.day
            self.shell.sounds.play("drink", 0.4)
        self.build()

    def _water(self):
        n = self.g.farm.water_all(self.g.sky.day)
        if n:
            self.shell.sounds.play("drink", 0.5)
        self.build()

    def _harvest(self):
        self._take(self.g.farm.harvest_all(self.g.rng))
        self.build()

    def _plant_all(self):
        g, farm, P = self.g, self.g.farm, self.g.player
        if not self.seed:
            return
        for i in range(len(farm.plots)):
            if farm.plots[i] is None and P.larder.get(self.seed, 0) > 0:
                farm.plant(i, self.seed.split(":", 1)[1], g.sky.day)
                F.add(P.larder, self.seed, -1)
        if P.larder.get(self.seed, 0) <= 0:
            self.seed = None
        self.shell.sounds.play("click", 0.5)
        self.build()

    def _basket(self):
        self._take(dict(self.g.farm.basket))
        self.g.farm.basket = {}
        self.build()

    def _take(self, got):
        P = self.g.player
        for k, n in got.items():
            F.add(P.larder, k, n)
        if got:
            self.shell.sounds.play("coin", 0.6)
            self.shell.view.toasts.append(("Harvested: " + ", ".join(f"{F.name_of(k)} x{n}" for k, n in got.items()),
                                           (0.8, 1.0, 0.6), time.perf_counter()))


# ---- the hearth, and the cookbook ---------------------------------------------------------------------------
class CookPanel(theme.Ornate):
    def __init__(self, shell):
        super().__init__()
        self.setFixedSize(1060, 660)
        self.shell = shell
        self.P = shell.view.game.player
        self.chosen = []
        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(26, 20, 26, 20)
        self.build()

    def build(self):
        from .panels import _clear, _label
        _clear(self.root)
        P = self.P
        head = QHBoxLayout()
        head.addWidget(_label("The hearth", "heading"))
        head.addStretch(1)
        book = QPushButton("The cookbook")
        book.clicked.connect(lambda: self.shell.set_panel(CookbookPanel(self.shell, back=CookPanel)))
        head.addWidget(book)
        close = QPushButton("Close")
        close.clicked.connect(self.shell.close_panel)
        head.addWidget(close)
        self.root.addLayout(head)
        self.root.addWidget(_label("The cauldron's on. Cook what you know, or put up to three things in and see what "
                                   "comes of it - a new dish goes in the cookbook.", "sub"))
        body = QHBoxLayout()
        # what's known
        known = QVBoxLayout()
        known.addWidget(_label(f"Known recipes ({len(P.cookbook)} of {len(F.RECIPES)})", "heading"))
        if not P.cookbook:
            known.addWidget(_label("None yet. Try something.", "sub"))
        for k in P.cookbook[:9]:
            r = F.RECIPES[k]
            row = QHBoxLayout()
            lab = QLabel(f"<b>{r[0]}</b> <span style='color:#B8A888'>({', '.join(F.name_of('raw:' + x) for x in r[2])})</span>")
            lab.setTextFormat(Qt.RichText)
            lab.setWordWrap(True)
            row.addWidget(lab, 1)
            b = QPushButton("Cook")
            b.setEnabled(F.has(P.larder, ["raw:" + x for x in r[2]]))
            b.clicked.connect(lambda _=False, k=k: self._cook(["raw:" + x for x in F.RECIPES[k][2]]))
            row.addWidget(b)
            known.addLayout(row)
        known.addStretch(1)
        kw = QWidget()
        kw.setLayout(known)
        body.addWidget(kw, 1)
        # trying something new
        new = QVBoxLayout()
        new.addWidget(_label("Your raw things", "heading"))
        raw = entries([], P.larder, None, "raw")
        g, _ = grid(raw, None, self._toggle, cols=6, rows=4, size=54)
        new.addLayout(g)
        new.addWidget(_label("In the pot: " + (", ".join(F.name_of(k) for k in self.chosen) or "nothing yet"), "small"))
        row = QHBoxLayout()
        b = QPushButton("Cook it")
        b.setEnabled(bool(self.chosen))
        b.clicked.connect(lambda: self._cook(list(self.chosen)))
        row.addWidget(b)
        c = QPushButton("Empty the pot")
        c.clicked.connect(lambda: (self.chosen.clear(), self.build()))
        row.addWidget(c)
        row.addStretch(1)
        new.addLayout(row)
        new.addStretch(1)
        nw = QWidget()
        nw.setLayout(new)
        body.addWidget(nw, 1)
        self.root.addLayout(body, 1)

    def _toggle(self, sel):
        key = sel[1]
        if len(self.chosen) < 3 and self.P.larder.get(key, 0) > self.chosen.count(key):
            self.chosen.append(key)
            self.shell.sounds.play("click", 0.4)
        self.build()

    def _cook(self, keys):
        P = self.P
        r = F.match([k.split(":", 1)[1] for k in keys])
        if r is None:
            self.shell.view.toasts.append(("It doesn't come together. (Nothing was wasted.)", (0.9, 0.75, 0.6), time.perf_counter()))
            self.chosen.clear()
            self.build()
            return
        if not F.has(P.larder, keys):
            return
        for k in keys:
            F.add(P.larder, k, -1)
        F.add(P.larder, "cooked:" + r, 1)
        new = r not in P.cookbook
        if new:
            P.cookbook.append(r)
        self.shell.sounds.play("levelup" if new else "drink", 0.5)
        self.shell.view.toasts.append((("A new dish for the cookbook: " if new else "Cooked: ") + F.RECIPES[r][0],
                                       (1.0, 0.85, 0.5), time.perf_counter()))
        self.chosen.clear()
        self.build()


class CookbookPanel(theme.Ornate):
    def __init__(self, shell, back=None):
        super().__init__()
        self.setFixedSize(1000, 660)
        from .panels import _label
        P = shell.view.game.player
        lay = QVBoxLayout(self)
        lay.setContentsMargins(26, 20, 26, 20)
        head = QHBoxLayout()
        head.addWidget(_label(f"The cookbook - {len(P.cookbook)} of {len(F.RECIPES)} found", "heading", False))
        head.addStretch(1)
        if back is not None:
            b = QPushButton("Back to the hearth")
            b.clicked.connect(lambda: shell.set_panel(back(shell)))
            head.addWidget(b)
        close = QPushButton("Close")
        close.clicked.connect(shell.close_panel)
        head.addWidget(close)
        lay.addLayout(head)
        g = QGridLayout()
        g.setSpacing(6)
        for i, (k, r) in enumerate(F.RECIPES.items()):
            if k in P.cookbook:
                text = (f"<b style='color:#F6D98A'>{r[0]}</b><br><span style='color:#C8B898'>"
                        f"{' + '.join(F.name_of('raw:' + x) for x in r[2])}</span><br>{', '.join(F.buff_lines(r[3]))}, {r[4]} h")
            else:
                text = f"<b style='color:#7A6A50'>? ? ?</b><br><span style='color:#7A6A50'>{len(r[2])} thing{'s' if len(r[2]) > 1 else ''} in the pot</span>"
            lab = QLabel(text)
            lab.setTextFormat(Qt.RichText)
            lab.setWordWrap(True)
            lab.setObjectName("card")
            lab.setStyleSheet("QLabel { background: rgba(30,23,16,200); border: 1px solid #4A3C2A; border-radius: 6px; padding: 5px; font-size: 12px; }")
            g.addWidget(lab, i // 4, i % 4)
        lay.addLayout(g)
        lay.addStretch(1)


_ = (random, D, I)
