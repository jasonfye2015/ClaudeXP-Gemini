"use strict";
// The sounds, made in code with Web Audio - the same recipes the old game cooked into .wav files: square and sine
// tones that fade, smoothed noise, and an eight-second dungeon (a low drone, a far rumble, water dripping) that loops.
// Browsers won't play a sound before the first click or key, so unlock() is called on the first of either.
CM.audio = {
  ctx: null,
  buffers: {},
  enabled: true,
  volume: 0.6,
  ambientOn: false,
  ambientNode: null,
  ambientGain: null,

  unlock() {
    if (!this.ctx) {
      try { this.ctx = new (window.AudioContext || window.webkitAudioContext)(); } catch (e) { return false; }
      this.master = this.ctx.createGain();
      this.master.gain.value = this.volume;
      this.master.connect(this.ctx.destination);
      this._cook();
    }
    if (this.ctx.state === "suspended") this.ctx.resume();
    if (this.ambientOn && !this.ambientNode) this._startAmbient();
    return true;
  },

  setEnabled(on) {
    this.enabled = on;
    if (this.master) this.master.gain.value = on ? this.volume : 0;
  },

  setVolume(v) {
    this.volume = CM.clamp(v, 0, 1);
    if (this.master && this.enabled) this.master.gain.value = this.volume;
  },

  _tones(notes, kind = "square", vol = 0.15) {
    const rate = this.ctx.sampleRate, out = [];
    for (const [freq, length] of notes) {
      const n = Math.floor(rate * length);
      for (let i = 0; i < n; i++) {
        const t = i / rate, fade = Math.pow(1 - i / n, 1.5);
        const v = kind === "sine" ? Math.sin(2 * Math.PI * freq * t) : ((t * freq) % 1 < 0.5 ? 1 : -1);
        out.push(v * vol * fade);
      }
    }
    return out;
  },

  _noise(length, vol, smooth, seed = 1) {
    const rate = this.ctx.sampleRate, rnd = new CM.Random(seed), out = [], n = Math.floor(rate * length);
    let last = 0;
    for (let i = 0; i < n; i++) {
      last += (rnd.next() * 2 - 1 - last) * smooth;
      out.push(last * vol * (1 - i / n));
    }
    return out;
  },

  _buffer(samples) {
    const b = this.ctx.createBuffer(1, samples.length, this.ctx.sampleRate);
    b.getChannelData(0).set(samples);
    return b;
  },

  _cook() {
    const T = (notes, kind, vol) => this._tones(notes, kind, vol);
    const recipes = {
      step: () => this._noise(0.09, 0.28, 0.08, 3),
      bump: () => T([[70, 0.12]], "square", 0.2),
      chest: () => T([[392, 0.07], [523, 0.07], [659, 0.12]]),
      hit: () => this._noise(0.12, 0.42, 0.5, 5),
      hurt: () => T([[180, 0.06], [120, 0.1]], "square", 0.18),
      spell: () => T(Array.from({ length: 15 }, (_, i) => [400 + i * 80, 0.025]), "sine", 0.2),
      heal: () => T([[523, 0.07], [659, 0.07], [784, 0.07], [1047, 0.14]], "sine", 0.18),
      coin: () => T([[1319, 0.05], [1760, 0.12]]),
      stairs: () => T([[392, 0.1], [330, 0.1], [262, 0.1], [196, 0.2]], "sine", 0.18),
      level: () => T([[523, 0.09], [659, 0.09], [784, 0.09], [1047, 0.09], [784, 0.09], [1047, 0.25]]),
      death: () => T([[330, 0.2], [262, 0.2], [196, 0.25], [131, 0.5]], "sine", 0.2),
      victory: () => T([[523, 0.12], [523, 0.12], [523, 0.12], [659, 0.3], [587, 0.15], [784, 0.5]]),
      monster: () => T([[110, 0.15], [98, 0.25]], "square", 0.18),
    };
    for (const [name, make] of Object.entries(recipes)) this.buffers[name] = this._buffer(make());
    // the dungeon itself
    const rate = this.ctx.sampleRate, secs = 8, n = rate * secs, rnd = new CM.Random(11);
    const rumble = this._noise(secs, 0.08, 0.01, 7);
    const drips = Array.from({ length: 5 }, () => 0.3 + rnd.next() * (secs - 0.7)).sort();
    const out = new Float32Array(n);
    for (let i = 0; i < n; i++) {
      const t = i / rate;
      let v = 0.028 * Math.sin(2 * Math.PI * 55 * t) * (0.7 + 0.3 * Math.sin(2 * Math.PI * 0.25 * t));
      v += 0.015 * Math.sin(2 * Math.PI * 82.5 * t);
      v += rumble[i];
      for (const d of drips) {
        const k = t - d;
        if (k >= 0 && k < 0.25) v += 0.15 * Math.sin(2 * Math.PI * (1800 - k * 2000) * k) * Math.exp(-k * 25);
      }
      out[i] = v;
    }
    const b = this.ctx.createBuffer(1, n, rate);
    b.getChannelData(0).set(out);
    this.buffers.ambient = b;
  },

  play(name) {
    if (!this.ctx || !this.enabled || !this.buffers[name]) return;
    const src = this.ctx.createBufferSource();
    src.buffer = this.buffers[name];
    src.connect(this.master);
    src.start();
  },

  _startAmbient() {
    if (!this.ctx || !this.buffers.ambient) return;
    this.ambientGain = this.ctx.createGain();
    this.ambientGain.gain.value = 0.5;
    this.ambientGain.connect(this.master);
    this.ambientNode = this.ctx.createBufferSource();
    this.ambientNode.buffer = this.buffers.ambient;
    this.ambientNode.loop = true;
    this.ambientNode.connect(this.ambientGain);
    this.ambientNode.start();
  },

  ambience(on) {
    this.ambientOn = on;
    if (on) { if (this.ctx && !this.ambientNode) this._startAmbient(); }
    else if (this.ambientNode) { try { this.ambientNode.stop(); } catch (e) { /* already stopped */ } this.ambientNode = null; }
  },
};
