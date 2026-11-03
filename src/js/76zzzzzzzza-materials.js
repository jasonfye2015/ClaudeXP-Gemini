"use strict";
// Materials (v45.0, UPGRADE_PLAN_40.md): a blow sounds like what it lands on, under the hit's own sound - a blade
// rings on plate (a bell's inharmonic partials), cracks on shell and crystal, crunches on bone, thuds into hide and
// slaps into flesh, and only whistles through the bodiless; an arrow lands with a wooden thunk before it; a weak spot
// struck is louder and brighter. (CM.hideOf, 14-items.js, says what a foe is made of; the crates and barrels that
// break, 69w-breakables.js, knock like wood.)
{ const ctx = () => CM.audio && CM.audio.ctx, live = () => { const A = CM.audio; return A && A.ctx && A.enabled && A.master; };
  let noise = null; const N = (c) => { if (!noise) { const n = c.sampleRate, b = c.createBuffer(1, n, n), d = b.getChannelData(0); for (let i = 0; i < n; i++) d[i] = Math.random() * 2 - 1; noise = b; } return noise; };
  const out = (c, pan) => { const A = CM.audio, g = c.createGain(); g.gain.value = 0.7; g.connect(A.master); if (pan && c.createStereoPanner) { const p = c.createStereoPanner(); p.pan.value = Math.max(-1, Math.min(1, pan)); p.connect(g); return p; } return g; };
  const sine = (c, dest, hz, at, dur, vol, type = "sine") => { const o = c.createOscillator(), g = c.createGain(); o.type = type; o.frequency.value = hz; g.gain.setValueAtTime(vol, at); g.gain.exponentialRampToValueAtTime(0.0001, at + dur); o.connect(g); g.connect(dest); o.start(at); o.stop(at + dur + 0.05); };
  const burst = (c, dest, at, dur, vol, hz, type = "bandpass", q = 1, sweepTo) => { const s = c.createBufferSource(), f = c.createBiquadFilter(), g = c.createGain(); s.buffer = N(c); s.playbackRate.value = 0.5 + Math.random();
    f.type = type; f.frequency.setValueAtTime(hz, at); if (sweepTo) f.frequency.exponentialRampToValueAtTime(sweepTo, at + dur); f.Q.value = q; g.gain.setValueAtTime(vol, at); g.gain.exponentialRampToValueAtTime(0.0001, at + dur); s.connect(f); f.connect(g); g.connect(dest); s.start(at, Math.random() * 0.5); s.stop(at + dur + 0.05); };
  const SOUND = {
    plate: (c, d, at, k) => { const f = 900 + Math.random() * 300; for (const [m, v, len] of [[1, 0.12, 0.7], [2.76, 0.07, 0.45], [5.4, 0.04, 0.25], [8.9, 0.02, 0.12]]) sine(c, d, f * m, at, len * (0.8 + k * 0.4), v * k); burst(c, d, at, 0.03, 0.3 * k, 4000, "highpass"); },
    shell: (c, d, at, k) => { burst(c, d, at, 0.06, 0.35 * k, 2800, "bandpass", 3); burst(c, d, at + 0.025, 0.05, 0.2 * k, 1800, "bandpass", 4); sine(c, d, 1300, at, 0.12, 0.05 * k, "triangle"); },
    bone: (c, d, at, k) => { for (let i = 0; i < 4; i++) burst(c, d, at + i * 0.018 + Math.random() * 0.01, 0.03, (0.25 - i * 0.04) * k, 1500 + Math.random() * 1500, "bandpass", 5); sine(c, d, 260, at, 0.08, 0.08 * k, "triangle"); },
    hide: (c, d, at, k) => { sine(c, d, 95, at, 0.18, 0.3 * k); burst(c, d, at, 0.1, 0.25 * k, 500, "lowpass"); },
    flesh: (c, d, at, k) => { burst(c, d, at, 0.09, 0.3 * k, 900, "lowpass", 1, 300); sine(c, d, 120, at, 0.1, 0.15 * k); },
    none: (c, d, at, k) => burst(c, d, at, 0.35, 0.18 * k, 600, "bandpass", 2, 2400),
    wood: (c, d, at, k) => { sine(c, d, 190, at, 0.12, 0.25 * k, "triangle"); sine(c, d, 420, at, 0.05, 0.08 * k); burst(c, d, at, 0.05, 0.2 * k, 1200, "bandpass", 2); } };
  CM.MATERIAL_SOUNDS = SOUND;
  const isBow = (h) => { const w = h && h.weapon; return Boolean(w && /Bow|Sling/.test(`${w.base || ""} ${w.name || ""}`)); };
  CM.materialHit = (foe, hero, crit, pan = 0) => { if (!live()) return; const c = ctx(), at = c.currentTime + 0.01, d = out(c, pan), k = crit ? 1.5 : 1, kind = foe ? CM.hideOf(foe) || "flesh" : "wood";
    try { if (isBow(hero)) { SOUND.wood(c, d, at, 0.8); SOUND[kind] && SOUND[kind](c, d, at + 0.04, k * 0.7); } else (SOUND[kind] || SOUND.flesh)(c, d, at, k); } catch (e) { /* (quiet) */ } };
  const bind = () => { const g = CM.game; if (!g || !g.on) return false; let last = 0;
    g.on("fx", (fx) => { if (!fx || fx.kind !== "hit" || fx.spell) return; const now = performance.now(); if (now - last < 60) return; last = now;
      if (!fx.foe || fx.foe.breakable || fx.foe.crate) { CM.materialHit(null, fx.hero, fx.crit); return; } const i = (g.foes || []).indexOf(fx.foe), n = (g.foes || []).length; CM.materialHit(fx.foe, fx.hero, fx.crit, n > 1 && i >= 0 ? (i / (n - 1) - 0.5) * 0.8 : 0); }); return true; };
  const t = typeof self !== "undefined" && self.CM_WORKER ? null : setInterval(() => { if (bind()) clearInterval(t); }, 300);
}
