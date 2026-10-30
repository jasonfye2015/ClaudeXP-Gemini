"use strict";
// Around the run: the dungeon's people and their requests, riddles, the paths and boons a level brings, the
// difficulty and the day's mutators as they bite, achievements, the Hall of Fame, and Export / Import.
{
const keyOf = CM.keyOf;
Object.assign(CM.Game.prototype, {
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
    if (this.endless) {
      entry.endless = true;
      if (fl >= 60) this.achieve("endless");
      if (fl >= 100) this.achieve("beyond");
    }
    entry.titles = (this.earned || []).slice();
    if (this.endless) { this.fameEndless.push(entry); this.sortFameEndless(); CM.store.set("fameEndless", this.fameEndless); }
    else { this.fame.push(entry); this.sortFame(); CM.store.set("fame", this.fame); }
    if (won) this.trophy("lich");
    CM.store.remove(this.runKey(this.slot));
    this.lastRun = null;
    this.sound(won ? "victory" : "death");
    this.titleNote = this.endless && !(won && fl <= CM.LAST_FLOOR) ? `Endless: the party went ${fl} floors down into a dark with no bottom${this.crowned ? ", with the Lich King's crown" : ""}. Their story ends there.`
      : this.bottom ? "To the bottom of the world and back, with the Lich King's crown. There is no deeper."
      : won && this.floor.number > CM.LAST_FLOOR ? `With the Lich King's crown, the party went down into the Deep, and fell on floor ${this.floor.number}.`
      : won ? "The Lich King is no more. The party returns as legends!"
      : `The party fell on floor ${this.floor.number}. Their story ends here.`;
    this.emit("over", won, entry);
    this.setMode("title");
  },

  sortFame() {
    this.fame.sort((a, b) => (b.bottom ? 1 : 0) - (a.bottom ? 1 : 0) || (b.won ? 1 : 0) - (a.won ? 1 : 0) || b.floor - a.floor || b.gold - a.gold);
    this.fame = this.fame.slice(0, 10);
  },

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
      this.lastRun = CM.migrateRun(Object.assign({ seed: CM.randomSeed(), mode: "explore" }, data.run));
      CM.store.set(this.runKey(this.slot), this.lastRun);
      took.push("run");
    }
    this.emit("change");
    return took;
  },

  exportText() {
    return JSON.stringify({ game: "Claude and Magic", version: CM.version, built: CM.built, run: this.runs[0], runs: this.runs, slot: this.slot, fame: this.fame, fameEndless: this.fameEndless, settings: this.settings,
      trophies: this.trophies, vault: this.vault, achievements: this.achievements, bestiary: this.bestiary, combos: this.combos });
  },

  importText(text) {
    let data;
    try { data = JSON.parse(text); } catch (e) { return "That isn't a Claude and Magic save."; }
    if (!data || data.game !== "Claude and Magic") return "That isn't a Claude and Magic save.";
    if (Array.isArray(data.runs)) data.runs.forEach((r, i) => { if (r && r.floor && r.party) { this.runs[i] = CM.migrateRun(r); CM.store.set(this.runKey(i + 1), this.runs[i]); } });
    else if (data.run && data.run.floor && data.run.party) { this.runs[0] = CM.migrateRun(data.run); CM.store.set("run", this.runs[0]); }
    if (data.achievements && typeof data.achievements === "object") { this.achievements = Object.assign({}, this.achievements, data.achievements); CM.store.set("achievements", this.achievements); }
    if (Array.isArray(data.fame)) { this.fame = data.fame; this.sortFame(); CM.store.set("fame", this.fame); }
    if (Array.isArray(data.fameEndless)) { this.fameEndless = data.fameEndless; this.sortFameEndless(); CM.store.set("fameEndless", this.fameEndless); }
    if (data.settings) { Object.assign(this.settings, data.settings); this.saveSettings(); }
    if (data.trophies && typeof data.trophies === "object") { this.trophies = Object.assign({}, this.trophies, data.trophies); CM.store.set("trophies", this.trophies); }
    if (data.vault && typeof data.vault === "object" && data.vault.name) { this.vault = data.vault; CM.store.set("vault", this.vault); }
    if (data.bestiary && typeof data.bestiary === "object") { this.bestiary = Object.assign({}, this.bestiary, data.bestiary); CM.store.set("bestiary", this.bestiary); }
    if (data.combos && typeof data.combos === "object") { this.combos = Object.assign({}, this.combos, data.combos); CM.store.set("combos", this.combos); }
    this.emit("change");
    return "";
  },


  // ---- the journal, and the dungeon's people ----
  // everything read and heard goes in the journal (once), to be read again with J, and to pay the hermit with
  remember(kind, text, extra = {}) {
    this.journal = this.journal || [];
    if (this.journal.some((e) => e.text === text)) return false;
    this.journal.push(Object.assign({ kind, text, floor: this.floor ? this.floor.number : 0 }, extra));
    this.emit("journal");
    if (this.journal.length >= 10) this.achieve("scholar");
    return true;
  },
  hasItem(kind) { return this.bag.findIndex((i) => i.kind === kind); },

  // someone to talk to, where the party stands (Space)
  talk(thing, k) {
    if (thing.type === "ghost") this.talkGhost(thing, k);
    else if (thing.type === "hermit") this.talkHermit(thing);
    else if (thing.type === "adventurer") this.freeAdventurer(thing, k);
  },

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
  },

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
  },

  directionTo([x, y]) {
    const [px, py] = this.floor.pos, dx = x - px, dy = y - py;
    if (!dx && !dy) return "under your feet";
    const ns = dy < -Math.abs(dx) / 2 ? "north" : dy > Math.abs(dx) / 2 ? "south" : "", ew = dx > Math.abs(dy) / 2 ? "east" : dx < -Math.abs(dy) / 2 ? "west" : "";
    return `to the ${ns}${ns && ew ? "-" : ""}${ew}, ${Math.abs(dx) + Math.abs(dy)} paces or so`;
  },

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
  },

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
  },

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
  },

  // down a pit on a rope: no fall, and the rope stays tied to climb back by
  ropeDown(k) {
    const fl = this.floor, [x, y] = k.split(",").map(Number), n = fl.number;
    this.sound("stairs");
    this.enterFloor(n + 1, "fall", [x, y]);
    const below = this.floor;
    below.things[keyOf(below.pos[0], below.pos[1])] = { type: "rope", up: [x, y] };
    this.say("The rope hangs down beside you: a way back up.");
    this.saveRun();
  },


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
  },

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
  },
  has(mutator) { return (this.mutators || []).includes(mutator); },
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
  },
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
  },
  deepen(number) {                                                       // every tenth floor below the bottom, a mutator more - one the run is without
    const left = CM.DEEPENING.filter((m) => !this.has(m));
    if (!left.length || (this.deepened || []).includes(number)) return null;
    this.deepened = (this.deepened || []).concat(number);
    const m = left[CM.hashSeed(`${this.seed}:deepen:${number}`) % left.length];
    this.mutators = (this.mutators || []).concat(m);
    this.say(`The dark deepens. ${CM.MUTATORS[m].name}: ${CM.MUTATORS[m].what}.`);
    return m;
  },
  sortFameEndless() {
    this.fameEndless.sort((a, b) => b.floor - a.floor || b.gold - a.gold);
    this.fameEndless = this.fameEndless.slice(0, 10);
  },

  // ---- a level earned is a boon chosen ----
  offerBoons(hero) {
    if (hero.offer && hero.offer.length === 3) return hero.offer;
    const have = hero.boons || [], c = CM.CLASSES[hero.cls] || CM.CLASSES.Knight;
    const own = Object.keys(CM.BOONS).find((id) => CM.BOONS[id].stat === c.key);       // the class's own stat is always on offer
    const pool = Object.keys(CM.BOONS).filter((id) => id !== own && (CM.BOONS[id].stat || !have.includes(id)));
    hero.offer = [own, ...this.rnd.shuffle(pool).slice(0, 2)];
    this.dirty = true;
    return hero.offer;
  },

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
  },

  setRow(hero, row) {
    if (this.mode === "combat" || !["front", "back"].includes(row)) return false;
    hero.row = row;
    this.dirty = true;
    this.emit("change");
    return true;
  },
});
}
