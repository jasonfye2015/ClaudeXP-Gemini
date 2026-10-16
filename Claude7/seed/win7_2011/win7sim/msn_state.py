"""Per-fursona MSN preferences, wiped with user data rather than machine settings."""

import json
import re
from pathlib import Path

from . import config


class MSNState:
    def __init__(self, profile_id):
        if not re.fullmatch(r"[A-Za-z0-9_-]+", profile_id or ""):
            raise ValueError("MSN needs a valid active fursona ID.")
        self.path = config.USER_PROFILES / profile_id / "msn.json"
        self.data = {"version": 1, "blocked": [], "user_status": "Offline",
                     "away_message": "", "last_received": {}, "show_tray_icon": True}
        self.error = ""
        self.read_only = False
        try:
            if self.path.exists():
                raw = json.loads(self.path.read_text(encoding="utf-8"))
                if (not isinstance(raw, dict) or raw.get("version") != 1
                    or not isinstance(raw.get("blocked"), list)
                    or not all(isinstance(item, str) for item in raw["blocked"])
                    or raw.get("user_status") not in ("Online", "Away", "Do not disturb", "Offline")
                    or not isinstance(raw.get("away_message"), str)
                    or ("show_tray_icon" in raw and not isinstance(raw["show_tray_icon"], bool))
                    or not isinstance(raw.get("last_received"), dict)
                    or not all(isinstance(k, str) and isinstance(v, str)
                               for k, v in raw["last_received"].items())):
                    raise ValueError("Invalid MSN preferences")
                self.data = raw
                self.data.setdefault("show_tray_icon", True)
        except (OSError, UnicodeError, ValueError) as exc:
            self.error = f"MSN preferences could not be loaded; original file preserved: {exc}"
            self.read_only = True

    def save(self):
        if self.read_only:
            return False
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            if self.path.is_symlink() or self.path.parent.is_symlink():
                raise OSError("Refusing to save MSN preferences through a symbolic link.")
            config._atomic_write_private_json(self.path, json.dumps(self.data, indent=2) + "\n")
        except (OSError, ValueError) as exc:
            self.error = f"MSN preferences could not be saved: {exc}"
            return False
        self.error = ""
        return True
