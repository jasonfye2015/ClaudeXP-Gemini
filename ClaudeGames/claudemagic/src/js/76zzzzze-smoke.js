"use strict";
// Smoke (v30.5, UPGRADE_PLAN_25.md): the wall torches' smoke rises and, under a ceiling, gathers and runs along it;
// braziers, the camp's fire and fire on the floor send up a thicker plume the wind takes; the town's chimneys smoke
// more at supper-time (they already smoked more by night and in the cold months: 27-props.js, 46-air.js). The air's
// own motes (CM.Air), its "air:smoke" picture.
{ const acc = new Map();
  const fires = (r) => (r.lights || []).filter((l) => l.flicker && l.colour && l.colour[0] >= l.colour[2] * 1.4 && Math.abs(l.x - r.eye[0]) + Math.abs(l.z - r.eye[2]) < 7.5);
  const st0 = CM.Air.prototype.step; CM.Air.prototype.step = function (dt, env) {
    const r = CM.renderer, sky = Boolean(r && r.sky);
    if (r && env && env.budget && !CM.reducedMotion) for (const l of fires(r)) {
      const k = `${l.x.toFixed(2)},${l.z.toFixed(2)}`, low = l.y < 0.6, rate = low ? 2.4 : 1.1; let a = (acc.get(k) || Math.random()) + dt * rate;
      while (a >= 1) { a -= 1; if (this.parts.length >= env.budget) continue; const rn = Math.random;
        this.parts.push({ kind: low ? "firesmoke" : "torchsmoke", layer: "air:smoke", age: 0, seed: rn() * 10, sway: 0.5 + rn(), swayAmp: 0.03, windy: sky ? 0.35 : 0, vx: 0, vz: 0,
          x: l.x + (rn() - 0.5) * 0.06, z: l.z + (rn() - 0.5) * 0.06, y: l.y + (low ? 0.25 : 0.1), vy: low ? 0.3 : 0.16, life: low ? 5 : 7, size: low ? 0.14 : 0.07, grow: low ? 0.2 : 0.05,
          glow: 0, alpha: low ? 0.42 : 0.3, top: sky ? 3.5 : 1.2 }); }
      acc.set(k, a); }
    if (!sky) for (const p of this.parts) if (p.kind === "torchsmoke" && p.y > 0.86) {   // (under the ceiling: it gathers, and runs along)
      p.y = 0.88; p.vy = 0; if (!p.spread) { p.spread = true; const an = p.seed * 2.1; p.vx = Math.cos(an) * 0.07; p.vz = Math.sin(an) * 0.07; p.grow = 0.09; p.alpha *= 0.85; } }
    if (acc.size > 200) acc.clear();
    return st0.call(this, dt, env);
  };
  const ak0 = CM.airKinds; CM.airKinds = function (env) { const out = ak0.call(this, env); if (env && env.town && env.hour >= 17 && env.hour < 22) for (const k of out) if (k.id === "smoke") k.rate *= 1.6; return out; };   // (supper on the fire)
}
