"use strict";
// The Hexmarch (the thirty-first big update - v14.1): a shooter in the Gilded Joker's cellar range. Fifty-five hexlings
// in five ranks - Grubs at the front, Wisps behind, Imps at the back - march from side to side, a step down each time
// they reach a wall, quicker as their numbers thin. A rune-cannon behind four warding stones slides along the floor and
// fires one bolt at a time; the hexlings drop hexes back, and both chip the wards away. A comet crosses the top now and
// then for a mystery score. If the march reaches the floor, the game is over whatever lives are left. Each level starts
// the ranks lower and shoots back harder. Three lives (one more at 1,500). One stake a play: each level cleared pays
// gold, more each level, every play; and a Claudescryption card the first time ever each third level is cleared - 3, 6,
// 9 and on (common, then a stronger common, then rare from 12). The same inputs give the same game. The window:
// 76x-hexmarch.js.
CM.HX = {
  W: 28, H: 32, step: 1 / 60, lives: 3, extra: 1500, gunY: 30, floorY: 29,
  gunSpeed: 13, boltSpeed: 38, hexSpeed: 12, cols: 11, gapX: 2.0, gapY: 2.0, dx: 0.5,
  RANKS: ["imp", "wisp", "wisp", "grub", "grub"], PTS: { imp: 30, wisp: 20, grub: 10 }, COMET: [50, 100, 150, 300],
  WARDS: 4, WARD: { w: 8, h: 4, cell: 0.5, y: 25 },
  cardEvery: 3, pay: (n) => 0.06 + 0.04 * n,
};
const HX = CM.HX;
HX.Level = class {
  constructor(n, seed, keep) {
    this.rnd = new CM.Random(seed); this.n = n; this.t = 0; this.events = []; this.stage = "play"; Object.assign(this, keep || { score: 0, lives: HX.lives, extraGiven: false });
    const top = 5 + ((n - 1) % 8) * 0.9; this.foes = [];
    HX.RANKS.forEach((kind, r) => { for (let c = 0; c < HX.cols; c++) this.foes.push({ id: this.foes.length, kind, r, c, x: HX.W / 2 + (c - (HX.cols - 1) / 2) * HX.gapX, y: top + r * HX.gapY, dead: false }); });
    this.dir = 1; this.marchT = 0.6; this.frame = 0; this.p = { x: HX.W / 2, dead: 0 }; this.bolt = null; this.hexes = []; this.hexT = 1.2; this.comet = null; this.cometT = 18 + this.rnd.next() * 8; this.shots = 0; this.move = 0; this.firePressed = false; this.fireHeld = false;
    // the wards: cells, a notch out of the bottom middle
    const Wd = HX.WARD; this.wards = []; for (let k = 0; k < HX.WARDS; k++) { const x0 = (HX.W / (HX.WARDS + 1)) * (k + 1) - (Wd.w * Wd.cell) / 2; for (let i = 0; i < Wd.w; i++) for (let j = 0; j < Wd.h; j++) { if ((j === 0 && (i === 0 || i === Wd.w - 1)) || (j === Wd.h - 1 && i >= 3 && i <= 4)) continue; this.wards.push({ x: x0 + (i + 0.5) * Wd.cell, y: Wd.y + (j + 0.5) * Wd.cell, hp: 2 }); } }
    this.mul = 1 + Math.min(0.5, (n - 1) * 0.04);
  }
  live() { return this.foes.filter((f) => !f.dead); }
  input(move, fire) { this.move = move; if (fire && !this.fireHeld) this.firePressed = true; this.fireHeld = !!fire; }
  // the march: one step each beat, the beat quicker as they thin; at a wall, a step down and back
  march(dt) {
    this.marchT -= dt; if (this.marchT > 0) return; const L = this.live(), alive = L.length;
    this.marchT = Math.max(0.016, (0.05 + 0.75 * (alive / 55)) / this.mul); this.frame ^= 1; this.events.push({ kind: "beat", n: this.frame });
    const minX = Math.min(...L.map((f) => f.x)), maxX = Math.max(...L.map((f) => f.x));
    if ((this.dir > 0 && maxX + HX.dx > HX.W - 1) || (this.dir < 0 && minX - HX.dx < 1)) { for (const f of L) f.y += 1; this.dir *= -1; } else for (const f of L) f.x += this.dir * HX.dx;
    for (const f of L) for (const w of this.wards) if (w.hp > 0 && Math.abs(w.x - f.x) < 1 && Math.abs(w.y - f.y) < 0.8) w.hp = 0;
    if (Math.max(...L.map((f) => f.y)) >= HX.floorY) { this.lives = 0; this.p.dead = 1.5; this.events.push({ kind: "landed" }); }
  }
  hitWard(x, y, r) { for (const w of this.wards) if (w.hp > 0 && Math.abs(w.x - x) < r && Math.abs(w.y - y) < 0.45) { w.hp -= 1; return true; } return false; }
  tick(dt) {
    if (this.stage !== "play") return; this.t += dt; const P = this.p;
    if (P.dead) { P.dead -= dt; if (P.dead <= 0) { if (this.lives <= 0) { this.stage = "over"; this.events.push({ kind: "over" }); return; } P.dead = 0; P.x = HX.W / 2; this.hexes = []; this.events.push({ kind: "respawn" }); } else return; }
    P.x = Math.max(1, Math.min(HX.W - 1, P.x + this.move * HX.gunSpeed * dt));
    if ((this.firePressed || this.fireHeld) && !this.bolt) { this.bolt = { x: P.x, y: HX.gunY - 1 }; this.shots += 1; this.events.push({ kind: "fire" }); } this.firePressed = false;
    this.march(dt); if (P.dead) return;
    // the bolt
    if (this.bolt) { const B = this.bolt; B.y -= HX.boltSpeed * dt;
      if (B.y < 0) this.bolt = null;
      else if (this.hitWard(B.x, B.y, 0.35)) this.bolt = null;
      else { const f = this.live().find((q) => Math.abs(q.x - B.x) < 0.8 && Math.abs(q.y - B.y) < 0.7); if (f) { f.dead = true; this.bolt = null; this.score += HX.PTS[f.kind]; this.events.push({ kind: "kill", f, pts: HX.PTS[f.kind] }); }
        else if (this.comet && Math.abs(this.comet.x - B.x) < 1.3 && Math.abs(this.comet.y - B.y) < 0.8) { const pts = HX.COMET[(this.shots + this.n) % HX.COMET.length]; this.score += pts; this.events.push({ kind: "comet", pts, x: this.comet.x }); this.comet = null; this.bolt = null; }
        else { const h = this.hexes.find((q) => Math.abs(q.x - B.x) < 0.5 && Math.abs(q.y - B.y) < 0.8); if (h) { h.dead = true; this.bolt = null; this.events.push({ kind: "clash" }); } } } }
    // the hexes: dropped from the front of a column, now and then aimed
    this.hexT -= dt; const L = this.live();
    if (this.hexT <= 0 && L.length) { const R = this.rnd; this.hexT = Math.max(0.25, 1.1 - 0.06 * this.n) * (0.6 + R.next() * 0.8);
      if (this.hexes.length < Math.min(5, 2 + Math.floor(this.n / 3))) { const front = new Map(); for (const f of L) if (!front.has(f.c) || front.get(f.c).y < f.y) front.set(f.c, f); const fs = [...front.values()];
        const f = R.chance(0.4) ? fs.reduce((a, b) => (Math.abs(a.x - P.x) < Math.abs(b.x - P.x) ? a : b)) : R.pick(fs); this.hexes.push({ x: f.x, y: f.y + 0.8, kind: R.int(0, 2), t: 0 }); this.events.push({ kind: "hex" }); } }
    for (const h of this.hexes) { h.y += HX.hexSpeed * Math.min(1.3, this.mul) * dt; h.t += dt; if (this.hitWard(h.x, h.y, 0.35)) h.dead = true; else if (Math.abs(h.y - HX.gunY) < 0.6 && Math.abs(h.x - P.x) < 1) { h.dead = true; this.lose(); } }
    this.hexes = this.hexes.filter((h) => !h.dead && h.y < HX.H);
    // the comet
    if (this.comet) { this.comet.x += this.comet.v * dt; if (this.comet.x < -3 || this.comet.x > HX.W + 3) this.comet = null; }
    else if ((this.cometT -= dt) <= 0 && L.length > 7) { const fromLeft = this.rnd.chance(0.5); this.comet = { x: fromLeft ? -2 : HX.W + 2, y: 2.5, v: fromLeft ? 6 : -6 }; this.cometT = 20 + this.rnd.next() * 10; this.events.push({ kind: "cometcome" }); }
    if (!this.extraGiven && this.score >= HX.extra) { this.extraGiven = true; this.lives += 1; this.events.push({ kind: "extra" }); }
    if (!this.live().length && !P.dead) { this.stage = "clear"; this.events.push({ kind: "clear" }); }
  }
  lose() { const P = this.p; if (P.dead) return; P.dead = 2; this.lives -= 1; this.bolt = null; this.events.push({ kind: "die" }); }
  update(dt) { for (let s = 0; s < dt / HX.step - 1e-9; s++) this.tick(HX.step); }
};
Object.assign(CM.Game.prototype, {
  hxState() { return this.cgStore().hx || null; },
  hxClaimed() { const F = this.cgStore(); F.hxCards = F.hxCards || {}; return F.hxCards; },
  hxLevel() {
    const S = this.hxState(); if (!S || S.stage !== "play") return null;
    if (!this.hxLive || this.hxLive.key !== `${S.seed}:${S.n}`) {
      if (this.hxLive && this.hxLive.key && this.hxLive.key.startsWith(`${S.seed}:`)) { const L = this.hxLive, keep = { score: L.score, lives: L.lives, extraGiven: L.extraGiven }; this.hxLive = new HX.Level(S.n, CM.hashSeed(`${S.seed}:${S.n}`), keep); this.hxLive.key = `${S.seed}:${S.n}`; }
      else { S.stage = "done"; S.last = S.last || { level: S.n, won: S.won, cards: [], lost: true }; this.saveCasino && this.saveCasino(); return null; }
    }
    return this.hxLive;
  },
  hxStart(bet) {
    const S0 = this.hxState(); if (S0 && S0.stage === "play" && this.hxLive && this.hxLive.key && this.hxLive.key.startsWith(`${S0.seed}:`)) return { error: "A game is on." };
    const why = this.cgStake("hexmarch", bet); if (why) return { error: why };
    const F = this.cgStore(); F.n += 1; F.hx = { stage: "play", n: 1, bet: Math.floor(bet), seed: `${this.seed}:hexmarch:${F.n}`, won: 0, cards: [] };
    this.hxLive = new HX.Level(1, CM.hashSeed(`${F.hx.seed}:1`)); this.hxLive.key = `${F.hx.seed}:1`; this.saveCasino && this.saveCasino(); return F.hx;
  },
  // a level cleared: its gold (every play), and each third level a card the first time ever; on to the next
  hxCheck() {
    const S = this.hxState(), L = this.hxLive; if (!S || !L || S.stage !== "play") return null;
    if (L.stage === "clear") {
      const n = S.n, pay = Math.round(S.bet * HX.pay(n)), C = this.hxClaimed(); let card = null;
      if (n % HX.cardEvery === 0 && !C[n]) { card = this.cgTierCard(CM.cardTierFor(n), `The Hexmarch, level ${n} cleared!`, new CM.Random(CM.hashSeed(`${this.seed}:hexmarch:card:${n}`))); C[n] = card || true; if (card) S.cards.push(card); }
      this.cgPay("hexmarch", pay); S.won += pay; S.n += 1; this.saveCasino && this.saveCasino(); this.emit("change");
      this.hxLevel(); return { cleared: n, pay, card };
    }
    if (L.stage === "over") { S.stage = "done"; S.last = { level: S.n, score: L.score, won: S.won, cards: S.cards.slice() }; const F = this.cgStore(); F.hxBest = Math.max(F.hxBest || 0, L.score); this.hxLive = null; this.saveCasino && this.saveCasino(); this.emit("change"); return { over: true }; }
    return null;
  },
});
