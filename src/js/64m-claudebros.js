"use strict";
// Super Claude Bros (the seventeenth update), for fun: a pipe in the Square drops one of the party into a side-on world
// of four levels - 1-1 the Meadow Road, 1-2 Under the Hill, 1-3 the Treetops, 1-4 the Brass Keep - to run and jump to
// the banner pole at each level's end. Coins (from the air and from crates knocked from below) are gold; the hero's
// own weapon or spell still kills, and so does landing on a foe's head; every foe gives experience. The Brass Warden
// waits at the end of the Keep. The levels are drawn here in tiles, made by small builders so they stay sound; the
// rules for going in and coming out are 61j-pipe.js, and the window draws it (76g-claudebros.js).
//
//   run.update(dt, input)   input: { left, right, jump, run, attack }
//   run.events              what happened, for the window's sounds (emptied by the window)
CM.BR = { H: 14, step: 1 / 60, gravity: 38, jumpV: 17.5, walk: 5.2, sprint: 8.2, accel: 40, air: 22, w: 0.7, h: 1.5, coinGold: 2, hit: 0.15, bossHit: 0.25, invuln: 1.3, swing: 0.32, bolt: 0.45, xpShare: 0.5 };
CM.BR_SOLID = new Set(["#", "B", "C", "K", "=", "S", "W", "J"]);
CM.BR_LEVELS = [
  { id: "1-1", name: "The Meadow Road", sky: ["#7EC8F0", "#D8F0FF"], ground: "meadow" },
  { id: "1-2", name: "Under the Hill", sky: ["#0E0A12", "#1E1624"], ground: "cave" },
  { id: "1-3", name: "The Treetops", sky: ["#F0B878", "#FCE8C8"], ground: "trees" },
  { id: "1-4", name: "The Brass Keep", sky: ["#1A0A0A", "#3A1610"], ground: "keep" },
];
// the builders: a grid of characters, H rows; the ground's top is row 12 unless said otherwise
CM.brBuild = function (index) {
  const H = CM.BR.H, W = [212, 196, 204, 168][index], g = Array.from({ length: H }, () => new Array(W).fill(" ")), ents = [];
  const set = (x, y, c) => { if (x >= 0 && x < W && y >= 0 && y < H) g[y][x] = c; };
  const ground = (x0, x1, top = 12, c = "#") => { for (let x = x0; x <= x1; x++) for (let y = top; y < H; y++) set(x, y, c); };
  const row = (x0, x1, y, c) => { for (let x = x0; x <= x1; x++) set(x, y, c); };
  const coins = (x0, x1, y) => { for (let x = x0; x <= x1; x++) set(x, y, "o"); };
  const stairs = (x, n, up = true, top = 12, c = "S") => { for (let i = 0; i < n; i++) for (let k = 0; k <= i; k++) set(up ? x + i : x + n - 1 - i, top - 1 - k, c); };
  const foe = (x, y, kind) => ents.push({ x, y, kind });
  const draught = (x, y) => set(x, y, "h");                               // (a draught to mend: the only healing down here)
  const pole = (x, top = 12) => { for (let y = top - 9; y < top; y++) set(x, y, "|"); set(x, top - 10, "F"); set(x, top, "S"); ents.push({ x, y: top - 1, kind: "pole" }); };
  if (index === 0) {                                                       // 1-1: the Meadow Road - gentle gaps, crates, rats and slimes
    ground(0, 38); ground(42, 70); ground(73, 101); ground(105, 140); ground(144, 211);
    row(14, 18, 8, "B"); set(16, 8, "C"); set(22, 8, "C"); coins(15, 17, 7); foe(20, 11, "rat"); foe(30, 11, "slime");
    row(46, 50, 8, "B"); set(48, 8, "C"); row(52, 56, 5, "B"); set(54, 5, "C"); coins(52, 56, 4); foe(55, 11, "rat"); foe(62, 11, "rat");
    stairs(64, 4); coins(40, 41, 9); coins(71, 72, 9); foe(80, 11, "slime"); foe(88, 11, "rat"); row(84, 90, 8, "B"); set(86, 8, "C"); set(88, 8, "C");
    coins(102, 104, 8); row(110, 116, 9, "="); coins(110, 116, 8); row(120, 125, 6, "="); coins(120, 125, 5); foe(114, 11, "slime"); foe(124, 11, "rat"); foe(132, 11, "rat");
    coins(141, 143, 8); row(150, 153, 8, "B"); set(151, 8, "C"); set(152, 8, "C"); foe(158, 11, "slime"); foe(166, 11, "rat");
    draught(55, 4); draught(122, 5); stairs(176, 8); coins(176, 183, 2); pole(196); ground(197, 211);
  } else if (index === 1) {                                                // 1-2: Under the Hill - a low ceiling, bats, kobolds, tunnels of coins
    ground(0, 195); row(0, 195, 0, "W"); row(0, 195, 1, "W");
    for (const [x0, x1] of [[12, 30], [48, 70], [96, 120], [140, 160]]) row(x0, x1, 2, "W");
    ground(36, 40, 12, " "); ground(78, 81, 12, " "); ground(126, 129, 12, " "); ground(166, 168, 12, " ");   // (pits)
    row(18, 26, 8, "B"); set(20, 8, "C"); set(24, 8, "C"); coins(18, 26, 7); foe(22, 11, "kobold"); foe(28, 6, "bat");
    row(44, 47, 9, "="); coins(44, 47, 8); row(52, 66, 6, "B"); coins(53, 65, 5); foe(58, 11, "kobold"); foe(64, 11, "kobold"); foe(60, 4, "bat");
    stairs(84, 4); stairs(88, 4, false); coins(86, 89, 6); foe(94, 11, "slime"); row(100, 116, 8, "B"); set(104, 8, "C"); set(108, 8, "C"); set(112, 8, "C"); foe(106, 11, "kobold"); foe(110, 5, "bat");
    row(132, 138, 9, "="); coins(132, 138, 8); foe(136, 8, "bat"); row(144, 156, 7, "B"); coins(144, 156, 6); foe(150, 11, "kobold"); foe(154, 11, "kobold");
    draught(60, 5); draught(136, 8); row(170, 176, 9, "="); stairs(178, 6); pole(188);
  } else if (index === 2) {                                                // 1-3: the Treetops - branches over a long drop, archers
    ground(0, 14); ground(194, 203);
    const branch = (x0, x1, y) => { row(x0, x1, y, "="); for (let yy = y + 1; yy < 14; yy++) set(Math.floor((x0 + x1) / 2), yy, "T"); };   // (a branch on its trunk)
    branch(17, 22, 10); coins(18, 21, 9); branch(26, 30, 8); foe(28, 7, "goblin"); branch(34, 40, 10); coins(35, 39, 9); branch(44, 47, 7); coins(44, 47, 6);
    branch(51, 58, 9); foe(56, 8, "slime"); branch(62, 66, 7); foe(64, 4, "bat"); branch(70, 78, 10); coins(71, 77, 9); foe(76, 9, "goblin"); branch(82, 86, 8); branch(90, 96, 6); coins(91, 95, 5);
    branch(100, 104, 9); foe(102, 8, "rat"); branch(108, 114, 7); set(111, 3, "C"); branch(118, 122, 9); coins(118, 122, 8); branch(126, 132, 10); foe(130, 9, "goblin"); foe(128, 5, "bat");
    branch(136, 140, 8); branch(144, 150, 6); coins(145, 149, 5); branch(154, 158, 8); foe(156, 7, "slime"); branch(162, 168, 10); coins(163, 167, 9); branch(172, 176, 8); foe(174, 4, "bat"); branch(180, 186, 10); branch(189, 192, 11);
    draught(93, 5); draught(165, 9); pole(198);
  } else {                                                                 // 1-4: the Brass Keep - lava, fire jets, skeletons, the Warden
    for (let x = 0; x < W; x++) { set(x, 0, "W"); set(x, 1, "W"); }
    ground(0, 20); ground(21, 26, 12, "L"); ground(27, 50); ground(51, 55, 12, "L"); ground(56, 84); ground(85, 90, 12, "L"); ground(91, 120); ground(121, 167);
    row(22, 25, 8, "="); coins(22, 25, 7); set(34, 11, "J"); set(40, 11, "J"); foe(44, 11, "skeleton"); row(52, 54, 8, "="); coins(52, 54, 7);
    row(60, 66, 8, "B"); set(63, 8, "C"); foe(64, 11, "skeleton"); set(72, 11, "J"); foe(78, 11, "kobold"); row(86, 89, 9, "="); coins(86, 89, 8);
    set(96, 11, "J"); set(100, 11, "J"); set(104, 11, "J"); coins(95, 105, 7); foe(110, 11, "skeleton"); foe(116, 11, "skeleton");
    for (let y = 2; y < 9; y++) { set(121, y, "W"); }                      // (the Warden's hall: a low door in)
    draught(53, 7); draught(98, 6); draught(132, 7); draught(152, 7); row(130, 134, 8, "="); row(150, 154, 8, "="); foe(146, 11, "warden"); pole(162);
  }
  return { grid: g, ents, w: W };
};

CM.BrosRun = class {
  constructor(game, heroIndex, levelIndex = 0, carry = null) {
    this.game = game; this.heroIndex = heroIndex; this.hero = game.party[heroIndex]; this.li = levelIndex; this.L = CM.BR_LEVELS[levelIndex];
    const b = CM.brBuild(levelIndex); this.grid = b.grid; this.w = b.w; this.events = []; this.t = 0; this.acc = 0;
    this.p = { x: 2.5, y: 11.99, vx: 0, vy: 0, onGround: true, face: 1, coyote: 0, jumpHeld: false, inv: 0, cool: 0, swingAt: -9, dead: false };
    Object.assign(this, { coins: carry ? carry.coins : 0, xp: carry ? carry.xp : 0, kills: carry ? carry.kills : 0, over: null, cleared: false, shots: [], pops: [] });
    this.arms = CM.brArms(this.hero); this.foes = []; this.pole = null;
    for (const e of b.ents) { if (e.kind === "pole") { this.pole = e; continue; } this.foes.push(this.makeFoe(e)); }
    this.coinsHere = this.grid.reduce((s, r) => s + r.filter((c) => c === "o").length, 0);
  }
  makeFoe(e) {
    const D = { rat: [1, 2.2, 0.8, 0.6, "Giant Rat"], slime: [1, 1.4, 0.9, 0.8, "Kobold"], kobold: [1, 3, 0.8, 1.1, "Kobold"], bat: [1, 2.4, 0.8, 0.6, "Wraith"], goblin: [2, 0, 0.8, 1.2, "Goblin"], skeleton: [2, 1.8, 0.8, 1.4, "Skeleton"], warden: [14, 2.6, 2.2, 2.6, "The Brass Warden"] }[e.kind];
    return { kind: e.kind, x: e.x + 0.5, y: e.y + 0.99, vx: -D[1], vy: 0, hp: D[0], max: D[0], speed: D[1], w: D[2], h: D[3], art: D[4], dead: false, deadAt: null, hitAt: -9, t: Math.random() * 3, home: e.y + 0.99, cd: 2, boss: e.kind === "warden" };
  }
  tile(x, y) { const r = this.grid[Math.floor(y)]; if (!r) return y < 0 ? " " : "#"; const c = r[Math.floor(x)]; return c === undefined ? (x < 0 ? "W" : " ") : c; }
  solid(x, y) { return CM.BR_SOLID.has(this.tile(x, y)); }
  boxFree(x, y, w, h) { const x0 = x - w / 2, x1 = x + w / 2 - 1e-6, y0 = y - h, y1 = y - 1e-6; for (let ty = Math.floor(y0); ty <= Math.floor(y1); ty++) for (let tx = Math.floor(x0); tx <= Math.floor(x1); tx++) if (CM.BR_SOLID.has(this.tile(tx, ty))) return false; return true; }
  update(dt, input = {}) { if (this.over) return; this.acc += Math.min(0.1, dt); while (this.acc >= CM.BR.step) { this.acc -= CM.BR.step; this.tick(CM.BR.step, input); if (this.over || this.cleared) break; } }
  tick(dt, input) {
    const B = CM.BR, p = this.p; this.t += dt; p.inv = Math.max(0, p.inv - dt); p.cool = Math.max(0, p.cool - dt);
    if (this.cleared) return;
    // the hero: running, jumping (held for higher), falling
    const want = (input.right ? 1 : 0) - (input.left ? 1 : 0), top = input.run ? B.sprint : B.walk, a = p.onGround ? B.accel : B.air;
    if (want) { p.vx += Math.sign(want * top - p.vx) * Math.min(Math.abs(want * top - p.vx), a * dt); p.face = want; } else p.vx -= Math.sign(p.vx) * Math.min(Math.abs(p.vx), (p.onGround ? 30 : 6) * dt);
    p.coyote = p.onGround ? 0.1 : Math.max(0, p.coyote - dt);
    if (input.jump && !p.jumpHeld && p.coyote > 0) { p.vy = -B.jumpV - Math.abs(p.vx) * 0.25; p.coyote = 0; p.onGround = false; this.events.push({ kind: "jump" }); }
    if (!input.jump && p.vy < -6) p.vy = -6;                               // (let go early: a shorter jump)
    p.jumpHeld = Boolean(input.jump);
    p.vy = Math.min(22, p.vy + B.gravity * dt);
    this.moveBody(p, B.w, B.h, dt, true);
    if (input.attack && p.cool <= 0) this.attack();
    // the coins in the air, the lava, the pits
    for (const [dx, dy] of [[0, -0.3], [0, -1.2]]) { const tx = Math.floor(p.x + dx), ty = Math.floor(p.y + dy), c = this.grid[ty] && this.grid[ty][tx]; if (c === "o") { this.grid[ty][tx] = " "; this.coins += 1; this.events.push({ kind: "coin" }); } else if (c === "h") { this.grid[ty][tx] = " "; const h = this.hero; h.hp = Math.min(h.max, h.hp + Math.ceil(h.max * 0.3)); this.events.push({ kind: "draught" }); } }
    if (this.tile(p.x, p.y - 0.2) === "L" || this.tile(p.x, p.y + 0.05) === "L") { this.events.push({ kind: "lava" }); this.die(); return; }
    if (p.y > B.H + 2) { this.events.push({ kind: "fall" }); this.die(); return; }
    for (let y = 0; y < B.H; y++) { const tx = Math.floor(p.x); if (this.grid[y][tx] === "J" && this.jetOn() && Math.abs(p.x - tx - 0.5) < 0.7 && p.y > y - 3 && p.y <= y + 0.1) this.hurt(B.hit, "fire"); }
    for (const f of this.foes) if (!f.dead) this.stepFoe(f, dt);
    this.foes = this.foes.filter((f) => !f.dead || this.t - f.deadAt < 1);
    for (const s of this.shots) this.stepShot(s, dt);
    this.shots = this.shots.filter((s) => s.life > 0);
    this.pops = this.pops.filter((q) => this.t - q.t < 0.6);
    if (this.pole && Math.abs(p.x - (this.pole.x + 0.5)) < 0.6 && !this.foes.some((f) => f.boss && !f.dead)) { this.cleared = true; this.xp += 40 * (this.li + 1); this.hero.hp = Math.min(this.hero.max, this.hero.hp + Math.ceil(this.hero.max * 0.2)); this.events.push({ kind: "pole", height: Math.max(0, 12 - p.y) }); }
  }
  jetOn() { return this.t % 2.4 < 0.9; }
  // a body moved by its velocity through the tiles; the hero's head knocks crates from below
  moveBody(o, w, h, dt, hero) {
    const nx = o.x + o.vx * dt;
    if (this.boxFree(nx, o.y, w, h)) o.x = nx; else { o.vx = 0; if (!hero) o.bumped = true; }
    if (hero) o.x = Math.max(w / 2, Math.min(this.w - w / 2, o.x));
    const ny = o.y + o.vy * dt; o.onGround = false;
    if (this.boxFree(o.x, ny, w, h)) o.y = ny;
    else {
      if (o.vy > 0) { o.y = Math.floor(ny) - 1e-4 + (Math.floor(ny) === Math.floor(o.y) ? 0 : 0); while (!this.boxFree(o.x, o.y, w, h)) o.y -= 0.01; o.onGround = true; }
      else if (hero) { const ty = Math.floor(ny - h); for (const tx of [Math.floor(o.x - w / 2 + 0.05), Math.floor(o.x), Math.floor(o.x + w / 2 - 0.05)]) this.bump(tx, ty); }
      o.vy = 0;
    }
  }
  bump(tx, ty) {
    const c = this.tile(tx, ty);
    if (c === "C") { this.grid[ty][tx] = "K"; this.coins += 1; this.pops.push({ x: tx + 0.5, y: ty, t: this.t }); this.events.push({ kind: "crate" }); }
    else if (c === "B") this.events.push({ kind: "bump", x: tx, y: ty });
    for (const f of this.foes) if (!f.dead && Math.abs(f.x - tx - 0.5) < 0.8 && Math.abs(f.y - ty) < 0.3) this.kill(f, "bump");   // (a foe standing on a crate knocked from below)
  }
  // the hero's own weapon: a blade swung in front, or a bolt or an arrow
  attack() {
    const p = this.p, A = this.arms; p.cool = A.ranged ? CM.BR.bolt : CM.BR.swing; p.swingAt = this.t;
    if (A.ranged) { this.shots.push({ x: p.x + p.face * 0.5, y: p.y - 0.9, vx: p.face * 16, vy: 0, life: 0.9, from: "hero", kind: A.shot }); this.events.push({ kind: "shoot", shot: A.shot }); return; }
    this.events.push({ kind: "swing" });
    for (const f of this.foes) if (!f.dead && Math.abs(f.x - (p.x + p.face * 0.9)) < 0.6 + f.w / 2 + 0.4 && f.y - f.h < p.y && f.y > p.y - CM.BR.h - 0.2) this.hitFoe(f, 1, "blade");
  }
  hitFoe(f, n, how) {
    if (f.boss && this.t - f.hitAt < 0.6) return;
    f.hp -= n; f.hitAt = this.t; this.events.push({ kind: "hit", boss: f.boss });
    if (f.hp <= 0) this.kill(f, how);
  }
  kill(f, how) {
    if (f.dead) return; f.dead = true; f.deadAt = this.t; this.kills += 1; this.xp += f.boss ? 300 : { rat: 6, slime: 8, kobold: 10, bat: 10, goblin: 14, skeleton: 16 }[f.kind] || 8;
    if (f.boss) { this.coins += 40; this.events.push({ kind: "bossdown" }); } else this.coins += 1;
    this.events.push({ kind: "kill", how, boss: f.boss });
  }
  stepFoe(f, dt) {
    const p = this.p, B = CM.BR; f.t += dt; f.cd -= dt;
    if (Math.abs(f.x - p.x) > 22 && !f.boss) return;                      // (asleep, off the screen)
    if (f.kind === "bat") { f.x -= f.speed * dt * (f.x > p.x ? 1 : -0.3); f.y = f.home - 1 + Math.sin(f.t * 3) * 1.2; }
    else if (f.kind === "goblin") { if (f.cd <= 0 && Math.abs(f.x - p.x) < 11) { f.cd = 2.2; const dir = p.x < f.x ? -1 : 1; this.shots.push({ x: f.x + dir * 0.5, y: f.y - 0.8, vx: dir * 9, vy: 0, life: 1.6, from: "foe", kind: "arrow" }); this.events.push({ kind: "foeshot" }); } f.vy = Math.min(22, f.vy + B.gravity * dt); this.moveBody(f, f.w, f.h, dt, false); }
    else if (f.kind === "warden") {
      const dir = p.x < f.x ? -1 : 1, rage = f.hp < f.max / 2 ? 1.5 : 1;
      if (f.onGround && f.cd <= 0) { f.cd = 2.4 / rage; if (Math.random() < 0.5) { f.vy = -15; f.vx = dir * 5 * rage; this.events.push({ kind: "leap" }); } else { f.vx = dir * 9 * rage; this.events.push({ kind: "charge" }); } }
      else if (f.onGround && Math.abs(f.vx) < 0.5) f.vx = dir * f.speed;
      f.vy = Math.min(22, f.vy + B.gravity * dt); this.moveBody(f, f.w, f.h, dt, false); if (f.bumped) { f.bumped = false; f.vx = -Math.sign(f.vx || 1) * f.speed; }
      f.x = Math.max(122.5, Math.min(160, f.x));
    } else {
      if (f.kind === "slime" && f.onGround && f.cd <= 0) { f.cd = 1.1; f.vy = -9; f.vx = (p.x < f.x ? -1 : 1) * 2.4; }
      if (f.kind === "skeleton" && f.cd <= 0 && Math.abs(f.x - p.x) < 9) { f.cd = 2.6; this.shots.push({ x: f.x, y: f.y - 1.2, vx: (p.x < f.x ? -1 : 1) * 5, vy: -11, life: 2.2, from: "foe", kind: "bone", gravity: true }); this.events.push({ kind: "foeshot" }); }
      f.vy = Math.min(22, f.vy + B.gravity * dt); const vx0 = f.vx; this.moveBody(f, f.w, f.h, dt, false);
      if (f.bumped) { f.bumped = false; f.vx = -vx0; }
      else if (f.onGround && f.kind !== "slime" && !this.solid(f.x + Math.sign(f.vx) * (f.w / 2 + 0.1), f.y + 0.2)) f.vx = -f.vx;   // (they turn at an edge)
      if (f.kind === "slime" && f.onGround) f.vx *= 0.9;
      if (f.y > B.H + 2) { f.dead = true; f.deadAt = this.t; }
    }
    // a touch: a stomp from above, or a hurt
    const pt = p.y - B.h, overlapX = Math.abs(f.x - p.x) < (f.w + B.w) / 2 - 0.05, overlapY = p.y > f.y - f.h && pt < f.y;
    if (overlapX && overlapY) {
      if (p.vy > 2 && p.y - f.y + f.h < 0.55) { p.vy = -11; this.events.push({ kind: "stomp" }); this.hitFoe(f, f.boss ? 2 : f.hp, "stomp"); }
      else this.hurt(f.boss ? B.bossHit : B.hit, f.kind, f.x);
    }
  }
  stepShot(s, dt) {
    s.life -= dt; if (s.gravity) s.vy += 22 * dt; s.x += s.vx * dt; s.y += s.vy * dt;
    if (this.solid(s.x, s.y)) { s.life = 0; return; }
    if (s.from === "hero") { for (const f of this.foes) if (!f.dead && Math.abs(f.x - s.x) < f.w / 2 + 0.2 && s.y > f.y - f.h && s.y < f.y + 0.1) { s.life = 0; this.hitFoe(f, 1, "shot"); return; } }
    else { const p = this.p; if (Math.abs(p.x - s.x) < CM.BR.w / 2 + 0.15 && s.y > p.y - CM.BR.h && s.y < p.y) { s.life = 0; this.hurt(CM.BR.hit, s.kind, s.x); } }
  }
  hurt(frac, what, fromX) {
    const p = this.p, h = this.hero; if (p.inv > 0 || this.over) return;
    const dmg = Math.max(1, Math.round(h.max * frac)); h.hp -= dmg; p.inv = CM.BR.invuln; p.vy = -8; p.vx = (fromX !== undefined && fromX > p.x ? -1 : 1) * 6;
    this.events.push({ kind: "hurt", dmg, what });
    if (h.hp <= 0) this.die();
  }
  die() { if (this.over) return; this.hero.hp = Math.min(this.hero.hp, 0); this.p.dead = true; this.over = "dead"; this.events.push({ kind: "dead" }); }
};
// what the hero fights with here: a blade (the fighters), or a bolt (the casters), or arrows (a bow in hand)
CM.brArms = (h) => { const bow = h.weapon && h.weapon.props && h.weapon.props.bow; if (bow) return { ranged: true, shot: "arrow" }; if ((CM.TOWER_CASTERS || []).includes(h.cls)) return { ranged: true, shot: "bolt" }; return { ranged: false, shot: null }; };
