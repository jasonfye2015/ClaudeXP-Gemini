"use strict";
// Shadows (v22.2, UPGRADE_PLAN_17.md): what stands on the floor - monsters, people, chests, props, trees - casts a
// shadow away from the light that rules where it stands: by day on the surface, the sun, long at dawn and dusk and
// short at noon; at night and below, the strongest lamp, torch or brazier near it, or else the party's own torch. A
// small soft shadow stays under each foot. The renderer lays the cast one turned and stretched (40-render.js).
{ const sunDir = (renderer) => { const sky = renderer.sky; if (!sky || sky.sun === null || !(sky.light > 0.15)) return null; const a = Math.PI * sky.sun, el = Math.max(0.035, Math.sin(a) * 0.5);   // (v77.0: the cap lowered - the sunset's shadows run longer)   // (as the renderer's sun: east over the south to the west)
    return { x: Math.cos(a), z: Math.sin(a), el, k: Math.min(1, (sky.light - 0.15) * 2) }; };
  CM.shadowCaster = (game, renderer, fl) => { const S = fl.number === 0 || fl.number === -1 ? sunDir(renderer) : null, lights = renderer.lights || [], eye = renderer.eye || [fl.pos[0] + 0.5, 0.5, fl.pos[1] + 0.5];
    return (x, y, w, dx = 0, dz = 0) => { const cx = x + 0.5 + dx, cz = y + 0.5 + dz, out = [{ x, y, dx, dz, layer: "shadow", flat: true, w: w * 0.8, alpha: 0.75 }];
      let lx, lz, len, alpha;
      if (S) { lx = -S.x; lz = -S.z; len = Math.min(3.2, 0.5 / Math.tan(S.el)); alpha = 0.55 * S.k; }
      else { let best = null, bestK = 0; for (const L of lights) { const d = Math.hypot(L.x - cx, L.z - cz); if (d >= L.reach) continue; const k = (1 - d / L.reach) * (L.colour[0] + L.colour[1] + L.colour[2]); if (k > bestK) { bestK = k; best = L; } }
        const src = best || { x: eye[0], z: eye[2], y: 0.62 }, d = Math.max(0.15, Math.hypot(cx - src.x, cz - src.z)); if (!best && d > 4) return out;
        lx = (cx - src.x) / d; lz = (cz - src.z) / d; len = Math.min(2.6, 0.8 + d * 0.45); alpha = best ? 0.5 * Math.min(1, bestK) : 0.38; }
      if (alpha > 0.04) out.push({ x, y, dx, dz, layer: "shadow", flat: true, w: w * 0.85, len, rot: Math.atan2(lz, lx), alpha });
      return out; }; };
}
