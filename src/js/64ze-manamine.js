"use strict";
// Mana-Mine (the twenty-eighth big update - v13.8): an arcade game on the Gilded Joker's floor. A miner with a lamp on
// her helmet digs down through four bands of earth. In the hollows wait Mudlings (that drift through the earth as a pair
// of eyes when they cannot reach her) and Ember Newts (that spit fire along their row, through earth and all). Her
// mana-tether shoots a beam along the tunnel: it latches, and each pump swells the creature until it bursts (left
// alone it shrinks back). Boulders in the earth wobble and fall when what holds them is dug away, crushing whatever is
// below - creatures, or her. Two boulders down and a mana crystal shows in the middle for a while. Clear every creature
// to finish the level; the next has more of them, quicker. Three lives. One stake a play: each level cleared pays gold
// back, more for each, every play; and a Claudescryption card for each level the first time it is ever cleared (common to
// four, a stronger common to nine, rare from ten). The same inputs give the same game. The window: 76u-manamine.js.
CM.MM = {
  W: 14, H: 16, SKY: 2, step: 1 / 60, speed: 3.2, digSpeed: 2.2, monSpeed: 2.0, ghostSpeed: 1.2, lives: 3,
  beam: 3, beamTime: 0.25, pumpGap: 0.55, stages: 4, deflate: 1.4, wobble: 0.7, fall: 9, fireReach: 3, fireTime: 0.6, fireWarn: 0.5,
  pay: (n) => 0.15 + 0.1 * n, SCORE: { dig: 10, pop: [200, 300, 400, 500], rock: 1000, crystal: [400, 600, 800, 1000, 1500] },
  DIRS: { up: [0, -1], down: [0, 1], left: [-1, 0], right: [1, 0] },
};
const MM = CM.MM;
MM.Level = class {
  constructor(n, seed, keep) {
    const R = this.rnd = new CM.Random(seed), W = MM.W, H = MM.H; this.n = n; this.t = 0; this.events = []; this.stage = "play"; this.rocksDown = 0; this.crystal = null; this.shots = [];
    Object.assign(this, keep || { score: 0, lives: MM.lives });
    this.dug = Array.from({ length: H }, (_, y) => Array(W).fill(y < MM.SKY));
    // the miner's shaft down the middle to the start, and the creatures' hollows (short tunnels)
    const cx = Math.floor(W / 2); for (let y = MM.SKY; y <= 8; y++) this.dug[y][cx] = true; this.dug[8][cx - 1] = this.dug[8][cx + 1] = true;
    const count = Math.min(10, 3 + n), newts = Math.min(4, Math.floor(n / 2)), used = new Set();
    this.mons = [];
    for (let i = 0; i < count; i++) {
      let x, y, horiz, ok = false; for (let k = 0; k < 200 && !ok; k++) { horiz = R.chance(0.5); x = R.int(1, W - 5); y = R.int(MM.SKY + 2, H - 3); ok = Math.abs(x - cx) > 2 || y > 11; for (let d = -1; d <= 4 && ok; d++) { const cx2 = horiz ? x + d : x, cy2 = horiz ? y : y + d; if (used.has(`${cx2},${cy2}`) || cy2 >= H - 1) ok = false; } }
      for (let d = 0; d < 4; d++) { const tx = horiz ? x + d : x, ty = horiz ? y : y + d; if (ty < H) { this.dug[ty][tx] = true; used.add(`${tx},${ty}`); } }
      this.mons.push({ id: i, kind: i < newts ? "newt" : "mud", x: x + (horiz ? 1 : 0), y: y + (horiz ? 0 : 1), dir: horiz ? "right" : "down", home: [x, y], swell: 0, pumpT: 0, ghost: false, ghostT: 3 + R.next() * 6, fireT: 0, warnT: 0, dead: false });
    }
    this.rocks = []; for (let k = 0; k < 400 && this.rocks.length < 3 + Math.floor(n / 3); k++) { const x = R.int(0, W - 1), y = R.int(MM.SKY + 1, H - 4); if (this.dug[y][x] || this.dug[y + 1][x] || used.has(`${x},${y}`) || this.rocks.some((r) => Math.abs(r.x - x) + Math.abs(r.y - y) < 3)) continue; this.rocks.push({ x, y, fy: y, state: "set", t: 0, crushed: 0 }); }
    this.spawn(); this.speedMul = 1 + Math.min(0.8, (n - 1) * 0.07);
  }
  spawn() { this.p = { x: Math.floor(MM.W / 2), y: 8, fx: Math.floor(MM.W / 2), fy: 8, dir: "right", face: "right", beam: null, dead: 0 }; for (const m of this.mons) if (!m.dead) { m.x = m.home[0] + 1; m.y = m.home[1]; m.fx = m.x; m.fy = m.y; m.swell = 0; m.ghost = false; m.ghostT = 3 + this.rnd.next() * 6; } this.shots = []; }
  solid(x, y) { return x < 0 || x >= MM.W || y < 0 || y >= MM.H || !this.dug[y][x]; }
  rockAt(x, y) { return this.rocks.find((r) => r.state !== "gone" && Math.round(r.fy) === y && r.x === x); }
  live() { return this.mons.filter((m) => !m.dead); }
  // the miner: moves cell to cell along an axis, turning only at a cell's middle, digging what she walks into
  input(dir) { this.want = dir; }
  pump() { this.pumpPressed = true; }
  stepMiner(dt) {
    const P = this.p; if (P.dead) return;
    const at = Math.abs(P.fx - P.x) < 1e-6 && Math.abs(P.fy - P.y) < 1e-6;
    if (P.beam && P.beam.hold !== undefined) { const m = this.mons.find((q) => q.id === P.beam.hold); if (!m || m.dead) P.beam = null; else { if (this.want && this.want !== P.face) P.beam = null; return; } }
    if (at && this.want) { const [dx, dy] = MM.DIRS[this.want], nx = P.x + dx, ny = P.y + dy; P.face = this.want; if (nx >= 0 && nx < MM.W && ny >= MM.SKY - 1 && ny < MM.H && !this.rockAt(nx, ny)) { P.x = nx; P.y = ny; P.dir = this.want; } }
    if (!this.want) return;
    const digging = !this.dug[P.y][P.x], sp = (digging ? MM.digSpeed : MM.speed) * dt;
    const mv = (a, b) => (Math.abs(b - a) <= sp ? b : a + Math.sign(b - a) * sp); P.fx = mv(P.fx, P.x); P.fy = mv(P.fy, P.y);
    if (Math.abs(P.fx - P.x) < 0.5 && Math.abs(P.fy - P.y) < 0.5 && !this.dug[P.y][P.x]) { this.dug[P.y][P.x] = true; this.score += MM.SCORE.dig; this.events.push({ kind: "dig", x: P.x, y: P.y }); }
  }
  // the tether: a beam along the tunnel that latches; each pump after swells the creature
  stepBeam(dt) {
    const P = this.p; if (!this.pumpPressed || P.dead) return; this.pumpPressed = false;
    if (P.beam && P.beam.hold !== undefined) { const m = this.mons.find((q) => q.id === P.beam.hold); if (m && !m.dead) { m.swell += 1; m.pumpT = 0; this.events.push({ kind: "pump", m, stage: m.swell }); if (m.swell >= MM.stages) this.pop(m); } return; }
    const [dx, dy] = MM.DIRS[P.face]; let hit = null, len = 0;
    for (let k = 1; k <= MM.beam; k++) { const x = Math.round(P.fx) + dx * k, y = Math.round(P.fy) + dy * k; if (this.solid(x, y)) break; len = k; hit = this.live().find((m) => Math.round(m.fx) === x && Math.round(m.fy) === y && !m.ghost) || null; if (hit) break; }
    P.beam = { len: hit ? len : Math.max(len, 0.6), t: MM.beamTime, hold: hit ? hit.id : undefined }; if (hit) { hit.swell = Math.max(1, hit.swell + 1); hit.pumpT = 0; this.events.push({ kind: "latch", m: hit }); } else this.events.push({ kind: "beam" });
  }
  pop(m) { m.dead = true; const band = Math.min(3, Math.floor(((m.y - MM.SKY) / (MM.H - MM.SKY)) * 4)); const pts = MM.SCORE.pop[band] * (m.kind === "newt" && (m.dir === "left" || m.dir === "right") ? 2 : 1); this.score += pts; this.p.beam = null; this.events.push({ kind: "pop", m, pts }); this.checkClear(); }
  checkClear() { if (!this.live().length && this.stage === "play") { this.stage = "clear"; this.events.push({ kind: "clear" }); } }
  // the creatures: down the tunnels toward her; when they cannot reach her a while, through the earth as eyes
  stepMon(m, dt) {
    if (m.dead) return; const P = this.p, R = this.rnd;
    if (m.swell > 0) { m.pumpT += dt; if (m.pumpT > MM.deflate) { m.swell -= 1; m.pumpT = 0; if (!m.swell && P.beam && P.beam.hold === m.id) P.beam = null; } return; }
    const sp = (m.ghost ? MM.ghostSpeed : MM.monSpeed) * this.speedMul * dt;
    if (m.ghost) { const dx = P.x - m.fx, dy = P.y - m.fy, d = Math.hypot(dx, dy) || 1; m.fx += (dx / d) * sp; m.fy += (dy / d) * sp; const cx = Math.round(m.fx), cy = Math.round(m.fy); if (Math.hypot(m.fx - cx, m.fy - cy) < 0.15 && !this.solid(cx, cy) && m.ghostT < -1.5) { m.ghost = false; m.x = cx; m.y = cy; m.fx = cx; m.fy = cy; m.ghostT = 4 + R.next() * 6; } m.ghostT -= dt; return; }
    // the newts' fire, along their row, through earth: a breath drawn first
    if (m.kind === "newt") { if (m.warnT > 0) { m.warnT -= dt; if (m.warnT <= 0) { const dir = P.fx > m.fx ? 1 : -1; this.shots.push({ x: m.fx, y: m.y, dir, t: MM.fireTime, m: m.id }); this.events.push({ kind: "fire", m }); } return; } m.fireT -= dt; if (m.fireT <= 0 && Math.round(P.fy) === m.y && Math.abs(P.fx - m.fx) <= MM.fireReach + 0.5) { m.warnT = MM.fireWarn; m.fireT = 3 + R.next() * 2; m.dir = P.fx > m.fx ? "right" : "left"; return; } }
    const at = Math.abs(m.fx - m.x) < 1e-6 && Math.abs(m.fy - m.y) < 1e-6;
    if (at) {
      m.ghostT -= dt * 0;
      // the shortest way through the tunnels to her
      const key = (x, y) => y * MM.W + x, prev = new Map([[key(m.x, m.y), null]]), q = [[m.x, m.y]]; let found = null;
      while (q.length && !found) { const [x, y] = q.shift(); for (const [d, [dx, dy]] of Object.entries(MM.DIRS)) { const nx = x + dx, ny = y + dy; if (this.solid(nx, ny) || ny < MM.SKY || this.rockAt(nx, ny) || prev.has(key(nx, ny))) continue; prev.set(key(nx, ny), [x, y, d]); if (nx === P.x && ny === P.y) { found = [nx, ny]; break; } q.push([nx, ny]); } }
      let step = null; if (found) { let c = found; while (true) { const pr = prev.get(key(...c)); if (!pr || (pr[0] === m.x && pr[1] === m.y)) { step = pr ? pr[2] : null; break; } c = [pr[0], pr[1]]; } }
      if (!step) { const ds = Object.keys(MM.DIRS).filter((d) => { const [dx, dy] = MM.DIRS[d]; return !this.solid(m.x + dx, m.y + dy) && m.y + dy >= MM.SKY && !this.rockAt(m.x + dx, m.y + dy); }); step = ds.includes(m.dir) && R.chance(0.8) ? m.dir : ds.length ? R.pick(ds) : null; m.ghostT -= 0.25; if (m.ghostT <= 0) { m.ghost = true; m.ghostT = 0; this.events.push({ kind: "ghost", m }); return; } }
      else m.ghostT = Math.max(m.ghostT, 2);
      if (step) { m.dir = step; const [dx, dy] = MM.DIRS[step]; m.x += dx; m.y += dy; }
    }
    const mv = (a, b) => (Math.abs(b - a) <= sp ? b : a + Math.sign(b - a) * sp); m.fx = mv(m.fx, m.x); m.fy = mv(m.fy, m.y);
  }
  // boulders: once what holds them is dug away (and she is not right under, pushing up), they wobble, then fall
  stepRocks(dt) {
    for (const r of this.rocks) {
      if (r.state === "gone") continue; const below = Math.round(r.fy) + 1;
      if (r.state === "set") { const P = this.p; if (below < MM.H && this.dug[below][r.x] && !(Math.round(P.fx) === r.x && Math.round(P.fy) === below)) { r.state = "wobble"; r.t = MM.wobble; this.events.push({ kind: "wobble", r }); } continue; }
      if (r.state === "wobble") { r.t -= dt; if (r.t <= 0) { r.state = "fall"; this.dug[r.y][r.x] = true; } continue; }
      if (r.state === "fall") {
        r.fy += MM.fall * dt; const cy = Math.floor(r.fy + 0.99);
        for (const m of this.live()) if (Math.abs(m.fx - r.x) < 0.7 && Math.abs(m.fy - r.fy) < 0.8) { m.dead = true; r.crushed++; this.events.push({ kind: "crush", m }); }
        const P = this.p; if (!P.dead && Math.abs(P.fx - r.x) < 0.7 && Math.abs(P.fy - r.fy) < 0.8) this.lose("rock");
        if (cy >= MM.H || this.solid(r.x, cy)) { r.fy = cy - 1; r.state = "gone"; this.rocksDown += 1; const pts = r.crushed ? MM.SCORE.rock * Math.pow(2, r.crushed - 1) : 0; this.score += pts; this.events.push({ kind: "land", r, pts }); if (this.rocksDown === 2 && !this.crystal) { this.crystal = { x: Math.floor(MM.W / 2), y: 8, t: 10 }; this.events.push({ kind: "crystal" }); } this.checkClear(); }
      }
    }
  }
  lose(why) { const P = this.p; if (P.dead) return; P.dead = 1.6; this.lives -= 1; this.events.push({ kind: "die", why }); }
  update(dt) { for (let s = 0; s < dt / MM.step - 1e-9; s++) this.tick(MM.step); }
  tick(dt) {
    if (this.stage !== "play") return; this.t += dt; const P = this.p;
    if (P.dead) { P.dead -= dt; if (P.dead <= 0) { if (this.lives <= 0) { this.stage = "over"; this.events.push({ kind: "over" }); } else { this.spawn(); this.events.push({ kind: "respawn" }); } } return; }
    this.stepMiner(dt); this.stepBeam(dt); if (P.beam && P.beam.hold === undefined) { P.beam.t -= dt; if (P.beam.t <= 0) P.beam = null; }
    for (const m of this.mons) this.stepMon(m, dt); this.stepRocks(dt);
    for (const s of this.shots) { s.t -= dt; } this.shots = this.shots.filter((s) => s.t > 0);
    for (const s of this.shots) { const reach = MM.fireReach * (1 - s.t / MM.fireTime), x0 = s.x, x1 = s.x + s.dir * reach; if (Math.round(P.fy) === s.y && P.fx >= Math.min(x0, x1) - 0.4 && P.fx <= Math.max(x0, x1) + 0.4) this.lose("fire"); }
    if (this.crystal) { this.crystal.t -= dt; if (this.crystal.t <= 0) this.crystal = null; else if (Math.round(P.fx) === this.crystal.x && Math.round(P.fy) === this.crystal.y) { const pts = MM.SCORE.crystal[Math.min(4, this.n - 1)]; this.score += pts; this.events.push({ kind: "gem", pts }); this.crystal = null; } }
    for (const m of this.live()) if (!m.swell && Math.abs(m.fx - P.fx) < 0.6 && Math.abs(m.fy - P.fy) < 0.6) { this.lose("touch"); break; }
  }
};
Object.assign(CM.Game.prototype, {
  mmState() { return this.cgStore().mm || null; },
  mmClaimed() { const F = this.cgStore(); F.mmCards = F.mmCards || {}; return F.mmCards; },
  mmLevel() { const S = this.mmState(); if (!S || S.stage !== "play") return null; if (!this.mmLive || this.mmLive.key !== `${S.seed}:${S.n}`) { if (this.mmLive && this.mmLive.key && this.mmLive.key.startsWith(`${S.seed}:`)) { const keep = { score: this.mmLive.score, lives: this.mmLive.lives }; this.mmLive = new MM.Level(S.n, CM.hashSeed(`${S.seed}:${S.n}`), keep); this.mmLive.key = `${S.seed}:${S.n}`; } else { S.stage = "done"; S.last = S.last || { level: S.n, won: S.won, lost: true }; this.saveCasino && this.saveCasino(); return null; } } return this.mmLive; },
  mmStart(bet) {
    const S0 = this.mmState(); if (S0 && S0.stage === "play" && this.mmLive && this.mmLive.key && this.mmLive.key.startsWith(`${S0.seed}:`)) return { error: "A game is on." };
    const why = this.cgStake("manamine", bet); if (why) return { error: why };
    const F = this.cgStore(); F.n += 1; F.mm = { stage: "play", n: 1, bet: Math.floor(bet), seed: `${this.seed}:manamine:${F.n}`, won: 0, cards: [] };
    this.mmLive = new MM.Level(1, CM.hashSeed(`${F.mm.seed}:1`)); this.mmLive.key = `${F.mm.seed}:1`; this.saveCasino && this.saveCasino(); return F.mm;
  },
  // a level cleared: its gold (every play), its card (the first time ever); on to the next. The game over: done.
  mmCheck() {
    const S = this.mmState(), L = this.mmLive; if (!S || !L || S.stage !== "play") return null;
    if (L.stage === "clear") {
      const n = S.n, pay = Math.round(S.bet * MM.pay(n)), C = this.mmClaimed(); let card = null;
      if (!C[n]) { card = this.cgTierCard(CM.cardTierFor(n), `Mana-Mine, level ${n} cleared!`, new CM.Random(CM.hashSeed(`${this.seed}:manamine:card:${n}`))); C[n] = card || true; if (card) S.cards.push(card); }
      this.cgPay("manamine", pay); S.won += pay; S.n += 1; S.best = Math.max(S.best || 0, n); this.saveCasino && this.saveCasino(); this.emit("change");
      this.mmLevel(); return { cleared: n, pay, card };
    }
    if (L.stage === "over") { S.stage = "done"; S.last = { level: S.n, score: L.score, won: S.won, cards: S.cards.slice() }; const F = this.cgStore(); F.mmBest = Math.max(F.mmBest || 0, L.score); this.mmLive = null; this.saveCasino && this.saveCasino(); this.emit("change"); return { over: true }; }
    return null;
  },
});
