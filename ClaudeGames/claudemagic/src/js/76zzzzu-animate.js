"use strict";
// Monsters that move (v29.0, UPGRADE_PLAN_24.md): a monster's picture is drawn in strips that bend (40-render.js), so it
// moves as a body, not a card: at rest it sways a little from the hips; on the move it bobs and its feet step; in a
// fight it draws itself down for the blow (the wind-up), stretches into it (the strike) and is crushed back by a hard
// one taken (the recoil), as 28-motion.js times them. Still, with Reduced motion.
{ CM.monsterBend = (state, now, phase, M) => {
    if (CM.reducedMotion) return null;
    if (state === "walk") { const t = now / 125 + phase; return { legs: 0.055 * Math.sin(t), lean: 0.035 * Math.sin(t / 2), squash: 1 - 0.045 * Math.abs(Math.sin(t)) }; }
    if (state === "fight" && M) {
      if (M.flash > 0.2 || (M.back > 0.05 && M.forward === 0 && M.flash > 0)) return { squash: 0.86, lean: 0.09 * Math.sin(phase * 3), legs: 0 };   // (struck: crushed back)
      if (M.forward > 0.02) return { squash: 1 + 0.25 * M.forward, lean: 0, legs: 0 };                      // (the strike: stretched into it)
      if (M.back > 0.02) return { squash: 1 - 0.8 * M.back, lean: -0.04, legs: 0 };                           // (the wind-up, or the flinch: drawn down)
    }
    return { lean: 0.028 * Math.sin(now / 900 + phase), squash: 1, legs: 0 };                                // (at rest: a sway from the hips)
  };
}
