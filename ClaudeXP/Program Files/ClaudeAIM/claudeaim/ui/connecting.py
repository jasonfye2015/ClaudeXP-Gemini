"""The small 'Connecting...' window (connecting.png)."""
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import QLabel, QPushButton

from .common import ImageWindow


class ConnectingWindow(ImageWindow):
    connected = Signal()
    cancelled = Signal()

    def __init__(self, settings, sounds):
        super().__init__("connecting.png", "Sign On")
        self.sounds = sounds
        self.finished = False

        w = self.width()
        self.name = QLabel(settings["screen_name"], self)
        self.name.setAlignment(Qt.AlignCenter)
        self.name.setStyleSheet("font-weight: bold;")
        self.name.setGeometry(0, 165, w, 16)

        self.status = QLabel("Connecting...", self)
        self.status.setAlignment(Qt.AlignCenter)
        self.status.setGeometry(0, 184, w, 16)

        self.cancel = QPushButton("Cancel", self)
        self.cancel.setGeometry((w - 75) // 2, 208, 75, 23)
        self.cancel.clicked.connect(self.close)

        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.center_on_screen()

    def start(self):
        self.show()
        self.timer.timeout.connect(self._welcome)
        self.timer.start(3000)

    def _welcome(self):
        self.status.setText("Connected!")
        self.sounds.play("welcome.wav")
        self.timer.timeout.disconnect()
        self.timer.timeout.connect(self._done)
        self.timer.start(3000)

    def _done(self):
        self.finished = True
        self.close()
        self.connected.emit()

    def closeEvent(self, event):
        event.accept()
        self.timer.stop()
        if not self.finished:
            self.cancelled.emit()
