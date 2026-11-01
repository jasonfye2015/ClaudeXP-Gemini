"use strict";
// The Joker's Almanac and the visit calendar (v17.5).
// - The Almanac: a track of thirty steps for each real month, named for the month's festival, filled by the JXP the
//   party earns anywhere on the floor (fifty a step). Every step pays something - tickets, gold, a potion, a card at
//   every fifth - and the tenth, twentieth and thirtieth more; the thirtieth leaves the month's keepsake in the
//   Almanac's cabinet. A new month starts a new track; steps reached and not collected are kept for a month after.
// - The visit calendar: a card of twenty-eight stamps, one for each real day the party comes in (missing a day costs
//   nothing - the next visit takes the next stamp). Each stamp pays a little, the seventh, fourteenth, twenty-first and
//   twenty-eighth more; a full card starts a new one.
// The window is 76zzy-almanac.js.
{ const AL = CM.ALMANAC = { steps: 30, per: 50, KEEPSAKES: ["a Midwinter star", "the Sexton's candle", "a Sowing seed-pouch", "the Dwarves' letter", "a Greening garland", "a Midsummer lantern", "a Forge Fire ember", "a Reaping sheaf", "a Harvest Fair rosette", "a Feast of the Dead lamp", "a Night of Bells bell", "a Wassail cup"] };
  const VC = CM.VISITCAL = { stamps: 28 };
  AL.month = (now) => { const d = new Date(now || Date.now()); return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`; };
  AL.name = (month) => { const m = Number(month.split("-")[1]) - 1, f = CM.FESTIVALS ? Object.values(CM.FESTIVALS).find((x) => x.month === m) : null; return f ? `The Almanac of ${f.name.replace(/^the /, "the ")}` : "The Joker's Almanac"; };
  // what a step pays
  AL.reward = (k) => { if (k === 30) return { gold: 800, tickets: 250, card: "rare", keepsake: true }; if (k === 20) return { gold: 300, tickets: 150, card: "better" }; if (k === 10) return { gold: 300, card: "better" };
    if (k % 5 === 0) return { tickets: 50, card: "common" }; if (k % 10 === 3) return { potion: true, tickets: 10 }; return k % 2 ? { tickets: 15 + k } : { gold: 20 + 3 * k }; };
  VC.reward = (n) => (n === 28 ? { gold: 500, card: "rare" } : n === 21 ? { gold: 300, card: "better" } : n === 14 ? { tickets: 200 } : n === 7 ? { gold: 100, card: "common" } : { tickets: 10 + (n % 7) * 2 });
  const day = (now) => { const d = new Date(now || Date.now()); return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`; };
  const P = CM.Game.prototype, jk0 = P.jkGain;
  Object.assign(P, {
    alStore() { const F = this.cgStore(); F.almanac = F.almanac || { months: {}, keepsakes: [] }; return F.almanac; },
    alMonth(month) { const S = this.alStore(); month = month || AL.month(); S.months[month] = S.months[month] || { pts: 0, got: [] }; return S.months[month]; },
    alInfo(now) { const month = AL.month(now), M = this.alMonth(month), reached = Math.min(AL.steps, Math.floor(M.pts / AL.per)); return { month, name: AL.name(month), pts: M.pts, reached, into: M.pts - reached * AL.per, waiting: Array.from({ length: reached }, (_, i) => i + 1).filter((k) => !M.got.includes(k)) }; },
    // what the steps reached pay, all at once (this month's, and last month's left over)
    alCollect(now) { const out = { gold: 0, tickets: 0, cards: [], items: [], keepsake: null, steps: 0 }, S = this.alStore(), months = [AL.month(now)];
      { const d = new Date(now || Date.now()); d.setDate(1); d.setMonth(d.getMonth() - 1); months.push(AL.month(d.getTime())); }
      for (const month of months) { const M = S.months[month]; if (!M) continue; const reached = Math.min(AL.steps, Math.floor(M.pts / AL.per));
        for (let k = 1; k <= reached; k++) { if (M.got.includes(k)) continue; M.got.push(k); out.steps += 1; const R = AL.reward(k);
          if (R.gold) { out.gold += R.gold; this.gold += R.gold; } if (R.tickets) out.tickets += R.tickets;
          if (R.potion) { const it = { name: "Healing Potion", kind: "heal", power: 30, value: 20 }; this.gain && this.gain([it], "casino"); out.items.push(it); }
          if (R.card && this.cgTierCard) { const c = this.cgTierCard(R.card, `${AL.name(month)}, step ${k}.`, new CM.Random(CM.hashSeed(`${this.seed}:almanac:${month}:${k}`))); if (c) out.cards.push(c); }
          if (R.keepsake) { const ks = AL.KEEPSAKES[Number(month.split("-")[1]) - 1]; if (!S.keepsakes.some((x) => x.month === month)) { S.keepsakes.push({ month, name: ks }); out.keepsake = ks; } } } }
      if (out.tickets && this.tkAdd) this.tkAdd(out.tickets, "almanac"); if (out.keepsake && this.cgCelebrate) this.cgCelebrate(2, `The month's keepsake: ${out.keepsake}!`); this.saveCasino && this.saveCasino(); this.emit && this.emit("change"); return out; },
    jkGain(n, why) { const ups = jk0.call(this, n, why); if (!this.cgPractice && n > 0 && why !== "almanac") { const I = this.wkInfo ? this.wkInfo() : null, k = I && why === I.id ? 2 : 1; this.alMonth().pts += Math.floor(n) * k; } return ups; },
    // ---- the visit calendar ----
    vcStore() { const F = this.cgStore(); F.visitcal = F.visitcal || { days: [], card: 1, n: 0 }; return F.visitcal; },
    // a visit today: the next stamp, if today hasn't one
    vcStamp(now) { const S = this.vcStore(), d = day(now); if (S.days.includes(d)) return null; S.days.push(d); if (S.days.length > 60) S.days.shift(); S.n += 1; const n = S.n, R = VC.reward(n), out = { n, card: S.card, gold: R.gold || 0, tickets: R.tickets || 0, cards: [] };
      if (R.gold) this.gold += R.gold; if (R.tickets && this.tkAdd) this.tkAdd(R.tickets, "visits"); if (R.card && this.cgTierCard) { const c = this.cgTierCard(R.card, `The visit calendar: stamp ${n}.`, new CM.Random(CM.hashSeed(`${this.seed}:visit:${S.card}:${n}`))); if (c) out.cards.push(c); }
      if (n >= VC.stamps) { S.card += 1; S.n = 0; out.full = true; if (this.cgCelebrate) this.cgCelebrate(2, "A full visit calendar!"); } this.saveCasino && this.saveCasino(); return out; },
  });
}
