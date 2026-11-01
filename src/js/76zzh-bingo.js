"use strict";
// The Bell Hall, the window's side: the old chapel's nave with the priest at a brass cage on the altar step - the
// cage turns, the balls tumble in it, and each drawn ball rolls out big with its rune and number while she calls it;
// the board of all seventy-five behind lights each number called; the party's cards below, a stamp of red ink thumped
// on each number daubed (the hall's dauber does it if asked); the pattern of the game shown in a little card of its
// own; "Bingo!" to call. When anyone calls: the bell rings, the winners are read out, and the pot shared. The rules
// are 64zzh-bingo.js.
CM.CG_TABLES.push(["bingo", "The Bell Hall"]);
{ const floor0 = CM.UI.prototype.renderFloor, BGO = CM.BGO, CW = 340, CH = 210, COLS = ["#C03838", "#E0A030", "#3A9A50", "#3070C0", "#8A50C0"];
  // the pattern's little picture
  const patCells = (id) => { const m = Array(25).fill(false);
    if (id === "line") for (let x = 0; x < 5; x++) m[10 + x] = true; else if (id === "corners") [0, 4, 20, 24].forEach((k) => { m[k] = true; }); else if (id === "x") for (let k = 0; k < 5; k++) { m[k * 6] = true; m[(k + 1) * 4] = true; } else if (id === "frame") for (let k = 0; k < 25; k++) m[k] = k < 5 || k >= 20 || k % 5 === 0 || k % 5 === 4; else m.fill(true); return m; };
  Object.assign(CM.UI.prototype, {
    renderFloor(box) { if (this.cgView === "bingo") return this.cgBingo(box); return floor0.call(this, box); },
    cgBingo(box) {
      const g = this.game, B = g.bgStore(), G = g.bgGame(), live = G && G.stage === "play", room = this.bgRoom || "copper", count = this.bgCount || 2, auto = this.bgAuto !== false, pat = G ? BGO.PATTERNS.find((p) => p.id === G.pat) : g.bgPattern(), called = G ? g.bgCalled(G) : new Set(), last = G && G.drawn ? G.balls[G.drawn - 1] : 0;
      const pm = patCells(pat.id), mini = `<div class="bgpat" title="${pat.name}">${pm.map((v) => `<i class="${v ? "on" : ""}"></i>`).join("")}</div>`;
      const board = BGO.RUNES.map((r, c) => `<div class="bgrow"><b style="background:${COLS[c]}">${r}</b>${Array.from({ length: 15 }, (_, k) => c * 15 + k + 1).map((n) => `<span class="${called.has(n) ? "on" : ""}${n === last ? " last" : ""}">${n}</span>`).join("")}</div>`).join("");
      const done = G ? g.bgDone(G) : [];
      const cards = G ? G.cards.map((cd, i) => `<div class="bgcard${done[i] ? " done" : ""}${G.result && G.result.mine[i] ? " won" : ""}"><div class="bghead">${BGO.RUNES.map((r, c) => `<b style="background:${COLS[c]}">${r}</b>`).join("")}</div><div class="bggrid">${cd.map((n, k) => `<span data-bgd="${i}:${k}" class="${G.daub[i][k] ? "d" : ""}${n === 0 ? " free" : ""}">${n || "★"}</span>`).join("")}</div></div>`).join("") : "";
      box.innerHTML = `<div class="cgtable bingo"><h3>The Bell Hall</h3><p class="lore">The Joker bought the old chapel next door and kept the bell. Of an evening the pews fill with half the village and their cards, and the priest's sister turns the brass cage on the altar step. "Eyes down," she says, "for ${pat.name.toLowerCase()}."</p>
        <div class="bgtop"><canvas class="bgcage" width="${CW}" height="${CH}"></canvas><div class="bgside"><div class="bgboard">${board}</div><div class="bgpatrow">${mini}<div><b>${pat.name}</b><br><span class="small">${G ? `${G.hall.length} cards in the hall · pot ${Math.floor((G.cards.length + G.hall.length) * G.price * BGO.share)} gold · ball ${G.drawn}` : "the next game's pattern"}</span></div></div></div></div>
        <div class="bgcards">${cards}</div>
        <div class="cgnote">${this.cgNote || ""}</div>${this.bgCard ? this.cgCardWon(this.bgCard) : ""}
        <div class="row">${live ? `<button class="primary bgcall${done.some(Boolean) ? " ready" : ""}" data-bgcall>Bingo!</button><button data-bgfast>${this.bgFast ? "Slower" : "Faster"}</button>` : `${Object.entries(BGO.ROOMS).map(([k, R]) => `<button data-bgroom="${k}" class="${k === room ? "primary" : ""}">${R.name[4].toUpperCase() + R.name.slice(5)} - ${R.price} a card</button>`).join("")}`}</div>
        ${live ? "" : `<div class="row"><span>Cards:</span>${[1, 2, 3, 4].map((n) => `<button data-bgn="${n}" class="${n === count ? "primary" : ""}">${n}</button>`).join("")}<label><input type="checkbox" data-bgauto ${auto ? "checked" : ""}> the hall's dauber</label><button class="primary" data-bgbuy>Buy ${count} card${count > 1 ? "s" : ""} (${count * BGO.ROOMS[room].price} gold)</button><button data-leave>Leave</button></div>`}
        <div class="small">Daub each number called on your cards (click it) - or let the hall's dauber do it - and call Bingo! when the game's pattern is done. When anyone calls, every finished card shares the pot: 85 in every 100 gold the hall took. A win pays tickets too (one for each 25 gold won); a coverall won the first time brings a card. Patterns in turn: ${BGO.PATTERNS.map((p) => p.name.toLowerCase()).join(", ")}. Games ${B.games}, won ${B.wins}, best ${B.best} gold.</div>${this.cgStats("bingo")}</div>`;
      const q = (s) => box.querySelector(s); if (q("[data-leave]")) q("[data-leave]").addEventListener("click", () => this.closeDialogs());
      box.querySelectorAll("[data-bgroom]").forEach((b) => b.addEventListener("click", () => { this.bgRoom = b.dataset.bgroom; this.renderCasino(); }));
      box.querySelectorAll("[data-bgn]").forEach((b) => b.addEventListener("click", () => { this.bgCount = Number(b.dataset.bgn); this.renderCasino(); }));
      if (q("[data-bgauto]")) q("[data-bgauto]").addEventListener("change", (e) => { this.bgAuto = e.target.checked; });
      if (q("[data-bgbuy]")) q("[data-bgbuy]").addEventListener("click", () => { const r = g.bgBuy(room, count, auto); this.cgNote = r.error || `Eyes down for ${BGO.PATTERNS.find((p) => p.id === r.pat).name.toLowerCase()}!`; this.bgCard = null; this.bgNextAt = performance.now() + 1500; this.cgSfx(r.error ? "miss" : "door", 0.4); this.renderCasino(); });
      if (q("[data-bgfast]")) q("[data-bgfast]").addEventListener("click", () => { this.bgFast = !this.bgFast; this.renderCasino(); });
      if (q("[data-bgcall]")) q("[data-bgcall]").addEventListener("click", () => { const r = g.bgCall(); if (r.error) { this.cgNote = r.error; this.cgSfx("miss", 0.3); const n = q(".cgnote"); if (n) n.textContent = r.error; return; } this.bgResult(r); });
      box.querySelectorAll("[data-bgd]").forEach((el) => el.addEventListener("click", () => { const [i, k] = el.dataset.bgd.split(":").map(Number); if (g.bgDaub(i, k)) { el.classList.add("d", "stamp"); this.cgSfx("slam", 0.2, 1.6); const G2 = g.bgGame(); if (G2 && g.bgDone(G2)[i]) { el.closest(".bgcard").classList.add("done"); const c = q("[data-bgcall]"); if (c) c.classList.add("ready"); } } else this.cgSfx("miss", 0.15, 1.5); }));
      this.bgCanvas = q(".bgcage");
      if (!this.bgLoop) { const loop = (now) => { if (!this.bgCanvas || !this.bgCanvas.isConnected || this.cgView !== "bingo") { this.bgLoop = null; return; } this.bgTick(now); this.bgFrame(now); this.bgLoop = requestAnimationFrame(loop); }; this.bgLoop = requestAnimationFrame(loop); }
    },
    bgTick(now) { const g = this.game, G = g.bgGame(); if (!G || G.stage !== "play" || now < (this.bgNextAt || 0)) return; this.bgNextAt = now + (this.bgFast ? 1100 : 2200);
      const r = g.bgDraw(); if (!r) return; this.bgBall = { n: r.ball, at: now }; this.cgSfx("chain", 0.25, 1.6); this.cgNote = `${r.letter} - ${r.ball}.`;
      if (r.won !== undefined) { setTimeout(() => this.bgResult(r), 900); this.bgNextAt = 1e15; } else this.renderCasino(); },
    bgResult(r) { const who = r.hallWho.length ? r.hallWho.slice(0, 3).join(", ") + (r.hallWho.length > 3 ? ` and ${r.hallWho.length - 3} more` : "") : "";
      this.cgNote = r.won ? `BINGO! ${who ? `You share it with ${who}: ` : "Yours alone: "}${r.won} gold of the ${r.pool} pot after ${r.balls} balls${r.tickets ? `, and ${r.tickets} tickets` : ""}${r.card ? `, and a card - ${r.card}` : ""}.` : `"Bingo!" - ${who} ${r.hallWho.length > 1 ? "share" : "takes"} the ${r.pool}-gold pot after ${r.balls} balls.`;
      this.bgBell = performance.now(); this.cgSfx("tablebell", 0.5, 0.7); setTimeout(() => this.cgSfx("tablebell", 0.4, 0.7), 350); if (r.won) { this.cgSfx("victory", 0.5); if (r.card) { this.bgCard = r.card; setTimeout(() => this.cgSfx("cardwin", 0.5), 500); } } this.renderCasino(); if (r.won) this.cgCoins(this.$("#casino-body"), 12); },
    bgFrame(now) {
      const p = this.bgCanvas.getContext("2d"), G = this.game.bgGame(), live = G && G.stage === "play";
      const bg = p.createLinearGradient(0, 0, 0, CH); bg.addColorStop(0, "#3A2A40"); bg.addColorStop(1, "#1A1218"); p.fillStyle = bg; p.fillRect(0, 0, CW, CH);
      for (let k = 0; k < 3; k++) { const x = 40 + k * 130; p.fillStyle = "rgba(255,220,150,0.08)"; p.beginPath(); p.moveTo(x, 0); p.lineTo(x + 30, 0); p.lineTo(x + 70, CH); p.lineTo(x - 20, CH); p.fill(); p.fillStyle = k === 1 ? "#5A3A6A" : "#3A5A8A"; p.beginPath(); p.moveTo(x, 40); p.arc(x + 15, 40, 15, Math.PI, 0); p.lineTo(x + 30, 80); p.lineTo(x, 80); p.fill(); }
      if (this.bgBell && now - this.bgBell < 1500) { const t = (now - this.bgBell) / 1500; p.save(); p.translate(CW - 40, 30); p.rotate(Math.sin(t * 20) * 0.5 * (1 - t)); p.fillStyle = "#D8A840"; p.beginPath(); p.moveTo(-14, 18); p.quadraticCurveTo(-12, -16, 0, -16); p.quadraticCurveTo(12, -16, 14, 18); p.fill(); p.restore(); }
      // the cage
      const cx = 100, cy = 110, R = 62, spin = live ? now / 250 : now / 1500; p.fillStyle = "#4A3020"; p.fillRect(cx - 50, cy + R - 4, 100, 12); p.fillRect(cx - 4, cy, 8, R);
      for (let k = 0; k < 22; k++) { const a = spin * (0.7 + (k % 5) * 0.13) + k * 1.7, r = (k % 4) * 11 + 10, bx = cx + Math.cos(a) * r, by = cy + 18 + Math.sin(a * 1.3) * (R - 30) * 0.6 + (live ? Math.abs(Math.sin(now / 90 + k)) * -12 : 10); p.fillStyle = COLS[k % 5]; p.beginPath(); p.arc(bx, by, 7, 0, Math.PI * 2); p.fill(); p.fillStyle = "#FFFFFF"; p.beginPath(); p.arc(bx - 1, by - 1, 3, 0, Math.PI * 2); p.fill(); }
      p.strokeStyle = "#E0B860"; p.lineWidth = 2; p.beginPath(); p.arc(cx, cy, R, 0, Math.PI * 2); p.stroke(); p.lineWidth = 1; for (let k = 0; k < 8; k++) { const a = spin + (k * Math.PI) / 8; p.strokeStyle = "rgba(224,184,96,0.55)"; p.beginPath(); p.ellipse(cx, cy, Math.abs(Math.cos(a)) * R, R, 0, 0, Math.PI * 2); p.stroke(); }
      p.strokeStyle = "#B08840"; p.lineWidth = 3; p.beginPath(); p.moveTo(cx + R, cy); p.lineTo(cx + R + 14 + Math.cos(spin * 2) * 8, cy + Math.sin(spin * 2) * 8); p.stroke(); p.lineWidth = 1;
      // the ball drawn
      const Bb = this.bgBall; if (Bb && G) { const t = Math.min(1, (now - Bb.at) / 700), x = cx + R + (250 - cx - R) * t, y = cy + 40 - Math.sin(t * Math.PI) * 50 - 20 * t, rr = 10 + 36 * t, c = Math.floor((Bb.n - 1) / 15); p.fillStyle = "rgba(0,0,0,0.3)"; p.beginPath(); p.ellipse(x + 4, cy + 72, rr, rr * 0.25, 0, 0, Math.PI * 2); p.fill();
        const gr = p.createRadialGradient(x - rr * 0.3, y - rr * 0.3, 2, x, y, rr); gr.addColorStop(0, "#FFFFFF"); gr.addColorStop(0.25, COLS[c]); gr.addColorStop(1, "#1A1A1A"); p.fillStyle = gr; p.beginPath(); p.arc(x, y, rr, 0, Math.PI * 2); p.fill(); p.fillStyle = "#FBF4E0"; p.beginPath(); p.arc(x, y, rr * 0.6, 0, Math.PI * 2); p.fill();
        p.fillStyle = "#1A1A22"; p.textAlign = "center"; p.font = `bold ${Math.round(rr * 0.5)}px Georgia`; p.fillText(String(Bb.n), x, y + rr * 0.32); p.font = `${Math.round(rr * 0.32)}px serif`; p.fillText(BGO.RUNES[c], x, y - rr * 0.2); p.textAlign = "left"; }
      else { p.fillStyle = "#F0E0B0"; p.font = "14px Georgia"; p.fillText(live ? "Eyes down…" : "Buy cards to play", 190, 115); }
    },
  });
}
