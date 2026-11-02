"use strict";
// The hound's tricks (v35.1, UPGRADE_PLAN_30.md): taught at the farm (and later the kennel) for gold, kept with the
// hound in the village. Fetch: after a fight some of the foes fled, the hound brings back what they dropped - coins, and
// now and then a thing. Guard: nobody catches the party napping while the hound is with it, and at a camp's rest it
// keeps watch (the party wakes in better heart). Track: when a foe flees, the hound takes the scent and follows it to its
// lair - a den in the Deep Wood, a cave of its own (three at most at once), with the fled beast's kin, the beast itself
// leading them, and what they have dragged home. A den cleared is gone.
//   CM.TRICKS; game.tricks(); game.teachTrick(id); game.dens() -> [{n, kind, depth, at, cleared}]; CM.DEN_NUMBERS
{ CM.TRICKS = { fetch: { name: "Fetch", gold: 40, what: "brings back what fled foes dropped" }, guard: { name: "Guard", gold: 60, what: "no one catches the party napping; a better night's rest at a camp" },
    track: { name: "Track", gold: 80, what: "follows a fled foe to its lair: a den in the Deep Wood" } };
  CM.DEN_NUMBERS = [-1.81, -1.82, -1.83]; CM.DEN_SPEC = {};
  CM.isDen = (n) => CM.DEN_NUMBERS.includes(n);
  const G = CM.Game.prototype, key = (x, y) => `${x},${y}`;
  Object.assign(G, {
    tricks() { const p = this.pets().dog; if (!p) return {}; return (p.tricks = p.tricks || {}); },
    hasTrick(id) { return Boolean(this.petName("dog") && this.tricks()[id]); },
    teachTrickWhy(id) { const T = CM.TRICKS[id]; if (!T) return "No such trick."; if (!this.petName("dog")) return "There's no hound to teach."; if (!((this.atFarm && this.atFarm()) || (this.atKennel && this.atKennel()))) return "Tricks are taught at the farm (or the kennel, once there is one).";
      if (this.tricks()[id]) return `${this.petName("dog")} knows it already.`; if (this.gold < T.gold) return `${T.gold} gold.`; return ""; },
    teachTrick(id) { const why = this.teachTrickWhy(id); if (why) return why; this.logAct && this.logAct("teachTrick", id); const T = CM.TRICKS[id]; this.gold -= T.gold; this.tricks()[id] = true; this.saveVillage && this.saveVillage();
      this.say(`A few days of patience and dried meat: ${this.petName("dog")} has learnt to ${id === "fetch" ? "fetch" : id === "guard" ? "keep watch" : "follow a scent wherever it goes"}.`); if (Object.keys(CM.TRICKS).every((k) => this.tricks()[k]) && this.achieve) this.achieve("goodboy"); this.saveRun && this.saveRun(); this.emit("change"); return ""; },
    dens() { const D = this.ext("dens"); D.list = D.list || []; return D.list; },
    denOf(number) { const i = CM.DEN_NUMBERS.indexOf(number); return i < 0 ? null : this.dens().find((d) => d.n === i) || null; },
    denSpecs() { for (const d of this.dens()) CM.DEN_SPEC[CM.DEN_NUMBERS[d.n]] = { kind: d.kind, depth: d.depth }; },
  });
  CM.ACHIEVEMENTS.goodboy = { name: "Who's a Good Hound", what: "Teach the hound all three tricks", title: "of the Hounds" };
  CM.ACHIEVEMENTS.denbreaker = { name: "Den-breaker", what: "Clear a lair the hound tracked down", title: "the Tracker" };
  // the den: a short floor of the fled kind, the beast itself leading, a hoard at the far end; the way out where the stair was
  CM.makeDen = function (number, seed, gen) { const S = CM.DEN_SPEC[number] || { kind: "Wolf", depth: 2 }, n = CM.DEN_NUMBERS.indexOf(number), depth = Math.max(1, Math.min(40, S.depth));
    const fl = CM.makeFloor(depth, `${seed}:den:${n}:${S.kind}`, 2); fl.number = number; fl.special = "cave"; fl.den = n; delete fl.wing;
    const K = CM.monsterKind(S.kind), rnd = new CM.Random(CM.hashSeed(`${seed}:denfolk:${n}`)); let far = null, farD = -1;
    for (const [k, t] of Object.entries(fl.things)) {
      if (t.type === "stairs_up") fl.things[k] = { type: "denexit" };
      else if (t.type === "monsters" && K) { t.group = Array.from({ length: Math.max(1, Math.min(4, (t.group || []).length)) }, () => CM.makeMonster(K, depth, rnd)); const [x, y] = k.split(",").map(Number), d = Math.abs(x - fl.pos[0]) + Math.abs(y - fl.pos[1]); if (d > farD) { farD = d; far = t; } }
      else if (!["chest", "monsters", "key"].includes(t.type)) delete fl.things[k]; }
    if (far && K) { const lord = CM.makeMonster(K, depth + 2, rnd); lord.name = `The ${S.kind} that Fled`; lord.champion = "hoarder"; lord.max = Math.round(lord.max * 1.6); lord.hp = lord.max; far.group[0] = lord; far.denLord = true; }
    for (const [k, f] of Object.entries(fl.features)) if (["carving", "teleporter", "spinner", "trapdoor", "pit"].includes(f.type)) delete fl.features[k];
    if (!Object.values(fl.things).some((t) => t.type === "denexit")) fl.things[key(fl.pos[0], fl.pos[1])] = { type: "denexit" };
    return fl; };
  const mf0 = CM.makeFloor; CM.makeFloor = function (number, seed, gen) { return CM.isDen(number) ? CM.makeDen(number, seed, gen) : mf0.call(this, number, seed, gen); };
  const fa0 = G.floorAt; if (fa0) G.floorAt = function (number, ...a) { if (CM.isDen(number)) this.denSpecs(); return fa0.call(this, number, ...a); };
  // the Wood: a den's mouth where the trail ends (deep in the forest, by hash, kept)
  const placeDens = (g) => { const fl = g.floor; if (!fl || fl.number !== -1) return; const size = fl.grid.length;
    for (const d of g.dens()) { if (d.cleared) { if (d.at && fl.things[d.at] && fl.things[d.at].type === "den") delete fl.things[d.at]; continue; }
      if (!d.at) { const cells = []; for (let y = 2; y < size - 2; y++) for (let x = 2; x < 18; x++) if (fl.grid[y][x] === 0 && !fl.things[key(x, y)] && !(fl.features || {})[key(x, y)] && ["grass", "dirt"].includes((fl.ground || {})[key(x, y)])) cells.push(key(x, y));
        if (!cells.length) continue; d.at = cells[CM.hashSeed(`${g.seed}:den:${d.n}:${d.kind}`) % cells.length]; }
      fl.things[d.at] = { type: "den", n: d.n, kind: d.kind }; } };
  const em0 = G.emit; G.emit = function (ev, ...a) { if (ev === "floor") { placeDens(this); if (this.floor && CM.isDen(this.floor.number)) this.denSpecs(); } return em0.call(this, ev, ...a); };
  const use0 = G.use; G.use = function (...a) { const fl = this.floor; if (this.mode === "explore" && fl) { const t = fl.things[key(fl.pos[0], fl.pos[1])];
      if (t && t.type === "den") { this.logAct && this.logAct("use"); const d = this.dens().find((x) => x.n === t.n); if (d) { this.denSpecs(); this.sound && this.sound("stairs"); this.enterFloor(CM.DEN_NUMBERS[d.n], "down"); this.say(`Down into the dark under the roots, where the ${d.kind.toLowerCase()} went to ground. It smells of wet fur and old bones.`); return; } }
      if (t && t.type === "denexit") { this.logAct && this.logAct("use"); const d = this.denOf(fl.number); const left = Object.values(fl.things).some((x) => x.type === "monsters");
        if (d && !left) { d.cleared = true; this.say(`The den is quiet. ${this.petName("dog") || "The hound"} has a last sniff round, satisfied.`); if (this.achieve) this.achieve("denbreaker"); }
        this.sound && this.sound("stairs"); this.enterFloor(-1, "rope", d && d.at ? d.at.split(",").map(Number) : CM.WOOD_GATE.slice()); this.say("Up out of the den, into the Wood."); return; } }
    return use0.apply(this, a); };
  // after a fight: fetch, and the scent
  const wf0 = G.wonFight; G.wonFight = function (...a) { const fled = (this.foes || []).filter((m) => m.fled && !m.summoned && !m.boss && !m.guardian), fl = this.floor, out = wf0.apply(this, a), dog = this.petName("dog");
    if (dog && fled.length && fl) {
      if (this.hasTrick("fetch")) { const gold = Math.max(3, Math.round((fl.number > 0 ? fl.number : 2) * 4 * fled.length)); this.gold += gold; let it = null;
        if (CM.hashSeed(`${this.seed}:fetch:${this.tally.fights || 0}`) % 4 === 0) { const r = new CM.Random(CM.hashSeed(`${this.seed}:fetchitem:${this.tally.fights || 0}`)); it = CM.makeItem(Math.max(1, fl.number), r); this.gain([it], "foe"); }
        this.say(`${dog} trots back from where they ran, with ${gold} gold in a torn purse${it ? ` and ${it.unknown ? "something" : it.name}` : ""}.`); }
      if (this.hasTrick("track") && !CM.isDen(fl.number) && this.dens().filter((d) => !d.cleared).length < CM.DEN_NUMBERS.length) { const m = fled[0], kind = m.kind || m.name;
        if (CM.monsterKind(kind)) { const used = new Set(this.dens().filter((d) => !d.cleared).map((d) => d.n)), n = [0, 1, 2].find((i) => !used.has(i)); const D = this.dens(); for (let i = D.length - 1; i >= 0; i--) if (D[i].n === n) D.splice(i, 1);
          D.push({ n, kind, depth: fl.number > 0 ? fl.number : 2, cleared: false }); this.say(`${dog} puts its nose down where the ${kind.toLowerCase()} fled and goes very still - then pulls at the lead. The trail runs up and out, all the way to the Deep Wood: there's a den there now, under the roots, waiting.`); } } }
    return out; };
  const sc0 = G.startCombat; G.startCombat = function (...a) { const guard = this.hasTrick("guard") && this.floor && this.floor.number !== 0, B = this.buffs = this.buffs || {}, had = B.night !== undefined;
    if (guard && !had) B.night = 0; try { return sc0.apply(this, a); } finally { if (guard && !had) delete this.buffs.night; } };
  const rest0 = G.rest; if (rest0) G.rest = function (...a) { const g0 = this.gold, out = rest0.apply(this, a); if (this.gold < g0 && this.hasTrick("guard")) {   /* (rested: the bed was paid for) */ this.cheer && this.cheer(5); this.say(`${this.petName("dog")} keeps watch all night: everyone sleeps deeper for it.`); } return out; };
}
