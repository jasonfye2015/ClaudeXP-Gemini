"use strict";
// The south of the Deep Wood (UPGRADE_PLAN_78.md): the Wood runs twenty rows further south than it did - old forest,
// the river going on through it - and in it two meadows where the deer graze: the South Meadow east of the river,
// reached by a track south from Claude's clearing, and the Long Meadow west of it, over a shallow ford, with a deer
// track north through the trees to the wolf den. Laid after everything the seed placed in the old land, by dice of its
// own, so nothing there moves by a cell; the east beyond the cliffs is the hill (23b-wood.js, CM.WOOD_EAST).
//   CM.SOUTH_WOOD; CM.laySouthWood(parts, seed)
CM.SOUTH_WOOD = { top: 61, meadows: [{ name: "The South Meadow", c: [36, 68], r: [6, 3] }, { name: "The Long Meadow", c: [10, 72], r: [7, 3] }], track: [33, 50], denTrack: [2, 44] };
CM.laySouthWood = function (P, seed) {
  const { grid, kinds, ground, features, size } = P, S = CM.SOUTH_WOOD, key = (x, y) => `${x},${y}`, rnd = new CM.Random(CM.hashSeed(`${seed}:southwood`));
  if (size <= S.top) return;
  const open = (x, y, g) => { if (x < 1 || y < 1 || x >= CM.WOOD_EAST || y >= size - 1) return; if (features[key(x, y)] && features[key(x, y)].type === "river") return; grid[y][x] = 0; delete kinds[key(x, y)]; if (g) ground[key(x, y)] = g; };
  const carve = ([cx, cy], [rx, ry], g) => { for (let y = cy - ry - 1; y <= cy + ry + 1; y++) for (let x = cx - rx - 1; x <= cx + rx + 1; x++) { const w = ((x - cx) / (rx + 0.5)) ** 2 + ((y - cy) / (ry + 0.5)) ** 2 + (rnd.next() - 0.5) * 0.3; if (w <= 1) open(x, y, g); } };
  const walk = (a, b, g = "dirt") => { let [x, y] = a; let guard = 0; while ((x !== b[0] || y !== b[1]) && guard++ < 400) { open(x, y, g); if (x !== b[0] && (y === b[1] || rnd.chance(0.45))) x += Math.sign(b[0] - x); else y += Math.sign(b[1] - y); } open(x, y, g); };
  // the meadows, a few trees standing in them
  for (const M of S.meadows) { carve(M.c, M.r, "grass"); for (let i = 0; i < 3; i++) { const x = M.c[0] + rnd.int(-M.r[0] + 1, M.r[0] - 1), y = M.c[1] + rnd.int(-M.r[1] + 1, M.r[1] - 1); if (grid[y] && grid[y][x] === 0 && (Math.abs(x - M.c[0]) > 1 || Math.abs(y - M.c[1]) > 1)) { grid[y][x] = 1; delete ground[key(x, y)]; } } }
  // the tracks: south from Claude's clearing; west over a shallow ford to the Long Meadow; north to the den
  const [m1, m2] = S.meadows; walk(S.track, [m1.c[0] - 2, m1.c[1] - m1.r[1]]);
  const fy = m2.c[1] - 1, fx = CM.riverX(fy); delete features[key(fx, fy)]; ground[key(fx, fy)] = "dirt";   // (the second ford: the water shallow enough here)
  walk([m1.c[0] - m1.r[0], m1.c[1]], [fx + 1, fy]); walk([fx - 1, fy], [m2.c[0] + m2.r[0], m2.c[1]]);
  { const [dx, dy] = S.denTrack; for (let y = dy; y <= m2.c[1]; y++) open(dx, y, "dirt"); walk([dx, m2.c[1]], [m2.c[0] - m2.r[0], m2.c[1]]); }
  P.rooms = S.meadows.map((M) => ({ x0: M.c[0] - M.r[0] - 1, y0: M.c[1] - M.r[1] - 1, x1: M.c[0] + M.r[0] + 1, y1: M.c[1] + M.r[1] + 1, name: M.name }));
};
// the meadows by name, on the map
{ const mw0 = CM.makeWood; CM.makeWood = function (seed) { const fl = mw0.call(this, seed); if (fl && !fl.rooms.some((r) => r.name === "The South Meadow") && fl.grid.length > CM.SOUTH_WOOD.top) fl.rooms = fl.rooms.concat(CM.SOUTH_WOOD.meadows.map((M) => ({ x0: M.c[0] - M.r[0] - 1, y0: M.c[1] - M.r[1] - 1, x1: M.c[0] + M.r[0] + 1, y1: M.c[1] + M.r[1] + 1, name: M.name }))); return fl; }; }
