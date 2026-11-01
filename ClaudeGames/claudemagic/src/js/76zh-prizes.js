"use strict";
// The Prize Counter, the window's side (the forty-first big update): a glass counter by the cashier's cage, its shelves
// (gold, potions, gear, cards) laid out as little cards with a painted picture, a name, what it is and its price in
// tokens; those you cannot yet afford dimmed. The tokens show in the gallery's strip and in every table's slim bar, and
// a token earned at a table makes a little ticket hop up beside the count. The rules are 64zq-prizes.js.
{ const gal2 = CM.UI.prototype.cgGallery, nav2 = CM.UI.prototype.cgNav, r4 = CM.UI.prototype.renderCasino, PRIZE = CM.PRIZE;
  // a prize's little picture
  const art = (p, id, w, h) => {
    const bg = p.createLinearGradient(0, 0, 0, h); bg.addColorStop(0, "#3A2A1A"); bg.addColorStop(1, "#1A120A"); p.fillStyle = bg; p.fillRect(0, 0, w, h); const cx = w / 2, cy = h / 2 + 2;
    const coin = (x, y, r) => { const g = p.createRadialGradient(x - r / 3, y - r / 3, 1, x, y, r); g.addColorStop(0, "#FFF0A0"); g.addColorStop(1, "#B07A10"); p.fillStyle = g; p.beginPath(); p.arc(x, y, r, 0, Math.PI * 2); p.fill(); };
    const bottle = (col) => { p.fillStyle = "rgba(210,230,240,0.85)"; p.fillRect(cx - 4, cy - 22, 8, 10); p.fillStyle = "#8A5A20"; p.fillRect(cx - 5, cy - 26, 10, 5); p.fillStyle = col; p.beginPath(); p.arc(cx, cy, 15, 0, Math.PI * 2); p.fill(); p.fillStyle = "rgba(255,255,255,0.45)"; p.fillRect(cx - 9, cy - 7, 4, 9); };
    const card = (col, star) => { p.save(); p.translate(cx, cy); p.rotate(-0.12); p.fillStyle = "#F4ECD8"; p.fillRect(-15, -21, 30, 42); p.strokeStyle = col; p.lineWidth = 3; p.strokeRect(-13, -19, 26, 38); p.fillStyle = col; p.font = "bold 18px Georgia"; p.textAlign = "center"; p.fillText(star, 0, 7); p.restore(); };
    if (id === "pouch") { p.fillStyle = "#B08040"; p.beginPath(); p.moveTo(cx - 16, cy + 16); p.quadraticCurveTo(cx - 20, cy - 8, cx - 6, cy - 12); p.lineTo(cx + 6, cy - 12); p.quadraticCurveTo(cx + 20, cy - 8, cx + 16, cy + 16); p.fill(); p.fillStyle = "#6A4A20"; p.fillRect(cx - 8, cy - 15, 16, 4); coin(cx + 18, cy + 12, 6); }
    else if (id === "purse") { for (let k = 0; k < 6; k++) coin(cx - 18 + (k % 3) * 18, cy + 10 - Math.floor(k / 3) * 12, 9); }
    else if (id === "chest") { p.fillStyle = "#7A4A20"; p.fillRect(cx - 24, cy - 4, 48, 22); p.fillStyle = "#9A6A30"; p.beginPath(); p.ellipse(cx, cy - 4, 24, 11, 0, Math.PI, 0); p.fill(); p.fillStyle = "#F0C040"; p.fillRect(cx - 24, cy - 2, 48, 3); p.fillRect(cx - 3, cy - 2, 6, 10); for (let k = 0; k < 5; k++) coin(cx - 14 + k * 7, cy - 12 + (k % 2) * 3, 4); }
    else if (id === "torch") { p.fillStyle = "#6A4A20"; p.fillRect(cx - 3, cy - 6, 6, 26); p.fillStyle = "#FF9030"; p.beginPath(); p.moveTo(cx - 8, cy - 6); p.quadraticCurveTo(cx, cy - 34, cx + 8, cy - 6); p.fill(); p.fillStyle = "#FFE080"; p.beginPath(); p.moveTo(cx - 4, cy - 6); p.quadraticCurveTo(cx, cy - 20, cx + 4, cy - 6); p.fill(); }
    else if (id === "antidote") bottle("#40B060"); else if (id === "heal") bottle("#D02838"); else if (id === "mana") bottle("#2850D0");
    else if (id === "feather") { p.save(); p.translate(cx, cy); p.rotate(-0.6); const g = p.createLinearGradient(0, -24, 0, 24); g.addColorStop(0, "#FFE060"); g.addColorStop(0.5, "#FF7020"); g.addColorStop(1, "#C02010"); p.fillStyle = g; p.beginPath(); p.ellipse(0, 0, 9, 24, 0, 0, Math.PI * 2); p.fill(); p.strokeStyle = "#5A2A10"; p.beginPath(); p.moveTo(0, -22); p.lineTo(0, 28); p.stroke(); p.restore(); }
    else if (id === "mystery") { p.fillStyle = "#8A5A30"; p.fillRect(cx - 18, cy - 14, 36, 30); p.fillStyle = "#C03040"; p.fillRect(cx - 3, cy - 14, 6, 30); p.fillRect(cx - 18, cy - 2, 36, 6); p.fillStyle = "#FFE070"; p.font = "bold 18px Georgia"; p.textAlign = "center"; p.fillText("?", cx, cy - 18); }
    else if (id === "weapon" || id === "enchanted") { p.save(); p.translate(cx, cy); p.rotate(-0.7); if (id === "enchanted") { p.shadowColor = "#A080FF"; p.shadowBlur = 14; } p.fillStyle = "#D0D8E8"; p.beginPath(); p.moveTo(-3, -24); p.lineTo(0, -30); p.lineTo(3, -24); p.lineTo(3, 6); p.lineTo(-3, 6); p.fill(); p.shadowBlur = 0; p.fillStyle = "#C0902A"; p.fillRect(-10, 6, 20, 4); p.fillStyle = "#6A3A1A"; p.fillRect(-2.5, 10, 5, 12); p.restore(); if (id === "enchanted") { p.fillStyle = "#E0D0FF"; for (const [x, y] of [[cx - 18, cy - 14], [cx + 16, cy + 10], [cx + 14, cy - 18]]) p.fillRect(x, y, 2, 2); } }
    else if (id === "armor") { p.fillStyle = "#9AA0B0"; p.beginPath(); p.moveTo(cx - 18, cy - 14); p.lineTo(cx - 6, cy - 18); p.quadraticCurveTo(cx, cy - 12, cx + 6, cy - 18); p.lineTo(cx + 18, cy - 14); p.lineTo(cx + 15, cy + 6); p.quadraticCurveTo(cx, cy + 20, cx - 15, cy + 6); p.fill(); p.fillStyle = "#C0902A"; p.fillRect(cx - 13, cy + 1, 26, 3); }
    else if (id === "shield") { p.fillStyle = "#3A5AA0"; p.beginPath(); p.moveTo(cx - 16, cy - 16); p.lineTo(cx + 16, cy - 16); p.lineTo(cx + 16, cy); p.quadraticCurveTo(cx + 16, cy + 14, cx, cy + 20); p.quadraticCurveTo(cx - 16, cy + 14, cx - 16, cy); p.fill(); p.fillStyle = "#F0C040"; p.fillRect(cx - 2, cy - 12, 4, 26); p.fillRect(cx - 12, cy - 2, 24, 4); }
    else if (id === "helm") { p.fillStyle = "#A0A8B8"; p.beginPath(); p.arc(cx, cy + 2, 17, Math.PI, 0); p.lineTo(cx + 17, cy + 10); p.lineTo(cx - 17, cy + 10); p.fill(); p.fillStyle = "#3A3A48"; p.fillRect(cx - 11, cy, 22, 3); p.fillStyle = "#C03030"; p.beginPath(); p.moveTo(cx, cy - 14); p.quadraticCurveTo(cx + 12, cy - 24, cx + 17, cy - 14); p.lineTo(cx + 2, cy - 12); p.fill(); }
    else if (id === "card1") card("#8A6A40", "♦"); else if (id === "card2") card("#3A8AC0", "◆"); else if (id === "card3") card("#B050D0", "★");
  };
  const ticket = (n) => `<span class="tkcount" title="Prize tokens - spend them at the prize counter"><i class="tkt"></i>${n}</span>`;
  Object.assign(CM.UI.prototype, {
    renderCasino() { if (this.cgView === "prizes") { this.cgPrizes(this.$("#casino-body")); this.cgToasts && this.cgToasts(); this.tkSeen = this.game.tkStore().n; return; } r4.call(this); this.tkSeen = this.game.tkStore().n; },
    cgGallery(box) {
      gal2.call(this, box); const strip = box.querySelector(".cgclub"); if (!strip) return; const b = document.createElement("button"); b.className = "tkbtn"; b.innerHTML = `Prize counter ${ticket(this.game.tkStore().n)}`;
      strip.querySelector("[data-cgclub='trophies']").after(b); b.addEventListener("click", () => { this.cgView = "prizes"; this.caSfx("cardplace", 0.3); this.renderCasino(); });
    },
    cgNav(box) { nav2.call(this, box); const bar = box.querySelector(".cgbar .cggold"); if (bar) { bar.insertAdjacentHTML("beforebegin", ticket(this.game.tkStore().n)); this.tkWatch(box); } },
    // the count in a table's bar kept up while it is played, a ticket hopping up when tokens come
    tkWatch(box) {
      if (this.tkTimer) clearInterval(this.tkTimer);
      this.tkTimer = setInterval(() => { const el = box.querySelector(".cgbar .tkcount"); if (!el || !el.isConnected) { clearInterval(this.tkTimer); this.tkTimer = null; return; } const n = this.game.tkStore().n; if (n === this.tkSeen) return; const d = n - (this.tkSeen || 0); this.tkSeen = n; el.lastChild.textContent = n;
        if (d > 0) { const f = document.createElement("span"); f.className = "tkfly"; f.textContent = `+${d}`; el.appendChild(f); setTimeout(() => f.remove(), 1200); } }, 250);
    },
    cgPrizes(box) {
      const g = this.game, T = g.tkStore(), shelf = this.tkShelf || "all";
      const rows = PRIZE.LIST.filter((r) => shelf === "all" || r[1] === shelf);
      box.innerHTML = `<div class="cgprizes"><p class="lore">A long glass counter by the cashier's cage, lit from within: pouches of coin, stoppered potions, steel on velvet and cards in little frames. "Tokens only," says the clerk, and slides a felt tray across. "The tables hand them out - a few for every stake, a few for what the free tables pay, more for a name on the boards."</p>
        <div class="tkhead">${ticket(T.n)}<span>You have <b>${T.n}</b> prize token${T.n === 1 ? "" : "s"}.</span><span class="tksub">Earned ${T.earned}, spent ${T.spent}.</span></div>
        <div class="cgcats">${[["all", "Everything"], ...PRIZE.SHELVES].map(([k, n]) => `<button data-tkshelf="${k}" class="${k === shelf ? "primary" : ""}">${n}</button>`).join("")}</div>
        <div class="tkgrid">${rows.map(([id, , name, cost, what]) => `<div class="tkprize ${T.n >= cost ? "" : "dear"}"><canvas width="96" height="72" data-tkart="${id}"></canvas><b>${name}</b><span>${what}</span><button class="${T.n >= cost ? "primary" : ""}" data-tkbuy="${id}" ${T.n >= cost ? "" : "disabled"}>${ticket(cost)}</button></div>`).join("")}</div>
        ${this.tkOut || ""}<div class="small">How tokens come: one for every ${PRIZE.perStake} gold staked at any table, one for every ${PRIZE.perPay} gold a free table pays out, ${PRIZE.blind} for each blind beaten at Claudeatro (${PRIZE.boss} for a boss), ${PRIZE.board} for a place on a high-score board and ${PRIZE.record} for a new record. Odd gold is carried over. Gear is made for the deepest floor the party has reached.</div></div>`;
      this.cgClubHead(box, "The Prize Counter"); box.querySelector(".cgbar .cggold").insertAdjacentHTML("beforebegin", ticket(T.n));
      box.querySelectorAll("[data-tkart]").forEach((c) => art(c.getContext("2d"), c.dataset.tkart, c.width, c.height));
      box.querySelectorAll("[data-tkshelf]").forEach((b) => b.addEventListener("click", () => { this.tkShelf = b.dataset.tkshelf; this.caSfx("card", 0.25); this.renderCasino(); }));
      box.querySelectorAll("[data-tkbuy]").forEach((b) => b.addEventListener("click", () => { const o = g.tkBuy(b.dataset.tkbuy); if (o.error) { this.cgSfx("miss", 0.3); return; } this.cgSfx("cardwin", 0.5); if (o.gold) this.cgCoins(this.$("#casino-body"), 10);
        this.tkOut = `<div class="tkout">${o.gold ? `${o.name}: <b>${o.gold} gold</b>.` : o.card ? this.cgCardWon(o.card) : o.item ? `${o.name}: <b class="rarity-${CM.rarityOf(o.item)}">${o.item.name}</b>${o.item.unknown ? " (not yet known)" : ""} - in the party's pack.` : ""}</div>`; this.renderCasino(); this.tkOut = ""; }));
    },
  });
}
