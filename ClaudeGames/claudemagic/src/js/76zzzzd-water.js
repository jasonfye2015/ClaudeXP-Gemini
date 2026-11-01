"use strict";
// Living water (v24.1, UPGRADE_PLAN_19.md): rings spread where the party wades - in the river, a flooded vault, the
// Undercroft, a puddle on the road - and a few drops fly; the shader does the rest (40-render.js): the Wood's river
// runs, its ripples carried downstream; still water lies calm and mirrors the sky; rain rings every pool and puddle.
{ const wade = (K, x, y) => {
    if (CM.reducedMotion || !K || !K.renderer || !K.renderer.ok) return;
    const f = [Math.sin(K.renderer.yaw), -Math.cos(K.renderer.yaw)], at = [x + 0.5 + f[0] * 0.35, 0, y + 0.5 + f[1] * 0.35];
    K.fxs.ring({ at, to: 1.1, ms: 900, glow: 0.35 }); setTimeout(() => K.fxs.ring({ at, to: 0.7, ms: 800, glow: 0.3 }), 180);
    K.fxs.burst({ at: [at[0], 0.05, at[2]], layer: "fx:frost", n: 5, size: 0.04, speed: 0.6, up: 1.2, gravity: 4, ms: 420 });
  };
  const rf0 = CM.UI.prototype.refresh; CM.UI.prototype.refresh = function (...a) { if (!this.waterBound && this.game && this.game.on && CM.fxKit) { this.waterBound = true; this.game.on("moved", (x, y) => { if (CM.waterHere && CM.waterHere(x, y)) wade(CM.fxKit, x, y); }); } return rf0.apply(this, a); };
}
