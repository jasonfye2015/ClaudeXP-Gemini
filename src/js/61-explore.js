"use strict";
// Exploring: turning and stepping, what a square does underfoot, the light the party carries, what the automap learns,
// Space on whatever is before you, and the monsters moving about the floor between the party's steps.
{
const keyOf = CM.keyOf;
Object.assign(CM.Game.prototype, {
  // ---- moving ----
  turn(way) {
    if (this.mode !== "explore") return false;
    this.logAct("turn", way);
    this.floor.facing = (this.floor.facing + way + 4) % 4;
    this.look();
    this.emit("turned", this.floor.facing);
    this.emit("change");
    return true;
  },

  hasKey() { return this.bag.findIndex((i) => i.kind === "key"); },

  move(rel) {
    if (this.mode !== "explore") return false;
    this.logAct("move", rel);
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
    if (fl.hazard === "tide" && this.steps % CM.TIDE_STEPS === 0) {       // the Drowned Town's tide turns
      fl.tide = !fl.tide;
      this.dirty = true;
      this.say(fl.tide ? "The water rises in the streets, cold and quick: high tide. The torch hisses, and things move in the water." : "The water drains away down the streets: low tide.");
    }
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
      } else if (thing.type === "boxkey") {
        delete fl.things[k];
        this.bag.push({ name: `Strongbox Key (floor ${thing.box})`, kind: "boxkey", box: thing.box, power: 0, value: 0 });
        this.sound("coin");
        this.say(`A heavy key, stamped with a number: ${thing.box}. A strongbox waits for it two floors down.`);
      } else {
        this.say({ chest: "A chest sits here. (Space to open it)", ladder: "A ladder leads down into the dark. (Space to climb down)",
          stairs_up: "The stairs you came down. (Space to climb back up)",
          phylactery: "A plain box, cold to look at. Something in it beats, slowly. (Space to smash it)",
          ghost: "A pale shape hangs in the air here, waiting. (Space to speak to it)", hermit: "A hermit crouches in a nest of rags. (Space to speak to him)",
          adventurer: "Someone sits bound against the wall. (Space to cut them loose)", rope: "A rope hangs down from the floor above. (Space to climb it)",
          event: `${(CM.EVENTS[thing.event] || {}).title || "Something"}. (Space to look closer)`, strongbox: thing.opened ? "An iron strongbox, open and empty." : `An iron strongbox, bolted to the floor, with a keyhole. (The key is on floor ${thing.from}.)`,
          peddler: "A peddler sits on his pack, with a lantern and a smile. (Space to see his wares)", rivals: "Four adventurers, armed, look you over. (Space to speak to them)",
          remains: "Bones in torn gear, four of them, and a name you know from the Hall of Fame. (Space to see what they left)" }[thing.type]);
      }
    }
    if (f) this.arrive(f, k);
    this.emit("change");
    return true;
  },

  // what a square does when the party steps onto it
  arrive(f, k) {
    const fl = this.floor;
    if (f.type === "pit" && f.roped && fl.number < CM.LAST_FLOOR) { this.say("You climb down the rope you left, hand over hand."); this.inUse = true; this.ropeDown(k); this.inUse = false; return; }
    if (f.type === "pit" && this.hasItem("rope") >= 0 && fl.number < CM.LAST_FLOOR) {
      this.bag.splice(this.hasItem("rope"), 1);
      f.roped = true;
      this.say("You make the rope fast and lower the party down the pit, slow and safe.");
      this.inUse = true; this.ropeDown(k); this.inUse = false;
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
    } else if (f.type === "spores") {
      f.known = true;
      this.sound("ailment");
      this.emit("fx", { kind: "trap", trap: "gas" });
      const front = this.alive().filter((h) => h.row === "front");
      let took = 0;
      for (const h of (front.length ? front : this.alive())) if (this.rnd.chance(0.5) && this.afflict(h, "poison", "the spores")) took++;
      this.say(`You walk through a hanging cloud of spores${took ? "" : ", holding your breath"}.`);
    } else if (f.type === "vents") {
      f.known = true;
      this.steps = this.steps || 0;
      if (this.steps % 3 === 0) {
        this.sound("trap");
        this.emit("fx", { kind: "trap", trap: "blade" });
        for (const h of this.alive()) h.hp = Math.max(1, h.hp - Math.max(2, Math.floor(h.max * 0.1)));
        this.say("The vent under your boots breathes fire! Everyone is scorched.");
      } else this.say("A vent in the floor, hot. It breathes on a beat: move on.");
    } else if (f.type === "bonepiles") {
      if (!f.spent) {
        f.spent = true; f.known = true;
        if (this.rnd.chance(0.6)) {
          const n = 2 + this.rnd.int(0, 1), group = [];
          for (let i = 0; i < n; i++) group.push(this.tune(CM.makeMonster(CM.monsterKind("Skeleton"), CM.monsterLevel(fl.number), this.rnd)));
          this.say("The bones heaped beside you rattle, and stand up!");
          this.foes = group;
          this.startCombat(k, { group }, true);
          return;
        }
        this.say("A heap of bones, higher than a man. It does not move. This time.");
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
    l.left -= (this.floor && (this.floor.special === "wading" || this.floor.tide)) || this.has("gloom") ? 2 : 1;
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
    const spell = this.spellLight > 0 || this.alive().some((h) => h.familiar === "owl");   // (a conjured light - or an owl - sees through a magical dark)
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
    const cat = this.alive().find((h) => h.familiar === "cat");
    if (cat) for (const [k, f] of Object.entries(fl.features)) { const [tx, ty] = k.split(",").map(Number); if (Math.abs(tx - x) + Math.abs(ty - y) <= 1 && f.type === "secret" && !f.found) { f.found = true; fl.grid[ty][tx] = 0; this.say(`${cat.name}'s cat scratches at the wall - and a hidden door gives.`); this.emit("mesh"); } }
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
    this.logAct("use");
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
    if (thing && ["ghost", "hermit", "adventurer"].includes(thing.type)) { this.inUse = true; this.talk(thing, k); this.inUse = false; return; }
    if (thing && thing.type === "event") { this.askEvent(thing, k); return; }
    if (thing && thing.type === "strongbox") { this.openStrongbox(thing, k); return; }
    if (thing && thing.type === "peddler") { this.peddle(thing, k); return; }
    if (thing && thing.type === "rivals") { this.meetRivals(thing, k); return; }
    if (thing && thing.type === "remains") { this.takeRemains(thing, k); return; }
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
      this.inUse = true; this.drink(here); this.inUse = false;
    } else if (here && here.type === "altar") {
      this.inUse = true; this.kneel(here); this.inUse = false;
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
      const group = CM.monsterGroup(fl.number, this.rnd, this.gen);
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
    if (!this.inUse) this.logAct("drink");
    f.used = true; f.known = true;
    if (this.has("drought")) { this.say("The basin is dry to the bottom, cracked. A drought lies on the dungeon today."); this.saveRun(); this.emit("change"); return; }
    this.tally.drank = (this.tally.drank || 0) + 1;
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
    if (!this.inUse) this.logAct("kneel");
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
    this.wanderMonsters();
  },

  // the monsters' turn to move (one every second or so of real time, logged so a replay moves them at the same moments)
  wanderMonsters() {
    if (this.mode !== "explore") return;
    this.logAct("tick");
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
      if (d !== undefined && d <= 6 && (!nearest || d < nearest.d)) nearest = { d, t, k };
    }
    if (nearest) {                                                       // its call, from the side it is on
      const m = nearest.t.group.find((f) => f.hp > 0 && !f.fled) || nearest.t.group[0];
      const [mx, my] = nearest.k.split(",").map(Number), [fx, fy] = CM.DIRS[fl.facing];
      const pan = CM.clamp(((mx - px) * -fy + (my - py) * fx) / Math.max(1, Math.abs(mx - px) + Math.abs(my - py)), -1, 1);   // (right of the facing is positive)
      if (m) this.emit("near", m.kind || m.name, nearest.d, pan);
    }
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
      if (d !== undefined && (d <= 7 || t.hunter || this.has("hunted"))) {
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
const WATCHED = ["chest", "key", "ghost", "hermit", "adventurer", "phylactery", "bones", "rope", "event", "strongbox", "boxkey", "peddler", "rivals", "remains"];
const SEEN_AS = { chest: "a chest", key: "a key on the floor", ghost: "a pale shape in the air", hermit: "someone in a nest of rags", adventurer: "someone bound against the wall", phylactery: "a cold box", bones: "bones on the floor", rope: "a rope from above",
  event: "something strange", strongbox: "an iron strongbox", boxkey: "a heavy key on the floor", peddler: "a peddler with a lantern", rivals: "other adventurers", remains: "the remains of a party" };
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
      if (f && ["trapdoor", "teleporter", "spinner", "spores", "vents", "bonepiles"].includes(f.type) && f.known) return false;
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
    this.logAct("travelTo", x, y, explore ? 1 : 0);
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
  stopTravel() { if (this.travel) { this.logAct("stopTravel"); this.travel = null; this.emit("change"); } },
  // one step of the journey; false when it is over
  travelStep() {
    const t = this.travel;
    if (!t || this.mode !== "explore") { this.travel = null; return false; }
    this.logAct("travelStep");
    this.replaying = (this.replaying || 0) + 1;                          // (the moves and turns of a step are the step's: not logged twice)
    try { return this.travelStep2(); } finally { this.replaying -= 1; }
  },
  travelStep2() {
    const t = this.travel;
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
    if (thing && !["key", "bones", "boxkey"].includes(thing.type)) return stop(null);
    if (f && ((f.type === "fountain" && !f.used) || (f.type === "altar" && !f.used) || (f.type === "lever" && !f.pulled) || (f.type === "carving" && !f.read))) return stop(null);
    if (this.monstersNear(3)) return stop("Something is close. You stop.");
    const now = this.thingsInView();
    for (const key of now) if (!t.known.has(key)) { const what = fl.things[key]; return stop(`You see ${SEEN_AS[what.type] || "something"}. You stop.`); }
    if (!t.path.length && !t.explore) return stop(null);
    return true;
  },
  // a note pinned to a square of the automap (a word or two; empty takes it off)
  setNote(x, y, text) {
    this.logAct("setNote", x, y, text);
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

// ---- the dungeon's strangers: a choice on the floor, a strongbox and its key, a peddler, a rival party ----
{
Object.assign(CM.Game.prototype, {
  // a party that fell on this floor of this seed, in a run before: their bones, and one thing they carried
  layRemains(fl) {
    const past = (this.fallen || []).find((f) => f.seed === this.seed && f.floor === fl.number && !(this.remainsFound || []).includes(f.id));
    if (!past || !past.pos) return;
    const free = (x, y) => CM.passable(fl, x, y) && !fl.things[keyOf(x, y)] && !fl.features[keyOf(x, y)] && !(fl.pos[0] === x && fl.pos[1] === y);
    let at = free(past.pos[0], past.pos[1]) ? past.pos : null;
    if (!at) {                                                           // (they fell on the stairs, or where something stands: the nearest open square)
      let best = 1e9;
      for (const [k, d] of CM.distances(fl.grid, past.pos, (x, y) => CM.passable(fl, x, y))) { const [x, y] = k.split(",").map(Number); if (d < best && d <= 4 && free(x, y)) { best = d; at = [x, y]; } }
    }
    if (!at) return;
    fl.things[keyOf(at[0], at[1])] = { type: "remains", id: past.id, names: past.names, date: past.date, item: past.item || null };
  },
  takeRemains(thing, k) {
    this.remainsFound = (this.remainsFound || []).concat(thing.id);
    delete this.floor.things[k];
    if (thing.item) this.bag.push(thing.item);
    this.sound("coin");
    this.say(`${thing.names.join(", ").replace(/, ([^,]*)$/, " and $1")} fell here, ${thing.date}. The dark did not take everything${thing.item ? `: ${thing.item.name} is still with them, and now with you` : ""}.`);
    this.emit("talk", { title: "The remains of a party", text: `Four of them, where they fell: ${thing.names.join(", ")}. You know the names from the Hall of Fame. ${thing.item ? `Among the bones, ${thing.item.name}. They would want it used.` : "There is nothing left to take but the warning."}` });
    this.saveRun();
    this.emit("change");
  },
  hazardsSeen(id) { this.hazardsMet = this.hazardsMet || []; if (this.hazardsMet.includes(id)) return true; this.hazardsMet.push(id); return false; },
  askEvent(thing, k) {
    const E = CM.EVENTS[thing.event];
    if (!E) return;
    if (thing.done) { this.say(thing.after || "Nothing more here."); return; }
    this.emit("choice", { k, title: E.title, text: E.text, options: E.options.map((o) => o.label) });
  },
  // the player chose: the option's effect, with the run's dice
  choose(k, i) {
    const fl = this.floor, thing = fl.things[k], E = thing && CM.EVENTS[thing.event], opt = E && E.options[i];
    if (!opt || thing.done) return false;
    this.logAct("choose", k, i);
    const rnd = this.rnd, L = fl.number, front = this.alive().find((h) => h.row === "front") || this.alive()[0];
    const finish = (text, keep) => { thing.done = true; thing.after = keep || "Nothing more here."; this.say(text); if (!keep) delete fl.things[k]; this.saveRun(); this.emit("change"); };
    switch (opt.effect) {
      case "leave": this.say("You walk on."); return true;
      case "blood": { const cost = Math.max(1, Math.floor(front.hp / 5)); front.hp -= cost; front.stats.str = Math.min(25, front.stats.str + 1); CM.recompute(front); this.emit("fx", { kind: "hurt", hero: front, amount: cost, foe: { name: "The knife" } }); finish(`${front.name} opens a palm over the altar. The stone drinks, and something comes back up the arm: +1 Strength, for good (-${cost} health).`, "The altar is sated."); return true; }
      case "prisoner": {
        if (rnd.chance(0.5)) { const h = CM.makeRecruit(Math.max(1, Math.floor(L / 2)), rnd); h.price = 0; this.rescued = (this.rescued || []).concat(h); this.achieve("friend"); finish(`The hood comes off: ${h.name} the ${h.cls}, three days chained and still breathing. They make for the camp, owing you their life; the tavern will have them, free.`); }
        else { finish("The hood comes off, and under it is a face that has been dead a while, and is hungry."); const g = [this.tune(CM.makeMonster(CM.monsterKind("Ghoul"), CM.monsterLevel(L), rnd))]; this.foes = g; this.startCombat(k, { group: g }, true); }
        return true;
      }
      case "gamble": { if (this.gold < 100) { this.say("You haven't a hundred gold. The dealer shrugs."); return true; } this.gold -= 100; if (rnd.chance(0.45)) { this.gold += 250; this.sound("coin"); finish("Three sixes. The dealer counts out 250 gold without a word, and the lantern goes out.", "The table is empty, and the dealer gone."); } else { finish("Two and a one. The dealer sweeps the gold away, and the lantern goes out.", "The table is empty, and the dealer gone."); } return true; }
      case "blackwater": { const h = rnd.pick(this.alive()), st = rnd.pick(CM.STATS); h.stats[st] = Math.min(25, h.stats[st] + 2); CM.recompute(h); h.status = h.status || {}; h.status.curse = 999; this.sound("ailment"); finish(`${h.name} drinks. +2 ${CM.STAT_NAMES[st]}, for good - and a curse, until the temple lifts it.`, "The fountain runs black, and you have drunk."); return true; }
      case "campfire": { for (const h of this.alive()) h.hp = Math.min(h.max, h.hp + Math.ceil(h.max / 3)); this.sound("heal"); if (rnd.chance(0.4)) { finish("You rest by the warm ashes, and mend - until something comes to the light."); const g = CM.monsterGroup(L, rnd, this.gen).map((m) => this.tune(m)); this.foes = g; this.startCombat(k, { group: g }, true); } else finish("You rest by the warm ashes, and mend. Nothing comes."); return true; }
      case "purse": { const gold = 30 * L; this.gold += gold; this.sound("coin"); if (rnd.chance(0.4)) { this.afflict(front, "poison", "the needle"); finish(`${gold} gold, and a needle in the lining of the purse.`); } else finish(`${gold} gold. He will not need it.`); return true; }
      case "bury": { const xp = 20 * L; for (const h of this.alive()) h.xp += xp; this.achieve("kind"); this.checkLevels(); finish(`You heap stones over him and say what you can. ${xp} experience each, and the floor feels quieter.`); return true; }
      case "whisper": { fl.seen = []; for (let y = 0; y < fl.grid.length; y++) for (let x = 0; x < fl.grid.length; x++) fl.seen.push([x, y]); for (const f of Object.values(fl.features)) if ("known" in f) f.known = true; const h = rnd.pick(this.alive()); if (rnd.chance(0.3)) { h.status = h.status || {}; h.status.curse = 999; this.sound("ailment"); finish(`The box whispers the floor into your ear, every turn of it - and something else into ${h.name}'s: a curse.`); } else finish("The box whispers the floor into your ear, every turn of it, and falls silent."); return true; }
      case "burnnest": { const t = this.bag.findIndex((i) => i.kind === "torch"); if (t < 0) { this.say("No spare torch to burn it with."); return true; } this.bag.splice(t, 1); const gold = 15 * L; this.gold += gold; this.sound("coin"); finish(`The nest goes up like paper. In the ashes, ${gold} gold.`); return true; }
      case "rummage": { const gold = 20 * L; this.gold += gold; this.sound("coin"); for (const h of this.alive().slice(0, 2)) if (rnd.chance(0.5)) this.afflict(h, "poison", "the rats"); finish(`${gold} gold, and small teeth.`); return true; }
      case "pray": { this.blessedNext = true; this.sound("heal"); finish("You pray. The stone hand is warm for a moment. The next fight begins under a blessing.", "The saint's hand is cold again."); return true; }
      case "touch": { if (rnd.chance(0.3) && this.afflict(front, "stone", "the statue")) finish(`${front.name} touches the hand, and the stone looks back.`, "The saint's hand is cold again."); else { front.pending = (front.pending || 0) + 1; this.sound("level"); finish(`${front.name} touches the hand, and something is given: a boon to choose (press ${this.party.indexOf(front) + 1}).`, "The saint's hand is cold again."); } return true; }
      case "pack": { if (rnd.chance(0.6)) { const it = CM.affix(CM.makeItem(L + 2, rnd, rnd.pick(["weapon", "armor", "helm", "shield"])), L + 8, rnd); it.unknown = false; this.bag.push(it); this.sound("chest"); finish(`In the pack: ${it.name} (${CM.itemLabel(it)}).`); } else { this.sound("trap"); this.springTrap(rnd.pick(["gas", "blade", "needle"]), k); finish("The straps were cut for a reason."); } return true; }
      case "bathe": { for (const h of this.alive()) { this.cure(h, "all"); h.hp = Math.min(h.max, h.hp + Math.ceil(h.max / 4)); } this.sound("heal"); if (rnd.chance(0.25)) { finish("The water takes every ache with it - and something takes hold of an ankle."); const g = [this.tune(CM.makeMonster(CM.monsterKind("Drowned"), CM.monsterLevel(L), rnd)), this.tune(CM.makeMonster(CM.monsterKind("Drowned"), CM.monsterLevel(L), rnd))]; this.foes = g; this.startCombat(k, { group: g }, true); } else finish("The water takes every ache with it. On the bottom, a face, smiling."); return true; }
      case "dig": { if (rnd.chance(0.5)) { const ids = Object.keys(CM.TOMES), it = CM.tome(ids[rnd.int(0, ids.length - 1)]); this.bag.push(it); this.sound("chest"); finish(`Under the cairn, wrapped in oilcloth: the ${it.name}.`); } else { finish("Under the cairn, the hermit - and he is not pleased."); const g = [this.tune(CM.makeMonster(CM.monsterKind("Wraith"), CM.monsterLevel(L), rnd))]; this.foes = g; this.startCombat(k, { group: g }, true); } return true; }
      default: return false;
    }
  },
  openStrongbox(thing, k) {
    if (thing.opened) { this.say("The strongbox is open, and empty."); return; }
    const row = this.bag.findIndex((i) => i.kind === "boxkey" && i.box === this.floor.number);
    if (row < 0) { this.sound("bump"); this.say(`The strongbox is bolted to the floor and locked. Its key lies on floor ${thing.from}${this.bag.some((i) => i.kind === "boxkey") ? " - not the one you carry" : ""}.`); return; }
    this.bag.splice(row, 1);
    thing.opened = true;
    const rnd = new CM.Random(CM.hashSeed(`${this.seed}:strongbox:${this.floor.number}`)), gold = 60 * this.floor.number;
    const it = CM.affix(CM.makeItem(this.floor.number + 3, rnd, rnd.pick(["weapon", "armor", "helm", "shield", "ring", "amulet"])), 99, rnd);
    it.unknown = false;
    this.gold += gold; this.bag.push(it);
    this.sound("chest");
    this.achieve("strongbox");
    this.emit("fx", { kind: "sparkle", at: k.split(",").map(Number) });
    this.say(`The key turns twice, and the lid comes up: ${gold} gold, and ${it.name} (${CM.itemLabel(it)}).`);
    this.saveRun();
    this.emit("change");
  },
  // a peddler: a few odd things, dear, from the seed (what you buy stays bought)
  peddle(thing, k) {
    if (!thing.stock) {
      const rnd = new CM.Random(CM.hashSeed(`${this.seed}:peddler:${this.floor.number}`)), L = this.floor.number;
      const gear = CM.affix(CM.makeItem(L + 4, rnd, rnd.pick(["weapon", "armor"])), 99, rnd); gear.unknown = false; gear.value = Math.floor(gear.value * 1.5) + 100;
      thing.stock = [gear, { name: "Greater Healing Potion", kind: "greaterheal", power: 2 * (20 + L * 3), value: 90 }, CM.oil(rnd.pick(["fire", "frost", "holy"])), CM.scroll("mapping"), CM.ingredient(rnd.pick(Object.keys(CM.INGREDIENTS)))];
      thing.stock[3].value = 60;
    }
    this.stock = thing.stock; this.peddling = k;
    this.say("The peddler spreads a cloth and lays out what he has. His prices are what you'd expect, down here.");
    this.openBag(true);
  },
  meetRivals(thing, k) {
    if (thing.met) { this.say("The rivals are gone, one way or the other."); return; }
    this.emit("choice", { k, title: "A rival party", text: "Four adventurers, as deep as you and as tired, with their hands near their hilts. \"This floor's ours,\" says the one in front, not unkindly. \"Trade, if you like. Or go round.\"", rivals: true,
      options: ["Trade: their map of the floor, for 40 gold", "Challenge them for the floor (a fight; their purse and their best thing)", "Let them be"] });
  },
  chooseRivals(k, i) {
    const fl = this.floor, thing = fl.things[k];
    if (!thing || thing.type !== "rivals" || thing.met) return false;
    this.logAct("chooseRivals", k, i);
    if (i === 0) {
      if (this.gold < 40) { this.say("You haven't forty gold. They shrug."); return true; }
      this.gold -= 40; thing.met = true;
      fl.seen = []; for (let y = 0; y < fl.grid.length; y++) for (let x = 0; x < fl.grid.length; x++) fl.seen.push([x, y]);
      delete fl.things[k];
      this.sound("coin");
      this.say("Their map is good: the whole floor, in a careful hand. They go up the stairs, and you don't see them again.");
    } else if (i === 1) {
      thing.met = true;
      const L = CM.monsterLevel(fl.number), rnd = this.rnd, group = [];
      for (const kind of ["Sellsword", "Sellsword", "Hedge Wizard"]) group.push(this.tune(CM.makeMonster(CM.monsterKind(kind), L, rnd)));
      for (const m of group) { m.gold = 20 * fl.number; m.xp = Math.round(m.xp * 1.5); }
      thing.group = group; thing.type = "monsters"; thing.rivalsFight = true;
      this.say("\"Then it's like that,\" says the one in front, and draws.");
      this.startCombat(k, thing);
    } else {
      thing.met = true; delete fl.things[k];
      if (this.rnd.chance(0.5)) { this.bag.push({ name: "Healing Potion", kind: "heal", power: 20 + fl.number * 3, value: 20 }); this.say("They nod, and go round you, and the last of them leaves a potion on the floor as they pass. \"For the road.\""); }
      else this.say("They nod, and go round you, and the dark takes them.");
    }
    this.saveRun(); this.emit("change");
    return true;
  },
});
}

