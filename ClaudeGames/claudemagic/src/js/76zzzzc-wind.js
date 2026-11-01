"use strict";
// Wind (v24.0, UPGRADE_PLAN_19.md): on the surface the wind blows from a way of its own each day, in gusts that roll
// across the land - the trees, the grass, the reeds, the flowers and the crops all give to it together, and the
// scarecrow's coat flaps. Rain brings it up, mist lays it down, and below ground there is none. 26-surface.js marks what
// grows (CM.SWAY), 40-render.js bends it (uWind; a billboard with `sway` by CM.windAt), 80-main.js asks here each frame.
{ CM.windFor = (game, renderer) => {
    if (!renderer.sky || CM.windOff) return null;
    const day = CM.dayOf ? CM.dayOf(game) : 0, h = CM.hashSeed(`${game.seed}:wind:${day}`), a = (h % 360) * Math.PI / 180, w = CM.weather ? CM.weather(game) : "clear";
    const k = (0.45 + ((h >> 9) % 50) / 100) * (w === "rain" ? 1.5 : w === "snow" ? 0.8 : w === "mist" ? 0.2 : 1);
    return { dir: [Math.cos(a), Math.sin(a)], k };
  };
  CM.windAt = (x, z, t, W) => {                                          // (the shader's own sum, for what is drawn as a billboard)
    const along = x * W.dir[0] + z * W.dir[1], g = 0.5 + 0.5 * Math.sin(t * 0.9 - along * 0.35);
    return W.k * (0.3 + 0.7 * g * g + 0.22 * Math.sin(t * 3.1 + x * 1.7 + z * 2.3));
  };
  // the crops and the scarecrow give too
  const ps0 = CM.plotSprites; if (ps0) CM.plotSprites = (game, key, x, y) => ps0(game, key, x, y).map((s) => (/^crop|^crops/.test(s.layer) && !s.flat ? Object.assign(s, { sway: 0.06 * (s.h || 0.6) }) : s));
}
