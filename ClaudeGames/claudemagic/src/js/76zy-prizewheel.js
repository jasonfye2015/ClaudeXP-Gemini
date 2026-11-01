"use strict";
// The Prize Wheel, the window's side: a cheerful painted wheel on a post by the door, its slices in bright colours with
// little pictures (tickets, coins, a potion, a card), a flapper and a bulb-lit frame; once a real day a free spin -
// a tug and it whirls, ticks and slows, then the slice wins, bursts with confetti and the prize is given. The rules
// are 64zzd-luck.js.
CM.CG_TABLES.push(["prizewheel", "The Prize Wheel"]);
{ const floor0 = CM.UI.prototype.renderFloor, PW = CM.LUCK.PW, S = 360, R0 = 150, COLS = ["#E05050", "#F0A030", "#F0D040", "#60C060", "#40A0E0", "#8060D0", "#E060B0", "#40C0B0", "#C04040", "#F08060"];
  Object.assign(CM.UI.prototype, {
    renderFloor(box) { if (this.cgView === "prizewheel") return this.cgPrizeWheel(box); return floor0.call(this, box); },
    cgPrizeWheel(box) {
      const g = this.game, ready = g.pwReady(), last = this.pwLast;
      box.innerHTML = `<div class="cgtable prizewheel runestack dash"><h3>The Prize Wheel</h3><div class="rswrap"><canvas class="pwcanvas" width="${S}" height="${S + 30}"></canvas>
        <div class="dashside"><p class="lore">By the door hangs a bright painted wheel with a sign: ONE FREE SPIN A DAY, ON THE HOUSE. The doorman winks. "Give it a good pull."</p>
        <div class="pwlist">${PW.SLICES.map(([id, label], i) => `<span style="--c:${COLS[i]}">${label}</span>`).join("")}</div>
        <div class="cgnote">${this.cgNote || ""}</div>${last && last.card ? this.cgCardWon(last.card) : ""}
        <div class="row"><button class="primary" data-pwspin ${ready && !this.cgBusy ? "" : "disabled"}>${ready ? "Spin - it's free" : "Come back tomorrow"}</button><button data-leave>Leave</button></div>
        <div class="small">One free spin each real day: tickets (5 to 100), gold, a potion or a Claudescryption card. Spins so far: ${g.cgStore().pwN || 0}.</div></div></div></div>`;
      const q = (s) => box.querySelector(s); q("[data-leave]").addEventListener("click", () => this.closeDialogs()); this.pwCanvas = q(".pwcanvas"); this.pwDraw(this.pwA || 0, performance.now());
      q("[data-pwspin]").addEventListener("click", () => {
        if (this.cgBusy) return; const r = g.pwSpin(); if (r.error) { this.cgNote = r.error; this.renderCasino(); return; } this.cgBusy = true; this.cgSfx("hinge", 0.4, 1.5);
        const n = PW.SLICES.length, step = (Math.PI * 2) / n, a0 = this.pwA || 0, target = -Math.PI / 2 - (r.i + 0.5) * step, end = a0 - Math.PI * 2 * 4 - ((((a0 - target) % (Math.PI * 2)) + Math.PI * 2) % (Math.PI * 2)), t0 = performance.now(), dur = 4200; let lp = -1;
        const frame = (now) => { const k = Math.min(1, (now - t0) / dur), e = 1 - Math.pow(1 - k, 3), a = a0 + (end - a0) * e, peg = Math.floor(-a / step); if (peg !== lp) { lp = peg; this.cgSfx("card", 0.15, 2 - k); } this.pwDraw(a, now);
          if (k < 1) { requestAnimationFrame(frame); return; } this.pwA = end % (Math.PI * 2); this.cgBusy = false; this.pwLast = r; this.pwConf = now; this.cgNote = `The wheel stops on ${r.label}${r.item ? ` - ${r.item.name}, in the party's pack` : ""}!`; this.cgSfx("cardwin", 0.5); this.renderCasino(); };
        requestAnimationFrame(frame);
      });
      if (!this.pwLoop) { const loop = (now) => { if (!this.pwCanvas || !this.pwCanvas.isConnected || this.cgView !== "prizewheel") { this.pwLoop = null; return; } if (!this.cgBusy) this.pwDraw(this.pwA || 0, now); this.pwLoop = requestAnimationFrame(loop); }; this.pwLoop = requestAnimationFrame(loop); }
    },
    pwDraw(a, now) {
      const p = this.pwCanvas.getContext("2d"), c = S / 2, cy = S / 2 + 20, n = PW.SLICES.length, step = (Math.PI * 2) / n; p.clearRect(0, 0, S, S + 30);
      p.fillStyle = "#6A4A2A"; p.fillRect(c - 8, cy, 16, S); p.fillStyle = "rgba(0,0,0,0.35)"; p.beginPath(); p.arc(c + 5, cy + 6, R0 + 10, 0, Math.PI * 2); p.fill();
      p.fillStyle = "#F8F0E0"; p.beginPath(); p.arc(c, cy, R0 + 10, 0, Math.PI * 2); p.fill();
      PW.SLICES.forEach(([id, label], i) => { const s0 = a + i * step; p.fillStyle = COLS[i]; p.beginPath(); p.moveTo(c, cy); p.arc(c, cy, R0, s0, s0 + step); p.closePath(); p.fill(); p.strokeStyle = "#FFF"; p.lineWidth = 2; p.stroke(); p.lineWidth = 1;
        p.save(); p.translate(c, cy); p.rotate(s0 + step / 2); p.translate(R0 * 0.62, 0); p.rotate(Math.PI / 2); p.fillStyle = "#FFFFFF"; p.font = "bold 11px Georgia"; p.textAlign = "center"; const [top, bot] = label.split(" "); p.fillText(top, 0, -2); p.font = "9px Georgia"; p.fillText(bot || "", 0, 9);
        if (id.startsWith("t")) { p.fillStyle = "#FFD0E8"; p.fillRect(-8, -24, 16, 9); } else if (id.startsWith("g")) { p.fillStyle = "#FFE070"; p.beginPath(); p.arc(0, -20, 6, 0, Math.PI * 2); p.fill(); } else if (id === "potion") { p.fillStyle = "#E04060"; p.beginPath(); p.arc(0, -19, 6, 0, Math.PI * 2); p.fill(); } else if (id === "card") { p.fillStyle = "#FFFFFF"; p.fillRect(-6, -28, 12, 16); }
        p.restore(); });
      for (let k = 0; k < 20; k++) { const b = (k * Math.PI * 2) / 20, on = this.cgBusy ? (Math.floor(now / 70) + k) % 2 === 0 : (Math.floor(now / 500) + k) % 2 === 0; p.fillStyle = on ? "#FFF6A0" : "#C0A060"; p.beginPath(); p.arc(c + Math.cos(b) * (R0 + 6), cy + Math.sin(b) * (R0 + 6), 3.5, 0, Math.PI * 2); p.fill(); }
      p.fillStyle = "#F0C040"; p.beginPath(); p.arc(c, cy, 18, 0, Math.PI * 2); p.fill(); p.fillStyle = "#8A5A10"; p.beginPath(); p.arc(c, cy, 7, 0, Math.PI * 2); p.fill();
      p.fillStyle = "#C02030"; p.beginPath(); p.moveTo(c - 10, cy - R0 - 22); p.lineTo(c + 10, cy - R0 - 22); p.lineTo(c, cy - R0 + 4); p.fill();
      if (this.pwConf && now - this.pwConf < 2200) { const t = (now - this.pwConf) / 1000; for (let k = 0; k < 50; k++) { const x = c + Math.sin(k * 7.3) * 160 + Math.sin(t * 3 + k) * 10, y = -10 + ((k * 37) % 60) + t * (90 + (k % 5) * 30); p.fillStyle = COLS[k % COLS.length]; p.save(); p.translate(x, y); p.rotate(t * 4 + k); p.fillRect(-3, -1.5, 6, 3); p.restore(); } }
    },
  });
}
