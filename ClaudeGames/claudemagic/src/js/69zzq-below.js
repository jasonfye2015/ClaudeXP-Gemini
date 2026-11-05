"use strict";
// The dungeon coupling (v78.0, UPGRADE_PLAN_61.md part 8): what the sky does reaches down the shaft. CM.aboveNow
// answers the surface's event from any floor. A heavy storm above floods the lowest halls of the first three
// floors - the sunken rooms (69zzi-levels.js) stand knee-deep - and the water drains over the day after: a step in
// it takes a minute more and the walk is heavier. The drips, the waterfalls at the grates, the drafts, the lightning
// through the grates and the steam are the window's (76zzzzzzzzzzn-below.js).
//   CM.aboveNow(game)                 the surface's weather, anywhere (CM.weatherNow)
//   CM.floodNow(game) -> 0..1         the floodwater's level: 1 in a heavy storm, draining to 0 over a day
//   CM.floodedAt(game, fl, x, y)       a square standing in floodwater (a sunken square of floors 1-3, level > 0)
//   CM.floodedHere(game)               the party's square
//   CM.floodTick(game, minutes)        the level, kept in game.ext("flood"); wrapped into CM.tickClock
{ const F = CM.FLOOD = { from: 0.75, drainMinutes: 24 * 60, floors: [1, 2, 3] };
  CM.aboveNow = (game) => CM.weatherNow(game);
  const state = (game) => game.ext("flood");
  CM.floodTick = (game, minutes = 1) => { if (!game || !game.ext || !(minutes > 0)) return; const E = state(game), W = CM.weatherNow(game), t = CM.clockOf(game);
    if (W.kind === "storm" && W.strength >= F.from) { if (E.level !== 1 && game.floor && F.floors.includes(game.floor.number)) game.say("Water comes down the shaft and the stairs in a sheet: the storm above is flooding the low halls."); E.level = 1; E.at = t; return; }
    if (E.at !== undefined) { const was = E.level || 0; E.level = Math.max(0, 1 - (t - E.at) / F.drainMinutes); if (was > 0 && E.level === 0) { delete E.at; if (game.floor && F.floors.includes(game.floor.number)) game.say("The last of the floodwater has drained away down the cracks."); } } };
  CM.floodNow = (game) => { if (!game || !game.ext) return 0; const E = state(game); return E.at !== undefined ? Math.max(0, Math.min(1, E.level || 0)) : 0; };
  CM.floodedAt = (game, fl, x, y) => Boolean(fl && F.floors.includes(fl.number) && CM.floodNow(game) > 0 && CM.floorAt(fl, x, y) < 0 && fl.grid[y] && fl.grid[y][x] === 0);
  CM.floodedHere = (game) => { const fl = game && game.floor; return Boolean(fl && fl.pos && CM.floodedAt(game, fl, fl.pos[0], fl.pos[1])); };
  CM.floodSquares = (game, fl) => { const out = []; if (!fl || !F.floors.includes(fl.number) || !fl.levels || CM.floodNow(game) <= 0) return out; for (const [k, L] of Object.entries(fl.levels)) if (L[0] < 0) { const [x, y] = k.split(",").map(Number); if (fl.grid[y] && fl.grid[y][x] === 0) out.push([x, y]); } return out; };
  { const t0 = CM.tickClock; CM.tickClock = (game, minutes) => { t0(game, minutes); if (game && game.ext) CM.floodTick(game, minutes); }; }
  const P = CM.Game.prototype, burn0 = P.burn; P.burn = function (...a) { if (CM.floodedHere(this)) this.clock = (this.clock || 0) + 1; return burn0.apply(this, a); };   // (wading: the step takes two minutes)
  const wp0 = P.walkPace; P.walkPace = function (...a) { const p = wp0.apply(this, a); return CM.floodedHere(this) ? p * 1.5 : p; };
}
