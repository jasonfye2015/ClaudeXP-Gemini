"use strict";
// The lighthouse (UPGRADE_PLAN_80.md, v132.0): off the east end of the dock, a shoulder of rock in the sea, flat-topped
// at the dock's height, and on it a tall tower banded red and white, a gallery round its top and the lamp room over
// that. Its door faces the dock; the stair inside goes up to the gallery.
//   CM.LIGHTHOUSE; CM.layLighthouse(parts) -> levels for the rock
CM.LIGHTHOUSE = { at: [58, 97], rock: [57, 95, 59, 99], door: [57, 97], h: 6.2, r0: 0.47, r1: 0.36, lamp: 6.7 };
CM.isLighthouseRock = (x, y) => { const [x0, y0, x1, y1] = CM.LIGHTHOUSE.rock; return x >= x0 && x <= x1 && y >= y0 && y <= y1; };
CM.layLighthouse = function (P) {
  const { grid, kinds, ground, things, size } = P, L = CM.LIGHTHOUSE, key = (x, y) => `${x},${y}`, levels = {};
  if (size <= L.rock[3] + 1 || !CM.HARBOUR) return levels;
  const [x0, y0, x1, y1] = L.rock;
  for (let y = y0; y <= y1; y++) for (let x = x0; x <= x1; x++) { grid[y][x] = 0; delete kinds[key(x, y)]; ground[key(x, y)] = "rock"; levels[key(x, y)] = [CM.HARBOUR.deck, CM.HARBOUR.deck + 1]; }
  const [tx, ty] = L.at; grid[ty][tx] = 1; kinds[key(tx, ty)] = "lighthouse"; delete ground[key(tx, ty)]; delete levels[key(tx, ty)];
  things[key(...L.door)] = { type: "lighthousedoor" };
  return levels;
};
