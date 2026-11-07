"use strict";
// The mix, first pass (UPGRADE_PLAN_76.md, release 1, from the audio review).
//  Variation: every effect played is a touch different each time - its pitch within about four parts in a hundred, its
//  level within a tenth - so the coin, the step, the door and the blow stop sounding stamped (the bells, the tolls, the
//  victory and the level's fanfare keep their pitch). A burst of one sound is thinned: the third copy inside a tenth
//  of a second and a half is quieter, the fifth not played - twenty coins become a cascade, not a wall.
//  A gentle compressor on both outputs, the effects' and the music's, so a crowded moment never clips.
//  Silence where it matters: the music and the place's ambience dip under any conversation (Claude, a guardian's
//  parley, a letter, a choice); when a hero falls the music falls to almost nothing for a few seconds; a new band's
//  first floor gets a breath of quiet before its theme; and on the king's own floor the music is a hush. Every change
//  eases in and out - never a cut. The sliders, the mute and the headphones are untouched.
//   CM.mixState() -> what the mix is doing (for the tests and the curious)
{ const A = CM.audio; if (A && A.play) {
  const FIXED = new Set(["victory", "level", "lich", "toll", "bell", "tablebell", "cardwin", "cardlose", "death"]);
  const recent = new Map();
  const p0 = A.play; A.play = function (name, volume = 1, pan = 0, rate = 1) {
    if (!this.ctx || !this.enabled) return p0.call(this, name, volume, pan, rate);
    const now = this.ctx.currentTime, L = (recent.get(name) || []).filter((t) => now - t < 0.15); if (L.length >= 4) return; L.push(now); recent.set(name, L);
    const crowd = L.length >= 3 ? 0.6 : 1;
    if (!FIXED.has(name)) { rate *= 1 + (Math.random() - 0.5) * 0.08; volume *= 0.92 + Math.random() * 0.1; }
    return p0.call(this, name, volume * crowd, pan, rate); };
  // the outputs: a compressor each, and the duckers
  const st = { dialog: false, fallUntil: 0, quietUntil: 0, king: false, music: 1, amb: 1 };
  const holds = new Map(); CM.mixHold = (id, music, amb, ms) => { holds.set(id, { music, amb, until: performance.now() + (ms || 1000) }); };   // (another file's moment: music and ambience at most these, for a while)
  CM.mixState = () => Object.assign({}, st, { installed: Boolean(A._mixed) });
  const comp = (ctx) => { const c = ctx.createDynamicsCompressor(); c.threshold.value = -14; c.knee.value = 12; c.ratio.value = 3; c.attack.value = 0.006; c.release.value = 0.25; c.connect(ctx.destination); return c; };
  const install = () => { if (A._mixed || !A.ctx || !A.master) return false; const ctx = A.ctx;
    try { A.master.disconnect(); A._comp = comp(ctx); A.master.connect(A._comp);
      const amb = CM.ambienceOut ? CM.ambienceOut() : null; if (amb && amb !== A.master) { amb.disconnect(); A._ambDuck = ctx.createGain(); amb.connect(A._ambDuck); A._ambDuck.connect(A.master); }
      A._mixed = true; return true; } catch (e) { try { A.master.connect(ctx.destination); } catch (e2) { /* (as it was) */ } return false; } };
  const installMusic = () => { const M = CM.music; if (!M || !M.master || M._mixed || !A.ctx) return false; const ctx = A.ctx;
    try { M.master.disconnect(); M._duck = ctx.createGain(); M._comp = comp(ctx); M.master.connect(M._duck); M._duck.connect(M._comp); M._mixed = true; return true; } catch (e) { try { M.master.connect(ctx.destination); } catch (e2) { /* */ } return false; } };
  // what the mix wants, a few times a second
  const tick = () => { install(); installMusic(); const ctx = A.ctx; if (ctx) { const now = performance.now(), g = CM.game, ui = CM.ui;
      st.dialog = Boolean(ui && ui.dialogOpen && ui.dialogOpen() && g && g.mode !== "title");
      st.king = Boolean(g && g.floor && g.floor.number === CM.LAST_FLOOR && g.mode === "explore");
      let music = 1, amb = 1; if (st.dialog) { music = Math.min(music, 0.55); amb = Math.min(amb, 0.6); } if (st.king) music = Math.min(music, 0.35);
      if (now < st.fallUntil) music = Math.min(music, 0.08); for (const [id, H] of holds) { if (now > H.until) { holds.delete(id); continue; } music = Math.min(music, H.music); amb = Math.min(amb, H.amb); } if (now < st.quietUntil) music = Math.min(music, 0.0);
      const ease = (node, want, was) => { if (!node) return; node.gain.setTargetAtTime(want, ctx.currentTime, want < was ? 0.18 : 0.6); };
      if (CM.music && CM.music._duck && Math.abs(music - st.music) > 0.001) { ease(CM.music._duck, music, st.music); st.music = music; }
      if (A._ambDuck && Math.abs(amb - st.amb) > 0.001) { ease(A._ambDuck, amb, st.amb); st.amb = amb; } }
    setTimeout(tick, 150); };
  setTimeout(tick, 500);
  // the moments: a hero falls; a new band begins
  const bind = () => { const g = CM.game; if (!g || !g.on) return false; let down = new Set();
    g.on("change", () => { if (!g.party || g.replaying) return; for (const h of g.party) { if (h.hp <= 0 && !down.has(h)) { down.add(h); if (g.mode === "combat" || g.mode === "explore") st.fallUntil = performance.now() + 3500; } else if (h.hp > 0) down.delete(h); } });
    g.on("floor", (fl) => { if (!fl || !(fl.number >= 1) || g.replaying) return; const b = CM.themeIndex(fl.number), key = `${g.seed}:${g.startedAt || ""}:${b}`; if (!seen.has(key)) { seen.add(key); st.quietUntil = performance.now() + 1500; } });
    return true; };
  const seen = new Set();
  if (!bind()) { const t = setInterval(() => { if (bind()) clearInterval(t); }, 300); }
} }
