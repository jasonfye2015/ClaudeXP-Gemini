"""The list of offline Piper voices (piper_voices.json), grouped for the voice pickers."""
import json
from pathlib import Path

CATALOG = Path(__file__).with_name("piper_voices.json")
GROUPS = (("female", "Female voices"), ("male", "Male voices"), ("nonbinary", "Non-binary voices"),
          ("mixed", "Multi-speaker voices (mixed)"))


def _load():
    try:
        return json.loads(CATALOG.read_text(encoding="utf-8")).get("voices", [])
    except (OSError, ValueError, AttributeError):
        return []


ENTRIES = {v["id"]: v for v in _load()}


def label(voice_id):
    v = ENTRIES.get(voice_id)
    if v is None:
        return voice_id
    extra = f"{v['speakers']} speakers" if v["speakers"] > 1 else v["quality"]
    return f"{v['name']} \u2013 {v['accent']}, {extra}"


# id -> label, so older code that looks a voice up by id keeps working
VOICES = {voice_id: label(voice_id) for voice_id in ENTRIES}


def grouped():
    """[(group title, [voice ids])], each group sorted by name then quality (low, medium, high)."""
    order = {"low": 0, "medium": 1, "high": 2}
    out = []
    for key, title in GROUPS:
        ids = sorted((v["id"] for v in ENTRIES.values() if v["gender"] == key),
                     key=lambda i: (ENTRIES[i]["name"].lower(), ENTRIES[i]["accent"], order.get(ENTRIES[i]["quality"], 9)))
        if ids:
            out.append((title, ids))
    return out


def size_mb(voice_id):
    return ENTRIES.get(voice_id, {}).get("mb", 63)
