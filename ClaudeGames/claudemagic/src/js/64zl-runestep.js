"use strict";
// Runestep Pyramid (the thirty-fifth big update - v14.5): a hopping game on the Gilded Joker's floor. A pyramid of
// twenty-eight rune-cubes, seven rows, seen from the corner; a glimmerkin hops diagonally from cube to cube, and each
// landing lights a cube's top a step nearer the finished colour - one step on levels 1-2, two from 3, and from 6 a
// hop on a finished cube turns it back. Light every cube to clear the level. Ember-balls drop in and bounce down;
// a violet egg bounces to the bottom and hatches into the Sigil Serpent, who hops after the glimmerkin; from level 3
// a Smudge hops down undoing cubes (catch it for points); now and then a frost orb (catch it to freeze them all). Two
// wind-wisps wait off the sides: hop onto one to ride to the top, and a serpent close behind follows you off the edge.
// Hop off the pyramid anywhere else and you fall. Three lives (one more at 8,000). One stake a play: each level cleared
// pays gold, more each level, every play; and a Claudescryption card the first time ever each third level is cleared
// (3 common, 6 and 9 a stronger common, rare from 12). The window: 76zb-runestep.js.
CM.RP = {
  ROWS: 7, step: 1 / 60, lives: 3, extra: 8000, hop: 0.3, ride: 1.8, fall: 1.2, freeze: 4,
  enemyHop: { ember: 0.62, egg: 0.62, serpent: 0.66, smudge: 0.7, frost: 0.7 },
  SCORE: { tile: 25, serpentLured: 500, smudge: 300, frost: 100, wispLeft: 50, level: (n) => 1000 + 250 * n },
  cardEvery: 3, pay: (n) => 0.06 + 0.04 * n,
};
const RP = CM.RP;
// the four hops: up-left, up-right, down-left, down-right (row, col)
RP.MOVES = { ul: [-1, -1], ur: [-1, 0], dl: [1, 0], dr: [1, 1] };
// hops between two cubes: the four moves change the column by one, or (row - column) by one
RP.dist = (a, b) => Math.abs(b[1] - a[1]) + Math.abs(b[0] - b[1] - (a[0] - a[1]));
RP.on = (r, c) => r >= 0 && r < RP.ROWS && c >= 0 && c <= r;
RP.Level = class {
  constructor(n, seed, keep) {
    const R = this.rnd = new CM.Random(seed); this.n = n; this.t = 0; this.events = []; this.stage = "play"; Object.assign(this, keep || { score: 0, lives: RP.lives, extraGiven: false });
    this.need = n <= 2 ? 1 : 2; this.toggle = n >= 6; this.tiles = Array.from({ length: RP.ROWS }, (_, r) => Array(r + 1).fill(0));
    // the wind-wisps: one off each side, on rows chosen by the seed
    const rows = [2, 3, 4, 5]; this.wisps = [{ r: R.pick(rows), side: -1, used: false }, { r: R.pick(rows), side: 1, used: false }];
    this.mul = 1 + Math.min(0.6, (n - 1) * 0.06); this.foes = []; this.spawnT = 2.5; this.eggT = 6 + R.next() * 4; this.frozen = 0; this.spawnHop();
  }
  spawnHop() { this.p = { r: 0, c: 0, fr: 0, fc: 0, hopT: 0, dead: 0, ride: null, fallT: 0 }; this.want = null; }
  done(r, c) { return this.tiles[r][c] >= this.need; }
  left() { let k = 0; for (let r = 0; r < RP.ROWS; r++) for (let c = 0; c <= r; c++) if (!this.done(r, c)) k++; return k; }
  input(dir) { if (dir) this.want = dir; }
  land(r, c) {
    const v = this.tiles[r][c];
    if (v < this.need) { this.tiles[r][c] = v + 1; this.score += RP.SCORE.tile; this.events.push({ kind: "tile", r, c, v: v + 1 }); }
    else if (this.toggle) { this.tiles[r][c] = this.need - 1; this.events.push({ kind: "untile", r, c }); }
    if (!this.left()) { const bonus = RP.SCORE.level(this.n) + this.wisps.filter((w) => !w.used).length * RP.SCORE.wispLeft; this.score += bonus; this.stage = "clear"; this.events.push({ kind: "clear", bonus }); }
  }
  // the glimmerkin's hop: onto a cube, onto a wisp, or off into the air
  hop(dir) {
    const P = this.p; if (P.dead || P.hopT > 0 || P.ride || P.fallT) return; const [dr, dc] = RP.MOVES[dir], r = P.r + dr, c = P.c + dc; P.face = dir;
    P.fr = P.r; P.fc = P.c; P.r = r; P.c = c; P.hopT = RP.hop; this.events.push({ kind: "hop" });
    if (!RP.on(r, c)) { const w = this.wisps.find((q) => !q.used && q.r === r && ((q.side < 0 && c === -1) || (q.side > 0 && c === r + 1))); if (w) { w.used = true; P.wispAt = w; } }
  }
  arrive() {
    const P = this.p;
    if (RP.on(P.r, P.c)) { this.land(P.r, P.c); return; }
    if (P.wispAt) { P.ride = { t: RP.ride, from: [P.r, P.c] }; this.events.push({ kind: "wisp" }); const S = this.foes.find((f) => f.kind === "serpent"); if (S && RP.dist([S.r, S.c], [P.r, P.c]) <= 3) { S.lured = { r: P.r, c: P.c }; } return; }
    P.fallT = RP.fall; this.events.push({ kind: "fall" });
  }
  // the enemies' hops: down at random; the serpent toward the glimmerkin; at the bottom the egg hatches
  foeHop(f) {
    const R = this.rnd, P = this.p;
    if (f.kind === "serpent") {
      if (f.lured) { const L = f.lured; f.fr = f.r; f.fc = f.c; const d = Object.values(RP.MOVES).map(([dr, dc]) => [f.r + dr, f.c + dc]).sort((a, b) => Math.hypot(a[0] - L.r, a[1] - L.c) - Math.hypot(b[0] - L.r, b[1] - L.c))[0]; f.r = d[0]; f.c = d[1]; if (!RP.on(f.r, f.c)) { f.falling = RP.fall; this.score += RP.SCORE.serpentLured; this.events.push({ kind: "lured", pts: RP.SCORE.serpentLured }); } return; }
      const tr = P.ride ? 0 : P.r, tc = P.ride ? 0 : P.c, opts = Object.values(RP.MOVES).map(([dr, dc]) => [f.r + dr, f.c + dc]).filter(([r, c]) => RP.on(r, c));
      opts.sort((a, b) => RP.dist(a, [tr, tc]) - RP.dist(b, [tr, tc]));
      f.fr = f.r; f.fc = f.c; [f.r, f.c] = opts[0]; return;
    }
    f.fr = f.r; f.fc = f.c; const d = R.chance(0.5) ? RP.MOVES.dl : RP.MOVES.dr; f.r += d[0]; f.c += d[1];
    if (f.r >= RP.ROWS) { if (f.kind === "egg") { f.r = RP.ROWS - 1; f.c = Math.min(f.c, f.r); f.kind = "serpent"; this.events.push({ kind: "hatch" }); } else f.gone = true; return; }
    if (f.kind === "smudge" && this.tiles[f.r][f.c] > 0) { this.tiles[f.r][f.c] -= 1; this.events.push({ kind: "untile", r: f.r, c: f.c }); }
  }
  spawnFoes(dt) {
    const R = this.rnd, has = (k) => this.foes.some((f) => f.kind === k);
    if ((this.spawnT -= dt) <= 0) { this.spawnT = Math.max(1.6, 4.2 - 0.25 * this.n) * (0.7 + R.next() * 0.6); const embers = this.foes.filter((f) => f.kind === "ember").length;
      let kind = "ember"; if (this.n >= 3 && !has("smudge") && R.chance(0.25)) kind = "smudge"; else if (!has("frost") && R.chance(0.08)) kind = "frost"; else if (embers >= 1 + Math.floor(this.n / 3)) kind = null;
      if (kind) { const c = R.int(0, 1); this.foes.push({ kind, r: 1, c, fr: -1, fc: c, t: 0.5, hopT: 0.5 }); this.events.push({ kind: "drop", foe: kind }); } }
    if (!has("egg") && !has("serpent") && (this.eggT -= dt) <= 0) { const c = R.int(0, 1); this.foes.push({ kind: "egg", r: 1, c, fr: -1, fc: c, t: 0.5, hopT: 0.5 }); this.eggT = 6; this.events.push({ kind: "drop", foe: "egg" }); }
  }
  lose(why) { const P = this.p; if (P.dead) return; P.dead = 1.6; this.lives -= 1; this.events.push({ kind: "die", why }); }
  tick(dt) {
    if (this.stage !== "play") return; this.t += dt; const P = this.p;
    if (P.dead) { P.dead -= dt; if (P.dead <= 0) { if (this.lives <= 0) { this.stage = "over"; this.events.push({ kind: "over" }); return; } const at = RP.on(P.r, P.c) ? [P.r, P.c] : [0, 0]; this.foes = []; this.spawnHop(); [this.p.r, this.p.c] = at; this.spawnT = 2; this.eggT = 4; } return; }
    if (P.fallT) { P.fallT -= dt; if (P.fallT <= 0) { P.fallT = 0; this.lose("fall"); this.p.r = 0; this.p.c = 0; } return; }
    if (P.ride) { P.ride.t -= dt; if (P.ride.t <= 0) { P.ride = null; P.wispAt = null; P.r = 0; P.c = 0; this.foes = this.foes.filter((f) => f.kind === "serpent" && f.lured); this.land(0, 0); } }
    if (P.hopT > 0) { P.hopT -= dt; if (P.hopT <= 0) { P.hopT = 0; this.arrive(); if (this.stage !== "play") return; } }
    if (!P.hopT && !P.ride && !P.fallT && this.want) { this.hop(this.want); this.want = null; }
    this.spawnFoes(dt); if (this.frozen > 0) this.frozen -= dt;
    for (const f of this.foes) {
      if (f.falling) { f.falling -= dt; if (f.falling <= 0) f.gone = true; continue; }
      if (this.frozen > 0 && f.hopT <= 0) continue;
      f.hopT -= dt; if (f.hopT <= 0) { this.foeHop(f); f.hopT = RP.enemyHop[f.kind] / this.mul; f.t = f.hopT; }
    }
    this.foes = this.foes.filter((f) => !f.gone);
    // meeting: on the same cube once both are down, or crossing mid-hop
    if (!P.ride && !P.fallT && RP.on(P.r, P.c)) for (const f of this.foes) {
      if (f.falling || !RP.on(f.r, f.c)) continue; const midF = f.hopT > (RP.enemyHop[f.kind] / this.mul) * 0.6, same = f.r === P.r && f.c === P.c && !P.hopT && !midF, cross = P.hopT > 0 && f.r === P.fr && f.c === P.fc && f.fr === P.r && f.fc === P.c;
      if (!same && !cross) continue;
      if (f.kind === "smudge") { f.gone = true; this.score += RP.SCORE.smudge; this.events.push({ kind: "catch", foe: "smudge", pts: RP.SCORE.smudge }); }
      else if (f.kind === "frost") { f.gone = true; this.frozen = RP.freeze; this.score += RP.SCORE.frost; this.events.push({ kind: "catch", foe: "frost", pts: RP.SCORE.frost }); }
      else { this.lose(f.kind); break; }
    }
    this.foes = this.foes.filter((f) => !f.gone);
    if (!this.extraGiven && this.score >= RP.extra) { this.extraGiven = true; this.lives += 1; this.events.push({ kind: "extra" }); }
  }
  update(dt) { for (let s = 0; s < dt / RP.step - 1e-9; s++) this.tick(RP.step); }
};
Object.assign(CM.Game.prototype, {
  rpState() { return this.cgStore().rp || null; },
  rpClaimed() { const F = this.cgStore(); F.rpCards = F.rpCards || {}; return F.rpCards; },
  rpLevel() {
    const S = this.rpState(); if (!S || S.stage !== "play") return null;
    if (!this.rpLive || this.rpLive.key !== `${S.seed}:${S.n}`) {
      if (this.rpLive && this.rpLive.key && this.rpLive.key.startsWith(`${S.seed}:`)) { const L = this.rpLive; this.rpLive = new RP.Level(S.n, CM.hashSeed(`${S.seed}:${S.n}`), { score: L.score, lives: L.lives, extraGiven: L.extraGiven }); this.rpLive.key = `${S.seed}:${S.n}`; }
      else { S.stage = "done"; S.last = S.last || { level: S.n, won: S.won, cards: [], lost: true }; this.saveCasino && this.saveCasino(); return null; }
    }
    return this.rpLive;
  },
  rpStart(bet) {
    const S0 = this.rpState(); if (S0 && S0.stage === "play" && this.rpLive && this.rpLive.key && this.rpLive.key.startsWith(`${S0.seed}:`)) return { error: "A game is on." };
    const why = this.cgStake("runestep", bet); if (why) return { error: why };
    const F = this.cgStore(); F.n += 1; F.rp = { stage: "play", n: 1, bet: Math.floor(bet), seed: `${this.seed}:runestep:${F.n}`, won: 0, cards: [] };
    this.rpLive = new RP.Level(1, CM.hashSeed(`${F.rp.seed}:1`)); this.rpLive.key = `${F.rp.seed}:1`; this.saveCasino && this.saveCasino(); return F.rp;
  },
  // a level cleared: its gold (every play), and each third level a card the first time ever; on to the next
  rpCheck() {
    const S = this.rpState(), L = this.rpLive; if (!S || !L || S.stage !== "play") return null;
    if (L.stage === "clear") {
      const n = S.n, pay = Math.round(S.bet * RP.pay(n)), C = this.rpClaimed(); let card = null;
      if (n % RP.cardEvery === 0 && !C[n]) { card = this.cgTierCard(CM.cardTierFor(n), `Runestep Pyramid, level ${n} cleared!`, new CM.Random(CM.hashSeed(`${this.seed}:runestep:card:${n}`))); C[n] = card || true; if (card) S.cards.push(card); }
      this.cgPay("runestep", pay); S.won += pay; S.n += 1; this.saveCasino && this.saveCasino(); this.emit("change");
      this.rpLevel(); return { cleared: n, pay, card };
    }
    if (L.stage === "over") { S.stage = "done"; S.last = { level: S.n, score: L.score, won: S.won, cards: S.cards.slice() }; const F = this.cgStore(); F.rpBest = Math.max(F.rpBest || 0, L.score); this.cgRecord && this.cgRecord("runestep", L.score, S.last.level); this.rpLive = null; this.saveCasino && this.saveCasino(); this.emit("change"); return { over: true }; }
    return null;
  },
});
