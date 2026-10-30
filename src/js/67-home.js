"use strict";
// The party's own house, at the west end of the town's main lane: raised with renown like any building (CM.VILLAGE.home,
// five levels), and kept in the village store (village.home: the stash, the larder, the will). The hearth rests the
// party for nothing before a run and sends it down rested; the stash is storage of the party's own between runs,
// apart from the camps' vault - it takes only what the party walks home, and a fallen party's pack does not come to it;
// the trophy wall is what the runs brought back; the kitchen cooks for the first two floors and the larder keeps
// three rations from run to run; the door-plate carries the memorial's names and a candle lit at home sends the
// buried thing to the stash; the study is where a hero retires home and writes a will.
CM.HOME_STASH = [0, 6, 12, 20, 20, 40];                                   // things the stash holds, by the house's level
CM.HOME_LARDER = 3;
CM.RESTED_FLOORS = 5;
CM.VILLAGE.home = { name: "Your house", costs: [50, 150, 400, 800, 1500], levels: [
  "The hearth: the party rests for nothing before a run, and goes down rested (+5% to hit on floors 1 to 5); the stash holds six things between runs",
  "The trophy wall: the guardians' trophies, the named weapons and the uniques found hang here; the stash holds twelve",
  "The kitchen: meat brought home is cooked for a meal that lasts the first two floors, and a larder keeps three rations from run to run; the stash holds twenty",
  "The door-plate: the memorial's names on the door, and a candle lit at home sends what they were buried with to the stash",
  "The study: a hero may retire home and write a will - one thing from the stash starts every later run in the pack; the stash holds forty"] };
CM.TOWN_PLOTS.home.village = "home";
Object.assign(CM.Game.prototype, {
  home() { this.village = this.village || {}; const h = this.village.home = this.village.home || { stash: [], larder: 0, will: null, retired: [] }; h.stash = h.stash || []; h.retired = h.retired || []; return h; },
  homeLevel() { return this.villageLevel("home"); },
  inTown() { return Boolean(this.floor && this.floor.number === 0 && this.mode === "explore"); },
  stashRoom() { return CM.HOME_STASH[Math.min(this.homeLevel(), CM.HOME_STASH.length - 1)] - this.home().stash.length; },
  // the hearth: once a visit to the town, the party rests for nothing and goes down rested
  hearthRest() {
    if (!this.inTown()) return "The hearth is at home.";
    if (this.homeLevel() < 1) return "The house has no roof yet.";
    if (this.floor.hearthUsed) return "The fire is banked: the party has rested here already. The next run, or the next time home.";
    this.logAct("hearthRest");
    this.floor.hearthUsed = true;
    for (const m of this.alive()) { m.hp = m.max; m.mp = m.maxmp; this.cure(m, CM.CURABLE); }
    this.fed = 0; if ((this.morale || 0) < 85) this.morale = 85;
    this.buffs = this.buffs || {}; this.buffs.rested = CM.RESTED_FLOORS;
    this.sound("heal");
    this.say(`The party sleeps in its own beds and eats at its own table. Rested: a little surer of hand on the first ${CM.RESTED_FLOORS} floors.`);
    this.saveRun(); this.emit("change");
    return "";
  },
  rested() { return Boolean(this.buffs && this.buffs.rested && this.floor && this.floor.number >= 1 && this.floor.number <= this.buffs.rested); },
  // the stash: the party's own storage between runs; anything but a floor's key may be left; taking is free
  stashPut(row) {
    if (!this.inTown()) return "The stash is at home.";
    if (this.homeLevel() < 1) return "The house has no roof yet.";
    const item = this.bag[row]; if (!item) return "Pick something from your pack.";
    if (["key", "boxkey"].includes(item.kind)) return "A key belongs to its floor.";
    if (this.stashRoom() <= 0) return `The stash is full (${CM.HOME_STASH[Math.min(this.homeLevel(), CM.HOME_STASH.length - 1)]} things). Raise the house, or take something out.`;
    this.logAct("stashPut", row);
    this.bag.splice(row, 1); this.home().stash.push(item); this.saveVillage();
    this.sound("chest"); this.say(`${CM.itemName(item)} goes into the stash.`);
    this.saveRun(); this.emit("change");
    return "";
  },
  stashTake(i) {
    if (!this.inTown()) return "The stash is at home.";
    const h = this.home(); if (!h.stash[i]) return "Nothing there.";
    this.logAct("stashTake", i);
    const item = h.stash.splice(i, 1)[0]; this.saveVillage();
    this.gain([item], "stash");
    this.sound("chest"); this.say(`${CM.itemName(item)} comes out of the stash.`);
    this.saveRun(); this.emit("change");
    return "";
  },
  // the trophy wall: what the runs brought back
  homeTrophies() {
    const named = (this.compendium || {}).named || [], uniques = Object.values(CM.UNIQUES).filter((u) => (this.compendium || {})[u.name]).map((u) => u.name);
    const trophies = Object.entries(this.trophies || {}).map(([id, t]) => ({ id, name: (CM.GUARDIANS[id] || {}).name || id, date: t.date }));
    return { trophies, named, uniques, crowns: (this.fame || []).filter((e) => e.won).length, bottoms: (this.fame || []).filter((e) => e.bottom).length };
  },
  // the kitchen: meat cooked at home lasts the first two floors; the larder keeps rations from run to run
  homeCook(row) {
    if (!this.inTown()) return "The kitchen is at home.";
    if (this.homeLevel() < 3) return "The house has no kitchen yet.";
    const item = this.bag[row]; if (!item || item.kind !== "meat") return "Nothing to cook.";
    const M = CM.MEALS[item.meat]; if (!M) return "Nobody would eat that.";
    this.logAct("homeCook", row);
    this.bag.splice(row, 1); this.countUse("meal");
    this.fed = 0; this.cheer(4);
    this.meal = { kind: item.meat, floor: 2 };
    for (const h of this.party) { h.mealLuck = M.luck || 0; CM.recompute(h); }
    this.sound("heal"); this.say(`${M.name} at the party's own table: ${M.what}, for the first two floors.`);
    this.saveRun(); this.emit("change");
    return "";
  },
  larderPut(row) {
    if (!this.inTown()) return "The larder is at home.";
    if (this.homeLevel() < 3) return "The house has no kitchen yet.";
    const item = this.bag[row]; if (!item || item.kind !== "ration") return "The larder takes rations.";
    const h = this.home(); if ((h.larder || 0) >= CM.HOME_LARDER) return `The larder holds ${CM.HOME_LARDER}.`;
    this.logAct("larderPut", row);
    this.bag.splice(row, 1); h.larder = (h.larder || 0) + 1; this.saveVillage();
    this.say(`A ration on the larder's shelf (${h.larder} of ${CM.HOME_LARDER}).`); this.saveRun(); this.emit("change");
    return "";
  },
  larderTake() {
    if (!this.inTown()) return "The larder is at home.";
    const h = this.home(); if (!(h.larder > 0)) return "The larder is bare.";
    this.logAct("larderTake");
    h.larder -= 1; this.saveVillage(); this.gain([CM.ration()], "larder");
    this.say(`A ration from the larder (${h.larder} left).`); this.saveRun(); this.emit("change");
    return "";
  },
  // the door-plate: a candle lit at home sends the buried thing to the stash
  homeCandle(i) {
    if (!this.inTown()) return "The door-plate is at home.";
    if (this.homeLevel() < 4) return "The names are not on the door yet.";
    const m = (this.memorial || [])[i]; if (!m) return "No such name.";
    if (m.candle) return `A candle burns for ${m.name} already.`;
    if (this.stashRoom() <= 0 && m.buried) return "The stash is full: the candle's gift would have nowhere to go.";
    const vaults = (this.vaults || []).length;
    const note = this.lightCandle(i); if (note) return note;
    if (m.buried && (this.vaults || []).length > vaults) { const it = this.vaults.pop(); CM.store.set("vaults", this.vaults); this.home().stash.push(it); this.saveVillage(); this.say(`${CM.itemName(it)} comes home to the stash, not the vault.`); }
    else if (m.buried) { this.home().stash.push(m.buried); this.saveVillage(); this.say(`${CM.itemName(m.buried)} comes home to the stash.`); }
    this.emit("change");
    return "";
  },
  // the study: a hero retires home (as the guildhall's trainers do, without teaching), and may write a will
  retireHome(heroIndex) {
    if (!this.inTown()) return "The study is at home.";
    if (this.homeLevel() < 5) return "The house has no study yet.";
    const h = this.party[heroIndex]; if (!h || h.hp <= 0) return "Only a hero on their feet retires.";
    if (this.party.filter((p) => p.hp > 0).length <= 1) return "Someone has to go down.";
    this.logAct("retireHome", heroIndex);
    this.home().retired.push({ name: h.name, cls: h.cls, level: h.level, date: CM.today() }); this.saveVillage();
    this.party.splice(heroIndex, 1);
    this.sound("level"); this.say(`${h.name} the ${h.cls} hangs up the ${CM.baseIdOf(h.weapon || { name: "pack" })} and sits down by the window. Home for good.`);
    this.saveRun(); this.emit("change");
    return "";
  },
  writeWill(stashIndex) {
    if (!this.inTown()) return "The will is written in the study.";
    if (this.homeLevel() < 5) return "The house has no study yet.";
    const h = this.home(); if (!h.retired.length) return "A will is written by someone who has retired home.";
    const item = h.stash[stashIndex]; if (!item) return "Pick a thing from the stash.";
    if (item.props && (item.props.unique || item.props.relic)) return "A relic or a unique thing is one of a kind: it is not willed.";
    this.logAct("writeWill", stashIndex);
    h.will = JSON.parse(JSON.stringify(item)); this.saveVillage();
    this.say(`${h.retired[h.retired.length - 1].name} writes it down: ${CM.itemName(item)}, to every party that sets out from this house.`);
    this.saveRun(); this.emit("change");
    return "";
  },
});
