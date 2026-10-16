"""Claudeablo - a Diablo-style dungeon crawler for ClaudeXP's Games folder.

Pick a Warrior, Rogue or Sorcerer and fight down through fifty randomly built levels - the Cathedral, Catacombs,
Caves, Hell and the Abyss - to Diablo himself. Better weapons and armour drop as you go (white, magic blue and rare
yellow, most of the good ones unidentified); scrolls of Town Portal take you home to sell, buy and heal.

Mouse: left-click to walk, attack, open, pick up and talk (hold to keep walking); right-click casts your spell;
Shift+left-click attacks on the spot. Keys: 1-4 potions, I inventory, C character, S spells, Tab map, Alt item
names, F1 help, Esc menu. Saved in data/claudeablo/save.json.
"""
import json
import math
from pathlib import Path
import random
import time

from PySide6.QtCore import QPointF, QRect, QRectF, Qt, QTimer
from PySide6.QtGui import (QBrush, QColor, QFont, QFontMetrics, QLinearGradient, QPainter, QPen, QPolygonF,
                           QRadialGradient)
from PySide6.QtWidgets import QLineEdit, QWidget
from shiboken6 import isValid

from claudecore import host
from . import art
from . import dungeon as D
from . import items as I
from . import world as W

SAVE = host.saves("claudeablo") / "save.json"          # shared by every era
PANEL_H = 104
GOLD = QColor("#D8B060")
CELL = 30
EQUIP_LAYOUT = {"helm": (125, 54, 2, 2), "amulet": (195, 60, 1, 1), "weapon": (36, 110, 2, 3),
                "armor": (125, 120, 2, 3), "shield": (214, 110, 2, 3), "ring1": (66, 222, 1, 1),
                "ring2": (214, 222, 1, 1)}
SLOT_NAMES = {"helm": "Helm", "amulet": "Amulet", "weapon": "Weapon", "armor": "Armor", "shield": "Shield",
              "ring1": "Ring", "ring2": "Ring"}


def ablo_icon():
    return art.icon()


def _font(size, bold=False, family="Georgia"):
    f = QFont(family, size)
    f.setBold(bold)
    return f


class Game(QWidget):
    def __init__(self, desktop):
        super().__init__()
        self.desktop = desktop
        self.frame = None
        self.state = "title"
        self.world = None
        self.cls = "warrior"
        self.panels = set()               # "inv", "char", "spells", "map", "shop", "waystone", "help", "menu"
        self.held = None                  # an item on the mouse cursor
        self.held_from = None
        self.mouse = QPointF(0, 0)
        self.left_down = False
        self.walk_timer = 0.0
        self.hover = None
        self.shop = None                  # the NPC whose shop is open
        self.shop_tab = "buy"
        self.shop_scroll = 0
        self.shop_note = ""
        self.buttons = []
        self.item_hits = []               # (rect, kind, key) for tooltips and clicks in panels
        self.cache = {}
        self.last = time.monotonic()
        self.save_t = 0.0
        self.alt = False
        self.embers = [(random.random(), random.random(), random.random()) for _ in range(60)]
        self.name_edit = QLineEdit(self)
        self.name_edit.setMaxLength(14)
        self.name_edit.setText("Aidan")
        self.name_edit.setStyleSheet("QLineEdit { background: #1A1010; color: #E8D8B0; border: 2px solid #8A6A30; "
                                     "font-family: Georgia; font-size: 16px; padding: 3px 6px; }")
        self.name_edit.hide()
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMinimumSize(900, 640)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(16)

    # ---- loop ------------------------------------------------------------------------------------------------
    def _tick(self):
        now = time.monotonic()
        dt = min(0.05, now - self.last)
        self.last = now
        w = self.world
        if self.state == "play" and w is not None and "menu" not in self.panels and "help" not in self.panels:
            if self.left_down and self.held is None and not self._over_ui(self.mouse):
                self.walk_timer -= dt
                if self.walk_timer <= 0:
                    self.walk_timer = 0.22
                    self._click_world(self.mouse, hold=True)
            depth_before = w.depth
            w.update(dt)
            if w.talk_to is not None:
                self._open_shop(w.talk_to)
                w.talk_to = None
            if w.waystone_open:
                w.waystone_open = False
                self.panels.add("waystone")
            if w.depth != depth_before:
                self.panels.discard("shop")
                self.panels.discard("waystone")
                self.cache.pop("floors", None)
                self.save()
            self.save_t += dt
            if self.save_t > 60:
                self.save_t = 0
                self.save()
        self.update()

    # ---- saving ----------------------------------------------------------------------------------------------
    def save(self):
        if self.world is None:
            return
        try:
            SAVE.parent.mkdir(parents=True, exist_ok=True)
            tmp = SAVE.with_suffix(".tmp")
            tmp.write_text(json.dumps(self.world.to_json()), encoding="utf-8")
            tmp.replace(SAVE)
        except OSError:
            pass

    def shutdown(self):
        if self.state == "play":
            if self.held is not None:
                self.world.player.add_item(self.held) or self.world.drop_item(self.held)
                self.held = None
            self.save()
        self.timer.stop()

    def _continue(self):
        try:
            self.world = W.World.from_json(json.loads(SAVE.read_text(encoding="utf-8")))
        except Exception:
            return
        self.state = "play"
        self.setFocus()

    def _new_game(self):
        name = self.name_edit.text().strip() or "Hero"
        self.name_edit.hide()
        self.world = W.World(random.randint(1, 10 ** 8), W.Player(self.cls, name))
        self.world.say(f"Welcome to Haven, {name}. The cathedral to the north leads down into Hell. "
                       "Diablo waits at its bottom.", "#F0C060")
        self.world.say("Talk to the townsfolk (click them). Press F1 for help.", "#C8C0A0")
        self.state = "play"
        self.panels.clear()
        self.save()
        self.setFocus()

    # ---- coordinates -----------------------------------------------------------------------------------------------
    def _origin(self):
        p = self.world.player
        return self.width() / 2 - (p.x - p.y) * 32, (self.height() - PANEL_H) / 2 - (p.x + p.y) * 16

    def to_screen(self, x, y):
        ox, oy = self._origin()
        return ox + (x - y) * 32, oy + (x + y) * 16

    def to_tile(self, sx, sy):
        ox, oy = self._origin()
        mx, my = sx - ox, sy - oy
        return (mx / 32 + my / 16) / 2, (my / 16 - mx / 32) / 2

    def _over_ui(self, pos):
        if pos.y() > self.height() - PANEL_H:
            return True
        if ("char" in self.panels or "shop" in self.panels or "spells" in self.panels or "waystone" in self.panels) \
                and pos.x() < 330:
            return True
        if "inv" in self.panels and pos.x() > self.width() - 330:
            return True
        return False

    # ---- input -------------------------------------------------------------------------------------------------
    def keyPressEvent(self, e):
        k = e.key()
        if self.state == "create":
            if k in (Qt.Key_Return, Qt.Key_Enter):
                self._new_game()
            return
        if self.state != "play":
            return
        w = self.world
        if k == Qt.Key_Alt:
            self.alt = True
        if w.dead:
            return
        if Qt.Key_1 <= k <= Qt.Key_4:
            w.use_belt(k - Qt.Key_1)
        elif k == Qt.Key_I or k == Qt.Key_B:
            self._toggle("inv")
        elif k == Qt.Key_C:
            self._toggle("char")
        elif k == Qt.Key_S:
            self._toggle("spells")
        elif k == Qt.Key_Tab:
            self._toggle("map")
        elif k == Qt.Key_F1:
            self._toggle("help")
        elif k == Qt.Key_Space:
            self._close_all()
        elif k == Qt.Key_Escape:
            if self.panels - {"map"}:
                self._close_all()
            else:
                self._toggle("menu")

    def keyReleaseEvent(self, e):
        if e.key() == Qt.Key_Alt:
            self.alt = False

    def _toggle(self, name):
        if name in self.panels:
            self.panels.discard(name)
        else:
            if name in ("char", "spells", "shop", "waystone"):
                self.panels -= {"char", "spells", "shop", "waystone"}
            self.panels.add(name)

    def _close_all(self):
        if self.held is not None:
            if not self.world.player.add_item(self.held):
                self.world.drop_item(self.held)
            self.held = None
        self.panels.clear()
        self.shop = None

    def mouseMoveEvent(self, e):
        self.mouse = e.position()

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.left_down = False

    def wheelEvent(self, e):
        if "shop" in self.panels:
            self.shop_scroll = max(0, self.shop_scroll - (1 if e.angleDelta().y() > 0 else -1))

    def mousePressEvent(self, e):
        pos = e.position()
        self.mouse = pos
        self.setFocus()
        for rect, action in reversed(self.buttons):
            if rect.contains(pos):
                if e.button() == Qt.LeftButton:
                    action()
                return
        if self.state != "play":
            if self.state == "create":
                for rect, cls in getattr(self, "class_rects", []):
                    if rect.contains(pos):
                        self.cls = cls
            return
        w = self.world
        if w.dead or "menu" in self.panels or "help" in self.panels:
            return
        # panels first
        for rect, kind, key in reversed(self.item_hits):
            if rect.contains(pos):
                self._panel_click(kind, key, e.button(), e.modifiers())
                return
        if self._over_ui(pos):
            return
        if e.button() == Qt.RightButton:
            x, y = self.to_tile(pos.x(), pos.y())
            m = self._thing_at(pos)
            if isinstance(m, W.Monster):
                x, y = m.x, m.y
            w.cast(x, y)
            return
        if e.button() != Qt.LeftButton:
            return
        if self.held is not None:
            w.drop_item(self.held)
            self.held = None
            return
        self.left_down = True
        self.walk_timer = 0.3
        if e.modifiers() & Qt.ShiftModifier:
            self._attack_here(pos)
            return
        self._click_world(pos)

    def _attack_here(self, pos):
        w = self.world
        p = w.player
        x, y = self.to_tile(pos.x(), pos.y())
        m = self._thing_at(pos)
        target = m if isinstance(m, W.Monster) else None
        if target is None:
            near = [mm for mm in w.monsters if not mm.dead and math.hypot(mm.x - x, mm.y - y) < 1.2]
            target = near[0] if near else None
        if target is not None:
            w.attack(target)
        elif p.ranged and p.cool <= 0:
            w._face(x, y)
            p.cool, p.anim, p.pose = p.swing, 0.35, "attack"
            w.missiles.append(W.Missile("arrow", p.x, p.y, x - p.x, y - p.y, 13, w._roll_player_damage(), "player",
                                        radius=0.4, life=1.2))

    def _click_world(self, pos, hold=False):
        w = self.world
        thing = self._thing_at(pos)
        if isinstance(thing, W.Monster):
            w.attack(thing)
        elif thing is not None and not hold:
            w.interact(thing)
        elif not (hold and isinstance(w.player.target, W.Monster)):
            x, y = self.to_tile(pos.x(), pos.y())
            if w.level.floor(int(x), int(y)):
                w.move_to(int(x), int(y))

    def _thing_at(self, pos):
        """The monster, townsperson, item or object under the mouse."""
        w = self.world
        best, bd = None, 1e9
        for m in w.monsters:
            if m.dead or (int(m.x), int(m.y)) not in w.explored or not self._lit(m.x, m.y):
                continue
            sx, sy = self.to_screen(m.x, m.y)
            size = m.looks.get("size", 1.0) * (2.0 if m.kind == "diablo" else 1.0)
            r = QRectF(sx - 14 * size, sy - 56 * size, 28 * size, 58 * size)
            if r.contains(pos):
                d = abs(pos.x() - sx) + abs(pos.y() - (sy - 26 * size))
                if d < bd:
                    best, bd = m, d
        if best:
            return best
        for n in w.npcs:
            sx, sy = self.to_screen(n.x, n.y)
            if QRectF(sx - 14, sy - 58, 28, 60).contains(pos):
                return n
        for g in w.ground:
            sx, sy = self.to_screen(g.x, g.y)
            if QRectF(sx - 14, sy - 14, 28, 18).contains(pos) or (self.alt and self._label_rect(g).contains(pos)):
                return g
        tx, ty = self.to_tile(pos.x(), pos.y())
        for o in w.objects:
            if o.kind in ("chest", "barrel", "shrine") and o.opened:
                continue
            sx, sy = self.to_screen(o.x, o.y)
            if QRectF(sx - 18, sy - (52 if o.kind in ("portal", "waystone") else 30), 36,
                      (56 if o.kind in ("portal", "waystone") else 36)).contains(pos):
                return o
        return None

    def _label_rect(self, g):
        sx, sy = self.to_screen(g.x, g.y)
        name = self._ground_name(g)
        fm = QFontMetrics(QFont("Tahoma", 8, QFont.Bold))
        tw = fm.horizontalAdvance(name) + 10
        return QRectF(sx - tw / 2, sy - 34, tw, 15)

    def _ground_name(self, g):
        if g.item.get("base") == "Gold":
            return f"{g.item['gold']} gold"
        return I.name(g.item)

    # ---- panel clicks ----------------------------------------------------------------------------------------
    def _panel_click(self, kind, key, button, mods):
        w = self.world
        p = w.player
        if kind == "inv":
            it = p.inv[key]
            if button == Qt.RightButton:
                if self.held is None and it is not None:
                    if "shop" in self.panels and self.shop_tab == "sell":
                        self._sell(key)
                    else:
                        w.use_item(key)
                return
            if self.held is None:
                if it is not None:
                    if "shop" in self.panels and self.shop_tab == "sell":
                        self._sell(key)
                        return
                    self.held, p.inv[key] = it, None
            else:
                p.inv[key], self.held = self.held, it
        elif kind == "equip":
            cur = p.equip[key]
            if self.held is None:
                if cur is not None:
                    self.held, p.equip[key] = cur, None
                    p.recalc()
            else:
                s = I.slot(self.held)
                if s is None or (s != key and not (s == "ring" and key.startswith("ring"))):
                    w.say("That doesn't go there.", "#FF8080")
                    return
                if not p.can_equip(self.held):
                    w.say("You don't meet the requirements for that.", "#FF8080")
                    return
                p.equip[key], self.held = self.held, cur
                other = "shield" if key == "weapon" else "weapon" if key == "shield" else None
                if other and p.equip[other] and (I.two_handed(p.equip[key]) or I.two_handed(p.equip[other])):
                    loose = p.equip[other]
                    p.equip[other] = None
                    if self.held is None:
                        self.held = loose
                    elif not p.add_item(loose):
                        w.drop_item(loose)
                p.recalc()
        elif kind == "belt":
            it = p.belt[key]
            if button == Qt.RightButton and it is not None:
                w.use_belt(key)
            elif self.held is None and it is not None:
                self.held, p.belt[key] = it, None
            elif self.held is not None and I.kind(self.held) == "potion":
                one = dict(self.held)
                one["qty"] = 1
                if p.belt[key] is None:
                    p.belt[key] = one
                    self.held["qty"] = self.held.get("qty", 1) - 1
                    if self.held["qty"] <= 0:
                        self.held = None
        elif kind == "buy":
            note = w.buy(self.shop.role, key)
            self.shop_note = note or ""
        elif kind == "spell":
            p.active_spell = key
        elif kind == "stat":
            if p.points > 0:
                p.base[key] += 1
                p.points -= 1
                p.recalc()

    def _sell(self, idx):
        w = self.world
        it = w.player.inv[idx]
        if it is None or not self._buys(it):
            self.shop_note = "I've no use for that." if it else ""
            return
        price = w.sell(idx)
        self.shop_note = f"Sold for {price} gold."

    def _buys(self, it):
        role = self.shop.role if self.shop else None
        k = I.kind(it)
        if role == "smith":
            return k in ("dagger", "sword", "axe", "mace", "bow", "armor", "helm", "shield")
        if role == "witch":
            return k in ("staff", "ring", "amulet", "potion", "scroll", "book")
        if role == "healer":
            return k == "potion"
        return False

    def _open_shop(self, npc):
        w = self.world
        self.shop = npc
        self.shop_tab = "buy"
        self.shop_scroll = 0
        self.shop_note = ""
        self.panels -= {"char", "spells", "waystone"}
        self.panels.add("shop")
        self.panels.add("inv")
        if npc.role == "healer":
            w.heal()
            self.shop_note = "There, you are healed. Stay safe down there."

    # ---- painting --------------------------------------------------------------------------------------------
    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        self.buttons, self.item_hits = [], []
        if self.state == "play" and self.world:
            p.fillRect(self.rect(), QColor("#000000"))
            self._draw_world(p)
            self._draw_panel(p)
            self._draw_target_bar(p)
            self._draw_messages(p)
            if "map" in self.panels:
                self._draw_automap(p)
            if "char" in self.panels:
                self._draw_char(p)
            if "spells" in self.panels:
                self._draw_spells(p)
            if "shop" in self.panels:
                self._draw_shop(p)
            if "waystone" in self.panels:
                self._draw_waystone(p)
            if "inv" in self.panels:
                self._draw_inventory(p)
            if self.held is not None:
                p.drawPixmap(QPointF(self.mouse.x() - 15, self.mouse.y() - 15), self._icon(self.held))
            self._draw_tooltip(p)
            if self.world.dead:
                self._draw_death(p)
            elif self.world.won_at is not None and self.world.time - self.world.won_at < 12:
                self._draw_victory(p)
            if "help" in self.panels:
                self._draw_help(p)
            if "menu" in self.panels:
                self._draw_menu(p)
        elif self.state == "create":
            self._draw_create(p)
        else:
            self._draw_title(p)
        p.end()

    def _icon(self, it):
        key = ("icon", it["base"], it.get("rarity"))
        if key not in self.cache:
            k = "gold" if it.get("base") == "Gold" else I.kind(it)
            self.cache[key] = art.item_icon(k, it["base"], 30, it.get("rarity", "normal"))
        return self.cache[key]

    def _floor_pm(self, theme, v, lava=False):
        key = ("floor", theme, v, lava)
        if key not in self.cache:
            self.cache[key] = art.floor_tile(theme, v, lava)
        return self.cache[key]

    def _wall_pm(self, theme, style, v):
        key = ("wall", theme, style, v)
        if key not in self.cache:
            self.cache[key] = art.wall_block(theme, style, v)
        return self.cache[key]

    def _lit(self, x, y):
        w = self.world
        if w.depth == 0:
            return True
        p = w.player
        return math.hypot(x - p.x, y - p.y) <= p.light + 0.5

    def _bright(self, tx, ty):
        w = self.world
        if w.depth == 0:
            return 1.0
        p = w.player
        d = math.hypot(tx + 0.5 - p.x, ty + 0.5 - p.y)
        L = p.light
        if d <= L - 2.5:
            return 1.0
        if d <= L + 0.5:
            return 0.25 + 0.75 * (L + 0.5 - d) / 3.0
        return 0.18

    def _draw_world(self, p):
        w = self.world
        lv = w.level
        pl = w.player
        vw, vh = self.width(), self.height() - PANEL_H
        ptx, pty = int(pl.x), int(pl.y)
        R = 19
        tiles = []
        for ty in range(pty - R, pty + R + 1):
            for tx in range(ptx - R, ptx + R + 1):
                if not lv.inside(tx, ty) or (tx, ty) not in w.explored:
                    continue
                sx, sy = self.to_screen(tx + 0.5, ty + 0.5)
                if -70 < sx < vw + 70 and -40 < sy < vh + 120:
                    tiles.append((tx, ty, sx, sy))
        theme = lv.theme
        # floors
        for tx, ty, sx, sy in tiles:
            t = lv.grid[ty][tx]
            if t == D.WALL:
                if theme == "town" and lv.style.get((tx, ty)) in ("tree", "well"):
                    p.drawPixmap(QPointF(sx - 32, sy - 16), self._floor_pm(theme, (tx * 7 + ty * 13) % 3))
                continue
            b = 1.0 if t == D.LAVA else self._bright(tx, ty)
            p.setOpacity(b)
            p.drawPixmap(QPointF(sx - 32, sy - 16), self._floor_pm(theme, (tx * 7 + ty * 13) % 3, t == D.LAVA))
            dec = lv.decor.get((tx, ty))
            if dec and dec != "pentagram":
                p.save()
                p.translate(sx, sy)
                art.floor_decor(p, dec, random.Random(tx * 1000 + ty))
                p.restore()
        p.setOpacity(1.0)
        if theme == "sanctum":
            self._pentagram(p, lv)
        # walls, objects and creatures back to front
        items = []
        for tx, ty, sx, sy in tiles:
            if lv.grid[ty][tx] == D.WALL:
                # walls with no floor next to them are never seen from inside
                if theme != "town" and not any(lv.floor(tx + dx, ty + dy) or (lv.inside(tx + dx, ty + dy) and
                                                                           lv.grid[ty + dy][tx + dx] == D.LAVA)
                                               for dx in (-1, 0, 1) for dy in (-1, 0, 1)):
                    continue
                items.append((tx + ty + 1.0, 0, (tx, ty, sx, sy)))
        for o in w.objects:
            if (int(o.x), int(o.y)) in w.explored:
                items.append((o.x + o.y - 0.3 if o.kind.startswith("stairs") else o.x + o.y, 1, o))
        for g in w.ground:
            if (int(g.x), int(g.y)) in w.explored:
                items.append((g.x + g.y - 0.2, 2, g))
        for m in w.monsters:
            if (int(m.x), int(m.y)) in w.explored and self._lit(m.x, m.y):
                items.append((m.x + m.y - (0.5 if m.dead else 0), 3, m))
        for n in w.npcs:
            items.append((n.x + n.y, 3, n))
        items.append((pl.x + pl.y, 3, pl))
        for ms in w.missiles:
            items.append((ms.x + ms.y + 0.1, 4, ms))
        items.sort(key=lambda it: (it[0], it[1]))
        pdepth = pl.x + pl.y
        now = w.time
        self.hover = self._thing_at(self.mouse) if not self._over_ui(self.mouse) else None
        for _d, kind, thing in items:
            if kind == 0:
                tx, ty, sx, sy = thing
                pm, anchor = self._wall_pm(theme, lv.style.get((tx, ty)), (tx * 3 + ty * 5) % 4)
                op = self._bright(tx, ty)
                # walls between you and the camera go see-through
                if tx + ty + 1 > pdepth and abs((tx - ty) - (pl.x - pl.y)) < 3.2 and tx + ty + 1 - pdepth < 4.5 \
                        and lv.style.get((tx, ty)) != "tree":
                    op *= 0.32
                elif theme == "town" and lv.style.get((tx, ty)) in ("house", "church") and tx + ty > pdepth and \
                        abs((tx - ty) - (pl.x - pl.y)) < 2.5 and tx + ty - pdepth < 6:
                    op *= 0.4
                p.setOpacity(op)
                p.drawPixmap(QPointF(sx - anchor.x(), sy - anchor.y()), pm)
                p.setOpacity(1.0)
            elif kind == 1:
                sx, sy = self.to_screen(thing.x, thing.y)
                p.save()
                p.translate(sx, sy)
                if thing is self.hover:
                    p.setOpacity(1.0)
                art.draw_object(p, thing.kind, now, thing.opened, getattr(thing, "colour", None))
                p.restore()
            elif kind == 2:
                self._draw_ground(p, thing)
            elif kind == 3:
                self._draw_actor(p, thing)
            else:
                self._draw_missile(p, thing)
        self._draw_effects(p)
        if w.depth > 0:
            self._vignette(p)
        if self.alt:
            for g in w.ground:
                if (int(g.x), int(g.y)) in w.explored and self._lit(g.x, g.y):
                    self._ground_label(p, g)
        elif isinstance(self.hover, W.GroundItem):
            self._ground_label(p, self.hover)

    def _pentagram(self, p, lv):
        cx, cy = lv.places["diablo"][0] + 0.5, lv.places["diablo"][1] + 2.5
        pts = []
        for i in range(5):
            a = -math.pi / 2 + i * 4 * math.pi / 5
            pts.append(self.to_screen(cx + math.cos(a) * 4, cy + math.sin(a) * 4))
        p.setPen(QPen(QColor(200, 30, 20, 200), 3))
        p.setBrush(Qt.NoBrush)
        p.drawPolygon(QPolygonF([QPointF(*q) for q in pts]))
        sx, sy = self.to_screen(cx, cy)
        p.drawEllipse(QPointF(sx, sy), 4.3 * 32 * 1.41, 4.3 * 16 * 1.41)

    def _vignette(self, p):
        """Diablo's darkness: everything beyond your light fades to black."""
        pl = self.world.player
        sx, sy = self.to_screen(pl.x, pl.y)
        r = pl.light * 32 * 1.5
        g = QRadialGradient(QPointF(sx, sy - 20), r)
        g.setColorAt(0, QColor(0, 0, 0, 0))
        g.setColorAt(0.65, QColor(0, 0, 0, 30))
        g.setColorAt(1, QColor(0, 0, 0, 160))
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(g))
        p.drawRect(QRectF(0, 0, self.width(), self.height() - PANEL_H))

    def _draw_ground(self, p, g):
        sx, sy = self.to_screen(g.x, g.y)
        if not self._lit(g.x, g.y) and self.world.depth > 0:
            p.setOpacity(0.4)
        if g.item.get("base") == "Gold":
            p.save()
            p.translate(sx, sy)
            art.draw_object(p, "gold")
            p.restore()
        else:
            pm = self._icon(g.item)
            p.save()
            p.translate(sx, sy - 4)
            p.scale(0.7, 0.7)
            p.drawPixmap(QPointF(-15, -15), pm)
            p.restore()
            if g.item.get("rarity") in ("magic", "rare"):
                p.setPen(Qt.NoPen)
                c = QColor(I.colour(g.item))
                c.setAlpha(60)
                p.setBrush(c)
                p.drawEllipse(QPointF(sx, sy - 2), 12, 5)
        p.setOpacity(1.0)

    def _ground_label(self, p, g):
        r = self._label_rect(g)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(0, 0, 0, 180))
        p.drawRect(r)
        p.setFont(QFont("Tahoma", 8, QFont.Bold))
        p.setPen(QColor("#F8D040") if g.item.get("base") == "Gold" else QColor(I.colour(g.item)))
        p.drawText(r, Qt.AlignCenter, self._ground_name(g))

    def _draw_actor(self, p, a):
        sx, sy = self.to_screen(a.x, a.y)
        back = a.facing in (2, 3)
        mirror = a.facing in (1, 3)
        p.save()
        p.translate(sx, sy)
        if mirror:
            p.scale(-1, 1)
        if isinstance(a, W.Player):
            art.draw_figure(p, a.cls, "dead" if self.world.dead else a.pose, a.phase if a.pose != "attack"
                            else 1 - a.anim / 0.45, back, a.hurt, self._hero_look(a))
        elif isinstance(a, W.NPC):
            art.draw_figure(p, a.look, a.pose, a.phase, back)
        else:
            looks = dict(a.looks)
            if a.champion:
                looks.setdefault("body", None)
            hurt = a.hurt
            pose = "dead" if a.dead else a.pose
            if a.look == "bat":
                if not a.dead:
                    art.draw_bat(p, a.phase + self.world.time, hurt)
            elif a.look == "beast":
                art.draw_beast(p, a.phase, a.pose == "walk", hurt, dead=a.dead)
            else:
                if a.ai == "stealth" and not a.dead and math.hypot(a.x - self.world.player.x,
                                                                  a.y - self.world.player.y) > 3:
                    p.setOpacity(0.25)
                art.draw_figure(p, a.look, pose, a.phase if pose != "attack" else 0.6, back, hurt,
                                {k: v for k, v in looks.items() if v is not None})
            if a.champion and not a.dead:
                p.setOpacity(0.5)
                p.setPen(QPen(QColor("#6080FF"), 2))
                p.setBrush(Qt.NoBrush)
                p.drawEllipse(QPointF(0, 0), 16, 6)
            if a.boss and not a.dead:
                p.setOpacity(0.6)
                p.setPen(QPen(QColor("#F0C040"), 2))
                p.setBrush(Qt.NoBrush)
                s = a.looks.get("size", 1.0) * (2.0 if a.kind == "diablo" else 1.0)
                p.drawEllipse(QPointF(0, 0), 18 * s, 7 * s)
        p.restore()
        if a is self.hover and isinstance(a, W.NPC):
            self._name_over(p, sx, sy - 66, a.name, QColor("#E8D8B0"))

    def _hero_look(self, pl):
        e = pl.equip
        look = {}
        wpn = e["weapon"]
        look["weapon"] = {"dagger": "dagger", "sword": "sword", "axe": "axe", "mace": "mace", "bow": "bow",
                          "staff": "staff"}.get(I.kind(wpn), None) if wpn else None
        look["shield"] = e["shield"] is not None
        if e["shield"]:
            look["shield_colour"] = "#6A4A2A" if "Buckler" in e["shield"]["base"] or "Small" in e["shield"]["base"] \
                else "#8A8A94"
        arm = e["armor"]
        if arm:
            b = arm["base"]
            look["body"] = "#7A5A38" if "Leather" in b or "Quilted" in b or "Rags" in b else \
                "#9A9AA4" if "Mail" in b else "#C8CCD8" if "Plate" in b else look.get("body", None)
            if look["body"] is None:
                look.pop("body")
        if e["helm"]:
            look["head"] = "helm"
            look["helm_colour"] = "#C8C0A0" if "Crown" in e["helm"]["base"] else "#9A9AA4"
        if wpn and wpn.get("rarity") in ("magic", "rare"):
            look["weapon_colour"] = "#B8C8FF" if wpn["rarity"] == "magic" else "#F0E080"
        return look

    def _name_over(self, p, x, y, text, colour):
        p.setFont(QFont("Tahoma", 8, QFont.Bold))
        fm = QFontMetrics(p.font())
        tw = fm.horizontalAdvance(text) + 10
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(0, 0, 0, 170))
        p.drawRect(QRectF(x - tw / 2, y, tw, 15))
        p.setPen(colour)
        p.drawText(QRectF(x - tw / 2, y, tw, 15), Qt.AlignCenter, text)

    def _draw_missile(self, p, ms):
        sx, sy = self.to_screen(ms.x, ms.y)
        sy -= 24
        if ms.kind == "arrow":
            vx, vy = (ms.vx - ms.vy) * 32, (ms.vx + ms.vy) * 16
            n = math.hypot(vx, vy) or 1
            p.setPen(QPen(QColor("#E8DCC0"), 2))
            p.drawLine(QPointF(sx, sy), QPointF(sx - vx / n * 14, sy - vy / n * 14))
            return
        colour = {"firebolt": "#FF8020", "fireball": "#FF6010", "redbolt": "#FF3030"}.get(ms.kind, "#FF8020")
        r = 14 if ms.kind == "fireball" else 9
        g = QRadialGradient(QPointF(sx, sy), r)
        g.setColorAt(0, QColor("#FFF0B0"))
        g.setColorAt(0.4, QColor(colour))
        g.setColorAt(1, QColor(255, 80, 0, 0))
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(g))
        p.drawEllipse(QPointF(sx, sy), r, r)

    def _draw_effects(self, p):
        w = self.world
        for e in w.effects:
            age = (w.time - e["t0"]) / e["ttl"]
            if e["kind"] == "text":
                sx, sy = self.to_screen(e["x"], e["y"])
                p.setFont(QFont("Tahoma", 9, QFont.Bold))
                c = QColor(e["colour"])
                c.setAlphaF(max(0.0, 1 - age))
                p.setPen(QColor(0, 0, 0, int(200 * (1 - age))))
                p.drawText(QPointF(sx - 9, sy - 62 - age * 22), e["text"])
                p.setPen(c)
                p.drawText(QPointF(sx - 10, sy - 63 - age * 22), e["text"])
            elif e["kind"] in ("explosion", "flame"):
                sx, sy = self.to_screen(e["x"], e["y"])
                r = (e.get("r", 0.8) * 40) * (0.4 + age)
                g = QRadialGradient(QPointF(sx, sy - 12), r)
                g.setColorAt(0, QColor(255, 240, 160, int(230 * (1 - age))))
                g.setColorAt(0.5, QColor(255, 120, 20, int(200 * (1 - age))))
                g.setColorAt(1, QColor(120, 20, 0, 0))
                p.setPen(Qt.NoPen)
                p.setBrush(QBrush(g))
                p.drawEllipse(QPointF(sx, sy - 12), r, r * 0.75)
            elif e["kind"] == "bolt":
                pts = [QPointF(*self.to_screen(x, y)) - QPointF(0, 24) for x, y in e["pts"]]
                c = QColor(e["colour"])
                c.setAlphaF(max(0.0, 1 - age))
                p.setPen(QPen(c, 3))
                p.drawPolyline(QPolygonF(pts))
                p.setPen(QPen(QColor(255, 255, 255, int(220 * (1 - age))), 1))
                p.drawPolyline(QPolygonF(pts))
            elif e["kind"] == "nova":
                sx, sy = self.to_screen(e["x"], e["y"])
                r = e["r"] * 32 * age * 1.4
                c = QColor(e["colour"])
                c.setAlphaF(max(0.0, 1 - age))
                p.setPen(QPen(c, 6))
                p.setBrush(Qt.NoBrush)
                p.drawEllipse(QPointF(sx, sy - 10), r, r * 0.5)
            elif e["kind"] in ("heal", "mana", "flash", "level"):
                sx, sy = self.to_screen(e["x"], e["y"])
                c = QColor({"heal": "#FF6060", "mana": "#6080FF", "level": "#F0D060"}.get(e["kind"],
                                                                                       e.get("colour", "#FFFFFF")))
                c.setAlphaF(max(0.0, 0.8 * (1 - age)))
                g = QRadialGradient(QPointF(sx, sy - 30), 34)
                g.setColorAt(0, c)
                g.setColorAt(1, QColor(c.red(), c.green(), c.blue(), 0))
                p.setPen(Qt.NoPen)
                p.setBrush(QBrush(g))
                p.drawEllipse(QPointF(sx, sy - 30), 26, 44 if e["kind"] == "level" else 30)

    # ---- the control panel -------------------------------------------------------------------------------------
    def _draw_panel(self, p):
        w = self.world
        pl = w.player
        W_, H = self.width(), self.height()
        top = H - PANEL_H
        g = QLinearGradient(0, top, 0, H)
        g.setColorAt(0, QColor("#2A2218"))
        g.setColorAt(1, QColor("#0E0A06"))
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(g))
        p.drawRect(QRectF(0, top, W_, PANEL_H))
        p.setPen(QPen(GOLD, 2))
        p.drawLine(QPointF(0, top + 1), QPointF(W_, top + 1))
        # life and mana orbs
        self._orb(p, QPointF(70, top + 52), 44, pl.hp / max(1, pl.maxhp), QColor("#C01818"), f"{int(pl.hp)}/{pl.maxhp}")
        self._orb(p, QPointF(W_ - 70, top + 52), 44, pl.mana / max(1, pl.maxmana), QColor("#1838C8"),
                  f"{int(pl.mana)}/{pl.maxmana}")
        # experience bar
        xb = QRectF(140, top + 8, W_ - 280, 7)
        p.setPen(QPen(QColor("#5A4A30"), 1))
        p.setBrush(QColor("#100C08"))
        p.drawRect(xb)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#C8A040"))
        p.drawRect(QRectF(xb.x(), xb.y(), xb.width() * min(1.0, pl.xp / pl.next_level_xp()), xb.height()))
        # the belt
        bx = W_ / 2 - 2 * 40
        for i in range(4):
            r = QRectF(bx + i * 40, top + 26, 34, 34)
            p.setPen(QPen(QColor("#6A5A3A"), 1))
            p.setBrush(QColor("#140E08"))
            p.drawRect(r)
            if pl.belt[i]:
                p.drawPixmap(QPointF(r.x() + 2, r.y() + 2), self._icon(pl.belt[i]))
            p.setFont(QFont("Tahoma", 7, QFont.Bold))
            p.setPen(QColor("#C8B080"))
            p.drawText(QRectF(r.x() + 2, r.y() + 1, 10, 10), Qt.AlignLeft, str(i + 1))
            self.item_hits.append((r, "belt", i))
        # the active spell
        sr = QRectF(W_ / 2 + 100, top + 22, 42, 42)
        p.setPen(QPen(GOLD, 1.5))
        p.setBrush(QColor("#1A1008"))
        p.drawRect(sr)
        if pl.active_spell:
            self._spell_icon(p, sr.adjusted(4, 4, -4, -4), pl.active_spell)
        p.setFont(QFont("Tahoma", 7))
        p.setPen(QColor("#A89870"))
        p.drawText(QRectF(sr.x() - 10, sr.bottom() + 2, sr.width() + 20, 12), Qt.AlignCenter,
                   pl.active_spell or "no spell")
        self.buttons.append((sr, lambda: self._toggle("spells")))
        # buttons
        labels = [("CHAR", "char"), ("INV", "inv"), ("SPELLS", "spells"), ("MAP", "map"), ("MENU", "menu")]
        for i, (text, panel) in enumerate(labels):
            col, row = i % 3, i // 3
            r = QRectF(140 + col * 62, top + 26 + row * 30, 58, 24)
            on = panel in self.panels
            p.setPen(QPen(GOLD if on else QColor("#6A5A3A"), 1))
            p.setBrush(QColor("#3A2A18") if on else QColor("#1A140C"))
            p.drawRect(r)
            p.setFont(_font(8, True))
            p.setPen(QColor("#E8D8B0"))
            p.drawText(r, Qt.AlignCenter, text)
            self.buttons.append((r, lambda panel=panel: self._toggle(panel)))
        # where you are
        place = D.THEME_NAMES[w.level.theme] + ("" if w.depth == 0 else f" - level {w.depth}")
        p.setFont(_font(9, True))
        p.setPen(GOLD)
        p.drawText(QRectF(W_ / 2 + 150, top + 24, 200, 16), Qt.AlignLeft, place)
        p.setFont(QFont("Tahoma", 8))
        p.setPen(QColor("#C8B890"))
        p.drawText(QRectF(W_ / 2 + 150, top + 42, 220, 14), Qt.AlignLeft,
                   f"Level {pl.level} {pl.cls.title()}" + (f"  (+{pl.points} points)" if pl.points else ""))
        p.drawText(QRectF(W_ / 2 + 150, top + 58, 220, 14), Qt.AlignLeft, f"Gold: {pl.gold}")

    def _orb(self, p, c, r, frac, colour, text):
        p.setPen(QPen(QColor("#6A5030"), 3))
        p.setBrush(QColor("#0A0606"))
        p.drawEllipse(c, r, r)
        p.save()
        clip = QRectF(c.x() - r, c.y() + r - 2 * r * max(0.0, min(1.0, frac)), 2 * r, 2 * r)
        p.setClipRect(clip)
        g = QRadialGradient(QPointF(c.x() - r * 0.3, c.y() - r * 0.3), r * 1.3)
        g.setColorAt(0, colour.lighter(160))
        g.setColorAt(1, colour.darker(160))
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(g))
        p.drawEllipse(c, r - 3, r - 3)
        p.restore()
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(255, 255, 255, 40))
        p.drawEllipse(QPointF(c.x() - r * 0.35, c.y() - r * 0.45), r * 0.35, r * 0.2)
        if QRectF(c.x() - r, c.y() - r, 2 * r, 2 * r).contains(self.mouse):
            p.setFont(QFont("Tahoma", 8, QFont.Bold))
            p.setPen(QColor("white"))
            p.drawText(QRectF(c.x() - r, c.y() - 8, 2 * r, 16), Qt.AlignCenter, text)

    def _spell_icon(self, p, r, spell):
        colour = {"Firebolt": "#FF7020", "Fireball": "#FF4010", "Inferno": "#FF9020", "Healing": "#40D060",
                  "Lightning": "#A0C8FF", "Chain Lightning": "#C0D8FF", "Nova": "#80B0FF", "Teleport": "#C080FF",
                  "Town Portal": "#60A0FF"}.get(spell, "#FFFFFF")
        g = QRadialGradient(r.center(), r.width() / 2)
        g.setColorAt(0, QColor("#FFFFFF"))
        g.setColorAt(0.35, QColor(colour))
        g.setColorAt(1, QColor(colour).darker(300))
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(g))
        p.drawRect(r)
        p.setFont(_font(int(r.height() * 0.42), True))
        p.setPen(QColor(0, 0, 0, 170))
        p.drawText(r, Qt.AlignCenter, spell[0])

    def _draw_target_bar(self, p):
        h = self.hover
        target = h if isinstance(h, W.Monster) else self.world.player.target if isinstance(
            self.world.player.target, W.Monster) else None
        if target is None or target.dead:
            return
        W_ = self.width()
        r = QRectF(W_ / 2 - 150, 8, 300, 26)
        p.setPen(QPen(QColor("#6A5030"), 1))
        p.setBrush(QColor(10, 6, 4, 200))
        p.drawRect(r)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#8A1010"))
        p.drawRect(QRectF(r.x() + 2, r.y() + 2, (r.width() - 4) * max(0, target.hp / target.maxhp), r.height() - 4))
        p.setFont(_font(10, True))
        p.setPen(QColor("#F0C040") if target.boss else QColor("#8098FF") if target.champion else QColor("#E8E0D0"))
        p.drawText(r, Qt.AlignCenter, f"{target.name}  (level {target.mlevel})")

    def _draw_messages(self, p):
        w = self.world
        y = self.height() - PANEL_H - 24
        p.setFont(_font(10, True))
        for text, colour, t in reversed(w.messages):
            age = w.time - t
            if age > 7:
                continue
            c = QColor(colour)
            c.setAlphaF(max(0.0, min(1.0, (7 - age) / 2)))
            p.setPen(QColor(0, 0, 0, int(200 * c.alphaF())))
            p.drawText(QRectF(1, y + 1, self.width(), 20), Qt.AlignHCenter, text)
            p.setPen(c)
            p.drawText(QRectF(0, y, self.width(), 20), Qt.AlignHCenter, text)
            y -= 20

    # ---- panels -----------------------------------------------------------------------------------------------
    def _frame(self, p, r, title):
        g = QLinearGradient(r.topLeft(), r.bottomLeft())
        g.setColorAt(0, QColor(36, 28, 20, 245))
        g.setColorAt(1, QColor(16, 12, 8, 245))
        p.setPen(QPen(GOLD, 2))
        p.setBrush(QBrush(g))
        p.drawRect(r)
        p.setFont(_font(14, True))
        p.setPen(GOLD)
        p.drawText(QRectF(r.x(), r.y() + 6, r.width(), 24), Qt.AlignHCenter, title)

    def _draw_inventory(self, p):
        w = self.world
        pl = w.player
        r = QRectF(self.width() - 330, 0, 330, self.height() - PANEL_H)
        self._frame(p, r, "Inventory")
        x0, y0 = r.x(), r.y()
        for slot_name, (ex, ey, cw, ch) in EQUIP_LAYOUT.items():
            sr = QRectF(x0 + ex, y0 + ey, cw * CELL + 4, ch * CELL + 4)
            p.setPen(QPen(QColor("#6A5A3A"), 1))
            p.setBrush(QColor("#140E08"))
            p.drawRect(sr)
            it = pl.equip[slot_name]
            if it:
                if not pl.can_equip(it):
                    p.fillRect(sr.adjusted(1, 1, -1, -1), QColor(140, 20, 20, 90))
                pm = self._icon(it)
                scale = min(sr.width(), sr.height()) / 32
                p.save()
                p.translate(sr.center())
                p.scale(scale, scale)
                p.drawPixmap(QPointF(-15, -15), pm)
                p.restore()
            else:
                p.setFont(QFont("Tahoma", 7))
                p.setPen(QColor("#5A4A30"))
                p.drawText(sr, Qt.AlignCenter, SLOT_NAMES[slot_name])
            self.item_hits.append((sr, "equip", slot_name))
        gy = y0 + 290
        gx = x0 + 15
        for i in range(40):
            c, rr = i % 10, i // 10
            cr = QRectF(gx + c * CELL, gy + rr * CELL, CELL, CELL)
            p.setPen(QPen(QColor("#4A3A24"), 1))
            p.setBrush(QColor("#140E08"))
            p.drawRect(cr)
            it = pl.inv[i]
            if it:
                if it.get("rarity") in ("magic", "rare"):
                    col = QColor(I.colour(it))
                    col.setAlpha(45)
                    p.fillRect(cr.adjusted(1, 1, -1, -1), col)
                if I.slot(it) and not pl.can_equip(it):
                    p.fillRect(cr.adjusted(1, 1, -1, -1), QColor(140, 20, 20, 90))
                p.drawPixmap(QPointF(cr.x(), cr.y()), self._icon(it))
                if it.get("qty", 1) > 1:
                    p.setFont(QFont("Tahoma", 7, QFont.Bold))
                    p.setPen(QColor("white"))
                    p.drawText(cr.adjusted(0, 0, -2, -1), Qt.AlignRight | Qt.AlignBottom, str(it["qty"]))
            self.item_hits.append((cr, "inv", i))
        p.setFont(_font(11, True))
        p.setPen(QColor("#F8D040"))
        p.drawText(QRectF(gx, gy + 4 * CELL + 10, 300, 20), Qt.AlignLeft, f"Gold: {pl.gold}")
        p.setFont(QFont("Tahoma", 8))
        p.setPen(QColor("#A89870"))
        p.drawText(QRectF(gx, gy + 4 * CELL + 34, 300, 60), Qt.TextWordWrap,
                   "Click to pick up and place. Right-click to use, drink, read or put on. Click the ground while "
                   "holding something to drop it.")

    def _draw_char(self, p):
        pl = self.world.player
        r = QRectF(0, 0, 330, self.height() - PANEL_H)
        self._frame(p, r, pl.name)
        p.setFont(_font(10))
        p.setPen(QColor("#C8B890"))
        p.drawText(QRectF(0, 32, 330, 18), Qt.AlignHCenter, f"Level {pl.level} {pl.cls.title()}")
        y = 62
        p.setFont(QFont("Tahoma", 9))
        rows = [("Experience", f"{int(pl.xp)} / {pl.next_level_xp()}")]
        for label, val in rows:
            p.setPen(QColor("#A89870"))
            p.drawText(QRectF(20, y, 150, 18), Qt.AlignLeft, label)
            p.setPen(QColor("#E8E0D0"))
            p.drawText(QRectF(150, y, 160, 18), Qt.AlignRight, val)
            y += 22
        y += 6
        for key, label in (("str", "Strength"), ("dex", "Dexterity"), ("mag", "Magic"), ("vit", "Vitality")):
            total = {"str": pl.str_, "dex": pl.dex, "mag": pl.mag, "vit": pl.vit}[key]
            p.setPen(QColor("#D8C8A0"))
            p.setFont(_font(10, True))
            p.drawText(QRectF(20, y, 120, 22), Qt.AlignVCenter, label)
            p.setPen(QColor("#E8E0D0") if total == pl.base[key] else QColor("#8098FF"))
            p.drawText(QRectF(150, y, 90, 22), Qt.AlignVCenter | Qt.AlignRight, str(total))
            if pl.points:
                br = QRectF(255, y + 1, 22, 20)
                p.setPen(QPen(GOLD, 1))
                p.setBrush(QColor("#3A2A18"))
                p.drawRect(br)
                p.setPen(GOLD)
                p.drawText(br, Qt.AlignCenter, "+")
                self.item_hits.append((br, "stat", key))
            y += 28
        if pl.points:
            p.setFont(_font(10, True))
            p.setPen(QColor("#F0C060"))
            p.drawText(QRectF(20, y, 290, 20), Qt.AlignLeft, f"Points to spend: {pl.points}")
            y += 26
        y += 6
        p.setFont(QFont("Tahoma", 9))
        stats = [("Life", f"{int(pl.hp)} / {pl.maxhp}"), ("Mana", f"{int(pl.mana)} / {pl.maxmana}"),
                 ("Armor class", str(pl.ac)), ("Chance to hit", f"{pl.to_hit}%"),
                 ("Damage", f"{pl.dmg[0]}-{pl.dmg[1]}" + (f" +{pl.elem}" if pl.elem else "")),
                 ("Block", f"{pl.block}%"), ("Resist fire", f"{pl.res_fire}%"),
                 ("Resist lightning", f"{pl.res_light}%"), ("Light radius", str(pl.light)),
                 ("Deepest level", str(pl.max_depth))]
        for label, val in stats:
            p.setPen(QColor("#A89870"))
            p.drawText(QRectF(20, y, 150, 18), Qt.AlignLeft, label)
            p.setPen(QColor("#E8E0D0"))
            p.drawText(QRectF(150, y, 160, 18), Qt.AlignRight, val)
            y += 21
        if self.world.player.buffs:
            p.setPen(QColor("#80C0FF"))
            p.drawText(QRectF(20, y + 6, 290, 18), Qt.AlignLeft,
                       "Blessings: " + ", ".join(b.replace(" Shrine", "") for b in pl.buffs))

    def _draw_spells(self, p):
        pl = self.world.player
        r = QRectF(0, 0, 330, self.height() - PANEL_H)
        self._frame(p, r, "Spellbook")
        if not pl.spells:
            p.setFont(_font(10))
            p.setPen(QColor("#A89870"))
            p.drawText(r.adjusted(20, 50, -20, 0), Qt.TextWordWrap,
                       "You don't know any spells yet. Buy books from Adria the Witch, or find them in the dungeon, "
                       "and right-click them to read.")
            return
        y = 48
        for spell, lvl in sorted(pl.spells.items()):
            row = QRectF(16, y, 298, 46)
            on = spell == pl.active_spell
            p.setPen(QPen(GOLD if on else QColor("#4A3A24"), 1.5 if on else 1))
            p.setBrush(QColor("#2A2014") if on else QColor("#140E08"))
            p.drawRect(row)
            self._spell_icon(p, QRectF(row.x() + 5, row.y() + 5, 36, 36), spell)
            p.setFont(_font(10, True))
            p.setPen(QColor("#E8D8B0"))
            p.drawText(QRectF(row.x() + 50, row.y() + 4, 240, 18), Qt.AlignLeft,
                       f"{spell}  (level {lvl + pl.spell_bonus})")
            p.setFont(QFont("Tahoma", 8))
            p.setPen(QColor("#A89870"))
            p.drawText(QRectF(row.x() + 50, row.y() + 23, 240, 18), Qt.AlignLeft,
                       f"Mana {I.SPELLS[spell][0]} - {I.SPELLS[spell][3]}")
            self.item_hits.append((row, "spell", spell))
            y += 52
        p.setFont(QFont("Tahoma", 8))
        p.setPen(QColor("#A89870"))
        p.drawText(QRectF(16, y + 6, 298, 40), Qt.TextWordWrap, "Click a spell to ready it, then right-click to cast.")

    def _draw_shop(self, p):
        w = self.world
        npc = self.shop
        r = QRectF(0, 0, 330, self.height() - PANEL_H)
        self._frame(p, r, npc.name)
        greet = {"smith": "Weapons and armour, forged right here. Or sell me what you drag up from below.",
                 "witch": "Potions, scrolls, staves and spellbooks... and I pay for trinkets.",
                 "healer": "Come, let me tend your wounds.",
                 "elder": "Stay a while and listen. I can tell you what your finds truly are."}[npc.role]
        p.setFont(QFont("Tahoma", 8))
        p.setPen(QColor("#C8B890"))
        p.drawText(QRectF(16, 34, 298, 34), Qt.TextWordWrap, greet)
        if npc.role == "elder":
            self._draw_elder(p)
            return
        for i, tab in enumerate(("buy", "sell")):
            tr = QRectF(16 + i * 150, 70, 146, 24)
            on = self.shop_tab == tab
            p.setPen(QPen(GOLD if on else QColor("#4A3A24"), 1))
            p.setBrush(QColor("#2A2014") if on else QColor("#140E08"))
            p.drawRect(tr)
            p.setFont(_font(10, True))
            p.setPen(QColor("#E8D8B0"))
            p.drawText(tr, Qt.AlignCenter, tab.title())
            self.buttons.append((tr, lambda tab=tab: setattr(self, "shop_tab", tab)))
        if self.shop_tab == "sell":
            p.setFont(QFont("Tahoma", 9))
            p.setPen(QColor("#A89870"))
            p.drawText(QRectF(16, 104, 298, 80), Qt.TextWordWrap,
                       "Click an item in your inventory to sell it. Hover over it to see what I'll pay.")
        else:
            stock = w.shop_stock.get(npc.role, [])
            rows = (r.height() - 150) // 40
            self.shop_scroll = min(self.shop_scroll, max(0, len(stock) - int(rows)))
            y = 102
            for i, it in list(enumerate(stock))[self.shop_scroll:self.shop_scroll + int(rows)]:
                row = QRectF(16, y, 298, 38)
                p.setPen(QPen(QColor("#4A3A24"), 1))
                p.setBrush(QColor("#140E08"))
                p.drawRect(row)
                p.drawPixmap(QPointF(row.x() + 4, row.y() + 4), self._icon(it))
                p.setFont(QFont("Tahoma", 8, QFont.Bold))
                p.setPen(QColor(I.colour(it)))
                p.drawText(QRectF(row.x() + 40, row.y() + 3, 180, 16), Qt.AlignLeft,
                           QFontMetrics(p.font()).elidedText(I.name(it), Qt.ElideRight, 180))
                p.setFont(QFont("Tahoma", 8))
                lines = I.tooltip(it, w.player)
                p.setPen(QColor("#A89870"))
                p.drawText(QRectF(row.x() + 40, row.y() + 19, 180, 16), Qt.AlignLeft,
                           lines[1][0] if len(lines) > 1 else "")
                price = I.buy_price(it)
                p.setPen(QColor("#F8D040") if w.player.gold >= price else QColor("#A04040"))
                p.drawText(QRectF(row.right() - 80, row.y(), 74, 38), Qt.AlignRight | Qt.AlignVCenter,
                           f"{price} g")
                self.item_hits.append((row, "buy", i))
                y += 40
            if len(stock) > rows:
                p.setPen(QColor("#806A4A"))
                p.drawText(QRectF(16, y + 2, 298, 16), Qt.AlignHCenter, "(scroll for more)")
        if self.shop_note:
            p.setFont(_font(9, True))
            p.setPen(QColor("#F0C060"))
            p.drawText(QRectF(16, r.bottom() - 40, 298, 32), Qt.TextWordWrap | Qt.AlignHCenter, self.shop_note)

    def _draw_elder(self, p):
        w = self.world
        pl = w.player
        todo = len([it for it in pl.inv + list(pl.equip.values()) if it and not it.get("ident", True)])
        br = QRectF(30, 80, 270, 34)
        self._button(p, br, f"Identify everything ({todo * 100} gold)", self._identify)
        lore = self._lore()
        p.setFont(QFont("Georgia", 9))
        p.setPen(QColor("#C8B890"))
        p.drawText(QRectF(20, 130, 290, 300), Qt.TextWordWrap, lore)
        if self.shop_note:
            p.setFont(_font(9, True))
            p.setPen(QColor("#F0C060"))
            p.drawText(QRectF(16, self.height() - PANEL_H - 70, 298, 60), Qt.TextWordWrap | Qt.AlignHCenter,
                       self.shop_note)

    def _identify(self):
        self.shop_note = self.world.identify_all()

    def _lore(self):
        d = self.world.player.max_depth
        if self.world.flags.get("diablo_dead"):
            return ("You have done it. The Lord of Terror is cast down, and Haven sleeps soundly for the first time in "
                    "years. Yet the darkness below never truly empties... the dungeon still stirs, if you wish to "
                    "test yourself again.")
        if d < 5:
            return ("The cathedral was once the heart of Haven. When the Archbishop vanished, the dead began to walk "
                    "its halls. Something butchers travellers on the fifth level - be wary of it. Bring me anything "
                    "strange you find; I will tell you what it is.")
        if d < 15:
            return ("Beneath the cathedral lie the old catacombs, and beneath those a king who refused to stay "
                    "buried. Every fifth level holds a waystone's echo: touch the stone in town to return to the "
                    "depths you have reached.")
        if d < 30:
            return ("You have passed into the caves, where the earth itself bleeds fire. The demons there are "
                    "drawn by heat - fire will do little against them. Seek armour that resists flame.")
        if d < 50:
            return ("This is Hell itself. Black knights and pit lords guard the way, and witches with burning eyes. "
                    "At the fiftieth level, in a sanctum of blood and lava, Diablo waits. Go prepared: resist "
                    "fire and lightning, and carry many potions.")
        return "You stood before Diablo... and live to tell of it. Return, and finish him."

    def _draw_waystone(self, p):
        r = QRectF(0, 0, 330, self.height() - PANEL_H)
        self._frame(p, r, "The Waystone")
        p.setFont(QFont("Tahoma", 8))
        p.setPen(QColor("#C8B890"))
        p.drawText(QRectF(16, 34, 298, 34), Qt.TextWordWrap,
                   "The runes glow. Touch one to travel to a depth you have already reached.")
        y = 76
        for d in self.world.waystone_depths():
            br = QRectF(40, y, 250, 30)
            name = D.THEME_NAMES[D.theme_for(d)]
            self._button(p, br, f"Level {d} - {name}", lambda d=d: self._travel(d), small=True)
            y += 36

    def _travel(self, depth):
        self.panels.discard("waystone")
        self.world.enter(depth, "up")

    def _button(self, p, rect, text, action, small=False):
        hot = rect.contains(self.mouse)
        g = QLinearGradient(rect.topLeft(), rect.bottomLeft())
        g.setColorAt(0, QColor("#5A4228") if hot else QColor("#3A2A18"))
        g.setColorAt(1, QColor("#2A1C10") if hot else QColor("#1A120A"))
        p.setPen(QPen(GOLD, 1.5))
        p.setBrush(QBrush(g))
        p.drawRect(rect)
        p.setFont(_font(9 if small else 12, True))
        p.setPen(QColor("#F0E0B0") if hot else QColor("#D8C8A0"))
        p.drawText(rect, Qt.AlignCenter, text)
        self.buttons.append((rect, action))

    def _draw_automap(self, p):
        w = self.world
        lv = w.level
        pl = w.player
        cx, cy = self.width() / 2, (self.height() - PANEL_H) / 2
        k = 6
        p.setPen(QPen(QColor(200, 170, 110, 170), 1))
        for (x, y) in w.explored:
            if not lv.inside(x, y) or lv.grid[y][x] != D.WALL:
                continue
            if not any(lv.floor(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                continue
            sx = cx + ((x - pl.x) - (y - pl.y)) * k
            sy = cy + ((x - pl.x) + (y - pl.y)) * k / 2
            p.drawLine(QPointF(sx - k / 2, sy), QPointF(sx + k / 2, sy))
        for o in w.objects:
            if (int(o.x), int(o.y)) in w.explored and o.kind in ("stairs_down", "stairs_up", "portal", "waystone"):
                sx = cx + ((o.x - pl.x) - (o.y - pl.y)) * k
                sy = cy + ((o.x - pl.x) + (o.y - pl.y)) * k / 2
                p.setPen(Qt.NoPen)
                p.setBrush(QColor("#60C0FF") if o.kind in ("portal", "waystone") else QColor("#F0D060"))
                p.drawEllipse(QPointF(sx, sy), 4, 4)
        p.setBrush(QColor("#FF4040"))
        p.drawEllipse(QPointF(cx, cy), 3.5, 3.5)

    def _draw_tooltip(self, p):
        w = self.world
        pos = self.mouse
        it = None
        price = None
        for rect, kind, key in self.item_hits:
            if rect.contains(pos):
                if kind == "inv":
                    it = w.player.inv[key]
                    if it and "shop" in self.panels and self.shop_tab == "sell" and self._buys(it):
                        price = f"Sells for {I.sell_price(it) if it['rarity'] != 'supply' else max(1, I.SUPPLIES[it['base']][1] // 4)} gold"
                elif kind == "equip":
                    it = w.player.equip[key]
                elif kind == "belt":
                    it = w.player.belt[key]
                elif kind == "buy":
                    stock = w.shop_stock.get(self.shop.role, [])
                    it = stock[key] if key < len(stock) else None
                    if it:
                        price = f"Costs {I.buy_price(it)} gold"
                break
        if it is None and isinstance(self.hover, W.GroundItem) and self.hover.item.get("base") != "Gold":
            it = self.hover.item
        if it is None or self.held is not None:
            return
        lines = I.tooltip(it, w.player)
        if price:
            lines.append((price, "#F8D040"))
        fm = QFontMetrics(QFont("Tahoma", 9))
        bw = max(fm.horizontalAdvance(t) for t, _c in lines) + 20
        bh = len(lines) * 17 + 10
        x = min(self.width() - bw - 6, pos.x() + 16)
        y = min(self.height() - bh - 6, pos.y() + 12)
        p.setPen(QPen(QColor("#6A5A3A"), 1))
        p.setBrush(QColor(8, 6, 4, 235))
        p.drawRect(QRectF(x, y, bw, bh))
        for i, (text, colour) in enumerate(lines):
            p.setFont(QFont("Tahoma", 9, QFont.Bold if i == 0 else QFont.Normal))
            p.setPen(QColor(colour))
            p.drawText(QRectF(x, y + 5 + i * 17, bw, 17), Qt.AlignHCenter, text)

    # ---- overlays ----------------------------------------------------------------------------------------------
    def _draw_death(self, p):
        p.fillRect(self.rect(), QColor(60, 0, 0, 120))
        p.setFont(_font(36, True))
        p.setPen(QColor("#E02020"))
        p.drawText(QRect(0, self.height() // 2 - 110, self.width(), 60), Qt.AlignHCenter, "You have died")
        self._button(p, QRectF(self.width() / 2 - 140, self.height() / 2 - 30, 280, 44), "Restart in town",
                     self._revive)

    def _revive(self):
        self.held = None
        self.panels.clear()
        self.world.revive()
        self.save()

    def _draw_victory(self, p):
        a = min(1.0, (self.world.time - self.world.won_at) / 2)
        p.fillRect(self.rect(), QColor(0, 0, 0, int(150 * a)))
        p.setFont(_font(30, True))
        p.setPen(QColor(240, 192, 64, int(255 * a)))
        p.drawText(QRect(0, self.height() // 2 - 120, self.width(), 50), Qt.AlignHCenter, "Diablo is defeated!")
        p.setFont(_font(12))
        p.setPen(QColor(232, 216, 176, int(255 * a)))
        p.drawText(QRect(80, self.height() // 2 - 60, self.width() - 160, 90), Qt.AlignHCenter | Qt.TextWordWrap,
                   "The Lord of Terror falls, his soulstone cracked. Haven is saved - for now. "
                   "You may keep playing: the dungeon still waits below.")

    def _draw_menu(self, p):
        p.fillRect(self.rect(), QColor(0, 0, 0, 150))
        cx, cy = self.width() / 2, self.height() / 2
        p.setFont(_font(24, True))
        p.setPen(GOLD)
        p.drawText(QRect(0, int(cy) - 150, self.width(), 40), Qt.AlignHCenter, "Claudeablo")
        self._button(p, QRectF(cx - 130, cy - 80, 260, 40), "Back to the Game", lambda: self.panels.discard("menu"))
        self._button(p, QRectF(cx - 130, cy - 30, 260, 40), "Help", lambda: (self.panels.discard("menu"),
                                                                             self.panels.add("help")))
        self._button(p, QRectF(cx - 130, cy + 20, 260, 40), "Save and Quit to Title", self._quit_title)

    def _quit_title(self):
        self._close_all()
        self.save()
        self.world = None
        self.state = "title"

    def _draw_help(self, p):
        r = QRectF(self.width() / 2 - 330, 40, 660, self.height() - PANEL_H - 70)
        self._frame(p, r, "How to Play")
        text = (
            "Fight your way down fifty levels to Diablo. Gold, weapons, armour, potions and spellbooks drop as you go.\n\n"
            "MOUSE  Left-click to walk (hold to keep walking), attack, open chests and barrels, pick things up and "
            "talk. Right-click casts your ready spell where you point. Shift+left-click attacks without moving.\n\n"
            "KEYS  1-4 drink from your belt.  I inventory.  C character.  S spellbook.  Tab map.  Alt shows the "
            "names of everything on the ground.  Space closes panels.  Esc menu.\n\n"
            "LOOT  White items are plain, blue are magic, yellow are rare. Magic and rare items drop unidentified - "
            "their powers work, but read a Scroll of Identify or visit Deckard to see them. Red means you don't meet "
            "the requirements yet.\n\n"
            "LEVELS  Each level up gives 5 points - press C and click +. Strength helps swords, axes and maces; "
            "Dexterity bows and accuracy; Magic mana and spells; Vitality life.\n\n"
            "TOWN  Read a Scroll of Town Portal to open a portal home - it stays open so you can step back down. "
            "Griswald buys and sells arms and armour, Adria potions, scrolls, staves, jewellery and spellbooks, "
            "Pepin heals you for free, Deckard identifies. The waystone takes you to levels you've reached (every "
            "fifth). Shrines in the dungeon grant blessings - and every tenth level or so, something big is waiting.")
        p.setFont(QFont("Tahoma", 9))
        p.setPen(QColor("#E8D8B8"))
        p.drawText(r.adjusted(26, 44, -26, -50), Qt.TextWordWrap, text)
        self._button(p, QRectF(r.center().x() - 70, r.bottom() - 46, 140, 34), "Close",
                     lambda: self.panels.discard("help"), True)

    # ---- title and class screens -------------------------------------------------------------------------------
    def _hellfire(self, p):
        w, h = self.width(), self.height()
        g = QLinearGradient(0, 0, 0, h)
        g.setColorAt(0, QColor("#0A0202"))
        g.setColorAt(0.7, QColor("#2A0604"))
        g.setColorAt(1, QColor("#5A1006"))
        p.fillRect(self.rect(), QBrush(g))
        t = time.monotonic()
        p.setPen(Qt.NoPen)
        for fx, fy, sp in self.embers:
            x = (fx * w + math.sin(t + sp * 6) * 20) % w
            y = h - ((fy * h + t * (30 + sp * 60)) % h)
            a = int(200 * (y / h))
            p.setBrush(QColor(255, 140 + int(80 * sp), 40, a))
            p.drawEllipse(QPointF(x, y), 1.5 + sp * 1.5, 1.5 + sp * 1.5)
        fl = QRadialGradient(QPointF(w / 2, h + 80), w * 0.6)
        fl.setColorAt(0, QColor(255, 120, 30, 160))
        fl.setColorAt(1, QColor(255, 60, 10, 0))
        p.setBrush(QBrush(fl))
        p.drawRect(self.rect())

    def _logo(self, p, y):
        w = self.width()
        f = _font(54, True, "Times New Roman")
        p.setFont(f)
        r = QRect(0, int(y), w, 80)
        p.setPen(QColor(0, 0, 0, 200))
        p.drawText(r.translated(4, 4), Qt.AlignHCenter, "CLAUDEABLO")
        g = QLinearGradient(0, y, 0, y + 70)
        g.setColorAt(0, QColor("#FFE8A0"))
        g.setColorAt(0.5, QColor("#E08020"))
        g.setColorAt(1, QColor("#8A1A08"))
        p.setPen(QPen(QBrush(g), 1))
        p.drawText(r, Qt.AlignHCenter, "CLAUDEABLO")
        p.setFont(_font(12, False))
        p.setPen(QColor("#C8A070"))
        p.drawText(QRect(0, int(y) + 76, w, 24), Qt.AlignHCenter, "Fifty levels down, the Lord of Terror waits.")

    def _title_picture(self):
        """assets/claudeablo/title.jpg - the Claudeablo logo, scaled to the window (cached)."""
        key = ("title", self.width(), self.height())
        if key not in self.cache:
            from PySide6.QtGui import QPixmap
            pm = QPixmap(str(Path(__file__).resolve().parent / "assets" / "title.jpg"))
            self.cache[key] = None if pm.isNull() else pm.scaled(self.width(), self.height(), Qt.KeepAspectRatio,
                                                                  Qt.SmoothTransformation)
        return self.cache[key]

    def _draw_title(self, p):
        w, h = self.width(), self.height()
        pic = self._title_picture()
        if pic is not None:
            p.fillRect(self.rect(), QColor("#000000"))
            t = time.monotonic()
            p.setPen(Qt.NoPen)
            for fx, fy, sp in self.embers:                  # embers drifting up behind the logo
                x = (fx * w + math.sin(t + sp * 6) * 20) % w
                y = h - ((fy * h + t * (25 + sp * 50)) % h)
                p.setBrush(QColor(255, 120 + int(80 * sp), 30, int(150 * (y / h))))
                p.drawEllipse(QPointF(x, y), 1.2 + sp * 1.4, 1.2 + sp * 1.4)
            p.drawPixmap((w - pic.width()) // 2, (h - pic.height()) // 2, pic)
            top = h * 0.74
        else:
            self._hellfire(p)
            self._logo(p, h * 0.12)
            p.save()
            p.translate(w / 2, h * 0.62)
            art.draw_figure(p, "diablo", "stand", time.monotonic() * 1.5)
            p.restore()
            top = h * 0.68
        labels = []
        if SAVE.exists():
            labels.append(("Continue", self._continue))
        labels += [("New Hero", self._to_create), ("Quit", lambda: self.frame.request_close() if self.frame else None)]
        for i, (text, act) in enumerate(labels):
            self._button(p, QRectF(w / 2 - 120, top + i * 50, 240, 40), text, act)

    def _to_create(self):
        self.state = "create"
        self.name_edit.show()
        self.name_edit.setFocus()
        self.name_edit.selectAll()

    def _draw_create(self, p):
        self._hellfire(p)
        w, h = self.width(), self.height()
        p.setFont(_font(28, True))
        p.setPen(GOLD)
        p.drawText(QRect(0, 30, w, 44), Qt.AlignHCenter, "Choose Your Hero")
        p.setFont(_font(11))
        p.setPen(QColor("#C8B890"))
        p.drawText(QRect(0, 86, w, 20), Qt.AlignHCenter, "Name:")
        self.name_edit.setGeometry(int(w / 2 - 120), 108, 240, 34)
        info = {"warrior": ("Warrior", "A master of sword and shield. Tough, strong, and at home in the thick of "
                                       "the fight."),
                "rogue": ("Rogue", "A sharp-eyed archer who strikes from a distance before the enemy can close."),
                "sorcerer": ("Sorcerer", "A scholar of the arcane, armed with fire and lightning. Frail, but deadly "
                                         "from afar. Starts knowing Firebolt.")}
        cw = 240
        x0 = w / 2 - cw * 1.5 - 10
        self.class_rects = []
        for i, cls in enumerate(("warrior", "rogue", "sorcerer")):
            r = QRectF(x0 + i * (cw + 10), 170, cw, 330)
            on = cls == self.cls
            p.setPen(QPen(GOLD if on else QColor("#5A4228"), 3 if on else 1))
            p.setBrush(QColor(30, 18, 10, 220) if on else QColor(14, 8, 4, 200))
            p.drawRect(r)
            p.save()
            p.translate(r.center().x(), r.y() + 170)
            p.scale(2.2, 2.2)
            art.draw_figure(p, cls, "walk" if on else "stand", time.monotonic() * 3 if on else 0)
            p.restore()
            name, desc = info[cls]
            p.setFont(_font(14, True))
            p.setPen(GOLD if on else QColor("#C8B890"))
            p.drawText(QRectF(r.x(), r.y() + 186, r.width(), 24), Qt.AlignHCenter, name)
            c = W.CLASSES[cls]
            p.setFont(QFont("Tahoma", 8))
            p.setPen(QColor("#A89870"))
            p.drawText(QRectF(r.x() + 12, r.y() + 214, r.width() - 24, 20), Qt.AlignHCenter,
                       f"Str {c['str']}  Dex {c['dex']}  Mag {c['mag']}  Vit {c['vit']}")
            p.setFont(QFont("Georgia", 9))
            p.setPen(QColor("#D8C8A8"))
            p.drawText(QRectF(r.x() + 14, r.y() + 238, r.width() - 28, 90), Qt.TextWordWrap | Qt.AlignHCenter, desc)
            self.class_rects.append((r, cls))
        self._button(p, QRectF(w / 2 - 250, h - 90, 220, 44), "Back", self._back)
        self._button(p, QRectF(w / 2 + 30, h - 90, 220, 44), "Begin", self._new_game)

    def _back(self):
        self.name_edit.hide()
        self.state = "title"


# ---- the window ------------------------------------------------------------------------------------------------
_open = {}


def launch(desktop):
    win = _open.get("win")
    if win is not None and isValid(win):
        desktop.open_window(win)
        return win
    body = Game(desktop)
    win = host.window(desktop, "Claudeablo", body, ablo_icon(), size=(1020, 740))
    body.frame = win
    _open["win"] = win
    desktop.open_window(win)
    body.setFocus()
    return win


def shutdown():
    win = _open.get("win")
    if win is not None and isValid(win):
        win.content.shutdown()
