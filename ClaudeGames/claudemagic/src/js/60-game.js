"use strict";
// The game itself, with no screen in it: the party, the floors they've walked (kept, so they can climb back), the
// light they carry, the fight they're in, the camp, the bag, saving as it goes, the Hall of Fame. The window
// (70-ui.js) listens to its events and draws; the tests drive it straight.
const keyOf = CM.keyOf = (x, y) => `${x},${y}`;

// a floor saved by an older version of the game gets the parts it didn't have
CM.upgradeFloor = function (fl) {
  fl.features = fl.features || {};
  fl.dark = fl.dark || [];
  fl.rooms = fl.rooms || [];
  fl.seen = fl.seen || [];
  fl.decor = fl.decor || [];
  fl.special = fl.special || null;
  return fl;
};

// The class holds what every part of the game needs: the constructor, the events, saving and loading, and the
// stairs between floors. The rest of the rules are added to its prototype by the files after this one:
// 61-explore.js (moving, looking, using), 62-combat.js (the fight), 63-camp.js (the bag, the merchant, the camp)
// and 64-meta.js (the dungeon's people, growth, the Hall of Fame, achievements, the slots).
CM.Game = class {
  constructor() {
    this.listeners = {};
    this.mode = "title";                 // title, explore, combat, camp
    this.titleNote = "";
    this.messages = [];
    this.party = []; this.bag = []; this.gold = 0; this.floor = null; this.foes = []; this.foeKey = null;
    this.floors = {};                    // every floor walked this run, by number: climb back and it's as you left it
    this.light = { kind: "torch", left: CM.TORCH_STEPS };
    this.seed = "";
    this.stock = null; this.shopping = false;
    this.rnd = new CM.Random(Math.floor(Math.random() * 4294967296));   // (a run's dice come from its seed: see newGame)
    this.bases = {};                     // each floor walked, as it was fresh from the seed (CM.snapshot): the save keeps only what changed
    this.deltas = {};                    // the changes to the floors the party isn't on, as last saved
    this.saveWarned = false;
    this.fame = CM.store.get("fame", []);
    this.trophies = CM.store.get("trophies", {});     // the guardians slain, ever: {id: {date, name, seed}}
    this.vaults = (CM.store.get("vaults", null) || (CM.store.get("vault", null) ? [CM.store.get("vault", null)] : [])).map((it) => CM.normalizeItem(it, "vault"));
    this.compendium = CM.store.get("compendium", {});     // every base ever found: {baseId: {floor, date}}   // the heirlooms left at the camp for the next party (one slot, or three, or five, by the guildhall)
    this.village = Object.assign({ renown: 0, spent: 0, levels: {}, trainers: [] }, CM.store.get("village", {}));   // the surface: renown and the buildings
    this.settings = Object.assign({ sound: true, volume: 0.6, music: true, musicVolume: 0.5, smooth: true, fps: false, look: "pixel", tapMove: true, skipWalk: false, detail: "medium" }, CM.store.get("settings", {}));
    this.settings.keys = Object.assign({}, CM.DEFAULT_KEYS, this.settings.keys || {});
    this.settings.pad = Object.assign({}, CM.DEFAULT_PAD, this.settings.pad || {});
    this.ledger = CM.store.get("ledger", []);        // every expedition that ended, one line each (the statistics; the Hall of Fame keeps ten)
    if (!CM.LOOKS[this.settings.look]) this.settings.look = "pixel";
    this.tally = this.freshTally();      // what this run has come to: steps, kills, chests, fights, fled
    this.slot = [1, 2, 3].includes(CM.store.get("slot", 1)) ? CM.store.get("slot", 1) : 1;
    this.runs = [1, 2, 3].map((n) => CM.migrateRun(CM.store.get(this.runKey(n), null)));   // three expeditions may wait, one in each slot
    this.achievements = CM.store.get("achievements", {});   // earned ever: {id: {date, seed, name}}
    this.difficulty = "fair"; this.mutators = []; this.everFell = false; this.fightFell = false; this.earned = [];
    this.crowned = false; this.bottom = false;       // the Lich King slain this run; the bottom of the world reached
    this.endless = false; this.deepened = [];        // an Endless expedition: the shaft has no bottom; the floors where the dark deepened
    this.fameEndless = CM.store.get("fameEndless", []);   // the Endless board: how deep, ever
    this.bestiary = CM.store.get("bestiary", {});         // every kind met and slain, and what it fears: kept between runs
    this.memorial = CM.store.get("memorial", []);         // the heroes laid to rest, ever: {name, cls, level, floor, seed, date}
    this.fallen = CM.store.get("fallen", []);             // where parties fell, by seed: a later run on that seed finds their remains
    CM.activeRumours = (this.village.rumours || []).filter((r) => r.seed);   // (what the chronicler promised, for CM.furnish)
    CM.legends = this.fame.filter((e) => e.won);
    CM.namedWeapons = (this.compendium.named || []).slice();            // (a named weapon of an earlier party may be found again: CM.furnish)
    if (!this.ledger.length && (this.fame.length || this.fameEndless.length)) {   // (the runs that ended before the ledger was kept: read back from the boards)
      this.ledger = this.fame.concat(this.fameEndless).map(CM.ledgerFromFame);
      CM.store.set("ledger", this.ledger);
    }
    this.combos = CM.store.get("combos", {});             // the combos found, ever
    this.weaves = CM.store.get("weaves", {});             // the weaves found, ever
    this.dirty = false; this.sinceSave = 0; this.wander = 0;
  }

  // ---- events: change (redraw), message, mode, floor, moved, turned, fx, sound, near, mesh, teleported, fell, spin, lore, over, talk, riddle, journal ----
  // fx kinds: hit, miss, die, hurt, ailment, swing, attack, cast, cold, trap, summon, rise, shatter, sparkle, levelup, potion,
  //   grasp (the Drowned Knight's), slam (the Forge-Warden's hammer), sear (its heat), relic (a guardian's, taken)
  on(event, fn) { (this.listeners[event] = this.listeners[event] || []).push(fn); return this; }
  emit(event, ...args) { for (const fn of this.listeners[event] || []) fn(...args); }

  say(text) {
    this.messages.push(text);
    if (this.messages.length > 60) this.messages = this.messages.slice(-60);
    this.emit("message", text);
    this.emit("change");
  }

  sound(name) { this.emit("sound", name); }

  freshTally() { return { steps: 0, kills: 0, chests: 0, fights: 0, fled: 0, guardians: [] }; }
  // things gained: tagged with where, noted in the compendium, counted, and into the pack
  gain(items, how) {
    const list = (Array.isArray(items) ? items : [items]).filter(Boolean), floor = this.floor ? this.floor.number : 0;
    if (list.some((it) => it.kind === "scroll" && it.spell === "lostpage") && this.shelvePage) this.shelvePage();   // (the library shelves a copy of every lost page found)
    CM.tagFound(list, floor, how);
    this.tally.found = this.tally.found || {};
    for (const it of list) {
      const r = it.unknown ? "unknown" : CM.rarityOf(it);
      this.tally.found[r] = (this.tally.found[r] || 0) + 1;
      const id = CM.baseIdOf(it);
      if (CM.BASES[id] && !this.compendium[id] && !it.unknown) { this.compendium[id] = { floor, date: CM.today() }; CM.store.set("compendium", this.compendium); if (Object.keys(this.compendium).filter((k) => CM.BASES[k]).length >= Object.keys(CM.BASES).length) this.achieve("collector"); }
    }
    this.bag.push(...list);
    return list;
  }
  noteKnown(item) {                                                      // an unknown thing, named: the compendium learns it
    const id = CM.baseIdOf(item);
    if (CM.BASES[id] && !this.compendium[id]) { this.compendium[id] = { floor: this.floor ? this.floor.number : 0, date: CM.today() }; CM.store.set("compendium", this.compendium); }
  }
  countUse(kind) { this.tally.used = this.tally.used || {}; this.tally.used[kind] = (this.tally.used[kind] || 0) + 1; }
  // ---- the belt: four things from the pack, to hand; in a fight the first used in a round is free ----
  toBelt(row, slot) {
    this.belt = this.belt || [];
    const item = this.bag[row];
    if (!item) return "Pick something from the pack first.";
    if (!CM.BELT_KINDS.includes(item.kind)) return "The belt takes things to drink, read, light or throw.";
    slot = slot === undefined ? this.belt.findIndex((x) => !x) : slot;
    if (slot < 0) slot = this.belt.length < CM.BELT_SIZE ? this.belt.length : -1;
    if (slot < 0 || slot >= CM.BELT_SIZE) return "The belt is full: take something off it first.";
    this.logAct("toBelt", row, slot);
    this.bag.splice(row, 1);
    if (this.belt[slot]) this.bag.push(this.belt[slot]);
    this.belt[slot] = item;
    this.emit("change");
    return "";
  }
  fromBelt(slot) {
    const item = (this.belt || [])[slot];
    if (!item) return "Nothing there.";
    this.logAct("fromBelt", slot);
    this.belt[slot] = null;
    this.bag.push(item);
    this.emit("change");
    return "";
  }
  // a belt slot used: out of a fight, as the pack's give; in one, through act("item", {belt, who})
  useBelt(slot, who) {
    const item = (this.belt || [])[slot];
    if (!item) return "Nothing on the belt there.";
    if (this.mode === "combat") { const ok = this.act("item", { belt: slot, who: who === undefined ? this.party.indexOf(this.alive()[0]) : who }); return ok ? "" : "Not now."; }
    if (this.mode !== "explore" && this.mode !== "camp") return "Not now.";
    this.logAct("useBelt", slot, who === undefined ? null : who);
    this.bag.push(item); this.belt[slot] = null;
    const row = this.bag.length - 1, hero = who === undefined ? this.alive()[0] : this.party[who];
    const note = this.give(row, this.party.indexOf(hero));
    if (this.bag[row] === item) { this.bag.splice(row, 1); this.belt[slot] = item; }   // (not used after all: back on the belt)
    this.emit("change");
    return note;
  }
  count(what, n = 1) { if (!this.tally) this.tally = this.freshTally(); this.tally[what] = (this.tally[what] || 0) + n; }

  setMode(mode) { if (mode !== "explore") this.travel = null; if (mode === "camp" && this.followerAtCamp) this.followerAtCamp(); this.mode = mode; this.emit("mode", mode); this.emit("change"); }

  // ---- the log: every choice the player makes, as a line, so a run can be played again from its seed (CM.replayRun) ----
  logAct(name, ...args) { if (this.replaying) return; this.runLog = this.runLog || []; this.runLog.push(args.length ? [name, ...args] : [name]); }
  replaySpec() { return { seed: this.seed, gen: this.gen || 1, party: this.startParty || null, kit: this.kit || "pauper", difficulty: this.difficulty || "fair", mutators: this.startMutators || this.mutators || [], mode: this.dream ? "otherdream" : this.awakened ? "awakened" : this.endless ? "endless" : "dungeon", ascension: this.ascension || 0, iron: Boolean(this.iron), town: Boolean(this.startedInTown), trail: (this.trail || []).slice(), log: (this.runLog || []).slice() }; }

  // ---- the film: a run watched in the real view, line by line, on this very game (nothing is saved while it plays) ----
  startFilm(spec) {
    if (!spec || !Array.isArray(spec.log)) return false;
    this.film = { spec, at: 0, playing: true, speed: 1, last: 0 };
    this.replaying = 1;
    const gen = CM.GEN, maxWas = CM.store.get("ascension", 0);
    if ((spec.ascension || 0) > (maxWas || 0)) CM.store.set("ascension", spec.ascension);
    const bottomWas = this.achievements.bottom;
    if (spec.mode === "awakened" && !bottomWas) this.achievements.bottom = { date: "film" };
    if (spec.mode === "otherdream" && !this.achievements.dreamer) this.achievements.dreamer = { date: "film" };
    CM.GEN = spec.gen || 1;
    try { this.newGame(spec.seed, spec.party || null, spec.kit, spec.difficulty, spec.mutators, spec.mode, { ascension: spec.ascension || 0, iron: spec.iron, town: Boolean(spec.town) }); }   // (a film of a run that began at home begins at home)
    finally { CM.GEN = gen; CM.store.set("ascension", maxWas || 0); if (!bottomWas) delete this.achievements.bottom; }
    this.gen = spec.gen || 1;
    this.replaying = 0;                                                  // (the film's lines log nothing: filmStep says so itself)
    this.say(`A film: ${spec.party ? spec.party.map((p) => p.name).join(", ") : "a party"} on ${spec.seed}, ${spec.log.length} moves. Esc stops it.`);
    this.emit("film", true);
    return true;
  }
  filmStep() {
    const f = this.film;
    if (!f || f.at >= f.spec.log.length || this.mode === "title") { if (f) { f.playing = false; if (f.at >= f.spec.log.length) this.say("The film ends here."); } return false; }
    this.replaying = 1;
    try { CM.replayStep(this, f.spec.log[f.at++]); } finally { this.replaying = 0; }
    return true;
  }
  // on to the next fight, or the next floor, without the walk between
  filmSkip(what) {
    const f = this.film;
    if (!f) return;
    const floor = this.floor ? this.floor.number : 0, fights = this.tally.fights || 0;
    let guard = 0;
    while (this.filmStep() && guard++ < 20000) { if (what === "fight" && (this.tally.fights || 0) > fights) break; if (what === "floor" && this.floor && this.floor.number !== floor) break; }
    this.emit("change");
  }
  stopFilm() {
    if (!this.film) return;
    this.film = null; this.replaying = 0;
    this.combat = null; this.foes = [];
    this.runs = [1, 2, 3].map((n) => CM.migrateRun(CM.store.get(this.runKey(n), null)));   // (the player's own runs, as they were)
    this.setMode("title");
    this.emit("film", false);
  }
  // down the stairs by hand (the simulator's bot, when it has lost its way): logged, so a replay follows
  warp(number) { this.logAct("warp", number); this.enterFloor(number, "down"); }
  mapAll() {                                                             // (the tests' other cheat, logged like warp: the whole floor seen, so travelTo has a map)
    this.logAct("mapAll");
    const fl = this.floor; if (!fl) return;
    fl.seen = []; for (let y = 0; y < fl.grid.length; y++) for (let x = 0; x < fl.grid.length; x++) fl.seen.push([x, y]);
  }
  // the party's temper: a number from 0 to 100, said as a word (CM.moraleWord); what the fight reads
  cheer(n, why) {
    const was = this.morale === undefined ? CM.MORALE.start : this.morale;
    this.morale = CM.clamp(was + n, 0, 100);
    const w1 = CM.moraleWord(was), w2 = CM.moraleWord(this.morale);
    if (w1 !== w2) this.say(`The party is ${w2.toLowerCase()}${why ? ` (${why})` : ""}.`);
    this.dirty = true;
  }
  moraleWord() { return CM.moraleWord(this.morale === undefined ? CM.MORALE.start : this.morale); }
  hungerWord() { return (this.fed || 0) >= CM.HUNGER.weary ? "Weary" : (this.fed || 0) >= CM.HUNGER.hungry ? "Hungry" : ""; }
  // what a tally counts besides steps and kills: gold by where it went, and how often each spell or skill was used
  spend(where, gold) { this.tally.spent = this.tally.spent || {}; this.tally.spent[where] = (this.tally.spent[where] || 0) + gold; }

  saveSettings() { CM.store.set("settings", this.settings); }

  // ---- saving ----
  // the three callings earned: by an achievement, or a guardian's trophy
  classUnlocked(cls) {
    const u = CM.CLASS_UNLOCK[cls];
    if (!u) return true;
    return Boolean((u.achievement && this.achievements[u.achievement]) || (u.trophy && this.trophies[u.trophy]));
  }
  classesAvailable() { return CM.ALL_CLASSES.filter((c) => this.classUnlocked(c)); }

  // a hero laid to rest for good is written down, between runs (the title's memorial)
  remember2(hero) {
    this.memorial = this.memorial || [];
    const buried = [hero.weapon, hero.armor].filter((it) => it && !(it.props && it.props.fists)).sort((a, b) => (b.value || 0) - (a.value || 0))[0] || null;
    const floor = this.floor ? this.floor.number : 0;
    this.memorial.unshift({ name: hero.name, cls: hero.cls, level: hero.level, origin: hero.origin || null, floor, seed: this.seed, date: CM.today(), buried, last: CM.lastWords(hero, floor), epitaph: "", scars: (hero.scars || []).slice() });
    this.memorial = this.memorial.slice(0, this.villageLevel("shrine") >= 3 ? 60 : 30);
    CM.store.set("memorial", this.memorial);
  }

  // a trace: something the party left on this floor (a bottle, remains, a scorch, a stub), saved with the floor, at
  // most CM.TRACES_MOST of them; the floor's mesh is made again to show it
  trace(id, x, y) {
    const fl = this.floor;
    if (!fl || !CM.PROPS[id] || this.mode === "camp" || x === undefined) return;
    fl.tracesMade = (fl.tracesMade || 0) + 1;
    const rnd = new CM.Random(CM.hashSeed(`${this.seed}:trace:${fl.number}:${fl.tracesMade}`));
    const r2 = (v) => Math.round(v * 100) / 100 + 0;                      // (two places, and never a -0 that a save would turn to 0)
    fl.traces = (fl.traces || []).concat({ id, x, y, dx: r2((rnd.next() - 0.5) * 0.5), dz: r2((rnd.next() - 0.5) * 0.5), turn: r2(rnd.next() * 3.14), s: r2(rnd.next()) });
    if (fl.traces.length > CM.TRACES_MOST) fl.traces = fl.traces.slice(-CM.TRACES_MOST);
    this.emit("mesh");
  }
  bottleFor(kind) { return kind === "mana" ? "bottle_blue" : kind === "heal" || kind === "greaterheal" ? "bottle_red" : "bottle_green"; }

  // a floor made from the seed, and remembered as it was fresh (so the save can keep only what changes)
  freshFloor(number) {
    const fl = CM.makeFloor(number, this.seed, this.gen || CM.GEN);
    if (this.awakened) CM.mirrorFloor(fl);
    this.bases[number] = CM.snapshot(fl);
    this.floors[number] = fl;
    return fl;
  }

  // the floor by that number: as the party left it (made again from the save's changes the first time it's wanted), or new
  floorAt(number) {
    if (this.floors[number]) return this.floors[number];
    const delta = this.deltas[number];
    if (!delta) return this.freshFloor(number);
    const r = CM.restoreFloor(delta, this.seed, this.gen || 1, this.awakened);
    this.floors[number] = r.floor; this.bases[number] = r.base;
    if (r.drifted) this.say(`(The dungeon has shifted a little since this run was saved: floor ${number} may not be quite as you left it.)`);
    return r.floor;
  }

  // the party is leaving this floor: what changed on it is worked out afresh at the next save
  leaveFloor() { if (this.floor) delete this.deltas[this.floor.number]; }

  // every floor walked, as what changed: the one the party is on is diffed now, the others as they were left
  floorDeltas() {
    const out = {};
    for (const [n, fl] of Object.entries(this.floors)) {
      const base = this.bases[n] || (this.bases[n] = CM.snapshot(this.awakened ? CM.mirrorFloor(CM.makeFloor(Number(n), this.seed, this.gen || 1)) : CM.makeFloor(Number(n), this.seed, this.gen || 1)));
      if (fl === this.floor || !this.deltas[n]) this.deltas[n] = CM.floorDelta(fl, base);
      out[n] = this.deltas[n];
    }
    for (const n of Object.keys(this.deltas)) if (!out[n]) out[n] = this.deltas[n];   // (floors not walked since the run was loaded: as saved)
    return out;
  }

  saveRun() {
    if (this.replaying || this.film) return;                             // (a film plays on the live game; nothing of it is kept)
    if (!["explore", "camp"].includes(this.mode)) return;
    if (this.iron && this.mode !== "camp" && !this.ironAllow) { this.dirty = false; this.sinceSave = 0; return; }   // (Iron: the camps only)
    const data = { schema: CM.SCHEMA, gen: this.gen || 1, version: CM.version, party: this.party, bag: this.bag, gold: this.gold, floor: this.floor.number, floors: this.floorDeltas(), light: this.light,
      spellLight: this.spellLight || 0, phylactery: Boolean(this.phylactery), reminded: Boolean(this.reminded), belt: this.belt || [], buffs: this.buffs || {}, lanternHeld: Boolean(this.lanternHeld), meal: this.meal || null, alchemistFree: Boolean(this.alchemistFree), kit: this.kit || "pauper", mode: this.mode, seed: this.seed, rng: this.rnd.s,
      tally: this.tally || this.freshTally(), journal: this.journal || [], story: this.story || { read: {} }, rescued: this.rescued || [], saved: new Date().toISOString(),
      difficulty: this.difficulty || "fair", mutators: this.mutators || [], everFell: Boolean(this.everFell), earned: this.earned || [], crowned: Boolean(this.crowned), endless: Boolean(this.endless), deepened: this.deepened || [],
      camps: this.camps || [], pairFights: this.pairFights || {}, bonds: this.bonds || [], hazardsMet: this.hazardsMet || [], remainsFound: this.remainsFound || [],
      startParty: this.startParty || null, startMutators: this.startMutators || [], log: CM.packLog(this.runLog || []), formation: this.formation || "line", ascension: this.ascension || 0, iron: Boolean(this.iron), awakened: Boolean(this.awakened), dream: Boolean(this.dream), rootPending: Boolean(this.rootPending), behind: this.behind || 0, startedInTown: Boolean(this.startedInTown), clock: this.clock || 0, fellFrom: this.fellFrom || null, orders: this.orders || [], bounty: this.bounty || null, blessedUntil: this.blessedUntil || 0, rumourBox: this.rumourBox || 0, season: this.season || null, farmDay: this.farmDay || 0, festival: this.festival || null,
      morale: this.morale === undefined ? CM.MORALE.start : this.morale, fed: this.fed || 0, trail: this.trail || [], lightOut: Boolean(this.lightOut), noiseLevel: this.noiseLevel || 0, follower: this.follower || null, tavernBarred: Boolean(this.tavernBarred), tower: this.tower || null, fort: this.fort || null };
    this.lastRun = data;
    const ok = CM.store.set(this.runKey(this.slot), data);
    if (!ok && !this.saveWarned) {                                       // (the browser's keeping is full, or forbidden: say so once, loudly)
      this.saveWarned = true;
      this.say("The browser would not keep the save: its storage is full or shut. The run goes on, but it will not be here next time - Export it from the title, and clear an old slot.");
      this.emit("saveFailed");
    }
    if (ok) this.saveWarned = false;
    this.dirty = false; this.sinceSave = 0;
  }

  canContinue() { return Boolean(this.lastRun && CM.runFloor(this.lastRun) !== null && this.lastRun.party); }   // (floor 0 is the town: a run)

  continueRun() {
    const d = CM.migrateRun(this.lastRun);
    if (!this.canContinue()) return false;
    this.seed = d.seed || CM.randomSeed();
    this.gen = d.gen || 1;                                               // (the generator this run began with: its floors stay its floors)
    this.awakened = Boolean(d.awakened);
    this.party = d.party.map(CM.upgradeHero); this.bag = d.bag || []; this.gold = d.gold || 0;
    this.floors = {}; this.bases = {}; this.deltas = {};
    for (const delta of Object.values(d.floors || {})) this.deltas[delta.n] = delta;   // (each floor is made again when the party goes back to it)
    this.floor = this.floorAt(d.floor);
    this.rnd = new CM.Random(typeof d.rng === "number" ? d.rng : CM.hashSeed(`${this.seed}:dice`));
    this.light = d.light || { kind: "torch", left: CM.TORCH_STEPS };
    this.spellLight = d.spellLight || 0;
    this.lightOut = Boolean(d.lightOut); this.noiseLevel = d.noiseLevel || 0;   // (the eleventh update's light and noise)
    this.follower = d.follower || null; this.tavernBarred = Boolean(d.tavernBarred); this.tower = d.tower || null; this.towerRun = null; this.caveRun = null; this.fort = d.fort || null; this.fortRun = null; this.abloWorld = null; this.brosRun = null;   // (the Mage Tower: how far climbed)   // (a follower, and a tavern that won't hire after one died)
    this.phylactery = Boolean(d.phylactery); this.reminded = Boolean(d.reminded);
    this.belt = Array.isArray(d.belt) ? d.belt.slice(0, CM.BELT_SIZE) : []; this.buffs = d.buffs || {}; this.lanternHeld = Boolean(d.lanternHeld); this.meal = d.meal || null; this.alchemistFree = Boolean(d.alchemistFree);
    if (this.light && this.light.kind === "lantern" && !this.light.left) this.light.left = CM.LANTERN_OIL;   // (a lantern from before v4.4: a flask of oil in it)
    this.combat = null;
    this.recruits = null;
    this.identifying = false;
    this.kit = d.kit || "pauper";
    this.tally = Object.assign(this.freshTally(), d.tally || {});
    this.steps = this.tally.steps || 0;
    this.journal = d.journal || [];
    this.story = d.story || CM.storyFromJournal(this.journal);          // (a save from before the codex: what was read is in the journal)
    this.rescued = d.rescued || [];
    this.difficulty = CM.DIFFICULTIES[d.difficulty] ? d.difficulty : "fair";
    this.mutators = d.mutators || CM.mutatorsFor(d.seed || "");
    this.everFell = Boolean(d.everFell); this.fightFell = false; this.earned = d.earned || [];
    this.crowned = Boolean(d.crowned); this.bottom = false; this.endless = Boolean(d.endless); this.deepened = d.deepened || [];
    this.camps = d.camps || []; this.travel = null;
    this.pairFights = d.pairFights || {}; this.bonds = d.bonds || []; this.hazardsMet = d.hazardsMet || []; this.remainsFound = d.remainsFound || [];
    this.startParty = d.startParty || null; this.startMutators = d.startMutators || []; this.runLog = CM.unpackLog(d.log || []);
    this.formation = CM.FORMATIONS[d.formation] ? d.formation : "line";
    this.ascension = d.ascension || 0; this.iron = Boolean(d.iron); this.ironAllow = false;
    this.awakened = Boolean(d.awakened); this.dream = Boolean(d.dream); this.rootPending = Boolean(d.rootPending); this.behind = d.behind || 0; this.startedInTown = Boolean(d.startedInTown); this.clock = d.clock || 0; this.fellFrom = d.fellFrom || null; this.orders = d.orders || []; this.bounty = d.bounty || null; this.blessedUntil = d.blessedUntil || 0; this.rumourBox = d.rumourBox || 0; this.season = d.season || CM.seasonOfDate(); this.farmDay = d.farmDay || 0; this.festival = d.festival || null;
    this.morale = d.morale === undefined ? CM.MORALE.start : d.morale; this.fed = d.fed || 0; this.trail = d.trail || [];
    this.applyBonds();
    this.messages = [];
    this.setMode(d.mode === "camp" ? "camp" : "explore");
    if (this.rootPending) { this.rootPending = false; this.rootChoice(); }   // (the party stood over the beaten Root when the window closed: the choice again)
    this.emit("floor", this.floor);
    this.say("You take up the expedition where you left it.");
    return true;
  }

  // ---- starting, and the stairs between floors ----
  // the best earlier run on this seed that left a trail (its floors and the step each was reached): a ghost to race
  ghostTrail() {
    if (this.film) return null;
    const runs = this.fame.concat(this.fameEndless || []).filter((e) => e.seed === this.seed && Array.isArray(e.trail) && e.trail.length > 1).sort((a, b) => b.floor - a.floor);
    return runs.length ? runs[0].trail : null;
  }
  // the rung of the ladder this run is on: at k, every rule to k applies (CM.ASCENSION)
  asc(k) { const rung = typeof k === "string" ? CM.ASCENSION.findIndex((r) => r.id === k) + 1 : k; return rung > 0 && (this.ascension || 0) >= rung; }
  ascensionMax() { return CM.clamp(CM.store.get("ascension", 0) || 0, 0, CM.ASCENSION.length); }

  newGame(seed, chosen, kit, difficulty, mutators, mode, opts) {         // chosen: the party made on the creation screen (or none: the classic four); kit: what's been earned; mode: "endless" for no bottom; opts: {ascension, iron}
    this.seed = (seed || "").trim() || CM.randomSeed();
    this.rnd = new CM.Random(CM.hashSeed(`${this.seed}:dice`));          // the run's dice: the same seed, the same fights, given the same choices
    this.gen = CM.GEN;
    this.bases = {}; this.deltas = {}; this.saveWarned = false;
    this.party = CM.newParty(chosen);
    this.steps = 0;
    this.kit = CM.unlocked(this.allFame).includes(kit) ? kit : "pauper";
    this.recruits = null;
    this.identifying = false;
    this.bag = CM.tagFound(CM.startingBag(this.seed), 1, "start");
    this.gold = 30;
    this.floors = {};
    this.light = { kind: "torch", left: CM.TORCH_STEPS };
    this.spellLight = 0; this.lightOut = false; this.noiseLevel = 0; this.follower = null; this.tavernBarred = false; this.tower = null; this.towerRun = null; this.caveRun = null; this.fort = null; this.fortRun = null; this.abloWorld = null; this.brosRun = null;
    this.phylactery = false;
    this.combat = null;
    this.messages = [];
    this.titleNote = "";
    this.tally = this.freshTally();
    this.journal = []; this.story = { read: {} }; this.reminded = false; this.left = false; this.dreamed = false; this.rootPending = false;
    this.belt = []; this.buffs = {}; this.lanternHeld = false; this.meal = null; this.alchemistFree = false;
    this.bindRumours();
    this.rescued = [];
    this.difficulty = CM.DIFFICULTIES[difficulty] ? difficulty : "fair";
    this.mutators = Array.isArray(mutators) ? mutators.filter((m) => CM.MUTATORS[m]) : CM.mutatorsFor(this.seed);
    this.everFell = false; this.fightFell = false; this.earned = [];
    this.crowned = false; this.bottom = false; this.endless = mode === "endless"; this.deepened = [];
    this.awakened = mode === "awakened" && Boolean(this.achievements.bottom); this.behind = 0;
    this.dream = mode === "otherdream" && Boolean(this.achievements.dreamer);   // the Other Dream: the same floors, re-read
    this.morale = CM.MORALE.start; this.fed = 0; this.trail = [];
    this.camps = []; this.travel = null; this.pairFights = {}; this.bonds = []; this.hazardsMet = []; this.remainsFound = [];
    this.startParty = this.party.map((h) => ({ cls: h.cls, name: h.name, stats: Object.assign({}, h.stats), row: h.row, quirk: h.quirk || null, origin: h.origin || null }));
    this.startMutators = this.mutators.slice(); this.runLog = []; this.formation = "line";
    this.ascension = CM.clamp(Number((opts || {}).ascension) || 0, 0, Math.min(CM.ASCENSION.length, this.ascensionMax())); this.iron = Boolean((opts || {}).iron);
    this.ironAllow = true;                                               // (the first save of an Iron run, at the top of the stair)
    if (this.has("lean")) { this.bag = this.bag.filter((i) => !["heal", "mana", "revive"].includes(i.kind)); this.gold += 100; }
    if (this.kit === "veteran") { this.gold += 60; this.bag.push(CM.lantern()); }
    else if (this.kit === "delver") this.bag.push(CM.scroll("mapping"), CM.scroll("mapping"), CM.torch(), CM.torch(), CM.torch(), CM.antidote(), CM.antidote());
    else if (this.kit === "heir") for (const h of this.party) { h.weapon.power += 2; h.weapon.name += " +1"; h.weapon.props = Object.assign({}, h.weapon.props, { bonus: 1 }); h.weapon.value = 45; }
    else if (this.kit === "legend") for (const h of this.party) { h.level = 2; h.pending = 1; CM.recompute(h); h.hp = h.max; h.mp = h.maxmp; }
    if (this.party.some((h) => h.cls === "Artificer")) this.bag.push(CM.trapKit());   // (the Artificer's trade: a trap kit from the start)
    { const will = this.villageLevel("home") >= 5 && this.village.home && this.village.home.will; if (will) { const it = JSON.parse(JSON.stringify(will)); it.willed = true; this.bag.push(it); } }   // (the study's will)
    if (this.kit === "scholar") { for (const k of CM.LORE_KEYS.slice(0, 5)) this.markRead(k); const ids = Object.keys(CM.TOMES); this.bag.push(CM.tome(ids[CM.hashSeed(`${this.seed}:scholar`) % ids.length])); }
    else if (this.kit === "abyss") { this.gold += 150; this.bag.push(CM.rope(), CM.gem("diamond"), CM.scroll("mapping")); for (const h of this.party) { h.level = 3; h.pending = 1; CM.recompute(h); h.hp = h.max; h.mp = h.maxmp; } }
    for (const h of this.party) { const t = this.trainerFor(h.cls); if (t && CM.BOONS[t.boon] && !CM.BOONS[t.boon].stat && !(h.boons || []).includes(t.boon)) { h.boons = (h.boons || []).concat(t.boon); CM.recompute(h); h.hp = h.max; } else if (t && CM.BOONS[t.boon] && CM.BOONS[t.boon].stat) { h.stats[CM.BOONS[t.boon].stat] = Math.min(25, h.stats[CM.BOONS[t.boon].stat] + 2); CM.recompute(h); h.hp = h.max; h.mp = h.maxmp; } }   // (the guildhall's trainers)
    this.retiredThisRun = false; this.clock = 0;                          // (dawn, six in the morning)
    this.season = CM.SEASONS.includes(this.settings.season) ? this.settings.season : CM.seasonOfDate(); this.farmDay = 0;   // (the season, pinned to the run from the real date or Settings; the farm's last dawn seen)
    this.festival = this.settings.festival && CM.FESTIVALS[this.settings.festival] ? this.settings.festival : CM.festivalOfDate();   // (the festival, if the run begins in its week)
    const town = (opts || {}).town !== undefined ? Boolean((opts || {}).town) : !this.settings.skipWalk;   // (a run begins at the party's door, or at the shaft: Settings)
    this.startedInTown = town;
    this.enterFloor(town ? 0 : 1, "down");                                // (the town's own start is the party's door, facing down the lane)
    for (const h of this.party) {                                        // the origins' touches at the stair, and a trainer's word to their pupil
      if (h.origin === "east") this.gold += 20;
      if (h.origin === "caerduin") this.markRead("carving.catacombs.1");
      const t = this.trainerFor(h.cls); if (t && CM.TRAINER_LINES[h.cls]) this.say(`${t.name}, who taught ${h.name}: ${CM.TRAINER_LINES[h.cls]}`);
    }
    this.ironAllow = false;
    this.say((town ? CM.t("town.open") : "Four adventurers climb down into the dark. Somewhere below, the Lich King stirs.") + (this.kit !== "pauper" ? ` (${CM.KITS[this.kit].name}.)` : "")
      + (this.difficulty !== "fair" ? ` ${CM.DIFFICULTIES[this.difficulty].name}: ${CM.DIFFICULTIES[this.difficulty].what}.` : "")
      + (this.endless ? " An Endless expedition: this shaft has no bottom, and below the fiftieth floor the dark deepens every ten." : "")
      + (this.ascension ? ` Ascension ${this.ascension}: ${CM.ASCENSION.slice(0, this.ascension).map((r) => r.name).join(", ")}.` : "") + (this.iron ? " Iron: the run is saved only at the camps." : "")
      + (this.awakened ? " Awakened: the Root remembers you. Every floor is the mirror of itself, the monsters a band deeper, the uniques awake." : "")
      + (this.dream ? " The Other Dream: the Root dreams otherwise. The floors are the floors; the walls are not; the monsters are the Awakened ones." : ""));
    if (this.mutators.length) this.say(`Today's dungeon: ${this.mutators.map((m) => `${CM.MUTATORS[m].name} - ${CM.MUTATORS[m].what}`).join("; ")}.`);
  }

  cellOf(fl, type) {
    const k = Object.keys(fl.things).find((c) => fl.things[c].type === type);
    return k ? k.split(",").map(Number) : null;
  }

  // how: "down" (by the stairs, arriving at the top), "up" (arriving at the ladder), "fall" (through the floor at `at`)
  enterFloor(number, how = "down", at = null) {
    if (!CM.isDeep(number)) this.lightOut = false;                       // (above ground: nothing to creep past)
    const fresh = !this.floors[number] && !this.deltas[number];
    const fl = this.floorAt(number);
    if (fl !== this.floor) { this.leaveFloor(); this.stock = null; this.recruits = null; if (this.floor && number % 1 === 0 && this.floor.number % 1 === 0) this.clock = (this.clock || 0) + CM.CLOCK.stair * Math.max(1, Math.abs(number - this.floor.number)); if (this.farmDawns && this.village) this.farmDawns(); }   // (a merchant's table and a tavern's bench belong to where they are; a stair is an hour)
    this.floor = fl;
    if (this.songEpic !== number) { this.song = 0; this.songEpic = 0; }  // (a song that lasts the floor ends with it)
    if (how === "down") {
      const top = this.cellOf(fl, "stairs_up") || this.cellOf(fl, "wingstair_up");
      if (top) fl.pos = top.slice();
      else if (!fresh) fl.pos = fl.pos.slice();
      const open = CM.openNeighbours(fl, fl.pos[0], fl.pos[1]);
      if (open.length) fl.facing = CM.DIRS.indexOf(open[0]);
    } else if (how === "upwing") {                                        // back up a wing stair: onto it
      const stair = this.cellOf(fl, "wingstair") || this.cellOf(fl, "stairs_up");
      if (stair) fl.pos = stair.slice();
      const open = CM.openNeighbours(fl, fl.pos[0], fl.pos[1]);
      if (open.length) fl.facing = CM.DIRS.indexOf(open[0]);
    } else if (how === "up") {
      const ladder = this.cellOf(fl, "ladder") || this.cellOf(fl, "boss") || this.cellOf(fl, "guardian");
      if (ladder) fl.pos = ladder.slice();
      const open = CM.openNeighbours(fl, fl.pos[0], fl.pos[1]);
      if (open.length) fl.facing = CM.DIRS.indexOf(open[0]);
    } else if (how === "rope" && at) {
      fl.pos = at.slice();
      const open = CM.openNeighbours(fl, fl.pos[0], fl.pos[1]);
      if (open.length) fl.facing = CM.DIRS.indexOf(open[0]);
    } else if (how === "fall" && at) {
      let best = null, bd = 1e9;
      for (let y = 0; y < fl.grid.length; y++) for (let x = 0; x < fl.grid.length; x++) {
        const k = keyOf(x, y), f = fl.features[k], t = fl.things[k];
        if (!CM.passable(fl, x, y) || (f && ["pit", "trapdoor", "teleporter"].includes(f.type)) || (t && t.type !== "key")) continue;
        const d = Math.abs(x - at[0]) + Math.abs(y - at[1]);
        if (d < bd) { bd = d; best = [x, y]; }
      }
      if (best) fl.pos = best;
    }
    if (fresh && number % 1 === 0) {
      this.trail = (this.trail || []).concat([[number, this.tally.steps || 0]]);
      if (number >= 1 && number <= CM.GAZETTEER_FLOORS && this.villageLevel("library") >= 5) {   // the gazetteer: the walls, not the things
        for (let y = 0; y < fl.grid.length; y++) for (let x = 0; x < fl.grid.length; x++) if (!fl.seen.some(([sx, sy]) => sx === x && sy === y)) fl.seen.push([x, y]);
        if (number === 1) this.say("The library's gazetteer: the first floors are mapped before you are on them. What stands in the rooms is another matter.");
      }
      const ghost = this.ghostTrail(), g = ghost && ghost.find(([n]) => n === number);
      if (g && number > 1) { const d = (this.tally.steps || 0) - g[1]; this.say(`The ghost of your best run on this seed took this stair at step ${g[1].toLocaleString()}: you are ${d > 0 ? `${d} steps behind` : d < 0 ? `${-d} steps ahead` : "level with it"}.`); }
    }
    if (number === -1) this.refreshWood();
    if (this.followerOnFloor) this.followerOnFloor(number, fresh);       // (the follower: 64b-people.js)
    if (this.layErrand && number >= 1) this.layErrand(fl);              // (an errand's thing, on its floor)
    if (this.layUndercroftBack) this.layUndercroftBack(fl);             // (the flooded stair down to the bell-yard, once its door is open)
    if (fresh) this.layRemains(fl);
    this.showHeart(fl);
    if (fresh && (fl.special === "wading" || fl.tide)) this.banter("water");
    if (number === 0 && CM.festivalIs(this, "harvest") && !fl.things[CM.TOWN_AT.market.join(",")]) fl.things[CM.TOWN_AT.market.join(",")] = { type: "peddler", stock: null };   // (the Harvest Fair: market day all week)
    if (fresh) {                                                         // the trinkets that mark the map: the carving, the way down, the gathering
      const mark = (k) => { const [x, y] = k.split(",").map(Number); if (!fl.seen.some(([sx, sy]) => sx === x && sy === y)) fl.seen.push([x, y]); };
      if (CM.partyProp(this.party, "chalk")) for (const [k, f] of Object.entries(fl.features)) if (f.type === "carving") mark(k);
      if (CM.partyProp(this.party, "lodestone")) { const goal = CM.goalOf(fl); if (goal) mark(goal); }
      if (CM.partyProp(this.party, "dowsing")) for (const [k, t] of Object.entries(fl.things)) if (t.type === "node") mark(k);
      if (this.rumourBox === number) { for (const [k, t] of Object.entries(fl.things)) if (t.type === "strongbox") { mark(k); this.say("The fence's rumour was good: the strongbox is marked on the map."); } this.rumourBox = 0; }
    }
    if (fresh && this.meal && this.meal.floor < number) { this.meal = null; this.say("The meal has worn off."); for (const h of this.party) { h.mealLuck = 0; h.mealStat = null; CM.recompute(h); } }
    if (fresh && this.staleDishes) this.staleDishes();
    if (fresh && this.buffs) { for (const k of ["stoneskin", "night", "sharpen", "salve", "rested"]) if (this.buffs[k] !== undefined && this.buffs[k] < number) delete this.buffs[k]; if (this.buffs.owleyes) { this.buffs.owleyes -= 1; if (this.buffs.owleyes <= 0) { delete this.buffs.owleyes; this.say("The owl's eyes close: the dark is the dark again."); } } }
    if (fresh) for (const h of this.alive()) if (CM.equipped(h).some((it) => it.props && it.props.cursed && it.props.curse === "haunted")) this.afflict(h, "curse", "the haunted thing");
    if (fresh) { const toad = this.alive().find((h) => h.familiar === "toad"); if (toad) { const sick = this.alive().find((h) => Object.keys(h.status || {}).some((s) => s !== "stone")); if (sick) { const s = Object.keys(sick.status).find((x) => x !== "stone"); delete sick.status[s]; this.say(`${toad.name}'s toad swallows ${sick.name}'s ${CM.STATUSES[s].name.toLowerCase()} whole.`); } } }
    for (const h of this.alive()) if (h.cls === "Necromancer" && !h.familiar && h.level >= CM.FAMILIAR_AT) { h.familiar = "skull"; this.say(`A skull on ${h.name}'s belt opens its jaws: ${CM.FAMILIARS.skull.what}.`); }
    if (fresh && this.has("pilgrim") && number > 0) { const xp = 60 * number; for (const h of this.alive()) h.xp += xp; this.say(`Pilgrim: ${xp} experience each, for the floor itself.`); }
    this.setMode("explore");
    this.look();
    this.emit("floor", fl);
    this.saveRun();
    if (fresh && this.has("pilgrim")) this.checkLevels();
    if (fl.wing !== undefined) { if (fresh) this.say(`${fl.wingName.charAt(0).toUpperCase() + fl.wingName.slice(1)}: ${CM.WINGS[fl.wing].smell}. The only way on is the way down to the main stair.`); if (fresh && fl.secretWing) this.achieve("secretfloor"); else if (fresh) this.achieve("wings"); }
    else if (fresh || how !== "fall") this.say(number === 0 ? CM.t("town.arrive", { name: CM.TOWN_THEME.name }) : number === -1 ? `${CM.WOOD_THEME.name}: ${CM.hourWord(CM.hourOf(this))} under the trees.` : CM.isUndercroft(number) ? `${CM.UNDERCROFT_NAMES[-number - 2].charAt(0).toUpperCase() + CM.UNDERCROFT_NAMES[-number - 2].slice(1)}: standing water, and old streets under the hill.` : number < 0 ? "A cave under the Wood: roots in the roof, and the first bands' kinds in the dark." : `Floor ${number}, ${CM.bandName(this, number)}.` + (number === CM.LAST_FLOOR ? (this.dream ? "  A smell of bread rises from somewhere ahead." : "  A terrible cold rises from somewhere ahead...") : ""));
    if (fresh && fl.special && CM.SPECIALS[fl.special]) this.say(CM.SPECIALS[fl.special].note);
    if (fresh && fl.hazard && CM.HAZARDS[CM.themeIndex(number)] && !this.hazardsSeen(fl.hazard)) this.say(CM.HAZARDS[CM.themeIndex(number)].note);
    if (fresh && number === CM.LAST_FLOOR + 1) this.say("The stair goes on below the palace, cut by no mason. The air is wet and old. The Deep begins here, and the carvings above never spoke of it.");
    if (fresh && this.endless && number === CM.BOTTOM + 1) this.say("Below the Root, the stair goes on. It should not. The stone is the catacombs' stone again, and the dark is the same dark, and it does not end.");
    if (fresh && this.endless && number > CM.BOTTOM + 10 && number % 10 === 1) this.deepen(number);     // (61, 71, 81 ...)
  }

  climbUp() {
    this.logAct("climbUp");
    const n = this.floor.number;
    if (n === 1) { this.say("The way out. Not without the Lich King's crown."); return; }
    this.sound("stairs");
    if (this.campBelow(n - 1)) {                          // the camp is between this floor and the one above
      const above = this.floorAt(n - 1);
      this.leaveFloor();
      this.floor = above;
      const ladder = this.cellOf(above, "ladder");
      if (ladder) above.pos = ladder.slice();
      this.setMode("camp");
      this.reachCamp(n - 1);
      this.emit("floor", above);
      this.saveRun();
      this.say("Up the long shaft, the merchant's lantern glows again.");
      return;
    }
    this.enterFloor(n - 1, "up");
    this.say("You climb back up.");
  }


  // ---- ways to play: the slot, the difficulty and the day's mutators as they bite, achievements ----
  get lastRun() { return (this.runs || [])[this.slot - 1] || null; }
  set lastRun(v) { this.runs = this.runs || [null, null, null]; this.runs[this.slot - 1] = v; }
  runKey(n) { return n === 1 ? "run" : `run${n}`; }
  setSlot(n) {
    if (![1, 2, 3].includes(n)) return false;
    this.slot = n;
    CM.store.set("slot", n);
    this.emit("change");
    return true;
  }


  // ---- Endless: no bottom - the bands come round again, the guardians echo, and the dark deepens ----
  get allFame() { return this.fame.concat(this.fameEndless || []); }   // (both boards: what has been reached, ever, unlocks the kits)
  campBelow(n) { return CM.CAMP_AFTER.includes(n) || Boolean(this.endless && n >= CM.BOTTOM && n % 5 === 0); }
};
