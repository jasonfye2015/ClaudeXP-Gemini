"use strict";
// The luck games (v15.8):
// - The Pin Garden: pachinko. Balls are bought a gold apiece and shot up the rail with the handle; they rattle down
//   through the brass pins, and most are lost, but the start pockets pay 3 balls, the windmill cups 6, and the tulip
//   in the middle 4 and a spin of the three drums - three alike is Fever, 60 balls and a Claudescryption card. Balls
//   held are exchanged at the counter at any time: 85 coppers' worth of gold for each hundred, and a prize ticket for
//   every ten. The path of each ball is worked out here, the same for the same shot.
// - The Joker's Wheel: a big wheel of 54 slots - 24 ones, 15 twos, 7 fives, 4 tens, 2 twenties, a Joker and a Star at
//   forty; a bet on a number pays that many to one when the wheel stops on it, and the Joker brings a card besides.
// - Fortune Slips: scratch cards at 2, 10 and 50 gold - nine squares; three of the same prize wins it, three cards win a
//   Claudescryption card. Each slip is printed from its own seed before it is sold.
// - The Prize Wheel: once a real day, a free spin for tickets, gold, a potion or a card.
// The windows are 76zv-pachinko.js, 76zw-bigwheel.js, 76zx-scratch.js and 76zy-prizewheel.js.
CM.LUCK = {
  PC: { W: 300, H: 430, pinR: 3, ballR: 4.5, g: 520, rate: 0.85, ticketPer: 10, fever: 60,
    POCKETS: [{ id: "start", x: 88, y: 404, w: 8, pays: 3 }, { id: "start", x: 212, y: 404, w: 8, pays: 3 }, { id: "tulip", x: 150, y: 400, w: 7, pays: 4 }, { id: "mill", x: 52, y: 214, w: 4, pays: 6 }, { id: "mill", x: 248, y: 214, w: 4, pays: 6 }] },
  BW: { SLOTS: [], PAYS: { 1: 1, 2: 2, 5: 5, 10: 10, 20: 20, joker: 40, star: 40 } },
  SC: { KINDS: { copper: { price: 2, PRIZES: [[0.2, 2], [0.08, 4], [0.03, 10], [0.006, 40], [0.001, 200]], card: 0.004 }, silver: { price: 10, PRIZES: [[0.2, 10], [0.08, 20], [0.03, 50], [0.006, 200], [0.001, 1000]], card: 0.01 }, gold: { price: 50, PRIZES: [[0.2, 50], [0.08, 100], [0.03, 250], [0.006, 1000], [0.001, 5000]], card: 0.03 } } },
  PW: { SLICES: [["t5", "5 tickets", 18], ["t10", "10 tickets", 16], ["t25", "25 tickets", 10], ["t50", "50 tickets", 5], ["t100", "100 tickets", 1.5], ["g10", "10 gold", 14], ["g25", "25 gold", 8], ["potion", "a potion", 12], ["card", "a card", 2.5], ["t10b", "10 tickets", 13]] },
};
{ const L = CM.LUCK, PC = L.PC;
  // the wheel's 54 slots, spread out as on a real wheel
  { const counts = [[1, 24], [2, 15], [5, 7], [10, 4], [20, 2], ["joker", 1], ["star", 1]], order = []; const left = Object.fromEntries(counts.map(([k, n]) => [k, n]));
    for (let i = 0; i < 54; i++) { let best = null, bs = -1; for (const [k, n] of counts) { if (!left[k]) continue; const want = (n * (i + 1)) / 54 - (n - left[k]); if (want > bs) { bs = want; best = k; } } order.push(best); left[best] -= 1; } L.BW.SLOTS = order; }
  // pins in staggered rows; a clear lane down the sides of the windmills
  PC.PINS = []; for (let r = 0; r < 12; r++) { const y = 92 + r * 25, off = r % 2 ? 13 : 0; for (let x = 24 + off; x < PC.W - 18; x += 26) { if (r >= 4 && r <= 6 && (Math.abs(x - 52) < 16 || Math.abs(x - 248) < 16)) continue; PC.PINS.push([x, y]); } }
  // a ball's whole fall, from where the handle sends it in at the top
  PC.fall = (power, seed) => {
    const R = new CM.Random(seed), b = { x: 30 + power * (PC.W - 60) + (R.next() - 0.5) * 18, y: 40, vx: (R.next() - 0.5) * 60, vy: 40 }, path = [[b.x, b.y]], dt = 1 / 120;
    for (let s = 0; s < 1600; s++) {
      b.vy += PC.g * dt; b.x += b.vx * dt; b.y += b.vy * dt;
      if (b.x < 10) { b.x = 10; b.vx = Math.abs(b.vx) * 0.6; } if (b.x > PC.W - 10) { b.x = PC.W - 10; b.vx = -Math.abs(b.vx) * 0.6; }
      for (const [px, py] of PC.PINS) { const dx = b.x - px, dy = b.y - py, d = Math.hypot(dx, dy), m = PC.pinR + PC.ballR; if (d < m && d > 0) { const nx = dx / d, ny = dy / d, vn = b.vx * nx + b.vy * ny; b.x = px + nx * m; b.y = py + ny * m; if (vn < 0) { b.vx -= 1.55 * vn * nx; b.vy -= 1.55 * vn * ny; b.vx += (R.next() - 0.5) * 14; } } }
      if (s % 2 === 0) path.push([Math.round(b.x * 10) / 10, Math.round(b.y * 10) / 10]);
      for (const P of PC.POCKETS) if (Math.abs(b.x - P.x) < P.w / 2 && Math.abs(b.y - P.y) < 6 && b.vy > 0) { path.push([P.x, P.y + 6]); return { path, pocket: P.id, pays: P.pays }; }
      if (b.y > PC.H - 8) { path.push([b.x, PC.H]); return { path, pocket: "out", pays: 0 }; }
    }
    return { path, pocket: "out", pays: 0 };
  };
  Object.assign(CM.Game.prototype, {
    // ---- the Pin Garden ----
    pcState() { const F = this.cgStore(); F.pc = F.pc || { balls: 0, shots: 0, fevers: 0 }; return F.pc; },
    pcBuy(n) { n = Math.floor(n || 0); const why = this.cgStake("pachinko", n); if (why) return why; this.pcState().balls += n; this.saveCasino && this.saveCasino(); return ""; },
    pcShoot(power) {
      const S = this.pcState(); if (S.balls < 1) return { error: "Buy a tray of balls first." }; S.balls -= 1; S.shots += 1; const out = PC.fall(CM.ARC.clamp(power, 0, 1), CM.hashSeed(`${this.seed}:pachinko:${S.shots}`));
      if (out.pocket === "tulip") { const R = new CM.Random(CM.hashSeed(`${this.seed}:pachinko:drums:${S.shots}`)), fev = R.chance(1 / 36), a = R.int(1, 9); out.drums = fev ? [a, a, a] : (() => { let d; do { d = [R.int(1, 9), R.int(1, 9), R.int(1, 9)]; } while (d[0] === d[1] && d[1] === d[2]); return d; })(); if (fev) { out.fever = true; out.pays += PC.fever; S.fevers += 1; out.card = this.cgCard(false, "Fever at the Pin Garden!", R); } }
      S.balls += out.pays; this.saveCasino && this.saveCasino(); return out;
    },
    pcExchange() { const S = this.pcState(), n = S.balls; if (!n) return { gold: 0, tickets: 0 }; const gold = Math.floor(n * PC.rate), tickets = Math.floor(n / PC.ticketPer); S.balls = 0; this.cgPay("pachinko", gold); if (this.tkAdd) this.tkAdd(tickets, "pachinko"); this.saveCasino && this.saveCasino(); this.emit("change"); return { gold, tickets, balls: n }; },
    // ---- the Joker's Wheel ----
    bwSpin(bets) {
      const total = Object.values(bets).reduce((a, b) => a + (b || 0), 0); if (!total) return { error: "Put a chip on a number first." }; if (total > CM.CG.max) return { error: `The wheel takes no more than ${CM.CG.max} gold a spin.` };
      const why = this.cgStake("bigwheel", total); if (why) return { error: why }; const R = this.cgRnd("bigwheel"), i = R.int(0, 53), hit = L.BW.SLOTS[i], stake = bets[hit] || 0, back = stake ? stake * (L.BW.PAYS[hit] + 1) : 0;
      if (back) this.cgPay("bigwheel", back); const card = hit === "joker" && stake ? this.cgCard(true, "The Joker's Wheel stops on the Joker!", R) : null; this.saveCasino && this.saveCasino(); this.emit("change"); return { i, hit, back, staked: total, card };
    },
    // ---- Fortune Slips ----
    scBuy(kind) {
      const K = L.SC.KINDS[kind]; if (!K) return { error: "No such slip." }; const why = this.cgStake("scratch", K.price); if (why) return { error: why }; const R = this.cgRnd("scratch");
      let prize = 0, card = false, roll = R.next(); if (R.next() < K.card) card = true; else for (const [p, v] of K.PRIZES) { if (roll < p) { prize = v; break; } roll -= p; }
      // the nine squares: the winning three, and the rest never three alike
      const vals = K.PRIZES.map(([, v]) => v), syms = []; const win = card ? "card" : prize || null; if (win) for (let k = 0; k < 3; k++) syms.push(win);
      const pool = vals.concat(["card"]).filter((v) => v !== win), cnt = {}; while (syms.length < 9) { const v = R.pick(pool); if ((cnt[v] || 0) >= 2) continue; cnt[v] = (cnt[v] || 0) + 1; syms.push(v); }
      for (let i = syms.length - 1; i > 0; i--) { const j = R.int(0, i); [syms[i], syms[j]] = [syms[j], syms[i]]; }
      const S = this.cgStore(); S.slip = { kind, syms, prize, card, paid: false }; this.saveCasino && this.saveCasino(); return S.slip;
    },
    scClaim() { const S = this.cgStore(), P = S.slip; if (!P || P.paid) return null; P.paid = true; let card = null; if (P.prize) this.cgPay("scratch", P.prize); if (P.card) card = this.cgTierCard(P.kind === "gold" ? "rare" : P.kind === "silver" ? "better" : "common", "Three cards on a Fortune Slip!", this.cgRnd("scratchcard")); this.saveCasino && this.saveCasino(); this.emit("change"); return { prize: P.prize, card }; },
    // ---- the Prize Wheel: once a real day ----
    pwToday() { return CM.DAILY ? (this.dlDay || CM.DAILY.key()) : new Date().toDateString(); },
    pwReady() { return this.cgStore().pwLast !== this.pwToday(); },
    pwSpin() {
      if (!this.pwReady()) return { error: "The prize wheel turns once a day. Come back tomorrow." }; const S = this.cgStore(); S.pwLast = this.pwToday(); S.pwN = (S.pwN || 0) + 1;
      const R = new CM.Random(CM.hashSeed(`${this.seed}:prizewheel:${S.pwLast}`)), tot = L.PW.SLICES.reduce((t, s) => t + s[2], 0); let roll = R.next() * tot, i = 0; for (; i < L.PW.SLICES.length - 1; i++) { roll -= L.PW.SLICES[i][2]; if (roll <= 0) break; }
      const [id, label] = L.PW.SLICES[i], out = { i, id, label }; if (this.cgStamp) this.cgStamp("prizewheel");
      if (id.startsWith("t")) { out.tickets = Number(id.replace(/\D/g, "")); this.tkAdd && this.tkAdd(out.tickets, "prizewheel"); }
      else if (id.startsWith("g")) { out.gold = Number(id.slice(1)); this.gold += out.gold; }
      else if (id === "potion") { const it = R.chance(0.5) ? { name: "Healing Potion", kind: "heal", power: 30, value: 20 } : { name: "Mana Potion", kind: "mana", power: 18, value: 25 }; this.gain([it], "casino"); out.item = it; }
      else if (id === "card") out.card = this.cgTierCard("common", "The prize wheel stops on a card!", R);
      this.saveCasino && this.saveCasino(); this.emit("change"); return out;
    },
  });
}
