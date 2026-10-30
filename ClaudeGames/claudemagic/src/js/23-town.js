"use strict";
// The town above: floor 0, hand-laid (no generator, so nothing moves between runs or versions) - Caer Duin on its
// hill, inside a ring wall, 45 cells a side. The west gate opens on the land; Lantern Street runs from it, forks round
// a block and comes to the Square (cobbles, the well, the market's pitch); Shaft Lane goes east from the Square to the
// Keep-yard, a walled yard of flagstones where the shaft's mouth is; Temple Row runs north from the Square to the
// Temple's porch, Smiths' Lane south. The nine plots are blocks of house with a door cell cut into the street side
// (a thing of type "building" with an id: walk in and Space opens it; what stands there is the village's business,
// CM.VILLAGE, read live), eight townsfolk's houses fill the rest, hedges and fences mark the yards, and outside the
// wall the hill falls away into trees, with cliffs at the north and south. Daylight: nothing wanders it, no torch
// burns on it, no one is hungry on it. Everything on the floor is a thing, so the town is the same for a seed
// whatever has been built and a save of it never drifts.
CM.TOWN_THEME = { name: "Caer Duin, above", floors: [0, 0], stone: [168, 150, 122], mortar: [110, 96, 78], floor: [138, 124, 100], ceiling: [150, 172, 200],
  moss: [110, 140, 70], fog: [0.004, 0.004, 0.006], torch: [1.0, 0.96, 0.9], reach: 9.0, bones: 0, town: true, sky: true };
CM.TOWN_PLOTS = {
  home: { name: "Your house", village: null, what: "The party's own door. A hearth, a stash and a trophy wall, as the house is raised." },
  tavern: { name: "The Hanged Lantern", village: null, what: "The tavern: recruits, the fence, rumours and the board." },
  merchant: { name: "The Merchant's House", village: "merchant", what: "The merchant at home: the full stock, orders and insurance." },
  smith: { name: "The Smith's forge", village: null, what: "The forge: everything the camps' smith does, and the work only a forge can." },
  garden: { name: "The Alchemist's Garden", village: null, what: "Beds for ingredients between runs, and the brewing bench." },
  library: { name: "The Library", village: "library", what: "The codex, the compendium and the bestiary at a desk; tomes to borrow." },
  temple: { name: "The Temple", village: "shrine", what: "The shrine of the fallen: candles, the Patriarch's history, the priest's services." },
  guildhall: { name: "The Guildhall", village: "guildhall", what: "The trainers, the second calling, the week's contracts." },
  chronicler: { name: "The Chronicler's House", village: null, what: "The films, the statistics, the ledger and the Hall of Fame, under a roof." },
};
CM.TOWN_SIZE = 45;
// the blocks: each plot's house [x0, y0, x1, y1] and the door cell cut into its street side; the shops wear a board over the door
CM.TOWN_BLOCKS = {
  home: { rect: [3, 21, 5, 23], door: [5, 22] },                        // the first house inside the gate, its door on Lantern Street's west end
  tavern: { rect: [16, 13, 19, 16], door: [18, 16], shop: true },
  merchant: { rect: [21, 13, 24, 16], door: [22, 16], shop: true },
  smith: { rect: [16, 24, 19, 27], door: [18, 24], shop: true },
  guildhall: { rect: [21, 24, 24, 27], door: [22, 24] },
  garden: { rect: [12, 24, 14, 26], door: [13, 24], shop: true },
  library: { rect: [17, 9, 19, 12], door: [19, 10] },
  temple: { rect: [18, 4, 22, 7], door: [20, 7] },
  chronicler: { rect: [27, 22, 29, 24], door: [28, 22] },
};
CM.TOWN_HOUSES = [[11, 20, 15, 21], [8, 24, 10, 26], [4, 24, 6, 26], [21, 9, 23, 12], [17, 29, 19, 31], [21, 29, 23, 31], [27, 17, 29, 19], [10, 16, 12, 18]];   // the townsfolk's
CM.TOWN_STREETS = {                                                       // [x0, y0, x1, y1] of dirt, by name (the compass says where the party stands)
  "Lantern Street": [[6, 22, 16, 22]],
  "Gate Lane": [[3, 19, 8, 19], [8, 20, 8, 21]],                          // from the West Gate, bending south to Lantern Street
  "Shaft Lane": [[24, 20, 31, 21]],
  "Temple Row": [[20, 8, 20, 16]],
  "Smiths' Lane": [[20, 24, 20, 32]],
};
CM.TOWN_SQUARE = [17, 17, 23, 23];
CM.TOWN_YARD = [32, 17, 38, 23];                                          // the Keep-yard, walled, open to Shaft Lane at its west side
CM.TOWN_HEDGES = [[3, 27, 6, 27], [12, 27, 14, 28], [24, 29, 25, 31], [15, 29, 16, 31], [3, 17, 7, 17]];
CM.TOWN_FENCES = [[8, 27, 10, 27], [30, 22, 30, 24], [9, 20, 10, 21], [13, 18, 15, 18]];
// where each door is (x, y), and the town's other places - the tests and the bot read these by name
CM.TOWN_AT = { home: [5, 22], shaft: [35, 20], well: [18, 18], market: [22, 18], woodgate: [2, 19],
  tavern: [18, 16], merchant: [22, 16], smith: [18, 24], garden: [13, 24], library: [19, 10], temple: [20, 7], guildhall: [22, 24], chronicler: [28, 22] };
CM.townInside = (x, y) => ((x - 22) / 20.5) ** 2 + ((y - 22) / 17.5) ** 2 <= 1;   // the hill's top, inside the ring wall
CM.townStreet = (x, y) => Object.keys(CM.TOWN_STREETS).find((name) => CM.TOWN_STREETS[name].some(([x0, y0, x1, y1]) => x >= x0 && x <= x1 && y >= y0 && y <= y1)) || null;
CM.makeTown = function (seed) {
  const size = CM.TOWN_SIZE, grid = [], kinds = {}, ground = {}, things = {}, features = {};
  for (let y = 0; y < size; y++) grid.push(new Array(size).fill(1));
  const key = (x, y) => `${x},${y}`;
  const open = (x, y, g) => { grid[y][x] = 0; delete kinds[key(x, y)]; if (g) ground[key(x, y)] = g; };
  const solid = (x, y, kind) => { grid[y][x] = 1; kinds[key(x, y)] = kind; delete ground[key(x, y)]; };
  const rect = ([x0, y0, x1, y1], fn) => { for (let y = y0; y <= y1; y++) for (let x = x0; x <= x1; x++) fn(x, y); };
  // the hill: grass inside the wall, trees down the slope outside, cliffs at the north and south edges
  for (let y = 0; y < size; y++) for (let x = 0; x < size; x++) {
    if (CM.townInside(x, y)) open(x, y, "grass");
    else solid(x, y, y <= 1 || y >= size - 2 ? "cliff" : "tree");
  }
  for (let y = 0; y < size; y++) for (let x = 0; x < size; x++) if (CM.townInside(x, y) && CM.DIRS.some(([dx, dy]) => !CM.townInside(x + dx, y + dy))) solid(x, y, "townwall");
  // the streets, the square, the yard
  for (const runs of Object.values(CM.TOWN_STREETS)) for (const r of runs) rect(r, (x, y) => open(x, y, "dirt"));
  rect(CM.TOWN_SQUARE, (x, y) => open(x, y, "cobbles"));
  rect(CM.TOWN_YARD, (x, y) => { const [x0, y0, x1, y1] = CM.TOWN_YARD; if (x === x0 || x === x1 || y === y0 || y === y1) solid(x, y, "townwall"); else open(x, y, "flags"); });
  open(32, 20, "dirt"); open(32, 21, "dirt");                              // the yard's opening, from Shaft Lane
  // the gate in the wall, and the road through it to the land
  open(2, 19, "dirt"); open(1, 19, "dirt"); open(0, 19, "dirt");
  // the blocks: the plots' houses with a door cell each, and the townsfolk's
  for (const [id, B] of Object.entries(CM.TOWN_BLOCKS)) {
    rect(B.rect, (x, y) => solid(x, y, "house"));
    const [dx, dy] = B.door;
    open(dx, dy, "flags");
    things[key(dx, dy)] = { type: "building", id };
    const street = CM.DIRS.find(([ox, oy]) => grid[dy + oy] && grid[dy + oy][dx + ox] === 0 && !things[key(dx + ox, dy + oy)]);   // the way out of the doorway
    if (street) { const bx = dx - street[0], by = dy - street[1]; if (kinds[key(bx, by)] === "house") kinds[key(bx, by)] = B.shop ? "shop" : "door"; }
  }
  for (const r of CM.TOWN_HOUSES) rect(r, (x, y) => solid(x, y, "house"));
  for (const r of CM.TOWN_HEDGES) rect(r, (x, y) => solid(x, y, "hedge"));
  for (const r of CM.TOWN_FENCES) rect(r, (x, y) => solid(x, y, "fence"));
  // the things: the shaft, the gate, the well; a peddler's cloth on market day; three townsfolk, by the seed
  things[key(...CM.TOWN_AT.shaft)] = { type: "ladder" };
  things[key(...CM.TOWN_AT.woodgate)] = { type: "woodgate" };
  things[key(...CM.TOWN_AT.well)] = { type: "well" };
  if (String(seed).startsWith("weekly-")) things[key(...CM.TOWN_AT.market)] = { type: "peddler", stock: null };
  const lane = [];                                                        // (on the side streets, not in the way between the door and the shaft)
  for (const name of ["Temple Row", "Smiths' Lane", "Gate Lane"]) for (const [x0, y0, x1, y1] of CM.TOWN_STREETS[name]) for (let y = y0; y <= y1; y++) for (let x = x0; x <= x1; x++) if (!things[key(x, y)] && !lane.some((c) => c[0] === x && c[1] === y)) lane.push([x, y]);
  for (let i = 0; i < 3; i++) { let k = CM.hashSeed(`${seed}:folk:${i}`) % lane.length, guard = 0; while (things[key(lane[k][0], lane[k][1])] && guard++ < lane.length) k = (k + 1) % lane.length; things[key(lane[k][0], lane[k][1])] = { type: "villager", who: i }; }
  const seen = []; for (let y = 0; y < size; y++) for (let x = 0; x < size; x++) seen.push([x, y]);   // (daylight: the whole town is on the map)
  const [sx0, sy0, sx1, sy1] = CM.TOWN_SQUARE, [yx0, yy0, yx1, yy1] = CM.TOWN_YARD;
  return { number: 0, grid, pos: CM.TOWN_AT.home.slice(), facing: 1, things, features, dark: [], seen, decor: [], special: "town", solidDefault: "tree", kinds, ground,
    rooms: [{ x0: sx0, y0: sy0, x1: sx1, y1: sy1, name: "The Square" }, { x0: yx0 + 1, y0: yy0 + 1, x1: yx1 - 1, y1: yy1 - 1, name: "The Keep-yard" }] };
};
// where the party stands in the town, by name: a street, the Square, the Keep-yard, a doorway, the gate, or a yard
CM.townPlace = function (fl, x, y) {
  if (!fl || fl.number !== 0) return null;
  const t = fl.things[`${x},${y}`];
  if (t && t.type === "building") return CM.TOWN_PLOTS[t.id] ? CM.TOWN_PLOTS[t.id].name : "a doorway";
  if (t && t.type === "woodgate") return "the West Gate";
  if (x <= 2 && y === 19) return "the road";
  const room = (fl.rooms || []).find((r) => x >= r.x0 && x <= r.x1 && y >= r.y0 && y <= r.y1);
  if (room) return room.name;
  if (x >= 32 && x <= 38 && y >= 17 && y <= 23) return "The Keep-yard";
  return CM.townStreet(x, y) || "the yards";
};
// a plot's level: the village's, for the plots the village already raises; none yet for the rest (the next phases raise them)
CM.plotLevel = (game, id) => { const P = CM.TOWN_PLOTS[id]; return P && P.village && game ? game.villageLevel(P.village) : 0; };
CM.isTown = (fl) => Boolean(fl && fl.number === 0);
CM.houseStage = (level, most) => (level <= 0 ? 0 : most <= 1 ? 4 : Math.max(1, Math.min(4, Math.ceil(level * 4 / most))));   // a building's drawn stage (1 a frame, 2 a roof, 3 a sign, 4 a lit window), by its level against its most
