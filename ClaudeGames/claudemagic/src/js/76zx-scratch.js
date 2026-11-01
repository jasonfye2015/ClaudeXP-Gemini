"use strict";
// Fortune Slips, the window's side: a slip of card printed in copper, silver or gold - a border of little suns, the
// house's name, nine squares under a grey scratch-off foil with a sheen on it. Scratch with the mouse held down (the
// foil comes away in flakes where the coin goes, with a rasp); a square nearly cleared lifts the rest of its foil, and
// once three alike show they glow and the slip pays. "Scratch it all" clears the rest at once. The rules are 64zzd-luck.js.
CM.CG_TABLES.push(["scratch", "Fortune Slips"]);
{ const floor0 = CM.UI.prototype.renderFloor, SC = CM.LUCK.SC, W = 360, H = 400, GX = 45, GY = 110, CS = 90, TINT = { copper: ["#C87A40", "#7A3A18"], silver: ["#D8E0E8", "#6A7480"], gold: ["#F0C850", "#8A6010"] };
  const label = (v) => (v === "card" ? "🂠" : `${v}`);
  Object.assign(CM.UI.prototype, {
    renderFloor(box) { if (this.cgView === "scratch") return this.cgScratch(box); return floor0.call(this, box); },
    cgScratch(box) {
      const g = this.game, P = g.cgStore().slip;
      box.innerHTML = `<div class="cgtable scratch runestack dash"><h3>Fortune Slips</h3><div class="rswrap"><div class="scwrap"><canvas class="scbase" width="${W}" height="${H}"></canvas><canvas class="scfoil" width="${W}" height="${H}"></canvas></div>
        <div class="dashside"><p class="lore">A little booth with a brass grille, and a girl selling slips from three drawers - copper, silver, gold. "Scratch the foil," she says, sliding a coin across. "Three alike wins it. Three cards... well. That's lucky."</p>
        <div class="row scbuy">${Object.entries(SC.KINDS).map(([k, K]) => `<button data-scbuy="${k}" class="sc-${k}">${k[0].toUpperCase() + k.slice(1)} slip - ${K.price} gold</button>`).join("")}</div>
        <div class="cgnote">${this.cgNote || ""}</div>${this.scCard ? this.cgCardWon(this.scCard) : ""}
        <div class="row">${P && !P.paid ? `<button class="primary" data-scall>Scratch it all</button>` : ""}<button data-leave>Leave</button></div>
        <div class="small">Buy a slip and scratch the foil with the mouse held down. Three of the same amount wins that much gold; three cards win a Claudescryption card (a better one on the dearer slips). The top prize is a hundred times the slip. The slips give back about 73% in gold, with tickets for every purchase.</div>${this.cgStats("scratch")}</div></div></div>`;
      const q = (s) => box.querySelector(s); q("[data-leave]").addEventListener("click", () => this.closeDialogs());
      box.querySelectorAll("[data-scbuy]").forEach((b) => b.addEventListener("click", () => { const Pp = g.cgStore().slip; if (Pp && !Pp.paid) { this.cgNote = "Finish scratching this slip first."; this.renderCasino(); return; } const r = g.scBuy(b.dataset.scbuy); if (r.error) { this.cgNote = r.error; this.renderCasino(); return; } this.scCard = null; this.scFresh = true; this.cgNote = "Scratch away!"; this.cgSfx("card", 0.4); this.renderCasino(); }));
      if (q("[data-scall]")) q("[data-scall]").addEventListener("click", () => { const f = this.scFoil.getContext("2d"); f.clearRect(0, 0, W, H); this.scDone(); });
      const base = q(".scbase"), foil = this.scFoil = q(".scfoil"); this.scDrawBase(base, P);
      if (P && !P.paid) { if (this.scFresh || !this.scFoilImg) { this.scDrawFoil(foil, P); this.scFresh = false; } else foil.getContext("2d").putImageData(this.scFoilImg, 0, 0); }
      const pos = (e) => { const r = foil.getBoundingClientRect(); return [((e.clientX - r.left) / r.width) * W, ((e.clientY - r.top) / r.height) * H]; };
      let down = false, lastSnd = 0; foil.addEventListener("mousedown", (e) => { down = true; this.scScratch(pos(e)); }); foil.addEventListener("mouseup", () => { down = false; }); foil.addEventListener("mouseleave", () => { down = false; });
      foil.addEventListener("mousemove", (e) => { if (!down || !P || P.paid) return; this.scScratch(pos(e)); const n = performance.now(); if (n - lastSnd > 90) { lastSnd = n; this.cgSfx("step", 0.06, 2.4 + Math.random() * 0.3); } });
    },
    scScratch([x, y]) { const f = this.scFoil.getContext("2d"); f.globalCompositeOperation = "destination-out"; f.beginPath(); f.arc(x, y, 13, 0, Math.PI * 2); f.fill(); for (let k = 0; k < 3; k++) { f.beginPath(); f.arc(x + (Math.random() - 0.5) * 26, y + (Math.random() - 0.5) * 26, 3, 0, Math.PI * 2); f.fill(); } f.globalCompositeOperation = "source-over"; this.scFoilImg = f.getImageData(0, 0, W, H); this.scCheck(); },
    // how much of each square is showing; a square mostly cleared drops the rest of its foil
    scCheck() {
      const f = this.scFoil.getContext("2d"), d = this.scFoilImg.data; let open = 0;
      for (let i = 0; i < 9; i++) { const x0 = GX + (i % 3) * CS, y0 = GY + Math.floor(i / 3) * CS; let clear = 0, tot = 0; for (let y = y0 + 6; y < y0 + CS - 6; y += 6) for (let x = x0 + 6; x < x0 + CS - 6; x += 6) { tot++; if (d[(y * W + x) * 4 + 3] < 40) clear++; }
        if (clear / tot > 0.55) { if (clear / tot < 0.99) { f.clearRect(x0 + 2, y0 + 2, CS - 4, CS - 4); this.scFoilImg = f.getImageData(0, 0, W, H); } open++; } }
      if (open === 9) this.scDone();
    },
    scDone() { const g = this.game, P = g.cgStore().slip; if (!P || P.paid) return; const r = g.scClaim(); this.scFoilImg = null; this.scCard = r.card; this.cgNote = r.prize ? `Three ${r.prize}s - ${r.prize} gold!` : r.card ? `Three cards - ${r.card}!` : "Not this time."; this.cgSfx(r.prize || r.card ? "cardwin" : "miss", 0.5); if (r.prize) this.cgCoins(this.$("#casino-body"), Math.min(30, 4 + Math.round(r.prize / 10))); this.scWinAt = performance.now(); this.renderCasino(); },
    scDrawBase(cv, P) {
      const p = cv.getContext("2d"), kind = P ? P.kind : "copper", [c1, c2] = TINT[kind]; const bg = p.createLinearGradient(0, 0, W, H); bg.addColorStop(0, c1); bg.addColorStop(1, c2); p.fillStyle = bg; p.fillRect(0, 0, W, H);
      p.fillStyle = "rgba(255,255,255,0.18)"; for (let k = 0; k < 28; k++) { const x = (k * 37) % W, y = k < 14 ? 8 : H - 8; p.beginPath(); p.arc(x + 10, y, 4, 0, Math.PI * 2); p.fill(); }
      p.fillStyle = "#2A1408"; p.font = "bold 26px Georgia"; p.textAlign = "center"; p.fillText("FORTUNE SLIP", W / 2, 48); p.font = "italic 13px Georgia"; p.fillText(`The Gilded Joker · ${kind} · ${SC.KINDS[kind].price} gold`, W / 2, 70); p.font = "12px Georgia"; p.fillText("Match three to win", W / 2, 92);
      p.fillStyle = "#FBF4E0"; p.fillRect(GX - 4, GY - 4, CS * 3 + 8, CS * 3 + 8);
      if (P) { const win = P.prize || (P.card ? "card" : null); P.syms.forEach((v, i) => { const x = GX + (i % 3) * CS, y = GY + Math.floor(i / 3) * CS, hit = win !== null && v === win && P.paid; p.fillStyle = hit ? "#FFF0A0" : (i % 2 ? "#F4ECD4" : "#FBF4E0"); p.fillRect(x + 2, y + 2, CS - 4, CS - 4);
        p.fillStyle = v === "card" ? "#8040B0" : "#3A2408"; p.font = `bold ${v === "card" ? 40 : String(v).length > 3 ? 26 : 32}px Georgia`; p.textAlign = "center"; p.fillText(label(v), x + CS / 2, y + CS / 2 + 12); if (v !== "card") { p.font = "10px Georgia"; p.fillText("GOLD", x + CS / 2, y + CS - 12); } if (hit) { p.strokeStyle = "#E0A020"; p.lineWidth = 3; p.strokeRect(x + 4, y + 4, CS - 8, CS - 8); p.lineWidth = 1; } }); }
      else { p.fillStyle = "#3A2408"; p.font = "16px Georgia"; p.textAlign = "center"; p.fillText("Buy a slip to play", W / 2, GY + CS * 1.5); }
      p.textAlign = "left";
    },
    scDrawFoil(cv, P) { const f = cv.getContext("2d"); f.clearRect(0, 0, W, H); for (let i = 0; i < 9; i++) { const x = GX + (i % 3) * CS, y = GY + Math.floor(i / 3) * CS, gr = f.createLinearGradient(x, y, x + CS, y + CS); gr.addColorStop(0, "#B8BCC8"); gr.addColorStop(0.5, "#E8ECF4"); gr.addColorStop(1, "#9098A8"); f.fillStyle = gr; f.fillRect(x + 2, y + 2, CS - 4, CS - 4); f.fillStyle = "rgba(80,80,100,0.35)"; f.font = "bold 22px Georgia"; f.textAlign = "center"; f.fillText("★", x + CS / 2, y + CS / 2 + 8); } f.textAlign = "left"; this.scFoilImg = f.getImageData(0, 0, W, H); void P; },
  });
}
