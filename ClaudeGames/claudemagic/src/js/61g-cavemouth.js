"use strict";
// Claudeita's cave mouth (the thirteenth update): a crag of grey rock south of the fields, three squares deep, with a
// dark mouth in its face and a warm light far down in it; a path to it from the fields and a portal home beside it; the
// second plinth in the portal yard lit for it. One caster goes in (CM.TOWER_CASTERS), with the default wands (and up
// to two of their own from the rack), and the cave is Claudeita's (64i-claudeita.js; the window's side 76c-cave.js).
//   Death: back with the party at the mouth, a tenth of their health, and none of the run's gold, things or wands.
//   A win (the Unmaker's fall, or the rope up from a sanctuary): the run's gold and things are the party's, and its
//   wands and spells go to the rack at the mouth. Experience is the hero's whichever way it ends.
CM.CLAUDEITA = { crag: [45, 46, 51, 48], mouth: [48, 46], front: [48, 45], portal: [45, 44], clearing: [42, 42, 54, 50], path: [48, 30, 48, 44], centre: [48, 46] };
CM.PORTAL_YARD.claudeita = CM.PORTAL_YARD.plinths[1];                  // the second plinth lights for the cave
CM.CAVE_RACK = { wands: 12, spells: 40, carry: 2 };                     // the rack at the mouth: how many it holds, how many wands go in
CM.isCragCell = (x, y) => { const [x0, y0, x1, y1] = CM.CLAUDEITA.crag; return x >= x0 && x <= x1 && y >= y0 && y <= y1; };
CM.CAVE_LINES = {
  mouth: "A crag of grey rock among the trees, and in its face a low dark mouth. Far down, something glows like a forge, and the air out of it smells of wet stone and smoke. Whoever goes in goes alone, with a wand.",
  dead: (name) => `${name} wakes at the cave's mouth, cold and barely breathing. Everything the deep gave is gone back to it.`,
  out: (name) => `${name} climbs out of the cave's mouth into the daylight, carrying what the deep gave.`,
  won: (name) => `${name} comes up out of the deep with the Unmaker undone behind them. The cave is quiet.`,
  left: (name) => `${name} turns back and climbs out empty-handed.`,
};

// laid on the land after everything else: the crag, its clearing, the path from the fields, the portal home
CM.layClaudeita = function (fl) {
  const C = CM.CLAUDEITA, [x0, y0, x1, y1] = C.clearing, key = (x, y) => `${x},${y}`, [cx, cy] = C.centre;
  const open = (x, y, g) => { fl.grid[y][x] = 0; if (fl.kinds) delete fl.kinds[key(x, y)]; (fl.ground = fl.ground || {})[key(x, y)] = g; delete fl.things[key(x, y)]; };
  for (let y = y0; y <= y1; y++) for (let x = x0; x <= x1; x++) if (((x - cx) / 6.2) ** 2 + ((y - cy) / 4.6) ** 2 <= 1 && !CM.isCragCell(x, y)) open(x, y, (x * 5 + y * 3) % 4 ? "grass" : "dirt");
  for (let y = C.crag[1]; y <= C.crag[3]; y++) for (let x = C.crag[0]; x <= C.crag[2]; x++) { fl.grid[y][x] = 1; (fl.kinds = fl.kinds || {})[key(x, y)] = x === C.mouth[0] && y === C.mouth[1] ? "cavemouth" : x === C.crag[0] || x === C.crag[2] ? "craglow" : y > C.crag[1] && Math.abs(x - C.mouth[0]) <= 2 ? "cragtall" : "crag"; if (fl.ground) delete fl.ground[key(x, y)]; delete fl.things[key(x, y)]; }
  const [px, py0, , py1] = C.path;                                      // the path north to the fields, as far as it needs to go
  for (let y = py1; y >= py0; y--) { const was = fl.grid[y][px]; if (y < py1 - 1 && was === 0 && !(fl.kinds && fl.kinds[key(px, y)])) break; open(px, y, "dirt"); }
  fl.things[key(...C.front)] = { type: "claudeita" };
  fl.things[key(...C.portal)] = { type: "portal", to: "town" };
  fl.decor = (fl.decor || []).filter((d) => !(d.x >= x0 && d.x <= x1 && d.y >= y0 && d.y <= y1));
  fl.rooms = (fl.rooms || []).concat({ x0, y0, x1, y1, name: "Claudeita's cave" });
  for (let y = y0; y <= y1; y++) for (let x = x0; x <= x1; x++) if (!(fl.seen || []).some(([sx, sy]) => sx === x && sy === y)) (fl.seen = fl.seen || []).push([x, y]);
  for (let y = py0; y <= py1; y++) if (!(fl.seen || []).some(([sx, sy]) => sx === px && sy === y)) fl.seen.push([px, y]);
  return fl;
};

Object.assign(CM.Game.prototype, {
  // the cave's keep, with the village: the rack's wands and spells, and the runs
  caveStore() {
    this.village = this.village || {};
    const K = this.village.cave = this.village.cave || {};
    K.wands = K.wands || []; K.spells = K.spells || []; K.runs = K.runs || 0; K.wins = K.wins || 0; K.deaths = K.deaths || 0; K.deepest = K.deepest || 0; K.bosses = K.bosses || 0;
    return K;
  },
  caveChoices() { return this.party.map((h, i) => ({ i, name: h.name, cls: h.cls, why: !h || h.hp <= 0 ? `${h.name} has fallen.` : CM.TOWER_CASTERS.includes(h.cls) ? "" : `${h.name} the ${h.cls} has no gift for wands: the cave is for casters.` })); },
  // in at the mouth: the hero alone, their health in the cave's measure, the default wands and up to two from the rack
  enterClaudeita(i, rackPicks = []) {
    const h = this.party[i], c = this.caveChoices()[i];
    if (!h) return "No one.";
    if (c.why) return c.why;
    if (this.mode !== "explore" || !this.floor || this.floor.number !== -1) return "The cave's mouth is in the Wood.";
    const K = this.caveStore(), picks = [...new Set(rackPicks)].filter((k) => K.wands[k]).slice(0, CM.CAVE_RACK.carry);
    const stat = Math.max(h.stats ? h.stats.int || 10 : 10, h.stats ? h.stats.wis || 10 : 10);
    const hpMax = Math.round(60 + h.max * 2.5), dmgScale = 1 + (h.level - 1) * 0.06 + Math.max(0, stat - 10) * 0.03;
    K.runs += 1; this.saveVillage && this.saveVillage();
    const seed = CM.hashSeed(`${this.seed}:claudeita:${K.runs}`);
    this.logAct && this.logAct("enterClaudeita", i);
    this.caveRun = new CM.CaveRun(seed, { hpMax, hp: Math.max(1, Math.round(hpMax * h.hp / h.max)), dmgScale, name: h.name, wands: picks.map((k) => K.wands[k]), spells: ["Digging Bolt", "Spark Bolt"] });
    this.caveRun.heroIndex = i; this.caveRun.rackPicks = picks;
    this.caveRun.player.wands.forEach((w, n) => { if (w.own) w.rackIndex = picks[n - 2]; });
    this.say(`${h.name} goes down into the cave's mouth alone, the Apprentice's Wand in hand.`);
    this.setMode("cave");
    this.emit("cave", this.caveRun);
    return "";
  },
  // out of the cave: "dead" (a tenth of their health, and nothing kept but experience), "won" or "out" (everything
  // kept), "left" (turned back: nothing kept but experience, the health as it was)
  leaveClaudeita(how) {
    const run = this.caveRun; if (!run) return null;
    const h = this.party[run.heroIndex], K = this.caveStore(), p = run.player, kept = how === "won" || how === "out";
    const xp = Math.round(run.xp); if (xp && h) { h.xp += xp; this.checkLevels(); }
    K.deepest = Math.max(K.deepest, run.depth()); K.bosses = Math.max(K.bosses, run.bossesDown.size);
    let gold = 0, things = [], wands = 0, spells = 0;
    if (kept) {
      gold = p.gold; this.gold += gold;
      for (const L of run.loot) { const rnd = new CM.Random(CM.hashSeed(`${this.seed}:cavething:${K.runs}:${L.boss}`)), depth = 5 + L.boss * 9, item = CM.affix(CM.makeItem(depth, rnd), depth + 2, rnd); item.unknown = false; things.push(item); }
      if (things.length) this.gain(things, "cave");
      for (const w of p.wands) {                                          // the rack: wands carried out (the given two stay behind; your own come back as they are now)
        if (w.given) continue;
        if (w.own && w.rackIndex !== undefined && K.wands[w.rackIndex]) K.wands[w.rackIndex] = w.toJSON();
        else if (K.wands.length < CM.CAVE_RACK.wands) { K.wands.push(w.toJSON()); wands++; }
      }
      for (const s of p.spells) if (K.spells.length < CM.CAVE_RACK.spells) { K.spells.push(s); spells++; }
      K.wins += how === "won" ? 1 : 0;
      if (how === "won") this.achieve && this.achieve("unmaker");
    } else if (how === "dead") K.deaths += 1;
    if (h) {
      if (how === "dead") h.hp = Math.max(1, Math.round(h.max * 0.1));
      else h.hp = Math.max(1, Math.min(h.max, Math.round(h.max * p.hp / p.hpMax)));
    }
    this.tally.caveRuns = (this.tally.caveRuns || 0) + 1; this.tally.caveBosses = Math.max(this.tally.caveBosses || 0, run.bossesDown.size);
    const name = h ? h.name : "The hero";
    this.say(how === "dead" ? CM.CAVE_LINES.dead(name) : how === "won" ? CM.CAVE_LINES.won(name) : how === "out" ? CM.CAVE_LINES.out(name) : CM.CAVE_LINES.left(name));
    const bits = [xp ? `${xp} experience` : "", gold ? `${gold} gold` : "", things.length ? things.map((t) => t.name).join(", ") : "", wands ? CM.plural(wands, "wand") + " for the rack" : "", spells ? CM.plural(spells, "spell") + " for the rack" : ""].filter(Boolean);
    if (bits.length) this.say(`From the cave: ${bits.join("; ")}.`);
    this.caveRun = null;
    this.setMode("explore");
    this.floor.pos = CM.CLAUDEITA.front.slice(); this.floor.facing = 0;
    this.saveVillage && this.saveVillage(); this.saveRun();
    this.emit("floor", this.floor);
    return { how, xp, gold, things, wands, spells };
  },
});
