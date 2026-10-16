"""Away Message window (away.jpg)."""
from PySide6.QtWidgets import QPushButton, QTextEdit

from .common import ImageWindow


class AwayWindow(ImageWindow):
    def __init__(self, settings, world, parent=None):
        super().__init__("away.jpg", "Away Message", parent=parent, dialog=True)
        self.world = world

        self.message = QTextEdit(self)
        self.message.setGeometry(7, 36, 272, 59)
        self.message.setFrameShape(QTextEdit.NoFrame)
        self.message.setAcceptRichText(False)
        self.message.setStyleSheet("QTextEdit { background: white; font: 10pt 'Arial'; }")
        self.message.setPlainText(settings["away_message"])

        self.away_btn = QPushButton("I'm Away", self)
        self.away_btn.setGeometry(55, 99, 80, 23)
        self.away_btn.clicked.connect(self._go_away)

        self.cancel_btn = QPushButton("Cancel", self)
        self.cancel_btn.setGeometry(150, 99, 80, 23)
        self.cancel_btn.clicked.connect(self.close)

        world.user_away_changed.connect(self._update_title)
        self._update_title()

    def _update_title(self, *_):
        self.setWindowTitle("*Away* - Away Message" if self.world.user_away else "Away Message")
        self.away_btn.setText("Update" if self.world.user_away else "I'm Away")

    def _go_away(self):
        self.world.set_user_away(True, self.message.toPlainText().strip())

    def closeEvent(self, event):
        # Cancel (or closing this window) ends away status, like AIM's "I'm Back".
        self.world.set_user_away(False)
        event.accept()
