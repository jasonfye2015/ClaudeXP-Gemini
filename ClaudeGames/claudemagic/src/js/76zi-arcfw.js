"use strict";
// The arcade cabinets' common window (the forty-second big update): each registered cabinet's table is laid out the
// same way - its canvas in a cabinet frame on the left, the ladder of levels (gold, and the card levels marked), the lore,
// the stake, the buttons and the help on the right - and run by the same loop: the keys held and pressed and the mouse
// passed to the rules, the rules stepped, their events turned into sound and sparks by the cabinet, the house's terms
// checked, a banner for each level cleared and a note at the end. The cabinet draws only its own play: the bar of
// score, level and lives across the top, the banner, the pause and the sparks and floating points are drawn here.
{ const floor0 = CM.UI.prototype.renderFloor, TOP = 28;
  Object.assign(CM.UI.prototype, {
    renderFloor(box) { if (CM.ARC.reg[this.cgView]) return this.arcTable(box, this.cgView); return floor0.call(this, box); },
    arcTable(box, id) {
      const g = this.game, def = CM.ARC.reg[id], U = def.ui, S = g.arcState(id), L = g.arcLevel(id), live = !!L, bet = live ? S.bet : (this.cgBet === undefined ? 5 : this.cgBet), Cl = g.arcClaimed(id), last = S && S.stage === "done" ? S.last : null;
      const top = Math.max(15, (S && live ? S.n : 1) + 4), rows = []; for (let n = 1; n <= top; n++) { const card = n % def.cardEvery === 0, tier = CM.cardTierFor(n); rows.push(`<div class="rung${live && S.n === n ? " now" : ""}${live && S.n > n ? " done" : ""}"><span>${U.levelWord || "Level"} ${n}</span><b>${Math.round(bet * def.pay(n))}</b><i class="${!card ? "" : Cl[n] ? "got" : tier}" title="${!card ? "" : Cl[n] ? "card already won" : `a ${tier === "better" ? "stronger common" : tier} card, the first time`}">${!card ? "" : Cl[n] ? "✓" : tier === "rare" ? "★" : tier === "better" ? "◆" : "♦"}</i></div>`); }
      box.innerHTML = `<div class="cgtable arcfw ${id} runestack dash"><h3>${def.name}</h3><div class="rswrap"><div class="arccab" style="--c1:${U.frame || "#3A2A18"}"><canvas class="arccanvas" width="${U.W}" height="${U.H + TOP}" tabindex="0" style="width:${U.W * (U.scale || 1)}px;height:${(U.H + TOP) * (U.scale || 1)}px"></canvas></div>
        <div class="dashside"><p class="lore">${U.lore}</p>
        <div class="ladder rsladder">${rows.reverse().join("")}</div>
        ${live ? "" : this.cgBetRow("The stake")}<div class="cgnote">${this.cgNote || ""}</div>${last && last.cards && last.cards.length ? last.cards.map((c) => this.cgCardWon(c)).join("") : ""}
        <div class="row">${live ? `<button data-arcpause>${this.arcPaused ? "Go on" : "Pause"}</button>` : `<button class="primary" data-arcstart>${U.start || "Insert"} (${bet} gold)</button>`}<button data-leave>Leave</button></div>
        <div class="small">${U.help} P to pause. Each ${(U.levelWord || "level").toLowerCase()} cleared pays gold, more each, every game, and as many prize tickets as its number; every third gives a card the first time ever (♦ to the 4th, ◆ to the 9th, ★ from the 10th). Best score ${(g.cgStore()[`ar_${id}_best`] || 0).toLocaleString("en")}.</div>${this.cgStats(id)}</div></div></div>`;
      this.cgWireBet(box); const q = (s) => box.querySelector(s); q("[data-leave]").addEventListener("click", () => this.closeDialogs());
      if (q("[data-arcstart]")) q("[data-arcstart]").addEventListener("click", () => { const r = g.arcStart(id, bet); this.cgNote = r.error || U.go || "Level 1!"; this.arcFx = { parts: [], pts: [], banner: r.error ? null : { at: performance.now(), text: `${(U.levelWord || "Level").toUpperCase()} 1` }, shake: 0 }; this.arcPaused = false; this.cgSfx(r.error ? "miss" : "door", 0.45); this.renderCasino(); const cv = this.$("#casino-body .arccanvas"); if (cv) cv.focus(); });
      if (q("[data-arcpause]")) q("[data-arcpause]").addEventListener("click", () => { this.arcPaused = !this.arcPaused; this.renderCasino(); });
      const cv = this.arcCanvas = q(".arccanvas"); this.arcId = id;
      const pos = (e) => { const r = cv.getBoundingClientRect(); return [((e.clientX - r.left) / r.width) * U.W, ((e.clientY - r.top) / r.height) * (U.H + TOP) - TOP]; };
      cv.addEventListener("mousemove", (e) => { this.arcMouse = pos(e); });
      cv.addEventListener("mousedown", (e) => { const Lm = g.arcLevel(id); this.arcMouseDown = true; if (Lm && !this.arcPaused && def.click) def.click(Lm, ...pos(e), this); cv.focus(); });
      cv.addEventListener("mouseup", (e) => { const Lm = g.arcLevel(id); this.arcMouseDown = false; if (Lm && !this.arcPaused && def.release) def.release(Lm, ...pos(e), this); });
      cv.addEventListener("contextmenu", (e) => e.preventDefault());
      if (!this.arcKeys) { this.arcHeld = new Set();
        this.arcKeys = (e) => { const id2 = this.arcId, d2 = CM.ARC.reg[id2]; if (!d2 || this.cgView !== id2 || !this.dialogOpen() || !this.game.arcLevel(id2)) return; if (e.type === "keydown" && e.code === "KeyP") { e.preventDefault(); this.arcPaused = !this.arcPaused; this.renderCasino(); return; }
          if (!(d2.ui.keys || []).includes(e.code)) return; e.preventDefault(); e.stopPropagation();
          if (e.type === "keydown") { if (!e.repeat && d2.press && !this.arcPaused) d2.press(this.game.arcLevel(id2), e.code, this); this.arcHeld.add(e.code); } else this.arcHeld.delete(e.code); };
        window.addEventListener("keydown", this.arcKeys, true); window.addEventListener("keyup", this.arcKeys, true); }
      if (!this.arcLoop) { let prev = performance.now(); const loop = (now) => { if (!this.arcCanvas || !this.arcCanvas.isConnected || !CM.ARC.reg[this.cgView]) { this.arcLoop = null; return; } const dt = Math.min(0.05, (now - prev) / 1000); prev = now; this.arcFrame(dt, now); this.arcLoop = requestAnimationFrame(loop); }; this.arcLoop = requestAnimationFrame(loop); }
    },
    arcFrame(dt, now) {
      const g = this.game, id = this.arcId, def = CM.ARC.reg[id], U = def.ui, L = g.arcLevel(id), cv = this.arcCanvas, p = cv.getContext("2d"), fx = this.arcFx = this.arcFx || { parts: [], pts: [], shake: 0 };
      if (L && !this.arcPaused) { if (def.input) def.input(L, this.arcHeld || new Set(), this); L.update(dt); for (const e of L.events.splice(0)) def.event && def.event(this, e, now, L, fx);
        const out = g.arcCheck(id);
        if (out && out.cleared) { fx.banner = { at: now, text: `${(U.levelWord || "Level").toUpperCase()} ${out.cleared + 1}`, sub: `${U.levelWord || "Level"} ${out.cleared} cleared: +${out.pay} gold, +${out.tickets} tickets${out.card ? ` - ${out.card}` : ""}` }; this.cgSfx("victory", 0.5); if (out.card) setTimeout(() => this.cgSfx("cardwin", 0.5), 300); this.cgNote = `${U.levelWord || "Level"} ${out.cleared} cleared: ${out.pay} gold and ${out.tickets} tickets${out.card ? `, and a card - ${out.card}` : ""}.`; this.renderCasino(); return; }
        if (out && out.over) { const S = g.arcState(id); this.cgNote = `${U.over || "Game over"} on ${(U.levelWord || "level").toLowerCase()} ${S.last.level}: ${S.last.score.toLocaleString("en")} points, ${S.won} gold back${S.last.cards.length ? `, and ${S.last.cards.length} card${S.last.cards.length > 1 ? "s" : ""}` : ""}.`; this.cgSfx("cardlose", 0.5); this.renderCasino(); if (S.won) this.cgCoins(this.$("#casino-body"), 12); return; } }
      const Lv = L || (this.arcLastDrawn && this.arcLastDrawn.__id === id ? this.arcLastDrawn : null); if (L) { this.arcLastDrawn = L; L.__id = id; }
      p.save(); if (fx.shake > 0) { fx.shake -= dt; p.translate((Math.random() - 0.5) * fx.shake * 24, (Math.random() - 0.5) * fx.shake * 24); }
      p.save(); p.translate(0, TOP); def.draw(p, Lv, now, dt, this, fx); p.restore();
      p.save(); p.translate(0, TOP);
      fx.parts = fx.parts.filter((q) => (q.life -= dt) > 0); for (const q of fx.parts) { q.x += q.vx * dt; q.y += q.vy * dt; q.vy += (q.g === undefined ? 300 : q.g) * dt; p.globalAlpha = Math.min(1, q.life * 2.5); p.fillStyle = q.c; p.fillRect(q.x - (q.s || 3) / 2, q.y - (q.s || 3) / 2, q.s || 3, q.s || 3); } p.globalAlpha = 1;
      fx.pts = fx.pts.filter((q) => now - q.at < 900); for (const q of fx.pts) { p.globalAlpha = 1 - (now - q.at) / 900; p.fillStyle = q.c || "#FFF0B0"; p.font = "bold 12px monospace"; p.textAlign = "center"; p.fillText(String(q.n), q.x, q.y - (now - q.at) / 35); p.textAlign = "left"; } p.globalAlpha = 1;
      p.restore(); p.restore();
      // the bar
      p.fillStyle = "#0E0A14"; p.fillRect(0, 0, cv.width, TOP); p.fillStyle = "#FFE070"; p.font = "bold 14px monospace"; p.fillText(Lv ? `SCORE ${Lv.score.toLocaleString("en")}` : def.name.toUpperCase(), 8, 19);
      if (Lv) { p.textAlign = "center"; p.fillText(`${(U.levelWord || "Level").toUpperCase()} ${Lv.n}`, cv.width / 2, 19); p.textAlign = "left"; if (U.extraHud) U.extraHud(p, Lv, cv.width, now); else for (let k = 0; k < Math.min(6, Lv.lives || 0); k++) { const x = cv.width - 14 - k * 18; if (def.lifeIcon) def.lifeIcon(p, x, 14, now); else { p.fillStyle = "#80E0FF"; p.beginPath(); p.arc(x, 14, 5, 0, Math.PI * 2); p.fill(); } } }
      if (!Lv) { p.fillStyle = "rgba(0,0,0,0.45)"; p.fillRect(0, TOP, cv.width, cv.height - TOP); p.fillStyle = "rgba(255,240,200,0.92)"; p.font = "bold 26px Georgia, serif"; p.textAlign = "center"; p.fillText(def.name, cv.width / 2, cv.height / 2); if (Math.floor(now / 600) % 2) { p.font = "13px Georgia, serif"; p.fillText("Set a stake and begin", cv.width / 2, cv.height / 2 + 26); } p.textAlign = "left"; }
      if (fx.banner && now - fx.banner.at < 2600) { const B = fx.banner, t = (now - B.at) / 2600; p.globalAlpha = t > 0.8 ? (1 - t) / 0.2 : Math.min(1, t * 8); p.fillStyle = "rgba(0,0,0,0.6)"; p.fillRect(0, cv.height / 2 - 46, cv.width, 92); p.fillStyle = "#FFE070"; p.font = "bold 26px Georgia, serif"; p.textAlign = "center"; p.fillText(B.text, cv.width / 2, cv.height / 2 + 12 + (B.sub ? 14 : 0)); if (B.sub) { p.font = "13px Georgia, serif"; p.fillStyle = "#F0E0B0"; p.fillText(B.sub, cv.width / 2, cv.height / 2 - 14); } p.textAlign = "left"; p.globalAlpha = 1; }
      if (this.arcPaused) { p.fillStyle = "rgba(0,0,0,0.6)"; p.fillRect(0, 0, cv.width, cv.height); p.fillStyle = "#FFF"; p.font = "bold 26px Georgia, serif"; p.textAlign = "center"; p.fillText("Paused", cv.width / 2, cv.height / 2); p.textAlign = "left"; }
    },
    // sparks and points, for the cabinets
    arcBurst(fx, x, y, cols, n = 14, sp = 140, g = 300) { for (let k = 0; k < n; k++) { const a = Math.random() * Math.PI * 2, v = sp * (0.3 + Math.random() * 0.7); fx.parts.push({ x, y, vx: Math.cos(a) * v, vy: Math.sin(a) * v - sp * 0.3, life: 0.4 + Math.random() * 0.4, c: cols[k % cols.length], g }); } },
    arcPts(fx, x, y, n, c) { fx.pts.push({ x, y, n, at: performance.now(), c }); },
  });
}
