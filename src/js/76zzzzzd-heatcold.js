"use strict";
// Heat and cold (v30.4, UPGRADE_PLAN_25.md): the air shimmers above flames - braziers, the forge, fire on the floor,
// the bigger wall lamps a little - and all through the Foundry and the Root of the World; the party's breath shows
// on a winter's day outdoors and in the cold bands below (the Lich King's Palace, the Drowned Town, the Crystal
// Caverns); ice and crystal walls glint as the eye moves, and so does snow in the sun. renderer.screen (heat, heatAll,
// breath) and renderer.sparkle (40-render.js).
{ const COLD = new Set(["The Lich King's Palace", "The Drowned Town", "The Crystal Caverns"]), HOT = { "The Foundry": 1, "The Root of the World": 0.7 };
  const GLINT = { "The Crystal Caverns": 1, "The Lich King's Palace": 0.45 };
  CM.heatAndCold = (game, r) => { const fl = game.floor; if (!fl) return null; const th = CM.themeFor(fl.number) || {}, sky = Boolean(r.sky);
    const heat = []; for (const l of r.lights || []) { if (!l.flicker || !l.colour || l.colour[0] < l.colour[2] * 1.4) continue; const d = Math.abs(l.x - r.eye[0]) + Math.abs(l.z - r.eye[2]); if (d > 7) continue;
      heat.push([l.x, l.y, l.z, Math.min(1, 0.35 + l.reach / 5) * (l.y < 0.6 ? 1 : 0.5), d]); }
    heat.sort((a, b) => a[4] - b[4]);
    const winter = sky && CM.season(game) === "winter" && (fl.number === 0 || fl.number === -1) && CM.hourOf(game) > 5;
    return { heat: heat.slice(0, 8), heatAll: sky ? 0 : HOT[th.name] || 0, breath: winter || (!sky && COLD.has(th.name)) ? 1 : 0, sparkle: sky ? 0 : GLINT[th.name] || 0 };
  };
  const bf0 = CM.beforeFrame; CM.beforeFrame = (game, r, dt, now) => { if (bf0) bf0(game, r, dt, now); const H = CM.heatAndCold(game, r);
    r.screen = Object.assign(r.screen || {}, { heat: H ? H.heat : [], heatAll: H ? H.heatAll : 0, breath: H && game.mode !== "combat" ? H.breath : 0 }); r.sparkle = H ? H.sparkle : 0; };
}
