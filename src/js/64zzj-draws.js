"use strict";
// The town's draws and the pond (v16.2):
// - Big wins: the floor notices a large prize - a payout ten or twenty-five times the stake, a great deal of gold at
//   once, a rare card, a fistful of tickets - and queues a celebration for the window (fireworks, 76zzj-fireworks.js).
//   Cash-outs (chips back from the residents' table, a pachinko tray changed in) are not wins and are not noticed.
// - The Town Lottery: slips at 2 gold, six numbers from thirty, drawn at eight each evening (a slip bought after eight
//   is in the next night's draw). Three matched pay 8 gold, four 60, five 1,200 and a rare card, all six the town's
//   jackpot - which starts at 5,000, grows every night nobody wins it (and with a share of the party's slips), and
//   is sometimes won by somebody in the village instead. The night's balls are the save's own, the same however often
//   the draw is watched.
// - The Drop Board: plinko - one big chip dropped down twelve rows of pegs into thirteen bins; low, middle and high
//   risk boards pay from 0.2 to 120 times the stake, each about 96% back. Ten times or better pays tickets too, and
//   the high board's corner pays a card the first time.
// - The Fishing Pond: buy bait (worms, or spinners for the deep water), cast out, strike when the float goes under,
//   and play the fish in; the fishmonger buys the catch by weight and the creel book counts every kind. Some fish
//   only bite after dark (real time), the pike and catfish fight hard, and the golden carp is rare. The heaviest of
//   each catch goes on the board.
// The windows are 76zzj-fireworks.js, 76zzk-lottery.js, 76zzl-plinko.js and 76zzm-pond.js.
{ const FW = CM.FW = { big: 10, huge: 25, gold: 400, hugeGold: 1500, tickets: 100, CASH: ["holdem", "pachinko", "tournament"] };
  const LOT = CM.LOT = { price: 2, pick: 6, of: 30, hour: 20, max: 25, pot0: 5000, PAYS: { 3: [8, 3], 4: [60, 15], 5: [1200, 80] }, jackTickets: 200, share: 0.4, villager: 1 / 60 };
  const PK = CM.PK = { rows: 12, RISK: { low: [8, 3, 1.5, 1.2, 1.1, 1, 0.5], med: [25, 9, 3, 2, 1.1, 0.6, 0.4], high: [120, 24, 8, 2, 0.7, 0.2, 0.2] } };
  for (const k of Object.keys(PK.RISK)) { const v = PK.RISK[k]; PK.RISK[k] = v.concat(v.slice(0, -1).reverse()); }
  // [id, name, tier, kg from, kg to, gold a kg, tickets, how far out (0 near .. 1 far), night only, fight 0..1]
  const POND = CM.POND = { BAIT: { worms: { name: "A pot of worms", price: 12, casts: 5 }, spinners: { name: "A card of spinners", price: 18, casts: 5 } },
    FISH: [
      ["boot", "An old boot", 0, 0.4, 0.9, 0, 1, 0.3, false, 0], ["weed", "A clump of weed", 0, 0.1, 0.3, 0, 0, 0.5, false, 0],
      ["roach", "Roach", 1, 0.1, 0.4, 8, 1, 0.2, false, 0.15], ["perch", "Perch", 1, 0.2, 0.8, 5.5, 1, 0.4, false, 0.25],
      ["bream", "Bream", 2, 1, 3, 1.6, 2, 0.5, false, 0.35], ["trout", "Brown trout", 2, 0.5, 2, 3, 2, 0.8, false, 0.5],
      ["pike", "Pike", 3, 2, 8, 1.6, 4, 0.85, false, 0.8], ["eel", "Eel", 3, 0.5, 2, 4.5, 3, 0.4, true, 0.6],
      ["catfish", "Catfish", 4, 4, 14, 1.3, 6, 0.7, true, 0.95], ["golden", "The golden carp", 5, 2, 6, 10, 30, 0.6, false, 0.7],
    ] };
  POND.byId = Object.fromEntries(POND.FISH.map((f) => [f[0], f]));
  const day = (d) => (CM.DAILY ? CM.DAILY.key(d) : d.toISOString().slice(0, 10));
  // the draw a slip bought now is in: tonight's, or tomorrow night's after the hour
  LOT.drawKey = (now) => { const d = new Date(now); if (d.getHours() >= LOT.hour) d.setDate(d.getDate() + 1); return day(d); };
  LOT.drawTime = (key) => { const [y, m, dd] = key.split("-").map(Number); return new Date(y, m - 1, dd, LOT.hour, 0, 0).getTime(); };
  LOT.nextKey = (key) => { const [y, m, dd] = key.split("-").map(Number); return day(new Date(y, m - 1, dd + 1, 12)); };
  LOT.quick = (R) => R.shuffle(Array.from({ length: LOT.of }, (_, i) => i + 1)).slice(0, LOT.pick).sort((a, b) => a - b);
  // a big chip's path: right (1) or left (0) at each row
  PK.path = (R) => Array.from({ length: PK.rows }, () => (R.next() < 0.5 ? 0 : 1));
  // what bites, for a cast this far out with this bait at this hour
  POND.pick = (dist, bait, hour, R) => { const night = hour >= 20 || hour < 6, w = POND.FISH.map((f) => { if (f[8] && !night) return 0; let k = Math.max(0.05, 1 - Math.abs(f[7] - dist) * 1.1);
      k *= [1.6, 4, 3, 1.4, 0.9, 0.05][f[2]]; if (bait === "spinners") k *= [0.3, 0.3, 1.2, 3.5, 3.5, 3][f[2]]; if (f[0] === "boot" || f[0] === "weed") k *= 0.5; return k; });
    let r = R.next() * w.reduce((a, b) => a + b, 0), i = 0; for (; i < w.length - 1; i++) { r -= w[i]; if (r <= 0) break; } const f = POND.FISH[i], kg = Math.round((f[3] + (f[4] - f[3]) * Math.pow(R.next(), 1.8)) * 100) / 100;
    return { id: f[0], name: f[1], tier: f[2], kg, fight: f[9], bite: 1.4 + R.next() * 4.5, window: 1.1 - f[9] * 0.45 }; };
  if (CM.CLUB && !CM.CLUB.BOARDS.includes("pond")) CM.CLUB.BOARDS.push("pond"); if (CM.DAILY) CM.DAILY.MARKS.pond = [2, 3, 4];
  const st0 = CM.Game.prototype.cgStake, pay0 = CM.Game.prototype.cgPay, tk0 = CM.Game.prototype.tkAdd, card0 = CM.Game.prototype.cgCard, tier0 = CM.Game.prototype.cgTierCard;
  Object.assign(CM.Game.prototype, {
    // ---- big wins, noticed ----
    cgCelebrate(tier, text) { (this.fwQ = this.fwQ || []).push({ tier, text }); },
    cgStake(game, bet) { const why = st0.call(this, game, bet); if (!why) (this.fwStake = this.fwStake || {})[game] = Math.floor(bet); return why; },
    cgPay(game, amount) { const n = pay0.call(this, game, amount); if (n > 0 && !FW.CASH.includes(game)) { const s = (this.fwStake || {})[game] || 0, x = s ? n / s : 0;
        const tier = n >= FW.hugeGold || (x >= FW.huge && n >= 150) ? 2 : n >= FW.gold || (x >= FW.big && n >= 60) ? 1 : 0; if (tier) this.cgCelebrate(tier, `${n.toLocaleString("en")} gold!`); } return n; },
    tkAdd(n, why) { const k = tk0.call(this, n, why); if (k >= FW.tickets) this.cgCelebrate(1, `${k} tickets!`); return k; },
    cgCard(rare, why, rnd) { const c = card0.call(this, rare, why, rnd); if (c && rare) this.cgCelebrate(1, "A rare card!"); return c; },
    cgTierCard(tier, why, R) { const c = tier0.call(this, tier, why, R); if (c && tier === "rare") this.cgCelebrate(1, "A rare card!"); return c; },
    // ---- the Town Lottery ----
    lotStore() { const F = this.cgStore(); F.lot = F.lot || { slips: [], pot: LOT.pot0, potKey: "", n: 0, won: 0, best: 0, news: [], seen: {} }; return F.lot; },
    lotBalls(key) { const R = new CM.Random(CM.hashSeed(`${this.seed}:lottery:${key}`)); return R.shuffle(Array.from({ length: LOT.of }, (_, i) => i + 1)).slice(0, LOT.pick); },
    lotBuy(nums, now) { now = now || Date.now(); const S = this.lotStore(), key = LOT.drawKey(now); if (S.slips.filter((s) => s.key === key).length >= LOT.max) return { error: `${LOT.max} slips a draw is the limit.` };
      const R = new CM.Random(CM.hashSeed(`${this.seed}:lotquick:${S.n}`)); nums = nums && nums.length ? [...new Set(nums.map(Number))].sort((a, b) => a - b) : LOT.quick(R);
      if (nums.length !== LOT.pick || nums.some((n) => !(n >= 1 && n <= LOT.of))) return { error: `Pick ${LOT.pick} different numbers from 1 to ${LOT.of}.` };
      const why = this.cgStake("lottery", LOT.price); if (why) return { error: why }; S.n += 1; const slip = { key, nums, id: S.n }; S.slips.push(slip); this.saveCasino && this.saveCasino(); return slip; },
    // the pot through every night up to this draw: it grows, and now and then the village wins it
    lotPotTo(key) { const S = this.lotStore(); if (!S.potKey) { S.potKey = key; return S.pot; } let k = S.potKey, guard = 0;
      while (k < key && guard++ < 120) { k = LOT.nextKey(k); const R = new CM.Random(CM.hashSeed(`${this.seed}:lotpot:${k}`)), mine = S.slips.filter((s) => s.key === k).length * LOT.price;
        S.pot += R.int(250, 600) + Math.floor(mine * LOT.share); if (k < key && R.chance(LOT.villager)) { S.news.unshift({ key: k, who: R.pick(CM.FLOOR ? CM.FLOOR.FOLK : ["a farmer"]), pot: S.pot }); S.news.length = Math.min(S.news.length, 6); S.pot = LOT.pot0; } }
      S.potKey = key; return S.pot; },
    lotDue(now) { now = now || Date.now(); return [...new Set(this.lotStore().slips.filter((s) => LOT.drawTime(s.key) <= now).map((s) => s.key))].sort(); },
    lotMatch(slip, balls) { return slip.nums.filter((n) => balls.includes(n)).length; },
    // a night's draw, settled: every slip in it checked and paid
    lotSettle(key, now) { now = now || Date.now(); if (LOT.drawTime(key) > now) return { error: "That draw hasn't happened yet." }; const S = this.lotStore(), mine = S.slips.filter((s) => s.key === key); if (!mine.length) return { error: "No slips in that draw." };
      const pot = this.lotPotTo(key), balls = this.lotBalls(key), out = { key, balls, slips: [], gold: 0, tickets: 0, cards: [], pot };
      for (const s of mine) { const m = this.lotMatch(s, balls); let gold = 0, tickets = 0;
        if (m === 6) { gold = S.pot; tickets = LOT.jackTickets; out.jackpot = gold; S.pot = LOT.pot0; S.news.unshift({ key, who: "You", pot: gold }); this.cgCelebrate(3, `THE TOWN JACKPOT - ${gold.toLocaleString("en")} gold!`); }
        else if (LOT.PAYS[m]) [gold, tickets] = LOT.PAYS[m];
        if (m >= 5) { const c = this.cgTierCard("rare", m === 6 ? "The Town Lottery's jackpot!" : "Five numbers in the Town Lottery!", new CM.Random(CM.hashSeed(`${this.seed}:lotcard:${s.id}`))); if (c) out.cards.push(c); }
        out.gold += gold; out.tickets += tickets; out.slips.push({ nums: s.nums, m, gold }); S.best = Math.max(S.best, m); }
      if (out.gold) { this.cgPay("lottery", out.gold); S.won += out.gold; } if (out.tickets && this.tkAdd) this.tkAdd(out.tickets, "lottery");
      S.slips = S.slips.filter((s) => s.key !== key); S.seen[key] = { balls, gold: out.gold }; const keys = Object.keys(S.seen).sort(); while (keys.length > 10) delete S.seen[keys.shift()];
      this.saveCasino && this.saveCasino(); this.emit("change"); return out; },
    // ---- the Drop Board ----
    pkDrop(bet, risk) { const T = PK.RISK[risk]; if (!T) return { error: "Pick a board." }; const why = this.cgStake("plinko", bet); if (why) return { error: why };
      const F = this.cgStore(), P = F.pk = F.pk || { drops: 0, best: 0, corner: false }, R = this.cgRnd("plinko"), path = PK.path(R), bin = path.reduce((a, b) => a + b, 0), mult = T[bin], gold = Math.floor(Math.floor(bet) * mult);
      P.drops += 1; P.best = Math.max(P.best, mult); if (gold) this.cgPay("plinko", gold); const out = { path, bin, mult, gold, tickets: 0 };
      if (mult >= 10) { out.tickets = Math.min(60, Math.round(mult / 2)); this.tkAdd && this.tkAdd(out.tickets, "plinko"); }
      if (risk === "high" && (bin === 0 || bin === PK.rows) && !P.corner) { P.corner = true; out.card = this.cgTierCard("rare", "The Drop Board's far corner!", R); }
      this.saveCasino && this.saveCasino(); this.emit("change"); return out; },
    // ---- the Fishing Pond ----
    pdStore() { const F = this.cgStore(); F.pond = F.pond || { bait: "worms", left: 0, n: 0, book: {}, best: {}, landed: 0, lost: 0, cur: null, all: false }; return F.pond; },
    pdBuy(bait) { const B = POND.BAIT[bait]; if (!B) return { error: "No such bait." }; const S = this.pdStore(); if (S.left && S.bait !== bait) return { error: "Use up the bait you have first." };
      const why = this.cgStake("pond", B.price); if (why) return { error: why }; S.bait = bait; S.left += B.casts; this.saveCasino && this.saveCasino(); return { ok: true, left: S.left }; },
    pdCast(dist, hour) { const S = this.pdStore(); if (S.cur) return { error: "Your line's already out." }; if (S.left < 1) return { error: "Buy some bait first." }; S.left -= 1; S.n += 1;
      hour = hour === undefined ? new Date().getHours() : hour; const R = new CM.Random(CM.hashSeed(`${this.seed}:pond:${S.n}`)); S.cur = Object.assign(POND.pick(CM.ARC.clamp(dist, 0, 1), S.bait, hour, R), { dist }); this.saveCasino && this.saveCasino(); return S.cur; },
    // the fish on the line, landed (ok) or lost
    pdLand(ok) { const S = this.pdStore(), c = S.cur; if (!c) return { error: "Nothing on the line." }; S.cur = null; if (!ok) { S.lost += 1; this.saveCasino && this.saveCasino(); return { lost: true, name: c.name }; }
      const f = POND.byId[c.id], gold = Math.floor(c.kg * f[5]), out = { name: c.name, id: c.id, kg: c.kg, gold, tickets: f[6], tier: c.tier, cards: [] }; S.landed += 1;
      if (c.tier > 0) { if (!S.book[c.id]) { S.book[c.id] = 0; out.first = true; out.tickets += 10; } S.book[c.id] += 1; if (!S.best[c.id] || c.kg > S.best[c.id]) { out.best = !!S.best[c.id]; S.best[c.id] = c.kg; } }
      if (gold) this.cgPay("pond", gold); if (out.tickets && this.tkAdd) this.tkAdd(out.tickets, "pond");
      if (c.id === "golden") { const card = this.cgTierCard("rare", "The golden carp, landed!", new CM.Random(CM.hashSeed(`${this.seed}:pondcard:${S.n}`))); if (card) out.cards.push(card); this.cgCelebrate(2, "The golden carp!"); }
      const kinds = POND.FISH.filter((x) => x[2] > 0).map((x) => x[0]); if (!S.all && kinds.every((k) => S.book[k])) { S.all = true; out.all = true; const card = this.cgTierCard("rare", "Every fish in the creel book!", new CM.Random(CM.hashSeed(`${this.seed}:pondall`))); if (card) out.cards.push(card); }
      if (c.tier > 0 && this.cgRecord) this.cgRecord("pond", Math.round(c.kg * 1000), c.tier); this.saveCasino && this.saveCasino(); this.emit("change"); return out; },
  });
}
