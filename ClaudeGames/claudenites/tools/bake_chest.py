"""The chest: Kenney's Pirate Kit chest (CC0; kept with Claude and Magic's models in Local Storage), baked into
assets/figures/chest.npz - its body and its lid apart (the lid in its own place, its hinge at its origin, so it can
swing open), each vertex coloured from the kit's colour map, read with Claude and Magic's own glTF reader.

    python tools/bake_chest.py"""
import importlib.util
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
CM_TOOLS = ROOT.parent / "Claude and Magic" / "tools"
GLB = ROOT.parents[1] / "Local Storage" / "Claude and Magic models" / "kenney-pirate" / "Models" / "GLB format" / "chest.glb"


def _load(name):
    spec = importlib.util.spec_from_file_location("cm_" + name, CM_TOOLS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    models = _load("models")
    plants = _load("plants")
    g = models.Gltf(GLB)
    j = g.j
    mats = j.get("materials", [])
    parts = {}
    for n in j["nodes"]:
        if "mesh" not in n:
            continue
        pos, col, idx = [], [], []
        for prim in j["meshes"][n["mesh"]]["primitives"]:
            P = g.accessor(prim["attributes"]["POSITION"])
            mat = mats[prim["material"]] if "material" in prim else {}
            tex = plants.texture_colours(g, j, GLB, mat, prim) or [(200, 160, 110)] * len(P)
            base = len(pos)
            pos += P
            col += tex
            idx += [base + i for i in (g.accessor(prim["indices"]) if "indices" in prim else range(len(P)))]
        parts[n["name"]] = (np.array(pos, np.float32), np.array(col, np.float32) / 255, np.array(idx, np.uint32),
                            np.array(n.get("translation", [0, 0, 0]), np.float32))
    body, lid = parts["chest"], parts["lid"]
    out = ROOT / "assets" / "figures" / "chest.npz"
    np.savez_compressed(out, body_pos=body[0], body_col=body[1], body_idx=body[2], lid_pos=lid[0], lid_col=lid[1],
                        lid_idx=lid[2], hinge=lid[3])
    allp = np.concatenate([body[0], lid[0] + lid[3]])
    print("chest:", len(body[0]), "+", len(lid[0]), "verts; box", allp.min(0).round(2), allp.max(0).round(2), "->", out.name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
