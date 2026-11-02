"use strict";
// New Game+ - the window's side (v33.2): once the Lich King has fallen, the new party's screen has "Again" (how many
// times again, to the highest won plus one) and the heirloom to carry down (one of the last crowning party's things);
// the side panel names the again-run. Rules: 69zf-again.js.
{ const oc0 = CM.UI.prototype.openCreate;
  CM.UI.prototype.openCreate = function (...a) { const out = oc0.apply(this, a), g = this.game, asc = this.$("#ascension"); if (!asc || !g.againMax) return out;
    const max = g.againMax(); let row = this.$("#again-row"); if (max < 1) { if (row) row.remove(); return out; }
    if (!row) { row = document.createElement("span"); row.id = "again-row"; asc.after(row); }
    const H = g.againHeirlooms();
    row.innerHTML = ` <label for="again" title="Set out again: the dungeon deeper and meaner each time, and one thing of the last crowning party's carried down">Again</label><select id="again"><option value="0">No</option>${Array.from({ length: max }, (_, i) => `<option value="${i + 1}">${i + 1}</option>`).join("")}</select>`
      + (H.length ? ` <label for="again-heir">Carry</label><select id="again-heir">${H.map((it, i) => `<option value="${i}">${this.esc(it.name)}</option>`).join("")}</select>` : "");
    return out; };
  const so0 = CM.UI.prototype.setOut;
  CM.UI.prototype.setOut = function (...a) { const sel = this.$("#again"), heir = this.$("#again-heir"), L = sel ? Number(sel.value) || 0 : 0;
    if (!L) return so0.apply(this, a);
    const g = this.game, ng = g.newGame; g.newGame = function (seed, chosen, kit, difficulty, mutators, mode, opts) { g.newGame = ng; return ng.call(this, seed, chosen, kit, difficulty, mutators, mode, Object.assign({}, opts || {}, { again: L, heirloom: heir ? Number(heir.value) || 0 : 0 })); };
    try { return so0.apply(this, a); } finally { g.newGame = ng; } };
}
