"""Where Soul and Song keeps things: next to the user's own project, so the mind files stay readable by hand.

    Local Storage/Projects/AI LLM Txt Files/
      Mind L0..L6 - ....txt       the user's originals: the templates a new Companion starts from (never changed)
      Companions/
        app.json                  which Companion was open last
        <id>/                     one Companion
          Mind L1..L6 - ....txt   its mind files, the same format as the originals
          companion.json          its settings and where its day is at
          session.json            the current context window (today's conversation)
          Chats/<date>.txt        every conversation, as it happened
          Archive/                each bank as it was before a distillation emptied it"""
from pathlib import Path

HERE = Path(__file__).resolve().parent
TIMELINE = HERE.parents[1]


def project():
    """Local Storage/Projects/<AI LLM Txt Files> (found by its name, whatever the case)."""
    try:
        from claudecore import host
        storage = Path(host.local_storage())
    except Exception:
        storage = TIMELINE / "Local Storage"
    projects = storage / "Projects"
    if projects.is_dir():
        for d in sorted(projects.iterdir()):
            if d.is_dir() and d.name.lower().startswith("ai llm txt"):
                return d
    return projects / "AI LLM Txt Files"


def companions():
    return project() / "Companions"
