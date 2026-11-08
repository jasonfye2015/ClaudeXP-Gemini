"""Three things he carries, each on its own screen: her letter (silk, in her hand - front and back; read before the
night, and again from the pause), his notebook (what he's learned of her, written as he learns it, kept across
nights; flipped through), and what's been unlocked so far."""
import math
import random

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QFontMetrics, QLinearGradient, QPainter, QPainterPath, QPen, QRadialGradient
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QVBoxLayout, QWidget

from . import fonts
from ..game import notes as NOTES
from ..game.records import ENDINGS

SERIF = "Georgia"
BUTTONS = """QPushButton { color: #E6D8C2; background: rgba(24, 16, 13, 210); border: 1px solid #5C4632; border-radius: 4px;
    padding: 8px 22px; font-family: Georgia; font-size: 14px; }
QPushButton:hover { background: rgba(70, 40, 28, 230); border-color: #A07A54; color: #FFF0DA; }"""

FRONT = ("Little wizard -", "", "I have heard you in my forest,", "asking the trees what they know.",
         "They know very little.", "I know a great deal.", "", "Come at dusk. Come alone.", "Come hungry for knowing.",
         "", "- Y.")
BACK = ("By the roots of the Hollow Oak,", "past the Fairy Ring,", "where nothing grows.", "", "Bring no fire.")
INTENT = ("It was on your doorstep at sundown: a square of silk, finer than anything woven in Thornwick, written in a "
          "hand that seems to move when you look away. You have read it a hundred times since.\n\n"
          "You know what it is. Everyone in Thornwick knows what lives in the Hollow Oak, and what became of the ones "
          "who went before. You mean to go anyway - not because you are brave, but because you are hungry: for what "
          "she knows, for what no master in Thornwick will teach you.\n\n"
          "And because the silk will not let you put it down. It is damp with something sweet and faintly bitter; your "
          "fingertips have been numb since you first touched it, and your thoughts keep turning, slow and warm, to "
          "the oak. Her venom, you think - and something else beneath it, something meant for you, that makes the "
          "invitation impossible to refuse.")


def _button(text, fn):
    b = QPushButton(text)
    b.setCursor(Qt.PointingHandCursor)
    b.clicked.connect(fn)
    return b


class _Screen(QWidget):
    """A full screen of its own, with a row of buttons at its foot; Esc does the last of them."""

    def __init__(self, shell, buttons):
        super().__init__(shell)
        self.shell = shell
        self.setStyleSheet(BUTTONS)
        lay = QVBoxLayout(self)
        lay.addStretch(1)
        row = QHBoxLayout()
        row.addStretch(1)
        self.actions = []
        for text, fn in buttons:
            b = _button(text, fn)
            row.addWidget(b)
            self.actions.append(fn)
        row.addStretch(1)
        lay.addLayout(row)
        lay.setContentsMargins(20, 20, 20, 26)
        self.setFocusPolicy(Qt.StrongFocus)

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape and self.actions:
            self.actions[-1]()
            return
        super().keyPressEvent(e)

    def backdrop(self, p):
        g = QRadialGradient(QPointF(self.width() / 2, self.height() * 0.45), max(self.width(), self.height()) * 0.7)
        g.setColorAt(0, QColor(18, 12, 12, 238))
        g.setColorAt(1, QColor(2, 1, 2, 250))
        p.fillRect(self.rect(), g)


class Letter(_Screen):
    """Her letter: silk, in her hand. Before the night ("begin"), with what it means to him; or to look at again
    ("view"), from the pause."""

    LEAD = {"led": ("Let it lead you", "\n\nYou don't decide to go. Your feet are already moving."),
            "first": ("Learn the oak", "\n\nThe first night, then. Go slowly; write everything down.")}

    def __init__(self, shell, mode="begin", on_go=None, on_back=None, lead=None):
        buttons = [("Turn it over", self.flip)]
        self.intent = INTENT + (self.LEAD[lead][1] if lead in self.LEAD else "")
        if mode == "begin":
            buttons += [("Not tonight", on_back), (self.LEAD[lead][0] if lead in self.LEAD else "Go to the oak", on_go)]
        else:
            buttons += [("Back", on_back)]
        super().__init__(shell, buttons)
        if mode == "begin":                                # (Esc: not tonight, rather than in)
            self.actions = [self.flip, on_go, on_back]
        self.mode = mode
        self.back = False
        rng = random.Random(5)
        self.fibres = [(rng.random(), rng.random(), rng.uniform(-0.25, 0.25), rng.uniform(0.15, 0.6),
                        rng.randint(8, 30)) for _ in range(260)]
        self.threads = [(rng.random(), rng.uniform(10, 40), rng.uniform(-0.4, 0.4)) for _ in range(14)]

    def flip(self):
        self.back = not self.back
        self.update()

    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        self.backdrop(p)
        W, H = self.width(), self.height()
        lw, lh = min(W * 0.38, H * 0.56), H * 0.74
        x0 = W * 0.08 if self.mode == "begin" else (W - lw) / 2
        r = QRectF(x0, H * 0.07, lw, lh)
        self._silk(p, r)
        p.setPen(QColor(78, 44, 34, 235))
        lines = BACK if self.back else FRONT
        f = fonts.her(self.shell.records, 30 if not self.back else 26)
        p.setFont(f)
        fm = QFontMetrics(f)
        y = r.top() + lh * (0.1 if not self.back else 0.3)
        for line in lines:
            p.drawText(QRectF(r.left() + lw * 0.1, y, lw * 0.8, fm.height()), Qt.AlignLeft | Qt.AlignVCenter, line)
            y += fm.height() * (0.95 if line else 0.5)
        if self.back:
            self._seal(p, QPointF(r.center().x(), r.top() + lh * 0.18))
        if self.mode == "begin":
            p.setFont(QFont(SERIF, 13))
            p.setPen(QColor(214, 200, 182))
            text = QRectF(W * 0.52, H * 0.12, W * 0.4, H * 0.7)
            p.drawText(text, Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap, self.intent)
        p.end()

    def _silk(self, p, r):
        """Pale, faintly translucent, its fibres catching the light, frayed at the edges, threads trailing."""
        path = QPainterPath()
        steps = 60
        pts = []
        for k in range(steps):                                   # (a frayed edge all round)
            u = k / steps
            if u < 0.25:
                x, y = r.left() + r.width() * u * 4, r.top()
            elif u < 0.5:
                x, y = r.right(), r.top() + r.height() * (u - 0.25) * 4
            elif u < 0.75:
                x, y = r.right() - r.width() * (u - 0.5) * 4, r.bottom()
            else:
                x, y = r.left(), r.bottom() - r.height() * (u - 0.75) * 4
            j = 3.5 * math.sin(k * 7.3) + 2.0 * math.sin(k * 2.1)
            pts.append(QPointF(x + j * 0.6, y + j * 0.6))
        path.moveTo(pts[0])
        for q in pts[1:]:
            path.lineTo(q)
        path.closeSubpath()
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(0, 0, 0, 120))
        p.drawPath(path.translated(8, 10))
        g = QLinearGradient(r.topLeft(), r.bottomRight())
        g.setColorAt(0, QColor(238, 234, 224, 246))
        g.setColorAt(0.5, QColor(226, 222, 210, 240))
        g.setColorAt(1, QColor(214, 208, 196, 244))
        p.setBrush(g)
        p.drawPath(path)
        p.save()
        p.setClipPath(path)
        for fx, fy, slope, alpha, length in self.fibres:          # (its weave)
            x, y = r.left() + fx * r.width(), r.top() + fy * r.height()
            p.setPen(QPen(QColor(255, 255, 255, int(70 * alpha)), 0.7))
            p.drawLine(QPointF(x, y), QPointF(x + length, y + length * slope))
            p.setPen(QPen(QColor(150, 140, 120, int(40 * alpha)), 0.6))
            p.drawLine(QPointF(x, y + 1), QPointF(x + length * slope, y + 1 + length))
        sheen = QLinearGradient(r.topLeft(), r.bottomRight())     # (a sheen across it, like a web in the light)
        sheen.setColorAt(0.35, QColor(255, 255, 255, 0))
        sheen.setColorAt(0.5, QColor(255, 255, 255, 46))
        sheen.setColorAt(0.65, QColor(255, 255, 255, 0))
        p.fillRect(r, sheen)
        p.restore()
        p.setPen(QPen(QColor(235, 230, 220, 150), 0.8))           # (threads trailing from its foot)
        for u, length, bend in self.threads:
            x = r.left() + u * r.width()
            q = QPainterPath(QPointF(x, r.bottom()))
            q.quadTo(QPointF(x + bend * length, r.bottom() + length * 0.6), QPointF(x + bend * length * 1.5, r.bottom() + length))
            p.setBrush(Qt.NoBrush)
            p.drawPath(q)

    def _seal(self, p, c):
        """Her mark: a small knot of silk, and eight legs."""
        p.setPen(QPen(QColor(78, 44, 34, 210), 1.6, Qt.SolidLine, Qt.RoundCap))
        for side in (-1, 1):
            for k in range(4):
                a = math.radians(-50 + k * 33)
                knee = QPointF(c.x() + side * math.cos(a) * 18, c.y() + math.sin(a) * 14 - 6)
                foot = QPointF(c.x() + side * math.cos(a) * 30, c.y() + math.sin(a) * 26 + 6)
                p.drawPolyline([c, knee, foot])
        p.setBrush(QColor(78, 44, 34, 220))
        p.drawEllipse(c, 7, 9)
        p.drawEllipse(QPointF(c.x(), c.y() - 11), 4.5, 4.5)


class Notebook(_Screen):
    """His notes on her: a two-page spread, flipped with the arrows (or the keys)."""
    PER_PAGE = 3

    def __init__(self, shell, on_back):
        super().__init__(shell, [("‹", self.prev), ("›", self.next), ("Back", on_back)])
        self.actions = [self.prev, self.next, on_back]
        self.rec = shell.records
        self.pages = self._paginate()
        self.at = 0

    def _paginate(self):
        pages = []
        for section in NOTES.SECTIONS:
            ids = [k for k, v in NOTES.PAGES.items() if v[0] == section]
            for i in range(0, len(ids), self.PER_PAGE):
                pages.append((section, ids[i:i + self.PER_PAGE], i == 0))
        return pages

    def prev(self):
        self.at = max(0, self.at - 2)
        self.update()

    def next(self):
        self.at = min(len(self.pages) - 1 - (len(self.pages) - 1) % 2, self.at + 2)
        self.update()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Left:
            self.prev()
        elif e.key() == Qt.Key_Right:
            self.next()
        else:
            super().keyPressEvent(e)

    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        self.backdrop(p)
        W, H = self.width(), self.height()
        book = QRectF(W * 0.09, H * 0.06, W * 0.82, H * 0.8)
        p.setPen(QPen(QColor(20, 12, 8), 2))
        p.setBrush(QColor(58, 34, 22))
        p.drawRoundedRect(book, 14, 14)                           # (its leather)
        written = sum(1 for k in NOTES.PAGES if k in self.rec.notes)
        p.setFont(QFont(SERIF, 11))
        p.setPen(QColor(200, 170, 130))
        p.drawText(QRectF(book.left(), book.top() - 2, book.width(), 0), Qt.AlignHCenter | Qt.AlignBottom,
                   f"Notes on her  -  {written} of {len(NOTES.PAGES)} written")
        for side in (0, 1):
            k = self.at + side
            pr = QRectF(book.left() + 18 + side * (book.width() / 2 - 8), book.top() + 16, book.width() / 2 - 28,
                        book.height() - 32)
            g = QLinearGradient(pr.topLeft(), pr.topRight())
            g.setColorAt(0, QColor(222, 208, 178) if side else QColor(208, 192, 160))
            g.setColorAt(1, QColor(208, 192, 160) if side else QColor(224, 210, 182))
            p.setPen(Qt.NoPen)
            p.setBrush(g)
            p.drawRect(pr)
            p.setPen(QPen(QColor(150, 130, 100, 60), 1))
            for ly in range(int(pr.top() + 60), int(pr.bottom() - 20), 26):     # (its ruled lines)
                p.drawLine(QPointF(pr.left() + 20, ly), QPointF(pr.right() - 20, ly))
            if k < len(self.pages):
                self._page(p, pr, *self.pages[k])
                p.setFont(QFont(SERIF, 9))
                p.setPen(QColor(120, 96, 70))
                p.drawText(QRectF(pr.left(), pr.bottom() - 24, pr.width(), 20), Qt.AlignHCenter, str(k + 1))
        p.setPen(QPen(QColor(30, 18, 12), 3))
        p.drawLine(QPointF(book.center().x(), book.top() + 12), QPointF(book.center().x(), book.bottom() - 12))
        p.end()

    def _page(self, p, pr, section, ids, first):
        y = pr.top() + 22
        if first:
            p.setFont(QFont(SERIF, 16, QFont.Bold))
            p.setPen(QColor(70, 40, 26))
            p.drawText(QRectF(pr.left() + 24, y, pr.width() - 48, 30), Qt.AlignLeft, section)
            y += 40
        for nid in ids:
            sec, title, text = NOTES.PAGES[nid]
            known = nid in self.rec.notes
            p.setFont(QFont(SERIF, 13, QFont.Bold))
            p.setPen(QColor(64, 38, 24) if known else QColor(140, 120, 96))
            p.drawText(QRectF(pr.left() + 24, y, pr.width() - 48, 24), Qt.AlignLeft, title if known else "? ? ?")
            y += 26
            f = QFont(SERIF, 12)
            f.setItalic(True)
            p.setFont(f)
            body = text if known else "(not yet learned)"
            box = QFontMetrics(f).boundingRect(int(pr.left() + 30), int(y), int(pr.width() - 60), 400,
                                               Qt.TextWordWrap, body)
            p.setPen(QColor(54, 40, 30) if known else QColor(150, 132, 108))
            p.drawText(QRectF(pr.left() + 30, y, pr.width() - 60, box.height() + 4), Qt.AlignLeft | Qt.TextWordWrap, body)
            y += box.height() + 22


class Unlocks(_Screen):
    """What's been found so far: endings, her guests, the pages of his notes, and anything else unlocked."""

    def __init__(self, shell, on_back):
        super().__init__(shell, [("Back", on_back)])
        self.rec = shell.records

    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        self.backdrop(p)
        W, H = self.width(), self.height()
        rec = self.rec
        p.setFont(QFont(SERIF, 30))
        p.setPen(QColor(232, 220, 200))
        p.drawText(QRectF(0, H * 0.06, W, 50), Qt.AlignHCenter, "Unlocked")
        guests = [k for k in NOTES.SUITORS if k in rec.notes]
        rows = [("Endings", f"{len(rec.found)} of {ENDINGS}", ", ".join(sorted(rec.found)) or "none yet"),
                ("Her guests found", f"{len(guests)} of {len(NOTES.SUITORS)}",
                 ", ".join(NOTES.PAGES[k][1].split(",")[0] for k in guests) or "none yet"),
                ("Notes written", f"{sum(1 for k in NOTES.PAGES if k in rec.notes)} of {len(NOTES.PAGES)}", "")]
        for section in NOTES.SECTIONS:
            ids = [k for k, v in NOTES.PAGES.items() if v[0] == section]
            have = [k for k in ids if k in rec.notes]
            rows.append(("    " + section, f"{len(have)} of {len(ids)}", ", ".join(NOTES.PAGES[k][1] for k in have)))
        rows.append(("Other", f"{len(rec.unlocks)}", ", ".join(rec.unlocks) or "nothing yet"))
        y = H * 0.18
        for name, count, detail in rows:
            p.setFont(QFont(SERIF, 14, QFont.Bold if not name.startswith(" ") else QFont.Normal))
            p.setPen(QColor(220, 200, 170))
            p.drawText(QRectF(W * 0.14, y, W * 0.3, 26), Qt.AlignLeft, name)
            p.setPen(QColor(232, 201, 160))
            p.drawText(QRectF(W * 0.38, y, W * 0.12, 26), Qt.AlignLeft, count)
            f = QFont(SERIF, 12)
            f.setItalic(True)
            p.setFont(f)
            p.setPen(QColor(170, 156, 138))
            p.drawText(QRectF(W * 0.5, y + 2, W * 0.38, 40), Qt.AlignLeft | Qt.TextWordWrap, detail)
            y += 44
        p.end()
