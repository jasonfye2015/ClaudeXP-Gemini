"""Her scenes, on the screen: the letterbox, the dark between shots, and her window - low across the frame, dark,
dressed with old branches and oak leaves, a cobweb in its corner, glowing mushrooms at its feet. Her words in her own
hand (Italianno), written out as she speaks them; his last words above, small, in his. He answers below: typing (a
language model writes her words) or choosing (the script). A click shows her line whole. When she's done with him,
"Go on". Esc pauses, as ever."""
import math
import queue

from PySide6.QtCore import QPointF, QRect, QRectF, Qt, QTimer
from PySide6.QtGui import (QBrush, QColor, QFontMetrics, QLinearGradient, QPainter, QPainterPath, QPen,
                           QRadialGradient)
from PySide6.QtWidgets import QLineEdit, QPushButton, QWidget

from . import fonts
from .menu import web

STYLE = """
QPushButton { color: #E2D6C4; background: rgba(34, 22, 18, 215); border: 1px solid #5E4430; border-radius: 4px;
    padding: 5px 14px; font-family: Georgia; text-align: left; }
QPushButton:hover { background: rgba(78, 46, 30, 230); border-color: #A07A54; color: #FFF0DA; }
QLineEdit { color: #EADCC4; background: rgba(8, 5, 6, 230); border: 1px solid #6A4E36; border-radius: 4px;
    padding: 7px 10px; font-family: Georgia; }
"""
REVEAL = 34.0                    # (characters a second: as she speaks)
LEAVES = ((0.04, 0.0, 2.6, (128, 82, 36)), (0.12, -0.12, 0.4, (96, 84, 38)), (0.2, 0.05, 2.2, (150, 64, 30)),
          (0.29, -0.06, 0.9, (122, 78, 34)), (0.62, -0.08, 2.4, (140, 92, 40)), (0.71, 0.04, 0.5, (84, 70, 34)),
          (0.8, -0.1, 2.9, (150, 64, 30)), (0.9, 0.02, 0.7, (122, 78, 34)))


def leaf(p, x, y, turn, size, col):
    """An oak leaf on its stalk: lobed along a rib."""
    p.save()
    p.translate(x, y)
    p.rotate(math.degrees(turn))
    path = QPainterPath(QPointF(size * 0.15, 0))
    lobes = 4
    top = [QPointF(size * (0.2 + 0.8 * k / lobes), -size * (0.18 + 0.12 * math.sin(k * math.pi / lobes)))
           for k in range(lobes + 1)]
    for k in range(lobes):
        a, b = top[k], top[k + 1]
        path.quadTo(QPointF((a.x() + b.x()) / 2, a.y() - size * 0.16), b)
        if k < lobes - 1:
            path.lineTo(b.x() - size * 0.03, b.y() * 0.45)
    path.lineTo(size * 1.08, 0)
    for k in range(lobes, 0, -1):
        a, b = QPointF(top[k].x(), -top[k].y()), QPointF(top[k - 1].x(), -top[k - 1].y())
        path.quadTo(QPointF((a.x() + b.x()) / 2, a.y() + size * 0.16), b)
        if k > 1:
            path.lineTo(b.x() + size * 0.03, b.y() * 0.45)
    path.closeSubpath()
    p.setPen(QPen(col.darker(170), 0.8))
    p.setBrush(QBrush(col))
    p.drawPath(path)
    p.setPen(QPen(col.lighter(135), 0.9))
    p.drawLine(QPointF(-size * 0.12, 0), QPointF(size * 0.95, 0))
    p.restore()


def mushrooms(p, x, y, scale, t, seed):
    """A little cluster of the den's glowing fungus: three caps on pale stems, breathing light."""
    glow = 0.55 + 0.45 * math.sin(t * 2 * math.pi / (7.0 + seed) + seed * 2.0)
    halo = QRadialGradient(QPointF(x, y - 14 * scale), 46 * scale)
    halo.setColorAt(0, QColor(80, 240, 200, int(80 * glow)))
    halo.setColorAt(1, QColor(80, 240, 200, 0))
    p.setPen(Qt.NoPen)
    p.setBrush(halo)
    p.drawEllipse(QPointF(x, y - 14 * scale), 46 * scale, 46 * scale)
    for dx, h, w in ((-12, 18, 13), (2, 28, 17), (15, 14, 10)):
        cx, cap = x + dx * scale, y - h * scale
        p.setBrush(QColor(196, 214, 200, 210))
        p.drawRoundedRect(QRectF(cx - 2 * scale, cap, 4 * scale, h * scale), 2 * scale, 2 * scale)
        g = QLinearGradient(0, cap - w * 0.55 * scale, 0, cap)
        g.setColorAt(0, QColor(120, 255, 220, int(140 + 115 * glow)))
        g.setColorAt(1, QColor(40, 150, 130, 230))
        p.setBrush(g)
        path = QPainterPath(QPointF(cx - w * scale, cap))
        path.cubicTo(QPointF(cx - w * scale, cap - w * 0.75 * scale), QPointF(cx + w * scale, cap - w * 0.75 * scale),
                     QPointF(cx + w * scale, cap))
        path.closeSubpath()
        p.drawPath(path)
        p.setPen(QPen(QColor(20, 80, 70, 160), 0.8))
        for k in range(-3, 4):
            p.drawLine(QPointF(cx + k * w * 0.25 * scale, cap), QPointF(cx + k * w * 0.1 * scale, cap + 2.5 * scale))
        p.setPen(Qt.NoPen)


class SceneView(QWidget):
    def __init__(self, shell, scene, talk, on_done):
        super().__init__(shell)
        self.shell, self.scene, self.talk, self.on_done = shell, scene, talk, on_done
        self.setStyleSheet(STYLE)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.replies = queue.Queue()
        self.opened = False
        self.waiting = True
        self.her_text, self.his_text = "", ""
        self.line_t = 0.0
        self.t = 0.0
        self.closing = False
        self.widgets = []
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(33)
        self.setGeometry(shell.rect())
        self.setFocusPolicy(Qt.StrongFocus)
        self.show()
        self.raise_()
        self.setFocus()

    # ---- where the window is --------------------------------------------------------------------------------------
    def box(self):
        """Low across the frame, as tall as her line and his answers need (growing upward)."""
        W, H = self.width(), self.height()
        h = max(H * 0.24, min(H * 0.82, getattr(self, "need", 0.0)))
        return QRectF(W * 0.13, H * 0.965 - h, W * 0.74, h)

    def _tick(self):
        self.t += 0.033
        typing = getattr(self, "_typing", None)
        if typing is not None:                                     # (the letter's hand, typing for him)
            edit, line, t0 = typing
            k = int((self.t - t0) * 28)
            try:
                edit.setText(line[:k])
            except RuntimeError:
                self._typing = None
            else:
                if k >= len(line) + 12:
                    self._typing = None
                    self._typed(line)
        if self.scene.ready and not self.opened:
            self.opened = True
            self.talk.open(self.scene.name, lambda text, ch: self.replies.put((text, ch)))
        try:
            text, choices = self.replies.get_nowait()
        except queue.Empty:
            text = None
        if text is not None:
            self._her(text, choices)
        if self.shell.view.director is not None:
            if getattr(self, "ghost", None) is None:
                from .ghost import Ghost
                self.ghost = Ghost(self)
            if not self.ghost.busy:
                self._auto()
        if self.scene.done and not self.closing:
            self.closing = True
            self.timer.stop()
            self.on_done()
            return
        self.update()

    def _auto(self):
        """Led by her letter: when her line's all there, and there's been time to read it - his answer."""
        if self.waiting or not self.widgets:
            self._full_at = None
            return
        if self._shown() < len(self.her_text):
            return
        if getattr(self, "_full_at", None) is None:
            self._full_at = self.t
            return
        if self.t - self._full_at < 1.4 + 0.3 * len(self.her_text.split()):
            return
        self._full_at = None
        from ..game import script
        from ..game.autoplay import best_gift, choose_line
        n, talk = self.shell.view.night, self.talk
        if self.choices is None:
            self._press("Go on", self._go_on)
            return
        gift = best_gift(n)
        if gift and not getattr(self, "_gave", False):
            self._gave = True
            self._press("Hold out" if n.held == gift else "Offer", lambda: self._offered(gift))
            return
        if self.scene.name == "crown" and n.spells.unshown() and not getattr(self, "_shown_memory", False):
            self._shown_memory = True
            mem = n.spells.unshown()[0]
            self._press("Cast a spell", lambda: self._cast("memory", mem))
            return
        node = script.SCENES[talk.scene]["nodes"].get(talk.node, {}).get("choices", []) if talk.node else []
        if self.choices and node:
            i = choose_line([(c[0], c[1], c[4] if len(c) > 4 else None) for c in node])
            self._press(node[i][0], lambda: self._chose(i, node[i][0]))
            return
        pool = getattr(self, "_pool", None)                        # (a model speaks for her: his lines, typed)
        if pool is None:
            lines = [c for nd in script.SCENES[talk.scene]["nodes"].values() for c in nd.get("choices", [])]
            from ..game.autoplay import score_kinds
            lines.sort(key=lambda c: -score_kinds(c[1]))
            self._pool = pool = [c[0] for c in lines if "lie" not in c[1] and not (len(c) > 4 and c[4] == "stay")]
        if pool:
            line = pool.pop(0)
            edit = next((w for w in self.widgets if isinstance(w, QLineEdit)), None)
            if edit is not None:                                   # (typed into her window, a letter at a time)
                self._type_into(edit, line)
            else:
                self._typed(line)
        else:
            self._press("Go on", self._go_on)

    def _press(self, label, then):
        """The ghost of a hand: to the button that reads `label` (or begins with it), a moment there, and pressed."""
        w = next((b for b in self.widgets if isinstance(b, QPushButton) and
                  (b.text() == label or b.text().lstrip("✦✧ ").startswith(label))), None)
        if w is None:
            then()
            return
        c = w.geometry().center()
        self.ghost.go(QPointF(c.x() - w.width() * 0.3, c.y() + 2), lambda: (w.setDown(True), then()))

    def _type_into(self, edit, line):
        c = edit.geometry().center()

        def typing():
            self._typing = (edit, line, self.t)
        self.ghost.go(QPointF(c.x() - edit.width() * 0.3, c.y()), typing)

    def _shown(self):
        speed = REVEAL * (0.4 + 1.2 * self.shell.records.options.get("text_speed", 50) / 100.0)
        return int((self.t - self.line_t) * speed)

    def _her(self, text, choices, again=False):
        if again:                                              # (back to where they were: no word said again)
            self._clear()
            self._choices_for(choices)
            self._lay()
            return
        from ..game import notes
        view = self.shell.view
        view.note(notes.for_line(text))
        for node in self.talk.visited[getattr(self, "_seen", 0):]:
            view.note(notes.for_node(node))
        self._seen = len(self.talk.visited)
        self.waiting = False
        self.her_text, self.line_t = text, self.t
        audio = self.shell.view.audio
        if audio is not None:
            audio.say(text)
        self._clear()
        self._choices_for(choices)
        self._lay()

    def _choices_for(self, choices):
        self.choices = choices
        if choices is None:
            self._button("Go on", self._go_on)
        elif choices:
            for i, c in enumerate(choices):
                self._button(c, lambda _x=False, i=i, c=c: self._chose(i, c))
            self._offer_button()
        else:
            e = QLineEdit(self)
            e.setPlaceholderText("Answer her...")
            e.setFont(fonts.his(self.shell.records, 13))
            e.returnPressed.connect(lambda: self._typed(e.text()))
            self.widgets.append(e)
            e.show()
            e.setFocus()
            self._offer_button()

    def _offer_button(self):
        """If he carries anything: something to give her. And his spells, as gestures."""
        from ..game.offerings import KEPT
        n = self.shell.view.night
        if n.held and n.held not in KEPT:                       # (what's in his hand: held out to her)
            from ..game.offerings import ITEMS
            self._button("✦  Hold out " + ITEMS[n.held][0].split(" ", 1)[-1], lambda: self._offered(n.held),
                         small=True)
        if any(i not in KEPT and i != n.held for i in n.pack):
            self._button("✦  Offer" + (" something else" if n.held and n.held not in KEPT else " her something") + "...",
                         self._open_pack, small=True)
        if self.talk.knows_her and not self.talk.flags.get("named"):
            self._button("✦  Speak her true name", self._speak_name, small=True)
        if n.venom.active and not self.talk.flags.get("asked_cure"):
            self._button("✦  Ask her for the antidote", self._ask_cure, small=True)
        sp = self.shell.view.night.spells
        if any(sp.ready(k) for k in ("light", "warmth", "illusion")) or sp.unshown():
            self._button("✧  Cast a spell...", self._open_spells, small=True)

    SPELLS = (("light", "Light  -  a hard white light"), ("warmth", "Warmth  -  a small flame in his palm"),
              ("illusion", "Illusion  -  seem grander than he is"))

    def _open_spells(self):
        sp = self.shell.view.night.spells
        self._clear()
        for name, label in self.SPELLS:
            if sp.ready(name):
                self._button("✧  " + label, lambda _x=False, name=name: self._cast(name))
        if sp.unshown():
            self._button("✧  Memory  -  show her something true", self._open_memories)
        self._button("Never mind", lambda: self._her(self.her_text, self.choices, again=True))
        self._lay()

    def _open_memories(self):
        from ..game.spells import MEMORIES
        self._clear()
        for k in self.shell.view.night.spells.unshown():
            self._button("✧  " + MEMORIES[k][0], lambda _x=False, k=k: self._cast("memory", k))
        self._button("Never mind", lambda: self._her(self.her_text, self.choices, again=True))
        self._lay()

    def _speak_name(self):
        from ..game.hidden import SPEAK
        self.his_text = SPEAK
        self._clear()
        self.waiting = True
        self.talk.speak_name(lambda t, ch: self.replies.put((t, ch)))

    def _ask_cure(self):
        self.his_text = "(You ask her to take her venom out of you.)"
        self._clear()
        self.waiting = True
        self.talk.ask_cure(lambda t, ch: self.replies.put((t, ch)))

    def _cast(self, name, memory=None):
        self.his_text = {"light": "(You raise a hard white light.)", "warmth": "(You open your hand: a small flame.)",
                         "illusion": "(You wrap yourself in an illusion - a cloak of stars.)"}.get(name) or \
            "(You show her a memory, and let her see it all.)"
        n = self.shell.view.night
        n.spells.lit.append((name, n.eye, n.spells.t, 4.0 if name != "memory" else 2.0))
        audio = self.shell.view.audio
        if audio is not None:
            audio.synth.play("whoosh", 0.7)
        self._clear()
        self.waiting = True
        self.talk.cast(name, lambda t, ch: self.replies.put((t, ch)), memory)

    def _open_pack(self):
        from ..game.offerings import ITEMS
        self._clear()
        from ..game.offerings import KEPT
        learned = self.shell.records.learned
        for item in [i for i in self.shell.view.night.pack if i not in KEPT]:
            seen = learned.get(item, [])
            label = "✦  " + ITEMS[item][0][:1].upper() + ITEMS[item][0][1:]
            if seen:
                label += "\n      (" + seen[-1] + ")"                 # (what he's learned of it, other times)
            self._button(label, lambda _x=False, item=item: self._offered(item))
        self._button("Never mind", lambda: self._her(self.her_text, self.choices, again=True))
        self._lay()

    def _offered(self, item):
        from ..game.offerings import ITEMS
        self.his_text = "(You offer her " + ITEMS[item][0] + ".)"
        self._clear()
        self.waiting = True
        self.talk.offer(item, lambda t, ch: self.replies.put((t, ch)))

    def _button(self, text, fn, small=False):
        b = QPushButton(text, self)
        b.small = small
        b.setFont(fonts.his(self.shell.records, 10 if small else 12))
        b.setCursor(Qt.PointingHandCursor)
        b.clicked.connect(fn)
        self.widgets.append(b)
        b.show()

    def _clear(self):
        for w in self.widgets:
            w.hide()
            w.deleteLater()
        self.widgets = []

    def _lay(self):
        W = self.width()
        fm = QFontMetrics(fonts.her(self.shell.records, 30))
        text_h = fm.boundingRect(QRect(0, 0, int(W * 0.74 - 80), 4000), Qt.TextWordWrap, self.her_text or "...").height()
        big = [w for w in self.widgets if not getattr(w, "small", False)]
        small = [w for w in self.widgets if getattr(w, "small", False)]
        rows, row, room = [], [], W * 0.74 - 80                  # (the small ones: in a row - or two - under his lines)
        for w in small:
            need = w.sizeHint().width() + 16
            if row and sum(x.sizeHint().width() + 16 for x in row) + need > room:
                rows.append(row)
                row = []
            row.append(w)
        if row:
            rows.append(row)
        sh = sum(max(x.sizeHint().height() for x in r_) + 6 for r_ in rows)
        buttons = sum(w.sizeHint().height() + 6 for w in big) + sh
        self.need = 44 + (24 if self.his_text else 0) + text_h + 14 + buttons + 22
        r = self.box()
        y = r.bottom() - 18
        for r_ in reversed(rows):
            h = max(x.sizeHint().height() for x in r_)
            y -= h + 6
            x = r.left() + 40
            for w in r_:
                ww = w.sizeHint().width() + 16
                w.setGeometry(int(x), int(y), int(ww), h)
                x += ww + 8
        for w in reversed(big):
            h = w.sizeHint().height()
            y -= h + 6
            w.setGeometry(int(r.left() + 40), int(y), int(r.width() - 80), h)
        if getattr(self, "ghost", None) is not None:
            self.ghost.setGeometry(self.rect())
            self.ghost.raise_()

    def resizeEvent(self, e):
        self._lay()
        super().resizeEvent(e)

    def _chose(self, i, text):
        self.his_text = text
        self._clear()
        self.waiting = True
        self.talk.choose(i, lambda t, ch: self.replies.put((t, ch)))

    def _typed(self, text):
        if not text.strip():
            return
        speaking = self._shown() < len(self.her_text)
        n = self.shell.view.night
        if n.venom.active:                                         # (her venom: it comes out wrong)
            from ..game.venom import slur
            text = slur(text.strip(), n.venom.rng)
        self.his_text = text.strip()
        self._clear()
        self.waiting = True
        self.talk.say(text, lambda t, ch: self.replies.put((t, ch)), interrupting=speaking)

    def _go_on(self):
        self._clear()
        self.her_text = ""
        self.scene.end()

    def mousePressEvent(self, e):
        self.line_t = -99.0                                    # (a click: her line whole)

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.shell.pause()
            return
        super().keyPressEvent(e)

    # ---- the drawing --------------------------------------------------------------------------------------------
    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        W, H = self.width(), self.height()
        sc = self.scene
        bar = H * 0.11 * sc.box
        p.fillRect(QRectF(0, 0, W, bar), QColor(0, 0, 0))
        p.fillRect(QRectF(0, H - bar, W, bar), QColor(0, 0, 0))
        if sc.dim > 0:
            p.fillRect(self.rect(), QColor(0, 0, 0, int(255 * min(1.0, sc.dim))))
        if sc.phase == "talk" and self.opened:
            self._window(p)
        toast = getattr(self.shell.view, "note_toast", None)
        import time
        if toast and time.perf_counter() - toast[1] < 4.5:            # (a page written in his notes, even now)
            age = time.perf_counter() - toast[1]
            f = fonts.his(self.shell.records, 11)
            f.setItalic(True)
            p.setFont(f)
            p.setPen(QColor(220, 196, 150, int(220 * min(1.0, age / 0.4, (4.5 - age) / 0.8))))
            p.drawText(QRectF(0, H * 0.115 * sc.box + 8, W, 22), Qt.AlignHCenter, f"Written in your notes:  {toast[0]}")
        self.shell.view.draw_lesson(p, W, H)                         # (the first night's margin note, even here)
        p.end()

    def _window(self, p):
        r = self.box()
        t = self.t
        g = QLinearGradient(0, r.top(), 0, r.bottom())
        g.setColorAt(0, QColor(14, 9, 10, 228))
        g.setColorAt(1, QColor(5, 3, 4, 240))
        p.setPen(QPen(QColor(84, 60, 42), 1.4))
        p.setBrush(g)
        p.drawRoundedRect(r, 10, 10)
        web(p, r.right() - 4, r.top() + 4, min(110.0, r.height() * 0.55), 2.35, t, alpha=55)
        sway = math.sin(t * 0.7) * 1.5
        for side in (0, 1):                                    # (old branches along its top, from each corner)
            x0 = r.left() - 30 if side == 0 else r.right() + 30
            x3 = r.left() + r.width() * 0.46 if side == 0 else r.right() - r.width() * 0.4
            pts = (QPointF(x0, r.top() + 22), QPointF(x0 + (x3 - x0) * 0.35, r.top() - 18 + sway),
                   QPointF(x0 + (x3 - x0) * 0.7, r.top() + 10), QPointF(x3, r.top() - 6 + sway))
            for width, col in ((17, QColor(16, 11, 8)), (11, QColor(46, 32, 22)), (4, QColor(70, 50, 34))):
                path = QPainterPath(pts[0])
                path.cubicTo(pts[1], pts[2], pts[3])
                p.setPen(QPen(col, width, Qt.SolidLine, Qt.RoundCap))
                p.setBrush(Qt.NoBrush)
                p.drawPath(path)
        for u, dy, turn, col in LEAVES:
            x = r.left() + r.width() * u
            leaf(p, x, r.top() - 4 + dy * 60 + sway * (1 - u), turn + 0.12 * math.sin(t * 0.9 + u * 9), 34,
                 QColor(*col))
        mushrooms(p, r.left() + 30, r.bottom() + 4, 1.45, t, 1.0)
        mushrooms(p, r.right() - 40, r.bottom() + 2, 1.15, t, 3.0)
        rec = self.shell.records
        p.setFont(fonts.her(rec, 20))                          # (her name, a little gold, at the top)
        p.setPen(QColor(196, 160, 104, 200))
        p.drawText(QRectF(r.left() + 40, r.top() + 12, 300, 34), Qt.AlignLeft | Qt.AlignVCenter, "Ysmeine")
        y = r.top() + 44
        if self.his_text:
            p.setFont(fonts.his(rec, 11))
            p.setPen(QColor(150, 166, 178, 170))
            p.drawText(QRectF(r.left() + 56, y, r.width() - 110, 24), Qt.AlignLeft | Qt.TextWordWrap,
                       "— " + self.his_text)
            y += 24
        top_of_buttons = min([w.geometry().top() for w in self.widgets] or [r.bottom() - 20])
        area = QRectF(r.left() + 40, y, r.width() - 80, max(30.0, top_of_buttons - y - 6))
        p.setFont(fonts.her(rec, 30))
        if self.waiting:
            dots = "." * (1 + int(t * 2.5) % 3)
            p.setPen(QColor(233, 210, 196, 150))
            p.drawText(area, Qt.AlignLeft | Qt.AlignTop, dots)
        else:
            shown = self.her_text[:max(0, self._shown())]
            p.setPen(QColor(0, 0, 0, 180))
            p.drawText(area.translated(1, 1), Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap, shown)
            p.setPen(QColor(236, 216, 200))
            p.drawText(area, Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap, shown)
