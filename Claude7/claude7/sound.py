"""Windows 7's sounds, played by event name: sound.play("startup"). The same interface as ClaudeXP's sound module,
so the period programs' own calls (sound.play("menu"), sound.is_muted()) play Windows 7's scheme here."""
from PySide6.QtCore import QObject, QTimer, QUrl
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer, QSoundEffect

from .paths import SOUNDS

EVENTS = {
    "startup": "Windows Startup.wav",
    "shutdown": "Windows Shutdown.wav",
    "logon": "Windows Logon Sound.wav",
    "logoff": "Windows Logoff Sound.wav",
    "navigate": "Windows Navigation Start.wav",
    "menu": "Windows Menu Command.wav",
    "default": "Windows Default.wav",
    "error": "Windows Error.wav",
    "exclamation": "Windows Exclamation.wav",
    "critical": "Windows Critical Stop.wav",
    "info": "Windows Information Bar.wav",
    "ding": "Windows Ding.wav",
    "minimize": "Windows Minimize.wav",
    "restore": "Windows Restore.wav",
    "recycle": "Windows Recycle.wav",
    "balloon": "Windows Balloon.wav",
    "notify": "Windows Notify.wav",
    "print_done": "Windows Print complete.wav",
    "hw_insert": "Windows Hardware Insert.wav",
    "hw_remove": "Windows Hardware Remove.wav",
    "hw_fail": "Windows Hardware Fail.wav",
    "battery_low": "Windows Battery Low.wav",
    "battery_critical": "Windows Battery Critical.wav",
    "ring_in": "Windows Ringin.wav",
    "ring_out": "Windows Ringout.wav",
    "uac": "Windows User Account Control.wav",
    "popup_blocked": "Windows Pop-up Blocked.wav",
    "feed": "Windows Feed Discovered.wav",
    "tada": "tada.wav",
    "chimes": "chimes.wav",
    "chord": "chord.wav",
    "user_highlight": "User_Highlight.wav",
    "user_select": "User_Select.wav",
}


class Sounds(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.muted = False
        self.wave = 1.0
        self._effects = {}
        self.scheme = None

    def path(self, event):
        if self.scheme is not None and event in self.scheme:
            return self.scheme[event]
        return SOUNDS / EVENTS[event] if event in EVENTS else None

    def set_scheme(self, scheme):
        self.scheme = scheme
        for effect in self._effects.values():
            effect.deleteLater()
        self._effects = {}

    def _effect(self, event):
        if event not in self._effects:
            effect = QSoundEffect(self)
            effect.setSource(QUrl.fromLocalFile(str(self.path(event))))
            effect.setVolume(self.wave)
            self._effects[event] = effect
        return self._effects[event]

    def preload(self):
        for event in EVENTS:
            if self.path(event) and self.path(event).exists():
                self._effect(event)

    def play(self, event, on_finished=None):
        path = self.path(event) if event in EVENTS else None
        if self.muted or path is None or not path.exists():
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
            QTimer.singleShot(15000, lambda: finish(True))
        effect.play()


def play_file(name, on_finished=None):
    """Play a longer sound (mp3, a wav) from assets/sounds. Returns the QMediaPlayer, or None if muted/missing."""
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


def set_scheme(scheme):
    _instance().set_scheme(scheme)


def preload():
    _instance().preload()


def is_muted():
    return _instance().muted


def set_muted(muted):
    _instance().muted = muted


def wave_volume():
    return _instance().wave


def set_wave_volume(level):
    s = _instance()
    s.wave = max(0.0, min(1.0, level))
    for effect in s._effects.values():
        effect.setVolume(s.wave)
