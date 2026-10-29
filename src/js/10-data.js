"use strict";
// What there is: the classes, the gear, the monsters, the depths and what they look like.

CM.DIRS = [[0, -1], [1, 0], [0, 1], [-1, 0]];              // north, east, south, west (x, y on the grid)
CM.DIR_NAMES = "NESW";
// a monster's name in a sentence: "the Orc", but "the Lich King" (whose name carries its own The)
CM.the = (m) => { const n = typeof m === "string" ? m : m.name; return /^The /.test(n) ? "t" + n.slice(1) : "the " + n; };
CM.The = (m) => { const n = typeof m === "string" ? m : m.name; return /^The /.test(n) ? n : "The " + n; };
CM.LAST_FLOOR = 20;                                        // the Lich King's floor: the story's end, and the Deep's door
CM.BOTTOM = 50;                                            // the bottom of the world
CM.CAMP_AFTER = [5, 10, 15, 25, 30, 35, 40, 45];           // a merchant's camp waits below these floors

// the six stats a hero is rolled with (3-18, plus what the class brings)
CM.STATS = ["str", "dex", "con", "int", "wis", "luck"];
CM.STAT_NAMES = { str: "Strength", dex: "Dexterity", con: "Constitution", int: "Intelligence", wis: "Wisdom", luck: "Luck" };
CM.STAT_HINTS = { str: "harder blows", dex: "hits land, blows miss", con: "more health, every level", int: "stronger spells (arcane)",
  wis: "stronger prayers, more magic", luck: "weak spots found, ailments shrugged off" };

// the eight classes: what they start with, how they grow (grow: health a level), where they stand, what they bring
// to the roll (bonus), the stat that matters most to them (key), and what Cast does for them
CM.CLASSES = {
  Knight: { hp: 34, mp: 0, atk: 6, df: 3, grow: 7, atkGrow: 2, row: "front", key: "str", bonus: { str: 3, con: 2 }, weapon: "Club", armor: "Tunic",
    role: "Front line", cast: null, blurb: "Hits hard and wears the heaviest armour. Foes go for the Knight first." },
  Paladin: { hp: 32, mp: 6, atk: 5, df: 3, grow: 6, atkGrow: 1, row: "front", key: "wis", bonus: { str: 2, wis: 2, con: 1 }, weapon: "Club", armor: "Tunic",
    role: "Front line, healer", cast: "lay", blurb: "A knight who prays: tough up front, and Lay on Hands mends the most wounded." },
  Rogue: { hp: 24, mp: 0, atk: 5, df: 2, grow: 5, atkGrow: 2, row: "front", key: "dex", bonus: { dex: 3, luck: 2 }, weapon: "Knife", armor: "Tunic",
    role: "Striker", cast: null, blurb: "Quick. One hit in four finds a weak spot for double damage - and moved to the back row, every hit does." },
  Ranger: { hp: 28, mp: 0, atk: 5, df: 2, grow: 5, atkGrow: 2, row: "back", key: "dex", bonus: { dex: 3, wis: 1, con: 1 }, weapon: "Short Bow", armor: "Tunic",
    role: "Archer", cast: "volley", blurb: "Shoots over the front line at full strength; a Volley hits two foes at once." },
  Cleric: { hp: 26, mp: 12, atk: 4, df: 2, grow: 5, atkGrow: 1, row: "back", key: "wis", bonus: { wis: 3, con: 1 }, weapon: "Staff", armor: "Tunic",
    role: "Healer", cast: "heal", blurb: "Prays over the most wounded of the party: a heal that grows with every level." },
  Mage: { hp: 18, mp: 14, atk: 3, df: 1, grow: 3, atkGrow: 1, row: "back", key: "int", bonus: { int: 3, dex: 1 }, weapon: "Staff", armor: "Robes",
    role: "Caster", cast: "fireball", blurb: "Frail, but a fireball hits every foe at once. Keep the Mage at the back." },
  Druid: { hp: 24, mp: 12, atk: 4, df: 2, grow: 4, atkGrow: 1, row: "back", key: "wis", bonus: { wis: 2, con: 2, int: 1 }, weapon: "Staff", armor: "Tunic",
    role: "Caster, healer", cast: "thorns", blurb: "Calls thorns up through the stone: every foe hurt, some held fast, the party a little mended." },
  Bard: { hp: 22, mp: 10, atk: 4, df: 2, grow: 4, atkGrow: 1, row: "back", key: "luck", bonus: { luck: 2, dex: 1, int: 1, wis: 1 }, weapon: "Knife", armor: "Tunic",
    role: "Support", cast: "song", blurb: "A song that puts heart into the party: everyone hits harder for the fight, and hurts a little less." },
};
CM.CLASS_ORDER = ["Knight", "Paladin", "Rogue", "Ranger", "Cleric", "Mage", "Druid", "Bard"];
CM.CLASSIC = ["Knight", "Rogue", "Cleric", "Mage"];                  // the party the game suggests
CM.CASTS = { lay: "Lay on Hands", volley: "Volley", heal: "Heal", fireball: "Fireball", thorns: "Thorns", song: "Song" };

// a level earned is a boon chosen: three are offered, from these
CM.BOONS = {
  brawn: { name: "Brawn", what: "+2 Strength", stat: "str" },
  grace: { name: "Grace", what: "+2 Dexterity", stat: "dex" },
  hardy: { name: "Hardy", what: "+2 Constitution, and the health that brings", stat: "con" },
  lore: { name: "Lore", what: "+2 Intelligence", stat: "int" },
  faith: { name: "Faith", what: "+2 Wisdom", stat: "wis" },
  fortune: { name: "Fortune", what: "+2 Luck", stat: "luck" },
  ironskin: { name: "Iron Skin", what: "+2 defence" },
  secondwind: { name: "Second Wind", what: "Once a fight, brought below a quarter of their health, they recover a third of it" },
  keeneye: { name: "Keen Eye", what: "Hits land more often (+10%)" },
  thickblood: { name: "Thick Blood", what: "Poison does half, and ailments are shrugged off more often" },
  scavenger: { name: "Scavenger", what: "A quarter more gold from every fight the party wins" },
  warcry: { name: "War Cry", what: "The first blow they land in a fight does double" },
};

// what can ail a hero
CM.STATUSES = {
  poison: { name: "Poisoned", mark: "☠", hint: "loses a little health each round, and every few steps" },
  paralysis: { name: "Paralysed", mark: "✦", hint: "can't act for a few rounds" },
  sleep: { name: "Asleep", mark: "z", hint: "can't act until hit, or a few rounds pass" },
  blind: { name: "Blinded", mark: "◌", hint: "misses far more often, for a while" },
  curse: { name: "Cursed", mark: "†", hint: "weaker in attack and defence until the curse is lifted" },
  stone: { name: "Stone", mark: "▣", hint: "turned to stone: out of it until restored at a camp" },
};
CM.CURABLE = ["poison", "paralysis", "sleep", "blind"];               // what a rest, an antidote or the temple's Cure mends

// names a hero might have, built from pieces
CM.NAME_STARTS = ["Al", "Bren", "Cael", "Dor", "El", "Fen", "Gar", "Hal", "Is", "Jor", "Kel", "Lir", "Mor", "Nim", "Or", "Pel", "Quin",
  "Ros", "Sar", "Tam", "Ul", "Val", "Wyn", "Yor", "Ash", "Brae", "Cor", "Dun", "Ev", "Fal", "Gwen", "Hol", "Ith", "Kae", "Lor", "Mer", "Ned"];
CM.NAME_ENDS = ["dan", "dric", "lin", "mir", "ric", "wen", "ryn", "wyn", "ssa", "la", "na", "ris", "dor", "mund", "ton", "wick", "ven", "a", "o",
  "ia", "eth", "an", "ard", "ley", "nor", "is"];
CM.randomName = function (rnd) {
  rnd = rnd || new CM.Random(Math.floor(Math.random() * 4294967296));
  const name = rnd.pick(CM.NAME_STARTS) + rnd.pick(CM.NAME_ENDS);
  return name.length < 4 ? name + rnd.pick(["a", "is", "an"]) : name;
};

CM.WEAPONS = ["Dagger", "Short Sword", "Mace", "Long Sword", "Battle Axe", "War Hammer", "Bastard Sword", "Rune Blade",
  "Flamberge", "Mithril Sword", "Dragonslayer", "Claudebrand"];
CM.TWO_HANDED = ["Battle Axe", "War Hammer", "Flamberge", "Dragonslayer"];        // (no shield with these)
CM.BOWS = ["Short Bow", "Hunting Bow", "Long Bow", "Elven Bow", "Dragonbone Bow"];  // the Ranger's, two-handed
CM.ARMORS = ["Padded Vest", "Leather Armor", "Studded Leather", "Ring Mail", "Scale Mail", "Chain Mail", "Banded Mail",
  "Plate Mail", "Elven Mail", "Mithril Plate", "Dragon Scale", "Aegis of Claude"];
CM.SHIELDS = ["Buckler", "Wooden Shield", "Iron Shield", "Kite Shield", "Tower Shield", "Mithril Shield"];
CM.HELMS = ["Leather Cap", "Iron Cap", "Chain Coif", "Steel Helm", "Great Helm", "Mithril Helm"];
CM.RINGS = { str: "Ring of Might", dex: "Ring of Grace", con: "Ring of Vigour", int: "Ring of Wit", wis: "Ring of Faith", luck: "Ring of Fortune" };
CM.AMULETS = [
  { name: "Amulet against Poison", resist: "poison" }, { name: "Amulet against Curses", resist: "curse" },
  { name: "Amulet of the Stone's Bane", resist: "stone" }, { name: "Amulet of Clear Sight", resist: "blind" },
  { name: "Amulet of Warding", df: 2 }, { name: "Amulet of Waking", resist: "sleep" },
];
// what a weapon may carry, deeper down: fire (trolls and the rotting fear it), frost (demons), holy (the undead)
CM.ELEMENTS = { fire: { prefix: "Flaming", weak: ["Troll", "Zombie"] }, frost: { prefix: "Frost", weak: ["Demon", "Wyvern"] }, holy: { prefix: "Blessed", weak: null } };
// armour by weight, and who can bear it: tiers 0-3 light, 4-7 medium, 8-11 heavy
CM.ARMOR_WEIGHT = (tier) => (tier <= 3 ? "light" : tier <= 7 ? "medium" : "heavy");
CM.BEARS = { Knight: "heavy", Paladin: "heavy", Rogue: "medium", Ranger: "medium", Cleric: "medium", Druid: "medium", Bard: "medium", Mage: "light" };
CM.SHIELD_BEARERS = ["Knight", "Paladin", "Cleric", "Rogue", "Druid", "Bard"];
CM.SLOTS = ["weapon", "offhand", "armor", "helm", "ring", "amulet"];
CM.SLOT_NAMES = { weapon: "Weapon", offhand: "Off hand", armor: "Armour", helm: "Helm", ring: "Ring", amulet: "Amulet" };

// scrolls (one reading) and wands (a few charges; anyone can wave one)
CM.SCROLLS = {
  identify: { name: "Scroll of Identify", outside: true, what: "Reveals what one unknown thing in the pack really is." },
  mapping: { name: "Scroll of Mapping", outside: true, what: "The whole floor appears on the automap." },
  teleport: { name: "Scroll of Teleport", outside: true, what: "The party is somewhere else on this floor. Somewhere." },
  fire: { name: "Scroll of Fire", what: "Fire on every foe." },
  frost: { name: "Scroll of Frost", what: "Cold on every foe; some are held fast." },
  protection: { name: "Scroll of Protection", what: "Every blow on the party does less, for the fight." },
};
CM.WANDS = {
  fire: { name: "Wand of Fire", what: "Fire at one foe." },
  frost: { name: "Wand of Frost", what: "Cold on every foe." },
  sleep: { name: "Wand of Sleep", what: "Every foe may fall asleep." },
  healing: { name: "Wand of Healing", outside: true, what: "Mends one of the party." },
};

// what a chest may hold besides treasure
CM.TRAPS = {
  needle: "a poisoned needle", gas: "a breath of choking gas", blade: "a blade that springs from the lid", alarm: "a bell, and something that heard it",
};

// kits earned between runs: what the deepest run so far has unlocked
CM.KITS = {
  pauper: { name: "Pauper's kit", need: 0, what: "30 gold, two potions, two torches. Where everyone starts." },
  veteran: { name: "Veteran's kit", need: 5, what: "60 gold more, and a lantern that never runs out." },
  delver: { name: "Delver's kit", need: 10, what: "Two Scrolls of Mapping, three torches, two antidotes." },
  heir: { name: "Heir's kit", need: 15, what: "Every hero's own weapon, well made: +2 to start." },
  legend: { name: "Legend's kit", need: 21, what: "Every hero sets out at level 2, with a boon to choose. (For slaying the Lich King.)" },
  abyss: { name: "Abyss kit", need: 30, what: "Every hero sets out at level 3 with a boon, and the party with 150 gold more, a rope, a diamond and a Scroll of Mapping. (For reaching floor 30 of the Deep.)" },
};

// each monster, with how it's painted: body (beast, biped, small, wide, tall, ghost), head, eyes, and what it carries
// Each monster: how it's painted; touch - what a hit from it may leave behind, and how often; speed - who moves first;
// undead - what Turn Undead and Smite are for; ability - what else it does in a fight:
//   ranged: reaches the back row as easily as the front   coward: bolts with a purse when hurt   savage: double blows
//   regen: mends each round   drain: steals experience   stun: knocks flat   charge: the first blow is double
//   lifesteal: feeds on the blow   breath: fire on everyone, every other round   buffet: two struck at once
CM.MONSTERS = [
  { name: "Giant Rat", colour: "#8A7058", body: "beast", head: "snout", eyes: "#FF5040", extras: ["tail"], speed: 14, touch: { status: "poison", chance: 0.15 } },
  { name: "Kobold", colour: "#B07040", body: "small", head: "snout", eyes: "#FFE040", extras: ["dagger"], speed: 12, ability: "coward" },
  { name: "Skeleton", colour: "#E0E0D0", body: "thin", head: "skull", eyes: "#FFE040", extras: ["sword"], speed: 8, undead: true },
  { name: "Goblin", colour: "#5A9A40", body: "small", head: "ears", eyes: "#FFE040", extras: ["club"], speed: 11, ability: "ranged" },
  { name: "Zombie", colour: "#7A9A70", body: "biped", head: "round", eyes: "#D0FFD0", extras: ["torn"], skin: "rot", speed: 4, undead: true, touch: { status: "poison", chance: 0.12 } },
  { name: "Orc", colour: "#4A7A3A", body: "wide", head: "tusks", eyes: "#FFE040", extras: ["axe"], speed: 9, ability: "savage" },
  { name: "Ghoul", colour: "#9AA0A0", body: "thin", head: "round", eyes: "#80FF80", extras: ["claws"], speed: 10, undead: true, touch: { status: "paralysis", chance: 0.15 } },
  { name: "Dark Elf", colour: "#5A4A8A", body: "tall", head: "hood", eyes: "#FF80FF", extras: ["bow"], speed: 13, ability: "ranged", touch: { status: "sleep", chance: 0.12 } },
  { name: "Troll", colour: "#3A6A50", body: "wide", head: "round", eyes: "#FFE040", extras: ["club", "claws"], skin: "warts", speed: 7, ability: "regen" },
  { name: "Wraith", colour: "#6A7AA0", body: "ghost", head: "hood", eyes: "#A0E0FF", extras: [], speed: 12, undead: true, ability: "drain", touch: { status: "curse", chance: 0.12 } },
  { name: "Ogre", colour: "#A08050", body: "wide", head: "round", eyes: "#FFE040", extras: ["club"], speed: 6, ability: "stun" },
  { name: "Minotaur", colour: "#7A4A30", body: "wide", head: "horns", eyes: "#FF5040", extras: ["axe"], speed: 10, ability: "charge" },
  { name: "Gargoyle", colour: "#707078", body: "wide", head: "horns", eyes: "#FFE040", extras: ["wings"], skin: "stone", speed: 8, touch: { status: "stone", chance: 0.06 } },
  { name: "Vampire", colour: "#8A2030", body: "tall", head: "pale", eyes: "#FF3030", extras: ["cape"], speed: 13, undead: true, ability: "lifesteal", touch: { status: "sleep", chance: 0.12 } },
  { name: "Demon", colour: "#C03020", body: "wide", head: "horns", eyes: "#FFE040", extras: ["wings", "claws"], speed: 11, ability: "breath", touch: { status: "blind", chance: 0.12 } },
  { name: "Wyvern", colour: "#407A70", body: "beast", head: "snout", eyes: "#FFE040", extras: ["wings", "tail"], speed: 12, ability: "buffet", touch: { status: "poison", chance: 0.2 } },
  // the Deep's kinds (floors 21-50), by the band they belong to (the theme's index): never seen above the Lich King
  { name: "Drowned", colour: "#3E6A74", body: "biped", head: "pale", eyes: "#80E8D8", extras: ["torn"], skin: "rot", speed: 6, undead: true, ability: "lifesteal", touch: { status: "sleep", chance: 0.15 }, deep: 4 },
  { name: "Weed Hag", colour: "#2E5A4E", body: "thin", head: "hood", eyes: "#A0FFE0", extras: ["claws"], speed: 11, ability: "ranged", touch: { status: "paralysis", chance: 0.15 }, deep: 4 },
  { name: "Fungal Horror", colour: "#8AA050", body: "wide", head: "round", eyes: "#F0FF80", extras: ["claws"], skin: "warts", speed: 7, ability: "regen", touch: { status: "poison", chance: 0.3 }, deep: 5 },
  { name: "Spore Beast", colour: "#A0B070", body: "beast", head: "round", eyes: "#E0FF60", extras: ["tail"], speed: 10, ability: "breath", touch: { status: "poison", chance: 0.2 }, deep: 5 },
  { name: "Crystal Golem", colour: "#B090D0", body: "wide", head: "round", eyes: "#F0E0FF", extras: [], skin: "stone", speed: 6, ability: "stun", deep: 6 },
  { name: "Shard Wisp", colour: "#D0C0F0", body: "ghost", head: "pale", eyes: "#FFFFFF", extras: [], speed: 14, ability: "ranged", touch: { status: "blind", chance: 0.2 }, deep: 6 },
  { name: "Iron Hound", colour: "#6A5A50", body: "beast", head: "snout", eyes: "#FF8030", extras: ["tail"], skin: "stone", speed: 13, ability: "charge", deep: 7 },
  { name: "Foundry Imp", colour: "#B04020", body: "small", head: "horns", eyes: "#FFE060", extras: ["wings", "claws"], speed: 12, ability: "breath", touch: { status: "blind", chance: 0.1 }, deep: 7 },
  { name: "Bone Colossus", colour: "#E0D8C0", body: "wide", head: "skull", eyes: "#FF6040", extras: ["club"], speed: 5, undead: true, ability: "buffet", deep: 8 },
  { name: "Grave Priest", colour: "#4A3A5A", body: "tall", head: "skull", eyes: "#C080FF", extras: ["staff", "robe"], speed: 9, undead: true, ability: "drain", touch: { status: "curse", chance: 0.25 }, deep: 8 },
  { name: "Rootling", colour: "#6A3A2A", body: "small", head: "ears", eyes: "#FF4040", extras: ["claws"], speed: 12, ability: "savage", touch: { status: "paralysis", chance: 0.15 }, deep: 9 },
  { name: "Hollow One", colour: "#3A1A1A", body: "ghost", head: "hood", eyes: "#FF3030", extras: [], speed: 11, undead: true, ability: "lifesteal", touch: { status: "curse", chance: 0.2 }, deep: 9 },
];
CM.SHALLOW = 16;                                                        // the kinds of the first twenty floors: the first sixteen rows (the Deep's come after)
CM.monsterLevel = (floor) => (floor <= CM.LAST_FLOOR ? floor : CM.LAST_FLOOR + Math.round((floor - CM.LAST_FLOOR) * 0.5));   // (the Deep climbs more slowly)
CM.monsterKind = (name) => CM.MONSTERS.find((m) => m.name === name) || CM.MONSTERS.find((m) => name && name.endsWith(m.name)) || null;

// now and then a group has a leader out of the ordinary
CM.ELITES = {
  hulking: { name: "Hulking", hp: 1.5, atk: 2, blurb: "half again as tough, and hits harder" },
  swift: { name: "Swift", speed: 6, blurb: "moves before anyone" },
  venomous: { name: "Venomous", touch: { status: "poison", chance: 0.4 }, blurb: "a poisoned bite" },
  ancient: { name: "Ancient", df: 4, xp: 1.6, blurb: "armoured by age, and worth more" },
  cunning: { name: "Cunning", ability: "ranged", blurb: "reaches the back row" },
  ravenous: { name: "Ravenous", ability: "lifesteal", blurb: "feeds on every blow" },
};

// Spells and skills, by calling and the level they come at. mp 0 is a skill; once: once a fight; outside: castable
// between fights too. Targets: foe, foes, ally, allies, fallen, none.
CM.ABILITIES = {
  // the Mage's book
  missile: { name: "Magic Missile", cls: { Mage: 1 }, mp: 2, target: "foe", what: "A bolt of force that never misses." },
  firebolt: { name: "Fire Bolt", cls: { Mage: 1 }, mp: 3, target: "foe", what: "Fire at one foe." },
  light: { name: "Light", cls: { Mage: 2, Cleric: 2 }, mp: 2, target: "none", outside: true, what: "Light to see by for 200 steps, torch or no torch." },
  sleep: { name: "Sleep", cls: { Mage: 2 }, mp: 3, target: "foes", what: "Every foe may fall asleep until struck." },
  frost: { name: "Frost", cls: { Mage: 3 }, mp: 4, target: "foes", what: "Cold on every foe; some are held fast." },
  fireball: { name: "Fireball", cls: { Mage: 4 }, mp: 5, target: "foes", what: "Fire on every foe." },
  blink: { name: "Blink", cls: { Mage: 5 }, mp: 4, target: "none", what: "The party is elsewhere: a sure escape, two squares back (not from the Lich King)." },
  lightning: { name: "Lightning", cls: { Mage: 6 }, mp: 6, target: "foe", what: "A great bolt at one foe." },
  // the Cleric's prayers
  heal: { name: "Heal", cls: { Cleric: 1 }, mp: 3, target: "ally", outside: true, what: "Mends one of the party." },
  cure: { name: "Cure", cls: { Cleric: 2 }, mp: 2, target: "ally", outside: true, what: "Poison, sleep, paralysis and blindness leave one of the party." },
  bless: { name: "Bless", cls: { Cleric: 3, Paladin: 5 }, mp: 4, target: "allies", what: "The party hits harder and is harder to hit, for the fight." },
  turn: { name: "Turn Undead", cls: { Cleric: 3 }, mp: 4, target: "foes", what: "The undead burn, and may flee." },
  protection: { name: "Protection", cls: { Cleric: 5 }, mp: 4, target: "allies", what: "Every blow on the party does less, for the fight." },
  lift: { name: "Lift", cls: { Cleric: 6 }, mp: 3, target: "allies", outside: true, what: "Curses, blindness and sleep leave the whole party." },
  sanctuary: { name: "Sanctuary", cls: { Cleric: 7 }, mp: 6, target: "foes", what: "Half the foes can't bring themselves to strike, this round." },
  raise: { name: "Raise Dead", cls: { Cleric: 8 }, mp: 10, target: "fallen", outside: true, what: "A fallen hero stands again, at a third of their health." },
  // the Paladin
  lay: { name: "Lay on Hands", cls: { Paladin: 1 }, mp: 3, target: "ally", outside: true, what: "Mends one of the party, and takes the poison from them." },
  smite: { name: "Smite", cls: { Paladin: 3 }, mp: 4, target: "foe", what: "A holy blow: double against the undead." },
  // the Druid
  thorns: { name: "Thorns", cls: { Druid: 1 }, mp: 4, target: "foes", what: "Thorns up through the stone: every foe hurt, some held fast, the party a little mended." },
  mend: { name: "Mend", cls: { Druid: 2 }, mp: 3, target: "ally", outside: true, what: "Mends one of the party." },
  entangle: { name: "Entangle", cls: { Druid: 3 }, mp: 3, target: "foe", what: "One foe held fast for two rounds." },
  regrowth: { name: "Regrowth", cls: { Druid: 5 }, mp: 5, target: "allies", outside: true, what: "The whole party mends." },
  calllightning: { name: "Call Lightning", cls: { Druid: 6 }, mp: 6, target: "foe", what: "Lightning on one foe." },
  // the Bard
  song: { name: "Song", cls: { Bard: 1 }, mp: 4, target: "allies", what: "Hearts lift: the party hits harder for the fight, and hurts a little less." },
  mockery: { name: "Mockery", cls: { Bard: 2 }, mp: 2, target: "foe", what: "One foe, stung, takes a quarter more from every blow." },
  lullaby: { name: "Lullaby", cls: { Bard: 3 }, mp: 4, target: "foes", what: "Every foe may fall asleep until struck." },
  rally: { name: "Rally", cls: { Bard: 5 }, mp: 5, target: "allies", outside: true, what: "The party mends a little and shrugs off the small ailments." },
  // skills: no magic in them
  volley: { name: "Volley", cls: { Ranger: 1 }, mp: 0, target: "foes", what: "Two arrows, at two foes." },
  aimed: { name: "Aimed Shot", cls: { Ranger: 3 }, mp: 0, target: "foe", once: true, what: "An arrow that can't miss, half again as hard. Once a fight." },
  mark: { name: "Mark", cls: { Ranger: 5 }, mp: 0, target: "foe", what: "One foe marked: a quarter more from every blow." },
  guard: { name: "Guard", cls: { Knight: 1 }, mp: 0, target: "ally", what: "Blows aimed at one of the party land on the Knight instead, until their next turn." },
  taunt: { name: "Taunt", cls: { Knight: 3 }, mp: 0, target: "none", once: true, what: "Every foe comes for the Knight, this round and the next. Once a fight." },
  bash: { name: "Shield Bash", cls: { Knight: 5 }, mp: 0, target: "foe", what: "A blow that may leave the foe reeling for a round." },
  trick: { name: "Dirty Trick", cls: { Rogue: 4 }, mp: 0, target: "foe", what: "Sand in the eyes: the foe misses more, for a while." },
};
// (the Rogue's Pick Lock comes at level 2 and works on its own: walk into a locked door without a key)
CM.PICK_LOCK_LEVEL = 2;
CM.LIGHT_STEPS = 200;

// ---- the dungeon's people and its puzzles ------------------------------------------------------------------------
// Riddle doors ask about the carvings: `lore` is the carving (an index in CM.LORE, found on floor lore + 1) that holds
// the answer, so a riddle is only ever asked below the floor where it could have been read.
CM.RIDDLES = [
  { lore: 1, q: "What came up the river in the king's twelfth year?", a: "The plague", wrong: ["A fleet of the dwarves", "The queen's brothers"] },
  { lore: 2, q: "What did King Mordeth have taken down when the queen died?", a: "The bells", wrong: ["The gates", "The banners"] },
  { lore: 5, q: "What did the stranger from the east leave behind him?", a: "A box he would not open", wrong: ["A sword", "A letter"] },
  { lore: 6, q: "What did the court physician write that the king no longer does?", a: "Sleep", wrong: ["Eat", "Pray"] },
  { lore: 7, q: "What did the dwarves' last letter ask?", a: "Why the king's coin was cold", wrong: ["For grain", "For a wife for their king"] },
  { lore: 9, q: "What did the one page of the physician's notes that survived say?", a: "The heart may be kept apart", wrong: ["The king must sleep", "Burn the body"] },
  { lore: 11, q: "What did the child's letters say not to do?", a: "Look at him", wrong: ["Ring the bells", "Go below"] },
  { lore: 13, q: "Who did the king ask for by name, last of all?", a: "The captain of the guard", wrong: ["The physician", "The dwarf-king"] },
  { lore: 15, q: "What are the palace's foundations made of?", a: "The masons' graves", wrong: ["The dwarves' stone", "River mud"] },
  { lore: 18, q: "Where is the king's heart?", a: "Not in his chest", wrong: ["In the river", "With the queen"] },
];
CM.RIDDLE_FROM = 4;                                                      // the first floor a door may ask

// the ghosts: each has a name, something it wants (bones brought to it, the thing that killed it slain, or this
// floor's carving read and told to it), and a tale to tell when it has it
CM.GHOSTS = [
  { name: "Hal of the lower watch", tale: "Hal says: the water came in the night, and the captain stood in it to the chest and would not leave. We left him. He is down there still, I think, standing." },
  { name: "Ysolde the king's cook", tale: "Ysolde says: in the twelfth year the king stopped eating, and the dogs would not eat what came back from his table either. I carved the bread recipe on a wall so something of mine would last." },
  { name: "Brother Cael", tale: "Cael says: we rang the last bell ourselves, the night the queen died, before they came for it. He heard it. He has heard it ever since, I think. Good." },
  { name: "Tamsin, who kept the tally", tale: "Tamsin says: I counted the dead for the king, a mark for each. When the marks stopped meaning anything to him I kept counting anyway. Someone had to." },
  { name: "Aldous the Lesser", tale: "Aldous says: it was a good chair. Oak. I'd have liked them to remember the troll was already wounded, but no one carves that part." },
  { name: "Mother Ennis", tale: "Mother Ennis says: I told the child not to look at him. I looked. That is all I will say about that, and I have had a long time to think of more." },
];
CM.REQUESTS = {
  bones: { ask: "My bones lie somewhere on this floor, where they dragged me. Bring them here, and I'll rest - and tell you what I know.", wait: "You haven't found them. They're on this floor, somewhere the rats go.",
    done: "You lay the bones down, and the ghost kneels to them like a mother. \"Thank you. Take this; I kept it a long time for nothing.\"" },
  vengeance: { ask: "The thing that killed me still walks this floor. Kill it. Then come back, and I'll give you what I have.", wait: "It still walks. I can hear it.",
    done: "\"It's dead? It's dead.\" The ghost stands a little taller. \"Then take this. I won't need it where I'm going.\"" },
  story: { ask: "There's writing on this floor's wall. I can't read it any more - the letters swim. Read it, and come and tell me what it says.", wait: "You haven't read it yet. It's on a wall of this floor, where the light falls.",
    done: "You tell the ghost what the wall says. It listens with its eyes shut. \"Yes. That was it. That was us.\" It presses something into your hand." },
};
// the hermit, who wants a story for his work; the lost adventurer, who owes you one
CM.HERMIT = {
  greet: "A hermit in a nest of rags looks up. \"I'll tell you what your things are - I know every make the dungeon ever swallowed - but I want paying in stories. Read the walls. Tell me what they say.\"",
  told: ["\"Hm. Yes, I'd heard that.\" He turns the thing over in his hands.", "\"Ha! No - no, I hadn't heard that one.\"", "\"The old king,\" he says, and spits. \"Go on, then.\"", "\"Good. Good. Give it here.\""],
  nothing: "\"Nothing unknown in your pack. Then I'll give you a direction for your story, since you have nothing else to spend it on:\"",
  noStory: "\"You've told me everything you've read. Read something else - the walls are full of it - and come back.\"",
};
CM.ADVENTURER = {
  found: "Someone sits against the wall, bound hand and foot: an adventurer, one of a party that didn't come back. They look up. \"Cut me loose and I'm yours. I owe you that.\"",
  joins: (name, cls, gone) => `You cut ${name} the ${cls} loose, and they take up ${gone}'s place in the line.`,
  leaves: (name) => `You cut ${name} loose. "You've no place for me - but I mapped this floor before they took me, and I've a rope you can have. I'll make for the camp. Ask for me there."`,
};

CM.abilitiesFor = (hero) => Object.keys(CM.ABILITIES).filter((id) => {
  if ((hero.learned || []).includes(id)) return true;                  // (from a tome)
  const at = CM.ABILITIES[id].cls[hero.cls];
  return at !== undefined && hero.level >= at;
});

// ---- growth: a path for each calling, chosen at level 5, deepening at level 10 ----------------------------------------
// Each path has two traits: the first comes with the choice, the second at the deeper level. CM.trait(hero, id) says
// whether a hero has one. The effects live where they bite: in the fight's code (60-game.js) and in CM.recompute.
CM.PATH_AT = [5, 10];
CM.PATHS = {
  Knight: {
    bulwark: { name: "Bulwark", blurb: "The wall the party stands behind.",
      t1: { id: "stonewall", name: "Stone Wall", what: "+3 defence" }, t2: { id: "aegis", name: "Aegis", what: "A blow the Knight steps in front of does half" } },
    champion: { name: "Champion", blurb: "The blade that ends things.",
      t1: { id: "mighty", name: "Mighty", what: "+3 attack" }, t2: { id: "flurry", name: "Flurry", what: "Every Fight is two blows, the second at half strength" } },
  },
  Paladin: {
    crusader: { name: "Crusader", blurb: "Holy in the hand.",
      t1: { id: "holyblade", name: "Holy Blade", what: "Every blow bites deep into the undead, blessed or not" }, t2: { id: "radiance", name: "Radiance", what: "Smite falls on every undead foe at once" } },
    shepherd: { name: "Shepherd", blurb: "No one left behind.",
      t1: { id: "gentlehands", name: "Gentle Hands", what: "Lay on Hands mends half again as much and lifts the small ailments" }, t2: { id: "lastrites", name: "Last Rites", what: "Lay on Hands can call a fallen hero back, once a fight" } },
  },
  Rogue: {
    assassin: { name: "Assassin", blurb: "One blow is enough.",
      t1: { id: "deadly", name: "Deadly", what: "A weak spot does triple, not double" }, t2: { id: "ambush", name: "Ambush", what: "The first blow in every fight finds a weak spot" } },
    trickster: { name: "Trickster", blurb: "Never where the blow lands.",
      t1: { id: "sand", name: "Sand", what: "Dirty Trick also holds the foe a round" }, t2: { id: "slippery", name: "Slippery", what: "Running always works (not from the Lich King), and the party is never caught by surprise" } },
  },
  Ranger: {
    sharpshooter: { name: "Sharpshooter", blurb: "Every arrow counts.",
      t1: { id: "truearrow", name: "True Arrow", what: "Arrows never miss" }, t2: { id: "rainofarrows", name: "Rain of Arrows", what: "Volley looses three arrows" } },
    warden: { name: "Warden", blurb: "The dungeon's ways, learned.",
      t1: { id: "wardeneye", name: "Warden's Eye", what: "Trapdoors and trap plates two steps off are seen; a hidden door beside you is found" }, t2: { id: "pathfinder", name: "Pathfinder", what: "Torches burn half as fast" } },
  },
  Cleric: {
    priest: { name: "Priest", blurb: "The healing hand.",
      t1: { id: "blessedhands", name: "Blessed Hands", what: "Heal mends half again as much" }, t2: { id: "miracle", name: "Miracle", what: "Raise Dead brings a hero back whole" } },
    exorcist: { name: "Exorcist", blurb: "The light that burns.",
      t1: { id: "purifier", name: "Purifier", what: "Turn Undead scorches the living too, for half" }, t2: { id: "consecrate", name: "Consecrate", what: "Bless also lays Protection on the party" } },
  },
  Mage: {
    pyromancer: { name: "Pyromancer", blurb: "Fire, and more fire.",
      t1: { id: "firebrand", name: "Firebrand", what: "Fire spells do half again as much" }, t2: { id: "inferno", name: "Inferno", what: "Fireball leaves every foe burning for two rounds" } },
    archmage: { name: "Archmage", blurb: "Magic without end.",
      t1: { id: "thrifty", name: "Thrifty", what: "Every spell costs one less" }, t2: { id: "wellspring", name: "Wellspring", what: "Two magic back at the end of every round of a fight" } },
  },
  Druid: {
    grove: { name: "Grove", blurb: "Green things mend.",
      t1: { id: "deeproots", name: "Deep Roots", what: "Thorns mends the party three times as much" }, t2: { id: "evergreen", name: "Evergreen", what: "The whole party mends 3 at the end of every round" } },
    storm: { name: "Storm", blurb: "The sky brought down.",
      t1: { id: "stormcall", name: "Storm Call", what: "Call Lightning strikes every foe, for most of its force" }, t2: { id: "tempest", name: "Tempest", what: "Lightning may leave a foe reeling for a round" } },
  },
  Bard: {
    skald: { name: "Skald", blurb: "Songs for a shield wall.",
      t1: { id: "warsong", name: "War Song", what: "Song gives twice the heart: +4 attack, and every blow on the party does 2 less" }, t2: { id: "epic", name: "Epic", what: "Song lasts the whole floor, fight after fight" } },
    jester: { name: "Jester", blurb: "Laughter, and a knife in it.",
      t1: { id: "jeer", name: "Jeer", what: "Mockery also leaves the foe half blind" }, t2: { id: "lull", name: "Lull", what: "Lullaby never fails" } },
  },
};
CM.trait = function (h, id) {
  const P = h && h.path && CM.PATHS[h.cls] && CM.PATHS[h.cls][h.path];
  if (!P) return false;
  return (P.t1.id === id && h.level >= CM.PATH_AT[0]) || (P.t2.id === id && h.level >= CM.PATH_AT[1]);
};
CM.needsPath = (h) => Boolean(h && h.hp > 0 && h.level >= CM.PATH_AT[0] && !h.path && CM.PATHS[h.cls]);

// tomes teach a spell to any caster who reads one (Paladin, Cleric, Mage, Druid, Bard) - one they don't know yet
CM.TOMES = {
  light: "Tome of Light", sleep: "Tome of Sleep", frost: "Tome of Frost", fireball: "Tome of Fire", lightning: "Tome of Storms",
  heal: "Tome of Mending", cure: "Tome of Cures", bless: "Tome of Blessing", turn: "Tome of the Holy Symbol", protection: "Tome of Wards",
  mend: "Tome of Herbs", entangle: "Tome of Roots", regrowth: "Tome of Regrowth", song: "Tome of Songs", lullaby: "Tome of Lullabies", rally: "Tome of Rallying",
};
// gems, for the camp's smith: a diamond puts +1 on a piece of gear, the others put fire, frost or holiness into a weapon
CM.GEMS = {
  diamond: { name: "Diamond", element: null }, ruby: { name: "Ruby", element: "fire" }, sapphire: { name: "Sapphire", element: "frost" }, sunstone: { name: "Sunstone", element: "holy" },
};
CM.SMITH = { enchant: 80, gem: 120, most: 3 };
// ---- ways to play: difficulty, the daily dungeon's mutators, achievements and the titles they give, the keys ---------
CM.DIFFICULTIES = {
  gentle: { name: "Gentle", hp: 0.75, atk: 0.8, gold: 1.25, what: "monsters a quarter weaker, and more gold" },
  fair: { name: "Fair", hp: 1, atk: 1, gold: 1, what: "the dungeon as it is" },
  grim: { name: "Grim", hp: 1.3, atk: 1.25, gold: 0.9, what: "monsters a third tougher and harder-hitting, a little less gold; the Hall of Fame marks it" },
};
// Today's dungeon comes with two of these, from the date
CM.MUTATORS = {
  hordes: { name: "Hordes", what: "every band of monsters has one more in it" },
  brittle: { name: "Brittle", what: "monsters have half the health and hit half again as hard" },
  rich: { name: "Rich veins", what: "chests hold twice the gold" },
  swift: { name: "Swift", what: "monsters move faster" },
  drought: { name: "Drought", what: "every fountain is dry" },
  gloom: { name: "Gloom", what: "torches burn twice as fast" },
  lean: { name: "Lean", what: "the party sets out without potions, and with 100 gold more" },
};
CM.DEEPENING = ["hordes", "brittle", "swift", "gloom", "drought"];      // Endless: the dark deepens with one of these every ten floors below the bottom
CM.mutatorsFor = function (seed) {
  if (!String(seed).startsWith("daily-")) return [];
  const ids = Object.keys(CM.MUTATORS), a = CM.hashSeed(`${seed}:mutator:1`) % ids.length;
  let b = CM.hashSeed(`${seed}:mutator:2`) % (ids.length - 1);
  if (b >= a) b++;
  return [ids[a], ids[b]];
};
// achievements, kept between runs; the first one earned in this order is the title the player wears on the title screen
CM.ACHIEVEMENTS = {
  beyond: { name: "Beyond the Dream", what: "Reach floor 100 in an Endless expedition", title: "Beyond the Dream" },
  bottom: { name: "To the Bottom", what: "Reach the bottom of the world, below the fiftieth floor", title: "of the Bottom" },
  crown: { name: "Crownbreaker", what: "Slay the Lich King", title: "Crownbreaker" },
  ironman: { name: "Unfallen", what: "Slay the Lich King with no hero ever fallen", title: "the Unfallen" },
  grim: { name: "Grim", what: "Slay the Lich King on Grim", title: "the Grim" },
  swift: { name: "Swift", what: "Slay the Lich King in under 1,500 steps", title: "the Swift" },
  abyss: { name: "Of the Deep", what: "Reach floor 30, in the Deep", title: "of the Deep" },
  endless: { name: "Without End", what: "Reach floor 60 in an Endless expedition", title: "Without End" },
  deeper: { name: "Of the Halls", what: "Reach floor 15", title: "of the Halls" },
  labyrinth: { name: "Minotaur's Bane", what: "Slay the Minotaur of the Labyrinth", title: "the Minotaur's Bane" },
  untouched: { name: "Unbowed", what: "Slay a guardian with no one falling in the fight", title: "the Unbowed" },
  deep: { name: "Of the Vaults", what: "Reach floor 10", title: "of the Vaults" },
  daily: { name: "Of the Day", what: "Reach floor 10 in Today's dungeon", title: "of the Day" },
  smith: { name: "Tempered", what: "Have the smith work a piece of gear to +3", title: "the Tempered" },
  hoarder: { name: "Rich", what: "Hold 2,000 gold at once", title: "the Rich" },
  scholar: { name: "Learned", what: "Fill the journal with ten entries", title: "the Learned" },
  friend: { name: "Kind", what: "Cut a lost adventurer loose", title: "the Kind" },
  restful: { name: "Gentle", what: "Lay a ghost to rest", title: "the Gentle" },
  delver: { name: "Delver", what: "Reach floor 5", title: "the Delver" },
};
CM.titleFor = (achievements) => { const id = Object.keys(CM.ACHIEVEMENTS).find((a) => achievements && achievements[a]); return id ? CM.ACHIEVEMENTS[id].title : ""; };
// the keys, as the player may set them (Settings > Keys); the arrows always move as well
CM.DEFAULT_KEYS = { forward: "KeyW", back: "KeyS", left: "KeyA", right: "KeyD", strafeLeft: "KeyQ", strafeRight: "KeyE", use: "Space", inventory: "KeyI",
  cast: "KeyC", journal: "KeyJ", map: "Tab", fight: "KeyF", item: "KeyP", defend: "KeyD", run: "KeyR", explore: "KeyX", auto: "KeyA" };
CM.KEY_ACTIONS = [["forward", "forward"], ["back", "back"], ["left", "turn left"], ["right", "turn right"], ["strafeLeft", "sidestep left"], ["strafeRight", "sidestep right"],
  ["use", "use / talk / search"], ["inventory", "inventory"], ["journal", "journal"], ["map", "the automap, large"], ["cast", "cast or use a skill"],
  ["explore", "walk to the nearest unexplored square (any key stops)"],
  ["fight", "in a fight: fight the chosen foe"], ["item", "in a fight: an item"], ["defend", "in a fight: defend"], ["run", "in a fight: run"], ["auto", "in a fight: the party fights on by itself"]];
CM.keyName = (code) => (code || "").replace(/^Key/, "").replace(/^Digit/, "").replace(/^Arrow/, "").replace("Space", "Space").replace("Backquote", "`");
// an Endless entry that ended below - not one that took the daylight with the crown
CM.endlessFall = (e) => Boolean(e && e.endless && !(e.won && e.floor <= CM.LAST_FLOOR));
// a run's story in a few lines, to copy and share (from a Hall of Fame entry)
CM.summaryText = function (e) {
  const d = CM.DIFFICULTIES[e.difficulty] ? CM.DIFFICULTIES[e.difficulty].name : "Fair", t = e.tally || {};
  const lines = [`Claude and Magic - ${e.name}'s ${e.endless ? "Endless " : ""}expedition (${d})${e.mutators && e.mutators.length ? `, ${e.endless ? "the dark deepened" : "today's dungeon"}: ${e.mutators.map((m) => CM.MUTATORS[m] ? CM.MUTATORS[m].name : m).join(" and ")}` : ""}`,
    `${CM.endlessFall(e) ? `Floor ${e.floor} of the endless dark${e.won ? ", with the Lich King's crown" : ""}` : e.bottom ? "To the bottom of the world, floor " + CM.BOTTOM
      : e.won && e.floor > CM.LAST_FLOOR ? `Slew the Lich King, and fell on floor ${e.floor} of the Deep` : e.won ? "Slew the Lich King on floor " + CM.LAST_FLOOR : `Fell on floor ${e.floor}, ${CM.themeFor(e.floor).name}`}, with ${(e.gold || 0).toLocaleString()} gold - seed ${e.seed || "?"} - ${e.date || ""}`];
  if (e.party && e.party.length) lines.push(`Party: ${e.party.join(", ")}`);
  lines.push(`${CM.plural(t.kills || 0, "monster")} slain, ${CM.plural(t.chests || 0, "chest")} opened, ${CM.plural(t.steps || 0, "step")}, ${CM.plural(t.fights || 0, "fight")}${t.fled ? ` (${t.fled} fled)` : ""}`);
  if (t.guardians && t.guardians.length) lines.push(`Guardians slain: ${t.guardians.map((id) => (CM.GUARDIANS[id] || { name: id }).name.replace(/^The /, "the ")).join(", ")}`);
  if (e.titles && e.titles.length) lines.push(`Earned: ${e.titles.map((id) => (CM.ACHIEVEMENTS[id] || { name: id }).name).join(", ")}`);
  return lines.join("\n");
};
                           // gold a +1 (times the pluses so far), gold a gem set, the most pluses the smith will work

// the Lich King: what he does as the fight goes
CM.LICH = { summonEvery: 3, summonMax: 4, coldFrom: 0.3, summonFrom: 0.6, riseTo: 0.4 };
CM.BOSS = { name: "The Lich King", colour: "#A0E0FF", body: "tall", head: "skull", eyes: "#40F0FF", extras: ["crown", "staff", "robe"] };

// ---- the guardians ---------------------------------------------------------------------------------------------------
// On the floor above each camp something has made its lair over the shaft down, and the party must go through it. Each
// has its look (painted like the monsters), its lair (a set piece with the shaft under its feet: B the guardian, # a
// pillar, n a heap of bones and rags, t a throne, v an anvil, e embers in the floor, W a carving of its story; flood puts
// water on every floor of it), two things it does in a fight, what it is weak to and what it shrugs off, the company it
// keeps, a relic it leaves, and the wash of colour over the view when it falls.
CM.GUARDIANS = {
  rat: { floor: 5, name: "The Rat King", colour: "#6E5444", body: "beast", head: "snout", eyes: "#FF5040", extras: ["tail", "crown", "swarm"], speed: 13, size: 0.9,
    hp: 150, atk: 15, df: 6, xp: 500, gold: 350, touch: { status: "poison", chance: 0.45 }, weak: "fire", resist: null, undead: false,
    escorts: ["Giant Rat", "Giant Rat"], tint: "rgba(160,220,80,0.35)",
    moves: [{ kind: "summon", what: "Giant Rat", n: 2, max: 4, word: "rat", text: "The Rat King shrieks, and {n} pour out of the refuse!" }], passives: ["plague"],
    abilities: [["Call the swarm", "every third turn, rats pour out of the refuse (four at most)"],
      ["Plague bite", "poisons more often than not, for longer, and bites a poisoned hero half again as hard"]],
    intro: "The heap of bones and rags heaves, and something climbs out of it: a rat the size of a hound, a crown of knotted tails on its head. The Rat King.",
    fall: "The Rat King shrieks once, and the swarm pours away into the walls. The nest is quiet.",
    take: "Among the bones you find its crown - gold, under the filth - and the shaft the nest was heaped over.",
    lore: "They fed the rats, so the rats would not feed on them. Then the rats learned to want. Here the feeding stopped.",
    relic: { name: "Rat King's Crown", kind: "helm", slot: "helm", power: 3, value: 600, props: { relic: true, resist: "poison", stat: "luck" } },
    lair: { name: "Rat King's Nest", lore: "g:rat", rows: ["####W####", "#n.....n#", "#..n.n..#", "#...B...#", "#.n...n.#", "#n.....n#", "###D#####"] } },
  knight: { floor: 10, name: "The Drowned Knight", colour: "#3E6068", body: "tall", head: "helm", eyes: "#80E8D8", extras: ["sword", "shield", "weed"], speed: 8, size: 1.0,
    hp: 280, atk: 26, df: 12, xp: 1400, gold: 1000, touch: null, weak: "holy", resist: "frost", undead: true, escorts: [], tint: "rgba(80,180,200,0.4)",
    moves: [{ kind: "grasp", mult: 1.5, status: "paralysis", text: "The Drowned Knight's gauntlet closes on {who} and drags them under!", how: " - held under the water" }], passives: ["rise"],
    riseText: "The Drowned Knight goes down into the water... and the water lifts him up again. He will not stay down. Not yet.",
    abilities: [["Drowning grasp", "every third turn, drags one of the party under: half again the blow, and a round lost gasping"],
      ["Unquiet", "the water lifts him up again, once, at a third of his strength"]],
    intro: "In the sunken hall a knight sits his throne under the water, and stands as you come in. Weed hangs from his helm; the water runs out of him and never stops. The Drowned Knight.",
    fall: "The Drowned Knight sinks to one knee, and then into the water, and this time the water keeps him.",
    take: "His shield floats where he fell, and under the throne the water drains away down the shaft.",
    lore: "The captain of the lower town's watch would not leave his post when the water came. The water, in the end, agreed with him.",
    relic: { name: "Shield of the Drowned", kind: "shield", slot: "offhand", power: 5, value: 900, props: { relic: true, resist: "paralysis", df: 2 } },
    lair: { name: "Drowned Hall", lore: "g:knight", flood: true, rows: ["#####W#####", "#....t....#", "#.#.....#.#", "#....B....#", "#.#.....#.#", "#.........#", "#####D#####"] } },
  forge: { floor: 15, name: "The Forge-Warden", colour: "#5C5450", body: "wide", head: "round", eyes: "#FFB030", extras: ["hammer", "glow"], skin: "stone", speed: 6, size: 1.08,
    hp: 440, atk: 36, df: 20, xp: 2600, gold: 1800, touch: null, weak: "frost", resist: "fire", undead: false, escorts: [], tint: "rgba(255,150,40,0.4)",
    moves: [{ kind: "slam", frac: 2.5, status: "paralysis", chance: 0.3, front: true, text: "The Forge-Warden raises the hammer in both hands and brings it down!", how: " - the hammer", flat: "{who} is knocked flat!" }],
    passives: ["heat"], sear: "The heat of the Forge-Warden sears {who} (-{n}).",
    abilities: [["Hammer slam", "every third turn, the hammer comes down on the whole front row, and some are knocked flat"],
      ["Forge heat", "every blow struck on it sears the striker (arrows don't); fire does it little, frost bites deep"]],
    intro: "The forge is lit. Between the anvils something of iron and stone, that the dwarves made to keep their door, turns its head; the light in its chest comes up like a bellows. The Forge-Warden.",
    fall: "The Forge-Warden stops, the light in its chest going out an inch at a time, and the iron ticks as it cools.",
    take: "Its hammer lies where it dropped it, still warm. Under the forge-floor, the shaft goes down.",
    lore: "The dwarves made a warden for their door and went down to the deep halls without it, trusting it. It is still here. They are not.",
    relic: { name: "Forge-Warden's Hammer", kind: "weapon", slot: "weapon", power: 10, value: 1400, props: { relic: true, element: "fire", twohanded: true, stun: 0.25 } },
    lair: { name: "The Forge", lore: "g:forge", rows: ["#####W#####", "#e.v...v.e#", "#e#.....#e#", "#e...B...e#", "#e#.....#e#", "#e.v...v.e#", "#####D#####"] } },
  // the Deep's guardians, one every five floors, and the thing at the bottom
  queen: { floor: 25, name: "The Drowned Queen", colour: "#5A7A8A", body: "tall", head: "pale", eyes: "#A0F0FF", extras: ["crown", "robe", "weed"], speed: 9, size: 1.0,
    hp: 560, atk: 44, df: 22, xp: 4200, gold: 3000, touch: { status: "sleep", chance: 0.25 }, weak: "holy", resist: "frost", undead: true, escorts: ["Drowned", "Drowned"], tint: "rgba(120,200,220,0.4)",
    moves: [{ kind: "ailment", status: "sleep", chance: 0.6, text: "The Drowned Queen opens her mouth, and what comes out is the whole drowned town's grief. Eyes close." },
      { kind: "summon", what: "Drowned", n: 2, max: 4, level: "deep", plural: "{n} of the drowned", text: "The Queen lifts a hand, and {n} climb out of the water." }],
    passives: ["rise"], riseText: "The Drowned Queen sinks... and rises again, the water streaming from her crown. The town will not let her go.",
    abilities: [["Lament", "every third turn, a grief the whole party may fall asleep to"], ["The court", "the drowned climb out of the water to her; killed, the water lifts her up again, once"]],
    intro: "In a hall the river took, a woman sits a throne with the water to her waist, and stands. The crown is the queen's. The face was. The Drowned Queen.",
    fall: "The Drowned Queen lets the crown slip from her head into the water, and follows it down, and does not come up.",
    take: "Her ring floats where she sank. Under the throne the water drains away, down the shaft.",
    lore: "The queen did not die of the plague. The carvings above say she did. The water knows what she died of, and who held her under.",
    relic: { name: "The Queen's Ring", kind: "ring", slot: "ring", power: 4, value: 1500, props: { relic: true, stat: "wis", resist: "sleep" } },
    lair: { name: "The Queen's Court", lore: "g:queen", flood: true, rows: ["#####W#####", "#....t....#", "#.#.....#.#", "#....B....#", "#.#.....#.#", "#.........#", "#####D#####"] } },
  mind: { floor: 30, name: "The Mycelial Mind", colour: "#9AB060", body: "wide", head: "round", eyes: "#F0FF90", extras: ["claws"], skin: "warts", speed: 5, size: 1.1,
    hp: 620, atk: 40, df: 20, xp: 5000, gold: 3400, touch: { status: "poison", chance: 0.3 }, weak: "fire", resist: "frost", undead: false, escorts: ["Fungal Horror"], tint: "rgba(180,240,120,0.4)",
    moves: [{ kind: "ailment", status: "poison", chance: 0.7, text: "The Mind exhales, and the air fills with spores." },
      { kind: "summon", what: "Spore Beast", n: 1, max: 3, level: "deep", word: "spore beast", text: "Something tears loose from the Mind's flank: {n}." }],
    passives: ["regrow"],
    abilities: [["Spores", "every third turn, a breath of spores that poisons most of the party"], ["The flesh of the floor", "it regrows a twentieth of itself every round, and spore beasts tear loose from it"]],
    intro: "The grotto glows green, and the glow is thinking. A mass of pale flesh the size of a house turns toward you without a face. The Mycelial Mind.",
    fall: "The Mycelial Mind blackens from the edges inward, and the glow of the grotto goes out with it.",
    take: "Where it grew thickest there is a cap of tough grey hide, light as cork, and under it the shaft.",
    lore: "Below the drowned town the dead were not buried. They were put down here, where something grew on them, and learned.",
    relic: { name: "Sporecap Helm", kind: "helm", slot: "helm", power: 5, value: 1500, props: { relic: true, resist: "poison", stat: "con" } },
    lair: { name: "The Spore Grotto", lore: "g:mind", rows: ["#####W#####", "#f.f...f.f#", "#.#.....#.#", "#f...B...f#", "#.#.....#.#", "#f.f...f.f#", "#####D#####"] } },
  tyrant: { floor: 35, name: "The Crystal Tyrant", colour: "#B898E0", body: "wide", head: "horns", eyes: "#FFFFFF", extras: ["crown"], skin: "stone", speed: 7, size: 1.1,
    hp: 700, atk: 50, df: 30, xp: 6000, gold: 4000, touch: null, weak: "frost", resist: "fire", undead: false, escorts: ["Crystal Golem"], tint: "rgba(220,200,255,0.45)",
    moves: [{ kind: "slam", frac: 3, status: "blind", chance: 0.35, front: false, text: "The Tyrant rings like a struck bell, and shards fly from it across the cavern!", how: " - flying shards", flat: "{who} is blinded by the glare!" }],
    passives: ["glass"], sear: "A shard of the Crystal Tyrant cuts {who} (-{n}).",
    abilities: [["Shatter", "every third turn, shards fly at everyone, and some are blinded"], ["Glass", "every blow struck on it cuts the striker (arrows don't); frost cracks it, fire does little"]],
    intro: "The cavern is one crystal, and at its heart something has grown a face and a crown of its own substance. It turns, slowly, singing. The Crystal Tyrant.",
    fall: "The Crystal Tyrant cracks across, and across again, and comes down in a long bright rain.",
    take: "One shard did not shatter: a prism the size of a fist, warm. Under the Tyrant's seat, the shaft.",
    lore: "The dwarves mined here until the crystal began to mine them. The deep halls were abandoned for this, not for the king.",
    relic: { name: "Prism Amulet", kind: "amulet", slot: "amulet", power: 0, value: 1800, props: { relic: true, df: 4, resist: "blind" } },
    lair: { name: "The Crystal Throne", lore: "g:tyrant", rows: ["#####W#####", "#c...t...c#", "#.#.....#.#", "#c...B...c#", "#.#.....#.#", "#c.......c#", "#####D#####"] } },
  master: { floor: 40, name: "The Foundry Master", colour: "#803020", body: "wide", head: "horns", eyes: "#FFD040", extras: ["wings", "hammer"], skin: "stone", speed: 9, size: 1.15,
    hp: 820, atk: 58, df: 28, xp: 7000, gold: 4800, touch: { status: "blind", chance: 0.15 }, weak: "frost", resist: "fire", undead: false, escorts: ["Foundry Imp", "Foundry Imp"], tint: "rgba(255,140,40,0.45)",
    moves: [{ kind: "breath", frac: 2, text: "The Foundry Master opens its furnace of a mouth, and fire pours over the whole party!" },
      { kind: "slam", frac: 2.5, status: "paralysis", chance: 0.3, front: true, text: "The Master's hammer comes down on the front line!", how: " - the hammer", flat: "{who} is knocked flat!" }],
    passives: ["heat"], sear: "The heat of the Foundry Master sears {who} (-{n}).",
    abilities: [["Furnace", "every third turn, fire over the whole party, or the hammer on the front line"], ["Forge heat", "every blow struck on it sears the striker; fire does it little, frost bites deep"]],
    intro: "The forges here never went out; something kept them. It stands up from the anvil, wings of beaten iron opening, and the heat comes off it in a wall. The Foundry Master.",
    fall: "The Foundry Master falls to its knees and then to the floor, and the iron of it rings as it cools, and goes dark.",
    take: "Its mail lies in plates where it fell, still warm: the Ember Mail. Under the great anvil, the shaft.",
    lore: "The king had the dwarves' forges relit for one work only. The masons' graves are the palace's foundations. The smiths' are here.",
    relic: { name: "Ember Mail", kind: "armor", slot: "armor", power: 10, value: 2200, props: { relic: true, df: 2, weight: "medium" } },
    lair: { name: "The Great Foundry", lore: "g:master", rows: ["#####W#####", "#e.v...v.e#", "#e#.....#e#", "#e...B...e#", "#e#.....#e#", "#e.v...v.e#", "#####D#####"] } },
  patriarch: { floor: 45, name: "The Bone Patriarch", colour: "#D8D0B8", body: "tall", head: "skull", eyes: "#80FF80", extras: ["staff", "robe"], speed: 10, size: 1.05,
    hp: 900, atk: 60, df: 30, xp: 8000, gold: 5600, touch: { status: "curse", chance: 0.3 }, weak: "holy", resist: "frost", undead: true, escorts: ["Bone Colossus"], tint: "rgba(160,255,160,0.4)",
    moves: [{ kind: "summon", what: "Skeleton", n: 2, max: 6, level: "deep", word: "skeleton", text: "The Patriarch raps his staff on the floor, and {n} rise from the heaps." },
      { kind: "ailment", status: "curse", chance: 0.5, text: "The Patriarch speaks a word that was old when the king was young, and a curse settles on the party." }],
    passives: ["drain"],
    abilities: [["The ossuary", "every third turn, skeletons rise from the heaps, or a word that curses the party"], ["Old hunger", "every blow of his draws experience out of the one it lands on"]],
    intro: "The first dead of Caer Duin were not laid in the catacombs. They were brought here, to him, and he has kept them. He stands, taller than a man has any right to be. The Bone Patriarch.",
    fall: "The Bone Patriarch comes apart a bone at a time, and the heaps around him settle, as if a long breath had gone out of them.",
    take: "On his breast, a reliquary of black iron on a chain: cold, and quiet now. Under his dais, the shaft.",
    lore: "The king's heart is kept apart, the physician wrote. He learned the way of it here, from one who had done it first.",
    relic: { name: "Patriarch's Reliquary", kind: "amulet", slot: "amulet", power: 0, value: 2400, props: { relic: true, df: 3, resist: "curse" } },
    lair: { name: "The Ossuary Chapel", lore: "g:patriarch", rows: ["#####W#####", "#n...t...n#", "#.#.....#.#", "#n...B...n#", "#.#.....#.#", "#n.......n#", "#####D#####"] } },
  root: { floor: 50, name: "The Root of the World", colour: "#4A2A2A", body: "wide", head: "round", eyes: "#FF5040", extras: ["claws"], skin: "warts", speed: 8, size: 1.25,
    hp: 1400, atk: 70, df: 34, xp: 12000, gold: 9000, touch: { status: "paralysis", chance: 0.2 }, weak: "fire", resist: "frost", undead: false, escorts: ["Rootling", "Rootling"], tint: "rgba(255,80,60,0.45)",
    moves: [{ kind: "slam", frac: 2.5, status: "paralysis", chance: 0.3, front: false, text: "The Root heaves, and the whole floor of the world shakes!", how: " - the quake", flat: "{who} is thrown down!" },
      { kind: "summon", what: "Rootling", n: 2, max: 4, level: "deep", word: "rootling", text: "{n} tear themselves out of the Root's bark." }],
    passives: ["regrow", "rise"], riseText: "The Root splits and sags... and knits, slowly, the sap running black. It is not done.",
    abilities: [["Quake", "every third turn, the whole floor shakes under everyone, and some are thrown down"], ["Rooted", "it regrows every round, rootlings tear out of it, and killed, it knits once more"]],
    intro: "There is no floor below this one. There is a root, and the root is the size of the world, and it has been dreaming the king's dreams for him. It wakes. The Root of the World.",
    fall: "The Root of the World shudders along its whole length, down into the dark no torch has reached, and is still. The silence afterwards is the first real silence the dungeon has had.",
    take: "There is nothing to take. There is nothing below. You have come to the bottom of the world.",
    lore: "Here the king's voice came from. Here it always came from. He only listened.",
    relic: null, final: true,
    lair: { name: "The Root", lore: "g:root", rows: ["#####W#####", "#r.e...e.r#", "#.#.....#.#", "#r...B...r#", "#.#.....#.#", "#r.e...e.r#", "#####D#####"] } },
};
CM.GUARDIAN_ORDER = ["rat", "knight", "forge", "queen", "mind", "tyrant", "master", "patriarch", "root"];
CM.echoOf = (floor) => (floor > CM.BOTTOM && floor % 10 === 0 ? Math.floor((floor - CM.BOTTOM) / 10) : 0);     // Endless: 60 -> 1, 70 -> 2 ... which echo (0: none)
CM.guardianFor = (floor) => (floor > CM.BOTTOM ? (CM.echoOf(floor) ? CM.GUARDIAN_ORDER[(CM.echoOf(floor) - 1) % CM.GUARDIAN_ORDER.length] : null)
  : Object.keys(CM.GUARDIANS).find((id) => CM.GUARDIANS[id].floor === floor) || null);
CM.guardianHas = (m, passive) => Boolean(m && m.guardian && CM.GUARDIANS[m.guardian] && (CM.GUARDIANS[m.guardian].passives || []).includes(passive));
CM.unmoved = (m) => Boolean(m && (m.boss || m.guardian));          // the Lich King and the guardians: not held, not put to sleep, not routed
// below the bottom (Endless) the carvings are not the story any more: they are the dream, still dreaming
CM.LORE_ENDLESS = [
  "There is no floor below this one, the carving says. You are standing on the floor below this one.",
  "The same hand, the same words, the same king. The dream did not end when the dreamer did.",
  "A mark you made yourself, you would swear, on a floor you have never been to.",
  "Here lie the first dead of Caer Duin, again. They are not tired of it. You will be.",
  "The water rose and never fell, the carving says, as it said forty floors up. It is drier here. It is lying.",
  "Turn back, in six languages. The seventh says: there is no back. There is only further.",
  "The dwarves' word for this place has no end. Neither does the place.",
  "Someone has started counting the floors here, and given up, and started again.",
];
// what a carving says: the floor's part of the story, an odd one, a guardian's (text "g:<guardian>") or the endless dark's ("e:<n>")
CM.loreText = (text) => (typeof text === "string" && text.startsWith("g:") ? (CM.GUARDIANS[text.slice(2)] || {}).lore || ""
  : typeof text === "string" && text.startsWith("e:") ? CM.LORE_ENDLESS[Number(text.slice(2)) % CM.LORE_ENDLESS.length]
  : text >= 0 ? CM.LORE[text] || CM.LORE[CM.LORE.length - 1] : CM.LORE_EXTRA[-text - 1] || CM.LORE_EXTRA[0]);

// what a monster sounds like, by kind (the sounds are cooked in 50-audio.js)
CM.roarFor = function (kind) {
  if (!kind) return "monster";
  if (kind === CM.BOSS.name) return "lich";
  const g = Object.values(CM.GUARDIANS).find((G) => G.name === kind);
  if (g) return g.undead ? "roar_undead" : g.body === "beast" ? "roar_beast" : "roar_big";
  const k = CM.monsterKind(kind), name = k ? k.name : kind;
  if (["Giant Rat", "Kobold", "Goblin", "Dark Elf", "Shard Wisp", "Rootling", "Foundry Imp", "Weed Hag"].includes(name)) return "roar_small";
  if (["Skeleton", "Zombie", "Ghoul", "Wraith", "Vampire", "Drowned", "Grave Priest", "Bone Colossus", "Hollow One"].includes(name)) return "roar_undead";
  if (["Wyvern", "Spore Beast", "Iron Hound"].includes(name)) return "roar_beast";
  return "roar_big";
};

// the depths: what the stone looks like down there, how far the torch reaches, what the dark is made of
CM.THEMES = [
  { name: "The Catacombs", floors: [1, 5], stone: [118, 104, 88], mortar: [52, 44, 36], floor: [92, 80, 66], ceiling: [60, 52, 44],
    moss: [70, 90, 50], fog: [0.04, 0.03, 0.02], torch: [1.0, 0.82, 0.58], reach: 5.5, bones: 0.25 },
  { name: "The Flooded Vaults", floors: [6, 10], stone: [92, 100, 96], mortar: [38, 44, 42], floor: [60, 72, 70], ceiling: [44, 52, 50],
    moss: [40, 90, 70], fog: [0.02, 0.04, 0.045], torch: [0.9, 0.85, 0.7], reach: 5.0, bones: 0.1 },
  { name: "The Dwarven Halls", floors: [11, 15], stone: [104, 92, 84], mortar: [40, 34, 30], floor: [84, 74, 64], ceiling: [56, 48, 42],
    moss: [120, 90, 50], fog: [0.03, 0.025, 0.02], torch: [1.0, 0.75, 0.45], reach: 6.0, bones: 0.05 },
  { name: "The Lich King's Palace", floors: [16, 20], stone: [78, 84, 100], mortar: [28, 30, 40], floor: [50, 54, 70], ceiling: [36, 38, 52],
    moss: [60, 110, 130], fog: [0.015, 0.025, 0.045], torch: [0.75, 0.85, 1.0], reach: 4.5, bones: 0.4 },
  // the Deep, below him: six bands more (their Stone theme borrows the photos of a band above, in their own colour)
  { name: "The Drowned Town", floors: [21, 25], stone: [54, 70, 84], mortar: [22, 30, 38], floor: [40, 52, 60], ceiling: [30, 38, 46],
    moss: [40, 100, 90], fog: [0.02, 0.035, 0.05], torch: [0.8, 0.9, 1.0], reach: 4.5, bones: 0.15, photos: "t1" },
  { name: "The Fungal Deep", floors: [26, 30], stone: [60, 80, 50], mortar: [26, 36, 20], floor: [48, 60, 36], ceiling: [34, 44, 26],
    moss: [120, 200, 90], fog: [0.02, 0.04, 0.02], torch: [0.85, 1.0, 0.7], reach: 5.0, bones: 0.05, photos: "t1" },
  { name: "The Crystal Caverns", floors: [31, 35], stone: [96, 80, 120], mortar: [40, 32, 56], floor: [70, 60, 90], ceiling: [50, 42, 66],
    moss: [200, 160, 255], fog: [0.03, 0.025, 0.05], torch: [0.9, 0.85, 1.0], reach: 6.0, bones: 0.02, photos: "t3" },
  { name: "The Foundry", floors: [36, 40], stone: [70, 56, 48], mortar: [30, 22, 18], floor: [56, 44, 36], ceiling: [40, 30, 24],
    moss: [200, 90, 30], fog: [0.04, 0.025, 0.015], torch: [1.0, 0.7, 0.4], reach: 5.5, bones: 0.05, photos: "t2" },
  { name: "The Ossuary", floors: [41, 45], stone: [120, 112, 96], mortar: [60, 54, 44], floor: [96, 88, 74], ceiling: [70, 64, 54],
    moss: [150, 140, 110], fog: [0.035, 0.03, 0.025], torch: [1.0, 0.9, 0.7], reach: 5.0, bones: 0.8, photos: "t0" },
  { name: "The Root of the World", floors: [46, 50], stone: [60, 30, 30], mortar: [26, 10, 10], floor: [44, 22, 22], ceiling: [30, 14, 14],
    moss: [140, 40, 40], fog: [0.05, 0.015, 0.015], torch: [1.0, 0.6, 0.5], reach: 4.0, bones: 0.3, photos: "t1" },
];
CM.AMBIENCE_OF = [0, 1, 2, 3, 1, 0, 3, 2, 0, 3];                      // which of the four ambiences (and footfalls) each band uses
CM.themeFor = (number) => (number > CM.BOTTOM ? CM.THEMES[Math.floor((number - CM.BOTTOM - 1) / 5) % CM.THEMES.length]      // (Endless: below the bottom the bands come round again, five floors each)
  : CM.THEMES.find((t) => number >= t.floors[0] && number <= t.floors[1]) || CM.THEMES[CM.THEMES.length - 1]);
CM.themeIndex = (number) => Math.max(0, CM.THEMES.indexOf(CM.themeFor(number)));

CM.KEYS_HELP = [
  ["W / Up", "forward"], ["S / Down", "back"], ["A / Left", "turn left"], ["D / Right", "turn right"], ["Q / E", "sidestep"],
  ["Space", "use: a chest, the stairs, a fountain, a lever, someone to talk to - or search the wall you face"], ["I", "inventory"], ["J", "the journal: everything read and heard"],
  ["1 - 4", "a hero's sheet: stats, row, ailments, a boon when they level"], ["Tab", "the automap, large (click a square to walk there; right-click for a note)"], ["X", "explore: walk to the nearest unexplored square"], ["Esc", "close a screen / pause"],
  ["F", "fight the chosen foe"], ["C", "cast a spell or use a skill (and between fights: healing, Light)"], ["P", "an item"],
  ["D", "defend: half the blows until their next turn"], ["R", "run"], ["A", "auto: the party fights on by itself, until someone is badly hurt"], ["Tab / click a foe", "choose the foe"],
  ["1 - 9", "pick from a list"], ["F3", "frames per second"],
];
