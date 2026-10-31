"use strict";
// Shatterpane, the window's side (the thirty-second big update): the old chapel window on a canvas - candlelight behind
// it showing through where panes are gone, panes of stained glass in six tints (darker and with a cross-hatch the more
// hits they take, cracks once struck), lead frames with rivets, the glass-slipper paddle with its gold trim (wider,
// shimmering when sticky), the mana orb and its trail, falling charms with their marks, shards; the score, the lives
// and the level at the top. The mouse over the window or left and right (A and D) to move; a click or Space to let fly;
// P to pause. The rules are 64zi-pane.js.
CM.CG_TABLES.push(["shatterpane", "Shatterpane"]);
{ const floor0 = CM.UI.prototype.renderFloor, C = 17, TOP = 28;
  const TINT = [[200, 60, 70], [60, 110, 210], [230, 180, 60], [70, 170, 100], [150, 80, 190], [60, 180, 190]], MARK = { wide: "W", multi: "3", slow: "S", sticky: "C", life: "♥" }, CCOL = { wide: "#60A0F0", multi: "#F0A040", slow: "#80D080", sticky: "#C080F0", life: "#F06080" };
  Object.assign(CM.UI.prototype, {
    renderFloor(box) { if (this.cgView === "shatterpane") return this.cgPane(box); return floor0.call(this, box); },
    cgPane(box) {
      const g = this.game, PN = CM.PN, S = g.pnState(), L = g.pnLevel(), live = !!L, bet = live ? S.bet : (this.cgBet === undefined ? 5 : this.cgBet), Cl = g.pnClaimed(), last = S && S.stage === "done" ? S.last : null;
      const top = Math.max(15, (S && live ? S.n : 1) + 4), rows = []; for (let n = 1; n <= top; n++) { const card = n % PN.cardEvery === 0, tier = CM.cardTierFor(n); rows.push(`<div class="rung${live && S.n === n ? " now" : ""}${live && S.n > n ? " done" : ""}"><span>Level ${n}</span><b>${Math.round(bet * PN.pay(n))}</b><i class="${!card ? "" : Cl[n] ? "got" : tier}" title="${!card ? "" : Cl[n] ? "card already won" : `a ${tier === "better" ? "stronger common" : tier} card, the first time`}">${!card ? "" : Cl[n] ? "✓" : tier === "rare" ? "★" : tier === "better" ? "◆" : "♦"}</i></div>`); }
      box.innerHTML = `<div class="cgtable shatterpane runestack dash"><h3>Shatterpane</h3><div class="rswrap"><canvas class="pncanvas" width="${PN.W * C}" height="${PN.H * C + TOP}" tabindex="0"></canvas>
        <div class="dashside"><p class="lore">The house bought a ruined chapel's windows by the cartload and set them up in the back room, one after another. "They're to be broken," says the attendant, handing over a glass slipper the size of a plank. "Every last pane. The house pays by the window."</p>
        <div class="ladder rsladder">${rows.reverse().join("")}</div>
        ${live ? "" : this.cgBetRow("The stake")}<div class="cgnote">${this.cgNote || ""}</div>${last && last.cards && last.cards.length ? last.cards.map((c) => this.cgCardWon(c)).join("") : ""}
        <div class="row">${live ? `<button data-pnpause>${this.pnPaused ? "Go on" : "Pause"}</button>` : `<button class="primary" data-pnstart>To the window (${bet} gold)</button>`}<button data-leave>Leave</button></div>
        <div class="small">Move the mouse over the window (or left and right, A and D) to slide the slipper; click or press Space to let the orb fly; P to pause. Where the orb strikes the slipper sets its angle. Tinted panes take two hits, the darkest three; lead frames never break - though if nothing breaks for a while a guiding light bends the orb toward a pane, and later the lead crumbles. Charms: W a wider slipper, 3 two more orbs, S a slower orb, C a sticky slipper (click to let go), ♥ a life. Three lives. Each level cleared pays gold, more each, every play; every third level gives a card the first time ever (♦ level 3, ◆ 6 and 9, ★ from 12). Best score ${g.cgStore().pnBest || 0}.</div>${this.cgStats("shatterpane")}</div></div></div>`;
      this.cgWireBet(box); const q = (s) => box.querySelector(s); q("[data-leave]").addEventListener("click", () => this.closeDialogs());
      if (q("[data-pnstart]")) q("[data-pnstart]").addEventListener("click", () => { const r = g.pnStart(bet); this.cgNote = r.error || "Level 1. Click to let fly!"; this.pnFx = { parts: [], pts: [], banner: { at: performance.now(), text: "LEVEL 1" } }; this.pnPaused = false; this.pnMouse = null; this.cgSfx(r.error ? "miss" : "door", 0.45); this.renderCasino(); const cv = this.$("#casino-body .pncanvas"); if (cv) cv.focus(); });
      if (q("[data-pnpause]")) q("[data-pnpause]").addEventListener("click", () => { this.pnPaused = !this.pnPaused; this.renderCasino(); });
      const cv = this.pnCanvas = q(".pncanvas");
      cv.addEventListener("mousemove", (e) => { const r = cv.getBoundingClientRect(); this.pnMouse = ((e.clientX - r.left) / r.width) * PN.W; });
      cv.addEventListener("mousedown", () => { this.pnLaunch = true; cv.focus(); });
      if (!this.pnKeys) { this.pnHeld = new Set();
        this.pnKeys = (e) => { if (this.cgView !== "shatterpane" || !this.dialogOpen() || !this.game.pnLevel()) return; if (e.type === "keydown" && e.code === "KeyP") { e.preventDefault(); this.pnPaused = !this.pnPaused; this.renderCasino(); return; }
          if (e.code === "Space") { e.preventDefault(); e.stopPropagation(); if (e.type === "keydown") this.pnLaunch = true; return; }
          const k = { ArrowLeft: "l", KeyA: "l", ArrowRight: "r", KeyD: "r" }[e.code]; if (!k) return; e.preventDefault(); e.stopPropagation(); this.pnMouse = null; if (e.type === "keydown") this.pnHeld.add(k); else this.pnHeld.delete(k); };
        window.addEventListener("keydown", this.pnKeys, true); window.addEventListener("keyup", this.pnKeys, true); }
      if (!this.pnLoop) { let prev = performance.now(); const loop = (now) => { if (!this.pnCanvas || !this.pnCanvas.isConnected || this.cgView !== "shatterpane") { this.pnLoop = null; return; } const dt = Math.min(0.05, (now - prev) / 1000); prev = now; this.pnFrame(dt, now); this.pnLoop = requestAnimationFrame(loop); }; this.pnLoop = requestAnimationFrame(loop); }
    },
    pnFrame(dt, now) {
      const g = this.game, PN = CM.PN, L = g.pnLevel(), cv = this.pnCanvas, p = cv.getContext("2d"), fx = this.pnFx = this.pnFx || { parts: [], pts: [] }, H = this.pnHeld || new Set();
      if (L && !this.pnPaused) { L.input((H.has("r") ? 1 : 0) - (H.has("l") ? 1 : 0), this.pnLaunch, this.pnMouse === null || this.pnMouse === undefined ? undefined : this.pnMouse); this.pnLaunch = false; L.update(dt); for (const e of L.events.splice(0)) this.pnEvent(e, now, L); const out = g.pnCheck();
        if (out && out.cleared) { fx.banner = { at: now, text: `LEVEL ${out.cleared + 1}`, sub: `Level ${out.cleared} cleared: +${out.pay} gold${out.card ? ` - ${out.card}` : ""}` }; this.cgSfx("victory", 0.5); if (out.card) setTimeout(() => this.cgSfx("cardwin", 0.5), 300); this.cgNote = `Level ${out.cleared} cleared: ${out.pay} gold${out.card ? `, and a card - ${out.card}` : ""}.`; this.renderCasino(); return; }
        if (out && out.over) { const S = g.pnState(); this.cgNote = `The last orb falls on level ${S.last.level}. ${S.won} gold back${S.last.cards.length ? `, and ${S.last.cards.length} card${S.last.cards.length > 1 ? "s" : ""}` : ""}.`; this.cgSfx("cardlose", 0.5); this.renderCasino(); if (S.won) this.cgCoins(this.$("#casino-body"), 12); return; } }
      const Lv = L || this.pnLastDrawn; if (L) this.pnLastDrawn = L;
      // the room and the candlelight behind the window
      p.fillStyle = "#120E0C"; p.fillRect(0, 0, cv.width, cv.height);
      p.fillStyle = "#1A1410"; p.fillRect(0, 0, cv.width, TOP); p.fillStyle = "#FFE070"; p.font = "bold 14px monospace"; p.fillText(Lv ? `SCORE ${Lv.score}` : "SHATTERPANE", 8, 19);
      if (Lv) { p.fillText(`LEVEL ${Lv.n}`, cv.width / 2 - 30, 19); for (let k = 0; k < Math.min(6, Lv.lives); k++) { p.fillStyle = "#80E0FF"; p.beginPath(); p.arc(cv.width - 14 - k * 16, 14, 5, 0, Math.PI * 2); p.fill(); } }
      if (!Lv) { p.fillStyle = "rgba(255,240,200,0.9)"; p.font = "bold 24px Georgia, serif"; p.textAlign = "center"; p.fillText("Shatterpane", cv.width / 2, cv.height / 2); p.textAlign = "left"; return; }
      p.save(); p.translate(0, TOP);
      const wy = PN.top * C, wh = Lv.grid.length * PN.bh * C, glow = p.createRadialGradient(cv.width / 2, wy + wh / 2, 10, cv.width / 2, wy + wh / 2, cv.width * 0.7); glow.addColorStop(0, "rgba(255,210,140,0.35)"); glow.addColorStop(1, "rgba(255,210,140,0.03)"); p.fillStyle = glow; p.fillRect(0, wy - 8, cv.width, wh + 16);
      p.strokeStyle = "#3A2C20"; p.lineWidth = 6; p.strokeRect(3, wy - 6, cv.width - 6, wh + 12); p.lineWidth = 1;
      for (let gy = 0; gy < Lv.grid.length; gy++) for (let gx = 0; gx < PN.cols; gx++) { const v = Lv.grid[gy][gx]; if (!v) continue; const X = gx * PN.bw * C, Y = (PN.top + gy * PN.bh) * C, w = PN.bw * C, h = PN.bh * C;
        if (v === 9) { p.fillStyle = "#3A3A44"; p.fillRect(X + 1, Y + 1, w - 2, h - 2); p.fillStyle = "#6A6A78"; p.fillRect(X + 1, Y + 1, w - 2, 2); p.fillStyle = "#9090A0"; p.fillRect(X + 4, Y + h / 2 - 1, 2, 2); p.fillRect(X + w - 6, Y + h / 2 - 1, 2, 2); continue; }
        const [r, gg, b] = TINT[Lv.tints[gy][gx]], dk = v === 3 ? 0.55 : v === 2 ? 0.75 : 1; p.fillStyle = `rgba(${Math.round(r * dk)},${Math.round(gg * dk)},${Math.round(b * dk)},0.92)`; p.fillRect(X + 1, Y + 1, w - 2, h - 2);
        p.fillStyle = "rgba(255,255,255,0.28)"; p.fillRect(X + 2, Y + 2, w * 0.4, 2); p.strokeStyle = "#1A1410"; p.strokeRect(X + 0.5, Y + 0.5, w - 1, h - 1);
        if (v >= 2) { p.strokeStyle = "rgba(0,0,0,0.3)"; p.beginPath(); for (let k = 4; k < w; k += 6) { p.moveTo(X + k, Y + 1); p.lineTo(X + k - 4, Y + h - 1); } p.stroke(); }
        if (Lv.cracked && Lv.cracked[`${gx},${gy}`]) { p.strokeStyle = "rgba(255,255,255,0.7)"; p.beginPath(); p.moveTo(X + w * 0.3, Y + 2); p.lineTo(X + w * 0.5, Y + h * 0.6); p.lineTo(X + w * 0.75, Y + h - 2); p.moveTo(X + w * 0.5, Y + h * 0.6); p.lineTo(X + w * 0.2, Y + h - 3); p.stroke(); } }
      for (const c of Lv.charms) { const X = c.x * C, Y = c.y * C; p.fillStyle = CCOL[c.kind]; p.beginPath(); p.ellipse(X, Y, 13, 7, 0, 0, Math.PI * 2); p.fill(); p.strokeStyle = "#FFF4D0"; p.stroke(); p.fillStyle = "#1A1410"; p.font = "bold 11px monospace"; p.textAlign = "center"; p.fillText(MARK[c.kind], X, Y + 4); p.textAlign = "left"; }
      const P = Lv.pad, px = P.x * C, py = PN.padY * C, pw = P.w * C; p.save(); if (P.stickyT > 0) { p.shadowColor = "#C080F0"; p.shadowBlur = 10 + 4 * Math.sin(now / 100); } const pg = p.createLinearGradient(0, py - 5, 0, py + 6); pg.addColorStop(0, "#E8F8FF"); pg.addColorStop(1, "#80B8D8"); p.fillStyle = pg;
      p.beginPath(); p.moveTo(px - pw / 2 + 4, py - 5); p.lineTo(px + pw / 2 - 4, py - 5); p.quadraticCurveTo(px + pw / 2 + 2, py, px + pw / 2 - 4, py + 6); p.lineTo(px - pw / 2 + 4, py + 6); p.quadraticCurveTo(px - pw / 2 - 2, py, px - pw / 2 + 4, py - 5); p.fill(); p.restore();
      p.fillStyle = "#E0B040"; p.fillRect(px - pw / 2 + 4, py + 4, pw - 8, 2); p.fillStyle = "rgba(255,255,255,0.6)"; p.fillRect(px - pw / 4, py - 4, pw / 3, 1.5);
      for (const b of Lv.balls) { const X = b.x * C, Y = b.y * C; b.trail = b.trail || []; if (!this.pnPaused) { b.trail.push([X, Y]); if (b.trail.length > 8) b.trail.shift(); } b.trail.forEach(([tx, ty], k) => { p.fillStyle = `rgba(128,224,255,${(k / b.trail.length) * 0.35})`; p.beginPath(); p.arc(tx, ty, PN.r * C * (0.5 + k / 16), 0, Math.PI * 2); p.fill(); });
        p.save(); p.shadowColor = Lv.since > PN.guideAfter ? "#FFE070" : "#80E0FF"; p.shadowBlur = 12; p.fillStyle = "#E0FAFF"; p.beginPath(); p.arc(X, Y, PN.r * C + 1, 0, Math.PI * 2); p.fill(); p.restore(); }
      if (Lv.slowT > 0) { p.fillStyle = "rgba(128,208,128,0.6)"; p.fillRect(4, PN.H * C - 6, (Lv.slowT / PN.slow) * 80, 3); }
      fx.parts = fx.parts.filter((q) => (q.life -= dt) > 0); for (const q of fx.parts) { q.x += q.vx * dt; q.y += q.vy * dt; q.vy += 400 * dt; q.rot += dt * 8; p.save(); p.translate(q.x, q.y); p.rotate(q.rot); p.globalAlpha = Math.min(1, q.life * 2); p.fillStyle = q.c; p.beginPath(); p.moveTo(-3, -2); p.lineTo(3, -1); p.lineTo(0, 3); p.closePath(); p.fill(); p.restore(); }
      fx.pts = fx.pts.filter((q) => now - q.at < 700); for (const q of fx.pts) { p.globalAlpha = 1 - (now - q.at) / 700; p.fillStyle = "#FFF0B0"; p.font = "bold 11px monospace"; p.fillText(String(q.n), q.x, q.y - (now - q.at) / 40); } p.globalAlpha = 1;
      p.restore();
      if (fx.banner && now - fx.banner.at < 2600) { const B = fx.banner, t = (now - B.at) / 2600; p.globalAlpha = t > 0.8 ? (1 - t) / 0.2 : 1; p.fillStyle = "#FFE0A0"; p.font = "bold 26px Georgia, serif"; p.textAlign = "center"; p.fillText(B.text, cv.width / 2, cv.height / 2 + 60); if (B.sub) { p.font = "14px Georgia, serif"; p.fillStyle = "#F0E0B0"; p.fillText(B.sub, cv.width / 2, cv.height / 2 + 26); } p.textAlign = "left"; p.globalAlpha = 1; }
      if (Lv.balls.some((b) => !b.vx && !b.vy) && !this.pnPaused) { p.fillStyle = "rgba(255,240,200,0.8)"; p.font = "13px Georgia, serif"; p.textAlign = "center"; p.fillText("Click or Space to let fly", cv.width / 2, cv.height - 40); p.textAlign = "left"; }
      if (this.pnPaused) { p.fillStyle = "rgba(0,0,0,0.6)"; p.fillRect(0, 0, cv.width, cv.height); p.fillStyle = "#FFF"; p.font = "bold 26px Georgia, serif"; p.textAlign = "center"; p.fillText("Paused", cv.width / 2, cv.height / 2); p.textAlign = "left"; }
    },
    pnEvent(e, now, L) {
      const fx = this.pnFx, PN = CM.PN;
      if (e.kind === "break") { const [r, g, b] = TINT[e.tint], X = (e.gx + 0.5) * PN.bw * C, Y = (PN.top + (e.gy + 0.5) * PN.bh) * C; this.cgSfx("shatter", 0.3, 1.2 + Math.random() * 0.4); for (let k = 0; k < 10; k++) fx.parts.push({ x: X, y: Y, vx: (Math.random() - 0.5) * 160, vy: -Math.random() * 120, life: 0.7, rot: Math.random() * 6, c: `rgb(${r},${g},${b})` }); fx.pts.push({ x: X - 8, y: Y, n: e.pts, at: now }); if (L.cracked) delete L.cracked[`${e.gx},${e.gy}`]; }
      else if (e.kind === "crack") { (L.cracked = L.cracked || {})[`${e.gx},${e.gy}`] = true; this.cgSfx("card", 0.35, 1.6); }
      else if (e.kind === "lead") this.cgSfx("bump", 0.3, 1.2); else if (e.kind === "paddle") this.cgSfx("bump", 0.3, 0.9); else if (e.kind === "wall") this.cgSfx("bump", 0.12, 1.5); else if (e.kind === "launch") this.cgSfx("zap", 0.3, 1.4);
      else if (e.kind === "charm") { this.cgSfx(e.charm === "life" ? "cardwin" : "spell", 0.45); fx.banner = { at: now, text: { wide: "WIDE SLIPPER", multi: "THREE ORBS", slow: "SLOW ORB", sticky: "STICKY SLIPPER", life: "ONE MORE LIFE" }[e.charm] }; }
      else if (e.kind === "guide") this.cgSfx("spell", 0.25, 1.8); else if (e.kind === "leadfall") { this.cgSfx("grind", 0.5, 0.8); fx.banner = { at: now, text: "THE LEAD CRUMBLES" }; }
      else if (e.kind === "die") this.cgSfx("hurt", 0.55);
    },
  });
}
