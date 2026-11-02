"use strict";
// Interiors (v24.6, UPGRADE_PLAN_19.md): the town's houses can be walked into. Through the door of the Hanged Lantern,
// the Merchant's House, the forge, the Library, the Temple, the Guildhall, the Chronicler's House or the party's own
// house, the party steps into a furnished room of its own - a counter with the keeper behind it, shelves, tables and
// benches, a hearth, an anvil, bookcases, pews and an altar, a bed - and Space at the keeper (or at home, the hearth)
// opens the same window the door used to. The door in the south wall goes back out into the street. A building not
// yet raised still opens its window at the door, as before. Floors -21 to -28 in the save; nothing burns indoors, and
// the shops' rules count a room as being in town (Game.inTown). The furniture is solid (76zzzzh-models.js's kit).
{ const IN = CM.INTERIORS = {
    tavern: { n: -21, who: "res_tavern", name: "the Hanged Lantern", style: "inn", keeper: "The landlady, behind the bar" },
    merchant: { n: -22, who: "res_merchant", name: "the Merchant's House", style: "inn", keeper: "The merchant, at the counter" },
    smith: { n: -23, who: "res_smith", name: "the Smith's forge", style: "forge", keeper: "The smith, by the anvil" },
    library: { n: -24, who: "res_library", name: "the Library", style: "library", keeper: "The librarian, at the desk" },
    temple: { n: -25, who: "res_priest", name: "the Temple", style: "temple", keeper: "The priest, at the altar" },
    guildhall: { n: -26, who: "adventurer", name: "the Guildhall", style: "hall", keeper: "The guildmaster, at the counter" },
    chronicler: { n: -27, who: "res_library", name: "the Chronicler's House", style: "library", keeper: "The chronicler, at the desk" },
    home: { n: -28, who: null, name: "your house", style: "inn", keeper: "The hearth" },
  };
  const BY_N = {}; for (const [id, R] of Object.entries(IN)) BY_N[R.n] = id;
  CM.isInterior = (n) => BY_N[n] !== undefined;
  CM.interiorOf = (n) => BY_N[n] || null;
  // may the party walk in? only once the house stands (the rest still open their window at the door)
  CM.interiorOpen = (game, id) => { if (!IN[id] || CM.interiorsOff) return false;
    if (id === "tavern" || id === "merchant" || id === "smith") return true; if (id === "home") return game.homeLevel() >= 1;
    return game.villageLevel(id === "temple" ? "shrine" : id) >= 1; };
  // the themes: a set of its own for each style (its walls, floor and ceiling painted below)
  const base = CM.THEMES[2];
  const theme = (id) => Object.assign({}, base, { name: IN[id].name.charAt(0).toUpperCase() + IN[id].name.slice(1), floors: [IN[id].n, IN[id].n], fog: [0.02, 0.014, 0.01], torch: [1.0, 0.86, 0.66], reach: 9,
    bones: 0, grade: IN[id].style === "temple" ? [1.0, 0.98, 1.02] : [1.04, 0.99, 0.94], interior: IN[id].style, lightColour: [1.0, 0.78, 0.5] });
  const THEMES = {}; for (const id of Object.keys(IN)) THEMES[IN[id].n] = theme(id);
  // the rooms: a 9 x 8 room, the door in the south wall, a clear way from the door to the keeper
  const SIZE = 13, START = [6, 9], EXIT = [6, 10], KEEP = [6, 3];
  const F = (id, x, y, o = {}) => Object.assign({ id, x, y }, o);
  const N = Math.PI, E = -Math.PI / 2, W = Math.PI / 2, S = 0;          // (which way a thing's front faces: into the room)
  const counter = [3, 4, 5, 7, 8, 9].map((x) => F("counter", x, 4, { turn: S }));
  const LAYOUT = {
    tavern: [...counter, F("barrel", 3, 2), F("barrel", 4, 2), F("shelf", 8, 2, { turn: S, dz: -0.3 }), F("shelf", 9, 2, { turn: S, dz: -0.3 }), F("hearth", 2, 6, { turn: E, dx: -0.3 }),
      F("table", 3, 7), F("stool", 3, 8), F("stool", 4, 7), F("table", 9, 7), F("stool", 9, 8), F("stool", 8, 7), F("table", 9, 5), F("stool", 10, 5)],
    merchant: [...counter, F("shelf", 3, 2, { turn: S, dz: -0.3 }), F("shelf", 4, 2, { turn: S, dz: -0.3 }), F("shelf", 8, 2, { turn: S, dz: -0.3 }), F("shelf", 9, 2, { turn: S, dz: -0.3 }),
      F("crate", 2, 7), F("crate", 2, 8), F("barrel", 3, 8), F("crate", 10, 6), F("barrel", 10, 7), F("barrel", 10, 8), F("table", 8, 7)],
    smith: [F("anvil", 5, 4), F("anvil", 7, 4, { turn: W }), F("hearth", 2, 4, { turn: E, dx: -0.3, forge: true }), F("hearth", 2, 5, { turn: E, dx: -0.3, forge: true }), F("barrel", 3, 7), F("shelf", 10, 5, { turn: W, dx: 0.3 }),
      F("shelf", 10, 6, { turn: W, dx: 0.3 }), F("crate", 9, 8), F("table", 9, 3)],
    library: [F("counter", 5, 4), F("counter", 7, 4), ...[2, 3, 4, 8, 9, 10].map((x) => F("shelf", x, 2, { turn: S, dz: -0.3, books: true })), ...[5, 6, 7, 8].map((y) => F("shelf", 2, y, { turn: E, dx: -0.3, books: true })),
      ...[5, 6, 7, 8].map((y) => F("shelf", 10, y, { turn: W, dx: 0.3, books: true })), F("table", 4, 7), F("stool", 4, 8), F("table", 8, 7), F("stool", 8, 8)],
    temple: [F("altar", 6, 2), ...[3, 4, 8, 9].flatMap((x) => [F("pew", x, 5), F("pew", x, 7)]), F("shelf", 2, 3, { turn: E, dx: -0.3, books: true }), F("shelf", 10, 3, { turn: W, dx: 0.3, books: true })],
    guildhall: [...counter, F("shelf", 3, 2, { turn: S, dz: -0.3 }), F("shelf", 9, 2, { turn: S, dz: -0.3 }), F("table", 3, 7), F("table", 4, 7), F("stool", 3, 8), F("stool", 4, 8), F("table", 8, 7), F("table", 9, 7), F("stool", 8, 8), F("stool", 9, 8),
      F("shelf", 2, 5, { turn: E, dx: -0.3 }), F("shelf", 10, 5, { turn: W, dx: 0.3 })],
    chronicler: [F("counter", 5, 4), F("counter", 7, 4), ...[3, 4, 8, 9].map((x) => F("shelf", x, 2, { turn: S, dz: -0.3, books: true })), F("shelf", 2, 6, { turn: E, dx: -0.3, books: true }), F("shelf", 10, 6, { turn: W, dx: 0.3, books: true }), F("table", 4, 7), F("table", 8, 7)],
    home: [F("hearth", 6, 2, { turn: S, dz: -0.3 }), F("table", 4, 6), F("stool", 4, 7), F("stool", 3, 6), F("bed", 9, 7), F("crate", 10, 8), F("shelf", 2, 4, { turn: E, dx: -0.3 }), F("barrel", 10, 3)],
  };
  const LIGHTS = { tavern: [["candelabra", 6, 5], ["ember", 3, 6]], merchant: [["candelabra", 6, 6]], smith: [["ember", 3, 4], ["ember", 3, 5]], library: [["candle", 4, 7], ["candle", 8, 7], ["candelabra", 6, 6]],
    temple: [["candelabra", 4, 2], ["candelabra", 8, 2], ["candle", 6, 3]], guildhall: [["candelabra", 6, 6]], chronicler: [["candle", 4, 7], ["candle", 8, 7]], home: [["ember", 6, 3], ["candle", 4, 6]] };
  CM.makeInterior = (n) => {
    const id = BY_N[n], grid = []; for (let y = 0; y < SIZE; y++) grid.push(new Array(SIZE).fill(1));
    for (let y = 2; y <= 9; y++) for (let x = 2; x <= 10; x++) grid[y][x] = 0; grid[EXIT[1]][EXIT[0]] = 0;
    const things = {}, features = {}, key = (x, y) => `${x},${y}`, furniture = [];
    things[key(...EXIT)] = { type: "intexit", id };
    if (id === "home") things[key(6, 3)] = { type: "inthearth", id }; else if (id !== "smith") things[key(...KEEP)] = { type: "intkeeper", id }; else things[key(6, 5)] = { type: "intkeeper", id };
    for (const f of LAYOUT[id]) { furniture.push({ id: f.id, how: "model", layer: `prop:${f.id}`, x: f.x, y: f.y, dx: f.dx || 0, dz: f.dz || 0, w: f.id === "counter" || f.id === "shelf" || f.id === "pew" ? 0.98 : 0.8, h: 0.8, turn: f.turn || 0, books: f.books, forge: f.forge });
      if (f.id !== "stool") features[key(f.x, f.y)] = { type: "furniture" }; }
    const seen = []; for (let y = 0; y < SIZE; y++) for (let x = 0; x < SIZE; x++) seen.push([x, y]);
    const decor = (LIGHTS[id] || []).map(([kind, x, y]) => ({ kind, x, y, light: true }));
    return { number: n, grid, things, features, dark: [], seen, decor, rooms: [{ x0: 2, y0: 2, x1: 10, y1: 9, name: IN[id].name }], special: "interior", interior: id, name: IN[id].name, furniture, pos: START.slice(), facing: 0, start: START.slice() };
  };
  { const tf0 = CM.themeFor; CM.themeFor = (n) => (THEMES[n] || tf0(n)); const mf0 = CM.makeFloor; CM.makeFloor = (n, seed, gen) => (BY_N[n] !== undefined ? CM.makeInterior(n) : mf0(n, seed, gen)); }
  // furniture stands in the way
  { const p0 = CM.passable; CM.passable = function (floor, x, y) { const f = floor.features[`${x},${y}`]; if (f && f.type === "furniture") return false; return p0.call(this, floor, x, y); }; }
  // what the room is made of: only its own furniture, and nothing on its walls but its lamps
  { const sc0 = CM.scatter; CM.scatter = function (fl, seed, density, ctx) { if (fl && fl.special === "interior") return (fl.furniture || []).map((p) => Object.assign({}, p)); return sc0.call(this, fl, seed, density, ctx); }; }
  { const fm0 = CM.floorMesh; CM.floorMesh = function (fl, th, index, opts = {}) { return fm0.call(this, fl, th, index, fl && fl.special === "interior" ? Object.assign({}, opts, { decals: false }) : opts); }; }
  // where the party stands, in words, and what is underfoot
  { const po0 = CM.placeOf; CM.placeOf = (fl, x, y) => { if (!fl || fl.special !== "interior") return po0(fl, x, y); const t = fl.things[`${x},${y}`]; return t && t.type === "intexit" ? "by the door" : t && (t.type === "intkeeper" || t.type === "inthearth") ? (t.type === "inthearth" ? "at the hearth" : "at the counter") : fl.name; }; }
  CM.interiorDescribe = (t) => { const R = IN[t.id]; if (!R) return ""; if (t.type === "intexit") return "The door, and the street outside. (Space to go out)";
    if (t.type === "inthearth") return "Your own hearth: the house's rooms, the stash and the kitchen. (Space)"; return `${R.keeper}. (Space)`; };
  const P = CM.Game.prototype;
  { const it0 = P.inTown; P.inTown = function () { return it0.call(this) || Boolean(this.floor && this.floor.special === "interior" && this.mode === "explore"); }; }
  { const bu0 = P.burn; P.burn = function (...a) { if (this.floor && this.floor.special === "interior") return; return bu0.apply(this, a); }; }
  { const ef0 = P.enterFloor; P.enterFloor = function (number, how, at) {   // (a door is a step, not a stair: a minute, not an hour a floor)
      const from = this.floor ? this.floor.number : null, inside = (n) => n !== null && BY_N[n] !== undefined, c = this.clock || 0, out = ef0.call(this, number, how, at);
      if (inside(number) || inside(from)) this.clock = c + 1; return out; }; }
  Object.assign(P, {
    intEnter(id) { const R = IN[id]; if (!R || !this.floor || this.floor.number !== 0 || !CM.interiorOpen(this, id)) return false; this.logAct && this.logAct("intEnter", id); this.sound && this.sound("door"); this.enterFloor(R.n, "rope", START.slice()); this.floor.facing = 0;
      this.say(`In through the door of ${R.name}.`); this.emit("floor", this.floor); this.emit("change"); return true; },
    intLeave() { const id = this.floor && this.floor.interior, B = id && CM.TOWN_BLOCKS[id]; if (!B) return; const [dx, dy] = B.door, [x0, y0, x1, y1] = B.rect;
      const facing = dy > y1 ? 2 : dy < y0 ? 0 : dx > x1 ? 1 : 3; this.sound && this.sound("door"); this.enterFloor(0, "rope", [dx, dy]); this.floor.facing = facing; this.say("Out through the door, into the street."); this.emit("floor", this.floor); this.emit("change"); },
  });
  // Automatic steps out of a room before it goes on (a room is not a place it has errands in)
  { const st0 = CM.Autopilot.prototype.step; CM.Autopilot.prototype.step = function (...a) { const g = this.game; if (g && g.floor && g.floor.special === "interior" && g.mode === "explore") { g.intLeave(); return "out of the room"; } return st0.apply(this, a); }; }
}
