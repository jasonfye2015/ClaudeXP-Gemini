"use strict";
// Entrances (v23.2, UPGRADE_PLAN_18.md): a boss or a guardian enters on a stage. Black bars close in from above and
// below, the camera leans in on it while it rises from the floor, its name comes up in a banner with where it rules,
// and a sting of music sounds. Any key or a click skips it; the fight waits (the automatic hand too, by holdUntil)
// until it is done. Settings > Combat speed sets how long: Cinematic longer, Quick shorter, As good as instant only the
// banner. 80-main.js's "intro" asks here first (CM.bossStage).
{ let ending = null;
  CM.STAGE_MS = 2600;
  CM.bossStage = (K, fx) => {
    const foe = fx.foe; if (!foe || !K || !K.renderer || !K.renderer.ok) return false;
    const G = foe.guardian ? CM.GUARDIANS[foe.guardian] : null, sub = G ? (foe.echo ? "an echo, in " : "in ") + G.lair.name : "in his palace";
    const quick = CM.fxSpeed || 1, card = K.ui.$("#view .titlecard");
    if (card) card.classList.add("staged");
    K.ui.titleCard(foe.name, sub);
    if (CM.music && CM.music.motif) CM.music.motif("entrance");
    if (quick >= 6 || CM.reducedMotion) { K.renderer.punch(); return true; }   // (instant, or motion reduced: the banner and the sting only)
    if (ending) ending();
    const view = K.ui.$("#view"); let bars = view.querySelector(".letterbox");
    if (!bars) { bars = document.createElement("div"); bars.className = "letterbox"; bars.innerHTML = '<span class="skip">any key or a click to go on</span>'; view.appendChild(bars); }
    const ms = CM.STAGE_MS * (CM.cinematic ? 1.4 : 1) / (quick >= 2 ? 1.6 : 1), t0 = performance.now();
    K.fxs.holdUntil = Math.max(K.fxs.holdUntil, t0 + ms);
    K.renderer.zoomTo(0.8, ms * 0.85); K.renderer.shake(0.3);
    setTimeout(() => { if (ending === end) { K.renderer.shake(0.45); K.renderer.punch(); } }, ms * 0.35);
    void bars.offsetWidth; bars.classList.add("on"); view.classList.add("staging");
    const key = (e) => { e.preventDefault(); e.stopPropagation(); end(); };
    const end = () => { if (ending !== end) return; ending = null; bars.classList.remove("on"); view.classList.remove("staging"); window.removeEventListener("keydown", key, true); bars.removeEventListener("pointerdown", key);
      clearTimeout(timer); K.fxs.holdUntil = performance.now(); if (K.renderer.zoomAnim) { K.renderer.zoomAnim = null; K.renderer.zoomNow = 1; } if (card) setTimeout(() => card.classList.remove("staged"), 900); };
    ending = end;
    window.addEventListener("keydown", key, true); bars.addEventListener("pointerdown", key);
    const timer = setTimeout(end, ms);
    return true;
  };
  CM.bossStaging = () => Boolean(ending);
  // the sting: a low drum and a rising minor chord in brass-ish saws, under the banner
  const m0 = CM.music && CM.music.motif;
  if (m0) CM.music.motif = function (name) {
    if (name !== "entrance") return m0.call(this, name);
    if (!this.enabled || !this._ensure()) return false;
    const ctx = CM.audio.ctx, at = ctx.currentTime + 0.05, dest = this.master;
    this._osc("sine", 55, at, at + 0.9, 0.35, 400, dest); this._osc("sine", 41.2, at + 0.5, at + 1.6, 0.3, 300, dest);
    [[0, 0], [3, 0.18], [7, 0.36], [12, 0.62]].forEach(([semi, dt]) => { const hz = 146.8 * Math.pow(2, semi / 12); this._osc("sawtooth", hz, at + dt, at + 1.9, 0.07, 1400, dest); this._osc("square", hz / 2, at + dt, at + 1.9, 0.035, 700, dest); });
    return true;
  };
}
