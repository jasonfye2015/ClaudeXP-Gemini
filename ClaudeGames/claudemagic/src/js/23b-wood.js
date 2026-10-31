"use strict";
// The Deep Wood: a second surface floor (-1) west of the town through a gate at the end of the main lane, made by the
// seed from the forest's own rules - glades joined by paths through the trees (a tree is a wall the renderer draws as
// a trunk and a crown), a river with one ford, a hermit's hut, a ruined shrine, a charcoal burner's clearing and three
// cave mouths (one open a day, by the day of the run; each a short floor of the first bands' kinds, and a troll under
// the third). By day the Wood is foraging (mushrooms, berries, herbs, deadwood, a beehive) and deer and boar that run;
// by night wolves, a bear and bandits come to the party, and under a full moon a wolf that is more. The Wood's beasts
// give no renown and little gold: hides and meat, and the night's danger. The dungeon's floors do not change by a cell.
CM.WOOD_THEME = { name: "The Deep Wood", floors: [-1, -1], stone: [58, 84, 46], mortar: [34, 52, 28], floor: [78, 104, 52], ceiling: [140, 170, 205],
  moss: [120, 160, 70], fog: [0.01, 0.014, 0.008], torch: [1.0, 0.95, 0.85], reach: 7.0, bones: 0, tree: true, sky: true };
CM.WOOD_SIZE = 61;
CM.WOOD_GATE = [59, 30];                                                 // the land's end of the West Gate: the town is east, up the hill; the land lies west
CM.LAND_ROAD = [[44, 30, 59, 30], [44, 30, 44, 33], [24, 33, 44, 33]];   // the road from the gate, bending south at the farm, to the ford
CM.FIELDS = [40, 20, 57, 42];                                            // the fields between the hill and the river
CM.riverX = (y) => 22 + Math.round(Math.sin(y / 5) * 2);                 // where the river runs, north to south
CM.WOOD_NODES = [["a patch of mushrooms", "fungus"], ["a bramble of berries", "nest"], ["herbs by the path", "nest"], ["a stand of deadwood", "ember"], ["a beehive in a hollow oak", "nest"]];
CM.CAVE_OF = (number) => Math.round((-number - 1.5) * 10);              // -1.5 -> 0, -1.6 -> 1, -1.7 -> 2
CM.caveNumber = (n) => -(1.5 + n / 10);
CM.WOOD_LINES = {
  hut: ["The hermit of the Wood opens the door a hand's width. \"Hides I'll take, by daylight. Trouble I won't.\" The door shuts.", "The hut is shuttered for the night, and something inside is awake and not opening."],
  shrine: "A shrine with its roof in the grass. Cut into the one standing wall, older than the town's oldest stone: THE ORDER KEPT THE DEAD IN THE TREES BEFORE IT KEPT THEM IN THE HILL. THE TREES DID NOT ASK TO BE FED EITHER.",
  burner: ["The charcoal burner sits by a smoking mound. \"Deadwood in, charcoal out. Come back when the forge wants it.\"", "The charcoal burner's mound glows in the dark; the man himself is a shape asleep against a tree."],
  caveShut: "The cave's mouth is choked with fallen rock today. The Wood opens one a day, the hermit says, and never says which.",
};
CM.woodCache = {};
// the land: from the gate in the cliffs at the hill's foot, the road west through the fields and past the farm to the
// river's ford (a plank bridge a little north of it, found by walking), and over the river the forest - the first glade
// just past the ford, safe at any hour, seven more joined by paths under the trees, and deep among them the hermit's
// hut, the ruined shrine, the charcoal burner's clearing and the three cave mouths; things to gather along the paths
CM.makeWood = function (seed) {
  if (CM.woodCache[seed]) return JSON.parse(CM.woodCache[seed]);
  const size = CM.WOOD_SIZE, rnd = new CM.Random(CM.hashSeed(`${seed}:wood`)), grid = [], kinds = {}, ground = {}, features = {}, decor = [], things = {};
  for (let y = 0; y < size; y++) grid.push(new Array(size).fill(1));
  const key = (x, y) => `${x},${y}`;
  const open = (x, y, g) => { if (x >= 0 && y >= 0 && x < size && y < size) { grid[y][x] = 0; delete kinds[key(x, y)]; if (g) ground[key(x, y)] = g; } };
  const solid = (x, y, kind) => { grid[y][x] = 1; if (kind === "tree") delete kinds[key(x, y)]; else kinds[key(x, y)] = kind; delete ground[key(x, y)]; };
  const rect = ([x0, y0, x1, y1], fn) => { for (let y = y0; y <= y1; y++) for (let x = x0; x <= x1; x++) fn(x, y); };
  const carve = (cx, cy, rx, ry, g) => { for (let y = cy - ry; y <= cy + ry; y++) for (let x = cx - rx; x <= cx + rx; x++) if (((x - cx) / (rx + 0.5)) ** 2 + ((y - cy) / (ry + 0.5)) ** 2 <= 1) open(x, y, g); };
  const path = (a, b, g = "dirt") => { let [x, y] = a; while (x !== b[0] || y !== b[1]) { open(x, y, g); if (x !== b[0] && (y === b[1] || rnd.chance(0.6))) x += Math.sign(b[0] - x); else y += Math.sign(b[1] - y); } open(x, y, g); };
  // the hill's foot: cliffs along the east edge, the gate in them, the road running out of it
  for (let y = 0; y < size; y++) for (let x = size - 3; x < size; x++) solid(x, y, "cliff");
  // the fields: grass between the hill and the river, hedged pastures, the farm's tilled rows inside a fence by the road's bend, copses in the corners
  rect(CM.FIELDS, (x, y) => open(x, y, "grass"));
  for (const r of [[41, 22, 48, 22], [41, 22, 41, 27], [50, 36, 56, 36], [50, 36, 50, 41]]) rect(r, (x, y) => solid(x, y, "hedge"));
  rect([45, 34, 49, 37], (x, y) => open(x, y, "tilled"));
  for (const r of [[44, 34, 44, 38], [50, 34, 50, 38], [44, 38, 50, 38]]) rect(r, (x, y) => solid(x, y, "fence"));
  for (const [cx, cy] of [[43, 25], [55, 24], [54, 40], [42, 40]]) for (let i = 0; i < 5; i++) { const x = cx + rnd.int(-2, 2), y = cy + rnd.int(-2, 2); if (grid[y][x] === 0 && ground[key(x, y)] === "grass") solid(x, y, "tree"); }
  for (const r of CM.LAND_ROAD) rect(r, (x, y) => open(x, y, "dirt"));
  open(CM.WOOD_GATE[0], CM.WOOD_GATE[1], "dirt"); open(size - 1, CM.WOOD_GATE[1], "dirt");
  things[key(...CM.WOOD_GATE)] = { type: "woodgate" };
  // the river, with the ford where the road meets it and a plank bridge to the north
  const fordY = 33, bridgeY = 26;
  for (let y = 0; y < size; y++) {
    const rx = CM.riverX(y);
    open(rx, y, "dirt");
    if (y === bridgeY) { ground[key(rx, y)] = "planks"; continue; }
    decor.push({ kind: "water", x: rx, y });
    if (y !== fordY) features[key(rx, y)] = { type: "river" };
  }
  // over the river: the forest, the first glade just past the ford, seven more joined by paths
  const first = [CM.riverX(fordY) - 5, fordY], glades = [first];
  let guard = 0; while (glades.length < 8 && guard++ < 600) { const c = [rnd.int(4, 17), rnd.int(4, 56)]; if (glades.every((g) => Math.abs(g[0] - c[0]) + Math.abs(g[1] - c[1]) >= 8)) glades.push(c); }
  glades.forEach((g, i) => carve(g[0], g[1], i === 0 ? 3 : rnd.int(2, 4), i === 0 ? 2 : rnd.int(2, 3), "grass"));
  for (let i = 1; i < glades.length; i++) path(glades[i - 1], glades[i]);
  path([CM.riverX(fordY) - 1, fordY], first);                           // from the ford into the first glade
  path([CM.riverX(bridgeY) - 1, bridgeY], first);                       // from the bridge too
  path([CM.riverX(bridgeY) + 1, bridgeY], [44, 30]);                    // and the bridge's track east through the trees to the road's bend
  // deep in the forest, far from the ford: the hut, the shrine, the burner, three cave mouths; things to gather along the ways
  const cells = []; for (let y = 1; y < size - 1; y++) for (let x = 1; x < size - 1; x++) if (grid[y][x] === 0 && !features[key(x, y)] && !things[key(x, y)] && (ground[key(x, y)] === "grass" || ground[key(x, y)] === "dirt")) cells.push([x, y]);
  const deep = (c) => c[0] < CM.riverX(c[1]) - 1 && Math.abs(c[0] - first[0]) + Math.abs(c[1] - first[1]) >= 9;
  const take = (ok) => { for (let g = 0; g < 400; g++) { const c = cells[rnd.int(0, cells.length - 1)], k = key(c[0], c[1]); if (!things[k] && (!ok || ok(c))) return k; } return null; };
  for (let n = 0; n < 3; n++) { const k = take(deep); if (k) things[k] = { type: "cave", n }; }
  for (const type of ["hut", "shrine", "burner"]) { const k = take(deep); if (k) things[k] = { type }; }
  for (let i = 0; i < 8; i++) { const k = take((c) => c[0] < CM.riverX(c[1])); if (k) things[k] = { type: "node", band: -1, forage: i % CM.WOOD_NODES.length }; }
  for (const [at, text] of [[[57, 29], "THE ROAD, west: the fields, the farm's gate, the river's ford and the Deep Wood over it. Behind: the West Gate, and Caer Duin on its hill."],
    [[43, 31], "The road bends south here to the ford. The farm's gate is a step back along it. A track north of the road, through the trees, comes to the plank bridge."],
    [[first[0], first[1] - 2], "THE FIRST GLADE: safe at any hour. The paths beyond are the Wood's own; the hermit's hut, the ruined shrine, the charcoal burner and the cave mouths lie along them, somewhere."]]) {
    if (grid[at[1]] && grid[at[1]][at[0]] === 0 && !things[key(...at)] && !features[key(...at)]) things[key(...at)] = { type: "signpost", text };
  }
  { const [px, py0, , py1] = CM.POSTERN_PATH; for (let y = py0; y <= py1; y++) open(px, y, "dirt"); things[key(...CM.POSTERN_LAND)] = { type: "postern" }; }   // the cliff path from the postern (61c-tower.js; laid last, so nothing the seed placed moves)
  const seen = [];                                                       // open country in daylight: the road, the fields and the river's near bank are on the map from the gate; the forest is not
  for (let y = 0; y < size; y++) for (let x = 0; x < size; x++) if (grid[y][x] === 0 && x >= CM.riverX(y)) seen.push([x, y]);
  const fl = { number: -1, grid, pos: CM.WOOD_GATE.slice(), facing: 3, things, features, dark: [], seen, decor, special: "wood", glades, ford: [CM.riverX(fordY), fordY], bridge: [CM.riverX(bridgeY), bridgeY],
    solidDefault: "tree", kinds, ground,
    rooms: [...glades.map((g, i) => ({ x0: g[0] - 3, y0: g[1] - 3, x1: g[0] + 3, y1: g[1] + 3, name: i === 0 ? "The First Glade" : "A Glade" })), { x0: CM.FIELDS[0], y0: CM.FIELDS[1], x1: CM.FIELDS[2], y1: CM.FIELDS[3], name: "The Fields" }] };
  if (CM.layMageTower) CM.layMageTower(fl);
  if (CM.layCabin) CM.layCabin(fl);                                      // Leshy's cabin (61f-cabin.js; laid last)                              // the Mage Tower's clearing (61d-magetower.js; laid last, so nothing the seed placed moves)
  CM.markCanopy(fl);
  CM.woodCache[seed] = JSON.stringify(fl);
  return JSON.parse(CM.woodCache[seed]);
};
CM.makeLand = CM.makeWood;
// where the party stands on the land, by name - and the places the beasts keep off
CM.woodPlace = function (fl, x, y) {
  if (!fl || fl.number !== -1) return null;
  const t = fl.things[`${x},${y}`];
  if (t && t.type === "woodgate") return "the West Gate";
  if (t && t.type === "farm") return "the farm";
  if (fl.ford && x === fl.ford[0] && y === fl.ford[1]) return "the ford";
  if (fl.bridge && x === fl.bridge[0] && y === fl.bridge[1]) return "the bridge";
  if (CM.LAND_ROAD.some(([x0, y0, x1, y1]) => x >= x0 && x <= x1 && y >= y0 && y <= y1)) return "the road";
  if (CM.CABIN && x === CM.CABIN.path[0] && y >= CM.CABIN.path[1] && y <= CM.CABIN.path[3]) return "the cabin path";
  if (CM.POSTERN_PATH && x === CM.POSTERN_PATH[0] && y >= CM.POSTERN_PATH[1] && y <= CM.POSTERN_PATH[3]) return "the cliff path";
  const room = (fl.rooms || []).find((r) => x >= r.x0 && x <= r.x1 && y >= r.y0 && y <= r.y1);
  if (room) return room.name;
  return x < CM.riverX(y) ? "the Deep Wood" : "the river's bank";
};
// where the party stands on the surface, by name (the town's or the land's)
CM.placeOf = (fl, x, y) => (fl && fl.number === 0 ? CM.townPlace(fl, x, y) : fl && fl.number === -1 ? CM.woodPlace(fl, x, y) : null);
// Where to?: the doors and places the party knows on this surface floor, with the walk's length (null: no known way)
CM.wayPlaces = function (game) {
  const fl = game.floor;
  if (!fl || fl.number > 0 || fl.number % 1 !== 0 || (CM.isUndercroft && CM.isUndercroft(fl.number))) return [];
  const out = [], seen = new Set((fl.seen || []).map(([x, y]) => `${x},${y}`));
  const add = (name, x, y, always) => { if (!always && !seen.has(`${x},${y}`)) return; if (x === fl.pos[0] && y === fl.pos[1]) return; const path = game.pathTo(x, y); out.push({ name, x, y, steps: path ? path.length : null }); };
  if (fl.number === 0) {
    for (const id of ["home", "tavern", "merchant", "smith", "garden", "library", "temple", "guildhall", "chronicler"]) add(CM.TOWN_PLOTS[id].name, ...CM.TOWN_AT[id], true);
    add("The well", ...CM.TOWN_AT.well, true); add("The shaft", ...CM.TOWN_AT.shaft, true); add("The West Gate", ...CM.TOWN_AT.woodgate, true);
    add("The portal yard", ...CM.PORTAL_YARD.tower, true); add("The gate tower's stair", ...Object.keys(CM.TOWER_STAIRS)[0].split(",").map(Number), true); if (CM.posternOpen(game)) add("The postern", ...CM.TOWN_POSTERN, true);
  } else {
    add("The West Gate", ...CM.WOOD_GATE, true); if (CM.posternOpen(game)) add("The postern", ...CM.POSTERN_LAND, true); add("The Mage Tower", ...CM.MAGE_DOOR, true); add("Leshy's cabin", ...CM.CABIN.front, true);
    const farm = Object.keys(fl.things).find((k) => fl.things[k].type === "farm");
    if (farm) add("The farm", ...farm.split(",").map(Number), true);
    add("The ford", ...fl.ford, true); if (fl.bridge) add("The bridge", ...fl.bridge, true); add("The First Glade", ...fl.glades[0], true);
    for (const [k, t] of Object.entries(fl.things)) if (["hut", "shrine", "burner", "cave"].includes(t.type)) add(t.type === "hut" ? "The hermit's hut" : t.type === "shrine" ? "The ruined shrine" : t.type === "burner" ? "The charcoal burner" : `A cave mouth${t.n === CM.dayOf(game) % 3 ? " (open today)" : ""}`, ...k.split(",").map(Number), false);
  }
  return out;
};
CM.woodSafe = (fl, x, y) => ["the West Gate", "the farm", "the ford", "the bridge", "the road", "the cliff path", "the Mage Tower", "Leshy's cabin", "the cabin path", "The Fields", "The First Glade"].includes(CM.woodPlace(fl, x, y));
CM.woodCaveAt = (seed, n) => { const fl = CM.makeWood(seed); return Object.keys(fl.things).find((k) => fl.things[k].type === "cave" && fl.things[k].n === n) || CM.WOOD_GATE.join(","); };
// a cave: a short floor of the first bands' kinds, carved as any floor of its own key, with the way out where the stair was;
// the third cave has a troll under the hill at its far end
CM.makeCave = function (number, seed, gen) {
  const n = CM.CAVE_OF(number), fl = CM.makeFloor(3 + n * 3, `${seed}:cave:${n}`, 2);
  fl.number = number; fl.special = "cave"; fl.cave = n; delete fl.wing;
  for (const [k, t] of Object.entries(fl.things)) {
    if (t.type === "stairs_up") fl.things[k] = { type: "caveexit" };
    else if (t.type === "ladder" && n === 2) { const troll = CM.makeMonster(CM.monsterKind("Troll"), 6, new CM.Random(CM.hashSeed(`${seed}:cavelord`))); troll.name = "The Troll under the Hill"; troll.elite = "hulking"; troll.max = Math.round(troll.max * 1.6); troll.hp = troll.max; troll.atk += 3; troll.xp *= 3; troll.gold = 60; fl.things[k] = { type: "monsters", group: [troll], still: true, caveLord: true }; }
    else if (!["chest", "monsters", "key", "node"].includes(t.type)) delete fl.things[k];
  }
  for (const [k, f] of Object.entries(fl.features)) if (["carving", "teleporter", "spinner", "trapdoor", "pit"].includes(f.type)) delete fl.features[k];
  if (!Object.values(fl.things).some((t) => t.type === "caveexit")) fl.things[CM.keyOf(fl.pos[0], fl.pos[1])] = { type: "caveexit" };
  const ores = [["copper", "copper"], ["iron", "iron"], ["gold", "iron"]][n], cells = [];   // the cave's own veins: copper in the first, iron in the second, gold at the deepest
  for (let y = 1; y < fl.grid.length - 1; y++) for (let x = 1; x < fl.grid.length - 1; x++) { const k = CM.keyOf(x, y); if (fl.grid[y][x] === 0 && !fl.things[k] && !fl.features[k] && CM.DIRS.some(([dx, dy]) => fl.grid[y + dy][x + dx] === 1)) cells.push(k); }
  ores.forEach((ore, i) => { if (cells.length) { const k = cells[CM.hashSeed(`${seed}:cavevein:${n}:${i}`) % cells.length]; fl.things[k] = { type: "vein", ore, left: CM.VEIN_SWINGS }; } });
  if (n === 2 && CM.undercroftStairOf) { const k = CM.undercroftStairOf(fl, seed); if (k) fl.things[k] = { type: "ucstair", hidden: true }; }   // (the old stair down: 64c-undercroft.js)
  return fl;
};
// the Wood's own kinds: never among a floor's bands
CM.WOOD_KINDS = [
  { name: "Deer", colour: "#A07A50", body: "beast", head: "snout", eyes: "#302010", extras: ["tail"], speed: 16, shape: [0.7, 0.4, 0.4], wood: true, flees: true },
  { name: "Boar", colour: "#5A4A3A", body: "beast", head: "tusks", eyes: "#FF5040", extras: ["tail"], speed: 11, ability: "charge", shape: [1.1, 1.0, 0.8], wood: true, flees: true },
  { name: "Wolf", colour: "#707478", body: "beast", head: "snout", eyes: "#FFE040", extras: ["tail"], speed: 14, ability: "savage", shape: [0.9, 1.1, 0.6], wood: true },
  { name: "Bear", colour: "#4A3A2A", body: "wide", head: "round", eyes: "#FFE040", extras: ["claws"], speed: 8, ability: "stun", shape: [1.8, 1.3, 0.9], wood: true },
];
for (const k of CM.WOOD_KINDS) CM.MONSTERS.push(k);
Object.assign(CM.MEALS, { Deer: { name: "venison", what: "+1 defence", df: 1 }, Boar: { name: "roast boar", what: "+1 attack", atk: 1 }, Wolf: { name: "wolf, stewed long", what: "+1 Luck", luck: 1 }, Bear: { name: "bear's flank", what: "mends 1 a round in fights", regen: 1 } });
CM.HIDES = { Deer: 30, Boar: 35, Wolf: 40, Bear: 90, Troll: 160 };
CM.hide = (kind) => ({ name: `${kind} hide`, kind: "hide", hide: kind, power: 0, value: CM.HIDES[kind] || 30 });
for (const kind of Object.keys(CM.HIDES)) CM.BASES[`${kind} hide`] = { id: `${kind} hide`, kind: "hide", slot: null, tier: 0, group: "ingredient" };
Object.assign(CM.INGREDIENTS, {
  mushroom: { band: -1, name: "Wood Mushroom" }, berries: { band: -1, name: "Bramble Berries" }, woodherb: { band: -1, name: "Wild Herbs" }, deadwood: { band: -1, name: "Deadwood" }, honey: { band: -1, name: "Wild Honey", rare: true },
});
for (const id of ["mushroom", "berries", "woodherb", "deadwood", "honey"]) CM.BASES[CM.INGREDIENTS[id].name] = { id: CM.INGREDIENTS[id].name, kind: "ingredient", slot: null, tier: 0, group: "ingredient" };
// the Wood's bands, by day and by night (and the moon): what walks there now
CM.woodBands = (night, fullMoon) => (night ? [["Wolf", "Wolf", "Wolf"], ["Bear"], ["Sellsword", "Sellsword"], fullMoon ? ["Wolf", "Wolf", "Wolf", "Wolf"] : ["Wolf", "Wolf"]] : [["Deer", "Deer"], ["Boar"], ["Deer"], ["Boar", "Boar"]]);
