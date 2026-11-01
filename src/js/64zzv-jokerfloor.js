"use strict";
// Into the Joker (v17.7): the Gilded Joker as a place to walk - floor -9 in the save, "the Gilded Joker" in words, made
// the same for every seed. A foyer from the street door (the way back out), and the great hall: the house's services
// along the north wall (the prize counter, the tournament's easel, the quest board, the VIP door, the exchange, the
// high-roller's table, the house's books, the wardrobe, the collections, the almanac, the charm case, the ledger, the
// Joker's standing, the week's board, the Hall of Champions, the loyalty desk, the trophy cabinet), and every table on
// the floor in rows - the fairground to the west, the card tables and the wheels in the middle, the cabinets of the
// arcade wing to the east - with the six residents standing about at their favourites. Walk onto a table and press
// Space to sit down at it (the window opens at that table); onto a resident to hear what they say; onto the door to go
// back out into the town. The window's side - the door's choice, the pictures - is 76zzza-walk.js.
{ const JF = CM.JOKER_FLOOR = -9;
  CM.isJokerFloor = (n) => n === JF;
  CM.JOKER_THEME = Object.assign({}, CM.THEMES[2], {
    name: "The Gilded Joker", floors: [JF, JF], stone: [112, 34, 46], mortar: [196, 150, 64], floor: [118, 30, 42], ceiling: [36, 20, 28], moss: [200, 160, 60],
    fog: [0.004, 0.003, 0.003], torch: [1.0, 0.86, 0.62], reach: 14, bones: 0, grade: [1.05, 0.98, 0.93], joker: true, lightColour: [1.0, 0.82, 0.55] });
  CM.JOKER_CATS = ["fair", "tables", "luck", "prizes", "puzzles", "idle", "arcade"];
  CM.JOKER_AREAS = { fair: "the fairground yard", tables: "the card tables", luck: "the wheels and the slips", prizes: "the prize machines", puzzles: "the quiet tables", idle: "the workshops", arcade: "the arcade wing" };
  CM.JOKER_SERVICES = [["prizes", "The prize counter"], ["tour", "Tournament night's easel"], ["quests", "The quest board"], ["vip", "The VIP room's door"], ["exchange", "The ticket exchange"], ["highroller", "The high-roller's table"], ["odds", "The house's books"],
    ["wardrobe", "The wardrobe"], ["books", "The collection books"], ["almanac", "The Joker's Almanac"], ["charms", "The charm case"], ["history", "Your ledger"], ["standing", "The Joker's standing"], ["week", "The week's board"], ["hall", "The Hall of Champions"], ["loyalty", "The loyalty desk"], ["trophies", "The trophy cabinet"]];
  CM.JOKER_FAVOURITES = { tavern: "bigwheel", merchant: "plinko", smith: "darts", library: "bingo", priest: "lottery", farm: "pond" };
  const SIZE = 37, FOYER = [15, 23, 21, 30], START = [18, 26], EXIT = [18, 29];
  CM.makeJokerFloor = function () {
    const grid = []; for (let y = 0; y < SIZE; y++) grid.push(new Array(SIZE).fill(1));
    const carve = (x0, y0, x1, y1) => { for (let y = y0; y <= y1; y++) for (let x = x0; x <= x1; x++) grid[y][x] = 0; };
    carve(2, 2, SIZE - 3, 21); carve(...FOYER); carve(17, 21, 19, 23);                      // (the hall, the foyer, the arch between)
    const things = {}, key = (x, y) => `${x},${y}`, rooms = [{ x0: FOYER[0], y0: FOYER[1], x1: FOYER[2], y1: FOYER[3], name: "the foyer" }];
    things[key(...EXIT)] = { type: "jokerexit" };
    CM.JOKER_SERVICES.forEach(([view, name], i) => { things[key(2 + 2 * i, 2)] = { type: "cgservice", view, name }; });
    // the tables, by kind, filling the hall's columns west to east
    const order = (CM.CG_TABLES || []).slice().sort((a, b) => CM.JOKER_CATS.indexOf((CM.CG_INFO[a[0]] || { cat: "tables" }).cat) - CM.JOKER_CATS.indexOf((CM.CG_INFO[b[0]] || { cat: "tables" }).cat));
    const spots = []; for (let x = 4; x <= SIZE - 5; x += 3) for (let y = 5; y <= 20; y += 3) spots.push([x, y]);
    order.forEach(([id], i) => { const s = spots[i] || [FOYER[0] + (i % 2 ? 6 : 0), FOYER[1] + 1 + Math.floor((i - spots.length) / 2) * 2]; things[key(...s)] = { type: "cgtable", id }; });
    for (const [who, fav] of Object.entries(CM.JOKER_FAVOURITES)) { const at = Object.keys(things).find((k) => things[k].type === "cgtable" && things[k].id === fav); if (!at) continue; const [x, y] = at.split(",").map(Number);
      const c = [[x + 1, y], [x - 1, y], [x, y + 1], [x, y - 1]].find(([a, b]) => grid[b] && grid[b][a] === 0 && !things[key(a, b)]); if (c) things[key(...c)] = { type: "cgresident", who }; }
    const seen = []; for (let y = 0; y < SIZE; y++) for (let x = 0; x < SIZE; x++) seen.push([x, y]);   // (lit: the whole hall is on the map)
    return { number: JF, grid, things, features: {}, dark: [], seen, decor: [], rooms, special: "joker", pos: START.slice(), facing: 0, start: START.slice() };
  };
  // the floor's own: its theme, its making
  { const tf0 = CM.themeFor; CM.themeFor = (n) => (n === JF ? CM.JOKER_THEME : tf0(n)); const mf0 = CM.makeFloor; CM.makeFloor = (n, seed, gen) => (n === JF ? CM.makeJokerFloor(seed) : mf0(n, seed, gen)); }
  // where the party stands, in words: the area by the nearest table, and the table it's at
  CM.jokerPlace = (fl, x, y) => { const t = fl.things[`${x},${y}`];
    if (t && t.type === "cgtable") return `at ${((CM.CG_TABLES || []).find(([k]) => k === t.id) || [])[1] || t.id}`; if (t && t.type === "cgservice") return `at ${t.name.replace(/^The /, "the ")}`; if (t && t.type === "jokerexit") return "the street door";
    const r = (fl.rooms || []).find((q) => x >= q.x0 && x <= q.x1 && y >= q.y0 && y <= q.y1); if (r) return r.name; if (y <= 3) return "the north wall";
    let best = null, bd = 1e9; for (const [k, q] of Object.entries(fl.things)) { if (q.type !== "cgtable") continue; const [a, b] = k.split(",").map(Number), d = Math.abs(a - x) + Math.abs(b - y); if (d < bd) { bd = d; best = q; } }
    return best ? CM.JOKER_AREAS[(CM.CG_INFO[best.id] || { cat: "tables" }).cat] || "the floor" : "the floor"; };
  { const po0 = CM.placeOf; CM.placeOf = (fl, x, y) => (fl && fl.number === JF ? CM.jokerPlace(fl, x, y) : po0(fl, x, y)); }
  // what's underfoot, said when the party steps onto it
  CM.jokerDescribe = (t) => { if (t.type === "cgtable") { const nm = ((CM.CG_TABLES || []).find(([k]) => k === t.id) || [])[1] || t.id; return `${nm}: ${(CM.CG_INFO[t.id] || {}).line || ""} (Space to sit down)`; }
    if (t.type === "cgservice") return `${t.name}. (Space)`; if (t.type === "jokerexit") return "The street door, and the town beyond. (Space to go out)";
    if (t.type === "cgresident") { const R = CM.HE && CM.HE.RES[t.who]; return R ? `${R.name.charAt(0).toUpperCase() + R.name.slice(1)} is here, by ${(((CM.CG_TABLES || []).find(([k]) => k === CM.JOKER_FAVOURITES[t.who]) || [])[1]) || "the tables"}. (Space to talk)` : ""; } return ""; };
  CM.JOKER_TALK = { tavern: ["\"The wheel's my table. Number one, every time - it comes up more than you'd think.\"", "\"Pull up a stool, love. The Joker's kind tonight.\""], merchant: ["\"The Drop Board's middle risk is the honest one. Read the books on the wall if you don't believe me.\"", "\"Never stake what you can't count.\""],
    smith: ["\"Darts. Steady hand. That's all it is.\"", "\"Treble twenty. Again. Again.\""], library: ["\"Bingo is mostly patience. I have a great deal of patience.\"", "\"The house's odds are posted on the north wall. Fewer people read them than you'd hope.\""],
    priest: ["\"Six numbers. I pray for none of them; it seems only fair.\"", "\"Fortune is a poor god to pray to, but a fine one to watch.\""], farm: ["\"I've seen the golden carp! Well. I've seen its shadow.\"", "\"The eels come up after dark. Bring worms.\""] };
  const P = CM.Game.prototype;
  Object.assign(P, {
    // in through the street door, from the town
    jfEnter() { if (!this.floor || this.floor.number !== 0) return "The Joker's doors are in town."; this.logAct && this.logAct("jokerEnter"); this.sound && this.sound("door"); this.enterFloor(JF, "rope", START.slice()); this.floor.facing = 0;
      this.say("Through the street door, out of the night and into the Gilded Joker: warm light, red carpet, the clatter of the reels and the murmur of the crowd. The tables go back further than seems possible."); this.emit("floor", this.floor); this.emit("change"); return ""; },
    // back out to the street outside the door
    jfLeave() { const town = this.floorAt(0), door = Object.keys(town.things).find((k) => town.things[k].type === "building" && town.things[k].id === "casino"), [dx, dy] = (door || "27,14").split(",").map(Number);
      const out = CM.DIRS.map(([a, b]) => [dx + a, dy + b]).find(([x, y]) => town.grid[y] && town.grid[y][x] === 0 && !town.things[`${x},${y}`]) || [dx, dy + 1];
      this.sound && this.sound("door"); this.enterFloor(0, "rope", out); this.floor.facing = 2; this.say("Out through the street door, into the town again."); this.emit("floor", this.floor); this.emit("change"); },
    jfTalk(t) { const R = CM.HE && CM.HE.RES[t.who], L = CM.JOKER_TALK[t.who]; if (!R || !L) return; const line = L[(this.tally.steps || 0) % L.length]; this.say(`${R.name.charAt(0).toUpperCase() + R.name.slice(1)}: ${line}`); this.emit("talk", { title: R.name.charAt(0).toUpperCase() + R.name.slice(1), text: line }); },
  });
}
