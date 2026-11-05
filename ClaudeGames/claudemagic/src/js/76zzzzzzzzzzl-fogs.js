"use strict";
// The magical fogs - the window's side (v76.0, UPGRADE_PLAN_61.md part 6): a fog (69zzo-fogs.js) is a coloured
// layer of soft drifting billows about the party, above and below ground alike, the sky's and the stone's colours
// drawn toward its own, the mist's low veil under a sky and the dungeon's haze thickened below. The rules' statuses
// are told in the message log when it comes and goes, and the sky bar names it with what it does.
{ const P = 128, pic = (c0) => { const c = document.createElement("canvas"); c.width = c.height = P; const p = c.getContext("2d"), g = p.createRadialGradient(P / 2, P / 2, 2, P / 2, P / 2, P / 2); const [r, gg, b] = c0.map((v) => Math.round(v * 255)); g.addColorStop(0, `rgba(${r},${gg},${b},0.85)`); g.addColorStop(0.55, `rgba(${r},${gg},${b},0.4)`); g.addColorStop(1, `rgba(${r},${gg},${b},0)`); p.fillStyle = g; p.fillRect(0, 0, P, P); return c; };
  const KINDS = CM.FOGS.kinds, layerOf = (k) => `life:${k}`;
  { const b0 = CM.art.build; CM.art.build = function (theme, look) { const set = b0.call(this, theme, look); for (const k of Object.keys(KINDS)) { const L = layerOf(k); if (set.index[L] === undefined) { set.index[L] = set.layers.length; set.layers.push(pic(KINDS[k].colour)); } } return set; }; }
  { const s0 = CM.art.isSurfaceLayer; CM.art.isSurfaceLayer = (name) => (name.startsWith("life:fog") && KINDS[name.slice(5)] !== undefined) || s0(name); }
  // the billows: an air kind of their own, above and below
  { const k0 = CM.airKinds; CM.airKinds = function (env) { const out = k0.call(this, env); const g = CM.game, Fg = g && CM.fogNow ? CM.fogNow(g) : null; if (Fg && Fg.strength > 0) out.push({ id: "fogx", rate: 16 * Fg.strength }); return out; }; }
  { const sp0 = CM.Air.prototype.spawn; CM.Air.prototype.spawn = function (k, eye, R, env) { if (k.id !== "fogx") return sp0.call(this, k, eye, R, env); const g = CM.game, Fg = CM.fogNow(g); if (!Fg) return null; const r = Math.random, a = r() * Math.PI * 2, d = 0.8 + r() * (R - 0.5);
      return { kind: "fogx", age: 0, seed: r() * 10, sway: 0.4 + r() * 0.6, swayAmp: 0.12, windy: 0.25, vx: 0, vy: 0.015, vz: 0, life: 7 + r() * 5, size: 1.1 + r() * 1.1, grow: 0.06, glow: env.surface ? 1.3 : 2, alpha: (env.surface ? 0.22 : 0.3) + 0.2 * Fg.strength, x: eye[0] + Math.cos(a) * d, z: eye[2] + Math.sin(a) * d, y: 0.05 + r() * 0.9, top: 2.6, layer: layerOf(Fg.kind) }; }; }
  // the colours: the sky and the mist above, the stone's fog and the haze below
  const kept = new WeakMap(), mix = (c, t, k) => [c[0] + (t[0] - c[0]) * k, c[1] + (t[1] - c[1]) * k, c[2] + (t[2] - c[2]) * k];
  const bf0 = CM.beforeFrame; CM.beforeFrame = (game, r, dt, now) => { if (bf0) bf0(game, r, dt, now); if (!game || !game.floor || game.mode === "title" || !game.ext) return; const Fg = CM.fogNow(game), th = r.theme;
    if (th && kept.has(th) && (!Fg || r.sky)) { Object.assign(th, kept.get(th)); kept.delete(th); }   // (the stone's own colour back when the fog goes, or under a sky)
    if (!Fg || Fg.strength <= 0) return; const k = Fg.strength, C = Fg.colour;
    if (r.sky) { r.sky.horizon = mix(r.sky.horizon, C, 0.55 * k); r.sky.zenith = mix(r.sky.zenith, C, 0.3 * k); r.mist = Math.max(r.mist || 0, 0.2 + 0.5 * k); if (r.skyx) { r.skyx.cloudCol = mix(r.skyx.cloudCol || [1, 1, 1], C, 0.6 * k); } }
    else if (th) { if (!kept.has(th)) kept.set(th, { fog: th.fog, torch: th.torch }); const K = kept.get(th); th.fog = mix(K.fog, C.map((v) => v * 0.35), 0.7 * k); th.torch = mix(K.torch, C, 0.5 * k); if (r.air) r.air = Object.assign({}, r.air, { haze: Math.max(r.air.haze || 0, 0.45 + 0.4 * k) });
      if (r.lights) r.lights.forEach((l) => { l.colour = mix(l.colour, C, 0.45 * k); }); } };   // (below: the torches and the lamps burn in its colour, and the haze thickens)
}
