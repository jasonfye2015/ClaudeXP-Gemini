"use strict";
// Meteors and the ore (v75.0, UPGRADE_PLAN_61.md part 5): a star falls a couple of times a week at least, by night
// more often than by day, and lands on an open square the party can walk to on the surface floor they are on (or on
// the town's or the Wood's floor, if they are below, where the shock comes down through the stone). The strike leaves
// a crater - a scorched ring that fades over days - and a chunk of meteorite ore lying in it, picked up by stepping
// onto it: Meteor Iron, an ingredient worth more than the alchemist's, which the smith takes in a diamond's place.
// Trees within its reach may catch (69zzm-trees.js: CM.igniteTree), not in rain or snow. The strike is a sight and a
// shock, never a harm: it never lands on the party, a building, a fence or a tree. State lives in the run (game.ext).
//   CM.meteorStep(game, minutes)              the schedule, the strike (emits "meteor" on the game)
//   CM.meteorWarning(game) -> 0..1            the minutes before a strike, when the birds go up
//   CM.cratersOf(game, fl) -> { "x,y": days } the craters still showing, by age in days (26-surface.js draws them)
//   CM.meteorSite(game, fl, from) -> [x, y]   an open, reachable, lonely square at a walk from `from`
//   CM.lastMeteor(game) -> strike | null       the latest strike { floor, x, y, at, felt, fires }
{ const M = CM.METEORS = { gapMinDays: 1.5, gapMaxDays: 3.5, firstMaxDays: 1.2, nightOdds: 0.65, warnMinutes: 3, nearMin: 4, nearMax: 14, fireChance: 0.5, fireReach: 2.5, craterDays: 10, oreValue: 60 };
  const rnd = () => (CM.wxRandom ? CM.wxRandom() : Math.random()), between = (a, b) => a + rnd() * (b - a), DAY = 24 * 60;
  CM.INGREDIENTS.meteoriron = { name: "Meteor Iron", band: -2, rare: true, what: "a chunk of a fallen star, heavy and black, with a bright grain where it broke: the smith takes it in a diamond's place, and anyone buys it" };
  { const i0 = CM.ingredient; CM.ingredient = (id) => { const it = i0(id); if (id === "meteoriron") it.value = M.oreValue; return it; }; }
  const store = (game) => { const E = game.ext("meteors"); E.strikes = E.strikes || []; return E; };
  const hourAt = (clock) => ((CM.CLOCK.start + clock) % CM.CLOCK.day) / 60;
  const nightAt = (game, clock) => { const [dawn, dusk] = CM.daylightOf(game), h = hourAt(clock); return h >= dusk || h < dawn; };
  // the next strike: a gap of days, and more often than not moved on into the night that follows
  const schedule = (game, from, first) => { let at = Math.round(from + between(first ? 60 : M.gapMinDays * DAY, (first ? M.firstMaxDays : M.gapMaxDays) * DAY));
    if (!nightAt(game, at) && rnd() < M.nightOdds) { const dusk = CM.daylightOf(game)[1], h = hourAt(at); at += Math.round(((dusk - h + 24) % 24) * 60 + between(10, 240)); } return at; };
  // the square: open, with no thing or feature on it, every neighbour open or a tree (no building, fence or wall beside it), at a walk of nearMin..nearMax from `from`, never under the party
  CM.meteorSite = (game, fl, from) => { if (!fl || !(fl.number === 0 || fl.number === -1)) return null; const start = from || fl.pos, N = fl.grid.length, D = CM.distances(fl.grid, start, (x, y) => CM.passable(fl, x, y)), out = [];
    for (const [k, d] of D) { if (d < M.nearMin || d > M.nearMax) continue; const [x, y] = k.split(",").map(Number); if (fl.things[k] || fl.features[k] || (fl.pos && x === fl.pos[0] && y === fl.pos[1])) continue; let ok = true;
      for (let dy = -1; dy <= 1 && ok; dy++) for (let dx = -1; dx <= 1 && ok; dx++) { const nx = x + dx, ny = y + dy; if (nx < 0 || ny < 0 || nx >= N || ny >= N) { ok = false; break; } const s = CM.solidAt(fl, nx, ny); if (s !== null && s !== "tree") ok = false; }
      if (ok) out.push([x, y, d]); }
    if (!out.length) return null; const pick = out[Math.floor(rnd() * out.length)]; return [pick[0], pick[1]]; };
  const surfaceFloor = (game) => { const fl = game.floor; if (fl && (fl.number === 0 || fl.number === -1)) return fl; const have = [game.floors && game.floors[-1], game.floors && game.floors[0]].filter(Boolean); return have.length ? have[Math.floor(rnd() * have.length)] : null; };
  const strike = (game) => { const E = store(game), fl = surfaceFloor(game); if (!fl) return null; const here = game.floor === fl, site = CM.meteorSite(game, fl, fl.pos); if (!site) return null;
    const [x, y] = site, k = `${x},${y}`, t = CM.clockOf(game), W = CM.weatherNow ? CM.weatherNow(game) : { kind: "clear" }, wet = W.kind === "rain" || W.kind === "storm" || W.kind === "snow"; let fires = 0;
    fl.things[k] = { type: "meteorite", at: t };
    if (!wet && CM.igniteTree) { const was = game.floor; game.floor = fl; for (const tk of CM.treeSquares(fl)) { const [tx, ty] = tk.split(",").map(Number); if (Math.hypot(tx - x, ty - y) <= M.fireReach && rnd() < M.fireChance && CM.igniteTree(game, fl, tk)) fires++; } game.floor = was; }
    const s = { floor: fl.number, x, y, at: t, felt: !here, fires }; E.strikes.push(s); if (E.strikes.length > 40) E.strikes = E.strikes.slice(-40); E.count = (E.count || 0) + 1; game.meteorVersion = (game.meteorVersion || 0) + 1;
    if (game.count) game.count("meteors", 1); game.emit("meteor", s); return s; };
  CM.meteorStep = (game, minutes = 1) => { if (!game || !game.ext || !(minutes > 0)) return null; const E = store(game), t = CM.clockOf(game);
    if (!E.next) { E.next = schedule(game, t, true); return null; } if (t < E.next) return null;
    const s = strike(game); E.next = s ? schedule(game, t, false) : t + 60; return s; };   // (no floor or no square yet: try again in an hour)
  CM.meteorWarning = (game) => { if (!game || !game.ext) return 0; const E = store(game); if (!E.next) return 0; const m = E.next - CM.clockOf(game); return m < 0 || m > M.warnMinutes ? 0 : 1 - m / M.warnMinutes; };
  CM.lastMeteor = (game) => { if (!game || !game.ext) return null; const S = store(game).strikes; return S.length ? S[S.length - 1] : null; };
  CM.cratersOf = (game, fl) => { const out = {}; if (!game || !game.ext || !fl) return out; const t = CM.clockOf(game); for (const s of store(game).strikes) { if (s.floor !== fl.number) continue; const days = (t - s.at) / DAY; if (days < M.craterDays) out[`${s.x},${s.y}`] = Math.round(days * 10) / 10; } return out; };
  // the ore: picked up by stepping onto it (the move's own thing branch does not know it, so it is taken first)
  { const mv0 = CM.Game.prototype.move; CM.Game.prototype.move = function (rel) { const fl = this.floor, before = fl && fl.pos ? fl.pos.slice() : null; let out;
      const say0 = this.say; this.say = function (t) { if (t !== undefined) return say0.call(this, t); };   // (the move's own look at the square has no words for the ore: it says nothing, and the words come below)
      try { out = mv0.call(this, rel); } finally { delete this.say; }
      if (!fl || !fl.pos || !this.floor || this.floor !== fl) return out;
      const k = `${fl.pos[0]},${fl.pos[1]}`, th = fl.things[k]; if (th && th.type === "meteorite" && (!before || before[0] !== fl.pos[0] || before[1] !== fl.pos[1])) { delete fl.things[k]; this.gain([CM.ingredient("meteoriron")], "event"); if (this.count) { this.count("gathered", 1); this.count("meteoriron", 1); } this.sound("coin"); this.say("In the crater, still warm: a chunk of the fallen star, black and heavy, with a bright grain where it broke. You take it."); }
      return out; }; }
  // the smith takes a chunk of meteor iron in a diamond's place (a diamond in the bag goes first)
  { const sm0 = CM.Game.prototype.smith; CM.Game.prototype.smith = function (service, heroIndex, slot) { if (service !== "enchant") return sm0.call(this, service, heroIndex, slot); const gem = this.bag.findIndex((i) => i.kind === "gem" && i.gem === "diamond"), ore = this.bag.findIndex((i) => i.kind === "ingredient" && i.ingredient === "meteoriron");
      if (gem >= 0 || ore < 0) return sm0.call(this, service, heroIndex, slot);
      const stand = { name: "Diamond", kind: "gem", gem: "diamond", power: 0, value: 0, meteor: true }; this.bag.splice(ore, 1, stand); const out = sm0.call(this, service, heroIndex, slot), i = this.bag.indexOf(stand);
      if (i >= 0) this.bag.splice(i, 1, CM.ingredient("meteoriron"));   // (not taken: the work was refused, and the ore is back)
      else { const n = this.messages.length - 1, m = this.messages[n]; if (typeof m === "string" && m.includes("sets the diamond in it")) this.messages[n] = m.replace("sets the diamond in it", "works the meteor iron into it, star-bright at the edge"); }
      return out; }; }
}
