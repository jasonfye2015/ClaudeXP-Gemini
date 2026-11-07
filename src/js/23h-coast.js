"use strict";
// The coast (UPGRADE_PLAN_80.md, v131.0): a path round the island's outer edge - up the west coast from the Strand,
// along the north coast past the river's springhead (crossed on the north bridge just below it) and behind the
// Fortress, and down the island's north-east corner through the trees to the cliff path and the fields - so the
// whole land can be walked round, the sea always at one hand; the river given its source, a spring under a knot of
// rock at the north coast; a plank bridge over the river's mouth beside the ford; and more ways down to the shore.
// Laid after everything else, on the land's very edge and lines no seed ever placed anything on.
//   CM.COAST; CM.layCoast(parts)
CM.COAST = { west: 0, north: 0, last: 82, east: 56, eastTo: 14, spring: [21, 23], northBridge: [23, 2], detour: [[20, 0], [20, 2], [24, 2], [24, 0]],
  mouthBridge: 83, spurs: [[[3, 72], [0, 72]], [[1, 44], [0, 44]], [[1, 82], [1, 83]]] };
CM.isCoastLine = (x, y) => { const C = CM.COAST; return x === C.west || y === C.north || (x === C.east && y <= C.eastTo) || (x === C.east + 1 && y === C.eastTo) || (y <= 2 && x >= C.detour[0][0] && x <= C.detour[2][0])
  || C.spurs.some(([[ax, ay], [bx, by]]) => x >= Math.min(ax, bx) && x <= Math.max(ax, bx) && y >= Math.min(ay, by) && y <= Math.max(ay, by)); };   // (the coast's own squares: what picks among the land's open squares leaves these out, so nothing it placed moves)
CM.layCoast = function (P) {
  const { grid, kinds, ground, features, decor, things, size } = P, C = CM.COAST, key = (x, y) => `${x},${y}`;
  if (size <= CM.SHORE.sea) return;
  const dry = (x, y) => { delete features[key(x, y)]; for (let i = decor.length - 1; i >= 0; i--) if (decor[i].kind === "water" && decor[i].x === x && decor[i].y === y) decor.splice(i, 1); };
  const path = (x, y, g = "sand") => { if (grid[y][x] === 0 || things[key(x, y)]) return; grid[y][x] = 0; delete kinds[key(x, y)]; ground[key(x, y)] = g; };
  const walk = (pts, g) => { for (let i = 1; i < pts.length; i++) { let [x, y] = pts[i - 1]; const [bx, by] = pts[i]; path(x, y, g); while (x !== bx || y !== by) { if (x !== bx) x += Math.sign(bx - x); else y += Math.sign(by - y); path(x, y, g); } } };
  // the river's springhead: a knot of rock at the north coast, the water rising from under it
  for (let x = C.spring[0]; x <= C.spring[1]; x++) { dry(x, 0); grid[0][x] = 1; kinds[key(x, 0)] = x === CM.riverX(0) ? "denrock" : "denrocklow"; delete ground[key(x, 0)]; }
  // the coast path: west, north (round the springhead, over the north bridge), and down the north-east corner
  for (let y = 0; y <= C.last; y++) path(C.west, y);
  for (let x = 0; x <= CM.WOOD_EAST - 1; x++) if (x < C.spring[0] || x > C.spring[1]) path(x, C.north);
  walk(C.detour, "sand"); { const [bx, by] = C.northBridge; dry(bx, by); grid[by][bx] = 0; ground[key(bx, by)] = "planks"; }
  for (let y = 0; y <= C.eastTo; y++) path(C.east, y, "dirt"); path(C.east + 1, C.eastTo, "dirt");
  for (const s of C.spurs) walk(s, "sand");
  // a plank bridge over the river's mouth, beside the ford
  { const mx = CM.riverX(C.mouthBridge); dry(mx, C.mouthBridge); ground[key(mx, C.mouthBridge)] = "planks"; }
  things[key(C.west, C.last - 1)] = things[key(C.west, C.last - 1)] || { type: "signpost", text: "THE COAST PATH, north: up the island's west shore, along the north coast past the river's springhead, and round to the cliff path and the fields. South: the Strand." };
};
