"""Fire-and-forget sound playback."""
from PySide6.QtCore import QObject, QTimer, QUrl
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer

from . import host, paths


class Sounds(QObject):
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self._active = set()

    def play(self, name, on_finished=None, force=False):
        """Play a sound file. Returns the player, or None if sounds are off.

        on_finished is called exactly once, when playback ends or fails.
        """
        if not (self.settings["sounds"] or force) or host.muted():
            if on_finished:
                QTimer.singleShot(0, on_finished)
            return None

        player = QMediaPlayer(self)
        output = QAudioOutput(player)
        player.setAudioOutput(output)
        self._active.add(player)
        done = False

        def finish(*_):
            nonlocal done
            if done:
                return
            done = True
            self._active.discard(player)
            player.deleteLater()
            if on_finished:
                on_finished()

        def status(st):
            if st in (QMediaPlayer.MediaStatus.EndOfMedia, QMediaPlayer.MediaStatus.InvalidMedia):
                finish()

        player.mediaStatusChanged.connect(status)
        player.errorOccurred.connect(finish)
        player.setSource(QUrl.fromLocalFile(paths.sound(name)))
        player.play()
        return player
