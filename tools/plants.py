"""The plants' pipeline (UPGRADE_PLAN_62.md phase 0): static, vertex-coloured low-poly meshes from the CC0 Quaternius
Ultimate Nature Pack (see src/models/CREDITS.txt), baked small enough to ride inside the one HTML file.

    python tools/plants.py            bake src/models/plants.json -> src/js/35d-plants.js (and report the sizes)
    python tools/plants.py --check    bake to memory and report only (the tests and ship do this)

Sources are read from the Local Storage folder (SOURCES below), never committed: only the baked file is. Each model's
.glb is read with the standard library alone (the figures' Gltf reader, tools/models.py) and written out as:
  header:  verts (uint32), indices (uint32)
  pos:     int16 x 3 a vertex over the model's box (the box is in the manifest, in metres as the pack has them)
  colour:  one uint8 a vertex: an index into the model's palette (the palette - sRGB triples - is in the manifest)
  index:   uint16 (uint32 when over 65535 vertices)
No normals and no uv: the shader takes the facing from the triangle, and the colour is a palette lookup. The whole
binary is deflated (raw) and base64'd; src/js/37b-plants.js parses the inflated bytes in the game and in the tests.
"""
import base64
import importlib.util
import json
import struct
import sys
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCES = Path(r"F:\Claude Timeline\Local Storage\Claude and Magic models")
MAPPING = ROOT / "src" / "models" / "plants.json"
OUT = ROOT / "src" / "js" / "35d-plants.js"

_spec = importlib.util.spec_from_file_location("cm_models", HERE / "models.py")
_models = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_models)
Gltf, mat_apply, node_local, mat_mul = _models.Gltf, _models.mat_apply, _models.node_local, _models.mat_mul


def world_of(nodes, parent, nid, cache):
    if nid in cache:
        return cache[nid]
    m = node_local(nodes[nid])
    if nid in parent:
        m = mat_mul(world_of(nodes, parent, parent[nid], cache), m)
    cache[nid] = m
    return m


_png_cache = {}


def read_png(path):
    """An 8-bit RGB or RGBA PNG, not interlaced, read with the standard library: (width, height, channels, rows)."""
    if path in _png_cache:
        return _png_cache[path]
    data = Path(path).read_bytes()
    assert data[:8] == bytes([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A]), path
    pos, idat, w = 8, b"", 0
    while pos < len(data):
        ln, = struct.unpack(">I", data[pos:pos + 4]); typ = data[pos + 4:pos + 8]; body = data[pos + 8:pos + 8 + ln]; pos += 12 + ln
        if typ == b"IHDR":
            w, h, depth, ctype, _, _, inter = struct.unpack(">IIBBBBB", body)
            assert depth == 8 and ctype in (2, 6) and inter == 0, (path, depth, ctype, inter)
        elif typ == b"IDAT":
            idat += body
    raw, bpp = zlib.decompress(idat), (4 if ctype == 6 else 3)
    stride, rows, prev, i = w * bpp, [], bytearray(w * bpp), 0
    for _ in range(h):
        f = raw[i]; i += 1; line = bytearray(raw[i:i + stride]); i += stride
        for x in range(stride):
            a = line[x - bpp] if x >= bpp else 0; b = prev[x]; c = prev[x - bpp] if x >= bpp else 0
            if f == 1: line[x] = (line[x] + a) & 255
            elif f == 2: line[x] = (line[x] + b) & 255
            elif f == 3: line[x] = (line[x] + (a + b) // 2) & 255
            elif f == 4:
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                line[x] = (line[x] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        rows.append(bytes(line)); prev = line
    _png_cache[path] = (w, h, bpp, rows)
    return _png_cache[path]


def texture_colours(g, j, glb, mat, prim):
    """(v133.0) a model painted from a colour-map texture (Kenney's kits): each vertex takes the texel under its uv."""
    t = mat.get("pbrMetallicRoughness", {}).get("baseColorTexture")
    if t is None or "TEXCOORD_0" not in prim["attributes"]:
        return None
    img = j["images"][j["textures"][t["index"]]["source"]]
    w, h, bpp, rows = read_png(Path(glb).parent / img["uri"])
    out = []
    for u, v in g.accessor(prim["attributes"]["TEXCOORD_0"]):
        x = min(w - 1, max(0, int((u % 1.0) * w))); y = min(h - 1, max(0, int((v % 1.0) * h)))
        out.append(tuple(rows[y][x * bpp:x * bpp + 3]))
    return out


def bake_model(name, spec, mapping):
    pack = mapping["packs"][spec["pack"]]
    glb = SOURCES / pack["dir"] / spec["file"]
    g = Gltf(glb)
    j = g.j
    nodes = j["nodes"]
    parent = {}
    for i, n in enumerate(nodes):
        for c in n.get("children", []):
            parent[c] = i
    mats = j.get("materials", [])
    cache = {}
    pos, col, idx = [], [], []
    palette, at = [], {}
    for nid, n in enumerate(nodes):
        if "mesh" not in n:
            continue
        W = world_of(nodes, parent, nid, cache)
        mesh = j["meshes"][n["mesh"]]
        for prim in mesh["primitives"]:
            P = [mat_apply(W, v) for v in g.accessor(prim["attributes"]["POSITION"])]
            mat = mats[prim["material"]] if "material" in prim else {}
            bc = mat.get("pbrMetallicRoughness", {}).get("baseColorFactor", [1, 1, 1, 1])
            c = tuple(min(255, int(round((v ** (1 / 2.2)) * 255))) for v in bc[:3])   # (linear to sRGB, as the paints are)
            if c not in at:
                at[c] = len(palette)
                palette.append(list(c))
            ci = at[c]
            base = len(pos)
            pos.extend(P)
            tex = texture_colours(g, j, glb, mat, prim)
            if tex is None:
                col.extend([ci] * len(P))
            else:
                for t in tex:
                    if t not in at:
                        at[t] = len(palette)
                        palette.append(list(t))
                    col.append(at[t])
            I = g.accessor(prim["indices"]) if "indices" in prim else list(range(len(P)))
            idx.extend(base + i for i in I)
    assert pos, f"{name}: no mesh"
    assert len(palette) <= 255, f"{name}: {len(palette)} colours"
    # a model may be trimmed to its lowest y as the foot: the box is kept as it is, the game reads it
    lo = [min(v[i] for v in pos) for i in range(3)]
    hi = [max(v[i] for v in pos) for i in range(3)]
    span = [max(1e-6, h - l) for l, h in zip(lo, hi)]
    out = bytearray(struct.pack("<II", len(pos), len(idx)))
    for v in pos:
        out += struct.pack("<hhh", *[int(round((v[i] - lo[i]) / span[i] * 65534 - 32767)) for i in range(3)])
    out += bytes(col)
    big = len(pos) > 65535
    out += b"".join(struct.pack("<I" if big else "<H", i) for i in idx)
    return bytes(out), {"verts": len(pos), "tris": len(idx) // 3, "box": [lo, hi], "big": big, "palette": palette, "tags": spec.get("tags", [])}


def bake(mapping):
    blobs, manifest, off = [], {"models": {}}, 0
    for name, spec in mapping["models"].items():
        b, m = bake_model(name, spec, mapping)
        m["offset"], m["length"] = off, len(b)
        manifest["models"][name] = m
        blobs.append(b)
        off += len(b)
    raw = b"".join(blobs)
    deflated = zlib.compress(raw, 9)[2:-4]
    return raw, deflated, manifest


def main():
    mapping = json.loads(MAPPING.read_text(encoding="utf-8"))
    raw, deflated, manifest = bake(mapping)
    b64 = base64.b64encode(deflated).decode()
    print(f"{'model':22} {'verts':>6} {'tris':>6} {'cols':>4} {'bytes':>8}")
    for name, m in manifest["models"].items():
        print(f"{name:22} {m['verts']:6} {m['tris']:6} {len(m['palette']):4} {m['length']:8}")
    budget = mapping.get("budget", 1200000)
    print(f"raw {len(raw)} B, deflated {len(deflated)} B, base64 {len(b64)} B (budget {budget}); {len(manifest['models'])} models")
    if len(b64) > budget:
        raise SystemExit("over budget")
    if "--check" in sys.argv:
        return
    text = ("// GENERATED by tools/plants.py from src/models/plants.json and the CC0 pack in Local Storage - do not edit.\n"
            "// The plants: static vertex-coloured meshes (UPGRADE_PLAN_62.md), as one deflated binary; 37b-plants.js parses it.\n"
            "CM.plantsPack = {\n"
            f"  credits: {json.dumps(mapping.get('credits', ''))},\n"
            f"  manifest: {json.dumps(manifest, separators=(',', ':'))},\n"
            f"  data: \"{b64}\",\n"
            "};\n")
    OUT.write_text(text, encoding="utf-8")
    print("wrote", OUT.name, len(text), "B")


if __name__ == "__main__":
    main()
