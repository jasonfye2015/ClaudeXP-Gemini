"use strict";
// The Gloomwing Swarm (the thirtieth big update - v14.0): a shooter on the Gilded Joker's floor. A little lantern-skiff
// at the bottom of the night sky slides left and right firing mana bolts (two in the air at once). Each stage the
// Gloomwings swoop in along curving paths and settle into a breathing formation - Mites below, Moths above them and four
// armoured Wardens on top (two hits each) - then peel off and dive, Moths weaving, the diving ones dropping embers. A
// Warden now and then hovers low and lowers a binding beam: a skiff caught in it is carried up into the formation (a
// life lost), and shooting that Warden while it is out of formation sets the skiff free to fly beside yours - two skiffs,
// two bolts at once. Every fourth stage is a Bonus Flight: forty fly past without fighting back, 100 each, 10,000 for all.
// Three lives (more at 20,000 and 70,000). One stake a play: each stage cleared pays gold, more each stage, every play;
// and a Claudescryption card the first time ever each of stages 2, 4, 6, 8, 10, 12, 15 and 20 is cleared (common, then a
// stronger common, then rare). The same inputs give the same game. The window: 76w-swarm.js.
CM.SW = {
  W: 28, H: 32, step: 1 / 60, lives: 3, extras: [20000, 70000], shipY: 30,
  shipSpeed: 15, boltSpeed: 36, maxBolts: 2, refire: 0.16, shotSpeed: 14, flySpeed: 17, diveSpeed: 11,
  KINDS: { mite: { hp: 1, pts: [50, 100] }, moth: { hp: 1, pts: [80, 160] }, warden: { hp: 2, pts: [150, 400] } },
  ROWS: [["warden", 4], ["moth", 6], ["moth", 6], ["mite", 8], ["mite", 8]],
  CARDS: [2, 4, 6, 8, 10, 12, 15, 20], bonusEvery: 4,
  pay: (n) => 0.05 + 0.03 * n,
};
const SW = CM.SW;
// a cubic curve, sampled
SW.curve = (a, b, c, d, k = 10) => { const out = []; for (let i = 1; i <= k; i++) { const t = i / k, u = 1 - t; out.push([u * u * u * a[0] + 3 * u * u * t * b[0] + 3 * u * t * t * c[0] + t * t * t * d[0], u * u * u * a[1] + 3 * u * u * t * b[1] + 3 * u * t * t * c[1] + t * t * t * d[1]]); } return out; };
SW.loop = (cx, cy, r, from, turn, k = 10) => { const out = []; for (let i = 1; i <= k; i++) { const a = from + (turn * i) / k; out.push([cx + Math.cos(a) * r, cy + Math.sin(a) * r]); } return out; };
// the ways in: from the top (m = which side it curls to) or from a side (s = -1 left, 1 right)
SW.entry = (kind, m) => { const W2 = SW.W / 2;
  if (kind === "top") { const a = [W2 + m * 2, -2], d = [W2 + m * 9, 20]; return [a, ...SW.curve(a, [W2 + m * 2, 10], [W2 + m * 12, 14], d), ...SW.loop(W2 + m * 6, 20, 3, m > 0 ? 0 : Math.PI, m > 0 ? Math.PI * 1.5 : -Math.PI * 1.5)]; }
  const a = [W2 + m * 16, 27], d = [W2 - m * 2, 14]; return [a, ...SW.curve(a, [W2 + m * 6, 26], [W2 - m * 6, 20], d), ...SW.loop(W2 + m * 1, 14, 3, m > 0 ? Math.PI : 0, m > 0 ? Math.PI * 1.6 : -Math.PI * 1.6)]; };
// the Bonus Flight's ways through and out again
SW.flyby = (w, m) => { const W2 = SW.W / 2;
  if (w % 2 === 0) { const a = [W2 + m * 3, -2]; return [a, ...SW.curve(a, [W2 + m * 3, 18], [W2 + m * 13, 24], [W2 + m * 8, 12]), ...SW.loop(W2 + m * 8, 16, 4, -Math.PI / 2, m * Math.PI * 1.5, 12), ...SW.curve([W2 + m * 4, 16], [W2 - m * 4, 10], [W2 - m * 10, 4], [W2 - m * 20, -4])]; }
  const a = [W2 + m * 16, 22]; return [a, ...SW.curve(a, [W2 + m * 4, 24], [W2 - m * 4, 6], [W2 - m * 8, 12]), ...SW.loop(W2 - m * 4, 12, 4, Math.PI, -m * Math.PI * 2, 14), ...SW.curve([W2 - m * 8, 12], [W2, 20], [W2 + m * 8, 26], [W2 + m * 18, 30])]; };
SW.Level = class {
  constructor(n, seed, keep) {
    this.rnd = new CM.Random(seed); this.n = n; this.t = 0; this.events = []; this.stage = "play"; this.bonus = n % SW.bonusEvery === 0;
    Object.assign(this, keep || { score: 0, lives: SW.lives, extrasGiven: 0, dual: false });
    this.mul = 1 + Math.min(0.6, (n - 1) * 0.05); this.p = { x: SW.W / 2, dead: 0, cool: 0 }; this.move = 0; this.fireHeld = false; this.firePressed = false;
    this.bolts = []; this.shots = []; this.foes = []; this.hits = 0; this.diveT = 5; this.beamFoe = null;
    let id = 0; const add = (kind, row, col, count, path, at) => { this.foes.push({ id: id++, kind, hp: SW.KINDS[kind].hp, row, col, count, state: "wait", at, path, pi: 0, x: path[0][0], y: path[0][1], dir: 0, t: 0, captive: false, shots: 0 }); };
    if (this.bonus) { const kinds = ["mite", "moth", "warden", "moth", "mite"]; for (let w = 0; w < 5; w++) for (let j = 0; j < 8; j++) { const m = j % 2 ? 1 : -1; add(kinds[w] === "warden" ? "moth" : kinds[w], -1, j, 8, SW.flyby(w, w % 2 ? m : (w % 4 ? -m : m)), 0.5 + w * 3.2 + Math.floor(j / 2) * 0.22); } this.foes.forEach((f) => { f.hp = 1; }); return; }
    // the formation's waves: Mites from the top; Wardens and Moths from the left; Moths from the right; Mites from the top
    const slots = (r) => Array.from({ length: SW.ROWS[r][1] }, (_, c) => [r, c]);
    const waves = [{ from: "top", list: slots(3) }, { from: "side", m: -1, list: [...slots(0), ...slots(1).slice(1, 5)] }, { from: "side", m: 1, list: [...slots(1).filter((s) => s[1] === 0 || s[1] === 5), ...slots(2)] }, { from: "top", list: slots(4) }];
    waves.forEach((W, k) => W.list.forEach(([r, c], j) => { const m = W.from === "top" ? (j % 2 ? 1 : -1) : W.m; add(SW.ROWS[r][0], r, c, SW.ROWS[r][1], SW.entry(W.from, m), 0.6 + k * 2.8 + j * 0.16); }));
  }
  slot(f) { const br = 1 + 0.07 * Math.sin(this.t * 1.3); return [SW.W / 2 + (f.col - (f.count - 1) / 2) * 2.6 * br, 4 + f.row * 2.3]; }
  live() { return this.foes.filter((f) => f.state !== "dead" && f.state !== "gone"); }
  input(move, fire) { this.move = move; if (fire && !this.fireHeld) this.firePressed = true; this.fireHeld = !!fire; }
  shipXs() { const P = this.p; return this.dual ? [P.x - 0.9, P.x + 0.9] : [P.x]; }
  stepShip(dt) {
    const P = this.p; if (P.dead) return; const half = this.dual ? 1.9 : 1;
    P.x = Math.max(half, Math.min(SW.W - half, P.x + this.move * SW.shipSpeed * dt)); P.cool -= dt;
    if ((this.firePressed || (this.fireHeld && P.cool <= 0)) && this.bolts.length < SW.maxBolts * (this.dual ? 2 : 1) && P.cool <= 0) { for (const x of this.shipXs()) this.bolts.push({ x, y: SW.shipY - 1 }); P.cool = SW.refire; this.events.push({ kind: "fire" }); }
    this.firePressed = false;
  }
  // flying a path, then to the slot (or out, on a Bonus Flight)
  follow(f, dt, sp) { let left = sp * dt; while (left > 0 && f.pi < f.path.length) { const [tx, ty] = f.path[f.pi], dx = tx - f.x, dy = ty - f.y, d = Math.hypot(dx, dy); if (d <= left) { f.x = tx; f.y = ty; left -= d; f.pi++; } else { f.x += (dx / d) * left; f.y += (dy / d) * left; f.dir = Math.atan2(dy, dx); left = 0; } } return f.pi >= f.path.length; }
  toward(f, tx, ty, sp, dt) { const dx = tx - f.x, dy = ty - f.y, d = Math.hypot(dx, dy); if (d <= sp * dt) { f.x = tx; f.y = ty; return true; } f.x += (dx / d) * sp * dt; f.y += (dy / d) * sp * dt; f.dir = Math.atan2(dy, dx); return false; }
  stepFoe(f, dt) {
    const P = this.p, sp = SW.flySpeed * this.mul;
    if (f.state === "wait") { if (this.t >= f.at) f.state = "enter"; return; }
    if (f.state === "enter") { if (this.follow(f, dt, sp)) f.state = this.bonus ? "gone" : "home"; return; }
    if (f.state === "home" || f.state === "return") { const [sx, sy] = this.slot(f); if (this.toward(f, sx, sy, sp, dt)) { f.state = "form"; f.dir = -Math.PI / 2; } return; }
    if (f.state === "form") { [f.x, f.y] = this.slot(f); f.dir = -Math.PI / 2; return; }
    if (f.state === "loop") { if (this.follow(f, dt, sp * 0.8)) { f.state = f.beam ? "tobeam" : "dive"; f.t = 0; f.vx = 0; } return; }
    if (f.state === "tobeam") { if (this.toward(f, f.beamX, SW.H - 12, SW.diveSpeed * this.mul, dt)) { f.state = "beam"; f.t = 0; this.events.push({ kind: "beam", f }); } return; }
    if (f.state === "beam") {
      f.t += dt; const on = f.t > 0.7 && f.t < 3.2;
      if (on && !P.dead && !this.dual && !f.captive && Math.abs(P.x - f.x) < 1.7) { f.captive = true; this.captured = f.id; this.events.push({ kind: "captured", f }); this.lose("beam"); }
      if (f.t > 3.6) { f.state = "return"; f.beam = false; this.beamFoe = null; } return;
    }
    if (f.state === "dive") {
      f.t += dt; const vy = SW.diveSpeed * this.mul, want = Math.max(-8, Math.min(8, (P.x - f.x) * 1.4)) + (f.kind === "moth" ? Math.sin(f.t * 4) * 7 : 0);
      f.vx += (want - f.vx) * Math.min(1, dt * 3); f.x = Math.max(0.5, Math.min(SW.W - 0.5, f.x + f.vx * dt)); f.y += vy * dt; f.dir = Math.atan2(vy, f.vx);
      // embers on the way down
      for (const fy of [9, 14, 18].slice(0, f.shots)) if (f.y - vy * dt < fy && f.y >= fy && !P.dead) { const tt = (SW.shipY - f.y) / SW.shotSpeed, vx = Math.max(-6, Math.min(6, (P.x - f.x) / tt)); this.shots.push({ x: f.x, y: f.y + 0.8, vx, vy: SW.shotSpeed }); this.events.push({ kind: "ember" }); }
      if (f.y > SW.H + 1) { f.y = -2; f.x = this.slot(f)[0]; f.state = "return"; } return;
    }
  }
  // who dives next: one at a time, quicker as the stages go; a Warden takes two Moths with it, or goes low to bind
  stepDives(dt) {
    if (this.bonus || this.p.dead) return; this.diveT -= dt; if (this.diveT > 0) return;
    const form = this.foes.filter((f) => f.state === "form"); if (!form.length) { this.diveT = 0.5; return; }
    const R = this.rnd, inFlight = this.foes.filter((f) => ["loop", "dive", "tobeam", "beam"].includes(f.state)).length, alive = this.live().length;
    this.diveT = Math.max(0.55, 2.6 - 0.14 * this.n) * (alive < 8 ? 0.6 : 1) * (0.7 + R.next() * 0.6); if (inFlight >= 2 + Math.floor(this.n / 3)) return;
    const f = R.pick(form), side = f.x < SW.W / 2 ? -1 : 1, go = (g, beam) => { g.state = "loop"; g.pi = 0; g.vx = 0; g.beam = !!beam; g.shots = beam ? 0 : Math.min(3, 1 + Math.floor(this.n / 3)); g.path = SW.loop(g.x + side * 1.6, g.y, 1.6, side > 0 ? Math.PI : 0, side > 0 ? Math.PI * 1.2 : -Math.PI * 1.2, 8); this.events.push({ kind: "dive", f: g }); };
    if (f.kind === "warden" && !f.captive && !this.dual && this.beamFoe === null && !this.foes.some((g) => g.captive) && R.chance(0.45)) { f.beamX = Math.max(3, Math.min(SW.W - 3, this.p.x)); this.beamFoe = f.id; go(f, true); return; }
    go(f); if (f.kind === "warden") for (const e of form.filter((g) => g.kind === "moth" && g.row === 1 && Math.abs(g.col - (f.col + 1)) <= 1).slice(0, 2)) go(e);
  }
  kill(f, how) {
    const diving = f.state !== "form"; f.state = "dead"; let pts = this.bonus ? 100 : SW.KINDS[f.kind].pts[diving ? 1 : 0]; this.hits += this.bonus ? 1 : 0;
    if (f.captive) { f.captive = false; if (diving && this.lives > 0) { this.dual = true; this.captured = 0; this.events.push({ kind: "rescue" }); } else { this.captured = 0; this.events.push({ kind: "lostcaptive" }); } }
    if (this.beamFoe === f.id) this.beamFoe = null; this.score += pts; this.events.push({ kind: "kill", f, pts, how });
  }
  lose(why) { const P = this.p; if (P.dead) return; if (this.dual && why !== "beam") { this.dual = false; this.events.push({ kind: "lostone" }); return; } P.dead = 2.2; this.lives -= 1; this.bolts = []; this.events.push({ kind: "die", why }); }
  update(dt) { for (let s = 0; s < dt / SW.step - 1e-9; s++) this.tick(SW.step); }
  tick(dt) {
    if (this.stage !== "play") return; this.t += dt; const P = this.p;
    if (P.dead) { P.dead -= dt; if (P.dead <= 0) { if (this.lives <= 0) { this.stage = "over"; this.events.push({ kind: "over" }); return; } P.dead = 0; P.x = SW.W / 2; this.shots = []; this.events.push({ kind: "respawn" }); } }
    this.stepShip(dt); for (const f of this.foes) this.stepFoe(f, dt); this.stepDives(dt);
    for (const b of this.bolts) b.y -= SW.boltSpeed * dt; this.bolts = this.bolts.filter((b) => b.y > -1);
    for (const b of this.bolts) for (const f of this.foes) { if (b.dead || f.state === "dead" || f.state === "gone" || f.state === "wait" || f.y < -0.5) continue; if (Math.abs(b.x - f.x) < 1 && Math.abs(b.y - f.y) < 1) { b.dead = true; f.hp -= 1; if (f.hp <= 0) this.kill(f, "bolt"); else this.events.push({ kind: "dent", f }); } }
    this.bolts = this.bolts.filter((b) => !b.dead);
    for (const s of this.shots) { s.x += s.vx * dt; s.y += s.vy * dt; } this.shots = this.shots.filter((s) => s.y < SW.H + 1);
    if (!P.dead) {
      const xs = this.shipXs();
      for (const s of this.shots) if (!s.dead && Math.abs(s.y - SW.shipY) < 0.9 && xs.some((x) => Math.abs(s.x - x) < 0.8)) { s.dead = true; this.lose("ember"); break; }
      this.shots = this.shots.filter((s) => !s.dead);
      if (!this.bonus) for (const f of this.foes) if (["dive", "loop", "return"].includes(f.state) && Math.abs(f.y - SW.shipY) < 1.1 && xs.some((x) => Math.abs(f.x - x) < 1.2)) { this.kill(f, "crash"); this.lose("crash"); break; }
    }
    const k = this.extrasGiven || 0; if (k < SW.extras.length && this.score >= SW.extras[k]) { this.extrasGiven = k + 1; this.lives += 1; this.events.push({ kind: "extra" }); }
    if (!this.live().length && !P.dead) { this.stage = "clear"; if (this.bonus && this.hits === this.foes.length) { this.score += 10000; this.events.push({ kind: "perfect" }); } this.events.push({ kind: "clear", hits: this.hits }); }
  }
};
Object.assign(CM.Game.prototype, {
  swState() { return this.cgStore().sw || null; },
  swClaimed() { const F = this.cgStore(); F.swCards = F.swCards || {}; return F.swCards; },
  swLevel() {
    const S = this.swState(); if (!S || S.stage !== "play") return null;
    if (!this.swLive || this.swLive.key !== `${S.seed}:${S.n}`) {
      if (this.swLive && this.swLive.key && this.swLive.key.startsWith(`${S.seed}:`)) { const L = this.swLive, keep = { score: L.score, lives: L.lives, extrasGiven: L.extrasGiven, dual: L.dual }; this.swLive = new SW.Level(S.n, CM.hashSeed(`${S.seed}:${S.n}`), keep); this.swLive.key = `${S.seed}:${S.n}`; }
      else { S.stage = "done"; S.last = S.last || { level: S.n, won: S.won, cards: [], lost: true }; this.saveCasino && this.saveCasino(); return null; }
    }
    return this.swLive;
  },
  swStart(bet) {
    const S0 = this.swState(); if (S0 && S0.stage === "play" && this.swLive && this.swLive.key && this.swLive.key.startsWith(`${S0.seed}:`)) return { error: "A game is on." };
    const why = this.cgStake("swarm", bet); if (why) return { error: why };
    const F = this.cgStore(); F.n += 1; F.sw = { stage: "play", n: 1, bet: Math.floor(bet), seed: `${this.seed}:swarm:${F.n}`, won: 0, cards: [] };
    this.swLive = new SW.Level(1, CM.hashSeed(`${F.sw.seed}:1`)); this.swLive.key = `${F.sw.seed}:1`; this.saveCasino && this.saveCasino(); return F.sw;
  },
  // a stage cleared: its gold (every play), and at the card stages a card the first time ever; on to the next
  swCheck() {
    const S = this.swState(), L = this.swLive; if (!S || !L || S.stage !== "play") return null;
    if (L.stage === "clear") {
      const n = S.n, pay = Math.round(S.bet * SW.pay(n)), C = this.swClaimed(); let card = null;
      if (SW.CARDS.includes(n) && !C[n]) { card = this.cgTierCard(CM.cardTierFor(n), `The Gloomwing Swarm, stage ${n} cleared!`, new CM.Random(CM.hashSeed(`${this.seed}:swarm:card:${n}`))); C[n] = card || true; if (card) S.cards.push(card); }
      this.cgPay("swarm", pay); S.won += pay; S.n += 1; this.saveCasino && this.saveCasino(); this.emit("change");
      this.swLevel(); return { cleared: n, pay, card, bonus: L.bonus, hits: L.hits };
    }
    if (L.stage === "over") { S.stage = "done"; S.last = { level: S.n, score: L.score, won: S.won, cards: S.cards.slice() }; const F = this.cgStore(); F.swBest = Math.max(F.swBest || 0, L.score); this.cgRecord && this.cgRecord("swarm", L.score, S.last.level); this.swLive = null; this.saveCasino && this.saveCasino(); this.emit("change"); return { over: true }; }
    return null;
  },
});
