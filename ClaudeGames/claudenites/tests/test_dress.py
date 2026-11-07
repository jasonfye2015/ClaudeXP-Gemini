"""Claude and Magic's dressings and set pieces, laid into the floors."""
from pathlib import Path

from claudenites.game import data as D
from claudenites.game import dress, levels
from claudenites.game.world import Game, Input

ART = Path(__file__).resolve().parents[1] / "assets" / "cm"


def test_every_picture_is_there():
    """Every picture a floor asks for (on the walls, floors, corners, ceilings, standing) is in assets/cm."""
    have = {p.stem for p in ART.glob("*.png")}
    names = set()
    for d in range(1, D.FLOORS + 1, 3):
        L = levels.dungeon(d, 5)
        names |= {x[7] for x in L.decals} | {x[4] for x in L.flats} | {x[6] for x in L.webs} | {x[5] for x in L.hangs}
        names |= {s["name"] for s in L.sprites}
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
    for seed in range(4):
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
    assert with_piece > 150, with_piece
    assert len(seen) >= 45, len(seen)


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
    g.step(0.02, Input())
    assert not [e for e in g.events[len(g.events) - 2:] if e[0] == "piece"]


def test_things_stand_in_the_way():
    L = levels.dungeon(15, 2)
    s = next(s for s in L.sprites if s.get("solid"))
    assert not L.can_stand(s["x"], s["z"], 0.24, s["y"])
    c = L.chests[0]
    assert not L.can_stand(c["x"], c["z"], 0.24, c["y"])
