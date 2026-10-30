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
    for (const [id, which] of [["#btn-sell-shown", () => this.bagFilter || "all"], ["#btn-sell-spare", () => "spare"]]) {
      this.$(id).addEventListener("click", () => {                         // a first click says what and for how much; a second, within a few seconds, sells
        const w = which(), { rows, gold } = g.sellable(w);
        if (!rows.length) { this.note("Nothing of that to sell."); return; }
        if (this.sellAsked && this.sellAsked.w === w && Date.now() - this.sellAsked.at < 6000) { this.sellAsked = null; this.note(g.sellMany(w)); this.bagRow = -1; this.fillBag(); return; }
        this.sellAsked = { w, at: Date.now() };
        this.note(`Sell ${CM.plural(rows.length, "thing")} for ${gold.toLocaleString()} gold? Click again to sell. (Keys, relics and a scroll that remembers a square below are kept.)`);
      });
    }
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
    this.$("#bag-title").textContent = `${CM.t(shop ? "bag.title.shop" : "bag.title.pack")}   -   ${CM.t("bag.gold", { n: g.gold })}   -   ${CM.t("bag.weight", { n: CM.bagWeight(g.bag), cap: CM.carryCap(g.party) })}${g.weightWord() ? ` (${g.weightWord().toLowerCase()})` : ""}`;
    this.$("#shop-list").style.display = shop ? "" : "none";
    this.$("#btn-buy").style.display = shop ? "" : "none";
    this.$("#btn-sell").style.display = shop ? "" : "none";
    for (const id of ["#btn-sell-shown", "#btn-sell-spare"]) this.$(id).style.display = shop ? "" : "none";
    this.$("#btn-sell-shown").textContent = (this.bagFilter || "all") === "all" ? "Sell everything" : `Sell all ${CM.BAG_FILTERS[this.bagFilter].name.toLowerCase()}`;
    const list = (el, head, items, selected, describe, onPick) => {
      el.innerHTML = `<div class="head">${head}</div>` + (items.length ? "" : `<div class="empty">Nothing here.</div>`);
      items.forEach((item, i) => {
        const row = document.createElement("div");
        row.className = "item" + (i === selected ? " sel" : "");
        row.appendChild(this.icon(item));
        const text = document.createElement("span");
        text.innerHTML = `<span class="rarity-${CM.rarityOf(item)}">${this.esc(item.unknown ? CM.baseName(item) : item.name)}</span> <span class="what">${describe(item)}</span>`;
        row.appendChild(text);
        row.title = CM.itemCard(item);
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
    const verb = !picked ? "Give to" : ["weapon", "armor", "shield", "helm", "ring", "amulet", "trinket", "boots", "cloak"].includes(picked.kind) ? "Equip on" : picked.kind === "scroll" || picked.kind === "tome" ? "Read" : picked.kind === "wand" ? "Use on" : picked.kind === "oil" ? "Rub on the weapon of" : picked.kind === "dish" ? "Eat, served by" : ["lockpick", "trapkit", "trapparts", "bar", "bait", "grapnel", "pick"].includes(picked.kind) ? "Use, by" : "Give to";
    this.$("#bag-give").querySelectorAll("button").forEach((b, i) => {
      const m = g.party[i], cmp = picked ? g.compare(m, picked) : null;
      b.innerHTML = `${verb} ${this.esc(m.name)}` + (m.hp <= 0 ? " (fallen)" : "") + (cmp ? ` <i class="cmp ${cmp.cls}">${this.esc(cmp.text)}</i>` : "");
      b.title = cmp && cmp.why ? cmp.why : "";
      if (knife && CM.canDualWield(m, picked)) { const o = document.createElement("i"); o.className = "offhand"; o.textContent = " (or the other hand)"; o.title = "A second knife in the off hand: another blow at half, every blow"; o.addEventListener("click", (e) => { e.stopPropagation(); this.note(g.equipOffhand(m, this.bagRow)); this.fillBag(); }); b.appendChild(o); }
    });
    const beltBox = this.$("#bag-belt"); beltBox.innerHTML = "";
    if (picked && CM.BELT_KINDS.includes(picked.kind)) { const b = document.createElement("button"); b.textContent = "To the belt"; b.title = "Four things to hand: keys 5 to 8; in a fight the first used in a round costs no turn"; b.addEventListener("click", () => { this.note(g.toBelt(this.bagRow)); this.bagRow = -1; this.fillBag(); }); beltBox.appendChild(b); }
    if (shop && picked && !picked.insured && g.atShop()) { const b = document.createElement("button"); b.textContent = CM.t("bag.insure", { n: Math.max(5, Math.ceil((picked.value || 0) * CM.INSURE_RATE)) }); b.title = "If the party falls, an insured thing goes to the vault for the next."; b.addEventListener("click", () => { this.note(g.insure(this.bagRow)); this.fillBag(); }); beltBox.appendChild(b); }
    if (shop && g.atShop()) g.party.forEach((h, hi) => { const worn = CM.equipped(h).filter((it) => !it.insured && (it.value || 0) >= 50 && !(it.props && it.props.fists)).sort((a, b) => (b.value || 0) - (a.value || 0))[0]; if (!worn) return; const slot = CM.SLOTS.find((s) => h[s] === worn); const b = document.createElement("button"); b.textContent = CM.t("bag.insure.worn", { who: h.name, what: CM.itemName(worn), n: Math.max(5, Math.ceil(worn.value * CM.INSURE_RATE)) }); b.addEventListener("click", () => { this.note(g.insure(hi, slot)); this.fillBag(); }); beltBox.appendChild(b); });
    if (shop && g.inTown()) { const V = CM.VILLAGE.merchant, lvl = g.villageLevel("merchant"); if (lvl < V.costs.length) { const b = document.createElement("button"); b.textContent = `Raise the Merchant's House (level ${lvl}): ${V.costs[lvl]} renown`; b.title = V.levels[lvl]; b.disabled = g.renown() < V.costs[lvl]; b.addEventListener("click", () => { this.note(g.build("merchant")); this.fillBag(); }); beltBox.appendChild(b); } }
    if (shop && g.inTown() && g.villageLevel("merchant") >= 3) { const sel = document.createElement("select"); const bases = Object.values(CM.BASES).filter((B) => ["weapon", "armor", "shield", "helm"].includes(B.kind) && !["unique", "relic"].includes(B.group)).sort((a, b) => a.kind.localeCompare(b.kind) || (a.tier || 0) - (b.tier || 0)); sel.innerHTML = `<option value="">Commission a thing at the party's level (half again over, to the first camp)...</option>` + bases.map((B) => `<option value="${this.esc(B.id)}">${this.esc(B.id)} (${B.kind}, tier ${(B.tier || 0) + 1})</option>`).join(""); sel.addEventListener("change", () => { if (sel.value) { this.note(g.commission(sel.value)); this.fillBag(); } }); beltBox.appendChild(sel); }
    if (shop && g.atShop()) { const sel = document.createElement("select"); sel.innerHTML = `<option value="">${this.esc(CM.t("bag.order"))}</option>` + Object.keys(CM.ORDERABLE).map((k) => `<option value="${k}">${this.esc(CM.ORDERABLE[k](g.floor.number + 3).name)} - ${Math.ceil(CM.priceAt(CM.ORDERABLE[k](g.floor.number + 3).value, g.floor.number) * CM.ORDER_OVER)} gold</option>`).join(""); sel.addEventListener("change", () => { if (sel.value) { this.note(g.order(sel.value)); this.fillBag(); } }); beltBox.appendChild(sel); if ((g.orders || []).length) { const o = document.createElement("i"); o.className = "small"; o.textContent = " " + CM.t("bag.ordered", { list: g.orders.map((x) => x.item.name).join(", ") }); beltBox.appendChild(o); } }
    (g.belt || []).forEach((it, i) => { if (!it) return; const b = document.createElement("button"); b.textContent = `Off the belt: ${it.name}`; b.addEventListener("click", () => { this.note(g.fromBelt(i)); this.fillBag(); }); beltBox.appendChild(b); });
    const base = picked ? CM.itemCard(picked) : "Pick something from your pack, then who should equip or use it. A hero's sheet (1-4) takes things off." + (shop ? "  Pick from the merchant's wares (right) to Buy." : "");
    if (picked) this.$("#bag-note").textContent = base;
    this.$("#bag-note").dataset.base = base;
    if (!this.$("#bag-note").textContent) this.$("#bag-note").textContent = base;
  },
});
