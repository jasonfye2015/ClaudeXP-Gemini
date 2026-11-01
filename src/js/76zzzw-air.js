"use strict";
// Air (v22.3, UPGRADE_PLAN_17.md): the air has a body. Below, each band its own: the Drowned Town and the Undercroft
// thick and drifting, the Foundry hazy with smoke, the Fungal Deep with spores, the Catacombs only a little; the
// torch and every lamp glow in it. Above, the Wood's hollows lie misty at dawn and the town's lanes a little; by day,
// looking toward the sun, bars of light stand in the Wood's air and, fainter, in the town's lanes. 40-render.js draws
// it (uHaze, uShaft); 80-main.js asks here each frame.
{ const BANDS = { "The Catacombs": 0.3, "The Flooded Vaults": 0.55, "The Dwarven Halls": 0.35, "The Lich King's Palace": 0.45, "The Drowned Town": 0.95, "The Fungal Deep": 0.65,
    "The Crystal Caverns": 0.3, "The Foundry": 0.7, "The Ossuary": 0.35, "The Root of the World": 0.55 };
  CM.AIR_BANDS = BANDS;
  CM.airFor = (game, renderer) => { const fl = game.floor; if (!fl || CM.airOff) return null; const n = fl.number, t = CM.themeFor(n), sky = renderer.sky;
    if (sky) { const h = CM.hourOf ? CM.hourOf(game) % 24 : 12, dawn = h >= 4.5 && h < 9 ? 1 - Math.abs(h - 6.5) / 2.5 : 0, rain = CM.weather && CM.weather(game) === "rain";
      const wood = n === -1, haze = (wood ? 0.18 + 0.6 * dawn : 0.08 + 0.3 * dawn) + (sky.night ? 0.12 : 0), up = sky.sun !== null && sky.light > 0.25 && !rain;
      return { haze, shaft: up ? (wood ? 1.0 : 0.45) * Math.min(1, (sky.light - 0.25) * 2.5) : 0 }; }
    return { haze: t.undercroft ? 0.85 : t.tower ? 0.25 : t.joker ? 0.2 : BANDS[t.name] !== undefined ? BANDS[t.name] : 0.3, shaft: 0 }; };
}
