"""The sticker library, shared by the Sticker Manager and every chat program in every era.

Each pack is a folder in Local Storage/Sticker Packs. What a sticker *means* - an emoji and a few words ("😊",
"happy tail wag") - is kept in Sticker Packs/stickers.json, along with which pack each contact favours. To the
residents a sticker is only its emoji and meaning: they send one by starting or ending a message with the emoji, and
a sticker the user sends reaches them as "[sticker: 😊 happy tail wag]". The pictures are for the user.

stickers.json:
    {"packs": {"<pack>": {"<file>": {"emoji": "😊", "meaning": "happy tail wag", "suggested": false}}},
     "favorites": {"<contact>": "<pack>"}}
"""
import json
import random
from pathlib import Path

from claudecore import host

EXTS = {".webp", ".png", ".jpg", ".jpeg", ".gif"}
FILE_NAME = "stickers.json"


def root():
    folder = host.local_storage() / "Sticker Packs"
    return folder if folder.is_dir() else None


def _file():
    r = root()
    return r / FILE_NAME if r is not None else None


def load():
    f = _file()
    try:
        data = json.loads(f.read_text(encoding="utf-8")) if f is not None else {}
    except (OSError, ValueError):
        data = {}
    data.setdefault("packs", {})
    data.setdefault("favorites", {})
    return data


def save(data):
    f = _file()
    if f is None:
        return
    tmp = f.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
    tmp.replace(f)


def packs():
    r = root()
    if r is None:
        return []
    return sorted((d for d in r.iterdir() if d.is_dir() and not d.name.startswith((".", "_"))),
                  key=lambda d: d.name.lower())


def stickers(pack):
    """The sticker files in a pack folder, in name order."""
    folder = Path(pack)
    try:
        return sorted((f for f in folder.iterdir() if f.is_file() and f.suffix.lower() in EXTS),
                      key=lambda f: f.name.lower())
    except OSError:
        return []


def assigned(data, pack_name):
    """{file name: {"emoji", "meaning", "suggested"}} for a pack (only stickers with an emoji)."""
    return {k: v for k, v in data["packs"].get(pack_name, {}).items() if v.get("emoji")}


# ---- for the chat programs ---------------------------------------------------------------------------------------
def favorite_pack(contact, data=None):
    """The pack a contact favours (chosen at random the first time, among packs with emojis assigned)."""
    own = data is None
    data = data or load()
    key = str(contact).lower()
    chosen = data["favorites"].get(key)
    ready = [p.name for p in packs() if assigned(data, p.name)]
    if chosen in ready:
        return chosen
    if not ready:
        return None
    chosen = random.choice(ready)
    data["favorites"][key] = chosen
    if own:
        save(data)
    return chosen


def menu_for(contact):
    """[(emoji, meaning, path)] the contact can send (their favourite pack, one sticker per emoji)."""
    data = load()
    pack = favorite_pack(contact, data)
    save(data)
    if pack is None:
        return []
    folder = root() / pack
    seen, out = set(), []
    for name, info in sorted(assigned(data, pack).items()):
        if info["emoji"] not in seen and (folder / name).exists():
            seen.add(info["emoji"])
            out.append((info["emoji"], info.get("meaning", ""), folder / name))
    return out


def prompt_lines(contact):
    """What to tell a resident about their stickers (empty when they have none)."""
    menu = menu_for(contact)
    if not menu:
        return ""
    choices = ", ".join(f"{e} ({m})" if m else e for e, m, _p in menu)
    return ("You can send a sticker now and then: put ONE of these emojis at the very start or the very end of your "
            f"message and it shows up as a sticker - {choices}. Don't overdo it. When the user sends you a sticker "
            "it arrives as [sticker: emoji meaning].")


def sticker_in(contact, text):
    """(path, emoji, meaning) when a message starts or ends with one of the contact's sticker emojis, else None."""
    stripped = (text or "").strip()
    if not stripped:
        return None
    for emoji, meaning, path in sorted(menu_for(contact), key=lambda m: -len(m[0])):
        if stripped.startswith(emoji) or stripped.endswith(emoji):
            return path, emoji, meaning
    return None


def describe(path):
    """How a sticker the user sends reads to a resident: '[sticker: 😊 happy tail wag]'."""
    path = Path(path)
    info = load()["packs"].get(path.parent.name, {}).get(path.name, {})
    if not info.get("emoji"):
        return "[sticker]"
    return f"[sticker: {info['emoji']} {info.get('meaning', '')}]".replace(" ]", "]")
