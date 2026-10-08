"""XP system sounds, played by event name: sound.play("startup")."""
from PySide6.QtCore import QObject, QTimer, QUrl
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer, QSoundEffect

from .paths import SOUNDS

EVENTS = {
    "startup": "Windows XP Startup.wav",
    "shutdown": "Windows XP Shutdown.wav",
    "navigate": "Windows XP Start.wav",
    "menu": "Windows XP Menu Command.wav",
    "default": "Windows XP Default.wav",
    "error": "Windows XP Error.wav",
    "exclamation": "Windows XP Exclamation.wav",
    "info": "Windows Information Bar.wav",
    "ding": "ding.wav",
}


class Sounds(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.muted = False
        self._effects = {}

    def _effect(self, event):
        if event not in self._effects:
            effect = QSoundEffect(self)
            effect.setSource(QUrl.fromLocalFile(str(SOUNDS / EVENTS[event])))
            self._effects[event] = effect
        return self._effects[event]

    def preload(self):
        for event in EVENTS:
            self._effect(event)

    def play(self, event, on_finished=None):
        """Play an event sound. on_finished is called once when it ends (or right away if it can't play)."""
        if self.muted or event not in EVENTS or not (SOUNDS / EVENTS[event]).exists():
            if on_finished:
                QTimer.singleShot(0, on_finished)
            return
        effect = self._effect(event)
        if on_finished:
            done = False

            def finish(force=False):
                nonlocal done
                if done or (effect.isPlaying() and not force):
                    return
                done = True
                effect.playingChanged.disconnect(finish)
                on_finished()

            effect.playingChanged.connect(finish)
            # Safety net in case the effect never reports that it stopped.
            QTimer.singleShot(15000, lambda: finish(True))
        effect.play()


def play_file(name, on_finished=None):
    """Play a longer sound (mp3 etc.) from assets/sounds. Returns the QMediaPlayer, or None
    if muted/missing (on_finished is then not called; the caller should fake the timing)."""
    path = SOUNDS / name
    if is_muted() or not path.exists():
        return None
    player = QMediaPlayer(_instance())
    output = QAudioOutput(player)
    player.setAudioOutput(output)
    done = False

    def finish(*_):
        nonlocal done
        if done:
            return
        done = True
        player.deleteLater()
        if on_finished:
            on_finished()

    player.mediaStatusChanged.connect(
        lambda st: finish() if st in (QMediaPlayer.MediaStatus.EndOfMedia,
                                      QMediaPlayer.MediaStatus.InvalidMedia) else None)
    player.errorOccurred.connect(finish)
    player.setSource(QUrl.fromLocalFile(str(path)))
    player.play()
    return player


_sounds = None


def _instance():
    global _sounds
    if _sounds is None:
        _sounds = Sounds()
    return _sounds


def play(event, on_finished=None):
    _instance().play(event, on_finished)


def preload():
    _instance().preload()


def is_muted():
    return _instance().muted


def set_muted(muted):
    _instance().muted = muted
