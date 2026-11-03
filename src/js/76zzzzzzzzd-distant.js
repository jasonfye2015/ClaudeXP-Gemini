"use strict";
// Distant sounds (v45.3, UPGRADE_PLAN_40.md): below ground the dungeon is heard from beyond the walls - nothing near, just
// the place - every ten seconds or so, from a side of its own, muffled and echoing: water dripping into pools, a roar
// far off, stone grinding somewhere, and each band's own - the Flooded Vaults dripping more, hammers far away in the
// Dwarven Halls and the Foundry, the Crystal Caverns chiming, the Ossuary's bones clattering, the Root groaning deep
// down. (The near monsters are heard as before, 76zzzzq-sound3d.js.)
{ const live = () => { const A = CM.audio; return A && A.ctx && A.enabled && A.master; };
  let noise = null, bus = null; const N = (c) => { if (!noise) { const n = c.sampleRate, b = c.createBuffer(1, n, n), d = b.getChannelData(0); for (let i = 0; i < n; i++) d[i] = Math.random() * 2 - 1; noise = b; } return noise; };
  const far = (c, pan) => { const A = CM.audio; if (!bus || bus.ctx !== c) { const lp = c.createBiquadFilter(), d = c.createDelay(2), fb = c.createGain(), wet = c.createGain(), dry = c.createGain(); lp.type = "lowpass"; lp.frequency.value = 1600; d.delayTime.value = 0.33; fb.gain.value = 0.45; wet.gain.value = 0.6; dry.gain.value = 0.7;
      lp.connect(dry); dry.connect(A.master); lp.connect(d); d.connect(fb); fb.connect(d); d.connect(wet); wet.connect(A.master); bus = { ctx: c, input: lp }; }
    const p = c.createStereoPanner ? c.createStereoPanner() : null; if (!p) return bus.input; p.pan.value = pan; p.connect(bus.input); return p; };
  const sine = (c, d, hz, at, dur, vol, type = "sine", to) => { const o = c.createOscillator(), g = c.createGain(); o.type = type; o.frequency.setValueAtTime(hz, at); if (to) o.frequency.exponentialRampToValueAtTime(to, at + dur); g.gain.setValueAtTime(0.0001, at); g.gain.exponentialRampToValueAtTime(vol, at + Math.min(0.05, dur / 4)); g.gain.exponentialRampToValueAtTime(0.0001, at + dur); o.connect(g); g.connect(d); o.start(at); o.stop(at + dur + 0.05); };
  const hiss = (c, d, at, dur, vol, hz, to, q = 1) => { const s = c.createBufferSource(), f = c.createBiquadFilter(), g = c.createGain(); s.buffer = N(c); s.loop = true; f.type = "bandpass"; f.frequency.setValueAtTime(hz, at); if (to) f.frequency.exponentialRampToValueAtTime(to, at + dur); f.Q.value = q;
    g.gain.setValueAtTime(0.0001, at); g.gain.exponentialRampToValueAtTime(vol, at + dur * 0.3); g.gain.exponentialRampToValueAtTime(0.0001, at + dur); s.connect(f); f.connect(g); g.connect(d); s.start(at); s.stop(at + dur + 0.05); };
  const SOUND = {
    drip: (c, d, at) => { for (let i = 0; i < 1 + Math.floor(Math.random() * 3); i++) sine(c, d, 900 + Math.random() * 900, at + i * (0.6 + Math.random()), 0.12, 0.09, "sine", 450); },
    roar: (c, d, at) => { sine(c, d, 70 + Math.random() * 30, at, 1.6, 0.12, "sawtooth", 45); hiss(c, d, at, 1.4, 0.06, 300, 150, 2); },
    grind: (c, d, at) => { hiss(c, d, at, 2.2, 0.07, 180, 120, 3); sine(c, d, 42, at, 2.2, 0.06, "sawtooth"); },
    hammer: (c, d, at) => { for (let i = 0; i < 3; i++) { sine(c, d, 1500 + i * 30, at + i * 0.55, 0.5, 0.05); hiss(c, d, at + i * 0.55, 0.08, 0.08, 2500, null, 6); } },
    chime: (c, d, at) => { for (let i = 0; i < 4; i++) sine(c, d, [1760, 2093, 2349, 2637][Math.floor(Math.random() * 4)], at + i * 0.18 + Math.random() * 0.1, 1.5, 0.03); },
    bones: (c, d, at) => { for (let i = 0; i < 8; i++) hiss(c, d, at + i * 0.06 + Math.random() * 0.05, 0.05, 0.08, 2200 + Math.random() * 1200, null, 5); },
    groan: (c, d, at) => { sine(c, d, 38, at, 3, 0.14, "triangle", 30); sine(c, d, 57, at + 0.4, 2.4, 0.05, "sine", 44); } };
  const MIX = [["drip", "roar", "grind", "bones"], ["drip", "drip", "drip", "roar"], ["hammer", "grind", "drip", "roar"], ["roar", "grind", "bones", "drip"], ["drip", "drip", "roar", "grind"],
    ["drip", "roar", "groan", "drip"], ["chime", "chime", "drip", "grind"], ["hammer", "hammer", "grind", "roar"], ["bones", "bones", "roar", "drip"], ["groan", "groan", "roar", "grind"]];
  CM.DISTANT = SOUND;
  let next = 0;
  setInterval(() => { const g = CM.game, fl = g && g.floor, now = performance.now(); if (!fl || !live() || g.mode !== "explore" || !(fl.number >= 1) || fl.number % 1 !== 0 || fl.special === "vault" || now < next) return; next = now + 7000 + Math.random() * 9000;
    const list = MIX[CM.themeIndex(fl.number)] || MIX[0], kind = list[Math.floor(Math.random() * list.length)], c = CM.audio.ctx; try { SOUND[kind](c, far(c, (Math.random() - 0.5) * 1.6), c.currentTime + 0.05); } catch (e) { /* (quiet) */ } }, 1000);
}
