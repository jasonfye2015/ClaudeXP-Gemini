"use strict";
// The party's standing with the Joker, the window's side: a door on the club strip with the level and a little bar of
// JXP (and a mark when there are rewards to collect), the level on every table's bar, and a word when a level is
// gained. The standing page: the Joker's own card drawn large with the level in its corners, the bar to the next
// level, what is waiting to be collected (each level's gold and card, the banked bonus tickets), the bonuses the level
// gives on the floor and in the world now, every perk with the level it opens at, and where the JXP has come from.
// The rules are 64zzn-joker.js.
{ const r11 = CM.UI.prototype.renderCasino, gal11 = CM.UI.prototype.cgGallery, nav11 = CM.UI.prototype.cgNav, JK = CM.JK;
  const money = (n) => Math.floor(n).toLocaleString("en"), pct = (k) => `${Math.round(k * 100)}%`;
  const nameOf = (id) => ({ quests: "Quests", tournament: "Tournament night", highroller: "High-roller", joker: "the Joker", play: "play" }[id] || ((CM.CG_TABLES.find(([k]) => k === id) || [])[1]) || id);
  const card = (p, w, h, L, now) => { p.clearRect(0, 0, w, h); const t = now / 1000, r = 14;
    p.save(); p.translate(w / 2, h / 2); p.rotate(Math.sin(t * 0.7) * 0.03); p.translate(-w / 2, -h / 2);
    p.fillStyle = "rgba(0,0,0,0.45)"; p.beginPath(); p.roundRect(14, 16, w - 22, h - 22, r); p.fill();
    const bg = p.createLinearGradient(0, 0, 0, h); bg.addColorStop(0, "#FBF6E8"); bg.addColorStop(1, "#EADFC4"); p.fillStyle = bg; p.beginPath(); p.roundRect(8, 8, w - 22, h - 22, r); p.fill(); p.strokeStyle = "#B8902A"; p.lineWidth = 3; p.stroke();
    p.strokeStyle = "rgba(140,30,40,0.35)"; p.lineWidth = 1; p.beginPath(); p.roundRect(18, 18, w - 42, h - 42, 8); p.stroke();
    const cx = (w - 14) / 2 + 1, cy = h / 2 - 2;
    // the Joker: a jester's cap of three points with bells, a grin
    p.fillStyle = "#F0D0A8"; p.beginPath(); p.arc(cx, cy + 14, 30, 0, Math.PI * 2); p.fill();
    const capC = ["#B02030", "#2A4AA0", "#C8961A"]; [-1, 0, 1].forEach((k, i) => { p.fillStyle = capC[i]; p.beginPath(); p.moveTo(cx - 30 + i * 20, cy - 4); p.quadraticCurveTo(cx + k * 34, cy - 50 - (k ? 0 : 10), cx + k * 46, cy - 26 - (k ? 0 : 30)); p.lineTo(cx - 10 + i * 20, cy - 4); p.fill();
      p.fillStyle = "#FFD840"; p.beginPath(); p.arc(cx + k * 46, cy - 26 - (k ? 0 : 30) + Math.sin(t * 4 + i) * 1.5, 5, 0, Math.PI * 2); p.fill(); });
    p.fillStyle = "#F4ECD8"; p.fillRect(cx - 32, cy - 8, 64, 8); p.fillStyle = "#1A1A1A"; p.beginPath(); p.arc(cx - 10, cy + 10, 3, 0, Math.PI * 2); p.arc(cx + 10, cy + 10, 3, 0, Math.PI * 2); p.fill();
    p.strokeStyle = "#8A2020"; p.lineWidth = 3; p.beginPath(); p.arc(cx, cy + 18, 14, 0.15, Math.PI - 0.15); p.stroke(); p.lineWidth = 1; p.fillStyle = "#E06070"; p.beginPath(); p.arc(cx - 20, cy + 20, 5, 0, Math.PI * 2); p.arc(cx + 20, cy + 20, 5, 0, Math.PI * 2); p.fill();
    // the ruff and the level
    for (let k = 0; k < 9; k++) { p.fillStyle = k % 2 ? "#FFFFFF" : "#E0D8C8"; p.beginPath(); p.arc(cx - 32 + k * 8, cy + 46, 7, 0, Math.PI * 2); p.fill(); }
    p.fillStyle = "#8A1A28"; p.font = "bold 22px Georgia"; p.textAlign = "center"; p.fillText(String(L), 32, 44); p.save(); p.translate(w - 38, h - 36); p.rotate(Math.PI); p.fillText(String(L), 0, 0); p.restore();
    p.font = "bold 13px Georgia"; p.fillStyle = "#5A3A10"; p.fillText("THE JOKER", cx, h - 44); p.textAlign = "left";
    const sh = p.createLinearGradient(((t * 0.35) % 2) * w - w * 0.5, 0, ((t * 0.35) % 2) * w, h); sh.addColorStop(0, "rgba(255,255,255,0)"); sh.addColorStop(0.5, "rgba(255,255,255,0.35)"); sh.addColorStop(1, "rgba(255,255,255,0)"); p.fillStyle = sh; p.beginPath(); p.roundRect(8, 8, w - 22, h - 22, r); p.fill();
    p.restore(); };
  Object.assign(CM.UI.prototype, {
    renderCasino() { const g = this.game; if (g.jkUps && g.jkUps.length) { const L = g.jkUps[g.jkUps.length - 1]; g.jkUps = []; this.cgNote = `${this.cgNote ? `${this.cgNote} ` : ""}Joker level ${L}! Collect the reward on the Joker standing page.`; }
      if (this.cgView === "standing") { this.cgStanding(this.$("#casino-body")); this.cgToasts && this.cgToasts(); this.cgFwFlush && this.cgFwFlush(); return; } return r11.call(this); },
    cgGallery(box) { gal11.call(this, box); const g = this.game, strip = box.querySelector(".cgclub"); if (!strip || !g.jkInfo) return; const I = g.jkInfo(), W = g.jkWaiting(), b = document.createElement("button"); b.className = "flbtn jkbtn";
      b.innerHTML = `<span>♠ Joker level <b>${I.level}</b>${W.levels.length || W.tickets ? ` <b class="flready">!</b>` : ""}</span><i class="jkmini"><i style="width:${I.need ? Math.round((100 * I.into) / I.need) : 100}%"></i></i>`; strip.prepend(b);
      b.addEventListener("click", () => { this.cgView = "standing"; this.caSfx("cardplace", 0.3); this.renderCasino(); }); },
    cgNav(box) { nav11.call(this, box); const g = this.game, nav = box.querySelector(".cgnav"), gold = nav && nav.querySelector(".cggold"); if (!gold || !g.jkLevel) return; const s = document.createElement("button"); s.className = "jkchip"; s.title = "Your standing with the Joker"; s.textContent = `♠ Lv ${g.jkLevel()}`; gold.before(s);
      s.addEventListener("click", () => { if (this.cgBusy) return; this.cgView = "standing"; this.caSfx("cardplace", 0.3); this.renderCasino(); }); },
    cgStanding(box) {
      const g = this.game, I = g.jkInfo(), L = I.level, W = g.jkWaiting(), J = g.jkStore(), owedGold = W.levels.reduce((a, l) => a + JK.reward(l).gold, 0), owedCards = W.levels.filter((l) => JK.reward(l).card).length;
      const now = [[`${pct(JK.tickets(L))} more tickets`, "banked as they're won"], [`${pct(JK.counter(L))} off the prize counter`, "on top of its own discount"], [`${pct(JK.gold(L))} more gold from fights`, "out in the world"], [`${pct(JK.xp(L))} more experience from fights`, "out in the world"], [`${JK.cordials(L)} Joker's Cordial${JK.cordials(L) === 1 ? "" : "s"}`, "in the pack at each expedition's start"]];
      const by = Object.entries(J.by).sort((a, b) => b[1] - a[1]).slice(0, 6);
      box.innerHTML = `<div class="jkroom"><div class="jktop"><canvas width="210" height="290" data-jkcard></canvas><div class="jkside"><p class="lore">The Joker keeps a book on everyone who plays his floor, and he is generous to the ones he likes. "Play anything," says the cashier, tapping a thick ledger with your name in it. "He notices."</p>
        <div class="jklevel"><span>Joker level</span><b>${L}</b><span>of ${JK.cap}</span></div><div class="jkbar"><i style="width:${I.need ? Math.round((100 * I.into) / I.need) : 100}%"></i><span>${I.need ? `${money(I.into)} / ${money(I.need)} JXP to level ${L + 1}` : "The top of the book"}</span></div><div class="small">${money(I.jxp)} JXP in all.</div>
        <div class="jkwait">${W.levels.length || W.tickets ? `<b>Waiting for you:</b> ${[owedGold ? `${money(owedGold)} gold` : "", owedCards ? `${owedCards} card${owedCards > 1 ? "s" : ""}` : "", W.tickets ? `${money(W.tickets)} bonus tickets` : ""].filter(Boolean).join(", ")}${W.levels.length ? ` (from level${W.levels.length > 1 ? "s" : ""} ${W.levels.join(", ")})` : ""} <button class="primary" data-jkget>Collect</button>` : `<span class="small">Nothing waiting just now - the next level pays ${money(JK.reward(Math.min(JK.cap, L + 1)).gold)} gold${JK.reward(L + 1).card ? " and a card" : ""}.</span>`}</div>
        <div class="cgnote">${this.cgNote || ""}</div>${(this.jkGot || []).map((c) => this.cgCardWon(c)).join("")}</div></div>
        <h4>What your level gives now</h4><div class="jknow">${now.map(([a, b]) => `<div><b>${a}</b><span>${b}</span></div>`).join("")}</div>
        <h4>The Joker's perks</h4><ul class="jkperks">${JK.PERKS.map(([at, txt]) => `<li class="${L >= at ? "on" : ""}"><b>${L >= at ? "✓" : `Level ${at}`}</b> ${txt}</li>`).join("")}<li class="${L >= 5 ? "on" : ""}"><b>Every level</b> ${money(20)} gold for each level number, and a card at every fifth (a stronger one from 15, a rare one from 25)</li></ul>
        <div class="jkhow"><div><h4>How JXP is earned</h4><ul><li>1 for every ${JK.stakePer} gold laid (up to ${JK.stakeMax} a stake)</li><li>1 for every ${JK.ticketPer} tickets won</li><li>${JK.level} for each level reached at a cabinet</li><li>${JK.board} for a place on a board, ${JK.record} more for a record</li><li>${JK.quest} for a quest, ${JK.tour} for a tournament night (${JK.tourTop} in the top three), ${JK.roller} for beating a high-roller</li></ul></div>
        <div><h4>Where yours came from</h4>${by.length ? `<table class="jkby">${by.map(([k, v]) => `<tr><td>${nameOf(k)}</td><td>${money(v)}</td></tr>`).join("")}</table>` : `<p class="small">Nothing yet - play anything.</p>`}</div></div></div>`;
      this.cgClubHead(box, "Joker standing"); const q = (s) => box.querySelector(s), cv = q("[data-jkcard]");
      const draw = (t) => { if (!cv.isConnected) return; card(cv.getContext("2d"), cv.width, cv.height, L, t); requestAnimationFrame(draw); }; requestAnimationFrame(draw);
      if (q("[data-jkget]")) q("[data-jkget]").addEventListener("click", () => { const o = g.jkCollect(); this.jkGot = o.cards; this.cgNote = `The cashier counts it out: ${[o.gold ? `${money(o.gold)} gold` : "", o.tickets ? `${money(o.tickets)} tickets` : "", o.cards.length ? `${o.cards.length} card${o.cards.length > 1 ? "s" : ""}` : ""].filter(Boolean).join(", ")}.`; this.cgSfx("cardwin", 0.5); if (o.gold) this.cgCoins(this.$("#casino-body"), Math.min(30, 6 + o.gold / 40)); this.renderCasino(); this.jkGot = null; });
    },
  });
}
