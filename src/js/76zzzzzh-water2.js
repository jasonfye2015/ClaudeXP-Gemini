"use strict";
// Water you can see into (v30.8, UPGRADE_PLAN_25.md): the shallows by the banks show their bed - pebbles and weed -
// through the ripples; now and then a fish turns in the deeper water; foam gathers along the banks, more where the
// river runs; and rings spread where the followers, the townsfolk and the beasts stand or wade in water, as they did
// for the party (76zzzzd-water.js). The shader reads the floor's water from its map (40-render.js, CM.waterCells).
{ const last = new Map();
  const bf0 = CM.beforeFrame; CM.beforeFrame = (game, r, dt, now) => { if (bf0) bf0(game, r, dt, now);
    const K = CM.fxKit; if (!K || !K.fxs || CM.reducedMotion || !CM.waterHere || !game.floor) return; const fl = game.floor;
    for (const s of r.sprites || []) { if (!s.bend || s.flat || s.air) continue; if (Math.abs(s.x - fl.pos[0]) + Math.abs(s.y - fl.pos[1]) > 6 || !CM.waterHere(s.x, s.y)) continue;
      const k = `${s.layer}:${s.x},${s.y}`, wx = s.x + 0.5 + (s.dx || 0), wz = s.y + 0.5 + (s.dz || 0), L = last.get(k), moved = L && Math.hypot(L.x - wx, L.z - wz) > 0.02;
      if (!L || now - L.t > (moved ? 700 : 2600)) { last.set(k, { t: now, x: wx, z: wz }); if (L) K.fxs.ring({ at: [wx, 0, wz], to: (s.w || 0.6) * 1.3, ms: 1100, glow: 0.3 }); }
      else if (L) { L.x = wx; L.z = wz; } }
    if (last.size > 300) last.clear(); };
}
