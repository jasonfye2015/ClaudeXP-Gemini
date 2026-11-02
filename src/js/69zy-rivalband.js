"use strict";
// The rival party (v37.2, UPGRADE_PLAN_32.md): every run has its rivals, a named band of four (by the seed) going down
// ahead of the party. On a floor new to the party they have left signs of passing: their chalk mark on a wall (one floor
// in three - read it with Space), something dropped in a hurry (one in six), and - from the fifth floor - now and then
// one of their own, fallen, with what they carried (each of the four at most once). The rival parties met on a floor
// (meetRivals, 61-explore.js) are this band now, by name, while any of them stand.
//   CM.RIVAL_BANDS; game.rivalBand() -> {name, leader, members, fallen: []}
{ const RB = CM.RIVAL_BANDS = { names: ["the Red Lanterns", "the Ashwood Company", "Marrow's Lot", "the Gilt Spurs", "the Sons of the Ford", "the Grey Hoods", "the Last Bell Company", "Hesta's Own"],
    folk: ["Corran", "Isolde", "Pell", "Varra", "Daik", "Senna", "Holt", "Mirren", "Brisk", "Odile", "Tam Longshanks", "Ravel", "Quill", "Ysa", "Gorm", "Lark"] };
  const G = CM.Game.prototype, key = (x, y) => `${x},${y}`;
  G.rivalBand = function () { const E = this.ext("rivalband"); if (!E.name) { const r = new CM.Random(CM.hashSeed(`${this.seed}:rivalband`)), folk = r.shuffle(RB.folk.slice()); E.name = r.pick(RB.names); E.members = folk.slice(0, 4); E.leader = E.members[0]; E.fallen = []; E.floors = {}; } return E; };
  const spot = (fl, salt, seed, nearWall) => { const N = fl.grid.length, cells = []; for (let y = 1; y < N - 1; y++) for (let x = 1; x < N - 1; x++) { if (fl.grid[y][x] !== 0 || fl.things[key(x, y)] || (fl.features || {})[key(x, y)] || (fl.pos[0] === x && fl.pos[1] === y)) continue;
      if (nearWall) { const f = [0, 1, 2, 3].find((d) => fl.grid[y + CM.DIRS[d][1]] && fl.grid[y + CM.DIRS[d][1]][x + CM.DIRS[d][0]] === 1); if (f === undefined) continue; cells.push([x, y, f]); } else cells.push([x, y]); }
    return cells.length ? cells[CM.hashSeed(`${seed}:${salt}`) % cells.length] : null; };
  const signs = (g, fl) => { const n = fl.number; if (!(n >= 1 && n < 1000 && n % 1 === 0) || fl.special) return; const B = g.rivalBand(); if (B.floors[n]) return; B.floors[n] = true; if (g.deltas && g.deltas[n]) return;   /* (a floor the run had saved already: as it was) */ const s = g.seed;
    if (B.fallen.length >= 4) return;
    if (CM.hashSeed(`${s}:rbchalk:${n}`) % 3 === 0) { const c = spot(fl, `rbchalkat:${n}`, s, true); if (c) fl.things[key(c[0], c[1])] = { type: "chalk", face: c[2], text: CM.hashSeed(`${s}:rbline:${n}`) % 4 }; }
    if (CM.hashSeed(`${s}:rbdrop:${n}`) % 6 === 0) { const c = spot(fl, `rbdropat:${n}`, s); if (c) { const r = new CM.Random(CM.hashSeed(`${s}:rbdropitem:${n}`)); fl.things[key(...c)] = { type: "dropped", item: CM.makeItem(n + 1, r), by: r.pick(B.members.filter((m) => !B.fallen.includes(m))) }; } }
    if (n >= 5 && CM.hashSeed(`${s}:rbdead:${n}`) % 7 === 0) { const alive = B.members.filter((m) => !B.fallen.includes(m) && m !== B.leader); if (alive.length) { const c = spot(fl, `rbdeadat:${n}`, s); if (c) { const who = alive[CM.hashSeed(`${s}:rbwho:${n}`) % alive.length], r = new CM.Random(CM.hashSeed(`${s}:rbdeaditems:${n}`));
      B.fallen.push(who); const it = CM.affix(CM.makeItem(n + 2, r), n + 4, r); fl.things[key(...c)] = { type: "rivaldead", who, items: [it], gold: 20 * n }; } } } };
  const LINES = [(B, n) => `Chalked on the stone: "${B.name.toUpperCase()} - FLOOR ${n} - ALL WELL." The chalk's fresh.`, (B) => `A chalk arrow, and under it: "${B.leader} says this way. ${B.members[1]} says ${B.leader} is wrong."`, (B) => `"${B.name} were here first," in big letters, and under it, smaller, in another hand: "So?"`, (B) => `A tally of chalk marks - kills, by the look of them - and the initials of ${B.name}.`];
  const em0 = G.emit; G.emit = function (ev, ...a) { if (ev === "floor" && this.floor && this.tally) signs(this, this.floor); return em0.call(this, ev, ...a); };
  const use0 = G.use; G.use = function (...a) { const fl = this.floor; if (this.mode === "explore" && fl) { const k = key(fl.pos[0], fl.pos[1]), t = fl.things[k], B = this.rivalBand();
      if (t && t.type === "chalk") { this.logAct && this.logAct("use"); this.say(LINES[t.text % LINES.length](B, fl.number)); return; }
      if (t && t.type === "dropped") { this.logAct && this.logAct("use"); delete fl.things[k]; this.gain([t.item], "chest"); this.say(`Dropped in a hurry by one of ${B.name} - ${t.by}'s, by the mark on it: ${t.item.unknown ? CM.baseName(t.item) : t.item.name}.`); this.saveRun(); this.emit("change"); return; }
      if (t && t.type === "rivaldead") { this.logAct && this.logAct("use"); delete fl.things[k]; this.gold += t.gold; this.gain(t.items, "remains"); this.say(`${t.who}, of ${B.name}. They didn't get much further than this. You take what they carried - ${t.gold} gold and ${t.items.map((i) => (i.unknown ? CM.baseName(i) : i.name)).join(", ")} - and say a word.`); this.tally.rivalsFound = (this.tally.rivalsFound || 0) + 1; this.saveRun(); this.emit("change"); return; } }
    return use0.apply(this, a); };
  const mr0 = G.meetRivals; if (mr0) G.meetRivals = function (thing, k) { const B = this.rivalBand(), left = B.members.filter((m) => !B.fallen.includes(m)); if (!thing.met && left.length) this.say(`It's ${B.name} - ${left.join(", ")}${B.fallen.length ? `; no ${B.fallen.join(" or ")} with them now` : ""}.`); return mr0.call(this, thing, k); };
}
