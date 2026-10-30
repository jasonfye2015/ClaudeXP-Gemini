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
  Object.values(CM.FLASKS).forEach((f, i) => add(f.name, "flask", null, i, "stuff"));
  Object.values(CM.ELIXIRS).forEach((e, i) => add(e.name, "elixir", null, i, "stuff"));
  [["Field Kit", "kit"], ["Salve", "salve"], ["Dwarven Bread", "bread"], ["Liniment", "liniment"], ["Blade Poison", "oil"],
    ["Lockpick", "lockpick"], ["Master Pick", "lockpick"], ["Trap Kit", "trapkit"], ["Trap Parts", "trapparts"], ["Door Bar", "bar"], ["Bait", "bait"], ["Poisoned Bait", "bait"], ["Grapnel", "grapnel"], ["Dwarven Pick", "pick"]].forEach(([n, k], i) => add(n, k, null, 30 + i, "stuff"));
  Object.keys(CM.MEALS).forEach((kind, i) => add(`${kind} meat`, "meat", null, i, "ingredient"));
  [["Lesser Healing Potion", "heal"], ["Full Healing Potion", "heal"], ["Lesser Mana Potion", "mana"], ["Greater Mana Potion", "mana"], ["Lesser Phoenix Feather", "revive0"], ["Lamp Oil", "lampoil"], ["Glow Stone", "glowstone"], ["Essence", "essence"]].forEach(([n, k], i) => add(n, k, null, 20 + i, "stuff"));
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
  if (item.named) return item.named;
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

// ---- the belt, and things to drink, read and throw ----
CM.BELT_SIZE = 4;
CM.flask = (kind) => ({ name: CM.FLASKS[kind].name, kind: "flask", flask: kind, power: 0, value: 45 });
CM.elixir = (kind) => ({ name: CM.ELIXIRS[kind].name, kind: "elixir", elixir: kind, power: 0, value: 110 });
CM.lampOil = () => ({ name: "Lamp Oil", kind: "lampoil", power: CM.LANTERN_OIL, value: 25 });
CM.glowStone = () => ({ name: "Glow Stone", kind: "glowstone", power: 0, value: 200 });
CM.healPotion = function (floor) {                                        // the potion of the depth: lesser, healing, greater, full
  const t = CM.POTION_TIERS.slice().reverse().find((x) => floor >= x[0]) || CM.POTION_TIERS[0];
  return t[1] === "Greater Healing Potion" ? { name: t[1], kind: "greaterheal", power: 2 * (20 + floor * 3), value: t[3] } : { name: t[1], kind: "heal", power: t[1] === "Full Healing Potion" ? 999 : t[2] + floor * 3, value: t[3] };
};
CM.manaPotion = (floor) => (floor < 6 ? { name: "Lesser Mana Potion", kind: "mana", power: 8 + floor, value: 15 } : floor < 21 ? { name: "Mana Potion", kind: "mana", power: 12 + floor, value: 25 } : { name: "Greater Mana Potion", kind: "mana", power: 30 + floor, value: 60 });
CM.lesserFeather = () => ({ name: "Lesser Phoenix Feather", kind: "revive0", power: 0, value: 60 });
CM.BELT_KINDS = ["salve", "bread", "liniment", "heal", "greaterheal", "mana", "revive", "revive0", "antidote", "bomb", "flask", "elixir", "scroll", "wand", "ration", "torch", "lampoil"];

// ---- living items: charged powers on the relics, trinkets, weapons that grow and can be named, heirlooms with memory ----
CM.RELIC_POWERS = {
  "Rat King's Crown": { id: "swarm", name: "Call the swarm", where: "fight", what: "the rats pour out for you: every foe bitten" },
  "Shield of the Drowned": { id: "tide", name: "Raise the water", where: "fight", what: "the hall floods: water underfoot, and every foe chilled" },
  "Forge-Warden's Hammer": { id: "break", name: "Break the armour", where: "fight", what: "the chosen foe's defence is halved" },
  "The Queen's Ring": { id: "lull", name: "Her song", where: "fight", what: "half the room sleeps" },
  "Sporecap Helm": { id: "still", name: "Think it still", where: "fight", what: "the chosen foe is held two turns" },
  "Prism Amulet": { id: "prism", name: "Turn the light", where: "fight", what: "the next blow on each hero does half" },
  "Ember Mail": { id: "reforge", name: "Reforge on the spot", where: "both", what: "the wearer's weapon takes an edge for the floor (+2)" },
  "Patriarch's Reliquary": { id: "unlock", name: "The key that is not", where: "floor", what: "the nearest locked door on the floor opens" },
  "First Root": { id: "regrow", name: "Regrow", where: "both", what: "a fallen hero rises, to one health" },
};
CM.powerOf = (item) => (item && !item.unknown ? CM.RELIC_POWERS[CM.baseIdOf(item)] || null : null);
// twenty small strange things, one passive oddity each (most through props the rules already read)
CM.TRINKETS = {
  rattooth: { name: "A rat's tooth", what: "never ambushed by rats", props: { ratproof: true } },
  belltongue: { name: "The bell's tongue", what: "the last bell's note when a guardian gathers itself", props: { belltongue: true } },
  spoon: { name: "A cook's spoon", what: "a ration feeds a hundred steps further", props: { spoon: true } },
  tallystick: { name: "Tamsin's tally stick", what: "5% more experience", props: { xpBonus: 0.05 } },
  chalk: { name: "A child's chalk", what: "the floor's carving marked on the map as you arrive", props: { chalk: true } },
  lodestone: { name: "A lodestone", what: "the way down marked on the map as you arrive", props: { lodestone: true } },
  dowsingtwig: { name: "A dowsing twig", what: "the floor's gathering marked on the map as you arrive", props: { dowsing: true } },
  knucklebones: { name: "Knucklebones", what: "+1 Luck", props: { stats: { luck: 1 } } },
  hourglass: { name: "A cracked hourglass", what: "+3 to the first round's order", props: { hourglass: true } },
  mirrorshard: { name: "A mirror shard", what: "the first blow on the wearer each fight does half", props: { mirror: true } },
  thimble: { name: "A thimble", what: "a chest's trap never springs on the wearer", props: { thimble: true } },
  whetstone: { name: "A whetstone", what: "+1 to the wearer's blows", props: { power1: 1 } },
  bootlace: { name: "A lucky bootlace", what: "+1 to the round's order", props: { init: 1 } },
  emberstone: { name: "An ember stone", what: "proof against fire", props: { resist: "fire" } },
  coldcoin: { name: "A cold coin", what: "10% more gold from a fight", props: { killGold: 0.1 } },
  sewingkit: { name: "A sewing kit", what: "mends 1 a round in fights", props: { regen: 1 } },
  steadyhand: { name: "A steady-hand charm", what: "blows land 5% more", props: { hitBonus: 0.05 } },
  hearthstone: { name: "A hearth stone", what: "the whole party +1 defence", props: { auraDf: 1 } },
  wick: { name: "A long wick", what: "the torch burns slower", props: { torchSave: true } },
  sharpeye: { name: "A hawk's eye", what: "weak spots found 5% more", props: { crit: 0.05 } },
};
CM.trinket = (id) => ({ name: CM.TRINKETS[id].name, kind: "trinket", slot: "trinket", trinket: id, power: 0, value: 150, props: Object.assign({ rarity: "fine" }, JSON.parse(JSON.stringify(CM.TRINKETS[id].props))) });
Object.entries(CM.TRINKETS).forEach(([id, t], i) => { CM.BASES[t.name] = { id: t.name, kind: "trinket", slot: "trinket", tier: i, group: "trinket", trinket: id }; });
CM.GROUP_NAMES.trinket = "Trinkets";
// a weapon's marks: a guardian slain, or a hundred of anything; at three it may be named
// the tools of the seventh phase: picks for locks, a kit for traps, a bar for a door, bait, a grapnel, the dwarves' pick
CM.lockpick = (master) => (master ? { name: "Master Pick", kind: "lockpick", master: true, power: 0, value: 150 } : { name: "Lockpick", kind: "lockpick", power: 0, value: 25 });
CM.trapKit = () => ({ name: "Trap Kit", kind: "trapkit", power: 0, value: 120 });
CM.trapParts = (trap) => ({ name: "Trap Parts", kind: "trapparts", trap, power: 0, value: 30 });
CM.bar = () => ({ name: "Door Bar", kind: "bar", power: 0, value: 30 });
CM.bait = (poisoned) => (poisoned ? { name: "Poisoned Bait", kind: "bait", poisoned: true, power: 0, value: 25 } : { name: "Bait", kind: "bait", power: 0, value: 15 });
CM.grapnel = () => ({ name: "Grapnel", kind: "grapnel", power: 0, value: 80 });
CM.dwarfPick = () => ({ name: "Dwarven Pick", kind: "pick", power: 0, value: 150 });
// a lock's grade, by the seed and where it is: common above floor 6; iron two in five below; dwarven one in four from the palace down
CM.lockGrade = (seed, floor, k) => { if (floor < 6) return "common"; const r = CM.hashSeed(`${seed}:lock:${floor}:${k}`) % 100; return floor >= 16 && r < 25 ? "dwarven" : r < 65 ? "iron" : "common"; };
CM.MARK_KILLS = 100;
CM.MARKS_TO_NAME = 3;
