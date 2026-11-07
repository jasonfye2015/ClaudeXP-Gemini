"""Bakes Quaternius's Spider (the Easy Enemy pack, CC0) into assets/spider.npz: its clips sampled into frames of
skinned, flat-shaded triangles, so the game draws her small ones (and, later, her) without a skeleton of its own.

    python tools/export_spider.py      (reads the Timeline's Local Storage; run once - the result is committed)

assets/spider.npz holds, per clip: "<clip>" float16 (frames, triangles*3, 3) - positions (the game finds the faces'
normals), in units
where the body is one long (nose to tail, legs at rest), facing +z, feet at y = 0 - and "<clip>_fps"; and "colour"
(triangles*3, 3), each triangle its material's colour.
"""
import json
import struct
import sys
from pathlib import Path

import numpy as np

SOURCE = Path(r"F:\Claude Timeline\Local Storage\Claude and Magic models\quaternius\Spider.glb")
OUT = Path(__file__).resolve().parents[1] / "assets" / "spider.npz"
CLIPS = {"walk": "SpiderArmature|Spider_Walk", "idle": "SpiderArmature|Spider_Idle", "attack": "SpiderArmature|Spider_Attack"}
FPS = 20
CT = {5121: np.uint8, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
NC = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}


def load(path):
    b = path.read_bytes()
    n = struct.unpack("<I", b[12:16])[0]
    j = json.loads(b[20:20 + n])
    off = 20 + n
    ln = struct.unpack("<I", b[off:off + 4])[0]
    return j, b[off + 8:off + 8 + ln]


def accessor(j, blob, i):
    a = j["accessors"][i]
    bv = j["bufferViews"][a["bufferView"]]
    dt = np.dtype(CT[a["componentType"]])
    k = NC[a["type"]]
    stride = bv.get("byteStride") or dt.itemsize * k
    base = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
    raw = np.frombuffer(blob, np.uint8, count=stride * (a["count"] - 1) + dt.itemsize * k, offset=base)
    out = np.lib.stride_tricks.as_strided(raw, (a["count"], k * dt.itemsize), (stride, 1)).copy().view(dt)
    return out.reshape(a["count"], k) if k > 1 else out.reshape(-1)


def quat_mat(q):
    x, y, z, w = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)],
                     [2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)],
                     [2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)]])


def trs(t, r, s):
    m = np.identity(4)
    m[:3, :3] = quat_mat(r) * np.asarray(s)[None, :]
    m[:3, 3] = t
    return m


def sample(times, vals, t):
    if t <= times[0]:
        return vals[0]
    if t >= times[-1]:
        return vals[-1]
    i = int(np.searchsorted(times, t)) - 1
    k = (t - times[i]) / max(1e-9, times[i + 1] - times[i])
    a, b = vals[i], vals[i + 1]
    if len(a) == 4:
        if np.dot(a, b) < 0:
            b = -b
        v = a + (b - a) * k
        return v / np.linalg.norm(v)
    return a + (b - a) * k


def main():
    j, blob = load(SOURCE)
    nodes = j["nodes"]
    parent = {c: i for i, n in enumerate(nodes) for c in n.get("children", [])}
    skin = j["skins"][0]
    joints = skin["joints"]
    inv_bind = accessor(j, blob, skin["inverseBindMatrices"]).reshape(-1, 4, 4).transpose(0, 2, 1)   # (column-major)
    mesh_node = next(i for i, n in enumerate(nodes) if "mesh" in n)
    mats = j["materials"]
    P, J, W, C = [], [], [], []
    for prim in j["meshes"][nodes[mesh_node]["mesh"]]["primitives"]:
        at = prim["attributes"]
        p = accessor(j, blob, at["POSITION"]).astype(np.float64)
        jn = accessor(j, blob, at["JOINTS_0"]).astype(int)
        w = np.nan_to_num(accessor(j, blob, at["WEIGHTS_0"]).astype(np.float64))
        w /= np.maximum(w.sum(1, keepdims=True), 1e-9)
        idx = accessor(j, blob, prim["indices"]).astype(int)
        col = np.array(mats[prim["material"]]["pbrMetallicRoughness"]["baseColorFactor"][:3])
        P.append(p[idx]); J.append(jn[idx]); W.append(w[idx]); C.append(np.tile(col, (len(idx), 1)))
    P, J, W, C = (np.concatenate(a) for a in (P, J, W, C))
    anims = {a["name"]: a for a in j["animations"]}

    def world_mats(pose):
        cache = {}

        def world(i):
            if i in cache:
                return cache[i]
            n = nodes[i]
            t, r, s = pose.get(i, (n.get("translation", [0, 0, 0]), n.get("rotation", [0, 0, 0, 1]), n.get("scale", [1, 1, 1])))
            m = trs(np.asarray(t), np.asarray(r), np.asarray(s))
            if i in parent:
                m = world(parent[i]) @ m
            cache[i] = m
            return m
        return world

    def skinned(pose):
        world = world_mats(pose)
        jm = np.array([world(nid) @ inv_bind[k] for k, nid in enumerate(joints)])      # (world space: the skin's way)     # (n_joints, 4, 4)
        ph = np.concatenate([P, np.ones((len(P), 1))], 1)
        out = np.zeros((len(P), 3))
        for c in range(4):
            out += W[:, c:c + 1] * np.einsum("nij,nj->ni", jm[J[:, c]], ph)[:, :3]
        return out

    rest = skinned({})
    # the frame: the model's own up is +y in glTF; find its length along z (or x) and its feet
    lo, hi = rest.min(0), rest.max(0)
    span = hi - lo
    print("rest box", lo.round(3), hi.round(3))
    long_axis = 2                                       # (glTF faces +z; the legs splay wider than it is long)
    scale = 1.0 / span[long_axis]
    centre = np.array(((lo[0] + hi[0]) / 2, lo[1], (lo[2] + hi[2]) / 2))
    out = {}
    for alias, name in CLIPS.items():
        a = anims[name]
        chans = {}
        length = 0.0
        for ch in a["channels"]:
            smp = a["samplers"][ch["sampler"]]
            times = accessor(j, blob, smp["input"])
            vals = accessor(j, blob, smp["output"])
            chans.setdefault(ch["target"]["node"], {})[ch["target"]["path"]] = (times, vals)
            length = max(length, float(times[-1]))
        fps = FPS if alias != "idle" else 10
        frames = max(2, int(round(length * fps)))
        data = []
        for f in range(frames):
            t = f / fps
            pose = {}
            for nid, ch in chans.items():
                n = nodes[nid]
                pose[nid] = tuple(sample(*ch[k], t) if k in ch else np.asarray(n.get(d, dv)) for k, d, dv in
                                  (("translation", "translation", [0, 0, 0]), ("rotation", "rotation", [0, 0, 0, 1]), ("scale", "scale", [1, 1, 1])))
            v = (skinned(pose) - centre) * scale
            if long_axis == 0:
                v = v[:, [2, 1, 0]] * np.array((1, 1, -1))
            data.append(v)
        out[alias] = np.array(data, np.float16)
        out[alias + "_fps"] = np.array(fps)
        print(alias, out[alias].shape, f"{length:.2f}s")
    out["colour"] = C.astype(np.float32)
    np.savez_compressed(OUT, **out)
    print("->", OUT, OUT.stat().st_size // 1024, "KB")


if __name__ == "__main__":
    sys.exit(main())
