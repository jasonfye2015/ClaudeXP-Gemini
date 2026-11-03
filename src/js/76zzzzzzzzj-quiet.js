"use strict";
// Dynamic quiet (v46.4, UPGRADE_PLAN_41.md): while the party creeps through the dungeon with its light shaded (Douse,
// T), the music falls away to almost nothing over a few seconds and the dungeon's own sounds are left; when a fight
// starts out of that quiet - found - a sting strikes (a drum and a brass chord rising) and the music swells back up.
// Lighting up again brings it back gently.
{ const M = CM.music; if (M) {
  let quiet = false, factor = 1;
  const apply = (k, t = 2.5) => { factor = k; const c = CM.audio && CM.audio.ctx; if (M.master && c && M.enabled) M.master.gain.setTargetAtTime(M.volume * k, c.currentTime, t); };
  { const sv0 = M.setVolume; M.setVolume = function (v) { const out = sv0.call(this, v); if (factor !== 1) apply(factor, 0.1); return out; }; }
  const sting = () => { if (!M.enabled || !M._ensure()) return; const c = CM.audio.ctx, at = c.currentTime + 0.02, dest = M.master;
    M._osc("sine", 55, at, at + 0.4, 0.5, 300, dest); M._osc("sine", 41, at + 0.02, at + 0.6, 0.35, 200, dest);
    for (const [m, d] of [[50, 0], [53, 0.02], [57, 0.04], [62, 0.06]]) { const hz = 440 * Math.pow(2, (m - 69) / 12); M._osc("sawtooth", hz, at + d, at + 1.1, 0.06, 1200, dest); M._osc("sawtooth", hz * 2, at + d + 0.3, at + 1.3, 0.03, 1800, dest); } };
  CM.musicQuiet = () => quiet;
  setInterval(() => { const g = CM.game, fl = g && g.floor; if (!g || !fl) return; const creeping = g.mode === "explore" && Boolean(g.lightOut) && !(g.spellLight > 0) && CM.isDeep && CM.isDeep(fl.number);
    if (creeping && !quiet) { quiet = true; apply(0.12, 2.5); }
    else if (!creeping && quiet) { quiet = false; if (g.mode === "combat") { sting(); apply(1, 0.15); } else apply(1, 1.5); } }, 250);
} }
