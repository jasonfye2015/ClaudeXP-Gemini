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
    if (this.perch) { this.climbDown(); return false; }               // (on a tower's top: a step is the stair down)
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
      if (f.barred) {
        f.barred = 0; this.sound("unlock"); this.say("You lift the bar, and leave it: the door is a door again.");
      } else if (f.locked) {
        const i = this.hasKey();
        if (i < 0) {
          const note = this.tryLock(f, k);
          if (note !== "") { this.sound("bump"); if (note) this.say(note); return false; }
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
      this.makeNoise(CM.NOISE.door);
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
    if (thing && (thing.type === "guardian" || thing.type === "boss") && !thing.parleyed && !thing.group[0].echo && this.openParley(k, thing)) return false;   // (it speaks first)
    if (thing && (thing.type === "monsters" || thing.type === "boss" || thing.type === "guardian")) {
      if (thing.asleep) { thing.asleep = false; this.strikeSleepers = true; }   // (asleep: the party's blows fall first, and every one lands)
      this.startCombat(k, thing);
      return false;
    }
    fl.pos = [x, y];
    if (fl.number >= 1) this.makeNoise(this.stepNoise());              // (the step's noise: 61b-lairs.js)
    this.clock = (this.clock || 0) + 1;                                  // (a step is a minute)
    this.sound("step");
    this.burn();
    this.warnWeight();                                                   // (the pack's weight only slows the party: the frame loop paces the steps)
    this.lightSpare();
    this.look();
    this.emit("moved", x, y);
    this.dirty = true;
    this.steps = (this.steps || 0) + 1;
    this.count("steps");
    if (this.steps % 150 === 0 && this.gen >= 2) this.changeBehind();        // (the dungeon is not still behind you)
    if (this.buffs && this.buffs.salve !== undefined && (this.steps || 0) % 5 === 0) for (const h of this.alive()) if (h.hp < h.max) h.hp += 1;   // (the salve: a little, every few steps)
    if (fl.number !== 0) this.fed = (this.fed || 0) + 1 + (this.alive().some((h) => CM.equipped(h).some((it) => it.props && it.props.cursed && it.props.curse === "hunger")) ? 1 : 0);   // the stomachs: hungry past three hundred steps, weary past six (a hungering curse: twice as fast)
    if (this.fed === CM.HUNGER.hungry) this.say("The party is hungry. A ration would be welcome.");
    if (this.fed === CM.HUNGER.weary) this.say("The party is weary with hunger: every blow does less until they eat.");
    if (this.fed > CM.HUNGER.hungry && this.fed % 50 === 0) this.cheer(-1);
    if (fl.hazard === "tide" && this.steps % (CM.season(this) === "autumn" ? Math.round(CM.TIDE_STEPS * 0.75) : CM.TIDE_STEPS) === 0) {   // (autumn: mist on the Drowned Town, the tide quicker)       // the Drowned Town's tide turns
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
      } else if (thing.type === "bones" && thing.bell) {
        delete fl.things[k];
        this.bag.push(Object.assign({}, CM.BELL));
        this.sound("coin");
        this.say(CM.BELL.found);
        this.markRead("thing.bell");
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
          remains: "Bones in torn gear, four of them, and a name you know from the Hall of Fame. (Space to see what they left)",
          wingstair: `A second stair goes down here, narrower, into ${(CM.WINGS[thing.wing] || CM.WINGS[0]).name}: ${(CM.WINGS[thing.wing] || CM.WINGS[0]).smell}. (Space to take it; the main stair is still the way on)`,
          node: `${(CM.NODES[thing.band] || CM.NODES[0])[0].charAt(0).toUpperCase() + (CM.NODES[thing.band] || CM.NODES[0])[0].slice(1)}: something the alchemist would want. (Space to gather it)`,
          wingexit: "A stair down, back to the main way. (Space to take it)", wingstair_up: "The wing stair, back up. (Space to climb it)",
          building: thing.type === "building" ? `${(CM.TOWN_PLOTS[thing.id] || {}).name}${CM.plotLevel(this, thing.id) ? ` (level ${CM.plotLevel(this, thing.id)})` : " - " + CM.t("town.foundation")}. ${CM.t("town.door")}` : "",
          well: "The square's well, under its little roof, and the notice board beside it. (Space to look down it)",
          farm: this.villageLevel("farm") >= 1 ? "The farm's gate, and the rows beyond it. (Space to work the farm)" : "A fallow field, fenced long ago. (Space to look it over)",
          woodgate: fl.number === 0 ? "The west gate, and the trees beyond it. (Space to go out into the Deep Wood)" : "The gate back to the town. (Space to go through)",
          cave: thing.type === "cave" ? (thing.n === CM.dayOf(this) % 3 ? "A cave mouth, open and breathing cold. (Space to go down)" : "A cave mouth, choked with fallen rock today.") : "",
          caveexit: "The way out of the cave. (Space to climb out)", vein: thing.type === "vein" ? `A vein of ${CM.ORES[thing.ore].name} in the rock${thing.left < CM.VEIN_SWINGS ? ", part worked" : ""}. (Space to mine it, with a pick that will)` : "", hut: "A hut of turf and poles, smoke from the roof. (Space to knock)", shrine: "A shrine with its roof in the grass. (Space to read the wall)", burner: "A charcoal burner's mound, smoking. (Space to speak to him)",
          signpost: "A signpost, its boards weathered. (Space to read it)",
          cross: "The market cross, on its three steps: the Square's oldest stone. (Space to read what is cut in it)",
          villager: thing.type === "villager" ? `${(CM.TOWNSFOLK[thing.who % CM.TOWNSFOLK.length] || {}).who || "someone"}. (Space to pass the time of day)` : "" }[thing.type]);
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
      } else if (f.trap && !f.spent && this.alive()[0] && CM.scarred(this.alive()[0], "limp") && this.rnd.chance(0.5)) {
        f.known = true; this.say(`${this.alive()[0].name}'s bad leg stops short of the plate, as it always does.`);
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
    this.fellFrom = { floor: n, at: from.slice() };                       // (a grapnel climbs back to it)
    this.enterFloor(n + 1, "fall", from);
  },

  // ---- light ----
  burn() {
    if (this.floor && this.floor.number === 0) return;                   // (daylight: nothing burns in the town)
    if (this.floor && this.floor.number === -1 && !CM.isNight(this)) return;   // (nor in the Wood by day)
    if (this.spellLight > 0) {
      this.spellLight -= 1;
      if (this.spellLight === 0) this.say("The conjured light fades.");
    }
    if (this.lightOut) return;                                           // (a shaded light does not burn down)
    const l = this.light;
    if (l.kind === "lantern") {                                          // a lantern burns one step in two, and a flask of oil at a time
      if ((this.steps || 0) % 2 === 0) l.left -= 1;
      if (l.left === 60) this.say("The lantern burns low: it wants oil.");
      if (l.left <= 0) { const oil = this.bag.findIndex((i) => i.kind === "lampoil"); if (oil >= 0) { this.bag.splice(oil, 1); l.left = CM.LANTERN_OIL; this.say("The lantern gutters, and is filled from the pack."); } else { this.light = { kind: null, left: 0 }; this.say("The lantern goes out. Lamp oil would light it again."); this.emit("change"); } }
      return;
    }
    if (l.kind !== "torch") return;
    if ((this.steps || 0) % 2 === 1 && this.alive().some((h) => CM.trait(h, "pathfinder"))) return;   // (the Pathfinder banks the fire: every other step is free)
    const wet = this.floor && (this.floor.special === "wading" || this.floor.tide || (this.floor.number === -1 && CM.weather(this) === "rain" && this.floor.ford && this.floor.pos.join(",") === this.floor.ford.join(","))) && !this.alive().some((h) => (h.boots && h.boots.props && h.boots.props.waterwalk && !h.boots.unknown) || CM.equipped(h).some((it) => it.temper && it.props && it.props.waterwalk) || h.origin === "lowertown" || CM.setWorn(h) === "watch");
    if ((CM.partyProp(this.party, "torchSave") || (CM.mealOf(this).torch)) && (this.steps || 0) % 3 === 0) return;   // (of the Lantern, or a meal that lasts: every third step is free)
    l.left -= (wet || this.has("gloom") ? 2 : 1) + (this.asc("hungrydark") && (this.steps || 0) % 2 === 0 ? 1 : 0) + (this.alive().some((h) => CM.equipped(h).some((it) => it.props && it.props.cursed && it.props.curse === "dark")) ? 1 : 0);
    if (l.left === 40) this.say("Your torch is burning low.");
    if (l.left > 0) return;
    const spare = this.bag.findIndex((i) => i.kind === "torch");
    if (spare >= 0) {
      this.bag.splice(spare, 1);
      this.trace("stub", ...this.floor.pos);
      this.light = { kind: "torch", left: CM.TORCH_STEPS };
      this.say("Your torch gutters out. You light a fresh one.");
    } else {
      this.light = { kind: null, left: 0 };
      this.say("Your torch gutters out. The dark closes in.");
    }
  },

  inDark() { return this.floor && !(this.buffs && this.buffs.owleyes) ? this.floor.dark.includes(keyOf(this.floor.pos[0], this.floor.pos[1])) : false; },

  // how far the party can see, as a share of the depth's reach
  lightFactor() {
    if (this.floor && this.floor.number === 0) return CM.isNight(this) ? 0.8 : 1.3;   // (daylight, or the lanterns)
    if (this.floor && this.floor.number === -1) return (CM.isNight(this) ? (this.light.kind ? 0.55 : 0.35) : 1.2) * (CM.weather(this) === "mist" ? 0.8 : 1);   // (the Wood: daylight under the leaves, or a torch in the dark)
    const l = this.lightOut && !(this.spellLight > 0) ? {} : this.light, spell = this.spellLight > 0;   // (doused: as dark as no light at all)
    if (this.inDark()) return spell ? 0.7 : l.kind === "lantern" ? 0.45 : 0.25;
    let f = l.kind === "lantern" ? 1.15 : l.kind === "glow" ? 0.6 : l.kind === "torch" ? (l.left > 40 ? 1 : 0.6) : 0.22;
    if (spell) f = Math.max(f, 1.1);
    return f;
  },

  hasLight() { return (Boolean(this.light.kind) && !(this.lightOut && this.floor && this.floor.number >= 1)) || this.spellLight > 0 || Boolean(this.floor && this.floor.number === -1 && !CM.isNight(this)); },   // (the Wood by day is lit by the sky)

  // what the party can see goes on the automap: around them, and along the corridor they face - by torchlight
  look() {
    const fl = this.floor, size = fl.grid.length;
    const seen = new Set(fl.seen.map(([x, y]) => keyOf(x, y)));
    const [x, y] = fl.pos;
    seen.add(keyOf(x, y));
    const spell = this.spellLight > 0 || this.alive().some((h) => h.familiar === "owl");   // (a conjured light - or an owl - sees through a magical dark)
    if (this.inDark() && !spell && this.alive().some((h) => h.quirk === "nightsighted")) for (let dx = -1; dx <= 1; dx++) for (let dy = -1; dy <= 1; dy++) seen.add(keyOf(x + dx, y + dy));   // (the nightsighted: a step further)
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
    if (this.perch) { this.climbDown(); return; }
    { const t0 = this.floor.things[keyOf(this.floor.pos[0], this.floor.pos[1])];   // the tower's stair, the postern (61c-tower.js)
      if (t0 && t0.type === "towerstair") { this.climbTower(keyOf(this.floor.pos[0], this.floor.pos[1])); return; }
      if (t0 && t0.type === "postern") { this.postern(); return; } }
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
      let text = this.dream && typeof here.text === "number" && here.text >= 0 && here.text < CM.BOTTOM ? CM.DREAM.lore[here.text] : CM.loreText(here.text, this.seed, here.telling);
      const wall = text, lkey = CM.loreKey(here.text), L = CM.LORE_TEXT[lkey];
      if (!this.dream && L && (L.chapter === "root" || L.chapter === "endless")) {   // the Root's own voice: it knows the party
        text += " " + CM.rootAddress(this); this.story.rootSaid = (this.story.rootSaid || 0) + 1;
        if (this.awakened) text += " " + CM.LORE_AWAKENED[(this.story.rootSaid || 0) % CM.LORE_AWAKENED.length];
      }
      this.say("You read the carving on the wall.");
      this.markRead(lkey);
      this.remember("carving", wall, { key: lkey });                      // (the journal keeps the wall's own words; what the Root adds is for the moment)
      this.originLines(lkey);
      if ((this.tally.steps || 0) % 3 === 0) this.banter("carving");
      this.emit("lore", text);
      this.dirty = true;
      return;
    }
    if (thing && ["ghost", "hermit", "adventurer"].includes(thing.type)) { this.inUse = true; this.talk(thing, k); this.inUse = false; return; }
    if (thing && thing.type === "event") { this.askEvent(thing, k); return; }
    if (thing && thing.type === "vein") { this.mine(thing, k); return; }
    if (thing && thing.type === "woodgate") { if (fl.number === 0) { this.sound("door"); this.enterFloor(-1, "rope", CM.WOOD_GATE.slice()); this.say(`The west gate, and the Deep Wood beyond it: ${CM.hourWord(CM.hourOf(this))}, and ${CM.isNight(this) ? "the trees are a wall of dark" : "the light comes green through the leaves"}. The first glade is safe at any hour; the Wood is not.`); } else { this.sound("door"); this.enterFloor(0, "rope", CM.TOWN_AT.woodgate.slice()); this.say("Back through the gate: the lane, and the town."); } return; }
    if (thing && thing.type === "cave") { if (thing.n !== CM.dayOf(this) % 3) { this.say(CM.WOOD_LINES.caveShut); return; } this.sound("stairs"); this.enterFloor(CM.caveNumber(thing.n), "down"); this.say(`Down into the cave: ${["a short way under the roots", "deeper, and colder", "the hill's own dark, and something breathing at the end of it"][thing.n]}.`); return; }
    if (thing && thing.type === "caveexit") { this.sound("stairs"); this.enterFloor(-1, "rope", CM.woodCaveAt(this.seed, fl.cave).split(",").map(Number)); this.say("Up out of the cave, into the Wood."); return; }
    if (thing && thing.type === "hut") { if (CM.isNight(this)) { this.emit("talk", { title: "The hermit's hut", text: CM.WOOD_LINES.hut[1] }); this.say(CM.WOOD_LINES.hut[1]); return; } this.emit("hut", {}); this.say(CM.WOOD_LINES.hut[0]); return; }
    if (thing && thing.type === "burner") { this.burner(); return; }
    if (thing && thing.type === "farm") { this.farmDawns(); this.emit("farm", {}); this.say(this.villageLevel("farm") >= 1 ? `The farm: ${this.farm().rows.filter(Boolean).length} of ${this.farmRows()} rows planted, ${CM.season(this)}.` : "A fallow field in the first glade, waiting for the town's renown."); return; }
    if (thing && thing.type === "shrine") { this.emit("talk", { title: "The ruined shrine", text: CM.WOOD_LINES.shrine }); this.say(CM.WOOD_LINES.shrine); if (!thing.read) { thing.read = true; this.remember("carving", CM.WOOD_LINES.shrine, { key: "wood.shrine" }); this.saveRun(); } return; }
    if (thing && thing.type === "building") { this.tally.visited = this.tally.visited || []; if (!this.tally.visited.includes(thing.id)) this.tally.visited.push(thing.id); this.emit("building", thing.id); return; }
    if (thing && thing.type === "signpost") { this.say(`The signpost reads: ${thing.text}`); return; }
    if (thing && thing.type === "cross") { this.say("Cut into the cross's steps, worn almost smooth: HERE THE MARKET, BY THE KING'S LEAVE. Someone has scratched out the last three words and someone else has cut them again."); return; }
    if (thing && thing.type === "well") { this.well(); return; }
    if (thing && thing.type === "villager") { this.talkTownsfolk(thing); return; }
    if (thing && thing.type === "node") { this.gather(thing, k); return; }
    if (thing && thing.type === "strongbox") { this.openStrongbox(thing, k); return; }
    if (thing && thing.type === "peddler") { this.peddle(thing, k); return; }
    if (thing && thing.type === "rivals") { this.meetRivals(thing, k); return; }
    if (thing && thing.type === "remains") { this.takeRemains(thing, k); return; }
    if (thing && thing.type === "wingstair") { this.sound("stairs"); this.enterFloor(fl.number + 0.5, "down"); return; }
    if (thing && thing.type === "wingexit") { this.sound("stairs"); this.say("The wing's last stair comes out on the main stair below."); this.enterFloor(Math.floor(fl.number) + 1, "down"); return; }
    if (thing && thing.type === "wingstair_up") { this.sound("stairs"); this.enterFloor(Math.floor(fl.number), "upwing"); this.say("Back up the wing stair."); return; }
    if (thing && thing.type === "rope") {
      this.sound("stairs");
      this.enterFloor(fl.number - 1, "rope", thing.up);
      this.say("Hand over hand, you climb the rope back up to the pit's mouth.");
      return;
    }
    if (thing && thing.type === "chest" && thing.mimic) {               // a chest that isn't: it has teeth, and the hoard is in it
      const L = fl.number > CM.LAST_FLOOR ? CM.monsterLevel(fl.number) : fl.number, rnd = new CM.Random(CM.hashSeed(`${this.seed}:mimic:${fl.number}:${k}`));
      const group = [this.tune(CM.makeMonster(CM.MIMIC, L, rnd))];
      fl.things[k] = { type: "monsters", group, mimicOf: { gold: thing.gold || 0, items: thing.items || [] }, still: true };
      this.sound("roar"); this.say("The lid lifts by itself, and the chest is all mouth.");
      this.tally.mimics = (this.tally.mimics || 0) + 1;
      this.startCombat(k, fl.things[k], true);
      return;
    }
    if (thing && thing.type === "chest") {
      if (thing.trap && CM.partyProp(this.party, "thimble")) { this.say("The lid was trapped; the thimble turns the needle."); thing.trap = null; }
      if (thing.trap) {                                                   // a trapped lid: the Rogue may see to it (unless the opener is greedy)
        const rogue = this.alive().find((p) => p.cls === "Rogue" && this.canAct(p) && !(this.alive()[0] && this.alive()[0].quirk === "greedy"));
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
      delete fl.things[k]; this.trace("chest_open", ...k.split(",").map(Number));
      const gold = Math.floor(thing.gold * (this.has("rich") ? 2 : 1) * (this.asc("poorveins") ? 0.8 : 1) * (this.alive().some((h) => h.quirk === "greedy") ? 1.1 : 1));
      this.cheer(1);
      this.gold += gold; this.count("goldFound", gold);
      if (fl.number >= 3 && CM.hashSeed(`${this.seed}:homecoming:${fl.number}:${k}`) % CM.HOMECOMING.chest === 0) thing.items.push(CM.scroll("homecoming"));   // (one chest in twenty carries the way home)
      this.gain(thing.items, "chest");
      this.sound("chest"); this.makeNoise(CM.NOISE.chest);
      this.count("chests");
      this.emit("fx", { kind: "sparkle", at: [x, y] });
      const found = thing.items.map((i) => (i.unknown ? `${CM.baseName(i)} (unknown)` : `${i.name} (${CM.itemLabel(i)})`)).join(", ");
      this.say(`The chest creaks open: ${gold} gold` + (found ? `, ${found}.` : "."));
      if (this.gold >= 2000) this.achieve("hoarder");
      this.saveRun();
      this.emit("change");
    } else if (thing && thing.type === "ladder" && fl.number === 0 && (this.camps || []).length) {   // the shaft, from the town: down to the deepest camp reached
      this.sound("stairs");
      const n = Math.max(...this.camps), below = this.floorAt(n);
      this.leaveFloor(); this.floor = below; this.stock = null; this.recruits = null;
      const ladder = this.cellOf(below, "ladder"); if (ladder) below.pos = ladder.slice();
      this.setMode("camp"); this.emit("floor", below);
      this.say(`Down the shaft, past the floors you know, to the merchant's lantern beneath floor ${n}.`);
      this.saveRun(); this.emit("change");
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
      this.trace("glass", x, y);                                               // (the box's shards)
      this.emit("fx", { kind: "shatter" });
      this.saveRun();
      this.emit("change");
    } else if (here && here.type === "fountain") {
      this.inUse = true; this.drink(here); this.inUse = false;
    } else if (here && here.type === "altar") {
      this.inUse = true; this.kneel(here); this.inUse = false;
    } else if (!CM.isOpen(fl, x + dx, y + dy)) {                       // a wall before you: search it
      if (ahead && ahead.type === "secretstair" && !ahead.found) {
        ahead.found = true;
        fl.grid[y + dy][x + dx] = 0;
        fl.things[ak] = { type: "wingstair", wing: ahead.wing, secret: true };
        this.sound("grind");
        this.say("You press the stones... and a slab swings in on a stair going down, cut by no one who meant it to be found.");
        this.look(); this.emit("mesh"); this.dirty = true; this.emit("change");
        return;
      }
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
    else if (trap === "darts") { for (const p of this.alive()) p.hp = Math.max(1, p.hp - Math.max(1, Math.floor(p.max * 0.08))); this.say("Darts from every slit in the wall: everyone is stung."); }
    else if (trap === "floor") { if (this.floor.number < CM.BOTTOM || this.endless) { this.say("The flags tilt and are gone from under you."); this.fall(k.split(",").map(Number)); return; } for (const p of this.alive()) p.hp = Math.max(1, p.hp - Math.max(1, Math.floor(p.max * 0.1))); this.say("The floor drops a hand's breadth and stops: bruises."); }
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
    if (this.asc("dryfountains") && CM.hashSeed(`${this.seed}:dryrung:${this.floor.number}:${CM.keyOf(...this.floor.pos)}`) % 2 === 0) { this.say("Dry. Half the fountains are, this high on the ladder."); this.saveRun(); this.emit("change"); return; }
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
    if (this.floor.number === 0) return;                                 // (nothing wanders the town)
    if (this.floor.number === -1 && this.floor.nightWas !== CM.isNight(this)) this.refreshWood();   // (the Wood changes hands at dusk and dawn)
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
    if (fl.bait && (this.steps || 0) > fl.bait.until) { fl.bait = null; this.say("Something small has had the bait while you weren't looking."); }
    const baitDist = fl.bait ? CM.distances(fl.grid, fl.bait.at.split(",").map(Number), walk) : null;
    if (this.has("hordes")) for (const [k, t] of Object.entries(fl.things)) {   // hungry: a barred door beside a band is broken in three turns
      if (t.type !== "monsters") continue;
      const [x, y] = k.split(",").map(Number);
      for (const [dx, dy] of CM.DIRS) { const bf = fl.features[keyOf(x + dx, y + dy)]; if (bf && bf.type === "door" && bf.barred) { bf.hits = (bf.hits || 0) + 1; if (bf.hits >= CM.DOOR_BREAK) { bf.barred = 0; bf.open = true; bf.hits = 0; this.sound("grind"); this.say("Wood splinters somewhere close: a barred door has given."); } else this.say("Something heavy throws itself against a barred door."); } }
    }
    this.wakeSleepers();                                                 // (the light and the noise reach the lairs: 61b-lairs.js)
    const movers = Object.entries(fl.things).filter(([, t]) => t.type === "monsters" && !t.still && !t.asleep && !(t.fedUntil > (this.steps || 0)));
    this.rnd.shuffle(movers);
    for (const [k, t] of movers) {
      const [x, y] = k.split(",").map(Number);
      const d = dist.get(k), bd = baitDist ? baitDist.get(k) : undefined;
      let step = null;
      const options = CM.DIRS.map(([dx, dy]) => [x + dx, y + dy]).filter(([nx, ny]) => walk(nx, ny) && !fl.things[keyOf(nx, ny)]);
      if (t.flees && !(fl.number === -1 && CM.weather(this) === "wind")) {   // a deer, a boar: it runs from the party, and is hunted by walking into it (not in a wind: it does not smell them)
        if (d !== undefined && d <= 6) { const away = options.filter(([nx, ny]) => (dist.get(keyOf(nx, ny)) || 99) > d); if (away.length) { const [sx, sy] = this.rnd.pick(away); delete fl.things[k]; t.anim = { from: [x, y], at: performance.now() }; fl.things[keyOf(sx, sy)] = t; this.dirty = true; } }
        continue;
      }
      if (d === 1) {
        this.startCombat(k, t, true);
        return;
      }
      if (bd !== undefined && bd <= CM.BAIT_STEPS && bd > 0) {           // the bait: the nearest wanderers come to it, and not to you
        const nearer = options.filter(([nx, ny]) => baitDist.get(keyOf(nx, ny)) === bd - 1 && !(nx === px && ny === py));
        if (nearer.length) step = this.rnd.pick(nearer);
        if (!step && bd === 1) step = fl.bait.at.split(",").map(Number);
      } else if (d !== undefined && (d <= 7 || t.hunter || t.hunting > 0 || this.has("hunted")) && !(fl.number === -1 && CM.weather(this) === "mist" && d > 2)) {   // (mist in the Wood: the hunters find the party late)
        const nearer = options.filter(([nx, ny]) => dist.get(keyOf(nx, ny)) === d - 1 && !(nx === px && ny === py));
        if (nearer.length) step = this.rnd.pick(nearer);
      } else if (this.rnd.chance(0.3) && options.length) {
        step = this.rnd.pick(options.filter(([nx, ny]) => !(nx === px && ny === py)));
      }
      if (!step) continue;
      if (step[0] === px && step[1] === py) continue;
      delete fl.things[k];
      t.anim = { from: [x, y], at: performance.now() };
      const sk = keyOf(step[0], step[1]);
      fl.things[sk] = t;
      this.dirty = true;
      if (fl.bait && sk === fl.bait.at) this.takeBait(t, sk);
      const sf = fl.features[sk];
      if (sf && sf.type === "plate" && sf.set && !sf.spent) this.trapGroup(t, sf, sk);
    }
    this.emit("change");
  },
  // a lock without its key: a relic that opens anything; a Rogue of the grade's level; anyone with a pick, at a third of the
  // Rogue's chance (a master pick at the full chance, and a dwarven lock only to it); a pick breaks on a miss. "" when it gave.
  tryLock(f, k, what = "door") {
    const fl = this.floor, grade = f.grade || (f.grade = CM.lockGrade(this.seed, fl.number, k)), G = CM.LOCKS[grade];
    const relic = this.alive().flatMap((h) => CM.equipped(h)).find((it) => CM.OPENS_ANYTHING.includes(CM.baseIdOf(it)) && !it.unknown);
    if (relic) { this.sound("unlock"); this.say(`${CM.itemName(relic)} is held to ${G.name}, and the lock forgets itself.`); return ""; }
    const rogue = this.alive().find((h) => h.cls === "Rogue" && h.level >= G.rogue && this.canAct(h));
    const dexter = this.alive().filter((h) => this.canAct(h)).sort((a, b) => this.stat(b, "dex") - this.stat(a, "dex"))[0];
    const chance = (h) => CM.clamp(0.5 + CM.mod(this.stat(h, "dex")) * 0.1 + (CM.newMoon(this) ? 0.1 : 0) + (CM.festivalIs(this, "bells") ? 0.1 : 0), 0.1, 0.95);   // (a new moon: dark work goes better)
    if (rogue) {
      if (!this.rnd.chance(chance(rogue))) return `${rogue.name} works at ${G.name}... it won't give. Not yet.`;
      this.sound("unlock"); this.say(`${rogue.name} picks ${G.name}, and the ${what} gives.`); this.trace("pin", ...k.split(",").map(Number)); return "";
    }
    let row = this.bag.findIndex((i) => i.kind === "lockpick" && i.master);
    if (row < 0 && !G.master) row = this.bag.findIndex((i) => i.kind === "lockpick");
    if (row < 0 || !dexter) return G.master ? `The ${what} has ${G.name}: its key, a master pick, or a relic that opens anything.` : `The ${what} has ${G.name}. It needs a key, a Rogue of level ${G.rogue}, or a lockpick.`;
    const pick = this.bag[row], p = pick.master ? chance(dexter) : chance(dexter) / 3;
    this.countUse("lockpick");
    if (!this.rnd.chance(p)) { this.bag.splice(row, 1); this.tally.picksBroken = (this.tally.picksBroken || 0) + 1; return `${dexter.name} tries ${G.name} with the ${pick.name.toLowerCase()}... and it snaps in the keyhole.`; }
    this.sound("unlock"); this.say(`${dexter.name} tries ${G.name} with the ${pick.name.toLowerCase()}, and feels it turn.`); this.trace("pin", ...k.split(",").map(Number)); return "";
  },
  // a band of monsters walks onto a trap the party set: it takes the trap, and the party hears it
  trapGroup(t, f, k) {
    const fl = this.floor, trap = f.trap, live = () => t.group.filter((m) => m.hp > 0);
    f.spent = true; f.set = false; this.tally.trapped = (this.tally.trapped || 0) + 1; this.sound("trap");
    const bite = (m, share) => { m.hp = Math.max(0, m.hp - Math.max(1, Math.floor(m.max * share))); };
    if (trap === "darts") for (const m of live()) bite(m, 0.25);
    else if (trap === "gas") for (const m of live()) bite(m, 0.2);
    else if (trap === "blade") { const m = live()[0]; if (m) bite(m, 0.5); }
    else if (trap === "needle") for (const m of live()) { bite(m, 0.1); m.bleeding = Math.max(m.bleeding || 0, 3); }
    else if (trap === "alarm") t.hunter = true;
    else if (trap === "floor") { delete fl.things[k]; this.say("A crash, a long cry, and a quiet: the floor you rigged has taken them down a level."); this.emit("change"); return; }
    t.group = live();
    const where = trap === "alarm" ? "A bell rings behind you: they know where you are now." : t.group.length ? `A cry from behind you: ${CM.TRAPS[trap]} has caught a band of ${t.group[0].name}s.` : `A cry from behind you, then nothing: ${CM.TRAPS[trap]} has finished a band of ${t.group.length ? t.group[0].name : "something"}s.`;
    if (!t.group.length) { delete fl.things[k]; this.count("kills", 1); }
    this.say(where);
  },
  // a band reaches the bait: it eats, and stays with it a while; poisoned, it is the worse for it
  takeBait(t, k) {
    const fl = this.floor, bait = fl.bait; fl.bait = null;
    if (bait.poisoned) { for (const m of t.group) { m.hp = Math.max(0, m.hp - Math.max(1, Math.floor(m.max * 0.4))); m.bleeding = Math.max(m.bleeding || 0, 3); } t.group = t.group.filter((m) => m.hp > 0); this.tally.baited = (this.tally.baited || 0) + 1; if (!t.group.length) { delete fl.things[k]; this.count("kills", 1); this.say("Wet sounds from where you left the bait, and then none: it was poisoned, and they ate it all."); return; } this.say("Retching from where you left the bait: it was poisoned, and they ate it."); return; }
    t.fedUntil = (this.steps || 0) + CM.BAIT_STEPS; this.tally.baited = (this.tally.baited || 0) + 1;
    this.say("Snarling over the bait behind you: whatever it is, it has stopped to eat.");
  },
  // the party rests at a barred door: a third of the camp's rest, once a floor, for a ration
  restAtDoor(f) {
    const fl = this.floor;
    if (fl.restedAtDoor) return "The party has rested on this floor already; the next door is on the next floor.";
    const ration = this.bag.findIndex((i) => i.kind === "ration");
    if (ration < 0) return "A rest at the door takes a ration to share, and there is none.";
    this.bag.splice(ration, 1); fl.restedAtDoor = true; this.countUse("doorrest");
    for (const m of this.alive()) { m.hp = Math.min(m.max, m.hp + Math.ceil(m.max / 3)); m.mp = Math.min(m.maxmp, m.mp + Math.ceil(m.maxmp / 3)); }
    this.fed = Math.min(this.fed || 0, 0); this.sound("heal");
    this.say("With the door barred the party sits down against it, eats, and sleeps in turns. Not the camp, but something.");
    return "";
  },
  // a vein mined: the best pick in the pack that mines the ore, a point a swing, a chunk a swing (silver in the Dwarven Halls two;
  // the Artificer one more), three swings a vein and it is spent for the run; a swing is five minutes, and it is loud
  mine(thing, k) {
    const fl = this.floor, ore = thing.ore, row = CM.bestPick(this.bag, ore);
    if (row < 0) { const any = this.bag.find((i) => i.kind === "pick"); this.say(any ? ((any.points || 0) <= 0 ? `The ${any.name} is blunt: the forge in town puts a point back on it.` : `The ${any.name} will not bite ${CM.ORES[ore].name}: it wants a better pick.`) : `A vein of ${CM.ORES[ore].name}, and no pick to mine it with.`); return; }
    this.logAct("mine");
    const pick = this.bag[row]; pick.points -= 1; this.clock = (this.clock || 0) + CM.SWING_MINUTES;
    let n = 1; if (ore === "silver" && CM.themeIndex(fl.number) === 2 && fl.number >= 1) n += 1; if (this.alive().some((h) => h.cls === "Artificer" || h.second === "Artificer")) n += 1;
    const got = []; for (let i = 0; i < n; i++) got.push(CM.oreChunk(ore)); this.gain(got, "vein"); this.tally.mined = (this.tally.mined || 0) + n; this.countUse("mine");
    thing.left -= 1; if (thing.left <= 0) delete fl.things[k];
    this.sound("grind"); this.say(`${pick.name} into the rock: ${CM.plural(n, CM.ORES[ore].name + " chunk")}${thing.left > 0 ? `, and more in the vein (${thing.left} swing${thing.left === 1 ? "" : "s"})` : ", and the vein is worked out"}.${pick.points <= 0 ? ` The ${pick.name} is blunt.` : ""}`);
    this.noise(); this.makeNoise(CM.NOISE.mine); this.dirty = true; this.saveRun(); this.emit("change");
  },
  noise() {                                                              // a swing rings down the halls: the nearest band comes a square closer
    const fl = this.floor, dist = CM.distances(fl.grid, fl.pos, (x, y) => CM.passable(fl, x, y)); let nearest = null;
    for (const [k, t] of Object.entries(fl.things)) { if (t.type !== "monsters" || t.still) continue; const d = dist.get(k); if (d !== undefined && d > 1 && (!nearest || d < nearest.d)) nearest = { d, k, t }; }
    if (!nearest) return;
    const [x, y] = nearest.k.split(",").map(Number), step = CM.DIRS.map(([dx, dy]) => [x + dx, y + dy]).find(([nx, ny]) => CM.passable(fl, nx, ny) && !fl.things[keyOf(nx, ny)] && dist.get(keyOf(nx, ny)) === nearest.d - 1);
    if (step) { delete fl.things[nearest.k]; fl.things[keyOf(step[0], step[1])] = nearest.t; this.say("Something down the hall heard that."); }
  },
  // the charcoal burner: deadwood in, two charcoal out; or a charcoal for a coin; by day only
  burner() {
    if (CM.isNight(this)) { this.emit("talk", { title: "The charcoal burner", text: CM.WOOD_LINES.burner[1] }); this.say(CM.WOOD_LINES.burner[1]); return; }
    const wood = this.bag.map((it, i) => [it, i]).filter(([it]) => it.kind === "ingredient" && it.ingredient === "deadwood");
    if (wood.length) { for (const [, i] of wood.reverse()) this.bag.splice(i, 1); const out = []; for (let i = 0; i < wood.length * 2; i++) out.push(CM.charcoal()); this.gain(out, "burner"); this.say(`The burner takes the deadwood into his mound and hands back ${CM.plural(out.length, "charcoal")}. "The forge eats it one a bar."`); this.saveRun(); this.emit("change"); return; }
    if (this.gold >= CM.CHARCOAL_PRICE) { this.gold -= CM.CHARCOAL_PRICE; this.spend("burner", CM.CHARCOAL_PRICE); this.gain([CM.charcoal()], "burner"); this.say(`A charcoal for ${CM.CHARCOAL_PRICE} gold. "Bring deadwood and it's for nothing."`); this.saveRun(); this.emit("change"); return; }
    this.emit("talk", { title: "The charcoal burner", text: CM.WOOD_LINES.burner[0] }); this.say(CM.WOOD_LINES.burner[0]);
  },
  // the Wood changes hands at dusk and dawn: the day's deer and boar go in, the night's wolves, bear and bandits come out (by the seed, the day and the hour)
  refreshWood() {
    const fl = this.floor; if (!fl || fl.number !== -1) return;
    const night = CM.isNight(this), newDay = fl.woodDay !== CM.dayOf(this); fl.nightWas = night; fl.woodDay = CM.dayOf(this);
    fl.frozen = CM.weather(this) === "snow"; if (fl.frozen && newDay) this.say("Snow in the Wood: the river is frozen hard enough to cross anywhere, and the beasts have left tracks.");
    for (const [k, t] of Object.entries(fl.things)) if (t.type === "monsters" && t.wood && (newDay || t.wood !== (night ? "night" : "day"))) delete fl.things[k];   // (a new day, or the other half of it: other beasts)
    const have = Object.values(fl.things).filter((t) => t.type === "monsters" && t.wood).length;
    const rnd = new CM.Random(CM.hashSeed(`${this.seed}:woodbands:${CM.dayOf(this)}:${night ? 1 : 0}`)), bands = CM.woodBands(night, CM.fullMoon(this));
    const cells = []; for (let y = 1; y < fl.grid.length - 1; y++) for (let x = 1; x < fl.grid.length - 1; x++) { const k = `${x},${y}`; if (fl.grid[y][x] === 0 && !fl.things[k] && !fl.features[k] && !CM.woodSafe(fl, x, y) && Math.abs(x - CM.WOOD_GATE[0]) + Math.abs(y - CM.WOOD_GATE[1]) >= 9 && !(Math.abs(x - fl.pos[0]) + Math.abs(y - fl.pos[1]) <= 3)) cells.push(k); }
    for (let i = have; i < 4 && cells.length; i++) {
      const kinds = bands[rnd.int(0, bands.length - 1)], level = night ? 5 : 3, group = kinds.map((n) => this.tune(CM.makeMonster(CM.monsterKind(n), level, rnd)));
      for (const m of group) m.gold = Math.floor(m.gold / 4);
      if (night && CM.fullMoon(this) && kinds.length === 4) { group[0].name = "The Great Wolf"; group[0].elite = "hulking"; group[0].max = Math.round(group[0].max * 1.6); group[0].hp = group[0].max; group[0].atk += 3; }
      const k = cells.splice(rnd.int(0, cells.length - 1), 1)[0];
      fl.things[k] = { type: "monsters", group, wood: night ? "night" : "day", flees: Boolean(CM.monsterKind(kinds[0]).flees), hunter: night };
    }
    this.dirty = true;
  },
  // the pack's weight against what the party can carry: 1 is the line; over it costs, half again over it there is no running
  overweight() { return CM.bagWeight(this.bag) / CM.carryCap(this.party); },
  // nothing burning and a torch in the pack: light it (a torch found after the last went out is lit when it's wanted)
  lightSpare() {
    if (this.lightOut) return;                                           // (shaded on purpose: not lit behind the party's back)
    if (this.light && this.light.kind) return false;
    if (this.floor && (this.floor.number === 0 || (this.floor.number === -1 && !CM.isNight(this)))) return false;   // (daylight: no need)
    const spare = this.bag.findIndex((i) => i.kind === "torch");
    if (spare < 0) return false;
    this.bag.splice(spare, 1);
    this.light = { kind: "torch", left: CM.TORCH_STEPS };
    this.say("In the dark, a hand finds a torch in the pack, and lights it.");
    this.emit("change");
    return true;
  },
  // how much slower the party walks for its pack: 1 at or under the line, up to three times at twice the line and beyond
  walkPace() { const o = this.overweight(); return o <= 1 ? 1 : Math.min(3, 1 + (o - 1) * 2); },
  // the warning, once each time the pack goes over the line, with the way out
  warnWeight() {
    const o = this.overweight();
    if (o <= 1) { this.weightWarned = false; return; }
    if (this.weightWarned) return;
    this.weightWarned = true;
    const scroll = this.bag.some((i) => i.kind === "scroll" && i.spell === "homecoming" && !i.back);
    this.say(`The pack is over what the party can carry (${CM.bagWeight(this.bag)} of ${CM.carryCap(this.party)}): it walks slowly until it is lighter. A merchant buys - at the camps below every fifth floor, and the Merchant's House in town${scroll && this.floor && this.floor.number >= 1 ? "; a Scroll of Homecoming in the pack takes the party home to sell, and back to this square" : ""}.`);
    this.emit("heavy", o);
  },
  weightWord() { const o = this.overweight(); return o >= CM.OVERWEIGHT_RUN ? CM.t("hud.overloaded") : o > 1 ? CM.t("hud.heavy") : ""; },
  // the dwarves' pick: the nearest hidden door or stair on the floor opens without searching, and the pick breaks
  usePick(row) {
    const fl = this.floor, hidden = Object.entries(fl.features).filter(([, f]) => (f.type === "secret" || f.type === "secretstair") && !f.found);
    if (!hidden.length) return "The pick finds nothing on this floor worth breaking a wall for.";
    const dist = CM.distances(fl.grid, fl.pos), near = hidden.sort((a, b) => (dist.get(a[0]) || 999) - (dist.get(b[0]) || 999))[0], [k, f] = near, [x, y] = k.split(",").map(Number);
    f.found = true; f.known = true; fl.grid[y][x] = 0;
    if (f.type === "secretstair") fl.things[k] = { type: "wingstair", wing: f.wing, secret: true };
    if (!fl.seen.some(([sx, sy]) => sx === x && sy === y)) fl.seen.push([x, y]);
    const pick = this.bag[row]; if (pick && pick.points !== undefined) { if (pick.points < CM.SECRET_POINTS) return `The ${pick.name} is too blunt for a wall: the forge in town puts a point back on it.`; pick.points -= CM.SECRET_POINTS; } else this.bag.splice(row, 1);
    this.countUse("pick");
    this.sound("grind"); this.say(`The pick goes into the wall where the dwarves' marks say${pick && pick.points !== undefined ? ", and comes out blunter" : ", and comes out in two pieces"}: a hidden ${f.type === "secretstair" ? "stair" : "door"} stands open.`);
    this.look(); this.emit("mesh"); this.dirty = true; this.emit("change");
    return "";
  },
  // the grapnel: back up the pit the party fell down, to the floor above, where it fell from
  useGrapnel() {
    const from = this.fellFrom;
    if (!from || from.floor !== this.floor.number - 1) return "The grapnel wants a pit above you that you came down. There is none.";
    this.fellFrom = null; this.countUse("grapnel");
    this.say("The grapnel bites on the pit's lip above, and the party goes up the rope, hand over hand.");
    this.enterFloor(from.floor, "rope", from.at);
    const f = this.floor.features[keyOf(...from.at)]; if (f && f.type === "pit") f.roped = true;
    return "";
  },
});
}

// ---- travel: the party walks by itself - to a square clicked on the automap, or to the nearest unexplored one (X) -
// over the squares it knows, and stops when something is close, something is underfoot, something new comes into
// view, or the light fails. The window takes one step each time the view is still; any key or click stops it. ----
{
const keyOf = CM.keyOf;
const WATCHED = ["chest", "key", "ghost", "hermit", "adventurer", "phylactery", "bones", "rope", "event", "strongbox", "boxkey", "peddler", "rivals", "remains", "wingstair", "node", "building", "well", "villager", "woodgate", "cave", "caveexit", "hut", "shrine", "burner", "vein", "farm"];
const SEEN_AS = { chest: "a chest", key: "a key on the floor", ghost: "a pale shape in the air", hermit: "someone in a nest of rags", adventurer: "someone bound against the wall", phylactery: "a cold box", bones: "bones on the floor", rope: "a rope from above",
  event: "something strange", node: "something growing", building: "a door", well: "the well", villager: "one of the townsfolk", woodgate: "the gate", cave: "a cave mouth", vein: "ore in the rock", caveexit: "the way out", hut: "a hut", farm: "the farm's gate", shrine: "a ruined shrine", burner: "a smoking mound", strongbox: "an iron strongbox", boxkey: "a heavy key on the floor", peddler: "a peddler with a lantern", rivals: "other adventurers", remains: "the remains of a party", wingstair: "a second stair down" };
Object.assign(CM.Game.prototype, {
  // a way over the squares the party knows, from where it stands to (x, y): the steps, or null
  pathTo(x, y) {
    const fl = this.floor, seen = new Set(fl.seen.map(([a, b]) => keyOf(a, b))), goal = keyOf(x, y), start = keyOf(fl.pos[0], fl.pos[1]);
    const picks = this.alive().some((h) => h.cls === "Rogue" && h.level >= CM.PICK_LOCK_LEVEL) || this.bag.some((i) => i.kind === "lockpick"), key = this.hasKey() >= 0;
    const ok = (cx, cy) => {
      const k = keyOf(cx, cy);
      if (!seen.has(k) || !CM.isOpen(fl, cx, cy)) return false;
      const f = fl.features[k];
      if (f && f.type === "pit" && !f.roped) return false;                                       // (never into a pit by itself: walk there yourself, rope or no)
      if (f && ["trapdoor", "teleporter", "spinner", "spores", "vents", "bonepiles"].includes(f.type) && f.known) return false;
      if (f && f.type === "gate" && !f.open) return false;
      if (f && f.type === "door" && !f.open && (f.riddle !== undefined || (f.locked && !key && !picks))) return false;
      const t = fl.things[k];                                                                     // (what stands in a square is walked round, unless it is where the walk goes)
      if (t && k !== goal && ["well", "signpost", "cross", "hut", "shrine", "burner", "cave", "farm", "node", "vein", "building"].includes(t.type)) return false;   // (people are passed, and stop the walk to talk)
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
    if (this.perch) this.climbDown();
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
    if (!this.hasLight()) this.lightSpare();                            // (a torch in the pack and none burning: light it, and walk on)
    if (!this.hasLight()) return stop("The dark. You stop, and feel for the wall.");
    if (thing && !["key", "bones", "boxkey"].includes(thing.type)) return stop(null);
    if (f && ((f.type === "fountain" && !f.used) || (f.type === "altar" && !f.used) || (f.type === "lever" && !f.pulled) || (f.type === "carving" && !f.read))) return stop(null);
    if (this.monstersNear(3)) return stop("Something is close. You stop.");
    const now = this.thingsInView();
    for (const key of now) if (!t.known.has(key)) { const what = fl.things[key]; return stop(`You see ${SEEN_AS[what.type] || "something"}. You stop.`); }
    if (!t.path.length && !t.explore) return stop(null);
    return true;
  },
  // the dungeon behind you shifts, now and then: a door you left shut opens on a floor above, or a peddler sets up by a
  // fountain there, once a run (never the floor you are on; the floor's save is worked out afresh)
  changeBehind() {
    const above = Object.keys(this.floors).map(Number).filter((n) => n >= 1 && n < Math.floor(this.floor.number) && n % 1 === 0);
    if (!above.length) return;
    const n = above[this.rnd.int(0, above.length - 1)], fl = this.floors[n];
    const doors = Object.values(fl.features).filter((f) => f.type === "door" && !f.open && !f.locked && !f.barred && f.riddle === undefined);
    if (doors.length && this.rnd.chance(0.6)) { this.rnd.pick(doors).open = true; this.say(`Somewhere above, on floor ${n}, a door you left shut swings open.`); }
    else if (!this.behind) {
      const fountain = Object.keys(fl.features).find((k) => fl.features[k].type === "fountain");
      const spot = fountain && CM.DIRS.map(([dx, dy]) => `${Number(fountain.split(",")[0]) + dx},${Number(fountain.split(",")[1]) + dy}`).find((k) => { const [x, y] = k.split(",").map(Number); return CM.passable(fl, x, y) && !fl.things[k] && !fl.features[k]; });
      if (spot) { fl.things[spot] = { type: "peddler", stock: null }; this.behind = n; this.say(`Somewhere above, on floor ${n}, a peddler has set up by the fountain.`); }
    } else return;
    delete this.deltas[n];
    this.dirty = true;
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
  // a node gathered: the band's ingredient, one time in five its rarer one; the Druid and the Ranger take two, the Artificer two of ore
  gather(thing, k) {
    const band = thing.band === undefined ? CM.themeIndex(this.floor.number) : thing.band;
    const common = Object.keys(CM.INGREDIENTS).find((id) => CM.INGREDIENTS[id].band === band && !CM.INGREDIENTS[id].rare), rare = Object.keys(CM.INGREDIENTS).find((id) => CM.INGREDIENTS[id].band === band && CM.INGREDIENTS[id].rare);
    const hs = CM.hashSeed(`${this.seed}:gather:${this.floor.number}:${k}`), id = rare && hs % 5 === 0 ? rare : common;
    let n = 1;
    if (band === -1 && CM.festivalIs(this, "greening")) n += 1;             // (the Greening: the Wood green to the top)
    if (band === -1 && CM.season(this) === "summer" && (id === "honey" || id === "berries")) n += 1;   // (summer: the hive full, the brambles heavy)
    if (this.alive().some((h) => h.cls === "Druid" || h.cls === "Ranger")) n += 1;
    if (CM.ORE_BANDS.includes(band) && this.alive().some((h) => h.cls === "Artificer")) n += 1;
    const got = []; for (let i = 0; i < n; i++) got.push(CM.ingredient(id));
    delete this.floor.things[k];
    this.gain(got, "event"); this.count("gathered", n);
    this.sound("coin");
    this.say(`${(CM.NODES[band] || CM.NODES[0])[0].charAt(0).toUpperCase() + (CM.NODES[band] || CM.NODES[0])[0].slice(1)}: ${n > 1 ? `${n} of ` : ""}${CM.INGREDIENTS[id].name}${CM.INGREDIENTS[id].rare ? " - a rare thing" : ""}.`);
    this.saveRun(); this.emit("change");
  },
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
    // the one of them with the most levels stands over the bones, and wants them laid to rest
    const mine = (this.memorial || []).filter((m) => m.seed === this.seed && m.floor === fl.number && past.names.includes(m.name)).sort((a, b) => (b.level || 0) - (a.level || 0))[0]
      || { name: past.names[0], cls: "adventurer", level: 0 };
    const cells = [...CM.distances(fl.grid, at, (x, y) => CM.passable(fl, x, y))].filter(([k, d]) => d >= 1 && d <= 3 && free(...k.split(",").map(Number))).map(([k]) => k).sort();
    if (!cells.length) return;
    const gk = cells[CM.hashSeed(`${this.seed}:ownghost:${fl.number}`) % cells.length];
    if (Object.values(fl.things).some((t) => t.type === "ghost" && t.own)) return;
    fl.things[gk] = { type: "ghost", own: { name: mine.name, cls: mine.cls, level: mine.level || 0, epitaph: mine.epitaph || "" }, request: "bones", asked: false, line: CM.hashSeed(`${this.seed}:ownline:${fl.number}`) % CM.OWN_LINES.length };
    const [gx, gy] = gk.split(",").map(Number);
    const far = Object.keys(Object.fromEntries(CM.distances(fl.grid, at, (x, y) => CM.passable(fl, x, y)))).filter((k) => { const [x, y] = k.split(",").map(Number); return Math.abs(x - gx) + Math.abs(y - gy) >= 6 && free(x, y); }).sort();
    if (far.length) fl.things[far[CM.hashSeed(`${this.seed}:ownbones:${fl.number}`) % far.length]] = { type: "bones", ghost: gk }; else fl.things[gk].request = "story";
  },
  takeRemains(thing, k) {
    this.remainsFound = (this.remainsFound || []).concat(thing.id);
    delete this.floor.things[k];
    if (thing.item) this.gain([thing.item], "remains");
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
    if (row < 0) {
      const note = this.tryLock(thing, k, "strongbox");
      if (note !== "") { this.sound("bump"); this.say(`The strongbox is bolted to the floor and locked. Its key lies on floor ${thing.from}${this.bag.some((i) => i.kind === "boxkey") ? " - not the one you carry" : ""}. ${note || ""}`.trim()); return; }
    } else this.bag.splice(row, 1);
    thing.opened = true;
    const rnd = new CM.Random(CM.hashSeed(`${this.seed}:strongbox:${this.floor.number}`)), gold = 60 * this.floor.number;
    const it = rnd.chance(0.4) ? CM.trinket(rnd.pick(Object.keys(CM.TRINKETS))) : CM.affix(CM.makeItem(this.floor.number + 3, rnd, rnd.pick(["weapon", "armor", "helm", "shield", "ring", "amulet"])), 99, rnd);
    it.unknown = false;
    this.gold += gold; this.count("goldFound", gold); this.gain([it], "strongbox");
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
      thing.stock = [gear, { name: "Greater Healing Potion", kind: "greaterheal", power: 2 * (20 + L * 3), value: 90 }, CM.oil(rnd.pick(["fire", "frost", "holy"])), CM.scroll("mapping"), CM.ingredient(rnd.pick(Object.keys(CM.INGREDIENTS))), Object.assign(CM.trinket(rnd.pick(Object.keys(CM.TRINKETS))), { value: 220 })];
      thing.stock[3].value = 60;
      if (this.asc("nogreater")) thing.stock = thing.stock.filter((i) => i.kind !== "greaterheal");
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

