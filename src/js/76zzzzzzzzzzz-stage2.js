"use strict";
// Stage pieces, the second six - the window's side (UPGRADE_PLAN_65.md, release 2): the meshes ride with release 1's
// (CM.stageModels is extended, the parse hook adds them); pictures for the rope ladder, the sunk bell, the stone deer
// and the stone traveller, the Hollow One on its throne, the star's glow; spray and drips at the fall; the grate's
// daylight is the daylight's own (76zzzzzzzzu-daylight.js reads grate features).
{ const r = Math.random;
  if (CM.plants && CM.plants.models && CM.stageModels) Object.assign(CM.plants.models, CM.stageModels());
  const has = (L) => { const R0 = CM.renderer; return R0 && R0.index && R0.index[L] !== undefined; };
  const mon = (name, fallback) => (has(`monster:${name}`) ? `monster:${name}` : fallback);
  CM.thingSprites = Object.assign(CM.thingSprites || {}, {
    ropeladder: (t, x, y) => [{ x, y, layer: "rope", w: 0.4, h: 1.0, lift: 0.0 }, { x, y, layer: "rope", w: 0.4, h: 1.0, dx: 0.2, lift: 0.0, shade: 0.8 }],
    sunkbell: (t, x, y) => [{ x, y, layer: "sp:bell", w: 0.5, h: 0.6, flat: false, lift: -0.08, alpha: 0.55, shade: 0.5 }],
    stonefigure: (t, x, y) => [{ x, y, layer: t.of === "Deer" ? mon("Deer", "bones") : "npc:adventurer", w: t.of === "Deer" ? 0.8 : 0.75, h: t.of === "Deer" ? 0.7 : 0.8, shade: 0.45 }],
    throne: (t, x, y, now) => (t.taken ? [] : [{ x, y, layer: mon("Hollow One", "npc:ghost"), w: 0.8, h: 0.85, shade: 0.8, lift: 0.3 + Math.sin(now / 1800) * 0.004 }]),
    vein: (t, x, y, now) => (t.star ? [{ x, y, layer: "fx:spark", w: 0.9, h: 0.5, flat: true, alpha: 0.35 + 0.15 * Math.sin(now / 500), glow: 0.5 }] : []),
  });
  // spray and drips at the fall
  { const k0 = CM.airKinds; CM.airKinds = function (env) { const out = k0.call(this, env); const g = CM.game, fl = g && g.floor; if (env.surface || !fl || !(fl.number >= 1) || g.mode === "title" || !fl.features) return out; const n = Object.entries(fl.features).filter(([k, f]) => { if (f.type !== "curtain") return false; const [x, y] = k.split(",").map(Number); return Math.abs(x - fl.pos[0]) + Math.abs(y - fl.pos[1]) <= 10; }).length; if (n) out.push({ id: "fallspray", rate: Math.min(12, 2 * n) }); return out; }; }
  { const sp0 = CM.Air.prototype.spawn; CM.Air.prototype.spawn = function (k, eye, R, env) { if (k.id !== "fallspray") return sp0.call(this, k, eye, R, env); const g = CM.game, fl = g.floor, F = Object.keys(fl.features).filter((q) => fl.features[q].type === "curtain").map((q) => q.split(",").map(Number)); if (!F.length) return null; const [x, y] = F[Math.floor(r() * F.length)];
      return { kind: "drip", age: 0.4, seed: r() * 10, sway: 0.5, swayAmp: 0.02, windy: 0.2, vx: (r() - 0.5) * 0.3, vy: -1.4 - r() * 0.8, vz: 0.1 + r() * 0.3, life: 1.2 + r() * 0.5, size: 0.05 + r() * 0.04, h: 0.08, glow: 0.1, alpha: 0.8, x: x + r(), z: y + 0.1 + r() * 0.3, y: 0.9 + r() * 0.08, top: 1.0, layer: has("air:drip") ? "air:drip" : "fx:frost" }; }; }
}
