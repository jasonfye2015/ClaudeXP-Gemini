"use strict";
// The Fortress (the fourteenth update): twenty floors of maze under a black keep in the Wood, for one fighter, played as
// a gauntlet - seen from above, in real time: walls of keyed doors that open with a key carried, lairs that keep sending
// their monsters until they are broken, draughts and gold on the floors, and the stairs down somewhere in the maze. On
// the twentieth floor the Iron Marshal holds the way out. 61h-fortress.js says who goes in and what is kept; the window
// draws it (76d-fortress.js). CM.FortRun steps on a fixed clock, so the same inputs give the same run.
//
//   run.update(dt, input)   input: { up, down, left, right, attack, aim (radians or null), bomb (pressed once) }
//   run.events              what happened, for the window's sounds (emptied by the window)
//
// Positions are in tiles (x east, y south); a tile is 0 (floor), 1 (wall) or 2 (a door).
CM.FORT_FLOORS = 20;
CM.FT = {
  step: 1 / 60, speed: 4.3, radius: 0.3, reach: 1.3, arc: 2.1, swingCd: 0.38, monR: 0.34, monReach: 0.78, monCd: 1.15,
  xpShare: 0.4, bombReach: 6.5, genHp: 14, genPer: 5, genEvery: 4.2, genNear: 10, genCap: 3, hit: 0.55, draught: 0.4, level: 1, levelPer: 1.0,
};
CM.FORT_FIGHTERS = ["Knight", "Paladin", "Rogue", "Monk"];
CM.FORT_MARSHAL = { name: "The Iron Marshal", colour: "#3A3A46", body: "tall", head: "helm", eyes: "#FF4020", extras: ["sword", "shield"], speed: 9, ability: "charge" };
CM.fortDepth = (n) => Math.min(CM.BOTTOM || 50, Math.max(1, Math.round(n * 2)));
CM.fortFloorName = (n) => (n === CM.FORT_FLOORS ? "The Fortress, the Marshal's hall" : `The Fortress, floor ${n}`);
// who may go in: a fighter (Knight, Paladin, Rogue, Monk), or a Ranger with a blade instead of a bow
CM.fortWhyNot = (h) => {
  if (!h) return "No one.";
  if (h.hp <= 0) return `${h.name} has fallen.`;
  const bow = h.weapon && h.weapon.props && h.weapon.props.bow;
  if (CM.FORT_FIGHTERS.includes(h.cls) || (h.cls === "Ranger" && !bow)) return "";
  return `${h.name} the ${h.cls} is no one to send into a gauntlet: the Fortress is for those who fight hand to hand.`;
};

// ---- a floor: a maze of two-wide halls on a coarse grid, some opened into rooms; doors across the way down, a key for
// each somewhere before it; closets of treasure behind doors of their own (with a key of their own); lairs, monsters,
// draughts, gold, a chest now and then, the stairs at the far end ----
CM.makeFortFloor = function (n, seed) {
  const rnd = new CM.Random(CM.hashSeed(`${seed}:fortress:${n}`)), cs = Math.min(17, 10 + Math.floor(n / 3)), size = cs * 3 + 1;
  const grid = []; for (let y = 0; y < size; y++) grid.push(new Array(size).fill(1));
  const cellTiles = (i, j) => [[1 + 3 * i, 1 + 3 * j], [2 + 3 * i, 1 + 3 * j], [1 + 3 * i, 2 + 3 * j], [2 + 3 * i, 2 + 3 * j]];
  const passage = (i, j, di, dj) => (di ? [[3 + 3 * Math.min(i, i + di), 1 + 3 * j], [3 + 3 * Math.min(i, i + di), 2 + 3 * j]] : [[1 + 3 * i, 3 + 3 * Math.min(j, j + dj)], [2 + 3 * i, 3 + 3 * Math.min(j, j + dj)]]);
  for (let j = 0; j < cs; j++) for (let i = 0; i < cs; i++) for (const [x, y] of cellTiles(i, j)) grid[y][x] = 0;
  // the maze: a walk that never crosses itself
  const seen = new Set(["0,0"]), stack = [[0, 0]], D = [[1, 0], [-1, 0], [0, 1], [0, -1]];
  while (stack.length) {
    const [i, j] = stack[stack.length - 1], next = rnd.shuffle(D.slice()).filter(([di, dj]) => i + di >= 0 && i + di < cs && j + dj >= 0 && j + dj < cs && !seen.has(`${i + di},${j + dj}`));
    if (!next.length) { stack.pop(); continue; }
    const [di, dj] = next[0]; for (const [x, y] of passage(i, j, di, dj)) grid[y][x] = 0;
    seen.add(`${i + di},${j + dj}`); stack.push([i + di, j + dj]);
  }
  // rooms: blocks of cells opened into halls (the gauntlet's open floors), and a few more ways through
  const rooms = [];
  for (let k = 0; k < 3 + Math.floor(n / 4); k++) {
    const w = rnd.int(2, 3), h = rnd.int(2, 3), i0 = rnd.int(0, cs - w), j0 = rnd.int(0, cs - h);
    for (let y = 1 + 3 * j0; y <= 3 * (j0 + h) - 1; y++) for (let x = 1 + 3 * i0; x <= 3 * (i0 + w) - 1; x++) grid[y][x] = 0;
    rooms.push({ x0: 1 + 3 * i0, y0: 1 + 3 * j0, x1: 3 * (i0 + w) - 1, y1: 3 * (j0 + h) - 1 });
  }
  for (let k = 0; k < Math.floor(cs * 0.8); k++) { const i = rnd.int(0, cs - 2), j = rnd.int(0, cs - 1), [di, dj] = rnd.chance(0.5) ? [1, 0] : [0, 1]; if (j + dj < cs) for (const [x, y] of passage(i, j, di, dj)) grid[y][x] = 0; }
  const fl = { n, size, grid, items: [], lairs: [], spawns: [], doors: [], rooms, start: [1.5, 1.5] };
  const open = (x, y) => grid[y] && grid[y][x] === 0;
  const dist = (from, blocked) => { const d = new Map([[`${from[0]},${from[1]}`, 0]]), q = [from]; while (q.length) { const [x, y] = q.shift(), k = d.get(`${x},${y}`); for (const [dx, dy] of D) { const nx = x + dx, ny = y + dy, key = `${nx},${ny}`; if (!open(nx, ny) || d.has(key) || (blocked && blocked.has(key))) continue; d.set(key, k + 1); q.push([nx, ny]); } } return d; };
  const d0 = dist([1, 1]);
  let far = [1, 1], farD = -1; for (const [k, v] of d0) { const [x, y] = k.split(",").map(Number), score = v + (x + y - 2) * 1.5; if (x % 3 && y % 3 && score > farD) { farD = score; far = [x, y]; } }   // (far by the walk, and across the floor)
  fl.stairs = far;
  // the way down, and doors across it where the way must go through them
  const path = []; { let cur = far; const dS = d0; while (cur[0] !== 1 || cur[1] !== 1) { path.push(cur); const k = dS.get(`${cur[0]},${cur[1]}`); const nb = D.map(([dx, dy]) => [cur[0] + dx, cur[1] + dy]).find(([x, y]) => dS.get(`${x},${y}`) === k - 1); if (!nb) break; cur = nb; } path.reverse(); }
  const isPassage = (x, y) => (x % 3 === 0) !== (y % 3 === 0);    // (a tile in a wall line, opened: where a door can stand)
  const groupAt = (x, y) => { const out = [[x, y]]; for (const [dx, dy] of D) { const nx = x + dx, ny = y + dy; if (open(nx, ny) && isPassage(nx, ny) && (nx % 3 === 0) === (x % 3 === 0) && (ny % 3 === 0) === (y % 3 === 0)) out.push([nx, ny]); } return out; };
  const want = Math.min(4, 1 + Math.floor(n / 5)), blocked = new Set(), doorKeys = [];
  for (let k = 1; k <= want; k++) {
    const target = Math.floor((path.length * k) / (want + 1));
    for (let t = target; t < path.length - 4; t++) {
      const [x, y] = path[t]; if (!isPassage(x, y) || blocked.has(`${x},${y}`)) continue;
      const g = groupAt(x, y), trial = new Set(blocked); for (const [gx, gy] of g) trial.add(`${gx},${gy}`);
      if (dist([1, 1], trial).has(`${far[0]},${far[1]}`)) continue;     // (not a door the way must go through)
      for (const [gx, gy] of g) { blocked.add(`${gx},${gy}`); grid[gy][gx] = 2; }
      fl.doors.push(g); doorKeys.push(g); break;
    }
  }
  // a key for each door, in the part of the maze open before it (with the doors after it still shut)
  const taken = new Set([`1,1`, `${far[0]},${far[1]}`]);
  const place = (cands, kind, extra) => { const pool = cands.filter(([x, y]) => !taken.has(`${x},${y}`) && !isPassage(x, y)); if (!pool.length) return null; const [x, y] = pool[Math.floor(rnd.next() * pool.length)]; taken.add(`${x},${y}`); const it = Object.assign({ x, y, kind }, extra || {}); fl.items.push(it); return it; };
  for (let k = 0; k < doorKeys.length; k++) {
    const shut = new Set(); for (let m = k; m < doorKeys.length; m++) for (const [x, y] of doorKeys[m]) shut.add(`${x},${y}`);
    for (let m = 0; m < k; m++) for (const [x, y] of doorKeys[m]) grid[y][x] = 0;   // (the earlier doors open, for the reckoning)
    const reach = [...dist([1, 1], shut)].filter(([, v]) => v > 8).sort((a, b) => b[1] - a[1]), half = reach.slice(0, Math.max(1, Math.ceil(reach.length * 0.5)));
    place(half.map(([key]) => key.split(",").map(Number)), "key");
    for (let m = 0; m < k; m++) for (const [x, y] of doorKeys[m]) grid[y][x] = 2;
  }
  // closets of treasure: a dead end shut behind a door of its own, its key loose somewhere before it
  const deadEnds = []; for (let j = 0; j < cs; j++) for (let i = 0; i < cs; i++) { const ways = D.filter(([di, dj]) => { if (i + di < 0 || i + di >= cs || j + dj < 0 || j + dj >= cs) return false; return passage(i, j, di, dj).every(([x, y]) => grid[y][x] !== 1); }); if (ways.length === 1 && (i || j) && !(Math.floor(far[0] / 3) === i && Math.floor(far[1] / 3) === j)) deadEnds.push([i, j, ways[0]]); }
  rnd.shuffle(deadEnds);
  for (const [i, j, [di, dj]] of deadEnds.slice(0, 1 + Math.floor(n / 7))) {
    const g = passage(i, j, di, dj); if (g.some(([x, y]) => grid[y][x] !== 0) || cellTiles(i, j).some(([x, y]) => taken.has(`${x},${y}`))) continue;
    const shut = new Set(blocked); for (const [x, y] of g) shut.add(`${x},${y}`);
    const before = [...dist([1, 1], shut)].filter(([, v]) => v > 6).map(([key]) => key.split(",").map(Number));
    if (!before.length) continue;
    for (const [x, y] of g) grid[y][x] = 2; fl.doors.push(g);
    place(before, "key"); const [tx, ty] = cellTiles(i, j)[rnd.int(0, 3)]; taken.add(`${tx},${ty}`); fl.items.push({ x: tx, y: ty, kind: "chest" });
    for (const [x, y] of cellTiles(i, j)) if (!taken.has(`${x},${y}`) && rnd.chance(0.5)) { taken.add(`${x},${y}`); fl.items.push({ x, y, kind: "gold", big: true }); }
  }
  // the rest: draughts, gold, a fire flask now and then, a chest on some floors; lairs and monsters away from the start
  const all = []; for (let y = 1; y < size - 1; y++) for (let x = 1; x < size - 1; x++) if (open(x, y)) all.push([x, y]);
  const away = all.filter(([x, y]) => Math.abs(x - 1) + Math.abs(y - 1) > 10);
  for (let k = 0; k < 3 + Math.floor(cs / 4); k++) place(away, "draught");
  for (let k = 0; k < 6 + Math.floor(n / 2); k++) place(away, "gold");
  if (n % 2 === 1 || rnd.chance(0.4)) place(away, "flask");
  if (n % 5 === 0 || rnd.chance(0.25)) place(away, "chest");
  const depth = CM.fortDepth(n), pick = (r) => { const g = depth > 20 ? CM.deepGroup(depth, r, 2) : CM.monsterGroup(depth, r, 2); return (g[0] && (g[0].kind || g[0].name)) || "Goblin"; };
  for (let k = 0; k < 3 + Math.floor(n / 2); k++) { const it = place(away, "lair"); if (it) { fl.items.pop(); fl.lairs.push({ x: it.x, y: it.y, kind: pick(rnd) }); } }
  for (let k = 0; k < 6 + n; k++) { const it = place(away, "mon"); if (it) { fl.items.pop(); fl.spawns.push({ x: it.x, y: it.y, kind: pick(rnd) }); } }
  if (n % 5 === 0 && n < CM.FORT_FLOORS) fl.warden = { x: far[0], y: far[1], kind: pick(rnd) };   // (a champion at the stairs, every fifth floor)
  if (n === CM.FORT_FLOORS) fl.marshal = { x: far[0], y: far[1] };
  return fl;
};

// ---- the run: one fighter on one floor ----
CM.FortRun = class {
  constructor(game, heroIndex, n) {
    this.game = game; this.heroIndex = heroIndex; this.hero = game.party[heroIndex]; this.n = n;
    this.fl = CM.makeFortFloor(n, game.seed); this.grid = this.fl.grid;
    this.x = this.fl.start[0]; this.y = this.fl.start[1]; this.face = 0; this.t = 0; this.acc = 0; this.cool = 0; this.swingAt = -9; this.events = [];
    this.keys = 0; this.flasks = 0; this.gold = 0; this.loot = []; this.xp = 0; this.kills = 0; this.over = null; this.ids = 0; this.doorsOpened = 0; this.lastHurt = -9;
    this.level = Math.max(1, Math.round(CM.FT.level + n * CM.FT.levelPer)); this.rnd = new CM.Random(CM.hashSeed(`${game.seed}:fortrun:${n}`));
    this.items = this.fl.items.map((it) => Object.assign({ taken: false }, it));
    this.mons = this.fl.spawns.map((s) => this.makeMon(s.kind, s.x + 0.5, s.y + 0.5));
    this.lairs = this.fl.lairs.map((L) => ({ id: ++this.ids, x: L.x + 0.5, y: L.y + 0.5, kind: L.kind, hp: CM.FT.genHp + n * CM.FT.genPer, max: CM.FT.genHp + n * CM.FT.genPer, t: this.rnd.next() * CM.FT.genEvery, children: 0, hitAt: -9 }));
    if (this.fl.warden) { const o = this.makeMon(this.fl.warden.kind, this.fl.warden.x + 0.5, this.fl.warden.y + 0.5); o.m.max = o.m.hp = o.m.max * 4; o.m.atk = Math.round(o.m.atk * 1.4); o.m.xp *= 4; o.m.gold *= 4; o.scale = 1.45; o.boss = "warden"; o.name = `the Warden of floor ${n}`; this.mons.push(o); }
    if (this.fl.marshal) { const m = CM.makeMonster(CM.FORT_MARSHAL, this.level + 4, this.rnd); m.max = m.hp = m.max * 12; m.atk = Math.round(m.atk * 1.6); m.xp *= 12; m.gold *= 10; const o = { id: ++this.ids, m, kind: CM.FORT_MARSHAL.name, x: this.fl.marshal.x + 0.5, y: this.fl.marshal.y + 0.5, cd: 1, hitAt: -9, lungeAt: -9, fellAt: null, scale: 2, boss: "marshal", name: "the Iron Marshal", charge: 0, slamT: 6 }; this.mons.push(o); this.marshal = o; }
    this.floorGold = 0; this.floorLoot = [];
    this.flow = null; this.flowT = 0;
  }
  makeMon(kind, x, y) { const K = CM.monsterKind(kind) || CM.monsterKind("Goblin"), m = CM.makeMonster(K, this.level, this.rnd); return { id: ++this.ids, m, kind: K.name, x, y, cd: 0.5 + this.rnd.next(), hitAt: -9, lungeAt: -9, fellAt: null, ranged: K.ability === "ranged", shotT: 1 + this.rnd.next() * 2 }; }
  living() { return this.mons.filter((o) => o.m.hp > 0); }
  tile(x, y) { const r = this.grid[Math.floor(y)]; return r === undefined ? 1 : r[Math.floor(x)] === undefined ? 1 : r[Math.floor(x)]; }
  free(x, y, r) { return this.tile(x - r, y - r) === 0 && this.tile(x + r, y - r) === 0 && this.tile(x - r, y + r) === 0 && this.tile(x + r, y + r) === 0; }
  clear(x0, y0, x1, y1) { const n = Math.ceil(Math.hypot(x1 - x0, y1 - y0) * 3); for (let i = 1; i < n; i++) if (this.tile(x0 + ((x1 - x0) * i) / n, y0 + ((y1 - y0) * i) / n) !== 0) return false; return true; }
  // the way to the hero from every tile, kept fresh a few times a second: the monsters follow it down
  flowField() {
    const hx = Math.floor(this.x), hy = Math.floor(this.y), key = `${hx},${hy}`;
    if (this.flow && this.flow.key === key && this.t - this.flowT < 0.5) return this.flow;
    const S = this.fl.size, d = new Int16Array(S * S).fill(-1), q = [hx + hy * S]; d[q[0]] = 0;
    for (let h = 0; h < q.length; h++) { const i = q[h], x = i % S, y = (i - x) / S; if (d[i] > 40) continue; for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) { const nx = x + dx, ny = y + dy, j = nx + ny * S; if (nx < 0 || ny < 0 || nx >= S || ny >= S || d[j] >= 0 || this.grid[ny][nx] !== 0) continue; d[j] = d[i] + 1; q.push(j); } }
    this.flowT = this.t; return (this.flow = { key, d, S });
  }
  // ---- the clock ----
  update(dt, input = {}) {
    if (this.over) return;
    this.acc += Math.min(0.25, dt); if (input.bomb) this.bombWanted = true;
    while (this.acc >= CM.FT.step) { this.acc -= CM.FT.step; this.tick(CM.FT.step, input); if (this.over) break; }
  }
  tick(dt, input) {
    const T = CM.FT, h = this.hero; this.t += dt; this.cool = Math.max(0, this.cool - dt);
    let mx = (input.right ? 1 : 0) - (input.left ? 1 : 0), my = (input.down ? 1 : 0) - (input.up ? 1 : 0);
    if (mx || my) { const k = Math.hypot(mx, my); mx /= k; my /= k; if (input.aim === null || input.aim === undefined) this.face = Math.atan2(my, mx); }
    if (input.aim !== null && input.aim !== undefined) this.face = input.aim;
    const sp = T.speed * dt, nx = this.x + mx * sp, ny = this.y + my * sp, R = T.radius;
    if (this.free(nx, this.y, R)) this.x = nx; else this.bump(nx, this.y);
    if (this.free(this.x, ny, R)) this.y = ny; else this.bump(this.x, ny);
    if (input.attack && this.cool <= 0) this.swing();
    if (this.bombWanted) { this.bombWanted = false; this.throwFlask(); }
    this.pickUp();
    for (const o of this.mons) if (o.m.hp > 0) this.stepMon(o, dt);
    for (const L of this.lairs) if (L.hp > 0) this.stepLair(L, dt);
    if (this.bolts) { for (const b of this.bolts) { b.x += b.vx * dt; b.y += b.vy * dt; b.life -= dt; if (this.tile(b.x, b.y) !== 0) b.life = 0; else if (Math.hypot(b.x - this.x, b.y - this.y) < 0.4) { b.life = 0; this.hurt(b.from, this.game.damage(Math.floor(b.from.m.atk / 2), 0, this.heroDf()) * 0.8); } } this.bolts = this.bolts.filter((b) => b.life > 0); }
    if (h.hp <= 0) { h.hp = 0; this.over = "dead"; this.events.push({ kind: "dead" }); }
  }
  // walked into a door: a key opens it, and the whole of it
  bump(x, y) {
    const r = CM.FT.radius;
    for (const [cx, cy] of [[x - r, y - r], [x + r, y - r], [x - r, y + r], [x + r, y + r]].map(([a, b]) => [Math.floor(a), Math.floor(b)])) {
      if (!this.grid[cy] || this.grid[cy][cx] !== 2) continue;
      if (!this.keys) { if (this.t - (this.lockedSaid || -9) > 2) { this.lockedSaid = this.t; this.events.push({ kind: "locked" }); } return; }
      const door = this.fl.doors.find((g) => g.some(([gx, gy]) => gx === cx && gy === cy)) || [[cx, cy]];
      for (const [gx, gy] of door) this.grid[gy][gx] = 0;
      this.keys -= 1; this.doorsOpened += 1; this.flow = null; this.events.push({ kind: "door", at: [cx, cy] }); return;
    }
  }
  heroDf() { return this.game.effective(this.hero).df + (CM.gearDefence ? CM.gearDefence(this.hero) : 0); }
  // the swing: everything in the arc in front, within reach, struck
  swing() {
    const T = CM.FT, g = this.game, h = this.hero, eff = g.effective(h), power = h.weapon ? h.weapon.power || 1 : 1;
    this.cool = T.swingCd; this.swingAt = this.t; let hit = 0;
    const inArc = (x, y, r) => { const d = Math.hypot(x - this.x, y - this.y); if (d > T.reach + r) return false; let a = Math.atan2(y - this.y, x - this.x) - this.face; a = Math.atan2(Math.sin(a), Math.cos(a)); return Math.abs(a) <= T.arc / 2 || d < 0.45; };
    for (const o of this.living()) if (inArc(o.x, o.y, T.monR * (o.scale || 1))) {
      const dmg = Math.max(1, Math.round(g.damage(eff.atk, power, o.m.df) * (h.cls === "Rogue" && this.rnd.chance(0.25) ? 2 : 1)));
      o.m.hp -= dmg; o.hitAt = this.t; hit++;
      const k = Math.hypot(o.x - this.x, o.y - this.y) || 1, push = o.boss ? 0.05 : 0.22; if (this.free(o.x + ((o.x - this.x) / k) * push, o.y + ((o.y - this.y) / k) * push, T.monR)) { o.x += ((o.x - this.x) / k) * push; o.y += ((o.y - this.y) / k) * push; }   // (a blow knocks it back)
      this.events.push({ kind: "hit", at: [o.x, o.y], amount: dmg, mon: o });
      if (o.m.hp <= 0) this.fall(o);
    }
    for (const L of this.lairs) if (L.hp > 0 && inArc(L.x, L.y, 0.4)) { const dmg = Math.max(1, Math.round(g.damage(eff.atk, power, 0) * 0.6)); L.hp -= dmg; L.hitAt = this.t; hit++; this.events.push({ kind: "lairhit", at: [L.x, L.y], amount: dmg }); if (L.hp <= 0) { this.xp += 12 + this.n * 4; this.events.push({ kind: "lairdown", at: [L.x, L.y] }); } }
    this.events.push({ kind: "swing", hit });
  }
  fall(o) {
    o.fellAt = this.t; this.kills += 1; this.xp += o.m.xp; const gold = Math.round(o.m.gold * 0.5); this.gold += gold; this.floorGold += gold;
    this.events.push({ kind: "die", at: [o.x, o.y], mon: o });
    if (o.lair) o.lair.children = Math.max(0, o.lair.children - 1);
    if (o.boss) {
      const rnd = new CM.Random(CM.hashSeed(`${this.game.seed}:fortboss:${this.n}`)), depth = CM.fortDepth(this.n) + (o.boss === "marshal" ? 6 : 2), item = CM.affix(CM.makeItem(depth, rnd), depth + 2, rnd); item.unknown = false;
      this.loot.push(item); this.floorLoot.push(item); this.events.push({ kind: "bossdown", mon: o, item });
    }
  }
  // the monsters: down the flow toward the hero, a blow when close, a bolt for those who shoot
  stepMon(o, dt) {
    const T = CM.FT, d = Math.hypot(this.x - o.x, this.y - o.y), R = T.monR * Math.min(1.4, o.scale || 1);
    o.cd = Math.max(0, o.cd - dt);
    if (d > 16 && !o.boss) return;                                      // (asleep, far off)
    if (o.boss === "marshal") this.marshalAct(o, dt, d);
    const reach = T.monReach + (o.scale ? (o.scale - 1) * 0.35 : 0);
    if (d < reach) { if (o.cd <= 0) { o.cd = T.monCd * (o.boss ? 0.8 : 1); o.lungeAt = this.t; this.hurt(o, this.game.damage(Math.floor(o.m.atk / 2), 0, this.heroDf())); } return; }
    if (o.ranged && d < 7 && this.clear(o.x, o.y, this.x, this.y)) { o.shotT -= dt; if (o.shotT <= 0) { o.shotT = 2.4; const a = Math.atan2(this.y - o.y, this.x - o.x); (this.bolts = this.bolts || []).push({ x: o.x, y: o.y, vx: Math.cos(a) * 6, vy: Math.sin(a) * 6, life: 2, from: o }); this.events.push({ kind: "monshoot", mon: o }); } if (d < 4) return; }
    const F = this.flowField(), S = F.S, here = F.d[Math.floor(o.x) + Math.floor(o.y) * S];
    let tx = this.x, ty = this.y;
    if (!(d < 1.6 && this.clear(o.x, o.y, this.x, this.y)) && here > 0) {
      let best = here, bx = null, by = null; const cx = Math.floor(o.x), cy = Math.floor(o.y);
      for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) { const v = F.d[cx + dx + (cy + dy) * S]; if (v >= 0 && v < best) { best = v; bx = cx + dx + 0.5; by = cy + dy + 0.5; } }
      if (bx !== null) { tx = bx; ty = by; }
    } else if (here < 0 && !(d < 2)) return;                            // (no way to the hero from here)
    const a = Math.atan2(ty - o.y, tx - o.x), sp = (1.2 + (o.m.speed || 10) * 0.12) * (o.charging ? 2.6 : 1) * dt, nx = o.x + Math.cos(a) * sp, ny = o.y + Math.sin(a) * sp;
    const ok = (x, y) => this.free(x, y, R * 0.9) && Math.hypot(x - this.x, y - this.y) > T.radius + R * 0.8 && !this.mons.some((q) => q !== o && q.m.hp > 0 && Math.hypot(q.x - x, q.y - y) < R * 1.5 && Math.hypot(q.x - this.x, q.y - this.y) < Math.hypot(o.x - this.x, o.y - this.y));
    if (ok(nx, o.y)) o.x = nx;
    if (ok(o.x, ny)) o.y = ny;
  }
  // the Iron Marshal: he charges across his hall, and when he strikes the floor the ring of it hurts
  marshalAct(o, dt, d) {
    o.slamT -= dt;
    if (o.charging) { o.charging -= dt; if (o.charging <= 0) o.charging = 0; }
    else if (d > 3 && d < 9 && o.cd <= 0 && this.rnd.chance(dt * 0.6)) { o.charging = 0.9; this.events.push({ kind: "charge", mon: o }); }
    if (o.slamT <= 0) {
      o.slamT = o.m.hp < o.m.max / 2 ? 4 : 6; this.events.push({ kind: "slam", at: [o.x, o.y] });
      if (d < 3.2) this.hurt(o, this.game.damage(Math.floor(o.m.atk / 2), 0, this.heroDf()) * 1.3);
      if (o.m.hp < o.m.max / 2) for (let k = 0; k < 2; k++) { const m = this.makeMon(this.fl.lairs[0] ? this.fl.lairs[0].kind : "Skeleton", o.x + (k ? 1 : -1), o.y); if (this.free(m.x, m.y, CM.FT.monR)) this.mons.push(m); }
    }
  }
  hurt(o, dmg) {
    const h = this.hero; dmg = Math.max(1, Math.round(dmg * CM.FT.hit * Math.pow(Math.min(2, Math.max(0.3, this.level / Math.max(1, h.level))), 0.6)));
    h.hp -= dmg; this.lastHurt = this.t; this.events.push({ kind: "hurt", amount: dmg, mon: o });
  }
  // a lair sends out its kind while the hero is near and its brood is small
  stepLair(L, dt) {
    if (Math.hypot(this.x - L.x, this.y - L.y) > CM.FT.genNear) return;
    L.t -= dt; if (L.t > 0) return;
    L.t = Math.max(1.6, CM.FT.genEvery - this.n * 0.08);
    if (L.children >= CM.FT.genCap + Math.floor(this.n / 7)) return;
    for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) { const x = L.x + dx * 0.8, y = L.y + dy * 0.8; if (this.free(x, y, CM.FT.monR)) { const o = this.makeMon(L.kind, x, y); o.lair = L; o.m.xp = Math.ceil(o.m.xp / 2); o.m.gold = Math.ceil(o.m.gold / 3); L.children++; this.mons.push(o); this.events.push({ kind: "spawn", at: [x, y] }); return; } }
  }
  // a fire flask thrown: everything near takes the fire
  throwFlask() {
    if (!this.flasks) return; this.flasks -= 1; const g = this.game, eff = g.effective(this.hero);
    this.events.push({ kind: "flask", at: [this.x, this.y] });
    for (const o of this.living()) if (Math.hypot(o.x - this.x, o.y - this.y) < CM.FT.bombReach && this.clear(this.x, this.y, o.x, o.y)) { const dmg = Math.round((eff.atk * 2 + 8 + this.n * 3) * (o.boss ? 0.5 : 1)); o.m.hp -= dmg; o.hitAt = this.t; this.events.push({ kind: "hit", at: [o.x, o.y], amount: dmg, mon: o }); if (o.m.hp <= 0) this.fall(o); }
    for (const L of this.lairs) if (L.hp > 0 && Math.hypot(L.x - this.x, L.y - this.y) < CM.FT.bombReach) { L.hp -= 20 + this.n * 3; L.hitAt = this.t; if (L.hp <= 0) { this.xp += 12 + this.n * 4; this.events.push({ kind: "lairdown", at: [L.x, L.y] }); } }
  }
  // walked over: taken
  pickUp() {
    const h = this.hero;
    for (const it of this.items) {
      if (it.taken || Math.hypot(it.x + 0.5 - this.x, it.y + 0.5 - this.y) > 0.6) continue;
      it.taken = true;
      if (it.kind === "key") this.keys += 1;
      else if (it.kind === "draught") h.hp = Math.min(h.max, h.hp + Math.ceil(h.max * CM.FT.draught));
      else if (it.kind === "flask") this.flasks += 1;
      else if (it.kind === "gold") { const v = Math.round((it.big ? 30 : 10) * (1 + this.n * 0.35) * (0.7 + this.rnd.next() * 0.6)); this.gold += v; this.floorGold += v; it.value = v; }
      else if (it.kind === "chest") { const rnd = new CM.Random(CM.hashSeed(`${this.game.seed}:fortchest:${this.n}:${it.x},${it.y}`)), depth = CM.fortDepth(this.n), item = CM.affix(CM.makeItem(depth, rnd), depth + 1, rnd); item.unknown = false; this.loot.push(item); this.floorLoot.push(item); it.item = item; }
      this.events.push({ kind: "pickup", item: it });
    }
  }
  // the stairs: at them, and on the last floor the Marshal down
  stairsOpen() { return !this.marshal || this.marshal.m.hp <= 0; }
  atStairs() { const S = this.fl.stairs; return this.stairsOpen() && Math.hypot(S[0] + 0.5 - this.x, S[1] + 0.5 - this.y) < 0.9; }
  bossInSight() { return this.living().find((o) => o.boss && Math.hypot(o.x - this.x, o.y - this.y) < 9) || null; }
};
