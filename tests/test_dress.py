"""Claude and Magic's dressings and set pieces, laid into the floors."""
from pathlib import Path

from claudenites.game import data as D
from claudenites.game import dress, levels
from claudenites.game.world import Game, Input

ART = Path(__file__).resolve().parents[1] / "assets" / "cm"


def test_every_picture_is_there():
    """Every picture a floor asks for (on the walls, floors, corners, ceilings, standing) is in assets/cm (or, for the
    litter, assets/items)."""
    have = {p.stem for p in ART.glob("*.png")} | {"item:" + p.name for p in (ART.parent / "items").glob("*.png")}
    names = set()
    for d in range(1, D.FLOORS + 1, 3):
        L = levels.dungeon(d, 99)
        names |= {x[7] for x in L.decals} | {x[4] for x in L.flats} | {x[6] for x in L.webs} | {x[5] for x in L.hangs}
        names |= {s["name"] for s in L.sprites} | {x[4] for x in L.ceils}
    for spec in dress.LETTERS.values():
        if "sprite" in spec:
            names.add(spec["sprite"][0])
        for k in ("flat", "walldoor"):
            if k in spec:
                names.add(spec[k])
    missing = sorted(n for n in names if n not in have)
    assert not missing, missing
    for t in range(10):
        assert f"t{t}.water0" in have and f"t{t}.torch0" in have


def test_the_set_pieces():
    """Claude and Magic's sixty unique rooms are read; most floors have one; across a run nearly all of them turn up,
    and everything in them can be reached."""
    assert len(dress.set_pieces()) >= 50
    seen = set()
    with_piece = 0
    for seed in ("0:0", 99):                                       # (the floors the other slow tests walk too)
        for d in range(1, D.FLOORS + 1):
            L = levels.dungeon(d, seed)
            if L.pieces:
                with_piece += 1
                seen.add(L.pieces[0]["name"])
            dist = L.distances(int(L.start[0]), int(L.start[1]))
            for c in L.chests:
                assert dist[int(c["z"]), int(c["x"])] >= 0, (seed, d, c)
            for s in L.spawns:
                assert dist[int(s["z"]), int(s["x"])] >= 0, (seed, d, s)
    assert with_piece > 90, with_piece
    assert len(seen) >= 40, len(seen)


def test_the_dressing_by_band():
    """Pipes drip in the Sunken Halls and the Foundry; glowcaps light the Mossway; webs hang in the Barrows."""
    sunk = levels.dungeon(22, 3)
    assert sunk.drips and any(d[7] == "clut.pipe" for d in sunk.decals)
    moss = levels.dungeon(13, 3)
    assert any(s["name"] in ("clut.glowcap", "fungus", "lm.caps") for s in moss.sprites)
    barrow = levels.dungeon(33, 3)
    assert barrow.webs
    glass = levels.dungeon(43, 3)
    assert any(p["model"].startswith("stalagmite") for p in glass.props)


def test_a_chest():
    g = Game.new(seed=21)
    g.go_floor(3)
    L = g.level
    c = L.chests[0]
    c["guard"] = ["Skeleton"]
    g.x, g.z = c["x"] + 0.9, c["z"]
    what, label = g.near()
    assert what[0] == "chest" and "chest" in label
    gold, n = g.player.gold, len(g.monsters)
    g.interact()
    assert c["opened"] and g.player.gold > gold and len(g.player.inventory) >= 1
    assert len(g.monsters) == n + 1 and g.monsters[-1].awake
    assert g.near()[0] != ("chest", 0)


def test_walking_into_a_set_piece():
    for seed in range(20):
        g = Game.new(seed=seed)
        g.go_floor(8)
        if g.level.pieces:
            break
    pc = g.level.pieces[0]
    g.events.clear()
    for (x, y) in g.level.open_squares():
        if pc["x0"] <= x <= pc["x1"] and pc["y0"] <= y <= pc["y1"]:
            g.x, g.z = x + 0.5, y + 0.5
            break
    g.step(0.02, Input())
    said = [e for e in g.events if e[0] == "piece"]
    assert said and said[0][2] == pc["line"]
    g.events.clear()
    g.step(0.02, Input())
    assert not [e for e in g.events if e[0] == "piece"]


def test_things_stand_in_the_way():
    L = levels.dungeon(15, 2)
    s = next(s for s in L.sprites if s.get("solid"))
    assert not L.can_stand(s["x"], s["z"], 0.24, s["y"])
    c = L.chests[0]
    assert not L.can_stand(c["x"], c["z"], 0.24, c["y"])


def _walkable_reach(L, radius=0.24):
    return levels.walkable_reach(L, radius)


def test_nothing_blocks_the_way():
    """With every barrel, crate, chest and standing thing in its place, Claude can still walk to the stairs, to every
    chest's side and to every square of every corridor - on every floor."""
    for seed in range(1):
        for d in range(1, D.FLOORS + 1):
            L = levels.dungeon(d, f"{seed}:0")
            reach = _walkable_reach(L)
            sx, sy = int(L.stairs[0]), int(L.stairs[1])
            assert (sx, sy) in reach, f"floor {d}: the stairs are blocked off"
            for c in L.chests:
                cx, cy = int(c["x"]), int(c["z"])
                assert any((cx + dx, cy + dy) in reach for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))), (d, c)
            cut = [p for p in L.paths if L.open_at(*p) and p not in reach and L.floor[p[1], p[0]] > -0.5]
            assert not cut, f"floor {d}: corridor squares cut off {cut[:5]}"


def test_every_item_has_its_picture():
    """The item sprites (assets/items, tools/import_icons.py): every slot's five tiers, every wand body, every part
    and element, the potions, the scroll and the gold."""
    import json
    from claudenites.game import data as D2
    folder = ART.parent / "items"
    M = json.loads((folder / "items.json").read_text(encoding="utf-8"))
    names = []
    for slot in D2.GEAR_SLOTS:
        tiers = M["gear"][slot]
        assert len(tiers) == len(D2.GEAR_BASES[slot]), slot
        names += [n for tier in tiers for n in tier]
    assert set(M["wands"]) == set(D2.WAND_BODIES)
    names += list(M["wands"].values())
    for kind in D2.PART_KINDS:
        if kind == "core":
            names += [M["parts"][f"core:{e}"] for e in D2.ELEMENTS]
        else:
            names.append(M["parts"][kind])
    names += [M["other"][k] for k in ("potion:health", "potion:mana", "scroll", "gold_pile", "coin")]
    missing = [n for n in names if not (folder / n).exists()]
    assert not missing, missing


def test_a_chest_shot_open_and_shot_to_pieces():
    """Shot before it's opened, a chest gives its things as if opened (and its guards wake); shot after, it only
    breaks. Either way it stands in the way no longer."""
    from claudenites.game.world import Bolt

    def shoot(g, c):
        L = g.level
        dx, dz = next((dx, dz) for dx, dz in ((-1, 0), (1, 0), (0, -1), (0, 1)) if L.open_at(int(c["x"]) + dx, int(c["z"]) + dz))
        for _ in range(40):
            g.bolts = [Bolt(c["x"] + dx * 0.7, c["y"] + 0.3, c["z"] + dz * 0.7, -dx * 12, 0, -dz * 12, 12, "arcane")]
            for _ in range(8):
                g._bolts(1 / 60)
            if c.get("broken"):
                return True
        return False
    g = Game.new(seed=31)
    g.go_floor(4)
    L = g.level
    c = L.chests[0]
    c["guard"] = ["Skeleton"]
    gold, things, n = g.player.gold, len(g.player.inventory), len(g.monsters)
    assert not L.can_stand(c["x"], c["z"], 0.24, c["y"])
    assert shoot(g, c)
    assert c["opened"] and c["broken"] and g.player.gold > gold and len(g.player.inventory) > things
    assert len(g.monsters) == n + 1 and g.drops
    assert L.can_stand(c["x"], c["z"], 0.24, c["y"])
    assert g.near()[0] != ("chest", 0)
    d = L.chests[1]
    g.x, g.z = d["x"] + 0.9, d["z"]
    g.interact()
    assert d["opened"] and not d.get("broken")
    gold = g.player.gold
    assert shoot(g, d)
    assert d["broken"] and g.player.gold == gold                     # (emptied already: nothing more in it)
