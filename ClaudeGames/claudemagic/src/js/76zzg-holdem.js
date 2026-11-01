"use strict";
// The Residents' Game, the window's side: an oval table of green baize with a dark wood rail under a hanging lamp,
// the party's seat at the front and four of the village's residents round it - each drawn with their trade (a mug,
// a purse, a hammer, a book, a holy sign, a pitchfork), their chips stacked before them, their own way of talking in a
// bubble when they bet or fold or win. Cards fly from the dealer's place to the seats, the board turns over card by
// card, chips slide to the pot and from it to the winner; at the showdown the hands turn up and the winning hand's
// name rides over it. Fold, check or call, bet or raise below; deal the next hand, or cash out between hands. The rules
// are 64zzg-holdem.js.
CM.CG_TABLES.push(["holdem", "The Residents' Game"]);
{ const floor0 = CM.UI.prototype.renderFloor, HE = CM.HE, W = 720, H = 430, CX = 360, CY = 196;
  const SEAT = [[360, 352], [92, 222], [214, 72], [506, 72], [628, 222]];
  const card = (p, x, y, c, up, s = 1) => { const w = 34 * s, h = 48 * s; p.save(); p.translate(x, y); p.fillStyle = "rgba(0,0,0,0.35)"; p.fillRect(-w / 2 + 2, -h / 2 + 3, w, h);
    const r = 4 * s; p.beginPath(); p.moveTo(-w / 2 + r, -h / 2); p.arcTo(w / 2, -h / 2, w / 2, h / 2, r); p.arcTo(w / 2, h / 2, -w / 2, h / 2, r); p.arcTo(-w / 2, h / 2, -w / 2, -h / 2, r); p.arcTo(-w / 2, -h / 2, w / 2, -h / 2, r); p.closePath();
    if (up && c) { p.fillStyle = "#FBF8F0"; p.fill(); p.strokeStyle = "#B8B0A0"; p.stroke(); const red = c.s === 1 || c.s === 2; p.fillStyle = red ? "#C02028" : "#1A1A22"; p.font = `bold ${Math.round(15 * s)}px Georgia`; p.textAlign = "center"; p.fillText(HE.RANKS[c.r] === "T" ? "10" : HE.RANKS[c.r], 0, -3 * s); p.font = `${Math.round(17 * s)}px serif`; p.fillText(HE.SUITS[c.s], 0, 16 * s); p.textAlign = "left"; }
    else { p.fillStyle = "#7A1A24"; p.fill(); p.strokeStyle = "#E0B860"; p.lineWidth = 1.5; p.stroke(); p.lineWidth = 1; p.strokeStyle = "rgba(224,184,96,0.5)"; p.strokeRect(-w / 2 + 4 * s, -h / 2 + 4 * s, w - 8 * s, h - 8 * s); p.beginPath(); p.arc(0, 0, 7 * s, 0, Math.PI * 2); p.stroke(); }
    p.restore(); };
  const chips = (p, x, y, n) => { const k = Math.min(8, Math.ceil(Math.log2(n + 1))); for (let i = 0; i < k; i++) { p.fillStyle = ["#C03030", "#3060C0", "#30A050", "#E0B040", "#202020"][i % 5]; p.beginPath(); p.ellipse(x, y - i * 3, 9, 4, 0, 0, Math.PI * 2); p.fill(); p.strokeStyle = "rgba(255,255,255,0.6)"; p.setLineDash([2, 3]); p.stroke(); p.setLineDash([]); } };
  const face = (p, x, y, id, now, dim) => { const P = id === "you" ? { col: "#2A5A8A", hair: "#5A3A20" } : HE.RES[id]; p.save(); p.globalAlpha = dim ? 0.35 : 1;
    p.fillStyle = P.col; p.beginPath(); p.ellipse(x, y + 26, 24, 16, 0, Math.PI, 0); p.fill(); p.fillStyle = "#E8C8A0"; p.beginPath(); p.arc(x, y, 15, 0, Math.PI * 2); p.fill(); p.fillStyle = P.hair; p.beginPath(); p.arc(x, y - 4, 15, Math.PI * 1.05, Math.PI * 1.95); p.fill();
    const blink = Math.floor(now / 3000 + x) % 7 === 0 && now % 3000 < 140; p.fillStyle = "#2A2020"; if (!blink) { p.fillRect(x - 6, y - 1, 3, 3); p.fillRect(x + 3, y - 1, 3, 3); } else { p.fillRect(x - 6, y, 3, 1); p.fillRect(x + 3, y, 3, 1); } p.fillRect(x - 3, y + 7, 6, 1.5);
    p.fillStyle = "#F0E0B0"; p.strokeStyle = "#5A4020";
    if (id === "tavern") { p.fillStyle = "#C8A060"; p.fillRect(x + 18, y + 12, 9, 12); p.fillStyle = "#FFF8E0"; p.fillRect(x + 18, y + 10, 9, 3); }
    else if (id === "merchant") { p.fillStyle = "#806020"; p.beginPath(); p.arc(x + 22, y + 18, 6, 0, Math.PI * 2); p.fill(); p.fillStyle = "#F0C040"; p.fillRect(x + 21, y + 11, 2, 3); }
    else if (id === "smith") { p.fillStyle = "#6A4A2A"; p.fillRect(x + 21, y + 8, 2, 16); p.fillStyle = "#909098"; p.fillRect(x + 17, y + 6, 10, 5); }
    else if (id === "library") { p.fillStyle = "#6A2A2A"; p.fillRect(x + 16, y + 12, 12, 9); p.fillStyle = "#F0E6CC"; p.fillRect(x + 17, y + 13, 10, 2); p.strokeStyle = "#202020"; p.strokeRect(x - 8, y - 3, 6, 5); p.strokeRect(x + 2, y - 3, 6, 5); }
    else if (id === "priest") { p.fillStyle = "#F0C040"; p.fillRect(x - 1, y + 14, 2, 10); p.fillRect(x - 4, y + 17, 8, 2); }
    else if (id === "farm") { p.strokeStyle = "#8A6A40"; p.lineWidth = 2; p.beginPath(); p.moveTo(x + 22, y + 26); p.lineTo(x + 22, y - 6); p.stroke(); p.lineWidth = 1; p.strokeStyle = "#A0A0A8"; for (let k = -1; k <= 1; k++) { p.beginPath(); p.moveTo(x + 22 + k * 3, y - 6); p.lineTo(x + 22 + k * 3, y - 14); p.stroke(); } }
    p.restore(); };
  Object.assign(CM.UI.prototype, {
    renderFloor(box) { if (this.cgView === "holdem") return this.cgHoldem(box); return floor0.call(this, box); },
    cgHoldem(box) {
      const g = this.game, Hs = g.heStore(), T = g.heTable(), seated = !!T; SEAT[1] = T && T.seats.length === 2 ? [360, 72] : [92, 222];   // (heads up, the one opponent sits across)
      box.innerHTML = `<div class="cgtable holdem"><h3>The Residents' Game</h3><p class="lore">Through a curtain at the back of the floor there's a round table where the village's own sit down of an evening - the tavern-keeper, the merchant, the smith, the librarian, the priest and the farmer's hand, four at a time. "Limit hold'em," says the dealer, a quiet woman with very quick hands. "Buy in, and it's you against them. The house only deals."</p>
        <canvas class="hecanvas" width="${W}" height="${H}"></canvas><div class="hectl"></div>
        <div class="cgnote">${this.cgNote || ""}</div>${this.heCard ? this.cgCardWon(this.heCard) : ""}
        <div class="small">Fixed-limit Texas hold'em: two cards each and five on the board; the best five of seven wins. Blinds are a hundredth and a fiftieth of the buy-in; bets are a big blind before the turn and two after, four to a street. Each resident plays their own way - ${Object.values(HE.RES).map((P) => `${P.name} ${P.style}`).join(", ")}. Cash out between hands for gold. Tickets for the buy-in, and for a pot won with a straight (1), flush (2), full house (3), four of a kind (5) or straight flush (10), and 2 for each resident sent home; a royal flush brings a rare card; sending the whole table home, a card the first time at each buy-in. Hands played ${Hs.hands}, pots won ${Hs.pots}, biggest pot ${Hs.best}.</div>${this.cgStats("holdem")}</div>`;
      this.heCanvas = box.querySelector(".hecanvas"); this.heAnim = this.heAnim || { bub: {}, shown: {}, flips: {}, flights: [], deal: 0, win: null }; this.heCtl(); this.hePump();
      if (!this.heLoop) { const loop = (now) => { if (!this.heCanvas || !this.heCanvas.isConnected || this.cgView !== "holdem") { this.heLoop = null; return; } this.heTick(now); this.heFrame(now); this.heLoop = requestAnimationFrame(loop); }; this.heLoop = requestAnimationFrame(loop); }
      if (!seated) this.heAnim = { bub: {}, shown: {}, flips: {}, flights: [], deal: 0, win: null };
    },
    heCtl() {
      const g = this.game, T = g.heTable(), el = this.$("#casino-body .hectl"); if (!el) return; let html;
      if (!T) html = `<div class="row hebuy">${HE.BUYINS.concat(g.vipOn && g.vipOn() ? CM.FLOOR.VIP.buyins : []).map((b) => `<button class="primary" data-hesit="${b}">Buy in for ${b} gold${g.heStore().cleared[b] ? " ✓" : ""}</button>`).join("")}<button data-leave>Leave</button></div>`;
      else if (T.stage === "hand" && T.toAct === 0) { const owe = HE.toCall(T, 0), size = HE.betSize(T), S = T.seats[0], capped = T.raises >= HE.cap || S.stack <= owe;
        html = `<div class="row heact">${owe ? `<button data-hea="fold">Fold</button>` : ""}<button class="primary" data-hea="call">${owe ? `Call ${Math.min(owe, S.stack)}` : "Check"}</button>${capped ? "" : `<button class="primary" data-hea="raise">${T.cur ? `Raise to ${T.cur + size}` : `Bet ${size}`}</button>`}</div>`; }
      else if (T.stage === "hand") html = `<div class="row heact"><span class="small">${HE.RES[T.seats[T.toAct].id].short} to act…</span></div>`;
      else html = `<div class="row heact">${T.stage === "over" ? "" : `<button class="primary" data-hedeal>Deal the next hand</button>`}<button data-heleave>${T.stage === "over" && T.seats[0].stack <= 0 ? "Get up from the table" : `Cash out ${T.seats[0].stack} chips`}</button></div>`;
      el.innerHTML = html; const q = (s) => el.querySelector(s);
      if (q("[data-leave]")) q("[data-leave]").addEventListener("click", () => this.closeDialogs());
      el.querySelectorAll("[data-hesit]").forEach((b) => b.addEventListener("click", () => { const r = g.heSit(Number(b.dataset.hesit)); this.cgNote = r.error || `You buy in for ${b.dataset.hesit}. The dealer shuffles.`; this.heCard = null; this.heAnim = { bub: {}, shown: {}, flips: {}, flights: [], deal: 0, win: null }; this.cgSfx(r.error ? "miss" : "card", 0.4); this.renderCasino(); }));
      el.querySelectorAll("[data-hea]").forEach((b) => b.addEventListener("click", () => { g.heAct(b.dataset.hea); this.heNext = performance.now() + 650; this.hePump(); this.heCtl(); }));
      if (q("[data-hedeal]")) q("[data-hedeal]").addEventListener("click", () => { this.cgNote = ""; g.heDeal(); this.hePump(); this.heCtl(); });
      if (q("[data-heleave]")) q("[data-heleave]").addEventListener("click", () => { const r = g.heLeave(); if (r.error) { this.cgNote = r.error; } else { this.cgNote = r.chips ? `You cash out ${r.chips} gold - ${r.net >= 0 ? `${r.net} up` : `${-r.net} down`} on the night.` : "You get up from the table with empty pockets."; if (r.net > 0) this.cgCoins(this.$("#casino-body"), 14); } this.renderCasino(); });
    },
    // the residents' turns, one at a time, at a talking pace; a new hand after a pause
    heTick(now) { const g = this.game, T = g.heTable(); if (!T) return;
      if (T.stage === "hand" && T.toAct > 0 && now > (this.heNext || 0)) { g.heAi(); this.heNext = now + 700 + Math.random() * 500; this.hePump(); this.heCtl(); } },
    hePump() { const g = this.game, T = g.heTable(), A = this.heAnim, now = performance.now(); if (!T || !A) return; let delay = 0;
      for (const e of g.heEvents()) {
        if (e.kind === "deal") { A.shown = {}; A.flips = {}; A.win = null; A.bub = {}; A.deal = now; A.hand = e.hand; this.cgSfx("card", 0.35, 1.2); }
        else if (e.kind === "act") { const P = HE.RES[T.seats[e.seat].id]; A.bub[e.seat] = { text: e.what === "fold" && P && Math.random() < 0.4 ? P.say.fold : e.what === "raise" && P && Math.random() < 0.4 ? P.say.raise : e.what[0].toUpperCase() + e.what.slice(1) + (e.what === "call" || e.what === "bet" || e.what === "raise" ? ` (${e.amount})` : ""), at: now };
          this.cgSfx(e.what === "fold" ? "card" : e.what === "check" ? "step" : "coin", 0.25, e.what === "raise" || e.what === "bet" ? 1.1 : 1.4); if (e.what !== "fold" && e.what !== "check") A.flights.push({ from: SEAT[e.seat], to: [CX, CY + 58], at: now, n: e.amount }); }
        else if (e.kind === "street") { delay += 250; for (let k = 0; k < e.board.length; k++) if (!A.flips[k]) A.flips[k] = now + delay + k * 160; this.cgSfx("card", 0.3, 1.0); A.bub = {}; }
        else if (e.kind === "show") { A.shown[e.seat] = now + delay + 300; A.cats = A.cats || {}; A.cats[e.seat] = e.cat; }
        else if (e.kind === "win") { delay += 600; const S = T.seats[e.seat], P = HE.RES[S.id], who = P ? P.short : "You"; A.win = { seat: e.seat, at: now + delay, text: `${who} ${P ? "wins" : "win"} ${e.amount}${e.cat >= 0 ? ` - ${HE.CATS[e.cat].toLowerCase()}` : ""}` }; A.flights.push({ from: [CX, CY + 58], to: SEAT[e.seat], at: now + delay, n: e.amount });
          setTimeout(() => this.cgSfx(e.seat === 0 ? "victory" : "coin", e.seat === 0 ? 0.4 : 0.3), delay); if (P && Math.random() < 0.5) A.bub[e.seat] = { text: P.say.win, at: now + delay };
          if (e.seat === 0) this.cgNote = `You win ${e.amount}${e.cat >= 0 ? ` with ${HE.CATS[e.cat].toLowerCase()}` : ""}${e.tickets ? ` - ${e.tickets} ticket${e.tickets > 1 ? "s" : ""}` : ""}${e.card ? `, and a card - ${e.card}!` : "."}`; else this.cgNote = A.win.text + "."; if (e.card) { this.heCard = e.card; setTimeout(() => this.cgSfx("cardwin", 0.5), delay + 400); } }
        else if (e.kind === "bust") { const P = HE.RES[e.id]; A.bub[e.seat] = { text: P.say.bust, at: now + delay + 900 }; this.cgNote += ` ${P.short} is out of chips and goes home${e.tickets ? ` (+${e.tickets} tickets)` : ""}.`; }
        else if (e.kind === "cleared") { this.cgNote += e.card ? ` You've sent the whole table home - a card: ${e.card}!` : ` You've sent the whole table home${e.tickets ? ` (+${e.tickets} tickets)` : ""}!`; if (e.card) this.heCard = e.card; setTimeout(() => this.renderCasino(), delay + 1500); }
        else if (e.kind === "broke") this.cgNote += " You're out of chips.";
      }
      const note = this.$("#casino-body .holdem .cgnote"); if (note) note.textContent = this.cgNote || ""; },
    heFrame(now) {
      const p = this.heCanvas.getContext("2d"), T = this.game.heTable(), A = this.heAnim;
      const bg = p.createRadialGradient(CX, 0, 30, CX, CY, 520); bg.addColorStop(0, "#5A4630"); bg.addColorStop(1, "#160E0A"); p.fillStyle = bg; p.fillRect(0, 0, W, H);
      p.fillStyle = "#3A2214"; p.beginPath(); p.ellipse(CX, CY + 20, 318, 168, 0, 0, Math.PI * 2); p.fill(); const felt = p.createRadialGradient(CX, CY, 20, CX, CY + 20, 300); felt.addColorStop(0, "#2E8A4A"); felt.addColorStop(1, "#14502A"); p.fillStyle = felt; p.beginPath(); p.ellipse(CX, CY + 20, 296, 148, 0, 0, Math.PI * 2); p.fill();
      p.strokeStyle = "rgba(240,210,120,0.35)"; p.lineWidth = 2; p.beginPath(); p.ellipse(CX, CY + 20, 240, 110, 0, 0, Math.PI * 2); p.stroke(); p.lineWidth = 1; p.fillStyle = "rgba(240,210,120,0.12)"; p.font = "italic 16px Georgia"; p.textAlign = "center"; p.fillText("The Gilded Joker", CX, CY + 104); p.textAlign = "left";
      const lamp = p.createRadialGradient(CX, CY, 10, CX, CY, 300); lamp.addColorStop(0, "rgba(255,230,160,0.14)"); lamp.addColorStop(1, "rgba(0,0,0,0)"); p.fillStyle = lamp; p.fillRect(0, 0, W, H);
      if (!T) { p.fillStyle = "rgba(255,240,200,0.9)"; p.font = "bold 22px Georgia"; p.textAlign = "center"; p.fillText("Choose a buy-in and sit down", CX, CY + 24); p.textAlign = "left"; const who = Object.keys(HE.RES); who.forEach((id, k) => face(p, 120 + k * 96, 330, id, now, false)); return; }
      // the board and the pot
      for (let k = 0; k < 5; k++) { const c = T.board[k], f = A.flips[k], x = CX - 92 + k * 46; if (!c || (f && now < f)) { p.strokeStyle = "rgba(255,255,255,0.12)"; p.strokeRect(x - 17, CY - 24, 34, 48); continue; } const t = f ? Math.min(1, (now - f) / 220) : 1; p.save(); p.translate(x, CY); p.scale(Math.abs(Math.cos(t * Math.PI)) * 0.98 + 0.02, 1); card(p, 0, 0, c, t > 0.5); p.restore(); }
      const pot = HE.pot(T) + 0; if (pot > 0) { chips(p, CX - 26, CY + 62, pot); p.fillStyle = "#FFE8A0"; p.font = "bold 13px monospace"; p.fillText(`POT ${pot}`, CX - 10, CY + 66); }
      // the seats
      T.seats.forEach((S, i) => { const [x, y] = SEAT[i], out = S.out || (i && S.stack <= 0 && T.stage !== "hand"); if (i) face(p, x, y - 20, S.id, now, out || S.folded);
        const bx = i === 0 ? x - 140 : x - 46, by = i === 0 ? y + 28 : y + 18; p.fillStyle = T.toAct === i && T.stage === "hand" ? "rgba(255,224,112,0.9)" : "rgba(0,0,0,0.6)"; p.fillRect(bx, by, 92, 30); p.fillStyle = T.toAct === i && T.stage === "hand" ? "#2A1A08" : "#F0E0B0"; p.font = "bold 11px Georgia"; p.fillText(i ? HE.RES[S.id].short : "You", bx + 5, by + 12); p.font = "11px monospace"; p.fillText(`${S.stack}`, bx + 5, by + 25);
        if (T.button === i && T.stage !== "between" || (T.button === i && T.hand)) { p.fillStyle = "#F8F8F0"; p.beginPath(); p.arc(bx + 82, by + 15, 8, 0, Math.PI * 2); p.fill(); p.fillStyle = "#202020"; p.font = "bold 9px sans-serif"; p.fillText("D", bx + 79, by + 18); }
        if (S.cards && !S.folded) { const t = Math.min(1, (now - A.deal) / 300 - i * 0.15), up = i === 0 || (A.shown[i] && now >= A.shown[i]), cx = i === 0 ? x : x + (x < CX ? 52 : x > CX ? -52 : 0), cy = i === 0 ? y - 12 : y + (y < 150 ? 50 : 6);
          for (let k = 0; k < 2; k++) { if (t <= 0) break; const tx = i === 0 ? cx - 20 + k * 40 : cx - 9 + k * 20, ty = cy, fx = CX + (tx - CX) * t, fy = CY - 120 + (ty - CY + 120) * t; card(p, fx, fy, S.cards[k], up && t >= 1, i === 0 ? 1.05 : 0.8); }
          if (A.cats && A.cats[i] !== undefined && up) { p.fillStyle = "rgba(0,0,0,0.65)"; p.fillRect(cx - 50, cy + 24, 100, 16); p.fillStyle = A.win && A.win.seat === i ? "#FFE070" : "#E0E0E0"; p.font = "bold 10px Georgia"; p.textAlign = "center"; p.fillText(HE.CATS[A.cats[i]], cx, cy + 36); p.textAlign = "left"; } }
        if (S.bet > 0 && T.stage === "hand") { const tx = x + (CX - x) * 0.35, ty = y + (CY - y) * 0.35 + 10; chips(p, tx, ty, S.bet); p.fillStyle = "#FFF0C0"; p.font = "10px monospace"; p.fillText(String(S.bet), tx + 12, ty + 4); }
        const B = A.bub[i]; if (B && now >= B.at && now - B.at < 2600) { const a = Math.min(1, (2600 - (now - B.at)) / 400); p.globalAlpha = a; p.font = "12px Georgia"; const w = Math.min(220, p.measureText(B.text).width + 16), bx2 = Math.max(4, Math.min(W - w - 4, x - w / 2)), by2 = i === 0 ? y - 90 : y - 72; p.fillStyle = "#FBF4E0"; p.beginPath(); p.moveTo(bx2 + 6, by2); p.arcTo(bx2 + w, by2, bx2 + w, by2 + 22, 6); p.arcTo(bx2 + w, by2 + 22, bx2, by2 + 22, 6); p.lineTo(x + 6, by2 + 22); p.lineTo(x, by2 + 30); p.lineTo(x - 4, by2 + 22); p.arcTo(bx2, by2 + 22, bx2, by2, 6); p.arcTo(bx2, by2, bx2 + w, by2, 6); p.fill(); p.fillStyle = "#2A2010"; p.fillText(B.text, bx2 + 8, by2 + 15, w - 12); p.globalAlpha = 1; } });
      // chips in flight
      A.flights = A.flights.filter((f) => now - f.at < 600); for (const f of A.flights) { const t = (now - f.at) / 600; if (t < 0) continue; const e = 1 - (1 - t) * (1 - t); chips(p, f.from[0] + (f.to[0] - f.from[0]) * e, f.from[1] + (f.to[1] - f.from[1]) * e - Math.sin(t * Math.PI) * 30, Math.min(f.n, 40)); }
      if (A.win && now >= A.win.at && now - A.win.at < 2800) { const t = (now - A.win.at) / 2800; p.globalAlpha = t > 0.8 ? (1 - t) / 0.2 : 1; p.fillStyle = "rgba(0,0,0,0.6)"; p.fillRect(CX - 170, CY + 80, 340, 30); p.fillStyle = A.win.seat === 0 ? "#FFE070" : "#F0E0B0"; p.font = "bold 16px Georgia"; p.textAlign = "center"; p.fillText(A.win.text, CX, CY + 101); p.textAlign = "left"; p.globalAlpha = 1;
        if (A.win.seat === 0 && t < 0.5) for (let k = 0; k < 12; k++) { const a = k * 0.52 + now / 300, r = 40 + t * 120; p.fillStyle = k % 2 ? "#FFE070" : "#FFFFFF"; p.fillRect(SEAT[0][0] + Math.cos(a) * r, SEAT[0][1] - 20 + Math.sin(a) * r * 0.5, 3, 3); } }
      p.fillStyle = "rgba(0,0,0,0.5)"; p.fillRect(8, 8, 190, 20); p.fillStyle = "#F0E0B0"; p.font = "11px monospace"; p.fillText(`Hand ${T.hand}  Blinds ${T.sb}/${T.bb}  Buy-in ${T.buyin}`, 14, 22);
    },
  });
}
