"use strict";
// Doors, locks, lids, levers and traps (v45.1, UPGRADE_PLAN_40.md): each has its own made sound now, laid over the old
// one - a door's creak as it swings and its latch; a key turning (three clicks) and a bolt drawn; a chest's lid and its
// hinge; a lever's ratchet and clunk; a portcullis's chain running up; a slam; stone grinding; a trap's spring and
// snap. The big ones (a slam, the grinding, the chain, a trap, a toll) echo, longer in the great halls (the Dwarven
// Halls, the Palace, the Foundry, the Joker's) and shorter in tight places (caves, the houses).
{ const live = () => { const A = CM.audio; return A && A.ctx && A.enabled && A.master; };
  let noise = null, echo = null, echoFor = null;
  const N = (c) => { if (!noise) { const n = c.sampleRate, b = c.createBuffer(1, n, n), d = b.getChannelData(0); for (let i = 0; i < n; i++) d[i] = Math.random() * 2 - 1; noise = b; } return noise; };
  const roomOf = () => { const fl = CM.game && CM.game.floor; if (!fl) return 0.5; if (fl.special === "interior" || fl.special === "cave") return 0.25; if (CM.isJokerFloor && CM.isJokerFloor(fl.number)) return 0.9; if (fl.number < 1) return 0.35; return [0.6, 0.55, 0.9, 0.9, 0.6, 0.45, 0.75, 0.85, 0.7, 0.5][CM.themeIndex(fl.number)] || 0.6; };
  const echoBus = (c) => { const A = CM.audio, k = roomOf(); if (echo && echoFor === k && echo.ctx === c) return echo.input;
    const input = c.createGain(), d = c.createDelay(1.5), fb = c.createGain(), lp = c.createBiquadFilter(), wet = c.createGain(); d.delayTime.value = 0.08 + k * 0.22; fb.gain.value = 0.25 + k * 0.3; lp.type = "lowpass"; lp.frequency.value = 2200 - k * 900; wet.gain.value = 0.5;
    input.connect(d); d.connect(lp); lp.connect(fb); fb.connect(d); lp.connect(wet); wet.connect(A.master); echo = { input, ctx: c }; echoFor = k; return input; };
  const sine = (c, d, hz, at, dur, vol, type = "sine", to) => { const o = c.createOscillator(), g = c.createGain(); o.type = type; o.frequency.setValueAtTime(hz, at); if (to) o.frequency.exponentialRampToValueAtTime(to, at + dur); g.gain.setValueAtTime(vol, at); g.gain.exponentialRampToValueAtTime(0.0001, at + dur); o.connect(g); g.connect(d); o.start(at); o.stop(at + dur + 0.05); };
  const burst = (c, d, at, dur, vol, hz, type = "bandpass", q = 1, to) => { const s = c.createBufferSource(), f = c.createBiquadFilter(), g = c.createGain(); s.buffer = N(c); f.type = type; f.frequency.setValueAtTime(hz, at); if (to) f.frequency.exponentialRampToValueAtTime(to, at + dur); f.Q.value = q;
    g.gain.setValueAtTime(vol, at); g.gain.exponentialRampToValueAtTime(0.0001, at + dur); s.connect(f); f.connect(g); g.connect(d); s.start(at, Math.random() * 0.5); s.stop(at + dur + 0.05); };
  const creak = (c, d, at, dur, vol, hz = 180) => { const o = c.createOscillator(), f = c.createBiquadFilter(), g = c.createGain(), l = c.createOscillator(), lg = c.createGain(); o.type = "sawtooth"; o.frequency.setValueAtTime(hz, at); o.frequency.linearRampToValueAtTime(hz * 1.6, at + dur * 0.6); o.frequency.linearRampToValueAtTime(hz * 1.2, at + dur);
    l.frequency.value = 23; lg.gain.value = hz * 0.12; l.connect(lg); lg.connect(o.frequency); f.type = "bandpass"; f.frequency.value = 900; f.Q.value = 4; g.gain.setValueAtTime(0.0001, at); g.gain.exponentialRampToValueAtTime(vol, at + 0.05); g.gain.setValueAtTime(vol, at + dur * 0.7); g.gain.exponentialRampToValueAtTime(0.0001, at + dur);
    o.connect(f); f.connect(g); g.connect(d); o.start(at); o.stop(at + dur + 0.05); l.start(at); l.stop(at + dur + 0.05); };
  const click = (c, d, at, vol, hz = 3200) => burst(c, d, at, 0.025, vol, hz, "bandpass", 6);
  const FOLEY = {
    door: (c, d, at) => { creak(c, d, at, 0.55, 0.07, 160 + Math.random() * 60); click(c, d, at, 0.12, 2400); },
    hinge: (c, d, at) => creak(c, d, at, 0.4, 0.06, 200 + Math.random() * 60),
    unlock: (c, d, at) => { for (let i = 0; i < 3; i++) click(c, d, at + i * 0.09, 0.14, 2800 + i * 300); burst(c, d, at + 0.32, 0.18, 0.12, 1200, "bandpass", 3, 600); sine(c, d, 420, at + 0.48, 0.12, 0.06, "triangle"); },
    chest: (c, d, at) => { creak(c, d, at, 0.35, 0.05, 240); burst(c, d, at + 0.32, 0.12, 0.18, 300, "lowpass"); click(c, d, at, 0.1, 2000); },
    lever: (c, d, at) => { for (let i = 0; i < 4; i++) click(c, d, at + i * 0.045, 0.1, 1800); burst(c, d, at + 0.2, 0.2, 0.3, 180, "lowpass"); sine(c, d, 110, at + 0.2, 0.25, 0.15); },
    chain: (c, d, at, e) => { for (let i = 0; i < 18; i++) click(c, i % 3 ? d : e, at + i * 0.033 + Math.random() * 0.01, 0.08 + Math.random() * 0.05, 2500 + Math.random() * 2500); burst(c, e, at + 0.62, 0.35, 0.3, 140, "lowpass"); },
    slam: (c, d, at, e) => { burst(c, d, at, 0.3, 0.45, 160, "lowpass"); sine(c, d, 70, at, 0.35, 0.3); burst(c, e, at, 0.4, 0.3, 300, "lowpass"); },
    grind: (c, d, at, e) => { burst(c, d, at, 0.9, 0.25, 260, "bandpass", 2, 140); burst(c, e, at, 1.0, 0.2, 200, "lowpass"); sine(c, e, 48, at, 0.9, 0.12, "sawtooth"); },
    trap: (c, d, at, e) => { sine(c, d, 900, at, 0.15, 0.08, "triangle", 300); click(c, d, at + 0.05, 0.2, 4000); burst(c, e, at + 0.08, 0.2, 0.3, 700, "bandpass", 2); },
    toll: (c, d, at, e) => sine(c, e, 220, at, 1.8, 0.05),
  };
  CM.FOLEY = FOLEY;
  const prep = () => { const A = CM.audio; if (!A || !A.play || A.foleyWrapped) return false; const p0 = A.play;
    A.play = function (name, volume = 1, pan = 0, rate = 1) { const out = p0.call(this, name, volume, pan, rate); const f = FOLEY[name]; if (f && live()) try { const c = this.ctx, g = c.createGain(); g.gain.value = Math.min(1, volume) * 0.9; g.connect(this.master); f(c, g, c.currentTime + 0.005, echoBus(c)); } catch (e) { /* (quiet) */ } return out; };
    A.foleyWrapped = true; return true; };
  const t = typeof self !== "undefined" && self.CM_WORKER ? null : setInterval(() => { if (prep()) clearInterval(t); }, 300);
}
