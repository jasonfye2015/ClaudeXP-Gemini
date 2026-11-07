"use strict";
// The harbour (UPGRADE_PLAN_80.md, v130.0): a long wooden pier from the Strand out over the sea, raised on piles, with
// a broad dock across its head where a boat can lie alongside; a portal on the dock to the town's Square; and the
// Harbour Road from the pier's foot - west along the sand, over the falls' stream on a plank bridge, north past the
// falls and through the South Meadow and the forest to the fields, where it meets the road to the West Gate. Laid
// after everything else, in the sea's rows and along a line of forest no seed ever placed anything on.
//   CM.HARBOUR; CM.layHarbour(parts) -> levels for the pier
CM.HARBOUR = { pier: [50, 51], foot: 84, deck: 0.45, head: [45, 96, 56, 98], portal: [46, 97], berth: [50, 99],
  road: { x: 40, from: 34, to: 82 }, bridge: [40, 77], post: [41, 83] };
CM.isPier = (x, y) => { const H = CM.HARBOUR, [x0, y0, x1, y1] = H.head; return (x >= H.pier[0] && x <= H.pier[1] && y >= H.foot && y < y0) || (x >= x0 && x <= x1 && y >= y0 && y <= y1); };
CM.layHarbour = function (P) {
  const { grid, kinds, ground, features, decor, things, size } = P, H = CM.HARBOUR, key = (x, y) => `${x},${y}`, levels = {};
  if (size <= H.head[3] + 1) return levels;
  const open = (x, y, g) => { grid[y][x] = 0; delete kinds[key(x, y)]; if (g) ground[key(x, y)] = g; };
  // the pier: a ramp up off the sand, then the deck on its piles, out to the dock across its head
  for (let y = H.foot; y <= H.head[3]; y++) for (let x = 0; x < size; x++) if (CM.isPier(x, y)) { open(x, y, "planks"); const f = y === H.foot ? H.deck / 3 : y === H.foot + 1 ? H.deck * 2 / 3 : H.deck; levels[key(x, y)] = [Math.round(f * 1000) / 1000, f + 1]; }
  // the Harbour Road: north from the sand to the fields' road, the falls' stream crossed on planks
  for (let y = H.road.from; y <= H.road.to; y++) { const x = H.road.x, k = key(x, y);
    if (x === H.bridge[0] && y === H.bridge[1]) { open(x, y, "planks"); delete features[k]; for (let i = decor.length - 1; i >= 0; i--) if (decor[i].kind === "water" && decor[i].x === x && decor[i].y === y) decor.splice(i, 1); continue; }
    if (features[k] && features[k].type === "river") continue;
    if (grid[y][x] !== 0) open(x, y, "dirt"); }   // (where it's open already - the fields, the meadow, the bank - it stays as it is)
  things[key(...H.portal)] = { type: "portal", to: "town" };
  things[key(...H.post)] = { type: "signpost", text: "THE HARBOUR ROAD, north: over the stream, past the falls, through the South Meadow and the forest to the fields and the road to the West Gate. East along the sand: the pier and the dock." };
  return levels;
};
