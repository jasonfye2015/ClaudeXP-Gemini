"""Claudeatro's soundscape: chiptune blips for everything that happens, and a lounge-y retro synth loop in three
moods - the table, the shop and a boss - that crossfade as the run moves on.

All of it is synthesized here (organ chords, a walking bass, a wobbly lead with an echo, soft drums), written once to
this computer's data folder, and played from there. The music is built on a background thread the first time."""
import math
import random
import threading
import wave
from array import array

from PySide6.QtCore import QUrl

from claudecore import host

RATE = 22050
VERSION = "v1"
MOODS = ("main", "shop", "boss")
MUSIC_VOLUME = 0.32
SFX_VOLUME = 0.5
BPM = 100
BEAT = 60 / BPM
BAR = BEAT * 4
BARS = 16
SIZE = 1024


def midi(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def _table(harmonics):
    t = [sum(a * math.sin(2 * math.pi * h * i / SIZE) for h, a in harmonics) for i in range(SIZE)]
    peak = max(abs(x) for x in t)
    return [x / peak for x in t]


SINE = _table([(1, 1)])
ORGAN = _table([(1, 1), (2, 0.55), (3, 0.3), (4, 0.12), (6, 0.06)])
TRI = [1 - 4 * abs(i / SIZE - 0.5) for i in range(SIZE)]
PULSE = [1.0 if i < SIZE // 4 else -1.0 for i in range(SIZE)]
SQUARE = [1.0 if i < SIZE // 2 else -1.0 for i in range(SIZE)]


def note(buf, start, dur, freq, vol, table, attack=0.01, release=0.08, vib=0.0, vib_rate=5.5, trem=0.0,
         trem_rate=6.0, slide=None, wrap=True):
    """Add one note to a buffer. (With wrap, a tail past the end comes round to the start, so loops are seamless.)"""
    n_total = len(buf)
    i0 = int(start * RATE)
    n = int((dur + release) * RATE)
    inc = freq * SIZE / RATE
    inc2 = (slide if slide else freq) * SIZE / RATE
    phase = 0.0
    sine = SINE
    att = max(1, int(attack * RATE))
    hold = int(dur * RATE)
    rel = max(1, int(release * RATE))
    vstep = vib_rate * SIZE / RATE
    tstep = trem_rate * SIZE / RATE
    for k in range(n):
        idx = i0 + k
        if idx >= n_total:
            if not wrap:
                break
            idx %= n_total
        if k < att:
            env = k / att
        elif k > hold:
            env = 1 - (k - hold) / rel
        else:
            env = 1.0
        f = inc + (inc2 - inc) * (k / n) if slide else inc
        if vib:
            f *= 1 + vib * sine[int(k * vstep) & 1023]
        phase = (phase + f) % SIZE
        s = table[int(phase)] * env * vol
        if trem:
            s *= 1 - trem * (0.5 + 0.5 * sine[int(k * tstep) & 1023])
        buf[idx] += s


def noise(buf, rng, start, dur, vol, decay=30.0, smooth=0.0, wrap=True):
    """A burst of noise that dies away (smooth > 0 darkens it)."""
    n_total = len(buf)
    i0 = int(start * RATE)
    n = int(dur * RATE)
    y = 0.0
    for k in range(n):
        idx = i0 + k
        if idx >= n_total:
            if not wrap:
                break
            idx %= n_total
        x = rng.uniform(-1, 1)
        y = y + (1 - smooth) * (x - y) if smooth else x
        buf[idx] += y * vol * math.exp(-decay * k / RATE)


def kick(buf, start, vol, wrap=True):
    n_total = len(buf)
    i0 = int(start * RATE)
    phase = 0.0
    for k in range(int(0.22 * RATE)):
        t = k / RATE
        f = 45 + 110 * math.exp(-t * 28)
        phase += 2 * math.pi * f / RATE
        idx = i0 + k
        if idx >= n_total:
            if not wrap:
                break
            idx %= n_total
        buf[idx] += math.sin(phase) * vol * math.exp(-t * 14)


def echo(buf, delay, feedback):
    d = int(delay * RATE)
    n = len(buf)
    for i in range(n):
        buf[i] += buf[(i - d) % n] * feedback


def lowpass(buf, a):
    y = buf[-1]
    for i in range(len(buf)):
        y += a * (buf[i] - y)
        buf[i] = y


def to_wav(path, buf, peak_to=0.82):
    peak = max(1e-6, max(abs(x) for x in buf))
    k = peak_to * 32767 / peak
    data = array("h", (int(x * k) for x in buf))
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with wave.open(str(tmp), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(data.tobytes())
    tmp.replace(path)


# ---- the music -----------------------------------------------------------------------------------------------------
# a lounge progression in D minor: (bass root, organ chord) per bar
CHORDS = [(38, (53, 57, 60, 64)),      # Dm9
          (38, (53, 57, 59, 64)),      # Dm6/9
          (34, (53, 57, 62, 65)),      # Bbmaj7
          (33, (55, 58, 61, 64)),      # A7b9
          (31, (53, 57, 58, 62)),      # Gm9
          (36, (52, 55, 58, 62)),      # C9
          (29, (53, 57, 60, 64)),      # Fmaj7
          (33, (55, 57, 61, 65))]      # A7#5
# (beat, beats long, note) per bar; the second eight bars answer the first
MELODY = [[(0, 1.5, 81), (1.5, 0.5, 79), (2, 2, 77)],
          [(0.5, 0.5, 74), (1, 0.5, 77), (1.5, 0.5, 79), (2, 1.5, 81), (3.5, 0.5, 84)],
          [(0, 2, 81), (2, 1, 79), (3, 1, 77)],
          [(0, 3, 76), (3, 0.5, 77), (3.5, 0.5, 79)],
          [(0, 1.5, 77), (1.5, 0.5, 74), (2, 2, 70)],
          [(0, 1, 72), (1, 1, 76), (2, 2, 79)],
          [(0, 1.5, 81), (1.5, 0.5, 79), (2, 1, 76), (3, 1, 72)],
          [(0, 2, 73), (2, 2, 76)],
          [(0, 0.5, 86), (0.5, 0.5, 84), (1, 1, 81), (2, 1, 79), (3, 1, 77)],
          [(0, 2, 74), (2.5, 0.5, 77), (3, 0.5, 79), (3.5, 0.5, 81)],
          [(0, 1.5, 82), (1.5, 0.5, 81), (2, 2, 77)],
          [(0, 1, 79), (1, 1, 76), (2, 2, 73)],
          [(0, 1, 74), (1, 1, 77), (2, 1, 82), (3, 1, 81)],
          [(0, 3, 79), (3, 1, 76)],
          [(0, 1, 77), (1, 1, 76), (2, 1, 72), (3, 1, 69)],
          [(0, 2, 76), (2, 2, 73)]]
SWING = 0.62            # (where the offbeat falls: a lazy swing)


def render(mood):
    n = int(BAR * BARS * RATE)
    pad, bass, lead, drums = (array("f", bytes(4 * n)) for _ in range(4))
    rng = random.Random(7)
    cache = {}
    for b in range(BARS):
        root, chord = CHORDS[b % 8]
        t0 = b * BAR
        # the organ: one rendering per chord, reused
        key = (root, chord)
        if key not in cache:
            seg = array("f", bytes(4 * int((BAR + 0.4) * RATE)))
            low = -12 if mood == "boss" else 0
            for m in chord:
                note(seg, 0, BAR - 0.05, midi(m + low), 0.16, ORGAN, attack=0.18, release=0.35, vib=0.002,
                     trem=0.35 if mood != "boss" else 0.5, trem_rate=5.8 if mood != "boss" else 8.0, wrap=False)
                if mood == "boss":                  # a detuned twin, for an uneasy beating
                    note(seg, 0, BAR - 0.05, midi(m + low) * 1.006, 0.1, ORGAN, attack=0.3, release=0.35, wrap=False)
            cache[key] = seg
        seg = cache[key]
        i0 = int(t0 * RATE)
        for k in range(len(seg)):
            pad[(i0 + k) % n] += seg[k]
        # the bass
        nxt = CHORDS[(b + 1) % 8][0]
        if mood == "boss":
            for e in range(8):
                note(bass, t0 + e * BEAT / 2, BEAT / 2 - 0.04, midi(root), 0.34, TRI, release=0.04)
        else:
            steps = [(0, 1.4, root), (1.5 if mood == "shop" else 2, 1.3, root + 7), (3, 0.6, root + 12),
                     (3 + SWING, 0.36, nxt + (1 if nxt < root else -1))]
            for beat, length, m in steps:
                note(bass, t0 + beat * BEAT, length * BEAT, midi(m), 0.36, TRI, attack=0.005, release=0.06)
                note(bass, t0 + beat * BEAT, length * BEAT * 0.5, midi(m), 0.05, SQUARE, release=0.03)
        # the lead
        if mood == "main":
            for beat, length, m in MELODY[b]:
                note(lead, t0 + beat * BEAT, length * BEAT * 0.92, midi(m), 0.13, PULSE, attack=0.02, release=0.12,
                     vib=0.006, vib_rate=5.2)
        elif mood == "shop":                        # a busier arpeggio, up high
            tones = sorted(chord)
            for e in range(8):
                m = tones[[0, 1, 2, 3, 2, 1, 3, 2][e]] + 12
                beat = e // 2 + (SWING if e % 2 else 0)
                note(lead, t0 + beat * BEAT, BEAT * 0.3, midi(m), 0.09, PULSE, release=0.08, vib=0.004)
        else:                                       # a few low, ominous notes
            beat, length, m = MELODY[b][0]
            note(lead, t0 + beat * BEAT, length * BEAT, midi(m - 24), 0.16, SQUARE, attack=0.05, release=0.3,
                 vib=0.01, vib_rate=3.0)
        # the drums
        beats = range(4) if mood == "boss" else (0, 2)
        for beat in beats:
            kick(drums, t0 + beat * BEAT, 0.5)
        if mood != "boss":
            for beat in (1, 3):
                noise(drums, rng, t0 + beat * BEAT, 0.16, 0.12 if mood == "shop" else 0.08, decay=24, smooth=0.55)
            for beat in range(4):
                if mood == "shop":
                    noise(drums, rng, t0 + beat * BEAT, 0.04, 0.05, decay=90)
                noise(drums, rng, t0 + (beat + SWING) * BEAT, 0.05, 0.06, decay=80)
        else:
            if b % 2 == 1:
                noise(drums, rng, t0 + 3.5 * BEAT, 0.5, 0.06, decay=6, smooth=0.9)
    echo(lead, BEAT * 0.75, 0.38)
    lowpass(lead, 0.45)
    lowpass(pad, 0.5)
    mix = array("f", (pad[i] + bass[i] + lead[i] + drums[i] for i in range(n)))
    lowpass(mix, 0.7)
    return mix


def make_music(folder):
    paths = {}
    for mood in MOODS:
        path = folder / f"music-{mood}.wav"
        if not path.exists():
            to_wav(path, render(mood), 0.8)
        paths[mood] = path
    return paths


# ---- the sound effects ------------------------------------------------------------------------------------------
def _fx(seconds):
    return array("f", bytes(4 * int(seconds * RATE)))


def make_sfx(folder):
    rng = random.Random(3)
    out = {}

    def save(name, buf):
        path = folder / f"{name}.wav"
        out[name] = path
        if not path.exists():
            to_wav(path, buf, 0.7)

    b = _fx(0.06)
    note(b, 0, 0.035, 1180, 0.5, TRI, slide=1560, release=0.02, wrap=False)
    save("select", b)
    b = _fx(0.06)
    note(b, 0, 0.035, 980, 0.5, TRI, slide=760, release=0.02, wrap=False)
    save("deselect", b)
    b = _fx(0.03)
    note(b, 0, 0.012, 1600, 0.4, SQUARE, release=0.01, wrap=False)
    save("click", b)
    for k in range(12):                             # the chips, climbing a scale as a hand scores
        b = _fx(0.12)
        f = midi(72 + [0, 2, 4, 5, 7, 9, 11, 12, 14, 16, 17, 19][k])
        note(b, 0, 0.05, f, 0.45, TRI, release=0.05, wrap=False)
        note(b, 0, 0.03, f * 2, 0.15, SQUARE, release=0.03, wrap=False)
        save(f"chips{k}", b)
    b = _fx(0.16)
    note(b, 0, 0.08, 240, 0.6, SQUARE, slide=150, release=0.05, wrap=False)
    noise(b, rng, 0, 0.03, 0.25, decay=120, wrap=False)
    save("mult", b)
    b = _fx(0.45)
    for f, v in ((880, 0.4), (880 * 2.76, 0.15), (1320, 0.25)):
        note(b, 0, 0.02, f, v, SINE, release=0.4, wrap=False)
    save("xmult", b)
    b = _fx(0.3)
    note(b, 0, 0.06, 988, 0.4, SQUARE, release=0.0, wrap=False)
    note(b, 0.06, 0.15, 1319, 0.4, SQUARE, release=0.06, wrap=False)
    save("money", b)
    b = _fx(0.14)
    note(b, 0, 0.09, 420, 0.5, TRI, slide=860, release=0.04, vib=0.03, vib_rate=30, wrap=False)
    save("joker", b)
    b = _fx(0.32)
    noise(b, rng, 0, 0.3, 0.5, decay=16, wrap=False)
    for k, f in enumerate((3100, 2600, 3700, 2900)):
        note(b, 0.02 + k * 0.05, 0.01, f, 0.18, SINE, release=0.12, wrap=False)
    save("glass", b)
    b = _fx(0.32)
    noise(b, rng, 0, 0.28, 0.3, decay=10, smooth=0.85, wrap=False)
    note(b, 0, 0.2, 300, 0.25, TRI, slide=640, release=0.06, wrap=False)
    save("play", b)
    b = _fx(0.2)
    noise(b, rng, 0, 0.18, 0.35, decay=14, smooth=0.7, wrap=False)
    note(b, 0, 0.12, 520, 0.15, TRI, slide=260, release=0.05, wrap=False)
    save("discard", b)
    b = _fx(0.45)
    kick(b, 0, 0.8, wrap=False)
    for m in (62, 65, 69, 72):
        note(b, 0, 0.18, midi(m), 0.12, ORGAN, release=0.2, wrap=False)
    save("total", b)
    b = _fx(0.75)
    for k, m in enumerate((72, 76, 79, 84, 88)):
        note(b, k * 0.08, 0.1 if k < 4 else 0.3, midi(m), 0.32, PULSE, release=0.1, wrap=False)
    save("win", b)
    b = _fx(1.1)
    for k, m in enumerate((67, 64, 60, 55)):
        note(b, k * 0.2, 0.18 if k < 3 else 0.5, midi(m), 0.4, TRI, release=0.15, vib=0.01 if k == 3 else 0,
             wrap=False)
    save("lose", b)
    b = _fx(0.5)
    noise(b, rng, 0, 0.04, 0.4, decay=60, wrap=False)
    note(b, 0.03, 0.05, 1568, 0.3, SQUARE, release=0.0, wrap=False)
    note(b, 0.08, 0.02, 2093, 0.3, SINE, release=0.35, wrap=False)
    note(b, 0.08, 0.02, 2093 * 2.76, 0.08, SINE, release=0.25, wrap=False)
    save("buy", b)
    b = _fx(0.36)
    for k in range(7):
        noise(b, rng, k * 0.045, 0.03, 0.35, decay=120, wrap=False)
    save("reroll", b)
    b = _fx(0.32)
    n = int(0.28 * RATE)
    y = 0.0
    for k in range(n):                              # a rip: noise that brightens as it tears
        a = 0.05 + 0.9 * k / n
        y += a * (rng.uniform(-1, 1) - y)
        b[k] += y * 0.6 * (1 - k / n) ** 0.5
    save("pack", b)
    b = _fx(0.5)
    for k, m in enumerate((84, 91, 88, 96, 93, 100)):
        note(b, k * 0.05, 0.02, midi(m), 0.16, SINE, release=0.2, wrap=False)
    save("tarot", b)
    b = _fx(0.55)
    note(b, 0, 0.42, 220, 0.4, TRI, slide=1250, release=0.1, vib=0.02, vib_rate=9, wrap=False)
    save("planet", b)
    b = _fx(0.28)
    note(b, 0, 0.06, 1319, 0.35, SQUARE, release=0.0, wrap=False)
    note(b, 0.06, 0.14, 988, 0.35, SQUARE, release=0.05, wrap=False)
    save("sell", b)
    b = _fx(0.6)
    kick(b, 0, 0.7, wrap=False)
    for m in (50, 57, 62):
        note(b, 0, 0.3, midi(m), 0.15, ORGAN, attack=0.02, release=0.25, wrap=False)
    save("blind", b)
    b = _fx(0.2)
    note(b, 0, 0.12, 130, 0.4, SQUARE, release=0.05, wrap=False)
    note(b, 0, 0.12, 138, 0.3, SQUARE, release=0.05, wrap=False)
    save("nope", b)
    b = _fx(0.8)
    noise(b, rng, 0, 0.05, 0.4, decay=50, wrap=False)
    for k, m in enumerate((79, 84, 88, 91)):
        note(b, 0.05 + k * 0.06, 0.04, midi(m), 0.25, SQUARE, release=0.04, wrap=False)
    note(b, 0.3, 0.02, 2349, 0.3, SINE, release=0.45, wrap=False)
    save("cashout", b)
    return out


# ---- playing it -------------------------------------------------------------------------------------------------
class Audio:
    """The sound effects (QSoundEffect) and three music players kept in step, faded in and out by mood."""

    def __init__(self, parent, music=True, sfx=True):
        self.parent = parent
        self.music_on = music
        self.sfx_on = sfx
        self.mood = "main"
        self.fx = {}
        self.players = {}
        self.outputs = {}
        self.volume = {m: 0.0 for m in MOODS}
        self.paths = None
        self.closed = False
        self.failed = False
        self.folder = host.data("claudeatro") / f"sounds-{VERSION}"
        try:
            from PySide6.QtMultimedia import QSoundEffect
            for name, path in make_sfx(self.folder).items():
                fx = QSoundEffect(parent)
                fx.setSource(QUrl.fromLocalFile(str(path)))
                fx.setVolume(SFX_VOLUME)
                self.fx[name] = fx
        except Exception:
            self.fx = {}
        threading.Thread(target=self._build, daemon=True).start()

    def _build(self):
        try:
            self.paths = make_music(self.folder)
        except Exception:
            self.failed = True

    def _start_music(self):
        try:
            from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
            for m in MOODS:
                out = QAudioOutput(self.parent)
                out.setVolume(0.0)
                pl = QMediaPlayer(self.parent)
                pl.setAudioOutput(out)
                pl.setSource(QUrl.fromLocalFile(str(self.paths[m])))
                pl.setLoops(-1)
                self.outputs[m] = out
                self.players[m] = pl
            for pl in self.players.values():           # (all three together, so they stay in step)
                pl.play()
        except Exception:
            self.failed = True

    def tick(self, dt):
        if self.closed or self.failed:
            return
        if self.paths and not self.players:
            self._start_music()
            return
        if not self.players:
            return
        on = self.music_on and not host.muted()
        step = dt / 1.4 * MUSIC_VOLUME
        for m, out in self.outputs.items():
            want = MUSIC_VOLUME if on and m == self.mood else 0.0
            v = self.volume[m]
            v = min(want, v + step) if want > v else max(want, v - step)
            if v != self.volume[m]:
                self.volume[m] = v
                out.setVolume(v)

    def play(self, name):
        if not self.sfx_on or self.closed or host.muted():
            return
        fx = self.fx.get(name)
        if fx is not None:
            fx.play()

    def chips(self, k):
        self.play(f"chips{min(11, k)}")

    def stop(self):
        self.closed = True
        for pl in self.players.values():
            pl.stop()
        for fx in self.fx.values():
            fx.stop()
