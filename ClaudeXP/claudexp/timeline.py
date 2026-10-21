"""ClaudeXP as EPOCH-2001 in the Claude Timeline.

When ClaudeXP sits in a Claude Timeline folder (beside ClaudeLauncher), the launcher owns two things:
  - Profile/profile.json: the user's identity across every era (name, fursona, online handle, picture). Setup and
    reinstalls take it from here instead of asking 'Choose your fursona' and 'Who will use this computer?'.
  - ClaudeLauncher/settings.json: the launcher's Config, e.g. "local_storage" - where the shared Local Storage is
    (the full archive on an external SSD, or the trimmed copy beside ClaudeXP).
A ClaudeXP on its own has neither, and behaves as it always has.
"""
import json
import os

from .paths import ROOT

TIMELINE = ROOT.parent
LAUNCHER = TIMELINE / "ClaudeLauncher"
PROFILE_FILE = TIMELINE / "Profile" / "profile.json"
SETTINGS_FILE = LAUNCHER / "settings.json"
FORMAT_ENV = "CLAUDE_TIMELINE_FORMAT"          # set by the launcher's 'Load and Format'


def _load(path):
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def active():
    """Is this ClaudeXP part of a Claude Timeline?"""
    return LAUNCHER.is_dir()


def profile():
    """The user's Timeline identity ({"name", "fursona", "handle", "picture"}), or None."""
    if not active():
        return None
    data = _load(PROFILE_FILE)
    return data if data.get("name") else None


def user_codes():
    """The user's Furry Code and YIFF Code ({"furcode", "yiffcode"}): their own from the launcher, or else their
    fursona preset's defaults. {} when there are none."""
    p = profile() or {}
    if (p.get("codes") or {}).get("furcode") or (p.get("codes") or {}).get("yiffcode"):
        return dict(p["codes"])
    if p.get("fursona"):
        preset = _load(TIMELINE / "ClaudeXP" / "Program Files" / "The Fur Directory" / "user fursonas" /
                       p["fursona"] / "profile.json")
        return dict(preset.get("codes") or {})
    return {}


def setting(key, default=None):
    return _load(SETTINGS_FILE).get(key, default) if active() else default


def format_requested():
    """The launcher's 'Load and Format': boot straight into System Recovery. (Read once; the variable is cleared so
    Setup's own restarts don't format again.)"""
    if os.environ.get(FORMAT_ENV):
        os.environ.pop(FORMAT_ENV, None)
        return True
    return False
