"use strict";
// The water basins (UPGRADE_PLAN_63.md set 1.1, release 2): the flood of the sunken rooms (69zzq-below.js) has two
// depths now - knee-deep as the water drains, waist-deep while the storm's level stands - and the deep water slows
// the party more (two minutes a step, the walk at twice the pace). What the water hides: a spike grating, placed at
// a floor's making in a sunken room of four squares' width or more, harmless and drawn when dry, a point a step to
// each hero when flooded, said on the look line and never on a room's doorway; a leech, fastened on a hero now and
// then while wading waist-deep (a bite that festers like a poison - any healing or the camp pulls it off); and a
// sunk chest, one of the sunken rooms' chests marked so, that is dived for at the cost of a quarter hour while the
// water stands. Nothing here blocks a way: a grating is one square in a room three squares wide at least.
//   CM.floodDepth(game, fl, x, y) -> 0 | 1 | 2        knee-deep | waist-deep (CM.floodNow at BASINS.waistFrom or more)
//   CM.floodDepthHere(game) -> 0 | 1 | 2
//   CM.basinsOf(fl) -> { grates: ["x,y"], chests: ["x,y"] }   what the floor's making placed (features and things)
//   CM.leechStep(game, minutes)                        the leeches, on the clock; wrapped into CM.tickClock
{ const B = CM.BASINS = { waistFrom: 0.75, grateBite: 1, leechEvery: 10, leechChance: 0.3, leechPoison: 4, diveMinutes: 15, chestEvery: 3 };
  CM.floodDepth = (game, fl, x, y) => { if (!CM.floodedAt || !CM.floodedAt(game, fl, x, y)) return 0; return CM.floodNow(game) >= B.waistFrom ? 2 : 1; };
  CM.floodDepthHere = (game) => { const fl = game && game.floor; return fl && fl.pos ? CM.floodDepth(game, fl, fl.pos[0], fl.pos[1]) : 0; };
  // the floor's making: a grating in a sunken room wide enough, a chest of the sunken rooms marked sunk
  const sunkenRooms = (fl) => (fl.rooms || []).filter((r) => !r.name && !r.template && r.x1 - r.x0 >= 4 && r.y1 - r.y0 >= 4 && fl.levels && fl.levels[`${r.x0 + 1},${r.y0 + 1}`] && fl.levels[`${r.x0 + 1},${r.y0 + 1}`][0] < 0);
  CM.basinsOf = (fl) => { const out = { grates: [], chests: [] }; if (!fl || !fl.features) return out; for (const [k, f] of Object.entries(fl.features)) if (f.type === "grate") out.grates.push(k); for (const [k, t] of Object.entries(fl.things || {})) if (t.type === "chest" && t.sunk) out.chests.push(k); return out; };
  const furnish = (fl) => { if (!fl || !(fl.number >= 1) || !fl.levels || !fl.rooms || fl.basinsMade) return; fl.basinsMade = true; let i = 0;
    for (const r of sunkenRooms(fl)) { const h = CM.hashSeed(`${fl.number}:basin:${r.x0},${r.y0}`) >>> 0, cx = r.x0 + 2 + h % (r.x1 - r.x0 - 3), cy = r.y0 + 2 + (h >> 8) % (r.y1 - r.y0 - 3), k = `${cx},${cy}`;   // (inside the room, a square in from its edge: never a doorway)
      if (fl.grid[cy][cx] === 0 && !fl.things[k] && !fl.features[k]) fl.features[k] = { type: "grate", known: true };
      if (i++ % B.chestEvery === 0) { const chest = Object.entries(fl.things).find(([ck, t]) => t.type === "chest" && !t.mimic && !t.sunk && (() => { const [x, y] = ck.split(",").map(Number); return x >= r.x0 && x <= r.x1 && y >= r.y0 && y <= r.y1; })()); if (chest) chest[1].sunk = true; } } };
  const P = CM.Game.prototype;
  { const ef0 = P.enterFloor; P.enterFloor = function (...a) { const out = ef0.apply(this, a); if (this.floor) furnish(this.floor); return out; }; }   // (on the first visit, not at the making: the generator's fingerprints stay as they are, and the save's deltas carry the grating)
  // the deep water: a minute more again, the pace doubled
  { const b0 = P.burn; P.burn = function (...a) { if (CM.floodDepthHere(this) === 2) this.clock = (this.clock || 0) + 1; return b0.apply(this, a); }; }
  { const w0 = P.walkPace; P.walkPace = function (...a) { const p = w0.apply(this, a); return CM.floodDepthHere(this) === 2 ? p * 4 / 3 : p; }; }   // (69zzq's x1.5 and this: x2)
  // the grating underfoot
  { const ar0 = P.arrive; P.arrive = function (f, k) { if (f && f.type === "grate") { const [x, y] = k.split(",").map(Number), d = CM.floodDepth(this, this.floor, x, y);
        if (d) { let bit = 0; for (const h of this.alive()) if (h.hp > 1) { h.hp = Math.max(1, h.hp - B.grateBite); bit++; } this.sound("trap"); this.say(bit ? `The water hides a spiked grating: it bites through the boots (-${B.grateBite} each).` : "The water hides a spiked grating, and there is nothing left for it to bite."); }
        else this.say("An iron grating, spiked, set in the floor: harmless dry, and a thing to remember when the hall floods."); return; }
      return ar0.call(this, f, k); }; }
  // the leeches, while wading waist-deep
  CM.leechStep = (game, minutes = 1) => { if (!game || !game.ext || !(minutes > 0) || CM.floodDepthHere(game) !== 2 || game.mode !== "explore") return; const E = game.ext("basins"); E.wade = (E.wade || 0) + minutes;
    while (E.wade >= B.leechEvery) { E.wade -= B.leechEvery; for (const h of game.alive()) { if ((CM.hashSeed(`${game.seed}:leech:${h.name}:${CM.clockOf(game)}`) >>> 0) % 100 >= B.leechChance * 100) continue; h.status = h.status || {}; if (h.status.poison) continue; h.status.poison = B.leechPoison; game.say(`A leech has fastened on ${h.name} under the water: the bite will fester a while - any healing, or the camp, pulls it off.`); } } };
  { const t0 = CM.tickClock; CM.tickClock = (game, minutes) => { t0(game, minutes); if (game && game.ext) CM.leechStep(game, minutes); }; }
  // the sunk chest: dived for while the water stands
  { const u0 = P.use; P.use = function (...a) { const fl = this.floor; if (fl && fl.pos && this.mode === "explore") { const k = `${fl.pos[0]},${fl.pos[1]}`, t = fl.things[k]; if (t && t.type === "chest" && t.sunk && !t.opened && CM.floodDepth(this, fl, fl.pos[0], fl.pos[1]) > 0) { this.clock = (this.clock || 0) + B.diveMinutes; this.say(`The chest is under the water: ${this.alive()[0] ? this.alive()[0].name : "someone"} goes down for it, and comes up streaming, a quarter hour on.`); } }
      return u0.apply(this, a); }; }
}
