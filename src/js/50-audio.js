"use strict";
// The sounds, made in code with Web Audio - the same recipes the old game cooked into .wav files, and more: square and
// sine tones that fade, sweeps, smoothed noise, laid over one another; a ten-second ambience for each depth (the
// Catacombs drip, the Vaults run with water, wind and far-off iron in the Halls, a cold hum and whispers in the
// Palace, and the camp's fire) that loops; a call for each kind of monster, louder the nearer it comes (near()). The
// music is in 55-music.js. Browsers won't play a sound before the first click or key, so unlock() is called on both.
CM.audio = {
  ctx: null,
  buffers: {},
  enabled: true,
  volume: 0.6,
  ambientOn: false,
  ambientNode: null,
  ambientGain: null,

  ambients: {},
  theme: 0,
  lastNear: 0,

  unlock() {
    if (!this.ctx) {
      try { this.ctx = new (window.AudioContext || window.webkitAudioContext)(); } catch (e) { return false; }
      this.master = this.ctx.createGain();
      this.master.gain.value = this.enabled ? this.volume : 0;
      this.master.connect(this.ctx.destination);
      this._cook();
      if (CM.music) CM.music.resume();
    }
    if (this.ctx.state === "suspended") this.ctx.resume();
    if (this.ambientOn && !this.ambientNode) this._startAmbient();
    return true;
  },

  setEnabled(on) {
    this.enabled = on;
    if (this.master) this.master.gain.value = on ? this.volume : 0;
    if (!on && this.ambientNode) { try { this.ambientNode.stop(); } catch (e) { /* already stopped */ } this.ambientNode = null; }
    if (on && this.ambientOn && this.ctx && !this.ambientNode) this._startAmbient();
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

  _noise(length, vol, smooth, seed = 1, fade = true) {
    const rate = this.ctx.sampleRate, rnd = new CM.Random(seed), out = [], n = Math.floor(rate * length);
    let last = 0;
    for (let i = 0; i < n; i++) {
      last += (rnd.next() * 2 - 1 - last) * smooth;
      out.push(last * vol * (fade ? 1 - i / n : 1));
    }
    return out;
  },

  _buffer(samples) {
    const b = this.ctx.createBuffer(1, samples.length, this.ctx.sampleRate);
    b.getChannelData(0).set(samples);
    return b;
  },

  // a sweep: a tone sliding from one pitch to another
  _sweep(from, to, length, kind = "sine", vol = 0.15, fadeIn = 0) {
    const rate = this.ctx.sampleRate, n = Math.floor(rate * length), out = [];
    let phase = 0;
    for (let i = 0; i < n; i++) {
      const k = i / n, freq = from + (to - from) * k;
      phase += 2 * Math.PI * freq / rate;
      const env = Math.min(1, fadeIn ? i / (rate * fadeIn) : 1) * Math.pow(1 - k, 1.2);
      out.push((kind === "sine" ? Math.sin(phase) : (phase % (2 * Math.PI) < Math.PI ? 1 : -1)) * vol * env);
    }
    return out;
  },

  _mix(...parts) {                                                      // several sounds laid over one another
    const n = Math.max(...parts.map((p) => p.length)), out = new Array(n).fill(0);
    for (const p of parts) for (let i = 0; i < p.length; i++) out[i] += p[i];
    return out;
  },

  _after(delay, part) {                                                 // the same sound, that much later
    return new Array(Math.floor(this.ctx.sampleRate * delay)).fill(0).concat(part);
  },

  _cook() {
    const T = (notes, kind, vol) => this._tones(notes, kind, vol), N = (len, vol, smooth, seed) => this._noise(len, vol, smooth, seed);
    const recipes = {
      step: () => N(0.09, 0.28, 0.08, 3),
      step_water: () => this._mix(N(0.08, 0.2, 0.08, 3), this._after(0.03, N(0.16, 0.18, 0.5, 13))),
      step_hall: () => this._mix(N(0.07, 0.26, 0.08, 3), this._after(0.11, N(0.07, 0.1, 0.08, 3)), this._after(0.22, N(0.07, 0.04, 0.08, 3))),
      step_cold: () => N(0.05, 0.3, 0.2, 3),
      bump: () => T([[70, 0.12]], "square", 0.2),
      elite: () => this._mix(T([[196, 0.18], [233, 0.18], [294, 0.3]], "sawtooth", 0.09), this._after(0.02, N(0.12, 0.3, 0.5, 41)), this._after(0.36, N(0.2, 0.25, 0.5, 43))),   // a leader among them: two brass notes and a drum
      chest: () => T([[392, 0.07], [523, 0.07], [659, 0.12]]),
      door: () => this._mix(this._sweep(220, 90, 0.5, "square", 0.05), N(0.5, 0.12, 0.03, 17), this._after(0.45, T([[60, 0.1]], "square", 0.15))),
      unlock: () => this._mix(T([[1400, 0.02]], "square", 0.12), this._after(0.12, T([[900, 0.03]], "square", 0.15)), this._after(0.3, T([[180, 0.08]], "square", 0.12))),
      lever: () => this._mix(...[0, 0.06, 0.12, 0.18].map((d) => this._after(d, T([[700 - d * 2000, 0.02]], "square", 0.1))), this._after(0.3, T([[50, 0.3]], "sine", 0.3))),
      trap: () => this._mix(T([[1200, 0.03]], "square", 0.2), this._after(0.05, N(0.4, 0.18, 0.6, 23))),
      teleport: () => this._mix(this._sweep(200, 1600, 0.5, "sine", 0.14), this._after(0.3, T(Array.from({ length: 8 }, (_, i) => [1200 + i * 150, 0.03]), "sine", 0.1))),
      fall: () => this._mix(this._sweep(600, 80, 0.7, "sine", 0.1), N(0.7, 0.2, 0.15, 29), this._after(0.7, N(0.15, 0.4, 0.5, 31))),
      hit: () => N(0.12, 0.42, 0.5, 5),
      hurt: () => T([[180, 0.06], [120, 0.1]], "square", 0.18),
      spell: () => T(Array.from({ length: 15 }, (_, i) => [400 + i * 80, 0.025]), "sine", 0.2),
      heal: () => T([[523, 0.07], [659, 0.07], [784, 0.07], [1047, 0.14]], "sine", 0.18),
      coin: () => T([[1319, 0.05], [1760, 0.12]]),
      stairs: () => T([[392, 0.1], [330, 0.1], [262, 0.1], [196, 0.2]], "sine", 0.18),
      level: () => T([[523, 0.09], [659, 0.09], [784, 0.09], [1047, 0.09], [784, 0.09], [1047, 0.25]]),
      death: () => T([[330, 0.2], [262, 0.2], [196, 0.25], [131, 0.5]], "sine", 0.2),
      victory: () => T([[523, 0.12], [523, 0.12], [523, 0.12], [659, 0.3], [587, 0.15], [784, 0.5]]),
      monster: () => T([[110, 0.15], [98, 0.25]], "square", 0.18),
      roar_small: () => this._mix(this._sweep(900, 1300, 0.12, "square", 0.08), this._after(0.15, this._sweep(1100, 800, 0.1, "square", 0.07))),
      roar_beast: () => this._mix(this._sweep(180, 120, 0.5, "square", 0.08), N(0.5, 0.25, 0.3, 37)),
      roar_big: () => this._mix(this._sweep(110, 70, 0.8, "square", 0.1), N(0.8, 0.3, 0.2, 41)),
      roar_undead: () => this._mix(...[0, 0.08, 0.16, 0.26, 0.4].map((d) => this._after(d, N(0.05, 0.3, 0.9, 43 + Math.floor(d * 100)))), this._sweep(300, 200, 0.6, "sine", 0.04)),
      lich: () => this._mix(T([[55, 1.2]], "sine", 0.22), T([[82.4, 1.2]], "sine", 0.1), this._after(0.3, N(0.9, 0.08, 0.95, 47)), this._after(0.6, this._sweep(400, 180, 0.6, "sine", 0.05))),
      miss: () => this._mix(this._sweep(1200, 300, 0.12, "sine", 0.06), N(0.12, 0.15, 0.5, 61)),
      // Leshy's table (76b-cabin.js): paper and wood and a little bell
      card: () => this._mix(N(0.07, 0.22, 0.85, 111), this._after(0.02, N(0.05, 0.12, 0.6, 113))),                                   // (a card drawn: a flick of paper)
      cardplace: () => this._mix(N(0.05, 0.18, 0.7, 115), this._after(0.04, this._sweep(160, 90, 0.08, "sine", 0.22))),               // (laid on the table: a slap and a knock)
      cardhit: () => this._mix(this._sweep(220, 70, 0.14, "sine", 0.32), N(0.08, 0.2, 0.3, 117)),                                     // (a blow)
      carddeath: () => this._mix(N(0.28, 0.2, 0.92, 119), this._after(0.05, this._sweep(300, 120, 0.25, "triangle", 0.06))),          // (crumpled away)
      sacrifice: () => this._mix(this._sweep(1800, 900, 0.09, "sawtooth", 0.05), this._after(0.06, N(0.12, 0.16, 0.5, 121))),         // (the knife)
      bones: () => this._mix(...[0, 0.05, 0.11, 0.18].map((d, i) => this._after(d, T([[900 + i * 170, 0.025]], "square", 0.06)))),     // (a rattle of bones)
      scale: () => this._mix(T([[520, 0.05]], "triangle", 0.14), this._after(0.12, T([[390, 0.07]], "triangle", 0.12))),              // (the scale tips: tick, tock)
      tablebell: () => this._mix(T([[1320, 0.9]], "sine", 0.16), T([[1980, 0.6]], "sine", 0.06), T([[2640, 0.35]], "sine", 0.03)),      // (the bell on the table)
      cardwin: () => T([[523, 0.12], [659, 0.12], [784, 0.12], [1047, 0.35]], "triangle", 0.12),
      cardlose: () => T([[392, 0.18], [330, 0.18], [262, 0.45]], "triangle", 0.11),
      zap: () => this._mix(this._sweep(2400, 900, 0.07, "square", 0.05), N(0.03, 0.06, 0.9, 123)),                                   // (Claudeita's cave: a wand's bolt)
      wanddig: () => this._mix(N(0.06, 0.16, 0.35, 125), this._sweep(300, 180, 0.05, "square", 0.04)),                                // (a digging bolt in the earth)
      wandboom: () => this._mix(N(0.5, 0.6, 0.2, 127), this._sweep(110, 30, 0.6, "sine", 0.45), this._after(0.08, N(0.6, 0.25, 0.08, 129))),   // (a blast that takes the rock with it)
      splash: () => this._mix(N(0.22, 0.2, 0.6, 131), this._after(0.05, N(0.18, 0.1, 0.8, 133))),                                     // (water, or acid, thrown)
      snore: () => this._mix(N(0.7, 0.16, 0.92, 83), this._sweep(70, 55, 0.7, "sine", 0.06)),                                       // (a sleeper, near: phase 7)
      hinge: () => this._mix(this._sweep(520, 300, 0.32, "sawtooth", 0.03), this._sweep(610, 380, 0.28, "square", 0.015)),         // (a door swinging)
      chain: () => this._mix(...[0, 0.07, 0.14, 0.21, 0.28, 0.35, 0.42].map((d, i) => this._after(d, T([[900 + (i % 3) * 140, 0.03]], "square", 0.07))), this._after(0.5, T([[70, 0.2]], "square", 0.12))),   // (a portcullis)
      lap: () => this._mix(N(0.5, 0.1, 0.97, 89), this._after(0.25, N(0.4, 0.07, 0.97, 97))),                                   // (water against stone)
      wind: () => this._mix(N(1.6, 0.14, 0.985, 101), this._sweep(240, 330, 1.6, "sine", 0.015)),                              // (up on a tower)
      bark: () => this._mix(this._sweep(520, 300, 0.09, "square", 0.12), this._after(0.16, this._sweep(560, 320, 0.09, "square", 0.1))),   // (the dog)
      bell: () => this._mix(T([[131, 1.6]], "sine", 0.24), T([[139, 1.4]], "sine", 0.12), T([[262, 0.8]], "triangle", 0.05), this._after(0.01, N(0.06, 0.3, 0.5, 103))),   // (a cracked bell)
      toll: () => this._mix(T([[98, 1.4]], "sine", 0.26), T([[147, 1.1]], "sine", 0.12), T([[196, 0.9]], "triangle", 0.06), this._after(0.02, N(0.08, 0.3, 0.6, 73))),
      slam: () => this._mix(N(0.3, 0.55, 0.25, 71), this._sweep(140, 40, 0.45, "sine", 0.35), this._after(0.25, N(0.4, 0.2, 0.1, 79))),
      fallen: () => T([[220, 0.15], [165, 0.2], [110, 0.45]], "square", 0.14),
      ailment: () => this._mix(T([[440, 0.35]], "sine", 0.1), T([[466, 0.35]], "sine", 0.1)),
      grind: () => this._mix(N(0.9, 0.35, 0.02, 67), this._sweep(90, 60, 0.9, "square", 0.04), this._after(0.85, T([[55, 0.15]], "square", 0.2))),
      shatter: () => this._mix(N(0.3, 0.4, 0.95, 53), this._after(0.05, T(Array.from({ length: 10 }, (_, i) => [2000 + i * 300, 0.02]), "sine", 0.1)), this._after(0.4, this._sweep(300, 60, 0.8, "sine", 0.12))),
    };
    for (const [name, make] of Object.entries(recipes)) this.buffers[name] = this._buffer(make());
    this.ambients = {};
  },

  // the sound of a depth: dripping catacombs (0); water running through the vaults (1); wind and far-off iron in the
  // halls (2); a cold hum and half-heard whispers in the palace (3); the camp's fire (4) - each a loop made when it's
  // first wanted
  ambient(theme) {
    if (this.ambients[theme]) return this.ambients[theme];
    const rate = this.ctx.sampleRate, secs = 10, n = rate * secs, rnd = new CM.Random(11 + theme), out = new Float32Array(n);
    const rumble = this._noise(secs, theme === 2 ? 0.14 : theme === 4 ? 0.05 : 0.08, theme === 2 ? 0.03 : theme === 4 ? 0.35 : 0.01, 7 + theme, false);
    const drips = Array.from({ length: theme === 0 ? 6 : theme === 1 ? 10 : theme === 4 ? 0 : 2 }, () => 0.3 + rnd.next() * (secs - 0.7)).sort();
    const clanks = theme === 2 ? Array.from({ length: 3 }, () => 1 + rnd.next() * (secs - 2)) : [];
    const whispers = theme === 3 ? Array.from({ length: 4 }, () => 0.5 + rnd.next() * (secs - 1.5)) : [];
    const pops = theme === 4 ? Array.from({ length: 36 }, () => rnd.next() * (secs - 0.05)).sort() : [];
    const whisperNoise = this._noise(0.6, 0.06, 0.98, 59), popNoise = this._noise(0.04, 0.5, 0.8, 71);
    for (let i = 0; i < n; i++) {
      const t = i / rate;
      let v = 0;
      if (theme === 0) v = 0.028 * Math.sin(2 * Math.PI * 55 * t) * (0.7 + 0.3 * Math.sin(2 * Math.PI * 0.25 * t)) + 0.015 * Math.sin(2 * Math.PI * 82.5 * t);
      if (theme === 1) v = 0.02 * Math.sin(2 * Math.PI * 49 * t) + rumble[i] * (1.3 + 0.7 * Math.sin(2 * Math.PI * 0.11 * t));   // water, swelling
      if (theme === 2) v = rumble[i] * (0.8 + 0.6 * Math.sin(2 * Math.PI * 0.07 * t + 1)) + 0.012 * Math.sin(2 * Math.PI * 65 * t);   // wind
      if (theme === 3) v = 0.03 * Math.sin(2 * Math.PI * 48 * t) + 0.02 * Math.sin(2 * Math.PI * 72.2 * t) + 0.01 * Math.sin(2 * Math.PI * 96.5 * t);   // a cold hum, beating
      if (theme === 4) v = rumble[i] * (0.7 + 0.3 * Math.sin(2 * Math.PI * 0.4 * t)) + 0.012 * Math.sin(2 * Math.PI * 60 * t);   // the fire's hiss
      if (theme === 0 || theme === 2) v += rumble[i] * 0.6;
      for (const d of drips) { const k = t - d; if (k >= 0 && k < 0.25) v += 0.15 * Math.sin(2 * Math.PI * (1800 - k * 2000) * k) * Math.exp(-k * 25); }
      for (const c of clanks) { const k = t - c; if (k >= 0 && k < 1.2) v += 0.05 * Math.sin(2 * Math.PI * 620 * k) * Math.exp(-k * 4) + 0.03 * Math.sin(2 * Math.PI * 931 * k) * Math.exp(-k * 6); }
      for (const w of whispers) { const k = t - w; if (k >= 0 && k < 0.6) v += whisperNoise[Math.floor(k * rate)] * Math.sin(Math.PI * k / 0.6); }
      for (const c of pops) { const k = t - c; if (k >= 0 && k < 0.04) v += popNoise[Math.floor(k * rate)] * (1 - k / 0.04); }
      out[i] = v;
    }
    const b = this.ctx.createBuffer(1, n, rate);
    b.getChannelData(0).set(out);
    this.ambients[theme] = b;
    return b;
  },

  play(name, volume = 1, pan = 0, rate = 1) {
    if (!this.ctx || !this.enabled || !this.buffers[name]) return;
    const src = this.ctx.createBufferSource(), g = this.ctx.createGain();
    src.buffer = this.buffers[name];
    if (rate !== 1) src.playbackRate.value = rate;
    g.gain.value = CM.clamp(volume, 0, 1);
    src.connect(g);
    if (pan && this.ctx.createStereoPanner) { const p = this.ctx.createStereoPanner(); p.pan.value = CM.clamp(pan, -1, 1); g.connect(p); p.connect(this.master); }
    else g.connect(this.master);
    src.start();
  },

  // a bark: a kind's call, short and shifted - high and quick for a blow taken, low and slow for its death
  bark(kind, what) { if (!this.ctx || !this.enabled) return; const now = performance.now(); if (now - (this.lastBark || 0) < 180) return; this.lastBark = now; this.play(CM.roarFor(kind), what === "die" ? 0.5 : 0.22, 0, what === "die" ? 0.7 : 1.5); },
  // something is coming: its kind's call, louder the nearer it is, not too often - and from the side it is on (pan -1..1)
  near(kind, strength, pan = 0) {
    const now = performance.now();
    if (now - this.lastNear < 2500) return;
    this.lastNear = now;
    this.play(CM.roarFor(kind), CM.clamp(strength, 0.1, 0.8), pan);
  },

  _startAmbient() {
    if (!this.ctx) return;
    this.ambientGain = this.ctx.createGain();
    this.ambientGain.gain.value = 0.5;
    this.ambientGain.connect(this.master);
    this.ambientNode = this.ctx.createBufferSource();
    this.ambientNode.buffer = this.ambient(this.theme);
    this.ambientNode.loop = true;
    this.ambientNode.connect(this.ambientGain);
    this.ambientNode.start();
    this.ambientTheme = this.theme;
  },

  ambience(on, theme) {
    if (theme !== undefined) this.theme = theme;
    this.ambientOn = on;
    if (this.ambientNode && (!on || this.ambientTheme !== this.theme)) { try { this.ambientNode.stop(); } catch (e) { /* already stopped */ } this.ambientNode = null; }
    if (on && this.ctx && !this.ambientNode) this._startAmbient();
  },
};

