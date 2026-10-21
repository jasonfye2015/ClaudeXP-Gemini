"""The user's identity across the Timeline (Profile/profile.json), and the launcher's settings.

Every computer's Setup takes the account from here: {"name", "fursona" (a preset id or null), "handle", "picture"}.
The fursona presets are, for now, ClaudeXP's (Program Files/The Fur Directory/user fursonas/<id>/).
"""
import json
from pathlib import Path

from .systems import TIMELINE

PROFILE_FILE = TIMELINE / "Profile" / "profile.json"
SETTINGS_FILE = TIMELINE / "ClaudeLauncher" / "settings.json"
PRESETS = TIMELINE / "ClaudeXP" / "Program Files" / "The Fur Directory" / "user fursonas"
PICTURE_EXTS = (".png", ".jpg", ".jpeg", ".gif", ".bmp")


def _load(path):
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def _save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)


# ---- the identity -----------------------------------------------------------------------------------------
def load():
    data = _load(PROFILE_FILE)
    return data if data.get("name") else None


def save(name, fursona=None, handle=None, codes=None):
    """codes: {"furcode", "yiffcode"} - the user's own; None keeps the ones already saved."""
    old = _load(PROFILE_FILE)
    data = {"name": name.strip(), "fursona": fursona or None, "handle": (handle or name).strip(),
            "picture": f"fursona:{fursona}" if fursona else None}
    codes = old.get("codes") if codes is None else codes
    if codes and (codes.get("furcode") or codes.get("yiffcode")):
        data["codes"] = {"furcode": codes.get("furcode", ""), "yiffcode": codes.get("yiffcode", "")}
    _save(PROFILE_FILE, data)
    return data


def save_codes(codes):
    data = _load(PROFILE_FILE)
    if not data.get("name"):
        return
    data["codes"] = {"furcode": codes.get("furcode", ""), "yiffcode": codes.get("yiffcode", "")}
    _save(PROFILE_FILE, data)


def codes(me=None):
    """The user's codes: their own, or else their fursona preset's defaults."""
    me = me if me is not None else (load() or {})
    own = me.get("codes") or {}
    if own.get("furcode") or own.get("yiffcode"):
        return dict(own)
    pr = preset(me.get("fursona")) if me.get("fursona") else None
    return dict(pr.codes) if pr else {}


def suggestion():
    """For the first run: the account ClaudeXP already has, so the identity matches the existing install."""
    xp = _load(TIMELINE / "ClaudeXP" / "data" / "user.json")
    if not xp.get("name"):
        return {}
    return {"name": xp["name"], "fursona": xp.get("fursona"),
            "handle": (xp.get("online") or {}).get("handle") or xp["name"]}


class Preset:
    def __init__(self, folder):
        self.folder = Path(folder)
        self.id = self.folder.name
        data = _load(self.folder / "profile.json")
        self.name = data.get("fur_name") or self.id
        self.handle = data.get("handle") or self.name
        sona = data.get("fursona") or {}
        self.summary = data.get("summary") or sona.get("description") or ""
        self.species = sona.get("species", "")
        self.codes = data.get("codes") or {}            # its default Furry Code and YIFF Code

    def picture(self):
        for stem in ("account", "buddy_icon"):
            for ext in PICTURE_EXTS:
                p = self.folder / f"{stem}{ext}"
                if p.exists():
                    return p
        return None


def presets():
    if not PRESETS.is_dir():
        return []
    return [Preset(p) for p in sorted(PRESETS.iterdir(), key=lambda p: p.name.lower())
            if p.is_dir() and (p / "profile.json").exists()]


def preset(pid):
    return next((p for p in presets() if p.id == pid), None)


# ---- settings ---------------------------------------------------------------------------------------------
def setting(key, default=None):
    return _load(SETTINGS_FILE).get(key, default)


def set_setting(key, value):
    data = _load(SETTINGS_FILE)
    if value is None:
        data.pop(key, None)
    else:
        data[key] = value
    _save(SETTINGS_FILE, data)
