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
