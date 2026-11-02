"use strict";
// Cooking, wider - the window's side (v32.0): the feast's table where the dishes are made (a camp's fire, the home's
// kitchen) whenever the pack holds two different dishes; and the Journal's Recipes page - every dish, those made
// named with what they need and do, the rest a blank with their first need for a hint. The rules: 69z-cooking2.js.
{ const db0 = CM.UI.prototype.dishButtons;
  CM.UI.prototype.dishButtons = function (into, run) {
    const out = db0.call(this, into, run), g = this.game, rows = g.bag.map((it, i) => [it, i]).filter(([it]) => it.kind === "dish" && CM.DISHES[it.dish]);
    const kinds = new Set(rows.map(([it]) => it.dish)), atTable = g.mode === "camp" || (g.inTown() && g.homeLevel && g.homeLevel() >= 3); if (kinds.size < 2 || !atTable) return out;
    const box = document.createElement("div"); box.className = "feast"; box.innerHTML = `<div class="list-title">A feast</div><div class="small">Two or three different dishes eaten together: all their good at once, for as long as the shortest lasts.</div>`;
    const seen = new Set(), picks = [];
    for (const [it, i] of rows) { if (seen.has(it.dish)) continue; seen.add(it.dish); const l = document.createElement("label"); l.className = "small"; l.style.display = "block";
      l.innerHTML = `<input type="checkbox" data-row="${i}"> ${this.esc(it.name)} - ${this.esc(CM.DISHES[it.dish].what)}`; box.appendChild(l); picks.push(l.querySelector("input")); }
    const b = document.createElement("button"); b.textContent = "Lay the feast"; b.disabled = true; box.appendChild(b);
    const sync = () => { const on = picks.filter((p) => p.checked); b.disabled = on.length < 2 || on.length > CM.FEAST_MOST; for (const p of picks) p.disabled = !p.checked && on.length >= CM.FEAST_MOST; };
    for (const p of picks) p.addEventListener("change", sync);
    b.addEventListener("click", () => run(() => g.layFeast(picks.filter((p) => p.checked).map((p) => Number(p.dataset.row)))));
    into.appendChild(box); return out; };
  CM.journalPage("recipes", "Recipes", "Every dish there is: those made, with what they need and do", (ui, box) => {
    const g = ui.game, known = g.recipesKnown(), all = Object.keys(CM.DISHES), ids = all.filter((id) => known[id]).concat(all.filter((id) => !known[id])), n = ids.filter((id) => known[id]).length;
    box.innerHTML = `<div class="list-title">The recipe book: ${n} of ${ids.length} made</div><p class="small">A dish is written in the first time it is made. Dishes are made at a camp's fire, the home's kitchen, or on the floor by a cook of the third level; two or three different ones eaten together at a camp or at home make a feast.</p>` +
      ids.map((id) => { const D = CM.DISHES[id], can = CM.canCook(g.bag, id); return known[id] ? `<div class="entry"><b>${ui.esc(D.name)}</b>${can ? " <small>(the pack has it all)</small>" : ""}<br><small>${ui.esc(D.needs.map(CM.needName).join(", "))} - ${ui.esc(D.what)}, ${CM.plural(D.floors, "floor")}</small></div>`
        : `<div class="entry"><b>?</b><br><small>${D.needs.length === 1 ? `one thing: ${ui.esc(CM.needName(D.needs[0]))}` : `${ui.esc(CM.needName(D.needs[0]))}, and ${["", "one", "two", "three"][D.needs.length - 1]} thing${D.needs.length > 2 ? "s" : ""} more`}${can ? " - the pack has what it needs" : ""}</small></div>`; }).join(""); });
}
