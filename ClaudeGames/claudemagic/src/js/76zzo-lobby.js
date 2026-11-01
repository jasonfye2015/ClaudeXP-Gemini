"use strict";
// The floor, easier to find your way round - the window's side: the gallery's search, sort, favourites, recent row
// and "new" ribbons are in 76ze-gallery.js; here, a star and a figures button on every table's bar, the figures page
// for a table (a ledger of what it has given and taken, its best score, when first and last played), the table marked
// as tried and recent when it's opened, and the reckoning at the door: leaving the Joker after a busy visit shows a
// bill of the evening - the time, the tables, gold laid and paid back, the purse before and after, tickets, the best
// moment and the cards won - with the way out or back to the floor. The rules are 64zzl-lobby.js.
{ const r8 = CM.UI.prototype.renderCasino, nav8 = CM.UI.prototype.cgNav, open8 = CM.UI.prototype.openCasino, close8 = CM.UI.prototype.closeDialogs, od8 = CM.UI.prototype.openDialog;
  const nameOf = (id) => ((CM.CG_TABLES.find(([k]) => k === id) || [])[1]) || id, isTable = (id) => CM.CG_TABLES.some(([k]) => k === id), money = (n) => Math.floor(n).toLocaleString("en");
  const ago = (t) => { if (!t) return "never"; const s = (Date.now() - t) / 1000; return s < 90 ? "just now" : s < 3600 ? `${Math.round(s / 60)} minutes ago` : s < 86400 * 2 ? `${Math.round(s / 3600)} hours ago` : new Date(t).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" }); };
  const span = (s) => (s < 60 ? `${s} seconds` : s < 3600 ? `${Math.round(s / 60)} minute${Math.round(s / 60) === 1 ? "" : "s"}` : `${Math.floor(s / 3600)} h ${Math.round((s % 3600) / 60)} m`);
  Object.assign(CM.UI.prototype, {
    openCasino() { if (this.game.cgVisitStart && !this.game.cgVisit) this.game.cgVisitStart(); return open8.call(this); },
    openDialog(sel) { this.cgElsewhere = true; try { return od8.call(this, sel); } finally { this.cgElsewhere = false; } },
    // leaving the Joker: the reckoning first, if there's anything to reckon
    closeDialogs() { const g = this.game, dlg = this.$("#dlg-casino");
      if (dlg && dlg.classList.contains("on") && !this.cgElsewhere && !this.cgLeaving && g.cgVisit && this.cgView !== "summary") { const s = g.cgVisitEnd(Date.now(), true); if (s && !s.quiet && !this.cgBusy) { this.cgSummary = s; this.cgSummaryFrom = this.cgView; this.cgView = "summary"; this.renderCasino(); return; } }
      if (dlg && dlg.classList.contains("on") && !this.cgElsewhere && g.cgVisit) g.cgVisitEnd();
      return close8.call(this); },
    cgLeave() { this.cgLeaving = true; try { this.game.cgVisitEnd(); this.cgView = "gallery"; this.closeDialogs(); } finally { this.cgLeaving = false; } },   // (through every door-keeper: the music, the air)
    renderCasino() { const v = this.cgView, g = this.game, box = this.$("#casino-body");
      if (isTable(v) && this.lbLastView !== v && g.lbTouch) g.lbTouch(v); this.lbLastView = v;
      if (v === "stats") { this.cgTableStats(box); this.cgFwFlush && this.cgFwFlush(); return; } if (v === "summary") { this.cgVisitBill(box); return; } return r8.call(this); },
    cgNav(box) { nav8.call(this, box); const g = this.game, nav = box.querySelector(".cgnav"), id = this.cgView; if (!nav || !g.lbStore || !isTable(id)) return; const name = nav.querySelector(".cgname"); if (!name) return;
      const fav = g.lbIsFav(id), b = document.createElement("span"); b.className = "cgnavtools"; b.innerHTML = `<button class="cgstar${fav ? " on" : ""}" data-navfav title="${fav ? "Unstar" : "Star as a favourite"}">${fav ? "★" : "☆"}</button><button data-navstats title="This table's figures">Figures</button>`; name.after(b);
      b.querySelector("[data-navfav]").addEventListener("click", () => { const on = g.lbFav(id); this.caSfx(on ? "coin" : "card", 0.3, 1.4); const s = b.querySelector("[data-navfav]"); s.textContent = on ? "★" : "☆"; s.classList.toggle("on", on); });
      b.querySelector("[data-navstats]").addEventListener("click", () => { if (this.cgBusy) return; this.cgStatsFor = id; this.cgStatsBack = id; this.cgView = "stats"; this.caSfx("cardplace", 0.3); this.renderCasino(); }); },
    // ---- a table's figures ----
    cgTableStats(box) { const g = this.game, id = this.cgStatsFor, S = g.lbStats(id), info = CM.CG_INFO[id] || { line: "" }, free = !S.wagered, cell = (k, v, cls) => `<div class="lbcell ${cls || ""}"><span>${k}</span><b>${v}</b></div>`;
      box.innerHTML = `<div class="lbstats"><div class="lbtop"><canvas width="264" height="123" data-lbthumb></canvas><div><h3>${nameOf(id)}</h3><p class="lore">${info.line}</p><div class="row"><button class="primary" data-lbplay>Play</button><button class="cgstar${S.fav ? " on" : ""}" data-lbfav>${S.fav ? "★ A favourite" : "☆ Star it"}</button><button data-lbback>${this.cgStatsBack === "gallery" ? "Back to the gallery" : "Back to the table"}</button></div></div></div>
        <div class="lbgrid">${cell("Times played", money(S.played))}${free ? cell("Gold laid", "free to play", "dim") : cell("Gold laid", money(S.wagered))}${cell("Gold paid back", money(S.paid))}${free ? "" : cell("Your return so far", S.ret === null ? "-" : `${Math.round(S.ret * 100)}%`, S.ret === null ? "" : S.ret >= 1 ? "up" : "down")}${free ? "" : cell("Up or down", `${S.net >= 0 ? "+" : "-"}${money(Math.abs(S.net))} gold`, S.net >= 0 ? "up" : "down")}
        ${cell("Tickets won here", `<span class="tkcount"><i class="tkt"></i>${money(S.tickets)}</span>`)}${cell("Best score", S.best ? `${money(S.best.score)}${S.best.level ? ` <small>(level ${S.best.level})</small>` : ""}` : "none yet")}${cell("First played", ago(S.first))}${cell("Last played", ago(S.last))}</div>
        ${!free && S.ret !== null ? `<div class="lbbar" title="Gold paid back against gold laid"><i style="width:${Math.min(100, Math.round(S.ret * 50))}%"></i><em style="left:50%"></em><span>Paid back ${Math.round(S.ret * 100)}% of what was laid (the line is break-even)</span></div>` : ""}</div>`;
      this.cgClubHead(box, `Figures: ${nameOf(id)}`); const q = (s) => box.querySelector(s), f = CM.CG_THUMB[id], c = q("[data-lbthumb]"); if (f && c) { const p = c.getContext("2d"); p.scale(1.5, 1.5); f(p, 176, 82); }
      q("[data-lbplay]").addEventListener("click", () => { this.cgView = id; this.cgNote = ""; this.caSfx("cardplace", 0.35); this.renderCasino(); });
      q("[data-lbback]").addEventListener("click", () => { this.cgView = this.cgStatsBack || "gallery"; this.caSfx("cardplace", 0.3); this.renderCasino(); });
      q("[data-lbfav]").addEventListener("click", () => { g.lbFav(id); this.caSfx("coin", 0.3, 1.4); this.renderCasino(); }); },
    // ---- the reckoning at the door ----
    cgVisitBill(box) { const S = this.cgSummary || {}, net = (S.after || 0) - (S.before || 0), row = (k, v, cls) => `<tr class="${cls || ""}"><td>${k}</td><td>${v}</td></tr>`;
      box.innerHTML = `<div class="lbbill"><div class="lbpaper"><h3>Your evening at the Gilded Joker</h3><p class="lore">The doorman hands you your coat, and with it a slip in the house's copperplate.</p>
        <table>${row("Time on the floor", span(S.secs || 0))}${row("Tables played", S.tables && S.tables.length ? `${S.tables.length} <small>(${S.tables.slice(0, 6).map(nameOf).join(", ")}${S.tables.length > 6 ? ", ..." : ""})</small>` : "none")}
        ${row("Gold laid", money(S.staked || 0))}${row("Gold paid back", money(S.paid || 0))}${row("Purse when you came in", `${money(S.before || 0)} gold`)}${row("Purse now", `${money(S.after || 0)} gold`)}${row("Up or down", `${net >= 0 ? "+" : "-"}${money(Math.abs(net))} gold`, net >= 0 ? "up" : "down")}
        ${row("Tickets won", `<span class="tkcount"><i class="tkt"></i>${money(S.tickets || 0)}</span>`)}${row("The best moment", S.best || "a quiet night")}${row("Cards won", S.cards && S.cards.length ? S.cards.length : "none")}</table>
        ${(S.cards || []).map((c) => this.cgCardWon(c)).join("")}<div class="row"><button class="primary" data-lbout>Leave the Joker</button><button data-lbstay>Back to the floor</button></div></div></div>`;
      const q = (s) => box.querySelector(s); this.cgSfx(net >= 0 ? "coin" : "cardplace", 0.4);
      q("[data-lbout]").addEventListener("click", () => this.cgLeave());
      q("[data-lbstay]").addEventListener("click", () => { this.cgView = this.cgSummaryFrom && this.cgSummaryFrom !== "summary" ? this.cgSummaryFrom : "gallery"; this.renderCasino(); }); },
  });
}
