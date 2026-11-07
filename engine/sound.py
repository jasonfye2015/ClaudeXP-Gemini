"""The sounds, made at start (no files shipped): short synthesized effects, written once as WAVs to a cache folder and
played with Qt's QSoundEffect. Sound follows the computer's mute (host.muted())."""
import math
import tempfile
import wave
from pathlib import Path

import numpy as np

RATE = 22050


def _env(n, attack=0.005, release=0.15):
    t = np.arange(n) / RATE
    a = np.clip(t / max(attack, 1e-4), 0, 1)
    r = np.clip((n / RATE - t) / max(release, 1e-4), 0, 1)
    return a * r


def _noise(n, seed=1):
    return np.random.default_rng(seed).uniform(-1, 1, n)


def _make():
    s = {}
    t = lambda d: np.arange(int(RATE * d)) / RATE   # noqa: E731
    # casting: a zap per element
    for el, (f0, f1, grit) in {"arcane": (900, 380, 0.15), "fire": (300, 120, 0.6), "frost": (1400, 700, 0.1),
                              "storm": (1800, 300, 0.5), "venom": (500, 260, 0.35)}.items():
        x = t(0.16)
        f = f0 + (f1 - f0) * (x / x[-1])
        ph = np.cumsum(2 * math.pi * f / RATE)
        w = np.sin(ph) * (1 - grit) + _noise(len(x), 3) * grit
        s["cast_" + el] = w * _env(len(x), 0.002, 0.12) * 0.35
    x = t(0.12)
    s["hit"] = (_noise(len(x), 5) * 0.6 + np.sin(2 * math.pi * 140 * x) * 0.4) * _env(len(x), 0.001, 0.1) * 0.45
    x = t(0.45)
    s["kill"] = (np.sin(np.cumsum(2 * math.pi * (220 - 160 * x / x[-1]) / RATE)) * 0.5 + _noise(len(x), 7) * 0.3) * _env(len(x), 0.002, 0.4) * 0.4
    x = t(0.25)
    s["hurt"] = (np.sin(2 * math.pi * 90 * x) * 0.6 + _noise(len(x), 9) * 0.4) * _env(len(x), 0.002, 0.2) * 0.55
    x = t(0.18)
    s["coin"] = (np.sin(2 * math.pi * 1650 * x) + 0.5 * np.sin(2 * math.pi * 2475 * x)) * _env(len(x), 0.001, 0.16) * 0.18
    x = t(0.9)
    s["levelup"] = sum(np.sin(2 * math.pi * f * x) * _env(len(x), 0.01 + i * 0.1, 0.6) for i, f in enumerate((523, 659, 784, 1046))) * 0.12
    x = t(0.35)
    s["drink"] = np.sin(np.cumsum(2 * math.pi * (300 + 260 * np.sin(x * 40)) / RATE)) * _env(len(x), 0.01, 0.2) * 0.25
    x = t(1.2)
    s["stairs"] = (np.sin(2 * math.pi * 110 * x) * 0.4 + np.sin(2 * math.pi * 165 * x) * 0.3) * _env(len(x), 0.2, 0.8) * 0.4
    x = t(0.45)
    crack = _noise(len(x), 13) * np.exp(-x * 14) * 0.8 + np.sin(2 * math.pi * 70 * x) * np.exp(-x * 9) * 0.5
    for k in range(5):                                        # (the pieces landing)
        at = int(RATE * (0.08 + k * 0.06))
        n = int(RATE * 0.03)
        crack[at:at + n] += _noise(n, 20 + k) * np.exp(-np.arange(n) / RATE * 60) * 0.35
    s["break"] = crack * 0.5
    x = t(0.12)
    s["thud"] = (np.sin(2 * math.pi * 110 * x) * 0.6 + _noise(len(x), 17) * 0.3) * _env(len(x), 0.001, 0.1) * 0.35
    # the weather's loops (they join end to end) and the thunder
    x = t(3.0)
    hiss = np.convolve(_noise(len(x), 31), [1, -0.85], "same")
    pat = np.zeros(len(x))
    prng = np.random.default_rng(5)
    for at in prng.integers(0, len(x) - 400, 260):
        pat[at:at + 300] += prng.uniform(-1, 1, 300) * np.exp(-np.arange(300) / 40) * 0.6
    s["rain"] = (hiss * 0.35 + pat * 0.4) * 0.5
    x = t(6.0)
    wn = np.cumsum(_noise(len(x), 41)) * 0.02
    wn = wn - np.convolve(wn, np.ones(400) / 400, "same")
    s["wind"] = wn / (np.abs(wn).max() or 1) * (0.55 + 0.45 * np.sin(2 * math.pi * x / 6.0 * 2)) * 0.6
    x = t(3.2)
    rum = np.cumsum(_noise(len(x), 51)) * 0.01
    rum = rum - np.convolve(rum, np.ones(300) / 300, "same")
    crack = _noise(len(x), 52) * np.exp(-x * 9)
    s["thunder"] = (rum / (np.abs(rum).max() or 1) * np.exp(-x * 0.9) * 0.9 + crack * 0.4) * _env(len(x), 0.01, 1.4) * 0.8
    x = t(0.1)
    s["click"] = np.sin(2 * math.pi * 700 * x) * _env(len(x), 0.001, 0.08) * 0.15
    x = t(0.2)
    s["nomana"] = np.sin(2 * math.pi * 180 * x) * _env(len(x), 0.005, 0.15) * 0.2
    x = t(0.6)
    s["foecast"] = (np.sin(np.cumsum(2 * math.pi * (200 + 200 * x / x[-1]) / RATE)) * 0.5 + _noise(len(x), 11) * 0.2) * _env(len(x), 0.05, 0.3) * 0.22
    return s


class Sounds:
    def __init__(self, muted=lambda: False):
        self.muted = muted
        self.effects = {}
        try:
            from PySide6.QtCore import QUrl
            from PySide6.QtMultimedia import QSoundEffect
        except ImportError:
            return
        folder = Path(tempfile.gettempdir()) / "claudenites-sounds"
        folder.mkdir(exist_ok=True)
        for name, w in _make().items():
            path = folder / f"{name}.wav"
            pcm = (np.clip(w, -1, 1) * 32000).astype("<i2").tobytes()
            if not path.exists() or path.stat().st_size != len(pcm) + 44:
                with wave.open(str(path), "wb") as f:
                    f.setnchannels(1)
                    f.setsampwidth(2)
                    f.setframerate(RATE)
                    f.writeframes(pcm)
            pool = []
            for _ in range(3):                         # (a few of each, so quick repeats overlap)
                e = QSoundEffect()
                e.setSource(QUrl.fromLocalFile(str(path)))
                e.setVolume(0.7)
                pool.append(e)
            self.effects[name] = [pool, 0]

    def loop(self, name, volume):
        """A sound that goes on (the rain, the wind), at this volume now (0: stopped)."""
        slot = self.effects.get(name)
        if not slot:
            return
        e = slot[0][0]
        v = 0.0 if self.muted() else max(0.0, min(1.0, volume))
        if v < 0.01:
            if e.isPlaying():
                e.stop()
            return
        e.setVolume(v)
        if not e.isPlaying():
            e.setLoopCount(-2)
            e.play()

    def play(self, name, volume=0.7):
        if self.muted():
            return
        slot = self.effects.get(name)
        if not slot:
            return
        pool, i = slot
        e = pool[i % len(pool)]
        e.setVolume(volume)
        e.play()
        slot[1] = i + 1
