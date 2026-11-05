"use strict";
// The combat synergies - the window's side (v79.0, UPGRADE_PLAN_61.md part 9): when the storm's own lightning
// leaps on to a second foe (69zzr-synergy.js emits "stormchain"), the sky flashes with it and the thunder comes.
{ let flash = 0, thunderAt = 0;
  const thunder = () => { const A = CM.audio; if (!A || !A.ctx || !A.enabled || !A.master) return; try { const ctx = A.ctx, rate = ctx.sampleRate, secs = 2.4, n = Math.floor(rate * secs), b = ctx.createBuffer(1, n, rate), d = b.getChannelData(0); let lp = 0, lp2 = 0, s = 4242;
      for (let i = 0; i < n; i++) { s = (s * 1103515245 + 12345) & 0x7fffffff; const w = s / 0x7fffffff * 2 - 1, t = i / rate; lp += (w - lp) * 0.04; lp2 += (lp - lp2) * 0.09; d[i] = (lp2 * 9 + Math.exp(-t * 25) * w * 0.4) * Math.min(1, t / 0.03) * Math.exp(-t * 1.6); }
      const src = ctx.createBufferSource(), g = ctx.createGain(); src.buffer = b; g.gain.value = 0.55; src.connect(g); g.connect(A.master); src.start(); } catch (er) { /* quiet */ } };
  const bf0 = CM.beforeFrame; CM.beforeFrame = (game, r, dt, now) => { if (bf0) bf0(game, r, dt, now); if (!game || !game.ext) return;
    if (game.on && !game._chainHooked) { game._chainHooked = true; game.on("fx", (ev) => { if (ev && ev.kind === "stormchain") { flash = 1; thunderAt = performance.now() + 250; } }); }
    if (thunderAt && now >= thunderAt) { thunder(); thunderAt = 0; }
    if (flash > 0) { if (r.skyx) r.skyx.flash = Math.max(r.skyx.flash || 0, flash * flash); flash = Math.max(0, flash - dt * 2.8); } };
}
