"use strict";
// The place's own sound (v28.2, UPGRADE_PLAN_23.md): over the depth's ambience, loops of the place itself, made by the
// game (no recordings) when first wanted, each as loud as the party is near to it and from its side: birds by day and
// crickets by night in the Wood, the river beside it; the market's murmur about the Square and hammering at the forge
// by day, in the town; in the houses' rooms, the tavern's talk and the forge's anvil; below, each band its own - water
// lapping in the Flooded Vaults, the Undercroft and the Drowned Town, bubbling in the Fungal Deep, chimes in the
// Crystal Caverns, the Foundry's hammers and hiss, a slow beat at the Root of the World.
{ const A = CM.audio;
  const make = (id) => { const ctx = A.ctx, rate = ctx.sampleRate, secs = 10, n = rate * secs, out = new Float32Array(n); let s = CM.hashSeed(`amb:${id}`) || 1;
    const rnd = () => ((s = (s * 1103515245 + 12345) & 0x7fffffff) / 0x7fffffff), noise = () => rnd() * 2 - 1;
    const tone = (at, len, f0, f1, amp, decay = 6) => { const i0 = Math.floor(at * rate), m = Math.floor(len * rate); let ph = 0; for (let i = 0; i < m && i0 + i < n; i++) { const k = i / m, f = f0 + (f1 - f0) * k; ph += 2 * Math.PI * f / rate; out[i0 + i] += Math.sin(ph) * amp * Math.exp(-k * decay) * Math.min(1, i / (rate * 0.005)); } };
    if (id === "birds") { for (let c = 0; c < 9; c++) { const at = rnd() * (secs - 1), f = 2400 + rnd() * 1800, k = 2 + Math.floor(rnd() * 4); for (let j = 0; j < k; j++) tone(at + j * 0.09, 0.06, f, f * (1.2 + rnd() * 0.3), 0.07, 3); } }
    else if (id === "crickets") { for (const [f, off] of [[4400, 0], [4700, 0.31]]) for (let t = off; t < secs - 0.2; t += 0.62) for (let j = 0; j < 4; j++) tone(t + j * 0.035, 0.025, f, f, 0.025, 2); }
    else if (id === "river" || id === "lapping") { let y = 0, y2 = 0; for (let i = 0; i < n; i++) { const t = i / rate; y += 0.02 * (noise() - y); y2 += 0.004 * (noise() - y2); out[i] = id === "river" ? y * 0.55 * (0.8 + 0.2 * Math.sin(2 * Math.PI * 0.13 * t)) + y2 * 0.3 : y2 * 0.9 * (0.4 + 0.6 * Math.max(0, Math.sin(2 * Math.PI * 0.3 * t))); }
      if (id === "lapping") for (let c = 0; c < 5; c++) tone(rnd() * (secs - 0.3), 0.12, 900, 1600, 0.05, 8); }
    else if (id === "murmur") { let y = 0, b = 0; for (let i = 0; i < n; i++) { const t = i / rate; y += 0.08 * (noise() - y); b = 0.97 * b + y; const syll = 0.5 + 0.5 * Math.sin(2 * Math.PI * (3.1 + Math.sin(t * 0.7)) * t) * Math.sin(2 * Math.PI * 0.37 * t); out[i] = (y - b * 0.03) * 0.25 * syll; }
      for (let c = 0; c < 6; c++) tone(rnd() * (secs - 0.5), 0.28, 160 + rnd() * 90, 140 + rnd() * 60, 0.03, 2); }
    else if (id === "hammer") { for (let t = 0.2; t < secs - 0.6; t += 1.1 + (rnd() < 0.2 ? 0.55 : 0)) { tone(t, 0.6, 620, 618, 0.11, 7); tone(t, 0.5, 1340, 1338, 0.06, 9); tone(t, 0.25, 2210, 2200, 0.03, 12); const i0 = Math.floor(t * rate); for (let i = 0; i < rate * 0.01; i++) out[i0 + i] += noise() * 0.15 * (1 - i / (rate * 0.01)); } }
    else if (id === "hiss") { for (let c = 0; c < 4; c++) { const at = rnd() * (secs - 2), m = Math.floor(rate * 1.4), i0 = Math.floor(at * rate); let y = 0; for (let i = 0; i < m; i++) { const x = noise(); y = x - y * 0.6; out[i0 + i] += y * 0.05 * Math.sin(Math.PI * i / m); } } }
    else if (id === "bubbles") { for (let c = 0; c < 28; c++) tone(rnd() * (secs - 0.1), 0.05, 220 + rnd() * 200, 600 + rnd() * 400, 0.05, 4); }
    else if (id === "chimes") { const scale = [2093, 2349, 2637, 3136, 3520]; for (let c = 0; c < 10; c++) tone(rnd() * (secs - 2), 2.2, scale[Math.floor(rnd() * 5)], scale[Math.floor(rnd() * 5)] * 1.0, 0.03, 3); }
    else if (id === "beat") { for (let t = 0.2; t < secs - 0.5; t += 1.33) { tone(t, 0.18, 60, 45, 0.25, 5); tone(t + 0.26, 0.15, 55, 42, 0.18, 6); } }
    const b = ctx.createBuffer(1, n, rate); b.getChannelData(0).set(out); return b; };
  const loops = CM.__ambLoops = {};
  const want = (game) => { const fl = game.floor, out = {}; if (!fl || game.mode === "title" || game.mode === "camp") return out; const n = fl.number, [x, y] = fl.pos, day = !CM.isNight(game), h = CM.hourOf(game) % 24, wx = CM.weather(game), season = CM.season(game);
    const near = (at, r, k) => { const d = Math.hypot(at[0] - x, at[1] - y); return d < r ? [k * (1 - d / r), at] : null; };
    if (n === -1) { if (day) out.birds = [(wx === "rain" ? 0.15 : season === "winter" ? 0.25 : 0.5), null]; else if (season !== "winter" && wx !== "rain") out.crickets = [0.45, null];
      const rx = CM.riverX ? CM.riverX(y) : -99, d = Math.abs(rx - x); if (d < 7) out.river = [0.5 * (1 - d / 7), [rx, y]]; }
    else if (n === 0) { if (h >= 6 && h < 20 && CM.TOWN_AT) { const m = near(CM.TOWN_AT.market, 14, 0.4); if (m) out.murmur = m; } if (h >= 7 && h < 19 && CM.TOWN_BLOCKS && CM.TOWN_BLOCKS.smith) { const s = near(CM.TOWN_BLOCKS.smith.door, 10, 0.45); if (s) out.hammer = s; } if (day) out.birds = [0.18, null]; }
    else if (fl.special === "interior") { if (fl.interior === "smith") out.hammer = [0.4, null]; if (fl.interior === "tavern") out.murmur = [0.4, null]; }
    else if (CM.isDeep(n)) { const band = CM.isUndercroft(n) ? -1 : CM.themeIndex(n), B = { "-1": ["lapping", 0.35], 1: ["lapping", 0.35], 4: ["lapping", 0.5], 5: ["bubbles", 0.35], 6: ["chimes", 0.3], 7: ["hammer", 0.3], 9: ["beat", 0.35] }[band];
      if (B) out[B[0]] = [B[1], null]; if (band === 7) out.hiss = [0.25, null]; }
    return out; };
  const tick = () => { const g = CM.game, r = CM.renderer; if (!g || !A.ctx || !A.enabled) return; const W = want(g), ctx = A.ctx, now = ctx.currentTime;
    for (const id of new Set([...Object.keys(W), ...Object.keys(loops)])) { const w = W[id], L = loops[id];
      if (w && !L) { const src = ctx.createBufferSource(), gain = ctx.createGain(), pan = ctx.createStereoPanner ? ctx.createStereoPanner() : null; src.buffer = make(id); src.loop = true; src.loopStart = 0; gain.gain.value = 0;
        src.connect(gain); if (pan) { gain.connect(pan); pan.connect(A.master); } else gain.connect(A.master); src.start(now, Math.random() * 9); loops[id] = { src, gain, pan, idle: 0 }; continue; }
      if (!L) continue; const k = w ? w[0] : 0; L.gain.gain.setTargetAtTime(k * 0.6, now, 0.8);
      if (L.pan && w && w[1] && r) { const ang = Math.atan2(w[1][0] - g.floor.pos[0], -(w[1][1] - g.floor.pos[1])) - r.yaw; L.pan.pan.setTargetAtTime(CM.clamp(Math.sin(ang) * 0.85, -1, 1), now, 0.3); } else if (L.pan) L.pan.pan.setTargetAtTime(0, now, 0.5);
      L.idle = k ? 0 : L.idle + 1; if (L.idle > 25) { try { L.src.stop(); } catch (e) { /* (gone) */ } delete loops[id]; } } };
  setInterval(tick, 300);
}
