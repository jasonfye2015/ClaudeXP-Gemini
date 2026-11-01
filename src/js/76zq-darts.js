"use strict";
// The Tavern Board, the window's side: a dartboard hung on the tavern's timber wall under a lamp - its wedges in black
// and cream, the doubles and trebles rings in red and green, the bull, the wire, the numbers round the rim - and the
// hand's crosshair wavering where the mouse is (a slow drift that never quite settles). A click: the dart flies in from
// below and thuds into the board, wobbling as it stops, its score floating up; three darts a round, then they are
// pulled. A chalk-board beside keeps the rounds. The rules are 64zz-fair.js.
CM.CG_TABLES.push(["darts", "The Tavern Board"]);
{ const floor0 = CM.UI.prototype.renderFloor, FA = CM.FAIR, K = FA.darts, S = 420, BR = 180, CX = S / 2, CY = S / 2;
  Object.assign(CM.UI.prototype, {
    renderFloor(box) { if (this.cgView === "darts") return this.cgDarts(box); return floor0.call(this, box); },
    cgDarts(box) {
      const g = this.game, St = g.faState("darts"), live = St && St.stage === "play", bet = live ? St.bet : (this.cgBet === undefined ? 5 : this.cgBet), F = g.cgStore(), C = F.fa_darts_cards || {}, last = St && St.stage === "done" ? St.last : null;
      const rounds = []; if (St) for (let r = 0; r < K.rounds; r++) { const ts = St.throws.slice(r * 3, r * 3 + 3); rounds.push(`<tr><td>${r + 1}</td><td>${ts.map((t) => t.label).join(" · ") || "-"}</td><td>${ts.reduce((a, t) => a + t.pts, 0) || ""}</td></tr>`); }
      box.innerHTML = `<div class="cgtable dartstbl runestack dash"><h3>The Tavern Board</h3><div class="rswrap"><canvas class="dtcanvas" width="${S}" height="${S}"></canvas>
        <div class="dashside"><p class="lore">In the taproom corner a dartboard hangs under a lamp, its cork pocked by a thousand evenings. "Eight rounds of three," says the barman, chalk in hand. "The house pays on the total. A steady hand helps; a tankard does not."</p>
        <table class="dtchalk"><tr><th>Round</th><th>Darts</th><th>Score</th></tr>${rounds.join("")}<tr class="tot"><td colspan="2">Total</td><td>${St ? St.score : 0}</td></tr></table>
        <table class="paytable"><tr><th>Score</th><th>Pays</th></tr>${K.PAY.map(([s, m]) => `<tr class="${St && St.score >= s ? "won" : ""}"><td>${s}+</td><td>${Math.round(bet * m)} gold</td></tr>`).join("")}</table>
        ${live ? "" : this.cgBetRow("The stake")}<div class="cgnote">${this.cgNote || ""}</div>${last && last.cards.length ? last.cards.map((c) => this.cgCardWon(c)).join("") : ""}
        <div class="row">${live ? "" : `<button class="primary" data-dtstart>Chalk up (${bet} gold)</button>`}<button data-leave>Leave</button></div>
        <div class="small">Aim with the mouse and click to throw - the hand wavers, so wait for it. Treble ring triples, the outer ring doubles, the outer bull is 25 and the bull 50. A ticket for every ${K.ticketPer} points; a card the first time ever past ${K.MARKS.join(", ")}${K.MARKS.map((m) => (C[m] ? " ✓" : "")).join("")}. Best ${F.fa_darts_best || 0}.</div>${this.cgStats("darts")}</div></div></div>`;
      this.cgWireBet(box); const q = (s) => box.querySelector(s); q("[data-leave]").addEventListener("click", () => this.closeDialogs());
      if (q("[data-dtstart]")) q("[data-dtstart]").addEventListener("click", () => { const r = g.faStart("darts", bet); this.cgNote = r.error || "Round 1 - three darts."; this.dtStuck = []; this.cgSfx(r.error ? "miss" : "door", 0.4); this.renderCasino(); });
      const cv = this.dtCanvas = q(".dtcanvas");
      cv.addEventListener("mousemove", (e) => { const r = cv.getBoundingClientRect(); this.dtMouse = [((e.clientX - r.left) / r.width) * S, ((e.clientY - r.top) / r.height) * S]; });
      cv.addEventListener("mousedown", () => {
        const St2 = g.faState("darts"); if (!St2 || St2.stage !== "play" || this.dtFly) return; const [mx, my] = this.dtAim || [CX, CY], bx = (mx - CX) / BR, by = (my - CY) / BR, out = g.faThrow("darts", bx, by); if (out.error) return;
        this.dtFly = { at: performance.now(), x: CX + out.x * BR, y: CY + out.y * BR, out }; this.cgSfx("zap", 0.2, 2.2);
      });
      cv.style.cursor = "none";
      if (!this.dtLoop) { let prev = performance.now(); const loop = (now) => { if (!this.dtCanvas || !this.dtCanvas.isConnected || this.cgView !== "darts") { this.dtLoop = null; return; } const dt = Math.min(0.05, (now - prev) / 1000); prev = now; this.dtFrame(dt, now); this.dtLoop = requestAnimationFrame(loop); }; this.dtLoop = requestAnimationFrame(loop); }
    },
    dtFrame(dt, now) {
      const g = this.game, St = g.faState("darts"), live = St && St.stage === "play", p = this.dtCanvas.getContext("2d");
      // the waver: a drift pulled back to the middle, kicked about at random
      const W = this.dtW = this.dtW || { x: 0, y: 0, vx: 0, vy: 0 }; const k = 9, sd = K.waver * BR; W.vx += (-k * W.x * 3 + (Math.random() - 0.5) * sd * 60) * dt; W.vy += (-k * W.y * 3 + (Math.random() - 0.5) * sd * 60) * dt; W.vx *= 1 - 3 * dt; W.vy *= 1 - 3 * dt; W.x += W.vx * dt; W.y += W.vy * dt;
      const m = this.dtMouse || [CX, CY]; this.dtAim = [m[0] + W.x, m[1] + W.y];
      // the wall and the board
      const wall = p.createLinearGradient(0, 0, S, 0); wall.addColorStop(0, "#3A2414"); wall.addColorStop(0.5, "#5A3A20"); wall.addColorStop(1, "#3A2414"); p.fillStyle = wall; p.fillRect(0, 0, S, S); p.strokeStyle = "rgba(0,0,0,0.3)"; for (let x = 0; x < S; x += 42) { p.beginPath(); p.moveTo(x, 0); p.lineTo(x, S); p.stroke(); }
      const lamp = p.createRadialGradient(CX, 0, 10, CX, CY, S * 0.7); lamp.addColorStop(0, "rgba(255,220,150,0.25)"); lamp.addColorStop(1, "rgba(0,0,0,0.3)"); p.fillStyle = lamp; p.fillRect(0, 0, S, S);
      p.fillStyle = "rgba(0,0,0,0.4)"; p.beginPath(); p.arc(CX + 6, CY + 8, BR * 1.16, 0, Math.PI * 2); p.fill(); p.fillStyle = "#1A1410"; p.beginPath(); p.arc(CX, CY, BR * 1.16, 0, Math.PI * 2); p.fill();
      const R = FA.RING, ring = (r0, r1, a0, a1, c) => { p.fillStyle = c; p.beginPath(); p.arc(CX, CY, r1 * BR, a0, a1); p.arc(CX, CY, r0 * BR, a1, a0, true); p.closePath(); p.fill(); };
      for (let i = 0; i < 20; i++) { const a0 = -Math.PI / 2 - Math.PI / 20 + (i * Math.PI) / 10, a1 = a0 + Math.PI / 10, dark = i % 2 === 0; ring(R.outer, R.tIn, a0, a1, dark ? "#1A1A1A" : "#E8DCC0"); ring(R.tIn, R.tOut, a0, a1, dark ? "#C02828" : "#208040"); ring(R.tOut, R.dIn, a0, a1, dark ? "#1A1A1A" : "#E8DCC0"); ring(R.dIn, 1, a0, a1, dark ? "#C02828" : "#208040");
        const am = (a0 + a1) / 2; p.fillStyle = "#F0E8D0"; p.font = "bold 15px Georgia"; p.textAlign = "center"; p.fillText(String(FA.ORDER[i]), CX + Math.cos(am) * BR * 1.08, CY + Math.sin(am) * BR * 1.08 + 5); }
      p.textAlign = "left"; p.fillStyle = "#208040"; p.beginPath(); p.arc(CX, CY, R.outer * BR, 0, Math.PI * 2); p.fill(); p.fillStyle = "#C02828"; p.beginPath(); p.arc(CX, CY, R.bull * BR, 0, Math.PI * 2); p.fill();
      p.strokeStyle = "rgba(200,200,210,0.55)"; p.lineWidth = 0.8; for (const r of [R.outer, R.tIn, R.tOut, R.dIn, 1]) { p.beginPath(); p.arc(CX, CY, r * BR, 0, Math.PI * 2); p.stroke(); } for (let i = 0; i < 20; i++) { const a = -Math.PI / 2 - Math.PI / 20 + (i * Math.PI) / 10; p.beginPath(); p.moveTo(CX + Math.cos(a) * R.outer * BR, CY + Math.sin(a) * R.outer * BR); p.lineTo(CX + Math.cos(a) * BR, CY + Math.sin(a) * BR); p.stroke(); } p.lineWidth = 1;
      const dart = (x, y, wob) => { p.save(); p.translate(x, y); p.rotate(-0.5 + wob); p.fillStyle = "rgba(0,0,0,0.35)"; p.fillRect(4, 4, 24, 3); p.fillStyle = "#C0C0C8"; p.fillRect(0, -1, 8, 2); p.fillStyle = "#8A5A20"; p.fillRect(8, -2.5, 12, 5); p.fillStyle = "#C03030"; p.beginPath(); p.moveTo(20, 0); p.lineTo(30, -7); p.lineTo(28, 0); p.lineTo(30, 7); p.fill(); p.restore(); };
      for (const d of this.dtStuck || []) dart(d.x, d.y, Math.sin((now - d.at) / 40) * Math.max(0, 1 - (now - d.at) / 500) * 0.3);
      // a dart in flight
      if (this.dtFly) { const F2 = this.dtFly, t = Math.min(1, (now - F2.at) / 220), sx = CX + 60, sy = S + 40, x = sx + (F2.x - sx) * t, y = sy + (F2.y - sy) * t - Math.sin(t * Math.PI) * 60; dart(x, y, 0);
        if (t >= 1) { this.dtFly = null; const o = F2.out; (this.dtStuck = this.dtStuck || []).push({ x: F2.x, y: F2.y, at: now }); (this.dtPts = this.dtPts || []).push({ x: F2.x, y: F2.y - 14, text: o.pts ? o.label : "Miss", at: now, big: o.pts >= 40 });
          this.cgSfx(o.pts ? "bump" : "step", 0.5, o.pts ? 1.4 : 0.7); if (o.pts >= 50 || o.label.startsWith("T")) this.cgSfx("coin", 0.4, 1.5);
          if (o.over) { this.cgNote = `${o.score} points: ${o.gold ? `${o.gold} gold back` : "nothing back"}, and ${o.tickets} tickets.`; if (o.gold) this.cgCoins(this.$("#casino-body"), 10); if (o.cards.length) this.cgSfx("cardwin", 0.5); setTimeout(() => this.renderCasino(), 500); }
          else if (o.n % 3 === 0) { this.cgNote = `Round ${o.n / 3} done - ${o.score} so far. Round ${o.n / 3 + 1}.`; setTimeout(() => { this.dtStuck = []; this.renderCasino(); }, 650); } else this.renderCasino(); } }
      this.dtPts = (this.dtPts || []).filter((q) => now - q.at < 900); for (const q of this.dtPts) { p.globalAlpha = 1 - (now - q.at) / 900; p.fillStyle = q.big ? "#FFE070" : "#FFFFFF"; p.strokeStyle = "#000"; p.lineWidth = 3; p.font = `bold ${q.big ? 22 : 16}px Georgia`; p.textAlign = "center"; p.strokeText(q.text, q.x, q.y - (now - q.at) / 30); p.fillText(q.text, q.x, q.y - (now - q.at) / 30); p.textAlign = "left"; } p.globalAlpha = 1; p.lineWidth = 1;
      if (live && !this.dtFly) { const [ax, ay] = this.dtAim; p.strokeStyle = "rgba(255,255,255,0.9)"; p.lineWidth = 1.5; p.beginPath(); p.arc(ax, ay, 10, 0, Math.PI * 2); p.moveTo(ax - 16, ay); p.lineTo(ax - 5, ay); p.moveTo(ax + 5, ay); p.lineTo(ax + 16, ay); p.moveTo(ax, ay - 16); p.lineTo(ax, ay - 5); p.moveTo(ax, ay + 5); p.lineTo(ax, ay + 16); p.stroke(); p.lineWidth = 1; p.fillStyle = "#FF4040"; p.fillRect(ax - 1, ay - 1, 2, 2);
        p.fillStyle = "rgba(0,0,0,0.5)"; p.fillRect(8, S - 30, 150, 22); p.fillStyle = "#FFE070"; p.font = "bold 13px monospace"; p.fillText(`ROUND ${Math.min(8, Math.floor(St.throws.length / 3) + 1)}  DART ${St.throws.length % 3 + 1}`, 14, S - 14); }
      if (!live && !this.dtFly) { p.fillStyle = "rgba(0,0,0,0.35)"; p.fillRect(0, S - 40, S, 40); p.fillStyle = "#F0E0B0"; p.font = "15px Georgia"; p.textAlign = "center"; p.fillText(St && St.last ? `Last game: ${St.last.score} points` : "Set a stake and chalk up", CX, S - 15); p.textAlign = "left"; }
    },
  });
}
