"use strict";
// The Gilded Joker's floor (the twentieth big update - v13.0): beside the Claudeatro table, four of a casino's own
// games, played for the party's gold at fair odds - the house keeps a little and no more, and every game's return is
// what the tests say it is:
//   - the Gilded Reels, three reels and one line, 97.1% back (and three Jokers: a thousand times the bet and a rare
//     Claudescryption card for Leshy's box);
//   - Roulette, a single zero, the usual payouts, 97.3% back (a winning straight bet on the zero: a common card too);
//   - Blackjack, six decks, a natural pays 3 to 2, the dealer stands on soft 17, double any two, split once - about
//     99.5% back with good play (a natural of the Ace and Jack of Spades, the black jack: a common card besides);
//   - Jacks or Better, the full 9/6 pay table, 99.5% back with good play (a royal flush: a rare card besides).
// Every turn of the dice is the run's seed and the house's count, so a game plays back the same. The window is
// 76i-casinofloor.js; the Claudeatro table is 64k-claudeatro.js.
CM.CG = {
  chips: [1, 5, 25, 100, 500], max: 500,
  REEL: ["cherry", "lemon", "bell", "lemon", "bar", "cherry", "lemon", "seven", "bell", "lemon", "cherry", "bar", "lemon", "bell", "joker", "cherry", "lemon", "bell", "bar", "lemon", "seven", "cherry", "bell", "lemon", "bar", "bell"],   // (5 cherries, 8 lemons, 6 bells, 4 bars, 2 sevens, a Joker)
  SLOT_PAY: { joker: 1000, seven: 100, bar: 20, bell: 9, lemon: 5, cherry: 10, mix: 2, twoCherry: 2, oneCherry: 1 },
  SLOT_ART: { cherry: "🍒", lemon: "🍋", bell: "🔔", bar: "▬", seven: "7", joker: "🃏" },
  RED: new Set([1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]),
  WHEEL: [0, 32, 15, 19, 4, 21, 2, 25, 17, 34, 6, 27, 13, 36, 11, 30, 8, 23, 10, 5, 24, 16, 33, 1, 20, 14, 31, 9, 22, 18, 29, 7, 28, 12, 35, 3, 26],
  RBET: { straight: 35, red: 1, black: 1, odd: 1, even: 1, low: 1, high: 1, dozen: 2, column: 2 },
  VP_PAY: [["Royal Flush", 800], ["Straight Flush", 50], ["Four of a Kind", 25], ["Full House", 9], ["Flush", 6], ["Straight", 4], ["Three of a Kind", 3], ["Two Pair", 2], ["Jacks or Better", 1]],
  DECKS: 6,
};
const CG = CM.CG;
// ---- the reels: a line's pay, as a multiple of the bet ----
CG.slotLine = (a, b, c) => {
  const P = CG.SLOT_PAY;
  if (a === b && b === c) return { pay: P[a], what: `Three ${a === "joker" ? "Jokers" : a === "cherry" ? "cherries" : a + "s"}`, jackpot: a === "joker" };
  if ([a, b, c].every((x) => x === "bar" || x === "seven" || x === "bell")) return { pay: P.mix, what: "Any three of bars, bells and sevens" };
  const ch = [a, b, c].filter((x) => x === "cherry").length;
  if (ch === 2) return { pay: P.twoCherry, what: "Two cherries" };
  if (ch === 1 && a === "cherry") return { pay: P.oneCherry, what: "A cherry on the first reel" };
  return { pay: 0, what: "" };
};
CG.slotReturn = () => { const R = CG.REEL; let t = 0; for (const a of R) for (const b of R) for (const c of R) t += CG.slotLine(a, b, c).pay; return t / R.length ** 3; };
// ---- roulette: what a bet on a number returns (stake and winnings), 0 when it loses ----
CG.rouletteWins = (bet, n) => {
  if (bet.type === "straight") return bet.n === n;
  if (n === 0) return false;
  switch (bet.type) {
    case "red": return CG.RED.has(n); case "black": return !CG.RED.has(n); case "odd": return n % 2 === 1; case "even": return n % 2 === 0;
    case "low": return n <= 18; case "high": return n >= 19; case "dozen": return Math.ceil(n / 12) === bet.n; case "column": return ((n - 1) % 3) + 1 === bet.n;
    default: return false;
  }
};
CG.rouletteReturn = (type, n = 1) => { let t = 0; for (let k = 0; k <= 36; k++) if (CG.rouletteWins({ type, n }, k)) t += CG.RBET[type] + 1; return t / 37; };
// ---- cards: the Claudeatro table's own (r 2-14, an Ace 14; s S H D C) ----
CG.deck = (n = 1) => { const out = []; let id = 1; for (let d = 0; d < n; d++) for (const s of "SHDC") for (let r = 2; r <= 14; r++) out.push({ r, s, id: id++ }); return out; };
CG.shuffle = (cards, rnd) => { for (let i = cards.length - 1; i > 0; i--) { const j = rnd.int(0, i); [cards[i], cards[j]] = [cards[j], cards[i]]; } return cards; };
CG.bjValue = (cards) => { let t = 0, aces = 0; for (const c of cards) { if (c.down) continue; if (c.r === 14) { aces++; t += 11; } else t += Math.min(10, c.r); } while (t > 21 && aces) { t -= 10; aces--; } return { total: t, soft: aces > 0 }; };
CG.bjNatural = (cards) => cards.length === 2 && CG.bjValue(cards).total === 21;
// ---- video poker: the hand's name and pay ----
CG.vpRank = (cards) => {
  const rs = cards.map((c) => c.r).sort((a, b) => a - b), flush = cards.every((c) => c.s === cards[0].s), counts = {};
  for (const r of rs) counts[r] = (counts[r] || 0) + 1;
  const groups = Object.values(counts).sort((a, b) => b - a), uniq = Object.keys(counts).length;
  const wheel = rs.join(",") === "2,3,4,5,14", straight = uniq === 5 && (rs[4] - rs[0] === 4 || wheel);
  if (straight && flush) return rs[0] === 10 ? 0 : 1;
  if (groups[0] === 4) return 2; if (groups[0] === 3 && groups[1] === 2) return 3; if (flush) return 4; if (straight) return 5; if (groups[0] === 3) return 6;
  if (groups[0] === 2 && groups[1] === 2) return 7;
  if (groups[0] === 2) { const pair = Number(Object.keys(counts).find((r) => counts[r] === 2)); if (pair >= 11) return 8; }
  return -1;
};

Object.assign(CM.Game.prototype, {
  cgStore() { const K = this.casino(); const F = K.floor = K.floor || {}; F.n = F.n || 0; F.wagered = F.wagered || {}; F.paid = F.paid || {}; F.played = F.played || {}; F.cards = F.cards || []; return F; },
  cgRnd(what) { const F = this.cgStore(); F.n += 1; return new CM.Random(CM.hashSeed(`${this.seed}:gildedfloor:${what}:${F.n}`)); },
  // a stake on the table: a whole number of gold, within the house's limit and the party's purse
  cgStake(game, bet) {
    bet = Math.floor(Number(bet) || 0); if (bet < 1) return "Put a chip down first.";
    if (bet > CG.max) return `The house takes no more than ${CG.max} gold a bet.`; if (bet > this.gold) return `The party has ${this.gold} gold.`;
    const F = this.cgStore(); this.gold -= bet; F.wagered[game] = (F.wagered[game] || 0) + bet; F.played[game] = (F.played[game] || 0) + 1; return "";
  },
  cgPay(game, amount) { if (amount <= 0) return 0; const F = this.cgStore(); this.gold += amount; F.paid[game] = (F.paid[game] || 0) + amount; return amount; },
  // a jackpot's card: into the box at Leshy's cabin
  cgCard(rare, why, rnd) { const pool = rare ? CM.CARD_RARES : CM.CARD_COMMONS; if (!pool || !pool.length) return null; const name = pool[rnd.int(0, pool.length - 1)]; this.addCard(name, why); this.cgStore().cards.push(name); this.tally.casinoCards = (this.tally.casinoCards || 0) + 1; return name; },
  // ---- the Gilded Reels ----
  slotSpin(bet) {
    const why = this.cgStake("slots", bet); if (why) return { error: why };
    const R = this.cgRnd("slots"), stops = [0, 1, 2].map(() => R.int(0, CG.REEL.length - 1)), [a, b, c] = stops.map((s) => CG.REEL[s]), line = CG.slotLine(a, b, c);
    const won = this.cgPay("slots", line.pay * bet), card = line.jackpot ? this.cgCard(true, "The Gilded Reels pay their jackpot!", R) : null;
    if (line.jackpot) this.cgStore().jackpots = (this.cgStore().jackpots || 0) + 1;
    this.saveCasino && this.saveCasino(); this.emit("change");
    return { stops, symbols: [a, b, c], won, what: line.what, jackpot: !!line.jackpot, card };
  },
  // ---- Roulette: bets of {type, n, amount}; the wheel's number, and what came back ----
  rouletteSpin(bets) {
    bets = (bets || []).filter((b) => b && b.amount >= 1 && CG.RBET[b.type] !== undefined); const total = bets.reduce((t, b) => t + Math.floor(b.amount), 0);
    if (!total) return { error: "Place a bet on the board first." }; if (total > CG.max * 4) return { error: `The house takes no more than ${CG.max * 4} gold on a spin.` };
    const why = this.cgStake("roulette", total); if (why) return { error: why };
    const R = this.cgRnd("roulette"), n = R.int(0, 36); let back = 0; const winners = [];
    for (const b of bets) if (CG.rouletteWins(b, n)) { const r = Math.floor(b.amount) * (CG.RBET[b.type] + 1); back += r; winners.push(b); }
    this.cgPay("roulette", back);
    const card = n === 0 && bets.some((b) => b.type === "straight" && b.n === 0 && b.amount >= 5) ? this.cgCard(false, "The zero comes up for you!", R) : null;
    this.saveCasino && this.saveCasino(); this.emit("change");
    return { n, colour: n === 0 ? "green" : CG.RED.has(n) ? "red" : "black", staked: total, back, winners, card };
  },
  // ---- Blackjack: a hand kept on the table until it is settled (it waits if you leave) ----
  bjState() { return this.cgStore().bj || null; },
  bjShoe() { const F = this.cgStore(); if (!F.shoe || F.shoe.length < 78) { F.shoe = CG.shuffle(CG.deck(CG.DECKS), this.cgRnd("shoe")); F.shuffled = true; } return F.shoe; },
  bjDraw(down) { const c = Object.assign({}, this.bjShoe().pop()); if (down) c.down = true; return c; },
  bjDeal(bet) {
    if (this.bjState() && this.bjState().stage === "play") return { error: "A hand is on the table." };
    const why = this.cgStake("blackjack", bet); if (why) return { error: why };
    const F = this.cgStore(); F.shuffled = false; this.bjShoe(); const shuffled = F.shuffled;
    const p = [this.bjDraw(), null], d = [this.bjDraw(), null]; p[1] = this.bjDraw(); d[1] = this.bjDraw(true);
    F.bj = { stage: "play", hands: [{ cards: p, bet: Math.floor(bet), done: false }], active: 0, dealer: d, shuffled };
    const peek = Object.assign({}, d[1]); delete peek.down;
    if (CG.bjNatural(p) || ((d[0].r === 14 || Math.min(10, d[0].r) === 10) && CG.bjNatural([d[0], peek]))) return this.bjSettle();
    this.saveCasino && this.saveCasino(); return F.bj;
  },
  bjHand() { const B = this.bjState(); return B && B.stage === "play" ? B.hands[B.active] : null; },
  bjHit() { const H = this.bjHand(); if (!H) return { error: "No hand." }; H.cards.push(this.bjDraw()); if (CG.bjValue(H.cards).total >= 21) return this.bjNext(); this.saveCasino && this.saveCasino(); return this.bjState(); },
  bjStand() { if (!this.bjHand()) return { error: "No hand." }; return this.bjNext(); },
  bjCanDouble() { const H = this.bjHand(); return !!(H && H.cards.length === 2 && !H.splitAces && this.gold >= H.bet); },
  bjDouble() { const H = this.bjHand(); if (!this.bjCanDouble()) return { error: "Not now." }; const why = this.cgStake("blackjack", H.bet); if (why) return { error: why }; this.cgStore().played.blackjack -= 1; H.bet *= 2; H.doubled = true; H.cards.push(this.bjDraw()); return this.bjNext(); },
  bjCanSplit() { const B = this.bjState(), H = this.bjHand(); return !!(H && B.hands.length === 1 && H.cards.length === 2 && Math.min(10, H.cards[0].r) === Math.min(10, H.cards[1].r) && this.gold >= H.bet); },
  bjSplit() {
    const B = this.bjState(), H = this.bjHand(); if (!this.bjCanSplit()) return { error: "Not now." }; const why = this.cgStake("blackjack", H.bet); if (why) return { error: why }; this.cgStore().played.blackjack -= 1;
    const aces = H.cards[0].r === 14, two = { cards: [H.cards.pop(), this.bjDraw()], bet: H.bet, done: false, split: true, splitAces: aces }; H.cards.push(this.bjDraw()); H.split = true; H.splitAces = aces; B.hands.push(two);
    if (aces) { B.active = B.hands.length - 1; return this.bjSettle(); }             // (split aces: one card each, and done)
    this.saveCasino && this.saveCasino(); return B;
  },
  bjNext() { const B = this.bjState(); B.hands[B.active].done = true; if (B.active < B.hands.length - 1) { B.active += 1; this.saveCasino && this.saveCasino(); return B; } return this.bjSettle(); },
  // the dealer turns the hole card and draws to seventeen (stands on a soft seventeen); each hand paid
  bjSettle() {
    const B = this.bjState(), d = B.dealer; d[1].down = false; const playerNatural = B.hands.length === 1 && CG.bjNatural(B.hands[0].cards) && !B.hands[0].split, dealerNatural = CG.bjNatural(d);
    const live = B.hands.some((H) => CG.bjValue(H.cards).total <= 21);
    if (!playerNatural && !dealerNatural && live) while (CG.bjValue(d).total < 17) d.push(this.bjDraw());
    const dv = CG.bjValue(d).total; let back = 0;
    B.results = B.hands.map((H) => {
      const v = CG.bjValue(H.cards).total, nat = playerNatural;
      let r, pay = 0;
      if (nat && dealerNatural) { r = "push"; pay = H.bet; } else if (nat) { r = "blackjack"; pay = H.bet + Math.ceil(H.bet * 1.5); } else if (dealerNatural) r = "lose";
      else if (v > 21) r = "bust"; else if (dv > 21 || v > dv) { r = "win"; pay = H.bet * 2; } else if (v === dv) { r = "push"; pay = H.bet; } else r = "lose";
      back += pay; return { r, pay };
    });
    this.cgPay("blackjack", back); B.back = back; B.stage = "done";
    const H0 = B.hands[0].cards; B.card = playerNatural && H0.some((c) => c.r === 14 && c.s === "S") && H0.some((c) => c.r === 11 && c.s === "S") ? this.cgCard(false, "The black jack itself!", this.cgRnd("bjcard")) : null;
    this.saveCasino && this.saveCasino(); this.emit("change"); return B;
  },
  // ---- Jacks or Better: deal five, hold what you will, draw ----
  vpState() { return this.cgStore().vp || null; },
  vpDeal(bet) {
    if (this.vpState() && this.vpState().stage === "hold") return { error: "Draw first." };
    const why = this.cgStake("poker", bet); if (why) return { error: why };
    const deck = CG.shuffle(CG.deck(1), this.cgRnd("poker")); this.cgStore().vp = { stage: "hold", bet: Math.floor(bet), cards: deck.splice(0, 5), held: [false, false, false, false, false], rest: deck };
    this.saveCasino && this.saveCasino(); return this.vpState();
  },
  vpHold(i) { const V = this.vpState(); if (!V || V.stage !== "hold") return false; V.held[i] = !V.held[i]; return true; },
  vpDraw() {
    const V = this.vpState(); if (!V || V.stage !== "hold") return { error: "Deal first." };
    V.drawn = []; V.cards = V.cards.map((c, i) => { if (V.held[i]) return c; V.drawn.push(i); return V.rest.shift(); });
    const k = CG.vpRank(V.cards); V.rank = k; V.stage = "done"; V.back = this.cgPay("poker", k >= 0 ? V.bet * CG.VP_PAY[k][1] : 0) || 0; V.what = k >= 0 ? CG.VP_PAY[k][0] : "";
    V.card = k === 0 ? this.cgCard(true, "A royal flush!", this.cgRnd("vpcard")) : null; delete V.rest;
    this.saveCasino && this.saveCasino(); this.emit("change"); return V;
  },
});
