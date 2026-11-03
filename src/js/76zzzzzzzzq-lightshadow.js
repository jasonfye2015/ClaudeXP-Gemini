"use strict";
// Shadows from the walls (v49.0, UPGRADE_PLAN_44.md): the lamps, wall torches, braziers and spell-lights no longer shine
// through stone - each of the eight nearest is traced to the square it lights across the floor's map, and where a wall
// stands between them its light stops, softly at the edge, so a torch round a corner lights only its own side of it
// (40-render.js: uLShadow). The party's own torch, held at the eye, sees what the party sees. Off at Low detail.
{ const bf0 = CM.beforeFrame; CM.beforeFrame = (game, r, dt, now) => { if (bf0) bf0(game, r, dt, now); CM.lightShadowsOff = Boolean(game && game.settings && game.settings.detail === "low"); }; }
