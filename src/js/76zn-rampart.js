"use strict";
// The Rampart Battery, the window's side: the night over the town - a deep sky with stars and a low moon, the hills,
// the town wall and its six cottages (lit windows, chimneys smoking), the three mana wells glowing (their charges as
// pips beneath, dark once struck); embers as falling sparks with smoke trails, bolts as thin streaks of blue light,
// the bursts as rings of white and blue swelling and fading; the fire-drake flapping across; a cottage burning when
// struck. The crosshair follows the mouse. Click to loose a bolt; the arrows move the crosshair and Space looses too.
// The rules are 64zw-rampart.js.
CM.CG_TABLES.push(["rampart", "The Rampart Battery"]);
{ const RB = CM.RB;
  Object.assign(CM.ARC.reg.rampart, {
    ui: { W: RB.W, H: RB.H, scale: 1, frame: "#1A2030", start: "To the rampart", go: "Wave 1. Hold the wall!", over: "The last cottage burns", levelWord: "Wave",
      lore: "When the Joker's town has a bad night, embers fall out of the sky. The house keeps three mana wells on the wall to put them out, and pays anyone who will man them. \"Mind the cottages,\" says the watch-captain. \"The house rents them.\"",
      help: "Move the mouse and click (or the arrows and Space) to loose a bolt from the nearest well that has charges; it bursts where you aimed and puts out every ember in the ring. Each well holds ten charges a wave (the middle one fires fastest). At the end of a wave each charge left pays 5 and each cottage 100, more each wave. A lost cottage comes back every 10,000. The game ends when the last one burns.",
      keys: ["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight", "Space"],
      extraHud(p, L, W) { for (let i = 0; i < 6; i++) { p.fillStyle = L.cottages[i] ? "#F0C060" : "#3A3030"; p.fillRect(W - 100 + i * 15, 9, 10, 10); } } },
    input(L, H, ui) { const mx = (H.has("ArrowRight") ? 1 : 0) - (H.has("ArrowLeft") ? 1 : 0), my = (H.has("ArrowDown") ? 1 : 0) - (H.has("ArrowUp") ? 1 : 0); const A = ui.rbAim = ui.rbAim || [RB.W / 2, RB.H / 2];
      if (mx || my) { A[0] = CM.ARC.clamp(A[0] + mx * 300 / 60, 0, RB.W); A[1] = CM.ARC.clamp(A[1] + my * 300 / 60, 0, RB.ground - 30); ui.rbKeys = true; } else if (ui.arcMouse && !ui.rbKeys) { A[0] = ui.arcMouse[0]; A[1] = ui.arcMouse[1]; } },
    press(L, code, ui) { if (code === "Space") { const A = ui.rbAim || [RB.W / 2, 200]; L.fire(A[0], A[1]); } },
    click(L, x, y, ui) { ui.rbKeys = false; ui.rbAim = [x, y]; L.fire(x, y); },
    event(ui, e, now, L, fx) {
      if (e.kind === "fire") ui.cgSfx("zap", 0.18, 1.7); else if (e.kind === "empty") ui.cgSfx("miss", 0.25); else if (e.kind === "burst") ui.cgSfx("spell", 0.18, 1.9);
      else if (e.kind === "out") { ui.arcBurst(fx, e.x, e.y, ["#FFB040", "#FFFFFF"], 5, 60, 40); } else if (e.kind === "drake") ui.cgSfx("monster", 0.35, 0.8); else if (e.kind === "drakedown") { ui.cgSfx("cardwin", 0.4); ui.arcBurst(fx, e.x, e.y, ["#C04020", "#FFE070"], 24, 160); ui.arcPts(fx, e.x, e.y - 10, e.pts); }
      else if (e.kind === "burn") { ui.cgSfx(e.home ? "slam" : "hurt", 0.5, 0.8); fx.shake = 0.25; ui.arcBurst(fx, e.x, RB.ground - 10, ["#FF6020", "#FFB040", "#3A3030"], 26, 150); } else if (e.kind === "thud") ui.arcBurst(fx, e.x, RB.ground, ["#6A4A3A", "#FF8040"], 6, 60);
      else if (e.kind === "held") { ui.cgNote = `Wave held: ${e.charges} charges and ${e.homes} cottages left - ${e.pts} points.`; } else if (e.kind === "rebuild") ui.cgSfx("cardwin", 0.4);
    },
    draw(p, L, now) {
      const W = RB.W, H = RB.H, G = RB.ground, sky = p.createLinearGradient(0, 0, 0, H); sky.addColorStop(0, "#060818"); sky.addColorStop(0.7, "#1A1A3A"); sky.addColorStop(1, "#3A2030"); p.fillStyle = sky; p.fillRect(0, 0, W, H);
      for (let k = 0; k < 70; k++) { p.globalAlpha = 0.3 + 0.5 * Math.abs(Math.sin(now / 700 + k * 2.1)); p.fillStyle = "#FFF"; p.fillRect((k * 131) % W, (k * 37) % (G - 120), 1.5, 1.5); } p.globalAlpha = 1;
      p.fillStyle = "#F0E8D0"; p.beginPath(); p.arc(W - 70, 70, 20, 0, Math.PI * 2); p.fill(); p.fillStyle = "rgba(240,232,208,0.1)"; p.beginPath(); p.arc(W - 70, 70, 34, 0, Math.PI * 2); p.fill();
      p.fillStyle = "#14142A"; p.beginPath(); p.moveTo(0, G - 40); for (let x = 0; x <= W; x += 40) p.lineTo(x, G - 40 - 20 * Math.abs(Math.sin(x / 90))); p.lineTo(W, G); p.lineTo(0, G); p.fill();
      p.fillStyle = "#3A3440"; p.fillRect(0, G, W, H - G); for (let x = 0; x < W; x += 16) { p.fillStyle = "#4A4450"; p.fillRect(x + 1, G + 3, 14, 7); p.fillRect(x + 9, G + 13, 14, 7); } for (let x = 0; x < W; x += 24) { p.fillStyle = "#3A3440"; p.fillRect(x, G - 6, 12, 6); }
      if (!L) return;
      // cottages
      L.homes.forEach((x, i) => { const up = L.cottages[i]; if (up) { p.fillStyle = "#6A5040"; p.fillRect(x - 12, G - 22, 24, 16); p.fillStyle = "#8A3A2A"; p.beginPath(); p.moveTo(x - 15, G - 22); p.lineTo(x, G - 34); p.lineTo(x + 15, G - 22); p.fill(); p.fillStyle = "#4A4040"; p.fillRect(x + 6, G - 34, 4, 8); p.fillStyle = Math.sin(now / 400 + i) > -0.8 ? "#FFD070" : "#C09040"; p.fillRect(x - 7, G - 17, 5, 5); p.fillRect(x + 2, G - 17, 5, 5);
          p.fillStyle = "rgba(180,180,190,0.25)"; for (let k = 0; k < 3; k++) { const t = ((now / 1500 + k / 3 + i * 0.17) % 1); p.beginPath(); p.arc(x + 8 + t * 8, G - 36 - t * 30, 2 + t * 4, 0, Math.PI * 2); p.fill(); } }
        else { p.fillStyle = "#2A2020"; p.fillRect(x - 12, G - 10, 24, 4); for (let k = 0; k < 3; k++) { p.fillStyle = k % 2 ? "#FF7020" : "#FFB040"; const f = Math.sin(now / 70 + k + i) * 3; p.beginPath(); p.moveTo(x - 8 + k * 7, G - 6); p.quadraticCurveTo(x - 6 + k * 7, G - 18 - f, x - 3 + k * 7, G - 6); p.fill(); } } });
      // wells
      L.wells.forEach((w) => { p.fillStyle = "#5A5464"; p.fillRect(w.x - 14, G - 14, 28, 14); if (!w.dark) { const gl = p.createRadialGradient(w.x, G - 16, 2, w.x, G - 16, 26); gl.addColorStop(0, "rgba(120,200,255,0.6)"); gl.addColorStop(1, "rgba(120,200,255,0)"); p.fillStyle = gl; p.fillRect(w.x - 26, G - 42, 52, 52); p.fillStyle = "#A0E0FF"; p.beginPath(); p.ellipse(w.x, G - 14, 10, 3, 0, 0, Math.PI * 2); p.fill(); }
        for (let k = 0; k < RB.charges; k++) { p.fillStyle = k < w.n ? "#A0E0FF" : "#2A2A3A"; p.fillRect(w.x - 14 + (k % 5) * 6, G + 6 + Math.floor(k / 5) * 6, 4, 4); } });
      for (const e of L.embers) { const tg = p.createLinearGradient(e.x0, e.y0, e.x, e.y); tg.addColorStop(0, "rgba(180,120,90,0)"); tg.addColorStop(1, "rgba(255,140,60,0.55)"); p.strokeStyle = tg; p.lineWidth = 2; p.beginPath(); p.moveTo(e.x0, e.y0); p.lineTo(e.x, e.y); p.stroke(); p.lineWidth = 1; p.save(); p.shadowColor = "#FF8030"; p.shadowBlur = 8; p.fillStyle = "#FFE0A0"; p.beginPath(); p.arc(e.x, e.y, 2.5, 0, Math.PI * 2); p.fill(); p.restore(); }
      for (const b of L.bolts) { p.strokeStyle = "rgba(140,220,255,0.8)"; p.lineWidth = 1.5; p.beginPath(); p.moveTo(b.x0, b.y0); p.lineTo(b.x, b.y); p.stroke(); p.lineWidth = 1; p.strokeStyle = "rgba(255,255,255,0.5)"; p.beginPath(); p.moveTo(b.tx - 4, b.ty - 4); p.lineTo(b.tx + 4, b.ty + 4); p.moveTo(b.tx + 4, b.ty - 4); p.lineTo(b.tx - 4, b.ty + 4); p.stroke(); }
      for (const B of L.bursts) { const g = p.createRadialGradient(B.x, B.y, 0, B.x, B.y, Math.max(1, B.r)); g.addColorStop(0, "rgba(255,255,255,0.95)"); g.addColorStop(0.6, "rgba(140,210,255,0.6)"); g.addColorStop(1, "rgba(80,140,255,0)"); p.fillStyle = g; p.beginPath(); p.arc(B.x, B.y, B.r, 0, Math.PI * 2); p.fill(); }
      if (L.drake) { const D = L.drake, fl = Math.sin(now / 80) * 8, s = D.vx > 0 ? 1 : -1; p.save(); p.translate(D.x, D.y); p.scale(s, 1); p.fillStyle = "#802818"; p.beginPath(); p.ellipse(0, 0, 14, 5, 0, 0, Math.PI * 2); p.fill(); p.beginPath(); p.moveTo(-4, -2); p.lineTo(-10, -12 - fl); p.lineTo(6, -2); p.fill(); p.beginPath(); p.moveTo(12, -2); p.lineTo(20, -5); p.lineTo(14, 2); p.fill(); p.fillStyle = "#FFE040"; p.fillRect(15, -4, 2, 2); p.restore(); }
      const A = this.aimOf(); if (A) { p.strokeStyle = "rgba(255,255,255,0.8)"; p.beginPath(); p.arc(A[0], A[1], 8, 0, Math.PI * 2); p.moveTo(A[0] - 13, A[1]); p.lineTo(A[0] - 4, A[1]); p.moveTo(A[0] + 4, A[1]); p.lineTo(A[0] + 13, A[1]); p.moveTo(A[0], A[1] - 13); p.lineTo(A[0], A[1] - 4); p.moveTo(A[0], A[1] + 4); p.lineTo(A[0], A[1] + 13); p.stroke(); }
    },
    aimOf() { return CM.ui && CM.ui.rbAim; },
  });
}
