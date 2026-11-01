"use strict";
// Moatleap, the window's side (the thirty-fourth big update): the crossing on a canvas - the castle wall along the top
// with its five lily-bays (a toad sitting in each one filled, a firefly's glow or a pike's jaws in an empty one), the
// moat with its ripples, logs with their rings and lily-turtles (sinking ones going pale, then gone under), the grass
// verge, the cobbled market road with handcarts, hay wagons, galloping riders and ox-trains, the near bank; the toad
// with its hop and a splash or a squash; the score, the lives, the level and the time left. Arrows or W A S D to hop,
// P to pause. The rules are 64zk-moat.js.
CM.CG_TABLES.push(["moatleap", "Moatleap"]);
{ const floor0 = CM.UI.prototype.renderFloor, C = 32, TOP = 28;
  Object.assign(CM.UI.prototype, {
    renderFloor(box) { if (this.cgView === "moatleap") return this.cgMoat(box); return floor0.call(this, box); },
    cgMoat(box) {
      const g = this.game, MQ = CM.MQ, S = g.mqState(), L = g.mqLevel(), live = !!L, bet = live ? S.bet : (this.cgBet === undefined ? 5 : this.cgBet), Cl = g.mqClaimed(), last = S && S.stage === "done" ? S.last : null;
      const top = Math.max(15, (S && live ? S.n : 1) + 4), rows = []; for (let n = 1; n <= top; n++) { const card = n % MQ.cardEvery === 0, tier = CM.cardTierFor(n); rows.push(`<div class="rung${live && S.n === n ? " now" : ""}${live && S.n > n ? " done" : ""}"><span>Level ${n}</span><b>${Math.round(bet * MQ.pay(n))}</b><i class="${!card ? "" : Cl[n] ? "got" : tier}" title="${!card ? "" : Cl[n] ? "card already won" : `a ${tier === "better" ? "stronger common" : tier} card, the first time`}">${!card ? "" : Cl[n] ? "✓" : tier === "rare" ? "★" : tier === "better" ? "◆" : "♦"}</i></div>`); }
      box.innerHTML = `<div class="cgtable moatleap runestack dash"><h3>Moatleap</h3><div class="rswrap"><canvas class="mqcanvas" width="${MQ.W * C}" height="${MQ.H * C + TOP}" tabindex="0"></canvas>
        <div class="dashside"><p class="lore">Out past the Joker's back gate runs the market road, and past that the old castle's moat. The house keeps toads, and wagers on them. "Five bays under the wall," says the attendant. "Get a toad into every one. Mind the wagons, and the turtles - some of them dive."</p>
        <div class="ladder rsladder">${rows.reverse().join("")}</div>
        ${live ? "" : this.cgBetRow("The stake")}<div class="cgnote">${this.cgNote || ""}</div>${last && last.cards && last.cards.length ? last.cards.map((c) => this.cgCardWon(c)).join("") : ""}
        <div class="row">${live ? `<button data-mqpause>${this.mqPaused ? "Go on" : "Pause"}</button>` : `<button class="primary" data-mqstart>To the road (${bet} gold)</button>`}<button data-leave>Leave</button></div>
        <div class="small">Arrows or W A S D to hop one square; P to pause. Across the road without being run down; across the moat only on logs and lily-turtles (those going pale are about to dive - from level 2), and don't ride off the edge. Into an empty bay - not the wall, not a full bay, not a pike's jaws (from level 3). Thirty seconds a toad. 10 a step forward, 50 a toad home and 10 for each second left, 200 for a firefly, 1,000 for all five bays. Three lives, one more at 10,000. Each level cleared pays gold, more each, every play; every third level gives a card the first time ever (♦ level 3, ◆ 6 and 9, ★ from 12). Best score ${g.cgStore().mqBest || 0}.</div>${this.cgStats("moatleap")}</div></div></div>`;
      this.cgWireBet(box); const q = (s) => box.querySelector(s); q("[data-leave]").addEventListener("click", () => this.closeDialogs());
      if (q("[data-mqstart]")) q("[data-mqstart]").addEventListener("click", () => { const r = g.mqStart(bet); this.cgNote = r.error || "Level 1. Hop to it!"; this.mqFx = { parts: [], pts: [], banner: { at: performance.now(), text: "LEVEL 1" } }; this.mqPaused = false; this.cgSfx(r.error ? "miss" : "door", 0.45); this.renderCasino(); const cv = this.$("#casino-body .mqcanvas"); if (cv) cv.focus(); });
      if (q("[data-mqpause]")) q("[data-mqpause]").addEventListener("click", () => { this.mqPaused = !this.mqPaused; this.renderCasino(); });
      this.mqCanvas = q(".mqcanvas");
      if (!this.mqKeys) {
        this.mqKeys = (e) => { if (this.cgView !== "moatleap" || !this.dialogOpen() || !this.game.mqLevel()) return; if (e.code === "KeyP") { e.preventDefault(); this.mqPaused = !this.mqPaused; this.renderCasino(); return; }
          const d = { ArrowUp: "up", KeyW: "up", ArrowDown: "down", KeyS: "down", ArrowLeft: "left", KeyA: "left", ArrowRight: "right", KeyD: "right" }[e.code]; if (!d) return; e.preventDefault(); e.stopPropagation(); if (!e.repeat && !this.mqPaused) this.game.mqLevel().input(d); };
        window.addEventListener("keydown", this.mqKeys, true); }
      if (!this.mqLoop) { let prev = performance.now(); const loop = (now) => { if (!this.mqCanvas || !this.mqCanvas.isConnected || this.cgView !== "moatleap") { this.mqLoop = null; return; } const dt = Math.min(0.05, (now - prev) / 1000); prev = now; this.mqFrame(dt, now); this.mqLoop = requestAnimationFrame(loop); }; this.mqLoop = requestAnimationFrame(loop); }
    },
    mqFrame(dt, now) {
      const g = this.game, MQ = CM.MQ, L = g.mqLevel(), cv = this.mqCanvas, p = cv.getContext("2d"), fx = this.mqFx = this.mqFx || { parts: [], pts: [] };
      if (L && !this.mqPaused) { L.update(dt); for (const e of L.events.splice(0)) this.mqEvent(e, now, L); const out = g.mqCheck();
        if (out && out.cleared) { fx.banner = { at: now, text: `LEVEL ${out.cleared + 1}`, sub: `Level ${out.cleared} cleared: +${out.pay} gold${out.card ? ` - ${out.card}` : ""}` }; this.cgSfx("victory", 0.5); if (out.card) setTimeout(() => this.cgSfx("cardwin", 0.5), 300); this.cgNote = `Level ${out.cleared} cleared: ${out.pay} gold${out.card ? `, and a card - ${out.card}` : ""}.`; this.renderCasino(); return; }
        if (out && out.over) { const S = g.mqState(); this.cgNote = `The last toad croaks on level ${S.last.level}. ${S.won} gold back${S.last.cards.length ? `, and ${S.last.cards.length} card${S.last.cards.length > 1 ? "s" : ""}` : ""}.`; this.cgSfx("cardlose", 0.5); this.renderCasino(); if (S.won) this.cgCoins(this.$("#casino-body"), 12); return; } }
      const Lv = L || this.mqLastDrawn; if (L) this.mqLastDrawn = L;
      p.fillStyle = "#101810"; p.fillRect(0, 0, cv.width, TOP); p.fillStyle = "#FFE070"; p.font = "bold 14px monospace"; p.fillText(Lv ? `SCORE ${Lv.score}` : "MOATLEAP", 8, 19);
      if (Lv) { p.fillText(`LEVEL ${Lv.n}`, cv.width / 2 - 30, 19); for (let k = 0; k < Math.min(6, Lv.lives); k++) this.mqToad(p, cv.width - 14 - k * 18, 14, "up", 0.45, 0); }
      p.save(); p.translate(0, TOP); const W = cv.width;
      // the ground: wall, moat, verge, road, bank
      p.fillStyle = "#5A5048"; p.fillRect(0, 0, W, C); for (let x = 0; x < W; x += 16) { p.fillStyle = (x / 16) % 2 ? "#4A4038" : "#6A6058"; p.fillRect(x, 2, 15, 12); p.fillRect(x + 8, 16, 15, 12); }
      for (const bx of [MQ.BAYS[1] * C + C + 18, MQ.BAYS[3] * C - 18]) { p.fillStyle = "#4A3A20"; p.fillRect(bx, 1, 2, 20); const wv = Math.sin(now / 200 + bx) * 2; p.fillStyle = "#A02838"; p.beginPath(); p.moveTo(bx + 2, 2); p.lineTo(bx + 14, 5 + wv); p.lineTo(bx + 2, 11); p.closePath(); p.fill(); p.fillStyle = "#F0C040"; p.fillRect(bx + 5, 5, 3, 3); }
      p.fillStyle = "#1E4A78"; p.fillRect(0, C, W, 5 * C); p.strokeStyle = "rgba(160,210,255,0.25)"; for (let k = 0; k < 24; k++) { const x = (k * 71 + now / 30) % W, y = C + ((k * 37) % (5 * C)); p.beginPath(); p.moveTo(x, y); p.quadraticCurveTo(x + 6, y - 3, x + 12, y); p.stroke(); }
      for (let k = 0; k < 10; k++) { const x = (k * 97 + 30) % W, y = C + 8 + ((k * 61) % (5 * C - 16)), gl = Math.max(0, Math.sin(now / 400 + k * 2)); if (gl > 0.7) { p.fillStyle = `rgba(255,255,230,${(gl - 0.7) * 2.5})`; p.fillRect(x, y, 6, 1); p.fillRect(x + 2, y - 1, 2, 3); } }
      for (const [lx, ly] of [[18, C + 12], [W - 26, C * 3 + 10], [40, C * 5 + 14], [W - 60, C + 20]]) { p.fillStyle = "#3A7A3A"; p.beginPath(); p.arc(lx, ly, 7, 0.4, Math.PI * 2); p.lineTo(lx, ly); p.fill(); p.fillStyle = "#F0A0C0"; p.beginPath(); p.arc(lx + 2, ly - 1, 2, 0, Math.PI * 2); p.fill(); }
      p.strokeStyle = "#5A7A30"; p.lineWidth = 2; for (let k = 0; k < 14; k++) { const x = (k * 53 + 7) % W, sw = Math.sin(now / 600 + k) * 2; p.beginPath(); p.moveTo(x, MQ.VERGE * C); p.quadraticCurveTo(x + sw, MQ.VERGE * C - 6, x + sw * 1.6, MQ.VERGE * C - 11); p.stroke(); } p.lineWidth = 1;
      p.fillStyle = "#3A7A30"; p.fillRect(0, MQ.VERGE * C, W, C); p.fillStyle = "#4A8A3A"; for (let x = 4; x < W; x += 11) p.fillRect(x, MQ.VERGE * C + 4 + (x % 3) * 6, 2, 6);
      p.fillStyle = "#3A3632"; p.fillRect(0, (MQ.VERGE + 1) * C, W, 5 * C); p.fillStyle = "#4A4640"; for (let r = 0; r < 5; r++) for (let x = (r % 2) * 10; x < W; x += 20) p.fillRect(x + 1, (MQ.VERGE + 1 + r) * C + 6, 16, 8); p.fillStyle = "rgba(240,220,160,0.35)"; for (let r = 1; r < 5; r++) for (let x = 6; x < W; x += 30) p.fillRect(x, (MQ.VERGE + 1 + r) * C - 1, 14, 2);
      p.fillStyle = "#3A7A30"; p.fillRect(0, MQ.START * C, W, C);
      if (!Lv) { p.restore(); p.fillStyle = "rgba(255,240,200,0.9)"; p.font = "bold 24px Georgia, serif"; p.textAlign = "center"; p.fillText("Moatleap", cv.width / 2, cv.height / 2); p.textAlign = "left"; return; }
      // the bays
      MQ.BAYS.forEach((b, k) => { const X = b * C, Y = 0; p.fillStyle = "#1E4A78"; p.fillRect(X + 2, Y + 4, C - 4, C - 4); p.fillStyle = "#3A8A3A"; p.beginPath(); p.arc(X + C / 2, Y + C / 2 + 2, 11, 0.3, Math.PI * 2 - 0.3); p.lineTo(X + C / 2, Y + C / 2 + 2); p.fill();
        if (Lv.bays[k]) this.mqToad(p, X + C / 2, Y + C / 2 + 2, "down", 0.8, 0);
        else if (Lv.fly && Lv.fly.bay === k) { p.save(); p.shadowColor = "#F0F080"; p.shadowBlur = 14; p.fillStyle = "#F8F8A0"; p.beginPath(); p.arc(X + C / 2 + Math.sin(now / 150) * 4, Y + C / 2, 3, 0, Math.PI * 2); p.fill(); p.restore(); }
        else if (Lv.pike && Lv.pike.bay === k) { p.fillStyle = "#5A6A4A"; p.beginPath(); p.moveTo(X + 4, Y + C / 2); p.lineTo(X + C - 6, Y + 8); p.lineTo(X + C - 6, Y + C - 4); p.closePath(); p.fill(); p.fillStyle = "#F0F0E0"; for (let k2 = 0; k2 < 4; k2++) p.fillRect(X + 10 + k2 * 4, Y + C / 2 - 2 + (k2 % 2) * 2, 2, 3); p.fillStyle = "#F0D040"; p.fillRect(X + C - 12, Y + 12, 3, 3); } });
      // the lanes' things
      for (const l of Lv.lanes) for (const th of l.things) { const a = Lv.left(l, th), X = a * C, Y = l.row * C;
        if (l.kind === "log") { p.fillStyle = "#7A5230"; p.fillRect(X + 2, Y + 6, l.len * C - 4, C - 12); p.fillStyle = "#9A6A40"; p.fillRect(X + 2, Y + 7, l.len * C - 4, 3); p.fillStyle = "#C09060"; p.beginPath(); p.ellipse(X + 4, Y + C / 2, 3, (C - 12) / 2, 0, 0, Math.PI * 2); p.fill(); p.strokeStyle = "#7A5230"; p.beginPath(); p.ellipse(X + 4, Y + C / 2, 1.5, 4, 0, 0, Math.PI * 2); p.stroke(); }
        else if (l.kind === "turtle") { if (Lv.under(th)) { p.strokeStyle = "rgba(160,210,255,0.5)"; for (let k = 0; k < l.len; k++) { p.beginPath(); p.arc(X + k * C + C / 2, Y + C / 2, 6 + (now / 60) % 6, 0, Math.PI * 2); p.stroke(); } continue; }
          const sink = Lv.sinking(th); for (let k = 0; k < l.len; k++) { const cx = X + k * C + C / 2, cy = Y + C / 2; p.globalAlpha = sink ? 0.45 + 0.25 * Math.sin(now / 60) : 1; p.fillStyle = "#3A6A30"; p.beginPath(); p.arc(cx + l.dir * 10, cy, 4, 0, Math.PI * 2); p.fill(); p.fillStyle = sink ? "#7AAA70" : "#4A8A3A"; p.beginPath(); p.ellipse(cx, cy, 11, 10, 0, 0, Math.PI * 2); p.fill(); p.strokeStyle = "#2A5A20"; p.beginPath(); p.moveTo(cx - 6, cy); p.lineTo(cx + 6, cy); p.moveTo(cx, cy - 6); p.lineTo(cx, cy + 6); p.stroke(); p.fillStyle = "#F07090"; p.beginPath(); p.arc(cx - 3, cy - 3, 2.5, 0, Math.PI * 2); p.fill(); p.globalAlpha = 1; } }
        else this.mqCart(p, l.kind, X, Y, l.len, l.dir, now); }
      // the toad
      const T = Lv.toad; if (!T.dead) { const hopK = T.hopT > 0 ? Math.sin((1 - T.hopT / MQ.hop) * Math.PI) : 0, [dx, dy] = { up: [0, 1], down: [0, -1], left: [1, 0], right: [-1, 0] }[T.face], back = T.hopT > 0 ? T.hopT / MQ.hop : 0; this.mqToad(p, (T.x + dx * back) * C + C / 2, (T.y + dy * back) * C + C / 2 - hopK * 6, T.face, 1 + hopK * 0.2, hopK); }
      else if (T.why) { const X = T.x * C + C / 2, Y = T.y * C + C / 2; if (T.why === "water" || T.why === "edge") { p.strokeStyle = "rgba(200,230,255,0.8)"; p.beginPath(); p.arc(X, Y, 14 * (1.6 - T.dead), 0, Math.PI * 2); p.stroke(); } else { p.fillStyle = "#4A8A3A"; p.beginPath(); p.ellipse(X, Y, 14, 5, 0, 0, Math.PI * 2); p.fill(); p.fillStyle = "#FFE070"; p.font = "bold 16px Georgia"; p.fillText("✶", X - 6, Y - 8); } }
      // time left
      const tl = Math.max(0, T.time / MQ.time); p.fillStyle = "#101810"; p.fillRect(0, MQ.START * C + C - 5, W, 5); p.fillStyle = tl < 0.25 ? "#F05040" : "#F0D060"; p.fillRect(0, MQ.START * C + C - 5, W * tl, 5);
      fx.parts = fx.parts.filter((q) => (q.life -= dt) > 0); for (const q of fx.parts) { q.x += q.vx * dt; q.y += q.vy * dt; q.vy += 300 * dt; p.globalAlpha = Math.min(1, q.life * 2); p.fillStyle = q.c; p.fillRect(q.x - 1.5, q.y - 1.5, 3, 3); } p.globalAlpha = 1;
      fx.pts = fx.pts.filter((q) => now - q.at < 900); for (const q of fx.pts) { p.globalAlpha = 1 - (now - q.at) / 900; p.fillStyle = "#FFF0B0"; p.font = "bold 12px monospace"; p.fillText(String(q.n), q.x - 10, q.y - (now - q.at) / 40); } p.globalAlpha = 1;
      p.restore();
      if (fx.banner && now - fx.banner.at < 2600) { const B = fx.banner, t = (now - B.at) / 2600; p.globalAlpha = t > 0.8 ? (1 - t) / 0.2 : 1; p.fillStyle = "rgba(0,0,0,0.6)"; p.fillRect(0, TOP + MQ.VERGE * C - 22, cv.width, 76); p.fillStyle = "#E0FFC0"; p.font = "bold 26px Georgia, serif"; p.textAlign = "center"; p.fillText(B.text, cv.width / 2, TOP + MQ.VERGE * C + 40); if (B.sub) { p.font = "14px Georgia, serif"; p.fillStyle = "#F0E0B0"; p.fillText(B.sub, cv.width / 2, TOP + MQ.VERGE * C); } p.textAlign = "left"; p.globalAlpha = 1; }
      if (this.mqPaused) { p.fillStyle = "rgba(0,0,0,0.6)"; p.fillRect(0, 0, cv.width, cv.height); p.fillStyle = "#FFF"; p.font = "bold 26px Georgia, serif"; p.textAlign = "center"; p.fillText("Paused", cv.width / 2, cv.height / 2); p.textAlign = "left"; }
    },
    mqEvent(e, now, L) {
      const fx = this.mqFx, MQ = CM.MQ;
      if (e.kind === "hop") this.cgSfx("step", 0.25, 1.6);
      else if (e.kind === "home") { this.cgSfx("coin", 0.5); fx.pts.push({ x: MQ.BAYS[e.bay] * C + 10, y: C, n: e.pts, at: now }); }
      else if (e.kind === "fly") this.cgSfx("cardwin", 0.35); else if (e.kind === "pike") this.cgSfx("monster", 0.25, 1.2); else if (e.kind === "extra") this.cgSfx("cardwin", 0.4);
      else if (e.kind === "die") { const X = e.x * C + C / 2, Y = e.y * C + C / 2, wet = e.why === "water" || e.why === "edge"; this.cgSfx(wet ? "splash" : e.why === "time" ? "miss" : "hurt", 0.55); for (let k = 0; k < 14; k++) fx.parts.push({ x: X, y: Y, vx: (Math.random() - 0.5) * 140, vy: -Math.random() * 160, life: 0.6, c: wet ? (k % 2 ? "#A0D0FF" : "#FFFFFF") : (k % 2 ? "#4A8A3A" : "#F0E060") }); }
    },
    // the toad: a squat green body, golden eyes, legs tucked (spread mid-hop), turned the way it faces
    mqToad(p, X, Y, face, s, spread) {
      p.save(); p.translate(X, Y); p.rotate({ up: 0, right: Math.PI / 2, down: Math.PI, left: -Math.PI / 2 }[face]); p.scale(s, s);
      p.fillStyle = "#2E6A2A"; const lg = 4 + spread * 5; p.fillRect(-11, 2, 5, lg); p.fillRect(6, 2, 5, lg); p.fillRect(-10, -8 - spread * 3, 4, 5); p.fillRect(6, -8 - spread * 3, 4, 5);
      p.fillStyle = "#5AAA40"; p.beginPath(); p.ellipse(0, 0, 9, 10, 0, 0, Math.PI * 2); p.fill(); p.fillStyle = "#7ACA58"; p.beginPath(); p.ellipse(0, 2, 5, 5, 0, 0, Math.PI * 2); p.fill();
      p.fillStyle = "#F0D040"; p.beginPath(); p.arc(-4, -7, 3, 0, Math.PI * 2); p.arc(4, -7, 3, 0, Math.PI * 2); p.fill(); p.fillStyle = "#101010"; p.fillRect(-5, -8, 2, 2); p.fillRect(3, -8, 2, 2); p.restore();
    },
    // the road's traffic: handcarts, hay wagons, galloping riders, ox-trains
    mqCart(p, kind, X, Y, len, dir, now) {
      const w = len * C, cy = Y + C / 2; p.save(); p.translate(X + w / 2, cy); p.scale(dir, 1); const x0 = -w / 2;
      if (kind === "cart") { p.fillStyle = "#8A5A2A"; p.fillRect(x0 + 4, -8, w - 10, 12); p.fillStyle = "#C08040"; p.fillRect(x0 + 6, -10, w - 14, 4); p.fillStyle = "#3A2A1A"; p.beginPath(); p.arc(x0 + 10, 6, 4, 0, Math.PI * 2); p.arc(x0 + w - 10, 6, 4, 0, Math.PI * 2); p.fill(); p.fillStyle = "#6A4A2A"; p.fillRect(x0 + w - 6, -2, 6, 2); }
      else if (kind === "wagon") { p.fillStyle = "#6A4A2A"; p.fillRect(x0 + 4, -6, w - 14, 12); p.fillStyle = "#E0C060"; p.beginPath(); p.ellipse(x0 + w / 2 - 4, -8, w / 2 - 8, 8, 0, Math.PI, 0); p.fill(); p.fillStyle = "#3A2A1A"; for (const k of [0.2, 0.75]) { p.beginPath(); p.arc(x0 + w * k, 8, 5, 0, Math.PI * 2); p.fill(); } p.fillStyle = "#8A6A4A"; p.fillRect(x0 + w - 12, -4, 10, 8); }
      else if (kind === "rider") { const g = Math.sin(now / 50) * 3; p.fillStyle = "#6A3A1A"; p.fillRect(x0 + 4, -6, w - 8, 9); p.fillRect(x0 + w - 8, -12, 6, 8); p.fillStyle = "#4A2A10"; p.fillRect(x0 + 6, 3, 3, 7 + g); p.fillRect(x0 + w - 10, 3, 3, 7 - g); p.fillStyle = "#A03030"; p.fillRect(x0 + 10, -15, 7, 10); p.fillStyle = "#F0C8A0"; p.fillRect(x0 + 11, -20, 5, 5); }
      else { for (let k = 0; k < len; k++) { const ox = x0 + k * C; if (k === len - 1) { p.fillStyle = "#8A7A6A"; p.fillRect(ox + 4, -8, C - 10, 14); p.fillStyle = "#E0D8C8"; p.fillRect(ox + C - 8, -10, 3, 4); p.fillRect(ox + C - 8, 4, 3, 4); } else { p.fillStyle = "#7A5A3A"; p.fillRect(ox + 2, -10, C - 4, 18); p.fillStyle = "#5A3A1A"; p.fillRect(ox + 2, -10, C - 4, 3); p.fillStyle = "#3A2A1A"; p.beginPath(); p.arc(ox + C / 2, 9, 4, 0, Math.PI * 2); p.fill(); } } }
      p.restore();
    },
  });
}
