"""ClaudePit's soundscape: the noises of the machine, the ATM, the phone and the trapdoor, and an uneasy loop at the
bottom of the pit - a low drone, a music box with an echo and a slow heartbeat - that turns to dread when a deadline is
close and the money isn't there.

All of it is synthesized here, written once to this computer's data folder and played from there. The music is built
on a background thread the first time."""
import math
import random
import threading
import wave
from array import array

from PySide6.QtCore import QUrl

from claudecore import host

RATE = 22050
VERSION = "v1"
MOODS = ("pit", "tension")
MUSIC_VOLUME = 0.34
SFX_VOLUME = 0.5
BPM = 66
BEAT = 60 / BPM
BAR = BEAT * 4
BARS = 8
SIZE = 1024


def midi(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def _table(harmonics):
    t = [sum(a * math.sin(2 * math.pi * h * i / SIZE) for h, a in harmonics) for i in range(SIZE)]
    peak = max(abs(x) for x in t)
    return [x / peak for x in t]


SINE = _table([(1, 1)])
ORGAN = _table([(1, 1), (2, 0.5), (3, 0.25), (5, 0.08)])
BOX = _table([(1, 1), (3, 0.35), (5.0, 0.0), (6, 0.12)])     # a music box's tine
BELL = _table([(1, 1), (2.76, 0.4), (5.4, 0.2)])
SAW = _table([(h, 1 / h) for h in range(1, 12)])
TRI = [1 - 4 * abs(i / SIZE - 0.5) for i in range(SIZE)]
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
            f *= 1 + vib * SINE[int(k * vstep) & 1023]
        phase = (phase + f) % SIZE
        s = table[int(phase)] * env * vol
        if trem:
            s *= 1 - trem * (0.5 + 0.5 * SINE[int(k * tstep) & 1023])
        buf[idx] += s


def pluck(buf, start, freq, vol, decay=3.0, table=BOX, wrap=True):
    """A struck note that rings away (music box, bell, coin)."""
    n_total = len(buf)
    i0 = int(start * RATE)
    inc = freq * SIZE / RATE
    phase = 0.0
    for k in range(int(min(3.0, 5.0 / decay) * RATE)):
        idx = i0 + k
        if idx >= n_total:
            if not wrap:
                break
            idx %= n_total
        phase = (phase + inc) % SIZE
        env = math.exp(-decay * k / RATE) * min(1.0, k / 40)
        buf[idx] += table[int(phase)] * env * vol


def noise(buf, rng, start, dur, vol, decay=30.0, smooth=0.0, wrap=True):
    """A burst of noise that dies away (smooth > 0 darkens it)."""
    n_total = len(buf)
    i0 = int(start * RATE)
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


def thump(buf, start, vol, low=40, high=90, length=0.25, wrap=True):
    """A soft kick: a heartbeat, a thud."""
    n_total = len(buf)
    i0 = int(start * RATE)
    phase = 0.0
    for k in range(int(length * RATE)):
        t = k / RATE
        f = low + high * math.exp(-t * 30)
        phase += 2 * math.pi * f / RATE
        idx = i0 + k
        if idx >= n_total:
            if not wrap:
                break
            idx %= n_total
        buf[idx] += math.sin(phase) * vol * math.exp(-t * 12)


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
# A minor, with the Phrygian Bb for unease: (drone root, pad chord) per bar
CHORDS = [(33, (57, 60, 64)), (33, (57, 60, 64)), (29, (57, 60, 65)), (34, (58, 62, 65)),
          (33, (57, 60, 64)), (31, (55, 59, 62)), (34, (58, 62, 65)), (28, (56, 59, 64))]
# the music box: (beat, note) per bar - a little tune that doesn't quite resolve
TUNE = [[(0, 81), (1, 84), (2, 83), (3, 81)], [(0, 79), (1.5, 76), (3, 77)],
        [(0, 81), (1, 77), (2, 74), (3, 72)], [(0, 74), (1, 77), (2.5, 82)],
        [(0, 81), (1, 84), (2, 88), (3, 87)], [(0, 86), (1.5, 83), (3, 79)],
        [(0, 82), (1, 81), (2, 77), (3, 74)], [(0, 76), (2, 80)]]


def render(mood):
    n = int(BAR * BARS * RATE)
    drone, pad, box, beat = (array("f", bytes(4 * n)) for _ in range(4))
    rng = random.Random(11)
    tense = mood == "tension"
    for b in range(BARS):
        root, chord = CHORDS[b]
        t0 = b * BAR
        note(drone, t0, BAR, midi(root), 0.30, ORGAN, attack=0.4, release=0.6, vib=0.003, vib_rate=0.4)
        note(drone, t0, BAR, midi(root) * 1.004, 0.18, SINE, attack=0.6, release=0.6)
        if tense:                                   # a thin, wavering whine a tritone up
            note(drone, t0, BAR, midi(root + 30), 0.05, SINE, attack=1.0, release=0.8, vib=0.012, vib_rate=0.7)
        for m in chord:
            note(pad, t0, BAR - 0.1, midi(m - 12), 0.07, SAW, attack=0.9, release=0.9, vib=0.004,
                 trem=0.5 if tense else 0.25, trem_rate=7.0 if tense else 1.2)
        for bt, m in TUNE[b]:
            detune = 1.0 + (rng.uniform(-0.012, 0.012) if tense else rng.uniform(-0.003, 0.003))
            pluck(box, t0 + bt * BEAT, midi(m) * detune, 0.16 if not tense else 0.12, decay=2.6)
        # the heartbeat: lub-dub once a bar, or on every beat when it's close
        for k in (range(4) if tense else (0,)):
            thump(beat, t0 + k * BEAT, 0.55, low=38, high=55)
            thump(beat, t0 + k * BEAT + 0.17, 0.35, low=38, high=45)
        if b % 2 == 1:                              # something metal, far off
            noise(beat, rng, t0 + 2.5 * BEAT, 0.6, 0.05, decay=5, smooth=0.97)
            pluck(beat, t0 + 2.5 * BEAT, 196 * rng.uniform(0.97, 1.03), 0.035, decay=1.6, table=BELL)
    echo(box, BEAT * 1.5, 0.45)
    lowpass(box, 0.5)
    lowpass(pad, 0.25)
    lowpass(drone, 0.2)
    mix = array("f", (drone[i] + pad[i] + box[i] + beat[i] for i in range(n)))
    lowpass(mix, 0.75)
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
    rng = random.Random(5)
    out = {}

    def save(name, buf, peak=0.7):
        path = folder / f"{name}.wav"
        out[name] = path
        if not path.exists():
            to_wav(path, buf, peak)

    b = _fx(0.03)
    note(b, 0, 0.012, 1500, 0.4, SQUARE, release=0.01, wrap=False)
    save("click", b, 0.5)
    b = _fx(0.5)                                    # the lever: a ratcheting pull and a clunk
    for k in range(6):
        noise(b, rng, k * 0.035, 0.02, 0.4, decay=150, wrap=False)
    thump(b, 0.24, 0.8, low=60, high=120, length=0.2, wrap=False)
    noise(b, rng, 0.24, 0.12, 0.4, decay=40, smooth=0.6, wrap=False)
    save("lever", b)
    b = _fx(0.05)                                   # the reels whirring: one tick
    noise(b, rng, 0, 0.03, 0.5, decay=180, smooth=0.3, wrap=False)
    note(b, 0, 0.01, 900, 0.15, SQUARE, release=0.01, wrap=False)
    save("tick", b, 0.4)
    for k in range(5):                              # each reel stopping, a little higher
        b = _fx(0.2)
        thump(b, 0, 0.7, low=70 + k * 8, high=140, length=0.15, wrap=False)
        noise(b, rng, 0, 0.05, 0.35, decay=90, smooth=0.4, wrap=False)
        note(b, 0, 0.02, 600 + 80 * k, 0.15, SQUARE, release=0.03, wrap=False)
        save(f"stop{k}", b)
    for k in range(12):                             # a pattern paying, climbing as more pay
        b = _fx(0.5)
        m = 72 + [0, 3, 5, 7, 10, 12, 15, 17, 19, 22, 24, 27][k]
        pluck(b, 0, midi(m), 0.5, decay=6, table=BELL, wrap=False)
        pluck(b, 0.06, midi(m + 7), 0.3, decay=7, table=BELL, wrap=False)
        save(f"win{k}", b)
    b = _fx(0.3)                                    # a coin
    pluck(b, 0, 2093, 0.4, decay=14, table=BELL, wrap=False)
    pluck(b, 0.05, 2637, 0.3, decay=14, table=BELL, wrap=False)
    save("coin", b, 0.5)
    b = _fx(1.6)                                    # coins pouring out
    for k in range(26):
        t = k * 0.045 + rng.uniform(0, 0.02)
        pluck(b, t, rng.choice((1760, 2093, 2349, 2637, 3136)), 0.25, decay=12, table=BELL, wrap=False)
    save("pour", b)
    b = _fx(2.2)                                    # Jackpot
    for k, m in enumerate((72, 76, 79, 84, 79, 84, 88, 91)):
        note(b, k * 0.1, 0.09, midi(m), 0.3, SQUARE, release=0.06, wrap=False)
    for m in (84, 88, 91, 96):
        note(b, 0.85, 0.9, midi(m), 0.15, SQUARE, release=0.4, vib=0.01, wrap=False)
    for k in range(30):
        pluck(b, 0.8 + k * 0.04, rng.choice((2093, 2637, 3136)), 0.18, decay=10, table=BELL, wrap=False)
    save("jackpot", b)
    b = _fx(2.4)                                    # 6-6-6: everything gone
    for m in (33, 39, 45):                          # a low tritone stack, swelling
        note(b, 0, 1.6, midi(m), 0.3, SAW, attack=0.3, release=0.6, vib=0.01, vib_rate=3, wrap=False)
    for k in range(3):
        thump(b, k * 0.33, 0.9, low=35, high=60, length=0.35, wrap=False)
    noise(b, rng, 0, 2.0, 0.25, decay=1.5, smooth=0.95, wrap=False)
    lowpass(b, 0.35)
    save("six", b)
    b = _fx(0.7)                                    # the ATM taking coins: beeps and a clunk
    for k, f in enumerate((1318, 1568, 1318)):
        note(b, k * 0.08, 0.05, f, 0.25, SQUARE, release=0.01, wrap=False)
    for k in range(8):
        pluck(b, 0.25 + k * 0.025, rng.choice((1760, 2093, 2349)), 0.18, decay=18, table=BELL, wrap=False)
    thump(b, 0.5, 0.6, low=55, high=80, length=0.15, wrap=False)
    save("deposit", b)
    b = _fx(0.6)
    note(b, 0, 0.05, 1568, 0.3, SQUARE, release=0.0, wrap=False)
    pluck(b, 0.06, 2093, 0.35, decay=5, table=BELL, wrap=False)
    save("interest", b)
    b = _fx(0.9)                                    # the charm machine: a whirr, a drop and a jingle
    note(b, 0, 0.35, 90, 0.25, SAW, slide=140, release=0.05, wrap=False)
    thump(b, 0.4, 0.8, low=50, high=90, length=0.2, wrap=False)
    noise(b, rng, 0.4, 0.15, 0.3, decay=40, smooth=0.5, wrap=False)
    for k, m in enumerate((84, 88, 91)):
        pluck(b, 0.5 + k * 0.07, midi(m), 0.25, decay=6, table=BELL, wrap=False)
    save("buy", b)
    b = _fx(0.4)
    for k in range(6):
        noise(b, rng, k * 0.05, 0.035, 0.3, decay=110, wrap=False)
        note(b, k * 0.05, 0.02, 700 + 90 * k, 0.12, SQUARE, release=0.02, wrap=False)
    save("reroll", b)
    b = _fx(0.3)
    note(b, 0, 0.06, 1319, 0.3, SQUARE, release=0.0, wrap=False)
    note(b, 0.06, 0.14, 988, 0.3, SQUARE, release=0.05, wrap=False)
    save("sell", b)
    b = _fx(0.5)                                    # a ticket printing
    for k in range(10):
        noise(b, rng, k * 0.03, 0.02, 0.35, decay=200, smooth=0.2, wrap=False)
        note(b, k * 0.03, 0.015, 2400, 0.08, SQUARE, release=0.005, wrap=False)
    save("ticket", b, 0.5)
    b = _fx(1.6)                                    # an old telephone bell
    n = int(1.1 * RATE)
    for k in range(n):
        t = k / RATE
        strike = 0.6 + 0.4 * math.sin(2 * math.pi * 22 * t)
        env = min(1.0, t * 40) * (1.0 if t < 1.0 else max(0.0, 1 - (t - 1.0) * 10))
        s = (math.sin(2 * math.pi * 1180 * t) + 0.6 * math.sin(2 * math.pi * 1475 * t)
             + 0.3 * math.sin(2 * math.pi * 3250 * t))
        b[k] += s * strike * env * 0.3
    save("ring", b)
    b = _fx(0.35)
    thump(b, 0, 0.6, low=90, high=150, length=0.12, wrap=False)
    noise(b, rng, 0.02, 0.1, 0.3, decay=60, smooth=0.5, wrap=False)
    note(b, 0.1, 0.15, 440, 0.06, SQUARE, release=0.05, wrap=False)
    save("pickup", b)
    b = _fx(0.3)
    thump(b, 0, 0.8, low=70, high=120, length=0.14, wrap=False)
    noise(b, rng, 0, 0.08, 0.4, decay=70, smooth=0.4, wrap=False)
    save("hangup", b)
    b = _fx(1.4)                                    # a holy answer: a choir-ish shimmer
    for m in (72, 76, 79, 84):
        note(b, 0, 0.7, midi(m), 0.12, ORGAN, attack=0.25, release=0.5, vib=0.006, wrap=False)
    for k in range(10):
        pluck(b, 0.1 + k * 0.08, midi(rng.choice((96, 100, 103, 108))), 0.1, decay=5, table=SINE, wrap=False)
    save("holy", b)
    b = _fx(1.4)                                    # an evil answer: a growl
    note(b, 0, 0.9, 55, 0.4, SAW, slide=41, attack=0.05, release=0.4, vib=0.05, vib_rate=11, wrap=False)
    note(b, 0, 0.9, 77.8, 0.2, SAW, slide=58, attack=0.05, release=0.4, vib=0.05, vib_rate=13, wrap=False)
    lowpass(b, 0.3)
    save("evil", b)
    b = _fx(0.9)
    for k, m in enumerate((69, 72, 76)):
        note(b, k * 0.06, 0.4, midi(m), 0.12, ORGAN, attack=0.02, release=0.3, wrap=False)
    save("ability", b)
    b = _fx(3.0)                                    # the trapdoor: a creak, a fall, and a long way down
    note(b, 0, 0.5, 140, 0.3, SAW, slide=95, vib=0.08, vib_rate=17, release=0.05, wrap=False)
    thump(b, 0.55, 1.0, low=45, high=110, length=0.35, wrap=False)
    noise(b, rng, 0.55, 0.2, 0.5, decay=20, smooth=0.5, wrap=False)
    n0 = int(0.7 * RATE)
    y = 0.0
    for k in range(int(1.8 * RATE)):                # the wind rushing past
        a = 0.02 + 0.3 * k / (1.8 * RATE)
        y += a * (rng.uniform(-1, 1) - y)
        b[n0 + k] += y * 0.5 * (1 - k / (1.8 * RATE))
    save("trapdoor", b)
    b = _fx(0.25)
    note(b, 0, 0.12, 130, 0.4, SQUARE, release=0.05, wrap=False)
    note(b, 0, 0.12, 138, 0.3, SQUARE, release=0.05, wrap=False)
    save("nope", b)
    b = _fx(0.6)                                    # buying spins: a coin down the slot
    pluck(b, 0, 2093, 0.3, decay=12, table=BELL, wrap=False)
    for k in range(5):
        noise(b, rng, 0.08 + k * 0.05, 0.03, 0.2 * (1 - k / 5), decay=120, smooth=0.3, wrap=False)
    thump(b, 0.35, 0.5, low=60, high=90, length=0.12, wrap=False)
    save("package", b)
    b = _fx(1.2)                                    # a deadline paid
    for k, m in enumerate((69, 72, 76, 81)):
        pluck(b, k * 0.11, midi(m), 0.35, decay=3, table=BELL, wrap=False)
    save("paid", b)
    b = _fx(3.2)                                    # climbing out
    for k, m in enumerate((69, 72, 76, 81, 76, 81, 84, 88)):
        note(b, k * 0.16, 0.14, midi(m), 0.25, SQUARE, release=0.08, wrap=False)
    for m in (81, 84, 88, 93):
        note(b, 1.35, 1.2, midi(m), 0.12, ORGAN, attack=0.1, release=0.6, vib=0.008, wrap=False)
    save("escape", b)
    return out


# ---- playing it -------------------------------------------------------------------------------------------------
class Audio:
    """The sound effects (QSoundEffect) and the two music loops kept in step, faded between by mood."""

    def __init__(self, parent, music=True, sfx=True):
        self.parent = parent
        self.music_on = music
        self.sfx_on = sfx
        self.mood = "pit"
        self.fx = {}
        self.players = {}
        self.outputs = {}
        self.volume = {m: 0.0 for m in MOODS}
        self.paths = None
        self.closed = False
        self.failed = False
        self.folder = host.data("claudepit") / f"sounds-{VERSION}"
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
            for pl in self.players.values():           # (both together, so they stay in step)
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
        step = dt / 2.0 * MUSIC_VOLUME
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

    def stop(self):
        self.closed = True
        for pl in self.players.values():
            pl.stop()
        for fx in self.fx.values():
            fx.stop()
