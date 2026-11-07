"""The figures: Claude and Magic's rigged, animated CC0 bodies (KayKit, Quaternius), read from assets/figures/ (see
tools/import_cm.py) - the same binary Claude and Magic's 37-figures.js reads, read here with numpy.

    pack = Pack.load()                    every model, parsed; clips posed lazily and kept
    m = pack.model("skeleton_mage")       a Model: arrays ready for a vertex buffer, its skeleton and clips
    m.skin_matrices("walk", t)            (joints, 4, 4) float32: each joint's world * inverse bind at t seconds
    pack.figure("monster:Goblin")         the mapping: {model, scale, tint, wear, lift?} (None when unmapped/painted)

No GL here: the renderer uploads what this gives it, and the tests read it the same way."""
import json
import struct
import zlib
from pathlib import Path

import numpy as np

ASSETS = Path(__file__).resolve().parents[1] / "assets" / "figures"
FPS_SAMPLES = 15


def _trs(t, q, s):
    """(n,3),(n,4),(n,3) -> (n,4,4) row-major matrices (M @ v for column vectors)."""
    x, y, z, w = q[:, 0], q[:, 1], q[:, 2], q[:, 3]
    xx, yy, zz, xy, xz, yz, wx, wy, wz = x * x, y * y, z * z, x * y, x * z, y * z, w * x, w * y, w * z
    m = np.zeros((len(t), 4, 4), np.float32)
    m[:, 0, 0] = (1 - 2 * (yy + zz)) * s[:, 0]
    m[:, 1, 0] = 2 * (xy + wz) * s[:, 0]
    m[:, 2, 0] = 2 * (xz - wy) * s[:, 0]
    m[:, 0, 1] = 2 * (xy - wz) * s[:, 1]
    m[:, 1, 1] = (1 - 2 * (xx + zz)) * s[:, 1]
    m[:, 2, 1] = 2 * (yz + wx) * s[:, 1]
    m[:, 0, 2] = 2 * (xz + wy) * s[:, 2]
    m[:, 1, 2] = 2 * (yz - wx) * s[:, 2]
    m[:, 2, 2] = (1 - 2 * (xx + yy)) * s[:, 2]
    m[:, :3, 3] = t
    m[:, 3, 3] = 1
    return m


class Clip:
    def __init__(self, frames, fps, joints, rot, trans):
        self.frames, self.fps, self.joints = frames, fps, joints
        self.rot = rot.reshape(frames, joints, 4).astype(np.float32) / 32767.0
        self.trans = trans.reshape(frames, joints, 3).astype(np.float32)

    @property
    def length(self):
        return self.frames / self.fps


class Model:
    def __init__(self, name, meta):
        self.name, self.meta = name, meta
        self.posed = {}                      # clip name -> (frames, joints, 4, 4) skinning matrices

    # the pose at one sampled frame (or the rest pose), for every joint
    def _pose(self, rot, trans):
        n = self.n_joints
        local = _trs(trans, rot, self.rest_s)
        world = np.empty_like(local)
        done = np.zeros(n, bool)            # (parents needn't come first in the baked order: each walks up)

        def solve(j):
            if done[j]:
                return world[j]
            p = self.parent[j]
            world[j] = local[j] if p < 0 else solve(p) @ local[j]
            done[j] = True
            return world[j]

        for j in range(n):
            solve(j)
        return world @ self.inv_bind

    def skin_frames(self, clip_name):
        """(frames, joints, 4, 4) for a clip, made once; None for the rest pose (one frame)."""
        key = clip_name or ""
        if key not in self.posed:
            c = self.clips.get(clip_name) if clip_name else None
            if c is None:
                self.posed[key] = self._pose(self.rest_r, self.rest_t)[None]
            else:
                self.posed[key] = np.stack([self._pose(c.rot[f], c.trans[f]) for f in range(c.frames)])
        return self.posed[key]

    def skin_matrices(self, clip_name, t, once=False):
        """Each joint's skinning matrix t seconds into the clip (looping, or held at its end when once)."""
        frames = self.skin_frames(clip_name if clip_name in self.clips else None)
        if len(frames) == 1:
            return frames[0]
        c = self.clips[clip_name]
        f = t * c.fps
        if once:
            f = min(f, c.frames - 1.001)
        else:
            f %= c.frames
        a = int(f)
        b = min(c.frames - 1, a + 1) if once else (a + 1) % c.frames
        k = f - a
        return frames[a] * (1 - k) + frames[b] * k

    def has(self, clip):
        return clip in self.clips

    def measure(self):
        """The model at rest, posed: (lo, hi) in its own units (Quaternius' raw mesh is tiny before its armature)."""
        if getattr(self, "_measured", None) is None:
            M = self.skin_frames(None)[0]
            v = self.skinned(M)
            self._measured = (v.min(0), v.max(0))
        return self._measured

    def skinned(self, M):
        p = np.concatenate([self.positions, np.ones((len(self.positions), 1), np.float32)], 1)
        out = np.zeros((len(p), 3), np.float32)
        for k in range(4):
            w = self.weights[:, k:k + 1]
            mats = M[self.joints[:, k]]                       # (n,4,4)
            out += w * np.einsum("nij,nj->ni", mats, p)[:, :3]
        return out

    def height(self):
        lo, hi = self.measure()
        return max(1e-3, float(hi[1] - lo[1]))

    def width(self):
        lo, hi = self.measure()
        return max(1e-3, float(hi[0] - lo[0]), float(hi[2] - lo[2]))

    def foot(self):
        return float(self.measure()[0][1])


class Pack:
    _loaded = None

    def __init__(self, data, meta):
        self.meta = meta
        self.manifest = meta["manifest"]
        self.figures = meta["figures"]
        self.credits = meta.get("credits", "")
        self.data = data
        self._models = {}
        self._clips = self._parse_clips()

    @classmethod
    def load(cls):
        if cls._loaded is None:
            meta = json.loads((ASSETS / "figures.json").read_text(encoding="utf-8"))
            data = zlib.decompress((ASSETS / "figures.bin").read_bytes(), -15)
            cls._loaded = cls(data, meta)
        return cls._loaded

    def _parse_clips(self):
        T = self.manifest["clips"]
        b, o = self.data, T["offset"]
        (count,) = struct.unpack_from("<I", b, o)
        o += 4
        clips = []
        rec = np.dtype([("r", "<i2", 4), ("t", "<f2", 3)])
        for _ in range(count):
            (ln,) = struct.unpack_from("<I", b, o)
            o += 4
            frames, fps, joints = struct.unpack_from("<HBH", b, o)
            arr = np.frombuffer(b, rec, frames * joints, o + 5)
            assert 5 + arr.nbytes == ln, "clip length"
            clips.append(Clip(frames, fps, joints, arr["r"].copy(), arr["t"].astype(np.float32)))
            o += ln
        return clips

    def names(self):
        return list(self.manifest["models"])

    def model(self, name):
        if name in self._models:
            return self._models[name]
        meta = self.manifest["models"][name]
        b, o = self.data, meta["offset"]
        end = o + meta["length"]
        verts, n_idx = struct.unpack_from("<II", b, o)
        o += 8
        m = Model(name, meta)
        lo, hi = np.array(meta["box"][0], np.float32), np.array(meta["box"][1], np.float32)
        q = np.frombuffer(b, "<i2", verts * 3, o).reshape(verts, 3).astype(np.float32)
        o += verts * 6
        m.positions = lo + (q + 32767) / 65534 * (hi - lo)
        m.uv = np.frombuffer(b, "<u2", verts * 2, o).reshape(verts, 2).astype(np.float32) / 65535
        o += verts * 4
        m.colours = np.frombuffer(b, "u1", verts * 3, o).reshape(verts, 3).astype(np.float32) / 255
        o += verts * 3
        m.joints = np.frombuffer(b, "u1", verts * 4, o).reshape(verts, 4).astype(np.int64)
        o += verts * 4
        m.weights = np.frombuffer(b, "u1", verts * 4, o).reshape(verts, 4).astype(np.float32) / 255
        o += verts * 4
        big = verts > 65535
        m.indices = np.frombuffer(b, "<u4" if big else "<u2", n_idx, o).astype(np.uint32)
        o += n_idx * (4 if big else 2)
        (n,) = struct.unpack_from("<I", b, o)
        o += 4
        m.n_joints = n
        m.parent = np.zeros(n, np.int64)
        rest = np.zeros((n, 10), np.float32)
        inv = np.zeros((n, 4, 4), np.float32)
        for k in range(n):
            (m.parent[k],) = struct.unpack_from("<h", b, o)
            o += 2
            rest[k] = struct.unpack_from("<10f", b, o)
            o += 40
            inv[k] = np.array(struct.unpack_from("<16f", b, o), np.float32).reshape(4, 4).T   # (column-major in)
            o += 64
        m.rest_t, m.rest_r, m.rest_s, m.inv_bind = rest[:, :3], rest[:, 3:7], rest[:, 7:10], inv
        (nc,) = struct.unpack_from("<I", b, o)
        o += 4
        m.clips = {}
        for _ in range(nc):
            ln = b[o]
            name_c = b[o + 1:o + 1 + ln].decode()
            o += 1 + ln
            (cid,) = struct.unpack_from("<I", b, o)
            o += 4
            m.clips[name_c] = self._clips[cid]
        (tl,) = struct.unpack_from("<I", b, o)
        o += 4
        m.texture = bytes(b[o:o + tl]) if tl else None
        o += tl
        assert o == end, f"figure {name}: read {o - meta['offset']} of {meta['length']}"
        self._models[name] = m
        return m

    def figure(self, key):
        f = self.figures.get(key)
        return f if isinstance(f, dict) else None


class Plants:
    """The plants: static, vertex-coloured meshes (trees, bushes, rocks, stumps, barrels, crates), from
    assets/figures/plants.* (Claude and Magic's 35d-plants.js, imported). plants.mesh(name) -> (positions (n,3),
    colours (n,3) 0..1 sRGB, indices), in metres as the pack has them; plants.tags(name) -> its tags."""
    _loaded = None

    def __init__(self, data, meta):
        self.data, self.manifest, self.credits = data, meta["manifest"], meta.get("credits", "")
        self._cache = {}

    @classmethod
    def load(cls):
        if cls._loaded is None:
            meta = json.loads((ASSETS / "plants.json").read_text(encoding="utf-8"))
            cls._loaded = cls(zlib.decompress((ASSETS / "plants.bin").read_bytes(), -15), meta)
        return cls._loaded

    def names(self):
        return list(self.manifest["models"])

    def tags(self, name):
        return self.manifest["models"][name].get("tags", [])

    def box(self, name):
        lo, hi = self.manifest["models"][name]["box"]
        return np.array(lo, np.float32), np.array(hi, np.float32)

    def mesh(self, name):
        if name in self._cache:
            return self._cache[name]
        m = self.manifest["models"][name]
        b, o = self.data, m["offset"]
        verts, n_idx = struct.unpack_from("<II", b, o)
        o += 8
        lo, hi = self.box(name)
        q = np.frombuffer(b, "<i2", verts * 3, o).reshape(verts, 3).astype(np.float32)
        o += verts * 6
        pos = lo + (q + 32767) / 65534 * (hi - lo)
        ci = np.frombuffer(b, "u1", verts, o).astype(np.int64)
        o += verts
        pal = np.array(m["palette"], np.float32) / 255
        big = verts > 65535
        idx = np.frombuffer(b, "<u4" if big else "<u2", n_idx, o).astype(np.uint32)
        o += n_idx * (4 if big else 2)
        assert o == m["offset"] + m["length"], f"plant {name}: read {o - m['offset']} of {m['length']}"
        self._cache[name] = (pos, pal[np.minimum(ci, len(pal) - 1)], idx)
        return self._cache[name]
