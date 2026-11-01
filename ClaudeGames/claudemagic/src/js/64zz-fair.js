"use strict";
// The fairground games (v15.7): the Tavern Board and Rune-Roll, games of aim on the Gilded Joker's floor. Both take a
// stake and pay back by the score - gold on a table that rises with it, and prize tickets for every point (a ticket a
// twenty at darts, a ticket a ten at skee) - and give a Claudescryption card the first time ever each high mark is
// passed. The scores go on the high-score boards.
// - The Tavern Board: darts - eight rounds of three, at a board of twenty numbered wedges with the doubles ring, the
//   trebles ring, the outer bull (25) and the bull (50). The hand wavers as it aims, and each dart flies a little wide.
// - Rune-Roll: skee-ball - nine wooden balls rolled up a lane to hop into the rings of the target: 10 the outer, then
//   20, 30, 40, 50 at the heart and 100 in the two little corner cups. Aim with where the ball is let go and power with
//   how long it is held.
// The windows are 76zq-darts.js and 76zr-runeroll.js.
CM.FAIR = {
  darts: { name: "The Tavern Board", rounds: 8, per: 3, scatter: 0.075, ticketPer: 20, MARKS: [500, 700, 900], PAY: [[400, 0.2], [500, 0.35], [600, 0.55], [700, 0.75], [800, 0.95], [900, 1.1]], waver: 0.16 },
  skee: { name: "Rune-Roll", balls: 9, ticketPer: 10, MARKS: [380, 500, 640], PAY: [[300, 0.25], [380, 0.45], [440, 0.7], [500, 0.95], [560, 1.25], [640, 1.6], [720, 2.2]] },
  ORDER: [20, 1, 18, 4, 13, 6, 10, 15, 2, 17, 3, 19, 7, 16, 8, 11, 14, 9, 12, 5],
  // board radii as a share of the doubles' outer edge
  RING: { bull: 0.037, outer: 0.094, tIn: 0.582, tOut: 0.629, dIn: 0.953 },
};
{ const FA = CM.FAIR;
  FA.dartScore = (x, y) => { const r = Math.hypot(x, y), R = FA.RING; if (r > 1) return { pts: 0, label: "Miss" }; if (r < R.bull) return { pts: 50, label: "Bull" }; if (r < R.outer) return { pts: 25, label: "25" };
    const a = (Math.atan2(x, -y) + Math.PI * 2 + Math.PI / 20) % (Math.PI * 2), n = FA.ORDER[Math.floor(a / (Math.PI / 10))]; if (r >= R.dIn) return { pts: 2 * n, label: `D${n}` }; if (r >= R.tIn && r < R.tOut) return { pts: 3 * n, label: `T${n}` }; return { pts: n, label: String(n) }; };
  // where a skee ball lands on the target (x across from -1 to 1, y up from 0 at the lip), and what it scores
  FA.skeeAt = (aim, power, R) => { const g = () => (R.next() + R.next() + R.next() - 1.5) * 0.7; return [aim * 0.85 + g() * (0.07 + 0.1 * power), 0.08 + power * 1.12 + g() * (0.05 + 0.12 * power)]; };
  FA.skeeScore = (x, y) => { if (y < 0.12) return { pts: 0, label: "Gutter" }; for (const cx of [-0.58, 0.58]) if (Math.hypot(x - cx, y - 1.02) < 0.065) return { pts: 100, label: "100" };
    const d = Math.hypot(x, y - 0.6); if (d < 0.1) return { pts: 50, label: "50" }; if (d < 0.2) return { pts: 40, label: "40" }; if (d < 0.31) return { pts: 30, label: "30" }; if (d < 0.43) return { pts: 20, label: "20" }; return { pts: 10, label: "10" }; };
  if (CM.CLUB) for (const k of ["darts", "skee"]) if (!CM.CLUB.BOARDS.includes(k)) CM.CLUB.BOARDS.push(k);
  if (CM.DAILY) { CM.DAILY.MARKS.darts = [5, 6, 8]; CM.DAILY.MARKS.skee = [3, 4, 5]; }
  FA.pay = (kind, score) => { let m = 0; for (const [s, k] of FA[kind].PAY) if (score >= s) m = k; return m; };
  Object.assign(CM.Game.prototype, {
    faState(kind) { return this.cgStore()[`fa_${kind}`] || null; },
    faStart(kind, bet) { const S0 = this.faState(kind); if (S0 && S0.stage === "play") return { error: "A game is on." }; const why = this.cgStake(kind, bet); if (why) return { error: why };
      const F = this.cgStore(); F.n += 1; F[`fa_${kind}`] = { stage: "play", bet: Math.floor(bet), seed: `${this.seed}:${kind}:${F.n}`, throws: [], score: 0 }; this.saveCasino && this.saveCasino(); return F[`fa_${kind}`]; },
    // a dart at where the hand was when it let go; a ball let go at an aim with a power
    faThrow(kind, a, b) {
      const S = this.faState(kind), K = FA[kind]; if (!S || S.stage !== "play") return { error: "No game on." }; const R = new CM.Random(CM.hashSeed(`${S.seed}:${S.throws.length}`));
      let x, y, sc; if (kind === "darts") { const g = () => (R.next() + R.next() + R.next() - 1.5) * 0.8; x = a + g() * K.scatter; y = b + g() * K.scatter; sc = FA.dartScore(x, y); } else { [x, y] = FA.skeeAt(CM.ARC.clamp(a, -1, 1), CM.ARC.clamp(b, 0, 1), R); sc = FA.skeeScore(x, y); }
      S.throws.push({ x, y, pts: sc.pts, label: sc.label }); S.score += sc.pts; const total = kind === "darts" ? K.rounds * K.per : K.balls, out = { x, y, ...sc, score: S.score, n: S.throws.length };
      if (S.throws.length >= total) Object.assign(out, this.faEnd(kind)); this.saveCasino && this.saveCasino(); return out;
    },
    faEnd(kind) {
      const S = this.faState(kind), K = FA[kind], F = this.cgStore(), gold = Math.round(S.bet * FA.pay(kind, S.score)), tickets = Math.floor(S.score / K.ticketPer); S.stage = "done";
      if (gold) this.cgPay(kind, gold); if (this.tkAdd) this.tkAdd(tickets, kind); const C = F[`fa_${kind}_cards`] = F[`fa_${kind}_cards`] || {}, cards = [];
      K.MARKS.forEach((m, i) => { if (S.score >= m && !C[m]) { const c = this.cgTierCard(["common", "better", "rare"][i], `${K.name}: ${m} points!`, new CM.Random(CM.hashSeed(`${this.seed}:${kind}:card:${m}`))); C[m] = c || true; if (c) cards.push(c); } });
      F[`fa_${kind}_best`] = Math.max(F[`fa_${kind}_best`] || 0, S.score); this.cgRecord && this.cgRecord(kind, S.score, Math.floor(S.score / 100)); S.last = { score: S.score, gold, tickets, cards }; this.emit("change");
      return { over: true, gold, tickets, cards };
    },
  });
}
