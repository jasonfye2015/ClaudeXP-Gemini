"""Her voice, made hers: a plain Piper voice (Kathleen) pitched five semitones down, creaking with vocal fry, driven
rough, an octave-down whisper of the same words trailing just behind, a scratch on top, and the hollow's echo. (The
user's pick from the auditions: "3B Kathleen - rasp".) numpy only.

    rasp(samples, rate) -> float32 at OUT_RATE, ready to play
"""
import numpy as np

OUT_RATE = 22050
N, HOP = 1024, 256
WIN = np.hanning(N)


def _resample(x, sr, to):
    if sr == to:
        return x
    t = np.arange(int(len(x) * to / sr)) / to
    return np.interp(t, np.arange(len(x)) / sr, x)


def _stft(x):
    x = np.concatenate([np.zeros(N), x, np.zeros(N)])
    idx = np.arange(0, len(x) - N, HOP)
    return np.fft.rfft(WIN * np.stack([x[i:i + N] for i in idx]), axis=1)


def _istft(X, length):
    frames = np.fft.irfft(X, N, axis=1) * WIN
    out = np.zeros(len(X) * HOP + N)
    norm = np.zeros_like(out)
    for k in range(len(X)):
        out[k * HOP:k * HOP + N] += frames[k]
        norm[k * HOP:k * HOP + N] += WIN ** 2
    out /= np.maximum(norm, 1e-6)
    return out[N:N + length]


def _stretch(x, rate):
    """Phase vocoder: longer by `rate`, the pitch kept."""
    X = _stft(x)
    steps = np.arange(0, len(X) - 1, 1 / rate)
    omega = 2 * np.pi * HOP * np.arange(N // 2 + 1) / N
    i = steps.astype(int)
    f = (steps - i)[:, None]
    mag = (1 - f) * np.abs(X[i]) + f * np.abs(X[i + 1])
    dp = np.angle(X[i + 1]) - np.angle(X[i]) - omega
    dp -= 2 * np.pi * np.round(dp / (2 * np.pi))
    step = omega + dp
    phase = np.angle(X[0]) + np.concatenate([np.zeros((1, step.shape[1])), np.cumsum(step, axis=0)[:-1]])
    return _istft(mag * np.exp(1j * phase), int(len(x) * rate))


def _pitch(x, semis):
    a = 2 ** (semis / 12)
    y = _stretch(x, a)
    return np.interp(np.arange(len(x)) * a, np.arange(len(y)), y)


def _whisper(x, rng):
    X = _stft(x)
    return _istft(np.abs(X) * np.exp(1j * rng.uniform(0, 2 * np.pi, X.shape)), len(x))


def _band(x, lo, hi):
    F = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / OUT_RATE)
    g = np.clip((f - lo * 0.7) / (lo * 0.3 + 1e-9), 0, 1) * np.clip((hi * 1.3 - f) / (hi * 0.3), 0, 1)
    return np.fft.irfft(F * g, len(x))


def _shelf(x, at, gain):
    F = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / OUT_RATE)
    return np.fft.irfft(F * (1 + (gain - 1) / (1 + np.exp(-(f - at) / (at * 0.15)))), len(x))


def _fry(x, depth, rng, rate=42.0):
    """Vocal fry: the voice in uneven pulses - a creak."""
    pulse = np.zeros(len(x))
    t = 0.0
    while t < len(x) / OUT_RATE:
        i = int(t * OUT_RATE)
        pulse[i:i + int(OUT_RATE * 0.006)] = 1.0
        t += 1 / (rate * rng.uniform(0.75, 1.3))
    pulse = np.convolve(pulse, np.hanning(int(OUT_RATE * 0.008)), "same")
    pulse /= pulse.max() or 1
    return x * (1 - depth + depth * pulse)


def _delay(x, ms):
    k = int(OUT_RATE * ms / 1000)
    return np.concatenate([np.zeros(k), x])[:len(x)]


def _reverb(x, wet, rng, seconds=1.4):
    n = int(OUT_RATE * seconds)
    t = np.arange(n) / OUT_RATE
    ir = rng.standard_normal(n) * np.exp(-t / (seconds / 4.5))
    ir = _band(ir, 120, 4000)
    ir[:int(OUT_RATE * 0.012)] = 0
    ir /= np.sqrt(np.sum(ir ** 2))
    m = len(x) + n
    y = np.fft.irfft(np.fft.rfft(x, m) * np.fft.rfft(ir, m), m)[:m]
    return np.concatenate([x, np.zeros(n)]) * (1 - wet) + y * wet * 1.6


def rasp(samples, rate, seed=7):
    """Kathleen's words, in Ysmeine's throat."""
    rng = np.random.default_rng(seed)
    x = _resample(np.asarray(samples, np.float64), rate, OUT_RATE)
    if len(x) < N * 2:
        x = np.concatenate([x, np.zeros(N * 2 - len(x))])
    v = _pitch(x, -5)
    v = _fry(v, 0.55, rng)
    v = np.tanh(v * 3.0) / 3.0 * 1.8
    v = v + 0.4 * _delay(_band(_whisper(_pitch(x, -12), rng), 200, 6000), 40)
    v = _shelf(v, 2500, 1.6)
    v = _reverb(v, 0.3, rng)
    loud = np.sqrt(np.mean(v[np.abs(v) > np.abs(v).max() * 0.02] ** 2)) or 1.0
    v = np.tanh(v / loud * 0.16 * 1.6) / 1.6
    return (v / max(1.0, np.abs(v).max() / 0.95)).astype(np.float32)
