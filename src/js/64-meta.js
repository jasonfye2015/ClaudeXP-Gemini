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
    if (won) { this.achieve("crown"); if (!this.everFell) this.achieve("ironman"); if (steps < 1500) this.achieve("swift"); if (this.difficulty === "grim") this.achieve("grim"); if (this.iron) this.achieve("ironwill"); if ((this.ascension || 0) >= 5) this.achieve("ascended"); }
    entry.ascension = this.ascension || 0; entry.iron = Boolean(this.iron); entry.awakened = Boolean(this.awakened); entry.reminded = Boolean(this.reminded);
    entry.trail = (this.trail || []).slice();
    if (!this.film) {                                                    // the film of this run, kept for a while (the last six)
      const films = CM.store.get("films", []), key = `${this.seed}:${Date.now()}`;
      films.unshift({ key, seed: this.seed, date: entry.date, floor: entry.floor, won, name: entry.name, spec: Object.assign({}, this.replaySpec(), { log: CM.packLog(this.runLog || []) }) });
      entry.film = key;
      if (!CM.store.set("films", films.slice(0, 6))) CM.store.set("films", films.slice(0, 2));
    }
    if (won && this.awakened) this.achieve("awakened");
    if (won && !this.endless && ["fair", "hard", "grim"].includes(this.difficulty)) {   // the ladder: a crown on Fair or above opens the next rung
      const next = Math.min(CM.ASCENSION.length, (this.ascension || 0) + 1);
      if (next > this.ascensionMax()) { CM.store.set("ascension", next); this.say(`Ascension ${next} is open: the next run may carry ${CM.ASCENSION[next - 1].name.toLowerCase()} too.`); }
    }
    if (this.endless) {
      entry.endless = true;
      if (fl >= 60) this.achieve("endless");
      if (fl >= 100) this.achieve("beyond");
    }
    entry.titles = (this.earned || []).slice();
    entry.renown = CM.renownFor(entry, this);
    this.village.renown = (this.village.renown || 0) + entry.renown;
    entry.chapters = this.payChapters(entry);
    this.saveVillage();
    this.checkContracts(entry);
    entry.code = CM.runCode(this.seed, this.difficulty, this.endless ? "endless" : "dungeon", this.kit, this.startParty || this.party, { ascension: this.ascension || 0, iron: this.iron });
    entry.weekly = String(this.seed).startsWith("weekly-");
    if (!won) for (const h of this.party) if (h.hp <= 0 && !(this.memorial || []).some((m) => m.name === h.name && m.seed === this.seed)) { this.remember2(h); this.say(`${h.name}'s last words: "${this.memorial[0].last}"`); }
    if (!won && !this.bottom) {                                          // where they fell: a later run on this seed finds them
      const carried = this.party.flatMap((h) => CM.equipped(h)).filter((it) => !(it.props && (it.props.relic || it.props.unique)) && !["weapon", "armor"].includes(it.kind));
      const item = carried.length ? carried[Math.floor(this.rnd.next() * carried.length)] : null;
      this.fallen = (this.fallen || []).filter((f) => f.seed !== this.seed || f.floor !== fl).concat({ id: `${this.seed}:${fl}:${Date.now()}`, seed: this.seed, floor: fl, pos: this.floor.pos.slice(), names: this.party.map((h) => h.name), date: CM.today(), item }).slice(-40);
      CM.store.set("fallen", this.fallen);
    }
    if (this.endless) { this.fameEndless.push(entry); this.sortFameEndless(); CM.store.set("fameEndless", this.fameEndless); }
    else { this.fame.push(entry); this.sortFame(); CM.store.set("fame", this.fame); }
    this.ledger = (this.ledger || []).concat([CM.ledgerLine(entry, this.party.map((h) => h.cls))]).slice(-CM.LEDGER_MAX);
    CM.store.set("ledger", this.ledger);
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
      trophies: this.trophies, vaults: this.vaults, achievements: this.achievements, bestiary: this.bestiary, combos: this.combos, weaves: this.weaves, memorial: this.memorial, fallen: this.fallen, village: this.village, ledger: this.ledger });
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
    if (data.vault && typeof data.vault === "object" && data.vault.name) { this.vaults = [data.vault]; CM.store.set("vaults", this.vaults); }
    if (Array.isArray(data.vaults)) { this.vaults = data.vaults.filter((i) => i && i.name); CM.store.set("vaults", this.vaults); }
    if (data.village && typeof data.village === "object") { this.village = Object.assign({ renown: 0, spent: 0, levels: {}, trainers: [] }, data.village); this.saveVillage(); }
    if (data.bestiary && typeof data.bestiary === "object") { this.bestiary = Object.assign({}, this.bestiary, data.bestiary); CM.store.set("bestiary", this.bestiary); }
    if (data.combos && typeof data.combos === "object") { this.combos = Object.assign({}, this.combos, data.combos); CM.store.set("combos", this.combos); }
    if (data.weaves && typeof data.weaves === "object") { this.weaves = Object.assign({}, this.weaves, data.weaves); CM.store.set("weaves", this.weaves); }
    if (Array.isArray(data.memorial)) { this.memorial = data.memorial.concat(this.memorial || []).slice(0, 30); CM.store.set("memorial", this.memorial); }
    if (Array.isArray(data.ledger)) { const have = new Set((this.ledger || []).map(CM.ledgerKey)); this.ledger = (this.ledger || []).concat(data.ledger.filter((l) => l && l.d && !have.has(CM.ledgerKey(l)))).sort((x, y) => (x.t || 0) - (y.t || 0)).slice(-CM.LEDGER_MAX); CM.store.set("ledger", this.ledger); }
    if (Array.isArray(data.fallen)) { const have = new Set((this.fallen || []).map((f) => f.id)); this.fallen = (this.fallen || []).concat(data.fallen.filter((f) => f && f.id && !have.has(f.id))).slice(-40); CM.store.set("fallen", this.fallen); }
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
  // the story: every line of lore read or heard this run, by key (CM.codex reads it)
  markRead(key) {
    if (!key) return false;
    this.story = this.story || { read: {} };
    if (this.story.read[key] !== undefined) return false;
    this.story.read[key] = this.floor ? this.floor.number : 0;
    this.checkHeart();
    const codex = CM.codex(this);
    if (codex.filter((c) => c.band !== undefined).every((c) => c.complete)) this.achieve("chronicler");
    return true;
  },
  // ---- a guardian at the door of its lair: it speaks first; the party fights, speaks, or passes by what it has read ----
  openParley(k, thing) {
    const id = thing.type === "boss" ? "boss" : thing.group[0].guardian, P = CM.PARLEY[id], G = CM.GUARDIANS[id];
    if (!P) return false;
    thing.talk = 0;
    const options = ["Fight"];
    if (P.speak.length) options.push("Speak");
    if (P.gate && CM.gateOpen(this, P.gate)) options.push(P.gate.label);
    this.emit("choice", { k, title: G ? G.name : CM.BOSS.name, text: P.open, options, parley: true });
    return true;
  },
  parley(k, i) {
    const thing = this.floor.things[k];
    if (!thing || !["guardian", "boss"].includes(thing.type)) return false;
    const id = thing.type === "boss" ? "boss" : thing.group[0].guardian, P = CM.PARLEY[id], G = CM.GUARDIANS[id] || CM.BOSS;
    if (!P) return false;
    this.logAct("parley", k, i);
    const step = thing.talk || 0;
    if (step === 0) {                                                    // fight, speak, or the gate (the options as openParley laid them out)
      const acts = ["fight"];
      if (P.speak.length) acts.push("speak");
      if (P.gate && CM.gateOpen(this, P.gate)) acts.push("gate");
      const act = acts[i];
      if (act === "fight") { thing.parleyed = true; this.startCombat(k, thing); return true; }
      if (act === "speak") { thing.talk = 1; thing.score = 0; this.emit("choice", { k, title: G.name, text: P.speak[0].ask, options: P.speak[0].replies.map((r) => r.say), parley: true }); return true; }
      if (act === "gate" && id === "boss") { this.remind(k, thing); return true; }
      if (act === "gate") { this.passGuardian(k, thing, id); return true; }
      return false;
    }
    if (step >= 100) return this.answerRemind(k, thing, i);
    const ex = P.speak[step - 1], reply = ex && ex.replies[i];           // the exchanges
    if (!reply) return false;
    if (reply.good) thing.score = (thing.score || 0) + 1;
    this.say(reply.back);
    if (step < P.speak.length) { thing.talk = step + 1; this.emit("choice", { k, title: G.name, text: `${reply.back} ${P.speak[step].ask}`, options: P.speak[step].replies.map((r) => r.say), parley: true }); return true; }
    thing.parleyed = true; thing.spoke = true;
    thing.terms = (thing.score || 0) >= 2 ? "good" : (thing.score || 0) === 0 ? "bad" : "even";
    this.say(thing.terms === "good" ? P.good : thing.terms === "bad" ? P.bad : "It has heard enough.");
    this.emit("talk", { title: G.name, text: reply.back, lines: [thing.terms === "good" ? P.good : thing.terms === "bad" ? P.bad : "It has heard enough. It comes."] });
    this.startCombat(k, thing);
    return true;
  },
  // passed by speech: not slain - no trophy, no experience, half the gold - but the way is open, and its relic is left behind
  passGuardian(k, thing, id) {
    const P = CM.PARLEY[id], G = CM.GUARDIANS[id], m = thing.group[0];
    if (P.gate.item) { const row = this.bag.findIndex((it) => it.kind === P.gate.item); if (row >= 0) this.bag.splice(row, 1); }
    if (P.gate.holy) {
      const row = this.bag.findIndex((it) => (it.props || {}).element === "holy");
      if (row >= 0) this.bag.splice(row, 1);
      else for (const h of this.party) for (const slot of CM.SLOTS) if (h[slot] && (h[slot].props || {}).element === "holy") { h[slot] = null; CM.recompute(h); break; }
    }
    const gold = Math.floor((m.gold || G.gold || 0) / 2);
    this.gold += gold;
    if (G.relic && !m.echo) { const relic = CM.relic(id); this.bag.push(relic); this.emit("fx", { kind: "relic", item: relic }); }
    this.tally.spoken = (this.tally.spoken || []).concat(id);
    this.story.spoken = (this.story.spoken || []).concat(id);
    if (this.story.spoken.length >= 3) this.achieve("softspoken");
    this.markRead(`passed.${id}`);
    this.remember("ghost", P.gate.text, { who: G.name, key: `passed.${id}` });
    delete this.floor.things[k];
    this.floor.things[k] = { type: "ladder" };
    this.lairAfter(id);
    this.sound("toll");
    this.cheer(6);
    this.say(`${G.name} lets the party by. ${gold} gold lay where it stood.`);
    this.emit("talk", { title: G.name, text: P.gate.text });
    this.emit("fx", { kind: "relic", item: null });
    if (G.final && !this.endless) { this.bottom = true; this.endRun(true); return; }
    this.saveRun();
    this.emit("change");
  },
  // the lair, once its guardian is gone: the water drains, the embers go out, and its carving speaks in the past tense
  lairAfter(id) {
    const fl = this.floor;
    if (!fl) return;
    if (id === "knight" || id === "queen") fl.decor = fl.decor.filter((d) => d.kind !== "water");
    if (id === "forge" || id === "master") fl.decor = fl.decor.filter((d) => d.kind !== "ember");
    for (const f of Object.values(fl.features)) if (f.type === "carving" && f.text === `g:${id}`) f.text = `ga:${id}`;
    this.emit("mesh");
  },
  // the three clues together: the heart's hiding place is known, and marked on the throne room's map
  checkHeart() {
    this.story = this.story || { read: {} };
    if (this.story.heartKnown || !CM.heartKnown(this)) return false;
    this.story.heartKnown = true;
    this.say("The floor above the throne room, under the last stone laid: you know where the king's heart is kept.");
    this.remember("carving", "The floor above the throne room, under the last stone laid: that is where the king's heart is kept. The Chancellor, the wall and the physician's page agree.", { key: "heart.known" });
    this.showHeart(this.floor);
    return true;
  },
  showHeart(fl) {
    if (!fl || fl.number !== CM.LAST_FLOOR - 1 || !this.story || !this.story.heartKnown) return;
    for (const [k, t] of Object.entries(fl.things)) if (t.type === "phylactery") { const [x, y] = k.split(",").map(Number); if (!fl.seen.some(([sx, sy]) => sx === x && sy === y)) fl.seen.push([x, y]); }
    this.emit("change");
  },
  // to remind him: the king asks, five times, and the party answers with what it has read - or cannot, and he draws
  remind(k, thing) {
    thing.talk = 100; thing.remind = 0;                                  // (the parley line that opened this is the log's record)
    this.askRemind(k, thing);
  },
  askRemind(k, thing) {
    const step = thing.remind || 0, R = CM.REMIND[step];
    const have = this.story && this.story.read[R.key] !== undefined;
    this.emit("choice", { k, title: CM.BOSS.name, text: R.ask, options: have ? [R.say, "Say nothing"] : ["Say nothing"], parley: true, remind: true });
  },
  answerRemind(k, thing, i) {
    const step = thing.remind || 0, R = CM.REMIND[step], have = this.story && this.story.read[R.key] !== undefined;
    if (have && i === 0) {
      this.say(R.back);
      thing.remind = step + 1;
      if (thing.remind < CM.REMIND.length) { this.emit("talk", { title: CM.BOSS.name, text: R.back }); this.askRemind(k, thing); return true; }
      this.quietEnd(k, thing);
      return true;
    }
    thing.parleyed = true;
    this.say(CM.REMIND_FAIL);
    this.emit("talk", { title: CM.BOSS.name, text: CM.REMIND_FAIL });
    this.startCombat(k, thing);
    return true;
  },
  // the quiet ending: Mordeth, reminded, ends himself; the crown is the party's without a blow
  quietEnd(k, thing) {
    this.reminded = true;
    this.story.reminded = true;
    delete this.floor.things[k];
    this.foeKey = k;
    this.achieve("merciful");
    this.markRead("ending.quiet");
    this.remember("ghost", CM.REMIND_END, { who: "King Mordeth", key: "ending.quiet" });
    this.emit("talk", { title: "King Mordeth", text: CM.REMIND_END, lines: CM.REMIND_COURT.slice() });
    this.crown();
  },
  // ---- the village's people ----
  // the chronicler's rumours: bought between runs, bound to the next seed begun
  buyRumour(kind) {
    const R = CM.RUMOURS[kind];
    if (!R) return "No such rumour.";
    if (this.villageLevel("library") < 1) return "The village has no library yet.";
    if (this.renown() < CM.RUMOUR_COST) return `A rumour costs ${CM.RUMOUR_COST} renown.`;
    const pending = (this.village.rumours || []).filter((r) => !r.seed);
    if (pending.some((r) => r.kind === kind)) return "Wren has told you that one already. Begin a run, and it will be true.";
    this.village.spent = (this.village.spent || 0) + CM.RUMOUR_COST;
    const floors = []; for (let n = R.floors[0]; n <= R.floors[1]; n++) if (!CM.guardianFor(n) && n !== CM.LAST_FLOOR) floors.push(n);   // (never a guardian's floor)
    const floor = floors[CM.hashSeed(`${Date.now()}:${kind}:${(this.village.rumours || []).length}`) % floors.length];
    this.village.rumours = (this.village.rumours || []).concat({ kind, floor, seed: null });
    this.saveVillage();
    return "";
  },
  bindRumours() {                                                        // a new run: the pending rumours are this seed's
    let bound = false;
    for (const r of this.village.rumours || []) if (!r.seed) { r.seed = this.seed; bound = true; }
    if (bound) { this.village.rumours = this.village.rumours.slice(-12); this.saveVillage(); CM.activeRumours = this.village.rumours.filter((r) => r.seed); }
  },
  rumourText(r) { return CM.RUMOURS[r.kind].what.replace("{n}", r.floor); },
  // the chronicler pays for chapters copied fair, once each, at a run's end
  payChapters(entry) {
    if (this.villageLevel("library") < 1) return 0;
    this.village.chaptersPaid = this.village.chaptersPaid || [];
    let got = 0;
    for (const c of CM.codex(this)) {
      if (c.band === undefined || !c.complete || this.village.chaptersPaid.includes(c.id)) continue;
      const n = c.band >= 4 ? 40 : 20;
      this.village.chaptersPaid.push(c.id); got += n;
      this.say(CM.VILLAGERS.chronicler.paid(c.name, n));
    }
    if (got) { this.village.renown = (this.village.renown || 0) + got; this.saveVillage(); }
    return got;
  },
  // the village's own chapter: a line for every threshold of renown spent
  villageLore() {
    this.village.loreRead = this.village.loreRead || {};
    const spent = this.village.spent || 0, fresh = [];
    CM.VILLAGE_LORE_AT.forEach((at, i) => { const key = `village.${i + 1}`; if (spent >= at && this.village.loreRead[key] === undefined) { this.village.loreRead[key] = 0; fresh.push(key); } });
    if (fresh.length) this.saveVillage();
    return fresh;
  },
  // the priest says three names
  priestNames(from = 0) {
    const names = (this.memorial || []).slice(from, from + 3);
    if (!names.length) return ["\"No names yet. May it stay so.\""];
    return names.map((m) => `"${m.name}, ${m.cls}, who fell on floor ${m.floor}.${m.epitaph ? ` ${m.epitaph}` : ""}${m.candle ? " A candle burns." : ""}"`);
  },
  book() { return CM.chronicle(this.fame, this.ledger); },
  // an epitaph for a name on the memorial (the village's shrine; the priest and the ghost repeat it)
  setEpitaph(i, text) {
    const m = (this.memorial || [])[i];
    if (!m) return false;
    m.epitaph = String(text || "").trim().slice(0, 60);
    CM.store.set("memorial", this.memorial);
    return true;
  },
  // a hero's word at a wall that concerns their past, once a run
  originLines(key) {
    this.story.said = this.story.said || [];
    for (const h of this.alive()) {
      const O = h.origin && CM.ORIGINS[h.origin], line = O && O.lines[key];
      if (!line || this.story.said.includes(`${h.name}:${key}`)) continue;
      this.story.said.push(`${h.name}:${key}`);
      this.say(`${h.name}: "${line}"`);
      this.remember("ghost", `${h.name}, at the wall on floor ${this.floor ? this.floor.number : 0}: "${line}"`, { who: h.name, key: `said.${h.name}.${key}` });
      if (h.origin === "dwarffriend" && ["halls", "crystal"].includes((CM.LORE_TEXT[key] || {}).chapter)) { const goal = CM.goalOf(this.floor); if (goal) this.say(`${h.name} reads the dwarves' mark again: the way down lies ${this.directionTo(goal.split(",").map(Number))}.`); }
    }
  },
  // banter: one line, the bonded pair's or two who stand, by what just happened (never in a fight)
  banter(kind) {
    const lines = CM.BANTER2[kind] || [];
    if (!lines.length || this.mode === "combat") return "";
    const alive = this.alive(); if (alive.length < 2) return "";
    const bond = (this.bonds || [])[Math.floor((this.tally.fights || 0) / 7) % Math.max(1, (this.bonds || []).length)];
    const [a, b] = bond || [alive[(this.tally.steps || 0) % alive.length].name, alive[((this.tally.steps || 0) + 1) % alive.length].name];
    if (a === b) return "";
    const key = `${a}|${b}`, joke = bond && (this.pairFights || {})[key] >= CM.BOND_FIGHTS * 3 && kind === "camp" && (this.tally.fights || 0) % 2 === 0;
    const text = (joke ? CM.JOKES[(this.tally.fights || 0) % CM.JOKES.length] : lines[((this.tally.fights || 0) + (this.tally.steps || 0)) % lines.length]).replace(/\{a\}/g, a).replace(/\{b\}/g, b);
    this.say(text);
    return text;
  },
  metGhost(name) { this.village.ghostsMet = (this.village.ghostsMet || []).filter((n) => n !== name).concat(name).slice(-40); this.saveVillage(); },
  hasItem(kind) { return this.bag.findIndex((i) => i.kind === kind); },

  // someone to talk to, where the party stands (Space)
  talk(thing, k) {
    if (!this.inUse) this.logAct("talk", k);
    if (thing.type === "ghost") this.talkGhost(thing, k);
    else if (thing.type === "hermit") this.talkHermit(thing);
    else if (thing.type === "adventurer") this.freeAdventurer(thing, k);
  },

  talkGhost(thing, k) {
    const fl = this.floor, P = thing.arc ? CM.PEOPLE[thing.who] : null;
    const G = thing.own ? { name: thing.own.name, tale: thing.own.epitaph ? `${thing.own.name}'s epitaph: ${thing.own.epitaph}` : `${thing.own.name} the ${thing.own.cls} says: ${CM.OWN_LINES[thing.line || 0]}` }
      : P ? { name: P.name, tale: P.tale } : CM.GHOSTS[thing.who] || CM.GHOSTS[0];
    const R = P && thing.arc === 3 ? P.request : CM.REQUESTS[thing.request] || CM.REQUESTS.story;
    if (thing.legend !== undefined) {                                    // a legend of one of your own crowned parties, carved in a newer hand
      const e = CM.legends[thing.legend] || CM.legends[0];
      if (!e) { delete this.floor.things[k]; return; }
      this.sound("ailment");
      this.emit("talk", { title: "A newer carving", text: CM.legendLine(e) });
      if (!thing.asked) { thing.asked = true; this.remember("carving", CM.legendLine(e), { key: `legend.${e.date}.${e.floor}` }); this.saveRun(); }
      return;
    }
    if (thing.courtier !== undefined) {                                  // the court: it sits, and speaks, and has nothing to ask
      const C = CM.COURT[thing.courtier];
      this.sound("ailment");
      this.emit("talk", { title: C.name, text: C.line });
      if (!thing.asked) { thing.asked = true; this.markRead(`court.${thing.courtier + 1}`); this.remember("ghost", C.line, { who: C.name, key: `court.${thing.courtier + 1}` }); this.saveRun(); }
      return;
    }
    if (P && thing.arc < 3) {                                            // the first and the second meeting: a word, remembered
      const met = (this.village.ghostsMet || []).includes(P.name), key = `people.${thing.who + 1}.${thing.arc}`;
      this.sound("ailment");
      this.emit("talk", { title: P.name, text: thing.arc === 1 ? P.first : P.second, lines: met && !thing.asked ? [P.again] : [] });
      if (!thing.asked) { thing.asked = true; this.markRead(key); this.remember("ghost", thing.arc === 1 ? P.first : P.second, { who: P.name, key }); this.metGhost(P.name); this.saveRun(); }
      return;
    }
    const done = thing.request === "bones" ? this.hasItem("bones") >= 0
      : thing.request === "vengeance" ? Boolean(fl.avenged && fl.avenged.includes(k))
      : thing.request === "bell" ? this.hasItem("bell") >= 0
      : thing.request === "witness" ? Boolean(this.story && this.story.read[R.key] !== undefined)
      : Object.values(fl.features).some((f) => f.type === "carving" && f.read && !(typeof f.text === "string"));
    if (!thing.asked) {
      thing.asked = true;
      this.sound("ailment");
      const met = P && (this.village.ghostsMet || []).includes(P.name);
      this.emit("talk", { title: G.name, text: thing.own ? `${thing.own.name} the ${thing.own.cls}${thing.own.level ? `, level ${thing.own.level}` : ""} - yours, once, and fallen here. "${CM.OWN_LINES[thing.line || 0]}" A pause. "${R.ask}"`
        : `A pale shape waits in the air, not quite a man or a woman any more. "I was ${G.name}," it says.${met ? ` ${P.again}` : ""} "${R.ask}"` });
      if (P) this.metGhost(P.name);
      this.saveRun();
      return;
    }
    if (!done) { this.emit("talk", { title: G.name, text: `"${R.wait}"` }); return; }
    if (thing.request === "bones") this.bag.splice(this.hasItem("bones"), 1);
    if (thing.request === "bell") { this.bag.splice(this.hasItem("bell"), 1); this.story.bell = true; this.sound("victory"); this.achieve("bellringer"); }
    if (thing.own) {                                                     // laid to rest: a candle burns for them at the shrine, for nothing
      const m = (this.memorial || []).find((x) => x.name === thing.own.name && x.seed === this.seed && !x.candle);
      if (m) { m.candle = CM.today(); if (m.buried && this.vaultRoom && this.vaultRoom()) { this.vaults.push(m.buried); CM.store.set("vaults", this.vaults); } CM.store.set("memorial", this.memorial); }
      this.achieve("laidtorest");
    }
    const rnd = new CM.Random(CM.hashSeed(`${this.seed}:ghost:${fl.number}`));
    const gift = CM.makeGear(rnd.pick(["ring", "amulet", "amulet"]), fl.number + 4, rnd);
    gift.unknown = false;
    this.bag.push(gift);
    const xp = 30 * fl.number;
    for (const h of this.alive()) h.xp += xp;
    delete fl.things[k];
    const gkey = thing.own ? null : `ghost.${(P ? thing.who : CM.GHOSTS.indexOf(G)) + 1}`;
    this.markRead(gkey);
    this.remember("ghost", G.tale, { who: G.name, key: gkey });
    if (P) { this.story.witnessed = (this.story.witnessed || []).concat(P.name); if (this.story.witnessed.length >= CM.PEOPLE.length) this.achieve("witness"); }
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
    // a chapter all but read (one telling missed, at most): he tells it back, with the truth under it, and the codex counts it whole
    this.story = this.story || { read: {} }; this.story.told = this.story.told || {};
    const chapter = CM.codex(this).find((c) => c.band !== undefined && c.done >= c.total - 1 && !this.story.told[c.id] && CM.CHAPTER_TRUTH[c.id]);
    if (chapter) {
      this.story.told[chapter.id] = true;
      this.remember("ghost", CM.CHAPTER_TRUTH[chapter.id], { who: "The hermit", key: `told.${chapter.id}` });
      this.emit("talk", { title: "The hermit", text: `"${chapter.name}. You've read it, near enough. I'll tell it back to you, so you know what you've read." He shuts his eyes. "${chapter.epigraph}"`, lines: [CM.CHAPTER_TRUTH[chapter.id]] });
      this.saveRun();
      return;
    }
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
      const wall = Object.entries(this.floor.features).find(([, f]) => f.type === "carving" && !f.read);
      const goal = CM.goalOf(this.floor), where = goal ? this.directionTo(goal.split(",").map(Number)) : "nowhere you can get to";
      this.emit("talk", { title: "The hermit", text: `${CM.HERMIT.nothing} "${wall ? `There's a wall on this floor you haven't read: ${this.directionTo(wall[0].split(",").map(Number))}.` : `The way down lies ${where}.`}"` });
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
    if (!thing.freed) {
      thing.freed = true;
      const past = (this.memorial || []).filter((m) => m.cls === h.cls && m.floor < fl.number && !(this.story.recalled || []).includes(m.name) && m.name !== h.name);
      if (past.length) {                                                 // (a hero of yours who fell shallower, on any seed: found alive after all)
        const m = past[CM.hashSeed(`${this.seed}:recalled:${fl.number}`) % past.length];
        thing.hero.name = m.name; h.name = m.name; thing.hero.recalled = m.floor;
        this.story.recalled = (this.story.recalled || []).concat(m.name);
        this.emit("talk", { title: h.name + " the " + h.cls, text: `${CM.ADVENTURER.found} You know the face. ${h.name} fell on floor ${m.floor} of another descent, ${m.date} - or was left for dead, and crawled, and was taken. "You look like you've seen a ghost," ${h.name} says. "Fair."` });
      } else this.emit("talk", { title: h.name + " the " + h.cls, text: CM.ADVENTURER.found });
      this.saveRun(); return;
    }
    const fallen = this.party.findIndex((p) => p.hp <= 0 || (p.status || {}).stone);
    delete fl.things[k];
    this.sound("unlock");
    this.achieve("friend");
    if (fallen >= 0) {
      const gone = this.party[fallen];
      for (const slot of CM.SLOTS) if (gone[slot] && !(slot === "weapon" || slot === "armor")) this.bag.push(gone[slot]);
      this.remember2(gone);
      this.bonds = (this.bonds || []).filter((b) => !b.includes(gone.name));
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
      this.village.met = (this.village.met || []).filter((m) => m.name !== h.name).concat(Object.assign({}, h)).slice(-12); this.saveVillage();
      this.say(CM.ADVENTURER.leaves(h.name));
    }
    this.saveRun();
    this.emit("change");
  },

  // a riddle door, walked into: the window asks; a right answer opens it, a wrong one burns
  answerRiddle(k, answer) {
    const f = this.floor.features[k], r = f && CM.RIDDLES[f.riddle];
    if (!r || f.open) return false;
    this.logAct("answerRiddle", k, answer);
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
    if (!this.inUse) this.logAct("ropeDown", k);
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
    this.logAct("choosePath", this.party.indexOf(hero), id);
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

  readTome(row, hero) {                                                 // "" when learned, else why not (through give: logged there)
    const item = this.bag[row], id = item.spell;
    if (!CM.isCaster(hero)) return `${hero.name} turns the pages and can't make head or tail of them: a tome is for a caster.`;
    if (CM.abilitiesFor(hero).includes(id)) {                            // known: the tome raises it a level
      hero.spellLevels = hero.spellLevels || {};
      const lvl = hero.spellLevels[id] || 1;
      if (lvl >= CM.SPELL_LEVELS) return `${hero.name} knows ${CM.ABILITIES[id].name} as well as it can be known.`;
      hero.spellLevels[id] = lvl + 1;
      this.bag.splice(row, 1);
      this.sound("spell");
      this.say(`${hero.name} reads the ${item.name} again, deeper: ${CM.ABILITIES[id].name} is level ${lvl + 1} now - a quarter more, and one less to cast.`);
      this.emit("fx", { kind: "levelup", hero });
      this.saveRun(); this.emit("change");
      return "";
    }
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
    if (this.asc("hardened")) hp *= 1.05;
    if (this.asc("keenblades")) atk *= 1.1;
    if (this.asc("thickskins")) hp *= 1.1;
    if (this.awakened) { hp *= CM.AWAKENED.hp; atk *= CM.AWAKENED.atk; }
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
    this.logAct("offerBoons", this.party.indexOf(hero));
    const have = hero.boons || [], c = CM.CLASSES[hero.cls] || CM.CLASSES.Knight;
    const own = Object.keys(CM.BOONS).find((id) => CM.BOONS[id].stat === c.key);       // the class's own stat is always on offer
    const pool = Object.keys(CM.BOONS).filter((id) => id !== own && (CM.BOONS[id].stat || !have.includes(id)));
    hero.offer = [own, ...this.rnd.shuffle(pool).slice(0, 2)];
    this.dirty = true;
    return hero.offer;
  },

  chooseBoon(hero, id) {
    if (!hero.pending || !(hero.offer || []).includes(id)) return false;
    this.logAct("chooseBoon", this.party.indexOf(hero), id);
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
    this.logAct("setRow", this.party.indexOf(hero), row);
    hero.row = row;
    this.dirty = true;
    this.emit("change");
    return true;
  },
});
}

// ---- the ledger: one short line for every expedition that ended, and the statistics read from it ----
CM.LEDGER_MAX = 600;
CM.ledgerLine = function (entry, classes) {
  const t = entry.tally || {};
  return { t: Date.now(), d: entry.date, sd: entry.seed, f: entry.floor, w: entry.won ? 1 : 0, b: entry.bottom ? 1 : 0, e: entry.endless ? 1 : 0, df: entry.difficulty || "fair", a: entry.ascension || 0,
    c: classes || [], s: t.steps || 0, fi: t.fights || 0, k: t.kills || 0, fl: t.fled || 0, ch: t.chests || 0, g: entry.gold || 0, sp: Object.assign({}, t.spent || {}) };
};
CM.ledgerKey = (l) => `${l.d}|${l.sd}|${l.f}|${l.s}|${l.g}`;
// a Hall of Fame entry as a ledger line, for the runs that ended before the ledger was kept ("Name the cls 7")
CM.ledgerFromFame = function (entry) {
  const classes = (entry.party || []).map((p) => { const m = / the (\w+) \d+$/.exec(String(p)); return m ? m[1] : null; }).filter(Boolean);
  return Object.assign(CM.ledgerLine(entry, classes), { t: 0, old: 1 });
};
CM.BANDS = [[1, 5], [6, 10], [11, 15], [16, 20], [21, 25], [26, 30], [31, 35], [36, 40], [41, 45], [46, 50], [51, Infinity]];
CM.statistics = function (ledger) {
  const st = { runs: 0, crowns: 0, bottoms: 0, fell: 0, old: 0, deepest: 0, steps: 0, fights: 0, kills: 0, fled: 0, chests: 0, gold: 0, spent: {}, spentTotal: 0, first: null, last: null,
    bands: CM.BANDS.map(([from, to]) => ({ from, to, fell: 0, through: 0 })), callings: {}, difficulties: {} };
  for (const l of ledger || []) {
    st.runs++; if (l.old) st.old++;
    if (l.w) st.crowns++; if (l.b) st.bottoms++; if (!l.w && !l.b) st.fell++;
    st.deepest = Math.max(st.deepest, l.f || 0);
    st.steps += l.s || 0; st.fights += l.fi || 0; st.kills += l.k || 0; st.fled += l.fl || 0; st.chests += l.ch || 0; st.gold += l.g || 0;
    for (const [where, n] of Object.entries(l.sp || {})) { st.spent[where] = (st.spent[where] || 0) + n; st.spentTotal += n; }
    if (!st.first) st.first = l.d; st.last = l.d;
    for (const band of st.bands) { if (l.f > band.to) band.through++; else if (l.f >= band.from) { if (!l.w && !l.b) band.fell++; else band.through++; break; } }
    for (const c of l.c || []) { const row = st.callings[c] = st.callings[c] || { n: 0, crowns: 0 }; row.n++; if (l.w) row.crowns++; }
    const d = st.difficulties[l.df || "fair"] = st.difficulties[l.df || "fair"] || { n: 0, crowns: 0, a: 0 }; d.n++; if (l.w) d.crowns++; d.a = Math.max(d.a, l.a || 0);
  }
  st.favourite = Object.entries(st.callings).sort((x, y) => y[1].n - x[1].n || y[1].crowns - x[1].crowns)[0] || null;
  return st;
};
