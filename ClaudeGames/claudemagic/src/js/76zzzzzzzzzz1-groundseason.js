"use strict";
// The season on the ground (v54.4, UPGRADE_PLAN_49.md): in autumn the fallen leaves drift against the walls and the kerbs
// (as the season turns, more of them); in winter the snow settles in along the walls and the edges first, filling the
// open ground last; and after rain - while it rains, and the morning after - the earth of the paths and the worn grass
// go to mud. (40-render.js: uGSeason [leaves, mud, -].)
{ const bf0 = CM.beforeFrame; CM.beforeFrame = (game, r, dt, now) => { if (bf0) bf0(game, r, dt, now); const fl = game && game.floor; if (!fl || (fl.number !== 0 && fl.number !== -1) || game.mode === "title") { r.gSeason = null; return; }
    const season = CM.season ? CM.season(game) : "summer", leaves = season === "autumn" ? Math.max(0.35, CM.leafFall ? CM.leafFall(game) || 0 : 0.6) : 0;
    const d = CM.dayOf(game), h = CM.hourOf(game), rain = CM.weather(game) === "rain", after = !rain && d > 0 && h < 14 && CM.weatherOf && CM.weatherOf(game.seed, d - 1, season) === "rain";
    r.gSeason = [leaves, rain ? 1 : after ? 0.7 * (h < 7 ? 1 : 1 - (h - 7) / 7) : 0, 0]; }; }
