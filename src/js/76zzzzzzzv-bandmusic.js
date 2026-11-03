"use strict";
// A theme for every band in its own instruments (v44.0, UPGRADE_PLAN_39.md): each band's tune (55-music.js depth0-9)
// is played on its own consort now instead of the shared pad and lute - the Catacombs by a low choir with a bell at
// each change of chord; the Flooded Vaults on a glass harmonica, water dripping; the Dwarven Halls on a hammered
// dulcimer over a horn, an anvil keeping time; the Palace on a harpsichord over an organ; the Drowned Town on a music
// box out of tune, a bell far off; the Fungal Deep on a marimba with a hand drum; the Crystal Caverns on glass bells;
// the Foundry in brass with the anvils; the Ossuary on a bone xylophone over the choir; the Root in a throat's drone
// and a heartbeat. (The calm of 76zzzzr-musicmood.js holds: in safe places three notes in four are left out.)
{ const M = CM.music; if (M) {
  const ctx = () => CM.audio.ctx;
  const tone = (type, hz, at, dur, vol, o = {}) => { const c = ctx(), os = c.createOscillator(), g = c.createGain(), f = c.createBiquadFilter(); os.type = type; os.frequency.value = hz; if (o.detune) os.detune.value = o.detune;
    f.type = o.ftype || "lowpass"; f.frequency.value = o.filter || 2400; if (o.q) f.Q.value = o.q; const a = o.attack || 0.01;
    g.gain.setValueAtTime(0.0001, at); g.gain.exponentialRampToValueAtTime(vol, at + a); if (o.hold) g.gain.setValueAtTime(vol, at + a + o.hold); g.gain.exponentialRampToValueAtTime(0.0001, at + Math.max(a + 0.02, dur));
    if (o.vib) { const l = c.createOscillator(), lg = c.createGain(); l.frequency.value = o.vibRate || 5; lg.gain.value = hz * o.vib; l.connect(lg); lg.connect(os.frequency); l.start(at); l.stop(at + dur + 0.1); }
    os.connect(f); f.connect(g); g.connect(o.dest || M.bus); os.start(at); os.stop(at + dur + 0.1); };
  let noise = null; const hit = (at, hz, vol, len, type = "bandpass", q = 1) => { const c = ctx(); if (!noise) { const n = c.sampleRate, b = c.createBuffer(1, n, n), d = b.getChannelData(0); for (let i = 0; i < n; i++) d[i] = Math.random() * 2 - 1; noise = b; }
    const s = c.createBufferSource(), f = c.createBiquadFilter(), g = c.createGain(); s.buffer = noise; f.type = type; f.frequency.value = hz; f.Q.value = q; g.gain.setValueAtTime(vol, at); g.gain.exponentialRampToValueAtTime(0.0001, at + len); s.connect(f); f.connect(g); g.connect(M.bus); s.start(at); s.stop(at + len + 0.05); };
  const choir = (hz, at, d, v = 0.06) => { tone("sawtooth", hz, at, d, v, { attack: 0.12, hold: d * 0.5, filter: 620, ftype: "bandpass", q: 4, vib: 0.006 }); tone("sawtooth", hz * 1.003, at, d, v * 0.6, { attack: 0.15, hold: d * 0.5, filter: 1050, ftype: "bandpass", q: 6 }); };
  const bell = (hz, at, v = 0.06) => { tone("sine", hz, at, 2.4, v); tone("sine", hz * 2.76, at, 0.8, v * 0.4); tone("sine", hz * 5.4, at, 0.3, v * 0.15); };
  const NOTE = [
    (hz, at, d) => choir(hz, at, Math.max(0.5, d * 1.4)),
    (hz, at, d) => tone("sine", hz * 2, at, Math.max(0.8, d * 2), 0.09, { attack: 0.06, vib: 0.004, vibRate: 5.5, filter: 3000 }),
    (hz, at) => { tone("triangle", hz, at, 0.6, 0.13, { filter: 3800 }); tone("square", hz * 2, at, 0.18, 0.025, { filter: 3000 }); },
    (hz, at) => { tone("sawtooth", hz, at, 0.55, 0.06, { filter: 3200 }); tone("square", hz * 2, at, 0.25, 0.02, { filter: 4000 }); },
    (hz, at) => { tone("sine", hz * 2, at, 1.3, 0.09, { detune: (Math.random() - 0.5) * 30 }); tone("sine", hz * 4, at, 0.4, 0.02); },
    (hz, at) => { tone("sine", hz, at, 0.5, 0.15, { filter: 2000 }); tone("sine", hz * 4, at, 0.12, 0.04); },
    (hz, at) => bell(hz * 2, at, 0.05),
    (hz, at, d) => tone("sawtooth", hz, at, Math.max(0.4, d * 1.1), 0.06, { attack: 0.06, filter: 1300, hold: d * 0.4 }),
    (hz, at) => { tone("triangle", hz * 2, at, 0.14, 0.12, { filter: 5000 }); hit(at, 3500, 0.05, 0.03); },
    (hz, at, d) => tone("sawtooth", hz / 2, at, Math.max(0.6, d * 1.6), 0.07, { attack: 0.1, filter: 320, ftype: "bandpass", q: 3, vib: 0.01, vibRate: 3 }) ];
  // each chord's change (eight steps): the band's accent, and its beat through the bar
  const BAR = [
    (t, at, len, root) => bell(root * 2, at, 0.05),
    (t, at, len) => { for (let i = 0; i < 3; i++) if (Math.random() < 0.6) tone("sine", 1400 + Math.random() * 900, at + Math.random() * len, 0.25, 0.04, { attack: 0.003 }); },
    (t, at, len, root) => { tone("sawtooth", root, at, len, 0.035, { attack: 0.3, filter: 600, hold: len * 0.5 }); for (let i = 0; i < 4; i++) { hit(at + i * len / 4, 2600, 0.12, 0.09, "bandpass", 8); tone("sine", 1850, at + i * len / 4, 0.3, 0.025); } },
    (t, at, len, root) => tone("square", root / 2, at, len, 0.03, { attack: 0.2, filter: 500, hold: len * 0.6 }),
    (t, at, len, root) => { if (Math.random() < 0.5) bell(root * 1.5, at + len * 0.5, 0.03); },
    (t, at, len) => { for (let i = 0; i < 4; i++) { hit(at + i * len / 4, 180, i % 2 ? 0.15 : 0.25, 0.12, "lowpass"); if (i % 2) hit(at + i * len / 4 + len / 8, 800, 0.08, 0.06); } },
    (t, at, len, root) => { for (let i = 0; i < 2; i++) tone("sine", root * 4 * (i ? 1.5 : 1), at + i * len / 2, 1.6, 0.025); },
    (t, at, len) => { for (let i = 0; i < 4; i++) { hit(at + i * len / 4, 2200, 0.16, 0.12, "bandpass", 10); tone("sine", 1620, at + i * len / 4, 0.4, 0.03); } hit(at, 90, 0.3, 0.25, "lowpass"); },
    (t, at, len, root) => choir(root, at, len, 0.035),
    (t, at, len) => { for (let i = 0; i < 2; i++) { const b = at + i * len / 2; tone("sine", 55, b, 0.14, 0.24, { filter: 200 }); tone("sine", 50, b + 0.2, 0.16, 0.17, { filter: 200 }); } } ];
  const bandOf = (t) => (t && /^depth\d$/.test(t.kind) ? Number(t.kind.slice(5)) : -1);
  CM.BAND_MUSIC = { NOTE, BAR, bandOf };
  let n = 0; const note0 = M._note;
  M._note = function (t, deg, at, len) { const b = bandOf(t); if (b < 0 || !this.bus || !ctx()) return note0.call(this, t, deg, at, len);
    n++; if (this.calm && n % 4 !== 0) return; const hz = this.hz(this.midi(t, deg, 1)); NOTE[b](hz, at, len);
    if (this.depth >= 0.5) tone("sine", hz * 2, at + 0.02, len * 0.7, 0.025 + 0.025 * this.depth, { filter: 2400 }); };
  const pad0 = M._pad;
  M._pad = function (t, chord, at, len) { const out = pad0.call(this, t, chord, at, len), b = bandOf(t); if (b >= 0 && this.bus && ctx()) try { BAR[b](t, at, len, this.hz(this.midi(t, chord, 0))); } catch (e) { /* (quiet) */ } return out; };
} }
