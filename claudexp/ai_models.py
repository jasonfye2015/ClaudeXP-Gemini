"""AI Models: which language models are installed, and which one does which job.

Models live in Local Storage/LLM Models/models/<name>/ - the model's .gguf, an optional mmproj-*.gguf (so it can see
pictures) and an optional info.json ({"title", "source", "licence", "notes", "suggested": ["conversation", ...],
"thinking": true, "chat_template": "chatml"} - the last for models whose file has no chat template; any of
llama.cpp's built-in names: chatml, mistral-v3-tekken, mistral-v7, llama3, gemma...). The folder name is the model's name everywhere.

Jobs (roles):
  conversation  buddies talking with you: AIM, and replies to you on IRC and the MUCK
  background    the life sim (journals, e-mail, catch-up) and ambient IRC / MUCK chatter
  assistant     ClaudeAI's default model
  pictures      used instead whenever a message carries a picture and the chosen model can't see
  clippy        the Office Assistant's tips and 'help'
  coding        Copilot Python Studio's AI Helper
Per-resident overrides give one buddy or regular their own model. The choices live in data/ai_models.json, and
ClaudeAIM's own settings (default model, per-buddy overrides, context size) are kept in step with them, so ClaudeAIM
itself never needs changing."""
import json
import re
import threading
from pathlib import Path

from .paths import DATA

CONFIG = DATA / "ai_models.json"
ROLES = [("conversation", "Buddy conversations", "AIM, and when buddies and regulars talk to you on IRC and the MUCK"),
         ("background", "Background life", "journals, e-mail, catch-up and ambient IRC / MUCK chatter"),
         ("assistant", "ClaudeAI", "the default model in ClaudeAI"),
         ("pictures", "Pictures", "used when a message has a picture the chosen model can't see"),
         ("clippy", "Clippy", "the Office Assistant's tips and 'help'"),
         ("coding", "Python Studio", "the AI Helper that writes and explains code in Copilot Python Studio")]
DEFAULTS = {"engine": "", "max_loaded": 2, "context": 16384, "idle_minutes": 0, "compact_cache": True, "assign": {},
            "overrides": {}}
_lock = threading.RLock()


class Model:
    def __init__(self, folder):
        self.folder = Path(folder)
        self.id = self.folder.name
        ggufs = sorted(f for f in self.folder.glob("*.gguf") if not f.name.lower().startswith(("mmproj", "mtp")))
        self.path = ggufs[0] if ggufs else None
        self.mmproj = next(iter(sorted(self.folder.glob("mmproj*.gguf"))), None)
        try:
            self.info = json.loads((self.folder / "info.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            self.info = {}
        self.title = self.info.get("title") or self.id
        self.size = sum(f.stat().st_size for f in self.folder.glob("*.gguf")) if self.path else 0

    @property
    def vision(self):
        return self.mmproj is not None

    @property
    def thinking(self):
        return bool(self.info.get("thinking"))


def models_root():
    from .llm_server import models_dir
    return models_dir() / "models"


def installed():
    """Every usable model (a folder with a .gguf), smallest first."""
    root = models_root()
    if not root.is_dir():
        return []
    found = [Model(d) for d in sorted(root.iterdir()) if d.is_dir()]
    return sorted((m for m in found if m.path is not None), key=lambda m: m.size)


def get(model_id):
    return next((m for m in installed() if m.id == model_id), None)


def _norm(name):
    return re.sub(r"[^a-z0-9]", "", str(name or "").lower())


# ---- the choices -------------------------------------------------------------------------------------------------

def config():
    with _lock:
        try:
            data = json.loads(CONFIG.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            data = {}
        out = json.loads(json.dumps(DEFAULTS))
        out.update(data)
        return out


def save(data):
    with _lock:
        CONFIG.parent.mkdir(parents=True, exist_ok=True)
        CONFIG.write_text(json.dumps(data, indent=2), encoding="utf-8")
    sync_aim()


def default_for(role, models=None):
    """A sensible model for a job when nothing has been chosen: info.json hints, then size and abilities."""
    models = installed() if models is None else models
    if not models:
        return ""
    hinted = [m for m in models if role in (m.info.get("suggested") or [])]
    if hinted:
        return hinted[0].id
    if role == "clippy":
        return default_for("conversation", models)              # small models make a poor Clippy
    if role == "coding":
        coders = [m for m in models if "coder" in m.id.lower()]
        return (coders or models)[-1].id                        # the biggest coder, else the biggest model
    if role == "background":
        return models[0].id                                     # the smallest
    if role == "pictures":
        seeing = [m for m in models if m.vision]
        return seeing[0].id if seeing else models[0].id
    if role == "assistant":
        return models[-1].id                                    # the biggest
    mid = [m for m in models if m.vision] or models
    return mid[0].id


def model_for(role, resident=None):
    """The model to use for a job (and, for conversations, a particular resident)."""
    models = installed()
    ids = {m.id for m in models}
    cfg = config()
    if resident:
        chosen = cfg["overrides"].get(str(resident))
        if chosen in ids:
            return chosen
    chosen = cfg["assign"].get(role)
    return chosen if chosen in ids else default_for(role, models)


def resolve(name, role="conversation"):
    """Any name a program asks for -> an installed model ('gemma3:4b' finds the 'gemma3-4b' folder; unknown names
    get the job's model, so old settings never break)."""
    models = installed()
    for m in models:
        if m.id == name or _norm(m.id) == _norm(name) or _norm(m.title) == _norm(name):
            return m.id
    return model_for(role)


def vision_model():
    return model_for("pictures")


# ---- keeping ClaudeAIM's settings in step --------------------------------------------------------------------

def sync_aim():
    """Write the conversation model, per-buddy overrides and context size into ClaudeAIM's settings."""
    try:
        from .programs.aim import ensure_aim_path
        ensure_aim_path()
        from claudeaim.contacts import load_contacts
        from claudeaim.storage import Settings
        s = Settings()
        cfg = config()
        contacts, _errors = load_contacts()
        by_name = {c.screen_name.lower(): c.id for c in contacts}
        ids = {m.id for m in installed()}
        overrides = {by_name[n.lower()]: m for n, m in cfg["overrides"].items() if n.lower() in by_name and m in ids}
        want = {"default_model": model_for("conversation") or s["default_model"], "model_overrides": overrides,
                "context_size": int(cfg["context"])}
        if any(s[k] != v for k, v in want.items()):
            s.update(**want)
    except Exception:
        pass


# ---- what's been happening (for the Activity tab) -----------------------------------------------------------

_activity = []


def record(model, tokens, per_second, seconds, kind=""):
    with _lock:
        import time
        _activity.append({"when": time.time(), "model": model, "tokens": tokens, "tps": per_second,
                          "seconds": seconds, "kind": kind})
        del _activity[:-200]


def activity():
    with _lock:
        return list(_activity)
