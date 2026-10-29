"use strict";
// The game itself, with no screen in it: the party, the floor they're on, the fight they're in, the camp, the bag,
// saving as it goes, the Hall of Fame. The window (70-ui.js) listens to its events and draws; the tests drive it
// straight. Everything here was the old Python game's rules, kept to the number.
CM.Game = class {
  constructor() {
    this.listeners = {};
    this.mode = "title";                 // title, explore, combat, camp
    this.titleNote = "";
    this.messages = [];
    this.party = []; this.bag = []; this.gold = 0; this.floor = null; this.foes = []; this.foeKey = null;
    this.seed = "";
    this.stock = null; this.shopping = false;
    this.rnd = new CM.Random(Math.floor(Math.random() * 4294967296));
    this.fame = CM.store.get("fame", []);
    this.settings = Object.assign({ sound: true, volume: 0.6, smooth: true, fps: false }, CM.store.get("settings", {}));
    this.lastRun = CM.store.get("run", null);        // a run left part way, to continue
  }

  // ---- events: change (redraw), message, mode, floor, moved, turned, fx, sound ----
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
    const data = { party: this.party, bag: this.bag, gold: this.gold, floor: this.floor, mode: this.mode, seed: this.seed,
      saved: new Date().toISOString() };
    this.lastRun = data;
    CM.store.set("run", data);
  }

  canContinue() { return Boolean(this.lastRun && this.lastRun.floor && this.lastRun.party); }

  continueRun() {
    const d = this.lastRun;
    if (!this.canContinue()) return false;
    this.party = d.party; this.bag = d.bag || []; this.gold = d.gold || 0; this.floor = d.floor;
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
    let took = [];
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

  // ---- starting ----
  newGame(seed) {
    this.seed = (seed || "").trim() || CM.randomSeed();
    this.party = CM.newParty();
    this.bag = CM.startingBag(this.seed);
    this.gold = 30;
    this.messages = [];
    this.titleNote = "";
    this.enterFloor(1);
    this.say("Four adventurers climb down into the dark. Somewhere below, the Lich King stirs.");
  }

  enterFloor(number) {
    this.floor = CM.makeFloor(number, this.seed);
    this.setMode("explore");
    this.look();
    this.emit("floor", this.floor);
    this.saveRun();
    this.say(`Floor ${number}.` + (number === CM.LAST_FLOOR ? "  A terrible cold rises from somewhere ahead..." : ""));
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

  move(rel) {
    if (this.mode !== "explore") return false;
    const fl = this.floor;
    const [dx, dy] = CM.DIRS[(fl.facing + rel) % 4];
    const x = fl.pos[0] + dx, y = fl.pos[1] + dy;
    if (y < 0 || y >= fl.grid.length || x < 0 || x >= fl.grid.length || fl.grid[y][x]) {
      this.sound("bump");
      this.say("Ouch! A solid wall.");
      return false;
    }
    const thing = fl.things[`${x},${y}`];
    if (thing && (thing.type === "monsters" || thing.type === "boss")) {
      this.startCombat(`${x},${y}`, thing);
      return false;
    }
    fl.pos = [x, y];
    this.sound("step");
    this.look();
    this.emit("moved", x, y);
    if (thing) this.say({ chest: "A chest sits here. (Space to open it)", ladder: "A ladder leads down into the dark. (Space to climb down)" }[thing.type]);
    this.emit("change");
    return true;
  }

  // what the party can see goes on the automap: around them, and along the corridor they face
  look() {
    const fl = this.floor, size = fl.grid.length;
    const seen = new Set(fl.seen.map(([x, y]) => `${x},${y}`));
    const [x, y] = fl.pos;
    for (let dx = -1; dx <= 1; dx++) for (let dy = -1; dy <= 1; dy++) seen.add(`${x + dx},${y + dy}`);
    const [fx, fy] = CM.DIRS[fl.facing];
    for (let d = 1; d < 5; d++) {
      const cx = x + fx * d, cy = y + fy * d;
      seen.add(`${cx},${cy}`); seen.add(`${cx + fy},${cy + fx}`); seen.add(`${cx - fy},${cy - fx}`);
      if (cy < 0 || cy >= size || cx < 0 || cx >= size || fl.grid[cy][cx]) break;
    }
    fl.seen = [...seen].map((k) => k.split(",").map(Number)).filter(([a, b]) => a >= 0 && a < size && b >= 0 && b < size);
  }

  use() {
    if (this.mode !== "explore") return;
    const fl = this.floor, key = `${fl.pos[0]},${fl.pos[1]}`, thing = fl.things[key];
    if (!thing) { this.say("There's nothing here to use."); return; }
    if (thing.type === "chest") {
      delete fl.things[key];
      this.gold += thing.gold;
      this.bag.push(...thing.items);
      this.sound("chest");
      const found = thing.items.map((i) => i.name).join(", ");
      this.say(`The chest creaks open: ${thing.gold} gold` + (found ? `, ${found}.` : "."));
      this.saveRun();
      this.emit("change");
    } else if (thing.type === "ladder") {
      this.sound("stairs");
      if (CM.CAMP_AFTER.includes(fl.number)) {
        this.setMode("camp");
        this.saveRun();
        this.say(`Halfway down a long shaft, a lantern glows: a merchant's camp beneath floor ${fl.number}. Rest, trade, and see to the fallen.`);
      } else {
        this.enterFloor(fl.number + 1);
      }
    }
  }

  // ---- fighting ----
  startCombat(key, thing) {
    this.foes = thing.group;
    this.foeKey = key;
    this.setMode("combat");
    this.sound("monster");
    const names = {};
    for (const m of this.foes) names[m.name] = (names[m.name] || 0) + 1;
    this.say("Monsters! " + Object.entries(names).map(([k, n]) => CM.plural(n, k)).join(", ") + " attack!");
  }

  alive() { return this.party.filter((m) => m.hp > 0); }
  living() { return this.foes.filter((m) => m.hp > 0); }

  damage(atk, power, df) {
    return Math.max(1, atk + power + this.rnd.int(0, Math.max(1, Math.floor((atk + power) / 2))) - Math.floor(df / 2));
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
      if (action === "cast" && hero.cls === "Mage" && hero.mp >= 4) {
        hero.mp -= 4;
        this.sound("spell");
        const dmg = 8 + hero.level * 4;
        for (const m of foes) { m.hp -= dmg; this.emit("fx", { kind: "hit", foe: m, amount: dmg, spell: true }); }
        this.say(`The Mage hurls a fireball! ${dmg} damage to every foe.`);
      } else if (action === "cast" && hero.cls === "Cleric" && hero.mp >= 3) {
        hero.mp -= 3;
        const target = this.alive().reduce((a, b) => (a.hp / a.max <= b.hp / b.max ? a : b));
        const heal = 12 + hero.level * 4;
        target.hp = Math.min(target.max, target.hp + heal);
        this.sound("heal");
        this.say(`The Cleric prays: the ${target.cls} is healed by ${heal}.`);
      } else {
        const target = rnd.pick(foes);
        if (rnd.chance(0.88)) {
          let dmg = this.damage(hero.atk, hero.weapon.power, target.df);
          if (hero.cls === "Rogue" && rnd.chance(0.25)) {
            dmg *= 2;
            this.say(`The Rogue strikes a weak spot! ${target.name} takes ${dmg}.`);
          } else {
            this.say(`The ${hero.cls} hits the ${target.name} for ${dmg}.`);
          }
          target.hp -= dmg;
          this.emit("fx", { kind: "hit", foe: target, amount: dmg });
          this.sound("hit");
        } else {
          this.say(`The ${hero.cls} misses.`);
          this.emit("fx", { kind: "miss", foe: target });
        }
      }
    }
    for (const m of this.foes) if (m.hp <= 0 && !m.dead) { m.dead = true; this.emit("fx", { kind: "die", foe: m }); }
    if (!this.living().length) { this.wonFight(); return; }
    for (const m of this.living()) {                                     // the monsters' turn
      const heroes = this.alive();
      if (!heroes.length) break;
      const target = rnd.pick(heroes);
      if (rnd.chance(0.8)) {
        const dmg = this.damage(Math.floor(m.atk / 2), 0, target.df + target.armor.power * 2);
        target.hp -= dmg;
        this.sound("hurt");
        this.emit("fx", { kind: "hurt", hero: target, amount: dmg, foe: m });
        this.say(`The ${m.name} hits the ${target.cls} for ${dmg}.` + (target.hp <= 0 ? `  The ${target.cls} falls!` : ""));
      } else {
        this.say(`The ${m.name} misses the ${target.cls}.`);
      }
    }
    for (const hero of this.party) hero.hp = Math.max(0, hero.hp);
    if (!this.alive().length) {
      this.say("The last of the party falls...");
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
    const xp = this.foes.reduce((s, m) => s + m.xp, 0), gold = this.foes.reduce((s, m) => s + m.gold, 0);
    this.gold += gold;
    const loot = rnd.chance(0.45) ? [CM.makeItem(this.floor.number, rnd)] : [];
    this.bag.push(...loot);
    const boss = this.foes.some((m) => m.boss);
    delete this.floor.things[this.foeKey];
    this.sound("coin");
    this.say(`Victory! ${xp} experience and ${gold} gold` + (loot.length ? `, and a ${loot[0].name}.` : "."));
    for (const hero of this.alive()) {
      hero.xp += Math.floor(xp / 2);                                      // everyone standing learns from the fight
      while (hero.xp >= 60 * Math.pow(hero.level, 1.6)) {
        hero.level += 1;
        const base = CM.CLASSES[hero.cls];
        hero.max += Math.max(3, Math.floor(base.hp / 5));
        hero.hp = hero.max;
        hero.atk += 1 + (hero.cls === "Knight" || hero.cls === "Rogue" ? 1 : 0);
        hero.df += hero.level % 2 === 0 ? 1 : 0;
        if (hero.maxmp) { hero.maxmp += 3; hero.mp = hero.maxmp; }
        this.sound("level");
        this.say(`The ${hero.cls} reaches level ${hero.level}!`);
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
        { name: "Phoenix Feather", kind: "revive", power: 0, value: 120 });
    }
    this.emit("bag", true);
  }

  closeBag() {
    this.emit("bag", false);
    this.saveRun();
    this.emit("change");
  }

  describe(item) {
    return { weapon: `weapon +${item.power}`, armor: `armor +${item.power}`, heal: "heals", mana: "restores magic", revive: "raises the fallen" }[item.kind];
  }

  give(row, n) {                                                        // returns a note for the bag screen, "" when it worked
    if (row < 0 || row >= this.bag.length) return "Pick something from your pack first.";
    const item = this.bag[row], hero = this.party[n];
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
    if (item.kind === "weapon" || item.kind === "armor") this.stock.splice(row, 1);
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
    for (const m of this.alive()) { m.hp = m.max; m.mp = m.maxmp; }
    this.sound("heal");
    this.say("The party rests by the fire. Wounds close and magic returns.");
    this.saveRun();
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
    this.enterFloor(this.floor.number + 1);
  }

  potionCount() { return this.bag.filter((i) => ["heal", "mana", "revive"].includes(i.kind)).length; }
};
