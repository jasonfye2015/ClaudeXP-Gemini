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
    this.settings = Object.assign({ sound: true, volume: 0.6, smooth: true, fps: false }, CM.store.get("settings", {}));
    this.lastRun = CM.store.get("run", null);        // a run left part way, to continue
    this.dirty = false; this.sinceSave = 0; this.wander = 0;
  }

  // ---- events: change (redraw), message, mode, floor, moved, turned, fx, sound, mesh, teleported, fell, spin, lore ----
  on(event, fn) { (this.listeners[event] = this.listeners[event] || []).push(fn); return this; }
  emit(event, ...args) { for (const fn of this.listeners[event] || []) fn(...args); }

  say(text) {
    this.messages.push(text);
    if (this.messages.length > 60) this.messages = this.messages.slice(-60);
    this.emit("message", text);
    this.emit("change");
  }

  sound(name) { this.emit("sound", name); }

  setMode(mode) { this.mode = mode; this.emit("mode", mode); this.emit("change"); }

  saveSettings() { CM.store.set("settings", this.settings); }

  // ---- saving ----
  saveRun() {
    if (!["explore", "camp"].includes(this.mode)) return;
    const data = { party: this.party, bag: this.bag, gold: this.gold, floor: this.floor, floors: this.floors, light: this.light,
      mode: this.mode, seed: this.seed, saved: new Date().toISOString() };
    this.lastRun = data;
    CM.store.set("run", data);
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
    this.seed = d.seed || CM.randomSeed();
    this.messages = [];
    this.setMode(d.mode === "camp" ? "camp" : "explore");
    this.emit("floor", this.floor);
    this.say("You take up the expedition where you left it.");
    return true;
  }

  endRun(won) {
    const entry = { name: CM.playerName || "Adventurer", floor: this.floor.number, gold: this.gold, won, date: CM.today(), seed: this.seed };
    this.fame.push(entry);
    this.sortFame();
    CM.store.set("fame", this.fame);
    CM.store.remove("run");
    this.lastRun = null;
    this.sound(won ? "victory" : "death");
    this.titleNote = won ? "The Lich King is no more. The party returns as legends!"
      : `The party fell on floor ${this.floor.number}. Their story ends here.`;
    this.emit("over", won);
    this.setMode("title");
  }

  sortFame() {
    this.fame.sort((a, b) => (b.won ? 1 : 0) - (a.won ? 1 : 0) || b.floor - a.floor || b.gold - a.gold);
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
      CM.store.set("run", this.lastRun);
      took.push("run");
    }
    this.emit("change");
    return took;
  }

  exportText() {
    return JSON.stringify({ game: "Claude and Magic", version: CM.version, run: this.lastRun, fame: this.fame, settings: this.settings });
  }

  importText(text) {
    let data;
    try { data = JSON.parse(text); } catch (e) { return "That isn't a Claude and Magic save."; }
    if (!data || data.game !== "Claude and Magic") return "That isn't a Claude and Magic save.";
    if (data.run && data.run.floor && data.run.party) { this.lastRun = data.run; CM.store.set("run", data.run); }
    if (Array.isArray(data.fame)) { this.fame = data.fame; this.sortFame(); CM.store.set("fame", this.fame); }
    if (data.settings) { Object.assign(this.settings, data.settings); this.saveSettings(); }
    this.emit("change");
    return "";
  }

  // ---- starting, and the stairs between floors ----
  newGame(seed, chosen) {                                                // chosen: the party made on the creation screen, or none for the classic four
    this.seed = (seed || "").trim() || CM.randomSeed();
    this.party = CM.newParty(chosen);
    this.steps = 0;
    this.bag = CM.startingBag(this.seed);
    this.gold = 30;
    this.floors = {};
    this.light = { kind: "torch", left: CM.TORCH_STEPS };
    this.messages = [];
    this.titleNote = "";
    this.enterFloor(1, "down");
    this.say("Four adventurers climb down into the dark. Somewhere below, the Lich King stirs.");
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
    if (how === "down") {
      const top = this.cellOf(fl, "stairs_up");
      if (top) fl.pos = top.slice();
      else if (!fresh) fl.pos = fl.pos.slice();
      const open = CM.openNeighbours(fl, fl.pos[0], fl.pos[1]);
      if (open.length) fl.facing = CM.DIRS.indexOf(open[0]);
    } else if (how === "up") {
      const ladder = this.cellOf(fl, "ladder") || this.cellOf(fl, "boss");
      if (ladder) fl.pos = ladder.slice();
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
      if (f.locked) {
        const i = this.hasKey();
        if (i < 0) { this.sound("bump"); this.say("The door is locked. It needs a key."); return false; }
        this.bag.splice(i, 1);
        f.locked = false;
        this.say("The key turns, and the door swings open.");
      } else {
        this.say("The door creaks open.");
      }
      f.open = true;
      this.sound("chest");
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
    if (thing && (thing.type === "monsters" || thing.type === "boss")) {
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
      } else {
        this.say({ chest: "A chest sits here. (Space to open it)", ladder: "A ladder leads down into the dark. (Space to climb down)",
          stairs_up: "The stairs you came down. (Space to climb back up)" }[thing.type]);
      }
    }
    if (f) this.arrive(f, k);
    this.emit("change");
    return true;
  }

  // what a square does when the party steps onto it
  arrive(f, k) {
    const fl = this.floor;
    if (f.type === "pit" || f.type === "trapdoor") {
      if (f.type === "trapdoor") { f.known = true; this.say("The floor gives way beneath you!"); }
      else this.say("You step into the pit!");
      this.fall(k.split(",").map(Number));
    } else if (f.type === "teleporter") {
      f.known = true;
      const to = fl.features[keyOf(f.to[0], f.to[1])];
      if (to) to.known = true;
      fl.pos = f.to.slice();
      this.sound("spell");
      this.look();
      this.emit("teleported", fl.pos[0], fl.pos[1]);
      this.say("The runes flare - and the walls around you are different ones.");
    } else if (f.type === "spinner") {
      f.known = true;
      fl.facing = (fl.facing + this.rnd.int(1, 3)) % 4;
      this.look();
      this.emit("spin", fl.facing);
      this.say("The floor lurches and the world turns. Which way were you facing?");
    } else if (f.type === "fountain") {
      this.say(f.used ? "A dry fountain." : "A fountain, running. (Space to drink)");
    } else if (f.type === "altar") {
      this.say(f.used ? "A quiet altar." : "An altar, with candles still lit. (Space to kneel)");
    }
  }

  fall(from) {
    const n = this.floor.number;
    for (const m of this.alive()) m.hp = Math.max(1, m.hp - Math.max(1, Math.floor(m.max / 10)));
    this.sound("hurt");
    this.emit("fell");
    if (n >= CM.LAST_FLOOR) { this.say("You fall into blackness... and land, bruised, on the stone below."); return; }
    this.say(`You fall to floor ${n + 1}, bruised but alive.`);
    this.enterFloor(n + 1, "fall", from);
  }

  // ---- light ----
  burn() {
    const l = this.light;
    if (l.kind !== "torch") return;
    l.left -= 1;
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
    const l = this.light;
    if (this.inDark()) return l.kind === "lantern" ? 0.45 : 0.25;
    if (l.kind === "lantern") return 1.15;
    if (l.kind === "torch") return l.left > 40 ? 1 : 0.6;
    return 0.22;
  }

  // what the party can see goes on the automap: around them, and along the corridor they face - by torchlight
  look() {
    const fl = this.floor, size = fl.grid.length;
    const seen = new Set(fl.seen.map(([x, y]) => keyOf(x, y)));
    const [x, y] = fl.pos;
    seen.add(keyOf(x, y));
    if (!this.inDark()) {
      for (let dx = -1; dx <= 1; dx++) for (let dy = -1; dy <= 1; dy++) seen.add(keyOf(x + dx, y + dy));
      if (this.light.kind) {
        const [fx, fy] = CM.DIRS[fl.facing];
        for (let d = 1; d < 5; d++) {
          const cx = x + fx * d, cy = y + fy * d;
          if (fl.dark.includes(keyOf(cx, cy))) break;
          seen.add(keyOf(cx, cy)); seen.add(keyOf(cx + fy, cy + fx)); seen.add(keyOf(cx - fy, cy - fx));
          if (!CM.passable(fl, cx, cy)) break;
        }
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
      this.sound("stairs");
      this.say("You haul the lever down. Somewhere, iron grinds upward.");
      this.dirty = true;
      this.emit("change");
      return;
    }
    if (here && here.type === "carving" && here.face === fl.facing) {
      here.read = true;
      const text = here.text >= 0 ? CM.LORE[here.text] || CM.LORE[CM.LORE.length - 1] : CM.LORE_EXTRA[-here.text - 1] || CM.LORE_EXTRA[0];
      this.say("You read the carving on the wall.");
      this.emit("lore", text);
      this.dirty = true;
      return;
    }
    if (thing && thing.type === "chest") {
      delete fl.things[k];
      this.gold += thing.gold;
      this.bag.push(...thing.items);
      this.sound("chest");
      const found = thing.items.map((i) => i.name).join(", ");
      this.say(`The chest creaks open: ${thing.gold} gold` + (found ? `, ${found}.` : "."));
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
    } else if (here && here.type === "fountain") {
      this.drink(here);
    } else if (here && here.type === "altar") {
      this.kneel(here);
    } else if (!CM.isOpen(fl, x + dx, y + dy)) {                       // a wall before you: search it
      if (ahead && ahead.type === "secret" && !ahead.found) {
        ahead.found = true;
        fl.grid[y + dy][x + dx] = 0;
        this.sound("stairs");
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

  drink(f) {
    if (f.used) { this.say("The fountain has run dry."); return; }
    f.used = true; f.known = true;
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
    if (this.wander < 1.1) return;
    this.wander = 0;
    const fl = this.floor, [px, py] = fl.pos;
    const walk = (x, y) => {
      if (!CM.passable(fl, x, y)) return false;
      const f = fl.features[keyOf(x, y)];
      return !(f && ["pit", "trapdoor", "teleporter", "spinner"].includes(f.type));
    };
    const dist = CM.distances(fl.grid, fl.pos, walk);
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
      if (d !== undefined && d <= 7) {
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

  // ---- fighting ----
  startCombat(key, thing, theyCame = false) {
    this.foes = thing.group;
    this.foeKey = key;
    delete thing.anim;
    this.song = 0;                                                       // the Bard's song lasts the fight
    for (const h of this.party) { h.cried = false; h.winded = false; }
    for (const m of this.foes) m.held = 0;
    this.setMode("combat");
    this.sound("monster");
    const names = {};
    for (const m of this.foes) names[m.name] = (names[m.name] || 0) + 1;
    const who = Object.entries(names).map(([k, n]) => CM.plural(n, k)).join(", ");
    this.say(theyCame ? `${who} come at you out of the dark!` : `Monsters! ${who} attack!`);
  }

  alive() { return this.party.filter((m) => m.hp > 0); }
  living() { return this.foes.filter((m) => m.hp > 0); }
  canAct(h) { const s = h.status || {}; return h.hp > 0 && !s.paralysis && !s.sleep && !s.stone; }   // standing, and not held by an ailment
  targets() { return this.alive().filter((h) => !(h.status || {}).stone); }                           // what a monster can reach: stone isn't worth hitting

  damage(atk, power, df) {
    return Math.max(1, atk + power + this.rnd.int(0, Math.max(1, Math.floor((atk + power) / 2))) - Math.floor(df / 2));
  }

  // a hero's numbers as they stand right now: a curse takes from them, the song gives
  effective(h) {
    const cursed = (h.status || {}).curse ? 2 : 0;
    return { atk: Math.max(1, h.atk - cursed + (this.song ? 2 : 0)), df: Math.max(0, h.df - cursed) };
  }
  stat(h, s) { return h.stats && h.stats[s] !== undefined ? h.stats[s] : 10; }
  hitChance(h) {
    return CM.clamp(0.8 + (this.stat(h, "dex") - 10) * 0.01 + ((h.boons || []).includes("keeneye") ? 0.1 : 0) - ((h.status || {}).blind ? 0.4 : 0), 0.25, 0.97);
  }
  critChance(h) { return CM.clamp((h.cls === "Rogue" ? 0.25 : 0.05) + (this.stat(h, "luck") - 10) * 0.01, 0.02, 0.6); }
  resistChance(h) {
    return CM.clamp((this.stat(h, "luck") - 10) * 0.02 + (this.stat(h, "wis") - 10) * 0.01 + ((h.boons || []).includes("thickblood") ? 0.2 : 0), 0, 0.6);
  }

  // an ailment settles on a hero, unless they shrug it off; it lasts this many rounds (curses and stone, until lifted)
  afflict(h, status, by) {
    if (!CM.STATUSES[status] || (h.status || {})[status]) return false;
    if (this.rnd.chance(this.resistChance(h))) { this.say(`${h.name} shrugs off the ${by}'s ${status === "stone" ? "gaze" : "touch"}.`); return false; }
    h.status = h.status || {};
    let turns = { poison: 8, paralysis: 2, sleep: 3, blind: 4, curse: 999, stone: 999 }[status];
    if (turns < 900 && (h.boons || []).includes("thickblood")) turns = Math.ceil(turns / 2);
    h.status[status] = turns;
    this.say(`${h.name} is ${CM.STATUSES[status].name.toLowerCase()}!`);
    this.emit("fx", { kind: "ailment", hero: h, status });
    return true;
  }

  cure(h, which) {                                                       // which: a list of ailments, or "all"
    const cured = [];
    for (const s of Object.keys(h.status || {})) if (which === "all" || which.includes(s)) { delete h.status[s]; cured.push(s); }
    return cured;
  }

  // the Knight draws the blows; the front row takes most of them; the back row is reached when it must be
  pickTarget() {
    const pool = this.targets();
    if (!pool.length) return null;
    const front = pool.some((h) => h.row === "front");
    const weights = pool.map((h) => (front ? (h.row === "front" ? (h.cls === "Knight" ? 5 : 3) : 1) : 1));
    let r = this.rnd.next() * weights.reduce((a, b) => a + b, 0);
    for (let i = 0; i < pool.length; i++) { r -= weights[i]; if (r < 0) return pool[i]; }
    return pool[pool.length - 1];
  }

  // one hero's blow on one foe (Fight, and the Ranger's arrows): the damage done, 0 for a miss
  strike(hero, target, note = "") {
    const rnd = this.rnd;
    if (!rnd.chance(this.hitChance(hero))) {
      this.say(`${hero.name} misses${note ? " with" + note : ""}.`);
      this.emit("fx", { kind: "miss", foe: target });
      return 0;
    }
    let dmg = this.damage(this.effective(hero).atk, hero.weapon.power, target.df), how = "";
    const back = hero.row === "back", reaches = hero.cls === "Rogue" || hero.cls === "Ranger";
    if (hero.cls === "Rogue" && back) { dmg *= 2; how = " - a knife from behind"; }
    else if (rnd.chance(this.critChance(hero))) { dmg *= 2; how = " - a weak spot"; }
    else if (back && !reaches) { dmg = Math.max(1, Math.ceil(dmg / 2)); how = ", reaching from the back row"; }
    if ((hero.boons || []).includes("warcry") && !hero.cried) { hero.cried = true; dmg *= 2; how += " - a war cry"; }
    target.hp -= dmg;
    this.say(`${hero.name} hits the ${target.name}${note} for ${dmg}${how}.`);
    this.emit("fx", { kind: "hit", foe: target, amount: dmg });
    this.sound("hit");
    return dmg;
  }

  // what Cast does, class by class
  cast(hero, foes) {
    const c = CM.CLASSES[hero.cls] || CM.CLASSES.Knight, rnd = this.rnd, key = this.stat(hero, c.key);
    const weakest = () => this.alive().reduce((a, b) => (a.hp / a.max <= b.hp / b.max ? a : b));
    if (c.cast === "fireball" && hero.mp >= 4) {
      hero.mp -= 4;
      this.sound("spell");
      const dmg = Math.max(1, 8 + hero.level * 4 + (key - 10));
      for (const m of foes) { m.hp -= dmg; this.emit("fx", { kind: "hit", foe: m, amount: dmg, spell: true }); }
      this.say(`${hero.name} hurls a fireball! ${dmg} damage to every foe.`);
    } else if (c.cast === "heal" && hero.mp >= 3) {
      hero.mp -= 3;
      const t = weakest(), heal = Math.max(1, 12 + hero.level * 4 + (key - 10));
      t.hp = Math.min(t.max, t.hp + heal);
      this.sound("heal");
      this.say(`${hero.name} prays: ${t.name} is healed by ${heal}.`);
    } else if (c.cast === "lay" && hero.mp >= 3) {
      hero.mp -= 3;
      const t = weakest(), heal = Math.max(1, 8 + hero.level * 3 + Math.floor((key - 10) / 2));
      t.hp = Math.min(t.max, t.hp + heal);
      const cured = this.cure(t, ["poison"]);
      this.sound("heal");
      this.say(`${hero.name} lays on hands: ${t.name} mends by ${heal}${cured.length ? ", and the poison leaves them" : ""}.`);
    } else if (c.cast === "thorns" && hero.mp >= 4) {
      hero.mp -= 4;
      this.sound("spell");
      const dmg = Math.max(1, 6 + hero.level * 3 + Math.floor((key - 10) / 2));
      let held = 0;
      for (const m of foes) {
        m.hp -= dmg;
        this.emit("fx", { kind: "hit", foe: m, amount: dmg, spell: true });
        if (m.hp > 0 && !m.boss && rnd.chance(0.3 + (key - 10) * 0.02)) { m.held = 1; held++; }
      }
      for (const h of this.alive()) h.hp = Math.min(h.max, h.hp + 3 + Math.floor(hero.level / 2));
      this.say(`${hero.name} calls thorns up through the stone: ${dmg} to every foe${held ? `, ${CM.plural(held, "foe")} held fast` : ""}; the party mends a little.`);
    } else if (c.cast === "song" && hero.mp >= 4) {
      hero.mp -= 4;
      this.song = 1;
      this.sound("heal");
      for (const h of this.alive()) { h.hp = Math.min(h.max, h.hp + 4); if ((h.status || {}).sleep) delete h.status.sleep; }
      this.say(`${hero.name} sings. Hearts lift: the party hits harder this fight, and hurts a little less.`);
    } else if (c.cast === "volley") {
      const first = rnd.pick(foes);
      this.strike(hero, first, " with an arrow");
      const rest = this.living().filter((m) => m !== first);
      if (rest.length) this.strike(hero, rnd.pick(rest), " with a second arrow");
      else if (first.hp > 0) this.strike(hero, first, " with a second arrow");
    } else {
      if (c.cast) this.say(`${hero.name} is out of magic, and swings instead.`);
      this.strike(hero, rnd.pick(foes));
    }
  }

  combatRound(action) {
    if (this.mode !== "combat") return;
    const rnd = this.rnd;
    let foes = this.living();
    if (action === "run") {
      if (rnd.chance(foes.some((m) => m.boss) ? 0 : 0.55)) {
        this.say("The party flees back the way it came!");
        this.setMode("explore");
        return;
      }
      this.say("You can't get away!");
    } else if (action === "potion") {
      this.potionInBattle();
    }
    for (const hero of this.alive()) {
      foes = this.living();
      if (!foes.length || action === "run" || action === "potion") break;
      const st = hero.status || {};
      if (!this.canAct(hero)) {
        if (!st.stone) this.say(`${hero.name} is ${st.sleep ? "asleep" : "paralysed"} and can't act.`);
        continue;
      }
      if (action === "cast") this.cast(hero, foes);
      else this.strike(hero, rnd.pick(foes));
    }
    for (const m of this.foes) if (m.hp <= 0 && !m.dead) { m.dead = true; this.emit("fx", { kind: "die", foe: m }); }
    if (!this.living().length) { this.wonFight(); return; }
    for (const m of this.living()) {                                     // the monsters' turn
      if (m.held > 0) { m.held--; this.say(`The ${m.name} is held fast by the thorns.`); continue; }
      const target = this.pickTarget();
      if (!target) break;
      if (rnd.chance(0.8)) {
        let dmg = this.damage(Math.floor(m.atk / 2), 0, this.effective(target).df + target.armor.power * 2);
        if (this.song) dmg = Math.max(1, dmg - 1);
        target.hp -= dmg;
        if ((target.status || {}).sleep) delete target.status.sleep;     // (a blow wakes)
        this.sound("hurt");
        this.emit("fx", { kind: "hurt", hero: target, amount: dmg, foe: m });
        this.say(`The ${m.name} hits ${target.name} for ${dmg}.` + (target.hp <= 0 ? `  ${target.name} falls!` : ""));
        if (target.hp > 0) {
          const kind = CM.monsterKind(m.name);
          if (kind && kind.touch && rnd.chance(kind.touch.chance)) this.afflict(target, kind.touch.status, m.name);
          if ((target.boons || []).includes("secondwind") && !target.winded && target.hp < target.max / 4) {
            target.winded = true;
            const back = Math.floor(target.max / 3);
            target.hp = Math.min(target.max, target.hp + back);
            this.say(`${target.name} finds a second wind (+${back}).`);
          }
        }
      } else {
        this.say(`The ${m.name} misses ${target.name}.`);
      }
    }
    for (const h of this.alive()) {                                      // the round's end: poison bites, ailments run their course
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
    for (const hero of this.party) hero.hp = Math.max(0, hero.hp);
    if (!this.alive().length || this.alive().every((h) => (h.status || {}).stone)) {
      this.say(this.alive().length ? "The last of the party stands as stone, and the dark closes in..." : "The last of the party falls...");
      this.endRun(false);
      return;
    }
    this.emit("change");
  }

  potionInBattle() {
    const potion = this.bag.find((i) => i.kind === "heal");
    if (!potion) { this.say("No healing potions left!"); return; }
    const target = this.alive().reduce((a, b) => (a.hp / a.max <= b.hp / b.max ? a : b));
    this.bag.splice(this.bag.indexOf(potion), 1);
    target.hp = Math.min(target.max, target.hp + potion.power);
    this.sound("heal");
    this.say(`The ${target.cls} drinks a Healing Potion (+${potion.power}).`);
  }

  wonFight() {
    const rnd = this.rnd;
    const xp = this.foes.reduce((s, m) => s + m.xp, 0);
    let gold = this.foes.reduce((s, m) => s + m.gold, 0);
    if (this.alive().some((h) => (h.boons || []).includes("scavenger"))) gold = Math.floor(gold * 1.25);
    this.gold += gold;
    const loot = rnd.chance(0.45) ? [CM.makeItem(this.floor.number, rnd)] : [];
    this.bag.push(...loot);
    const boss = this.foes.some((m) => m.boss);
    delete this.floor.things[this.foeKey];
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
        this.say(`${hero.name} reaches level ${hero.level}! A boon is theirs to choose (press ${this.party.indexOf(hero) + 1}).`);
      }
    }
    if (boss) { this.endRun(true); return; }
    this.setMode("explore");
    this.saveRun();
  }

  // ---- the bag, the merchant, the camp ----
  openBag(shop = false) {
    this.shopping = shop;
    if (shop && !this.stock) {
      const rnd = this.rnd, depth = this.floor.number + 3;
      this.stock = ["weapon", "weapon", "weapon", "armor", "armor", "armor"].map((k) => CM.makeItem(depth, rnd, k));
      this.stock.push({ name: "Healing Potion", kind: "heal", power: 20 + depth * 3, value: 20 },
        { name: "Mana Potion", kind: "mana", power: 12 + depth, value: 25 },
        { name: "Phoenix Feather", kind: "revive", power: 0, value: 120 }, CM.antidote(), CM.torch(), CM.lantern());
    }
    this.emit("bag", true);
  }

  closeBag() {
    this.emit("bag", false);
    this.saveRun();
    this.emit("change");
  }

  describe(item) {
    return { weapon: `weapon +${item.power}`, armor: `armor +${item.power}`, heal: "heals", mana: "restores magic", revive: "raises the fallen",
      torch: "light, for a while", lantern: "light that lasts", key: "opens a locked door",
      antidote: "cures poison, sleep, paralysis and blindness" }[item.kind];
  }

  give(row, n) {                                                        // returns a note for the bag screen, "" when it worked
    if (row < 0 || row >= this.bag.length) return "Pick something from your pack first.";
    const item = this.bag[row], hero = this.party[n];
    if (item.kind === "key") return "Keys turn in locks, not in hands. Walk into the locked door.";
    if (item.kind === "torch") {
      this.bag.splice(row, 1);
      this.light = { kind: "torch", left: CM.TORCH_STEPS };
      this.sound("spell");
      this.say(`The ${hero.cls} lights a fresh torch.`);
      this.emit("change");
      return "";
    }
    if (item.kind === "lantern") {
      this.bag.splice(row, 1);
      this.light = { kind: "lantern", left: 0 };
      this.sound("spell");
      this.say(`The ${hero.cls} lights the lantern. It won't run out.`);
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
      return `The ${hero.cls} has fallen. Raise them first.`;
    } else if (item.kind === "heal") {
      hero.hp = Math.min(hero.max, hero.hp + item.power);
      this.bag.splice(row, 1);
      this.sound("heal");
    } else if (item.kind === "mana") {
      if (!hero.maxmp) return `The ${hero.cls} has no magic to restore.`;
      hero.mp = Math.min(hero.maxmp, hero.mp + item.power);
      this.bag.splice(row, 1);
      this.sound("heal");
    } else {
      const old = hero[item.kind];
      hero[item.kind] = item;
      this.bag[row] = old;
      this.sound("chest");
    }
    this.emit("change");
    return "";
  }

  buy(row) {
    if (!this.stock || row < 0 || row >= this.stock.length) return "Pick something from the merchant's wares first.";
    const item = this.stock[row];
    if (this.gold < item.value) return "You can't afford that.";
    this.gold -= item.value;
    this.bag.push(Object.assign({}, item));
    if (["weapon", "armor", "lantern"].includes(item.kind)) this.stock.splice(row, 1);
    this.sound("coin");
    this.emit("change");
    return "";
  }

  sell(row) {
    if (row < 0 || row >= this.bag.length) return "Pick something from your pack to sell.";
    const item = this.bag.splice(row, 1)[0];
    this.gold += Math.floor(item.value / 2);
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

  // the camp's temple: ailments cured, a curse lifted, stone made flesh - for a price
  temple(service) {
    const cost = { cure: 30, uncurse: 60, unstone: 150 }[service];
    const which = service === "cure" ? CM.CURABLE : service === "uncurse" ? ["curse"] : ["stone"];
    const who = this.party.filter((h) => which.some((s) => (h.status || {})[s]));
    if (!who.length) {
      this.say({ cure: "No one here is ailing.", uncurse: "No curse lies on the party.", unstone: "No one here is stone." }[service]);
      return false;
    }
    if (this.gold < cost) { this.say(`The old priest asks ${cost} gold for that.`); return false; }
    this.gold -= cost;
    for (const h of who) this.cure(h, which);
    this.sound("heal");
    this.say({ cure: "Herbs and prayers: the party's ailments pass.", uncurse: "The priest's chant lifts the curse.",
      unstone: `Stone becomes flesh again: ${who.map((h) => h.name).join(", ")} can move.` }[service]);
    this.saveRun();
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
