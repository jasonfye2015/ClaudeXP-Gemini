"use strict";
// The Patience Table, the window's side: a green baize table under a lamp, the cards drawn with the house's own face -
// rounded ivory with the rank and suit in the corners, pips or a crowned court figure in the middle, backs in claret
// with a gold Joker's diamond - sliding to wherever they go; empty places outlined (an A on a foundation, a K on an
// empty Klondike column). Drag a card (or a run) to move it, or click it and then click where it goes; double-click to
// send it home; click the stock to turn a card. When the last card goes up, the cards bounce away down the table in the
// old way. The rules are 64zzb-patience.js.
CM.CG_TABLES.push(["patience", "The Patience Table"]);
{ const floor0 = CM.UI.prototype.renderFloor, CW = 70, CH = 98, GAP = 14, W = 760, H = 560, TOPY = 16, TABY = 136, SUIT = ["♠", "♥", "♦", "♣"], RANK = ["", "A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"];
  const id = (c) => c.s * 13 + c.r;
  Object.assign(CM.UI.prototype, {
    renderFloor(box) { if (this.cgView === "patience") return this.cgPatience(box); return floor0.call(this, box); },
    cgPatience(box) {
      const g = this.game, P = g.ptStore(), D = g.ptDeal(), total = P.wins.klondike + P.wins.freecell, next = CM.PAT.MARKS.find(([n]) => n > total);
      box.innerHTML = `<div class="cgtable patience"><h3>The Patience Table</h3><p class="lore">A quiet table in the corner, green baize under a lamp, and two packs laid ready. "Patience is free," says the attendant, "and the house rewards it."</p>
        <canvas class="ptcanvas" width="${W}" height="${H}"></canvas>
        <div class="cgnote">${this.cgNote || ""}</div>${this.ptCard ? this.cgCardWon(this.ptCard) : ""}
        <div class="row"><button class="${!D || D.mode === "klondike" ? "primary" : ""}" data-ptnew="klondike">New Klondike</button><button class="${D && D.mode === "freecell" ? "primary" : ""}" data-ptnew="freecell">New FreeCell</button>${D && !D.done ? `<button data-ptundo ${D.hist.length ? "" : "disabled"}>Take back</button><button data-ptauto>Put up what's safe</button>` : ""}<button data-leave>Leave</button></div>
        <div class="small">Drag a card or a run to move it, or click it then click where it goes; double-click sends a card home; click the stock to turn a card (and again to turn the pile over). Build columns down in alternating colours, foundations up by suit from the ace. A Klondike win pays ${CM.PAT.gold.klondike} gold and ${CM.PAT.tickets.klondike} tickets, FreeCell ${CM.PAT.gold.freecell} gold and ${CM.PAT.tickets.freecell}; cards at the 1st, 5th, 15th and 40th win${next ? ` (next at ${next[0]})` : ""}. Won: Klondike ${P.wins.klondike} of ${P.played.klondike}, FreeCell ${P.wins.freecell} of ${P.played.freecell}.</div></div>`;
      const q = (s) => box.querySelector(s); q("[data-leave]").addEventListener("click", () => this.closeDialogs());
      box.querySelectorAll("[data-ptnew]").forEach((b) => b.addEventListener("click", () => { const Dd = g.ptDeal(); if (Dd && !Dd.done && Dd.moves > 0 && !(this.ptAsk && performance.now() - this.ptAsk < 4000)) { this.ptAsk = performance.now(); this.cgNote = "Leave this deal unfinished? Click again to deal a new one."; this.renderCasino(); return; } this.ptAsk = 0; g.ptNew(b.dataset.ptnew); this.ptPos = {}; this.ptSel = null; this.ptCard = null; this.ptWinFx = null; this.cgNote = ""; this.cgSfx("chain", 0.4); this.renderCasino(); }));
      if (q("[data-ptundo]")) q("[data-ptundo]").addEventListener("click", () => { if (g.ptDeal().undo()) { g.ptKeep(); this.cgSfx("card", 0.3, 0.8); this.renderCasino(); } });
      if (q("[data-ptauto]")) q("[data-ptauto]").addEventListener("click", () => { const Dd = g.ptDeal(); Dd.push(); const n = Dd.canFinish() ? this.ptFinish(Dd) : Dd.autoUp(); if (!n) Dd.hist.pop(); this.ptAfter(n ? "up" : null); });
      const cv = this.ptCanvas = q(".ptcanvas"), pos = (e) => { const r = cv.getBoundingClientRect(); return [((e.clientX - r.left) / r.width) * W, ((e.clientY - r.top) / r.height) * H]; };
      cv.addEventListener("mousedown", (e) => { const Dd = g.ptDeal(); if (!Dd || Dd.done) return; const [x, y] = pos(e), hit = this.ptHit(Dd, x, y); if (!hit) { this.ptSel = null; return; }
        if (hit.pile === "stock") { Dd.draw(); this.ptAfter("draw"); return; } const cards = hit.pile === "empty" ? [] : Dd.lift(hit); if (cards.length) this.ptDrag = { from: hit, cards, x0: x, y0: y, x, y, moved: false }; else if (this.ptSel && hit.pile !== "stock") this.ptTry(Dd, this.ptSel, hit.pile === "empty" ? hit.to : hit); });
      cv.addEventListener("mousemove", (e) => { if (!this.ptDrag) return; const [x, y] = pos(e); this.ptDrag.x = x; this.ptDrag.y = y; if (Math.hypot(x - this.ptDrag.x0, y - this.ptDrag.y0) > 6) this.ptDrag.moved = true; });
      cv.addEventListener("mouseup", (e) => { const Dd = g.ptDeal(), Dg = this.ptDrag; this.ptDrag = null; if (!Dd || !Dg) return; const [x, y] = pos(e);
        if (Dg.moved) { const to = this.ptDrop(Dd, x - (Dg.x0 - this.ptCardXY(Dd, Dg.from)[0]) + CW / 2, y); if (!to || !Dd.move(Dg.from, to)) this.cgSfx("miss", 0.2); else this.ptAfter("move"); return; }
        if (this.ptSel && !(this.ptSel.pile === Dg.from.pile && this.ptSel.i === Dg.from.i)) { const t = { pile: Dg.from.pile === "tab" ? "tab" : Dg.from.pile, i: Dg.from.i }; if (Dd.move(this.ptSel, t)) { this.ptSel = null; this.ptAfter("move"); return; } }
        this.ptSel = Dg.from; this.cgSfx("card", 0.2, 1.4); });
      cv.addEventListener("dblclick", (e) => { const Dd = g.ptDeal(); if (!Dd || Dd.done) return; const [x, y] = pos(e), hit = this.ptHit(Dd, x, y); if (hit && hit.pile !== "stock" && hit.pile !== "empty") { if (hit.pile === "tab") hit.k = Dd.tab[hit.i].length - 1; if (Dd.sendHome(hit)) { this.ptSel = null; this.ptAfter("move"); } } });
      if (!this.ptLoop) { let prev = performance.now(); const loop = (now) => { if (!this.ptCanvas || !this.ptCanvas.isConnected || this.cgView !== "patience") { this.ptLoop = null; return; } const dt = Math.min(0.05, (now - prev) / 1000); prev = now; this.ptFrame(dt, now); this.ptLoop = requestAnimationFrame(loop); }; this.ptLoop = requestAnimationFrame(loop); }
    },
    ptTry(Dd, from, to) { if (Dd.move(from, to)) { this.ptSel = null; this.ptAfter("move"); } else { this.cgSfx("miss", 0.2); this.ptSel = null; } },
    ptFinish(Dd) { let n = 0, moved = true; while (moved) { moved = false; for (let i = 0; i < Dd.tab.length && !moved; i++) { const col = Dd.tab[i]; if (!col.length) continue; for (let f = 0; f < 4; f++) if (Dd.move({ pile: "tab", i, k: col.length - 1 }, { pile: "found", i: f })) { Dd.hist.pop(); n++; moved = true; break; } } } return n; },
    ptAfter(kind) {
      const g = this.game, Dd = g.ptDeal(); if (kind === "move" || kind === "up") { const n = Dd.autoUp(); this.cgSfx("cardplace", 0.35, 1 + Math.random() * 0.3); if (n) setTimeout(() => this.cgSfx("card", 0.3, 1.5), 120); } else if (kind === "draw") this.cgSfx("card", 0.3, 1.2);
      g.ptKeep(); if (Dd.won()) { const r = g.ptWin(); if (r) { this.cgNote = `Won in ${r.moves} moves: ${r.gold} gold and ${r.tickets} tickets${r.card ? `, and a card - ${r.card}` : ""}!`; this.ptCard = r.card; this.ptWinFx = { at: performance.now(), cards: [] }; this.cgSfx("victory", 0.6); if (r.card) setTimeout(() => this.cgSfx("cardwin", 0.5), 400); } }
      else if (Dd.canFinish() && !this.ptOffered) { this.ptOffered = true; this.cgNote = "Every card is showing - \"Put up what's safe\" will play the rest off."; }
      this.renderCasino();
    },
    // where things sit on the table
    ptSlots(Dd) { const kl = Dd.mode === "klondike", cols = Dd.tab.length, tw = cols * (CW + GAP) - GAP, x0 = (W - tw) / 2, slot = { tab: [], found: [], cell: [] };
      for (let i = 0; i < cols; i++) slot.tab.push([x0 + i * (CW + GAP), TABY]);
      if (kl) { slot.stock = [x0, TOPY]; slot.waste = [x0 + CW + GAP, TOPY]; for (let i = 0; i < 4; i++) slot.found.push([x0 + (3 + i) * (CW + GAP), TOPY]); }
      else { for (let i = 0; i < 4; i++) slot.cell.push([x0 + i * (CW + GAP), TOPY]); for (let i = 0; i < 4; i++) slot.found.push([x0 + (4 + i) * (CW + GAP), TOPY]); }
      return slot; },
    ptFan(col) { const n = col.length, room = H - TABY - CH - 10; let dn = 10, up = 26; const need = col.reduce((t, c, i) => (i === n - 1 ? t : t + (c.up ? up : dn)), 0); if (need > room) { const k = room / need; dn *= k; up *= k; } return [dn, up]; },
    ptCardXY(Dd, from) { const S = this.ptSlots(Dd); if (from.pile === "tab") { const col = Dd.tab[from.i], [dn, up] = this.ptFan(col); let y = S.tab[from.i][1]; for (let k = 0; k < from.k; k++) y += col[k].up ? up : dn; return [S.tab[from.i][0], y]; } return from.pile === "waste" ? S.waste : from.pile === "cell" ? S.cell[from.i] : S.found[from.i]; },
    ptHit(Dd, x, y) { const S = this.ptSlots(Dd), inn = ([sx, sy], h = CH) => x >= sx && x < sx + CW && y >= sy && y < sy + h;
      if (S.stock && inn(S.stock)) return { pile: "stock" }; if (S.waste && inn(S.waste) && Dd.waste.length) return { pile: "waste" };
      for (let i = 0; i < 4; i++) { if (S.cell[i] && inn(S.cell[i])) return Dd.cells[i] ? { pile: "cell", i } : { pile: "empty", to: { pile: "cell", i } }; if (inn(S.found[i])) return Dd.found[i].length ? { pile: "found", i } : { pile: "empty", to: { pile: "found", i } }; }
      for (let i = 0; i < Dd.tab.length; i++) { const col = Dd.tab[i]; if (!col.length) { if (inn(S.tab[i])) return { pile: "empty", to: { pile: "tab", i } }; continue; } for (let k = col.length - 1; k >= 0; k--) { const [cx, cy] = this.ptCardXY(Dd, { pile: "tab", i, k }); if (x >= cx && x < cx + CW && y >= cy && y < cy + CH) return { pile: "tab", i, k }; } }
      return null; },
    // where a dragged card is let go: the nearest place it may go
    ptDrop(Dd, x, y) { const S = this.ptSlots(Dd), cand = []; S.tab.forEach(([sx], i) => cand.push([{ pile: "tab", i }, Math.abs(sx + CW / 2 - x) + (y < TABY - 20 ? 200 : 0)])); S.found.forEach(([sx, sy], i) => cand.push([{ pile: "found", i }, Math.abs(sx + CW / 2 - x) + Math.abs(sy + CH / 2 - y)])); S.cell.forEach(([sx, sy], i) => cand.push([{ pile: "cell", i }, Math.abs(sx + CW / 2 - x) + Math.abs(sy + CH / 2 - y)]));
      cand.sort((a, b) => a[1] - b[1]); return cand[0][1] < CW * 1.2 ? cand[0][0] : null; },
    ptFrame(dt, now) {
      const g = this.game, Dd = g.ptDeal(), p = this.ptCanvas.getContext("2d"), baize = p.createRadialGradient(W / 2, H * 0.4, 40, W / 2, H / 2, W * 0.7); baize.addColorStop(0, "#2A7A4A"); baize.addColorStop(1, "#0E3A20"); p.fillStyle = baize; p.fillRect(0, 0, W, H);
      p.fillStyle = "rgba(255,255,255,0.025)"; for (let k = 0; k < 400; k++) p.fillRect((k * 97) % W, (k * 61) % H, 1, 1);
      if (!Dd) { p.fillStyle = "rgba(255,240,200,0.85)"; p.font = "bold 26px Georgia"; p.textAlign = "center"; p.fillText("Deal a game of Klondike or FreeCell", W / 2, H / 2); p.textAlign = "left"; return; }
      const S = this.ptSlots(Dd), outline = ([x, y], t) => { p.strokeStyle = "rgba(255,255,255,0.25)"; p.lineWidth = 2; p.beginPath(); p.roundRect ? p.roundRect(x, y, CW, CH, 7) : p.rect(x, y, CW, CH); p.stroke(); p.lineWidth = 1; if (t) { p.fillStyle = "rgba(255,255,255,0.22)"; p.font = "bold 26px Georgia"; p.textAlign = "center"; p.fillText(t, x + CW / 2, y + CH / 2 + 9); p.textAlign = "left"; } };
      if (S.stock) { outline(S.stock, "↻"); outline(S.waste); } S.found.forEach((s, i) => outline(s, Dd.found[i].length ? "" : "A")); S.cell.forEach((s) => outline(s)); S.tab.forEach((s) => outline(s, Dd.mode === "klondike" ? "K" : ""));
      // every card's target, eased toward
      const tgt = []; const dragIds = new Set(this.ptDrag && this.ptDrag.moved ? this.ptDrag.cards.map(id) : []), selIds = new Set(this.ptSel ? Dd.lift(this.ptSel).map(id) : []);
      if (S.stock) Dd.stock.forEach((c, k) => tgt.push([c, S.stock[0] - Math.min(k, 6) * 0.6, S.stock[1] - Math.min(k, 6) * 0.6])); if (S.waste) Dd.waste.forEach((c, k) => tgt.push([c, S.waste[0] + Math.max(0, k - Dd.waste.length + 3) * 14, S.waste[1]]));
      Dd.found.forEach((f, i) => f.forEach((c) => tgt.push([c, ...S.found[i]]))); (Dd.cells || []).forEach((c, i) => c && tgt.push([c, ...S.cell[i]]));
      Dd.tab.forEach((col, i) => col.forEach((c, k) => tgt.push([c, ...this.ptCardXY(Dd, { pile: "tab", i, k })])));
      const P = this.ptPos = this.ptPos || {}, win = this.ptWinFx;
      if (win) { // the old way: one by one off the foundations, bouncing down the table
        const t = (now - win.at) / 1000; if (win.cards.length < 52 && t > win.cards.length * 0.12) { const f = win.cards.length % 4, top = Dd.found[f][12 - Math.floor(win.cards.length / 4)]; if (top) win.cards.push({ c: top, x: S.found[f][0], y: S.found[f][1], vx: (Math.random() < 0.5 ? -1 : 1) * (120 + Math.random() * 160), vy: -Math.random() * 200 }); }
        for (const w of win.cards) { w.vy += 900 * dt; w.x += w.vx * dt; w.y += w.vy * dt; if (w.y > H - CH) { w.y = H - CH; w.vy = -w.vy * 0.75; } (win.trail = win.trail || []).push([w.c, w.x, w.y]); }
        if (!win.bg) { win.bg = document.createElement("canvas"); win.bg.width = W; win.bg.height = H; } const bp = win.bg.getContext("2d"); for (const [c, x, y] of win.trail || []) this.ptCardDraw(bp, c, x, y, false); win.trail = []; p.drawImage(win.bg, 0, 0);
        const gone = new Set(win.cards.map((w) => id(w.c))); for (const [c, x, y] of tgt) if (c.up && !gone.has(id(c))) this.ptCardDraw(p, c, x, y, false); return; }
      for (const [c, x, y] of tgt) { const k = id(c), cur = P[k] || (P[k] = { x, y }); cur.x += (x - cur.x) * Math.min(1, dt * 14); cur.y += (y - cur.y) * Math.min(1, dt * 14); if (Math.abs(x - cur.x) + Math.abs(y - cur.y) < 0.5) { cur.x = x; cur.y = y; } }
      const moving = tgt.filter(([c]) => { const cur = P[id(c)]; return Math.abs(cur.x - tgt.find(([d]) => d === c)[1]) > 1 || dragIds.has(id(c)); });
      for (const [c] of tgt) { if (dragIds.has(id(c)) || moving.some(([d]) => d === c)) continue; this.ptCardDraw(p, c, P[id(c)].x, P[id(c)].y - (selIds.has(id(c)) ? 4 : 0), selIds.has(id(c))); }
      for (const [c] of moving) { if (dragIds.has(id(c))) continue; this.ptCardDraw(p, c, P[id(c)].x, P[id(c)].y, false, true); }
      if (this.ptDrag && this.ptDrag.moved) { const Dg = this.ptDrag, [bx, by] = this.ptCardXY(Dd, Dg.from), dx = Dg.x - Dg.x0, dy = Dg.y - Dg.y0; Dg.cards.forEach((c, k) => this.ptCardDraw(p, c, bx + dx, by + dy + k * 26, true, true)); }
      p.fillStyle = "rgba(0,0,0,0.35)"; p.fillRect(W - 150, H - 26, 146, 20); p.fillStyle = "#F0E0B0"; p.font = "12px monospace"; p.fillText(`${Dd.mode === "klondike" ? "KLONDIKE" : "FREECELL"}  MOVES ${Dd.moves}`, W - 144, H - 12);
    },
    ptCardDraw(p, c, x, y, lit, lifted) {
      const rr = (r) => { p.beginPath(); p.roundRect ? p.roundRect(x, y, CW, CH, r) : p.rect(x, y, CW, CH); };
      p.fillStyle = `rgba(0,0,0,${lifted ? 0.4 : 0.25})`; p.beginPath(); p.roundRect ? p.roundRect(x + (lifted ? 6 : 2), y + (lifted ? 8 : 3), CW, CH, 7) : p.rect(x + 2, y + 3, CW, CH); p.fill();
      if (!c.up) { const bg = p.createLinearGradient(x, y, x + CW, y + CH); const cb = CM.cosBack ? CM.cosBack() : ["#7A1A2A", "#4A0A18"]; bg.addColorStop(0, cb[0]); bg.addColorStop(1, cb[1]); p.fillStyle = bg; rr(7); p.fill(); p.strokeStyle = "#E0B860"; p.lineWidth = 1.5; p.beginPath(); p.roundRect ? p.roundRect(x + 5, y + 5, CW - 10, CH - 10, 4) : p.rect(x + 5, y + 5, CW - 10, CH - 10); p.stroke(); p.lineWidth = 1; p.fillStyle = "#E0B860"; p.beginPath(); p.moveTo(x + CW / 2, y + CH / 2 - 14); p.lineTo(x + CW / 2 + 10, y + CH / 2); p.lineTo(x + CW / 2, y + CH / 2 + 14); p.lineTo(x + CW / 2 - 10, y + CH / 2); p.fill(); return; }
      p.fillStyle = "#FBF6E8"; rr(7); p.fill(); p.strokeStyle = lit ? "#F0B020" : "rgba(60,40,20,0.4)"; p.lineWidth = lit ? 3 : 1; rr(7); p.stroke(); p.lineWidth = 1;
      const col = c.s === 1 || c.s === 2 ? "#C02030" : "#1A1A22", sy = SUIT[c.s], rk = RANK[c.r]; p.fillStyle = col; p.font = "bold 15px Georgia"; p.fillText(rk, x + 5, y + 17); p.font = "13px Georgia"; p.fillText(sy, x + 5, y + 31);
      p.save(); p.translate(x + CW - 5, y + CH - 5); p.rotate(Math.PI); p.font = "bold 15px Georgia"; p.fillText(rk, 0, 12); p.restore();
      if (c.r > 10) { p.fillStyle = col === "#C02030" ? "rgba(192,32,48,0.12)" : "rgba(30,30,40,0.1)"; p.fillRect(x + 16, y + 20, CW - 32, CH - 40); p.strokeStyle = "#C8962A"; p.strokeRect(x + 16, y + 20, CW - 32, CH - 40); p.fillStyle = "#C8962A"; p.beginPath(); p.moveTo(x + CW / 2 - 10, y + 40); p.lineTo(x + CW / 2 - 10, y + 30); p.lineTo(x + CW / 2 - 5, y + 36); p.lineTo(x + CW / 2, y + 28); p.lineTo(x + CW / 2 + 5, y + 36); p.lineTo(x + CW / 2 + 10, y + 30); p.lineTo(x + CW / 2 + 10, y + 40); p.fill(); p.fillStyle = col; p.font = "bold 22px Georgia"; p.textAlign = "center"; p.fillText(rk, x + CW / 2, y + 66); p.textAlign = "left"; }
      else { p.font = `${c.r === 1 ? 34 : 18}px Georgia`; p.textAlign = "center"; if (c.r === 1) p.fillText(sy, x + CW / 2, y + CH / 2 + 12); else { const rows = Math.ceil(c.r / 2); for (let i = 0; i < c.r; i++) { const colx = c.r <= 3 ? 0.5 : i % 2 ? 0.68 : 0.32, row = c.r <= 3 ? i : Math.floor(i / 2), ry = c.r <= 3 ? c.r : rows; p.fillText(sy, x + CW * colx, y + 30 + (row + 0.5) * ((CH - 44) / ry)); } } p.textAlign = "left"; }
    },
  });
}
