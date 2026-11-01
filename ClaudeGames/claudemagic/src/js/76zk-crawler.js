"use strict";
// The Barrow Crawler, the window's side: the barrow's earthen floor in shadow, roots hanging from above, toadstools with
// spotted caps (shrinking as they are chipped, glowing faintly), the crawler's segments in banded carapace with legs
// that ripple, the head with mandibles and eyes; the gnome with a pointed hat and a wand, sparks from it; the spider all
// legs; bursts of green when a segment pops. Arrows or W A S D (or the mouse) to move, Space (or a click) to fire.
// The rules are 64zt-crawler.js.
CM.CG_TABLES.push(["crawler", "The Barrow Crawler"]);
{ const C = 16, BC = CM.BC;
  Object.assign(CM.ARC.reg.crawler, {
    ui: { W: BC.W * C, H: BC.H * C, scale: 1.1, frame: "#3A2A1A", start: "Into the barrow", go: "Level 1. Here it comes!", over: "The barrow goes quiet",
      lore: "Under the Joker's cellars the house broke into an old barrow, and something long lives in it. \"Keep it off the gnome,\" says the attendant, handing over a wand. \"It turns at every toadstool. It gets quicker.\"",
      help: "Arrows or W A S D (or the mouse over the barrow) to move about the bottom; Space or a click to fire one spark at a time. A head is 100, a segment 10, the spider up to 900 the closer it is. Hit segments become toadstools and split the crawler. One more life at 12,000.",
      keys: ["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight", "KeyW", "KeyA", "KeyS", "KeyD", "Space"] },
    input(L, H, ui) { const mx = (H.has("ArrowRight") || H.has("KeyD") ? 1 : 0) - (H.has("ArrowLeft") || H.has("KeyA") ? 1 : 0), my = (H.has("ArrowDown") || H.has("KeyS") ? 1 : 0) - (H.has("ArrowUp") || H.has("KeyW") ? 1 : 0);
      if (!mx && !my && ui.arcMouse && ui.arcMouseOn) { const tx = ui.arcMouse[0] / C, ty = ui.arcMouse[1] / C, dx = tx - L.p.x, dy = ty - L.p.y; L.input(Math.abs(dx) > 0.2 ? Math.sign(dx) * Math.min(1, Math.abs(dx)) : 0, Math.abs(dy) > 0.2 ? Math.sign(dy) * Math.min(1, Math.abs(dy)) : 0); } else L.input(mx, my);
      if (H.has("Space") || ui.arcMouseDown) L.fire(); if (mx || my) ui.arcMouseOn = false; },
    click(L, x, y, ui) { ui.arcMouseOn = true; L.fire(); },
    lifeIcon(p, x, y) { p.fillStyle = "#3060C0"; p.beginPath(); p.moveTo(x - 5, y + 5); p.lineTo(x, y - 6); p.lineTo(x + 5, y + 5); p.fill(); },
    event(ui, e, now, L, fx) {
      if (e.kind === "fire") ui.cgSfx("zap", 0.12, 2); else if (e.kind === "chip") ui.cgSfx("step", 0.12, 1.6); else if (e.kind === "pop") ui.arcBurst(fx, e.x * C + 8, e.y * C + 8, ["#E04030", "#F0E0D0"], 8, 80);
      else if (e.kind === "hit") { ui.cgSfx(e.head ? "shatter" : "card", 0.35, e.head ? 1.3 : 1.7); ui.arcBurst(fx, e.x * C + 8, e.y * C + 8, ["#80E060", "#40A030", "#FFFFFF"], e.head ? 16 : 9, 120); if (e.head) ui.arcPts(fx, e.x * C + 8, e.y * C, e.pts); }
      else if (e.kind === "spider") { ui.cgSfx("cardwin", 0.4); ui.arcBurst(fx, e.x * C, e.y * C, ["#A060E0", "#FFFFFF"], 18, 150); ui.arcPts(fx, e.x * C, e.y * C - 8, e.pts, "#E0B0FF"); }
      else if (e.kind === "spidercome") ui.cgSfx("monster", 0.2, 1.8); else if (e.kind === "die") { ui.cgSfx("hurt", 0.6); fx.shake = 0.3; ui.arcBurst(fx, e.x * C, e.y * C, ["#3060C0", "#F0C8A0", "#FFE070"], 24, 170); } else if (e.kind === "extra") ui.cgSfx("cardwin", 0.4);
    },
    draw(p, L, now) {
      const W = BC.W * C, H = BC.H * C, bg = p.createLinearGradient(0, 0, 0, H); bg.addColorStop(0, "#140C08"); bg.addColorStop(1, "#2A1C12"); p.fillStyle = bg; p.fillRect(0, 0, W, H);
      for (let k = 0; k < 60; k++) { p.fillStyle = k % 3 ? "rgba(0,0,0,0.25)" : "rgba(200,160,100,0.06)"; p.fillRect((k * 97) % W, (k * 53) % H, 3 + (k % 4), 2); }
      p.strokeStyle = "rgba(120,90,50,0.5)"; p.lineWidth = 1.5; for (let k = 0; k < 9; k++) { const x0 = (k * 61 + 20) % W; p.beginPath(); p.moveTo(x0, 0); let x = x0; for (let y = 0; y < 20 + (k % 3) * 12; y += 4) { x += Math.sin(y / 4 + k + now / 1500) * 1.5; p.lineTo(x, y); } p.stroke(); } p.lineWidth = 1;
      p.fillStyle = "rgba(90,120,200,0.06)"; p.fillRect(0, BC.zone * C, W, H - BC.zone * C); p.strokeStyle = "rgba(140,170,255,0.15)"; p.setLineDash([4, 6]); p.beginPath(); p.moveTo(0, BC.zone * C); p.lineTo(W, BC.zone * C); p.stroke(); p.setLineDash([]);
      if (!L) return;
      for (const [k, h] of L.mush) { const [x, y] = k.split(",").map(Number), X = x * C + 8, Y = y * C + 9, s = 0.55 + h * 0.15; p.fillStyle = "#E8D8C0"; p.fillRect(X - 2 * s, Y, 4 * s, 6 * s); p.save(); p.shadowColor = "rgba(255,90,60,0.6)"; p.shadowBlur = 4; p.fillStyle = "#C83828"; p.beginPath(); p.arc(X, Y, 7 * s, Math.PI, 0); p.fill(); p.restore(); p.fillStyle = "#F8E8D8"; p.fillRect(X - 4 * s, Y - 4 * s, 2, 2); p.fillRect(X + 2 * s, Y - 5 * s, 2, 2); }
      for (const s of L.segs) { const X = s.fx * C + 8, Y = s.fy * C + 8, leg = Math.sin(now / 60 + s.id) * 2; p.strokeStyle = "#5A3A10"; p.lineWidth = 1.5; for (const o of [-4, 0, 4]) { p.beginPath(); p.moveTo(X + o, Y); p.lineTo(X + o + leg, Y + 8); p.moveTo(X + o, Y); p.lineTo(X + o - leg, Y - 8); p.stroke(); } p.lineWidth = 1;
        const gr = p.createRadialGradient(X - 2, Y - 2, 1, X, Y, 8); gr.addColorStop(0, s.head ? "#F0D060" : "#B0E070"); gr.addColorStop(1, s.head ? "#A06010" : "#4A8020"); p.fillStyle = gr; p.beginPath(); p.arc(X, Y, 7.5, 0, Math.PI * 2); p.fill(); p.strokeStyle = "rgba(0,0,0,0.35)"; p.beginPath(); p.arc(X, Y, 4.5, 0, Math.PI * 2); p.stroke();
        if (s.head) { p.fillStyle = "#FFF"; p.fillRect(X + s.dir * 2 - 1, Y - 4, 3, 3); p.fillRect(X + s.dir * 2 - 1, Y + 1, 3, 3); p.strokeStyle = "#3A2008"; p.beginPath(); p.moveTo(X + s.dir * 6, Y - 3); p.lineTo(X + s.dir * 10, Y - 1); p.moveTo(X + s.dir * 6, Y + 3); p.lineTo(X + s.dir * 10, Y + 1); p.stroke(); } }
      if (L.spider) { const S = L.spider, X = S.x * C, Y = S.y * C; p.strokeStyle = "#3A2050"; p.lineWidth = 2; for (let k = 0; k < 4; k++) { const a = Math.sin(now / 50 + k) * 0.4; for (const sd of [-1, 1]) { p.beginPath(); p.moveTo(X, Y); p.lineTo(X + sd * (8 + k * 2), Y - 6 + k * 4 + a * 4); p.lineTo(X + sd * (12 + k * 2), Y + 2 + k * 4); p.stroke(); } } p.lineWidth = 1; p.fillStyle = "#7040A0"; p.beginPath(); p.ellipse(X, Y, 8, 6, 0, 0, Math.PI * 2); p.fill(); p.fillStyle = "#FF4040"; p.fillRect(X - 3, Y - 2, 2, 2); p.fillRect(X + 1, Y - 2, 2, 2); }
      if (L.bolt) { p.save(); p.shadowColor = "#80F0FF"; p.shadowBlur = 8; p.fillStyle = "#C0F8FF"; p.fillRect(L.bolt.x * C - 1.5, L.bolt.y * C - 6, 3, 10); p.restore(); }
      const P = L.p; if (!P.dead || Math.floor(now / 100) % 2) { const X = P.x * C, Y = P.y * C; p.fillStyle = "rgba(0,0,0,0.3)"; p.beginPath(); p.ellipse(X, Y + 8, 7, 2, 0, 0, Math.PI * 2); p.fill(); p.fillStyle = "#6A4A2A"; p.fillRect(X - 5, Y + 1, 10, 7); p.fillStyle = "#F0C8A0"; p.beginPath(); p.arc(X, Y - 1, 4, 0, Math.PI * 2); p.fill(); p.fillStyle = "#3060C0"; p.beginPath(); p.moveTo(X - 6, Y - 2); p.lineTo(X, Y - 14); p.lineTo(X + 6, Y - 2); p.fill(); p.fillStyle = "#F0F0F0"; p.fillRect(X - 3, Y + 1, 6, 3); p.strokeStyle = "#8A5A20"; p.lineWidth = 2; p.beginPath(); p.moveTo(X + 6, Y + 4); p.lineTo(X + 6, Y - 6); p.stroke(); p.lineWidth = 1; p.fillStyle = "#A0F0FF"; p.fillRect(X + 5, Y - 9, 3, 3); }
    },
  });
}
