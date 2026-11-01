"use strict";
// The Rampart Battery (v15.6): a defence game on the town wall. Embers fall out of the night sky toward six cottages and
// the three mana wells on the rampart. Aim and loose a bolt (the nearest well with charges left fires it): where it
// reaches it bursts into a ring of light that swells and fades, and any ember inside is put out. Each well holds ten
// charges a wave. From the third wave some embers split as they fall; from the fifth a fire-drake crosses, dropping
// its own. A wave is held when every ember is out: each charge left and each cottage standing pays. A well hit is dark
// for the rest of the wave; a cottage hit is gone. When the last cottage burns, the game is over (a cottage comes back
// every 10,000). Window: 76zn-rampart.js.
CM.RB = { W: 480, H: 400, ground: 368, charges: 10 };
{ const RB = CM.RB;
  RB.Level = class {
    constructor(n, seed, keep) {
      this.rnd = new CM.Random(seed); this.n = n; this.t = 0; this.events = []; this.stage = "play";
      Object.assign(this, keep || { score: 0, cottages: [true, true, true, true, true, true], bank: 0, nextBonus: 10000 }); this.cottages = this.cottages.slice();
      this.lives = this.cottages.filter(Boolean).length; this.wells = [40, 240, 440].map((x) => ({ x, y: RB.ground - 6, n: RB.charges, dark: false }));
      this.homes = [90, 135, 180, 300, 345, 390]; this.embers = []; this.bolts = []; this.bursts = []; this.toSend = 10 + 3 * n; this.sendT = 0.6; this.speed = 24 + 4 * n; this.drake = null; this.drakeT = 8; this.endT = 0;
    }
    targets() { const t = []; this.homes.forEach((x, i) => { if (this.cottages[i]) t.push({ x, y: RB.ground, home: i }); }); this.wells.forEach((w, i) => { if (!w.dark) t.push({ x: w.x, y: RB.ground, well: i }); }); return t; }
    ember(x, y) { const T = this.targets(); if (!T.length) return; const tg = this.rnd.pick(T), d = Math.hypot(tg.x - x, tg.y - y); this.embers.push({ x0: x, y0: y, x, y, tx: tg.x, ty: tg.y, vx: (tg.x - x) / d * this.speed, vy: (tg.y - y) / d * this.speed, split: this.n >= 3 && this.rnd.chance(0.25) ? 120 + this.rnd.next() * 100 : 0 }); }
    fire(x, y) {
      if (y > RB.ground - 30) y = RB.ground - 30; let best = null, bd = 1e9; for (const w of this.wells) if (!w.dark && w.n > 0) { const d = Math.abs(w.x - x); if (d < bd) { bd = d; best = w; } }
      if (!best || this.stage !== "play") { this.events.push({ kind: "empty" }); return; } best.n -= 1; const d = Math.hypot(x - best.x, y - best.y), sp = best === this.wells[1] ? 520 : 380;
      this.bolts.push({ x0: best.x, y0: best.y, x: best.x, y: best.y, tx: x, ty: y, vx: (x - best.x) / d * sp, vy: (y - best.y) / d * sp, left: d / sp }); this.events.push({ kind: "fire" });
    }
    update(dt) {
      if (this.stage !== "play") return; this.t += dt;
      if (this.toSend > 0 && (this.sendT -= dt) <= 0) { this.sendT = Math.max(0.25, 1.4 - 0.08 * this.n) * (0.5 + this.rnd.next()); const k = Math.min(this.toSend, this.rnd.int(1, 2 + Math.floor(this.n / 3))); for (let i = 0; i < k; i++) { this.ember(this.rnd.next() * RB.W, 0); this.toSend -= 1; } }
      if (this.n >= 5 && !this.drake && (this.drakeT -= dt) <= 0) { const L = this.rnd.chance(0.5); this.drake = { x: L ? -20 : RB.W + 20, y: 70 + this.rnd.next() * 80, vx: L ? 60 : -60, drop: 1 }; this.drakeT = 12; this.events.push({ kind: "drake" }); }
      if (this.drake) { const D = this.drake; D.x += D.vx * dt; D.drop -= dt; if (D.drop <= 0) { D.drop = 1.4; this.ember(D.x, D.y); } if (D.x < -40 || D.x > RB.W + 40) this.drake = null; }
      for (const b of this.bolts) { b.x += b.vx * dt; b.y += b.vy * dt; b.left -= dt; if (b.left <= 0) { b.gone = true; this.bursts.push({ x: b.tx, y: b.ty, t: 0 }); this.events.push({ kind: "burst", x: b.tx, y: b.ty }); } }
      this.bolts = this.bolts.filter((b) => !b.gone);
      for (const B of this.bursts) { B.t += dt; B.r = B.t < 0.5 ? (B.t / 0.5) * 34 : Math.max(0, 34 * (1 - (B.t - 0.5) / 0.6)); }
      this.bursts = this.bursts.filter((B) => B.t < 1.1);
      for (const e of this.embers) {
        e.x += e.vx * dt; e.y += e.vy * dt;
        if (e.split && e.y > e.split) { e.split = 0; for (let k = 0; k < 2; k++) this.ember(e.x, e.y); }
        for (const B of this.bursts) if (Math.hypot(e.x - B.x, e.y - B.y) < B.r) { e.gone = true; this.score += 25; this.events.push({ kind: "out", x: e.x, y: e.y, pts: 25 }); break; }
        if (!e.gone && e.y >= RB.ground) { e.gone = true; const hi = this.homes.findIndex((x, i) => this.cottages[i] && Math.abs(x - e.x) < 16), wi = this.wells.findIndex((w) => !w.dark && Math.abs(w.x - e.x) < 16);
          if (hi >= 0) { this.cottages[hi] = false; this.events.push({ kind: "burn", x: e.x, home: true }); } else if (wi >= 0) { this.wells[wi].dark = true; this.wells[wi].n = 0; this.events.push({ kind: "burn", x: e.x, well: true }); } else this.events.push({ kind: "thud", x: e.x }); }
      }
      if (this.drake) for (const B of this.bursts) if (Math.hypot(this.drake.x - B.x, this.drake.y - B.y) < B.r + 8) { this.score += 300; this.events.push({ kind: "drakedown", x: this.drake.x, y: this.drake.y, pts: 300 }); this.drake = null; break; }
      this.embers = this.embers.filter((e) => !e.gone); this.lives = this.cottages.filter(Boolean).length;
      if (!this.lives) { this.stage = "over"; this.events.push({ kind: "over" }); return; }
      if (this.toSend <= 0 && !this.embers.length && !this.drake && !this.bolts.length && !this.bursts.length) {
        const charges = this.wells.reduce((t, w) => t + w.n, 0), homes = this.cottages.filter(Boolean).length, mul = Math.min(6, 1 + Math.floor((this.n - 1) / 2)), pts = (charges * 5 + homes * 100) * mul; this.score += pts;
        while (this.score >= this.nextBonus) { this.nextBonus += 10000; const i = this.cottages.indexOf(false); if (i >= 0) { this.cottages[i] = true; this.events.push({ kind: "rebuild" }); } }
        this.stage = "clear"; this.events.push({ kind: "held", charges, homes, pts });
      }
    }
  };
  CM.ARC.add("rampart", { name: "The Rampart Battery", Level: RB.Level, keep: (L) => ({ score: L.score, cottages: L.cottages, nextBonus: L.nextBonus }), marks: [3, 5, 8] });
}
