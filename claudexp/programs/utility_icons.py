"""Icons for Nero Burning ROM, Alcohol 120%, WinRAR, and WinZip."""
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (QBrush, QColor, QFont, QIcon, QLinearGradient, QPainter,
                          QPainterPath, QPen, QPixmap, QPolygonF)


def nero_icon(size=32):
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)

    # Optical disc base tilted
    dg = QLinearGradient(0, 0, size, size)
    dg.setColorAt(0.0, QColor("#FFFFFF"))
    dg.setColorAt(0.3, QColor("#E8E0D0"))
    dg.setColorAt(0.7, QColor("#D0B890"))
    dg.setColorAt(1.0, QColor("#A07840"))
    p.setBrush(dg)
    p.setPen(QPen(QColor("#705020"), 1))
    p.drawEllipse(QRectF(size * 0.08, size * 0.18, size * 0.84, size * 0.74))

    # Center hole
    p.setBrush(QColor("#ECE9D8"))
    p.setPen(QPen(QColor("#907040"), 1))
    p.drawEllipse(QRectF(size * 0.38, size * 0.43, size * 0.24, size * 0.24))

    # Colosseum / roman architecture silhouette base
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#4A2810"))
    p.drawRoundedRect(QRectF(size * 0.18, size * 0.52, size * 0.64, size * 0.32), 2, 2)
    # Colosseum arches
    p.setBrush(QColor("#D87010"))
    for i in range(4):
        p.drawRoundedRect(QRectF(size * (0.24 + i * 0.14), size * 0.60, size * 0.09, size * 0.18), 1, 1)

    # Burning flames rising from the Colosseum
    flame = QPainterPath()
    flame.moveTo(size * 0.15, size * 0.60)
    flame.quadTo(size * 0.25, size * 0.35, size * 0.35, size * 0.12)
    flame.quadTo(size * 0.45, size * 0.32, size * 0.52, size * 0.06)
    flame.quadTo(size * 0.60, size * 0.28, size * 0.70, size * 0.16)
    flame.quadTo(size * 0.82, size * 0.38, size * 0.85, size * 0.60)
    flame.closeSubpath()

    fg = QLinearGradient(0, size * 0.60, 0, 0)
    fg.setColorAt(0.0, QColor("#D01000"))
    fg.setColorAt(0.4, QColor("#FF6800"))
    fg.setColorAt(0.8, QColor("#FFCC00"))
    fg.setColorAt(1.0, QColor("#FFFFE0"))
    p.setBrush(fg)
    p.drawPath(flame)

    # Inner intense flame core
    core = QPainterPath()
    core.moveTo(size * 0.30, size * 0.60)
    core.quadTo(size * 0.40, size * 0.38, size * 0.50, size * 0.22)
    core.quadTo(size * 0.60, size * 0.38, size * 0.70, size * 0.60)
    core.closeSubpath()
    cg = QLinearGradient(0, size * 0.60, 0, size * 0.22)
    cg.setColorAt(0.0, QColor("#FFA000"))
    cg.setColorAt(1.0, QColor("#FFFFFF"))
    p.setBrush(cg)
    p.drawPath(core)

    p.end()
    return QIcon(pm)


def alcohol_icon(size=32):
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)

    # Optical disc in background
    dg = QLinearGradient(0, 0, size, size)
    dg.setColorAt(0.0, QColor("#EAF4FE"))
    dg.setColorAt(0.5, QColor("#99C0F6"))
    dg.setColorAt(1.0, QColor("#3070D0"))
    p.setBrush(dg)
    p.setPen(QPen(QColor("#2050A0"), 1))
    p.drawEllipse(QRectF(size * 0.08, size * 0.08, size * 0.84, size * 0.84))

    # Center hole of disc
    p.setBrush(QColor("#ECE9D8"))
    p.setPen(QPen(QColor("#4070B0"), 1))
    p.drawEllipse(QRectF(size * 0.38, size * 0.38, size * 0.24, size * 0.24))

    # Blue flask / potion bottle shape
    flask = QPainterPath()
    flask.moveTo(size * 0.42, size * 0.16)
    flask.lineTo(size * 0.58, size * 0.16)
    flask.lineTo(size * 0.58, size * 0.34)
    flask.lineTo(size * 0.82, size * 0.76)
    flask.quadTo(size * 0.82, size * 0.86, size * 0.72, size * 0.86)
    flask.lineTo(size * 0.28, size * 0.86)
    flask.quadTo(size * 0.18, size * 0.86, size * 0.18, size * 0.76)
    flask.lineTo(size * 0.42, size * 0.34)
    flask.closeSubpath()

    # Flask liquid fill
    lg = QLinearGradient(0, size * 0.86, 0, size * 0.2)
    lg.setColorAt(0.0, QColor("#0044BB"))
    lg.setColorAt(0.6, QColor("#0088FF"))
    lg.setColorAt(1.0, QColor("#80D0FF"))
    p.setBrush(lg)
    p.setPen(QPen(QColor("#002277"), 1.2))
    p.drawPath(flask)

    # Bubbles inside flask
    p.setBrush(QColor("#E0F4FF"))
    p.setPen(Qt.NoPen)
    p.drawEllipse(QRectF(size * 0.40, size * 0.68, size * 0.08, size * 0.08))
    p.drawEllipse(QRectF(size * 0.54, size * 0.58, size * 0.11, size * 0.11))
    p.drawEllipse(QRectF(size * 0.34, size * 0.52, size * 0.07, size * 0.07))
    p.drawEllipse(QRectF(size * 0.62, size * 0.72, size * 0.06, size * 0.06))

    # Flask lip
    p.setBrush(QColor("#FFFFFF"))
    p.setPen(QPen(QColor("#002277"), 1))
    p.drawRoundedRect(QRectF(size * 0.38, size * 0.12, size * 0.24, size * 0.06), 1, 1)

    # Highlight glare on left
    p.setPen(QPen(QColor(255, 255, 255, 180), 1.5))
    p.drawLine(QPointF(size * 0.26, size * 0.74), QPointF(size * 0.44, size * 0.38))

    p.end()
    return QIcon(pm)


def winrar_icon(size=32):
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)

    # Three books stacked horizontally: Bottom (Blue), Middle (Green), Top (Red/Burgundy)
    # Book 1 (Bottom, Blue)
    b1 = QLinearGradient(0, size * 0.66, 0, size * 0.88)
    b1.setColorAt(0.0, QColor("#3060C0"))
    b1.setColorAt(0.5, QColor("#1E3F8A"))
    b1.setColorAt(1.0, QColor("#0E2254"))
    p.setBrush(b1)
    p.setPen(QPen(QColor("#081434"), 1))
    p.drawRoundedRect(QRectF(size * 0.10, size * 0.66, size * 0.80, size * 0.20), 2, 2)
    # Pages on right
    p.setBrush(QColor("#FFFDE8"))
    p.drawRect(QRectF(size * 0.84, size * 0.69, size * 0.04, size * 0.14))

    # Book 2 (Middle, Green)
    b2 = QLinearGradient(0, size * 0.44, 0, size * 0.66)
    b2.setColorAt(0.0, QColor("#2EB045"))
    b2.setColorAt(0.5, QColor("#1C782D"))
    b2.setColorAt(1.0, QColor("#0D4417"))
    p.setBrush(b2)
    p.setPen(QPen(QColor("#082A0E"), 1))
    p.drawRoundedRect(QRectF(size * 0.12, size * 0.44, size * 0.76, size * 0.20), 2, 2)
    # Pages on right
    p.setBrush(QColor("#FFFDE8"))
    p.drawRect(QRectF(size * 0.82, size * 0.47, size * 0.04, size * 0.14))

    # Book 3 (Top, Burgundy/Purple)
    b3 = QLinearGradient(0, size * 0.22, 0, size * 0.44)
    b3.setColorAt(0.0, QColor("#B82436"))
    b3.setColorAt(0.5, QColor("#861424"))
    b3.setColorAt(1.0, QColor("#520B16"))
    p.setBrush(b3)
    p.setPen(QPen(QColor("#34060E"), 1))
    p.drawRoundedRect(QRectF(size * 0.14, size * 0.22, size * 0.72, size * 0.20), 2, 2)
    # Pages on right
    p.setBrush(QColor("#FFFDE8"))
    p.drawRect(QRectF(size * 0.80, size * 0.25, size * 0.04, size * 0.14))

    # Leather strap belt wrapped around the books vertically
    p.setBrush(QColor("#4A2810"))
    p.setPen(QPen(QColor("#241206"), 1))
    p.drawRect(QRectF(size * 0.42, size * 0.18, size * 0.16, size * 0.72))

    # Golden buckle on belt
    p.setBrush(QColor("#FFD700"))
    p.setPen(QPen(QColor("#AA8800"), 1))
    p.drawRoundedRect(QRectF(size * 0.38, size * 0.48, size * 0.24, size * 0.14), 1, 1)
    p.setBrush(QColor("#4A2810"))
    p.drawRect(QRectF(size * 0.44, size * 0.52, size * 0.12, size * 0.06))

    p.end()
    return QIcon(pm)


def winzip_icon(size=32):
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)

    # Yellow 2-drawer filing cabinet
    cg = QLinearGradient(0, size * 0.12, 0, size * 0.88)
    cg.setColorAt(0.0, QColor("#FFE066"))
    cg.setColorAt(0.5, QColor("#F4B41A"))
    cg.setColorAt(1.0, QColor("#C68406"))
    p.setBrush(cg)
    p.setPen(QPen(QColor("#8C5B00"), 1))
    p.drawRoundedRect(QRectF(size * 0.16, size * 0.14, size * 0.68, size * 0.74), 2, 2)

    # Drawer line separator
    p.setPen(QPen(QColor("#8C5B00"), 1))
    p.drawLine(QPointF(size * 0.16, size * 0.51), QPointF(size * 0.84, size * 0.51))

    # Drawer handles
    p.setBrush(QColor("#E0E0E0"))
    p.setPen(QPen(QColor("#707070"), 1))
    p.drawRoundedRect(QRectF(size * 0.40, size * 0.30, size * 0.20, size * 0.06), 1, 1)
    p.drawRoundedRect(QRectF(size * 0.40, size * 0.67, size * 0.20, size * 0.06), 1, 1)

    # Metal Vise / clamp around the cabinet squeezing it
    p.setBrush(QColor("#6A7888"))
    p.setPen(QPen(QColor("#33404D"), 1))
    p.drawRect(QRectF(size * 0.06, size * 0.44, size * 0.88, size * 0.14))

    # Vise screw thread & handle
    p.setBrush(QColor("#9EACBC"))
    p.drawRect(QRectF(size * 0.86, size * 0.47, size * 0.10, size * 0.08))
    p.setBrush(QColor("#D02020"))
    p.drawRect(QRectF(size * 0.94, size * 0.38, size * 0.04, size * 0.26))

    p.end()
    return QIcon(pm)


def burn_icon(size=16):
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    # CD with flame
    p.setBrush(QColor("#D8E4F8"))
    p.setPen(QPen(QColor("#6080B0"), 1))
    p.drawEllipse(QRectF(1, 4, size - 3, size - 5))
    flame = QPainterPath()
    flame.moveTo(size * 0.3, size * 0.9)
    flame.quadTo(size * 0.5, size * 0.4, size * 0.7, size * 0.1)
    flame.quadTo(size * 0.9, size * 0.5, size * 0.8, size * 0.9)
    flame.closeSubpath()
    p.setBrush(QColor("#FF4500"))
    p.setPen(Qt.NoPen)
    p.drawPath(flame)
    p.end()
    return QIcon(pm)


def virtual_drive_icon(size=16):
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    # Drive tray
    p.setBrush(QColor("#D0D0D0"))
    p.setPen(QPen(QColor("#606060"), 1))
    p.drawRect(QRectF(1, 3, size - 2, size - 6))
    # Tray slot
    p.setPen(QPen(QColor("#404040"), 1))
    p.drawLine(3, size - 6, size - 4, size - 6)
    # Green LED
    p.setBrush(QColor("#20D020"))
    p.setPen(Qt.NoPen)
    p.drawRect(QRectF(size - 6, size - 8, 2, 2))
    # Disc icon popping out
    p.setBrush(QColor("#80B0FF"))
    p.setPen(QPen(QColor("#2050B0"), 1))
    p.drawEllipse(QRectF(size * 0.25, 1, size * 0.5, size * 0.5))
    p.end()
    return QIcon(pm)

