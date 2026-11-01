"use strict";
// The tongue of the last bell, the window's side: "The last bell" in the Journal - the chapter the story is at, the bell
// drawn with the makings found glowing round it, every place's page once found (or what to do there, and Go), and the
// casting and the answer when they're ready. A making found goes up with the level-up jingle. The rules: 69i-thread.js.
{ const TH = CM.THREAD, oj0 = CM.UI.prototype.openJournal;
  const bind = (ui) => { if (ui.thBound || !ui.game || !ui.game.on) return; ui.thBound = true; ui.game.on("threadnote", (ids) => { try { if (CM.soloLevelFlourish) CM.soloLevelFlourish("The last bell", `${ui.game.thInfo().have} of ${TH.NOTES.length}`); } catch (e) { /* quiet */ } }); };
  // the bell, with a mark for every making round its rim
  const bellSvg = (I) => { const n = I.notes.length, marks = I.notes.map((x, k) => { const a = -Math.PI / 2 + (2 * Math.PI * k) / n, cx = 90 + Math.cos(a) * 80, cy = 80 + Math.sin(a) * 72; return `<circle cx="${cx.toFixed(1)}" cy="${cy.toFixed(1)}" r="7" class="${x.got ? "got" : ""}"><title>${x.place}</title></circle>`; }).join("");
    return `<svg class="thbell${I.rung ? " rung" : ""}" viewBox="0 0 180 162" aria-hidden="true"><path d="M60 40 Q60 18 90 18 Q120 18 120 40 L128 104 Q132 118 146 124 L34 124 Q48 118 52 104 Z" class="body"/><rect x="84" y="8" width="12" height="12" rx="3" class="body"/>
      ${I.forged ? `<circle cx="90" cy="132" r="9" class="tongue"/>` : `<circle cx="90" cy="132" r="9" class="socket"/>`}${marks}</svg>`; };
  Object.assign(CM.UI.prototype, {
    openJournal() { bind(this); const j = this.$("#dlg-journal"), boards = j && j.querySelector(".boards");
      if (boards && !boards.querySelector('[data-page="goals"]') && this.openWorldMap) { const b = document.createElement("button"); b.dataset.page = "goals"; b.textContent = "Goals"; boards.prepend(b); b.addEventListener("click", () => { this.journalPage = "goals"; this.openJournal(); }); }
      if (boards && !boards.querySelector('[data-page="thread"]')) { const b = document.createElement("button"); b.dataset.page = "thread"; b.textContent = "The last bell"; const goals = boards.querySelector('[data-page="goals"]'); if (goals) goals.after(b); else boards.prepend(b); b.addEventListener("click", () => { this.journalPage = "thread"; this.openJournal(); }); }
      if (this.journalPage !== "thread") { const tb = boards && boards.querySelector('[data-page="thread"]'); if (tb) tb.classList.remove("on"); return oj0.call(this); }
      const g = this.game; g.thSync(); const I = g.thInfo(), box = this.$("#journal-list"), can = g.wmCanTravel ? !g.wmCanTravel() : false, C = TH.CHAPTERS;
      for (const b of this.root.querySelectorAll("#dlg-journal .boards button")) b.classList.toggle("on", b.dataset.page === "thread");
      const fw = g.thForgeWhy(), rw = g.thRingWhy();
      box.innerHTML = `<div class="thtop">${bellSvg(I)}<div><div class="list-title">The tongue of the last bell</div><p class="lore">${C.map((c, k) => k <= I.chapter ? `<b>${this.esc(c[0])}.</b> ${this.esc(c[1])}` : "").filter(Boolean).slice(-2).join("<br>")}</p>
          <p class="small">${I.have} of ${I.all} of its makings found${I.forged ? "; the tongue is cast" : ""}${I.rung ? "; the bell has rung" : ""}.</p>
          ${!I.forged && I.have >= I.all ? `<button class="primary" data-thforge ${fw ? "disabled" : ""} title="${this.esc(fw)}">Have the smith cast it (a metal bar, ${TH.forgeGold} gold)</button><span class="small"> ${this.esc(fw)}</span>` : ""}
          ${I.forged && !I.rung ? `<button class="primary" data-thring ${rw ? "disabled" : ""}>Give the Boy the tongue</button><span class="small"> ${this.esc(rw)}</span>` : ""}<div class="note" id="th-note">${this.thNote || ""}</div></div></div>
        ${I.notes.map((x) => `<div class="entry thnote${x.got ? " got" : ""}"><div class="thplace"><b>${this.esc(x.place)}</b>${x.got ? "" : `<span>${this.esc(x.hint)}</span>`}</div>${x.got ? `<p>${this.esc(x.page)}</p>` : x.go ? `<button data-thgo="${x.go}" ${can ? "" : "disabled"}>Go</button>` : ""}</div>`).join("")}`;
      const fb = box.querySelector("[data-thforge]"); if (fb) fb.addEventListener("click", () => { const e = g.thForge(); this.thNote = e || "Cast."; this.openJournal(); this.refresh && this.refresh(); });
      const rb = box.querySelector("[data-thring]"); if (rb) rb.addEventListener("click", () => { const e = g.thRing(); this.thNote = e || ""; if (!e) { try { CM.levelJingle && CM.levelJingle(); } catch (x) { /* quiet */ } } this.openJournal(); this.refresh && this.refresh(); });
      box.querySelectorAll("[data-thgo]").forEach((b) => b.addEventListener("click", () => { this.closeDialogs(); const e = g.wmTravel(b.dataset.thgo); if (e) g.say(e); this.refresh && this.refresh(); }));
      this.openDialog("#dlg-journal"); },
  });
}
