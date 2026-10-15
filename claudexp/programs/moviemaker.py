"""Windows Movie Maker 1.1, the one that came with Windows XP: import videos, pictures and music into Collections,
drag clips onto the storyboard, add a soundtrack, preview the whole thing in the monitor, and Save Movie - a real
.wmv rendered with FFmpeg into My Videos. Projects are saved as .MSWMM (JSON).
"""
import json
import re
import subprocess
import threading
from pathlib import Path

from PySide6.QtCore import QObject, QSize, Qt, QTimer, QUrl, Signal
from PySide6.QtGui import QColor, QFont, QIcon, QLinearGradient, QPainter, QPen, QPixmap
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import (QAbstractItemView, QComboBox, QHBoxLayout, QLabel, QLineEdit, QListWidget,
                               QListWidgetItem, QMenuBar, QProgressBar, QPushButton, QSlider, QSplitter,
                               QStackedWidget, QToolButton, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget)
from shiboken6 import isValid

from .. import sound
from ..paths import DATA
from ..wm import XPWindow

VIDEO = {".avi", ".mpg", ".mpeg", ".mp4", ".wmv", ".mov", ".asf", ".mkv", ".m4v", ".webm"}
PICTURE = {".jpg", ".jpeg", ".png", ".bmp", ".gif"}
AUDIO = {".mp3", ".wav", ".wma", ".ogg", ".m4a"}
THUMBS = DATA / "moviemaker_thumbs"
PHOTO_SECONDS = 5
QUALITY = {"Low quality (for e-mail, 56 Kbps)": (160, 120, 15, "128k", "32k"),
           "Medium quality (recommended)": (320, 240, 30, "512k", "64k"),
           "High quality (for playback on a computer)": (640, 480, 30, "1500k", "128k")}
CSS = """
QWidget#mm { background: #ECE9D8; }
QLabel, QPushButton, QToolButton, QComboBox, QLineEdit { font-family: Tahoma; font-size: 11px; }
QMenuBar { background: #ECE9D8; font-family: Tahoma; font-size: 11px; }
QMenuBar::item:selected { background: #316AC5; color: white; }
QMenu { background: white; font-family: Tahoma; font-size: 11px; }
QMenu::item:selected { background: #316AC5; color: white; }
QToolButton { border: 1px solid transparent; padding: 2px 6px; }
QToolButton:hover { border: 1px solid #ACA899; background: #FFFFFF; }
QTreeWidget, QListWidget { background: white; border: 1px solid #7F9DB9; font-family: Tahoma; font-size: 11px; }
QListWidget#story { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #6A7A9A, stop:1 #4A5A7A); }
QLabel#pane { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3A6EA5, stop:1 #8EB0DA); color: white;
              font-weight: bold; padding: 2px 6px; }
"""


def ffmpeg_exe():
    from .pystudio.media import ffmpeg_exe as exe
    return exe()


def mm_pixmap(size=32):
    """A film strip with a clapperboard top."""
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    s = size / 32
    from PySide6.QtCore import QRectF
    p.setPen(QPen(QColor("#202020"), max(1.0, s)))
    p.setBrush(QColor("#303030"))
    p.drawRect(QRectF(3 * s, 11 * s, 26 * s, 17 * s))
    g = QLinearGradient(0, 11 * s, 0, 28 * s)
    g.setColorAt(0, QColor("#7FB2FF"))
    g.setColorAt(1, QColor("#2A5ABE"))
    p.setBrush(g)
    p.drawRect(QRectF(7 * s, 14 * s, 18 * s, 11 * s))
    p.setBrush(QColor("#FFFFFF"))
    for i in range(6):
        p.drawRect(QRectF((4 + i * 4.3) * s, 11.8 * s, 2 * s, 1.4 * s))
        p.drawRect(QRectF((4 + i * 4.3) * s, 25.8 * s, 2 * s, 1.4 * s))
    p.save()
    p.translate(3 * s, 10 * s)
    p.rotate(-18)
    p.setBrush(QColor("#F0F0F0"))
    p.drawRect(QRectF(0, -6 * s, 26 * s, 6 * s))
    p.setBrush(QColor("#202020"))
    for i in range(4):
        p.drawRect(QRectF((2 + i * 6.5) * s, -6 * s, 3 * s, 6 * s))
    p.restore()
    p.end()
    return pm


def mm_icon():
    return QIcon(mm_pixmap(32))


def kind_of(path):
    ext = Path(path).suffix.lower()
    return "video" if ext in VIDEO else "picture" if ext in PICTURE else "audio" if ext in AUDIO else None


def probe(path):
    """(duration seconds or None, has audio) from ffmpeg's banner."""
    exe = ffmpeg_exe()
    if not exe.exists():
        return None, False
    try:
        out = subprocess.run([str(exe), "-hide_banner", "-i", str(path)], capture_output=True, text=True,
                             timeout=20, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)).stderr
    except (OSError, subprocess.TimeoutExpired):
        return None, False
    m = re.search(r"Duration: (\d+):(\d+):(\d+(?:\.\d+)?)", out)
    dur = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3)) if m else None
    return dur, "Audio:" in out


def thumbnail(path):
    """A small picture of a clip (a frame from a video, made with ffmpeg and kept)."""
    k = kind_of(path)
    if k == "picture":
        pm = QPixmap(str(path))
        if not pm.isNull():
            return pm.scaled(96, 72, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    if k == "video":
        THUMBS.mkdir(parents=True, exist_ok=True)
        import hashlib
        out = THUMBS / (hashlib.md5(str(path).encode()).hexdigest() + ".jpg")
        if not out.exists() and ffmpeg_exe().exists():
            try:
                subprocess.run([str(ffmpeg_exe()), "-y", "-ss", "1", "-i", str(path), "-frames:v", "1", "-vf",
                                "scale=96:-1", str(out)], capture_output=True, timeout=20,
                               creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            except (OSError, subprocess.TimeoutExpired):
                pass
        pm = QPixmap(str(out)) if out.exists() else QPixmap()
        if not pm.isNull():
            return pm
    pm = QPixmap(96, 72)
    pm.fill(QColor("#203050" if k == "video" else "#305020"))
    p = QPainter(pm)
    p.setPen(QColor("white"))
    p.setFont(QFont("Tahoma", 9))
    p.drawText(pm.rect(), Qt.AlignCenter, {"video": "Video", "audio": "♫ Audio"}.get(k, "?"))
    p.end()
    return pm


class _Render(QObject):
    progress = Signal(int)
    finished = Signal(bool, str)


def render(items, audio, out, quality, signals):
    """Build and run the ffmpeg command for the storyboard (in a thread). items: [{path, kind, seconds}]."""
    w, h, fps, vbr, abr = QUALITY[quality]
    exe = str(ffmpeg_exe())
    args = [exe, "-y", "-hide_banner"]
    filters, total = [], 0.0
    for i, it in enumerate(items):
        if it["kind"] == "picture":
            args += ["-loop", "1", "-t", str(it["seconds"]), "-i", it["path"]]
        else:
            args += ["-i", it["path"]]
    n = len(items)
    extra = n
    concat = ""
    for i, it in enumerate(items):
        filters.append(f"[{i}:v]scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,"
                       f"setsar=1,fps={fps},format=yuv420p[v{i}]")
        dur = it["seconds"]
        total += dur or 0
        if it["kind"] == "video" and it.get("has_audio"):
            filters.append(f"[{i}:a]aresample=44100,aformat=channel_layouts=stereo[a{i}]")
        else:
            args += ["-f", "lavfi", "-t", str(dur or 1), "-i", "anullsrc=channel_layout=stereo:sample_rate=44100"]
            filters.append(f"[{extra}:a]anull[a{i}]")
            extra += 1
        concat += f"[v{i}][a{i}]"
    filters.append(f"{concat}concat=n={n}:v=1:a=1[vout][aclips]")
    if audio:
        args += ["-i", audio]
        filters.append(f"[{extra}:a]aresample=44100,aformat=channel_layouts=stereo[music]")
        filters.append("[aclips][music]amix=inputs=2:duration=first[aout]")
        amap = "[aout]"
    else:
        amap = "[aclips]"
    args += ["-filter_complex", ";".join(filters), "-map", "[vout]", "-map", amap, "-c:v", "wmv2", "-b:v", vbr,
             "-c:a", "wmav2", "-b:a", abr, str(out)]
    try:
        proc = subprocess.Popen(args, stderr=subprocess.PIPE, stdout=subprocess.DEVNULL, text=True,
                                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        tail = []
        for line in proc.stderr:
            tail = (tail + [line])[-12:]
            m = re.search(r"time=(\d+):(\d+):(\d+(?:\.\d+)?)", line)
            if m and total:
                t = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
                signals.progress.emit(min(99, int(t * 100 / total)))
        ok = proc.wait() == 0
        signals.finished.emit(ok, "" if ok else "".join(tail))
    except OSError as e:
        signals.finished.emit(False, str(e))


# ---- the window ------------------------------------------------------------------------------------------------------

class MovieMaker(QWidget):
    def __init__(self, desktop):
        super().__init__()
        self.desktop = desktop
        self.frame = None
        self.project_path = None
        self.collections = {}                 # name -> [clip dicts]
        self.soundtrack = None
        self.setObjectName("mm")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(CSS)
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(2)
        bar = QMenuBar()
        f = bar.addMenu("&File")
        f.addAction("&New Project", self.new_project)
        f.addAction("&Open Project...", self.open_project)
        f.addAction("&Save Project", self.save_project)
        f.addSeparator()
        f.addAction("&Import...", self.import_file)
        f.addAction("Sa&ve Movie...", self.save_movie)
        f.addSeparator()
        f.addAction("E&xit", lambda: self.frame.request_close() if self.frame else None)
        e = bar.addMenu("&Edit")
        e.addAction("&Delete", self.delete_selected)
        e.addAction("Clear Storyboard", self.clear_story)
        clip = bar.addMenu("&Clip")
        clip.addAction("&Add to Storyboard", self.add_selected)
        clip.addAction("Add as &Soundtrack", self.set_soundtrack)
        play = bar.addMenu("&Play")
        play.addAction("Play &Entire Storyboard", self.play_story)
        play.addAction("&Stop", self.stop)
        bar.addMenu("&Help").addAction("&About Windows Movie Maker", lambda: self._msg(
            "Windows Movie Maker\nVersion 1.1.2427.0\n\nCopyright (c) 1981-2001 Microsoft Corporation."))
        v.setMenuBar(bar)
        tb = QHBoxLayout()
        tb.setContentsMargins(4, 2, 4, 2)
        for text, slot in (("New Project", self.new_project), ("Open", self.open_project),
                           ("Save", self.save_project), ("Import", self.import_file),
                           ("Save Movie", self.save_movie), ("Record", lambda: self._msg(
                               "No video capture device was detected.\n\nConnect a camcorder or a Web camera, "
                               "and then try again."))):
            b = QToolButton()
            b.setText(text)
            b.clicked.connect(slot)
            tb.addWidget(b)
        tb.addStretch()
        v.addLayout(tb)
        split = QSplitter(Qt.Horizontal)
        left = QWidget()
        lv = QVBoxLayout(left)
        lv.setContentsMargins(4, 0, 0, 0)
        title = QLabel("Collections")
        title.setObjectName("pane")
        lv.addWidget(title)
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.currentItemChanged.connect(lambda *_: self._show_collection())
        lv.addWidget(self.tree, 1)
        split.addWidget(left)
        mid = QWidget()
        mv = QVBoxLayout(mid)
        mv.setContentsMargins(0, 0, 0, 0)
        self.coll_title = QLabel("My Collections")
        self.coll_title.setObjectName("pane")
        mv.addWidget(self.coll_title)
        self.clips = QListWidget()
        self.clips.setViewMode(QListWidget.IconMode)
        self.clips.setIconSize(QSize(96, 72))
        self.clips.setGridSize(QSize(112, 100))
        self.clips.setResizeMode(QListWidget.Adjust)
        self.clips.setDragEnabled(True)
        self.clips.itemActivated.connect(lambda it: self.preview_clip(it.data(Qt.UserRole)))
        mv.addWidget(self.clips, 1)
        split.addWidget(mid)
        right = QWidget()
        rv = QVBoxLayout(right)
        rv.setContentsMargins(0, 0, 4, 0)
        mon_title = QLabel("Monitor")
        mon_title.setObjectName("pane")
        rv.addWidget(mon_title)
        self.monitor = QStackedWidget()
        self.monitor.setStyleSheet("background: black;")
        self.video = QVideoWidget()
        self.still = QLabel()
        self.still.setAlignment(Qt.AlignCenter)
        self.monitor.addWidget(self.still)
        self.monitor.addWidget(self.video)
        self.monitor.setMinimumSize(240, 180)
        rv.addWidget(self.monitor, 1)
        controls = QHBoxLayout()
        for text, slot in (("▶", self.play_story), ("■", self.stop)):
            b = QPushButton(text)
            b.setFixedSize(30, 22)
            b.clicked.connect(slot)
            controls.addWidget(b)
        self.seek = QSlider(Qt.Horizontal)
        controls.addWidget(self.seek, 1)
        rv.addLayout(controls)
        split.addWidget(right)
        split.setSizes([160, 330, 300])
        v.addWidget(split, 1)
        story_title = QLabel("Storyboard  -  drag clips here, drag to reorder, Delete to remove")
        story_title.setObjectName("pane")
        v.addWidget(story_title)
        self.story = _Storyboard(self)
        self.story.setObjectName("story")
        v.addWidget(self.story)
        self.audio_label = QLabel("  Soundtrack: (none) - select a music clip and choose Clip > Add as Soundtrack")
        v.addWidget(self.audio_label)
        self.status = QLabel("  Ready")
        self.status.setStyleSheet("border-top: 1px solid #ACA899;")
        v.addWidget(self.status)
        self.player = QMediaPlayer(self)
        self.out = QAudioOutput(self)
        self.player.setAudioOutput(self.out)
        self.player.setVideoOutput(self.video)
        self.player.mediaStatusChanged.connect(self._media_status)
        self.player.durationChanged.connect(lambda d: self.seek.setRange(0, d))
        self.player.positionChanged.connect(self.seek.setValue)
        self.music = QMediaPlayer(self)
        self.music_out = QAudioOutput(self)
        self.music.setAudioOutput(self.music_out)
        self.queue = []
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self._next)
        self._refresh_tree()
        self._blank()

    # ---- collections ----
    def _msg(self, text, icon="info"):
        from ..explorer.dialogs import msgbox
        msgbox(self.desktop, "Windows Movie Maker", text, icon, window_icon=mm_icon())

    def import_file(self):
        from .opendialog import open_dialog
        open_dialog(self.desktop, "Select the File to Import", sorted(VIDEO | PICTURE | AUDIO), self._imported,
                    icon=mm_icon())

    def _imported(self, path):
        path = Path(path)
        k = kind_of(path)
        if k is None:
            return
        self.status.setText(f"  Importing {path.name}...")
        dur, has_audio = (PHOTO_SECONDS, False) if k == "picture" else probe(path)
        clip = {"path": str(path), "kind": k, "name": path.stem, "seconds": dur or PHOTO_SECONDS,
                "has_audio": has_audio}
        name = path.stem
        self.collections.setdefault(name, []).append(clip)
        self._refresh_tree(select=name)
        self.status.setText(f"  Imported {path.name}")

    def _refresh_tree(self, select=None):
        self.tree.clear()
        root = QTreeWidgetItem(["My Collections"])
        root.setIcon(0, self.style().standardIcon(self.style().StandardPixmap.SP_DirIcon))
        self.tree.addTopLevelItem(root)
        chosen = root
        for name in self.collections:
            it = QTreeWidgetItem([name])
            it.setIcon(0, self.style().standardIcon(self.style().StandardPixmap.SP_DirIcon))
            root.addChild(it)
            if name == select:
                chosen = it
        root.setExpanded(True)
        self.tree.setCurrentItem(chosen)
        self._show_collection()

    def _show_collection(self):
        it = self.tree.currentItem()
        self.clips.clear()
        if it is None:
            return
        name = it.text(0)
        self.coll_title.setText(name)
        clips = (self.collections.get(name, []) if it.parent() is not None
                 else [c for cs in self.collections.values() for c in cs])
        for c in clips:
            item = QListWidgetItem(QIcon(thumbnail(c["path"])), c["name"])
            item.setData(Qt.UserRole, c)
            self.clips.addItem(item)

    def add_selected(self):
        for it in self.clips.selectedItems() or ([self.clips.currentItem()] if self.clips.currentItem() else []):
            self.story.add_clip(it.data(Qt.UserRole))

    def set_soundtrack(self):
        it = self.clips.currentItem()
        if it is None:
            return
        c = it.data(Qt.UserRole)
        if c["kind"] != "audio":
            self._msg("Choose a music or sound clip to use as the soundtrack.")
            return
        self.soundtrack = c["path"]
        self.audio_label.setText(f"  Soundtrack: ♫ {c['name']}")

    def delete_selected(self):
        self.story.delete_selected()

    def clear_story(self):
        self.story.clear()

    # ---- the monitor ----
    def _blank(self):
        pm = QPixmap(320, 240)
        pm.fill(QColor("black"))
        p = QPainter(pm)
        p.drawPixmap(128, 90, mm_pixmap(64))
        p.end()
        self.still.setPixmap(pm)
        self.monitor.setCurrentWidget(self.still)

    def preview_clip(self, clip):
        self.stop()
        self.queue = [clip]
        self._next()

    def play_story(self):
        clips = self.story.clips()
        if not clips:
            self._msg("Drag clips from a collection onto the storyboard first.")
            return
        self.stop()
        self.queue = list(clips)
        if self.soundtrack:
            self.music.setSource(QUrl.fromLocalFile(self.soundtrack))
            self.music.play()
        self.status.setText("  Playing storyboard...")
        self._next()

    def _next(self):
        if not self.queue:
            self.music.stop()
            self.status.setText("  Ready")
            return
        c = self.queue.pop(0)
        if c["kind"] == "picture":
            self.player.stop()
            pm = QPixmap(c["path"])
            self.still.setPixmap(pm.scaled(self.monitor.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
            self.monitor.setCurrentWidget(self.still)
            self.timer.start(int(c["seconds"] * 1000))
        elif c["kind"] == "audio":
            self.music.setSource(QUrl.fromLocalFile(c["path"]))
            self.music.play()
            self._blank()
        else:
            self.monitor.setCurrentWidget(self.video)
            self.player.setSource(QUrl.fromLocalFile(c["path"]))
            self.player.play()

    def _media_status(self, st):
        if st == QMediaPlayer.MediaStatus.EndOfMedia:
            self._next()

    def stop(self):
        self.queue = []
        self.timer.stop()
        self.player.stop()
        self.music.stop()
        self._blank()

    # ---- projects ----
    def _folder(self):
        from ..explorer import vfs
        vfs.setup_c()
        folder = vfs.my_documents() / "My Videos"
        folder.mkdir(parents=True, exist_ok=True)
        return folder

    def new_project(self):
        self.stop()
        self.collections = {}
        self.soundtrack = None
        self.story.clear()
        self.project_path = None
        self.audio_label.setText("  Soundtrack: (none)")
        self._refresh_tree()
        if self.frame:
            self.frame.set_title("Untitled - Windows Movie Maker")

    def save_project(self):
        path = self.project_path or self._folder() / "My Movie.MSWMM"
        data = {"collections": self.collections, "story": self.story.clips(), "soundtrack": self.soundtrack}
        Path(path).write_text(json.dumps(data, indent=1), encoding="utf-8")
        self.project_path = Path(path)
        self.status.setText(f"  Project saved: {Path(path).name}")
        if self.frame:
            self.frame.set_title(f"{Path(path).stem} - Windows Movie Maker")

    def open_project(self):
        from .opendialog import open_dialog
        open_dialog(self.desktop, "Open Project", [".mswmm"], self._load, icon=mm_icon(), start=self._folder())

    def _load(self, path):
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            self._msg("Windows Movie Maker cannot open this project file.", "error")
            return
        self.new_project()
        self.collections = data.get("collections", {})
        self.soundtrack = data.get("soundtrack")
        for c in data.get("story", []):
            self.story.add_clip(c)
        if self.soundtrack:
            self.audio_label.setText(f"  Soundtrack: ♫ {Path(self.soundtrack).stem}")
        self.project_path = Path(path)
        self._refresh_tree()
        if self.frame:
            self.frame.set_title(f"{Path(path).stem} - Windows Movie Maker")

    # ---- Save Movie ----
    def save_movie(self):
        clips = [c for c in self.story.clips() if c["kind"] != "audio"]
        if not clips:
            self._msg("The storyboard is empty. Add video clips or pictures to the storyboard, and then try "
                      "again.", "warning")
            return
        if not ffmpeg_exe().exists():
            self._msg("Windows Movie Maker needs its encoder (FFmpeg, in Local Storage\\Python Studio\\ffmpeg) to "
                      "save movies.", "error")
            return
        from ..network import DialogBody, _fixed_window
        body = DialogBody()
        v = QVBoxLayout(body)
        v.setContentsMargins(14, 12, 14, 12)
        v.addWidget(QLabel("<b>Playback quality</b>"))
        qual = QComboBox()
        qual.addItems(list(QUALITY))
        qual.setCurrentIndex(1)
        v.addWidget(qual)
        total = sum(c["seconds"] or 0 for c in clips)
        info = QLabel()
        v.addWidget(info)

        def update_info():
            w, h, fps, vbr, _abr = QUALITY[qual.currentText()]
            kb = int(vbr.rstrip("k")) + 64
            info.setText(f"Display size: {w} x {h} pixels\nFrames per second: {fps}\nVideo profile: Windows Media "
                         f"Video 8\nFile size: {kb * total / 8 / 1024:.1f} MB\nDuration: {int(total // 60)}:"
                         f"{int(total % 60):02d}")
        qual.currentIndexChanged.connect(lambda _i: update_info())
        update_info()
        v.addWidget(QLabel("<b>Display information</b>"))
        title = QLineEdit("My Movie")
        author = QLineEdit(self._author())
        for label, w in (("Title:", title), ("Author:", author)):
            r = QHBoxLayout()
            r.addWidget(QLabel(label))
            r.addWidget(w)
            v.addLayout(r)
        row = QHBoxLayout()
        row.addStretch()
        ok, cancel = QPushButton("OK"), QPushButton("Cancel")
        for b in (ok, cancel):
            b.setFixedSize(75, 23)
            row.addWidget(b)
        v.addLayout(row)
        body.setFixedWidth(340)
        holder = {}

        def close():
            if holder.get("win") is not None and isValid(holder["win"]):
                self.desktop.close_window(holder.pop("win"))

        def go():
            name = re.sub(r'[\\/:*?"<>|]', "", title.text().strip()) or "My Movie"
            out = self._folder() / f"{name}.wmv"
            close()
            self._render(clips, out, qual.currentText())
        ok.clicked.connect(go)
        cancel.clicked.connect(close)
        holder["win"] = _fixed_window(self.desktop, "Save Movie", body, close)
        holder["win"].icon = mm_icon()
        self.desktop.open_window(holder["win"])

    def _author(self):
        from .. import user
        return user.user_name()

    def _render(self, clips, out, quality):
        from ..network import DialogBody, _fixed_window
        body = DialogBody()
        v = QVBoxLayout(body)
        v.setContentsMargins(14, 12, 14, 12)
        label = QLabel(f"Creating movie: {out.name}")
        v.addWidget(label)
        bar = QProgressBar()
        v.addWidget(bar)
        body.setFixedWidth(340)
        win = _fixed_window(self.desktop, "Creating Movie", body, lambda: None)
        win.icon = mm_icon()
        self.desktop.open_window(win)
        sig = _Render(self)
        sig.progress.connect(bar.setValue)

        def done(ok, err):
            if isValid(win):
                self.desktop.close_window(win)
            if not ok:
                self._msg(f"Windows Movie Maker could not save the movie.\n\n{err[-600:]}", "error")
                return
            sound.play("default")
            from ..explorer.dialogs import msgbox

            def answer(b):
                if b == "Yes":
                    from ..explorer import viewers
                    viewers.open_file(self.desktop, out)
            msgbox(self.desktop, "Windows Movie Maker", f"Your movie has been saved:\n{out}\n\nDo you want to watch "
                   "your movie now?", "question", ("Yes", "No"), answer, window_icon=mm_icon())
        sig.finished.connect(done)
        threading.Thread(target=render, args=(clips, self.soundtrack, out, quality, sig), daemon=True).start()

    def shutdown(self):
        self.stop()


class _Storyboard(QListWidget):
    """The strip along the bottom: clips in order. Accepts drags from the collection; reorder by dragging."""

    def __init__(self, mm):
        super().__init__()
        self.mm = mm
        self.setViewMode(QListWidget.IconMode)
        self.setFlow(QListWidget.LeftToRight)
        self.setWrapping(False)
        self.setIconSize(QSize(80, 60))
        self.setGridSize(QSize(100, 90))
        self.setFixedHeight(112)
        self.setMovement(QListWidget.Snap)
        self.setDragDropMode(QAbstractItemView.DragDrop)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setAcceptDrops(True)
        self.setStyleSheet("QListWidget { color: white; }")
        self.itemActivated.connect(lambda it: mm.preview_clip(it.data(Qt.UserRole)))

    def add_clip(self, clip):
        item = QListWidgetItem(QIcon(thumbnail(clip["path"])), clip["name"])
        item.setData(Qt.UserRole, clip)
        self.addItem(item)

    def clips(self):
        return [self.item(i).data(Qt.UserRole) for i in range(self.count())]

    def delete_selected(self):
        for it in self.selectedItems():
            self.takeItem(self.row(it))

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Delete:
            self.delete_selected()
        else:
            super().keyPressEvent(e)

    def dropEvent(self, e):
        src = e.source()
        if src is self.mm.clips:
            for it in src.selectedItems():
                self.add_clip(it.data(Qt.UserRole))
            e.acceptProposedAction()
            return
        super().dropEvent(e)


_open = {}


def open_moviemaker(desktop):
    win = _open.get("win")
    if win is not None and isValid(win):
        desktop.open_window(win)
        return win
    body = MovieMaker(desktop)
    win = XPWindow(desktop, "Untitled - Windows Movie Maker", body, mm_icon(), size=(860, 620))
    body.frame = win
    _open["win"] = win
    desktop.open_window(win)
    return win


def shutdown():
    win = _open.get("win")
    if win is not None and isValid(win):
        win.content.shutdown()
