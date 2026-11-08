"""Claude's own state, drawn over the view: two glass orbs at the bottom corners, each holding two fluids - health
(red) on the left with poison (green) rising under it from the bottom, sanity (blue) on the right with stupor (yellow)
rising under it - and their numbers under them in their colours. When the green comes near the other, the edge of the
view beats; when it reaches it, he's done.

And the end of him: the silk laid across his eyes, the dark coming down, and the ending's line."""
import math

import numpy as np
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainterPath, QPen, QRadialGradient

from ..game.condition import pulse

SERIF = "Georgia"
EDGE = {"health": (QColor(210, 25, 20), QColor(70, 220, 60)),          # (red, then green, beat by beat)
        "sanity": (QColor(40, 90, 240), QColor(235, 205, 40))}        # (blue, then yellow)
BEAT = 1.1


def _fluid(p, cx, cy, r, level, deep, bright, t, seed, alpha=255):
    """A fluid in the orb up to `level` (0..1), its surface moving."""
    top = cy + r - 2 * r * max(0.0, min(1.0, level))
    surf = QPainterPath()
    surf.moveTo(cx - r, cy + r + 2)
    for k in range(25):
        x = cx - r + 2 * r * k / 24
        y = top + 2.2 * math.sin(t * 2.1 + k * 0.55 + seed) + 1.4 * math.sin(t * 3.3 - k * 0.9 + seed)
        surf.lineTo(x, y)
    surf.lineTo(cx + r, cy + r + 2)
    surf.closeSubpath()
    lg = QLinearGradient(0, top, 0, cy + r)
    lg.setColorAt(0, QColor(bright.red(), bright.green(), bright.blue(), alpha))
    lg.setColorAt(1, QColor(deep.red(), deep.green(), deep.blue(), alpha))
    p.setBrush(lg)
    p.drawPath(surf)
    if level > 0.01:                                       # (a bright line where its surface is)
        edge = QPainterPath()
        for k in range(25):
            x = cx - r + 2 * r * k / 24
            y = top + 2.2 * math.sin(t * 2.1 + k * 0.55 + seed) + 1.4 * math.sin(t * 3.3 - k * 0.9 + seed)
            edge.lineTo(x, y) if k else edge.moveTo(x, y)
        p.setPen(QPen(QColor(min(255, bright.red() + 60), min(255, bright.green() + 60), min(255, bright.blue() + 60), 150), 1.2))
        p.setBrush(Qt.NoBrush)
        p.drawPath(edge)
        p.setPen(Qt.NoPen)


def _orb(p, cx, cy, r, level, deep, bright, rising, rdeep, rbright, t, seed):
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
    _fluid(p, cx, cy, r, level, deep, bright, t, seed)
    if rising > 0.004:                                     # (the green, rising under it: where they meet, he's done)
        _fluid(p, cx, cy, r, rising, rdeep, rbright, t * 0.8, seed + 2.7, 235)
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
         QColor(14, 70, 10), QColor(90, 225, 55), t, 0.0)
    _orb(p, right, cy, r, v["sanity"] / 100, QColor(6, 14, 70), QColor(45, 100, 235), v["stupor"] / 100,
         QColor(90, 70, 6), QColor(240, 205, 50), t, 2.0)
    f = QFont(SERIF, 11)
    p.setFont(f)
    for x, lines in ((left, (("Health", v["health"], QColor(225, 70, 60)), ("Poison", v["poison"], QColor(110, 220, 90)))),
                     (right, (("Sanity", v["sanity"], QColor(95, 140, 245)), ("Stupor", v["stupor"], QColor(235, 205, 70))))):
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
        tk = t + k * BEAT * 0.5                                    # (two at once: beating between each other)
        a = int(150 * pulse(tk - BEAT * 0.25, BEAT))
        if a < 3:
            continue
        c = EDGE[name][int(tk / BEAT) % 2]                         # (each beat the other colour)
        on, off = QColor(c.red(), c.green(), c.blue(), a), QColor(c.red(), c.green(), c.blue(), 0)
        for x0, y0, x1, y1, rect in ((0, 0, 0, d, QRectF(0, 0, W, d)), (0, H, 0, H - d, QRectF(0, H - d, W, d)),
                                     (0, 0, d, 0, QRectF(0, 0, d, H)), (W, 0, W - d, 0, QRectF(W - d, 0, d, H))):
            g = QLinearGradient(x0, y0, x1, y1)
            g.setColorAt(0, on)
            g.setColorAt(1, off)
            p.fillRect(rect, g)


def draw_death(p, W, H, death, t, first=False):
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
            if w["kind"] == "band":                                  # (the wrapping: drawn on its own, below)
                continue
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
    for w in death.webs:                                             # (the bands of the wrapping: thick, milky, many-threaded)
        if w["kind"] != "band":
            continue
        k = w.get("drawn", 1.0)
        (u0, v0), (u1, v1), sag = w["a"], w["b"], w["sag"]
        mu, mv = (u0 + u1) / 2 - (v1 - v0) * sag, (v0 + v1) / 2 + (u1 - u0) * sag
        path = QPainterPath(at(u0, v0))
        for i in range(1, max(2, int(30 * k)) + 1):
            s_ = i / 30
            path.lineTo(at((1 - s_) ** 2 * u0 + 2 * (1 - s_) * s_ * mu + s_ * s_ * u1,
                           (1 - s_) ** 2 * v0 + 2 * (1 - s_) * s_ * mv + s_ * s_ * v1))
        wpx = w["width"] * H
        p.setPen(QPen(QColor(225, 228, 235, 70), wpx, Qt.SolidLine, Qt.FlatCap))
        p.drawPath(path)
        for off in (-0.33, 0.0, 0.33):                               # (the threads it's twisted from)
            p.setPen(QPen(QColor(245, 247, 252, 70), 1.0))
            p.drawPath(path.translated(0, off * wpx))
    if death.black > 0:
        p.fillRect(QRectF(0, 0, W, H), QColor(0, 0, 0, int(255 * death.black)))
    if death.done:
        from ..game.death import ENDING
        age = death.t - 24.4
        a = max(0.0, min(1.0, age / 2.0))
        f = QFont(SERIF, 15)
        f.setItalic(True)
        p.setFont(f)
        p.setPen(QColor(205, 190, 175, int(220 * a)))
        p.drawText(QRectF(0, H * 0.45, W, 30), Qt.AlignHCenter, ENDING[1])
        p.setFont(QFont(SERIF, 10))
        p.setPen(QColor(170, 160, 150, int(200 * max(0.0, min(1.0, (age - 1.5) / 2.0)))))
        p.drawText(QRectF(0, H * 0.45 + 44, W, 20), Qt.AlignHCenter, ENDING[0])
        if first:
            p.setPen(QColor(200, 170, 120, int(180 * max(0.0, min(1.0, (age - 2.5) / 2.0)))))
            p.drawText(QRectF(0, H * 0.45 + 64, W, 20), Qt.AlignHCenter, "(found for the first time)")
        p.setPen(QColor(150, 140, 130, int(150 * max(0.0, min(1.0, (age - 4.0) / 2.0)))))
        p.drawText(QRectF(0, H * 0.88, W, 20), Qt.AlignHCenter, "Click to go back to the title")



def draw_heart(p, W, H, body, alpha=1.0, span=6.0):
    """His heart, at the bottom of the view between the orbs: the trace running right to left (each beat a small rise,
    the sharp spike and its dip, a slow swell after), the last minute of its rate faint behind it, and the rate."""
    if alpha <= 0.01:
        return
    p.save()
    p.setOpacity(alpha)
    w, h = min(300.0, W * 0.24), max(58.0, H * 0.085)
    x0, y0 = (W - w) / 2, H - 22 - h
    box = QRectF(x0, y0, w, h)
    p.setPen(QPen(QColor(92, 74, 58, 200), 1.2))
    p.setBrush(QColor(6, 4, 6, 175))
    p.drawRoundedRect(box, 6, 6)
    plot = QRectF(x0 + 8, y0 + 8, w - 74, h - 16)
    p.setPen(QPen(QColor(60, 30, 30, 120), 1))                       # (a faint grid, like the paper)
    for k in range(1, 6):
        x = plot.left() + plot.width() * k / 6
        p.drawLine(QPointF(x, plot.top()), QPointF(x, plot.bottom()))
    p.drawLine(QPointF(plot.left(), plot.center().y()), QPointF(plot.right(), plot.center().y()))
    if len(body.history) > 1:                                         # (the last minute of it, faint)
        path = QPainterPath()
        n = len(body.history)
        for i, b in enumerate(body.history):
            x = plot.right() - (n - 1 - i) / 119 * plot.width()
            y = plot.bottom() - max(0.0, min(1.0, (b - 40) / 140)) * plot.height()
            path.lineTo(x, y) if i else path.moveTo(x, y)
        p.setPen(QPen(QColor(200, 120, 90, 70), 1.2))
        p.setBrush(Qt.NoBrush)
        p.drawPath(path)
    now = body.t
    beats = np.array([b for b in body.beats if now - b < span + 0.6])
    mid, amp = plot.center().y() + plot.height() * 0.18, plot.height() * 0.62
    times = [np.linspace(now - span, now, 60)]                         # (the flat between beats: a few points)
    for b in beats:                                                    # (each beat: finely, so its spike is never missed)
        times.append(np.arange(b - 0.3, b + 0.45, 0.004))
    tt = np.unique(np.clip(np.concatenate(times), now - span, now))
    v = np.zeros_like(tt)
    for b in beats:
        d = tt - b
        v += (0.12 * np.exp(-((d + 0.17) / 0.035) ** 2) - 0.14 * np.exp(-((d + 0.025) / 0.012) ** 2)
              + np.exp(-(d / 0.013) ** 2) - 0.28 * np.exp(-((d - 0.03) / 0.014) ** 2)
              + 0.22 * np.exp(-((d - 0.26) / 0.06) ** 2))
    xs = plot.right() - (now - tt) / span * plot.width()
    ys = mid - v * amp
    trace = QPainterPath(QPointF(float(xs[0]), float(ys[0])))          # (the trace, running right to left)
    for x, y in zip(xs[1:], ys[1:]):
        trace.lineTo(float(x), float(y))
    for width, col in ((4.0, QColor(255, 70, 60, 45)), (1.4, QColor(255, 120, 105, 230))):
        p.setPen(QPen(col, width))
        p.drawPath(trace)
    last = now - float(beats[-1]) if len(beats) else 9.0                           # (the heart itself, pulsing with each beat)
    k = max(0.0, 1.0 - last / 0.25)
    cx, cy, s = x0 + w - 33, y0 + h * 0.36, 7.0 + 3.0 * k
    heart = QPainterPath()
    heart.moveTo(cx, cy + s * 0.9)
    heart.cubicTo(cx - s * 1.6, cy - s * 0.1, cx - s * 0.7, cy - s * 1.3, cx, cy - s * 0.45)
    heart.cubicTo(cx + s * 0.7, cy - s * 1.3, cx + s * 1.6, cy - s * 0.1, cx, cy + s * 0.9)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(200 + int(55 * k), 30, 30, 230))
    p.drawPath(heart)
    bpm = int(round(body.bpm)) if body.bpm >= 1 else 0
    p.setPen(QColor(255, 150, 135))
    p.setFont(QFont(SERIF, 13, QFont.Bold))
    p.drawText(QRectF(x0 + w - 66, y0 + h * 0.52, 66, 20), Qt.AlignHCenter, str(bpm))
    p.setFont(QFont(SERIF, 7))
    p.setPen(QColor(200, 150, 140))
    p.drawText(QRectF(x0 + w - 66, y0 + h * 0.52 + 18, 66, 12), Qt.AlignHCenter, "BPM")
    p.restore()
