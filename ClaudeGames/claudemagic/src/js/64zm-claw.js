"use strict";
// The Wishing Claw (the thirty-sixth big update - v14.6): three claw machines on the Gilded Joker's floor - copper,
// silver and gold, each with its own glass case and its own pit of prizes kept between visits: gold pouches, hoards,
// card capsules, weapons, armour, shields, helms and mystery eggs. One try a price. Hold to slide the claw right, let
// go; hold to send it back, let go - and it drops (or the time runs out and it drops where it is). It grips the
// nearest prize under it, more surely the closer to its middle and the lighter the prize; lifts; carries it to the
// chute in the front corner - and may lose it on the way (a prize dropped over the chute falls in all the same). What
// falls in the chute is the party's: gold, a Claudescryption card, or a real piece of gear made at the machine's depth
// (the gold machine's often enchanted). The silver machine waits for a party that has been to the fourth floor, the
// gold one for the tenth. The window: 76zc-claw.js.
CM.CW = {
  W: 10, D: 6, CHUTE: { x: 1.9, z: 1.7 }, home: { x: 0.9, z: 0.8 }, move: 2.4, drop: 2.2, lift: 2.0, carry: 2.4, time: 15, reach: 0.4, step: 1 / 60,
  TIERS: {
    copper: { name: "the Copper Claw", price: 25, depth: 3, card: "common", affix: 0.12, need: 0 },
    silver: { name: "the Silver Claw", price: 120, depth: 9, card: "better", affix: 0.3, need: 4 },
    gold: { name: "the Gold Claw", price: 400, depth: 18, card: "rare", affix: 0.55, need: 10 },
  },
  // a prize's size, how surely it is gripped, how likely it slips on the way, and how often it is put in the pit
  PRIZES: {
    pouch: { r: 0.5, grip: 0.88, slip: 0.1, w: 30, gold: 1.8 }, hoard: { r: 0.78, grip: 0.48, slip: 0.3, w: 9, gold: 6 },
    card: { r: 0.48, grip: 0.74, slip: 0.12, w: 11 }, egg: { r: 0.52, grip: 0.68, slip: 0.14, w: 12 },
    weapon: { r: 0.72, grip: 0.46, slip: 0.3, w: 9 }, armor: { r: 0.84, grip: 0.4, slip: 0.32, w: 8 }, shield: { r: 0.7, grip: 0.5, slip: 0.25, w: 8 }, helm: { r: 0.6, grip: 0.56, slip: 0.2, w: 8 },
  },
  pit: 16, restock: 11,
};
const CW = CM.CW;
CW.inChute = (x, z) => x < CW.CHUTE.x && z < CW.CHUTE.z;
// a prize for the pit, somewhere clear of the chute and not on top of another
CW.place = (pit, kind, R) => { const r = CW.PRIZES[kind].r; for (let k = 0; k < 60; k++) { const x = r + 0.2 + R.next() * (CW.W - 2 * r - 0.4), z = r + 0.2 + R.next() * (CW.D - 2 * r - 0.4); if (CW.inChute(x - r, z - r) || CW.inChute(x - r * 0.5, z - r * 0.5)) continue; if (pit.some((q) => Math.hypot(q.x - x, q.z - z) < (CW.PRIZES[q.kind].r + r) * 0.85)) continue; return { x, z }; } return null; };
CW.stock = (pit, R, ids) => { const kinds = Object.keys(CW.PRIZES), total = kinds.reduce((t, k) => t + CW.PRIZES[k].w, 0);
  while (pit.length < CW.pit) { let roll = R.next() * total, kind = kinds[0]; for (const k of kinds) { roll -= CW.PRIZES[k].w; if (roll <= 0) { kind = k; break; } } const at = CW.place(pit, kind, R); if (!at) break; pit.push({ id: ids.n++, kind, x: at.x, z: at.z, rot: R.next() * 6.28 }); } };
// one try at a machine: the claw's journey, step by step
CW.Try = class {
  constructor(pit, seed) {
    this.pit = pit; this.rnd = new CM.Random(seed); this.events = []; this.x = CW.home.x; this.z = CW.home.z; this.y = 1; this.open = 1; this.stage = "x"; this.time = CW.time; this.held = null; this.result = null; this.hold = false; this.used = { x: false, z: false };
  }
  input(hold) { this.hold = !!hold; }
  // where the claw's grip lands: the nearest prize under it, and how surely it holds
  aim() { let best = null, bd = Infinity; for (const q of this.pit) { const d = Math.hypot(q.x - this.x, q.z - this.z); if (d < bd) { bd = d; best = q; } } if (!best) return null; const P = CW.PRIZES[best.kind], reach = P.r + CW.reach; if (bd >= reach) return { prize: best, chance: 0 }; const align = 1 - bd / reach; return { prize: best, chance: P.grip * (0.3 + 0.7 * align), d: bd }; }
  tick(dt) {
    const S = this.stage;
    if (S === "x" || S === "z") { this.time -= dt; const ax = S;
      if (this.hold) { this.used[ax] = true; if (ax === "x") this.x = Math.min(CW.W - 0.4, this.x + CW.move * dt); else this.z = Math.min(CW.D - 0.4, this.z + CW.move * dt); }
      else if (this.used[ax]) { this.stage = ax === "x" ? "z" : "drop"; this.events.push({ kind: ax === "x" ? "stopx" : "stopz" }); }
      if (this.time <= 0) { this.stage = "drop"; this.events.push({ kind: "timeup" }); } return; }
    if (S === "drop") { this.open = 1; this.y -= CW.drop * dt; if (this.y <= 0.12) { this.y = 0.12; this.stage = "grip"; this.t = 0.45; this.events.push({ kind: "down" }); } return; }
    if (S === "grip") { this.open = Math.max(0, this.t / 0.45); this.t -= dt; if (this.t <= 0) {
        const A = this.aim(); this.jostle(A && A.prize);
        if (A && A.chance > 0 && this.rnd.chance(A.chance)) { this.held = A.prize; this.events.push({ kind: "grab", prize: A.prize }); } else this.events.push({ kind: "miss", near: !!(A && A.chance > 0) });
        this.stage = "lift"; } return; }
    if (S === "lift") { this.y += CW.lift * dt; if (this.held) { this.held.x = this.x; this.held.z = this.z; } if (this.y >= 1) { this.y = 1; if (!this.held) { this.stage = "home"; return; } this.stage = "carry"; const L = Math.hypot(this.x - CW.home.x, this.z - CW.home.z); this.hazard = L > 0.1 ? -Math.log(1 - CW.PRIZES[this.held.kind].slip) / (L / CW.carry) : 0; } return; }
    if (S === "carry" || S === "home") {
      const dx = CW.home.x - this.x, dz = CW.home.z - this.z, d = Math.hypot(dx, dz), m = Math.min(d, CW.carry * dt); if (d > 1e-6) { this.x += (dx / d) * m; this.z += (dz / d) * m; }
      if (this.held) { this.held.x = this.x; this.held.z = this.z; if (this.rnd.chance(Math.min(1, this.hazard * dt))) { const q = this.held; this.held = null; this.events.push({ kind: "slip", prize: q }); if (CW.inChute(q.x, q.z)) return this.won(q, true); this.settle(q); this.stage = "home"; return; } }
      if (d <= 1e-6) { if (this.held) return this.won(this.held, false); this.stage = "done"; this.result = { prize: null }; this.events.push({ kind: "empty" }); } return; }
  }
  won(q, lucky) { this.pit.splice(this.pit.indexOf(q), 1); this.held = null; this.stage = "done"; this.result = { prize: q, lucky }; this.events.push({ kind: "chute", prize: q, lucky }); }
  // a dropped prize finds a free spot near where it fell
  settle(q) { const r = CW.PRIZES[q.kind].r; q.x = Math.max(r, Math.min(CW.W - r, q.x)); q.z = Math.max(r, Math.min(CW.D - r, q.z)); for (let k = 0; k < 20; k++) { const o = this.pit.find((p) => p !== q && Math.hypot(p.x - q.x, p.z - q.z) < (CW.PRIZES[p.kind].r + r) * 0.8); if (!o) break; const a = this.rnd.next() * 6.28; q.x = Math.max(r, Math.min(CW.W - r, q.x + Math.cos(a) * 0.4)); q.z = Math.max(r, Math.min(CW.D - r, q.z + Math.sin(a) * 0.4)); } if (CW.inChute(q.x - r, q.z - r)) { q.x = Math.max(q.x, CW.CHUTE.x + r); } }
  // the claw coming down nudges what is close by
  jostle(skip) { for (const q of this.pit) { if (q === skip) continue; const dx = q.x - this.x, dz = q.z - this.z, d = Math.hypot(dx, dz); if (d < 1.3 && d > 1e-3) { const push = (1.3 - d) * 0.25 * this.rnd.next(), r = CW.PRIZES[q.kind].r; q.x = Math.max(r, Math.min(CW.W - r, q.x + (dx / d) * push)); q.z = Math.max(r, Math.min(CW.D - r, q.z + (dz / d) * push)); if (CW.inChute(q.x - r * 0.5, q.z - r * 0.5)) q.x = CW.CHUTE.x + r; } } }
  update(dt) { for (let s = 0; s < dt / CW.step - 1e-9; s++) { if (this.stage === "done") return; this.tick(CW.step); } }
};
Object.assign(CM.Game.prototype, {
  cwDeepest() { return (this.trail || []).reduce((m, x) => Math.max(m, x[0] || 0), 0); },
  cwMachine(tier) { const F = this.cgStore(); F.claw = F.claw || {}; const M = F.claw[tier] = F.claw[tier] || { pit: [], ids: { n: 1 }, n: 0, won: 0 }; if (M.pit.length < CW.restock) CW.stock(M.pit, new CM.Random(CM.hashSeed(`${this.seed}:claw:${tier}:stock:${M.n}`)), M.ids); return M; },
  cwOpen(tier) { const T = CW.TIERS[tier]; return this.cwDeepest() >= T.need; },
  cwStart(tier) {
    const T = CW.TIERS[tier]; if (!T) return { error: "No such machine." }; if (!this.cwOpen(tier)) return { error: `The attendant shakes her head: ${T.name} is for parties that have been to floor ${T.need}.` };
    if (this.cwLive && this.cwLive.stage !== "done") return { error: "The claw is still moving." };
    const why = this.cgStake("claw", T.price); if (why) return { error: why };
    const M = this.cwMachine(tier); M.n += 1; this.cwLive = new CW.Try(M.pit, CM.hashSeed(`${this.seed}:claw:${tier}:${M.n}`)); this.cwLive.tier = tier; this.saveCasino && this.saveCasino(); return { ok: true };
  },
  // what came down the chute, made real
  cwSettle() {
    const L = this.cwLive; if (!L || L.stage !== "done" || L.settled) return null; L.settled = true; const tier = L.tier, T = CW.TIERS[tier], M = this.cwMachine(tier), q = L.result.prize;
    if (!q) { this.saveCasino && this.saveCasino(); return { prize: null }; }
    const R = new CM.Random(CM.hashSeed(`${this.seed}:claw:${tier}:prize:${q.id}`)), P = CW.PRIZES[q.kind], out = { prize: q.kind, lucky: L.result.lucky }; M.won += 1;
    if (P.gold) { const g = Math.round(T.price * P.gold * (0.8 + R.next() * 0.4)); this.cgPay("claw", g); out.gold = g; }
    else if (q.kind === "card") out.card = this.cgTierCard(T.card, `The Wishing Claw brought up a card capsule (${T.name}).`, R);
    else { let it = CM.makeItem(T.depth + R.int(-1, 1), R, q.kind === "egg" ? undefined : q.kind); if (it && R.chance(T.affix) && CM.affix) it = CM.affix(it, T.depth + 2, R) || it; if (it) { this.gain([it], "casino"); out.item = it; } }
    const F = this.cgStore(); F.clawPrizes = (F.clawPrizes || 0) + 1; this.saveCasino && this.saveCasino(); this.emit("change"); return out;
  },
});
