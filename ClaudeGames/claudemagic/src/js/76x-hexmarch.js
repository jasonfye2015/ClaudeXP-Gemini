"use strict";
// The Hexmarch, the window's side (the thirty-first big update): the cellar range on a canvas - a brick back wall in
// the dark, the ranks of hexlings drawn in chunky pixels with two steps of their march (Imps with horns, Wisps like
// flames, Grubs on their many legs), the four warding stones cracking as they are hit, the rune-cannon and its bolt,
// the hexes twisting down, the comet's streak, bursts and points; the score, the lives and the level at the top. Left
// and right (or A and D) to slide, Space to fire, P to pause. The rules are 64zh-hexmarch.js.
CM.CG_TABLES.push(["hexmarch", "The Hexmarch"]);
{ const floor0 = CM.UI.prototype.renderFloor, C = 16, TOP = 28;
  // the hexlings' pixels, two steps each ("#" body, "o" eye)
  const ART = {
    imp: [["..#.....#..", "...#...#...", "..#######..", ".##o###o##.", "###########", "#.#######.#", "#.#.....#.#", "...##.##..."], ["..#.....#..", "#..#...#..#", "#.#######.#", "###o###o###", "###########", "..#######..", "..#.....#..", ".#.......#."]],
    wisp: [["....#.#....", "...#####...", "..#######..", ".##o###o##.", ".#########.", "..#######..", ".#.#.#.#.#.", "#.........#"], ["...#.#.#...", "...#####...", "..#######..", ".##o###o##.", ".#########.", "..#######..", "..#.#.#.#..", ".#.#...#.#."]],
    grub: [["...#####...", ".#########.", "##o#####o##", "###########", ".#.#.#.#.#.", "#.#.#.#.#.#", "...........", "..........."], ["...#####...", ".#########.", "##o#####o##", "###########", "#.#.#.#.#.#", ".#.#.#.#.#.", "...........", "..........."]],
  };
  const COL = { imp: "#F06080", wisp: "#60D0F0", grub: "#A0E060" };
  Object.assign(CM.UI.prototype, {
    renderFloor(box) { if (this.cgView === "hexmarch") return this.cgHexmarch(box); return floor0.call(this, box); },
    cgHexmarch(box) {
      const g = this.game, HX = CM.HX, S = g.hxState(), L = g.hxLevel(), live = !!L, bet = live ? S.bet : (this.cgBet === undefined ? 5 : this.cgBet), Cl = g.hxClaimed(), last = S && S.stage === "done" ? S.last : null;
      const top = Math.max(15, (S && live ? S.n : 1) + 4), rows = []; for (let n = 1; n <= top; n++) { const card = n % HX.cardEvery === 0, tier = CM.cardTierFor(n); rows.push(`<div class="rung${live && S.n === n ? " now" : ""}${live && S.n > n ? " done" : ""}"><span>Level ${n}</span><b>${Math.round(bet * HX.pay(n))}</b><i class="${!card ? "" : Cl[n] ? "got" : tier}" title="${!card ? "" : Cl[n] ? "card already won" : `a ${tier === "better" ? "stronger common" : tier} card, the first time`}">${!card ? "" : Cl[n] ? "✓" : tier === "rare" ? "★" : tier === "better" ? "◆" : "♦"}</i></div>`); }
      box.innerHTML = `<div class="cgtable hexmarch runestack dash"><h3>The Hexmarch</h3><div class="rswrap"><canvas class="hxcanvas" width="${HX.W * C}" height="${HX.H * C + TOP}" tabindex="0"></canvas>
        <div class="dashside"><p class="lore">Down in the Joker's cellar range a rune-cannon sits behind four old warding stones, and every night the hexlings march out of the far wall in ranks. "Don't let them reach the floor," says the attendant. "The house pays by the rank."</p>
        <div class="ladder rsladder">${rows.reverse().join("")}</div>
        ${live ? "" : this.cgBetRow("The stake")}<div class="cgnote">${this.cgNote || ""}</div>${last && last.cards && last.cards.length ? last.cards.map((c) => this.cgCardWon(c)).join("") : ""}
        <div class="row">${live ? `<button data-hxpause>${this.hxPaused ? "Go on" : "Pause"}</button>` : `<button class="primary" data-hxstart>Down to the range (${bet} gold)</button>`}<button data-leave>Leave</button></div>
        <div class="small">Left and right (or A and D) to slide; Space to fire - one bolt at a time, so make it count; P to pause. Grubs 10, Wisps 20, Imps 30, the comet across the top a mystery score. The march quickens as it thins, and steps down at each wall; if it reaches the floor the game is over. The warding stones stop hexes and bolts alike until they crumble. Three lives, one more at 1,500. Each level cleared pays gold, more each, every play; every third level gives a card the first time ever (♦ level 3, ◆ 6 and 9, ★ from 12). Best score ${g.cgStore().hxBest || 0}.</div>${this.cgStats("hexmarch")}</div></div></div>`;
      this.cgWireBet(box); const q = (s) => box.querySelector(s); q("[data-leave]").addEventListener("click", () => this.closeDialogs());
      if (q("[data-hxstart]")) q("[data-hxstart]").addEventListener("click", () => { const r = g.hxStart(bet); this.cgNote = r.error || "Level 1. Hold the range!"; this.hxFx = { parts: [], pts: [], banner: { at: performance.now(), text: "LEVEL 1" } }; this.hxPaused = false; this.cgSfx(r.error ? "miss" : "door", 0.45); this.renderCasino(); const cv = this.$("#casino-body .hxcanvas"); if (cv) cv.focus(); });
      if (q("[data-hxpause]")) q("[data-hxpause]").addEventListener("click", () => { this.hxPaused = !this.hxPaused; this.renderCasino(); });
      this.hxCanvas = q(".hxcanvas");
      if (!this.hxKeys) { this.hxHeld = new Set();
        this.hxKeys = (e) => { if (this.cgView !== "hexmarch" || !this.dialogOpen() || !this.game.hxLevel()) return; if (e.type === "keydown" && e.code === "KeyP") { e.preventDefault(); this.hxPaused = !this.hxPaused; this.renderCasino(); return; }
          const k = { ArrowLeft: "l", KeyA: "l", ArrowRight: "r", KeyD: "r", Space: "f" }[e.code]; if (!k) return; e.preventDefault(); e.stopPropagation(); if (e.type === "keydown") this.hxHeld.add(k); else this.hxHeld.delete(k); };
        window.addEventListener("keydown", this.hxKeys, true); window.addEventListener("keyup", this.hxKeys, true); }
      if (!this.hxLoop) { let prev = performance.now(); const loop = (now) => { if (!this.hxCanvas || !this.hxCanvas.isConnected || this.cgView !== "hexmarch") { this.hxLoop = null; return; } const dt = Math.min(0.05, (now - prev) / 1000); prev = now; this.hxFrame(dt, now); this.hxLoop = requestAnimationFrame(loop); }; this.hxLoop = requestAnimationFrame(loop); }
    },
    hxFrame(dt, now) {
      const g = this.game, HX = CM.HX, L = g.hxLevel(), cv = this.hxCanvas, p = cv.getContext("2d"), fx = this.hxFx = this.hxFx || { parts: [], pts: [] }, H = this.hxHeld || new Set();
      if (L && !this.hxPaused) { L.input((H.has("r") ? 1 : 0) - (H.has("l") ? 1 : 0), H.has("f")); L.update(dt); for (const e of L.events.splice(0)) this.hxEvent(e, now, L); const out = g.hxCheck();
        if (out && out.cleared) { fx.banner = { at: now, text: `LEVEL ${out.cleared + 1}`, sub: `Level ${out.cleared} cleared: +${out.pay} gold${out.card ? ` - ${out.card}` : ""}` }; this.cgSfx("victory", 0.5); if (out.card) setTimeout(() => this.cgSfx("cardwin", 0.5), 300); this.cgNote = `Level ${out.cleared} cleared: ${out.pay} gold${out.card ? `, and a card - ${out.card}` : ""}.`; this.renderCasino(); return; }
        if (out && out.over) { const S = g.hxState(); this.cgNote = `The range is overrun on level ${S.last.level}. ${S.won} gold back${S.last.cards.length ? `, and ${S.last.cards.length} card${S.last.cards.length > 1 ? "s" : ""}` : ""}.`; this.cgSfx("cardlose", 0.5); this.renderCasino(); if (S.won) this.cgCoins(this.$("#casino-body"), 12); return; } }
      const Lv = L || this.hxLastDrawn; if (L) this.hxLastDrawn = L;
      // the cellar: a dark brick wall, the floor line
      p.fillStyle = "#0C0A10"; p.fillRect(0, 0, cv.width, cv.height); p.fillStyle = "#16121C"; for (let y = TOP; y < cv.height; y += 14) for (let x = ((y / 14) % 2) * 14 - 14; x < cv.width; x += 28) p.fillRect(x + 1, y + 1, 26, 12);
      for (const tx of [14, cv.width - 14]) { const ty = TOP + 150, fl = 0.8 + 0.2 * Math.sin(now / 70 + tx) * Math.sin(now / 131 + tx); const tg = p.createRadialGradient(tx, ty, 4, tx, ty, 150 * fl); tg.addColorStop(0, "rgba(255,160,70,0.3)"); tg.addColorStop(1, "rgba(255,160,70,0)"); p.fillStyle = tg; p.fillRect(tx - 160, ty - 160, 320, 320);
        p.fillStyle = "#3A2A1A"; p.fillRect(tx - 3, ty, 6, 16); p.fillStyle = "#FF8030"; p.beginPath(); p.moveTo(tx - 5, ty); p.quadraticCurveTo(tx, ty - 16 * fl, tx + 5, ty); p.fill(); p.fillStyle = "#FFE080"; p.beginPath(); p.moveTo(tx - 2, ty); p.quadraticCurveTo(tx, ty - 8 * fl, tx + 2, ty); p.fill(); }
      { const fg = p.createLinearGradient(0, cv.height - 70, 0, cv.height); fg.addColorStop(0, "rgba(200,80,120,0)"); fg.addColorStop(1, "rgba(200,80,120,0.12)"); p.fillStyle = fg; p.fillRect(0, cv.height - 70, cv.width, 70); }
      p.fillStyle = "#140E18"; p.fillRect(0, 0, cv.width, TOP); p.fillStyle = "#FFE070"; p.font = "bold 14px monospace"; p.fillText(Lv ? `SCORE ${Lv.score}` : "THE HEXMARCH", 8, 19);
      if (Lv) { p.fillText(`LEVEL ${Lv.n}`, cv.width / 2 - 30, 19); for (let k = 0; k < Math.min(6, Lv.lives); k++) this.hxCannon(p, cv.width - 16 - k * 20, 16, 0.55); }
      if (!Lv) { p.fillStyle = "rgba(255,240,200,0.9)"; p.font = "bold 24px Georgia, serif"; p.textAlign = "center"; p.fillText("The Hexmarch", cv.width / 2, cv.height / 2); p.textAlign = "left"; return; }
      p.save(); p.translate(0, TOP);
      p.fillStyle = "#6A3040"; p.fillRect(0, (HX.floorY + 1.2) * C, cv.width, 2);
      for (const f of Lv.foes) if (!f.dead) this.hxFoe(p, f, Lv.frame);
      for (const w of Lv.wards) if (w.hp > 0) { const s = HX.WARD.cell * C; p.fillStyle = w.hp > 1 ? "#8A8A9A" : "#5A5A68"; p.fillRect(w.x * C - s / 2, w.y * C - s / 2, s, s); if (w.hp < 2) { p.fillStyle = "#2A2A30"; p.fillRect(w.x * C - 2, w.y * C - 1, 3, 2); } else { p.fillStyle = "rgba(160,200,255,0.25)"; p.fillRect(w.x * C - s / 2, w.y * C - s / 2, s, 2); } }
      if (Lv.comet) { const X = Lv.comet.x * C, Y = Lv.comet.y * C, gr = p.createLinearGradient(X - Math.sign(Lv.comet.v) * 50, Y, X, Y); gr.addColorStop(0, "rgba(255,200,100,0)"); gr.addColorStop(1, "rgba(255,230,160,0.9)"); p.fillStyle = gr; p.fillRect(Math.min(X, X - Math.sign(Lv.comet.v) * 50), Y - 4, 50, 8); p.fillStyle = "#FFF4D0"; p.beginPath(); p.arc(X, Y, 6, 0, Math.PI * 2); p.fill(); }
      if (Lv.bolt) { p.fillStyle = "#80F0FF"; p.shadowColor = "#80F0FF"; p.shadowBlur = 8; p.fillRect(Lv.bolt.x * C - 1.5, Lv.bolt.y * C - 7, 3, 12); p.shadowBlur = 0; }
      for (const h of Lv.hexes) { const X = h.x * C, Y = h.y * C; p.strokeStyle = ["#C080FF", "#FF80C0", "#FFC060"][h.kind]; p.lineWidth = 2; p.beginPath(); for (let k = 0; k <= 4; k++) p.lineTo(X + ((k + Math.floor(h.t * 12)) % 2 ? 3 : -3), Y - 8 + k * 4); p.stroke(); p.lineWidth = 1; }
      if (!Lv.p.dead) this.hxCannon(p, Lv.p.x * C, HX.gunY * C, 1);
      fx.parts = fx.parts.filter((q) => (q.life -= dt) > 0); for (const q of fx.parts) { q.x += q.vx * dt; q.y += q.vy * dt; p.globalAlpha = Math.min(1, q.life * 2.5); p.fillStyle = q.c; p.fillRect(q.x - 1.5, q.y - 1.5, 3, 3); } p.globalAlpha = 1;
      fx.pts = fx.pts.filter((q) => now - q.at < 900); for (const q of fx.pts) { p.globalAlpha = 1 - (now - q.at) / 900; p.fillStyle = "#FFE070"; p.font = "bold 12px monospace"; p.fillText(String(q.n), q.x - 10, q.y - (now - q.at) / 40); } p.globalAlpha = 1;
      p.restore();
      if (fx.banner && now - fx.banner.at < 2600) { const B = fx.banner, t = (now - B.at) / 2600; p.globalAlpha = t > 0.8 ? (1 - t) / 0.2 : 1; p.fillStyle = "#F0C0FF"; p.font = "bold 26px Georgia, serif"; p.textAlign = "center"; p.fillText(B.text, cv.width / 2, cv.height / 2 + 20); if (B.sub) { p.font = "14px Georgia, serif"; p.fillStyle = "#F0E0B0"; p.fillText(B.sub, cv.width / 2, cv.height / 2 - 14); } p.textAlign = "left"; p.globalAlpha = 1; }
      if (this.hxPaused) { p.fillStyle = "rgba(0,0,0,0.6)"; p.fillRect(0, 0, cv.width, cv.height); p.fillStyle = "#FFF"; p.font = "bold 26px Georgia, serif"; p.textAlign = "center"; p.fillText("Paused", cv.width / 2, cv.height / 2); p.textAlign = "left"; }
    },
    hxEvent(e, now, L) {
      const fx = this.hxFx, C2 = C, burst = (x, y, cols, n = 14) => { for (let k = 0; k < n; k++) { const a = Math.random() * Math.PI * 2, v = 40 + Math.random() * 110; fx.parts.push({ x: x * C2, y: y * C2, vx: Math.cos(a) * v, vy: Math.sin(a) * v, life: 0.35 + Math.random() * 0.35, c: cols[k % cols.length] }); } };
      if (e.kind === "beat") this.cgSfx("bump", 0.12, e.n ? 0.55 : 0.48); else if (e.kind === "fire") { this.cgSfx("zap", 0.2, 1.7); for (let k = 0; k < 6; k++) fx.parts.push({ x: L.p.x * C2, y: (CM.HX.gunY - 0.8) * C2, vx: (Math.random() - 0.5) * 70, vy: -30 - Math.random() * 70, life: 0.16, c: k % 2 ? "#FFFFFF" : "#80F0FF" }); }
      else if (e.kind === "kill") { this.cgSfx("shatter", 0.3, 1.3); burst(e.f.x, e.f.y, [COL[e.f.kind], "#FFFFFF"]); }
      else if (e.kind === "comet") { this.cgSfx("coin", 0.6); fx.pts.push({ x: e.x * C2, y: 2.5 * C2, n: e.pts, at: now }); burst(e.x, 2.5, ["#FFF4D0", "#FFC060"], 20); }
      else if (e.kind === "cometcome") this.cgSfx("spell", 0.25, 1.5); else if (e.kind === "clash") this.cgSfx("card", 0.3, 1.8);
      else if (e.kind === "die" || e.kind === "landed") { this.cgSfx("hurt", 0.6); burst(L.p.x, CM.HX.gunY, ["#FFE070", "#F06030", "#FFFFFF"], 26); }
      else if (e.kind === "extra") this.cgSfx("cardwin", 0.4);
    },
    // the rune-cannon: a bronze carriage, a barrel, a rune glowing on its side
    hxCannon(p, X, Y, s) {
      p.save(); p.translate(X, Y); p.scale(s, s); p.fillStyle = "#6A4A2A"; p.fillRect(-11, 2, 22, 6); p.fillStyle = "#3A2A1A"; p.beginPath(); p.arc(-7, 9, 3, 0, Math.PI * 2); p.arc(7, 9, 3, 0, Math.PI * 2); p.fill();
      p.fillStyle = "#C08A40"; p.fillRect(-5, -4, 10, 7); p.fillRect(-2, -11, 4, 8); p.fillStyle = "#80F0FF"; p.shadowColor = "#80F0FF"; p.shadowBlur = 6; p.fillRect(-1.5, -2, 3, 3); p.shadowBlur = 0; p.restore();
    },
    hxFoe(p, f, frame) {
      const art = ART[f.kind][frame], X = f.x * C - 11, Y = f.y * C - 8; p.fillStyle = COL[f.kind];
      for (let j = 0; j < art.length; j++) for (let i = 0; i < art[j].length; i++) { const c = art[j][i]; if (c === "#") p.fillRect(X + i * 2, Y + j * 2, 2, 2); }
      p.fillStyle = "#101010"; for (let j = 0; j < art.length; j++) for (let i = 0; i < art[j].length; i++) if (art[j][i] === "o") p.fillRect(X + i * 2, Y + j * 2, 2, 2);
    },
  });
}
