"use strict";
// The bag and the merchant.
Object.assign(CM.UI.prototype, {
  // ---- the bag and the merchant ----
  _bag() {
    const g = this.game;
    const give = this.$("#bag-give");
    for (let i = 0; i < 4; i++) {
      const b = document.createElement("button");
      b.addEventListener("click", () => { this.note(g.give(this.bagRow, i)); this.fillBag(); });
      give.appendChild(b);
    }
    this.$("#btn-buy").addEventListener("click", () => { this.note(g.buy(this.shopRow)); this.fillBag(); });
    this.$("#btn-sell").addEventListener("click", () => { this.note(g.sell(this.bagRow)); this.fillBag(); });
    this.$("#btn-sort").addEventListener("click", () => { g.sortBag(); this.bagRow = -1; this.fillBag(); });
    this.$("#btn-bag-done").addEventListener("click", () => g.closeBag());
    const filters = this.$("#bag-filters");
    for (const [id, F] of Object.entries(CM.BAG_FILTERS)) { const b = document.createElement("button"); b.textContent = F.name; b.dataset.filter = id; b.addEventListener("click", () => { this.bagFilter = id; this.bagRow = -1; this.fillBag(); }); filters.appendChild(b); }
  },

  note(text) { this.$("#bag-note").textContent = text || this.$("#bag-note").dataset.base; },

  openBag() {
    this.bagRow = this.shopRow = -1;
    this.show("bag");
    this.fillBag();
  },

  fillBag() {
    const g = this.game, shop = g.shopping;
    this.$("#bag-title").textContent = `${shop ? "The Merchant" : "Inventory"}   -   Gold: ${g.gold.toLocaleString()}`;
    this.$("#shop-list").style.display = shop ? "" : "none";
    this.$("#btn-buy").style.display = shop ? "" : "none";
    this.$("#btn-sell").style.display = shop ? "" : "none";
    const list = (el, head, items, selected, describe, onPick) => {
      el.innerHTML = `<div class="head">${head}</div>` + (items.length ? "" : `<div class="empty">Nothing here.</div>`);
      items.forEach((item, i) => {
        const row = document.createElement("div");
        row.className = "item" + (i === selected ? " sel" : "");
        row.appendChild(this.icon(item));
        const text = document.createElement("span");
        text.innerHTML = `<span class="rarity-${CM.rarityOf(item)}">${this.esc(item.unknown ? CM.baseName(item) : item.name)}</span> <span class="what">${describe(item)}</span>`;
        row.appendChild(text);
        row.addEventListener("click", () => { onPick(i); this.fillBag(); });
        el.appendChild(row);
      });
    };
    const F = CM.BAG_FILTERS[this.bagFilter || "all"], rows = g.bag.map((it, i) => i).filter((i) => !F.kinds || F.kinds.includes(g.bag[i].kind));
    for (const b of this.$("#bag-filters").querySelectorAll("button")) b.classList.toggle("on", b.dataset.filter === (this.bagFilter || "all"));
    list(this.$("#bag-list"), g.identifying ? "Your pack - pick the unknown thing to identify" : `Your pack${rows.length !== g.bag.length ? ` (${rows.length} of ${g.bag.length})` : ""}`, rows.map((i) => g.bag[i]), rows.indexOf(this.bagRow),
      (i) => `(${g.describe(i)}, worth ${i.unknown ? 10 : Math.floor(i.value / 2)} gold)`,
      (i) => { if (g.identifying) this.note(g.identify(rows[i])); else this.bagRow = rows[i]; });
    if (shop) list(this.$("#shop-list"), "The merchant's wares", g.stock || [], this.shopRow,
      (i) => (i.kind === "weapon" || i.kind === "armor" ? `(+${i.power})  -  ${i.value} gold` : `-  ${i.value} gold`), (i) => { this.shopRow = i; });
    const picked = this.bagRow >= 0 ? g.bag[this.bagRow] : null;
    const knife = picked && picked.kind === "weapon" && CM.weaponClass(picked) === "dagger";
    if (picked && picked.kind === "kit") { const b = document.createElement("button"); b.textContent = "Open the field kit (the alchemist's list)"; b.addEventListener("click", () => { g.closeBag(); this.openAlchemist(); }); beltBox.appendChild(b); }
    const verb = !picked ? "Give to" : ["weapon", "armor", "shield", "helm", "ring", "amulet", "trinket", "boots", "cloak"].includes(picked.kind) ? "Equip on" : picked.kind === "scroll" || picked.kind === "tome" ? "Read" : picked.kind === "wand" ? "Use on" : picked.kind === "oil" ? "Rub on the weapon of" : "Give to";
    this.$("#bag-give").querySelectorAll("button").forEach((b, i) => {
      const m = g.party[i], cmp = picked ? g.compare(m, picked) : null;
      b.innerHTML = `${verb} ${this.esc(m.name)}` + (m.hp <= 0 ? " (fallen)" : "") + (cmp ? ` <i class="cmp ${cmp.cls}">${this.esc(cmp.text)}</i>` : "");
      b.title = cmp && cmp.why ? cmp.why : "";
      if (knife && CM.canDualWield(m, picked)) { const o = document.createElement("i"); o.className = "offhand"; o.textContent = " (or the other hand)"; o.title = "A second knife in the off hand: another blow at half, every blow"; o.addEventListener("click", (e) => { e.stopPropagation(); this.note(g.equipOffhand(m, this.bagRow)); this.fillBag(); }); b.appendChild(o); }
    });
    const beltBox = this.$("#bag-belt"); beltBox.innerHTML = "";
    if (picked && CM.BELT_KINDS.includes(picked.kind)) { const b = document.createElement("button"); b.textContent = "To the belt"; b.title = "Four things to hand: keys 5 to 8; in a fight the first used in a round costs no turn"; b.addEventListener("click", () => { this.note(g.toBelt(this.bagRow)); this.bagRow = -1; this.fillBag(); }); beltBox.appendChild(b); }
    (g.belt || []).forEach((it, i) => { if (!it) return; const b = document.createElement("button"); b.textContent = `Off the belt: ${it.name}`; b.addEventListener("click", () => { this.note(g.fromBelt(i)); this.fillBag(); }); beltBox.appendChild(b); });
    const base = picked ? CM.itemCard(picked) : "Pick something from your pack, then who should equip or use it. A hero's sheet (1-4) takes things off." + (shop ? "  Pick from the merchant's wares (right) to Buy." : "");
    if (picked) this.$("#bag-note").textContent = base;
    this.$("#bag-note").dataset.base = base;
    if (!this.$("#bag-note").textContent) this.$("#bag-note").textContent = base;
  },
});
