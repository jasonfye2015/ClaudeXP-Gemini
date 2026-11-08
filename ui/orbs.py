"""Claude's own state, drawn over the view: two glass orbs at the bottom corners - health (red) with poison (green)
round its rim on the left, sanity (blue) with consciousness (green) round its rim on the right - and their numbers
under them in their colours. When one is in danger, the edge of the view beats in its colour.

And the end of him: the silk laid across his eyes, the dark coming down, and the ending's line."""
import math

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainterPath, QPen, QRadialGradient

from ..game.condition import pulse

SERIF = "Georgia"
EDGE = {"health": QColor(210, 25, 20), "poison": QColor(70, 220, 60), "sanity": QColor(40, 90, 240),
        "conscious": QColor(130, 235, 160)}


def _orb(p, cx, cy, r, level, deep, bright, ring, ring_col, t, seed):
    # the iron round it
    g = QRadialGradient(QPointF(cx - r * 0.3, cy - r * 0.4), r * 1.5)
    g.setColorAt(0, QColor(92, 80, 66))
    g.setColorAt(1, QColor(22, 18, 15))
    p.setPen(QPen(QColor(8, 6, 5, 220), 2))
    p.setBrush(g)
    p.drawEllipse(QPointF(cx, cy), r + 8, r + 8)
    # the dark glass
    g = QRadialGradient(QPointF(cx, cy), r)
    g.setColorAt(0, QColor(14, 10, 14))
    g.setColorAt(1, QColor(3, 2, 4))
    p.setBrush(g)
    p.setPen(Qt.NoPen)
    p.drawEllipse(QPointF(cx, cy), r, r)
    # what's in it: a liquid, its surface moving
    clip = QPainterPath()
    clip.addEllipse(QPointF(cx, cy), r - 1, r - 1)
    p.save()
    p.setClipPath(clip)
    top = cy + r - 2 * r * max(0.0, min(1.0, level))
    surf = QPainterPath()
    surf.moveTo(cx - r, cy + r + 2)
    for k in range(25):
        x = cx - r + 2 * r * k / 24
        y = top + 2.2 * math.sin(t * 2.1 + k * 0.55 + seed) + 1.4 * math.sin(t * 3.3 - k * 0.9)
        surf.lineTo(x, y)
    surf.lineTo(cx + r, cy + r + 2)
    surf.closeSubpath()
    lg = QLinearGradient(0, top, 0, cy + r)
    lg.setColorAt(0, bright)
    lg.setColorAt(1, deep)
    p.setBrush(lg)
    p.drawPath(surf)
    shade = QRadialGradient(QPointF(cx + r * 0.25, cy + r * 0.2), r * 1.1)          # (round: darker at its edge)
    shade.setColorAt(0, QColor(0, 0, 0, 0))
    shade.setColorAt(1, QColor(0, 0, 0, 150))
    p.setBrush(shade)
    p.drawEllipse(QPointF(cx, cy), r, r)
    p.restore()
    # the shine on the glass
    hl = QRadialGradient(QPointF(cx - r * 0.35, cy - r * 0.45), r * 0.55)
    hl.setColorAt(0, QColor(255, 255, 255, 70))
    hl.setColorAt(1, QColor(255, 255, 255, 0))
    p.setBrush(hl)
    p.drawEllipse(QPointF(cx - r * 0.3, cy - r * 0.4), r * 0.55, r * 0.4)
    # the second measure, round the rim
    rect = QRectF(cx - r - 4, cy - r - 4, 2 * r + 8, 2 * r + 8)
    p.setBrush(Qt.NoBrush)
    p.setPen(QPen(QColor(0, 0, 0, 160), 5, Qt.SolidLine, Qt.FlatCap))
    p.drawArc(rect, 0, 360 * 16)
    if ring > 0.005:
        p.setPen(QPen(ring_col, 4, Qt.SolidLine, Qt.RoundCap))
        p.drawArc(rect, -90 * 16, -int(360 * 16 * max(0.0, min(1.0, ring))))         # (from the bottom, round)


def draw_orbs(p, W, H, body, t, alpha=1.0):
    if alpha <= 0.01:
        return
    p.save()
    p.setOpacity(alpha)
    r = max(34.0, H * 0.072)
    m = 22.0
    cy = H - m - 44 - r
    v = body.values()
    left, right = m + 8 + r, W - m - 8 - r
    _orb(p, left, cy, r, v["health"] / 100, QColor(70, 4, 6), QColor(215, 30, 26), v["poison"] / 100,
         QColor(80, 225, 60), t, 0.0)
    _orb(p, right, cy, r, v["sanity"] / 100, QColor(6, 14, 70), QColor(45, 100, 235), v["conscious"] / 100,
         QColor(120, 230, 150), t, 2.0)
    f = QFont(SERIF, 11)
    p.setFont(f)
    for x, lines in ((left, (("Health", v["health"], QColor(225, 70, 60)), ("Poison", v["poison"], QColor(110, 220, 90)))),
                     (right, (("Sanity", v["sanity"], QColor(95, 140, 245)), ("Consciousness", v["conscious"], QColor(130, 225, 155))))):
        for k, (name, val, col) in enumerate(lines):
            p.setPen(QColor(0, 0, 0, 200))
            box = QRectF(x - 90, cy + r + 12 + k * 17, 180, 18)
            p.drawText(box.translated(1, 1), Qt.AlignHCenter, f"{name}  {int(round(val))}")
            p.setPen(col)
            p.drawText(box, Qt.AlignHCenter, f"{name}  {int(round(val))}")
    p.restore()


def draw_danger(p, W, H, body, t):
    """The edge of the view beating, in the colour of each thing that's in danger."""
    crit = body.critical()
    if not crit:
        return
    d = min(W, H) * 0.11
    for k, name in enumerate(crit):
        a = int(150 * pulse(t + k * 0.37))
        if a < 3:
            continue
        c = EDGE[name]
        on, off = QColor(c.red(), c.green(), c.blue(), a), QColor(c.red(), c.green(), c.blue(), 0)
        for x0, y0, x1, y1, rect in ((0, 0, 0, d, QRectF(0, 0, W, d)), (0, H, 0, H - d, QRectF(0, H - d, W, d)),
                                     (0, 0, d, 0, QRectF(0, 0, d, H)), (W, 0, W - d, 0, QRectF(W - d, 0, d, H))):
            g = QLinearGradient(x0, y0, x1, y1)
            g.setColorAt(0, on)
            g.setColorAt(1, off)
            p.fillRect(rect, g)


def draw_death(p, W, H, death, t):
    """The silk over his eyes; the dark; and the line."""
    def at(u, v):
        return QPointF(u * W, (1 - v) * H)
    veil = min(1.0, len(death.webs) / 70.0)                    # (a milky film over his eyes, thickening)
    p.fillRect(QRectF(0, 0, W, H), QColor(200, 205, 215, int(28 * veil)))
    for glow, width, alpha in ((True, 3.0, 14), (False, 1.0, 82)):
        p.setPen(QPen(QColor(235, 238, 245, alpha), width, Qt.SolidLine, Qt.RoundCap))
        p.setBrush(Qt.NoBrush)
        for w in death.webs:
            k = w.get("drawn", 1.0)
            if w["kind"] == "strand":
                (u0, v0), (u1, v1), sag = w["a"], w["b"], w["sag"]
                mu, mv = (u0 + u1) / 2 - (v1 - v0) * sag, (v0 + v1) / 2 + (u1 - u0) * sag
                path = QPainterPath(at(u0, v0))
                n = max(2, int(24 * k))
                for i in range(1, n + 1):
                    s = i / 24
                    u = (1 - s) ** 2 * u0 + 2 * (1 - s) * s * mu + s * s * u1
                    v = (1 - s) ** 2 * v0 + 2 * (1 - s) * s * mv + s * s * v1
                    path.lineTo(at(u, v))
                p.drawPath(path)
            else:
                (cu, cv), r, turn = w["c"], w["r"], w["turn"]
                spokes = 11
                jag = [0.65 + 0.35 * abs(math.sin(turn * 7.3 + i * 2.9)) for i in range(spokes)]    # (torn, uneven)
                for i in range(int(spokes * k)):
                    a = turn + i / spokes * math.tau + 0.2 * math.sin(turn * 3.1 + i)
                    p.drawLine(at(cu, cv), at(cu + math.cos(a) * r * jag[i] * H / W, cv + math.sin(a) * r * jag[i]))
                if k >= 1.0 and not glow:
                    path = QPainterPath()
                    for i in range(spokes * 6):
                        a = turn + i / spokes * math.tau + 0.2 * math.sin(turn * 3.1 + i % spokes)
                        f = (0.18 + 0.8 * i / (spokes * 6)) * jag[i % spokes]
                        pt = at(cu + math.cos(a) * r * f * H / W, cv + math.sin(a) * r * f)
                        path.lineTo(pt) if i else path.moveTo(pt)
                    p.drawPath(path)
    if death.black > 0:
        p.fillRect(QRectF(0, 0, W, H), QColor(0, 0, 0, int(255 * death.black)))
    if death.done:
        from ..game.death import ENDING
        age = death.t - 21.4
        a = max(0.0, min(1.0, age / 2.0))
        f = QFont(SERIF, 15)
        f.setItalic(True)
        p.setFont(f)
        p.setPen(QColor(205, 190, 175, int(220 * a)))
        p.drawText(QRectF(0, H * 0.45, W, 30), Qt.AlignHCenter, ENDING[1])
        p.setFont(QFont(SERIF, 10))
        p.setPen(QColor(170, 160, 150, int(200 * max(0.0, min(1.0, (age - 1.5) / 2.0)))))
        p.drawText(QRectF(0, H * 0.45 + 44, W, 20), Qt.AlignHCenter, ENDING[0])
        p.setPen(QColor(150, 140, 130, int(150 * max(0.0, min(1.0, (age - 4.0) / 2.0)))))
        p.drawText(QRectF(0, H * 0.88, W, 20), Qt.AlignHCenter, "Click to go back to the title")

