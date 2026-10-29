"use strict";
// What there is: the classes, the gear, the monsters, the depths and what they look like.

CM.DIRS = [[0, -1], [1, 0], [0, 1], [-1, 0]];              // north, east, south, west (x, y on the grid)
CM.DIR_NAMES = "NESW";
CM.LAST_FLOOR = 20;
CM.CAMP_AFTER = [5, 10, 15];                               // a merchant's camp waits below these floors

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
CM.ARMORS = ["Padded Vest", "Leather Armor", "Studded Leather", "Ring Mail", "Scale Mail", "Chain Mail", "Banded Mail",
  "Plate Mail", "Elven Mail", "Mithril Plate", "Dragon Scale", "Aegis of Claude"];

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
  { name: "Zombie", colour: "#7A9A70", body: "biped", head: "round", eyes: "#D0FFD0", extras: ["torn"], speed: 4, undead: true, touch: { status: "poison", chance: 0.12 } },
  { name: "Orc", colour: "#4A7A3A", body: "wide", head: "tusks", eyes: "#FFE040", extras: ["axe"], speed: 9, ability: "savage" },
  { name: "Ghoul", colour: "#9AA0A0", body: "thin", head: "round", eyes: "#80FF80", extras: ["claws"], speed: 10, undead: true, touch: { status: "paralysis", chance: 0.15 } },
  { name: "Dark Elf", colour: "#5A4A8A", body: "tall", head: "hood", eyes: "#FF80FF", extras: ["bow"], speed: 13, ability: "ranged", touch: { status: "sleep", chance: 0.12 } },
  { name: "Troll", colour: "#3A6A50", body: "wide", head: "round", eyes: "#FFE040", extras: ["club", "claws"], speed: 7, ability: "regen" },
  { name: "Wraith", colour: "#6A7AA0", body: "ghost", head: "hood", eyes: "#A0E0FF", extras: [], speed: 12, undead: true, ability: "drain", touch: { status: "curse", chance: 0.12 } },
  { name: "Ogre", colour: "#A08050", body: "wide", head: "round", eyes: "#FFE040", extras: ["club"], speed: 6, ability: "stun" },
  { name: "Minotaur", colour: "#7A4A30", body: "wide", head: "horns", eyes: "#FF5040", extras: ["axe"], speed: 10, ability: "charge" },
  { name: "Gargoyle", colour: "#707078", body: "wide", head: "horns", eyes: "#FFE040", extras: ["wings"], speed: 8, touch: { status: "stone", chance: 0.06 } },
  { name: "Vampire", colour: "#8A2030", body: "tall", head: "pale", eyes: "#FF3030", extras: ["cape"], speed: 13, undead: true, ability: "lifesteal", touch: { status: "sleep", chance: 0.12 } },
  { name: "Demon", colour: "#C03020", body: "wide", head: "horns", eyes: "#FFE040", extras: ["wings", "claws"], speed: 11, ability: "breath", touch: { status: "blind", chance: 0.12 } },
  { name: "Wyvern", colour: "#407A70", body: "beast", head: "snout", eyes: "#FFE040", extras: ["wings", "tail"], speed: 12, ability: "buffet", touch: { status: "poison", chance: 0.2 } },
];
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

CM.abilitiesFor = (hero) => Object.keys(CM.ABILITIES).filter((id) => {
  const at = CM.ABILITIES[id].cls[hero.cls];
  return at !== undefined && hero.level >= at;
});

// the Lich King: what he does as the fight goes
CM.LICH = { summonEvery: 3, summonMax: 4, coldFrom: 0.3, summonFrom: 0.6, riseTo: 0.4 };
CM.BOSS = { name: "The Lich King", colour: "#A0E0FF", body: "tall", head: "skull", eyes: "#40F0FF", extras: ["crown", "staff", "robe"] };

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
];
CM.themeFor = (number) => CM.THEMES.find((t) => number >= t.floors[0] && number <= t.floors[1]) || CM.THEMES[CM.THEMES.length - 1];
CM.themeIndex = (number) => Math.max(0, CM.THEMES.indexOf(CM.themeFor(number)));

CM.KEYS_HELP = [
  ["W / Up", "forward"], ["S / Down", "back"], ["A / Left", "turn left"], ["D / Right", "turn right"], ["Q / E", "sidestep"],
  ["Space", "use: a chest, the stairs, a fountain, a lever - or search the wall you face"], ["I", "inventory"],
  ["1 - 4", "a hero's sheet: stats, row, ailments, a boon when they level"], ["Tab", "the automap, large"], ["Esc", "close a screen / pause"],
  ["F", "fight the chosen foe"], ["C", "cast a spell or use a skill (and between fights: healing, Light)"], ["P", "an item"],
  ["D", "defend: half the blows until their next turn"], ["R", "run"], ["Tab / click a foe", "choose the foe"],
  ["1 - 9", "pick from a list"], ["F3", "frames per second"],
];
