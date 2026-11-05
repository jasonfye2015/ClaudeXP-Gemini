"use strict";
// The well, built (v56.1, UPGRADE_PLAN_51.md): the Square's well is stonework now, not a picture - a round wall of dressed
// stone with a capstone rim, dark water down inside it, two posts carrying a little shingled roof, the windlass across
// them with its crank, and a bucket on its rope. 26-surface.js builds it into the town's mesh (CM.wellModel); the party
// can still step onto its square to draw water, and while they stand there it folds away (40-render.js: uHideAt).
//   CM.wellModel(o) -> how many wells   o: { quad, out, fl, index }
//   CM.WELL_HIDE = 0.6: how far from its middle the well reaches (what uHideAt folds)
{ CM.WELL_MODEL = true; CM.WELL_HIDE = 0.6;
  CM.wellModel = (o) => { const { quad, out, fl, index } = o; let n = 0;
    const stone = index["solid:sill"] !== undefined ? index["solid:sill"] : index["solid:townwall"], wood = index["solid:timber"] !== undefined ? index["solid:timber"] : stone, roof = index["solid:roof"] !== undefined ? index["solid:roof"] : wood, water = index.water;
    if (stone === undefined) return 0;
    for (const [k, t] of Object.entries(fl.things || {})) { if (!t || t.type !== "well") continue; const [x, y] = k.split(",").map(Number), cx = x + 0.5, cz = y + 0.5; n++;
      const N = 14, Ro = 0.34, Ri = 0.27, Hw = 0.36, P = (r, i, h) => { const a = (i / N) * Math.PI * 2; return [cx + Math.cos(a) * r, h, cz + Math.sin(a) * r]; };
      for (let i = 0; i < N; i++) { const j = i + 1, lit = 0.72 + 0.28 * Math.max(0, Math.cos((i / N) * Math.PI * 2 - 0.9));
        quad(P(Ro, i, 0), P(Ro, j, 0), P(Ro, j, Hw), P(Ro, i, Hw), stone, lit);                               // the wall, outside
        quad(P(Ri, j, 0.06), P(Ri, i, 0.06), P(Ri, i, Hw), P(Ri, j, Hw), stone, 0.42);                       // inside, in shadow
        quad(P(Ri - 0.02, i, Hw + 0.05), P(Ri - 0.02, j, Hw + 0.05), P(Ro + 0.025, j, Hw + 0.05), P(Ro + 0.025, i, Hw + 0.05), stone, 1.15);   // the capstones
        quad(P(Ro + 0.025, i, Hw), P(Ro + 0.025, j, Hw), P(Ro + 0.025, j, Hw + 0.05), P(Ro + 0.025, i, Hw + 0.05), stone, lit * 0.95);
        quad(P(Ri - 0.02, j, Hw), P(Ri - 0.02, i, Hw), P(Ri - 0.02, i, Hw + 0.05), P(Ri - 0.02, j, Hw + 0.05), stone, 0.6); }
      if (water !== undefined && out) for (let i = 0; i < N; i++) {   // the water, a little down: the river's own ripple and sky (glow 4)
        const A = [cx, 0.07, cz], B = P(Ri, i, 0.07), C = P(Ri, i + 1, 0.07), uv = (q) => [(q[0] - cx) * 2 + 0.5, (q[2] - cz) * 2 + 0.5];
        for (const q of [A, B, C]) { const [u, v] = uv(q); out.push(q[0], q[1], q[2], u, v, water, 0.8, 0, 1, 4); } }
      const box = (x0, y0, z0, x1, y1, z1, L, k = 1) => { const V = (a, b, c) => [cx + a, b, cz + c];
        quad(V(x0, y0, z1), V(x1, y0, z1), V(x1, y1, z1), V(x0, y1, z1), L, 0.95 * k); quad(V(x1, y0, z0), V(x0, y0, z0), V(x0, y1, z0), V(x1, y1, z0), L, 0.78 * k);
        quad(V(x1, y0, z1), V(x1, y0, z0), V(x1, y1, z0), V(x1, y1, z1), L, 0.86 * k); quad(V(x0, y0, z0), V(x0, y0, z1), V(x0, y1, z1), V(x0, y1, z0), L, 0.72 * k);
        quad(V(x0, y1, z1), V(x1, y1, z1), V(x1, y1, z0), V(x0, y1, z0), L, 1.05 * k); };
      const px = Ro - 0.01, top = 1.02;
      for (const s of [-1, 1]) box(s * px - 0.03, Hw, -0.03, s * px + 0.03, top, 0.03, wood);                     // the posts, set in the wall
      box(-px, 0.78, -0.022, px, 0.824, 0.022, wood, 0.9);                                                      // the windlass
      box(px + 0.03, 0.79, -0.012, px + 0.1, 0.81, 0.012, wood, 0.85); box(px + 0.085, 0.71, -0.012, px + 0.105, 0.81, 0.012, wood, 0.85);   // its crank
      quad([cx - 0.006, 0.78, cz], [cx + 0.006, 0.78, cz], [cx + 0.006, 0.5, cz], [cx - 0.006, 0.5, cz], wood, 0.6);   // the rope
      quad([cx, 0.78, cz - 0.006], [cx, 0.78, cz + 0.006], [cx, 0.5, cz + 0.006], [cx, 0.5, cz - 0.006], wood, 0.6);
      box(-0.05, 0.4, -0.05, 0.05, 0.5, 0.05, wood, 0.9);                                                       // the bucket
      const ex = 0.46, ez = 0.3, ey = 0.97, ry = 1.2;                                                            // the roof: two slopes and the gables
      quad([cx - ex, ey, cz + ez], [cx + ex, ey, cz + ez], [cx + ex, ry, cz], [cx - ex, ry, cz], roof, 1.0);
      quad([cx + ex, ey, cz - ez], [cx - ex, ey, cz - ez], [cx - ex, ry, cz], [cx + ex, ry, cz], roof, 0.8);
      quad([cx - ex, ey - 0.02, cz + ez], [cx - ex, ry - 0.02, cz], [cx + ex, ry - 0.02, cz], [cx + ex, ey - 0.02, cz + ez], wood, 0.45);   // (its underside)
      quad([cx + ex, ey - 0.02, cz - ez], [cx + ex, ry - 0.02, cz], [cx - ex, ry - 0.02, cz], [cx - ex, ey - 0.02, cz - ez], wood, 0.45);
      for (const s of [-1, 1]) quad([cx + s * px, ey, cz - ez * 0.8], [cx + s * px, ey, cz + ez * 0.8], [cx + s * px, ry - 0.01, cz], [cx + s * px, ry - 0.01, cz], wood, 0.75); }
    return n; };
  // standing on the well's square, the well folds away (the shader's uHideAt)
  const bf0 = CM.beforeFrame; CM.beforeFrame = (game, r, dt, now) => { if (bf0) bf0(game, r, dt, now); const fl = game && game.floor;
    if (!fl || fl.number !== 0 || !CM.TOWN_AT || !CM.TOWN_AT.well) { r.hideAt = null; return; } const [x, y] = CM.TOWN_AT.well; r.hideAt = [x + 0.5, y + 0.5, CM.WELL_HIDE]; };
}
