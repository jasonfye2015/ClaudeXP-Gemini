"use strict";
// Runestep Pyramid, the window's side (the thirty-fifth big update): the pyramid on a canvas, seen from the corner - each
// cube with its lit top (the start colour, a halfway colour on the two-step levels, the finished colour with its rune),
// shaded sides in the level's stone; the wind-wisps spinning off the sides (and carrying the glimmerkin up); the
// glimmerkin, a round lantern-sprite with a tuft, hopping in an arc and looking the way it goes (tumbling away when it
// falls); ember-balls, the violet egg, the Sigil Serpent coiled like a spring, the Smudge, the frost orb (and everything
// rimed while frozen); the score, the lives, the level and the colour wanted. Q W A S or the arrows hop: Q (or left)
// up-left, W (or up) up-right, A (or down) down-left, S (or right) down-right. P to pause. The rules are
// 64zl-runestep.js.
CM.CG_TABLES.push(["runestep", "Runestep Pyramid"]);
{ const floor0 = CM.UI.prototype.renderFloor, A = 28, ROWH = 42, Y0 = 74, TOP = 28, CW = 480, CH = 410;
  const THEME = [{ side: ["#4A3A6A", "#2E2448"], tops: ["#5A70C0", "#E0A040", "#F0E060"] }, { side: ["#6A3A3A", "#442424"], tops: ["#40A090", "#C060C0", "#F0F0F0"] }, { side: ["#3A5A3A", "#243A24"], tops: ["#C05050", "#5080E0", "#60E080"] }, { side: ["#5A4A2A", "#3A2E18"], tops: ["#8060C0", "#40C0E0", "#F0A040"] }];
  const pos = (r, c) => [CW / 2 + (2 * c - r) * A, Y0 + r * ROWH];
  Object.assign(CM.UI.prototype, {
    renderFloor(box) { if (this.cgView === "runestep") return this.cgRunestep(box); return floor0.call(this, box); },
    cgRunestep(box) {
      const g = this.game, RP = CM.RP, S = g.rpState(), L = g.rpLevel(), live = !!L, bet = live ? S.bet : (this.cgBet === undefined ? 5 : this.cgBet), Cl = g.rpClaimed(), last = S && S.stage === "done" ? S.last : null;
      const top = Math.max(15, (S && live ? S.n : 1) + 4), rows = []; for (let n = 1; n <= top; n++) { const card = n % RP.cardEvery === 0, tier = CM.cardTierFor(n); rows.push(`<div class="rung${live && S.n === n ? " now" : ""}${live && S.n > n ? " done" : ""}"><span>Level ${n}</span><b>${Math.round(bet * RP.pay(n))}</b><i class="${!card ? "" : Cl[n] ? "got" : tier}" title="${!card ? "" : Cl[n] ? "card already won" : `a ${tier === "better" ? "stronger common" : tier} card, the first time`}">${!card ? "" : Cl[n] ? "✓" : tier === "rare" ? "★" : tier === "better" ? "◆" : "♦"}</i></div>`); }
      box.innerHTML = `<div class="cgtable runestep runestack dash"><h3>Runestep Pyramid</h3><div class="rswrap"><canvas class="rpcanvas" width="${CW}" height="${CH + TOP}" tabindex="0"></canvas>
        <div class="dashside"><p class="lore">In the middle of the back room stands a pyramid of rune-cubes, and on its peak a glimmerkin waiting to hop. "Light every cube," says the attendant. "The stones roll down. The serpent hatches. The wisps on the sides are your friends."</p>
        <div class="ladder rsladder">${rows.reverse().join("")}</div>
        ${live ? "" : this.cgBetRow("The stake")}<div class="cgnote">${this.cgNote || ""}</div>${last && last.cards && last.cards.length ? last.cards.map((c) => this.cgCardWon(c)).join("") : ""}
        <div class="row">${live ? `<button data-rppause>${this.rpPaused ? "Go on" : "Pause"}</button>` : `<button class="primary" data-rpstart>To the pyramid (${bet} gold)</button>`}<button data-leave>Leave</button></div>
        <div class="small">Hop diagonally: <b>Q</b> or ← up-left, <b>W</b> or ↑ up-right, <b>A</b> or ↓ down-left, <b>S</b> or → down-right; P to pause. Each landing lights a cube's top a step toward the colour shown at the top - one step on levels 1-2, two from level 3, and from level 6 landing on a finished cube turns it back. Ember-balls and the violet egg roll down; the egg hatches into the Sigil Serpent, who hops after you. Catch the Smudge (from level 3) before it undoes your cubes, 300; catch a frost orb to freeze everything, 100. Hop onto a wind-wisp off the side to ride to the top - a serpent close behind follows you off the edge, 500. Hop off anywhere else and you fall. Three lives, one more at 8,000. Each level cleared pays gold, more each, every play; every third level gives a card the first time ever (♦ level 3, ◆ 6 and 9, ★ from 12). Best score ${g.cgStore().rpBest || 0}.</div>${this.cgStats("runestep")}</div></div></div>`;
      this.cgWireBet(box); const q = (s) => box.querySelector(s); q("[data-leave]").addEventListener("click", () => this.closeDialogs());
      if (q("[data-rpstart]")) q("[data-rpstart]").addEventListener("click", () => { const r = g.rpStart(bet); this.cgNote = r.error || "Level 1. Hop!"; this.rpFx = { parts: [], pts: [], banner: { at: performance.now(), text: "LEVEL 1" } }; this.rpPaused = false; this.cgSfx(r.error ? "miss" : "door", 0.45); this.renderCasino(); const cv = this.$("#casino-body .rpcanvas"); if (cv) cv.focus(); });
      if (q("[data-rppause]")) q("[data-rppause]").addEventListener("click", () => { this.rpPaused = !this.rpPaused; this.renderCasino(); });
      this.rpCanvas = q(".rpcanvas");
      if (!this.rpKeys) {
        this.rpKeys = (e) => { if (this.cgView !== "runestep" || !this.dialogOpen() || !this.game.rpLevel()) return; if (e.code === "KeyP") { e.preventDefault(); this.rpPaused = !this.rpPaused; this.renderCasino(); return; }
          const d = { KeyQ: "ul", ArrowLeft: "ul", Numpad7: "ul", KeyW: "ur", ArrowUp: "ur", Numpad9: "ur", KeyA: "dl", ArrowDown: "dl", Numpad1: "dl", KeyS: "dr", ArrowRight: "dr", Numpad3: "dr" }[e.code]; if (!d) return; e.preventDefault(); e.stopPropagation(); if (!e.repeat && !this.rpPaused) this.game.rpLevel().input(d); };
        window.addEventListener("keydown", this.rpKeys, true); }
      if (!this.rpLoop) { let prev = performance.now(); const loop = (now) => { if (!this.rpCanvas || !this.rpCanvas.isConnected || this.cgView !== "runestep") { this.rpLoop = null; return; } const dt = Math.min(0.05, (now - prev) / 1000); prev = now; this.rpFrame(dt, now); this.rpLoop = requestAnimationFrame(loop); }; this.rpLoop = requestAnimationFrame(loop); }
    },
    rpFrame(dt, now) {
      const g = this.game, RP = CM.RP, L = g.rpLevel(), cv = this.rpCanvas, p = cv.getContext("2d"), fx = this.rpFx = this.rpFx || { parts: [], pts: [] };
      if (L && !this.rpPaused) { L.update(dt); for (const e of L.events.splice(0)) this.rpEvent(e, now, L); const out = g.rpCheck();
        if (out && out.cleared) { fx.banner = { at: now, text: `LEVEL ${out.cleared + 1}`, sub: `Level ${out.cleared} cleared: +${out.pay} gold${out.card ? ` - ${out.card}` : ""}` }; this.cgSfx("victory", 0.5); if (out.card) setTimeout(() => this.cgSfx("cardwin", 0.5), 300); this.cgNote = `Level ${out.cleared} cleared: ${out.pay} gold${out.card ? `, and a card - ${out.card}` : ""}.`; this.renderCasino(); return; }
        if (out && out.over) { const S = g.rpState(); this.cgNote = `The glimmerkin's light goes out on level ${S.last.level}. ${S.won} gold back${S.last.cards.length ? `, and ${S.last.cards.length} card${S.last.cards.length > 1 ? "s" : ""}` : ""}.`; this.cgSfx("cardlose", 0.5); this.renderCasino(); if (S.won) this.cgCoins(this.$("#casino-body"), 12); return; } }
      const Lv = L || this.rpLastDrawn; if (L) this.rpLastDrawn = L; const T = THEME[((Lv ? Lv.n : 1) - 1) % THEME.length];
      const bg = p.createLinearGradient(0, 0, 0, cv.height); bg.addColorStop(0, "#0C0818"); bg.addColorStop(1, "#1A1028"); p.fillStyle = bg; p.fillRect(0, 0, cv.width, cv.height);
      p.fillStyle = "#120C1C"; p.fillRect(0, 0, cv.width, TOP); p.fillStyle = "#FFE070"; p.font = "bold 14px monospace"; p.fillText(Lv ? `SCORE ${Lv.score}` : "RUNESTEP PYRAMID", 8, 19);
      if (Lv) { p.fillText(`LEVEL ${Lv.n}`, cv.width / 2 - 30, 19); for (let k = 0; k < Math.min(6, Lv.lives); k++) this.rpHopper(p, cv.width - 16 - k * 18, 16, "dl", 0.45, now); }
      p.save(); p.translate(0, TOP);
      if (Lv) { p.fillStyle = "#C0B0E0"; p.font = "12px Georgia, serif"; p.fillText("Light them:", 10, 22); const ts = T.tops; this.rpTop(p, 98, 18, ts[Lv.need === 1 ? 2 : 2], true, 0.6); if (Lv.need > 1) { p.fillText("by way of", 10, 46); this.rpTop(p, 98, 42, ts[1], false, 0.6); } if (Lv.toggle) { p.fillStyle = "#F0A0A0"; p.fillText("(a hop turns it back)", 10, 68); } }
      // the cubes
      for (let r = 0; r < RP.ROWS; r++) for (let c = 0; c <= r; c++) { const [x, y] = pos(r, c), v = Lv ? Lv.tiles[r][c] : 0, need = Lv ? Lv.need : 1, col = v >= need ? T.tops[2] : v === 0 ? T.tops[0] : T.tops[1];
        p.fillStyle = T.side[0]; p.beginPath(); p.moveTo(x - A, y); p.lineTo(x, y + A / 2); p.lineTo(x, y + A / 2 + 28); p.lineTo(x - A, y + 28); p.closePath(); p.fill();
        p.fillStyle = T.side[1]; p.beginPath(); p.moveTo(x + A, y); p.lineTo(x, y + A / 2); p.lineTo(x, y + A / 2 + 28); p.lineTo(x + A, y + 28); p.closePath(); p.fill();
        this.rpTop(p, x, y, col, v >= need, 1); if (Lv && Lv.frozen > 0) { p.fillStyle = "rgba(200,240,255,0.18)"; p.beginPath(); p.moveTo(x, y - A / 2); p.lineTo(x + A, y); p.lineTo(x, y + A / 2); p.lineTo(x - A, y); p.closePath(); p.fill(); } }
      if (!Lv) { p.restore(); p.fillStyle = "rgba(255,240,200,0.9)"; p.font = "bold 24px Georgia, serif"; p.textAlign = "center"; p.fillText("Runestep Pyramid", cv.width / 2, cv.height - 20); p.textAlign = "left"; return; }
      // wisps
      const P = Lv.p;
      for (const w of Lv.wisps) { if (w.used && !(P.ride && P.wispAt === w)) continue; let [x, y] = pos(w.r, w.side < 0 ? -1 : w.r + 1); if (P.ride && P.wispAt === w) { const k = 1 - P.ride.t / RP.ride, [tx, ty] = pos(0, 0); x += (tx - x) * k; y += (ty - 40 - y) * k - Math.sin(k * Math.PI) * 40; } y -= 6 + Math.sin(now / 200) * 3;
        p.strokeStyle = "rgba(220,240,255,0.85)"; p.lineWidth = 2; p.beginPath(); for (let k = 0; k < 30; k++) { const a = now / 150 + k * 0.45, rr = 3 + k * 0.5; p.lineTo(x + Math.cos(a) * rr, y + Math.sin(a) * rr * 0.4); } p.stroke(); p.lineWidth = 1;
        if (P.ride && P.wispAt === w) this.rpHopper(p, x, y - 12, "dl", 1, now); }
      // foes and the glimmerkin, drawn in row order so nearer ones cover farther ones
      const arc = (fr, fc, r, c, k) => { const [x0, y0] = fr < 0 ? [pos(r, c)[0], pos(r, c)[1] - 120] : pos(fr, fc), [x1, y1] = pos(r, c); return [x0 + (x1 - x0) * k, y0 + (y1 - y0) * k - Math.sin(k * Math.PI) * 26 - 10]; };
      const draws = [];
      for (const f of Lv.foes) { const full = RP.enemyHop[f.kind] / Lv.mul, k = f.falling ? 1 : Math.min(1, Math.max(0, 1 - Math.max(0, f.hopT - full * 0.55) / (full * 0.45))); let [x, y] = arc(f.fr, f.fc, f.r, f.c, f.fr === -1 ? Math.min(1, 1 - f.hopT / 0.5) : k); if (f.falling) y += (RP.fall - f.falling) * 260; draws.push({ z: f.r + (f.falling ? 9 : 0), fn: () => this.rpFoe(p, f, x, y, now, Lv.frozen > 0) }); }
      if (!P.ride && !(P.dead && !RP.on(P.r, P.c))) { const k = P.hopT ? 1 - P.hopT / RP.hop : 1; let [x, y] = P.hopT ? arc(P.fr, P.fc, P.r, P.c, k) : [pos(P.r, P.c)[0], pos(P.r, P.c)[1] - 10]; if (P.fallT) { y += (RP.fall - P.fallT) * 300; } draws.push({ z: P.r + (P.fallT ? 9 : 0) + 0.5, fn: () => { if (!P.dead || Math.floor(now / 100) % 2) this.rpHopper(p, x, y, P.face || "dl", 1, now); if (P.dead) { p.fillStyle = "#FFF"; p.font = "bold 13px Georgia"; p.fillText("✶!#", x - 12, y - 22); } } }); }
      draws.sort((a, b) => a.z - b.z).forEach((d) => d.fn());
      fx.parts = fx.parts.filter((q) => (q.life -= dt) > 0); for (const q of fx.parts) { q.x += q.vx * dt; q.y += q.vy * dt; q.vy += 200 * dt; p.globalAlpha = Math.min(1, q.life * 2); p.fillStyle = q.c; p.fillRect(q.x - 1.5, q.y - 1.5, 3, 3); } p.globalAlpha = 1;
      fx.pts = fx.pts.filter((q) => now - q.at < 900); for (const q of fx.pts) { p.globalAlpha = 1 - (now - q.at) / 900; p.fillStyle = "#FFF0B0"; p.font = "bold 12px monospace"; p.fillText(String(q.n), q.x - 10, q.y - (now - q.at) / 40); } p.globalAlpha = 1;
      p.restore();
      if (fx.banner && now - fx.banner.at < 2600) { const B = fx.banner, t = (now - B.at) / 2600; p.globalAlpha = t > 0.8 ? (1 - t) / 0.2 : 1; p.fillStyle = "rgba(0,0,0,0.6)"; p.fillRect(0, cv.height - 84, cv.width, 70); p.fillStyle = "#F0E0FF"; p.font = "bold 24px Georgia, serif"; p.textAlign = "center"; p.fillText(B.text, cv.width / 2, cv.height - 24); if (B.sub) { p.font = "14px Georgia, serif"; p.fillStyle = "#F0E0B0"; p.fillText(B.sub, cv.width / 2, cv.height - 58); } p.textAlign = "left"; p.globalAlpha = 1; }
      if (this.rpPaused) { p.fillStyle = "rgba(0,0,0,0.6)"; p.fillRect(0, 0, cv.width, cv.height); p.fillStyle = "#FFF"; p.font = "bold 26px Georgia, serif"; p.textAlign = "center"; p.fillText("Paused", cv.width / 2, cv.height / 2); p.textAlign = "left"; }
    },
    rpEvent(e, now, L) {
      const fx = this.rpFx, burst = (x, y, cols, n = 12) => { for (let k = 0; k < n; k++) fx.parts.push({ x, y, vx: (Math.random() - 0.5) * 160, vy: -Math.random() * 140, life: 0.6, c: cols[k % cols.length] }); };
      if (e.kind === "hop") this.cgSfx("step", 0.22, 1.5); else if (e.kind === "tile") { this.cgSfx("coin", 0.18, 1.2 + e.v * 0.2); const [x, y] = pos(e.r, e.c); burst(x, y + TOP * 0, ["#FFF0A0", "#FFFFFF"], 6); }
      else if (e.kind === "untile") this.cgSfx("card", 0.3, 0.7); else if (e.kind === "wisp") this.cgSfx("spell", 0.45, 1.3); else if (e.kind === "fall") this.cgSfx("miss", 0.5, 0.7);
      else if (e.kind === "lured") { this.cgSfx("victory", 0.4, 1.3); fx.pts.push({ x: CW / 2, y: 40, n: e.pts, at: now }); } else if (e.kind === "hatch") this.cgSfx("monster", 0.35, 0.9);
      else if (e.kind === "catch") { this.cgSfx(e.foe === "frost" ? "spell" : "coin", 0.5); const [x, y] = pos(L.p.r, L.p.c); fx.pts.push({ x, y: y - 20, n: e.pts, at: now }); }
      else if (e.kind === "drop") this.cgSfx("bump", 0.2, 1.4); else if (e.kind === "die") this.cgSfx("hurt", 0.6); else if (e.kind === "extra") this.cgSfx("cardwin", 0.4);
      else if (e.kind === "clear") { this.cgSfx("tablebell", 0.5); fx.pts.push({ x: CW / 2 - 20, y: 60, n: e.bonus, at: now }); }
    },
    // a cube's top: a rhombus in its colour; a finished one carries a rune
    rpTop(p, x, y, col, rune, s) {
      p.save(); p.translate(x, y); p.scale(s, s); p.fillStyle = col; p.beginPath(); p.moveTo(0, -A / 2); p.lineTo(A, 0); p.lineTo(0, A / 2); p.lineTo(-A, 0); p.closePath(); p.fill(); p.strokeStyle = "rgba(0,0,0,0.35)"; p.stroke();
      p.fillStyle = "rgba(255,255,255,0.2)"; p.beginPath(); p.moveTo(0, -A / 2); p.lineTo(A * 0.6, -A * 0.2); p.lineTo(0, 0); p.lineTo(-A * 0.6, -A * 0.2); p.closePath(); p.fill();
      if (rune) { p.strokeStyle = "rgba(60,30,10,0.6)"; p.lineWidth = 1.5; p.beginPath(); p.moveTo(-6, -2); p.lineTo(0, -6); p.lineTo(6, -2); p.moveTo(0, -6); p.lineTo(0, 6); p.moveTo(-4, 3); p.lineTo(4, 3); p.stroke(); p.lineWidth = 1; }
      p.restore();
    },
    // the glimmerkin: a round glowing body, a tuft, two feet, eyes toward where it hops
    rpHopper(p, x, y, face, s, now) {
      const look = { ul: [-1, -1], ur: [1, -1], dl: [-1, 1], dr: [1, 1] }[face] || [0, 1];
      p.save(); p.translate(x, y); p.scale(s, s); p.fillStyle = "#3A2A10"; p.fillRect(-7, 9, 5, 4); p.fillRect(2, 9, 5, 4);
      p.shadowColor = "#FFC040"; p.shadowBlur = 10; const gr = p.createRadialGradient(-3, -4, 1, 0, 0, 11); gr.addColorStop(0, "#FFF0B0"); gr.addColorStop(1, "#F0A030"); p.fillStyle = gr; p.beginPath(); p.arc(0, 0, 11, 0, Math.PI * 2); p.fill(); p.shadowBlur = 0;
      p.strokeStyle = "#F06030"; p.lineWidth = 2; p.beginPath(); p.moveTo(0, -10); p.quadraticCurveTo(3, -17, 7, -15 + Math.sin(now / 150) * 2); p.stroke(); p.lineWidth = 1;
      for (const ex of [-4, 4]) { p.fillStyle = "#FFF"; p.beginPath(); p.arc(ex + look[0] * 2, -1 + look[1], 3.2, 0, Math.PI * 2); p.fill(); p.fillStyle = "#201010"; p.beginPath(); p.arc(ex + look[0] * 3, -1 + look[1] * 1.6, 1.6, 0, Math.PI * 2); p.fill(); }
      p.restore();
    },
    rpFoe(p, f, x, y, now, frozen) {
      p.save(); p.translate(x, y);
      if (f.kind === "ember") { p.shadowColor = "#FF6030"; p.shadowBlur = 12; p.fillStyle = "#E04020"; p.beginPath(); p.arc(0, 0, 9, 0, Math.PI * 2); p.fill(); p.fillStyle = "#FFB060"; p.beginPath(); p.arc(-3, -3, 3, 0, Math.PI * 2); p.fill(); }
      else if (f.kind === "egg") { p.fillStyle = "#8A50C0"; p.beginPath(); p.ellipse(0, 0, 8, 10, 0, 0, Math.PI * 2); p.fill(); p.fillStyle = "#C0A0F0"; for (const [a, b] of [[-3, -4], [3, 0], [-1, 4]]) p.fillRect(a, b, 2, 2); }
      else if (f.kind === "serpent") { p.strokeStyle = "#8A50C0"; p.lineWidth = 5; p.beginPath(); for (let k = 0; k < 18; k++) { const a = k * 0.9, yy = 10 - k * 1.2; p.lineTo(Math.cos(a) * 6, yy + Math.sin(a) * 2); } p.stroke(); p.lineWidth = 1; p.fillStyle = "#A060E0"; p.beginPath(); p.ellipse(0, -14, 7, 5, 0, 0, Math.PI * 2); p.fill(); p.fillStyle = "#F0E040"; p.fillRect(-4, -16, 2, 2); p.fillRect(2, -16, 2, 2); p.strokeStyle = "#E04040"; p.beginPath(); p.moveTo(0, -10); p.lineTo(0, -6); p.lineTo(-2, -4); p.moveTo(0, -6); p.lineTo(2, -4); p.stroke(); }
      else if (f.kind === "smudge") { p.fillStyle = "#6A6A70"; p.beginPath(); p.ellipse(0, 2, 10, 8, 0, 0, Math.PI * 2); p.fill(); p.fillStyle = "#4A4A50"; p.beginPath(); p.arc(-6, -4, 4, 0, Math.PI * 2); p.arc(5, -5, 5, 0, Math.PI * 2); p.fill(); p.fillStyle = "#FFF"; p.fillRect(-4, 0, 3, 3); p.fillRect(2, 0, 3, 3); }
      else if (f.kind === "frost") { p.shadowColor = "#A0E0FF"; p.shadowBlur = 12; p.fillStyle = "#80D0FF"; p.beginPath(); p.arc(0, 0, 8, 0, Math.PI * 2); p.fill(); p.strokeStyle = "#FFF"; p.beginPath(); for (let k = 0; k < 3; k++) { const a = (k * Math.PI) / 3 + now / 500; p.moveTo(Math.cos(a) * 6, Math.sin(a) * 6); p.lineTo(-Math.cos(a) * 6, -Math.sin(a) * 6); } p.stroke(); }
      if (frozen) { p.shadowBlur = 0; p.fillStyle = "rgba(200,240,255,0.45)"; p.beginPath(); p.arc(0, 0, 12, 0, Math.PI * 2); p.fill(); }
      p.restore();
    },
  });
}
