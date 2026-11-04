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


def test_shared():
    """The folders no computer owns (saves, Kithylin's and the Companions' settings) follow a new drive letter too."""
    with tempfile.TemporaryDirectory() as tmp:
        new = Path(tmp) / "Claude Timeline"
        old = r"F:\Claude Timeline"
        own = "own:" + old + r"\ClaudeApps\kithylinai\Models\kithylin\kithylin.gguf"
        saves, kith, comp = relocate.shared_folders(new)[0], relocate.shared_folders(new)[1], relocate.shared_folders(new)[3]
        for folder in (saves / "doom", kith, comp / "companion-1"):
            folder.mkdir(parents=True)
        (saves / "doom" / "settings.json").write_text(json.dumps({"recent": [old + r"\Local Storage\WADs\DOOM.WAD"]}), encoding="utf-8")
        (kith / "settings.json").write_text(json.dumps({"model": own}), encoding="utf-8")
        (comp / "companion-1" / "companion.json").write_text(json.dumps({"model": own}), encoding="utf-8")

        changed = relocate.fix_shared(new)
        assert len(changed) == 3
        assert json.loads((kith / "settings.json").read_text(encoding="utf-8"))["model"] ==             "own:" + str(new / "ClaudeApps" / "kithylinai" / "Models" / "kithylin" / "kithylin.gguf")
        assert json.loads((comp / "companion-1" / "companion.json").read_text(encoding="utf-8"))["model"].startswith("own:" + str(new))
        assert json.loads((saves / "doom" / "settings.json").read_text(encoding="utf-8"))["recent"] == [str(new / "Local Storage" / "WADs" / "DOOM.WAD")]
        assert relocate.fix_shared(new) == []                                         # each folder's marker: done once


if __name__ == "__main__":
    test_moves()
    test_shared()
    print("ok")
