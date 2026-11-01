"use strict";
// The Residents' Game (v16.0): fixed-limit Texas hold'em at the back table of the Gilded Joker against four of the
// village's six residents - the tavern-keeper, the merchant, the smith, the librarian, the priest and the farmer's
// hand - each with a way of playing of their own (loose or tight, timid or pushy, given to bluffing or not), judged by
// how often their cards would win (a quick count of a hundred deals) against what the pot asks. A buy-in (50 to 500
// gold) is the stake; the blinds are a fiftieth and a hundredth of it; bets are one big blind before the turn and two
// after, four to a street. Pots are the party's to win off the residents, side pots and all; leave between hands to
// cash the chips back to gold. Tickets: those of the stake, plus a few for a pot won with a straight or better and for
// each resident sent home; a royal flush brings a rare card, and sending the whole table home a card the first time
// at each buy-in (tickets after). The table is kept between visits as plain state. The window is 76zzg-holdem.js.
{ const HE = CM.HE = { BUYINS: [50, 100, 250, 500], cap: 4, sims: 100,
    RES: {
      tavern: { name: "the tavern-keeper", short: "Tavern-keeper", style: "calls anything", loose: 0.85, aggr: 0.25, bluff: 0.05, col: "#C07A40", hair: "#8A3A20",
        say: { win: "\"That's the round paid for.\"", fold: "\"Not with these.\"", raise: "\"Bit more in the pot, love.\"", bust: "\"Well, that's me back behind the bar.\"" } },
      merchant: { name: "the merchant", short: "Merchant", style: "counts the odds", loose: 0.45, aggr: 0.5, bluff: 0.1, col: "#3A6AA0", hair: "#3A3030",
        say: { win: "\"A fair return.\"", fold: "\"The price is wrong.\"", raise: "\"Let's see what it's worth to you.\"", bust: "\"I'll put it down as a loss.\"" } },
      smith: { name: "the smith", short: "Smith", style: "plays few, plays hard", loose: 0.3, aggr: 0.8, bluff: 0.08, col: "#6A6A70", hair: "#202020",
        say: { win: "\"Hammered.\"", fold: "\"Hm.\"", raise: "\"Raise.\"", bust: "\"Back to the forge.\"" } },
      library: { name: "the librarian", short: "Librarian", style: "a careful rock", loose: 0.2, aggr: 0.2, bluff: 0.02, col: "#5A4A7A", hair: "#B0A090",
        say: { win: "\"As the odds said.\"", fold: "\"I'll pass, thank you.\"", raise: "\"I believe I'll raise.\"", bust: "\"I should have stayed with my books.\"" } },
      priest: { name: "the priest", short: "Priest", style: "steady, a little hopeful", loose: 0.55, aggr: 0.4, bluff: 0.06, col: "#E8E0C8", hair: "#909090",
        say: { win: "\"Blessings on the house.\"", fold: "\"Not this time.\"", raise: "\"Have a little faith.\"", bust: "\"The collection plate will have to wait.\"" } },
      farm: { name: "the farmer's hand", short: "Farmer's hand", style: "wild and fearless", loose: 0.75, aggr: 0.85, bluff: 0.3, col: "#6A8A30", hair: "#D0A040",
        say: { win: "\"Ha! Told you!\"", fold: "\"Aw.\"", raise: "\"All the way up!\"", bust: "\"Easy come, easy go.\"" } },
    } };
  HE.RANKS = "  23456789TJQKA"; HE.SUITS = "♠♥♦♣";
  HE.CATS = ["High card", "Pair", "Two pair", "Three of a kind", "Straight", "Flush", "Full house", "Four of a kind", "Straight flush"];
  // the best five of any number of cards, as one number (higher wins)
  HE.score = (cs) => {
    const byS = [[], [], [], []], cnt = Array(15).fill(0); for (const c of cs) { byS[c.s].push(c.r); cnt[c.r] += 1; }
    const high = (rs) => { const has = new Set(rs); if (has.has(14)) has.add(1); for (let h = 14; h >= 5; h--) { let ok = true; for (let k = 0; k < 5; k++) if (!has.has(h - k)) { ok = false; break; } if (ok) return h; } return 0; };
    const pack = (cat, ks) => { let v = cat; for (let i = 0; i < 5; i++) v = v * 15 + (ks[i] || 0); return v; };
    for (const f of byS) if (f.length >= 5) { const h = high(f); if (h) return pack(8, [h]); }
    const gs = []; for (let r = 14; r >= 2; r--) if (cnt[r]) gs.push([cnt[r], r]); gs.sort((a, b) => b[0] - a[0] || b[1] - a[1]);
    const rest = (ex) => gs.filter((g) => !ex.includes(g[1])).map((g) => g[1]).sort((a, b) => b - a);
    if (gs[0][0] === 4) return pack(7, [gs[0][1], rest([gs[0][1]])[0]]);
    if (gs[0][0] === 3 && gs[1] && gs[1][0] >= 2) return pack(6, [gs[0][1], gs[1][1]]);
    for (const f of byS) if (f.length >= 5) return pack(5, f.sort((a, b) => b - a).slice(0, 5));
    const h = high(cs.map((c) => c.r)); if (h) return pack(4, [h]);
    if (gs[0][0] === 3) return pack(3, [gs[0][1], ...rest([gs[0][1]]).slice(0, 2)]);
    if (gs[0][0] === 2 && gs[1] && gs[1][0] === 2) return pack(2, [gs[0][1], gs[1][1], rest([gs[0][1], gs[1][1]])[0]]);
    if (gs[0][0] === 2) return pack(1, [gs[0][1], ...rest([gs[0][1]]).slice(0, 3)]);
    return pack(0, rest([]).slice(0, 5));
  };
  HE.cat = (v) => Math.floor(v / 759375);
  HE.royal = (v) => HE.cat(v) === 8 && Math.floor(v / 50625) % 15 === 14;
  HE.name = (c) => HE.RANKS[c.r] + HE.SUITS[c.s];
  // how often these cards win against so many random hands, by a quick count
  HE.equity = (hole, board, nOpp, R, sims = HE.sims) => {
    const used = new Set(hole.concat(board).map((c) => c.r * 4 + c.s)), deck = []; for (let r = 2; r <= 14; r++) for (let s = 0; s < 4; s++) if (!used.has(r * 4 + s)) deck.push({ r, s });
    const need = nOpp * 2 + 5 - board.length; let won = 0;
    for (let k = 0; k < sims; k++) { for (let i = 0; i < need; i++) { const j = i + Math.floor(R.next() * (deck.length - i)); [deck[i], deck[j]] = [deck[j], deck[i]]; }
      const b = board.concat(deck.slice(nOpp * 2, need)), me = HE.score(hole.concat(b)); let ties = 0, lost = false;
      for (let o = 0; o < nOpp && !lost; o++) { const v = HE.score([deck[o * 2], deck[o * 2 + 1]].concat(b)); if (v > me) lost = true; else if (v === me) ties += 1; }
      if (!lost) won += 1 / (ties + 1); }
    return won / sims;
  };
  // ---- the table, as plain state ----
  const inHand = (S) => S.cards && !S.folded, canAct = (S) => inHand(S) && !S.allin;
  HE.newTable = (seed, buyin, who) => { const bb = Math.max(2, Math.round(buyin / 50)); return { rs: CM.hashSeed(seed) >>> 0, buyin, bb, sb: Math.floor(bb / 2), seats: [{ id: "you", stack: buyin }].concat(who.map((id) => ({ id, stack: buyin }))), button: who.length, hand: 0, stage: "between", board: [], events: [] }; };
  HE.pot = (T) => T.seats.reduce((a, S) => a + (S.put || 0), 0);
  HE.next = (T, i, ok) => { for (let k = 1; k <= T.seats.length; k++) { const j = (i + k) % T.seats.length; if (ok(T.seats[j])) return j; } return -1; };
  const pay = (T, i, amt) => { const S = T.seats[i], n = Math.min(amt, S.stack); S.stack -= n; S.bet += n; S.put += n; if (S.stack === 0) S.allin = true; return n; };
  HE.deal = (T) => {
    if (T.stage === "hand") return "A hand is on.";
    if (T.seats[0].stack <= 0) { T.stage = "over"; return "You have no chips."; } if (T.seats.filter((S) => S.stack > 0).length < 2) { T.stage = "over"; return "Nobody left to play."; }
    const R = new CM.Random(T.rs); for (const S of T.seats) Object.assign(S, { cards: null, bet: 0, put: 0, folded: false, allin: false, acted: false, last: "" });
    const deck = []; for (let r = 2; r <= 14; r++) for (let s = 0; s < 4; s++) deck.push({ r, s }); R.shuffle(deck); T.deck = deck; T.board = []; T.rs = R.s;
    const has = (S) => S.stack > 0; T.button = HE.next(T, T.button, has); const n = T.seats.filter(has).length;
    for (let k = 0, i = T.button; k < n; k++) { i = HE.next(T, i, has); T.seats[i].cards = [T.deck.pop(), T.deck.pop()]; }
    const sbI = n === 2 ? T.button : HE.next(T, T.button, has), bbI = HE.next(T, sbI, has); pay(T, sbI, T.sb); pay(T, bbI, T.bb); T.sbI = sbI; T.bbI = bbI;
    T.stage = "hand"; T.street = 0; T.cur = T.bb; T.raises = 1; T.hand += 1; T.events.push({ kind: "deal", hand: T.hand, button: T.button, sb: sbI, bb: bbI });
    T.toAct = HE.next(T, bbI, canAct); if (T.toAct < 0 || (T.seats.filter(canAct).length < 2 && T.seats[T.toAct].bet >= T.cur)) HE.endStreet(T); return "";
  };
  HE.toCall = (T, i) => Math.max(0, T.cur - T.seats[i].bet);
  HE.betSize = (T) => (T.street < 2 ? T.bb : T.bb * 2);
  HE.act = (T, i, a) => {
    if (T.stage !== "hand" || T.toAct !== i) return "Not your turn."; const S = T.seats[i], owe = HE.toCall(T, i);
    if (a === "raise" && (T.raises >= HE.cap || S.stack <= owe)) a = "call"; if (a === "fold" && owe === 0) a = "call";
    if (a === "fold") { S.folded = true; S.last = "fold"; }
    else if (a === "call") { pay(T, i, owe); S.last = owe ? (S.allin ? "all in" : "call") : "check"; }
    else { pay(T, i, owe + HE.betSize(T)); T.cur = Math.max(T.cur, S.bet); T.raises += 1; for (const O of T.seats) if (O !== S) O.acted = false; S.last = S.allin ? "all in" : T.raises === 1 ? "bet" : "raise"; }
    S.acted = true; T.events.push({ kind: "act", seat: i, what: S.last, amount: S.bet });
    const left = T.seats.filter(inHand); if (left.length === 1) { HE.award(T, false); return ""; }
    const nx = HE.next(T, i, (O) => canAct(O) && (!O.acted || O.bet < T.cur)); if (nx >= 0) T.toAct = nx; else HE.endStreet(T); return "";
  };
  HE.endStreet = (T) => {
    for (;;) { for (const S of T.seats) { S.bet = 0; S.acted = false; } T.cur = 0; T.raises = 0;
      if (T.street >= 3) { HE.award(T, true); return; } T.street += 1; T.deck.pop(); const k = T.street === 1 ? 3 : 1; for (let j = 0; j < k; j++) T.board.push(T.deck.pop()); T.events.push({ kind: "street", street: T.street, board: T.board.slice() });
      if (T.seats.filter(canAct).length >= 2) { T.toAct = HE.next(T, T.button, canAct); return; } }
  };
  // the pots, layer by layer, to the best hands that reached them
  HE.award = (T, show) => {
    const ins = T.seats.map((S, i) => [S, i]).filter(([S]) => inHand(S)), val = {}; if (show) for (const [S, i] of ins) { val[i] = HE.score(S.cards.concat(T.board)); T.events.push({ kind: "show", seat: i, cards: S.cards, cat: HE.cat(val[i]) }); }
    const levels = [...new Set(T.seats.filter((S) => S.put > 0 && inHand(S)).map((S) => S.put))].sort((a, b) => a - b); let prev = 0; const won = {};
    for (const lv of levels) { let part = 0; for (const S of T.seats) part += Math.max(0, Math.min(S.put, lv) - prev); const elig = ins.filter(([S]) => S.put >= lv);
      const best = show ? Math.max(...elig.map(([, i]) => val[i])) : null, ws = show ? elig.filter(([, i]) => val[i] === best) : elig, each = Math.floor(part / ws.length); let odd = part - each * ws.length;
      for (const [S, i] of ws) { const n = each + (odd > 0 ? 1 : 0); odd -= 1; S.stack += n; won[i] = (won[i] || 0) + n; } prev = lv; }
    // chips put in above anyone's reach go back
    for (const S of T.seats) if (S.put > prev) { S.stack += S.put - prev; }
    for (const i of Object.keys(won)) T.events.push({ kind: "win", seat: Number(i), amount: won[i], cat: show ? HE.cat(val[i]) : -1, royal: show && HE.royal(val[i]), pot: HE.pot(T) });
    T.stage = "between"; T.toAct = -1; for (const S of T.seats) { S.put = 0; S.bet = 0; }
    T.seats.forEach((S, i) => { if (i && S.stack <= 0 && !S.out) { S.out = true; T.events.push({ kind: "bust", seat: i, id: S.id }); } });
    if (T.seats[0].stack <= 0) { T.stage = "over"; T.events.push({ kind: "broke" }); } else if (T.seats.every((S, i) => !i || S.out)) { T.stage = "over"; T.events.push({ kind: "cleared" }); }
  };
  // a resident's turn: their chance of winning against the pot's price, as their nature bends it
  HE.decide = (T, i) => {
    const S = T.seats[i], P = HE.RES[S.id], R = new CM.Random(T.rs), opp = T.seats.filter((O) => O !== S && inHand(O)).length, eq = HE.equity(S.cards, T.board, opp, R, T.street ? HE.sims : 60);
    const owe = HE.toCall(T, i), pot = HE.pot(T), odds = owe / (pot + owe), fair = 1 / (opp + 1), adj = eq + (P.loose - 0.5) * 0.12 * (T.street ? 0.6 : 1), roll = R.next(); let a;
    if (owe === 0) a = adj > fair + 0.12 + (1 - P.aggr) * 0.15 && roll < 0.35 + P.aggr * 0.6 ? "raise" : roll < P.bluff ? "raise" : "call";
    else if (adj > fair + 0.18 + (1 - P.aggr) * 0.15 && roll < P.aggr) a = "raise";
    else if (adj >= odds - (P.loose - 0.5) * 0.08 || (T.street === 0 && adj > fair * 0.8 + (0.5 - P.loose) * 0.25)) a = "call";
    else a = roll < P.bluff * 0.5 ? "raise" : "fold";
    T.rs = R.s; return a;
  };
  HE.aiStep = (T) => { if (T.stage !== "hand" || T.toAct <= 0) return false; HE.act(T, T.toAct, HE.decide(T, T.toAct)); return true; };
  // ---- the party at the table ----
  const ROYAL_WHY = "A royal flush at the Residents' Game!";
  Object.assign(CM.Game.prototype, {
    heStore() { const F = this.cgStore(); F.he = F.he || { cleared: {}, hands: 0, pots: 0, best: 0, sent: 0 }; return F.he; },
    heTable() { return this.heStore().live || null; },
    heWho(n) { const R = new CM.Random(CM.hashSeed(`${this.seed}:he:who:${n}`)); return R.shuffle(Object.keys(HE.RES)).slice(0, 4); },
    heSit(buyin) { const H = this.heStore(); if (H.live) return { error: "You're already at the table." }; if (!HE.BUYINS.includes(buyin)) return { error: "Pick a buy-in." };
      const why = this.cgStake("holdem", buyin); if (why) return { error: why }; const F = this.cgStore(); F.n += 1; H.live = HE.newTable(`${this.seed}:he:${F.n}`, buyin, this.heWho(F.n)); if (this.cgStamp) this.cgStamp("holdem"); HE.deal(H.live); this.saveCasino && this.saveCasino(); return { table: H.live }; },
    // the events since last asked, with the house's rewards worked in
    heEvents() { const T = this.heTable(); if (!T) return []; const out = T.events.splice(0), H = this.heStore();
      for (const e of out) {
        if (e.kind === "deal") H.hands += 1;
        if (e.kind === "win" && e.seat === 0) { H.pots += 1; H.best = Math.max(H.best, e.amount); const tk = e.cat >= 4 ? [0, 0, 0, 0, 1, 2, 3, 5, 10][e.cat] : 0; if (tk && this.tkAdd) { this.tkAdd(tk, "holdem"); e.tickets = tk; } if (e.royal) e.card = this.cgCard(true, ROYAL_WHY, this.cgRnd("herc")); }
        if (e.kind === "bust") { H.sent += 1; if (this.tkAdd) { this.tkAdd(2, "holdem"); e.tickets = 2; } }
        if (e.kind === "cleared") { const k = T.buyin; if (!H.cleared[k]) { H.cleared[k] = true; e.card = this.cgTierCard(T.buyin >= 250 ? "rare" : T.buyin >= 100 ? "better" : "common", `The Residents' Game: the whole table sent home at ${k} gold!`, new CM.Random(CM.hashSeed(`${this.seed}:he:card:${k}`))); } else if (this.tkAdd) { this.tkAdd(10, "holdem"); e.tickets = 10; } }
      }
      this.saveCasino && this.saveCasino(); return out; },
    heAct(a) { const T = this.heTable(); if (!T) return "Not at the table."; const why = HE.act(T, 0, a); this.saveCasino && this.saveCasino(); return why; },
    heAi() { const T = this.heTable(); const did = T ? HE.aiStep(T) : false; if (did) this.saveCasino && this.saveCasino(); return did; },
    heDeal() { const T = this.heTable(); if (!T) return "Not at the table."; const why = HE.deal(T); this.saveCasino && this.saveCasino(); return why; },
    // up from the table: the chips back to gold (between hands only)
    heLeave() { const H = this.heStore(), T = H.live; if (!T) return { error: "Not at the table." }; if (T.stage === "hand") return { error: "Finish the hand first." };
      const chips = T.seats[0].stack; delete H.live; if (chips > 0) this.cgPay("holdem", chips); if (chips > T.buyin && this.cgRecord) this.cgRecord("holdem", chips - T.buyin, 0); this.saveCasino && this.saveCasino(); this.emit("change"); return { chips, net: chips - T.buyin }; },
  });
  if (CM.CLUB && !CM.CLUB.BOARDS.includes("holdem")) CM.CLUB.BOARDS.push("holdem");
}
