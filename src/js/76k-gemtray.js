"use strict";
// The Gemcutter's Tray, the window's side (the twenty-second big update): the tray on a canvas - cut stones drawn
// facet by facet, a swap that slides (and slides back when it does nothing), the cut stones flashing and bursting
// into sparks, the rest falling into their places and the new dropping in, the cascade called out as it climbs, a
// rune-stone's ring of gold and a star-stone's turning light; and beside it the score against the tray's mark. The
// rules are 64u-gemtray.js.
CM.CG_TABLES.push(["gemtray", "The Gemcutter's Tray"]);
CM.GT_ART = { ruby: ["#E02838", "#FF90A0", "hex"], sapphire: ["#2850E0", "#A0C0FF", "kite"], sunstone: ["#F08A18", "#FFE090", "round"], diamond: ["#D8F0FF", "#FFFFFF", "oct"], jade: ["#20A050", "#A0F0B0", "square"], amethyst: ["#9030D0", "#E0A0FF", "tri"], pearl: ["#E8E0D0", "#FFFFFF", "pearl"] };
{ const floor0 = CM.UI.prototype.renderFloor;
  Object.assign(CM.UI.prototype, {
    renderFloor(box) { if (this.cgView === "gemtray") return this.cgGemTray(box); return floor0.call(this, box); },
    cgGemTray(box) {
      const g = this.game, S = g.gtState(), T = g.gtTray(), GT = CM.GT, live = S && S.stage === "tray", bet = live || (S && S.stage !== "done") ? S.bet : (this.cgBet === undefined ? 5 : this.cgBet), last = S && S.last;
      const ladder = GT.TRAYS.map(([name, mv, tgt], i) => `<tr class="${live && S.n === i + 1 ? "now" : ""}${S && (S.n > i + 1 || (S.stage === "done" && S.cleared)) ? " done" : ""}"><td>${i + 1}. ${name} <small>${tgt} in ${mv}</small></td><td>${Math.round(bet * GT.PAY[i])}${GT.CARD[i + 1] ? ` <small>+ ${GT.CARD[i + 1]} card</small>` : ""}</td></tr>`).join("");
      box.innerHTML = `<div class="cgtable gemtray"><h3>The Gemcutter's Tray</h3><div class="gtwrap"><canvas class="gtcanvas" width="512" height="512"></canvas><div class="gtside">
        <p class="lore">A velvet tray under a jeweller's lamp, eight stones by eight, and a gemcutter's loupe on a chain. "Line them up and I cut them," she says. "Three of a kind, or better."</p>
        <div class="gtinfo">${T ? `<b>${GT.TRAYS[T.n - 1][0]}</b><div>Moves <b class="gtmv">${T.moves}</b> - best cascade <b class="gtcs">${T.best}</b></div><div class="gtbar"><span style="width:${Math.min(100, (100 * T.score) / T.target)}%"></span><em class="scx">${T.score} / ${T.target}</em></div>` : "<div>Put down a stake and start a run of five trays.</div>"}</div>
        <table class="paytable rfladder">${ladder}<tr><td colspan="2" class="small">Reach the tray's mark in its moves; each tray done pays its share of the stake. A tray left short pays back a little for the score you made.</td></tr></table>
        ${live ? "" : this.cgBetRow("The stake")}<div class="cgnote">${this.cgNote || ""}</div>${last && last.card ? this.cgCardWon(last.card) : ""}
        <div class="row">${live ? `<button data-gthint>A hint</button>` : `<button class="primary" data-gtstart>Start a run</button>`}<button data-leave>Leave</button></div>
        <div class="small">Click a stone, then a neighbour, to swap them (or drag). Four in a line, or an L or T, leaves a rune-stone that bursts its square of nine; five in a line a star-stone that, swapped, takes every stone of that kind.</div>${this.cgStats("gemtray")}</div></div></div>`;
      this.cgWireBet(box); box.querySelector("[data-leave]").addEventListener("click", () => this.closeDialogs());
      const st = box.querySelector("[data-gtstart]"); if (st) st.addEventListener("click", () => { const r = g.gtStart(bet); this.cgNote = r.error || "The first tray. Line them up!"; this.cgSfx(r.error ? "miss" : "chain", 0.4); this.gtDisp = null; this.renderCasino(); });
      const hb = box.querySelector("[data-gthint]"); if (hb) hb.addEventListener("click", () => { const Tr = g.gtTray(); this.gtHintAt = performance.now(); this.gtHint = Tr && Tr.hint(); this.cgSfx("card", 0.3, 1.4); });
      const cv = box.querySelector(".gtcanvas"); this.gtCanvas = cv;
      const cell = (e) => { const r = cv.getBoundingClientRect(); return [Math.floor(((e.clientX - r.left) * 512) / r.width / 64), Math.floor(((e.clientY - r.top) * 512) / r.height / 64)]; };
      cv.addEventListener("mousedown", (e) => { if (this.gtBusy()) return; const [x, y] = cell(e); const s = this.gtSel; if (s && Math.abs(s[0] - x) + Math.abs(s[1] - y) === 1) { this.gtTry(s[0], s[1], x, y); this.gtSel = null; return; } this.gtSel = [x, y]; this.gtDrag = [x, y]; this.cgSfx("card", 0.25, 1.3); });
      cv.addEventListener("mouseup", (e) => { const d = this.gtDrag; this.gtDrag = null; if (!d || this.gtBusy()) return; const [x, y] = cell(e); if (Math.abs(d[0] - x) + Math.abs(d[1] - y) === 1) { this.gtTry(d[0], d[1], x, y); this.gtSel = null; } });
      if (!this.gtLoop) { let prev = performance.now(); const loop = (now) => { if (!this.gtCanvas || !this.gtCanvas.isConnected || this.cgView !== "gemtray") { this.gtLoop = null; return; } const dt = Math.min(0.05, (now - prev) / 1000); prev = now; this.gtFrame(dt, now); this.gtLoop = requestAnimationFrame(loop); }; this.gtLoop = requestAnimationFrame(loop); }
    },
    gtBusy() { return (this.gtQueue && this.gtQueue.length) || this.gtPhase || this.gtSettling; },
    // the stones as drawn: where each one is, and where it is going
    gtSync(T) { const D = this.gtDisp = new Map(); for (let y = 0; y < 8; y++) for (let x = 0; x < 8; x++) { const s = T.grid[y][x]; D.set(s.id, { x, y, tx: x, ty: y, vy: 0, k: s.k, sp: s.sp, pop: 0 }); } this.gtKey = T.key; },
    gtTry(x1, y1, x2, y2) {
      const T = this.game.gtTray(); if (!T || T.stage !== "play") return; const D = this.gtDisp, a = T.grid[y1][x1], b = T.grid[y2][x2];
      const phases = T.swap(x1, y1, x2, y2); this.gtHint = null;
      if (!phases) { const da = D.get(a.id), db = D.get(b.id); da.tx = x2; da.ty = y2; db.tx = x1; db.ty = y1; this.gtBounce = { a: a.id, b: b.id, x1, y1, x2, y2, t: 0 }; this.cgSfx("miss", 0.3); return; }
      const da = D.get(a.id), db = D.get(b.id); da.tx = x2; da.ty = y2; db.tx = x1; db.ty = y1; this.cgSfx("cardplace", 0.35, 1.1);
      this.gtQueue = phases.slice(1); this.gtPhase = { kind: "wait", t: 0.16 };
    },
    gtFrame(dt, now) {
      const g = this.game, T = g.gtTray(), GT = CM.GT, cv = this.gtCanvas, p = cv.getContext("2d");
      p.fillStyle = "#1A0E14"; p.fillRect(0, 0, 512, 512);
      for (let y = 0; y < 8; y++) for (let x = 0; x < 8; x++) { p.fillStyle = (x + y) % 2 ? "#3A1828" : "#44202F"; p.fillRect(x * 64, y * 64, 64, 64); p.fillStyle = "rgba(255,255,255,0.025)"; p.beginPath(); p.moveTo(x * 64 + 32, y * 64 + 6); p.lineTo(x * 64 + 58, y * 64 + 32); p.lineTo(x * 64 + 32, y * 64 + 58); p.lineTo(x * 64 + 6, y * 64 + 32); p.fill(); }
      const lamp = p.createRadialGradient(256, 160, 40, 256, 256, 420); lamp.addColorStop(0, "rgba(255,230,170,0.12)"); lamp.addColorStop(1, "rgba(0,0,0,0.35)"); p.fillStyle = lamp; p.fillRect(0, 0, 512, 512);
      if (!T) { p.fillStyle = "rgba(255,240,200,0.85)"; p.font = "bold 28px Georgia, serif"; p.textAlign = "center"; const S = g.gtState(); p.fillText(S && S.stage === "done" ? (S.cleared ? "Five trays cut!" : "The run is over") : "The Gemcutter's Tray", 256, 256); p.textAlign = "left"; return; }
      if (!this.gtDisp || this.gtKey !== T.key) { this.gtSync(T); this.gtQueue = []; this.gtPhase = null; this.gtParts = []; }
      const D = this.gtDisp;
      // a swap that did nothing goes back
      if (this.gtBounce) { const B = this.gtBounce; B.t += dt; if (B.t > 0.16 && !B.back) { B.back = true; const da = D.get(B.a), db = D.get(B.b); da.tx = B.x1; da.ty = B.y1; db.tx = B.x2; db.ty = B.y2; } if (B.t > 0.34) this.gtBounce = null; }
      // the phases, one after another
      if (this.gtPhase) { const P = this.gtPhase; P.t -= dt; const settled = [...D.values()].every((d) => Math.abs(d.x - d.tx) < 0.02 && Math.abs(d.y - d.ty) < 0.02);
        if (P.t <= 0 && settled) { this.gtPhase = null; const next = this.gtQueue.shift(); if (next) this.gtBegin(next, now); else this.gtDone(T); } }
      // move the stones toward their places: falling ones fall, the rest slide
      for (const [id, d] of D) { if (d.dead) { d.pop += dt * 4.5; if (d.pop >= 1) D.delete(id); continue; } const dx = d.tx - d.x; d.x += Math.sign(dx) * Math.min(Math.abs(dx), dt * 7); if (d.ty > d.y) { d.vy += dt * 40; d.y = Math.min(d.ty, d.y + d.vy * dt); if (d.y >= d.ty) { if (d.vy > 4) d.land = 0.12; d.vy = 0; } } else { const dy = d.ty - d.y; d.y += Math.sign(dy) * Math.min(Math.abs(dy), dt * 7); } if (d.land) d.land = Math.max(0, d.land - dt); if (d.grow !== undefined && d.grow < 1) d.grow = Math.min(1, d.grow + dt * 4); }
      const hint = this.gtHint && now - this.gtHintAt < 3000 ? this.gtHint : null;
      for (const [, d] of D) this.gtDrawGem(p, d, now, (this.gtSel && this.gtSel[0] === Math.round(d.tx) && this.gtSel[1] === Math.round(d.ty) && !d.dead) || (hint && ((hint[0] === d.tx && hint[1] === d.ty) || (hint[2] === d.tx && hint[3] === d.ty))));
      // glints: now and then a stone catches the lamp
      if (Math.random() < dt * 2.5 && D.size) { const ds = [...D.values()].filter((d) => !d.dead), d = ds[Math.floor(Math.random() * ds.length)]; if (d) (this.gtGlints = this.gtGlints || []).push({ x: d.tx * 64 + 32 - 8 + Math.random() * 10, y: d.ty * 64 + 32 - 12 + Math.random() * 8, at: now }); }
      this.gtGlints = (this.gtGlints || []).filter((q) => now - q.at < 600); for (const q of this.gtGlints) { const k = (now - q.at) / 600, r = Math.sin(k * Math.PI) * 9; p.save(); p.globalAlpha = Math.sin(k * Math.PI); p.fillStyle = "#FFFFFF"; p.translate(q.x, q.y); p.rotate(k); p.beginPath(); p.moveTo(0, -r); p.lineTo(r * 0.18, 0); p.lineTo(0, r); p.lineTo(-r * 0.18, 0); p.closePath(); p.moveTo(-r, 0); p.lineTo(0, r * 0.18); p.lineTo(r, 0); p.lineTo(0, -r * 0.18); p.closePath(); p.fill(); p.restore(); }
      this.gtRings = (this.gtRings || []).filter((r) => now - r.at < 380); for (const r of this.gtRings) { const k = (now - r.at) / 380; p.strokeStyle = r.c; p.globalAlpha = 1 - k; p.lineWidth = 3 * (1 - k) + 0.5; p.beginPath(); p.arc(r.x, r.y, 14 + k * 30, 0, Math.PI * 2); p.stroke(); } p.globalAlpha = 1; p.lineWidth = 1;
      // sparks
      this.gtParts = (this.gtParts || []).filter((q) => (q.life -= dt) > 0); for (const q of this.gtParts) { q.x += q.vx * dt; q.y += q.vy * dt; q.vy += 260 * dt; p.globalAlpha = Math.min(1, q.life * 2); p.fillStyle = q.c; p.fillRect(q.x - 1.5, q.y - 1.5, 3, 3); } p.globalAlpha = 1;
      // the cascade's call
      if (this.gtCall && now - this.gtCall.at < 900) { const k = (now - this.gtCall.at) / 900; p.save(); p.globalAlpha = 1 - k; p.fillStyle = "#FFE070"; p.strokeStyle = "#3A1A08"; p.lineWidth = 4; p.font = `bold ${30 + this.gtCall.n * 3}px Georgia, serif`; p.textAlign = "center"; p.strokeText(this.gtCall.text, 256, 240 - k * 40); p.fillText(this.gtCall.text, 256, 240 - k * 40); p.restore(); }
      if (T.stage !== "play" && !this.gtBusy()) { p.fillStyle = "rgba(0,0,0,0.55)"; p.fillRect(0, 206, 512, 100); p.fillStyle = T.stage === "won" ? "#FFE070" : "#FF9080"; p.font = "bold 32px Georgia, serif"; p.textAlign = "center"; p.fillText(T.stage === "won" ? "The tray is cut!" : "Out of moves", 256, 268); p.textAlign = "left"; }
      const side = cv.parentElement; if (side) { const q = (s) => side.querySelector(s); if (q(".gtmv")) q(".gtmv").textContent = T.moves; if (q(".gtcs")) q(".gtcs").textContent = T.best; const bar = q(".gtbar span"); if (bar) bar.style.width = `${Math.min(100, (100 * (this.gtShown === undefined ? T.score : this.gtShown)) / T.target)}%`; if (q(".scx")) q(".scx").textContent = `${this.gtShown === undefined ? T.score : this.gtShown} / ${T.target}`; }
    },
    // a phase begun: the cut stones flash and burst, the made ones grow, the rest fall
    gtBegin(P, now) {
      const D = this.gtDisp;
      if (P.kind === "shake") { for (let y = 0; y < 8; y++) for (let x = 0; x < 8; x++) { const s = P.grid[y][x], d = D.get(s.id); if (d) { d.tx = x; d.ty = y; } } this.cgSfx("chain", 0.45); this.gtCall = { text: "Shaken up", n: 0, at: now }; this.gtPhase = { kind: "shake", t: 0.4 }; return; }
      for (const c of P.cut) { const d = D.get(c.id); if (d) { d.dead = true; d.pop = 0; } const [col] = CM.GT_ART[CM.GT.KINDS[c.k]] || ["#FFF"]; (this.gtRings = this.gtRings || []).push({ x: c.x * 64 + 32, y: c.y * 64 + 32, at: now, c: col }); for (let k = 0; k < 7; k++) this.gtParts.push({ x: c.x * 64 + 32, y: c.y * 64 + 32, vx: (Math.random() - 0.5) * 260, vy: -Math.random() * 220, life: 0.6 + Math.random() * 0.3, c: k % 2 ? "#FFF6D0" : col }); }
      for (const m of P.placed) D.set(m.id, { x: m.x, y: m.y, tx: m.x, ty: m.y, vy: 0, k: m.k, sp: m.sp, pop: 0, grow: 0 });
      for (const f of P.falls) { const d = D.get(f.id); if (f.fresh) D.set(f.id, { x: f.x, y: f.from, tx: f.x, ty: f.to, vy: 0, k: f.k, sp: null, pop: 0 }); else if (d) d.ty = f.to; }
      this.gtShown = P.score;
      const n = P.cascade; this.cgSfx(P.kind === "star" ? "spell" : "coin", 0.45, Math.min(2.2, 0.9 + n * 0.15)); this.cgSfx("card", 0.3, Math.min(2.4, 1 + n * 0.18));
      if (P.burst) this.cgSfx("shatter", 0.5); if (P.placed.some((m) => m.sp === "star")) this.cgSfx("zap", 0.5); else if (P.placed.length) this.cgSfx("tablebell", 0.4);
      if (n >= 2) this.gtCall = { text: n >= 5 ? `Dazzling! x${n}` : n >= 3 ? `Brilliant! x${n}` : `Cascade x${n}`, n, at: now };
      if (P.kind === "star") this.gtCall = { text: "Starburst!", n: 4, at: now };
      this.gtPhase = { kind: P.kind, t: 0.24 };
    },
    gtDone(T) {
      this.gtShown = undefined;
      if (T.stage !== "play" && !this.gtSettling) { this.gtSettling = true; if (T.stage === "won") { this.cgSfx("victory", 0.6); this.cgSfx("cardwin", 0.5); } else this.cgSfx("cardlose", 0.5);
        setTimeout(() => { this.gtSettling = false; const r = this.game.gtSettle(); if (!r) return; this.cgNote = r.won ? `Tray ${r.n} done: ${r.pay} gold back.${this.game.gtState().stage === "done" ? " Every tray cut!" : " On to the next."}` : `Out of moves at ${r.score}. ${r.pay ? `${r.pay} gold back for the score.` : ""}`; this.gtDisp = null; this.renderCasino(); if (r.won) this.cgCoins(this.$("#casino-body"), 12); }, 1100); }
    },
    gtDrawGem(p, d, now, lit) {
      const A = CM.GT_ART[CM.GT.KINDS[d.k]] || CM.GT_ART.pearl, [c0, c1, shape] = A, cx = d.x * 64 + 32, cy = d.y * 64 + 32 + (d.land ? Math.sin(d.land * 26) * 2 : 0), s = (d.dead ? 1 + d.pop * 0.6 : d.grow !== undefined ? d.grow : 1) * 24 * (lit && !d.dead ? 1 + 0.06 * Math.sin(now / 110) : 1);
      if (!d.dead) { p.fillStyle = "rgba(0,0,0,0.28)"; p.beginPath(); p.ellipse(cx + 3, cy + s * 0.92, s * 0.75, s * 0.2, 0, 0, Math.PI * 2); p.fill(); }
      p.save(); p.globalAlpha = d.dead ? Math.max(0, 1 - d.pop) : 1; p.translate(cx, cy);
      if (lit) { p.shadowColor = "#FFF0A0"; p.shadowBlur = 18 + 6 * Math.sin(now / 120); }
      if (d.sp === "star") { const n = 5, rot = now / 700; p.rotate(rot); const gr = p.createLinearGradient(-s, -s, s, s); ["#FF5060", "#FFC040", "#60E080", "#60A0FF", "#C070FF"].forEach((c, i) => gr.addColorStop(i / 4, c)); p.fillStyle = gr; p.beginPath(); for (let i = 0; i < n * 2; i++) { const r = i % 2 ? s * 0.45 : s, a = (i / (n * 2)) * Math.PI * 2; p.lineTo(Math.sin(a) * r, -Math.cos(a) * r); } p.closePath(); p.fill(); p.strokeStyle = "#FFF"; p.lineWidth = 2; p.stroke(); p.restore(); return; }
      const g2 = p.createLinearGradient(-s, -s, s, s); g2.addColorStop(0, c1); g2.addColorStop(0.5, c0); g2.addColorStop(1, "#000000"); p.fillStyle = g2; p.beginPath();
      const poly = (pts) => { pts.forEach(([x, y], i) => (i ? p.lineTo(x * s, y * s) : p.moveTo(x * s, y * s))); p.closePath(); };
      if (shape === "hex") poly([[0, -1], [0.87, -0.5], [0.87, 0.5], [0, 1], [-0.87, 0.5], [-0.87, -0.5]]); else if (shape === "kite") poly([[0, -1], [0.8, -0.2], [0, 1], [-0.8, -0.2]]); else if (shape === "oct") poly([[-0.4, -0.95], [0.4, -0.95], [0.95, -0.4], [0.95, 0.4], [0.4, 0.95], [-0.4, 0.95], [-0.95, 0.4], [-0.95, -0.4]]);
      else if (shape === "square") poly([[-0.78, -0.78], [0.78, -0.78], [0.78, 0.78], [-0.78, 0.78]]); else if (shape === "tri") poly([[0, -1], [0.95, 0.8], [-0.95, 0.8]]); else p.arc(0, 0, s * 0.88, 0, Math.PI * 2);
      p.fill(); p.shadowBlur = 0; p.strokeStyle = "rgba(255,255,255,0.55)"; p.lineWidth = 1.5; p.stroke();
      p.fillStyle = "rgba(255,255,255,0.55)"; p.beginPath(); p.ellipse(-s * 0.28, -s * 0.34, s * 0.24, s * 0.12, -0.6, 0, Math.PI * 2); p.fill();
      if (shape !== "round" && shape !== "pearl") { p.strokeStyle = "rgba(255,255,255,0.22)"; p.beginPath(); p.moveTo(-s * 0.4, 0); p.lineTo(0, -s * 0.4); p.lineTo(s * 0.4, 0); p.lineTo(0, s * 0.4); p.closePath(); p.stroke(); }
      if (d.sp === "rune") { p.rotate(now / 900); p.strokeStyle = "#F0C040"; p.lineWidth = 3; p.shadowColor = "#FFE080"; p.shadowBlur = 10; p.beginPath(); p.arc(0, 0, s * 1.05, 0, Math.PI * 2); p.stroke(); p.fillStyle = "#FFE080"; for (let k = 0; k < 4; k++) { p.rotate(Math.PI / 2); p.fillRect(-2, -s * 1.12, 4, 6); } }
      p.restore();
    },
  });
}
