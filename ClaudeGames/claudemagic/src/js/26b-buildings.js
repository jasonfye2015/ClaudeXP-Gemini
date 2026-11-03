"use strict";
// Buildings with depth (v53.0 on, UPGRADE_PLAN_48.md): the town's walls are no longer flat pictures where their windows
// are - each window painted on a wall (30-art.js facade: a house's at u .62-.84, v .30-.56; a door's beside it at
// .74-.90, .36-.56) is set into the wall: a stone sill standing proud below it, a timber lintel over it, and the
// reveals of its frame standing out at each side, so it reads as a hole with a window in it. 26-surface.js calls this for
// each wall face of a house, a door or a shop (CM.buildingDetail); the pictures are 76zzzzzzzzzz-buildings.js's.
//   CM.WINDOW_AT(kind, front) -> [u0, v0, u1, v1] (v from the top) or null
{ CM.WINDOW_AT = (kind, front) => (front && kind === "shop" ? null : front && kind === "door" ? [0.74, 0.36, 0.9, 0.56] : [0.62, 0.3, 0.84, 0.56]);
  CM.buildingDetail = (o) => { if (o.front && (o.kind === "door" || o.kind === "shop") && CM.doorDetail) CM.doorDetail(o); const W = CM.WINDOW_AT(o.kind, o.front); if (!W) return o.front && o.kind === "shop" ? 1 : 0; const { poly, index, a, b, dx, dy, h } = o;
    const stone = index["solid:sill"] !== undefined ? index["solid:sill"] : index["solid:townwall"], wood = index["solid:timber"] !== undefined ? index["solid:timber"] : stone; if (stone === undefined) return 0;   /* (solid: names - the town's own surface pictures; a shared one is not drawn on its walls) */
    const P = (u, y, dep) => [a[0] + (b[0] - a[0]) * u + dx * dep, y, a[1] + (b[1] - a[1]) * u + dy * dep], UV = [[0, 1], [1, 1], [1, 0], [0, 0]], sh = o.shade * (o.wash || 1);
    const box = (u0, u1, y0, y1, d0, d1, layer, k = 1) => {   // a block standing out of the wall: its face, its top, its underside and its two ends
      poly([P(u0, y0, d1), P(u1, y0, d1), P(u1, y1, d1), P(u0, y1, d1)], UV, layer, sh * 1.0 * k);
      poly([P(u0, y1, d0), P(u1, y1, d0), P(u1, y1, d1), P(u0, y1, d1)], UV, layer, sh * 1.12 * k);
      poly([P(u0, y0, d0), P(u1, y0, d0), P(u1, y0, d1), P(u0, y0, d1)], UV, layer, sh * 0.62 * k);
      poly([P(u0, y0, d0), P(u0, y0, d1), P(u0, y1, d1), P(u0, y1, d0)], UV, layer, sh * 0.8 * k);
      poly([P(u1, y0, d0), P(u1, y0, d1), P(u1, y1, d1), P(u1, y1, d0)], UV, layer, sh * 0.8 * k); };
    const [u0, v0, u1, v1] = W, yb = h * (1 - v1), yt = h * (1 - v0), fu = 0.02, fy = 0.02 * h;   // (the window's painted frame is about 2% wide)
    box(u0 - 0.045, u1 + 0.045, yb - 0.055, yb, 0, 0.085, stone, 1.05);                 // the sill
    box(u0 - 0.03, u1 + 0.03, yt, yt + 0.045, 0, 0.045, wood, 0.9);                       // the lintel
    box(u0 - fu, u0 + 0.004, yb, yt, 0, 0.035, wood, 0.85); box(u1 - 0.004, u1 + fu, yb, yt, 0, 0.035, wood, 0.85);   // the reveals
    // (v53.1) shutters: a pair beside it, folded back against the wall - in the house's own colour, one of three - or, on about one window in six, closed over it
    const col = Math.round((o.wash || 1) * 100) % 3, sl = index[`solid:shutter${col}`] !== undefined ? index[`solid:shutter${col}`] : wood, hsh = CM.hashSeed(`shut:${o.fl ? o.fl.number : 0}:${o.x},${o.y},${o.d}`) >>> 0, sw = Math.min(0.11, (u1 - u0) * 0.5);
    if (hsh % 6 === 0) { box(u0, (u0 + u1) / 2, yb, yt, 0, 0.03, sl, 0.95); box((u0 + u1) / 2, u1, yb, yt, 0, 0.03, sl, 0.95); }
    else { if (u0 - fu - sw > 0.01) box(u0 - fu - sw, u0 - fu, yb, yt, 0, 0.018, sl, 0.95); if (u1 + fu + sw < 0.99) box(u1 + fu, u1 + fu + sw, yb, yt, 0, 0.018, sl, 0.95); }
    void fy; return 1; };
  // (v53.3) a door in its frame: a stone step before it, the jambs and the lintel of its frame standing out (the facade's door at u .30-.70, from v .30 down)
  CM.doorDetail = (o) => { const { poly, index, a, b, dx, dy, h } = o; const stone = index["solid:sill"] !== undefined ? index["solid:sill"] : index["solid:townwall"], wood = index["solid:timber"] !== undefined ? index["solid:timber"] : stone; if (stone === undefined) return 0;
    const P = (u, y, dep) => [a[0] + (b[0] - a[0]) * u + dx * dep, y, a[1] + (b[1] - a[1]) * u + dy * dep], UV = [[0, 1], [1, 1], [1, 0], [0, 0]], sh = o.shade * (o.wash || 1);
    const box = (u0, u1, y0, y1, d0, d1, layer, k = 1) => { poly([P(u0, y0, d1), P(u1, y0, d1), P(u1, y1, d1), P(u0, y1, d1)], UV, layer, sh * k); poly([P(u0, y1, d0), P(u1, y1, d0), P(u1, y1, d1), P(u0, y1, d1)], UV, layer, sh * 1.12 * k);
      poly([P(u0, y0, d0), P(u1, y0, d0), P(u1, y0, d1), P(u0, y0, d1)], UV, layer, sh * 0.62 * k); poly([P(u0, y0, d0), P(u0, y0, d1), P(u0, y1, d1), P(u0, y1, d0)], UV, layer, sh * 0.8 * k); poly([P(u1, y0, d0), P(u1, y0, d1), P(u1, y1, d1), P(u1, y1, d0)], UV, layer, sh * 0.8 * k); };
    const top = h * 0.7;
    box(0.25, 0.75, 0, 0.07, 0, 0.24, stone, 1.0);                              // the step
    box(0.285, 0.335, 0.07, top, 0, 0.06, wood, 0.85); box(0.665, 0.715, 0.07, top, 0, 0.06, wood, 0.85);   // the jambs
    box(0.26, 0.74, top, top + 0.06, 0, 0.075, wood, 0.9);                       // the lintel
    return 1; };
}
