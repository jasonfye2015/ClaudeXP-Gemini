"use strict";
// Low fog (v49.2, UPGRADE_PLAN_44.md): mist lies low below ground - a thin skin over every floor, deeper where the floor
// goes down, so the pits and the sunk halls (69zzi-levels.js) fill with it - thicker in the dank bands (the Flooded
// Vaults, the Drowned Town, the Fungal Deep, the Ossuary, the Root); it drifts slowly and stirs as the party moves
// through it, lit by the torch (40-render.js: uLowFog).
{ const BAND = [0.25, 0.7, 0.2, 0.3, 0.75, 0.65, 0.2, 0.15, 0.55, 0.7];
  const bf0 = CM.beforeFrame; CM.beforeFrame = (game, r, dt, now) => { if (bf0) bf0(game, r, dt, now); const fl = game && game.floor; r.lowFog = fl && game.mode !== "title" && fl.number >= 1 && fl.number % 1 === 0 && fl.special !== "vault" ? BAND[CM.themeIndex(fl.number)] || 0.25 : 0; }; }
