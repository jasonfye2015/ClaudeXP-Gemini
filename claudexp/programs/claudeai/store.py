"""ClaudeAI's saved chats and settings (data/claudeai)."""
import time
import uuid

from ...paths import DATA
from ..people import load_json, save_json

STORE_DIR = DATA / "claudeai"
CHATS_FILE = STORE_DIR / "chats.json"
SETTINGS_FILE = STORE_DIR / "settings.json"

DEFAULT_INSTRUCTIONS = ("You are ClaudeAI, a helpful, thoughtful and friendly AI assistant running locally on "
                        "this computer. Answer clearly, use Markdown for structure when it helps, and say so "
                        "when you're not sure about something.")


class Settings:
    def __init__(self):
        self.values = {"model": "", "instructions": DEFAULT_INSTRUCTIONS, "temperature": 0.7,
                       "think": False, "sidebar": True}
        self.values.update(load_json(SETTINGS_FILE, {}))

    def __getitem__(self, key):
        return self.values[key]

    def set(self, key, value):
        self.values[key] = value
        save_json(SETTINGS_FILE, self.values)


class Chats:
    def __init__(self):
        self.chats = load_json(CHATS_FILE, [])

    def save(self):
        save_json(CHATS_FILE, self.chats)

    def new(self, model):
        chat = {"id": uuid.uuid4().hex[:12], "title": "New chat", "pinned": False, "titled": False,
                "created": time.time(), "updated": time.time(), "model": model, "messages": []}
        self.chats.append(chat)
        return chat

    def get(self, chat_id):
        return next((c for c in self.chats if c["id"] == chat_id), None)

    def delete(self, chat_id):
        self.chats = [c for c in self.chats if c["id"] != chat_id]
        self.save()

    def touch(self, chat):
        chat["updated"] = time.time()
        self.save()

    def listed(self, query=""):
        """(pinned, recents), newest first, skipping empty chats, filtered by a search query."""
        q = query.strip().lower()

        def match(c):
            if not c["messages"]:
                return False
            if not q:
                return True
            return q in c["title"].lower() or any(q in m["content"].lower() for m in c["messages"])

        shown = sorted((c for c in self.chats if match(c)), key=lambda c: -c["updated"])
        return [c for c in shown if c["pinned"]], [c for c in shown if not c["pinned"]]
