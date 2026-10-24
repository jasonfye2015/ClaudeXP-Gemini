"""The pictures, from Local Storage\\casualties unknown: the Expie and the traders as paper dolls (parts), the item
pictures cut from the Items sheet, the status icons ("moodles"), the cave tiles, the lore notes, the title, the
preset portraits and the death screens."""
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPixmap, QTransform

from .items import ITEMS

VARIOUS = "Sprites - Various"
SHEETS = {"items": "PC _ Computer - Casualties_ Unknown - Objects - Items.png",
          "status": "PC _ Computer - Casualties_ Unknown - User Interface - Status Icons.png",
          "tiles": "PC _ Computer - Casualties_ Unknown - Environment - Tile Backgrounds.png",
          "notes": "PC _ Computer - Casualties_ Unknown - User Interface - Note Drawings.png"}
# status icons: 20x20 cells, 9 across from (18, 74), every 24 px; (row, column) for each state the game shows
MOODLES = {"bleeding": (0, 5), "bleeding2": (3, 6), "shard": (2, 6), "fracture": (0, 8), "infection": (2, 2),
           "fever": (7, 2), "arrest": (1, 3), "lowblood": (4, 5), "oxygen": (6, 0), "cold": (1, 6), "hot": (4, 2),
           "wet": (8, 4), "hungry": (5, 1), "thirsty": (7, 6), "tired": (0, 4), "depressed": (2, 1), "gloomy": (3, 3),
           "pain": (0, 7), "brain": (6, 6), "pills": (5, 6), "unconscious": (4, 0), "healed": (2, 5), "immune": (3, 8),
           "alarm": (1, 7), "question": (1, 8), "wait": (8, 2)}
TILE_RECTS = {"rock": (16, 48, 32, 32), "sand": (54, 48, 32, 32), "dark": (92, 48, 32, 32), "pale": (130, 48, 32, 32),
              "gold": (168, 48, 32, 32), "cave64": (15, 111, 64, 64), "moss64": (85, 111, 64, 64),
              "teal64": (155, 111, 64, 64), "black64": (225, 111, 64, 64), "marble": (14, 204, 128, 128)}
LAYER_TILES = {1: ("rock", "cave64"), 2: ("pale", "cave64"), 3: ("teal64", "teal64"), 4: ("dark", "black64"),
               5: ("gold", "marble")}
EXP = "Sprites - Main Character"
OTH = "Sprites - Other characters"


def _px(img):
    return QPixmap.fromImage(img)


def _visible_box(img):
    """(left, top, right, bottom) of the pixels that aren't transparent."""
    xs, ys = [], []
    for y in range(img.height()):
        for x in range(img.width()):
            if (img.pixel(x, y) >> 24) > 40:
                xs.append(x)
                ys.append(y)
    return (min(xs), min(ys), max(xs), max(ys)) if xs else (0, 0, img.width() - 1, img.height() - 1)


class Assets:
    def __init__(self, root):
        self.root = Path(root)
        self.ok = (self.root / EXP / "experimentHead.png").exists() and (self.root / VARIOUS / SHEETS["items"]).exists()
        if not self.ok:
            return
        self.sheets = {k: QImage(str(self.root / VARIOUS / v)).convertToFormat(QImage.Format_ARGB32) for k, v in SHEETS.items()}
        self.exp = {p.stem[len("experiment"):]: QImage(str(p)).convertToFormat(QImage.Format_ARGB32)
                    for p in (self.root / EXP).glob("*.png")}
        self.oth = {p.stem: QImage(str(p)).convertToFormat(QImage.Format_ARGB32) for p in (self.root / OTH).glob("*.png")}
        self.box = {k: _visible_box(img) for k, img in self.exp.items()}
        self.items = {}
        for key, (_n, (x, y, w, h), _k, _v, _b) in ITEMS.items():
            img = self.sheets["items"].copy(x, y, w, h)
            self._clear_purple(img)
            self.items[key] = img
        self.moodles = {}
        for key, (r, c) in MOODLES.items():
            self.moodles[key] = self.sheets["status"].copy(18 + 24 * c, 74 + 24 * r, 20, 20)
        self.tiles = {k: self.sheets["tiles"].copy(*r) for k, r in TILE_RECTS.items()}
        self.notes = [self.sheets["notes"].copy(6 + 60 * c, 50 + 120 * r, 54, 114) for r in range(4) for c in range(6)]
        self.title = QImage(str(self.root / "Title.jpg"))
        self.presets = {k: QImage(str(self.root / f"Preset{k}.png")) for k in ("Normal", "Relaxed", "Paradise", "Unchipped")}
        self.deaths = [QImage(str(self.root / f"DeathScreen{i}.png")) for i in (1, 2, 3)]
        self._cache = {}

    def _clear_purple(self, img):
        for y in range(img.height()):
            for x in range(img.width()):
                p = img.pixel(x, y)
                r, g, b = (p >> 16) & 255, (p >> 8) & 255, p & 255
                if abs(r - 0x8A) < 24 and abs(g - 0x5A) < 24 and abs(b - 0x9D) < 24:
                    img.setPixel(x, y, 0)

    def item(self, key, size):
        """An item's picture as a pixmap fitting a size x size box (nearest-neighbour, pixels kept crisp)."""
        k = ("item", key, size)
        if k not in self._cache:
            img = self.items.get(key)
            if img is None:
                pm = QPixmap(size, size)
                pm.fill(Qt.transparent)
            else:
                sc = max(1, int(size / max(img.width(), img.height())))
                pm = _px(img.scaled(img.width() * sc, img.height() * sc, Qt.IgnoreAspectRatio, Qt.FastTransformation))
            self._cache[k] = pm
        return self._cache[k]

    def moodle(self, key, size=20):
        k = ("moodle", key, size)
        if k not in self._cache:
            img = self.moodles.get(key, self.moodles["question"])
            self._cache[k] = _px(img.scaled(size, size, Qt.IgnoreAspectRatio, Qt.FastTransformation))
        return self._cache[k]

    def tile(self, name, size):
        k = ("tile", name, size)
        if k not in self._cache:
            self._cache[k] = _px(self.tiles[name].scaled(size, size, Qt.IgnoreAspectRatio, Qt.FastTransformation))
        return self._cache[k]

    def note(self, n, height):
        k = ("note", n, height)
        if k not in self._cache:
            img = self.notes[n % len(self.notes)]
            sc = height / img.height()
            self._cache[k] = _px(img.scaled(int(img.width() * sc), height, Qt.IgnoreAspectRatio, Qt.FastTransformation))
        return self._cache[k]

    # ---- the Expie ----------------------------------------------------------------------------------------------
    def draw_expie(self, p, x, y, facing, phase, body, talking=False, lying=False, scale=1.0, eyes=None):
        """Paint the Expie with its feet at (x, y) in the painter's coordinates. phase: walk cycle 0..1 (None standing).
        body: a Body (for the look of the head, the eyes and the limbs), or None for the healthy one."""
        e = self.exp
        p.save()
        p.translate(x, y)
        p.scale(scale * (1 if facing >= 0 else -1), scale)
        if lying:
            p.rotate(-90)
            p.translate(0, 12)
        import math
        swing = math.sin(phase * 2 * math.pi) if phase is not None else 0.0
        # tail, behind
        tl, tt, tr, tb = self.box["Tail"]
        p.save()
        p.translate(-1, -27 + (1.0 * swing if phase is not None else 0))       # the hips, at the back of the body
        p.rotate(-8 + 6 * swing if phase is not None else -8)
        p.scale(0.7, 0.7)
        p.drawImage(QPointF(-tr - 1, -(tt + tb) / 2), e["Tail"])             # the fur's base on that point
        p.restore()
        # back leg, back arm
        self._leg(p, -1, -swing, body, "l_leg", dim=True)
        self._arm(p, -1, swing, body, "l_arm", dim=True)
        # torso
        p.drawImage(QPointF(-4, -34), e["DownTorso"])
        p.drawImage(QPointF(-4, -43), e["UpTorso"])
        # front leg, front arm
        self._leg(p, 1, swing, body, "r_leg")
        self._arm(p, 1, -swing, body, "r_arm")
        # head
        head = self._head_image(body, talking)
        hl, ht, hr, hb = self.box["Head"]
        hx = -(hl + hr) / 2 + 1            # the head's visible middle just ahead of the body's centre line
        hy = -40 - hb                      # its underside overlapping the top of the torso, no neck
        p.drawImage(QPointF(hx, hy), head)
        eye = eyes or self._eye_name(body)
        if eye and eye in e:
            p.drawImage(QPointF(hx, hy), e[eye])
        if body is not None and body.parts["head"].bleed > 0 and "Nosebleed" in e:
            nl, nt, nr, nb = self.box["Nosebleed"]
            # the drip's top at the underside of the snout, near its tip
            p.drawImage(QPointF(hx + hr - 3 - (nl + nr) / 2, hy + hb - 2 - nt), e["Nosebleed"])
        if body is not None and body.parts["head"].bandage > 0:
            p.fillRect(QRectF(hx + 4, hy + 3, 9, 3), QColor(235, 230, 220, 230))     # round the forehead
        p.restore()

    def _head_image(self, body, talking):
        e = self.exp
        if body is not None:
            d = body.parts["head"].disfigured
            if d > 0:
                return e.get(f"HeadDisfigured{min(3, d)}", e["Head"])
            if d < 0:
                return e.get(f"HeadDisfigured{min(3, -d)}Healed", e["Head"])
        if talking:
            return e.get("HeadBackMouth", e["Head"])
        return e["Head"]

    def _eye_name(self, body):
        if body is None:
            return "EyeOpen"
        if not body.alive:
            return "EyeClosed"
        if not body.conscious:
            return "EyeClosed"
        if body.parts["head"].disfigured and body.parts["head"].bleed > 0.5:
            return "EyeGone"
        if body.pain > 35 or body.blood < 30:
            return "EyePanic"
        if body.mood < 20:
            return "EyeSad"
        if body.temp < 34 or body.o2 < 88:
            return "EyeScared"
        if body.exhaustion > 80:
            return "EyeHalfClosed"
        if body.mood > 85 and body.pain < 5:
            return "EyeHappy"
        return "EyeOpen"

    def _leg(self, p, side, swing, body, part, dim=False):
        e = self.exp
        hurt = body is not None and body.parts[part].fracture
        p.save()
        p.translate(-1 + side, -26)
        p.rotate(swing * 22 if not hurt else swing * 6)
        self._dim(p, dim)
        p.drawImage(QPointF(-3, 0), e["Thigh"])
        p.translate(0, 10)
        p.rotate(max(0.0, -swing) * 25 if not hurt else 12)
        p.drawImage(QPointF(-2, -1), e["Crus"])
        p.drawImage(QPointF(-3, 6), e["Foot"])
        if body is not None and body.parts[part].bandage > 0:
            p.fillRect(QRectF(-3, 1, 5, 3), QColor(235, 230, 220, 230))
        if body is not None and body.parts[part].splint:
            p.fillRect(QRectF(-4, -2, 1.5, 12), QColor(150, 110, 60))
        p.restore()

    def _arm(self, p, side, swing, body, part, dim=False):
        e = self.exp
        p.save()
        p.translate(-1 + side * 2, -41)
        p.rotate(swing * 18)
        self._dim(p, dim)
        p.drawImage(QPointF(-2, 0), e["UpArm"])
        p.translate(0, 11)
        p.rotate(-10)
        p.drawImage(QPointF(-2, 0), e["DownArm"])
        p.drawImage(QPointF(-3, 13), e["HandF"] if side > 0 else e["HandB"])
        if body is not None and body.parts[part].bandage > 0:
            p.fillRect(QRectF(-2, 3, 4, 3), QColor(235, 230, 220, 230))
        if body is not None and body.parts[part].splint:
            p.fillRect(QRectF(-3, -1, 1.5, 12), QColor(150, 110, 60))
        p.restore()

    def _dim(self, p, on):
        if on:
            p.setOpacity(0.75)

    # ---- a trader ---------------------------------------------------------------------------------------------------
    def draw_trader(self, p, kind, x, y, facing=-1, talking=False, mood="calm", scale=1.0):
        prefix = {"dune": "duntrader", "mil": "miltrader", "exp": "exptrader"}[kind]
        eyes_prefix = {"dune": "dunetrader", "mil": "miltrader", "exp": "exptrader"}[kind]
        o = self.oth
        torso, head = o[prefix + "torso"], o[prefix + ("headtalk" if talking else "head")]
        arm, thigh, foot = o[prefix + "arm"], o[prefix + "thigh"], o[prefix + "foot"]
        eyes = o.get(eyes_prefix + {"calm": "eyes", "angry": "eyesangry", "sleep": "eyessleep" if kind == "dune" else "eyesclosed"}[mood])
        p.save()
        p.translate(x, y)
        p.scale(scale * (1 if facing >= 0 else -1), scale)
        th, fh = thigh.height(), foot.height()
        for side in (-1, 1):
            p.drawImage(QPointF(side * 5 - thigh.width() / 2, -fh - th + 2), thigh)
            p.drawImage(QPointF(side * 5 - foot.width() / 2, -fh), foot)
        ty = -fh - th - torso.height() + 6
        p.drawImage(QPointF(-torso.width() / 2, ty), torso)
        p.drawImage(QPointF(-torso.width() / 2 - 2, ty + 6), arm)
        p.drawImage(QPointF(torso.width() / 2 - arm.width() + 2, ty + 6), arm)
        hy = ty - head.height() + 8
        p.drawImage(QPointF(-head.width() / 2 + 2, hy), head)
        if eyes is not None:
            p.drawImage(QPointF(-eyes.width() / 2 + 2, hy + (head.height() - eyes.height()) / 2 - 2), eyes)
        p.restore()
