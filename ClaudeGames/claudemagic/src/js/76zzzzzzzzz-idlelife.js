"use strict";
// Idle life (v50.4, UPGRADE_PLAN_45.md): a monster at rest is never quite still - it breathes (a slow rise and settle,
// slower for the big), shifts its weight from one foot to the other every few seconds, and now and then looks round:
// toward the party when a hero acts in a fight, or after the party's own noise when it is awake on the floor
// (Game.noiseLevel). Over the sway from the hips it had (76zzzzu-animate.js). Not with reduced motion asked for.
{ let noiseAt = -1e9, actAt = -1e9;
  const b0 = CM.monsterBend; CM.monsterBend = (state, now, phase, M) => { const out = b0 ? b0(state, now, phase, M) : null; if (!out || CM.reducedMotion || state === "walk" || (M && (M.flash > 0.05 || M.forward > 0.02 || M.back > 0.02))) return out;
    const t = now / 1000 + phase, breath = 0.018 * Math.sin(t * 1.6), shift = Math.sin(t * 0.55) > 0.6 ? 0.03 : Math.sin(t * 0.55) < -0.6 ? -0.03 : 0;
    const since = Math.min(now - noiseAt, now - actAt), look = since < 1500 ? Math.sin(Math.min(1, since / 400) * Math.PI / 2) * (1 - Math.max(0, since - 1000) / 500) * (Math.sin(phase * 7) > 0 ? 1 : -1) * 0.06 : 0;
    return Object.assign({}, out, { squash: (out.squash || 1) * (1 + breath), legs: (out.legs || 0) + shift, lean: (out.lean || 0) + look }); };
  const bind = () => { const g = CM.game; if (!g || !g.on) return false; let last = 0;
    g.on("fx", (fx) => { if (fx && (fx.kind === "attack" || fx.kind === "cast" || fx.kind === "potion")) actAt = performance.now(); });
    g.on("change", () => { const n = g.noiseLevel || 0; if (n > last + 0.5) noiseAt = performance.now(); last = n; }); return true; };
  const t = typeof self !== "undefined" && self.CM_WORKER ? null : setInterval(() => { if (bind()) clearInterval(t); }, 300);
}
