"use strict";
// Blows that land (v23.1, UPGRADE_PLAN_18.md): a blow has weight. A critical hit - a weak spot found, a knife from
// behind - flashes white, holds everything still for a moment (a hit-stop), nudges the view toward it and throws a big
// gold number with a "!"; any heavy blow knocks its foe further back and rocks it (28-motion.js takes the weight); a
// blow taken by the party pushes the view back a little. The rules mark the crit (62-combat.js strike).
{ CM.blowFx = (K, fx) => {
    if (!K || !K.renderer || !K.renderer.ok) return;
    const now = performance.now(), cine = CM.cinematic ? 1.6 : 1, quick = CM.fxSpeed || 1;
    if (fx.kind === "hit" && fx.foe) {
      const k = Math.min(1, (fx.frac || 0) * 2.2 + (fx.crit ? 0.45 : 0));
      K.weight.set(fx.foe, k);
      if (fx.spell || CM.reducedMotion || quick >= 6) return;
      if (fx.crit || k > 0.6) {
        const stop = (fx.crit ? 95 : 55) * cine / quick, p = K.foePlace(fx.foe), side = p ? Math.sign(p.dx * Math.cos(K.renderer.yaw) + p.dz * Math.sin(K.renderer.yaw)) : 0;
        K.fxs.hitStop(stop); K.hits.set(fx.foe, now + stop); K.flashes.set(fx.foe, 1);
        K.renderer.nudge(side * 0.6, (fx.crit ? 1 : 0.6) * cine);
        if (fx.crit) { const at = K.atFoe(fx.foe, 0.55); if (at) K.fxs.burst({ at, layer: "fx:spark", n: 18, size: 0.07, speed: 2.0, up: 1.8, ms: 600 }); K.ui.tint("rgba(255,255,255,0.35)", 120); K.renderer.shake(0.25 * cine); }
      }
    } else if (fx.kind === "hurt" && fx.hero && fx.hero.max && !CM.reducedMotion) {
      const frac = fx.amount / fx.hero.max; if (frac > 0.08) K.later(() => K.renderer.nudge(0, -Math.min(1, frac * 3) * 0.8));
    }
  };
  const rf0 = CM.UI.prototype.refresh; CM.UI.prototype.refresh = function (...a) { if (!this.blowBound && this.game && this.game.on && CM.fxKit) { this.blowBound = true; this.game.on("fx", (e) => CM.blowFx(CM.fxKit, e)); } return rf0.apply(this, a); };
}
