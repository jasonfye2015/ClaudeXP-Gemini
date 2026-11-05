"use strict";
// The Deep Wood, closer (v55.3, UPGRADE_PLAN_50.md): the trees stand in the ground now - roots spreading from the foot of
// every trunk, four to six of them, each its own length and way - and the forest floor has things in it: a stump here
// and there beside the trees, cut low, and rocks half sunk in the moss and the litter. Only what's seen: none of it is in
// the way, and none of it is on a path, a door or anything to be used. 26-surface.js calls this after the trees.
//   CM.woodDetail(o) -> { roots, stumps, rocks }   o: { quad, fl, index, trees, openAt, features, size, detail }
{ const R = (fl, k) => new CM.Random(CM.hashSeed(`${fl.number}:wood:${k}`));
  CM.woodDetail = (o) => { const { quad, fl, index, trees, openAt } = o, out = { roots: 0, stumps: 0, rocks: 0 };
    const wood = index["solid:bark"] !== undefined ? index["solid:bark"] : index["solid:timber"], cut = index["solid:stumptop"] !== undefined ? index["solid:stumptop"] : wood, stone = index["solid:sill"]; if (wood === undefined || o.detail === 0) return out;
    // a ridge along the ground from (x0, z0) to (x1, z1): high and wide at the trunk, nothing at its end
    const ridge = (x0, z0, x1, z1, h, w, L, k) => { const dx = x1 - x0, dz = z1 - z0, n = Math.hypot(dx, dz) || 1, px = -dz / n, pz = dx / n, w1 = w * 0.25;
      quad([x0 + px * w, 0, z0 + pz * w], [x1 + px * w1, 0, z1 + pz * w1], [x1, 0.008, z1], [x0, h, z0], L, k * 0.95);
      quad([x0, h, z0], [x1, 0.008, z1], [x1 - px * w1, 0, z1 - pz * w1], [x0 - px * w, 0, z0 - pz * w], L, k * 0.7); };
    for (const key of trees) { const [x, y] = key.split(",").map(Number); if (![[1, 0], [-1, 0], [0, 1], [0, -1], [1, 1], [1, -1], [-1, 1], [-1, -1]].some(([dx, dy]) => openAt(x + dx, y + dy))) continue;   /* (v58.0: only the trees one can walk up to - deep in the wood their feet are never seen) */ const r = R(fl, `roots:${key}`), cx = x + 0.5, cz = y + 0.5, n = 4 + Math.floor(r.next() * 3), a0 = r.next() * Math.PI * 2;
      const k = CM.treeVariant(fl, x, y) === 2 ? 1.05 : 0.9;   // (a birch's roots paler)
      for (let i = 0; i < n; i++) { const a = a0 + (i / n) * Math.PI * 2 + (r.next() - 0.5) * 0.6, len = 0.16 + r.next() * 0.18, s = 0.05;
        ridge(cx + Math.cos(a) * s, cz + Math.sin(a) * s, cx + Math.cos(a) * (s + len), cz + Math.sin(a) * (s + len), 0.05 + r.next() * 0.04, 0.026 + r.next() * 0.018, wood, k); out.roots++; } }
    if (fl.number !== -1) return out;
    const busy = (x, y) => (o.features && o.features[`${x},${y}`]) || (fl.things && fl.things[`${x},${y}`]) || (CM.groundAt && ["dirt", "planks", "tilled", "cobbles", "flags"].includes(CM.groundAt(fl, x, y)));
    const ring = (cx, cz, rad, n, a0, jit, r) => { const p = []; for (let i = 0; i < n; i++) { const a = a0 + (i / n) * Math.PI * 2; const rr = rad * (1 - jit + r.next() * jit * 2); p.push([cx + Math.cos(a) * rr, cz + Math.sin(a) * rr]); } return p; };
    const nearTree = (x, y) => CM.DIRS.find(([dx, dy]) => trees.has(`${x + dx},${y + dy}`));
    for (let y = 1; y < o.size - 1; y++) for (let x = 1; x < o.size - 1; x++) { if (!openAt(x, y) || busy(x, y)) continue; const r = R(fl, `floor:${x},${y}`), roll = r.next(), t = nearTree(x, y);
      if (t && roll < 0.06) {   // a stump, toward the tree it stands beside: eight sides of bark, the cut top paler
        const cx = x + 0.5 + t[0] * 0.28 + (r.next() - 0.5) * 0.2, cz = y + 0.5 + t[1] * 0.28 + (r.next() - 0.5) * 0.2, rad = 0.07 + r.next() * 0.05, h = 0.08 + r.next() * 0.12, P = ring(cx, cz, rad, 8, r.next(), 0.12, r), Q = P.map(([px, pz]) => [cx + (px - cx) * 1.25, cz + (pz - cz) * 1.25]);
        for (let i = 0; i < 8; i++) { const j = (i + 1) % 8; quad([Q[i][0], 0, Q[i][1]], [Q[j][0], 0, Q[j][1]], [P[j][0], h, P[j][1]], [P[i][0], h, P[i][1]], wood, 0.62 + 0.25 * Math.abs(Math.cos(i))); }
        for (let i = 0; i < 8; i++) { const j = (i + 1) % 8; quad([cx, h + 0.01, cz], [P[i][0], h, P[i][1]], [P[j][0], h, P[j][1]], [cx, h + 0.01, cz], cut, 1.0); }
        out.stumps++; continue; }
      if (stone !== undefined && roll > 0.92) {   // a rock half sunk: a low ring, a shoulder and a top, all a little uneven
        const cx = x + 0.25 + r.next() * 0.5, cz = y + 0.25 + r.next() * 0.5, rad = 0.1 + r.next() * 0.16, h = rad * (0.45 + r.next() * 0.35), n = 7, a0 = r.next() * 6;
        const B = ring(cx, cz, rad, n, a0, 0.18, r), M = ring(cx, cz, rad * 0.78, n, a0 + 0.2, 0.15, r), top = [cx + (r.next() - 0.5) * rad * 0.3, h, cz + (r.next() - 0.5) * rad * 0.3];
        for (let i = 0; i < n; i++) { const j = (i + 1) % n, k = 0.62 + 0.3 * ((Math.cos(a0 + (i / n) * 6.283) + 1) / 2);
          quad([B[i][0], 0, B[i][1]], [B[j][0], 0, B[j][1]], [M[j][0], h * 0.62, M[j][1]], [M[i][0], h * 0.62, M[i][1]], stone, k);
          quad([M[i][0], h * 0.62, M[i][1]], [M[j][0], h * 0.62, M[j][1]], top, top, stone, k + 0.18); }
        out.rocks++; } }
    return out; };
}
