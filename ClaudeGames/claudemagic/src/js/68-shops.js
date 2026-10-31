"use strict";
// The town's shops: the Hanged Lantern (the tavern - recruits, the fence, rumours, the board, a drink, the regular's
// gossip), the Merchant's House (the full stock, orders to the first camp, insurance, and at level 3 a commission: a
// thing of a chosen base at the party's level, made by the next camp) and the Smith's forge (the camps' smith's work,
// and two things only a forge does: a base reforged with its affixes kept, and a second gem set in a relic; the
// apprentice buys scrap at three quarters). The camps keep their benches; the camps' tavern keeps the recruits only.
CM.TOWN_PLOTS.tavern.always = true; CM.TOWN_PLOTS.smith.always = true; CM.TOWN_PLOTS.merchant.always = true;
CM.VILLAGE.tavern = { name: "The Hanged Lantern", costs: [60, 140], levels: ["A better cellar: the round sets the party's heart to full, and the regular's gossip is on the house", "A better bench: the recruits come a level higher"] };
CM.VILLAGE.smith = { name: "The Smith's forge", costs: [60, 140, 260], levels: ["The apprentice buys scrap at its full value", "A reforging costs half, and the smelter is lit", "The smith tempers: a word from the land worked in for the run"] };
CM.TOWN_PLOTS.tavern.village = "tavern"; CM.TOWN_PLOTS.smith.village = "smith";
CM.plotLevel = (game, id) => { const P = CM.TOWN_PLOTS[id]; if (!P) return 0; const v = P.village && game ? game.villageLevel(P.village) : 0; return P.always ? Math.max(1, v) : v; };
CM.COMMISSION_OVER = 1.5;
CM.DRINK_PRICE = 5;
CM.GOSSIP_PRICE = 10;
CM.SCRAP_PRICE = 0.75;
// a thing of a given base, at a floor's level: the base's kind, tier and hands; the floor's dice for the rest; known
CM.gearOfBase = function (baseId, floor, rnd) {
  const B = CM.BASES[baseId]; if (!B || !["weapon", "armor", "shield", "helm"].includes(B.kind)) return null;
  const item = CM.makeGear(B.kind, floor, rnd), tier = B.tier || 0, roll = rnd.int(0, 2);
  item.props = {}; item.unknown = false; item.name = B.id; item.base = B.id;
  if (B.kind === "weapon") { item.power = (tier + 1) * 2 + roll; item.value = 15 * (tier + 1) * (tier + 1); if (B.twohanded) item.props.twohanded = true; if (B.bow) { item.props.bow = true; item.props.twohanded = true; } }
  else if (B.kind === "armor") { item.power = tier + 1 + roll; item.value = 15 * (tier + 1) * (tier + 1); item.props.weight = CM.ARMOR_WEIGHT(tier); }
  else { item.power = tier + 1; item.value = (B.kind === "shield" ? 20 : 15) * (tier + 1) * (tier + 1); }
  const imp = CM.implicitFor(item); if (imp) { CM.applyProps(item, imp); item.props.implicit = true; }
  return item;
};
Object.assign(CM.Game.prototype, {
  atShop() { return this.mode === "camp" || this.inTown(); },
  partyLevel() { const up = this.party.filter((h) => h.hp > 0); return Math.max(1, Math.round(up.reduce((s, h) => s + h.level, 0) / Math.max(1, up.length))); },
  // the merchant's commission: a thing of a chosen base at the party's level, affixed as the floor would, paid now, made by the first camp
  commission(baseId) {
    if (!this.inTown() || !this.shopping) return "Commissions are placed at the Merchant's House, in town.";
    if (this.villageLevel("merchant") < 3) return "The merchant takes commissions when his house has a third level.";
    const B = CM.BASES[baseId]; if (!B || !["weapon", "armor", "shield", "helm"].includes(B.kind) || B.group === "unique" || B.group === "relic") return "The merchant has no pattern for that.";
    const L = this.partyLevel(), rnd = new CM.Random(CM.hashSeed(`${this.seed}:commission:${baseId}:${(this.orders || []).length}`));
    const item = CM.gearOfBase(baseId, L, rnd); if (!item) return "The merchant has no pattern for that.";
    CM.affix(item, L, rnd); item.unknown = false; item.name = CM.itemName(item);
    const price = Math.ceil(CM.priceAt(item.value, 1) * CM.COMMISSION_OVER) + 40;
    if (this.gold < price) return `A commission for ${item.name} is ${price} gold, paid now.`;
    this.logAct("commission", baseId);
    this.gold -= price; this.spend("orders", price);
    this.orders = (this.orders || []).concat({ item, from: 0, commission: true });
    this.sound("coin"); this.say(`The merchant measures and writes: ${item.name}, ${price} gold, to be waiting at the first camp.`);
    this.saveRun(); this.emit("change");
    return "";
  },
  // the Hanged Lantern: a drink sets the party out in heart; the regular sells what the seed knows
  drink() {
    if (!this.inTown()) return "The Hanged Lantern is in town.";
    if (this.floor.drank) return "One round is enough before a descent.";
    const price = CM.festivalIs(this, "midsummer") ? 0 : ((this.village || {}).perks || {}).tavern ? Math.ceil(CM.DRINK_PRICE / 2) : CM.DRINK_PRICE; if (this.gold < price) return `A round is ${price} gold.`;   // (the tavern-keeper's errand: half price)
    this.logAct("drink");
    this.gold -= price; this.spend("tavern", price); this.floor.drank = true;
    if (CM.festivalIs(this, "wassail")) { this.gain([CM.dish("beer")], "tavern"); this.say("The Wassail: the cellar is open, and a jug of beer goes into the pack."); }
    const heart = this.villageLevel("tavern") >= 1 || CM.festivalIs(this, "wassail") ? 100 : 90; if ((this.morale || CM.MORALE.start) < heart) this.morale = heart;
    this.fed = 0; if (!this.meal) { this.meal = { kind: "pottage", dish: true, floor: 1 }; for (const h of this.party) { h.mealLuck = 0; h.mealStat = "str"; CM.recompute(h); } this.say("The round comes with the pot: bean pottage, for the first floor."); }   // (the round is a meal)
    this.sound("coin"); this.say(`A round at the Hanged Lantern, and the party is ${this.moraleWord().toLowerCase()}.`);
    this.saveRun(); this.emit("change");
    return "";
  },
  gossip() {
    if (!this.inTown()) return "The regular drinks at the Hanged Lantern.";
    if (this.gossiped) return "The regular has told you what he knows this run.";
    const fee = this.villageLevel("tavern") >= 1 || CM.festivalIs(this, "bells") ? 0 : CM.GOSSIP_PRICE;
    if (this.gold < fee) return `The regular talks for ${CM.GOSSIP_PRICE} gold.`;
    this.logAct("gossip");
    this.gold -= fee; if (fee) this.spend("tavern", fee); this.gossiped = true;
    const seed = this.seed, floors = []; for (let n = 16; n <= 20; n++) if (!CM.guardianFor(n) && n !== CM.LAST_FLOOR) floors.push(n);
    const holding = floors[CM.hashSeed(`${seed}:holding`) % floors.length];
    const first = [2, 3, 4]; const unique0 = first[CM.hashSeed(`${seed}:unique:0`) % first.length];
    this.say(`The regular leans in: "The sexton's helm is in a chest on floor ${unique0}, they say. And the dwarves' bottomless sack - the palace, floor ${holding}. Don't ask me how I know."`);
    this.saveRun(); this.emit("change");
    return "";
  },
  // the forge: a base reforged, its words and its marks kept (gold by the tier, and an essence); a second gem in a relic; the apprentice's scrap price
  reforgeBase(heroIndex, slot, baseId) {
    if (!this.inTown()) return "Only the forge in town reforges a base.";
    const hero = this.party[heroIndex], item = hero && hero[slot], B = CM.BASES[baseId];
    if (!item || !["weapon", "armor", "offhand", "helm"].includes(slot)) return "Pick a weapon, armour, a shield or a helm.";
    if (item.unknown) return "The smith won't reforge what nobody can name.";
    if (item.props && (item.props.relic || item.props.unique)) return "A relic or a unique thing is what it is.";
    if (!B || B.kind !== item.kind || B.group === "unique" || B.group === "relic") return "The new base must be of the same kind.";
    if (B.id === CM.baseIdOf(item)) return "It is that already.";
    const cost = Math.ceil(100 * ((B.tier || 0) + 1) * (this.villageLevel("smith") >= 2 ? 0.5 : 1)), ess = this.bag.findIndex((i) => i.kind === "essence");
    if (ess < 0) return "The forge wants an essence for a reforging.";
    if (this.gold < cost) return `The forge wants ${cost} gold for a ${B.id}, and an essence.`;
    this.logAct("reforgeBase", heroIndex, slot, baseId);
    this.gold -= cost; this.spend("smith", cost);
    if ((this.bag[ess].power || 1) > 1) this.bag[ess].power -= 1; else this.bag.splice(ess, 1);
    const oldTier = (CM.BASES[CM.baseIdOf(item)] || {}).tier || 0, p = item.props = item.props || {};
    item.power = Math.max(1, item.power + ((B.tier || 0) - oldTier) * (item.kind === "weapon" ? 2 : 1));
    item.base = B.id; delete p.twohanded; delete p.bow; if (B.twohanded) p.twohanded = true; if (B.bow) { p.bow = true; p.twohanded = true; }
    item.name = CM.itemName(item); item.value += 50 * ((B.tier || 0) + 1);
    item.history = (item.history || []).concat(`reforged into a ${B.id} at the forge in town`);
    CM.recompute(hero);
    this.sound("lever"); this.say(`The smith heats ${hero.name}'s blade white and beats it into a ${B.id}: ${item.name}, with every word it had.`);
    this.saveRun(); this.emit("change");
    return "";
  },
  secondGem(heroIndex, slot) {
    if (!this.inTown()) return "Only the forge in town sets a second gem.";
    const hero = this.party[heroIndex], item = hero && hero[slot];
    if (!item || !(item.props && item.props.relic)) return "A second gem goes into a relic.";
    if (item.props.gem2) return `${item.name} has its second gem.`;
    const gem = this.bag.findIndex((i) => i.kind === "gem" && CM.GEMS[i.gem].element); if (gem < 0) return "The forge wants a ruby, a sapphire or a sunstone.";
    const cost = CM.SMITH.gem * 2; if (this.gold < cost) return `The forge wants ${cost} gold to set a second gem.`;
    this.logAct("secondGem", heroIndex, slot);
    const el = CM.GEMS[this.bag[gem].gem].element, name = this.bag[gem].name;
    this.gold -= cost; this.spend("smith", cost); this.bag.splice(gem, 1);
    item.props.gem2 = el; item.props.resist = el; item.power += 1; item.value += 150;
    CM.recompute(hero);
    this.sound("lever"); this.say(`The ${name.toLowerCase()} goes into ${item.name} beside the first: the wearer is proof against ${CM.ELEMENT_NAMES[el] || el}, and the relic is a little stronger for it.`);
    this.saveRun(); this.emit("change");
    return "";
  },
  // the smelter: three chunks and a charcoal make a bar; two bars of a kind and one of the kind above make an alloy; at the forge's second level
  smelt(ore) {
    if (!this.inTown()) return "The smelter is at the forge in town.";
    if (this.villageLevel("smith") < 2) return "The forge has no smelter yet: the smith's second level.";
    if (!CM.ORES[ore]) return "No such ore.";
    const rows = this.bag.map((it, i) => [it, i]).filter(([it]) => it.kind === "ore" && it.ore === ore), coal = this.bag.findIndex((i) => i.kind === "charcoal");
    if (rows.length < CM.SMELT_CHUNKS) return `${/^[aeiou]/.test(CM.ORES[ore].name) ? "An" : "A"} ${CM.ORES[ore].name} bar wants ${CM.SMELT_CHUNKS} chunks; the pack has ${rows.length}.`;
    if (coal < 0) return "The smelter wants a charcoal a bar: the Wood's burner has it.";
    this.logAct("smelt", ore);
    for (const [, i] of rows.slice(0, CM.SMELT_CHUNKS).reverse()) this.bag.splice(i, 1); this.bag.splice(this.bag.findIndex((i) => i.kind === "charcoal"), 1);
    this.gain([CM.metalBar(ore)], "smelter"); this.tally.bars = (this.tally.bars || 0) + 1; this.countUse("smelt");
    this.sound("lever"); this.say(`The smelter roars, and a ${CM.ORES[ore].name} bar comes out of the mould.`);
    this.saveRun(); this.emit("change");
    return "";
  },
  alloy(kind) {
    if (!this.inTown()) return "The smelter is at the forge in town.";
    if (this.villageLevel("smith") < 2) return "The forge has no smelter yet: the smith's second level.";
    const A = CM.ALLOYS[kind]; if (!A) return "No such alloy.";
    const low = this.bag.map((it, i) => [it, i]).filter(([it]) => it.kind === "bar" && it.bar === A.of[0]), high = this.bag.findIndex((i) => i.kind === "bar" && i.bar === A.of[1]);
    if (low.length < 2 || high < 0) return `${A.name.charAt(0).toUpperCase() + A.name.slice(1)} wants two ${CM.ORES[A.of[0]].name} bars and one of ${CM.ORES[A.of[1]].name}.`;
    this.logAct("alloy", kind);
    for (const [, i] of low.slice(0, 2).reverse()) this.bag.splice(i, 1); this.bag.splice(this.bag.findIndex((i) => i.kind === "bar" && i.bar === A.of[1]), 1);
    this.gain([CM.metalBar(kind)], "smelter"); this.tally.bars = (this.tally.bars || 0) + 1; this.countUse("smelt");
    this.sound("lever"); this.say(`Three bars go in and one comes out, and it rings: ${A.name}.`);
    this.saveRun(); this.emit("change");
    return "";
  },
  whetPicks() {
    if (!this.inTown()) return "The picks are whetted at the forge in town.";
    const picks = this.bag.filter((i) => i.kind === "pick" && i.points !== undefined && i.points < CM.PICKS[i.pick].points); if (!picks.length) return "Every pick in the pack has its point.";
    const cost = CM.festivalIs(this, "letter") ? 0 : 20 * picks.length; if (this.gold < cost) return `The smith wants ${cost} gold to put a point back on ${CM.plural(picks.length, "pick")}.`;
    this.logAct("whetPicks");
    this.gold -= cost; this.spend("smith", cost); for (const p of picks) p.points = CM.PICKS[p.pick].points;
    this.sound("lever"); this.say(`${CM.plural(picks.length, "pick")} on the grindstone: as new.`);
    this.saveRun(); this.emit("change");
    return "";
  },
  sellBars() {
    if (!this.inTown()) return "The apprentice is at the forge in town.";
    const rows = this.bag.map((it, i) => [it, i]).filter(([it]) => it.kind === "bar"); if (!rows.length) return "No bars in the pack.";
    this.logAct("sellBars");
    const paid = rows.reduce((s, [it]) => s + (it.value || 0), 0); for (const [, i] of rows.reverse()) this.bag.splice(i, 1); this.gold += paid;
    this.sound("coin"); this.say(`The apprentice weighs the bars and pays ${paid} gold, which is what they are worth.`);
    this.saveRun(); this.emit("change");
    return "";
  },
  sellScrap() {
    if (!this.inTown()) return "The apprentice is at the forge in town.";
    const rows = this.bag.map((it, i) => [it, i]).filter(([it]) => it.kind === "scrap");
    if (!rows.length) return "No scrap in the pack.";
    this.logAct("sellScrap");
    const paid = rows.reduce((s, [it]) => s + Math.ceil((it.value || 5) * (this.villageLevel("smith") >= 1 ? 1 : CM.SCRAP_PRICE)), 0);
    for (const [, i] of rows.reverse()) this.bag.splice(i, 1);
    this.gold += paid;
    this.sound("coin"); this.say(`The apprentice weighs the scrap and pays ${paid} gold for it.`);
    this.saveRun(); this.emit("change");
    return "";
  },
});
