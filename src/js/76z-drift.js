"use strict";
// Starstone Drift, the window's side (the thirty-third big update): the void through the scrying glass on a canvas - a
// nebula's glow and stars, the starstones as jagged tumbling shapes (amethyst, slate, ember-veined) drawn again across
// the folded edges, the wand-ship with its crystal tip and a flame when it thrusts (a shimmer while it is guarded), its
// sparks, the wraith-lanterns and their red shots, bursts and points; the score, the lives and the wave at the top.
// Left and right (A and D) to turn, up (W) to thrust, Space to fire, down (S) or Shift to blink, P to pause. The rules
// are 64zj-drift.js.
CM.CG_TABLES.push(["starstone", "Starstone Drift"]);
{ const floor0 = CM.UI.prototype.renderFloor, C = 12, TOP = 28;
  const STONE = [["#8A6AB0", "#C8A8F0"], ["#6A7280", "#A8B0C0"], ["#7A4A3A", "#F0A060"]];
  Object.assign(CM.UI.prototype, {
    renderFloor(box) { if (this.cgView === "starstone") return this.cgDrift(box); return floor0.call(this, box); },
    cgDrift(box) {
      const g = this.game, SD = CM.SD, S = g.sdState(), L = g.sdLevel(), live = !!L, bet = live ? S.bet : (this.cgBet === undefined ? 5 : this.cgBet), Cl = g.sdClaimed(), last = S && S.stage === "done" ? S.last : null;
      const top = Math.max(15, (S && live ? S.n : 1) + 4), rows = []; for (let n = 1; n <= top; n++) { const card = n % SD.cardEvery === 0, tier = CM.cardTierFor(n); rows.push(`<div class="rung${live && S.n === n ? " now" : ""}${live && S.n > n ? " done" : ""}"><span>Wave ${n}</span><b>${Math.round(bet * SD.pay(n))}</b><i class="${!card ? "" : Cl[n] ? "got" : tier}" title="${!card ? "" : Cl[n] ? "card already won" : `a ${tier === "better" ? "stronger common" : tier} card, the first time`}">${!card ? "" : Cl[n] ? "✓" : tier === "rare" ? "★" : tier === "better" ? "◆" : "♦"}</i></div>`); }
      box.innerHTML = `<div class="cgtable starstone runestack dash"><h3>Starstone Drift</h3><div class="rswrap"><canvas class="sdcanvas" width="${SD.W * C}" height="${SD.H * C + TOP}" tabindex="0"></canvas>
        <div class="dashside"><p class="lore">In the back room a great scrying glass looks out on a void where starstones drift, and the house's wand-ship floats among them. "Steer it from here," says the attendant, setting your hands on the brass rail. "The stones break small. The lanterns out there shoot back."</p>
        <div class="ladder rsladder">${rows.reverse().join("")}</div>
        ${live ? "" : this.cgBetRow("The stake")}<div class="cgnote">${this.cgNote || ""}</div>${last && last.cards && last.cards.length ? last.cards.map((c) => this.cgCardWon(c)).join("") : ""}
        <div class="row">${live ? `<button data-sdpause>${this.sdPaused ? "Go on" : "Pause"}</button>` : `<button class="primary" data-sdstart>To the glass (${bet} gold)</button>`}<button data-leave>Leave</button></div>
        <div class="small">Left and right (A and D) to turn; up (W) to thrust - the ship drifts on, so mind your speed; Space to fire (four sparks at once); down (S) or Shift to blink somewhere at random; P to pause. The void's edges fold round. Great stones 20, middling 50, small 100; a big wraith-lantern 200, a small one (from wave 4, and it aims) 1,000. Three lives, one more every 10,000. Each wave cleared pays gold, more each, every play; every third wave gives a card the first time ever (♦ wave 3, ◆ 6 and 9, ★ from 12). Best score ${g.cgStore().sdBest || 0}.</div>${this.cgStats("starstone")}</div></div></div>`;
      this.cgWireBet(box); const q = (s) => box.querySelector(s); q("[data-leave]").addEventListener("click", () => this.closeDialogs());
      if (q("[data-sdstart]")) q("[data-sdstart]").addEventListener("click", () => { const r = g.sdStart(bet); this.cgNote = r.error || "Wave 1. Break them up!"; this.sdFx = { parts: [], pts: [], banner: { at: performance.now(), text: "WAVE 1" } }; this.sdPaused = false; this.cgSfx(r.error ? "miss" : "door", 0.45); this.renderCasino(); const cv = this.$("#casino-body .sdcanvas"); if (cv) cv.focus(); });
      if (q("[data-sdpause]")) q("[data-sdpause]").addEventListener("click", () => { this.sdPaused = !this.sdPaused; this.renderCasino(); });
      this.sdCanvas = q(".sdcanvas");
      if (!this.sdKeys) { this.sdHeld = new Set();
        this.sdKeys = (e) => { if (this.cgView !== "starstone" || !this.dialogOpen() || !this.game.sdLevel()) return; if (e.type === "keydown" && e.code === "KeyP") { e.preventDefault(); this.sdPaused = !this.sdPaused; this.renderCasino(); return; }
          const k = { ArrowLeft: "l", KeyA: "l", ArrowRight: "r", KeyD: "r", ArrowUp: "t", KeyW: "t", Space: "f", ArrowDown: "b", KeyS: "b", ShiftLeft: "b", ShiftRight: "b" }[e.code]; if (!k) return; e.preventDefault(); e.stopPropagation();
          if (e.type === "keydown") { if (k === "b" && !e.repeat) this.sdBlink = true; this.sdHeld.add(k); } else this.sdHeld.delete(k); };
        window.addEventListener("keydown", this.sdKeys, true); window.addEventListener("keyup", this.sdKeys, true); }
      if (!this.sdLoop) { let prev = performance.now(); const loop = (now) => { if (!this.sdCanvas || !this.sdCanvas.isConnected || this.cgView !== "starstone") { this.sdLoop = null; return; } const dt = Math.min(0.05, (now - prev) / 1000); prev = now; this.sdFrame(dt, now); this.sdLoop = requestAnimationFrame(loop); }; this.sdLoop = requestAnimationFrame(loop); }
    },
    sdFrame(dt, now) {
      const g = this.game, SD = CM.SD, L = g.sdLevel(), cv = this.sdCanvas, p = cv.getContext("2d"), fx = this.sdFx = this.sdFx || { parts: [], pts: [] }, H = this.sdHeld || new Set();
      if (L && !this.sdPaused) { L.input((H.has("r") ? 1 : 0) - (H.has("l") ? 1 : 0), H.has("t"), H.has("f"), this.sdBlink); this.sdBlink = false; L.update(dt); for (const e of L.events.splice(0)) this.sdEvent(e, now, L); const out = g.sdCheck();
        if (out && out.cleared) { fx.banner = { at: now, text: `WAVE ${out.cleared + 1}`, sub: `Wave ${out.cleared} cleared: +${out.pay} gold${out.card ? ` - ${out.card}` : ""}` }; this.cgSfx("victory", 0.5); if (out.card) setTimeout(() => this.cgSfx("cardwin", 0.5), 300); this.cgNote = `Wave ${out.cleared} cleared: ${out.pay} gold${out.card ? `, and a card - ${out.card}` : ""}.`; this.renderCasino(); return; }
        if (out && out.over) { const S = g.sdState(); this.cgNote = `The wand-ship's light goes out in wave ${S.last.level}. ${S.won} gold back${S.last.cards.length ? `, and ${S.last.cards.length} card${S.last.cards.length > 1 ? "s" : ""}` : ""}.`; this.cgSfx("cardlose", 0.5); this.renderCasino(); if (S.won) this.cgCoins(this.$("#casino-body"), 12); return; } }
      const Lv = L || this.sdLastDrawn; if (L) this.sdLastDrawn = L;
      p.fillStyle = "#04040E"; p.fillRect(0, 0, cv.width, cv.height);
      const neb = p.createRadialGradient(cv.width * 0.7, cv.height * 0.35, 10, cv.width * 0.7, cv.height * 0.35, cv.width * 0.6); neb.addColorStop(0, "rgba(90,40,120,0.35)"); neb.addColorStop(0.5, "rgba(30,40,100,0.15)"); neb.addColorStop(1, "rgba(0,0,0,0)"); p.fillStyle = neb; p.fillRect(0, TOP, cv.width, cv.height - TOP);
      { const n2 = p.createRadialGradient(cv.width * 0.2, cv.height * 0.75, 10, cv.width * 0.2, cv.height * 0.75, cv.width * 0.4); n2.addColorStop(0, "rgba(40,110,120,0.22)"); n2.addColorStop(1, "rgba(0,0,0,0)"); p.fillStyle = n2; p.fillRect(0, TOP, cv.width, cv.height - TOP);
        const px = cv.width * 0.12, py = TOP + 46; p.fillStyle = "#6A5A8A"; p.beginPath(); p.arc(px, py, 14, 0, Math.PI * 2); p.fill(); p.fillStyle = "rgba(255,255,255,0.15)"; p.beginPath(); p.arc(px - 4, py - 4, 8, 0, Math.PI * 2); p.fill(); p.strokeStyle = "rgba(220,200,255,0.55)"; p.lineWidth = 2; p.beginPath(); p.ellipse(px, py, 24, 6, -0.3, 0, Math.PI * 2); p.stroke(); p.lineWidth = 1; }
      for (let k = 0; k < 90; k++) { p.fillStyle = k % 7 ? "#7080B0" : "#F0E0C0"; p.globalAlpha = 0.35 + 0.35 * Math.abs(Math.sin(now / 900 + k * 1.7)); p.fillRect((k * 151) % cv.width, TOP + ((k * 89) % (cv.height - TOP)), k % 9 ? 1 : 2, k % 9 ? 1 : 2); } p.globalAlpha = 1;
      p.fillStyle = "#0C0A18"; p.fillRect(0, 0, cv.width, TOP); p.fillStyle = "#FFE070"; p.font = "bold 14px monospace"; p.fillText(Lv ? `SCORE ${Lv.score}` : "STARSTONE DRIFT", 8, 19);
      if (Lv) { p.fillText(`WAVE ${Lv.n}`, cv.width / 2 - 26, 19); for (let k = 0; k < Math.min(6, Lv.lives); k++) this.sdShip(p, cv.width - 14 - k * 16, 14, -Math.PI / 2, 0.6, false, now); }
      if (!Lv) { p.fillStyle = "rgba(255,240,200,0.9)"; p.font = "bold 24px Georgia, serif"; p.textAlign = "center"; p.fillText("Starstone Drift", cv.width / 2, cv.height / 2); p.textAlign = "left"; return; }
      p.save(); p.beginPath(); p.rect(0, TOP, cv.width, cv.height - TOP); p.clip(); p.translate(0, TOP);
      // things near an edge are drawn again on the far side, so they slide across the fold
      const around = (o, r, draw) => { for (const ox of [0, -SD.W, SD.W]) for (const oy of [0, -SD.H, SD.H]) { const x = o.x + ox, y = o.y + oy; if (x + r < 0 || x - r > SD.W || y + r < 0 || y - r > SD.H) continue; draw(x * C, y * C); } };
      for (const s of Lv.stones) { const r = SD.SIZES[s.size].r, [body, edge] = STONE[s.kind]; around(s, r, (X, Y) => { p.save(); p.translate(X, Y); p.rotate(s.rot); p.beginPath(); s.shape.forEach((k, i) => { const a = (i / s.shape.length) * Math.PI * 2, R2 = r * C * k; if (i) p.lineTo(Math.cos(a) * R2, Math.sin(a) * R2); else p.moveTo(Math.cos(a) * R2, Math.sin(a) * R2); }); p.closePath(); p.fillStyle = body; p.fill(); p.strokeStyle = edge; p.lineWidth = 1.5; p.stroke();
        p.fillStyle = "rgba(0,0,0,0.25)"; p.beginPath(); p.arc(r * C * 0.25, r * C * 0.2, r * C * 0.22, 0, Math.PI * 2); p.fill(); if (s.kind === 2) { p.strokeStyle = "#F0A060"; p.beginPath(); p.moveTo(-r * C * 0.5, -r * C * 0.1); p.lineTo(0, r * C * 0.15); p.lineTo(r * C * 0.4, -r * C * 0.3); p.stroke(); } p.restore(); }); }
      if (Lv.wraith) { const W = Lv.wraith, K = SD.WRAITH[W.kind]; around(W, K.r * 2, (X, Y) => this.sdWraith(p, X, Y, K.r * C, now)); }
      for (const b of Lv.bolts) around(b, 0.3, (X, Y) => { p.fillStyle = "#A0F8FF"; p.shadowColor = "#80F0FF"; p.shadowBlur = 8; p.beginPath(); p.arc(X, Y, 2.2, 0, Math.PI * 2); p.fill(); p.shadowBlur = 0; });
      for (const s of Lv.shots) around(s, 0.3, (X, Y) => { p.fillStyle = "#FF6050"; p.beginPath(); p.arc(X, Y, 2.4, 0, Math.PI * 2); p.fill(); });
      const Sh = Lv.ship; if (!Sh.dead && (Sh.guard <= 0 || Math.floor(now / 90) % 2)) around(Sh, 1.5, (X, Y) => this.sdShip(p, X, Y, Sh.a, 1, Sh.thrusting, now));
      if (!Sh.dead && Sh.guard > 0) { p.strokeStyle = `rgba(160,240,255,${0.3 + 0.2 * Math.sin(now / 80)})`; p.beginPath(); p.arc(Sh.x * C, Sh.y * C, 14, 0, Math.PI * 2); p.stroke(); }
      fx.parts = fx.parts.filter((q) => (q.life -= dt) > 0); for (const q of fx.parts) { q.x += q.vx * dt; q.y += q.vy * dt; p.globalAlpha = Math.min(1, q.life * 2); p.fillStyle = q.c; p.fillRect(q.x - 1.5, q.y - 1.5, 3, 3); } p.globalAlpha = 1;
      fx.pts = fx.pts.filter((q) => now - q.at < 800); for (const q of fx.pts) { p.globalAlpha = 1 - (now - q.at) / 800; p.fillStyle = "#FFF0B0"; p.font = "bold 11px monospace"; p.fillText(String(q.n), q.x - 8, q.y - (now - q.at) / 40); } p.globalAlpha = 1;
      p.restore();
      if (fx.banner && now - fx.banner.at < 2600) { const B = fx.banner, t = (now - B.at) / 2600; p.globalAlpha = t > 0.8 ? (1 - t) / 0.2 : 1; p.fillStyle = "#C0E8FF"; p.font = "bold 26px Georgia, serif"; p.textAlign = "center"; p.fillText(B.text, cv.width / 2, cv.height / 2 + 50); if (B.sub) { p.font = "14px Georgia, serif"; p.fillStyle = "#F0E0B0"; p.fillText(B.sub, cv.width / 2, cv.height / 2 + 18); } p.textAlign = "left"; p.globalAlpha = 1; }
      if (this.sdPaused) { p.fillStyle = "rgba(0,0,0,0.6)"; p.fillRect(0, 0, cv.width, cv.height); p.fillStyle = "#FFF"; p.font = "bold 26px Georgia, serif"; p.textAlign = "center"; p.fillText("Paused", cv.width / 2, cv.height / 2); p.textAlign = "left"; }
    },
    sdEvent(e, now, L) {
      const fx = this.sdFx, burst = (x, y, cols, n, sp = 120) => { for (let k = 0; k < n; k++) { const a = Math.random() * Math.PI * 2, v = 20 + Math.random() * sp; fx.parts.push({ x: x * C, y: y * C, vx: Math.cos(a) * v, vy: Math.sin(a) * v, life: 0.4 + Math.random() * 0.5, c: cols[k % cols.length] }); } };
      if (e.kind === "fire") this.cgSfx("zap", 0.18, 1.9);
      else if (e.kind === "split") { this.cgSfx("slam", 0.25 + e.s.size * 0.08, 1.6 - e.s.size * 0.25); burst(e.s.x, e.s.y, STONE[e.s.kind], 6 + e.s.size * 5); if (e.pts) fx.pts.push({ x: e.s.x * C, y: e.s.y * C, n: e.pts, at: now }); }
      else if (e.kind === "wraith") this.cgSfx("monster", 0.3, e.w === "small" ? 1.7 : 1.1); else if (e.kind === "wfire") this.cgSfx("wandboom", 0.12, 2);
      else if (e.kind === "wraithdown") { this.cgSfx("shatter", 0.5, 0.9); burst(e.x, e.y, ["#F0D070", "#80F0C0", "#FFFFFF"], 24); if (e.pts) fx.pts.push({ x: e.x * C, y: e.y * C, n: e.pts, at: now }); }
      else if (e.kind === "blink") { this.cgSfx("spell", 0.35, 1.6); burst(L.ship.x, L.ship.y, ["#C0F0FF", "#FFFFFF"], 14, 60); }
      else if (e.kind === "die") { this.cgSfx("hurt", 0.6); burst(e.x, e.y, ["#FFE070", "#80F0FF", "#F06030", "#FFFFFF"], 34, 160); }
      else if (e.kind === "extra") this.cgSfx("cardwin", 0.4);
    },
    // the wand-ship: a slim wand body, a crystal at the tip, two little fins, a flame when it thrusts
    sdShip(p, X, Y, a, s, thrust, now) {
      p.save(); p.translate(X, Y); p.rotate(a); p.scale(s * 1.4, s * 1.4);
      if (thrust) { p.fillStyle = Math.floor(now / 50) % 2 ? "#FFB040" : "#FFE080"; p.beginPath(); p.moveTo(-8, -3); p.lineTo(-15 - Math.random() * 4, 0); p.lineTo(-8, 3); p.closePath(); p.fill(); }
      p.fillStyle = "#8A5A2A"; p.beginPath(); p.moveTo(-9, -2.5); p.lineTo(6, -1.5); p.lineTo(6, 1.5); p.lineTo(-9, 2.5); p.closePath(); p.fill();
      p.fillStyle = "#C0C8E0"; p.beginPath(); p.moveTo(-6, -2); p.lineTo(-10, -7); p.lineTo(-3, -2); p.closePath(); p.moveTo(-6, 2); p.lineTo(-10, 7); p.lineTo(-3, 2); p.closePath(); p.fill();
      p.fillStyle = "#A0F0FF"; p.shadowColor = "#80F0FF"; p.shadowBlur = 8; p.beginPath(); p.moveTo(6, -3.5); p.lineTo(12, 0); p.lineTo(6, 3.5); p.closePath(); p.fill(); p.restore();
    },
    // a wraith-lantern: a ghostly hood round a lantern, wisps trailing
    sdWraith(p, X, Y, r, now) {
      p.save(); p.translate(X, Y); p.fillStyle = "rgba(200,240,220,0.35)"; p.beginPath(); p.arc(0, -r * 0.2, r * 1.5, Math.PI, 0); for (let k = 0; k <= 6; k++) p.lineTo(r * 1.5 - (k * r * 3) / 6, r * 0.8 + (k % 2 ? 4 : 0) + Math.sin(now / 120 + k) * 2); p.closePath(); p.fill();
      p.fillStyle = "#4A3A20"; p.fillRect(-r * 0.6, -r * 0.9, r * 1.2, r * 0.25); p.fillStyle = "#F0D070"; p.shadowColor = "#F0D070"; p.shadowBlur = 12; p.fillRect(-r * 0.45, -r * 0.6, r * 0.9, r * 1.1); p.shadowBlur = 0; p.fillStyle = "#4A3A20"; p.fillRect(-r * 0.6, r * 0.45, r * 1.2, r * 0.25);
      p.fillStyle = "#203040"; p.fillRect(-r * 0.25, -r * 0.2, r * 0.15, r * 0.2); p.fillRect(r * 0.1, -r * 0.2, r * 0.15, r * 0.2); p.restore();
    },
  });
}
