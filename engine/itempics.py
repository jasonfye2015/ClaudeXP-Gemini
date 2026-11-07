"""Which picture an item is (assets/items, by tools/import_icons.py): no Qt here, so the renderer (the drops flying
out of the dead, the things lying about) and the pack (ui/icons.py) choose the same."""
import json
import zlib
from pathlib import Path

from ..game import data as D

ITEMS = Path(__file__).resolve().parents[1] / "assets" / "items"
_map = None


def _mapping():
    global _map
    if _map is None:
        try:
            _map = json.loads((ITEMS / "items.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            _map = {}
    return _map


def sprite_name(it):
    """The sprite file for an item (None: paint it)."""
    M = _mapping()
    if not M:
        return None
    t = it.get("type")
    if t == "gear":
        tiers = M["gear"].get(it["slot"])
        if not tiers:
            return None
        bases = D.GEAR_BASES[it["slot"]]
        tier = bases.index(it["base"]) if it["base"] in bases else 0
        if it.get("rarity", 0) >= 3:
            tier = len(tiers) - 1                                  # (a legendary wears the finest)
        pics = tiers[min(tier, len(tiers) - 1)]
        return pics[zlib.crc32(str(it.get("id", "")).encode()) % len(pics)]
    if t == "wand":
        return M["wands"].get(it["body"])
    if t == "part":
        key = f"core:{it.get('element', 'arcane')}" if it["kind"] == "core" else it["kind"]
        return M["parts"].get(key)
    if t == "potion":
        return M["other"].get("potion:" + it["kind"]) if it["kind"] != "return" else M["other"].get("scroll")
    if t == "scroll":
        return M["other"].get("scroll")
    return None




def drop_picture(what):
    """A drop: "gold", "health", "mana", "scroll", or an item -> its sprite's file name (None when it has none)."""
    M = _mapping()
    if not M:
        return None
    if what == "gold":
        return M["other"].get("gold_pile")
    if what in ("health", "mana"):
        return M["other"].get("potion:" + what)
    if what == "scroll":
        return M["other"].get("scroll")
    if isinstance(what, dict):
        return sprite_name(what)
    return None
