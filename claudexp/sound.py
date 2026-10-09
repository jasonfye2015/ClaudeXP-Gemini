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
    # XP's own sound scheme (C:\WINDOWS\Media, short names)
    "minimize": "xp/xpmin.wav",
    "restore": "xp/xprestor.wav",
    "logon": "xp/xplogon.wav",
    "logoff": "xp/xplogoff.wav",
    "recycle": "xp/xprecycl.wav",
    "balloon": "xp/xpballn.wav",
    "print_done": "xp/xpprint.wav",
    "critical": "xp/xpcrtstp.wav",
    "notify": "xp/xpnotify.wav",
    "hw_insert": "xp/xphdinst.wav",
    "hw_remove": "xp/xphdrem.wav",
    "hw_fail": "xp/xphdfail.wav",
    "battery_low": "xp/xpbatlow.wav",
    "battery_critical": "xp/xpbatcrt.wav",
    "ring_in": "xp/xpringin.wav",
    "ring_out": "xp/xprngout.wav",
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


def play_clip(name, ms):
    """Play the first `ms` milliseconds of a sound file (e.g. a few seconds of a floppy grinding)."""
    player = play_file(name)
    if player is not None:
        QTimer.singleShot(ms, lambda: player.stop() if _alive(player) else None)
    return player


def _alive(obj):
    from shiboken6 import isValid
    return isValid(obj)


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
