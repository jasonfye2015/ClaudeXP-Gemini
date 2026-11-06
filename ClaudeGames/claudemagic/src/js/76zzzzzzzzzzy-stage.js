"use strict";
// Stage pieces - the window's side (UPGRADE_PLAN_65.md, release 1): the meshes made in code ride with the plants (added
// to the model table at parse), drawn untinted in their own colours; the bridge sways under the party (the camera's
// roll); wyverns pass under the bridge now and then (air parts in the chasm); the mast's bell has a picture.
{ const r = Math.random;
  { const p0 = CM.Plants.parse; CM.Plants.parse = (bytes, manifest) => { const out = p0(bytes, manifest); if (CM.stageModels) Object.assign(out.models, CM.stageModels()); return out; }; }
  if (CM.plants && CM.plants.models && CM.stageModels) Object.assign(CM.plants.models, CM.stageModels());   // (if the plants were parsed before this file)
  CM.thingSprites = Object.assign(CM.thingSprites || {}, { mastbell: (t, x, y, now) => [{ x, y, layer: "sp:bell", w: 0.45, h: 0.7, lift: 0.08, dx: Math.sin(now / 800) * 0.01, shade: t.rung ? 0.7 : 1 }] });
  // the sway
  { const hook = () => { const g = CM.game; if (!g || !g.on || g._swayHooked) return; g._swayHooked = true; g.on("sway", () => { const ren = CM.renderer; if (!ren || !ren.rollTo) return; ren.rollTo((r() - 0.5) * 0.05, 300); setTimeout(() => ren.rollTo(0, 900), 420); }); };
    hook(); if (!CM.game) { const i0 = setInterval(() => { if (CM.game) { hook(); clearInterval(i0); } }, 500); } }
  // wyverns under the bridge
  const has = (L) => { const R0 = CM.renderer; return R0 && R0.index && R0.index[L] !== undefined; };
  { const k0 = CM.airKinds; CM.airKinds = function (env) { const out = k0.call(this, env); const g = CM.game, fl = g && g.floor; if (env.surface || !fl || !(fl.number >= 1) || g.mode === "title" || !fl.chasm) return out; const near = Object.keys(fl.chasm).some((k) => { const [x, y] = k.split(",").map(Number); return Math.abs(x - fl.pos[0]) + Math.abs(y - fl.pos[1]) <= 10; }); if (near && has("monster:Wyvern")) out.push({ id: "wyvern", rate: 0.12 }); return out; }; }
  { const sp0 = CM.Air.prototype.spawn; CM.Air.prototype.spawn = function (k, eye, R, env) { if (k.id !== "wyvern") return sp0.call(this, k, eye, R, env); const g = CM.game, fl = g.floor, cells = Object.keys(fl.chasm || {}).map((q) => q.split(",").map(Number)); if (!cells.length) return null; const xs = cells.map(([x]) => x), zs = cells.map(([, y]) => y), along = (Math.max(...zs) - Math.min(...zs)) >= (Math.max(...xs) - Math.min(...xs)); const dir = r() < 0.5 ? 1 : -1;
      const x = along ? Math.min(...xs) + r() * (Math.max(...xs) - Math.min(...xs) + 1) : (dir > 0 ? Math.min(...xs) : Math.max(...xs) + 1), z = along ? (dir > 0 ? Math.min(...zs) : Math.max(...zs) + 1) : Math.min(...zs) + r() * (Math.max(...zs) - Math.min(...zs) + 1);
      return { kind: "wyvern", age: 0.4, seed: r() * 10, sway: 1.2, swayAmp: 0.05, windy: 0, vx: along ? 0 : dir * 1.6, vy: 0, vz: along ? dir * 1.6 : 0, life: 6 + r() * 3, size: 0.6, h: 0.4, glow: 0, alpha: 0.85, x, z, y: -0.45 + r() * 0.2, top: 0.2, layer: "monster:Wyvern", flap: true, far: true, wyvern: true }; }; }
}
