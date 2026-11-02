"use strict";
// The pony's gear - the window's side (v35.2): the farm's window fits it. Rules: 69zo-ponygear.js.
{ const of0 = CM.UI.prototype.openFarm;
  CM.UI.prototype.openFarm = function (...a) { const out = of0.apply(this, a), g = this.game, more = this.$("#farm-more"); if (!more || !g.ponyGear || !g.petName("pony")) return out;
    let box = more.querySelector(".ponygear"); if (box) box.remove(); box = document.createElement("div"); box.className = "ponygear"; box.innerHTML = `<div class="list-title">${this.esc(g.petName("pony"))}'s gear</div>`;
    for (const [id, T] of Object.entries(CM.PONY_GEAR)) { const row = document.createElement("div"); row.className = "recruit"; row.style.gridTemplateColumns = "1fr auto"; const has = g.ponyGear()[id], why = g.buyPonyGearWhy(id);
      row.innerHTML = `<div><b>${this.esc(T.name)}</b> <small>${this.esc(T.what)}</small></div>`; const b = document.createElement("button"); b.textContent = has ? "Fitted" : `${T.gold} gold`; b.disabled = Boolean(why); if (why && !has) b.title = why;
      b.addEventListener("click", () => { this.$("#farm-note").textContent = g.buyPonyGear(id) || "Fitted."; this.openFarm(); this.refresh(); }); row.appendChild(b); box.appendChild(row); }
    more.appendChild(box); return out; };
}
