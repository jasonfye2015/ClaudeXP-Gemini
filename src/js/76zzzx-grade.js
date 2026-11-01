"use strict";
// Grade and hour (v22.4, UPGRADE_PLAN_17.md): each band its own grade - a lift in the shadows, a contrast, a
// saturation - not only a tint: the Lich King's Palace cold and hard, the Ossuary drained, the Crystal Caverns vivid,
// the Foundry hot. On the surface the hour colours everything: gold at dawn and dusk, blue in the hour after, the
// colours drained at night. Winter mornings frost the walls. 40-render.js applies it (uGrade, uLift, uLook);
// 80-main.js asks here each frame.
{ const BANDS = { "The Catacombs": [[0.012, 0.006, 0], 1.05, 0.95], "The Flooded Vaults": [[0, 0.01, 0.016], 1.0, 0.88], "The Dwarven Halls": [[0.016, 0.008, 0], 1.08, 1.05],
    "The Lich King's Palace": [[0, 0.006, 0.022], 1.12, 0.78], "The Drowned Town": [[0, 0.012, 0.02], 0.95, 0.85], "The Fungal Deep": [[0.004, 0.016, 0], 1.0, 1.15],
    "The Crystal Caverns": [[0.01, 0, 0.022], 1.1, 1.2], "The Foundry": [[0.022, 0.006, 0], 1.12, 1.1], "The Ossuary": [[0.01, 0.01, 0.008], 1.0, 0.7], "The Root of the World": [[0.022, 0, 0], 1.15, 1.1] };
  CM.GRADE_BANDS = BANDS;
  const mix = (a, b, k) => a.map((v, i) => v + (b[i] - v) * k), bump = (h, at, w) => Math.max(0, 1 - Math.abs(h - at) / w);
  CM.gradeFor = (game, renderer) => { const fl = game.floor; if (!fl || CM.gradeOff) return null; const t = CM.themeFor(fl.number), sky = renderer.sky;
    if (!sky) { const b = t.undercroft ? [[0, 0.01, 0.01], 0.98, 0.85] : t.tower ? [[0.008, 0, 0.02], 1.05, 1.05] : t.joker ? [[0.015, 0.005, 0], 1.05, 1.1] : BANDS[t.name] || [[0, 0, 0], 1, 1];
      return { mul: [1, 1, 1], lift: b[0], con: b[1], sat: b[2], frost: 0 }; }
    const h = CM.hourOf ? CM.hourOf(game) % 24 : 12, gold = Math.max(bump(h, 6.5, 2), bump(h, 18, 2)), blue = Math.max(bump(h, 20, 1.3), bump(h, 4.6, 1)) * (1 - gold);
    let mul = mix([1, 1, 1], [1.1, 0.97, 0.82], gold * 0.8); mul = mix(mul, [0.88, 0.93, 1.08], blue * 0.8);
    if (sky.night) mul = mix(mul, [0.9, 0.95, 1.06], 0.7);
    const sat = sky.night ? 0.62 : 1.06 - 0.2 * blue, winter = game.season === "winter" || renderer.season === "winter";
    return { mul, lift: [0, 0, 0], con: 1.04, sat, frost: winter && h >= 4 && h < 10.5 ? Math.min(1, (10.5 - h) / 3) : 0 }; };
}
