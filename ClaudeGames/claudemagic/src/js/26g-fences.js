"use strict";
// Fences and hedges with depth (v56.2, UPGRADE_PLAN_51.md): a fence is built now, not four pictures round its square - a
// post in the middle of each fence square, two rails running on to the next fence square (or across, alone), and pointed
// pickets with their own thickness, so a run of fence reads as one fence along its line. A hedge's top is a rounded,
// uneven crown instead of a flat lid. They stand in the way exactly as before. 26-surface.js calls CM.fenceModel for the
// fence and hedge squares, and leaves their old faces and tops out.
//   CM.fenceModel(o) -> { fences, hedges }   o: { quad, fl, index, solidKind(x, y), size }
{ CM.FENCE_MODEL = true;
  CM.fenceModel = (o) => { const { quad, fl, index, solidKind, size } = o, out = { fences: 0, hedges: 0 };
    const wood = index["solid:paling"] !== undefined ? index["solid:paling"] : index["solid:timber"], leaf = index["solid:hedge"];
    const box = (x0, y0, z0, x1, y1, z1, L, k = 1) => {
      quad([x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1], L, 0.95 * k); quad([x1, y0, z0], [x0, y0, z0], [x0, y1, z0], [x1, y1, z0], L, 0.8 * k);
      quad([x1, y0, z1], [x1, y0, z0], [x1, y1, z0], [x1, y1, z1], L, 0.88 * k); quad([x0, y0, z0], [x0, y0, z1], [x0, y1, z1], [x0, y1, z0], L, 0.74 * k);
      quad([x0, y1, z1], [x1, y1, z1], [x1, y1, z0], [x0, y1, z0], L, 1.05 * k); };
    for (let y = 0; y < size; y++) for (let x = 0; x < size; x++) { const kind = solidKind(x, y);
      if (kind === "fence" && wood !== undefined) { out.fences++; const cx = x + 0.5, cz = y + 0.5, H = 0.5;
        const runs = [[1, 0], [-1, 0], [0, 1], [0, -1]].filter(([dx, dy]) => solidKind(x + dx, y + dy) === "fence");
        const legs = runs.length ? runs : (solidKind(x, y - 1) === null || solidKind(x, y + 1) === null ? [[1, 0], [-1, 0]] : [[0, 1], [0, -1]]);   // (alone: across the way it's seen)
        box(cx - 0.04, 0, cz - 0.04, cx + 0.04, H + 0.06, cz + 0.04, wood, 0.9); box(cx - 0.05, H + 0.06, cz - 0.05, cx + 0.05, H + 0.08, cz + 0.05, wood, 1);   // the post and its cap
        for (const [dx, dy] of legs) { const ex = cx + dx * 0.5, ez = cz + dy * 0.5, t = 0.016;
          for (const ry of [0.14, 0.36]) box(Math.min(cx, ex) - (dy ? t : 0), ry, Math.min(cz, ez) - (dx ? t : 0), Math.max(cx, ex) + (dy ? t : 0), ry + 0.04, Math.max(cz, ez) + (dx ? t : 0), wood, 0.85);   // the rails
          for (let s = 0.1; s < 0.5; s += 0.12) { const px = cx + dx * s, pz = cz + dy * s, hw = 0.022, th = 0.012, oz = dx ? 0.03 : 0, ox = dy ? 0.03 : 0;   // the pickets, in front of the rails
            const a = dx ? [px - hw, pz + oz] : [px + ox, pz - hw], b = dx ? [px + hw, pz + oz] : [px + ox, pz + hw];
            for (const f of [-th, th]) { const fa = dx ? [a[0], a[1] + f] : [a[0] + f, a[1]], fb = dx ? [b[0], b[1] + f] : [b[0] + f, b[1]], mid = [(fa[0] + fb[0]) / 2, (fa[1] + fb[1]) / 2];
              quad([fa[0], 0.02, fa[1]], [fb[0], 0.02, fb[1]], [fb[0], H - 0.04, fb[1]], [fa[0], H - 0.04, fa[1]], wood, f < 0 ? 0.9 : 0.75);
              quad([fa[0], H - 0.04, fa[1]], [fb[0], H - 0.04, fb[1]], [mid[0], H + 0.02, mid[1]], [mid[0], H + 0.02, mid[1]], wood, f < 0 ? 0.95 : 0.8); } } } }
      if (kind === "hedge" && leaf !== undefined) { out.hedges++; const h = (CM.SOLID.hedge && CM.SOLID.hedge.h) || 0.55, r = new CM.Random(CM.hashSeed(`${fl.number}:hedge:${x},${y}`)), N = 4;   // a rounded crown: the top in a grid of bumps
        const top = (i, j) => { const u = i / N, v = j / N, edge = Math.min(u, 1 - u, v, 1 - v); const inside = (i > 0 && i < N && j > 0 && j < N) ? 1 : 0; return h + inside * (0.05 + Math.min(1, edge * 3) * 0.1 + r.next() * 0.06); };
        const T = []; for (let j = 0; j <= N; j++) { T.push([]); for (let i = 0; i <= N; i++) T[j].push(top(i, j)); }
        for (let j = 0; j < N; j++) for (let i = 0; i < N; i++) { const X = (k) => x + k / N, Z = (k) => y + k / N;
          quad([X(i), T[j + 1][i], Z(j + 1)], [X(i + 1), T[j + 1][i + 1], Z(j + 1)], [X(i + 1), T[j][i + 1], Z(j)], [X(i), T[j][i], Z(j)], leaf, 0.92 + ((i + j) % 2) * 0.1); } } }
    return out; };
}
