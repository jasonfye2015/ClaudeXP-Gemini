"use strict";
// The world: items, a floor's maze with its chests, monsters and ladder, monster groups, a new party.
// Pure functions of a Random, so a seed gives the same dungeon every time (and the tests can check thousands).

CM.makeItem = function (floor, rnd, kind) {
  kind = kind || rnd.pick(["weapon", "weapon", "armor", "armor", "potion", "potion", "potion"]);
  if (kind === "potion") {
    const roll = rnd.next();
    if (roll < 0.12) return { name: "Phoenix Feather", kind: "revive", power: 0, value: 120 };
    if (roll < 0.4) return { name: "Mana Potion", kind: "mana", power: 12 + floor, value: 25 };
    return { name: "Healing Potion", kind: "heal", power: 20 + floor * 3, value: 20 };
  }
  const tier = CM.clamp(Math.floor((floor + rnd.int(-2, 2)) * 12 / 21), 0, 11);
  const names = kind === "weapon" ? CM.WEAPONS : CM.ARMORS;
  const power = (tier + 1) * (kind === "weapon" ? 2 : 1) + rnd.int(0, 2);
  const bonus = rnd.chance(0.15);
  return { name: names[tier] + (bonus ? " +1" : ""), kind, power: power + (bonus ? 2 : 0),
    value: 15 * (tier + 1) * (tier + 1) + (bonus ? 40 : 0) };
};

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

// how far every open square is from the start (a breadth-first walk)
CM.distances = function (grid, start) {
  const key = (x, y) => `${x},${y}`;
  const dist = new Map([[key(start[0], start[1]), 0]]);
  const queue = [start];
  for (let i = 0; i < queue.length; i++) {
    const [x, y] = queue[i];
    for (const [dx, dy] of CM.DIRS) {
      const nx = x + dx, ny = y + dy;
      if (ny >= 0 && ny < grid.length && nx >= 0 && nx < grid[0].length && grid[ny][nx] === 0 && !dist.has(key(nx, ny))) {
        dist.set(key(nx, ny), dist.get(key(x, y)) + 1);
        queue.push([nx, ny]);
      }
    }
  }
  return dist;
};

// A floor: a maze (recursive backtracker, with some extra openings so it isn't perfect), the start, the ladder on the
// open square furthest from it (or the Lich King, on the last), chests and monsters on the way.
CM.makeFloor = function (number, seed) {
  const rnd = new CM.Random(CM.hashSeed(`${seed}:floor:${number}`));
  const size = Math.min(17 + Math.floor(number / 4) * 2, 27);
  const grid = [];
  for (let y = 0; y < size; y++) grid.push(new Array(size).fill(1));
  const stack = [[1, 1]];
  grid[1][1] = 0;
  while (stack.length) {
    const [x, y] = stack[stack.length - 1];
    const options = CM.DIRS.filter(([dx, dy]) => x + dx * 2 > 0 && x + dx * 2 < size - 1 && y + dy * 2 > 0 && y + dy * 2 < size - 1
      && grid[y + dy * 2][x + dx * 2] === 1);
    if (!options.length) { stack.pop(); continue; }
    const [dx, dy] = rnd.pick(options);
    grid[y + dy][x + dx] = 0;
    grid[y + dy * 2][x + dx * 2] = 0;
    stack.push([x + dx * 2, y + dy * 2]);
  }
  for (let i = 0; i < Math.floor(size * size / 14); i++) {                // loops, so there's more than one way round
    const x = rnd.int(1, size - 2), y = rnd.int(1, size - 2);
    if (grid[y][x] === 1 && ((grid[y][x - 1] === 0 && grid[y][x + 1] === 0) || (grid[y - 1][x] === 0 && grid[y + 1][x] === 0))) grid[y][x] = 0;
  }
  const start = [1, 1];
  const dist = CM.distances(grid, start);
  let far = start, best = -1;
  for (const [k, d] of dist) if (d > best) { best = d; far = k.split(",").map(Number); }
  const things = {};
  const spare = [];
  for (let y = 0; y < size; y++) for (let x = 0; x < size; x++) {
    if (grid[y][x] === 0 && !(x === 1 && y === 1) && !(x === far[0] && y === far[1]) && (dist.get(`${x},${y}`) || 0) > 3) spare.push([x, y]);
  }
  rnd.shuffle(spare);
  for (let i = 0; i < 3 + Math.floor(number / 4) && spare.length; i++) {
    const [x, y] = spare.pop();
    const items = [];
    const n = rnd.int(1, 2);
    for (let j = 0; j < n; j++) items.push(CM.makeItem(number, rnd));
    things[`${x},${y}`] = { type: "chest", gold: rnd.int(10, 30) * number, items };
  }
  for (let i = 0; i < 5 + Math.floor(number / 2) && spare.length; i++) {
    const [x, y] = spare.pop();
    things[`${x},${y}`] = { type: "monsters", group: CM.monsterGroup(number, rnd) };
  }
  things[`${far[0]},${far[1]}`] = number === CM.LAST_FLOOR ? { type: "boss", group: [CM.bossMonster()] } : { type: "ladder" };
  return { number, grid, pos: [1, 1], facing: grid[2][1] === 0 ? 2 : 1, things, seen: [] };
};

// can the party get from the start to the ladder (or the Lich King)? - what the tests ask of every floor
CM.solvable = function (floor) {
  const dist = CM.distances(floor.grid, [1, 1]);
  const goal = Object.entries(floor.things).find(([, t]) => t.type === "ladder" || t.type === "boss");
  return Boolean(goal) && dist.has(goal[0]);
};

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
  return [CM.makeItem(1, rnd, "potion"), CM.makeItem(1, rnd, "potion")];
};
