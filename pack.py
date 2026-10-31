"""The art packs for the Pixel and Stone themes, built into one JavaScript module so the game stays one file.

    python pack.py --gather   copy the chosen tiles and textures from the kept sets in Local Storage into src/art/
    python pack.py            write src/js/35-packs.js from src/art/ (an atlas of the pixel tiles, the stone textures)
    python pack.py --check    say whether src/js/35-packs.js matches src/art/ (the tests ask)

The Pixel theme is drawn from the Dungeon Crawl Stone Soup tiles (CC0; the whole set is kept in
  Local Storage\\Dungeon Crawl - Sprites\\Dungeon Crawl Stone Soup Full, with its LICENSE.txt and README.txt of credits).
The Stone theme's walls, floors and ceilings are ambientCG photo textures (CC0; the sets are kept in
  Local Storage\\ambientCG - Textures, one folder each, all maps; the game uses the *_Color.jpg maps only).
PIXEL and STONE below say which file goes where; --gather copies them (the stone textures resized to STONE_SIZE) into
src/art/pixel/<key>.png and src/art/stone/<key>.jpg, which are committed, so the build never needs Local Storage.
The game reads the packs through CM.packs (35-packs.js): pixel {atlas, index {key: [x, y]}, size 32}, stone {key: dataURL}.
"""
import base64
import io
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ART = HERE / "src" / "art"
OUT = HERE / "src" / "js" / "35-packs.js"
# the Timeline that keeps the whole sets: the folder above the game in the Timeline's tree, or its sibling "Claude Timeline" when
# the game lives in its own repo beside it, or wherever CLAUDE_TIMELINE points
import os
TIMELINE = next((p for p in [Path(os.environ.get("CLAUDE_TIMELINE", "")), HERE.parent.parent, HERE.parent / "Claude Timeline"] if (p / "Local Storage").is_dir()), HERE.parent.parent)
DCSS = TIMELINE / "Local Storage" / "Dungeon Crawl - Sprites" / "Dungeon Crawl Stone Soup Full"
ACG = TIMELINE / "Local Storage" / "ambientCG - Textures"
TILE = 32
COLUMNS = 16
STONE_SIZE = 512

# the Pixel theme: game key -> Crawl tile (a path under the set, without .png)
PIXEL = {
    # the stone of each depth: wall, a second wall, the wall with bones (or carvings), floor, ceiling
    "t0.wall": "dungeon/wall/brick_dark_0", "t0.wall2": "dungeon/wall/brick_dark_2", "t0.wallbones": "dungeon/wall/catacombs_1",
    "t0.floor": "dungeon/floor/crypt_10", "t0.ceiling": "dungeon/floor/rect_gray_0_new",
    "t1.wall": "dungeon/wall/stone_dark_0", "t1.wall2": "dungeon/wall/stone_dark_1", "t1.wallbones": "dungeon/wall/wall_vines_1",
    "t1.floor": "dungeon/floor/black_cobalt_1", "t1.ceiling": "dungeon/floor/rect_gray_1_new",
    "t2.wall": "dungeon/wall/stone_brick_1", "t2.wall2": "dungeon/wall/stone_brick_5", "t2.wallbones": "dungeon/wall/relief_brown_0",
    "t2.floor": "dungeon/floor/sandstone_floor_0", "t2.ceiling": "dungeon/floor/limestone_0",
    "t3.wall": "dungeon/wall/marble_wall_1", "t3.wall2": "dungeon/wall/marble_wall_5", "t3.wallbones": "dungeon/wall/undead_0",
    "t3.floor": "dungeon/floor/tomb_0_new", "t3.ceiling": "dungeon/floor/frozen_0",
    # the Deep's six bands
    "t4.wall": "dungeon/wall/cobalt_rock_1", "t4.wall2": "dungeon/wall/cobalt_rock_2", "t4.wallbones": "dungeon/wall/cobalt_rock_3", "t4.floor": "dungeon/floor/black_cobalt_1", "t4.ceiling": "dungeon/floor/black_cobalt_5",
    "t5.wall": "dungeon/wall/wall_vines_0", "t5.wall2": "dungeon/wall/wall_vines_2", "t5.wallbones": "dungeon/wall/slime_0_new", "t5.floor": "dungeon/floor/bog_green_0_new", "t5.ceiling": "dungeon/floor/swamp_0_new",
    "t6.wall": "dungeon/wall/crystal_wall_lightmagenta", "t6.wall2": "dungeon/wall/crystal_wall_magenta", "t6.wallbones": "dungeon/wall/crystal_wall_white", "t6.floor": "dungeon/floor/crystal_floor_0", "t6.ceiling": "dungeon/floor/crystal_floor_3",
    "t7.wall": "dungeon/wall/metal_wall", "t7.wall2": "dungeon/wall/metal_wall_cracked", "t7.wallbones": "dungeon/wall/metal_wall_brown", "t7.floor": "dungeon/floor/volcanic_floor_0", "t7.ceiling": "dungeon/floor/rough_red_0",
    "t8.wall": "dungeon/wall/undead_0", "t8.wall2": "dungeon/wall/undead_1", "t8.wallbones": "dungeon/wall/catacombs_0", "t8.floor": "dungeon/floor/crypt_10", "t8.ceiling": "dungeon/floor/tomb_0_new",
    "t9.wall": "dungeon/wall/volcanic_wall_0", "t9.wall2": "dungeon/wall/volcanic_wall_2", "t9.wallbones": "dungeon/wall/hell_1", "t9.floor": "dungeon/floor/demonic_red_1", "t9.ceiling": "dungeon/floor/infernal_1",
    "secret": "dungeon/doors/detected_secret_door",
    # the furniture
    "chest": "dungeon/chest_2_closed", "hatch": "dungeon/gateways/escape_hatch_down", "stairs_up": "dungeon/gateways/stone_stairs_up",
    "door": "dungeon/doors/closed_door", "door_locked": "dungeon/doors/runed_door", "door_open": "dungeon/doors/open_door",
    "gate": "dungeon/doors/gate_closed_middle", "gate_open": "dungeon/doors/gate_open_middle",
    "pit": "dungeon/traps/shaft", "trapdoor": "dungeon/traps/trap_shaft", "teleporter": "dungeon/traps/teleport_permanent",
    "fountain": "dungeon/blue_fountain", "fountain_dry": "dungeon/dry_fountain", "altar": "dungeon/altars/altar_shining_one",
    "carving": "dungeon/wall/relief_0", "key": "item/misc/key", "phylactery": "item/misc/misc_box",
    # what flies and bursts, the torches on the walls, the water on the floors
    "fx.spark": "effect/gold_sparkles_1", "fx.fire": "effect/cloud_fire_0", "fx.frost": "effect/frost_0", "fx.bolt": "effect/zap_0",
    "fx.force": "effect/magic_dart_0", "fx.holy": "effect/sanctuary", "fx.arrow": "effect/arrow_1",
    "torch0": "dungeon/wall/torches/torch_0", "torch1": "dungeon/wall/torches/torch_1", "torch2": "dungeon/wall/torches/torch_2",
    "water0": "dungeon/water/shallow_water", "water1": "dungeon/water/shallow_water_2", "water2": "dungeon/water/shallow_water_disturbance",
    # the surface: grass and dirt underfoot, the trees, the town wall's grey brick
    "ground.grass": "dungeon/floor/grass/grass_0_new", "ground.dirt": "dungeon/floor/dirt_0_new", "solid.townwall": "dungeon/wall/brick_gray_0", "solid.townwall.top": "dungeon/wall/brick_gray_2",
    "cross": "dungeon/statues/granite_statue",
    # the monsters, by kind
    "m.Giant Rat": "monster/animals/rat", "m.Kobold": "monster/kobold_new", "m.Skeleton": "monster/undead/skeletal_warrior_new",
    "m.Goblin": "monster/goblin_new", "m.Zombie": "monster/undead/zombies/zombie_small", "m.Orc": "monster/orc_warrior_new",
    "m.Ghoul": "monster/undead/ghoul", "m.Dark Elf": "monster/deep_elf_master_archer", "m.Troll": "monster/troll",
    "m.Wraith": "monster/undead/wraith", "m.Ogre": "monster/ogre_new", "m.Minotaur": "monster/minotaur",
    "m.Gargoyle": "monster/nonliving/gargoyle", "m.Vampire": "monster/undead/vampire_new", "m.Demon": "monster/demons/balrug_new",
    "m.Wyvern": "monster/dragons/wyvern_new", "m.The Lich King": "monster/undead/ancient_lich_new",
    # the guardians, and the forge-floor of the third's lair
    "m.The Rat King": "monster/animals/orange_rat", "m.The Drowned Knight": "monster/death_knight", "m.The Forge-Warden": "monster/nonliving/iron_golem",
    "ember": "dungeon/floor/lava_0",
    # the Deep's monsters and guardians
    "m.Spore Mother": "monster/fungi_plants/hyperactive_ballistomycete", "m.Mycelid Crawler": "monster/fungi_plants/vine_stalker", "m.Sporeling": "monster/fungi_plants/deathcap",   # the Deep's ten more (v10.0)
    "m.Glass Hound": "monster/animals/war_dog", "m.Prism Sentinel": "monster/nonliving/fulminant_prism_1", "m.Bellows Imp": "monster/demons/imp", "m.Slag Golem": "monster/nonliving/iron_elemental",
    "m.Grave Lantern": "monster/undead/hungry_ghost", "m.Charnel Hound": "monster/undead/zombies/zombie_hound", "m.Thorn Lotus": "monster/fungi_plants/thorn_lotus", "m.Root Wyrm": "monster/animals/rock_worm",
    "m.The King of the Tower": "monster/deep_elf_annihilator",   # the Mage Tower's King (v10.6)
    "m.Drowned Townsfolk": "monster/undead/revenant", "m.Eel": "monster/aquatic/electric_eel", "m.Marsh Light": "monster/nonliving/ball_lightning",   # the Undercroft's (v9.9)
    "m.Cellar Spider": "monster/animals/wolf_spider_new", "m.Bell-Ringer": "monster/undead/silent_spectre", "m.The Bell-Founder's Boy": "monster/human_monk_ghost",
    "m.Drowned": "monster/undead/drowned_soul", "m.Weed Hag": "monster/undead/bog_body", "m.Fungal Horror": "monster/fungi_plants/wandering_mushroom_new",
    "m.Spore Beast": "monster/fungi_plants/giant_spore", "m.Crystal Golem": "monster/nonliving/crystal_golem", "m.Shard Wisp": "monster/nonliving/insubstantial_wisp",
    "m.Iron Hound": "monster/animals/hell_hound_new", "m.Foundry Imp": "monster/demons/iron_imp_new", "m.Bone Colossus": "monster/undead/macabre_mass",
    "m.Grave Priest": "monster/undead/mummy_priest", "m.Rootling": "monster/fungi_plants/thorn_hunter", "m.Hollow One": "monster/undead/shadow_new",
    "m.The Drowned Queen": "monster/merfolk_avatar", "m.The Mycelial Mind": "monster/giant_orange_brain", "m.The Crystal Tyrant": "monster/nonliving/crystal_guardian",
    "m.The Foundry Master": "monster/fire_giant_new", "m.The Bone Patriarch": "monster/undead/lich", "m.The Root of the World": "monster/abyss/tentacled_starspawn",
    # the dungeon's people, a plate in the floor, a door written over with runes, someone's bones (as an icon)
    "npc.ghost": "monster/human_monk_ghost", "npc.hermit": "monster/unique/crazy_yiuf", "npc.adventurer": "monster/human_slave",
    "plate": "dungeon/traps/pressure_plate", "door_riddle": "dungeon/doors/sealed_door", "i.bones": "item/food/bone",
    # tomes and gems for the smith
    "i.tome": "item/book/dark_blue_new", "i.gem_diamond": "item/amulet/crystal_white", "i.gem_ruby": "item/amulet/crystal_red",
    "i.gem_sapphire": "item/amulet/stone_2_blue", "i.gem_sunstone": "item/misc/misc_crystal_new",
    # the things in the pack
    "i.heal": "item/potion/ruby_new", "i.mana": "item/potion/brilliant_blue_new", "i.revive": "item/potion/golden", "i.antidote": "item/potion/emerald",
    "i.scroll": "item/scroll/scroll_new", "i.wand": "item/wand/wand_brass", "i.torch": "player/hand_left/misc/torch", "i.lantern": "item/misc/misc_lantern",
    "i.key": "item/misc/key", "i.gold": "item/gold/gold_pile_5",
    "i.dagger": "item/weapon/dagger_new", "i.short_sword": "item/weapon/short_sword_1_new", "i.mace": "item/weapon/mace_1_new",
    "i.long_sword": "item/weapon/long_sword_1_new", "i.axe": "item/weapon/battle_axe_1", "i.hammer": "item/weapon/hammer_1_new",
    "i.great_sword": "item/weapon/greatsword_1_new", "i.club": "item/weapon/club_new", "i.staff": "item/weapon/quarterstaff_new",
    "i.knife": "item/weapon/knife", "i.spear": "item/weapon/spear_1", "i.bow": "item/weapon/ranged/shortbow_1", "i.longbow": "item/weapon/ranged/longbow",
    "i.robe": "item/armor/torso/robe_1_new", "i.leather": "item/armor/torso/leather_armor_1", "i.ring_mail": "item/armor/torso/ring_mail_1_new",
    "i.scale": "item/armor/torso/scale_mail_1_new", "i.chain": "item/armor/torso/chain_mail_1", "i.plate": "item/armor/torso/plate_mail_1",
    "i.buckler": "item/armor/shields/buckler_1_new", "i.shield": "item/armor/shields/shield_2_kite", "i.tower": "item/armor/shields/large_shield_1_new",
    "i.cap": "item/armor/headgear/cap_1", "i.helm": "item/armor/headgear/helmet_1", "i.great_helm": "item/armor/headgear/plumed_helmet",
    "i.ring": "item/ring/gold", "i.amulet": "item/amulet/celtic_blue", "i.unknown": "misc/unseen_item_new",
    # the spells and skills, by their ids in CM.ABILITIES
    "s.missile": "gui/spells/conjuration/magic_dart", "s.firebolt": "gui/spells/fire/throw_flame_new", "s.light": "gui/spells/enchantment/corona",
    "s.sleep": "gui/spells/ice/ensorcelled_hibernation_new", "s.frost": "gui/spells/ice/throw_frost_new", "s.fireball": "gui/spells/fire/fireball_new",
    "s.blink": "gui/spells/translocation/blink", "s.lightning": "gui/spells/air/lightning_bolt_new",
    "s.heal": "gui/invocations/elyvilon_heal_other", "s.cure": "gui/spells/poison/cure_poison_new", "s.bless": "gui/invocations/tso_bless_weapon",
    "s.turn": "gui/spells/necromancy/dispel_undead_new", "s.protection": "gui/spells/earth/stoneskin_new", "s.lift": "gui/spells/remove_curse",
    "s.sanctuary": "effect/sanctuary", "s.raise": "gui/spells/necromancy/borgnjors_revivification_new",
    "s.lay": "gui/spells/necromancy/regeneration_new", "s.smite": "gui/spells/enchantment/sure_blade_new",
    "s.thorns": "gui/spells/summoning/summon_forest", "s.mend": "gui/spells/necromancy/regeneration_new", "s.entangle": "gui/spells/summoning/sticks_to_snakes_new",
    "s.regrowth": "gui/spells/necromancy/regeneration_new", "s.calllightning": "gui/spells/air/chain_lightning_new",
    "s.song": "gui/spells/enchantment/song_of_slaying", "s.mockery": "gui/spells/enchantment/cause_fear_new", "s.lullaby": "gui/spells/ice/ensorcelled_hibernation_new",
    "s.rally": "gui/spells/enchantment/berserker_rage_new", "s.volley": "effect/arrow_0", "s.aimed": "gui/spells/enchantment/sure_blade_new",
    "s.mark": "gui/spells/divination/detect_creatures", "s.guard": "gui/spells/earth/stoneskin_new", "s.taunt": "gui/spells/enchantment/discord",
    "s.bash": "item/armor/shields/shield_2_kite", "s.trick": "gui/spells/enchantment/confuse_new",
    # the heroes' portraits: paper-doll parts, laid in this order
    "d.human_male": "player/base/human_male", "d.human_female": "player/base/human_female",
    "d.body.plate": "player/body/plate", "d.body.plate_cloth": "player/body/plate_and_cloth", "d.body.leather": "player/body/leather_armor",
    "d.body.leather_green": "player/body/leather_green", "d.body.robe_white_red": "player/body/robe_white_red", "d.body.robe_blue": "player/body/robe_blue",
    "d.body.robe_green": "player/body/robe_green", "d.body.vest": "player/body/shirt_vest",
    "d.head.helm_plume": "player/head/helm_plume", "d.head.full_gold": "player/head/full_gold", "d.head.hood_black": "player/head/hood_black_2",
    "d.head.hood_green": "player/head/hood_green", "d.head.healer": "player/head/healer", "d.head.wizard_blue": "player/head/wizard_blue",
    "d.head.hood_green_2": "player/head/hood_green_2", "d.head.feather_red": "player/head/feather_red",
    "d.right.long_sword": "player/hand_right/long_sword", "d.right.blessed_blade": "player/hand_right/blessed_blade", "d.right.dagger": "player/hand_right/dagger_slant_new",
    "d.right.bow": "player/hand_right/bow", "d.right.mace": "player/hand_right/mace_new", "d.right.staff_mage": "player/hand_right/staff_mage",
    "d.right.staff_organic": "player/hand_right/staff_organic", "d.right.horn": "player/hand_right/misc/horn",
    "d.left.shield_knight": "player/hand_left/shield_knight_blue", "d.left.shield_holy": "player/hand_left/shield_holy",
    "d.left.shield_round": "player/hand_left/shield_round_white", "d.left.book": "player/hand_left/misc/book_blue",
    "d.hair.short_black": "player/hair/short_black", "d.hair.long_red": "player/hair/long_red", "d.beard.long_white": "player/beard/long_white",
    "d.cloak.black": "player/cloak/black", "d.cloak.green": "player/cloak/green", "d.cloak.white": "player/cloak/white", "d.cloak.red": "player/cloak/red",
    "d.legs.armor": "player/legs/leg_armor_1", "d.legs.black": "player/legs/pants_black", "d.legs.green": "player/legs/pants_darkgreen", "d.legs.blue": "player/legs/pants_blue",
    "d.boots.gray": "player/boots/middle_gray", "d.boots.short": "player/boots/short_brown", "d.boots.brown": "player/boots/middle_brown",
}

# the Stone theme: game key -> ambientCG set (its *_Color.jpg)
STONE = {
    "t0.wall": "Bricks089", "t0.floor": "PavingStones141", "t0.ceiling": "Rock035",
    "t1.wall": "Rock037", "t1.floor": "Rock020", "t1.ceiling": "Bricks058",
    "t2.wall": "Bricks100", "t2.floor": "PavingStones128", "t2.ceiling": "Planks039",
    "t3.wall": "Marble006", "t3.floor": "Tiles074", "t3.ceiling": "Onyx013",
    # the surface: underfoot, and the faces of what stands on it
    "ground.grass": "Grass001", "ground.dirt": "Ground110", "ground.tilled": "Ground103", "ground.cobbles": "PavingStones141", "ground.flags": "PavingStones128",
    "ground.planks": "Planks039", "ground.moss": "Grass005", "solid.hedge": "Grass005", "solid.plaster": "Plaster001", "solid.roof": "RoofingTiles013A",
    "solid.bark": "Bark007", "solid.townwall": "Bricks097", "solid.townwall.top": "PavingStones128", "solid.cliff": "Rock035",
    "ground.needles": "Ground077", "ground.litter": "ScatteredLeaves001",
}

# cut-outs: single grass blades and leaves with their opacity, for the Stone look's props to stamp (PNG with alpha)
CUTOUT = {"cut.blades": "Foliage001", "cut.grass": "Foliage006", "cut.maple": "LeafSet027", "cut.leaf": "LeafSet024"}
CUTOUT_SIZE = 384

CREDITS = {
    "pixel": "Dungeon Crawl Stone Soup tiles (CC0) - by the Crawl Stone Soup team and the RLTiles project; "
             "https://opengameart.org/content/dungeon-crawl-32x32-tiles",
    "stone": "ambientCG textures (CC0) - Bricks089, PavingStones141, Rock035, Rock037, Rock020, Bricks058, Bricks100, PavingStones128, "
             "Planks039, Marble006, Tiles074, Onyx013, Grass001, Grass005, Ground110, Ground103, Plaster001, RoofingTiles013A, Bark007, Bricks097, Ground077, ScatteredLeaves001; cut-outs Foliage001, Foliage006, LeafSet027, LeafSet024; https://ambientcg.com",
}


def gather():
    from PIL import Image
    (ART / "pixel").mkdir(parents=True, exist_ok=True)
    (ART / "stone").mkdir(parents=True, exist_ok=True)
    missing = []
    for key, rel in PIXEL.items():
        src = DCSS / (rel + ".png")
        if not src.exists():
            missing.append(rel)
            continue
        img = Image.open(src).convert("RGBA")
        if img.size != (TILE, TILE):
            img = img.crop((0, 0, TILE, TILE))
        img.save(ART / "pixel" / (key + ".png"), optimize=True)
    for key, name in STONE.items():
        src = next((ACG / name).glob("*_Color.jpg"), None)
        if src is None:
            missing.append(name)
            continue
        img = Image.open(src).convert("RGB").resize((STONE_SIZE, STONE_SIZE), Image.LANCZOS)
        img.save(ART / "stone" / (key + ".jpg"), quality=82, optimize=True)
    for key, name in CUTOUT.items():
        col, op = next((ACG / name).glob("*_Color.png"), None), next((ACG / name).glob("*_Opacity.png"), None)
        if col is None or op is None:
            missing.append(name)
            continue
        img = Image.open(col).convert("RGB")
        img.putalpha(Image.open(op).convert("L"))
        img.resize((CUTOUT_SIZE, CUTOUT_SIZE), Image.LANCZOS).save(ART / "stone" / (key + ".png"), optimize=True)
    (ART / "CREDITS.txt").write_text(
        "Art packs for Claude and Magic's Pixel and Stone themes, gathered by pack.py --gather.\n\n"
        f"pixel/  {CREDITS['pixel']}\n        The whole set, with its LICENSE.txt (CC0) and README.txt of contributors, is kept in\n"
        "        Local Storage\\Dungeon Crawl - Sprites.\n\n"
        f"stone/  {CREDITS['stone']}\n        Each set (all its maps) is kept in Local Storage\\ambientCG - Textures.\n", encoding="utf-8")
    print(f"gathered {len(PIXEL) - len([m for m in missing if m in PIXEL.values()])} tiles and {len(STONE)} textures"
          + (f"; MISSING: {missing}" if missing else ""))
    return 1 if missing else 0


def build_text():
    from PIL import Image
    keys = list(PIXEL)
    rows = (len(keys) + COLUMNS - 1) // COLUMNS
    atlas = Image.new("RGBA", (COLUMNS * TILE, rows * TILE), (0, 0, 0, 0))
    index = {}
    for i, key in enumerate(keys):
        x, y = (i % COLUMNS) * TILE, (i // COLUMNS) * TILE
        f = ART / "pixel" / (key + ".png")
        if f.exists():
            atlas.paste(Image.open(f).convert("RGBA"), (x, y))
        index[key] = [x, y]
    buf = io.BytesIO()
    atlas.save(buf, format="PNG", optimize=True)
    png = base64.b64encode(buf.getvalue()).decode("ascii")
    stone = {}
    for key in STONE:
        f = ART / "stone" / (key + ".jpg")
        if f.exists():
            stone[key] = "data:image/jpeg;base64," + base64.b64encode(f.read_bytes()).decode("ascii")
    for key in CUTOUT:
        f = ART / "stone" / (key + ".png")
        if f.exists():
            stone[key] = "data:image/png;base64," + base64.b64encode(f.read_bytes()).decode("ascii")
    import json
    lines = ['"use strict";',
             "// GENERATED by pack.py from src/art/ - do not edit. The Pixel theme's tiles as one atlas (Dungeon Crawl Stone Soup, CC0) and",
             "// the Stone theme's textures (ambientCG, CC0), carried inside the one file. CM.packs.load() decodes them; see 30-art.js.",
             "CM.packs = {",
             f"  credits: {json.dumps(CREDITS, ensure_ascii=False)},",
             f"  pixel: {{ size: {TILE}, columns: {COLUMNS}, index: {json.dumps(index, ensure_ascii=False)},",
             f'    atlas: "data:image/png;base64,{png}" }},',
             f"  stone: {{ size: {STONE_SIZE}, textures: {json.dumps(stone)} }},",
             "};",
             ""]
    return "\n".join(lines)


def same_pack(have, want):
    """Two packs are the same when they hold the same pictures: Pillow's PNG encoder differs from version to version, so
    the atlas is compared pixel by pixel, the rest as text."""
    import re
    from PIL import Image
    pat = r'atlas: "data:image/png;base64,([A-Za-z0-9+/=]+)"'
    a, b = re.search(pat, have), re.search(pat, want)
    if not a or not b or re.sub(pat, "", have) != re.sub(pat, "", want):
        return False
    img_a = Image.open(io.BytesIO(base64.b64decode(a.group(1)))).convert("RGBA")
    img_b = Image.open(io.BytesIO(base64.b64decode(b.group(1)))).convert("RGBA")
    return img_a.size == img_b.size and img_a.tobytes() == img_b.tobytes()


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--gather" in argv:
        return gather()
    text = build_text()
    if "--check" in argv:
        same = OUT.exists() and same_pack(OUT.read_text(encoding="utf-8"), text)
        print("up to date" if same else "out of date: run  python pack.py  in ClaudeGames/claudemagic")
        return 0 if same else 1
    OUT.write_text(text, encoding="utf-8")
    print(f"wrote {OUT.name} ({OUT.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
