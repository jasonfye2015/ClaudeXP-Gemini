"""Sprite and art rendering for Neko (The Classic Desktop Cat)."""
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (QBrush, QColor, QFont, QIcon, QLinearGradient, QPainter,
                          QPainterPath, QPen, QPixmap, QPolygonF)

PALETTES = {
    "classic": {
        "name": "Classic Calico",
        "body": "#FFFFFF",
        "patch1": "#E67318",
        "patch2": "#282828",
        "eye": "#1B8A3C",
        "nose": "#FF7597",
        "outline": "#1A1A1A",
    },
    "tabby": {
        "name": "Ginger Tabby",
        "body": "#FFA028",
        "patch1": "#D06000",
        "patch2": "#B84800",
        "eye": "#2A8A24",
        "nose": "#FF6888",
        "outline": "#401800",
    },
    "black": {
        "name": "Midnight Black",
        "body": "#1E1E24",
        "patch1": "#1E1E24",
        "patch2": "#1E1E24",
        "eye": "#FFD700",
        "nose": "#383845",
        "outline": "#0A0A0E",
    },
    "white": {
        "name": "Snow White",
        "body": "#FBFBFF",
        "patch1": "#F0F0F8",
        "patch2": "#F0F0F8",
        "eye": "#2E8CF0",
        "nose": "#FFA0B8",
        "outline": "#404050",
    },
    "tuxedo": {
        "name": "Tuxedo",
        "body": "#1A1A22",
        "patch1": "#FFFFFF",
        "patch2": "#FFFFFF",
        "eye": "#26A65B",
        "nose": "#FFA0B8",
        "outline": "#0A0A10",
    },
}


def _draw_ears(p, x1, y1, x2, y2, ear_w, ear_h, pal):
    # Left ear
    p.setBrush(QColor(pal["body"]))
    p.setPen(QPen(QColor(pal["outline"]), 1.1))
    e1 = QPolygonF([QPointF(x1, y1), QPointF(x1 + ear_w * 0.4, y1 - ear_h), QPointF(x1 + ear_w, y1 + ear_h * 0.2)])
    p.drawPolygon(e1)
    # Right ear
    e2 = QPolygonF([QPointF(x2 - ear_w, y2 + ear_h * 0.2), QPointF(x2 - ear_w * 0.4, y2 - ear_h), QPointF(x2, y2)])
    p.drawPolygon(e2)

    # Inner ear pink
    p.setBrush(QColor("#FFAEC9"))
    p.setPen(Qt.NoPen)
    ie1 = QPolygonF([QPointF(x1 + 1, y1), QPointF(x1 + ear_w * 0.4, y1 - ear_h + 2), QPointF(x1 + ear_w - 1, y1)])
    ie2 = QPolygonF([QPointF(x2 - ear_w + 1, y2), QPointF(x2 - ear_w * 0.4, y2 - ear_h + 2), QPointF(x2 - 1, y2)])
    p.drawPolygon(ie1)
    p.drawPolygon(ie2)


def render_sprite(pose="sit", frame=0, palette_name="classic", size=32):
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)

    pal = PALETTES.get(palette_name, PALETTES["classic"])
    s = size / 32.0  # scaling factor

    pen_out = QPen(QColor(pal["outline"]), 1.2 * s)
    pen_out.setJoinStyle(Qt.RoundJoin)
    brush_body = QBrush(QColor(pal["body"]))

    if pose == "sit":
        # Sitting cat facing viewer
        # Tail curled to side
        tail = QPainterPath()
        tail.moveTo(22 * s, 26 * s)
        tail_tip = 28 * s if (frame % 2 == 0) else 26 * s
        tail.quadTo(28 * s, 20 * s, tail_tip, 15 * s)
        p.setPen(QPen(QColor(pal["outline"]), 2.2 * s, Qt.SolidLine, Qt.RoundCap))
        p.drawPath(tail)

        # Body
        p.setPen(pen_out)
        p.setBrush(brush_body)
        p.drawEllipse(QRectF(8 * s, 14 * s, 16 * s, 14 * s))

        # Calico patch
        if palette_name == "classic":
            p.setBrush(QColor(pal["patch1"]))
            p.setPen(Qt.NoPen)
            p.drawEllipse(QRectF(9 * s, 17 * s, 6 * s, 7 * s))

        # Paws
        p.setBrush(brush_body)
        p.setPen(pen_out)
        p.drawEllipse(QRectF(10 * s, 25 * s, 4 * s, 4 * s))
        p.drawEllipse(QRectF(18 * s, 25 * s, 4 * s, 4 * s))

        # Ears
        _draw_ears(p, 9 * s, 10 * s, 23 * s, 10 * s, 4 * s, 5 * s, pal)

        # Head
        p.setBrush(brush_body)
        p.setPen(pen_out)
        p.drawEllipse(QRectF(9 * s, 7 * s, 14 * s, 11 * s))

        if palette_name == "classic":
            p.setBrush(QColor(pal["patch2"]))
            p.setPen(Qt.NoPen)
            p.drawEllipse(QRectF(18 * s, 8 * s, 4 * s, 5 * s))

        # Eyes
        p.setBrush(QColor(pal["eye"]))
        p.setPen(Qt.NoPen)
        p.drawEllipse(QRectF(11.5 * s, 11 * s, 2.5 * s, 3 * s))
        p.drawEllipse(QRectF(18 * s, 11 * s, 2.5 * s, 3 * s))
        p.setBrush(QColor("black"))
        p.drawEllipse(QRectF(12.5 * s, 11.5 * s, 1.2 * s, 2 * s))
        p.drawEllipse(QRectF(19 * s, 11.5 * s, 1.2 * s, 2 * s))

        # Nose & whiskers
        p.setBrush(QColor(pal["nose"]))
        p.drawPolygon(QPolygonF([QPointF(15.5 * s, 14.5 * s), QPointF(16.5 * s, 14.5 * s), QPointF(16 * s, 15.5 * s)]))
        p.setPen(QPen(QColor(pal["outline"]), 0.8 * s))
        p.drawLine(QPointF(11 * s, 14 * s), QPointF(6 * s, 13 * s))
        p.drawLine(QPointF(11 * s, 15 * s), QPointF(6 * s, 16 * s))
        p.drawLine(QPointF(21 * s, 14 * s), QPointF(26 * s, 13 * s))
        p.drawLine(QPointF(21 * s, 15 * s), QPointF(26 * s, 16 * s))

    elif pose == "alert":
        # Cat alert / startled
        # Ears up, exclamation mark above head
        _draw_ears(p, 9 * s, 10 * s, 23 * s, 10 * s, 4 * s, 6 * s, pal)
        # Body
        p.setPen(pen_out)
        p.setBrush(brush_body)
        p.drawEllipse(QRectF(8 * s, 14 * s, 16 * s, 14 * s))
        p.drawEllipse(QRectF(10 * s, 25 * s, 4 * s, 4 * s))
        p.drawEllipse(QRectF(18 * s, 25 * s, 4 * s, 4 * s))
        # Head
        p.drawEllipse(QRectF(9 * s, 7 * s, 14 * s, 11 * s))
        # Big alert eyes
        p.setBrush(QColor(pal["eye"]))
        p.setPen(Qt.NoPen)
        p.drawEllipse(QRectF(11 * s, 10 * s, 3.5 * s, 4 * s))
        p.drawEllipse(QRectF(17.5 * s, 10 * s, 3.5 * s, 4 * s))
        p.setBrush(QColor("black"))
        p.drawEllipse(QRectF(12 * s, 11 * s, 1.8 * s, 2.5 * s))
        p.drawEllipse(QRectF(18.5 * s, 11 * s, 1.8 * s, 2.5 * s))
        # Nose
        p.setBrush(QColor(pal["nose"]))
        p.drawEllipse(QRectF(15.5 * s, 14.5 * s, 1.2 * s, 1 * s))
        # Yellow badge with red '!'
        p.setBrush(QColor("#FFDE00"))
        p.setPen(QPen(QColor("#C02000"), 1 * s))
        p.drawEllipse(QRectF(22 * s, 1 * s, 8 * s, 8 * s))
        p.setFont(QFont("Tahoma", int(6 * s), QFont.Bold))
        p.setPen(QColor("#C02000"))
        p.drawText(QRectF(22 * s, 1 * s, 8 * s, 8 * s), Qt.AlignCenter, "!")

    elif pose == "down":
        # Running towards screen (down)
        f = frame % 2
        # Tail behind
        p.setPen(QPen(QColor(pal["outline"]), 2.2 * s, Qt.SolidLine, Qt.RoundCap))
        tail_x = 13 * s if f == 0 else 19 * s
        p.drawLine(QPointF(16 * s, 14 * s), QPointF(tail_x, 4 * s))

        # Body
        p.setPen(pen_out)
        p.setBrush(brush_body)
        p.drawEllipse(QRectF(9 * s, 12 * s, 14 * s, 13 * s))

        # Paws alternating
        p1_y = 25 * s if f == 0 else 22 * s
        p2_y = 22 * s if f == 0 else 25 * s
        p.drawEllipse(QRectF(8 * s, p1_y, 4 * s, 5 * s))
        p.drawEllipse(QRectF(20 * s, p2_y, 4 * s, 5 * s))

        # Ears & Head
        _draw_ears(p, 9 * s, 10 * s, 23 * s, 10 * s, 4 * s, 5 * s, pal)
        p.setPen(pen_out)
        p.setBrush(brush_body)
        p.drawEllipse(QRectF(9 * s, 7 * s, 14 * s, 11 * s))

        # Eyes & Nose
        p.setBrush(QColor(pal["eye"]))
        p.setPen(Qt.NoPen)
        p.drawEllipse(QRectF(11.5 * s, 11 * s, 2.5 * s, 3 * s))
        p.drawEllipse(QRectF(18 * s, 11 * s, 2.5 * s, 3 * s))
        p.setBrush(QColor(pal["nose"]))
        p.drawEllipse(QRectF(15.5 * s, 14.5 * s, 1.2 * s, 1 * s))

    elif pose == "up":
        # Running away from screen (up, seen from behind)
        f = frame % 2
        # Paws reaching forward
        p.setPen(pen_out)
        p.setBrush(brush_body)
        p1_y = 6 * s if f == 0 else 9 * s
        p2_y = 9 * s if f == 0 else 6 * s
        p.drawEllipse(QRectF(7 * s, p1_y, 4 * s, 5 * s))
        p.drawEllipse(QRectF(21 * s, p2_y, 4 * s, 5 * s))

        # Body
        p.drawEllipse(QRectF(9 * s, 10 * s, 14 * s, 15 * s))

        # Ears (back view)
        p.setBrush(QColor(pal["body"]))
        e1 = QPolygonF([QPointF(9 * s, 12 * s), QPointF(11 * s, 6 * s), QPointF(14 * s, 11 * s)])
        e2 = QPolygonF([QPointF(18 * s, 11 * s), QPointF(21 * s, 6 * s), QPointF(23 * s, 12 * s)])
        p.drawPolygon(e1)
        p.drawPolygon(e2)

        # Head (back)
        p.drawEllipse(QRectF(9 * s, 9 * s, 14 * s, 10 * s))

        # Tail waving back
        tail_x = 10 * s if f == 0 else 22 * s
        p.setPen(QPen(QColor(pal["outline"]), 2.2 * s, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(QPointF(16 * s, 24 * s), QPointF(tail_x, 28 * s))

    elif pose in ("left", "right"):
        # Profile running
        is_r = (pose == "right")
        f = frame % 2

        if is_r:
            p.translate(size, 0)
            p.scale(-1, 1)

        # Tail
        p.setPen(QPen(QColor(pal["outline"]), 2.2 * s, Qt.SolidLine, Qt.RoundCap))
        tail = QPainterPath()
        tail.moveTo(22 * s, 16 * s)
        tail.quadTo(28 * s, 14 * s, 27 * s, 8 * s if f == 0 else 11 * s)
        p.drawPath(tail)

        # Body
        p.setPen(pen_out)
        p.setBrush(brush_body)
        p.drawEllipse(QRectF(10 * s, 12 * s, 14 * s, 10 * s))

        # Legs (extended vs contracted)
        if f == 0:
            # Extended stride
            p.drawEllipse(QRectF(6 * s, 17 * s, 6 * s, 4 * s))  # front leg forward
            p.drawEllipse(QRectF(18 * s, 18 * s, 6 * s, 4 * s)) # back leg back
        else:
            # Contracted stride
            p.drawEllipse(QRectF(9 * s, 18 * s, 5 * s, 5 * s))
            p.drawEllipse(QRectF(15 * s, 18 * s, 5 * s, 5 * s))

        # Ear
        p.setBrush(QColor(pal["body"]))
        ear = QPolygonF([QPointF(7 * s, 9 * s), QPointF(9 * s, 4 * s), QPointF(12 * s, 8 * s)])
        p.drawPolygon(ear)

        # Head
        p.drawEllipse(QRectF(5 * s, 8 * s, 10 * s, 10 * s))

        # Eye
        p.setBrush(QColor(pal["eye"]))
        p.setPen(Qt.NoPen)
        p.drawEllipse(QRectF(7 * s, 11 * s, 2.5 * s, 3 * s))
        p.setBrush(QColor(pal["nose"]))
        p.drawEllipse(QRectF(4.5 * s, 13 * s, 1.5 * s, 1.2 * s))

        if is_r:
            p.resetTransform()

    elif pose in ("upleft", "upright", "downleft", "downright"):
        # Diagonal runs: slight rotation
        is_r = "right" in pose
        is_u = "up" in pose
        f = frame % 2

        if is_r:
            p.translate(size, 0)
            p.scale(-1, 1)

        p.save()
        rot = -25 if is_u else 20
        p.translate(16 * s, 16 * s)
        p.rotate(rot)
        p.translate(-16 * s, -16 * s)

        # Draw left profile tilted
        p.setPen(pen_out)
        p.setBrush(brush_body)
        p.drawEllipse(QRectF(10 * s, 12 * s, 14 * s, 10 * s))
        leg_dx = 3 * s if f == 0 else -2 * s
        p.drawEllipse(QRectF((7 + leg_dx) * s, 18 * s, 5 * s, 5 * s))
        p.drawEllipse(QRectF((17 - leg_dx) * s, 18 * s, 5 * s, 5 * s))
        _draw_ears(p, 5 * s, 9 * s, 13 * s, 9 * s, 3 * s, 4 * s, pal)
        p.setBrush(brush_body)
        p.setPen(pen_out)
        p.drawEllipse(QRectF(5 * s, 8 * s, 10 * s, 10 * s))
        p.restore()

        if is_r:
            p.resetTransform()

    elif pose == "sleep":
        # Curled up sleeping cat
        f = frame % 2
        # Curled body oval
        p.setPen(pen_out)
        p.setBrush(brush_body)
        rise = 0.5 * s if f == 1 else 0.0
        p.drawEllipse(QRectF(6 * s, (15 - rise) * s, 20 * s, 13 * s))

        # Tail wrapped around
        p.setPen(QPen(QColor(pal["outline"]), 2 * s))
        tail = QPainterPath()
        tail.moveTo(24 * s, 21 * s)
        tail.quadTo(20 * s, 26 * s, 10 * s, 26 * s)
        p.drawPath(tail)

        # Curled head
        p.setPen(pen_out)
        p.setBrush(brush_body)
        p.drawEllipse(QRectF(7 * s, 16 * s, 10 * s, 9 * s))
        # Small closed ear
        p.drawPolygon(QPolygonF([QPointF(10 * s, 16 * s), QPointF(12 * s, 12 * s), QPointF(15 * s, 15 * s)]))

        # Closed sleeping eyes (^ ^)
        p.setPen(QPen(QColor(pal["outline"]), 1.2 * s))
        p.drawArc(QRectF(9 * s, 18 * s, 3 * s, 2 * s), 0, 180 * 16)
        p.drawArc(QRectF(13 * s, 18 * s, 3 * s, 2 * s), 0, 180 * 16)

        # "Zzz" drifting above
        p.setPen(QColor("#2070D0"))
        p.setFont(QFont("Tahoma", int(6 * s), QFont.Bold))
        z_y = 10 * s if f == 0 else 7 * s
        p.drawText(QRectF(18 * s, z_y, 12 * s, 8 * s), Qt.AlignCenter, "Zzz" if f == 1 else "z")

    elif pose == "yawn":
        # Yawning and stretching
        p.setPen(pen_out)
        p.setBrush(brush_body)
        # Front paws stretched far out
        p.drawEllipse(QRectF(4 * s, 24 * s, 7 * s, 4 * s))
        # Body sloped
        p.drawEllipse(QRectF(11 * s, 13 * s, 14 * s, 12 * s))
        # Tail high up
        p.setPen(QPen(QColor(pal["outline"]), 2.2 * s, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(QPointF(23 * s, 15 * s), QPointF(26 * s, 6 * s))
        # Head
        _draw_ears(p, 6 * s, 14 * s, 14 * s, 14 * s, 3 * s, 4 * s, pal)
        p.setPen(pen_out)
        p.setBrush(brush_body)
        p.drawEllipse(QRectF(6 * s, 12 * s, 10 * s, 10 * s))
        # Open mouth (pink triangle)
        p.setBrush(QColor("#FF4080"))
        p.drawPolygon(QPolygonF([QPointF(9 * s, 17 * s), QPointF(13 * s, 17 * s), QPointF(11 * s, 21 * s)]))

    elif pose == "scratch":
        # Scratching ear with hind paw
        f = frame % 2
        p.setPen(pen_out)
        p.setBrush(brush_body)
        p.drawEllipse(QRectF(8 * s, 14 * s, 15 * s, 13 * s))
        # Head tilted
        p.save()
        p.translate(13 * s, 12 * s)
        p.rotate(-15)
        p.translate(-13 * s, -12 * s)
        _draw_ears(p, 9 * s, 10 * s, 21 * s, 10 * s, 3.5 * s, 4.5 * s, pal)
        p.setBrush(brush_body)
        p.setPen(pen_out)
        p.drawEllipse(QRectF(9 * s, 8 * s, 12 * s, 10 * s))
        p.restore()
        # Raised scratch foot
        scratch_y = (11 if f == 0 else 13) * s
        p.setPen(pen_out)
        p.setBrush(brush_body)
        p.drawEllipse(QRectF(20 * s, scratch_y, 5 * s, 7 * s))
        # Scratch motion marks
        p.setPen(QPen(QColor("#808080"), 1 * s))
        p.drawLine(QPointF(26 * s, 10 * s), QPointF(29 * s, 9 * s))
        p.drawLine(QPointF(26 * s, 13 * s), QPointF(29 * s, 13 * s))

    elif pose == "pet":
        # Happy purring cat with hearts
        p.setPen(pen_out)
        p.setBrush(brush_body)
        p.drawEllipse(QRectF(8 * s, 14 * s, 16 * s, 14 * s))
        _draw_ears(p, 9 * s, 10 * s, 23 * s, 10 * s, 4 * s, 5 * s, pal)
        p.setBrush(brush_body)
        p.drawEllipse(QRectF(9 * s, 7 * s, 14 * s, 11 * s))
        # Happy closed squint eyes (^ ^)
        p.setPen(QPen(QColor(pal["outline"]), 1.5 * s))
        p.drawArc(QRectF(11 * s, 11 * s, 3 * s, 3 * s), 0, 180 * 16)
        p.drawArc(QRectF(18 * s, 11 * s, 3 * s, 3 * s), 0, 180 * 16)
        # Floating heart
        f_y = (2 if frame % 2 == 0 else 4) * s
        p.setBrush(QColor("#FF2060"))
        p.setPen(Qt.NoPen)
        heart = QPainterPath()
        heart.moveTo(22 * s, f_y + 3 * s)
        heart.cubicTo(20 * s, f_y, 17 * s, f_y + 2 * s, 22 * s, f_y + 6 * s)
        heart.cubicTo(27 * s, f_y + 2 * s, 24 * s, f_y, 22 * s, f_y + 3 * s)
        p.drawPath(heart)

    p.end()
    return pm


def neko_icon(size=32):
    """Program / Start menu icon for Neko."""
    return QIcon(render_sprite("sit", 0, "classic", size))


def paw_icon(size=32):
    """A small paw print for Neko's notification-area icon."""
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    s = size / 32.0
    p.setPen(QPen(QColor("#5A3545"), 1.2 * s))
    p.setBrush(QColor("#F59AB5"))
    p.drawEllipse(QRectF(7 * s, 16 * s, 18 * s, 13 * s))
    for x, y, w, h in ((4, 8, 7, 9), (11, 3, 7, 10), (20, 3, 7, 10), (25, 8, 6, 9)):
        p.drawEllipse(QRectF(x * s, y * s, w * s, h * s))
    p.end()
    return QIcon(pm)
