"use strict";
// The Town Lottery, the window's side: the crier's booth on the square - the jackpot in lit brass digits over a
// striped awning, and the draw machine, a glass drum of thirty painted balls tumbling on the stir of air; when a draw is
// due the drum spins up, and one by one six balls ride the chute into the tray while the party's slips light each match.
// A slip is picked on a card of thirty numbers (or quick-picked); the slips for tonight are listed, with a countdown to
// eight o'clock; the board by the booth keeps the last nights' balls and who in the village won the pot. The rules are
// 64zzj-draws.js.
CM.CG_TABLES.push(["lottery", "The Town Lottery"]);
{ const floor0 = CM.UI.prototype.renderFloor, LOT = CM.LOT, W = 300, H = 330, DR = 104, DX = 150, DY = 128;
  const col = (n) => (n <= 10 ? ["#F0C840", "#8A6A10"] : n <= 20 ? ["#4A90E0", "#1A4A90"] : ["#E05090", "#8A1A50"]);
  const when = (ms) => { if (ms <= 0) return "now"; const m = Math.ceil(ms / 60000), h = Math.floor(m / 60); return h ? `${h}h ${m % 60}m` : `${m}m`; };
  const nice = (key) => { const [y, m, d] = key.split("-").map(Number); return new Date(y, m - 1, d).toLocaleDateString("en-GB", { weekday: "short", day: "numeric", month: "short" }); };
  const ball = (p, x, y, r, n, glow) => { const [a, b] = col(n), g = p.createRadialGradient(x - r * 0.35, y - r * 0.35, r * 0.1, x, y, r); g.addColorStop(0, "#FFFFFF"); g.addColorStop(0.25, a); g.addColorStop(1, b); if (glow) { p.shadowColor = "#FFF0A0"; p.shadowBlur = 16; }
    p.fillStyle = g; p.beginPath(); p.arc(x, y, r, 0, Math.PI * 2); p.fill(); p.shadowBlur = 0; p.fillStyle = "#FFFFFF"; p.beginPath(); p.arc(x, y, r * 0.55, 0, Math.PI * 2); p.fill(); p.fillStyle = "#1A1A2A"; p.font = `bold ${Math.round(r * 0.75)}px Georgia`; p.textAlign = "center"; p.fillText(String(n), x, y + r * 0.27); p.textAlign = "left"; };
  Object.assign(CM.UI.prototype, {
    renderFloor(box) { if (this.cgView === "lottery") return this.cgLottery(box); return floor0.call(this, box); },
    cgLottery(box) {
      const g = this.game, D = this.ltDraw, S = g.lotStore(), now = Date.now(), key = LOT.drawKey(now), pot = g.lotPotTo(key), mine = S.slips.filter((s) => s.key === (D ? D.key : key)), due = g.lotDue(now), pick = this.ltPick = this.ltPick || [], last = this.ltLast;
      const slipHtml = (s, balls) => `<div class="ltslip">${s.nums.map((n) => `<i class="${balls && balls.includes(n) ? "hit" : ""}" style="--c:${col(n)[0]}">${n}</i>`).join("")}${s.m !== undefined ? `<b>${s.m} matched${s.gold ? ` - ${s.gold.toLocaleString("en")} gold` : ""}</b>` : ""}</div>`;
      box.innerHTML = `<div class="cgtable lottery runestack dash"><h3>The Town Lottery</h3><div class="ltpot"><span>THE TOWN JACKPOT</span><b>${pot.toLocaleString("en")}</b><span>gold</span></div><div class="rswrap"><canvas class="ltcanvas" width="${W}" height="${H}"></canvas>
        <div class="dashside"><p class="lore">On the square, under a striped awning, the crier keeps the town's lottery - a glass drum of thirty painted balls and a slate of the jackpot in brass. "Six numbers, two gold a slip! Drawn at eight o'clock tonight! Three numbers and you're paid, all six and the pot's yours!"</p>
        ${D ? `<div class="cgnote">The drum is turning...</div>` : due.length ? `<div class="row"><button class="primary ltwatch" data-ltwatch="${due[0]}">Watch the draw - ${nice(due[0])}</button></div>` : ""}
        <h4>Pick a slip <span class="small">(${pick.length} of ${LOT.pick})</span></h4><div class="ltcard">${Array.from({ length: LOT.of }, (_, i) => `<button data-ltn="${i + 1}" class="${pick.includes(i + 1) ? "on" : ""}" style="--c:${col(i + 1)[0]}">${i + 1}</button>`).join("")}</div>
        <div class="row"><button class="primary" data-ltbuy ${pick.length === LOT.pick && !D ? "" : "disabled"}>Buy this slip (${LOT.price} gold)</button><button data-ltquick="1" ${D ? "disabled" : ""}>Quick pick</button><button data-ltquick="5" ${D ? "disabled" : ""}>5 quick picks</button><button data-ltclear>Clear</button></div>
        <div class="cgnote">${D ? "" : this.cgNote || ""}</div>${last ? `<div class="ltresult">${last.slips.map((s) => slipHtml(s, last.balls)).join("")}<div>${last.gold ? `<b>${last.gold.toLocaleString("en")} gold</b>` : "No prize this time"}${last.tickets ? ` and ${last.tickets} tickets` : ""}.</div>${last.cards.map((c) => this.cgCardWon(c)).join("")}</div>` : ""}
        <h4>Your slips for ${nice(D ? D.key : key)} <span class="small">${D ? "- being drawn" : `- drawn in ${when(LOT.drawTime(key) - now)}`}</span></h4><div class="ltslips">${mine.length ? mine.map((s) => slipHtml(s)).join("") : `<span class="small">None yet.</span>`}</div>
        <table class="paytable"><tr><th>Matched</th><th>Pays</th></tr>${[3, 4, 5].map((m) => `<tr><td>${m}</td><td>${LOT.PAYS[m][0].toLocaleString("en")} gold, ${LOT.PAYS[m][1]} tickets${m === 5 ? ", a rare card" : ""}</td></tr>`).join("")}<tr><td>6</td><td>The jackpot, ${LOT.jackTickets} tickets, a rare card</td></tr></table>
        <div class="ltnews"><h4>The crier's board</h4>${Object.entries(S.seen).sort((a, b) => (a[0] < b[0] ? 1 : -1)).slice(0, 4).map(([k, v]) => `<div>${nice(k)}: ${v.balls.slice().sort((a, b) => a - b).map((n) => `<i style="--c:${col(n)[0]}">${n}</i>`).join("")}</div>`).join("") || `<div class="small">No draws watched yet.</div>`}
        ${S.news.slice(0, 3).map((e) => `<div class="small">${nice(e.key)}: <b>${e.who}</b> won the jackpot - ${e.pot.toLocaleString("en")} gold!</div>`).join("")}</div>
        <div class="small">Up to ${LOT.max} slips a draw. A slip bought after eight o'clock is in the next night's draw. The jackpot grows every night nobody wins it. Your best: ${S.best} matched; won in all ${S.won.toLocaleString("en")} gold.</div><div class="row"><button data-leave>Leave</button></div>${this.cgStats("lottery")}</div></div></div>`;
      const q = (s) => box.querySelector(s); q("[data-leave]").addEventListener("click", () => this.closeDialogs());
      box.querySelectorAll("[data-ltn]").forEach((b) => b.addEventListener("click", () => { const n = Number(b.dataset.ltn), i = pick.indexOf(n); if (i >= 0) pick.splice(i, 1); else if (pick.length < LOT.pick) pick.push(n); this.cgSfx("card", 0.2, 1.6); this.renderCasino(); }));
      q("[data-ltclear]").addEventListener("click", () => { this.ltPick = []; this.renderCasino(); });
      q("[data-ltbuy]").addEventListener("click", () => { const r = g.lotBuy(pick.slice()); if (r.error) { this.cgNote = r.error; this.cgSfx("miss", 0.3); } else { this.ltPick = []; this.ltLast = null; this.cgNote = `A slip for ${nice(r.key)}: ${r.nums.join(", ")}. Good luck!`; this.cgSfx("cardplace", 0.4); } this.renderCasino(); });
      box.querySelectorAll("[data-ltquick]").forEach((b) => b.addEventListener("click", () => { let k = 0, err = ""; for (let i = 0; i < Number(b.dataset.ltquick); i++) { const r = g.lotBuy(); if (r.error) { err = r.error; break; } k += 1; } this.ltLast = null; this.cgNote = err && !k ? err : `${k} quick pick${k > 1 ? "s" : ""} for ${nice(key)}.${err ? ` ${err}` : ""}`; this.cgSfx(k ? "cardplace" : "miss", 0.4); this.renderCasino(); }));
      if (q("[data-ltwatch]")) q("[data-ltwatch]").addEventListener("click", () => { const k = q("[data-ltwatch]").dataset.ltwatch; this.ltDraw = { key: k, balls: g.lotBalls(k), at: performance.now() }; this.ltLast = null; this.cgBusy = true; this.cgSfx("hinge", 0.4, 0.8); this.renderCasino(); });
      this.ltCanvas = q(".ltcanvas"); if (!this.ltBalls) { this.ltBalls = Array.from({ length: LOT.of }, (_, i) => { const a = Math.random() * Math.PI * 2, r = Math.random() * (DR - 16); return { n: i + 1, x: DX + Math.cos(a) * r, y: DY + Math.sin(a) * r, vx: 0, vy: 0 }; }); }
      if (!this.ltLoop) { let prev = performance.now(); const loop = (now2) => { if (!this.ltCanvas || !this.ltCanvas.isConnected || this.cgView !== "lottery") { this.ltLoop = null; return; } const dt = Math.min(0.04, (now2 - prev) / 1000); prev = now2; this.ltFrame(dt, now2); this.ltLoop = requestAnimationFrame(loop); }; this.ltLoop = requestAnimationFrame(loop); }
    },
    ltFrame(dt, now) {
      const p = this.ltCanvas.getContext("2d"), D = this.ltDraw, step = 1.3, t = D ? (now - D.at) / 1000 : 0, out = D ? Math.max(0, Math.min(LOT.pick, Math.floor((t - 1.2) / step) + 1)) : 0, stir = D ? 900 : 160;
      // the booth
      const bg = p.createLinearGradient(0, 0, 0, H); bg.addColorStop(0, "#1E2A50"); bg.addColorStop(1, "#0E1428"); p.fillStyle = bg; p.fillRect(0, 0, W, H);
      for (let k = 0; k < 8; k++) { p.fillStyle = k % 2 ? "#F0E8D8" : "#C03848"; p.beginPath(); p.moveTo(k * 40 - 2, 0); p.lineTo(k * 40 + 38, 0); p.lineTo(k * 40 + 38, 14); p.quadraticCurveTo(k * 40 + 18, 26, k * 40 - 2, 14); p.fill(); }
      // the drum's stand and the chute
      p.fillStyle = "#6A4A28"; p.fillRect(DX - 46, DY + DR - 4, 92, 14); p.fillRect(DX - 6, DY + DR + 8, 12, 40); p.fillStyle = "#8A6A38"; p.fillRect(30, H - 62, W - 60, 10);
      p.strokeStyle = "#B8C0D0"; p.lineWidth = 6; p.beginPath(); p.moveTo(DX + DR * 0.7, DY + DR * 0.7); p.quadraticCurveTo(DX + DR + 20, DY + DR + 10, W - 34, H - 76); p.stroke(); p.lineWidth = 1;
      // the balls tumbling in the drum
      const inDrum = this.ltBalls.filter((b) => !(D && D.balls.slice(0, out).includes(b.n)));
      for (const b of inDrum) { b.vy += 260 * dt; if (Math.random() < dt * 3) { b.vx += (Math.random() - 0.5) * stir; b.vy -= Math.random() * stir; } b.vx *= 0.99; b.vy *= 0.99; b.x += b.vx * dt; b.y += b.vy * dt;
        const dx = b.x - DX, dy = b.y - DY, d = Math.hypot(dx, dy), lim = DR - 12; if (d > lim) { const nx = dx / d, ny = dy / d, vn = b.vx * nx + b.vy * ny; b.x = DX + nx * lim; b.y = DY + ny * lim; if (vn > 0) { b.vx -= 1.7 * vn * nx; b.vy -= 1.7 * vn * ny; } } }
      for (let i = 0; i < inDrum.length; i++) for (let j = i + 1; j < inDrum.length; j++) { const a = inDrum[i], b = inDrum[j], dx = b.x - a.x, dy = b.y - a.y, d = Math.hypot(dx, dy); if (d < 22 && d > 0) { const k = (22 - d) / 2, nx = dx / d, ny = dy / d; a.x -= nx * k; a.y -= ny * k; b.x += nx * k; b.y += ny * k; } }
      p.save(); p.beginPath(); p.arc(DX, DY, DR, 0, Math.PI * 2); p.clip(); p.fillStyle = "rgba(160,200,255,0.08)"; p.fill(); for (const b of inDrum) ball(p, b.x, b.y, 11, b.n); p.restore();
      p.strokeStyle = "rgba(220,240,255,0.75)"; p.lineWidth = 3; p.beginPath(); p.arc(DX, DY, DR, 0, Math.PI * 2); p.stroke(); p.lineWidth = 1; p.fillStyle = "rgba(255,255,255,0.12)"; p.beginPath(); p.ellipse(DX - DR * 0.4, DY - DR * 0.45, DR * 0.35, DR * 0.18, -0.6, 0, Math.PI * 2); p.fill();
      p.strokeStyle = "#C8A060"; p.lineWidth = 4; for (let k = 0; k < 4; k++) { const a = (D ? t * 3 : now / 3000) + (k * Math.PI) / 2; p.beginPath(); p.moveTo(DX, DY); p.lineTo(DX + Math.cos(a) * 18, DY + Math.sin(a) * 18); p.stroke(); } p.lineWidth = 1;
      // the tray: the balls drawn so far, and one riding the chute
      if (D) { for (let k = 0; k < out; k++) { const n = D.balls[k], landed = t - 1.2 - k * step, f = Math.min(1, landed / 0.6), x0 = DX + DR * 0.7, y0 = DY + DR * 0.7, x1 = 44 + k * 42, y1 = H - 76, x = x0 + (x1 - x0) * f, y = y0 + (y1 - y0) * f - Math.sin(f * Math.PI) * 30;
          if (landed < 0.05 && !D[`s${k}`]) { D[`s${k}`] = true; this.cgSfx("cardplace", 0.4, 1.3); } if (f >= 1 && !D[`l${k}`]) { D[`l${k}`] = true; this.cgSfx(this.game.lotStore().slips.some((s) => s.key === D.key && s.nums.includes(n)) ? "coin" : "card", 0.45, 1.1); this.ltMark(n); }
          ball(p, x, y, f >= 1 ? 17 : 13, n, f >= 1 && (now / 300) % 2 < 1 && k === out - 1); }
        if (t > 1.2 + LOT.pick * step + 0.6 && !D.done) { D.done = true; const r = this.game.lotSettle(D.key); this.ltDraw = null; this.cgBusy = false; this.ltLast = r.error ? null : r; this.cgNote = r.error || (r.jackpot ? "ALL SIX! The square goes wild!" : r.gold ? "Winner! The crier counts out your gold." : "Not this time. There's always tomorrow night.");
          this.cgSfx(r.jackpot ? "victory" : r.gold ? "cardwin" : "cardlose", 0.5); if (r.gold) this.cgCoins(this.$("#casino-body"), Math.min(40, 6 + r.gold / 20)); this.renderCasino(); } }
      else if (this.ltLast) this.ltLast.balls.forEach((n, k) => ball(p, 44 + k * 42, H - 76, 17, n));
      else { p.fillStyle = "rgba(255,240,200,0.5)"; p.font = "italic 12px Georgia"; p.textAlign = "center"; p.fillText("The draw is at eight o'clock", W / 2, H - 72); p.textAlign = "left"; }
    },
    // a drawn number lit on the slips shown
    ltMark(n) { this.$("#casino-body").querySelectorAll(".ltslips .ltslip i").forEach((i) => { if (Number(i.textContent) === n) i.classList.add("hit"); }); },
  });
}
