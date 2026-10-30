"use strict";
// Music, made as it plays: a tune for each depth of the dungeon (a mode and a root for its mood), a battle theme with
// drums, a warm tune for the camp, one for the title and one for the end. Each tune is written once, from a seed
// (CM.music.tune), as four bars of melody over four chords, played A A B A; the notes are oscillators scheduled a
// little ahead through a filter, an envelope and a touch of reverb. It shares the sounds' AudioContext (50-audio.js).
CM.music = {
  kinds: {
    title: { scale: [0, 2, 3, 5, 7, 9, 10], root: 50, tempo: 54, rest: 0.4, voice: "pad" },          // Dorian, slow
    depth0: { scale: [0, 2, 3, 5, 7, 9, 10], root: 50, tempo: 60, rest: 0.35, voice: "pad" },        // the Catacombs: Dorian
    depth1: { scale: [0, 1, 3, 5, 7, 8, 10], root: 48, tempo: 54, rest: 0.4, voice: "pad" },         // the Flooded Vaults: Phrygian
    depth2: { scale: [0, 2, 4, 5, 7, 9, 10], root: 52, tempo: 66, rest: 0.3, voice: "pluck" },       // the Dwarven Halls: Mixolydian
    depth3: { scale: [0, 2, 3, 5, 7, 8, 11], root: 47, tempo: 48, rest: 0.45, voice: "pad" },        // the Palace: harmonic minor
    depth4: { scale: [0, 1, 3, 5, 7, 8, 10], root: 45, tempo: 50, rest: 0.45, voice: "pad" },        // the Drowned Town: Phrygian, lower
    depth5: { scale: [0, 2, 3, 6, 7, 9, 10], root: 49, tempo: 58, rest: 0.4, voice: "pluck" },       // the Fungal Deep: Dorian with a sharp fourth
    depth6: { scale: [0, 2, 4, 6, 7, 9, 11], root: 54, tempo: 62, rest: 0.35, voice: "pad" },        // the Crystal Caverns: Lydian, high and clear
    depth7: { scale: [0, 1, 4, 5, 7, 8, 10], root: 44, tempo: 70, rest: 0.3, voice: "pluck" },       // the Foundry: Phrygian dominant, hammering
    depth8: { scale: [0, 2, 3, 5, 7, 8, 10], root: 43, tempo: 46, rest: 0.5, voice: "pad" },         // the Ossuary: Aeolian, slow as a procession
    depth9: { scale: [0, 1, 3, 4, 6, 8, 10], root: 41, tempo: 40, rest: 0.5, voice: "pad" },         // the Root: a whole-tone murk with a flat second
    battle: { scale: [0, 3, 5, 6, 7, 10], root: 45, tempo: 132, rest: 0.15, voice: "lead", drums: true },   // minor, with a flat fifth
    boss: { scale: [0, 1, 4, 5, 7, 8, 11], root: 43, tempo: 108, rest: 0.12, voice: "lead", drums: true },   // double harmonic, slower and heavier: a guardian, the Lich King
    camp: { scale: [0, 2, 4, 7, 9], root: 55, tempo: 76, rest: 0.3, voice: "pluck" },                // major pentatonic: a lute by the fire
    victory: { scale: [0, 2, 4, 5, 7, 9, 11], root: 55, tempo: 96, rest: 0.2, voice: "pluck" },      // major
    lament: { scale: [0, 2, 3, 5, 7, 8, 10], root: 45, tempo: 44, rest: 0.45, voice: "pad" },         // Aeolian, slow: the party fell
  },
  playing: null,
  depth: 0,                                        // how far into its band the party is (0..1): the tune gains a voice past the middle, and a fifth near the end
  danger: 0,                                       // the battle tune in layers: 0 drums and pad while the party is whole, 0.6 the lead joins under half, 1 the pad drops out when a hero has fallen
  shiftBy: 0,                                      // semitones the tune is shifted (a guardian's second form changes the key)
  enabled: true,
  volume: 0.5,
  master: null,
  reverb: null,
  timer: null,
  tunes: {},

  // the tune for a kind, always the same: chords (scale degrees, one each two bars... one each eight steps),
  // and a melody of 64 eighth-note steps (null for a rest), as A A B A
  tune(kind) {
    if (this.tunes[kind]) return this.tunes[kind];
    const k = this.kinds[kind], rnd = new CM.Random(CM.hashSeed("tune:" + kind)), n = k.scale.length;
    const chords = [0, rnd.pick([3, 4, 5]), rnd.pick([2, 3, 5, 6 % n]), rnd.pick([4, 3])];
    const phrase = (start) => {
      const out = [];
      let deg = start;
      for (let i = 0; i < 16; i++) {
        if (i > 0 && rnd.chance(k.rest)) { out.push(null); continue; }
        deg = CM.clamp(deg + rnd.int(-2, 2) + (rnd.chance(0.15) ? rnd.int(-4, 4) : 0), 0, n + 5);
        if (i % 8 === 0 && rnd.chance(0.6)) deg = chords[Math.floor((i % 16) / 8)] + (deg >= n ? n : 0);   // (land on the chord)
        out.push(deg);
      }
      return out;
    };
    const a = phrase(n), b = phrase(n + 2);
    const tune = { kind, chords, melody: [...a, ...a, ...b, ...a], tempo: k.tempo, scale: k.scale, root: k.root, voice: k.voice, drums: Boolean(k.drums) };
    this.tunes[kind] = tune;
    return tune;
  },

  midi(tune, degree, octave = 0) {
    if (this.shiftBy) return this.midi0(tune, degree, octave) + this.shiftBy;
    return this.midi0(tune, degree, octave);
  },
  midi0(tune, degree, octave = 0) {
    const n = tune.scale.length, d = ((degree % n) + n) % n, o = Math.floor(degree / n) + octave;
    return tune.root + tune.scale[d] + 12 * o;
  },
  hz: (m) => 440 * Math.pow(2, (m - 69) / 12),

  _ensure() {
    const a = CM.audio;
    if (!a.ctx) return false;
    if (!this.master) {
      this.master = a.ctx.createGain();
      this.master.gain.value = this.enabled ? this.volume : 0;
      this.master.connect(a.ctx.destination);
      // a little stone-hall reverb: an impulse of fading noise
      const rate = a.ctx.sampleRate, len = Math.floor(rate * 2.2), buf = a.ctx.createBuffer(2, len, rate), rnd = new CM.Random(3);
      for (let ch = 0; ch < 2; ch++) { const d = buf.getChannelData(ch); for (let i = 0; i < len; i++) d[i] = (rnd.next() * 2 - 1) * Math.pow(1 - i / len, 2.6) * 0.5; }
      this.reverb = a.ctx.createConvolver();
      this.reverb.buffer = buf;
      this.wet = a.ctx.createGain();
      this.wet.gain.value = 0.35;
      this.reverb.connect(this.wet);
      this.wet.connect(this.master);
    }
    return true;
  },

  setEnabled(on) { this.enabled = on; if (this.master) this.master.gain.setTargetAtTime(on ? this.volume : 0, CM.audio.ctx.currentTime, 0.2); },
  setVolume(v) { this.volume = CM.clamp(v, 0, 1); if (this.master && this.enabled) this.master.gain.setTargetAtTime(this.volume, CM.audio.ctx.currentTime, 0.1); },

  // play this kind of tune (fading the last one out); the same kind again does nothing
  start(kind) {
    if (this.playing === kind) return;
    this.want = kind;
    if (!this._ensure()) { this.playing = kind; return; }       // (the context comes with the first click; we'll start then)
    const ctx = CM.audio.ctx;
    if (this.bus) { const old = this.bus; old.gain.setTargetAtTime(0, ctx.currentTime, 0.4); setTimeout(() => { try { old.disconnect(); } catch (e) { /* gone */ } }, 2500); }
    this.bus = ctx.createGain();
    this.bus.gain.value = 0;
    this.bus.gain.setTargetAtTime(1, ctx.currentTime + 0.05, 0.6);
    this.bus.connect(this.master);
    this.bus.connect(this.reverb);
    this.playing = kind;
    this.tuneNow = this.tune(kind);
    this.step = 0;
    this.nextAt = ctx.currentTime + 0.1;
    if (this.timer) clearInterval(this.timer);
    this.timer = setInterval(() => this._schedule(), 100);
  },

  stop() {
    this.want = null;
    if (!this.playing) return;
    this.playing = null;
    if (this.timer) { clearInterval(this.timer); this.timer = null; }
    if (this.bus && CM.audio.ctx) { const old = this.bus; old.gain.setTargetAtTime(0, CM.audio.ctx.currentTime, 0.5); setTimeout(() => { try { old.disconnect(); } catch (e) { /* gone */ } }, 3000); this.bus = null; }
  },

  // called when the AudioContext arrives (the first click or key): start what was wanted
  resume() { if (this.want && (!this.timer || !this.bus)) { const w = this.want; this.playing = null; this.start(w); } },

  _schedule() {
    const ctx = CM.audio.ctx, t = this.tuneNow;
    if (!ctx || !t || !this.bus) return;
    const stepLen = 60 / t.tempo / 2;
    if (!this.enabled) { this.nextAt = Math.max(this.nextAt, ctx.currentTime + 0.1); return; }   // (off: nothing to play, nothing piles up)
    while (this.nextAt < ctx.currentTime + 1.5) {                        // (a second and a half ahead: a hidden tab's timers come once a second)
      const i = this.step % 64, chord = t.chords[Math.floor((i % 32) / 8)];
      if (i % 8 === 0 && !(t.drums && this.danger >= 1)) this._pad(t, chord, this.nextAt, stepLen * 8);
      if (t.drums) this._drums(i, this.nextAt, stepLen);
      const deg = t.melody[i];
      if (deg !== null && deg !== undefined && !(t.drums && this.danger < 0.6)) this._note(t, deg, this.nextAt, stepLen * (t.melody[(i + 1) % 64] === null ? 2 : 1));
      this.nextAt += stepLen;
      this.step += 1;
    }
  },

  _osc(type, hz, at, until, gain, filterHz, dest) {
    const ctx = CM.audio.ctx, o = ctx.createOscillator(), g = ctx.createGain(), f = ctx.createBiquadFilter();
    o.type = type; o.frequency.value = hz;
    f.type = "lowpass"; f.frequency.value = filterHz;
    g.gain.value = 0;
    g.gain.setTargetAtTime(gain, at, 0.02);
    g.gain.setTargetAtTime(0, until, 0.08);
    o.connect(f); f.connect(g); g.connect(dest || this.bus);
    o.start(at); o.stop(until + 0.6);
    return o;
  },

  // a leitmotif: the bell (three tolls, falling), the queen's song (five notes, minor, unsteady), the Root's one note
  motif(name) {
    if (!this.enabled || !this._ensure()) return false;
    const ctx = CM.audio.ctx, at = ctx.currentTime + 0.05, dest = this.master;
    if (name === "bell") { [[440, 0], [330, 1.1], [220, 2.3]].forEach(([hz, dt]) => { this._osc("sine", hz, at + dt, at + dt + 2.2, 0.16, 3000, dest); this._osc("sine", hz * 2.76, at + dt, at + dt + 0.5, 0.05, 6000, dest); }); }
    else if (name === "queen") { [0, 3, 2, 3, -2].forEach((semi, i) => { const hz = 392 * Math.pow(2, semi / 12) * (1 + (i % 2 ? 0.004 : -0.003)); this._osc("triangle", hz, at + i * 0.42, at + i * 0.42 + 0.5, 0.11, 2200, dest); }); }
    else if (name === "root") { this._osc("sine", 41.2, at, at + 3.2, 0.3, 300, dest); this._osc("triangle", 41.2 * 1.5, at + 0.4, at + 3.0, 0.05, 400, dest); }
    else return false;
    return true;
  },
  setDepth(k) { this.depth = CM.clamp(k || 0, 0, 1); },
  setDanger(k) { this.danger = CM.clamp(k || 0, 0, 1); },
  shift(semitones) { this.shiftBy = semitones || 0; },
  _note(t, deg, at, len) {
    const hz = this.hz(this.midi(t, deg, 1));
    if (this.depth >= 0.5 && !t.drums && this.bus) this._osc("sine", hz * 2, at + 0.02, at + len * 0.7, 0.03 + 0.03 * this.depth, 2400);   // deeper in: an echo an octave up
    if (this.depth >= 0.9 && !t.drums && this.bus) this._osc("triangle", this.hz(this.midi(t, deg + 4, 0)), at, at + len * 0.9, 0.04, 1200);   // at the band's end: a fifth under it
    if (t.voice === "pluck") {                                           // a lute: bright, quick to fade
      const ctx = CM.audio.ctx, o = ctx.createOscillator(), g = ctx.createGain(), f = ctx.createBiquadFilter();
      o.type = "triangle"; o.frequency.value = hz; f.type = "lowpass"; f.frequency.value = 2400;
      g.gain.setValueAtTime(0.0001, at); g.gain.exponentialRampToValueAtTime(0.22, at + 0.01); g.gain.exponentialRampToValueAtTime(0.0001, at + Math.min(0.9, len * 1.6));
      o.connect(f); f.connect(g); g.connect(this.bus); o.start(at); o.stop(at + 1.2);
    } else if (t.voice === "lead") {
      this._osc("sawtooth", hz, at, at + len * 0.9, 0.09, 1600);
      this._osc("square", hz / 2, at, at + len * 0.9, 0.04, 800);
    } else {
      this._osc("sine", hz, at, at + len * 0.95, 0.16, 2000);
      this._osc("triangle", hz * 1.002, at, at + len * 0.95, 0.06, 1200);
    }
  },

  _pad(t, chord, at, len) {                                             // root, third, fifth of the chord, held
    const n = t.scale.length, degs = [chord, chord + 2, chord + 4];
    for (const d of degs) {
      const hz = this.hz(this.midi(t, d, 0));
      this._osc("triangle", hz, at, at + len, t.voice === "lead" ? 0.035 : 0.055, 700);
      this._osc("triangle", hz * 0.997, at, at + len, 0.03, 500);
    }
    this._osc("sine", this.hz(this.midi(t, chord, -1)), at, at + len, 0.12, 300);   // the bass
    void n;
  },

  _drums(i, at, stepLen) {
    const ctx = CM.audio.ctx;
    const burst = (len, hz, gain, type = "lowpass") => {
      const n = Math.floor(ctx.sampleRate * len), buf = ctx.createBuffer(1, n, ctx.sampleRate), d = buf.getChannelData(0);
      for (let k = 0; k < n; k++) d[k] = (Math.random() * 2 - 1) * (1 - k / n);
      const s = ctx.createBufferSource(), f = ctx.createBiquadFilter(), g = ctx.createGain();
      s.buffer = buf; f.type = type; f.frequency.value = hz; g.gain.value = gain;
      s.connect(f); f.connect(g); g.connect(this.bus); s.start(at);
    };
    if (i % 4 === 0) burst(0.12, 160, 0.9);                               // the drum
    if (i % 8 === 4) burst(0.1, 1800, 0.35, "bandpass");                   // the snare
    if (i % 2 === 1) burst(0.03, 6000, 0.12, "highpass");                  // the hat
    void stepLen;
  },
};
