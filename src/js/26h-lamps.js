"use strict";
// Lamp posts (v56.3, UPGRADE_PLAN_51.md): the town's lamps are built - a stone plinth, an iron post with a collar, an arm,
// and a lantern's cage with its little roof and finial - in the town's mesh (CM.lampModel). The glass in the cage and a
// soft pool of light on the ground beneath glow once the lamplighter has lit that lamp (80-main.js: the glass and the
// pool take the old picture's place; 76zzzzzzzzzz4-lamps.js paints them).
//   CM.lampModel(p, quad, index) -> true when built     CM.LAMP_GLASS_Y: the glass's foot, CM.LAMP_GLASS_H its height
{ CM.LAMP_MODEL = true; CM.LAMP_GLASS_Y = 1.03; CM.LAMP_GLASS_H = 0.15;
  CM.lampModel = (p, quad, index) => { const iron = index["model:iron"] !== undefined ? index["model:iron"] : index["solid:timber"], stone = index["solid:sill"] !== undefined ? index["solid:sill"] : iron; if (iron === undefined) return false;
    const cx = p.x + 0.5 + (p.dx || 0), cz = p.y + 0.5 + (p.dz || 0);
    const box = (x0, y0, z0, x1, y1, z1, L, k = 1) => { const V = (a, b, c) => [cx + a, b, cz + c];
      quad(V(x0, y0, z1), V(x1, y0, z1), V(x1, y1, z1), V(x0, y1, z1), L, 0.95 * k); quad(V(x1, y0, z0), V(x0, y0, z0), V(x0, y1, z0), V(x1, y1, z0), L, 0.78 * k);
      quad(V(x1, y0, z1), V(x1, y0, z0), V(x1, y1, z0), V(x1, y1, z1), L, 0.88 * k); quad(V(x0, y0, z0), V(x0, y0, z1), V(x0, y1, z1), V(x0, y1, z0), L, 0.72 * k);
      quad(V(x0, y1, z1), V(x1, y1, z1), V(x1, y1, z0), V(x0, y1, z0), L, 1.05 * k); };
    box(-0.075, 0, -0.075, 0.075, 0.09, 0.075, stone, 1); box(-0.055, 0.09, -0.055, 0.055, 0.13, 0.055, stone, 0.95);   // the plinth
    const N = 8, R = 0.026, ring = (r, i, y) => { const a = (i / N) * Math.PI * 2; return [cx + Math.cos(a) * r, y, cz + Math.sin(a) * r]; };
    for (let i = 0; i < N; i++) quad(ring(R, i, 0.13), ring(R, i + 1, 0.13), ring(R * 0.8, i + 1, 0.98), ring(R * 0.8, i, 0.98), iron, 0.7 + 0.3 * Math.abs(Math.cos((i / N) * 6.28 - 0.8)));   // the post, tapering
    box(-0.04, 0.5, -0.04, 0.04, 0.54, 0.04, iron, 0.9); box(-0.035, 0.96, -0.035, 0.035, 1.0, 0.035, iron, 0.9);   // its collars
    const y0 = CM.LAMP_GLASS_Y - 0.02, y1 = CM.LAMP_GLASS_Y + CM.LAMP_GLASS_H + 0.02, a = 0.06, t = 0.011;
    box(-a, y0 - 0.02, -a, a, y0, a, iron, 0.85);                                                                    // the lantern's floor
    for (const [sx, sz] of [[-1, -1], [1, -1], [1, 1], [-1, 1]]) box(sx * a - t, y0, sz * a - t, sx * a + t, y1, sz * a + t, iron, 0.8);   // its corner bars
    const top = [cx, y1 + 0.075, cz], C = [[-a - 0.015, -a - 0.015], [a + 0.015, -a - 0.015], [a + 0.015, a + 0.015], [-a - 0.015, a + 0.015]].map(([x, z]) => [cx + x, y1, cz + z]);
    for (let i = 0; i < 4; i++) quad(C[i], C[(i + 1) % 4], top, top, iron, 0.75 + 0.15 * i);                         // its roof
    box(-0.012, y1 + 0.07, -0.012, 0.012, y1 + 0.12, 0.012, iron, 0.9);                                             // the finial
    return true; };
}
