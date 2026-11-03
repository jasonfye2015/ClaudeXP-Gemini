"use strict";
// Floor detail (v48.4, UPGRADE_PLAN_43.md): below ground the floor shows how it has been walked on - a path worn paler
// and smoother down the middle of every corridor and room, away from the walls where feet don't go - and the joints of
// its flags, two to a square and staggered, faint in the stone (40-render.js: uWorn). Not in the town or the Wood.
{ const bf0 = CM.beforeFrame; CM.beforeFrame = (game, r, dt, now) => { if (bf0) bf0(game, r, dt, now); const fl = game && game.floor; r.worn = fl && game.mode !== "title" && fl.number !== 0 && fl.number !== -1 ? 1 : 0; }; }
