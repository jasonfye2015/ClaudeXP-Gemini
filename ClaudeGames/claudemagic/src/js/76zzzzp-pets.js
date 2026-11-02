"use strict";
// A dog and a pony, the window's side (v27.2): at the farm, a pup from the litter and the farm's pony, for gold; the
// side panel names them. The rules are 69x-pets.js.
{ const PT = CM.PETS;
  const of0 = CM.UI.prototype.openFarm;
  CM.UI.prototype.openFarm = function (...a) {
    const out = of0.apply(this, a), g = this.game, more = this.$("#farm-more"); if (!more || !g.pets) return out;
    let box = more.querySelector(".pets"); if (box) box.remove(); box = document.createElement("div"); box.className = "pets";
    box.innerHTML = `<div class="list-title">Your own animals</div>`;
    for (const [kind, what] of [["dog", "A pup from the litter: it comes everywhere, growls at traps, scratches at hidden doors, and digs on the land by day."], ["pony", "The farm's pony: thirty more carried and quicker feet on the land; it waits at the shaft's head."]]) {
      const row = document.createElement("div"); row.className = "recruit"; row.style.gridTemplateColumns = "1fr auto"; const have = g.petName(kind);
      row.innerHTML = `<div><b>${have ? this.esc(have) : kind === "dog" ? "A hound" : "A pony"}</b> <small>${this.esc(what)}</small></div>`;
      const b = document.createElement("button"); b.textContent = have ? "Yours" : `${PT[kind].price} gold`; b.disabled = Boolean(have) || g.gold < PT[kind].price;
      b.addEventListener("click", () => { const why = g.buyPet(kind); this.$("#farm-note").textContent = why || `${g.petName(kind)} is yours.`; this.openFarm(); this.refresh(); });
      row.appendChild(b); box.appendChild(row); }
    more.appendChild(box); return out;
  };
  // the side panel: who comes along
  const rf0 = CM.UI.prototype.refresh;
  CM.UI.prototype.refresh = function (...a) { const out = rf0.apply(this, a), g = this.game, fo = this.$ && this.$("#side .follower"); if (fo && g && g.pets && g.mode !== "title") {
      const dog = g.petName("dog"), pony = g.petName("pony"), deep = g.floor && CM.isDeep(g.floor.number), bits = [];
      if (dog) bits.push(`${dog} at heel`); if (pony) bits.push(deep ? `${pony} waiting above` : `${pony} on the lead`);
      let el = this.$("#side .pets"); if (!el) { el = document.createElement("div"); el.className = "pets small"; fo.insertAdjacentElement("afterend", el); } el.textContent = bits.join(" - "); }
    return out; };
}
