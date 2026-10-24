"""Claudualties' sound, all synthesized (the media folder has pictures only): the cave's drone and drips, the
Expie's footsteps, yelps and whimpers, bandages, cracks, splashes, the trader's chime, the hatch, and a heartbeat
that comes forward as the blood runs low. Written once to this computer's data folder and played from there; the
loops are built on a background thread the first time."""
import math
import random
import threading
import wave
from array import array

from PySide6.QtCore import QUrl

from claudecore import host

RATE = 22050
VERSION = "v1"
LOOPS = ("cave", "water", "heart", "crisis")
LOOP_VOLUME = {"cave": 0.35, "water": 0.25, "heart": 0.5, "crisis": 0.4}
SFX_VOLUME = 0.55


def _sine(buf, start, dur, f0, vol, f1=None, attack=0.01, release=0.05, wrap=False):
    n_total, i0 = len(buf), int(start * RATE)
    n = int(dur * RATE)
    phase = 0.0
    for k in range(n):
        idx = i0 + k
        if idx >= n_total:
            if not wrap:
                break
            idx %= n_total
        t = k / n
        f = f0 + ((f1 - f0) * t if f1 is not None else 0)
        phase += 2 * math.pi * f / RATE
        env = min(1.0, k / max(1, attack * RATE), (n - k) / max(1, release * RATE))
        buf[idx] += math.sin(phase) * vol * env


def _noise(buf, rng, start, dur, vol, decay=20.0, smooth=0.0, wrap=False):
    n_total, i0 = len(buf), int(start * RATE)
    y = 0.0
    for k in range(int(dur * RATE)):
        idx = i0 + k
        if idx >= n_total:
            if not wrap:
                break
            idx %= n_total
        x = rng.uniform(-1, 1)
        y = y + (1 - smooth) * (x - y) if smooth else x
        buf[idx] += y * vol * math.exp(-decay * k / RATE)


def _lowpass(buf, a):
    y = 0.0
    for i in range(len(buf)):
        y += a * (buf[i] - y)
        buf[i] = y


def _wav(path, buf, peak_to=0.8):
    peak = max(1e-6, max(abs(x) for x in buf))
    k = peak_to * 32767 / peak
    data = array("h", (int(max(-32767, min(32767, x * k))) for x in buf))
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with wave.open(str(tmp), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(data.tobytes())
    tmp.replace(path)


def make_sfx(folder):
    out = {}
    rng = random.Random(4)

    def one(name, dur, fn):
        path = folder / f"{name}.wav"
        if not path.exists():
            buf = [0.0] * int(dur * RATE)
            fn(buf)
            _wav(path, buf)
        out[name] = path

    one("step", 0.12, lambda b: _noise(b, rng, 0, 0.1, 0.5, decay=40, smooth=0.6))
    one("land", 0.25, lambda b: (_noise(b, rng, 0, 0.2, 0.8, decay=18, smooth=0.75), _sine(b, 0, 0.15, 90, 0.4, 50)))
    one("yelp", 0.35, lambda b: (_sine(b, 0, 0.3, 700, 0.5, 420), _sine(b, 0, 0.3, 1400, 0.2, 800)))
    one("whimper", 0.6, lambda b: (_sine(b, 0, 0.25, 520, 0.3, 600), _sine(b, 0.3, 0.3, 600, 0.3, 430)))
    one("crack", 0.3, lambda b: (_noise(b, rng, 0, 0.08, 1.0, decay=60), _noise(b, rng, 0.06, 0.2, 0.5, decay=25, smooth=0.3)))
    one("cut", 0.25, lambda b: _noise(b, rng, 0, 0.2, 0.7, decay=30, smooth=0.1))
    one("bandage", 0.5, lambda b: [_noise(b, rng, i * 0.08, 0.1, 0.35, decay=25, smooth=0.8) for i in range(6)])
    one("drink", 0.5, lambda b: [_sine(b, i * 0.12, 0.08, 300 + 60 * i, 0.3, 380 + 60 * i) for i in range(4)])
    one("eat", 0.5, lambda b: [_noise(b, rng, i * 0.16, 0.1, 0.4, decay=35, smooth=0.5) for i in range(3)])
    one("pickup", 0.2, lambda b: (_sine(b, 0, 0.08, 660, 0.4), _sine(b, 0.08, 0.1, 990, 0.4)))
    one("splash", 0.6, lambda b: (_noise(b, rng, 0, 0.5, 0.8, decay=8, smooth=0.5), _sine(b, 0, 0.2, 200, 0.3, 80)))
    one("hatch", 0.9, lambda b: (_noise(b, rng, 0, 0.3, 0.6, decay=12, smooth=0.6), _sine(b, 0.3, 0.5, 110, 0.5, 70),
                                 _noise(b, rng, 0.75, 0.15, 0.5, decay=40, smooth=0.7)))
    one("chime", 0.7, lambda b: [_sine(b, i * 0.15, 0.3, f, 0.35, release=0.2) for i, f in enumerate((880, 1109, 1319))])
    one("beep", 0.15, lambda b: _sine(b, 0, 0.12, 1760, 0.35))
    one("shock", 0.4, lambda b: (_noise(b, rng, 0, 0.3, 1.0, decay=10), _sine(b, 0, 0.3, 60, 0.6)))
    one("craft", 0.4, lambda b: [_noise(b, rng, i * 0.1, 0.08, 0.5, decay=40, smooth=0.3) for i in range(4)])
    one("note", 0.4, lambda b: _noise(b, rng, 0, 0.35, 0.3, decay=6, smooth=0.9))
    one("refuse", 0.5, lambda b: (_sine(b, 0, 0.2, 400, 0.3, 300), _sine(b, 0.25, 0.25, 320, 0.3, 240)))
    one("die", 2.0, lambda b: (_sine(b, 0, 2.0, 220, 0.5, 40, release=1.0), _noise(b, rng, 0, 2.0, 0.3, decay=1.5, smooth=0.9)))
    one("drip", 0.3, lambda b: _sine(b, 0, 0.12, 1800, 0.25, 900))
    one("flash", 0.15, lambda b: _noise(b, rng, 0, 0.1, 0.4, decay=50, smooth=0.2))
    return out


def make_loops(folder):
    out = {}
    rng = random.Random(9)
    path = folder / "cave.wav"
    if not path.exists():
        n = RATE * 8
        buf = [0.0] * n
        for f, v in ((38, 0.5), (57, 0.25), (76, 0.15)):
            _sine(buf, 0, 8.0, f, v, attack=0.0, release=0.0, wrap=True)
        _noise(buf, rng, 0, 8.0, 0.08, decay=0.0, smooth=0.97, wrap=True)
        for i in range(n):
            buf[i] *= 0.8 + 0.2 * math.sin(2 * math.pi * i / n)
        _wav(path, buf, 0.6)
    out["cave"] = path
    path = folder / "water.wav"
    if not path.exists():
        n = RATE * 6
        buf = [0.0] * n
        _noise(buf, rng, 0, 6.0, 0.3, decay=0.0, smooth=0.9, wrap=True)
        for k in range(14):
            _sine(buf, rng.uniform(0, 6), 0.1, rng.uniform(1200, 2400), 0.2, 700, wrap=True)
        _wav(path, buf, 0.6)
    out["water"] = path
    path = folder / "heart.wav"
    if not path.exists():
        n = int(RATE * 0.86)
        buf = [0.0] * n
        for start, vol in ((0.0, 0.9), (0.22, 0.6)):
            _sine(buf, start, 0.16, 55, vol, 38, attack=0.005, release=0.1, wrap=True)
        _wav(path, buf, 0.85)
    out["heart"] = path
    path = folder / "crisis.wav"
    if not path.exists():
        n = RATE * 5
        buf = [0.0] * n
        _sine(buf, 0, 5.0, 110, 0.4, attack=0.0, release=0.0, wrap=True)
        _sine(buf, 0, 5.0, 112.5, 0.4, attack=0.0, release=0.0, wrap=True)
        _sine(buf, 0, 5.0, 165, 0.15, attack=0.0, release=0.0, wrap=True)
        _wav(path, buf, 0.7)
    out["crisis"] = path
    return out


class Audio:
    def __init__(self, parent, music=True, sfx=True):
        self.parent, self.music_on, self.sfx_on = parent, music, sfx
        self.want = {m: 0.0 for m in LOOPS}
        self.want["cave"] = 1.0
        self.volume = {m: 0.0 for m in LOOPS}
        self.fx, self.players, self.outputs = {}, {}, {}
        self.paths = None
        self.closed = self.failed = False
        self.rate = 1.0
        folder = host.data("claudualties") / f"sounds-{VERSION}"
        try:
            from PySide6.QtMultimedia import QSoundEffect
            for name, path in make_sfx(folder).items():
                fx = QSoundEffect(parent)
                fx.setSource(QUrl.fromLocalFile(str(path)))
                fx.setVolume(SFX_VOLUME)
                self.fx[name] = fx
        except Exception:
            self.fx = {}
        threading.Thread(target=self._build, args=(folder,), daemon=True).start()

    def _build(self, folder):
        try:
            self.paths = make_loops(folder)
        except Exception:
            self.failed = True

    def _start(self):
        try:
            from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
            for m in LOOPS:
                out = QAudioOutput(self.parent)
                out.setVolume(0.0)
                pl = QMediaPlayer(self.parent)
                pl.setAudioOutput(out)
                pl.setSource(QUrl.fromLocalFile(str(self.paths[m])))
                pl.setLoops(-1)
                self.outputs[m], self.players[m] = out, pl
                pl.play()
        except Exception:
            self.failed = True

    def tick(self, dt):
        if self.closed or self.failed:
            return
        if self.paths and not self.players:
            self._start()
            return
        if not self.players:
            return
        on = self.music_on and not host.muted()
        for m, out in self.outputs.items():
            want = LOOP_VOLUME[m] * self.want[m] if on else 0.0
            v = self.volume[m]
            step = dt / 1.2 * LOOP_VOLUME[m]
            v = min(want, v + step) if want > v else max(want, v - step)
            if v != self.volume[m]:
                self.volume[m] = v
                out.setVolume(v)
        try:
            pl = self.players.get("heart")
            if pl is not None and abs(pl.playbackRate() - self.rate) > 0.02:
                pl.setPlaybackRate(self.rate)
        except Exception:
            pass

    def play(self, name, volume=1.0):
        if not self.sfx_on or self.closed or host.muted():
            return
        fx = self.fx.get(name)
        if fx is not None:
            fx.setVolume(SFX_VOLUME * volume)
            fx.play()

    def stop(self):
        self.closed = True
        for pl in self.players.values():
            pl.stop()
        for fx in self.fx.values():
            fx.stop()
