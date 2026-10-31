"use strict";
// The Gloomwing Swarm, the window's side (the thirtieth big update): a night sky of drifting stars on a canvas; the
// lantern-skiff (two side by side once one is freed), its mana bolts; Mites, Moths and the armoured Wardens with their
// wings beating, turned along their flight when they swoop, a dented Warden's shell gone blue; the binding beam, a
// captive skiff above its Warden, the embers, bursts and points; the stage's banner, the Bonus Flight's tally; the score,
// the lives and the stage at the top. Left and right (or A and D) to slide, Space to fire (hold for a steady stream), P
// to pause. The rules are 64zg-swarm.js.
CM.CG_TABLES.push(["swarm", "The Gloomwing Swarm"]);
{ const floor0 = CM.UI.prototype.renderFloor, C = 16, TOP = 28;
  Object.assign(CM.UI.prototype, {
    renderFloor(box) { if (this.cgView === "swarm") return this.cgSwarm(box); return floor0.call(this, box); },
    cgSwarm(box) {
      const g = this.game, SW = CM.SW, S = g.swState(), L = g.swLevel(), live = !!L, bet = live ? S.bet : (this.cgBet === undefined ? 5 : this.cgBet), Cl = g.swClaimed(), last = S && S.stage === "done" ? S.last : null;
      const top = Math.max(20, (S && live ? S.n : 1) + 4), rows = []; for (let n = 1; n <= top; n++) { const card = SW.CARDS.includes(n), tier = CM.cardTierFor(n); rows.push(`<div class="rung${live && S.n === n ? " now" : ""}${live && S.n > n ? " done" : ""}"><span>Stage ${n}${n % SW.bonusEvery ? "" : " ✧"}</span><b>${Math.round(bet * SW.pay(n))}</b><i class="${!card ? "" : Cl[n] ? "got" : tier}" title="${!card ? "" : Cl[n] ? "card already won" : `a ${tier === "better" ? "stronger common" : tier} card, the first time`}">${!card ? "" : Cl[n] ? "✓" : tier === "rare" ? "★" : tier === "better" ? "◆" : "♦"}</i></div>`); }
      box.innerHTML = `<div class="cgtable swarm runestack dash"><h3>The Gloomwing Swarm</h3><div class="rswrap"><canvas class="swcanvas" width="${SW.W * C}" height="${SW.H * C + TOP}" tabindex="0"></canvas>
        <div class="dashside"><p class="lore">On the Joker's roof, under the night sky, the house keeps a lantern-skiff on a rail. "The Gloomwings come to the lights every night," says the attendant. "Thin them out and the house pays by the wave."</p>
        <div class="ladder rsladder">${rows.reverse().join("")}</div>
        ${live ? "" : this.cgBetRow("The stake")}<div class="cgnote">${this.cgNote || ""}</div>${last && last.cards && last.cards.length ? last.cards.map((c) => this.cgCardWon(c)).join("") : ""}
        <div class="row">${live ? `<button data-swpause>${this.swPaused ? "Go on" : "Pause"}</button>` : `<button class="primary" data-swstart>Up to the roof (${bet} gold)</button>`}<button data-leave>Leave</button></div>
        <div class="small">Left and right (or A and D) to slide; Space to fire - two bolts in the air at once, hold it for a steady stream; P to pause. Mites 50, Moths 80, Wardens take two hits for 150 - all worth double when shot diving. A Warden that hovers low lowers a binding beam: get caught and your skiff is carried off (a life); shoot that Warden while it is out of the formation to free it, and fly two skiffs side by side. Every fourth stage (✧) is a Bonus Flight: 100 each, 10,000 for all forty. Three lives, more at 20,000 and 70,000. Each stage cleared pays gold, more each, every play; at stages 2, 4, 6, 8, 10, 12, 15 and 20 a card, the first time ever (♦ common, ◆ a stronger common from 6, ★ rare from 10). Best score ${g.cgStore().swBest || 0}.</div>${this.cgStats("swarm")}</div></div></div>`;
      this.cgWireBet(box); const q = (s) => box.querySelector(s); q("[data-leave]").addEventListener("click", () => this.closeDialogs());
      if (q("[data-swstart]")) q("[data-swstart]").addEventListener("click", () => { const r = g.swStart(bet); this.cgNote = r.error || "Stage 1. Here they come!"; this.swFx = { parts: [], pts: [], banner: { at: performance.now(), text: "STAGE 1" } }; this.swPaused = false; this.cgSfx(r.error ? "miss" : "door", 0.45); this.renderCasino(); const cv = this.$("#casino-body .swcanvas"); if (cv) cv.focus(); });
      if (q("[data-swpause]")) q("[data-swpause]").addEventListener("click", () => { this.swPaused = !this.swPaused; this.renderCasino(); });
      this.swCanvas = q(".swcanvas");
      if (!this.swKeys) { this.swHeld = new Set();
        this.swKeys = (e) => { if (this.cgView !== "swarm" || !this.dialogOpen() || !this.game.swLevel()) return; const k = { ArrowLeft: "l", KeyA: "l", ArrowRight: "r", KeyD: "r", Space: "f" }[e.code];
          if (e.type === "keydown" && e.code === "KeyP") { e.preventDefault(); this.swPaused = !this.swPaused; this.renderCasino(); return; }
          if (!k) return; e.preventDefault(); e.stopPropagation(); if (e.type === "keydown") this.swHeld.add(k); else this.swHeld.delete(k); };
        window.addEventListener("keydown", this.swKeys, true); window.addEventListener("keyup", this.swKeys, true); }
      if (!this.swLoop) { let prev = performance.now(); const loop = (now) => { if (!this.swCanvas || !this.swCanvas.isConnected || this.cgView !== "swarm") { this.swLoop = null; return; } const dt = Math.min(0.05, (now - prev) / 1000); prev = now; this.swFrame(dt, now); this.swLoop = requestAnimationFrame(loop); }; this.swLoop = requestAnimationFrame(loop); }
    },
    swFrame(dt, now) {
      const g = this.game, SW = CM.SW, L = g.swLevel(), cv = this.swCanvas, p = cv.getContext("2d"), fx = this.swFx = this.swFx || { parts: [], pts: [] }, H = this.swHeld || new Set();
      if (L && !this.swPaused) { L.input((H.has("r") ? 1 : 0) - (H.has("l") ? 1 : 0), H.has("f")); L.update(dt); for (const e of L.events.splice(0)) this.swEvent(e, now, L); const out = g.swCheck();
        if (out && out.cleared) { const nx = out.cleared + 1; fx.banner = { at: now, text: nx % SW.bonusEvery ? `STAGE ${nx}` : "BONUS FLIGHT", sub: `Stage ${out.cleared} cleared: +${out.pay} gold${out.bonus ? ` - ${out.hits} of 40 hit` : ""}${out.card ? ` - ${out.card}` : ""}` }; this.cgSfx("victory", 0.5); if (out.card) setTimeout(() => this.cgSfx("cardwin", 0.5), 300); this.cgNote = `Stage ${out.cleared} cleared: ${out.pay} gold${out.card ? `, and a card - ${out.card}` : ""}.`; this.renderCasino(); return; }
        if (out && out.over) { const S = g.swState(); this.cgNote = `The skiff's last lantern goes out on stage ${S.last.level}. ${S.won} gold back${S.last.cards.length ? `, and ${S.last.cards.length} card${S.last.cards.length > 1 ? "s" : ""}` : ""}.`; this.cgSfx("cardlose", 0.5); this.renderCasino(); if (S.won) this.cgCoins(this.$("#casino-body"), 12); return; } }
      const Lv = L || this.swLastDrawn; if (L) this.swLastDrawn = L;
      // the sky
      p.fillStyle = "#06061A"; p.fillRect(0, 0, cv.width, cv.height);
      for (let k = 0; k < 70; k++) { const x = (k * 97) % cv.width, sp = 10 + (k % 3) * 14, y = TOP + ((k * 53 + now / 1000 * sp) % (cv.height - TOP)); p.fillStyle = ["#6070A0", "#A0B0E0", "#F0E0A0"][k % 3]; p.globalAlpha = 0.4 + 0.4 * Math.abs(Math.sin(now / 500 + k)); p.fillRect(x, y, k % 5 ? 1 : 2, k % 5 ? 1 : 2); } p.globalAlpha = 1;
      p.fillStyle = "#100C20"; p.fillRect(0, 0, cv.width, TOP); p.fillStyle = "#FFE070"; p.font = "bold 14px monospace"; p.fillText(Lv ? `SCORE ${Lv.score}` : "THE GLOOMWING SWARM", 8, 19);
      if (Lv) { p.fillText(`STAGE ${Lv.n}`, cv.width / 2 - 30, 19); for (let k = 0; k < Math.min(6, Lv.lives); k++) this.swSkiff(p, cv.width - 14 - k * 18, 14, 0.55, now); }
      if (!Lv) { p.fillStyle = "rgba(255,240,200,0.9)"; p.font = "bold 24px Georgia, serif"; p.textAlign = "center"; p.fillText("The Gloomwing Swarm", cv.width / 2, cv.height / 2); p.textAlign = "left"; return; }
      p.save(); p.translate(0, TOP);
      // the binding beam
      for (const f of Lv.foes) if (f.state === "beam") { const k = Math.min(1, Math.max(0, (f.t - 0.2) / 0.5)) * (f.t > 3.2 ? Math.max(0, 1 - (f.t - 3.2) / 0.4) : 1), X = f.x * C, Y = f.y * C + 10, Y2 = (SW.shipY + 1.2) * C; p.save(); p.globalAlpha = 0.55 * k; const gr = p.createLinearGradient(0, Y, 0, Y2); gr.addColorStop(0, "#C0F0FF"); gr.addColorStop(1, "#6060FF"); p.fillStyle = gr; p.beginPath(); p.moveTo(X - 6, Y); p.lineTo(X + 6, Y); p.lineTo(X + 28 * k, Y2); p.lineTo(X - 28 * k, Y2); p.closePath(); p.fill();
        p.strokeStyle = "#FFFFFF"; p.globalAlpha = 0.5 * k; for (let s = 0; s < 6; s++) { const yy = Y + ((s / 6 + now / 900) % 1) * (Y2 - Y), w = 6 + (yy - Y) / (Y2 - Y) * 22 * k; p.beginPath(); p.moveTo(X - w, yy); p.lineTo(X + w, yy); p.stroke(); } p.restore(); }
      for (const f of Lv.foes) { if (f.state === "dead" || f.state === "gone" || f.state === "wait") continue; this.swFoe(p, f, now); if (f.captive) { p.save(); p.globalAlpha = 0.85; p.filter = "hue-rotate(150deg)"; this.swSkiff(p, f.x * C, f.y * C - 18, 0.8, now); p.restore(); } }
      for (const b of Lv.bolts) { p.fillStyle = "#80F0FF"; p.shadowColor = "#80F0FF"; p.shadowBlur = 6; p.fillRect(b.x * C - 1.5, b.y * C - 7, 3, 12); p.shadowBlur = 0; }
      for (const s of Lv.shots) { p.fillStyle = "#FFB040"; p.beginPath(); p.arc(s.x * C, s.y * C, 3, 0, Math.PI * 2); p.fill(); p.fillStyle = "#FFF0C0"; p.fillRect(s.x * C - 1, s.y * C - 1, 2, 2); }
      if (!Lv.p.dead) for (const x of Lv.shipXs()) this.swSkiff(p, x * C, SW.shipY * C, 1, now);
      fx.parts = fx.parts.filter((q) => (q.life -= dt) > 0); for (const q of fx.parts) { q.x += q.vx * dt; q.y += q.vy * dt; p.globalAlpha = Math.min(1, q.life * 2.5); p.fillStyle = q.c; p.fillRect(q.x - 1.5, q.y - 1.5, 3, 3); } p.globalAlpha = 1;
      fx.pts = fx.pts.filter((q) => now - q.at < 800); for (const q of fx.pts) { p.globalAlpha = 1 - (now - q.at) / 800; p.fillStyle = "#A0F0FF"; p.font = "bold 11px monospace"; p.fillText(String(q.n), q.x - 10, q.y - (now - q.at) / 40); } p.globalAlpha = 1;
      p.restore();
      if (fx.banner && now - fx.banner.at < 2600) { const B = fx.banner, t = (now - B.at) / 2600; p.globalAlpha = t > 0.8 ? (1 - t) / 0.2 : 1; p.fillStyle = "#80E0FF"; p.font = "bold 26px Georgia, serif"; p.textAlign = "center"; p.fillText(B.text, cv.width / 2, cv.height / 2 + 20); if (B.sub) { p.font = "14px Georgia, serif"; p.fillStyle = "#F0E0B0"; p.fillText(B.sub, cv.width / 2, cv.height / 2 - 14); } p.textAlign = "left"; p.globalAlpha = 1; }
      if (Lv.bonus && Lv.t < 2) { p.fillStyle = "#FFE070"; p.font = "bold 18px Georgia, serif"; p.textAlign = "center"; p.fillText("Hit as many as you can!", cv.width / 2, cv.height / 2 + 50); p.textAlign = "left"; }
      if (this.swPaused) { p.fillStyle = "rgba(0,0,0,0.6)"; p.fillRect(0, 0, cv.width, cv.height); p.fillStyle = "#FFF"; p.font = "bold 26px Georgia, serif"; p.textAlign = "center"; p.fillText("Paused", cv.width / 2, cv.height / 2); p.textAlign = "left"; }
    },
    swEvent(e, now, L) {
      const fx = this.swFx, burst = (x, y, cols, n = 16) => { for (let k = 0; k < n; k++) { const a = Math.random() * Math.PI * 2, v = 40 + Math.random() * 120; fx.parts.push({ x: x * C, y: y * C, vx: Math.cos(a) * v, vy: Math.sin(a) * v, life: 0.4 + Math.random() * 0.4, c: cols[k % cols.length] }); } };
      if (e.kind === "fire") this.cgSfx("zap", 0.15, 1.8);
      else if (e.kind === "kill") { this.cgSfx("shatter", 0.35, 1.1 + Math.random() * 0.3); burst(e.f.x, e.f.y, e.f.kind === "warden" ? ["#80E070", "#F0D060", "#FFF"] : e.f.kind === "moth" ? ["#F09040", "#60D0E0", "#FFF"] : ["#B070F0", "#F0E0FF"]); fx.pts.push({ x: e.f.x * C, y: e.f.y * C, n: e.pts, at: now }); }
      else if (e.kind === "dent") this.cgSfx("bump", 0.35, 1.5); else if (e.kind === "dive") this.cgSfx("monster", 0.12, 1.7); else if (e.kind === "ember") this.cgSfx("wandboom", 0.12, 2);
      else if (e.kind === "beam") this.cgSfx("spell", 0.4, 0.6); else if (e.kind === "captured") this.cgSfx("cardlose", 0.5);
      else if (e.kind === "rescue") { this.cgSfx("cardwin", 0.5); fx.banner = { at: now, text: "SKIFF FREED!" }; } else if (e.kind === "lostcaptive") this.cgSfx("miss", 0.4);
      else if (e.kind === "die" || e.kind === "lostone") { this.cgSfx("hurt", 0.6); burst(L.p.x, CM.SW.shipY, ["#FFE070", "#F06030", "#FFFFFF"], 28); }
      else if (e.kind === "extra") this.cgSfx("cardwin", 0.4); else if (e.kind === "perfect") { this.cgSfx("victory", 0.6); fx.banner = { at: now, text: "PERFECT! +10000" }; }
    },
    // the lantern-skiff: a little hull, two swept fins, a lantern at the mast giving off its glow
    swSkiff(p, X, Y, s, now) {
      p.save(); p.translate(X, Y); p.scale(s * 1.2, s * 1.2);
      p.fillStyle = "#8A5A2A"; p.beginPath(); p.moveTo(-9, 2); p.lineTo(9, 2); p.lineTo(6, 8); p.lineTo(-6, 8); p.closePath(); p.fill();
      p.fillStyle = "#C0C8E0"; p.beginPath(); p.moveTo(-3, 2); p.lineTo(-11, 6); p.lineTo(-10, 0); p.closePath(); p.fill(); p.beginPath(); p.moveTo(3, 2); p.lineTo(11, 6); p.lineTo(10, 0); p.closePath(); p.fill();
      p.fillStyle = "#5A3A1A"; p.fillRect(-1, -8, 2, 10); p.fillStyle = "#FFE070"; p.shadowColor = "#FFD040"; p.shadowBlur = 10 + 3 * Math.sin(now / 120); p.fillRect(-3, -11, 6, 5); p.shadowBlur = 0; p.fillStyle = "#3A2A10"; p.fillRect(-3, -12, 6, 1.5);
      p.restore();
    },
    // the Gloomwings, with beating wings, turned along their flight when not in the formation
    swFoe(p, f, now) {
      const X = f.x * C, Y = f.y * C, beat = Math.sin(now / 70 + f.id), ang = f.state === "form" ? 0 : f.dir + Math.PI / 2;
      p.save(); p.translate(X, Y); p.rotate(ang); p.scale(1.35, 1.35);
      if (f.kind === "mite") { p.fillStyle = "#D0B0FF"; p.globalAlpha = 0.85; p.beginPath(); p.ellipse(-5, -1, 5, 3 + beat * 1.5, -0.4, 0, Math.PI * 2); p.ellipse(5, -1, 5, 3 + beat * 1.5, 0.4, 0, Math.PI * 2); p.fill(); p.globalAlpha = 1; p.fillStyle = "#7030C0"; p.beginPath(); p.ellipse(0, 1, 3.5, 6, 0, 0, Math.PI * 2); p.fill(); p.fillStyle = "#F0E040"; p.fillRect(-2, -4, 1.5, 1.5); p.fillRect(0.5, -4, 1.5, 1.5); }
      else if (f.kind === "moth") { p.fillStyle = "#F09040"; const w = 8 + beat * 2; p.beginPath(); p.moveTo(0, -2); p.lineTo(-w, -7); p.lineTo(-w + 1, 4); p.closePath(); p.moveTo(0, -2); p.lineTo(w, -7); p.lineTo(w - 1, 4); p.closePath(); p.fill(); p.fillStyle = "#60D0E0"; p.beginPath(); p.arc(-w / 2, -2, 1.8, 0, Math.PI * 2); p.arc(w / 2, -2, 1.8, 0, Math.PI * 2); p.fill(); p.fillStyle = "#402810"; p.beginPath(); p.ellipse(0, 1, 2.5, 6, 0, 0, Math.PI * 2); p.fill(); p.strokeStyle = "#402810"; p.beginPath(); p.moveTo(-1, -5); p.lineTo(-3, -9); p.moveTo(1, -5); p.lineTo(3, -9); p.stroke(); }
      else { const dent = f.hp < CM.SW.KINDS.warden.hp; p.fillStyle = dent ? "#5080E0" : "#40A050"; p.globalAlpha = 0.8; p.beginPath(); p.ellipse(-8, 0, 6, 3 + beat, -0.3, 0, Math.PI * 2); p.ellipse(8, 0, 6, 3 + beat, 0.3, 0, Math.PI * 2); p.fill(); p.globalAlpha = 1;
        p.fillStyle = dent ? "#3050B0" : "#2A7A3A"; p.beginPath(); p.ellipse(0, 1, 6, 8, 0, 0, Math.PI * 2); p.fill(); p.strokeStyle = "#F0D060"; p.lineWidth = 1.5; p.beginPath(); p.moveTo(0, -6); p.lineTo(0, 8); p.stroke(); p.lineWidth = 1; p.fillStyle = "#F0D060"; p.fillRect(-5, -9, 10, 3); p.fillStyle = "#F04040"; p.fillRect(-3, -5, 2, 2); p.fillRect(1, -5, 2, 2); }
      p.restore();
    },
  });
}
