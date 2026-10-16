"""The resident loader keeps each era to its own past (run: python -m pytest ClaudeCore/tests, or directly)."""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import residents  # noqa: E402


def _make(root):
    r = root / "Redfawks"
    (r / "eras").mkdir(parents=True)
    (r / "media" / "2001").mkdir(parents=True)
    (r / "media" / "2025").mkdir(parents=True)
    (r / "resident.json").write_text(json.dumps({
        "name": "Redfawks", "tier": "main", "born": "1978-02-12",
        "history": [{"from": 1999, "text": "Met the user on a furry forum"},
                    {"from": 2001, "to": 2025, "text": "Met up with the user at conventions"},
                    {"from": 2017, "to": 2023, "text": "Was in a relationship with the user"}]}), "utf-8")
    (r / "eras" / "2001.json").write_text(json.dumps({"year": 2001, "persona": "2001 me",
                                                      "services": {"aim": {"screen_name": "RedFawks"}}}), "utf-8")
    (r / "eras" / "2011.json").write_text(json.dumps({"year": 2011, "persona": "2011 me",
                                                      "services": {"skype": {"handle": "redfawks.ks"}}}), "utf-8")
    (r / "eras" / "2025.json").write_text("{ this file must never be read before 2025 ", "utf-8")


def run():
    with tempfile.TemporaryDirectory() as tmp:
        residents.RESIDENTS = Path(tmp)
        _make(Path(tmp))
        r01 = residents.load("Redfawks", 2001)
        assert r01.age == 23 and r01.persona == "2001 me" and r01.used_to == []
        assert [h["text"] for h in r01.history] == ["Met the user on a furry forum", "Met up with the user at conventions"]
        assert "to" not in r01.history[1]                       # ongoing in 2001: no end date yet
        assert [p.name for p in r01.media] == ["2001"]          # no 2025 photos in 2001
        opened, real = [], residents._load
        residents._load = lambda p: (opened.append(Path(p).name), real(p))[1]
        r11 = residents.load("Redfawks", 2011)                  # reads 2001 and 2011, never the 2025 file
        residents._load = real
        assert "2025.json" not in opened and "2011.json" in opened and "2001.json" in opened
        assert r11.age == 33 and r11.used_to == ["used to be on AIM as RedFawks (in 2001)"]
        assert all("relationship" not in h["text"] for h in r11.history)
        assert residents.load("Redfawks", 2008) is None          # no era file: not around then
        assert residents.load("Nobody", 2001) is None
    print("residents loader: all checks passed")


def test_loader():
    run()


if __name__ == "__main__":
    run()
