"use strict";
// One set of controls and one result card, at every table (v16.6). The keys, the same everywhere on the floor:
// Space or Enter for the table's main action (Spin, Deal, Drop, Throw... - left to the arcade cabinets, which have their
// own keys), Esc back to the gallery (and from the gallery, out of the door), [ and ] for the table before and after.
// The keys are written on every table's bar. And whatever a play wins - gold, tickets, a card - comes up the same way at
// every table when the play is done: a card at the foot of the window, counting up, staying a moment (a run of wins
// close together adds up on the one card). The rules are 64zzm-result.js.
{ const r9 = CM.UI.prototype.renderCasino, nav9 = CM.UI.prototype.cgNav;
  const isTable = (id) => CM.CG_TABLES.some(([k]) => k === id), keyed = (id) => (CM.CG_INFO[id] || {}).cat === "arcade" || ["pit", "pachinko", "pond", "mint", "shelter", "cascade", "claw"].includes(id);
  const money = (n) => Math.floor(n).toLocaleString("en");
  Object.assign(CM.UI.prototype, {
    renderCasino() { const out = r9.call(this); this.cgResultFlush(); this.cgKeysOn(); return out; },
    cgNav(box) { nav9.call(this, box); const nav = box.querySelector(".cgnav"); if (!nav || nav.querySelector(".cgkeys")) return; const k = document.createElement("span"); k.className = "cgkeys";
      k.innerHTML = `${keyed(this.cgView) ? "" : "<kbd>Space</kbd> play · "}<kbd>Esc</kbd> back · <kbd>[</kbd> <kbd>]</kbd> tables`; k.title = keyed(this.cgView) ? "This cabinet has its own keys - see its instructions." : "Space or Enter does the table's main action."; const g = nav.querySelector(".cggold"); if (g) g.before(k); else nav.appendChild(k); },
    // ---- the result card ----
    cgResultFlush() { const g = this.game; if (this.cgBusy || this.cgView === "summary" || !g.cgTakeResult) return; const R = g.cgTakeResult(); if (!R) return; this.cgResultShow(R); },
    cgResultShow(R) {
      const dlg = this.$("#dlg-casino"); if (!dlg || !dlg.classList.contains("on")) return; const host = dlg.querySelector(".casinobox") || dlg; let C = this.cgResCard;
      if (!C || !C.el.isConnected) { const el = document.createElement("div"); el.className = "cgresult"; el.setAttribute("role", "status"); host.appendChild(el); C = this.cgResCard = { el, gold: 0, tickets: 0, cards: [], xp: 0, items: [], shown: { gold: 0, tickets: 0 } }; }
      C.gold += R.gold; C.tickets += R.tickets; C.cards = C.cards.concat(R.cards); C.xp += R.xp || 0; C.items = C.items.concat(R.items || []); const big = C.gold >= 200 || C.cards.length || C.items.length;
      C.el.className = `cgresult on${big ? " big" : ""}`; C.el.innerHTML = `<b class="cgrtitle">${big ? "A fine win!" : "You win"}</b><span class="cgrgold" ${C.gold ? "" : "hidden"}><i class="cgrcoin"></i><em>+0</em> gold</span><span class="cgrtk" ${C.tickets ? "" : "hidden"}><i class="tkt"></i><em>+0</em> tickets</span>${C.xp ? `<span class="cgrxp"><b>+${money(C.xp)}</b> XP each</span>` : ""}${C.items.length ? `<span class="cgritems">${C.items.slice(-3).map((it) => `<b class="rarity-${CM.rarityOf ? CM.rarityOf(it) : "common"}">${this.esc ? this.esc(it.name) : it.name}</b>`).join(", ")}${C.items.length > 3 ? ` and ${C.items.length - 3} more` : ""} - in the pack</span>` : ""}${C.cards.length ? `<span class="cgrcards">${C.cards.slice(-3).map((c) => `<i>${(CM.CARDS[c] || ["🂠"])[0]}</i>${this.esc ? this.esc(c) : c}`).join(", ")}</span>` : ""}`;
      const eg = C.el.querySelector(".cgrgold em"), et = C.el.querySelector(".cgrtk em"), from = { ...C.shown }, t0 = performance.now(), dur = 650;
      const tick = (now) => { const k = Math.min(1, (now - t0) / dur), e = 1 - Math.pow(1 - k, 3); C.shown.gold = Math.round(from.gold + (C.gold - from.gold) * e); C.shown.tickets = Math.round(from.tickets + (C.tickets - from.tickets) * e); if (eg) eg.textContent = `+${money(C.shown.gold)}`; if (et) et.textContent = `+${money(C.shown.tickets)}`; if (k < 1 && C.el.isConnected) requestAnimationFrame(tick); };
      requestAnimationFrame(tick); clearTimeout(C.timer); C.timer = setTimeout(() => { C.el.classList.remove("on"); setTimeout(() => { if (C === this.cgResCard) { C.el.remove(); this.cgResCard = null; } }, 400); }, big ? 4200 : 3000);
    },
    // ---- the keys ----
    cgKeysOn() { if (this.cgKeyFn) return; this.cgKeyFn = (e) => {
        const dlg = this.$("#dlg-casino"); if (!dlg || !dlg.classList.contains("on") || dlg.querySelector(".cghowto")) return; if (e.target && e.target.closest && e.target.closest("input, select, textarea")) return; const v = this.cgView;
        if (e.code === "Escape") { if (v === "gallery" || v === "summary") return; e.preventDefault(); e.stopPropagation(); if (this.cgBusy) return; this.cgView = "gallery"; this.cgNote = ""; this.caSfx("cardplace", 0.3); this.renderCasino(); return; }
        if ((e.key === "[" || e.key === "]") && isTable(v)) { e.preventDefault(); e.stopPropagation(); if (this.cgBusy) return; const L = CM.CG_TABLES, i = L.findIndex(([k]) => k === v), j = (i + (e.key === "]" ? 1 : -1) + L.length) % L.length; this.cgView = L[j][0]; this.cgNote = ""; this.caSfx("cardplace", 0.3); this.renderCasino(); return; }
        if ((e.code === "Space" || e.code === "Enter") && isTable(v) && !keyed(v) && !e.repeat) { const box = this.$("#casino-body"), skip = /^(leave|clear|cash out|get up|sell all|let it go)/i;
          if (e.target && e.target.closest && e.target.closest("button") && box.contains(e.target)) return;   // (a focused button: the key presses it, as ever)
          const b = [...box.querySelectorAll("button.primary")].find((x) => !x.disabled && x.offsetParent && !x.closest(".cgnav") && !x.closest(".cgcats") && !skip.test(x.textContent.trim())); if (!b) return; e.preventDefault(); e.stopPropagation(); b.click(); } };
      window.addEventListener("keydown", this.cgKeyFn, true); },
  });
}
