"use strict";
// The Strand (UPGRADE_PLAN_79.md, v129.0): the Wood runs on south past the Scarp to the coast - the trees thinning to
// a fringe on the dunes, then sand from the forest's edge to the water, under the hill's cliffs as well, the river
// crossing it shallow at its mouth, and the sea. Two tracks go down to the shore, one from each meadow, the eastern one
// over the falls' stream on stepping stones. Laid after everything else, in rows no seed ever placed anything in.
//   CM.SHORE; CM.layShore(parts); CM.LAND_ISLE (the sea lies round the land on every side but the hill's)
CM.SHORE = { fringe: 81, strand: [83, 85], sea: 86, mouth: 84, tracks: [[36, 72, 83], [10, 76, 83]], streamFord: [36, 77], shore: [36, 85] };
CM.LAND_ISLE = true;
CM.layShore = function (P) {
  const { grid, kinds, ground, features, decor, things, size } = P, H = CM.SHORE, key = (x, y) => `${x},${y}`;
  if (size <= H.sea) return;
  const river = (x, y) => Boolean(features[key(x, y)] && features[key(x, y)].type === "river");
  const open = (x, y, g) => { grid[y][x] = 0; delete kinds[key(x, y)]; ground[key(x, y)] = g; };
  const sea = (x, y) => { grid[y][x] = 1; kinds[key(x, y)] = "sea"; delete ground[key(x, y)]; delete features[key(x, y)]; delete things[key(x, y)]; };   // (nothing drawn on the square: the sea itself lies under the land and out past it - 77t-island.js)
  // the fringe: the trees thinning toward the shore, sand and rough grass between them
  for (let y = H.fringe; y < H.strand[0]; y++) for (let x = 1; x < CM.WOOD_EAST; x++) { if (river(x, y) || grid[y][x] === 0) continue; const h = CM.hashSeed(`shore:${x},${y}`) % 100; if (h < (y === H.fringe ? 22 : 58)) open(x, y, h % 3 ? "sand" : "grass"); }
  // the Strand: sand from the trees to the water, under the cliffs too; the river shallow at its mouth
  for (let y = H.strand[0]; y <= H.strand[1]; y++) for (let x = 1; x < size - 1; x++) if (!river(x, y)) open(x, y, "sand");
  { const mx = CM.riverX(H.mouth); delete features[key(mx, H.mouth)]; ground[key(mx, H.mouth)] = "sand"; }
  // the sea: every row past the sand, and the strand's two ends
  for (let y = H.sea; y < size; y++) for (let x = 0; x < size; x++) sea(x, y);
  for (let y = H.strand[0]; y <= H.strand[1]; y++) { sea(0, y); sea(size - 1, y); }
  for (let i = decor.length - 1; i >= 0; i--) if (decor[i].kind === "water" && (decor[i].y >= H.sea || grid[decor[i].y][decor[i].x] !== 0)) decor.splice(i, 1);   // (the river's water ends where the sea begins)
  // the ways down: south from each meadow; stepping stones over the falls' stream
  for (const [x, y0, y1] of H.tracks) for (let y = y0; y <= y1; y++) if (!river(x, y) && grid[y][x] !== 0) open(x, y, "dirt");
  { const [fx, fy] = H.streamFord; delete features[key(fx, fy)]; }
  things[key(H.tracks[0][0] + 1, H.strand[0])] = { type: "signpost", text: "THE STRAND. North: the meadow, the falls' stream on stepping stones, the Wood. West along the sand: the river's mouth, shallow enough to wade." };
};
