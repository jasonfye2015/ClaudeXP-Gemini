"""CopilotAI chat history and settings, stored separately from ClaudeAI."""
import time
import uuid

from claudecore.jsonfile import load_json, save_json
from claudecore import host

STORE_DIR = host.data("copilotai")         # this computer's chats
CHATS_FILE = STORE_DIR / "chats.json"
SETTINGS_FILE = STORE_DIR / "settings.json"

DEFAULT_INSTRUCTIONS = (
    "You are CopilotAI, a helpful, thoughtful and friendly assistant running locally on this computer. "
    "Answer clearly, use Markdown when it helps, and say when you are unsure."
)


class Settings:
    DEFAULTS = {
        "model": "",
        "temperature": 0.7,
        "context": 8192,
        "instructions": DEFAULT_INSTRUCTIONS,
        "think": False,
        "sidebar": True,
        "auto_listen": False,
        "voice_id": "en_US-lessac-medium",
        "speak_replies": True,
        "speech_rate": 1.0,
        "auto_title": True,
        "image_tool": True,
        "image_model": "sd15",
        "image_steps": 25,
        "image_free_memory": True,
    }

    def __init__(self):
        self.values = dict(self.DEFAULTS)
        self.values.update(load_json(SETTINGS_FILE, {}))

    def __getitem__(self, key):
        return self.values[key]

    def set(self, key, value):
        self.values.update(load_json(SETTINGS_FILE, {}))
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
        return next((chat for chat in self.chats if chat["id"] == chat_id), None)

    def delete(self, chat_id):
        self.chats = [chat for chat in self.chats if chat["id"] != chat_id]
        self.save()

    def touch(self, chat):
        chat["updated"] = time.time()
        self.save()

    def listed(self, query=""):
        query = query.strip().lower()

        def matches(chat):
            if not chat.get("messages"):
                return False
            if not query:
                return True
            return query in chat["title"].lower() or any(
                query in message.get("content", "").lower() for message in chat["messages"])

        shown = sorted((chat for chat in self.chats if matches(chat)), key=lambda chat: -chat["updated"])
        return ([chat for chat in shown if chat["pinned"]],
                [chat for chat in shown if not chat["pinned"]])
