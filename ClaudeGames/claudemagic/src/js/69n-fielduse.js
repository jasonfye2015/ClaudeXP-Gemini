"use strict";
// The South Fields, what they're for (v19.4, UPGRADE_PLAN_14.md phase 4).
// - The market stall in the Square: the fields' produce sold at its full worth (stars and all), and three crops a day
//   in demand at half as much again; from the pack or straight out of the silo, anywhere in town.
// - The Harvest Fair's contest (the fair's week in September, or the season pinned): one entry a fair, the party's best
//   crop against three of the village's, judged on its stars and its kind; first, second and third pay renown and
//   gold, and first a blue ribbon.
// - The still in the shed: mana-blossom to a mana potion, two frost-berries to a healing potion, a moon-melon to a
//   bottle of moon-melon wine, coin-bean pods cracked for their copper (gold), the Joker's roses sold to the Joker for
//   tickets.
// - The request board asks for the fields too (a crop of three stars, a charmed crop), once they're laid out.
// - The fields count toward the renown level: a picking of ten, a giant, a fair won, the market's takings.
// The window's side: 76zzzn-fielduse.js.
{ const FU = CM.FIELDUSE = { demand: 3, demandMult: 1.5, places: [[60, 300, 1], [30, 120, 2], [15, 50, 3]] };
  const G = CM.Game.prototype, FS = CM.FIELDSEEDS;
  const produce = (it) => it && it.kind === "ingredient" && CM.CROPS[it.ingredient] && CM.CROPS[it.ingredient].price;
  FU.day = () => (CM.TOWNREQ ? CM.TOWNREQ.day() : Math.floor(Date.now() / 86400000));
  FU.demandFor = (g, day) => { const all = Object.keys(CM.CROPS).filter((c) => CM.CROPS[c].price), R = new CM.Random(CM.hashSeed(`${g.seed}:market:${day === undefined ? FU.day() : day}`)), out = []; while (out.length < FU.demand && out.length < all.length) { const c = R.pick(all); if (!out.includes(c)) out.push(c); } return out; };
  FU.price = (g, it) => Math.round((it.value || CM.CROPS[it.ingredient].price) * (FU.demandFor(g).includes(it.ingredient) ? FU.demandMult : 1));
  // the contest: the party's entry, scored; the village's three, by the year
  FU.score = (it) => (it.q || 1) * 20 + Math.min(60, Math.round(CM.CROPS[it.ingredient].price / 2)) + (CM.CROPS[it.ingredient].charmed ? 15 : 0);
  FU.rivals = (g, year) => { const R = new CM.Random(CM.hashSeed(`${g.seed}:fair:${year}`)); return [["the farmer's hand", R.int(70, 120)], ["the tavern-keeper", R.int(55, 105)], ["the priest", R.int(40, 95)]]; };
  FU.year = () => new Date().getFullYear();
  Object.assign(G, {
    marketSell(from = "pack") { if (!this.floor || this.floor.number !== 0) return { error: "The market stall is in the Square, in town." }; const F = this.fields(), src = from === "silo" ? (F.silo || []) : this.bag;
      const sold = src.filter(produce); if (!sold.length) return { error: from === "silo" ? "Nothing of the fields' in the silo." : "Nothing of the fields' in the pack." }; this.logAct && this.logAct("marketSell", from);
      let gold = 0; for (const it of sold) gold += FU.price(this, it); for (const it of sold) src.splice(src.indexOf(it), 1);
      this.gold += gold; F.marketGold = (F.marketGold || 0) + gold; this.sound && this.sound("coin"); this.say(`The market stall sells ${CM.plural(sold.length, "thing")} from the fields for ${gold} gold.`); this.saveVillage && this.saveVillage(); this.emit && this.emit("change"); return { n: sold.length, gold }; },
    fairOpen() { return Boolean(CM.festivalIs && CM.festivalIs(this, "harvest")); },
    fairEnter(i) { if (!this.fairOpen()) return { error: "The contest is at the Harvest Fair (September's fair week)." }; if (!this.floor || this.floor.number !== 0) return { error: "The contest is judged in town." };
      const F = this.fields(), year = FU.year(); if (F.fairYear === year) return { error: "One entry a fair: yours is in." }; const it = this.bag[i]; if (!produce(it)) return { error: "Enter something grown in the fields." };
      this.logAct && this.logAct("fairEnter", i); this.bag.splice(i, 1); F.fairYear = year; const mine = FU.score(it), table = FU.rivals(this, year).concat([["your party", mine]]).sort((a, b) => b[1] - a[1]), place = table.findIndex(([w]) => w === "your party") + 1;
      const P = FU.places[place - 1]; if (P) { this.village.renown = (this.village.renown || 0) + P[0]; this.gold += P[1]; } if (place === 1) { F.fairWins = (F.fairWins || 0) + 1; this.achieve && this.achieve("blueribbon"); }
      this.say(`The judges walk the tables, poke everything, and confer. ${["First", "Second", "Third", "Fourth"][place - 1]} prize for your ${it.name.toLowerCase()}${P ? ` (+${P[0]} renown, ${P[1]} gold)` : " - the village is very good at this"}.`);
      this.saveVillage && this.saveVillage(); this.emit && this.emit("change"); return { place, table, score: mine }; },
    stillWhy(crop) { if (!this.atFields()) return "The still is in the shed."; const need = { manablossom: 1, frostberry: 2, moonmelon: 1, coinbean: 1, jokerrose: 1 }[crop]; if (!need) return "The still has nothing to make of that.";
      return this.bag.filter((it) => it.kind === "ingredient" && it.ingredient === crop).length >= need ? "" : `It wants ${need} ${CM.CROPS[crop].name.toLowerCase()}.`; },
    still(crop) { const why = this.stillWhy(crop); if (why) return why; this.logAct && this.logAct("still", crop); const need = crop === "frostberry" ? 2 : 1;
      for (let k = 0; k < need; k++) this.bag.splice(this.bag.findIndex((it) => it.kind === "ingredient" && it.ingredient === crop), 1);
      if (crop === "manablossom") this.gain([{ name: "Mana Potion", kind: "mana", power: 30, value: 40 }], "fields");
      else if (crop === "frostberry") this.gain([{ name: "Healing Potion", kind: "heal", power: 45, value: 35 }], "fields");
      else if (crop === "moonmelon") this.gain([{ name: "Moon-melon wine", kind: "heal", power: 90, value: 120 }], "fields");
      else if (crop === "coinbean") { this.gold += 15; this.say("The pod cracks: fifteen copper-bright coins."); }
      else if (crop === "jokerrose") { if (this.tkAdd) this.tkAdd(30, "fields"); this.say("A boy from the Joker takes the rose and leaves thirty tickets."); }
      this.sound && this.sound("heal"); this.saveVillage && this.saveVillage(); this.emit && this.emit("change"); return ""; },
  });
  CM.ACHIEVEMENTS.blueribbon = { name: "Blue Ribbon", what: "Take first prize at the Harvest Fair's contest with something from the South Fields", title: "of the Blue Ribbon" };
  // the request board asks for the fields too
  if (CM.TOWNREQ && CM.TOWNREQ.KINDS) { const RQ = CM.TOWNREQ, open = (g) => g.fieldsLevel && g.fieldsLevel() >= 1, take = (g, test, n) => { for (let i = g.bag.length - 1; i >= 0 && n > 0; i--) if (test(g.bag[i])) { g.bag.splice(i, 1); n--; } };
    const starred = (it) => produce(it) && (it.q || 0) >= 3, charmed = (it) => produce(it) && CM.CROPS[it.ingredient].charmed;
    RQ.KINDS.push({ id: "starred", place: "the South Fields", n: 1, open, what: () => "a crop of three stars or more from the South Fields", have: (g) => g.bag.filter(starred).length, take: (g, n) => take(g, starred, n) },
      { id: "charmed", place: "the South Fields", n: 1, open, what: () => "a charmed crop (mana-blossom, frost-berries, ember pepper, moon-melon, coin-bean or the Joker's rose)", have: (g) => g.bag.filter(charmed).length, take: (g, n) => take(g, charmed, n) });
    RQ.byId.starred = RQ.KINDS[RQ.KINDS.length - 2]; RQ.byId.charmed = RQ.KINDS[RQ.KINDS.length - 1]; }
  // toward the renown level
  if (CM.RENOWNLV) CM.RENOWNLV.AREAS.push(["fields", "The South Fields", "1 a ten picked, 15 a giant, 20 a fair won, 1 a 200 gold sold", (g) => { const F = (g.village || {}).fields || {}; return Math.floor((F.picked || 0) / 10) + 15 * (F.giants || 0) + 20 * (F.fairWins || 0) + Math.floor((F.marketGold || 0) / 200); }]);
}
