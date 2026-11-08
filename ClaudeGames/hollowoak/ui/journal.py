"""His notebook, in his hands (phase 6b): Esc - and he looks down, and lifts it. Nothing stops for it: the night goes on
around him while he reads (he can't walk with it open), and if something drops onto his face, or she comes for him,
it's knocked from his hands. The left page is its contents; the right, what he's turned to - and a page turns between.

    journal = Journal(view)
    journal.toggle() / journal.close(knocked=False)
    journal.draw(p, W, H)            over the den
    journal.press(pos) / journal.move(pos) / journal.release()     the mouse, on its pages
The true pause is P (or the window losing focus): ui/shell.py's "The night waits"."""
import math
import time

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QFontMetrics, QLinearGradient, QPen

from ..game import notes as NOTES
from ..game.records import ENDINGS
from . import fonts
from .pages import BACK, FRONT

SERIF = "Georgia"
INK, FADED, RULE = QColor(52, 36, 26), QColor(120, 98, 76), QColor(150, 130, 100, 60)
CONTENTS = (("go", "Go on"), ("notes", "Notes on her"), ("letter", "Her letter"), ("unlocks", "What's been found"),
            ("options", "Options"), ("body", "What the night does"), ("save", "Save here"),
            ("leave", "Back to the title"))
SLIDERS = (("Brightness", "brightness"), ("Volume", "volume"), ("Music", "music"), ("Looking about", "look"), ("Her words, how fast", "text_speed"),
           ("Her words, their size", "her_size"), ("Your words, their size", "his_size"),
           ("How wide he sees", "fov"))
RANGE = {"her_size": (60, 160), "his_size": (60, 160)}            # (the rest: 0 to 100)
TOGGLES = (("The heart monitor", "heart"), ("The heartbeat, heard", "heartbeat"), ("The orbs", "orbs"),
           ("Her voice, aloud", "aloud"), ("Her venom's pulse", "venom_fx"), ("Steadier light", "steady"),
           ("The lantern's shadows", "shadows"), ("Invert looking up and down", "invert"))
PER_PAGE = 3
FLIP = 0.42


class Journal:
    def __init__(self, view):
        self.view = view
        self.open = False
        self.at = -9.0
        self.page = "contents"
        self.shown = "notes"                 # (what the right page shows)
        self.notes_at = 0
        self.flip_at = -9.0
        self.next_shown = None
        self.hits = []                       # [(rect, action)]
        self.dragging = None
        self.said = None                     # (a line written on the save / leave page)
        self.said_next = None

    # ---- open, shut ---------------------------------------------------------------------------------------------
    def toggle(self):
        if self.open:
            self.close()
        else:
            self.open, self.at = True, time.perf_counter()
            self.said = None

    def open_to(self, nid):
        """Lifted, open at the page where nid is written (the letter leading him: what he's just learned)."""
        for k, page in enumerate(self._note_pages()):
            if nid in page:
                self.notes_at = k
        self.shown, self.next_shown = "notes", None
        if not self.open:
            self.open, self.at = True, time.perf_counter()

    def close(self, knocked=False):
        if not self.open:
            return
        self.open, self.at = False, time.perf_counter()
        self.dragging = None
        self.view.shell.records.save()
        if knocked:
            self.view.whisper = ("The notebook's knocked from your hands.", time.perf_counter(), 3.0)

    def lift(self):
        """0..1: down at his side, up before him."""
        k = min(1.0, (time.perf_counter() - self.at) / 0.45)
        k = k * k * (3 - 2 * k)
        return k if self.open else 1.0 - k

    def turn_to(self, what):
        if what == self.shown and self.next_shown is None:
            return
        self.next_shown = what
        self.flip_at = time.perf_counter()
        self.said = None

    # ---- the mouse ----------------------------------------------------------------------------------------------
    def press(self, pos):
        for rect, action in self.hits:
            if rect.contains(pos):
                self._do(action, pos)
                return True
        return False

    def move(self, pos):
        if self.dragging is not None:
            key, rect = self.dragging
            lo, hi = RANGE.get(key, (0, 100))
            k = max(0.0, min(1.0, (pos.x() - rect.left()) / rect.width()))
            self.view.shell.records.options[key] = int(round(lo + (hi - lo) * k))

    def release(self):
        if self.dragging is not None:
            self.dragging = None
            self.view.shell.records.save()

    def _do(self, action, pos):
        kind, arg = action
        rec = self.view.shell.records
        if kind == "turn":
            if arg == "go":
                self.close()
                self.view.capture()
            elif arg == "save":
                why = self.view.quick_save()
                line = "Saved, at " + self.view.night.clock_words() + "." if why is None else why
                if self.shown == "save" and self.next_shown is None:
                    self.said = line
                else:
                    self.turn_to("save")
                    self.said_next = line
            else:
                self.turn_to(arg)
        elif kind == "page":
            pages = self._note_pages()
            self.notes_at = max(0, min(len(pages) - 1, self.notes_at + arg))
            self.flip_at, self.next_shown = time.perf_counter(), "notes"
        elif kind == "slider":
            self.dragging = (arg[0], arg[1])
            self.move(pos)
        elif kind == "level":
            rec.options["difficulty"] = arg
            rec.save()
        elif kind == "toggle":
            rec.options[arg] = not rec.options.get(arg, True)
            rec.save()
        elif kind == "leave":
            self.open = False
            self.view.shell.show_title()
        elif kind == "stay":
            self.turn_to("notes")

    # ---- the drawing --------------------------------------------------------------------------------------------
    def draw(self, p, W, H):
        k = self.lift()
        if k <= 0.001:
            self.hits = []
            return
        now = time.perf_counter()
        if self.next_shown is not None and now - self.flip_at >= FLIP / 2:     # (under the turning page: what's next)
            self.shown, self.next_shown = self.next_shown, None
            if getattr(self, "said_next", None):
                self.said, self.said_next = self.said_next, None
        bw, bh = min(W * 0.74, H * 1.12), min(H * 0.72, W * 0.48)
        top = H - bh * k * 1.06 + (1 - k) * 40
        tilt = (1 - k) * 0.25
        book = QRectF(W / 2 - bw / 2, top, bw, bh)
        p.save()
        p.fillRect(QRectF(0, 0, W, H), QColor(0, 0, 0, int(70 * k)))
        p.translate(book.center())
        p.rotate(-6 * tilt * 57.3 / 10)
        p.translate(-book.center())
        p.setPen(QPen(QColor(20, 12, 8), 2))
        p.setBrush(QColor(58, 34, 22))
        p.drawRoundedRect(book.adjusted(-10, -10, 10, 10), 14, 14)          # (its leather)
        left = QRectF(book.left() + 8, book.top() + 8, book.width() / 2 - 12, book.height() - 16)
        right = QRectF(book.center().x() + 4, book.top() + 8, book.width() / 2 - 12, book.height() - 16)
        for side, pr in ((0, left), (1, right)):
            g = QLinearGradient(pr.topLeft(), pr.topRight())
            g.setColorAt(0, QColor(222, 208, 178) if side else QColor(208, 192, 160))
            g.setColorAt(1, QColor(208, 192, 160) if side else QColor(224, 210, 182))
            p.setPen(Qt.NoPen)
            p.setBrush(g)
            p.drawRect(pr)
            p.setPen(QPen(RULE, 1))
            for ly in range(int(pr.top() + 54), int(pr.bottom() - 16), 24):
                p.drawLine(QPointF(pr.left() + 16, ly), QPointF(pr.right() - 16, ly))
        self.hits = []
        self._contents(p, left)
        self._right(p, right, self.shown)
        flip = (now - self.flip_at) / FLIP if self.next_shown is not None or now - self.flip_at < FLIP else 1.0
        if flip < 1.0:                                                     # (a page, turning over)
            w = right.width() * abs(math.cos(math.pi * flip))
            x = right.left() if flip < 0.5 else right.left() - w
            g = QLinearGradient(QPointF(x, 0), QPointF(x + w, 0))
            shade = int(60 * math.sin(math.pi * flip))
            g.setColorAt(0, QColor(214 - shade, 200 - shade, 170 - shade))
            g.setColorAt(1, QColor(226 - shade // 2, 212 - shade // 2, 184 - shade // 2))
            p.setPen(QPen(QColor(150, 130, 100, 120), 1))
            p.setBrush(g)
            p.drawRect(QRectF(x, right.top(), w, right.height()))
        p.setPen(QPen(QColor(30, 18, 12), 3))
        p.drawLine(QPointF(book.center().x(), book.top() + 6), QPointF(book.center().x(), book.bottom() - 6))
        p.restore()
        if k < 0.98:
            self.hits = []                                                 # (not to be clicked while it's moving)

    def _contents(self, p, pr):
        p.setFont(QFont(SERIF, 17, QFont.Bold))
        p.setPen(INK)
        p.drawText(QRectF(pr.left() + 24, pr.top() + 16, pr.width() - 48, 30), Qt.AlignLeft, "Contents")
        y = pr.top() + 62
        for key, label in CONTENTS:
            f = QFont(SERIF, 14)
            on = key == self.shown or (key == "go" and False)
            f.setUnderline(on)
            p.setFont(f)
            p.setPen(INK if on else QColor(84, 60, 42))
            r = QRectF(pr.left() + 30, y, pr.width() - 60, 26)
            p.drawText(r, Qt.AlignLeft | Qt.AlignVCenter, label)
            self.hits.append((r, ("turn", key)))
            y += 36
        n = self.view.night
        f = QFont(SERIF, 11)
        f.setItalic(True)
        p.setFont(f)
        p.setPen(FADED)
        if n is not None:
            p.drawText(QRectF(pr.left() + 30, pr.bottom() - 70, pr.width() - 60, 50), Qt.AlignLeft | Qt.TextWordWrap,
                       f"It is {n.clock_words()}. {n.acts.request}\n(The night doesn't wait. P pauses it.)")

    def _right(self, p, pr, what):
        getattr(self, "_page_" + what, self._page_notes)(p, pr)

    def _head(self, p, pr, text):
        p.setFont(QFont(SERIF, 16, QFont.Bold))
        p.setPen(INK)
        p.drawText(QRectF(pr.left() + 24, pr.top() + 16, pr.width() - 48, 30), Qt.AlignLeft, text)
        return pr.top() + 58

    def _note_pages(self):
        rec = self.view.shell.records
        ids = [k for s in NOTES.SECTIONS for k, v in NOTES.PAGES.items() if v[0] == s]
        ids = [k for k in ids if k in rec.notes] + [k for k in ids if k not in rec.notes]   # (what's written, first)
        return [ids[i:i + PER_PAGE] for i in range(0, len(ids), PER_PAGE)] or [[]]

    def _page_notes(self, p, pr):
        rec = self.view.shell.records
        pages = self._note_pages()
        self.notes_at = min(self.notes_at, len(pages) - 1)
        written = sum(1 for k in NOTES.PAGES if k in rec.notes)
        y = self._head(p, pr, f"Notes on her  ({written} of {len(NOTES.PAGES)})")
        for nid in pages[self.notes_at]:
            sec, title, text = NOTES.PAGES[nid]
            known = nid in rec.notes
            p.setFont(QFont(SERIF, 12, QFont.Bold))
            p.setPen(INK if known else QColor(140, 120, 96))
            p.drawText(QRectF(pr.left() + 24, y, pr.width() - 48, 22), Qt.AlignLeft, title if known else "? ? ?")
            y += 22
            f = QFont(SERIF, 11)
            f.setItalic(True)
            p.setFont(f)
            body = text if known else "(not yet learned)"
            h = QFontMetrics(f).boundingRect(int(pr.left() + 28), 0, int(pr.width() - 56), 600, Qt.TextWordWrap, body)
            p.setPen(QColor(54, 40, 30) if known else QColor(150, 132, 108))
            p.drawText(QRectF(pr.left() + 28, y, pr.width() - 56, h.height() + 4), Qt.AlignLeft | Qt.TextWordWrap, body)
            y += h.height() + 16
            if y > pr.bottom() - 60:
                break
        p.setFont(QFont(SERIF, 12))
        p.setPen(INK)
        for arg, text, x in ((-1, "‹  back", pr.left() + 24), (1, "on  ›", pr.right() - 84)):
            r = QRectF(x, pr.bottom() - 34, 60, 24)
            if (arg < 0 and self.notes_at > 0) or (arg > 0 and self.notes_at < len(pages) - 1):
                p.drawText(r, Qt.AlignCenter, text)
                self.hits.append((r, ("page", arg)))
        p.setFont(QFont(SERIF, 9))
        p.setPen(FADED)
        p.drawText(QRectF(pr.left(), pr.bottom() - 30, pr.width(), 20), Qt.AlignHCenter,
                   f"{self.notes_at + 1} of {len(pages)}")

    def _page_letter(self, p, pr):
        y = self._head(p, pr, "Her letter")
        rec = self.view.shell.records
        p.setFont(fonts.her(rec, 22))
        p.setPen(QColor(70, 40, 30))
        for line in FRONT + ("",) + BACK:
            if line:
                p.drawText(QRectF(pr.left() + 30, y, pr.width() - 60, 26), Qt.AlignLeft, line)
            y += 22 if line else 12
            if y > pr.bottom() - 30:
                break

    def _page_unlocks(self, p, pr):
        rec = self.view.shell.records
        y = self._head(p, pr, "What's been found")
        guests = [k for k in NOTES.SUITORS if k in rec.notes]
        rows = [("Endings", f"{len(rec.found)} of {ENDINGS}", ", ".join(sorted(rec.found)) or "none yet"),
                ("Her guests", f"{len(guests)} of {len(NOTES.SUITORS)}",
                 ", ".join(NOTES.PAGES[k][1].split(",")[0] for k in guests) or "none yet"),
                ("Notes", f"{sum(1 for k in NOTES.PAGES if k in rec.notes)} of {len(NOTES.PAGES)}", ""),
                ("Gifts learned", f"{len(rec.learned)}", ", ".join(sorted(rec.learned)) or "nothing yet")]
        for name, count, detail in rows:
            p.setFont(QFont(SERIF, 12, QFont.Bold))
            p.setPen(INK)
            p.drawText(QRectF(pr.left() + 24, y, pr.width() * 0.5, 22), Qt.AlignLeft, name)
            p.drawText(QRectF(pr.left() + pr.width() * 0.5, y, pr.width() * 0.4, 22), Qt.AlignLeft, count)
            y += 22
            if detail:
                f = QFont(SERIF, 10)
                f.setItalic(True)
                p.setFont(f)
                p.setPen(FADED)
                h = QFontMetrics(f).boundingRect(0, 0, int(pr.width() - 56), 400, Qt.TextWordWrap, detail).height()
                p.drawText(QRectF(pr.left() + 30, y, pr.width() - 56, h + 4), Qt.AlignLeft | Qt.TextWordWrap, detail)
                y += h
            y += 12

    def _page_options(self, p, pr):
        o = self.view.shell.records.options
        y = self._head(p, pr, "Options")
        from ..game.condition import LEVEL_NAMES
        p.setFont(QFont(SERIF, 10))
        p.setPen(INK)
        p.drawText(QRectF(pr.left() + 24, y - 4, 120, 18), Qt.AlignLeft, "How hard:")
        x = pr.left() + 100
        for key, name in LEVEL_NAMES:                                  # (the four: the chosen one underlined)
            f = QFont(SERIF, 10, QFont.Bold if o.get("difficulty", "normal") == key else QFont.Normal)
            f.setUnderline(o.get("difficulty", "normal") == key)
            p.setFont(f)
            wd = QFontMetrics(f).horizontalAdvance(name) + 12
            r = QRectF(x, y - 4, wd, 18)
            p.drawText(r, Qt.AlignLeft, name)
            self.hits.append((r, ("level", key)))
            x += wd + 6
        y += 22
        for label, key in SLIDERS:
            p.setFont(QFont(SERIF, 10))
            p.setPen(INK)
            p.drawText(QRectF(pr.left() + 24, y, pr.width() - 48, 16), Qt.AlignLeft, label)
            track = QRectF(pr.left() + 28, y + 20, pr.width() - 56, 10)
            p.setPen(QPen(QColor(90, 66, 46), 2))
            p.drawLine(QPointF(track.left(), track.center().y()), QPointF(track.right(), track.center().y()))
            lo, hi = RANGE.get(key, (0, 100))
            x = track.left() + track.width() * (o.get(key, (lo + hi) / 2) - lo) / (hi - lo)
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(70, 44, 28))
            p.drawEllipse(QPointF(x, track.center().y()), 6, 6)
            self.hits.append((track.adjusted(-8, -8, 8, 8), ("slider", (key, track))))
            y += 38
        y += 6
        colw = (pr.width() - 48) / 2
        for i, (label, key) in enumerate(TOGGLES):
            x = pr.left() + 24 + (i % 2) * colw
            yy = y + (i // 2) * 26
            box = QRectF(x, yy + 3, 13, 13)
            p.setPen(QPen(QColor(80, 58, 40), 1.5))
            p.setBrush(Qt.NoBrush)
            p.drawRect(box)
            if o.get(key, True):
                p.setPen(QPen(INK, 2))
                p.drawLine(QPointF(box.left() + 2, box.center().y()), QPointF(box.center().x(), box.bottom() - 2))
                p.drawLine(QPointF(box.center().x(), box.bottom() - 2), QPointF(box.right() + 2, box.top() - 2))
            p.setFont(QFont(SERIF, 10))
            p.setPen(INK)
            p.drawText(QRectF(x + 20, yy, colw - 24, 20), Qt.AlignLeft | Qt.AlignVCenter, label)
            self.hits.append((QRectF(x, yy, colw - 4, 20), ("toggle", key)))
        f = QFont(SERIF, 9)
        f.setItalic(True)
        p.setFont(f)
        p.setPen(FADED)
        p.drawText(QRectF(pr.left() + 24, pr.bottom() - 40, pr.width() - 48, 30), Qt.AlignLeft | Qt.TextWordWrap,
                   "What speaks for her is chosen before the night.")

    BODY = (("All of it", "fx_all"), ("His body (health)", "fx_health"), ("The poison in him", "fx_poison"),
            ("His mind (sanity)", "fx_sanity"), ("The stupor", "fx_stupor"), ("Blood and vomit", "fx_gore"),
            ("His eye", "fx_eye"), ("His sight swaying, swimming", "fx_distort"),
            ("Crawling, refusing, falling", "fx_control"))

    def _page_body(self, p, pr):
        o = self.view.shell.records.options
        y = self._head(p, pr, "What the night does to him")
        f = QFont(SERIF, 10)
        f.setItalic(True)
        p.setFont(f)
        p.setPen(FADED)
        p.drawText(QRectF(pr.left() + 24, y - 6, pr.width() - 48, 40), Qt.AlignLeft | Qt.TextWordWrap,
                   "At three quarters, half, and a quarter, each of the four shows on him. Tick what you'd see.")
        y += 34
        for label, key in self.BODY:
            box = QRectF(pr.left() + 28, y + 3, 13, 13)
            p.setPen(QPen(QColor(80, 58, 40), 1.5))
            p.setBrush(Qt.NoBrush)
            p.drawRect(box)
            if o.get(key, True):
                p.setPen(QPen(INK, 2))
                p.drawLine(QPointF(box.left() + 2, box.center().y()), QPointF(box.center().x(), box.bottom() - 2))
                p.drawLine(QPointF(box.center().x(), box.bottom() - 2), QPointF(box.right() + 2, box.top() - 2))
            p.setFont(QFont(SERIF, 11, QFont.Bold if key == "fx_all" else QFont.Normal))
            p.setPen(INK)
            p.drawText(QRectF(box.right() + 10, y, pr.width() - 90, 20), Qt.AlignLeft | Qt.AlignVCenter, label)
            self.hits.append((QRectF(pr.left() + 24, y, pr.width() - 48, 20), ("toggle", key)))
            y += 28

    def _page_save(self, p, pr):
        y = self._head(p, pr, "Saved")
        f = QFont(SERIF, 13)
        f.setItalic(True)
        p.setFont(f)
        p.setPen(INK)
        p.drawText(QRectF(pr.left() + 28, y, pr.width() - 56, 120), Qt.AlignLeft | Qt.TextWordWrap,
                   (self.said or "") + "\n\nThe night saves itself, too, as each act begins. F5 saves wherever you stand.")

    def _page_leave(self, p, pr):
        y = self._head(p, pr, "Leave the night?")
        f = QFont(SERIF, 12)
        f.setItalic(True)
        p.setFont(f)
        p.setPen(INK)
        p.drawText(QRectF(pr.left() + 28, y, pr.width() - 56, 80), Qt.AlignLeft | Qt.TextWordWrap,
                   "Back to the title. What's saved - the act begun, or your own save - you can go on from there.")
        y += 96
        p.setFont(QFont(SERIF, 14))
        for text, act, x in (("Leave", ("leave", None), pr.left() + 40), ("Stay", ("stay", None), pr.left() + 170)):
            r = QRectF(x, y, 100, 30)
            p.setPen(QPen(QColor(90, 66, 46), 1.5))
            p.setBrush(QColor(0, 0, 0, 0))
            p.drawRoundedRect(r, 4, 4)
            p.setPen(INK)
            p.drawText(r, Qt.AlignCenter, text)
            self.hits.append((r, act))

    _page_go = _page_notes
