"""Kithylin AI's settings and chat history, all in kithylinai/Data/ (never in a computer's own data folder, so the
same chats are there on every era and come along when the program is lifted out)."""
import json
import re
import time
import uuid

from . import defaults
from .paths import DATA

SETTINGS_FILE = DATA / "settings.json"
CHATS_DIR = DATA / "chats"
SAVED_DIR = DATA / "saved"

ADULT_FOLDERS = ("Kithy Porn", "Kithy Porn Hyper")


def load_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    tmp.replace(path)


def default_settings():
    return {"model": "", "engine": "auto", "temperature": 0.9, "context": 8192, "max_tokens": 600,
            "text_size": 11, "user_name": "You",
            "background": {"mode": "rotate", "folder": "", "picture": "", "minutes": 4, "dim": 0.58,
                           "skip_adult": True},
            "character": defaults.DEFAULT_CHARACTER,
            "codes": {"furcode": defaults.KITHYLIN_FURCODE, "yiffcode": defaults.KITHYLIN_YIFFCODE},
            "codes_prompt": defaults.codes_prompt(defaults.KITHYLIN_FURCODE, defaults.KITHYLIN_YIFFCODE),
            "show_system": True, "echo_prompts": True, "autoload": True}


class Settings:
    def __init__(self):
        self.values = default_settings()
        saved = load_json(SETTINGS_FILE, {})
        for k, v in saved.items():
            if isinstance(v, dict) and isinstance(self.values.get(k), dict):
                self.values[k] = {**self.values[k], **v}
            else:
                self.values[k] = v

    def __getitem__(self, key):
        return self.values[key]

    def set(self, key, value):
        self.values[key] = value
        save_json(SETTINGS_FILE, self.values)

    def update(self, **kw):
        self.values.update(kw)
        save_json(SETTINGS_FILE, self.values)

    def reset(self, keys=None):
        fresh = default_settings()
        for k in (keys or fresh.keys()):
            self.values[k] = fresh[k]
        save_json(SETTINGS_FILE, self.values)

    def filled(self, key):
        """A prompt setting with {name} replaced by your chat name ('a friend' if it's still 'You')."""
        name = (self.values.get("user_name") or "").strip()
        name = name if name and name.lower() != "you" else "a friend"
        return self.values[key].replace("{name}", name)

    def system_prompt(self):
        """The two prompts together. {name} in them becomes your chat name (the trained models learned to expect
        who they're talking to, as in 'chatting on AIM with ... in 2007')."""
        parts = [self.filled("character").strip(), self.filled("codes_prompt").strip()]
        return "\n\n".join(p for p in parts if p)


def _safe_name(name):
    name = re.sub(r"[^\w\- ().,']+", "_", name).strip(" .") or "chat"
    return name[:80]


class Chat:
    """One conversation: {"id", "title", "model", "created", "updated", "messages": [{"role", "content", "time"}]}.
    System messages (purple) are kept in the history too, but never sent to the model."""

    def __init__(self, data=None, path=None):
        self.data = data or {"id": uuid.uuid4().hex[:12], "title": "", "model": "", "created": time.time(),
                             "updated": time.time(), "messages": []}
        self.path = path or CHATS_DIR / f"{self.data['id']}.json"

    @property
    def messages(self):
        return self.data["messages"]

    def add(self, role, content, **extra):
        m = {"role": role, "content": content, "time": time.time(), **extra}
        self.messages.append(m)
        return m

    def spoken(self):
        """The user's and Kithylin's turns only, for the model."""
        return [m for m in self.messages if m["role"] in ("user", "assistant") and m.get("content")]

    def title(self):
        if self.data.get("title"):
            return self.data["title"]
        first = next((m["content"] for m in self.messages if m["role"] == "user"), "")
        return (first.strip().splitlines()[0][:48] if first.strip() else "New chat")

    def save(self):
        if not self.spoken():
            return
        self.data["updated"] = time.time()
        save_json(self.path, self.data)

    def save_as(self, name):
        """A named copy in Data/saved/ (the working copy stays where it is)."""
        self.data["title"] = name
        path = SAVED_DIR / f"{_safe_name(name)}.json"
        save_json(path, self.data)
        self.save()
        return path

    def export_text(self, path, user_name="You"):
        lines = []
        for m in self.messages:
            who = {"user": user_name, "assistant": "Kithylin", "system": "*"}.get(m["role"], m["role"])
            stamp = time.strftime("%Y-%m-%d %H:%M", time.localtime(m.get("time", 0)))
            lines.append(f"[{stamp}] {who}: {m['content']}")
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def delete(self):
        try:
            self.path.unlink()
        except OSError:
            pass


def list_chats():
    """Every chat, newest first: [(path, title, updated, turns)] from both the working copies and the saved ones."""
    out = []
    for folder in (SAVED_DIR, CHATS_DIR):
        if not folder.is_dir():
            continue
        for p in folder.glob("*.json"):
            d = load_json(p, None)
            if isinstance(d, dict) and d.get("messages"):
                c = Chat(d, p)
                out.append((p, c.title(), d.get("updated", 0), len(c.spoken()), folder is SAVED_DIR))
    out.sort(key=lambda t: -t[2])
    return out


def load_chat(path):
    d = load_json(path, None)
    return Chat(d, path) if isinstance(d, dict) else None


def clear_history():
    n = 0
    for folder in (CHATS_DIR, SAVED_DIR):
        if folder.is_dir():
            for p in folder.glob("*.json"):
                try:
                    p.unlink()
                    n += 1
                except OSError:
                    pass
    return n
