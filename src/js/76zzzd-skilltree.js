"use strict";
// The skill trees, the window's side: a "Skill tree" button on every hero's sheet (with the points waiting), and the
// tree itself over the sheet - three branches side by side, each a column of five tiers joined by a line that fills
// as points go in; every node shows its name, what a rank gives, its ranks, and whether it can be taken (lit), is
// learned (gold), or is still closed (and why, when pointed at). Click to spend a point. The capstones name the trait
// they'd teach. In town, "Unlearn" gives the points back. The party card says "Skill!" while points wait. The rules
// are 64zzz-skilltree.js.
{ const ST = CM.SKILLTREE, rs0 = CM.UI.prototype.renderSheet;
  CM.UI.prototype.renderSheet = function () { rs0.call(this); const g = this.game, h = g.party[this.sheetOf]; if (!h) return; const facts = this.$("#sheet-left .facts"); if (!facts || facts.querySelector("[data-tsopen]")) { if (this.tsOpen) this.tsRender(); return; }
    const left = ST.points(h) - ST.spent(h), b = document.createElement("button"); b.dataset.tsopen = "1"; b.className = `tsopenbtn${left > 0 ? " ready" : ""}`; b.innerHTML = `Skill tree${left > 0 ? ` <b>${left} to spend</b>` : ""}`; facts.prepend(b);
    b.addEventListener("click", () => { this.tsOpen = true; this.tsRender(); }); if (this.tsOpen) this.tsRender(); };
  Object.assign(CM.UI.prototype, {
    tsRender() { const g = this.game, h = g.party[this.sheetOf], box = this.$("#dlg-sheet .sheetbox"); if (!h || !box) return; let el = box.querySelector(".tsview"); if (!el) { el = document.createElement("div"); el.className = "tsview"; box.appendChild(el); }
      const left = ST.points(h) - ST.spent(h), B = ST.branches(h.cls), town = g.inTown ? g.inTown() : false;
      const node = (n, col) => { const [id, name, what, max, E] = n, have = (h.tree || {})[id] || 0, why = ST.why(h, id), open = !why, T = E.other ? ST.otherTrait(h, E.other) : null, tier = Number(id[1]);
        const detail = E.other ? (T ? `Learn <b>${T.name}</b>: ${T.what}` : `A trait of the path not taken (choose a path at level 5)`) : what;
        return `<button class="tsnode${have ? " has" : ""}${have >= max ? " full" : ""}${open ? " open" : ""}${tier === 5 ? " cap" : ""}" data-tsnode="${id}" title="${this.esc(why || "Click to learn a rank")}" ${open ? "" : "aria-disabled=\"true\""}><b>${this.esc(name)}</b><span>${detail}</span><i>${have} / ${max}</i></button>`; };
      el.innerHTML = `<div class="tshead"><h3>${this.esc(h.name)}'s skill tree <span class="small">(${this.esc(h.cls)}, level ${h.level})</span></h3><span class="tspts"><b>${left}</b> point${left === 1 ? "" : "s"} to spend · ${ST.spent(h)} spent</span>
        ${ST.spent(h) ? `<button data-tsreset ${town ? "" : "disabled"} title="${town ? "Give every point back" : "Unlearning takes quiet: in town"}">Unlearn</button>` : ""}<button class="primary" data-tsclose>Back to the sheet</button></div>
        <div class="tsnote">${this.tsNote || "A point comes with every level gained. A tier opens with two more points spent in its branch; the last needs level 15."}</div>
        <div class="tscols">${B.map((br) => { const inB = ST.inBranch(h, br.id); return `<div class="tscol"><div class="tsbr"><b>${this.esc(br.name)}</b><span>${this.esc(br.what)}</span><em>${inB} in this branch</em></div><div class="tsline"><i style="height:${Math.min(100, (inB / 8) * 100)}%"></i></div>${br.nodes.map((n) => node(n)).join("")}</div>`; }).join("")}</div>
        ${((L) => L.length ? `<div class="tsalone"><b>When alone</b> (the Tower, the Fortress, the island, the cave, Haven, the pipe): ${L.map((x) => this.esc(x)).join("; ")}.</div>` : "")(CM.SOLOEDGE ? CM.SOLOEDGE.lines(h) : [])}`;
      el.querySelector("[data-tsclose]").addEventListener("click", () => { this.tsOpen = false; this.tsNote = ""; el.remove(); this.renderSheet(); this.refresh && this.refresh(); });
      const rb = el.querySelector("[data-tsreset]"); if (rb) rb.addEventListener("click", () => { const why = g.tsReset(h); this.tsNote = why || "Unlearned: every point is yours to spend again."; this.tsRender(); });
      el.querySelectorAll("[data-tsnode]").forEach((b) => b.addEventListener("click", () => { const why = g.tsLearn(h, b.dataset.tsnode); this.tsNote = why || `${this.esc(ST.node(h.cls, b.dataset.tsnode)[1])}: learned.`; if (!why) { b.classList.add("pop"); try { CM.audio.play("spell", 0.35, 0, 1.3); } catch (e) { /* quiet */ } } this.tsRender(); this.refresh && this.refresh(); })); },
  });
  const close0 = CM.UI.prototype.closeDialogs; CM.UI.prototype.closeDialogs = function () { this.tsOpen = false; const v = document.querySelector("#dlg-sheet .tsview"); if (v) v.remove(); return close0.call(this); };
}
