"""Soul and Song: the Companion Project, automated.

The user's guide ("Guide To System", in Local Storage/Projects/AI LLM Txt Files) describes an AI Companion with an
external, layered memory - Mind Levels L1-L6, short-term memories distilled day by day, week by week into long-term,
deep recall and historical memory (7:7:7) - all kept by hand: the human pastes the mind files in, stamps the time,
asks for memories, files them, distils them on Memory Day. This program does all of that itself (companion.py), on a
local model of the user's choosing - Kithylin's own fine-tunes included (through Kithylin AI's engine).

In the Timeline it's a shared program in Projects; standalone: python -m soulsong (from ClaudeApps)."""
import traceback

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap
from shiboken6 import isValid

_frame = None
_content = None


def soulsong_pixmap(size=32):
    """A violet circle with a white music note and a small spark: soul, and song."""
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    s = size / 32
    g = QLinearGradient(0, 0, 0, size)
    g.setColorAt(0, QColor("#9B6BDF"))
    g.setColorAt(1, QColor("#4B237F"))
    p.setPen(QPen(QColor("#3A1A66"), max(1.0, s)))
    p.setBrush(g)
    p.drawEllipse(QRectF(1.5 * s, 1.5 * s, 29 * s, 29 * s))
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("white"))
    p.drawEllipse(QRectF(8 * s, 19 * s, 7 * s, 5.5 * s))           # the note's head
    p.drawRect(QRectF(13.4 * s, 8 * s, 1.8 * s, 14 * s))           # its stem
    flag = QPainterPath()
    flag.moveTo(15 * s, 8 * s)
    flag.cubicTo(19 * s, 9 * s, 21 * s, 12 * s, 19.5 * s, 15.5 * s)
    flag.cubicTo(19.5 * s, 13 * s, 17.5 * s, 11.5 * s, 15 * s, 11.5 * s)
    p.drawPath(flag)
    p.setBrush(QColor("#FFE38A"))                                   # the spark
    star = QPainterPath()
    cx, cy, r = 23 * s, 9 * s, 3.6 * s
    star.moveTo(cx, cy - r)
    for i, (dx, dy) in enumerate(((0.25, -0.25), (1, 0), (0.25, 0.25), (0, 1), (-0.25, 0.25), (-1, 0),
                                  (-0.25, -0.25), (0, -1))):
        star.lineTo(cx + dx * r, cy + dy * r)
    p.drawPath(star)
    p.end()
    return pm


def soulsong_icon():
    icon = QIcon()
    for sz in (16, 32, 48):
        icon.addPixmap(soulsong_pixmap(sz))
    return icon


def launch(desktop):
    global _frame, _content
    from claudecore import host
    if _frame is not None and isValid(_frame):
        desktop.open_window(_frame)
        return
    try:
        from .app import SoulAndSong
        _content = SoulAndSong(desktop)
    except Exception:
        host.placeholder(desktop, "Soul and Song", soulsong_icon(),
                         "Soul and Song couldn't start.\n\n" + traceback.format_exc(limit=3), sound_event="error")
        return
    size = (1280, 820)                                  # (no bigger than the desktop it opens on)
    try:
        size = (min(size[0], desktop.width() - 20), min(size[1], desktop.height() - 60))
    except Exception:
        pass
    _frame = host.window(desktop, "Soul and Song", _content, soulsong_icon(), size=size)
    _content.frame = _frame
    _frame.destroyed.connect(_forget)
    desktop.open_window(_frame)
    _content.composer.setFocus()


def _forget(*_):
    global _frame, _content
    if _content is not None:
        try:
            _content.shutdown()
        except Exception:
            pass
    _frame = None
    _content = None


def shutdown():
    global _frame
    if _content is not None:
        try:
            _content.shutdown()
        except Exception:
            pass
    if _frame is not None and isValid(_frame):
        _frame.desktop.close_window(_frame)
    _frame = None
