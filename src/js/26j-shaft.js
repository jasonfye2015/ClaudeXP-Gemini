"use strict";
// The shaft head (v57.3, UPGRADE_PLAN_52.md): the shaft in the Keep-yard is built up now - a low kerb of dressed stone
// round the hole, and over it a winch: two timber A-frames on opposite sides, the windlass drum on its axle between them
// with a crank, and a hemp rope wound on it running down into the dark. Nothing stands in the middle at the eye's height,
// so stepping onto the square to climb down is as it was. 26-surface.js builds it into the town's mesh.
//   CM.shaftHead(o) -> 1 when built   o: { quad, fl, index }
{ CM.SHAFT_HEAD = true;
  CM.shaftHead = (o) => { const { quad, fl, index } = o, S = CM.TOWN_AT && CM.TOWN_AT.shaft; if (!S || !fl || fl.number !== 0) return 0;
    const stone = index["solid:sill"], wood = index["solid:timber"] !== undefined ? index["solid:timber"] : stone, rope = index["model:sack"] !== undefined ? index["model:sack"] : wood; if (stone === undefined) return 0;
    const [x, y] = S, cx = x + 0.5, cz = y + 0.5;
    const box = (x0, y0, z0, x1, y1, z1, L, k = 1) => { const V = (a, b, c) => [cx + a, b, cz + c];
      quad(V(x0, y0, z1), V(x1, y0, z1), V(x1, y1, z1), V(x0, y1, z1), L, 0.95 * k); quad(V(x1, y0, z0), V(x0, y0, z0), V(x0, y1, z0), V(x1, y1, z0), L, 0.78 * k);
      quad(V(x1, y0, z1), V(x1, y0, z0), V(x1, y1, z0), V(x1, y1, z1), L, 0.88 * k); quad(V(x0, y0, z0), V(x0, y0, z1), V(x0, y1, z1), V(x0, y1, z0), L, 0.72 * k);
      quad(V(x0, y1, z1), V(x1, y1, z1), V(x1, y1, z0), V(x0, y1, z0), L, 1.08 * k); };
    const a = 0.47, b = 0.39, h = 0.2;                                                                                 // the kerb: four stones round the hole
    box(-a, 0, -a, a, h, -b, stone); box(-a, 0, b, a, h, a, stone); box(-a, 0, -b, -b, h, b, stone); box(b, 0, -b, a, h, b, stone);
    const lean = (x0, z0, x1, z1, y0, y1, t) => { const dx = x1 - x0, dz = z1 - z0, n = Math.hypot(dx, dz) || 1, px = -dz / n * t, pz = dx / n * t, V = (u, yy, s) => [cx + x0 + dx * u + px * s, yy, cz + z0 + dz * u + pz * s];
      quad(V(0, y0, 1), V(1, y1, 1), V(1, y1, -1), V(0, y0, -1), wood, 1.0); quad(V(0, y0, -1), V(1, y1, -1), V(1, y1, 1), V(0, y0, 1), wood, 0.75); };   // a timber leaning from one point to another (two faces)
    const top = 1.15, side = (sx) => { for (const sz of [-1, 1]) { lean(sx * 0.43, sz * 0.32, sx * 0.43, 0, h, top, 0.03); } box(sx * 0.43 - 0.035, top - 0.04, -0.05, sx * 0.43 + 0.035, top + 0.03, 0.05, wood, 0.9); };
    side(-1); side(1);                                                                                                 // the A-frames
    box(-0.47, top - 0.025, -0.025, 0.47, top + 0.025, 0.025, wood, 0.85);                                             // the axle
    const N = 10, r = 0.075, drum = (u, k) => { const a2 = (k / N) * Math.PI * 2; return [cx + u, top + Math.sin(a2) * r, cz + Math.cos(a2) * r]; };
    for (let k = 0; k < N; k++) quad(drum(-0.25, k), drum(0.25, k), drum(0.25, k + 1), drum(-0.25, k + 1), rope, 0.7 + 0.3 * Math.abs(Math.cos((k / N) * 6.28)));   // the drum, wound with rope
    box(0.47, top - 0.015, -0.015, 0.56, top + 0.015, 0.015, wood, 0.8); box(0.54, top - 0.15, -0.015, 0.57, top + 0.015, 0.015, wood, 0.8);   // the crank
    const rz = r + 0.005; quad([cx - 0.012, top, cz + rz], [cx + 0.012, top, cz + rz], [cx + 0.012, 0.0, cz + rz], [cx - 0.012, 0.0, cz + rz], rope, 0.8);   // the rope, down into the dark
    quad([cx, top, cz + rz - 0.012], [cx, top, cz + rz + 0.012], [cx, 0.0, cz + rz + 0.012], [cx, 0.0, cz + rz - 0.012], rope, 0.7);
    return 1; };
}
