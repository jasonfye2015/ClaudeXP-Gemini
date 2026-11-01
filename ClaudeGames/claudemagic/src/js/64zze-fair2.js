"use strict";
// More of the fairground (v15.8):
// - Hoop-la: ring toss - ten wooden rings at a table of bottles, green at the front (1), blue behind (2), gold at the
//   back (5) and the one red bottle in the middle of the back row (10). Aim with where the ring is let go, power with how
//   long it is held; a far throw strays more. A ring that drops over a neck scores; gold by the total, a ticket a point,
//   a card the first time ever past each high mark (it is one of the fair games of 64zz-fair.js).
// - The Crossbow Range: a shooting gallery - each round targets ride three rails across the back of the booth, tin
//   ducks (10), little dragons that hurry (25), gold stars that flash past (50) - and the keeper's lantern, which costs
//   50 if hit. Eighteen bolts a round, a bullseye (the ring's middle) doubles; make the round's mark to go on, more each
//   round; miss it and a life is gone. Two lives. An arcade cabinet (64zr-arcfw.js).
// The windows are 76zz-hoopla.js and 76zza-range.js.
{ const FA = CM.FAIR;
  FA.BOTTLES = []; for (let r = 0; r < 5; r++) for (let c = 0; c < 6; c++) FA.BOTTLES.push({ x: -0.75 + c * 0.3, y: 0.15 + r * 0.2, pts: r < 2 ? 1 : r < 4 ? 2 : c === 2 || c === 3 ? (c === 2 ? 10 : 5) : 5 });
  FA.rings = { name: "Hoop-la", balls: 10, ticketPer: 1, MARKS: [25, 40, 60], PAY: [[5, 0.3], [10, 0.65], [15, 0.95], [20, 1.25], [30, 1.7], [40, 2.4], [60, 4]], hitR: 0.032,
    throwAt(aim, power, R) { const g = () => (R.next() + R.next() + R.next() - 1.5) * 0.8, s = 0.05 + 0.1 * power, x = aim + g() * s, y = 0.05 + power * 1.0 + g() * s; let best = null; for (const B of FA.BOTTLES) { const d = Math.hypot(B.x - x, B.y - y); if (d < FA.rings.hitR && (!best || d < best.d)) best = { d, B }; }
      return best ? { x: best.B.x, y: best.B.y, pts: best.B.pts, label: `${best.B.pts}` } : { x, y, pts: 0, label: y > 1.08 || Math.abs(x) > 0.95 ? "Off the table" : "Rattles off" }; } };
  if (CM.CLUB && !CM.CLUB.BOARDS.includes("rings")) CM.CLUB.BOARDS.push("rings"); if (CM.DAILY) CM.DAILY.MARKS.rings = [1, 2, 3];
  // the crossbow range, a level a round
  CM.CB = { W: 480, H: 360, lives: 2, bolts: 18, time: 40, RAILS: [70, 140, 210],
    KINDS: { duck: { pts: 10, r: 15, v: 60 }, dragon: { pts: 25, r: 14, v: 115 }, star: { pts: 50, r: 11, v: 210 }, lantern: { pts: -50, r: 13, v: 50 } } };
  const CB = CM.CB;
  CB.Level = class {
    constructor(n, seed, keep) { this.rnd = new CM.Random(seed); this.n = n; this.events = []; this.stage = "play"; Object.assign(this, keep || { score: 0, lives: CB.lives }); this.need = 180 + 60 * n; this.mul = 1 + Math.min(0.8, (n - 1) * 0.08); this.reset(); }
    reset() { this.t = CB.time; this.bolts = CB.bolts; this.got = 0; this.targets = []; this.spawnT = 0; this.ids = 0; this.dead = 0; }
    spawn() { const R = this.rnd, rail = R.int(0, 2), r = R.next(), kind = r < 0.08 + 0.01 * this.n ? "star" : r < 0.3 + 0.02 * this.n ? "dragon" : r < 0.4 + 0.01 * this.n ? "lantern" : "duck", dir = rail % 2 ? -1 : 1;
      this.targets.push({ id: this.ids++, kind, rail, x: dir > 0 ? -30 : CB.W + 30, y: CB.RAILS[rail], dir, v: CB.KINDS[kind].v * this.mul * (0.85 + R.next() * 0.3), hit: 0, bob: R.next() * 6 }); }
    shoot(x, y) { if (this.stage !== "play" || this.dead || this.bolts <= 0 || this.t <= 0) return; this.bolts -= 1; this.events.push({ kind: "loose", x, y });
      let best = null; for (const T of this.targets) { if (T.hit) continue; const d = Math.hypot(T.x - x, T.y - y); if (d < CB.KINDS[T.kind].r && (!best || d < best.d)) best = { d, T }; }
      if (!best) { this.events.push({ kind: "miss", x, y }); return; } const T = best.T, K = CB.KINDS[T.kind], bull = best.d < K.r * 0.3 && K.pts > 0, pts = K.pts * (bull ? 2 : 1); T.hit = 0.6; this.score = Math.max(0, this.score + pts); this.got += pts; this.events.push({ kind: "hit", x: T.x, y: T.y, pts, bull, what: T.kind }); }
    update(dt) {
      if (this.stage !== "play") return;
      if (this.dead) { this.dead -= dt; if (this.dead <= 0) { this.dead = 0; if (this.lives <= 0) { this.stage = "over"; this.events.push({ kind: "over" }); } else this.reset(); } return; }
      this.t -= dt; if ((this.spawnT -= dt) <= 0) { this.spawnT = Math.max(0.35, 0.9 - 0.04 * this.n) * (0.6 + this.rnd.next() * 0.8); this.spawn(); }
      for (const T of this.targets) { if (T.hit) T.hit -= dt; else T.x += T.dir * T.v * dt; } this.targets = this.targets.filter((T) => !(T.hit < 0) && T.x > -50 && T.x < CB.W + 50);
      if (this.got >= this.need) { this.stage = "clear"; this.events.push({ kind: "clear" }); return; }
      if (this.t <= 0 || this.bolts <= 0) { this.lives -= 1; this.dead = 1.6; this.events.push({ kind: "short", got: this.got, need: this.need }); }
    }
  };
  CM.ARC.add("range", { name: "The Crossbow Range", Level: CB.Level, marks: [2, 3, 5] });
}
