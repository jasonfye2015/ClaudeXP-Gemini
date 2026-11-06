"use strict";
// Rockfalls (UPGRADE_PLAN_63.md set 1.2, release 3): on the first four floors the roof is not to be trusted when
// the ground above is sodden (CM.mudNow), when a gale blows above, or in the hour after a meteor's shock: now and
// then, on the clock, a fall of rock comes down on a corridor square of the party's floor within twenty squares -
// never a room, a doorway, a thing or a feature, never the party's square or the one beside it, never within six
// squares of the way up on the first floor, never within six of another fall, never more than three a floor - and
// it blocks that square. The rule that keeps a run from locking: before a fall is placed, every square that could be
// reached from the stairs before must still be reachable with the fall counted as a wall, or it is not placed. A
// fall is cleared by standing before it and pressing Space - twenty minutes of the clock and a little torch, never
// an item - and clears itself after a day of the clock whatever the party does.
//   CM.ROCKFALL                                 the numbers
//   CM.rockfallStep(game, minutes)              the chance and the fall; wrapped into CM.tickClock
//   CM.rockfallAt(game, fl, key)                a fall placed by hand (the harness, the tests): false if the way would close
//   CM.rockfallsOf(fl) -> ["x,y"]               the falls standing
//   CM.rockfallClear(game, key)                 the clearing (what Space does before one)
{ const R = CM.ROCKFALL = { floors: [1, 2, 3, 4], perMinuteWet: 0.004, perMinuteGale: 0.003, perMinuteShock: 0.02, afterShockMinutes: 60, mostPerFloor: 3, apart: 6, nearShaft: 6, reach: 20, clearMinutes: 20, clearTorch: 2, lifeMinutes: 24 * 60 };
  const rnd = () => (CM.wxRandom ? CM.wxRandom() : Math.random());
  CM.rockfallsOf = (fl) => Object.keys((fl && fl.things) || {}).filter((k) => fl.things[k].type === "debris");
  // a fall is a wall for the walk (the party's, the pathing's, the monsters') - never for the map's shape
  { const o0 = CM.isOpen; CM.isOpen = function (floor, x, y) { if (!o0(floor, x, y)) return false; const t = floor.things && floor.things[`${x},${y}`]; return !(t && t.type === "debris"); }; }
  const stairsOf = (fl) => { for (const [k, t] of Object.entries(fl.things)) if (t.type === "ladder" || t.type === "stairs_up") return k.split(",").map(Number); return fl.pos; };
  const inRoom = (fl, x, y) => (fl.rooms || []).some((r) => x >= r.x0 && x <= r.x1 && y >= r.y0 && y <= r.y1);
  const wayHolds = (fl, key) => { const S = stairsOf(fl), before = CM.distances(fl.grid, S, (x, y) => CM.isOpen(fl, x, y)), after = CM.distances(fl.grid, S, (x, y) => CM.isOpen(fl, x, y) && `${x},${y}` !== key); for (const k of before.keys()) if (k !== key && !after.has(k)) return false; return true; };   // (the map's shape, doors and all - a locked door's key may lie beyond, and the way to it must hold)
  CM.rockfallAt = (game, fl, key, how) => { if (!fl || !R.floors.includes(fl.number) || !fl.things) return false; const [x, y] = key.split(",").map(Number), N = fl.grid.length; if (!(x > 0 && y > 0 && x < N - 1 && y < N - 1) || fl.grid[y][x] !== 0 || fl.things[key] || (fl.features || {})[key] || inRoom(fl, x, y)) return false;
    if (fl.pos && Math.abs(x - fl.pos[0]) + Math.abs(y - fl.pos[1]) <= 1) return false; const S = stairsOf(fl); if (fl.number === 1 && Math.abs(x - S[0]) + Math.abs(y - S[1]) <= R.nearShaft) return false;
    const falls = CM.rockfallsOf(fl); if (falls.length >= R.mostPerFloor) return false; for (const f of falls) { const [fx, fy] = f.split(",").map(Number); if (Math.abs(fx - x) + Math.abs(fy - y) < R.apart) return false; }
    if (!wayHolds(fl, key)) return false;
    fl.things[key] = { type: "debris", at: CM.clockOf(game), how: how || "rain" }; game.plantsVersion = (game.plantsVersion || 0) + 1; if (game.emit) game.emit("rockfall", { x, y, how: how || "rain" }); return true; };
  const chance = (game) => { const W = CM.aboveNow ? CM.aboveNow(game) : { wind: { speed: 0 } }, mud = CM.mudNow ? CM.mudNow(game) : 0, M = CM.lastMeteor ? CM.lastMeteor(game) : null, t = CM.clockOf(game);
    return mud * R.perMinuteWet + (W.wind.speed > 0.8 ? R.perMinuteGale : 0) + (M && t - M.at >= 0 && t - M.at <= R.afterShockMinutes ? R.perMinuteShock : 0); };
  CM.rockfallStep = (game, minutes = 1) => { if (!game || !game.ext || !game.floor || !(minutes > 0)) return null; const fl = game.floor, t = CM.clockOf(game);
    for (const k of CM.rockfallsOf(fl)) if (t - (fl.things[k].at || 0) >= R.lifeMinutes) { delete fl.things[k]; game.plantsVersion = (game.plantsVersion || 0) + 1; if (game.say && Math.abs(Number(k.split(",")[0]) - fl.pos[0]) + Math.abs(Number(k.split(",")[1]) - fl.pos[1]) <= R.reach) game.say("Somewhere near, a fall of rock has settled and slid: the way through it is open again."); }   // (a day on, it clears itself)
    if (!R.floors.includes(fl.number) || game.mode !== "explore") return null; const p = chance(game); if (p <= 0 || rnd() >= 1 - Math.pow(1 - p, minutes)) return null;
    const cands = []; const N = fl.grid.length; for (let y = 1; y < N - 1; y++) for (let x = 1; x < N - 1; x++) { if (fl.grid[y][x] !== 0 || Math.abs(x - fl.pos[0]) + Math.abs(y - fl.pos[1]) > R.reach) continue; cands.push(`${x},${y}`); }
    for (let tries = 0; tries < 12 && cands.length; tries++) { const k = cands.splice(Math.floor(rnd() * cands.length), 1)[0]; if (CM.rockfallAt(game, fl, k, chance(game) >= R.perMinuteShock ? "shock" : CM.aboveNow(game).wind.speed > 0.8 ? "gale" : "rain")) { const [x, y] = k.split(",").map(Number), d = Math.abs(x - fl.pos[0]) + Math.abs(y - fl.pos[1]); game.say(d <= 4 ? "The roof comes down close by with a crack and a roar - a fall of rock across the way, and dust in the torchlight." : "A rumble through the stone, and dust from the roof: somewhere near, the way has come down."); return k; } }
    return null; };
  { const t0 = CM.tickClock; CM.tickClock = (game, minutes) => { t0(game, minutes); if (game && game.ext) CM.rockfallStep(game, minutes); }; }
  // the way blocked, said; the clearing
  const P = CM.Game.prototype;
  { const m0 = P.move; P.move = function (rel) { const fl = this.floor; if (fl && this.mode === "explore" && !this.perch) { const [dx, dy] = CM.DIRS[(fl.facing + rel) % 4], k = `${fl.pos[0] + dx},${fl.pos[1] + dy}`, t = fl.things[k]; if (t && t.type === "debris") { this.sound("bump"); this.say("A fall of rock fills the way. (Space to clear it: twenty minutes' work)"); return false; } } return m0.call(this, rel); }; }
  CM.rockfallClear = (game, key) => { const fl = game.floor, t = fl && fl.things[key]; if (!t || t.type !== "debris") return false; game.clock = (game.clock || 0) + R.clearMinutes; for (let i = 0; i < R.clearTorch; i++) if (game.burn) game.burn(); delete fl.things[key]; game.plantsVersion = (game.plantsVersion || 0) + 1; if (game.count) game.count("rockfallsCleared", 1);
    game.say(`Twenty minutes with hands and shoulders${game.bag.some((i) => /pick/i.test(i.name || "")) ? " and the pick" : ""}, and the rock is shifted aside: the way is open.`); if (game.emit) game.emit("change"); return true; };
  { const u0 = P.use; P.use = function (...a) { const fl = this.floor; if (fl && this.mode === "explore" && !this.perch) { const [dx, dy] = CM.DIRS[fl.facing], k = `${fl.pos[0] + dx},${fl.pos[1] + dy}`, t = fl.things[k]; if (t && t.type === "debris") return CM.rockfallClear(this, k); } return u0.apply(this, a); }; }
}
