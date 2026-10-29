"use strict";
// The world: items, monster groups, a new party - and a floor: rooms joined by corridors (Nystrom's rooms-and-mazes),
// a few set-piece rooms dropped in, then the dungeon's furniture: doors (some locked, their keys somewhere before
// them), secret doors on the shortcuts, pits and hidden trapdoors, teleporter pairs, spinners, a dark room, a
// fountain, an altar, a gate with its lever, a carving telling the Lich King's story, chests and monsters, the stairs
// up where you arrive and the ladder down as far from them as the floor allows. Pure functions of a Random, so a seed
// gives the same dungeon every time; CM.solvable proves each floor can be finished before it's handed over.

CM.makeItem = function (floor, rnd, kind) {
  kind = kind || rnd.pick(["weapon", "weapon", "armor", "armor", "potion", "potion", "potion"]);
  if (kind === "potion") {
    const roll = rnd.next();
    if (roll < 0.12) return { name: "Phoenix Feather", kind: "revive", power: 0, value: 120 };
    if (roll < 0.4) return { name: "Mana Potion", kind: "mana", power: 12 + floor, value: 25 };
    if (roll < 0.52) return CM.torch();
    return { name: "Healing Potion", kind: "heal", power: 20 + floor * 3, value: 20 };
  }
  const tier = CM.clamp(Math.floor((floor + rnd.int(-2, 2)) * 12 / 21), 0, 11);
  const names = kind === "weapon" ? CM.WEAPONS : CM.ARMORS;
  const power = (tier + 1) * (kind === "weapon" ? 2 : 1) + rnd.int(0, 2);
  const bonus = rnd.chance(0.15);
  return { name: names[tier] + (bonus ? " +1" : ""), kind, power: power + (bonus ? 2 : 0),
    value: 15 * (tier + 1) * (tier + 1) + (bonus ? 40 : 0) };
};

CM.TORCH_STEPS = 400;                    // a torch burns this many steps
CM.torch = () => ({ name: "Torch", kind: "torch", power: CM.TORCH_STEPS, value: 8 });
CM.lantern = () => ({ name: "Lantern", kind: "lantern", power: 0, value: 150 });
CM.key = () => ({ name: "Iron Key", kind: "key", power: 0, value: 0 });

CM.monsterGroup = function (floor, rnd) {
  const top = Math.min(CM.MONSTERS.length - 1, Math.floor(floor * CM.MONSTERS.length / CM.LAST_FLOOR));
  const kind = CM.MONSTERS[rnd.int(Math.max(0, top - 2), top)];
  const count = rnd.int(1, 2 + Math.floor(floor / 6));
  const level = floor;
  const group = [];
  for (let i = 0; i < count; i++) {
    group.push({ name: kind.name, colour: kind.colour, hp: 8 + level * 6, max: 8 + level * 6, atk: 3 + level * 2, df: level,
      xp: 10 + level * 8, gold: rnd.int(2, 8) * level });
  }
  return group;
};

CM.bossMonster = () => ({ name: CM.BOSS.name, colour: CM.BOSS.colour, hp: 650, max: 650, atk: 46, df: 18, xp: 5000, gold: 5000, boss: true });

CM.newParty = function () {
  return CM.CLASS_ORDER.map((cls) => {
    const s = CM.CLASSES[cls];
    return { name: cls, cls, level: 1, xp: 0, hp: s.hp, max: s.hp, mp: s.mp, maxmp: s.mp, atk: s.atk, df: s.df,
      weapon: { name: cls === "Mage" || cls === "Cleric" ? "Staff" : "Club", kind: "weapon", power: 1, value: 5 },
      armor: { name: cls === "Mage" ? "Robes" : "Tunic", kind: "armor", power: 0, value: 5 } };
  });
};

CM.startingBag = (seed) => {
  const rnd = new CM.Random(CM.hashSeed(`${seed}:bag`));
  return [CM.makeItem(1, rnd, "potion"), CM.makeItem(1, rnd, "potion"), CM.torch(), CM.torch()];
};

// ---- what's carved into the walls: the Lich King's story, a floor at a time ------------------------------------------
CM.LORE = [
  "Here lie the first dead of Caer Duin. King Mordeth wept for each of them. He would not always.",
  "The plague came up the river in the king's twelfth year. The priests said it would pass. It did not pass.",
  "When the queen died, Mordeth shut the gates and had the bells taken down. No one has rung one since.",
  "The king sent for every book that spoke of death, and for every man who claimed to have come back from it.",
  "Below this floor the water rose and never fell. The lower town drowned in a single night, doors still barred.",
  "A stranger came from the east with a box he would not open. He left without it. The king kept it by his bed.",
  "The court physician wrote: the king no longer sleeps, and says he no longer needs to. I have begun to believe him.",
  "The dwarves of the deep halls traded with Caer Duin for three hundred years. Their last letter asked why the king's coin was cold.",
  "Here the guard turned back. Beyond this point the king's orders came written in a hand that was not quite his.",
  "They burned the physician's notes. One page survived: the heart may be kept apart, and the body need not know.",
  "The dwarves sealed their doors from the inside. The seals held for a year. Then the doors opened, and nothing came out.",
  "A child's letters, scratched here: MOTHER SAYS THE KING IS STILL OUR KING. MOTHER SAYS NOT TO LOOK AT HIM.",
  "The halls below were made for a people who loved stone. They would not have left them. They did not leave them.",
  "The last captain of the guard wrote his name here before he went down. The king had asked for him by name.",
  "Whoever reads this: the thing that wears the crown remembers being Mordeth. That is the worst of it.",
  "The palace was built in a year, by hands that did not tire. The masons' graves are the foundations.",
  "He keeps the court. They sit where they sat. If you listen you can hear them not breathing.",
  "The box from the east is empty now. What was in it, he put somewhere safer. Somewhere nearer his heart.",
  "The king's heart is not in his chest. Find it, and he can be ended. Fail, and he will rise as often as you kill him.",
  "Beyond this door he waits. He has waited so long that he has forgotten what for. Remind him.",
];
CM.LORE_EXTRA = [
  "A recipe for barley bread, carved with great care, as if it mattered more than anything.",
  "Tally marks. Hundreds. The last row stops in the middle of a stroke.",
  "THE WATER IS NOT WATER, scratched deep, and under it in a smaller hand: it is, though.",
  "A map of a floor you haven't seen. The stairs are marked. So is something else, with a circle round it.",
  "Here Aldous the Lesser slew a troll with a chair. The chair is remembered more fondly than Aldous.",
  "Someone has carved a window here, with a view. They put a great deal of work into the sky.",
  "Turn back, in six languages. The seventh says: or don't - he's lonely.",
  "A prayer to a god whose name has been chiselled out. The prayer is still there, which seems rude.",
];

// ---- set-piece rooms: the ring of wall included; D door, L locked door, G gate, S secret door on the ring ------------
// Inside: C chest, M monsters that stay put, F fountain, A altar, P pit, K a key on the floor, X dark floor, W a wall
// with a carving (read from the floor beside it). Entrances sit at odd positions so the maze comes up to them.
CM.TEMPLATES = [
  { name: "Treasure Vault", min: 2, rows: ["#######", "#C...C#", "#..C..#", "###L###"] },
  { name: "Shrine", min: 2, rows: ["#######", "#..A..#", "#.....#", "#C....#", "###D###"] },
  { name: "Fountain Hall", min: 1, rows: ["#########", "#.......#", "#...F...#", "#.......#", "###D#####"] },
  { name: "Den", min: 2, rows: ["#######", "#M...M#", "#..C..#", "#.....#", "###D###"] },
  { name: "Library", min: 3, rows: ["###W###", "#.....#", "W..C..W", "#.....#", "###D###"] },
  { name: "Crypt", min: 3, rows: ["#######", "#XXXXX#", "#XMXCX#", "#XXXXX#", "###S###"] },
  { name: "Pit Room", min: 3, rows: ["#######", "#.P.P.#", "#.....#", "#P.C.P#", "###D###"] },
  { name: "Keep", min: 4, rows: ["#########", "#C.....C#", "#.......#", "#...K...#", "###G#####"] },
];

// ---- helpers -----------------------------------------------------------------------------------------------------
const key = (x, y) => `${x},${y}`;
const unkey = (k) => k.split(",").map(Number);

CM.inBounds = (floor, x, y) => y >= 0 && y < floor.grid.length && x >= 0 && x < floor.grid.length;

// a cell the party could stand in (doors and gates included, whatever their state)
CM.isOpen = function (floor, x, y) {
  if (!CM.inBounds(floor, x, y)) return false;
  if (floor.grid[y][x] === 0) return true;
  const f = floor.features[key(x, y)];
  return Boolean(f && f.type === "secret" && f.found);
};

// a cell the party can walk into right now
CM.passable = function (floor, x, y) {
  if (!CM.isOpen(floor, x, y)) return false;
  const f = floor.features[key(x, y)];
  if (f && (f.type === "door" || f.type === "gate") && !f.open) return false;
  return true;
};

CM.openNeighbours = (floor, x, y) => CM.DIRS.filter(([dx, dy]) => CM.isOpen(floor, x + dx, y + dy));

// how far every open square is from the start, walking where `walk` allows (a breadth-first walk)
CM.distances = function (grid, start, walk) {
  const size = grid.length;
  const ok = walk || ((x, y) => y >= 0 && y < size && x >= 0 && x < size && grid[y][x] === 0);
  const dist = new Map([[key(start[0], start[1]), 0]]);
  const queue = [start];
  for (let i = 0; i < queue.length; i++) {
    const [x, y] = queue[i];
    for (const [dx, dy] of CM.DIRS) {
      const nx = x + dx, ny = y + dy;
      if (ok(nx, ny) && !dist.has(key(nx, ny))) {
        dist.set(key(nx, ny), dist.get(key(x, y)) + 1);
        queue.push([nx, ny]);
      }
    }
  }
  return dist;
};

// Everything the party can reach from where it stands, finding keys and pulling levers as it goes, never falling into a
// pit, never finding a secret door: the floor is solvable when the ladder (or the Lich King) is in that set.
CM.reachable = function (floor, from) {
  const start = from || floor.pos;
  const unlocked = new Set(), opened = new Set();
  let reach = new Set();
  for (let pass = 0; pass < 12; pass++) {
    reach = new Set();
    const queue = [start];
    reach.add(key(start[0], start[1]));
    for (let i = 0; i < queue.length; i++) {
      const [x, y] = queue[i];
      const here = floor.features[key(x, y)];
      const nexts = CM.DIRS.map(([dx, dy]) => [x + dx, y + dy]);
      if (here && here.type === "teleporter") nexts.push(here.to);
      for (const [nx, ny] of nexts) {
        const k = key(nx, ny);
        if (reach.has(k) || !CM.inBounds(floor, nx, ny)) continue;
        const f = floor.features[k];
        if (floor.grid[ny][nx] !== 0) {
          if (!(f && f.type === "secret" && f.found)) continue;
        }
        if (f) {
          if ((f.type === "pit" || f.type === "trapdoor") && !(nx === start[0] && ny === start[1])) continue;
          if (f.type === "door" && f.locked && !unlocked.has(k)) continue;
          if (f.type === "gate" && !f.open && !opened.has(k)) continue;
        }
        reach.add(k);
        queue.push([nx, ny]);
      }
    }
    let keys = 0, changed = false;
    for (const k of reach) {
      const t = floor.things[k];
      if (t && t.type === "key") keys++;
      const f = floor.features[k];
      if (f && f.type === "lever" && !opened.has(f.gate)) { opened.add(f.gate); changed = true; }
    }
    keys -= unlocked.size;                                   // (a key opens one door)
    for (const k of reach) {
      for (const [dx, dy] of CM.DIRS) {
        const nk = key(unkey(k)[0] + dx, unkey(k)[1] + dy);
        const f = floor.features[nk];
        if (f && f.type === "door" && f.locked && !unlocked.has(nk) && !reach.has(nk) && keys > 0) { unlocked.add(nk); keys--; changed = true; }
      }
    }
    if (!changed) break;
  }
  return reach;
};

CM.goalOf = (floor) => Object.keys(floor.things).find((k) => ["ladder", "boss"].includes(floor.things[k].type)) || null;

CM.solvable = function (floor, from) {
  const goal = CM.goalOf(floor);
  return Boolean(goal) && CM.reachable(floor, from).has(goal);
};

// ---- the floor ----------------------------------------------------------------------------------------------------
CM.makeFloor = function (number, seed) {
  const rnd = new CM.Random(CM.hashSeed(`${seed}:floor:${number}`));
  const size = Math.min(17 + Math.floor(number / 4) * 2, 27);
  const grid = [];
  for (let y = 0; y < size; y++) grid.push(new Array(size).fill(1));
  const floor = { number, grid, pos: [1, 1], facing: 2, things: {}, features: {}, dark: [], seen: [], rooms: [] };
  const rooms = [];                            // {x0, y0, x1, y1 (interior, inclusive), template?, entrances: [[x,y,kind]]}
  const taken = (x0, y0, x1, y1) => rooms.some((r) => x0 <= r.x1 + 2 && x1 >= r.x0 - 2 && y0 <= r.y1 + 2 && y1 >= r.y0 - 2);
  const carve = (x0, y0, x1, y1) => { for (let y = y0; y <= y1; y++) for (let x = x0; x <= x1; x++) grid[y][x] = 0; };

  // set pieces first (one or two, where they fit), then ordinary rooms
  const wanted = CM.TEMPLATES.filter((t) => number >= t.min && !(number === CM.LAST_FLOOR && t.name === "Pit Room"));
  rnd.shuffle(wanted);
  for (const tpl of wanted.slice(0, number >= 6 ? 2 : 1)) {
    const h = tpl.rows.length - 2, w = tpl.rows[0].length - 2;
    for (let tries = 0; tries < 40; tries++) {
      const x0 = 3 + 2 * rnd.int(0, Math.floor((size - 6 - w) / 2)), y0 = 3 + 2 * rnd.int(0, Math.floor((size - 6 - h) / 2));
      const x1 = x0 + w - 1, y1 = y0 + h - 1;
      if (x1 > size - 4 || y1 > size - 4 || taken(x0, y0, x1, y1)) continue;         // (room for the maze beyond every entrance)
      const room = { x0, y0, x1, y1, template: tpl, entrances: [], fill: [] };
      let fits = true;
      tpl.rows.forEach((row, ry) => [...row].forEach((c, rx) => {
        const x = x0 - 1 + rx, y = y0 - 1 + ry;
        if ("DLGS".includes(c)) {
          const onSide = ry === 0 || ry === tpl.rows.length - 1;
          if ((onSide && x % 2 === 0) || (!onSide && y % 2 === 0)) fits = false;      // (the maze won't come up to it)
          room.entrances.push([x, y, c]);
        } else if (c !== "#" && c !== "W") room.fill.push([x, y, c]);
      }));
      if (!fits) continue;
      carve(x0, y0, x1, y1);
      rooms.push(room);
      break;
    }
  }
  const roomTries = 14 + number;
  for (let i = 0; i < roomTries; i++) {
    const w = 3 + 2 * rnd.int(0, 1 + Math.floor(number / 7)), h = 3 + 2 * rnd.int(0, 1);
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
  const keepEnds = 3 + Math.floor(size / 6);
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
  const startRoom = plain.length ? plain.reduce((a, b) => (a.x0 + a.y0 <= b.x0 + b.y0 ? a : b)) : null;
  const start = startRoom ? [Math.floor((startRoom.x0 + startRoom.x1) / 2), Math.floor((startRoom.y0 + startRoom.y1) / 2)] : [1, 1];
  if (grid[start[1]][start[0]] !== 0) { grid[start[1]][start[0]] = 0; }
  floor.pos = start.slice();
  const dist = CM.distances(grid, start);
  const inTemplate = (x, y) => rooms.some((r) => r.template && x >= r.x0 - 1 && x <= r.x1 + 1 && y >= r.y0 - 1 && y <= r.y1 + 1);
  let far = start, best = -1;
  for (const [k, d] of dist) {
    const [x, y] = unkey(k);
    if (d > best && !inTemplate(x, y) && !floor.features[k]) { best = d; far = [x, y]; }
  }
  floor.things[key(far[0], far[1])] = number === CM.LAST_FLOOR ? { type: "boss", group: [CM.bossMonster()] } : { type: "ladder" };
  if (number > 1) floor.things[key(start[0], start[1])] = { type: "stairs_up" };
  const open = CM.openNeighbours(floor, start[0], start[1]);
  floor.facing = open.length ? CM.DIRS.indexOf(open[0]) : 2;

  // what the set pieces hold
  const stillGroups = [];
  for (const r of rooms) if (r.template) for (const [x, y, c] of r.fill) {
    const k = key(x, y);
    if (c === "C") floor.things[k] = { type: "chest", gold: rnd.int(15, 40) * number, items: [CM.makeItem(number, rnd), CM.makeItem(number, rnd)] };
    else if (c === "M") { const g = CM.monsterGroup(number, rnd); stillGroups.push(k); floor.things[k] = { type: "monsters", group: g, still: true }; }
    else if (c === "F") floor.features[k] = { type: "fountain", kind: rnd.pick(["heal", "heal", "mana", "poison"]), used: false, known: false };
    else if (c === "A") floor.features[k] = { type: "altar", used: false };
    else if (c === "P") floor.features[k] = { type: "pit" };
    else if (c === "K") floor.things[k] = { type: "key" };
    else if (c === "X") floor.dark.push(k);
  }
  for (const r of rooms) if (r.template) r.template.rows.forEach((row, ry) => [...row].forEach((c, rx) => {
    if (c !== "W") return;
    const x = r.x0 - 1 + rx, y = r.y0 - 1 + ry;
    const inside = CM.DIRS.map(([dx, dy], d) => [x + dx, y + dy, d]).find(([ix, iy]) => ix >= r.x0 && ix <= r.x1 && iy >= r.y0 && iy <= r.y1);
    if (inside && !floor.features[key(inside[0], inside[1])]) {
      floor.features[key(inside[0], inside[1])] = { type: "carving", face: (inside[2] + 2) % 4, text: -(1 + rnd.int(0, CM.LORE_EXTRA.length - 1)), read: false };
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
  const bottom = number === CM.LAST_FLOOR;                        // (nothing to fall into below the last floor)
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
    floor.features[key(spot[0], spot[1])] = { type: "lever", face: wallFace(spot[0], spot[1]), gate: gk, pulled: false };
    if (!CM.solvable(floor)) { delete floor.features[key(spot[0], spot[1])]; floor.features[gk].open = true; }
  }
  // the carving for this floor, on a wall the party can stand before
  const carve_at = freeCells((x, y) => wallFace(x, y) >= 0)[0];
  if (carve_at) floor.features[key(carve_at[0], carve_at[1])] = { type: "carving", face: wallFace(carve_at[0], carve_at[1]), text: number - 1, read: false };
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
  for (let i = 0; i < 3 + Math.floor(number / 4) && spare.length; i++) {
    const [x, y] = spare.pop();
    const items = [];
    const n = rnd.int(1, 2);
    for (let j = 0; j < n; j++) items.push(CM.makeItem(number, rnd));
    floor.things[key(x, y)] = { type: "chest", gold: rnd.int(10, 30) * number, items };
  }
  for (let i = 0; i < 5 + Math.floor(number / 2) && spare.length; i++) {
    const [x, y] = spare.pop();
    floor.things[key(x, y)] = { type: "monsters", group: CM.monsterGroup(number, rnd) };
  }
  if (!CM.solvable(floor)) {                                     // (it never comes to this, but a floor must be finishable)
    for (const [k, f] of Object.entries(floor.features)) if (["pit", "trapdoor", "gate"].includes(f.type) || (f.type === "door" && f.locked)) delete floor.features[k];
  }
  floor.rooms = rooms.map((r) => ({ x0: r.x0, y0: r.y0, x1: r.x1, y1: r.y1, name: r.template ? r.template.name : "" }));
  return floor;
};
