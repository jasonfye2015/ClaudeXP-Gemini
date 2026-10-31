"use strict";
// Moatleap (the thirty-fourth big update - v14.4): a crossing game on the Gilded Joker's floor. A toad starts on the
// near bank and hops, one square at a time, across five lanes of market road - handcarts, hay wagons, galloping riders
// and long ox-trains - to the grass verge, then across five lanes of castle moat on drifting logs and lily-turtles
// (some of which dive under for a moment) to the five lily-bays under the castle wall. Fill all five for the next
// level. Each toad has thirty seconds. A firefly sometimes settles in an empty bay for a bonus; from level 3 a pike
// lurks in one now and then. Carried off the edge, drowned, run down, out of time or into the wall: a life gone. Three
// lives (one more at 10,000). One stake a play: each level cleared pays gold, more each level, every play; and a
// Claudescryption card the first time ever each third level is cleared (3 common, 6 and 9 a stronger common, rare
// from 12). The same inputs give the same game. The window: 76za-moat.js.
CM.MQ = {
  W: 15, H: 13, step: 1 / 120, lives: 3, extra: 10000, time: 30, hop: 0.13, BAYS: [1, 4, 7, 10, 13], VERGE: 6, START: 12,
  // lanes from the top of the moat down to the near side of the road: [kind, length, count, speed, direction]
  RIVER: [["log", 3, 3, 1.4, 1], ["turtle", 2, 4, 1.7, -1], ["log", 4, 2, 2.2, 1], ["log", 2, 3, 1.2, 1], ["turtle", 3, 3, 1.5, -1]],
  ROAD: [["ox", 3, 2, 1.1, -1], ["rider", 1, 2, 3.4, 1], ["wagon", 2, 3, 1.6, -1], ["cart", 1, 3, 1.3, 1], ["cart", 1, 3, 1.0, -1]],
  dive: { period: 6, under: 1.3, warn: 1.0 },
  SCORE: { step: 10, home: 50, perSec: 10, fly: 200, level: 1000 },
  cardEvery: 3, pay: (n) => 0.06 + 0.04 * n,
};
const MQ = CM.MQ;
MQ.Level = class {
  constructor(n, seed, keep) {
    const R = this.rnd = new CM.Random(seed); this.n = n; this.t = 0; this.events = []; this.stage = "play"; Object.assign(this, keep || { score: 0, lives: MQ.lives, extraGiven: false });
    this.mul = 1 + Math.min(0.9, (n - 1) * 0.09); this.span = MQ.W + 5; this.bays = MQ.BAYS.map(() => false); this.fly = null; this.flyT = 6; this.pike = null; this.pikeT = 9;
    // each lane's things, spread round its loop with a little jitter
    this.lanes = []; const mk = (row, [kind, len, count, sp, dir], k) => { const c = Math.min(count + (n >= 4 && kind !== "log" && kind !== "turtle" ? 1 : 0), Math.floor(this.span / (len + 1.5))), gap = this.span / c, off = R.next() * gap;
      this.lanes.push({ row, kind, len: kind === "log" && n >= 6 ? Math.max(2, len - 1) : len, dir, speed: sp * this.mul * (kind === "rider" ? 1 : 1), things: Array.from({ length: c }, (_, i) => ({ x: off + i * gap + (R.next() - 0.5) * gap * 0.25, dives: kind === "turtle" && n >= 2 && (i % 2 === 0 || n >= 5), phase: R.next() * MQ.dive.period })) }); };
    MQ.RIVER.forEach((L, i) => mk(1 + i, L, i)); MQ.ROAD.forEach((L, i) => mk(MQ.VERGE + 1 + i, L, i)); this.spawn();
  }
  spawn() { this.toad = { x: Math.floor(MQ.W / 2), y: MQ.START, face: "up", hopT: 0, dead: 0, best: MQ.START, time: MQ.time }; }
  lane(y) { return this.lanes.find((l) => l.row === y); }
  // a thing's left edge on screen (things wrap round a loop a little wider than the screen)
  left(l, th) { return ((th.x % this.span) + this.span) % this.span - 2.5; }
  under(th) { if (!th.dives) return false; const p = (this.t + th.phase) % MQ.dive.period; return p > MQ.dive.period - MQ.dive.under; }
  sinking(th) { if (!th.dives) return false; const p = (this.t + th.phase) % MQ.dive.period; return p > MQ.dive.period - MQ.dive.under - MQ.dive.warn && !this.under(th); }
  input(dir) { if (dir) this.want = dir; }
  hop(dir) {
    const T = this.toad; if (T.dead || T.hopT > 0) return; T.face = dir; const [dx, dy] = { up: [0, -1], down: [0, 1], left: [-1, 0], right: [1, 0] }[dir];
    const nx = T.x + dx, ny = T.y + dy; if (ny > MQ.START || nx < -0.4 || nx > MQ.W - 0.6) return;
    T.x = nx; T.y = ny; T.hopT = MQ.hop; if (ny > MQ.VERGE || ny === MQ.VERGE) T.x = Math.round(T.x); this.events.push({ kind: "hop" });
    if (ny < T.best) { T.best = ny; this.score += MQ.SCORE.step; }
    if (ny === 0) this.reachTop();
  }
  reachTop() {
    const T = this.toad, k = MQ.BAYS.findIndex((b) => Math.abs(T.x - b) < 0.5);
    if (k < 0) return this.lose("wall"); if (this.bays[k]) return this.lose("full"); if (this.pike && this.pike.bay === k) return this.lose("pike");
    this.bays[k] = true; let pts = MQ.SCORE.home + Math.floor(T.time) * MQ.SCORE.perSec; if (this.fly && this.fly.bay === k) { pts += MQ.SCORE.fly; this.fly = null; this.events.push({ kind: "fly" }); }
    this.score += pts; this.events.push({ kind: "home", bay: k, pts });
    if (this.bays.every(Boolean)) { this.score += MQ.SCORE.level; this.stage = "clear"; this.events.push({ kind: "clear" }); return; }
    this.spawn();
  }
  lose(why) { const T = this.toad; if (T.dead) return; T.dead = 1.6; T.why = why; this.lives -= 1; this.events.push({ kind: "die", why, x: T.x, y: T.y }); }
  tick(dt) {
    if (this.stage !== "play") return; this.t += dt; const T = this.toad;
    for (const l of this.lanes) for (const th of l.things) th.x += l.dir * l.speed * dt;
    // the firefly and the pike visit empty bays
    if (this.fly) { if ((this.fly.t -= dt) <= 0 || this.bays[this.fly.bay]) this.fly = null; } else if ((this.flyT -= dt) <= 0) { const free = this.bays.map((b, i) => (b ? -1 : i)).filter((i) => i >= 0 && !(this.pike && this.pike.bay === i)); if (free.length) this.fly = { bay: this.rnd.pick(free), t: 5 }; this.flyT = 8 + this.rnd.next() * 6; }
    if (this.pike) { if ((this.pike.t -= dt) <= 0) this.pike = null; } else if (this.n >= 3 && (this.pikeT -= dt) <= 0) { const free = this.bays.map((b, i) => (b ? -1 : i)).filter((i) => i >= 0 && !(this.fly && this.fly.bay === i)); if (free.length > 1) { this.pike = { bay: this.rnd.pick(free), t: 4 }; this.events.push({ kind: "pike" }); } this.pikeT = Math.max(4, 11 - this.n * 0.5) + this.rnd.next() * 4; }
    if (T.dead) { T.dead -= dt; if (T.dead <= 0) { if (this.lives <= 0) { this.stage = "over"; this.events.push({ kind: "over" }); return; } this.spawn(); } return; }
    if (T.hopT > 0) T.hopT -= dt; if (this.want) { this.hop(this.want); this.want = null; } if (T.dead || this.stage !== "play") return;
    T.time -= dt; if (T.time <= 0) return this.lose("time");
    const l = this.lane(T.y);
    if (l && T.y < MQ.VERGE) { // the moat: on something, or in the water
      const on = l.things.find((th) => { const a = this.left(l, th); return T.x > a - 0.35 && T.x < a + l.len - 0.65 && !this.under(th); });
      if (!on) { if (T.hopT <= 0) return this.lose("water"); } else { T.x += l.dir * l.speed * dt; if (T.x < -0.5 || T.x > MQ.W - 0.5) return this.lose("edge"); }
    } else if (l) { // the road
      for (const th of l.things) { const a = this.left(l, th); if (T.x + 0.35 > a && T.x - 0.35 < a + l.len - 0.1) return this.lose("road"); }
    }
    if (!this.extraGiven && this.score >= MQ.extra) { this.extraGiven = true; this.lives += 1; this.events.push({ kind: "extra" }); }
  }
  update(dt) { for (let s = 0; s < dt / MQ.step - 1e-9; s++) this.tick(MQ.step); }
};
Object.assign(CM.Game.prototype, {
  mqState() { return this.cgStore().mq || null; },
  mqClaimed() { const F = this.cgStore(); F.mqCards = F.mqCards || {}; return F.mqCards; },
  mqLevel() {
    const S = this.mqState(); if (!S || S.stage !== "play") return null;
    if (!this.mqLive || this.mqLive.key !== `${S.seed}:${S.n}`) {
      if (this.mqLive && this.mqLive.key && this.mqLive.key.startsWith(`${S.seed}:`)) { const L = this.mqLive; this.mqLive = new MQ.Level(S.n, CM.hashSeed(`${S.seed}:${S.n}`), { score: L.score, lives: L.lives, extraGiven: L.extraGiven }); this.mqLive.key = `${S.seed}:${S.n}`; }
      else { S.stage = "done"; S.last = S.last || { level: S.n, won: S.won, cards: [], lost: true }; this.saveCasino && this.saveCasino(); return null; }
    }
    return this.mqLive;
  },
  mqStart(bet) {
    const S0 = this.mqState(); if (S0 && S0.stage === "play" && this.mqLive && this.mqLive.key && this.mqLive.key.startsWith(`${S0.seed}:`)) return { error: "A game is on." };
    const why = this.cgStake("moatleap", bet); if (why) return { error: why };
    const F = this.cgStore(); F.n += 1; F.mq = { stage: "play", n: 1, bet: Math.floor(bet), seed: `${this.seed}:moatleap:${F.n}`, won: 0, cards: [] };
    this.mqLive = new MQ.Level(1, CM.hashSeed(`${F.mq.seed}:1`)); this.mqLive.key = `${F.mq.seed}:1`; this.saveCasino && this.saveCasino(); return F.mq;
  },
  // a level cleared: its gold (every play), and each third level a card the first time ever; on to the next
  mqCheck() {
    const S = this.mqState(), L = this.mqLive; if (!S || !L || S.stage !== "play") return null;
    if (L.stage === "clear") {
      const n = S.n, pay = Math.round(S.bet * MQ.pay(n)), C = this.mqClaimed(); let card = null;
      if (n % MQ.cardEvery === 0 && !C[n]) { card = this.cgTierCard(CM.cardTierFor(n), `Moatleap, level ${n} cleared!`, new CM.Random(CM.hashSeed(`${this.seed}:moatleap:card:${n}`))); C[n] = card || true; if (card) S.cards.push(card); }
      this.cgPay("moatleap", pay); S.won += pay; S.n += 1; this.saveCasino && this.saveCasino(); this.emit("change");
      this.mqLevel(); return { cleared: n, pay, card };
    }
    if (L.stage === "over") { S.stage = "done"; S.last = { level: S.n, score: L.score, won: S.won, cards: S.cards.slice() }; const F = this.cgStore(); F.mqBest = Math.max(F.mqBest || 0, L.score); this.cgRecord && this.cgRecord("moatleap", L.score, S.last.level); this.mqLive = null; this.saveCasino && this.saveCasino(); this.emit("change"); return { over: true }; }
    return null;
  },
});
