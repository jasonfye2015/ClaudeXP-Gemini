"""The item pictures: copied from two CC0 sprite sets kept in Local Storage into assets/items/, with the map of which
picture is which item (assets/items/items.json; ui/icons.py reads it).

  Dungeon Crawl Stone Soup's tiles (CC0; Local Storage/Dungeon Crawl - Sprites) - the robes, hats, gloves, boots,
    rings, amulets and wands, and the gold piles.
  Henrique Lazarini (7Soul1)'s "496 pixel art icons for medieval/fantasy RPG" (CC0; opengameart.org/content/
    496-pixel-art-icons-for-medievalfantasy-rpg, kept in Local Storage/Claudenites icons/7soul-496-rpg-icons) -
    the gems and the elements' runes for the wand parts, the potions, the scroll and the coin.

    python tools/import_icons.py"""
import json
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STORAGE = ROOT.parents[1] / "Local Storage"
DC = STORAGE / "Dungeon Crawl - Sprites" / "Dungeon Crawl Stone Soup Full" / "item"
S7 = STORAGE / "Claudenites icons" / "7soul-496-rpg-icons" / "496_RPG_icons.zip"
OUT = ROOT / "assets" / "items"

# gear: slot -> five tiers (the GEAR_BASES' order), each a few pictures to vary between
GEAR = {
    "hat": [["armor/headgear/cap_1", "armor/headgear/cap_2"], ["armor/headgear/hat_1", "armor/headgear/hat_2"],
            ["armor/headgear/wizard_hat_1", "armor/headgear/hat_3"], ["armor/headgear/cornuthaum", "armor/headgear/elven_leather_helm"],
            ["armor/headgear/wizard_hat_2", "armor/headgear/cornuthaum"]],
    "robe": [["armor/torso/robe_1_old", "armor/torso/robe_1_new"], ["armor/torso/robe_2_old", "armor/torso/robe_2_new"],
             ["armor/torso/robe_3", "armor/torso/robe_2_new"], ["armor/torso/robe_ego_1", "armor/torso/robe_ego_2"],
             ["armor/torso/robe_art_1", "armor/torso/robe_art_2"]],
    "gloves": [["armor/hands/glove_1_old", "armor/hands/glove_1_new"], ["armor/hands/glove_2_old", "armor/hands/glove_2_new"],
               ["armor/hands/glove_3_old", "armor/hands/glove_3_new"], ["armor/hands/glove_4_old", "armor/hands/glove_4_new"],
               ["armor/hands/glove_5", "armor/hands/glove_4_gauntlets"]],
    "boots": [["armor/feet/low_boots", "armor/feet/boots_1_brown_old"], ["armor/feet/boots_1_brown_new", "armor/feet/boots_3_stripe_old"],
              ["armor/feet/boots_3_stripe_new", "armor/feet/boots_4_green"], ["armor/feet/boots_2_jackboots", "armor/feet/boots_4_green"],
              ["armor/feet/boots_iron_2", "armor/feet/boots_2_jackboots"]],
    "ring": [["ring/copper", "ring/bronze", "ring/brass"], ["ring/silver", "ring/ring_plain_blue", "ring/ring_plain_green"],
             ["ring/gold", "ring/ring_ruby", "ring/ring_sapphire", "ring/ring_topaz"], ["ring/moonstone", "ring/opal", "ring/pearl"],
             ["ring/steel", "ring/diamond", "ring/ring_shiny", "ring/tourmaline"]],
    "amulet": [["amulet/bone_gray", "amulet/cylinder_gray"], ["amulet/stone_1_green", "amulet/stone_2_red", "amulet/ring_red"],
               ["amulet/celtic_blue", "amulet/celtic_red", "amulet/cameo_blue"], ["amulet/stone_3_blue", "amulet/crystal_white", "amulet/eye_cyan"],
               ["amulet/penta_orange", "amulet/face_1_gold", "amulet/crystal_red"]],
}
# the ten wand bodies
WANDS = {"birch": "wand/gem_wood_new", "willow": "wand/gem_wood_old", "ash": "wand/gem_bronze_new",
         "yew": "wand/gem_copper_new", "bone": "wand/gem_bone_new", "ironbark": "wand/gem_iron_new",
         "crystal": "wand/gem_glass_new", "emberwood": "wand/gem_brass_new", "starsteel": "wand/gem_silver_new",
         "heartwood": "wand/gem_gold_new"}
# the wand parts (cores by their element), the potions, the scroll, the coin: 7Soul1's
PARTS = {"core:fire": "S_Fire03", "core:frost": "S_Ice02", "core:storm": "S_Thunder03", "core:venom": "S_Poison05",
         "core:arcane": "S_Magic03", "lens": "I_Diamond", "splitter": "I_Crystal01", "focus": "I_Opal",
         "quickener": "I_Feather01", "seeker": "I_Eye", "rebound": "I_Sapphire", "piercer": "I_Amethist"}
OTHER = {"potion:health": "P_Red01", "potion:mana": "P_Blue01", "scroll": "I_Scroll", "coin": "I_GoldCoin"}
GOLD_PILE = "gold/gold_pile_10"


def main():
    if not DC.is_dir() or not S7.exists():
        print("The sprite sets aren't in Local Storage (see this file's top).")
        return 1
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*.png"):                               # (only what the map names)
        old.unlink()
    mapping = {"gear": {}, "wands": {}, "parts": {}, "other": {}, "credits": (
        "Item pictures: Dungeon Crawl Stone Soup tiles (CC0) and Henrique Lazarini (7Soul1)'s 496 pixel art icons "
        "for medieval/fantasy RPG (CC0)")}

    def dc(rel):
        name = "dc_" + rel.replace("/", "_") + ".png"
        shutil.copyfile(DC / (rel + ".png"), OUT / name)
        return name
    for slot, tiers in GEAR.items():
        mapping["gear"][slot] = [[dc(r) for r in tier] for tier in tiers]
    for body, rel in WANDS.items():
        mapping["wands"][body] = dc(rel)
    mapping["other"]["gold_pile"] = dc(GOLD_PILE)
    with zipfile.ZipFile(S7) as z:
        def s7(n):
            name = "s7_" + n + ".png"
            (OUT / name).write_bytes(z.read(n + ".png"))
            return name
        for k, n in PARTS.items():
            mapping["parts"][k] = s7(n)
        for k, n in OTHER.items():
            mapping["other"][k] = s7(n)
    (OUT / "items.json").write_text(json.dumps(mapping, indent=1), encoding="utf-8")
    print("items:", len(list(OUT.glob("*.png"))), "pictures")
    return 0


if __name__ == "__main__":
    sys.exit(main())
