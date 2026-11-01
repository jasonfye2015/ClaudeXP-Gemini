"use strict";
// The ways between, the window's side: the smith's island tempering - a row at the foot of the smith's list for each
// worn weapon and armour, with what it wants (a bar, an essence, the fee) and why not, if not. The rules are
// 64zzza-links.js.
{ const rs0 = CM.UI.prototype.renderSmith;
  CM.UI.prototype.renderSmith = function () { rs0.call(this); const g = this.game, box = this.$("#smith-list"); if (!box || !g.islandTemper) return; const bars = g.bag.filter((x) => x.kind === "bar").length, ess = g.bag.filter((x) => x.kind === "essence").length;
    const sec = document.createElement("div"); sec.className = "temperbox"; sec.innerHTML = `<h4>Island tempering</h4><p class="small">A metal bar from the island (or the smelter) and an essence from the dungeon, worked together: +1 on a worn weapon or armour, once a piece, for ${CM.LINKS.temper.gold} gold. In the pack: ${CM.plural(bars, "bar")}, ${CM.plural(ess, "essence")}.</p>`;
    g.party.forEach((h, hi) => { for (const slot of ["weapon", "armor"]) { const it = h[slot]; if (!it || (it.props && it.props.fists)) continue; const why = g.islandTemperWhy(h, slot), row = document.createElement("div"); row.className = "recruit";
      row.innerHTML = `<div><b>${this.esc(it.unknown ? CM.baseName(it) : it.name)}</b> <small>${this.esc(h.name)}'s ${CM.SLOT_NAMES[slot].toLowerCase()}${it.props && it.props.tempered ? " - island-tempered" : ""}</small></div><div class="hire"><button ${why ? "disabled" : ""} title="${this.esc(why || "Temper it")}">${it.props && it.props.tempered ? "Tempered" : "Temper: +1"}</button></div>`;
      row.querySelector("button").addEventListener("click", () => { this.$("#smith-note").textContent = g.islandTemper(hi, slot) || `${it.name}: island-tempered, +1.`; this.renderSmith(); this.refresh && this.refresh(); }); sec.appendChild(row); } });
    box.appendChild(sec); };
}
