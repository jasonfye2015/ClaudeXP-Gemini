"""The dial-up splash: dialing.jpg + modem noises."""
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import QCheckBox, QLabel, QPushButton

from .common import ImageWindow

CONNECTING_AT = 0.45   # fraction of the modem sound before "Connecting..."
NO_SOUND_MS = 8000     # how long to pretend when sounds are off or the file is missing


class DialupWindow(ImageWindow):
    finished = Signal()
    cancelled = Signal()

    def __init__(self, settings, sounds):
        super().__init__("dialing.jpg", "Sign On", bg="#ffffff")
        self.settings, self.sounds = settings, sounds
        self.player = None
        self.done = False

        w = self.width()
        self.status = QLabel("Dialing...", self)
        self.status.setAlignment(Qt.AlignCenter)
        self.status.setStyleSheet("background: white; font-size: 11pt;")
        self.status.setGeometry(0, 385, w, 22)

        self.cancel = QPushButton("Cancel", self)
        self.cancel.setGeometry((w - 80) // 2, 414, 80, 24)
        self.cancel.clicked.connect(self._cancel)

        self.skip = QCheckBox("Skip this during log on.", self)
        self.skip.setStyleSheet("background: white;")
        self.skip.adjustSize()
        self.skip.move((w - self.skip.width()) // 2, 448)
        self.skip.setChecked(bool(settings["skip_dialup"]))
        self.skip.toggled.connect(lambda on: settings.set("skip_dialup", on))

        self.center_on_screen()

    def start(self):
        self.show()
        self.player = self.sounds.play("dialup connection.mp3", on_finished=self._audio_done)
        if self.player is None:
            QTimer.singleShot(int(NO_SOUND_MS * CONNECTING_AT), self._connecting)
            QTimer.singleShot(NO_SOUND_MS, self._audio_done)
        else:
            self.player.positionChanged.connect(self._progress)

    def _progress(self, pos):
        dur = self.player.duration() if self.player else 0
        if dur > 0 and pos >= dur * CONNECTING_AT:
            self._connecting()

    def _connecting(self):
        if not self.done and self.status.text() == "Dialing...":
            self.status.setText("Connecting...")

    def _audio_done(self):
        if self.done:
            return
        self.done = True
        self.player = None
        self.status.setText("Connected...")
        QTimer.singleShot(3000, self._finish)

    def _finish(self):
        if self.isVisible():
            self.hide()
            self.finished.emit()

    def _cancel(self):
        self.done = True
        if self.player:
            self.player.stop()
        self.hide()
        self.cancelled.emit()

    def closeEvent(self, event):
        if self.isVisible():
            self._cancel()
        event.accept()
