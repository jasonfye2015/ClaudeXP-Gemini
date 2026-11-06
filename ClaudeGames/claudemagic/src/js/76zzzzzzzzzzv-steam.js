"use strict";
// Steam and the burning roots - the window's side (UPGRADE_PLAN_63.md sets 1.3 and 3.2, release 5): on a steam
// square the white billows thicken to a screen about the party; while the roots burn (69zzx-steam.js) the walls
// near the party wear flames and smoke and throw an orange, flickering light, and a crackle is heard; the look
// line names the steam.
{ const r = Math.random;
  { const k0 = CM.airKinds; CM.airKinds = function (env) { const out = k0.call(this, env); const g = CM.game, fl = g && g.floor; if (env.surface || !fl || !(fl.number >= 1) || g.mode === "title") return out;
      if (CM.steamHere && CM.steamHere(g)) out.push({ id: "steamscreen", rate: 22 });
      if (CM.rootsBurning && CM.rootsBurning(g, fl) > 0) out.push({ id: "rootfire", rate: 40 }, { id: "smoke", rate: 8 }); return out; }; }
  { const sp0 = CM.Air.prototype.spawn; CM.Air.prototype.spawn = function (k, eye, R, env) { const g = CM.game;
      if (k.id === "steamscreen") { const a = r() * Math.PI * 2, d = 0.4 + r() * 2.2; return { kind: "steam", age: 0.4, seed: r() * 10, sway: 0.5 + r(), swayAmp: 0.12, windy: 0.2, vx: 0, vy: 0.2 + r() * 0.2, vz: 0, life: 3 + r() * 2.5, size: 0.5 + r() * 0.4, grow: 0.25, glow: 1.3, alpha: 0.55, x: eye[0] + Math.cos(a) * d, z: eye[2] + Math.sin(a) * d, y: 0.05 + r() * 0.3, top: 2.4, layer: "life:breath" }; }
      if (k.id === "rootfire") { const fl = g.floor, N = fl.grid.length, open = (x, y) => x >= 0 && y >= 0 && x < N && y < N && fl.grid[y][x] === 0; for (let tries = 0; tries < 6; tries++) { const x = Math.floor(eye[0]) + Math.floor(r() * 9) - 4, y = Math.floor(eye[2]) + Math.floor(r() * 9) - 4; if (!open(x, y)) continue; const W = CM.DIRS.filter(([dx, dy]) => !open(x + dx, y + dy)); if (!W.length) continue; const [dx, dy] = W[Math.floor(r() * W.length)];
          return { kind: "rootfire", age: 0.4, seed: r() * 10, sway: 3 + r() * 3, swayAmp: 0.2, windy: 0, vx: 0, vy: 0.8 + r() * 0.6, vz: 0, life: 0.9 + r() * 0.6, size: 0.18 + r() * 0.2, h: 0.4 + r() * 0.3, glow: 2, alpha: 0.95, x: x + 0.5 + dx * 0.42 + (r() - 0.5) * 0.5 * Math.abs(dy), z: y + 0.5 + dy * 0.42 + (r() - 0.5) * 0.5 * Math.abs(dx), y: 0.05 + r() * 0.7, top: 1.3, layer: "life:treefire" }; } return null; }
      return sp0.call(this, k, eye, R, env); }; }
  { const xl0 = CM.extraLights; CM.extraLights = (game, fl, out, renderer) => { if (xl0) xl0(game, fl, out, renderer); if (!fl || !(fl.number >= 1) || !CM.rootsBurning || !CM.rootsBurning(game, fl) || !renderer || !renderer.eye) return; const [px, py] = fl.pos; for (let i = 0; i < 4; i++) { const a = i * Math.PI / 2 + 0.4, x = px + 0.5 + Math.cos(a) * 1.6, z = py + 0.5 + Math.sin(a) * 1.6; out.push({ x, y: 0.7, z, reach: 3, colour: [1.0, 0.5, 0.15], flicker: true, d: 2 }); } }; }
  // the look line
  { const d0 = CM.UI.prototype.drawSky; if (d0) CM.UI.prototype.drawSky = function (...a) { const out = d0.apply(this, a); try { const g = this.game, el = this.$ && this.$("#view .sky .wxtext"); if (!el || !g || !g.floor) return out; if (CM.steamHere && CM.steamHere(g) && !el.textContent.includes("steam")) el.textContent += " - steam (a square's sight, bows at three quarters)"; if (CM.rootsDry && CM.rootsDry(g) && !el.textContent.includes("roots")) el.textContent += " - the roots are dry"; } catch (e) { /* (quiet) */ } return out; }; }
  // the fire's sound: a crackle while the roots burn
  let crackleAt = 0; const bf0 = CM.beforeFrame; CM.beforeFrame = (game, ren, dt, now) => { if (bf0) bf0(game, ren, dt, now); if (!game || !game.floor || !game.ext || !CM.rootsBurning || !CM.rootsBurning(game, game.floor)) return; if (now < crackleAt) return; crackleAt = now + 300 + r() * 500; const A = CM.audio; if (!A || !A.ctx || !A.enabled || !A.master) return;
    try { const ctx = A.ctx, at = ctx.currentTime, o = ctx.createOscillator(), g = ctx.createGain(); o.type = "square"; o.frequency.setValueAtTime(1800 + r() * 2400, at); g.gain.setValueAtTime(0.035, at); g.gain.exponentialRampToValueAtTime(0.0001, at + 0.03); o.connect(g); g.connect(A.master); o.start(at); o.stop(at + 0.04); } catch (e) { /* quiet */ } };
}
