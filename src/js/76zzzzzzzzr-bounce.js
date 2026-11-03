"use strict";
// Bounced light (v49.1, UPGRADE_PLAN_44.md): what the torch lights on the floor it throws back up - the foot of the walls
// takes a warmth in the floor's own colour, fading as they rise, and the ceiling a little of it - a red floor
// reddening the stone, a pale one lightening it (40-render.js: uBounce, from the band's floor). Below ground only.
{ const bf0 = CM.beforeFrame; CM.beforeFrame = (game, r, dt, now) => { if (bf0) bf0(game, r, dt, now); const fl = game && game.floor; if (!fl || game.mode === "title" || fl.number === 0 || fl.number === -1) { r.bounce = null; return; }
    const T = CM.themeFor(fl.number) || {}, c = T.floor || [80, 70, 60], k = 0.0042; r.bounce = [c[0] * k, c[1] * k, c[2] * k]; }; }
