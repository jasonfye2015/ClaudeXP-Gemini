"""The music's way out: engine/music.py's synth, pulled a block at a time by a QAudioSink. It follows the game (the
town, the forest, each band of the Deep, a guardian's fight), the menu's Music switch and volume, and the
computer's mute. If there's no sound device, there's simply no music."""
from PySide6.QtCore import QIODevice

from ..engine.music import Synth

RATE = 32000


class _Stream(QIODevice):
    def __init__(self, synth, gain):
        super().__init__()
        self.synth, self.gain = synth, gain

    def readData(self, maxlen):
        n = max(0, min(maxlen // 2, RATE // 20))
        if n == 0:
            return b""
        x = self.synth.render(n) * self.gain()
        return (x * 32767).astype("<i2").tobytes()

    def writeData(self, data):
        return 0

    def bytesAvailable(self):
        return RATE * 2 + super().bytesAvailable()

    def isSequential(self):
        return True


class Music:
    def __init__(self, enabled=lambda: True, volume=lambda: 0.8, muted=lambda: False):
        self.enabled, self.volume, self.muted = enabled, volume, muted
        self.synth = Synth(RATE)
        self.sink = None
        self._fade = 0.0
        try:
            from PySide6.QtMultimedia import QAudioFormat, QAudioSink, QMediaDevices
            fmt = QAudioFormat()
            fmt.setSampleRate(RATE)
            fmt.setChannelCount(1)
            fmt.setSampleFormat(QAudioFormat.Int16)
            dev = QMediaDevices.defaultAudioOutput()
            if dev.isNull() or not dev.isFormatSupported(fmt):
                return
            self.stream = _Stream(self.synth, self._gain)
            self.stream.open(QIODevice.ReadOnly)
            self.sink = QAudioSink(dev, fmt)
            self.sink.setBufferSize(RATE // 4 * 2)
            self.sink.start(self.stream)
        except Exception:
            self.sink = None

    def _gain(self):
        want = 0.0 if (self.muted() or not self.enabled()) else float(self.volume())
        self._fade += (want - self._fade) * 0.15                 # (a block's worth of fade, so it never clicks)
        return self._fade

    def place(self, key, boss=False):
        self.synth.place(key, boss)

    def stop(self):
        if self.sink is not None:
            self.sink.stop()
            self.sink = None

