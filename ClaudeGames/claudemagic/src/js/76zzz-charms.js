"use strict";
// The Joker's charms, the window's side: a door on the club strip (with the charms worn shown on it) opens the charm
// case - the party's slots across the top (filled with what's worn), then every charm as a card: its picture, what it
// does, and either how it's earned (with how far the party has got) or its price in tickets; Wear / Take off, or Buy.
// The rules are 64zzu-charms.js.
{ const r19 = CM.UI.prototype.renderCasino, gal19 = CM.UI.prototype.cgGallery, CH = CM.CHARMS;
  const progress = (g, id) => { try { const F = g.cgStore(), B = F.boards || {};
      if (id === "die") return `${Object.keys(CM.ARC.reg).filter((k) => (B[k] || []).some((e) => (e.level || 0) >= 10)).length} of 5 cabinets`;
      if (id === "wink") return `best ${(F.fa_darts_best || 0).toLocaleString("en")} of 900`;
      if (id === "ace") return `${Object.keys(g.bkStore().done).length} of 3 books`;
      if (id === "owl") { const S = g.pdStore(); return `${S.book.golden ? "carp landed" : "no carp yet"}, ${Object.keys(S.book).length} of 8 in the book`; }
      if (id === "phoenix") return (g.heStore().cleared || {})[500] ? "done" : "not yet";
      if (id === "purse") return "not yet"; if (id === "crown") return "not yet"; } catch (e) { /* */ } return ""; };
  Object.assign(CM.UI.prototype, {
    renderCasino() { if (this.cgView === "charms") { this.cgCharms(this.$("#casino-body")); this.cgFwFlush && this.cgFwFlush(); return; } return r19.call(this); },
    cgGallery(box) { gal19.call(this, box); const g = this.game, strip = box.querySelector(".cgclub"); if (!strip || !g.chStore) return; const worn = g.chStore().worn.filter((id) => g.chOwned(id)), b = document.createElement("button"); b.className = "flbtn chbtn";
      b.innerHTML = `Charms ${worn.length ? worn.map((id) => CH.byId[id].icon).join("") : "<span class='small'>(none worn)</span>"}`; strip.appendChild(b); b.addEventListener("click", () => { this.cgView = "charms"; this.caSfx("cardplace", 0.3); this.renderCasino(); }); },
    cgCharms(box) { const g = this.game, S = g.chStore(), slots = g.chSlots(), T = g.tkStore(), worn = S.worn.filter((id) => g.chOwned(id));
      const card = (C) => { const own = g.chOwned(C.id), on = worn.includes(C.id);
        return `<div class="chcard${own ? " own" : ""}${on ? " on" : ""}"><span class="chicon">${C.icon}</span><b>${C.name}</b><p>${C.what}</p>${C.cost ? `<span class="small">${own ? "Bought" : `${C.cost.toLocaleString("en")} tickets at the counter`}</span>` : `<span class="small">${own ? "Earned" : `To earn: ${C.earn}`}${own ? "" : `<br><i>${progress(g, C.id)}</i>`}</span>`}
          <div class="row">${own ? `<button class="${on ? "" : "primary"}" data-chwear="${C.id}">${on ? "Take it off" : "Wear it"}</button>` : C.cost ? `<button class="${T.n >= C.cost ? "primary" : ""}" data-chbuy="${C.id}" ${T.n >= C.cost ? "" : "disabled"}>Buy (${C.cost.toLocaleString("en")} tickets)</button>` : `<span class="chlock">🔒</span>`}</div></div>`; };
      box.innerHTML = `<div class="chroom"><p class="lore">Behind glass at the cashier's cage, on black velvet, the Joker's charms. "Some of them you earn," says the cashier, "and some of them you buy. Either way, they go with you - down the shaft, into the woods, wherever." You hold ${T.n.toLocaleString("en")} tickets.</p>
        <div class="chslots">${Array.from({ length: 3 }, (_, i) => { const open = i < slots, id = worn[i]; return `<div class="chslot${open ? "" : " shut"}">${id ? `<span>${CH.byId[id].icon}</span><b>${CH.byId[id].name}</b>` : open ? "<i>an empty slot</i>" : `<i>🔒 Joker level ${CH.SLOTS[i][0]}</i>`}</div>`; }).join("")}</div>
        <div class="cgnote">${this.cgNote || ""}</div><h4>Earned - the floor's capstones</h4><div class="chgrid">${CH.LIST.filter((c) => !c.cost).map(card).join("")}</div>
        <h4>From the counter</h4><div class="chgrid">${CH.LIST.filter((c) => c.cost).map(card).join("")}</div></div>`;
      this.cgClubHead(box, "The Joker's charms");
      box.querySelectorAll("[data-chwear]").forEach((b) => b.addEventListener("click", () => { const r = g.chWear(b.dataset.chwear); this.cgNote = r.error || (r.on ? `${CH.byId[b.dataset.chwear].name} - worn. It rides with you on the next expedition.` : "Taken off."); this.cgSfx(r.error ? "miss" : "cardplace", 0.4); this.renderCasino(); }));
      box.querySelectorAll("[data-chbuy]").forEach((b) => b.addEventListener("click", () => { const r = g.chBuy(b.dataset.chbuy); this.cgNote = r.error || `${CH.byId[b.dataset.chbuy].name} - yours. Wear it to take it with you.`; this.cgSfx(r.error ? "miss" : "cardwin", 0.5); this.renderCasino(); })); },
  });
}
