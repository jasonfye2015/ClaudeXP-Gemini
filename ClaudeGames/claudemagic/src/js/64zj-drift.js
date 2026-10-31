"use strict";
// Starstone Drift (the thirty-third big update - v14.3): a drifter on the Gilded Joker's floor. Through the scrying glass
// in the back room, a wand-ship floats in an open void whose edges fold round on one another. It turns, thrusts (and
// drifts on - nothing slows it but a little), fires sparks and blinks to a random spot when cornered. Starstones tumble
// through: struck, a great one splits in two middling ones, a middling one in two small, a small one is gone. Now and
// then a wraith-lantern crosses, firing back - a big slow one at random, from the fourth wave a small quick one that
// aims. Each wave brings more and quicker stones. Three lives (one more every 10,000). One stake a play: each wave
// cleared pays gold, more each wave, every play; and a Claudescryption card the first time ever each third wave is
// cleared (3 common, 6 and 9 a stronger common, rare from 12). The window: 76z-drift.js.
CM.SD = {
  W: 40, H: 30, step: 1 / 120, lives: 3, extraEvery: 10000,
  turn: 4.2, thrust: 18, drag: 0.35, maxV: 16, shipR: 0.6, bolt: 26, boltLife: 0.95, maxBolts: 4, refire: 0.17, blinkCool: 1.2, guard: 2.2,
  SIZES: { 3: { r: 2.4, pts: 20, v: [1.6, 3.4] }, 2: { r: 1.3, pts: 50, v: [2.6, 5.2] }, 1: { r: 0.65, pts: 100, v: [3.6, 7] } },
  WRAITH: { big: { r: 1.2, pts: 200, v: 5, aim: false, fire: 1.4 }, small: { r: 0.7, pts: 1000, v: 7, aim: true, fire: 1.1 } }, shotSpeed: 15, shotLife: 1.5,
  cardEvery: 3, pay: (n) => 0.05 + 0.03 * n,
};
const SD = CM.SD;
SD.wrap = (o) => { o.x = ((o.x % SD.W) + SD.W) % SD.W; o.y = ((o.y % SD.H) + SD.H) % SD.H; };
// the shortest way from a to b across the folded edges
SD.delta = (a, b) => { let dx = b.x - a.x, dy = b.y - a.y; if (dx > SD.W / 2) dx -= SD.W; if (dx < -SD.W / 2) dx += SD.W; if (dy > SD.H / 2) dy -= SD.H; if (dy < -SD.H / 2) dy += SD.H; return [dx, dy]; };
SD.dist = (a, b) => Math.hypot(...SD.delta(a, b));
SD.Level = class {
  constructor(n, seed, keep) {
    const R = this.rnd = new CM.Random(seed); this.n = n; this.t = 0; this.events = []; this.stage = "play"; Object.assign(this, keep || { score: 0, lives: SD.lives, extras: 0 });
    this.mul = 1 + Math.min(0.7, (n - 1) * 0.07); this.ship = { x: SD.W / 2, y: SD.H / 2, a: -Math.PI / 2, vx: 0, vy: 0, dead: 0, guard: SD.guard, cool: 0, blinkT: 0, thrusting: false };
    this.bolts = []; this.shots = []; this.stones = []; this.wraith = null; this.wraithT = 14 + R.next() * 8; this.ctl = { turn: 0, thrust: false, fire: false, blink: false }; this.fireHeld = false;
    for (let k = 0; k < Math.min(11, 3 + n); k++) { let x, y; do { x = R.next() * SD.W; y = R.next() * SD.H; } while (Math.hypot(x - SD.W / 2, y - SD.H / 2) < 9); this.addStone(3, x, y); }
  }
  addStone(size, x, y) { const R = this.rnd, S = SD.SIZES[size], a = R.next() * Math.PI * 2, v = (S.v[0] + R.next() * (S.v[1] - S.v[0])) * this.mul;
    const shape = Array.from({ length: 10 }, () => 0.75 + R.next() * 0.4); this.stones.push({ size, x, y, vx: Math.cos(a) * v, vy: Math.sin(a) * v, rot: R.next() * 6, spin: (R.next() - 0.5) * 2, shape, kind: R.int(0, 2) }); }
  input(turn, thrust, fire, blink) { this.ctl.turn = turn; this.ctl.thrust = !!thrust; if (fire && !this.fireHeld) this.firePressed = true; this.fireHeld = !!fire; if (blink) this.ctl.blink = true; }
  split(s, i) {
    this.stones.splice(i, 1); this.score += SD.SIZES[s.size].pts; this.events.push({ kind: "split", s, pts: SD.SIZES[s.size].pts });
    if (s.size > 1) for (let k = 0; k < 2; k++) this.addStone(s.size - 1, s.x, s.y);
  }
  stepShip(dt) {
    const S = this.ship, C = this.ctl;
    if (S.dead) { S.dead -= dt; if (S.dead <= 0) { const clear = this.stones.every((s) => Math.hypot(s.x - SD.W / 2, s.y - SD.H / 2) > SD.SIZES[s.size].r + 4); if (clear || S.dead < -3) { Object.assign(S, { x: SD.W / 2, y: SD.H / 2, a: -Math.PI / 2, vx: 0, vy: 0, dead: 0, guard: SD.guard }); this.events.push({ kind: "respawn" }); } } return; }
    S.a += C.turn * SD.turn * dt; S.thrusting = C.thrust;
    if (C.thrust) { S.vx += Math.cos(S.a) * SD.thrust * dt; S.vy += Math.sin(S.a) * SD.thrust * dt; const v = Math.hypot(S.vx, S.vy); if (v > SD.maxV) { S.vx *= SD.maxV / v; S.vy *= SD.maxV / v; } }
    const k = Math.max(0, 1 - SD.drag * dt); S.vx *= k; S.vy *= k; S.x += S.vx * dt; S.y += S.vy * dt; SD.wrap(S);
    S.cool -= dt; S.blinkT -= dt; if (S.guard > 0) S.guard -= dt;
    if ((this.firePressed || this.fireHeld) && S.cool <= 0 && this.bolts.length < SD.maxBolts) { this.bolts.push({ x: S.x + Math.cos(S.a) * 0.9, y: S.y + Math.sin(S.a) * 0.9, vx: S.vx + Math.cos(S.a) * SD.bolt, vy: S.vy + Math.sin(S.a) * SD.bolt, life: SD.boltLife }); S.cool = SD.refire; this.events.push({ kind: "fire" }); }
    this.firePressed = false;
    if (C.blink && S.blinkT <= 0) { S.x = this.rnd.next() * SD.W; S.y = this.rnd.next() * SD.H; S.vx = S.vy = 0; S.blinkT = SD.blinkCool; this.events.push({ kind: "blink" }); } C.blink = false;
  }
  stepWraith(dt) {
    const R = this.rnd, W = this.wraith;
    if (!W) { if ((this.wraithT -= dt) <= 0 && this.stones.length) { const kind = this.n >= 4 && R.chance(0.3 + 0.05 * this.n) ? "small" : "big", fromLeft = R.chance(0.5); this.wraith = { kind, x: fromLeft ? 0 : SD.W - 0.01, y: 3 + R.next() * (SD.H - 6), dir: fromLeft ? 1 : -1, vy: 0, turnT: 1, fireT: 0.8, gone: 0 }; this.wraithT = Math.max(8, 20 - this.n) + R.next() * 8; this.events.push({ kind: "wraith", w: kind }); } return; }
    const K = SD.WRAITH[W.kind]; W.x += W.dir * K.v * dt; W.y += W.vy * dt; W.gone += K.v * dt; if ((W.turnT -= dt) <= 0) { W.vy = R.pick([-1, 0, 1]) * K.v * 0.6; W.turnT = 0.8 + R.next(); } SD.wrap(W);
    if (W.gone > SD.W) { this.wraith = null; return; }
    if ((W.fireT -= dt) <= 0 && !this.ship.dead) { W.fireT = K.fire / Math.min(1.5, this.mul); let a; if (K.aim) { const [dx, dy] = SD.delta(W, this.ship); a = Math.atan2(dy, dx) + (R.next() - 0.5) * Math.max(0.1, 0.5 - 0.04 * this.n); } else a = R.next() * Math.PI * 2; this.shots.push({ x: W.x, y: W.y, vx: Math.cos(a) * SD.shotSpeed, vy: Math.sin(a) * SD.shotSpeed, life: SD.shotLife }); this.events.push({ kind: "wfire" }); }
  }
  lose() { const S = this.ship; if (S.dead || S.guard > 0) return; S.dead = 2; this.lives -= 1; this.bolts = []; this.events.push({ kind: "die", x: S.x, y: S.y }); if (this.lives <= 0) { this.stage = "over"; this.events.push({ kind: "over" }); } }
  tick(dt) {
    if (this.stage !== "play") return; this.t += dt; const S = this.ship;
    this.stepShip(dt); this.stepWraith(dt);
    for (const s of this.stones) { s.x += s.vx * dt; s.y += s.vy * dt; s.rot += s.spin * dt; SD.wrap(s); }
    for (const o of [...this.bolts, ...this.shots]) { o.x += o.vx * dt; o.y += o.vy * dt; o.life -= dt; SD.wrap(o); }
    // the ship's sparks against stones and the wraith
    for (const b of this.bolts) { if (b.life <= 0) continue; for (let i = 0; i < this.stones.length; i++) { const s = this.stones[i]; if (SD.dist(b, s) < SD.SIZES[s.size].r) { b.life = 0; this.split(s, i); break; } }
      const W = this.wraith; if (b.life > 0 && W && SD.dist(b, W) < SD.WRAITH[W.kind].r) { b.life = 0; const pts = SD.WRAITH[W.kind].pts; this.score += pts; this.events.push({ kind: "wraithdown", x: W.x, y: W.y, pts }); this.wraith = null; } }
    // the wraith's shots, and the wraith itself, against stones
    for (const sh of this.shots) { if (sh.life <= 0) continue; for (let i = 0; i < this.stones.length; i++) { const s = this.stones[i]; if (SD.dist(sh, s) < SD.SIZES[s.size].r) { sh.life = 0; this.stones.splice(i, 1); if (s.size > 1) for (let k = 0; k < 2; k++) this.addStone(s.size - 1, s.x, s.y); this.events.push({ kind: "split", s, pts: 0 }); break; } } }
    if (this.wraith) for (let i = 0; i < this.stones.length; i++) { const s = this.stones[i]; if (SD.dist(this.wraith, s) < SD.SIZES[s.size].r + SD.WRAITH[this.wraith.kind].r * 0.7) { this.events.push({ kind: "wraithdown", x: this.wraith.x, y: this.wraith.y, pts: 0 }); this.wraith = null; break; } }
    this.bolts = this.bolts.filter((b) => b.life > 0); this.shots = this.shots.filter((s) => s.life > 0);
    // the ship struck
    if (!S.dead) {
      for (let i = 0; i < this.stones.length; i++) { const s = this.stones[i]; if (SD.dist(S, s) < SD.SIZES[s.size].r * 0.85 + SD.shipR && S.guard <= 0) { this.split(s, i); this.lose(); break; } }
      for (const sh of this.shots) if (sh.life > 0 && SD.dist(S, sh) < SD.shipR + 0.2) { sh.life = 0; this.lose(); }
      if (this.wraith && !S.dead && S.guard <= 0 && SD.dist(S, this.wraith) < SD.shipR + SD.WRAITH[this.wraith.kind].r) { this.wraith = null; this.lose(); }
    }
    if (this.stage !== "play") return;
    while (this.score >= SD.extraEvery * ((this.extras || 0) + 1)) { this.extras = (this.extras || 0) + 1; this.lives += 1; this.events.push({ kind: "extra" }); }
    if (!this.stones.length && !S.dead) { this.stage = "clear"; this.wraith = null; this.events.push({ kind: "clear" }); }
  }
  update(dt) { for (let s = 0; s < dt / SD.step - 1e-9; s++) this.tick(SD.step); }
};
Object.assign(CM.Game.prototype, {
  sdState() { return this.cgStore().sd || null; },
  sdClaimed() { const F = this.cgStore(); F.sdCards = F.sdCards || {}; return F.sdCards; },
  sdLevel() {
    const S = this.sdState(); if (!S || S.stage !== "play") return null;
    if (!this.sdLive || this.sdLive.key !== `${S.seed}:${S.n}`) {
      if (this.sdLive && this.sdLive.key && this.sdLive.key.startsWith(`${S.seed}:`)) { const L = this.sdLive; this.sdLive = new SD.Level(S.n, CM.hashSeed(`${S.seed}:${S.n}`), { score: L.score, lives: L.lives, extras: L.extras }); this.sdLive.key = `${S.seed}:${S.n}`; }
      else { S.stage = "done"; S.last = S.last || { level: S.n, won: S.won, cards: [], lost: true }; this.saveCasino && this.saveCasino(); return null; }
    }
    return this.sdLive;
  },
  sdStart(bet) {
    const S0 = this.sdState(); if (S0 && S0.stage === "play" && this.sdLive && this.sdLive.key && this.sdLive.key.startsWith(`${S0.seed}:`)) return { error: "A game is on." };
    const why = this.cgStake("starstone", bet); if (why) return { error: why };
    const F = this.cgStore(); F.n += 1; F.sd = { stage: "play", n: 1, bet: Math.floor(bet), seed: `${this.seed}:starstone:${F.n}`, won: 0, cards: [] };
    this.sdLive = new SD.Level(1, CM.hashSeed(`${F.sd.seed}:1`)); this.sdLive.key = `${F.sd.seed}:1`; this.saveCasino && this.saveCasino(); return F.sd;
  },
  // a wave cleared: its gold (every play), and each third wave a card the first time ever; on to the next
  sdCheck() {
    const S = this.sdState(), L = this.sdLive; if (!S || !L || S.stage !== "play") return null;
    if (L.stage === "clear") {
      const n = S.n, pay = Math.round(S.bet * SD.pay(n)), C = this.sdClaimed(); let card = null;
      if (n % SD.cardEvery === 0 && !C[n]) { card = this.cgTierCard(CM.cardTierFor(n), `Starstone Drift, wave ${n} cleared!`, new CM.Random(CM.hashSeed(`${this.seed}:starstone:card:${n}`))); C[n] = card || true; if (card) S.cards.push(card); }
      this.cgPay("starstone", pay); S.won += pay; S.n += 1; this.saveCasino && this.saveCasino(); this.emit("change");
      this.sdLevel(); return { cleared: n, pay, card };
    }
    if (L.stage === "over") { S.stage = "done"; S.last = { level: S.n, score: L.score, won: S.won, cards: S.cards.slice() }; const F = this.cgStore(); F.sdBest = Math.max(F.sdBest || 0, L.score); this.cgRecord && this.cgRecord("starstone", L.score, S.last.level); this.sdLive = null; this.saveCasino && this.saveCasino(); this.emit("change"); return { over: true }; }
    return null;
  },
});
