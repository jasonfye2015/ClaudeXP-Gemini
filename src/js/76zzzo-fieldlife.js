"use strict";
// The South Fields, finished (v19.5, UPGRADE_PLAN_14.md phase 5): the field through the year and the crew at work.
// - The seasons on the earth: frost on bare turned plots in winter, blossom along the rows in spring, fallen leaves in
//   autumn (a few plots each, by the seed, the same every visit).
// - The crew in the rows: the hands hired (one to three) stand at work among the crops, each in a different place
//   every hour of the day, and go home at night.
{ // (the hands are painted in 36c-cropart.js: npc:fieldhand0-2)
  const h = (game, what) => CM.hashSeed(`${game.seed}:fieldlife:${what}`);
  // where the hands are this hour: on plots with something growing (or any plot of the fields)
  CM.fieldHandsAt = (game) => { const F = game.fields(), n = Math.min(3, F.crew || 0); if (!n || (F.purse || 0) <= 0 && F.unpaid || CM.isNight && CM.isNight(game)) return {};
    const hour = Math.floor((game.clock || 0) / 60), cells = CM.fieldCells(game.fieldsLevel()).map(([x, y]) => `${x},${y}`), busy = cells.filter((k) => F.plots[k] && F.plots[k].crop && !F.plots[k].giant), pool = busy.length >= n ? busy : cells, out = {};
    for (let i = 0; i < n; i++) { let k = pool[h(game, `hand:${i}:${hour}`) % pool.length]; for (let t = 1; out[k] !== undefined && t < pool.length; t++) k = pool[(h(game, `hand:${i}:${hour}`) + t) % pool.length]; out[k] = i; } return out; };
  { const ps0 = CM.plotSprites; CM.plotSprites = (game, key, x, y) => { const out = ps0(game, key, x, y), P = game.fields().plots[key], season = CM.season(game), r = h(game, `deco:${key}`) % 10;
      if (P && P.t && !P.crop && !P.spr && season === "winter") out.push({ x, y, layer: "prop:frost", flat: true, w: 0.9 });
      else if (season === "spring" && r < 2) out.push({ x, y, dx: r ? 0.38 : -0.38, dz: 0.38, layer: "prop:flowers", w: 0.3, h: 0.3 });
      else if (season === "autumn" && r < 3) out.push({ x, y, dx: (r - 1) * 0.25, dz: -0.2, layer: "prop:leaves", flat: true, w: 0.5 });
      const hk = `${Math.floor((game.clock || 0) / 60)}:${game.fields().crew || 0}:${game.fieldsLevel()}`, at = game.fieldHandsCache && game.fieldHandsCache.hour === hk ? game.fieldHandsCache.at : (game.fieldHandsCache = { hour: hk, at: CM.fieldHandsAt(game) }).at;
      if (at[key] !== undefined) out.push({ x, y, dx: 0.05, dz: 0.3, layer: `npc:fieldhand${at[key]}`, w: 0.62, h: 0.8, lift: Math.abs(Math.sin((typeof performance !== "undefined" ? performance.now() : 0) / 500 + at[key])) * 0.03 });
      return out; }; }
}
