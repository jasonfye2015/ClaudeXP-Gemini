"""The den's sound, made as it plays (no sound files): plain numpy, a block at a time.

  the wind      low, breathing air in the trunk - louder the higher he climbs
  the hum       the silk under him, humming: two low notes beating against each other, as loud as it shakes
  creaks        each step on silk (harder when he hurries); a long one when he slips
  the catch     the whole web taking his weight when he falls into it: a deep, slow thrum
  skittering    many small legs, going away fast
  the lantern   its rattle when shaken; a soft puff when it gutters out
  a thud        a fall to the wood
  a whoosh      his hand across his face
  her           a dry rustle of many legs as she moves - louder the nearer she is
  his heart     lub-dub, when it races (and at the end, slowing, until it stops)

    synth = Synth()
    synth.set(hum=0..1, height=0..1)     the steady parts
    synth.play("creak", gain)            the one-offs: creak, slip, catch, skitter, rattle, puff, thud
    synth.render(n)                      -> float32 (n,), -1..1
"""
import math

import numpy as np

RATE = 22050


def _env(n, attack, release, rate=RATE):
    t = np.arange(n) / rate
    return np.clip(t / max(attack, 1e-4), 0, 1) * np.clip((n / rate - t) / max(release, 1e-4), 0, 1)


def _shaped_noise(rng, n, lo, hi, tilt, rate=RATE):
    """Noise with only the frequencies from lo to hi, falling off as 1/f**tilt - and it loops without a seam."""
    f = np.fft.rfftfreq(n, 1 / rate)
    amp = np.where((f >= lo) & (f <= hi), 1.0 / np.maximum(f, 1.0) ** tilt, 0.0)
    spec = amp * np.exp(1j * rng.uniform(0, math.tau, len(f)))
    x = np.fft.irfft(spec, n)
    return x / (np.abs(x).max() or 1.0)


def _resonator(freq, decay, n, rate=RATE):
    t = np.arange(n) / rate
    return np.sin(math.tau * freq * t) * np.exp(-t / decay)


def _creak(rng, dur, rate=RATE):
    """Silk taking weight: stick and slip - a quick train of catches, each ringing the strand a moment."""
    n = int(dur * rate)
    x = np.zeros(n)
    t = 0.0
    while t < dur:
        hz = 28 + 30 * math.sin(math.pi * t / dur) + rng.uniform(-6, 6)
        i = int(t * rate)
        if i < n:
            x[i] = rng.uniform(0.5, 1.0)
        t += 1.0 / hz
    ring = _resonator(rng.uniform(240, 380), 0.011, int(0.05 * rate), rate) + \
        0.5 * _resonator(rng.uniform(620, 900), 0.006, int(0.05 * rate), rate)
    y = np.convolve(x, ring)[:n] * _env(n, 0.02, dur * 0.5, rate)
    return y / (np.abs(y).max() or 1.0)


def _skitter(rng, dur, rate=RATE):
    n = int(dur * rate)
    x = np.zeros(n)
    count = int(dur * rng.uniform(70, 120))
    at = np.sort(rng.uniform(0, 1, count) ** 1.6) * (n - 1)              # (bunched at the start, thinning: going away)
    x[at.astype(int)] = rng.uniform(0.3, 1.0, count) * np.linspace(1, 0.25, count)
    click = rng.uniform(-1, 1, int(0.0025 * rate)) * np.linspace(1, 0, int(0.0025 * rate))
    y = np.convolve(x, click)[:n]
    y = np.diff(y, prepend=0.0)                                          # (thin and dry: the low end taken away)
    return y / (np.abs(y).max() or 1.0)


def _rattle(rng, rate=RATE):
    n = int(0.7 * rate)
    x = np.zeros(n)
    t = 0.0
    while t < 0.62:
        x[int(t * rate)] = rng.uniform(0.4, 1.0) * (1 - t / 0.7)
        t += rng.uniform(0.035, 0.09)
    ring = sum(_resonator(f, 0.025, int(0.06 * rate), rate) * a for f, a in ((1830, 1.0), (2710, 0.6), (4120, 0.35)))
    grit = np.random.default_rng(int(rng.random() * 1e9)).uniform(-1, 1, 60)
    y = np.convolve(x, ring)[:n] + 0.4 * np.convolve(x, grit)[:n]
    return y / (np.abs(y).max() or 1.0)


def _catch(rng, rate=RATE):
    n = int(2.2 * rate)
    t = np.arange(n) / rate
    f = 52 - 10 * t / 2.2
    y = np.sin(np.cumsum(math.tau * f / rate)) * (0.6 + 0.4 * np.sin(math.tau * 5.5 * t)) + \
        0.5 * np.sin(np.cumsum(math.tau * (f * 1.51) / rate)) * np.exp(-t * 1.2)
    y = y * _env(n, 0.05, 1.6, rate)
    y[:int(0.4 * rate)] += _creak(rng, 0.4, rate) * 0.5
    return y / (np.abs(y).max() or 1.0)


def _thud(rng, rate=RATE):
    n = int(0.4 * rate)
    t = np.arange(n) / rate
    y = np.sin(np.cumsum(math.tau * (75 - 35 * t / 0.4) / rate)) * np.exp(-t * 9)
    y += _shaped_noise(rng, n, 40, 500, 0.5, rate) * np.exp(-t * 30) * 0.6
    return y / (np.abs(y).max() or 1.0)


def _beat(rng, rate=RATE):
    """Lub-dub: two low thumps, the second softer."""
    n = int(0.42 * rate)
    t = np.arange(n) / rate
    y = np.zeros(n)
    for at, f, a in ((0.0, 58.0, 1.0), (0.17, 66.0, 0.7)):
        u = np.clip(t - at, 0, None)
        y += a * np.sin(math.tau * f * u * (1 - 0.3 * u)) * np.exp(-u * 22) * (t >= at)
    return y / (np.abs(y).max() or 1.0)


def _whoosh(rng, rate=RATE):
    n = int(0.4 * rate)
    t = np.arange(n) / rate
    y = _shaped_noise(rng, n, 250, 3500, 0.6, rate) * np.sin(np.pi * t / 0.4) ** 2
    return y / (np.abs(y).max() or 1.0)


def _puff(rng, rate=RATE):
    n = int(0.35 * rate)
    y = _shaped_noise(rng, n, 150, 1800, 0.8, rate) * _env(n, 0.03, 0.3, rate)
    return y / (np.abs(y).max() or 1.0)


class Synth:
    def __init__(self, rate=RATE, seed=7):
        self.rate = rate
        rng = np.random.default_rng(seed)
        import random
        r = random.Random(seed)
        self.wind_loop = _shaped_noise(rng, rate * 8, 35, 700, 0.9, rate)
        self.sounds = {"creak": [_creak(r, d, rate) for d in (0.18, 0.22, 0.26, 0.2)],
                       "slip": [_creak(r, 0.75, rate)],
                       "skitter": [_skitter(rng, d, rate) for d in (0.45, 0.6, 0.75)],
                       "rattle": [_rattle(r, rate), _rattle(r, rate)],
                       "catch": [_catch(r, rate)], "thud": [_thud(rng, rate)], "puff": [_puff(rng, rate)],
                       "whoosh": [_whoosh(rng, rate)], "beat": [_beat(rng, rate)]}
        self.levels = {"creak": 0.32, "slip": 0.55, "skitter": 0.22, "rattle": 0.3, "catch": 0.7, "thud": 0.6, "puff": 0.25, "whoosh": 0.35, "beat": 0.6}
        self.voices = []                    # [samples, position, gain]
        self.n = 0                          # (samples played so far)
        self.hum, self._hum = 0.0, 0.0
        self.height, self._height = 0.0, 0.0
        self.her, self._her = 0.0, 0.0
        self.rustle_loop = _shaped_noise(rng, rate * 4, 90, 1400, 0.7, rate)
        self._pick = 0

    def set(self, hum=None, height=None, her=None):
        if her is not None:
            self.her = max(0.0, min(1.0, her))
        if hum is not None:
            self.hum = max(0.0, min(1.0, hum))
        if height is not None:
            self.height = max(0.0, min(1.0, height))

    def play(self, name, gain=1.0):
        bank = self.sounds.get(name)
        if not bank or gain <= 0.01:
            return
        self._pick += 1
        self.voices.append([bank[self._pick % len(bank)], 0, gain * self.levels[name]])
        if len(self.voices) > 12:
            self.voices.pop(0)

    def render(self, n):
        rate = self.rate
        t = (self.n + np.arange(n)) / rate
        out = np.zeros(n)
        # the wind: louder the higher, breathing slowly
        h0, self._height = self._height, self._height + (self.height - self._height) * 0.2
        i = (self.n + np.arange(n)) % len(self.wind_loop)
        breath = 0.65 + 0.35 * np.sin(math.tau * t / 11.0) * np.sin(math.tau * t / 4.3 + 1.0)
        out += self.wind_loop[i] * breath * np.linspace(0.04 + 0.1 * h0, 0.04 + 0.1 * self._height, n)
        # the hum of the silk under him
        a0, self._hum = self._hum, self._hum + (self.hum - self._hum) * 0.25
        if a0 > 1e-4 or self._hum > 1e-4:
            amp = np.linspace(a0, self._hum, n) * 0.2
            hum = (np.sin(math.tau * 55.0 * t) + 0.8 * np.sin(math.tau * 55.6 * t) + 0.5 * np.sin(math.tau * 82.4 * t)
                   + 0.3 * np.sin(math.tau * 110.7 * t) + 0.12 * np.sin(math.tau * 220.0 * t + np.sin(math.tau * 3 * t)))
            out += hum / 2.7 * amp * (0.75 + 0.25 * np.sin(math.tau * 6.3 * t))
        # her: many legs, slow, felt more than heard - a dry rustle, ticking
        h0, self._her = self._her, self._her + (self.her - self._her) * 0.2
        if h0 > 1e-4 or self._her > 1e-4:
            i = (self.n + np.arange(n)) % len(self.rustle_loop)
            legs = 0.45 + 0.55 * np.abs(np.sin(math.tau * 2.3 * t)) ** 6 + 0.3 * np.abs(np.sin(math.tau * 3.1 * t + 1)) ** 8
            out += self.rustle_loop[i] * legs * np.linspace(h0, self._her, n) * 0.22
        # the one-offs
        keep = []
        for v in self.voices:
            buf, pos, g = v
            m = min(n, len(buf) - pos)
            out[:m] += buf[pos:pos + m] * g
            v[1] = pos + m
            if v[1] < len(buf):
                keep.append(v)
        self.voices = keep
        self.n += n
        return np.tanh(out * 1.2).astype(np.float32)
