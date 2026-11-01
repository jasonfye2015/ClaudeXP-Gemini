"use strict";
// Rune-Roll, the window's side: a skee lane in perspective - polished boards running up to a ramp and the target, its
// rings carved with runes and numbered (10 to 50), the two little 100 cups high in the corners, a lit marquee over it
// all and a ticket slot that spits a strip of pink tickets at the end. Move the mouse to aim (a ghost ball shows where
// it will go), hold the button to wind up the power (the meter climbs and falls back), let go to roll: the ball rattles
// up the lane, hops the ramp, arcs and drops into its ring with a glow. The rules are 64zz-fair.js.
CM.CG_TABLES.push(["skee", "Rune-Roll"]);
{ const floor0 = CM.UI.prototype.renderFloor, FA = CM.FAIR, K = FA.skee, W = 420, H = 560, TX = W / 2, TY = 120, TS = 140;
  // the target plane: x -1..1, y 0..1.2 (up), to the canvas
  const tgt = (x, y) => [TX + x * TS, TY + 110 - y * 100];
  Object.assign(CM.UI.prototype, {
    renderFloor(box) { if (this.cgView === "skee") return this.cgSkee(box); return floor0.call(this, box); },
    cgSkee(box) {
      const g = this.game, St = g.faState("skee"), live = St && St.stage === "play", bet = live ? St.bet : (this.cgBet === undefined ? 5 : this.cgBet), F = g.cgStore(), C = F.fa_skee_cards || {}, last = St && St.stage === "done" ? St.last : null;
      box.innerHTML = `<div class="cgtable skeetbl runestack dash"><h3>Rune-Roll</h3><div class="rswrap"><canvas class="skcanvas" width="${W}" height="${H}"></canvas>
        <div class="dashside"><p class="lore">A row of long wooden lanes at the back of the arcade wing, each ending in a target of carved rings. "Nine balls," says the attendant, setting them clacking into the trough. "Roll them up, not throw them. The little cups at the top are worth a hundred - if you can find them."</p>
        <div class="skballs">${Array.from({ length: K.balls }, (_, i) => { const t = St && St.throws[i]; return `<span class="${t ? "used" : ""}">${t ? t.pts : ""}</span>`; }).join("")}</div><div class="sktotal">Score <b>${St ? St.score : 0}</b></div>
        <table class="paytable"><tr><th>Score</th><th>Pays</th></tr>${K.PAY.map(([s, m]) => `<tr class="${St && St.score >= s ? "won" : ""}"><td>${s}+</td><td>${Math.round(bet * m)} gold</td></tr>`).join("")}</table>
        ${live ? "" : this.cgBetRow("The stake")}<div class="cgnote">${this.cgNote || ""}</div>${last && last.cards.length ? last.cards.map((c) => this.cgCardWon(c)).join("") : ""}
        <div class="row">${live ? "" : `<button class="primary" data-skstart>Drop the balls (${bet} gold)</button>`}<button data-leave>Leave</button></div>
        <div class="small">Move the mouse across the lane to aim; hold the button to wind up and let go to roll. A soft roll stops in the lower rings, a hard one reaches the top - and strays more. A ticket for every ${K.ticketPer} points; a card the first time ever past ${K.MARKS.join(", ")}${K.MARKS.map((m) => (C[m] ? " ✓" : "")).join("")}. Best ${F.fa_skee_best || 0}.</div>${this.cgStats("skee")}</div></div></div>`;
      this.cgWireBet(box); const q = (s) => box.querySelector(s); q("[data-leave]").addEventListener("click", () => this.closeDialogs());
      if (q("[data-skstart]")) q("[data-skstart]").addEventListener("click", () => { const r = g.faStart("skee", bet); this.cgNote = r.error || "Nine balls - roll them up."; this.skIn = []; this.cgSfx(r.error ? "miss" : "chain", 0.4); this.renderCasino(); });
      const cv = this.skCanvas = q(".skcanvas");
      cv.addEventListener("mousemove", (e) => { const r = cv.getBoundingClientRect(); this.skAim = CM.ARC.clamp((((e.clientX - r.left) / r.width) * W - TX) / TS, -1, 1); });
      cv.addEventListener("mousedown", () => { const S2 = g.faState("skee"); if (!S2 || S2.stage !== "play" || this.skBall) return; this.skHold = performance.now(); });
      const let_go = () => { if (!this.skHold) return; const S2 = g.faState("skee"), pw = this.skPower || 0; this.skHold = 0; if (!S2 || S2.stage !== "play") return; const out = g.faThrow("skee", this.skAim || 0, pw); if (out.error) return; this.skBall = { at: performance.now(), out, aim: this.skAim || 0 }; this.cgSfx("grind", 0.35, 1.4); };
      cv.addEventListener("mouseup", let_go); cv.addEventListener("mouseleave", let_go);
      if (!this.skLoop) { const loop = (now) => { if (!this.skCanvas || !this.skCanvas.isConnected || this.cgView !== "skee") { this.skLoop = null; return; } this.skFrame(now); this.skLoop = requestAnimationFrame(loop); }; this.skLoop = requestAnimationFrame(loop); }
    },
    skFrame(now) {
      const g = this.game, St = g.faState("skee"), live = St && St.stage === "play", p = this.skCanvas.getContext("2d");
      if (this.skHold) { const t = ((now - this.skHold) / 1300) % 2; this.skPower = t < 1 ? t : 2 - t; }
      p.fillStyle = "#1A1210"; p.fillRect(0, 0, W, H);
      // the marquee
      p.fillStyle = "#4A1A30"; p.fillRect(30, 6, W - 60, 34); p.strokeStyle = "#F0C040"; p.lineWidth = 2; p.strokeRect(30, 6, W - 60, 34); p.lineWidth = 1; for (let k = 0; k < 16; k++) { p.fillStyle = (Math.floor(now / 160) + k) % 3 ? "#7A5A20" : "#FFF0A0"; p.beginPath(); p.arc(40 + k * ((W - 80) / 15), 44, 3, 0, Math.PI * 2); p.fill(); } p.fillStyle = "#FFE070"; p.font = "bold 18px Georgia"; p.textAlign = "center"; p.fillText("RUNE · ROLL", TX, 30); p.textAlign = "left";
      // the target
      p.fillStyle = "#3A2418"; p.beginPath(); p.moveTo(TX - TS - 20, TY + 130); p.lineTo(TX - TS - 10, TY - 30); p.lineTo(TX + TS + 10, TY - 30); p.lineTo(TX + TS + 20, TY + 130); p.fill();
      const [cx, cy] = tgt(0, 0.6); [[0.43, "#6A4A2A", "10"], [0.31, "#7A3A2A", "20"], [0.2, "#5A3A6A", "30"], [0.1, "#3A5A7A", "40"]].forEach(([r, c, t]) => { p.fillStyle = c; p.beginPath(); p.ellipse(cx, cy, r * TS, r * 100, 0, 0, Math.PI * 2); p.fill(); p.strokeStyle = "#C8A040"; p.stroke(); p.fillStyle = "#F0D070"; p.font = "bold 11px Georgia"; p.fillText(t, cx - 6, cy - r * 100 + 13); });
      p.fillStyle = "#101010"; p.beginPath(); p.ellipse(cx, cy, 0.1 * TS * 0.7, 7, 0, 0, Math.PI * 2); p.fill(); p.fillStyle = "#FFE070"; p.font = "bold 12px Georgia"; p.fillText("50", cx - 7, cy + 22);
      for (const sx of [-0.58, 0.58]) { const [hx, hy] = tgt(sx, 1.02); p.fillStyle = "#101010"; p.beginPath(); p.ellipse(hx, hy, 0.065 * TS, 6, 0, 0, Math.PI * 2); p.fill(); p.strokeStyle = "#F0C040"; p.stroke(); p.fillStyle = "#FFE070"; p.font = "bold 11px Georgia"; p.fillText("100", hx - 10, hy - 9); }
      const glow = p.createRadialGradient(cx, cy, 10, cx, cy, 160); glow.addColorStop(0, "rgba(255,220,140,0.12)"); glow.addColorStop(1, "rgba(0,0,0,0)"); p.fillStyle = glow; p.fillRect(0, 0, W, 300);
      for (const b of this.skIn || []) { const [x, y] = tgt(b.x, b.y), k = Math.max(0, 1 - (now - b.at) / 700); if (k > 0) { p.fillStyle = `rgba(255,240,160,${k * 0.6})`; p.beginPath(); p.arc(x, y, 14 + (1 - k) * 20, 0, Math.PI * 2); p.fill(); } }
      // the lane, in perspective
      const ramp = TY + 150, laneTop = ramp + 10, laneBot = H - 20; p.fillStyle = "#6A4A28"; p.beginPath(); p.moveTo(TX - 70, laneTop); p.lineTo(TX + 70, laneTop); p.lineTo(TX + 170, laneBot); p.lineTo(TX - 170, laneBot); p.fill();
      p.strokeStyle = "rgba(0,0,0,0.25)"; for (let k = -4; k <= 4; k++) { p.beginPath(); p.moveTo(TX + k * 15, laneTop); p.lineTo(TX + k * 37, laneBot); p.stroke(); } p.fillStyle = "rgba(255,240,200,0.06)"; p.beginPath(); p.moveTo(TX - 30, laneTop); p.lineTo(TX + 10, laneTop); p.lineTo(TX + 30, laneBot); p.lineTo(TX - 80, laneBot); p.fill();
      p.fillStyle = "#8A5A30"; p.beginPath(); p.moveTo(TX - 70, laneTop); p.lineTo(TX + 70, laneTop); p.lineTo(TX + 64, ramp - 6); p.lineTo(TX - 64, ramp - 6); p.fill();
      const ball = (x, y, r) => { const gr = p.createRadialGradient(x - r * 0.35, y - r * 0.35, 1, x, y, r); gr.addColorStop(0, "#F0D8A8"); gr.addColorStop(1, "#8A5A28"); p.fillStyle = gr; p.beginPath(); p.arc(x, y, r, 0, Math.PI * 2); p.fill(); };
      // the roll
      if (this.skBall) { const B = this.skBall, t = (now - B.at) / 1000, o = B.out, startX = TX + B.aim * 150;
        if (t < 0.55) { const k = t / 0.55, y = laneBot - 20 - (laneBot - 20 - ramp) * k, x = startX + (TX + B.aim * 62 - startX) * k + Math.sin(t * 60) * 1.2; ball(x, y, 12 - k * 6); }
        else if (t < 1.05) { const k = (t - 0.55) / 0.5, [ex, ey] = tgt(o.x, o.y), x0 = TX + B.aim * 62, y0 = ramp - 6, x = x0 + (ex - x0) * k, y = y0 + (ey - y0) * k - Math.sin(k * Math.PI) * 70; p.fillStyle = "rgba(0,0,0,0.3)"; p.beginPath(); p.ellipse(x, y0 + (ey - y0) * k + 4, 6, 2, 0, 0, Math.PI * 2); p.fill(); ball(x, y, 6); }
        else { this.skBall = null; (this.skIn = this.skIn || []).push({ x: o.x, y: o.y, at: now }); (this.skPts = this.skPts || []).push({ ...o, at: now }); this.cgSfx(o.pts >= 100 ? "cardwin" : o.pts >= 40 ? "coin" : o.pts ? "bump" : "miss", 0.45, o.pts ? 1 + o.pts / 200 : 0.7);
          if (o.over) { this.cgNote = `${o.score} points: ${o.gold ? `${o.gold} gold back` : "nothing back"}, and ${o.tickets} tickets.`; this.skTickets = { at: now, n: o.tickets }; if (o.gold) this.cgCoins(this.$("#casino-body"), 10); if (o.cards.length) this.cgSfx("cardwin", 0.5); setTimeout(() => this.renderCasino(), 1600); } else this.renderCasino(); } }
      this.skPts = (this.skPts || []).filter((q) => now - q.at < 1000); for (const q of this.skPts) { const [x, y] = tgt(q.x, q.y); p.globalAlpha = 1 - (now - q.at) / 1000; p.fillStyle = q.pts >= 100 ? "#FFE070" : "#FFFFFF"; p.strokeStyle = "#000"; p.lineWidth = 3; p.font = `bold ${q.pts >= 50 ? 22 : 16}px Georgia`; p.textAlign = "center"; p.strokeText(q.label, x, y - 16 - (now - q.at) / 30); p.fillText(q.label, x, y - 16 - (now - q.at) / 30); p.textAlign = "left"; } p.globalAlpha = 1; p.lineWidth = 1;
      // aiming: the ghost ball and the power
      if (live && !this.skBall) { const a = this.skAim || 0; p.globalAlpha = 0.45; ball(TX + a * 150, laneBot - 20, 12); p.globalAlpha = 1; p.strokeStyle = "rgba(255,255,255,0.25)"; p.setLineDash([4, 6]); p.beginPath(); p.moveTo(TX + a * 150, laneBot - 30); p.lineTo(TX + a * 62, ramp); p.stroke(); p.setLineDash([]);
        const pw = this.skHold ? this.skPower || 0 : 0; p.fillStyle = "rgba(0,0,0,0.5)"; p.fillRect(W - 34, laneTop, 20, laneBot - laneTop); const pg = p.createLinearGradient(0, laneBot, 0, laneTop); pg.addColorStop(0, "#40C060"); pg.addColorStop(0.6, "#F0C040"); pg.addColorStop(1, "#E04030"); p.fillStyle = pg; p.fillRect(W - 32, laneBot - (laneBot - laneTop) * pw, 16, (laneBot - laneTop) * pw); p.fillStyle = "#F0E0B0"; p.font = "10px Georgia"; p.fillText("POWER", W - 46, laneTop - 4); }
      if (this.skTickets && now - this.skTickets.at < 2500) { const k = Math.min(1, (now - this.skTickets.at) / 1500), len = 20 + k * 120; p.fillStyle = "#E04080"; p.fillRect(18, H - 30 - len, 26, len); p.fillStyle = "#FFD0E8"; for (let y = H - 30 - len + 6; y < H - 30; y += 12) p.fillRect(22, y, 18, 1); p.fillStyle = "#FFF"; p.font = "bold 12px monospace"; p.fillText(`${this.skTickets.n}`, 50, H - 34); }
      if (!live && !this.skBall) { p.fillStyle = "rgba(0,0,0,0.35)"; p.fillRect(0, H - 50, W, 50); p.fillStyle = "#F0E0B0"; p.font = "15px Georgia"; p.textAlign = "center"; p.fillText(St && St.last ? `Last game: ${St.last.score} points` : "Set a stake and drop the balls", TX, H - 22); p.textAlign = "left"; }
    },
  });
}
