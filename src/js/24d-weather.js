"use strict";
// Weather in the small things (v60.0, UPGRADE_PLAN_55.md): a rainbow when the low sun comes through the rain, frost on
// the ground on a clear cold morning, and the rain dripping from the eaves. The window's side draws them
// (76zzzzzzzzzz8-weather2.js, 40-render.js); nothing here touches the rules.
//   CM.rainbowNow(game) -> 0..1     a rainy day's sun-shower: in the second hour after dawn and the late afternoon
//                                   the cloud thins, the rain eases and a bow stands opposite the sun
//   CM.groundFrost(game) -> 0..1    hoar frost on the ground: a clear or windy morning in winter or autumn, from an
//                                   hour before dawn and gone two hours after it (none under lying snow)
//   CM.eavesOf(fl) -> [{ x0, z0, x1, z1, y }]   the eave lines of a surface floor's buildings, where the rain runs off
{ const clamp = (v, lo = 0, hi = 1) => Math.max(lo, Math.min(hi, v));
  CM.rainbowNow = (game) => {
    const fl = game && game.floor; if (!fl || !(fl.number === 0 || fl.number === -1)) return 0;
    if ((CM.weather ? CM.weather(game) : "clear") !== "rain") return 0;
    const [dawn, dusk] = CM.daylightOf(game), h = CM.hourOf(game);
    const bell = (c) => clamp(1 - Math.abs(h - c) / 0.75);                        // an hour and a half, peaking at its middle
    return Math.max(bell(dawn + 1.5), bell(Math.min(dusk - 1.5, 16.5))); };   // (the evening's while the sun is still on its arc - it sets at six by the sky's reckoning, 24-clock.js)
  CM.groundFrost = (game) => {
    const fl = game && game.floor; if (!fl || !(fl.number === 0 || fl.number === -1)) return 0;
    const s = CM.season ? CM.season(game) : "spring"; if (s !== "winter" && s !== "autumn") return 0;
    const w = CM.weather ? CM.weather(game) : "clear"; if (w !== "clear" && w !== "wind") return 0;
    if (CM.snowLying && CM.snowLying(game)) return 0;
    const [dawn] = CM.daylightOf(game), h = CM.hourOf(game), k = s === "winter" ? 1 : 0.7;
    return k * (h < dawn - 1 ? 0 : h < dawn ? h - (dawn - 1) : clamp(1 - (h - dawn) / 2)); };
  CM.eavesOf = (fl) => { const out = []; if (!fl || !CM.buildingsOf || !CM.ROOF) return out; const g = CM.ROOF.gableOverhang || 0;
    for (const B of CM.buildingsOf(fl)) { const ax = B.along === "x", X0 = B.x0, X1 = B.x1 + 1, Z0 = B.y0, Z1 = B.y1 + 1, o = B.overhang || 0;
      const U0 = ax ? X0 : Z0, U1 = ax ? X1 : Z1, V0 = ax ? Z0 : X0, V1 = ax ? Z1 : X1, mid = (V0 + V1) / 2, half = (V1 - V0) / 2, y = B.h - (o * B.rise) / half;
      for (const side of [-1, 1]) { const v = mid + side * (half + o); out.push(ax ? { x0: U0 - g, z0: v, x1: U1 + g, z1: v, y } : { x0: v, z0: U0 - g, x1: v, z1: U1 + g, y }); } }
    return out; };
}
