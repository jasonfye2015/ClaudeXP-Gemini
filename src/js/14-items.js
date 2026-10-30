"use strict";
// The ledger of things: every base a thing can be, by id (its name, which the old lists already used as one), what
// a thing is called from what it is made of, where it was found, and the compendium of every base ever seen.
//
//   CM.BASES["Long Sword"]            -> { id, kind, slot, tier, group }
//   CM.itemName(item)                 -> "Keen Flaming Long Sword of the Bear +2" (from base, affixes, element, bonus)
//   CM.normalizeItem(item)            -> the same item, with base and found set (a save from before)
//   CM.tagFound(items, floor, how)    -> the items, each with found = {floor, how}
//   CM.compendium(seen)               -> groups of bases, with which have been seen
CM.BASES = {};
{
  const add = (id, kind, slot, tier, group, more) => { CM.BASES[id] = Object.assign({ id, kind, slot, tier, group }, more || {}); };
  CM.WEAPONS.forEach((n, i) => add(n, "weapon", "weapon", i, "weapon", { twohanded: CM.TWO_HANDED.includes(n) }));
  CM.BOWS.forEach((n, i) => add(n, "weapon", "weapon", Math.min(11, Math.round(i * 2.5)), "bow", { bow: true, twohanded: true }));
  [["Stiletto", 3], ["Kris", 7], ["Morning Star", 4], ["Maul", 8], ["Hand Axe", 1], ["Broad Axe", 5], ["Spear", 2], ["Glaive", 6], ["Halberd", 9], ["Ashwood Staff", 2], ["Runed Staff", 7]].forEach(([n, t]) => add(n, "weapon", "weapon", t, "weapon", { twohanded: ["Maul", "Halberd", "Glaive"].includes(n) }));
  CM.ARMORS.forEach((n, i) => add(n, "armor", "armor", i, "armor", { weight: CM.ARMOR_WEIGHT(i) }));
  CM.SHIELDS.forEach((n, i) => add(n, "shield", "offhand", i * 2, "shield"));
  CM.HELMS.forEach((n, i) => add(n, "helm", "helm", i * 2, "helm"));
  Object.entries(CM.RINGS).forEach(([st, n], i) => add(n, "ring", "ring", i, "ring", { stat: st }));
  CM.AMULETS.forEach((a, i) => add(a.name, "amulet", "amulet", i, "amulet"));
  CM.BOOTS.forEach((b, i) => add(b.name, "boots", "boots", Math.round(i * 1.7), "boots"));
  CM.CLOAKS.forEach((c, i) => add(c.name, "cloak", "cloak", Math.round(i * 1.7), "cloak"));
  Object.values(CM.UNIQUES).forEach((u) => add(u.name, u.kind, u.slot, u.band, "unique"));
  Object.entries(CM.SETS).forEach(([id, S]) => S.pieces.forEach(([n, kind, slot, tier]) => add(n, kind, slot, tier * 1, "set", { set: id })));
  Object.values(CM.GUARDIANS).forEach((G) => { if (G.relic) add(G.relic.name, G.relic.kind, G.relic.slot, CM.GUARDIAN_ORDER.indexOf(Object.keys(CM.GUARDIANS).find((k) => CM.GUARDIANS[k] === G)), "relic"); });
  [["Healing Potion", "heal"], ["Greater Healing Potion", "greaterheal"], ["Mana Potion", "mana"], ["Phoenix Feather", "revive"], ["Antidote", "antidote"], ["Torch", "torch"], ["Lantern", "lantern"], ["Ration", "ration"], ["Rope", "rope"], ["Firepot", "bomb"]]
    .forEach(([n, k], i) => add(n, k, null, i, "stuff"));
  Object.values(CM.SCROLLS).forEach((s, i) => add(s.name, "scroll", null, i, "scroll"));
  Object.values(CM.WANDS).forEach((w, i) => add(w.name, "wand", null, i, "wand"));
  Object.values(CM.TOMES).forEach((n, i) => add(n, "tome", null, i, "tome"));
  Object.values(CM.GEMS).forEach((g, i) => add(g.name, "gem", null, i, "stuff"));
  Object.values(CM.INGREDIENTS).forEach((g, i) => add(g.name, "ingredient", null, i, "ingredient"));
  ["Oil of Fire", "Oil of Rime", "Oil of Saints"].forEach((n, i) => add(n, "oil", null, i, "stuff"));
}
CM.GROUP_NAMES = { set: "Sets", weapon: "Weapons", bow: "Bows", armor: "Armour", shield: "Shields", helm: "Helms", ring: "Rings", amulet: "Amulets", boots: "Boots", cloak: "Cloaks", unique: "Uniques", relic: "Relics", stuff: "Potions and stuff", scroll: "Scrolls", wand: "Wands", tome: "Tomes", ingredient: "Ingredients" };
CM.HOW_FOUND = { chest: "in a chest", foe: "on a slain foe", strongbox: "in a strongbox", ghost: "a ghost's gift", remains: "among a fallen party's remains", relic: "a guardian's", merchant: "bought at the camp", peddler: "bought from a peddler", vault: "from the vault", rivals: "a rival party's", event: "found on the floor", start: "carried from the stair", made: "brewed by the alchemist", smith: "the smith's work" };

// a thing's base id: what it was before any work (rings drop their plus; names made by the smith drop theirs)
CM.baseIdOf = function (item) {
  if (!item) return null;
  let b = item.base || CM.baseName(item);
  if (item.kind === "ring") b = b.replace(/ \+\d+$/, "");
  for (const e of Object.values(CM.ELEMENTS)) if (b.startsWith(e.prefix + " ")) b = b.slice(e.prefix.length + 1);   // (a base written down with its element's prefix, before v4.1)
  return b;
};
// what a thing is called, from what it is made of: prefix, element, base, suffix, plus
CM.itemName = function (item) {
  const p = item.props || {}, base = CM.baseIdOf(item);
  if (p.unique) return CM.UNIQUES[p.unique] ? CM.UNIQUES[p.unique].name + (p.awake ? ", Awake" : "") : item.name;
  if (p.relic) return base;
  if (item.kind === "ring") return `${base} +${item.power}`;
  if (!["weapon", "armor", "shield", "helm"].includes(item.kind)) return base;
  const words = p.affixes || [], prefix = words.find((w) => !w.startsWith("of ")), suffix = words.find((w) => w.startsWith("of "));
  return `${prefix ? prefix + " " : ""}${p.element && CM.ELEMENTS[p.element] ? CM.ELEMENTS[p.element].prefix + " " : ""}${base}${suffix ? " " + suffix : ""}${p.bonus && (words.length || p.enchant) ? ` +${p.bonus}` : ""}`;
};
// a thing from an older save: its base set, its finding unknown
CM.normalizeItem = function (item, how) {
  if (!item || typeof item !== "object") return item;
  if (!item.base || (item.kind === "ring" && / \+\d+$/.test(item.base))) item.base = CM.baseIdOf(item);
  if (!item.found) item.found = { floor: 0, how: how || "unknown" };
  const imp = CM.implicitFor(item); if (imp && !(item.props || {}).implicit && !(item.props || {}).unique && !(item.props || {}).relic) { CM.applyProps(item, imp); item.props.implicit = true; }
  return item;
};
CM.tagFound = function (items, floor, how) {
  for (const it of items) { if (!it) continue; it.base = CM.baseIdOf(it); it.found = { floor: floor || 0, how: how || "unknown" }; }
  return items;
};
// the compendium: every base, by group, with the ones seen (seen: {baseId: {floor, date}})
CM.compendium = function (seen) {
  seen = seen || {};
  const groups = {};
  for (const b of Object.values(CM.BASES)) (groups[b.group] = groups[b.group] || []).push(Object.assign({}, b, { seen: Boolean(seen[b.id]), when: seen[b.id] || null }));
  return Object.entries(CM.GROUP_NAMES).filter(([g]) => groups[g]).map(([g, name]) => { const list = groups[g].sort((a, b) => a.tier - b.tier || a.id.localeCompare(b.id)); return { id: g, name, list, seen: list.filter((x) => x.seen).length, total: list.length }; });
};
// a thing's card: what it is, and where it came from
CM.itemCard = function (item) {
  const where = item.found && item.found.how !== "unknown" ? ` Found ${item.found.floor ? `on floor ${item.found.floor}, ` : ""}${CM.HOW_FOUND[item.found.how] || item.found.how}.` : "";
  return `${item.unknown ? CM.baseName(item) : item.name}: ${CM.itemLabel(item)}.${where}`;
};
// the bag's filters
CM.BAG_FILTERS = { all: { name: "All", kinds: null }, gear: { name: "Gear", kinds: ["weapon", "armor", "shield", "helm", "ring", "amulet", "boots", "cloak"] }, drink: { name: "Drink", kinds: ["heal", "greaterheal", "mana", "revive", "antidote", "ration"] },
  read: { name: "Read", kinds: ["scroll", "wand", "tome"] }, stuff: { name: "Stuff", kinds: ["gem", "ingredient", "oil", "bomb", "torch", "lantern", "rope", "key", "boxkey", "bones", "scrap", "page", "bell"] } };

// ---- weapons with character: a class for every weapon, one rule each; who is at home with what; what a monster is
// made of, which the rules read ----
CM.WEAPON_CLASSES = {
  blade: { name: "blade", what: "the standard: a sixth more against flesh" },
  blunt: { name: "blunt", what: "ignores a third of bone, shell and plate, and of the undead's defence; never finds a weak spot" },
  axe: { name: "axe", what: "cleaves: a second foe in the same row takes half; a sixth more against hide" },
  polearm: { name: "polearm", what: "strikes at full strength from the back row; cramped in the front, three quarters" },
  dagger: { name: "dagger", what: "quick: two steps earlier in the round, weak spots found a tenth more and struck for three times; two thirds of a blow" },
  bow: { name: "bow", what: "shoots over the front line at full strength; a Ranger's" },
  staff: { name: "staff", what: "half a blow; +1 to every spell a tier (a caster's)" },
  fist: { name: "fists", what: "the Monk's hands" },
};
CM.WEAPON_CLASS_OF = { Dagger: "dagger", Knife: "dagger", Stiletto: "dagger", Kris: "dagger", "Short Sword": "blade", "Long Sword": "blade", "Bastard Sword": "blade", "Rune Blade": "blade", "Mithril Sword": "blade", Claudebrand: "blade",
  Club: "blunt", Mace: "blunt", "War Hammer": "blunt", "Morning Star": "blunt", Maul: "blunt", "Battle Axe": "axe", Flamberge: "axe", Dragonslayer: "axe", "Hand Axe": "axe", "Broad Axe": "axe",
  Spear: "polearm", Glaive: "polearm", Halberd: "polearm", Staff: "staff", "Ashwood Staff": "staff", "Runed Staff": "staff", "Wrapped Fists": "fist" };
// the other arms, by class and tier (CM.makeGear reaches for them a third of the time; the old list keeps its tiers)
CM.ARMS_MORE = { dagger: [["Stiletto", 3], ["Kris", 7]], blunt: [["Morning Star", 4], ["Maul", 8]], axe: [["Hand Axe", 1], ["Broad Axe", 5]], polearm: [["Spear", 2], ["Glaive", 6], ["Halberd", 9]], staff: [["Ashwood Staff", 2], ["Runed Staff", 7]] };
CM.weaponClass = (item) => { if (!item) return "fist"; const p = item.props || {}; if (p.bow) return "bow"; if (p.fists) return "fist"; if (p.wclass) return p.wclass; return CM.WEAPON_CLASS_OF[CM.baseIdOf(item)] || "blade"; };
// who is at home with what (a second calling adds its arms); the Monk's hands are the Monk's
CM.ARMS_AT_HOME = { Knight: ["blade", "blunt", "axe", "polearm"], Paladin: ["blade", "blunt"], Rogue: ["dagger", "blade"], Ranger: ["bow", "dagger", "blade"], Cleric: ["blunt", "staff"], Mage: ["staff", "dagger"], Druid: ["staff", "blunt"],
  Bard: ["blade", "dagger"], Monk: ["fist"], Necromancer: ["staff", "dagger"], Artificer: ["blunt", "axe", "polearm"] };
CM.atHome = (hero, item) => { const c = CM.weaponClass(item); return (CM.ARMS_AT_HOME[hero.cls] || []).includes(c) || (hero.second && (CM.ARMS_AT_HOME[hero.second] || []).includes(c)); };
CM.CLUMSY = 0.85;                                                        // to hit, with an arm one is not at home with (and no class rule)
// what a monster is made of: flesh, hide, bone, shell, plate, none (the rules read it)
CM.HIDE = { "Giant Rat": "hide", Kobold: "hide", Skeleton: "bone", Goblin: "flesh", Zombie: "flesh", Orc: "flesh", Ghoul: "flesh", "Dark Elf": "flesh", Troll: "hide", Wraith: "none", Ogre: "hide", Minotaur: "hide", Gargoyle: "shell", Vampire: "flesh",
  Demon: "plate", Wyvern: "shell", Drowned: "flesh", "Weed Hag": "flesh", "Fungal Horror": "hide", "Spore Beast": "hide", "Crystal Golem": "shell", "Shard Wisp": "none", "Iron Hound": "plate", "Foundry Imp": "plate", "Bone Colossus": "bone", "Grave Priest": "bone",
  Rootling: "hide", "Hollow One": "none", Sellsword: "plate", "Hedge Wizard": "flesh" };
CM.GUARDIAN_HIDE = { rat: "hide", knight: "plate", forge: "plate", queen: "flesh", mind: "hide", tyrant: "shell", master: "plate", patriarch: "bone", root: "hide" };
CM.hideOf = (m) => (m.guardian ? CM.GUARDIAN_HIDE[m.guardian] : m.boss ? "bone" : CM.HIDE[m.kind || m.name] || "flesh");
// shields block: a chance by tier that a blow does half; a tower shield blocks for a back-row hero as well
CM.blockChance = (shield) => (!shield || shield.unknown ? 0 : 0.08 + 0.06 * Math.max(0, CM.SHIELDS.indexOf(CM.baseIdOf(shield))) + (shield.props && shield.props.block ? shield.props.block : 0));
CM.isTower = (shield) => Boolean(shield) && CM.baseIdOf(shield) === "Tower Shield";
// armour weight: the heavy are a step late and loud; the light a step early
CM.weightInit = (h) => { const w = h.armor && h.armor.props && h.armor.props.weight; return w === "heavy" && CM.baseIdOf(h.armor) !== "Mithril Plate" ? -1 : w === "light" ? 1 : 0; };

// ---- affixes that grow, implicits, curses, sets, essence ----
CM.scaledAffix = function (a, tier) {                                    // an affix's numbers at a tier (words, flags and elements as they are)
  const k = CM.AFFIX_SCALE[tier] || 1, out = {};
  for (const [key, v] of Object.entries(a)) {
    if (key === "deep" || key === "weapon") continue;
    if (key === "stats") { out.stats = {}; for (const [st, d] of Object.entries(v)) out.stats[st] = Math.round(d * k); }
    else if (typeof v === "number" && !["vsUndead", "vsHide"].includes(key)) out[key] = key === "crit" || key === "bleed" || key === "chill" || key === "blindHit" || key === "stun" || key === "hitBonus" || key === "killGold" || key === "xpBonus" ? Math.round(v * k * 100) / 100 : Math.round(v * k);
    else if (typeof v === "number") out[key] = Math.round((1 + (v - 1) * k) * 100) / 100;
    else out[key] = v;
  }
  return out;
};
CM.applyProps = function (item, add) {                                   // lay a set of props on a thing (numbers add, flags set)
  const p = item.props = item.props || {};
  for (const [k, v] of Object.entries(add)) {
    if (k === "power") item.power += v;
    else if (k === "stats") { p.stats = p.stats || {}; for (const [st, d] of Object.entries(v)) p.stats[st] = (p.stats[st] || 0) + d; }
    else if (typeof v === "number" && typeof p[k] === "number" && !["vsUndead", "vsHide"].includes(k)) p[k] += v;
    else p[k] = v;
  }
  return item;
};
CM.implicitFor = (item) => CM.IMPLICITS[CM.baseIdOf(item)] || null;
CM.setOf = (item) => (item && item.props && item.props.set) || (item && CM.BASES[CM.baseIdOf(item)] && CM.BASES[CM.baseIdOf(item)].set) || null;
CM.setWorn = function (h) {                                              // the set a hero wears all three of, if any
  const count = {};
  for (const it of CM.equipped(h)) { const id = CM.setOf(it); if (id && !it.unknown) count[id] = (count[id] || 0) + 1; }
  return Object.keys(count).find((id) => count[id] >= 3) || null;
};
CM.makeSetPiece = function (setId, index, floor) {
  const S = CM.SETS[setId], [name, kind, slot, tier] = S.pieces[index];
  const power = kind === "ring" ? 1 : kind === "boots" ? 2 : kind === "armor" ? tier + 2 : tier + 1;
  const props = Object.assign({ set: setId, rarity: "fine" }, kind === "ring" ? { stat: "con" } : {}, kind === "boots" ? { silence: false } : {});
  return { name, base: name, kind, slot, power, value: 300 + 60 * tier, props, unknown: floor >= 2 };
};
CM.essence = (n = 1) => ({ name: "Essence", kind: "essence", power: n, value: 40 * n });
CM.ESSENCE_FOR_GEM = 3;
