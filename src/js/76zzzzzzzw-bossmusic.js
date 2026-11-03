"use strict";
// Boss themes (v44.1, UPGRADE_PLAN_39.md): each guardian and the Lich King has a battle theme of its own in place of
// the one shared boss tune - the Rat King's scurrying chromatic run, the Drowned Knight's slow funeral march, the
// Forge-Warden's hammering, the Drowned Queen's waltz, the Mycelial Mind's whole-tone drift, the Crystal Tyrant's
// bright cruel Lydian, the Foundry Master's grind, the Bone Patriarch's dirge, the Root's murk, the Bell-Founder's
// Boy's bells, and the Lich King's own - and when it turns at half its life (its second phase), the theme turns with
// it: faster, a step higher, harder on the drums. Over the band's instruments, a guardian's own voice from them.
{ const M = CM.music; if (M) {
  const DEF = { rat: [[0, 1, 3, 4, 6, 7, 9, 10], 47, 150], knight: [[0, 2, 3, 5, 7, 8, 10], 43, 84], forge: [[0, 1, 4, 5, 7, 8, 10], 45, 120], queen: [[0, 2, 3, 5, 7, 8, 11], 50, 96],
    mind: [[0, 2, 4, 6, 8, 10], 46, 92], tyrant: [[0, 2, 4, 6, 7, 9, 11], 52, 126], master: [[0, 1, 3, 5, 6, 8, 10], 41, 112], patriarch: [[0, 1, 3, 5, 7, 8, 10], 42, 76],
    root: [[0, 1, 3, 4, 6, 8, 10], 38, 70], bell: [[0, 2, 4, 7, 9], 55, 108], lich: [[0, 1, 4, 5, 7, 8, 11], 40, 100] };
  const BAND = { rat: 0, knight: 1, forge: 2, queen: 4, mind: 5, tyrant: 6, master: 7, patriarch: 8, root: 9, bell: 0, lich: 3 };
  for (const [id, [scale, root, tempo]] of Object.entries(DEF)) { M.kinds[`boss_${id}`] = { scale, root, tempo, rest: 0.14, voice: "lead", drums: true, band: BAND[id] }; M.kinds[`boss_${id}_2`] = { scale, root: root + 2, tempo: Math.round(tempo * 1.18), rest: 0.08, voice: "lead", drums: true, band: BAND[id], hard: true }; }
  const bossOf = () => { const g = CM.game; if (!g || g.mode !== "combat") return null; const m = (g.foes || []).find((f) => f.hp > 0 && (f.boss || f.guardian)); if (!m) return null; const id = m.boss ? "lich" : m.guardian; return DEF[id] ? { id, two: Boolean(m.phase2 || m.phaseShown || (m.form2 && m.formed)) } : null; };
  CM.bossTuneFor = (id, two) => `boss_${id}${two ? "_2" : ""}`;
  const start0 = M.start; M.start = function (kind, ...a) { if (kind === "boss") { const B = bossOf(); if (B) kind = CM.bossTuneFor(B.id, B.two); } return start0.call(this, kind, ...a); };
  // the guardian's own colour: its band's instrument doubling the lead, quietly
  const note0 = M._note; M._note = function (t, deg, at, len) { const out = note0.call(this, t, deg, at, len), k = t && this.kinds[t.kind];
    if (k && k.band !== undefined && CM.BAND_MUSIC && this.bus && this.danger >= 0.6) { try { const hz = this.hz(this.midi(t, deg, 0)); CM.BAND_MUSIC.NOTE[k.band](hz, at, len); } catch (e) { /* (quiet) */ } } return out; };
  const drums0 = M._drums; M._drums = function (i, at, stepLen) { const out = drums0.call(this, i, at, stepLen), t = this.tuneNow, k = t && this.kinds[t.kind];
    if (k && k.hard && i % 4 === 2 && CM.audio.ctx) { const c = CM.audio.ctx, o = c.createOscillator(), g = c.createGain(); o.frequency.setValueAtTime(120, at); o.frequency.exponentialRampToValueAtTime(45, at + 0.15); g.gain.setValueAtTime(0.5, at); g.gain.exponentialRampToValueAtTime(0.001, at + 0.2); o.connect(g); g.connect(this.bus); o.start(at); o.stop(at + 0.25); }   /* (the second phase: a double kick) */
    return out; };
  const bind = () => { const g = CM.game; if (!g || !g.on) return false; g.on("fx", (fx) => { if (!fx || fx.kind !== "bossphase" || !fx.foe) return; const id = fx.foe.boss ? "lich" : fx.foe.guardian; if (DEF[id] && String(M.playing || "").startsWith("boss_")) M.start(CM.bossTuneFor(id, true)); }); return true; };
  const t = typeof self !== "undefined" && self.CM_WORKER ? null : setInterval(() => { if (bind()) clearInterval(t); }, 300);
} }
