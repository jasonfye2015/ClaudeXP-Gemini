"use strict";
// The town wall and keep (v57.0 on, UPGRADE_PLAN_52.md): the ring wall's top is battlemented now - along its outer edge
// (and its town side) a low parapet and on it two merlons a square, with the crenels between them to see out through, capped in the walk's
// stone, turning the corners where the wall does. 26-surface.js calls this for the town (CM.wallDetail).
//   CM.wallDetail(o) -> { merlons }   o: { quad, fl, index, size, solidKind(x, y) }
{ CM.WALL_DETAIL = true;
  CM.wallDetail = (o) => { const { quad, index, size, solidKind } = o, out = { merlons: 0 };
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
        for (const [u0, u1] of [[0.06, 0.36], [0.56, 0.86]]) { block(x, y, d, u0, u1, 0, 0.16, H + 0.07, H + 0.3); out.merlons++; } } }   // two merlons, the crenels between
    return out; };
}
