"use strict";
// The Drop Board, the window's side: a tall board of midnight blue with twelve rows of brass pegs that ring and glow
// when struck, and thirteen bins along the foot in a heat of colours - cool in the middle where the small returns are,
// hot at the edges where the big ones wait (the high board's corners blaze). A big gilt chip stamped with the Joker is
// dropped from the top and bounces peg to peg, spinning, to its bin; the bin flares and the multiple floats up.
// Several chips can be falling at once. Pick the board (low, middle, high risk) and the stake. The rules are
// 64zzj-draws.js.
CM.CG_TABLES.push(["plinko", "The Drop Board"]);
{ const floor0 = CM.UI.prototype.renderFloor, PK = CM.PK, W = 420, H = 440, ROWS = PK.rows, SP = 29, TOP = 58, RH = 27, CHIP = 9, NAMES = { low: "Low", med: "Middle", high: "High" };
  const pegX = (r, j) => W / 2 + (j - r / 2) * SP, pegY = (r) => TOP + r * RH, binX = (b) => W / 2 + (b - ROWS / 2) * SP, BIN_Y = TOP + ROWS * RH + 6;
  const heat = (m) => (m >= 20 ? "#FF2A40" : m >= 8 ? "#FF6A30" : m >= 3 ? "#F0A030" : m >= 1.5 ? "#E0D040" : m >= 1 ? "#70C060" : m >= 0.6 ? "#40A0E0" : "#5070C0");
  Object.assign(CM.UI.prototype, {
    renderFloor(box) { if (this.cgView === "plinko") return this.cgPlinko(box); return floor0.call(this, box); },
    cgPlinko(box) {
      const g = this.game, risk = this.pkRisk = this.pkRisk || "med", P = g.cgStore().pk || { drops: 0, best: 0 }, T = PK.RISK[risk];
      box.innerHTML = `<div class="cgtable plinko runestack dash"><h3>The Drop Board</h3><div class="rswrap"><canvas class="pkcanvas" width="${W}" height="${H}"></canvas>
        <div class="dashside"><p class="lore">A tall board of midnight lacquer studded with brass pegs, and at its foot a row of bins in fiery colours. The attendant hands you a chip the size of a saucer, stamped with the Joker. "Let it go from the top. Where it lands is where it lands."</p>
        <div class="row pkrisk">${Object.keys(PK.RISK).map((k) => `<button data-pkrisk="${k}" class="${k === risk ? "primary" : ""}">${NAMES[k]} risk</button>`).join("")}</div>
        <div class="pkbins">${T.map((m) => `<i style="--c:${heat(m)}">${m}×</i>`).join("")}</div>
        ${this.cgBetRow("The chip")}<div class="row"><button class="primary" data-pkdrop="1">Drop a chip</button><button data-pkdrop="5">Drop five</button></div>
        <div class="cgnote">${this.cgNote || ""}</div>${this.pkCard ? this.cgCardWon(this.pkCard) : ""}
        <div class="small">Each board returns about 96% over time; the high board swings hardest - the corners pay 120 times, the middle a fifth. Ten times or better pays tickets too, and the high board's corner a rare card the first time${P.corner ? " ✓" : ""}. Chips dropped: ${P.drops}; best ${P.best || 0}×.</div><div class="row"><button data-leave>Leave</button></div>${this.cgStats("plinko")}</div></div></div>`;
      this.cgWireBet(box); const q = (s) => box.querySelector(s); q("[data-leave]").addEventListener("click", () => { if (!(this.pkFly || []).length) this.closeDialogs(); });
      box.querySelectorAll("[data-pkrisk]").forEach((b) => b.addEventListener("click", () => { if ((this.pkFly || []).length) return; this.pkRisk = b.dataset.pkrisk; this.cgSfx("card", 0.3); this.renderCasino(); }));
      box.querySelectorAll("[data-pkdrop]").forEach((b) => b.addEventListener("click", () => { const n = Number(b.dataset.pkdrop), bet = this.cgBet === undefined ? 5 : this.cgBet; this.pkCard = null;
        for (let k = 0; k < n; k++) setTimeout(() => { const r = g.pkDrop(bet, this.pkRisk); if (r.error) { this.cgNote = r.error; this.cgSfx("miss", 0.3); if (!(this.pkFly || []).length) this.renderCasino(); return; } this.cgBusy = true; (this.pkFly = this.pkFly || []).push({ r, bet, at: performance.now(), x: W / 2 + (Math.random() - 0.5) * 6, spin: Math.random() * 6, hit: -1 }); this.cgSfx("cardplace", 0.3, 1.4);
            const gold = this.$("#casino-body .cggold"); if (gold) gold.textContent = `${g.gold} gold`; }, k * 260); }));
      this.pkCanvas = q(".pkcanvas"); this.pkGlow = this.pkGlow || {};
      if (!this.pkLoop) { const loop = (now) => { if (!this.pkCanvas || !this.pkCanvas.isConnected || this.cgView !== "plinko") { this.pkLoop = null; if (this.cgView !== "plinko") { this.pkFly = []; this.cgBusy = false; } return; } this.pkFrame(now); this.pkLoop = requestAnimationFrame(loop); }; this.pkLoop = requestAnimationFrame(loop); }
    },
    pkFrame(now) {
      const p = this.pkCanvas.getContext("2d"), T = PK.RISK[this.pkRisk || "med"], glow = this.pkGlow, per = 0.16;
      const bg = p.createLinearGradient(0, 0, 0, H); bg.addColorStop(0, "#162454"); bg.addColorStop(1, "#080E26"); p.fillStyle = bg; p.fillRect(0, 0, W, H);
      for (let k = 0; k < 30; k++) { p.fillStyle = `rgba(200,220,255,${0.15 + 0.15 * Math.sin(now / 700 + k)})`; p.fillRect((k * 71) % W, (k * 43) % (H - 120), 1.5, 1.5); }
      // the hopper
      p.fillStyle = "#3A2A10"; p.beginPath(); p.moveTo(W / 2 - 34, 10); p.lineTo(W / 2 + 34, 10); p.lineTo(W / 2 + 12, 40); p.lineTo(W / 2 - 12, 40); p.fill(); p.strokeStyle = "#F0C040"; p.stroke();
      // pegs
      for (let r = 0; r < ROWS; r++) for (let j = 0; j <= r + 2; j++) { const x = W / 2 + (j - (r + 2) / 2) * SP, y = pegY(r), k = glow[`${r}:${j}`] ? Math.max(0, 1 - (now - glow[`${r}:${j}`]) / 400) : 0;
        if (k > 0) { p.fillStyle = `rgba(255,230,140,${0.5 * k})`; p.beginPath(); p.arc(x, y, 9 * k + 4, 0, Math.PI * 2); p.fill(); } p.fillStyle = "#5A4010"; p.beginPath(); p.arc(x + 0.8, y + 1, 3.6, 0, Math.PI * 2); p.fill(); p.fillStyle = k > 0 ? "#FFF6C0" : "#F0C850"; p.beginPath(); p.arc(x, y, 3.2, 0, Math.PI * 2); p.fill(); }
      // bins
      T.forEach((m, b) => { const x = binX(b), k = glow[`bin${b}`] ? Math.max(0, 1 - (now - glow[`bin${b}`]) / 900) : 0, c = heat(m); p.fillStyle = c; p.globalAlpha = 0.55 + 0.45 * k; p.fillRect(x - SP / 2 + 2, BIN_Y, SP - 4, 34); p.globalAlpha = 1;
        if (k > 0) { p.shadowColor = c; p.shadowBlur = 20 * k; p.fillRect(x - SP / 2 + 2, BIN_Y, SP - 4, 34); p.shadowBlur = 0; } p.fillStyle = "#FFFFFF"; p.font = `bold ${m >= 100 ? 9 : 10}px Georgia`; p.textAlign = "center"; p.fillText(`${m}`, x, BIN_Y + 15); p.font = "8px Georgia"; p.fillText("×", x, BIN_Y + 27); p.textAlign = "left"; });
      // the chips falling: from the hopper to each row's peg in turn, a little hop between
      const fly = this.pkFly = this.pkFly || []; let landed = false;
      for (let i = fly.length - 1; i >= 0; i--) { const F = fly[i], t = (now - F.at) / 1000, path = F.r.path; let x, y, a = F.spin + t * 7;
        if (t < 0.25) { const k = t / 0.25; x = W / 2; y = 30 + (pegY(0) - CHIP - 30) * k * k; }
        else { const s = (t - 0.25) / per, r = Math.floor(s), f = s - r; if (r >= ROWS) { const k2 = Math.min(1, (s - ROWS) / 0.8); x = binX(F.r.bin); y = pegY(ROWS - 1) - CHIP + (BIN_Y + 14 - pegY(ROWS - 1) + CHIP) * k2;
            if (k2 >= 1) { fly.splice(i, 1); glow[`bin${F.r.bin}`] = now; (this.pkPop = this.pkPop || []).push({ x, y: BIN_Y - 8, at: now, r: F.r }); this.cgSfx(F.r.mult >= 8 ? "cardwin" : F.r.mult >= 1 ? "coin" : "card", F.r.mult >= 1 ? 0.45 : 0.2, F.r.mult >= 3 ? 1 : 1.3); landed = true; if (F.r.card) this.pkCard = F.r.card; continue; } }
          else { const k = path.slice(0, r).reduce((s2, v) => s2 + v, 0), j0 = k + 1, x0 = W / 2 + (j0 - (r + 2) / 2) * SP, k1 = k + path[r], x1 = W / 2 + (k1 + 1 - (r + 3) / 2) * SP;
            if (F.hit !== r) { F.hit = r; glow[`${r}:${j0}`] = now; this.cgSfx("card", 0.07, 1.8 + Math.random() * 0.4); }
            x = x0 + (x1 - x0) * f; y = pegY(r) - CHIP + (pegY(Math.min(ROWS - 1, r + 1)) - pegY(r)) * f - Math.sin(f * Math.PI) * 10; if (r === ROWS - 1) y = pegY(r) - CHIP + 18 * f - Math.sin(f * Math.PI) * 10; } }
        p.save(); p.translate(x, y); p.rotate(a); const gr = p.createRadialGradient(-3, -3, 1, 0, 0, CHIP); gr.addColorStop(0, "#FFF4C0"); gr.addColorStop(0.5, "#F0C040"); gr.addColorStop(1, "#8A5A10"); p.fillStyle = gr; p.beginPath(); p.arc(0, 0, CHIP, 0, Math.PI * 2); p.fill();
        p.strokeStyle = "#8A5A10"; p.setLineDash([2, 2]); p.beginPath(); p.arc(0, 0, CHIP - 2, 0, Math.PI * 2); p.stroke(); p.setLineDash([]); p.fillStyle = "#6A3A08"; p.font = "bold 9px Georgia"; p.textAlign = "center"; p.fillText("J", 0, 3); p.textAlign = "left"; p.restore(); }
      // the multiples floating up from the bins
      this.pkPop = (this.pkPop || []).filter((o) => { const k = (now - o.at) / 1400; if (k >= 1) return false; p.globalAlpha = 1 - k; p.fillStyle = o.r.mult >= 1 ? "#FFE880" : "#A0B0D0"; p.font = `bold ${o.r.mult >= 8 ? 20 : 14}px Georgia`; p.textAlign = "center"; p.fillText(`${o.r.mult}×${o.r.gold ? ` +${o.r.gold}` : ""}`, o.x, o.y - k * 50); p.textAlign = "left"; p.globalAlpha = 1; return true; });
      if (landed && !fly.length) { this.cgBusy = false; const last = this.pkPop[this.pkPop.length - 1].r; this.cgNote = last.mult >= 1 ? `${last.mult}× - ${last.gold} gold${last.tickets ? ` and ${last.tickets} tickets` : ""}!` : `${last.mult}× - ${last.gold} gold back.`; this.renderCasino(); }
    },
  });
}
