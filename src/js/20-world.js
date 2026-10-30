"use strict";
// The world: items, monster groups, a new party - and a floor: rooms joined by corridors (Nystrom's rooms-and-mazes),
// a few set-piece rooms dropped in, then the dungeon's furniture: doors (some locked, their keys somewhere before
// them), secret doors on the shortcuts, pits and hidden trapdoors, teleporter pairs, spinners, a dark room, a
// fountain, an altar, a gate with its lever, a carving telling the Lich King's story, chests and monsters, the stairs
// up where you arrive and the ladder down as far from them as the floor allows. Pure functions of a Random, so a seed
// gives the same dungeon every time; CM.solvable proves each floor can be finished before it's handed over.

// ---- the hoard ------------------------------------------------------------------------------------------------------
// An item: {name, kind, power, value} and, for gear, slot and perhaps props {bonus, element, resist, stat, df, cursed,
// twohanded, bow, weight}; found gear may be unknown (its props and bonus hidden) until it's worn or identified.
CM.tierFor = (floor, rnd) => CM.clamp(Math.floor((floor + rnd.int(-2, 2)) * 12 / 21), 0, 11);

CM.makeGear = function (kind, floor, rnd) {
  const tier = CM.tierFor(floor, rnd), props = {};
  let name, power, value, slot = kind;
  if (kind === "weapon") {
    if (rnd.chance(0.12)) { const bt = Math.min(CM.BOWS.length - 1, Math.floor(tier / 2.5)); name = CM.BOWS[bt]; props.bow = true; props.twohanded = true; power = (bt + 1) * 3 + 1 + rnd.int(0, 2); value = 20 * (bt + 1) * (bt + 1); }
    else {
      const roll = rnd.int(0, 2);                                        // (the one draw the old list made: the generators' dice must not move)
      const other = (tier * 7 + roll * 5 + floor) % 3 === 0;             // an arm of another class, a third of the time, by the draws already made
      if (other) {
        const classes = Object.keys(CM.ARMS_MORE), cls = classes[(tier * 3 + roll + floor) % classes.length], list = CM.ARMS_MORE[cls], pick = list.reduce((best, x) => (Math.abs(x[1] - tier) < Math.abs(best[1] - tier) ? x : best), list[0]);
        name = pick[0]; const t2 = pick[1]; power = (t2 + 1) * 2 + roll; value = 15 * (t2 + 1) * (t2 + 1); if (["Maul", "Halberd", "Glaive"].includes(name)) props.twohanded = true;
      } else { name = CM.WEAPONS[tier]; power = (tier + 1) * 2 + roll; value = 15 * (tier + 1) * (tier + 1); if (CM.TWO_HANDED.includes(name)) props.twohanded = true; }
    }
    props.base0 = name;                                                  // (the base, before the element's prefix goes on the name)
    if (floor >= 3 && rnd.chance(0.2)) { props.element = rnd.pick(Object.keys(CM.ELEMENTS)); name = `${CM.ELEMENTS[props.element].prefix} ${name}`; value += 60; }
  } else if (kind === "armor") {
    name = CM.ARMORS[tier]; power = tier + 1 + rnd.int(0, 2); value = 15 * (tier + 1) * (tier + 1); props.weight = CM.ARMOR_WEIGHT(tier);
  } else if (kind === "shield") {
    const st = Math.min(CM.SHIELDS.length - 1, Math.floor(tier / 2)); name = CM.SHIELDS[st]; power = st + 1; value = 20 * (st + 1) * (st + 1); slot = "offhand";
  } else if (kind === "helm") {
    const ht = Math.min(CM.HELMS.length - 1, Math.floor(tier / 2)); name = CM.HELMS[ht]; power = ht + 1; value = 15 * (ht + 1) * (ht + 1);
  } else if (kind === "ring") {
    const stat = rnd.pick(CM.STATS); props.stat = stat; power = 1 + Math.floor(tier / 4); name = `${CM.RINGS[stat]} +${power}`; value = 80 * power * power;
  } else if (kind === "amulet") {
    const a = rnd.pick(CM.AMULETS); name = a.name; power = 0; value = 140;
    if (a.resist) props.resist = a.resist;
    if (a.df) { props.df = a.df; power = a.df; }
  } else if (kind === "boots") {
    const b = CM.BOOTS[Math.min(CM.BOOTS.length - 1, Math.floor(tier / 1.7))]; name = b.name; power = b.power; value = 40 * (power + 1) * (power + 1);
    if (b.silence) props.silence = true;
    if (b.waterwalk) props.waterwalk = true;
  } else if (kind === "cloak") {
    const c = CM.CLOAKS[Math.min(CM.CLOAKS.length - 1, Math.floor(tier / 1.7))]; name = c.name; power = c.df; props.df = c.df; value = 40 * (power + 1) * (power + 1);
    if (c.hood) props.hood = true;
  }
  if ((kind === "weapon" || kind === "armor" || kind === "shield" || kind === "helm") && rnd.chance(0.15)) { props.bonus = 1; power += 2; value += 40; }
  if (floor >= 4 && (kind === "weapon" || kind === "armor") && rnd.chance(0.08)) { props.cursed = true; power = Math.max(1, power - 3); value = Math.floor(value / 3); }
  const item = { name, base: props.base0 || name, kind: slot === "offhand" ? "shield" : kind, slot, power, value, props };
  delete props.base0;
  const imp = CM.implicitFor(item); if (imp) { CM.applyProps(item, imp); props.implicit = true; }
  if (props.cursed) {                                                    // cursed: hidden until worn, a cost, and a tier-III word (CM.affix)
    item.unknown = true;
    const kinds = Object.keys(CM.CURSES); props.curse = kinds[(tier * 5 + power + floor) % kinds.length];
    if (props.curse === "weak") { const st = CM.CLASSES.Knight ? ["str", "dex", "int", "wis"][(tier + floor) % 4] : "str"; props.stats = props.stats || {}; props.stats[st] = (props.stats[st] || 0) - 2; }
    props.rarity = "cursed";
  }
  if (floor >= 2 && rnd.chance(0.5)) item.unknown = true;
  return item;
};

// an affix or two on a weapon or a piece of armour, by the floor: fine (one) from the third floor, rare (two) from the
// eighth; the deeper pools open below the Lich King. Drawn from its own dice (a hash, in the generator) so the floors
// stay as they were. Returns the item.
CM.affix = function (item, floor, rnd) {
  if (!["weapon", "armor", "shield", "helm"].includes(item.kind) || (item.props || {}).relic || (item.props || {}).unique) return item;
  const fine = floor >= 3 ? 0.18 + Math.min(0.17, floor * 0.005) : 0, rare = floor >= 8 ? 0.05 + Math.min(0.15, (floor - 8) * 0.004) : 0;
  const roll = rnd.next();
  const n = (item.props || {}).cursed ? Math.max(1, roll < rare ? 2 : roll < rare + fine ? 1 : 0) : roll < rare ? 2 : roll < rare + fine ? 1 : 0;   // (a cursed thing always has its word)
  if (!n) return item;
  const deep = floor > CM.LAST_FLOOR, p = item.props = item.props || {}, tier = p.cursed ? 3 : CM.affixTier(floor);
  const pool = (table) => Object.entries(table).filter(([, a]) => (!a.deep || deep) && (!a.weapon || item.kind === "weapon") && !(a.element && p.element));
  const kinds = n === 2 ? ["prefix", "suffix"] : [rnd.chance(0.5) ? "prefix" : "suffix"];
  const words = [];
  for (const where of kinds) {
    const table = where === "prefix" ? CM.AFFIXES.prefix[item.kind === "weapon" ? "weapon" : "armor"] : CM.AFFIXES.suffix;
    const choices = pool(table);
    if (!choices.length) continue;
    const [word, a] = rnd.pick(choices);
    words.push([where, word]);
    CM.applyProps(item, CM.scaledAffix(a, tier));
    item.value += (where === "prefix" ? 60 : 90) * tier;
  }
  if (!words.length) return item;
  p.tier = tier;
  p.rarity = p.cursed ? "cursed" : words.length === 2 ? "rare" : "fine";
  p.affixes = words.map(([, w]) => w);
  const prefix = words.find(([w]) => w === "prefix"), suffix = words.find(([w]) => w === "suffix");
  item.name = `${p.element && !CM.ELEMENTS[p.element] ? "" : ""}${prefix ? prefix[1] + " " : ""}${p.element ? CM.ELEMENTS[p.element].prefix + " " : ""}${item.base || CM.baseName(item)}${suffix ? " " + suffix[1] : ""}${p.bonus ? ` +${p.bonus}` : ""}`;
  return item;
};
CM.makeUnique = function (id, awake) {
  const u = CM.UNIQUES[id];
  const item = { name: u.name, base: u.name, kind: u.kind, slot: u.slot, power: u.power, value: u.value, props: Object.assign({ unique: id, rarity: "unique" }, JSON.parse(JSON.stringify(u.props))) };
  if (awake) { item.name = u.name + ", Awake"; item.props.awake = true; item.props.regen = (item.props.regen || 0) + 1; item.props.crit = (item.props.crit || 0) + 0.05; item.power += 2; item.value *= 2; }   // (an Awakened run: a second power in each)
  return item;
};
CM.ration = () => ({ name: "Ration", kind: "ration", power: 0, value: 15 });
CM.ingredient = (id) => ({ name: CM.INGREDIENTS[id].name, kind: "ingredient", ingredient: id, power: 0, value: 25 });
CM.oil = (element) => ({ name: { fire: "Oil of Fire", frost: "Oil of Rime", holy: "Oil of Saints", poison: "Blade Poison", storm: "Oil of Storms", venom: "Oil of Venom", shadow: "Oil of Shadow" }[element], kind: "oil", element, power: 0, value: 60 });
CM.bomb = () => ({ name: "Firepot", kind: "bomb", power: 0, value: 80 });
CM.scrap = () => ({ name: "Scrap", kind: "scrap", power: 0, value: 5 });
// the rarity of a thing, for its colour: common, fine, rare, relic, unique
CM.rarityOf = (item) => (item && item.props && !item.unknown ? (item.props.unique ? "unique" : item.props.relic ? "relic" : item.props.cursed ? "cursed" : item.props.set ? "fine" : item.props.rarity || "common") : "common");

CM.scroll = (id) => ({ name: CM.SCROLLS[id].name, kind: "scroll", spell: id, power: 0, value: 40 });
CM.wand = (id, charges) => ({ name: CM.WANDS[id].name, kind: "wand", spell: id, power: 0, charges, value: 90 });

CM.makeItem = function (floor, rnd, kind, gen) {
  kind = kind || rnd.pick(gen >= 2 ? ["weapon", "weapon", "weapon", "armor", "armor", "armor", "potion", "potion", "potion", "potion", "potion",
    "shield", "helm", "ring", "amulet", "scroll", "scroll", "wand", "boots", "cloak"] : ["weapon", "weapon", "weapon", "armor", "armor", "armor", "potion", "potion", "potion", "potion", "potion",
    "shield", "helm", "ring", "amulet", "scroll", "scroll", "wand"]);
  if (kind === "potion") {
    const roll = rnd.next();
    if (roll < 0.12) return { name: "Phoenix Feather", kind: "revive", power: 0, value: 120 };
    if (roll < 0.4) return { name: "Mana Potion", kind: "mana", power: 12 + floor, value: 25 };
    if (roll < 0.52) return CM.torch();
    if (roll < 0.62) return CM.antidote();
    return { name: "Healing Potion", kind: "heal", power: 20 + floor * 3, value: 20 };
  }
  if (kind === "scroll") return CM.scroll(rnd.pick(Object.keys(CM.SCROLLS)));
  if (kind === "wand") return CM.wand(rnd.pick(Object.keys(CM.WANDS)), rnd.int(3, 5));
  return CM.makeGear(kind, floor, rnd);
};

// the base of a thing's name, as it looks before it's known: no prefix, no plus
CM.baseName = function (item) {
  if (item.base) return item.base;
  let n = item.name.replace(/ \+\d+$/, "");
  for (const e of Object.values(CM.ELEMENTS)) if (n.startsWith(e.prefix + " ")) n = n.slice(e.prefix.length + 1);
  return n;
};

// what an item is, in words
CM.itemLabel = function (item) {
  if (item.unknown) return "unknown: wear it, read a Scroll of Identify, or ask the camp's scribe";
  const p = item.props || {}, bits = [];
  if (item.kind === "weapon") bits.push(`weapon +${item.power}`, p.bow || p.fists ? "" : `${CM.WEAPON_CLASSES[CM.weaponClass(item)].name}: ${CM.WEAPON_CLASSES[CM.weaponClass(item)].what}`);
  else if (item.kind === "armor") bits.push(`armour +${item.power}`, p.weight || "");
  else if (item.kind === "shield") bits.push(`shield +${item.power}`, `blocks ${Math.round(CM.blockChance(Object.assign({}, item, { unknown: false })) * 100)}% of blows for half${CM.isTower(item) ? ", and for the row behind" : ""}`);
  else if (item.kind === "helm") bits.push(`helm +${item.power}`);
  else if (item.kind === "ring") bits.push(`+${item.power} ${CM.STAT_NAMES[p.stat]}`);
  else if (item.kind === "amulet") bits.push(p.resist ? `proof against ${p.resist}` : `warding +${p.df}`);
  else if (item.kind === "boots") bits.push(`speed +${item.power}`, p.silence ? "silent: the party is never surprised" : "", p.waterwalk ? "dry feet: water costs the torch nothing" : "");
  else if (item.kind === "cloak") bits.push(`warding +${p.df}`, p.hood ? "a hood: no surprise in the dark" : "");
  else if (item.kind === "ration") bits.push("a meal: the party eats, and is not hungry for a while");
  else if (item.kind === "scroll") bits.push(CM.SCROLLS[item.spell].what + (item.back ? ` (It remembers floor ${item.back.floor}.)` : ""));
  else if (item.kind === "flask") bits.push(`thrown, from any row: ${CM.FLASKS[item.flask].what}`);
  else if (item.kind === "elixir") bits.push(CM.ELIXIRS[item.elixir].what);
  else if (item.kind === "lampoil") bits.push(`fills the lantern: ${CM.LANTERN_OIL} steps of slow burning`);
  else if (item.kind === "glowstone") bits.push("a light that never goes out, and does not reach far");
  else if (item.kind === "revive0") bits.push("raises a fallen hero to half, once a floor");
  else if (item.kind === "wand") bits.push(`${CM.WANDS[item.spell].what} ${CM.plural(item.charges, "charge")}.`);
  else if (item.kind === "tome") bits.push(`teaches ${CM.ABILITIES[item.spell].name} to a caster who reads it: ${CM.ABILITIES[item.spell].what}`);
  else if (item.kind === "gem") bits.push(CM.GEMS[item.gem].element ? `for the camp's smith: ${CM.GEMS[item.gem].element} set into a weapon` : "for the camp's smith: +1 on a piece of gear");
  else if (item.kind === "ingredient") bits.push(CM.INGREDIENTS[item.ingredient] && CM.INGREDIENTS[item.ingredient].rare ? "a rare thing, gathered, for the alchemist's finer work" : `for the camp's alchemist`);
  else if (item.kind === "meat") bits.push(`cooked at a camp (or on the floor, for a torch): ${CM.MEALS[item.meat] ? CM.MEALS[item.meat].what + ", the next floor" : "a meal"}`);
  else if (item.kind === "kit") bits.push("the alchemist's work, anywhere: brew on the floor at a fifth over the camp's price");
  else if (item.kind === "salve") bits.push("rubbed in: the party mends a little every few steps, this floor");
  else if (item.kind === "bread") bits.push("a meal that also mends twenty");
  else if (item.kind === "liniment") bits.push("closes a wound and the small ailments, and mends ten");
  else if (item.kind === "oil") bits.push(`rubbed on a hero's weapon: ${CM.ELEMENT_NAMES[item.element] || item.element} for ${CM.OIL_FIGHTS} fights`);
  else if (item.kind === "bomb") bits.push("thrown in a fight: fire on every foe");
  else if (item.kind === "scrap") bits.push("for the camp's smith: five stand in for a diamond");
  else if (item.kind === "essence") bits.push(`what worded things leave in the fire: ${item.power} - three stand in for a gem at the smith's rework`);
  else if (item.kind === "greaterheal") bits.push(`heals ${item.power}`);
  if (p.stat && item.kind !== "ring") bits.push(`+${item.power} ${CM.STAT_NAMES[p.stat]}`);
  if (p.stats) for (const [st, d] of Object.entries(p.stats)) bits.push(`${d > 0 ? "+" : ""}${d} ${CM.STAT_NAMES[st]}`);
  if (p.resist && item.kind !== "amulet") bits.push(`proof against ${p.resist}`);
  if (p.df && item.kind !== "amulet") bits.push(`warding +${p.df}`);
  if (p.element) bits.push(p.element);
  if (p.crit) bits.push(`weak spots found ${Math.round(p.crit * 100)}% more`);
  if (p.regen) bits.push(`mends ${p.regen} a round`);
  if (p.lifesteal) bits.push("feeds on every blow");
  if (p.sleep) bits.push("a blow may put the foe to sleep");
  if (p.thorns) bits.push(`whoever strikes the wearer takes ${p.thorns}`);
  if (p.stun) bits.push("a blow may leave the foe reeling");
  if (p.twohanded) bits.push("two-handed");
  if (p.relic) bits.push("a guardian's relic");
  if (p.heirloom) bits.push("an heirloom thrice borne: worn as a relic");
  if (p.element && CM.ELEMENT_WORDS[p.element] && ["storm", "venom", "shadow"].includes(p.element)) bits.push(`${CM.ELEMENT_NAMES[p.element]}: ${CM.ELEMENT_WORDS[p.element]}`);
  if (item.kind === "oil" && ["storm", "venom", "shadow"].includes(item.element)) bits.push(`${CM.ELEMENT_NAMES[item.element]}: ${CM.ELEMENT_WORDS[item.element]}`);
  if (item.kind === "lockpick") bits.push(item.master ? "opens any lock at the Rogue's chance, a dwarven one too; breaks on a miss" : "anyone may try a lock at a third of the Rogue's chance; breaks on a miss");
  if (item.kind === "trapkit") bits.push("disarms a found plate for its parts (the Artificer never fails); with parts in the pack, sets a trap on the square behind the party");
  if (item.kind === "trapparts") bits.push(`${CM.TRAPS[item.trap] || "a trap"}, in parts: set it behind the party with a trap kit, and a band that walks onto it takes it`);
  if (item.kind === "bar") bits.push("bars the open door beside the party for the floor; used again at a barred door, the party rests there a little (once a floor, a ration)");
  if (item.kind === "bait") bits.push(item.poisoned ? "dropped where you stand: draws the nearest wanderers ten steps, and poisons what eats it" : "dropped where you stand: draws the nearest wanderers for ten steps, and holds them there");
  if (item.kind === "grapnel") bits.push("climbs the party back up the pit it fell down; kept");
  if (item.kind === "pick") bits.push("opens the nearest hidden door or stair on the floor without searching, and breaks");
  if (item.bearers && item.bearers.length) bits.push(`borne by ${item.bearers.join(", ")}`);
  if (CM.powerOf(item)) bits.push(`a power, once a floor: ${CM.powerOf(item).name} - ${CM.powerOf(item).what}`);
  if (item.kind === "trinket" && CM.TRINKETS[item.trinket]) bits.push(CM.TRINKETS[item.trinket].what);
  if (item.marks) bits.push(`${CM.plural(item.marks, "mark")}${item.named ? "" : item.marks >= CM.MARKS_TO_NAME ? " - it may be named" : ""}`);
  if (item.history && item.history.length) bits.push(item.history.join("; "));
  if (p.power1) bits.push(`+${p.power1} to blows`);
  if (p.unique) bits.push("unique: " + CM.UNIQUES[p.unique].lore.replace(/\.$/, ""));
  if (p.bow) bits.push("a bow: the Ranger's");
  if (p.cursed) bits.push(`CURSED${p.curse && CM.CURSES[p.curse] ? ` (${CM.CURSES[p.curse].name}: ${CM.CURSES[p.curse].what})` : ""}`);
  if (p.tier && p.tier > 1) bits.push(`tier ${["", "I", "II", "III"][p.tier]} work`);
  if (p.set && CM.SETS[p.set]) bits.push(`one of ${CM.SETS[p.set].name}: all three worn, ${CM.SETS[p.set].what}`);
  if (p.bleed) bits.push("a blow may open a wound that bleeds");
  if (p.chill) bits.push("a blow may chill the foe");
  if (p.blindHit) bits.push("a blow may blind the foe for its next");
  if (p.vsUndead) bits.push(`${Math.round((p.vsUndead - 1) * 100)}% more against the undead`);
  if (p.vsHide) bits.push(`${Math.round((p.vsHide - 1) * 100)}% more against hide`);
  if (p.underHalf) bits.push(`+${p.underHalf} to blows while under half health`);
  if (p.hitBonus) bits.push(`blows land ${Math.round(p.hitBonus * 100)}% more`);
  if (p.init) bits.push(`${p.init > 0 ? "+" : ""}${p.init} to the round's order`);
  if (p.xpBonus) bits.push(`${Math.round(p.xpBonus * 100)}% more experience`);
  if (p.killGold) bits.push(`${Math.round(p.killGold * 100)}% more gold from a fight`);
  if (p.killHeal) bits.push(`${p.killHeal} health back for every foe slain`);
  if (p.killMana) bits.push(`${p.killMana} magic to the casters for every foe slain`);
  if (p.auraDf) bits.push(`the whole party +${p.auraDf} defence while worn`);
  if (p.torchSave) bits.push("the party's torch burns slower");
  if (p.spellPower) bits.push(`+${p.spellPower} to every spell`);
  if (p.block) bits.push(`blocks ${Math.round(p.block * 100)}% more`);
  if (p.stun0) bits.push("the wearer is never knocked flat");
  if (p.reach) bits.push("reaches the back row from the front");
  return bits.filter(Boolean).join(", ");
};

CM.TORCH_STEPS = 400;                    // a torch burns this many steps
CM.torch = () => ({ name: "Torch", kind: "torch", power: CM.TORCH_STEPS, value: 8 });
CM.lantern = () => ({ name: "Lantern", kind: "lantern", power: 0, value: 150 });
CM.key = () => ({ name: "Iron Key", kind: "key", power: 0, value: 0 });
CM.antidote = () => ({ name: "Antidote", kind: "antidote", power: 0, value: 15 });

// one floor in a run may be special - all water, or all dark, or a labyrinth with something in it - decided by the
// seed, never on a guardian's floor nor near the top or the bottom
CM.specialFor = function (number, seed) {
  if (number > CM.BOTTOM) {                                            // Endless: where the first fifty floors had theirs, of whatever kind the dark dreams
    if (CM.guardianFor(number)) return null;
    const kind = ["wading", "dark", "maze"][CM.hashSeed(`${seed}:special:endless:${number}`) % 3];
    return CM.specialFor(((number - 1) % CM.BOTTOM) + 1, seed) ? kind : null;
  }
  if (CM.guardianFor(number) || number <= 2 || number === CM.LAST_FLOOR - 1 || number === CM.LAST_FLOOR || number >= CM.BOTTOM - 1) return null;
  const h = (what, n) => CM.hashSeed(`${seed}:special:${what}:${n}`);
  if (number > CM.LAST_FLOOR) {                                        // the Deep has its own: a flooded street, a labyrinth of the forges, the ossuary's dark
    const wading = 21 + h("wading2", 0) % 4, maze = 36 + h("maze2", 0) % 4, dark = [41, 42, 43, 44, 46, 47][h("dark2", 0) % 6];
    if (number === wading && h("wading2", 1) % 10 < 7) return "wading";
    if (number === maze && h("maze2", 1) % 10 < 7) return "maze";
    if (number === dark && h("dark2", 1) % 10 < 6) return "dark";
    return null;
  }
  const wading = 7 + h("wading", 0) % 3, maze = 11 + h("maze", 0) % 4, dark = [3, 4, 12, 13, 14, 17, 18][h("dark", 0) % 7];
  if (number === wading && h("wading", 1) % 10 < 7) return "wading";
  if (number === maze && h("maze", 1) % 10 < 7) return "maze";
  if (number === dark && dark !== maze && h("dark", 1) % 10 < 6) return "dark";
  return null;
};
CM.SPECIALS = {
  wading: { name: "a flooded floor", note: "The whole floor is under water, knee-deep and cold. You wade, and the torch gutters in the damp." },
  dark: { name: "a dark floor", note: "No torch reaches far here: a dark lies over this whole floor like water. Only a conjured Light cuts through it." },
  maze: { name: "a labyrinth", note: "No rooms, no doors: a labyrinth of narrow ways. Something in it has your scent." },
};
CM.rope = () => ({ name: "Rope", kind: "rope", power: 0, value: 30 });
CM.tome = (id) => ({ name: CM.TOMES[id], kind: "tome", spell: id, power: 0, value: 160 });
CM.gem = (id) => ({ name: CM.GEMS[id].name, kind: "gem", gem: id, power: 0, value: 150 });
CM.isCaster = (h) => Boolean((CM.CLASSES[h.cls] || {}).mp);
CM.bones = (ghost) => ({ name: "Someone's bones", kind: "bones", power: 0, value: 0, ghost });

// one monster of a kind, at a depth - with what the kind does carried on it, so a save stands alone
CM.makeMonster = function (kind, level, rnd) {
  const sh = kind.shape || [1, 1, 1], hp = Math.max(1, Math.round((8 + level * 6) * sh[0]));
  const m = { name: kind.name, kind: kind.name, colour: kind.colour, hp, max: hp, atk: Math.max(1, Math.round((3 + level * 2) * sh[1])), df: Math.max(0, Math.round(level * sh[2])),
    xp: 10 + level * 8, gold: rnd.int(2, 8) * level, speed: kind.speed || 10, undead: Boolean(kind.undead), ability: kind.ability || null,
    touch: kind.touch ? Object.assign({}, kind.touch) : null, row: kind.row || "front" };
  if (kind.rival) CM.armMonster(m, level);                               // (a rival's person comes armed; an elite is armed in makeElite)
  return m;
};
// a loadout, by the kind's table and a hash of the monster (no dice of the floor's are spent): the weapon, and a shield
CM.armMonster = function (m, level) {
  const L = CM.LOADOUTS[m.kind || m.name]; if (!L || m.gear) return m;
  const rnd = new CM.Random(CM.hashSeed(`arms:${m.name}:${level}:${m.max}:${m.gold}`)), floor = Math.max(1, level);
  const weapon = CM.makeGear("weapon", floor, rnd); const B = CM.BASES[L.weapon];
  if (B) { weapon.name = L.weapon; weapon.base = L.weapon; weapon.props = Object.assign({}, weapon.props || {}, { twohanded: Boolean(B.twohanded) }); delete weapon.props.element; delete weapon.props.base0; weapon.unknown = false; weapon.power = Math.max(1, Math.round(2 + floor * 0.8)); weapon.value = 20 + floor * 6; }
  m.gear = { weapon };
  if (L.shield) { const shield = CM.makeGear("shield", floor, rnd); shield.unknown = false; m.gear.offhand = shield; }
  m.atk += 1;
  return m;
};
// a part with its own health, for the kinds that have one (CM.PARTS): set when the fight begins (tune), so a save before knows nothing of it
CM.setPart = function (m) {
  const P = CM.PARTS[m.boss ? "Lich King" : m.kind || m.name]; if (!P || m.part !== undefined) return m;
  m.part = { name: P.name, hp: Math.max(1, Math.round(m.max * P.share)), max: Math.max(1, Math.round(m.max * P.share)), loses: P.loses, drop: P.drop, broken: false };
  return m;
};

// a monster saved before it knew what it does
CM.upgradeMonster = function (m) {
  if (m.kind) return m;
  const kind = CM.monsterKind(m.name);
  m.kind = kind ? kind.name : m.name;
  if (kind) { m.speed = kind.speed || 10; m.undead = Boolean(kind.undead); m.ability = kind.ability || null; m.touch = kind.touch ? Object.assign({}, kind.touch) : null; m.row = kind.row || "front"; }
  else { m.speed = m.speed || (m.boss ? 12 : 10); m.undead = Boolean(m.undead || m.boss); m.ability = m.ability || null; m.touch = m.touch || null; }
  return m;
};

// a group: one kind, or (deeper down) two; now and then with a leader out of the ordinary
CM.monsterGroup = function (floor, rnd, gen) {
  if (floor > CM.LAST_FLOOR) return CM.deepGroup(floor, rnd, gen);
  const top = Math.min(CM.SHALLOW - 1, Math.floor(floor * CM.SHALLOW / CM.LAST_FLOOR));
  const kind = CM.MONSTERS[rnd.int(Math.max(0, top - 2), top)];
  const count = rnd.int(1, 2 + Math.floor(floor / 6));
  const group = [];
  for (let i = 0; i < count; i++) group.push(CM.makeMonster(kind, floor, rnd));
  if (floor >= 4 && count >= 2 && rnd.chance(0.35)) {                   // mixed company: the second kind, a step down
    const other = CM.MONSTERS[Math.max(0, CM.MONSTERS.indexOf(kind) - rnd.int(1, 2))];
    if (other !== kind) for (let i = Math.floor(count / 2); i < count; i++) group[i] = CM.makeMonster(other, floor, rnd);
  }
  if (floor >= 3 && rnd.chance(0.12)) CM.makeElite(group, rnd, gen);
  return group;
};
// a band of the Deep: the kinds of this depth's band (now and then one of the band above), two to five of them, and a
// leader one time in five; their level climbs more slowly than the floors do (CM.monsterLevel)
CM.deepGroup = function (floor, rnd, gen) {
  const band = CM.themeIndex(floor), level = CM.monsterLevel(floor);
  const here = CM.MONSTERS.filter((m) => m.deep === band), above = CM.MONSTERS.filter((m) => m.deep === band - 1);
  const shallow = floor > CM.BOTTOM && !here.length ? CM.MONSTERS.slice(band * 4, Math.min(CM.SHALLOW, band * 4 + 5)) : [];   // (Endless: the first bands come round with their own kinds)
  const kinds = here.length ? here : shallow.length ? shallow : CM.MONSTERS.filter((m) => m.deep);
  const kind = rnd.pick(kinds), count = rnd.int(2, 4 + (floor >= 36 ? 1 : 0) + (floor > CM.BOTTOM ? 1 : 0));
  const group = [];
  for (let i = 0; i < count; i++) group.push(CM.makeMonster(kind, level, rnd));
  if (count >= 3 && rnd.chance(0.4)) {
    const other = rnd.pick(above.length && rnd.chance(0.4) ? above : kinds);
    if (other !== kind) for (let i = Math.floor(count / 2); i < count; i++) group[i] = CM.makeMonster(other, level, rnd);
  }
  if (rnd.chance(floor > CM.BOTTOM ? 0.3 : 0.2)) CM.makeElite(group, rnd, gen);
  return group;
};
CM.makeElite = function (group, rnd, gen) {
  {
    const table = gen >= 2 ? Object.assign({}, CM.ELITES, CM.ELITES_MORE) : CM.ELITES;
    const id = rnd.pick(Object.keys(table)), e = table[id], m = group[0];
    m.name = `${e.name} ${m.name}`;
    m.elite = id;
    if (e.hp) { m.max = Math.round(m.max * e.hp); m.hp = m.max; }
    if (e.atk) m.atk += e.atk;
    if (e.df) m.df += e.df;
    if (e.speed) m.speed += e.speed;
    if (e.touch) m.touch = Object.assign({}, e.touch);
    if (e.ability) m.ability = e.ability;
    m.xp = Math.round(m.xp * (e.xp || 1.5));
    m.gold *= 2;
    CM.armMonster(m, Math.max(1, Math.round(m.max / 6)));
  }
  return group;
};

CM.bossMonster = () => ({ name: CM.BOSS.name, kind: CM.BOSS.name, colour: CM.BOSS.colour, hp: 650, max: 650, atk: 46, df: 18, xp: 5000, gold: 5000,
  boss: true, speed: 12, undead: true, ability: null, touch: { status: "curse", chance: 0.2 } });
CM.skeleton = (level, rnd) => CM.makeMonster(CM.MONSTERS[2], level, rnd);

// a guardian (CM.GUARDIANS), ready to fight, with the company it keeps; and the relic it leaves behind
// a guardian over its shaft - or, below the bottom (Endless), its echo: the same thing, grown to the depth (this floor's
// monster level against its own floor's), that leaves nothing behind when it falls
CM.guardianMonster = function (id, floor) {
  const G = CM.GUARDIANS[id], echo = floor ? CM.echoOf(floor) : 0, k = echo ? CM.monsterLevel(floor) / CM.monsterLevel(G.floor) : 1;
  return { name: echo ? `${G.name}'s Echo` : G.name, kind: G.name, colour: G.colour, hp: Math.round(G.hp * k), max: Math.round(G.hp * k), atk: Math.round(G.atk * k), df: Math.round(G.df * Math.sqrt(k)),
    xp: Math.round(G.xp * k), gold: Math.round(G.gold * k), guardian: id, echo, speed: G.speed, undead: Boolean(G.undead), ability: null, touch: G.touch ? Object.assign({}, G.touch) : null, turns: 0 };
};
CM.guardianGroup = function (id, floor, rnd) {
  const group = [CM.guardianMonster(id, floor)], level = floor > CM.BOTTOM ? CM.monsterLevel(floor) : floor;
  for (const name of CM.GUARDIANS[id].escorts || []) group.push(CM.makeMonster(CM.monsterKind(name), level, rnd));
  return group;
};
// a named weapon from the compendium, made again for a later party: its base, its marks, and its story so far
CM.namedWeapons = CM.namedWeapons || [];
CM.legendWeapon = function (e, floor) {
  const B = CM.BASES[e.base] || CM.BASES["Short Sword"], marks = Math.max(1, (e.history || []).length), props = { rarity: "fine", legend: true };
  if (B.bow) { props.bow = true; props.twohanded = true; } else if (B.twohanded) props.twohanded = true;
  return { name: e.name, named: e.name, base: B.id, kind: "weapon", slot: "weapon", power: (B.tier + 1) * 3 + marks, value: 300 + marks * 100, props, marks,
    history: (e.history || []).concat(`lost by ${e.bearer || "a party before"}, and found again on floor ${floor}`), unknown: false };
};
CM.relic = function (id) {
  const r = CM.GUARDIANS[id].relic;
  return { name: r.name, kind: r.kind, slot: r.slot, power: r.power, value: r.value, props: Object.assign({}, r.props), unknown: false };
};

// ---- heroes: rolled, made, grown ---------------------------------------------------------------------------------------
CM.rollStats = function (cls, rnd) {                                      // three dice a stat, and what the class brings
  rnd = rnd || new CM.Random(Math.floor(Math.random() * 4294967296));
  const bonus = CM.CLASSES[cls].bonus, stats = {};
  for (const s of CM.STATS) stats[s] = CM.clamp(rnd.int(1, 6) + rnd.int(1, 6) + rnd.int(1, 6) + (bonus[s] || 0), 3, 18);
  return stats;
};

CM.mod = (v, per = 2) => Math.floor((v - 10) / per);                     // how a stat tells: 10 is nothing, 16 is +3 (at 2 a point)
// the experience a level asks for: measured so a party fighting its way down is about the monsters' level - 20 on floor
// 20, the middle thirties at the bottom (the old game's 60 * (L-1)^1.6 was for twenty floors, and ran to level 100 by fifty)
CM.xpForLevel = (level) => Math.ceil(20 * (level - 1) + 8 * Math.pow(level - 1, 2.6));

// the numbers a hero fights with, from class, level, stats and boons (health and magic stay where they were, within the new most)
CM.recompute = function (h) {
  const c = CM.CLASSES[h.cls] || CM.CLASSES.Knight, L = h.level - 1, s = {};
  for (const st of CM.STATS) s[st] = CM.heroStat(h, st);                 // (rings count)
  const boons = h.boons || [];
  h.max = Math.max(1, c.hp + (s.con - 10) + L * (c.grow + CM.mod(s.con, 3)));
  h.maxmp = c.mp ? Math.max(0, c.mp + (s[c.key] - 10) + L * 3) : h.second && CM.CLASSES[h.second].mp ? 6 + Math.floor(L / 4) : 0;
  const hitStat = c.key === "dex" ? s.dex : s.str;
  const relics = CM.relicsWorn(h), set = relics >= 2 ? CM.RELIC_SET.two : null;   // (the guardians' things, worn together)
  if (h.cls === "Monk" && h.weapon && h.weapon.props && h.weapon.props.fists) h.weapon.power = 3 + Math.floor(h.level / 2) + 2 * (h.weapon.props.bonus || 0) + (CM.trait(h, "ironfists") ? Math.ceil((3 + Math.floor(h.level / 2)) / 2) : 0);   // (the hands grow; the smith's work and the Heir's kit count double on them)
  h.atk = Math.max(1, c.atk + CM.mod(hitStat) + L * c.atkGrow + (CM.trait(h, "mighty") ? 3 : 0) + (set ? set.atk : 0) + (h.bondAtk || 0));
  h.df = Math.max(0, c.df + CM.mod(s.dex, 3) + Math.floor(L / 2) + (boons.includes("ironskin") ? 2 : 0) + (CM.trait(h, "stonewall") || CM.trait(h, "ironbody") ? 3 : 0) + (set ? set.df : 0) + (h.bondDf || 0) + (CM.setWorn(h) === "masons" ? 3 : 0));
  h.hp = Math.min(h.hp, h.max);
  h.mp = Math.min(h.mp, h.maxmp);
  return h;
};

CM.makeHero = function (cls, name, stats, row, quirk, origin) {
  const c = CM.CLASSES[cls];
  const h = { name: (name || "").trim() || cls, cls, level: 1, xp: 0, hp: 1, max: 1, mp: 0, maxmp: 0, atk: 1, df: 0,
    stats: Object.assign({}, stats || CM.rollStats(cls)), row: row || c.row, status: {}, boons: [], pending: 0, offer: null, path: null, learned: [], quirk: CM.QUIRKS[quirk] ? quirk : null,
    weapon: { name: c.weapon, kind: "weapon", slot: "weapon", power: 1, value: 5, props: c.weapon === "Short Bow" ? { bow: true, twohanded: true } : c.weapon === "Wrapped Fists" ? { fists: true, twohanded: true } : {} },
    armor: { name: c.armor, kind: "armor", slot: "armor", power: 0, value: 5, props: { weight: "light" } },
    offhand: null, helm: null, ring: null, amulet: null, boots: null, cloak: null, trinket: null };
  if (h.quirk) for (const [st, d] of Object.entries(CM.QUIRKS[h.quirk].stats)) h.stats[st] = CM.clamp(h.stats[st] + d, 3, 25);
  h.origin = CM.ORIGINS[origin] ? origin : null;
  if (h.origin === "nobody") h.stats.luck = CM.clamp(h.stats.luck + 1, 3, 25);
  CM.recompute(h);
  h.hp = h.max; h.mp = h.maxmp;
  return h;
};

// a hero saved by an older version gets stats (middling, plus the class's), a row, the empty slots and the rest
CM.upgradeHero = function (h) {
  const c = CM.CLASSES[h.cls] || CM.CLASSES.Knight;
  if (!h.stats) { h.stats = {}; for (const s of CM.STATS) h.stats[s] = 10 + (c.bonus[s] || 0); }
  h.row = h.row || c.row;
  h.status = h.status || {};
  h.boons = h.boons || [];
  h.pending = h.pending || 0;
  h.offer = h.offer || null;
  h.path = h.path || null;
  h.learned = h.learned || [];
  for (const slot of ["offhand", "helm", "ring", "amulet", "boots", "cloak", "trinket"]) if (h[slot] === undefined) h[slot] = null;
  for (const slot of ["weapon", "armor"]) if (h[slot]) { h[slot].props = h[slot].props || {}; h[slot].slot = slot; }
  return h;
};

CM.equipped = (h) => CM.SLOTS.map((s) => h[s]).filter(Boolean);

// a stat as it stands, rings and all
// the party's gear, summed over everyone standing (auras)
CM.partyProp = (party, prop) => (party || []).filter((h) => h.hp > 0).reduce((n, h) => n + CM.gearProp(h, prop), 0);
CM.heroStat = function (h, s) {
  let v = h.stats && h.stats[s] !== undefined ? h.stats[s] : 10;
  if (s === "luck" && h.mealLuck) v += h.mealLuck;                     // (a meal that lasts: rat on a stick, kobold stew)
  for (const it of CM.equipped(h)) {
    if (!it.props || it.unknown) continue;
    if (it.props.stat === s) v += it.power;
    if (it.props.stats && it.props.stats[s]) v += it.props.stats[s];
  }
  return v;
};
// what the gear gives besides: weak spots, mending a round, thorns - summed over what's worn and known
CM.gearProp = (h, prop) => CM.equipped(h).reduce((n, it) => n + (it.props && !it.unknown ? (typeof it.props[prop] === "number" ? it.props[prop] : it.props[prop] === true ? 1 : 0) : 0), 0);   // (a flag counts one: the trinkets' oddities)
CM.relicsWorn = (h) => CM.equipped(h).filter((it) => it.props && (it.props.relic || it.props.heirloom) && !it.unknown).length;   // (an heirloom worn by its third bearer counts)

// what the gear keeps off: armour and shield count double, a helm and a warding amulet once
CM.gearDefence = (h) => (h.armor ? h.armor.power : 0) * 2 + (h.offhand ? h.offhand.power * 2 : 0) + (h.helm ? h.helm.power : 0) + (h.cloak && h.cloak.unknown ? h.cloak.power : 0)
  + CM.equipped(h).reduce((s, it) => s + ((it.props || {}).df || 0), 0);

// may this hero wear or wield it? "" when they may, else why not
CM.cantWear = function (h, item) {
  const p = item.props || {};
  if (item.kind === "weapon" && p.bow && h.cls !== "Ranger") return `Only a Ranger draws a bow.`;
  if (item.kind === "weapon" && h.cls === "Monk" && !p.fists) return `A Monk's hands are the weapon.`;
  if (item.kind === "shield" && h.cls === "Monk") return `A Monk's hands are the weapon, and the shield.`;
  if (item.kind === "armor") {
    const w = p.weight || CM.ARMOR_WEIGHT(Math.max(0, CM.ARMORS.indexOf(CM.baseName(item)))), rank = { light: 0, medium: 1, heavy: 2 };
    if (rank[w] > rank[CM.BEARS[h.cls] || "light"]) return `${h.cls}s can't fight in ${w} armour.`;
  }
  if (item.kind === "shield") {
    if (!CM.SHIELD_BEARERS.includes(h.cls)) return `${h.cls}s don't carry shields.`;
    if (h.weapon && h.weapon.props && h.weapon.props.twohanded) return `${h.name}'s ${CM.baseName(h.weapon)} takes both hands.`;
    if (h.offhand && h.offhand.kind === "weapon") return `${h.name}'s other hand holds a knife already.`;
  }
  return "";
};
// a second knife, in the off hand: the Rogue's and the Ranger's, when the main hand holds a dagger too
CM.canDualWield = (h, item) => ["Rogue", "Ranger"].includes(h.cls) && item && item.kind === "weapon" && CM.weaponClass(item) === "dagger" && h.weapon && CM.weaponClass(h.weapon) === "dagger" && !(h.weapon.props || {}).twohanded;
CM.offhandWeapon = (h) => (h.offhand && h.offhand.kind === "weapon" && !h.offhand.unknown ? h.offhand : null);


CM.newParty = function (chosen) {                                         // chosen: [{cls, name, stats, row}] - else the classic four
  return (chosen || CM.CLASSIC.map((cls) => ({ cls }))).map((p) => CM.makeHero(p.cls, p.name, p.stats, p.row, p.quirk, p.origin));
};

// someone to hire at the camp: a calling, a name, a roll, a level a step behind the party's
CM.makeRecruit = function (level, rnd, classes) {
  const cls = rnd.pick(classes || CM.CLASS_ORDER), h = CM.makeHero(cls, CM.randomName(rnd), CM.rollStats(cls, rnd));
  h.level = Math.max(1, level);
  CM.recompute(h);
  h.hp = h.max; h.mp = h.maxmp;
  h.price = 20 + 40 * h.level;
  return h;
};

// ---- between runs: what the deepest run so far has earned ------------------------------------------------------------
CM.deepest = function (fame) {
  let floor = 0, won = false;
  for (const e of fame || []) { floor = Math.max(floor, e.floor || 0); if (e.won) won = true; }
  return { floor, won };
};
CM.unlocked = function (fame) {
  const d = CM.deepest(fame);
  return Object.keys(CM.KITS).filter((id) => CM.KITS[id].need === 0 || (CM.KITS[id].need === 21 ? d.won : d.floor >= CM.KITS[id].need));
};
// this week's dungeon: the same seed for everyone all week, three mutators, and a party the seed rolls (CM.weeklyParty)
CM.weeklySeed = (date) => {
  const d = date || new Date(), t = new Date(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate()));
  const day = t.getUTCDay() || 7; t.setUTCDate(t.getUTCDate() + 4 - day);                 // (ISO week: the Thursday decides the year)
  const y = t.getUTCFullYear(), week = Math.ceil(((t - Date.UTC(y, 0, 1)) / 86400000 + 1) / 7);
  return `weekly-${y}-${String(week).padStart(2, "0")}`;
};
CM.weeklyParty = (seed) => { const rnd = new CM.Random(CM.hashSeed(`${seed}:party`)); return CM.CLASSIC.map((cls) => ({ cls, name: CM.randomName(rnd), stats: CM.rollStats(cls, rnd), row: CM.CLASSES[cls].row })); };
CM.dailySeed = (date) => { const d = date || new Date(); return `daily-${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`; };

// what the party could do with: a line or two of advice, and whether it's sound
CM.partyAdvice = function (party) {
  const notes = [], roles = party.map((p) => p.cls), rows = party.map((p) => p.row || CM.CLASSES[p.cls].row);
  const front = rows.filter((r) => r === "front").length;
  const healers = roles.filter((c) => ["Cleric", "Paladin", "Druid", "Bard"].includes(c)).length;
  const area = roles.filter((c) => ["Mage", "Druid", "Ranger", "Artificer", "Necromancer"].includes(c)).length;
  const casters = roles.filter((c) => CM.CLASSES[c].mp > 0).length;
  if (front === 0) notes.push("No one up front: the monsters will reach whoever they like.");
  else if (front === 1) notes.push("Only one hero up front will take most of the blows - a second would share them.");
  else if (front >= 3) notes.push("Three or more in the front row: the back row's reach is wasted, and all of them get hit.");
  if (!healers) notes.push("No one can heal. Potions will have to do, and they run out.");
  if (!area) notes.push("No spell or volley that hits more than one foe: big groups will wear you down.");
  if (casters >= 3) notes.push("Three casters: strong magic, thin armour. Keep the Knight or Paladin alive.");
  if (!roles.some((c) => ["Knight", "Paladin", "Monk"].includes(c))) notes.push("Without a Knight, Paladin or Monk, nothing draws the monsters' attention.");
  for (const p of party) {
    const c = CM.CLASSES[p.cls];
    if (p.stats && p.stats[c.key] < 10) notes.push(`${p.name || p.cls}'s ${CM.STAT_NAMES[c.key]} is low for a ${p.cls} - reroll?`);
    if (p.stats && p.stats.con <= 6) notes.push(`${p.name || p.cls} is frail (Constitution ${p.stats.con}).`);
  }
  const sound = front >= 1 && front <= 2 && healers > 0 && area > 0;
  if (!notes.length) notes.push(sound ? "A sound party: someone to take the blows, someone to heal, something that hits every foe." : "It could work.");
  return { notes, sound };
};

CM.startingPotion = function (rnd) {                                       // a real potion: no torch, no antidote
  const roll = rnd.next();
  if (roll < 0.12) return { name: "Phoenix Feather", kind: "revive", power: 0, value: 120 };
  if (roll < 0.4) return { name: "Mana Potion", kind: "mana", power: 13, value: 25 };
  return { name: "Healing Potion", kind: "heal", power: 23, value: 20 };
};

CM.startingBag = (seed) => {
  const rnd = new CM.Random(CM.hashSeed(`${seed}:bag`));
  return [CM.startingPotion(rnd), CM.startingPotion(rnd), CM.torch(), CM.torch()];
};

// ---- what's carved into the walls: the Lich King's story, a floor at a time ------------------------------------------

// ---- set-piece rooms: the ring of wall included; D door, L locked door, G gate, S secret door on the ring ------------
// Inside: C chest, M monsters that stay put, F fountain, A altar, P pit, K a key on the floor, X dark floor, W a wall
// with a carving (read from the floor beside it). Entrances sit at odd positions so the maze comes up to them.
CM.TEMPLATES = [
  { name: "Treasure Vault", min: 2, rows: ["#######", "#C...C#", "#..C..#", "###L###"] },
  { name: "Shrine", min: 2, rows: ["#######", "#..A..#", "#.....#", "#C....#", "###D###"] },
  { name: "Fountain Hall", min: 1, rows: ["#########", "#.......#", "#...F...#", "#.......#", "###D#####"] },
  { name: "Den", min: 2, rows: ["#######", "#M...M#", "#..C..#", "#.....#", "###D###"] },
  { name: "Library", min: 3, rows: ["###W###", "#.....#", "W..C..W", "#.....#", "###D###"] },
  { name: "Crypt", min: 3, rows: ["#######", "#XXXXX#", "#XMXCX#", "#XXXXX#", "###S###"] },
  { name: "Pit Room", min: 3, rows: ["#######", "#.P.P.#", "#.....#", "#P.C.P#", "###D###"] },
  { name: "Keep", min: 4, rows: ["#########", "#C.....C#", "#.......#", "#...K...#", "###G#####"] },
];

// ---- helpers -----------------------------------------------------------------------------------------------------
const key = (x, y) => `${x},${y}`;
const unkey = (k) => k.split(",").map(Number);

CM.inBounds = (floor, x, y) => y >= 0 && y < floor.grid.length && x >= 0 && x < floor.grid.length;

// a cell the party could stand in (doors and gates included, whatever their state)
CM.isOpen = function (floor, x, y) {
  if (!CM.inBounds(floor, x, y)) return false;
  if (floor.grid[y][x] === 0) return true;
  const f = floor.features[key(x, y)];
  return Boolean(f && f.type === "secret" && f.found);
};

// a cell the party can walk into right now
CM.passable = function (floor, x, y) {
  if (!CM.isOpen(floor, x, y)) return false;
  const f = floor.features[key(x, y)];
  if (f && (f.type === "door" || f.type === "gate") && !f.open) return false;
  return true;
};

CM.openNeighbours = (floor, x, y) => CM.DIRS.filter(([dx, dy]) => CM.isOpen(floor, x + dx, y + dy));

// how far every open square is from the start, walking where `walk` allows (a breadth-first walk)
CM.distances = function (grid, start, walk) {
  const size = grid.length;
  const ok = walk || ((x, y) => y >= 0 && y < size && x >= 0 && x < size && grid[y][x] === 0);
  const dist = new Map([[key(start[0], start[1]), 0]]);
  const queue = [start];
  for (let i = 0; i < queue.length; i++) {
    const [x, y] = queue[i];
    for (const [dx, dy] of CM.DIRS) {
      const nx = x + dx, ny = y + dy;
      if (ok(nx, ny) && !dist.has(key(nx, ny))) {
        dist.set(key(nx, ny), dist.get(key(x, y)) + 1);
        queue.push([nx, ny]);
      }
    }
  }
  return dist;
};

// Everything the party can reach from where it stands, finding keys and pulling levers as it goes, never falling into a
// pit, never finding a secret door: the floor is solvable when the ladder (or the Lich King) is in that set.
CM.reachable = function (floor, from) {
  const start = from || floor.pos;
  const unlocked = new Set(), opened = new Set();
  let reach = new Set();
  for (let pass = 0; pass < 12; pass++) {
    reach = new Set();
    const queue = [start];
    reach.add(key(start[0], start[1]));
    for (let i = 0; i < queue.length; i++) {
      const [x, y] = queue[i];
      const here = floor.features[key(x, y)];
      const nexts = CM.DIRS.map(([dx, dy]) => [x + dx, y + dy]);
      if (here && here.type === "teleporter") nexts.push(here.to);
      for (const [nx, ny] of nexts) {
        const k = key(nx, ny);
        if (reach.has(k) || !CM.inBounds(floor, nx, ny)) continue;
        const f = floor.features[k];
        if (floor.grid[ny][nx] !== 0) {
          if (!(f && f.type === "secret" && f.found)) continue;
        }
        if (f) {
          if ((f.type === "pit" || f.type === "trapdoor") && !(nx === start[0] && ny === start[1])) continue;
          if (f.type === "door" && f.locked && !unlocked.has(k)) continue;
          if (f.type === "gate" && !f.open && !opened.has(k)) continue;
        }
        reach.add(k);
        queue.push([nx, ny]);
      }
    }
    let keys = 0, changed = false;
    for (const k of reach) {
      const t = floor.things[k];
      if (t && t.type === "key") keys++;
      const f = floor.features[k];
      if (f && (f.type === "lever" || (f.type === "plate" && f.gate)) && !opened.has(f.gate)) { opened.add(f.gate); changed = true; }
    }
    keys -= unlocked.size;                                   // (a key opens one door)
    for (const k of reach) {
      for (const [dx, dy] of CM.DIRS) {
        const nk = key(unkey(k)[0] + dx, unkey(k)[1] + dy);
        const f = floor.features[nk];
        if (f && f.type === "door" && f.locked && !unlocked.has(nk) && !reach.has(nk) && keys > 0) { unlocked.add(nk); keys--; changed = true; }
      }
    }
    if (!changed) break;
  }
  return reach;
};

CM.goalOf = (floor) => Object.keys(floor.things).find((k) => ["ladder", "boss", "guardian"].includes(floor.things[k].type)) || null;

CM.solvable = function (floor, from) {
  const goal = CM.goalOf(floor);
  return Boolean(goal) && CM.reachable(floor, from).has(goal);
};

// ---- the floor ----------------------------------------------------------------------------------------------------
// What every generator's floor gets afterwards, each by a hash of the seed and the floor so the floor itself never
// moves: gems and tomes in the chests, an affix or two on their gear, one unique a band, a choice event, a strongbox
// two floors below its key, a peddler, rivals, and the band's hazards.
CM.furnish = function (floor, seed, gen) {
  const number = floor.number, grid = floor.grid, size = grid.length, special = floor.special;
  const dist = CM.distances(grid, floor.pos);
  const named = floor.rooms.filter((r) => r.name), plain = floor.rooms.filter((r) => !r.name);
  const inTemplate = (x, y) => named.some((r) => x >= r.x0 - 1 && x <= r.x1 + 1 && y >= r.y0 - 1 && y <= r.y1 + 1);
  const roomCells = new Set();
  for (const r of plain) for (let y = r.y0; y <= r.y1; y++) for (let x = r.x0; x <= r.x1; x++) roomCells.add(key(x, y));
  if (number >= 3) for (const [k, t] of Object.entries(floor.things)) {   // deeper down, some chests hold a gem for the smith, or a tome
    if (t.type !== "chest") continue;
    const h = CM.hashSeed(`${seed}:craft:${number}:${k}`);
    if (h % 100 < 12) t.items.push(CM.gem(["diamond", "diamond", "ruby", "sapphire", "sunstone"][(h >>> 8) % 5]));
    else if (h % 100 < 21 && number >= 4) { const ids = Object.keys(CM.TOMES); t.items.push(CM.tome(ids[(h >>> 8) % ids.length])); }
  }
  if (CM.themeIndex(number) === 6) for (const [k, t] of Object.entries(floor.things)) if (t.type === "chest" && CM.hashSeed(`${seed}:glow:${number}:${k}`) % 100 < 15) { t.items.push(CM.glowStone()); break; }   // (the Crystal Caverns: a glow stone now and then)
  // a set's piece, now and then, in a chest of its bands (CM.SETS; by hash, so no floor moves)
  for (const [setId, S] of Object.entries(CM.SETS)) {
    const band0 = CM.themeIndex(number);
    if (band0 < S.bands[0] || band0 > S.bands[1]) continue;
    const hs = CM.hashSeed(`${seed}:set:${setId}:${number}`);              // one roll a floor a set: a piece in a chest, one floor in twelve or so
    if (hs % 100 >= 8) continue;
    const chests = Object.keys(floor.things).filter((k) => floor.things[k].type === "chest").sort();
    if (chests.length) floor.things[chests[(hs >>> 8) % chests.length]].items.push(CM.makeSetPiece(setId, (hs >>> 16) % S.pieces.length, number));
  }
  // the hoard, deeper: an affix or two on the chests' gear, and one unique a band, in a chest on one of its floors
  for (const [k, t] of Object.entries(floor.things)) {
    if (t.type !== "chest") continue;
    t.items.forEach((it, i) => CM.affix(it, number, new CM.Random(CM.hashSeed(`${seed}:affix:${number}:${k}:${i}`))));
  }
  const band = CM.themeIndex(number), uniqueId = Object.keys(CM.UNIQUES).find((id) => CM.UNIQUES[id].band === band);
  if (uniqueId && number <= CM.BOTTOM && !CM.guardianFor(number)) {
    const first = band === 0 ? 2 : band * 5 + 1, floorsOfBand = [];
    for (let n = first; n <= band * 5 + 5; n++) if (!CM.guardianFor(n)) floorsOfBand.push(n);
    if (floorsOfBand[CM.hashSeed(`${seed}:unique:${band}`) % floorsOfBand.length] === number) {
      const chests = Object.keys(floor.things).filter((k) => floor.things[k].type === "chest").sort();
      if (chests.length) floor.things[chests[CM.hashSeed(`${seed}:unique:${band}:chest`) % chests.length]].items.push(CM.makeUnique(uniqueId));
    }
  }
  // the dungeon, stranger: a choice now and then, a strongbox two floors below its key, a peddler, rivals, and the
  // band's hazards - each by its own hash, on cells chosen the same way every time, so the floors stay as they were
  const openCells = () => {
    const out = [];
    for (let y = 1; y < size - 1; y++) for (let x = 1; x < size - 1; x++) {
      const k = key(x, y);
      if (grid[y][x] !== 0 || floor.features[k] || floor.things[k] || inTemplate(x, y) || (dist.get(k) || 0) < 3) continue;
      out.push(k);
    }
    return out;
  };
  const pickCell = (what, filter) => { const cells = openCells().filter(filter || (() => true)); return cells.length ? cells[CM.hashSeed(`${seed}:${what}:${number}`) % cells.length] : null; };
  const h = (what) => CM.hashSeed(`${seed}:${what}:${number}`);
  const ordinary = number >= 2 && number < CM.BOTTOM && !CM.guardianFor(number) && number !== CM.LAST_FLOOR && special !== "maze";
  if (ordinary && h("event") % 100 < 35) {
    const ids = Object.keys(CM.EVENTS).filter((id) => number > CM.LAST_FLOOR || !["pool"].includes(id)), id = ids[h("event:which") % ids.length];
    const k = pickCell("event", (c) => roomCells.has(c));
    if (k) floor.things[k] = { type: "event", event: id, done: false };
  }
  if (ordinary && number >= 4 && number + 2 < CM.BOTTOM && h("boxkey") % 100 < 30 && !(gen >= 2 && CM.guardianFor(number + 2))) {   // the key here, the box two floors down (never a guardian's floor, from the second generator)
    const k = pickCell("boxkey", (c) => !roomCells.has(c));
    if (k) floor.things[k] = { type: "boxkey", box: number + 2 };
  }
  if (number >= 6 && number < CM.BOTTOM && CM.hashSeed(`${seed}:boxkey:${number - 2}`) % 100 < 30 && (number - 2 >= 2 && !CM.guardianFor(number - 2) && number - 2 !== CM.LAST_FLOOR && CM.specialFor(number - 2, seed) !== "maze") && !(gen >= 2 && CM.guardianFor(number))) {
    const k = pickCell("strongbox", (c) => roomCells.has(c)) || (gen >= 2 ? pickCell("strongbox") : null);
    if (k) floor.things[k] = { type: "strongbox", from: number - 2, opened: false };
  }
  if (ordinary && number >= 3 && h("peddler") % 100 < 8) {
    const k = pickCell("peddler", (c) => roomCells.has(c));
    if (k) floor.things[k] = { type: "peddler", stock: null };
  }
  if (ordinary && number >= 4 && h("rivals") % 100 < 10) {
    const k = pickCell("rivals", (c) => roomCells.has(c));
    if (k) floor.things[k] = { type: "rivals", met: false };
  }
  // the second generator's wings: a second stair down into a short floor of the band's own, one a band now and then;
  // a secret stair in a wall, once a band, to a hidden one (CM.WINGS)
  if (gen >= 2 && number >= 3 && number < CM.BOTTOM - 1 && !CM.guardianFor(number) && !CM.guardianFor(number + 1) && !CM.CAMP_AFTER.includes(number) && number !== CM.LAST_FLOOR - 1 && number !== CM.LAST_FLOOR && special !== "maze") {
    const band = CM.themeIndex(number), first = band * 5 + 1, floors = [];
    for (let n = Math.max(3, first); n <= band * 5 + 5; n++) if (!CM.guardianFor(n) && !CM.guardianFor(n + 1) && !CM.CAMP_AFTER.includes(n) && n !== CM.LAST_FLOOR - 1 && n !== CM.LAST_FLOOR && n < CM.BOTTOM - 1) floors.push(n);
    const wingAt = floors.length ? floors[CM.hashSeed(`${seed}:wing:${band}`) % floors.length] : -1, secretAt = floors.length > 1 ? floors.filter((n) => n !== wingAt)[CM.hashSeed(`${seed}:secretwing:${band}`) % (floors.length - 1)] : -1;
    if (number === wingAt) { const k = pickCell("wingstair", (c) => !roomCells.has(c)); if (k) floor.things[k] = { type: "wingstair", wing: band }; }
    if (number === secretAt) {                                           // (a wall beside a corridor cell, searched: Space before it)
      const cells = openCells().filter((c) => !roomCells.has(c));
      for (let i = 0; i < cells.length; i++) {
        const [x, y] = unkey(cells[(CM.hashSeed(`${seed}:secretstair:${number}`) + i) % cells.length]);
        const wall = CM.DIRS.map(([dx, dy]) => [x + dx, y + dy]).find(([wx, wy]) => grid[wy] && grid[wy][wx] === 1 && wx > 0 && wy > 0 && wx < size - 1 && wy < size - 1 && !floor.features[key(wx, wy)]);
        if (wall) { floor.features[key(wall[0], wall[1])] = { type: "secretstair", found: false, wing: band }; break; }
      }
    }
  }
  const hazard = CM.HAZARDS[CM.themeIndex(number)];
  if (hazard && !CM.guardianFor(number)) {
    floor.hazard = hazard.id;
    const n = { spores: 4, vents: 4, bonepiles: 3 }[hazard.id] || 0;
    for (let i = 0; i < n; i++) {
      const k = pickCell(`${hazard.id}:${i}`, (c) => !roomCells.has(c) && !floor.features[c]);
      if (k) floor.features[k] = { type: hazard.id, known: false, spent: false };
    }
  }
  // the people of Caer Duin, each on their three floors (placed last, so the older hashes' cells are what they were) (never beside a generator's ghost of the same name), and the
  // bell they dropped on the fourth; a request's bones far from the ghost, its quarry marked among the floor's bands
  if (number < CM.BOTTOM && !CM.guardianFor(number) && number !== CM.LAST_FLOOR) {
    CM.PEOPLE.forEach((p, i) => {
      const arc = p.floors.indexOf(number);
      if (arc < 0) return;
      const twin = Object.keys(floor.things).find((c) => floor.things[c].type === "ghost" && !floor.things[c].arc && floor.things[c].who === i);
      if (twin) {                                                        // (the generator rolled the same soul here: it stands in their place, and its errand goes)
        for (const [c, t] of Object.entries(floor.things)) { if (t.type === "bones" && t.ghost === twin) delete floor.things[c]; if (t.vengeance === twin) delete t.vengeance; }
        delete floor.things[twin];
      }
      const k = twin || pickCell(`person:${i}`, (c) => roomCells.has(c)) || pickCell(`person:${i}`);
      if (!k) return;
      const ghost = { type: "ghost", who: i, arc: arc + 1, request: arc === 2 ? p.request.kind : null, asked: false };
      floor.things[k] = ghost;
      if (arc !== 2) return;
      if (p.request.kind === "bones") {
        const [gx, gy] = unkey(k), far = pickCell(`personbones:${i}`, (c) => { const [x, y] = unkey(c); return Math.abs(x - gx) + Math.abs(y - gy) >= 6; }) || pickCell(`personbones:${i}`, (c) => c !== k);
        if (far) floor.things[far] = { type: "bones", ghost: k }; else ghost.request = "story";
      } else if (p.request.kind === "vengeance") {
        const groups = Object.entries(floor.things).filter(([, t]) => t.type === "monsters" && !t.still && !t.hunter && !t.vengeance);
        if (!groups.length) { ghost.request = "story"; return; }
        const [, t] = groups[h(`personquarry:${i}`) % groups.length];
        t.vengeance = k;
        const m = t.group[0];
        if (!m.elite) { m.name = `Hulking ${m.name}`; m.elite = "hulking"; m.max = Math.round(m.max * 1.5); m.hp = m.max; m.atk += 2; m.xp = Math.round(m.xp * 1.5); m.gold *= 2; }
      }
    });
    if (number === CM.BELL_FLOOR) { const k = pickCell("bell", (c) => !roomCells.has(c)) || pickCell("bell"); if (k) floor.things[k] = { type: "bones", bell: true }; }
    // the chronicler's rumours, kept: a ghost who wants its bones, a hermit, the other telling of the floor's carving
    if (CM.rumourAt(seed, number, "telling")) for (const f of Object.values(floor.features)) if (f.type === "carving" && f.text === number - 1) f.telling = 1;
    if (CM.rumourAt(seed, number, "hermit") && !Object.values(floor.things).some((t) => t.type === "hermit")) { const k = pickCell("rumour:hermit", (c) => roomCells.has(c)) || pickCell("rumour:hermit"); if (k) floor.things[k] = { type: "hermit", heard: 0, greeted: false }; }
    if (CM.rumourAt(seed, number, "ghostbones") && !Object.values(floor.things).some((t) => t.type === "ghost" && t.request === "bones")) {
      const k = pickCell("rumour:ghost", (c) => roomCells.has(c)) || pickCell("rumour:ghost");
      if (k) {
        floor.things[k] = { type: "ghost", who: h("rumour:who") % CM.GHOSTS.length, request: "bones", asked: false };
        const [gx, gy] = unkey(k), far = pickCell("rumour:bones", (c) => { const [x, y] = unkey(c); return Math.abs(x - gx) + Math.abs(y - gy) >= 6; }) || pickCell("rumour:bones", (c) => c !== k);
        if (far) floor.things[far] = { type: "bones", ghost: k }; else floor.things[k].request = "story";
      }
    }
    // the dungeon remembers the crowned: near the surface, a legend of one of this browser's own parties, now and then
    if (number <= 3 && CM.legends.length && h("legend") % 100 < 50) {
      const k = pickCell("legend", (c) => !roomCells.has(c)) || pickCell("legend");
      if (k) floor.things[k] = { type: "ghost", legend: h("legend:which") % CM.legends.length, asked: false };
    }
    if (number >= 3) {                                                 // a bar in one chest in ten; the dwarves' pick in their halls, now and then
      const chests = Object.keys(floor.things).filter((c) => floor.things[c].type === "chest" && floor.things[c].items).sort();
      for (const c of chests) if (h(`bar:${c}`) % 10 === 0) floor.things[c].items.push(CM.bar());
      if (chests.length && CM.themeIndex(number) === 2 && h("dwarfpick") % 3 === 0) floor.things[chests[h("dwarfpick:chest") % chests.length]].items.push(CM.dwarfPick());
    }
    if (number >= 4 && gen >= 2) {                                     // a mimic: a chest that isn't, one in twelve, by hash (generator 2's floors)
      const chests = Object.keys(floor.things).filter((c) => floor.things[c].type === "chest" && floor.things[c].items && !floor.things[c].items.some((i) => i.kind === "page" || i.named || i.kind === "pick")).sort();
      for (const c of chests) if (h(`mimic:${c}`) % 12 === 0) { floor.things[c].mimic = true; break; }
    }
    if (number >= 4 && (CM.namedWeapons || []).length && h("named") % 100 < 12) {   // a weapon a party of this browser's named, found again, in a chest
      const chests = Object.keys(floor.things).filter((c) => floor.things[c].type === "chest" && floor.things[c].items).sort();
      if (chests.length) floor.things[chests[h("named:chest") % chests.length]].items.push(CM.legendWeapon(CM.namedWeapons[h("named:which") % CM.namedWeapons.length], number));
    }
    CM.COURT.forEach((c, i) => {                                        // the seated dead of the palace, and the physician's page in one of its chests
      if (c.floor !== number) return;
      const k = pickCell(`court:${i}`, (cell) => roomCells.has(cell)) || pickCell(`court:${i}`);
      if (k) floor.things[k] = { type: "ghost", courtier: i, asked: false };
    });
    if (number === CM.LAST_FLOOR - 4 + (CM.hashSeed(`${seed}:page`) % 3)) {   // (one floor of the three, by the seed alone)
      const chests = Object.keys(floor.things).filter((c) => floor.things[c].type === "chest").sort();
      if (chests.length) floor.things[chests[h("page:chest") % chests.length]].items.push(Object.assign({}, CM.PAGE));
    }
  }
  if (number >= 1 && number <= CM.BOTTOM && !CM.guardianFor(number) && number !== CM.LAST_FLOOR && special !== "maze") {   // gathering nodes: two or three a floor, off the rooms' middles (last of all, so no older hash's cell moves)
    const n = 2 + (h("nodes") % 2);
    for (let i = 0; i < n; i++) { const k = pickCell(`node:${i}`, (c) => !roomCells.has(c)) || pickCell(`node:${i}`); if (k) floor.things[k] = { type: "node", band: CM.themeIndex(number) }; }
  }
  return floor;
};

// a floor: made by the run's generator (CM.GEN for a new run), then furnished; a wing (number + 0.5) is made its own way
CM.makeFloor = function (number, seed, gen) {
  if (number % 1 !== 0) return CM.makeWing(number, seed, gen);
  const make = CM.generators[gen || CM.GEN] || CM.generators[1];
  return CM.furnish(make(number, seed), seed, gen || CM.GEN);
};

// a wing: the band's short floor beside floor n (number n + 0.5), carved as any floor of the seed's own key, then made
// a wing of - no way down but the exit to the main stair a floor below, no people, its own hazard; a secret one richer
CM.makeWing = function (number, seed, gen) {
  const n = Math.floor(number), band = CM.themeIndex(n), W = CM.WINGS[band] || CM.WINGS[0];
  const secret = CM.hashSeed(`${seed}:secretwing:${band}`) !== CM.hashSeed(`${seed}:wing:${band}`) && (() => { const first = band * 5 + 1, floors = []; for (let f = Math.max(3, first); f <= band * 5 + 5; f++) if (!CM.guardianFor(f) && !CM.guardianFor(f + 1) && !CM.CAMP_AFTER.includes(f) && f !== CM.LAST_FLOOR - 1 && f !== CM.LAST_FLOOR && f < CM.BOTTOM - 1) floors.push(f); const wingAt = floors.length ? floors[CM.hashSeed(`${seed}:wing:${band}`) % floors.length] : -1; return n !== wingAt; })();
  const make = CM.generators[gen || CM.GEN] || CM.generators[1];
  const fl = make(n, `${seed}:wing:${n}`);
  fl.number = number; fl.wing = band; fl.wingName = secret ? W.secret : W.name; fl.secretWing = secret; fl.special = null;
  for (const [k, t] of Object.entries(fl.things)) {
    if (t.type === "ladder" || t.type === "boss" || t.type === "guardian") fl.things[k] = { type: "wingexit" };
    else if (t.type === "stairs_up") fl.things[k] = { type: "wingstair_up" };
    else if (!["chest", "monsters", "key"].includes(t.type)) delete fl.things[k];
  }
  for (const [k, f] of Object.entries(fl.features)) if (["carving", "teleporter", "spinner", "trapdoor"].includes(f.type)) delete fl.features[k];
  if (!Object.values(fl.things).some((t) => t.type === "wingstair_up")) fl.things[CM.keyOf(fl.pos[0], fl.pos[1])] = { type: "wingstair_up" };
  const rnd = new CM.Random(CM.hashSeed(`${seed}:wingloot:${n}`));
  for (const t of Object.values(fl.things)) if (t.type === "chest") { t.gold = Math.floor(t.gold * (secret ? 2.5 : 1.3)); if (secret) t.items.push(CM.affix(CM.makeItem(n + 3, rnd, rnd.pick(["weapon", "armor", "helm", "shield", "ring", "amulet"])), 99, rnd)); }
  if (secret) { let i = 0; for (const [k, t] of Object.entries(fl.things)) if (t.type === "monsters" && i++ > 0) delete fl.things[k]; }   // (a secret floor: one band, a lot of chests)
  fl.hazard = W.hazard;
  if (W.hazard !== "tide" && W.hazard !== "mirror") { const cells = []; for (let y = 1; y < fl.grid.length - 1; y++) for (let x = 1; x < fl.grid.length - 1; x++) { const k = CM.keyOf(x, y); if (fl.grid[y][x] === 0 && !fl.things[k] && !fl.features[k] && !(x === fl.pos[0] && y === fl.pos[1])) cells.push(k); } for (let i = 0; i < 3 && cells.length; i++) fl.features[cells[CM.hashSeed(`${seed}:winghazard:${n}:${i}`) % cells.length]] = { type: W.hazard, known: false, spent: false }; }
  for (const t of Object.values(fl.things)) if (t.type === "chest") t.items.forEach((it, i) => CM.affix(it, n, new CM.Random(CM.hashSeed(`${seed}:wingaffix:${n}:${i}`))));
  return fl;
};

// an Awakened run: every floor the mirror of itself (x across the middle), done to a floor already made
CM.mirrorFloor = function (fl) {
  const size = fl.grid.length, mx = (x) => size - 1 - x, mk = (k) => { const [x, y] = k.split(",").map(Number); return `${mx(x)},${y}`; };
  fl.grid = fl.grid.map((row) => row.slice().reverse());
  const flipKeys = (map) => { const out = {}; for (const [k, v] of Object.entries(map)) out[mk(k)] = v; return out; };
  fl.things = flipKeys(fl.things); fl.features = flipKeys(fl.features);
  for (const f of Object.values(fl.features)) { if (f.to) f.to = [mx(f.to[0]), f.to[1]]; if (f.gate) f.gate = mk(f.gate); if (f.face === 1) f.face = 3; else if (f.face === 3) f.face = 1; }
  for (const t of Object.values(fl.things)) { if (t.ghost) t.ghost = mk(t.ghost); if (t.vengeance) t.vengeance = mk(t.vengeance); if (t.up) t.up = [mx(t.up[0]), t.up[1]]; }
  fl.dark = fl.dark.map(mk); fl.seen = fl.seen.map(([x, y]) => [mx(x), y]);
  fl.decor = fl.decor.map((d) => Object.assign({}, d, { x: mx(d.x) }));
  fl.rooms = fl.rooms.map((r) => Object.assign({}, r, { x0: mx(r.x1), x1: mx(r.x0) }));
  fl.pos = [mx(fl.pos[0]), fl.pos[1]];
  if (fl.facing === 1) fl.facing = 3; else if (fl.facing === 3) fl.facing = 1;
  fl.mirrored = true;
  return fl;
};
