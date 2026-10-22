"""Claude11 as WORKSTATION-2025 in the Claude Timeline: the launcher's profile (who you are in every era), its settings
(where Local Storage is) and its 'Load and Format' request."""
import json
import os

from .paths import TIMELINE, XP_ROOT

LAUNCHER = TIMELINE / "ClaudeLauncher"
PROFILE_FILE = TIMELINE / "Profile" / "profile.json"
SETTINGS_FILE = LAUNCHER / "settings.json"
FORMAT_ENV = "CLAUDE_TIMELINE_FORMAT"


def _load(path):
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def active():
    return LAUNCHER.is_dir()


def profile():
    """The user's Timeline identity ({"name", "fursona", "handle", "picture"}), or None."""
    data = _load(PROFILE_FILE)
    return data if data.get("name") else None


def user_codes():
    """The user's Furry Code and YIFF Code: their own from the launcher, or else their fursona preset's."""
    p = profile() or {}
    codes = p.get("codes") or {}
    if codes.get("furcode") or codes.get("yiffcode"):
        return dict(codes)
    if p.get("fursona"):
        preset = _load(XP_ROOT / "Program Files" / "The Fur Directory" / "user fursonas" / p["fursona"] / "profile.json")
        return dict(preset.get("codes") or {})
    return {}


def setting(key, default=None):
    return _load(SETTINGS_FILE).get(key, default) if active() else default


def format_requested():
    """The launcher's 'Load and Format': boot straight into Windows Setup (read once)."""
    if os.environ.get(FORMAT_ENV):
        os.environ.pop(FORMAT_ENV, None)
        return True
    return False
