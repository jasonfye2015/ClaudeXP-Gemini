"use strict";
// The Hexed Wand, the window's side (the twenty-fourth big update): the table under one lamp, the dealer in a hood
// across it, a row of candles each side, the wand between - it swings to its mark, a live hex cracks across in red and
// a candle gutters out in smoke, a dud puffs grey; the charges shown as they are loaded and then turned face down; the
// charms as little cards; the dealer takes its turns a beat apart. The rules are 64w-hexwand.js.
CM.CG_TABLES.push(["hexwand", "The Hexed Wand"]);
{ const floor0 = CM.UI.prototype.renderFloor;
  Object.assign(CM.UI.prototype, {
    renderFloor(box) { if (this.cgView === "hexwand") return this.cgHexWand(box); return floor0.call(this, box); },
    cgHexWand(box) {
      const g = this.game, HW = CM.HW, S = g.hwState(), D = g.hwDuel(), bet = S && S.stage !== "done" ? S.bet : (this.cgBet === undefined ? 5 : this.cgBet), between = S && S.stage === "between", mine = D && D.stage === "play" && D.turn === "you" && !this.hwBusy;
      const ladder = HW.LADDER.map((m, i) => `<div class="rung${S && S.round === i + 1 && S.stage !== "done" ? " now" : ""}${S && (S.round > i + 1 || (between && S.round === i + 1)) ? " done" : ""}"><span>Round ${i + 1} <small>(${HW.ROUNDS[i].candles} candles)</small></span><b>${Math.round(bet * m)}</b>${HW.CARD[i + 1] ? `<i>${HW.CARD[i + 1] === "rare" ? "★" : "♦"}</i>` : ""}</div>`).reverse().join("");
      const charms = D ? D.you.charms.map((c, i) => `<button class="hwcharm" data-hwc="${i}" title="${this.esc(HW.CHARMS[c][1])}" ${mine ? "" : "disabled"}>${HW.CHARMS[c][0]}</button>`).join("") : "";
      box.innerHTML = `<div class="cgtable hexwand dash"><h3>The Hexed Wand</h3><div class="hwwrap"><canvas class="hwcanvas" width="620" height="420"></canvas><div class="dashside">
        <div class="ladder">${ladder}</div><p class="lore">A round table, one lamp, and across it a dealer whose hood shows nothing. Between you lies a wand of black wood. "Hexes and duds," it says. "I tell you how many. Not which."</p>
        ${S && (S.stage === "duel" || between) ? "" : this.cgBetRow("The stake")}<div class="cgnote">${this.cgNote || ""}</div>${S && S.last && S.last.card ? this.cgCardWon(S.last.card) : ""}
        <div class="row">${D && D.stage === "play" ? `<button class="primary" data-hwf="dealer" ${mine ? "" : "disabled"}>Point it at the dealer</button><button data-hwf="you" ${mine ? "" : "disabled"}>Point it at yourself</button>` : between ? `<button class="primary" data-hwon>Play round ${S.round + 1}</button><button data-hwcollect>Collect ${S.pot} gold</button>` : `<button class="primary" data-hwstart>Sit down (${bet} gold)</button>`}<button data-leave>Leave</button></div>
        ${charms ? `<div class="hwcharms"><span class="lbl">Your charms:</span>${charms}</div>` : ""}
        <div class="small">A live hex snuffs a candle of whoever the wand points at; a dud does nothing - and if you pointed it at yourself, the turn stays yours. The dealer plays fair: it knows the counts and what its own glass shows.</div>${this.cgStats("hexwand")}</div></div></div>`;
      this.cgWireBet(box); const q = (s) => box.querySelector(s); q("[data-leave]").addEventListener("click", () => this.closeDialogs());
      if (q("[data-hwstart]")) q("[data-hwstart]").addEventListener("click", () => { const r = g.hwStart(bet); this.cgNote = r.error || "Round one. Your turn."; this.hwFx = []; this.cgSfx(r.error ? "miss" : "chain", 0.45); this.renderCasino(); });
      if (q("[data-hwon]")) q("[data-hwon]").addEventListener("click", () => { g.hwOn(); this.cgNote = `Round ${g.hwState().round}.`; this.hwFx = []; this.cgSfx("tablebell", 0.4); this.renderCasino(); });
      if (q("[data-hwcollect]")) q("[data-hwcollect]").addEventListener("click", () => { const n = g.hwCollect(); this.cgNote = `You take ${n} gold and stand.`; this.cgSfx("coin", 0.6); this.renderCasino(); this.cgCoins(this.$("#casino-body"), 12); });
      box.querySelectorAll("[data-hwf]").forEach((b) => b.addEventListener("click", () => { const Dd = g.hwDuel(); if (!Dd || this.hwBusy) return; Dd.fire("you", b.dataset.hwf); this.hwAfter(); }));
      box.querySelectorAll("[data-hwc]").forEach((b) => b.addEventListener("click", () => { const Dd = g.hwDuel(); if (!Dd || this.hwBusy) return; const r = Dd.use("you", Number(b.dataset.hwc)); if (!r) { this.cgNote = "Not now."; this.renderCasino(); return; } this.cgNote = r.seen !== null && r.seen !== undefined ? `It shows ${r.seen ? "a live hex" : "a dud"}.` : ""; this.hwAfter(); }));
      this.hwCanvas = q(".hwcanvas");
      if (!this.hwLoop) { const loop = (now) => { if (!this.hwCanvas || !this.hwCanvas.isConnected || this.cgView !== "hexwand") { this.hwLoop = null; return; } this.hwFrame(now); this.hwLoop = requestAnimationFrame(loop); }; this.hwLoop = requestAnimationFrame(loop); }
      if (D && D.turn === "dealer" && D.stage === "play" && !this.hwBusy) this.hwAfter();
    },
    // after a move: the events played out, then the dealer's turns a beat apart, then the end of the round
    hwAfter() {
      const g = this.game, D = g.hwDuel(); if (!D) return; this.hwBusy = true; const ev = D.events.splice(0); let delay = 0;
      for (const e of ev) { setTimeout(() => this.hwShow(e), delay); delay += e.kind === "fire" ? 1900 : e.kind === "load" ? 1400 : 600; }
      setTimeout(() => {
        this.hwBusy = false;
        if (D.stage !== "play") { const r = g.hwSettle(); this.cgNote = r.won ? (g.hwState().stage === "done" ? `The last round! ${r.pot} gold.` : `Round ${r.round} won: the pot is ${r.pot} gold. Collect, or play on.`) : `Your last candle is out. ${r.lost ? `The pot of ${r.lost} is lost.` : "The stake is the house's."}`; if (r.won) { this.cgSfx("victory", 0.55); if (r.card) this.cgSfx("cardwin", 0.5); } else this.cgSfx("cardlose", 0.5); this.renderCasino(); return; }
        if (D.turn === "dealer") { setTimeout(() => { if (g.hwDuel() === D && D.turn === "dealer") { D.dealerAct(); this.hwAfter(); } }, 700); this.renderCasino(); return; }
        this.renderCasino();
      }, delay + 200);
      this.renderCasino();
    },
    hwShow(e) {
      const now = performance.now(); (this.hwFx = this.hwFx || []).push(Object.assign({}, e, { t0: now }));
      if (e.kind === "fire") { this.cgSfx("hinge", 0.3, 1.5); setTimeout(() => this.cgSfx("spell", 0.25, 1.6), 320);
        setTimeout(() => { if (e.live) { this.cgSfx("wandboom", 0.8); this.cgSfx("zap", 0.6, 0.8); setTimeout(() => this.cgSfx(e.at === "you" ? "hurt" : "fallen", 0.55), 150); } else { this.cgSfx("miss", 0.45, 0.6); [0, 70, 150, 260].forEach((d, k) => setTimeout(() => this.cgSfx("card", 0.18, 2.4 - k * 0.3), d)); } }, 600); }
      else if (e.kind === "charm") this.cgSfx(e.c === "glass" ? "card" : e.c === "tallow" ? "heal" : e.c === "cord" ? "chain" : e.c === "whet" ? "grind" : "cardplace", 0.45);
      else if (e.kind === "load") this.cgSfx("chain", 0.4); else if (e.kind === "bound") this.cgSfx("chain", 0.3, 0.8);
      if (e.kind === "charm" && e.who === "dealer") this.cgNote = `The dealer uses ${CM.HW.CHARMS[e.c][0].toLowerCase()}${e.c === "unload" ? ` - ${e.seen ? "a live hex" : "a dud"} falls out` : ""}.`;
      if (e.kind === "fire" && e.who === "dealer") this.cgNote = `The dealer points the wand at ${e.at === "dealer" ? "itself" : "you"}...`;
    },
    hwFrame(now) {
      const g = this.game, D = g.hwDuel(), cv = this.hwCanvas, p = cv.getContext("2d"), W = 620, H = 420, fx = (this.hwFx || []).filter((f) => now - f.t0 < 2000); this.hwFx = fx;
      const bg = p.createRadialGradient(W / 2, 120, 20, W / 2, 200, 420); bg.addColorStop(0, "#3A2A1C"); bg.addColorStop(1, "#050404"); p.fillStyle = bg; p.fillRect(0, 0, W, H);
      p.fillStyle = "#FFE6A0"; p.beginPath(); p.moveTo(W / 2 - 30, 0); p.lineTo(W / 2 + 30, 0); p.lineTo(W / 2 + 14, 30); p.lineTo(W / 2 - 14, 30); p.fill(); p.fillStyle = "rgba(255,230,160,0.06)"; p.beginPath(); p.moveTo(W / 2 - 14, 30); p.lineTo(W / 2 + 14, 30); p.lineTo(W - 40, H); p.lineTo(40, H); p.fill();
      for (let k = 0; k < 26; k++) { const t = now / 1000, x = W / 2 + Math.sin(t * 0.3 + k * 2.1) * (40 + k * 6) * ((k % 7) / 7 + 0.3), y = 40 + ((k * 53 + t * 9 * (1 + (k % 3))) % (H - 60)), spread = 14 + (y - 30) * 0.75; if (Math.abs(x - W / 2) > spread) continue; p.fillStyle = `rgba(255,235,180,${0.18 + 0.18 * Math.sin(t * 2 + k)})`; p.fillRect(x, y, 1.5, 1.5); }
      // the dealer
      const sway = Math.sin(now / 900) * 3; p.fillStyle = "#16101A"; p.beginPath(); p.moveTo(W / 2 - 70, 230); p.quadraticCurveTo(W / 2 - 60, 60 + sway, W / 2, 50 + sway); p.quadraticCurveTo(W / 2 + 60, 60 + sway, W / 2 + 70, 230); p.fill();
      p.fillStyle = "#000"; p.beginPath(); p.ellipse(W / 2, 120 + sway, 28, 34, 0, 0, Math.PI * 2); p.fill(); const blink = Math.floor(now / 3000) % 7 === 0 && now % 3000 < 160; if (!blink) { p.fillStyle = "#E0C060"; p.fillRect(W / 2 - 14, 116 + sway, 7, 3); p.fillRect(W / 2 + 7, 116 + sway, 7, 3); }
      p.fillStyle = "#C8B8A0"; p.fillRect(W / 2 - 80, 222, 26, 10); p.fillRect(W / 2 + 54, 222, 26, 10);
      // the table
      const rim = p.createLinearGradient(0, 190, 0, 410); rim.addColorStop(0, "#4A2E18"); rim.addColorStop(1, "#1A0E06"); p.fillStyle = rim; p.beginPath(); p.ellipse(W / 2, 300, 300, 110, 0, 0, Math.PI * 2); p.fill();
      p.strokeStyle = "rgba(120,80,40,0.35)"; p.lineWidth = 1; for (let k = 0; k < 5; k++) { p.beginPath(); p.ellipse(W / 2, 300, 292 - k * 3, 104 - k * 1.2, 0, 0.15 + k * 0.3, 2.6 + k * 0.4); p.stroke(); }
      p.strokeStyle = "#B08A40"; p.lineWidth = 2; p.beginPath(); p.ellipse(W / 2, 297, 286, 102, 0, 0, Math.PI * 2); p.stroke(); p.lineWidth = 1;
      const felt = p.createRadialGradient(W / 2, 260, 20, W / 2, 300, 300); felt.addColorStop(0, "#2A7A50"); felt.addColorStop(1, "#123A26"); p.fillStyle = felt; p.beginPath(); p.ellipse(W / 2, 296, 284, 100, 0, 0, Math.PI * 2); p.fill();
      if (!D) { p.fillStyle = "rgba(255,240,200,0.85)"; p.font = "bold 24px Georgia, serif"; p.textAlign = "center"; const S = g.hwState(); p.fillText(S && S.stage === "between" ? "The dealer waits." : "Sit down.", W / 2, 300); p.textAlign = "left"; return; }
      // candles: the dealer's across the table, yours near
      const candles = (n, max, y, scale) => { for (let i = 0; i < max; i++) { const x = W / 2 - (max - 1) * 18 * scale + i * 36 * scale, lit = i < n; p.fillStyle = "#E8E0C8"; p.fillRect(x - 5 * scale, y - 22 * scale, 10 * scale, 22 * scale); if (lit) { const fl = 1 + Math.sin(now / 90 + i * 2) * 0.15; p.fillStyle = "rgba(255,180,60,0.25)"; p.beginPath(); p.arc(x, y - 30 * scale, 12 * scale, 0, Math.PI * 2); p.fill(); p.fillStyle = "#FFC040"; p.beginPath(); p.ellipse(x, y - 28 * scale, 3.5 * scale, 7 * scale * fl, 0, 0, Math.PI * 2); p.fill(); } else { p.fillStyle = "#2A2A2A"; p.fillRect(x - 1, y - 26 * scale, 2, 4 * scale); } } };
      candles(D.dealer.candles, D.max, 250, 0.8); candles(D.you.candles, D.max, 392, 1.1);
      // the dealer's charms, face down; the loaded charges shown, then turned over
      for (let i = 0; i < D.dealer.charms.length; i++) { p.fillStyle = "#6A1A2A"; p.fillRect(W / 2 + 110 + i * 18, 262, 14, 20); p.strokeStyle = "#C8A040"; p.strokeRect(W / 2 + 110 + i * 18 + 0.5, 262.5, 13, 19); }
      const load = [...fx].reverse().find((f) => f.kind === "load"), lastFire = [...fx].reverse().find((f) => f.kind === "fire");
      if (load && now - load.t0 < 1400 && !(lastFire && lastFire.t0 > load.t0)) { const n = load.live + load.dud; for (let i = 0; i < n; i++) { const x = W / 2 - (n - 1) * 14 + i * 28, live = i < load.live; p.fillStyle = live ? "#C82020" : "#8A8A8A"; p.beginPath(); p.arc(x, 300, 10, 0, Math.PI * 2); p.fill(); p.strokeStyle = "#000"; p.stroke(); } p.fillStyle = "#FFF"; p.font = "bold 14px Georgia, serif"; p.textAlign = "center"; p.fillText(`${load.live} live, ${load.dud} dud`, W / 2, 335); p.textAlign = "left"; }
      else if (!fx.some((f) => f.kind === "fire" && now - f.t0 < 1900)) { p.fillStyle = "#E0D8C0"; p.font = "12px Georgia, serif"; p.textAlign = "center"; p.fillText(`${D.charges.length} in the wand - ${D.liveLeft} live, ${D.dudLeft} dud${D.known !== null ? ` - the next is ${D.known ? "LIVE" : "a dud"}` : ""}${D.whet ? " - whetted" : ""}`, W / 2, 352); p.textAlign = "left"; }
      // (v13.5) the wand: it rises from the table into the shooter's hand, turns on its mark and draws closer, the tip
      // gathering light; then a blast - a white flash, a bolt, rings and sparks, the room shaking - or a fizzle: the tip
      // sputters, a few sparks drop and a curl of grey smoke goes up; then it is laid down again
      const shot = [...fx].reverse().find((f) => f.kind === "fire"), T0 = shot ? now - shot.t0 : 9999, REL = 600;
      const face = { dealer: [W / 2, 128], you: [W / 2 + 10, 450] }, hand = { dealer: [W / 2 - 50, 228], you: [W / 2 + 80, 335] }, rest = [W / 2, 300];
      let base = rest, tipDir = [-Math.cos(0.15), -Math.sin(0.15)], len = 140, lift = 0;
      if (shot && T0 < 1900) {
        const H = hand[shot.who], Tg = face[shot.at], self = shot.who === shot.at, go = Math.min(1, T0 / 450), back = T0 > 1450 ? Math.min(1, (T0 - 1450) / 450) : 0, e = (x) => x * x * (3 - 2 * x), m = e(go) * (1 - e(back));
        const near = [H[0] + (Tg[0] - H[0]) * (self ? 0.12 : 0.28), H[1] + (Tg[1] - H[1]) * (self ? 0.12 : 0.28)];
        base = [rest[0] + (near[0] - rest[0]) * m, rest[1] + (near[1] - rest[1]) * m];
        const dx = Tg[0] - near[0], dy = Tg[1] - near[1], n = Math.hypot(dx, dy) || 1, aim = [dx / n, dy / n];
        tipDir = [tipDir[0] + (aim[0] - tipDir[0]) * m, tipDir[1] + (aim[1] - tipDir[1]) * m]; const tn = Math.hypot(...tipDir) || 1; tipDir = [tipDir[0] / tn, tipDir[1] / tn];
        len = 140 - (self && shot.who === "you" ? 70 : self ? 30 : 10) * m; lift = m;
        if (T0 > 450 && T0 < REL) { base = [base[0] + (Math.random() - 0.5) * 3, base[1] + (Math.random() - 0.5) * 3]; }
        if (T0 >= REL && T0 < REL + 180 && shot.live) { base = [base[0] - tipDir[0] * 14 * (1 - (T0 - REL) / 180), base[1] - tipDir[1] * 14 * (1 - (T0 - REL) / 180)]; }   // (the kick)
      }
      const tip = [base[0] + tipDir[0] * len / 2, base[1] + tipDir[1] * len / 2], butt = [base[0] - tipDir[0] * len / 2, base[1] - tipDir[1] * len / 2];
      if (lift) { p.fillStyle = `rgba(0,0,0,${0.35 * (1 - lift)})`; p.beginPath(); p.ellipse(rest[0], rest[1] + 6, 70, 8, 0, 0, Math.PI * 2); p.fill(); }
      p.lineCap = "round"; p.strokeStyle = "#0E0A08"; p.lineWidth = 10 + lift * 2; p.beginPath(); p.moveTo(...butt); p.lineTo(...tip); p.stroke(); p.strokeStyle = "#3A2A20"; p.lineWidth = 3; p.beginPath(); p.moveTo(butt[0] + tipDir[1] * 2, butt[1] - tipDir[0] * 2); p.lineTo(tip[0] + tipDir[1] * 2, tip[1] - tipDir[0] * 2); p.stroke();
      p.strokeStyle = "#C8A040"; p.lineWidth = 12 + lift * 2; p.beginPath(); p.moveTo(...butt); p.lineTo(butt[0] + tipDir[0] * 16, butt[1] + tipDir[1] * 16); p.stroke(); p.lineCap = "butt";
      const charge = shot && T0 > 300 && T0 < REL ? (T0 - 300) / (REL - 300) : 0, glowR = 5 + charge * 9 + Math.sin(now / 120) * 1.2;
      p.save(); p.shadowColor = shot && shot.live && charge ? "#FF5030" : "#A060FF"; p.shadowBlur = 10 + charge * 26; p.fillStyle = charge ? `rgb(255,${Math.round(200 - charge * 120)},${Math.round(255 - charge * 200)})` : "#A060FF"; p.beginPath(); p.arc(tip[0], tip[1], glowR, 0, Math.PI * 2); p.fill(); p.restore();
      if (shot && T0 >= REL && T0 < REL + 900) {
        const t = (T0 - REL) / 900, Tg = face[shot.at];
        if (shot.live) {
          if (T0 < REL + 90) { p.fillStyle = `rgba(255,250,235,${0.85 * (1 - (T0 - REL) / 90)})`; p.fillRect(0, 0, W, H); }
          if (t < 0.45) { const k2 = t / 0.45; for (const [col, wdt] of [["rgba(255,90,40,0.85)", 9], ["rgba(255,240,200,1)", 3]]) { p.strokeStyle = col; p.lineWidth = wdt * (1 - k2 * 0.6); p.beginPath(); p.moveTo(...tip); const segs = 8; for (let k = 1; k <= segs; k++) { const f = k / segs, j2 = k === segs ? 0 : (Math.sin(now / 13 + k * 7.3) * 16) * (1 - f * 0.4); p.lineTo(tip[0] + (Tg[0] - tip[0]) * f - tipDir[1] * j2, tip[1] + (Tg[1] - tip[1]) * f + tipDir[0] * j2); } p.stroke(); } }
          for (let r = 0; r < 3; r++) { const rt = t - r * 0.12; if (rt <= 0) continue; p.strokeStyle = `rgba(255,${120 + r * 50},60,${Math.max(0, 0.8 - rt)})`; p.lineWidth = 4 - r; p.beginPath(); p.arc(Tg[0], Tg[1] - (shot.at === "you" ? 110 : 0), rt * 170, 0, Math.PI * 2); p.stroke(); }
          for (let k = 0; k < 26; k++) { const a = k * 2.399 + shot.at.length, sp = 120 + (k * 37) % 160, r = sp * t, cy = Tg[1] - (shot.at === "you" ? 110 : 0); p.fillStyle = k % 3 ? `rgba(255,${150 + (k * 13) % 100},60,${1 - t})` : `rgba(255,255,220,${1 - t})`; p.fillRect(Tg[0] + Math.cos(a) * r, cy + Math.sin(a) * r + t * t * 60, 3, 3); }
          p.fillStyle = `rgba(255,40,20,${0.28 * (1 - t)})`; p.fillRect(0, 0, W, H);
        } else {
          for (let k = 0; k < 9; k++) { const kt = t * 1.6 - k * 0.06; if (kt <= 0 || kt > 1) continue; const a = -Math.PI / 2 + Math.sin(k * 5.1) * 1.2; p.fillStyle = `rgba(255,${200 - k * 10},120,${1 - kt})`; p.fillRect(tip[0] + Math.cos(a) * 18 * kt, tip[1] + Math.sin(a) * 10 * kt + kt * kt * 40, 2, 2); }
          if (t < 0.35 && Math.floor(now / 45) % 2) { p.fillStyle = "rgba(255,230,180,0.9)"; p.beginPath(); p.arc(tip[0], tip[1], 4, 0, Math.PI * 2); p.fill(); }
          for (let k = 0; k < 7; k++) { const kt = t - k * 0.06; if (kt <= 0) continue; p.fillStyle = `rgba(150,150,150,${0.45 * (1 - kt)})`; p.beginPath(); p.arc(tip[0] + Math.sin(kt * 6 + k) * 10 * kt, tip[1] - kt * 70 - k * 4, 5 + kt * 14, 0, Math.PI * 2); p.fill(); }
          if (t < 0.7) { p.save(); p.globalAlpha = 1 - t / 0.7; p.fillStyle = "#D8D0C0"; p.font = "italic bold 18px Georgia, serif"; p.textAlign = "center"; p.fillText("fzzt...", tip[0] + 40, tip[1] - 20 - t * 20); p.restore(); }
        }
      }
      { const sh = shot && shot.live && T0 >= REL && T0 < REL + 350 ? (1 - (T0 - REL) / 350) * 7 : 0; cv.style.transform = sh ? `translate(${(Math.random() - 0.5) * sh}px, ${(Math.random() - 0.5) * sh}px)` : ""; }
      if (shot && shot.live && now - shot.t0 > 800 && now - shot.t0 < 1800) { const t = (now - shot.t0 - 800) / 1000, y0 = shot.at === "dealer" ? 210 : 360; p.fillStyle = `rgba(120,120,120,${0.5 * (1 - t)})`; for (let s = 0; s < 4; s++) { p.beginPath(); p.arc(W / 2 + Math.sin(now / 200 + s) * 20, y0 - t * 60 - s * 8, 6 + s * 2, 0, Math.PI * 2); p.fill(); } }
      if (T0 < 1900) { cv.style.cursor = "wait"; } else cv.style.cursor = ""; if (T0 >= 1900) { p.fillStyle = D.turn === "you" ? "#FFE070" : "#C8B8A0"; p.font = "bold 15px Georgia, serif"; p.textAlign = "center"; p.fillText(D.stage !== "play" ? (D.stage === "won" ? "The dealer's last candle goes out." : "Your last candle goes out.") : D.turn === "you" ? "Your turn" : "The dealer's turn", W / 2, 24 + 380 * 0 + 380); p.textAlign = "left"; }
      p.fillStyle = "#C8B8A0"; p.font = "12px Georgia, serif"; p.fillText(`Round ${D.round}`, 12, 20);
    },
  });
}
