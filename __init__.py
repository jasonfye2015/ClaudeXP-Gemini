"""Claudenites 3-D: a first-person roguelike in the Deep under Thornwick. Claude - an apprentice mage, before he was
anything else - goes down a hundred floors with a wand he builds himself (a body for its rate and speed, parts for
its element, its power, how many bolts and how they fly), finding robes, gloves, boots and rings, and gold and
potions from everything he kills. Ten bands of ten floors, each band its own place and its own guardian; the last
waits on floor 100. He comes home to Thornwick between floors, or with a Scroll of Return; if he falls, he wakes in
the clearing with all he had, all his levels and every skill Mother Wren taught him - but the run starts again.

Its art is Claude and Magic's: the same CC0 figures (KayKit, Quaternius), plants (Quaternius) and stone (ambientCG),
imported by tools/import_cm.py into assets/. Drawn with OpenGL 3.3 (PyOpenGL) in a QOpenGLWidget; the game itself
(game/) is plain Python, played the same by the tests. Three save slots in Saves/claudenites."""
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap, QRadialGradient
from shiboken6 import isValid

from claudecore import host

TITLE = "Claudenites 3-D"
HERE = Path(__file__).resolve().parent
_open = {}


def nites_icon():
    """A wand's glow in the dark of the Deep."""
    pm = QPixmap(32, 32)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setBrush(QColor("#120E14"))
    p.setPen(QPen(QColor("#5A4630"), 1))
    p.drawRoundedRect(QRectF(1, 1, 30, 30), 5, 5)
    p.setPen(QPen(QColor("#B07A40"), 3))
    p.drawLine(QPointF(8, 26), QPointF(20, 12))
    g = QRadialGradient(QPointF(22, 10), 9)
    g.setColorAt(0, QColor("#FFFFFF"))
    g.setColorAt(0.35, QColor("#B080FF"))
    g.setColorAt(1, QColor(176, 128, 255, 0))
    p.setPen(Qt.NoPen)
    p.setBrush(g)
    p.drawEllipse(QPointF(22, 10), 9, 9)
    p.end()
    return QIcon(pm)


def launch(desktop):
    win = _open.get("win")
    if win is not None and isValid(win):
        desktop.open_window(win)
        return win
    from .ui.shell import Shell
    body = Shell(host.saves("claudenites"), host.muted)
    win = host.window(desktop, TITLE, body, nites_icon(), (1280, 800))
    body.frame = win
    _open["win"] = win
    desktop.open_window(win)
    return win


def shutdown():
    win = _open.get("win")
    if win is not None and isValid(win):
        try:
            win.content.save()
        except Exception:
            pass
