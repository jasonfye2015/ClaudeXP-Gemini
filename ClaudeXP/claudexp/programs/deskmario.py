"""Desktop Mario: a desktop pet in the spirit of Neko, drawn from the NES Super Mario Bros. sheets in Local
Storage\\SMB Clock (the same ones as the Super Claude Bros. screen saver - its cutter, supercb.cut, and its frames).

- Free roam (the default): he drops onto the taskbar and runs about. Goombas and Koopa Troopas walk in from the
  sides; he jumps on them - Goombas squish, Koopas go into their shells and he kicks the shells, which knock any
  enemy in their way flying - and now and then one catches him (Super Mario shrinks; little Mario does the death
  hop, falls off the screen and drops back in from the top).
- Follow the pointer: like Neko, he runs to stay under the pointer and jumps up at it.
Windows' title bars are platforms: he lands on them, runs along them and drops off their ends. Drag him anywhere
and let go (he falls), click him to make him jump, double-click for a mushroom (Super <-> small), click an enemy to
knock it over, right-click for his menu (the same as his icon in the notification area). The game's sound effects
come from Local Storage\\SMB Clock\\sounds."""
import json
import random
import warnings

from PySide6.QtCore import QObject, QRect, Qt, QTimer, QUrl
from PySide6.QtGui import QAction, QActionGroup, QColor, QCursor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QMenu, QMessageBox, QSystemTrayIcon, QWidget

from .. import supercb as smb
from ..paths import DATA
from ..tray import TrayIcon

SETTINGS_FILE = DATA / "deskmario.json"
DEFAULT_SETTINGS = {"start_at_logon": True, "mode": "roam", "character": "Mario", "size": 3, "enemies": "some",
                    "sound": True}
CHARACTERS = list(smb.CHARACTERS)               # Mario, Luigi, Super Mario, Super Luigi, Fire Mario
MUSHROOM = {"Mario": "Super Mario", "Luigi": "Super Luigi", "Super Mario": "Mario", "Super Luigi": "Luigi",
            "Fire Mario": "Mario"}
SMALL = {"Super Mario": "Mario", "Super Luigi": "Luigi", "Fire Mario": "Mario"}
ENEMIES = {"off": None, "some": (9, 20), "lots": (3, 8)}     # seconds between arrivals
TICK_MS = 16
# NES pixels per frame (60 a second), as the game moves
GRAVITY, MAX_FALL = 0.28, 4.5
JUMP, BOUNCE, HOP = -5.0, -3.6, -3.2
WALK, RUN = 1.1, 1.8
ENEMY_SPEED, SHELL_SPEED = 0.45, 3.2
CHAIN = ["100", "200", "400"]


def _pixmap(img, scale):
    return QPixmap.fromImage(img.scaled(img.width() * scale, img.height() * scale, Qt.IgnoreAspectRatio,
                                        Qt.FastTransformation))


_pix = {}


def sprite(key, x, y, w, h, scale, flip=False, upside=False):
    """A piece of an NES sheet, scaled up without smoothing (cached)."""
    k = (key, x, y, w, h, scale, flip, upside)
    if k not in _pix:
        img = smb.cut(key, x, y, w, h, flip)
        if upside:
            img = img.mirrored(False, True)
        _pix[k] = _pixmap(img, scale)
    return _pix[k]


class Sprite(QWidget):
    """One thing on the desktop - Mario, an enemy, a score - drawn from a pixmap."""

    def __init__(self, desktop, clickable=True):
        super().__init__(desktop)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        if not clickable:
            self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.pm = QPixmap()
        self.owner = None

    def set_picture(self, pm, x, y):
        """Draw pm with its bottom-left at (x, y + its height): sprites stand on their feet."""
        if pm.size() != self.size():
            self.resize(pm.size())
        self.pm = pm
        self.move(int(x), int(y))
        self.update()

    def paintEvent(self, event):
        QPainter(self).drawPixmap(0, 0, self.pm)

    # Mario and the enemies hand their mouse to the world
    def mousePressEvent(self, e):
        if self.owner is not None:
            self.owner.press(self, e)

    def mouseMoveEvent(self, e):
        if self.owner is not None:
            self.owner.drag(self, e)

    def mouseReleaseEvent(self, e):
        if self.owner is not None:
            self.owner.release(self, e)

    def mouseDoubleClickEvent(self, e):
        if self.owner is not None:
            self.owner.double(self, e)


class Thing:
    """Something that moves: position (top-left, desktop pixels), speed (desktop pixels per frame), its sprite."""

    def __init__(self, world, kind, w, h, clickable=True):
        self.world, self.kind = world, kind
        self.w, self.h = w, h
        self.x = self.y = self.vx = self.vy = 0.0
        self.t = 0
        self.state = ""
        self.widget = Sprite(world.desktop, clickable)
        self.widget.owner = world
        self.widget.show()

    def feet(self):
        return self.y + self.h

    def rect(self, shrink=0):
        return QRect(int(self.x + shrink), int(self.y + shrink), int(self.w - 2 * shrink), int(self.h - 2 * shrink))

    def remove(self):
        self.widget.hide()
        self.widget.deleteLater()


class World(QObject):
    """Mario, his enemies and the bits that fly about, on one desktop."""

    def __init__(self, desktop, controller):
        super().__init__(desktop)
        self.desktop, self.c = desktop, controller
        self.s = int(controller.settings["size"])
        self.character = controller.settings["character"]
        self.mario = Thing(self, "mario", 16 * self.s, self._height(), clickable=True)
        self.enemies, self.bits = [], []
        self.effects = {}
        self.chain = 0
        self.aim = None                         # the enemy he's jumped at
        self.safe_until = 0                    # (frames) invincible: just hurt, or just back
        self.dragging = None
        self.pressed = None
        self.wander_x = None
        self.next_wander = 0
        self.next_enemy = self._enemy_delay()
        self.frame_no = 0
        self.respawn_at = None
        area = desktop.work_area()
        self.mario.x = area.left() + area.width() * random.uniform(0.3, 0.7)
        self.mario.y = area.top() - self.mario.h
        self.mario.state = "air"
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(TICK_MS)
        self._draw_mario()

    # ---- what he is ----------------------------------------------------------------------------------------------
    def _height(self):
        return smb.CHARACTERS[self.character][2] * self.s

    @property
    def big(self):
        return smb.CHARACTERS[self.character][2] == 32

    def set_character(self, name):
        bottom = self.mario.feet()
        self.character = name
        self.mario.h = self._height()
        self.mario.y = bottom - self.mario.h
        self._draw_mario()

    def sfx(self, name):
        from .. import sound
        if not self.c.settings["sound"] or sound.is_muted():
            return
        path = smb._folder() / smb.SOUNDS / f"{name}.wav"
        if not path.exists():
            return
        if name not in self.effects:
            from PySide6.QtMultimedia import QSoundEffect
            e = QSoundEffect(self)
            e.setSource(QUrl.fromLocalFile(str(path)))
            self.effects[name] = e
        e = self.effects[name]
        e.setVolume(0.55 * sound.wave_volume())
        e.play()

    # ---- the ground: the taskbar, and windows' title bars ---------------------------------------------------
    def floor_y(self):
        return self.desktop.work_area().bottom() + 1

    def platforms(self):
        """[(top, left, right)]: the taskbar's top edge and every open window's."""
        out = [(self.floor_y(), -10 ** 6, 10 ** 6)]
        for w in getattr(self.desktop, "windows", []):
            if w.isVisible() and not getattr(w, "minimized", False):
                g = w.geometry()
                if g.top() > 0:
                    out.append((g.top(), g.left(), g.right()))
        return out

    def _under(self, t, old_feet, new_feet):
        """The highest platform crossed going from old_feet to new_feet under t (or None)."""
        mid = t.x + t.w / 2
        best = None
        for top, left, right in self.platforms():
            if left + 4 <= mid <= right - 4 and old_feet - 1 <= top <= new_feet + 0.5:
                if best is None or top < best:
                    best = top
        return best

    def _support(self, t):
        mid = t.x + t.w / 2
        for top, left, right in self.platforms():
            if left + 4 <= mid <= right - 4 and abs(top - t.feet()) <= 10:
                return top
        return None

    def _fall(self, t, dead=False):
        """Gravity for one frame; True when it has landed."""
        old = t.feet()
        t.vy = min(t.vy + GRAVITY * self.s, MAX_FALL * self.s)
        t.y += t.vy
        if dead or t.vy < 0:
            return False
        top = self._under(t, old, t.feet())
        if top is not None:
            t.y, t.vy = top - t.h, 0.0
            return True
        return False

    # ---- the clock ------------------------------------------------------------------------------------------
    def tick(self):
        self.frame_no += 1
        m = self.mario
        m.t += 1
        if self.dragging is None:
            self._mario_step(m)
        self._enemies_step()
        self._bits_step()
        if self.c.settings["mode"] == "roam" and ENEMIES.get(self.c.settings["enemies"]):
            self.next_enemy -= 1
            if self.next_enemy <= 0:
                self.next_enemy = self._enemy_delay()
                if len(self.enemies) < 4 and m.state != "dead":
                    self._spawn()
        if self.frame_no % 120 == 0:
            self.raise_all()
        self._draw_mario()

    def raise_all(self):
        menu = getattr(self.desktop, "start_menu", None)
        if menu is not None and menu.isVisible():
            return
        for e in self.enemies:
            e.widget.raise_()
        self.mario.widget.raise_()

    def _enemy_delay(self):
        span = ENEMIES.get(self.c.settings["enemies"]) or (10, 20)
        return int(random.uniform(*span) * 1000 / TICK_MS)

    # ---- Mario ----------------------------------------------------------------------------------------------
    def _mario_step(self, m):
        s = self.s
        if m.state == "dead":
            if m.t > 30:                              # (a moment's pause, then the hop and the fall)
                if m.t == 31:
                    m.vy = -5.0 * s
                self._fall(m, dead=True)
            if m.y > self.desktop.height() + 10:
                self._respawn()
            return
        if self.safe_until:
            self.safe_until -= 1
        area = self.desktop.work_area()
        if m.state == "ground":
            if self._support(m) is None:
                m.state = "air"
            else:
                m.y = self._support(m) - m.h       # (riding a window that moved)
                self._think(m)
        if m.state == "air":
            a = self.aim
            if a is not None and a in self.enemies and a.state in ("walk", "shell"):
                # steering in the air to come down on its head, the way a player does
                d = (a.x + a.w / 2) - (m.x + m.w / 2)
                m.vx = max(-RUN * s, min(RUN * s, a.vx + 0.12 * d))
                if abs(m.vx) > 0.1:
                    m.facing = 1 if m.vx > 0 else -1
            if self._fall(m):
                m.state = "ground"
                self.chain = 0
                self.aim = None
        m.x += m.vx
        if m.x < area.left() - m.w // 2 or m.x > area.right() - m.w // 2:
            m.x = max(area.left() - m.w // 2, min(m.x, area.right() - m.w // 2))
            m.vx = 0.0
        if m.y > self.desktop.height():               # (fell off somewhere)
            self._respawn()

    def _think(self, m):
        """On the ground: where to run, when to jump."""
        s = self.s
        mode = self.c.settings["mode"]
        if mode == "follow":
            p = self.desktop.mapFromGlobal(QCursor.pos())
            target = p.x() - m.w / 2
            dy = m.y - p.y()
            if abs(target - m.x) < 6 * s and 0 < dy < 70 * s and random.random() < 0.04:
                self._jump(m, JUMP)
                return
        else:
            target = self._roam_target(m)
            threat = self._threat(m)
            if threat is not None:
                gap = abs((threat.x + threat.w / 2) - (m.x + m.w / 2))
                if gap < 34 * s:
                    m.vx = (1 if threat.x > m.x else -1) * WALK * s
                    m.facing = 1 if m.vx > 0 else -1
                    self.aim = threat if random.random() < 0.9 else None    # (now and then he misjudges it)
                    self._jump(m, JUMP)
                    return
                target = threat.x                     # (go and meet it)
            if random.random() < 0.003:
                self._jump(m, HOP)
                return
        dx = target - m.x
        speed = (RUN if abs(dx) > 120 * s else WALK) * s
        if abs(dx) < 2 * s:
            m.vx = 0.0
        else:
            m.vx = speed if dx > 0 else -speed
            m.facing = 1 if dx > 0 else -1

    def _roam_target(self, m):
        if self.wander_x is None or self.frame_no >= self.next_wander or abs(self.wander_x - m.x) < 3 * self.s:
            if self.wander_x is not None and abs(self.wander_x - m.x) < 3 * self.s and self.frame_no < self.next_wander:
                return m.x                                # (got there: stand a while)
            area = self.desktop.work_area()
            self.wander_x = random.uniform(area.left(), area.right() - m.w)
            self.next_wander = self.frame_no + random.randint(180, 600)
        return self.wander_x

    def _threat(self, m):
        """The nearest enemy coming at him (or a still shell to kick), on his level."""
        best, gap = None, 10 ** 6
        for e in self.enemies:
            if e.state in ("squished", "flipped") or abs(e.feet() - m.feet()) > 6:
                continue
            d = (e.x + e.w / 2) - (m.x + m.w / 2)
            coming = e.vx == 0 or (d > 0) != (e.vx > 0)
            if coming and abs(d) < gap and abs(d) < 160 * self.s:
                best, gap = e, abs(d)
        return best

    def _jump(self, m, power):
        m.vy = power * self.s
        m.state = "air"
        self.sfx("jump" if self.big else "jumpsmall")

    def hurt(self):
        m = self.mario
        if self.safe_until or m.state == "dead":
            return
        if self.character in SMALL:                   # Super Mario shrinks
            self.set_character(SMALL[self.character])
            self.safe_until = 120
            self.sfx("pipepowerdown")
            return
        m.state, m.t, m.vx, m.vy = "dead", 0, 0.0, 0.0
        self.sfx("death")

    def _respawn(self):
        m = self.mario
        area = self.desktop.work_area()
        self.set_character(self.c.settings["character"])
        if self.c.settings["mode"] == "follow":
            m.x = self.desktop.mapFromGlobal(QCursor.pos()).x() - m.w / 2
        else:
            m.x = area.left() + area.width() * random.uniform(0.15, 0.85)
        m.y = area.top() - m.h
        m.vx = m.vy = 0.0
        m.state, m.t = "air", 0
        self.safe_until = 90

    def _draw_mario(self):
        m = self.mario
        x0, y0, h = smb.CHARACTERS[self.character]
        facing = getattr(m, "facing", 1)
        if m.state == "dead":
            pm = sprite("chars", x0 + smb.FRAME_X[6], 8, 16, 16, self.s)
        else:
            if m.state in ("air", "held"):
                f = 5
            elif abs(m.vx) > 0.01:
                f = 1 + (m.t // max(3, int(8 - abs(m.vx) / self.s * 2))) % 3
            else:
                f = 0
            pm = sprite("chars", x0 + smb.FRAME_X[f], y0, 16, h, self.s, flip=facing < 0)
        if self.safe_until and (self.safe_until // 4) % 2:   # (blinking while he can't be hurt)
            pm = QPixmap(pm.size())
            pm.fill(Qt.transparent)
        m.widget.set_picture(pm, m.x, m.y + m.h - pm.height())

    # ---- enemies --------------------------------------------------------------------------------------------
    def _spawn(self):
        kind = random.choice(["goomba", "goomba", "koopa"])
        s = self.s
        e = Thing(self, kind, 16 * s, (16 if kind == "goomba" else 24) * s)
        area = self.desktop.work_area()
        left = random.random() < 0.5
        e.x = area.left() - e.w if left else area.right()
        e.y = self.floor_y() - e.h
        e.vx = (ENEMY_SPEED if left else -ENEMY_SPEED) * s
        e.state = "walk"
        self.enemies.append(e)
        self._draw_enemy(e)
        self.mario.widget.raise_()

    def _enemies_step(self):
        s = self.s
        m = self.mario
        area = self.desktop.work_area()
        for e in list(self.enemies):
            e.t += 1
            if e.state == "flipped":
                self._fall(e, dead=True)
                if e.y > self.desktop.height():
                    self._drop(e)
                    continue
            elif e.state == "squished":
                if e.t > 30:
                    self._drop(e)
                    continue
            else:
                e.x += e.vx
                if e.x < area.left() - e.w - 4 or e.x > area.right() + 4:
                    self._drop(e)
                    continue
                if e.state == "shell" and e.vx:                # a kicked shell bowls the others over
                    for o in self.enemies:
                        if o is not e and o.state in ("walk", "shell") and o.rect(2 * s).intersects(e.rect(2 * s)):
                            self._flip(o)
                            self._score(o, "400")
                            self.sfx("kickkill")
                if m.state not in ("dead", "held") and self.dragging is None:
                    self._touch(m, e)
            self._draw_enemy(e)

    def _touch(self, m, e):
        s = self.s
        if not m.rect(2 * s).intersects(e.rect(1 * s)):
            return
        if m.vy > 0 and m.feet() <= e.y + 8 * s:             # landed on it
            self._stomp(e)
            m.vy = BOUNCE * s
            m.state = "air"
            return
        if e.state == "shell" and e.vx == 0:                 # a still shell: kick it
            e.vx = (SHELL_SPEED if e.x >= m.x else -SHELL_SPEED) * s
            e.x += e.vx * 3
            self.sfx("kickkill")
            self._score(e, "400")
            return
        if e.state == "shell" and e.t < 12:                   # (just kicked: it's moving away)
            return
        self.hurt()

    def _stomp(self, e):
        s = self.s
        self.sfx("stompswim")
        self._score(e, CHAIN[min(self.chain, len(CHAIN) - 1)])
        self.chain += 1
        if e.kind == "goomba":
            e.state, e.t, e.vx = "squished", 0, 0.0
        elif e.state == "walk":
            e.state, e.vx, e.t = "shell", 0.0, 0
            bottom = e.feet()
            e.h = 16 * s
            e.y = bottom - e.h
        else:
            e.vx = 0.0 if e.vx else (SHELL_SPEED if e.x >= self.mario.x else -SHELL_SPEED) * s
            e.t = 0

    def _flip(self, e):
        e.state, e.vy, e.vx = "flipped", -3.0 * self.s, 0.0

    def _drop(self, e):
        if e in self.enemies:
            self.enemies.remove(e)
        e.remove()

    def _draw_enemy(self, e):
        s = self.s
        walk = (e.t // 12) % 2
        if e.kind == "goomba":
            pm = sprite("enemies", 36, 24, 16, 8, s) if e.state == "squished" else \
                sprite("enemies", 18 * walk, 16, 16, 16, s, upside=e.state == "flipped")
        elif e.state in ("shell", "flipped"):
            pm = sprite("enemies", 72, 120, 16, 16, s, upside=e.state == "flipped")
        else:
            pm = sprite("enemies", 18 * walk, 112, 16, 24, s, flip=e.vx > 0)
        e.widget.set_picture(pm, e.x, e.y + e.h - pm.height())

    # ---- scores and coins -------------------------------------------------------------------------------------
    def _score(self, e, text):
        b = Thing(self, "score", 16 * self.s, 8 * self.s, clickable=False)
        b.x, b.y, b.text = e.x, e.y - 10 * self.s, text
        self.bits.append(b)
        self._draw_bit(b)

    def coin(self):
        """A coin pops out of the top of his head."""
        m = self.mario
        b = Thing(self, "coin", 8 * self.s, 16 * self.s, clickable=False)
        b.x, b.y, b.vy = m.x + 4 * self.s, m.y - 16 * self.s, -4.0 * self.s
        self.bits.append(b)
        self.sfx("coin")
        self._draw_bit(b)

    def _bits_step(self):
        for b in list(self.bits):
            b.t += 1
            if b.kind == "score":
                b.y -= 0.6 * self.s
                done = b.t > 45
            else:
                b.vy += GRAVITY * self.s
                b.y += b.vy
                done = b.t > 30
            if done:
                self.bits.remove(b)
                b.remove()
            else:
                self._draw_bit(b)

    def _draw_bit(self, b):
        if b.kind == "score":
            row = {"100": 26, "200": 36, "400": 46}[b.text]
            pm = sprite("items", 234, row, 16, 8, self.s)
        else:
            pm = sprite("items", 180 + 10 * ((b.t // 4) % 4), 36, 8, 16, self.s)
        b.widget.set_picture(pm, b.x, b.y)

    # ---- the mouse --------------------------------------------------------------------------------------------
    def press(self, widget, e):
        if e.button() == Qt.RightButton:
            self.c.menu.exec(e.globalPosition().toPoint())
            return
        if e.button() != Qt.LeftButton:
            return
        if widget is not self.mario.widget:                    # an enemy: knocked over
            for en in self.enemies:
                if en.widget is widget and en.state in ("walk", "shell"):
                    self._flip(en)
                    self._score(en, "100")
                    self.sfx("kickkill")
            return
        self.pressed = (e.globalPosition().toPoint(), e.position().toPoint())

    def drag(self, widget, e):
        if self.pressed is None or widget is not self.mario.widget:
            return
        at, offset = self.pressed
        if self.dragging is None and (e.globalPosition().toPoint() - at).manhattanLength() > 4:
            self.dragging = offset
            self.mario.state, self.mario.vx, self.mario.vy = "held", 0.0, 0.0
        if self.dragging is not None:
            p = self.desktop.mapFromGlobal(e.globalPosition().toPoint()) - self.dragging
            self.mario.x, self.mario.y = p.x(), p.y()
            self._draw_mario()

    def release(self, widget, e):
        if self.pressed is None or widget is not self.mario.widget:
            return
        self.pressed = None
        m = self.mario
        if self.dragging is not None:                           # let go: he falls
            self.dragging = None
            m.state, m.vy = "air", 0.0
            return
        if m.state == "ground":
            self._jump(m, JUMP)
            if random.random() < 0.3:
                QTimer.singleShot(250, self.coin)

    def double(self, widget, e):
        if widget is not self.mario.widget:
            return
        self.mushroom()

    def mushroom(self):
        new = MUSHROOM.get(self.character, "Super Mario")
        self.sfx("powerup" if smb.CHARACTERS[new][2] == 32 else "pipepowerdown")
        self.set_character(new)

    def close(self):
        self.timer.stop()
        for t in [self.mario] + self.enemies + self.bits:
            t.remove()
        self.enemies, self.bits = [], []


# ---- the program -------------------------------------------------------------------------------------------------
_controller = None


def mario_icon(size=32):
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    if smb.available():
        img = smb.cut("chars", 0, 8, 16, 16)
        p = QPainter(pm)
        p.drawImage(QRect(0, 0, size, size), img)
        p.end()
    else:
        p = QPainter(pm)
        p.setRenderHint(QPainter.Antialiasing)
        p.setBrush(QColor("#D82800"))
        p.setPen(Qt.NoPen)
        p.drawEllipse(4, 4, size - 8, size - 8)
        p.end()
    return QIcon(pm)


class MarioController:
    def __init__(self, desktop):
        self.desktop = desktop
        self.settings = dict(DEFAULT_SETTINGS)
        try:
            data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        except FileNotFoundError:
            data = {}
        except (OSError, ValueError) as exc:
            warnings.warn(f"Could not read Desktop Mario's settings from {SETTINGS_FILE}: {exc}")
            data = {}
        if isinstance(data, dict):
            self.settings.update({k: v for k, v in data.items()
                                  if k in DEFAULT_SETTINGS and isinstance(v, type(DEFAULT_SETTINGS[k]))})
        if self.settings["mode"] not in ("roam", "follow"):
            self.settings["mode"] = "roam"
        if self.settings["character"] not in CHARACTERS:
            self.settings["character"] = "Mario"
        if self.settings["size"] not in (2, 3, 4):
            self.settings["size"] = 3
        if self.settings["enemies"] not in ENEMIES:
            self.settings["enemies"] = "some"
        self.world = None
        self.tray = TrayIcon(desktop, mario_icon(32), desktop)
        self.tray.setToolTip("Desktop Mario")
        self.menu = QMenu(desktop)
        self.tray.setContextMenu(self.menu)
        self.tray.activated.connect(self._tray_activated)
        self.menu.aboutToShow.connect(self._build_menu)
        self._build_menu()

    def _save(self):
        try:
            SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
            SETTINGS_FILE.write_text(json.dumps(self.settings, indent=2), encoding="utf-8")
        except OSError as exc:
            QMessageBox.warning(self.desktop, "Desktop Mario", f"Could not save the settings:\n{exc}")

    def _radio(self, title, key, options):
        sub = self.menu.addMenu(title)
        group = QActionGroup(sub)
        for value, label in options:
            act = QAction(label, sub)
            act.setCheckable(True)
            act.setChecked(self.settings[key] == value)
            act.triggered.connect(lambda _=False, v=value: self._set(key, v))
            group.addAction(act)
            sub.addAction(act)

    def _toggle(self, title, key):
        act = QAction(title, self.menu)
        act.setCheckable(True)
        act.setChecked(bool(self.settings[key]))
        act.toggled.connect(lambda on: self._set(key, on))
        self.menu.addAction(act)

    def _build_menu(self):
        m = self.menu
        m.clear()
        out = self.world is not None
        act = m.addAction("Send Mario home" if out else "Show Desktop Mario", self.hide if out else self.show)
        f = act.font()
        f.setBold(True)
        act.setFont(f)
        self._toggle("Start Desktop Mario when Windows starts", "start_at_logon")
        m.addSeparator()
        self._radio("Behavior", "mode", [("roam", "Free roam (enemies, the taskbar)"),
                                         ("follow", "Follow the pointer")])
        self._radio("Character", "character", [(c, c) for c in CHARACTERS])
        self._radio("Enemies (free roam)", "enemies", [("off", "None"), ("some", "Now and then"),
                                                       ("lots", "Lots")])
        self._radio("Size", "size", [(2, "Small (2x)"), (3, "Normal (3x)"), (4, "Big (4x)")])
        self._toggle("Sound effects", "sound")
        m.addSeparator()
        m.addAction("Mushroom!", lambda: self.world and self.world.mushroom())
        m.addAction("Send in a Goomba", lambda: self.world and self.world._spawn())
        m.addSeparator()
        m.addAction("About Desktop Mario...", self._about)

    def _set(self, key, value):
        self.settings[key] = value
        self._save()
        w = self.world
        if w is None:
            return
        if key == "character":
            w.set_character(value)
        elif key == "size":
            self.hide()
            self.show()
        elif key == "enemies":
            w.next_enemy = w._enemy_delay()

    def show(self):
        if not smb.available():
            from ..explorer.dialogs import msgbox
            msgbox(self.desktop, "Desktop Mario", "Desktop Mario needs the Super Mario Bros. sprite sheets in the "
                   "SMB Clock folder on drive E: (Local Storage\\SMB Clock).", icon="warning",
                   window_icon=mario_icon(16))
            return
        if self.world is None:
            self.world = World(self.desktop, self)
        self.tray.show()

    def hide(self):
        if self.world is not None:
            self.world.close()
            self.world.deleteLater()
            self.world = None
        self.tray.hide()

    def _about(self):
        from ..explorer.dialogs import msgbox
        msgbox(self.desktop, "About Desktop Mario",
               "Desktop Mario - a desktop pet in the spirit of Neko.\n\n"
               "Free roam: he drops onto the taskbar and runs about, stomping the Goombas and Koopa Troopas that walk "
               "in from the sides and kicking their shells. Follow the pointer: he runs after it and jumps at it. "
               "Windows' title bars are platforms.\n\nClick him to jump, double-click for a mushroom, drag him "
               "anywhere, click an enemy to knock it over, right-click for this menu.\n\nThe pictures and sounds are "
               "the NES game's, from Local Storage\\SMB Clock (as the Super Claude Bros. screen saver uses them).",
               icon="info", window_icon=mario_icon(16))

    def _tray_activated(self, reason):
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self.hide() if self.world is not None else self.show()


def _controller_for(desktop):
    global _controller
    if _controller is None or _controller.desktop is not desktop:
        if _controller is not None:
            _controller.hide()
        _controller = MarioController(desktop)
    return _controller


def start_at_logon(desktop):
    c = _controller_for(desktop)
    if c.settings["start_at_logon"] and smb.available():
        c.show()


def launch(desktop):
    c = _controller_for(desktop)
    c.show()
    return c.world


def shutdown():
    if _controller is not None:
        _controller.hide()
