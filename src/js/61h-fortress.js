"use strict";
// The Fortress (the fourteenth update): a black keep in the north of the Wood, twelve squares of wall with a tower at
// each corner and two great dark-brown doors in its front; a path down to Leshy's clearing, a portal home beside the
// doors, and a portal to it in the town's portal yard. One fighter goes in (CM.fortWhyNot), and the floors below are a
// gauntlet (64j-fortress.js). What a floor gives is carried; it is the party's when the fighter comes out by the stairs.
//   Death: back with the party at the doors with a tenth of their health, and none of the carried gold or things.
//   Out by the stairs: everything carried is the party's, and the next time in is the floor after.
//   Out mid-floor: the floor is lost (what it gave with it), what was carried before it kept.
// Experience is the fighter's whichever way it ends.
CM.FORTRESS = { walls: [30, 1, 41, 3], doors: [[35, 3], [36, 3]], front: [35, 4], portal: [32, 6], path: [35, 4, 35, 12], clearing: [27, 1, 44, 9], centre: [35.5, 2] };
CM.PORTAL_YARD.fortress = [35, 22];                                       // a third portal in the yard, between the other two
CM.isFortCell = (x, y) => { const [x0, y0, x1, y1] = CM.FORTRESS.walls; return x >= x0 && x <= x1 && y >= y0 && y <= y1; };
CM.FORT_LINES = {
  doors: "The Fortress: black stone, a tower at each corner, and doors of dark wood bound in iron, three men high. Behind them the floors go down twenty deep, a maze each, with keys to be found and the stairs somewhere in the dark. One goes in, and fights.",
  dead: (name) => `${name} is found at the Fortress doors at dawn, barely alive. Whatever they carried is still somewhere inside.`,
  out: (name, n) => `${name} comes up out of the Fortress by the stairs from floor ${n}, carrying everything.`,
  fled: (name) => `${name} turns back and finds the way up - without what this floor gave.`,
  done: (name) => `${name} comes out of the Fortress with the Iron Marshal's fall behind them. Twenty floors, and the keep is quiet.`,
};

// laid on the land after everything else: the keep's cells, its doors, the ground before it, the portal, the path
CM.layFortress = function (fl) {
  const F = CM.FORTRESS, [x0, y0, x1, y1] = F.clearing, key = (x, y) => `${x},${y}`, [wx0, wy0, wx1, wy1] = F.walls;
  const open = (x, y, g) => { fl.grid[y][x] = 0; if (fl.kinds) delete fl.kinds[key(x, y)]; (fl.ground = fl.ground || {})[key(x, y)] = g; delete fl.things[key(x, y)]; };
  for (let y = y0; y <= y1; y++) for (let x = x0; x <= x1; x++) if (!CM.isFortCell(x, y) && ((x - 35.5) / 9) ** 2 + ((y - 3) / 6.5) ** 2 <= 1) open(x, y, (x + 2 * y) % 5 ? "dirt" : "grass");
  for (let y = wy0; y <= wy1; y++) for (let x = wx0; x <= wx1; x++) {
    fl.grid[y][x] = 1; if (fl.ground) delete fl.ground[key(x, y)]; delete fl.things[key(x, y)];
    const corner = (x === wx0 || x === wx1) && (y === wy0 || y === wy1), door = F.doors.findIndex(([dx, dy]) => dx === x && dy === y);
    (fl.kinds = fl.kinds || {})[key(x, y)] = door >= 0 ? (door ? "fortdoorR" : "fortdoorL") : corner || x === wx0 || x === wx1 ? "forttower" : (x === F.doors[0][0] - 1 || x === F.doors[1][0] + 1) && y === wy1 ? "forttower" : "fortwall";
  }
  const [px, py0, , py1] = F.path; for (let y = py0; y <= py1; y++) if (fl.grid[y][px] !== 0 || y <= y1) { if (CM.isCabinCell && CM.isCabinCell(px, y)) break; open(px, y, "dirt"); }
  fl.things[key(...F.front)] = { type: "fortress" }; fl.things[key(F.front[0] + 1, F.front[1])] = { type: "fortress" };
  fl.things[key(...F.portal)] = { type: "portal", to: "town" };
  fl.decor = (fl.decor || []).filter((d) => !(d.x >= x0 && d.x <= x1 && d.y >= y0 && d.y <= y1));
  fl.rooms = (fl.rooms || []).concat({ x0, y0, x1, y1, name: "the Fortress" });
  for (let y = y0; y <= y1; y++) for (let x = x0; x <= x1; x++) if (!(fl.seen || []).some(([sx, sy]) => sx === x && sy === y)) (fl.seen = fl.seen || []).push([x, y]);
  for (let y = py0; y <= py1; y++) if (!fl.seen.some(([sx, sy]) => sx === px && sy === y)) fl.seen.push([px, y]);
  return fl;
};

Object.assign(CM.Game.prototype, {
  fortChoices() { return this.party.map((h, i) => ({ i, name: h.name, cls: h.cls, why: CM.fortWhyNot(h) })); },
  // in at the doors: the floor after the last one counted, the fighter alone
  enterFortress(i) {
    const h = this.party[i], why = CM.fortWhyNot(h);
    if (why) return why;
    if (this.mode !== "explore" || !this.floor || this.floor.number !== -1) return "The doors are in the Wood.";
    this.fort = this.fort || { cleared: 0, best: 0 };
    if (this.fort.cleared >= CM.FORT_FLOORS) return "The Fortress is quiet. The Iron Marshal is gone, and its twenty floors keep nothing for anyone now.";
    const n = Math.min(CM.FORT_FLOORS, this.fort.cleared + 1);
    this.logAct && this.logAct("enterFortress", i);
    this.fortRun = new CM.FortRun(this, i, n);
    this.say(`${h.name} goes in alone, and the great doors shut behind them. ${CM.fortFloorName(n)}.`);
    this.setMode("fortress");
    this.emit("fortfloor", this.fortRun);
    return "";
  },
  // the stairs: the floor counted, and down to the next (what was carried goes too), or out with it all
  fortStairs(leave = false) {
    const run = this.fortRun;
    if (!run || !run.atStairs()) return "The stairs are at the far end of the floor.";
    this.logAct && this.logAct("fortStairs", leave);
    this.fort = this.fort || { cleared: 0, best: 0 };
    this.fort.cleared = Math.max(this.fort.cleared, run.n); this.fort.best = Math.max(this.fort.best || 0, run.n);
    this.tally.fortBest = Math.max(this.tally.fortBest || 0, run.n);
    if (run.n >= CM.FORT_FLOORS) { this.achieve && this.achieve("marshal"); return this.leaveFortress("done"); }
    if (leave) return this.leaveFortress("out");
    const next = new CM.FortRun(this, run.heroIndex, run.n + 1);
    for (const k of ["gold", "loot", "xp", "kills", "keys", "flasks"]) next[k] = run[k];   // (carried down: the gold, the things, the keys and flasks)
    this.fortRun = next;
    this.say(`Down the stairs: ${CM.fortFloorName(next.n)}.`);
    this.emit("fortfloor", next);
    return "";
  },
  // out of the Fortress: "out"/"done" by the stairs (everything kept), "fled" mid-floor (the floor's finds lost),
  // "dead" (a tenth of their health; nothing carried kept). Experience always.
  leaveFortress(how) {
    const run = this.fortRun; if (!run) return null;
    const h = run.hero, xp = Math.round(run.xp * CM.FT.xpShare);
    if (xp) { h.xp += xp; this.checkLevels(); }
    let gold = 0, things = [];
    if (how === "out" || how === "done") { gold = run.gold; things = run.loot; }
    else if (how === "fled") { gold = run.gold - run.floorGold; things = run.loot.filter((it) => !run.floorLoot.includes(it)); }
    if (gold) this.gold += gold;
    if (things.length) this.gain(things, "fortress");
    if (how === "dead") { h.hp = Math.max(1, Math.round(h.max * 0.1)); this.tally.fortFalls = (this.tally.fortFalls || 0) + 1; }
    else h.hp = Math.max(1, h.hp);
    this.say(how === "dead" ? CM.FORT_LINES.dead(h.name) : how === "done" ? CM.FORT_LINES.done(h.name) : how === "out" ? CM.FORT_LINES.out(h.name, run.n) : CM.FORT_LINES.fled(h.name));
    const bits = [xp ? `${xp} experience` : "", gold ? `${gold} gold` : "", things.length ? things.map((t) => t.name).join(", ") : ""].filter(Boolean);
    if (bits.length) this.say(`From the Fortress: ${bits.join("; ")}.`);
    if (this.fort && this.fort.cleared && this.fort.cleared < CM.FORT_FLOORS) this.say(`The Fortress will have you back at floor ${this.fort.cleared + 1}.`);
    this.fortRun = null;
    this.setMode("explore");
    this.floor.pos = CM.FORTRESS.front.slice(); this.floor.facing = 2;
    this.saveRun();
    this.emit("floor", this.floor);
    return { how, xp, gold, things };
  },
});
