"use strict";
// Wet stone and dry dust (v48.1, UPGRADE_PLAN_43.md): the Flooded Vaults and the Drowned Town are damp - their stone
// darker, streaked where the water runs down the walls, and shining where the torch catches it - and so is any floor
// the party wades; the Ossuary is dry, a pale dust lying on its floors and on all that faces up, and nothing in it
// shines. (40-render.js: uDamp, uDust.)
{ const bf0 = CM.beforeFrame; CM.beforeFrame = (game, r, dt, now) => { if (bf0) bf0(game, r, dt, now); const fl = game && game.floor;
    if (!fl || !(fl.number >= 1) || game.mode === "title") { r.damp = 0; r.dust = 0; return; } const b = CM.themeIndex(fl.number);
    r.damp = b === 1 || b === 4 ? 0.85 : fl.special === "wading" || fl.tide ? 0.6 : 0; r.dust = b === 8 ? 0.75 : 0; }; }
