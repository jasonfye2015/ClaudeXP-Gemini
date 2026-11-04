"use strict";
// The forest floor (v55.0, UPGRADE_PLAN_50.md): in the Wood the grass gives way under the trees - an open square with
// trees close on most sides is leaf litter (or needles among the pines), one at the trees' edge is moss, and the open
// grass begins only where the trees fall back; the grounds then blend into each other (v54.0). The picture only: the
// square's own ground (CM.groundAt, the footsteps and the props' rules) is as it was.
//   CM.blendGroundAt(fl, x, y) -> the ground drawn there
{ const cache = new WeakMap();
  CM.blendGroundAt = (fl, x, y) => { const g = CM.groundAt(fl, x, y); if (!fl || fl.number !== -1 || g !== "grass") return g;
    let M = cache.get(fl); if (!M) { M = new Map(); cache.set(fl, M); } const k = `${x},${y}`; if (M.has(k)) return M.get(k);
    let trees = 0, pines = 0; for (let dy = -2; dy <= 2; dy++) for (let dx = -2; dx <= 2; dx++) { if (!dx && !dy) continue; const nx = x + dx, ny = y + dy; if (!CM.inBounds(fl, nx, ny) || fl.grid[ny][nx] === 0 || CM.solidAt(fl, nx, ny) !== "tree") continue; const w = Math.abs(dx) + Math.abs(dy) <= 1 ? 2 : 1; trees += w; if (CM.treeVariant && CM.treeVariant(fl, nx, ny) === 1) pines += w; }
    const out = trees >= 11 ? (pines * 2 > trees ? "needles" : "litter") : trees >= 6 ? "moss" : g; M.set(k, out); return out; };
}
