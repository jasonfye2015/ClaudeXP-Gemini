"use strict";
// Focus (v31.3, UPGRADE_PLAN_26.md): while a dialog is open the view behind it goes soft, and comes back sharp when it
// closes; when a boss or a guardian makes its entrance the focus is pulled onto it - all else soft, then the room
// coming back into focus as the entrance ends. renderer.screen.focus / focusAt / focusR (40-render.js's screen pass).
{ let soft = 0, pull = null;
  { const s0 = CM.bossStage; if (s0) CM.bossStage = (K, fx) => { const out = s0(K, fx); if (out && fx && fx.foe && !CM.reducedMotion) pull = { foe: fx.foe, K, t0: performance.now(), ms: CM.STAGE_MS * (CM.cinematic ? 1.4 : 1) }; return out; }; }
  const bf0 = CM.beforeFrame; CM.beforeFrame = (game, r, dt, now) => { if (bf0) bf0(game, r, dt, now);
    const ui = CM.ui, open = Boolean(ui && ui.dialogOpen && ui.dialogOpen() && ui.screen === "play");
    soft += ((open ? 0.85 : 0) - soft) * Math.min(1, dt * 7);
    let focus = soft, at = null, rad = 0;
    if (pull) { const e = (performance.now() - pull.t0) / pull.ms; if (e >= 1 || game.mode !== "combat") pull = null;
      else { const w = pull.K.atFoe ? pull.K.atFoe(pull.foe, 0.55) : null, m = r.viewProj;
        if (w && m) { const cx = m[0] * w[0] + m[4] * w[1] + m[8] * w[2] + m[12], cy = m[1] * w[0] + m[5] * w[1] + m[9] * w[2] + m[13], cw = m[3] * w[0] + m[7] * w[1] + m[11] * w[2] + m[15];
          if (cw > 0.1) { at = [cx / cw * 0.5 + 0.5, cy / cw * 0.5 + 0.5]; rad = 0.16 + 0.1 * e; focus = Math.max(focus, e < 0.65 ? 1 : 1 - (e - 0.65) / 0.35); } } } }
    const S = r.screen || (r.screen = {}); S.focus = CM.reducedMotion && !open ? 0 : focus; S.focusAt = at; S.focusR = rad; };
}
