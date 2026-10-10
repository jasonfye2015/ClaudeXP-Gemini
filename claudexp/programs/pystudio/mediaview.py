"""Audio and Video Converter window for Python Studio."""
import os
import threading
from pathlib import Path

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import (QComboBox, QDoubleSpinBox, QFileDialog, QFormLayout, QHBoxLayout, QLabel, QLineEdit,
                               QPushButton, QSpinBox, QVBoxLayout, QWidget)

from . import media


class _Bridge(QObject):
    done = Signal(bool, str)


class MediaConverter(QWidget):
    """insert(text) puts code in the editor; ask(text) sends a question to the AI Helper."""

    def __init__(self, insert, ask=None, out_root=None):
        super().__init__()
        self.insert, self.ask = insert, ask
        self.out_root = out_root
        self.last = None
        self.bridge = _Bridge()
        self.bridge.done.connect(self._finished)

        self.source = QLineEdit()
        self.source.setPlaceholderText("Choose a sound or video file...")
        browse = QPushButton("Browse...")
        browse.clicked.connect(self.browse)
        row = QHBoxLayout()
        row.addWidget(self.source, 1)
        row.addWidget(browse)

        self.preset = QComboBox()
        for key, label, *_ in media.PRESETS:
            self.preset.addItem(label, key)
        self.preset.currentIndexChanged.connect(self._preset_changed)
        self.about = QLabel()
        self.about.setWordWrap(True)

        self.start = QDoubleSpinBox(); self.start.setRange(0, 36000); self.start.setSuffix(" sec")
        self.length = QDoubleSpinBox(); self.length.setRange(0, 36000); self.length.setSuffix(" sec")
        self.length.setSpecialValueText("to the end")
        self.fade = QDoubleSpinBox(); self.fade.setRange(0.05, 30); self.fade.setValue(1.0); self.fade.setSuffix(" sec")
        self.repeat = QSpinBox(); self.repeat.setRange(2, 99); self.repeat.setValue(2)
        self.fps = QSpinBox(); self.fps.setRange(1, 60); self.fps.setValue(10)
        self.options = {"start": ("Start at", self.start), "length": ("Length", self.length),
                        "fade": ("Fade", self.fade), "repeat": ("Repeat", self.repeat),
                        "fps": ("Frames per second", self.fps)}
        form = QFormLayout()
        form.addRow("File:", row)
        form.addRow("What to do:", self.preset)
        form.addRow("", self.about)
        self.labels = {}
        for key, (text, widget) in self.options.items():
            label = QLabel(text + ":")
            self.labels[key] = label
            form.addRow(label, widget)

        self.go = QPushButton("Convert")
        self.go.clicked.connect(self.convert)
        self.use = QPushButton("Insert code to use it")
        self.use.clicked.connect(self.insert_code)
        self.use.setEnabled(False)
        self.show_btn = QPushButton("Show in folder")
        self.show_btn.clicked.connect(self.show_folder)
        self.show_btn.setEnabled(False)
        buttons = QHBoxLayout()
        for b in (self.go, self.use, self.show_btn):
            buttons.addWidget(b)
        self.result = QLabel("")
        self.result.setWordWrap(True)
        self.missing = QLabel("")
        self.missing.setWordWrap(True)

        lay = QVBoxLayout(self)
        lay.addLayout(form)
        lay.addLayout(buttons)
        lay.addWidget(self.result)
        lay.addWidget(self.missing)
        lay.addStretch(1)
        if not media.available():
            self.missing.setText("ffmpeg.exe is missing. Put it in Local Storage\\Python Studio\\ffmpeg.")
            self.go.setEnabled(False)
        self._preset_changed()

    def key(self):
        return self.preset.currentData()

    def _preset_changed(self):
        entry = media.preset(self.key())
        self.about.setText(entry[2])
        for name, label in self.labels.items():
            shown = name in entry[3]
            label.setVisible(shown)
            self.options[name][1].setVisible(shown)

    def browse(self):
        exts = " ".join("*" + e for e in sorted(media.MEDIA_EXT))
        path, _ = QFileDialog.getOpenFileName(self, "Choose a sound or video", "", f"Sound and video ({exts});;All files (*)")
        if path:
            self.source.setText(path)

    def out_dir(self):
        from .assets import assets_dir
        root = Path(self.out_root) if self.out_root else assets_dir()
        return root / ("My Sprites" if media.preset(self.key())[4] == "folder" or self.key() == "gif" else "My Sounds")

    def convert(self):
        source = self.source.text().strip().strip('"')
        if not source:
            self._say("Choose a file first.", False)
            return
        key = self.key()
        entry = media.preset(key)
        options = {name: self.options[name][1].value() for name in entry[3]}
        if "repeat" in options:
            options["repeat"] = int(options["repeat"])
        if "fps" in options:
            options["fps"] = int(options["fps"])
        out_dir = self.out_dir()
        self.go.setEnabled(False)
        self._say("Working...")

        def work():
            try:
                ok, info = media.convert(key, source, out_dir, **options)
            except Exception as exc:
                ok, info = False, f"Could not convert: {exc}"
            self.bridge.done.emit(ok, info)
        threading.Thread(target=work, daemon=True).start()

    def _finished(self, ok, info):
        self.go.setEnabled(media.available())
        if ok:
            self.last = info
            self.use.setEnabled(True)
            self.show_btn.setEnabled(True)
            self._say(f"Done: {info}", True)
        else:
            self._say(info, False)

    def _say(self, text, good=None):
        color = {True: "#1b7a1b", False: "#b03030"}.get(good, "#000000")
        self.result.setStyleSheet(f"color: {color}; font-weight: bold;")
        self.result.setText(text)

    def code_for(self, path):
        p = Path(path)
        name = p.stem.replace("-", "_").replace(" ", "_")
        if p.is_dir():
            return (f'frames = [pygame.image.load(str(f)).convert_alpha()\n          for f in sorted(__import__("pathlib")'
                    f'.Path(r"{p}").glob("frame_*.png"))]\n')
        if p.suffix.lower() == ".gif":
            return f'{name} = pygame.image.load(r"{p}")  # first frame; use the frames preset for animation\n'
        return f'{name} = pygame.mixer.Sound(r"{p}")\n'

    def insert_code(self):
        if self.last:
            self.insert(self.code_for(self.last))

    def show_folder(self):
        if self.last and Path(self.last).exists():
            target = Path(self.last)
            os.startfile(str(target if target.is_dir() else target.parent))
