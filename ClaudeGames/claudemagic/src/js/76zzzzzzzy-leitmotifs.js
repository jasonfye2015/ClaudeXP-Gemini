"use strict";
// Leitmotifs (v44.3, UPGRADE_PLAN_39.md): three themes that come back when they matter, over whatever is playing - the
// party's (four notes rising, a horn's call: on going down into a new band, and when a guardian falls), the Lich
// King's (a falling minor line with a tritone in it: on first coming into his Palace, woven quietly into the Palace's
// own tune every so often, and turned to the major when he falls), and the Joker's (a chromatic little waltz, on
// coming onto his floor). Through the music's own volume (55-music.js motif).
{ const M = CM.music; if (M) {
  const hz = (m) => 440 * Math.pow(2, (m - 69) / 12);
  const play = (notes, voice, vol0 = 1) => { const vol = vol0 * 1.6; if (!M.enabled || !M._ensure()) return false; const at0 = CM.audio.ctx.currentTime + 0.05, dest = M.master;
    for (const [m, t, d] of notes) { const at = at0 + t, f = hz(m);
      if (voice === "horn") { M._osc("sawtooth", f, at, at + d, 0.07 * vol, 1400, dest); M._osc("triangle", f / 2, at, at + d, 0.05 * vol, 600, dest); }
      else if (voice === "dark") { M._osc("triangle", f, at, at + d, 0.1 * vol, 1500, dest); M._osc("sine", f / 2, at, at + d, 0.08 * vol, 500, dest); }
      else { M._osc("square", f, at, at + d * 0.6, 0.035 * vol, 2600, dest); M._osc("triangle", f * 2, at, at + d * 0.4, 0.04 * vol, 3500, dest); } }
    return true; };
  const MOTIFS = {
    party: [[67, 0, 0.35], [71, 0.32, 0.35], [74, 0.64, 0.35], [79, 0.96, 1.1]],
    lich: [[62, 0, 0.6], [61, 0.6, 0.6], [58, 1.2, 0.6], [56, 1.8, 1.4]],
    lich_end: [[62, 0, 0.6], [64, 0.6, 0.6], [66, 1.2, 0.6], [69, 1.8, 1.6]],
    joker: [[72, 0, 0.25], [71, 0.3, 0.25], [72, 0.6, 0.25], [76, 0.9, 0.45], [75, 1.5, 0.25], [76, 1.8, 0.25], [79, 2.1, 0.6]] };
  const VOICE = { party: "horn", lich: "dark", lich_end: "dark", joker: "reed" };
  CM.LEITMOTIFS = MOTIFS;
  const m0 = M.motif; M.motif = function (name, vol) { if (MOTIFS[name]) return play(MOTIFS[name], VOICE[name], vol || 1); return m0.call(this, name); };
  const heard = new Set();
  const bind = () => { const g = CM.game; if (!g || !g.on) return false; let band = null;
    g.on("floor", (fl) => { if (!fl || g.mode === "title") return; const n = fl.number;
      if (CM.isJokerFloor && CM.isJokerFloor(n)) { setTimeout(() => M.motif("joker"), 1500); return; }
      if (!(n >= 1) || n % 1 !== 0) { band = null; return; } const b = CM.themeIndex(n); if (band !== null && b !== band) setTimeout(() => M.motif(b === 3 && !heard.has(`lich:${g.seed}`) ? "lich" : "party"), 2200); if (b === 3) heard.add(`lich:${g.seed}`); band = b; });
    g.on("fx", (fx) => { if (!fx || fx.kind !== "die" || !fx.foe) return; if (fx.foe.boss) setTimeout(() => M.motif("lich_end"), 1800); else if (fx.foe.guardian) setTimeout(() => M.motif("party"), 1600); });
    return true; };
  const t = typeof self !== "undefined" && self.CM_WORKER ? null : setInterval(() => { if (bind()) clearInterval(t); }, 300);
  // woven in: in the Palace, now and then, his line under the band's own tune
  let woven = -1; setInterval(() => { if (M.playing !== "depth3" || !M.bus) return; const bar = Math.floor((M.step || 0) / 64); if (bar === woven || (M.step % 64) < 30 || (M.step % 64) > 34 || bar % 2 !== 1) return; woven = bar; M.motif("lich", 0.45); }, 400);
} }
