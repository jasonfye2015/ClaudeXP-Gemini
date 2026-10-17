"""The Timeline moving drives: saved paths follow it."""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from claudecore import relocate  # noqa: E402


def test_moves():
    with tempfile.TemporaryDirectory() as tmp:
        data = Path(tmp) / "data"
        (data / "doom").mkdir(parents=True)
        old = r"C:\Users\someone\Desktop\Claude Timeline"
        new = Path(r"F:\Claude Timeline")
        wad = old + r"\Local Storage\WADs\DOOM1.WAD"
        (data / "doom" / "settings.json").write_text(json.dumps({"recent": [wad]}), encoding="utf-8")
        (data / "llm.ini").write_text(f"model = {old}\\Local Storage\\m.gguf\n", encoding="utf-8")
        (data / "other.json").write_text(json.dumps({"p": r"C:\Claude Timeline Backup\x"}), encoding="utf-8")
        (data / "pic.png").write_bytes(old.encode())

        changed = relocate.fix(data, new)
        assert {p.name for p in changed} == {"settings.json", "llm.ini"}
        recent = json.loads((data / "doom" / "settings.json").read_text(encoding="utf-8"))["recent"]
        assert recent == [r"F:\Claude Timeline\Local Storage\WADs\DOOM1.WAD"]
        assert (data / "llm.ini").read_text(encoding="utf-8") == "model = F:\\Claude Timeline\\Local Storage\\m.gguf\n"
        assert "Backup" in (data / "other.json").read_text(encoding="utf-8")       # a different folder: untouched
        assert (data / "pic.png").read_bytes() == old.encode()                        # not a text file
        assert (data / relocate.MARKER).read_text(encoding="utf-8") == str(new)

        assert relocate.fix(data, new) == []                                          # nothing moved since

        # back to the Desktop, now under a renamed folder: the marker knows where it was
        home = Path(r"C:\Users\someone\Desktop\Timeline")
        relocate.fix(data, home)
        recent = json.loads((data / "doom" / "settings.json").read_text(encoding="utf-8"))["recent"]
        assert recent == [str(home / "Local Storage" / "WADs" / "DOOM1.WAD")]


if __name__ == "__main__":
    test_moves()
    print("ok")
