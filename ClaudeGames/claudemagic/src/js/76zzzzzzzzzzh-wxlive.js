"use strict";
// The weather, live - the window's side (v72.0, UPGRADE_PLAN_61.md part 2): what the sky shows follows the event in
// force and its strength, not the day's word - the rain's fall and the ground's wet by how hard it rains, the cloud's
// cover by the kind, the mist's depth, the wind's push on everything that sways, the storm's lightning at any hour,
// the aurora when one is rolled, the heat's shimmer on a summer afternoon. The dial's predictor (73c-wxhud.js) says
// what's coming. Below ground the surface's event still runs (the grates' light, the drips to come).
{ const COVER = { clear: 0.12, cloud: 0.75, rain: 0.86, storm: 0.96, mist: 0.6, wind: 0.45, snow: 0.82, heat: 0.05, aurora: 0.08 };
  const bf0 = CM.beforeFrame; CM.beforeFrame = (game, r, dt, now) => { if (bf0) bf0(game, r, dt, now); if (!game || !game.floor || game.mode === "title" || !game.ext) { r.wxNow = null; return; }
    const W = CM.weatherNow(game), k = W.strength; r.wxNow = W;
    if (r.sky) { const rain = W.kind === "rain" || W.kind === "storm"; r.wet = rain ? Math.max(0.25, k) * (W.kind === "storm" ? 1 : 0.9) : Math.max(0, (r.wet || 0) - dt * 0.02);   // (the wet lingers a little, then the puddles' own file keeps what lingers)
      r.mist = W.kind === "mist" ? 0.35 + 0.65 * k : 0; r.heat = W.kind === "heat" ? k : 0;
      if (r.skyx && r.skyx.cloud) { const c = r.skyx.cloud.slice(); const want = COVER[W.kind] === undefined ? 0.3 : COVER[W.kind]; c[2] = W.kind === "clear" ? Math.min(c[2], 0.2) : want * (0.4 + 0.6 * k) + (COVER.clear) * (1 - (0.4 + 0.6 * k)); r.skyx.cloud = c;
        if (W.kind === "aurora") r.skyx.aurora = Math.max(r.skyx.aurora || 0, k * (r.sky.night ? 1 : 0)); }
      if (r.wind) r.wind.k = W.wind.speed; } };
  // the storm's lightning at any hour of a storm; the rain's and the snow's fall by strength
  { const s0 = CM.stormNow; CM.stormNow = (game) => { const W = game && game.ext && game.tally && game.tally.ext && game.tally.ext.wx && game.tally.ext.wx.cur; if (W && W.kind === "storm") return true; if (W) return false; return s0 ? s0(game) : false; }; }
  { const k0 = CM.airKinds; CM.airKinds = function (env) { const out = k0.call(this, env); const g = CM.game; if (!env.surface || !g || !g.ext) return out; const W = CM.weatherNow(g), k = Math.max(0.15, W.strength);
      for (const o of out) { if (o.id === "rain") o.rate *= (W.kind === "storm" ? 1.4 : 1) * k; else if (o.id === "snow" && W.kind === "snow") o.rate *= k; else if (o.id === "fog") o.rate *= W.kind === "mist" ? 0.5 + k : 1; }
      return out; }; }
}
