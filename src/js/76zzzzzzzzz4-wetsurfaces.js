"use strict";
// Weather on the surfaces (v51.4, UPGRADE_PLAN_46.md): while it rains, the rain is seen running down the town's walls
// in streaks (40-render.js); and the morning after a rainy day the cobbles and the walls are still wet - darker, shining
// a little - drying as the day warms, dry by early afternoon (with the puddles of 76zzzzzzzzz2-puddles.js). Snow lies on
// the sills and the tops of things as it did.
{ const bf0 = CM.beforeFrame; CM.beforeFrame = (game, r, dt, now) => { if (bf0) bf0(game, r, dt, now); const fl = game && game.floor;
    if (!fl || (fl.number !== 0 && fl.number !== -1) || game.mode === "title" || !r.sky || !CM.weatherOf || CM.weather(game) === "rain") return; const d = CM.dayOf(game), h = CM.hourOf(game);
    if (d < 1 || h >= 14 || CM.weatherOf(game.seed, d - 1, CM.season(game)) !== "rain") return; r.wet = Math.max(r.wet || 0, 0.7 * (h < 7 ? 1 : 1 - (h - 7) / 7)); }; }
