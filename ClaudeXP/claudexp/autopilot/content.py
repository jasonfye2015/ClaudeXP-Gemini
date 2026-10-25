"""Kithylin's quieter legs: looking through Local Storage the way a person does on a slow evening - reading comics a
page at a time, paging through artists' portfolios and the art CDs, scrolling through stories and old chat logs at
reading speed, wandering drive E: in Explorer and the Picture Viewer, reading Wikipedia in Kiwix, music in ClaudeAmp,
and writing in his LiveJournal.

The pace is a person's: a comic page is looked at for 15-45 seconds, a picture for 5-20, a page of text scrolls about
as fast as it can be read (around 250 words a minute). Between actions the hands are let go, so an IM can be answered
in the middle of a comic and he comes back to it."""
import json
import os
import random
import threading
import time
from pathlib import Path

from PySide6.QtCore import QPoint, Qt
from shiboken6 import isValid

from claudecore.autopilot.engine import BACKGROUND, FOREGROUND, Leg
from claudecore.autopilot.voice import persona

from .. import clock, programs
from .legs import ask, focus

AUDIO = {".mp3", ".ogg", ".wav", ".wma", ".m4a", ".flac", ".mid", ".midi"}
IMAGES = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}
CONTAINERS = {"disc", "album", "folder", "shelf", "artist", "folio", "year", "month", "service", "account", "buddy",
              "room"}


# ---- shared steps ----------------------------------------------------------------------------------------------
def acting(ctx, key, win=None):
    """`yield from acting(ctx, key, win)` before using the mouse; ctx.hands.release(key) after. With a window, it's
    brought to the front first if something else (a game, an IM) has come over it."""
    yield from ctx.hands.take(key)
    if win is not None and isValid(win) and ctx.desktop.active is not win:
        yield from focus(ctx, win)


def item_point(view, item):
    """(viewport, centre of an item's rectangle) for the cursor, or the view itself when it's off screen."""
    rect = view.visualItemRect(item)
    if rect.isValid() and view.viewport().rect().intersects(rect):
        return view.viewport(), rect.center()
    return view, view.rect().center()


def pick_tile(ctx, wall, kinds, avoid=()):
    """A random visible tile on a gallery wall whose node is one of these kinds: (item, node) or (None, None)."""
    found = []
    for i in range(wall.count()):
        item = wall.item(i)
        node = item.data(Qt.UserRole)
        if item.isHidden() or node is None or getattr(node, "kind", None) not in kinds:
            continue
        if getattr(node, "key", None) in avoid:
            continue
        found.append((item, node))
    return random.choice(found) if found else (None, None)


def click_tile(ctx, wall, item, then):
    """Scroll a tile into view, move the pointer onto it, and open it."""
    wall.scrollToItem(item)
    yield 0.3
    widget, point = item_point(wall, item)
    yield from ctx.hands.move_to((widget, point))
    yield 0.25 * ctx.pace
    wall.setCurrentItem(item)
    yield from ctx.hands.click((widget, point), action=then)


def scroll_bar(ctx, bar, pixels, secs=1.2):
    """Scroll a scroll bar by some pixels, smoothly, the way a wheel or a dragged thumb would."""
    start = bar.value()
    end = max(bar.minimum(), min(bar.maximum(), start + int(pixels)))
    steps = max(4, int(secs / 0.04))
    for i in range(1, steps + 1):
        t = i / steps
        bar.setValue(int(start + (end - start) * (t * t * (3 - 2 * t))))
        yield 0.04
    return end != start


def read_secs(ctx, pixels, line_px=18, words_per_line=11, wpm=250):
    """How long a person takes to read so many pixels of text."""
    lines = max(1.0, pixels / line_px)
    return lines * words_per_line / wpm * 60 * ctx.pace * random.uniform(0.8, 1.25)


def close(win):
    if win is not None and isValid(win):
        try:
            win.request_close()
        except Exception:
            pass


def window_of(module):
    win = getattr(module, "_open", {}).get("win")
    return win if win is not None and isValid(win) else None


# ---- FurComix Reader -------------------------------------------------------------------------------------------
class Comics(Leg):
    """FurComix Reader: picks up a comic he was reading, or browses the shelves for one, and reads it a page at a time,
    scrolling down a tall page before turning it."""
    key, title, kind = "comics", "Reading comics", FOREGROUND
    minutes, weight, cooldown = (15, 40), 1.1, 35 * 60
    blurb = "read comics in FurComix Reader, a page at a time"

    def run(self, ctx):
        from comix import library as L
        from comix import reader as R
        yield from acting(ctx, self.key)
        try:
            ctx.status("Opening FurComix Reader")
            programs.launch(ctx.desktop, "comix")
            win = window_of(R)
            if win is None:
                return
            rd = win.content
            yield from focus(ctx, win)
            yield 2 * ctx.pace
            if rd.root is None:
                ctx.note("No comics on drive E:.")
                return
        finally:
            ctx.hands.release(self.key)
        books = 0
        try:
            while ctx.time_left() > 0 and not ctx.stopping and isValid(win):
                entry = yield from self.choose(ctx, rd, L)
                if entry is None:
                    break
                books += 1
                yield from self.read(ctx, rd, entry)
                if random.random() < 0.35:
                    break                                       # one or two comics is a good sitting
        finally:
            if isValid(win):
                yield from acting(ctx, self.key, win)
                try:
                    if rd.reading is not None:
                        rd.close_book()
                    yield 1
                    close(win)
                finally:
                    ctx.hands.release(self.key)

    def choose(self, ctx, rd, L):
        """A comic to read: the one he left off (often), else down the shelves to something."""
        yield from acting(ctx, self.key, rd.frame)
        try:
            recent = [e for e in L.recent(rd.state) if e.kind == "comic"]
            if recent and random.random() < 0.55:
                entry = random.choice(recent[:3])
                ctx.status(f"Picking up {entry.name} again")
                item = next((i for i in rd.recent.items_for(entry.key)), None) if rd.recent.isVisible() else None
                if item is not None:
                    yield from click_tile(ctx, rd.recent, item, lambda: rd.open_entry(entry))
                else:
                    rd.open_entry(entry)
                return entry
            rd.go_home()
            for _depth in range(5):
                yield random.uniform(2, 5) * ctx.pace            # looking along the shelf
                item, node = pick_tile(ctx, rd.grid, {"comic", "shelf"})
                if item is None:
                    return None
                if node.kind == "shelf":
                    ctx.status(f"Browsing {L.nice_name(node.path.name)}")
                    yield from click_tile(ctx, rd.grid, item, lambda n=node: rd.open_entry(n))
                    continue
                ctx.status(f"Opening {node.name}")
                yield from click_tile(ctx, rd.grid, item, lambda n=node: rd.open_entry(n))
                return node
            return None
        finally:
            ctx.hands.release(self.key)

    def read(self, ctx, rd, entry):
        v = rd.viewer
        yield 2 * ctx.pace
        pages_read = 0
        while ctx.time_left() > 0 and not ctx.stopping and rd.reading is not None and v.book is not None:
            n = len(v.book.pages)
            ctx.status(f"Reading {entry.name}, page {v.page + 1} of {n}")
            canvas = v.canvas
            yield random.uniform(12, 30) * ctx.pace             # taking in the page
            while canvas.offset < canvas.max_offset() and ctx.time_left() > 0:
                yield from acting(ctx, self.key, rd.frame)
                try:
                    yield from ctx.hands.move_to(canvas)
                    step = min(canvas.height() * 0.6, canvas.max_offset() - canvas.offset)
                    for _ in range(6):
                        canvas.scroll_by(step / 6)
                        yield 0.05
                finally:
                    ctx.hands.release(self.key)
                yield random.uniform(6, 14) * ctx.pace
            if v.page + 1 >= n:
                ctx.note(f"Finished {entry.name}.")
                yield from acting(ctx, self.key, rd.frame)
                try:
                    v.next_page()                               # past the end: back to the shelf
                finally:
                    ctx.hands.release(self.key)
                return
            yield from acting(ctx, self.key, rd.frame)
            try:
                yield from ctx.hands.click((canvas, QPoint(int(canvas.width() * 0.85), canvas.height() // 2)),
                                           action=v.next_page)
            finally:
                ctx.hands.release(self.key)
            pages_read += 1


# ---- the picture galleries: FurFolio, Personal Image Gallery, Misc Furry Images, Art CDs, Camera Rolls ------------
class _Gallery(Leg):
    """Down a gallery's walls - artist, folio, album, disc, folder - to a wall of pictures, then through them in the
    framed viewer, a few seconds each, and on to another wall."""
    kind = FOREGROUND
    minutes, weight, cooldown = (10, 30), 1.0, 30 * 60
    program = ""                # the program key
    app = ""                    # its name, for the status line
    module = ""                 # where its window is kept
    noun = "pictures"

    def run(self, ctx):
        import importlib
        mod = importlib.import_module(self.module)
        yield from acting(ctx, self.key)
        try:
            ctx.status(f"Opening {self.app}")
            programs.launch(ctx.desktop, self.program)
            yield (lambda: window_of(mod) is not None, 20)
            win = window_of(mod)
            if win is None:
                return
            g = win.content
            yield from focus(ctx, win)
            yield 2 * ctx.pace
            if getattr(g, "root", None) is None:
                ctx.note(f"Nothing for {self.app} on drive E:.")
                return
        finally:
            ctx.hands.release(self.key)
        seen = set()
        try:
            while ctx.time_left() > 0 and not ctx.stopping and isValid(win):
                found = yield from self.find_pictures(ctx, g, seen)
                if not found:
                    break
                yield from self.look(ctx, g)
        finally:
            if isValid(win):
                yield from acting(ctx, self.key)
                try:
                    if g.stack.currentWidget() is g.viewer:
                        g.close_viewer()
                    yield 1
                    close(win)
                finally:
                    ctx.hands.release(self.key)

    def home(self, g):
        if hasattr(g, "go_home"):
            g.go_home()
        elif hasattr(g, "show_rack"):
            g.show_rack()

    def find_pictures(self, ctx, g, seen):
        """Down through the walls to one with pictures on it. True when there."""
        yield from acting(ctx, self.key, g.frame)
        try:
            self.home(g)
            yield random.uniform(2, 4) * ctx.pace
            for _depth in range(6):
                pieces = [n for _i, n in [pick_tile(ctx, g.wall, {"piece"})] if n is not None]
                folders = [x for x in [pick_tile(ctx, g.wall, CONTAINERS, avoid=seen)] if x[0] is not None]
                if pieces and (not folders or random.random() < 0.75):
                    return True
                if not folders:
                    return False
                item, node = folders[0]
                seen.add(getattr(node, "key", None))
                ctx.status(f"{self.app}: {node.name.splitlines()[0][:50]}")
                yield from click_tile(ctx, g.wall, item, lambda n=node: g.open_node(n))
                yield random.uniform(2, 5) * ctx.pace               # looking over the wall
            return bool([n for _i, n in [pick_tile(ctx, g.wall, {"piece"})] if n is not None])
        finally:
            ctx.hands.release(self.key)

    def look(self, ctx, g):
        yield from acting(ctx, self.key, g.frame)
        try:
            item, node = pick_tile(ctx, g.wall, {"piece"})
            if item is None:
                return
            yield from click_tile(ctx, g.wall, item, lambda n=node: g.open_node(n))
        finally:
            ctx.hands.release(self.key)
        v = g.viewer
        count = random.randint(6, 25)
        for _ in range(count):
            if ctx.time_left() <= 0 or ctx.stopping or g.stack.currentWidget() is not v:
                break
            cur = v.current()
            ctx.status(f"Looking at {cur.name[:50] if cur else 'a picture'} ({v.index + 1} of {len(v.nodes)})")
            yield random.uniform(5, 20) * ctx.pace
            yield from acting(ctx, self.key, g.frame)
            try:
                easel = v.easel
                yield from ctx.hands.click((easel, QPoint(int(easel.width() * 0.9), easel.height() // 2)),
                                           action=v.next)
            finally:
                ctx.hands.release(self.key)
        yield from acting(ctx, self.key, g.frame)
        try:
            g.close_viewer()
        finally:
            ctx.hands.release(self.key)
        yield random.uniform(2, 5) * ctx.pace


class Portfolios(_Gallery):
    key, title, app, program, module = "portfolios", "Art portfolios", "FurFolio Reader", "folio", "folio.gallery"
    blurb = "page through artists' portfolios in FurFolio Reader"


class Pictures(_Gallery):
    key, title, app, program, module = "pictures", "Your pictures", "Personal Image Gallery", "photos", "folio.photos"
    blurb = "look through your own picture folders"
    weight = 0.8


class MiscArt(_Gallery):
    key, title, app, program, module = "miscart", "Misc furry art", "Misc Furry Image Viewer", "miscfurry", "folio.miscfurry"
    blurb = "browse the numbered albums of assorted furry art"


class ArtCDs(_Gallery):
    key, title, app, program, module = "artcds", "Art CDs", "Fur CD Viewer", "cdviewer", "folio.cdviewer"
    blurb = "pull an art CD off the rack and look through it"
    weight = 0.7


class CameraRoll(_Gallery):
    key, title, app, program, module = "camroll", "Old phone photos", "Camera Roll Archive", "camroll", "folio.camroll"
    blurb = "flip through a month of old phone photos"
    weight = 0.5


# ---- FurStory Reader -------------------------------------------------------------------------------------------
class Stories(Leg):
    """FurStory Reader: carries on with a story, or takes one off the shelf, and reads it, scrolling at reading
    speed and on into the next chapter."""
    key, title, kind = "stories", "Reading a story", FOREGROUND
    minutes, weight, cooldown = (15, 45), 0.9, 40 * 60
    blurb = "read a story in FurStory Reader, scrolling at reading speed"

    def run(self, ctx):
        from folio import stories as S
        yield from acting(ctx, self.key)
        try:
            ctx.status("Opening FurStory Reader")
            programs.launch(ctx.desktop, "stories")
            win = window_of(S)
            if win is None:
                return
            r = win.content
            yield from focus(ctx, win)
            yield 2 * ctx.pace
            books = S.list_books(S.stories_root()) if S.stories_root() else []
            if not books:
                ctx.note("No stories on drive E:.")
                return
            if r._last_read() is not None and random.random() < 0.6:
                ctx.status("Picking the story up where he left it")
                r.continue_reading()
            else:
                book = random.choice(books)
                ctx.status(f"Taking {book.name} off the shelf")
                yield random.uniform(3, 8) * ctx.pace
                r.open_book(book)
                yield random.uniform(3, 6) * ctx.pace               # the contents page
                if not r.chapters:
                    return
                r.read(0)
        finally:
            ctx.hands.release(self.key)
        try:
            while ctx.time_left() > 0 and not ctx.stopping and isValid(win):
                if r.stack.currentIndex() != 2:
                    break
                bar = r.page.verticalScrollBar()
                title = r.chapter_label.text().split(":", 1)[-1].strip()[:50]
                ctx.status(f"Reading {r.book.name[:40]}: {title}")
                page_px = r.page.viewport().height()
                yield read_secs(ctx, page_px * 0.85)
                if bar.value() < bar.maximum():
                    yield from acting(ctx, self.key, win)
                    try:
                        yield from ctx.hands.move_to(r.page)
                        yield from scroll_bar(ctx, bar, page_px * 0.85)
                    finally:
                        ctx.hands.release(self.key)
                elif r.index + 1 < len(r.chapters):
                    yield from acting(ctx, self.key, win)
                    try:
                        yield from ctx.hands.click(r.next_btn, action=lambda: r.step(1))
                    finally:
                        ctx.hands.release(self.key)
                    yield 2 * ctx.pace
                else:
                    ctx.note(f"Finished {r.book.name}.")
                    break
        finally:
            if isValid(win):
                yield from acting(ctx, self.key, win)
                try:
                    close(win)
                finally:
                    ctx.hands.release(self.key)


# ---- old chat logs ---------------------------------------------------------------------------------------------
class ChatLogs(Leg):
    """Furry Chat Logs: down to an old conversation with someone and reading a year of it, scrolling slowly - the
    nostalgic kind of evening."""
    key, title, kind = "chatlogs", "Old chat logs", FOREGROUND
    minutes, weight, cooldown = (10, 25), 0.7, 45 * 60
    blurb = "reread old conversations in Furry Chat Logs"

    def run(self, ctx):
        from chatlogs import viewer as V
        yield from acting(ctx, self.key)
        try:
            ctx.status("Opening Furry Chat Logs")
            programs.launch(ctx.desktop, "chatlogs")
            win = window_of(V)
            if win is None:
                return
            c = win.content
            yield from focus(ctx, win)
            yield 2 * ctx.pace
            if getattr(c, "db", None) is None:
                ctx.note("The chat log index isn't built.")
                return
        finally:
            ctx.hands.release(self.key)
        try:
            while ctx.time_left() > 0 and not ctx.stopping and isValid(win):
                if not (yield from self.pick_conversation(ctx, c, win)):
                    break
                yield from self.read_conversation(ctx, c, win)
        finally:
            if isValid(win):
                yield from acting(ctx, self.key, win)
                try:
                    close(win)
                finally:
                    ctx.hands.release(self.key)

    def pick_conversation(self, ctx, c, win):
        """Down from the services to someone, then to a stretch of the conversation with a good many lines."""
        yield from acting(ctx, self.key, win)
        try:
            c.show_rack()
            for kinds in ({"service"}, {"account"}, {"buddy"}):
                yield random.uniform(2, 5) * ctx.pace
                item, node = pick_tile(ctx, c.wall, kinds)
                if item is None:
                    return False
                ctx.status(f"Old logs: {node.name.splitlines()[0][:50]}")
                yield from click_tile(ctx, c.wall, item, lambda n=node: c.open_node(n))
            t = c.transcript
            sizes = [n for _l, _lo, _hi, n in t.periods]
            busy = [i for i, n in enumerate(sizes) if n >= 60] or list(range(len(sizes)))
            if busy:
                t.periods_box.setCurrentIndex(random.choice(busy))
            return True
        finally:
            ctx.hands.release(self.key)

    def read_conversation(self, ctx, c, win):
        """Read on at reading speed; at the end of one stretch, on into the next (most of the time)."""
        t = c.transcript
        bar = t.view.verticalScrollBar()
        while ctx.time_left() > 0 and not ctx.stopping and isValid(win) and c.stack.currentWidget() is t:
            ctx.status(f"Rereading {t.title.text()[:40]}, {t.periods_box.currentText()[:24]}")
            yield read_secs(ctx, t.view.viewport().height() * 0.8, words_per_line=7)
            if bar.value() >= bar.maximum():
                if t.next.isEnabled() and random.random() < 0.7:
                    yield from acting(ctx, self.key, win)
                    try:
                        yield from ctx.hands.click(t.next)
                    finally:
                        ctx.hands.release(self.key)
                    yield 1.5
                    continue
                return
            yield from acting(ctx, self.key, win)
            try:
                yield from ctx.hands.move_to(t.view)
                yield from scroll_bar(ctx, bar, t.view.viewport().height() * 0.8)
            finally:
                ctx.hands.release(self.key)


# ---- Explorer on drive E: ---------------------------------------------------------------------------------------
class ExploreDrive(Leg):
    """My Computer > drive E: (Local Storage), down a few folders the way you poke around a backup drive, opening
    pictures in the Picture and Fax Viewer and stepping through the ones beside them."""
    key, title, kind = "explore", "Exploring drive E:", FOREGROUND
    minutes, weight, cooldown = (8, 20), 0.8, 30 * 60
    blurb = "poke around drive E: in Explorer and open pictures"
    SKIP = {"llm models", "python studio", "secondlife", "_index", "__pycache__", "projects", "emulation", "wads"}

    def run(self, ctx):
        from ..explorer import launch as explore, vfs
        root = Path(vfs.local_storage())
        if not root.is_dir():
            return
        from ..explorer import MY_COMPUTER
        yield from acting(ctx, self.key)
        try:
            ctx.status("Opening My Computer")
            win = explore(ctx.desktop, MY_COMPUTER)
            ex = win.content
            yield from focus(ctx, win)
            yield random.uniform(1.5, 3) * ctx.pace
            ctx.status("Opening drive E:")
            yield from ctx.hands.move_to(ex)
            ex.navigate(root)                                # (a sleeping drive spins up first, as on a real PC)
            yield (lambda: isinstance(ex.location, Path), 30)
            yield 2 * ctx.pace
        finally:
            ctx.hands.release(self.key)
        if not isinstance(ex.location, Path):
            return
        viewer = None
        try:
            here = root
            for _depth in range(random.randint(2, 5)):
                if ctx.time_left() <= 0 or ctx.stopping or not isValid(win):
                    break
                try:
                    kids = [p for p in here.iterdir() if p.is_dir() and not p.name.startswith((".", "_"))
                            and p.name.lower() not in self.SKIP]
                    pics = [p for p in here.iterdir() if p.suffix.lower() in IMAGES]
                except OSError:
                    break
                ctx.status(f"Looking in {here.name}")
                yield random.uniform(4, 10) * ctx.pace
                if pics and (not kids or random.random() < 0.5):
                    viewer = yield from self.view(ctx, ex, random.choice(pics))
                    break
                if not kids:
                    break
                here = random.choice(kids)
                yield from acting(ctx, self.key, win)
                try:
                    yield from ctx.hands.move_to(ex.active_view())
                    ex.navigate(here)
                finally:
                    ctx.hands.release(self.key)
        finally:
            if isValid(win) and not ctx.stopping:
                yield from acting(ctx, self.key)
                try:
                    if viewer is not None and isValid(viewer):
                        close(viewer)
                    close(win)
                finally:
                    ctx.hands.release(self.key)

    def view(self, ctx, ex, path):
        from ..explorer.viewers import PictureViewer
        yield from acting(ctx, self.key)
        try:
            ctx.status(f"Opening {path.name}")
            yield from ctx.hands.move_to(ex.active_view())
            PictureViewer.open(ctx.desktop, path)
            yield 1
            frame = ctx.desktop.active
        finally:
            ctx.hands.release(self.key)
        pv = frame.content if frame is not None and isinstance(getattr(frame, "content", None), PictureViewer) else None
        if pv is None:
            return frame
        for _ in range(random.randint(4, 15)):
            if ctx.time_left() <= 0 or ctx.stopping or not isValid(frame):
                break
            ctx.status(f"Looking at {pv.path.name}")
            yield random.uniform(5, 15) * ctx.pace
            yield from acting(ctx, self.key, frame)
            try:
                yield from ctx.hands.click(frame, action=lambda: pv.step(1))
            finally:
                ctx.hands.release(self.key)
        return frame


# ---- Kiwix ------------------------------------------------------------------------------------------------------
class Wikipedia(Leg):
    """Kiwix: a random Wikipedia article, read and scrolled through, then a link that caught his eye, and so on."""
    key, title, kind = "wikipedia", "Reading Wikipedia", FOREGROUND
    minutes, weight, cooldown = (10, 25), 0.8, 35 * 60
    blurb = "wander Wikipedia offline in Kiwix"

    def js(self, view, code):
        box = {}
        view.page().runJavaScript(code, lambda r: box.__setitem__("r", r))
        yield (lambda: "r" in box, 15)
        return box.get("r")

    def run(self, ctx):
        from ..programs import kiwix as K
        from ..programs.kiwix import library
        if not library.books():
            return
        yield from acting(ctx, self.key)
        try:
            ctx.status("Opening Kiwix")
            win = K.launch(ctx.desktop)
            kw = win.content
            yield from focus(ctx, win)
            yield 2 * ctx.pace
            kw.random_article()
            yield 4
        finally:
            ctx.hands.release(self.key)
        try:
            while ctx.time_left() > 0 and not ctx.stopping and isValid(win):
                book = kw._current_book()
                if book is None:
                    break
                view = book.view
                ctx.status(f"Reading {view.title()[:60] or 'Wikipedia'}")
                for _ in range(random.randint(2, 6)):
                    yield read_secs(ctx, view.height() * 0.8, words_per_line=14)
                    if ctx.time_left() <= 0 or ctx.stopping:
                        break
                    yield from acting(ctx, self.key, win)
                    try:
                        yield from ctx.hands.move_to(view)
                        for _s in range(8):
                            view.page().runJavaScript(f"window.scrollBy(0, {int(view.height() * 0.1)})")
                            yield 0.06
                    finally:
                        ctx.hands.release(self.key)
                yield from acting(ctx, self.key, win)
                try:
                    if random.random() < 0.6:
                        went = yield from self.js(view, "(function(){const a=[...document.querySelectorAll("
                                                        "'#mw-content-text a[href], .mw-parser-output a[href], p a[href]')]"
                                                        ".filter(a=>!/^(#|http)|:/.test(a.getAttribute('href')));"
                                                        "if(!a.length)return '';const x=a[Math.floor(Math.random()*a.length)];"
                                                        "const t=x.textContent;x.click();return t;})()")
                        if went:
                            ctx.note(f"Wikipedia: followed a link to {went}")
                        else:
                            kw.random_article()
                    else:
                        kw.random_article()
                finally:
                    ctx.hands.release(self.key)
                yield 3
        finally:
            if isValid(win):
                yield from acting(ctx, self.key, win)
                try:
                    close(win)
                finally:
                    ctx.hands.release(self.key)


# ---- music (background) ------------------------------------------------------------------------------------------
_songs = {"list": None, "busy": False}


def find_songs(root, limit=600):
    """Music on drive E: (found once, in the background, and kept in data/)."""
    from ..paths import DATA
    cache = DATA / "autopilot_music.json"
    try:
        data = json.loads(cache.read_text(encoding="utf-8"))
        if data.get("root") == str(root):
            return [p for p in data["songs"] if os.path.exists(p)]
    except (OSError, ValueError, KeyError):
        pass
    found = []
    skip = {"llm models", "python studio", "secondlife", "tv and movies", "camera rolls", "emulation", "projects"}
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d.lower() not in skip and not d.startswith(".")]
        found += [os.path.join(dirpath, f) for f in files if os.path.splitext(f)[1].lower() in AUDIO]
        if len(found) >= limit:
            break
    try:
        cache.write_text(json.dumps({"root": str(root), "songs": found}), encoding="utf-8")
    except OSError:
        pass
    return found


class Music(Leg):
    """ClaudeAmp: a shuffled playlist of whatever music is on drive E:, playing behind everything else."""
    key, title, kind = "music", "Music in ClaudeAmp", BACKGROUND
    minutes, weight, cooldown = (20, 60), 0.9, 30 * 60
    blurb = "put on music in ClaudeAmp while he does other things"

    def run(self, ctx):
        from ..explorer import vfs
        from ..programs import amp
        if _songs["list"] is None and not _songs["busy"]:
            _songs["busy"] = True

            def scan():
                try:
                    _songs["list"] = find_songs(Path(vfs.local_storage()))
                finally:
                    _songs["busy"] = False
            threading.Thread(target=scan, daemon=True).start()
        yield (lambda: _songs["list"] is not None, 120)
        songs = list(_songs["list"] or [])
        if not songs:
            ctx.note("No music on drive E:.")
            return
        random.shuffle(songs)
        yield from acting(ctx, self.key)
        try:
            ctx.status("Putting some music on")
            frame = amp.open_amp(ctx.desktop)
            yield 4                                           # (the Winamp intro)
            if frame is None or not isValid(frame):
                return
            player = frame.content
            yield from focus(ctx, frame)
            player.play_files(songs[:40], replace=True)
            if random.random() < 0.5:
                ctx.desktop.minimize(frame)
        finally:
            ctx.hands.release(self.key)
        ctx.note("Music on.")
        while ctx.time_left() > 0 and not ctx.stopping:
            yield 5
        if not ctx.stopping:
            yield from acting(ctx, self.key)
            try:
                if isValid(frame):
                    player.player.stop()
                    close(frame)
                ctx.note("Music off.")
            finally:
                ctx.hands.release(self.key)


# ---- LiveJournal -------------------------------------------------------------------------------------------------
LJ_NOTE = ("\n\nYou're writing an entry in your LiveJournal in {year}, for your friends to read. Write it as yourself: "
           "what you've been up to today, what's on your mind, casual and warm, a few short paragraphs. First line: "
           "'Subject: ...'. Then the entry. Then a last line 'Mood: ...' with one word.")


class Journal(Leg):
    """LiveJournal: opens his journal, writes an entry about his day, posts it; his friends comment on it later."""
    key, title, kind = "journal", "Writing in LiveJournal", FOREGROUND
    minutes, weight, cooldown = (6, 12), 0.5, 3 * 60 * 60
    blurb = "write a LiveJournal entry about his day"

    def run(self, ctx):
        from ..life import get as life
        from ..life import lj
        from ..programs.navigator import iexplore
        from ..programs.navigator.sites import livejournal as site
        from .legs import ensure_online
        sim = life()
        if sim is None:
            return
        yield from acting(ctx, self.key)
        try:
            yield from ensure_online(ctx)
            ctx.status("Opening LiveJournal")
            site.open_livejournal(ctx.desktop)
            yield (lambda: iexplore._frame is not None, 30)
            frame = iexplore._frame
            if frame is not None:
                yield from focus(ctx, frame)
        finally:
            ctx.hands.release(self.key)
        yield random.uniform(10, 25) * ctx.pace                 # reading the friends page
        doing = [t.leg.title for t in ctx.engine.tasks.values() if t.leg.key != self.key]
        context = (f"Today you've been: {', '.join(doing) or 'around the house'}. It's "
                   f"{clock.now():%A, %B} {clock.now().day}, {clock.time_text()}.")
        ctx.status("Writing a journal entry")
        text = yield from ask(ctx, persona("your friends") + LJ_NOTE.format(year=clock.now().year),
                              [{"role": "user", "content": context}], "Write today's entry.", max_tokens=380)
        if not text:
            return
        lines = text.splitlines()
        subject = lines[0].split(":", 1)[1].strip() if lines and lines[0].lower().startswith("subject:") else ""
        body = [l for l in (lines[1:] if subject else lines)]
        mood = ""
        if body and body[-1].lower().startswith("mood:"):
            mood = body.pop().split(":", 1)[1].strip()
        entry_text = "\n".join(body).strip()
        if not entry_text:
            return
        yield min(120, 5 + len(entry_text) / 12) * ctx.pace     # typing it out
        friends = sorted(sim.buddies) if getattr(sim, "buddies", None) else []

        def change(data):
            entry = lj.new_entry(data, subject, entry_text, mood, "", "public")
            lj.queue_comments_on(data, entry, friends)
        lj.update(change)
        ctx.note(f"Posted to LiveJournal: {subject or entry_text[:40]}")
        if frame is not None and isValid(frame):
            yield from acting(ctx, self.key, frame)
            try:
                frame.content.navigate("http://www.livejournal.com" + site._u(site._me()))
            finally:
                ctx.hands.release(self.key)
            yield random.uniform(10, 20) * ctx.pace         # admiring it
            if isValid(frame) and random.random() < 0.7:
                yield from acting(ctx, self.key, frame)
                try:
                    yield from ctx.hands.click((frame, QPoint(frame.width() - 14, 12)), action=frame.request_close)
                finally:
                    ctx.hands.release(self.key)


CONTENT_LEGS = [Comics, Portfolios, Pictures, MiscArt, ArtCDs, CameraRoll, Stories, ChatLogs, ExploreDrive,
                Wikipedia, Music, Journal]
