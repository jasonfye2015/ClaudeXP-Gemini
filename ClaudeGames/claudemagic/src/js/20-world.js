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
    else { name = CM.WEAPONS[tier]; power = (tier + 1) * 2 + rnd.int(0, 2); value = 15 * (tier + 1) * (tier + 1); if (CM.TWO_HANDED.includes(name)) props.twohanded = true; }
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
  }
  if ((kind === "weapon" || kind === "armor" || kind === "shield" || kind === "helm") && rnd.chance(0.15)) { props.bonus = 1; power += 2; value += 40; }
  if (floor >= 4 && (kind === "weapon" || kind === "armor") && rnd.chance(0.08)) { props.cursed = true; power = Math.max(1, power - 3); value = Math.floor(value / 3); }
  const item = { name, kind: slot === "offhand" ? "shield" : kind, slot, power, value, props };
  if (floor >= 2 && rnd.chance(0.5)) item.unknown = true;
  return item;
};

CM.scroll = (id) => ({ name: CM.SCROLLS[id].name, kind: "scroll", spell: id, power: 0, value: 40 });
CM.wand = (id, charges) => ({ name: CM.WANDS[id].name, kind: "wand", spell: id, power: 0, charges, value: 90 });

CM.makeItem = function (floor, rnd, kind) {
  kind = kind || rnd.pick(["weapon", "weapon", "weapon", "armor", "armor", "armor", "potion", "potion", "potion", "potion", "potion",
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
  let n = item.name.replace(/ \+\d+$/, "");
  for (const e of Object.values(CM.ELEMENTS)) if (n.startsWith(e.prefix + " ")) n = n.slice(e.prefix.length + 1);
  return n;
};

// what an item is, in words
CM.itemLabel = function (item) {
  if (item.unknown) return "unknown: wear it, read a Scroll of Identify, or ask the camp's scribe";
  const p = item.props || {}, bits = [];
  if (item.kind === "weapon") bits.push(`weapon +${item.power}`);
  else if (item.kind === "armor") bits.push(`armour +${item.power}`, p.weight || "");
  else if (item.kind === "shield") bits.push(`shield +${item.power}`);
  else if (item.kind === "helm") bits.push(`helm +${item.power}`);
  else if (item.kind === "ring") bits.push(`+${item.power} ${CM.STAT_NAMES[p.stat]}`);
  else if (item.kind === "amulet") bits.push(p.resist ? `proof against ${p.resist}` : `warding +${p.df}`);
  else if (item.kind === "scroll") bits.push(CM.SCROLLS[item.spell].what);
  else if (item.kind === "wand") bits.push(`${CM.WANDS[item.spell].what} ${CM.plural(item.charges, "charge")}.`);
  if (p.stat && item.kind !== "ring") bits.push(`+${item.power} ${CM.STAT_NAMES[p.stat]}`);
  if (p.resist && item.kind !== "amulet") bits.push(`proof against ${p.resist}`);
  if (p.df && item.kind !== "amulet") bits.push(`warding +${p.df}`);
  if (p.element) bits.push(p.element);
  if (p.stun) bits.push("a blow may leave the foe reeling");
  if (p.twohanded) bits.push("two-handed");
  if (p.relic) bits.push("a guardian's relic");
  if (p.bow) bits.push("a bow: the Ranger's");
  if (p.cursed) bits.push("CURSED");
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
  if (CM.guardianFor(number) || number <= 2 || number >= CM.LAST_FLOOR - 1) return null;
  const h = (what, n) => CM.hashSeed(`${seed}:special:${what}:${n}`);
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
CM.bones = (ghost) => ({ name: "Someone's bones", kind: "bones", power: 0, value: 0, ghost });

// one monster of a kind, at a depth - with what the kind does carried on it, so a save stands alone
CM.makeMonster = function (kind, level, rnd) {
  return { name: kind.name, kind: kind.name, colour: kind.colour, hp: 8 + level * 6, max: 8 + level * 6, atk: 3 + level * 2, df: level,
    xp: 10 + level * 8, gold: rnd.int(2, 8) * level, speed: kind.speed || 10, undead: Boolean(kind.undead), ability: kind.ability || null,
    touch: kind.touch ? Object.assign({}, kind.touch) : null };
};

// a monster saved before it knew what it does
CM.upgradeMonster = function (m) {
  if (m.kind) return m;
  const kind = CM.monsterKind(m.name);
  m.kind = kind ? kind.name : m.name;
  if (kind) { m.speed = kind.speed || 10; m.undead = Boolean(kind.undead); m.ability = kind.ability || null; m.touch = kind.touch ? Object.assign({}, kind.touch) : null; }
  else { m.speed = m.speed || (m.boss ? 12 : 10); m.undead = Boolean(m.undead || m.boss); m.ability = m.ability || null; m.touch = m.touch || null; }
  return m;
};

// a group: one kind, or (deeper down) two; now and then with a leader out of the ordinary
CM.monsterGroup = function (floor, rnd) {
  const top = Math.min(CM.MONSTERS.length - 1, Math.floor(floor * CM.MONSTERS.length / CM.LAST_FLOOR));
  const kind = CM.MONSTERS[rnd.int(Math.max(0, top - 2), top)];
  const count = rnd.int(1, 2 + Math.floor(floor / 6));
  const group = [];
  for (let i = 0; i < count; i++) group.push(CM.makeMonster(kind, floor, rnd));
  if (floor >= 4 && count >= 2 && rnd.chance(0.35)) {                   // mixed company: the second kind, a step down
    const other = CM.MONSTERS[Math.max(0, CM.MONSTERS.indexOf(kind) - rnd.int(1, 2))];
    if (other !== kind) for (let i = Math.floor(count / 2); i < count; i++) group[i] = CM.makeMonster(other, floor, rnd);
  }
  if (floor >= 3 && rnd.chance(0.12)) {                                  // a leader
    const id = rnd.pick(Object.keys(CM.ELITES)), e = CM.ELITES[id], m = group[0];
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
  }
  return group;
};

CM.bossMonster = () => ({ name: CM.BOSS.name, kind: CM.BOSS.name, colour: CM.BOSS.colour, hp: 650, max: 650, atk: 46, df: 18, xp: 5000, gold: 5000,
  boss: true, speed: 12, undead: true, ability: null, touch: { status: "curse", chance: 0.2 } });
CM.skeleton = (level, rnd) => CM.makeMonster(CM.MONSTERS[2], level, rnd);

// a guardian (CM.GUARDIANS), ready to fight, with the company it keeps; and the relic it leaves behind
CM.guardianMonster = function (id) {
  const G = CM.GUARDIANS[id];
  return { name: G.name, kind: G.name, colour: G.colour, hp: G.hp, max: G.hp, atk: G.atk, df: G.df, xp: G.xp, gold: G.gold, guardian: id, speed: G.speed,
    undead: Boolean(G.undead), ability: null, touch: G.touch ? Object.assign({}, G.touch) : null, turns: 0 };
};
CM.guardianGroup = function (id, floor, rnd) {
  const group = [CM.guardianMonster(id)];
  for (const name of CM.GUARDIANS[id].escorts || []) group.push(CM.makeMonster(CM.monsterKind(name), floor, rnd));
  return group;
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
CM.xpForLevel = (level) => Math.ceil(60 * Math.pow(level - 1, 1.6));     // the experience a level asks for (the old game's curve)

// the numbers a hero fights with, from class, level, stats and boons (health and magic stay where they were, within the new most)
CM.recompute = function (h) {
  const c = CM.CLASSES[h.cls] || CM.CLASSES.Knight, L = h.level - 1, s = {};
  for (const st of CM.STATS) s[st] = CM.heroStat(h, st);                 // (rings count)
  const boons = h.boons || [];
  h.max = Math.max(1, c.hp + (s.con - 10) + L * (c.grow + CM.mod(s.con, 3)));
  h.maxmp = c.mp ? Math.max(0, c.mp + (s[c.key] - 10) + L * 3) : 0;
  const hitStat = c.key === "dex" ? s.dex : s.str;
  h.atk = Math.max(1, c.atk + CM.mod(hitStat) + L * c.atkGrow);
  h.df = Math.max(0, c.df + CM.mod(s.dex, 3) + Math.floor(L / 2) + (boons.includes("ironskin") ? 2 : 0));
  h.hp = Math.min(h.hp, h.max);
  h.mp = Math.min(h.mp, h.maxmp);
  return h;
};

CM.makeHero = function (cls, name, stats, row) {
  const c = CM.CLASSES[cls];
  const h = { name: (name || "").trim() || cls, cls, level: 1, xp: 0, hp: 1, max: 1, mp: 0, maxmp: 0, atk: 1, df: 0,
    stats: stats || CM.rollStats(cls), row: row || c.row, status: {}, boons: [], pending: 0, offer: null,
    weapon: { name: c.weapon, kind: "weapon", slot: "weapon", power: 1, value: 5, props: c.weapon === "Short Bow" ? { bow: true, twohanded: true } : {} },
    armor: { name: c.armor, kind: "armor", slot: "armor", power: 0, value: 5, props: { weight: "light" } },
    offhand: null, helm: null, ring: null, amulet: null };
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
  for (const slot of ["offhand", "helm", "ring", "amulet"]) if (h[slot] === undefined) h[slot] = null;
  for (const slot of ["weapon", "armor"]) if (h[slot]) { h[slot].props = h[slot].props || {}; h[slot].slot = slot; }
  return h;
};

CM.equipped = (h) => CM.SLOTS.map((s) => h[s]).filter(Boolean);

// a stat as it stands, rings and all
CM.heroStat = function (h, s) {
  let v = h.stats && h.stats[s] !== undefined ? h.stats[s] : 10;
  for (const it of CM.equipped(h)) if (it.props && it.props.stat === s && !it.unknown) v += it.power;
  return v;
};

// what the gear keeps off: armour and shield count double, a helm and a warding amulet once
CM.gearDefence = (h) => (h.armor ? h.armor.power : 0) * 2 + (h.offhand ? h.offhand.power * 2 : 0) + (h.helm ? h.helm.power : 0)
  + CM.equipped(h).reduce((s, it) => s + ((it.props || {}).df || 0), 0);

// may this hero wear or wield it? "" when they may, else why not
CM.cantWear = function (h, item) {
  const p = item.props || {};
  if (item.kind === "weapon" && p.bow && h.cls !== "Ranger") return `Only a Ranger draws a bow.`;
  if (item.kind === "armor") {
    const w = p.weight || CM.ARMOR_WEIGHT(Math.max(0, CM.ARMORS.indexOf(CM.baseName(item)))), rank = { light: 0, medium: 1, heavy: 2 };
    if (rank[w] > rank[CM.BEARS[h.cls] || "light"]) return `${h.cls}s can't fight in ${w} armour.`;
  }
  if (item.kind === "shield") {
    if (!CM.SHIELD_BEARERS.includes(h.cls)) return `${h.cls}s don't carry shields.`;
    if (h.weapon && h.weapon.props && h.weapon.props.twohanded) return `${h.name}'s ${CM.baseName(h.weapon)} takes both hands.`;
  }
  return "";
};

CM.newParty = function (chosen) {                                         // chosen: [{cls, name, stats, row}] - else the classic four
  return (chosen || CM.CLASSIC.map((cls) => ({ cls }))).map((p) => CM.makeHero(p.cls, p.name, p.stats, p.row));
};

// someone to hire at the camp: a calling, a name, a roll, a level a step behind the party's
CM.makeRecruit = function (level, rnd) {
  const cls = rnd.pick(CM.CLASS_ORDER), h = CM.makeHero(cls, CM.randomName(rnd), CM.rollStats(cls, rnd));
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
  return Object.keys(CM.KITS).filter((id) => CM.KITS[id].need === 0 || (CM.KITS[id].need > 20 ? d.won : d.floor >= CM.KITS[id].need));
};
CM.dailySeed = (date) => { const d = date || new Date(); return `daily-${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`; };

// what the party could do with: a line or two of advice, and whether it's sound
CM.partyAdvice = function (party) {
  const notes = [], roles = party.map((p) => p.cls), rows = party.map((p) => p.row || CM.CLASSES[p.cls].row);
  const front = rows.filter((r) => r === "front").length;
  const healers = roles.filter((c) => ["Cleric", "Paladin", "Druid", "Bard"].includes(c)).length;
  const area = roles.filter((c) => ["Mage", "Druid", "Ranger"].includes(c)).length;
  const casters = roles.filter((c) => CM.CLASSES[c].mp > 0).length;
  if (front === 0) notes.push("No one up front: the monsters will reach whoever they like.");
  else if (front === 1) notes.push("Only one hero up front will take most of the blows - a second would share them.");
  else if (front >= 3) notes.push("Three or more in the front row: the back row's reach is wasted, and all of them get hit.");
  if (!healers) notes.push("No one can heal. Potions will have to do, and they run out.");
  if (!area) notes.push("No spell or volley that hits more than one foe: big groups will wear you down.");
  if (casters >= 3) notes.push("Three casters: strong magic, thin armour. Keep the Knight or Paladin alive.");
  if (!roles.some((c) => ["Knight", "Paladin"].includes(c))) notes.push("Without a Knight or Paladin, nothing draws the monsters' attention.");
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
CM.LORE = [
  "Here lie the first dead of Caer Duin. King Mordeth wept for each of them. He would not always.",
  "The plague came up the river in the king's twelfth year. The priests said it would pass. It did not pass.",
  "When the queen died, Mordeth shut the gates and had the bells taken down. No one has rung one since.",
  "The king sent for every book that spoke of death, and for every man who claimed to have come back from it.",
  "Below this floor the water rose and never fell. The lower town drowned in a single night, doors still barred.",
  "A stranger came from the east with a box he would not open. He left without it. The king kept it by his bed.",
  "The court physician wrote: the king no longer sleeps, and says he no longer needs to. I have begun to believe him.",
  "The dwarves of the deep halls traded with Caer Duin for three hundred years. Their last letter asked why the king's coin was cold.",
  "Here the guard turned back. Beyond this point the king's orders came written in a hand that was not quite his.",
  "They burned the physician's notes. One page survived: the heart may be kept apart, and the body need not know.",
  "The dwarves sealed their doors from the inside. The seals held for a year. Then the doors opened, and nothing came out.",
  "A child's letters, scratched here: MOTHER SAYS THE KING IS STILL OUR KING. MOTHER SAYS NOT TO LOOK AT HIM.",
  "The halls below were made for a people who loved stone. They would not have left them. They did not leave them.",
  "The last captain of the guard wrote his name here before he went down. The king had asked for him by name.",
  "Whoever reads this: the thing that wears the crown remembers being Mordeth. That is the worst of it.",
  "The palace was built in a year, by hands that did not tire. The masons' graves are the foundations.",
  "He keeps the court. They sit where they sat. If you listen you can hear them not breathing.",
  "The box from the east is empty now. What was in it, he put somewhere safer. Somewhere nearer his heart.",
  "The king's heart is not in his chest. Find it, and he can be ended. Fail, and he will rise as often as you kill him.",
  "Beyond this door he waits. He has waited so long that he has forgotten what for. Remind him.",
];
CM.LORE_EXTRA = [
  "A recipe for barley bread, carved with great care, as if it mattered more than anything.",
  "Tally marks. Hundreds. The last row stops in the middle of a stroke.",
  "THE WATER IS NOT WATER, scratched deep, and under it in a smaller hand: it is, though.",
  "A map of a floor you haven't seen. The stairs are marked. So is something else, with a circle round it.",
  "Here Aldous the Lesser slew a troll with a chair. The chair is remembered more fondly than Aldous.",
  "Someone has carved a window here, with a view. They put a great deal of work into the sky.",
  "Turn back, in six languages. The seventh says: or don't - he's lonely.",
  "A prayer to a god whose name has been chiselled out. The prayer is still there, which seems rude.",
];

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
CM.makeFloor = function (number, seed) {
  const rnd = new CM.Random(CM.hashSeed(`${seed}:floor:${number}`));
  const size = Math.min(17 + Math.floor(number / 4) * 2, 27);
  const grid = [];
  for (let y = 0; y < size; y++) grid.push(new Array(size).fill(1));
  const special = CM.specialFor(number, seed);
  const floor = { number, grid, pos: [1, 1], facing: 2, things: {}, features: {}, dark: [], seen: [], rooms: [], decor: [], special };
  const rooms = [];                            // {x0, y0, x1, y1 (interior, inclusive), template?, entrances: [[x,y,kind]]}
  const taken = (x0, y0, x1, y1) => rooms.some((r) => x0 <= r.x1 + 2 && x1 >= r.x0 - 2 && y0 <= r.y1 + 2 && y1 >= r.y0 - 2);
  const carve = (x0, y0, x1, y1) => { for (let y = y0; y <= y1; y++) for (let x = x0; x <= x1; x++) grid[y][x] = 0; };

  // set pieces first (one or two, where they fit), then ordinary rooms
  const guardian = CM.guardianFor(number), lair = guardian ? CM.GUARDIANS[guardian].lair : null;
  const wanted = CM.TEMPLATES.filter((t) => number >= t.min && !(number === CM.LAST_FLOOR && t.name === "Pit Room"));
  rnd.shuffle(wanted);
  const chosen = special === "maze" ? [] : wanted.slice(0, number >= 6 ? 2 : 1);
  if (lair) chosen.unshift(lair);                                   // (the guardian's lair first, and away from the top left, where the party starts)
  for (const tpl of chosen) {
    const h = tpl.rows.length - 2, w = tpl.rows[0].length - 2;
    const spots = [];
    if (tpl === lair) {
      for (let i = 0; i <= Math.floor((size - 6 - w) / 2); i++) for (let j = 0; j <= Math.floor((size - 6 - h) / 2); j++) spots.push([3 + 2 * i, 3 + 2 * j]);
      const reach = Math.max(...spots.map(([x, y]) => x + y));
      spots.splice(0, spots.length, ...spots.filter(([x, y]) => x + y >= reach * 0.6));
    }
    for (let tries = 0; tries < 40; tries++) {
      const [x0, y0] = tpl === lair ? rnd.pick(spots) : [3 + 2 * rnd.int(0, Math.floor((size - 6 - w) / 2)), 3 + 2 * rnd.int(0, Math.floor((size - 6 - h) / 2))];
      const x1 = x0 + w - 1, y1 = y0 + h - 1;
      if (x1 > size - 4 || y1 > size - 4 || taken(x0, y0, x1, y1)) continue;         // (room for the maze beyond every entrance)
      const room = { x0, y0, x1, y1, template: tpl, entrances: [], fill: [], pillars: [] };
      let fits = true;
      tpl.rows.forEach((row, ry) => [...row].forEach((c, rx) => {
        const x = x0 - 1 + rx, y = y0 - 1 + ry;
        const onRing = ry === 0 || ry === tpl.rows.length - 1 || rx === 0 || rx === row.length - 1;
        if ("DLGS".includes(c)) {
          const onSide = ry === 0 || ry === tpl.rows.length - 1;
          if ((onSide && x % 2 === 0) || (!onSide && y % 2 === 0)) fits = false;      // (the maze won't come up to it)
          room.entrances.push([x, y, c]);
        } else if (c === "#" && !onRing) room.pillars.push([x, y]);                  // (a pillar inside: on even coordinates, where the maze never goes)
        else if (c !== "#" && c !== "W") room.fill.push([x, y, c]);
      }));
      if (!fits) continue;
      carve(x0, y0, x1, y1);
      for (const [px, py] of room.pillars) grid[py][px] = 1;
      rooms.push(room);
      break;
    }
  }
  const roomTries = special === "maze" ? 2 : 14 + number;
  for (let i = 0; i < roomTries; i++) {
    const w = special === "maze" ? 3 : 3 + 2 * rnd.int(0, 1 + Math.floor(number / 7)), h = special === "maze" ? 3 : 3 + 2 * rnd.int(0, 1);
    const x0 = 1 + 2 * rnd.int(0, Math.floor((size - 2 - w) / 2)), y0 = 1 + 2 * rnd.int(0, Math.floor((size - 2 - h) / 2));
    const x1 = x0 + w - 1, y1 = y0 + h - 1;
    if (x1 >= size - 1 || y1 >= size - 1 || taken(x0, y0, x1, y1)) continue;
    carve(x0, y0, x1, y1);
    rooms.push({ x0, y0, x1, y1, entrances: [], fill: [] });
  }

  // the maze between the rooms
  for (let sy = 1; sy < size - 1; sy += 2) for (let sx = 1; sx < size - 1; sx += 2) {
    if (grid[sy][sx] !== 1) continue;
    const stack = [[sx, sy]];
    grid[sy][sx] = 0;
    while (stack.length) {
      const [x, y] = stack[stack.length - 1];
      const options = CM.DIRS.filter(([dx, dy]) => x + dx * 2 > 0 && x + dx * 2 < size - 1 && y + dy * 2 > 0 && y + dy * 2 < size - 1
        && grid[y + dy * 2][x + dx * 2] === 1 && grid[y + dy][x + dx] === 1);
      if (!options.length) { stack.pop(); continue; }
      const [dx, dy] = rnd.pick(options);
      grid[y + dy][x + dx] = 0;
      grid[y + dy * 2][x + dx * 2] = 0;
      stack.push([x + dx * 2, y + dy * 2]);
    }
  }

  // join the regions: one way between each pair, and a few more for the loops
  const region = new Map();
  let regions = 0;
  for (let y = 0; y < size; y++) for (let x = 0; x < size; x++) {
    if (grid[y][x] !== 0 || region.has(key(x, y))) continue;
    const id = regions++, queue = [[x, y]];
    region.set(key(x, y), id);
    for (let i = 0; i < queue.length; i++) {
      for (const [dx, dy] of CM.DIRS) {
        const nx = queue[i][0] + dx, ny = queue[i][1] + dy;
        if (ny > 0 && ny < size && nx > 0 && nx < size && grid[ny][nx] === 0 && !region.has(key(nx, ny))) { region.set(key(nx, ny), id); queue.push([nx, ny]); }
      }
    }
  }
  const templateWall = new Set(), templateDoor = new Map();
  for (const r of rooms) if (r.template) {
    for (let y = r.y0 - 1; y <= r.y1 + 1; y++) for (let x = r.x0 - 1; x <= r.x1 + 1; x++) templateWall.add(key(x, y));
    for (const [x, y, c] of r.entrances) templateDoor.set(key(x, y), c);
  }
  let connectors = [];
  for (let y = 1; y < size - 1; y++) for (let x = 1; x < size - 1; x++) {
    if (grid[y][x] !== 1) continue;
    const k = key(x, y);
    if (templateWall.has(k) && !templateDoor.has(k)) continue;
    const a = region.get(key(x - 1, y)), b = region.get(key(x + 1, y)), c = region.get(key(x, y - 1)), d = region.get(key(x, y + 1));
    if (a !== undefined && b !== undefined && a !== b && c === undefined && d === undefined) connectors.push([x, y, a, b]);
    else if (c !== undefined && d !== undefined && c !== d && a === undefined && b === undefined) connectors.push([x, y, c, d]);
  }
  const merged = new Map();
  const find = (id) => { while (merged.has(id)) id = merged.get(id); return id; };
  const loops = [], doorways = [];
  rnd.shuffle(connectors);
  connectors.sort((p, q) => (templateDoor.has(key(q[0], q[1])) ? 1 : 0) - (templateDoor.has(key(p[0], p[1])) ? 1 : 0));   // (set pieces first)
  for (const [x, y, a, b] of connectors) {
    const ra = find(a), rb = find(b);
    const k = key(x, y);
    if (ra !== rb) {
      grid[y][x] = 0;
      merged.set(rb, ra);
      doorways.push([x, y]);
      if (templateDoor.has(k)) floor.features[k] = { type: { D: "door", L: "door", G: "gate", S: "secret" }[templateDoor.get(k)], open: false };
    } else if (!templateDoor.has(k) && rnd.chance(0.06)
               && ![...doorways, ...loops].some(([ox, oy]) => Math.abs(ox - x) + Math.abs(oy - y) <= 2)) {
      loops.push([x, y]);                     // (a second way round: open, or a secret door - not beside another way)
    }
  }
  for (const [x, y] of loops) {
    if (rnd.chance(0.5) && number >= 2) { floor.features[key(x, y)] = { type: "secret", found: false }; }
    else { grid[y][x] = 0; doorways.push([x, y]); }
  }
  // template entrances: locked, gated, secret - as the template says
  for (const r of rooms) if (r.template) for (const [x, y, c] of r.entrances) {
    const f = floor.features[key(x, y)];
    if (!f) continue;
    if (c === "L") f.locked = true;
    if (c === "S") { grid[y][x] = 1; f.found = false; delete f.open; }
  }

  // trim the dead ends, most of them (a corridor that ends at a secret door isn't one: the door is the point of it)
  const leadsOn = (x, y) => grid[y][x] === 0 || (floor.features[key(x, y)] || {}).type === "secret";
  const deadEnds = () => {
    const out = [];
    for (let y = 1; y < size - 1; y++) for (let x = 1; x < size - 1; x++) {
      if (grid[y][x] === 0 && !templateWall.has(key(x, y)) && CM.DIRS.filter(([dx, dy]) => leadsOn(x + dx, y + dy)).length === 1) out.push([x, y]);
    }
    return out;
  };
  const keepEnds = special === "maze" ? 9999 : 3 + Math.floor(size / 6);
  for (let pass = 0; pass < 40; pass++) {
    const ends = deadEnds();
    if (ends.length <= keepEnds) break;
    rnd.shuffle(ends);
    for (const [x, y] of ends.slice(0, Math.max(1, ends.length - keepEnds))) {
      if (floor.features[key(x, y)]) continue;
      grid[y][x] = 1;
    }
  }
  // (a secret door with nothing on one side any more is just a wall now)
  for (const [k, f] of Object.entries(floor.features)) {
    if (f.type === "secret") {
      const [x, y] = unkey(k);
      if (CM.DIRS.filter(([dx, dy]) => grid[y + dy][x + dx] === 0).length < 2) delete floor.features[k];
    }
  }
  // every set piece can be walked to (through its door, or its secret door): a sealed one gets a plain doorway
  for (const r of rooms) if (r.template) {
    const walk = CM.distances(grid, [r.x0, r.y0], (x, y) => x >= 0 && y >= 0 && x < size && y < size && leadsOn(x, y));
    if (walk.size > (r.x1 - r.x0 + 1) * (r.y1 - r.y0 + 1) + 4) continue;
    for (const [x, y] of r.entrances) {
      const outside = CM.DIRS.map(([dx, dy]) => [x + dx, y + dy]).find(([ox, oy]) => grid[oy] && grid[oy][ox] === 0 && !(ox >= r.x0 && ox <= r.x1 && oy >= r.y0 && oy <= r.y1));
      if (!outside) continue;
      grid[y][x] = 0;
      floor.features[key(x, y)] = { type: "door", open: false, locked: false };
      break;
    }
  }

  // where the party arrives and where the ladder goes
  const plain = rooms.filter((r) => !r.template);
  const inTemplate = (x, y) => rooms.some((r) => r.template && x >= r.x0 - 1 && x <= r.x1 + 1 && y >= r.y0 - 1 && y <= r.y1 + 1);
  const startRoom = plain.length ? plain.reduce((a, b) => (a.x0 + a.y0 <= b.x0 + b.y0 ? a : b)) : null;
  let start = startRoom ? [Math.floor((startRoom.x0 + startRoom.x1) / 2), Math.floor((startRoom.y0 + startRoom.y1) / 2)] : null;
  if (!start) {                                                   // (no plain room at all: the corridor square nearest the top left)
    for (let y = 1; y < size - 1; y++) for (let x = 1; x < size - 1; x++) if (grid[y][x] === 0 && !inTemplate(x, y) && (!start || x + y < start[0] + start[1])) start = [x, y];
    start = start || [1, 1];
  }
  if (grid[start[1]][start[0]] !== 0) { grid[start[1]][start[0]] = 0; }
  floor.pos = start.slice();
  const dist = CM.distances(grid, start);
  let far = start, best = -1;
  for (const [k, d] of dist) {
    const [x, y] = unkey(k);
    if (d > best && !inTemplate(x, y) && !floor.features[k]) { best = d; far = [x, y]; }
  }
  if (!lair) floor.things[key(far[0], far[1])] = number === CM.LAST_FLOOR ? { type: "boss", group: [CM.bossMonster()] } : { type: "ladder" };
  if (number > 1) floor.things[key(start[0], start[1])] = { type: "stairs_up" };
  const open = CM.openNeighbours(floor, start[0], start[1]);
  floor.facing = open.length ? CM.DIRS.indexOf(open[0]) : 2;

  // what the set pieces hold (a chest may be trapped, from the second floor down)
  const trap = () => (number >= 2 && rnd.chance(0.3) ? rnd.pick(Object.keys(CM.TRAPS)) : null);
  const stillGroups = [];
  for (const r of rooms) if (r.template) for (const [x, y, c] of r.fill) {
    const k = key(x, y);
    if (c === "C") floor.things[k] = { type: "chest", gold: rnd.int(15, 40) * number, items: [CM.makeItem(number, rnd), CM.makeItem(number, rnd)], trap: trap() };
    else if (c === "M") { const g = CM.monsterGroup(number, rnd); stillGroups.push(k); floor.things[k] = { type: "monsters", group: g, still: true }; }
    else if (c === "F") floor.features[k] = { type: "fountain", kind: rnd.pick(["heal", "heal", "mana", "poison"]), used: false, known: false };
    else if (c === "A") floor.features[k] = { type: "altar", used: false };
    else if (c === "P") floor.features[k] = { type: "pit" };
    else if (c === "K") floor.things[k] = { type: "key" };
    else if (c === "X") floor.dark.push(k);
    else if (c === "B" && guardian) floor.things[k] = { type: "guardian", group: CM.guardianGroup(guardian, number, rnd) };
    else if ("ntve".includes(c)) floor.decor.push({ x, y, kind: { n: "nest", t: "throne", v: "anvil", e: "ember" }[c] });
  }
  for (const r of rooms) if (r.template && r.template.flood) {                     // a flooded set piece: water on every floor of it
    for (let y = r.y0; y <= r.y1; y++) for (let x = r.x0; x <= r.x1; x++) if (grid[y][x] === 0) floor.decor.push({ x, y, kind: "water" });
  }
  for (const r of rooms) if (r.template) r.template.rows.forEach((row, ry) => [...row].forEach((c, rx) => {
    if (c !== "W") return;
    const x = r.x0 - 1 + rx, y = r.y0 - 1 + ry;
    const inside = CM.DIRS.map(([dx, dy], d) => [x + dx, y + dy, d]).find(([ix, iy]) => ix >= r.x0 && ix <= r.x1 && iy >= r.y0 && iy <= r.y1);
    if (inside && !floor.features[key(inside[0], inside[1])]) {
      floor.features[key(inside[0], inside[1])] = { type: "carving", face: (inside[2] + 2) % 4, text: r.template.lore || -(1 + rnd.int(0, CM.LORE_EXTRA.length - 1)), read: false };
    }
  }));

  // doors on the ordinary rooms' doorways
  const roomCells = new Set();
  for (const r of plain) for (let y = r.y0; y <= r.y1; y++) for (let x = r.x0; x <= r.x1; x++) roomCells.add(key(x, y));
  for (const [x, y] of doorways) {
    const k = key(x, y);
    if (floor.features[k] || !CM.DIRS.some(([dx, dy]) => roomCells.has(key(x + dx, y + dy)))) continue;
    const ns = grid[y - 1][x] === 0 && grid[y + 1][x] === 0 && grid[y][x - 1] === 1 && grid[y][x + 1] === 1;
    const ew = grid[y][x - 1] === 0 && grid[y][x + 1] === 0 && grid[y - 1][x] === 1 && grid[y + 1][x] === 1;
    if (!(ns || ew) || !rnd.chance(0.55)) continue;
    floor.features[k] = { type: "door", open: false, locked: number >= 2 && rnd.chance(0.12) };
  }

  // the furniture, each piece checked: the floor must still be finishable
  const place = (k, feature) => {
    floor.features[k] = feature;
    if (CM.solvable(floor)) return true;
    delete floor.features[k];
    return false;
  };
  const freeCells = (filter) => {
    const out = [];
    for (let y = 1; y < size - 1; y++) for (let x = 1; x < size - 1; x++) {
      const k = key(x, y);
      if (grid[y][x] !== 0 || floor.features[k] || floor.things[k] || (x === start[0] && y === start[1]) || inTemplate(x, y)) continue;
      if ((dist.get(k) || 0) < 2 || Math.abs(x - start[0]) + Math.abs(y - start[1]) < 2) continue;
      if (!filter || filter(x, y, k)) out.push([x, y]);
    }
    return rnd.shuffle(out);
  };
  const corridor = (x, y, k) => !roomCells.has(k);
  const wallFace = (x, y) => { const d = CM.DIRS.findIndex(([dx, dy]) => grid[y + dy][x + dx] === 1); return d; };
  const bottom = number === CM.LAST_FLOOR;                        // (nothing to fall into below the last floor)
  if (number >= 2 && !bottom) for (const [x, y] of freeCells((x, y, k) => roomCells.has(k)).slice(0, rnd.int(0, 1 + Math.floor(number / 7)))) place(key(x, y), { type: "pit" });
  if (number >= 3 && !bottom) for (const [x, y] of freeCells(corridor).slice(0, rnd.int(0, 2))) place(key(x, y), { type: "trapdoor", known: false });
  if (number >= 3 && rnd.chance(0.7)) {
    const ends = freeCells((x, y) => CM.openNeighbours(floor, x, y).length === 1);
    if (ends.length >= 2) {
      const [a, b] = ends;
      floor.features[key(a[0], a[1])] = { type: "teleporter", to: b, known: false };
      floor.features[key(b[0], b[1])] = { type: "teleporter", to: a, known: false };
    }
  }
  if (number >= 2 && rnd.chance(0.6)) { const c = freeCells((x, y) => CM.openNeighbours(floor, x, y).length >= 3)[0]; if (c) place(key(c[0], c[1]), { type: "spinner", known: false }); }
  if (number >= 2 && rnd.chance(0.5)) {
    const darkRoom = rnd.pick(plain.filter((r) => r !== startRoom));
    if (darkRoom) for (let y = darkRoom.y0 - 1; y <= darkRoom.y1 + 1; y++) for (let x = darkRoom.x0 - 1; x <= darkRoom.x1 + 1; x++) {
      if (grid[y][x] === 0 && !(x === start[0] && y === start[1]) && !floor.dark.includes(key(x, y))) floor.dark.push(key(x, y));
    }
  }
  if (rnd.chance(0.6)) { const c = freeCells((x, y, k) => roomCells.has(k))[0]; if (c) place(key(c[0], c[1]), { type: "fountain", kind: rnd.pick(["heal", "heal", "mana", "poison"]), used: false, known: false }); }
  if (number >= 2 && rnd.chance(0.35)) { const c = freeCells((x, y, k) => roomCells.has(k))[0]; if (c) place(key(c[0], c[1]), { type: "altar", used: false }); }
  // a gate on a doorway, its lever somewhere you can get to first
  const gated = Object.entries(floor.features).filter(([, f]) => f.type === "gate");
  if (number >= 4 && rnd.chance(0.4)) {
    const door = Object.entries(floor.features).find(([, f]) => f.type === "door" && !f.locked);
    if (door) { floor.features[door[0]] = { type: "gate", open: false }; gated.push([door[0], floor.features[door[0]]]); }
  }
  for (const [gk] of gated) {
    const reach = CM.reachable(floor);
    const spots = freeCells((x, y, k) => reach.has(k) && wallFace(x, y) >= 0);
    const spot = spots[0];
    if (!spot) { floor.features[gk].open = true; continue; }
    const plate = number >= 4 && CM.hashSeed(`${seed}:plate:${number}:${gk}`) % 5 < 2;
    floor.features[key(spot[0], spot[1])] = plate ? { type: "plate", gate: gk, pressed: false } : { type: "lever", face: wallFace(spot[0], spot[1]), gate: gk, pulled: false };
    if (!CM.solvable(floor)) { delete floor.features[key(spot[0], spot[1])]; floor.features[gk].open = true; }
  }
  // the carving for this floor, on a wall the party can stand before
  const carve_at = freeCells((x, y) => wallFace(x, y) >= 0)[0];
  if (carve_at) floor.features[key(carve_at[0], carve_at[1])] = { type: "carving", face: wallFace(carve_at[0], carve_at[1]), text: number - 1, read: false };
  // keys: one for every locked door, somewhere before it
  for (const [dk, f] of Object.entries(floor.features)) {
    if (f.type !== "door" || !f.locked) continue;
    const reach = CM.reachable(floor);
    const spots = freeCells((x, y, k) => reach.has(k) && !roomCells.has(k) || (reach.has(k) && rnd.chance(0.3)));
    const spot = spots[0];
    if (spot) floor.things[key(spot[0], spot[1])] = { type: "key" };
    else f.locked = false;
  }
  // chests and monsters
  const spare = freeCells((x, y, k) => (dist.get(k) || 0) > 3);
  for (let i = 0; i < 3 + Math.floor(number / 4) && spare.length; i++) {
    const [x, y] = spare.pop();
    const items = [];
    const n = rnd.int(1, 2);
    for (let j = 0; j < n; j++) items.push(CM.makeItem(number, rnd));
    floor.things[key(x, y)] = { type: "chest", gold: rnd.int(10, 30) * number, items, trap: trap() };
  }
  for (let i = 0; i < (special === "maze" ? 3 : 5 + Math.floor(number / 2)) && spare.length; i++) {
    const [x, y] = spare.pop();
    floor.things[key(x, y)] = { type: "monsters", group: CM.monsterGroup(number, rnd) };
  }
  if (special === "maze" && spare.length) {                      // the thing in the labyrinth: a great minotaur that hunts the party wherever it goes
    const [x, y] = spare.pop(), m = CM.makeMonster(CM.monsterKind("Minotaur"), number + 3, rnd);
    Object.assign(m, { name: "Minotaur of the Labyrinth", elite: "hulking", max: Math.round(m.max * 1.5), atk: m.atk + 3, xp: m.xp * 3, gold: m.gold * 4 });
    m.hp = m.max;
    floor.things[key(x, y)] = { type: "monsters", group: [m], hunter: true };
  }
  if (!CM.solvable(floor)) {                                     // (it never comes to this, but a floor must be finishable)
    for (const [k, f] of Object.entries(floor.features)) if (["pit", "trapdoor", "gate"].includes(f.type) || (f.type === "door" && f.locked)) delete floor.features[k];
  }
  if (number === CM.LAST_FLOOR - 1) {                             // the Lich King's heart, somewhere the party can get to
    const reach = CM.reachable(floor), goal = CM.goalOf(floor);
    const spots = freeCells((x, y, k) => reach.has(k) && k !== goal).sort((a, b) => (dist.get(key(b[0], b[1])) || 0) - (dist.get(key(a[0], a[1])) || 0));
    const spot = spots[0];
    if (spot) floor.things[key(spot[0], spot[1])] = { type: "phylactery" };
  }
  // a door that asks a riddle from the carvings above (never a locked one, never a set piece's)
  if (number >= CM.RIDDLE_FROM) {
    const asks = CM.RIDDLES.map((r, i) => i).filter((i) => CM.RIDDLES[i].lore + 1 < number);
    const doors = Object.entries(floor.features).filter(([k, f]) => f.type === "door" && !f.locked && !inTemplate(...unkey(k)));
    const pick = doors.filter(([k]) => CM.hashSeed(`${seed}:riddle:${number}:${k}`) % 10 < 3)[0];
    if (pick && asks.length) pick[1].riddle = asks[CM.hashSeed(`${seed}:riddle:${number}`) % asks.length];
  }
  // plates in the floor that spring a trap, from the third floor down
  if (number >= 3) for (const [x, y] of freeCells(corridor).slice(0, rnd.int(0, 2))) floor.features[key(x, y)] = { type: "plate", trap: rnd.pick(Object.keys(CM.TRAPS)), known: false, spent: false };
  // the people: a ghost with a request, a hermit, a lost adventurer - one of them on a floor, now and then
  if (number >= 2 && number < CM.LAST_FLOOR && !CM.guardianFor(number) && special !== "maze") {
    const roll = rnd.next(), room = (x, y, k) => roomCells.has(k);
    if (roll < 0.22) {
      const spot = freeCells(room)[0];
      if (spot) {
        const who = rnd.int(0, CM.GHOSTS.length - 1), gk = key(spot[0], spot[1]);
        const groups = Object.entries(floor.things).filter(([, t]) => t.type === "monsters" && !t.still && !t.hunter);
        let request = rnd.pick(["bones", "vengeance", "story"]);
        if (request === "vengeance" && !groups.length) request = "story";
        floor.things[gk] = { type: "ghost", who, request, asked: false };
        if (request === "bones") {
          const far = freeCells((x, y, k) => Math.abs(x - spot[0]) + Math.abs(y - spot[1]) >= 6)[0] || freeCells()[0];
          if (far) floor.things[key(far[0], far[1])] = { type: "bones", ghost: gk };
          else floor.things[gk].request = "story";
        } else if (request === "vengeance") {
          const [, t] = rnd.pick(groups);
          t.vengeance = gk;
          const m = t.group[0];
          if (!m.elite) { m.name = `Hulking ${m.name}`; m.elite = "hulking"; m.max = Math.round(m.max * 1.5); m.hp = m.max; m.atk += 2; m.xp = Math.round(m.xp * 1.5); m.gold *= 2; }
        }
      }
    } else if (roll < 0.36 && number >= 3) {
      const spot = freeCells((x, y) => CM.openNeighbours(floor, x, y).length === 1)[0] || freeCells(room)[0];
      if (spot) floor.things[key(spot[0], spot[1])] = { type: "hermit", heard: 0, greeted: false };
    } else if (roll < 0.5 && number >= 3) {
      const spot = freeCells(room)[0];
      if (spot) floor.things[key(spot[0], spot[1])] = { type: "adventurer", hero: CM.makeRecruit(Math.max(1, Math.floor(number / 2)), rnd), freed: false };
    }
  }
  if (special === "wading") for (let y = 1; y < size - 1; y++) for (let x = 1; x < size - 1; x++) if (grid[y][x] === 0) floor.decor.push({ x, y, kind: "water" });
  if (special === "dark") for (let y = 1; y < size - 1; y++) for (let x = 1; x < size - 1; x++) if (grid[y][x] === 0 && !floor.dark.includes(key(x, y))) floor.dark.push(key(x, y));
  floor.rooms = rooms.map((r) => ({ x0: r.x0, y0: r.y0, x1: r.x1, y1: r.y1, name: r.template ? r.template.name : "" }));
  return floor;
};
