"use strict";
// The Gilded Joker's arcade, the window's side (the twenty-first big update): Runefall's board on a canvas - the
// wizard's staff turning to aim with its guide, the orb falling and ringing up the scale as it strikes rune after
// rune, the lit runes crumbling to dust, the Well sliding along the bottom - and Lantern Lane Dash in its cabinet, a
// little pixel world under scanlines with lit readouts, hopped across with the arrow keys. The rules are
// 64t-casinoarcade.js.
CM.CG_TABLES.push(["runefall", "Runefall"], ["dash", "Lantern Lane Dash"]);
{ const floor0 = CM.UI.prototype.renderFloor;
  Object.assign(CM.UI.prototype, {
    renderFloor(box) { if (this.cgView === "runefall") return this.cgRunefall(box); if (this.cgView === "dash") return this.cgDash(box); return floor0.call(this, box); },
    // ---- Runefall ----
    cgRunefall(box) {
      const g = this.game, S = g.pgState(), B = g.pgBoard(), PG = CM.PG, live = S && S.stage === "board";
      const bets = this.cgBet === undefined ? 5 : this.cgBet, ladder = PG.BOARDS.map(([name], i) => `<tr class="${live && S.n === i + 1 ? "now" : ""}${S && (S.n > i + 1 || (S.stage === "done" && S.cleared)) ? " done" : ""}"><td>${i + 1}. ${name}</td><td>${Math.round((live || S ? S.bet : bets) * PG.PAY[i])}${PG.CARD[i + 1] ? ` <small>+ ${PG.CARD[i + 1]} card</small>` : ""}</td></tr>`).join("");
      const last = S && S.last;
      box.innerHTML = `<div class="cgtable runefall"><h3>Runefall</h3><div class="rfwrap"><canvas class="rfcanvas" width="${PG.W}" height="${PG.H}"></canvas><div class="rfside">
        <p class="lore">A slate board leaning on an easel, studded with rune-stones, and a wizard's staff on a swivel at its head. "Break every ember rune," says the attendant. "Ten orbs a board."</p>
        <div class="rfinfo">${B ? `<b>${PG.BOARDS[B.n - 1][0]}</b><div>Orbs <b class="orbs">${B.orbs}</b> - ember runes left <b class="emb">${B.embersLeft()}</b></div><div>Score <b class="sc">${B.score}</b> <span class="mul">x${B.mult()}</span>${B.fire ? ` <span class="fire">fireball ready</span>` : ""}</div>` : "<div>Put down a stake and start a run of five boards.</div>"}</div>
        <table class="paytable rfladder">${ladder}<tr><td colspan="2" class="small">Each board cleared pays its share of the stake; a lost board pays back a little for every ember rune broken.</td></tr></table>
        ${live ? "" : this.cgBetRow("The stake")}<div class="cgnote">${this.cgNote || ""}</div>${last && last.card ? this.cgCardWon(last.card) : ""}
        <div class="row">${live ? "" : `<button class="primary" data-rfstart>Start a run</button>`}<button data-leave>Leave</button></div>
        <div class="small">Aim with the mouse; click to loose an orb. Green runes make the next orb a fireball; the purple rune pays a bonus; the Well gives a caught orb back.</div>${this.cgStats("runefall")}</div></div></div>`;
      this.cgWireBet(box); box.querySelector("[data-leave]").addEventListener("click", () => this.closeDialogs());
      const st = box.querySelector("[data-rfstart]"); if (st) st.addEventListener("click", () => { const r = g.pgStart(bets); this.cgNote = r.error || "Board one. Aim, and click."; this.cgSfx(r.error ? "miss" : "card", 0.4); this.renderCasino(); });
      const cv = box.querySelector(".rfcanvas"); this.rfCanvas = cv; this.rfAim = this.rfAim === undefined ? 0 : this.rfAim; this.rfParts = this.rfParts || [];
      const pos = (e) => { const r = cv.getBoundingClientRect(); return [(e.clientX - r.left) * (PG.W / r.width), (e.clientY - r.top) * (PG.H / r.height)]; };
      cv.addEventListener("mousemove", (e) => { const [x, y] = pos(e), [lx, ly] = PG.launcher; this.rfAim = Math.max(-1.45, Math.min(1.45, Math.atan2(x - lx, Math.max(4, y - ly)))); });
      cv.addEventListener("click", (e) => { const Bd = g.pgBoard(); if (!Bd || Bd.stage !== "aim") return; const [x, y] = pos(e), [lx, ly] = PG.launcher; this.rfAim = Math.max(-1.45, Math.min(1.45, Math.atan2(x - lx, Math.max(4, y - ly)))); Bd.shoot(this.rfAim); });
      if (!this.rfLoop) { let prev = performance.now(); const loop = (now) => { if (!this.rfCanvas || !this.rfCanvas.isConnected || this.cgView !== "runefall") { this.rfLoop = null; return; } const dt = Math.min(0.05, (now - prev) / 1000); prev = now; this.rfFrame(dt, now); this.rfLoop = requestAnimationFrame(loop); }; this.rfLoop = requestAnimationFrame(loop); }
    },
    rfFrame(dt, now) {
      const g = this.game, B = g.pgBoard(), PG = CM.PG, cv = this.rfCanvas, p = cv.getContext("2d"), S = g.pgState();
      if (B) { B.update(dt); for (const e of B.events.splice(0)) this.rfEvent(e, B); if ((B.stage === "won" || B.stage === "lost") && !this.rfSettling) { this.rfSettling = true; setTimeout(() => { this.rfSettling = false; const r = g.pgSettle(); if (!r) return; this.cgNote = r.won ? `Board ${r.n} cleared: ${r.pay} gold back.${g.pgState().stage === "done" ? " The whole run!" : " On to the next."}` : `The orbs are spent. ${r.pay ? `${r.pay} gold back for the embers broken.` : ""}`; this.renderCasino(); }, 900); }
        const info = cv.parentElement.querySelector(".rfinfo"); if (info) { const q = (s) => info.querySelector(s); if (q(".orbs")) q(".orbs").textContent = B.orbs; if (q(".emb")) q(".emb").textContent = B.embersLeft(); if (q(".sc")) q(".sc").textContent = B.score; if (q(".mul")) q(".mul").textContent = `x${B.mult()}`; } }
      // the board
      const band = B ? PG.BOARDS[B.n - 1][1] : "#3A3430", gr = p.createLinearGradient(0, 0, 0, PG.H); gr.addColorStop(0, band); gr.addColorStop(1, "#0E0C10"); p.fillStyle = gr; p.fillRect(0, 0, PG.W, PG.H);
      p.strokeStyle = "rgba(255,255,255,0.04)"; for (let y = 0; y < PG.H; y += 40) for (let x = (y / 40) % 2 ? 0 : 40; x < PG.W; x += 80) p.strokeRect(x + 0.5, y + 0.5, 80, 40);
      const pegs = B ? B.pegs : [], col = { blue: ["#3A6AC8", "#9AC0FF"], ember: ["#D86A18", "#FFC070"], mana: ["#2A9A4A", "#90FFA0"], gold: ["#8A3AC8", "#E0A0FF"] };
      for (const q of pegs) { if (q.gone) continue; const [c0, c1] = col[q.kind], lit = q.hit, pulse = q.kind === "gold" ? 0.5 + 0.5 * Math.sin(now / 160) : 0;
        p.save(); if (lit) { p.shadowColor = c1; p.shadowBlur = 16; } else if (pulse) { p.shadowColor = c1; p.shadowBlur = 8 * pulse; }
        const rg = p.createRadialGradient(q.x - 3, q.y - 3, 1, q.x, q.y, PG.pegR); rg.addColorStop(0, lit ? "#FFFFFF" : c1); rg.addColorStop(1, lit ? c1 : c0); p.fillStyle = rg; p.beginPath(); p.arc(q.x, q.y, PG.pegR, 0, Math.PI * 2); p.fill(); p.restore();
        p.strokeStyle = lit ? "rgba(255,255,255,0.9)" : "rgba(0,0,0,0.45)"; p.lineWidth = 1.2; p.beginPath(); p.moveTo(q.x, q.y - 5); p.lineTo(q.x, q.y + 5); p.moveTo(q.x - 3, q.y - 2); p.lineTo(q.x + 3, q.y + 1); p.stroke(); }
      // the dust of crumbled runes
      this.rfParts = this.rfParts.filter((d) => (d.life -= dt) > 0); for (const d of this.rfParts) { d.x += d.vx * dt; d.y += d.vy * dt; d.vy += 300 * dt; p.globalAlpha = Math.max(0, d.life / 0.8); p.fillStyle = d.c; p.fillRect(d.x, d.y, 3, 3); } p.globalAlpha = 1;
      // the Well
      if (B) { const wl = B.well, y = PG.H - 30; p.fillStyle = "#5A5048"; p.fillRect(wl.x - wl.w / 2, y, wl.w, 26); p.fillStyle = "#3A3430"; for (let k = 0; k < 4; k++) p.fillRect(wl.x - wl.w / 2 + k * (wl.w / 4) + 1, y + 2 + (k % 2) * 10, wl.w / 4 - 2, 8); p.fillStyle = "#1A3A5A"; p.fillRect(wl.x - wl.w / 2 + 6, y + 2, wl.w - 12, 6); p.strokeStyle = "#C8A040"; p.lineWidth = 2; p.strokeRect(wl.x - wl.w / 2, y, wl.w, 26); }
      // the staff, the guide and the orb
      const [lx, ly] = PG.launcher, a = this.rfAim || 0; p.save(); p.translate(lx, ly); p.rotate(-a); p.strokeStyle = "#7A5A30"; p.lineWidth = 7; p.beginPath(); p.moveTo(0, -30); p.lineTo(0, 22); p.stroke(); p.fillStyle = B && B.fire ? "#FF7030" : "#A0E0FF"; p.shadowColor = p.fillStyle; p.shadowBlur = 14 + 4 * Math.sin(now / 200); p.beginPath(); p.arc(0, 26, 8, 0, Math.PI * 2); p.fill(); p.restore();
      if (B && B.stage === "aim") { p.fillStyle = "rgba(255,255,255,0.6)"; B.guide(a).forEach(([x, y], i) => { if (i % 3 === 0) { p.beginPath(); p.arc(x, y, 2, 0, Math.PI * 2); p.fill(); } }); }
      if (B && B.ball) { const b = B.ball; (this.rfTrail = this.rfTrail || []).push([b.x, b.y]); if (this.rfTrail.length > 12) this.rfTrail.shift(); this.rfTrail.forEach(([x, y], i) => { p.globalAlpha = i / 24; p.fillStyle = b.fire ? "#FF8030" : "#A0E0FF"; p.beginPath(); p.arc(x, y, PG.orbR * (i / 12), 0, Math.PI * 2); p.fill(); }); p.globalAlpha = 1;
        p.save(); p.shadowColor = b.fire ? "#FF6020" : "#A0E0FF"; p.shadowBlur = 16; const og = p.createRadialGradient(b.x - 2, b.y - 2, 1, b.x, b.y, PG.orbR); og.addColorStop(0, "#FFFFFF"); og.addColorStop(1, b.fire ? "#FF5010" : "#60B0FF"); p.fillStyle = og; p.beginPath(); p.arc(b.x, b.y, PG.orbR, 0, Math.PI * 2); p.fill(); p.restore(); } else this.rfTrail = [];
      if (B && B.stage !== "aim" && B.stage !== "flying") { p.fillStyle = "rgba(0,0,0,0.55)"; p.fillRect(0, PG.H / 2 - 50, PG.W, 100); p.fillStyle = B.stage === "won" ? "#FFE070" : "#FF9080"; p.font = "bold 36px Georgia, serif"; p.textAlign = "center"; p.fillText(B.stage === "won" ? "Every ember broken!" : "The orbs are spent", PG.W / 2, PG.H / 2 + 12); p.textAlign = "left"; }
      if (!B) { p.fillStyle = "rgba(255,240,200,0.8)"; p.font = "bold 28px Georgia, serif"; p.textAlign = "center"; p.fillText(S && S.stage === "done" ? (S.cleared ? "All five boards cleared!" : "The run is over") : "Runefall", PG.W / 2, PG.H / 2); p.textAlign = "left"; }
    },
    rfEvent(e, B) {
      if (e.kind === "hit") { this.cgSfx(e.peg.kind === "ember" ? "cardplace" : "card", 0.35, Math.min(2.4, 0.8 + e.n * 0.07)); if (e.peg.kind === "gold") this.cgSfx("coin", 0.5); }
      else if (e.kind === "mana") this.cgSfx("spell", 0.5); else if (e.kind === "shoot") this.cgSfx("zap", 0.4); else if (e.kind === "well") { this.cgSfx("coin", 0.55); this.cgSfx("tablebell", 0.4); }
      else if (e.kind === "wall") this.cgSfx("step", 0.15, 1.5);
      else if (e.kind === "crumble") { if (e.n) this.cgSfx("shatter", Math.min(0.6, 0.2 + e.n * 0.03), 1.2); for (const q of B.pegs) if (q.gone && !q.dusted) { q.dusted = true; for (let k = 0; k < 6; k++) this.rfParts.push({ x: q.x, y: q.y, vx: (Math.random() - 0.5) * 160, vy: -Math.random() * 120, life: 0.8, c: q.kind === "ember" ? "#FFB060" : q.kind === "mana" ? "#90FFA0" : q.kind === "gold" ? "#E0A0FF" : "#9AC0FF" }); } }
      else if (e.kind === "cleared") { this.cgSfx("victory", 0.6); this.cgSfx("cardwin", 0.5); } else if (e.kind === "lost") this.cgSfx("cardlose", 0.5);
    },
    // ---- Lantern Lane Dash ----
    cgDash(box) {
      const g = this.game, S = g.crState(), CR = CM.CR, L = g.crLevel(), bet = S && S.stage !== "done" ? S.bet : (this.cgBet === undefined ? 5 : this.cgBet), between = S && S.stage === "between";
      const ladder = CR.LADDER.map((m, i) => `<div class="rung${S && S.n === i + 1 && S.stage !== "done" ? " now" : ""}${S && (S.n > i + 1 || (between && S.n === i + 1)) ? " done" : ""}"><span>LV${i + 1}</span><b>${Math.round(bet * m)}</b>${CR.CARD[i + 1] ? `<i>${CR.CARD[i + 1] === "rare" ? "★" : "♦"}</i>` : ""}</div>`).reverse().join("");
      box.innerHTML = `<div class="cgtable dash"><h3>Lantern Lane Dash</h3><div class="dashwrap"><div class="cabinet"><div class="marquee">LANTERN LANE DASH</div>
        <div class="leds"><span>BET <b>${bet}</b></span><span>LEVEL <b>${S && S.stage !== "done" ? S.n : "-"}</b></span><span>POT <b class="pot">${S ? S.pot : 0}</b></span><span>GOLD <b>${g.gold}</b></span></div>
        <div class="crt"><canvas class="dashcanvas" width="144" height="208"></canvas><div class="scan"></div></div>
        <div class="pad"><button data-hop="up">▲</button><div><button data-hop="left">◀</button><button data-hop="down">▼</button><button data-hop="right">▶</button></div></div></div>
        <div class="dashside"><div class="ladder">${ladder}</div><p class="lore">A cabinet in the corner, its glass warm, a little lamp-lit lane on it. "Hop across," says the attendant. "Carts, the river, the mine rail. Get to the gate."</p>
        ${S && S.stage === "run" ? "" : this.cgBetRow("The stake")}<div class="cgnote">${this.cgNote || ""}</div>${S && S.last && S.last.card ? this.cgCardWon(S.last.card) : ""}
        <div class="row">${between ? `<button class="primary" data-cron>Press on to level ${S.n + 1}</button><button data-crcollect>Collect ${S.pot} gold</button>` : S && S.stage === "run" ? "" : `<button class="primary" data-crstart>Insert ${bet} gold</button>`}<button data-leave>Leave</button></div>
        <div class="small">Arrow keys or W A S D (or the pad) to hop. Each level cleared raises the pot up the ladder - collect it, or press on and risk it; cards at levels 3 and 5. Dawdle too long and the Night Watch's crow comes for you.</div>${this.cgStats("dash")}</div></div></div>`;
      this.cgWireBet(box); box.querySelector("[data-leave]").addEventListener("click", () => this.closeDialogs());
      const q = (s) => box.querySelector(s);
      if (q("[data-crstart]")) q("[data-crstart]").addEventListener("click", () => { const r = g.crStart(bet); this.cgNote = r.error || "Level 1. Hop!"; this.cgSfx(r.error ? "miss" : "coin", 0.5); this.renderCasino(); });
      if (q("[data-cron]")) q("[data-cron]").addEventListener("click", () => { g.crOn(); this.cgNote = `Level ${g.crState().n}.`; this.cgSfx("tablebell", 0.4); this.renderCasino(); });
      if (q("[data-crcollect]")) q("[data-crcollect]").addEventListener("click", () => { const n = g.crCollect(); this.cgNote = `Collected ${n} gold.`; this.cgSfx("coin", 0.6); this.renderCasino(); this.cgCoins(this.$("#casino-body"), 14); });
      box.querySelectorAll("[data-hop]").forEach((b) => b.addEventListener("click", () => this.crHop(b.dataset.hop)));
      if (!this.crKeys) { this.crKeys = (e) => { if (this.cgView !== "dash" || !this.dialogOpen() || !this.game.crLevel()) return; const d = { ArrowUp: "up", KeyW: "up", ArrowDown: "down", KeyS: "down", ArrowLeft: "left", KeyA: "left", ArrowRight: "right", KeyD: "right" }[e.code]; if (!d) return; e.preventDefault(); e.stopPropagation(); this.crHop(d); }; window.addEventListener("keydown", this.crKeys, true); }
      this.crCanvas = box.querySelector(".dashcanvas");
      if (!this.crLoop) { let prev = performance.now(); const loop = (now) => { if (!this.crCanvas || !this.crCanvas.isConnected || this.cgView !== "dash") { this.crLoop = null; return; } const dt = Math.min(0.05, (now - prev) / 1000); prev = now; this.crFrame(dt, now); this.crLoop = requestAnimationFrame(loop); }; this.crLoop = requestAnimationFrame(loop); }
    },
    crHop(d) { const L = this.game.crLevel(); if (!L || L.stage !== "play") return; if (L.hop(d)) this.crHopAt = performance.now(); },
    crFrame(dt, now) {
      const g = this.game, L = g.crLevel(), cv = this.crCanvas, p = cv.getContext("2d"), T = 16, CR = CM.CR; p.imageSmoothingEnabled = false;
      p.fillStyle = "#000"; p.fillRect(0, 0, 144, 208);
      if (!L) { const S = g.crState(); p.fillStyle = "#F0C040"; p.font = "bold 10px monospace"; p.textAlign = "center"; p.fillText(S && S.stage === "between" ? `LEVEL ${S.n} CLEAR!` : S && S.stage === "done" ? (S.last && S.last.won ? "YOU MADE IT!" : "GAME OVER") : "INSERT GOLD", 72, 96); if (Math.floor(now / 500) % 2) { p.fillStyle = "#FFF"; p.fillText(S && S.stage === "between" ? "COLLECT OR PRESS ON" : "PRESS START", 72, 116); } p.textAlign = "left"; return; }
      L.update(dt); for (const e of L.events.splice(0)) this.crEvent(e, L);
      if (L.stage !== "play" && !this.crSettling) { this.crSettling = true; setTimeout(() => { this.crSettling = false; const r = g.crSettle(); if (!r) return; this.cgNote = r.won ? (g.crState().stage === "done" ? `The last gate! ${r.pot} gold.` : `Level ${r.n} cleared: the pot is ${r.pot} gold.`) : `${{ cart: "Run down by a cart", water: "Into the river", swept: "Swept off downstream", train: "The mine train", watch: "The Night Watch's crow took you" }[r.why] || "Caught"} - the pot is lost.`; this.renderCasino(); }, 1100); }
      const h = L.hero, camY = Math.max(0, Math.min(L.rows.length - 13, h.y - 3)), rowY = (y) => 208 - (y - camY + 1) * T, hopK = this.crHopAt ? Math.min(1, (now - this.crHopAt) / 120) : 1;
      for (let y = Math.floor(camY); y < Math.min(L.rows.length, camY + 14); y++) {
        const R = L.rows[y], Y = rowY(y);
        if (R.kind === "grass") { p.fillStyle = y % 2 ? "#3A7A2A" : "#428A30"; p.fillRect(0, Y, 144, T); for (const c of R.posts) { p.fillStyle = "#2A2A30"; p.fillRect(c * T + 7, Y + 3, 2, 12); p.fillStyle = Math.floor(now / 400 + c) % 2 ? "#FFE080" : "#F0C040"; p.fillRect(c * T + 5, Y + 1, 6, 4); } }
        else if (R.kind === "road") { p.fillStyle = "#3A3A40"; p.fillRect(0, Y, 144, T); p.fillStyle = "#7A7A70"; for (let x = 0; x < 144; x += 12) p.fillRect(x + ((now / 40) % 12) * 0, Y + 7, 6, 1);
          for (const o of R.things) { const x = Math.round(o.x * T); p.fillStyle = "#7A4A20"; p.fillRect(x, Y + 3, o.len * T - 2, 8); p.fillStyle = "#A06A30"; p.fillRect(x + 1, Y + 3, o.len * T - 4, 3); p.fillStyle = "#1A1A1A"; p.fillRect(x + 2, Y + 11, 4, 4); p.fillRect(x + o.len * T - 8, Y + 11, 4, 4); p.fillStyle = "#F0C040"; p.fillRect(R.dir > 0 ? x + o.len * T - 3 : x, Y + 4, 2, 2); } }
        else if (R.kind === "river") { p.fillStyle = "#1E4A8A"; p.fillRect(0, Y, 144, T); p.fillStyle = "#3A6AB0"; for (let x = 0; x < 144; x += 16) p.fillRect((x + Math.floor(now / 90) * R.dir) % 144 < 0 ? (x + Math.floor(now / 90) * R.dir) % 144 + 144 : (x + Math.floor(now / 90) * R.dir) % 144, Y + 5 + (x % 32 ? 4 : 0), 5, 1);
          for (const o of R.things) { const x = Math.round(o.x * T); p.fillStyle = "#6A4A28"; p.fillRect(x, Y + 3, o.len * T, 10); p.fillStyle = "#8A6438"; p.fillRect(x, Y + 3, o.len * T, 3); p.fillStyle = "#4A3018"; p.fillRect(x, Y + 3, 2, 10); p.fillRect(x + o.len * T - 2, Y + 3, 2, 10); } }
        else if (R.kind === "rail") { p.fillStyle = "#4A3A30"; p.fillRect(0, Y, 144, T); p.fillStyle = "#6A5A4A"; for (let x = 0; x < 144; x += 6) p.fillRect(x, Y + 3, 3, 10); p.fillStyle = "#9A9AA0"; p.fillRect(0, Y + 4, 144, 1); p.fillRect(0, Y + 11, 144, 1);
          const Tn = R.train; if (Tn.t <= 1.2 && Tn.x <= -20 && Math.floor(now / 150) % 2) { p.fillStyle = "#FF3020"; p.fillRect(2, Y + 1, 4, 4); p.fillRect(138, Y + 1, 4, 4); }
          if (Tn.x > -Tn.len - 2) for (let k = 0; k < Tn.len; k++) { const x = Math.round((Tn.x + k) * T); p.fillStyle = k === Tn.len - 1 ? "#5A5A62" : "#7A5A3A"; p.fillRect(x + 1, Y + 2, T - 2, 11); p.fillStyle = "#2A2A2A"; p.fillRect(x + 3, Y + 12, 3, 3); p.fillRect(x + T - 6, Y + 12, 3, 3); if (k === Tn.len - 1) { p.fillStyle = "#FFE080"; p.fillRect(x + T - 3, Y + 5, 2, 3); } } }
        else if (R.kind === "gate") { p.fillStyle = "#6A6460"; p.fillRect(0, Y, 144, T); p.fillStyle = "#8A847A"; for (let x = 0; x < 144; x += 8) p.fillRect(x, Y, 7, 4); p.fillStyle = "#F0C040"; p.fillRect(56, Y + 4, 32, 12); p.fillStyle = "#3A2A10"; p.fillRect(60, Y + 6, 24, 10); }
      }
      // the hero, a hop's squash and rise
      const hx = Math.round(h.fx * T), hy = rowY(h.y) - Math.round(Math.sin(hopK * Math.PI) * 4), dead = L.stage === "lost";
      p.fillStyle = "rgba(0,0,0,0.35)"; p.fillRect(hx + 4, rowY(h.y) + 13, 8, 2);
      if (!dead || Math.floor(now / 100) % 2) { p.fillStyle = "#C83030"; p.fillRect(hx + 5, hy + 6, 6, 6); p.fillStyle = "#F0C8A0"; p.fillRect(hx + 5, hy + 2, 6, 4); p.fillStyle = "#3A2A1A"; p.fillRect(hx + 5, hy + 1, 6, 2); p.fillStyle = "#2A2A3A"; p.fillRect(hx + 5, hy + 12, 2, 3); p.fillRect(hx + 9, hy + 12, 2, 3); p.fillStyle = "#F0C040"; p.fillRect(hx + 11, hy + 7, 2, 3); }
      // the Night Watch's crow, when the hero dawdles
      const late = L.idleT - (CR.idle - 3); if (late > 0 && L.stage === "play") { const cx = 144 - late / 3 * (144 - hx), cy = 20 + late / 3 * (hy - 20); p.fillStyle = "#101018"; p.fillRect(cx, cy, 10, 4); p.fillRect(cx + (Math.floor(now / 120) % 2 ? -4 : 10), cy - 2, 4, 2); }
      const pot = cv.closest(".cabinet") && cv.closest(".cabinet").querySelector(".pot"); if (pot) pot.textContent = g.crState() ? g.crState().pot : 0;
    },
    crEvent(e) {
      if (e.kind === "hop") this.cgSfx("step", 0.3, 1.7); else if (e.kind === "bell") this.cgSfx("bell", 0.35, 1.3); else if (e.kind === "cleared") { this.cgSfx("victory", 0.55); this.cgSfx("coin", 0.4); }
      else if (e.kind === "die") this.cgSfx({ cart: "hurt", water: "splash", swept: "splash", train: "slam", watch: "monster" }[e.why] || "hurt", 0.6);
    },
  });
}
