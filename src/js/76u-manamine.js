"use strict";
// Mana-Mine, the window's side (the twenty-eighth big update): the mine on a canvas in a chunky pixel look - a sky with
// the Joker's sign, four bands of earth darker as they go down (pebbles, roots, crystals), black tunnels, the miner with
// her lamp and its cone of light, Mudlings and Ember Newts with their walks (as floating eyes when they pass through the
// earth), the tether's beam, a creature swelling at each pump and bursting, the newts' breath and fire, boulders that
// shake and fall, the crystal; the score, the lives and the level at the top. Arrows or W A S D to dig, Space to shoot
// and pump, P to pause. The rules are 64ze-manamine.js.
CM.CG_TABLES.push(["manamine", "Mana-Mine"]);
{ const floor0 = CM.UI.prototype.renderFloor, C = 32;
  Object.assign(CM.UI.prototype, {
    renderFloor(box) { if (this.cgView === "manamine") return this.cgManaMine(box); return floor0.call(this, box); },
    cgManaMine(box) {
      const g = this.game, MM = CM.MM, S = g.mmState(), L = g.mmLevel(), live = !!L, bet = live ? S.bet : (this.cgBet === undefined ? 5 : this.cgBet), Cl = g.mmClaimed(), last = S && S.stage === "done" ? S.last : null;
      const top = Math.max(12, (S && live ? S.n : 1) + 4), rows = []; for (let n = 1; n <= top; n++) { const tier = CM.cardTierFor(n); rows.push(`<div class="rung${live && S.n === n ? " now" : ""}${live && S.n > n ? " done" : ""}"><span>Level ${n}</span><b>${Math.round(bet * MM.pay(n))}</b><i class="${Cl[n] ? "got" : tier}" title="${Cl[n] ? "card already won" : `a ${tier === "better" ? "stronger common" : tier} card, the first time`}">${Cl[n] ? "✓" : tier === "rare" ? "★" : tier === "better" ? "◆" : "♦"}</i></div>`); }
      box.innerHTML = `<div class="cgtable manamine runestack dash"><h3>Mana-Mine</h3><div class="rswrap"><canvas class="mmcanvas" width="${MM.W * C}" height="${MM.H * C + 28}" tabindex="0"></canvas>
        <div class="dashside"><p class="lore">A trapdoor behind the Joker's bar and a ladder down into a mine the house says is "lively". "Dig where you like," says the attendant, handing over a lamp-helmet and a mana-tether. "Pop what you meet. Mind the rocks."</p>
        <div class="ladder rsladder">${rows.reverse().join("")}</div>
        ${live ? "" : this.cgBetRow("The stake")}<div class="cgnote">${this.cgNote || ""}</div>${last && last.cards && last.cards.length ? last.cards.map((c) => this.cgCardWon(c)).join("") : ""}
        <div class="row">${live ? `<button data-mmpause>${this.mmPaused ? "Go on" : "Pause"}</button>` : `<button class="primary" data-mmstart>Down the ladder (${bet} gold)</button>`}<button data-leave>Leave</button></div>
        <div class="small">Arrows or W A S D to dig and walk; Space to shoot the tether and pump (keep pumping until it bursts); P to pause. Mudlings drift through the earth as eyes; Ember Newts spit fire along their row when you are near - watch for the breath. Dig under a boulder to drop it on what follows you. Three lives. Each level cleared pays gold, more each, every play; its card comes the first time ever (♦ common 1-4, ◆ a stronger common 5-9, ★ rare from 10). Best score ${g.cgStore().mmBest || 0}.</div>${this.cgStats("manamine")}</div></div></div>`;
      this.cgWireBet(box); const q = (s) => box.querySelector(s); q("[data-leave]").addEventListener("click", () => this.closeDialogs());
      if (q("[data-mmstart]")) q("[data-mmstart]").addEventListener("click", () => { const r = g.mmStart(bet); this.cgNote = r.error || "Level 1. Dig!"; this.mmFx = { parts: [], banner: null }; this.mmPaused = false; this.cgSfx(r.error ? "miss" : "door", 0.45); this.renderCasino(); const cv = this.$("#casino-body .mmcanvas"); if (cv) cv.focus(); });
      if (q("[data-mmpause]")) q("[data-mmpause]").addEventListener("click", () => { this.mmPaused = !this.mmPaused; this.renderCasino(); });
      this.mmCanvas = q(".mmcanvas");
      if (!this.mmKeys) { this.mmHeld = []; const map = { ArrowUp: "up", KeyW: "up", ArrowDown: "down", KeyS: "down", ArrowLeft: "left", KeyA: "left", ArrowRight: "right", KeyD: "right" };
        this.mmKeys = (e) => { if (this.cgView !== "manamine" || !this.dialogOpen() || !this.game.mmLevel()) return; const d = map[e.code]; if (e.type === "keydown") { if (e.code === "Space") { e.preventDefault(); e.stopPropagation(); if (!e.repeat && !this.mmPaused) this.game.mmLevel().pump(); return; } if (e.code === "KeyP") { e.preventDefault(); this.mmPaused = !this.mmPaused; this.renderCasino(); return; } if (d) { e.preventDefault(); e.stopPropagation(); this.mmHeld = this.mmHeld.filter((x) => x !== d).concat(d); } } else if (d) { this.mmHeld = this.mmHeld.filter((x) => x !== d); } };
        window.addEventListener("keydown", this.mmKeys, true); window.addEventListener("keyup", this.mmKeys, true); }
      if (!this.mmLoop) { let prev = performance.now(); const loop = (now) => { if (!this.mmCanvas || !this.mmCanvas.isConnected || this.cgView !== "manamine") { this.mmLoop = null; return; } const dt = Math.min(0.05, (now - prev) / 1000); prev = now; this.mmFrame(dt, now); this.mmLoop = requestAnimationFrame(loop); }; this.mmLoop = requestAnimationFrame(loop); }
    },
    mmFrame(dt, now) {
      const g = this.game, MM = CM.MM, L = g.mmLevel(), cv = this.mmCanvas, p = cv.getContext("2d"), fx = this.mmFx = this.mmFx || { parts: [] }; p.imageSmoothingEnabled = false;
      if (L && !this.mmPaused) { L.input(this.mmHeld[this.mmHeld.length - 1] || null); L.update(dt); for (const e of L.events.splice(0)) this.mmEvent(e, now); const out = g.mmCheck();
        if (out && out.cleared) { fx.banner = { at: now, level: out.cleared, pay: out.pay, card: out.card }; this.cgSfx("victory", 0.55); if (out.card) setTimeout(() => this.cgSfx("cardwin", 0.5), 300); this.cgNote = `Level ${out.cleared} cleared: ${out.pay} gold${out.card ? `, and a card - ${out.card}` : ""}.`; this.renderCasino(); return; }
        if (out && out.over) { const S = g.mmState(); this.cgNote = `The last lamp goes out on level ${S.last.level}. ${S.won} gold back${S.last.cards.length ? `, and ${S.last.cards.length} card${S.last.cards.length > 1 ? "s" : ""}` : ""}.`; this.cgSfx("cardlose", 0.5); this.renderCasino(); if (S.won) this.cgCoins(this.$("#casino-body"), 12); return; } }
      const Lv = L || this.mmLastDrawn; if (L) this.mmLastDrawn = L;
      // the hud strip
      p.fillStyle = "#120C08"; p.fillRect(0, 0, cv.width, 28); p.fillStyle = "#FFE070"; p.font = "bold 14px monospace"; p.fillText(Lv ? `SCORE ${Lv.score}` : "MANA-MINE", 8, 19); if (Lv) { p.fillText(`LEVEL ${Lv.n}`, cv.width / 2 - 34, 19); for (let k = 0; k < Lv.lives; k++) this.mmMiner(p, cv.width - 24 - k * 22, 4, "left", 0.55, now); }
      p.save(); p.translate(0, 28);
      // sky and earth
      const band = ["#C89A5A", "#B07A3A", "#8A5A2A", "#6A3A1E"];
      for (let y = 0; y < MM.H; y++) for (let x = 0; x < MM.W; x++) { const X = x * C, Y = y * C;
        if (y < MM.SKY) { p.fillStyle = y ? "#5A8AD0" : "#4A7AC0"; p.fillRect(X, Y, C, C); continue; }
        const b = Math.min(3, Math.floor(((y - MM.SKY) / (MM.H - MM.SKY)) * 4)); p.fillStyle = band[b]; p.fillRect(X, Y, C, C);
        const h = (x * 73 + y * 151) % 17; p.fillStyle = "rgba(0,0,0,0.18)"; p.fillRect(X + (h % 5) * 5 + 2, Y + (h % 7) * 4 + 3, 4, 3); if (h < 3) { p.fillStyle = b > 1 ? "#60C0F0" : "#E0C080"; p.fillRect(X + 18, Y + 20, 3, 3); }
        if (Lv && Lv.dug[y][x]) { p.fillStyle = "rgba(20,12,8,0.5)"; p.fillRect(X, Y, C, C); p.fillStyle = "#140C08"; p.fillRect(X + 2, Y + 2, C - 4, C - 4); p.fillStyle = "rgba(0,0,0,0.35)"; p.fillRect(X + 2, Y + 2, C - 4, 3); if (y > MM.SKY && Lv.dug[y - 1][x]) p.fillRect(X + 2, Y - 2, C - 4, 6); if (x > 0 && Lv.dug[y][x - 1]) p.fillRect(X - 2, Y + 2, 6, C - 4); } }
      { const sg = p.createRadialGradient(cv.width - 140, 18, 4, cv.width - 140, 18, 60); sg.addColorStop(0, "rgba(255,240,170,0.9)"); sg.addColorStop(0.25, "rgba(255,230,140,0.45)"); sg.addColorStop(1, "rgba(255,230,140,0)"); p.fillStyle = sg; p.fillRect(cv.width - 200, 0, 120, MM.SKY * C); p.fillStyle = "#FFF4C0"; p.beginPath(); p.arc(cv.width - 140, 18, 9, 0, Math.PI * 2); p.fill();
        p.fillStyle = "rgba(255,255,255,0.85)"; for (let k = 0; k < 3; k++) { const cx = ((now / (90 + k * 30) + k * 170) % (cv.width + 120)) - 60, cy = 14 + k * 14; for (const [dx, dy, r] of [[0, 0, 9], [10, -4, 11], [22, 0, 9], [11, 4, 9]]) { p.beginPath(); p.arc(cx + dx, cy + dy, r * 0.8, 0, Math.PI * 2); p.fill(); } } }
      p.fillStyle = "#4A8A2A"; p.fillRect(0, MM.SKY * C - 4, cv.width, 4); p.fillStyle = "#5AA036"; for (let x = 0; x < cv.width; x += 4) p.fillRect(x, MM.SKY * C - 6 - ((x * 7) % 3), 2, 3);
      p.fillStyle = "#8A2030"; p.fillRect(cv.width - 92, 6, 84, 22); p.fillStyle = "#FFE070"; p.font = "bold 10px Georgia, serif"; p.fillText("THE GILDED", cv.width - 86, 16); p.fillText("JOKER", cv.width - 70, 26);
      if (!Lv) { p.restore(); p.fillStyle = "rgba(255,240,200,0.9)"; p.font = "bold 24px Georgia, serif"; p.textAlign = "center"; p.fillText("Mana-Mine", cv.width / 2, cv.height / 2); p.textAlign = "left"; return; }
      // the miner's lamp light
      const P = Lv.p, mx = P.fx * C + C / 2, my = P.fy * C + C / 2, lg = p.createRadialGradient(mx, my, 10, mx, my, 120); lg.addColorStop(0, "rgba(255,230,150,0.18)"); lg.addColorStop(1, "rgba(255,230,150,0)"); p.fillStyle = lg; p.fillRect(mx - 120, my - 120, 240, 240);
      for (const r of Lv.rocks) { if (r.state === "gone") continue; const wob = r.state === "wobble" ? Math.sin(now / 30) * 2 : 0, X = r.x * C + wob, Y = r.fy * C; p.fillStyle = "#6A6460"; p.beginPath(); p.moveTo(X + 4, Y + 26); p.lineTo(X + 2, Y + 12); p.lineTo(X + 10, Y + 3); p.lineTo(X + 24, Y + 4); p.lineTo(X + 30, Y + 14); p.lineTo(X + 27, Y + 27); p.closePath(); p.fill(); p.fillStyle = "#8A847E"; p.fillRect(X + 10, Y + 7, 8, 5); p.strokeStyle = "#3A3430"; p.beginPath(); p.moveTo(X + 14, Y + 16); p.lineTo(X + 20, Y + 22); p.stroke(); }
      if (Lv.crystal) { const X = Lv.crystal.x * C + C / 2, Y = Lv.crystal.y * C + C / 2 + Math.sin(now / 200) * 2; p.save(); p.shadowColor = "#80E0FF"; p.shadowBlur = 14; p.fillStyle = "#80D8FF"; p.beginPath(); p.moveTo(X, Y - 12); p.lineTo(X + 8, Y); p.lineTo(X, Y + 12); p.lineTo(X - 8, Y); p.closePath(); p.fill(); p.restore(); }
      for (const m of Lv.mons) if (!m.dead) this.mmMon(p, m, now);
      for (const s of Lv.shots) { const k = 1 - s.t / MM.fireTime, reach = MM.fireReach * k * C, X = s.x * C + C / 2, Y = s.y * C + C / 2; const gr = p.createLinearGradient(X, Y, X + s.dir * reach, Y); gr.addColorStop(0, "rgba(255,240,120,0.95)"); gr.addColorStop(1, "rgba(255,80,20,0.5)"); p.fillStyle = gr; p.beginPath(); p.moveTo(X, Y - 4); p.lineTo(X + s.dir * reach, Y - 10 - Math.sin(now / 40) * 3); p.lineTo(X + s.dir * reach, Y + 10); p.lineTo(X, Y + 4); p.closePath(); p.fill(); }
      if (P.beam) { const [dx, dy] = MM.DIRS[P.face], len = P.beam.hold !== undefined ? (() => { const m = Lv.mons.find((q) => q.id === P.beam.hold); return m ? Math.hypot(m.fx - P.fx, m.fy - P.fy) : 0; })() : P.beam.len * (1 - Math.max(0, P.beam.t) / MM.beamTime * 0.3);
        p.strokeStyle = "#80F0FF"; p.lineWidth = 3; p.shadowColor = "#80F0FF"; p.shadowBlur = 8; p.beginPath(); p.moveTo(mx, my); for (let k = 1; k <= 8; k++) { const f = k / 8; p.lineTo(mx + dx * len * C * f + dy * Math.sin(now / 50 + k) * 3, my + dy * len * C * f + dx * Math.sin(now / 50 + k) * 3); } p.stroke(); p.shadowBlur = 0; p.lineWidth = 1; }
      if (!P.dead || Math.floor(now / 120) % 2) this.mmMiner(p, P.fx * C, P.fy * C, P.face, 1, now, P.dead);
      fx.parts = fx.parts.filter((q) => (q.life -= dt) > 0); for (const q of fx.parts) { q.x += q.vx * dt; q.y += q.vy * dt; q.vy += 300 * dt; p.globalAlpha = Math.min(1, q.life * 2); p.fillStyle = q.c; p.fillRect(q.x, q.y, 4, 4); } p.globalAlpha = 1;
      fx.pts = (fx.pts || []).filter((q) => now - q.at < 900); for (const q of fx.pts) { p.globalAlpha = 1 - (now - q.at) / 900; p.fillStyle = "#FFF0A0"; p.font = "bold 13px monospace"; p.fillText(String(q.n), q.x, q.y - (now - q.at) / 30); p.globalAlpha = 1; }
      p.restore();
      if (fx.banner && now - fx.banner.at < 2400) { const B = fx.banner, t = (now - B.at) / 2400; p.globalAlpha = t > 0.8 ? (1 - t) / 0.2 : 1; p.fillStyle = "rgba(0,0,0,0.7)"; p.fillRect(0, cv.height / 2 - 50, cv.width, 100); p.fillStyle = "#FFE070"; p.font = "bold 28px Georgia, serif"; p.textAlign = "center"; p.fillText(`Level ${B.level} cleared!`, cv.width / 2, cv.height / 2 - 10); p.font = "15px Georgia, serif"; p.fillStyle = "#F0E0B0"; p.fillText(`+${B.pay} gold${B.card ? ` - ${B.card}` : ""}`, cv.width / 2, cv.height / 2 + 20); p.textAlign = "left"; p.globalAlpha = 1; }
      if (this.mmPaused) { p.fillStyle = "rgba(0,0,0,0.6)"; p.fillRect(0, 0, cv.width, cv.height); p.fillStyle = "#FFF"; p.font = "bold 26px Georgia, serif"; p.textAlign = "center"; p.fillText("Paused", cv.width / 2, cv.height / 2); p.textAlign = "left"; }
    },
    mmEvent(e, now) {
      const fx = this.mmFx, C2 = C;
      if (e.kind === "dig") { if (Math.random() < 0.3) this.cgSfx("step", 0.12, 0.7 + Math.random() * 0.3); const band = ["#C89A5A", "#B07A3A", "#8A5A2A", "#6A3A1E"], b = Math.min(3, Math.floor(((e.y - CM.MM.SKY) / (CM.MM.H - CM.MM.SKY)) * 4)); for (let k = 0; k < 5; k++) fx.parts.push({ x: e.x * C2 + 16, y: e.y * C2 + 16, vx: (Math.random() - 0.5) * 90, vy: -Math.random() * 90, life: 0.4, c: band[Math.max(0, b)] }); }
      else if (e.kind === "beam") this.cgSfx("zap", 0.25, 1.6); else if (e.kind === "latch") this.cgSfx("zap", 0.35, 1.2);
      else if (e.kind === "pump") this.cgSfx("card", 0.35, 0.9 + e.stage * 0.25);
      else if (e.kind === "pop" || e.kind === "crush") { this.cgSfx(e.kind === "pop" ? "shatter" : "slam", 0.5, 1.2); const m = e.m; for (let k = 0; k < 14; k++) fx.parts.push({ x: m.fx * C2 + 16, y: m.fy * C2 + 16, vx: (Math.random() - 0.5) * 260, vy: -Math.random() * 200, life: 0.6, c: m.kind === "newt" ? (k % 2 ? "#60C040" : "#F08030") : (k % 2 ? "#C84040" : "#F0D0A0") }); if (e.pts) (fx.pts = fx.pts || []).push({ x: m.fx * C2, y: m.fy * C2, n: e.pts, at: now }); }
      else if (e.kind === "wobble") this.cgSfx("grind", 0.35, 1.3); else if (e.kind === "land") { this.cgSfx("bump", 0.55, 0.6); if (e.pts) (fx.pts = fx.pts || []).push({ x: e.r.x * C2, y: e.r.fy * C2, n: e.pts, at: now }); }
      else if (e.kind === "crystal") this.cgSfx("spell", 0.5); else if (e.kind === "gem") this.cgSfx("coin", 0.6);
      else if (e.kind === "fire") this.cgSfx("wandboom", 0.4, 1.4); else if (e.kind === "ghost") this.cgSfx("monster", 0.15, 1.6);
      else if (e.kind === "die") this.cgSfx("hurt", 0.6); else if (e.kind === "clear") this.cgSfx("tablebell", 0.5);
    },
    // the miner: boots, a blue coat, a lamp-helmet (its light toward where she faces), the tether in hand
    mmMiner(p, X, Y, face, s, now, dead) {
      p.save(); p.translate(X + 16 * s, Y + 16 * s); p.scale((face === "left" ? -1 : 1) * s, s); if (face === "up") p.rotate(-Math.PI / 2 * 0.0); if (dead) p.rotate(Math.PI / 2);
      const step = Math.sin(now / 80) > 0 ? 1 : 0; p.fillStyle = "#3A2A1A"; p.fillRect(-7, 8, 5, 6 + step); p.fillRect(2, 8, 5, 7 - step);
      p.fillStyle = "#3060B0"; p.fillRect(-8, -4, 16, 13); p.fillStyle = "#F0C8A0"; p.fillRect(-6, -12, 12, 9); p.fillStyle = "#202020"; p.fillRect(2, -9, 2, 2);
      p.fillStyle = "#E0B030"; p.fillRect(-8, -16, 16, 6); p.fillStyle = "#FFF4B0"; p.fillRect(6, -15, 4, 4); p.fillStyle = "#8A8A90"; p.fillRect(6, 0, 9, 3); p.fillStyle = "#80F0FF"; p.fillRect(14, -1, 3, 5);
      p.restore();
    },
    mmMon(p, m, now) {
      const C2 = C, X = m.fx * C2 + 16, Y = m.fy * C2 + 16;
      if (m.ghost) { p.fillStyle = "rgba(255,255,255,0.9)"; for (const dx of [-6, 6]) { p.beginPath(); p.arc(X + dx, Y, 4, 0, Math.PI * 2); p.fill(); } p.fillStyle = m.kind === "newt" ? "#F08030" : "#C03030"; for (const dx of [-6, 6]) p.fillRect(X + dx - 1, Y - 1, 2, 2); return; }
      const sw = 1 + m.swell * 0.3, flip = m.dir === "left" ? -1 : 1, bob = Math.sin(now / 150 + m.id) * 1.5; p.save(); p.translate(X, Y + bob); p.scale(sw * flip, sw);
      if (m.kind === "mud") { p.fillStyle = m.swell ? `rgb(${200 + m.swell * 10},${90 + m.swell * 20},${70 + m.swell * 20})` : "#A0583A"; p.beginPath(); p.arc(0, 0, 12, 0, Math.PI * 2); p.fill(); p.fillStyle = "#6A3020"; p.fillRect(-10, 6, 6, 5); p.fillRect(4, 6, 6, 5); p.fillStyle = "#FFF0A0"; p.beginPath(); p.arc(-4, -3, 4, 0, Math.PI * 2); p.arc(5, -3, 4, 0, Math.PI * 2); p.fill(); p.fillStyle = "#201008"; p.fillRect(-3, -4, 2, 3); p.fillRect(6, -4, 2, 3); }
      else { p.fillStyle = m.swell ? "#90E070" : "#4A9A3A"; p.beginPath(); p.ellipse(0, 2, 13, 9, 0, 0, Math.PI * 2); p.fill(); p.fillRect(-16, 2, 6, 4); p.fillStyle = "#F08030"; for (const k of [-6, 0, 6]) p.fillRect(k - 1, -8, 3, 4); p.fillStyle = "#3A7A2A"; p.fillRect(-9, 9, 4, 4); p.fillRect(5, 9, 4, 4); p.fillStyle = "#FFE060"; p.fillRect(6, -2, 4, 4); p.fillStyle = "#101010"; p.fillRect(8, -1, 2, 2);
        if (m.warnT > 0) { p.fillStyle = `rgba(255,${120 + 100 * Math.sin(now / 40)},40,0.9)`; p.beginPath(); p.arc(14, 2, 4 + 3 * Math.sin(now / 40), 0, Math.PI * 2); p.fill(); } }
      p.restore();
    },
  });
}
