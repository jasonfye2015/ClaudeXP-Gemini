"use strict";
// Glimmerpop, the window's side: the inside of a great glass still - a copper ceiling plate that comes down with chains,
// bubbles of coloured glimmer with a shine and a soft inner glow (each colour its own rune so they read without colour),
// a dotted aiming line that bounces off the walls, the brass launcher and the next bubble beside it, rings of light
// where bubbles pop and the loose ones tumbling away, the danger line glowing as they near it. The mouse aims and a
// click shoots; Left and Right aim and Space shoots too. The rules are 64zx-glimmerpop.js.
CM.CG_TABLES.push(["glimmerpop", "Glimmerpop"]);
{ const GP = CM.GP, COL = [["#E04050", "♥"], ["#40A0F0", "◆"], ["#50C060", "♣"], ["#F0C030", "★"], ["#B060E0", "●"], ["#F08030", "▲"], ["#E0E0F0", "✦"]];
  Object.assign(CM.ARC.reg.glimmerpop, {
    ui: { W: Math.round(GP.W), H: Math.round(GP.H), scale: 1.1, frame: "#5A3A18", start: "Light the still", go: "Level 1. Pop them all!",
      lore: "In the alchemist's corner a great glass still bubbles over with glimmer, and the house pays to have it cleared. \"Three of a colour and they pop,\" says the alchemist. \"Knock out what holds the rest and they all fall. Don't let it reach the spout.\"",
      help: "Aim with the mouse and click to shoot (or Left and Right to aim, Space to shoot). Shots bounce off the walls. Three or more of one colour joined pop; anything left hanging falls for a bonus that doubles with each one. The ceiling comes down every few shots. If the glimmer reaches the line, a life is lost.",
      keys: ["ArrowLeft", "ArrowRight", "Space", "KeyA", "KeyD"] },
    input(L, H, ui) { const t = (H.has("ArrowRight") || H.has("KeyD") ? 1 : 0) - (H.has("ArrowLeft") || H.has("KeyA") ? 1 : 0); if (t) { L.setAim(L.aim + t * 0.03); ui.gpKeys = true; } else if (ui.arcMouse && !ui.gpKeys) { const [mx, my] = ui.arcMouse; L.setAim(Math.atan2(Math.min(my, GP.H - 40) - (GP.H - 30), mx - GP.W / 2)); } },
    press(L, code) { if (code === "Space") L.shoot(); },
    click(L, x, y, ui) { ui.gpKeys = false; L.setAim(Math.atan2(Math.min(y, GP.H - 40) - (GP.H - 30), x - GP.W / 2)); L.shoot(); },
    event(ui, e, now, L, fx) {
      if (e.kind === "shoot") ui.cgSfx("zap", 0.2, 1.6); else if (e.kind === "wall") ui.cgSfx("step", 0.1, 2); else if (e.kind === "stick") ui.cgSfx("bump", 0.2, 1.4);
      else if (e.kind === "pop") { (this.rings = this.rings || []).push({ x: e.x, y: e.y, at: now, c: COL[e.k][0] }); ui.arcBurst(fx, e.x, e.y, [COL[e.k][0], "#FFFFFF"], 6, 100); }
      else if (e.kind === "score") { ui.cgSfx(e.dropped ? "cardwin" : "coin", 0.4, e.dropped ? 1 : 1.5); ui.arcPts(fx, e.x, e.y - 10, e.pts, e.dropped ? "#FFE070" : "#FFF0B0"); }
      else if (e.kind === "lower") { ui.cgSfx("grind", 0.4, 0.7); fx.shake = 0.12; } else if (e.kind === "die") { ui.cgSfx("hurt", 0.55); fx.shake = 0.35; }
    },
    bubble(p, x, y, k, now, r = GP.R) { const [c, rune] = COL[k]; const g = p.createRadialGradient(x - r * 0.35, y - r * 0.4, 1, x, y, r); g.addColorStop(0, "#FFFFFF"); g.addColorStop(0.25, c); g.addColorStop(1, "rgba(0,0,0,0.55)"); p.fillStyle = g; p.beginPath(); p.arc(x, y, r - 1, 0, Math.PI * 2); p.fill();
      p.fillStyle = "rgba(255,255,255,0.75)"; p.font = `bold ${Math.round(r * 0.8)}px Georgia`; p.textAlign = "center"; p.fillText(rune, x, y + r * 0.3); p.textAlign = "left"; p.strokeStyle = "rgba(255,255,255,0.25)"; p.beginPath(); p.arc(x, y, r - 1.5, 0, Math.PI * 2); p.stroke(); void now; },
    draw(p, L, now) {
      const W = GP.W, H = GP.H, bg = p.createLinearGradient(0, 0, 0, H); bg.addColorStop(0, "#1A2830"); bg.addColorStop(1, "#0A1014"); p.fillStyle = bg; p.fillRect(0, 0, W, H);
      p.fillStyle = "rgba(160,220,255,0.05)"; for (let k = 0; k < 6; k++) { const y = ((now / 40 + k * 90) % H); p.beginPath(); p.arc(20 + (k * 71) % (W - 40), H - y, 3 + k % 3, 0, Math.PI * 2); p.fill(); }
      p.fillStyle = "rgba(255,255,255,0.05)"; p.fillRect(8, 0, 6, H); p.fillRect(W - 14, 0, 4, H);
      if (!L) return;
      // the ceiling plate
      p.fillStyle = "#8A5A2A"; p.fillRect(0, L.top - 10, W, 10); p.fillStyle = "#C88A40"; p.fillRect(0, L.top - 10, W, 3); p.strokeStyle = "#6A6A70"; for (let x = 30; x < W; x += 80) { p.beginPath(); p.moveTo(x, 0); p.lineTo(x, L.top - 10); p.stroke(); }
      // the line
      const near = L.grid.some((row, r) => row.some((v, c) => v >= 0 && GP.pos(r, c, L.top)[1] + GP.R * 4 > GP.line)); p.strokeStyle = near ? `rgba(255,80,60,${0.5 + 0.4 * Math.sin(now / 100)})` : "rgba(255,200,120,0.3)"; p.setLineDash([8, 6]); p.beginPath(); p.moveTo(0, GP.line); p.lineTo(W, GP.line); p.stroke(); p.setLineDash([]);
      for (let r = 0; r < GP.ROWS; r++) for (let c = 0; c < L.cols(r); c++) { const k = L.grid[r][c]; if (k < 0) continue; const [x, y] = GP.pos(r, c, L.top), wob = L.dead ? Math.sin(now / 40 + r + c) * 2 : 0; this.bubble(p, x + wob, y, k, now); }
      for (const f of L.falling) this.bubble(p, f.x, f.y, f.k, now);
      this.rings = (this.rings || []).filter((q) => now - q.at < 350); for (const q of this.rings) { const t = (now - q.at) / 350; p.strokeStyle = q.c; p.globalAlpha = 1 - t; p.lineWidth = 3; p.beginPath(); p.arc(q.x, q.y, GP.R * (1 + t), 0, Math.PI * 2); p.stroke(); } p.globalAlpha = 1; p.lineWidth = 1;
      // the aim, bounced
      if (!L.ball && !L.dead) { let x = W / 2, y = H - 30, vx = Math.cos(L.aim), vy = Math.sin(L.aim); p.fillStyle = "rgba(255,255,255,0.55)"; for (let k = 0; k < 60; k++) { x += vx * 9; y += vy * 9; if (x < GP.R || x > W - GP.R) { vx = -vx; x = CM.ARC.clamp(x, GP.R, W - GP.R); } if (y < L.top + GP.R) break; if (k % 2 === 0) { p.beginPath(); p.arc(x, y, 1.6, 0, Math.PI * 2); p.fill(); } } }
      if (L.ball) this.bubble(p, L.ball.x, L.ball.y, L.ball.k, now);
      // the launcher
      p.save(); p.translate(W / 2, H - 30); p.rotate(L.aim + Math.PI / 2); p.fillStyle = "#B08840"; p.fillRect(-6, -34, 12, 30); p.fillStyle = "#E0B860"; p.fillRect(-6, -34, 12, 4); p.restore();
      p.fillStyle = "#6A4A28"; p.beginPath(); p.arc(W / 2, H - 22, 22, Math.PI, 0); p.fill(); if (!L.ball) this.bubble(p, W / 2, H - 30, L.cur, now, GP.R * 0.95);
      p.fillStyle = "#E0D0B0"; p.font = "10px Georgia"; p.fillText("next", W / 2 + 40, H - 34); this.bubble(p, W / 2 + 52, H - 18, L.next, now, GP.R * 0.7);
      p.fillStyle = "#C0D8E0"; p.font = "bold 11px monospace"; p.fillText(`DROP IN ${L.every - (L.shots % L.every)}`, 8, H - 8);
    },
  });
}
