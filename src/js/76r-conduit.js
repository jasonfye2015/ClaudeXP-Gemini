"use strict";
// The Mana Conduit, the window's side (the twenty-sixth big update): the slate on a canvas - brass conduits with a dark
// groove, the font a pulsing crystal, the drain a stone well, rubble; the rack of what comes next down the left (the top
// one is laid where you click, and shows where the pointer is); a sand-glass bar until the font opens, then the mana
// running glowing along each groove, a bubbling sound as it goes, a burst where it spills. The rules: 64zb-conduit.js.
CM.CG_TABLES.push(["conduit", "The Mana Conduit"]);
{ const floor0 = CM.UI.prototype.renderFloor, CELL = 56, RACK = 86;
  Object.assign(CM.UI.prototype, {
    renderFloor(box) { if (this.cgView === "conduit") return this.cgConduit(box); return floor0.call(this, box); },
    cgConduit(box) {
      const g = this.game, CD = CM.CD, S = g.cdStore(), B = g.cdLive, levels = CD.LEVELS.map((L, i) => { const k = i + 1, done = k <= S.best, open = k <= S.best + 1, tier = CM.cardTierFor(k); return `<button data-cdl="${k}" class="${B && B.level === k ? "primary" : ""}" ${open ? "" : "disabled"} title="pass ${L[4]} pieces; first time: ${CD.gold(k)} gold and a ${tier === "better" ? "stronger common" : tier} card${L[6] ? "; a drain for a fifth more" : ""}">${done ? "✓ " : open ? "" : "🔒 "}${k}</button>`; }).join("");
      const W = RACK + (B ? B.cols : 10) * CELL, H = (B ? B.rows : 7) * CELL;
      box.innerHTML = `<div class="cgtable conduit"><h3>The Mana Conduit</h3><p class="lore">A slate table with a font of mana set in it, and a rack of brass conduit by its side. "Lay a way for it before it opens," says the attendant. "It does not like to be kept waiting, and it does not like to spill."</p>
        <div class="lxlevels"><span class="lbl">Level:</span>${levels}</div>
        <div class="cdwrap"><canvas class="cdcanvas" width="${W}" height="${H + 30}"></canvas></div>
        <div class="cgnote">${this.cgNote || ""}</div>${this.cdPrize && this.cdPrize.card ? this.cgCardWon(this.cdPrize.card) : ""}
        <div class="row">${B && B.stage !== "done" ? `<button data-cdfast>${B.stage === "build" ? "Open the font now" : "Hurry the mana"}</button>` : B ? `<button class="primary" data-cdagain>${B.won ? (B.level < CD.LEVELS.length ? `On to level ${B.level + 1}` : "Again") : "Try again"}</button>` : ""}<button data-leave>Leave</button></div>
        <div class="small">Click a square to lay the top piece of the rack there; laying it over a dry piece swaps it (before the font opens it costs a little time). The mana must pass through as many pieces as the level asks before it reaches an open end; a crossing it runs both ways counts twice; from level 6 a drain to finish in pays a fifth more. Each level pays gold and a Claudescryption card the first time (common to 4, a stronger common to 9, rare at 10); it costs nothing to play. Done ${S.best} of ${CD.LEVELS.length}.</div></div>`;
      const q = (s) => box.querySelector(s); q("[data-leave]").addEventListener("click", () => this.closeDialogs());
      const start = (lv) => { const r = g.cdStart(lv); this.cgNote = r.error || ""; this.cdPrize = null; this.cdFx = { spill: null, last: 0 }; this.cgSfx("cardplace", 0.4); this.renderCasino(); };
      box.querySelectorAll("[data-cdl]").forEach((b) => b.addEventListener("click", () => start(Number(b.dataset.cdl))));
      if (q("[data-cdagain]")) q("[data-cdagain]").addEventListener("click", () => start(B.won ? Math.min(CD.LEVELS.length, B.level + 1) : B.level));
      if (q("[data-cdfast]")) q("[data-cdfast]").addEventListener("click", () => { if (B.stage === "build") B.t = B.wait; else B.fast = true; this.cgSfx("spell", 0.4); this.renderCasino(); });
      const cv = q(".cdcanvas"); this.cdCanvas = cv;
      const cell = (e) => { const r = cv.getBoundingClientRect(), x = ((e.clientX - r.left) * cv.width) / r.width - RACK, y = ((e.clientY - r.top) * cv.height) / r.height - 30; return [Math.floor(x / CELL), Math.floor(y / CELL)]; };
      cv.addEventListener("mousemove", (e) => { this.cdHover = cell(e); });
      cv.addEventListener("mouseleave", () => { this.cdHover = null; });
      cv.addEventListener("mousedown", (e) => { const Bd = g.cdLive; if (!Bd) return; const [x, y] = cell(e); if (Bd.place(x, y)) { const ev = Bd.events[Bd.events.length - 1]; this.cgSfx(ev.kind === "swap" ? "grind" : "cardplace", 0.4, ev.kind === "swap" ? 1.2 : 0.9 + Math.random() * 0.2); } else this.cgSfx("miss", 0.2, 1.5); });
      if (!this.cdLoop) { let prev = performance.now(); const loop = (now) => { if (!this.cdCanvas || !this.cdCanvas.isConnected || this.cgView !== "conduit") { this.cdLoop = null; return; } const dt = Math.min(0.05, (now - prev) / 1000); prev = now; this.cdFrame(dt, now); this.cdLoop = requestAnimationFrame(loop); }; this.cdLoop = requestAnimationFrame(loop); }
    },
    cdFrame(dt, now) {
      const g = this.game, CD = CM.CD, B = g.cdLive, cv = this.cdCanvas, p = cv.getContext("2d"), fx = this.cdFx = this.cdFx || { spill: null, last: 0 };
      p.fillStyle = "#14100C"; p.fillRect(0, 0, cv.width, cv.height);
      if (!B) { p.fillStyle = "rgba(255,240,200,0.85)"; p.font = "bold 24px Georgia, serif"; p.textAlign = "center"; p.fillText("Choose a level", cv.width / 2, cv.height / 2); p.textAlign = "left"; return; }
      B.update(dt);
      for (const e of B.events.splice(0)) {
        if (e.kind === "open") { this.cgSfx("spell", 0.55, 0.8); this.cgNote = "The font opens!"; this.renderCasino(); }
        else if (e.kind === "fill") { this.cgSfx("splash", 0.18, 1.2 + Math.min(1, e.n / 25)); if (e.cross) this.cgSfx("coin", 0.4, 1.5); if (e.n === B.need) this.cgSfx("tablebell", 0.5); }
        else if (e.kind === "end") { fx.spill = { x: e.x, y: e.y, at: now, won: e.won, drained: e.drained }; this.cgSfx(e.drained ? "victory" : e.won ? "victory" : "splash", 0.6, e.won ? 1 : 0.6);
          setTimeout(() => { const r = g.cdDone(); if (!r) return; this.cdPrize = r; this.cgNote = !r.won ? `Spilled after ${r.passed} of ${r.need}.` : r.again ? `Level ${r.level} done again${r.drained ? ", into the drain" : ""} (its prize was paid the first time).` : `Level ${r.level} done${r.drained ? ", into the drain" : ""}: ${r.gold} gold, and a card - ${r.card}.`; if (r.card) this.cgSfx("cardwin", 0.5); this.renderCasino(); if (r.gold) this.cgCoins(this.$("#casino-body"), 12); }, 900); }
      }
      // the bar: the sand-glass, then the count
      const barW = cv.width - RACK - 10; p.fillStyle = "#2A2018"; p.fillRect(RACK, 6, barW, 16);
      if (B.stage === "build") { const k = 1 - B.t / B.wait; p.fillStyle = k < 0.25 ? "#E05030" : "#C8A040"; p.fillRect(RACK, 6, barW * k, 16); p.fillStyle = "#FFF"; p.font = "bold 12px Georgia, serif"; p.fillText(`The font opens in ${Math.ceil(B.wait - B.t)}s - pass ${B.need} pieces`, RACK + 8, 18); }
      else { const k = Math.min(1, B.passed / B.need); p.fillStyle = "#3AC0E0"; p.fillRect(RACK, 6, barW * k, 16); p.fillStyle = "#FFF"; p.font = "bold 12px Georgia, serif"; p.fillText(`${B.passed} of ${B.need} pieces${B.passed >= B.need ? " - enough!" : ""}`, RACK + 8, 18); }
      // the rack
      p.fillStyle = "#3A2A18"; p.fillRect(4, 30, RACK - 12, CELL * B.rows); p.fillStyle = "#E8D8B0"; p.font = "11px Georgia, serif"; p.fillText("NEXT", 22, 44);
      B.queue.forEach((k, i) => { const y = 50 + i * 62, s = i ? 0.75 : 1; p.save(); p.translate(8 + (RACK - 16 - CELL * s) / 2, y); p.scale(s, s); p.fillStyle = i ? "#2A1E14" : "#4A3420"; p.fillRect(0, 0, CELL, CELL); this.cdPiece(p, 0, 0, k, null, now); p.restore(); if (!i) { p.strokeStyle = "#F0D070"; p.lineWidth = 2; p.strokeRect(8 + (RACK - 16 - CELL) / 2, y, CELL, CELL); p.lineWidth = 1; } });
      // the slate
      for (let y = 0; y < B.rows; y++) for (let x = 0; x < B.cols; x++) { const X = RACK + x * CELL, Y = 30 + y * CELL; p.fillStyle = (x + y) % 2 ? "#2E2A28" : "#34302C"; p.fillRect(X, Y, CELL, CELL); for (let k = 0; k < 7; k++) { const h = (x * 131 + y * 71 + k * 37) % 97; p.fillStyle = k % 3 ? "rgba(0,0,0,0.16)" : "rgba(255,255,255,0.05)"; p.fillRect(X + 4 + (h % (CELL - 10)), Y + 4 + ((h * 7) % (CELL - 10)), 2 + (h % 3), 1 + (h % 2)); }
        const sg = p.createLinearGradient(X, Y, X + CELL, Y + CELL); sg.addColorStop(0, "rgba(255,255,255,0.05)"); sg.addColorStop(1, "rgba(0,0,0,0.12)"); p.fillStyle = sg; p.fillRect(X, Y, CELL, CELL); p.strokeStyle = "rgba(0,0,0,0.45)"; p.strokeRect(X + 0.5, Y + 0.5, CELL - 1, CELL - 1); p.strokeStyle = "rgba(255,255,255,0.04)"; p.beginPath(); p.moveTo(X + 1.5, Y + CELL - 1.5); p.lineTo(X + 1.5, Y + 1.5); p.lineTo(X + CELL - 1.5, Y + 1.5); p.stroke();
        const c = B.grid[y][x]; if (!c) continue;
        if (c.kind === "rubble") { p.fillStyle = "#5A524A"; for (const [a, b2, r] of [[18, 22, 12], [36, 30, 14], [24, 40, 9], [40, 16, 7]]) { p.beginPath(); p.arc(X + a, Y + b2, r, 0, Math.PI * 2); p.fill(); } p.fillStyle = "rgba(255,255,255,0.12)"; p.beginPath(); p.arc(X + 32, Y + 26, 6, 0, Math.PI * 2); p.fill(); }
        else if (c.kind === "font") { const [dx, dy] = CD.DIRS[c.out]; p.fillStyle = "#6A5A3A"; p.fillRect(X + CELL / 2 - 8 + Math.min(0, dx) * 20, Y + CELL / 2 - 8 + Math.min(0, dy) * 20, 16 + Math.abs(dx) * 20 + (dx > 0 ? 12 : 0), 16 + Math.abs(dy) * 20 + (dy > 0 ? 12 : 0)); const pulse = 0.6 + 0.4 * Math.sin(now / 250); p.save(); p.shadowColor = "#60E0FF"; p.shadowBlur = 16 * pulse; p.fillStyle = "#60D0F0"; p.beginPath(); p.moveTo(X + CELL / 2, Y + 8); p.lineTo(X + CELL - 14, Y + CELL / 2); p.lineTo(X + CELL / 2, Y + CELL - 8); p.lineTo(X + 14, Y + CELL / 2); p.closePath(); p.fill(); p.restore(); }
        else if (c.kind === "drain") { const [dx, dy] = CD.DIRS[c.in]; p.fillStyle = "#6A5A3A"; p.fillRect(X + CELL / 2 - 8 + Math.min(0, dx) * 20, Y + CELL / 2 - 8 + Math.min(0, dy) * 20, 16 + Math.abs(dx) * 20 + (dx > 0 ? 12 : 0), 16 + Math.abs(dy) * 20 + (dy > 0 ? 12 : 0)); p.fillStyle = "#4A4440"; p.beginPath(); p.arc(X + CELL / 2, Y + CELL / 2, 18, 0, Math.PI * 2); p.fill(); p.fillStyle = "#08080C"; p.beginPath(); p.arc(X + CELL / 2, Y + CELL / 2, 12, 0, Math.PI * 2); p.fill(); }
        else this.cdPiece(p, X, Y, c.p, c, now, B);
      }
      { const bx0 = RACK, by0 = 30, bx1 = RACK + B.cols * CELL, by1 = 30 + B.rows * CELL; p.strokeStyle = "#7A5A30"; p.lineWidth = 3; p.strokeRect(bx0 - 1.5, by0 - 1.5, bx1 - bx0 + 3, by1 - by0 + 3); p.lineWidth = 1; for (const [rx, ry] of [[bx0, by0], [bx1, by0], [bx0, by1], [bx1, by1]]) { const rg = p.createRadialGradient(rx - 1, ry - 1, 0.5, rx, ry, 4); rg.addColorStop(0, "#FFF0B0"); rg.addColorStop(1, "#8A6420"); p.fillStyle = rg; p.beginPath(); p.arc(rx, ry, 4, 0, Math.PI * 2); p.fill(); } }
      for (let y = 0; y < B.rows; y++) for (let x = 0; x < B.cols; x++) { const c = B.grid[y][x]; if (!c || c.kind !== "font") continue; const X = RACK + x * CELL + CELL / 2, Y = 30 + y * CELL + CELL / 2, lg = p.createRadialGradient(X, Y, 6, X, Y, CELL * 1.6); lg.addColorStop(0, `rgba(96,208,240,${0.16 + 0.06 * Math.sin(now / 250)})`); lg.addColorStop(1, "rgba(96,208,240,0)"); p.fillStyle = lg; p.fillRect(X - CELL * 1.6, Y - CELL * 1.6, CELL * 3.2, CELL * 3.2); }
      if (B.stage !== "build") { fx.sp = (fx.sp || []).filter((q) => (q.life -= dt) > 0); if (Math.random() < dt * 14) { const wet = []; for (let y = 0; y < B.rows; y++) for (let x = 0; x < B.cols; x++) { const c = B.grid[y][x]; if (c && c.kind === "pipe" && c.wet) wet.push([x, y]); } if (wet.length) { const [wx, wy] = wet[Math.floor(Math.random() * wet.length)]; fx.sp.push({ x: RACK + wx * CELL + CELL / 2 + (Math.random() - 0.5) * 20, y: 30 + wy * CELL + CELL / 2 + (Math.random() - 0.5) * 20, life: 0.5 }); } }
        for (const q of fx.sp) { p.globalAlpha = q.life * 2; p.fillStyle = "#C8F4FF"; p.fillRect(q.x - 1, q.y - 1 - (0.5 - q.life) * 14, 2, 2); } p.globalAlpha = 1; }
      // where the next piece would go
      const hv = this.cdHover; if (hv && B.stage !== "done" && hv[0] >= 0 && hv[1] >= 0 && hv[0] < B.cols && hv[1] < B.rows) { const c = B.grid[hv[1]][hv[0]], ok = !c || (c.kind === "pipe" && !c.wet); p.globalAlpha = 0.45; if (ok) this.cdPiece(p, RACK + hv[0] * CELL, 30 + hv[1] * CELL, B.queue[0], null, now); p.globalAlpha = 1; p.strokeStyle = ok ? "#F0D070" : "#E05030"; p.lineWidth = 2; p.strokeRect(RACK + hv[0] * CELL + 1, 30 + hv[1] * CELL + 1, CELL - 2, CELL - 2); p.lineWidth = 1; }
      // a spill
      if (fx.spill && now - fx.spill.at < 1200) { const t = (now - fx.spill.at) / 1200, X = RACK + fx.spill.x * CELL + CELL / 2, Y = 30 + fx.spill.y * CELL + CELL / 2; for (let k = 0; k < 18; k++) { const a = k * 0.35, r = 10 + t * 50 * (0.6 + (k % 3) * 0.2); p.fillStyle = fx.spill.won ? `rgba(255,230,120,${1 - t})` : `rgba(90,210,255,${1 - t})`; p.beginPath(); p.arc(X + Math.cos(a) * r, Y + Math.sin(a) * r, 3 + 3 * (1 - t), 0, Math.PI * 2); p.fill(); } }
    },
    // a conduit piece: brass arms to its open sides, a dark groove, the mana in it (filling, for the one being filled)
    cdPiece(p, X, Y, k, c, now, B) {
      const CD = CM.CD, open = CD.PIECES[k], cx = X + CELL / 2, cy = Y + CELL / 2, arm = (d) => { const [dx, dy] = CD.DIRS[d]; return [cx + dx * CELL / 2, cy + dy * CELL / 2]; };
      const stroke = (pts, col, w) => { p.strokeStyle = col; p.lineWidth = w; p.lineCap = "butt"; p.beginPath(); p.moveTo(...pts[0]); for (const q of pts.slice(1)) p.lineTo(...q); p.stroke(); };
      const paths = k === "X" ? [["W", "E"], ["N", "S"]] : [open];
      for (const [a, b] of paths) { const pts = [arm(a), [cx, cy], arm(b)]; stroke(pts, "#6A4A18", 22); stroke(pts, "#C8A040", 18); stroke(pts, "#1A120A", 8); }
      p.fillStyle = "#D8B050"; p.beginPath(); p.arc(cx, cy, k === "X" ? 6 : 4, 0, Math.PI * 2); p.fill();
      if (!c || !c.wet) return;
      const glow = (pts) => { p.save(); p.shadowColor = "#60E0FF"; p.shadowBlur = 8; stroke(pts, "#5AD8F8", 7); p.restore(); };
      const F = B && B.flow, filling = F && F.x === (X - 86) / CELL && F.y === (Y - 30) / CELL && B.stage === "flow", frac = filling ? Math.min(1, F.t / F.fillT) : 1;
      if (k === "X") { for (const ax of c.through || []) { const [a, b] = ax === "H" ? ["W", "E"] : ["N", "S"], last = ax === (c.through || [])[c.through.length - 1], f = last ? frac : 1, from = c.entry && last ? c.entry : a, to = from === a ? b : a, A = arm(from), Z = arm(to); glow([A, [A[0] + (Z[0] - A[0]) * f, A[1] + (Z[1] - A[1]) * f]]); } return; }
      const from = c.entry, to = open.find((d) => d !== from), A = arm(from), Z = arm(to);
      if (frac <= 0.5) { const f = frac * 2; glow([A, [A[0] + (cx - A[0]) * f, A[1] + (cy - A[1]) * f]]); } else { const f = (frac - 0.5) * 2; glow([A, [cx, cy], [cx + (Z[0] - cx) * f, cy + (Z[1] - cy) * f]]); }
      void now;
    },
  });
}
