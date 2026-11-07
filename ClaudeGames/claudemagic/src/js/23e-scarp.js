"use strict";
// The Scarp (UPGRADE_PLAN_79.md): in the south-east of the Wood, against the hill's cliffs, the land lifts - a high heath
// as high as the cliffs' tops, walled all round by the same grey rock, and reached by one stair cut into its west face
// from the South Meadow. On the heath: a tarn, the spring that fills it, tors of weathered stone, heather and wind; and
// from the tarn a stream that wanders across the heath, under a plank bridge, and goes over the west edge in a fall
// into a pool among the trees, and from the pool runs on west through the forest to the river. The heights are the
// floor's levels (CM.floorAt, 69zzi-levels.js), drawn under the sky as they are below (26-surface.js), and made with
// the land, never saved; laid after everything the seed placed, in a corner of old forest every seed leaves alone.
//   CM.SCARP; CM.layScarp(parts) -> the levels; CM.isScarp(x, y)
CM.SCARP = { x0: 44, y0: 56, x1: 57, y1: 80, h: 2.2, stair: { y: 68, x0: 44, x1: 50 }, foot: [43, 68], tarn: [52, 59, 54, 60], spring: [53, 58],
  stream: [[53, 61], [53, 65], [54, 65], [54, 71], [50, 71], [50, 74], [46, 74], [46, 76], [45, 76]], bridge: [48, 74], falls: [44, 76], pool: [42, 75, 43, 77],
  below: [[41, 77], [24, 77]], bank: [[43, 69], [43, 74]], lookout: [50, 79], trail: [[51, 68], [51, 62], [51, 68], [51, 72], [48, 72], [48, 78], [50, 78], [50, 79]],
  tors: [[46, 59], [47, 59], [46, 60], [47, 60], [56, 62], [55, 77], [56, 77], [56, 78]] };
CM.isScarp = (x, y) => x >= CM.SCARP.x0 && x <= CM.SCARP.x1 && y >= CM.SCARP.y0 && y <= CM.SCARP.y1;
CM.layScarp = function (P) {
  const { grid, kinds, ground, features, decor, things, size } = P, S = CM.SCARP, key = (x, y) => `${x},${y}`, levels = {};
  if (size <= S.y1) return levels;
  const open = (x, y, g) => { grid[y][x] = 0; delete kinds[key(x, y)]; ground[key(x, y)] = g; };
  const rock = (x, y, kind = "scarp") => { grid[y][x] = 1; kinds[key(x, y)] = kind; delete ground[key(x, y)]; delete things[key(x, y)]; };
  const water = (x, y, g = "dirt") => { open(x, y, g); decor.push({ kind: "water", x, y }); features[key(x, y)] = { type: "river" }; };
  const walk = (pts, fn) => { for (let i = 1; i < pts.length; i++) { let [x, y] = pts[i - 1]; const [bx, by] = pts[i]; fn(x, y); while (x !== bx || y !== by) { if (x !== bx) x += Math.sign(bx - x); else y += Math.sign(by - y); fn(x, y); } } };
  // the heath, and the rock round it (the hill's cliffs are its east side)
  for (let y = S.y0; y <= S.y1; y++) for (let x = S.x0; x <= S.x1; x++) {
    if (x === S.x0 || y === S.y0 || y === S.y1) { rock(x, y); continue; }
    open(x, y, (CM.hashSeed(`scarp:${x},${y}`) % 7) < 2 ? "rock" : "heath"); levels[key(x, y)] = [S.h, S.h + 1]; }
  for (const [x, y] of S.tors) rock(x, y, "tor");
  // the stair: cut into the west face, a step a square, rock on either hand
  for (let x = S.stair.x0; x <= S.stair.x1; x++) { const k = x - S.stair.x0 + 1, f = Math.round(S.h * k / (S.stair.x1 - S.stair.x0 + 2) * 1000) / 1000;
    open(x, S.stair.y, "rock"); levels[key(x, S.stair.y)] = [f, f + 1]; rock(x, S.stair.y - 1); rock(x, S.stair.y + 1); }
  open(...S.foot, "dirt");
  // the trodden way over the heath: from the stair's head north to the spring, south over the bridge to the Lookout
  walk(S.trail, (x, y) => { if (grid[y][x] === 0 && ground[key(x, y)] !== "rock") ground[key(x, y)] = "dirt"; });
  // the tarn, the stream across the heath, the bridge, the fall over the edge, the pool, and the stream on to the river
  for (let y = S.tarn[1]; y <= S.tarn[3]; y++) for (let x = S.tarn[0]; x <= S.tarn[2]; x++) water(x, y);
  walk(S.stream, (x, y) => { if (!(x === S.bridge[0] && y === S.bridge[1])) water(x, y); });
  open(...S.bridge, "planks");
  water(...S.falls); levels[key(...S.falls)] = [S.h, S.h + 1];
  for (let y = S.pool[1]; y <= S.pool[3]; y++) for (let x = S.pool[0]; x <= S.pool[2]; x++) { water(x, y); delete levels[key(x, y)]; }
  walk(S.below, (x, y) => water(x, y));
  walk(S.bank, (x, y) => open(x, y, y === S.bank[1][1] ? "grass" : "dirt"));
  for (const [x, y] of [[40, 74], [41, 74], [42, 74], [40, 75], [41, 75]]) open(x, y, "grass");   // (a little bank by the pool, to stand and look at the fall)
  { const [mx, my] = CM.SOUTH_WOOD.meadows[0].c; for (let x = mx; x <= S.foot[0]; x++) if (grid[my][x] !== 0) open(x, my, "dirt"); }   // (the way to the stair's foot, east from the meadow)
  for (const k of Object.keys(levels)) { const [x, y] = k.split(",").map(Number); if (grid[y][x] !== 0) delete levels[k]; }
  things[key(...S.spring)] = { type: "scarpspring" }; things[key(...S.lookout)] = { type: "lookout" };
  things[key(S.foot[0], S.foot[1] + 1)] = { type: "signpost", text: "THE SCARP: a stair cut in the rock, up onto the high heath. A stream comes off the top in a fall, south of here, a little way along the foot of the rock." };
  return levels;
};
