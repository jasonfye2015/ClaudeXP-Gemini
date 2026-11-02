"use strict";
// Scars and stories - the window's side (v34.2): a hero's scars drawn on their portrait (a pale line with stitch
// marks; a burn a blotch), and the sheet's Scars - each with its place, its giver, its floor and its trait. The party's
// cards are drawn again when a scar is new. Rules: 69zj-scars.js.
{ const P = CM.UI.prototype, base = P.portrait, LINES = [[0.3, 0.3, 0.45, 0.42], [0.62, 0.48, 0.7, 0.66], [0.38, 0.7, 0.58, 0.74], [0.6, 0.26, 0.66, 0.4], [0.32, 0.5, 0.4, 0.58], [0.25, 0.36, 0.28, 0.5]];
  P.portrait = function (who, size) { const c = base.call(this, who, size); if (!who || typeof who === "string" || !(who.marks || []).length || !c.getContext) return c;
    const p = c.getContext("2d"), S = size; who.marks.forEach((s, i) => { const L = LINES[CM.SCAR_PLACES.indexOf(s.where) >= 0 ? CM.SCAR_PLACES.indexOf(s.where) : i % LINES.length];
      if (s.burn) { p.fillStyle = "rgba(150,60,50,0.55)"; p.beginPath(); p.ellipse(S * (L[0] + L[2]) / 2, S * (L[1] + L[3]) / 2, S * 0.07, S * 0.05, 0.4, 0, Math.PI * 2); p.fill(); return; }
      p.strokeStyle = "rgba(120,40,40,0.75)"; p.lineWidth = Math.max(1, S / 28); p.beginPath(); p.moveTo(S * L[0], S * L[1]); p.lineTo(S * L[2], S * L[3]); p.stroke();
      p.strokeStyle = "rgba(240,210,190,0.7)"; p.lineWidth = Math.max(1, S / 60); for (let k = 1; k < 4; k++) { const x = S * (L[0] + (L[2] - L[0]) * k / 4), y = S * (L[1] + (L[3] - L[1]) * k / 4); p.beginPath(); p.moveTo(x - S * 0.02, y + S * 0.015); p.lineTo(x + S * 0.02, y - S * 0.015); p.stroke(); } });
    return c; };
  let count = -1; const rf0 = P.refresh; P.refresh = function (...a) { const g = this.game; if (g && g.party) { const n = g.party.reduce((k, h) => k + (h.marks || []).length + (h.scars || []).length, 0); if (n !== count) { count = n; const box = this.$ && this.$("#party"); if (box) box.dataset.signature = ""; } } return rf0.apply(this, a); };
  CM.sheetExtra((ui, h) => (h.marks || []).length + (h.scars || []).length ? `<div class="list-title">Scars</div><div class="boons">${(h.scars || []).filter((s) => CM.SCARS[s]).map((s) => `<div><b>${ui.esc(CM.SCARS[s].name[0].toUpperCase() + CM.SCARS[s].name.slice(1))}</b> - from a wound healed: ${ui.esc(CM.SCARS[s].what)}</div>`).join("")}${(h.marks || []).map((s) => { const T = CM.SCAR_TRAITS[s.trait]; return `<div><b>${ui.esc(T.name)}</b> - a scar ${ui.esc(s.where)}, from ${ui.esc(s.by)} on floor ${s.floor}: ${ui.esc(T.what)}</div>`; }).join("")}</div>` : "");
}
