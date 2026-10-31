"use strict";
// The Joker's Club, the window's side (the thirty-ninth big update): under the gallery's head a strip - the membership,
// a little loyalty card filling with stamps, and doors to the Hall of Champions (every high-score board, best first),
// the loyalty card itself (its stamps as tiny pictures of the tables, the membership and what a full card brings, and
// any full card waiting to be collected) and the achievements (bronze, silver and gold, locked, waiting to be
// collected, or collected). What happens on the floor - a stamp, a place on a board, a record, an achievement - shows
// for a moment in the corner of the window. The rules are 64zo-floorclub.js.
{ const r2 = CM.UI.prototype.renderCasino, gal0 = CM.UI.prototype.cgGallery, CLUB = CM.CLUB;
  const nameOf = (id) => ((CM.CG_TABLES.find(([k]) => k === id) || [])[1]) || id[0].toUpperCase() + id.slice(1);
  const MEDAL = { bronze: "#C88A50", silver: "#C8D0D8", gold: "#F0C040" };
  const thumbInto = (c, id) => { const p = c.getContext("2d"), f = CM.CG_THUMB[id]; if (f) f(p, c.width, c.height); else { p.fillStyle = "#3A2A10"; p.fillRect(0, 0, c.width, c.height); p.fillStyle = "#F0C040"; p.font = `bold ${c.height * 0.5}px Georgia`; p.textAlign = "center"; p.fillText("★", c.width / 2, c.height * 0.68); } };
  Object.assign(CM.UI.prototype, {
    renderCasino() {
      const v = this.cgView, box = this.$("#casino-body");
      if (v === "hall") this.cgHall(box); else if (v === "loyalty") this.cgLoyalty(box); else if (v === "trophies") this.cgTrophies(box); else r2.call(this);
      this.cgToasts();
    },
    cgClubHead(box, title) {
      const head = document.createElement("div"); head.className = "cgnav cgbar"; head.innerHTML = `<button data-cggal>◀ All games</button><span class="cgname">${title}</span><span class="cggold">${this.game.gold} gold</span>`; box.prepend(head);
      head.querySelector("[data-cggal]").addEventListener("click", () => { this.cgView = "gallery"; this.caSfx("cardplace", 0.3); this.renderCasino(); });
    },
    cgGallery(box) {
      gal0.call(this, box); const F = this.game.cgStore(), L = F.loyalty || { card: [], done: 0 }, member = CLUB.member(L.done || 0), U = this.game.cgUnpaid(), got = Object.keys(F.ach || {}).length, waiting = U.ach.length + U.loyalty;
      const strip = document.createElement("div"); strip.className = "cgclub";
      strip.innerHTML = `<span class="cgmember m-${member.toLowerCase()}">${member} member</span><span class="cgminicard" title="Loyalty card: ${L.card.length} of ${CLUB.stamps} different tables">${Array.from({ length: CLUB.stamps }, (_, k) => `<i class="${k < L.card.length ? "on" : ""}"></i>`).join("")}</span>
        <button data-cgclub="hall">Hall of Champions</button><button data-cgclub="loyalty">Loyalty card${U.loyalty ? " ✦" : ""}</button><button data-cgclub="trophies">Achievements ${got}/${CLUB.ACH.length}${U.ach.length ? " ✦" : ""}</button>${waiting ? `<span class="cgwait">${waiting} reward${waiting > 1 ? "s" : ""} to collect</span>` : ""}`;
      const head = box.querySelector(".cghead"); head.after(strip);
      strip.querySelectorAll("[data-cgclub]").forEach((b) => b.addEventListener("click", () => { this.cgView = b.dataset.cgclub; this.caSfx("cardplace", 0.3); this.renderCasino(); }));
    },
    // the Hall of Champions: every board, its ten best
    cgHall(box) {
      const F = this.game.cgStore(), B = F.boards || {};
      box.innerHTML = `<div class="cghall"><p class="lore">On the wall by the bar, ten boards in gilt frames, the house's chalk-boy keeping them. "Beat your own name," he says, "and I'll write it larger."</p><div class="cghallgrid">${CLUB.BOARDS.map((id) => { const rows = B[id] || [];
        return `<div class="cgboard"><div class="cgbhead"><canvas width="88" height="44" data-cgbt="${id}"></canvas><b>${nameOf(id)}</b><button data-cgplay="${id}">Play</button></div><ol>${rows.length ? rows.map((e, k) => `<li class="${k === 0 ? "top" : ""}"><span class="sc">${e.score.toLocaleString("en")}</span><span class="lv">${id === "pinball" ? `${e.level} mark${e.level === 1 ? "" : "s"}` : `level ${e.level}`}</span><span class="who">${e.who}</span><span class="at">${e.at || ""}</span></li>`).join("") : `<li class="none">No scores yet.</li>`}</ol></div>`; }).join("")}</div><div class="small">Records broken: ${F.records || 0}.</div></div>`;
      this.cgClubHead(box, "Hall of Champions");
      box.querySelectorAll("[data-cgbt]").forEach((c) => thumbInto(c, c.dataset.cgbt));
      box.querySelectorAll("[data-cgplay]").forEach((b) => b.addEventListener("click", () => { this.cgView = b.dataset.cgplay; this.cgNote = ""; this.caSfx("cardplace", 0.35); this.renderCasino(); }));
    },
    // the loyalty card
    cgLoyalty(box) {
      const g = this.game, F = g.cgStore(), L = F.loyalty || { card: [], done: 0, all: {} }, member = CLUB.member(L.done || 0), k = CLUB.TIERS.findIndex((t) => t[0] === member), next = CLUB.TIERS[k + 1], U = g.cgUnpaid();
      const nextGold = 150 + 100 * CLUB.TIERS.findIndex((t) => t[0] === CLUB.member((L.done || 0) + 1)), nextCard = CLUB.member((L.done || 0) + 1);
      box.innerHTML = `<div class="cgloyal"><p class="lore">The attendant punches a little gilt card. "A stamp for every different table," she says. "Eight on a card and the house thanks you for it. Fill enough and you'll find the house thanks its better members better."</p>
        <div class="cgpunch m-${member.toLowerCase()}"><div class="cgpunchhead"><b>THE GILDED JOKER</b><span>${member} member</span></div><div class="cgslots">${Array.from({ length: CLUB.stamps }, (_, i) => { const id = L.card[i]; return `<div class="cgslot ${id ? "on" : ""}">${id ? `<canvas width="64" height="64" data-cgst="${id}"></canvas><small>${nameOf(id)}</small>` : `<span>${i + 1}</span>`}</div>`; }).join("")}</div>
        <div class="cgpunchfoot">${L.card.length} of ${CLUB.stamps} - a full card brings ${nextGold} gold and a ${nextCard === "Platinum" ? "rare" : nextCard === "Gold" ? "stronger common" : "common"} card</div></div>
        ${U.loyalty ? `<div class="row"><button class="primary" data-cgcollect="loyalty">Collect ${U.loyalty} full card${U.loyalty > 1 ? "s" : ""}</button></div>` : ""}
        <div class="cgtiers">${CLUB.TIERS.slice(1).map(([n, need]) => `<div class="${(L.done || 0) >= need ? "on" : ""} m-${n.toLowerCase()}"><b>${n}</b><span>${need} full card${need > 1 ? "s" : ""}</span></div>`).join("")}</div>
        <div class="small">Cards filled: ${L.done || 0}${next ? ` - ${next[1] - (L.done || 0)} more for ${next[0]}` : " - the highest membership"}. Different tables played, all told: ${Object.keys(L.all || {}).length}. A stamp comes with a stake laid, or with gold from a free table. Gold from the club so far: ${F.clubGold || 0}.</div>${this.cwOutCards || ""}</div>`;
      this.cgClubHead(box, "Loyalty Card");
      box.querySelectorAll("[data-cgst]").forEach((c) => { thumbInto(c, c.dataset.cgst); });
      const cb = box.querySelector("[data-cgcollect]"); if (cb) cb.addEventListener("click", () => this.cgDoCollect("loyalty"));
    },
    // the achievements
    cgTrophies(box) {
      const F = this.game.cgStore(), A = F.ach || {};
      box.innerHTML = `<div class="cgtroph"><p class="lore">A glass case of medals by the cashier's cage, each with a little brass plate. "Earn one and it's yours," says the cashier, "and the house pays to have it said."</p>${["bronze", "silver", "gold"].map((tier) => { const R = CLUB.REWARD[tier];
        return `<h4 style="color:${MEDAL[tier]}">${tier[0].toUpperCase() + tier.slice(1)} - ${R.gold} gold${R.card ? ` and a ${R.card} card` : ""} each</h4><div class="cgachs">${CLUB.ACH.filter((a) => a[1] === tier).map(([id, , name, desc]) => { const a = A[id], st = !a ? "locked" : a.paid ? "done" : "ready";
          return `<div class="cgach ${st}"><span class="medal" style="background:${a ? MEDAL[tier] : "#3A3430"}">${a ? "★" : "?"}</span><div><b>${name}</b><span>${desc}</span></div>${st === "ready" ? `<button class="primary" data-cgcollect="${id}">Collect</button>` : st === "done" ? `<i>${a.at || "collected"}</i>` : ""}</div>`; }).join("")}</div>`; }).join("")}${this.cwOutCards || ""}</div>`;
      this.cgClubHead(box, `Achievements - ${Object.keys(A).length} of ${CLUB.ACH.length}`);
      box.querySelectorAll("[data-cgcollect]").forEach((b) => b.addEventListener("click", () => this.cgDoCollect(b.dataset.cgcollect)));
    },
    cgDoCollect(what) { const out = this.game.cgCollect(what); if (!out.gold && !out.cards.length) return; this.cgSfx("cardwin", 0.5); this.cgCoins(this.$("#casino-body"), 12); this.cwOutCards = out.cards.map((c) => this.cgCardWon(c)).join(""); this.renderCasino(); this.cwOutCards = ""; },
    // what has happened on the floor, for a moment in the corner
    cgToasts() {
      const news = this.game.cgNews(); if (!news.length) return; const dlg = this.$("#dlg-casino") || document.body; let host = dlg.querySelector(".cgtoasts"); if (!host) { host = document.createElement("div"); host.className = "cgtoasts"; dlg.appendChild(host); }
      for (const n of news.splice(0)) { const t = document.createElement("div"); t.className = `cgtoast t-${n.kind}`;
        t.textContent = n.kind === "stamp" ? `Loyalty stamp: ${nameOf(n.table)} (${n.n}/${CLUB.stamps})` : n.kind === "loyalty" ? `Loyalty card full! ${n.member} member - collect it on the loyalty card.` : n.kind === "record" ? `New record at ${nameOf(n.table)}: ${n.score.toLocaleString("en")}!` : n.kind === "board" ? `High-score board: #${n.rank} at ${nameOf(n.table)} (${n.score.toLocaleString("en")})` : n.kind === "ach" ? `Achievement: ${n.name} (${n.tier}) - collect it in Achievements` : "";
        host.appendChild(t); if (n.kind === "ach" || n.kind === "loyalty" || n.kind === "record") this.cgSfx("cardwin", 0.35); setTimeout(() => t.classList.add("out"), 6000); setTimeout(() => t.remove(), 6800); }
      this.game.saveCasino && this.game.saveCasino();
    },
  });
}
