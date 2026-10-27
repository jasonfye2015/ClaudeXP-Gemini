"""Stands in for ClaudeXP's display settings in the .scr: the screen saver's own settings, kept in
%APPDATA%\\Claude Entertainment System\\settings.json (which games, how long, the order, Super Claude Bros' options)."""
import json
import os
from pathlib import Path

FILE = Path(os.environ.get("APPDATA") or Path.home()) / "Claude Entertainment System" / "settings.json"


class _Settings:
    def __init__(self):
        self.data = {}
        try:
            self.data.update(json.loads(FILE.read_text(encoding="utf-8")))
        except (OSError, ValueError):
            pass

    def _save(self):
        FILE.parent.mkdir(parents=True, exist_ok=True)
        FILE.write_text(json.dumps(self.data, indent=2), encoding="utf-8")


_settings = None


def get():
    global _settings
    if _settings is None:
        _settings = _Settings()
    return _settings
