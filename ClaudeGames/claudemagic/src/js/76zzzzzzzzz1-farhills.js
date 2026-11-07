"use strict";
// Real distance (v51.1, UPGRADE_PLAN_46.md): beyond the treeline round the town and the land, two rings of hills more -
// a near range half again as tall as the trees, and a far one twice as far and taller still - each paler and bluer for
// the air between (the sky's own haze does the rest), so the world goes back in layers to the edge of seeing, and the
// keep, the spire and the Mage Tower (76zzzzg-farviews.js) stand against them.
{ const fv0 = CM.farViews; CM.farViews = (fl, size, index, night, quad) => { if (fv0) fv0(fl, size, index, night, quad); const L = index["far:hill"]; if (L === undefined) return;
    for (const [E, H, W, sh] of [[(CM.SKIRT || 24) + 22, 19, 16, 0.42], [(CM.SKIRT || 24) + 60, 34, 26, 0.34]]) for (let t = -E; t < size + E; t += W) { const t1 = Math.min(t + W, size + E), lo = -0.5, isle = CM.seaGirt ? CM.seaGirt(fl) : false, land = isle && fl.number === -1;   // (v129.0: from the island, only the hill's range, east; the rest is sea)
      if (!isle) { quad([t, lo, -E], [t1, lo, -E], [t1, H, -E], [t, H, -E], L, sh, 0); quad([t1, lo, size + E], [t, lo, size + E], [t, H, size + E], [t1, H, size + E], L, sh, 0); }
      if (!isle || (land && t >= -W && t < size * 0.8)) quad([size + E, lo, t], [size + E, lo, t1], [size + E, H, t1], [size + E, H, t], L, sh, 0); if (!isle) quad([-E, lo, t1], [-E, lo, t], [-E, H, t], [-E, H, t1], L, sh, 0); } };
}
