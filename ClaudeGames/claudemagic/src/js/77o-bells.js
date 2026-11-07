"use strict";
// The bells of Caer Duin (UPGRADE_PLAN_76.md, release 2). The story turns on bells - taken down when the queen died,
// cast by the hundred in the Foundry, never rung - so they are almost unheard until the story earns them: in the
// Foundry, now and then, far off, a cracked bell begins to sound and is cut short. At the quiet ending a single bell
// rings out clear, the first in all the years; at the Last Page, three, a slow peal. After that, the town keeps the
// hours with a soft bell far off, and the title card opens with one. And each band's first floor gives the first
// phrase of the band's own theme, once, on arrival. All of it made as the music is (no recordings), on the music's and
// the ambience's own channels, so the sliders and the mute rule it as before.
//   CM.bellsRung(game) -> has the story earned them; CM.ringBell(count)
{ const A = CM.audio, M = CM.music;
  CM.bellsRung = (g) => Boolean(g && ((g.fame || []).some((e) => e && e.reminded) || (g.vext && g.vext("claude").edition === 2) || g.reminded));
  const live = () => A && A.ctx && A.enabled && M && M.enabled !== false && M._ensure && M._ensure();
  // a clear bell: a struck bell's partials (hum, prime, tierce, quint, nominal), each fading at its own pace
  const clearBell = (at, hz, gain, dest) => { const P = [[0.5, 1.0, 6.5], [1.0, 0.8, 5.0], [1.2, 0.45, 3.8], [1.5, 0.3, 3.0], [2.0, 0.38, 2.6], [2.97, 0.12, 1.4], [4.07, 0.06, 0.9]];
    const ctx = A.ctx; for (const [k, a, dur] of P) { const o = ctx.createOscillator(), g = ctx.createGain(); o.type = "sine"; o.frequency.value = hz * k * (1 + (k > 2 ? 0.002 : 0));
      g.gain.setValueAtTime(0.0001, at); g.gain.linearRampToValueAtTime(gain * a, at + 0.006); g.gain.exponentialRampToValueAtTime(0.0001, at + dur);   /* (struck, then dying away) */
      o.connect(g); g.connect(dest); o.start(at); o.stop(at + dur + 0.05); } };
  CM.ringBell = (count = 1, gain = 0.2, gap = 3.2, hz = 262) => { if (!live()) return false; const ctx = A.ctx, at = ctx.currentTime + 0.1; for (let i = 0; i < count; i++) clearBell(at + i * gap, hz * (i === 1 ? 0.89 : i === 2 ? 0.75 : 1), gain, A.master); return true; };   /* (on the effects, which no conversation ducks) */
  // the cracked bell in the Foundry, far off, cut short
  const crackedFar = () => { if (!A || !A.ctx || !A.enabled || !A.buffers || !A.buffers.bell) return; const ctx = A.ctx, s = ctx.createBufferSource(), g = ctx.createGain(), f = ctx.createBiquadFilter(), t = ctx.currentTime;
    s.buffer = A.buffers.bell; s.playbackRate.value = 0.82; f.type = "lowpass"; f.frequency.value = 900; g.gain.setValueAtTime(0.0001, t); g.gain.linearRampToValueAtTime(0.22, t + 0.03); g.gain.setValueAtTime(0.22, t + 0.32); g.gain.linearRampToValueAtTime(0.0001, t + 0.38);
    s.connect(f); f.connect(g); g.connect((CM.ambienceOut && CM.ambienceOut()) || A.master); s.start(t); s.stop(t + 0.5); };
  let nextCrack = 0;
  const tick = () => { const g = CM.game, now = performance.now();
    if (g && g.floor && g.mode === "explore" && g.floor.number >= 1 && CM.themeIndex(g.floor.number) === 7 && !CM.bellsRung(g)) { if (!nextCrack) nextCrack = now + 25000 + Math.random() * 30000; else if (now > nextCrack) { crackedFar(); nextCrack = now + 45000 + Math.random() * 45000; } } else nextCrack = 0;
    setTimeout(tick, 1000); };
  setTimeout(tick, 2000);
  // the endings: one bell, or the Last Page's peal
  { const qe0 = CM.Game.prototype.quietEnd; if (qe0) CM.Game.prototype.quietEnd = function (...a) { const peal = Boolean(this.ext && this.ext("claude").walking), out = qe0.apply(this, a); if (!this.replaying && !this.film) setTimeout(() => CM.ringBell(peal ? 3 : 1, 0.24, 3.4), 1800); return out; }; }
  // after: the town's hours, and the title
  let lastHour = null;
  const hourTick = () => { const g = CM.game; if (g && g.floor && g.floor.number === 0 && g.mode === "explore" && CM.bellsRung(g) && CM.hourOf) { const h = CM.hourOf(g); if (lastHour !== null && h !== lastHour && h >= 6 && h <= 21) CM.ringBell(1, 0.07, 3, 330); lastHour = h; } else lastHour = null; setTimeout(hourTick, 1500); };
  setTimeout(hourTick, 3000);
  { const ss0 = CM.UI.prototype.showSplash; if (ss0) CM.UI.prototype.showSplash = function (...a) { const out = ss0.apply(this, a); setTimeout(() => { if (CM.bellsRung(this.game)) CM.ringBell(1, 0.12, 3, 294); }, 2500); return out; }; }
  // a band's first phrase, on arrival
  const seen = new Set();
  const phrase = (b) => { if (!live() || !M.tune || !M.midi) return false; let T; try { T = M.tune(`depth${b}`); } catch (e) { return false; } if (!T || !T.melody) return false;
    const ctx = A.ctx, at = ctx.currentTime + 2.4, beat = 60 / Math.max(50, T.tempo || 80) * 0.75, notes = T.melody.filter((d) => d !== null && d !== undefined).slice(0, 5);
    notes.forEach((d, i) => { const hz = 440 * Math.pow(2, (M.midi(T, d, 1) - 69) / 12); M._osc("triangle", hz, at + i * beat, at + i * beat + beat * 1.6, 0.07, 2600, M.master); }); return true; };
  const bind = () => { const g = CM.game; if (!g || !g.on) return false; g.on("floor", (fl) => { if (!fl || !(fl.number >= 1) || fl.number > CM.BOTTOM || g.replaying || g.film || (g.autoOn && g.autoOn())) return; const b = CM.themeIndex(fl.number), key = `${g.seed}:${g.startedAt || ""}:${b}`; if (seen.has(key)) return; seen.add(key); phrase(b); }); return true; };
  if (!bind()) { const t = setInterval(() => { if (bind()) clearInterval(t); }, 300); }
}
