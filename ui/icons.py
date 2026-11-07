"""Item pictures: CC0 sprites (assets/items, by tools/import_icons.py - Dungeon Crawl Stone Soup's gear and wands,
7Soul1's gems, runes, potions and scroll), chosen by the item: its slot and tier (and a little variety between items
of the same tier), its wand body, its part's kind and element. The pixel art is enlarged crisply, then smoothed to the
size asked. Where a picture is missing, the item is painted instead."""
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QImage, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap, QRadialGradient

from ..game import data as D
from ..game import items as I

_cache = {}
from ..engine.itempics import ITEMS, sprite_name  # noqa: F401  (the pictures' choice: engine/itempics.py)


def _sprite(name, size):
    img = QImage(str(ITEMS / name))
    if img.isNull():
        return None
    k = max(1, (size * 2) // max(img.width(), img.height()))
    big = img.scaled(img.width() * k, img.height() * k, Qt.IgnoreAspectRatio, Qt.FastTransformation)   # (crisp)
    return QPixmap.fromImage(big.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation))


def rarity_colour(it):
    if it.get("type") in ("gear", "part", "wand"):
        r = D.RARITIES[min(4, int(it.get("rarity", 0)))][2]
    elif it.get("type") == "larder":
        r = {"seed": (0.7, 0.85, 0.45), "raw": (0.9, 0.62, 0.5), "cooked": (1.0, 0.78, 0.35)}[it["key"].split(":")[0]]
    elif it.get("type") == "crop":
        r = (0.65, 0.9, 0.45)
    else:
        r = (0.8, 0.8, 0.8)
    return QColor.fromRgbF(*r)


def element_qcolour(el):
    return QColor.fromRgbF(*D.ELEMENT_COLOUR.get(el, (0.8, 0.8, 0.8)))


def icon(it, size=56):
    key = (it.get("id") or str(it), size, I.item_name(it))
    if key in _cache:
        return _cache[key]
    if it.get("type") == "larder" and it["key"].startswith("seed:"):   # (a seed: its pouch, and what it grows)
        pm = _seed(it["key"][5:], size)
        if pm is not None:
            _cache[key] = pm
            return pm
    name = sprite_name(it)
    if name:
        pm = _sprite(name, size)
        if pm is not None:
            _cache[key] = pm
            return pm
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.scale(size / 64, size / 64)
    _draw(p, it)
    p.end()
    _cache[key] = pm
    return pm


def _seed(crop, size):
    from ..engine.itempics import larder_picture
    pouch, veg = larder_picture("seed:" + crop), larder_picture("raw:" + crop)
    a = _sprite(pouch, int(size * 0.72)) if pouch else None
    b = _sprite(veg, int(size * 0.62)) if veg else None
    if a is None or b is None:
        return None
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.SmoothPixmapTransform)
    p.drawPixmap(0, size - a.height(), a)
    p.drawPixmap(size - b.width(), 0, b)
    p.end()
    return pm


def _draw(p, it):
    t = it.get("type")
    if t == "gear":
        tone = QColor.fromRgbF(*D.RARITIES[it["rarity"]][2]).darker(130)
        _gear(p, it["slot"], tone)
    elif t == "wand":
        el = I.wand_stats(it)["element"]
        _wand(p, element_qcolour(el), D.WAND_BODIES[it["body"]]["tier"])
    elif t == "part":
        _gem(p, it["kind"], element_qcolour(it.get("element", "arcane")) if it["kind"] == "core" else None)
    elif t == "potion":
        _potion(p, QColor("#D83838") if it["kind"] == "health" else QColor("#3866E0"))
    elif t == "scroll":
        _scroll(p)


def _gear(p, slot, tone):
    p.setPen(QPen(tone.darker(180), 2))
    g = QLinearGradient(0, 8, 0, 58)
    g.setColorAt(0, tone.lighter(140))
    g.setColorAt(1, tone.darker(120))
    p.setBrush(g)
    path = QPainterPath()
    if slot == "hat":
        path.moveTo(32, 6)
        path.lineTo(50, 46)
        path.quadTo(32, 54, 14, 46)
        path.closeSubpath()
        p.drawPath(path)
        p.drawEllipse(QRectF(8, 42, 48, 12))
    elif slot == "robe":
        path.moveTo(24, 8)
        path.lineTo(40, 8)
        path.lineTo(54, 20)
        path.lineTo(48, 26)
        path.lineTo(46, 58)
        path.lineTo(18, 58)
        path.lineTo(16, 26)
        path.lineTo(10, 20)
        path.closeSubpath()
        p.drawPath(path)
        p.drawLine(QPointF(32, 12), QPointF(32, 56))
    elif slot == "gloves":
        p.drawRoundedRect(QRectF(18, 22, 28, 30), 8, 8)
        for k in range(4):
            p.drawRoundedRect(QRectF(19 + k * 7, 8, 6, 20), 3, 3)
        p.drawRoundedRect(QRectF(8, 28, 14, 8), 4, 4)
    elif slot == "boots":
        path.moveTo(18, 8)
        path.lineTo(34, 8)
        path.lineTo(34, 40)
        path.lineTo(54, 46)
        path.lineTo(54, 56)
        path.lineTo(16, 56)
        path.closeSubpath()
        p.drawPath(path)
    elif slot == "ring":
        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(tone.lighter(130), 6))
        p.drawEllipse(QRectF(16, 22, 32, 32))
        p.setPen(QPen(tone.darker(150), 1))
        p.setBrush(QColor("#9FE3FF"))
        p.drawEllipse(QRectF(25, 10, 14, 14))
    elif slot == "amulet":
        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(QColor("#B0A080"), 2))
        p.drawArc(QRectF(14, 2, 36, 40), 200 * 16, 140 * 16)
        p.setPen(QPen(tone.darker(180), 2))
        p.setBrush(g)
        p.drawEllipse(QRectF(20, 30, 24, 26))
        p.setBrush(QColor("#FFE070"))
        p.drawEllipse(QRectF(27, 38, 10, 10))


def _wand(p, glow, tier):
    wood = QColor.fromHsv(28, 140, 120 + min(100, tier * 12))
    p.setPen(QPen(wood.darker(170), 1.5))
    p.setBrush(wood)
    path = QPainterPath()
    path.moveTo(12, 56)
    path.lineTo(44, 18)
    path.lineTo(48, 22)
    path.lineTo(16, 60)
    path.closeSubpath()
    p.drawPath(path)
    rg = QRadialGradient(QPointF(48, 14), 14)
    c = QColor(glow)
    rg.setColorAt(0, QColor(255, 255, 255))
    rg.setColorAt(0.3, c)
    c.setAlpha(0)
    rg.setColorAt(1, c)
    p.setPen(Qt.NoPen)
    p.setBrush(rg)
    p.drawEllipse(QPointF(48, 14), 14, 14)


def _gem(p, kind, colour):
    c = colour or QColor({"lens": "#E8E0FF", "splitter": "#FFB0F0", "focus": "#F0E080", "quickener": "#90FFB0",
                          "seeker": "#FFD090", "rebound": "#A0C8FF", "piercer": "#FF9090"}.get(kind, "#FFFFFF"))
    p.setPen(QPen(c.darker(200), 1.5))
    g = QLinearGradient(16, 10, 48, 54)
    g.setColorAt(0, c.lighter(160))
    g.setColorAt(1, c.darker(140))
    p.setBrush(g)
    path = QPainterPath()
    if kind in ("core", "lens"):
        p.drawEllipse(QRectF(14, 14, 36, 36))
    elif kind == "splitter":
        path.moveTo(32, 8)
        path.lineTo(54, 50)
        path.lineTo(10, 50)
        path.closeSubpath()
        p.drawPath(path)
    elif kind == "focus":
        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(c, 7))
        p.drawEllipse(QRectF(14, 14, 36, 36))
    elif kind == "piercer":
        path.moveTo(32, 6)
        path.lineTo(42, 32)
        path.lineTo(32, 58)
        path.lineTo(22, 32)
        path.closeSubpath()
        p.drawPath(path)
    else:
        path.moveTo(32, 8)
        path.lineTo(54, 26)
        path.lineTo(46, 54)
        path.lineTo(18, 54)
        path.lineTo(10, 26)
        path.closeSubpath()
        p.drawPath(path)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(255, 255, 255, 120))
    p.drawEllipse(QRectF(22, 18, 10, 8))


def _potion(p, c):
    p.setPen(QPen(QColor("#303040"), 2))
    p.setBrush(QColor(220, 230, 240, 120))
    p.drawRect(QRectF(26, 6, 12, 14))
    g = QRadialGradient(QPointF(28, 38), 22)
    g.setColorAt(0, c.lighter(150))
    g.setColorAt(1, c.darker(150))
    p.setBrush(g)
    p.drawEllipse(QRectF(12, 18, 40, 40))
    p.setBrush(QColor("#8A6A40"))
    p.drawRect(QRectF(25, 2, 14, 7))


def _scroll(p):
    p.setPen(QPen(QColor("#6A5030"), 2))
    p.setBrush(QColor("#E8D8A8"))
    p.drawRoundedRect(QRectF(12, 14, 40, 36), 4, 4)
    p.setBrush(QColor("#C8B080"))
    p.drawEllipse(QRectF(8, 10, 10, 44))
    p.drawEllipse(QRectF(46, 10, 10, 44))
    p.setPen(QPen(QColor("#8060C0"), 2))
    for y in (24, 32, 40):
        p.drawLine(QPointF(22, y), QPointF(42, y))
