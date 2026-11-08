"""Her voice: the three choices, which is best of what's there, and what's ready - asked without a real engine."""
from hollowoak.game import voice as V


def test_the_choices():
    assert [c[0] for c in V.CHOICES] == ["nemomix-unleashed-12b", "gemma3-4b", "none"]
    assert V.best_choice({"gemma3-4b", "nemomix-unleashed-12b"}) == "nemomix-unleashed-12b"
    assert V.best_choice({"gemma3-4b", "qwen25-coder-1.5b"}) == "gemma3-4b"
    assert V.best_choice(set()) == "none"
    for cid in ("nemomix-unleashed-12b", "gemma3-4b"):
        h = V.HELP[cid]
        assert h["page"].startswith("https://huggingface.co/") and h["file"].endswith(".gguf")
    assert '"chatml"' in V.HELP["nemomix-unleashed-12b"]["info"]


def test_what_is_ready():
    v = V.Voice("gemma3-4b")
    assert v.status("none") == "ready"
    assert v.status("gemma3-4b", installed={"gemma3-4b"}, engine=True) == "ready"
    assert v.status("nemomix-unleashed-12b", installed={"gemma3-4b"}, engine=True) == "missing"
    assert v.status("gemma3-4b", installed={"gemma3-4b"}, engine=False) == "no engine"
    got = []
    V.Voice("none").ask([{"role": "user", "content": "hello"}], got.append)
    assert got == [None]                                                     # (no model: the script speaks)


def test_her_rasp():
    import numpy as np

    from hollowoak.engine import rasp
    sr = 16000
    t = np.arange(int(sr * 1.5)) / sr                                            # (a stand-in for Kathleen: a voiced
    x = np.sin(2 * np.pi * 200 * t) * np.sin(np.pi * t / 1.5) ** 2               #  sound at her pitch, rising and falling)
    y = rasp.rasp(x, sr)
    assert y.dtype == np.float32 and np.isfinite(y).all() and np.abs(y).max() <= 0.951
    assert len(y) >= 1.5 * rasp.OUT_RATE                                          # (and the hollow's echo after it)
    spec = np.abs(np.fft.rfft(y[: int(rasp.OUT_RATE * 1.2)]))
    f = np.fft.rfftfreq(int(rasp.OUT_RATE * 1.2), 1 / rasp.OUT_RATE)
    peak = f[np.argmax(spec[(f > 60) & (f < 400)]) + np.searchsorted(f, 60)]
    assert 135 < peak < 165                                                       # (five semitones down: 200 -> ~150)


def test_her_voice_heard_or_quietly_not():
    import numpy as np

    from hollowoak.engine import herspeech, sound
    s = sound.Synth()
    s.speak(np.ones(2205, np.float32) * 0.2)
    assert s.speaking()
    for _ in range(3):
        s.render(1102)
    assert not s.speaking()                                                       # (said, and done)
    old = herspeech.runtime
    herspeech.runtime = lambda: (None, None)                                      # (no voice runtime here)
    try:
        h = herspeech.HerSpeech()
        got = []
        assert not h.available()
        h.say("Closer.", got.append)
        h.warm()
        assert got == [None] and h.thread is None
    finally:
        herspeech.runtime = old
