"""Where assets/arm.npz came from: the left arm of KayKit's Mage (Kay Lousberg, the Adventurers pack, CC0 - the same
pack as his wand): sleeve, forearm and hand, in its bind pose, each triangle coloured from the pack's texture. Kept here
so The Hollow Oak needs nothing of any other game.

    python tools/export_arm.py        (reads the Timeline's Local Storage; only needed to make it again)

assets/arm.npz: "positions" float32 (triangles*3, 3), "colours" float32 (triangles*3, 3), and "shoulder", "wrist",
"hand" - where those joints are - all in the model's own units.
"""
import io
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from export_spider import accessor, load, trs  # noqa: E402

SOURCE = Path(r"F:\Claude Timeline\Local Storage\Claude and Magic models\kaykit-adventurers\Mage.glb")
OUT = Path(__file__).resolve().parents[1] / "assets" / "arm.npz"


def main():
    from PIL import Image
    j, blob = load(SOURCE)
    nodes = j["nodes"]
    parent = {c: i for i, n in enumerate(nodes) for c in n.get("children", [])}

    def world(i):
        n = nodes[i]
        m = trs(np.asarray(n.get("translation", [0, 0, 0])), np.asarray(n.get("rotation", [0, 0, 0, 1])),
                np.asarray(n.get("scale", [1, 1, 1])))
        return world(parent[i]) @ m if i in parent else m
    names = {n.get("name"): i for i, n in enumerate(nodes)}
    node = names["Mage_ArmLeft"]
    skin = j["skins"][nodes[node]["skin"]]
    inv_bind = accessor(j, blob, skin["inverseBindMatrices"]).reshape(-1, 4, 4).transpose(0, 2, 1)
    joint = {nodes[nid]["name"]: k for k, nid in enumerate(skin["joints"])}
    # the skin's bind pose: each vertex through its joints at rest
    jm = np.array([world(nid) @ inv_bind[k] for k, nid in enumerate(skin["joints"])])
    img = j["images"][0]
    bv = j["bufferViews"][img["bufferView"]]
    tex = Image.open(io.BytesIO(blob[bv.get("byteOffset", 0):bv.get("byteOffset", 0) + bv["byteLength"]])).convert("RGB")
    P, C = [], []
    for prim in j["meshes"][nodes[node]["mesh"]]["primitives"]:
        at = prim["attributes"]
        p = accessor(j, blob, at["POSITION"]).astype(np.float64)
        jn = accessor(j, blob, at["JOINTS_0"]).astype(int)
        w = np.nan_to_num(accessor(j, blob, at["WEIGHTS_0"]).astype(np.float64))
        w /= np.maximum(w.sum(1, keepdims=True), 1e-9)
        ph = np.concatenate([p, np.ones((len(p), 1))], 1)
        v = np.zeros((len(p), 3))
        for c in range(4):
            v += w[:, c:c + 1] * np.einsum("nij,nj->ni", jm[jn[:, c]], ph)[:, :3]
        uv = accessor(j, blob, at["TEXCOORD_0"])
        idx = accessor(j, blob, prim["indices"]).astype(int).reshape(-1, 3)
        for tri in idx:
            u = uv[tri].mean(0)
            c = tex.getpixel((int(u[0] % 1.0 * (tex.width - 1)), int(u[1] % 1.0 * (tex.height - 1))))
            col = tuple((ch / 255.0) ** 2.2 for ch in c)                      # (the texture's sRGB, to light)
            for i in tri:
                P.append(v[i])
                C.append(col)

    def at_joint(name):
        return np.linalg.inv(inv_bind[joint[name]])[:3, 3]
    np.savez_compressed(OUT, positions=np.array(P, np.float32), colours=np.array(C, np.float32),
                        shoulder=at_joint("upperarm.l"), wrist=at_joint("wrist.l"), hand=at_joint("hand.l"))
    print("the arm:", len(P) // 3, "triangles; shoulder", at_joint("upperarm.l").round(3), "hand", at_joint("hand.l").round(3),
          "box", np.min(P, 0).round(3), np.max(P, 0).round(3))


if __name__ == "__main__":
    main()
