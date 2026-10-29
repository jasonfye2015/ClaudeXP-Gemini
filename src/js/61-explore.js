"use strict";
// Exploring: turning and stepping, what a square does underfoot, the light the party carries, what the automap learns,
// Space on whatever is before you, and the monsters moving about the floor between the party's steps.
{
const keyOf = CM.keyOf;
Object.assign(CM.Game.prototype, {
  // ---- moving ----
  turn(way) {
    if (this.mode !== "explore") return false;
    this.floor.facing = (this.floor.facing + way + 4) % 4;
    this.look();
    this.emit("turned", this.floor.facing);
    this.emit("change");
    return true;
  },

  hasKey() { return this.bag.findIndex((i) => i.kind === "key"); },

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
  },

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
  },

  fall(from) {
    const n = this.floor.number;
    for (const m of this.alive()) m.hp = Math.max(1, m.hp - Math.max(1, Math.floor(m.max / 10)));
    this.sound("fall");
    this.emit("fell");
    if (n >= CM.BOTTOM && !this.endless) { this.say("You fall into blackness... and land, bruised, on the stone below."); return; }
    this.say(`You fall to floor ${n + 1}, bruised but alive.`);
    this.enterFloor(n + 1, "fall", from);
  },

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
  },

  inDark() { return this.floor ? this.floor.dark.includes(keyOf(this.floor.pos[0], this.floor.pos[1])) : false; },

  // how far the party can see, as a share of the depth's reach
  lightFactor() {
    const l = this.light, spell = this.spellLight > 0;
    if (this.inDark()) return spell ? 0.7 : l.kind === "lantern" ? 0.45 : 0.25;
    let f = l.kind === "lantern" ? 1.15 : l.kind === "torch" ? (l.left > 40 ? 1 : 0.6) : 0.22;
    if (spell) f = Math.max(f, 1.1);
    return f;
  },

  hasLight() { return Boolean(this.light.kind) || this.spellLight > 0; },

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
  },

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
      if (this.campBelow(fl.number)) {
        this.setMode("camp");
        this.reachCamp(fl.number);
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
  },

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
  },

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
  },

  kneel(f) {
    if (f.used) { this.say("You have prayed here already. The candles gutter."); return; }
    f.used = true;
    let lifted = 0;
    for (const m of this.alive()) { m.hp = Math.min(m.max, m.hp + Math.max(1, Math.floor(m.max * 0.3))); lifted += this.cure(m, ["curse"]).length; }
    this.sound("heal");
    this.say("You kneel. A warmth passes through the party" + (lifted ? ", and the curse lifts." : "."));
    this.saveRun();
    this.emit("change");
  },

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
  },
});
}

// ---- travel: the party walks by itself - to a square clicked on the automap, or to the nearest unexplored one (X) -
// over the squares it knows, and stops when something is close, something is underfoot, something new comes into
// view, or the light fails. The window takes one step each time the view is still; any key or click stops it. ----
{
const keyOf = CM.keyOf;
const WATCHED = ["chest", "key", "ghost", "hermit", "adventurer", "phylactery", "bones", "rope"];
const SEEN_AS = { chest: "a chest", key: "a key on the floor", ghost: "a pale shape in the air", hermit: "someone in a nest of rags", adventurer: "someone bound against the wall", phylactery: "a cold box", bones: "bones on the floor", rope: "a rope from above" };
Object.assign(CM.Game.prototype, {
  // a way over the squares the party knows, from where it stands to (x, y): the steps, or null
  pathTo(x, y) {
    const fl = this.floor, seen = new Set(fl.seen.map(([a, b]) => keyOf(a, b))), goal = keyOf(x, y), start = keyOf(fl.pos[0], fl.pos[1]);
    const picks = this.alive().some((h) => h.cls === "Rogue" && h.level >= CM.PICK_LOCK_LEVEL), key = this.hasKey() >= 0;
    const ok = (cx, cy) => {
      const k = keyOf(cx, cy);
      if (!seen.has(k) || !CM.isOpen(fl, cx, cy)) return false;
      const f = fl.features[k];
      if (f && f.type === "pit" && !f.roped) return false;                                       // (never into a pit by itself: walk there yourself, rope or no)
      if (f && ["trapdoor", "teleporter", "spinner"].includes(f.type) && f.known) return false;
      if (f && f.type === "gate" && !f.open) return false;
      if (f && f.type === "door" && !f.open && (f.riddle !== undefined || (f.locked && !key && !picks))) return false;
      return true;                                                                                // (a band of monsters on the way: the walk stops three squares short of it)
    };
    if (goal !== start && !ok(x, y)) return null;
    const parent = new Map([[start, null]]), queue = [fl.pos.slice()];
    for (let i = 0; i < queue.length && !parent.has(goal); i++) {
      const [cx, cy] = queue[i];
      for (const [dx, dy] of CM.DIRS) {
        const nx = cx + dx, ny = cy + dy, nk = keyOf(nx, ny);
        if (parent.has(nk) || !ok(nx, ny)) continue;
        parent.set(nk, keyOf(cx, cy)); queue.push([nx, ny]);
      }
    }
    if (!parent.has(goal)) return null;
    const path = [];
    for (let k = goal; k !== start; k = parent.get(k)) path.unshift(k.split(",").map(Number));
    return path;
  },
  // the keys of the things the party can see that are worth stopping for
  thingsInView() {
    const fl = this.floor, out = new Set();
    for (const [x, y] of fl.seen) { const k = keyOf(x, y), t = fl.things[k]; if (t && WATCHED.includes(t.type)) out.add(k); }
    return out;
  },
  // is a band of monsters within n steps of the party, by the corridors?
  monstersNear(n) {
    const fl = this.floor, dist = CM.distances(fl.grid, fl.pos, (x, y) => CM.passable(fl, x, y));
    for (const [k, t] of Object.entries(fl.things)) if (["monsters", "boss", "guardian"].includes(t.type) && dist.has(k) && dist.get(k) <= n) return t;
    return null;
  },
  // the nearest known square with an unknown one beside it (not the one the party stands on)
  frontier() {
    const fl = this.floor, seen = new Set(fl.seen.map(([a, b]) => keyOf(a, b))), size = fl.grid.length;
    const walk = (x, y) => { const f = fl.features[keyOf(x, y)]; return seen.has(keyOf(x, y)) && CM.passable(fl, x, y) && !(f && ((f.type === "pit" && !f.roped) || (["trapdoor", "teleporter", "spinner"].includes(f.type) && f.known))); };
    const unknownBeside = (x, y) => CM.DIRS.some(([dx, dy]) => { const nx = x + dx, ny = y + dy; return nx > 0 && ny > 0 && nx < size - 1 && ny < size - 1 && !seen.has(keyOf(nx, ny)); });
    let best = null, bd = 1e9;
    for (const [k, d] of CM.distances(fl.grid, fl.pos, walk)) {
      if (d === 0 || d >= bd) continue;
      const [x, y] = k.split(",").map(Number);
      if (unknownBeside(x, y)) { best = [x, y]; bd = d; }
    }
    return best;
  },
  travelTo(x, y, explore = false) {
    if (this.mode !== "explore" || !this.floor) return false;
    if (x === this.floor.pos[0] && y === this.floor.pos[1]) return false;
    const path = this.pathTo(x, y);
    if (!path) { if (!explore) this.say("No known way there."); return false; }
    this.travel = { path, to: [x, y], explore, known: this.thingsInView() };
    this.emit("change");
    return true;
  },
  explore() {
    if (this.mode !== "explore") return false;
    const next = this.frontier();
    if (!next || !this.travelTo(next[0], next[1], true)) { this.say("Nothing more to explore that you can see: the floor is known, as far as the light has reached."); return false; }
    return true;
  },
  stopTravel() { if (this.travel) { this.travel = null; this.emit("change"); } },
  // one step of the journey; false when it is over
  travelStep() {
    const t = this.travel;
    if (!t || this.mode !== "explore") { this.travel = null; return false; }
    const fl = this.floor;
    if (!t.path.length) {
      if (t.explore) {
        const next = this.frontier(), path = next && this.pathTo(next[0], next[1]);
        if (path) { t.path = path; t.to = next; return this.travelStep(); }
        this.say("Nothing more to explore that you can see: the floor is known, as far as the light has reached.");
      }
      this.travel = null; this.emit("change"); return false;
    }
    const [nx, ny] = t.path[0], d = CM.DIRS.findIndex(([dx, dy]) => fl.pos[0] + dx === nx && fl.pos[1] + dy === ny);
    if (d < 0) { this.travel = null; this.emit("change"); return false; }   // (a spin or a teleporter put the party elsewhere)
    const rel = (d - fl.facing + 4) % 4;
    if (rel !== 0) { this.turn(rel === 3 ? -1 : 1); return true; }
    const was = fl.pos.join(",");
    const moved = this.move(0);
    if (this.mode !== "explore" || this.floor !== fl || !this.travel) { this.travel = null; return false; }
    if (!moved && fl.pos.join(",") === was) {
      const f = fl.features[keyOf(nx, ny)];
      if (f && f.type === "door" && f.open) return true;                 // (the door opened: through it next step)
      this.travel = null; this.emit("change"); return false;
    }
    t.path.shift();
    return this.travelCheck();
  },
  travelCheck() {
    const t = this.travel, fl = this.floor, k = keyOf(fl.pos[0], fl.pos[1]), thing = fl.things[k], f = fl.features[k];
    const stop = (why) => { this.travel = null; if (why) this.say(why); this.emit("change"); return false; };
    if (!this.hasLight()) return stop("The dark. You stop, and feel for the wall.");
    if (thing && !["key", "bones"].includes(thing.type)) return stop(null);
    if (f && ((f.type === "fountain" && !f.used) || (f.type === "altar" && !f.used) || (f.type === "lever" && !f.pulled) || (f.type === "carving" && !f.read))) return stop(null);
    if (this.monstersNear(3)) return stop("Something is close. You stop.");
    const now = this.thingsInView();
    for (const key of now) if (!t.known.has(key)) { const what = fl.things[key]; return stop(`You see ${SEEN_AS[what.type] || "something"}. You stop.`); }
    if (!t.path.length && !t.explore) return stop(null);
    return true;
  },
  // a note pinned to a square of the automap (a word or two; empty takes it off)
  setNote(x, y, text) {
    const fl = this.floor, k = keyOf(x, y);
    fl.notes = fl.notes || {};
    text = String(text || "").trim().slice(0, 24);
    if (text) fl.notes[k] = text; else delete fl.notes[k];
    if (!Object.keys(fl.notes).length) delete fl.notes;
    this.dirty = true;
    this.emit("change");
    return true;
  },
});
}

