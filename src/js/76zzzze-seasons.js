"use strict";
// Seasons that turn (v24.2, UPGRADE_PLAN_19.md): a run's season comes in over its first days rather than all at once.
// The trees turn a few at a time (the rest still wear last season's crowns: 26-surface.js, `tree:N:was`); through
// autumn the leaves come down and gather on the ground, more each day; in winter the snow builds over the days it
// falls - patchy at first, then whole - and melts back the same way on the days it doesn't (40-render.js uSnow).
{ const day = (game) => (CM.dayOf ? Math.max(0, CM.dayOf(game)) : 0);
  CM.seasonTurn = (game) => (CM.seasonOff ? 1 : Math.min(1, 0.35 + 0.2 * day(game)));   // (by the day: a third turned at the start, all by the fourth)
  CM.leafFall = (game) => (CM.seasonOff || CM.season(game) !== "autumn" ? 0 : Math.min(1, Math.round((day(game) + 1) * 10 / 6) / 10));
  // (CM.snowDepth: in the rules since v27.0 - 69v-weather.js - for the snow slows the Wood)
  // the leaves down: more of them each day of autumn, on the open ground of the town and the land
  const sc0 = CM.scatter;
  CM.scatter = function (fl, seed, density, ctx = {}) {
    const out = sc0.call(this, fl, seed, density, ctx), k = ctx.leafK || 0;
    if (!k || !fl || !CM.isSurface(fl) || !density) return out;
    const size = fl.grid.length, P = CM.PROPS.leaves;
    for (let y = 0; y < size; y++) for (let x = 0; x < size; x++) {
      if (fl.grid[y][x] !== 0 || fl.things[`${x},${y}`]) continue;
      const h = CM.hashSeed(`${seed}:${fl.number}:fall:${x},${y}`); if ((h % 1000) / 1000 >= 0.3 * k) continue;
      const s = P.size[0] + ((h >> 10) % 100) / 100 * (P.size[1] - P.size[0]);
      out.push({ id: "leaves", how: "flat", layer: "prop:leaves", x, y, dx: ((h >> 3) % 50 - 25) / 100, dz: ((h >> 7) % 50 - 25) / 100, w: s, h: s, turn: ((h >> 12) % 628) / 100 });
    }
    return out;
  };
}
