"use strict";
// The Wishing Claw, the window's side (the thirty-sixth big update): the three machines as tabs, and the chosen one's
// glass case on a canvas, seen from the front - its frame in copper, silver or gold, coloured lights along the top,
// the felt floor going back in perspective, the chute in the front corner, the prizes from the back forward (a gold
// pouch, a little hoard chest, card capsules, mystery eggs, and soft plush weapons, armour, shields and helms), the
// claw on its rail with a shadow on the floor beneath it to aim by, its prongs opening and closing, what it holds
// swinging below. Hold the button (or Space, or an arrow) to send the claw right, let go; hold again to send it back,
// let go, and it drops. The rules are 64zm-claw.js.
CM.CG_TABLES.push(["claw", "The Wishing Claw"]);
{ const floor0 = CM.UI.prototype.renderFloor, CWID = 480, CHT = 420, FRONT = 380, ZSTEP = 36, CEIL = 70;
  const FRAME = { copper: ["#B06A3A", "#6A3A1A"], silver: ["#C8D0D8", "#6A7078"], gold: ["#F0C040", "#8A6A10"] };
  const scale = (z) => 40 * (1 - 0.05 * z), sx = (x, z) => CWID / 2 + (x - CM.CW.W / 2) * scale(z), sy = (z) => FRONT - z * ZSTEP;
  const LABEL = { pouch: "a gold pouch", hoard: "a hoard of gold", card: "a card capsule", egg: "a mystery egg", weapon: "a weapon", armor: "armour", shield: "a shield", helm: "a helm" };
  Object.assign(CM.UI.prototype, {
    renderFloor(box) { if (this.cgView === "claw") return this.cgClaw(box); return floor0.call(this, box); },
    cgClaw(box) {
      const g = this.game, CW = CM.CW, tier = this.cwTier = this.cwTier || "copper", T = CW.TIERS[tier], L = g.cwLive, busy = L && L.stage !== "done", open = g.cwOpen(tier), M = g.cwMachine(tier);
      const tabs = Object.entries(CW.TIERS).map(([k, t]) => `<button data-cwtier="${k}" class="${k === tier ? "primary" : ""}" ${busy ? "disabled" : ""}>${t.name.replace("the ", "The ")} - ${t.price} gold${g.cwOpen(k) ? "" : " 🔒"}</button>`).join("");
      const out = this.cwOut, item = out && out.item, rar = item && CM.rarityOf ? CM.rarityOf(item) : "";
      box.innerHTML = `<div class="cgtable claw runestack dash"><h3>The Wishing Claw</h3><div class="row cwtabs">${tabs}</div><div class="rswrap"><canvas class="cwcanvas" width="${CWID}" height="${CHT}"></canvas>
        <div class="dashside"><p class="lore">Three glass cases by the Joker's door, each full of prizes, each with a brass claw on a rail. "Real prizes," says the attendant, tapping the glass. "Gold, cards, steel. The copper one's for anyone. The silver and the gold ones are for parties who've been deep."</p>
        <div class="cwlegend">${Object.keys(CW.PRIZES).map((k) => `<span><canvas class="cwicon" data-cwicon="${k}" width="34" height="34"></canvas>${LABEL[k]}</span>`).join("")}</div>
        <div class="cgnote">${this.cgNote || ""}</div>${out && out.card ? this.cgCardWon(out.card) : ""}${item ? `<div class="cwprize rarity-${rar}">${item.name}${item.unknown ? " (not yet known)" : ""} - ${item.kind}${rar ? `, ${rar}` : ""}. It is in the party's pack.</div>` : ""}
        <div class="row">${busy ? `<button class="primary cwhold" data-cwhold>${L.stage === "x" ? "Hold: claw right →" : L.stage === "z" ? "Hold: claw back ↑" : "…"}</button>` : open ? `<button class="primary" data-cwstart>Insert ${T.price} gold</button>` : `<button disabled>Locked - reach floor ${T.need}</button>`}<button data-leave>Leave</button></div>
        <div class="small">Hold the button (or Space, or an arrow key) to slide the claw right, and let go; hold again to send it back, and let go - it drops. Fifteen seconds, then it drops wherever it is. Watch its shadow on the floor. It grips the prize nearest under it - more surely right over the middle, and light things (pouches, cards, eggs) more surely than heavy (hoards, armour) - and may lose it on the way to the chute (if it falls over the chute, it's yours anyway). ${T.name[0].toUpperCase() + T.name.slice(1)}'s gear is made for floor ${T.depth} (${Math.round(T.affix * 100)}% enchanted), its cards are ${T.card === "better" ? "stronger commons" : `${T.card}s`}, its pouches hold about ${Math.round(T.price * CW.PRIZES.pouch.gold)} gold and its hoards about ${Math.round(T.price * CW.PRIZES.hoard.gold)}. Prizes won here: ${M.won}.</div>${this.cgStats("claw")}</div></div></div>`;
      const q = (s) => box.querySelector(s); q("[data-leave]").addEventListener("click", () => this.closeDialogs());
      box.querySelectorAll("[data-cwtier]").forEach((b) => b.addEventListener("click", () => { this.cwTier = b.dataset.cwtier; this.cwOut = null; this.cgNote = ""; this.renderCasino(); }));
      box.querySelectorAll("[data-cwicon]").forEach((c) => { const p = c.getContext("2d"); this.cwPrize(p, { kind: c.dataset.cwicon, rot: 0.3 }, 17, 20, 0.62, tier); });
      if (q("[data-cwstart]")) q("[data-cwstart]").addEventListener("click", () => { const r = g.cwStart(tier); this.cwOut = null; this.cgNote = r.error || "Hold to send the claw right…"; this.cwFx = { falls: [] }; this.cgSfx(r.error ? "miss" : "coin", 0.45); this.renderCasino(); });
      const hb = q("[data-cwhold]"); if (hb) { const set = (v) => { this.cwHolding = v; }; hb.addEventListener("mousedown", () => set(true)); hb.addEventListener("mouseup", () => set(false)); hb.addEventListener("mouseleave", () => set(false)); hb.addEventListener("touchstart", (e) => { e.preventDefault(); set(true); }); hb.addEventListener("touchend", () => set(false)); }
      this.cwCanvas = q(".cwcanvas");
      if (!this.cwKeys) { this.cwKeys = (e) => { if (this.cgView !== "claw" || !this.dialogOpen() || !this.game.cwLive || this.game.cwLive.stage === "done") return; if (!["Space", "ArrowRight", "ArrowUp", "KeyD", "KeyW"].includes(e.code)) return; e.preventDefault(); e.stopPropagation(); this.cwKeyHold = e.type === "keydown"; }; window.addEventListener("keydown", this.cwKeys, true); window.addEventListener("keyup", this.cwKeys, true); window.addEventListener("mouseup", () => { this.cwHolding = false; }); }
      if (!this.cwLoop) { let prev = performance.now(); const loop = (now) => { if (!this.cwCanvas || !this.cwCanvas.isConnected || this.cgView !== "claw") { this.cwLoop = null; return; } const dt = Math.min(0.05, (now - prev) / 1000); prev = now; this.cwFrame(dt, now); this.cwLoop = requestAnimationFrame(loop); }; this.cwLoop = requestAnimationFrame(loop); }
    },
    cwFrame(dt, now) {
      const g = this.game, CW = CM.CW, tier = this.cwTier, L = g.cwLive && g.cwLive.tier === tier ? g.cwLive : null, M = g.cwMachine(tier), cv = this.cwCanvas, p = cv.getContext("2d"), fx = this.cwFx = this.cwFx || { falls: [] };
      if (L && L.stage !== "done") { const before = L.stage; L.input(this.cwHolding || this.cwKeyHold); L.update(dt); for (const e of L.events.splice(0)) this.cwEvent(e, now);
        if (L.stage !== before && (L.stage === "z" || L.stage === "drop")) { this.cgNote = L.stage === "z" ? "Now hold to send it back…" : "Down it goes…"; this.renderCasino(); return; }
        if (L.stage === "done") { const out = g.cwSettle(); this.cwOut = out; this.cwHolding = false; this.cwKeyHold = false;
          if (!out || !out.prize) { this.cgNote = "Nothing this time."; this.cgSfx("miss", 0.4); }
          else { this.cgNote = `${out.lucky ? "It slipped - right over the chute! " : ""}${LABEL[out.prize][0].toUpperCase() + LABEL[out.prize].slice(1)}${out.gold ? `: ${out.gold} gold` : out.card ? "" : ""}!`; this.cgSfx("cardwin", 0.5); if (out.gold) this.cgCoins(this.$("#casino-body"), 10); }
          this.renderCasino(); return; } }
      const [c1, c2] = FRAME[tier]; p.clearRect(0, 0, cv.width, cv.height);
      // the cabinet
      p.fillStyle = c2; p.fillRect(0, 0, cv.width, cv.height); p.fillStyle = c1; p.fillRect(6, 6, cv.width - 12, cv.height - 12);
      const back = p.createLinearGradient(0, CEIL, 0, FRONT); back.addColorStop(0, "#1A1030"); back.addColorStop(1, "#2A1A40"); p.fillStyle = back; p.fillRect(18, CEIL - 40, cv.width - 36, FRONT - CEIL + 48);
      for (let k = 0; k < 14; k++) { p.fillStyle = ["#FF6060", "#FFD060", "#60E0FF", "#C080FF"][k % 4]; p.globalAlpha = 0.5 + 0.5 * Math.abs(Math.sin(now / 300 + k)); p.beginPath(); p.arc(30 + k * ((cv.width - 60) / 13), 22, 4, 0, Math.PI * 2); p.fill(); } p.globalAlpha = 1;
      p.fillStyle = c2; p.font = "bold 13px Georgia, serif"; p.textAlign = "center"; p.fillText(CW.TIERS[tier].name.toUpperCase(), cv.width / 2, 46); p.textAlign = "left";
      // the floor in perspective, and the chute
      p.fillStyle = "#4A1A30"; p.beginPath(); p.moveTo(sx(0, 0), sy(0)); p.lineTo(sx(CW.W, 0), sy(0)); p.lineTo(sx(CW.W, CW.D), sy(CW.D)); p.lineTo(sx(0, CW.D), sy(CW.D)); p.closePath(); p.fill();
      p.strokeStyle = "rgba(255,255,255,0.06)"; for (let z = 1; z < CW.D; z++) { p.beginPath(); p.moveTo(sx(0, z), sy(z)); p.lineTo(sx(CW.W, z), sy(z)); p.stroke(); }
      p.fillStyle = "#0A0408"; p.beginPath(); p.moveTo(sx(0, 0), sy(0)); p.lineTo(sx(CW.CHUTE.x, 0), sy(0)); p.lineTo(sx(CW.CHUTE.x, CW.CHUTE.z), sy(CW.CHUTE.z)); p.lineTo(sx(0, CW.CHUTE.z), sy(CW.CHUTE.z)); p.closePath(); p.fill(); p.strokeStyle = c1; p.lineWidth = 2; p.stroke(); p.lineWidth = 1;
      p.fillStyle = "#FFE070"; p.font = "bold 10px monospace"; p.fillText("PRIZE", sx(0.25, 0.7), sy(0.7));
      // the claw's position and shadow
      const cx = L ? L.x : CW.home.x, cz = L ? L.z : CW.home.z, cy = L ? L.y : 1, open = L ? L.open : 1, held = L && L.held;
      p.fillStyle = "rgba(0,0,0,0.45)"; p.beginPath(); p.ellipse(sx(cx, cz), sy(cz), scale(cz) * 0.45, scale(cz) * 0.16, 0, 0, Math.PI * 2); p.fill(); p.strokeStyle = "rgba(255,240,180,0.55)"; p.beginPath(); p.ellipse(sx(cx, cz), sy(cz), scale(cz) * 0.45, scale(cz) * 0.16, 0, 0, Math.PI * 2); p.stroke();
      if (L && (L.stage === "x" || L.stage === "z")) { p.strokeStyle = "rgba(255,240,180,0.3)"; p.setLineDash([4, 5]); p.beginPath(); p.moveTo(sx(cx, cz), CEIL + 30); p.lineTo(sx(cx, cz), sy(cz)); p.stroke(); p.setLineDash([]); }
      // the prizes, back to front, the claw drawn in among them by depth
      const things = M.pit.filter((q) => q !== held).map((q) => ({ z: q.z, draw: () => this.cwPrize(p, q, sx(q.x, q.z), sy(q.z) - scale(q.z) * 0.32, scale(q.z) / 40, tier) }));
      things.push({ z: cz - 0.01, draw: () => this.cwClawDraw(p, cx, cz, cy, open, held, tier, now) });
      things.sort((a, b) => b.z - a.z).forEach((t) => t.draw());
      fx.falls = fx.falls.filter((f) => now - f.at < 600); for (const f of fx.falls) { const k = (now - f.at) / 600; p.globalAlpha = 1 - k; this.cwPrize(p, f.q, sx(f.q.x, f.q.z), sy(f.q.z) + k * 40, scale(f.q.z) / 40 * (1 - k * 0.5), tier); p.globalAlpha = 1; }
      { const sp = p.createRadialGradient(CWID / 2, CEIL, 10, CWID / 2, FRONT - 40, 260); sp.addColorStop(0, "rgba(255,240,200,0.12)"); sp.addColorStop(1, "rgba(255,240,200,0)"); p.fillStyle = sp; p.fillRect(18, CEIL, CWID - 36, FRONT - CEIL); }
      { const sw = ((now / 5200) % 1) * (CWID + 200) - 100; p.save(); p.globalAlpha = 0.08; p.fillStyle = "#FFFFFF"; p.beginPath(); p.moveTo(sw, 30); p.lineTo(sw + 40, 30); p.lineTo(sw - 60, FRONT); p.lineTo(sw - 100, FRONT); p.closePath(); p.fill(); p.restore(); }
      // the glass
      const gl = p.createLinearGradient(0, 0, cv.width, cv.height); gl.addColorStop(0, "rgba(255,255,255,0.08)"); gl.addColorStop(0.45, "rgba(255,255,255,0)"); gl.addColorStop(0.55, "rgba(255,255,255,0.05)"); gl.addColorStop(1, "rgba(255,255,255,0)"); p.fillStyle = gl; p.fillRect(18, 30, cv.width - 36, FRONT - 22);
      if (L && (L.stage === "x" || L.stage === "z")) { p.fillStyle = L.time < 5 ? "#FF6050" : "#FFE070"; p.font = "bold 16px monospace"; p.fillText(`${Math.ceil(L.time)}`, cv.width - 44, 46); }
      p.fillStyle = c2; p.fillRect(0, FRONT + 8, cv.width, cv.height - FRONT - 8); p.fillStyle = c1; p.fillRect(6, FRONT + 8, cv.width - 12, 4);
    },
    cwEvent(e, now) {
      const fx = this.cwFx;
      if (e.kind === "stopx" || e.kind === "stopz") this.cgSfx("bump", 0.3, 1.3); else if (e.kind === "timeup") this.cgSfx("tablebell", 0.3);
      else if (e.kind === "down") this.cgSfx("grind", 0.3, 1.6); else if (e.kind === "grab") this.cgSfx("card", 0.45, 0.8); else if (e.kind === "miss") this.cgSfx("card", 0.3, 1.5);
      else if (e.kind === "slip") { this.cgSfx("bump", 0.5, 0.8); } else if (e.kind === "chute") { fx.falls.push({ q: { ...e.prize }, at: now }); this.cgSfx("coin", 0.6); }
    },
    // the claw: a carriage on the rail, the cable, three prongs (open or closed), and what it holds
    cwClawDraw(p, x, z, y, open, held, tier, now) {
      const CW = CM.CW, X = sx(x, z), floorY = sy(z) - scale(z) * 0.3, top = CEIL - 10 + z * 2, Y = floorY - y * (floorY - top - 30), s = scale(z) / 40, [c1, c2] = FRAME[tier];
      p.strokeStyle = "#888"; p.lineWidth = 3; p.beginPath(); p.moveTo(30, top - 8); p.lineTo(CWID - 30, top - 8); p.stroke(); p.lineWidth = 1;
      p.fillStyle = c2; p.fillRect(X - 12 * s, top - 14, 24 * s, 12); p.strokeStyle = "#CCC"; p.beginPath(); p.moveTo(X, top - 2); p.lineTo(X, Y - 12 * s); p.stroke();
      if (held) this.cwPrize(p, held, X, Y + 16 * s, s, tier);
      p.fillStyle = c1; p.beginPath(); p.arc(X, Y - 10 * s, 8 * s, 0, Math.PI * 2); p.fill(); p.strokeStyle = c2; p.lineWidth = 3 * s;
      const spread = 6 + open * 10; for (const k of [-1, 0, 1]) { p.beginPath(); p.moveTo(X + k * 4 * s, Y - 6 * s); p.quadraticCurveTo(X + k * spread * s, Y + 6 * s, X + k * (spread - 6) * s, Y + 18 * s); p.stroke(); } p.lineWidth = 1;
    },
    // one prize, drawn round its centre at a given size
    cwPrize(p, q, X, Y, s, tier) {
      p.save(); p.translate(X, Y); p.scale(s, s); const k = q.kind;
      if (k === "pouch") { p.fillStyle = "#B08040"; p.beginPath(); p.moveTo(-14, 12); p.quadraticCurveTo(-18, -6, -6, -10); p.lineTo(6, -10); p.quadraticCurveTo(18, -6, 14, 12); p.closePath(); p.fill(); p.fillStyle = "#6A4A20"; p.fillRect(-8, -12, 16, 4); p.fillStyle = "#FFE070"; p.font = "bold 12px Georgia"; p.textAlign = "center"; p.fillText("G", 0, 6); p.textAlign = "left"; }
      else if (k === "hoard") { p.fillStyle = "#7A4A20"; p.fillRect(-18, -4, 36, 18); p.fillStyle = "#9A6A30"; p.beginPath(); p.ellipse(0, -4, 18, 9, 0, Math.PI, 0); p.fill(); p.fillStyle = "#F0C040"; p.fillRect(-18, -2, 36, 3); p.fillRect(-3, -2, 6, 8); for (let i = 0; i < 5; i++) { p.beginPath(); p.arc(-10 + i * 5, -12 + (i % 2) * 2, 3, 0, Math.PI * 2); p.fill(); } }
      else if (k === "card") { p.fillStyle = "rgba(200,230,255,0.35)"; p.beginPath(); p.arc(0, 0, 15, 0, Math.PI * 2); p.fill(); p.strokeStyle = "rgba(255,255,255,0.6)"; p.stroke(); p.save(); p.rotate(q.rot * 0.3 - 0.2); p.fillStyle = tier === "gold" ? "#F0D060" : tier === "silver" ? "#80C0F0" : "#E0D0B0"; p.fillRect(-7, -10, 14, 20); p.strokeStyle = "#3A2A10"; p.strokeRect(-7, -10, 14, 20); p.fillStyle = "#3A2A10"; p.fillRect(-4, -6, 8, 6); p.restore(); p.fillStyle = "rgba(255,255,255,0.5)"; p.beginPath(); p.arc(-5, -6, 4, 0, Math.PI * 2); p.fill(); }
      else if (k === "egg") { p.fillStyle = "#F0E8D0"; p.beginPath(); p.ellipse(0, 0, 12, 15, 0, 0, Math.PI * 2); p.fill(); p.fillStyle = ["#C060C0", "#60A0E0", "#E08040"][Math.floor(q.rot) % 3]; for (const [a, b] of [[-5, -6], [4, -2], [-3, 6], [6, 8]]) { p.beginPath(); p.arc(a, b, 2.5, 0, Math.PI * 2); p.fill(); } p.fillStyle = "#5A3A6A"; p.font = "bold 13px Georgia"; p.textAlign = "center"; p.fillText("?", 0, 5); p.textAlign = "left"; }
      else if (k === "weapon") { p.rotate(-0.7 + (q.rot % 1) * 0.4); p.fillStyle = "#D0D8E8"; p.beginPath(); p.moveTo(-3, -20); p.lineTo(0, -26); p.lineTo(3, -20); p.lineTo(3, 6); p.lineTo(-3, 6); p.closePath(); p.fill(); p.strokeStyle = "#7A8090"; p.stroke(); p.fillStyle = "#C0902A"; p.fillRect(-9, 6, 18, 4); p.fillStyle = "#6A3A1A"; p.fillRect(-2.5, 10, 5, 10); p.fillStyle = "#F0C040"; p.beginPath(); p.arc(0, 22, 3, 0, Math.PI * 2); p.fill(); }
      else if (k === "armor") { p.fillStyle = "#9AA0B0"; p.beginPath(); p.moveTo(-16, -12); p.lineTo(-6, -16); p.quadraticCurveTo(0, -10, 6, -16); p.lineTo(16, -12); p.lineTo(13, 4); p.quadraticCurveTo(0, 18, -13, 4); p.closePath(); p.fill(); p.strokeStyle = "#5A6070"; p.stroke(); p.beginPath(); p.moveTo(0, -11); p.lineTo(0, 10); p.stroke(); p.fillStyle = "#C0902A"; p.fillRect(-12, 0, 24, 3); }
      else if (k === "shield") { p.fillStyle = "#3A5AA0"; p.beginPath(); p.moveTo(-14, -14); p.lineTo(14, -14); p.lineTo(14, 0); p.quadraticCurveTo(14, 12, 0, 18); p.quadraticCurveTo(-14, 12, -14, 0); p.closePath(); p.fill(); p.strokeStyle = "#C0C8D8"; p.lineWidth = 2; p.stroke(); p.lineWidth = 1; p.fillStyle = "#F0C040"; p.fillRect(-2, -10, 4, 22); p.fillRect(-10, -2, 20, 4); }
      else if (k === "helm") { p.fillStyle = "#A0A8B8"; p.beginPath(); p.arc(0, 2, 14, Math.PI, 0); p.lineTo(14, 8); p.lineTo(-14, 8); p.closePath(); p.fill(); p.fillStyle = "#3A3A48"; p.fillRect(-9, 0, 18, 3); p.fillStyle = "#C03030"; p.beginPath(); p.moveTo(0, -12); p.quadraticCurveTo(10, -20, 14, -12); p.lineTo(2, -10); p.closePath(); p.fill(); }
      p.restore();
    },
  });
}
