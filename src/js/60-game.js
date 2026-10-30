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
    this.vault = CM.store.get("vault", null);         // the one heirloom a party left at the camp for the next
    this.settings = Object.assign({ sound: true, volume: 0.6, music: true, musicVolume: 0.5, smooth: true, fps: false, look: "drawn", tapMove: true }, CM.store.get("settings", {}));
    this.settings.keys = Object.assign({}, CM.DEFAULT_KEYS, this.settings.keys || {});
    if (!CM.LOOKS[this.settings.look]) this.settings.look = "drawn";
    this.tally = this.freshTally();      // what this run has come to: steps, kills, chests, fights, fled
    this.slot = [1, 2, 3].includes(CM.store.get("slot", 1)) ? CM.store.get("slot", 1) : 1;
    this.runs = [1, 2, 3].map((n) => CM.migrateRun(CM.store.get(this.runKey(n), null)));   // three expeditions may wait, one in each slot
    this.achievements = CM.store.get("achievements", {});   // earned ever: {id: {date, seed, name}}
    this.difficulty = "fair"; this.mutators = []; this.everFell = false; this.fightFell = false; this.earned = [];
    this.crowned = false; this.bottom = false;       // the Lich King slain this run; the bottom of the world reached
    this.endless = false; this.deepened = [];        // an Endless expedition: the shaft has no bottom; the floors where the dark deepened
    this.fameEndless = CM.store.get("fameEndless", []);   // the Endless board: how deep, ever
    this.bestiary = CM.store.get("bestiary", {});         // every kind met and slain, and what it fears: kept between runs
    this.combos = CM.store.get("combos", {});             // the combos found, ever
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
  count(what, n = 1) { if (!this.tally) this.tally = this.freshTally(); this.tally[what] = (this.tally[what] || 0) + n; }

  setMode(mode) { if (mode !== "explore") this.travel = null; this.mode = mode; this.emit("mode", mode); this.emit("change"); }

  saveSettings() { CM.store.set("settings", this.settings); }

  // ---- saving ----
  // a floor made from the seed, and remembered as it was fresh (so the save can keep only what changes)
  freshFloor(number) {
    const fl = CM.makeFloor(number, this.seed);
    this.bases[number] = CM.snapshot(fl);
    this.floors[number] = fl;
    return fl;
  }

  // the floor by that number: as the party left it (made again from the save's changes the first time it's wanted), or new
  floorAt(number) {
    if (this.floors[number]) return this.floors[number];
    const delta = this.deltas[number];
    if (!delta) return this.freshFloor(number);
    const r = CM.restoreFloor(delta, this.seed);
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
      const base = this.bases[n] || (this.bases[n] = CM.snapshot(CM.makeFloor(Number(n), this.seed)));
      if (fl === this.floor || !this.deltas[n]) this.deltas[n] = CM.floorDelta(fl, base);
      out[n] = this.deltas[n];
    }
    for (const n of Object.keys(this.deltas)) if (!out[n]) out[n] = this.deltas[n];   // (floors not walked since the run was loaded: as saved)
    return out;
  }

  saveRun() {
    if (!["explore", "camp"].includes(this.mode)) return;
    const data = { schema: CM.SCHEMA, gen: CM.GEN, version: CM.version, party: this.party, bag: this.bag, gold: this.gold, floor: this.floor.number, floors: this.floorDeltas(), light: this.light,
      spellLight: this.spellLight || 0, phylactery: Boolean(this.phylactery), kit: this.kit || "pauper", mode: this.mode, seed: this.seed, rng: this.rnd.s,
      tally: this.tally || this.freshTally(), journal: this.journal || [], rescued: this.rescued || [], saved: new Date().toISOString(),
      difficulty: this.difficulty || "fair", mutators: this.mutators || [], everFell: Boolean(this.everFell), earned: this.earned || [], crowned: Boolean(this.crowned), endless: Boolean(this.endless), deepened: this.deepened || [],
      camps: this.camps || [] };
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

  canContinue() { return Boolean(this.lastRun && CM.runFloor(this.lastRun) && this.lastRun.party); }

  continueRun() {
    const d = CM.migrateRun(this.lastRun);
    if (!this.canContinue()) return false;
    this.seed = d.seed || CM.randomSeed();
    this.party = d.party.map(CM.upgradeHero); this.bag = d.bag || []; this.gold = d.gold || 0;
    this.floors = {}; this.bases = {}; this.deltas = {};
    for (const delta of Object.values(d.floors || {})) this.deltas[delta.n] = delta;   // (each floor is made again when the party goes back to it)
    this.floor = this.floorAt(d.floor);
    this.rnd = new CM.Random(typeof d.rng === "number" ? d.rng : CM.hashSeed(`${this.seed}:dice`));
    this.light = d.light || { kind: "torch", left: CM.TORCH_STEPS };
    this.spellLight = d.spellLight || 0;
    this.phylactery = Boolean(d.phylactery);
    this.combat = null;
    this.recruits = null;
    this.identifying = false;
    this.kit = d.kit || "pauper";
    this.tally = Object.assign(this.freshTally(), d.tally || {});
    this.steps = this.tally.steps || 0;
    this.journal = d.journal || [];
    this.rescued = d.rescued || [];
    this.difficulty = CM.DIFFICULTIES[d.difficulty] ? d.difficulty : "fair";
    this.mutators = d.mutators || CM.mutatorsFor(d.seed || "");
    this.everFell = Boolean(d.everFell); this.fightFell = false; this.earned = d.earned || [];
    this.crowned = Boolean(d.crowned); this.bottom = false; this.endless = Boolean(d.endless); this.deepened = d.deepened || [];
    this.camps = d.camps || []; this.travel = null;
    this.messages = [];
    this.setMode(d.mode === "camp" ? "camp" : "explore");
    this.emit("floor", this.floor);
    this.say("You take up the expedition where you left it.");
    return true;
  }

  // ---- starting, and the stairs between floors ----
  newGame(seed, chosen, kit, difficulty, mutators, mode) {               // chosen: the party made on the creation screen (or none: the classic four); kit: what's been earned; mode: "endless" for no bottom
    this.seed = (seed || "").trim() || CM.randomSeed();
    this.rnd = new CM.Random(CM.hashSeed(`${this.seed}:dice`));          // the run's dice: the same seed, the same fights, given the same choices
    this.bases = {}; this.deltas = {}; this.saveWarned = false;
    this.party = CM.newParty(chosen);
    this.steps = 0;
    this.kit = CM.unlocked(this.allFame).includes(kit) ? kit : "pauper";
    this.recruits = null;
    this.identifying = false;
    this.bag = CM.startingBag(this.seed);
    this.gold = 30;
    this.floors = {};
    this.light = { kind: "torch", left: CM.TORCH_STEPS };
    this.spellLight = 0;
    this.phylactery = false;
    this.combat = null;
    this.messages = [];
    this.titleNote = "";
    this.tally = this.freshTally();
    this.journal = [];
    this.rescued = [];
    this.difficulty = CM.DIFFICULTIES[difficulty] ? difficulty : "fair";
    this.mutators = Array.isArray(mutators) ? mutators.filter((m) => CM.MUTATORS[m]) : CM.mutatorsFor(this.seed);
    this.everFell = false; this.fightFell = false; this.earned = [];
    this.crowned = false; this.bottom = false; this.endless = mode === "endless"; this.deepened = [];
    this.camps = []; this.travel = null;
    if (this.has("lean")) { this.bag = this.bag.filter((i) => !["heal", "mana", "revive"].includes(i.kind)); this.gold += 100; }
    if (this.kit === "veteran") { this.gold += 60; this.bag.push(CM.lantern()); }
    else if (this.kit === "delver") this.bag.push(CM.scroll("mapping"), CM.scroll("mapping"), CM.torch(), CM.torch(), CM.torch(), CM.antidote(), CM.antidote());
    else if (this.kit === "heir") for (const h of this.party) { h.weapon.power += 2; h.weapon.name += " +1"; h.weapon.props = Object.assign({}, h.weapon.props, { bonus: 1 }); h.weapon.value = 45; }
    else if (this.kit === "legend") for (const h of this.party) { h.level = 2; h.pending = 1; CM.recompute(h); h.hp = h.max; h.mp = h.maxmp; }
    else if (this.kit === "abyss") { this.gold += 150; this.bag.push(CM.rope(), CM.gem("diamond"), CM.scroll("mapping")); for (const h of this.party) { h.level = 3; h.pending = 1; CM.recompute(h); h.hp = h.max; h.mp = h.maxmp; } }
    this.enterFloor(1, "down");
    this.say("Four adventurers climb down into the dark. Somewhere below, the Lich King stirs." + (this.kit !== "pauper" ? ` (${CM.KITS[this.kit].name}.)` : "")
      + (this.difficulty !== "fair" ? ` ${CM.DIFFICULTIES[this.difficulty].name}: ${CM.DIFFICULTIES[this.difficulty].what}.` : "")
      + (this.endless ? " An Endless expedition: this shaft has no bottom, and below the fiftieth floor the dark deepens every ten." : ""));
    if (this.mutators.length) this.say(`Today's dungeon: ${this.mutators.map((m) => `${CM.MUTATORS[m].name} - ${CM.MUTATORS[m].what}`).join("; ")}.`);
  }

  cellOf(fl, type) {
    const k = Object.keys(fl.things).find((c) => fl.things[c].type === type);
    return k ? k.split(",").map(Number) : null;
  }

  // how: "down" (by the stairs, arriving at the top), "up" (arriving at the ladder), "fall" (through the floor at `at`)
  enterFloor(number, how = "down", at = null) {
    const fresh = !this.floors[number] && !this.deltas[number];
    const fl = this.floorAt(number);
    if (fl !== this.floor) this.leaveFloor();
    this.floor = fl;
    if (this.songEpic !== number) { this.song = 0; this.songEpic = 0; }  // (a song that lasts the floor ends with it)
    if (how === "down") {
      const top = this.cellOf(fl, "stairs_up");
      if (top) fl.pos = top.slice();
      else if (!fresh) fl.pos = fl.pos.slice();
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
    this.setMode("explore");
    this.look();
    this.emit("floor", fl);
    this.saveRun();
    if (fresh || how !== "fall") this.say(`Floor ${number}, ${CM.themeFor(number).name}.` + (number === CM.LAST_FLOOR ? "  A terrible cold rises from somewhere ahead..." : ""));
    if (fresh && fl.special && CM.SPECIALS[fl.special]) this.say(CM.SPECIALS[fl.special].note);
    if (fresh && fl.hazard && CM.HAZARDS[CM.themeIndex(number)] && !this.hazardsSeen(fl.hazard)) this.say(CM.HAZARDS[CM.themeIndex(number)].note);
    if (fresh && number === CM.LAST_FLOOR + 1) this.say("The stair goes on below the palace, cut by no mason. The air is wet and old. The Deep begins here, and the carvings above never spoke of it.");
    if (fresh && this.endless && number === CM.BOTTOM + 1) this.say("Below the Root, the stair goes on. It should not. The stone is the catacombs' stone again, and the dark is the same dark, and it does not end.");
    if (fresh && this.endless && number > CM.BOTTOM + 10 && number % 10 === 1) this.deepen(number);     // (61, 71, 81 ...)
  }

  climbUp() {
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
