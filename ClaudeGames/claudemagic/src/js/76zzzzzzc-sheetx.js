"use strict";
// A hero's sheet, more of it (v34.1): CM.sheetExtra(fn) - fn(ui, hero) gives HTML laid at the foot of the sheet's
// right side, for the window files' own (rivals now; scars and letters after). The rival's line: who, and the score.
{ const extras = []; CM.sheetExtra = (fn) => extras.push(fn);
  const rs0 = CM.UI.prototype.renderSheet;
  CM.UI.prototype.renderSheet = function (...a) { const out = rs0.apply(this, a), g = this.game, h = g.party[this.sheetOf], right = this.$("#sheet-right"); if (!h || !right) return out;
    for (const fn of extras) { try { const html = fn(this, h); if (html) right.insertAdjacentHTML("beforeend", html); } catch (er) { /* a picture only */ } }
    return out; };
  CM.sheetExtra((ui, h) => { const g = ui.game, r = g.rivalOf && g.rivalOf(h), K = g.heroKills || {}; const kills = K[h.name] || 0;
    return (r ? `<div class="list-title">Rival</div><div class="boons"><div><b>Keeping score</b> - with ${ui.esc(r.name)}: ${kills} to ${K[r.name] || 0}; a weak spot found a twentieth more often while they stand</div></div>` : "")
      + (kills ? `<div class="small">Killing blows this run: ${kills}.</div>` : ""); });
}
