"use strict";
// The Vault Runes, the window's side: a round vault door of dark iron set in the stone, its face a grid of rune-plates;
// a lit rune glows gold with a soft pulse and its sigil burns, a dark one is cold slate; touching a plate turns it and
// its neighbours with a little rotating flip and a chime that rises with the lit count; the bolts round the rim draw
// back one by one as the runes light, and when all are lit the great wheel spins and the door swings open on a heap of
// gold. Free to play: each vault opened pays tickets, the first time gold, and every third vault a card. The rules are
// 64zzf-arc2.js.
CM.CG_TABLES.push(["vault", "The Vault Runes"]);
{ const floor0 = CM.UI.prototype.renderFloor, VR = CM.VR, S = 340, GLYPH = ["ᚠ", "ᚢ", "ᚦ", "ᚨ", "ᚱ", "ᚲ", "ᚷ", "ᚹ", "ᚺ", "ᚾ", "ᛁ", "ᛃ", "ᛇ", "ᛈ", "ᛉ", "ᛊ", "ᛏ", "ᛒ", "ᛖ", "ᛗ", "ᛚ", "ᛜ", "ᛞ", "ᛟ"];
  Object.assign(CM.UI.prototype, {
    renderFloor(box) { if (this.cgView === "vault") return this.cgVault(box); return floor0.call(this, box); },
    cgVault(box) {
      const g = this.game, St = g.vrStore(), top = Object.keys(St.done).length + 1, L = g.vrLive, n = L ? L.n : Math.min(top, this.vrN || top);
      const btns = []; for (let k = Math.max(1, top - 11); k <= top; k++) btns.push(`<button data-vrn="${k}" class="${k === n ? "primary" : ""}${St.done[k] ? " done" : ""}">${k}${St.done[k] ? " ✓" : ""}${k % 3 === 0 && !St.done[k] ? " ♦" : ""}</button>`);
      box.innerHTML = `<div class="cgtable vault"><h3>The Vault Runes</h3><p class="lore">In the deepest cellar the Joker keeps a row of old dwarf vaults, each sealed with a rune-lock. \"Light every rune and the door's yours to open,\" says the vault-keeper. \"Touch one and its neighbours turn with it. That's the whole trick, and nobody gets it quick.\"</p>
        <div class="row vrlevels">${btns.join("")}</div>
        <div class="vrwrap"><canvas class="vrcanvas" width="${S}" height="${S}"></canvas></div>
        <div class="cgnote">${this.cgNote || ""}</div>${this.vrCard ? this.cgCardWon(this.vrCard) : ""}
        <div class="row"><button class="primary" data-vrgo>${L && L.open ? "The next vault" : L ? "Start this vault again" : "Try the lock"}</button><button data-leave>Leave</button></div>
        <div class="small">Touch a rune to turn it and the runes beside it${n >= 8 ? " (from vault 8, the corners too)" : ""}; light them all to open the vault. Free to try. Each vault opened gives ${VR.tickets(n)} tickets (2 more within ${L ? L.par : "the keeper's"} touches); the first time, ${VR.gold(n)} gold, and every third vault a card. Opened ${St.opened} time${St.opened === 1 ? "" : "s"}; ${Object.keys(St.done).length} vaults beaten.${St.best[n] ? ` Your best on vault ${n}: ${St.best[n]} touches.` : ""}</div></div>`;
      const q = (s) => box.querySelector(s); q("[data-leave]").addEventListener("click", () => this.closeDialogs());
      const start = (k) => { g.vrNew(k); this.vrN = k; this.vrFx = { flips: [], at: performance.now() }; this.vrCard = null; this.cgNote = `Vault ${g.vrLive.n}: light every rune.`; this.cgSfx("door", 0.35, 0.8); this.renderCasino(); };
      box.querySelectorAll("[data-vrn]").forEach((b) => b.addEventListener("click", () => start(Number(b.dataset.vrn))));
      q("[data-vrgo]").addEventListener("click", () => start(L && L.open ? Math.min(top, L.n + 1) : n));
      const cv = this.vrCanvas = q(".vrcanvas");
      cv.addEventListener("mousemove", (e) => { const r = cv.getBoundingClientRect(); this.vrMouse = [((e.clientX - r.left) / r.width) * S, ((e.clientY - r.top) / r.height) * S]; });
      cv.addEventListener("mousedown", (e) => { const Lv = g.vrLive; if (!Lv || Lv.open) return; const c = this.vrCell(Lv, ...this.vrMouse); if (!c) return; const before = Lv.on.flat().filter(Boolean).length, r = g.vrTouch(c[0], c[1]), now = performance.now(), fx = this.vrFx = this.vrFx || { flips: [] };
        for (const [a, b] of Lv.nb(c[0], c[1])) fx.flips.push({ x: a, y: b, at: now + (a === c[0] && b === c[1] ? 0 : 60) }); const lit = Lv.on.flat().filter(Boolean).length; this.cgSfx("tablebell", 0.22, 0.7 + (lit / (Lv.w * Lv.h)) * 1.1); if (lit < before) this.cgSfx("step", 0.15, 0.6);
        if (r && r.open) { fx.open = now; this.cgSfx("victory", 0.6); if (r.card) setTimeout(() => this.cgSfx("cardwin", 0.5), 600); this.vrCard = r.card; this.cgNote = `Vault ${r.n} opened in ${r.moves} touches${r.moves <= r.par ? " - as quick as the keeper" : ""}: ${r.tickets} tickets${r.gold ? `, ${r.gold} gold for the first time` : ""}${r.card ? `, and a card - ${r.card}` : ""}.`; setTimeout(() => { this.renderCasino(); if (r.gold) this.cgCoins(this.$("#casino-body"), 14); }, 1400); } });
      if (!this.vrLoop) { const loop = (now) => { if (!this.vrCanvas || !this.vrCanvas.isConnected || this.cgView !== "vault") { this.vrLoop = null; return; } this.vrFrame(now); this.vrLoop = requestAnimationFrame(loop); }; this.vrLoop = requestAnimationFrame(loop); }
    },
    vrGeom(Lv) { const cs = Math.min(52, Math.floor(200 / Math.max(Lv.w, Lv.h))); return { cs, x0: S / 2 - (Lv.w * cs) / 2, y0: S / 2 - (Lv.h * cs) / 2 }; },
    vrCell(Lv, mx, my) { const { cs, x0, y0 } = this.vrGeom(Lv), x = Math.floor((mx - x0) / cs), y = Math.floor((my - y0) / cs); return x >= 0 && y >= 0 && x < Lv.w && y < Lv.h ? [x, y] : null; },
    vrFrame(now) {
      const p = this.vrCanvas.getContext("2d"), Lv = this.game.vrLive, fx = this.vrFx || { flips: [] }, cx = S / 2, cy = S / 2, R = S / 2 - 12;
      const bg = p.createRadialGradient(cx, cy, 40, cx, cy, S * 0.75); bg.addColorStop(0, "#3A3430"); bg.addColorStop(1, "#141010"); p.fillStyle = bg; p.fillRect(0, 0, S, S);
      for (let k = 0; k < 14; k++) { p.strokeStyle = "rgba(0,0,0,0.35)"; p.strokeRect((k % 4) * 110 - 10 + (Math.floor(k / 4) % 2) * 55, Math.floor(k / 4) * 110, 110, 110); }
      const open = fx.open ? Math.min(1, (now - fx.open) / 1200) : 0, lit = Lv ? Lv.on.flat().filter(Boolean).length / (Lv.w * Lv.h) : 0;
      if (open > 0) { p.fillStyle = "#0A0806"; p.beginPath(); p.arc(cx, cy, R, 0, Math.PI * 2); p.fill(); for (let k = 0; k < 40; k++) { const a = (k * 2.4) % (Math.PI * 2), d = (k * 37) % (R * 0.7); p.fillStyle = k % 3 ? "#F0C040" : "#FFE890"; p.beginPath(); p.ellipse(cx + Math.cos(a) * d, cy + 40 + Math.sin(a) * d * 0.4, 7, 4, 0, 0, Math.PI * 2); p.fill(); } const gl = p.createRadialGradient(cx, cy + 40, 10, cx, cy + 40, R); gl.addColorStop(0, `rgba(255,220,120,${0.5 * open})`); gl.addColorStop(1, "rgba(255,220,120,0)"); p.fillStyle = gl; p.fillRect(0, 0, S, S); }
      p.save(); p.translate(cx, cy); if (open > 0) p.scale(1 - open * 0.85, 1); p.translate(-cx, -cy);
      const door = p.createRadialGradient(cx - 40, cy - 40, 20, cx, cy, R); door.addColorStop(0, "#5A5860"); door.addColorStop(1, "#24222A"); p.fillStyle = door; p.beginPath(); p.arc(cx, cy, R, 0, Math.PI * 2); p.fill(); p.strokeStyle = "#7A7680"; p.lineWidth = 6; p.stroke(); p.lineWidth = 1;
      for (let k = 0; k < 16; k++) { const a = (k / 16) * Math.PI * 2, back = lit * 16 > k ? 8 : 0; p.fillStyle = back ? "#3A3840" : "#A8A4B0"; p.beginPath(); p.arc(cx + Math.cos(a) * (R - 10 + back), cy + Math.sin(a) * (R - 10 + back), 5, 0, Math.PI * 2); p.fill(); }
      p.save(); p.translate(cx, cy); p.rotate(open * Math.PI * 2 + lit * 0.4); p.strokeStyle = "rgba(160,150,170,0.35)"; p.lineWidth = 3; p.beginPath(); p.arc(0, 0, R - 34, 0, Math.PI * 2); p.stroke(); for (let k = 0; k < 6; k++) { p.rotate(Math.PI / 3); p.beginPath(); p.moveTo(0, R - 44); p.lineTo(0, R - 24); p.stroke(); } p.lineWidth = 1; p.restore();
      if (Lv) { const { cs, x0, y0 } = this.vrGeom(Lv), hov = this.vrMouse && !Lv.open ? this.vrCell(Lv, ...this.vrMouse) : null, hn = hov ? Lv.nb(hov[0], hov[1]).map(([a, b]) => `${a},${b}`) : [];
        for (let y = 0; y < Lv.h; y++) for (let x = 0; x < Lv.w; x++) { const on = Lv.on[y][x], f = fx.flips.filter((q) => q.x === x && q.y === y).pop(), k = f ? Math.min(1, Math.max(0, (now - f.at) / 220)) : 1, X = x0 + x * cs, Y = y0 + y * cs, sq = Math.abs(Math.cos(k * Math.PI)), show = k < 0.5 ? !on : on;
          p.save(); p.translate(X + cs / 2, Y + cs / 2); p.scale(sq * 0.9 + 0.1, 1); const pulse = 0.7 + 0.3 * Math.sin(now / 400 + x + y);
          p.fillStyle = show ? "#6A5020" : "#2E2C34"; p.fillRect(-cs / 2 + 3, -cs / 2 + 3, cs - 6, cs - 6); if (show) { const gg = p.createRadialGradient(0, 0, 2, 0, 0, cs * 0.6); gg.addColorStop(0, `rgba(255,224,112,${0.7 * pulse})`); gg.addColorStop(1, "rgba(255,180,60,0.1)"); p.fillStyle = gg; p.fillRect(-cs / 2 + 3, -cs / 2 + 3, cs - 6, cs - 6); }
          p.strokeStyle = show ? "#F0C850" : "#4A4852"; p.lineWidth = 2; p.strokeRect(-cs / 2 + 3, -cs / 2 + 3, cs - 6, cs - 6); p.lineWidth = 1;
          p.fillStyle = show ? "#FFF4C0" : "#5A5864"; if (show) { p.shadowColor = "#FFC040"; p.shadowBlur = 10; } p.font = `bold ${Math.round(cs * 0.5)}px serif`; p.textAlign = "center"; p.fillText(GLYPH[(x * 5 + y * 7 + Lv.n) % GLYPH.length], 0, cs * 0.18); p.shadowBlur = 0; p.textAlign = "left"; p.restore();
          if (hn.includes(`${x},${y}`)) { p.strokeStyle = hov[0] === x && hov[1] === y ? "rgba(255,255,255,0.8)" : "rgba(255,255,255,0.35)"; p.strokeRect(X + 1.5, Y + 1.5, cs - 3, cs - 3); } }
        p.fillStyle = "rgba(0,0,0,0.5)"; p.fillRect(cx - 70, y0 + Lv.h * cs + 10, 140, 20); p.fillStyle = "#F0E0B0"; p.font = "12px Georgia"; p.textAlign = "center"; p.fillText(`Vault ${Lv.n} · ${Lv.moves} touch${Lv.moves === 1 ? "" : "es"} (keeper ${Lv.par})`, cx, y0 + Lv.h * cs + 24); p.textAlign = "left"; }
      else { p.fillStyle = "#F0E0B0"; p.font = "18px Georgia"; p.textAlign = "center"; p.fillText("A sealed vault", cx, cy); p.font = "13px Georgia"; p.fillText("Try the lock", cx, cy + 22); p.textAlign = "left"; }
      p.restore();
    },
  });
}
