"use strict";
// The farm in the First Glade (the eighth big update, phase 4): raised with renown like a building (CM.VILLAGE.farm,
// five levels - a field, an orchard, a mill and a farmhand, hens, a cow and a byre) and kept in the village store
// (village.farm). Rows are sown with seed in the crop's season, grow a stage every dawn the party sees (the clock's
// day: a run that sleeps at the camps grows the field, one that reads Homecoming and sleeps at home grows it too),
// are cut at the fourth stage, and rot three dawns past ripe. Crows take a ripe row in ten unless a scarecrow stands.
// The farm's things are ingredients with a freshness (eggs and milk a week). The town's beds stay the alchemist's.
//
//   CM.season(game)                   -> "spring" | "summer" | "autumn" | "winter" (pinned to the run from the real date)
//   CM.CROPS, CM.FOODS                -> what is sown, and what the farm gives
//   game.farm() / game.farmDawns()    -> the state; the dawns since the last look, applied
//   game.sow(i, row) / game.cut(i)    -> a row sown from a seed in the pack; a ripe row cut into the pack (and a seed back)
//   game.collectFarm() ...            -> the store into the pack; feedCow, setScarecrow, hireHand, orderHand, storeSeeds
CM.SEASONS = ["spring", "summer", "autumn", "winter"];
CM.seasonOfDate = (d) => { const m = (d || new Date()).getMonth(); return m >= 2 && m <= 4 ? "spring" : m >= 5 && m <= 7 ? "summer" : m >= 8 && m <= 10 ? "autumn" : "winter"; };
CM.season = (game) => (game && game.season) || CM.seasonOfDate();
CM.VILLAGE.farm = { name: "The farm in the First Glade", costs: [50, 90, 150, 220, 300], levels: [
  "A field in the Wood's first glade: four rows, sown with seed from the Merchant's House, grown a stage every dawn the party sees",
  "An orchard: apples and pears in autumn",
  "A mill (flour and malt, a sack a dawn) and a farmhand for hire, who sows and cuts while the party is away",
  "Hens: an egg a dawn each, three of them, and two more rows",
  "A cow and a byre: milk a dawn for a cabbage a week, and the Wood's venison twice a season",
] };
CM.CROPS = {
  wheat: { name: "Wheat", sow: ["spring"], yields: 3, mill: "flour" },
  barley: { name: "Barley", sow: ["spring"], yields: 3, mill: "malt" },
  beans: { name: "Beans", sow: ["spring", "autumn"], yields: 4 },
  cabbage: { name: "Cabbage", sow: ["spring", "autumn"], yields: 2 },
  turnip: { name: "Turnip", sow: ["spring", "summer", "autumn"], yields: 3 },
  hops: { name: "Hops", sow: ["summer"], yields: 2 },
};
CM.FOODS = { wheat: { name: "Wheat" }, barley: { name: "Barley" }, beans: { name: "Beans" }, cabbage: { name: "Cabbage" }, turnip: { name: "Turnip" }, hops: { name: "Hops" },
  apple: { name: "Apple" }, pear: { name: "Pear" }, flour: { name: "Flour" }, malt: { name: "Malt" }, egg: { name: "Egg", keeps: 7 }, milk: { name: "Milk", keeps: 7 } };
for (const [id, F] of Object.entries(CM.FOODS)) { CM.INGREDIENTS[id] = { name: F.name, band: -1, food: true }; CM.BASES[F.name] = { id: F.name, kind: "ingredient", slot: null, tier: 0, group: "ingredient" }; }
CM.food = (id, spoils) => { const it = CM.ingredient(id); it.value = 8; if (spoils !== undefined) it.spoils = spoils; return it; };
CM.seed = (crop) => ({ name: `${CM.CROPS[crop].name} seed`, kind: "seed", crop, power: 0, value: 10 });
for (const crop of Object.keys(CM.CROPS)) CM.BASES[`${CM.CROPS[crop].name} seed`] = { id: `${CM.CROPS[crop].name} seed`, kind: "seed", slot: null, tier: 0, group: "stuff" };
CM.FARM = { stages: 4, rotAfter: 3, crows: 10, hens: 3, cowWeek: 7, handSeason: 90, handGold: 30, venisonEvery: 45, rows: [0, 4, 4, 4, 6, 6], eggsMost: 21 };
CM.HOW_FOUND.farm = "from the farm";
CM.FARM_AT = [25, 14];                                                   // the farm's gate, in the First Glade (set when the Wood is made)
{ const mw = CM.makeWood; CM.makeWood = function (seed) { const fl = mw(seed); if (!Object.values(fl.things).some((t) => t.type === "farm")) { const k = [CM.FARM_AT, [25, 15], [26, 14], [24, 15], [26, 16], [24, 14]].map((c) => c.join(",")).find((c) => !fl.things[c] && !fl.features[c] && fl.grid[Number(c.split(",")[1])][Number(c.split(",")[0])] === 0); if (k) fl.things[k] = { type: "farm" }; } return fl; }; }   // (placed last, by no die: the Wood's other things stand where they stood)
Object.assign(CM.Game.prototype, {
  farm() { this.village = this.village || {}; const F = this.village.farm = this.village.farm || { rows: [], store: [], seeds: {}, days: 0, scarecrow: false, cowFed: 0, hand: 0, order: null, venison: 0, notes: [] }; F.rows = F.rows || []; F.store = F.store || []; F.seeds = F.seeds || {}; F.notes = F.notes || []; return F; },
  farmRows() { return CM.FARM.rows[Math.min(this.villageLevel("farm"), CM.FARM.rows.length - 1)]; },
  atFarm() { const fl = this.floor, t = fl && fl.things[fl.pos.join(",")]; return Boolean(t && t.type === "farm"); },
  canSow(crop) { return CM.CROPS[crop] && CM.CROPS[crop].sow.includes(CM.season(this)); },
  // the dawns since the last look at the farm, applied one at a time
  farmDawns() {
    const day = CM.dayOf(this), n = day - (this.farmDay || 0); this.farmDay = day;
    if (n <= 0 || this.villageLevel("farm") < 1) return 0;
    for (let i = 0; i < n; i++) this.farmDawn();
    for (let i = this.bag.length - 1; i >= 0; i--) if (this.bag[i].spoils !== undefined && this.bag[i].spoils <= this.farm().days) { this.say(`The ${this.bag[i].name.toLowerCase()} has gone off.`); this.bag.splice(i, 1); }
    this.saveVillage(); return n;
  },
  farmDawn() {
    const F = this.farm(), L = this.villageLevel("farm"), season = CM.season(this), notes = []; F.days += 1;
    const roll = (what, n) => CM.hashSeed(`${this.seed}:farm:${what}:${F.days}`) % n;
    const rows = this.farmRows(); while (F.rows.length < rows) F.rows.push(null); if (F.rows.length > rows) F.rows.length = rows;
    F.rows.forEach((r, i) => {
      if (!r) return;
      if (r.stage < CM.FARM.stages) { if (season !== "winter") r.stage += 1; if (r.stage >= CM.FARM.stages && !F.scarecrow && roll(`crows:${i}`, CM.FARM.crows) === 0) { F.rows[i] = null; notes.push(`crows took the ${CM.CROPS[r.crop].name.toLowerCase()} in row ${i + 1}`); } }
      else { r.ripeFor = (r.ripeFor || 0) + 1; if (r.ripeFor > CM.FARM.rotAfter) { F.rows[i] = null; notes.push(`the ${CM.CROPS[r.crop].name.toLowerCase()} in row ${i + 1} rotted in the field`); } }
    });
    if (L >= 2 && season === "autumn" && roll("orchard", 2) === 0) { const id = roll("fruit", 3) === 0 ? "pear" : "apple"; F.store.push({ id, day: F.days }, { id, day: F.days }); notes.push(`the orchard dropped two ${id}s`); }
    if (L >= 3) { const grain = F.store.find((s) => s.id === "wheat" || s.id === "barley"); if (grain) { F.store.splice(F.store.indexOf(grain), 1); F.store.push({ id: CM.CROPS[grain.id].mill, day: F.days }); } }
    for (let i = F.store.length - 1; i >= 0; i--) { const keeps = (CM.FOODS[F.store[i].id] || {}).keeps; if (keeps && F.days - F.store[i].day >= keeps) F.store.splice(i, 1); }   // (what has gone off, first)
    if (L >= 4 && F.store.filter((s) => s.id === "egg").length < CM.FARM.eggsMost) for (let i = 0; i < CM.FARM.hens; i++) F.store.push({ id: "egg", day: F.days });
    if (L >= 5 && F.cowFed >= F.days) F.store.push({ id: "milk", day: F.days });
    if (L >= 5 && F.days - (F.venison || 0) >= CM.FARM.venisonEvery) { F.venison = F.days; F.store.push({ id: "venison", day: F.days }, { id: "venison", day: F.days }); notes.push("the byre gave two of venison"); }
    if (L >= 3 && F.hand > F.days) {                                     // the farmhand: cuts what is ripe into the store, sows what was ordered
      F.rows.forEach((r, i) => { if (r && r.stage >= CM.FARM.stages) { for (let k = 0; k < CM.CROPS[r.crop].yields; k++) F.store.push({ id: r.crop, day: F.days }); F.seeds[r.crop] = (F.seeds[r.crop] || 0) + 1; F.rows[i] = null; notes.push(`the farmhand cut the ${CM.CROPS[r.crop].name.toLowerCase()} in row ${i + 1}`); } });
      if (F.order && this.canSow(F.order)) F.rows.forEach((r, i) => { if (!r && (F.seeds[F.order] || 0) > 0) { F.seeds[F.order] -= 1; F.rows[i] = { crop: F.order, stage: 0 }; notes.push(`the farmhand sowed ${CM.CROPS[F.order].name.toLowerCase()} in row ${i + 1}`); } });
    }
    if (notes.length) F.notes = F.notes.concat(notes).slice(-12);
  },
  // the work at the farm: sow, cut, collect, feed, the scarecrow, the farmhand
  sow(i, row) {
    if (!this.atFarm()) return "The rows are at the farm, in the Wood's first glade.";
    if (this.villageLevel("farm") < 1) return "A fallow field: the farm is raised at the town's board, with renown.";
    this.farmDawns(); const F = this.farm(); while (F.rows.length < this.farmRows()) F.rows.push(null);
    if (i < 0 || i >= F.rows.length) return "No such row."; if (F.rows[i]) return `Row ${i + 1} has ${CM.CROPS[F.rows[i].crop].name.toLowerCase()} in it.`;
    const seed = this.bag[row]; if (!seed || seed.kind !== "seed") return "Pick a seed from the pack.";
    if (!this.canSow(seed.crop)) return `${CM.CROPS[seed.crop].name} is not sown in ${CM.season(this)}: ${CM.CROPS[seed.crop].sow.join(" or ")}.`;
    this.logAct("sow", i, row);
    this.bag.splice(row, 1); F.rows[i] = { crop: seed.crop, stage: 0 }; this.tally.sown = (this.tally.sown || 0) + 1;
    this.say(`${CM.CROPS[seed.crop].name} sown in row ${i + 1}; it ripens in ${CM.FARM.stages} dawns.`); this.saveVillage(); this.saveRun(); this.emit("change"); return "";
  },
  cut(i) {
    if (!this.atFarm()) return "The rows are at the farm, in the Wood's first glade.";
    this.farmDawns(); const F = this.farm(), r = F.rows[i]; if (!r) return "Nothing grows in that row.";
    if (r.stage < CM.FARM.stages) return `The ${CM.CROPS[r.crop].name.toLowerCase()} in row ${i + 1} is ${CM.FARM.stages - r.stage} ${CM.FARM.stages - r.stage === 1 ? "dawn" : "dawns"} from ripe.`;
    this.logAct("cut", i);
    const got = []; for (let k = 0; k < CM.CROPS[r.crop].yields; k++) got.push(CM.food(r.crop)); got.push(CM.seed(r.crop)); this.gain(got, "farm"); F.rows[i] = null; this.tally.cut = (this.tally.cut || 0) + 1;
    this.say(`Row ${i + 1} cut: ${CM.plural(CM.CROPS[r.crop].yields, CM.CROPS[r.crop].name.toLowerCase())}, and seed kept back.`); this.saveVillage(); this.saveRun(); this.emit("change"); return "";
  },
  collectFarm() {
    if (!this.atFarm()) return "The store is at the farm.";
    this.farmDawns(); const F = this.farm(); if (!F.store.length) return "The store is bare.";
    this.logAct("collectFarm");
    const got = F.store.map((s) => (s.id === "venison" ? CM.meat("Deer") : CM.food(s.id, CM.FOODS[s.id] && CM.FOODS[s.id].keeps ? s.day + CM.FOODS[s.id].keeps : undefined))); F.store = [];
    this.gain(got, "farm"); this.say(`From the store: ${got.map((g) => g.name.toLowerCase()).join(", ")}.`); this.saveVillage(); this.saveRun(); this.emit("change"); return "";
  },
  feedCow() {
    if (!this.atFarm()) return "The cow is at the farm."; if (this.villageLevel("farm") < 5) return "There is no cow yet: the farm's fifth level.";
    const F = this.farm(), row = this.bag.findIndex((i) => i.kind === "ingredient" && i.ingredient === "cabbage"); if (row < 0) return "The cow wants a cabbage.";
    this.logAct("feedCow"); this.bag.splice(row, 1); F.cowFed = Math.max(F.cowFed || 0, F.days) + CM.FARM.cowWeek; this.say("The cow takes the cabbage, and will give milk a dawn for the week."); this.saveVillage(); this.saveRun(); this.emit("change"); return "";
  },
  setScarecrow() {
    if (!this.atFarm()) return "The scarecrow stands at the farm."; const F = this.farm(); if (F.scarecrow) return "A scarecrow stands already.";
    const wood = this.bag.findIndex((i) => i.kind === "ingredient" && i.ingredient === "deadwood"), coat = this.bag.map((it, i) => [it, i]).filter(([it]) => it.kind === "armor" && !(it.props && (it.props.unique || it.props.relic)) && (it.props || {}).weight === "light").sort((a, b) => (a[0].value || 0) - (b[0].value || 0))[0];
    if (wood < 0 || !coat) return "A scarecrow wants a deadwood and an old tunic (any light armour in the pack).";
    this.logAct("setScarecrow"); this.bag.splice(Math.max(wood, coat[1]), 1); this.bag.splice(Math.min(wood, coat[1]), 1); F.scarecrow = true; this.say(`${coat[0].name} on a deadwood pole: the crows think better of it.`); this.saveVillage(); this.saveRun(); this.emit("change"); return "";
  },
  hireHand() {
    if (!this.atFarm()) return "The farmhand is hired at the farm."; if (this.villageLevel("farm") < 3) return "A farmhand comes with the mill: the farm's third level.";
    const F = this.farm(); if (F.hand > F.days) return `The farmhand is paid for ${F.hand - F.days} more dawns.`; if (this.gold < CM.FARM.handGold) return `A farmhand is ${CM.FARM.handGold} gold a season.`;
    this.logAct("hireHand"); this.gold -= CM.FARM.handGold; this.spend("farm", CM.FARM.handGold); F.hand = F.days + CM.FARM.handSeason; this.say(`A farmhand for the season: he will cut what ripens and sow what you tell him, from the farm's own seed.`); this.saveVillage(); this.saveRun(); this.emit("change"); return "";
  },
  orderHand(crop) {
    if (!this.atFarm()) return "The farmhand is told at the farm."; const F = this.farm(); if (crop !== null && !CM.CROPS[crop]) return "No such crop.";
    this.logAct("orderHand", crop); F.order = crop; this.say(crop ? `The farmhand will sow ${CM.CROPS[crop].name.toLowerCase()} in every empty row, in its season.` : "The farmhand will sow nothing."); this.saveVillage(); this.saveRun(); return "";
  },
  storeSeeds() {
    if (!this.atFarm()) return "The seed is stored at the farm."; const F = this.farm(), rows = this.bag.map((it, i) => [it, i]).filter(([it]) => it.kind === "seed"); if (!rows.length) return "No seed in the pack.";
    this.logAct("storeSeeds"); for (const [it, i] of rows.reverse()) { this.bag.splice(i, 1); F.seeds[it.crop] = (F.seeds[it.crop] || 0) + 1; } this.say(`${CM.plural(rows.length, "packet")} of seed into the farm's chest, for the farmhand.`); this.saveVillage(); this.saveRun(); this.emit("change"); return "";
  },
  // the bot's visit: cut what is ripe, collect, sow what it can, feed the cow
  tendFarmAuto() {
    if (!this.atFarm() || this.villageLevel("farm") < 1) return 0; let did = 0; this.farmDawns(); const F = this.farm();
    F.rows.forEach((r, i) => { if (r && r.stage >= CM.FARM.stages && this.cut(i) === "") did++; });
    if (F.store.length && this.collectFarm() === "") did++;
    for (let i = 0; i < this.farmRows(); i++) { if (F.rows[i]) continue; const row = this.bag.findIndex((it) => it.kind === "seed" && this.canSow(it.crop)); if (row < 0) break; if (this.sow(i, row) === "") did++; }
    if (this.villageLevel("farm") >= 5 && F.cowFed <= F.days && this.feedCow() === "") did++;
    if (this.villageLevel("farm") >= 3 && F.hand <= F.days && this.gold >= CM.FARM.handGold + 100 && this.hireHand() === "") { did++; const crop = Object.keys(CM.CROPS).find((c) => this.canSow(c)); if (crop) this.orderHand(crop); this.storeSeeds(); }
    return did;
  },
  farmWants() {                                                          // is there anything at the farm for the bot: ripe rows, a store, or seed for an empty row
    if (this.villageLevel("farm") < 1) return false; const F = this.farm(), rows = this.farmRows();
    return F.rows.some((r) => r && r.stage >= CM.FARM.stages) || F.store.length > 0 || (F.rows.filter(Boolean).length < rows && this.bag.some((it) => it.kind === "seed" && this.canSow(it.crop)));
  },
});
