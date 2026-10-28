"""Raw Logs: everything a Companion has been through, day by day, from the start (the Raw Logs tab).

Each Companion writes Raw Logs/<day>.jsonl in its folder (Companion._raw): every line shown in the conversation (the
user, the Companion, a guide's prompt, the program's notes, memories), what it hears in an Interlink, and every
question the program asked the model and the answer that came back - including the ones never shown (journal,
reflections, time checks...). One entry a line: {"t", "kind", "who", "text"}.

Days from before the raw log existed come from the conversation logs (Chats/<day>.txt): what was said, if not the
notes and the model's side. A day that has both gets the conversation log's earlier part, then the raw log."""
import json
import re
from pathlib import Path

KINDS = {                        # kind -> (label, filter group)
    "user": ("You", "talk"), "companion": ("Companion", "talk"), "other": ("Another Companion", "talk"),
    "guide": ("Guide", "guide"), "system": ("Note", "notes"), "request": ("Request", "notes"),
    "memory": ("Memory", "memories"), "asked": ("Asked the model", "model"), "answered": ("The model's answer",
                                                                                          "model"),
    "error": ("Error", "notes"),
}
GROUPS = {"talk": "Conversation", "guide": "Guide prompts", "notes": "Notes", "memories": "Memories",
          "model": "Model in and out (raw)"}
CHAT_LINE = re.compile(r"^\[(\d{4}-\d\d-\d\d \d\d:\d\d)\] ([^:\n]{1,60}): ", re.M)


def folder_of(comp_folder):
    return Path(comp_folder) / "Raw Logs"


def days(comp_folder):
    """Every day with something logged, oldest first: {day: approximate entry count}."""
    comp_folder = Path(comp_folder)
    out = {}
    raw = folder_of(comp_folder)
    if raw.is_dir():
        for p in raw.glob("*.jsonl"):
            try:
                out[p.stem] = sum(1 for _ in open(p, encoding="utf-8"))
            except OSError:
                pass
    chats = comp_folder / "Chats"
    if chats.is_dir():
        for p in chats.glob("*.txt"):
            if p.stem not in out:
                try:
                    out[p.stem] = len(CHAT_LINE.findall(p.read_text(encoding="utf-8", errors="replace")))
                except OSError:
                    pass
    return dict(sorted(out.items()))


def _chat_entries(path, names):
    """A conversation log's entries: who's who decided from the names (the user's, the guide, the Companion's)."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    marks = list(CHAT_LINE.finditer(text))
    out = []
    for i, m in enumerate(marks):
        body = text[m.end():marks[i + 1].start() if i + 1 < len(marks) else len(text)].strip()
        who = m.group(2).strip()
        if who in names["user"]:
            kind = "user"
        elif who == "Guided session":
            kind = "guide"
        elif who in names["self"]:
            kind = "companion"
        else:
            kind = "other"
        out.append({"t": m.group(1), "kind": kind, "who": who, "text": body})
    return out


def entries(comp_folder, day, names):
    """A day's entries, oldest first. names: {"user": {...}, "self": {...}} for reading the conversation log."""
    comp_folder = Path(comp_folder)
    raw = []
    p = folder_of(comp_folder) / f"{day}.jsonl"
    if p.exists():
        try:
            with open(p, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            raw.append(json.loads(line))
                        except ValueError:
                            continue
        except OSError:
            pass
    chat = _chat_entries(comp_folder / "Chats" / f"{day}.txt", names)
    if not raw:
        return chat
    first = raw[0].get("t", "")
    return [e for e in chat if e["t"] < first] + raw


def search(comp_folder, text, names, limit=400):
    """Entries anywhere that contain the text (any case), oldest first, with their day."""
    want = text.lower()
    out = []
    for day in days(comp_folder):
        for e in entries(comp_folder, day, names):
            if want in (e.get("text") or "").lower() or want in (e.get("who") or "").lower():
                out.append(dict(e, day=day))
                if len(out) >= limit:
                    return out
    return out
