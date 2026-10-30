"use strict";
// Props: the small things on a floor that are only for the eye - grass tufts, stones, bones, rubble - never in the way,
// never in a save, never in a floor's fingerprint. CM.PROPS says what each one is and how it is drawn; CM.SCATTER says
// where they lie; CM.scatter(fl, seed, density) works out, square by square, what lies there, from a hash of the seed,
// the floor and the square, so a floor wears the same props every visit. The renderer puts the flat and crossed ones
// into the floor's mesh with the walls and stands the rest up as billboards near the party (40-render.js, 80-main.js).
//   how: "flat" lies on the ground; "cross" is two crossed pictures (plants: they read from any side); "stand" is a
//   billboard that faces the camera. size: [least, most] across, in squares; h: the height against the width.
CM.PROPS = {
  tuft: { how: "cross", size: [0.3, 0.5], h: 0.7 },
  flowers: { how: "cross", size: [0.25, 0.4], h: 0.75 },
  pebbles: { how: "flat", size: [0.35, 0.6] },
  rock: { how: "stand", size: [0.2, 0.4], h: 0.75 },
  bones: { how: "flat", size: [0.4, 0.6] },
  skull: { how: "stand", size: [0.15, 0.2], h: 0.9 },
};
// where they lie: `surface` (the town and the land) or `bands` (the dungeon's, by CM.themeIndex: 0 the Catacombs ... 9
// the Root); `grounds` the ground the square wears; `near` "wall" (a square with a wall beside it: the prop lies
// against it) or "corner" (two walls meeting); `per` the chance a square has one at full detail; `most` how many
CM.SCATTER = [
  { prop: "tuft", where: { surface: true, grounds: ["grass"] }, per: 0.55, most: 3 },
  { prop: "flowers", where: { surface: true, grounds: ["grass"] }, per: 0.08, most: 1 },
  { prop: "pebbles", where: { surface: true, grounds: ["dirt"] }, per: 0.1, most: 1 },
  { prop: "rock", where: { surface: true, grounds: ["grass"] }, per: 0.04, most: 1 },
  { prop: "pebbles", where: { bands: "all", near: "wall" }, per: 0.14, most: 1 },
  { prop: "rock", where: { bands: [2, 6, 9], near: "wall" }, per: 0.08, most: 1 },
  { prop: "bones", where: { bands: [0, 3, 8], near: "wall" }, per: 0.07, most: 1 },
  { prop: "skull", where: { bands: [0, 8], near: "corner" }, per: 0.35, most: 1 },
];
CM.DETAIL = { low: 0, medium: 0.6, high: 1 };
CM.DETAIL_ORDER = ["low", "medium", "high"];
CM.isSurface = (fl) => Boolean(fl && (fl.number === 0 || fl.number === -1));
// what lies on each square: [{ id, how, layer, x, y, dx, dz, w, h, turn }]
CM.scatter = function (fl, seed, density = CM.DETAIL.medium) {
  const out = [];
  if (!fl || !density) return out;
  const grid = fl.grid, size = grid.length, surface = CM.isSurface(fl), band = surface ? -1 : CM.themeIndex(fl.number >= 1 ? fl.number : 1);
  const open = (x, y) => x >= 0 && y >= 0 && x < size && y < size && grid[y][x] === 0;
  const wet = new Set((fl.decor || []).filter((d) => d.kind === "water").map((d) => `${d.x},${d.y}`));
  const rules = CM.SCATTER.filter((r) => (surface ? r.where.surface : r.where.bands && (r.where.bands === "all" || r.where.bands.includes(band))));
  if (!rules.length) return out;
  for (let y = 0; y < size; y++) for (let x = 0; x < size; x++) {
    if (grid[y][x] !== 0) continue;
    const k = `${x},${y}`, t = fl.things[k];
    if ((t && t.type !== "monsters") || fl.features[k] || wet.has(k)) continue;   // (never on a thing, a feature or the water)
    const walls = CM.DIRS.map(([dx, dy]) => !open(x + dx, y + dy));               // north, east, south, west
    const ground = surface ? CM.groundAt(fl, x, y) || "grass" : null;
    const rnd = new CM.Random(CM.hashSeed(`${seed}:props:${fl.number}:${k}`));
    for (const r of rules) {
      const w = r.where;
      if (w.grounds && !w.grounds.includes(ground)) continue;
      let toward = null;
      if (w.near === "wall") { const sides = [0, 1, 2, 3].filter((d) => walls[d]); if (!sides.length) continue; toward = [sides[rnd.int(0, sides.length - 1)]]; }
      if (w.near === "corner") { const c = [[0, 1], [1, 2], [2, 3], [3, 0]].filter(([a, b]) => walls[a] && walls[b]); if (!c.length) continue; toward = c[rnd.int(0, c.length - 1)]; }
      for (let i = 0; i < (r.most || 1); i++) {
        if (!rnd.chance(r.per * density)) continue;
        const P = CM.PROPS[r.prop], s = P.size[0] + rnd.next() * (P.size[1] - P.size[0]);
        let dx = (rnd.next() - 0.5) * 0.6, dz = (rnd.next() - 0.5) * 0.6;
        if (toward) { dx = 0; dz = 0; for (const d of toward) { dx += CM.DIRS[d][0] * (0.5 - s / 2 - 0.04); dz += CM.DIRS[d][1] * (0.5 - s / 2 - 0.04); } dx += (rnd.next() - 0.5) * (toward.length === 1 ? 0.4 : 0.05); }
        out.push({ id: r.prop, how: P.how, layer: `prop:${r.prop}`, x, y, dx, dz, w: s, h: s * (P.h || 1), turn: rnd.next() * Math.PI });
      }
    }
  }
  return out;
};
