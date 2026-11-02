"use strict";
// Moving shadows (v41.0, UPGRADE_PLAN_36.md): below ground a shadow cast by a flame (the party's torch, a brazier, a wall
// torch: 76zzzv-shadows.js) sways and breathes with it - turning a little this way and that and lengthening as the flame
// dips - and the free-standing pillars of a room now cast their own long shadows away from the party's torch, swaying
// the same. (The sun's shadows above stay still.) Reduced motion keeps them steady.
{ const flick = (t, seed) => Math.sin(t * 7.3 + seed) * 0.5 + Math.sin(t * 11.9 + seed * 1.7) * 0.3 + Math.sin(t * 3.1 + seed * 0.3) * 0.2;   // (-1..1: three flickers at odd rates)
  const sc0 = CM.shadowCaster; if (sc0) CM.shadowCaster = (game, renderer, fl) => { const c = sc0(game, renderer, fl); if (!fl || fl.number === 0 || fl.number === -1 || CM.reducedMotion) return c; const t = performance.now() / 1000;
    return (x, y, w, dx = 0, dz = 0) => { const out = c(x, y, w, dx, dz); for (const s of out) if (s.rot !== undefined) { const f = flick(t, x * 3.7 + y * 1.3); s.rot += f * 0.07; s.len = (s.len || 1) * (1 + f * 0.08); s.alpha = (s.alpha || 0.5) * (1 - f * 0.08); } return out; }; };
  // a room's pillars: wall squares with open floor on three sides or all four
  const pillars = new WeakMap(), pillarsOf = (fl) => { let p = pillars.get(fl); if (p) return p; p = []; const N = fl.grid.length, open = (x, y) => fl.grid[y] && fl.grid[y][x] === 0;
    for (let y = 1; y < N - 1; y++) for (let x = 1; x < N - 1; x++) if (fl.grid[y][x] === 1 && CM.DIRS.filter(([dx, dy]) => open(x + dx, y + dy)).length >= 3) p.push([x, y]); pillars.set(fl, p); return p; };
  { const ls0 = CM.lifeSprites; CM.lifeSprites = (game, fl, now) => { const out = ls0 ? ls0(game, fl, now) : []; if (!fl || !(fl.number >= 1) || !CM.renderer || CM.renderer.index.shadow === undefined || game.mode !== "explore") return out;
      const eye = CM.renderer.eye || [fl.pos[0] + 0.5, 0.5, fl.pos[1] + 0.5], t = now / 1000;
      for (const [x, y] of pillarsOf(fl)) { const cx = x + 0.5, cz = y + 0.5, d = Math.hypot(cx - eye[0], cz - eye[2]); if (d > 6 || d < 0.6) continue;
        const f = CM.reducedMotion ? 0 : flick(t, x * 2.1 + y * 5.3), lx = (cx - eye[0]) / d, lz = (cz - eye[2]) / d, len = Math.min(4, 1.2 + d * 0.6) * (1 + f * 0.08);
        out.push({ x, y, layer: "shadow", flat: true, w: 1.0, len, rot: Math.atan2(lz, lx) + f * 0.05, alpha: Math.max(0, 0.6 - d * 0.07) * (1 - f * 0.08) }); }
      return out; }; }
}
