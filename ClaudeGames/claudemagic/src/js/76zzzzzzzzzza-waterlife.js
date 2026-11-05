"use strict";
// The river's life, the window's side (v62.0, UPGRADE_PLAN_57.md): the trees and the banks darken the water that
// mirrors them (40-render.js: uBankTint), lily pads and duckweed lie in the slack water by the banks in the warm months
// (uLily), dragonflies dart over the river on a summer's day (the "dragonfly" air kind, spawned over the water), and a
// pair of ducks drifts each slow stretch and paddles back. Where and when is 69zzl-waterlife.js's.
{ const P = 64, cv = () => { const c = document.createElement("canvas"); c.width = c.height = P; return c; };
  const E = (p, x, y, rx, ry, col, rot = 0) => { p.fillStyle = col; p.beginPath(); p.ellipse(x, y, rx, ry, rot, 0, Math.PI * 2); p.fill(); };
  const duck = (p, drake, dip) => { const body = drake ? "#8A8A80" : "#8A6A48", hy = dip ? 40 : 24;
    E(p, 30, 42, 20, 10, body); E(p, 24, 40, 12, 6, drake ? "#6A6A62" : "#6A5038", -0.2); p.fillStyle = drake ? "#2A2A2A" : "#5A4430"; p.beginPath(); p.moveTo(12, 42); p.lineTo(2, 34); p.lineTo(8, 44); p.fill();   // body, wing, tail
    if (!dip) { p.strokeStyle = drake ? "#1E6A3A" : "#7A5A3A"; p.lineWidth = 7; p.beginPath(); p.moveTo(42, 38); p.lineTo(47, hy + 4); p.stroke(); if (drake) { p.strokeStyle = "#F0F0F0"; p.lineWidth = 2; p.beginPath(); p.moveTo(40, 34); p.lineTo(50, 32); p.stroke(); } }   // neck (and the drake's white ring)
    E(p, 48, hy, 7, 6, drake ? "#1E6A3A" : "#7A5A3A"); p.fillStyle = "#E8A020"; p.beginPath(); p.moveTo(54, hy - 1); p.lineTo(63, hy + 1); p.lineTo(54, hy + 3); p.fill(); p.fillStyle = "#141008"; p.fillRect(49, hy - 2, 2, 2); };   // head, bill, eye
  const dragonfly = (p) => { p.strokeStyle = "rgba(220,235,255,0.75)"; p.lineWidth = 3; for (const [a, b] of [[-1, -1], [1, -1], [-1, 1], [1, 1]]) { p.beginPath(); p.ellipse(32 + a * 14, 30 + b * 4, 14, 4, a * b * 0.25, 0, Math.PI * 2); p.stroke(); }   // four wings
    p.strokeStyle = "#2A7AA0"; p.lineWidth = 3; p.beginPath(); p.moveTo(32, 26); p.lineTo(32, 56); p.stroke(); E(p, 32, 26, 4, 4, "#2A5A80"); };   // body, head
  const PAINT = { "life:duck": (p) => duck(p, false, false), "life:duck:dip": (p) => duck(p, false, true), "life:drake": (p) => duck(p, true, false), "life:drake:dip": (p) => duck(p, true, true) };
  { const b0 = CM.art.build; CM.art.build = function (theme, look) { const set = b0.call(this, theme, look); for (const [k, f] of Object.entries(PAINT)) { if (set.index[k] !== undefined) continue; const c = cv(); f(c.getContext("2d")); set.index[k] = set.layers.length; set.layers.push(c); } return set; }; }
  { const s0 = CM.art.isSurfaceLayer; CM.art.isSurfaceLayer = (name) => name in PAINT || s0(name); }
  { CM.art.AIR = CM.art.AIR || []; if (!CM.art.AIR.includes("dragonfly")) CM.art.AIR.push("dragonfly");
    const ap0 = CM.art.airPicture; CM.art.airPicture = function (id) { if (id !== "dragonfly") return ap0.call(this, id); const c = cv(); dragonfly(c.getContext("2d")); return c; }; }
  // the shader's share: the banks' tint on the water, the lilies by season; and the river's squares for the dragonflies
  { const bf0 = CM.beforeFrame; CM.beforeFrame = (game, r, dt, now) => { if (bf0) bf0(game, r, dt, now); const fl = game && game.floor;
      if (!fl || !r.sky || game.mode === "title") { r.bankTint = null; r.lily = 0; r.waters = null; return; }
      r.bankTint = fl.number === -1 ? [0.12, 0.2, 0.1, 0.8] : [0.3, 0.28, 0.25, 0.55]; r.lily = CM.lilyNow(game) * (game.settings && game.settings.detail === "low" ? 0 : 1);
      if (r._watersFor !== fl) { r.waters = CM.riverSquares(fl); r._watersFor = fl; } }; }
  { const k0 = CM.airKinds; CM.airKinds = function (env) { const out = k0.call(this, env); const g = CM.game; if (!env.surface || !g || !g.floor || g.floor.number !== -1) return out;
      const k = CM.dragonfliesNow(g); if (k > 0 && CM.renderer && CM.renderer.waters && CM.renderer.waters.length) out.push({ id: "dragonfly", rate: 2.2 * k }); return out; }; }
  { const sp0 = CM.Air.prototype.spawn; CM.Air.prototype.spawn = function (k, eye, R, env) { if (k.id !== "dragonfly") return sp0.call(this, k, eye, R, env);
      const Wt = CM.renderer && CM.renderer.waters; if (!Wt || !Wt.length) return null; const r = Math.random;
      for (let tries = 0; tries < 8; tries++) { const [wx, wy] = Wt[Math.floor(r() * Wt.length)]; if (Math.abs(wx + 0.5 - eye[0]) > 7 || Math.abs(wy + 0.5 - eye[2]) > 7) continue; const a = r() * Math.PI * 2;
        return { kind: "dragonfly", age: 0, seed: r() * 10, sway: 3 + r() * 3, swayAmp: 1.6, windy: 0.1, vx: Math.cos(a) * 0.5, vy: 0, vz: Math.sin(a) * 0.5, life: 5 + r() * 4, size: 0.1, h: 0.08, glow: 1.3, alpha: 0.9, x: wx + r(), z: wy + r(), y: 0.25 + r() * 0.5, top: 2, layer: "air:dragonfly" }; }
      return null; }; }
  // the ducks
  { const groups = new WeakMap(), of = (fl) => { let g = groups.get(fl); if (!g) { g = CM.ducksOf(fl); groups.set(fl, g); } return g; };
    const ls0 = CM.lifeSprites; CM.lifeSprites = (game, fl, now) => { const out = ls0 ? ls0(game, fl, now) : []; const r = CM.renderer;
      if (!fl || fl.number !== -1 || game.mode === "title" || !r || !r.index || r.index["life:duck"] === undefined || !CM.ducksOut(game)) return out;
      const t = now / 1000, [px, py] = fl.pos;
      for (const g of of(fl)) { if (Math.abs(g.stretch[0][0] - px) + Math.abs(g.stretch[0][1] - py) > 16) continue;
        for (let i = 0; i < g.n; i++) { const q = CM.duckPose(g, i, t), x = Math.floor(q.x), y = Math.floor(q.y), drake = i % 2 === 0;
          out.push({ x, y, dx: q.x - x - 0.5, dz: q.y - y - 0.5, layer: `life:${drake ? "drake" : "duck"}${q.dip ? ":dip" : ""}`, w: 0.3, h: 0.22, mirror: q.mirror, lift: 0.01 + (CM.reducedMotion ? 0 : Math.sin(t * 1.3 + i * 2) * 0.012) }); } }
      return out; }; }
}
