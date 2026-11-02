"use strict";
// Spell colours in the room (v31.4, UPGRADE_PLAN_26.md): a bolt in flight carries its own light along the walls - a
// fireball orange, frost blue, force violet, holy gold, poison and acid green, shadow purple - (where it lands it
// already flared: 76zzzu-light.js); lightning flashes the whole room white, below ground as under the sky.
// CM.extraLights and renderer.roomFlash (40-render.js's uFlash).
{ const COLOUR = { "fx:fire": [1.0, 0.55, 0.18], "fx:frost": [0.45, 0.75, 1.0], "fx:force": [0.7, 0.45, 1.0], "fx:holy": [1.0, 0.88, 0.45], "fx:poison": [0.45, 1.0, 0.35],
    "fx:acid": [0.6, 1.0, 0.3], "fx:dark": [0.6, 0.25, 0.9], "fx:shadow": [0.6, 0.25, 0.9], "fx:bolt": [0.75, 0.85, 1.0], "fx:spark": [1.0, 0.8, 0.45] };
  { const xl0 = CM.extraLights; CM.extraLights = (game, fl, out, renderer) => { if (xl0) xl0(game, fl, out, renderer); const K = CM.fxKit; if (!K || !K.fxs || !K.fxs.list) return;
      const now = performance.now(); let n = 0;
      for (const e of K.fxs.list) { if (e.type !== "projectile" || !e.from || !e.to || n >= 3) continue; const c = COLOUR[e.layer]; if (!c) continue; const k = (now - e.t0) / e.ms; if (k < 0 || k >= 1) continue;
        const kk = CM.ease(k), x = CM.lerp(e.from[0], e.to[0], kk), z = CM.lerp(e.from[2], e.to[2], kk), y = CM.lerp(e.from[1], e.to[1], kk) + Math.sin(Math.PI * kk) * e.arc;
        out.unshift({ x, y, z, reach: 2.2 + e.size * 4, colour: c.map((v) => v * 1.5), flicker: false, d: 0 }); n++; } }; }   // (first in the list: never the one left out)
  let flash = 0;
  { const em0 = CM.Game.prototype.emit; CM.Game.prototype.emit = function (ev, ...a) { if (ev === "fx" && a[0] && /lightning|thunder|storm/.test(`${a[0].kind || ""} ${a[0].id || ""}`)) flash = 1; return em0.call(this, ev, ...a); }; }
  const bf0 = CM.beforeFrame; CM.beforeFrame = (game, r, dt, now) => { if (bf0) bf0(game, r, dt, now); r.roomFlash = CM.reducedMotion ? 0 : flash * flash * 0.8; flash = Math.max(0, flash - dt * 3.5); };
}
