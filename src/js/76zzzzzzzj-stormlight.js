"use strict";
// Storm light (v41.3, UPGRADE_PLAN_36.md): when a storm is over Caer Duin (CM.stormNow, 76zzzzzc-sky.js) its lightning
// reaches down the shaft to the first floors - a cold flash whitening the stone, brightest by the shaft's foot and
// fainter each floor down (the third sees only a glimmer), and a while after it the thunder, muffled by the earth.
{ const STRENGTH = { 1: 0.55, 2: 0.32, 3: 0.15 };
  let flash = 0, next = 4, restrike = false, rumbleAt = 0, rumbleK = 0;
  const rumble = (k) => { const A = CM.audio; if (!A || !A.ctx || !A.enabled || !A.master) return; try {
      const ctx = A.ctx, rate = ctx.sampleRate, n = Math.floor(rate * 3.6), b = ctx.createBuffer(1, n, rate), d = b.getChannelData(0); let lp = 0, lp2 = 0, s = 54321;
      for (let i = 0; i < n; i++) { s = (s * 1103515245 + 12345) & 0x7fffffff; const w = s / 0x7fffffff * 2 - 1, t = i / rate; lp += (w - lp) * 0.012; lp2 += (lp - lp2) * 0.03; d[i] = lp2 * Math.min(1, t / 0.4) * Math.exp(-t * 0.8) * (1 + 0.5 * Math.sin(t * 5.3)) * 14; }
      const src = ctx.createBufferSource(), g = ctx.createGain(); src.buffer = b; g.gain.value = 0.5 * k; src.connect(g); g.connect(A.master); src.start(); } catch (er) { /* quiet */ } };
  const strengthOf = (game) => { const fl = game && game.floor; return fl && game.mode !== "title" && CM.stormNow && CM.stormNow(game) ? STRENGTH[fl.number] || 0 : 0; };
  const bf0 = CM.beforeFrame; CM.beforeFrame = (game, r, dt, now) => { if (bf0) bf0(game, r, dt, now); const k = strengthOf(game);
    if (k) { next -= dt; if (next <= 0) { flash = 1; restrike = Math.random() < 0.4; next = 8 + Math.random() * 20; rumbleAt = now + 1200 + Math.random() * 2500; rumbleK = k; } }
    if (restrike && flash < 0.45 && flash > 0.3) { flash = 0.8; restrike = false; }
    if (rumbleAt && now >= rumbleAt) { rumble(rumbleK); rumbleAt = 0; }
    flash = Math.max(0, flash - dt * 2.6); if (k && !CM.reducedMotion) r.roomFlash = Math.max(r.roomFlash || 0, flash * flash * k); };
  // the shaft's foot, where it is brightest
  const shaftOf = (fl) => { for (const [key, t] of Object.entries(fl.things)) if (t.type === "ladder" || t.type === "stairs_up") return key.split(",").map(Number); return null; };
  { const xl0 = CM.extraLights; CM.extraLights = (game, fl, out, renderer) => { if (xl0) xl0(game, fl, out, renderer); const k = strengthOf(game); if (!k || flash < 0.05 || CM.reducedMotion) return; const at = shaftOf(fl); if (!at) return;
      const d = Math.abs(at[0] - fl.pos[0]) + Math.abs(at[1] - fl.pos[1]); if (d > 10) return; const v = flash * flash * k * 4; out.unshift({ x: at[0] + 0.5, y: 1.0, z: at[1] + 0.5, reach: 5, colour: [0.7 * v, 0.8 * v, 1.0 * v], flicker: false, d: 0 }); }; }
  CM.stormLightNow = () => flash;
}
