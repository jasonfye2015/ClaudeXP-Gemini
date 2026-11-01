"use strict";
// The Wyrm's Feast, the window's side: a walled garden bed of checkered grass with the moss on its stone wall, standing
// stones with lichen, berries that pulse with a glow, the golden one ringed and blinking as it fades; the wyrm in green
// scales darkening to the tail, its head with eyes and a flicking tongue, sliding smoothly between squares; a burst of
// juice for each berry. Arrows or W A S D to turn. The rules are 64zs-wyrm.js.
CM.CG_TABLES.push(["wyrm", "The Wyrm's Feast"]);
{ const C = 20, WY = CM.WY;
  Object.assign(CM.ARC.reg.wyrm, {
    ui: { W: WY.W * C, H: WY.H * C, scale: 1.1, frame: "#2A4A20", start: "Into the garden", go: "Level 1. Feast!", over: "The wyrm curls up to sleep",
      lore: "A walled bed in the Joker's kitchen garden, and in it a young wyrm with an appetite. \"Feed it glimmer berries,\" says the gardener. \"It grows. It gets quick. It does not like walls.\"",
      help: "Arrows or W A S D to turn (it will not turn straight back on itself). Eat the level's berries to clear it; a golden berry is worth five; walls, stones and the wyrm itself cost a life.",
      keys: ["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight", "KeyW", "KeyA", "KeyS", "KeyD"] },
    press(L, code) { const d = { ArrowUp: [0, -1], KeyW: [0, -1], ArrowDown: [0, 1], KeyS: [0, 1], ArrowLeft: [-1, 0], KeyA: [-1, 0], ArrowRight: [1, 0], KeyD: [1, 0] }[code]; if (d) L.turn(...d); },
    lifeIcon(p, x, y) { p.fillStyle = "#5AC060"; p.beginPath(); p.arc(x, y, 5, 0, Math.PI * 2); p.fill(); p.fillStyle = "#101010"; p.fillRect(x + 1, y - 2, 2, 2); },
    event(ui, e, now, L, fx) {
      if (e.kind === "eat") { ui.cgSfx("coin", 0.3, 1.2 + Math.min(1, L.eaten / L.need)); ui.arcBurst(fx, e.x * C + C / 2, e.y * C + C / 2, ["#E04060", "#FF90A0", "#FFFFFF"], 12, 110); ui.arcPts(fx, e.x * C + C / 2, e.y * C, e.pts); }
      else if (e.kind === "gold") { ui.cgSfx("cardwin", 0.4); ui.arcBurst(fx, e.x * C + C / 2, e.y * C + C / 2, ["#FFE070", "#FFF8C0"], 20, 150); ui.arcPts(fx, e.x * C + C / 2, e.y * C, e.pts, "#FFE070"); }
      else if (e.kind === "goldshow") ui.cgSfx("spell", 0.25, 1.6); else if (e.kind === "die") { ui.cgSfx("hurt", 0.55); fx.shake = 0.25; ui.arcBurst(fx, e.x * C + C / 2, e.y * C + C / 2, ["#5AC060", "#2A7A30", "#FFFFFF"], 22, 160); }
    },
    draw(p, L, now) {
      const W = WY.W * C, H = WY.H * C; for (let y = 0; y < WY.H; y++) for (let x = 0; x < WY.W; x++) { p.fillStyle = (x + y) % 2 ? "#3A7A2E" : "#438834"; p.fillRect(x * C, y * C, C, C); if ((x * 7 + y * 13) % 9 === 0) { p.fillStyle = "#56A040"; p.fillRect(x * C + 6, y * C + 10, 2, 5); p.fillRect(x * C + 10, y * C + 8, 2, 6); } }
      p.strokeStyle = "#7A7068"; p.lineWidth = 6; p.strokeRect(3, 3, W - 6, H - 6); p.strokeStyle = "#5A8A40"; p.lineWidth = 2; p.setLineDash([6, 10]); p.strokeRect(3, 3, W - 6, H - 6); p.setLineDash([]); p.lineWidth = 1;
      if (!L) return;
      for (const k of L.stones) { const [x, y] = k.split(",").map(Number), X = x * C, Y = y * C; p.fillStyle = "rgba(0,0,0,0.3)"; p.beginPath(); p.ellipse(X + 11, Y + 17, 9, 3, 0, 0, Math.PI * 2); p.fill(); p.fillStyle = "#8A847C"; p.beginPath(); p.moveTo(X + 3, Y + 17); p.lineTo(X + 5, Y + 3); p.lineTo(X + 15, Y + 2); p.lineTo(X + 17, Y + 17); p.fill(); p.fillStyle = "#9AB060"; p.fillRect(X + 6, Y + 5, 4, 3); p.fillStyle = "#A8A29A"; p.fillRect(X + 7, Y + 8, 2, 7); }
      const pulse = 1 + 0.12 * Math.sin(now / 160), [bx, by] = L.berry; p.save(); p.shadowColor = "#FF5070"; p.shadowBlur = 10; p.fillStyle = "#D02848"; p.beginPath(); p.arc(bx * C + C / 2, by * C + C / 2 + 1, 6 * pulse, 0, Math.PI * 2); p.fill(); p.restore(); p.fillStyle = "#FFB0C0"; p.fillRect(bx * C + 7, by * C + 7, 3, 3); p.fillStyle = "#3A8A30"; p.fillRect(bx * C + 10, by * C + 2, 2, 4);
      if (L.gold) { const G = L.gold, blink = G.t < 2 && Math.floor(now / 120) % 2; if (!blink) { p.save(); p.shadowColor = "#FFE070"; p.shadowBlur = 14; p.fillStyle = "#F0C030"; p.beginPath(); p.arc(G.x * C + C / 2, G.y * C + C / 2, 7, 0, Math.PI * 2); p.fill(); p.restore(); p.strokeStyle = "#FFF4B0"; p.beginPath(); p.arc(G.x * C + C / 2, G.y * C + C / 2, 9 + 2 * Math.sin(now / 100), 0, Math.PI * 2); p.stroke(); } }
      // the wyrm, slid between squares by how far the step has gone
      const k = L.dead ? 1 : Math.min(1, L.acc / L.tick), n = L.body.length, flick = L.dead && Math.floor(now / 100) % 2;
      for (let i = n - 1; i >= 0; i--) { const [x, y] = L.body[i], prev = L.body[i + 1] || L.body[i], X = (prev[0] + (x - prev[0]) * k) * C + C / 2, Y = (prev[1] + (y - prev[1]) * k) * C + C / 2, f = i / Math.max(1, n - 1), r = C * (0.48 - f * 0.18);
        if (flick) continue; const gr = p.createRadialGradient(X - 3, Y - 3, 1, X, Y, r); gr.addColorStop(0, `hsl(${110 - f * 30},60%,${58 - f * 18}%)`); gr.addColorStop(1, `hsl(${110 - f * 30},55%,${32 - f * 12}%)`); p.fillStyle = gr; p.beginPath(); p.arc(X, Y, r, 0, Math.PI * 2); p.fill();
        if (i % 2 === 0 && i) { p.fillStyle = "rgba(255,240,150,0.35)"; p.beginPath(); p.arc(X, Y, r * 0.35, 0, Math.PI * 2); p.fill(); }
        if (i === 0) { const [ex, ey] = L.dir, sx = -ey, sy = ex; p.fillStyle = "#FFF"; for (const s of [-1, 1]) { p.beginPath(); p.arc(X + ex * 3 + sx * 4 * s, Y + ey * 3 + sy * 4 * s, 2.6, 0, Math.PI * 2); p.fill(); } p.fillStyle = "#101010"; for (const s of [-1, 1]) p.fillRect(X + ex * 4 + sx * 4 * s - 1, Y + ey * 4 + sy * 4 * s - 1, 2, 2);
          if (Math.floor(now / 300) % 3 === 0) { p.strokeStyle = "#E03040"; p.lineWidth = 1.5; p.beginPath(); p.moveTo(X + ex * 9, Y + ey * 9); p.lineTo(X + ex * 14, Y + ey * 14); p.lineTo(X + ex * 16 + sx * 2, Y + ey * 16 + sy * 2); p.moveTo(X + ex * 14, Y + ey * 14); p.lineTo(X + ex * 16 - sx * 2, Y + ey * 16 - sy * 2); p.stroke(); p.lineWidth = 1; } } }
      // berries left
      p.fillStyle = "rgba(0,0,0,0.45)"; p.fillRect(W - 92, H - 22, 86, 16); p.fillStyle = "#FFD0D8"; p.font = "bold 11px monospace"; p.fillText(`BERRIES ${L.eaten}/${L.need}`, W - 86, H - 10);
    },
  });
}
