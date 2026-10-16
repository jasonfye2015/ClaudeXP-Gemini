"""Game assets: installs the bundled CC0 packs, browses sprites and sounds, and makes retro sound effects."""
import math
import random
import struct
import wave
import zipfile
from pathlib import Path

from PySide6.QtCore import QProcess, QSize, Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (QApplication, QComboBox, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
                               QPushButton, QSlider, QTabWidget, QVBoxLayout, QWidget)

IMAGE_EXT = {".png", ".gif", ".jpg", ".jpeg", ".bmp"}
SOUND_EXT = {".ogg", ".wav", ".mp3"}


def assets_dir():
    from .app import projects_dir
    return projects_dir() / "Assets"


def bundled():
    from .app import studio_root
    return sorted((studio_root() / "assets").glob("*.zip"))


def install():
    """Unpack the bundled asset packs into <Python Programs>\\Assets\\<pack>. Returns the number of packs installed."""
    count = 0
    for z in bundled():
        name = z.stem.replace("kenney_", "")
        target = assets_dir() / name
        if (target / ".installed").exists():
            continue
        target.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(z) as arc:
            for n in arc.namelist():
                if n.endswith("/") or Path(n).suffix.lower() in (".url", ".ini", ".c3p"):
                    continue
                out = target / n
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_bytes(arc.read(n))
        (target / ".installed").write_text("ok", encoding="utf-8")
        count += 1
    if count:
        notice = assets_dir() / "ABOUT ASSETS.txt"
        notice.write_text("The packs in these folders are by Kenney (kenney.nl), released as Creative Commons CC0:\n"
                          "free to use in any project, no credit needed (but always appreciated).\n"
                          "Use them in your programs with paths like  Assets/pixel-platformer/Tiles/tile_0000.png\n"
                          "Put your own pictures and sounds in My Sounds / any folder here too.\n", encoding="utf-8")
    return count


def packs():
    root = assets_dir()
    return sorted(p for p in root.iterdir() if p.is_dir()) if root.is_dir() else []


def files_in(pack, extensions):
    return sorted((f for f in pack.rglob("*") if f.suffix.lower() in extensions), key=lambda f: str(f).lower())


# ---- synthesised retro sound effects (pure Python, so no extra packages are needed) -------------------------

RATE = 22050
KINDS = ["Coin", "Jump", "Laser", "Explosion", "Hit", "Powerup", "Blip"]


def synth(kind, pitch=1.0, length=1.0, seed=0):
    """A short sound effect as a list of 16-bit samples."""
    rng = random.Random(seed)
    base = {"Coin": (900, 1500, .25, "square"), "Jump": (260, 700, .28, "square"), "Laser": (1400, 220, .3, "saw"),
            "Explosion": (140, 30, .8, "noise"), "Hit": (330, 90, .2, "noise"), "Powerup": (330, 1300, .5, "square"),
            "Blip": (700, 700, .08, "square")}[kind]
    f0, f1, dur, shape = base
    f0, f1, dur = f0 * pitch, f1 * pitch, dur * length
    n = int(RATE * dur)
    out, phase = [], 0.0
    for i in range(n):
        t = i / max(1, n - 1)
        if kind == "Coin":
            freq = f0 if t < .35 else f1
        elif kind == "Powerup":
            freq = f0 + (f1 - f0) * t + 40 * math.sin(t * 60)
        else:
            freq = f0 + (f1 - f0) * t
        phase += freq / RATE
        frac = phase % 1.0
        if shape == "square":
            v = 1.0 if frac < .5 else -1.0
        elif shape == "saw":
            v = 2 * frac - 1
        else:
            v = rng.uniform(-1, 1) * .8 + (1.0 if frac < .5 else -1.0) * .2
        env = (1 - t) ** (2.0 if kind in ("Explosion", "Hit") else 1.2)
        env *= min(1.0, i / 60)
        out.append(int(max(-1, min(1, v * env * .55)) * 32767))
    return out


def write_wav(path, samples):
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(b"".join(struct.pack("<h", s) for s in samples))


# ---- the window ---------------------------------------------------------------------------------------------

class AssetBrowser(QWidget):
    """Sprites, sounds and a sound-effect maker. `insert` puts a line of code into the editor."""

    def __init__(self, python, insert, rel_to):
        super().__init__()
        self.python, self.insert, self.rel_to = python, insert, rel_to
        self.player = None
        root = QVBoxLayout(self)
        root.setContentsMargins(4, 4, 4, 4)
        self.tabs = QTabWidget()
        root.addWidget(self.tabs, 1)
        self.note = QLabel("")
        self.note.setWordWrap(True)
        root.addWidget(self.note)
        self._images_tab()
        self._sounds_tab()
        self._maker_tab()

    def rel(self, path):
        try:
            return Path(path).relative_to(self.rel_to()).as_posix()
        except ValueError:
            return str(path).replace("\\", "/")

    # images
    def _images_tab(self):
        page = QWidget()
        box = QVBoxLayout(page)
        row = QHBoxLayout()
        self.pack_box = QComboBox()
        self.pack_box.addItem("All packs", None)
        for p in packs():
            self.pack_box.addItem(p.name, str(p))
        self.pack_box.currentIndexChanged.connect(self._fill_images)
        self.filter = QLineEdit()
        self.filter.setPlaceholderText("Filter by name")
        self.filter.textChanged.connect(self._fill_images)
        row.addWidget(self.pack_box)
        row.addWidget(self.filter, 1)
        box.addLayout(row)
        self.images = QListWidget()
        self.images.setViewMode(QListWidget.IconMode)
        self.images.setIconSize(QSize(48, 48))
        self.images.setResizeMode(QListWidget.Adjust)
        self.images.setUniformItemSizes(True)
        self.images.setGridSize(QSize(64, 64))
        self.images.itemSelectionChanged.connect(self._image_picked)
        box.addWidget(self.images, 1)
        self.preview = QLabel("")
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setMinimumHeight(110)
        box.addWidget(self.preview)
        buttons = QHBoxLayout()
        insert = QPushButton("Insert load line")
        insert.setToolTip("Put code that loads this picture into your program")
        insert.clicked.connect(lambda: self._insert_image())
        copy = QPushButton("Copy path")
        copy.clicked.connect(lambda: self._copy(self._image_path()))
        buttons.addWidget(insert)
        buttons.addWidget(copy)
        buttons.addStretch()
        box.addLayout(buttons)
        self.tabs.addTab(page, "Sprites")
        self._fill_images()

    def _fill_images(self, *_):
        self.images.clear()
        data = self.pack_box.currentData()
        folders = [Path(data)] if data else packs()
        text = self.filter.text().lower()
        shown = 0
        for folder in folders:
            for f in files_in(folder, IMAGE_EXT):
                if text and text not in f.name.lower():
                    continue
                if shown >= 600:
                    break
                item = QListWidgetItem(QIcon(QPixmap(str(f)).scaled(48, 48, Qt.KeepAspectRatio, Qt.FastTransformation)),
                                       "")
                item.setToolTip(self.rel(f))
                item.setData(Qt.UserRole, str(f))
                self.images.addItem(item)
                shown += 1
        self.note.setText(f"{shown} pictures" + (" (first 600 shown: use the filter)" if shown >= 600 else ""))

    def _image_path(self):
        item = self.images.currentItem()
        return self.rel(item.data(Qt.UserRole)) if item else ""

    def _image_picked(self):
        item = self.images.currentItem()
        if item is None:
            return
        pm = QPixmap(item.data(Qt.UserRole))
        scale = max(1, min(8, 100 // max(1, max(pm.width(), pm.height()))))
        self.preview.setPixmap(pm.scaled(pm.width() * scale, pm.height() * scale, Qt.KeepAspectRatio,
                                         Qt.FastTransformation))
        self.note.setText(f"{self._image_path()}   ({pm.width()} x {pm.height()})")

    def _insert_image(self):
        path = self._image_path()
        if path:
            name = Path(path).stem.replace("-", "_").replace(" ", "_")
            self.insert(f'{name} = pygame.image.load("{path}").convert_alpha()\n')

    def _copy(self, text):
        if text:
            QApplication.clipboard().setText(text)
            self.note.setText("Copied: " + text)

    # sounds
    def _sounds_tab(self):
        page = QWidget()
        box = QVBoxLayout(page)
        row = QHBoxLayout()
        self.sound_filter = QLineEdit()
        self.sound_filter.setPlaceholderText("Filter by name, e.g. coin, footstep, click")
        self.sound_filter.textChanged.connect(self._fill_sounds)
        row.addWidget(self.sound_filter, 1)
        box.addLayout(row)
        self.sounds = QListWidget()
        self.sounds.itemDoubleClicked.connect(lambda _i: self.play())
        box.addWidget(self.sounds, 1)
        buttons = QHBoxLayout()
        play = QPushButton("\u25B6 Play")
        play.clicked.connect(self.play)
        stop = QPushButton("Stop")
        stop.clicked.connect(self.stop_playing)
        insert = QPushButton("Insert load line")
        insert.clicked.connect(self._insert_sound)
        copy = QPushButton("Copy path")
        copy.clicked.connect(lambda: self._copy(self._sound_path()))
        for b in (play, stop, insert, copy):
            buttons.addWidget(b)
        box.addLayout(buttons)
        self.tabs.addTab(page, "Sounds")
        self._fill_sounds()

    def _fill_sounds(self, *_):
        self.sounds.clear()
        text = self.sound_filter.text().lower()
        for folder in packs():
            for f in files_in(folder, SOUND_EXT):
                if text and text not in f.name.lower():
                    continue
                item = QListWidgetItem(f"{folder.name} / {f.name}")
                item.setData(Qt.UserRole, str(f))
                self.sounds.addItem(item)

    def _sound_path(self):
        item = self.sounds.currentItem()
        return self.rel(item.data(Qt.UserRole)) if item else ""

    def _insert_sound(self):
        path = self._sound_path()
        if path:
            name = Path(path).stem.replace("-", "_").replace(" ", "_")
            self.insert(f'{name} = pygame.mixer.Sound("{path}")\n')

    def play(self, path=None):
        """Play a file through the studio's own Python and pygame (it handles .ogg as well as .wav)."""
        item = self.sounds.currentItem()
        path = path or (item.data(Qt.UserRole) if item else None)
        if not path or not Path(self.python).exists():
            return
        self.stop_playing()
        code = ("import os,sys\nos.environ['PYGAME_HIDE_SUPPORT_PROMPT']='1'\nimport pygame,time\npygame.mixer.init()\n"
                "s=pygame.mixer.Sound(sys.argv[1]);s.play()\ntime.sleep(s.get_length()+.2)\n")
        self.player = QProcess(self)
        self.player.start(str(self.python), ["-c", code, str(path)])

    def stop_playing(self):
        if self.player is not None:
            self.player.kill()
            self.player.waitForFinished(500)
            self.player = None

    # sound effect maker
    def _maker_tab(self):
        page = QWidget()
        box = QVBoxLayout(page)
        box.addWidget(QLabel("Make a retro sound effect, hear it, and save it for your game."))
        self.kind = QComboBox()
        self.kind.addItems(KINDS)
        self.pitch = QSlider(Qt.Horizontal)
        self.pitch.setRange(50, 200)
        self.pitch.setValue(100)
        self.length = QSlider(Qt.Horizontal)
        self.length.setRange(40, 250)
        self.length.setValue(100)
        self.seed = 1
        for label, w in (("Sound", self.kind), ("Pitch", self.pitch), ("Length", self.length)):
            row = QHBoxLayout()
            row.addWidget(QLabel(label))
            row.addWidget(w, 1)
            box.addLayout(row)
        self.sfx_name = QLineEdit("my_sound")
        row = QHBoxLayout()
        row.addWidget(QLabel("File name"))
        row.addWidget(self.sfx_name, 1)
        box.addLayout(row)
        buttons = QHBoxLayout()
        hear = QPushButton("\u25B6 Hear it")
        hear.clicked.connect(self.hear)
        shuffle = QPushButton("Randomize")
        shuffle.clicked.connect(self._shuffle)
        save = QPushButton("Save to Assets\\My Sounds")
        save.clicked.connect(self.save_sfx)
        for b in (hear, shuffle, save):
            buttons.addWidget(b)
        box.addLayout(buttons)
        box.addStretch()
        self.tabs.addTab(page, "Make Sound")

    def _samples(self):
        return synth(self.kind.currentText(), self.pitch.value() / 100, self.length.value() / 100, self.seed)

    def _shuffle(self):
        self.seed = random.randint(1, 10 ** 6)
        self.pitch.setValue(random.randint(70, 150))
        self.length.setValue(random.randint(70, 140))
        self.hear()

    def hear(self):
        import tempfile
        import winsound
        tmp = Path(tempfile.gettempdir()) / "pystudio_sfx.wav"
        write_wav(tmp, self._samples())
        winsound.PlaySound(str(tmp), winsound.SND_FILENAME | winsound.SND_ASYNC)

    def save_sfx(self):
        name = "".join(c for c in self.sfx_name.text().strip() if c.isalnum() or c in "_- ") or "my_sound"
        folder = assets_dir() / "My Sounds"
        folder.mkdir(parents=True, exist_ok=True)
        target = folder / f"{name}.wav"
        write_wav(target, self._samples())
        self.note.setText(f"Saved {self.rel(target)}")
        self._fill_sounds()
        if not any(self.pack_box.itemText(i) == "My Sounds" for i in range(self.pack_box.count())):
            self.pack_box.addItem("My Sounds", str(folder))

    def shutdown(self):
        self.stop_playing()
