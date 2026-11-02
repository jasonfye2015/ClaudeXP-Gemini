"use strict";
// Hero barks (v43.0, UPGRADE_PLAN_38.md): the heroes have made voices now - no words, a throat: a grunt when a blow lands
// on them, a shout on a weak spot struck, a long cry as one falls, a whoop at a new level. Each hero's voice is pitched by
// calling (a Knight's low, a Mage's light) and a little by name, so the four sound like four. CM.voice is the throat - a
// buzz through two vowel filters and a breath of air, made with the Web Audio nodes - and the later voices use it too.
// CM.VOICE_LEVELS: each kind of voice's loudness (heroes, monsters, town, ghosts, followers), 0..1.
{ const VOWELS = { a: [730, 1090], e: [530, 1840], i: [300, 2250], o: [570, 840], u: [320, 870], uh: [640, 1190], er: [490, 1350] };
  CM.VOICE_LEVELS = Object.assign({ heroes: 1, monsters: 1, town: 1, ghosts: 1, followers: 1 }, CM.VOICE_LEVELS || {});
  let noiseBuf = null;
  CM.voice = (o) => { const A = CM.audio; if (!A || !A.ctx || !A.enabled || !A.master) return; const lvl = CM.VOICE_LEVELS[o.group || "heroes"]; if (lvl !== undefined && lvl <= 0) return;
    try { const ctx = A.ctx, t = ctx.currentTime + (o.at || 0), d = (o.ms || 250) / 1000, vol = (o.vol || 0.2) * (lvl === undefined ? 1 : lvl), V1 = VOWELS[o.vowel || "a"] || VOWELS.a, V2 = VOWELS[o.to2 || o.vowel || "a"] || V1;
      const out = ctx.createGain(); out.gain.setValueAtTime(0.0001, t); out.gain.exponentialRampToValueAtTime(vol, t + Math.min(0.03, d * 0.2)); out.gain.setValueAtTime(vol, t + d * 0.6); out.gain.exponentialRampToValueAtTime(0.0001, t + d);
      let tail = out; if (o.pan && ctx.createStereoPanner) { const p = ctx.createStereoPanner(); p.pan.value = Math.max(-1, Math.min(1, o.pan)); out.connect(p); tail = p; } tail.connect(A.master);
      const src = ctx.createOscillator(); src.type = o.wave || "sawtooth"; src.frequency.setValueAtTime(o.pitch || 140, t); src.frequency.exponentialRampToValueAtTime(Math.max(30, o.to || o.pitch || 140), t + d);
      if (o.growl) { const lfo = ctx.createOscillator(), lg = ctx.createGain(); lfo.frequency.value = o.growlRate || 28; lg.gain.value = (o.pitch || 140) * o.growl; lfo.connect(lg); lg.connect(src.frequency); lfo.start(t); lfo.stop(t + d + 0.05); }
      for (const [i, Q, g] of [[0, 7, 1], [1, 9, 0.6]]) { const f = ctx.createBiquadFilter(), fg = ctx.createGain(); f.type = "bandpass"; f.Q.value = Q; f.frequency.setValueAtTime(V1[i] * (o.formant || 1), t); f.frequency.linearRampToValueAtTime(V2[i] * (o.formant || 1), t + d); fg.gain.value = g * 3; src.connect(f); f.connect(fg); fg.connect(out); }
      src.start(t); src.stop(t + d + 0.05);
      if (o.breath) { if (!noiseBuf) { const n = ctx.sampleRate, b = ctx.createBuffer(1, n, n), dd = b.getChannelData(0); for (let i = 0; i < n; i++) dd[i] = Math.random() * 2 - 1; noiseBuf = b; }
        const ns = ctx.createBufferSource(), nf = ctx.createBiquadFilter(), ng = ctx.createGain(); ns.buffer = noiseBuf; nf.type = "bandpass"; nf.frequency.value = V1[1] * 1.3; nf.Q.value = 1.2; ng.gain.value = o.breath; ns.connect(nf); nf.connect(ng); ng.connect(out); ns.start(t); ns.stop(t + d + 0.05); } } catch (e) { /* (no voice) */ } };
  const BASE = { Knight: 100, Paladin: 112, Rogue: 150, Ranger: 138, Cleric: 165, Mage: 190, Druid: 158, Bard: 175, Monk: 128, Necromancer: 118, Artificer: 145 };
  const pitchOf = (h) => (BASE[h.cls] || 140) * (0.85 + ((CM.hashSeed(`voice:${h.name}`) >>> 0) % 1000) / 1000 * 0.4);
  const panOf = (g, h) => { const i = (g.party || []).indexOf(h); return i < 0 ? 0 : (i - 1.5) * 0.25; };
  const last = new WeakMap(), ok = (h, ms) => { const now = performance.now(); if (now - (last.get(h) || 0) < ms) return false; last.set(h, now); return true; };
  CM.heroBark = (g, h, what) => { if (!h || CM.VOICE_LEVELS.heroes <= 0) return; const P = pitchOf(h), pan = panOf(g, h);
    if (what === "hurt" && ok(h, 300)) CM.voice({ pitch: P * 1.15, to: P * 0.85, ms: 170, vowel: "uh", vol: 0.16, breath: 0.25, pan });
    if (what === "crit" && ok(h, 300)) CM.voice({ pitch: P * 1.3, to: P * 1.05, ms: 200, vowel: "a", to2: "uh", vol: 0.2, breath: 0.4, pan });
    if (what === "fall") { last.set(h, performance.now()); CM.voice({ pitch: P * 1.35, to: P * 0.55, ms: 900, vowel: "a", to2: "o", vol: 0.22, breath: 0.2, pan, growl: 0.02, growlRate: 6 }); }
    if (what === "level") { last.set(h, performance.now()); CM.voice({ pitch: P, to: P * 1.45, ms: 300, vowel: "e", to2: "i", vol: 0.18, pan }); CM.voice({ pitch: P * 1.4, to: P * 1.2, ms: 220, vowel: "a", vol: 0.16, pan, at: 0.32, breath: 0.2 }); } };
  const bind = () => { const g = CM.game; if (!g || !g.on) return false;
    g.on("fx", (fx) => { if (!fx) return; if (fx.kind === "hurt" && fx.hero) CM.heroBark(g, fx.hero, fx.hero.hp <= 0 ? "fall" : "hurt"); else if (fx.kind === "hit" && fx.crit && fx.hero) CM.heroBark(g, fx.hero, "crit"); else if (fx.kind === "levelup" && fx.hero) CM.heroBark(g, fx.hero, "level"); }); return true; };
  const t = typeof self !== "undefined" && self.CM_WORKER ? null : setInterval(() => { if (bind()) clearInterval(t); }, 300);
}
