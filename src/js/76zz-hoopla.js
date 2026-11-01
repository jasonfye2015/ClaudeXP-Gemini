"use strict";
// Hoop-la, the window's side: a striped fairground booth with bunting, a sloped table of bottles in perspective - green
// at the front, blue behind, gold at the back and the single red one - each with a glint on its glass; wooden rings
// thrown from the bottom in an arc, spinning flat as they fly, and either dropping over a neck with a clink (the bottle
// lights, its points float up) or rattling off across the table. Aim with the mouse, hold to wind up the throw, let go.
// The rules are 64zze-fair2.js (a fair game of 64zz-fair.js).
CM.CG_TABLES.push(["rings", "Hoop-la"]);
{ const floor0 = CM.UI.prototype.renderFloor, FA = CM.FAIR, K = FA.rings, W = 440, H = 460, COL = { 1: "#3A9A50", 2: "#3A70C0", 5: "#D0A020", 10: "#C02830" };
  // the table plane x -1..1, y 0..1 (far) to the canvas
  const proj = (x, y) => { const s = 1 - y * 0.45, Y = 400 - y * 230; return [W / 2 + x * 170 * s, Y, s]; };
  Object.assign(CM.UI.prototype, {
    renderFloor(box) { if (this.cgView === "rings") return this.cgHoopla(box); return floor0.call(this, box); },
    cgHoopla(box) {
      const g = this.game, St = g.faState("rings"), live = St && St.stage === "play", bet = live ? St.bet : (this.cgBet === undefined ? 5 : this.cgBet), F = g.cgStore(), C = F.fa_rings_cards || {}, last = St && St.stage === "done" ? St.last : null;
      box.innerHTML = `<div class="cgtable hoopla runestack dash"><h3>Hoop-la</h3><div class="rswrap"><canvas class="hpcanvas" width="${W}" height="${H}"></canvas>
        <div class="dashside"><p class="lore">A striped booth hung with bunting, and a sloped table crowded with bottles. "Ten rings!" calls the barker. "Green's a point, blue two, gold five - and the red one, the red one's ten. Over the neck, mind, not just touching."</p>
        <div class="skballs">${Array.from({ length: K.balls }, (_, i) => { const t = St && St.throws[i]; return `<span class="ring ${t ? "used" : ""}">${t ? t.pts || "·" : ""}</span>`; }).join("")}</div><div class="sktotal">Points <b>${St ? St.score : 0}</b></div>
        <table class="paytable"><tr><th>Points</th><th>Pays</th></tr>${K.PAY.map(([s, m]) => `<tr class="${St && St.score >= s ? "won" : ""}"><td>${s}+</td><td>${Math.round(bet * m)} gold</td></tr>`).join("")}</table>
        ${live ? "" : this.cgBetRow("The stake")}<div class="cgnote">${this.cgNote || ""}</div>${last && last.cards.length ? last.cards.map((c) => this.cgCardWon(c)).join("") : ""}
        <div class="row">${live ? "" : `<button class="primary" data-hpstart>Ten rings (${bet} gold)</button>`}<button data-leave>Leave</button></div>
        <div class="small">Aim across with the mouse; hold to wind up how far, let go to throw - the far bottles need more and the throw strays more. A ticket for every point; a card the first time ever past ${K.MARKS.join(", ")}${K.MARKS.map((m) => (C[m] ? " ✓" : "")).join("")}. Best ${F.fa_rings_best || 0}.</div>${this.cgStats("rings")}</div></div></div>`;
      this.cgWireBet(box); const q = (s) => box.querySelector(s); q("[data-leave]").addEventListener("click", () => this.closeDialogs());
      if (q("[data-hpstart]")) q("[data-hpstart]").addEventListener("click", () => { const r = g.faStart("rings", bet); this.cgNote = r.error || "Ten rings - over the neck!"; this.hpOn = []; this.cgSfx(r.error ? "miss" : "chain", 0.4); this.renderCasino(); });
      const cv = this.hpCanvas = q(".hpcanvas");
      cv.addEventListener("mousemove", (e) => { const r = cv.getBoundingClientRect(); this.hpAim = CM.ARC.clamp((((e.clientX - r.left) / r.width) * W - W / 2) / 170, -1, 1); });
      cv.addEventListener("mousedown", () => { const S2 = g.faState("rings"); if (S2 && S2.stage === "play" && !this.hpFly) this.hpHold = performance.now(); });
      const go = () => { if (!this.hpHold) return; this.hpHold = 0; const out = g.faThrow("rings", this.hpAim || 0, this.hpPow || 0); if (out.error) return; this.hpFly = { at: performance.now(), out }; this.cgSfx("zap", 0.2, 1.1); };
      cv.addEventListener("mouseup", go); cv.addEventListener("mouseleave", go);
      if (!this.hpLoop) { const loop = (now) => { if (!this.hpCanvas || !this.hpCanvas.isConnected || this.cgView !== "rings") { this.hpLoop = null; return; } this.hpFrame(now); this.hpLoop = requestAnimationFrame(loop); }; this.hpLoop = requestAnimationFrame(loop); }
    },
    hpFrame(now) {
      const g = this.game, St = g.faState("rings"), live = St && St.stage === "play", p = this.hpCanvas.getContext("2d");
      if (this.hpHold) { const t = ((now - this.hpHold) / 1200) % 2; this.hpPow = t < 1 ? t : 2 - t; }
      // the booth
      for (let k = 0; k < 11; k++) { p.fillStyle = k % 2 ? "#F0E8D8" : "#C03040"; p.fillRect(k * 40, 0, 40, H); } p.fillStyle = "rgba(0,0,0,0.35)"; p.fillRect(0, 0, W, H);
      for (let k = 0; k < 14; k++) { p.fillStyle = ["#F04060", "#F0C040", "#40A0F0", "#60C060"][k % 4]; p.beginPath(); p.moveTo(k * 32, 4); p.lineTo(k * 32 + 32, 4); p.lineTo(k * 32 + 16, 26 + Math.sin(now / 400 + k) * 2); p.fill(); }
      // the table
      const [ax, ay] = proj(-1.05, -0.05), [bx, by] = proj(1.05, -0.05), [cx, cy] = proj(1.05, 1.08), [dx, dy] = proj(-1.05, 1.08); p.fillStyle = "#6A4A2A"; p.beginPath(); p.moveTo(ax, ay); p.lineTo(bx, by); p.lineTo(cx, cy); p.lineTo(dx, dy); p.fill(); p.strokeStyle = "#3A2410"; p.lineWidth = 4; p.stroke(); p.lineWidth = 1;
      // bottles, far first
      const on = this.hpOn = this.hpOn || [];
      for (const B of FA.BOTTLES.slice().sort((a, b) => b.y - a.y)) { const [x, y, s] = proj(B.x, B.y), h = 46 * s, w = 13 * s, lit = on.find((o) => o.B === B); p.fillStyle = "rgba(0,0,0,0.3)"; p.beginPath(); p.ellipse(x + 3 * s, y, w * 0.8, w * 0.3, 0, 0, Math.PI * 2); p.fill();
        const gl = p.createLinearGradient(x - w / 2, 0, x + w / 2, 0); gl.addColorStop(0, COL[B.pts]); gl.addColorStop(0.35, "#FFFFFF"); gl.addColorStop(0.5, COL[B.pts]); gl.addColorStop(1, "#101010"); p.fillStyle = gl; p.globalAlpha = 0.9;
        p.beginPath(); p.moveTo(x - w / 2, y); p.lineTo(x - w / 2, y - h * 0.55); p.quadraticCurveTo(x - w / 2, y - h * 0.7, x - w * 0.18, y - h * 0.78); p.lineTo(x - w * 0.18, y - h); p.lineTo(x + w * 0.18, y - h); p.lineTo(x + w * 0.18, y - h * 0.78); p.quadraticCurveTo(x + w / 2, y - h * 0.7, x + w / 2, y - h * 0.55); p.lineTo(x + w / 2, y); p.fill(); p.globalAlpha = 1;
        if (lit) { p.strokeStyle = "#C89050"; p.lineWidth = 4 * s; p.beginPath(); p.ellipse(x, y - h * 0.68, 11 * s, 4 * s, 0, 0, Math.PI * 2); p.stroke(); p.lineWidth = 1; if (now - lit.at < 800) { p.fillStyle = `rgba(255,240,150,${1 - (now - lit.at) / 800})`; p.beginPath(); p.arc(x, y - h / 2, 22 * s, 0, Math.PI * 2); p.fill(); } } }
      // a ring in flight
      if (this.hpFly) { const F = this.hpFly, t = (now - F.at) / 650, o = F.out, [tx, ty, ts] = proj(o.x, Math.min(1.1, o.y)), sx = W / 2 + (this.hpAim || 0) * 80, sy = H - 20;
        if (t < 1) { const x = sx + (tx - sx) * t, y = sy + (ty - 30 * ts - sy) * t - Math.sin(t * Math.PI) * 120, s = 1 - t * (1 - ts); p.strokeStyle = "#C89050"; p.lineWidth = 5 * s; p.beginPath(); p.ellipse(x, y, 16 * s, 6 * s * (0.5 + 0.5 * Math.abs(Math.cos(t * 9))), 0, 0, Math.PI * 2); p.stroke(); p.lineWidth = 1; }
        else { this.hpFly = null; if (o.pts) { const B = FA.BOTTLES.find((b) => b.x === o.x && b.y === o.y); on.push({ B, at: now }); this.cgSfx("tablebell", 0.4, 1 + o.pts / 10); } else this.cgSfx("bump", 0.3, 1.6); (this.hpPts = this.hpPts || []).push({ x: tx, y: ty - 50 * ts, text: o.pts ? `+${o.pts}` : o.label, at: now, good: o.pts > 0 });
          if (o.over) { this.cgNote = `${o.score} points: ${o.gold ? `${o.gold} gold back` : "nothing back"}, and ${o.tickets} tickets.`; if (o.gold) this.cgCoins(this.$("#casino-body"), 10); if (o.cards.length) this.cgSfx("cardwin", 0.5); setTimeout(() => this.renderCasino(), 900); } else this.renderCasino(); } }
      this.hpPts = (this.hpPts || []).filter((q) => now - q.at < 1000); for (const q of this.hpPts) { p.globalAlpha = 1 - (now - q.at) / 1000; p.fillStyle = q.good ? "#FFE070" : "#F0E0D0"; p.font = `bold ${q.good ? 20 : 13}px Georgia`; p.textAlign = "center"; p.fillText(q.text, q.x, q.y - (now - q.at) / 25); p.textAlign = "left"; } p.globalAlpha = 1;
      if (live && !this.hpFly) { const a = this.hpAim || 0, sx = W / 2 + a * 80; p.strokeStyle = "#C89050"; p.lineWidth = 5; p.beginPath(); p.ellipse(sx, H - 22, 16, 6, 0, 0, Math.PI * 2); p.stroke(); p.lineWidth = 1;
        const pw = this.hpHold ? this.hpPow || 0 : 0, [gx, gy] = proj(a, 0.05 + pw); p.strokeStyle = "rgba(255,255,255,0.4)"; p.setLineDash([4, 6]); p.beginPath(); p.moveTo(sx, H - 30); p.quadraticCurveTo((sx + gx) / 2, gy - 60, gx, gy); p.stroke(); p.setLineDash([]);
        p.fillStyle = "rgba(0,0,0,0.5)"; p.fillRect(W - 26, 160, 14, 220); const pg = p.createLinearGradient(0, 380, 0, 160); pg.addColorStop(0, "#40C060"); pg.addColorStop(1, "#E04030"); p.fillStyle = pg; p.fillRect(W - 24, 380 - 216 * pw, 10, 216 * pw); }
      if (!live && !this.hpFly) { p.fillStyle = "rgba(0,0,0,0.45)"; p.fillRect(0, H - 46, W, 46); p.fillStyle = "#F0E0B0"; p.font = "15px Georgia"; p.textAlign = "center"; p.fillText(St && St.last ? `Last game: ${St.last.score} points` : "Set a stake and take your rings", W / 2, H - 18); p.textAlign = "left"; }
    },
  });
}
