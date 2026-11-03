"use strict";
// Water and weather (v45.2, UPGRADE_PLAN_40.md): above ground the weather is heard - rain as a hiss, pattering on the
// roofs when there are houses about and dripping fat from the leaves under the trees; the wind in gusts as strong as it
// is (a breeze on a clear day, a howl on a windy one); and snow hushing everything, the ambience let down while it
// falls. Below, wading is heard by its depth - a light splash in a puddle, a slosh to the knee on a flooded floor or
// in the tide - and standing in water, it laps.
{ const live = () => { const A = CM.audio; return A && A.ctx && A.enabled && A.master; };
  let noise = null; const N = (c) => { if (!noise) { const n = c.sampleRate * 2, b = c.createBuffer(1, n, c.sampleRate), d = b.getChannelData(0); let p = 0; for (let i = 0; i < n; i++) { const w = Math.random() * 2 - 1; p = 0.97 * p + 0.03 * w; d[i] = w * 0.6 + p * 2; } noise = b; } return noise; };
  // a bed: looping noise through a filter, its level eased toward a want
  const beds = {}; const bed = (id, type, hz, q) => { const A = CM.audio, c = A.ctx; let B = beds[id]; if (B && B.ctx === c) return B; const s = c.createBufferSource(), f = c.createBiquadFilter(), g = c.createGain(); s.buffer = N(c); s.loop = true; f.type = type; f.frequency.value = hz; f.Q.value = q || 0.7; g.gain.value = 0;
    s.connect(f); f.connect(g); g.connect(A.master); s.start(); B = beds[id] = { ctx: c, s, f, g, level: 0 }; return B; };
  const ease = (B, want, t = 0.8) => { const c = CM.audio.ctx; if (Math.abs(B.level - want) < 0.002) return; B.level = want; B.g.gain.setTargetAtTime(want, c.currentTime, t); };
  const drop = (c, at, hz, vol, len = 0.04) => { const o = c.createOscillator(), g = c.createGain(); o.type = "sine"; o.frequency.setValueAtTime(hz, at); o.frequency.exponentialRampToValueAtTime(hz * 0.55, at + len); g.gain.setValueAtTime(vol, at); g.gain.exponentialRampToValueAtTime(0.0001, at + len); o.connect(g); g.connect(CM.audio.master); o.start(at); o.stop(at + len + 0.02); };
  const near = (fl, x, y, test, r = 2) => { for (let dy = -r; dy <= r; dy++) for (let dx = -r; dx <= r; dx++) if (test(x + dx, y + dy)) return true; return false; };
  let tick = 0, gust = 0, ambientWas = null;
  const step = () => { if (!live()) return; const g = CM.game, fl = g && g.floor, c = CM.audio.ctx; if (!fl || g.mode === "title") { for (const B of Object.values(beds)) ease(B, 0); return; }
    const top = fl.number === 0 || fl.number === -1, w = top ? CM.weather(g) : "clear", [px, py] = fl.pos, A = CM.audio;
    const roofs = top && near(fl, px, py, (x, y) => CM.isBuilding && CM.isBuilding(fl, x, y)), leaves = top && (fl.canopy || []).includes(`${px},${py}`);
    const rain = top && (w === "rain" || (CM.stormNow && CM.stormNow(g)));
    ease(bed("rain", "lowpass", 5200), rain ? 0.11 : 0); ease(bed("rainlow", "lowpass", 700), rain ? 0.06 : 0);
    if (rain) { const n = roofs ? 6 : leaves ? 2 : 3; for (let i = 0; i < n; i++) drop(c, c.currentTime + Math.random() * 0.25, roofs ? 2600 + Math.random() * 1800 : leaves ? 700 + Math.random() * 500 : 1800 + Math.random() * 1500, roofs ? 0.025 : leaves ? 0.05 : 0.015, leaves ? 0.09 : 0.03); }
    const wind = top ? (CM.windOf ? CM.windOf(w)[0] : 0.15) : 0; gust += (Math.random() - 0.5) * 0.3; gust = Math.max(-1, Math.min(1, gust * 0.97)); const W = bed("wind", "bandpass", 420, 1.2);
    W.f.frequency.setTargetAtTime(320 + wind * 260 + gust * 120, c.currentTime, 0.6); ease(W, top ? Math.max(0, wind * 0.06 * (1 + gust * 0.6)) : 0, 1.2);
    // the snow's hush: the ambience let down while it falls
    if (A.ambientGain) { const want = top && w === "snow" ? 0.18 : 0.5; if (ambientWas !== want) { A.ambientGain.gain.setTargetAtTime(want, c.currentTime, 2); ambientWas = want; } }
    // standing in water: it laps
    const wet = fl.special === "wading" || fl.tide || (fl.decor || []).some((d) => d.kind === "water" && d.x === px && d.y === py) || (CM.waterHere && CM.waterHere(px, py));
    const L = bed("lap", "bandpass", 600, 2); L.f.frequency.setTargetAtTime(450 + Math.sin(tick * 0.7) * 150, c.currentTime, 0.4); ease(L, wet && g.mode === "explore" ? 0.03 + 0.02 * Math.max(0, Math.sin(tick * 0.9)) : 0, 0.5); tick++; };
  setInterval(() => { try { step(); } catch (e) { /* (quiet) */ } }, 250);
  // wading: a step in water by its depth
  CM.wadeSound = (deep) => { if (!live()) return; const c = CM.audio.ctx, at = c.currentTime, s = c.createBufferSource(), f = c.createBiquadFilter(), g = c.createGain(); s.buffer = N(c); f.type = "bandpass"; f.frequency.setValueAtTime(deep ? 500 : 1400, at); f.frequency.exponentialRampToValueAtTime(deep ? 220 : 700, at + (deep ? 0.45 : 0.18)); f.Q.value = 1.4;
    g.gain.setValueAtTime(0.0001, at); g.gain.exponentialRampToValueAtTime(deep ? 0.35 : 0.18, at + (deep ? 0.12 : 0.02)); g.gain.exponentialRampToValueAtTime(0.0001, at + (deep ? 0.5 : 0.2)); s.connect(f); f.connect(g); g.connect(CM.audio.master); s.start(at, Math.random()); s.stop(at + 0.6);
    if (deep) for (let i = 0; i < 3; i++) drop(c, at + 0.15 + Math.random() * 0.3, 500 + Math.random() * 600, 0.04, 0.06); };
  const bind = () => { const g = CM.game; if (!g || !g.on) return false; g.on("sound", (name) => { if (name !== "step" || !g.floor) return; const fl = g.floor, [x, y] = fl.pos;
      const deep = fl.special === "wading" || fl.tide, shallow = (fl.decor || []).some((d) => d.kind === "water" && d.x === x && d.y === y) || (CM.waterHere && CM.waterHere(x, y)); if (deep || shallow) CM.wadeSound(Boolean(deep)); }); return true; };
  const t = typeof self !== "undefined" && self.CM_WORKER ? null : setInterval(() => { if (bind()) clearInterval(t); }, 300);
}
