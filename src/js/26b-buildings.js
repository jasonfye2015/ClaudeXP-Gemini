"use strict";
// Buildings with depth (v53.0 on, UPGRADE_PLAN_48.md): the town's walls are no longer flat pictures where their windows
// are - each window painted on a wall (30-art.js facade: a house's at u .62-.84, v .30-.56; a door's beside it at
// .74-.90, .36-.56) is set into the wall: a stone sill standing proud below it, a timber lintel over it, and the
// reveals of its frame standing out at each side, so it reads as a hole with a window in it. 26-surface.js calls this for
// each wall face of a house, a door or a shop (CM.buildingDetail); the pictures are 76zzzzzzzzzz-buildings.js's.
//   CM.WINDOW_AT(kind, front) -> [u0, v0, u1, v1] (v from the top) or null
{ CM.WINDOW_AT = (kind, front) => (front && kind === "shop" ? null : front && kind === "door" ? [0.74, 0.36, 0.9, 0.56] : [0.62, 0.3, 0.84, 0.56]);
  CM.buildingDetail = (o) => { if (CM.timberDetail) CM.timberDetail(o); if (o.front && (o.kind === "door" || o.kind === "shop") && CM.doorDetail) CM.doorDetail(o); const W = CM.WINDOW_AT(o.kind, o.front); if (!W) return o.front && o.kind === "shop" ? 1 : 0; const { poly, index, a, b, dx, dy, h } = o;
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
    if (index["solid:stain"] !== undefined) poly([P(u0 + 0.01, yb - 0.32, 0.004), P(u1 - 0.01, yb - 0.32, 0.004), P(u1 - 0.01, yb - 0.055, 0.004), P(u0 + 0.01, yb - 0.055, 0.004)], UV, index["solid:stain"], sh * 0.9);   // (v57.4) the rain's stain run down from it
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
  // (v53.5) the half-timbering standing out: the posts at the wall's ends, the house's middle post and the beam under the eaves, as strips over their paint
  CM.timberDetail = (o) => { const { poly, index, a, b, dx, dy, h } = o, wood = index["solid:timber"]; if (wood === undefined) return 0;
    const P = (u, y, dep) => [a[0] + (b[0] - a[0]) * u + dx * dep, y, a[1] + (b[1] - a[1]) * u + dy * dep], UV = [[0, 1], [1, 1], [1, 0], [0, 0]], sh = o.shade * (o.wash || 1), d1 = 0.022;
    const strip = (u0, u1, y0, y1) => { poly([P(u0, y0, d1), P(u1, y0, d1), P(u1, y1, d1), P(u0, y1, d1)], UV, wood, sh * 0.95); poly([P(u0, y0, 0), P(u0, y0, d1), P(u0, y1, d1), P(u0, y1, 0)], UV, wood, sh * 0.7); poly([P(u1, y0, 0), P(u1, y0, d1), P(u1, y1, d1), P(u1, y1, 0)], UV, wood, sh * 0.7);
      poly([P(u0, y1, 0), P(u1, y1, 0), P(u1, y1, d1), P(u0, y1, d1)], UV, wood, sh * 1.1); poly([P(u0, y0, 0), P(u1, y0, 0), P(u1, y0, d1), P(u0, y0, d1)], UV, wood, sh * 0.6); };
    const foot = 0.16, top = h * (1 - 10 / 256);
    strip(0, 12 / 256, foot, h); strip(1 - 12 / 256, 1, foot, h); strip(12 / 256, 1 - 12 / 256, top, h);
    if (!o.front || o.kind === "house") strip(0.5 - 6 / 256, 0.5 + 6 / 256, foot, top);
    return 1; };
  // (v53.6) the rooflines: the eaves' underside and the rafters' ends under it; a dormer with its window on each side of a long roof; on about half the
  // buildings a gutter along the eaves and a downpipe at a corner
  CM.roofDetail = (o) => { const { poly, index, B, P, U0, U1, mid, half, h, top, eaveY, roofL } = o, wood = index["solid:timber"], metal = index["solid:sill"]; if (wood === undefined) return 0;
    const UV = [[0, 1], [1, 1], [1, 0], [0, 0]], ov = o.o, hsh = CM.hashSeed(`roof:${o.fl ? o.fl.number : 0}:${B.x0},${B.y0}`) >>> 0, slopeY = (v) => h + B.rise * (1 - Math.abs(v - mid) / half);
    const box = (u0, u1, v0, v1, y0, y1, L, k) => { poly([P(u0, v0, y0), P(u1, v0, y0), P(u1, v0, y1), P(u0, v0, y1)], UV, L, k); poly([P(u0, v1, y0), P(u1, v1, y0), P(u1, v1, y1), P(u0, v1, y1)], UV, L, k * 0.85);
      poly([P(u0, v0, y0), P(u0, v1, y0), P(u0, v1, y1), P(u0, v0, y1)], UV, L, k * 0.8); poly([P(u1, v0, y0), P(u1, v1, y0), P(u1, v1, y1), P(u1, v0, y1)], UV, L, k * 0.8);
      poly([P(u0, v0, y1), P(u1, v0, y1), P(u1, v1, y1), P(u0, v1, y1)], UV, L, k * 1.1); poly([P(u0, v0, y0), P(u1, v0, y0), P(u1, v1, y0), P(u0, v1, y0)], UV, L, k * 0.55); };
    for (const side of [-1, 1]) { const vw = mid + side * half, ve = mid + side * (half + ov);
      poly([P(U0, vw, h), P(U1, vw, h), P(U1, ve, eaveY - 0.01), P(U0, ve, eaveY - 0.01)], UV, wood, 0.42);                       // the underside of the eaves, in shadow
      for (let u = U0 + 0.25; u < U1; u += 0.5) box(u - 0.025, u + 0.025, vw, ve, eaveY - 0.07, eaveY - 0.01, wood, 0.6);         // the rafters' ends
      if (U1 - U0 >= 3) { const um = (U0 + U1) / 2, dw = 0.42, vd = mid + side * half * 0.62, yb = slopeY(vd), yt = Math.min(top - 0.02, yb + 0.38), dl = index["solid:house"] !== undefined ? index["solid:house"] : wood;   // a dormer
        poly([P(um - dw, vd, yb - 0.1), P(um + dw, vd, yb - 0.1), P(um + dw, vd, yt), P(um - dw, vd, yt)], [[0.5, 1], [0.95, 1], [0.95, 0.15], [0.5, 0.15]], dl, 1.0);   // (its face: the window side of the house picture)
        for (const uu of [um - dw, um + dw]) poly([P(uu, vd, yb - 0.1), P(uu, vd, yt), P(uu, mid, yt), P(uu, mid, yt)], UV, dl, 0.78);
        poly([P(um - dw - 0.05, vd - side * 0.06, yt), P(um + dw + 0.05, vd - side * 0.06, yt), P(um + dw + 0.05, mid, yt + 0.12), P(um - dw - 0.05, mid, yt + 0.12)], UV, roofL, 0.9);
        poly([P(um - dw - 0.05, vd - side * 0.06, yt), P(um - dw - 0.05, vd, yt - 0.02), P(um + dw + 0.05, vd, yt - 0.02), P(um + dw + 0.05, vd - side * 0.06, yt)], UV, roofL, 0.6); }
      if (metal !== undefined && hsh % 2 === 0) { box(U0 - o.g * 0.5, U1 + o.g * 0.5, ve - side * 0.02, ve + side * 0.07, eaveY - 0.13, eaveY - 0.05, metal, 0.7);   // the gutter
        const ud = side > 0 ? U1 - 0.06 : U0 + 0.06; box(ud - 0.035, ud + 0.035, ve + side * 0.0, ve + side * 0.07, 0, eaveY - 0.08, metal, 0.65); } }   // the downpipe
    return 1; };
  // (v57.4) ivy: on about one wall face in five, a climbing patch from the ground, its own width and height
  CM.ivyDetail = (o) => { const L = o.index["solid:ivy"]; if (L === undefined) return 0; const { poly, a, b, dx, dy, h } = o, r = new CM.Random(CM.hashSeed(`ivy:${o.x},${o.y}:${o.d}`)); if (r.next() > 0.2) return 0;
    const P = (u, y, dep) => [a[0] + (b[0] - a[0]) * u + dx * dep, y, a[1] + (b[1] - a[1]) * u + dy * dep], u0 = r.next() * 0.55, u1 = Math.min(1, u0 + 0.25 + r.next() * 0.3), top = h * (0.45 + r.next() * 0.45);
    poly([P(u0, 0, 0.006), P(u1, 0, 0.006), P(u1, top, 0.006), P(u0, top, 0.006)], [[0, 1], [1, 1], [1, 0], [0, 0]], L, o.shade * 0.95); return 1; };
}
