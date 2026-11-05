"use strict";
// Weather in the small things, the window's side (v60.0, UPGRADE_PLAN_55.md): a rainbow stands opposite the low sun
// in a rainy day's sun-shower hours, the cloud thinned and the rain eased for it (40-render.js: uRainbow); hoar frost
// whitens the ground on a clear cold morning and glints in the first sun (uGroundFrost); and in the rain drops run off
// the eaves of the town's houses (the "eavedrip" air kind). By 24d-weather.js.
{ const EAVE = { rate: 26, near: 7 };
  { const bf0 = CM.beforeFrame; CM.beforeFrame = (game, r, dt, now) => { if (bf0) bf0(game, r, dt, now); const fl = game && game.floor;
      if (!fl || !r.sky || game.mode === "title") { r.rainbow = 0; r.groundFrost = 0; return; }
      r.rainbow = CM.rainbowNow(game); r.groundFrost = CM.groundFrost(game);
      if (r.rainbow > 0 && r.skyx && r.skyx.cloud) { r.skyx.cloud = r.skyx.cloud.slice(); r.skyx.cloud[2] *= 1 - 0.45 * r.rainbow; }   // (the cloud thins for the sun to come through)
      r.eaves = fl.number === 0 && CM.eavesOf ? (r._eavesFor === fl ? r.eaves : CM.eavesOf(fl)) : null; r._eavesFor = fl; }; }
  // the rain eases in the sun-shower, and runs off the eaves
  { const k0 = CM.airKinds; CM.airKinds = function (env) { const out = k0.call(this, env); if (!env.surface) return out; const g = CM.game, rb = g && CM.rainbowNow ? CM.rainbowNow(g) : 0;
      if (env.weather === "rain") { for (const k of out) if (k.id === "rain") k.rate *= 1 - 0.55 * rb; if (env.town && CM.renderer && CM.renderer.eaves && CM.renderer.eaves.length) out.push({ id: "eavedrip", rate: EAVE.rate * (1 - 0.5 * rb) }); }
      return out; }; }
  { const sp0 = CM.Air.prototype.spawn; CM.Air.prototype.spawn = function (k, eye, R, env) { if (k.id !== "eavedrip") return sp0.call(this, k, eye, R, env);
      const E = CM.renderer && CM.renderer.eaves; if (!E || !E.length) return null; const r = Math.random;
      for (let tries = 0; tries < 6; tries++) { const e = E[Math.floor(r() * E.length)], t = r(), x = e.x0 + (e.x1 - e.x0) * t, z = e.z0 + (e.z1 - e.z0) * t;
        if (Math.abs(x - eye[0]) > EAVE.near || Math.abs(z - eye[2]) > EAVE.near) continue;
        return { kind: "eavedrip", age: 0, seed: r() * 10, sway: 0, swayAmp: 0, windy: 0.05, vx: 0, vy: -3.2 - r() * 0.8, vz: 0, life: 0.7, size: 0.035, h: 0.1, glow: 2, alpha: 0.85, x, z, y: e.y - 0.03, top: 4, layer: "air:eavedrip" }; }
      return null; }; }
  { CM.art.AIR = CM.art.AIR || []; if (!CM.art.AIR.includes("eavedrip")) CM.art.AIR.push("eavedrip");
    const ap0 = CM.art.airPicture; CM.art.airPicture = function (id) { return id === "eavedrip" ? ap0.call(this, "drip") : ap0.call(this, id); }; }
}
