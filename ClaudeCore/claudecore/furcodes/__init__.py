"""Furry Code 2.0 and YIFF Code 3.0: shared by the launcher, every era and the Fur Codes program.

furcode / yiffcode   read, write and describe each code
steering             what a resident's codes and the user's mean for how they get along (for personas)
editor               the encoder/decoder widget
Here: the user's own codes (Profile/profile.json, or their fursona preset's defaults) and who shows a YIFF Code."""
import json
import random
from pathlib import Path

TIMELINE = Path(__file__).resolve().parents[3]
PROFILE = TIMELINE / "Profile" / "profile.json"
PRESETS = TIMELINE / "ClaudeXP" / "Program Files" / "The Fur Directory" / "user fursonas"


def _load(path):
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def user_codes():
    """{"furcode", "yiffcode"}: the user's own from the launcher, or else their fursona preset's; {} if none."""
    me = _load(PROFILE)
    own = me.get("codes") or {}
    if own.get("furcode") or own.get("yiffcode"):
        return dict(own)
    if me.get("fursona"):
        return dict(_load(PRESETS / me["fursona"] / "profile.json").get("codes") or {})
    return {}


def save_user_codes(codes):
    """Make these the user's own codes (the residents go by them from the next time a computer starts)."""
    me = _load(PROFILE)
    if not me.get("name"):
        return False
    me["codes"] = {"furcode": codes.get("furcode", ""), "yiffcode": codes.get("yiffcode", "")}
    tmp = PROFILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(me, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(PROFILE)
    return True


def yiff_public(name, yiffcode_text):
    """Does this resident show their YIFF Code in their profiles? About a third of those who don't keep it private."""
    if not yiffcode_text:
        return False
    from . import yiffcode
    v = yiffcode.parts(yiffcode_text)["categories"].get("V") or {}
    return v.get("q") not in (None, "No", "Ne", "Ce", "Tr") and random.Random(f"yiff-public:{name}").random() < 0.3
