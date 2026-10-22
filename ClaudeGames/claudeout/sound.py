"""Claudeout 4's soundscape: the vault's hum, drips and distant clanks; the wind, crows and creaking metal of the
surface; a nervous pulse when something's hunting you; and a jaunty old-time swing tune on the Pip-Boy's radio. Plus
the pod's hiss, sliding doors, terminal keys, punches, the baton, the 10mm pistol, chitters, buzzing, mole rats
bursting out of the ground, the vault door's klaxon and grinding gear, the elevator, and the robot's chirps.

All of it is synthesized here, written once to this computer's data folder and played from there; the loops are
built on a background thread the first time."""
import math
import random
import threading
import wave
from array import array

from PySide6.QtCore import QUrl

from claudecore import host

RATE = 22050
VERSION = "v1"
MOODS = ("vault", "surface", "combat", "radio")
VOLUMES = {"vault": 0.35, "surface": 0.33, "combat": 0.3, "radio": 0.3}
SFX_VOLUME = 0.5
SIZE = 1024


def midi(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def _table(harmonics):
    t = [sum(a * math.sin(2 * math.pi * h * i / SIZE) for h, a in harmonics) for i in range(SIZE)]
    peak = max(abs(x) for x in t)
    return [x / peak for x in t]


SINE = _table([(1, 1)])
ORGAN = _table([(1, 1), (2, 0.5), (3, 0.25), (5, 0.08)])
BELL = _table([(1, 1), (2.76, 0.4), (5.4, 0.2)])
SAW = _table([(h, 1 / h) for h in range(1, 12)])
TRI = [1 - 4 * abs(i / SIZE - 0.5) for i in range(SIZE)]
SQUARE = [1.0 if i < SIZE // 2 else -1.0 for i in range(SIZE)]
PULSE = [1.0 if i < SIZE // 4 else -1.0 for i in range(SIZE)]


def note(buf, start, dur, freq, vol, table, attack=0.01, release=0.08, vib=0.0, vib_rate=5.5, trem=0.0,
         trem_rate=6.0, slide=None, wrap=True):
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
        env = k / att if k < att else (1 - (k - hold) / rel if k > hold else 1.0)
        f = inc + (inc2 - inc) * (k / n) if slide else inc
        if vib:
            f *= 1 + vib * SINE[int(k * vstep) & 1023]
        phase = (phase + f) % SIZE
        s = table[int(phase)] * env * vol
        if trem:
            s *= 1 - trem * (0.5 + 0.5 * SINE[int(k * tstep) & 1023])
        buf[idx] += s


def pluck(buf, start, freq, vol, decay=3.0, table=BELL, wrap=True):
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
        buf[idx] += table[int(phase)] * math.exp(-decay * k / RATE) * min(1.0, k / 40) * vol


def noise(buf, rng, start, dur, vol, decay=30.0, smooth=0.0, wrap=True):
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
    n_total = len(buf)
    i0 = int(start * RATE)
    phase = 0.0
    for k in range(int(length * RATE)):
        t = k / RATE
        phase += 2 * math.pi * (low + high * math.exp(-t * 30)) / RATE
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


def _fx(seconds):
    return array("f", bytes(4 * int(seconds * RATE)))


# ---- the loops ---------------------------------------------------------------------------------------------------
def render_vault():
    """The vault at rest: a deep hum from the machinery, pipes ticking, a drip, something far off clanking."""
    length = 24.0
    buf = _fx(length)
    rng = random.Random(111)
    note(buf, 0, length, 55, 0.22, SINE, attack=0.5, release=0.5, vib=0.004, vib_rate=0.3)
    note(buf, 0, length, 110, 0.08, ORGAN, attack=0.5, release=0.5, trem=0.4, trem_rate=0.9)
    note(buf, 0, length, 60, 0.05, SAW, attack=0.5, release=0.5, vib=0.01, vib_rate=0.15)
    for k in range(int(length / 0.5)):                   # the pipes ticking
        if rng.random() < 0.35:
            t = k * 0.5 + rng.uniform(0, 0.4)
            noise(buf, rng, t, 0.03, 0.08, decay=200, smooth=0.3)
    for t in (3.2, 9.7, 15.1, 20.4):                      # drips
        pluck(buf, t, rng.uniform(1800, 2600), 0.08, decay=18, table=SINE)
        pluck(buf, t + 0.05, rng.uniform(900, 1300), 0.05, decay=25, table=SINE)
    for t in (6.0, 17.5):                                 # a distant clank, with its echo
        thump(buf, t, 0.2, low=70, high=200, length=0.3)
        pluck(buf, t, 196, 0.06, decay=2, table=BELL)
    echo(buf, 0.37, 0.3)
    lowpass(buf, 0.5)
    return buf


def render_surface():
    """Outside: the wind over the hill, crows, something metal creaking, a rumble far off."""
    length = 28.0
    buf = _fx(length)
    rng = random.Random(21)
    n = int(length * RATE)
    y = 0.0
    for k in range(n):                                    # the wind: dark noise that swells and fades
        t = k / RATE
        swell = 0.35 + 0.65 * (0.5 + 0.5 * math.sin(2 * math.pi * t / 9.0 + 1.0)) * (0.6 + 0.4 * math.sin(2 * math.pi * t / 4.1))
        y += 0.02 * (rng.uniform(-1, 1) - y)
        buf[k] += y * swell * 0.9
    for t in (4.5, 12.8, 21.0):                           # crows
        for j in range(rng.randint(2, 4)):
            tt = t + j * 0.28
            note(buf, tt, 0.14, rng.uniform(600, 760), 0.12, SAW, slide=rng.uniform(420, 520), attack=0.01,
                 release=0.05, vib=0.03, vib_rate=28)
    for t in (8.0, 24.0):                                 # a sign creaking on its chains
        note(buf, t, 0.9, 180, 0.05, SAW, slide=140, attack=0.2, release=0.3, vib=0.04, vib_rate=7)
        note(buf, t + 1.6, 0.7, 150, 0.04, SAW, slide=190, attack=0.2, release=0.3, vib=0.04, vib_rate=6)
    thump(buf, 16.0, 0.25, low=30, high=40, length=1.2)   # thunder, a long way off
    noise(buf, rng, 16.0, 2.5, 0.12, decay=1.2, smooth=0.97)
    lowpass(buf, 0.45)
    return buf


def render_combat():
    """Radroaches about: a fast low pulse and a skittering top."""
    length = 8.0
    buf = _fx(length)
    rng = random.Random(7)
    beat = 60 / 132
    for k in range(int(length / beat)):
        t = k * beat
        thump(buf, t, 0.5 if k % 2 == 0 else 0.3, low=45, high=70, length=0.2)
        note(buf, t, beat * 0.4, midi(36 if k % 4 < 2 else 34), 0.2, SAW, release=0.05)
        if k % 2 == 1:
            noise(buf, rng, t + beat / 2, 0.08, 0.08, decay=60, smooth=0.2)
    for _ in range(40):                                   # skitters
        t = rng.uniform(0, length)
        for j in range(4):
            noise(buf, rng, t + j * 0.03, 0.015, 0.1, decay=300)
    lowpass(buf, 0.6)
    return buf


# the radio tune: a swing in F, (bass root, chord) per bar
CHORDS = [(41, (65, 69, 72, 76)), (41, (65, 69, 72, 76)), (46, (65, 70, 74, 77)), (41, (65, 69, 72, 76)),
          (48, (67, 71, 74, 77)), (48, (67, 71, 74, 77)), (41, (65, 69, 72, 76)), (48, (67, 70, 74, 77))]
MELODY = [[(0, 1, 77), (1, 1, 81), (2, 2, 84)], [(0, 0.5, 84), (0.5, 0.5, 81), (1, 1, 79), (2, 2, 77)],
          [(0, 1, 82), (1, 1, 79), (2, 1, 77), (3, 1, 74)], [(0, 3, 77)],
          [(0, 1, 79), (1, 1, 83), (2, 2, 86)], [(0, 0.5, 86), (0.5, 0.5, 83), (1, 1, 81), (2, 2, 79)],
          [(0, 1, 84), (1, 1, 81), (2, 1, 77), (3, 1, 72)], [(0, 2, 74), (2, 2, 77)]]


def render_radio():
    bpm = 168
    beat = 60 / bpm
    bar = beat * 4
    bars = 16
    length = bar * bars
    buf = _fx(length)
    rng = random.Random(3)
    swing = 0.66
    for b in range(bars):
        root, chord = CHORDS[b % 8]
        t0 = b * bar
        for e in range(4):                                # a walking bass
            m = root + (0, 4, 7, 9)[e] if b % 2 == 0 else root + (12, 9, 7, 4)[e]
            note(buf, t0 + e * beat, beat * 0.7, midi(m), 0.32, TRI, attack=0.005, release=0.05)
        for e in range(4):                                # the comping chord on the off-beats
            if e % 2 == 1:
                for m in chord:
                    note(buf, t0 + (e + swing - 0.5) * beat, beat * 0.25, midi(m), 0.06, ORGAN, release=0.08)
        for bt, ln, m in MELODY[b % 8]:                   # the lead, a reedy pulse wave
            note(buf, t0 + bt * beat, ln * beat * 0.85, midi(m), 0.14, PULSE, attack=0.02, release=0.08,
                 vib=0.008, vib_rate=6.0)
        for e in range(4):                                # brushes
            noise(buf, rng, t0 + e * beat, 0.09, 0.07, decay=35, smooth=0.5)
            noise(buf, rng, t0 + (e + swing) * beat, 0.05, 0.05, decay=70, smooth=0.4)
        if b % 4 == 3:
            thump(buf, t0 + 3.5 * beat, 0.2, low=60, high=100, length=0.15)
    echo(buf, beat * 0.5, 0.2)
    # the old-radio sound: band-limited and a little crackly
    lowpass(buf, 0.35)
    for _ in range(120):
        t = rng.uniform(0, length)
        noise(buf, rng, t, 0.01, 0.04, decay=400)
    return buf


def make_music(folder):
    paths = {}
    for mood, fn in (("vault", render_vault), ("surface", render_surface), ("combat", render_combat),
                     ("radio", render_radio)):
        path = folder / f"music-{mood}.wav"
        if not path.exists():
            to_wav(path, fn(), 0.8)
        paths[mood] = path
    return paths


# ---- the sound effects ------------------------------------------------------------------------------------------
def make_sfx(folder):
    rng = random.Random(5)
    out = {}

    def save(name, buf, peak=0.7):
        path = folder / f"{name}.wav"
        out[name] = path
        if not path.exists():
            to_wav(path, buf, peak)

    b = _fx(2.2)                                    # the pod's seal breaking and the hiss of the thaw
    thump(b, 0, 0.6, low=50, high=90, length=0.3, wrap=False)
    noise(b, rng, 0.2, 1.8, 0.4, decay=2.0, smooth=0.6, wrap=False)
    note(b, 0.3, 1.2, 180, 0.1, SAW, slide=90, attack=0.1, release=0.3, wrap=False)
    save("pod", b)
    for k in range(2):
        b = _fx(0.18)
        thump(b, 0, 0.5, low=60 + k * 15, high=80, length=0.1, wrap=False)
        noise(b, rng, 0, 0.08, 0.3, decay=60, smooth=0.5 + k * 0.1, wrap=False)
        save(f"step{k}", b, 0.45)
    b = _fx(0.8)                                    # a door sliding up
    noise(b, rng, 0, 0.6, 0.3, decay=3, smooth=0.8, wrap=False)
    note(b, 0, 0.5, 120, 0.15, SAW, slide=220, release=0.1, wrap=False)
    thump(b, 0.6, 0.5, low=70, high=90, length=0.15, wrap=False)
    save("door", b)
    b = _fx(0.4)                                    # locked: a buzz
    note(b, 0, 0.3, 110, 0.3, SQUARE, release=0.03, trem=0.8, trem_rate=25, wrap=False)
    save("locked", b, 0.5)
    b = _fx(0.12)
    note(b, 0, 0.06, 1760, 0.3, SQUARE, release=0.03, wrap=False)
    save("beep", b, 0.45)
    b = _fx(0.06)
    noise(b, rng, 0, 0.02, 0.4, decay=200, wrap=False)
    note(b, 0, 0.015, 2200, 0.2, SQUARE, release=0.01, wrap=False)
    save("key", b, 0.4)
    b = _fx(0.25)                                   # a punch through the air
    noise(b, rng, 0, 0.2, 0.3, decay=12, smooth=0.9, wrap=False)
    save("swing", b, 0.5)
    b = _fx(0.3)                                    # the baton whistling
    noise(b, rng, 0, 0.25, 0.3, decay=10, smooth=0.6, wrap=False)
    note(b, 0, 0.15, 600, 0.08, SINE, slide=1400, release=0.05, wrap=False)
    save("baton", b, 0.5)
    b = _fx(0.35)                                   # a hit: a squish
    thump(b, 0, 0.6, low=90, high=160, length=0.12, wrap=False)
    noise(b, rng, 0.02, 0.25, 0.4, decay=14, smooth=0.75, wrap=False)
    note(b, 0.03, 0.1, 300, 0.15, TRI, slide=120, release=0.05, wrap=False)
    save("hit", b)
    b = _fx(0.6)                                    # a kill: the crunch and a dying chitter
    thump(b, 0, 0.7, low=70, high=140, length=0.15, wrap=False)
    noise(b, rng, 0, 0.3, 0.5, decay=10, smooth=0.5, wrap=False)
    for k in range(6):
        note(b, 0.15 + k * 0.05, 0.03, 1800 - k * 150, 0.12, SQUARE, release=0.01, wrap=False)
    save("kill", b)
    b = _fx(0.5)                                    # the 10mm
    noise(b, rng, 0, 0.12, 0.9, decay=25, wrap=False)
    thump(b, 0, 0.9, low=60, high=200, length=0.2, wrap=False)
    noise(b, rng, 0.08, 0.4, 0.25, decay=8, smooth=0.85, wrap=False)
    save("shot", b, 0.85)
    b = _fx(0.12)
    noise(b, rng, 0, 0.03, 0.3, decay=150, wrap=False)
    thump(b, 0, 0.3, low=200, high=300, length=0.05, wrap=False)
    save("empty", b, 0.4)
    b = _fx(0.5)                                    # a bite: chitter and a grunt
    for k in range(5):
        note(b, k * 0.04, 0.025, 2200 + rng.uniform(-300, 300), 0.15, SQUARE, release=0.01, wrap=False)
    note(b, 0.1, 0.2, 140, 0.3, SAW, slide=100, attack=0.02, release=0.1, wrap=False)
    noise(b, rng, 0.1, 0.2, 0.2, decay=15, smooth=0.7, wrap=False)
    save("bite", b)
    b = _fx(0.5)                                    # a roach chittering
    for k in range(7):
        note(b, k * 0.05 + rng.uniform(0, 0.02), 0.02, 1600 + rng.uniform(-400, 600), 0.14, SQUARE, release=0.01,
             wrap=False)
    save("chitter", b, 0.5)
    b = _fx(0.4)
    note(b, 0, 0.05, 1046, 0.3, SQUARE, release=0.0, wrap=False)
    note(b, 0.06, 0.12, 1568, 0.3, SQUARE, release=0.08, wrap=False)
    save("pickup", b, 0.5)
    b = _fx(0.7)                                    # a stimpak: a jab and relief
    noise(b, rng, 0, 0.05, 0.3, decay=100, wrap=False)
    for k, m in enumerate((72, 76, 79, 84)):
        pluck(b, 0.1 + k * 0.08, midi(m), 0.25, decay=6, table=SINE, wrap=False)
    save("stimpak", b, 0.5)
    b = _fx(1.8)                                    # the Pip-Boy booting
    noise(b, rng, 0, 0.3, 0.15, decay=8, smooth=0.3, wrap=False)
    for k in range(8):
        note(b, 0.1 + k * 0.05, 0.03, 800 + k * 150, 0.12, SQUARE, release=0.01, wrap=False)
    for k, m in enumerate((67, 72, 76, 79)):
        note(b, 0.7 + k * 0.12, 0.1, midi(m), 0.25, SQUARE, release=0.05, wrap=False)
    note(b, 1.2, 0.4, midi(84), 0.2, SQUARE, release=0.2, wrap=False)
    save("pipboy", b, 0.55)
    b = _fx(0.6)                                    # a two-tone chime: a new objective
    note(b, 0, 0.12, midi(79), 0.3, SQUARE, release=0.05, wrap=False)
    note(b, 0.14, 0.3, midi(84), 0.3, SQUARE, release=0.15, wrap=False)
    save("objective", b, 0.5)
    b = _fx(2.0)                                    # the klaxon
    for k in range(2):
        note(b, k * 1.0, 0.45, 440, 0.4, SAW, slide=330, attack=0.02, release=0.1, wrap=False)
        note(b, k * 1.0 + 0.5, 0.45, 330, 0.4, SAW, slide=440, attack=0.02, release=0.1, wrap=False)
    lowpass(b, 0.4)
    save("alarm", b, 0.6)
    b = _fx(6.5)                                    # the gear door: a slam, grinding, and rolling aside
    thump(b, 0, 1.0, low=40, high=120, length=0.6, wrap=False)
    noise(b, rng, 0.2, 1.3, 0.5, decay=2, smooth=0.8, wrap=False)
    note(b, 0.2, 1.2, 60, 0.3, SAW, slide=40, attack=0.1, release=0.3, vib=0.05, vib_rate=14, wrap=False)
    for k in range(40):                             # the teeth clanking past
        t = 1.8 + k * 0.11
        thump(b, t, 0.3, low=80, high=150, length=0.08, wrap=False)
        noise(b, rng, t, 0.05, 0.25, decay=60, smooth=0.5, wrap=False)
    note(b, 1.8, 4.4, 48, 0.25, SAW, attack=0.3, release=0.5, vib=0.03, vib_rate=9, wrap=False)
    noise(b, rng, 1.8, 4.6, 0.2, decay=0.5, smooth=0.92, wrap=False)
    lowpass(b, 0.5)
    save("gear", b, 0.8)
    b = _fx(7.0)                                    # the elevator: a jolt, then the motor
    thump(b, 0, 0.8, low=50, high=100, length=0.4, wrap=False)
    noise(b, rng, 0.5, 6.0, 0.25, decay=0.3, smooth=0.9, wrap=False)
    note(b, 0.5, 6.0, 70, 0.2, SAW, slide=95, attack=0.8, release=0.5, trem=0.3, trem_rate=12, wrap=False)
    note(b, 0.5, 6.0, 140, 0.08, SQUARE, slide=190, attack=0.8, release=0.5, wrap=False)
    lowpass(b, 0.4)
    save("elevator", b, 0.7)
    b = _fx(0.6)                                    # hurt
    note(b, 0, 0.25, 160, 0.3, SAW, slide=110, attack=0.02, release=0.1, wrap=False)
    noise(b, rng, 0, 0.3, 0.2, decay=12, smooth=0.7, wrap=False)
    save("hurt", b, 0.5)
    b = _fx(2.5)                                    # death: a long fall of tone
    note(b, 0, 2.0, 220, 0.3, SAW, slide=40, attack=0.05, release=0.4, wrap=False)
    thump(b, 0.3, 0.8, low=40, high=80, length=0.5, wrap=False)
    lowpass(b, 0.3)
    save("death", b, 0.6)
    b = _fx(3.0)                                    # out into the light
    for k, m in enumerate((65, 69, 72, 77, 72, 77, 81, 84)):
        note(b, k * 0.15, 0.13, midi(m), 0.22, SQUARE, release=0.06, wrap=False)
    for m in (77, 81, 84, 89):
        note(b, 1.25, 1.3, midi(m), 0.12, ORGAN, attack=0.1, release=0.6, vib=0.008, wrap=False)
    save("win", b, 0.6)
    b = _fx(0.2)
    note(b, 0, 0.08, 700, 0.25, SQUARE, release=0.03, wrap=False)
    note(b, 0.08, 0.08, 900, 0.25, SQUARE, release=0.03, wrap=False)
    save("tab", b, 0.4)
    b = _fx(0.9)                                    # a bloatfly's drone
    note(b, 0, 0.8, 175, 0.3, SAW, release=0.1, vib=0.03, vib_rate=4, trem=0.6, trem_rate=31, wrap=False)
    note(b, 0, 0.8, 352, 0.1, SQUARE, release=0.1, trem=0.6, trem_rate=31, wrap=False)
    save("buzz", b, 0.45)
    b = _fx(0.4)                                    # a sting
    note(b, 0, 0.05, 2400, 0.25, SQUARE, slide=600, release=0.03, wrap=False)
    note(b, 0.06, 0.2, 150, 0.3, SAW, slide=100, attack=0.01, release=0.1, wrap=False)
    save("sting", b, 0.5)
    b = _fx(1.2)                                    # a mole rat bursting out of the ground
    thump(b, 0, 0.9, low=40, high=90, length=0.5, wrap=False)
    noise(b, rng, 0.05, 0.7, 0.5, decay=4, smooth=0.75, wrap=False)
    for k in range(10):
        noise(b, rng, 0.15 + k * 0.04, 0.03, 0.3, decay=120, smooth=0.2, wrap=False)
    note(b, 0.5, 0.3, 900, 0.2, SAW, slide=1400, attack=0.02, release=0.1, vib=0.05, vib_rate=20, wrap=False)
    save("emerge", b, 0.7)
    b = _fx(0.4)                                    # a mole rat's squeal
    note(b, 0, 0.25, 1100, 0.25, SAW, slide=1600, attack=0.02, release=0.1, vib=0.06, vib_rate=18, wrap=False)
    save("squeak", b, 0.5)
    b = _fx(0.7)                                    # eating: three crunches
    for k in range(3):
        noise(b, rng, k * 0.2, 0.12, 0.4, decay=25, smooth=0.5, wrap=False)
        thump(b, k * 0.2, 0.3, low=90, high=120, length=0.08, wrap=False)
    save("eat", b, 0.5)
    b = _fx(0.8)                                    # a bottle opening and fizzing
    noise(b, rng, 0, 0.04, 0.4, decay=120, wrap=False)
    note(b, 0, 0.03, 1800, 0.2, SINE, release=0.05, wrap=False)
    noise(b, rng, 0.08, 0.7, 0.25, decay=4, smooth=0.15, wrap=False)
    save("fizz", b, 0.45)
    b = _fx(0.7)                                    # the Geiger counter
    for _ in range(14):
        noise(b, rng, rng.uniform(0, 0.65), 0.008, 0.5, decay=400, wrap=False)
    save("geiger", b, 0.5)
    b = _fx(0.5)                                    # taking something off a corpse
    noise(b, rng, 0, 0.3, 0.35, decay=12, smooth=0.8, wrap=False)
    note(b, 0.1, 0.1, 240, 0.15, TRI, slide=160, release=0.08, wrap=False)
    save("loot", b, 0.5)
    b = _fx(1.2)                                    # the robot: a thruster's hiss and a few chirps
    noise(b, rng, 0, 1.1, 0.12, decay=1.5, smooth=0.6, wrap=False)
    for k, f in enumerate((1200, 1600, 1400, 1900)):
        note(b, 0.1 + k * 0.12, 0.06, f, 0.14, SQUARE, slide=f * 1.2, release=0.02, wrap=False)
    save("robot", b, 0.45)
    b = _fx(0.15)
    note(b, 0, 0.05, 1500, 0.2, SQUARE, slide=1900, release=0.03, wrap=False)
    save("talk", b, 0.4)
    b = _fx(3.5)                                    # a gust: out into the open air
    y = 0.0
    for k in range(int(3.4 * RATE)):
        t = k / RATE
        env = math.sin(math.pi * min(1.0, t / 3.4)) ** 1.5
        y += 0.03 * (rng.uniform(-1, 1) - y)
        b[k] += y * env * 0.9
    save("wind", b, 0.6)
    return out


# ---- playing it -------------------------------------------------------------------------------------------------
class Audio:
    """The sound effects (QSoundEffect) and the three loops, each faded in and out on its own."""

    def __init__(self, parent, music=True, sfx=True):
        self.parent = parent
        self.music_on = music
        self.sfx_on = sfx
        self.want = {"vault": 1.0, "surface": 0.0, "combat": 0.0, "radio": 0.0}
        self.fx = {}
        self.players = {}
        self.outputs = {}
        self.volume = {m: 0.0 for m in MOODS}
        self.paths = None
        self.closed = False
        self.failed = False
        self.folder = host.data("claudeout") / f"sounds-{VERSION}"
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
        for m, out in self.outputs.items():
            want = VOLUMES[m] * self.want[m] if on else 0.0
            v = self.volume[m]
            step = dt / 1.5 * VOLUMES[m]
            v = min(want, v + step) if want > v else max(want, v - step)
            if v != self.volume[m]:
                self.volume[m] = v
                out.setVolume(v)

    def play(self, name, volume=1.0):
        if not self.sfx_on or self.closed or host.muted():
            return
        fx = self.fx.get(name)
        if fx is not None:
            fx.setVolume(SFX_VOLUME * volume)
            fx.play()

    def stop_fx(self, name):
        fx = self.fx.get(name)
        if fx is not None:
            fx.stop()

    def stop(self):
        self.closed = True
        for pl in self.players.values():
            pl.stop()
        for fx in self.fx.values():
            fx.stop()
