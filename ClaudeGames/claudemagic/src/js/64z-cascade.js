"use strict";
// The Gilded Cascade (the twenty-fifth big update - v13.5): a coin pusher on the Gilded Joker's floor. A brass shelf
// strewn with coins, a pusher that slides back and forth across its back, and side gutters near the front. Buy a cup
// of coins with gold (a coin is worth its cup's price), drop them where you like behind the shelf's edge; the pusher
// shoves the bed forward, and what goes over the front edge drops into your tray - what slips into a gutter is the
// house's. Now and then a prize is set on the bed with a coin: a gold nugget (ten coins), a Claudescryption card token,
// or a sealed item token (a real piece of gear by the party's depth); push it off the front and it is yours. The bed
// is kept between visits. Coins move only when pushed (shove by shove, the pusher's face and the coins against each
// other), so a play is the same for the same drops. The window is 76p-cascade.js.
CM.CS = {
  W: 300, D: 360, R: 11, faceMin: 70, faceMax: 150, period: 3.2, gutterFrom: 300, gutter: 20, step: 1 / 60, iters: 6,
  CUPS: [[20, 1], [20, 5], [20, 25]], NUGGET: 10, ODDS: { nugget: 1 / 250, card: 1 / 150, item: 1 / 250 }, startCoins: 125, maxDiscs: 240,
};
const CS = CM.CS;
CS.Bed = class {
  constructor(seed, saved) {
    this.rnd = new CM.Random(seed); this.t = 0; this.discs = []; this.events = []; this.ids = 0;
    if (saved && saved.discs) { this.t = saved.t || 0; for (const d of saved.discs) this.discs.push({ id: ++this.ids, x: d[0], y: d[1], v: d[2], k: d[3] || "coin", it: d[4] }); }
    else { for (let i = 0; i < CS.startCoins; i++) this.discs.push({ id: ++this.ids, x: CS.R + this.rnd.next() * (CS.W - 2 * CS.R), y: CS.faceMax + CS.R + this.rnd.next() * (CS.D - CS.faceMax - 3 * CS.R), v: 1, k: "coin" }); for (let k = 0; k < 12; k++) this.settle(); this.discs = this.discs.filter((d) => d.y < CS.D - CS.R && d.x > 0 && d.x < CS.W); }
  }
  face(t = this.t) { return CS.faceMin + (CS.faceMax - CS.faceMin) * (0.5 - 0.5 * Math.cos((t / CS.period) * Math.PI * 2)); }
  // a coin dropped at x: it lands just in front of the pusher's face; a prize may come down with it
  drop(x, v) {
    const f = this.face(), R = CS.R; x = Math.max(R, Math.min(CS.W - R, x));
    const d = { id: ++this.ids, x: x + (this.rnd.next() - 0.5) * 6, y: f + R + 2 + this.rnd.next() * 24, v, k: "coin" }; this.discs.push(d); this.events.push({ kind: "drop", d }); this.dirty = true;
    const r = this.rnd.next(), O = CS.ODDS; let prize = null;
    if (r < O.item) prize = "item"; else if (r < O.item + O.card) prize = "card"; else if (r < O.item + O.card + O.nugget) prize = "nugget";
    if (prize) { const p = { id: ++this.ids, x: R + this.rnd.next() * (CS.W - 2 * R), y: f + R + 4 + this.rnd.next() * 40, v: prize === "nugget" ? v * CS.NUGGET : 0, k: prize }; this.discs.push(p); this.events.push({ kind: "prize", d: p }); }
    while (this.discs.length > CS.maxDiscs) { const i = this.discs.findIndex((q) => q.k === "coin"); this.discs.splice(i, 1); }
    return d;
  }
  // a little time: the pusher moves; what it touches is shoved; the coins push each other apart; the edges take what is over them
  update(dt) {
    const out = []; for (let s = 0; s < dt / CS.step - 1e-9; s++) out.push(...this.tick(CS.step)); return out;
  }
  tick(dt) {
    const f0 = this.face(); this.t += dt; const f = this.face(), R = CS.R, D = CS.discs;
    let touched = this.dirty; this.dirty = false; if (f > f0) for (const d of this.discs) if (d.y - R < f) { d.y = f + R; touched = true; }
    if (touched) this.settle();
    const off = []; this.discs = this.discs.filter((d) => { if (d.y > CS.D) { off.push({ d, where: "front" }); return false; } if (d.x < 0 || d.x > CS.W) { off.push({ d, where: "gutter" }); return false; } return true; });
    for (const o of off) this.events.push({ kind: o.where, d: o.d });
    void D; return off;
  }
  // the coins pushed apart; never back into the pusher, never through the side walls behind the gutters (a grid of
  // cells, integer keys; it stops early once nothing overlaps)
  settle() {
    const R = CS.R, f = this.face(), L = this.discs, n = L.length, cell = 2 * R, R4 = 4 * R * R, GW = 40;
    for (let it = 0; it < CS.iters; it++) {
      const grid = new Map(); for (let i = 0; i < n; i++) { const d = L[i], k = (Math.floor(d.x / cell) + 4) + (Math.floor(d.y / cell) + 4) * GW; const c = grid.get(k); if (c) c.push(i); else grid.set(k, [i]); }
      let moved = false;
      for (let i = 0; i < n; i++) { const a = L[i], cx = Math.floor(a.x / cell) + 4, cy = Math.floor(a.y / cell) + 4;
        for (let gy = cy - 1; gy <= cy + 1; gy++) for (let gx = cx - 1; gx <= cx + 1; gx++) { const c = grid.get(gx + gy * GW); if (!c) continue;
          for (let q = 0; q < c.length; q++) { const j = c[q]; if (j <= i) continue; const b = L[j], dx = b.x - a.x, dy = b.y - a.y, d2 = dx * dx + dy * dy; if (d2 >= R4) continue; moved = true; const d = Math.sqrt(d2) || 0.01, push = (2 * R - d) / 2, nx = d2 ? dx / d : 1, ny = d2 ? dy / d : 0;
            const aBack = a.y - ny * push < f + R, bBack = b.y + ny * push < f + R, ka = bBack ? 2 : aBack ? 0 : 1, kb = aBack ? 2 : bBack ? 0 : 1;
            a.x -= nx * push * ka; a.y -= ny * push * ka; b.x += nx * push * kb; b.y += ny * push * kb; } } }
      for (const d of L) { if (d.y < f + R) d.y = f + R; if (d.y < CS.gutterFrom) d.x = Math.max(R, Math.min(CS.W - R, d.x)); else { const gx = CS.gutter; if (d.x < -gx) d.x = -gx; if (d.x > CS.W + gx) d.x = CS.W + gx; } }
      if (!moved) break;
    }
  }
  toJSON() { return { t: Math.round(this.t * 100) / 100, discs: this.discs.map((d) => [Math.round(d.x * 10) / 10, Math.round(d.y * 10) / 10, d.v, d.k === "coin" ? 0 : d.k, d.it]) }; }
};
Object.assign(CM.Game.prototype, {
  csStore() { const F = this.cgStore(); F.cs = F.cs || { coins: [], won: 0, n: 0 }; return F.cs; },
  csBed() { const S = this.csStore(); if (!this.csLive) { this.csLive = new CS.Bed(CM.hashSeed(`${this.seed}:cascade:${S.n}`), S.bed); } return this.csLive; },
  csKeep() { const S = this.csStore(); if (this.csLive) S.bed = this.csLive.toJSON(); this.saveCasino && this.saveCasino(); },
  // a cup of coins bought: twenty at its price each
  csBuy(cup) { const C = CS.CUPS[cup]; if (!C) return { error: "No such cup." }; const why = this.cgStake("cascade", C[0] * C[1]); if (why) return { error: why }; const S = this.csStore(); for (let i = 0; i < C[0]; i++) S.coins.push(C[1]); S.coins.sort((a, b) => a - b); this.csKeep(); return { n: C[0], v: C[1] }; },
  csDrop(x, v) {
    const S = this.csStore(); let i = v === undefined ? S.coins.length - 1 : S.coins.lastIndexOf(v); if (i < 0) return null; const val = S.coins.splice(i, 1)[0], B = this.csBed();
    B.rnd = new CM.Random(CM.hashSeed(`${this.seed}:cascade:drop:${S.n++}`)); return B.drop(x, val);
  },
  // what came over the front edge: coins and nuggets to gold, a card token to a card, an item token to a thing
  csCollect(off) {
    let gold = 0; const got = [];
    for (const o of off) { if (o.where !== "front") continue; const d = o.d;
      if (d.k === "coin" || d.k === "nugget") gold += d.v;
      else if (d.k === "card") { const R = new CM.Random(CM.hashSeed(`${this.seed}:cascade:card:${d.id}:${this.csStore().n}`)), card = this.cgCard(R.chance(0.2), "The Gilded Cascade drops a card token!", R); if (card) got.push({ card }); }
      else if (d.k === "item") { const depth = Math.max(2, Math.min(CM.BOTTOM || 50, (this.trail || []).reduce((m, x) => Math.max(m, x[0] || 0), 0) || 5)), R = new CM.Random(CM.hashSeed(`${this.seed}:cascade:item:${d.id}:${this.csStore().n}`)); let it = CM.makeItem(depth, R); if (R.chance(0.4) && CM.affix) it = CM.affix(it, depth, R) || it; this.gain([it], "casino"); got.push({ item: it }); } }
    if (gold) { this.cgPay("cascade", gold); this.csStore().won += gold; }
    if (gold || got.length) { this.csKeep(); this.emit("change"); }
    return { gold, got };
  },
  // coins left in the cup when the party goes: sold back at their price
  csCashCup() { const S = this.csStore(), v = S.coins.reduce((t, c) => t + c, 0); if (!v) return 0; S.coins = []; this.gold += v; const F = this.cgStore(); F.wagered.cascade = Math.max(0, (F.wagered.cascade || 0) - v); this.csKeep(); this.emit("change"); return v; },
});
