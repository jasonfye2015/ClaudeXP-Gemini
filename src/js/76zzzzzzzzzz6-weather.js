"use strict";
// Weathering (v57.4, UPGRADE_PLAN_52.md): moss creeping up the feet of the town's walls in patches (40-render.js: uMoss),
// stains run down from under the window sills, and ivy climbing some walls (26b-buildings.js, 26i-wall.js). Less moss
// in a dry summer, more in a wet autumn.
{ const bf0 = CM.beforeFrame; CM.beforeFrame = (game, r, dt, now) => { if (bf0) bf0(game, r, dt, now); const fl = game && game.floor;
    if (!fl || fl.number !== 0 || game.mode === "title") { r.moss = 0; return; } const s = CM.season ? CM.season(game) : "summer"; r.moss = { spring: 1, summer: 0.75, autumn: 1, winter: 0.85 }[s] || 0.9; }; }
