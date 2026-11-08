"""The den's sound's way out: engine/sound.py's synth, pulled a block at a time by a QAudioSink, following the
computer's mute. If there's no sound device, there's simply no sound."""
import math
import random
import time

from PySide6.QtCore import QIODevice

from ..engine.sound import RATE, Synth


class _Stream(QIODevice):
    def __init__(self, synth, gain):
        super().__init__()
        self.synth, self.gain = synth, gain

    def readData(self, maxlen):
        n = max(0, min(maxlen // 4, RATE // 20))
        if n == 0:
            return b""
        x = self.synth.render(n) * self.gain()                      # (n, 2): left, right - interleaved
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
        self.volume = 0.8
        self.heartbeat = True
        self.aloud = True
        self._beat = None
        self.her = None                                  # (her voice: started the first time she speaks)
        self.synth = Synth(RATE)
        self.synth.music.ready()                             # (the waltz's notes, made ahead)
        self.sink = None
        self._fade = 0.0
        try:
            from PySide6.QtMultimedia import QAudioFormat, QAudioSink, QMediaDevices
            fmt = QAudioFormat()
            fmt.setSampleRate(RATE)
            fmt.setChannelCount(2)
            fmt.setSampleFormat(QAudioFormat.Int16)
            dev = QMediaDevices.defaultAudioOutput()
            if dev.isNull() or not dev.isFormatSupported(fmt):
                return
            self.stream = _Stream(self.synth, self._gain)
            self.stream.open(QIODevice.ReadOnly)
            self.sink = QAudioSink(dev, fmt)
            self.sink.setBufferSize(RATE // 8 * 4)
            self.sink.start(self.stream)
        except Exception:
            self.sink = None

    def _gain(self):
        want = 0.0 if self.muted() else 1.1 * self.volume
        self._fade += (want - self._fade) * 0.15                 # (a block's worth of fade, so it never clicks)
        return self._fade

    def score(self, night, scene=None, playing=True):
        """The music, following the night: the drips, the waltz, the crown, a coda, or silence - and her moods."""
        mode = "explore"
        if playing and night is not None:
            if night.dying is not None:
                mode = "silence"                                        # (Supper ends in silence)
            elif night.ending is not None:
                mode = "coda:" + night.ending.name
            elif scene is not None:
                mode = "crown" if getattr(scene, "name", "") == "crown" else "scene"
        mood = {}
        if playing and night is not None:
            mood = dict(night.moods.values())
            mood["venom"] = night.venom.active
        self.synth.music.set(mode, **{k: v for k, v in mood.items()
                                      if k in ("hunger", "patience", "suspicion", "fascination", "venom")})

    @staticmethod
    def pan(night, p):
        from ..engine.sound import heard_pan
        return heard_pan(night, p)

    def hear(self, night, events):
        """What the night just did, as sound; and the steady parts as they stand now."""
        s = self.synth
        cam = getattr(night, "camera", None)
        room = night.where() if hasattr(night, "where") else "hollow"
        s.set(room="tunnel" if room == "tunnel" else "crown" if room == "crown" else
              "chamber" if room in ("gallery", "larder", "high hollow") else "hollow")
        her_p = night.her.at() if getattr(night, "her", None) is not None else None
        s.speech_pan = 0.0 if (night.quiet or cam is not None or her_p is None) else self.pan(night, her_p)
        af = getattr(night, "afflict", None)
        if af is not None:
            s.muffle = af.haze * 0.8
            if af.tier("poison") >= 2 and random.random() < 0.002:      # (a cough, now and then)
                s.play("cough")
            if af.tier("health") >= 1 and not night.quiet:
                s.set(breath=0.7 + 0.3 * (af.tier("health") >= 2))     # (panting)
            elif not night.quiet:
                s.set(breath=0.0)
            if af.posture > 0.4 and night.moved_now > 0 and random.random() < 0.08:
                s.play("scrape", 0.5)
        on = night.on is not None
        d = night.dying
        if d is not None and d.t < 20.0 and random.random() < 0.09:  # (all over him: the sound of them never stops)
            s.play("skitter", 0.4 + 0.5 * random.random())
        sg = getattr(night, "sightings", None)
        thrum = sg.thrum * 0.3 if sg is not None else 0.0          # (her web, thrumming with her)
        s.set(hum=max(thrum, min(1.0, 0.12 + night.tremor * 0.35) if on else min(0.3, night.tremor * 0.1)),
              height=night.y / 26.0 if d is None or not d.done else 0.0)
        sky = getattr(night, "sky", None)
        if sky is not None:
            s.set(rain=sky.strength if sky.weather in ("rain", "storm") else 0.0)
        moods = getattr(night, "moods", None)
        if moods is not None:
            v = getattr(night, "venom", None)
            waver = 1.0 + (0.05 * math.sin(time.perf_counter() * 1.7) + 0.02 * math.sin(time.perf_counter() * 4.3)
                           if v is not None and v.active else 0.0)
            s.set(pitch=moods.hum_pitch() * waver)
        her = getattr(night, "her", None)
        if her is not None and d is None:
            near = max(0.0, 1.0 - math.dist(her.at(), night.eye) / 14.0)
            s.set(her=(0.15 + 0.85 * her.moving) * near ** 1.5, her_pan=self.pan(night, her.at()))
        else:
            s.set(her=0.0)
        b = night.body.beats                                         # (his heart: heard when it races, and at the end)
        if b and b[-1] != self._beat:
            self._beat = b[-1]
            loud = max(0.0, min(1.0, (night.body.bpm - 92) / 50.0)) if d is None else 0.85
            if self.heartbeat and loud > 0.05:
                s.play("beat", loud)
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
                s.play("skitter", 0.55 * e[1], random.uniform(-0.7, 0.7))
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
            elif kind == "death" and e[1] == "wrap":
                s.play("creak", 1.5)
            elif kind == "death" and e[1] == "drag":
                s.play("slip", 1.2)
            elif kind == "death" and e[1] == "lift":
                s.play("catch", 1.2)
            elif kind == "her" and e[1] == "strike":
                s.play("slip", 1.4, self.pan(night, her_p))
                s.play("skitter", 1.0, self.pan(night, her_p))
            elif kind == "her" and e[1] == "bite":
                s.play("thud", 0.9)
            elif kind == "her" and e[1] == "glimpse":
                s.play("creak", 1.6, self.pan(night, her_p))           # (the web shifting under her weight)
            elif kind == "cocoon" and e[3]:
                pc = self.pan(night, e[2])
                s.play("slip", 1.0, pc)                            # (the silk tearing)
                s.play("skitter", 1.0, pc)
                s.play("skitter", 0.8, pc * 0.6)
            elif kind == "sight":                                     # (her, seen in pieces)
                hp = self.pan(night, her_p)
                if e[1] == "cross":
                    s.play("skitter", 0.9, hp)
                    s.play("creak", 1.2, hp)
                elif e[1] == "behind":
                    s.play("skitter", 1.0, 0.0)
                    s.play("slip", 0.8, 0.0)
                elif e[1] == "legs":
                    s.play("creak", 1.0, hp)
            elif kind == "thunder":
                s.play("thunder", 0.5 + 0.5 * e[1], random.uniform(-0.6, 0.6))
            elif kind == "swipe":
                s.play("whoosh")
            elif kind == "afflict":                                    # (what the night's doing to him)
                {"vomit": lambda: s.play("retch"), "refuse": lambda: s.play("no"),
                 "fall": lambda: (s.play("thud", 0.7), s.play("scrape")), "eye": lambda: s.play("scream"),
                 "crawl": lambda: s.play("scrape", 0.8), "stand": lambda: s.play("scrape", 0.5)}.get(e[1], lambda: None)()
            elif kind == "spell" and e[2] == "cast":
                s.play("whoosh", 0.8)
            elif kind == "smoulder":
                s.play("puff", 1.4)
                s.play("creak", 1.8)
            elif kind == "skitter":
                s.play("skitter", max(0.0, 1.0 - e[2] / 7.0), self.pan(night, e[1]))
            elif kind == "lantern" and e[1] == "shake":
                s.play("rattle", 1.0, 0.25)                             # (the lantern: a little to his right)
            elif kind == "lantern" and e[1] == "out":
                s.play("puff")

    def warm(self):
        """Her voice, readied in the background (so the first line isn't late)."""
        if not self.aloud:
            return
        if self.her is None:
            from ..engine.herspeech import HerSpeech
            self.her = HerSpeech()
        self.her.warm()

    def say(self, text):
        """Her line, aloud - if her voice is on, and there to be had."""
        if not self.aloud:
            return False
        if self.her is None:
            from ..engine.herspeech import HerSpeech
            self.her = HerSpeech()
        if not self.her.available():
            return False
        self.her.say(text, self.synth.speak)
        return True

    def stop(self):
        if self.her is not None:
            self.her.stop()
            self.her = None
        if self.sink is not None:
            self.sink.stop()
            self.sink = None
