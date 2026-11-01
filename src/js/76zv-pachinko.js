"use strict";
// The Pin Garden, the window's side: a tall pachinko cabinet - chrome frame, a garden painted behind the glass (a moon,
// cherry blossom, a pagoda-ish lantern house), brass pins, the two windmill cups that spin when a ball drops in, the
// start pockets and the tulip that opens its petals, the three drums in a little screen that spin and stop one by one
// (Fever: the whole cabinet flashes and the tray fills); steel balls rolling round the rail and pattering down with a
// little spin of light; the handle dial at the bottom right. Set the handle (the slider, or the mouse wheel over it),
// hold Shoot to fire a stream. The rules are 64zzd-luck.js.
CM.CG_TABLES.push(["pachinko", "The Pin Garden"]);
{ const floor0 = CM.UI.prototype.renderFloor, PC = CM.LUCK.PC, W = PC.W, H = PC.H;
  Object.assign(CM.UI.prototype, {
    renderFloor(box) { if (this.cgView === "pachinko") return this.cgPachinko(box); return floor0.call(this, box); },
    cgPachinko(box) {
      const g = this.game, S = g.pcState(); this.pcPower = this.pcPower === undefined ? 0.6 : this.pcPower;
      box.innerHTML = `<div class="cgtable pachinko runestack dash"><h3>The Pin Garden</h3><div class="rswrap"><div class="pccab"><canvas class="pccanvas" width="${W}" height="${H}"></canvas><div class="pctray"><span class="pcballs">${S.balls}</span> balls</div></div>
        <div class="dashside"><p class="lore">A row of tall glass cabinets humming against the wall, each a little garden of brass pins. "Buy a tray, turn the handle, let them fall," says the attendant. "What lands in the cups comes back to you. The tulip... the tulip is where fortunes start."</p>
        ${this.cgBetRow("Balls to buy (a gold each)")}<div class="row"><button data-pcbuy>Buy balls</button><button data-pcex ${S.balls ? "" : "disabled"}>Exchange ${S.balls} balls</button></div>
        <div class="pchandle"><label>The handle <input type="range" min="0" max="100" value="${Math.round(this.pcPower * 100)}" data-pcpow></label><button class="primary pcshoot" data-pcshoot ${S.balls ? "" : "disabled"}>Hold to shoot</button></div>
        <div class="cgnote">${this.cgNote || ""}</div>${this.pcCard ? this.cgCardWon(this.pcCard) : ""}
        <div class="small">Buy balls at a gold apiece, set the handle and hold Shoot. Start pockets give 3 balls back, the windmill cups 6, the tulip 4 and a spin of the drums - three alike is Fever: 60 balls and a card. Exchange balls held at any time: 85 gold for every hundred, and a ticket for every ten. The handle matters - find where the balls fall kindly. Fevers here: ${S.fevers}.</div><div class="row"><button data-leave>Leave</button></div>${this.cgStats("pachinko")}</div></div></div>`;
      this.cgWireBet(box); const q = (s) => box.querySelector(s); q("[data-leave]").addEventListener("click", () => this.closeDialogs());
      q("[data-pcbuy]").addEventListener("click", () => { const why = g.pcBuy(this.cgBet === undefined ? 5 : this.cgBet); this.cgNote = why || "The balls clatter into the tray."; this.cgSfx(why ? "miss" : "chain", 0.4, 1.3); this.renderCasino(); });
      q("[data-pcex]").addEventListener("click", () => { const r = g.pcExchange(); this.cgNote = `${r.balls} balls exchanged: ${r.gold} gold and ${r.tickets} tickets.`; this.cgSfx("coin", 0.5); this.cgCoins(this.$("#casino-body"), 10); this.renderCasino(); });
      const pw = q("[data-pcpow]"); pw.addEventListener("input", () => { this.pcPower = pw.value / 100; });
      const sb = q("[data-pcshoot]"), hold = (v) => { this.pcHold = v; }; sb.addEventListener("mousedown", () => hold(true)); sb.addEventListener("mouseup", () => hold(false)); sb.addEventListener("mouseleave", () => hold(false));
      this.pcCanvas = q(".pccanvas"); this.pcCanvas.addEventListener("wheel", (e) => { e.preventDefault(); this.pcPower = CM.ARC.clamp(this.pcPower - Math.sign(e.deltaY) * 0.02, 0, 1); pw.value = Math.round(this.pcPower * 100); });
      if (!this.pcLoop) { let prev = performance.now(), fireT = 0; const loop = (now) => { if (!this.pcCanvas || !this.pcCanvas.isConnected || this.cgView !== "pachinko") { this.pcLoop = null; this.pcHold = false; return; } const dt = Math.min(0.05, (now - prev) / 1000); prev = now;
          fireT -= dt; if (this.pcHold && fireT <= 0) { fireT = 0.28; const r = g.pcShoot(this.pcPower); if (r.error) this.pcHold = false; else { (this.pcFly = this.pcFly || []).push({ r, at: now }); this.cgSfx("card", 0.12, 2); } }
          this.pcFrame(dt, now); this.pcLoop = requestAnimationFrame(loop); }; this.pcLoop = requestAnimationFrame(loop); }
    },
    pcLand(r, now) {
      const g = this.game, fx = this.pcFx = this.pcFx || { mills: [0, 0], tulip: 0, drums: null, flash: 0 };
      if (r.pocket === "mill") { fx.mills[r.path[r.path.length - 1][0] < W / 2 ? 0 : 1] = now; this.cgSfx("coin", 0.35, 1.6); }
      else if (r.pocket === "start") this.cgSfx("coin", 0.25, 1.3); else if (r.pocket === "tulip") { fx.tulip = now; fx.drums = { at: now, d: r.drums, fever: r.fever }; this.cgSfx("spell", 0.35, 1.4); } else this.cgSfx("step", 0.05, 2.2);
      if (r.fever) { setTimeout(() => { fx.flash = performance.now(); this.cgSfx("victory", 0.6); this.cgSfx("cardwin", 0.5); this.pcCard = r.card; this.cgNote = "FEVER! Sixty balls pour into the tray."; this.renderCasino(); }, 1500); }
      const t = this.$("#casino-body .pcballs"); if (t) t.textContent = g.pcState().balls; const ex = this.$("#casino-body [data-pcex]"); if (ex) { ex.disabled = !g.pcState().balls; ex.textContent = `Exchange ${g.pcState().balls} balls`; }
    },
    pcFrame(dt, now) {
      const p = this.pcCanvas.getContext("2d"), fx = this.pcFx = this.pcFx || { mills: [0, 0], tulip: 0, drums: null, flash: 0 };
      // the garden behind the glass
      const bg = p.createLinearGradient(0, 0, 0, H); bg.addColorStop(0, "#1A1440"); bg.addColorStop(0.6, "#3A2050"); bg.addColorStop(1, "#5A2A3A"); p.fillStyle = bg; p.fillRect(0, 0, W, H);
      p.fillStyle = "#F8F0D0"; p.beginPath(); p.arc(W - 60, 70, 22, 0, Math.PI * 2); p.fill(); p.fillStyle = "rgba(248,240,208,0.08)"; p.beginPath(); p.arc(W - 60, 70, 40, 0, Math.PI * 2); p.fill();
      p.strokeStyle = "#3A2018"; p.lineWidth = 4; p.beginPath(); p.moveTo(0, 150); p.quadraticCurveTo(60, 120, 110, 140); p.stroke(); p.lineWidth = 1; for (let k = 0; k < 14; k++) { const x = 10 + k * 8, y = 132 + Math.sin(k) * 10; p.fillStyle = `rgba(255,${170 + k * 4},${200},0.8)`; p.beginPath(); p.arc(x, y, 4, 0, Math.PI * 2); p.fill(); }
      for (let k = 0; k < 8; k++) { const t = ((now / 7000 + k / 8) % 1), x = (k * 53 + t * 40) % W, y = t * H; p.fillStyle = "rgba(255,200,220,0.6)"; p.beginPath(); p.ellipse(x, y, 2.5, 1.5, t * 6, 0, Math.PI * 2); p.fill(); }
      // the rail
      p.strokeStyle = "#B0B8C8"; p.lineWidth = 3; p.beginPath(); p.arc(W / 2, W / 2 + 10, W / 2 - 6, Math.PI, 0); p.stroke(); p.lineWidth = 1;
      // pins
      for (const [x, y] of PC.PINS) { p.fillStyle = "#806020"; p.beginPath(); p.arc(x + 0.6, y + 0.8, PC.pinR, 0, Math.PI * 2); p.fill(); p.fillStyle = "#F0D070"; p.beginPath(); p.arc(x, y, PC.pinR - 0.6, 0, Math.PI * 2); p.fill(); }
      // windmills
      for (const [i, P] of PC.POCKETS.filter((q) => q.id === "mill").entries()) { const spin = now - fx.mills[i] < 1200 ? (now - fx.mills[i]) / 60 : now / 900; p.save(); p.translate(P.x, P.y - 14); p.rotate(spin); p.fillStyle = "#E0E0F0"; for (let k = 0; k < 4; k++) { p.rotate(Math.PI / 2); p.fillRect(-2, 0, 4, 12); } p.restore(); p.fillStyle = "#3A2A20"; p.fillRect(P.x - 8, P.y - 2, 16, 8); p.fillStyle = "#F0C040"; p.fillRect(P.x - P.w / 2, P.y - 2, P.w, 3); }
      // starts and tulip
      for (const P of PC.POCKETS.filter((q) => q.id === "start")) { p.fillStyle = "#C03040"; p.beginPath(); p.moveTo(P.x - 12, P.y - 6); p.lineTo(P.x + 12, P.y - 6); p.lineTo(P.x + 6, P.y + 6); p.lineTo(P.x - 6, P.y + 6); p.fill(); p.fillStyle = "#101010"; p.fillRect(P.x - P.w / 2, P.y - 4, P.w, 4); }
      { const T = PC.POCKETS.find((q) => q.id === "tulip"), open = now - fx.tulip < 1400 ? 1 : 0.15; p.fillStyle = "#E05090"; for (const s of [-1, 1]) { p.save(); p.translate(T.x + s * 5, T.y - 2); p.rotate(s * (0.3 + open * 0.6)); p.beginPath(); p.ellipse(s * 4, -8, 5, 10, 0, 0, Math.PI * 2); p.fill(); p.restore(); } p.fillStyle = "#101010"; p.fillRect(T.x - T.w / 2, T.y - 2, T.w, 4); }
      // the drums
      const Dd = fx.drums, dx = W / 2 - 45, dy = 300; p.fillStyle = "#0A0A12"; p.fillRect(dx - 4, dy - 4, 98, 40); p.strokeStyle = "#F0C040"; p.strokeRect(dx - 4, dy - 4, 98, 40);
      for (let k = 0; k < 3; k++) { const stop = Dd ? Dd.at + 400 + k * 350 : 0, spinning = Dd && now < stop, v = Dd ? (spinning ? 1 + Math.floor(now / 50 + k * 3) % 9 : Dd.d[k]) : 7; p.fillStyle = "#1A1A2A"; p.fillRect(dx + k * 31, dy, 27, 32); p.fillStyle = Dd && Dd.fever && !spinning ? "#FFE070" : "#F0F0F0"; p.font = "bold 22px Georgia"; p.textAlign = "center"; p.fillText(String(v), dx + k * 31 + 13.5, dy + 24 + (spinning ? (now / 6) % 10 - 5 : 0)); p.textAlign = "left"; }
      // balls
      this.pcFly = (this.pcFly || []).filter((b) => { const i = Math.floor((now - b.at) / (1000 / 60)), path = b.r.path; if (i >= path.length) { this.pcLand(b.r, now); return false; } const [x, y] = path[i]; const gr = p.createRadialGradient(x - 1.5, y - 1.5, 0.5, x, y, PC.ballR); gr.addColorStop(0, "#FFFFFF"); gr.addColorStop(1, "#7080A0"); p.fillStyle = gr; p.beginPath(); p.arc(x, y, PC.ballR, 0, Math.PI * 2); p.fill(); return true; });
      // the glass and the fever flash
      const gl = p.createLinearGradient(0, 0, W, H); gl.addColorStop(0, "rgba(255,255,255,0.1)"); gl.addColorStop(0.4, "rgba(255,255,255,0)"); p.fillStyle = gl; p.fillRect(0, 0, W, H);
      if (now - fx.flash < 2000) { const k = (now - fx.flash) / 2000; p.fillStyle = `rgba(255,${200 + Math.sin(now / 50) * 50},80,${0.4 * (1 - k)})`; p.fillRect(0, 0, W, H); p.fillStyle = `rgba(255,240,150,${1 - k})`; p.font = "bold 40px Georgia"; p.textAlign = "center"; p.fillText("FEVER!", W / 2, 260); p.textAlign = "left"; }
      // the handle
      const a = -2.4 + this.pcPower * 1.8; p.fillStyle = "#3A3A40"; p.beginPath(); p.arc(W - 30, H - 30, 20, 0, Math.PI * 2); p.fill(); p.strokeStyle = "#E0E0E8"; p.lineWidth = 4; p.beginPath(); p.moveTo(W - 30, H - 30); p.lineTo(W - 30 + Math.cos(a) * 16, H - 30 + Math.sin(a) * 16); p.stroke(); p.lineWidth = 1;
    },
  });
}
