"use strict";
// Shatterpane (the thirty-second big update - v14.2): a breaker on the Gilded Joker's floor. The house's old chapel
// windows are set up in the back room, pane by pane, and a glass-slipper paddle along the bottom keeps a mana orb in
// play to break them. Clear panes take one hit, tinted ones two, the darkest three; lead frames from the fifth level
// never break - though if nothing breaks for a long while a guiding light bends the rising orb toward a pane, and
// later still the lead frames crumble away. Some panes drop a charm as they go: a wider paddle, two more orbs, a slower orb, a sticky paddle that
// catches and lets fly, or a life. The orb quickens the longer it is in play. Each level a new window. Three lives. One
// stake a play: each level cleared pays gold, more each level, every play; and a Claudescryption card the first time
// ever each third level is cleared (3 common, 6 and 9 a stronger common, rare from 12). The window: 76y-pane.js.
CM.PN = {
  W: 26, H: 32, step: 1 / 120, lives: 3, cols: 13, bw: 2, bh: 1, top: 4, padY: 30, padW: 4, wideW: 6.5, padSpeed: 22, r: 0.35,
  speed: 16, maxSpeed: 27, speedUp: 0.12, charmChance: 0.13, charmSpeed: 7, guideAfter: 12, guideTurn: 1.4, leadAfter: 25, wide: 18, slow: 10, sticky: 15,
  CHARMS: ["wide", "multi", "slow", "sticky", "life"], PTS: [0, 10, 20, 40],
  cardEvery: 3, pay: (n) => 0.06 + 0.04 * n,
};
const PN = CM.PN;
// a level's window: a pattern by the level, hit points rising, lead frames from level 5 (0 empty, 1-3 hits, 9 lead)
PN.layout = (n, R) => {
  const rows = Math.min(11, 5 + Math.floor(n / 2)), C = PN.cols, g = Array.from({ length: rows }, () => Array(C).fill(0)), kind = (n - 1) % 6;
  for (let y = 0; y < rows; y++) for (let x = 0; x < C; x++) {
    const cx = Math.abs(x - (C - 1) / 2); let on = true;
    if (kind === 1) on = y >= cx - 1; // a pyramid hung from the top: wide below
    else if (kind === 2) on = (x + y) % 2 === 0 || y < 2; // a checkerboard
    else if (kind === 3) on = cx + Math.abs(y - (rows - 1) / 2) <= Math.max(4, rows / 2 + 1); // a diamond
    else if (kind === 4) on = x % 4 !== 3; // columns with gaps
    else if (kind === 5) on = y === 0 || y === rows - 1 || x === 0 || x === C - 1 || (y % 3 === 1 && x % 2 === 0); // a frame with bars
    if (!on) continue;
    let hp = 1; if (n >= 2 && y < Math.floor(rows / 3)) hp = 2; if (n >= 4 && y === 0) hp = 3; if (n >= 7 && y < 2) hp = 3; if (n >= 10 && R.chance(0.15)) hp = 3;
    g[y][x] = hp;
  }
  if (n >= 5) { const lead = Math.min(8, 2 + Math.floor((n - 5) / 2)); for (let k = 0; k < lead; k++) { const y = R.int(1, rows - 1), x = R.int(0, C - 1); if (g[y][x] && x !== Math.floor(C / 2)) g[y][x] = 9; } }
  return g;
};
PN.Level = class {
  constructor(n, seed, keep) {
    this.rnd = new CM.Random(seed); this.n = n; this.t = 0; this.events = []; this.stage = "play"; Object.assign(this, keep || { score: 0, lives: PN.lives });
    this.grid = PN.layout(n, this.rnd); this.tints = this.grid.map((row) => row.map(() => this.rnd.int(0, 5)));
    this.pad = { x: PN.W / 2, w: PN.padW, wideT: 0, stickyT: 0 }; this.slowT = 0; this.since = 0; this.charms = []; this.move = 0; this.launch = false; this.target = null; this.serve();
  }
  serve() { this.balls = [{ x: this.pad.x, y: PN.padY - PN.r - 0.5, vx: 0, vy: 0, stuck: 0, sp: PN.speed + Math.min(4, (this.n - 1) * 0.4) }]; this.charms = []; this.pad.wideT = 0; this.pad.w = PN.padW; this.pad.stickyT = 0; this.slowT = 0; }
  left() { let k = 0; for (const row of this.grid) for (const c of row) if (c && c !== 9) k++; return k; }
  input(move, launch, target) { this.move = move; if (launch) this.launch = true; this.target = target === undefined ? null : target; }
  brickAt(x, y) { const gx = Math.floor(x / PN.bw), gy = Math.floor((y - PN.top) / PN.bh); if (gy < 0 || gy >= this.grid.length || gx < 0 || gx >= PN.cols) return null; return this.grid[gy][gx] ? [gx, gy] : null; }
  hit(gx, gy, b) {
    const v = this.grid[gy][gx]; if (v === 9) { this.events.push({ kind: "lead" }); return; }
    this.grid[gy][gx] = v - 1; if (v > 1) { this.events.push({ kind: "crack", gx, gy }); return; }
    this.since = 0; const pts = PN.PTS[Math.min(3, (gy < 2 ? 3 : gy < 5 ? 2 : 1))] + (this.n - 1) * 2; this.score += pts; this.events.push({ kind: "break", gx, gy, tint: this.tints[gy][gx], pts });
    if (this.rnd.chance(PN.charmChance)) this.charms.push({ x: (gx + 0.5) * PN.bw, y: PN.top + (gy + 0.5) * PN.bh, kind: this.rnd.pick(this.lives >= 5 ? PN.CHARMS.slice(0, 4) : PN.CHARMS) });
    b.sp = Math.min(PN.maxSpeed, b.sp + PN.speedUp);
    if (!this.left()) { this.stage = "clear"; this.events.push({ kind: "clear" }); }
  }
  // one orb's flight, in small steps, x then y, so it never slips between panes
  fly(b, dt) {
    const sp = b.sp * (this.slowT > 0 ? 0.65 : 1), n = Math.max(1, Math.ceil((sp * dt) / 0.2)), h = dt / n, P = this.pad;
    for (let s = 0; s < n && this.stage === "play"; s++) {
      b.x += b.vx * sp * h; if (b.x < PN.r) { b.x = PN.r; b.vx = Math.abs(b.vx); this.events.push({ kind: "wall" }); } else if (b.x > PN.W - PN.r) { b.x = PN.W - PN.r; b.vx = -Math.abs(b.vx); this.events.push({ kind: "wall" }); }
      let c = this.brickAt(b.x + Math.sign(b.vx) * PN.r, b.y); if (c) { b.x -= b.vx * sp * h; b.vx = -b.vx; this.hit(c[0], c[1], b); }
      b.y += b.vy * sp * h; if (b.y < PN.r) { b.y = PN.r; b.vy = Math.abs(b.vy); this.events.push({ kind: "wall" }); }
      c = this.brickAt(b.x, b.y + Math.sign(b.vy) * PN.r); if (c) { b.y -= b.vy * sp * h; b.vy = -b.vy; this.hit(c[0], c[1], b); }
      // the paddle: where it is struck sets the angle
      if (b.vy > 0 && b.y + PN.r >= PN.padY - 0.3 && b.y - PN.r <= PN.padY + 0.4 && Math.abs(b.x - P.x) <= P.w / 2 + PN.r) {
        const k = Math.max(-1, Math.min(1, (b.x - P.x) / (P.w / 2))), a = k * 1.1; b.vx = Math.sin(a); b.vy = -Math.cos(a); b.y = PN.padY - 0.3 - PN.r; this.events.push({ kind: "paddle" });
        if (P.stickyT > 0) { b.stuck = b.x - P.x; b.vx = 0; b.vy = 0; return; }
      }
      if (b.y > PN.H + 1) { b.lost = true; return; }
    }
  }
  tick(dt) {
    if (this.stage !== "play") return; this.t += dt; const P = this.pad;
    if (this.target !== null) { const d = this.target - P.x; P.x += Math.sign(d) * Math.min(Math.abs(d), PN.padSpeed * 1.6 * dt); } else P.x += this.move * PN.padSpeed * dt;
    P.x = Math.max(P.w / 2, Math.min(PN.W - P.w / 2, P.x));
    this.since += dt; if (this.since > PN.guideAfter && !this.guiding) { this.guiding = true; this.events.push({ kind: "guide" }); } if (this.since <= PN.guideAfter) this.guiding = false;
    if (this.since > PN.leadAfter && this.grid.some((row) => row.includes(9))) { this.grid = this.grid.map((row) => row.map((c) => (c === 9 ? 0 : c))); this.events.push({ kind: "leadfall" }); }
    if (P.wideT > 0 && (P.wideT -= dt) <= 0) P.w = PN.padW; if (P.stickyT > 0) P.stickyT -= dt; if (this.slowT > 0) this.slowT -= dt;
    for (const b of this.balls) {
      if (b.stuck !== undefined && b.stuck !== 0 || (b.vx === 0 && b.vy === 0)) { b.x = P.x + (b.stuck || 0); b.y = PN.padY - 0.3 - PN.r; if (this.launch) { const k = Math.max(-1, Math.min(1, (b.stuck || 0.4) / (P.w / 2))), a = k * 0.9; b.vx = Math.sin(a); b.vy = -Math.cos(a); b.stuck = 0; this.events.push({ kind: "launch" }); } continue; }
      if (this.since > PN.guideAfter && b.vy < 0) this.guide(b, dt);
      this.fly(b, dt);
    }
    this.launch = false; this.balls = this.balls.filter((b) => !b.lost);
    if (this.stage !== "play") return;
    if (!this.balls.length) { this.lives -= 1; this.events.push({ kind: "die" }); if (this.lives <= 0) { this.stage = "over"; this.events.push({ kind: "over" }); return; } this.serve(); return; }
    for (const c of this.charms) { c.y += PN.charmSpeed * dt; if (Math.abs(c.y - PN.padY) < 0.7 && Math.abs(c.x - P.x) < P.w / 2 + 0.6) { c.got = true; this.charm(c.kind); } }
    this.charms = this.charms.filter((c) => !c.got && c.y < PN.H + 1);
  }
  // when no pane has broken for a while, a guiding light bends a rising orb toward the nearest pane left
  guide(b, dt) {
    let best = null, bd = Infinity; this.grid.forEach((row, gy) => row.forEach((c, gx) => { if (!c || c === 9) return; const x = (gx + 0.5) * PN.bw, y = PN.top + (gy + 0.5) * PN.bh, d = Math.hypot(x - b.x, y - b.y); if (d < bd) { bd = d; best = [x, y]; } }));
    if (!best) return; const want = Math.atan2(best[0] - b.x, -(best[1] - b.y)), now = Math.atan2(b.vx, -b.vy); let da = want - now; while (da > Math.PI) da -= 2 * Math.PI; while (da < -Math.PI) da += 2 * Math.PI;
    const a = now + Math.max(-PN.guideTurn * dt, Math.min(PN.guideTurn * dt, da)); b.vx = Math.sin(a); b.vy = -Math.cos(a); if (b.vy > -0.15) { b.vy = -0.15; b.vx = Math.sign(b.vx) * Math.sqrt(1 - 0.0225); }
  }
  charm(kind) {
    const P = this.pad; this.events.push({ kind: "charm", charm: kind });
    if (kind === "wide") { P.w = PN.wideW; P.wideT = PN.wide; }
    else if (kind === "slow") this.slowT = PN.slow;
    else if (kind === "sticky") P.stickyT = PN.sticky;
    else if (kind === "life") this.lives += 1;
    else if (kind === "multi") { const src = this.balls.find((b) => b.vy) || this.balls[0]; if (src) for (const a of [-0.5, 0.5]) { const ang = Math.atan2(src.vx || 0.3, -(src.vy || -1)) + a; this.balls.push({ x: src.x, y: Math.min(src.y, PN.padY - 1), vx: Math.sin(ang), vy: -Math.abs(Math.cos(ang)), stuck: 0, sp: src.sp }); } }
  }
  update(dt) { for (let s = 0; s < dt / PN.step - 1e-9; s++) this.tick(PN.step); }
};
Object.assign(CM.Game.prototype, {
  pnState() { return this.cgStore().pn || null; },
  pnClaimed() { const F = this.cgStore(); F.pnCards = F.pnCards || {}; return F.pnCards; },
  pnLevel() {
    const S = this.pnState(); if (!S || S.stage !== "play") return null;
    if (!this.pnLive || this.pnLive.key !== `${S.seed}:${S.n}`) {
      if (this.pnLive && this.pnLive.key && this.pnLive.key.startsWith(`${S.seed}:`)) { const L = this.pnLive; this.pnLive = new PN.Level(S.n, CM.hashSeed(`${S.seed}:${S.n}`), { score: L.score, lives: L.lives }); this.pnLive.key = `${S.seed}:${S.n}`; }
      else { S.stage = "done"; S.last = S.last || { level: S.n, won: S.won, cards: [], lost: true }; this.saveCasino && this.saveCasino(); return null; }
    }
    return this.pnLive;
  },
  pnStart(bet) {
    const S0 = this.pnState(); if (S0 && S0.stage === "play" && this.pnLive && this.pnLive.key && this.pnLive.key.startsWith(`${S0.seed}:`)) return { error: "A game is on." };
    const why = this.cgStake("shatterpane", bet); if (why) return { error: why };
    const F = this.cgStore(); F.n += 1; F.pn = { stage: "play", n: 1, bet: Math.floor(bet), seed: `${this.seed}:shatterpane:${F.n}`, won: 0, cards: [] };
    this.pnLive = new PN.Level(1, CM.hashSeed(`${F.pn.seed}:1`)); this.pnLive.key = `${F.pn.seed}:1`; this.saveCasino && this.saveCasino(); return F.pn;
  },
  // a level cleared: its gold (every play), and each third level a card the first time ever; on to the next
  pnCheck() {
    const S = this.pnState(), L = this.pnLive; if (!S || !L || S.stage !== "play") return null;
    if (L.stage === "clear") {
      const n = S.n, pay = Math.round(S.bet * PN.pay(n)), C = this.pnClaimed(); let card = null;
      if (n % PN.cardEvery === 0 && !C[n]) { card = this.cgTierCard(CM.cardTierFor(n), `Shatterpane, level ${n} cleared!`, new CM.Random(CM.hashSeed(`${this.seed}:shatterpane:card:${n}`))); C[n] = card || true; if (card) S.cards.push(card); }
      this.cgPay("shatterpane", pay); S.won += pay; S.n += 1; this.saveCasino && this.saveCasino(); this.emit("change");
      this.pnLevel(); return { cleared: n, pay, card };
    }
    if (L.stage === "over") { S.stage = "done"; S.last = { level: S.n, score: L.score, won: S.won, cards: S.cards.slice() }; const F = this.cgStore(); F.pnBest = Math.max(F.pnBest || 0, L.score); this.pnLive = null; this.saveCasino && this.saveCasino(); this.emit("change"); return { over: true }; }
    return null;
  },
});
