"use strict";
// Town music by the hour (v44.2, UPGRADE_PLAN_39.md): Caer Duin has tunes of its own now, by the clock - a flute over
// the rooftops in the morning, a busy lute and a tambourine through the middle of the day, the tavern's fiddle over a
// drone from dusk to late, and in the small hours only a few soft notes, far apart. Inside the Hanged Lantern it is
// always the fiddle. The tune changes as the hour turns (the old fades under the new).
{ const M = CM.music; if (M) {
  Object.assign(M.kinds, {
    town_morning: { scale: [0, 2, 4, 7, 9], root: 60, tempo: 72, rest: 0.35, voice: "pad", inst: "flute" },
    town_midday: { scale: [0, 2, 4, 5, 7, 9, 11], root: 57, tempo: 112, rest: 0.18, voice: "pluck", inst: "lute" },
    town_evening: { scale: [0, 2, 3, 5, 7, 9, 10], root: 55, tempo: 100, rest: 0.15, voice: "lead", inst: "fiddle" },
    town_night: { scale: [0, 2, 4, 7, 9], root: 52, tempo: 44, rest: 0.6, voice: "pad", inst: "hush" } });
  const hourKind = (g) => { const fl = g && g.floor; if (fl && fl.interior === "tavern") return "town_evening"; const h = CM.hourOf(g); return h >= 5 && h < 10 ? "town_morning" : h >= 10 && h < 17 ? "town_midday" : h >= 17 && h < 23 ? "town_evening" : "town_night"; };
  const inTown = (g) => { const fl = g && g.floor; return Boolean(fl && g.mode !== "title" && (fl.number === 0 || fl.special === "interior")); };
  CM.townTune = hourKind;
  const start0 = M.start; M.start = function (kind, ...a) { const g = CM.game; if (typeof kind === "string" && /^depth\d$/.test(kind) && g && g.mode === "explore" && inTown(g)) kind = hourKind(g); return start0.call(this, kind, ...a); };
  setInterval(() => { const g = CM.game; if (!g || !String(M.playing || "").startsWith("town_") || !inTown(g) || g.mode !== "explore") return; const k = hourKind(g); if (k !== M.playing) M.start(k); }, 4000);
  const ctx = () => CM.audio.ctx;
  const tone = (type, hz, at, dur, vol0, o = {}) => { const vol = vol0 * 2.2, c = ctx(), os = c.createOscillator(), g = c.createGain(), f = c.createBiquadFilter(); os.type = type; os.frequency.value = hz; f.type = "lowpass"; f.frequency.value = o.filter || 2600; const a = o.attack || 0.01;
    g.gain.setValueAtTime(0.0001, at); g.gain.exponentialRampToValueAtTime(vol, at + a); if (o.hold) g.gain.setValueAtTime(vol, at + a + o.hold); g.gain.exponentialRampToValueAtTime(0.0001, at + Math.max(a + 0.02, dur));
    if (o.vib) { const l = c.createOscillator(), lg = c.createGain(); l.frequency.value = o.vibRate || 5.5; lg.gain.value = hz * o.vib; l.connect(lg); lg.connect(os.frequency); l.start(at); l.stop(at + dur + 0.1); }
    os.connect(f); f.connect(g); g.connect(M.bus); os.start(at); os.stop(at + dur + 0.1); };
  let tamb = null; const jingle = (at, v) => { const c = ctx(); if (!tamb) { const n = Math.floor(c.sampleRate * 0.15), b = c.createBuffer(1, n, c.sampleRate), d = b.getChannelData(0); for (let i = 0; i < n; i++) d[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / n, 2) * (0.6 + 0.4 * Math.sin(i * 0.9)); tamb = b; }
    const s = c.createBufferSource(), f = c.createBiquadFilter(), g = c.createGain(); s.buffer = tamb; f.type = "highpass"; f.frequency.value = 5000; g.gain.value = v * 2; s.connect(f); f.connect(g); g.connect(M.bus); s.start(at); };
  const INST = {
    flute: (hz, at, d) => tone("sine", hz * 2, at, Math.max(0.4, d * 1.3), 0.11, { attack: 0.05, hold: d * 0.5, vib: 0.006, vibRate: 5 }),
    lute: (hz, at) => { tone("triangle", hz, at, 0.55, 0.16, { filter: 3000 }); tone("triangle", hz * 2, at, 0.2, 0.04, { filter: 3500 }); },
    fiddle: (hz, at, d) => tone("sawtooth", hz, at, Math.max(0.25, d * 1.05), 0.07, { attack: 0.04, hold: d * 0.6, filter: 2200, vib: 0.008, vibRate: 6 }),
    hush: (hz, at) => tone("sine", hz * 2, at, 1.8, 0.06, { attack: 0.08, filter: 1800 }) };
  const note0 = M._note; let n = 0;
  M._note = function (t, deg, at, len) { const k = t && this.kinds[t.kind]; if (!k || !k.inst || !this.bus || !ctx()) return note0.call(this, t, deg, at, len);
    n++; if (this.calm && k.inst !== "fiddle" && k.inst !== "hush" && n % 2 !== 0) return; INST[k.inst](this.hz(this.midi(t, deg, 1)), at, len); };
  const pad0 = M._pad; M._pad = function (t, chord, at, len) { const k = t && this.kinds[t.kind]; if (!k || !k.inst || !this.bus || !ctx()) return pad0.call(this, t, chord, at, len);
    const root = this.hz(this.midi(t, chord, 0));
    if (k.inst === "fiddle") { tone("sawtooth", root / 2, at, len, 0.035, { attack: 0.3, hold: len * 0.6, filter: 700 }); tone("sawtooth", root * 0.75, at, len, 0.02, { attack: 0.3, hold: len * 0.6, filter: 700 }); for (let i = 0; i < 4; i++) tone("triangle", root / 2, at + i * len / 4, 0.18, 0.08, { filter: 600 }); }
    else if (k.inst === "lute") { for (let i = 0; i < 8; i++) { jingle(at + i * len / 8 + (i % 2 ? len / 48 : 0), i % 2 ? 0.035 : 0.06); if (i % 2 === 0) tone("triangle", root / 2, at + i * len / 8, 0.25, 0.09, { filter: 900 }); } }
    else if (k.inst === "flute") { tone("triangle", root, at, len, 0.04, { attack: 0.4, hold: len * 0.5, filter: 900 }); tone("triangle", root * 1.5, at, len, 0.025, { attack: 0.5, hold: len * 0.5, filter: 900 }); }
    else tone("sine", root / 2, at, len, 0.05, { attack: 0.8, hold: len * 0.4, filter: 400 }); };
} }
