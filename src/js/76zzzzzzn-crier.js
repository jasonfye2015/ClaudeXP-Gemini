"use strict";
// The news board - the window's side (v36.4): The Caer Duin Crier, a broadsheet on old paper - its masthead, the week,
// the headline and its columns - opened from "The Crier" among the town's actions and from the court's noticeboard; the
// last eight weeks' sheets turned with the arrows. Rules: 69zv-crier.js.
{ const make = (ui) => { if (ui.$("#dlg-crier")) return; const d = document.createElement("div"); d.className = "dialog"; d.id = "dlg-crier";
    d.innerHTML = `<div class="box" style="max-width:700px;background:linear-gradient(170deg,#EADBB8,#D4BE90);color:#2A1C10"><div class="crier"></div><div class="end"><button data-cw="1">&#9664; Older</button><button data-cw="-1">Newer &#9654;</button><button class="close">Close</button></div></div>`;
    ui.$("#dlg-magetower").parentNode.appendChild(d); d.querySelector(".close").addEventListener("click", () => ui.closeDialogs());
    for (const b of d.querySelectorAll("[data-cw]")) b.addEventListener("click", () => { ui.crierAt = Math.max(0, Math.min(7, (ui.crierAt || 0) + Number(b.dataset.cw))); ui.openCrier(); }); };
  CM.UI.prototype.openCrier = function () { make(this); const g = this.game, W = g.crierWeeks(), C = g.crier(W[this.crierAt || 0]), d = this.$("#dlg-crier");
    d.querySelector(".crier").innerHTML = `<div style="text-align:center;border-bottom:3px double #5A3A1E;padding-bottom:6px;margin-bottom:8px"><div style="font:bold 34px Georgia,serif;letter-spacing:2px">The Caer Duin Crier</div><div style="font:italic 12px Georgia">The week of ${this.esc(C.week)} - one copper, or read it on the board for nothing</div></div>
      <div style="font:bold 22px Georgia;text-align:center;margin:6px 0 10px">${this.esc(C.headline)}</div><div style="columns:2;column-gap:20px;font:14px/1.4 Georgia">${C.items.map(([h, t]) => `<div style="break-inside:avoid;margin-bottom:10px"><b style="font-variant:small-caps;font-size:15px">${this.esc(h)}</b><br>${this.esc(t)}</div>`).join("")}</div>`;
    for (const b of d.querySelectorAll("[data-cw]")) b.disabled = (b.dataset.cw === "1" && (this.crierAt || 0) >= 7) || (b.dataset.cw === "-1" && !(this.crierAt || 0));
    this.openDialog("#dlg-crier"); };
  CM.addAction(["explore"], "The Crier", (ui) => { ui.crierAt = 0; ui.openCrier(); }, (ui) => Boolean(ui.game.inTown && ui.game.inTown()));
  const ocb = CM.UI.prototype.openCourtBoard; if (ocb) CM.UI.prototype.openCourtBoard = function (...a) { const out = ocb.apply(this, a), d = this.$("#dlg-courtboard .ck-body"); if (d && !d.querySelector(".crierlink")) { const b = document.createElement("button"); b.className = "crierlink"; b.textContent = "This week's Crier, pinned in the corner"; b.addEventListener("click", () => { this.crierAt = 0; this.openCrier(); }); d.prepend(b); } return out; };
}
