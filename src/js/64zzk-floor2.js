"use strict";
// The floor's big nights (v16.3): four things across the Gilded Joker.
// - The progressive jackpot: a pot over the whole floor that starts at 1,000 gold, takes two parts in a hundred of
//   every stake laid anywhere (and a little each real hour from the town's own players), and must go before it reaches
//   4,000 - it is set to burst at a point the house picks in secret when the pot is made. Once past that point the
//   next stake at one of the jackpot tables (the reels, video poker, the wheels, the Pin Garden, the Drop Board, the
//   slips, roulette) wins it all, with tickets and a rare card.
// - Happy hour: each real day one ticket-paying game has an hour (somewhere between noon and eleven at night) when
//   every ticket it pays is doubled. The hour is posted on the gallery all day.
// - High-roller challenges: each real day one of the residents comes to the floor with a wager - a heads-up game of
//   hold'em (first to take all the other's chips), or a score to beat at the Tavern Board, Rune-Roll or Hoop-la. The
//   party can take the wager or let it go; a win pays double the wager, tickets, and a card the first time each
//   resident is beaten. A challenge stands for the day.
// - The ticket exchange: tickets for gold and gold for tickets, at rates that drift from day to day; buying always
//   costs more than selling pays, so the two can't be turned round for profit. A little chart shows the last fortnight.
// The window is 76zzn-floor2.js.
{ const JP = CM.JP = { pot0: 1000, must: 4000, feed: 0.02, hourly: 40, tickets: 150, TABLES: ["slots", "poker", "bigwheel", "roulette", "pachinko", "plinko", "scratch"] };
  const HH = CM.HH = { from: 12, to: 22, GAMES: ["darts", "skee", "rings", "range", "pachinko", "plinko", "pond", "lottery", "joust", "courier", "sprint", "bastion", "vault", "bingo", "holdem", "slots", "craps"] };
  const HR = CM.HR = { WAGERS: [200, 300, 500, 750, 1000], KINDS: ["holdem", "darts", "skee", "rings"], TARGET: { darts: [420, 620], skee: [330, 520], rings: [18, 36] }, tickets: 40 };
  const TX = CM.TX = { buyMax: 1000, sellMax: 5000 };
  const day = () => (CM.FLOOR ? CM.FLOOR.day() : (CM.DAILY ? CM.DAILY.key() : new Date().toISOString().slice(0, 10)));
  const dayNo = (key) => { const [y, m, d] = key.split("-").map(Number); return Math.round(Date.UTC(y, m - 1, d) / 86400000); };
  const keyOf = (n) => new Date(n * 86400000).toISOString().slice(0, 10);
  // the exchange's rates for a day: gold paid for a ticket sold, and gold asked for a ticket bought
  TX.rates = (seed, key) => { const n = dayNo(key), R = new CM.Random(CM.hashSeed(`${seed}:tx:${key}`)), ph = (CM.hashSeed(`${seed}:txph`) % 1000) / 160;
    const sell = 0.11 + 0.02 * Math.sin(n / 3.1 + ph) + 0.012 * Math.sin(n / 1.3 + ph * 2) + (R.next() - 0.5) * 0.008, buy = 0.4 + 0.05 * Math.sin(n / 4.3 + ph) + 0.02 * Math.sin(n / 1.7) + (R.next() - 0.5) * 0.02;
    return { sell: Math.round(sell * 1000) / 1000, buy: Math.round(Math.max(sell * 2.6, buy) * 1000) / 1000 }; };
  TX.history = (seed, key, days = 14) => Array.from({ length: days }, (_, i) => { const k = keyOf(dayNo(key) - (days - 1 - i)); return Object.assign({ key: k }, TX.rates(seed, k)); });
  HH.today = (seed, key) => { const R = new CM.Random(CM.hashSeed(`${seed}:happy:${key}`)); return { table: R.pick(HH.GAMES), hour: R.int(HH.from, HH.to) }; };
  const st0 = CM.Game.prototype.cgStake, tk0 = CM.Game.prototype.tkAdd, fend0 = CM.Game.prototype.faEnd, hleave0 = CM.Game.prototype.heLeave;
  Object.assign(CM.Game.prototype, {
    // ---- the progressive jackpot ----
    jpStore(now) { const F = this.cgStore(); if (!F.jp) { F.jp = { pot: JP.pot0, trig: 0, n: 0, wins: [], at: now || Date.now() }; this.jpArm(); } return F.jp; },
    jpArm() { const J = this.cgStore().jp; J.n += 1; const R = new CM.Random(CM.hashSeed(`${this.seed}:jp:${J.n}`)); J.trig = R.int(JP.pot0 + 200, JP.must); },
    jpPot(now) { now = now || Date.now(); const J = this.jpStore(now), hrs = Math.floor((now - J.at) / 3600000); if (hrs > 0) { J.pot = Math.min(JP.must, J.pot + Math.min(48, hrs) * JP.hourly); J.at += hrs * 3600000; } return J.pot; },
    jpReady() { const J = this.jpStore(); return J.pot >= J.trig; },
    jpHit(game) { const J = this.jpStore(), won = Math.floor(J.pot), out = { gold: won, game, tickets: JP.tickets }; J.wins.unshift({ gold: won, game, day: day() }); J.wins.length = Math.min(J.wins.length, 5); J.pot = JP.pot0; this.jpArm();
      const F = this.cgStore(); this.gold += won; F.paid.jackpot = (F.paid.jackpot || 0) + won;   // (straight to the purse: the pot is no table, so no stamp)
      if (this.tkAdd) tk0.call(this, JP.tickets, "jackpot"); out.card = this.cgTierCard ? this.cgTierCard("rare", "The Gilded Joker's progressive jackpot!", new CM.Random(CM.hashSeed(`${this.seed}:jpcard:${J.n}`))) : null;
      this.fwQ = (this.fwQ || []).filter((e) => e.tier < 2); this.cgCelebrate && this.cgCelebrate(3, `The progressive jackpot - ${won.toLocaleString("en")} gold!`); this.jpJust = out; return out; },
    // ---- happy hour ----
    hhToday() { return HH.today(this.seed, day()); },
    hhOn(now) { const H = this.hhToday(), h = new Date(now || Date.now()).getHours(); return h === H.hour ? H.table : null; },
    // ---- the stakes and tickets, seen ----
    cgStake(game, bet) { const why = st0.call(this, game, bet); if (!why && game !== "tournament" && game !== "highroller") { this.jpPot(); const J = this.jpStore(); J.pot = Math.min(JP.must, J.pot + Math.floor(bet) * JP.feed); if (this.jpReady() && JP.TABLES.includes(game)) this.jpHit(game); } return why; },
    tkAdd(n, why) { const hh = why && this.hhOn() === why; const k = tk0.call(this, hh ? n * 2 : n, why); if (hh && k > 0) { const F = this.cgStore(); F.hhBonus = (F.hhBonus || 0) + Math.floor(k / 2); } return k; },
    // ---- high-roller challenges ----
    hrStore() { const F = this.cgStore(); F.hr = F.hr || { days: {}, beaten: {}, won: 0, lost: 0 }; return F.hr; },
    hrToday() { const key = day(), S = this.hrStore(); if (!S.days[key]) { const R = new CM.Random(CM.hashSeed(`${this.seed}:hr:${key}`)), kind = R.pick(HR.KINDS), who = R.pick(Object.keys(CM.HE.RES)), wager = R.pick(HR.WAGERS), T = HR.TARGET[kind];
        S.days = { [key]: { who, kind, wager, target: T ? R.int(T[0], T[1]) : 0, state: "offered" } }; } return S.days[key]; },
    hrName(C) { return CM.HE.RES[C.who].name; },
    hrAccept() { const C = this.hrToday(); if (C.state !== "offered") return { error: "That challenge has been settled." }; if (this.gold < C.wager) return { error: `The wager is ${C.wager} gold; the party has ${this.gold}.` };
      if (C.kind === "holdem") { const H = this.heStore(); if (H.live) return { error: "Finish your seat at the Residents' Game first." }; const old = CM.CG.max; CM.CG.max = Math.max(old, C.wager); let why; try { why = st0.call(this, "holdem", C.wager); } finally { CM.CG.max = old; } if (why) return { error: why };
        const F = this.cgStore(); F.n += 1; H.live = CM.HE.newTable(`${this.seed}:hrhe:${F.n}`, C.wager, [C.who]); H.live.duel = true; CM.HE.deal(H.live); }
      else { const old = CM.CG.max; CM.CG.max = Math.max(old, C.wager); let why; try { why = st0.call(this, "highroller", C.wager); } finally { CM.CG.max = old; } if (why) return { error: why }; }
      C.state = "on"; this.saveCasino && this.saveCasino(); return { ok: true, kind: C.kind }; },
    hrDecline() { const C = this.hrToday(); if (C.state !== "offered") return { error: "Too late for that." }; C.state = "declined"; this.saveCasino && this.saveCasino(); return { ok: true }; },
    hrSettle(win, detail) { const C = this.hrToday(), S = this.hrStore(); if (C.state !== "on") return null; C.state = win ? "won" : "lost"; const out = { win, who: this.hrName(C), wager: C.wager, detail };
      if (win) { S.won += 1; if (C.kind !== "holdem") { out.gold = C.wager * 2; this.cgPay("highroller", out.gold); } out.tickets = HR.tickets + Math.floor(C.wager / 20); if (this.tkAdd) tk0.call(this, out.tickets, "highroller");
        if (!S.beaten[C.who]) { S.beaten[C.who] = true; out.card = this.cgTierCard("better", `You beat ${out.who} for ${C.wager} gold!`, new CM.Random(CM.hashSeed(`${this.seed}:hrcard:${C.who}`))); }
        this.cgCelebrate && this.cgCelebrate(2, `You beat ${out.who}!`); }
      else S.lost += 1; C.result = out; this.saveCasino && this.saveCasino(); this.emit("change"); return out; },
    faEnd(kind) { const out = fend0.call(this, kind), C = this.hrStore().days[day()]; if (C && C.state === "on" && C.kind === kind) { const sc = this.faState(kind).score; out.challenge = this.hrSettle(sc > C.target, `${sc} against ${C.target}`); } return out; },
    heLeave() { const T = this.heTable(), duel = T && T.duel, out = hleave0.call(this); if (duel && !out.error) { const C = this.hrStore().days[day()]; if (C && C.state === "on" && C.kind === "holdem") out.challenge = this.hrSettle(out.chips >= T.buyin * 2, `${out.chips} chips of ${T.buyin * 2}`); } return out; },
    // ---- the ticket exchange ----
    txStore() { const F = this.cgStore(); F.tx = F.tx || { day: "", bought: 0, sold: 0, gold: 0, tk: 0 }; if (F.tx.day !== day()) Object.assign(F.tx, { day: day(), bought: 0, sold: 0 }); return F.tx; },
    txRates() { return TX.rates(this.seed, day()); },
    txSell(n) { n = Math.floor(n || 0); const X = this.txStore(), T = this.tkStore(), r = this.txRates(); if (n < 1) return { error: "How many tickets?" }; if (n > T.n) return { error: `You have ${T.n} tickets.` }; if (X.sold + n > TX.sellMax) return { error: `The exchange takes ${TX.sellMax - X.sold} more tickets today.` };
      const gold = Math.floor(n * r.sell); if (gold < 1) return { error: "That's not worth a gold piece." }; T.n -= n; X.sold += n; X.gold += gold; this.gold += gold; this.saveCasino && this.saveCasino(); this.emit("change"); return { tickets: n, gold }; },
    txBuy(n) { n = Math.floor(n || 0); const X = this.txStore(), T = this.tkStore(), r = this.txRates(); if (n < 1) return { error: "How many tickets?" }; if (X.bought + n > TX.buyMax) return { error: `The exchange sells ${TX.buyMax - X.bought} more tickets today.` };
      const gold = Math.ceil(n * r.buy); if (gold > this.gold) return { error: `That's ${gold} gold; the party has ${this.gold}.` }; this.gold -= gold; T.n += n; X.bought += n; X.tk += n; this.saveCasino && this.saveCasino(); this.emit("change"); return { tickets: n, gold }; },
  });
}
