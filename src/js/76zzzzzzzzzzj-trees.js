"use strict";
// Trees that fall, burn and grow again - the window's side (v74.0, UPGRADE_PLAN_61.md part 4): the rules
// (69zzm-trees.js) are stepped as the clock goes; the floor's mesh is told each tree's state (a lying log for a fallen
// one, a black log and ash for a charred one, a small tree for a sapling - 26-surface.js) and rebuilds when a state
// changes; a burning tree wears flames and smoke in the air and throws an orange, flickering light; a lamp blown out
// in a storm stays dark till the lamplighter's round. And the twister is fuller: more of its parts, with the air's
// budget raised while one crosses the land.
{ const P = 64, cv = () => { const c = document.createElement("canvas"); c.width = c.height = P; return c; };
  const PICS = { treefire: (p) => { const g = p.createRadialGradient(P / 2, P * 0.55, 2, P / 2, P * 0.55, P * 0.45); g.addColorStop(0, "rgba(255,245,200,1)"); g.addColorStop(0.35, "rgba(255,170,50,0.95)"); g.addColorStop(0.7, "rgba(230,80,20,0.6)"); g.addColorStop(1, "rgba(160,40,10,0)"); p.fillStyle = g; p.beginPath(); p.moveTo(P / 2, 2); p.quadraticCurveTo(P * 0.95, P * 0.6, P / 2, P - 2); p.quadraticCurveTo(P * 0.05, P * 0.6, P / 2, 2); p.fill(); } };
  { CM.art.AIR = CM.art.AIR || []; if (!CM.art.AIR.includes("treefire")) CM.art.AIR.push("treefire"); const ap0 = CM.art.airPicture; CM.art.airPicture = function (id) { if (!PICS[id]) return ap0.call(this, id); const c = cv(); PICS[id](c.getContext("2d")); return c; }; }
  // the flame's picture goes in with the surface's own pictures (a packed air picture doesn't draw large)
  { const b0 = CM.art.build; CM.art.build = function (theme, look) { const set = b0.call(this, theme, look); if (set.index["life:treefire"] === undefined) { const c = document.createElement("canvas"); c.width = c.height = 128; const p = c.getContext("2d"); p.scale(2, 2); PICS.treefire(p); set.index["life:treefire"] = set.layers.length; set.layers.push(c); } return set; }; }
  { const s0 = CM.art.isSurfaceLayer; CM.art.isSurfaceLayer = (name) => name === "life:treefire" || s0(name); }
  const burningNear = (game, fl, eye, reach = 14) => { const out = []; if (!game.ext) return out; const M = CM.treeStateMap(game, fl); for (const [k, s] of Object.entries(M)) { if (s !== "burning") continue; const [x, y] = k.split(",").map(Number); if (Math.abs(x + 0.5 - eye[0]) + Math.abs(y + 0.5 - eye[2]) <= reach) out.push([x + 0.5, y + 0.5]); } return out; };
  // the step, the mesh's states, and the fuller twister
  let lastClock = null, budget0 = null;
  const bf0 = CM.beforeFrame; CM.beforeFrame = (game, r, dt, now) => { if (bf0) bf0(game, r, dt, now); if (!game || !game.floor || !game.ext || game.mode === "title") { lastClock = null; return; } const fl = game.floor, t = CM.clockOf(game);
    if (lastClock !== null && t > lastClock && t - lastClock < 600) { CM.treesStep(game, t - lastClock); CM.lampOutStep(game, t - lastClock); } lastClock = t;
    if (fl.treesVersion !== (game.treesVersion || 0)) { fl.treeStates = CM.treeStateMap(game, fl); fl.treesVersion = game.treesVersion || 0; }   // (the mesh's key reads fl.treeStates)
    const tw = CM.twisterNow && CM.twisterNow(game); if (CM.AIR_BUDGET) { if (tw && tw.inside) { if (budget0 === null) budget0 = Object.assign({}, CM.AIR_BUDGET); CM.AIR_BUDGET.high = budget0.high * 2.4; CM.AIR_BUDGET.medium = budget0.medium * 2; } else if (budget0) { Object.assign(CM.AIR_BUDGET, budget0); budget0 = null; } } };
  // the fire in the air and its light
  { const k0 = CM.airKinds; CM.airKinds = function (env) { const out = k0.call(this, env); const g = CM.game, r = CM.renderer; if (!env.surface || !g || !g.floor || !r || !r.eye) return out; const n = burningNear(g, g.floor, r.eye).length; if (n) out.push({ id: "treefire", rate: 40 * n }, { id: "smoke", rate: 5 * n }); return out; }; }
  { const sp0 = CM.Air.prototype.spawn; CM.Air.prototype.spawn = function (k, eye, R, env) { const g = CM.game, r = Math.random;
      if (k.id === "treefire" || (k.id === "smoke" && g && g.floor && burningNear(g, g.floor, eye).length && r() < 0.7)) { const B = burningNear(g, g.floor, eye); if (!B.length) return k.id === "smoke" ? sp0.call(this, k, eye, R, env) : null; const [x, z] = B[Math.floor(r() * B.length)], a = r() * Math.PI * 2, d = k.id === "treefire" ? 0.42 + r() * 0.4 : r() * 0.45;   // (the flames at the crown's edge and over it, where the tree's own pictures don't hide them)
        if (k.id === "treefire") return { kind: "treefire", age: 0, seed: r() * 10, sway: 3 + r() * 3, swayAmp: 0.35, windy: 0.3, vx: 0, vy: 0.9 + r() * 0.7, vz: 0, life: 0.6 + r() * 0.6, size: 0.3 + r() * 0.3, h: 0.55 + r() * 0.4, glow: 2, alpha: 0.95, x: x + Math.cos(a) * d, z: z + Math.sin(a) * d, y: 0.5 + r() * 1.7, top: 3.8, layer: "life:treefire" };
        return { kind: "smoke", age: 0, seed: r() * 10, sway: 0.6 + r(), swayAmp: 0.15, windy: 0.5, vx: 0, vy: 0.45, vz: 0, life: 5 + r() * 3, size: 0.35, grow: 0.2, glow: 0, alpha: 0.7, x: x + Math.cos(a) * d * 0.5, z: z + Math.sin(a) * d * 0.5, y: 1.7, top: 6, layer: "air:smoke" }; }
      return sp0.call(this, k, eye, R, env); }; }
  { const xl0 = CM.extraLights; CM.extraLights = (game, fl, out, renderer) => { if (xl0) xl0(game, fl, out, renderer); if (!fl || !(fl.number === 0 || fl.number === -1) || !renderer || !renderer.eye) return; const [px, py] = fl.pos;
      for (const [x, z] of burningNear(game, fl, renderer.eye, 10)) out.push({ x, y: 1.2, z, reach: 3.4, colour: [1.0, 0.5, 0.15], flicker: true, d: Math.abs(x - 0.5 - px) + Math.abs(z - 0.5 - py) }); }; }
  // a blown-out lamp stays dark
  { const on0 = CM.lampOn; if (on0) CM.lampOn = (game, p) => (CM.lampBlownOut && CM.lampBlownOut(game, p) ? false : on0(game, p)); }
}
