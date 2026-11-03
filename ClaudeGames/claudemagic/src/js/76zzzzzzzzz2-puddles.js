"use strict";
// Water to see (v51.2, UPGRADE_PLAN_46.md): the puddles of a rainy day (80-main.js) no longer vanish when it stops - the
// next morning they still lie in the roads and paths of the town and the land, the same ones, holding the sky, and dry
// away shrinking as the day goes on, gone by early afternoon. With the Wood's river running, and the rain's own puddles.
{ const yesterdayRained = (game) => { if (!CM.weatherOf || !CM.season) return false; const d = CM.dayOf(game); return d > 0 && CM.weatherOf(game.seed, d - 1, CM.season(game)) === "rain"; };
  const cache = new WeakMap();
  { const ls0 = CM.lifeSprites; CM.lifeSprites = (game, fl, now) => { const out = ls0 ? ls0(game, fl, now) : []; if (!fl || (fl.number !== 0 && fl.number !== -1) || game.mode === "title" || !CM.renderer || CM.renderer.index.water0 === undefined) return out;
      const h = CM.hourOf(game); if (CM.weather(game) === "rain" || h >= 14 || !yesterdayRained(game)) return out; const k = h < 7 ? 1 : 1 - (h - 7) / 7, day = CM.dayOf(game) - 1;
      let list = cache.get(fl); if (!list || list.day !== day) { list = []; list.day = day; const N = fl.grid.length; for (let y = 0; y < N; y++) for (let x = 0; x < N; x++) { const g = CM.groundAt(fl, x, y), hh = CM.hashSeed(`${game.seed}:puddle:${day}:${x}:${y}`);
          if (fl.grid[y][x] === 0 && !fl.things[`${x},${y}`] && ["dirt", "cobbles", "flags"].includes(g) && hh % 4 === 0) list.push({ x, y, phase: hh % 3, w: 0.35 + (hh % 7) * 0.04, dx: ((hh >> 4) % 40 - 20) / 100, dz: ((hh >> 9) % 40 - 20) / 100 }); } cache.set(fl, list); }
      const fr = Math.floor(now / 400) % 3;
      for (const w of list) { if (Math.abs(w.x - fl.pos[0]) + Math.abs(w.y - fl.pos[1]) > 12) continue; const sz = w.w * (0.35 + 0.65 * k); if (sz < 0.12) continue; out.push({ x: w.x, y: w.y, dx: w.dx, dz: w.dz, flat: true, w: sz, layer: `water${(fr + w.phase) % 3}`, alpha: 0.75, water: true }); }
      return out; }; }
}
