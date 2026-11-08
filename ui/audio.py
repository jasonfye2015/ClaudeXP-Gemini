"""The den's sound's way out: engine/sound.py's synth, pulled a block at a time by a QAudioSink, following the
computer's mute. If there's no sound device, there's simply no sound."""
import random

from PySide6.QtCore import QIODevice

from ..engine.sound import RATE, Synth


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


class DenAudio:
    def __init__(self, muted=lambda: False):
        self.muted = muted
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
            self.sink.setBufferSize(RATE // 8 * 2)
            self.sink.start(self.stream)
        except Exception:
            self.sink = None

    def _gain(self):
        want = 0.0 if self.muted() else 0.9
        self._fade += (want - self._fade) * 0.15                 # (a block's worth of fade, so it never clicks)
        return self._fade

    def hear(self, night, events):
        """What the night just did, as sound; and the steady parts as they stand now."""
        s = self.synth
        on = night.on is not None
        d = night.dying
        if d is not None and d.t < 17.0 and random.random() < 0.09:  # (all over him: the sound of them never stops)
            s.play("skitter", 0.4 + 0.5 * random.random())
        s.set(hum=min(1.0, 0.12 + night.tremor * 0.35) if on else min(0.3, night.tremor * 0.1),
              height=night.y / 26.0 if d is None or not d.done else 0.0)
        for e in events:
            kind = e[0]
            if kind == "silk" and e[1] == "step":
                s.play("creak", 1.4 if e[2] else 0.8)
            elif kind == "silk" and e[1] == "slip":
                s.play("slip")
            elif kind == "silk" and e[1] == "caught":
                s.play("catch")
            elif kind == "fall" and not on:
                s.play("thud", min(1.0, e[1] / 14.0))
            elif kind == "crawler":                               # (right across his eyes: close, quick)
                s.play("skitter", 0.55 * e[1])
            elif kind == "dangler" and e[1] == "face":
                s.play("skitter", 0.9)
            elif kind == "swarm" and e[1] == "up":
                s.play("skitter", 0.25)
            elif kind == "lantern" and e[1] == "break":
                s.play("rattle", 1.3)
                s.play("thud", 0.4)
                s.play("puff", 1.2)
            elif kind == "collapse":
                s.play("thud", 0.8)
            elif kind == "death" and e[1] == "drag":
                s.play("slip", 1.2)
            elif kind == "death" and e[1] == "lift":
                s.play("catch", 1.2)
            elif kind == "swipe":
                s.play("whoosh")
            elif kind == "skitter":
                s.play("skitter", max(0.0, 1.0 - e[2] / 7.0))
            elif kind == "lantern" and e[1] == "shake":
                s.play("rattle")
            elif kind == "lantern" and e[1] == "out":
                s.play("puff")

    def stop(self):
        if self.sink is not None:
            self.sink.stop()
            self.sink = None
