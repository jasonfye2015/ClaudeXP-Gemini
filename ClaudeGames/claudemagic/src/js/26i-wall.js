"use strict";
// The town wall and keep (v57.0 on, UPGRADE_PLAN_52.md): the ring wall's top is battlemented now - along its outer edge
// (and its town side) a low parapet and on it two merlons a square, with the crenels between them to see out through, capped in the walk's
// stone, turning the corners where the wall does. 26-surface.js calls this for the town (CM.wallDetail).
//   CM.wallDetail(o) -> { merlons, buttresses, slits }   o: { quad, fl, index, size, solidKind(x, y) }
{ CM.WALL_DETAIL = true;
  CM.wallDetail = (o) => { const { quad, index, size, solidKind } = o, out = { merlons: 0, buttresses: 0, slits: 0, gate: 0 };
    const face = index["solid:townwall"], cap = index["solid:townwall:top"] !== undefined ? index["solid:townwall:top"] : face; if (face === undefined) return out;
    const H = (CM.SOLID.townwall && CM.SOLID.townwall.h) || 1.3, walled = (k) => k === "townwall" || k === "tower";
    // a block on the wall top, in the square's own frame: u along the edge (0..1), v in from it (0..1)
    const block = (x, y, d, u0, u1, v0, v1, y0, y1, k = 1) => {
      const P = (u, v, yy) => d === 0 ? [x + u, yy, y + v] : d === 2 ? [x + 1 - u, yy, y + 1 - v] : d === 1 ? [x + 1 - v, yy, y + u] : [x + v, yy, y + 1 - u];
      quad(P(u0, v0, y0), P(u1, v0, y0), P(u1, v0, y1), P(u0, v0, y1), face, 0.92 * k);      // the outer face
      quad(P(u1, v1, y0), P(u0, v1, y0), P(u0, v1, y1), P(u1, v1, y1), face, 0.78 * k);      // the inner face
      quad(P(u0, v1, y0), P(u0, v0, y0), P(u0, v0, y1), P(u0, v1, y1), face, 0.84 * k);      // its ends
      quad(P(u1, v0, y0), P(u1, v1, y0), P(u1, v1, y1), P(u1, v0, y1), face, 0.84 * k);
      quad(P(u0, v1, y1), P(u1, v1, y1), P(u1, v0, y1), P(u0, v0, y1), cap, 1.05 * k); };      // the cap
    for (let y = 0; y < size; y++) for (let x = 0; x < size; x++) { if (solidKind(x, y) !== "townwall") continue;
      // every edge of the walk that isn't along more wall: the outer edges (onto trees, the cliff, the edge of the world), and the
      // town's side too - a walk battlemented both ways, and the merlons seen from the streets (on a wall two squares thick the outer ones sink out of sight)
      const sides = [[0, -1, 0], [1, 0, 1], [0, 1, 2], [-1, 0, 3]].filter(([dx, dy]) => !walled(solidKind(x + dx, y + dy)));
      for (const [, , d] of sides) {
        block(x, y, d, 0, 1, 0, 0.16, H, H + 0.07, 0.95);                                             // the parapet, the length of the square
        for (const [u0, u1] of [[0.06, 0.36], [0.56, 0.86]]) { block(x, y, d, u0, u1, 0, 0.16, H + 0.07, H + 0.3); out.merlons++; } }
      // (v57.4) ivy up the town's side of the wall, here and there
      if (index["solid:ivy"] !== undefined) for (const [dx, dy, d] of [[0, -1, 0], [1, 0, 1], [0, 1, 2], [-1, 0, 3]]) { if (solidKind(x + dx, y + dy) !== null || (x * 11 + y * 5) % 4 !== 1) continue;
        const P = (u, v, yy) => d === 0 ? [x + u, yy, y + v] : d === 2 ? [x + 1 - u, yy, y + 1 - v] : d === 1 ? [x + 1 - v, yy, y + u] : [x + v, yy, y + 1 - u];
        const u0 = ((x * 3 + y) % 5) * 0.08, top = H * (0.5 + ((x + y * 3) % 4) * 0.12);
        quad(P(u0, -0.006, 0), P(u0 + 0.6, -0.006, 0), P(u0 + 0.6, -0.006, top), P(u0, -0.006, top), index["solid:ivy"], 0.9); out.ivy = (out.ivy || 0) + 1; }
      // (v57.1) a buttress on the town's side, one square in three: a pier leaning against the wall, its top sloping down and away
      for (const [dx, dy, d] of [[0, -1, 0], [1, 0, 1], [0, 1, 2], [-1, 0, 3]]) { if (solidKind(x + dx, y + dy) !== null || (x * 7 + y * 13) % 3 !== 0) continue;
        const P = (u, v, yy) => d === 0 ? [x + u, yy, y + v] : d === 2 ? [x + 1 - u, yy, y + 1 - v] : d === 1 ? [x + 1 - v, yy, y + u] : [x + v, yy, y + 1 - u];
        const u0 = 0.38, u1 = 0.62, v = -0.24, lo = H * 0.5, hi = H * 0.86;
        quad(P(u0, v, 0), P(u1, v, 0), P(u1, v, lo), P(u0, v, lo), face, 0.9);                                         // its front
        quad(P(u0, 0, 0), P(u0, v, 0), P(u0, v, lo), P(u0, 0, hi), face, 0.78); quad(P(u1, v, 0), P(u1, 0, 0), P(u1, 0, hi), P(u1, v, lo), face, 0.82);   // its sides
        quad(P(u0, v, lo), P(u1, v, lo), P(u1, 0, hi), P(u0, 0, hi), cap, 1.0); out.buttresses++; } }
    // (v57.1) arrow slits in the gate towers: one in each of the eight faces, high and low by turns, a dark slot in a stone surround
    const T = CM.TOWER; if (T && o.fl && o.fl.kinds) for (const [tk, kind] of Object.entries(o.fl.kinds)) { if (kind !== "tower") continue; const [tx, ty] = tk.split(",").map(Number), cx = tx + 0.5, cz = ty + 0.5, ap = T.r * Math.cos(Math.PI / 8) + 0.006;
      for (let i = 0; i < 8; i++) { const a = (Math.PI / 4) * (i + 1), nx = Math.cos(a), nz = Math.sin(a), tx2 = -nz, tz2 = nx, ym = T.h * (i % 2 ? 0.62 : 0.36);
        const S = (t, yy, r) => [cx + nx * r + tx2 * t, yy, cz + nz * r + tz2 * t];
        quad(S(-0.055, ym - 0.2, ap), S(0.055, ym - 0.2, ap), S(0.055, ym + 0.2, ap), S(-0.055, ym + 0.2, ap), cap, 0.95);   // the dressed surround
        quad(S(-0.022, ym - 0.16, ap + 0.003), S(0.022, ym - 0.16, ap + 0.003), S(0.022, ym + 0.16, ap + 0.003), S(-0.022, ym + 0.16, ap + 0.003), cap, 0.07); out.slits++; } }
    // (v57.2) the West Gate: an arch across the road on the gate's square - two thick jambs, a round arch with its soffit, the stonework
    // over it to a capped top with three merlons. The road runs through it as before.
    const G = CM.TOWN_AT && CM.TOWN_AT.woodgate; if (G && o.fl && o.fl.number === 0) { const [gx, gy] = G, ew = solidKind(gx - 1, gy) === null || solidKind(gx + 1, gy) === null;
      // in the arch's own frame: a across the road (0..1 over the gate's square, the jambs beyond), t along it (the arch's depth)
      const P = (a2, t, yy) => (ew ? [gx + t, yy, gy + a2] : [gx + a2, yy, gy + t]), t0 = 0.05, t1 = 0.65, spring = 1.0, top = 1.68, N = 10;
      const slab = (a0, a1, y0, y1, k = 1) => { quad(P(a0, t0, y0), P(a1, t0, y0), P(a1, t0, y1), P(a0, t0, y1), face, 0.9 * k); quad(P(a1, t1, y0), P(a0, t1, y0), P(a0, t1, y1), P(a1, t1, y1), face, 0.8 * k);
        quad(P(a0, t1, y0), P(a0, t0, y0), P(a0, t0, y1), P(a0, t1, y1), face, 0.7 * k); quad(P(a1, t0, y0), P(a1, t1, y0), P(a1, t1, y1), P(a1, t0, y1), face, 0.7 * k); };
      slab(-0.45, 0, 0, top); slab(1, 1.45, 0, top);                                                                    // the jambs
      for (let i = 0; i < N; i++) { const q0 = Math.PI * (i / N), q1 = Math.PI * ((i + 1) / N), A = [0.5 - 0.5 * Math.cos(q0), spring + 0.5 * Math.sin(q0)], B = [0.5 - 0.5 * Math.cos(q1), spring + 0.5 * Math.sin(q1)];
        quad(P(A[0], t0, A[1]), P(B[0], t0, B[1]), P(B[0], t0, top), P(A[0], t0, top), face, 0.9); quad(P(B[0], t1, B[1]), P(A[0], t1, A[1]), P(A[0], t1, top), P(B[0], t1, top), face, 0.8);   // the spandrels
        quad(P(A[0], t1, A[1]), P(B[0], t1, B[1]), P(B[0], t0, B[1]), P(A[0], t0, A[1]), cap, 0.55); }                                              // the soffit, shaded
      for (const [x0, x1] of [[0, 0.04], [0.96, 1]]) slab(x0, x1, 0, spring, 0.85);                                     // (the jambs' inner faces, to the springing)
      quad(P(-0.45, t0, top), P(1.45, t0, top), P(1.45, t1, top), P(-0.45, t1, top), cap, 1.05);                        // the top
      for (const [m0, m1] of [[-0.35, 0.05], [0.3, 0.7], [0.95, 1.35]]) { slab(m0, m1, top, top + 0.26); quad(P(m0, t0, top + 0.26), P(m1, t0, top + 0.26), P(m1, t1, top + 0.26), P(m0, t1, top + 0.26), cap, 1.05); }
      out.gate = 1; }
    return out; };
}
