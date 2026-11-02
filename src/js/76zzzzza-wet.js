"use strict";
// Wet surfaces (v30.0, UPGRADE_PLAN_25.md): in the rain the stone and the cobbles darken and shine and puddles lie in
// the low places, ringing; the morning after a day of rain the sheen dries in the first hour of sun and the puddles
// shrink till noon. (Not on lying snow: it is frozen.) The renderer's uWet, uRain and uPuddle (40-render.js).
{ CM.wetNow = (game) => {
    if (!game || game.seed === undefined) return { wet: 0, rain: 0, puddle: 0 };
    const w = CM.weather(game); if (w === "rain") return { wet: 1, rain: 1, puddle: 1 };
    const day = CM.dayOf(game); if (day <= 0 || CM.weatherOf(game.seed, day - 1, CM.season(game)) !== "rain" || (CM.snowLying && CM.snowLying(game))) return { wet: 0, rain: 0, puddle: 0 };
    const h = CM.hourOf(game), dawn = CM.daylightOf(game)[0], clamp = (v) => Math.max(0, Math.min(1, v));
    return { wet: clamp(1 - (h - dawn)), rain: 0, puddle: clamp(1 - (h - dawn) / Math.max(1, 12 - dawn)) * 0.8 };
  };
  const bf0 = CM.beforeFrame; CM.beforeFrame = (game, r, dt, now) => { if (bf0) bf0(game, r, dt, now);
    const W = r.sky ? CM.wetNow(game) : { wet: 0, rain: 0, puddle: 0 }; r.wet = W.wet; r.rain = W.rain; r.puddle = W.puddle; };
}
