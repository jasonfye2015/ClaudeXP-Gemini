"use strict";
// Ground that blends (v54.0, UPGRADE_PLAN_49.md): in the town and the land the grounds no longer meet in hard lines -
// near the edge of a square, its neighbour's ground fades into it, the line wandering with the noise, so grass runs into
// the dirt of a path, cobbles into flags, moss into litter. (40-render.js: uGBlend; each square's ground is in the map's
// blue.) Off at Low detail.
{ const bf0 = CM.beforeFrame; CM.beforeFrame = (game, r, dt, now) => { if (bf0) bf0(game, r, dt, now); r.gBlend = game && game.settings && game.settings.detail === "low" ? 0 : 1; }; }
