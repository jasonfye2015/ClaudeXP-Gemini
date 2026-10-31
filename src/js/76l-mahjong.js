"use strict";
// The Tilewright's Table, the window's side (the twenty-third big update): ivory tiles stacked with their depth on a
// canvas, each face painted in code - coins, runes and blades, the winds, the elements, potions and seasons - the
// free ones bright and the covered a shade darker; a picked tile lifts in gold, a pair taken flies together and is
// gone in a glint; a hint, the shuffles, the pay by how many were used. The rules are 64v-mahjong.js.
CM.CG_TABLES.push(["mahjong", "The Tilewright's Table"]);
CM.MJ_ART = { TW: 44, TH: 56, DX: 5, DY: 6 };
{ const floor0 = CM.UI.prototype.renderFloor;
  // the layout's bounds, for centring: [minX, maxX, minY, maxY, maxZ]
  const MJ_bounds = (T) => { if (T.bounds) return T.bounds; const ts = T.tiles; T.bounds = [Math.min(...ts.map((t) => t.x)), Math.max(...ts.map((t) => t.x)), Math.min(...ts.map((t) => t.y)), Math.max(...ts.map((t) => t.y)), Math.max(...ts.map((t) => t.z))]; return T.bounds; };
  Object.assign(CM.UI.prototype, {
    renderFloor(box) { if (this.cgView === "mahjong") return this.cgMahjong(box); return floor0.call(this, box); },
    cgMahjong(box) {
      const g = this.game, MJ = CM.MJ, S = g.mjState(), T = g.mjTable(), live = S && S.stage === "play", bet = live ? S.bet : (this.cgBet === undefined ? 5 : this.cgBet), last = S && S.last;
      this.mjLayout = this.mjLayout || "keep";
      const pays = MJ.PAY[T ? T.layout : this.mjLayout].map((m, i) => `<tr class="${live && T && MJ.shuffles - T.shuffles === i ? "now" : ""}"><td>Cleared with ${i ? `${i} shuffle${i > 1 ? "s" : ""}` : "no shuffle"}</td><td>${Math.round(bet * m)}${i === 0 ? " <small>+ rare card</small>" : i === 1 ? " <small>+ common card</small>" : ""}</td></tr>`).join("");
      box.innerHTML = `<div class="cgtable mahjong"><h3>The Tilewright's Table</h3><div class="mjwrap"><canvas class="mjcanvas" width="620" height="520"></canvas><div class="mjside">
        <p class="lore">A low table of black lacquer, and an old tilewright setting out ivory tiles in a stack. "Pairs," she says. "Only the free ones - nothing on top, and a side open."</p>
        <div class="mjinfo">${T ? `<b>${MJ.NAMES[T.layout]}</b><div>Tiles left <b class="mjleft">${T.live().length}</b> - open pairs <b class="mjopen">${T.pairsOpen().length}</b> - shuffles <b class="mjsh">${T.shuffles}</b></div>` : `<div>Choose a table: ${Object.keys(MJ.LAYOUTS).map((k) => `<button data-mjl="${k}" class="${this.mjLayout === k ? "primary" : ""}">${MJ.NAMES[k]}</button>`).join(" ")}</div>`}</div>
        <table class="paytable">${pays}<tr><td colspan="2" class="small">A table left or stuck pays back a little by how much of it was cleared. Every table can be cleared.</td></tr></table>
        ${live ? "" : this.cgBetRow("The stake")}<div class="cgnote">${this.cgNote || ""}</div>${last && last.card ? this.cgCardWon(last.card) : ""}
        <div class="row">${live ? `<button data-mjhint>A hint</button><button data-mjshuf ${T && T.shuffles ? "" : "disabled"}>Shuffle (${T ? T.shuffles : 0})</button><button data-mjleave title="Leave the table as it is: a little back for what was cleared">Give up the table</button>` : `<button class="primary" data-mjstart>Lay out the tiles</button>`}<button data-leave>Leave</button></div>
        <div class="small">Any potion matches any potion and any season any season; every other tile its twin.</div>${this.cgStats("mahjong")}</div></div></div>`;
      this.cgWireBet(box); const q = (s) => box.querySelector(s); q("[data-leave]").addEventListener("click", () => this.closeDialogs());
      box.querySelectorAll("[data-mjl]").forEach((b) => b.addEventListener("click", () => { this.mjLayout = b.dataset.mjl; this.cgSfx("card", 0.3); this.renderCasino(); }));
      if (q("[data-mjstart]")) q("[data-mjstart]").addEventListener("click", () => { const r = g.mjStart(bet, this.mjLayout); this.cgNote = r.error || "Find the pairs."; this.mjSel = null; this.mjFx = []; this.cgSfx(r.error ? "miss" : "chain", 0.45); this.renderCasino(); });
      if (q("[data-mjhint]")) q("[data-mjhint]").addEventListener("click", () => { const Tb = g.mjTable(), ps = Tb && Tb.pairsOpen(); this.mjHint = ps && ps.length ? [ps[0][0].i, ps[0][1].i] : null; this.mjHintAt = performance.now(); this.cgSfx("card", 0.3, 1.4); if (!this.mjHint) { this.cgNote = "No pair is open: shuffle."; this.renderCasino(); } });
      if (q("[data-mjshuf]")) q("[data-mjshuf]").addEventListener("click", () => { if (g.mjShuffle()) { this.mjSel = null; this.mjShufAt = performance.now(); this.cgNote = "The tiles left are turned and laid again."; this.cgSfx("chain", 0.5); this.renderCasino(); } });
      if (q("[data-mjleave]")) q("[data-mjleave]").addEventListener("click", () => { if (!this.mjAsk || performance.now() - this.mjAsk > 4000) { this.mjAsk = performance.now(); this.cgNote = "Give up this table? Click again: a little back for what was cleared."; this.renderCasino(); return; } this.mjAsk = 0; this.mjEnd(); });
      const cv = q(".mjcanvas"); this.mjCanvas = cv;
      cv.addEventListener("click", (e) => { const r = cv.getBoundingClientRect(), Tb = g.mjTable(), k = Tb ? this.mjK(Tb) : 1; this.mjClick(310 + ((e.clientX - r.left) * (620 / r.width) - 310) / k, 260 + ((e.clientY - r.top) * (520 / r.height) - 260) / k); });
      if (!this.mjLoop) { const loop = (now) => { if (!this.mjCanvas || !this.mjCanvas.isConnected || this.cgView !== "mahjong") { this.mjLoop = null; return; } this.mjFrame(now); this.mjLoop = requestAnimationFrame(loop); }; this.mjLoop = requestAnimationFrame(loop); }
    },
    mjEnd() { const r = this.game.mjSettle(); if (!r) return; this.cgNote = r.won ? `Cleared${r.clean ? " without a shuffle" : ` with ${r.used} shuffle${r.used > 1 ? "s" : ""}`}: ${r.pay} gold.` : `${r.removed} of 144 cleared: ${r.pay} gold back.`; if (r.won) { this.cgSfx("victory", 0.6); if (r.card) this.cgSfx("cardwin", 0.5); } else this.cgSfx("cardlose", 0.4); this.renderCasino(); if (r.won) this.cgCoins(this.$("#casino-body"), 18); },
    // where a tile is drawn: centred, each layer up and to the left
    mjPos(T, t) { const A = CM.MJ_ART, L = MJ_bounds(T); return [310 - ((L[1] - L[0]) / 2 + 2) * (A.TW / 2) + (t.x - L[0]) * (A.TW / 2) - t.z * A.DX + L[4] * A.DX / 2, 270 - ((L[3] - L[2]) / 2 + 2) * (A.TH / 2) + (t.y - L[2]) * (A.TH / 2) - t.z * A.DY + L[4] * A.DY / 2]; },
    // the stack scaled to fit the table, about its middle
    mjK(T) { const A = CM.MJ_ART, L = MJ_bounds(T); return Math.min(1, 590 / ((L[1] - L[0] + 2) * (A.TW / 2) + L[4] * A.DX + 8), 490 / ((L[3] - L[2] + 2) * (A.TH / 2) + L[4] * A.DY + 8)); },
    mjOrder(T) { return T.tiles.slice().sort((a, b) => a.z - b.z || a.y - b.y || b.x - a.x); },
    mjClick(px, py) {
      const g = this.game, T = g.mjTable(); if (!T || T.stage !== "play") return; const A = CM.MJ_ART;
      const hit = this.mjOrder(T).reverse().find((t) => { if (t.gone) return false; const [x, y] = this.mjPos(T, t); return px >= x && px < x + A.TW && py >= y && py < y + A.TH; }); if (!hit) { this.mjSel = null; return; }
      if (!T.isFree(hit)) { this.mjShake = { i: hit.i, at: performance.now() }; this.cgSfx("step", 0.3, 1.6); return; }
      const sel = this.mjSel !== null && this.mjSel !== undefined ? T.tiles[this.mjSel] : null;
      if (!sel || sel === hit) { this.mjSel = sel === hit ? null : hit.i; this.cgSfx("card", 0.35, 1.2); return; }
      if (T.match(sel, hit)) {
        const pa = this.mjPos(T, sel), pb = this.mjPos(T, hit); g.mjTake(sel.i, hit.i); this.mjSel = null; this.mjHint = null;
        (this.mjFx = this.mjFx || []).push({ a: sel, b: hit, pa, pb, at: performance.now() }); this.cgSfx("cardplace", 0.5, 1.1); this.cgSfx("coin", 0.3, 1.3 + Math.random() * 0.3);
        if (T.stage === "won") setTimeout(() => this.mjEnd(), 700);
        else if (T.stuck()) { this.cgNote = T.shuffles ? "No pair is open: shuffle the tiles left." : "No pair is open, and no shuffle left."; this.renderCasino(); if (!T.shuffles) setTimeout(() => this.mjEnd(), 900); }
        else this.mjRefreshInfo(T);
      } else { this.mjSel = hit.i; this.cgSfx("miss", 0.25); }
    },
    mjRefreshInfo(T) { const b = this.mjCanvas && this.mjCanvas.parentElement; if (!b) return; const q = (s) => b.querySelector(s); if (q(".mjleft")) q(".mjleft").textContent = T.live().length; if (q(".mjopen")) q(".mjopen").textContent = T.pairsOpen().length; },
    mjFrame(now) {
      const g = this.game, T = g.mjTable(), cv = this.mjCanvas, p = cv.getContext("2d"), A = CM.MJ_ART;
      const bg = p.createRadialGradient(310, 240, 60, 310, 260, 420); bg.addColorStop(0, "#2A1A12"); bg.addColorStop(1, "#0C0806"); p.fillStyle = bg; p.fillRect(0, 0, 620, 520);
      if (!T) { p.fillStyle = "rgba(255,240,200,0.85)"; p.font = "bold 28px Georgia, serif"; p.textAlign = "center"; const S = g.mjState(); p.fillText(S && S.stage === "done" ? (S.last && S.last.won ? "The table is cleared!" : "The table is put away") : "The Tilewright's Table", 310, 250); p.textAlign = "left"; return; }
      const k0 = this.mjK(T); p.save(); p.translate(310, 260); p.scale(k0, k0); p.translate(-310, -260);
      const order = this.mjOrder(T), live = T.live(), hint = this.mjHint && now - this.mjHintAt < 2500 ? this.mjHint : null, fresh = this.mjShufAt && now - this.mjShufAt < 500;
      for (const t of order) {
        if (t.gone) continue; let [x, y] = this.mjPos(T, t); if (this.mjShake && this.mjShake.i === t.i && now - this.mjShake.at < 260) x += Math.sin((now - this.mjShake.at) / 20) * 3;
        const sel = this.mjSel === t.i, lit = hint && hint.includes(t.i), free = T.isFree(t, live); if (sel) y -= 4;
        p.fillStyle = "#6A5A40"; p.fillRect(x + A.DX, y + A.DY, A.TW, A.TH); p.fillStyle = "#B8A880"; p.fillRect(x + 2, y + 2, A.TW, A.TH);
        p.fillStyle = free ? "#FBF6E6" : "#D8D0BC"; p.fillRect(x, y, A.TW - 2, A.TH - 2); p.strokeStyle = sel ? "#F0B020" : lit ? "#40E0A0" : "rgba(80,60,30,0.6)"; p.lineWidth = sel || lit ? 3 : 1; p.strokeRect(x + 0.5, y + 0.5, A.TW - 3, A.TH - 3);
        if (fresh) p.globalAlpha = Math.min(1, (now - this.mjShufAt) / 500); p.drawImage(this.mjFace(t.f), x + 3, y + 3); p.globalAlpha = 1;
        if (!free) { p.fillStyle = "rgba(40,30,20,0.18)"; p.fillRect(x, y, A.TW - 2, A.TH - 2); }
      }
      // a pair taken: lifted together, turning to light
      this.mjFx = (this.mjFx || []).filter((f) => now - f.at < 450); for (const f of this.mjFx) { const k = (now - f.at) / 450, mx = (f.pa[0] + f.pb[0]) / 2, my = (f.pa[1] + f.pb[1]) / 2 - 30;
        for (const [t, pp] of [[f.a, f.pa], [f.b, f.pb]]) { const x = pp[0] + (mx - pp[0]) * k, y = pp[1] + (my - pp[1]) * k - k * 20; p.globalAlpha = 1 - k; p.fillStyle = "#FFF8E0"; p.fillRect(x, y, A.TW - 2, A.TH - 2); p.drawImage(this.mjFace(t.f), x + 3, y + 3); }
        p.globalAlpha = 1 - k; p.fillStyle = "#FFE080"; for (let s = 0; s < 8; s++) { const a = s * 0.785 + k * 2; p.fillRect(mx + A.TW / 2 + Math.cos(a) * 40 * k, my + A.TH / 2 + Math.sin(a) * 40 * k, 3, 3); } p.globalAlpha = 1; }
      p.restore();
    },
    // a tile's face, painted once
    mjFace(f) {
      this.mjFaces = this.mjFaces || {}; if (this.mjFaces[f]) return this.mjFaces[f];
      const c = document.createElement("canvas"); c.width = CM.MJ_ART.TW - 8; c.height = CM.MJ_ART.TH - 8; const p = c.getContext("2d"), W = c.width, H = c.height;
      const n = Number(f.replace(/\D/g, "")) || 0, pips = (draw) => { const spots = { 1: [[0.5, 0.5]], 2: [[0.5, 0.28], [0.5, 0.72]], 3: [[0.5, 0.2], [0.5, 0.5], [0.5, 0.8]], 4: [[0.3, 0.3], [0.7, 0.3], [0.3, 0.7], [0.7, 0.7]], 5: [[0.3, 0.25], [0.7, 0.25], [0.5, 0.5], [0.3, 0.75], [0.7, 0.75]], 6: [[0.3, 0.2], [0.7, 0.2], [0.3, 0.5], [0.7, 0.5], [0.3, 0.8], [0.7, 0.8]], 7: [[0.3, 0.17], [0.7, 0.17], [0.5, 0.36], [0.3, 0.56], [0.7, 0.56], [0.3, 0.83], [0.7, 0.83]], 8: [[0.3, 0.15], [0.7, 0.15], [0.3, 0.38], [0.7, 0.38], [0.3, 0.62], [0.7, 0.62], [0.3, 0.85], [0.7, 0.85]], 9: [[0.2, 0.18], [0.5, 0.18], [0.8, 0.18], [0.2, 0.5], [0.5, 0.5], [0.8, 0.5], [0.2, 0.82], [0.5, 0.82], [0.8, 0.82]] }[n]; for (const [sx, sy] of spots) draw(sx * W, sy * H); };
      const num = (col) => { p.fillStyle = col; p.font = "bold 9px Georgia, serif"; p.fillText(String(n), 1, 9); };
      if (f.startsWith("coins")) { pips((x, y) => { const r = n > 6 ? 4.2 : 5.2; const gr = p.createRadialGradient(x - 1, y - 1, 1, x, y, r); gr.addColorStop(0, "#FFF0A0"); gr.addColorStop(1, "#B07A10"); p.fillStyle = gr; p.beginPath(); p.arc(x, y, r, 0, Math.PI * 2); p.fill(); p.fillStyle = "#7A5208"; p.fillRect(x - 1, y - 1, 2, 2); }); num("#8A6010"); }
      else if (f.startsWith("runes")) { pips((x, y) => { p.strokeStyle = "#2A50B0"; p.lineWidth = 1.6; p.beginPath(); p.moveTo(x - 2, y - 4); p.lineTo(x - 2, y + 4); p.moveTo(x - 2, y - 4); p.lineTo(x + 3, y - 1); p.lineTo(x - 2, y + 1); p.stroke(); }); num("#2A50B0"); }
      else if (f.startsWith("blades")) { pips((x, y) => { p.strokeStyle = "#5A6A7A"; p.lineWidth = 2; p.beginPath(); p.moveTo(x, y - 5); p.lineTo(x, y + 3); p.stroke(); p.strokeStyle = "#8A5A20"; p.beginPath(); p.moveTo(x - 3, y + 2); p.lineTo(x + 3, y + 2); p.moveTo(x, y + 2); p.lineTo(x, y + 6); p.stroke(); }); num("#3A4A5A"); }
      else if (f.startsWith("wind")) { const w = f.slice(4); p.strokeStyle = "rgba(60,40,20,0.35)"; p.beginPath(); p.arc(W / 2, H / 2, 14, 0, Math.PI * 2); p.stroke(); p.fillStyle = "#2A1A10"; p.font = "bold 24px Georgia, serif"; p.textAlign = "center"; p.fillText(w, W / 2, H / 2 + 8); p.textAlign = "left"; }
      else if (f === "fire") { p.fillStyle = "#D03010"; p.beginPath(); p.moveTo(W / 2, 6); p.quadraticCurveTo(W - 6, H / 2, W / 2, H - 6); p.quadraticCurveTo(6, H / 2, W / 2, 6); p.fill(); p.fillStyle = "#FFB030"; p.beginPath(); p.moveTo(W / 2, H / 2 - 4); p.quadraticCurveTo(W / 2 + 7, H / 2 + 8, W / 2, H - 9); p.quadraticCurveTo(W / 2 - 7, H / 2 + 8, W / 2, H / 2 - 4); p.fill(); }
      else if (f === "frost" || f === "season_winter") { p.strokeStyle = f === "frost" ? "#2A70D0" : "#6AA0E0"; p.lineWidth = 2; for (let k = 0; k < 3; k++) { const a = (k * Math.PI) / 3; p.beginPath(); p.moveTo(W / 2 - Math.cos(a) * 13, H / 2 - Math.sin(a) * 13); p.lineTo(W / 2 + Math.cos(a) * 13, H / 2 + Math.sin(a) * 13); p.stroke(); } }
      else if (f === "holy" || f === "season_summer") { p.fillStyle = f === "holy" ? "#E0A820" : "#F09020"; p.beginPath(); p.arc(W / 2, H / 2, 8, 0, Math.PI * 2); p.fill(); p.strokeStyle = p.fillStyle; p.lineWidth = 2; for (let k = 0; k < 8; k++) { const a = (k * Math.PI) / 4; p.beginPath(); p.moveTo(W / 2 + Math.cos(a) * 11, H / 2 + Math.sin(a) * 11); p.lineTo(W / 2 + Math.cos(a) * 15, H / 2 + Math.sin(a) * 15); p.stroke(); } }
      else if (f.startsWith("potion_")) { const col = { heal: "#D02838", mana: "#2850D0", luck: "#20A050", haste: "#E0B020" }[f.slice(7)]; p.fillStyle = "rgba(200,220,230,0.8)"; p.fillRect(W / 2 - 3, 8, 6, 8); p.fillStyle = "#8A5A20"; p.fillRect(W / 2 - 3, 5, 6, 4); p.fillStyle = col; p.beginPath(); p.arc(W / 2, H / 2 + 6, 11, 0, Math.PI * 2); p.fill(); p.fillStyle = "rgba(255,255,255,0.5)"; p.fillRect(W / 2 - 6, H / 2 + 1, 3, 5); }
      else if (f === "season_spring") { p.fillStyle = "#F0A0C0"; for (let k = 0; k < 5; k++) { const a = (k * 2 * Math.PI) / 5; p.beginPath(); p.arc(W / 2 + Math.cos(a) * 7, H / 2 + Math.sin(a) * 7, 5.5, 0, Math.PI * 2); p.fill(); } p.fillStyle = "#F0D040"; p.beginPath(); p.arc(W / 2, H / 2, 3.5, 0, Math.PI * 2); p.fill(); }
      else if (f === "season_autumn") { p.fillStyle = "#D06818"; p.beginPath(); p.moveTo(W / 2, 8); p.quadraticCurveTo(W - 4, H / 2, W / 2, H - 10); p.quadraticCurveTo(4, H / 2, W / 2, 8); p.fill(); p.strokeStyle = "#7A3A08"; p.beginPath(); p.moveTo(W / 2, 10); p.lineTo(W / 2, H - 4); p.stroke(); }
      if (f.startsWith("season_")) { p.fillStyle = "#6A4A20"; p.font = "8px Georgia, serif"; p.fillText(f.slice(7, 8).toUpperCase(), 2, 9); }
      this.mjFaces[f] = c; return c;
    },
  });
}
