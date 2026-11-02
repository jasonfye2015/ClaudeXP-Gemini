"use strict";
// Brewing at the still - the window's side (v32.2): the fields' still shows the book's recipes found so far, each
// a button when the pack holds its two; and the Journal's Recipes page gets the still's half. Rules: 69zb-stillbook.js.
{ const rf0 = CM.UI.prototype.renderFields;
  CM.UI.prototype.renderFields = function (...a) { const out = rf0.apply(this, a), g = this.game, box = this.$("#fd-body"); if (!box || !g.stillKnown || g.fieldsLevel() < 1) return out;
    const K = g.stillKnown(), ids = Object.keys(CM.STILLBOOK).filter((id) => K[id]); const old = box.querySelector(".stillbook"); if (old) old.remove();
    const el = document.createElement("div"); el.className = "stillbook"; const SB = CM.STILLBOOK;
    el.innerHTML = `<div class="list-title">The still's book (${ids.length} of ${Object.keys(SB).length} pages)</div>` + (ids.length ? ids.map((id) => { const why = g.stillBrewWhy(id);
      return `<button data-sb="${id}" ${why ? `disabled title="${this.esc(why)}"` : ""}>${this.esc(SB[id].name)} <small>(${this.esc(CM.CROPS[SB[id].crop].name.toLowerCase())} and ${this.esc(CM.INGREDIENTS[SB[id].ing].name.toLowerCase())}: ${this.esc(SB[id].what)})</small></button>`; }).join(" ")
      : `<p class="small">No pages yet. They turn up in chests below the first floor, and on fallen alchemists.</p>`);
    const at = box.querySelector(".fduse"); if (at) at.after(el); else box.appendChild(el);
    el.querySelectorAll("[data-sb]").forEach((b) => b.addEventListener("click", () => { this.fdNote = g.stillBrew(b.dataset.sb) || ""; this.renderFields(); this.refresh && this.refresh(); }));
    return out; };
  CM.journalPage("stillbook", "Still book", "The still's recipes: pages found in the dungeon", (ui, box) => { const g = ui.game, K = g.stillKnown(), SB = CM.STILLBOOK, ids = Object.keys(SB);
    box.innerHTML = `<div class="list-title">The still's book: ${ids.filter((id) => K[id]).length} of ${ids.length} pages</div><p class="small">Pages lie in chests below the first floor and among fallen parties' remains; a page is written in the moment it is found. At the still in the fields' shed, a crop and a band's ingredient make what the page says - no gold.</p>`
      + ids.map((id) => K[id] ? `<div class="entry"><b>${ui.esc(SB[id].name)}</b><br><small>${ui.esc(CM.CROPS[SB[id].crop].name)} and ${ui.esc(CM.INGREDIENTS[SB[id].ing].name)}: ${ui.esc(SB[id].what)}</small></div>` : `<div class="entry"><b>?</b><br><small>a page not yet found (from ${ui.esc(CM.THEMES[CM.INGREDIENTS[SB[id].ing].band] ? CM.THEMES[CM.INGREDIENTS[SB[id].ing].band].name : "the deep")} or above)</small></div>`).join(""); });
}
