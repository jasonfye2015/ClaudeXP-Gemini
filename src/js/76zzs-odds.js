"use strict";
// The House odds (v16.9): the house's own books, open to the floor - a board by the cashier's cage with what each game
// of chance pays back of every hundred gold laid (as measured by tools/balance.js, played many thousands of times
// a plain, sensible way), the tickets and JXP it gives for each hundred, and beside each the party's own return so far;
// the games of skill with their terms (the level or score that wins the stake back). The same figure on each table's
// Figures page. The figures are 64zzo-odds.js, made by the tool.
{ const r12 = CM.UI.prototype.renderCasino, gal12 = CM.UI.prototype.cgGallery, st12 = CM.UI.prototype.cgTableStats;
  const nameOf = (id) => ((CM.CG_TABLES.find(([k]) => k === id) || [])[1]) || id, pc = (x) => `${(x * 100).toFixed(1)}%`;
  const houseOf = (id) => (CM.ODDS ? CM.ODDS.rows.filter((r) => r.id === id) : []);
  Object.assign(CM.UI.prototype, {
    renderCasino() { if (this.cgView === "odds") { this.cgOdds(this.$("#casino-body")); this.cgFwFlush && this.cgFwFlush(); return; } return r12.call(this); },
    cgGallery(box) { gal12.call(this, box); const strip = box.querySelector(".cgclub"); if (!strip || !CM.ODDS) return; const b = document.createElement("button"); b.className = "flbtn oddsbtn"; b.textContent = "House odds"; strip.appendChild(b);
      b.addEventListener("click", () => { this.cgView = "odds"; this.caSfx("cardplace", 0.3); this.renderCasino(); }); },
    cgTableStats(box) { st12.call(this, box); const rows = houseOf(this.cgStatsFor), grid = box.querySelector(".lbgrid"); if (!rows.length || !grid) return; const main = rows.find((r) => !r.alt) || rows[0], d = document.createElement("div"); d.className = "lbcell lbhouse";
      d.innerHTML = `<span>The house's books</span><b>${main.ret !== null && main.kind !== "skill" ? `pays back ${pc(main.ret)}` : "a game of skill"}</b><small>${main.kind === "skill" ? main.note : `played as ${main.how}${main.note ? ` - ${main.note}` : ""}`}</small>`; grid.appendChild(d); },
    cgOdds(box) {
      const g = this.game, F = g.cgStore(), O = CM.ODDS, mine = (id) => { const w = F.wagered[id] || 0; return w ? (F.paid[id] || 0) / w : null; };
      const order = [], chance = []; for (const r of O.rows) if ((r.kind === "chance" || r.kind === "fair") && !order.includes(r.id)) order.push(r.id); for (const id of order) { const R = O.rows.filter((r) => r.id === id && (r.kind === "chance" || r.kind === "fair")); chance.push(...R.filter((r) => !r.alt), ...R.filter((r) => r.alt)); } const skill = O.rows.filter((r) => r.kind === "skill");
      const bar = (x) => `<i class="odbar"><i style="width:${Math.min(100, Math.round(x * 80))}%"></i><em style="left:80%"></em></i>`;
      box.innerHTML = `<div class="odroom"><p class="lore">By the cashier's cage hangs a long board in the house's copperplate: THE HOUSE'S BOOKS, OPEN TO ALL. "The Joker likes a fair game," says the cashier. "Fair enough, anyway. Every number up there is what the tables really do - played ten thousand times and more."</p>
        <h4>Games of chance <span class="small">- of every 100 gold laid</span></h4>
        <table class="odtable"><tr><th>Game</th><th>Played as</th><th>Pays back</th><th></th><th>Tickets</th><th>JXP</th><th>Your return so far</th></tr>
        ${chance.map((r) => { const m = r.alt ? null : mine(r.id); return `<tr class="${r.alt ? "alt" : ""}"><td>${r.alt ? "" : `<button class="odgo" data-odgo="${r.id}">${nameOf(r.id)}</button>`}</td><td>${r.how}${r.note ? `<small> - ${r.note}</small>` : ""}</td><td><b>${pc(r.ret)}</b>${r.exact ? `<small title="worked out exactly"> exact</small>` : ""}</td><td>${bar(r.ret)}</td><td>${r.tk}</td><td>${r.jxp}</td><td>${m === null ? (r.alt ? "" : "<span class='small'>not played</span>") : `<span class="${m >= r.ret ? "up" : "down"}">${pc(m)}</span>`}</td></tr>`; }).join("")}</table>
        <p class="small">The white line on each bar is break-even; "exact" marks a figure worked out from the game's own odds rather than measured. Tables that pay back near 100% keep your gold longest; the luckiest-looking games (the slips, the Joker on the wheel) give the least back on average but the biggest wins. Your own return wanders above and below the house's figure - that's luck, and it evens out over many plays.</p>
        <h4>Games of skill</h4><div class="odskill">${skill.map((r) => `<div><button class="odgo" data-odgo="${r.id}">${nameOf(r.id)}</button><span>${r.note}</span></div>`).join("")}</div>
        <p class="small">The books were last made on ${O.made}. The floor's run of tickets is about ${O.tkRun} for every 100 gold laid at the tables; the fairground and the cabinets pay their tickets by the score and the level instead.</p></div>`;
      this.cgClubHead(box, "House odds"); box.querySelectorAll("[data-odgo]").forEach((b) => b.addEventListener("click", () => { this.cgView = b.dataset.odgo; this.cgNote = ""; this.caSfx("cardplace", 0.3); this.renderCasino(); }));
    },
  });
}
