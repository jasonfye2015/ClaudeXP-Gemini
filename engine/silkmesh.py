"""Her silk and her small ones, made ready for the renderer.

    silk(web)        -> float32 (n, 11): every thread as a ribbon of triangles - position, the thread's direction, which
                        side of it (-1, 1), its width, its group, how free it is to move there, its phase. The vertex
                        shader turns each ribbon to face the eye (never thinner than a pixel), shivers it, and dips it
                        under his weight.
    spider_frames()  -> (float32 (frames * n, 9): position, normal, colour - every frame of every clip, one after
                        another; {clip: (first frame, frames, fps)}, vertices per frame)
"""
from pathlib import Path

import numpy as np

ASSETS = Path(__file__).resolve().parents[1] / "assets"


def silk(web):
    return ribbons(web.strands())


def ribbons(strands):
    """Threads -> ribbon vertices: [(points, width, group, free, phase)] -> float32 (n, 11)."""
    parts = []
    for pts, width, group, free, phase in strands:
        p = np.asarray(pts, np.float32)
        if len(p) < 2:
            continue
        f = np.asarray(free, np.float32)
        tan = np.zeros_like(p)
        tan[1:-1] = p[2:] - p[:-2]
        tan[0], tan[-1] = p[1] - p[0], p[-1] - p[-2]
        tan /= np.maximum(np.linalg.norm(tan, axis=1, keepdims=True), 1e-6)
        a, b = np.arange(len(p) - 1), np.arange(1, len(p))
        idx = np.stack([a, b, b, a, b, a], 1).reshape(-1)
        side = np.tile(np.array([-1, -1, 1, -1, 1, 1], np.float32), len(a))
        n = len(idx)
        parts.append(np.column_stack([p[idx], tan[idx], side, np.full(n, width, np.float32),
                                      np.full(n, group, np.float32), f[idx], np.full(n, phase, np.float32)]))
    return np.concatenate(parts).astype(np.float32) if parts else np.zeros((0, 11), np.float32)


def spider_frames():
    d = np.load(ASSETS / "spider.npz")
    col = d["colour"].astype(np.float32)
    clips, chunks, first = {}, [], 0
    for clip in ("walk", "idle"):
        frames = d[clip].astype(np.float32)
        tri = frames.reshape(len(frames), -1, 3, 3)
        nrm = np.cross(tri[:, :, 1] - tri[:, :, 0], tri[:, :, 2] - tri[:, :, 0])
        nrm /= np.maximum(np.linalg.norm(nrm, axis=-1, keepdims=True), 1e-9)
        nrm = np.repeat(nrm, 3, axis=1)
        for k in range(len(frames)):
            chunks.append(np.column_stack([frames[k], nrm[k], col]))
        clips[clip] = (first, len(frames), int(d[clip + "_fps"]))
        first += len(frames)
    return np.concatenate(chunks).astype(np.float32), clips, len(col)
