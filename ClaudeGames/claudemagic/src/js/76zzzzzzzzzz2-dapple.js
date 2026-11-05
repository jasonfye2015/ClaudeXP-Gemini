"use strict";
// Dappled light (v55.5, UPGRADE_PLAN_50.md): in the Deep Wood by day the sun comes through the leaves in soft patches of
// light and shade on the forest floor, drifting slowly as the breeze moves the crowns, most under and beside the trees
// (40-render.js: uDapple). Full on a clear day, softer under cloud, faint in the rain, none at night, none at Low detail.
{ const bf0 = CM.beforeFrame; CM.beforeFrame = (game, r, dt, now) => { if (bf0) bf0(game, r, dt, now); const fl = game && game.floor;
    if (!fl || fl.number !== -1 || game.mode === "title" || (game.settings && game.settings.detail === "low")) { r.dapple = 0; return; }
    const h = CM.hourOf(game), day = Math.max(0, Math.min(1, (h - 6) / 2.5, (20 - h) / 2.5)), w = CM.weather ? CM.weather(game) : "clear";
    r.dapple = day * ({ clear: 1, cloudy: 0.45, overcast: 0.3, mist: 0.25, rain: 0.15, storm: 0.1, snow: 0.3 }[w] ?? 0.6); }; }
