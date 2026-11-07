"""The music: ClaudeRPG's own (its SND engine, by Kithylin, MIT), carried over into Python - every note made as it
plays, never a recording. A low drone of three detuned saws under a slowly breathing filter; over it, a step
sequencer: in the calm ("explore") a bass note at the bar and the fifth at the half, a lead picked from the world's
scale, now and then a high bell, and an echo; for a guardian ("boss") a driving bass line, kicks, hats and snares.
Each of ClaudeRPG's worlds has its own scale, instruments and tempo (its MSTY): the Undercroft, the Frozen
Caverns, the Sunken Halls, the Clockwork City (a waltz), the Burning Heart (drums) and the Crystal Grotto.

    synth = Synth(rate)
    synth.set_style("undercroft", root=45)    a world's style (None: ClaudeRPG's own town/surface style), its root
    synth.set_mode("boss")                    or "explore"
    synth.render(n) -> float32 (n,)           the next n samples, -1..1

No Qt here: ui/audio.py plays it through a QAudioSink; the tests listen to it as numbers."""
import math
import random

import numpy as np

# ClaudeRPG's worlds' music (its MSTY, as it is): explore step (s), boss step, scale, lead wave, lead length, lead
# volume, lead chance, the boss scale and bass line, and the touches (bells, swells, the waltz, drums...)
STYLES = {
    "undercroft": {"et": .42, "bt": .16, "sc": [0, 2, 3, 5, 7, 9, 10, 12], "lead": "triangle", "ld": .5, "lv": .1, "lp": .34,
                   "bsc": [0, 2, 3, 5, 7, 9, 10, 12, 14], "bass": [0, 0, 12, 0, 0, 0, 3, 0, 0, 0, 12, 0, 5, 0, 3, 0]},
    "frozen": {"et": .52, "bt": .17, "sc": [0, 3, 5, 7, 10, 12, 15], "lead": "sine", "ld": 2.6, "lv": .07, "lp": .22, "bell": .16,
               "bsc": [0, 3, 5, 7, 10, 12, 15], "bass": [0, 0, 0, 12, 0, 0, 7, 0, 0, 0, 0, 12, 0, 0, 3, 0], "bbell": 1},
    "sunken": {"et": .48, "bt": .17, "sc": [0, 1, 3, 5, 7, 8, 10, 12], "lead": "sine", "ld": 2.2, "lv": .08, "lp": .25, "swell": 1,
               "bsc": [0, 1, 3, 5, 7, 8, 10, 12, 13], "bass": [0, 0, 1, 0, 0, 0, 0, 1, 0, 0, -2, 0, 0, 0, 1, 0]},
    "city": {"et": .3, "bt": .15, "sc": [0, 2, 4, 5, 7, 9, 11, 12], "lead": "square", "ld": .25, "lv": .03, "lp": .3, "cut": 1800,
             "waltz": 1, "tick": 1, "bsc": [0, 2, 4, 5, 7, 9, 11, 12], "bass": [0, 12, 0, 7, 0, 12, 0, 7, 5, 12, 5, 7, 7, 12, 7, 11]},
    "heart": {"et": .42, "bt": .15, "sc": [0, 2, 3, 5, 7, 8, 11, 12], "lead": "sawtooth", "ld": .6, "lv": .03, "lp": .26, "cut": 900,
              "drums": 1, "bsc": [0, 1, 3, 5, 7, 8, 11, 12], "bass": [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, -1, 0, -2, 0]},
    "grotto": {"et": .46, "bt": .16, "sc": [0, 2, 4, 7, 9, 12, 14], "lead": "sine", "ld": 2, "lv": .07, "lp": .3, "bell": .2,
               "bsc": [0, 2, 4, 7, 9, 12, 14], "bass": [0, 0, 7, 0, 0, 0, 4, 0, 0, 0, 7, 0, 9, 0, 7, 0], "bbell": 1},
}
# our places, in ClaudeRPG's music: (style, root) - the town and the forest in its own surface style and keys
PLACES = {
    "title": (None, 52), "town": (None, 52), "forest": ("grotto", 50),
    0: ("undercroft", 45), 1: ("grotto", 50), 2: ("sunken", 43), 3: ("undercroft", 47), 4: ("frozen", 52),
    5: ("city", 48), 6: ("grotto", 49), 7: ("heart", 47), 8: ("sunken", 45), 9: ("heart", 43),
}


def mf(n):
    return 440.0 * 2 ** ((n - 69) / 12)


class Synth:
    def __init__(self, rate=32000, seed=None):
        self.rate = rate
        self.rng = random.Random(seed)
        self.pos = 0                                   # samples made so far
        self.next = int(0.3 * rate)                    # when the next step falls
        self.step = 0
        self.mode = "explore"
        self.style = None
        self.root = 45
        self.voices = []                               # [start, n, f, wave, vol, wet, cut, kind]
        self.volume = 1.0
        # the drone: three detuned saws (0, a fifth, an octave down), through a resonant lowpass the LFO breathes
        self.drone_iv = [0, 7, -12]
        self.drone_f = [mf(self.root - 12 + iv) for iv in self.drone_iv]
        self.drone_ph = [0.0, 0.0, 0.0]
        self.drone_gain = 0.1
        self.lfo_ph = 0.0
        # the echo: 0.42 s, fed back at 0.38 through a lowpass
        self.delay = np.zeros(int(0.42 * rate), np.float32)
        self.dpos = 0
        self.lp_tail = np.zeros(7, np.float32)
        nrng = np.random.default_rng(seed)
        self.noise = nrng.uniform(-1, 1, rate).astype(np.float32)
        self._nz_cache = {}

    # ---- what the game sets --------------------------------------------------------------------------------------
    def set_style(self, style, root):
        self.style = STYLES.get(style) if style else None
        self.root = root

    def set_mode(self, mode):
        self.mode = mode
        self.target_drone = 0.15 if mode == "boss" else 0.1

    def place(self, key, boss=False):
        style, root = PLACES.get(key, (None, 52))
        if (self.style is not STYLES.get(style or "")) or self.root != root:
            self.set_style(style, root)
        self.set_mode("boss" if boss else "explore")

    # ---- the sequencer (ClaudeRPG's playStep, and its worlds' version of it) ------------------------------------
    def _step_len(self):
        S = self.style
        if self.mode == "boss":
            return S["bt"] if S else 0.16
        return S["et"] if S else 0.42

    def _pick(self, seq):
        return seq[self.rng.randrange(len(seq))]

    def _play_step(self, s, t):
        r, S = self.root, self.style
        note, kick, nz = self._note, self._kick, self._nz
        if S is None:                                   # ClaudeRPG's own
            if self.mode != "boss":
                sc = [0, 3, 5, 7, 10, 12, 15, 17]
                if s % 16 == 0:
                    note(mf(r - 12), t, 3.2, "triangle", .2, False)
                if s % 16 == 8:
                    note(mf(r - 12 + (7 if self.rng.random() < .5 else 5)), t, 3.2, "triangle", .16, False)
                if self.rng.random() < .3:
                    note(mf(r + 12 + self._pick(sc)), t, 1.6, "sine", .09, True)
                if self.rng.random() < .06:
                    note(mf(r + 24 + self._pick(sc)), t, 2.4, "triangle", .04, True)
            else:
                sc = [0, 2, 3, 5, 7, 8, 11, 12, 14, 15]
                bass = [0, 0, 12, 0, 0, 0, 3, 0, 0, 0, 12, 0, -2, 0, -1, 0]
                if s % 2 == 0:
                    note(mf(r - 12 + bass[s % 16]), t, .16, "sawtooth", .13, False, 700)
                if s % 4 == 0:
                    kick(t)
                if s % 2 == 1:
                    nz(t, .04, .05, "highpass", 7000)
                if s % 8 == 4:
                    nz(t, .12, .12, "bandpass", 1500)
                if self.rng.random() < .3:
                    note(mf(r + 12 + self._pick(sc)), t, .3, "square", .035, True, 2200)
            return
        sc = S["sc"]
        if self.mode != "boss":
            if S.get("waltz"):
                b = s % 6
                if b == 0:
                    note(mf(r - 12), t, .55, "triangle", .18, False)
                if b == 3:
                    note(mf(r - 12 + 7), t, .55, "triangle", .14, False)
                if b % 3:
                    note(mf(r + sc[2]), t, .16, "square", .022, False, 1400)
                    note(mf(r + sc[4]), t, .16, "square", .018, False, 1400)
                if S.get("tick"):
                    nz(t, .015, .035, "highpass", 6500)
                if self.rng.random() < S["lp"]:
                    note(mf(r + 12 + self._pick(sc)), t, S["ld"], S["lead"], S["lv"], True, S.get("cut"))
                return
            if s % 16 == 0:
                note(mf(r - 12), t, 3.2, "triangle", .2, False)
            if s % 16 == 8:
                note(mf(r - 12 + (5 if S.get("swell") else 7)), t, 3.2, "triangle", .16, False)
            if S.get("swell") and s % 32 == 16:
                note(mf(r - 24), t, 5, "sine", .15, True)
            if S.get("drums"):
                if s % 8 == 0:
                    kick(t)
                if s % 8 == 6 and self.rng.random() < .5:
                    kick(t)
            if self.rng.random() < S["lp"]:
                note(mf(r + 12 + self._pick(sc)), t, S["ld"], S["lead"], S["lv"], True, S.get("cut"))
            if S.get("bell") and self.rng.random() < S["bell"]:
                f = mf(r + 24 + self._pick(sc))
                note(f, t, 2.8, "sine", .05, True)
                note(f * 2.01, t, 1.2, "sine", .014, True)
        else:
            bsc, bass = S["bsc"], S["bass"]
            if s % 2 == 0:
                note(mf(r - 12 + bass[s % 16]), t, .16, "sawtooth", .13, False, 700)
            if s % 4 == 0:
                kick(t)
            if S.get("drums") and s % 8 == 3:
                kick(t)
            if s % 2 == 1:
                nz(t, .04, .05, "highpass", 7000)
            if s % 8 == 4:
                nz(t, .12, .12, "bandpass", 3200 if S.get("tick") else 1500)
            if S.get("tick") and s % 2 == 0:
                nz(t, .012, .04, "highpass", 9000)
            if self.rng.random() < .3:
                note(mf(r + 12 + self._pick(bsc)), t, .3, "square", .035, True, 2200)
            if S.get("bbell") and s % 8 == 0:
                note(mf(r + 24 + self._pick(bsc)), t, 1.2, "sine", .05, True)
            if S.get("swell") and s % 16 == 0:
                note(mf(r - 24), t, 2, "sine", .14, True)

    def _note(self, f, t, dur, wave, vol, wet, cut=None):
        self.voices.append([t, int(dur * self.rate) + 1, f, wave, vol, wet, cut, "note", dur])

    def _kick(self, t):
        self.voices.append([t, int(0.25 * self.rate), 0, "kick", .35, False, None, "kick", 0.25])

    def _nz(self, t, dur, vol, ftype, freq):
        self.voices.append([t, int(dur * self.rate) + 1, freq, ftype, vol, False, None, "noise", dur])

    # ---- making the sound --------------------------------------------------------------------------------------
    def _wave(self, wave, f, t, cut):
        ph = 2 * np.pi * f * t
        if wave == "sine":
            return np.sin(ph)
        if wave == "triangle":
            return 2 / np.pi * np.arcsin(np.sin(ph))
        top = min(self.rate / 2.2, cut or self.rate / 2.2)
        n = max(1, min(14, int(top / max(f, 1))))
        out = np.zeros_like(t)
        for k in range(1, n + 1):
            if wave == "square" and k % 2 == 0:
                continue
            out += np.sin(k * ph) / k
        return out * (4 / np.pi if wave == "square" else 2 / np.pi)

    def _filtered_noise(self, ftype, freq):
        key = (ftype, int(freq))
        if key not in self._nz_cache:
            spec = np.fft.rfft(self.noise)
            fr = np.fft.rfftfreq(len(self.noise), 1 / self.rate)
            if ftype == "highpass":
                spec[fr < freq] = 0
            else:
                spec *= np.exp(-((np.log2(np.maximum(fr, 1) / freq)) ** 2) / 0.18)
            x = np.fft.irfft(spec, len(self.noise)).astype(np.float32)
            self._nz_cache[key] = x / (np.abs(x).max() or 1)
        return self._nz_cache[key]

    def render(self, n):
        rate = self.rate
        start, end = self.pos, self.pos + n
        # the sequencer, a little ahead
        while self.next < end:
            self._play_step(self.step, self.next)
            self.next += int(self._step_len() * rate)
            self.step += 1
        dry = np.zeros(n, np.float32)
        wet = np.zeros(n, np.float32)
        keep = []
        for v in self.voices:
            t0, length, f, wave, vol, w, cut, kind, dur = v
            a, b = max(t0, start), min(t0 + length, end)
            if b <= start:
                if t0 + length > start:
                    keep.append(v)
                continue
            if a >= end:
                keep.append(v)
                continue
            idx = np.arange(a, b)
            t = (idx - t0) / rate
            if kind == "note":
                att = min(0.04, dur * 0.2)
                env = np.where(t < att, vol * t / att, vol * (0.0005 / vol) ** ((t - att) / max(1e-3, dur - att)))
                sig = self._wave(wave, f, t, cut) * env
            elif kind == "kick":
                k = 40 / 130
                ph = 2 * np.pi * 130 * 0.15 / math.log(k) * (k ** (np.minimum(t, 0.15) / 0.15) - 1) + \
                    2 * np.pi * 40 * np.maximum(t - 0.15, 0)
                sig = np.sin(ph) * 0.35 * (0.001 / 0.35) ** (t / 0.2)
            else:
                src = self._filtered_noise(wave, f)
                off = (t0 * 7919) % (len(src) - length - 1)
                sig = src[off + (idx - t0)] * vol * (0.001 / vol) ** (t / dur)
            dry[a - start:b - start] += sig
            if w:
                wet[a - start:b - start] += sig
            if t0 + length > end:
                keep.append(v)
        self.voices = keep
        # the echo
        D = len(self.delay)
        i = (self.dpos + np.arange(n)) % D
        delayed = self.delay[i]
        k = len(self.lp_tail)
        both = np.concatenate([self.lp_tail, delayed])
        echo = np.convolve(both, np.ones(k + 1, np.float32) / (k + 1), "valid")[-n:]
        self.lp_tail = delayed[-k:].copy() if n >= k else np.concatenate([self.lp_tail, delayed])[-k:]
        self.delay[i] = wet + echo * 0.38
        self.dpos = (self.dpos + n) % D
        # the drone
        drone = np.zeros(n, np.float32)
        tt = np.arange(n) / rate
        self.drone_gain += (getattr(self, "target_drone", 0.1) - self.drone_gain) * min(1.0, n / rate * 2)
        cutoff = 320 + 160 * math.sin(self.lfo_ph)
        self.lfo_ph += 2 * math.pi * 0.07 * n / rate
        for j, iv in enumerate(self.drone_iv):
            target = mf(self.root - 12 + iv) * 2 ** ((j - 1) * 7 / 1200)
            self.drone_f[j] += (target - self.drone_f[j]) * min(1.0, n / rate / 0.8)
            f = self.drone_f[j]
            ph0 = self.drone_ph[j]
            for h in range(1, int(cutoff * 2.2 / f) + 1):
                x = h * f / cutoff
                mag = 1 / math.sqrt((1 - x * x) ** 2 + (x / 3) ** 2)
                drone += (mag / h) * np.sin(h * (ph0 + 2 * np.pi * f * tt)) * 0.45
            self.drone_ph[j] = (ph0 + 2 * math.pi * f * n / rate) % (2 * math.pi)
        self.pos = end
        mus = (dry + echo + drone * self.drone_gain) * 0.3 * self.volume
        return np.clip(mus * 0.7 * 2.2, -1, 1).astype(np.float32)
