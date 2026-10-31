"use strict";
// Runestack, the window's side (the twenty-fifth big update): the well on a canvas, its stones cut and bevelled with a
// rune on each, a ghost where the falling one will land, rows that flash white and burst into chips when cut, the well
// shaking a little at a slam, a banner when the level rises (with its gold and its card); beside it the next three
// stones, the score, the lines, and the ladder of what each level pays (the cards already won marked). Arrow keys or
// W A S D move, Up / X turn (Z the other way), Space drops, P pauses. The rules are 64y-runestack.js.
CM.CG_TABLES.push(["runestack", "Runestack"]);
{ const floor0 = CM.UI.prototype.renderFloor, CELL = 28;
  Object.assign(CM.UI.prototype, {
    renderFloor(box) { if (this.cgView === "runestack") return this.cgRunestack(box); return floor0.call(this, box); },
    cgRunestack(box) {
      const g = this.game, RS = CM.RS, S = g.rsState(), W = g.rsWell(), live = !!W, bet = live ? S.bet : (this.cgBet === undefined ? 5 : this.cgBet), C = g.rsClaimed(), last = S && S.stage === "done" ? S.last : null;
      const top = Math.max(12, (W ? W.level : 1) + 4), rows = []; for (let n = 1; n <= top; n++) rows.push(`<div class="rung${W && W.level === n ? " now" : ""}${W && W.level > n ? " done" : ""}"><span>Level ${n}</span><b>${Math.round(bet * RS.pay(n))}</b><i class="${C[n] ? "got" : RS.cardKind(n)}" title="${C[n] ? "card already won" : `a ${RS.cardKind(n)} card, the first time`}">${C[n] ? "✓" : RS.cardKind(n) === "rare" ? "★" : RS.cardKind(n) === "better" ? "◆" : "♦"}</i></div>`);
      box.innerHTML = `<div class="cgtable runestack dash"><h3>Runestack</h3><div class="rswrap"><canvas class="rscanvas" width="${RS.W * CELL}" height="${RS.H * CELL}" tabindex="0"></canvas>
        <div class="rsmid"><div class="lbl">Next</div><canvas class="rsnext" width="96" height="230"></canvas><div class="rsinfo"><div>Score <b class="rssc">${W ? W.score : 0}</b></div><div>Lines <b class="rsln">${W ? W.lines : 0}</b></div><div>Level <b class="rslv">${W ? W.level : "-"}</b></div><div>Won <b class="rswon">${S && (live || last) ? S.won : 0}</b> gold</div><div class="small">Best score ${g.cgStore().rsBest || 0}</div></div></div>
        <div class="dashside"><p class="lore">A tall glass case of black water by the wall, and rune-stones that sink through it of their own accord. "Fill a row and the water takes it," says the attendant. "Ten rows, and they come faster."</p>
        <div class="ladder rsladder">${rows.reverse().join("")}</div>
        ${live ? "" : this.cgBetRow("The stake")}<div class="cgnote">${this.cgNote || ""}</div>${last && last.cards && last.cards.length ? last.cards.map((c) => this.cgCardWon(c)).join("") : ""}
        <div class="row">${live ? `<button data-rspause>${this.rsPaused ? "Go on" : "Pause"}</button><button data-rsquit>Stop here</button>` : `<button class="primary" data-rsstart>Drop the first stone (${bet} gold)</button>`}<button data-leave>Leave</button></div>
        <div class="small">Arrows or W A S D to move, Up or X to turn (Z the other way), Down to sink faster, Space to drop, P to pause. Each level cleared pays gold, every play; each level's card comes once, the first time it is cleared: ♦ common (1-4), ◆ a stronger one (5-9), ★ rare (10 on).</div>${this.cgStats("runestack")}</div></div></div>`;
      this.cgWireBet(box); const q = (s) => box.querySelector(s); q("[data-leave]").addEventListener("click", () => this.closeDialogs());
      if (q("[data-rsstart]")) q("[data-rsstart]").addEventListener("click", () => { const r = g.rsStart(bet); this.cgNote = r.error || ""; this.rsFx = { rows: null, parts: [], banner: null, shake: 0 }; this.rsPaused = false; this.cgSfx(r.error ? "miss" : "chain", 0.45); this.renderCasino(); const cv = this.$("#casino-body .rscanvas"); if (cv) cv.focus(); });
      if (q("[data-rspause]")) q("[data-rspause]").addEventListener("click", () => { this.rsPaused = !this.rsPaused; this.renderCasino(); });
      if (q("[data-rsquit]")) q("[data-rsquit]").addEventListener("click", () => { const out = g.rsQuit(); this.rsAfter(out || []); });
      this.rsCanvas = q(".rscanvas"); this.rsNextC = q(".rsnext");
      if (!this.rsKeys) { this.rsKeys = (e) => { if (this.cgView !== "runestack" || !this.dialogOpen()) return; const Wl = this.game.rsWell(); if (!Wl) return; const k = e.code;
        const act = { ArrowLeft: () => Wl.move(-1), KeyA: () => Wl.move(-1), ArrowRight: () => Wl.move(1), KeyD: () => Wl.move(1), ArrowDown: () => Wl.soft(), KeyS: () => Wl.soft(), ArrowUp: () => Wl.rotate(1), KeyW: () => Wl.rotate(1), KeyX: () => Wl.rotate(1), KeyZ: () => Wl.rotate(-1), Space: () => Wl.hard(), KeyP: () => { this.rsPaused = !this.rsPaused; this.renderCasino(); } }[k];
        if (!act) return; e.preventDefault(); e.stopPropagation(); if (this.rsPaused && k !== "KeyP") return; act(); };
        window.addEventListener("keydown", this.rsKeys, true); }
      if (!this.rsLoop) { let prev = performance.now(); const loop = (now) => { if (!this.rsCanvas || !this.rsCanvas.isConnected || this.cgView !== "runestack") { this.rsLoop = null; return; } const dt = Math.min(0.05, (now - prev) / 1000); prev = now; this.rsFrame(dt, now); this.rsLoop = requestAnimationFrame(loop); }; this.rsLoop = requestAnimationFrame(loop); }
    },
    // the rules' news, shown and heard
    rsAfter(out) {
      const RS = CM.RS; for (const o of out) {
        if (o.over) { const S = this.game.rsState(), L = S.last; this.cgNote = `The well is full. ${L.lines} lines, level ${L.level}: ${S.won} gold back${L.cards.length ? `, and ${L.cards.length} card${L.cards.length > 1 ? "s" : ""}` : ""}.`; this.cgSfx("cardlose", 0.5); this.rsPaused = false; this.renderCasino(); if (S.won) this.cgCoins(this.$("#casino-body"), Math.min(30, 6 + L.level * 2)); return; }
        (this.rsFx = this.rsFx || { parts: [] }).banner = { at: performance.now(), level: o.level + 1, pay: o.pay, card: o.card, kind: o.kind };
        this.cgSfx("victory", 0.5); this.cgSfx("coin", 0.5); if (o.card) setTimeout(() => this.cgSfx("cardwin", 0.55), 300);
        this.cgNote = `Level ${o.level} cleared: ${o.pay} gold${o.card ? `, and a ${o.kind === "better" ? "stronger " : o.kind === "rare" ? "rare " : ""}card - ${o.card}` : ""}.`; const n = this.$("#casino-body .cgnote"); if (n) n.textContent = this.cgNote;
        const rs = this.$("#casino-body .rsladder"); if (rs) { const W = this.game.rsWell(); this.renderCasino(); void W; }
        void RS;
      }
    },
    rsFrame(dt, now) {
      const g = this.game, RS = CM.RS, W = g.rsWell(), cv = this.rsCanvas, p = cv.getContext("2d"), fx = this.rsFx = this.rsFx || { parts: [] };
      if (W && !this.rsPaused) { W.update(dt); for (const e of W.events.splice(0)) this.rsEvent(e, W, now); const out = g.rsCheck(); if (out.length) this.rsAfter(out); }
      // the well: black water, faint grid
      const bg = p.createLinearGradient(0, 0, 0, RS.H * CELL); bg.addColorStop(0, "#0C1418"); bg.addColorStop(1, "#04080A"); p.fillStyle = bg; p.fillRect(0, 0, cv.width, cv.height);
      p.strokeStyle = "rgba(90,140,160,0.08)"; for (let x = 1; x < RS.W; x++) { p.beginPath(); p.moveTo(x * CELL + 0.5, 0); p.lineTo(x * CELL + 0.5, RS.H * CELL); p.stroke(); } for (let y = 1; y < RS.H; y++) { p.beginPath(); p.moveTo(0, y * CELL + 0.5); p.lineTo(RS.W * CELL, y * CELL + 0.5); p.stroke(); }
      if (!W) { p.fillStyle = "rgba(255,240,200,0.85)"; p.font = "bold 24px Georgia, serif"; p.textAlign = "center"; const S = g.rsState(); p.fillText(S && S.stage === "done" ? "The well is full" : "Runestack", cv.width / 2, cv.height / 2); p.textAlign = "left"; this.rsDrawNext(null); return; }
      const sh = fx.shake > 0 ? (fx.shake -= dt, fx.shake * 18) : 0; p.save(); p.translate(0, sh > 0 ? Math.sin(now / 20) * sh : 0);
      for (let y = 0; y < RS.H; y++) for (let x = 0; x < RS.W; x++) { const k = W.grid[y][x]; if (k) this.rsStone(p, x, y, k, 1, W.clearing && W.clearing.rows.includes(y) ? 1 - W.clearing.t / RS.clearTime : 0); }
      if (W.clearing) for (const y of W.clearing.rows) { const t = 1 - W.clearing.t / RS.clearTime; p.fillStyle = `rgba(255,250,230,${0.85 * Math.sin(t * Math.PI)})`; p.fillRect(0, y * CELL, RS.W * CELL, CELL); }
      if (!W.clearing && W.stage === "play") { const c = W.cur, gy = W.ghost(); for (const [x, y] of W.cells(c.k, c.rot)) if (gy + y >= 0) { p.strokeStyle = CM.RS.COLOUR[c.k]; p.globalAlpha = 0.45; p.lineWidth = 2; p.strokeRect((c.x + x) * CELL + 2.5, (gy + y) * CELL + 2.5, CELL - 5, CELL - 5); p.globalAlpha = 1; }
        const land = W.grounded() ? Math.min(1, W.lockT / RS.lockDelay) : 0; for (const [x, y] of W.cells(c.k, c.rot)) if (c.y + y >= 0) this.rsStone(p, c.x + x, c.y + y, c.k, 1, 0, land); }
      fx.parts = fx.parts.filter((q) => (q.life -= dt) > 0); for (const q of fx.parts) { q.x += q.vx * dt; q.y += q.vy * dt; q.vy += 500 * dt; p.globalAlpha = Math.min(1, q.life * 2); p.fillStyle = q.c; p.fillRect(q.x, q.y, 3, 3); } p.globalAlpha = 1;
      p.restore();
      if (fx.banner && now - fx.banner.at < 2600) { const t = (now - fx.banner.at) / 2600, B = fx.banner, a = t < 0.15 ? t / 0.15 : t > 0.8 ? (1 - t) / 0.2 : 1; p.save(); p.globalAlpha = a; p.fillStyle = "rgba(0,0,0,0.65)"; p.fillRect(0, 210, cv.width, 120); p.fillStyle = "#FFE070"; p.font = "bold 30px Georgia, serif"; p.textAlign = "center"; p.fillText(`Level ${B.level}!`, cv.width / 2, 252); p.font = "15px Georgia, serif"; p.fillStyle = "#F0E0B0"; p.fillText(`+${B.pay} gold`, cv.width / 2, 280); if (B.card) { p.fillStyle = B.kind === "rare" ? "#F0A0FF" : B.kind === "better" ? "#A0E0FF" : "#E8D8B0"; p.fillText(`${CM.CARDS[B.card] ? CM.CARDS[B.card][0] : ""} ${B.card}`, cv.width / 2, 306); } p.restore(); }
      if (this.rsPaused) { p.fillStyle = "rgba(0,0,0,0.6)"; p.fillRect(0, 0, cv.width, cv.height); p.fillStyle = "#FFF"; p.font = "bold 26px Georgia, serif"; p.textAlign = "center"; p.fillText("Paused", cv.width / 2, cv.height / 2); p.textAlign = "left"; }
      const side = cv.closest(".rswrap"); if (side) { const s2 = (c, v) => { const e = side.querySelector(c); if (e && e.textContent !== String(v)) e.textContent = v; }; s2(".rssc", W.score); s2(".rsln", W.lines); s2(".rslv", W.level); s2(".rswon", g.rsState().won); }
      this.rsDrawNext(W);
    },
    rsEvent(e, W, now) {
      const fx = this.rsFx, RS = CM.RS;
      if (e.kind === "move") this.cgSfx("step", 0.12, 1.9); else if (e.kind === "turn") this.cgSfx("card", 0.2, 1.6); else if (e.kind === "lock") this.cgSfx("cardplace", 0.3, 0.8);
      else if (e.kind === "slam") { this.cgSfx("bump", 0.4, 0.9); fx.shake = 0.12; }
      else if (e.kind === "clear") { const n = e.rows.length; this.cgSfx(n >= 4 ? "victory" : "shatter", 0.45 + n * 0.05, 0.9 + n * 0.1); if (n >= 4) fx.shake = 0.3;
        for (const y of e.rows) for (let x = 0; x < RS.W; x++) { const k = W.grid[y][x]; for (let s = 0; s < 3; s++) fx.parts.push({ x: x * CELL + 14, y: y * CELL + 14, vx: (Math.random() - 0.5) * 300, vy: -Math.random() * 260, life: 0.7 + Math.random() * 0.4, c: s ? RS.COLOUR[k] || "#FFF" : "#FFF6D0" }); } }
      else if (e.kind === "over") this.cgSfx("fall", 0.5);
      void now;
    },
    // a stone: cut face, a bevel, a rune; brighter as it sets, whiter as its row is cut
    rsStone(p, x, y, k, a, white = 0, setting = 0) {
      const col = CM.RS.COLOUR[k], X = x * CELL, Y = y * CELL;
      p.fillStyle = col; p.fillRect(X + 1, Y + 1, CELL - 2, CELL - 2);
      p.fillStyle = "rgba(255,255,255,0.35)"; p.fillRect(X + 1, Y + 1, CELL - 2, 4); p.fillRect(X + 1, Y + 1, 4, CELL - 2); p.fillStyle = "rgba(0,0,0,0.35)"; p.fillRect(X + 1, Y + CELL - 5, CELL - 2, 4); p.fillRect(X + CELL - 5, Y + 1, 4, CELL - 2);
      p.strokeStyle = "rgba(0,0,0,0.45)"; p.lineWidth = 1.6; p.beginPath(); const rune = "IOTSZJL".indexOf(k); const m = X + CELL / 2, n = Y + CELL / 2;
      if (rune % 3 === 0) { p.moveTo(m, n - 6); p.lineTo(m, n + 6); p.moveTo(m, n - 6); p.lineTo(m + 5, n - 2); } else if (rune % 3 === 1) { p.moveTo(m - 5, n - 5); p.lineTo(m + 5, n + 5); p.moveTo(m + 5, n - 5); p.lineTo(m - 5, n + 5); } else { p.moveTo(m - 5, n + 5); p.lineTo(m, n - 6); p.lineTo(m + 5, n + 5); }
      p.stroke();
      if (setting) { p.fillStyle = `rgba(255,255,255,${0.25 * setting})`; p.fillRect(X + 1, Y + 1, CELL - 2, CELL - 2); }
      if (white) { p.fillStyle = `rgba(255,255,240,${white})`; p.fillRect(X + 1, Y + 1, CELL - 2, CELL - 2); }
      void a;
    },
    rsDrawNext(W) {
      const cv = this.rsNextC; if (!cv) return; const p = cv.getContext("2d"); p.fillStyle = "#0C1418"; p.fillRect(0, 0, cv.width, cv.height); if (!W) return;
      W.next.forEach((k, i) => { const cells = W.cells(k, 0), s = i ? 16 : 22, minx = Math.min(...cells.map((c) => c[0])), maxx = Math.max(...cells.map((c) => c[0])), miny = Math.min(...cells.map((c) => c[1])), maxy = Math.max(...cells.map((c) => c[1])), ox = 48 - ((maxx - minx + 1) * s) / 2 - minx * s, oy = (i ? 90 + (i - 1) * 70 : 18) + 26 - ((maxy - miny + 1) * s) / 2 - miny * s;
        for (const [x, y] of cells) { p.fillStyle = CM.RS.COLOUR[k]; p.fillRect(ox + x * s + 1, oy + y * s + 1, s - 2, s - 2); p.fillStyle = "rgba(255,255,255,0.3)"; p.fillRect(ox + x * s + 1, oy + y * s + 1, s - 2, 3); } });
    },
  });
}
