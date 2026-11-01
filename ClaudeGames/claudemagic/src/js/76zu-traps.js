"use strict";
// The Trapfinder's Grid, the window's side: a floor of worn flagstones lit by a lantern that follows the mouse; a stone
// lifted flips up and away to show the earth below with its number carved in a rune-colour (1 blue, 2 green, 3 red ...),
// pennants on their little poles flutter on marked stones, and a trap struck springs its spikes with a flash and the
// floor shakes - the others then show where they were, and the wrongly marked ones crossed. A floor cleared: the traps
// marked in gold and the stones glint. Left-click to lift, right-click to mark, click a number to lift around it.
// The rules are 64zzc-traps.js.
CM.CG_TABLES.push(["traps", "The Trapfinder's Grid"]);
{ const floor0 = CM.UI.prototype.renderFloor, TRP = CM.TRP, NUM = ["", "#4A80F0", "#40B050", "#E04040", "#8040C0", "#C06020", "#30A0A0", "#E0E0E0", "#A0A0A0"];
  Object.assign(CM.UI.prototype, {
    renderFloor(box) { if (this.cgView === "traps") return this.cgTraps(box); return floor0.call(this, box); },
    cgTraps(box) {
      const g = this.game, T = g.tfStore(), B = g.tfLive, size = (B && B.size) || this.tfSize || "cellar", S = TRP.SIZES[size];
      box.innerHTML = `<div class="cgtable traps"><h3>The Trapfinder's Grid</h3><p class="lore">Down a stair behind the Joker's kitchens there are floors the old masons trapped. The house would like them made safe. "Lift every stone that hides nothing," says the old trapfinder, handing over a lantern and a bundle of pennants. "The numbers tell you how many traps lie next to them."</p>
        <div class="row tfsizes">${Object.entries(TRP.SIZES).map(([k, s]) => `<button data-tfnew="${k}" class="${k === size ? "primary" : ""}">${s.name[4].toUpperCase() + s.name.slice(5)} - ${s.w}×${s.h}, ${s.n} traps${T.cards[k] ? " ✓" : ""}</button>`).join("")}</div>
        <div class="tfwrap"><canvas class="tfcanvas"></canvas></div>
        <div class="cgnote">${this.cgNote || ""}</div>${this.tfCard ? this.cgCardWon(this.tfCard) : ""}
        <div class="small">Left-click to lift a stone, right-click to plant or pull a pennant, click a number whose pennants are all down to lift the rest around it. The first stone is always safe. ${S.name[0].toUpperCase() + S.name.slice(1)} pays ${S.gold} gold and ${S.tickets} tickets; its card the first time. Best times: ${Object.keys(TRP.SIZES).map((k) => `${k} ${T.best[k] ? `${T.best[k]}s` : "-"}`).join(", ")}. Won ${Object.keys(TRP.SIZES).map((k) => `${T.wins[k] || 0}/${T.played[k] || 0}`).join(", ")}.</div><div class="row"><button data-leave>Leave</button></div></div>`;
      const q = (s) => box.querySelector(s); q("[data-leave]").addEventListener("click", () => this.closeDialogs());
      box.querySelectorAll("[data-tfnew]").forEach((b) => b.addEventListener("click", () => { this.tfSize = b.dataset.tfnew; g.tfNew(this.tfSize); this.tfFx = { flips: [], at: performance.now() }; this.tfCard = null; this.cgNote = "Lift a stone - the first is always safe."; this.cgSfx("door", 0.35); this.renderCasino(); }));
      const cv = this.tfCanvas = q(".tfcanvas"), Bd = B || { w: S.w, h: S.h }, cs = Math.min(40, Math.floor(Math.min(720 / Bd.w, 480 / Bd.h))); cv.width = Bd.w * cs; cv.height = Bd.h * cs; this.tfCs = cs;
      const cell = (e) => { const r = cv.getBoundingClientRect(); return [Math.floor(((e.clientX - r.left) / r.width) * Bd.w), Math.floor(((e.clientY - r.top) / r.height) * Bd.h)]; };
      cv.addEventListener("mousemove", (e) => { const r = cv.getBoundingClientRect(); this.tfMouse = [((e.clientX - r.left) / r.width) * cv.width, ((e.clientY - r.top) / r.height) * cv.height]; });
      cv.addEventListener("contextmenu", (e) => e.preventDefault());
      cv.addEventListener("mousedown", (e) => { const Bl = g.tfLive; if (!Bl || Bl.stage !== "play") return; const [x, y] = cell(e); if (x < 0 || y < 0 || x >= Bl.w || y >= Bl.h) return;
        if (e.button === 2) Bl.toggle(x, y); else if (Bl.open[y][x]) Bl.chord(x, y); else Bl.reveal(x, y); this.tfAfter(); });
      if (!this.tfLoop) { let prev = performance.now(); const loop = (now) => { if (!this.tfCanvas || !this.tfCanvas.isConnected || this.cgView !== "traps") { this.tfLoop = null; return; } const dt = Math.min(0.05, (now - prev) / 1000); prev = now; this.tfFrame(dt, now); this.tfLoop = requestAnimationFrame(loop); }; this.tfLoop = requestAnimationFrame(loop); }
    },
    tfAfter() {
      const g = this.game, B = g.tfLive, fx = this.tfFx = this.tfFx || { flips: [] }, now = performance.now(); let re = false;
      for (const e of B.events.splice(0)) {
        if (e.kind === "lift") { this.cgSfx("step", 0.3, 1.2 + Math.min(0.8, e.n / 40)); for (let y = 0; y < B.h; y++) for (let x = 0; x < B.w; x++) if (B.open[y][x] && !(fx.seen && fx.seen[y * 100 + x])) { (fx.seen = fx.seen || {})[y * 100 + x] = 1; fx.flips.push({ x, y, at: now + Math.hypot(x - e.x, y - e.y) * 25 }); } }
        else if (e.kind === "flag") this.cgSfx("card", 0.3, 1.5); else if (e.kind === "unflag") this.cgSfx("card", 0.2, 1.1);
        else if (e.kind === "boom") { this.cgSfx("slam", 0.6, 0.8); this.cgSfx("hurt", 0.4); fx.boom = now; this.cgNote = `A trap! The floor is lost after ${Math.round(B.t)} seconds.`; re = true; }
        else if (e.kind === "won") { const r = g.tfWin(); if (r) { this.cgNote = `${TRP.SIZES[B.size].name[0].toUpperCase() + TRP.SIZES[B.size].name.slice(1)} made safe in ${r.time}s${r.record ? " - a best time!" : ""}: ${r.gold} gold and ${r.tickets} tickets${r.card ? `, and a card - ${r.card}` : ""}.`; this.tfCard = r.card; this.cgSfx("victory", 0.6); if (r.card) setTimeout(() => this.cgSfx("cardwin", 0.5), 400); fx.won = now; re = true; } }
      }
      if (re) setTimeout(() => this.renderCasino(), 30);
    },
    tfFrame(dt, now) {
      const g = this.game, B = g.tfLive, cv = this.tfCanvas, p = cv.getContext("2d"), cs = this.tfCs, fx = this.tfFx = this.tfFx || { flips: [] }; if (B) B.update(dt);
      const W = cv.width, H = cv.height, sh = fx.boom && now - fx.boom < 500 ? (1 - (now - fx.boom) / 500) * 8 : 0; p.save(); p.translate((Math.random() - 0.5) * sh, (Math.random() - 0.5) * sh);
      p.fillStyle = "#1A140E"; p.fillRect(-10, -10, W + 20, H + 20); const w = B ? B.w : W / cs, h = B ? B.h : H / cs;
      for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) { const X = x * cs, Y = y * cs, open = B && B.open[y][x], f = fx.flips.find((q) => q.x === x && q.y === y), k = f ? CM.ARC.clamp((now - f.at) / 180, 0, 1) : 1;
        if (open && k > 0) { p.fillStyle = (x + y) % 2 ? "#3A2E22" : "#40342A"; p.fillRect(X, Y, cs, cs); p.fillStyle = "rgba(0,0,0,0.35)"; p.fillRect(X, Y, cs, 3); p.fillRect(X, Y, 3, cs);
          if (B.mine && B.mine[y][x]) { const hit = B.boom && B.boom[0] === x && B.boom[1] === y; if (hit) { p.fillStyle = "#802010"; p.fillRect(X, Y, cs, cs); } this.tfTrap(p, X, Y, cs, hit ? now - fx.boom : 999); }
          else { const n = B.count(x, y); if (n) { p.fillStyle = NUM[n]; p.font = `bold ${Math.round(cs * 0.55)}px Georgia`; p.textAlign = "center"; p.fillText(String(n), X + cs / 2, Y + cs * 0.7); p.textAlign = "left"; } } }
        if (!open || k < 1) { const lift = open ? k : 0; p.save(); p.translate(X + cs / 2, Y + cs / 2 - lift * cs * 0.6); p.scale(1 - lift * 0.4, 1 - lift * 0.7); p.globalAlpha = 1 - lift;
          const st = p.createLinearGradient(-cs / 2, -cs / 2, cs / 2, cs / 2), shade = 100 + ((x * 37 + y * 53) % 23); st.addColorStop(0, `rgb(${shade + 30},${shade + 22},${shade + 10})`); st.addColorStop(1, `rgb(${shade - 20},${shade - 26},${shade - 34})`); p.fillStyle = st; p.fillRect(-cs / 2 + 1, -cs / 2 + 1, cs - 2, cs - 2);
          p.fillStyle = "rgba(255,255,255,0.14)"; p.fillRect(-cs / 2 + 1, -cs / 2 + 1, cs - 2, 2); p.fillStyle = "rgba(0,0,0,0.25)"; p.fillRect(-cs / 2 + 1, cs / 2 - 3, cs - 2, 2); if ((x * 7 + y * 3) % 5 === 0) { p.strokeStyle = "rgba(0,0,0,0.25)"; p.beginPath(); p.moveTo(-cs / 4, -cs / 5); p.lineTo(cs / 8, cs / 6); p.stroke(); }
          p.restore();
          if (B && B.flag[y][x] && !open) { const wv = Math.sin(now / 200 + x + y) * 2, wrong = B.stage === "lost" && !B.mine[y][x], gold = B.stage === "won"; p.strokeStyle = "#3A2A1A"; p.lineWidth = 2; p.beginPath(); p.moveTo(X + cs * 0.35, Y + cs * 0.82); p.lineTo(X + cs * 0.35, Y + cs * 0.2); p.stroke(); p.lineWidth = 1; p.fillStyle = gold ? "#F0C040" : "#C02830"; p.beginPath(); p.moveTo(X + cs * 0.37, Y + cs * 0.2); p.lineTo(X + cs * 0.75, Y + cs * 0.32 + wv); p.lineTo(X + cs * 0.37, Y + cs * 0.46); p.fill();
            if (wrong) { p.strokeStyle = "#FF4040"; p.lineWidth = 3; p.beginPath(); p.moveTo(X + 5, Y + 5); p.lineTo(X + cs - 5, Y + cs - 5); p.moveTo(X + cs - 5, Y + 5); p.lineTo(X + 5, Y + cs - 5); p.stroke(); p.lineWidth = 1; } }
          if (B && B.stage === "lost" && B.mine[y][x] && !B.flag[y][x] && !open) { p.globalAlpha = 0.85; this.tfTrap(p, X, Y, cs, 999); p.globalAlpha = 1; } } }
      // the lantern
      if (this.tfMouse) { const [mx, my] = this.tfMouse, lg = p.createRadialGradient(mx, my, 10, mx, my, cs * 5); lg.addColorStop(0, "rgba(255,220,150,0.14)"); lg.addColorStop(1, "rgba(0,0,0,0.22)"); p.fillStyle = lg; p.fillRect(0, 0, W, H); } else { p.fillStyle = "rgba(0,0,0,0.12)"; p.fillRect(0, 0, W, H); }
      if (fx.won && now - fx.won < 1500) { const k = (now - fx.won) / 1500; p.fillStyle = `rgba(255,230,140,${0.35 * (1 - k)})`; p.fillRect(0, 0, W, H); }
      p.restore();
      if (B) { p.fillStyle = "rgba(0,0,0,0.55)"; p.fillRect(4, 4, 150, 20); p.fillStyle = "#FFE070"; p.font = "bold 12px monospace"; p.fillText(`⚑ ${B.n - B.flags()}   ⏱ ${Math.round(B.t)}s`, 10, 18); }
      else { p.fillStyle = "rgba(0,0,0,0.5)"; p.fillRect(0, H / 2 - 20, W, 40); p.fillStyle = "#F0E0B0"; p.font = "16px Georgia"; p.textAlign = "center"; p.fillText("Choose a floor to search", W / 2, H / 2 + 6); p.textAlign = "left"; }
    },
    // a spike trap, sprung over a short while
    tfTrap(p, X, Y, cs, age) { const k = CM.ARC.clamp(age / 160, 0, 1); p.fillStyle = "#2A2A30"; p.fillRect(X + cs * 0.15, Y + cs * 0.7, cs * 0.7, cs * 0.12); p.fillStyle = "#B8C0C8"; for (let i = 0; i < 4; i++) { const sx = X + cs * (0.2 + i * 0.18); p.beginPath(); p.moveTo(sx, Y + cs * 0.72); p.lineTo(sx + cs * 0.07, Y + cs * (0.72 - 0.5 * k)); p.lineTo(sx + cs * 0.14, Y + cs * 0.72); p.fill(); }
      if (age < 300) { p.fillStyle = `rgba(255,200,80,${1 - age / 300})`; p.beginPath(); p.arc(X + cs / 2, Y + cs / 2, cs * (0.3 + age / 200), 0, Math.PI * 2); p.fill(); } },
  });
}
