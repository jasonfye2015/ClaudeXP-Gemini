"use strict";
// The light of the hour (v59.0, UPGRADE_PLAN_54.md): what colour the sun's light is, how much mist lies on the water,
// and how much the lamps glow in the air - by the clock, the season and the weather. The window's side applies them
// (76zzzzzzzzzz7-light.js, 40-render.js); nothing here touches the rules.
//   CM.sunColour(game) -> { col: [r, g, b], glow }   the sun's colour on what it lights (gold at the horizon, white at
//                                                     noon; silver-blue under the moon) and the glow about it in the sky
//   CM.waterMist(game) -> 0..1                      mist lying on the water and its banks: at dawn in clear weather,
//                                                     on autumn evenings, thickest in autumn and spring
//   CM.haloAir(game) -> 0..1                        the lights' halos in the night air: most in mist and rain
{ const mix = (a, b, k) => a.map((v, i) => v + (b[i] - v) * k), clamp = (v, lo = 0, hi = 1) => Math.max(lo, Math.min(hi, v));
  CM.SUN_GOLD = [1.0, 0.74, 0.46]; CM.MOON_SILVER = [0.78, 0.84, 1.0];
  CM.sunColour = (game) => {
    const sky = CM.sky(game), [dawn, dusk] = CM.daylightOf(game), h = CM.hourOf(game); if (!sky || sky.light <= 0.15 || h < dawn - 0.5 || h > dusk + 0.5) return { col: CM.MOON_SILVER.slice(), glow: 0 };
    const low = clamp(1 - Math.min(h - (dawn - 0.5), dusk + 0.5 - h) / 2.2);   // 1 at the horizon, 0 two hours in
    const w = CM.weather ? CM.weather(game) : "clear", clear = { clear: 1, wind: 0.85, mist: 0.5, snow: 0.3, rain: 0.15 }[w] ?? 0.6;
    return { col: mix([1, 1, 1], CM.SUN_GOLD, low * (0.4 + 0.6 * clear)), glow: low * clear }; };
  CM.waterMist = (game) => {
    const fl = game && game.floor; if (!fl || !(fl.number === 0 || fl.number === -1)) return 0;
    const w = CM.weather ? CM.weather(game) : "clear"; if (w === "rain" || w === "snow") return 0;
    const [dawn, dusk] = CM.daylightOf(game), h = CM.hourOf(game), s = CM.season ? CM.season(game) : "spring";
    const bySeason = { autumn: 1, spring: 0.8, winter: 0.6, summer: 0.45 }[s] ?? 0.7;
    const morning = h < dawn - 0.5 ? 0 : h < dawn + 0.5 ? (h - (dawn - 0.5)) : clamp(1 - (h - (dawn + 0.5)) / 2);                        // rising before dawn, gone two hours after
    const evening = s === "autumn" || s === "spring" ? clamp(1 - Math.abs(h - dusk) / 1.2) * 0.6 : 0;                                // an autumn (or spring) evening's mist off the water
    return clamp(Math.max(morning, evening) * bySeason * (w === "mist" ? 1.15 : w === "wind" ? 0.5 : 1)); };
  CM.haloAir = (game) => {
    if (!game || !game.floor || !(game.floor.number === 0 || game.floor.number === -1)) return 0;
    const [dawn, dusk] = CM.daylightOf(game), h = CM.hourOf(game), dark = h >= dusk + 0.5 || h < dawn - 0.5 ? 1 : clamp(1 - CM.sky(game).light / 0.5), w = CM.weather ? CM.weather(game) : "clear";   // full dark from half an hour after dusk
    return dark * ({ mist: 1, rain: 0.9, snow: 0.7, clear: 0.22, wind: 0.12 }[w] ?? 0.3); };
}
