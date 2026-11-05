"use strict";
// The soundscape (v80.0, UPGRADE_PLAN_61.md part 10): CM.Weatherscape - procedural beds on the ambience bus, each
// eased toward a want set every quarter second from CM.weatherNow (76zzzzzzzzc-weathersound.js keeps the rain's
// hiss and the breeze by the day's word; these go by the live event's strength): the downpour's broad roar and the
// roofs' patter rising with a heavy rain, the gale's howl in a resonant band that leans with the gusts; the four
// fogs' pads - orange a crackling static over a 55 Hz hum, green a soft bubbling hiss with slow dips, brown a 40 Hz
// drone pulsing every two seconds, violet a crystalline chord of sine partials with a slow detune; below ground
// the same beds through a low-pass at 600 Hz at a third the gain (the storm and the gale heard muffled through the
// stone, the draft's howl); a tree's crack when one is felled within hearing; and the music ducked under a storm or
// a fog - its gain down by a third and a low-pass from 20 kHz to 1.2 kHz over four seconds, back when it clears.
{ const live = () => { const A = CM.audio; return Boolean(A && A.ctx && A.enabled && A.master); };
  let noise = null; const N = (c) => { if (noise && noise.ctx === c) return noise.b; const n = c.sampleRate * 2, b = c.createBuffer(1, n, c.sampleRate), d = b.getChannelData(0); for (let i = 0; i < n; i++) d[i] = (Math.random() * 2 - 1) * 0.6; noise = { ctx: c, b }; return b; };
  const beds = {}, oscs = {}; let muffle = null;
  const outFor = (below) => { const A = CM.audio, c = A.ctx, amb = CM.ambienceOut ? CM.ambienceOut() : A.master; if (!below) return amb; if (!muffle || muffle.ctx !== c) { const f = c.createBiquadFilter(), g = c.createGain(); f.type = "lowpass"; f.frequency.value = 600; g.gain.value = 0.33; f.connect(g); g.connect(amb); muffle = { ctx: c, f, g }; } return muffle.f; };
  const bed = (id, type, hz, q, below) => { const c = CM.audio.ctx, key = `${id}:${below ? "b" : "a"}`; let B = beds[key]; if (B && B.ctx === c) return B; const s = c.createBufferSource(), f = c.createBiquadFilter(), g = c.createGain(); s.buffer = N(c); s.loop = true; f.type = type; f.frequency.value = hz; f.Q.value = q || 1; g.gain.value = 0; s.connect(f); f.connect(g); g.connect(outFor(below)); s.start(); B = beds[key] = { ctx: c, s, f, g, level: 0 }; return B; };
  const osc = (id, type, hz, below) => { const c = CM.audio.ctx, key = `${id}:${below ? "b" : "a"}`; let O = oscs[key]; if (O && O.ctx === c) return O; const o = c.createOscillator(), g = c.createGain(); o.type = type; o.frequency.value = hz; g.gain.value = 0; o.connect(g); g.connect(outFor(below)); o.start(); O = oscs[key] = { ctx: c, o, g, level: 0 }; return O; };
  const ease = (B, want, t = 0.8) => { const c = CM.audio.ctx; if (Math.abs(B.level - want) < 0.001) return; B.level = want; B.g.gain.setTargetAtTime(want, c.currentTime, t); };
  let tick = 0, gust = 0, duck = null;
  const step = () => { if (!live()) return; const g = CM.game, fl = g && g.floor, c = CM.audio.ctx, A = CM.audio;
    const off = !fl || g.mode === "title" || !g.ext; const W = off ? { kind: "clear", strength: 0, wind: { speed: 0, dir: [1, 0] } } : CM.weatherNow(g), top = !off && (fl.number === 0 || fl.number === -1), below = !off && !top, depth = below ? ({ 1: 1, 2: 0.6, 3: 0.3 }[fl.number] || 0.1) : 0, k = W.strength;
    gust += (Math.random() - 0.5) * 0.3; gust = Math.max(-1, Math.min(1, gust * 0.97));
    for (const b of [false, true]) { const here = b ? below : top, d = b ? depth : 1;   // the beds above, and their muffled selves below
      const rain = here && (W.kind === "rain" || W.kind === "storm") ? k : 0;
      ease(bed("downpour", "lowpass", 3800, 0.7, b), Math.max(0, rain - 0.45) / 0.55 * 0.16 * d, 1.5);
      ease(bed("patter", "bandpass", 3200, 0.8, b), rain * 0.07 * d, 1.0);
      const howl = here && W.wind.speed > 0.55 ? (W.wind.speed - 0.5) * 2 : 0, H = bed("howl", "bandpass", 260, 5, b); H.f.frequency.setTargetAtTime(200 + howl * 120 + gust * 90, c.currentTime, 0.7); ease(H, howl * 0.09 * (1 + 0.5 * gust) * d, 1.2);
      const Fg = here && CM.fogNow ? CM.fogNow(g) : null, fog = (kind) => (Fg && Fg.kind === kind ? Fg.strength : 0);
      ease(osc("hum55", "sine", 55, b), fog("fogorange") * 0.05 * d, 1.5); ease(bed("crackle", "highpass", 4200, 1, b), fog("fogorange") * (Math.random() < 0.35 ? 0.05 : 0.006) * d, 0.08);
      ease(bed("bubble", "bandpass", 900, 3, b), fog("foggreen") * 0.06 * (0.55 + 0.45 * Math.sin(tick * 0.31) * Math.sin(tick * 0.07)) * d, 0.5);
      ease(osc("drone40", "sine", 40, b), fog("fogbrown") * 0.1 * (0.5 + 0.5 * Math.sin(tick * Math.PI / 4)) * d, 0.3);
      for (const [i, hz] of [[0, 440], [1, 660], [2, 880]]) { const O = osc(`chord${i}`, "sine", hz, b); O.o.detune.setTargetAtTime((Math.random() - 0.5) * 24, c.currentTime, 2.5); ease(O, fog("fogpurple") * 0.018 * (0.6 + 0.4 * Math.sin(tick * 0.2 + i)) * d, 1.2); } }
    // the music ducked under a storm or a fog
    const m = CM.music; if (m && m.master && c) { if (!duck || duck.ctx !== c) { try { m.master.disconnect(); const lp = c.createBiquadFilter(), dg = c.createGain(); lp.type = "lowpass"; lp.frequency.value = 20000; dg.gain.value = 1; m.master.connect(lp); lp.connect(dg); dg.connect(c.destination); duck = { ctx: c, lp, dg }; } catch (er) { duck = null; } }
      if (duck) { const heavy = !off && (W.kind === "storm" && k > 0.3 || (CM.fogNow && CM.fogNow(g))); duck.lp.frequency.setTargetAtTime(heavy ? 1200 : 20000, c.currentTime, 1.3); duck.dg.gain.setTargetAtTime(heavy ? 0.67 : 1, c.currentTime, 1.3); } }
    tick++; A.weatherscapeTick = tick; };
  const t = typeof self !== "undefined" && self.CM_WORKER ? null : setInterval(() => { try { step(); } catch (e) { /* (quiet) */ } }, 250);
  CM.Weatherscape = { beds, oscs, step, levels: () => { const out = {}; for (const [k, B] of Object.entries(beds)) if (B.level > 0.001) out[k] = Math.round(B.level * 1000) / 1000; for (const [k, O] of Object.entries(oscs)) if (O.level > 0.001) out[k] = Math.round(O.level * 1000) / 1000; return out; }, duck: () => duck };
  // a tree's crack when one is felled within hearing
  const crack = (dist) => { if (!live()) return; const c = CM.audio.ctx, at = c.currentTime, vol = Math.max(0.08, 0.5 * (1 - dist / 14)); const o = c.createOscillator(), g = c.createGain(); o.type = "sawtooth"; o.frequency.setValueAtTime(140, at); o.frequency.exponentialRampToValueAtTime(38, at + 0.28); g.gain.setValueAtTime(vol * 0.6, at); g.gain.exponentialRampToValueAtTime(0.0001, at + 0.3); o.connect(g); g.connect(CM.ambienceOut ? CM.ambienceOut() : CM.audio.master); o.start(at); o.stop(at + 0.32);
    const s = c.createBufferSource(), f = c.createBiquadFilter(), ng = c.createGain(); s.buffer = N(c); f.type = "lowpass"; f.frequency.setValueAtTime(2400, at); f.frequency.exponentialRampToValueAtTime(300, at + 0.9); ng.gain.setValueAtTime(vol, at + 0.05); ng.gain.exponentialRampToValueAtTime(0.0001, at + 1.0); s.connect(f); f.connect(ng); ng.connect(CM.ambienceOut ? CM.ambienceOut() : CM.audio.master); s.start(at, Math.random()); s.stop(at + 1.1); };
  { const f0 = CM.fellTree; if (f0) CM.fellTree = (game, fl, key, how) => { const out = f0(game, fl, key, how); if (out && game && game.floor === fl && fl.pos) { const [x, y] = key.split(",").map(Number), d = Math.abs(x - fl.pos[0]) + Math.abs(y - fl.pos[1]); if (d <= 14) crack(d); } return out; }; }
}
