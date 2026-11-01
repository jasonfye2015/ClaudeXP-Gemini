"use strict";
// Seeds from everywhere, the window's side (v19.3): the charmed crops glow in the field (each its own colour, breathing)
// and on the board; the rules are 69m-fieldseeds.js.
{ const FS = CM.FIELDSEEDS;
  { const ps0 = CM.plotSprites; CM.plotSprites = (game, key, x, y) => { const out = ps0(game, key, x, y), P = game.fields().plots[key], C = P && P.crop && FS.CHARMED[P.crop]; if (!C) return out;
      const t = (typeof performance !== "undefined" ? performance.now() : 0) / 700; for (const s of out) if (String(s.layer).startsWith("crop:")) s.glow = 0.25 + 0.15 * Math.sin(t + x * 0.7 + y); return out; }; }
  const rf0 = CM.UI.prototype.renderFields;
  CM.UI.prototype.renderFields = function () { rf0.call(this); const g = this.game, box = this.$("#fd-body"); if (!box || g.fieldsLevel() < 1) return; const F = g.fields();
    box.querySelectorAll("[data-fd]").forEach((b) => { const P = F.plots[b.dataset.fd], C = P && P.crop && FS.CHARMED[P.crop]; if (C) { b.classList.add("charmed"); b.style.setProperty("--glow", C.glow); } }); };
}
