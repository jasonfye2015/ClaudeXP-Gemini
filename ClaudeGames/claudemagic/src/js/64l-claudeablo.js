"use strict";
// Claudeablo through the red portal (the sixteenth update): the Timeline's Claudeablo (ClaudeGames/claudeablo:
// dungeon.py, items.py, world.py) ported whole - Haven and its four townsfolk, fifty levels down to Vorthak the Undying (the
// Cathedral, the Catacombs, the Caves, Hell, the Abyss, the Sanctum), the loot of white, blue and gold, the spells,
// the shrines, the portals and the waystone. One of the party goes through (61i-redportal.js says what comes back);
// the window draws it (76f-claudeablo.js). Tiles and seconds, as there; the dice are the world's own.
const AB = CM.AB = { WALL: 0, FLOOR: 1, LAVA: 2 };
AB.themeFor = (depth) => (depth <= 0 ? "town" : depth === 50 ? "sanctum" : ["cathedral", "catacombs", "caves", "hell", "abyss"][Math.min(4, Math.floor((depth - 1) / 10))]);
AB.THEME_NAMES = { town: "Haven", cathedral: "Cathedral", catacombs: "Catacombs", caves: "Caves", hell: "Hell", abyss: "The Abyss", sanctum: "The Undying Sanctum" };
// the dice, with Python's ways
AB.Rng = class {
  constructor(seed) { this.R = new CM.Random(typeof seed === "number" ? seed >>> 0 : CM.hashSeed(String(seed))); }
  random() { return this.R.next(); }
  uniform(a, b) { return a + (b - a) * this.R.next(); }
  randint(a, b) { return a + Math.floor(this.R.next() * (b - a + 1)); }
  choice(list) { return list[Math.floor(this.R.next() * list.length)]; }
  sample(list, n) { const l = list.slice(); for (let i = l.length - 1; i > 0; i--) { const j = Math.floor(this.R.next() * (i + 1)); [l[i], l[j]] = [l[j], l[i]]; } return l.slice(0, n); }
  choices(list, weights) { let r = this.R.next() * weights.reduce((s, w) => s + w, 0); for (let i = 0; i < list.length; i++) { r -= weights[i]; if (r <= 0) return list[i]; } return list[list.length - 1]; }
};
const K2 = (x, y) => `${x},${y}`;

// ---- the places --------------------------------------------------------------------------------------------------
AB.Level = class {
  constructor(w, h, theme, depth) { Object.assign(this, { w, h, theme, depth, rooms: [], up: null, down: null, spawn: null }); this.grid = Array.from({ length: h }, () => new Array(w).fill(AB.WALL)); this.style = {}; this.decor = {}; this.places = {}; }
  inside(x, y) { return x >= 0 && x < this.w && y >= 0 && y < this.h; }
  floor(x, y) { return this.inside(x, y) && this.grid[y][x] === AB.FLOOR; }
  wall(x, y) { return !this.inside(x, y) || this.grid[y][x] === AB.WALL; }
  walkable(x, y) { return this.floor(Math.floor(x), Math.floor(y)); }
  carve(x0, y0, x1, y1, t = AB.FLOOR) { for (let y = Math.max(1, y0); y < Math.min(this.h - 1, y1 + 1); y++) for (let x = Math.max(1, x0); x < Math.min(this.w - 1, x1 + 1); x++) this.grid[y][x] = t; }
  floors() { const out = []; for (let y = 0; y < this.h; y++) for (let x = 0; x < this.w; x++) if (this.grid[y][x] === AB.FLOOR) out.push([x, y]); return out; }
  distances(start) { const d = new Map([[K2(...start), 0]]), q = [start]; for (let h = 0; h < q.length; h++) { const [x, y] = q[h]; for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) { const k = K2(x + dx, y + dy); if (!d.has(k) && this.floor(x + dx, y + dy)) { d.set(k, d.get(K2(x, y)) + 1); q.push([x + dx, y + dy]); } } } return d; }
};
AB.generate = function (seed, depth) {
  const rnd = new AB.Rng(`${seed}:${depth}`), theme = AB.themeFor(depth);
  if (theme === "sanctum") return AB.sanctum(depth);
  const size = 46 + Math.floor(Math.min(depth, 30) / 2), lv = new AB.Level(size, size, theme, depth);
  if (theme === "caves") AB.caves(lv, rnd);
  else { const small = theme === "catacombs"; AB.rooms(lv, rnd, small ? 4 : 5, small ? 8 : 12); if (theme === "hell" || theme === "abyss") AB.lavaPools(lv, rnd); }
  AB.keepConnected(lv); AB.stairs(lv, rnd); AB.scatterDecor(lv, rnd);
  return lv;
};
AB.rooms = function (lv, rnd, minRoom, maxRoom) {
  const split = (x, y, w, h, depth = 0) => {
    if (depth > 5 || (w < maxRoom * 2 && h < maxRoom * 2)) return [[x, y, w, h]];
    const horizontal = Math.abs(h - w) > 4 ? h > w : rnd.random() < 0.5;
    if (horizontal && h >= minRoom * 2 + 2) { const cut = rnd.randint(minRoom + 1, h - minRoom - 1); return split(x, y, w, cut, depth + 1).concat(split(x, y + cut, w, h - cut, depth + 1)); }
    if (!horizontal && w >= minRoom * 2 + 2) { const cut = rnd.randint(minRoom + 1, w - minRoom - 1); return split(x, y, cut, h, depth + 1).concat(split(x + cut, y, w - cut, h, depth + 1)); }
    return [[x, y, w, h]];
  };
  for (const [x, y, w, h] of split(1, 1, lv.w - 2, lv.h - 2)) {
    const rw = rnd.randint(minRoom, Math.max(minRoom, Math.min(maxRoom, w - 2))), rh = rnd.randint(minRoom, Math.max(minRoom, Math.min(maxRoom, h - 2)));
    const rx = x + rnd.randint(1, Math.max(1, w - rw - 1)), ry = y + rnd.randint(1, Math.max(1, h - rh - 1));
    lv.carve(rx, ry, rx + rw - 1, ry + rh - 1); lv.rooms.push([rx, ry, rw, rh]);
  }
  const centres = lv.rooms.map(([rx, ry, rw, rh]) => [rx + Math.floor(rw / 2), ry + Math.floor(rh / 2)]);
  const order = centres.map((_, i) => i).sort((a, b) => { const ka = [Math.floor(centres[a][1] / 12), centres[a][0] * (Math.floor(centres[a][1] / 12) % 2 === 0 ? 1 : -1)], kb = [Math.floor(centres[b][1] / 12), centres[b][0] * (Math.floor(centres[b][1] / 12) % 2 === 0 ? 1 : -1)]; return ka[0] - kb[0] || ka[1] - kb[1]; });
  for (let i = 0; i + 1 < order.length; i++) AB.hall(lv, centres[order[i]], centres[order[i + 1]], rnd);
  for (let k = 0; k < Math.max(1, Math.floor(centres.length / 4)); k++) { const [a, b] = rnd.sample(centres.map((_, i) => i), 2); if (b !== undefined) AB.hall(lv, centres[a], centres[b], rnd); }
};
AB.hall = function (lv, [x0, y0], [x1, y1], rnd) {
  const wide = rnd.random() < 0.35 && lv.theme !== "catacombs" ? 1 : 0;
  if (rnd.random() < 0.5) { lv.carve(Math.min(x0, x1), y0, Math.max(x0, x1), y0 + wide); lv.carve(x1, Math.min(y0, y1), x1 + wide, Math.max(y0, y1)); }
  else { lv.carve(x0, Math.min(y0, y1), x0 + wide, Math.max(y0, y1)); lv.carve(Math.min(x0, x1), y1, Math.max(x0, x1), y1 + wide); }
};
AB.caves = function (lv, rnd) {
  let g = Array.from({ length: lv.h }, (_, y) => Array.from({ length: lv.w }, (_, x) => (x === 0 || x === lv.w - 1 || y === 0 || y === lv.h - 1 || rnd.random() < 0.44 ? AB.WALL : AB.FLOOR)));
  for (let k = 0; k < 5; k++) { const n = Array.from({ length: lv.h }, () => new Array(lv.w).fill(AB.WALL)); for (let y = 1; y < lv.h - 1; y++) for (let x = 1; x < lv.w - 1; x++) { let walls = 0; for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) walls += g[y + dy][x + dx] === AB.WALL ? 1 : 0; n[y][x] = walls >= 5 ? AB.WALL : AB.FLOOR; } g = n; }
  lv.grid = g;
  for (let r = rnd.randint(1, 2); r > 0; r--) { let x = rnd.randint(5, lv.w - 6), y = 2; while (y < lv.h - 2) { for (const dx of [0, 1]) if (lv.grid[y][x + dx] === AB.FLOOR && rnd.random() < 0.85) lv.grid[y][x + dx] = AB.LAVA; y++; x = Math.max(3, Math.min(lv.w - 5, x + rnd.choice([-1, 0, 0, 1]))); } }   // (a lava river or two)
  for (let y = 2, step = rnd.randint(6, 9); y < lv.h - 2; y += step) for (let x = 1; x < lv.w - 1; x++) if (lv.grid[y][x] === AB.LAVA) lv.grid[y][x] = AB.FLOOR;   // (gaps to cross by)
};
AB.lavaPools = function (lv, rnd) { for (const [rx, ry, rw, rh] of lv.rooms) if (rw >= 8 && rh >= 8 && rnd.random() < 0.55) { const cx = rx + Math.floor(rw / 2), cy = ry + Math.floor(rh / 2), r = Math.floor(Math.min(rw, rh) / 4); for (let y = cy - r; y <= cy + r; y++) for (let x = cx - r; x <= cx + r; x++) if ((x - cx) ** 2 + (y - cy) ** 2 <= r * r && lv.grid[y][x] === AB.FLOOR) lv.grid[y][x] = AB.LAVA; } };
AB.keepConnected = function (lv) {
  const seen = new Set(); let best = new Set();
  for (const f of lv.floors()) { if (seen.has(K2(...f))) continue; const area = new Set(lv.distances(f).keys()); for (const k of area) seen.add(k); if (area.size > best.size) best = area; }
  for (const [x, y] of lv.floors()) if (!best.has(K2(x, y))) lv.grid[y][x] = AB.WALL;
};
AB.stairs = function (lv, rnd) {
  const floors = lv.floors(); let start = null;
  if (lv.rooms.length) { const [rx, ry, rw, rh] = lv.rooms[0]; start = [rx + Math.floor(rw / 2), ry + Math.floor(rh / 2)]; }
  if (!start || !lv.floor(...start)) start = rnd.choice(floors);
  const d = lv.distances(start); let far = start, fd = -1; for (const [k, v] of d) if (v > fd) { fd = v; far = k.split(",").map(Number); }
  lv.up = start; lv.down = far; lv.spawn = AB.nearFree(lv, start);
};
AB.nearFree = function (lv, [x, y]) {
  for (let r = 1; r < 6; r++) for (let dx = -r; dx <= r; dx++) for (let dy = -r; dy <= r; dy++) { const nx = x + dx, ny = y + dy; if (lv.floor(nx, ny) && !(lv.up && lv.up[0] === nx && lv.up[1] === ny) && !(lv.down && lv.down[0] === nx && lv.down[1] === ny)) return [nx, ny]; }
  return [x, y];
};
AB.scatterDecor = function (lv, rnd) {
  const marks = { cathedral: ["blood", "bones", "rug", "cracks"], catacombs: ["bones", "bones", "blood", "cracks"], caves: ["rocks", "bones", "cracks"], hell: ["blood", "bones", "skulls", "cracks"], abyss: ["skulls", "blood", "cracks"] }[lv.theme];
  const fl = lv.floors(); for (const f of rnd.sample(fl, Math.max(1, Math.floor(fl.length / 30)))) if (!(lv.up && K2(...f) === K2(...lv.up)) && !(lv.down && K2(...f) === K2(...lv.down))) lv.decor[K2(...f)] = rnd.choice(marks);
};
AB.sanctum = function (depth) {
  const lv = new AB.Level(44, 44, "sanctum", depth), cx = 22, cy = 16, r = 11;
  for (let y = 0; y < lv.h; y++) for (let x = 0; x < lv.w; x++) if ((x - cx) ** 2 + (y - cy) ** 2 <= r * r) lv.grid[y][x] = AB.FLOOR;
  lv.carve(cx - 1, cy + r - 1, cx + 1, 40); lv.carve(cx - 4, 36, cx + 4, 41);
  for (let y = 0; y < lv.h; y++) for (let x = 0; x < lv.w; x++) { const d2 = (x - cx) ** 2 + (y - cy) ** 2; if (lv.grid[y][x] === AB.FLOOR && d2 >= 30 && d2 <= 40 && (x + y) % 3 === 0) lv.grid[y][x] = AB.LAVA; if (lv.grid[y][x] === AB.FLOOR && d2 <= 20) lv.decor[K2(x, y)] = "pentagram"; }
  lv.up = [cx, 40]; lv.down = null; lv.spawn = [cx, 38]; lv.places.diablo = [cx, cy - 2];
  return lv;
};
// Haven: a little village above the cathedral, the same every time (and, here, a portal home to the Keep-yard)
AB.town = function () {
  const lv = new AB.Level(44, 44, "town", 0); lv.carve(2, 2, 41, 41);
  for (let x = 0; x < lv.w; x++) for (let y = 0; y < lv.h; y++) if (Math.min(x, y, lv.w - 1 - x, lv.h - 1 - y) < 2) { lv.grid[y][x] = AB.WALL; lv.style[K2(x, y)] = "tree"; }
  const rnd = new AB.Rng(7);
  for (let k = 0; k < 60; k++) { const x = rnd.randint(2, 41), y = rnd.randint(2, 41); if (Math.min(x, y, 43 - x, 43 - y) < 5 && !(x >= 18 && x <= 25)) { lv.grid[y][x] = AB.WALL; lv.style[K2(x, y)] = "tree"; } }
  const house = (x0, y0, w, h, door, key) => { for (let y = y0; y < y0 + h; y++) for (let x = x0; x < x0 + w; x++) { lv.grid[y][x] = AB.WALL; lv.style[K2(x, y)] = "house"; } lv.places[key] = door; };
  house(8, 9, 6, 5, [11, 15], "smith"); house(29, 8, 6, 5, [32, 14], "witch"); house(8, 27, 5, 5, [10, 33], "healer"); house(30, 28, 6, 5, [33, 34], "elder");
  for (let y = 3; y < 8; y++) for (let x = 18; x < 26; x++) { lv.grid[y][x] = AB.WALL; lv.style[K2(x, y)] = "church"; }
  lv.down = [22, 9]; lv.places.waystone = [25, 20]; lv.places.portal = [19, 22]; lv.places.well = [22, 21]; lv.places.home = [19, 26];
  lv.grid[21][22] = AB.WALL; lv.style[K2(22, 21)] = "well"; lv.spawn = [22, 24]; lv.up = null;
  for (let x = 14; x < 30; x++) lv.decor[K2(x, 22)] = "path";
  for (let y = 10; y < 36; y++) lv.decor[K2(22, y)] = lv.decor[K2(22, y)] || "path";
  for (const [x, y] of [[11, 16], [12, 16], [32, 15], [10, 34], [33, 35], [20, 26], [21, 26]]) lv.decor[K2(x, y)] = "path";
  for (const f of rnd.sample(lv.floors(), 70)) if (!lv.decor[K2(...f)]) lv.decor[K2(...f)] = rnd.choice(["flowers", "grasstuft", "grasstuft", "stone"]);
  return lv;
};
// A* over floor tiles (8 directions, no corner cutting): the tiles after start, or []
AB.path = function (lv, start, goal, blocked = null, limit = 4000) {
  if (!lv.floor(...goal)) return [];
  const sk = K2(...start), gk = K2(...goal), came = new Map([[sk, null]]), cost = new Map([[sk, 0]]), open = [[0, start]];
  while (open.length && came.size < limit) {
    let bi = 0; for (let i = 1; i < open.length; i++) if (open[i][0] < open[bi][0]) bi = i;
    const [, cur] = open.splice(bi, 1)[0], ck = K2(...cur); if (ck === gk) break;
    const [x, y] = cur;
    for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1], [1, 1], [1, -1], [-1, 1], [-1, -1]]) {
      const n = [x + dx, y + dy], nk = K2(...n);
      if (!lv.floor(...n) || (blocked && blocked.has(nk) && nk !== gk)) continue;
      if (dx && dy && (!lv.floor(x + dx, y) || !lv.floor(x, y + dy))) continue;
      const c = cost.get(ck) + (dx && dy ? 1.414 : 1);
      if (!cost.has(nk) || c < cost.get(nk)) { cost.set(nk, c); came.set(nk, ck); open.push([c + Math.max(Math.abs(goal[0] - n[0]), Math.abs(goal[1] - n[1])), n]); }
    }
  }
  if (!came.has(gk)) return [];
  const out = []; let cur = gk; while (cur !== sk) { out.push(cur.split(",").map(Number)); cur = came.get(cur); }
  return out.reverse();
};

// ---- the loot ------------------------------------------------------------------------------------------------------
// name: [kind, slot, ilvl, stat (damage [lo, hi] or armour), requirements [str, dex, mag], value]
AB.BASES = {
  Dagger: ["dagger", "weapon", 1, [1, 4], [0, 0, 0], 60], "Short Sword": ["sword", "weapon", 1, [2, 6], [18, 0, 0], 120], Club: ["mace", "weapon", 1, [1, 6], [0, 0, 0], 40], "Hand Axe": ["axe", "weapon", 2, [2, 7], [22, 0, 0], 110],
  Mace: ["mace", "weapon", 3, [3, 8], [24, 0, 0], 200], "Long Sword": ["sword", "weapon", 4, [3, 10], [30, 30, 0], 350], "Broad Axe": ["axe", "weapon", 6, [4, 12], [40, 0, 0], 450], "Morning Star": ["mace", "weapon", 8, [5, 11], [36, 0, 0], 520],
  Scimitar: ["sword", "weapon", 9, [4, 14], [25, 45, 0], 600], "Bastard Sword": ["sword", "weapon", 12, [6, 15], [50, 0, 0], 900], "War Hammer": ["mace", "weapon", 14, [6, 18], [55, 0, 0], 1100], "Great Sword": ["sword", "weapon", 18, [10, 22], [75, 0, 0], 1800],
  "Grand Axe": ["axe", "weapon", 22, [12, 26], [85, 0, 0], 2400], Maul: ["mace", "weapon", 26, [12, 30], [95, 0, 0], 3000], Runeblade: ["sword", "weapon", 32, [14, 32], [80, 60, 20], 4200],
  "Short Bow": ["bow", "weapon", 1, [1, 4], [0, 15, 0], 100], "Hunter's Bow": ["bow", "weapon", 3, [2, 6], [20, 35, 0], 300], "Long Bow": ["bow", "weapon", 6, [3, 9], [25, 45, 0], 500], "Composite Bow": ["bow", "weapon", 10, [4, 12], [30, 55, 0], 900],
  "War Bow": ["bow", "weapon", 16, [6, 16], [45, 70, 0], 1600], "Hellfire Bow": ["bow", "weapon", 28, [10, 24], [55, 95, 0], 3600],
  "Short Staff": ["staff", "weapon", 1, [2, 4], [0, 0, 20], 120], "Long Staff": ["staff", "weapon", 5, [4, 8], [0, 0, 35], 400], "Composite Staff": ["staff", "weapon", 12, [5, 10], [0, 0, 50], 1000], "War Staff": ["staff", "weapon", 22, [8, 16], [30, 0, 70], 2200], "Archon Staff": ["staff", "weapon", 34, [10, 20], [35, 0, 100], 4400],
  Rags: ["armor", "armor", 1, 2, [0, 0, 0], 10], "Quilted Armor": ["armor", "armor", 1, 5, [0, 0, 0], 60], "Leather Armor": ["armor", "armor", 3, 8, [0, 0, 0], 150], "Studded Leather": ["armor", "armor", 6, 12, [20, 0, 0], 300], "Ring Mail": ["armor", "armor", 9, 17, [30, 0, 0], 600],
  "Chain Mail": ["armor", "armor", 13, 22, [35, 0, 0], 900], "Scale Mail": ["armor", "armor", 17, 28, [45, 0, 0], 1300], "Splint Mail": ["armor", "armor", 22, 34, [55, 0, 0], 1800], "Plate Mail": ["armor", "armor", 27, 42, [65, 0, 0], 2600], "Full Plate": ["armor", "armor", 33, 52, [80, 0, 0], 3600], "Gothic Plate": ["armor", "armor", 40, 64, [95, 0, 0], 5000],
  Cap: ["helm", "helm", 1, 2, [0, 0, 0], 20], "Skull Cap": ["helm", "helm", 3, 4, [0, 0, 0], 80], Helm: ["helm", "helm", 7, 7, [25, 0, 0], 250], "Full Helm": ["helm", "helm", 13, 11, [35, 0, 0], 600], Crown: ["helm", "helm", 18, 13, [0, 0, 0], 1000], "Great Helm": ["helm", "helm", 25, 18, [55, 0, 0], 1700], "Bone Visage": ["helm", "helm", 36, 25, [70, 0, 0], 3200],
  Buckler: ["shield", "shield", 1, 3, [0, 0, 0], 40], "Small Shield": ["shield", "shield", 3, 6, [25, 0, 0], 120], "Large Shield": ["shield", "shield", 8, 10, [40, 0, 0], 400], "Kite Shield": ["shield", "shield", 14, 14, [50, 0, 0], 800], "Tower Shield": ["shield", "shield", 22, 20, [65, 0, 0], 1500], "Gothic Shield": ["shield", "shield", 32, 27, [80, 0, 0], 2800],
  Ring: ["ring", "ring", 2, 0, [0, 0, 0], 300], Amulet: ["amulet", "amulet", 5, 0, [0, 0, 0], 500],
};
AB.TWO_HANDED = new Set(["bow", "staff"]); AB.LARGE_TWO_HANDED = new Set(["Great Sword", "Grand Axe", "Maul"]);
AB.SUPPLIES = { "Potion of Healing": ["potion", 50, 1], "Potion of Mana": ["potion", 50, 1], "Potion of Full Healing": ["potion", 160, 8], "Potion of Full Mana": ["potion", 160, 8], "Potion of Rejuvenation": ["potion", 300, 14], "Scroll of Town Portal": ["scroll", 200, 1], "Scroll of Identify": ["scroll", 100, 1] };
AB.SPELLS = { Firebolt: [6, 1000, 1, "Hurls a bolt of fire."], Healing: [10, 1000, 1, "Restores some of your life."], Lightning: [12, 3000, 5, "A crackling bolt that tears through a line of foes."], Fireball: [18, 6000, 10, "A ball of fire that explodes among your enemies."],
  "Town Portal": [24, 3000, 6, "Opens a portal back to town (and back again)."], "Chain Lightning": [26, 11000, 18, "Lightning that leaps from foe to foe."], Teleport: [28, 14000, 22, "Blink to where you point."], Nova: [36, 21000, 28, "A ring of lightning bursts out around you."], Inferno: [14, 9000, 15, "Breathes a stream of flame."] };
for (const [n, [, v, lvl]] of Object.entries(AB.SPELLS)) AB.SUPPLIES[`Book of ${n}`] = ["book", v, lvl];
const AB_WEAPONS = ["dagger", "sword", "axe", "mace", "bow", "staff"], AB_ARMOUR = ["armor", "helm", "shield"], AB_JEWEL = ["ring", "amulet"];
AB.PREFIXES = {
  to_hit: [AB_WEAPONS.concat(AB_JEWEL), [[1, "Bronze", 5, 10], [5, "Iron", 11, 20], [12, "Steel", 21, 35], [20, "Silver", 36, 50], [30, "Gold", 51, 75], [40, "Platinum", 76, 100]]],
  dmg_pct: [AB_WEAPONS, [[1, "Jagged", 20, 35], [4, "Deadly", 36, 50], [8, "Heavy", 51, 65], [13, "Vicious", 66, 80], [18, "Brutal", 81, 95], [24, "Massive", 96, 120], [30, "Savage", 121, 150], [38, "Ruthless", 151, 180], [45, "Merciless", 181, 220]]],
  ac_pct: [AB_ARMOUR, [[1, "Sturdy", 20, 35], [4, "Strong", 36, 50], [9, "Glorious", 51, 65], [14, "Blessed", 66, 80], [20, "Saintly", 81, 100], [27, "Awesome", 101, 130], [34, "Holy", 131, 160], [42, "Godly", 161, 200]]],
  res_fire: [AB_ARMOUR.concat(AB_JEWEL), [[3, "Red", 10, 20], [10, "Crimson", 21, 30], [20, "Garnet", 31, 45], [32, "Ruby", 46, 60]]],
  res_light: [AB_ARMOUR.concat(AB_JEWEL), [[3, "Blue", 10, 20], [10, "Azure", 21, 30], [20, "Lapis", 31, 45], [32, "Sapphire", 46, 60]]],
  life: [AB_ARMOUR.concat(AB_JEWEL), [[1, "Fox's", 10, 15], [6, "Jackal's", 16, 25], [12, "Wolf's", 26, 40], [20, "Tiger's", 41, 55], [28, "Lion's", 56, 70], [36, "Mammoth's", 71, 90], [44, "Whale's", 91, 120]]],
  mana: [AB_JEWEL.concat(["staff", "helm", "armor"]), [[1, "Spider's", 10, 15], [6, "Raven's", 16, 25], [12, "Snake's", 26, 40], [20, "Serpent's", 41, 55], [28, "Drake's", 56, 70], [36, "Dragon's", 71, 90], [44, "Wyrm's", 91, 120]]],
  spell_lvl: [["staff", "amulet"], [[15, "Angel's", 1, 1], [35, "Arch-Angel's", 2, 2]]],
};
AB.SUFFIXES = {
  str: [AB_WEAPONS.concat(AB_ARMOUR, AB_JEWEL), [[1, "of Strength", 1, 5], [8, "of Might", 6, 10], [16, "of Power", 11, 15], [26, "of Giants", 16, 20], [38, "of Titans", 21, 30]]],
  dex: [AB_WEAPONS.concat(AB_ARMOUR, AB_JEWEL), [[1, "of Dexterity", 1, 5], [8, "of Skill", 6, 10], [16, "of Accuracy", 11, 15], [26, "of Precision", 16, 20], [38, "of Perfection", 21, 30]]],
  mag: [AB_WEAPONS.concat(AB_ARMOUR, AB_JEWEL), [[1, "of Magic", 1, 5], [8, "of the Mind", 6, 10], [16, "of Brilliance", 11, 15], [26, "of Sorcery", 16, 20], [38, "of Wizardry", 21, 30]]],
  vit: [AB_WEAPONS.concat(AB_ARMOUR, AB_JEWEL), [[1, "of Vitality", 1, 5], [8, "of Zest", 6, 10], [16, "of Vim", 11, 15], [26, "of Vigor", 16, 20], [38, "of Life", 21, 30]]],
  all: [AB_ARMOUR.concat(AB_JEWEL, AB_WEAPONS), [[20, "of the Sky", 3, 6], [34, "of the Moon", 7, 10], [45, "of the Heavens", 11, 15]]],
  leech: [AB_WEAPONS.concat(AB_JEWEL), [[6, "of the Leech", 3, 5], [20, "of Blood", 6, 9]]],
  speed: [AB_WEAPONS, [[4, "of Readiness", 10, 10], [14, "of Swiftness", 20, 20], [28, "of Speed", 30, 30], [40, "of Haste", 40, 40]]],
  fire_dmg: [AB_WEAPONS, [[4, "of Burning", 1, 6], [16, "of Flame", 4, 14], [30, "of Hellfire", 10, 30]]],
  light_dmg: [AB_WEAPONS, [[6, "of Shock", 1, 8], [18, "of Lightning", 4, 18], [32, "of Thunder", 10, 36]]],
  light_radius: [AB_ARMOUR.concat(AB_JEWEL), [[1, "of Light", 1, 1], [12, "of Radiance", 2, 2]]],
  thorns: [AB_ARMOUR, [[5, "of Thorns", 1, 3], [18, "of Spikes", 4, 8], [32, "of Barbs", 9, 15]]],
  regen: [AB_ARMOUR.concat(AB_JEWEL), [[10, "of Regeneration", 2, 4], [26, "of Rejuvenation", 5, 8]]],
};
AB.LABELS = { to_hit: "+{v}% chance to hit", dmg_pct: "+{v}% damage", ac_pct: "+{v}% armor", res_fire: "Resist Fire: {v}%", res_light: "Resist Lightning: {v}%", life: "+{v} to life", mana: "+{v} to mana", spell_lvl: "+{v} to all spell levels",
  str: "+{v} to Strength", dex: "+{v} to Dexterity", mag: "+{v} to Magic", vit: "+{v} to Vitality", all: "+{v} to all attributes", leech: "Steals {v}% of damage as life", speed: "{v}% faster attacks", fire_dmg: "Adds {v} fire damage",
  light_dmg: "Adds {v} lightning damage", light_radius: "+{v} to light radius", thorns: "Attackers take {v} damage", regen: "Regenerates {v} life per second" };
AB.RARE_A = ["Doom", "Grim", "Blood", "Dread", "Storm", "Bone", "Raven", "Gloom", "Wraith", "Ghoul", "Plague", "Soul", "Viper", "Shadow", "Rune", "Fiend", "Hell", "Night", "Skull", "Corpse", "Death", "Wolf", "Demon", "Ash"];
AB.RARE_B = { weapon: ["Bite", "Fang", "Song", "Edge", "Thirst", "Kill", "Reaver", "Splitter", "Gnash", "Scythe"], armor: ["Shell", "Hide", "Carapace", "Shroud", "Cloak", "Coat", "Wrap", "Mantle"], helm: ["Crown", "Visage", "Brow", "Veil", "Horn", "Mask"], shield: ["Wall", "Guard", "Ward", "Aegis", "Bastion"], ring: ["Loop", "Coil", "Band", "Grip", "Circle"], amulet: ["Eye", "Heart", "Star", "Talisman", "Charm"] };
AB.RARITY_COLOURS = { normal: "#E8E8E8", magic: "#7090FF", rare: "#F0E060", unique: "#C8A060", supply: "#E8E8E8" };
AB.scale = (ilvl) => 1 + 0.045 * Math.max(0, ilvl - 1);
AB.make = function (base, ilvl = 1, rarity = "normal", rnd = null, ident = null) {
  rnd = rnd || new AB.Rng(Math.random() * 1e9 | 0);
  if (AB.SUPPLIES[base]) return { base, ilvl, rarity: "supply", affixes: [], ident: true, qty: 1 };
  const item = { base, ilvl, rarity, affixes: [], prefix: "", suffix: "", ident: ident === null ? true : ident, qty: 1 }, kind = AB.BASES[base][0];
  if (AB_JEWEL.includes(kind) && rarity === "normal") rarity = item.rarity = "magic";
  if (rarity === "magic") for (const which of rnd.choice([["p"], ["s"], ["p", "s"], ["p", "s"]])) AB.addAffix(item, which, rnd);
  else if (rarity === "rare") { for (const which of rnd.sample(["p", "p", "p", "s", "s", "s"], rnd.randint(3, 5))) AB.addAffix(item, which, rnd, false); item.rare_name = `${rnd.choice(AB.RARE_A)} ${rnd.choice(AB.RARE_B[AB.BASES[base][1]] || AB.RARE_B.weapon)}`; }
  if ((rarity === "magic" || rarity === "rare") && ident === null) item.ident = false;
  return item;
};
AB.addAffix = function (item, which, rnd, named = true) {
  const kind = AB.BASES[item.base][0], table = which === "p" ? AB.PREFIXES : AB.SUFFIXES, have = new Set(item.affixes.map((a) => a[0]));
  const options = Object.entries(table).filter(([stat, [kinds]]) => kinds.includes(kind) && !have.has(stat)); if (!options.length) return;
  const [stat, [, tiers]] = rnd.choice(options), usable = tiers.filter((t) => t[0] <= item.ilvl).length ? tiers.filter((t) => t[0] <= item.ilvl) : tiers.slice(0, 1);
  const [, name, lo, hi] = usable[Math.min(usable.length - 1, Math.floor(usable.length * rnd.random() ** 0.7))];   // (higher tiers rarer: toward the middle of what is allowed)
  item.affixes.push([stat, rnd.randint(lo, hi)]); if (named) item[which === "p" ? "prefix" : "suffix"] = name;
};
AB.randomDrop = function (ilvl, rnd, magicFind = 0, kinds = null) {
  const bases = Object.keys(AB.BASES).filter((b) => AB.BASES[b][2] <= ilvl + 2 && (!kinds || kinds.includes(AB.BASES[b][0]))), weights = bases.map((b) => 1 + (AB.BASES[b][2] / Math.max(1, ilvl)) * 2);
  const base = rnd.choices(bases, weights), r = rnd.random() * (1 - magicFind), rarity = r < 0.06 + ilvl * 0.0015 ? "rare" : r < 0.3 + ilvl * 0.003 ? "magic" : "normal";
  return AB.make(base, ilvl, rarity, rnd);
};
AB.randomSupply = function (ilvl, rnd) { const names = Object.keys(AB.SUPPLIES).filter((n) => AB.SUPPLIES[n][2] <= ilvl && !n.startsWith("Book")); return AB.make(rnd.choices(names, names.map((n) => (n.includes("Healing") && !n.includes("Full") ? 6 : n.includes("Mana") && !n.includes("Full") ? 4 : n.includes("Scroll") ? 2 : 1))), ilvl); };
AB.kind = (it) => (AB.SUPPLIES[it.base] ? AB.SUPPLIES[it.base][0] : AB.BASES[it.base][0]);
AB.slot = (it) => (AB.SUPPLIES[it.base] ? null : AB.BASES[it.base][1]);
AB.twoHanded = (it) => Boolean(AB.BASES[it.base] && (AB.TWO_HANDED.has(AB.BASES[it.base][0]) || AB.LARGE_TWO_HANDED.has(it.base)));
AB.stat = (it, name) => it.affixes.reduce((s, [a, v]) => s + (a === name || (a === "all" && ["str", "dex", "mag", "vit"].includes(name)) ? v : 0), 0);
AB.damage = (it) => { const [lo, hi] = AB.BASES[it.base][3], s = AB.scale(it.ilvl); return [Math.max(1, Math.round(lo * s)), Math.max(2, Math.round(hi * s))]; };
AB.armour = (it) => { const b = AB.BASES[it.base][3]; return b ? Math.round(b * AB.scale(it.ilvl) * (1 + AB.stat(it, "ac_pct") / 100)) : 0; };
AB.requirements = (it) => { if (!AB.BASES[it.base]) return [0, 0, 0]; const s = 1 + 0.012 * it.ilvl; return AB.BASES[it.base][4].map((r) => Math.round(r * s)); };
AB.name = (it) => { if (AB.SUPPLIES[it.base]) return (it.qty || 1) === 1 ? it.base : `${it.base} (${it.qty})`; if (!it.ident && (it.rarity === "magic" || it.rarity === "rare")) return it.base; if (it.rarity === "rare") return it.rare_name || it.base; return [it.prefix, it.base, it.suffix].filter(Boolean).join(" "); };
AB.colour = (it) => AB.RARITY_COLOURS[it.rarity] || "#E8E8E8";
AB.value = (it) => { if (AB.SUPPLIES[it.base]) return AB.SUPPLIES[it.base][1] * (it.qty || 1); let v = AB.BASES[it.base][5] * AB.scale(it.ilvl); for (const [a, x] of it.affixes) v += ({ dmg_pct: 12, ac_pct: 10, to_hit: 6, life: 18, mana: 14, spell_lvl: 3000, leech: 400, speed: 80, all: 450, fire_dmg: 60, light_dmg: 50, light_radius: 300 }[a] || 80) * x; if (it.rarity === "rare") v *= 1.6; return Math.floor(v); };
AB.sellPrice = (it) => { let v = Math.floor(AB.value(it) / 4); if (it.ident === false) v = Math.floor(v / 2); return Math.max(1, v); };
AB.buyPrice = (it) => Math.max(1, Math.floor(AB.value(it) * (AB.SUPPLIES[it.base] ? 1 : 1.25)));
AB.tooltip = function (it, pl) {
  const lines = [[AB.name(it), AB.colour(it)]];
  if (AB.SUPPLIES[it.base]) { if (AB.SUPPLIES[it.base][0] === "book") { const sp = it.base.slice(8); lines.push([AB.SPELLS[sp][3], "#C8C8C8"], [`Mana: ${AB.SPELLS[sp][0]}`, "#C8C8C8"], ["Right-click to read", "#A0A0A0"]); } else lines.push(["Right-click to use", "#A0A0A0"]); return lines; }
  const k = AB.BASES[it.base][0];
  if (it.rarity === "rare" && it.ident) lines.push([it.base, AB.colour(it)]);
  if (AB_WEAPONS.includes(k)) { const [lo, hi] = AB.damage(it); lines.push([`Damage: ${lo}-${hi}${AB.twoHanded(it) ? "  (two-handed)" : ""}`, "#FFFFFF"]); } else if (AB.BASES[it.base][3]) lines.push([`Armor: ${AB.armour(it)}`, "#FFFFFF"]);
  if (it.ident || it.rarity === "normal") for (const [a, v] of it.affixes) lines.push([AB.LABELS[a].replace("{v}", v), "#8098FF"]); else lines.push(["Not identified", "#FF6060"]);
  const req = AB.requirements(it), have = pl ? [pl.str_, pl.dex, pl.mag] : [999, 999, 999];
  ["Strength", "Dexterity", "Magic"].forEach((label, i) => { if (req[i]) lines.push([`Requires ${req[i]} ${label}`, have[i] < req[i] ? "#FF6060" : "#C8C8C8"]); });
  lines.push([`Item level ${it.ilvl}`, "#808080"]);
  return lines;
};

// ---- the rules: the hero, the monsters, combat, spells, shrines, portals --------------------------------------------
AB.CLASSES = {
  warrior: { str: 30, dex: 20, mag: 10, vit: 25, lpv: 2.0, lpl: 2.0, mpm: 1.0, mpl: 1.0, block: 30, speed: 4.0, swing: 0.95, start: ["Short Sword", "Buckler", "Quilted Armor"], spells: [] },
  rogue: { str: 20, dex: 30, mag: 15, vit: 20, lpv: 1.5, lpl: 1.5, mpm: 1.25, mpl: 1.5, block: 20, speed: 4.3, swing: 0.85, start: ["Short Bow", "Quilted Armor"], spells: [] },
  sorcerer: { str: 15, dex: 15, mag: 35, vit: 20, lpv: 1.0, lpl: 1.0, mpm: 2.0, mpl: 2.0, block: 10, speed: 4.0, swing: 1.0, start: ["Short Staff", "Rags"], spells: ["Firebolt"] },
};
// kind: [name, look, hp, [dmg lo, hi], ac, speed, xp, ai, missile]
AB.MONSTERS = {
  zombie: ["Zombie", "zombie", 16, [2, 5], 5, 1.1, 20, "melee", null], ghoul: ["Ghoul", "ghoul", 30, [4, 9], 12, 1.4, 45, "melee", null], skeleton: ["Skeleton", "skeleton", 11, [1, 5], 10, 2.0, 22, "melee", null],
  skeleton_archer: ["Skeleton Archer", "skeleton_archer", 9, [1, 4], 8, 1.8, 26, "ranged", "arrow"], fallen: ["Fallen One", "fallen", 8, [1, 4], 8, 2.6, 15, "pack", null], scavenger: ["Scavenger", "beast", 10, [1, 5], 6, 3.0, 18, "melee", null],
  bat: ["Fiend", "bat", 7, [1, 4], 12, 3.2, 20, "erratic", null], goatman: ["Goatman", "goatman", 24, [3, 8], 15, 2.2, 48, "melee", null], hidden: ["Hidden", "hidden", 22, [3, 9], 20, 2.6, 60, "stealth", null],
  hellwitch: ["Hell Witch", "hellwitch", 26, [2, 6], 18, 2.0, 80, "caster", "firebolt"], knight: ["Black Knight", "knight", 62, [8, 16], 40, 1.9, 140, "melee", null], magma: ["Magma Demon", "magma", 56, [6, 14], 30, 1.6, 150, "caster", "fireball"],
  pitlord: ["Pit Lord", "pitlord", 120, [12, 26], 45, 1.8, 300, "melee", null], diablo: ["Vorthak the Undying", "diablo", 260, [20, 40], 60, 2.0, 5000, "diablo", "redbolt"],
};
AB.THEME_MONSTERS = { cathedral: ["zombie", "zombie", "skeleton", "skeleton", "skeleton_archer", "fallen", "fallen", "scavenger", "bat"], catacombs: ["skeleton", "skeleton_archer", "ghoul", "goatman", "goatman", "bat", "hidden", "fallen"], caves: ["goatman", "scavenger", "hidden", "magma", "bat", "ghoul"], hell: ["hellwitch", "knight", "magma", "goatman", "hidden", "hellwitch"], abyss: ["knight", "pitlord", "hellwitch", "magma", "knight"] };
AB.BOSSES = { 5: ["The Flesher", "ghoul", { skin: "#B04040", body: "#5A1A1A", size: 1.45, weapon: "axe" }], 15: ["The Bone King", "skeleton", { size: 1.5, head: "skull", skin: "#F0E4B0" }], 25: ["Ignis the Lavalord", "magma", { size: 1.7 }], 35: ["Azmorath the Black", "knight", { size: 1.5, body: "#14141A", trim: "#E02020" }], 45: ["Baalzeth the Pit Lord", "pitlord", { size: 1.8 }] };
AB.CHAMP_A = ["Bloodlust", "Gorefeast", "Blightfang", "Rotclaw", "Soulripper", "Grimjaw", "Ashbringer", "Doomhowl", "Bonegnaw", "Vilespawn", "Deathwhisper", "Hollowgaze"];
AB.CHAMP_B = ["the Cursed", "the Unclean", "the Cold", "the Hungry", "the Wretched", "the Defiler", "the Fiery", "the Vile", "the Mad", "the Ancient"];
AB.SHRINES = [["Glimmering Shrine", "#F8F0A0"], ["Divine Shrine", "#FFFFFF"], ["Eerie Shrine", "#A060FF"], ["Abandoned Shrine", "#60FF90"], ["Creepy Shrine", "#FF6060"], ["Quiet Shrine", "#FFA040"], ["Hidden Shrine", "#60C0FF"], ["Ornate Shrine", "#FF40C0"], ["Gloomy Shrine", "#8080A0"], ["Fascinating Shrine", "#40E0E0"]];
AB.dist = (a, b) => Math.hypot(a.x - b.x, a.y - b.y);
// the facing on the screen from a movement in tile space (x runs down-right, y down-left): 0 SE, 1 SW, 2 NE, 3 NW
AB.facingFor = (dx, dy) => { const sx = dx - dy, sy = dx + dy; if (Math.abs(sx) < 1e-6 && Math.abs(sy) < 1e-6) return null; if (sy >= 0) return sx >= 0 ? 0 : 1; return sx >= 0 ? 2 : 3; };
const abActor = (o, x, y, rnd) => Object.assign(o, { x, y, facing: 0, pose: "stand", phase: (rnd ? rnd.random() : 0.5) * 6, anim: 0, hurt: 0, dead: false, path: [] });
const abTile = (a) => [Math.floor(a.x), Math.floor(a.y)];

AB.Player = class {
  constructor(cls = "warrior", name = "Hero") {
    abActor(this, 0, 0); const c = AB.CLASSES[cls]; this.isPlayer = true;
    Object.assign(this, { cls, name, level: 1, xp: 0, points: 0, base: { str: c.str, dex: c.dex, mag: c.mag, vit: c.vit }, gold: 100, inv: new Array(40).fill(null), equip: { weapon: null, shield: null, helm: null, armor: null, amulet: null, ring1: null, ring2: null }, belt: [null, null, null, null], spells: {}, activeSpell: c.spells[0] || null, maxDepth: 0, buffs: {}, target: null, cool: 0, repathT: 0, hitPending: null });
    for (const s of c.spells) this.spells[s] = 1;
    for (const b of c.start) { const it = AB.make(b, 1); this.equip[AB.slot(it)] = it; }
    for (let k = 0; k < 2; k++) this.beltAdd(AB.make("Potion of Healing"));
    if (cls === "sorcerer") this.beltAdd(AB.make("Potion of Mana"));
    this.addItem(AB.make("Scroll of Town Portal"));
    this.recalc(); this.hp = this.maxhp; this.mana = this.maxmana;
  }
  items() { return Object.values(this.equip).filter(Boolean); }
  affix(name) { return this.items().reduce((s, it) => s + AB.stat(it, name), 0); }
  recalc() {
    const c = AB.CLASSES[this.cls];
    this.str_ = this.base.str + this.affix("str"); this.dex = this.base.dex + this.affix("dex"); this.mag = this.base.mag + this.affix("mag"); this.vit = this.base.vit + this.affix("vit");
    this.maxhp = Math.floor(20 + this.vit * c.lpv + this.level * c.lpl + this.affix("life"));
    const staff = this.equip.weapon && AB.kind(this.equip.weapon) === "staff" ? 20 : 0;
    this.maxmana = Math.floor(this.mag * c.mpm + this.level * c.mpl + this.affix("mana") + staff);
    this.ac = this.items().filter((it) => ["armor", "helm", "shield"].includes(AB.slot(it))).reduce((s, it) => s + AB.armour(it), 0) + Math.floor(this.dex / 5);
    if (this.buffs["Hidden Shrine"]) this.ac = Math.floor(this.ac * 1.5);
    this.toHit = 50 + Math.floor(this.dex / 2) + this.level + this.affix("to_hit");
    const w = this.equip.weapon; this.ranged = Boolean(w && AB.kind(w) === "bow");
    const [lo, hi] = w ? AB.damage(w) : [1, 3], mult = 1 + this.affix("dmg_pct") / 100 + (this.buffs["Gloomy Shrine"] ? 0.3 : 0), flat = (this.ranged ? this.dex : this.str_) / 8 + this.level * 0.2;
    this.dmg = [Math.max(1, Math.floor(lo * mult + flat)), Math.max(2, Math.floor(hi * mult + flat))];
    this.elem = this.affix("fire_dmg") + this.affix("light_dmg"); this.swing = c.swing * (1 - Math.min(0.5, this.affix("speed") / 100));
    this.block = this.equip.shield ? Math.min(75, c.block + Math.floor(this.dex / 4)) : 0;
    this.resFire = Math.min(75, this.affix("res_fire")); this.resLight = Math.min(75, this.affix("res_light")); this.leech = this.affix("leech"); this.thorns = this.affix("thorns"); this.regen = this.affix("regen");
    this.light = 7 + this.affix("light_radius"); this.spellBonus = this.affix("spell_lvl"); this.speed = c.speed;
    if (this.hp !== undefined) { this.hp = Math.min(this.hp, this.maxhp); this.mana = Math.min(this.mana, this.maxmana); }
  }
  canEquip(it) { const [s, d, m] = AB.requirements(it); return this.str_ >= s && this.dex >= d && this.mag >= m; }
  nextLevelXp() { return Math.floor(40 * this.level ** 1.75 + 40); }
  addItem(it) {
    if (it.rarity === "supply") for (const x of this.inv) if (x && x.base === it.base && ["potion", "scroll"].includes(AB.kind(x)) && x.qty < 20) { x.qty += it.qty || 1; return true; }
    const i = this.inv.indexOf(null); if (i < 0) return false; this.inv[i] = it; return true;
  }
  beltAdd(it) { if (AB.kind(it) !== "potion") return false; const i = this.belt.indexOf(null); if (i < 0) return false; this.belt[i] = it; return true; }
  takeOne(base) { const i = this.inv.findIndex((it) => it && it.base === base); if (i < 0) return false; this.inv[i].qty -= 1; if (this.inv[i].qty <= 0) this.inv[i] = null; return true; }
  toJSON() { const o = {}; for (const k of ["cls", "name", "level", "xp", "points", "base", "gold", "inv", "equip", "belt", "spells", "activeSpell", "maxDepth", "hp", "mana"]) o[k] = this[k]; return JSON.parse(JSON.stringify(o)); }
  static fromJSON(d) { const p = new AB.Player(d.cls, d.name); for (const k of ["level", "xp", "points", "base", "gold", "inv", "equip", "belt", "spells", "activeSpell", "maxDepth"]) p[k] = JSON.parse(JSON.stringify(d[k])); p.recalc(); p.hp = Math.min(d.hp || p.maxhp, p.maxhp); p.mana = Math.min(d.mana || p.maxmana, p.maxmana); return p; }
};
AB.Monster = class {
  constructor(x, y, kind, mlevel, rnd, champion = false, boss = null) {
    abActor(this, x, y, rnd); const [name, look, hp, [lo, hi], ac, speed, xp, ai, missile] = AB.MONSTERS[kind];
    Object.assign(this, { kind, look, ai, missile, mlevel, name, looks: {}, champion, boss: Boolean(boss), res: { fire: 0, light: 0 }, isMonster: true });
    const grow = 1 + 0.29 * (mlevel - 1), dg = 1 + 0.12 * (mlevel - 1);
    this.maxhp = hp * grow * rnd.uniform(0.85, 1.15); this.dmg = [lo * dg, hi * dg]; this.ac = ac * (1 + 0.08 * (mlevel - 1)); this.toHit = 70 + 1.2 * mlevel; this.speed = speed; this.xp = xp * (1 + 0.15 * (mlevel - 1));
    if (["magma", "hellwitch", "diablo"].includes(kind)) this.res.fire = 50;
    if (kind === "skeleton" || kind === "skeleton_archer") this.res.light = 25;
    if (champion) { this.name = `${rnd.choice(AB.CHAMP_A)} ${rnd.choice(AB.CHAMP_B)}`; this.maxhp *= 3; this.dmg = [this.dmg[0] * 1.5, this.dmg[1] * 1.5]; this.xp *= 3; this.looks = { size: 1.15 }; }
    if (boss) { [this.name, this.look, this.looks] = [boss[0], boss[1], Object.assign({}, boss[2])]; this.maxhp *= 7; this.dmg = [this.dmg[0] * 1.8, this.dmg[1] * 1.8]; this.xp *= 10; this.ac *= 1.3; }
    if (kind === "diablo") { this.maxhp = 9000; this.dmg = [60, 120]; this.ac = 260; this.toHit = 150; this.boss = true; }
    Object.assign(this, { hp: this.maxhp, state: "idle", home: [x, y], cool: rnd.uniform(0, 1.5), repath: 0, special: 0, flee: 0, seen: false, zig: rnd.uniform(0, 6) });
  }
};
AB.Missile = class { constructor(kind, x, y, dx, dy, speed, dmg, owner, elem = "phys", radius = 0.35, life = 2.5) { const n = Math.hypot(dx, dy) || 1; Object.assign(this, { kind, x, y, vx: (dx / n) * speed, vy: (dy / n) * speed, dmg, owner, elem, radius, life, hit: new Set(), dead: false }); } };
AB.Obj = class { constructor(kind, x, y, kw) { Object.assign(this, { kind, x, y, opened: false, isObj: true }, kw || {}); } };

AB.World = class {
  constructor(seed, player) {
    Object.assign(this, { seed, player, rnd: new AB.Rng(seed), depth: 0, level: null, monsters: [], missiles: [], ground: [], objects: [], npcs: [], effects: [], messages: [], portal: null, flags: { diablo_dead: false }, time: 0, explored: new Set(), dead: false, wonAt: null, shopStock: {}, talkTo: null, waystoneOpen: false, homeWanted: false, events: [] });
    this.enter(0);
  }
  say(text, colour = "#E8E0C8") { this.messages.push([text, colour, this.time]); this.messages = this.messages.slice(-8); }
  fx(kind, kw = {}) { this.effects.push(Object.assign({ ttl: 0.5 }, kw, { kind, t0: this.time })); }
  ev(kind, extra) { this.events.push(Object.assign({ kind }, extra || {})); if (this.events.length > 100) this.events.shift(); }
  // ---- moving between places ----
  enter(depth, arrive = "up") {
    this.depth = depth; this.monsters = []; this.missiles = []; this.ground = []; this.objects = []; this.npcs = []; this.effects = []; this.explored = new Set();
    const p = this.player; p.path = []; p.target = null;
    if (depth === 0) {
      const lv = this.level = AB.town(), spot = { down: lv.down, portal: lv.places.portal, waystone: lv.places.waystone, home: lv.places.home }[arrive] || lv.spawn;
      this.place(spot); this.townPeople();
      this.objects.push(new AB.Obj("stairs_down", lv.down[0] + 0.5, lv.down[1] + 0.5), new AB.Obj("waystone", lv.places.waystone[0] + 0.5, lv.places.waystone[1] + 0.5), new AB.Obj("red_portal", lv.places.home[0] + 0.5, lv.places.home[1] + 0.5));   // (the red portal: home to the Keep-yard)
      if (this.portal) this.objects.push(new AB.Obj("portal", lv.places.portal[0] + 0.5, lv.places.portal[1] + 0.5));
      this.restock();
      if (p.hp < p.maxhp * 0.3) this.say("You're badly hurt. Tobin the healer can help.", "#FFB080");
      for (let y = 0; y < lv.h; y++) for (let x = 0; x < lv.w; x++) this.explored.add(K2(x, y));
      this.ev("enter", { depth });
      return;
    }
    const lv = this.level = AB.generate(this.seed, depth); p.maxDepth = Math.max(p.maxDepth, depth);
    if (lv.up) this.objects.push(new AB.Obj("stairs_up", lv.up[0] + 0.5, lv.up[1] + 0.5));
    if (lv.down) this.objects.push(new AB.Obj("stairs_down", lv.down[0] + 0.5, lv.down[1] + 0.5));
    if (arrive === "down" && lv.down) this.place(AB.nearFree(lv, lv.down));
    else if (arrive === "portal" && this.portal && this.portal[0] === depth) this.place([Math.floor(this.portal[1]), Math.floor(this.portal[2])]);
    else this.place(lv.spawn);
    if (this.portal && this.portal[0] === depth) this.objects.push(new AB.Obj("portal", this.portal[1], this.portal[2]));
    this.populate();
    this.say(depth < 50 ? `${AB.THEME_NAMES[lv.theme]}, level ${depth}` : "The Undying Sanctum. Vorthak waits below the candles.", "#F0C060");
    this.ev("enter", { depth });
  }
  place([x, y]) { this.player.x = x + 0.5; this.player.y = y + 0.5; }
  townPeople() { for (const [key, name, look] of [["smith", "Brannoc the Smith", "smith"], ["witch", "Isolde the Witch", "witch"], ["healer", "Tobin the Healer", "healer"], ["elder", "Aldous the Elder", "elder"]]) { const [x, y] = this.level.places[key]; this.npcs.push(abActor({ role: key, name, look, home: [x + 0.5, y + 0.5], wait: this.rnd.uniform(1, 4), isNpc: true }, x + 0.5, y + 0.5, this.rnd)); } }
  // new wares each visit to town, matched to the hero's level
  restock() {
    const p = this.player, rnd = new AB.Rng(`${this.seed}:${p.level}:${p.maxDepth}:${Math.floor(this.time / 60)}`), lvl = Math.max(1, p.maxDepth, p.level);
    const smith = []; for (let i = 0; i < 14; i++) { let it = AB.randomDrop(lvl, rnd, 0, ["dagger", "sword", "axe", "mace", "bow", "armor", "helm", "shield"]); if (it.rarity === "rare") it = AB.make(it.base, it.ilvl, "magic", rnd); it.ident = true; smith.push(it); }
    const witch = ["Potion of Healing", "Potion of Mana", "Scroll of Town Portal", "Scroll of Identify"].map((n) => AB.make(n));
    if (lvl >= 8) witch.push(AB.make("Potion of Full Healing"), AB.make("Potion of Full Mana"));
    if (lvl >= 14) witch.push(AB.make("Potion of Rejuvenation"));
    for (const [spell, [, , need]] of Object.entries(AB.SPELLS)) if (need <= lvl + 2 && rnd.random() < 0.6) witch.push(AB.make(`Book of ${spell}`));
    for (let k = 0; k < 4; k++) { let it = AB.randomDrop(lvl, rnd, 0, ["staff", "ring", "amulet"]); if (it.rarity === "rare") it = AB.make(it.base, it.ilvl, "magic", rnd); it.ident = true; witch.push(it); }
    this.shopStock = { smith, witch, healer: lvl >= 6 ? [AB.make("Potion of Healing"), AB.make("Potion of Full Healing")] : [AB.make("Potion of Healing")] };
  }
  populate() {
    const lv = this.level, rnd = new AB.Rng(`${this.seed}:${this.depth}:m${this.time.toFixed(0)}`), depth = this.depth, p = this.player;
    const floors = lv.floors().filter(([x, y]) => Math.hypot(x - p.x, y - p.y) > 8);
    if (lv.theme === "sanctum") {
      const [dx, dy] = lv.places.diablo; if (!this.flags.diablo_dead) this.monsters.push(new AB.Monster(dx + 0.5, dy + 0.5, "diablo", 50, rnd));
      const near = floors.filter(([x, y]) => Math.hypot(x - dx, y - dy) < 9); for (let k = 0; k < 4; k++) { const [fx, fy] = rnd.choice(near); this.monsters.push(new AB.Monster(fx + 0.5, fy + 0.5, "knight", 49, rnd)); }
      return;
    }
    const kinds = AB.THEME_MONSTERS[lv.theme];
    for (let k = 0; k < 9 + Math.floor(depth / 4) && floors.length; k++) {
      const [cx, cy] = rnd.choice(floors), kind = rnd.choice(kinds), n = kind === "fallen" ? rnd.randint(4, 7) : kind !== "pitlord" ? rnd.randint(2, 4) : rnd.randint(1, 2);
      for (let i = 0; i < n; i++) { let x, y, ok = false; for (let t = 0; t < 10; t++) { x = cx + rnd.randint(-2, 2); y = cy + rnd.randint(-2, 2); if (lv.floor(x, y)) { ok = true; break; } } if (ok) this.monsters.push(new AB.Monster(x + 0.5, y + 0.5, kind, depth + rnd.randint(0, 1), rnd)); }
    }
    if (depth >= 3) for (let k = rnd.randint(1, 2); k > 0; k--) { const [x, y] = rnd.choice(floors); this.monsters.push(new AB.Monster(x + 0.5, y + 0.5, rnd.choice(kinds), depth + 1, rnd, true)); }
    if (AB.BOSSES[depth]) { const [x, y] = AB.nearFree(lv, lv.down || rnd.choice(floors)), kind = { 5: "ghoul", 15: "skeleton", 25: "magma", 35: "knight", 45: "pitlord" }[depth]; this.monsters.push(new AB.Monster(x + 0.5, y + 0.5, kind, depth + 2, rnd, false, AB.BOSSES[depth])); this.say("You feel a terrible presence on this level...", "#FF8060"); }
    for (let k = rnd.randint(2, 4); k > 0; k--) { const [x, y] = rnd.choice(floors); this.objects.push(new AB.Obj("chest", x + 0.5, y + 0.5)); }
    const all = lv.floors(); for (let k = rnd.randint(6, 12); k > 0; k--) { const [x, y] = rnd.choice(all); if (!(lv.up && x === lv.up[0] && y === lv.up[1]) && !(lv.down && x === lv.down[0] && y === lv.down[1])) this.objects.push(new AB.Obj("barrel", x + 0.5, y + 0.5)); }
    if (rnd.random() < 0.75) { const [x, y] = rnd.choice(floors), [name, colour] = rnd.choice(AB.SHRINES); this.objects.push(new AB.Obj("shrine", x + 0.5, y + 0.5, { name, colour })); }
    for (let k = rnd.randint(2, 5); k > 0; k--) { const [x, y] = rnd.choice(floors); this.ground.push({ x: x + 0.5, y: y + 0.5, item: { base: "Gold", gold: rnd.randint(5, 20) * depth } }); }
  }
  takeStairs(o) { if (o.kind === "stairs_down") { if (this.depth < 50) this.enter(this.depth + 1, "up"); } else if (o.kind === "stairs_up") this.enter(this.depth === 1 ? 0 : this.depth - 1, "down"); }
  waystoneDepths() { const out = [1]; for (let d = 5; d <= 50; d += 5) if (d <= this.player.maxDepth) out.push(d); return out; }
  // ---- the player's commands ----
  moveTo(tx, ty) { const p = this.player; p.target = null; if (!this.level.floor(tx, ty)) return; p.path = AB.path(this.level, abTile(p), [tx, ty]); }
  attack(m) { this.player.target = m; this.player.path = []; }
  interact(t) { this.player.target = t; this.player.path = AB.path(this.level, abTile(this.player), [Math.floor(t.x), Math.floor(t.y)]) || []; }
  cast(tx, ty) {
    const p = this.player, spell = p.activeSpell; if (!spell || p.anim > 0 || this.dead) return;
    const cost = AB.SPELLS[spell][0]; if (p.mana < cost) { this.say("Not enough mana.", "#8090FF"); return; }
    if (spell === "Town Portal" && this.depth === 0) return;
    p.mana -= cost; p.anim = 0.45; p.pose = "cast"; p.path = []; const d = this.face(tx, ty);
    this.spell(spell, (p.spells[spell] || 1) + p.spellBonus, tx, ty, d); this.ev("cast", { spell });
  }
  face(tx, ty) { const p = this.player, dx = tx - p.x, dy = ty - p.y, f = AB.facingFor(dx, dy); if (f !== null) p.facing = f; return [dx, dy]; }
  useBelt(i) {
    const p = this.player, it = p.belt[i]; if (!it) return; this.drink(it); p.belt[i] = null;
    const j = p.inv.findIndex((x) => x && x.base === it.base); if (j >= 0) { p.belt[i] = Object.assign({}, p.inv[j], { qty: 1 }); p.inv[j].qty -= 1; if (p.inv[j].qty <= 0) p.inv[j] = null; }
  }
  drink(it) {
    const p = this.player, b = it.base;
    if (b.includes("Rejuvenation")) { p.hp = p.maxhp; p.mana = p.maxmana; } else if (b.includes("Full Healing")) p.hp = p.maxhp; else if (b.includes("Full Mana")) p.mana = p.maxmana; else if (b.includes("Healing")) p.hp = Math.min(p.maxhp, p.hp + p.maxhp * 0.4 + 10); else if (b.includes("Mana")) p.mana = Math.min(p.maxmana, p.mana + p.maxmana * 0.4 + 10);
    this.fx(b.includes("Mana") ? "mana" : "heal", { x: p.x, y: p.y, ttl: 0.6 }); this.ev("drink");
  }
  useItem(idx) {
    const p = this.player, it = p.inv[idx]; if (!it) return; const k = AB.kind(it);
    if (k === "potion") { this.drink(it); it.qty -= 1; if (it.qty <= 0) p.inv[idx] = null; }
    else if (it.base === "Scroll of Town Portal") { if (this.depth === 0) { this.say("You're already in town."); return; } this.openPortal(); p.takeOne(it.base); }
    else if (it.base === "Scroll of Identify") { const t = p.inv.find((x) => x && x.ident === false); if (!t) { this.say("Everything you carry is already identified."); return; } t.ident = true; p.takeOne(it.base); this.say(`Identified: ${AB.name(t)}`, AB.colour(t)); }
    else if (k === "book") { const spell = it.base.slice(8), need = Math.floor(AB.SPELLS[spell][2] / 2) + 10; if (p.mag < need) { this.say(`You need ${need} Magic to learn ${spell}.`, "#FF8080"); return; } p.spells[spell] = (p.spells[spell] || 0) + 1; if (!p.activeSpell) p.activeSpell = spell; p.inv[idx] = null; this.say(`You learn ${spell} (level ${p.spells[spell]}).`, "#80C0FF"); }
    else this.equipFrom(idx);
  }
  equipFrom(idx) {
    const p = this.player, it = p.inv[idx]; let s = it ? AB.slot(it) : null; if (!s) return false;
    if (!p.canEquip(it)) { this.say("You don't meet the requirements for that.", "#FF8080"); return false; }
    if (s === "ring") s = !p.equip.ring1 || p.equip.ring2 ? "ring1" : "ring2";
    const old = p.equip[s]; p.equip[s] = it; p.inv[idx] = old;
    if (s === "weapon" && AB.twoHanded(it) && p.equip.shield) { if (!p.addItem(p.equip.shield)) this.dropItem(p.equip.shield); p.equip.shield = null; }
    if (s === "shield" && p.equip.weapon && AB.twoHanded(p.equip.weapon)) { if (!p.addItem(p.equip.weapon)) this.dropItem(p.equip.weapon); p.equip.weapon = null; }
    p.recalc(); this.ev("equip"); return true;
  }
  unequip(slot) { const p = this.player, it = p.equip[slot]; if (it && p.addItem(it)) { p.equip[slot] = null; p.recalc(); } }
  dropItem(it) { const p = this.player; this.ground.push({ x: p.x + this.rnd.uniform(-0.4, 0.4), y: p.y + this.rnd.uniform(-0.4, 0.4), item: it }); }
  openPortal() { const p = this.player; this.portal = [this.depth, p.x + 0.8, p.y + 0.8]; this.objects = this.objects.filter((o) => o.kind !== "portal"); this.objects.push(new AB.Obj("portal", this.portal[1], this.portal[2])); this.say("A portal to town opens.", "#80C0FF"); this.fx("flash", { x: this.portal[1], y: this.portal[2], colour: "#80C0FF", ttl: 0.6 }); this.ev("portal"); }
  // ---- the frame ----
  update(dt) {
    this.time += dt; if (this.dead) return;
    const p = this.player;
    for (const k of Object.keys(p.buffs)) { p.buffs[k] -= dt; if (p.buffs[k] <= 0) { delete p.buffs[k]; p.recalc(); } }
    p.hp = Math.min(p.maxhp, p.hp + (p.regen + 0.15) * dt); p.mana = Math.min(p.maxmana, p.mana + (0.35 + p.mag / 200) * dt);
    p.cool = Math.max(0, p.cool - dt); p.hurt = Math.max(0, p.hurt - dt);
    if (p.anim > 0) { p.anim -= dt; if (p.hitPending && p.anim <= p.hitPending[0]) { const target = p.hitPending[1]; p.hitPending = null; this.playerStrike(target); } if (p.anim <= 0) p.pose = "stand"; }
    else this.playerAct(dt);
    this.explore();
    for (const m of this.monsters) { if (!m.dead) this.monster(m, dt); else m.anim += dt; }
    this.monsters = this.monsters.filter((m) => !m.dead || m.anim < 30);
    for (const ms of this.missiles) this.missile(ms, dt);
    this.missiles = this.missiles.filter((m) => !m.dead);
    for (const n of this.npcs) this.npc(n, dt);
    this.effects = this.effects.filter((e) => this.time - e.t0 < e.ttl);
    for (const g of this.ground.slice()) if (g.item.base === "Gold" && Math.hypot(g.x - p.x, g.y - p.y) < 0.7) { p.gold += g.item.gold; this.ground.splice(this.ground.indexOf(g), 1); this.fx("text", { x: g.x, y: g.y, text: `${g.item.gold} gold`, colour: "#F8D040", ttl: 1 }); this.ev("gold"); }
  }
  explore() { const p = this.player, r = p.light, px = Math.floor(p.x), py = Math.floor(p.y); for (let y = py - r; y <= py + r; y++) for (let x = px - r; x <= px + r; x++) if ((x - px) ** 2 + (y - py) ** 2 <= r * r) this.explored.add(K2(x, y)); }
  walk(a, dt, speed) {
    if (!a.path.length) return false;
    const tx = a.path[0][0] + 0.5, ty = a.path[0][1] + 0.5, dx = tx - a.x, dy = ty - a.y, d = Math.hypot(dx, dy), step = speed * dt;
    if (d <= step) { a.x = tx; a.y = ty; a.path.shift(); } else { a.x += (dx / d) * step; a.y += (dy / d) * step; }
    const f = AB.facingFor(dx, dy); if (f !== null) a.facing = f; a.pose = "walk"; a.phase += dt * speed * 2.2; return true;
  }
  playerAct(dt) {
    const p = this.player, t = p.target;
    if (t) {
      if (t.isMonster) {
        if (t.dead) p.target = null;
        else {
          const d = AB.dist(p, t);
          if (p.ranged && d <= 9 && this.los(p, t)) { this.playerSwing(t); return; }
          if (!p.ranged && d <= 1.45) { this.playerSwing(t); return; }
          p.repathT -= dt; if (!p.path.length || p.repathT <= 0) { const np = AB.path(this.level, abTile(p), abTile(t)).slice(0, -1); if (np.length) p.path = np; p.repathT = 0.35; }
        }
      } else if (Math.hypot(t.x - p.x, t.y - p.y) <= 1.3) { p.target = null; p.path = []; this.use(t); return; }
    }
    if (!this.walk(p, dt, p.speed)) p.pose = "stand";
  }
  playerSwing(m) {
    const p = this.player; p.path = []; if (p.cool > 0) { p.pose = "stand"; return; }
    this.face(m.x, m.y); p.cool = p.swing; p.anim = Math.min(0.45, p.swing * 0.5); p.pose = "attack"; p.phase = 0;
    if (p.ranged) { this.missiles.push(new AB.Missile("arrow", p.x, p.y, m.x - p.x, m.y - p.y, 13, this.rollDamage(), "player", "phys", 0.4, 1.2)); this.ev("shoot"); }
    else { p.hitPending = [p.anim * 0.4, m]; this.ev("swing"); }
  }
  rollDamage() { const p = this.player; return this.rnd.uniform(...p.dmg) + p.elem; }
  playerStrike(m) { const p = this.player; if (m.dead || AB.dist(p, m) > 1.8) return; if (this.rnd.uniform(0, 100) > Math.max(10, Math.min(95, p.toHit - m.ac * 0.5))) { this.fx("text", { x: m.x, y: m.y, text: "miss", colour: "#A0A0A0", ttl: 0.6 }); this.ev("miss"); return; } this.hurtMonster(m, this.rollDamage(), "phys"); }
  hurtMonster(m, dmg, elem = "phys") {
    if (m.dead) return; if (m.res[elem] !== undefined) dmg *= 1 - m.res[elem] / 100;
    m.hp -= dmg; m.hurt = 0.18; m.state = "chase"; m.seen = true; const p = this.player;
    if (p.leech && elem === "phys") p.hp = Math.min(p.maxhp, p.hp + (dmg * p.leech) / 100);
    this.fx("text", { x: m.x, y: m.y, text: String(Math.floor(dmg)), colour: elem === "phys" ? "#FFFFFF" : "#FFB060", ttl: 0.7 }); this.ev("hit", { boss: m.boss });
    if (m.kind === "fallen" && m.hp < m.maxhp * 0.35) m.flee = 3;
    if (m.hp <= 0) this.kill(m);
  }
  kill(m) {
    m.dead = true; m.anim = 0; m.pose = "dead"; const p = this.player; p.xp += m.xp; this.xpGained = (this.xpGained || 0) + m.xp; this.drops(m); this.ev("kill", { boss: m.boss, kind: m.kind });
    if (m.kind === "diablo") { this.flags.diablo_dead = true; this.wonAt = this.time; this.say("Vorthak the Undying is undone!", "#F0C060"); for (const m2 of this.monsters) if (!m2.dead) this.kill(m2); }
    else if (m.boss) this.say(`${m.name} is dead!`, "#F0C060");
    while (p.xp >= p.nextLevelXp()) { p.xp -= p.nextLevelXp(); p.level += 1; p.points += 5; p.recalc(); p.hp = p.maxhp; p.mana = p.maxmana; this.say(`You have reached level ${p.level}! (5 points to spend - press C)`, "#F0C060"); this.fx("level", { x: p.x, y: p.y, ttl: 1.2 }); this.ev("level"); }
  }
  drops(m) {
    const rnd = this.rnd, ilvl = Math.max(1, m.mlevel), n = m.boss ? 3 : m.champion ? 1 : rnd.random() < 0.16 ? 1 : 0;
    for (let i = 0; i < n; i++) { let it = AB.randomDrop(ilvl + (m.boss ? 2 : 0), rnd, m.boss || m.champion ? 0.6 : 0); if ((m.boss || m.champion) && it.rarity === "normal") it = AB.make(it.base, it.ilvl, m.boss && i === 0 ? "rare" : "magic", rnd); this.drop(m.x, m.y, it); }
    if (rnd.random() < (m.boss ? 1 : 0.4)) this.drop(m.x, m.y, { base: "Gold", gold: Math.floor(rnd.randint(3, 12) * ilvl * (m.boss ? 5 : 1)) });
    if (rnd.random() < 0.12) this.drop(m.x, m.y, AB.randomSupply(ilvl, rnd));
  }
  drop(x, y, item) { let nx = x, ny = y; for (let k = 0; k < 12; k++) { const tx = x + this.rnd.uniform(-0.9, 0.9), ty = y + this.rnd.uniform(-0.9, 0.9); if (this.level.walkable(tx, ty)) { nx = tx; ny = ty; break; } } this.ground.push({ x: nx, y: ny, item }); }
  // ---- using things ----
  use(t) {
    const p = this.player;
    if (t.item) { if (this.ground.includes(t)) { if (t.item.base === "Gold") { p.gold += t.item.gold; this.ground.splice(this.ground.indexOf(t), 1); this.ev("gold"); } else if ((AB.kind(t.item) === "potion" && p.beltAdd(t.item)) || p.addItem(t.item)) { this.ground.splice(this.ground.indexOf(t), 1); this.ev("take", { item: t.item }); } else this.say("Your pack is full.", "#FF8080"); } return; }
    if (t.isNpc) { this.talkTo = t; this.ev("talk"); return; }
    if (!t.isObj) return;
    if (t.kind === "stairs_down" || t.kind === "stairs_up") { this.takeStairs(t); this.ev("stairs"); }
    else if (t.kind === "portal") { if (this.depth === 0) { const d = this.portal[0]; this.enter(d, "portal"); this.portal = null; this.objects = this.objects.filter((o) => o.kind !== "portal"); } else this.enter(0, "portal"); this.ev("portal"); }
    else if (t.kind === "red_portal") { this.homeWanted = true; this.ev("portal"); }   // (the way back to the Keep-yard: the window takes it from here)
    else if (t.kind === "waystone") this.waystoneOpen = true;
    else if (t.kind === "chest" && !t.opened) { t.opened = true; this.ev("chest"); for (let k = this.rnd.randint(1, 3); k > 0; k--) { if (this.rnd.random() < 0.6) this.drop(t.x, t.y, AB.randomDrop(this.depth, this.rnd)); else this.drop(t.x, t.y, { base: "Gold", gold: this.rnd.randint(8, 25) * this.depth }); } }
    else if (t.kind === "barrel" && !t.opened) {
      t.opened = true; const r = this.rnd.random(); this.ev("barrel");
      if (["hell", "abyss", "caves"].includes(this.level.theme) && r < 0.15) { this.fx("explosion", { x: t.x, y: t.y, r: 1.6, colour: "#FF8020", ttl: 0.5 }); this.ev("boom"); for (const m of this.monsters) if (!m.dead && Math.hypot(m.x - t.x, m.y - t.y) < 1.8) this.hurtMonster(m, 6 * this.depth, "fire"); if (Math.hypot(p.x - t.x, p.y - t.y) < 1.8) this.hurtPlayer(4 * this.depth, "fire", "An exploding barrel"); }
      else if (r < 0.45) this.drop(t.x, t.y, { base: "Gold", gold: this.rnd.randint(2, 10) * this.depth });
      else if (r < 0.6) this.drop(t.x, t.y, AB.randomSupply(this.depth, this.rnd));
    } else if (t.kind === "shrine" && !t.opened) { t.opened = true; this.shrine(t); }
  }
  shrine(t) {
    const p = this.player, name = t.name;
    let msg = { "Glimmering Shrine": "Your items glimmer - you know their secrets.", "Divine Shrine": "Divine light restores you.", "Eerie Shrine": "You feel your mind sharpen. (+2 Magic)", "Abandoned Shrine": "You feel more agile. (+2 Dexterity)", "Creepy Shrine": "You feel stronger. (+2 Strength)", "Quiet Shrine": "You feel hardier. (+2 Vitality)",
      "Hidden Shrine": "Your armor shimmers. (+50% armor for two minutes)", "Ornate Shrine": "Arcane power fills you. (spells hit harder for two minutes)", "Gloomy Shrine": "Your weapon feels heavier. (+30% damage for two minutes)", "Fascinating Shrine": "Your magic grows deeper." }[name];
    if (name === "Glimmering Shrine") for (const it of p.inv) { if (it) it.ident = true; }
    else if (name === "Divine Shrine") { p.hp = p.maxhp; p.mana = p.maxmana; }
    else if (["Eerie Shrine", "Abandoned Shrine", "Creepy Shrine", "Quiet Shrine"].includes(name)) p.base[{ "Eerie Shrine": "mag", "Abandoned Shrine": "dex", "Creepy Shrine": "str", "Quiet Shrine": "vit" }[name]] += 2;
    else if (["Hidden Shrine", "Ornate Shrine", "Gloomy Shrine"].includes(name)) p.buffs[name] = 120;
    else if (name === "Fascinating Shrine") { const ks = Object.keys(p.spells); if (ks.length) { const s = this.rnd.choice(ks); p.spells[s] += 1; msg = `Your magic grows deeper. (${s} level ${p.spells[s]})`; } else { p.base.mag += 3; msg = "Your mind opens. (+3 Magic)"; } }
    p.recalc(); this.say(`${name}: ${msg}`, t.colour); this.fx("flash", { x: t.x, y: t.y, colour: t.colour, ttl: 0.8 }); this.ev("shrine");
  }
  // ---- spells ----
  spell(spell, lvl, tx, ty, d) {
    const p = this.player, power = (1 + 0.25 * (lvl - 1)) * (p.buffs["Ornate Shrine"] ? 1.5 : 1), mag = p.mag, R = this.rnd;
    if (spell === "Firebolt") this.missiles.push(new AB.Missile("firebolt", p.x, p.y, d[0], d[1], 11, (R.uniform(3, 9) + mag / 4) * power, "player", "fire", 0.35, 1.4));
    else if (spell === "Healing") { p.hp = Math.min(p.maxhp, p.hp + (15 + p.level * 3 + mag / 3) * power); this.fx("heal", { x: p.x, y: p.y, ttl: 0.7 }); }
    else if (spell === "Lightning") this.bolt(p.x, p.y, d, 9, (R.uniform(4, 16) + mag / 3) * power, "player");
    else if (spell === "Fireball") this.missiles.push(new AB.Missile("fireball", p.x, p.y, d[0], d[1], 9, (R.uniform(10, 24) + mag / 2.5) * power, "player", "fire", 0.5, 1.6));
    else if (spell === "Chain Lightning") this.chain((R.uniform(8, 22) + mag / 2.5) * power, tx, ty);
    else if (spell === "Nova") { const dmg = (R.uniform(12, 26) + mag / 2) * power; this.fx("nova", { x: p.x, y: p.y, r: 5, colour: "#A0C8FF", ttl: 0.5 }); for (const m of this.monsters) if (!m.dead && AB.dist(m, p) < 5.2) this.hurtMonster(m, dmg, "light"); }
    else if (spell === "Inferno") { const n = Math.hypot(...d) || 1; for (let i = 0; i < 4; i++) { const fx = p.x + (d[0] / n) * (1 + i * 0.9), fy = p.y + (d[1] / n) * (1 + i * 0.9); this.fx("flame", { x: fx, y: fy, ttl: 0.5 }); for (const m of this.monsters) if (!m.dead && Math.hypot(m.x - fx, m.y - fy) < 0.9) this.hurtMonster(m, (R.uniform(4, 10) + mag / 5) * power, "fire"); } }
    else if (spell === "Teleport") { if (this.level.walkable(tx, ty) && this.explored.has(K2(Math.floor(tx), Math.floor(ty)))) { this.fx("flash", { x: p.x, y: p.y, colour: "#C080FF", ttl: 0.4 }); p.x = Math.floor(tx) + 0.5; p.y = Math.floor(ty) + 0.5; p.path = []; } }
    else if (spell === "Town Portal") this.openPortal();
  }
  bolt(x, y, d, length, dmg, owner, elem = "light", colour = "#C0E0FF") {
    const n = Math.hypot(...d) || 1, ux = d[0] / n, uy = d[1] / n, pts = [[x, y]], hit = new Set();
    for (let i = 1; i <= Math.floor(length * 3); i++) {
      const cx = x + (ux * i) / 3, cy = y + (uy * i) / 3; if (this.level.wall(Math.floor(cx), Math.floor(cy))) break;
      pts.push([cx + this.rnd.uniform(-0.15, 0.15), cy + this.rnd.uniform(-0.15, 0.15)]);
      if (owner === "player") { for (const m of this.monsters) if (!m.dead && !hit.has(m) && Math.hypot(m.x - cx, m.y - cy) < 0.6) { hit.add(m); this.hurtMonster(m, dmg, elem); } }
      else if (Math.hypot(this.player.x - cx, this.player.y - cy) < 0.5 && !hit.has("p")) { hit.add("p"); this.hurtPlayer(dmg, elem, "Lightning"); }
    }
    this.fx("bolt", { pts, colour, ttl: 0.25 }); this.ev("zap");
  }
  chain(dmg, tx, ty) {
    const p = this.player, live = this.monsters.filter((m) => !m.dead && AB.dist(m, p) < 10 && this.los(p, m)); if (!live.length) return;
    let cur = live.reduce((a, m) => (Math.hypot(m.x - tx, m.y - ty) < Math.hypot(a.x - tx, a.y - ty) ? m : a)); const pts = [[p.x, p.y]], done = [];
    for (let k = 0; k < 4; k++) { pts.push([cur.x, cur.y]); done.push(cur); this.hurtMonster(cur, dmg, "light"); const nxt = live.filter((m) => !done.includes(m) && !m.dead && AB.dist(m, cur) < 5); if (!nxt.length) break; const c0 = cur; cur = nxt.reduce((a, m) => (AB.dist(m, c0) < AB.dist(a, c0) ? m : a)); }
    this.fx("bolt", { pts, colour: "#D0E8FF", ttl: 0.3 }); this.ev("zap");
  }
  // ---- the monsters ----
  los(a, b) { const n = Math.floor(Math.max(Math.abs(b.x - a.x), Math.abs(b.y - a.y)) * 3) + 1; for (let i = 1; i < n; i++) if (this.level.wall(Math.floor(a.x + ((b.x - a.x) * i) / n), Math.floor(a.y + ((b.y - a.y) * i) / n))) return false; return true; }
  monster(m, dt) {
    const p = this.player; m.hurt = Math.max(0, m.hurt - dt); m.cool = Math.max(0, m.cool - dt); m.special = Math.max(0, m.special - dt); m.flee = Math.max(0, m.flee - dt);
    if (m.anim > 0) { m.anim -= dt; if (m.anim <= 0) m.pose = "stand"; return; }
    const d = AB.dist(m, p); if (d > 18) return;
    if (m.state === "idle") {
      if (d < (m.ai !== "stealth" ? 7 : 4) && this.los(m, p)) { m.state = "chase"; m.seen = true; if (m.boss) { this.say(`${m.name}: ${m.name.includes("Flesher") ? "Something warm, at last..." : m.kind === "diablo" ? "Kneel, little candle. I have outlasted brighter." : "You dare enter my domain?"}`, "#FF8060"); this.ev("bossspeaks"); } }
      else return;
    }
    if (m.flee > 0) { m.path = []; this.stepAway(m, p, dt); return; }
    if (m.kind === "diablo") { this.diablo(m, d, dt); return; }
    if ((m.ai === "ranged" || m.ai === "caster") && d < 8 && this.los(m, p)) {
      if (d < 3 && m.ai === "ranged") { this.stepAway(m, p, dt); return; }
      if (m.cool <= 0) {
        m.cool = m.ai === "ranged" ? 2.2 : 3; m.anim = 0.4; m.pose = m.ai === "ranged" ? "attack" : "cast"; const f = AB.facingFor(p.x - m.x, p.y - m.y); if (f !== null) m.facing = f;
        const kind = m.missile, dmg = this.rnd.uniform(...m.dmg) * (kind === "fireball" ? 1.3 : 1), elem = kind === "firebolt" || kind === "fireball" ? "fire" : "phys";
        this.missiles.push(new AB.Missile(kind, m.x, m.y, p.x - m.x, p.y - m.y, kind !== "arrow" ? 8 : 11, dmg, "monster", elem, 0.45, 1.6)); this.ev("foeshoot", { kind });
      }
      if (m.ai === "caster" && d > 2) return;
    }
    if (d <= 1.25 && m.ai !== "ranged") { m.path = []; if (m.cool <= 0) { m.cool = 1.3; m.anim = 0.4; m.pose = "attack"; const f = AB.facingFor(p.x - m.x, p.y - m.y); if (f !== null) m.facing = f; this.monsterHit(m); } return; }
    m.repath -= dt;
    if (m.ai === "erratic") { m.zig += dt * 3; const ang = Math.atan2(p.y - m.y, p.x - m.x) + Math.sin(m.zig) * 1.1, nx = m.x + Math.cos(ang) * m.speed * dt, ny = m.y + Math.sin(ang) * m.speed * dt; if (this.level.walkable(nx, ny)) { m.x = nx; m.y = ny; } m.pose = "walk"; m.phase += dt * 6; return; }
    if (this.los(m, p) && d < 6) { m.path = []; this.stepToward(m, p.x, p.y, dt); }
    else { if (m.repath <= 0 || !m.path.length) { m.repath = 0.8; m.path = AB.path(this.level, abTile(m), abTile(p), null, 900).slice(0, -1); } if (!this.walk(m, dt, m.speed)) m.pose = "stand"; }
    this.separate(m);
  }
  stepToward(m, tx, ty, dt) { const dx = tx - m.x, dy = ty - m.y, d = Math.hypot(dx, dy) || 1, nx = m.x + (dx / d) * m.speed * dt, ny = m.y + (dy / d) * m.speed * dt; if (this.level.walkable(nx, m.y)) m.x = nx; if (this.level.walkable(m.x, ny)) m.y = ny; const f = AB.facingFor(dx, dy); if (f !== null) m.facing = f; m.pose = "walk"; m.phase += dt * m.speed * 2.2; }
  stepAway(m, p, dt) { this.stepToward(m, m.x * 2 - p.x, m.y * 2 - p.y, dt); }
  separate(m) { for (const o of this.monsters) if (o !== m && !o.dead) { const dx = m.x - o.x, dy = m.y - o.y, d = Math.hypot(dx, dy); if (d > 0 && d < 0.6) { const push = (0.6 - d) * 0.5, nx = m.x + (dx / d) * push, ny = m.y + (dy / d) * push; if (this.level.walkable(nx, ny)) { m.x = nx; m.y = ny; } } } }
  monsterHit(m) {
    const p = this.player; if (this.rnd.uniform(0, 100) > Math.max(10, Math.min(95, m.toHit - p.ac * 0.25))) { this.ev("foemiss"); return; }
    if (p.block && this.rnd.uniform(0, 100) < p.block) { this.fx("text", { x: p.x, y: p.y, text: "blocked", colour: "#C0C0FF", ttl: 0.6 }); this.ev("block"); return; }
    this.hurtPlayer(this.rnd.uniform(...m.dmg), "phys", m.name); if (p.thorns) this.hurtMonster(m, p.thorns, "phys");
  }
  hurtPlayer(dmg, elem, source) {
    const p = this.player; if (elem === "fire") dmg *= 1 - p.resFire / 100; else if (elem === "light") dmg *= 1 - p.resLight / 100;
    p.hp -= dmg; p.hurt = 0.25; this.ev("hurt", { dmg });
    if (p.hp <= 0 && !this.dead) { p.hp = 0; this.dead = true; p.pose = "dead"; this.say(`You have been slain by ${source}.`, "#FF4040"); this.ev("dead"); }
  }
  diablo(m, d, dt) {
    const p = this.player;
    if (m.special <= 0 && d < 9) {
      m.special = 7; m.anim = 0.6; m.pose = "cast";
      if (this.rnd.random() < 0.5) { this.fx("nova", { x: m.x, y: m.y, r: 6, colour: "#FF6020", ttl: 0.6 }); this.ev("boom"); if (d < 6) this.hurtPlayer(this.rnd.uniform(40, 80), "fire", "Vorthak's firestorm"); }
      else for (const spread of [-0.3, 0, 0.3]) { const ang = Math.atan2(p.y - m.y, p.x - m.x) + spread; this.bolt(m.x, m.y, [Math.cos(ang), Math.sin(ang)], 10, this.rnd.uniform(35, 70), "monster", "light", "#FF4040"); }
      if (m.hp < m.maxhp * 0.5 && !m.summoned) { m.summoned = true; for (let k = 0; k < 3; k++) this.monsters.push(new AB.Monster(m.x + this.rnd.uniform(-2, 2), m.y + this.rnd.uniform(-2, 2), "knight", 50, this.rnd, true)); this.say("Vorthak calls up his knights!", "#FF6040"); }
      return;
    }
    if (d <= 1.8) { if (m.cool <= 0) { m.cool = 1.2; m.anim = 0.45; m.pose = "attack"; this.monsterHit(m); } return; }
    this.stepToward(m, p.x, p.y, dt);
  }
  missile(ms, dt) {
    ms.life -= dt;
    if (ms.life <= 0) { ms.dead = true; if (ms.kind === "fireball") this.explode(ms); return; }
    ms.x += ms.vx * dt; ms.y += ms.vy * dt;
    if (this.level.wall(Math.floor(ms.x), Math.floor(ms.y))) { ms.dead = true; if (ms.kind === "fireball") this.explode(ms); return; }
    if (ms.owner === "player") {
      for (const m of this.monsters) if (!m.dead && !ms.hit.has(m) && Math.hypot(m.x - ms.x, m.y - ms.y) < ms.radius + 0.25) {
        if (ms.kind === "fireball") { ms.dead = true; this.explode(ms); return; }
        const chance = ms.kind === "arrow" ? Math.max(10, Math.min(95, this.player.toHit - m.ac * 0.5)) : 100; ms.hit.add(m);
        if (this.rnd.uniform(0, 100) <= chance) this.hurtMonster(m, ms.dmg, ms.elem); ms.dead = true; return;
      }
    } else {
      const p = this.player;
      if (Math.hypot(p.x - ms.x, p.y - ms.y) < ms.radius + 0.2) {
        ms.dead = true; if (ms.kind === "fireball") { this.explode(ms); return; }
        if (p.block && ms.kind === "arrow" && this.rnd.uniform(0, 100) < p.block) { this.fx("text", { x: p.x, y: p.y, text: "blocked", colour: "#C0C0FF", ttl: 0.6 }); return; }
        this.hurtPlayer(ms.dmg, ms.elem, "a missile");
      }
    }
  }
  explode(ms) { this.fx("explosion", { x: ms.x, y: ms.y, r: 1.5, colour: "#FF8020", ttl: 0.45 }); this.ev("boom"); if (ms.owner === "player") { for (const m of this.monsters) if (!m.dead && Math.hypot(m.x - ms.x, m.y - ms.y) < 1.6) this.hurtMonster(m, ms.dmg, "fire"); } else if (Math.hypot(this.player.x - ms.x, this.player.y - ms.y) < 1.5) this.hurtPlayer(ms.dmg, "fire", "a fireball"); }
  npc(n, dt) { n.phase += dt; if (n.path.length) { this.walk(n, dt, 1); return; } n.pose = "stand"; n.wait -= dt; if (n.wait <= 0) { n.wait = this.rnd.uniform(3, 8); const [hx, hy] = n.home; n.path = AB.path(this.level, abTile(n), [Math.floor(hx + this.rnd.randint(-2, 2)), Math.floor(hy + this.rnd.randint(-1, 2))], null, 200); } }
  // ---- the town's services ----
  heal() { const p = this.player; p.hp = p.maxhp; p.mana = p.maxmana; }
  identifyAll() { const p = this.player, todo = p.inv.concat(Object.values(p.equip)).filter((it) => it && it.ident === false), cost = 100 * todo.length; if (!todo.length) return "You have nothing that needs identifying."; if (p.gold < cost) return `That will cost ${cost} gold, friend - and you have ${p.gold}.`; p.gold -= cost; for (const it of todo) it.ident = true; return `Let me see... (${todo.length} item${todo.length !== 1 ? "s" : ""} identified for ${cost} gold)`; }
  buy(shop, idx) { const p = this.player, stock = this.shopStock[shop], it = stock[idx], price = AB.buyPrice(it); if (p.gold < price) return "You can't afford that."; if (!((AB.kind(it) === "potion" && p.beltAdd(Object.assign({}, it))) || p.addItem(JSON.parse(JSON.stringify(it))))) return "Your pack is full."; p.gold -= price; if (it.rarity !== "supply") stock.splice(idx, 1); this.ev("buy"); return null; }
  sell(idx) { const p = this.player, it = p.inv[idx]; if (!it) return 0; const price = it.rarity !== "supply" ? AB.sellPrice(it) : Math.max(1, Math.floor(AB.SUPPLIES[it.base][1] / 4)); if (it.rarity === "supply" && it.qty > 1) it.qty -= 1; else p.inv[idx] = null; p.gold += price; this.ev("sell"); return price; }
  // after death: wake in town with half the gold
  revive() { const p = this.player, lost = Math.floor(p.gold / 2); p.gold -= lost; this.dead = false; p.hp = p.maxhp; p.mana = p.maxmana; p.pose = "stand"; this.portal = null; this.enter(0); this.say(`You wake in Haven. (${lost} gold was lost in the dark.)`, "#FF8080"); }
};
