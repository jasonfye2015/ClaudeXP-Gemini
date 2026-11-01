"use strict";
// The South Fields, what they're for - the window's side (v19.4): under the board, the market stall (today's demand,
// what the pack and the silo would fetch, Sell), the Harvest Fair's contest when the fair is on (enter a crop, the
// judges' table), and the shed's still. The rules are 69n-fielduse.js.
{ const FU = CM.FIELDUSE, rf0 = CM.UI.prototype.renderFields;
  CM.UI.prototype.renderFields = function () { rf0.call(this); const g = this.game, box = this.$("#fd-body"); if (!box || g.fieldsLevel() < 1) return; const F = g.fields(), town = g.floor && g.floor.number === 0, here = g.atFields();
    const isProd = (it) => it && it.kind === "ingredient" && CM.CROPS[it.ingredient] && CM.CROPS[it.ingredient].price, worth = (list) => list.filter(isProd).reduce((n, it) => n + FU.price(g, it), 0);
    const demand = FU.demandFor(g), packN = g.bag.filter(isProd).length, siloN = (F.silo || []).filter(isProd).length;
    const fair = g.fairOpen(), entered = F.fairYear === FU.year(), entries = g.bag.map((it, i) => [it, i]).filter(([it]) => isProd(it)).sort((a, b) => FU.score(b[0]) - FU.score(a[0])).slice(0, 6);
    const stills = ["manablossom", "frostberry", "moonmelon", "coinbean", "jokerrose"].filter((c) => g.bag.some((it) => it.kind === "ingredient" && it.ingredient === c));
    const el = document.createElement("div"); el.className = "fduse";
    el.innerHTML = `<div><div class="list-title">The market stall (the Square)</div><p class="small">In demand today, at half as much again: <b>${demand.map((c) => this.esc(CM.CROPS[c].name)).join(", ")}</b>.</p>
        <p><button data-fdsell="pack" ${town && packN ? "" : "disabled"}>Sell the pack's ${packN} (${worth(g.bag)}g)</button> <button data-fdsell="silo" ${town && siloN ? "" : "disabled"}>Sell the silo's ${siloN} (${worth(F.silo || [])}g)</button></p>${F.marketGold ? `<p class="small">Sold at the stall so far: ${F.marketGold} gold.</p>` : ""}</div>
      <div><div class="list-title">The Harvest Fair's contest</div>${fair ? (entered ? `<p class="small">Your entry is in for this fair.</p>` : entries.length ? `<p class="small">One entry a fair, judged on its stars and its kind:</p>${entries.map(([it, i]) => `<button data-fdfair="${i}">${this.esc(it.name)} <small>(${FU.score(it)})</small></button>`).join(" ")}` : `<p class="small">Bring something from the fields to enter.</p>`) : `<p class="small">At the Harvest Fair, in September's fair week.${F.fairWins ? ` Blue ribbons: ${F.fairWins}.` : ""}</p>`}</div>
      <div><div class="list-title">The still</div>${stills.length ? stills.map((c) => `<button data-fdstill="${c}" ${here && !g.stillWhy(c) ? "" : "disabled"} title="${this.esc(g.stillWhy(c) || "")}">${this.esc({ manablossom: "Mana-blossom to a mana potion", frostberry: "Two frost-berries to a healing potion", moonmelon: "Moon-melon to wine", coinbean: "Crack a coin-bean pod", jokerrose: "A rose for the Joker (30 tickets)" }[c])}</button>`).join(" ") : `<p class="small">The charmed crops go in the still: mana-blossom, frost-berries, moon-melon, coin-beans, the Joker's roses.</p>`}</div>`;
    const at = box.querySelector(".fdhands") || box.querySelector(".fdcare") || box.querySelector(".fdgrid"); if (at) at.after(el);
    const done = (r) => { this.fdNote = r || ""; this.renderFields(); this.refresh && this.refresh(); };
    el.querySelectorAll("[data-fdsell]").forEach((b) => b.addEventListener("click", () => { const r = g.marketSell(b.dataset.fdsell); done(r.error || `Sold for ${r.gold} gold.`); }));
    el.querySelectorAll("[data-fdfair]").forEach((b) => b.addEventListener("click", () => { const r = g.fairEnter(Number(b.dataset.fdfair)); done(r.error || `Placed ${r.place}: ${r.table.map(([w, s]) => `${w} ${s}`).join(", ")}.`); }));
    el.querySelectorAll("[data-fdstill]").forEach((b) => b.addEventListener("click", () => done(g.still(b.dataset.fdstill)))); };
}
