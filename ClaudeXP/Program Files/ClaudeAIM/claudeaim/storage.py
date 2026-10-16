"""Settings and per-contact chat history, saved as JSON under data/."""
import json
import os
from datetime import datetime

from . import paths

DEFAULTS = {
    "screen_name": "",
    "password": "",
    "save_password": False,
    "auto_login": False,
    "skip_dialup": False,
    "away_message": "",
    "buddy_icon": "",
    "default_model": "gemma3:4b",
    "model_overrides": {},
    "context_size": 8192,
    "sounds": True,
    "im_size": None,         # last Instant Message window size, [width, height]
    # Share of the whole buddy list already online when you log in (from those awake).
    "online_at_login": 0.5,
    # Speeds up contact timers (online/offline/away/scripts). 1.0 = real time.
    "time_scale": 1.0,
}


def _write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, path)


def _read_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


class Settings:
    def __init__(self):
        self.path = paths.DATA / "settings.json"
        self.values = dict(DEFAULTS)
        self.values.update(_read_json(self.path, {}))

    def __getitem__(self, key):
        return self.values.get(key, DEFAULTS.get(key))

    def set(self, key, value):
        self.values[key] = value
        self.save()

    def update(self, **kwargs):
        self.values.update(kwargs)
        self.save()

    def save(self):
        _write_json(self.path, self.values)


class History:
    """Every message between the user and one contact.

    Entry kinds:
      user          - typed by the user
      contact       - sent by the contact
      auto          - the user's away message, auto-sent to the contact
      contact_auto  - the contact's away message, auto-sent to the user
      system        - local notice, never sent to the model
    """

    def __init__(self, contact_id: str):
        self.path = paths.HISTORY / f"{contact_id}.json"
        data = _read_json(self.path, {})
        self.messages: list[dict] = data.get("messages", [])
        self.unread: bool = data.get("unread", False)

    def add(self, kind: str, text: str, image: str = "", **extra) -> dict:
        entry = {"kind": kind, "text": text, "ts": datetime.now().astimezone().isoformat(timespec="seconds")}
        if image:
            entry["image"] = image  # contact: filename in their folder; user: path under data/
        entry.update(extra)         # e.g. held=True: sent while they were offline
        self.messages.append(entry)
        self.save()
        return entry

    def release_held(self) -> bool:
        """Deliver messages that were sent while the contact was offline. True if there were any."""
        held = [m for m in self.messages if m.pop("held", False)]
        if held:
            self.save()
        return bool(held)

    def set_unread(self, value: bool):
        if self.unread != value:
            self.unread = value
            self.save()

    def save(self):
        _write_json(self.path, {"unread": self.unread, "messages": self.messages})
