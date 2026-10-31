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
      for (const e of ev) { setTimeout(() => this.hwShow(e), delay); delay += e.kind === "fire" ? 900 : e.kind === "load" ? 1400 : 600; }
      setTimeout(() => {
        this.hwBusy = false;
        if (D.stage !== "play") { const r = g.hwSettle(); this.cgNote = r.won ? (g.hwState().stage === "done" ? `The last round! ${r.pot} gold.` : `Round ${r.round} won: the pot is ${r.pot} gold. Collect, or play on.`) : `Your last candle is out. ${r.lost ? `The pot of ${r.lost} is lost.` : "The stake is the house's."}`; if (r.won) { this.cgSfx("victory", 0.55); if (r.card) this.cgSfx("cardwin", 0.5); } else this.cgSfx("cardlose", 0.5); this.renderCasino(); return; }
        if (D.turn === "dealer") { setTimeout(() => { if (g.hwDuel() === D && D.turn === "dealer") { D.dealerAct(); this.hwAfter(); } }, 700); this.renderCasino(); return; }
        this.renderCasino();
      }, delay + 200);
      this.renderCasino();
    },
    hwShow(e) {
      const now = performance.now(); (this.hwFx = this.hwFx || []).push(Object.assign({ at: now }, e));
      if (e.kind === "fire") { this.cgSfx("hinge", 0.3, 1.5); setTimeout(() => { if (e.live) { this.cgSfx("zap", 0.7); this.cgSfx(e.at === "you" ? "hurt" : "fallen", 0.5); } else this.cgSfx("miss", 0.45, 0.7); }, 420); }
      else if (e.kind === "charm") this.cgSfx(e.c === "glass" ? "card" : e.c === "tallow" ? "heal" : e.c === "cord" ? "chain" : e.c === "whet" ? "grind" : "cardplace", 0.45);
      else if (e.kind === "load") this.cgSfx("chain", 0.4); else if (e.kind === "bound") this.cgSfx("chain", 0.3, 0.8);
      if (e.kind === "charm" && e.who === "dealer") this.cgNote = `The dealer uses ${CM.HW.CHARMS[e.c][0].toLowerCase()}${e.c === "unload" ? ` - ${e.seen ? "a live hex" : "a dud"} falls out` : ""}.`;
      if (e.kind === "fire" && e.who === "dealer") this.cgNote = `The dealer points the wand at ${e.at === "dealer" ? "itself" : "you"}...`;
    },
    hwFrame(now) {
      const g = this.game, D = g.hwDuel(), cv = this.hwCanvas, p = cv.getContext("2d"), W = 620, H = 420, fx = (this.hwFx || []).filter((f) => now - f.at < 2000); this.hwFx = fx;
      const bg = p.createRadialGradient(W / 2, 120, 20, W / 2, 200, 420); bg.addColorStop(0, "#3A2A1C"); bg.addColorStop(1, "#050404"); p.fillStyle = bg; p.fillRect(0, 0, W, H);
      p.fillStyle = "#FFE6A0"; p.beginPath(); p.moveTo(W / 2 - 30, 0); p.lineTo(W / 2 + 30, 0); p.lineTo(W / 2 + 14, 30); p.lineTo(W / 2 - 14, 30); p.fill(); p.fillStyle = "rgba(255,230,160,0.06)"; p.beginPath(); p.moveTo(W / 2 - 14, 30); p.lineTo(W / 2 + 14, 30); p.lineTo(W - 40, H); p.lineTo(40, H); p.fill();
      // the dealer
      const sway = Math.sin(now / 900) * 3; p.fillStyle = "#16101A"; p.beginPath(); p.moveTo(W / 2 - 70, 230); p.quadraticCurveTo(W / 2 - 60, 60 + sway, W / 2, 50 + sway); p.quadraticCurveTo(W / 2 + 60, 60 + sway, W / 2 + 70, 230); p.fill();
      p.fillStyle = "#000"; p.beginPath(); p.ellipse(W / 2, 120 + sway, 28, 34, 0, 0, Math.PI * 2); p.fill(); const blink = Math.floor(now / 3000) % 7 === 0 && now % 3000 < 160; if (!blink) { p.fillStyle = "#E0C060"; p.fillRect(W / 2 - 14, 116 + sway, 7, 3); p.fillRect(W / 2 + 7, 116 + sway, 7, 3); }
      p.fillStyle = "#C8B8A0"; p.fillRect(W / 2 - 80, 222, 26, 10); p.fillRect(W / 2 + 54, 222, 26, 10);
      // the table
      p.fillStyle = "#2A1A10"; p.beginPath(); p.ellipse(W / 2, 300, 300, 110, 0, 0, Math.PI * 2); p.fill(); p.fillStyle = "#1E5A3A"; p.beginPath(); p.ellipse(W / 2, 296, 284, 100, 0, 0, Math.PI * 2); p.fill();
      if (!D) { p.fillStyle = "rgba(255,240,200,0.85)"; p.font = "bold 24px Georgia, serif"; p.textAlign = "center"; const S = g.hwState(); p.fillText(S && S.stage === "between" ? "The dealer waits." : "Sit down.", W / 2, 300); p.textAlign = "left"; return; }
      // candles: the dealer's across the table, yours near
      const candles = (n, max, y, scale) => { for (let i = 0; i < max; i++) { const x = W / 2 - (max - 1) * 18 * scale + i * 36 * scale, lit = i < n; p.fillStyle = "#E8E0C8"; p.fillRect(x - 5 * scale, y - 22 * scale, 10 * scale, 22 * scale); if (lit) { const fl = 1 + Math.sin(now / 90 + i * 2) * 0.15; p.fillStyle = "rgba(255,180,60,0.25)"; p.beginPath(); p.arc(x, y - 30 * scale, 12 * scale, 0, Math.PI * 2); p.fill(); p.fillStyle = "#FFC040"; p.beginPath(); p.ellipse(x, y - 28 * scale, 3.5 * scale, 7 * scale * fl, 0, 0, Math.PI * 2); p.fill(); } else { p.fillStyle = "#2A2A2A"; p.fillRect(x - 1, y - 26 * scale, 2, 4 * scale); } } };
      candles(D.dealer.candles, D.max, 250, 0.8); candles(D.you.candles, D.max, 392, 1.1);
      // the dealer's charms, face down; the loaded charges shown, then turned over
      for (let i = 0; i < D.dealer.charms.length; i++) { p.fillStyle = "#6A1A2A"; p.fillRect(W / 2 + 110 + i * 18, 262, 14, 20); p.strokeStyle = "#C8A040"; p.strokeRect(W / 2 + 110 + i * 18 + 0.5, 262.5, 13, 19); }
      const load = [...fx].reverse().find((f) => f.kind === "load"), lastFire = [...fx].reverse().find((f) => f.kind === "fire");
      if (load && now - load.at < 1400 && !(lastFire && lastFire.at > load.at)) { const n = load.live + load.dud; for (let i = 0; i < n; i++) { const x = W / 2 - (n - 1) * 14 + i * 28, live = i < load.live; p.fillStyle = live ? "#C82020" : "#8A8A8A"; p.beginPath(); p.arc(x, 300, 10, 0, Math.PI * 2); p.fill(); p.strokeStyle = "#000"; p.stroke(); } p.fillStyle = "#FFF"; p.font = "bold 14px Georgia, serif"; p.textAlign = "center"; p.fillText(`${load.live} live, ${load.dud} dud`, W / 2, 335); p.textAlign = "left"; }
      else { p.fillStyle = "#E0D8C0"; p.font = "12px Georgia, serif"; p.textAlign = "center"; p.fillText(`${D.charges.length} in the wand - ${D.liveLeft} live, ${D.dudLeft} dud${D.known !== null ? ` - the next is ${D.known ? "LIVE" : "a dud"}` : ""}${D.whet ? " - whetted" : ""}`, W / 2, 352); p.textAlign = "left"; }
      // the wand: lying between you, or swung to its mark
      const shot = [...fx].reverse().find((f) => f.kind === "fire"), k = shot ? Math.min(1, (now - shot.at) / 400) : 0, aimUp = shot && shot.at === "dealer";
      const rest = -0.15, ang = shot ? rest + (aimUp ? -1.45 : 1.45) * Math.min(1, k * 1.4) * (now - shot.at < 1400 ? 1 : Math.max(0, 1 - (now - shot.at - 1400) / 400)) : rest;
      p.save(); p.translate(W / 2, 300); p.rotate(ang); p.fillStyle = "#1A1210"; p.fillRect(-70, -4, 140, 8); p.fillStyle = "#C8A040"; p.fillRect(-70, -5, 14, 10); p.fillStyle = "#A060FF"; p.beginPath(); p.arc(70, 0, 5, 0, Math.PI * 2); p.fill(); p.restore();
      if (shot && now - shot.at > 400 && now - shot.at < 900) { const t = (now - shot.at - 400) / 500, ty = aimUp ? 130 : 395; if (shot.live) { p.strokeStyle = `rgba(255,${80 + 100 * (1 - t)},60,${1 - t})`; p.lineWidth = 4; p.beginPath(); p.moveTo(W / 2, 300); for (let s = 1; s <= 6; s++) p.lineTo(W / 2 + (Math.random() - 0.5) * 40, 300 + ((ty - 300) * s) / 6); p.stroke(); p.fillStyle = `rgba(255,60,40,${0.35 * (1 - t)})`; p.fillRect(0, 0, W, H); }
        else { p.fillStyle = `rgba(180,180,180,${0.6 * (1 - t)})`; for (let s = 0; s < 6; s++) { p.beginPath(); p.arc(W / 2 + Math.cos(s) * 30 * t + (aimUp ? 0 : 0), 300 + (aimUp ? -1 : 1) * 60 * t + Math.sin(s * 2) * 10, 8 + 10 * t, 0, Math.PI * 2); p.fill(); } } }
      if (shot && shot.live && now - shot.at > 800 && now - shot.at < 1800) { const t = (now - shot.at - 800) / 1000, y0 = shot.at === "dealer" ? 210 : 360; p.fillStyle = `rgba(120,120,120,${0.5 * (1 - t)})`; for (let s = 0; s < 4; s++) { p.beginPath(); p.arc(W / 2 + Math.sin(now / 200 + s) * 20, y0 - t * 60 - s * 8, 6 + s * 2, 0, Math.PI * 2); p.fill(); } }
      p.fillStyle = D.turn === "you" ? "#FFE070" : "#C8B8A0"; p.font = "bold 15px Georgia, serif"; p.textAlign = "center"; p.fillText(D.stage !== "play" ? (D.stage === "won" ? "The dealer's last candle goes out." : "Your last candle goes out.") : D.turn === "you" ? "Your turn" : "The dealer's turn", W / 2, 24 + 380 * 0 + 380); p.textAlign = "left";
      p.fillStyle = "#C8B8A0"; p.font = "12px Georgia, serif"; p.fillText(`Round ${D.round}`, 12, 20);
    },
  });
}
