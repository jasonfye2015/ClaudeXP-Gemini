"use strict";
// The surface: a village between runs that grows with what the party brings up. Renown is the currency (a run's
// floors, guardians, crown, achievements, the week's seed); it never buys power in the dungeon directly - the
// guildhall's trainers are the one exception, and capped at a boon. Four buildings, four levels each (CM.VILLAGE);
// contracts posted at the guildhall from the week's seed (CM.CONTRACTS). Kept between runs (CM.store "village").
CM.VILLAGE = {
  guildhall: { name: "The Guildhall", costs: [30, 80, 160, 200], levels: [
    "A hero who comes home may retire here as a trainer: every new hero of their calling sets out with the trainer's first boon",
    "The vault holds three things", "The tavern's third recruit is someone the party rescued in a run before", "The vault holds five things"] },
  merchant: { name: "The Merchant's House", costs: [30, 80, 160, 200], levels: [
    "The camps' merchant stocks Greater Healing Potions", "...and an oil of each kind", "...and one rare thing a camp", "...and sells everything a fifth cheaper"] },
  library: { name: "The Library", costs: [30, 80, 160, 280], levels: [
    "Scholarship: every kind fully learned (met and slain three times, a weakness found) takes 1% more from every blow",
    "...2% more", "...3% more", "The library knows every kind's weakness the moment it is met"] },
  shrine: { name: "The Shrine of the Fallen", costs: [15, 40, 100, 200], levels: [
    "Light a candle for a hero laid to rest (10 renown): what they were buried with comes to the vault",
    "A candle costs 5", "The memorial keeps sixty names, not thirty", "A hero remembered may come back to the tavern as a recruit, once"] },
};
CM.CANDLE_COST = [10, 5];
// what a run brings home in renown
CM.renownFor = function (entry, game) {
  let n = Math.min(50, entry.floor || 0) + 5 * ((entry.tally || {}).guardians || []).length + 5 * ((entry.tally || {}).spoken || []).length;
  if (entry.won) n += 50;
  if (entry.bottom) n += 100;
  if (entry.weekly) n += 30;
  n += 20 * ((entry.titles || []).length);
  n += 3 * Math.min(9, ((entry.tally || {}).visited || []).length);     // (the town rewards being used: three for every door opened before the descent)
  if (entry.difficulty === "grim") n = Math.round(n * 1.5); else if (entry.difficulty === "gentle") n = Math.round(n * 0.6);
  return n;
};
// contracts: three a week from the week's seed, checked on a run's end; renown and a title each
CM.CONTRACTS = {
  nohealer: { name: "Steel alone", what: "Slay the Forge-Warden with no Cleric, Paladin or Druid in the party", renown: 60, check: (e, g) => (e.tally.guardians || []).includes("forge") && !g.party.some((h) => ["Cleric", "Paladin", "Druid"].includes(h.cls)) },
  grim12: { name: "Grim dozen", what: "Reach floor 12 on Grim", renown: 50, check: (e) => e.difficulty === "grim" && e.floor >= 12 },
  sporecap: { name: "The alchemist's errand", what: "Come to a run's end carrying a Spore Cap", renown: 40, check: (e, g) => g.bag.some((i) => i.kind === "ingredient" && i.ingredient === "sporecap") },
  swiftcrown: { name: "No time to lose", what: "Slay the Lich King in under 1,200 steps", renown: 80, check: (e) => e.won && (e.tally.steps || 0) < 1200 },
  dryrun: { name: "Dry", what: "Reach floor 10 without drinking from a fountain", renown: 40, check: (e, g) => e.floor >= 10 && !(g.tally.drank) },
  unbroken: { name: "Unbroken", what: "Reach floor 15 with no hero ever fallen", renown: 60, check: (e, g) => e.floor >= 15 && !g.everFell },
  hoard: { name: "The hoard", what: "Come to a run's end with 1,500 gold", renown: 40, check: (e) => e.gold >= 1500 },
  deepfriends: { name: "Old friends, deep down", what: "Have a bond and reach floor 25", renown: 60, check: (e, g) => (g.bonds || []).length > 0 && e.floor >= 25 },
  weaver3: { name: "Three weaves", what: "Find three weaves, ever", renown: 50, check: (e, g) => Object.keys(g.weaves || {}).length >= 3 },
  bellgrim: { name: "The last bell, on Grim", what: "Bring Brother Cael the bell on Grim", renown: 70, check: (e, g) => e.difficulty === "grim" && Boolean(g.story && g.story.bell) },
  knightspoken: { name: "No blow struck", what: "Pass the Drowned Knight by speech", renown: 60, check: (e) => (e.tally.spoken || []).includes("knight") },
  ownrest: { name: "One of ours", what: "Lay a fallen hero of your own to rest where they fell", renown: 50, check: (e, g) => (g.earned || []).includes("laidtorest") },
  chapter3: { name: "Three chapters", what: "Complete three chapters of the codex in one run", renown: 60, check: (e, g) => CM.codex(g).filter((c) => c.band !== undefined && c.complete).length >= 3 },
  monkcrown: { name: "Empty hands", what: "Take the crown with a Monk in the party", renown: 80, check: (e, g) => e.won && g.party.some((h) => h.cls === "Monk") },
};
CM.contractsFor = function (seed) {
  const ids = Object.keys(CM.CONTRACTS), out = [];
  for (let i = 1; out.length < 3 && i < 30; i++) { const id = ids[CM.hashSeed(`${seed}:contract:${i}`) % ids.length]; if (!out.includes(id)) out.push(id); }
  return out;
};

{
Object.assign(CM.Game.prototype, {
  villageLevel(id) { return ((this.village || {}).levels || {})[id] || 0; },
  // renown, spent and unspent
  renown() { const v = this.village || {}; return (v.renown || 0) - (v.spent || 0); },
  saveVillage() { CM.store.set("village", this.village); },
  // the next level of a building, for renown
  build(id) {
    const B = CM.VILLAGE[id];
    if (!B) return "No such building.";
    const lvl = this.villageLevel(id);
    if (lvl >= B.costs.length) return `${B.name} is as grand as it can be.`;
    const cost = B.costs[lvl];
    if (this.renown() < cost) return `${B.name}'s next level asks ${cost} renown; the village has ${this.renown()}.`;
    this.village.spent = (this.village.spent || 0) + cost;
    this.village.levels[id] = lvl + 1;
    this.saveVillage();
    this.sound("lever");
    this.emit("change");
    return "";
  },
  // a hero who came home retires as a trainer (the guildhall): one trainer a calling, the trainer's first boon for every new hero of it
  retire(heroIndex) {
    const h = this.party[heroIndex];
    if (!h || h.hp <= 0) return "Only a hero who came home can retire.";
    if (this.villageLevel("guildhall") < 1) return "The village has no guildhall yet.";
    if (!(h.boons || []).length) return `${h.name} has no boon to teach.`;
    if (this.retiredThisRun) return "One retires a run.";
    this.village.trainers = (this.village.trainers || []).filter((t) => t.cls !== h.cls).concat({ name: h.name, cls: h.cls, boon: h.boons[0], level: h.level, date: CM.today(), how: this.bottom ? "bottom" : this.crowned ? (this.reminded ? "reminded" : "crowned") : "alive", floor: this.floor ? this.floor.number : 0 });
    this.retiredThisRun = true;
    this.saveVillage();
    this.sound("level");
    this.emit("change");
    return "";
  },
  trainerFor(cls) { return ((this.village || {}).trainers || []).find((t) => t.cls === cls) || null; },
  // a candle for a hero laid to rest: what they were buried with comes to the vault
  lightCandle(i) {
    const m = (this.memorial || [])[i];
    if (!m) return "No such name.";
    if (this.villageLevel("shrine") < 1) return "The village has no shrine yet.";
    if (m.candle) return `A candle burns for ${m.name} already.`;
    const cost = CM.CANDLE_COST[this.villageLevel("shrine") >= 2 ? 1 : 0];
    if (this.renown() < cost) return `A candle asks ${cost} renown.`;
    this.village.spent = (this.village.spent || 0) + cost;
    m.candle = CM.today();
    CM.store.set("memorial", this.memorial);
    let note = "";
    if (m.buried && this.vaultRoom()) { this.vaults.push(m.buried); CM.store.set("vaults", this.vaults); note = ` ${m.buried.name} comes up to the vault.`; }
    else if (m.buried) note = " The vault is full; what they were buried with waits.";
    this.saveVillage();
    this.sound("heal");
    this.emit("change");
    return "";
  },
  vaultCapacity() { const g = this.villageLevel("guildhall"); return g >= 4 ? 5 : g >= 2 ? 3 : 1; },
  vaultRoom() { return (this.vaults || []).filter((it) => !it.named).length < this.vaultCapacity(); },   // (a named weapon is kept for nothing: it takes no slot)
  // the week's contracts, and which are done
  contracts() {
    const week = CM.weeklySeed(), v = this.village;
    if (!v.contracts || v.contracts.week !== week) v.contracts = { week, done: [] };
    return CM.contractsFor(week).map((id) => ({ id, c: CM.CONTRACTS[id], done: v.contracts.done.includes(id) }));
  },
  checkContracts(entry) {
    const got = [];
    for (const { id, c, done } of this.contracts()) {
      if (done) continue;
      let ok = false;
      try { ok = Boolean(c.check(entry, this)); } catch (e) { ok = false; }
      if (!ok) continue;
      this.village.contracts.done.push(id);
      this.village.renown = (this.village.renown || 0) + c.renown;
      got.push(c);
      this.say(`Contract kept: ${c.name} - ${c.renown} renown.`);
    }
    this.saveVillage();
    return got;
  },
  // scholarship: the library's share more from every blow on a kind fully learned
  scholarship(m) {
    const lvl = this.villageLevel("library");
    if (!lvl || !m || m.boss || m.guardian) return 1;
    const e = (this.bestiary || {})[m.kind || m.name];
    if (!e || e.seen < 3 || e.slain < 3 || !(e.weak.length || e.resist.length)) return 1;
    return 1 + 0.01 * Math.min(3, lvl);
  },
});
}
