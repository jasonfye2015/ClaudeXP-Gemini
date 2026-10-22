"""Windows 11's sounds, played by event name: sound.play("logon"). The same interface as ClaudeXP's sound module,
so the period programs' own calls (sound.play("menu"), sound.is_muted()) go through Windows 11's scheme here - and
in Windows 11's scheme, menus, navigation, minimizing and restoring make no sound at all.

The files come from assets/sounds when you have put some there, else from Local Storage/Windows 11 Media/sounds (the
user's collection on the shared drive, which has the real startup chime as an m4a), else from the real Windows
installation's C:\\Windows\\Media (Windows 10 and 11 share the scheme). Nothing is copied into the project."""
from PySide6.QtCore import QObject, QTimer, QUrl
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer, QSoundEffect

from .paths import HOST_MEDIA, SOUNDS, media_sounds

EVENTS = {
    "startup": ("Windows Startup Sound.m4a", "Windows Startup.wav"),
    "shutdown": "Windows Shutdown.wav",
    "logon": "Windows Logon.wav",
    "logoff": "Windows Logoff Sound.wav",
    "unlock": "Windows Unlock.wav",
    "navigate": None,
    "menu": None,
    "default": "Windows Background.wav",
    "error": "Windows Foreground.wav",
    "exclamation": "Windows Background.wav",
    "critical": "Windows Foreground.wav",
    "info": "Windows Notify System Generic.wav",
    "ding": "Windows Ding.wav",
    "minimize": None,
    "restore": None,
    "recycle": "Windows Recycle.wav",
    "balloon": "Windows Notify System Generic.wav",
    "notify": "Windows Notify System Generic.wav",
    "mail": "Windows Notify Email.wav",
    "message": "Windows Notify Messaging.wav",
    "calendar": "Windows Notify Calendar.wav",
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
    "user_highlight": None,
    "user_select": None,
}


def _find(name):
    """The first of these places that has the file: assets/sounds, Local Storage/Windows 11 Media/sounds, the real
    PC's C:\\Windows\\Media. `name` may be a tuple of candidates, the preferred one first."""
    if not name:
        return None
    names = name if isinstance(name, (tuple, list)) else (name,)
    folders = [SOUNDS]
    media = media_sounds()
    if media is not None:
        folders.append(media)
    folders.append(HOST_MEDIA)
    for candidate in names:
        for folder in folders:
            path = folder / candidate
            if path.exists():
                return path
    return None


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
        return _find(EVENTS.get(event))

    def set_scheme(self, scheme):
        self.scheme = scheme
        for effect in self._effects.values():
            effect.deleteLater()
        self._effects = {}

    def _effect(self, event):
        path = self.path(event)
        if path is not None and path.suffix.lower() != ".wav":
            return None
        if event not in self._effects:
            effect = QSoundEffect(self)
            effect.setSource(QUrl.fromLocalFile(str(self.path(event))))
            effect.setVolume(self.wave)
            self._effects[event] = effect
        return self._effects[event]

    def preload(self):
        for event in EVENTS:
            if self.path(event) is not None:
                self._effect(event)
        start = self.path("startup")
        if start is not None and start.suffix.lower() != ".wav":
            _warm_media()

    def play(self, event, on_finished=None):
        path = self.path(event) if event in EVENTS else None
        if self.muted or path is None or not path.exists():
            if on_finished:
                QTimer.singleShot(0, on_finished)
            return
        if path.suffix.lower() != ".wav":              # the startup chime is an m4a: QSoundEffect only does wav
            _play_path(path, on_finished)
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
    """Play a longer sound (mp3, m4a, a wav) from assets/sounds or the Windows 11 Media collection. Returns the
    QMediaPlayer, or None if muted/missing."""
    path = _find(name)
    if is_muted() or path is None or not path.exists():
        if on_finished:
            QTimer.singleShot(0, on_finished)
        return None
    return _play_path(path, on_finished)


_media_players = []


def _warm_media():
    """Spin the media backend up once so the first startup chime isn't late."""
    try:
        player = QMediaPlayer(_instance())
        player.setAudioOutput(QAudioOutput(player))
        _media_players.append(player)
    except Exception:
        pass


def _play_path(path, on_finished=None):
    if is_muted():
        if on_finished:
            QTimer.singleShot(0, on_finished)
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
    QTimer.singleShot(60000, lambda: finish())
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
