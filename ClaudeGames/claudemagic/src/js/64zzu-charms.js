"use strict";
// The Joker's charms (v17.6): small things from the floor that ride with the party into the world. Seven are earned -
// the capstones of the floor, for mastering a part of it - and four are bought at the counter with tickets. One is
// worn at a time; a second from Joker level 20, a third from 40. They are kept with the floor's books, from expedition
// to expedition; what they do once a floor or once an expedition starts afresh with each.
//   earned: the Loaded Die (level 10 at five of the cabinets): heroes hit 5% more often; the Joker's Wink (900 at the
//   Tavern Board): 5% more criticals; the Phoenix Card (the residents' table cleared at a 500-gold buy-in): once an
//   expedition, a hero who would fall stands at 1; the Cartographer's Ace (three collection books full): each new
//   dungeon floor is mapped (its walls) on arrival; the Night Owl (the golden carp and the whole creel book): heroes
//   learn 10% more from fights; the Gambler's Purse (the progressive jackpot won): fights pay 10% more gold; the Crown
//   of the Week (first in a Joker's Week): all of these a little - 2% to hit, 2% criticals, 3% gold.
//   bought: the Lucky Coin (1,500 tickets): once a floor, a sprung trap fails; the Rabbit's Foot (2,000): once a floor,
//   a flight from a fight can't fail; the Wanderer's Token (1,200): a rest at camp mends a quarter more; the Golden
//   Ticket (2,500): 15% more tickets on the Joker's floor.
// The window is 76zzz-charms.js; 62-combat.js asks chPhoenix when a hero would fall.
{ const CH = CM.CHARMS = { SLOTS: [[1, 1], [20, 2], [40, 3]],
    LIST: [
      { id: "die", name: "The Loaded Die", icon: "🎲", what: "Heroes hit 5% more often.", earn: "Reach level 10 at five different arcade cabinets." },
      { id: "wink", name: "The Joker's Wink", icon: "😉", what: "Heroes land 5% more critical hits.", earn: "Score 900 at the Tavern Board." },
      { id: "phoenix", name: "The Phoenix Card", icon: "🔥", what: "Once an expedition, a hero who would fall stands at 1 health instead.", earn: "Send the whole residents' table home at a 500-gold buy-in." },
      { id: "ace", name: "The Cartographer's Ace", icon: "🗺", what: "Each new dungeon floor's walls are on the map when you arrive.", earn: "Fill three of the collection books." },
      { id: "owl", name: "The Night Owl", icon: "🦉", what: "Heroes learn 10% more from fights.", earn: "Land the golden carp and fill the creel book." },
      { id: "purse", name: "The Gambler's Purse", icon: "👛", what: "Fights pay 10% more gold.", earn: "Win the progressive jackpot." },
      { id: "crown", name: "The Crown of the Week", icon: "👑", what: "A little of everything: 2% to hit, 2% more criticals, 3% more gold from fights.", earn: "Finish first in a Joker's Week." },
      { id: "coin", name: "The Lucky Coin", icon: "🪙", what: "Once a floor, a sprung trap fails.", cost: 1500 },
      { id: "rabbit", name: "The Rabbit's Foot", icon: "🐇", what: "Once a floor, running from a fight can't fail.", cost: 2000 },
      { id: "token", name: "The Wanderer's Token", icon: "🧭", what: "A rest at camp mends a quarter more.", cost: 1200 },
      { id: "ticket", name: "The Golden Ticket", icon: "🎫", what: "15% more tickets on the Joker's floor.", cost: 2500 },
    ] };
  CH.byId = Object.fromEntries(CH.LIST.map((c) => [c.id, c]));
  CH.slots = (L) => CH.SLOTS.filter(([lv]) => L >= lv).length;
  const P = CM.Game.prototype, hit0 = P.hitChance, crit0 = P.critChance, mul0 = P.jkMul, trap0 = P.springTrap, flee0 = P.flee, rest0 = P.rest, enter0 = P.enterFloor, tk0 = P.tkAdd, new0 = P.newGame;
  Object.assign(P, {
    chStore() { const F = this.cgStore(); F.charms = F.charms || { bought: {}, worn: [] }; return F.charms; },
    // earned: read from the floor's own books each time
    chEarned(id) { try { const F = this.cgStore(), B = F.boards || {};
      if (id === "die") return Object.keys(CM.ARC.reg).filter((k) => (B[k] || []).some((e) => (e.level || 0) >= 10)).length >= 5;
      if (id === "wink") return (F.fa_darts_best || 0) >= 900;
      if (id === "phoenix") return !!(this.heStore().cleared || {})[500];
      if (id === "ace") return this.bkStore ? Object.keys(this.bkStore().done).length >= 3 : false;
      if (id === "owl") { const S = this.pdStore(); return !!(S.book.golden && S.all); }
      if (id === "purse") return this.jpStore ? this.jpStore().wins.length > 0 : false;
      if (id === "crown") { if (!this.wkStore) return false; const W = this.wkStore().weeks; return Object.keys(W).some((k) => W[k].paid && this.wkPlace(k, CM.WEEK.ends(k) + 1) === 1); }
    } catch (e) { return false; } return false; },
    chOwned(id) { const C = CH.byId[id]; if (!C) return false; if (C.cost) return !!this.chStore().bought[id]; const now = Date.now(), M = this.chMemo = this.chMemo && now - this.chMemo.at < 2000 ? this.chMemo : { at: now, v: {} }; if (!(id in M.v)) M.v[id] = this.chEarned(id); return M.v[id]; },   // (asked at every blow in a fight: worked out once in a while)
    chSlots() { return CH.slots(this.jkLevel ? this.jkLevel() : 1); },
    chOn(id) { try { return !!this.cgStore && this.chStore().worn.filter((x) => this.chOwned(x)).slice(0, this.chSlots()).includes(id); } catch (e) { return false; } },   // (only what fits the slots counts)
    chWear(id) { if (!this.chOwned(id)) return { error: "You don't have that charm yet." }; const S = this.chStore(); if (S.worn.includes(id)) { S.worn = S.worn.filter((x) => x !== id); this.saveCasino && this.saveCasino(); return { off: true }; }
      if (S.worn.length >= this.chSlots()) return { error: `You can wear ${this.chSlots()} charm${this.chSlots() > 1 ? "s" : ""} at a time${this.chSlots() < 3 ? ` - another at Joker level ${CH.SLOTS[this.chSlots()][0]}` : ""}.` };
      S.worn.push(id); this.saveCasino && this.saveCasino(); return { on: true }; },
    chBuy(id) { const C = CH.byId[id]; if (!C || !C.cost) return { error: "That one can't be bought." }; const S = this.chStore(), T = this.tkStore(); if (S.bought[id]) return { error: "You have it already." }; if (T.n < C.cost) return { error: `That takes ${C.cost} tickets; you have ${T.n}.` };
      T.n -= C.cost; T.spent += C.cost; S.bought[id] = true; this.saveCasino && this.saveCasino(); return { ok: true }; },
    chUses() { this.chUse = this.chUse || { coin: null, rabbit: null, phoenix: false, mapped: [] }; return this.chUse; },
    // ---- out in the world ----
    newGame(...a) { this.chUse = null; const out = new0.apply(this, a); try { const worn = this.chStore().worn.filter((id) => this.chOwned(id)); if (worn.length) this.say(`The Joker's charms ride with you: ${worn.map((id) => CH.byId[id].name).join(", ")}.`); } catch (e) { /* no books yet */ } return out; },
    hitChance(h) { return Math.min(0.98, hit0.call(this, h) + (this.chOn("die") ? 0.05 : 0) + (this.chOn("crown") ? 0.02 : 0)); },
    critChance(h) { return Math.min(0.75, crit0.call(this, h) + (this.chOn("wink") ? 0.05 : 0) + (this.chOn("crown") ? 0.02 : 0)); },
    jkMul(kind) { return mul0.call(this, kind) + (kind === "gold" ? (this.chOn("purse") ? 0.1 : 0) + (this.chOn("crown") ? 0.03 : 0) : kind === "xp" && this.chOn("owl") ? 0.1 : 0); },
    springTrap(trap, k) { const U = this.chUses(); if (this.chOn("coin") && this.floor && U.coin !== this.floor.number) { U.coin = this.floor.number; this.say("The lucky coin goes warm in your pocket - and the trap's spring snaps, and nothing comes."); return; } return trap0.call(this, trap, k); },
    flee(sure) { const U = this.chUses(); if (!sure && this.chOn("rabbit") && this.floor && U.rabbit !== this.floor.number && !this.foes.some((m) => m.boss && m.hp > 0)) { U.rabbit = this.floor.number; const c0 = this.rnd.chance; this.rnd.chance = () => { this.rnd.chance = c0; return true; }; try { return flee0.call(this, sure); } finally { this.rnd.chance = c0; } }
      return flee0.call(this, sure); },
    chPhoenix(h) { const U = this.chUses(); if (h.hp <= 0 && this.chOn("phoenix") && !U.phoenix) { U.phoenix = true; h.hp = 1; this.say(`The Phoenix Card flares in ${h.name}'s pocket: ${h.name} does not fall.`); } },
    rest(...a) { const before = this.party.map((h) => h.hp), out = rest0.apply(this, a); if (this.chOn("token")) for (const [i, h] of this.party.entries()) if (h.hp > 0 && h.hp > before[i]) h.hp = Math.min(h.max, h.hp + Math.ceil((h.hp - before[i]) * 0.25)); return out; },
    enterFloor(number, how, at) { const out = enter0.call(this, number, how, at), fl = this.floor, U = this.chUses();
      if (fl && number >= 1 && number % 1 === 0 && this.chOn("ace") && !U.mapped.includes(number)) { U.mapped.push(number); const seen = new Set(fl.seen.map(([x, y]) => `${x},${y}`)); for (let y = 0; y < fl.grid.length; y++) for (let x = 0; x < fl.grid.length; x++) if (!seen.has(`${x},${y}`)) fl.seen.push([x, y]); this.say("The Cartographer's Ace shows you the floor's walls."); }
      return out; },
    // ---- on the floor ----
    tkAdd(n, why) { if (n > 0 && this.chOn("ticket") && !this.cgPractice) { const T = this.tkStore(); T.gtFrac = (T.gtFrac || 0) + n * 0.15; const x = Math.floor(T.gtFrac); T.gtFrac -= x; n += x; } return tk0.call(this, n, why); },
  });
}
