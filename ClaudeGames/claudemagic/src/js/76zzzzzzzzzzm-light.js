"use strict";
// The light, the mud and the breath (v77.0, UPGRADE_PLAN_61.md part 7): god rays over the land in the hour after a
// rain when the sun is low; a lightning flash lights the land from the bolt's side for its frames, so the walls'
// facing and the cast shadows jump; the sunset's shadows run longer (76zzzv-shadows.js); the heat's shimmer is a
// band about the horizon (76zzzzzzzzzzi-wxair.js, uHeatFar); the earth darkens into mud after rain (uMud, by
// CM.mudNow); and in the cold the figures' breath shows, a puff from each head now and then.
{ let bolt = null, lastFlash = 0; const puffs = new Map(), r = Math.random;
  // the breath's picture: a pale soft puff, with the surface's own pictures (a packed air picture doesn't draw soft)
  { const b0 = CM.art.build; CM.art.build = function (theme, look) { const set = b0.call(this, theme, look); if (set.index["life:breath"] === undefined) { const c = document.createElement("canvas"); c.width = c.height = 64; const p = c.getContext("2d"), g = p.createRadialGradient(32, 32, 2, 32, 32, 32); g.addColorStop(0, "rgba(255,255,255,0.9)"); g.addColorStop(0.5, "rgba(240,244,250,0.45)"); g.addColorStop(1, "rgba(230,236,246,0)"); p.fillStyle = g; p.fillRect(0, 0, 64, 64); set.index["life:breath"] = set.layers.length; set.layers.push(c); } return set; }; }
  { const s0 = CM.art.isSurfaceLayer; CM.art.isSurfaceLayer = (name) => name === "life:breath" || s0(name); }
  const bf0 = CM.beforeFrame; CM.beforeFrame = (game, ren, dt, now) => { if (bf0) bf0(game, ren, dt, now); if (!game || !game.floor || game.mode === "title" || !game.ext) { ren.sunBoost = 1; return; }
    ren.mud = ren.sky ? CM.mudNow(game) : 0; if (ren.mud > 0 && ren.sky) ren.wet = Math.max(ren.wet || 0, 0.4 * ren.mud);   // (the gloss of wet earth)
    if (ren.sky && ren.air) { const ar = CM.afterRain(game), S = ren.sky; if (ar > 0 && S.sun !== null && S.light > 0.2 && (S.sun < 0.22 || S.sun > 0.78)) ren.air = Object.assign({}, ren.air, { shaft: Math.max(ren.air.shaft || 0, 0.9 * ar) }); }   // (god rays: the sun low through the cloud gaps after rain)
    ren.sunBoost = 1; if (ren.sky && ren.skyx && !CM.reducedMotion) { const f = ren.skyx.flash || 0; if (f > 0.3 && lastFlash <= 0.3) bolt = 0.15 + r() * 0.7; if (f > 0.3 && bolt !== null) { ren.sky = Object.assign({}, ren.sky, { sun: bolt, light: Math.max(ren.sky.light, 0.5) }); ren.sunBoost = 1 + 0.4 * Math.min(1, f); } lastFlash = f; }   // (the bolt is the light for its frames)
    const B = ren.screen && ren.screen.breath; if (B > 0 && ren.figList && ren.figList.length && CM.air && CM.air.parts) { const t = now / 1000;   // the figures' breath
      for (const e of ren.figList) { const id = e.s.m || e.s.id || e.key + "@" + Math.round(e.x) + "," + Math.round(e.z); let at = puffs.get(id); if (at === undefined) { at = t + r() * 3; puffs.set(id, at); } if (t < at) continue; puffs.set(id, t + 2.4 + r() * 1.6);
        const h = (e.s.h || 0.8) * 0.64, fx = Math.sin(e.yaw), fz = Math.cos(e.yaw);   /* (the mouth of a big-headed figure) */ for (let i = 0; i < 3; i++) CM.air.parts.push({ kind: "breath", age: 0.4, seed: r() * 10, sway: 0.5, swayAmp: 0.04, windy: 0.4, vx: fx * (0.12 + r() * 0.1), vy: 0.08 + r() * 0.06, vz: fz * (0.12 + r() * 0.1), life: 1.3 + r() * 0.5, size: 0.11 + r() * 0.05, grow: 0.12, glow: 1.3, alpha: 0.6, x: e.x + fx * 0.14, y: e.y + h, z: e.z + fz * 0.14, top: 4, layer: "life:breath" }); }
      if (puffs.size > 300) puffs.clear(); } };
}
