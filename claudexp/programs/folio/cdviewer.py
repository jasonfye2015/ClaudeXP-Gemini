"""Fur CD Viewer: the artists' art CDs and DVDs on E: (Local Storage/Furry Media Archive.../Art CDs and DVDs...).

The discs stand in a rack as jewel cases (DVDs as black keep cases) with their own cover art. Opening one browses
it like a gallery: folders as tiles with a peek at their first picture, pictures as thumbnails, videos as film
tiles, Flash movies as Flash cards. A disc's own thumbnail folders, programs, web pages and DVD menu files are left
out. Pictures open in FurFolio's framed viewer, videos (AVI, MPEG, the DVD's VOBs) play in a little built-in player,
and Flash opens in Macromedia Flash Player.

Like the other readers, nothing is scanned ahead: each folder is listed when it's opened and thumbnails are made
as they scroll into view (cached in data/folio_thumbs)."""
import ctypes
import hashlib
import os
import re
from pathlib import Path

from PySide6.QtCore import QObject, QPointF, QRectF, QSize, Qt, QTimer, QUrl, Signal
from PySide6.QtGui import QColor, QFont, QIcon, QImage, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer, QVideoSink
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QLabel, QLineEdit, QSlider, QStackedWidget, QToolButton,
                               QVBoxLayout, QWidget)
from shiboken6 import isValid

from ...paths import DATA
from ...wm import XPWindow
from ..comix.library import IMAGE_EXTS, natural_key, nice_name
from ..comix.reader import Loader
from .gallery import THUMB, THUMBS, TILE, Node, Viewer, Wall, make_thumb, piece_title

VIDEO_EXTS = {".avi", ".mpg", ".mpeg", ".vob", ".mp4", ".wmv", ".mov", ".m4v", ".mkv", ".asf", ".rm", ".ram"}
SHOW_IMAGES = IMAGE_EXTS | {".svg", ".jpe"} | {".pcx", ".iff", ".lbm", ".ilbm", ".ham", ".ham6", ".ham8", ".iff24"}
SOUND_EXTS = {".wav", ".mp3", ".mid", ".midi", ".rmi", ".snd", ".au", ".aif", ".aiff", ".wma", ".ogg"}
ARCHIVE_EXTS = {".zip", ".lzh", ".lha", ".tar"}              # opened like folders (via a cache in data/)
ARCHIVE_CACHE = DATA / "cd_archives"
SKIP_DIRS = {"thumbnails", "thumbnail", "thumbs", "thumb", "tn", "_vti_cnf", "_vti_pvt", "audio_ts", "autorun",
             "__macosx", "_notes", "cgi-bin"}
COVER_WORDS = ("cover", "front", "title", "large", "info", "disc", "cd", "dvd", "logo")
MIN_VOB = 2 * 2 ** 20                      # DVD menus are tiny VOBs; the movie parts are big


def cd_icon():
    pm = QPixmap(32, 32)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    g = QLinearGradient(4, 4, 28, 28)
    for stop, c in ((0, "#E8F0FF"), (0.3, "#B8F0D0"), (0.5, "#F8E0F8"), (0.7, "#C0D8FF"), (1, "#E0E0E0")):
        g.setColorAt(stop, QColor(c))
    p.setPen(QPen(QColor("#707070"), 1))
    p.setBrush(g)
    p.drawEllipse(QRectF(2.5, 2.5, 27, 27))
    p.setBrush(QColor("#D8D8D8"))
    p.drawEllipse(QRectF(11.5, 11.5, 9, 9))
    p.setBrush(Qt.white)
    p.drawEllipse(QRectF(14.5, 14.5, 3, 3))
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#E8261C"))
    paw = [(6, 22, 3.2), (9, 25.5, 2), (5, 18.5, 1.8), (9.5, 19.5, 1.8)]
    for x, y, r in paw:
        p.drawEllipse(QRectF(x - r, y - r, 2 * r, 2 * r))
    p.end()
    return QIcon(pm)


def discs_root():
    from .. import archive_folder
    archive = archive_folder("mediaarchive")
    if archive is None:
        return None
    return next((d for d in sorted(archive.iterdir()) if d.is_dir() and d.name.lower().startswith("art cd")), None)


def disc_name(name):
    n = nice_name(name)
    n = re.sub(r"\s+(CD|DVD|Art CD|Art Cd)$", "", n, flags=re.I).strip(" -")
    return re.sub(r"\s{2,}", " ", n)


# ---- listing ------------------------------------------------------------------------------------------------------

def listing(folder):
    """(sub-folders, pictures, videos) worth showing in a folder (names only)."""
    dirs, pics, vids = [], [], []
    try:
        with os.scandir(folder) as it:
            for e in it:
                name = e.name
                low = name.lower()
                if low.startswith(".") or low in ("thumbs.db", "desktop.ini"):
                    continue
                ext = os.path.splitext(low)[1]
                if e.is_dir():
                    if low not in SKIP_DIRS and not low.startswith(("thumb", "_vti")):
                        dirs.append(name)
                elif ext in SHOW_IMAGES:
                    if not re.match(r"(tn_|thumb_|th_|t_|sm_)", low) and not re.search(r"(_tn|_thumb|_t|_sm)\.", low):
                        pics.append(name)
                elif ext in VIDEO_EXTS:
                    if ext == ".vob":
                        try:
                            if e.stat().st_size < MIN_VOB:
                                continue
                        except OSError:
                            continue
                    vids.append(name)
    except OSError:
        pass
    return sorted(dirs, key=natural_key), sorted(pics, key=natural_key), sorted(vids, key=natural_key)


def extras(folder):
    """(sounds, archives) in a folder that the gallery also offers."""
    sounds, archives = [], []
    try:
        with os.scandir(folder) as it:
            for e in it:
                if e.is_dir():
                    continue
                ext = os.path.splitext(e.name.lower())[1]
                if ext in SOUND_EXTS:
                    sounds.append(e.name)
                elif ext in ARCHIVE_EXTS:
                    archives.append(e.name)
    except OSError:
        pass
    return sorted(sounds, key=natural_key), sorted(archives, key=natural_key)


def open_archive(path):
    """Unpack an archive into data/cd_archives/<id>/ (once) and return that folder (None if it can't be read)."""
    path = Path(path)
    try:
        st = path.stat()
    except OSError:
        return None
    dest = ARCHIVE_CACHE / hashlib.sha1(f"{path}|{st.st_size}|{int(st.st_mtime)}".encode()).hexdigest()[:16]
    done = dest / ".unpacked"
    if done.exists():
        return dest
    dest.mkdir(parents=True, exist_ok=True)
    try:
        if path.suffix.lower() == ".zip":
            import zipfile
            with zipfile.ZipFile(path) as z:
                for info in z.infolist():
                    target = (dest / info.filename).resolve()
                    if dest.resolve() in target.parents or target == dest.resolve():   # no escaping the cache
                        z.extract(info, dest)
        elif path.suffix.lower() == ".tar":
            import tarfile
            with tarfile.open(path) as t:
                t.extractall(dest, filter="data")                  # 'data' refuses paths that escape the cache
        else:
            from ..comix.library import _no_window, seven_zip
            exe = seven_zip()
            if exe is None:
                return None
            import subprocess
            r = subprocess.run([exe, "x", str(path), f"-o{dest}", "-y", "-bso0", "-bsp0"], capture_output=True,
                               stdin=subprocess.DEVNULL, **_no_window())
            if r.returncode not in (0, 1):
                return None
    except Exception:
        return None
    done.write_text(str(path), encoding="utf-8")
    return dest


def look_through(folder):
    """Discs often wrap everything in one folder ('[FxA] Chris Mcinley's sketchy reputation art cd')."""
    folder = Path(folder)
    for _ in range(4):
        dirs, pics, vids = listing(folder)
        if len(dirs) == 1 and not pics and not vids:
            folder = folder / dirs[0]
            continue
        return folder, (dirs, pics, vids)
    return folder, listing(folder)


def disc_cover(folder):
    """A disc's own cover art if it has some, else the first picture found near the top (worker thread)."""
    folder, (dirs, pics, _v) = look_through(folder)
    ranked = sorted(pics, key=lambda n: (not any(w in n.lower() for w in COVER_WORDS), natural_key(n)))
    for name in ranked[:6]:
        img = make_thumb(folder / name)
        if not img.isNull():
            return img
    queue = [folder / d for d in dirs[:6]]
    for _ in range(12):
        if not queue:
            break
        f = queue.pop(0)
        sub_dirs, sub_pics, _sv = listing(f)
        for name in sub_pics[:4]:
            img = make_thumb(f / name)
            if not img.isNull():
                return img
        queue += [f / d for d in sub_dirs[:3]]
    return QImage()


# ---- tiles -----------------------------------------------------------------------------------------------------

def _case_tile(node, img):
    """A jewel case for a CD, a black keep case for a DVD."""
    pm = QPixmap(TILE)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setRenderHint(QPainter.SmoothPixmapTransform)
    dvd = "dvd" in node.path.name.lower()
    if dvd:
        case = QRectF(30, 4, TILE.width() - 60, TILE.height() - 10)
        p.fillRect(case.translated(4, 5), QColor(0, 0, 0, 80))
        p.setPen(QPen(QColor("#000"), 1))
        p.setBrush(QColor("#151518"))
        p.drawRoundedRect(case, 4, 4)
        art = case.adjusted(6, 16, -6, -6)
        p.setPen(QColor("#C8C8D0"))
        p.setFont(QFont("Arial Black", 7))
        p.drawText(QRectF(case.left(), case.top() + 2, case.width(), 13), Qt.AlignCenter, "DVD")
    else:
        case = QRectF(10, 18, TILE.width() - 20, TILE.height() - 30)
        p.fillRect(case.translated(4, 5), QColor(0, 0, 0, 80))
        p.setPen(QPen(QColor("#5A6070"), 1))
        p.setBrush(QColor("#2A2E36"))
        p.drawRect(case)
        art = case.adjusted(12, 3, -3, -3)
        p.fillRect(QRectF(case.left() + 1, case.top() + 1, 10, case.height() - 2), QColor("#3C424E"))      # hinge
        p.setPen(QPen(QColor("#6A7280"), 1))
        for y in range(int(case.top()) + 8, int(case.bottom()) - 4, 6):
            p.drawLine(int(case.left() + 3), y, int(case.left() + 8), y)
    if img is not None and not img.isNull():
        scale = max(art.width() / img.width(), art.height() / img.height())         # covers fill the insert
        src_w, src_h = art.width() / scale, art.height() / scale
        src = QRectF((img.width() - src_w) / 2, (img.height() - src_h) / 2, src_w, src_h)
        p.drawImage(art, img, src)
    else:
        p.fillRect(art, QColor("#3A4050"))
        p.setPen(QColor("#A8B0C0"))
        p.setFont(QFont("Tahoma", 8))
        p.drawText(art.adjusted(4, 4, -4, -4), Qt.AlignCenter | Qt.TextWordWrap,
                   "Loading..." if img is None else node.name)
    shine = QLinearGradient(art.topLeft(), art.bottomRight())
    shine.setColorAt(0, QColor(255, 255, 255, 70))
    shine.setColorAt(0.45, QColor(255, 255, 255, 0))
    shine.setColorAt(1, QColor(255, 255, 255, 25))
    p.fillRect(art, shine)                                                              # the plastic
    p.end()
    return pm


def _folder_tile(node, img):
    pm = QPixmap(TILE)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setRenderHint(QPainter.SmoothPixmapTransform)
    body = QRectF(14, 40, TILE.width() - 28, TILE.height() - 52)
    back = QPainterPath()
    back.moveTo(body.left(), body.top() - 12)
    back.lineTo(body.left() + 40, body.top() - 12)
    back.lineTo(body.left() + 50, body.top())
    back.lineTo(body.right(), body.top())
    back.lineTo(body.right(), body.bottom())
    back.lineTo(body.left(), body.bottom())
    back.closeSubpath()
    p.setPen(QPen(QColor("#A07818"), 1))
    p.setBrush(QColor("#E8B840"))
    p.drawPath(back)
    if img is not None and not img.isNull():                                        # a picture poking out
        w = body.width() - 30
        h = min(img.height() * w / img.width(), body.height())
        r = QRectF(body.left() + 15, body.top() - 18, w, h)
        p.fillRect(r.adjusted(-3, -3, 3, 3), Qt.white)
        p.drawImage(r, img)
    front = QPainterPath()
    front.moveTo(body.left(), body.top() + 22)
    front.lineTo(body.right(), body.top() + 16)
    front.lineTo(body.right() - 4, body.bottom())
    front.lineTo(body.left() + 4, body.bottom())
    front.closeSubpath()
    g = QLinearGradient(0, body.top(), 0, body.bottom())
    g.setColorAt(0, QColor("#FFD868"))
    g.setColorAt(1, QColor("#E8A820"))
    p.setBrush(g)
    p.drawPath(front)
    p.end()
    return pm


def _sound_tile(node):
    pm = QPixmap(TILE)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    c = QRectF(TILE.width() / 2 - 34, 30, 68, 68)
    g = QLinearGradient(c.topLeft(), c.bottomRight())
    g.setColorAt(0, QColor("#6AA8F0"))
    g.setColorAt(1, QColor("#1E4A9A"))
    p.setPen(QPen(QColor("#18366E"), 1))
    p.setBrush(g)
    p.drawEllipse(c)
    p.setBrush(QColor("#FFFFFF"))
    p.setPen(Qt.NoPen)
    note = QPainterPath()
    x, y = c.center().x(), c.center().y()
    note.addEllipse(QRectF(x - 14, y + 4, 12, 9))
    note.addEllipse(QRectF(x + 4, y, 12, 9))
    p.drawPath(note)
    p.setPen(QPen(QColor("#FFFFFF"), 3))
    p.drawLine(QPointF(x - 3, y + 8), QPointF(x - 3, y - 16))
    p.drawLine(QPointF(x + 15, y + 4), QPointF(x + 15, y - 20))
    p.drawLine(QPointF(x - 3, y - 16), QPointF(x + 15, y - 20))
    p.setPen(QColor("#303030"))
    p.setFont(QFont("Tahoma", 7, QFont.Bold))
    p.drawText(QRectF(0, c.bottom() + 6, TILE.width(), 14), Qt.AlignCenter,
               os.path.splitext(node.path.name)[1].upper().lstrip("."))
    p.end()
    return pm


def _archive_tile(node):
    """A folder with a zipper, like XP's compressed folders."""
    pm = _folder_tile(node, None)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    x = TILE.width() / 2
    p.fillRect(QRectF(x - 6, 40, 12, TILE.height() - 52), QColor("#707070"))
    p.setPen(QPen(QColor("#D8D8D8"), 1))
    for y in range(44, TILE.height() - 16, 6):
        p.drawLine(QPointF(x - 5, y), QPointF(x + 5, y))
    p.setPen(QColor("#303030"))
    p.setFont(QFont("Tahoma", 7, QFont.Bold))
    p.drawText(QRectF(0, TILE.height() - 14, TILE.width(), 12), Qt.AlignCenter,
               os.path.splitext(node.path.name)[1].upper().lstrip("."))
    p.end()
    return pm


def _video_tile(node, img=None):
    pm = QPixmap(TILE)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    r = QRectF(14, 30, TILE.width() - 28, TILE.height() - 60)
    p.fillRect(r.translated(3, 4), QColor(0, 0, 0, 80))
    p.fillRect(r, QColor("#1A1A1E"))
    p.setBrush(QColor("#E8E8E8"))
    p.setPen(Qt.NoPen)
    for x in range(int(r.left()) + 6, int(r.right()) - 6, 14):                       # sprocket holes
        p.drawRect(QRectF(x, r.top() + 4, 7, 6))
        p.drawRect(QRectF(x, r.bottom() - 10, 7, 6))
    frame = r.adjusted(8, 16, -8, -16)
    if img is not None and not img.isNull():
        scale = max(frame.width() / img.width(), frame.height() / img.height())
        sw, sh = frame.width() / scale, frame.height() / scale
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        p.drawImage(frame, img, QRectF((img.width() - sw) / 2, (img.height() - sh) / 2, sw, sh))
        p.setBrush(QColor(0, 0, 0, 110))
        p.setPen(Qt.NoPen)
        p.drawEllipse(frame.center(), 17, 17)
    else:
        g = QLinearGradient(frame.topLeft(), frame.bottomRight())
        g.setColorAt(0, QColor("#3A5A9A"))
        g.setColorAt(1, QColor("#1A2A4A"))
        p.fillRect(frame, g)
    tri = QPainterPath()
    c = frame.center()
    tri.moveTo(c.x() - 10, c.y() - 13)
    tri.lineTo(c.x() + 14, c.y())
    tri.lineTo(c.x() - 10, c.y() + 13)
    tri.closeSubpath()
    p.setBrush(QColor(255, 255, 255, 220))
    p.drawPath(tri)
    p.setPen(QColor("#D0D0D0"))
    p.setFont(QFont("Tahoma", 7, QFont.Bold))
    p.drawText(QRectF(r.left(), r.bottom() + 2, r.width(), 14), Qt.AlignCenter,
               os.path.splitext(node.path.name)[1].upper().lstrip("."))
    p.end()
    return pm


# ---- video ---------------------------------------------------------------------------------------------------------

class FrameGrabber(QObject):
    """Takes one still a few seconds into each video, one video at a time (QMediaPlayer lives on the UI thread),
    and caches it with the picture thumbnails."""
    grabbed = Signal(object, object)                 # path, QImage

    def __init__(self, parent):
        super().__init__(parent)
        self.queue, self.busy = [], None
        self.player = QMediaPlayer(self)
        self.sink = QVideoSink(self)
        self.player.setVideoSink(self.sink)
        self.sink.videoFrameChanged.connect(self._frame)
        self.player.mediaStatusChanged.connect(self._status)
        self.player.errorOccurred.connect(lambda *_: self._finish(QImage()))
        self.timeout = QTimer(self, singleShot=True, interval=4000, timeout=lambda: self._finish(QImage()))
        self.seeked = self.retried = False

    @staticmethod
    def cache_file(path):
        try:
            st = Path(path).stat()
        except OSError:
            return None
        key = f"{path}|{int(st.st_mtime)}|{st.st_size}|frame"
        return THUMBS / (hashlib.sha1(key.encode()).hexdigest()[:20] + ".jpg")

    def request(self, path):
        f = self.cache_file(path)
        if f is not None and f.exists():
            img = QImage(str(f))
            if not img.isNull():
                QTimer.singleShot(0, lambda: self.grabbed.emit(path, img))
                return
        if path != self.busy and path not in self.queue:
            self.queue.append(path)
        self._next()

    def clear(self):
        self.queue.clear()

    def _next(self):
        if self.busy is not None or not self.queue:
            return
        self.busy = self.queue.pop(0)
        self.seeked = self.retried = False
        self.player.setSource(QUrl.fromLocalFile(str(self.busy)))
        self.player.pause()
        self.timeout.start()

    def _status(self, status):
        if self.busy is None:
            return
        if status in (QMediaPlayer.LoadedMedia, QMediaPlayer.BufferedMedia) and not self.seeked:
            self.seeked = True
            QTimer.singleShot(0, self._seek)        # seeking from inside the player's own signal stalls it
        elif status == QMediaPlayer.InvalidMedia:
            self._finish(QImage())

    def _seek(self):
        if self.busy is not None:
            dur = self.player.duration()
            self.player.setPosition(min(4000, dur // 3) if dur > 0 else 0)
            self.player.play()

    def _frame(self, frame):
        if self.busy is None or not self.seeked or not frame.isValid():
            return
        img = frame.toImage()
        if img.isNull():
            return
        tiny = img.scaled(8, 8).convertToFormat(QImage.Format_Grayscale8)
        dark = sum(tiny.pixelColor(x, y).value() for x in range(8) for y in range(8)) / 64 < 18
        if dark and not self.retried and self.player.duration() > 0:     # a black title card: try further in
            self.retried = True
            self.player.pause()
            QTimer.singleShot(0, lambda: (self.player.setPosition(self.player.duration() // 2), self.player.play()))
            return
        self._finish(img.scaled(THUMB, Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def _finish(self, img):
        path, self.busy = self.busy, None
        self.timeout.stop()
        self.player.stop()
        self.player.setSource(QUrl())
        if path is not None:
            if not img.isNull():
                f = self.cache_file(path)
                try:
                    THUMBS.mkdir(parents=True, exist_ok=True)
                    img.convertToFormat(QImage.Format_RGB32).save(str(f), "JPG", 85)
                except (OSError, TypeError):
                    pass
            self.grabbed.emit(path, img)
        QTimer.singleShot(0, self._next)


class VideoPane(QWidget):
    """A small player: the picture painted from a video sink, play/pause, a seek bar and the time."""

    def __init__(self, owner):
        super().__init__()
        self.owner = owner
        self.frame_img = QImage()
        self.player = QMediaPlayer(self)
        self.audio = QAudioOutput(self)
        self.player.setAudioOutput(self.audio)
        self.sink = QVideoSink(self)
        self.player.setVideoSink(self.sink)
        self.sink.videoFrameChanged.connect(self._frame)
        self.player.positionChanged.connect(self._position)
        self.player.durationChanged.connect(lambda d: self.seek.setRange(0, max(0, d)))
        self.player.playbackStateChanged.connect(self._state)
        self.player.errorOccurred.connect(lambda *_: self.time.setText("This video couldn't be played."))
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        self.screen = QWidget()
        self.screen.paintEvent = self._paint
        self.screen.mouseDoubleClickEvent = lambda e: owner.toggle_full_screen()
        self.screen.mousePressEvent = lambda e: self.toggle()
        lay.addWidget(self.screen, 1)
        bar = QWidget()
        bar.setObjectName("bar")
        bar.setAttribute(Qt.WA_StyledBackground)
        bar.setStyleSheet("QWidget#bar { background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #4A4E58,"
                          " stop:1 #262A32); } QToolButton { color: #E8ECF4; font: 11px Tahoma; padding: 2px 8px;"
                          " border: 1px solid transparent; border-radius: 3px; } QToolButton:hover {"
                          " border-color: #8A94A8; background: #565C6A; } QLabel { color: #E8ECF4; font: 11px Tahoma; }")
        row = QHBoxLayout(bar)
        row.setContentsMargins(4, 3, 8, 3)
        back = QToolButton()
        back.setText("◄ Back")
        back.clicked.connect(owner.close_video)
        row.addWidget(back)
        self.play_btn = QToolButton()
        self.play_btn.setText("❚❚")
        self.play_btn.setFixedWidth(40)
        self.play_btn.clicked.connect(self.toggle)
        row.addWidget(self.play_btn)
        self.seek = QSlider(Qt.Horizontal)
        self.seek.sliderMoved.connect(self.player.setPosition)
        row.addWidget(self.seek, 1)
        self.time = QLabel()
        self.time.setMinimumWidth(90)
        row.addWidget(self.time)
        lay.addWidget(bar)

    def play(self, path, title=""):
        self.stop()
        self.frame_img = QImage()
        self.title = title
        self.time.setText("")
        if Path(path).suffix.lower() in (".mid", ".midi", ".rmi"):
            self.midi = True
            mci = ctypes.windll.winmm.mciSendStringW
            mci("close claudexp_midi", None, 0, None)
            mci(f'open "{Path(path).resolve()}" type sequencer alias claudexp_midi', None, 0, None)
            mci("play claudexp_midi", None, 0, None)
            self.time.setText("MIDI")
            self.play_btn.setText("\u25A0")
            self.screen.update()
            return
        self.midi = False
        self.player.setSource(QUrl.fromLocalFile(str(path)))
        self.player.play()

    def stop(self):
        if getattr(self, "midi", False):
            ctypes.windll.winmm.mciSendStringW("close claudexp_midi", None, 0, None)
            self.midi = False
        self.player.stop()
        self.player.setSource(QUrl())

    def toggle(self):
        if getattr(self, "midi", False):
            self.stop()
            self.play_btn.setText("\u25B6")
            return
        if self.player.playbackState() == QMediaPlayer.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    def _state(self, state):
        self.play_btn.setText("❚❚" if state == QMediaPlayer.PlayingState else "▶")

    def _frame(self, frame):
        if frame.isValid():
            self.frame_img = frame.toImage()
            self.screen.update()

    def _position(self, ms):
        if not self.seek.isSliderDown():
            self.seek.setValue(ms)

        def t(v):
            s = v // 1000
            return f"{s // 60}:{s % 60:02d}"
        self.time.setText(f"{t(ms)} / {t(self.player.duration())}")

    def _paint(self, event):
        p = QPainter(self.screen)
        p.fillRect(self.screen.rect(), Qt.black)
        img = self.frame_img
        if img.isNull() and getattr(self, "title", ""):              # a sound: a note and its name
            p.setPen(QColor("#6AA8F0"))
            p.setFont(QFont("Segoe UI Symbol", 64))
            p.drawText(self.screen.rect().adjusted(0, -40, 0, -40), Qt.AlignCenter, "\u266B")
            p.setPen(QColor("#E0E8F8"))
            p.setFont(QFont("Tahoma", 12, QFont.Bold))
            p.drawText(self.screen.rect().adjusted(20, 90, -20, 0), Qt.AlignCenter, self.title)
        if not img.isNull():
            p.setRenderHint(QPainter.SmoothPixmapTransform)
            s = min(self.screen.width() / img.width(), self.screen.height() / img.height())
            w, h = img.width() * s, img.height() * s
            p.drawImage(QRectF((self.screen.width() - w) / 2, (self.screen.height() - h) / 2, w, h), img)


# ---- the window -----------------------------------------------------------------------------------------------------

class CDViewer(QWidget):
    TITLE = "Fur CD Viewer"
    PLACE = "Art CDs and DVDs"
    RACK = "All Discs"

    def find_root(self):
        return discs_root()

    def __init__(self, desktop):
        super().__init__()
        self.desktop = desktop
        self.frame = None
        self.state = {"slide_ms": 5000}
        self.root = self.find_root()
        self.history = []
        self.here = None                        # None = the rack, else the folder being browsed
        self.disc = None
        self.thumbs = {}
        self.waiting = {}
        self.archive_sources = {}               # unpacked archive folder (in data/) -> the archive it came from
        self.loader = Loader(self, threads=3)
        self.loader.loaded.connect(self._thumb_loaded)
        self.grabber = FrameGrabber(self)
        self.grabber.grabbed.connect(lambda path, img: self._thumb_loaded(f"video:{path}", img))

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        self.stack = QStackedWidget()
        lay.addWidget(self.stack)
        page = QWidget()
        col = QVBoxLayout(page)
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(0)
        col.addWidget(self._bar())
        self.wall = Wall(self)
        self.wall.opened.connect(self.open_node)
        col.addWidget(self.wall, 1)
        self.status = QLabel()
        self.status.setStyleSheet("font: 11px Tahoma; padding: 2px 6px; background: #ECE9D8;"
                                  " border-top: 1px solid #A0A0A0;")
        col.addWidget(self.status)
        self.stack.addWidget(page)
        self.viewer = Viewer(self)
        self.viewer.fav_btn.hide()
        self.viewer.info_btn.hide()
        self.stack.addWidget(self.viewer)
        self.video = VideoPane(self)
        self.stack.addWidget(self.video)
        if self.root is None:
            self.status.setText("Put the Furry Media Archive (with its Art CDs and DVDs folder) on drive E: "
                                "(Local Storage).")
        else:
            self.show_rack()

    def _bar(self):
        bar = QWidget()
        bar.setObjectName("bar")
        bar.setAttribute(Qt.WA_StyledBackground)
        bar.setStyleSheet("QWidget#bar { background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #FDFDFB,"
                          " stop:1 #E3E0D2); border-bottom: 1px solid #A0A0A0; }"
                          "QToolButton { font: 11px Tahoma; padding: 3px 8px; border: 1px solid transparent;"
                          " border-radius: 3px; } QToolButton:hover { border-color: #C0BCA8; background: white; }"
                          "QToolButton:disabled { color: #A0A0A0; }"
                          "QLineEdit { font: 11px Tahoma; border: 1px solid #7F9DB9; padding: 1px 4px; }"
                          "QLabel { font: 11px Tahoma; }")
        row = QHBoxLayout(bar)
        row.setContentsMargins(4, 3, 6, 3)
        row.setSpacing(3)
        self.back_btn = QToolButton()
        self.back_btn.setText("◄ Back")
        self.back_btn.clicked.connect(self.go_back)
        row.addWidget(self.back_btn)
        rack = QToolButton()
        rack.setText(self.RACK)
        rack.clicked.connect(self.show_rack)
        row.addWidget(rack)
        row.addSpacing(10)
        self.where = QLabel()
        self.where.setStyleSheet("color: #404040;")
        row.addWidget(self.where, 1)
        row.addWidget(QLabel("Find:"))
        self.find = QLineEdit()
        self.find.setPlaceholderText("Name")
        self.find.setFixedWidth(150)
        self.find.textChanged.connect(self._filter)
        row.addWidget(self.find)
        return bar

    def _set_wall_look(self, rack):
        if rack:
            self.wall.setStyleSheet("QListWidget { background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #3A4250,"
                                    " stop:1 #1E232C); border: none; font: 11px Tahoma; color: #E8ECF4; }"
                                    "QListWidget::item:selected { background: rgba(120,160,255,90); }")
        else:
            self.wall.setStyleSheet("QListWidget { background: white; border: none; font: 11px Tahoma;"
                                    " color: #202020; } QListWidget::item:selected { background: #316AC5;"
                                    " color: white; }")

    # ---- browsing ---------------------------------------------------------------------------------------------
    def _reset(self):
        self.loader.clear()
        self.grabber.clear()
        self.waiting.clear()
        self.thumbs = {k: v for k, v in self.thumbs.items() if v is not None}
        self.find.blockSignals(True)
        self.find.clear()
        self.find.blockSignals(False)

    def show_rack(self):
        if self.root is None:
            return
        self._reset()
        self.history.clear()
        self.here = self.disc = None
        dirs, _p, _v = listing(self.root)
        nodes = [Node(self.root / d, "disc", disc_name(d)) for d in dirs]
        self._set_wall_look(True)
        self.wall.fill(nodes)
        self.back_btn.setEnabled(False)
        self.where.setText(self.PLACE)
        self.status.setText(f"{len(nodes)} discs")
        self.stack.setCurrentIndex(0)
        if self.frame is not None:
            self.frame.set_title(self.TITLE)

    def show_folder(self, path, remember=True):
        if remember:
            self.history.append(self.here)
        self._reset()
        folder, nodes, counts = self.folder_contents(path)
        self.here = folder
        self._set_wall_look(False)
        self.wall.fill(nodes)
        self.back_btn.setEnabled(True)
        crumbs = self.crumbs(folder)
        self.where.setText("  ›  ".join([self.PLACE] + crumbs))
        bits = [f"{n} {word}{'s' if n != 1 else ''}" for word, n in counts if n]
        self.status.setText(", ".join(bits) or "Nothing to look at in this folder.")
        self.stack.setCurrentIndex(0)
        if self.frame is not None:
            self.frame.set_title(f"{crumbs[-1] if crumbs else self.PLACE} - {self.TITLE}")

    def folder_contents(self, path):
        """(the folder really shown, its nodes, [(noun, count)]) for a folder."""
        folder, (dirs, pics, vids) = look_through(path)
        artist = self.disc.name if self.disc else ""
        nodes = [Node(folder / d, "folder", nice_name(d)) for d in dirs]
        nodes += [Node(folder / n, "piece", piece_title(n), artist) for n in pics]
        nodes += [Node(folder / n, "video", piece_title(n), artist) for n in vids]
        from .videos import flash_files
        flash = flash_files(folder)
        nodes += [Node(folder / n, "flash", piece_title(n), artist) for n in flash]
        sounds, archives = extras(folder)
        nodes += [Node(folder / n, "sound", piece_title(n), artist) for n in sounds]
        nodes += [Node(folder / n, "archive", n, "") for n in archives]
        return folder, nodes, [("folder", len(dirs)), ("picture", len(pics)), ("video", len(vids)),
                               ("Flash animation", len(flash)), ("sound", len(sounds)), ("archive", len(archives))]

    def crumbs(self, folder):
        try:
            rel = folder.relative_to(self.disc.path)
            return [self.disc.name] + [nice_name(x) for x in rel.parts]
        except (ValueError, AttributeError):
            return self._archive_crumbs(folder)

    def go_back(self):
        if not self.history:
            self.show_rack()
            return
        prev = self.history.pop()
        if prev is None:
            self.show_rack()
        else:
            self.show_folder(prev, remember=False)

    def open_node(self, node):
        if node.kind == "disc":
            self.history.clear()
            self.disc = node
            self.here = None
            self.show_folder(node.path, remember=True)
        elif node.kind == "folder":
            self.show_folder(node.path)
        elif node.kind == "piece":
            pieces = [self.wall.item(i).data(Qt.UserRole) for i in range(self.wall.count())
                      if self.wall.item(i).data(Qt.UserRole).kind == "piece"]
            self.stack.setCurrentWidget(self.viewer)
            self.viewer.open(pieces, pieces.index(node))
            self.viewer.easel.setFocus()
        elif node.kind == "video":
            self.stack.setCurrentWidget(self.video)
            self.video.play(node.path)
            if self.frame is not None:
                self.frame.set_title(f"{node.name} - {self.TITLE}")
        elif node.kind == "sound":
            self.stack.setCurrentWidget(self.video)
            self.video.play(node.path, title=node.name)
            if self.frame is not None:
                self.frame.set_title(f"{node.name} - {self.TITLE}")
        elif node.kind == "flash":
            from ..flash import open_flash
            open_flash(self.desktop, node.path)
        elif node.kind == "archive":
            self.status.setText(f"Opening {node.path.name}...")
            QApplication.processEvents()
            folder = open_archive(node.path)
            if folder is None:
                from ...explorer.dialogs import msgbox
                msgbox(self.desktop, self.TITLE, f"{node.path.name} couldn't be opened.", "error")
                return
            self.archive_sources[folder] = node.path
            self.show_folder(folder)

    def _archive_crumbs(self, folder):
        """Inside an unpacked archive: show where it came from (Disc > ... > name.zip > inner folders)."""
        for cache, source in self.archive_sources.items():
            if folder == cache or cache in folder.parents:
                try:
                    outer = [self.disc.name] + [nice_name(x) for x in source.parent.relative_to(self.disc.path).parts]
                except (ValueError, AttributeError):
                    outer = []
                return outer + [source.name] + [nice_name(x) for x in folder.relative_to(cache).parts]
        return [nice_name(folder.name)]

    def close_video(self):
        self.video.stop()
        self.stack.setCurrentIndex(0)

    def _filter(self, text):
        t = text.lower().strip()
        for i in range(self.wall.count()):
            item = self.wall.item(i)
            item.setHidden(bool(t) and t not in item.text().lower())
        self.wall._timer.start()

    # ---- what FurFolio's viewer and wall expect from their owner ---------------------------------------------------
    def close_viewer(self):
        self.viewer.stop()
        self.stack.setCurrentIndex(0)
        cur = self.viewer.current()
        if cur is not None:
            for item in self.wall.items_for(cur.key):
                self.wall.setCurrentItem(item)
                self.wall.scrollToItem(item)

    def set_caption(self, node):
        if self.frame is not None:
            self.frame.set_title(f"{node.name} - {self.TITLE}")
        self.viewer.easel.update()

    def is_favorite(self, node):
        return False

    def info_for(self, node):
        return None

    def show_info(self):
        pass

    def toggle_full_screen(self):
        if self.frame is not None:
            self.frame.toggle_maximize()

    def want_thumb(self, node, callback=None):
        key = node.key
        if callback is not None:
            if self.thumbs.get(key) is not None:
                callback(self.thumbs[key])
                return
            self.waiting.setdefault(key, []).append(callback)
        if key in self.thumbs or node.kind in ("sound", "archive", "flash"):
            return
        self.thumbs[key] = None
        if node.kind == "video":
            self.grabber.request(node.path)
            return
        path = node.path
        if node.kind == "piece":
            job = lambda: make_thumb(path)
        else:
            job = lambda: disc_cover(path)
        self.loader.request(key, job)

    def _thumb_loaded(self, key, img):
        self.thumbs[key] = img
        for item in self.wall.items_for(key):
            self.paint_tile(item)
        for cb in self.waiting.pop(key, []):
            cb(img)

    def paint_tile(self, item):
        from .gallery import _tile
        node = item.data(Qt.UserRole)
        img = self.thumbs.get(node.key) if node.key in self.thumbs else None
        if node.kind == "disc":
            pm = _case_tile(node, img)
        elif node.kind == "folder":
            pm = _folder_tile(node, img)
        elif node.kind == "video":
            pm = _video_tile(node, img)
        elif node.kind == "sound":
            pm = _sound_tile(node)
        elif node.kind == "archive":
            pm = _archive_tile(node)
        elif node.kind == "flash":
            from .videos import _flash_tile
            pm = _flash_tile(node)
        else:
            pm = _tile(node, img)
        item.setIcon(QIcon(pm))

    def keyPressEvent(self, event):
        if self.stack.currentWidget() is self.viewer and self.viewer.key(event):
            return
        if self.stack.currentWidget() is self.video:
            if event.key() == Qt.Key_Escape:
                self.close_video()
                return
            if event.key() == Qt.Key_Space:
                self.video.toggle()
                return
        if event.key() == Qt.Key_Backspace:
            self.go_back()
            return
        super().keyPressEvent(event)

    def closeEvent(self, event):
        self.loader.clear()
        self.grabber.clear()
        self.viewer.stop()
        self.video.stop()
        event.accept()


_open = {}


def open_cdviewer(desktop):
    win = _open.get("win")
    if win is None or not isValid(win):
        body = CDViewer(desktop)
        win = XPWindow(desktop, "Fur CD Viewer", body, cd_icon(), (840, 610))
        body.frame = win
        _open["win"] = win
    desktop.open_window(win)
    return win


def shutdown():
    win = _open.get("win")
    if win is not None and isValid(win):
        win.content.video.stop()
