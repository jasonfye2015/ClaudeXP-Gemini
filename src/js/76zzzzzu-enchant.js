"use strict";
// Enchanting at the Mage Tower - the window's side (v32.1): the enchanter's corner of the Tower's doors: the pack's
// gear, each with the words she offers to add and those she can raise, the shards and gold each costs and the chance it
// takes; and a guardian's relic broken into shards. The rules: 69za-enchant.js.
{ const om0 = CM.UI.prototype.openMageTower;
  CM.UI.prototype.openMageTower = function (...a) {
    const out = om0.apply(this, a), g = this.game, dlg = this.$("#dlg-magetower .box"); if (!dlg || !g.towerOffers) return out;
    let box = dlg.querySelector(".enchanter"); if (box) box.remove(); box = document.createElement("div"); box.className = "enchanter";
    const TC = CM.TOWERCRAFT, pct = (k) => `${Math.round(k * 100)}%`;
    let h = `<div class="list-title">The enchanter</div><p class="lore">A woman in grey sits on the step with a lap-desk of silver wire. "Shards," she says. "I make words out of what's left of old power. It doesn't always take."</p>`
      + `<p class="small">Relic shards in the pack: <b>${g.shards()}</b>. A word added: ${TC.add.shards} shards and ${TC.add.gold} gold; a word raised a tier: ${TC.raise.shards} shards and ${TC.raise.gold} gold a tier. If it fails the shards are spent; now and then the thing cracks and loses a word.</p>`;
    const rows = g.bag.map((it, i) => [it, i]).filter(([, i]) => { const O = g.towerOffers(i); return O.add.length || O.raise.length; });
    if (!rows.length) h += `<p class="small">Nothing in the pack she can work on: worn gear without a unique's or a relic's nature.</p>`;
    for (const [it, i] of rows) { const O = g.towerOffers(i), ca = g.towerChance(i, "add"), cr = g.towerChance(i, "raise");
      h += `<div class="entry"><b class="rarity-${CM.rarityOf(it)}">${this.esc(it.name)}</b><br>`;
      for (const [where, w] of O.add) { const why = g.towerWhy(i, "add", w); h += `<button data-tadd="${i}" data-w="${this.esc(w)}" ${why ? `disabled title="${this.esc(why)}"` : ""}>Add "${this.esc(w)}" (${pct(ca)})</button> `; }
      for (const w of O.raise) { const why = g.towerWhy(i, "raise", w); h += `<button data-traise="${i}" data-w="${this.esc(w)}" ${why ? `disabled title="${this.esc(why)}"` : ""}>Raise "${this.esc(w)}" (${pct(cr)})</button> `; }
      h += `</div>`; }
    const relics = g.bag.map((it, i) => [it, i]).filter(([it]) => (it.props || {}).relic);
    for (const [it, i] of relics) h += `<div class="entry"><button data-tbreak="${i}">Break ${this.esc(it.name)} into ${TC.relic} shards</button></div>`;
    h += `<div class="note" id="enchant-note">${this.esc(this.enchantNote || "")}</div>`; this.enchantNote = "";
    box.innerHTML = h; dlg.insertBefore(box, dlg.querySelector(".end") || null);
    const again = (msg) => { this.enchantNote = msg; this.openMageTower(); this.refresh(); };
    for (const b of box.querySelectorAll("[data-tadd]")) b.addEventListener("click", () => { const e = g.towerEnchant(Number(b.dataset.tadd), "add", b.dataset.w); again(e || ""); });
    for (const b of box.querySelectorAll("[data-traise]")) b.addEventListener("click", () => { const e = g.towerEnchant(Number(b.dataset.traise), "raise", b.dataset.w); again(e || ""); });
    for (const b of box.querySelectorAll("[data-tbreak]")) b.addEventListener("click", () => { const e = g.breakRelic(Number(b.dataset.tbreak)); again(e || ""); });
    return out; };
}
