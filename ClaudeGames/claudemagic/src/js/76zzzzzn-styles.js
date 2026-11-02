"use strict";
// Screen styles (v31.5, UPGRADE_PLAN_26.md): Settings > Screen style - Clean (as it was), Old monitor (a curved tube,
// scanlines, colour fringes), Watercolour (soft washes that bleed, pigment pooled at the edges, the paper's grain),
// Ink and parchment (sepia shades and inked lines on old paper), Crisp (sharpened). One more step of the screen pass
// (40-render.js: renderer.screen.style); the game itself is the same underneath.
{ const STYLES = { clean: 0, crt: 1, water: 2, ink: 3, crisp: 4 };
  CM.settingLater((ui) => CM.addSetting("set-style", "Screen style - a look over the whole view", [["clean", "Clean"], ["crt", "Old monitor"], ["water", "Watercolour"], ["ink", "Ink and parchment"], ["crisp", "Crisp"]], "style", "clean", ui));
  const bf0 = CM.beforeFrame; CM.beforeFrame = (game, r, dt, now) => { if (bf0) bf0(game, r, dt, now); const S = r.screen || (r.screen = {}); S.style = STYLES[(game.settings && game.settings.style) || "clean"] || 0; };
  { const rf0 = CM.UI.prototype.refresh; CM.UI.prototype.refresh = function (...a) { const out = rf0.apply(this, a); const r = CM.renderer; if (r && this.game && this.game.settings) { const S = r.screen || (r.screen = {}); S.style = STYLES[this.game.settings.style || "clean"] || 0; } return out; }; }   // (and in the other places, where the frame's hook isn't called)
}
