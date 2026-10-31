"use strict";
// The Mage Tower's floors (the twelfth update, phase 1): forty floors of its own, apart from the shaft's - numbered 1001
// to 1040 where a floor needs a number, never saved as floors (the run keeps only how far it has climbed). Each is made
// from the run's seed: large rooms (five to ten a side) joined by halls two and three wide, the hero's start in the
// room nearest one corner, and the ladder up in the room farthest from it - the boss's room. The fortieth is one hall
// with pillars through it and the King's dais at the far end. What the floor holds is a list for the real-time fight
// (CM.TowerRun): the monsters' spawns, the boss's, and the things lying about (quivers, draughts).
CM.TOWER_FLOORS = 40;
CM.TOWER_BASE = 1000;
CM.isTowerFloor = (n) => n > CM.TOWER_BASE && n <= CM.TOWER_BASE + CM.TOWER_FLOORS;
CM.TOWER_THEME = Object.assign({}, CM.THEMES[3], {
  name: "The Mage Tower", floors: [1001, 1040], stone: [62, 60, 72], mortar: [22, 20, 28], floor: [46, 44, 54], ceiling: [30, 28, 38], moss: [90, 70, 140],
  fog: [0.02, 0.015, 0.035], torch: [0.82, 0.78, 1.0], reach: 7.5, bones: 0.08, photos: "t3", pixel: "t3", tower: true, grade: [0.97, 0.96, 1.05],
  lightColour: [0.62, 0.48, 1.0],
});
CM.towerFloorName = (n) => (n === CM.TOWER_FLOORS ? "The Mage Tower, the King's hall" : `The Mage Tower, floor ${n}`);
// the dungeon floor whose kinds and strength a tower floor borrows: the first bands low, the Deep high
CM.towerDepth = (n) => Math.min(CM.BOTTOM || 50, Math.max(1, Math.round(n * 1.2)));

CM.makeTowerFloor = function (n, seed) {
  const rnd = new CM.Random(CM.hashSeed(`${seed}:magetower:${n}`)), size = n === CM.TOWER_FLOORS ? 31 : 33 + 2 * Math.min(3, Math.floor(n / 10));
  const grid = []; for (let y = 0; y < size; y++) grid.push(new Array(size).fill(1));
  const carve = (x0, y0, x1, y1) => { for (let y = Math.max(1, y0); y <= Math.min(size - 2, y1); y++) for (let x = Math.max(1, x0); x <= Math.min(size - 2, x1); x++) grid[y][x] = 0; };
  const fl = { number: CM.TOWER_BASE + n, tower: n, grid, things: {}, features: {}, dark: [], seen: [], decor: [], rooms: [], spawns: [], items: [], pillars: [] };
  if (n === CM.TOWER_FLOORS) {                                          // the King's hall: open, pillars, a dais
    carve(2, 2, size - 3, size - 3);
    for (let y = 6; y <= size - 9; y += 5) for (let x = 5 + ((y / 5) % 2 ? 2 : 0); x <= size - 6; x += 6) { grid[y][x] = 1; grid[y][x + 1] = 1; grid[y + 1][x] = 1; grid[y + 1][x + 1] = 1; fl.pillars.push([x, y]); }
    const mid = Math.floor(size / 2);
    fl.start = [mid, size - 4, 0]; fl.ladder = null; fl.dais = [mid, 4];
    fl.rooms.push({ x0: 2, y0: 2, x1: size - 3, y1: size - 3, name: "The King's hall" });
    fl.boss = { x: mid, y: 4, king: true };
    for (const [x, y] of [[3, 3], [size - 4, 3], [3, size - 4], [size - 4, size - 4]]) fl.items.push({ x, y, kind: "draught" });
    fl.pos = fl.start.slice(0, 2); fl.facing = 0;
    return fl;
  }
  // rooms: as many as fit, a few tries each, three cells of rock between
  const rooms = [];
  for (let tries = 0; tries < 900 && rooms.length < 9 + Math.floor(n / 8); tries++) {
    const w = rnd.int(5, rooms.length < 3 ? 10 : 8), h = rnd.int(5, rooms.length < 3 ? 10 : 8), x0 = rnd.int(2, size - 3 - w), y0 = rnd.int(2, size - 3 - h), r = { x0, y0, x1: x0 + w - 1, y1: y0 + h - 1 };
    if (rooms.some((o) => r.x0 - 2 <= o.x1 && o.x0 - 2 <= r.x1 && r.y0 - 2 <= o.y1 && o.y0 - 2 <= r.y1)) continue;
    rooms.push(r);
  }
  for (const r of rooms) carve(r.x0, r.y0, r.x1, r.y1);
  const mid = (r) => [Math.floor((r.x0 + r.x1) / 2), Math.floor((r.y0 + r.y1) / 2)];
  // the halls: each room to its nearest joined room (a spanning tree), and a couple more for loops, two or three wide
  const hall = (a, b) => {
    const [ax, ay] = mid(a), [bx, by] = mid(b), w = rnd.chance(0.5) ? 2 : 3, flip = rnd.chance(0.5);
    const run = (x0, y0, x1, y1) => carve(Math.min(x0, x1), Math.min(y0, y1), Math.max(x0, x1) + (y0 === y1 ? 0 : w - 1), Math.max(y0, y1) + (y0 === y1 ? w - 1 : 0));
    if (flip) { run(ax, ay, bx, ay); run(bx, ay, bx, by); } else { run(ax, ay, ax, by); run(ax, by, bx, by); }
  };
  const joined = [rooms[0]], left = rooms.slice(1);
  while (left.length) {
    let best = null;
    for (const a of joined) for (const b of left) { const [ax, ay] = mid(a), [bx, by] = mid(b), d = Math.abs(ax - bx) + Math.abs(ay - by); if (!best || d < best.d) best = { a, b, d }; }
    hall(best.a, best.b); joined.push(best.b); left.splice(left.indexOf(best.b), 1);
  }
  for (let i = 0; i < 2 && rooms.length > 3; i++) hall(rooms[rnd.int(0, rooms.length - 1)], rooms[rnd.int(0, rooms.length - 1)]);
  // the start: the room nearest the south-west corner; the boss's room: the farthest walk from it
  const start = rooms.slice().sort((a, b) => (a.x0 + (size - a.y1)) - (b.x0 + (size - b.y1)))[0];
  const [sx, sy] = mid(start), dist = CM.distances(grid, [sx, sy], (x, y) => grid[y] && grid[y][x] === 0);
  const boss = rooms.filter((r) => r !== start).sort((a, b) => (dist.get(mid(b).join(",")) || 0) - (dist.get(mid(a).join(",")) || 0))[0];
  fl.start = [sx, sy, 0]; fl.pos = [sx, sy]; fl.facing = 0;
  const [bx, by] = mid(boss), far = [boss.x0 + 1, boss.y0 + 1, boss.x1 - 1, boss.y1 - 1];
  const corners = [[far[0], far[1]], [far[2], far[1]], [far[0], far[3]], [far[2], far[3]]].sort((p, q) => (dist.get(q.join(",")) || 0) - (dist.get(p.join(",")) || 0));
  fl.ladder = corners[0]; fl.boss = { x: bx, y: by };
  fl.rooms = rooms.map((r) => Object.assign({}, r, { name: r === start ? "The stair-head" : r === boss ? "The ladder's room" : "A room" }));
  // the floor's monsters: in the rooms but the start's, two or three a room, more as the tower rises
  const depth = CM.towerDepth(n), spawnRnd = new CM.Random(CM.hashSeed(`${seed}:magetower:spawns:${n}`));
  for (const r of rooms) {
    if (r === start) continue;
    const count = (r === boss ? 1 : 2) + (spawnRnd.chance(Math.min(0.8, n / 40)) ? 1 : 0);
    for (let i = 0; i < count; i++) {
      const x = spawnRnd.int(r.x0, r.x1), y = spawnRnd.int(r.y0, r.y1);
      if ((x === fl.ladder[0] && y === fl.ladder[1]) || (x === bx && y === by)) continue;
      const g = depth > 20 ? CM.deepGroup(depth, spawnRnd, 2) : CM.monsterGroup(depth, spawnRnd, 2);
      fl.spawns.push({ x, y, kind: (g[0] && (g[0].kind || g[0].name)) || "Goblin" });
    }
  }
  const bossRnd = new CM.Random(CM.hashSeed(`${seed}:magetower:boss:${n}`)), bg = depth > 20 ? CM.deepGroup(depth, bossRnd, 2) : CM.monsterGroup(depth, bossRnd, 2), words = Object.keys(CM.CHAMPIONS || { frenzied: 1 });
  fl.boss.kind = (bg[0] && (bg[0].kind || bg[0].name)) || "Orc"; fl.boss.word = words[CM.hashSeed(`${seed}:magetower:word:${n}`) % words.length];
  // things lying about: a quiver or two, a draught, in rooms off the way
  for (const r of rooms) { if (r === start || r === boss) continue; const h = CM.hashSeed(`${seed}:magetower:item:${n}:${r.x0},${r.y0}`); if (h % 3 === 0) fl.items.push({ x: r.x0, y: r.y0, kind: h % 2 ? "quiver" : "draught" }); }
  return fl;
};
