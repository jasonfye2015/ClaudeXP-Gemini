"use strict";
// The river's life (v62.0, UPGRADE_PLAN_57.md): what lives on and over the Deep Wood's river, by the rules so the tests
// can hold it - a pair of ducks drifting a slow stretch and paddling back up it, dragonflies over the water on a summer's
// day, and the lily pads and duckweed that lie in the slack water by the banks in the warm months. The window's side
// draws them (76zzzzzzzzzza-waterlife.js, 40-render.js). Nothing here touches the rules of play.
//   CM.riverSquares(fl) -> [[x, y]]                 the river's water squares (the Wood's decor)
//   CM.ducksOf(fl) -> [{ stretch: [[x, y]...], n }]   two stretches of river, away from the ford, a pair on each
//   CM.duckPose(group, i, t) -> { x, y, mirror, dip }   where duck i is at t seconds: drifting down the stretch, then paddling back
//   CM.ducksOut(game) -> bool                        by day, not when the river is frozen
//   CM.dragonfliesNow(game) -> 0..1                  summer and late spring, by day, not in rain or wind
//   CM.lilyNow(game) -> 0..1                         the pads by season: full in summer, some in spring and autumn, none in winter
{ CM.riverSquares = (fl) => (fl && fl.number === -1 ? (fl.decor || []).filter((d) => d.kind === "water" && d.x === CM.riverX(d.y)).map((d) => [d.x, d.y]) : []);   /* (v128.0: the river itself - not the Scarp's tarn and stream) */
  CM.ducksOf = (fl) => { const R = CM.riverSquares(fl); if (R.length < 12) return []; const isRiver = ([x, y]) => Boolean(fl.features && fl.features[`${x},${y}`] && fl.features[`${x},${y}`].type === "river"), ford = R.find((sq) => !isRiver(sq)) || null;   // (the ford: the one water square that isn't the river's deep)
    const fy = ford ? ford[1] : -99, rows = R.filter(([, y]) => Math.abs(y - fy) > 4).sort((a, b) => a[1] - b[1]), out = [];
    for (const from of [0.18, 0.7]) { const i0 = Math.floor(rows.length * from), stretch = rows.slice(i0, i0 + 4); if (stretch.length === 4 && !out.some((g) => g.stretch[0][1] === stretch[0][1])) out.push({ stretch, n: 2 }); }
    return out; };
  CM.duckPose = (group, i, t) => { const S = group.stretch, L = S.length - 1, T = 26, u = ((t + i * 9) % T) / T;   // down the stretch slowly (the first two thirds), back up it a little quicker
    const s = u < 0.66 ? u / 0.66 : 1 - (u - 0.66) / 0.34, f = s * L, j = Math.min(L - 1, Math.floor(f)), r = f - j, a = S[j], b = S[j + 1];
    const side = i % 2 ? 0.22 : -0.18, dip = u > 0.66 && Math.sin(t * 1.7 + i) > 0.85;   // (paddling back it ducks its head now and then)
    return { x: a[0] + (b[0] - a[0]) * r + 0.5 + side, y: a[1] + (b[1] - a[1]) * r + 0.5 + (i % 2 ? -0.1 : 0.12), mirror: u >= 0.66, dip }; };
  CM.ducksOut = (game) => { if (!game || !game.floor || game.floor.number !== -1) return false; const w = CM.weather ? CM.weather(game) : "clear"; if (w === "snow") return false;
    const h = CM.hourOf(game), [dawn, dusk] = CM.daylightOf(game); return h >= dawn - 0.5 && h < dusk + 0.5; };
  CM.dragonfliesNow = (game) => { if (!game || !game.floor || game.floor.number !== -1) return 0; const s = CM.season ? CM.season(game) : "spring", w = CM.weather ? CM.weather(game) : "clear";
    if (w === "rain" || w === "snow" || w === "wind") return 0; const k = s === "summer" ? 1 : s === "spring" ? 0.5 : s === "autumn" ? 0.25 : 0; if (!k) return 0;
    const h = CM.hourOf(game), [dawn, dusk] = CM.daylightOf(game); return k * Math.max(0, Math.min(1, (h - dawn - 1) / 1.5, (dusk - 1 - h) / 1.5)); };
  CM.lilyNow = (game) => { if (!game || !game.floor || game.floor.number !== -1) return 0; const s = CM.season ? CM.season(game) : "spring"; return { summer: 1, spring: 0.55, autumn: 0.45, winter: 0 }[s] ?? 0.5; };
}
