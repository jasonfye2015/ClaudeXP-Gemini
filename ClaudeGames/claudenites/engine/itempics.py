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
        if it.get("rarity", 0) >= 4:
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
    if t == "larder":
        return larder_picture(it["key"])
    if t == "crop":
        return crop_picture(it["crop"], it["stage"])
    return None




def larder_picture(key):
    """A larder key -> its sprite: seeds a pouch of them, a crop its produce, meat/fish/mushroom/honey theirs, a meal
    its dish (a recipe's picture is a food key, or "veg:<crop>")."""
    M = _mapping()
    if not M:
        return None
    kind, _, k = key.partition(":")
    if kind == "seed":
        return M["food"].get("seeds")
    if kind == "raw":
        return M["produce"].get(k) or M["food"].get(k)
    if kind == "cooked":
        from ..game.food import RECIPES
        pic = RECIPES[k][1]
        return M["produce"].get(pic[4:]) if pic.startswith("veg:") else M["food"].get(pic)
    return None


def crop_picture(crop, stage):
    """A crop growing: stage 0 the sown earth, 1-4 its four stages (4 ripe)."""
    M = _mapping()
    if not M:
        return None
    if stage == 0:
        return M["crops"].get("sown")
    frames = M["crops"].get(crop)
    return frames[min(3, stage - 1)] if frames else None


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
    if isinstance(what, str) and ":" in what:
        return larder_picture(what)
    return None
