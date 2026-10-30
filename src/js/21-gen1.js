"use strict";
// Generator 1: the floors of every run begun before v2.1, frozen. A seed must make the same floor in every version,
// so this file is never edited again (tests/fixtures/gen1.json holds its fingerprints for twenty-eight seeds, and the
// tests check them). New work goes in 22-gen2.js. The hash-furnished things - affixes, uniques, events, strongboxes,
// the peddler, rivals, hazards - are laid on afterwards by CM.furnish (20-world.js), for every generator alike.
{
const key = (x, y) => `${x},${y}`;
const unkey = (k) => k.split(",").map(Number);
CM.generators = CM.generators || {};
CM.generators[1] = function (number, seed) {
  const rnd = new CM.Random(CM.hashSeed(`${seed}:floor:${number}`));
  const size = Math.min(17 + Math.floor(number / 4) * 2, 27);
  const grid = [];
  for (let y = 0; y < size; y++) grid.push(new Array(size).fill(1));
  const special = CM.specialFor(number, seed);
  const floor = { number, grid, pos: [1, 1], facing: 2, things: {}, features: {}, dark: [], seen: [], rooms: [], decor: [], special };
  const rooms = [];                            // {x0, y0, x1, y1 (interior, inclusive), template?, entrances: [[x,y,kind]]}
  const taken = (x0, y0, x1, y1) => rooms.some((r) => x0 <= r.x1 + 2 && x1 >= r.x0 - 2 && y0 <= r.y1 + 2 && y1 >= r.y0 - 2);
  const carve = (x0, y0, x1, y1) => { for (let y = y0; y <= y1; y++) for (let x = x0; x <= x1; x++) grid[y][x] = 0; };

  // set pieces first (one or two, where they fit), then ordinary rooms
  const guardian = CM.guardianFor(number), lair = guardian ? CM.GUARDIANS[guardian].lair : null;
  const wanted = CM.TEMPLATES.filter((t) => number >= t.min && !((number === CM.LAST_FLOOR || number === CM.BOTTOM) && t.name === "Pit Room"));
  rnd.shuffle(wanted);
  const chosen = special === "maze" ? [] : wanted.slice(0, number >= 6 ? 2 : 1);
  if (lair) chosen.unshift(lair);                                   // (the guardian's lair first, and away from the top left, where the party starts)
  for (const tpl of chosen) {
    const h = tpl.rows.length - 2, w = tpl.rows[0].length - 2;
    const spots = [];
    if (tpl === lair) {
      for (let i = 0; i <= Math.floor((size - 6 - w) / 2); i++) for (let j = 0; j <= Math.floor((size - 6 - h) / 2); j++) spots.push([3 + 2 * i, 3 + 2 * j]);
      const reach = Math.max(...spots.map(([x, y]) => x + y));
      spots.splice(0, spots.length, ...spots.filter(([x, y]) => x + y >= reach * 0.6));
    }
    for (let tries = 0; tries < 40; tries++) {
      const [x0, y0] = tpl === lair ? rnd.pick(spots) : [3 + 2 * rnd.int(0, Math.floor((size - 6 - w) / 2)), 3 + 2 * rnd.int(0, Math.floor((size - 6 - h) / 2))];
      const x1 = x0 + w - 1, y1 = y0 + h - 1;
      if (x1 > size - 4 || y1 > size - 4 || taken(x0, y0, x1, y1)) continue;         // (room for the maze beyond every entrance)
      const room = { x0, y0, x1, y1, template: tpl, entrances: [], fill: [], pillars: [] };
      let fits = true;
      tpl.rows.forEach((row, ry) => [...row].forEach((c, rx) => {
        const x = x0 - 1 + rx, y = y0 - 1 + ry;
        const onRing = ry === 0 || ry === tpl.rows.length - 1 || rx === 0 || rx === row.length - 1;
        if ("DLGS".includes(c)) {
          const onSide = ry === 0 || ry === tpl.rows.length - 1;
          if ((onSide && x % 2 === 0) || (!onSide && y % 2 === 0)) fits = false;      // (the maze won't come up to it)
          room.entrances.push([x, y, c]);
        } else if (c === "#" && !onRing) room.pillars.push([x, y]);                  // (a pillar inside: on even coordinates, where the maze never goes)
        else if (c !== "#" && c !== "W") room.fill.push([x, y, c]);
      }));
      if (!fits) continue;
      carve(x0, y0, x1, y1);
      for (const [px, py] of room.pillars) grid[py][px] = 1;
      rooms.push(room);
      break;
    }
  }
  const roomTries = special === "maze" ? 2 : 14 + number;
  for (let i = 0; i < roomTries; i++) {
    const w = special === "maze" ? 3 : 3 + 2 * rnd.int(0, 1 + Math.floor(number / 7)), h = special === "maze" ? 3 : 3 + 2 * rnd.int(0, 1);
    const x0 = 1 + 2 * rnd.int(0, Math.floor((size - 2 - w) / 2)), y0 = 1 + 2 * rnd.int(0, Math.floor((size - 2 - h) / 2));
    const x1 = x0 + w - 1, y1 = y0 + h - 1;
    if (x1 >= size - 1 || y1 >= size - 1 || taken(x0, y0, x1, y1)) continue;
    carve(x0, y0, x1, y1);
    rooms.push({ x0, y0, x1, y1, entrances: [], fill: [] });
  }

  // the maze between the rooms
  for (let sy = 1; sy < size - 1; sy += 2) for (let sx = 1; sx < size - 1; sx += 2) {
    if (grid[sy][sx] !== 1) continue;
    const stack = [[sx, sy]];
    grid[sy][sx] = 0;
    while (stack.length) {
      const [x, y] = stack[stack.length - 1];
      const options = CM.DIRS.filter(([dx, dy]) => x + dx * 2 > 0 && x + dx * 2 < size - 1 && y + dy * 2 > 0 && y + dy * 2 < size - 1
        && grid[y + dy * 2][x + dx * 2] === 1 && grid[y + dy][x + dx] === 1);
      if (!options.length) { stack.pop(); continue; }
      const [dx, dy] = rnd.pick(options);
      grid[y + dy][x + dx] = 0;
      grid[y + dy * 2][x + dx * 2] = 0;
      stack.push([x + dx * 2, y + dy * 2]);
    }
  }

  // join the regions: one way between each pair, and a few more for the loops
  const region = new Map();
  let regions = 0;
  for (let y = 0; y < size; y++) for (let x = 0; x < size; x++) {
    if (grid[y][x] !== 0 || region.has(key(x, y))) continue;
    const id = regions++, queue = [[x, y]];
    region.set(key(x, y), id);
    for (let i = 0; i < queue.length; i++) {
      for (const [dx, dy] of CM.DIRS) {
        const nx = queue[i][0] + dx, ny = queue[i][1] + dy;
        if (ny > 0 && ny < size && nx > 0 && nx < size && grid[ny][nx] === 0 && !region.has(key(nx, ny))) { region.set(key(nx, ny), id); queue.push([nx, ny]); }
      }
    }
  }
  const templateWall = new Set(), templateDoor = new Map();
  for (const r of rooms) if (r.template) {
    for (let y = r.y0 - 1; y <= r.y1 + 1; y++) for (let x = r.x0 - 1; x <= r.x1 + 1; x++) templateWall.add(key(x, y));
    for (const [x, y, c] of r.entrances) templateDoor.set(key(x, y), c);
  }
  let connectors = [];
  for (let y = 1; y < size - 1; y++) for (let x = 1; x < size - 1; x++) {
    if (grid[y][x] !== 1) continue;
    const k = key(x, y);
    if (templateWall.has(k) && !templateDoor.has(k)) continue;
    const a = region.get(key(x - 1, y)), b = region.get(key(x + 1, y)), c = region.get(key(x, y - 1)), d = region.get(key(x, y + 1));
    if (a !== undefined && b !== undefined && a !== b && c === undefined && d === undefined) connectors.push([x, y, a, b]);
    else if (c !== undefined && d !== undefined && c !== d && a === undefined && b === undefined) connectors.push([x, y, c, d]);
  }
  const merged = new Map();
  const find = (id) => { while (merged.has(id)) id = merged.get(id); return id; };
  const loops = [], doorways = [];
  rnd.shuffle(connectors);
  connectors.sort((p, q) => (templateDoor.has(key(q[0], q[1])) ? 1 : 0) - (templateDoor.has(key(p[0], p[1])) ? 1 : 0));   // (set pieces first)
  for (const [x, y, a, b] of connectors) {
    const ra = find(a), rb = find(b);
    const k = key(x, y);
    if (ra !== rb) {
      grid[y][x] = 0;
      merged.set(rb, ra);
      doorways.push([x, y]);
      if (templateDoor.has(k)) floor.features[k] = { type: { D: "door", L: "door", G: "gate", S: "secret" }[templateDoor.get(k)], open: false };
    } else if (!templateDoor.has(k) && rnd.chance(0.06)
               && ![...doorways, ...loops].some(([ox, oy]) => Math.abs(ox - x) + Math.abs(oy - y) <= 2)) {
      loops.push([x, y]);                     // (a second way round: open, or a secret door - not beside another way)
    }
  }
  for (const [x, y] of loops) {
    if (rnd.chance(0.5) && number >= 2) { floor.features[key(x, y)] = { type: "secret", found: false }; }
    else { grid[y][x] = 0; doorways.push([x, y]); }
  }
  // template entrances: locked, gated, secret - as the template says
  for (const r of rooms) if (r.template) for (const [x, y, c] of r.entrances) {
    const f = floor.features[key(x, y)];
    if (!f) continue;
    if (c === "L") f.locked = true;
    if (c === "S") { grid[y][x] = 1; f.found = false; delete f.open; }
  }

  // trim the dead ends, most of them (a corridor that ends at a secret door isn't one: the door is the point of it)
  const leadsOn = (x, y) => grid[y][x] === 0 || (floor.features[key(x, y)] || {}).type === "secret";
  const deadEnds = () => {
    const out = [];
    for (let y = 1; y < size - 1; y++) for (let x = 1; x < size - 1; x++) {
      if (grid[y][x] === 0 && !templateWall.has(key(x, y)) && CM.DIRS.filter(([dx, dy]) => leadsOn(x + dx, y + dy)).length === 1) out.push([x, y]);
    }
    return out;
  };
  const keepEnds = special === "maze" ? 9999 : 3 + Math.floor(size / 6);
  for (let pass = 0; pass < 40; pass++) {
    const ends = deadEnds();
    if (ends.length <= keepEnds) break;
    rnd.shuffle(ends);
    for (const [x, y] of ends.slice(0, Math.max(1, ends.length - keepEnds))) {
      if (floor.features[key(x, y)]) continue;
      grid[y][x] = 1;
    }
  }
  // (a secret door with nothing on one side any more is just a wall now)
  for (const [k, f] of Object.entries(floor.features)) {
    if (f.type === "secret") {
      const [x, y] = unkey(k);
      if (CM.DIRS.filter(([dx, dy]) => grid[y + dy][x + dx] === 0).length < 2) delete floor.features[k];
    }
  }
  // every set piece can be walked to (through its door, or its secret door): a sealed one gets a plain doorway
  for (const r of rooms) if (r.template) {
    const walk = CM.distances(grid, [r.x0, r.y0], (x, y) => x >= 0 && y >= 0 && x < size && y < size && leadsOn(x, y));
    if (walk.size > (r.x1 - r.x0 + 1) * (r.y1 - r.y0 + 1) + 4) continue;
    for (const [x, y] of r.entrances) {
      const outside = CM.DIRS.map(([dx, dy]) => [x + dx, y + dy]).find(([ox, oy]) => grid[oy] && grid[oy][ox] === 0 && !(ox >= r.x0 && ox <= r.x1 && oy >= r.y0 && oy <= r.y1));
      if (!outside) continue;
      grid[y][x] = 0;
      floor.features[key(x, y)] = { type: "door", open: false, locked: false };
      break;
    }
  }

  // where the party arrives and where the ladder goes
  const plain = rooms.filter((r) => !r.template);
  const inTemplate = (x, y) => rooms.some((r) => r.template && x >= r.x0 - 1 && x <= r.x1 + 1 && y >= r.y0 - 1 && y <= r.y1 + 1);
  const startRoom = plain.length ? plain.reduce((a, b) => (a.x0 + a.y0 <= b.x0 + b.y0 ? a : b)) : null;
  let start = startRoom ? [Math.floor((startRoom.x0 + startRoom.x1) / 2), Math.floor((startRoom.y0 + startRoom.y1) / 2)] : null;
  if (!start) {                                                   // (no plain room at all: the corridor square nearest the top left)
    for (let y = 1; y < size - 1; y++) for (let x = 1; x < size - 1; x++) if (grid[y][x] === 0 && !inTemplate(x, y) && (!start || x + y < start[0] + start[1])) start = [x, y];
    start = start || [1, 1];
  }
  if (grid[start[1]][start[0]] !== 0) { grid[start[1]][start[0]] = 0; }
  floor.pos = start.slice();
  const dist = CM.distances(grid, start);
  let far = start, best = -1;
  for (const [k, d] of dist) {
    const [x, y] = unkey(k);
    if (d > best && !inTemplate(x, y) && !floor.features[k]) { best = d; far = [x, y]; }
  }
  if (!lair) floor.things[key(far[0], far[1])] = number === CM.LAST_FLOOR ? { type: "boss", group: [CM.bossMonster()] } : { type: "ladder" };
  if (number > 1) floor.things[key(start[0], start[1])] = { type: "stairs_up" };
  const open = CM.openNeighbours(floor, start[0], start[1]);
  floor.facing = open.length ? CM.DIRS.indexOf(open[0]) : 2;

  // what the set pieces hold (a chest may be trapped, from the second floor down)
  const trap = () => (number >= 2 && rnd.chance(0.3) ? rnd.pick(Object.keys(CM.TRAPS)) : null);
  const stillGroups = [];
  for (const r of rooms) if (r.template) for (const [x, y, c] of r.fill) {
    const k = key(x, y);
    if (c === "C") floor.things[k] = { type: "chest", gold: rnd.int(15, 40) * number, items: [CM.makeItem(number, rnd), CM.makeItem(number, rnd)], trap: trap() };
    else if (c === "M") { const g = CM.monsterGroup(number, rnd); stillGroups.push(k); floor.things[k] = { type: "monsters", group: g, still: true }; }
    else if (c === "F") floor.features[k] = { type: "fountain", kind: rnd.pick(["heal", "heal", "mana", "poison"]), used: false, known: false };
    else if (c === "A") floor.features[k] = { type: "altar", used: false };
    else if (c === "P") floor.features[k] = { type: "pit" };
    else if (c === "K") floor.things[k] = { type: "key" };
    else if (c === "X") floor.dark.push(k);
    else if (c === "B" && guardian) floor.things[k] = { type: "guardian", group: CM.guardianGroup(guardian, number, rnd) };
    else if ("ntvefcr".includes(c)) floor.decor.push({ x, y, kind: { n: "nest", t: "throne", v: "anvil", e: "ember", f: "fungus", c: "crystal", r: "root" }[c] });
  }
  for (const r of rooms) if (r.template && r.template.flood) {                     // a flooded set piece: water on every floor of it
    for (let y = r.y0; y <= r.y1; y++) for (let x = r.x0; x <= r.x1; x++) if (grid[y][x] === 0) floor.decor.push({ x, y, kind: "water" });
  }
  for (const r of rooms) if (r.template) r.template.rows.forEach((row, ry) => [...row].forEach((c, rx) => {
    if (c !== "W") return;
    const x = r.x0 - 1 + rx, y = r.y0 - 1 + ry;
    const inside = CM.DIRS.map(([dx, dy], d) => [x + dx, y + dy, d]).find(([ix, iy]) => ix >= r.x0 && ix <= r.x1 && iy >= r.y0 && iy <= r.y1);
    if (inside && !floor.features[key(inside[0], inside[1])]) {
      floor.features[key(inside[0], inside[1])] = { type: "carving", face: (inside[2] + 2) % 4, text: r.template.lore || -(1 + rnd.int(0, CM.LORE_EXTRA.length - 1)), read: false };
    }
  }));

  // doors on the ordinary rooms' doorways
  const roomCells = new Set();
  for (const r of plain) for (let y = r.y0; y <= r.y1; y++) for (let x = r.x0; x <= r.x1; x++) roomCells.add(key(x, y));
  for (const [x, y] of doorways) {
    const k = key(x, y);
    if (floor.features[k] || !CM.DIRS.some(([dx, dy]) => roomCells.has(key(x + dx, y + dy)))) continue;
    const ns = grid[y - 1][x] === 0 && grid[y + 1][x] === 0 && grid[y][x - 1] === 1 && grid[y][x + 1] === 1;
    const ew = grid[y][x - 1] === 0 && grid[y][x + 1] === 0 && grid[y - 1][x] === 1 && grid[y + 1][x] === 1;
    if (!(ns || ew) || !rnd.chance(0.55)) continue;
    floor.features[k] = { type: "door", open: false, locked: number >= 2 && rnd.chance(0.12) };
  }

  // the furniture, each piece checked: the floor must still be finishable
  const place = (k, feature) => {
    floor.features[k] = feature;
    if (CM.solvable(floor)) return true;
    delete floor.features[k];
    return false;
  };
  const freeCells = (filter) => {
    const out = [];
    for (let y = 1; y < size - 1; y++) for (let x = 1; x < size - 1; x++) {
      const k = key(x, y);
      if (grid[y][x] !== 0 || floor.features[k] || floor.things[k] || (x === start[0] && y === start[1]) || inTemplate(x, y)) continue;
      if ((dist.get(k) || 0) < 2 || Math.abs(x - start[0]) + Math.abs(y - start[1]) < 2) continue;
      if (!filter || filter(x, y, k)) out.push([x, y]);
    }
    return rnd.shuffle(out);
  };
  const corridor = (x, y, k) => !roomCells.has(k);
  const wallFace = (x, y) => { const d = CM.DIRS.findIndex(([dx, dy]) => grid[y + dy][x + dx] === 1); return d; };
  const bottom = number === CM.LAST_FLOOR || number === CM.BOTTOM;   // (nothing to fall into below the Lich King's floor - the Deep has its own stair - nor below the bottom)
  if (number >= 2 && !bottom) for (const [x, y] of freeCells((x, y, k) => roomCells.has(k)).slice(0, rnd.int(0, 1 + Math.floor(number / 7)))) place(key(x, y), { type: "pit" });
  if (number >= 3 && !bottom) for (const [x, y] of freeCells(corridor).slice(0, rnd.int(0, 2))) place(key(x, y), { type: "trapdoor", known: false });
  if (number >= 3 && rnd.chance(0.7)) {
    const ends = freeCells((x, y) => CM.openNeighbours(floor, x, y).length === 1);
    if (ends.length >= 2) {
      const [a, b] = ends;
      floor.features[key(a[0], a[1])] = { type: "teleporter", to: b, known: false };
      floor.features[key(b[0], b[1])] = { type: "teleporter", to: a, known: false };
    }
  }
  if (number >= 2 && rnd.chance(0.6)) { const c = freeCells((x, y) => CM.openNeighbours(floor, x, y).length >= 3)[0]; if (c) place(key(c[0], c[1]), { type: "spinner", known: false }); }
  if (number >= 2 && rnd.chance(0.5)) {
    const darkRoom = rnd.pick(plain.filter((r) => r !== startRoom));
    if (darkRoom) for (let y = darkRoom.y0 - 1; y <= darkRoom.y1 + 1; y++) for (let x = darkRoom.x0 - 1; x <= darkRoom.x1 + 1; x++) {
      if (grid[y][x] === 0 && !(x === start[0] && y === start[1]) && !floor.dark.includes(key(x, y))) floor.dark.push(key(x, y));
    }
  }
  if (rnd.chance(0.6)) { const c = freeCells((x, y, k) => roomCells.has(k))[0]; if (c) place(key(c[0], c[1]), { type: "fountain", kind: rnd.pick(["heal", "heal", "mana", "poison"]), used: false, known: false }); }
  if (number >= 2 && rnd.chance(0.35)) { const c = freeCells((x, y, k) => roomCells.has(k))[0]; if (c) place(key(c[0], c[1]), { type: "altar", used: false }); }
  // a gate on a doorway, its lever somewhere you can get to first
  const gated = Object.entries(floor.features).filter(([, f]) => f.type === "gate");
  if (number >= 4 && rnd.chance(0.4)) {
    const door = Object.entries(floor.features).find(([, f]) => f.type === "door" && !f.locked);
    if (door) { floor.features[door[0]] = { type: "gate", open: false }; gated.push([door[0], floor.features[door[0]]]); }
  }
  for (const [gk] of gated) {
    const reach = CM.reachable(floor);
    const spots = freeCells((x, y, k) => reach.has(k) && wallFace(x, y) >= 0);
    const spot = spots[0];
    if (!spot) { floor.features[gk].open = true; continue; }
    const plate = number >= 4 && CM.hashSeed(`${seed}:plate:${number}:${gk}`) % 5 < 2;
    floor.features[key(spot[0], spot[1])] = plate ? { type: "plate", gate: gk, pressed: false } : { type: "lever", face: wallFace(spot[0], spot[1]), gate: gk, pulled: false };
    if (!CM.solvable(floor)) { delete floor.features[key(spot[0], spot[1])]; floor.features[gk].open = true; }
  }
  // the carving for this floor, on a wall the party can stand before
  const carve_at = freeCells((x, y) => wallFace(x, y) >= 0)[0];
  if (carve_at) floor.features[key(carve_at[0], carve_at[1])] = { type: "carving", face: wallFace(carve_at[0], carve_at[1]),
    text: number > CM.BOTTOM ? `e:${CM.hashSeed(`${seed}:endless:${number}`) % CM.LORE_ENDLESS.length}` : number - 1, read: false };   // (below the bottom: the dream, still dreaming)
  // keys: one for every locked door, somewhere before it
  for (const [dk, f] of Object.entries(floor.features)) {
    if (f.type !== "door" || !f.locked) continue;
    const reach = CM.reachable(floor);
    const spots = freeCells((x, y, k) => reach.has(k) && !roomCells.has(k) || (reach.has(k) && rnd.chance(0.3)));
    const spot = spots[0];
    if (spot) floor.things[key(spot[0], spot[1])] = { type: "key" };
    else f.locked = false;
  }
  // chests and monsters
  const spare = freeCells((x, y, k) => (dist.get(k) || 0) > 3);
  for (let i = 0; i < Math.min(12, 3 + Math.floor(number / 4)) && spare.length; i++) {
    const [x, y] = spare.pop();
    const items = [];
    const n = rnd.int(1, 2);
    for (let j = 0; j < n; j++) items.push(CM.makeItem(number, rnd));
    floor.things[key(x, y)] = { type: "chest", gold: rnd.int(10, 30) * number, items, trap: trap() };
  }
  for (let i = 0; i < (special === "maze" ? 3 : Math.min(14, 5 + Math.floor(number / 2))) && spare.length; i++) {
    const [x, y] = spare.pop();
    floor.things[key(x, y)] = { type: "monsters", group: CM.monsterGroup(number, rnd) };
  }
  if (special === "maze" && spare.length) {                      // the thing in the labyrinth: a great minotaur that hunts the party wherever it goes
    const [x, y] = spare.pop(), m = CM.makeMonster(CM.monsterKind("Minotaur"), number + 3, rnd);
    Object.assign(m, { name: "Minotaur of the Labyrinth", elite: "hulking", max: Math.round(m.max * 1.5), atk: m.atk + 3, xp: m.xp * 3, gold: m.gold * 4 });
    m.hp = m.max;
    floor.things[key(x, y)] = { type: "monsters", group: [m], hunter: true };
  }
  if (!CM.solvable(floor)) {                                     // (it never comes to this, but a floor must be finishable)
    for (const [k, f] of Object.entries(floor.features)) if (["pit", "trapdoor", "gate"].includes(f.type) || (f.type === "door" && f.locked)) delete floor.features[k];
  }
  if (number === CM.LAST_FLOOR - 1) {                             // the Lich King's heart, somewhere the party can get to
    const reach = CM.reachable(floor), goal = CM.goalOf(floor);
    const spots = freeCells((x, y, k) => reach.has(k) && k !== goal).sort((a, b) => (dist.get(key(b[0], b[1])) || 0) - (dist.get(key(a[0], a[1])) || 0));
    const spot = spots[0];
    if (spot) floor.things[key(spot[0], spot[1])] = { type: "phylactery" };
  }
  // a door that asks a riddle from the carvings above (never a locked one, never a set piece's)
  if (number >= CM.RIDDLE_FROM) {
    const asks = CM.RIDDLES.map((r, i) => i).filter((i) => CM.RIDDLES[i].lore + 1 < number);
    const doors = Object.entries(floor.features).filter(([k, f]) => f.type === "door" && !f.locked && !inTemplate(...unkey(k)));
    const pick = doors.filter(([k]) => CM.hashSeed(`${seed}:riddle:${number}:${k}`) % 10 < 3)[0];
    if (pick && asks.length) pick[1].riddle = asks[CM.hashSeed(`${seed}:riddle:${number}`) % asks.length];
  }
  // plates in the floor that spring a trap, from the third floor down
  if (number >= 3) for (const [x, y] of freeCells(corridor).slice(0, rnd.int(0, 2))) floor.features[key(x, y)] = { type: "plate", trap: rnd.pick(Object.keys(CM.TRAPS)), known: false, spent: false };
  // the people: a ghost with a request, a hermit, a lost adventurer - one of them on a floor, now and then
  if (number >= 2 && number < CM.LAST_FLOOR && !CM.guardianFor(number) && special !== "maze") {
    const roll = rnd.next(), room = (x, y, k) => roomCells.has(k);
    if (roll < 0.22) {
      const spot = freeCells(room)[0];
      if (spot) {
        const who = rnd.int(0, CM.GHOSTS.length - 1), gk = key(spot[0], spot[1]);
        const groups = Object.entries(floor.things).filter(([, t]) => t.type === "monsters" && !t.still && !t.hunter);
        let request = rnd.pick(["bones", "vengeance", "story"]);
        if (request === "vengeance" && !groups.length) request = "story";
        floor.things[gk] = { type: "ghost", who, request, asked: false };
        if (request === "bones") {
          const far = freeCells((x, y, k) => Math.abs(x - spot[0]) + Math.abs(y - spot[1]) >= 6)[0] || freeCells()[0];
          if (far) floor.things[key(far[0], far[1])] = { type: "bones", ghost: gk };
          else floor.things[gk].request = "story";
        } else if (request === "vengeance") {
          const [, t] = rnd.pick(groups);
          t.vengeance = gk;
          const m = t.group[0];
          if (!m.elite) { m.name = `Hulking ${m.name}`; m.elite = "hulking"; m.max = Math.round(m.max * 1.5); m.hp = m.max; m.atk += 2; m.xp = Math.round(m.xp * 1.5); m.gold *= 2; }
        }
      }
    } else if (roll < 0.36 && number >= 3) {
      const spot = freeCells((x, y) => CM.openNeighbours(floor, x, y).length === 1)[0] || freeCells(room)[0];
      if (spot) floor.things[key(spot[0], spot[1])] = { type: "hermit", heard: 0, greeted: false };
    } else if (roll < 0.5 && number >= 3) {
      const spot = freeCells(room)[0];
      if (spot) floor.things[key(spot[0], spot[1])] = { type: "adventurer", hero: CM.makeRecruit(Math.max(1, Math.floor(number / 2)), rnd), freed: false };
    }
  }
  if (special === "wading") for (let y = 1; y < size - 1; y++) for (let x = 1; x < size - 1; x++) if (grid[y][x] === 0) floor.decor.push({ x, y, kind: "water" });
  if (special === "dark") for (let y = 1; y < size - 1; y++) for (let x = 1; x < size - 1; x++) if (grid[y][x] === 0 && !floor.dark.includes(key(x, y))) floor.dark.push(key(x, y));
  floor.rooms = rooms.map((r) => ({ x0: r.x0, y0: r.y0, x1: r.x1, y1: r.y1, name: r.template ? r.template.name : "" }));
  return floor;
};
}
