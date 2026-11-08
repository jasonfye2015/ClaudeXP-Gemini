"""The score (phase 5): made as it plays, plain numpy - the game's own, a sweeping, eerie voice.

    exploring    a low drone; sparse harp and bell plucks falling like drips in a cave; long silences between
    her scenes   a slow waltz in three, slightly out of true: courtship and dread keeping the same time
    the crown    the waltz opened out - strings over the drone - the one time the music lets itself be beautiful
    endings      each its own short coda; Supper ends in silence

It follows her moods:
    hunger rising         a heartbeat pulse under the drone, quickening
    patience thinning     the melody drops notes, leaving gaps
    suspicion high        a second voice shadows the melody, a semitone wrong
    fascination high      the bells warm and slow; the waltz steadies
    venom                 the pitch bends and wavers

    music = Music(rate)
    music.set(mode, hunger=, patience=, suspicion=, fascination=, venom=)
        mode: "explore", "scene", "crown", "silence", or "coda:<ending>"
    music.render(n) -> float64 (n,)
"""
import math
import random

import numpy as np

D4 = 293.66
MINOR = (0, 2, 3, 5, 7, 8, 10)                       # (D natural minor: the scale the drips fall down)
# the waltz (original): (semitones from D4, beats) - None a rest - eight bars of three
WALTZ = ((7, 2), (5, 1), (3, 3), (7, 1), (8, 1), (7, 1), (2, 3),
         (0, 2), (2, 1), (3, 2), (7, 1), (12, 2), (10, 1), (9, 3),
         (10, 2), (8, 1), (7, 2), (5, 1), (3, 1), (2, 1), (0, 1), (1, 2), (None, 1),
         (2, 1), (3, 1), (5, 1), (7, 2), (3, 1), (2, 3), (0, 3))
CHORDS = ((0, 3, 7), (-4, 0, 3), (-7, -2, 2), (-5, -1, 2))   # (Dm, Bb, Gm, A: the bass under each two bars)


def _hz(semi, bend=1.0):
    return D4 * 2 ** (semi / 12) * bend


def _note(kind, hz, rate, gain=1.0, length=None, warm=0.0):
    """One note, made whole: harp (plucked), bell (struck, inharmonic), string (bowed), thump (a heartbeat)."""
    if kind == "harp":
        dur = length or 2.2
        t = np.arange(int(dur * rate)) / rate
        out = np.zeros_like(t)
        for k, a in ((1, 1.0), (2, 0.45), (3, 0.22), (4, 0.12), (5, 0.06)):
            out += a * np.sin(math.tau * hz * k * t) * np.exp(-t * (1.6 + 1.3 * k))
        out *= np.clip(t / 0.004, 0, 1)
    elif kind == "bell":
        dur = length or 4.5
        t = np.arange(int(dur * rate)) / rate
        out = np.zeros_like(t)
        bright = 1.0 - 0.6 * warm                                    # (warmer: the high partials softer, slower)
        for r, a, d in ((1.0, 1.0, 0.7), (2.0, 0.5, 1.0), (2.76, 0.4 * bright, 1.6), (5.4, 0.25 * bright, 2.6),
                        (8.93, 0.12 * bright, 4.0)):
            out += a * np.sin(math.tau * hz * r * t) * np.exp(-t * d * (1.0 - 0.35 * warm))
        out *= np.clip(t / 0.002, 0, 1)
    elif kind == "string":
        dur = length or 3.0
        t = np.arange(int(dur * rate)) / rate
        vib = 1.0 + 0.004 * np.sin(math.tau * 5.2 * t) * np.clip(t / 0.8, 0, 1)
        ph = np.cumsum(math.tau * hz * vib / rate)
        out = sum(a * np.sin(ph * k) for k, a in ((1, 1.0), (2, 0.5), (3, 0.3), (4, 0.18), (5, 0.1), (6, 0.05)))
        out *= np.clip(t / 0.6, 0, 1) * np.clip((dur - t) / 0.9, 0, 1)
        out *= 0.5
    else:                                                            # (thump: the heartbeat under it all)
        dur = 0.35
        t = np.arange(int(dur * rate)) / rate
        f = 52 * (1 + 0.6 * np.exp(-t * 30))
        out = np.sin(np.cumsum(math.tau * f / rate)) * np.exp(-t * 14)
    return out * gain


# each ending's own short coda: (seconds in, instrument, semitones from D4, gain, length)
CODAS = {
    "Dawn": [(0.0, "bell", 0, 0.5, 5), (0.9, "bell", 4, 0.45, 5), (1.8, "bell", 7, 0.45, 5), (2.7, "bell", 12, 0.5, 6),
             (2.7, "string", -12, 0.35, 6), (2.7, "string", -5, 0.25, 6)],
    "Cast out": [(0.0, "harp", 7, 0.45, 3), (1.6, "harp", 3, 0.4, 3), (3.4, "harp", 0, 0.35, 3),
                 (5.6, "harp", -5, 0.3, 4)],
    "Bound": [(0.0, "harp", -12, 0.5, 3), (0.9, "harp", 3, 0.25, 2), (1.8, "harp", 7, 0.25, 2),
              (3.0, "string", -12, 0.35, 7), (3.0, "string", 3, 0.25, 7), (3.0, "string", 7, 0.22, 7),
              (4.5, "bell", 15, 0.3, 5)],
    "The gift": [(0.0, "string", -12, 0.3, 8), (0.0, "string", -5, 0.25, 8), (1.0, "bell", 7, 0.4, 5),
                 (2.2, "bell", 14, 0.35, 5), (3.6, "bell", 19, 0.3, 6)],
    "The hidden": [(0.0, "string", -12, 0.3, 9), (0.0, "harp", 7, 0.4, 2), (0.8, "harp", 5, 0.35, 2),
                   (1.2, "harp", 3, 0.4, 3), (2.4, "harp", 7, 0.35, 2), (3.2, "harp", 8, 0.35, 2),
                   (4.0, "harp", 7, 0.35, 2), (4.8, "harp", 2, 0.4, 3), (6.0, "string", -3, 0.3, 6),
                   (6.0, "string", 6, 0.25, 6), (6.0, "bell", 18, 0.3, 6)],
    "Spellbound": [(0.0, "string", -12, 0.25, 9), (0.0, "string", -5, 0.2, 9), (0.6, "bell", 12, 0.3, 6),
                   (2.2, "bell", 10, 0.28, 6), (3.8, "bell", 7, 0.26, 6), (5.4, "bell", 5, 0.24, 7),
                   (7.0, "bell", 7, 0.22, 7)],
    "Fire": [(0.0, "bell", 0, 0.4, 3), (0.15, "bell", 1, 0.4, 3), (0.5, "bell", 6, 0.35, 3), (0.7, "bell", 7, 0.35, 3),
             (1.1, "bell", 13, 0.3, 3), (1.3, "string", -12, 0.4, 5), (1.3, "string", -11, 0.35, 5),
             (1.3, "string", -6, 0.3, 5)],
}


class Music:
    def __init__(self, rate, seed=3):
        self.rate = rate
        self.rng = random.Random(seed)
        self.mode = "explore"
        self.mood = {"hunger": 20.0, "patience": 70.0, "suspicion": 30.0, "fascination": 30.0, "venom": False}
        self.n = 0                       # (samples played so far)
        self.notes = []                  # [buffer, start sample]
        self.next = int(rate * 2.0)      # (when the next thing in the score happens)
        self.next_beat = 0
        self.bar = 0
        self.beat = 0
        self.mel = 0
        self.mel_left = 0
        self.drone, self._drone, self._dph = 0.6, 0.0, 0.0
        self.coda = None
        self._wob = 0.0
        self._made = {}                  # (each note's sound, made once)
        self._thump = _note("thump", 0, rate, 1.0)

    def ready(self):
        """The waltz's and the crown's notes, made ahead (so the first bar at the crown doesn't stall the sound)."""
        save = self.n
        for crown in (False, True):
            beat_s = 60.0 / (64 if crown else 70)
            for chord in CHORDS:
                self._add("harp", chord[0] - 24, 1.0, 0, 2.4)
                for c in chord[1:]:
                    self._add("harp", c - 12, 1.0, 0, 1.0)
                if crown:
                    for c in chord:
                        self._add("string", c - 12, 1.0, 0, beat_s * 3 + 0.8)
            for semi, beats in WALTZ:
                if semi is not None:
                    self._add("bell" if crown else "harp", semi + (12 if crown else 0), 1.0, 0, beats * beat_s + 1.0)
        self.notes = []
        self.n = save

    def set(self, mode, **mood):
        self.mood.update(mood)
        if mode != self.mode:
            self.mode = mode
            now = self.n
            if mode.startswith("coda:"):
                self.coda = mode[5:]
                self.notes = [x for x in self.notes if x[1] + len(x[0]) > now][:4]      # (what's ringing, rings on)
                for at, kind, semi, g, length in CODAS.get(self.coda, []):
                    self._add(kind, semi, g, now + int(at * self.rate), length)
            if mode in ("scene", "crown"):
                self.next_beat, self.bar, self.beat, self.mel, self.mel_left = now + int(self.rate * 0.6), 0, 0, 0, 0
            if mode == "explore":
                self.next = now + int(self.rate * self.rng.uniform(2, 5))

    # ---- what's played ------------------------------------------------------------------------------------------
    def _bend(self):
        return 1.0 + (0.025 * math.sin(self.n / self.rate * 1.3) + 0.012 * math.sin(self.n / self.rate * 3.7)
                      if self.mood.get("venom") else 0.0)

    def _add(self, kind, semi, gain, at, length=None, warm=0.0):
        bend = round(self._bend() / 0.004) * 0.004                   # (bent in small steps: so each is made once)
        key = (kind, semi, round(bend, 3), round(length or 0, 1), round(warm, 1))
        buf = self._made.get(key)
        if buf is None:
            buf = _note(kind, _hz(semi, bend), self.rate, 1.0, length, round(warm, 1))
            if len(self._made) > 500:
                self._made.clear()
            self._made[key] = buf
        self.notes.append([buf, at, gain])
        if len(self.notes) > 40:
            self.notes.pop(0)

    def _compose(self, until):
        rng, rate, m = self.rng, self.rate, self.mood
        fasc, warm = m["fascination"] / 100.0, max(0.0, (m["fascination"] - 50) / 50.0)
        if self.mode == "explore":                                  # (drips, falling, then a long silence)
            while self.next < until:
                at = self.next
                k = rng.choice(range(len(MINOR)))
                octave = rng.choice((0, 0, 12, -12))
                count = rng.choice((1, 1, 2, 3, 4))
                gap = rng.uniform(0.35, 0.8) * (1 + 0.6 * warm)
                for j in range(count):
                    semi = MINOR[(k - j) % 7] + octave - (12 if k - j < 0 else 0)
                    kind = "bell" if rng.random() < 0.35 + 0.4 * warm else "harp"
                    self._add(kind, semi, rng.uniform(0.16, 0.26), at + int(j * gap * rate), warm=warm)
                self.next = at + int((count * gap + rng.uniform(4.0, 11.0) * (1 + 0.3 * warm)) * rate)
        elif self.mode in ("scene", "crown"):                       # (the waltz, in three)
            crown = self.mode == "crown"
            beat_s = 60.0 / (64 if crown else 70)
            out_of_true = 0.05 * (1.0 - fasc) + 0.008                # (steadier, the more she's taken with him)
            drop = max(0.0, (55 - m["patience"]) / 70.0)
            shadow = max(0.0, (m["suspicion"] - 55) / 45.0)
            while self.next_beat < until:
                at = self.next_beat + int(rng.gauss(0, out_of_true) * rate)
                chord = CHORDS[(self.bar // 2) % len(CHORDS)]
                if self.beat == 0:
                    self._add("harp", chord[0] - 24, 0.32, at, 2.4)
                    if crown:
                        for j, c in enumerate(chord):
                            self._add("string", c - 12, 0.13 - 0.02 * j, at, beat_s * 3 + 0.8)
                else:
                    for c in chord[1:]:
                        self._add("harp", c - 12, 0.1, at + int(rng.uniform(0, 0.02) * rate), 1.0)
                if self.mel_left <= 0:                              # (the melody: a note, or a gap where one was)
                    semi, beats = WALTZ[self.mel % len(WALTZ)]
                    self.mel += 1
                    self.mel_left = beats
                    if semi is not None and rng.random() >= drop:
                        kind = "bell" if crown or warm > 0.3 else "harp"
                        self._add(kind, semi + (12 if crown else 0), 0.26 if crown else 0.22, at,
                                  beats * beat_s + 1.0, warm=warm)
                        if shadow > 0:                              # (a second voice, a semitone wrong, a moment late)
                            self._add("harp", semi + 1, 0.16 * shadow, at + int(0.11 * rate), beats * beat_s + 0.6)
                self.mel_left -= 1
                self.beat = (self.beat + 1) % 3
                if self.beat == 0:
                    self.bar += 1
                self.next_beat += int(beat_s * rate)

    def _pulse(self, until):
        """Her hunger: a heartbeat under the drone, quickening."""
        h = self.mood["hunger"]
        if h < 45 or self.mode.startswith("coda") or self.mode == "silence":
            return
        bpm = 48 + (h - 45) * 1.1
        period = int(60.0 / bpm * self.rate)
        if not hasattr(self, "_next_pulse") or self._next_pulse < self.n - period:
            self._next_pulse = self.n
        while self._next_pulse < until:
            g = 0.18 * min(1.0, (h - 45) / 30.0)
            self.notes.append([self._thump, self._next_pulse, g])
            self.notes.append([self._thump, self._next_pulse + int(0.24 * self.rate), g * 0.6])
            self._next_pulse += period

    def render(self, n):
        rate = self.rate
        until = self.n + n
        if self.mode != "silence" and not self.mode.startswith("coda"):
            self._compose(until)
        self._pulse(until)
        out = np.zeros(n)
        # the drone: D and A, low, breathing; down to nothing for silence; for a coda, fading
        want = {"explore": 0.6, "scene": 0.4, "crown": 0.7, "silence": 0.0}.get(self.mode, 0.25)
        if self.coda in ("Supper", "Cast out") and self.mode.startswith("coda"):
            want = 0.0
        d0, self._drone = self._drone, self._drone + (want - self._drone) * 0.03
        if d0 > 1e-4 or self._drone > 1e-4:
            t = (self.n + np.arange(n)) / rate
            bend = np.full(n, self._bend())
            ph = self._dph + np.cumsum(math.tau * 73.42 * bend / rate)
            self._dph = float(ph[-1]) % (math.tau * 1000)
            swell = 0.75 + 0.25 * np.sin(math.tau * t / 13.0)
            tone = (np.sin(ph) + 0.6 * np.sin(ph * 1.5) + 0.35 * np.sin(ph * 2.0) + 0.2 * np.sin(ph * 3.002)
                    + 0.12 * np.sin(ph * 0.5))
            out += tone * swell * np.linspace(d0, self._drone, n) * 0.05
        keep = []
        for note in self.notes:
            buf, at, g = note
            a, b = max(at, self.n), min(at + len(buf), until)
            if b > a:
                out[a - self.n:b - self.n] += buf[a - at:b - at] * g
            if at + len(buf) > until:
                keep.append(note)
        if self.mode == "silence":                                  # (Supper: everything let go)
            for note in keep:
                note[2] *= 0.97
        self.notes = keep
        self.n = until
        return out * 0.55
