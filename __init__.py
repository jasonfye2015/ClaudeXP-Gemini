"""The Hollow Oak: one night as the guest of Ysmeine, the Weaver Below - an ancient spider who lives inside the Hollow
Oak - played in first person from dusk to dawn. A serious, eerie romance; the absurdity is never winked at.

This is phase 1 of the build: the tree itself, inside - the root tunnel, the great hollow, the ledge winding up its
wall past the chambers to the broken crown, glowing fungus, moonlight through the knot-holes, fog pooled at the
bottom - walked by lantern-light, and something watching from high in the dark. (The design: "The Hollow Oak - Design
Document", in Claude Docs.)

Drawn with OpenGL 3.3 (PyOpenGL) in a QOpenGLWidget; the night itself (game/) is plain Python, walked the same by the
tests. It stands alone: it shares nothing with the Timeline's other games."""
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap, QRadialGradient
from shiboken6 import isValid

from claudecore import host

TITLE = "The Hollow Oak"
HERE = Path(__file__).resolve().parent
SAVES = None                            # (where its saves go: host.saves("hollowoak") unless a test says otherwise)
_open = {}


def oak_icon():
    """An old oak's black trunk, hollow, and eight small lights in the dark of it."""
    pm = QPixmap(32, 32)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setBrush(QColor("#0C0A10"))
    p.setPen(QPen(QColor("#3A2A1E"), 1))
    p.drawRoundedRect(QRectF(1, 1, 30, 30), 5, 5)
    trunk = QPainterPath()
    trunk.moveTo(7, 30)
    trunk.cubicTo(10, 22, 9, 12, 8, 4)
    trunk.lineTo(24, 4)
    trunk.cubicTo(23, 12, 22, 22, 25, 30)
    trunk.closeSubpath()
    p.setBrush(QColor("#3B2A1F"))
    p.setPen(QPen(QColor("#5C4430"), 1))
    p.drawPath(trunk)
    hollow = QPainterPath()
    hollow.addEllipse(QPointF(16, 17), 4.5, 7.5)
    p.setBrush(QColor("#06050A"))
    p.setPen(Qt.NoPen)
    p.drawPath(hollow)
    for k in range(8):
        x = 13.6 + (k % 4) * 1.6
        y = 14.5 + (k // 4) * 1.8
        g = QRadialGradient(QPointF(x, y), 1.4)
        g.setColorAt(0, QColor(255, 110, 60, 255))
        g.setColorAt(1, QColor(255, 110, 60, 0))
        p.setBrush(g)
        p.drawEllipse(QPointF(x, y), 1.4, 1.4)
    p.end()
    return QIcon(pm)


def launch(desktop):
    win = _open.get("win")
    if win is not None and isValid(win):
        desktop.open_window(win)
        return win
    from .ui.shell import Shell
    body = Shell(SAVES or host.saves("hollowoak"), host.muted)
    win = host.window(desktop, TITLE, body, oak_icon(), (1280, 800))
    body.frame = win
    _open["win"] = win
    desktop.open_window(win)
    return win


def shutdown():
    win = _open.get("win")
    if win is not None and isValid(win):
        try:
            win.content.close_down()
        except Exception:
            pass
