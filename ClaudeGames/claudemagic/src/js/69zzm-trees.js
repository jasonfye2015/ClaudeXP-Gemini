"use strict";
// Trees that fall, burn and grow again (v74.0, UPGRADE_PLAN_61.md part 4): a gale fells a tree now and then and a
// tornado fells what stands in its wake; lightning in a storm sets one alight, and fire spreads tree to tree (less in
// rain, not in snow, out in a downpour) but never to a building, a fence or the party - it is a sight, not a harm.
// A burning tree burns BURN minutes and falls charred; a fallen or charred tree lies three days and then a sapling
// stands in its place, which is a tree again seven days on. The square stays solid the whole way (a lying tree is a
// different picture, not an open square), so nothing opens a way off the map. The lamps: in a storm or a gale a
// town lamp may blow out, and stays dark till the lamplighter's next round. State lives in the run (game.ext).
//   CM.treeSquares(fl) -> ["x,y"]                     every tree square of a surface floor
//   CM.treeStateAt(game, fl, x, y) -> null | "fallen" | "burning" | "charred" | "sapling"
//   CM.treeStateMap(game, fl) -> { "x,y": state }      for the mesh (26-surface.js reads opts.treeStates)
//   CM.fellTree / CM.igniteTree(game, fl, key)          by a gale, a tornado, lightning - or a meteor (part 5)
//   CM.treesStep(game, minutes)                         the timers, the spread, the gale's and the twister's felling
//   CM.lampsOut(game) -> { "x,y": at }; CM.lampOutStep(game, minutes); CM.lampOn wrapped to keep a blown lamp dark
{ const T = CM.TREES = { burnMinutes: 40, fallenDays: 3, saplingDays: 7, spread: 0.03, galePerMinute: 1 / 12, tornadoReach: 1.3, lightningPerMinute: 0.004, lampPerHour: 0.1, maxBurning: 12 };
  const rnd = () => (CM.wxRandom ? CM.wxRandom() : Math.random()), DAY = 24 * 60;
  const cache = new WeakMap();
  CM.treeSquares = (fl) => { if (!fl || !(fl.number === 0 || fl.number === -1)) return []; let c = cache.get(fl); if (c) return c; c = []; const N = fl.grid.length; for (let y = 0; y < N; y++) for (let x = 0; x < N; x++) if (fl.grid[y][x] !== 0 && CM.solidAt(fl, x, y) === "tree") c.push(`${x},${y}`); cache.set(fl, c); return c; };
  const store = (game, fl) => { const E = game.ext("trees"); return (E[fl.number] = E[fl.number] || {}); };
  CM.treeStateAt = (game, fl, x, y) => { if (!game || !game.ext || !fl) return null; const s = store(game, fl)[`${x},${y}`]; return s ? s.s : null; };
  CM.treeStateMap = (game, fl) => { const out = {}; if (!game || !game.ext || !fl) return out; for (const [k, v] of Object.entries(store(game, fl))) out[k] = v.s; return out; };
  CM.fellTree = (game, fl, key, how) => { const S = store(game, fl), s = S[key]; if (s && s.s !== "burning") return false; S[key] = { s: s && s.s === "burning" ? "charred" : "fallen", at: CM.clockOf(game), how: how || "gale" }; game.treesVersion = (game.treesVersion || 0) + 1; return true; };
  CM.igniteTree = (game, fl, key) => { const S = store(game, fl); if (S[key]) return false; if (Object.values(S).filter((v) => v.s === "burning").length >= T.maxBurning) return false; S[key] = { s: "burning", at: CM.clockOf(game) }; game.treesVersion = (game.treesVersion || 0) + 1; return true; };
  const neighbours = (key) => { const [x, y] = key.split(",").map(Number), out = []; for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) if (dx || dy) out.push(`${x + dx},${y + dy}`); return out; };
  CM.treesStep = (game, minutes = 1) => { if (!game || !game.ext || !game.floor || !(minutes > 0)) return; const fl = game.floor, S = store(game, fl), t = CM.clockOf(game), trees = CM.treeSquares(fl), set = new Set(trees); if (!trees.length) return;
    const W = CM.weatherNow ? CM.weatherNow(game) : { kind: "clear", strength: 0, wind: { speed: 0 } }, rainK = W.kind === "rain" || W.kind === "storm" ? W.strength : 0, snow = W.kind === "snow"; let changed = false;
    for (const [k, v] of Object.entries(S)) {   // the timers
      if (v.s === "burning" && (t - v.at >= T.burnMinutes || rainK > 0.7)) { v.s = "charred"; v.at = t; changed = true; }
      else if ((v.s === "fallen" || v.s === "charred") && t - v.at >= T.fallenDays * DAY) { v.s = "sapling"; v.at = t; changed = true; }
      else if (v.s === "sapling" && t - v.at >= T.saplingDays * DAY) { delete S[k]; changed = true; } }
    const burning = Object.keys(S).filter((k) => S[k].s === "burning"); const p = T.spread * (snow ? 0 : 1 - 0.7 * rainK);   // the spread, a chance a minute for each burning neighbour
    if (p > 0) for (const k of burning) for (const n of neighbours(k)) { if (!set.has(n) || S[n]) continue; if (1 - Math.pow(1 - p, minutes) > rnd()) { if (CM.igniteTree(game, fl, n)) changed = true; } }
    const tw = CM.twisterNow ? CM.twisterNow(game) : null;
    if (!(tw && tw.inside) && W.wind.speed > 0.8 && rnd() < T.galePerMinute * minutes * (W.wind.speed - 0.7) / 0.3) { const standing = trees.filter((k) => !S[k]); if (standing.length) { CM.fellTree(game, fl, standing[Math.floor(rnd() * standing.length)], "gale"); changed = true; } }   // the gale
    if (tw && tw.inside) for (const k of trees) { if (S[k] && S[k].s !== "burning") continue; const [x, y] = k.split(",").map(Number); if (Math.hypot(x + 0.5 - tw.x, y + 0.5 - tw.y) <= T.tornadoReach) { CM.fellTree(game, fl, k, "tornado"); changed = true; } }   // the twister's wake
    if (W.kind === "storm" && rnd() < T.lightningPerMinute * minutes) { const standing = trees.filter((k) => !S[k]); if (standing.length && CM.igniteTree(game, fl, standing[Math.floor(rnd() * standing.length)])) changed = true; }   // lightning
    if (changed) game.treesVersion = (game.treesVersion || 0) + 1; };
  // the lamps: blown out in a storm or a gale, dark till the lamplighter's round
  CM.lampsOut = (game) => (game && game.ext ? game.ext("lampsOut") : {});
  CM.lampOutStep = (game, minutes = 1) => { if (!game || !game.ext || !game.floor || game.floor.number !== 0) return; const O = CM.lampsOut(game), h = CM.hourOf(game), LH = CM.LAMPLIGHT || { from: 19, to: 21 };
    if (h >= LH.from && h < LH.to) { for (const k of Object.keys(O)) delete O[k]; return; }   // (his round relights them all)
    const W = CM.weatherNow ? CM.weatherNow(game) : null; if (!W || !(W.kind === "storm" || W.wind.speed > 0.8)) return;
    const lamps = CM.renderer && CM.renderer.standing ? CM.renderer.standing.filter((p) => p.id === "lamp") : []; for (const p of lamps) { const k = `${p.x},${p.y}`; if (!O[k] && rnd() < T.lampPerHour * minutes / 60) O[k] = CM.clockOf(game); } };
  CM.lampBlownOut = (game, p) => Boolean(p && game && game.ext && CM.lampsOut(game)[`${p.x},${p.y}`]);   // (the window wraps CM.lampOn with it: the lamplighter's file loads after this one)
}
