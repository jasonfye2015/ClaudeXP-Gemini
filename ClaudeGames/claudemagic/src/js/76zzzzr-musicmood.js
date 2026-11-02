"use strict";
// Music that follows (v28.1, UPGRADE_PLAN_23.md): the depth's tune knows what is about. As monsters come near, a layer
// of tension rises in it - a low pulse on the chord's root, a heartbeat under it - and falls away as they are left
// behind; in a fight the tune's own danger takes over (as before). In safe places - the town by day, a house's room,
// a camp - the tune drops to its quiet self: softer, and most of the melody left out, the pad carrying it.
{ const M = CM.music; if (!M) { /* (no music: nothing to follow) */ } else {
  M.tension = 0; M.tensionWant = 0; M.calm = false;
  M.setTension = (k) => { M.tensionWant = CM.clamp(k || 0, 0, 1); };
  M.setCalm = (on) => { if (Boolean(on) === M.calm) return; M.calm = Boolean(on); const ctx = CM.audio.ctx; if (M.bus && ctx) M.bus.gain.setTargetAtTime(M.calm ? 0.55 : 1, ctx.currentTime, 1.2); };
  { const start0 = M.start; M.start = function (...a) { const out = start0.apply(this, a); const ctx = CM.audio.ctx; if (M.calm && M.bus && ctx) M.bus.gain.setTargetAtTime(0.55, ctx.currentTime + 0.1, 1.2); return out; }; }   // (a new tune keeps the calm)
  // the calm: three notes in four of the melody left out
  const note0 = M._note; let n = 0;
  M._note = function (t, deg, at, len) { n++; if (M.calm && !t.drums && n % 4 !== 0) return; return note0.call(this, t, deg, at, len); };
  // the tension: its own beat, a second ahead, on the tune's tempo
  let nextAt = 0, beat = 0;
  const layer = () => { const ctx = CM.audio.ctx, t = M.tuneNow; M.tension += (M.tensionWant - M.tension) * 0.08; if (!ctx || !t || !M.bus || !M.enabled || t.drums || M.tension < 0.04) { nextAt = 0; return; }
    const step = 60 / t.tempo; if (nextAt < ctx.currentTime) nextAt = ctx.currentTime + 0.05;
    while (nextAt < ctx.currentTime + 1) { const k = M.tension, chord = t.chords[Math.floor((M.step % 32) / 8)] || 0, root = M.hz(M.midi(t, chord, -1)) / 2;
      M._osc("sawtooth", root, nextAt, nextAt + step * 0.45, 0.05 * k, 260 + 500 * k, M.bus);                  // (the pulse on the root, brighter the nearer)
      if (beat % 2 === 0 && k > 0.35) { M._osc("sine", 55, nextAt, nextAt + 0.12, 0.22 * k, 200, M.bus); M._osc("sine", 50, nextAt + 0.18, nextAt + 0.3, 0.16 * k, 200, M.bus); }   // (a heartbeat)
      if (k > 0.7 && beat % 4 === 3) M._osc("triangle", root * 4 * 1.06, nextAt, nextAt + step * 0.9, 0.025 * k, 1800, M.bus);   // (close: a sharp note, a half step off)
      nextAt += step; beat++; } };
  setInterval(layer, 150);
  // what's about: the nearest monsters awake, and whether this is a safe place
  setInterval(() => { const g = CM.game; if (!g || !g.floor) return; const fl = g.floor, n = fl.number;
    M.setCalm(g.mode === "camp" || fl.special === "interior" || (n === 0 && !CM.isNight(g)));
    if (g.mode !== "explore" || !CM.isDeep(n)) { M.setTension(0); return; }
    const [px, py] = fl.pos; let bd = 99; for (const [k, t] of Object.entries(fl.things)) { if (!(t.type === "monsters" || t.type === "boss" || t.type === "guardian") || t.asleep) continue; const [x, y] = k.split(",").map(Number); bd = Math.min(bd, Math.abs(x - px) + Math.abs(y - py)); }
    M.setTension(bd <= 7 ? (7 - bd) / 6 : 0); }, 300);
} }
