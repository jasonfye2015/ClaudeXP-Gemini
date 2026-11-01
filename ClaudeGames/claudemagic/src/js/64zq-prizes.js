"use strict";
// The Prize Counter (the forty-first big update - v15.4): every table on the Gilded Joker's floor hands out prize
// tokens, and a counter by the cashier's cage trades them for prizes. Tokens come in varying amounts: with every stake
// laid (one for each thirty gold staked), with the gold a free table pays (one for each fifty - the tables that take
// stakes give tokens for the stake, not the win), for each blind beaten at Claudeatro, and for a place on a high-score board (more for a record).
// Odd gold carries over, so small stakes add up. The counter sells pouches of gold, potions, gear (made for the party's
// depth, the dearest enchanted) and Claudescryption cards; gold is the poorest buy on purpose, so tokens cannot be
// turned back into the stakes that made them: a token buys at most an eighth of a gold, and even the fairest table
// (99.5% back) loses more than its tokens can buy back. The window is 76zh-prizes.js.
CM.PRIZE = {
  perStake: 30, perPay: 50, bestReturn: 0.995, blind: 2, boss: 5, board: 3, record: 10,
  // [id, shelf, name, cost, what it is]
  LIST: [
    ["pouch", "gold", "A pouch of gold", 80, "10 gold"], ["purse", "gold", "A purse of gold", 400, "50 gold"], ["chest", "gold", "A strongbox of gold", 2000, "250 gold"],
    ["torch", "potions", "A torch", 15, "lights the way"], ["antidote", "potions", "An antidote", 30, "cures poison"], ["heal", "potions", "A healing potion", 40, "heals, more for a deeper party"],
    ["mana", "potions", "A mana potion", 40, "restores mana"], ["feather", "potions", "A phoenix feather", 300, "brings a fallen hero back"],
    ["mystery", "gear", "A mystery parcel", 150, "any item, made for your depth"], ["weapon", "gear", "A weapon", 260, "made for your depth"], ["armor", "gear", "A suit of armour", 260, "made for your depth"],
    ["shield", "gear", "A shield", 200, "made for your depth"], ["helm", "gear", "A helm", 180, "made for your depth"], ["enchanted", "gear", "An enchanted piece", 650, "a weapon or armour, enchanted"],
    ["card1", "cards", "A common card", 120, "a Claudescryption card"], ["card2", "cards", "A stronger card", 350, "a stronger common card"], ["card3", "cards", "A rare card", 900, "a rare Claudescryption card"],
  ],
  SHELVES: [["gold", "Gold"], ["potions", "Potions"], ["gear", "Gear"], ["cards", "Cards"]],
};
const PRIZE = CM.PRIZE;
{ const stake1 = CM.Game.prototype.cgStake, pay1 = CM.Game.prototype.cgPay, rec1 = CM.Game.prototype.cgRecord, deal1 = CM.Game.prototype.casinoDeal, after1 = CM.Game.prototype.casinoAfterHand;
  Object.assign(CM.Game.prototype, {
    tkStore() { const F = this.cgStore(); F.tk = F.tk || { n: 0, earned: 0, spent: 0, stakeGold: 0, payGold: 0, bought: 0, by: {} }; return F.tk; },
    tkAdd(n, why) { if (!(n > 0)) return 0; const T = this.tkStore(); T.n += n; T.earned += n; if (why) T.by[why] = (T.by[why] || 0) + n; return n; },
    // gold counted toward tokens, the odd part kept for next time
    tkFromGold(key, amount, per, why) { const T = this.tkStore(); T[key] = (T[key] || 0) + amount; const n = Math.floor(T[key] / per); T[key] -= n * per; return this.tkAdd(n, why); },
    cgStake(game, bet) { const why = stake1.call(this, game, bet); if (!why) this.tkFromGold("stakeGold", Math.floor(bet), PRIZE.perStake, game); return why; },
    cgPay(game, amount) { const n = pay1.call(this, game, amount); if (n > 0 && !(this.cgStore().wagered || {})[game]) this.tkFromGold("payGold", n, PRIZE.perPay, game); return n; },
    cgRecord(table, score, level) { const F = this.cgStore(), before = F.records || 0, r = rec1.call(this, table, score, level); if (r > 0) this.tkAdd((F.records || 0) > before ? PRIZE.record : PRIZE.board, table); return r; },
    casinoDeal(deck, wager) { const r = deal1.call(this, deck, wager); if (!r && wager > 0) this.tkFromGold("stakeGold", Math.floor(wager), PRIZE.perStake, "claudeatro"); return r; },
    casinoAfterHand(run, res) { const was = run.paidFor, out = after1.call(this, run, res); if (run.paidFor && run.paidFor !== was && run.lastBlind) { this.tkAdd(run.lastBlind.kind === "boss" ? PRIZE.boss : PRIZE.blind, "claudeatro"); } return out; },
    // a prize bought: the tokens taken, the prize made real
    tkBuy(id) {
      const row = PRIZE.LIST.find((r) => r[0] === id); if (!row) return { error: "No such prize." }; const T = this.tkStore(), cost = row[3];
      if (T.n < cost) return { error: `That takes ${cost} tokens; you have ${T.n}.` };
      T.n -= cost; T.spent += cost; T.bought += 1; const R = new CM.Random(CM.hashSeed(`${this.seed}:prize:${T.bought}`)), depth = Math.max(3, this.cwDeepest ? this.cwDeepest() : 3), out = { name: row[2] };
      if (id === "pouch" || id === "purse" || id === "chest") { out.gold = { pouch: 10, purse: 50, chest: 250 }[id]; this.gold += out.gold; }
      else if (id === "card1" || id === "card2" || id === "card3") out.card = this.cgTierCard({ card1: "common", card2: "better", card3: "rare" }[id], "Bought at the Gilded Joker's prize counter.", R);
      else { let it;
        if (id === "torch") it = CM.torch(); else if (id === "antidote") it = CM.antidote(); else if (id === "heal") it = { name: "Healing Potion", kind: "heal", power: 20 + depth * 3, value: 20 };
        else if (id === "mana") it = { name: "Mana Potion", kind: "mana", power: 12 + depth, value: 25 }; else if (id === "feather") it = { name: "Phoenix Feather", kind: "revive", power: 0, value: 120 };
        else if (id === "mystery") it = CM.makeItem(depth, R); else if (id === "enchanted") { it = CM.makeItem(depth + 2, R, R.chance(0.5) ? "weapon" : "armor"); if (CM.affix) { for (let k = 0; k < 6 && it && !(it.props && it.props.rarity && it.props.rarity !== "common"); k++) it = CM.affix(CM.makeItem(depth + 2, R, it.kind), depth + 6, R) || it; } }
        else it = CM.makeItem(depth, R, id);
        if (it) { this.gain([it], "casino"); out.item = it; } }
      this.saveCasino && this.saveCasino(); this.emit && this.emit("change"); return out;
    },
  });
}
