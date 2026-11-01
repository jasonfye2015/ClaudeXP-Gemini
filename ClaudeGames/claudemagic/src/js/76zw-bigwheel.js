"use strict";
// The Joker's Wheel, the window's side: a great upright wheel of painted slots in a gilt rim studded with lamps, a
// leather clapper at the top that ticks over each peg (the ticks slowing as the wheel slows), the Joker and the Star
// slots glittering; the betting board below - a square for each number with what it pays - chips stacking on it. A spin
// whirls it, the lamps chase, and it settles with the clapper on the winner, which lights and the board pays. The rules
// are 64zzd-luck.js.
CM.CG_TABLES.push(["bigwheel", "The Joker's Wheel"]);
{ const floor0 = CM.UI.prototype.renderFloor, BW = CM.LUCK.BW, S = 380, R0 = 170, COL = { 1: "#E8DCC0", 2: "#60A0E0", 5: "#60C070", 10: "#E07040", 20: "#B060E0", joker: "#2A1A30", star: "#F0C040" };
  const label = (k) => (k === "joker" ? "J" : k === "star" ? "★" : String(k));
  Object.assign(CM.UI.prototype, {
    renderFloor(box) { if (this.cgView === "bigwheel") return this.cgBigWheel(box); return floor0.call(this, box); },
    cgBigWheel(box) {
      const g = this.game, bets = this.bwBets = this.bwBets || {}, staked = Object.values(bets).reduce((a, b) => a + b, 0), last = this.bwLast, keys = [1, 2, 5, 10, 20, "joker", "star"];
      box.innerHTML = `<div class="cgtable bigwheel runestack dash"><h3>The Joker's Wheel</h3><div class="rswrap"><canvas class="bwcanvas" width="${S}" height="${S + 20}"></canvas>
        <div class="dashside"><p class="lore">A great painted wheel taller than a man, ringed with lamps, and a barker in a striped coat. "Round she goes! Pick a number - the higher it pays, the fewer the slots. The Joker? The Joker pays forty and a little something besides."</p>
        <div class="bwboard">${keys.map((k) => `<div class="bwspot${last && last.hit === k ? " hit" : ""}" data-bwb="${k}" style="--c:${COL[k]}"><b>${label(k)}</b><small>${BW.PAYS[k]} to 1 · ${BW.SLOTS.filter((s) => s === k).length} slot${BW.SLOTS.filter((s) => s === k).length > 1 ? "s" : ""}</small>${bets[k] ? `<i class="crchip">${bets[k]}</i>` : ""}</div>`).join("")}</div>
        ${this.cgBetRow("The chip")}<div class="cgnote">${this.cgNote || ""}</div>${last && last.card ? this.cgCardWon(last.card) : ""}
        <div class="row"><button class="primary" data-bwspin ${staked && !this.cgBusy ? "" : "disabled"}>Spin (${staked} gold)</button><button data-bwclear>Clear</button><button data-leave>Leave</button></div>
        <div class="small">Click a number to put the chip on it, then spin. Each number pays its own odds when the wheel stops on it; the wheel gives back 76% to 89% depending on the bet (the ones best). The Joker brings a rare card with its winnings.</div>${this.cgStats("bigwheel")}</div></div></div>`;
      this.cgWireBet(box); const q = (s) => box.querySelector(s); q("[data-leave]").addEventListener("click", () => this.closeDialogs());
      box.querySelectorAll("[data-bwb]").forEach((el) => el.addEventListener("click", () => { if (this.cgBusy) return; const k = isNaN(el.dataset.bwb) ? el.dataset.bwb : Number(el.dataset.bwb), c = this.cgBet || 0; if (!c) { this.cgNote = "Choose a chip first."; this.renderCasino(); return; } bets[k] = (bets[k] || 0) + c; this.bwLast = null; this.cgSfx("coin", 0.25, 1.3); this.cgNote = ""; this.renderCasino(); }));
      q("[data-bwclear]").addEventListener("click", () => { if (!this.cgBusy) { this.bwBets = {}; this.renderCasino(); } });
      const cv = this.bwCanvas = q(".bwcanvas"); this.bwDraw(this.bwA || 0, performance.now(), last ? last.i : -1);
      q("[data-bwspin]").addEventListener("click", () => {
        if (this.cgBusy) return; const r = g.bwSpin(bets); if (r.error) { this.cgNote = r.error; this.renderCasino(); return; } this.cgBusy = true; this.cgSfx("hinge", 0.4, 1.2);
        const step = (Math.PI * 2) / 54, a0 = this.bwA || 0, target = -Math.PI / 2 - (r.i + 0.5) * step, t0 = performance.now(), dur = 5200; let lastPeg = -1;
        const end = a0 - Math.PI * 2 * 5 - ((((a0 - target) % (Math.PI * 2)) + Math.PI * 2) % (Math.PI * 2));
        const frame = (now) => { const k = Math.min(1, (now - t0) / dur), e = 1 - Math.pow(1 - k, 3.2), a = a0 + (end - a0) * e, peg = Math.floor(-a / step); if (peg !== lastPeg) { lastPeg = peg; this.cgSfx("card", 0.08 + 0.12 * k, 2.2 - k * 0.9); } this.bwDraw(a, now, -1);
          if (k < 1) { requestAnimationFrame(frame); return; } this.bwA = end % (Math.PI * 2); this.cgBusy = false; this.bwLast = r; this.cgNote = `${label(r.hit) === "J" ? "The Joker" : label(r.hit) === "★" ? "The Star" : r.hit}! ${r.back ? `${r.back} gold back.` : "The house takes the board."}`; if (!r.back) this.bwBets = {};
            this.renderCasino(); const b2 = this.$("#casino-body"); if (r.back) { this.cgSfx(r.back >= r.staked * 5 ? "victory" : "coin", 0.55); this.cgCoins(b2, Math.min(30, 4 + Math.round(r.back / Math.max(1, r.staked)) * 2)); } if (r.card) this.cgSfx("cardwin", 0.6); };
        requestAnimationFrame(frame);
      });
      if (!this.bwLoop) { const loop = (now) => { if (!this.bwCanvas || !this.bwCanvas.isConnected || this.cgView !== "bigwheel") { this.bwLoop = null; return; } if (!this.cgBusy) this.bwDraw(this.bwA || 0, now, this.bwLast ? this.bwLast.i : -1); this.bwLoop = requestAnimationFrame(loop); }; this.bwLoop = requestAnimationFrame(loop); }
    },
    bwDraw(a, now, lit) {
      const p = this.bwCanvas.getContext("2d"), c = S / 2, cy = S / 2 + 14, step = (Math.PI * 2) / 54; p.clearRect(0, 0, S, S + 20);
      p.fillStyle = "rgba(0,0,0,0.4)"; p.beginPath(); p.arc(c + 6, cy + 8, R0 + 14, 0, Math.PI * 2); p.fill();
      const rim = p.createRadialGradient(c - 40, cy - 40, 20, c, cy, R0 + 14); rim.addColorStop(0, "#F8D870"); rim.addColorStop(1, "#8A6420"); p.fillStyle = rim; p.beginPath(); p.arc(c, cy, R0 + 14, 0, Math.PI * 2); p.fill();
      BW.SLOTS.forEach((k, i) => { const s0 = a + i * step; p.fillStyle = COL[k]; p.beginPath(); p.moveTo(c, cy); p.arc(c, cy, R0, s0, s0 + step); p.closePath(); p.fill(); p.strokeStyle = "rgba(60,40,10,0.6)"; p.stroke();
        if (i === lit && Math.floor(now / 200) % 2) { p.fillStyle = "rgba(255,255,255,0.45)"; p.beginPath(); p.moveTo(c, cy); p.arc(c, cy, R0, s0, s0 + step); p.closePath(); p.fill(); }
        p.save(); p.translate(c, cy); p.rotate(s0 + step / 2); p.fillStyle = k === "joker" ? "#F0C040" : k === "star" ? "#3A2A08" : k === 1 ? "#3A2A10" : "#FFFFFF"; p.font = `bold ${k === "joker" || k === "star" ? 14 : 12}px Georgia`; p.textAlign = "center"; p.translate(R0 - 16, 0); p.rotate(Math.PI / 2); p.fillText(label(k), 0, 4); p.restore();
        p.fillStyle = "#E0E0E8"; p.beginPath(); p.arc(c + Math.cos(s0) * (R0 + 4), cy + Math.sin(s0) * (R0 + 4), 2.5, 0, Math.PI * 2); p.fill(); });
      for (let k = 0; k < 24; k++) { const b = (k * Math.PI * 2) / 24, on = this.cgBusy ? (Math.floor(now / 60) + k) % 3 === 0 : (Math.floor(now / 400) + k) % 2 === 0; p.fillStyle = on ? "#FFF6C0" : "#8A6A30"; p.beginPath(); p.arc(c + Math.cos(b) * (R0 + 10), cy + Math.sin(b) * (R0 + 10), 3, 0, Math.PI * 2); p.fill(); }
      const hub = p.createRadialGradient(c - 8, cy - 8, 2, c, cy, 40); hub.addColorStop(0, "#5A2A6A"); hub.addColorStop(1, "#2A0A30"); p.fillStyle = hub; p.beginPath(); p.arc(c, cy, 40, 0, Math.PI * 2); p.fill(); p.strokeStyle = "#F0C040"; p.lineWidth = 3; p.stroke(); p.lineWidth = 1; p.fillStyle = "#FFE070"; p.font = "bold 26px Georgia"; p.textAlign = "center"; p.fillText("J", c, cy + 9); p.textAlign = "left";
      // the clapper
      p.save(); p.translate(c, cy - R0 - 16); p.rotate(this.cgBusy ? Math.sin(now / 30) * 0.25 : 0); p.fillStyle = "#6A3A1A"; p.beginPath(); p.moveTo(-8, -6); p.lineTo(8, -6); p.lineTo(0, 22); p.fill(); p.fillStyle = "#C8962A"; p.beginPath(); p.arc(0, -6, 5, 0, Math.PI * 2); p.fill(); p.restore();
    },
  });
}
