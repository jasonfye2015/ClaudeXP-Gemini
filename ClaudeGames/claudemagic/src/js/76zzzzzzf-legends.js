"use strict";
// Legends' Row - the window's side (v34.4): in town, "Legends' Row" among the actions: the houses of the retired - each
// legend's door with their name, calling, level and day, and a hero of the party to send in for a lesson - and the
// heroes of level fifty or more who could retire there. Rules: 69zl-legends.js.
{ const make = (ui) => { if (ui.$("#dlg-legends")) return; const d = document.createElement("div"); d.className = "dialog"; d.id = "dlg-legends";
    d.innerHTML = `<div class="box journalbox"><h2>Legends' Row</h2><p class="lore">A short street of good stone houses off the Square, each with a name over its door. The town keeps them for those who went down further than anyone, and came back.</p><div class="legends"></div><div class="note" id="legends-note"></div><div class="end"><button class="close">Close</button></div></div>`;
    ui.$("#dlg-magetower").parentNode.appendChild(d); d.querySelector(".close").addEventListener("click", () => ui.closeDialogs()); };
  CM.UI.prototype.openLegends = function (note) { make(this); const g = this.game, box = this.$("#dlg-legends .legends"), L = g.legends(); let h = "";
    h += L.length ? L.map((Lg, li) => `<div class="recruit" style="grid-template-columns:auto 1fr auto"><div class="pslot" data-li="${li}"></div><div><b>${this.esc(Lg.name)}</b> the ${this.esc(Lg.cls)}, level ${Lg.level}<br><small>retired ${this.esc(Lg.date)}${Lg.scars ? `, ${Lg.scars} scar${Lg.scars === 1 ? "" : "s"}` : ""}; teaches +1 ${this.esc(CM.STAT_NAMES[(CM.CLASSES[Lg.cls] || {}).key || "str"])}${Lg.boon ? `, and a ${this.esc(Lg.cls)} their first boon` : ""}, once a run${(Lg.taught || {})[g.seed] ? ` - taught ${this.esc(Lg.taught[g.seed])} this run` : ""}</small></div><div><select data-teach="${li}"><option value="">Send in...</option>${g.party.map((p, hi) => p.hp > 0 ? `<option value="${hi}">${this.esc(p.name)}</option>` : "").join("")}</select></div></div>`).join("")
      : `<p class="small">The houses stand empty. A hero of level ${CM.LEGEND_AT} or more may retire here.</p>`;
    const can = g.party.map((p, i) => [p, i]).filter(([p]) => p.level >= CM.LEGEND_AT);
    if (can.length) h += `<div class="list-title">Ready to retire</div>` + can.map(([p, i]) => { const why = g.retireLegendWhy(i); return `<button data-retire="${i}" ${why ? `disabled title="${this.esc(why)}"` : ""}>${this.esc(p.name)} the ${this.esc(p.cls)} (level ${p.level}) takes a house</button>`; }).join(" ");
    box.innerHTML = h; this.$("#legends-note").textContent = note || "";
    for (const s of box.querySelectorAll("[data-li]")) { const Lg = L[Number(s.dataset.li)]; const c = this.portrait(Lg.cls, 40); s.appendChild(c); }
    for (const s of box.querySelectorAll("[data-teach]")) s.addEventListener("change", () => { if (s.value === "") return; const e = g.legendTeach(Number(s.dataset.teach), Number(s.value)); this.openLegends(e || "A lesson given."); this.refresh(); });
    for (const b of box.querySelectorAll("[data-retire]")) b.addEventListener("click", () => { const e = g.retireLegend(Number(b.dataset.retire)); this.openLegends(e || ""); this.refresh(); });
    this.openDialog("#dlg-legends"); };
  CM.addAction(["explore"], "Legends' Row", (ui) => ui.openLegends(), (ui) => ui.game.inTown && ui.game.inTown());
}
