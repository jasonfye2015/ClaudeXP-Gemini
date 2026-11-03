"use strict";
// Fire (v45.4, UPGRADE_PLAN_40.md): fire is heard - the party's torch crackles, quietly while it is new and louder and
// more fitfully as it burns low (its last forty steps), and not at all when it is doused or a lantern is carried; a lit
// brazier roars as the party comes near it; and the Foundry's vents, and anything burning, bubble and pop like lava.
{ const live = () => { const A = CM.audio; return A && A.ctx && A.enabled && A.master; };
  let noise = null; const N = (c) => { if (!noise) { const n = c.sampleRate * 2, b = c.createBuffer(1, n, c.sampleRate), d = b.getChannelData(0); for (let i = 0; i < n; i++) d[i] = Math.random() * 2 - 1; noise = b; } return noise; };
  const pop = (c, at, vol, hz) => { const s = c.createBufferSource(), f = c.createBiquadFilter(), g = c.createGain(); s.buffer = N(c); f.type = "bandpass"; f.frequency.value = hz; f.Q.value = 3; g.gain.setValueAtTime(vol, at); g.gain.exponentialRampToValueAtTime(0.0001, at + 0.02 + Math.random() * 0.02); s.connect(f); f.connect(g); g.connect((CM.ambienceOut ? CM.ambienceOut() : CM.audio.master)); s.start(at, Math.random() * 1.5); s.stop(at + 0.06); };
  const bloop = (c, at, vol) => { const o = c.createOscillator(), g = c.createGain(), hz = 60 + Math.random() * 50; o.type = "sine"; o.frequency.setValueAtTime(hz, at); o.frequency.exponentialRampToValueAtTime(hz * 2.6, at + 0.12); g.gain.setValueAtTime(0.0001, at); g.gain.exponentialRampToValueAtTime(vol, at + 0.03); g.gain.exponentialRampToValueAtTime(0.0001, at + 0.16); o.connect(g); g.connect((CM.ambienceOut ? CM.ambienceOut() : CM.audio.master)); o.start(at); o.stop(at + 0.2); };
  let roar = null; const roarBed = (c) => { if (roar && roar.ctx === c) return roar; const s = c.createBufferSource(), f = c.createBiquadFilter(), g = c.createGain(); s.buffer = N(c); s.loop = true; f.type = "lowpass"; f.frequency.value = 380; g.gain.value = 0; s.connect(f); f.connect(g); g.connect((CM.ambienceOut ? CM.ambienceOut() : CM.audio.master)); s.start(); return (roar = { ctx: c, g, f, level: 0 }); };
  CM.torchCrackle = (g) => { const L = g.light || {}; if (g.lightOut || L.kind !== "torch") return 0; const left = L.left === undefined ? 400 : L.left; return left > 40 ? 0.35 : 0.35 + (1 - left / 40) * 0.65; };
  setInterval(() => { if (!live()) return; const g = CM.game, fl = g && g.floor, c = CM.audio.ctx; if (!fl || g.mode === "title") { if (roar) { roar.g.gain.setTargetAtTime(0, c.currentTime, 0.4); roar.level = 0; } return; } const at = c.currentTime + 0.02, [px, py] = fl.pos;
    // the torch
    const k = (g.mode === "explore" || g.mode === "combat") && fl.number !== 0 ? CM.torchCrackle(g) : 0;
    if (k) { const n = Math.random() < k ? 1 + Math.floor(Math.random() * 3 * k) : 0; for (let i = 0; i < n; i++) pop(c, at + Math.random() * 0.2, 0.05 + 0.1 * k * Math.random(), 1800 + Math.random() * 3000); }
    // braziers, and what burns
    let bd = 99; for (const [key, t] of Object.entries(fl.things)) { if (t.type !== "brazier" || !t.lit) continue; const [x, y] = key.split(",").map(Number); bd = Math.min(bd, Math.hypot(x - px, y - py)); }
    const burning = fl.burning && (g.clock || 0) < fl.burning.until; if (burning) bd = Math.min(bd, 2);
    const R = roarBed(c), want = bd < 6 ? 0.12 * (1 - bd / 6) : 0; if (Math.abs(R.level - want) > 0.004) { R.g.gain.setTargetAtTime(want, c.currentTime, 0.4); R.level = want; } if (want > 0.02 && Math.random() < 0.5) pop(c, at + Math.random() * 0.2, want * 0.8, 1200 + Math.random() * 1500);
    // lava: the vents of the Foundry (and its band), what burns
    let vd = 99; for (const [key, f] of Object.entries(fl.features || {})) { if (f.type !== "vents") continue; const [x, y] = key.split(",").map(Number); vd = Math.min(vd, Math.hypot(x - px, y - py)); }
    if (fl.number >= 1 && CM.themeIndex(fl.number) === 7) vd = Math.min(vd, 4); if (burning) vd = Math.min(vd, 3);
    if (vd < 6 && Math.random() < 0.35 * (1 - vd / 6)) bloop(c, at + Math.random() * 0.2, 0.12 * (1 - vd / 6)); }, 220);
}
