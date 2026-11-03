"use strict";
// Brightness and contrast (v52.4, UPGRADE_PLAN_47.md): Settings has two sliders for the picture of the world itself - its
// brightness (from 60% to 160%: the dark floors lighter on a dim screen, or darker in a bright room) and its contrast
// (from 70% to 140%) - beside the text size and the high contrast that were there. The windows and the words are left
// as they are; only the view changes. Kept with the other settings.
{ if (typeof document !== "undefined" && !(typeof self !== "undefined" && self.CM_WORKER)) {
  const apply = () => { const s = CM.game && CM.game.settings; if (!s) return; const b = s.viewBright === undefined ? 1 : s.viewBright, c = s.viewContrast === undefined ? 1 : s.viewContrast; const cv = CM.renderer && CM.renderer.canvas;
    if (cv) cv.style.filter = b === 1 && c === 1 ? "" : `brightness(${b}) contrast(${c})`; };
  CM.applyPicture = apply;
  const ROWS = [["viewBright", "Brightness of the view", 60, 160], ["viewContrast", "Contrast of the view", 70, 140]];
  const wire = () => { const ui = CM.ui, g = CM.game; if (!ui || !g || !ui.$) return false; const anchor = ui.$("#set-contrast"); if (!anchor) return false; apply(); if (ui.$("#set-viewBright")) return true; let after = anchor.closest(".row");
    for (const [key, label, lo, hi] of ROWS) { const r = document.createElement("div"); r.className = "row"; r.innerHTML = `<label for="set-${key}">${label} <span class="small" data-v></span></label><input type="range" id="set-${key}" min="${lo}" max="${hi}">`; after.insertAdjacentElement("afterend", r); after = r;
      const inp = r.querySelector("input"), v = r.querySelector("[data-v]"), show = () => { v.textContent = `${inp.value}%`; }; inp.value = Math.round((g.settings[key] === undefined ? 1 : g.settings[key]) * 100); show();
      inp.addEventListener("input", () => { g.settings[key] = inp.value / 100; show(); apply(); if (g.saveSettings) g.saveSettings(); }); }
    return true; };
  const t = setInterval(() => { if (wire()) clearInterval(t); }, 300); } }
