"use strict";
// The Hexed Wand (the twenty-fourth big update - v13.4): a duel across a table with the house's dealer. A wand is
// loaded with charges - live hexes and duds, the counts told, the order not. On your turn point it at the dealer or at
// yourself: a live hex snuffs one of the target's candles (two with a whetstone); a dud does nothing, and if you aimed
// it at yourself the turn stays yours. When the wand is spent it is loaded again, and charms are dealt to both: a
// seeing-glass (see the next charge), an unloading (throw the next charge out, seen), a whetstone (the next live hex
// snuffs two), a stub of tallow (light a candle again) and a binding cord (the other side loses their next turn). The
// dealer plays fair - it knows the counts, and what its own glass shows, and nothing else. Three rounds, more candles
// each; the stake climbs a ladder with each round won (collect, or play on and risk it), cards at rounds 2 and 3; a
// round lost loses the pot. The ladder is set from tools' measure of a fair player's odds. The window is 76m-hexwand.js.
CM.HW = {
  ROUNDS: [{ candles: 2, charms: 0 }, { candles: 4, charms: 2 }, { candles: 5, charms: 3 }], maxCharms: 6,
  LADDER: [1.75, 3.6, 8.8], CARD: { 2: "common", 3: "rare" },
  CHARMS: { glass: ["Seeing-glass", "See the next charge"], unload: ["Unloading", "Throw out the next charge, and see it"], whet: ["Whetstone", "The next live hex snuffs two"], tallow: ["Tallow", "Light one of your candles again"], cord: ["Binding cord", "The other side loses their next turn"] },
};
const HW = CM.HW;
HW.Duel = class {
  constructor(round, seed) {
    const R = HW.ROUNDS[round - 1]; this.round = round; this.rnd = new CM.Random(seed); this.max = R.candles; this.you = { candles: R.candles, charms: [] }; this.dealer = { candles: R.candles, charms: [] };
    this.turn = "you"; this.stage = "play"; this.log = []; this.events = []; this.whet = false; this.known = null; this.dealerKnows = null; this.bound = { you: false, dealer: false }; this.load();
  }
  side(w) { return w === "you" ? this.you : this.dealer; }
  other(w) { return w === "you" ? "dealer" : "you"; }
  // the wand loaded: two to eight charges, at least one of each; charms dealt
  load() {
    const R = this.rnd, n = R.int(2, 8), live = Math.max(1, Math.min(n - 1, Math.round(n * (0.35 + R.next() * 0.3)))); this.charges = []; for (let i = 0; i < n; i++) this.charges.push(i < live ? 1 : 0);
    for (let i = n - 1; i > 0; i--) { const j = R.int(0, i); [this.charges[i], this.charges[j]] = [this.charges[j], this.charges[i]]; }
    this.liveLeft = live; this.dudLeft = n - live; this.known = null; this.dealerKnows = null; this.whet = false;
    const k = HW.ROUNDS[this.round - 1].charms, keys = Object.keys(HW.CHARMS);
    for (const s of [this.you, this.dealer]) for (let i = 0; i < k && s.charms.length < HW.maxCharms; i++) s.charms.push(keys[R.int(0, keys.length - 1)]);
    this.events.push({ kind: "load", live, dud: n - live });
  }
  // a charm used by whoever's turn it is
  use(who, i) {
    if (this.stage !== "play" || this.turn !== who) return null; const S = this.side(who), c = S.charms[i]; if (!c) return null;
    if (c === "tallow" && S.candles >= this.max) return null; if (c === "whet" && this.whet) return null; if (c === "cord" && this.bound[this.other(who)]) return null;
    S.charms.splice(i, 1); let seen = null;
    if (c === "glass") { seen = this.charges[0]; if (who === "you") this.known = seen; else this.dealerKnows = seen; }
    else if (c === "unload") { seen = this.charges.shift(); if (seen) this.liveLeft--; else this.dudLeft--; this.known = null; this.dealerKnows = null; }
    else if (c === "whet") this.whet = true; else if (c === "tallow") S.candles += 1; else if (c === "cord") this.bound[this.other(who)] = true;
    this.events.push({ kind: "charm", who, c, seen }); this.log.push(`${who === "you" ? "You use" : "The dealer uses"} ${HW.CHARMS[c][0].toLowerCase()}${seen !== null && seen !== undefined ? ` - ${seen ? "a live hex" : "a dud"}` : ""}.`);
    if (!this.charges.length) this.load();
    return { c, seen };
  }
  // the wand pointed and loosed
  fire(who, at) {
    if (this.stage !== "play" || this.turn !== who) return null; const live = this.charges.shift(), target = this.side(at), dmg = live ? (this.whet ? 2 : 1) : 0;
    if (live) this.liveLeft--; else this.dudLeft--; this.whet = false; this.known = null; this.dealerKnows = null;
    target.candles = Math.max(0, target.candles - dmg); this.events.push({ kind: "fire", who, at, live: !!live, dmg });
    this.log.push(`${who === "you" ? "You point" : "The dealer points"} the wand at ${at === who ? (who === "you" ? "yourself" : "itself") : at === "you" ? "you" : "the dealer"}: ${live ? `a live hex${dmg > 1 ? ", doubled" : ""}!` : "a dud."}`);
    if (target.candles <= 0) { this.stage = at === "you" ? "lost" : "won"; this.events.push({ kind: this.stage }); return { live: !!live }; }
    if (!this.charges.length) this.load();
    const keep = !live && at === who; if (!keep) { const nxt = this.other(who); if (this.bound[nxt]) { this.bound[nxt] = false; this.events.push({ kind: "bound", who: nxt }); } else this.turn = nxt; }
    return { live: !!live };
  }
  // the dealer's turn, played fairly from the counts and its own glass
  dealerAct() {
    if (this.stage !== "play" || this.turn !== "dealer") return null; const D = this.dealer, p = this.liveLeft / Math.max(1, this.liveLeft + this.dudLeft), k = this.dealerKnows;
    const has = (c) => D.charms.indexOf(c);
    if (D.candles < this.max && has("tallow") >= 0) return this.use("dealer", has("tallow"));
    if (k === null && has("glass") >= 0 && this.liveLeft && this.dudLeft) return this.use("dealer", has("glass"));
    const likelyLive = k === 1 || (k === null && p > 0.5), surelyDud = k === 0 || this.liveLeft === 0;
    if (likelyLive && !this.whet && has("whet") >= 0) return this.use("dealer", has("whet"));
    if (likelyLive && !this.bound.you && has("cord") >= 0) return this.use("dealer", has("cord"));
    if (!surelyDud && k === null && p <= 0.5 && has("unload") >= 0 && this.charges.length > 1) return this.use("dealer", has("unload"));
    return this.fire("dealer", surelyDud || (k === null && p < 0.5) ? "dealer" : "you");
  }
};
// a fair hand for the player, as the dealer plays: for the measure, and for the tests
HW.fairMove = (D) => {
  const Y = D.you, p = D.liveLeft / Math.max(1, D.liveLeft + D.dudLeft), k = D.known, has = (c) => Y.charms.indexOf(c);
  if (Y.candles < D.max && has("tallow") >= 0) return ["use", has("tallow")];
  if (k === null && has("glass") >= 0 && D.liveLeft && D.dudLeft) return ["use", has("glass")];
  const likely = k === 1 || (k === null && p > 0.5), dud = k === 0 || D.liveLeft === 0;
  if (likely && !D.whet && has("whet") >= 0) return ["use", has("whet")];
  if (likely && !D.bound.dealer && has("cord") >= 0) return ["use", has("cord")];
  return ["fire", dud || (k === null && p < 0.5) ? "you" : "dealer"];
};

Object.assign(CM.Game.prototype, {
  hwState() { return this.cgStore().hw || null; },
  hwDuel() { const S = this.hwState(); if (!S || S.stage !== "duel") return null; if (!this.hwLive || this.hwLive.key !== `${S.seed}:${S.round}`) { this.hwLive = new HW.Duel(S.round, CM.hashSeed(`${S.seed}:${S.round}`)); this.hwLive.key = `${S.seed}:${S.round}`; } return this.hwLive; },
  hwStart(bet) {
    const S0 = this.hwState(); if (S0 && (S0.stage === "duel" || S0.stage === "between")) return { error: "A duel is at the table." };
    const why = this.cgStake("hexwand", bet); if (why) return { error: why };
    const F = this.cgStore(); F.n += 1; F.hw = { stage: "duel", round: 1, bet: Math.floor(bet), pot: 0, cards: [], seed: `${this.seed}:hexwand:${F.n}` }; this.hwLive = null;
    this.saveCasino && this.saveCasino(); return F.hw;
  },
  hwSettle() {
    const S = this.hwState(), D = this.hwLive; if (!S || !D || D.stage === "play") return null;
    if (D.stage === "won") { S.pot = Math.round(S.bet * HW.LADDER[S.round - 1]); const kind = HW.CARD[S.round]; let card = null; if (kind) { card = this.cgCard(kind === "rare", `The Hexed Wand, round ${S.round} won!`, new CM.Random(CM.hashSeed(`${S.seed}:card:${S.round}`))); if (card) S.cards.push(card); }
      S.last = { round: S.round, won: true, pot: S.pot, card }; this.hwLive = null; if (S.round >= HW.ROUNDS.length) { this.cgPay("hexwand", S.pot); S.paid = S.pot; S.stage = "done"; } else S.stage = "between"; }
    else { S.last = { round: S.round, won: false, lost: S.pot }; S.pot = 0; S.paid = 0; S.stage = "done"; this.hwLive = null; }
    this.saveCasino && this.saveCasino(); this.emit("change"); return S.last;
  },
  hwCollect() { const S = this.hwState(); if (!S || S.stage !== "between") return 0; this.cgPay("hexwand", S.pot); S.paid = S.pot; S.stage = "done"; this.saveCasino && this.saveCasino(); this.emit("change"); return S.pot; },
  hwOn() { const S = this.hwState(); if (!S || S.stage !== "between") return false; S.round += 1; S.stage = "duel"; this.hwLive = null; this.saveCasino && this.saveCasino(); return true; },
});
