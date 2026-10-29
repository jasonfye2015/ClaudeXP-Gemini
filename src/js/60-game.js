"use strict";
// The game itself, with no screen in it: the party, the floors they've walked (kept, so they can climb back), the
// light they carry, the fight they're in, the camp, the bag, saving as it goes, the Hall of Fame. The window
// (70-ui.js) listens to its events and draws; the tests drive it straight.
const keyOf = (x, y) => `${x},${y}`;

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
    this.rnd = new CM.Random(Math.floor(Math.random() * 4294967296));
    this.fame = CM.store.get("fame", []);
    this.trophies = CM.store.get("trophies", {});     // the guardians slain, ever: {id: {date, name, seed}}
    this.vault = CM.store.get("vault", null);         // the one heirloom a party left at the camp for the next
    this.settings = Object.assign({ sound: true, volume: 0.6, music: true, musicVolume: 0.5, smooth: true, fps: false, look: "drawn", tapMove: true }, CM.store.get("settings", {}));
    this.settings.keys = Object.assign({}, CM.DEFAULT_KEYS, this.settings.keys || {});
    if (!CM.LOOKS[this.settings.look]) this.settings.look = "drawn";
    this.tally = this.freshTally();      // what this run has come to: steps, kills, chests, fights, fled
    this.slot = [1, 2, 3].includes(CM.store.get("slot", 1)) ? CM.store.get("slot", 1) : 1;
    this.runs = [1, 2, 3].map((n) => CM.store.get(this.runKey(n), null));   // three expeditions may wait, one in each slot
    this.achievements = CM.store.get("achievements", {});   // earned ever: {id: {date, seed, name}}
    this.difficulty = "fair"; this.mutators = []; this.everFell = false; this.fightFell = false; this.earned = [];
    this.crowned = false; this.bottom = false;       // the Lich King slain this run; the bottom of the world reached
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

  setMode(mode) { this.mode = mode; this.emit("mode", mode); this.emit("change"); }

  saveSettings() { CM.store.set("settings", this.settings); }

  // ---- saving ----
  saveRun() {
    if (!["explore", "camp"].includes(this.mode)) return;
    const data = { party: this.party, bag: this.bag, gold: this.gold, floor: this.floor, floors: this.floors, light: this.light,
      spellLight: this.spellLight || 0, phylactery: Boolean(this.phylactery), kit: this.kit || "pauper", mode: this.mode, seed: this.seed,
      tally: this.tally || this.freshTally(), journal: this.journal || [], rescued: this.rescued || [], saved: new Date().toISOString(),
      difficulty: this.difficulty || "fair", mutators: this.mutators || [], everFell: Boolean(this.everFell), earned: this.earned || [], crowned: Boolean(this.crowned) };
    this.lastRun = data;
    CM.store.set(this.runKey(this.slot), data);
    this.dirty = false; this.sinceSave = 0;
  }

  canContinue() { return Boolean(this.lastRun && this.lastRun.floor && this.lastRun.party); }

  continueRun() {
    const d = this.lastRun;
    if (!this.canContinue()) return false;
    this.party = d.party.map(CM.upgradeHero); this.bag = d.bag || []; this.gold = d.gold || 0;
    this.floors = d.floors || {};
    for (const fl of Object.values(this.floors)) CM.upgradeFloor(fl);
    this.floor = CM.upgradeFloor(d.floor);
    this.floors[this.floor.number] = this.floor;
    this.light = d.light || { kind: "torch", left: CM.TORCH_STEPS };
    this.spellLight = d.spellLight || 0;
    this.phylactery = Boolean(d.phylactery);
    this.combat = null;
    this.recruits = null;
    this.identifying = false;
    this.kit = d.kit || "pauper";
    this.tally = Object.assign(this.freshTally(), d.tally || {});
    this.journal = d.journal || [];
    this.rescued = d.rescued || [];
    this.difficulty = CM.DIFFICULTIES[d.difficulty] ? d.difficulty : "fair";
    this.mutators = d.mutators || CM.mutatorsFor(d.seed || "");
    this.everFell = Boolean(d.everFell); this.fightFell = false; this.earned = d.earned || [];
    this.crowned = Boolean(d.crowned); this.bottom = false;
    this.seed = d.seed || CM.randomSeed();
    this.messages = [];
    this.setMode(d.mode === "camp" ? "camp" : "explore");
    this.emit("floor", this.floor);
    this.say("You take up the expedition where you left it.");
    return true;
  }

  endRun(won) {
    won = Boolean(won || this.crowned);
    const entry = { name: CM.playerName || "Adventurer", floor: this.floor.number, gold: this.gold, won, bottom: Boolean(this.bottom), date: CM.today(), seed: this.seed,
      daily: String(this.seed).startsWith("daily-"), party: this.party.map((h) => `${h.name} the ${h.cls} ${h.level}`),
      kit: this.kit || "pauper", tally: Object.assign(this.freshTally(), this.tally || {}), difficulty: this.difficulty || "fair", mutators: this.mutators || [] };
    const fl = this.floor.number, steps = (this.tally || {}).steps || 0;
    if (fl >= 5 || won) this.achieve("delver");
    if (fl >= 10 || won) this.achieve("deep");
    if (fl >= 15 || won) this.achieve("deeper");
    if ((fl >= 10 || won) && entry.daily) this.achieve("daily");
    if (fl >= 30) this.achieve("abyss");
    if (this.bottom) this.achieve("bottom");
    if (won) { this.achieve("crown"); if (!this.everFell) this.achieve("ironman"); if (steps < 1500) this.achieve("swift"); if (this.difficulty === "grim") this.achieve("grim"); }
    entry.titles = (this.earned || []).slice();
    this.fame.push(entry);
    if (won) this.trophy("lich");
    this.sortFame();
    CM.store.set("fame", this.fame);
    CM.store.remove(this.runKey(this.slot));
    this.lastRun = null;
    this.sound(won ? "victory" : "death");
    this.titleNote = this.bottom ? "To the bottom of the world and back, with the Lich King's crown. There is no deeper."
      : won && this.floor.number > CM.LAST_FLOOR ? `With the Lich King's crown, the party went down into the Deep, and fell on floor ${this.floor.number}.`
      : won ? "The Lich King is no more. The party returns as legends!"
      : `The party fell on floor ${this.floor.number}. Their story ends here.`;
    this.emit("over", won, entry);
    this.setMode("title");
  }

  sortFame() {
    this.fame.sort((a, b) => (b.bottom ? 1 : 0) - (a.bottom ? 1 : 0) || (b.won ? 1 : 0) - (a.won ? 1 : 0) || b.floor - a.floor || b.gold - a.gold);
    this.fame = this.fame.slice(0, 10);
  }

  // what the old Python game kept on disk (run.json, hall_of_fame.json), brought over once by the Timeline's host
  importOld(data) {
    const took = [];
    if (data && Array.isArray(data.fame) && data.fame.length) {
      const have = new Set(this.fame.map((e) => `${e.name}|${e.floor}|${e.gold}|${e.date}`));
      for (const e of data.fame) if (e && !have.has(`${e.name}|${e.floor}|${e.gold}|${e.date}`)) this.fame.push(e);
      this.sortFame();
      CM.store.set("fame", this.fame);
      took.push("fame");
    }
    if (data && data.run && data.run.floor && data.run.party && !this.canContinue()) {
      this.lastRun = Object.assign({ seed: CM.randomSeed(), mode: "explore" }, data.run);
      CM.store.set(this.runKey(this.slot), this.lastRun);
      took.push("run");
    }
    this.emit("change");
    return took;
  }

  exportText() {
    return JSON.stringify({ game: "Claude and Magic", version: CM.version, run: this.runs[0], runs: this.runs, slot: this.slot, fame: this.fame, settings: this.settings,
      trophies: this.trophies, vault: this.vault, achievements: this.achievements });
  }

  importText(text) {
    let data;
    try { data = JSON.parse(text); } catch (e) { return "That isn't a Claude and Magic save."; }
    if (!data || data.game !== "Claude and Magic") return "That isn't a Claude and Magic save.";
    if (Array.isArray(data.runs)) data.runs.forEach((r, i) => { if (r && r.floor && r.party) { this.runs[i] = r; CM.store.set(this.runKey(i + 1), r); } });
    else if (data.run && data.run.floor && data.run.party) { this.runs[0] = data.run; CM.store.set("run", data.run); }
    if (data.achievements && typeof data.achievements === "object") { this.achievements = Object.assign({}, this.achievements, data.achievements); CM.store.set("achievements", this.achievements); }
    if (Array.isArray(data.fame)) { this.fame = data.fame; this.sortFame(); CM.store.set("fame", this.fame); }
    if (data.settings) { Object.assign(this.settings, data.settings); this.saveSettings(); }
    if (data.trophies && typeof data.trophies === "object") { this.trophies = Object.assign({}, this.trophies, data.trophies); CM.store.set("trophies", this.trophies); }
    if (data.vault && typeof data.vault === "object" && data.vault.name) { this.vault = data.vault; CM.store.set("vault", this.vault); }
    this.emit("change");
    return "";
  }

  // ---- starting, and the stairs between floors ----
  newGame(seed, chosen, kit, difficulty, mutators) {                     // chosen: the party made on the creation screen (or none: the classic four); kit: what's been earned
    this.seed = (seed || "").trim() || CM.randomSeed();
    this.party = CM.newParty(chosen);
    this.steps = 0;
    this.kit = CM.unlocked(this.fame).includes(kit) ? kit : "pauper";
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
    this.crowned = false; this.bottom = false;
    if (this.has("lean")) { this.bag = this.bag.filter((i) => !["heal", "mana", "revive"].includes(i.kind)); this.gold += 100; }
    if (this.kit === "veteran") { this.gold += 60; this.bag.push(CM.lantern()); }
    else if (this.kit === "delver") this.bag.push(CM.scroll("mapping"), CM.scroll("mapping"), CM.torch(), CM.torch(), CM.torch(), CM.antidote(), CM.antidote());
    else if (this.kit === "heir") for (const h of this.party) { h.weapon.power += 2; h.weapon.name += " +1"; h.weapon.props = Object.assign({}, h.weapon.props, { bonus: 1 }); h.weapon.value = 45; }
    else if (this.kit === "legend") for (const h of this.party) { h.level = 2; h.pending = 1; CM.recompute(h); h.hp = h.max; h.mp = h.maxmp; }
    else if (this.kit === "abyss") { this.gold += 150; this.bag.push(CM.rope(), CM.gem("diamond"), CM.scroll("mapping")); for (const h of this.party) { h.level = 3; h.pending = 1; CM.recompute(h); h.hp = h.max; h.mp = h.maxmp; } }
    this.enterFloor(1, "down");
    this.say("Four adventurers climb down into the dark. Somewhere below, the Lich King stirs." + (this.kit !== "pauper" ? ` (${CM.KITS[this.kit].name}.)` : "")
      + (this.difficulty !== "fair" ? ` ${CM.DIFFICULTIES[this.difficulty].name}: ${CM.DIFFICULTIES[this.difficulty].what}.` : ""));
    if (this.mutators.length) this.say(`Today's dungeon: ${this.mutators.map((m) => `${CM.MUTATORS[m].name} - ${CM.MUTATORS[m].what}`).join("; ")}.`);
  }

  cellOf(fl, type) {
    const k = Object.keys(fl.things).find((c) => fl.things[c].type === type);
    return k ? k.split(",").map(Number) : null;
  }

  // how: "down" (by the stairs, arriving at the top), "up" (arriving at the ladder), "fall" (through the floor at `at`)
  enterFloor(number, how = "down", at = null) {
    let fl = this.floors[number];
    const fresh = !fl;
    if (fresh) { fl = CM.makeFloor(number, this.seed); this.floors[number] = fl; }
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
    if (fresh && number === CM.LAST_FLOOR + 1) this.say("The stair goes on below the palace, cut by no mason. The air is wet and old. The Deep begins here, and the carvings above never spoke of it.");
  }

  climbUp() {
    const n = this.floor.number;
    if (n === 1) { this.say("The way out. Not without the Lich King's crown."); return; }
    this.sound("stairs");
    if (CM.CAMP_AFTER.includes(n - 1)) {                  // the camp is between this floor and the one above
      const above = this.floors[n - 1] || (this.floors[n - 1] = CM.makeFloor(n - 1, this.seed));
      this.floor = above;
      const ladder = this.cellOf(above, "ladder");
      if (ladder) above.pos = ladder.slice();
      this.setMode("camp");
      this.emit("floor", above);
      this.saveRun();
      this.say("Up the long shaft, the merchant's lantern glows again.");
      return;
    }
    this.enterFloor(n - 1, "up");
    this.say("You climb back up.");
  }

  // ---- moving ----
  turn(way) {
    if (this.mode !== "explore") return false;
    this.floor.facing = (this.floor.facing + way + 4) % 4;
    this.look();
    this.emit("turned", this.floor.facing);
    this.emit("change");
    return true;
  }

  hasKey() { return this.bag.findIndex((i) => i.kind === "key"); }

  move(rel) {
    if (this.mode !== "explore") return false;
    const fl = this.floor;
    const [dx, dy] = CM.DIRS[(fl.facing + rel) % 4];
    const x = fl.pos[0] + dx, y = fl.pos[1] + dy, k = keyOf(x, y);
    if (!CM.isOpen(fl, x, y)) {
      this.sound("bump");
      this.say("Ouch! A solid wall.");
      return false;
    }
    const f = fl.features[k];
    if (f && f.type === "door" && !f.open) {
      if (f.riddle !== undefined && CM.RIDDLES[f.riddle]) { this.sound("bump"); this.say("Runes crawl across the door, and a question with them."); this.emit("riddle", k); return false; }
      if (f.locked) {
        const i = this.hasKey();
        if (i < 0) {
          const rogue = this.alive().find((h) => h.cls === "Rogue" && h.level >= CM.PICK_LOCK_LEVEL && this.canAct(h));
          if (!rogue) { this.sound("bump"); this.say("The door is locked. It needs a key."); return false; }
          if (!this.rnd.chance(0.5 + CM.mod(this.stat(rogue, "dex")) * 0.1)) {
            this.sound("bump");
            this.say(`${rogue.name} works at the lock... it won't give. Not yet.`);
            return false;
          }
          this.sound("unlock");
          this.say(`${rogue.name} picks the lock, and the door swings open.`);
        } else {
          this.bag.splice(i, 1);
          this.sound("unlock");
          this.say("The key turns, and the door swings open.");
        }
        f.locked = false;
      } else {
        this.say("The door creaks open.");
      }
      f.open = true;
      this.sound("door");
      this.dirty = true;
      this.emit("change");
      return false;
    }
    if (f && f.type === "gate" && !f.open) {
      this.sound("bump");
      this.say("A portcullis bars the way. There must be a lever somewhere.");
      return false;
    }
    const thing = fl.things[k];
    if (thing && (thing.type === "monsters" || thing.type === "boss" || thing.type === "guardian")) {
      this.startCombat(k, thing);
      return false;
    }
    fl.pos = [x, y];
    this.sound("step");
    this.burn();
    this.look();
    this.emit("moved", x, y);
    this.dirty = true;
    this.steps = (this.steps || 0) + 1;
    this.count("steps");
    if (this.steps % 5 === 0) {                                          // poison walks with you
      for (const h of this.alive()) {
        const st = h.status || {};
        if (!st.poison) continue;
        const bite = Math.max(1, Math.floor(h.max * ((h.boons || []).includes("thickblood") ? 0.025 : 0.05)));
        h.hp = Math.max(1, h.hp - bite);
        st.poison--;
        if (st.poison <= 0) { delete st.poison; this.say(`${h.name} is no longer poisoned.`); }
        else this.say(`${h.name} suffers from the poison (-${bite}).`);
      }
    }
    if (thing) {
      if (thing.type === "key") {
        delete fl.things[k];
        this.bag.push(CM.key());
        this.sound("coin");
        this.say("An iron key lies in the dust. You take it.");
      } else if (thing.type === "bones") {
        delete fl.things[k];
        this.bag.push(CM.bones(thing.ghost));
        this.sound("coin");
        this.say("Bones, gnawed and scattered - someone's. You gather them up.");
      } else {
        this.say({ chest: "A chest sits here. (Space to open it)", ladder: "A ladder leads down into the dark. (Space to climb down)",
          stairs_up: "The stairs you came down. (Space to climb back up)",
          phylactery: "A plain box, cold to look at. Something in it beats, slowly. (Space to smash it)",
          ghost: "A pale shape hangs in the air here, waiting. (Space to speak to it)", hermit: "A hermit crouches in a nest of rags. (Space to speak to him)",
          adventurer: "Someone sits bound against the wall. (Space to cut them loose)", rope: "A rope hangs down from the floor above. (Space to climb it)" }[thing.type]);
      }
    }
    if (f) this.arrive(f, k);
    this.emit("change");
    return true;
  }

  // what a square does when the party steps onto it
  arrive(f, k) {
    const fl = this.floor;
    if (f.type === "pit" && f.roped && fl.number < CM.LAST_FLOOR) { this.say("You climb down the rope you left, hand over hand."); this.ropeDown(k); return; }
    if (f.type === "pit" && this.hasItem("rope") >= 0 && fl.number < CM.LAST_FLOOR) {
      this.bag.splice(this.hasItem("rope"), 1);
      f.roped = true;
      this.say("You make the rope fast and lower the party down the pit, slow and safe.");
      this.ropeDown(k);
      return;
    }
    if (f.type === "pit" || f.type === "trapdoor") {
      if (f.type === "trapdoor") { f.known = true; this.say("The floor gives way beneath you!"); }
      else this.say("You step into the pit!");
      this.fall(k.split(",").map(Number));
    } else if (f.type === "teleporter") {
      f.known = true;
      const to = fl.features[keyOf(f.to[0], f.to[1])];
      if (to) to.known = true;
      fl.pos = f.to.slice();
      this.sound("teleport");
      this.look();
      this.emit("teleported", fl.pos[0], fl.pos[1]);
      this.say("The runes flare - and the walls around you are different ones.");
    } else if (f.type === "spinner") {
      f.known = true;
      fl.facing = (fl.facing + this.rnd.int(1, 3)) % 4;
      this.look();
      this.emit("spin", fl.facing);
      this.say("The floor lurches and the world turns. Which way were you facing?");
    } else if (f.type === "plate") {
      if (f.gate) {
        if (!f.pressed) {
          f.pressed = true;
          const gate = fl.features[f.gate];
          if (gate) gate.open = true;
          this.sound("lever");
          this.say("A stone sinks under your boot - and somewhere, iron grinds upward.");
          this.dirty = true;
        } else this.say("The plate is down already.");
      } else if (f.trap && !f.spent) {
        f.known = true; f.spent = true;
        this.sound("trap");
        this.say(`A stone sinks under your boot: ${CM.TRAPS[f.trap]}!`);
        this.springTrap(f.trap, k);
      }
    } else if (f.type === "fountain") {
      this.say(f.used ? "A dry fountain." : "A fountain, running. (Space to drink)");
    } else if (f.type === "altar") {
      this.say(f.used ? "A quiet altar." : "An altar, with candles still lit. (Space to kneel)");
    }
  }

  fall(from) {
    const n = this.floor.number;
    for (const m of this.alive()) m.hp = Math.max(1, m.hp - Math.max(1, Math.floor(m.max / 10)));
    this.sound("fall");
    this.emit("fell");
    if (n >= CM.BOTTOM) { this.say("You fall into blackness... and land, bruised, on the stone below."); return; }
    this.say(`You fall to floor ${n + 1}, bruised but alive.`);
    this.enterFloor(n + 1, "fall", from);
  }

  // ---- light ----
  burn() {
    if (this.spellLight > 0) {
      this.spellLight -= 1;
      if (this.spellLight === 0) this.say("The conjured light fades.");
    }
    const l = this.light;
    if (l.kind !== "torch") return;
    if ((this.steps || 0) % 2 === 1 && this.alive().some((h) => CM.trait(h, "pathfinder"))) return;   // (the Pathfinder banks the fire: every other step is free)
    l.left -= (this.floor && this.floor.special === "wading") || this.has("gloom") ? 2 : 1;
    if (l.left === 40) this.say("Your torch is burning low.");
    if (l.left > 0) return;
    const spare = this.bag.findIndex((i) => i.kind === "torch");
    if (spare >= 0) {
      this.bag.splice(spare, 1);
      this.light = { kind: "torch", left: CM.TORCH_STEPS };
      this.say("Your torch gutters out. You light a fresh one.");
    } else {
      this.light = { kind: null, left: 0 };
      this.say("Your torch gutters out. The dark closes in.");
    }
  }

  inDark() { return this.floor ? this.floor.dark.includes(keyOf(this.floor.pos[0], this.floor.pos[1])) : false; }

  // how far the party can see, as a share of the depth's reach
  lightFactor() {
    const l = this.light, spell = this.spellLight > 0;
    if (this.inDark()) return spell ? 0.7 : l.kind === "lantern" ? 0.45 : 0.25;
    let f = l.kind === "lantern" ? 1.15 : l.kind === "torch" ? (l.left > 40 ? 1 : 0.6) : 0.22;
    if (spell) f = Math.max(f, 1.1);
    return f;
  }

  hasLight() { return Boolean(this.light.kind) || this.spellLight > 0; }

  // what the party can see goes on the automap: around them, and along the corridor they face - by torchlight
  look() {
    const fl = this.floor, size = fl.grid.length;
    const seen = new Set(fl.seen.map(([x, y]) => keyOf(x, y)));
    const [x, y] = fl.pos;
    seen.add(keyOf(x, y));
    const spell = this.spellLight > 0;                               // (a conjured light sees through a magical dark)
    if (!this.inDark() || spell) {
      for (let dx = -1; dx <= 1; dx++) for (let dy = -1; dy <= 1; dy++) seen.add(keyOf(x + dx, y + dy));
      if (this.hasLight()) {
        const [fx, fy] = CM.DIRS[fl.facing];
        for (let d = 1; d < 5; d++) {
          const cx = x + fx * d, cy = y + fy * d;
          if (fl.dark.includes(keyOf(cx, cy)) && !spell) break;
          seen.add(keyOf(cx, cy)); seen.add(keyOf(cx + fy, cy + fx)); seen.add(keyOf(cx - fy, cy - fx));
          if (!CM.passable(fl, cx, cy)) break;
        }
      }
    }
    const warden = this.alive().find((h) => CM.trait(h, "wardeneye"));
    if (warden) {                                                        // the Warden's eye: a trap two steps off is seen, a hidden door beside you found
      for (const [k, f] of Object.entries(fl.features)) {
        const [tx, ty] = k.split(",").map(Number), d = Math.abs(tx - x) + Math.abs(ty - y);
        if (d <= 2 && ((f.type === "trapdoor" && !f.known) || (f.type === "plate" && f.trap && !f.known && !f.spent))) { f.known = true; this.say(`${warden.name} points: a trap, there.`); }
        else if (d <= 1 && f.type === "secret" && !f.found) { f.found = true; fl.grid[ty][tx] = 0; this.say(`${warden.name} runs a hand along the wall, finds a hairline - and a hidden door gives.`); this.emit("mesh"); }
      }
    }
    fl.seen = [...seen].map((k) => k.split(",").map(Number)).filter(([a, b]) => a >= 0 && a < size && b >= 0 && b < size);
  }

  use() {
    if (this.mode !== "explore") return;
    const fl = this.floor, [x, y] = fl.pos, k = keyOf(x, y), here = fl.features[k], thing = fl.things[k];
    const [dx, dy] = CM.DIRS[fl.facing], ak = keyOf(x + dx, y + dy), ahead = fl.features[ak];
    if (here && here.type === "lever" && here.face === fl.facing) {
      if (here.pulled) { this.say("The lever is down already."); return; }
      here.pulled = true;
      const gate = fl.features[here.gate];
      if (gate) gate.open = true;
      this.sound("lever");
      this.say("You haul the lever down. Somewhere, iron grinds upward.");
      this.dirty = true;
      this.emit("change");
      return;
    }
    if (here && here.type === "carving" && here.face === fl.facing) {
      here.read = true;
      const text = CM.loreText(here.text);
      this.say("You read the carving on the wall.");
      this.remember("carving", text);
      this.emit("lore", text);
      this.dirty = true;
      return;
    }
    if (thing && ["ghost", "hermit", "adventurer"].includes(thing.type)) { this.talk(thing, k); return; }
    if (thing && thing.type === "rope") {
      this.sound("stairs");
      this.enterFloor(fl.number - 1, "rope", thing.up);
      this.say("Hand over hand, you climb the rope back up to the pit's mouth.");
      return;
    }
    if (thing && thing.type === "chest") {
      if (thing.trap) {                                                   // a trapped lid: the Rogue may see to it
        const rogue = this.alive().find((p) => p.cls === "Rogue" && this.canAct(p));
        if (rogue && this.rnd.chance(CM.clamp(0.5 + rogue.level * 0.05 + CM.mod(this.stat(rogue, "dex")) * 0.1, 0.2, 0.95))) {
          this.say(`${rogue.name} finds ${CM.TRAPS[thing.trap]} on the lid, and sees to it.`);
          thing.trap = null;
        } else {
          this.sound("trap");
          this.say(`The lid was trapped: ${CM.TRAPS[thing.trap]}!`);
          this.springTrap(thing.trap, k);
          thing.trap = null;
          if (this.mode !== "explore") return;                           // (an alarm: the fight is on, the chest waits)
        }
      }
      delete fl.things[k];
      const gold = thing.gold * (this.has("rich") ? 2 : 1);
      this.gold += gold;
      this.bag.push(...thing.items);
      this.sound("chest");
      this.count("chests");
      this.emit("fx", { kind: "sparkle", at: [x, y] });
      const found = thing.items.map((i) => (i.unknown ? `${CM.baseName(i)} (unknown)` : i.name)).join(", ");
      this.say(`The chest creaks open: ${gold} gold` + (found ? `, ${found}.` : "."));
      if (this.gold >= 2000) this.achieve("hoarder");
      this.saveRun();
      this.emit("change");
    } else if (thing && thing.type === "ladder") {
      this.sound("stairs");
      if (CM.CAMP_AFTER.includes(fl.number)) {
        this.setMode("camp");
        this.saveRun();
        this.say(`Halfway down a long shaft, a lantern glows: a merchant's camp beneath floor ${fl.number}. Rest, trade, and see to the fallen.`);
      } else {
        this.enterFloor(fl.number + 1, "down");
      }
    } else if (thing && thing.type === "stairs_up") {
      this.climbUp();
    } else if (thing && thing.type === "phylactery") {
      delete fl.things[k];
      this.phylactery = true;
      this.sound("shatter");
      this.say("You lift the box from the east and dash it on the stone. Something inside screams - and far below, something else does.");
      this.emit("fx", { kind: "shatter" });
      this.saveRun();
      this.emit("change");
    } else if (here && here.type === "fountain") {
      this.drink(here);
    } else if (here && here.type === "altar") {
      this.kneel(here);
    } else if (!CM.isOpen(fl, x + dx, y + dy)) {                       // a wall before you: search it
      if (ahead && ahead.type === "secret" && !ahead.found) {
        ahead.found = true;
        fl.grid[y + dy][x + dx] = 0;
        this.sound("grind");
        this.say("You press the stones... and a hidden door grinds open!");
        this.look();
        this.emit("mesh");
        this.dirty = true;
        this.emit("change");
      } else {
        this.say("You search the wall and find nothing.");
      }
    } else {
      this.say("There's nothing here to use.");
    }
  }

  // what a trapped chest does to whoever opens it
  springTrap(trap, k) {
    this.emit("fx", { kind: "trap", trap });
    const opener = this.alive()[0];
    if (trap === "needle" && opener) this.afflict(opener, "poison", "needle") || this.say(`${opener.name} snatches a hand back in time.`);
    else if (trap === "gas") for (const p of this.alive()) p.hp = Math.max(1, p.hp - Math.max(1, Math.floor(p.max * 0.1)));
    else if (trap === "blade" && opener) { opener.hp = Math.max(1, opener.hp - Math.max(2, Math.floor(opener.max * 0.15))); this.say(`The blade catches ${opener.name}.`); }
    else if (trap === "alarm") {
      const fl = this.floor, [x, y] = k.split(",").map(Number);
      const spot = CM.DIRS.map(([dx, dy]) => [x + dx, y + dy]).find(([nx, ny]) => CM.passable(fl, nx, ny) && !fl.things[keyOf(nx, ny)] && !(nx === fl.pos[0] && ny === fl.pos[1]));
      const group = CM.monsterGroup(fl.number, this.rnd);
      if (spot) {
        const sk = keyOf(spot[0], spot[1]);
        fl.things[sk] = { type: "monsters", group };
        this.startCombat(sk, fl.things[sk], true);
      } else {
        this.foes = group;
        this.startCombat(k, { group }, true);
      }
    }
    this.emit("change");
  }

  drink(f) {
    if (f.used) { this.say("The fountain has run dry."); return; }
    f.used = true; f.known = true;
    if (this.has("drought")) { this.say("The basin is dry to the bottom, cracked. A drought lies on the dungeon today."); this.saveRun(); this.emit("change"); return; }
    if (f.kind === "heal") {
      for (const m of this.alive()) { m.hp = m.max; this.cure(m, [...CM.CURABLE, "curse"]); }
      this.sound("heal");
      this.say("The water is cold and clean. Every wound closes, and every ailment but stone passes.");
    } else if (f.kind === "mana") {
      for (const m of this.alive()) m.mp = m.maxmp;
      this.sound("heal");
      this.say("The water tingles. Magic returns to the casters.");
    } else {
      for (const m of this.alive()) m.hp = Math.max(1, m.hp - Math.max(1, Math.floor(m.max * 0.15)));
      this.sound("hurt");
      this.say("The water is foul! The party retches and staggers.");
    }
    this.saveRun();
    this.emit("change");
  }

  kneel(f) {
    if (f.used) { this.say("You have prayed here already. The candles gutter."); return; }
    f.used = true;
    let lifted = 0;
    for (const m of this.alive()) { m.hp = Math.min(m.max, m.hp + Math.max(1, Math.floor(m.max * 0.3))); lifted += this.cure(m, ["curse"]).length; }
    this.sound("heal");
    this.say("You kneel. A warmth passes through the party" + (lifted ? ", and the curse lifts." : "."));
    this.saveRun();
    this.emit("change");
  }

  // ---- the monsters move: towards the party when they're near, else as they please ----
  tick(dt) {
    if (this.mode === "explore" && this.dirty) {
      this.sinceSave += dt;
      if (this.sinceSave > 4) this.saveRun();
    }
    if (this.mode !== "explore") return;
    this.wander += dt;
    if (this.wander < (this.has("swift") ? 0.7 : 1.1)) return;
    this.wander = 0;
    const fl = this.floor, [px, py] = fl.pos;
    const walk = (x, y) => {
      if (!CM.passable(fl, x, y)) return false;
      const f = fl.features[keyOf(x, y)];
      return !(f && ["pit", "trapdoor", "teleporter", "spinner"].includes(f.type));
    };
    const dist = CM.distances(fl.grid, fl.pos, walk);
    let nearest = null;                                                  // the nearest group within earshot: its call
    for (const [k, t] of Object.entries(fl.things)) {
      if (t.type !== "monsters" && t.type !== "boss" && t.type !== "guardian") continue;
      const d = dist.get(k);
      if (d !== undefined && d <= 6 && (!nearest || d < nearest.d)) nearest = { d, t };
    }
    if (nearest) { const m = nearest.t.group.find((f) => f.hp > 0 && !f.fled) || nearest.t.group[0]; if (m) this.emit("near", m.kind || m.name, nearest.d); }
    const movers = Object.entries(fl.things).filter(([, t]) => t.type === "monsters" && !t.still);
    this.rnd.shuffle(movers);
    for (const [k, t] of movers) {
      const [x, y] = k.split(",").map(Number);
      const d = dist.get(k);
      let step = null;
      const options = CM.DIRS.map(([dx, dy]) => [x + dx, y + dy]).filter(([nx, ny]) => walk(nx, ny) && !fl.things[keyOf(nx, ny)]);
      if (d === 1) {
        this.startCombat(k, t, true);
        return;
      }
      if (d !== undefined && (d <= 7 || t.hunter)) {
        const nearer = options.filter(([nx, ny]) => dist.get(keyOf(nx, ny)) === d - 1 && !(nx === px && ny === py));
        if (nearer.length) step = this.rnd.pick(nearer);
      } else if (this.rnd.chance(0.3) && options.length) {
        step = this.rnd.pick(options.filter(([nx, ny]) => !(nx === px && ny === py)));
      }
      if (!step) continue;
      delete fl.things[k];
      t.anim = { from: [x, y], at: performance.now() };
      fl.things[keyOf(step[0], step[1])] = t;
      this.dirty = true;
    }
    this.emit("change");
  }

  // ---- fighting: turn by turn, in order of speed ----
  // this.combat: { round, order [{hero | foe, init}], index, waiting (the hero whose turn it is), surprise (the party's
  // free round), taunter / tauntUntil, bless, protect, reached (foes that have come at the party this round) }
  startCombat(key, thing, theyCame = false) {
    this.foes = thing.group.map(CM.upgradeMonster);
    if (this.has("hordes") && !thing.horded && this.foes.length && !this.foes[0].boss && !this.foes[0].guardian) {   // one more, of the first kind
      thing.horded = true;
      const kind = CM.monsterKind(this.foes[0].kind || this.foes[0].name);
      if (kind) this.foes.push(CM.makeMonster(kind, CM.monsterLevel(this.floor ? this.floor.number : 1), this.rnd));
    }
    for (const m of this.foes) this.tune(m);
    thing.group = this.foes;
    this.fightFell = false;
    this.foeKey = key;
    delete thing.anim;
    if (!(this.song && this.songEpic === this.floor.number)) this.song = 0;   // the Bard's song lasts the fight (an Epic one, the floor)
    for (const h of this.party) { h.cried = false; h.winded = false; h.defending = false; h.guardedBy = null; h.guarding = null; h.used = {}; h.struck = false; }
    for (const m of this.foes) { m.held = 0; m.asleep = 0; m.blind = 0; m.marked = false; m.charged = false; m.fled = false; m.dead = m.hp <= 0; }
    this.target = 0;
    this.combat = { foes: this.foes, round: 0, order: [], index: 0, waiting: null, surprise: false, taunter: null, tauntUntil: 0, bless: false, protect: false, reached: 0 };
    this.setMode("combat");
    this.count("fights");
    this.sound(CM.roarFor((this.foes[0] || {}).kind || (this.foes[0] || {}).name));
    const names = {};
    for (const m of this.foes) names[m.name] = (names[m.name] || 0) + 1;
    const who = Object.entries(names).map(([k, n]) => CM.plural(n, k)).join(", ");
    const guardian = this.foes.find((m) => m.guardian);
    if (this.foes.some((m) => m.boss)) this.say(`The Lich King rises from his throne. "You took your time," he says.${this.phylactery ? "" : " Somewhere, his heart beats."}`);
    else if (guardian) this.say(CM.GUARDIANS[guardian.guardian].intro + (guardian.hp < guardian.max ? " The wounds you left are still there." : ""));
    else this.say(theyCame ? `${who} come at you out of the dark!` : `Monsters! ${who} attack!`);
    const sneaky = this.alive().some((h) => ["Rogue", "Ranger"].includes(h.cls) && this.canAct(h));
    if ((theyCame || this.inDark()) && !this.alive().some((h) => CM.trait(h, "slippery")) && this.rnd.chance(0.5)) {   // surprise: they're on you before you can draw...
      this.say("They're on you before you can draw!");
      for (const m of this.living()) this.monsterAct(m);
      this.afterBlows();
      if (this.mode !== "combat") return;
    } else if (!theyCame && this.rnd.chance(sneaky ? 0.35 : 0.2)) {     // ...or you have the drop on them
      this.say("You have the drop on them: a free round!");
      this.combat.surprise = true;
    }
    this.beginRound();
  }

  // a fight begun some other way (the tests set the mode by hand) still gets its turns
  ensureCombat() {
    if (this.combat && this.combat.order && this.combat.foes === this.foes) return;
    for (const h of this.party) { h.cried = false; h.winded = false; h.defending = false; h.guardedBy = null; h.guarding = null; h.used = h.used || {}; }
    for (const m of this.foes) { CM.upgradeMonster(m); m.held = m.held || 0; m.asleep = m.asleep || 0; m.blind = m.blind || 0; }
    this.target = 0;
    this.combat = { foes: this.foes, round: 0, order: [], index: 0, waiting: null, surprise: false, taunter: null, tauntUntil: 0, bless: false, protect: false, reached: 0 };
    this.beginRound();
  }

  alive() { return this.party.filter((m) => m.hp > 0); }
  living() { return this.foes.filter((m) => m.hp > 0 && !m.fled); }
  canAct(h) { const s = h.status || {}; return h.hp > 0 && !s.paralysis && !s.sleep && !s.stone; }   // standing, and not held by an ailment
  targets() { return this.alive().filter((h) => !(h.status || {}).stone); }                           // what a monster can reach: stone isn't worth hitting

  // the party's square: in a corridor, only two foes can come at them at once
  reachLimit() {
    const fl = this.floor;
    return fl && CM.openNeighbours(fl, fl.pos[0], fl.pos[1]).length <= 2 ? 2 : 99;
  }

  // a round: everyone standing, in order of speed (the dice have a say); heroes win ties
  beginRound() {
    const c = this.combat;
    c.round += 1;
    c.reached = 0;
    const order = [];
    for (const h of this.party) if (h.hp > 0) order.push({ hero: h, init: this.stat(h, "dex") + (["Rogue", "Ranger"].includes(h.cls) ? 2 : 0) + this.rnd.int(1, 6) + 0.5 });
    if (!c.surprise) for (const m of this.living()) order.push({ foe: m, init: (m.speed || 10) + this.rnd.int(1, 6) });
    order.sort((a, b) => b.init - a.init);
    c.order = order;
    c.index = 0;
    c.waiting = null;
    this.emit("round", c.round);
    this.advance();
  }

  // on through the order until a hero needs telling what to do, or the round is over
  advance() {
    const c = this.combat;
    while (this.mode === "combat" && c) {
      if (c.index >= c.order.length) {
        this.endRound();
        if (this.mode === "combat") this.beginRound();
        return;
      }
      const slot = c.order[c.index++];
      if (slot.hero) {
        const h = slot.hero;
        if (h.hp <= 0) continue;
        h.defending = false;                                               // (a guard raised lasts until now)
        if (h.guarding) { h.guarding.guardedBy = null; h.guarding = null; }
        const st = h.status || {};
        if (!this.canAct(h)) { if (!st.stone) this.say(`${h.name} is ${st.sleep ? "asleep" : "paralysed"} and can't act.`); continue; }
        if (!this.living().length) continue;
        c.waiting = h;
        this.emit("turn", h);
        this.emit("change");
        return;
      }
      const m = slot.foe;
      if (m.hp <= 0 || m.fled) continue;
      this.monsterAct(m);
      this.afterBlows();
    }
  }

  // the round's end: poison bites, ailments run their course, trolls knit
  endRound() {
    const c = this.combat;
    for (const h of this.alive()) {
      const st = h.status || {};
      if (st.poison) {
        const bite = Math.max(1, Math.floor(h.max * ((h.boons || []).includes("thickblood") ? 0.025 : 0.05)));
        h.hp = Math.max(1, h.hp - bite);
        this.say(`${h.name} suffers from the poison (-${bite}).`);
      }
      for (const s of Object.keys(st)) {
        if (st[s] >= 900) continue;
        st[s]--;
        if (st[s] <= 0) { delete st[s]; this.say(`${h.name} is no longer ${CM.STATUSES[s].name.toLowerCase()}.`); }
      }
    }
    for (const m of this.living()) {
      if (m.ability === "regen" && m.hp < m.max) {
        const back = Math.max(1, Math.floor(m.max * 0.05));
        m.hp = Math.min(m.max, m.hp + back);
        this.say(`The ${m.name}'s wounds knit (+${back}).`);
      }
      if (CM.guardianHas(m, "regrow") && m.hp < m.max) {                 // (the Mind's flesh, the Root's sap)
        const back = Math.max(1, Math.floor(m.max * 0.05));
        m.hp = Math.min(m.max, m.hp + back);
        this.say(`${CM.The(m)} regrows (+${back}).`);
      }
      if (m.burning > 0) {                                               // (an Inferno's fire)
        m.burning -= 1;
        this.spellHit(m, m.burnDmg || 5, `${CM.The(m)} burns:`, "fire");
      }
    }
    for (const h of this.alive()) if (CM.trait(h, "wellspring") && h.mp < h.maxmp) h.mp = Math.min(h.maxmp, h.mp + 2);
    if (this.alive().some((h) => CM.trait(h, "evergreen"))) for (const h of this.alive()) h.hp = Math.min(h.max, h.hp + 3);
    c.surprise = false;
    this.afterBlows();
    this.emit("change");
  }

  // after blows are struck: the fallen, the Lich King's rising, victory or the end
  afterBlows() {
    for (const m of this.foes) if (m.hp <= 0 && !m.dead && !m.fled) { m.dead = true; this.emit("fx", { kind: "die", foe: m }); }
    for (const h of this.party) h.hp = Math.max(0, h.hp);
    if (this.mode !== "combat") return;
    const lich = this.foes.find((m) => m.boss);
    if (lich && lich.hp <= 0 && !this.phylactery) {
      lich.hp = Math.floor(lich.max * CM.LICH.riseTo);
      lich.dead = false;
      lich.risen = (lich.risen || 0) + 1;
      this.sound("lich");
      this.say("The Lich King crumbles... and the bones knit again. Somewhere, his heart still beats.");
      this.summonSkeletons(2);
      this.emit("fx", { kind: "rise", foe: lich });
    }
    for (const m of this.foes) {
      if (!CM.guardianHas(m, "rise") || m.hp > 0 || m.risen) continue;
      m.hp = Math.floor(m.max / 3); m.dead = false; m.risen = 1;
      this.sound("lich");
      this.say(CM.GUARDIANS[m.guardian].riseText || `${CM.The(m)} rises again.`);
      this.emit("fx", { kind: "rise", foe: m });
    }
    if (!this.living().length) { this.wonFight(); return; }
    if (!this.alive().length || this.alive().every((h) => (h.status || {}).stone)) {
      this.say(this.alive().length ? "The last of the party stands as stone, and the dark closes in..." : "The last of the party falls...");
      this.endRun(false);
    }
  }

  // the hero whose turn it is does something: fight (the chosen foe), cast {id, target}, item {row, who}, defend, run
  act(action, arg) {
    const c = this.combat, h = c && c.waiting;
    if (!h || this.mode !== "combat") return false;
    if (action === "fight") {
      const t = this.foeAt(arg);
      if (!t) return false;
      this.strike(h, t);
      if (CM.trait(h, "flurry") && t.hp > 0 && !t.fled) this.strike(h, t, " again", { mult: 0.5 });
    } else if (action === "cast") {
      const id = arg && arg.id !== undefined ? arg.id : this.defaultAbility(h);
      if (!this.useAbility(h, id, arg && arg.target !== undefined ? arg.target : null)) return false;
    } else if (action === "item") {
      if (!this.useItemInBattle(h, arg)) return false;
    } else if (action === "defend") {
      h.defending = true;
      this.say(`${h.name} raises a guard.`);
    } else if (action === "run") {
      if (this.flee(false)) return true;
      this.say("You can't get away!");
    } else {
      return false;
    }
    if (this.mode !== "combat" || !this.combat) return true;
    c.waiting = null;
    this.afterBlows();
    if (this.mode === "combat") this.advance();
    return true;
  }

  // the chosen foe: an index among the living, a foe itself, or the one picked already (Tab, or a click)
  foeAt(arg) {
    const foes = this.living();
    if (!foes.length) return null;
    if (arg && typeof arg === "object") return foes.includes(arg) ? arg : foes[0];
    const i = typeof arg === "number" ? arg : (this.target || 0);
    return foes[Math.min(Math.max(0, i), foes.length - 1)];
  }

  setTarget(i) {
    const n = this.living().length;
    if (!n) return;
    this.target = ((i % n) + n) % n;
    this.emit("change");
  }

  // one of the party to cast on: an index, the hero itself, or the one who needs it most
  allyAt(target, fallen) {
    const pool = this.party.filter((p) => (fallen ? p.hp <= 0 : p.hp > 0));
    if (!pool.length) return null;
    if (target && typeof target === "object") return pool.includes(target) ? target : null;
    if (typeof target === "number") return pool.includes(this.party[target]) ? this.party[target] : null;
    return fallen ? pool[0] : pool.reduce((a, b) => (a.hp / a.max <= b.hp / b.max ? a : b));
  }

  // every hero does the one thing, with the foe and friend that need it most: the old game's round, kept for the tests
  combatRound(action) {
    if (this.mode !== "combat") return;
    this.ensureCombat();
    const round = this.combat.round;
    let guard = 0;
    while (this.mode === "combat" && this.combat && this.combat.round === round && this.combat.waiting && guard++ < 20) {
      const ok = action === "potion" ? this.act("item", null) : this.act(action, null);
      if (!ok && this.mode === "combat" && this.combat && this.combat.waiting) this.act("defend");
    }
  }

  // running: more than half the time (a Rogue helps), and never from the Lich King; the party steps back a square
  flee(sure) {
    if (this.foes.some((m) => m.boss && m.hp > 0) && !sure) { this.say("There's no running from the Lich King."); return false; }
    if (!sure && !this.alive().some((h) => CM.trait(h, "slippery")) && !this.rnd.chance(0.55 + (this.alive().some((h) => h.cls === "Rogue") ? 0.1 : 0))) return false;
    const fl = this.floor;
    for (let i = 0; i < (sure ? 2 : 1); i++) {                          // back the way you came, while the way is clear
      const [dx, dy] = CM.DIRS[(fl.facing + 2) % 4], nx = fl.pos[0] + dx, ny = fl.pos[1] + dy, k = keyOf(nx, ny);
      const f = fl.features[k];
      if (!CM.passable(fl, nx, ny) || fl.things[k] || (f && ["pit", "trapdoor", "teleporter", "spinner"].includes(f.type))) break;
      fl.pos = [nx, ny];
      this.emit("moved", nx, ny);
    }
    const guardian = this.foes.find((m) => m.guardian && m.hp > 0);
    if (guardian) {                                                      // it keeps its lair: it mends a little, and the swarm goes back into the walls
      guardian.hp = Math.min(guardian.max, guardian.hp + Math.floor(guardian.max / 4));
      const lairThing = this.floor.things[this.foeKey];
      if (lairThing) lairThing.group = this.foes.filter((m) => !m.summoned);
      this.say(`Behind you, ${CM.the(guardian)} settles back over the shaft to lick its wounds.`);
    }
    this.say(sure ? "The world folds, and the party is elsewhere." : "The party flees back the way it came!");
    this.count("fled");
    this.combat = null;
    this.setMode("explore");
    this.look();
    this.saveRun();
    return true;
  }

  damage(atk, power, df) {
    return Math.max(1, atk + power + this.rnd.int(0, Math.max(1, Math.floor((atk + power) / 2))) - Math.floor(df / 2));
  }

  // a hero's numbers as they stand right now: a curse takes from them, the song and a blessing give
  effective(h) {
    const cursed = (h.status || {}).curse ? 2 : 0, bless = this.combat && this.combat.bless;
    return { atk: Math.max(1, h.atk - cursed + (this.song === 2 ? 4 : this.song ? 2 : 0) + (bless ? 2 : 0)), df: Math.max(0, h.df - cursed + (bless ? 1 : 0)) };
  }
  stat(h, s) { return CM.heroStat(h, s); }
  hitChance(h) {
    return CM.clamp(0.8 + (this.stat(h, "dex") - 10) * 0.01 + ((h.boons || []).includes("keeneye") ? 0.1 : 0) - ((h.status || {}).blind ? 0.4 : 0), 0.25, 0.97);
  }
  critChance(h) { return CM.clamp((h.cls === "Rogue" ? 0.25 : 0.05) + (this.stat(h, "luck") - 10) * 0.01, 0.02, 0.6); }
  resistChance(h) {
    return CM.clamp((this.stat(h, "luck") - 10) * 0.02 + (this.stat(h, "wis") - 10) * 0.01 + ((h.boons || []).includes("thickblood") ? 0.2 : 0), 0, 0.6);
  }
  spellMod(h) { return this.stat(h, (CM.CLASSES[h.cls] || CM.CLASSES.Knight).key) - 10; }

  // an ailment settles on a hero, unless they shrug it off; it lasts this many rounds (curses and stone, until lifted)
  afflict(h, status, by) {
    if (!CM.STATUSES[status] || (h.status || {})[status]) return false;
    const charm = CM.equipped(h).find((it) => it.props && it.props.resist === status && !it.unknown);
    if (charm) { this.say(`${h.name}'s ${CM.baseName(charm)} grows warm: the ${status === "stone" ? "gaze" : "touch"} finds no purchase.`); return false; }
    if (this.rnd.chance(this.resistChance(h))) { this.say(`${h.name} shrugs off ${CM.the(by)}'s ${status === "stone" ? "gaze" : "touch"}.`); return false; }
    h.status = h.status || {};
    let turns = { poison: 8, paralysis: 2, sleep: 3, blind: 4, curse: 999, stone: 999 }[status];
    if (status === "poison" && by === CM.GUARDIANS.rat.name) turns = 12;
    if (turns < 900 && (h.boons || []).includes("thickblood")) turns = Math.ceil(turns / 2);
    h.status[status] = turns;
    this.sound("ailment");
    this.say(`${h.name} is ${CM.STATUSES[status].name.toLowerCase()}!`);
    this.emit("fx", { kind: "ailment", hero: h, status });
    return true;
  }

  cure(h, which) {                                                       // which: a list of ailments, or "all"
    const cured = [];
    for (const s of Object.keys(h.status || {})) if (which === "all" || which.includes(s)) { delete h.status[s]; cured.push(s); }
    return cured;
  }

  // who a monster goes for: the Knight's taunt, else the front row (the Knight most of all) - unless it shoots
  pickTarget(m) {
    const pool = this.targets(), c = this.combat || {};
    if (!pool.length) return null;
    if (c.taunter && pool.includes(c.taunter) && c.round <= c.tauntUntil) return c.taunter;
    if (m && m.ability === "ranged") return this.rnd.pick(pool);
    const front = pool.some((h) => h.row === "front");
    const weights = pool.map((h) => (front ? (h.row === "front" ? (h.cls === "Knight" ? 5 : 3) : 1) : 1));
    let r = this.rnd.next() * weights.reduce((a, b) => a + b, 0);
    for (let i = 0; i < pool.length; i++) { r -= weights[i]; if (r < 0) return pool[i]; }
    return pool[pool.length - 1];
  }

  // a blow lands on a hero: a guard steps in, a raised guard halves it, the song and a prayer soften it
  hurt(h, dmg, by, opts = {}) {
    const c = this.combat || {};
    if (h.guardedBy && h.guardedBy !== h && h.guardedBy.hp > 0 && this.canAct(h.guardedBy)) {
      this.say(`${h.guardedBy.name} steps in front of ${h.name}!`);
      if (CM.trait(h.guardedBy, "aegis")) dmg = Math.ceil(dmg / 2);
      h = h.guardedBy;
    }
    if (h.defending) dmg = Math.ceil(dmg / 2);
    if (this.song) dmg -= this.song;
    if (c.protect) dmg -= 3;
    dmg = Math.max(1, dmg);
    h.hp -= dmg;
    if ((h.status || {}).sleep) delete h.status.sleep;                   // (a blow wakes)
    this.sound(h.hp <= 0 ? "fallen" : "hurt");
    this.emit("fx", { kind: "hurt", hero: h, amount: dmg, foe: by });
    this.say(`${CM.The(by)} hits ${h.name} for ${dmg}${opts.how || ""}.` + (h.hp <= 0 ? `  ${h.name} falls!` : ""));
    if (h.hp <= 0) { this.fightFell = true; this.everFell = true; }
    if (h.hp > 0) {
      if (!opts.noTouch && by.touch && this.rnd.chance(by.touch.chance)) this.afflict(h, by.touch.status, by.name);
      if ((h.boons || []).includes("secondwind") && !h.winded && h.hp < h.max / 4) {
        h.winded = true;
        const back = Math.floor(h.max / 3);
        h.hp = Math.min(h.max, h.hp + back);
        this.say(`${h.name} finds a second wind (+${back}).`);
      }
    }
    return dmg;
  }

  // a monster's turn: what its kind does
  monsterAct(m) {
    const c = this.combat || {}, rnd = this.rnd;
    if (m.asleep > 0) { m.asleep--; if (m.asleep === 0) this.say(`The ${m.name} stirs.`); return; }
    if (m.held > 0) { m.held--; this.say(`The ${m.name} is held fast.`); return; }
    if (m.boss) { this.lichAct(m); return; }
    if (m.guardian) { this.guardianAct(m); return; }
    if (m.ability !== "ranged" && m.ability !== "breath") {
      c.reached = (c.reached || 0) + 1;
      const limit = this.reachLimit();
      if (c.reached > limit) { if (c.reached === limit + 1) this.say("The rest crowd behind, unable to reach you in the narrow way."); return; }
    }
    if (m.ability === "coward" && m.hp < m.max * 0.3) {
      const purse = Math.floor(this.gold * 0.05);
      this.gold -= purse;
      m.fled = true;
      this.say(`The ${m.name} snatches a purse (${purse} gold) and bolts!`);
      this.emit("fx", { kind: "die", foe: m });
      return;
    }
    if (m.ability === "breath") {
      m.breath = (m.breath || 0) + 1;
      if (m.breath % 2 === 0) {
        this.emit("fx", { kind: "attack", foe: m, breath: true });
        this.say(`The ${m.name} breathes fire over the whole party!`);
        for (const h of this.targets()) this.hurt(h, Math.max(1, Math.floor(m.atk / 3) + 2), m, { noTouch: true });
        return;
      }
    }
    this.emit("fx", { kind: "attack", foe: m, ranged: m.ability === "ranged" });
    const blows = m.ability === "buffet" ? 2 : 1;
    for (let i = 0; i < blows; i++) {
      const target = this.pickTarget(m);
      if (!target) break;
      if (!rnd.chance(0.8 * (m.blind > 0 ? 0.5 : 1))) { this.say(`${CM.The(m)} misses ${target.name}.`); continue; }
      let dmg = this.damage(Math.floor(m.atk / 2), 0, this.effective(target).df + CM.gearDefence(target)), how = "";
      if (m.ability === "savage" && rnd.chance(0.2)) { dmg *= 2; how = " - a savage blow"; }
      if (m.ability === "charge" && !m.charged) { m.charged = true; dmg *= 2; how = " - it charges"; }
      const dealt = this.hurt(target, dmg, m, { how });
      if (target.hp > 0) {
        if (m.ability === "stun" && rnd.chance(0.25) && !(target.status || {}).paralysis) { target.status.paralysis = 1; this.say(`${target.name} is knocked flat!`); }
        if (m.ability === "drain" && target.xp > 0) {
          const lost = Math.min(target.xp, Math.max(5, Math.floor(CM.xpForLevel(target.level + 1) * 0.15)));
          target.xp -= lost;
          this.say(`${target.name} feels the ${m.name} draw out ${lost} experience.`);
        }
      }
      if (m.ability === "lifesteal") { const back = Math.ceil(dealt / 2); m.hp = Math.min(m.max, m.hp + back); this.say(`The ${m.name} feeds: +${back}.`); }
    }
    if (m.blind > 0) m.blind--;
  }

  // the Lich King: a grave-cold touch; hurt, he calls skeletons up out of the floor; near his end, a deathly cold on everyone
  lichAct(m) {
    const c = this.combat || {}, share = m.hp / m.max;
    if (share <= CM.LICH.summonFrom) {
      c.summonTick = (c.summonTick || 0) + 1;
      const up = this.foes.filter((f) => f.summoned && f.hp > 0).length;
      if (c.summonTick % CM.LICH.summonEvery === 1 && up < CM.LICH.summonMax) { this.summonSkeletons(Math.min(2, CM.LICH.summonMax - up)); return; }
    }
    if (share <= CM.LICH.coldFrom) {
      c.cold = (c.cold || 0) + 1;
      if (c.cold % 2 === 0) {
        this.emit("fx", { kind: "cold", foe: m });
        this.say("The Lich King raises his hand, and a deathly cold fills the hall!");
        for (const h of this.targets()) this.hurt(h, 10 + Math.floor(this.floor.number / 2), m, { noTouch: true });
        return;
      }
    }
    const target = this.pickTarget(m);
    if (!target) return;
    this.emit("fx", { kind: "attack", foe: m });
    if (!this.rnd.chance(0.85)) { this.say(`The Lich King's hand closes on nothing: ${target.name} is too quick.`); return; }
    this.hurt(target, this.damage(Math.floor(m.atk / 2), 0, this.effective(target).df + CM.gearDefence(target)), m, { how: " - a touch of grave-cold" });
  }

  summonSkeletons(n) {
    for (let i = 0; i < n; i++) {
      const s = CM.skeleton(CM.LAST_FLOOR, this.rnd);
      Object.assign(s, { summoned: true, held: 0, asleep: 0, blind: 0, marked: false, charged: false, fled: false, dead: false });
      this.foes.push(this.tune(s));
    }
    this.sound("roar_undead");
    this.say(`The Lich King calls, and ${CM.plural(n, "skeleton")} claw up out of the floor!`);
    this.emit("fx", { kind: "summon" });
  }

  // a guardian's turn (CM.GUARDIANS): every third turn one of its moves, in turn - a swarm called, a grasp, a slam on
  // the front line or on everyone, a breath of fire, an ailment on the party; otherwise a blow like any other
  guardianAct(m) {
    const rnd = this.rnd, G = CM.GUARDIANS[m.guardian], moves = G.moves || [];
    m.turns = (m.turns || 0) + 1;
    if (m.turns % 3 === 0 && moves.length) {
      const mv = moves[(Math.floor(m.turns / 3) - 1) % moves.length];
      if (this.guardianMove(m, mv)) return;
    }
    const target = this.pickTarget(m);
    if (!target) return;
    this.emit("fx", { kind: "attack", foe: m });
    if (!rnd.chance(0.85)) { this.say(`${CM.The(m)} misses ${target.name}.`); return; }
    let dmg = this.damage(Math.floor(m.atk / 2), 0, this.effective(target).df + CM.gearDefence(target)), how = "";
    if (CM.guardianHas(m, "plague") && (target.status || {}).poison) { dmg = Math.ceil(dmg * 1.5); how = " - the plague bites deep"; }
    this.hurt(target, dmg, m, { how });
    if (CM.guardianHas(m, "drain") && target.hp > 0 && target.xp > 0) {   // (the Patriarch's old hunger)
      const lost = Math.min(target.xp, Math.max(5, Math.floor(CM.xpForLevel(target.level + 1) * 0.15)));
      target.xp -= lost;
      this.say(`${target.name} feels ${CM.the(m)} draw out ${lost} experience.`);
    }
  }

  guardianMove(m, mv) {
    const rnd = this.rnd, who = (t) => (mv.text || "").replace("{who}", t ? t.name : "");
    if (mv.kind === "summon") {
      const up = this.foes.filter((f) => f.summoned && f.hp > 0 && !f.fled).length;
      if (up >= mv.max) return false;
      this.summonFor(m, mv, Math.min(mv.n, mv.max - up));
      return true;
    }
    if (mv.kind === "grasp") {
      const target = this.pickTarget(m);
      if (!target) return false;
      this.emit("fx", { kind: "grasp", hero: target, foe: m });
      this.say(who(target));
      this.hurt(target, Math.ceil(this.damage(Math.floor(m.atk / 2), 0, this.effective(target).df + CM.gearDefence(target)) * (mv.mult || 1.5)), m, { how: mv.how || "", noTouch: true });
      if (target.hp > 0 && mv.status && this.afflict(target, mv.status, m.name) && mv.status === "paralysis") target.status.paralysis = 1;
      return true;
    }
    if (mv.kind === "slam") {
      const pool = this.targets(), front = pool.filter((h) => h.row === "front"), struck = mv.front && front.length ? front : pool;
      if (!struck.length) return false;
      this.emit("fx", { kind: "slam", foe: m });
      this.sound("slam");
      this.say(who());
      for (const h of struck) {
        this.hurt(h, this.damage(Math.floor(m.atk / (mv.frac || 2.5)), 0, this.effective(h).df + CM.gearDefence(h)), m, { how: mv.how || "", noTouch: true });
        if (h.hp > 0 && mv.status && rnd.chance(mv.chance || 0.3) && !(h.status || {})[mv.status]) {
          h.status[mv.status] = mv.status === "paralysis" ? 1 : mv.status === "blind" ? 2 : 2;
          this.say((mv.flat || "{who} reels.").replace("{who}", h.name));
        }
      }
      return true;
    }
    if (mv.kind === "breath") {
      const pool = this.targets();
      if (!pool.length) return false;
      this.emit("fx", { kind: "attack", foe: m, breath: true });
      this.say(who());
      for (const h of pool) this.hurt(h, Math.max(1, Math.floor(m.atk / (mv.frac || 2)) + 2), m, { noTouch: true });
      return true;
    }
    if (mv.kind === "ailment") {
      const pool = this.targets();
      if (!pool.length) return false;
      this.emit("fx", { kind: "cold", foe: m });
      this.say(who());
      let took = 0;
      for (const h of pool) if (rnd.chance(mv.chance === undefined ? 0.6 : mv.chance) && this.afflict(h, mv.status, m.name)) took++;
      if (!took) this.say("The party shakes it off.");
      return true;
    }
    return false;
  }

  // what a guardian calls up: its own kind of company, at the Deep's level where it says so
  summonFor(m, mv, n) {
    const kind = CM.monsterKind(mv.what);
    if (!kind) return;
    const level = mv.level === "deep" ? CM.monsterLevel(this.floor ? this.floor.number : CM.LAST_FLOOR) : (this.floor ? this.floor.number : 5);
    for (let i = 0; i < n; i++) {
      const r = CM.makeMonster(kind, level, this.rnd);
      Object.assign(r, { summoned: true, held: 0, asleep: 0, blind: 0, marked: false, charged: false, fled: false, dead: false });
      this.foes.push(this.tune(r));
    }
    this.sound(CM.roarFor(kind.name));
    this.say((mv.text || "{n} come.").replace("{n}", mv.plural ? mv.plural.replace("{n}", String(n)) : CM.plural(n, mv.word || kind.name.toLowerCase())));
    this.emit("fx", { kind: "summon", layer: kind.undead ? "fx:shard" : "fx:spark" });
  }

  summonRats(n) { this.summonFor(this.foes.find((f) => f.guardian === "rat") || { name: "The Rat King" }, CM.GUARDIANS.rat.moves[0], n); }

  // the Lich King falls: the crown is the party's, and the choice - into the daylight, or down the shaft the throne hid
  crown() {
    this.crowned = true;
    this.trophy("lich");
    const steps = (this.tally || {}).steps || 0;
    this.achieve("crown");
    if (!this.everFell) this.achieve("ironman");
    if (steps < 1500) this.achieve("swift");
    if (this.difficulty === "grim") this.achieve("grim");
    this.achieve("delver"); this.achieve("deep"); this.achieve("deeper");
    if (this.foeKey) this.floor.things[this.foeKey] = { type: "ladder" };
    this.sound("victory");
    this.say("The crown rolls from the throne, and the cold goes out of the stone. Behind the throne the floor has split: a shaft goes down, into a dark that was never his. The Deep.");
    this.setMode("explore");
    this.saveRun();
    this.emit("crowned");
  }

  // a guardian falls: its relic into the pack, a trophy kept between runs, and the shaft it stood over is open
  slayGuardian(m) {
    const id = m.guardian, G = CM.GUARDIANS[id], relic = G.relic ? CM.relic(id) : null;
    this.tally.guardians = (this.tally.guardians || []).concat(id);
    this.trophy(id);
    if (relic) this.bag.push(relic);
    this.sound("toll");
    this.say(G.fall);
    this.say(relic ? `${G.take} (${relic.name}: ${CM.itemLabel(relic)}.)` : G.take);
    this.emit("fx", { kind: "relic", item: relic });
  }

  trophy(id) {                                                           // a guardian slain, remembered between runs
    if (this.trophies[id]) return;
    this.trophies[id] = { date: CM.today(), name: CM.playerName || "Adventurer", seed: this.seed };
    CM.store.set("trophies", this.trophies);
  }

  // one hero's blow on one foe (Fight, and the Ranger's arrows): the damage done, 0 for a miss
  strike(hero, target, note = "", opts = {}) {
    const rnd = this.rnd;
    this.emit("fx", { kind: "swing", hero, foe: target });
    const bow = Boolean(hero.weapon && hero.weapon.props && hero.weapon.props.bow), ambush = CM.trait(hero, "ambush") && !hero.struck;
    if (!opts.sure && !ambush && !(bow && CM.trait(hero, "truearrow")) && !rnd.chance(this.hitChance(hero))) {
      this.say(`${hero.name} misses${note ? " with" + note : ""}.`);
      this.sound("miss");
      this.emit("fx", { kind: "miss", foe: target });
      return 0;
    }
    let dmg = this.damage(this.effective(hero).atk, hero.weapon.power, target.df), how = "";
    const back = hero.row === "back", reaches = hero.cls === "Rogue" || hero.cls === "Ranger";
    const critMult = CM.trait(hero, "deadly") ? 3 : 2;
    if (hero.cls === "Rogue" && back) { dmg *= 2; how = " - a knife from behind"; }
    else if (ambush || rnd.chance(this.critChance(hero))) { dmg *= critMult; how = " - a weak spot"; }
    else if (back && !reaches) { dmg = Math.max(1, Math.ceil(dmg / 2)); how = ", reaching from the back row"; }
    if ((hero.boons || []).includes("warcry") && !hero.cried) { hero.cried = true; dmg *= 2; how += " - a war cry"; }
    const props = (hero.weapon && hero.weapon.props) || {}, el = props.element && !hero.weapon.unknown ? props.element : null;
    const G = target.guardian ? CM.GUARDIANS[target.guardian] : null;
    if (el) {                                                            // a flaming, frost or blessed blade
      const weak = (el === "holy" ? Boolean(target.undead) : (CM.ELEMENTS[el].weak || []).includes(target.kind || target.name)) || Boolean(G && G.weak === el);
      if (weak) { dmg = Math.ceil(dmg * 1.5); how += ` - the ${el === "holy" ? "blessing" : el} bites deep`; }
      else if (G && G.resist === el) { dmg = Math.max(1, Math.ceil(dmg / 2)); how += ` - the ${el} does little to it`; }
      else dmg += 2;
    }
    else if (target.undead && CM.trait(hero, "holyblade")) { dmg = Math.ceil(dmg * 1.5); how += " - the blessing in the blade bites deep"; }
    hero.struck = true;
    if (opts.mult) dmg = Math.ceil(dmg * opts.mult);
    if (target.marked) dmg = Math.ceil(dmg * 1.25);
    target.hp -= dmg;
    if (target.asleep > 0) { target.asleep = 0; how += " - it wakes"; }
    this.say(`${hero.name} hits ${CM.the(target)}${note} for ${dmg}${how}.`);
    this.emit("fx", { kind: "hit", foe: target, amount: dmg });
    this.sound("hit");
    if (props.stun && target.hp > 0 && !CM.unmoved(target) && rnd.chance(props.stun)) { target.held = Math.max(target.held || 0, 1); this.say(`${CM.The(target)} reels from the blow.`); }
    if ((CM.guardianHas(target, "heat") || CM.guardianHas(target, "glass")) && !props.bow && hero.hp > 0) {   // its heat, or its shards: whoever strikes it pays
      const burn = 2 + Math.floor((this.floor ? this.floor.number : 15) / 5);
      hero.hp = Math.max(1, hero.hp - burn);
      this.say((G.sear || "The heat of " + CM.the(target) + " sears {who} (-{n}).").replace("{who}", hero.name).replace("{n}", burn));
      this.emit("fx", { kind: "sear", hero, amount: burn, foe: target });
    }
    return dmg;
  }

  // a spell's blow: it doesn't miss
  spellHit(foe, dmg, what, element) {
    const G = foe.guardian ? CM.GUARDIANS[foe.guardian] : null;        // (a guardian's weakness, and what it shrugs off)
    if (element === "fire" && this.casting && CM.trait(this.casting, "firebrand")) dmg = Math.ceil(dmg * 1.5);
    if (G && element && G.weak === element) dmg = Math.ceil(dmg * 1.5);
    else if (G && element && G.resist === element) dmg = Math.max(1, Math.ceil(dmg / 2));
    if (foe.marked) dmg = Math.ceil(dmg * 1.25);
    foe.hp -= dmg;
    if (foe.asleep > 0) foe.asleep = 0;
    this.emit("fx", { kind: "hit", foe, amount: dmg, spell: true });
    if (what) this.say(`${what} ${foe.name} takes ${dmg}.`);
    return dmg;
  }

  // what a hero reaches for when told only "cast": their calling's own thing, if they can afford it
  defaultAbility(h) {
    const can = CM.abilitiesFor(h).filter((id) => CM.ABILITIES[id].mp <= h.mp && !(CM.ABILITIES[id].once && h.used && h.used[id]));
    const prefer = { Mage: ["fireball", "frost", "firebolt", "missile"], Cleric: ["heal"], Paladin: ["lay"], Druid: ["thorns"], Bard: ["song"],
      Ranger: ["volley"], Knight: ["guard"], Rogue: ["trick"] }[h.cls] || [];
    return prefer.find((id) => can.includes(id)) || null;
  }

  // the old game's Cast, kept for the tests: the calling's own thing, at whoever needs it most
  cast(hero) {
    if (!this.useAbility(hero, this.defaultAbility(hero), null)) {
      const t = this.foeAt(null);
      if (t) this.strike(hero, t);
    }
  }

  // a spell or skill, if the hero knows it, can afford it and has someone to aim it at
  useAbility(h, id, target) {
    if (!id) {
      const t = this.foeAt(target);
      if (!t) return false;
      if (CM.CLASSES[h.cls] && CM.CLASSES[h.cls].cast) this.say(`${h.name} is out of magic, and swings instead.`);
      this.strike(h, t);
      return true;
    }
    const a = CM.ABILITIES[id];
    if (!a || !CM.abilitiesFor(h).includes(id)) { this.say(`${h.name} doesn't know that.`); return false; }
    if (a.once && h.used && h.used[id]) { this.say(`${h.name} has used ${a.name} this fight.`); return false; }
    const cost = a.mp && CM.trait(h, "thrifty") ? Math.max(1, a.mp - 1) : a.mp;
    if (h.mp < cost) { this.say(`${h.name} hasn't the magic for ${a.name}.`); return false; }
    if (this.mode !== "combat" && !a.outside) { this.say(`${a.name} is for a fight.`); return false; }
    const foes = this.living();
    let foe = null, ally = null;
    if (a.target === "foe") { foe = this.foeAt(target); if (!foe) return false; }
    if (a.target === "foes" && !foes.length) return false;
    if (a.target === "ally") {
      ally = this.allyAt(target, false);
      if (id === "lay" && CM.trait(h, "lastrites") && !(h.used && h.used.lastrites)) {   // (Last Rites: a fallen hero may be the one)
        const fallen = this.allyAt(target, true);
        if (fallen && (typeof target === "number" ? this.party[target] === fallen : !ally)) ally = fallen;
      }
      if (!ally) { this.say("No one to cast that on."); return false; }
    }
    if (a.target === "fallen") { ally = this.allyAt(target, true); if (!ally) { this.say("No one has fallen."); return false; } }
    h.mp -= cost;
    if (a.once) { h.used = h.used || {}; h.used[id] = true; }
    this.sound(a.mp ? "spell" : "hit");
    this.emit("fx", { kind: "cast", id, hero: h, foe, ally, foes });
    this.casting = h;
    this.doAbility(h, id, a, foe, ally, foes);
    this.casting = null;
    this.emit("change");
    return true;
  }

  doAbility(h, id, a, foe, ally, foes) {
    const rnd = this.rnd, L = h.level, mod = this.spellMod(h), c = this.combat || {};
    const healAll = (n, text) => { for (const p of this.alive()) p.hp = Math.min(p.max, p.hp + n); this.say(text); this.sound("heal"); };
    switch (id) {
      case "missile": this.spellHit(foe, Math.max(1, 6 + 2 * L + mod), `${h.name}'s bolt of force strikes:`); break;
      case "firebolt": this.spellHit(foe, Math.max(1, 10 + 3 * L + mod), `${h.name}'s fire bolt:`, "fire"); break;
      case "lightning": this.spellHit(foe, Math.max(1, 20 + 5 * L + mod), `${h.name} calls down lightning!`); if (CM.trait(h, "tempest") && foe.hp > 0 && !CM.unmoved(foe) && rnd.chance(0.5)) { foe.held = Math.max(foe.held || 0, 1); this.say(`${CM.The(foe)} reels, smoking.`); } break;
      case "calllightning": {
        const dmg = Math.max(1, 18 + 4 * L + mod), struck = CM.trait(h, "stormcall") ? foes : [foe];
        for (const m of struck) { this.spellHit(m, m === foe ? dmg : Math.ceil(dmg * 0.6), m === foe ? `${h.name} calls down lightning!` : "The storm reaches on:"); if (CM.trait(h, "tempest") && m.hp > 0 && !CM.unmoved(m) && rnd.chance(0.5)) { m.held = Math.max(m.held || 0, 1); this.say(`${CM.The(m)} reels, smoking.`); } }
        break;
      }
      case "smite": {
        const dmg = Math.max(1, 12 + 3 * L + Math.floor(mod / 2));
        if (CM.trait(h, "radiance") && foes.some((m) => m.undead)) { for (const m of foes) if (m.undead) this.spellHit(m, dmg * 2, `${h.name}'s radiance falls on the unholy:`, "holy"); }
        else this.spellHit(foe, dmg * (foe.undead ? 2 : 1), `${h.name} smites${foe.undead ? " the unholy thing" : ""}:`, "holy");
        break;
      }
      case "fireball": {
        const dmg = Math.max(1, 8 + 4 * L + mod);
        for (const m of foes) { this.spellHit(m, dmg, "", "fire"); if (CM.trait(h, "inferno") && m.hp > 0) { m.burning = 2; m.burnDmg = 5 + L; } }
        this.say(`${h.name} hurls a fireball! ${dmg} damage to every foe${CM.trait(h, "inferno") ? ", and they burn" : ""}.`);
        break;
      }
      case "frost": {
        const dmg = Math.max(1, 6 + 2 * L + mod);
        let held = 0;
        for (const m of foes) { this.spellHit(m, dmg, "", "frost"); if (m.hp > 0 && !CM.unmoved(m) && rnd.chance(0.3)) { m.held = Math.max(m.held || 0, 1); held++; } }
        this.say(`${h.name} breathes frost over every foe: ${dmg} each${held ? `, ${CM.plural(held, "foe")} frozen fast` : ""}.`);
        break;
      }
      case "sleep": case "lullaby": {
        let asleep = 0;
        for (const m of foes) if (!CM.unmoved(m) && ((id === "lullaby" && CM.trait(h, "lull")) || rnd.chance(0.5 + mod * 0.03))) { m.asleep = 3; asleep++; }
        this.say(id === "sleep" ? `${h.name} weaves a sleep: ${asleep ? CM.plural(asleep, "foe") + " slump where they stand" : "none of them so much as yawns"}.`
          : `${h.name} sings a lullaby: ${asleep ? CM.plural(asleep, "foe") + " nod off" : "none of them so much as yawns"}.`);
        break;
      }
      case "blink": this.flee(true); break;
      case "light": this.spellLight = CM.LIGHT_STEPS; this.say(`${h.name} calls up a light. It will last ${CM.LIGHT_STEPS} steps.`); break;
      case "heal": case "mend": {
        let n = Math.max(1, (id === "heal" ? 12 + 4 * L : 10 + 3 * L) + mod);
        if (id === "heal" && CM.trait(h, "blessedhands")) n = Math.ceil(n * 1.5);
        ally.hp = Math.min(ally.max, ally.hp + n);
        this.sound("heal");
        this.say(`${h.name} ${id === "heal" ? "prays" : "lays on herbs and words"}: ${ally.name} is healed by ${n}.`);
        break;
      }
      case "lay": {
        if (ally.hp <= 0) {                                              // (Last Rites)
          h.used = h.used || {}; h.used.lastrites = true;
          ally.hp = Math.max(1, Math.floor(ally.max / 3));
          this.sound("heal");
          this.say(`${h.name} lays hands on ${ally.name}, and says the last rites backwards. ${ally.name} breathes.`);
          break;
        }
        let n = Math.max(1, 8 + 3 * L + Math.floor(mod / 2));
        const gentle = CM.trait(h, "gentlehands");
        if (gentle) n = Math.ceil(n * 1.5);
        ally.hp = Math.min(ally.max, ally.hp + n);
        const cured = this.cure(ally, gentle ? CM.CURABLE : ["poison"]);
        this.sound("heal");
        this.say(`${h.name} lays on hands: ${ally.name} mends by ${n}${cured.length ? `, and the ${cured.length > 1 ? "ailments leave" : CM.STATUSES[cured[0]].name.toLowerCase() + " leaves"} them` : ""}.`);
        break;
      }
      case "cure": {
        const cured = this.cure(ally, CM.CURABLE);
        this.sound("heal");
        this.say(cured.length ? `${h.name} prays over ${ally.name}: no longer ${cured.map((s) => CM.STATUSES[s].name.toLowerCase()).join(" or ")}.` : `${h.name} prays over ${ally.name}, who had nothing to cure.`);
        break;
      }
      case "lift": {
        let n = 0;
        for (const p of this.alive()) n += this.cure(p, ["curse", "blind", "sleep"]).length;
        this.sound("heal");
        this.say(n ? `${h.name} lifts what lay on the party: ${CM.plural(n, "ailment")} gone.` : `${h.name} prays, but nothing lay on the party.`);
        break;
      }
      case "rally": {
        let n = 0;
        for (const p of this.alive()) { p.hp = Math.min(p.max, p.hp + 6); n += this.cure(p, CM.CURABLE).length; }
        this.sound("heal");
        this.say(`${h.name} rallies the party: a little mended${n ? `, and ${CM.plural(n, "ailment")} shaken off` : ""}.`);
        break;
      }
      case "regrowth": healAll(Math.max(1, 6 + 2 * L + Math.floor(mod / 2)), `${h.name} calls green growth through the party: everyone mends.`); break;
      case "bless": c.bless = true; if (CM.trait(h, "consecrate")) c.protect = true; this.say(`${h.name} blesses the party: blows land harder and glance off, this fight${CM.trait(h, "consecrate") ? ", and every blow on the party does less" : ""}.`); break;
      case "protection": c.protect = true; this.say(`${h.name} prays for protection: every blow on the party does less, this fight.`); break;
      case "song": {
        this.song = CM.trait(h, "warsong") ? 2 : 1;
        this.songEpic = CM.trait(h, "epic") ? this.floor.number : 0;
        for (const p of this.alive()) { p.hp = Math.min(p.max, p.hp + 4); if ((p.status || {}).sleep) delete p.status.sleep; }
        this.sound("heal");
        this.say(`${h.name} sings. Hearts lift: the party hits harder this fight, and hurts a little less.`);
        break;
      }
      case "turn": {
        const dmg = Math.max(1, 10 + 4 * L + mod);
        let burned = 0, fled = 0;
        for (const m of foes) if (m.undead) { burned++; this.spellHit(m, dmg, "", "holy"); if (m.hp > 0 && !CM.unmoved(m) && rnd.chance(0.4)) { m.fled = true; fled++; this.emit("fx", { kind: "die", foe: m }); } }
        if (CM.trait(h, "purifier")) for (const m of foes) if (!m.undead && m.hp > 0) this.spellHit(m, Math.ceil(dmg / 2), "The light scorches:", "holy");
        this.say(burned ? `${h.name} raises the holy symbol: the undead burn (${dmg})${fled ? `, and ${CM.plural(fled, "one")} flee` : ""}.` : `${h.name} raises the holy symbol, but nothing here is undead.`);
        break;
      }
      case "sanctuary": {
        let held = 0;
        for (const m of foes) if (!CM.unmoved(m) && rnd.chance(0.5)) { m.held = Math.max(m.held || 0, 1); held++; }
        this.say(`${h.name} prays for sanctuary: ${held ? CM.plural(held, "foe") + " can't bring themselves to strike" : "the foes press on regardless"}.`);
        break;
      }
      case "raise": {
        ally.hp = CM.trait(h, "miracle") ? ally.max : Math.max(1, Math.floor(ally.max / 3));
        this.sound("heal");
        this.say(`${h.name} calls ${ally.name} back from the dark!`);
        break;
      }
      case "thorns": {
        const dmg = Math.max(1, 6 + 3 * L + Math.floor(mod / 2));
        let held = 0;
        for (const m of foes) { this.spellHit(m, dmg); if (m.hp > 0 && !CM.unmoved(m) && rnd.chance(0.3 + mod * 0.02)) { m.held = Math.max(m.held || 0, 1); held++; } }
        for (const p of this.alive()) p.hp = Math.min(p.max, p.hp + (3 + Math.floor(L / 2)) * (CM.trait(h, "deeproots") ? 3 : 1));
        this.say(`${h.name} calls thorns up through the stone: ${dmg} to every foe${held ? `, ${CM.plural(held, "foe")} held fast` : ""}; the party mends a little.`);
        break;
      }
      case "entangle": if (CM.unmoved(foe)) { this.say(`${h.name} calls roots up round ${CM.the(foe)}, and they snap.`); break; } foe.held = Math.max(foe.held || 0, 2); this.say(`${h.name} calls roots round the ${foe.name}: held fast for two rounds.`); break;
      case "mockery": foe.marked = true; if (CM.trait(h, "jeer")) foe.blind = Math.max(foe.blind || 0, 2); this.say(`${h.name} mocks the ${foe.name}, who takes it badly: a quarter more from every blow${CM.trait(h, "jeer") ? ", and it can't see straight for rage" : ""}.`); break;
      case "mark": foe.marked = true; this.say(`${h.name} marks the ${foe.name}: a quarter more from every blow.`); break;
      case "volley": {
        const first = this.foeAt(foe || null);
        this.strike(h, first, " with an arrow");
        const rest = this.living().filter((m) => m !== first);
        if (rest.length) this.strike(h, rnd.pick(rest), " with a second arrow");
        else if (first.hp > 0) this.strike(h, first, " with a second arrow");
        if (CM.trait(h, "rainofarrows")) { const third = this.living()[0]; if (third) this.strike(h, third, " with a third arrow"); }
        break;
      }
      case "aimed": this.strike(h, foe, " with an aimed arrow", { sure: true, mult: 1.5 }); break;
      case "guard": h.guarding = ally; ally.guardedBy = h; this.say(`${h.name} stands guard over ${ally.name}.`); break;
      case "taunt": c.taunter = h; c.tauntUntil = c.round + 1; this.say(`${h.name} roars a challenge: every foe turns their way!`); break;
      case "bash": if (this.strike(h, foe, " with the shield") > 0 && foe.hp > 0 && !CM.unmoved(foe) && rnd.chance(0.5)) { foe.held = Math.max(foe.held || 0, 1); this.say(`${CM.The(foe)} reels.`); } break;
      case "trick": foe.blind = 3; if (CM.trait(h, "sand") && !CM.unmoved(foe)) foe.held = Math.max(foe.held || 0, 1); this.say(`${h.name} flings sand in the ${foe.name}'s eyes!${CM.trait(h, "sand") && !CM.unmoved(foe) ? " It stands there clawing at them." : ""}`); break;
      default: break;
    }
  }

  // a potion, an antidote, a feather, in the thick of it: {row, who}, or the first healing potion for whoever needs it most
  useItemInBattle(h, arg) {
    if (arg && typeof arg === "object" && arg.row !== undefined) {
      const item = this.bag[arg.row];
      if (item && (item.kind === "scroll" || item.kind === "wand")) return this.useMagicInBattle(h, arg.row, arg.who);
      if (!item || !["heal", "mana", "antidote", "revive"].includes(item.kind)) { this.say("Not now."); return false; }
      const who = arg.who !== undefined ? arg.who : this.party.indexOf(this.allyAt(null, item.kind === "revive"));
      if (who < 0) return false;
      const note = this.give(arg.row, who);
      if (note) { this.say(note); return false; }
      this.emit("fx", { kind: "potion", who, item: item.kind });
      return true;
    }
    return this.potionInBattle();
  }

  potionInBattle() {
    const potion = this.bag.find((i) => i.kind === "heal");
    if (!potion) { this.say("No healing potions left!"); return false; }
    const target = this.alive().reduce((a, b) => (a.hp / a.max <= b.hp / b.max ? a : b));
    this.bag.splice(this.bag.indexOf(potion), 1);
    target.hp = Math.min(target.max, target.hp + potion.power);
    this.sound("heal");
    this.emit("fx", { kind: "potion", who: this.party.indexOf(target), item: "heal" });
    this.say(`${target.name} drinks a Healing Potion (+${potion.power}).`);
    return true;
  }

  // between fights: a healing spell, a cure, Light - from whoever knows it
  castOutside(heroIndex, id, target) {
    const h = this.party[heroIndex];
    if (!h || h.hp <= 0 || !this.canAct(h) || this.mode === "combat") return false;
    const ok = this.useAbility(h, id, target);
    if (ok) this.saveRun();
    return ok;
  }

  wonFight() {
    const rnd = this.rnd;
    const slain = this.foes.filter((m) => !m.fled);
    this.count("kills", slain.length);
    const xp = slain.reduce((s, m) => s + m.xp, 0);
    let gold = slain.reduce((s, m) => s + m.gold, 0);
    if (this.alive().some((h) => (h.boons || []).includes("scavenger"))) gold = Math.floor(gold * 1.25);
    gold = Math.floor(gold * (CM.DIFFICULTIES[this.difficulty] || CM.DIFFICULTIES.fair).gold);
    this.gold += gold;
    if (this.gold >= 2000) this.achieve("hoarder");
    if (slain.some((m) => m.name === "Minotaur of the Labyrinth")) this.achieve("labyrinth");
    const loot = rnd.chance(0.45) ? [CM.makeItem(this.floor.number, rnd)] : [];
    this.bag.push(...loot);
    const boss = this.foes.some((m) => m.boss), guardian = this.foes.find((m) => m.guardian), fought = this.floor.things[this.foeKey];
    if (fought && fought.vengeance) { this.floor.avenged = (this.floor.avenged || []).concat(fought.vengeance); this.say("Somewhere on this floor, something lets out a long breath it has held a long time."); }
    delete this.floor.things[this.foeKey];
    if (guardian) this.floor.things[this.foeKey] = { type: "ladder" };   // (the shaft it stood over)
    this.combat = null;
    this.sound("coin");
    this.say(`Victory! ${xp} experience and ${gold} gold` + (loot.length ? `, and a ${loot[0].name}.` : "."));
    for (const hero of this.alive()) {
      hero.xp += Math.floor(xp / 2);                                      // everyone standing learns from the fight
      while (hero.xp >= CM.xpForLevel(hero.level + 1)) {
        hero.level += 1;
        CM.upgradeHero(hero);
        CM.recompute(hero);
        hero.hp = hero.max;
        hero.mp = hero.maxmp;
        hero.pending += 1;
        this.sound("level");
        this.emit("fx", { kind: "levelup", hero });
        this.say(`${hero.name} reaches level ${hero.level}! A boon is theirs to choose (press ${this.party.indexOf(hero) + 1}).`);
      }
    }
    if (guardian) {
      this.slayGuardian(guardian);
      if (!this.fightFell) this.achieve("untouched");
      if (CM.GUARDIANS[guardian.guardian].final) { this.bottom = true; this.endRun(true); return; }
    }
    if (boss) { this.crown(); return; }
    this.setMode("explore");
    this.saveRun();
  }

  // ---- the bag, the merchant, the camp ----
  openBag(shop = false) {
    this.shopping = shop;
    if (shop && !this.stock) {
      const rnd = this.rnd, depth = this.floor.number + 3;
      this.stock = ["weapon", "weapon", "weapon", "armor", "armor", "armor", "shield", "helm"].map((k) => { const it = CM.makeItem(depth, rnd, k); it.unknown = false; return it; });
      this.stock.push({ name: "Healing Potion", kind: "heal", power: 20 + depth * 3, value: 20 },
        { name: "Mana Potion", kind: "mana", power: 12 + depth, value: 25 },
        { name: "Phoenix Feather", kind: "revive", power: 0, value: 120 }, CM.antidote(), CM.torch(), CM.lantern(), CM.scroll("identify"), CM.scroll("mapping"), CM.rope());
    }
    this.emit("bag", true);
  }

  closeBag() {
    this.emit("bag", false);
    this.saveRun();
    this.emit("change");
  }

  describe(item) {
    const plain = { heal: "heals", mana: "restores magic", revive: "raises the fallen", torch: "light, for a while", lantern: "light that lasts",
      key: "opens a locked door", antidote: "cures poison, sleep, paralysis and blindness", rope: "down a pit without the fall, and back up again",
      bones: "someone's, gathered up for a ghost who asked" }[item.kind];
    return plain || CM.itemLabel(item);
  }

  // what the hero wears in that slot goes back to the pack - unless a curse holds it
  takeOff(n, slot) {
    const hero = this.party[n], item = hero && hero[slot];
    if (!item) return "Nothing there.";
    if (slot === "weapon" || slot === "armor") return "Swap it for another instead: no one goes bare-handed down here.";
    if (item.props && item.props.cursed) return `${item.name} is cursed: it won't come off. The camp's temple can lift it.`;
    hero[slot] = null;
    this.bag.push(item);
    CM.recompute(hero);
    this.sound("chest");
    this.emit("change");
    return "";
  }

  // an unknown thing is known: its name, its bonus, its properties
  reveal(item) {
    if (!item.unknown) return false;
    item.unknown = false;
    return true;
  }

  identify(row) {
    const item = this.bag[row];
    if (!this.identifying || !item) return "Pick a thing from the pack.";
    if (!item.unknown) return "That one is known already. Pick an unknown thing.";
    const scroll = this.bag.findIndex((i) => i.kind === "scroll" && i.spell === "identify");
    if (scroll < 0) { this.identifying = false; return "The scroll is gone."; }
    this.reveal(item);
    this.bag.splice(scroll, 1);
    this.identifying = false;
    this.sound("spell");
    this.say(`The scroll crumbles: it's ${item.name} (${CM.itemLabel(item)}).`);
    this.emit("change");
    return "";
  }

  // a scroll read or a wand waved, between fights; "" when it worked, else why not
  useMagicOutside(row, n) {
    const item = this.bag[row], hero = this.party[n], fl = this.floor;
    const spec = item.kind === "scroll" ? CM.SCROLLS[item.spell] : CM.WANDS[item.spell];
    if (!spec.outside) return `${item.name} is for a fight.`;
    if (item.spell === "identify") {
      if (!this.bag.some((i) => i.unknown)) return "Nothing in the pack is unknown.";
      this.identifying = true;
      return "Now pick the unknown thing in the pack to identify.";
    }
    if (item.spell === "mapping") {
      fl.seen = [];
      for (let y = 0; y < fl.grid.length; y++) for (let x = 0; x < fl.grid.length; x++) fl.seen.push([x, y]);
      for (const f of Object.values(fl.features)) if ("known" in f) f.known = true;
      this.say("The scroll crumbles, and the whole floor is drawn on the automap.");
    } else if (item.spell === "teleport") {
      const open = [];
      for (let y = 0; y < fl.grid.length; y++) for (let x = 0; x < fl.grid.length; x++) {
        const k = keyOf(x, y), f = fl.features[k];
        if (CM.passable(fl, x, y) && !fl.things[k] && !(f && ["pit", "trapdoor", "teleporter", "spinner"].includes(f.type))) open.push([x, y]);
      }
      if (!open.length) return "The scroll fizzles.";
      fl.pos = this.rnd.pick(open);
      this.look();
      this.emit("teleported", fl.pos[0], fl.pos[1]);
      this.say("The scroll crumbles - and the party is somewhere else on this floor.");
    } else if (item.spell === "healing") {
      if (!hero || hero.hp <= 0) return "Not on the fallen.";
      const n2 = 15 + 3 * (this.floor ? Math.floor(this.floor.number / 2) : 1);
      hero.hp = Math.min(hero.max, hero.hp + n2);
      this.say(`${hero.name} is mended by the wand (+${n2}).`);
    }
    this.sound("spell");
    if (item.kind === "scroll") this.bag.splice(row, 1);
    else { item.charges -= 1; if (item.charges <= 0) { this.bag.splice(row, 1); this.say(`The ${item.name} is spent, and crumbles.`); } }
    this.saveRun();
    this.emit("change");
    return "";
  }

  // a scroll or wand in the thick of it
  useMagicInBattle(h, row, who) {
    const item = this.bag[row], foes = this.living(), L = this.floor ? this.floor.number : 1;
    const spec = item.kind === "scroll" ? CM.SCROLLS[item.spell] : CM.WANDS[item.spell];
    if (spec.outside && item.spell !== "healing") { this.say(`${item.name} is for between fights.`); return false; }
    if (item.kind === "wand" && item.spell === "fire" && !this.foeAt(who)) { this.say("Nothing left to aim at."); return false; }
    this.sound("spell");
    this.emit("fx", { kind: "cast", id: item.spell, hero: h, item: item.kind, foes, foe: item.kind === "wand" && item.spell === "fire" ? this.foeAt(who) : null,
      ally: item.spell === "healing" ? this.allyAt(who, false) : null });
    if (item.spell === "fire") {
      if (item.kind === "wand") { const t = this.foeAt(who); if (!t) { this.say("Nothing left to aim at."); return false; } this.spellHit(t, 10 + 2 * L, `${h.name}'s wand spits fire:`, "fire"); }
      else { const dmg = 10 + 2 * L; for (const m of foes) this.spellHit(m, dmg, "", "fire"); this.say(`${h.name} reads the scroll: fire on every foe, ${dmg} each.`); }
    } else if (item.spell === "frost") {
      const dmg = 6 + 2 * L;
      let held = 0;
      for (const m of foes) { this.spellHit(m, dmg, "", "frost"); if (m.hp > 0 && !CM.unmoved(m) && this.rnd.chance(0.3)) { m.held = Math.max(m.held || 0, 1); held++; } }
      this.say(`${h.name} ${item.kind === "wand" ? "waves the wand" : "reads the scroll"}: cold on every foe, ${dmg} each${held ? `, ${CM.plural(held, "foe")} frozen fast` : ""}.`);
    } else if (item.spell === "sleep") {
      let asleep = 0;
      for (const m of foes) if (!CM.unmoved(m) && this.rnd.chance(0.5)) { m.asleep = 3; asleep++; }
      this.say(`${h.name} waves the wand: ${asleep ? CM.plural(asleep, "foe") + " slump where they stand" : "none of them so much as yawns"}.`);
    } else if (item.spell === "protection") {
      if (this.combat) this.combat.protect = true;
      this.say(`${h.name} reads the scroll: every blow on the party does less, this fight.`);
    } else if (item.spell === "healing") {
      const ally = this.allyAt(who, false);
      if (!ally) return false;
      const n2 = 15 + 3 * Math.floor(L / 2);
      ally.hp = Math.min(ally.max, ally.hp + n2);
      this.say(`${h.name} touches ${ally.name} with the wand: +${n2}.`);
    } else return false;
    if (item.kind === "scroll") this.bag.splice(row, 1);
    else { item.charges -= 1; if (item.charges <= 0) { this.bag.splice(row, 1); this.say(`The ${item.name} is spent, and crumbles.`); } }
    this.emit("change");
    return true;
  }

  // what the party wears: the thing in the slot goes back to the pack; wearing an unknown thing is how you learn it
  equip(hero, row) {
    const item = this.bag[row];
    const why = CM.cantWear(hero, item);
    if (why) return why;
    const slot = item.slot || (item.kind === "shield" ? "offhand" : item.kind);
    const old = hero[slot];
    if (old && old.props && old.props.cursed) return `${hero.name}'s ${old.name} is cursed and won't come off. The camp's temple can lift it.`;
    hero[slot] = item;
    this.bag.splice(row, 1);
    if (old) this.bag.push(old);
    if (slot === "weapon" && item.props && item.props.twohanded && hero.offhand) {
      if (hero.offhand.props && hero.offhand.props.cursed) { hero[slot] = old; this.bag.splice(row, 0, item); if (old) this.bag.pop(); return `${hero.name}'s shield is cursed to the arm: no room for a two-handed weapon.`; }
      this.bag.push(hero.offhand);
      this.say(`${hero.name} slings the shield: the ${CM.baseName(item)} takes both hands.`);
      hero.offhand = null;
    }
    const learned = this.reveal(item);
    const ratio = hero.hp / hero.max;
    CM.recompute(hero);
    hero.hp = Math.max(1, Math.round(hero.max * ratio));
    this.sound("chest");
    if (item.props && item.props.cursed) this.say(`${hero.name} takes up the ${CM.baseName(item)} - and it clings! It's cursed.`);
    else if (learned) this.say(`${hero.name} tries the ${CM.baseName(item)}: it's ${item.name} (${CM.itemLabel(item)}).`);
    this.emit("change");
    return "";
  }

  give(row, n) {                                                        // returns a note for the bag screen, "" when it worked
    if (row < 0 || row >= this.bag.length) return "Pick something from your pack first.";
    const item = this.bag[row], hero = this.party[n];
    if (item.kind === "key") return "Keys turn in locks, not in hands. Walk into the locked door.";
    if (item.kind === "rope") return "The rope is for a pit: walk into one with it in the pack.";
    if (item.kind === "tome") return this.readTome(row, hero);
    if (item.kind === "gem") return "A gem is for the camp's smith: he sets it into gear, for gold.";
    if (item.kind === "bones") return "They're not yours to use. Someone on this floor wants them back.";
    if (item.kind === "scroll" || item.kind === "wand") return this.useMagicOutside(row, n);
    if (item.kind === "torch") {
      this.bag.splice(row, 1);
      this.light = { kind: "torch", left: CM.TORCH_STEPS };
      this.sound("spell");
      this.say(`${hero.name} lights a fresh torch.`);
      this.emit("change");
      return "";
    }
    if (item.kind === "lantern") {
      this.bag.splice(row, 1);
      this.light = { kind: "lantern", left: 0 };
      this.sound("spell");
      this.say(`${hero.name} lights the lantern. It won't run out.`);
      this.emit("change");
      return "";
    }
    if (item.kind === "antidote") {
      if (hero.hp <= 0) return `${hero.name} has fallen. Raise them first.`;
      const cured = this.cure(hero, CM.CURABLE);
      if (!cured.length) return `${hero.name} has nothing an antidote would cure.`;
      this.bag.splice(row, 1);
      this.sound("heal");
      this.say(`${hero.name} drinks the antidote, and is no longer ${cured.map((s) => CM.STATUSES[s].name.toLowerCase()).join(" or ")}.`);
      this.emit("change");
      return "";
    }
    if (item.kind === "revive") {
      if (hero.hp > 0) return "The Phoenix Feather is for the fallen.";
      hero.hp = Math.floor(hero.max / 2);
      this.bag.splice(row, 1);
      this.sound("heal");
    } else if (hero.hp <= 0) {
      return `${hero.name} has fallen. Raise them first.`;
    } else if (item.kind === "heal") {
      hero.hp = Math.min(hero.max, hero.hp + item.power);
      this.bag.splice(row, 1);
      this.sound("heal");
    } else if (item.kind === "mana") {
      if (!hero.maxmp) return `${hero.name} has no magic to restore.`;
      hero.mp = Math.min(hero.maxmp, hero.mp + item.power);
      this.bag.splice(row, 1);
      this.sound("heal");
    } else {
      return this.equip(hero, row);
    }
    this.emit("change");
    return "";
  }

  buy(row) {
    if (!this.stock || row < 0 || row >= this.stock.length) return "Pick something from the merchant's wares first.";
    const item = this.stock[row];
    if (this.gold < item.value) return "You can't afford that.";
    this.gold -= item.value;
    this.bag.push(Object.assign({}, item, item.props ? { props: Object.assign({}, item.props) } : {}));
    if (["weapon", "armor", "shield", "helm", "lantern"].includes(item.kind)) this.stock.splice(row, 1);
    this.sound("coin");
    this.emit("change");
    return "";
  }

  sell(row) {
    if (row < 0 || row >= this.bag.length) return "Pick something from your pack to sell.";
    const item = this.bag.splice(row, 1)[0];
    this.gold += item.unknown ? 10 : Math.floor(item.value / 2);       // (the merchant pays a pittance for what no one can name)
    this.sound("coin");
    this.emit("change");
    return "";
  }

  rest() {
    if (this.gold < 20) { this.say("The merchant wants 20 gold for a bedroll by the fire."); return; }
    this.gold -= 20;
    for (const m of this.alive()) { m.hp = m.max; m.mp = m.maxmp; this.cure(m, CM.CURABLE); }
    this.sound("heal");
    this.say("The party rests by the fire. Wounds close, magic returns, and the small ailments pass.");
    this.saveRun();
  }

  // the camp's temple: ailments cured, a curse lifted (from the party, and from what they wear), stone made flesh - for a price
  temple(service) {
    const cost = { cure: 30, uncurse: 60, unstone: 150 }[service];
    const which = service === "cure" ? CM.CURABLE : service === "uncurse" ? ["curse"] : ["stone"];
    const cursedGear = service === "uncurse" ? this.party.flatMap((h) => CM.equipped(h).filter((it) => it.props && it.props.cursed)) : [];
    const who = this.party.filter((h) => which.some((s) => (h.status || {})[s]));
    if (!who.length && !cursedGear.length) {
      this.say({ cure: "No one here is ailing.", uncurse: "No curse lies on the party, nor on what they carry.", unstone: "No one here is stone." }[service]);
      return false;
    }
    if (this.gold < cost) { this.say(`The old priest asks ${cost} gold for that.`); return false; }
    this.gold -= cost;
    for (const h of who) this.cure(h, which);
    for (const it of cursedGear) { it.props.cursed = false; it.power += 3; }
    this.sound("heal");
    this.say({ cure: "Herbs and prayers: the party's ailments pass.",
      uncurse: "The priest's chant lifts the curse" + (cursedGear.length ? `, and ${cursedGear.map((i) => i.name).join(", ")} can be put down at last.` : "."),
      unstone: `Stone becomes flesh again: ${who.map((h) => h.name).join(", ")} can move.` }[service]);
    this.saveRun();
    return true;
  }

  // the priest's scribe names everything unknown in the pack and on the party's backs
  scribe() {
    const unknown = [...this.bag, ...this.party.flatMap(CM.equipped)].filter((i) => i.unknown);
    if (!unknown.length) { this.say("Nothing you carry is unknown to you."); return false; }
    if (this.gold < 25) { this.say("The scribe asks 25 gold to name what you carry."); return false; }
    this.gold -= 25;
    for (const it of unknown) this.reveal(it);
    this.sound("spell");
    this.say(`The scribe squints and names them: ${unknown.map((i) => i.name).join(", ")}.`);
    this.saveRun();
    return true;
  }

  // the tavern: three who'd come along, for a price - one of them for a hero who has fallen
  tavern() {
    if (!this.recruits || this.recruits.floor !== this.floor.number) {
      const level = Math.max(1, Math.round(this.party.reduce((s, h) => s + h.level, 0) / Math.max(1, this.party.length)) - 1);
      const rnd = new CM.Random(CM.hashSeed(`${this.seed}:tavern:${this.floor.number}`));
      this.recruits = { floor: this.floor.number, who: [0, 1, 2].map(() => CM.makeRecruit(level, rnd)) };
    }
    return (this.rescued || []).length ? this.rescued.concat(this.recruits.who) : this.recruits.who;   // (the rescued first, and free)
  }

  hire(i, replace) {
    const recruit = this.tavern()[i];
    if (!recruit) return "No one by that name.";
    const fallen = this.party.map((h, idx) => idx).filter((idx) => this.party[idx].hp <= 0 || (this.party[idx].status || {}).stone);
    if (!fallen.length) return "The party is whole. The recruits drink to that.";
    const idx = replace === undefined ? fallen[0] : replace;
    if (!fallen.includes(idx)) return `${this.party[idx].name} is still standing.`;
    if (this.gold < recruit.price) return `${recruit.name} wants ${recruit.price} gold to come along.`;
    this.gold -= recruit.price;
    const rescued = (this.rescued || []).length;
    const gone = this.party[idx];
    for (const slot of CM.SLOTS) if (gone[slot] && !(slot === "weapon" || slot === "armor")) this.bag.push(gone[slot]);   // (their trinkets stay with the party)
    const h = Object.assign({}, recruit);
    delete h.price;
    this.party[idx] = h;
    if (i < rescued) this.rescued.splice(i, 1); else this.recruits.who.splice(i - rescued, 1);
    this.sound("coin");
    this.say(`${gone.name} is laid to rest by the fire. ${h.name} the ${h.cls} takes up their place${recruit.price ? "" : ", owing you their life"}.`);
    this.saveRun();
    this.emit("change");
    return "";
  }


  // ---- the journal, and the dungeon's people ----
  // everything read and heard goes in the journal (once), to be read again with J, and to pay the hermit with
  remember(kind, text, extra = {}) {
    this.journal = this.journal || [];
    if (this.journal.some((e) => e.text === text)) return false;
    this.journal.push(Object.assign({ kind, text, floor: this.floor ? this.floor.number : 0 }, extra));
    this.emit("journal");
    if (this.journal.length >= 10) this.achieve("scholar");
    return true;
  }
  hasItem(kind) { return this.bag.findIndex((i) => i.kind === kind); }

  // someone to talk to, where the party stands (Space)
  talk(thing, k) {
    if (thing.type === "ghost") this.talkGhost(thing, k);
    else if (thing.type === "hermit") this.talkHermit(thing);
    else if (thing.type === "adventurer") this.freeAdventurer(thing, k);
  }

  talkGhost(thing, k) {
    const fl = this.floor, G = CM.GHOSTS[thing.who] || CM.GHOSTS[0], R = CM.REQUESTS[thing.request] || CM.REQUESTS.story;
    const done = thing.request === "bones" ? this.hasItem("bones") >= 0
      : thing.request === "vengeance" ? Boolean(fl.avenged && fl.avenged.includes(k))
      : Object.values(fl.features).some((f) => f.type === "carving" && f.read && !(typeof f.text === "string"));
    if (!thing.asked) {
      thing.asked = true;
      this.sound("ailment");
      this.emit("talk", { title: G.name, text: `A pale shape waits in the air, not quite a man or a woman any more. "I was ${G.name}," it says. "${R.ask}"` });
      this.saveRun();
      return;
    }
    if (!done) { this.emit("talk", { title: G.name, text: `"${R.wait}"` }); return; }
    if (thing.request === "bones") this.bag.splice(this.hasItem("bones"), 1);
    const rnd = new CM.Random(CM.hashSeed(`${this.seed}:ghost:${fl.number}`));
    const gift = CM.makeGear(rnd.pick(["ring", "amulet", "amulet"]), fl.number + 4, rnd);
    gift.unknown = false;
    this.bag.push(gift);
    const xp = 30 * fl.number;
    for (const h of this.alive()) h.xp += xp;
    delete fl.things[k];
    this.remember("ghost", G.tale, { who: G.name });
    this.achieve("restful");
    this.sound("heal");
    this.say(`${G.name} is at rest. ${gift.name} (${CM.itemLabel(gift)}) and ${xp} experience each.`);
    this.emit("fx", { kind: "sparkle", at: k.split(",").map(Number) });
    this.emit("talk", { title: G.name, text: `${R.done} ${G.tale}` });
    this.checkLevels();
    this.saveRun();
    this.emit("change");
  }

  talkHermit(thing) {
    const untold = (this.journal || []).length - (thing.heard || 0);
    if (!thing.greeted) { thing.greeted = true; this.emit("talk", { title: "The hermit", text: CM.HERMIT.greet }); this.saveRun(); return; }
    if (untold <= 0) { this.emit("talk", { title: "The hermit", text: CM.HERMIT.noStory }); return; }
    const row = this.bag.findIndex((i) => i.unknown);
    thing.heard = (thing.heard || 0) + 1;
    if (row >= 0) {
      const item = this.bag[row];
      this.reveal(item);
      this.sound("spell");
      this.say(`The hermit names it: ${item.name} (${CM.itemLabel(item)}).`);
      this.emit("talk", { title: "The hermit", text: `${CM.HERMIT.told[(thing.heard - 1) % CM.HERMIT.told.length]} "${item.name}. ${CM.itemLabel(item)}."` });
    } else {
      const goal = CM.goalOf(this.floor), where = goal ? this.directionTo(goal.split(",").map(Number)) : "nowhere you can get to";
      this.emit("talk", { title: "The hermit", text: `${CM.HERMIT.nothing} "The way down lies ${where}."` });
    }
    this.saveRun();
    this.emit("change");
  }

  directionTo([x, y]) {
    const [px, py] = this.floor.pos, dx = x - px, dy = y - py;
    if (!dx && !dy) return "under your feet";
    const ns = dy < -Math.abs(dx) / 2 ? "north" : dy > Math.abs(dx) / 2 ? "south" : "", ew = dx > Math.abs(dy) / 2 ? "east" : dx < -Math.abs(dy) / 2 ? "west" : "";
    return `to the ${ns}${ns && ew ? "-" : ""}${ew}, ${Math.abs(dx) + Math.abs(dy)} paces or so`;
  }

  // the lost adventurer: cut loose, they take a fallen hero's place - or go on up to the camp, leaving a rope and their map
  freeAdventurer(thing, k) {
    const fl = this.floor, h = Object.assign({}, thing.hero);
    if (!thing.freed) { thing.freed = true; this.emit("talk", { title: h.name + " the " + h.cls, text: CM.ADVENTURER.found }); this.saveRun(); return; }
    const fallen = this.party.findIndex((p) => p.hp <= 0 || (p.status || {}).stone);
    delete fl.things[k];
    this.sound("unlock");
    this.achieve("friend");
    if (fallen >= 0) {
      const gone = this.party[fallen];
      for (const slot of CM.SLOTS) if (gone[slot] && !(slot === "weapon" || slot === "armor")) this.bag.push(gone[slot]);
      delete h.price;
      h.hp = Math.max(1, Math.floor(h.max / 2));
      this.party[fallen] = h;
      this.say(CM.ADVENTURER.joins(h.name, h.cls, gone.name));
    } else {
      this.bag.push(CM.rope());
      fl.seen = [];
      for (let y = 0; y < fl.grid.length; y++) for (let x = 0; x < fl.grid.length; x++) fl.seen.push([x, y]);
      for (const f of Object.values(fl.features)) if ("known" in f) f.known = true;
      h.price = 0;
      this.rescued = (this.rescued || []).concat(h);
      this.say(CM.ADVENTURER.leaves(h.name));
    }
    this.saveRun();
    this.emit("change");
  }

  // a riddle door, walked into: the window asks; a right answer opens it, a wrong one burns
  answerRiddle(k, answer) {
    const f = this.floor.features[k], r = f && CM.RIDDLES[f.riddle];
    if (!r || f.open) return false;
    if (answer === r.a) {
      f.open = true;
      f.locked = false;
      this.sound("unlock");
      const xp = 15 * this.floor.number;
      for (const h of this.alive()) h.xp += xp;
      this.say(`The runes fade, and the door swings open. (${xp} experience each.)`);
      this.remember("riddle", `A door on floor ${this.floor.number} asked: ${r.q} The answer was: ${r.a.toLowerCase()}.`);
      this.checkLevels();
      this.dirty = true;
      this.emit("change");
      return true;
    }
    f.tries = (f.tries || 0) + 1;
    const burn = 2 + Math.floor(this.floor.number / 2);
    for (const h of this.alive()) h.hp = Math.max(1, h.hp - burn);
    this.sound("trap");
    this.emit("fx", { kind: "trap", trap: "blade" });
    this.say(`The runes flare white, and the heat of them sears everyone (-${burn}). The door stays shut.`);
    this.emit("change");
    return false;
  }

  // the levels a gift of experience may bring (a fight's are handled as it ends)
  checkLevels() {
    for (const hero of this.alive()) {
      while (hero.xp >= CM.xpForLevel(hero.level + 1)) {
        hero.level += 1;
        CM.upgradeHero(hero);
        CM.recompute(hero);
        hero.pending += 1;
        this.sound("level");
        this.emit("fx", { kind: "levelup", hero });
        this.say(`${hero.name} reaches level ${hero.level}! A boon is theirs to choose (press ${this.party.indexOf(hero) + 1}).`);
      }
    }
  }

  // down a pit on a rope: no fall, and the rope stays tied to climb back by
  ropeDown(k) {
    const fl = this.floor, [x, y] = k.split(",").map(Number), n = fl.number;
    this.sound("stairs");
    this.enterFloor(n + 1, "fall", [x, y]);
    const below = this.floor;
    below.things[keyOf(below.pos[0], below.pos[1])] = { type: "rope", up: [x, y] };
    this.say("The rope hangs down beside you: a way back up.");
    this.saveRun();
  }


  // ---- growth and craft: a path chosen, a tome read, the smith's work, the vault ----
  choosePath(hero, id) {
    if (!CM.needsPath(hero) || !CM.PATHS[hero.cls][id]) return false;
    hero.path = id;
    const ratio = hero.hp / hero.max, mratio = hero.maxmp ? hero.mp / hero.maxmp : 0;
    CM.recompute(hero);
    hero.hp = Math.max(1, Math.round(hero.max * ratio));
    hero.mp = Math.round(hero.maxmp * mratio);
    const P = CM.PATHS[hero.cls][id];
    this.sound("level");
    this.say(`${hero.name} takes the ${P.name}'s path: ${P.t1.name} - ${P.t1.what.charAt(0).toLowerCase() + P.t1.what.slice(1)}. (${P.t2.name} at level ${CM.PATH_AT[1]}.)`);
    this.saveRun();
    this.emit("change");
    return true;
  }

  readTome(row, hero) {                                                 // "" when learned, else why not
    const item = this.bag[row], id = item.spell;
    if (!CM.isCaster(hero)) return `${hero.name} turns the pages and can't make head or tail of them: a tome is for a caster.`;
    if (CM.abilitiesFor(hero).includes(id)) return `${hero.name} knows ${CM.ABILITIES[id].name} already.`;
    hero.learned = (hero.learned || []).concat(id);
    this.bag.splice(row, 1);
    this.sound("spell");
    this.say(`${hero.name} reads the ${item.name}, and the words stay: ${CM.ABILITIES[id].name} is theirs now.`);
    this.emit("fx", { kind: "levelup", hero });
    this.saveRun();
    this.emit("change");
    return "";
  }

  // the camp's smith: a diamond and gold put +1 on a piece of gear (up to +3 of his work); a ruby, sapphire or sunstone
  // and gold put fire, frost or holiness into a weapon. "" when it worked, else why not.
  smith(service, heroIndex, slot) {
    if (this.mode !== "camp") return "The smith works at the camp.";
    const hero = this.party[heroIndex], item = hero && hero[slot];
    if (!item || !["weapon", "armor", "offhand", "helm"].includes(slot)) return "Pick a weapon, armour, a shield or a helm.";
    if (item.unknown) return "The smith won't work on a thing nobody can name. Have it identified first.";
    const p = item.props = item.props || {};
    if (service === "enchant") {
      const n = p.enchant || 0, cost = CM.SMITH.enchant * (n + 1), gem = this.bag.findIndex((i) => i.kind === "gem" && i.gem === "diamond");
      if (n >= CM.SMITH.most) return `${item.name} has had all the smith's work it can take.`;
      if (gem < 0) return "The smith wants a diamond for the work.";
      if (this.gold < cost) return `The smith wants ${cost} gold, and the diamond.`;
      this.gold -= cost;
      this.bag.splice(gem, 1);
      p.enchant = n + 1;
      p.bonus = (p.bonus || 0) + 1;
      item.power += 1;
      item.value += 60;
      item.name = `${p.element ? CM.ELEMENTS[p.element].prefix + " " : ""}${CM.baseName(item)} +${p.bonus}`;
      CM.recompute(hero);
      this.sound("lever");
      this.say(`The smith works ${hero.name}'s ${CM.baseName(item)} by the fire, and sets the diamond in it: ${item.name}.`);
      if (p.enchant >= CM.SMITH.most) this.achieve("smith");
    } else if (service === "gem") {
      if (slot !== "weapon") return "A gem of fire, frost or holiness goes into a weapon.";
      const gem = this.bag.findIndex((i) => i.kind === "gem" && CM.GEMS[i.gem].element);
      if (gem < 0) return "The smith wants a ruby, a sapphire or a sunstone for a weapon.";
      if (this.gold < CM.SMITH.gem) return `The smith wants ${CM.SMITH.gem} gold to set a gem.`;
      const el = CM.GEMS[this.bag[gem].gem].element, name = this.bag[gem].name;
      this.gold -= CM.SMITH.gem;
      this.bag.splice(gem, 1);
      p.element = el;
      item.value += 80;
      item.name = `${CM.ELEMENTS[el].prefix} ${CM.baseName(item)}${p.bonus ? ` +${p.bonus}` : ""}`;
      this.sound("lever");
      this.say(`The smith sets the ${name.toLowerCase()} into ${hero.name}'s blade, and it takes: ${item.name}.`);
    } else return "The smith doesn't do that.";
    this.saveRun();
    this.emit("change");
    return "";
  }

  // the vault: one thing left at the camp waits for the next party (saved between runs); what was there comes out
  leaveHeirloom(row) {
    if (this.mode !== "camp") return "The vault is at the camp.";
    const item = this.bag[row];
    if (!item) return "Pick something from your pack.";
    if (["key", "bones", "rope", "torch"].includes(item.kind)) return "The merchant won't keep that. Something worth the keeping.";
    const old = this.vault;
    this.bag.splice(row, 1);
    this.vault = item;
    CM.store.set("vault", item);
    if (old) this.bag.push(old);
    this.sound("chest");
    this.say(`The merchant locks ${item.name} in the vault for whoever comes after${old ? `, and hands back ${old.name}` : ""}.`);
    this.saveRun();
    this.emit("change");
    return "";
  }
  takeHeirloom() {
    if (this.mode !== "camp") return "The vault is at the camp.";
    if (!this.vault) return "The vault is empty.";
    const item = this.vault;
    this.vault = null;
    CM.store.remove("vault");
    this.bag.push(item);
    this.sound("chest");
    this.say(`The merchant unlocks the vault: ${item.name}, left by a party before you.`);
    this.saveRun();
    this.emit("change");
    return "";
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
  has(mutator) { return (this.mutators || []).includes(mutator); }
  // a monster made ready for this run: the difficulty's weight, and Brittle's
  tune(m) {
    if (!m || m.tuned) return m;
    const d = CM.DIFFICULTIES[this.difficulty] || CM.DIFFICULTIES.fair;
    let hp = d.hp, atk = d.atk;
    if (this.has("brittle")) { hp *= 0.5; atk *= 1.5; }
    m.max = Math.max(1, Math.round(m.max * hp));
    m.hp = Math.max(1, Math.round(m.hp * hp));
    m.atk = Math.max(1, Math.round(m.atk * atk));
    m.tuned = true;
    return m;
  }
  achieve(id) {
    const a = CM.ACHIEVEMENTS[id];
    if (!a || this.achievements[id]) return false;
    this.achievements[id] = { date: CM.today(), seed: this.seed, name: CM.playerName || "Adventurer" };
    CM.store.set("achievements", this.achievements);
    this.earned = (this.earned || []).concat(id);
    this.sound("level");
    this.say(`Achievement: ${a.name} - ${a.what.charAt(0).toLowerCase() + a.what.slice(1)}. ${CM.playerName || "The player"} may be called ${a.title}.`);
    this.emit("fx", { kind: "relic" });
    this.emit("achieved", id);
    return true;
  }

  // ---- a level earned is a boon chosen ----
  offerBoons(hero) {
    if (hero.offer && hero.offer.length === 3) return hero.offer;
    const have = hero.boons || [], c = CM.CLASSES[hero.cls] || CM.CLASSES.Knight;
    const own = Object.keys(CM.BOONS).find((id) => CM.BOONS[id].stat === c.key);       // the class's own stat is always on offer
    const pool = Object.keys(CM.BOONS).filter((id) => id !== own && (CM.BOONS[id].stat || !have.includes(id)));
    hero.offer = [own, ...this.rnd.shuffle(pool).slice(0, 2)];
    this.dirty = true;
    return hero.offer;
  }

  chooseBoon(hero, id) {
    if (!hero.pending || !(hero.offer || []).includes(id)) return false;
    const b = CM.BOONS[id];
    if (b.stat) hero.stats[b.stat] = Math.min(25, hero.stats[b.stat] + 2);
    else hero.boons.push(id);
    hero.pending -= 1;
    hero.offer = null;
    const ratio = hero.hp / hero.max, mratio = hero.maxmp ? hero.mp / hero.maxmp : 0;
    CM.recompute(hero);
    hero.hp = Math.max(1, Math.round(hero.max * ratio));
    hero.mp = Math.round(hero.maxmp * mratio);
    this.sound("level");
    this.say(`${hero.name} takes ${b.name}: ${b.what.charAt(0).toLowerCase() + b.what.slice(1)}.`);
    this.saveRun();
    this.emit("change");
    return true;
  }

  setRow(hero, row) {
    if (this.mode === "combat" || !["front", "back"].includes(row)) return false;
    hero.row = row;
    this.dirty = true;
    this.emit("change");
    return true;
  }

  raiseDead() {
    const fallen = this.party.filter((m) => m.hp <= 0);
    if (!fallen.length) { this.say("No one needs raising."); return; }
    const hero = fallen[0], cost = 100 * hero.level;
    if (this.gold < cost) { this.say(`The old priest asks ${cost} gold to raise the ${hero.cls}.`); return; }
    this.gold -= cost;
    hero.hp = hero.max;
    this.sound("heal");
    this.say(`For ${cost} gold, the priest raises the ${hero.cls}!`);
    this.saveRun();
  }

  leaveCamp() {
    this.stock = null;
    this.enterFloor(this.floor.number + 1, "down");
  }

  backUp() {                                                             // from the camp, back onto the floor above it
    this.stock = null;
    const ladder = this.cellOf(this.floor, "ladder");
    if (ladder) this.floor.pos = ladder.slice();
    this.setMode("explore");
    this.look();
    this.emit("floor", this.floor);
    this.saveRun();
    this.say(`Back up the shaft to floor ${this.floor.number}.`);
  }

  potionCount() { return this.bag.filter((i) => ["heal", "mana", "revive", "antidote"].includes(i.kind)).length; }
};
