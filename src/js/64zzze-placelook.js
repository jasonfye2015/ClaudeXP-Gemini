"use strict";
// The real-time places' look (v64.0, UPGRADE_PLAN_59.md): the small, deterministic parts of it, by the rules so the
// tests can hold them - a torch's flicker, the hour's tint over Claudebros' sky, and where the dust motes drift in
// the Fortress. The window's side draws them (76zzzzzzzzzzc-places.js). Nothing here touches the rules of play.
//   CM.flickerAt(t, seed) -> 0.86..1.14      a flame's unsteadiness at t seconds, smooth, the same for the same t
//   CM.hourTint(h, dawn, dusk) -> [r, g, b, a]   what lies over the daylit sky at hour h: nothing by day, warm at dusk
//                                             and dawn, a deep blue at night (a 0..1, the colour 0..255)
//   CM.motesOf(seed, n) -> [{ x, y, vx, vy, phase }]   n motes in unit space, each with its own slow drift
{ CM.flickerAt = (t, seed = 0) => { const s = seed * 1.7; return 1 + 0.07 * Math.sin(t * 6.3 + s) + 0.04 * Math.sin(t * 17.1 + s * 2.3) + 0.03 * Math.sin(t * 2.2 + s * 0.7); };
  CM.hourTint = (h, dawn = 6, dusk = 20) => { const night = [16, 22, 60], warm = [255, 150, 70];
    if (h >= dawn + 1 && h <= dusk - 1) return [0, 0, 0, 0];
    if (h > dusk - 1 && h < dusk + 1) { const k = (h - (dusk - 1)) / 2; return k < 0.5 ? [...warm, k * 0.7] : [...night.map((c, i) => Math.round(warm[i] + (c - warm[i]) * ((k - 0.5) * 2))), 0.35 + (k - 0.5) * 0.7]; }
    if (h > dawn - 1 && h < dawn + 1) { const k = (h - (dawn - 1)) / 2; return k < 0.5 ? [...night.map((c, i) => Math.round(c + (warm[i] - c) * (k * 2))), 0.7 - k * 0.7] : [...warm, 0.35 * (1 - (k - 0.5) * 2)]; }
    return [...night, 0.7]; };
  CM.motesOf = (seed, n = 24) => { const r = new CM.Random(`motes:${seed}`), out = []; for (let i = 0; i < n; i++) out.push({ x: r.next(), y: r.next(), vx: (r.next() - 0.5) * 0.012, vy: (r.next() - 0.5) * 0.008 - 0.003, phase: r.next() * 6.28 }); return out; };
}
