"use strict";
// The Gilded Cascade, the window's side (the twenty-fifth big update): the machine on a canvas, in perspective - a
// marquee of chasing lamps, the brass pusher sliding across the back, the shelf of coins (each a gold disc with its
// rim and shine, a nugget a lump, a card token a little glowing card, an item token a sealed purple box), glass sides,
// dark gutters, and the tray below where what falls over the edge tumbles in and rings. Click over the shelf to drop a
// coin there (the chute follows the mouse), or hold the button to keep dropping. The rules are 64z-cascade.js.
CM.CG_TABLES.push(["cascade", "The Gilded Cascade"]);
{ const floor0 = CM.UI.prototype.renderFloor, VW = 560, VH = 600, TOP = 96;
  const proj = (x, y) => { const CS = CM.CS, s = 0.72 + 0.28 * (y / CS.D), w = 1.45 * s; return [VW / 2 + (x - CS.W / 2) * w, TOP + y * 1.18, w]; };
  Object.assign(CM.UI.prototype, {
    renderFloor(box) { if (this.cgView === "cascade") return this.cgCascade(box); return floor0.call(this, box); },
    cgCascade(box) {
      const g = this.game, CS = CM.CS, S = g.csStore(), cup = {}; for (const v of S.coins) cup[v] = (cup[v] || 0) + 1;
      const vals = Object.keys(cup).map(Number).sort((a, b) => a - b); if (!vals.includes(this.csVal)) this.csVal = vals[vals.length - 1];
      box.innerHTML = `<div class="cgtable cascade"><h3>The Gilded Cascade</h3><div class="cswrap"><canvas class="cscanvas" width="${VW}" height="${VH}"></canvas><div class="cside">
        <p class="lore">A tall cabinet of glass and brass, its lamps chasing round the top. Behind the glass a shelf heaped with coins, and a pusher that never stops. "Drop them in," says the attendant. "What goes over the edge is yours."</p>
        <div class="list-title">Buy a cup of twenty coins</div><div class="row">${CS.CUPS.map(([n, v], i) => `<button data-cscup="${i}" ${n * v > g.gold ? "disabled" : ""}>${n} at ${v} gold <small>(${n * v})</small></button>`).join("")}</div>
        <div class="list-title">In your cup</div><div class="cscup">${vals.length ? vals.map((v) => `<button data-csv="${v}" class="${this.csVal === v ? "primary" : ""}"><b>${cup[v]}</b> × ${v}g</button>`).join("") : "<small>Empty - buy a cup.</small>"}</div>
        <div class="cgnote">${this.cgNote || ""}</div><div class="cswins">${(this.csWins || []).slice(-3).map((w) => w.card ? this.cgCardWon(w.card) : w.item ? `<div class="cgprize"><span class="em">📦</span><div><b>${this.esc(w.item.name)}</b><small>Into the bag</small></div></div>` : "").join("")}</div>
        <div class="row">${vals.length ? `<button data-cscash>Cash in the cup</button>` : ""}<button data-leave>Leave</button></div>
        <div class="small">Click over the shelf to drop a coin where you choose; hold to keep dropping. Coins pushed over the front edge are paid at their worth; those that slip into the side gutters are the house's. Now and then a prize comes down with a coin - a nugget worth ten, a card token or a sealed item - push it over the edge to win it. The shelf is kept as you leave it. About nine in ten of what goes in comes back over the edge, more with the prizes and a good eye for where to drop.</div>${this.cgStats("cascade")}</div></div></div>`;
      const q = (s2) => box.querySelector(s2); q("[data-leave]").addEventListener("click", () => { g.csKeep(); this.closeDialogs(); });
      box.querySelectorAll("[data-cscup]").forEach((b) => b.addEventListener("click", () => { const r = g.csBuy(Number(b.dataset.cscup)); this.cgNote = r.error || `Twenty ${r.v}-gold coins clatter into your cup.`; if (!r.error) { this.csVal = r.v; this.cgSfx("coin", 0.6); setTimeout(() => this.cgSfx("coin", 0.4, 1.2), 90); } this.renderCasino(); }));
      box.querySelectorAll("[data-csv]").forEach((b) => b.addEventListener("click", () => { this.csVal = Number(b.dataset.csv); this.renderCasino(); }));
      if (q("[data-cscash]")) q("[data-cscash]").addEventListener("click", () => { const v = g.csCashCup(); this.cgNote = `The cup is cashed in: ${v} gold.`; this.cgSfx("coin", 0.5); this.renderCasino(); });
      const cv = q(".cscanvas"); this.csCanvas = cv; this.csFx = this.csFx || { falls: [], drops: [] };
      const toBed = (e) => { const r = cv.getBoundingClientRect(), sx = ((e.clientX - r.left) * VW) / r.width, [, , w] = proj(0, CS.faceMax); return CS.W / 2 + (sx - VW / 2) / w; };
      cv.addEventListener("mousemove", (e) => { this.csAim = toBed(e); });
      cv.addEventListener("mousedown", (e) => { this.csAim = toBed(e); this.csHold = true; this.csHoldT = 0; this.csDropOne(); });
      cv.addEventListener("mouseup", () => { this.csHold = false; }); cv.addEventListener("mouseleave", () => { this.csHold = false; this.csAim = null; });
      if (!this.csLoop) { let prev = performance.now(), keepT = 0; const loop = (now) => { if (!this.csCanvas || !this.csCanvas.isConnected || this.cgView !== "cascade") { this.csLoop = null; this.game.csKeep(); return; } const dt = Math.min(0.05, (now - prev) / 1000); prev = now; this.csFrame(dt, now); if ((keepT += dt) > 5) { keepT = 0; this.game.csKeep(); } this.csLoop = requestAnimationFrame(loop); }; this.csLoop = requestAnimationFrame(loop); }
    },
    csDropOne() {
      const g = this.game, S = g.csStore(); if (!S.coins.length) { this.cgNote = "Your cup is empty: buy a cup of coins."; const n = this.$("#casino-body .cgnote"); if (n) n.textContent = this.cgNote; this.cgSfx("miss", 0.3); this.csHold = false; return; }
      const v = S.coins.includes(this.csVal) ? this.csVal : S.coins[S.coins.length - 1], x = this.csAim === null || this.csAim === undefined ? CM.CS.W / 2 : this.csAim, d = g.csDrop(x, v); if (!d) return;
      this.csFx.drops.push({ id: d.id, at: performance.now() }); this.cgSfx("card", 0.25, 1.8 + Math.random() * 0.3); setTimeout(() => this.cgSfx("coin", 0.25, 0.8 + Math.random() * 0.3), 220);
      const left = S.coins.filter((c) => c === v).length; const b = this.$(`#casino-body [data-csv="${v}"] b`); if (b) b.textContent = left; if (!left) setTimeout(() => this.renderCasino(), 300);
    },
    csFrame(dt, now) {
      const g = this.game, CS = CM.CS, B = g.csBed(), cv = this.csCanvas, p = cv.getContext("2d"), fx = this.csFx;
      if (this.csHold) { this.csHoldT += dt; if (this.csHoldT > 0.28) { this.csHoldT = 0; this.csDropOne(); } }
      const off = B.update(dt); B.events.length = 0;
      if (off.length) { const won = g.csCollect(off); for (const o of off) fx.falls.push({ d: o.d, where: o.where, at: now, x: o.d.x, y: o.d.y });
        if (won.gold) { this.cgSfx("coin", 0.5, 0.9 + Math.random() * 0.4); const n = this.$("#casino-body .cggold"); if (n) n.textContent = `${g.gold} gold`; }
        if (off.some((o) => o.where === "gutter")) this.cgSfx("step", 0.2, 0.6);
        if (won.got.length) { this.csWins = (this.csWins || []).concat(won.got); this.cgSfx("victory", 0.55); this.cgSfx("cardwin", 0.5); this.cgNote = won.got.map((w) => w.card ? `A card token over the edge: ${w.card}!` : `A sealed box over the edge: ${w.item.name}!`).join(" "); setTimeout(() => this.renderCasino(), 60); }
        if (off.some((o) => o.where === "front" && o.d.k === "nugget")) this.cgSfx("victory", 0.45); }
      // the cabinet
      p.fillStyle = "#1A0E0A"; p.fillRect(0, 0, VW, VH); const back = p.createLinearGradient(0, TOP, 0, TOP + CS.D * 1.18); back.addColorStop(0, "#2A1A2E"); back.addColorStop(1, "#4A2E1A"); p.fillStyle = back;
      const [lx0, ly0] = proj(0, 0), [rx0] = proj(CS.W, 0), [lx1, ly1] = proj(0, CS.D), [rx1] = proj(CS.W, CS.D); p.beginPath(); p.moveTo(lx0, ly0); p.lineTo(rx0, ly0); p.lineTo(rx1, ly1); p.lineTo(lx1, ly1); p.closePath(); p.fill();
      p.strokeStyle = "rgba(200,160,64,0.25)"; for (let y = 40; y < CS.D; y += 40) { const [a, b] = proj(0, y), [c2] = proj(CS.W, y); p.beginPath(); p.moveTo(a, b); p.lineTo(c2, b); p.stroke(); }
      // gutters
      const [gl0, gy0] = proj(0, CS.gutterFrom), [gr0] = proj(CS.W, CS.gutterFrom); p.fillStyle = "#050303"; p.beginPath(); p.moveTo(gl0 - 26, gy0); p.lineTo(gl0, gy0); p.lineTo(lx1, ly1); p.lineTo(lx1 - 30, ly1); p.fill(); p.beginPath(); p.moveTo(gr0, gy0); p.lineTo(gr0 + 26, gy0); p.lineTo(rx1 + 30, ly1); p.lineTo(rx1, ly1); p.fill();
      // the tray
      p.fillStyle = "#3A2410"; p.fillRect(lx1 - 20, ly1 + 8, rx1 - lx1 + 40, VH - ly1 - 14); p.fillStyle = "#C8A040"; p.fillRect(lx1 - 20, ly1 + 4, rx1 - lx1 + 40, 6); p.fillStyle = "#E8D090"; p.font = "bold 13px Georgia, serif"; p.textAlign = "center"; p.fillText(`Won here: ${g.csStore().won} gold`, VW / 2, VH - 16); p.textAlign = "left";
      // the pusher
      const f = B.face(), [pl, py] = proj(0, f), [pr] = proj(CS.W, f), [bl, by] = proj(0, 0), [br] = proj(CS.W, 0);
      const brass = p.createLinearGradient(0, by, 0, py); brass.addColorStop(0, "#5A4018"); brass.addColorStop(1, "#C8A040"); p.fillStyle = brass; p.beginPath(); p.moveTo(bl, by); p.lineTo(br, by); p.lineTo(pr, py); p.lineTo(pl, py); p.closePath(); p.fill();
      p.fillStyle = "#8A6420"; p.fillRect(pl, py - 2, pr - pl, 10); p.strokeStyle = "rgba(255,240,180,0.6)"; p.beginPath(); p.moveTo(pl, py - 2); p.lineTo(pr, py - 2); p.stroke();
      // the discs, back to front; a dropped one falls into its place
      const L = B.discs.slice().sort((a, b) => a.y - b.y);
      for (const d of L) { const dr = fx.drops.find((q) => q.id === d.id), k = dr ? Math.min(1, (now - dr.at) / 260) : 1, [sx, sy, w] = proj(d.x, d.y); this.csDisc(p, d, sx, sy - (1 - k) * 90, w, now); }
      fx.drops = fx.drops.filter((q) => now - q.at < 300);
      // over the edge: tumbling into the tray, or away down a gutter
      fx.falls = fx.falls.filter((o) => now - o.at < 600); for (const o of fx.falls) { const t = (now - o.at) / 600, [sx, sy, w] = proj(Math.max(-20, Math.min(CS.W + 20, o.x)), Math.min(CS.D, o.y)); p.globalAlpha = 1 - t; this.csDisc(p, o.d, sx + (o.where === "gutter" ? (o.x < 0 ? -1 : 1) * 30 * t : 0), sy + t * t * 80, w * (1 - 0.3 * t), now); p.globalAlpha = 1; }
      // glass and frame
      p.fillStyle = "rgba(180,220,255,0.05)"; p.fillRect(lx1 - 40, TOP - 10, rx1 - lx1 + 80, ly1 - TOP + 10); p.strokeStyle = "#C8A040"; p.lineWidth = 6; p.beginPath(); p.moveTo(lx0 - 8, ly0 - 10); p.lineTo(lx1 - 34, ly1); p.moveTo(rx0 + 8, ly0 - 10); p.lineTo(rx1 + 34, ly1); p.stroke(); p.lineWidth = 1;
      // the marquee and its chasing lamps
      p.fillStyle = "#4A0E14"; p.fillRect(20, 10, VW - 40, 64); p.strokeStyle = "#E0B040"; p.lineWidth = 3; p.strokeRect(20, 10, VW - 40, 64); p.lineWidth = 1; p.fillStyle = "#FFE080"; p.font = "bold 26px Georgia, serif"; p.textAlign = "center"; p.fillText("THE GILDED CASCADE", VW / 2, 52); p.textAlign = "left";
      for (let k = 0; k < 28; k++) { const on = (Math.floor(now / 110) + k) % 4 === 0; p.fillStyle = on ? "#FFF0A0" : "#7A5A20"; const x = 26 + k * ((VW - 52) / 27); p.beginPath(); p.arc(x, 16, 3.5, 0, Math.PI * 2); p.arc(x, 68, 3.5, 0, Math.PI * 2); p.fill(); }
      // the chute, over where the mouse is
      if (this.csAim !== null && this.csAim !== undefined) { const ax = Math.max(CS.R, Math.min(CS.W - CS.R, this.csAim)), [cx2] = proj(ax, f); p.fillStyle = "rgba(255,230,140,0.25)"; p.fillRect(cx2 - 2, TOP - 14, 4, py - TOP + 10); p.fillStyle = "#C8A040"; p.fillRect(cx2 - 14, TOP - 20, 28, 10); }
    },
    csDisc(p, d, x, y, w, now) {
      const r = CM.CS.R * w, ry = r * 0.55;
      p.fillStyle = "rgba(0,0,0,0.35)"; p.beginPath(); p.ellipse(x + 2, y + 3, r, ry, 0, 0, Math.PI * 2); p.fill();
      if (d.k === "card") { p.save(); p.shadowColor = "#A0E0FF"; p.shadowBlur = 10 + 4 * Math.sin(now / 200); p.fillStyle = "#F4ECD8"; p.fillRect(x - r * 0.7, y - r * 1.1, r * 1.4, r * 1.6); p.restore(); p.strokeStyle = "#6A4A20"; p.strokeRect(x - r * 0.7, y - r * 1.1, r * 1.4, r * 1.6); p.font = `${Math.round(r)}px serif`; p.textAlign = "center"; p.fillText("🂠", x, y + r * 0.2); p.textAlign = "left"; return; }
      if (d.k === "item") { p.save(); p.shadowColor = "#D080FF"; p.shadowBlur = 10 + 4 * Math.sin(now / 230); p.fillStyle = "#6A2A9A"; p.fillRect(x - r * 0.9, y - r * 1.0, r * 1.8, r * 1.4); p.restore(); p.fillStyle = "#E0B040"; p.fillRect(x - 2, y - r * 1.0, 4, r * 1.4); p.fillRect(x - r * 0.9, y - r * 0.4, r * 1.8, 3); return; }
      const nug = d.k === "nugget", gr = p.createLinearGradient(x - r, y - ry, x + r, y + ry); gr.addColorStop(0, nug ? "#FFF0A0" : "#FFE890"); gr.addColorStop(0.5, nug ? "#E0A020" : "#D8A830"); gr.addColorStop(1, "#7A5410");
      p.fillStyle = "#6A4A10"; p.beginPath(); p.ellipse(x, y + 2, r, ry, 0, 0, Math.PI * 2); p.fill(); p.fillStyle = gr; p.beginPath();
      if (nug) { for (let k = 0; k < 9; k++) { const a = (k / 9) * Math.PI * 2, rr = 1.15 + 0.15 * Math.sin(k * 3.3); p.lineTo(x + Math.cos(a) * r * rr, y + Math.sin(a) * ry * rr * 1.2); } p.closePath(); } else p.ellipse(x, y, r, ry, 0, 0, Math.PI * 2);
      p.fill(); if (!nug) { p.strokeStyle = "rgba(120,80,10,0.8)"; p.beginPath(); p.ellipse(x, y, r * 0.7, ry * 0.7, 0, 0, Math.PI * 2); p.stroke(); if (d.v >= 25) { p.fillStyle = "rgba(160,40,40,0.75)"; p.beginPath(); p.ellipse(x, y, r * 0.35, ry * 0.35, 0, 0, Math.PI * 2); p.fill(); } else if (d.v >= 5) { p.fillStyle = "rgba(220,230,240,0.7)"; p.beginPath(); p.ellipse(x, y, r * 0.35, ry * 0.35, 0, 0, Math.PI * 2); p.fill(); } }
      p.fillStyle = "rgba(255,255,255,0.55)"; p.beginPath(); p.ellipse(x - r * 0.35, y - ry * 0.35, r * 0.25, ry * 0.18, -0.3, 0, Math.PI * 2); p.fill();
    },
  });
}
