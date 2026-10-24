"""Claudemmings' sound: the original sound effects and music from Local Storage\\Lemmings.

The effects are 8-bit WAVs at the odd rates the original used (3709 Hz, 7418 Hz...), which Qt's player doesn't
always take, so each is converted once to 16-bit 22050 Hz (into the shared Saves folder) and played from there.
Music is the MP3s, looped during a level. Nothing plays while the computer is muted, or with M (music) / S off."""
import array
import wave
from pathlib import Path

from PySide6.QtCore import QUrl

from claudecore import host

RATE = 22050
EVENTS = {"door": "DOOR", "letsgo": "LETSGO", "assign": "MOUSEPRE", "select": "CHANGEOP", "ohno": "OHNO",
          "explode": "EXPLODE", "splat": "SPLAT", "die": "DIE", "yippee": "YIPPEE", "chink": "CHINK", "rate": "TING"}


def _convert(src, dst):
    with wave.open(str(src)) as w:
        ch, width, rate, n = w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()
        raw = w.readframes(n)
    if width == 1:
        samples = [(b - 128) * 256 for b in raw[::ch]]
    else:
        a = array.array("h", raw)
        samples = list(a[::ch])
    out_n = max(1, int(len(samples) * RATE / rate))
    out = array.array("h", [0] * out_n)
    for i in range(out_n):
        pos = i * rate / RATE
        j = int(pos)
        f = pos - j
        s0 = samples[min(j, len(samples) - 1)]
        s1 = samples[min(j + 1, len(samples) - 1)]
        out[i] = int(max(-32768, min(32767, s0 + (s1 - s0) * f)))
    dst.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(dst), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(out.tobytes())


class Audio:
    def __init__(self, parent, root):
        self.parent, self.root = parent, Path(root)
        self.fx = {}
        self.cache = host.saves("claudemmings") / "sfx"
        self.player = self.output = None
        self.music_on = self.sfx_on = True
        self.current = None
        self.closed = False

    # ---- effects ------------------------------------------------------------------------------------------------
    def play(self, event):
        if self.closed or not self.sfx_on or host.muted():
            return
        name = EVENTS.get(event)
        if not name:
            return
        fx = self.fx.get(name)
        if fx is None:
            fx = self._load(name)
            self.fx[name] = fx
        if fx:
            fx.play()

    def _load(self, name):
        src = self.root / "sound effects" / f"{name}.WAV"
        if not src.exists():
            return False
        dst = self.cache / f"{name}.wav"
        try:
            if not dst.exists():
                _convert(src, dst)
            from PySide6.QtMultimedia import QSoundEffect
            fx = QSoundEffect(self.parent)
            fx.setSource(QUrl.fromLocalFile(str(dst)))
            fx.setVolume(0.6)
            return fx
        except Exception:
            return False

    # ---- music --------------------------------------------------------------------------------------------------
    def music(self, title, loop=True):
        """Play the track whose file name starts with title's number ('05 Just Dig!' -> 05 *.mp3)."""
        if self.closed:
            return
        self.current = (title, loop)
        if not self.music_on or host.muted():
            self._stop_player()
            return
        folder = self.root / "background Music"
        number = title.split(" ", 1)[0]
        path = next(iter(sorted(folder.glob(f"{number} *.mp3"))), None) if folder.is_dir() else None
        if path is None:
            self._stop_player()
            return
        try:
            if self.player is None:
                from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
                self.output = QAudioOutput(self.parent)
                self.output.setVolume(0.45)
                self.player = QMediaPlayer(self.parent)
                self.player.setAudioOutput(self.output)
            self.player.stop()
            self.player.setSource(QUrl.fromLocalFile(str(path)))
            self.player.setLoops(-1 if loop else 1)
            self.player.play()
        except Exception:
            pass

    def _stop_player(self):
        if self.player is not None:
            try:
                self.player.stop()
            except Exception:
                pass

    def toggle_music(self):
        self.music_on = not self.music_on
        if self.music_on and self.current:
            self.music(*self.current)
        else:
            self._stop_player()
        return self.music_on

    def toggle_sfx(self):
        self.sfx_on = not self.sfx_on
        return self.sfx_on

    def close(self):
        self.closed = True
        self._stop_player()
        for fx in self.fx.values():
            if fx:
                fx.stop()
