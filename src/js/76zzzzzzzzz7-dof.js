"use strict";
// Depth of field, deeper (v52.2, UPGRADE_PLAN_47.md): the view behind an open window (soft since v31.3, 76zzzzzl-focus.js)
// goes fully out of focus now and draws back into shadow at its edges, so the window stands clearly in front of the world
// and the world clearly behind it; it comes back sharp as the window closes.
{ const bf0 = CM.beforeFrame; CM.beforeFrame = (game, r, dt, now) => { if (bf0) bf0(game, r, dt, now); const S = r.screen; if (!S || S.focusAt) return; if (S.focus > 0.05) S.focus = Math.min(1, S.focus / 0.85); };
  if (typeof document !== "undefined" && !(typeof self !== "undefined" && self.CM_WORKER)) { const install = () => { if (document.getElementById("cm-dof")) return; const s = document.createElement("style"); s.id = "cm-dof";
      s.textContent = ".dialog.on { background: radial-gradient(ellipse at center, rgba(0,0,0,0.35) 0%, rgba(0,0,0,0.55) 55%, rgba(0,0,0,0.82) 100%); }"; document.head.appendChild(s); };
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", install); else install(); } }
