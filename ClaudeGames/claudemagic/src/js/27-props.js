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
  tuft_dry: { how: "cross", size: [0.3, 0.5], h: 0.65 },
  tuft_snow: { how: "cross", size: [0.25, 0.4], h: 0.5 },
  flowers: { how: "cross", size: [0.25, 0.4], h: 0.75 },
  tallgrass: { how: "cross", size: [0.45, 0.65], h: 1.0 },
  shrub: { how: "cross", size: [0.55, 0.8], h: 0.75 },
  fern: { how: "cross", size: [0.45, 0.65], h: 0.6 },
  mushroom: { how: "stand", size: [0.12, 0.2], h: 0.8 },
  leaves: { how: "flat", size: [0.5, 0.8] },
  log: { how: "stand", size: [0.6, 0.85], h: 0.3 },
  stump: { how: "stand", size: [0.3, 0.42], h: 0.6 },
  pebbles: { how: "flat", size: [0.35, 0.6] },
  rock: { how: "stand", size: [0.2, 0.4], h: 0.75 },
  boulder: { how: "stand", size: [0.5, 0.75], h: 0.7 },
  reeds: { how: "cross", size: [0.35, 0.55], h: 1.3 },
  steps: { how: "flat", size: [0.7, 0.85] },
  hay: { how: "stand", size: [0.45, 0.6], h: 0.75 },
  snow: { how: "flat", size: [0.45, 0.75] },
  barrel: { how: "stand", size: [0.28, 0.34], h: 1.25 },
  crate: { how: "stand", size: [0.3, 0.38], h: 0.95 },
  lamp: { how: "stand", size: [0.2, 0.22], h: 6.0, night: true },
  cart: { how: "stand", size: [0.7, 0.8], h: 0.62 },
  stall: { how: "stand", size: [0.75, 0.85], h: 1.0 },
  bones: { how: "flat", size: [0.4, 0.6] },
  skull: { how: "stand", size: [0.15, 0.2], h: 0.9 },
  // the dungeon's: `corner` spans an upper corner of the room, from wall to wall under the ceiling; `glow` shines unlit
  cobweb: { how: "corner", size: [0.35, 0.5], h: 0.8 },
  dust: { how: "flat", size: [0.5, 0.8] },
  coffinlid: { how: "flat", size: [0.55, 0.7] },
  candle: { how: "stand", size: [0.14, 0.2], h: 1.4, glow: 0.7 },
  puddle: { how: "flat", size: [0.45, 0.75] },
  slime: { how: "flat", size: [0.45, 0.7] },
  rotcrate: { how: "stand", size: [0.3, 0.38], h: 0.8 },
  rubble: { how: "stand", size: [0.35, 0.55], h: 0.5 },
  pick: { how: "flat", size: [0.4, 0.5] },
  rails: { how: "flat", size: [0.6, 0.8] },
  armour: { how: "flat", size: [0.4, 0.55] },
  glass: { how: "flat", size: [0.35, 0.55] },
  urn: { how: "stand", size: [0.22, 0.3], h: 1.3 },
  candelabra: { how: "stand", size: [0.25, 0.3], h: 2.0, glow: 0.7 },
  frost: { how: "flat", size: [0.55, 0.9] },
  weed: { how: "flat", size: [0.45, 0.7] },
  shells: { how: "flat", size: [0.3, 0.45] },
  oar: { how: "flat", size: [0.6, 0.75] },
  fungi: { how: "stand", size: [0.2, 0.32], h: 0.85, glow: 0.45 },
  shard: { how: "stand", size: [0.18, 0.3], h: 1.3, glow: 0.35 },
  slag: { how: "stand", size: [0.35, 0.5], h: 0.5, glow: 0.25 },
  chains: { how: "flat", size: [0.4, 0.6] },
  cogs: { how: "flat", size: [0.3, 0.45] },
  bonepile: { how: "stand", size: [0.4, 0.55], h: 0.6 },
  roots: { how: "flat", size: [0.6, 0.9] },
  coins: { how: "flat", size: [0.3, 0.45] },
  books: { how: "flat", size: [0.35, 0.5] },
  scrolls: { how: "flat", size: [0.3, 0.45] },
  straw: { how: "flat", size: [0.6, 0.9] },
  // traces: what the party leaves (never scattered; CM.traceProps draws them from the floor's saved list)
  bottle_red: { how: "stand", size: [0.1, 0.13], h: 1.6 },
  bottle_blue: { how: "stand", size: [0.1, 0.13], h: 1.6 },
  bottle_green: { how: "stand", size: [0.1, 0.13], h: 1.6 },
  stain: { how: "flat", size: [0.45, 0.7] },
  ash: { how: "flat", size: [0.45, 0.7] },
  ooze: { how: "flat", size: [0.45, 0.7] },
  scorch: { how: "flat", size: [0.7, 0.95] },
  arrows: { how: "flat", size: [0.35, 0.5] },
  stub: { how: "flat", size: [0.18, 0.24] },
  chest_open: { how: "stand", size: [0.62, 0.7], h: 1 },              // a chest the party emptied: it stays open where it stood
  pin: { how: "flat", size: [0.12, 0.16] },
};
// where they lie: `surface` (the town and the land) or `bands` (the dungeon's, by CM.themeIndex: 0 the Catacombs ... 9
// the Root); `floors` [0] the town or [-1] the land; `seasons`; `grounds` the ground the square wears; `near` "wall"
// (against a wall), "corner" (two walls meeting), "tree" (a tree beside it), "water" (water beside it); `canopy` true
// under the leaves, false in the open; `area` "fields"; `water` only on the water itself (the ford); `market` only on a
// week's seed, in the Square; `per` the chance a square has one at full detail; `most` how many
const GREEN = ["spring", "summer"], ALL = ["spring", "summer", "autumn", "winter"];
CM.SCATTER = [
  { prop: "tuft", where: { surface: true, grounds: ["grass"], seasons: GREEN, canopy: false }, per: 0.55, most: 3 },
  { prop: "tuft_dry", where: { surface: true, grounds: ["grass"], seasons: ["autumn"], canopy: false }, per: 0.5, most: 3 },
  { prop: "tuft_snow", where: { surface: true, grounds: ["grass"], seasons: ["winter"], canopy: false }, per: 0.25, most: 2 },
  { prop: "snow", where: { surface: true, grounds: ["grass"], seasons: ["winter"] }, per: 0.4, most: 1 },
  { prop: "flowers", where: { surface: true, grounds: ["grass"], seasons: GREEN, canopy: false }, per: 0.08, most: 1 },
  { prop: "tallgrass", where: { floors: [-1], grounds: ["grass"], area: "fields", seasons: ["summer", "autumn"] }, per: 0.25, most: 2 },
  { prop: "hay", where: { floors: [-1], grounds: ["grass"], area: "fields", seasons: ["summer", "autumn"] }, per: 0.025, most: 1 },
  { prop: "shrub", where: { floors: [-1, 0], grounds: ["grass"], near: "tree", seasons: ALL }, per: 0.22, most: 1 },
  { prop: "fern", where: { floors: [-1], grounds: ["grass", "dirt"], canopy: true, seasons: ["spring", "summer", "autumn"] }, per: 0.3, most: 2 },
  { prop: "mushroom", where: { floors: [-1], canopy: true, seasons: ["summer", "autumn"] }, per: 0.12, most: 2 },
  { prop: "leaves", where: { floors: [-1], near: "tree", seasons: ["autumn"] }, per: 0.45, most: 1 },
  { prop: "leaves", where: { floors: [-1], canopy: true, seasons: ["spring", "summer"] }, per: 0.15, most: 1 },
  { prop: "log", where: { floors: [-1], grounds: ["grass"], near: "tree", area: "forest" }, per: 0.03, most: 1 },
  { prop: "stump", where: { floors: [-1], grounds: ["grass"], near: "tree" }, per: 0.04, most: 1 },
  { prop: "pebbles", where: { surface: true, grounds: ["dirt"] }, per: 0.1, most: 1 },
  { prop: "rock", where: { surface: true, grounds: ["grass"] }, per: 0.04, most: 1 },
  { prop: "boulder", where: { floors: [-1], grounds: ["grass", "dirt"], near: "water" }, per: 0.12, most: 1 },
  { prop: "reeds", where: { floors: [-1], near: "water", seasons: ["spring", "summer", "autumn"] }, per: 0.5, most: 2 },
  { prop: "steps", where: { floors: [-1], water: true }, per: 1, most: 1 },
  { prop: "barrel", where: { floors: [0], grounds: ["dirt", "cobbles"], near: "wall" }, per: 0.07, most: 1 },
  { prop: "crate", where: { floors: [0], grounds: ["dirt"], near: "wall" }, per: 0.05, most: 1 },
  { prop: "lamp", where: { floors: [0], grounds: ["dirt", "cobbles"], near: "wall" }, per: 0.06, most: 1 },
  { prop: "cart", where: { floors: [0], grounds: ["dirt"], near: "wall" }, per: 0.01, most: 1 },
  { prop: "stall", where: { floors: [0], market: true }, per: 0.3, most: 1 },
  { prop: "pebbles", where: { bands: "all", near: "wall" }, per: 0.14, most: 1 },
  { prop: "cobweb", where: { bands: [0, 3, 8], near: "corner" }, per: 0.4, most: 1 },
  { prop: "cobweb", where: { bands: [1, 2, 4, 5, 7, 9], near: "corner" }, per: 0.12, most: 1 },
  // the bands: 0 Catacombs, 1 Flooded Vaults, 2 Dwarven Halls, 3 the Palace, 4 Drowned Town, 5 Fungal Deep, 6 Crystal Caverns, 7 Foundry, 8 Ossuary, 9 Root
  { prop: "dust", where: { bands: [0, 3], near: "wall" }, per: 0.1, most: 1 },
  { prop: "coffinlid", where: { bands: [0] }, per: 0.012, most: 1 },
  { prop: "candle", where: { bands: [0, 3], near: "corner" }, per: 0.15, most: 1 },
  { prop: "puddle", where: { bands: [1, 4] }, per: 0.08, most: 1 },
  { prop: "slime", where: { bands: [1, 5], near: "wall" }, per: 0.1, most: 1 },
  { prop: "rotcrate", where: { bands: [1], near: "wall" }, per: 0.03, most: 1 },
  { prop: "rubble", where: { bands: [2, 9], near: "wall" }, per: 0.1, most: 1 },
  { prop: "pick", where: { bands: [2] }, per: 0.012, most: 1 },
  { prop: "rails", where: { bands: [2] }, per: 0.02, most: 1 },
  { prop: "armour", where: { bands: [2, 3], near: "wall" }, per: 0.025, most: 1 },
  { prop: "glass", where: { bands: [3] }, per: 0.04, most: 1 },
  { prop: "urn", where: { bands: [3], near: "wall" }, per: 0.035, most: 1 },
  { prop: "candelabra", where: { bands: [3], near: "corner" }, per: 0.2, most: 1 },
  { prop: "frost", where: { bands: [3], near: "wall" }, per: 0.1, most: 1 },
  { prop: "weed", where: { bands: [1, 4] }, per: 0.08, most: 1 },
  { prop: "shells", where: { bands: [4] }, per: 0.05, most: 1 },
  { prop: "oar", where: { bands: [4], near: "wall" }, per: 0.015, most: 1 },
  { prop: "fungi", where: { bands: [5], near: "wall" }, per: 0.2, most: 2 },
  { prop: "shard", where: { bands: [6], near: "wall" }, per: 0.18, most: 2 },
  { prop: "slag", where: { bands: [7], near: "wall" }, per: 0.08, most: 1 },
  { prop: "chains", where: { bands: [7, 8] }, per: 0.03, most: 1 },
  { prop: "cogs", where: { bands: [7] }, per: 0.04, most: 1 },
  { prop: "bonepile", where: { bands: [8], near: "corner" }, per: 0.4, most: 1 },
  { prop: "roots", where: { bands: [9] }, per: 0.12, most: 1 },
  // the named rooms, in any band
  { prop: "coins", where: { bands: "all", rooms: ["Treasure Vault"] }, per: 0.35, most: 2 },
  { prop: "books", where: { bands: "all", rooms: ["Library"] }, per: 0.3, most: 1 },
  { prop: "scrolls", where: { bands: "all", rooms: ["Library"] }, per: 0.2, most: 1 },
  { prop: "urn", where: { bands: "all", rooms: ["Crypt", "Charnel Pit"], near: "wall" }, per: 0.25, most: 1 },
  { prop: "coffinlid", where: { bands: "all", rooms: ["Crypt"] }, per: 0.12, most: 1 },
  { prop: "straw", where: { bands: "all", rooms: ["Den"] }, per: 0.45, most: 1 },
  { prop: "bones", where: { bands: "all", rooms: ["Den", "Charnel Pit"] }, per: 0.2, most: 1 },
  { prop: "candle", where: { bands: "all", rooms: ["Shrine", "Drowned Chapel"], near: "wall" }, per: 0.3, most: 1 },
  { prop: "puddle", where: { bands: "all", rooms: ["Fountain Hall"] }, per: 0.15, most: 1 },
  { prop: "rock", where: { bands: [2, 6, 9], near: "wall" }, per: 0.08, most: 1 },
  { prop: "bones", where: { bands: [0, 3, 8], near: "wall" }, per: 0.07, most: 1 },
  { prop: "skull", where: { bands: [0, 8], near: "corner" }, per: 0.35, most: 1 },
];
// on the dungeon's walls, by band: [decal, chance a wall face has it]; the first that the face's hash falls under is drawn
CM.WALL_DECALS = {
  0: [["crack", 0.08], ["niche", 0.13], ["sconce", 0.16]],
  1: [["wet", 0.12], ["moss", 0.22], ["crack", 0.27]],
  2: [["crack", 0.06], ["chains", 0.09], ["sconce", 0.13]],
  3: [["banner", 0.08], ["crack", 0.12], ["frost", 0.18]],
  4: [["wet", 0.14], ["moss", 0.26]],
  5: [["moss", 0.2], ["wet", 0.26]],
  6: [["crack", 0.1]],
  7: [["chains", 0.08], ["soot", 0.2], ["crack", 0.25]],
  8: [["niche", 0.15], ["crack", 0.22]],
  9: [["roots", 0.25], ["crack", 0.3]],
};
// overhead, by band: beams across, or things hanging (stalactites, roots); `per` the chance a square has one
CM.OVERHEAD = { 2: { id: "beam", how: "beam", per: 0.22 }, 7: { id: "beam", how: "beam", per: 0.2 }, 3: { id: "rib", how: "beam", per: 0.12 },
  6: { id: "stalactite", how: "hang", per: 0.18, w: 0.4, h: 0.32 }, 9: { id: "hangroot", how: "hang", per: 0.22, w: 0.6, h: 0.42 }, 1: { id: "stalactite", how: "hang", per: 0.06, w: 0.3, h: 0.22 } };
CM.DETAIL = { low: 0, medium: 0.6, high: 1 };
// the air, by where the party is: [{ id, rate (a second, at full detail) }]; env: { surface, band, season, weather, night,
// hour, town } - the dungeon's dust, drips, embers, spores and glitter by band; on the surface leaves, fireflies, rain,
// snow, clouds, birds and chimney smoke, by the season, the weather and the hour
CM.AIR_BUDGET = { low: 0, medium: 180, high: 360 };
CM.airKinds = function (env) {
  const out = [], add = (id, rate) => out.push({ id, rate });
  if (!env.surface) {
    add("mote", 10);
    if ([1, 4].includes(env.band)) add("drip", 3);
    if (env.band === 7) add("ember", 6);
    if (env.band === 5) add("spore", 5);
    if (env.band === 6) add("glitter", 6);
    if (env.band === 9) add("spore", 2);
    return out;
  }
  const { season, weather, night } = env;
  if (weather === "rain") add("rain", 320);
  if (weather === "snow" || (season === "winter" && weather === "wind")) add("snow", weather === "snow" ? 50 : 8);
  if (season !== "winter" && weather !== "rain") add("leaf", season === "autumn" ? 4 : 0.6);
  if (night && season === "summer" && weather !== "rain") add("firefly", 3);
  if (!night && weather !== "rain" && weather !== "snow") add("bird", 0.08);
  add("cloud", weather === "clear" ? 0.04 : 0.1);
  if (env.town) add("smoke", night || season === "winter" || season === "autumn" ? 4 : 1.5);
  if (!night && weather !== "rain") add("mote", 1.5);
  return out;
};
CM.windOf = (weather) => (weather === "wind" ? [1.4, 0.5] : weather === "rain" ? [0.5, 0.2] : [0.15, 0.05]);
CM.TRACES_MOST = 40;                                                    // a floor keeps this many traces; the oldest go first
// the floor's traces as props to draw (every Detail shows them: they are the party's own doing)
CM.traceProps = (fl) => (fl && fl.traces ? fl.traces.filter((t) => CM.PROPS[t.id]).map((t) => { const P = CM.PROPS[t.id], s = P.size[0] + (t.s || 0.5) * (P.size[1] - P.size[0]);
  return { id: t.id, how: P.how, layer: `prop:${t.id}`, x: t.x, y: t.y, dx: t.dx, dz: t.dz, w: s, h: s * (P.h || 1), turn: t.turn, trace: true }; }) : []);
// what a fallen foe leaves: bones for the dead, ash for the fiery, ooze for the soft and the sporing, a stain for the rest
CM.remainsOf = (m) => { const kind = CM.monsterKind(m.kind || m.name) || {}, name = `${m.kind || m.name}`;
  return kind.undead || m.undead ? "bones" : /Demon|Imp|Hound|Ember|Fire|Salamander|Wyvern/.test(name) ? "ash" : /Slime|Ooze|Fung|Spore|Mold|Jelly/.test(name) ? "ooze" : "stain"; };
CM.DETAIL_ORDER = ["low", "medium", "high"];
CM.isSurface = (fl) => Boolean(fl && (fl.number === 0 || fl.number === -1));
// what lies on each square: [{ id, how, layer, x, y, dx, dz, w, h, turn }]; ctx: { season } (the run's; summer when not said)
CM.scatter = function (fl, seed, density = CM.DETAIL.medium, ctx = {}) {
  const out = [];
  if (!fl || !density) return out;
  const grid = fl.grid, size = grid.length, surface = CM.isSurface(fl), band = surface ? -1 : CM.themeIndex(fl.number >= 1 ? fl.number : 1);
  const open = (x, y) => x >= 0 && y >= 0 && x < size && y < size && grid[y][x] === 0;
  const wet = new Set((fl.decor || []).filter((d) => d.kind === "water").map((d) => `${d.x},${d.y}`));
  const season = ctx.season || "summer", market = String(seed).startsWith("weekly-");
  const rules = CM.SCATTER.filter((r) => { const w = r.where;
    if (surface ? !(w.surface || (w.floors && w.floors.includes(fl.number))) : !(w.bands && (w.bands === "all" || w.bands.includes(band)))) return false;
    if (w.seasons && !w.seasons.includes(season)) return false;
    return !(w.market && !market); });
  const canopy = new Set(fl.canopy || []), tree = (x, y) => CM.isSurface(fl) && x >= 0 && y >= 0 && x < size && y < size && grid[y][x] !== 0 && CM.solidAt(fl, x, y) === "tree";
  const F = CM.FIELDS, S = CM.TOWN_SQUARE;
  const roomOf = new Map(); for (const r of fl.rooms || []) if (r.name) for (let ry = r.y0; ry <= r.y1; ry++) for (let rx = r.x0; rx <= r.x1; rx++) roomOf.set(`${rx},${ry}`, r.name);
  if (!rules.length) return out;
  for (let y = 0; y < size; y++) for (let x = 0; x < size; x++) {
    if (grid[y][x] !== 0) continue;
    const k = `${x},${y}`, t = fl.things[k];
    if ((t && t.type !== "monsters") || fl.features[k]) continue;                    // (never on a thing or a feature; on the water, only what belongs there)
    const isWet = wet.has(k);
    const trees = [[-1, -1], [0, -1], [1, -1], [-1, 0], [1, 0], [-1, 1], [0, 1], [1, 1]].some(([dx, dy]) => tree(x + dx, y + dy));
    const byWater = CM.DIRS.some(([dx, dy]) => wet.has(`${x + dx},${y + dy}`));
    const walls = CM.DIRS.map(([dx, dy]) => !open(x + dx, y + dy));               // north, east, south, west
    const ground = surface ? CM.groundAt(fl, x, y) || "grass" : null;
    const rnd = new CM.Random(CM.hashSeed(`${seed}:props:${fl.number}:${k}`));
    for (const r of rules) {
      const w = r.where;
      if (Boolean(w.water) !== isWet) continue;
      if (w.grounds && !w.grounds.includes(ground)) continue;
      if (w.canopy !== undefined && w.canopy !== canopy.has(k)) continue;
      if (w.near === "tree" && !trees) continue;
      if (w.near === "water" && !byWater) continue;
      if (w.area === "fields" && !(F && x >= F[0] && x <= F[2] && y >= F[1] && y <= F[3])) continue;
      if (w.area === "forest" && F && x >= F[0]) continue;
      if (w.market && !(S && fl.number === 0 && x >= S[0] && x <= S[2] && y >= S[1] && y <= S[3])) continue;
      if (w.rooms && !w.rooms.includes(roomOf.get(k))) continue;
      let toward = null;
      if (w.near === "wall") { const sides = [0, 1, 2, 3].filter((d) => walls[d]); if (!sides.length) continue; toward = [sides[rnd.int(0, sides.length - 1)]]; }
      if (w.near === "corner") { const c = [[0, 1], [1, 2], [2, 3], [3, 0]].filter(([a, b]) => walls[a] && walls[b]); if (!c.length) continue; toward = c[rnd.int(0, c.length - 1)]; }
      for (let i = 0; i < (r.most || 1); i++) {
        if (!rnd.chance(r.per * density)) continue;
        const P = CM.PROPS[r.prop], s = P.size[0] + rnd.next() * (P.size[1] - P.size[0]);
        let dx = (rnd.next() - 0.5) * (r.where.water ? 0 : 0.6), dz = (rnd.next() - 0.5) * (r.where.water ? 0 : 0.6);
        if (toward) { dx = 0; dz = 0; for (const d of toward) { dx += CM.DIRS[d][0] * (0.5 - s / 2 - 0.04); dz += CM.DIRS[d][1] * (0.5 - s / 2 - 0.04); } dx += (rnd.next() - 0.5) * (toward.length === 1 ? 0.4 : 0.05); }
        const item = { id: r.prop, how: P.how, layer: `prop:${r.prop}`, x, y, dx, dz, w: s, h: s * (P.h || 1), turn: rnd.next() * Math.PI };
        if (P.how === "corner") { if (!toward || toward.length !== 2) continue; item.corner = [CM.DIRS[toward[0]][0] + CM.DIRS[toward[1]][0], CM.DIRS[toward[0]][1] + CM.DIRS[toward[1]][1]]; }
        out.push(item);
      }
    }
  }
  return out;
};
