"use strict";
// Bones, the window's side: a craps table in green felt with a padded rail - the point numbers along the top (the puck
// on the point, white ON, or black OFF in the Don't Come corner), the Place 6 and 8, the Field with its numbers, Any
// Seven in the middle, the Don't Pass bar and the Pass Line curving round the bottom with the Odds behind it; chips
// stacked on each spot. A throw: the dice tumble across a canvas strip of felt, spinning and bouncing off the far wall,
// their shadows under them, and settle; then the winning spots flash and the chips go. The rules are 64zy-craps.js.
CM.CG_TABLES.push(["craps", "Bones"]);
{ const floor0 = CM.UI.prototype.renderFloor, CR = CM.CRAPS;
  const pips = { 1: [[0.5, 0.5]], 2: [[0.28, 0.28], [0.72, 0.72]], 3: [[0.25, 0.25], [0.5, 0.5], [0.75, 0.75]], 4: [[0.28, 0.28], [0.72, 0.28], [0.28, 0.72], [0.72, 0.72]], 5: [[0.27, 0.27], [0.73, 0.27], [0.5, 0.5], [0.27, 0.73], [0.73, 0.73]], 6: [[0.28, 0.24], [0.72, 0.24], [0.28, 0.5], [0.72, 0.5], [0.28, 0.76], [0.72, 0.76]] };
  Object.assign(CM.UI.prototype, {
    renderFloor(box) { if (this.cgView === "craps") return this.cgCraps(box); return floor0.call(this, box); },
    cgCraps(box) {
      const g = this.game, K = g.crapsState(), B = K.bets, on = !!K.point, flash = this.crFlash || {}, chip = (t) => (B[t] ? `<i class="crchip">${B[t]}</i>` : ""), spot = (t, label, cls = "") => `<div class="crspot ${cls}${flash[t] ? ` fl-${flash[t]}` : ""}" data-crb="${t}">${label}${chip(t)}</div>`;
      const nums = [4, 5, 6, 8, 9, 10].map((n) => `<div class="crnum${K.point === n ? " pt" : ""}">${n === 6 ? "SIX" : n === 9 ? "NINE" : n}${K.point === n ? `<span class="puck on">ON</span>` : ""}</div>`).join("");
      box.innerHTML = `<div class="cgtable crapstbl"><h3>Bones</h3><p class="lore">A long table with a padded rail and a stickman in a waistcoat. "New shooter coming out," he calls, and pushes the dice across with his hooked stick. "Bets on the line."</p>
        <div class="crfelt"><div class="crtop"><div class="crdc">${on ? "" : `<span class="puck off">OFF</span>`}DON'T COME</div>${nums}</div>
        <div class="crmid">${spot("place6", "PLACE 6<small>pays 7 to 6</small>")}${spot("seven", "ANY SEVEN<small>4 to 1</small>", "red")}${spot("place8", "PLACE 8<small>pays 7 to 6</small>")}</div>
        ${spot("field", `FIELD<small><b>2</b> 3 4 9 10 11 <b>12</b> - 2 pays double, 12 pays triple</small>`, "field")}
        ${spot("dont", "DON'T PASS BAR <small>12 pushes</small>", "dont")}${spot("pass", "PASS LINE", "pass")}${spot("odds", "ODDS<small>true odds, up to 3×</small>", `odds${on && B.pass ? "" : " off"}`)}</div>
        <canvas class="crdice" width="640" height="120"></canvas>
        ${this.cgBetRow("The chip")}<div class="cgnote">${this.cgNote || ""}</div>${this.crCard ? this.cgCardWon(this.crCard) : ""}
        <div class="row"><button class="primary" data-crroll ${Object.values(B).some((v) => v > 0) && !this.cgBusy ? "" : "disabled"}>Throw the dice</button>${B.place6 || B.place8 ? `<button data-crdown>Take down the place bets</button>` : ""}<button data-leave>Leave</button></div>
        <div class="small">Click a spot to put the chip on it. The line bets go down on the come-out roll; the odds behind a pass bet once the point is on. Place bets go in sixes and stay up until a seven (they rest on the come-out). Pass and Don't Pass give back 98.6%, the odds 100%, Place 6 and 8 98.5%, the Field 97.2%, Any Seven 83.3%. A shooter who makes four points in a row wins a card. Points made by this shooter: ${K.made}.</div>${this.cgStats("craps")}</div>`;
      this.cgWireBet(box); const q = (s) => box.querySelector(s); q("[data-leave]").addEventListener("click", () => this.closeDialogs());
      box.querySelectorAll("[data-crb]").forEach((el) => el.addEventListener("click", () => { if (this.cgBusy) return; const why = g.crapsBet(el.dataset.crb, this.cgBet || 0); this.cgNote = why; this.crFlash = {}; this.crCard = null; this.cgSfx(why ? "miss" : "coin", why ? 0.3 : 0.25, 1.3); this.renderCasino(); }));
      if (q("[data-crdown]")) q("[data-crdown]").addEventListener("click", () => { const v = g.crapsTakeDown("place6") + g.crapsTakeDown("place8"); this.cgNote = `${v} gold taken down.`; this.renderCasino(); });
      const cv = q(".crdice"); this.crDraw(cv, this.crShown || (K.last ? K.last.d : [5, 2]), null);
      q("[data-crroll]").addEventListener("click", () => {
        if (this.cgBusy) return; const r = g.crapsRoll(); if (r.error) { this.cgNote = r.error; this.renderCasino(); return; } this.cgBusy = true; q("[data-crroll]").disabled = true; this.cgSfx("chain", 0.45, 1.4);
        const t0 = performance.now(), dur = 1300, R = Math.random, paths = [0, 1].map((i) => ({ x0: 40, y0: 30 + i * 40, vx: 520 + R() * 120, vy: (R() - 0.5) * 160, spin: 8 + R() * 6 }));
        const step = (now) => { const t = Math.min(1, (now - t0) / dur), e = 1 - Math.pow(1 - t, 2.4); this.crDraw(cv, t < 0.92 ? [1 + Math.floor(R() * 6), 1 + Math.floor(R() * 6)] : r.dice, paths.map((P, i) => { let x = P.x0 + P.vx * e * 1.1, y = P.y0 + P.vy * e; if (x > 600) x = 1200 - x; y = Math.max(14, Math.min(106, y)); return { x: t >= 1 ? 470 + i * 70 : x, y: t >= 1 ? 60 : y, a: (1 - e) * P.spin, h: Math.abs(Math.sin(e * Math.PI * 3)) * (1 - e) * 16 }; }));
          if (t > 0.3 && Math.random() < 0.08 && t < 0.9) this.cgSfx("step", 0.15, 2);
          if (t < 1) { requestAnimationFrame(step); return; }
          this.crShown = r.dice; this.cgBusy = false; this.cgSfx("cardplace", 0.5, 0.8); const fl = this.crFlash = {}; for (const x of r.res) fl[x.type] = x.lost ? "lose" : "win"; this.crCard = r.card;
          this.cgNote = `${r.sum}${r.sum === 7 && r.sevenOut ? " - seven out!" : r.made ? " - the point is made!" : !r.was && r.point ? ` - the point is ${r.point}` : r.sum === 2 || r.sum === 3 || r.sum === 12 ? (r.was ? "" : " - craps!") : r.sum === 11 && !r.was ? " - yo-leven!" : ""}${r.back ? `. ${r.back} gold back.` : "."}`;
          this.renderCasino(); const b2 = this.$("#casino-body"); if (r.back) { this.cgSfx("coin", 0.5); this.cgCoins(b2, Math.min(24, 4 + Math.round(r.back / 20))); } if (r.card) this.cgSfx("cardwin", 0.6); if (r.sevenOut) this.cgSfx("cardlose", 0.4); };
        requestAnimationFrame(step);
      });
    },
    // the dice on their strip of felt
    crDraw(cv, faces, at) {
      const p = cv.getContext("2d"), W = cv.width, H = cv.height, felt = p.createLinearGradient(0, 0, 0, H); felt.addColorStop(0, "#1E6A40"); felt.addColorStop(1, "#0E4A2A"); p.fillStyle = felt; p.fillRect(0, 0, W, H);
      p.fillStyle = "rgba(255,255,255,0.03)"; for (let k = 0; k < 120; k++) p.fillRect((k * 53) % W, (k * 29) % H, 1, 1); p.fillStyle = "#3A2210"; p.fillRect(W - 8, 0, 8, H); for (let y = 0; y < H; y += 10) { p.fillStyle = y % 20 ? "#5A3A20" : "#7A5030"; p.fillRect(W - 8, y, 8, 5); }
      const pos = at || [{ x: 470, y: 60, a: 0.1, h: 0 }, { x: 540, y: 60, a: -0.15, h: 0 }];
      faces.forEach((f, i) => { const P = pos[i], s = 40; p.fillStyle = "rgba(0,0,0,0.35)"; p.beginPath(); p.ellipse(P.x + 4, P.y + 18, 22, 7, 0, 0, Math.PI * 2); p.fill(); p.save(); p.translate(P.x, P.y - P.h); p.rotate(P.a);
        const g2 = p.createLinearGradient(-s / 2, -s / 2, s / 2, s / 2); g2.addColorStop(0, "#F02838"); g2.addColorStop(1, "#A01020"); p.fillStyle = g2; p.beginPath(); p.roundRect ? p.roundRect(-s / 2, -s / 2, s, s, 8) : p.rect(-s / 2, -s / 2, s, s); p.fill(); p.fillStyle = "rgba(255,255,255,0.25)"; p.fillRect(-s / 2 + 5, -s / 2 + 4, s - 10, 4);
        p.fillStyle = "#FFF8F0"; for (const [x, y] of pips[f]) { p.beginPath(); p.arc(-s / 2 + x * s, -s / 2 + y * s, 4, 0, Math.PI * 2); p.fill(); } p.restore(); });
    },
  });
}
