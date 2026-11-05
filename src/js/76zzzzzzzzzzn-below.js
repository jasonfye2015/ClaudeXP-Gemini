"use strict";
// The dungeon coupling - the window's side (v78.0, UPGRADE_PLAN_61.md part 8): rain above drips from the ceilings
// of the first floors and the damp rises; a storm pours a waterfall through each grate, with its splash; a heavy
// storm's floodwater stands in the sunken rooms (69zzq-below.js), drawn as the flooded mood's water; a gale above
// makes a draft below - the torches gutter and lean, the smoke and the haze drift; lightning comes down through
// the grates as well as the shaft; and in the fire bands the floodwater and the drips steam, thickening the haze.
{ const DEPTH = { 1: 1, 2: 0.6, 3: 0.3 }, HOT = new Set(["The Foundry", "The Root of the World"]), r = Math.random;
  const below = (game) => game && game.floor && game.floor.number >= 1 && game.mode !== "title" && game.ext;
  const near = (fl, x, y, R) => Math.abs(x - fl.pos[0]) + Math.abs(y - fl.pos[1]) <= R;
  const hot = (fl) => HOT.has((CM.themeFor(fl.number) || {}).name);
  // the air: drips, the grates' waterfalls, the steam (lives past the air's fade-out: a part's last 0.6 s is faint, and the floor takes these first)
  { const k0 = CM.airKinds; CM.airKinds = function (env) { const out = k0.call(this, env); const g = CM.game; if (env.surface || !below(g)) return out; const fl = g.floor, d = DEPTH[fl.number] || 0, W = CM.aboveNow(g), rain = W.kind === "rain" || W.kind === "storm" ? W.strength : 0;
      if (d && rain > 0) out.push({ id: "drip", rate: 14 * rain * d });
      if (d && W.kind === "storm" && CM.gratesOf) { const n = CM.gratesOf(fl).filter(([x, y]) => near(fl, x, y, 9)).length; if (n) out.push({ id: "gratefall", rate: 90 * W.strength * n }, { id: "gratesplash", rate: 24 * W.strength * n }); }
      if (hot(fl) && (CM.floodedHere(g) || (d && rain > 0.3))) out.push({ id: "steam", rate: 9 });
      return out; }; }
  { const sp0 = CM.Air.prototype.spawn; CM.Air.prototype.spawn = function (k, eye, R, env) { const g = CM.game;
      if (k.id === "gratefall" || k.id === "gratesplash") { const fl = g.floor, G = CM.gratesOf(fl).filter(([x, y]) => near(fl, x, y, 9)); if (!G.length) return null; const [gx, gy] = G[Math.floor(r() * G.length)], x = gx + 0.5 + (r() - 0.5) * 0.36, z = gy + 0.5 + (r() - 0.5) * 0.36;
        if (k.id === "gratefall") return { kind: "gratefall", age: 0.4, seed: r() * 10, sway: 0, swayAmp: 0, windy: 0, vx: 0, vy: -2.6, vz: 0, life: 1.4, size: 0.05, h: 0.34, glow: 1.3, alpha: 0.5, x, z, y: 0.98, top: 1.2, layer: "life:breath" };   // (a soft pale streak: the rain picture is too thin to read down here)
        const a = r() * Math.PI * 2, s = 0.3 + r() * 0.5; return { kind: "gratesplash", age: 0.4, seed: r() * 10, sway: 0, swayAmp: 0, windy: 0, vx: Math.cos(a) * s, vy: 0.5 + r() * 0.5, vz: Math.sin(a) * s, life: 1.4, size: 0.045, glow: 1.3, alpha: 0.8, x, z, y: 0.03, top: 1.2, layer: "life:breath", grav: 3 }; }
      if (k.id === "steam") { const a = r() * Math.PI * 2, d = 0.3 + r() * 1.6; return { kind: "steam", age: 0.4, seed: r() * 10, sway: 0.5 + r(), swayAmp: 0.1, windy: 0.3, vx: 0, vy: 0.25 + r() * 0.2, vz: 0, life: 2.5 + r() * 2, size: 0.25 + r() * 0.2, grow: 0.18, glow: 1.3, alpha: 0.4, x: eye[0] + Math.cos(a) * d, z: eye[2] + Math.sin(a) * d, y: 0.05 + r() * 0.2, top: 2.2, layer: "life:breath" }; }
      return sp0.call(this, k, eye, R, env); }; }
  // the floodwater in the mesh (the flooded mood's water on the sunken squares), the damp, the draft, the lightning through the grates, the steam's haze
  const flooded = new WeakMap();
  const bf0 = CM.beforeFrame; CM.beforeFrame = (game, ren, dt, now) => { if (bf0) bf0(game, ren, dt, now); if (!below(game)) return; const fl = game.floor, W = CM.aboveNow(game), d = DEPTH[fl.number] || 0, t = now / 1000;
    if (game.on && !game._floodHooked) { game._floodHooked = true; game.on("moved", () => { if (CM.floodedHere(game) && CM.audio && CM.audio.play) CM.audio.play("splash", 0.5); }); }   // (the wading's splash)
    const level = CM.floodNow(game), want = level > 0 ? CM.floodSquares(game, fl).length : 0, have = flooded.get(fl) || 0;   // the water comes and goes with the level
    if (want !== have) { fl.decor = (fl.decor || []).filter((e) => !e.flood); if (want) for (const [x, y] of CM.floodSquares(game, fl)) fl.decor.push({ kind: "water", x, y, flood: true }); flooded.set(fl, want); }
    const rain = W.kind === "rain" || W.kind === "storm" ? W.strength : 0; if (d && rain > 0) ren.damp = Math.max(ren.damp || 0, 0.4 + 0.5 * rain * d);
    if (W.wind.speed > 0.6 && ren.lights) { const gust = W.wind.speed - 0.45; ren.lights.forEach((l, i) => { if (!l.flicker) return; const k = 1 - gust * (0.3 + 0.4 * Math.abs(Math.sin(t * (6 + i * 0.7) + i * 1.9)) * Math.abs(Math.sin(t * 1.3 + i))); l.colour = l.colour.map((c) => c * k); }); ren.wind = { dir: W.wind.dir, k: 0.6 * gust }; }   // (the draft: the torches gutter and lean, the smoke drifts)
    if (d && CM.gratesOf && CM.stormLightNow && W.kind === "storm") { const f = CM.stormLightNow(); if (f > 0.05 && !CM.reducedMotion) { ren.lights = ren.lights || []; for (const [x, y] of CM.gratesOf(fl)) { if (!near(fl, x, y, 9)) continue; const v = f * f * d * 2.5; ren.lights.push({ x: x + 0.5, y: 0.98, z: y + 0.5, reach: 3.2, colour: [0.7 * v, 0.8 * v, 1.0 * v], flicker: false, d: Math.abs(x - fl.pos[0]) + Math.abs(y - fl.pos[1]) }); } } }   // (lightning through the grates)
    if (ren.air && hot(fl) && (CM.floodedHere(game) || (d && rain > 0.3))) ren.air = Object.assign({}, ren.air, { haze: Math.min(1, (ren.air.haze || 0) + 0.3) }); };   // (the steam thickens the haze)
}
