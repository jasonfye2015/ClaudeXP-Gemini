"use strict";
// Washing on the line (v61.0, UPGRADE_PLAN_56.md): behind about half the townsfolk's houses a line runs from the
// wall's middle out to a post in the yard, with three or four cloths pegged along it, each its own size and shade.
// None in winter. 26-surface.js builds it into the town's mesh (within 20 squares); the lines are 69zzk-townlife.js's.
//   CM.washingModel(o) -> lines built   o: { quad, fl, index, season }
{ CM.WASHING_MODEL = true;
  CM.washingModel = (o) => { const { quad, fl, index } = o, L = CM.washingLines ? CM.washingLines(fl, o.season || "summer") : []; if (!L.length) return 0;
    const wood = index["solid:timber"] !== undefined ? index["solid:timber"] : index["solid:sill"], rope = index["model:sack"] !== undefined ? index["model:sack"] : wood, cloth = index["model:cloth"]; if (wood === undefined || cloth === undefined) return 0;
    const box = (x0, y0, z0, x1, y1, z1, Lr, k = 1) => { quad([x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1], Lr, 0.95 * k); quad([x1, y0, z0], [x0, y0, z0], [x0, y1, z0], [x1, y1, z0], Lr, 0.78 * k);
      quad([x1, y0, z1], [x1, y0, z0], [x1, y1, z0], [x1, y1, z1], Lr, 0.88 * k); quad([x0, y0, z0], [x0, y0, z1], [x0, y1, z1], [x0, y1, z0], Lr, 0.72 * k); quad([x0, y1, z1], [x1, y1, z1], [x1, y1, z0], [x0, y1, z0], Lr, 1.05 * k); };
    for (const w of L) { const dx = w.x1 - w.x0, dz = w.z1 - w.z0, n = Math.hypot(dx, dz) || 1, px = -dz / n, pz = dx / n;   // (px, pz: across the line)
      box(w.x1 - 0.03, 0, w.z1 - 0.03, w.x1 + 0.03, w.y + 0.08, w.z1 + 0.03, wood, 0.9);                                                      // the post
      const R = (s, yy, t) => [w.x0 + dx * t + px * s, yy, w.z0 + dz * t + pz * s];
      quad(R(0.008, w.y, 0), R(0.008, w.y, 1), R(0.008, w.y + 0.014, 1), R(0.008, w.y + 0.014, 0), rope, 0.7); quad(R(-0.008, w.y, 1), R(-0.008, w.y, 0), R(-0.008, w.y + 0.014, 0), R(-0.008, w.y + 0.014, 1), rope, 0.7);   // the line, seen from both sides
      w.cloths.forEach((c, ci) => { const ta = c.t - c.w / 2 / n, tb = c.t + c.w / 2 / n, top = w.y - 0.005, bot = w.y - c.h, Lc = (ci + w.home) % 2 ? rope : cloth;   // (linen and the dyed cloth by turns)
        quad(R(0.004, bot, ta), R(0.004, bot, tb), R(0.004, top, tb), R(0.004, top, ta), Lc, c.k); quad(R(-0.004, bot, tb), R(-0.004, bot, ta), R(-0.004, top, ta), R(-0.004, top, tb), Lc, c.k * 0.85); }); }
    return L.length; };
}
