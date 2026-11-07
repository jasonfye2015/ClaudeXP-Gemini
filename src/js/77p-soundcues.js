"use strict";
// Claude's sound, and the cues (UPGRADE_PLAN_76.md, release 3) - all made in code, all on the existing channels.
//  Claude: a quiet quill scratching under his lines in the log (never more than one a second and a bit); a page turned
//  when a band's chapter opens; his cabin heard - a clock's tick, the hearth, now and then the kettle starting to sing,
//  the cat purring when you stand by it; and when he speaks plainly the room's sounds fall away.
//  Danger: a soft, muffled heartbeat in a fight while any hero is down to a third of their health or less; a small cue
//  as an ailment takes hold (poison's bubble, paralysis's tick, sleep's hush, blindness falling, a curse's low pair);
//  a low rumble as a guardian gathers itself for something terrible.
//  The new systems: a vow sworn is a low seal of two notes, kept a bright chord, broken a dull crack; the king's letter
//  a wax-crack and a cold chord; a revenant, now and then, heard crying out far off in the voice its hero had; a
//  curiosity, a soft chime the same for every one.
//  Weight: a critical blow has a bright crack on top of the hit; a foe's fall a low thud.
{ const A = CM.audio, live = () => A && A.ctx && A.enabled && A.master;
  const amb = () => (CM.ambienceOut && CM.ambienceOut()) || A.master;
  const tone = (hz, at, dur, gain, type = "sine", dest = A.master, to = null) => { const c = A.ctx, o = c.createOscillator(), g = c.createGain(); o.type = type; o.frequency.setValueAtTime(hz, at); if (to) o.frequency.exponentialRampToValueAtTime(to, at + dur);
    g.gain.setValueAtTime(0.0001, at); g.gain.linearRampToValueAtTime(gain, at + 0.008); g.gain.exponentialRampToValueAtTime(0.0001, at + dur); o.connect(g); g.connect(dest); o.start(at); o.stop(at + dur + 0.05); };
  let noiseBuf = null; const noise = (at, dur, gain, ftype, fhz, dest = A.master, q = 1) => { const c = A.ctx; if (!noiseBuf) { noiseBuf = c.createBuffer(1, c.sampleRate, c.sampleRate); const d = noiseBuf.getChannelData(0); for (let i = 0; i < d.length; i++) d[i] = Math.random() * 2 - 1; }
    const s = c.createBufferSource(), f = c.createBiquadFilter(), g = c.createGain(); s.buffer = noiseBuf; f.type = ftype; f.frequency.value = fhz; f.Q.value = q; g.gain.setValueAtTime(0.0001, at); g.gain.linearRampToValueAtTime(gain, at + 0.005); g.gain.exponentialRampToValueAtTime(0.0001, at + dur);
    s.connect(f); f.connect(g); g.connect(dest); s.start(at, Math.random() * 0.5); s.stop(at + dur + 0.05); };
  const now = () => A.ctx.currentTime + 0.02;
  const CUE = {
    quill: () => { const t = now(); for (let i = 0; i < 4; i++) noise(t + i * 0.07 + Math.random() * 0.03, 0.05, 0.035, "bandpass", 3200 + Math.random() * 1600, amb(), 4); },
    page: () => { const t = now(); noise(t, 0.28, 0.06, "highpass", 1800, A.master); noise(t + 0.12, 0.2, 0.04, "bandpass", 900, A.master, 0.8); },
    tick: () => noise(now(), 0.02, 0.025, "bandpass", 4200, amb(), 6),
    hearth: () => { const t = now(); for (let i = 0; i < 3; i++) noise(t + Math.random() * 0.6, 0.03, 0.03, "bandpass", 1600 + Math.random() * 1200, amb(), 3); },
    kettle: () => { const t = now(); tone(1800, t, 3.2, 0.018, "sine", amb(), 2300); noise(t, 3.0, 0.012, "bandpass", 2600, amb(), 8); },
    purr: () => { const t = now(); for (let i = 0; i < 6; i++) noise(t + i * 0.09, 0.07, 0.03, "lowpass", 140, amb(), 1); },
    heart: () => { const t = now(); tone(58, t, 0.16, 0.16, "sine", A.master, 40); tone(52, t + 0.22, 0.2, 0.11, "sine", A.master, 38); },
    poison: () => { const t = now(); for (let i = 0; i < 3; i++) tone(300 + i * 90, t + i * 0.08, 0.09, 0.05, "sine", A.master, 520 + i * 90); },
    paralysis: () => { const t = now(); tone(1800, t, 0.03, 0.05, "square"); tone(1200, t + 0.09, 0.03, 0.04, "square"); },
    sleep: () => noise(now(), 0.9, 0.05, "lowpass", 600, A.master),
    blind: () => tone(900, now(), 0.5, 0.05, "sine", A.master, 300),
    curse: () => { const t = now(); tone(110, t, 0.9, 0.08, "triangle"); tone(116.5, t, 0.9, 0.06, "triangle"); },
    rumble: () => { const t = now(); tone(42, t, 1.4, 0.2, "sine", A.master, 36); noise(t, 1.2, 0.08, "lowpass", 160, A.master); },
    vowSworn: () => { const t = now(); tone(147, t, 0.9, 0.12, "triangle"); tone(110, t + 0.32, 1.2, 0.12, "triangle"); },
    vowKept: () => { const t = now(); for (const [hz, d] of [[392, 0], [494, 0.05], [587, 0.1], [784, 0.15]]) tone(hz, t + d, 1.4, 0.06, "triangle"); },
    vowBroken: () => { const t = now(); noise(t, 0.18, 0.18, "lowpass", 700); tone(98, t, 0.8, 0.12, "sawtooth", A.master, 70); },
    wax: () => { const t = now(); noise(t, 0.06, 0.16, "highpass", 2500); for (const hz of [131, 156, 196]) tone(hz * (1 + (Math.random() - 0.5) * 0.006), t + 0.12, 2.6, 0.045, "sawtooth"); },
    chime: () => { const t = now(); tone(1568, t, 1.1, 0.035); tone(2093, t + 0.09, 1.0, 0.025); },
    crit: () => { const t = now(); noise(t, 0.09, 0.14, "highpass", 3000); tone(2200, t, 0.12, 0.05, "triangle", A.master, 1400); },
    thud: () => { const t = now(); tone(70, t, 0.35, 0.18, "sine", A.master, 42); noise(t, 0.12, 0.06, "lowpass", 300); },
  };
  CM.soundCue = (id) => { if (!live() || !CUE[id]) return false; try { CUE[id](); return true; } catch (e) { return false; } };
  const cue = CM.soundCue;
  // Claude's lines and the chapters
  let lastQuill = 0;
  const bind = () => { const g = CM.game; if (!g || !g.on) return false;
    g.on("message", (text) => { if (g.replaying || g.film || !CM.PEN || !String(text).startsWith(CM.PEN)) return; const t = performance.now(); if (/Chapter \d+:/.test(text)) cue("page"); else if (t - lastQuill > 1300) { lastQuill = t; cue("quill"); } });
    g.on("fx", (fx) => { if (!fx || g.replaying || g.film) return; if (fx.kind === "intent") cue("rumble"); if (fx.kind === "hit" && fx.crit) cue("crit"); if (fx.kind === "die") cue("thud"); });
    g.on("curio", () => cue("chime"));
    g.on("choice", (c) => { if (c && String(c.k || "").startsWith("bargain:")) cue("wax"); });
    let ail = new Map(), vowSig = "";
    g.on("change", () => { if (!g.party || g.replaying || g.film) return;
      for (const h of g.party) { const was = ail.get(h) || {}, st = h.status || {}; for (const s of Object.keys(st)) if (st[s] && !was[s] && CUE[s]) cue(s); ail.set(h, Object.assign({}, st)); }
      if (g.vows && g.tally) { const L = g.vows(), sig = L.map((v) => `${v.id}:${v.kept ? "k" : v.broken ? "b" : "h"}`).join(","); if (sig !== vowSig) { const before = vowSig.split(","); for (const v of L) { const s = `${v.id}:${v.kept ? "k" : v.broken ? "b" : "h"}`; if (before.includes(s)) continue; cue(v.kept ? "vowKept" : v.broken ? "vowBroken" : "vowSworn"); } vowSig = sig; } } });
    return true; };
  if (!bind()) { const t = setInterval(() => { if (bind()) clearInterval(t); }, 300); }
  // the heartbeat, the cabin, the revenants: a slow tick of its own
  let beat = 0, nextKettle = 0, nextCall = 0, hearth = 0;
  const tick = () => { const g = CM.game, t = performance.now(); if (live() && g && g.floor && !g.replaying && !g.film) { const fl = g.floor;
      if (g.mode === "combat" && (g.party || []).some((h) => h.hp > 0 && h.hp <= h.max / 3) && t > beat) { cue("heart"); beat = t + 950; }
      if (fl.interior === "claude" && g.mode === "explore") { cue("tick"); if (t > hearth) { cue("hearth"); hearth = t + 1800 + Math.random() * 1500; }
        if (!nextKettle) nextKettle = t + 20000 + Math.random() * 20000; else if (t > nextKettle) { cue("kettle"); nextKettle = t + 50000 + Math.random() * 40000; }
        const [dx, dy] = CM.DIRS[fl.facing]; const near = [`${fl.pos[0] + dx},${fl.pos[1] + dy}`, `${fl.pos[0]},${fl.pos[1]}`].some((k) => fl.things[k] && fl.things[k].type === "cabincat"); if (near && Math.random() < 0.6) cue("purr");
        if (CM.mixHold && g.claudeMenu && g.claudeMenu.some((o) => o[0] === "plainly")) CM.mixHold("plain", 0.4, 0.15, 1200); }
      else nextKettle = 0;
      if (fl.number >= 1 && g.mode === "explore" && CM.heroBark) { const R = Object.values(fl.things).find((x) => x && x.revenant && x.group && x.group[0] && x.group[0].hp > 0);
        if (R) { if (!nextCall) nextCall = t + 12000 + Math.random() * 15000; else if (t > nextCall) { const m = (g.memorial || []).find((e) => `${e.name}|${e.date}|${e.seed}` === R.group[0].revenant); if (m) CM.heroBark(g, { name: m.name, cls: m.cls, level: m.level }, "fall"); nextCall = t + 30000 + Math.random() * 30000; } } else nextCall = 0; } }
    setTimeout(tick, 1000); };
  setTimeout(tick, 1500);
}
