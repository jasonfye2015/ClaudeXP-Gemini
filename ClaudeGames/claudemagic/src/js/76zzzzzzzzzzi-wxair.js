"use strict";
// The stronger sky and air (v73.0, UPGRADE_PLAN_61.md part 3): in a gale the air fills with flying leaves, twigs and
// dust streaking downwind, and the lamps and torches gutter in the gusts; a tornado is a funnel of dark whirling air
// that crosses the land along its way (CM.twisterNow), dust and debris flung up round it; a heat event shimmers
// the air over the ground on a summer afternoon; after rain, with the sun low, the dawn or the dusk is dramatic -
// the sun's glow doubled and the clouds lit in its colour; a dense mist closes the sight to a square (the rules'),
// and the air thick with it. All of it air kinds and the renderer's fields; nothing here touches the rules.
{ const P = 64, cv = () => { const c = document.createElement("canvas"); c.width = c.height = P; return c; };
  const PICS = { debris: (p) => { p.strokeStyle = "#8A7048"; p.lineWidth = 5; p.lineCap = "round"; p.beginPath(); p.moveTo(10, 40); p.lineTo(54, 24); p.stroke(); p.fillStyle = "#A08048"; p.beginPath(); p.ellipse(40, 26, 10, 6, 0.6, 0, Math.PI * 2); p.fill(); },
    twister: (p) => { const g = p.createRadialGradient(P / 2, P / 2, 4, P / 2, P / 2, P / 2); g.addColorStop(0, "rgba(128,112,96,0.98)"); g.addColorStop(0.7, "rgba(104,92,80,0.72)"); g.addColorStop(1, "rgba(90,80,70,0)"); p.fillStyle = g; p.fillRect(0, 0, P, P); } };   // (dust-brown, so it reads against a black sky)
  { CM.art.AIR = CM.art.AIR || []; for (const id of Object.keys(PICS)) if (!CM.art.AIR.includes(id)) CM.art.AIR.push(id);
    const ap0 = CM.art.airPicture; CM.art.airPicture = function (id) { if (!PICS[id]) return ap0.call(this, id); const c = cv(); PICS[id](c.getContext("2d")); return c; }; }
  // the funnel's picture goes in with the surface's own pictures (a packed air picture doesn't draw large; the hens' kind does)
  { const b0 = CM.art.build; CM.art.build = function (theme, look) { const set = b0.call(this, theme, look); if (set.index["life:twister"] === undefined) { const c = document.createElement("canvas"); c.width = c.height = 128; const p = c.getContext("2d"); p.scale(2, 2); PICS.twister(p); set.index["life:twister"] = set.layers.length; set.layers.push(c); } return set; }; }
  { const s0 = CM.art.isSurfaceLayer; CM.art.isSurfaceLayer = (name) => name === "life:twister" || s0(name); }
  // the air's kinds by the event: debris in a gale, the twister's whirl, the mist thicker
  { const k0 = CM.airKinds; CM.airKinds = function (env) { const out = k0.call(this, env); const g = CM.game; if (!env.surface || !g || !g.ext) return out; const W = CM.weatherNow(g);
      if (W.wind.speed > 0.55) out.push({ id: "debris", rate: 14 * (W.wind.speed - 0.4) });
      const T = CM.twisterNow(g); if (T && T.inside) out.push({ id: "twister", rate: 340 }, { id: "debris", rate: 30 });   // (v74.0: fuller - the air's budget is raised while it crosses)
      return out; }; }
  { const sp0 = CM.Air.prototype.spawn; CM.Air.prototype.spawn = function (k, eye, R, env) { const g = CM.game, r = Math.random;
      if (k.id === "debris") { const W = CM.weatherNow(g), w = W.wind, T = CM.twisterNow(g); let x, z, y;
        if (T && T.inside && r() < 0.5) { const a = r() * Math.PI * 2, d = 0.3 + r() * 1.6; x = T.x + Math.cos(a) * d; z = T.y + Math.sin(a) * d; y = r() * 2.5; }
        else { x = eye[0] + (r() * 2 - 1) * 6 - w.dir[0] * 4; z = eye[2] + (r() * 2 - 1) * 6 - w.dir[1] * 4; y = 0.2 + r() * 1.6; }
        return { kind: "debris", age: 0, seed: r() * 10, sway: 2 + r() * 4, swayAmp: 0.5, windy: 1.6 + r() * 0.8, vx: 0, vy: (r() - 0.3) * 0.4, vz: 0, life: 2 + r() * 2, size: 0.06 + r() * 0.05, glow: 0, alpha: 0.9, x, z, y, top: 4, layer: "air:debris" }; }
      if (k.id === "twister") { const T = CM.twisterNow(g); if (!T) return null; const a = r() * Math.PI * 2, y = r() * 3.4, d = 0.1 + y * 0.34 + r() * 0.12;   // (the funnel: narrow at the ground, wide at the top)
        return { kind: "twister", age: 0, seed: a, sway: 0, swayAmp: 0, windy: 0, vx: 0, vy: 0.9 + r() * 0.6, vz: 0, life: 1.4 + r() * 0.8, size: 0.26 + y * 0.1, glow: 0.6, alpha: 0.9, x: T.x + Math.cos(a) * d, z: T.y + Math.sin(a) * d, y, top: 5, spin: { cx: T.x, cz: T.y, a, d, w: 3.5 }, layer: "life:twister" }; }
      return sp0.call(this, k, eye, R, env); }; }
  // the funnel's parts whirl about its centre instead of drifting (a step after the air's own)
  { const st0 = CM.Air.prototype.step; CM.Air.prototype.step = function (dt, env) { const out = st0.call(this, dt, env); const g = CM.game, T = g && CM.twisterNow ? CM.twisterNow(g) : null;
      for (const p of this.parts) if (p.spin) { if (!T) { p.life = 0; continue; } p.spin.a += p.spin.w * dt; p.spin.d += dt * 0.25; p.x = T.x + Math.cos(p.spin.a) * p.spin.d; p.z = T.y + Math.sin(p.spin.a) * p.spin.d; }
      return out; }; }
  // the renderer's fields: the lamps guttering, the heat's shimmer, the dramatic dawn and dusk
  const bf0 = CM.beforeFrame; CM.beforeFrame = (game, r, dt, now) => { if (bf0) bf0(game, r, dt, now); if (!game || !game.floor || !r.sky || game.mode === "title" || !game.ext) return; const W = CM.weatherNow(game), t = now / 1000;
    if (W.wind.speed > 0.55 && r.lights) { const gust = W.wind.speed - 0.4; r.lights.forEach((l, i) => { if (!l.flicker) return; const k = 1 - gust * (0.35 + 0.35 * Math.abs(Math.sin(t * (7 + i * 0.9) + i * 2.1)) * Math.abs(Math.sin(t * 1.7 + i))); l.colour = l.colour.map((c) => c * k); }); }   // (guttering in the gusts)
    if (r.screen) r.screen.heatAll = Math.max(r.screen.heatAll || 0, W.kind === "heat" ? W.strength * 0.7 : 0);
    const ar = CM.afterRain(game); if (ar > 0 && r.sunCol && r.sunCol[3] > 0) { r.sunCol = r.sunCol.slice(); r.sunCol[3] = Math.min(2, r.sunCol[3] * (1 + 1.5 * ar)); if (r.skyx && r.skyx.cloudCol) { const c = r.skyx.cloudCol, w = ar * r.sunCol[3] * 0.4; r.skyx.cloudCol = [c[0] + (1.0 - c[0]) * w, c[1] + (0.7 - c[1]) * w, c[2] + (0.45 - c[2]) * w]; } }   // (the sky after rain, the sun low: the glow doubled, the clouds lit)
    const T = CM.twisterNow(game); if (T && T.inside && r.skyx && r.skyx.cloud) { const c = r.skyx.cloud.slice(); c[2] = Math.max(c[2], 0.9); r.skyx.cloud = c; r.skyx.cloudCol = [0.35, 0.33, 0.32]; } };
}
