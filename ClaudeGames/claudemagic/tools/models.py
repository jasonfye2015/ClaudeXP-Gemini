"""The figures' pipeline (v65.0, UPGRADE_PLAN_60.md phase 0): rigged, animated low-poly bodies from CC0 packs (KayKit,
Quaternius - see src/models/CREDITS.txt) baked small enough to ride inside the one HTML file.

    python tools/models.py            bake src/models/figures.json -> src/js/35c-figures.js (and report the sizes)
    python tools/models.py --check    bake to memory and report only (the tests and ship do this)

Sources are read from the Local Storage folder (SOURCES below), never committed: only the baked file is. Each model's
glTF (.glb) is read with the standard library alone - no numpy, no gltf libraries - and written out as:
  mesh:      positions as int16 over the model's box, uv as uint16 (textured models), a colour per vertex (the
             material's base colour, for the untextured ones), 4 joint indices and 4 weights as uint8, uint16 indices.
             No normals: the game's shader takes the facing from the triangle itself, as it does for the floor.
  skeleton:  each joint's parent, rest translation/rotation/scale, and inverse bind matrix (float32).
  clips:     the chosen clips sampled at FPS: rotations as int16 quaternions, translations as float16, per joint
             per frame. Rigid parts (a hat, a weapon parented to a bone) are baked as skinned to that bone.
  texture:   the model's PNG, as it is (KayKit's are ~15 KB palettes).
The whole binary is deflated (raw) and base64'd; src/js/37-figures.js parses the inflated bytes in the game and in
the Node tests. Sizes are reported per model so the budget (figures.json "budget") can be held.
"""
import base64
import json
import math
import struct
import sys
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCES = Path(r"F:\Claude Timeline\Local Storage\Claude and Magic models")
MAPPING = ROOT / "src" / "models" / "figures.json"
OUT = ROOT / "src" / "js" / "35c-figures.js"
FPS = 15

CT = {5120: ("b", 1), 5121: ("B", 1), 5122: ("h", 2), 5123: ("H", 2), 5125: ("I", 4), 5126: ("f", 4)}
NC = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}


# ---- glTF reading --------------------------------------------------------------------------------------------------
class Gltf:
    def __init__(self, path):
        b = path.read_bytes()
        assert b[:4] == b"glTF", path
        n = struct.unpack("<I", b[12:16])[0]
        self.j = json.loads(b[20:20 + n])
        off = 20 + n
        self.bin = b""
        while off < len(b):
            ln, typ = struct.unpack("<II", b[off:off + 8])
            if typ == 0x004E4942:
                self.bin = b[off + 8:off + 8 + ln]
            off += 8 + ln

    def accessor(self, i):
        """-> list of tuples (or scalars), normalized where the accessor says so"""
        a = self.j["accessors"][i]
        bv = self.j["bufferViews"][a["bufferView"]]
        fmt, size = CT[a["componentType"]]
        n = NC[a["type"]]
        stride = bv.get("byteStride") or size * n
        base = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
        out = []
        norm = a.get("normalized", False)
        mx = {"b": 127.0, "B": 255.0, "h": 32767.0, "H": 65535.0}.get(fmt)
        for k in range(a["count"]):
            v = struct.unpack_from("<" + fmt * n, self.bin, base + k * stride)
            if norm and mx:
                v = tuple(c / mx for c in v)
            out.append(v if n > 1 else v[0])
        return out

    def image(self, i):
        im = self.j["images"][i]
        bv = self.j["bufferViews"][im["bufferView"]]
        o = bv.get("byteOffset", 0)
        return self.bin[o:o + bv["byteLength"]]


# ---- small matrix helpers (column-major 4x4 as flat lists, glTF's way) ----------------------------------------------
def mat_identity():
    return [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]


def mat_mul(a, b):
    """a * b (column-major)"""
    out = [0.0] * 16
    for c in range(4):
        for r in range(4):
            out[c * 4 + r] = sum(a[k * 4 + r] * b[c * 4 + k] for k in range(4))
    return out


def mat_trs(t, r, s):
    x, y, z, w = r
    xx, yy, zz = x * x, y * y, z * z
    xy, xz, yz, wx, wy, wz = x * y, x * z, y * z, w * x, w * y, w * z
    m = [1 - 2 * (yy + zz), 2 * (xy + wz), 2 * (xz - wy), 0,
         2 * (xy - wz), 1 - 2 * (xx + zz), 2 * (yz + wx), 0,
         2 * (xz + wy), 2 * (yz - wx), 1 - 2 * (xx + yy), 0,
         t[0], t[1], t[2], 1]
    for c in range(3):
        for rr in range(3):
            m[c * 4 + rr] *= s[c]
    return m


def mat_inv(m):
    """general 4x4 inverse by Gauss-Jordan"""
    a = [[m[c * 4 + r] for c in range(4)] for r in range(4)]   # row-major rows
    inv = [[1.0 if i == j else 0.0 for j in range(4)] for i in range(4)]
    for i in range(4):
        p = max(range(i, 4), key=lambda r: abs(a[r][i]))
        a[i], a[p] = a[p], a[i]
        inv[i], inv[p] = inv[p], inv[i]
        d = a[i][i]
        assert abs(d) > 1e-12, "singular matrix"
        a[i] = [v / d for v in a[i]]
        inv[i] = [v / d for v in inv[i]]
        for r in range(4):
            if r != i and a[r][i]:
                f = a[r][i]
                a[r] = [v - f * w for v, w in zip(a[r], a[i])]
                inv[r] = [v - f * w for v, w in zip(inv[r], inv[i])]
    return [inv[r][c] for c in range(4) for r in range(4)]


def mat_apply(m, v):
    x, y, z = v
    return (m[0] * x + m[4] * y + m[8] * z + m[12], m[1] * x + m[5] * y + m[9] * z + m[13], m[2] * x + m[6] * y + m[10] * z + m[14])


def quat_mul(a, b):
    ax, ay, az, aw = a
    bx, by, bz, bw = b
    return (aw * bx + ax * bw + ay * bz - az * by, aw * by - ax * bz + ay * bw + az * bx, aw * bz + ax * by - ay * bx + az * bw, aw * bw - ax * bx - ay * by - az * bz)


def quat_rotate(q, v):
    x, y, z, w = q
    ux, uy, uz = (y * v[2] - z * v[1], z * v[0] - x * v[2], x * v[1] - y * v[0])
    uux, uuy, uuz = (y * uz - z * uy, z * ux - x * uz, x * uy - y * ux)
    return (v[0] + 2 * (w * ux + uux), v[1] + 2 * (w * uy + uuy), v[2] + 2 * (w * uz + uuz))


def trs_compose(outer, inner):
    """outer * inner, both (T, R, S), with the outer's scale taken as uniform enough"""
    (T1, R1, S1), (T2, R2, S2) = outer, inner
    t = tuple(T1[i] + c for i, c in enumerate(quat_rotate(R1, tuple(S1[i] * T2[i] for i in range(3)))))
    r = quat_mul(R1, R2)
    s = tuple(S1[i] * S2[i] for i in range(3))
    return (t, r, s)


def node_local(n):
    if "matrix" in n:
        return n["matrix"]
    return mat_trs(n.get("translation", [0, 0, 0]), n.get("rotation", [0, 0, 0, 1]), n.get("scale", [1, 1, 1]))


# ---- sampling the animations --------------------------------------------------------------------------------------
def sample(times, values, t):
    if t <= times[0]:
        return values[0]
    if t >= times[-1]:
        return values[-1]
    lo, hi = 0, len(times) - 1
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if times[mid] <= t:
            lo = mid
        else:
            hi = mid
    k = (t - times[lo]) / max(1e-9, times[hi] - times[lo])
    a, b = values[lo], values[hi]
    if len(a) == 4:   # a rotation: the shorter way round, then normalized
        d = sum(x * y for x, y in zip(a, b))
        if d < 0:
            b = tuple(-x for x in b)
        v = tuple(x + (y - x) * k for x, y in zip(a, b))
        ln = math.sqrt(sum(x * x for x in v)) or 1.0
        return tuple(x / ln for x in v)
    return tuple(x + (y - x) * k for x, y in zip(a, b))


# ---- one model ------------------------------------------------------------------------------------------------------
def bake_model(name, spec, mapping, report):
    pack = mapping["packs"][spec["pack"]]
    path = SOURCES / pack["dir"] / spec["file"]
    g = Gltf(path)
    j = g.j
    nodes = j["nodes"]
    skin = j["skins"][0]
    joints = skin["joints"]
    jindex = {nid: k for k, nid in enumerate(joints)}
    inv_bind = g.accessor(skin["inverseBindMatrices"])
    parent = {}
    for i, n in enumerate(nodes):
        for c in n.get("children", []):
            parent[c] = i
    # the joints' parents (within the skeleton), rest transforms; a root joint's rest takes in whatever stands above it
    # (Quaternius' armature node carries a scale of its own: the vertices are tiny and the armature makes them whole)
    jparent = [jindex.get(parent.get(nid, -1), -1) for nid in joints]
    rest = [(tuple(nodes[nid].get("translation", [0, 0, 0])), tuple(nodes[nid].get("rotation", [0, 0, 0, 1])), tuple(nodes[nid].get("scale", [1, 1, 1]))) for nid in joints]

    def above(nid):   # the TRS of everything above a root joint, composed
        chain = []
        p = parent.get(nid)
        while p is not None:
            chain.append(p)
            p = parent.get(p)
        T, R, S = (0.0, 0.0, 0.0), (0.0, 0.0, 0.0, 1.0), (1.0, 1.0, 1.0)
        for a in reversed(chain):
            n = nodes[a]
            T, R, S = trs_compose((T, R, S), (tuple(n.get("translation", [0, 0, 0])), tuple(n.get("rotation", [0, 0, 0, 1])), tuple(n.get("scale", [1, 1, 1]))))
        return (T, R, S)

    root_above = {k: above(nid) for k, nid in enumerate(joints) if jparent[k] < 0}
    rest = [trs_compose(root_above[k], rest[k]) if k in root_above else rest[k] for k in range(len(joints))]
    # world matrices at rest, for the rigid parts
    world = {}

    def world_of(nid):
        if nid in world:
            return world[nid]
        m = node_local(nodes[nid])
        if nid in parent:
            m = mat_mul(world_of(parent[nid]), m)
        world[nid] = m
        return m

    # which mesh nodes: the body parts, and the gear asked for
    wanted = list(spec.get("parts") or [n.get("name") for n in nodes if "mesh" in n and "skin" in n])
    gear = spec.get("gear") or {}
    wanted += [gear[k] for k in spec.get("wear", [])]
    pos, uv, col, jn, wt, idx = [], [], [], [], [], []
    textured = False
    mats = j.get("materials", [])
    for nid, n in enumerate(nodes):
        if "mesh" not in n or n.get("name") not in wanted:
            continue
        mesh = j["meshes"][n["mesh"]]
        rigid = "skin" not in n
        if rigid:   # find the joint it hangs from, and bake its vertices as bound to that joint
            p = parent.get(nid)
            while p is not None and p not in jindex:
                p = parent.get(p)
            assert p is not None, f"{name}: rigid part {n.get('name')} is not under a joint"
            jk = jindex[p]
            to_bind = mat_mul(mat_inv(inv_bind[jk]), mat_mul(mat_inv(world_of(p)), world_of(nid)))   # local-to-joint, then into bind space
        for prim in mesh["primitives"]:
            at = prim["attributes"]
            P = g.accessor(at["POSITION"])
            base = len(pos)
            mat = mats[prim["material"]] if "material" in prim else {}
            pbr = mat.get("pbrMetallicRoughness", {})
            bc = pbr.get("baseColorFactor", [1, 1, 1, 1])
            has_tex = "baseColorTexture" in pbr
            textured = textured or has_tex
            U = g.accessor(at["TEXCOORD_0"]) if ("TEXCOORD_0" in at and has_tex) else None
            if rigid:
                P = [mat_apply(to_bind, v) for v in P]
                J = [(jk, 0, 0, 0)] * len(P)
                W = [(1.0, 0, 0, 0)] * len(P)
            else:
                J = g.accessor(at["JOINTS_0"])
                W = g.accessor(at["WEIGHTS_0"])
            for k in range(len(P)):
                pos.append(P[k])
                uv.append(U[k] if U else (0.0, 0.0))
                col.append((255, 255, 255) if has_tex else tuple(min(255, int(round((c ** (1 / 2.2)) * 255))) for c in bc[:3]))   # (linear to sRGB, as the paints are)
                jn.append(tuple(int(x) for x in J[k]))
                ws = tuple(float(x) for x in W[k])
                s = sum(ws) or 1.0
                wt.append(tuple(w / s for w in ws))
            I = g.accessor(prim["indices"]) if "indices" in prim else list(range(len(P)))
            idx.extend(base + i for i in I)
    assert pos, f"{name}: no parts matched {wanted}"
    # the box, and the quantised mesh
    lo = [min(v[i] for v in pos) for i in range(3)]
    hi = [max(v[i] for v in pos) for i in range(3)]
    span = [max(1e-6, h - l) for l, h in zip(lo, hi)]
    out = bytearray()
    out += struct.pack("<II", len(pos), len(idx))
    for v in pos:
        out += struct.pack("<hhh", *[int(round((v[i] - lo[i]) / span[i] * 65534 - 32767)) for i in range(3)])
    for u in uv:
        out += struct.pack("<HH", max(0, min(65535, int(round(u[0] * 65535)))), max(0, min(65535, int(round(u[1] * 65535)))))
    for c in col:
        out += struct.pack("<BBB", *c)
    for q in jn:
        out += struct.pack("<BBBB", *[min(255, x) for x in q])
    for w in wt:
        out += struct.pack("<BBBB", *[max(0, min(255, int(round(x * 255)))) for x in w])
    big = len(pos) > 65535
    out += b"".join(struct.pack("<I" if big else "<H", i) for i in idx)
    mesh_len = len(out)
    # the skeleton
    out += struct.pack("<I", len(joints))
    for k in range(len(joints)):
        out += struct.pack("<h", jparent[k])
        t, r, s = rest[k]
        out += struct.pack("<10f", *t, *r, *s)
        out += struct.pack("<16f", *inv_bind[k])
    skel_len = len(out) - mesh_len
    # the clips: each sampled once and kept in a shared table (the nine KayKit figures carry the same library, so a
    # clip's bytes come out the same for each and are stored once); the model lists alias -> table index
    clip_names = {**mapping["rigs"].get(spec.get("rig", ""), {}).get("clips", {}), **spec.get("clips", {})} if spec.get("clips") is not False else {}
    anims = {a.get("name"): a for a in j.get("animations", [])}
    clips = []
    out += struct.pack("<I", len(clip_names))
    for alias, src in clip_names.items():
        a = anims.get(src)
        if a is None:
            raise SystemExit(f"{name}: clip {alias} -> {src} not in {path.name}; it has {sorted(anims)[:8]}...")
        chans = {}
        length = 0.0
        for ch in a["channels"]:
            tgt = ch["target"]
            if tgt["node"] not in jindex:
                continue
            smp = a["samplers"][ch["sampler"]]
            times = g.accessor(smp["input"])
            vals = g.accessor(smp["output"])
            chans[(jindex[tgt["node"]], tgt["path"])] = (times, vals)
            length = max(length, times[-1])
        frames = max(2, int(round(length * FPS)) + 1)
        blob = bytearray(struct.pack("<HBH", frames, FPS, len(joints)))
        for f in range(frames):
            t = min(length, f / FPS)
            for k in range(len(joints)):
                r = sample(*chans[(k, "rotation")], t) if (k, "rotation") in chans else nodes[joints[k]].get("rotation", [0, 0, 0, 1])
                tr = sample(*chans[(k, "translation")], t) if (k, "translation") in chans else nodes[joints[k]].get("translation", [0, 0, 0])
                if k in root_above:
                    tr, r, _ = trs_compose(root_above[k], (tuple(tr), tuple(r), (1.0, 1.0, 1.0)))
                blob += struct.pack("<hhhh", *[max(-32767, min(32767, int(round(c * 32767)))) for c in r])
                blob += struct.pack("<eee", *tr)
        cid = CLIPS.add(bytes(blob))
        name_b = alias.encode()
        out += struct.pack("<B", len(name_b)) + name_b + struct.pack("<I", cid)
        clips.append({"name": alias, "frames": frames, "id": cid})
    clips_len = sum(len(CLIPS.table[c["id"]]) for c in clips if CLIPS.fresh.get(c["id"]) == name)
    # the texture
    tex = b""
    if textured and j.get("images"):
        tex = g.image(0)
    out += struct.pack("<I", len(tex)) + tex
    report.append((name, len(pos), len(idx) // 3, len(joints), len(clips), mesh_len, skel_len, clips_len, len(tex), len(out)))
    return bytes(out), {"verts": len(pos), "tris": len(idx) // 3, "joints": len(joints), "box": [lo, hi], "textured": bool(tex), "clips": [c["name"] for c in clips], "frames": {c["name"]: c["frames"] for c in clips}, "pack": spec["pack"], "scale": spec.get("scale", 1), "up": spec.get("up", 1.0)}


class _Clips:
    """the shared clip table: a clip's sampled bytes stored once, found again by their hash"""
    def __init__(self):
        self.table, self.ids, self.fresh = [], {}, {}

    def add(self, blob, owner=None):
        import hashlib
        h = hashlib.sha1(blob).digest()
        if h not in self.ids:
            self.ids[h] = len(self.table)
            self.table.append(blob)
            self.fresh[self.ids[h]] = owner or CURRENT[0]
        return self.ids[h]


CLIPS = _Clips()
CURRENT = [""]


def bake(mapping):
    report = []
    blobs, manifest = [], {"models": {}}
    off = 0
    for name, spec in mapping["models"].items():
        CURRENT[0] = name
        b, m = bake_model(name, spec, mapping, report)
        m["offset"], m["length"] = off, len(b)
        manifest["models"][name] = m
        blobs.append(b)
        off += len(b)
    table = bytearray(struct.pack("<I", len(CLIPS.table)))
    for blob in CLIPS.table:
        table += struct.pack("<I", len(blob)) + blob
    manifest["clips"] = {"offset": off, "count": len(CLIPS.table), "bytes": len(table)}
    raw = b"".join(blobs) + bytes(table)
    deflated = zlib.compress(raw, 9)[2:-4]   # raw deflate, as DecompressionStream("deflate-raw") and inflateRawSync read it
    return raw, deflated, manifest, report


def main():
    mapping = json.loads(MAPPING.read_text(encoding="utf-8"))
    raw, deflated, manifest, report = bake(mapping)
    b64 = base64.b64encode(deflated).decode()
    print(f"{'model':18} {'verts':>6} {'tris':>6} {'jts':>4} {'clips':>5} {'mesh':>8} {'skel':>7} {'clips':>8} {'tex':>7} {'total':>8}")
    for r in report:
        print(f"{r[0]:18} {r[1]:6} {r[2]:6} {r[3]:4} {r[4]:5} {r[5]:8} {r[6]:7} {r[7]:8} {r[8]:7} {r[9]:8}")
    budget = mapping.get("budget", 4500000)
    print(f"raw {len(raw)} B, deflated {len(deflated)} B, base64 {len(b64)} B (budget {budget}); {len(manifest['models'])} models, {manifest['clips']['count']} clips shared ({manifest['clips']['bytes']} B)")
    if len(b64) > budget:
        raise SystemExit("over budget")
    if "--check" in sys.argv:
        return
    credits = mapping.get("credits", "")
    figures = mapping.get("figures", {})
    text = ("// GENERATED by tools/models.py from src/models/figures.json and the CC0 packs in Local Storage - do not edit.\n"
            "// The figures: rigged, animated bodies (UPGRADE_PLAN_60.md), as one deflated binary; 37-figures.js parses it.\n"
            "CM.figuresPack = {\n"
            f"  credits: {json.dumps(credits)},\n"
            f"  manifest: {json.dumps(manifest, separators=(',', ':'))},\n"
            f"  figures: {json.dumps(figures, separators=(',', ':'))},\n"
            f"  data: \"{b64}\",\n"
            "};\n")
    OUT.write_text(text, encoding="utf-8")
    print("wrote", OUT.name, len(text), "B")


if __name__ == "__main__":
    main()
