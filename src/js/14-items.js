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
  CM.ARMORS.forEach((n, i) => add(n, "armor", "armor", i, "armor", { weight: CM.ARMOR_WEIGHT(i) }));
  CM.SHIELDS.forEach((n, i) => add(n, "shield", "offhand", i * 2, "shield"));
  CM.HELMS.forEach((n, i) => add(n, "helm", "helm", i * 2, "helm"));
  Object.entries(CM.RINGS).forEach(([st, n], i) => add(n, "ring", "ring", i, "ring", { stat: st }));
  CM.AMULETS.forEach((a, i) => add(a.name, "amulet", "amulet", i, "amulet"));
  CM.BOOTS.forEach((b, i) => add(b.name, "boots", "boots", Math.round(i * 1.7), "boots"));
  CM.CLOAKS.forEach((c, i) => add(c.name, "cloak", "cloak", Math.round(i * 1.7), "cloak"));
  Object.values(CM.UNIQUES).forEach((u) => add(u.name, u.kind, u.slot, u.band, "unique"));
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
CM.GROUP_NAMES = { weapon: "Weapons", bow: "Bows", armor: "Armour", shield: "Shields", helm: "Helms", ring: "Rings", amulet: "Amulets", boots: "Boots", cloak: "Cloaks", unique: "Uniques", relic: "Relics", stuff: "Potions and stuff", scroll: "Scrolls", wand: "Wands", tome: "Tomes", ingredient: "Ingredients" };
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
