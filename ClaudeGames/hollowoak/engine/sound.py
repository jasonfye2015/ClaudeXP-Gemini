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
  the weather   rain hissing down the trunk; thunder, a crack and a long roll
  his heart     lub-dub, when it races (and at the end, slowing, until it stops)

    synth = Synth()
    synth.set(hum=0..1, height=0..1)     the steady parts
    synth.play("creak", gain)            the one-offs: creak, slip, catch, skitter, rattle, puff, thud
    synth.render(n)                      -> float32 (n, 2), left and right, -1..1
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


def _thunder(rng, rate=RATE):
    """A crack, and a long roll after it."""
    n = int(4.2 * rate)
    t = np.arange(n) / rate
    roll = _shaped_noise(rng, n, 25, 260, 1.1, rate) * np.exp(-t / 1.4) * (0.6 + 0.4 * np.sin(np.pi * t * 1.3) ** 2)
    crack = _shaped_noise(rng, n, 200, 3000, 0.6, rate) * np.exp(-t / 0.12)
    y = roll + crack * 0.5
    return y / (np.abs(y).max() or 1.0)


def _puff(rng, rate=RATE):
    n = int(0.35 * rate)
    y = _shaped_noise(rng, n, 150, 1800, 0.8, rate) * _env(n, 0.03, 0.3, rate)
    return y / (np.abs(y).max() or 1.0)


def _retch(rng, rate=RATE):
    """Heaving: a low, wet, rising noise, twice, and the spill."""
    n = int(1.6 * rate)
    t = np.arange(n) / rate
    y = np.zeros(n)
    for at, g in ((0.0, 0.6), (0.55, 1.0)):
        k = np.clip((t - at) / 0.5, 0, 1)
        env = np.sin(np.pi * k) ** 2 * (t >= at)
        y += _shaped_noise(rng, n, 120, 900, 0.6, rate) * env * g
        y += np.sin(math.tau * (85 + 60 * k) * t) * env * 0.5 * g
    y += _shaped_noise(rng, n, 300, 3000, 0.4, rate) * np.exp(-np.maximum(0, t - 1.05) * 6) * (t > 1.05) * 0.6
    return y / (np.abs(y).max() or 1.0)


def _cough(rng, rate=RATE):
    n = int(0.6 * rate)
    t = np.arange(n) / rate
    y = np.zeros(n)
    for at in (0.0, 0.28):
        y += _shaped_noise(rng, n, 200, 2500, 0.5, rate) * np.exp(-np.maximum(0, t - at) * 18) * (t >= at)
    return y / (np.abs(y).max() or 1.0)


def _no(rng, rate=RATE):
    """Mm-mm: two closed-mouthed hums, the second lower."""
    n = int(0.75 * rate)
    t = np.arange(n) / rate
    y = np.zeros(n)
    for at, f in ((0.0, 150.0), (0.36, 118.0)):
        env = np.sin(np.pi * np.clip((t - at) / 0.3, 0, 1)) ** 2 * (t >= at) * (t < at + 0.3)
        ph = math.tau * f * t
        y += (np.sin(ph) + 0.5 * np.sin(2 * ph) + 0.25 * np.sin(3 * ph)) * env
    return y / (np.abs(y).max() or 1.0)


def _scream(rng, rate=RATE):
    """Stifled, through his teeth: a strained rising tone and breath, muffled."""
    n = int(1.5 * rate)
    t = np.arange(n) / rate
    env = np.clip(t / 0.15, 0, 1) * np.clip((1.5 - t) / 0.6, 0, 1)
    f = 260 + 120 * np.clip(t / 0.8, 0, 1)
    ph = np.cumsum(math.tau * f / rate)
    y = (np.sin(ph) + 0.6 * np.sin(2 * ph) + 0.3 * np.sin(3.01 * ph)) * env
    y += _shaped_noise(rng, n, 300, 1800, 0.5, rate) * env * 0.8
    k = 0.08                                                            # (behind his hand: dull)
    for i in range(1, n):
        y[i] = y[i - 1] + k * (y[i] - y[i - 1])
    return y / (np.abs(y).max() or 1.0)


def _scrape(rng, rate=RATE):
    n = int(0.5 * rate)
    y = _shaped_noise(rng, n, 80, 900, 0.7, rate) * _env(n, 0.08, 0.3, rate)
    return y / (np.abs(y).max() or 1.0)


def heard_pan(night, p):
    """Where p is, heard: -1 hard left of him .. 1 hard right (a little less, behind him)."""
    if p is None:
        return 0.0
    ex, _ey, ez = night.eye
    dx, dz = p[0] - ex, p[2] - ez
    d = math.hypot(dx, dz) or 1.0
    rx, rz = math.cos(night.yaw), math.sin(night.yaw)
    fx, fz = math.sin(night.yaw), -math.cos(night.yaw)
    side = (dx * rx + dz * rz) / d
    ahead = (dx * fx + dz * fz) / d
    return side * (1.0 if ahead > -0.2 else 0.8)


def _pans(pan):
    """Equal-power: pan -1 (all left) .. 1 (all right) -> (left, right) gains."""
    a = (max(-1.0, min(1.0, pan)) + 1.0) * math.pi / 4
    return math.cos(a) * 1.41421356 * 0.75 + 0.25, math.sin(a) * 1.41421356 * 0.75 + 0.25


class _Comb:
    """A feedback comb, its delay longer than a block: so a block is one numpy step."""

    def __init__(self, delay):
        self.ring = np.zeros(delay)
        self.at = 0

    def run(self, x, g):
        d = len(self.ring)
        out = np.empty(len(x))
        for j in range(0, len(x), d):             # (blocks longer than the delay: in pieces)
            seg = x[j:j + d]
            idx = (self.at + np.arange(len(seg))) % d
            past = self.ring[idx]
            self.ring[idx] = seg + g * past
            self.at = (self.at + len(seg)) % d
            out[j:j + len(seg)] = past
        return out


ROOMS = {"hollow": (0.32, 0.78), "tunnel": (0.12, 0.45), "crown": (0.08, 0.55), "chamber": (0.18, 0.6)}


class _Reverb:
    """The space he's in: four combs an ear, their echoes darker as they go (wet, feedback by room)."""

    def __init__(self):
        self.left = [_Comb(d) for d in (1163, 1327, 1489, 1613)]
        self.right = [_Comb(d) for d in (1201, 1361, 1523, 1657)]
        self.wet, self.fb = ROOMS["hollow"]
        self.want = ROOMS["hollow"]
        self._lp = np.zeros(2)

    def room(self, name):
        self.want = ROOMS.get(name, ROOMS["hollow"])

    def run(self, send):
        self.wet += (self.want[0] - self.wet) * 0.05
        self.fb += (self.want[1] - self.fb) * 0.05
        l = sum(c.run(send, self.fb) for c in self.left) * (self.wet / 4)
        r = sum(c.run(send, self.fb) for c in self.right) * (self.wet / 4)
        return l, r


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
                       "whoosh": [_whoosh(rng, rate)], "beat": [_beat(rng, rate)],
                       "thunder": [_thunder(rng, rate), _thunder(rng, rate)],
                       "retch": [_retch(rng, rate)], "cough": [_cough(rng, rate)], "no": [_no(rng, rate)],
                       "scream": [_scream(rng, rate)], "scrape": [_scrape(rng, rate), _scrape(rng, rate)]}
        self.levels = {"creak": 0.32, "slip": 0.55, "skitter": 0.22, "rattle": 0.3, "catch": 0.7, "thud": 0.6, "puff": 0.25, "whoosh": 0.35, "beat": 0.6, "thunder": 0.85, "retch": 0.6, "cough": 0.45, "no": 0.4, "scream": 0.7, "scrape": 0.3}
        self.voices = []                    # [samples, position, gain]
        self.n = 0                          # (samples played so far)
        self.hum, self._hum = 0.0, 0.0
        self.height, self._height = 0.0, 0.0
        self.her, self._her = 0.0, 0.0
        self.pitch, self._pitch, self._hph = 1.0, 1.0, 0.0
        self.speech = None                  # (her voice, a line at a time: [samples, position, gain])
        self.breath, self._breath = 0.0, 0.0     # (his breathing: heard in her scenes)
        self.rain, self._rain = 0.0, 0.0         # (rain, coming down through the crown)
        self.rain_loop = _shaped_noise(rng, rate * 3, 700, 7000, 0.4, rate)
        self.breath_loop = _shaped_noise(rng, rate * 2, 250, 2600, 0.5, rate)
        self.rustle_loop = _shaped_noise(rng, rate * 4, 90, 1400, 0.7, rate)
        self._pick = 0
        from .music import Music
        self.music = Music(rate)                 # (the score: engine/music.py)
        self.music_gain = 0.7
        self.muffle, self._lp = 0.0, 0.0          # (his hearing, dulled: stupor's haze)
        self.her_pan = 0.0                        # (where she is, left to right of him)
        self.speech_pan = 0.0                     # (where her voice comes from: the middle, in her scenes)
        self.reverb = _Reverb()                   # (the space he's in)

    def set(self, hum=None, height=None, her=None, pitch=None, breath=None, rain=None, her_pan=None, room=None):
        if rain is not None:
            self.rain = rain
        if breath is not None:
            self.breath = breath
        if pitch is not None:
            self.pitch = pitch
        if her is not None:
            self.her = max(0.0, min(1.0, her))
        if hum is not None:
            self.hum = max(0.0, min(1.0, hum))
        if height is not None:
            self.height = max(0.0, min(1.0, height))
        if her_pan is not None:
            self.her_pan = max(-1.0, min(1.0, her_pan))
        if room is not None:
            self.reverb.room(room)

    def play(self, name, gain=1.0, pan=0.0):
        """A one-off, where it is: pan -1 (left) .. 1 (right)."""
        bank = self.sounds.get(name)
        if not bank or gain <= 0.01:
            return
        self._pick += 1
        self.voices.append([bank[self._pick % len(bank)], 0, gain * self.levels[name], max(-1.0, min(1.0, pan))])
        if len(self.voices) > 12:
            self.voices.pop(0)

    def speak(self, samples, gain=1.0):
        """A line in her voice (already at the synth's rate): it plays over the den, which quiets a little for it - from
        where she is (speech_pan), unless she's before him."""
        if samples is not None and len(samples):
            self.speech = [np.asarray(samples, np.float64), 0, gain]

    def speaking(self):
        return self.speech is not None

    def speech_level(self):
        """How loud her voice is just now, 0..1 (her fangs move with it)."""
        if self.speech is None:
            return 0.0
        buf, pos, g = self.speech
        seg = buf[max(0, pos - 600):pos]
        return 0.0 if not len(seg) else min(1.0, float(np.sqrt((seg ** 2).mean())) * 4.0 * g)

    def render(self, n):
        """-> float32 (n, 2): left, right."""
        rate = self.rate
        t = (self.n + np.arange(n)) / rate
        L, R = np.zeros(n), np.zeros(n)
        send = np.zeros(n)                                        # (into the hollow's echo)
        # the wind: louder the higher, breathing slowly - each ear its own gusts
        h0, self._height = self._height, self._height + (self.height - self._height) * 0.2
        ln = len(self.wind_loop)
        i = (self.n + np.arange(n)) % ln
        breath = 0.65 + 0.35 * np.sin(math.tau * t / 11.0) * np.sin(math.tau * t / 4.3 + 1.0)
        amp = np.linspace(0.04 + 0.1 * h0, 0.04 + 0.1 * self._height, n) * breath
        L += self.wind_loop[i] * amp
        R += self.wind_loop[(i + ln // 2) % ln] * amp
        # the hum of the silk under him (under his feet: both ears)
        a0, self._hum = self._hum, self._hum + (self.hum - self._hum) * 0.25
        if a0 > 1e-4 or self._hum > 1e-4:
            amp = np.linspace(a0, self._hum, n) * 0.2
            p0, self._pitch = self._pitch, self._pitch + (self.pitch - self._pitch) * 0.05
            ph = self._hph + np.cumsum(math.tau * 55.0 * np.linspace(p0, self._pitch, n) / rate)   # (her hunger: higher)
            self._hph = float(ph[-1]) % (math.tau * 1000)
            hum = (np.sin(ph) + 0.8 * np.sin(ph * 1.0109) + 0.5 * np.sin(ph * 1.498)
                   + 0.3 * np.sin(ph * 2.013) + 0.12 * np.sin(ph * 4.0 + np.sin(math.tau * 3 * t)))
            x = hum / 2.7 * amp * (0.75 + 0.25 * np.sin(math.tau * 6.3 * t))
            L += x
            R += x
            send += x * 0.6
        # her: many legs, slow, felt more than heard - a dry rustle, ticking, from where she is
        h0, self._her = self._her, self._her + (self.her - self._her) * 0.2
        if h0 > 1e-4 or self._her > 1e-4:
            i = (self.n + np.arange(n)) % len(self.rustle_loop)
            legs = 0.45 + 0.55 * np.abs(np.sin(math.tau * 2.3 * t)) ** 6 + 0.3 * np.abs(np.sin(math.tau * 3.1 * t + 1)) ** 8
            x = self.rustle_loop[i] * legs * np.linspace(h0, self._her, n) * 0.22
            pl, pr = _pans(self.her_pan)
            L += x * pl
            R += x * pr
            send += x * 0.8
        # rain: a hiss down the trunk, and drops ticking - all about him
        r0, self._rain = self._rain, self._rain + (self.rain - self._rain) * 0.05
        if r0 > 1e-4 or self._rain > 1e-4:
            ln = len(self.rain_loop)
            i = (self.n + np.arange(n)) % ln
            amp = np.linspace(r0, self._rain, n) * 0.09
            L += self.rain_loop[i] * amp
            R += self.rain_loop[(i + ln // 3) % ln] * amp
        # his breathing, close: in, and out, slowly
        b0, self._breath = self._breath, self._breath + (self.breath - self._breath) * 0.1
        if b0 > 1e-4 or self._breath > 1e-4:
            i = (self.n + np.arange(n)) % len(self.breath_loop)
            ph = (t % 4.6) / 4.6
            shape = np.where(ph < 0.42, np.sin(np.pi * ph / 0.42) ** 2, 0.7 * np.sin(np.pi * (ph - 0.42) / 0.5) ** 2 * (ph < 0.92))
            x = self.breath_loop[i] * shape * np.linspace(b0, self._breath, n) * 0.07
            L += x
            R += x
        # the score: in the middle of everything
        if self.music_gain > 0.001:
            x = self.music.render(n) * self.music_gain
            L += x
            R += x
        # the one-offs, each where it is
        keep = []
        for v in self.voices:
            buf, pos, g, pan = v
            m = min(n, len(buf) - pos)
            x = buf[pos:pos + m] * g
            pl, pr = _pans(pan)
            L[:m] += x * pl
            R[:m] += x * pr
            send[:m] += x
            v[1] = pos + m
            if v[1] < len(buf):
                keep.append(v)
        self.voices = keep
        # her voice, over it all - from where she is - and the den hushed a little while she speaks
        if self.speech is not None:
            L *= 0.6
            R *= 0.6
            buf, pos, g = self.speech
            m = min(n, len(buf) - pos)
            x = buf[pos:pos + m] * g * 0.9
            pl, pr = _pans(self.speech_pan * 0.7)
            L[:m] += x * pl
            R[:m] += x * pr
            send[:m] += x * 0.5
            self.speech[1] = pos + m
            if self.speech[1] >= len(buf):
                self.speech = None
        # the hollow's echo: long and dark up the trunk, close in the roots, thin under the open sky
        el, er = self.reverb.run(send)
        L += el
        R += er
        self.n += n
        out = np.stack([L, R], axis=1)
        if self.muffle > 0.01:                    # (sounds from far away: a soft low-pass)
            k = 1.0 - 0.82 * min(1.0, self.muffle)
            y = np.empty_like(out)
            lp = self._lp if np.ndim(self._lp) else np.zeros(2)
            for j in range(0, n, 32):              # (in short runs: cheap enough)
                seg = out[j:j + 32]
                lp = lp + k * (seg.mean(axis=0) - lp)
                y[j:j + 32] = seg * (1 - 0.82 * min(1.0, self.muffle)) + lp * 0.82 * min(1.0, self.muffle)
            self._lp = lp
            out = y
        return np.tanh(out * 1.2).astype(np.float32)
