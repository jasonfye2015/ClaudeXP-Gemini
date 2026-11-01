"use strict";
// The floor's evenings (v16.1): four things that run across the whole of the Gilded Joker.
// - The prize counter grows and turns over: tickets spent raise it (glass cases, the velvet shelf, the Gilded Vault),
//   each step a little off every price and a shelf more of the day's specials - a few things the counter doesn't
//   always have, in short stock, changing each real day - and one everyday prize a quarter off as the day's bargain.
// - Tournament night: each real day one arcade cabinet hosts a tournament against fifteen of the village and its
//   visitors. Twenty-five gold enters for the night and buys three games; the best level reached (score breaking a tie)
//   is set against the field's; settle up and the pot (nine-tenths of the entries) pays the first three, with tickets
//   down to eighth and a card the first time the party wins each cabinet's tournament.
// - Casino quests: three at a time, asked by the residents - play so many tables, lay or win so much, reach a level
//   at a cabinet, make a board - counted from the floor's own doings; done, they pay gold, tickets and sometimes a
//   card, and another takes their place. A quest can be swapped for ten tickets.
// - The VIP back room: open to Platinum members, or to anyone with a pass from the counter (3,000 tickets). Inside, the
//   house limits go to 5,000 gold a bet (a 1,000 chip on the rail, and 1,000 and 2,500 buy-ins at the residents'
//   table) when the party asks for them, a drink on the house and twenty tickets each day, and a quiet word on the
//   night's tournament. The window is 76zzi-floor.js.
{ const FL = CM.FLOOR = {
    LEVELS: [{ name: "The prize counter", spent: 0, slots: 3, off: 0 }, { name: "Glass cases", spent: 1500, slots: 4, off: 0.05 }, { name: "The velvet shelf", spent: 5000, slots: 5, off: 0.1 }, { name: "The Gilded Vault", spent: 12000, slots: 6, off: 0.15 }],
    // [id, name, cost, what, stock, counter level needed]
    SPECIALS: [
      ["deepblade", "A deep-delve weapon", 450, "a weapon made three floors deeper than you've been", 2, 0], ["deepmail", "Deep-delve armour", 450, "armour made three floors deeper", 2, 0],
      ["tonic", "A crate of tonics", 110, "three healing potions", 3, 0], ["manabox", "A crate of mana", 110, "three mana potions", 3, 0],
      ["pack", "A card pack", 300, "three common cards", 2, 0], ["sack", "A sack of gold", 500, "60 gold", 1, 0], ["jokerbox", "The Joker's box", 180, "something from the shelves - a surprise", 3, 0],
      ["feathers", "Two phoenix feathers", 520, "brings back the fallen, twice", 1, 1], ["relic", "A gilded relic", 900, "an enchanted piece, made deeper still", 1, 2], ["rarepack", "A rare pack", 1600, "two rare Claudescryption cards", 1, 3],
    ],
    bargain: 0.25,
    TOUR: { fee: 25, tries: 3, field: 15, share: 0.9, PAY: [0.4, 0.25, 0.15], TICKETS: [12, 10, 8, 6, 5, 4, 3, 2] },
    FOLK: ["Brother Ambrose", "Sable the cardsharp", "Old Fenwick", "the Hollin twins", "a dwarf from the caves", "Maud of the mill", "a travelling knight", "Pell the pickpocket", "the guard captain", "Ysolde the weaver", "the ferryman", "a bored noble", "the cook's boy", "Grandmother Rook", "a gnome tinker", "the smith", "the farmer's hand", "the librarian"],
    GIVERS: ["the tavern-keeper", "the merchant", "the smith", "the librarian", "the priest", "the farmer's hand"],
    CLASSIC: ["slots", "roulette", "blackjack", "craps", "bigwheel", "holdem", "bingo", "pachinko"],
    VIP: { max: 5000, chip: 1000, pass: 3000, tickets: 20, buyins: [1000, 2500] },
  };
  FL.base = { max: CM.CG.max, chips: CM.CG.chips.slice() };
  FL.day = () => (CM.DAILY ? CM.DAILY.key() : new Date().toISOString().slice(0, 10));
  FL.level = (spent) => { let L = 0; FL.LEVELS.forEach((x, k) => { if (spent >= x.spent) L = k; }); return L; };
  FL.price = (cost, lvl) => Math.max(1, Math.round(cost * (1 - FL.LEVELS[lvl].off)));
  FL.arcade = () => Object.keys(CM.ARC.reg).sort();
  const name = (id) => (CM.ARC.reg[id] ? CM.ARC.reg[id].name : ((CM.CG_TABLES || []).find(([k]) => k === id) || [])[1] || id);
  FL.name = name;
  const heal = (depth) => ({ name: "Healing Potion", kind: "heal", power: 20 + depth * 3, value: 20 }), mana = (depth) => ({ name: "Mana Potion", kind: "mana", power: 12 + depth, value: 25 });
  const enchanted = (depth, R, kind) => { let it = CM.makeItem(depth, R, kind); if (CM.affix) for (let k = 0; k < 6 && it && !(it.props && it.props.rarity && it.props.rarity !== "common"); k++) it = CM.affix(CM.makeItem(depth, R, it.kind), depth + 4, R) || it; return it; };
  // the tournament's field for a day: who, how far, and a score for the tie
  FL.field = (day, table) => { const R = new CM.Random(CM.hashSeed(`tour:${day}:${table}`)), who = R.shuffle(FL.FOLK.slice()).slice(0, FL.TOUR.field);
    return who.map((w) => { const level = 1 + Math.floor(9 * Math.pow(R.next(), 1.7)); return { who: w, level, score: level * 1000 + R.int(0, 999) }; }).sort((a, b) => b.level - a.level || b.score - a.score); };
  FL.tourTable = (day) => { const list = FL.arcade(), R = new CM.Random(CM.hashSeed(`tour-table:${day}`)); let t = list[R.int(0, list.length - 1)]; const D = CM.DAILY && CM.DAILY.pick ? CM.DAILY.pick(day).table : null; if (t === D) t = list[(list.indexOf(t) + 1) % list.length]; return t; };
  // a quest for the board
  FL.quest = (R) => { const giver = R.pick(FL.GIVERS), kinds = ["play", "stake", "paid", "tickets", "level", "board", "table"], kind = kinds[R.int(0, kinds.length - 1)]; let q;
    if (kind === "play") { const n = R.int(3, 6); q = { n, text: `Try ${n} different tables.`, d: (n - 3) / 3 }; }
    else if (kind === "stake") { const n = R.pick([200, 400, 600, 1000]); q = { n, text: `Lay ${n} gold in stakes on the floor.`, d: n / 1000 }; }
    else if (kind === "paid") { const n = R.pick([150, 300, 500, 800]); q = { n, text: `Be paid ${n} gold by the tables.`, d: n / 800 }; }
    else if (kind === "tickets") { const n = R.pick([40, 70, 100, 150]); q = { n, text: `Win ${n} prize tickets.`, d: n / 150 }; }
    else if (kind === "level") { const table = R.pick(FL.arcade()), n = R.int(3, 6); q = { n, table, text: `Reach level ${n} at ${name(table)}.`, d: (n - 2) / 4 }; }
    else if (kind === "board") { const table = R.pick(CM.CLUB.BOARDS); q = { n: 1, table, text: `Put a score on the board at ${name(table)}.`, d: 0.4 }; }
    else { const table = R.pick(FL.CLASSIC), n = R.int(3, 8); q = { n, table, text: `Play ${name(table)} ${n} times.`, d: n / 10 }; }
    const d = Math.max(0, Math.min(1, q.d)); return Object.assign(q, { kind, giver, got: 0, seen: [], reward: { gold: 60 + Math.round(240 * d / 10) * 10, tickets: 15 + Math.round(45 * d), card: d >= 0.6 ? (d >= 0.95 ? "better" : "common") : null } }); };
  const st0 = CM.Game.prototype.cgStake, pay0 = CM.Game.prototype.cgPay, tk0 = CM.Game.prototype.tkAdd, rec0 = CM.Game.prototype.cgRecord, buy0 = CM.Game.prototype.tkBuy, sit0 = CM.Game.prototype.heSit;
  Object.assign(CM.Game.prototype, {
    flStore() { const F = this.cgStore(); F.fl = F.fl || { stock: {}, tour: {}, wins: {}, quests: [], qn: 0, qdone: 0, vip: { pass: false, high: false, day: "" } }; return F.fl; },
    // ---- the counter ----
    flLevel() { return FL.level(this.tkStore().spent); },
    flSpecials(day) { day = day || FL.day(); const S = this.flStore(), lvl = this.flLevel(), R = new CM.Random(CM.hashSeed(`${this.seed}:specials:${day}`)), pool = R.shuffle(FL.SPECIALS.filter((s) => s[5] <= lvl).slice()), bought = S.stock[day] || {};
      return pool.slice(0, FL.LEVELS[lvl].slots).map(([id, nm, cost, what, stock]) => ({ id, name: nm, cost: FL.price(cost, lvl), what, stock, left: stock - (bought[id] || 0) })); },
    flBargain(day) { const R = new CM.Random(CM.hashSeed(`${this.seed}:bargain:${day || FL.day()}`)); return CM.PRIZE.LIST[R.int(0, CM.PRIZE.LIST.length - 1)][0]; },
    flPrice(id, cost) { const lvl = this.flLevel(); let c = FL.price(cost, lvl); if (id === this.flBargain()) c = Math.max(1, Math.round(c * (1 - FL.bargain))); return c; },
    tkBuy(id) { const row = CM.PRIZE.LIST.find((r) => r[0] === id); if (!row) return buy0.call(this, id); const T = this.tkStore(), price = this.flPrice(id, row[3]), credit = row[3] - price;
      if (T.n < price) return { error: `That takes ${price} tickets; you have ${T.n}.` }; T.n += credit; const out = buy0.call(this, id); if (out.error) T.n -= credit; else { T.spent -= credit; out.price = price; } return out; },
    flBuy(id) { const day = FL.day(), sp = this.flSpecials(day).find((s) => s.id === id); if (!sp) return { error: "Not on the shelf today." }; if (sp.left <= 0) return { error: "Sold out until tomorrow." };
      const T = this.tkStore(); if (T.n < sp.cost) return { error: `That takes ${sp.cost} tickets; you have ${T.n}.` }; T.n -= sp.cost; T.spent += sp.cost; T.bought += 1; const S = this.flStore(); S.stock = { [day]: S.stock[day] || {} }; S.stock[day][id] = (S.stock[day][id] || 0) + 1;
      const R = new CM.Random(CM.hashSeed(`${this.seed}:special:${T.bought}`)), depth = Math.max(3, this.cwDeepest ? this.cwDeepest() : 3), out = { name: sp.name, items: [], cards: [] }; let what = id;
      if (what === "jokerbox") what = R.pick(["tonic", "manabox", "deepblade", "deepmail", "card", "feather"]);
      const give = (it) => { if (it) { this.gain([it], "casino"); out.items.push(it); } };
      if (what === "deepblade") give(CM.makeItem(depth + 3, R, "weapon")); else if (what === "deepmail") give(CM.makeItem(depth + 3, R, "armor"));
      else if (what === "tonic") for (let k = 0; k < 3; k++) give(heal(depth)); else if (what === "manabox") for (let k = 0; k < 3; k++) give(mana(depth));
      else if (what === "feathers" || what === "feather") for (let k = 0; k < (what === "feathers" ? 2 : 1); k++) give({ name: "Phoenix Feather", kind: "revive", power: 0, value: 120 });
      else if (what === "relic") give(enchanted(depth + 4, R, R.chance(0.5) ? "weapon" : "armor"));
      else if (what === "pack" || what === "rarepack" || what === "card") for (let k = 0; k < (what === "pack" ? 3 : what === "rarepack" ? 2 : 1); k++) { const c = this.cgTierCard(what === "rarepack" ? "rare" : "common", "From the prize counter's specials.", R); if (c) out.cards.push(c); }
      else if (what === "sack") { out.gold = 60; this.gold += 60; }
      this.saveCasino && this.saveCasino(); this.emit("change"); return out; },
    // ---- tournament night ----
    flTour(day) { day = day || FL.day(); const S = this.flStore(), table = FL.tourTable(day); S.tour = { [day]: S.tour[day] || { table, tries: 0, entered: false, armed: false, best: null, settled: null } }; return S.tour[day]; },
    flTourEnter() { const N = this.flTour(); if (N.settled) return { error: "Tonight's tournament is settled." }; if (N.armed) return { error: "Your entry is waiting - go and play." };
      if (N.tries >= FL.TOUR.tries) return { error: "That's your three games for the night." }; if (!N.entered) { const why = this.cgStake("tournament", FL.TOUR.fee); if (why) return { error: why }; N.entered = true; }
      N.armed = true; this.saveCasino && this.saveCasino(); return { table: N.table, game: N.tries + 1 }; },
    flStand(N) { N = N || this.flTour(); const field = FL.field(FL.day(), N.table).map((e) => Object.assign({}, e)); if (N.best) field.push({ who: "You", level: N.best.level, score: N.best.score, you: true });
      return field.sort((a, b) => b.level - a.level || (b.you ? 1 : 0) - (a.you ? 1 : 0) || b.score - a.score); },
    flTourSettle() { const N = this.flTour(), S = this.flStore(); if (N.settled) return N.settled; if (!N.best) return { error: "Play a tournament game first." }; if (N.armed) return { error: "Your entry is waiting - go and play." };
      const stand = this.flStand(N), place = stand.findIndex((e) => e.you) + 1, pool = Math.floor((FL.TOUR.field + 1) * FL.TOUR.fee * FL.TOUR.share), gold = place <= 3 ? Math.floor(pool * FL.TOUR.PAY[place - 1]) : 0, tickets = FL.TOUR.TICKETS[place - 1] || 0, out = { place, gold, tickets, of: stand.length };
      if (gold) this.cgPay("tournament", gold); if (tickets && this.tkAdd) this.tkAdd(tickets, "tournament");
      if (place === 1 && !S.wins[N.table]) { S.wins[N.table] = true; out.card = this.cgTierCard("rare", `Tournament night: first at ${name(N.table)}!`, new CM.Random(CM.hashSeed(`${this.seed}:tour:card:${N.table}`))); }
      N.settled = out; this.saveCasino && this.saveCasino(); this.emit("change"); return out; },
    // ---- quests ----
    flQuests() { const S = this.flStore(); while (S.quests.length < 3) { let q; for (let k = 0; k < 8; k++) { S.qn += 1; q = FL.quest(new CM.Random(CM.hashSeed(`${this.seed}:quest:${S.qn}`))); if (!S.quests.some((o) => o.kind === q.kind)) break; } S.quests.push(q); } return S.quests; },
    flQuestTick(kind, amount, table, level) { const S = this.flStore(); if (!S.quests.length) return; for (const q of S.quests) { if (q.got >= q.n) continue;
        if (q.kind === kind && kind === "play") { if (!q.seen.includes(table)) { q.seen.push(table); q.got = q.seen.length; } }
        else if (q.kind === kind && (kind === "stake" || kind === "paid" || kind === "tickets")) q.got = Math.min(q.n, q.got + amount);
        else if (q.kind === kind && q.table === table) { if (kind === "level") q.got = Math.max(q.got, Math.min(q.n, level || 0)); else if (kind === "board") q.got = 1; else if (kind === "table") q.got = Math.min(q.n, q.got + 1); } } },
    flQuestCollect(i) { const S = this.flStore(), q = S.quests[i]; if (!q) return { error: "No such quest." }; if (q.got < q.n) return { error: "Not done yet." }; S.quests.splice(i, 1); S.qdone += 1;
      const out = { text: q.text, giver: q.giver, gold: q.reward.gold, tickets: q.reward.tickets }; this.gold += q.reward.gold; if (this.tkAdd) tk0.call(this, q.reward.tickets, "quests");
      if (q.reward.card) out.card = this.cgTierCard(q.reward.card, `A quest for ${q.giver}, done.`, new CM.Random(CM.hashSeed(`${this.seed}:questcard:${S.qdone}`))); this.flQuests(); this.saveCasino && this.saveCasino(); this.emit("change"); return out; },
    flQuestSwap(i) { const S = this.flStore(), T = this.tkStore(); if (!S.quests[i]) return { error: "No such quest." }; if (T.n < 10) return { error: "Swapping a quest takes 10 tickets." }; T.n -= 10; T.spent += 10; S.quests.splice(i, 1); this.flQuests(); this.saveCasino && this.saveCasino(); return { ok: true }; },
    // ---- the VIP room ----
    vipUnlocked() { const F = this.cgStore(); return ((F.loyalty || {}).done || 0) >= 10 || this.flStore().vip.pass; },
    vipOn() { return this.vipUnlocked() && this.flStore().vip.high; },
    vipApply() { const on = this.vipOn(); CM.CG.max = on ? FL.VIP.max : FL.base.max; CM.CG.chips = on ? FL.base.chips.concat([FL.VIP.chip]) : FL.base.chips.slice(); return on; },
    vipSet(high) { if (!this.vipUnlocked()) return "The back room is for Platinum members and pass-holders."; this.flStore().vip.high = !!high; this.vipApply(); this.saveCasino && this.saveCasino(); return ""; },
    vipBuyPass() { const V = this.flStore().vip, T = this.tkStore(); if (this.vipUnlocked()) return { error: "You're already welcome in the back room." }; if (T.n < FL.VIP.pass) return { error: `A pass takes ${FL.VIP.pass} tickets; you have ${T.n}.` }; T.n -= FL.VIP.pass; T.spent += FL.VIP.pass; V.pass = true; this.saveCasino && this.saveCasino(); return { ok: true }; },
    vipDaily() { const V = this.flStore().vip, day = FL.day(); if (!this.vipUnlocked()) return { error: "Members only." }; if (V.day === day) return { error: "The bar's already sent your drink over today." }; V.day = day;
      const depth = Math.max(3, this.cwDeepest ? this.cwDeepest() : 3), it = heal(depth); it.name = "The Joker's Cordial"; this.gain([it], "casino"); if (this.tkAdd) tk0.call(this, FL.VIP.tickets, "vip"); this.saveCasino && this.saveCasino(); this.emit("change"); return { item: it, tickets: FL.VIP.tickets }; },
    // ---- the floor's doings, counted ----
    cgStake(game, bet) { const old = CM.CG.max; if (this.vipOn()) CM.CG.max = FL.VIP.max; let why; try { why = st0.call(this, game, bet); } finally { CM.CG.max = old; } if (!why && game !== "tournament") { this.flQuestTick("play", 0, game); this.flQuestTick("stake", Math.floor(bet), game); this.flQuestTick("table", 1, game); } return why; },
    cgPay(game, amount) { const n = pay0.call(this, game, amount); if (n > 0) { this.flQuestTick("paid", n, game); if (!(this.cgStore().wagered || {})[game]) this.flQuestTick("play", 0, game); } return n; },
    tkAdd(n, why) { const k = tk0.call(this, n, why); if (k > 0) this.flQuestTick("tickets", k, why); return k; },
    cgRecord(table, score, level) { const r = rec0.call(this, table, score, level); if (level) this.flQuestTick("level", 0, table, level); if (r > 0) this.flQuestTick("board", 1, table);
      const N = this.flStore().tour[FL.day()]; if (N && N.armed && N.table === table) { N.armed = false; N.tries += 1; const e = { level: level || 0, score: Math.floor(score || 0) }; if (!N.best || e.level > N.best.level || (e.level === N.best.level && e.score > N.best.score)) N.best = e; } return r; },
    heSit(buyin) { if (FL.VIP.buyins.includes(buyin) && this.vipOn()) { const B = CM.HE.BUYINS; B.push(buyin); try { return sit0.call(this, buyin); } finally { B.splice(B.indexOf(buyin), 1); } } return sit0.call(this, buyin); },
  });
}
