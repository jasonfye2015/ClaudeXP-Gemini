"use strict";
// Wyrmhold Pinball, the window's side (the thirty-seventh big update): the table on a canvas - a painted playfield of
// dungeon flagstones with a dragon's shadow, metal rails, red rubber slingshots that flash when they kick, the R U N E S
// targets (lit letters standing, dark slots when down), rune bumpers that flare, the three stars, the Hoard Hole's
// golden glow, the kickback's arrow, the dragon with its eyes and the pips of its strength, the flippers, the plunger
// and its spring, the ball with its shine; the score, the ball, the multiplier and the marks passed. Z or Left Shift
// (or the left arrow) for the left flipper, / or Right Shift (or the right arrow) for the right; hold Space (or down) to
// draw the plunger and let go to fire. The buttons under the table do the same with the mouse. The rules are
// 64zn-pinball.js.
CM.CG_TABLES.push(["pinball", "Wyrmhold Pinball"]);
{ const floor0 = CM.UI.prototype.renderFloor, K = 16, TOP = 30;
  Object.assign(CM.UI.prototype, {
    renderFloor(box) { if (this.cgView === "pinball") return this.cgPinball(box); return floor0.call(this, box); },
    cgPinball(box) {
      const g = this.game, PB = CM.PB, S = g.pbState(), G = g.pbGame(), live = !!G, bet = live ? S.bet : (this.cgBet === undefined ? 5 : this.cgBet), Cl = g.pbClaimed(), last = S && S.stage === "done" ? S.last : null, passed = live ? G.marks : 0;
      const rows = PB.MARKS.map((m, k) => { const i = k + 1, tier = CM.cardTierFor(i); return `<div class="rung${live && passed === k ? " now" : ""}${live && passed > k ? " done" : ""}"><span>${m.toLocaleString("en")}</span><b>${Math.round(bet * PB.pay(i))}</b><i class="${Cl[i] ? "got" : tier}" title="${Cl[i] ? "card already won" : `a ${tier === "better" ? "stronger common" : tier} card, the first time`}">${Cl[i] ? "✓" : tier === "rare" ? "★" : tier === "better" ? "◆" : "♦"}</i></div>`; });
      box.innerHTML = `<div class="cgtable pinball runestack dash"><h3>Wyrmhold Pinball</h3><div class="rswrap"><div class="pbcol"><canvas class="pbcanvas" width="${PB.W * K}" height="${PB.H * K + TOP}" tabindex="0"></canvas>
        <div class="row pbbtns"><button data-pbflip="0">◀ Flip</button><button data-pbplunge>Plunger (hold)</button><button data-pbflip="1">Flip ▶</button></div></div>
        <div class="dashside"><p class="lore">In the corner of the Joker stands a pinball table painted with the dungeon itself - its flagstones, its runes, and at the top a dragon who does not like being hit. "Three balls," says the attendant. "The house pays at every mark you pass."</p>
        <div class="ladder rsladder">${rows.reverse().join("")}</div>
        ${live ? "" : this.cgBetRow("The stake")}<div class="cgnote">${this.cgNote || ""}</div>${last && last.cards && last.cards.length ? last.cards.map((c) => this.cgCardWon(c)).join("") : ""}
        <div class="row">${live ? "" : `<button class="primary" data-pbstart>Insert ${bet} gold</button>`}<button data-leave>Leave</button></div>
        <div class="small">Left flipper: Z, Left Shift or ←. Right flipper: /, Right Shift or →. Hold Space (or ↓) to draw the plunger back, let go to fire. Rune bumpers 100 (200 with all three stars lit), slingshots 10, R U N E S targets 500 each and 5,000 times the multiplier for the bank (and the multiplier goes up), stars 250, the Hoard Hole 5,000, each hit on the dragon 1,000 and 25,000 times its level to slay it - which starts a three-ball multiball, and every second dragon gives an extra ball. The kickback in the left outlane is lit for each ball and by all three stars. A ball lost in its first seconds is given back once. At the end of a ball its bonus is paid times the multiplier. Every mark the score passes pays gold, every game; the first time ever, a card (♦ to the 4th mark, ◆ to the 9th, ★ beyond). Best score ${(g.cgStore().pbBest || 0).toLocaleString("en")}.</div>${this.cgStats("pinball")}</div></div></div>`;
      this.cgWireBet(box); const q = (s) => box.querySelector(s); q("[data-leave]").addEventListener("click", () => this.closeDialogs());
      if (q("[data-pbstart]")) q("[data-pbstart]").addEventListener("click", () => { const r = g.pbStart(bet); this.cgNote = r.error || "Hold Space to draw the plunger…"; this.pbFx = { flash: {}, pts: [] }; this.cgSfx(r.error ? "miss" : "coin", 0.45); this.renderCasino(); const cv = this.$("#casino-body .pbcanvas"); if (cv) cv.focus(); });
      this.pbHeld = this.pbHeld || { l: false, r: false, p: false };
      box.querySelectorAll("[data-pbflip]").forEach((b) => { const k = b.dataset.pbflip === "0" ? "l" : "r", set = (v) => { this.pbHeld[k] = v; }; b.addEventListener("mousedown", () => set(true)); b.addEventListener("mouseup", () => set(false)); b.addEventListener("mouseleave", () => set(false)); b.addEventListener("touchstart", (e) => { e.preventDefault(); set(true); }); b.addEventListener("touchend", () => set(false)); });
      const pl = q("[data-pbplunge]"); if (pl) { const set = (v) => { this.pbHeld.p = v; }; pl.addEventListener("mousedown", () => set(true)); pl.addEventListener("mouseup", () => set(false)); pl.addEventListener("mouseleave", () => set(false)); pl.addEventListener("touchstart", (e) => { e.preventDefault(); set(true); }); pl.addEventListener("touchend", () => set(false)); }
      this.pbCanvas = q(".pbcanvas");
      if (!this.pbKeys) { this.pbKeys = (e) => { if (this.cgView !== "pinball" || !this.dialogOpen() || !this.game.pbGame()) return; const k = { KeyZ: "l", ShiftLeft: "l", ArrowLeft: "l", Slash: "r", ShiftRight: "r", ArrowRight: "r", Space: "p", ArrowDown: "p" }[e.code]; if (!k) return; e.preventDefault(); e.stopPropagation(); this.pbHeld[k] = e.type === "keydown"; }; window.addEventListener("keydown", this.pbKeys, true); window.addEventListener("keyup", this.pbKeys, true); }
      if (!this.pbLoop) { let prev = performance.now(); const loop = (now) => { if (!this.pbCanvas || !this.pbCanvas.isConnected || this.cgView !== "pinball") { this.pbLoop = null; return; } const dt = Math.min(0.04, (now - prev) / 1000); prev = now; this.pbFrame(dt, now); this.pbLoop = requestAnimationFrame(loop); }; this.pbLoop = requestAnimationFrame(loop); }
    },
    pbFrame(dt, now) {
      const g = this.game, PB = CM.PB, G = g.pbGame(), cv = this.pbCanvas, p = cv.getContext("2d"), fx = this.pbFx = this.pbFx || { flash: {}, pts: [] }, H = this.pbHeld || {};
      if (G) { G.input(H.l, H.r, H.p); G.update(dt); for (const e of G.events.splice(0)) this.pbEvent(e, now, G); const out = g.pbCheck();
        if (out) { if (out.marks.length) { const m = out.marks[out.marks.length - 1]; this.cgNote = `${PB.MARKS[m.i - 1].toLocaleString("en")} points: +${out.marks.reduce((t, x) => t + x.pay, 0)} gold${out.marks.some((x) => x.card) ? ` and a card - ${out.marks.filter((x) => x.card).map((x) => x.card).join(", ")}` : ""}!`; this.cgSfx("coin", 0.5); if (out.marks.some((x) => x.card)) this.cgSfx("cardwin", 0.5); }
          if (out.over) { const S = g.pbState(); this.cgNote = `Game over: ${S.last.score.toLocaleString("en")} points, ${S.last.marks} mark${S.last.marks === 1 ? "" : "s"} passed, ${S.won} gold back.`; this.cgSfx("tablebell", 0.5); this.pbLast = G; }
          this.renderCasino(); return; } }
      const Gd = G || this.pbLast; const T = Gd ? Gd.T : PB.table(), X = (x) => x * K, Y = (y) => y * K + TOP;
      // the playfield
      const wood = p.createLinearGradient(0, TOP, 0, cv.height); wood.addColorStop(0, "#2A1E30"); wood.addColorStop(1, "#1A1420"); p.fillStyle = wood; p.fillRect(0, 0, cv.width, cv.height);
      p.strokeStyle = "rgba(255,255,255,0.05)"; for (let y = 0; y < PB.H; y += 2) for (let x = (y / 2) % 2; x < PB.W; x += 2) p.strokeRect(X(x), Y(y), 2 * K, 2 * K);
      p.save(); p.globalAlpha = 0.12; p.fillStyle = "#60C060"; p.beginPath(); p.moveTo(X(9.45), Y(9)); p.quadraticCurveTo(X(2), Y(14), X(4), Y(22)); p.quadraticCurveTo(X(9.45), Y(17), X(14.9), Y(22)); p.quadraticCurveTo(X(16.9), Y(14), X(9.45), Y(9)); p.fill(); p.restore();
      p.fillStyle = "#0E0A14"; p.fillRect(0, 0, cv.width, TOP); p.fillStyle = "#FFE070"; p.font = "bold 13px monospace"; p.fillText(Gd ? Gd.score.toLocaleString("en") : "WYRMHOLD", 8, 20);
      if (Gd) { p.fillStyle = "#C0B0E0"; p.font = "11px monospace"; p.fillText(`BALL ${Gd.ballNo}/${PB.balls}${Gd.extra ? " +" + Gd.extra : ""}  x${Gd.mult}`, cv.width - 128, 20); }
      // lane arrows and the kickback light
      if (Gd) { p.fillStyle = Gd.kickback ? "#FFB040" : "rgba(255,176,64,0.2)"; p.beginPath(); p.moveTo(X(1.15), Y(29.4)); p.lineTo(X(1.5), Y(30.2)); p.lineTo(X(0.8), Y(30.2)); p.closePath(); p.fill(); }
      // walls
      for (const s of T.segs) { if (s.kind === "target") continue; const sling = s.kind === "sling", rub = s.kind === "rubber"; p.strokeStyle = sling || rub ? (fx.flash["sling" + s.a[0]] > now ? "#FFFFFF" : "#D04040") : s.kind === "plunger" ? "transparent" : "#B8C0CC"; p.lineWidth = sling || rub ? 4 : 3; if (s.oneWay) { p.strokeStyle = "#8A8070"; p.lineWidth = 2; } p.beginPath(); p.moveTo(X(s.a[0]), Y(s.a[1])); p.lineTo(X(s.b[0]), Y(s.b[1])); p.stroke(); }
      p.lineWidth = 1;
      // the targets
      for (const s of T.segs) if (s.kind === "target") { const up = !Gd || Gd.targets[s.id], x0 = X(s.a[0]), x1 = X(s.b[0]), y = Y(s.a[1]); p.fillStyle = up ? "#F0C040" : "#3A2A20"; p.fillRect(x0, y - 7, x1 - x0, 8); if (up) { p.fillStyle = "#3A2010"; p.font = "bold 8px monospace"; p.textAlign = "center"; p.fillText("RUNES"[s.id], (x0 + x1) / 2, y); p.textAlign = "left"; } }
      // sensors: stars, the hoard
      for (const s of T.sensors) { const x = X(s.x), y = Y(s.y);
        if (s.kind === "star") { const lit = Gd && Gd.stars[s.id]; p.fillStyle = lit ? "#FFF080" : "rgba(255,240,128,0.25)"; p.beginPath(); for (let k = 0; k < 10; k++) { const a = -Math.PI / 2 + (k * Math.PI) / 5, rr = k % 2 ? 4 : 9; p.lineTo(x + Math.cos(a) * rr, y + Math.sin(a) * rr); } p.closePath(); p.fill(); }
        else if (s.kind === "hoard") { const gl = p.createRadialGradient(x, y, 2, x, y, 18); gl.addColorStop(0, "#000"); gl.addColorStop(0.5, "#2A1A08"); gl.addColorStop(1, "rgba(240,192,64,0)"); p.fillStyle = gl; p.beginPath(); p.arc(x, y, 18, 0, Math.PI * 2); p.fill(); p.fillStyle = "#F0C040"; p.font = "8px monospace"; p.fillText("HOARD", x - 13, y + 22); } }
      // round things
      for (const c of T.circles) { const x = X(c.x), y = Y(c.y), r = c.r * K, hot = fx.flash["c" + c.x + c.y] > now;
        if (c.kind === "bumper") { p.fillStyle = hot ? "#FFFFFF" : "#6040C0"; p.beginPath(); p.arc(x, y, r, 0, Math.PI * 2); p.fill(); p.strokeStyle = hot ? "#FFF080" : "#C0A0FF"; p.lineWidth = 3; p.stroke(); p.lineWidth = 1; p.fillStyle = hot ? "#6040C0" : "#E0D0FF"; p.font = "bold 12px Georgia"; p.textAlign = "center"; p.fillText("ᚱ", x, y + 4); p.textAlign = "left"; }
        else if (c.kind === "dragon") { p.fillStyle = hot ? "#C0FFC0" : "#3A8A3A"; p.beginPath(); p.arc(x, y, r, 0, Math.PI * 2); p.fill(); p.fillStyle = "#2A6A2A"; p.beginPath(); p.moveTo(x - r * 0.8, y - r * 0.5); p.lineTo(x - r * 1.2, y - r * 1.3); p.lineTo(x - r * 0.3, y - r * 0.8); p.moveTo(x + r * 0.8, y - r * 0.5); p.lineTo(x + r * 1.2, y - r * 1.3); p.lineTo(x + r * 0.3, y - r * 0.8); p.fill(); p.fillStyle = "#FFD040"; p.beginPath(); p.ellipse(x - 7, y - 3, 4, 3, 0, 0, Math.PI * 2); p.ellipse(x + 7, y - 3, 4, 3, 0, 0, Math.PI * 2); p.fill(); p.fillStyle = "#101010"; p.fillRect(x - 8, y - 5, 2, 4); p.fillRect(x + 6, y - 5, 2, 4);
          if (Gd) { const D = Gd.dragon, full = 3 + D.level; for (let k = 0; k < full; k++) { p.fillStyle = k < D.hp ? "#F05040" : "rgba(240,80,64,0.2)"; p.fillRect(x - full * 3 + k * 6, y + r + 4, 4, 4); } p.fillStyle = "#C0F0C0"; p.font = "9px monospace"; p.fillText(`LV ${D.level}`, x - 12, y + r + 18); } }
        else { p.fillStyle = "#B8C0CC"; p.beginPath(); p.arc(x, y, r, 0, Math.PI * 2); p.fill(); } }
      // flippers
      const flips = Gd ? Gd.flips : T.flippers.map((f) => ({ ...f, a: f.rest }));
      for (const f of flips) { const L = PB.flip.len, x0 = X(f.px), y0 = Y(f.py), x1 = X(f.px + Math.cos(f.a) * L), y1 = Y(f.py + Math.sin(f.a) * L), r0 = PB.flip.rBase * K, r1 = PB.flip.rTip * K, nx = -(y1 - y0) / (L * K), ny = (x1 - x0) / (L * K);
        p.fillStyle = "#F0E8E0"; p.beginPath(); p.moveTo(x0 + nx * r0, y0 + ny * r0); p.lineTo(x1 + nx * r1, y1 + ny * r1); p.arc(x1, y1, r1, Math.atan2(ny, nx), Math.atan2(ny, nx) + Math.PI); p.lineTo(x0 - nx * r0, y0 - ny * r0); p.arc(x0, y0, r0, Math.atan2(-ny, -nx), Math.atan2(-ny, -nx) + Math.PI); p.closePath(); p.fill(); p.strokeStyle = "#C03030"; p.lineWidth = 2; p.stroke(); p.lineWidth = 1; p.fillStyle = "#808890"; p.beginPath(); p.arc(x0, y0, 3, 0, Math.PI * 2); p.fill(); }
      // the plunger
      const pull = Gd ? Gd.pull : 0, pt = Y(34.6) + pull * 14; p.strokeStyle = "#A0A0A8"; p.lineWidth = 2; p.beginPath(); for (let k = 0; k <= 10; k++) p.lineTo(X(18.95) + (k % 2 ? 6 : -6), pt + 2 + (k * (cv.height - pt - 4)) / 10); p.stroke(); p.lineWidth = 1; p.fillStyle = "#C03030"; p.fillRect(X(18.5), pt, X(19.4) - X(18.5), 5);
      // balls
      if (Gd) for (const b of Gd.balls) { const x = X(b.x), y = Y(b.y), r = PB.r * K, gr = p.createRadialGradient(x - r * 0.4, y - r * 0.4, 1, x, y, r); gr.addColorStop(0, "#FFFFFF"); gr.addColorStop(0.4, "#C8D0D8"); gr.addColorStop(1, "#5A6068"); p.fillStyle = gr; p.beginPath(); p.arc(x, y, r, 0, Math.PI * 2); p.fill(); }
      fx.pts = fx.pts.filter((q) => now - q.at < 900); for (const q of fx.pts) { p.globalAlpha = 1 - (now - q.at) / 900; p.fillStyle = q.c || "#FFF0B0"; p.font = `bold ${q.big ? 16 : 11}px Georgia`; p.textAlign = "center"; p.fillText(q.text, q.x, q.y - (now - q.at) / 30); p.textAlign = "left"; } p.globalAlpha = 1;
    },
    pbEvent(e, now, G) {
      const fx = this.pbFx, PB = CM.PB, cx = (PB.W * K) / 2, msg = (text, c, big) => fx.pts.push({ text, x: cx, y: TOP + 26 * K, at: now, c, big });
      if (e.kind === "bumper") { fx.flash["c" + e.x + e.y] = now + 90; this.cgSfx("bump", 0.35, 1.6); }
      else if (e.kind === "sling") { fx.flash["sling" + e.x] = now + 90; this.cgSfx("bump", 0.3, 1.2); } else if (e.kind === "flip") this.cgSfx("card", 0.18, 0.7); else if (e.kind === "launch") this.cgSfx("zap", 0.35, 0.8);
      else if (e.kind === "target") this.cgSfx("card", 0.4, 1.4); else if (e.kind === "bank") { this.cgSfx("tablebell", 0.5); msg(`RUNES! x${e.mult}`, "#F0C040", true); }
      else if (e.kind === "star") this.cgSfx("coin", 0.25, 1.8); else if (e.kind === "stars") { this.cgSfx("spell", 0.45); msg("ALL STARS - bumpers x2, kickback lit", "#FFF080"); }
      else if (e.kind === "hoard") { this.cgSfx("coin", 0.5, 0.9); msg("THE HOARD +5,000", "#F0C040"); } else if (e.kind === "kickout") this.cgSfx("slam", 0.3, 1.4);
      else if (e.kind === "dragonhit") { const c = G.T.circles.find((q) => q.kind === "dragon"); fx.flash["c" + c.x + c.y] = now + 120; this.cgSfx("monster", 0.35, 1.3); }
      else if (e.kind === "dragon") { this.cgSfx("victory", 0.6); msg(`DRAGON SLAIN! MULTIBALL`, "#80FF80", true); } else if (e.kind === "extraball") { this.cgSfx("cardwin", 0.5); msg("EXTRA BALL", "#80E0FF", true); }
      else if (e.kind === "kickback") { this.cgSfx("slam", 0.5, 0.9); msg("KICKBACK!", "#FFB040"); } else if (e.kind === "saved") { this.cgSfx("spell", 0.4, 1.4); msg("BALL SAVED", "#80E0FF", true); }
      else if (e.kind === "drain") { this.cgSfx("miss", 0.45, 0.8); msg(`BONUS ${e.bonus.toLocaleString("en")}`, "#FFE070", true); } else if (e.kind === "shootagain") msg("SHOOT AGAIN", "#80E0FF", true);
      else if (e.kind === "wall" && e.v > 14) this.cgSfx("bump", Math.min(0.3, e.v / 80), 1.9);
      else if (e.kind === "mark") msg(`${PB.MARKS[e.i - 1].toLocaleString("en")}!`, "#FFE070", true);
    },
  });
}
