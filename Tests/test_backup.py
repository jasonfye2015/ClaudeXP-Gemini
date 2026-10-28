"""Backup and restore, on a make-believe Timeline in a scratch folder: the settings (and parts added since they were
saved), a backup of two parts and putting it back, and every part pointing at a folder that's really there."""
import json
import zipfile

import support

from claudecore import backup as B


def _fake_timeline():
    root = support.scratch("timeline")
    (root / "ClaudeGames" / "Saves").mkdir(parents=True, exist_ok=True)
    (root / "ClaudeGames" / "Saves" / "claudecity.json").write_text('{"population": 5000}', encoding="utf-8")
    lyra = root / "Local Storage" / "Projects" / "AI LLM Txt Files" / "Companions" / "companion-1"
    (lyra / "Chats").mkdir(parents=True, exist_ok=True)
    (lyra / "companion.json").write_text('{"name": "Lyra"}', encoding="utf-8")
    (lyra / "Chats" / "2026-10-28.txt").write_text("Hello, Lyra.\n", encoding="utf-8")
    B.TIMELINE = root
    B.SETTINGS = root / "Profile" / "backup.json"
    return root, lyra


def test_settings_remember_new_parts():
    """Settings: a part that's on by default is switched on for settings saved before it existed, and stays off once unticked"""
    _fake_timeline()
    assert "companions" in B.settings()["parts"], B.settings()["parts"]
    B.SETTINGS.parent.mkdir(parents=True, exist_ok=True)
    B.SETTINGS.write_text(json.dumps({"parts": ["saves", "xp"]}), encoding="utf-8")       # (saved before Companions)
    assert B.settings()["parts"] == ["saves", "xp", "companions"], B.settings()["parts"]
    B.save_settings({**B.settings(), "parts": ["saves"]})
    assert B.settings()["parts"] == ["saves"], B.settings()["parts"]


def test_backup_and_restore():
    """A backup of the game saves and the Companions, then put back over changed files (with a safety backup first)"""
    root, lyra = _fake_timeline()
    dest = support.scratch("backups")
    made = B.create(["saves", "companions"], dest, label="test")
    with zipfile.ZipFile(made) as z:
        names = set(z.namelist())
    assert "ClaudeGames/Saves/claudecity.json" in names, names
    assert "Local Storage/Projects/AI LLM Txt Files/Companions/companion-1/Chats/2026-10-28.txt" in names, names
    assert B.manifest(made)["parts"] == ["saves", "companions"]
    (root / "ClaudeGames" / "Saves" / "claudecity.json").write_text('{"population": 0}', encoding="utf-8")
    (lyra / "Chats" / "2026-10-28.txt").unlink()
    (lyra / "companion.json").write_text('{"name": "someone else"}', encoding="utf-8")
    safety = B.restore(made, ["saves", "companions"])
    assert json.loads((root / "ClaudeGames" / "Saves" / "claudecity.json").read_text())["population"] == 5000
    assert (lyra / "Chats" / "2026-10-28.txt").read_text(encoding="utf-8") == "Hello, Lyra.\n"
    assert json.loads((lyra / "companion.json").read_text())["name"] == "Lyra"
    assert safety is not None and safety.exists(), "no safety backup was made first"
    assert not list(root.rglob("*.restoring-*")), "a set-aside copy was left behind"


def test_parts_point_at_real_folders():
    """Every backup part points at something that's really there (a moved folder would quietly drop out of backups)"""
    support.needs(support.LOCAL_STORAGE, "Local Storage")
    missing = []
    for key, (label, paths, _on, _what) in B.PARTS.items():
        if not any((support.TIMELINE / p).exists() for p in paths):
            missing.append(f"{label}: {', '.join(paths)}")
    assert not missing, "\n".join(missing)


def test_companions_never_restored_under_a_running_computer():
    """The Companions can't be restored while a computer (and so maybe Soul and Song) is running"""
    assert "companions" in B.SHARED
    ui = (support.CORE / "claudecore" / "backup_ui.py").read_text(encoding="utf-8")
    launcher = (support.TIMELINE / "ClaudeLauncher" / "systec" / "ui.py").read_text(encoding="utf-8")
    assert "B.SHARED" in ui and "B.SHARED" in launcher, "the backup panels don't block the shared parts"


if __name__ == "__main__":
    support.main(globals())
