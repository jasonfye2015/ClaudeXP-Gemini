"use strict";
// The forge's upgrading and tempering, and the Wood's leatherworker (the eighth big update, phase 5).
//
//   item.grade (0..5)                 -> stars in the name's tail; +1 power a grade, and at 3 and 5 an implicit word better
//   CM.gradeCost(item)                -> { bars, metal, gold } for the next grade: bars of the base's metal tier, and gold
//   game.upgrade(heroIndex, slot)     -> a grade, at the forge in town (the ceiling: not both grade 5 and enchanted +3)
//   CM.TEMPERS                        -> oak, beeswax, wolf-fat, bear's bile, star-dust: one word from the land, for the run
//   game.temper(heroIndex, slot, id)  -> at the smith's third level; gone at the run's end (stripTempers)
//   game.tan(kind)                    -> the hermit by day: hides into a cloak, boots, a buckler, a quiver
CM.GRADE_MOST = 5;
CM.GRADE_GOLD = 60;                                                      // gold a grade, times the grade
CM.GRADE_METAL = (tier) => (tier <= 2 ? "copper" : tier <= 4 ? "bronze" : tier <= 6 ? "iron" : tier <= 8 ? "steel" : "electrum");
CM.gradeCost = function (item) {
  const B = CM.BASES[CM.baseIdOf(item)] || {}, tier = B.tier || 0, grade = (item.grade || 0) + 1;
  const metal = tier >= 9 && grade >= 4 ? "starsteel" : CM.GRADE_METAL(tier);
  return { bars: grade, metal, gold: Math.ceil(CM.GRADE_GOLD * grade * (item.forgeRate || 1)), name: (CM.ALLOYS[metal] || CM.ORES[metal]).name };
};
CM.stars = (n) => "★".repeat(Math.max(0, n || 0));
CM.gradable = (item) => Boolean(item && ["weapon", "armor", "shield", "helm"].includes(item.kind) && !(item.props && (item.props.unique || item.props.relic || item.props.fists)));
// the tempers: what the land gives, worked in for one run
CM.TEMPERS = {
  oak: { name: "oak", from: { kind: "ingredient", ingredient: "deadwood" }, what: "oak-hafted: weighs one less", props: {} },
  beeswax: { name: "beeswax", from: { kind: "ingredient", ingredient: "honey" }, what: "waxed: the water costs the torch nothing", props: { waterwalk: true } },
  wolffat: { name: "wolf-fat", from: { kind: "hide", hide: "Wolf" }, what: "greased with wolf-fat: the party is not surprised", props: { silence: true } },
  bearbile: { name: "bear's bile", from: { kind: "hide", hide: "Bear" }, what: "bear's bile on the edge: a blow in four bleeds", props: { bleed: 0.25 }, weapon: true },
  stardust: { name: "star-dust", from: { kind: "ore", ore: "stariron" }, what: "star-dust in the steel: +1 to blows", props: { power1: 1 } },
};
CM.TEMPER_GOLD = 40;
CM.temperWord = (item) => (item && item.temper && CM.TEMPERS[item.temper.id] ? CM.TEMPERS[item.temper.id].what : "");
CM.untemper = function (item) {                                          // the temper's props off again (numbers subtracted, flags cleared)
  if (!item || !item.temper) return item;
  const p = item.props || {};
  for (const [k, v] of Object.entries(item.temper.props || {})) { if (typeof v === "number") { p[k] = (p[k] || 0) - v; if (!p[k]) delete p[k]; } else delete p[k]; }
  delete item.temper; return item;
};
{ const w0 = CM.weightOf; CM.weightOf = (item) => Math.max(0, w0(item) - (item && item.temper && item.temper.id === "oak" ? 1 : 0)); }
// the leatherworker's patterns: hides in, gear out (by day, at the hermit's hut)
CM.quiver = () => ({ name: "Quiver", kind: "quiver", power: 0, value: 60 });
CM.BASES.Quiver = { id: "Quiver", kind: "quiver", slot: null, tier: 31, group: "stuff" };
CM.WEIGHTS.quiver = 1;
CM.TANNING = {
  cloak: { name: "Travel Cloak", hides: 2, any: true, what: "a cloak of hides" },
  hood: { name: "Hooded Cloak", hides: 1, of: "Bear", what: "a bear's hide for a hood" },
  wards: { name: "Cloak of Wards", hides: 1, of: "Troll", what: "the Troll's hide, which turns a blow" },
  boots: { name: "Soft Boots", hides: 2, any: true, what: "soft boots, silent" },
  buckler: { name: "Buckler", hides: 3, any: true, what: "a buckler of boiled hide" },
  quiver: { name: "Quiver", hides: 3, any: true, what: "a quiver: a bow shoots a second arrow once a fight" },
};
CM.TAN_GOLD = 20;
CM.tanned = function (kind, floor, rnd) {
  const T = CM.TANNING[kind]; if (!T) return null;
  if (kind === "quiver") return CM.quiver();
  const B = CM.BASES[T.name], item = B.kind === "shield" ? CM.gearOfBase(T.name, floor, rnd) : CM.makeGear(B.kind, floor, rnd);
  if (B.kind !== "shield") { const row = (B.kind === "boots" ? CM.BOOTS : CM.CLOAKS).find((x) => x.name === T.name); item.name = T.name; item.base = T.name; item.props = {}; if (B.kind === "boots") { item.power = row.power; if (row.silence) item.props.silence = true; if (row.waterwalk) item.props.waterwalk = true; } else { item.power = row.df; item.props.df = row.df; if (row.hood) item.props.hood = true; } item.value = 40 * (item.power + 1) * (item.power + 1); }
  item.unknown = false; return item;
};
Object.assign(CM.Game.prototype, {
  // a grade: bars of the metal and gold; +1 power; at 3 and 5 an implicit word better; the ceiling
  upgrade(heroIndex, slot) {
    if (!this.inTown()) return "Only the forge in town raises a grade.";
    const hero = this.party[heroIndex], item = hero && hero[slot];
    if (!item || !["weapon", "armor", "offhand", "helm"].includes(slot)) return "Pick a weapon, armour, a shield or a helm.";
    if (item.unknown) return "The smith won't grade what nobody can name.";
    if (!CM.gradable(item)) return "A relic or a unique thing is what it is.";
    const grade = (item.grade || 0) + 1, p = item.props = item.props || {};
    if (grade > CM.GRADE_MOST) return `${item.name} is at the fifth grade: there is no sixth.`;
    if (grade === CM.GRADE_MOST && (p.enchant || 0) >= CM.SMITH.most) return `The smith shakes his head: a thing enchanted thrice cannot take the fifth grade too. "It would not hold the one and the other."`;
    const cost = CM.gradeCost(Object.assign(Object.create(item), { forgeRate: this.forgeRate() })), bars = this.bag.map((it, i) => [it, i]).filter(([it]) => it.kind === "bar" && it.bar === cost.metal);
    if (bars.length < cost.bars) return `The ${CM.ordinal(grade)} grade of ${item.name} wants ${CM.plural(cost.bars, `${cost.name} bar`)} and ${cost.gold} gold; the pack has ${bars.length}.`;
    if (this.gold < cost.gold) return `The smith wants ${cost.gold} gold for the grade, with the bars.`;
    this.logAct("upgrade", heroIndex, slot);
    this.gold -= cost.gold; this.spend("smith", cost.gold);
    for (const [, i] of bars.slice(0, cost.bars).reverse()) this.bag.splice(i, 1);
    item.grade = grade; item.power += 1; item.value += 40 * grade;
    if (grade === 3 || grade === 5) { if (item.kind === "weapon") p.power1 = (p.power1 || 0) + 1; else p.df = (p.df || 0) + 1; }
    item.name = CM.itemName(item);
    item.history = (item.history || []).concat(`graded ${CM.stars(grade)} at the forge in town`);
    this.tally.graded = (this.tally.graded || 0) + 1; this.countUse("upgrade");
    CM.recompute(hero);
    this.sound("lever"); this.say(`${cost.name.charAt(0).toUpperCase() + cost.name.slice(1)} into the fire, and the hammer: ${item.name}${grade === 3 || grade === 5 ? ", and the metal remembers it" : ""}.`);
    if (grade === CM.GRADE_MOST) this.achieve("graded");
    this.saveRun(); this.emit("change");
    return "";
  },
  // a temper: one word from the land, for the run (the smith's third level)
  temper(heroIndex, slot, id) {
    if (!this.inTown()) return "Only the forge in town tempers.";
    if (this.villageLevel("smith") < 3) return "The forge tempers at the smith's third level.";
    const hero = this.party[heroIndex], item = hero && hero[slot], T = CM.TEMPERS[id];
    if (!item || !["weapon", "armor", "offhand", "helm"].includes(slot)) return "Pick a weapon, armour, a shield or a helm.";
    if (item.unknown) return "The smith won't temper what nobody can name.";
    if (!T) return "No such temper.";
    if (T.weapon && item.kind !== "weapon") return `${T.name.charAt(0).toUpperCase() + T.name.slice(1)} goes on a blade.`;
    if (item.temper && item.temper.id === id) return `${item.name} is tempered with ${T.name} already.`;
    const src = this.bag.findIndex((it) => Object.entries(T.from).every(([k, v]) => it[k] === v));
    if (src < 0) return `${T.name.charAt(0).toUpperCase() + T.name.slice(1)} wants ${T.from.ingredient ? CM.INGREDIENTS[T.from.ingredient].name : T.from.hide ? T.from.hide + " hide" : CM.ORES[T.from.ore].name + " ore"} in the pack.`;
    const tg = Math.ceil(CM.TEMPER_GOLD * this.forgeRate()); if (this.gold < tg) return `The smith wants ${tg} gold for a tempering.`;
    this.logAct("temper", heroIndex, slot, id);
    this.gold -= tg; this.spend("smith", tg);
    if ((this.bag[src].power || 1) > 1 && this.bag[src].kind === "ore") this.bag[src].power -= 1; else this.bag.splice(src, 1);
    CM.untemper(item); CM.applyProps(item, T.props); item.temper = { id, props: Object.assign({}, T.props) };
    this.tally.tempered = (this.tally.tempered || 0) + 1; this.countUse("temper");
    CM.recompute(hero);
    this.sound("lever"); this.say(`${T.name.charAt(0).toUpperCase() + T.name.slice(1)} worked into ${item.name} while it is hot: ${T.what}. It will last the run.`);
    this.saveRun(); this.emit("change");
    return "";
  },
  stripTempers() {                                                       // at a run's end: the tempers are gone (the bag, what is worn, the vault's and the stash's never had one)
    for (const it of this.bag.concat(this.party.flatMap((h) => CM.equipped(h)))) if (it && it.temper) CM.untemper(it);
    for (const h of this.party) CM.recompute(h);
  },
  // the leatherworker: hides into gear, by day, at the hut
  tan(kind) {
    const fl = this.floor, here = fl && fl.things[fl.pos.join(",")];
    if (!here || here.type !== "hut") return "The hermit tans at the hut in the Deep Wood.";
    if (CM.isNight(this)) return "The hut is shuttered for the night.";
    const T = CM.TANNING[kind]; if (!T) return "The hermit has no such pattern.";
    const rows = this.bag.map((it, i) => [it, i]).filter(([it]) => it.kind === "hide" && (T.any ? true : it.hide === T.of));
    if (rows.length < T.hides) return `${T.name} wants ${T.any ? CM.plural(T.hides, "hide") : `a ${T.of} hide`}; the pack has ${rows.length}.`;
    if (this.gold < CM.TAN_GOLD) return `The hermit wants ${CM.TAN_GOLD} gold for the work.`;
    this.logAct("tan", kind);
    this.gold -= CM.TAN_GOLD; this.spend("hermit", CM.TAN_GOLD);
    const used = rows.slice(0, T.hides); for (const [, i] of used.reverse()) this.bag.splice(i, 1);
    const item = CM.tanned(kind, Math.max(1, this.partyLevel()), this.rnd);
    item.history = [`tanned by the hermit of the Deep Wood from ${used.map(([it]) => it.name.toLowerCase()).join(", ")}`];
    this.gain([item], "hermit"); this.tally.tanned = (this.tally.tanned || 0) + 1; this.countUse("tan");
    this.sound("coin"); this.say(`The hermit scrapes, soaks and stitches, and hands over ${/^[aeiou]/i.test(item.name) ? "an" : "a"} ${item.name}: ${T.what}.`);
    this.saveRun(); this.emit("change");
    return "";
  },
  hasQuiver() { return this.bag.some((it) => it.kind === "quiver"); },
});
CM.HOW_FOUND.hermit = "the hermit's work";
CM.ACHIEVEMENTS.graded = { name: "Five Stars", what: "Raise a thing to the fifth grade at the forge", title: "the Starred" };
