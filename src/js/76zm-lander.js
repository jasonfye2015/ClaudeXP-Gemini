"use strict";
// The Skyreach Landing, the window's side: a dusk sky going from violet to amber with stars and two moons, far isles in
// silhouette drifting, the near isle's rock in layers with grass on top and roots underneath, the pads lit by beacon
// posts (their multipliers over them, blinking); the sky-skiff - a hull under a small balloon - with a flame from its
// burner, puffs of smoke as it burns; the readouts: fuel, speed down and across, the tilt, green when safe and red when
// not. Up (W) to burn, Left and Right (A, D) to turn. The rules are 64zv-lander.js.
CM.CG_TABLES.push(["lander", "The Skyreach Landing"]);
{ const C = 8, LD = CM.LD;
  Object.assign(CM.ARC.reg.lander, {
    ui: { W: LD.W * C, H: LD.H * C, scale: 1, frame: "#2A2440", start: "Cast off", go: "Level 1. Bring her down gently!", over: "The skiff is towed home in pieces",
      lore: "High over the Joker's roof a few rocks float, and the house keeps a little sky-skiff tethered there. \"Set it down on a lit pad,\" says the attendant. \"Slow, and straight. The smaller pads pay more. The rocks pay nothing.\"",
      help: "Up or W to burn, Left and Right (A, D) to turn. Touch down on a lit pad slower than the green marks, nearly upright; ×2, ×3 and ×5 pads, more for fuel left and a softer touch. The pull grows each level; from level 4 a wind blows.",
      keys: ["ArrowUp", "ArrowLeft", "ArrowRight", "KeyW", "KeyA", "KeyD"] },
    input(L, H) { L.input((H.has("ArrowRight") || H.has("KeyD") ? 1 : 0) - (H.has("ArrowLeft") || H.has("KeyA") ? 1 : 0), H.has("ArrowUp") || H.has("KeyW")); },
    lifeIcon(p, x, y) { p.fillStyle = "#E0C080"; p.beginPath(); p.arc(x, y - 2, 4, 0, Math.PI * 2); p.fill(); p.fillStyle = "#8A5A2A"; p.fillRect(x - 3, y + 2, 6, 3); },
    event(ui, e, now, L, fx) {
      if (e.kind === "land") { ui.cgSfx("tablebell", 0.5); ui.arcBurst(fx, e.x * C, e.y * C, ["#FFE070", "#FFFFFF", "#A0F0A0"], 24, 120, -60); ui.arcPts(fx, e.x * C, e.y * C - 24, e.pts, "#FFE070"); }
      else if (e.kind === "crash") { ui.cgSfx("slam", 0.6, 0.7); fx.shake = 0.4; ui.arcBurst(fx, e.x * C, e.y * C, ["#FF8030", "#FFE070", "#6A4A2A", "#FFFFFF"], 36, 200); ui.cgNote = `Wrecked - ${e.why}.`; }
    },
    draw(p, L, now, dt) {
      const W = LD.W * C, H = LD.H * C, sky = p.createLinearGradient(0, 0, 0, H); sky.addColorStop(0, "#2A1A4A"); sky.addColorStop(0.6, "#8A4A6A"); sky.addColorStop(1, "#F0A050"); p.fillStyle = sky; p.fillRect(0, 0, W, H);
      if (L) for (const [x, y, b] of L.stars) { p.globalAlpha = 0.3 + 0.5 * Math.abs(Math.sin(now / 800 + b * 9)); p.fillStyle = "#FFF"; p.fillRect(x * C, y * C, 1.5, 1.5); } p.globalAlpha = 1;
      p.fillStyle = "#F0E8D0"; p.beginPath(); p.arc(W * 0.8, 50, 16, 0, Math.PI * 2); p.fill(); p.fillStyle = "#C8B8E0"; p.beginPath(); p.arc(W * 0.86, 30, 7, 0, Math.PI * 2); p.fill();
      for (let k = 0; k < 4; k++) { const x = ((now / (300 + k * 120) + k * 140) % (W + 160)) - 80, y = 90 + k * 30; p.fillStyle = `rgba(60,30,70,${0.25 + k * 0.08})`; p.beginPath(); p.ellipse(x, y, 40 - k * 4, 8, 0, 0, Math.PI * 2); p.fill(); p.beginPath(); p.moveTo(x - 30, y); p.lineTo(x, y + 26 - k * 3); p.lineTo(x + 30, y); p.fill(); }
      if (!L) return;
      // the isle
      p.beginPath(); p.moveTo(0, H); for (const [x, y] of L.ground) p.lineTo(x * C, y * C); p.lineTo(W, H); p.closePath(); const rock = p.createLinearGradient(0, 160, 0, H); rock.addColorStop(0, "#5A4A5A"); rock.addColorStop(1, "#2A1E2A"); p.fillStyle = rock; p.fill();
      p.strokeStyle = "rgba(0,0,0,0.25)"; for (let k = 1; k < 5; k++) { p.beginPath(); for (const [x, y] of L.ground) p.lineTo(x * C, y * C + k * 12); p.stroke(); }
      p.strokeStyle = "#5A9A40"; p.lineWidth = 3; p.beginPath(); L.ground.forEach(([x, y], i) => (i ? p.lineTo(x * C, y * C) : p.moveTo(x * C, y * C))); p.stroke(); p.lineWidth = 1;
      for (const P of L.pads) { const x0 = P.x0 * C, x1 = P.x1 * C, y = P.y * C; p.fillStyle = "#C8A060"; p.fillRect(x0, y - 2, x1 - x0, 4); for (const bx of [x0, x1]) { p.fillStyle = "#3A3030"; p.fillRect(bx - 1, y - 14, 2, 12); const on = Math.floor(now / 400 + P.m) % 2; p.save(); p.shadowColor = "#FFE070"; p.shadowBlur = on ? 10 : 2; p.fillStyle = on ? "#FFE070" : "#8A7030"; p.beginPath(); p.arc(bx, y - 15, 3, 0, Math.PI * 2); p.fill(); p.restore(); } p.fillStyle = "#FFF0C0"; p.font = "bold 11px Georgia"; p.textAlign = "center"; p.fillText(`×${P.m}`, (x0 + x1) / 2, y - 8); p.textAlign = "left"; }
      // the skiff
      const S = L.s; if (!S.dead) { const X = S.x * C, Y = S.y * C; p.save(); p.translate(X, Y); p.rotate(S.a);
        if (S.burn) { const f = 10 + Math.random() * 8; p.fillStyle = "#FFB040"; p.beginPath(); p.moveTo(-4, 8); p.lineTo(0, 8 + f); p.lineTo(4, 8); p.fill(); p.fillStyle = "#FFF0A0"; p.beginPath(); p.moveTo(-2, 8); p.lineTo(0, 8 + f * 0.5); p.lineTo(2, 8); p.fill(); }
        p.strokeStyle = "#5A4030"; p.beginPath(); p.moveTo(-6, -2); p.lineTo(-5, -10); p.moveTo(6, -2); p.lineTo(5, -10); p.stroke(); p.fillStyle = "#E0C080"; p.beginPath(); p.ellipse(0, -16, 9, 10, 0, 0, Math.PI * 2); p.fill(); p.fillStyle = "#C03030"; p.fillRect(-9, -17, 18, 3);
        p.fillStyle = "#8A5A2A"; p.beginPath(); p.moveTo(-8, -2); p.lineTo(8, -2); p.lineTo(5, 6); p.lineTo(-5, 6); p.fill(); p.strokeStyle = "#3A3030"; p.beginPath(); p.moveTo(-5, 6); p.lineTo(-8, 10); p.moveTo(5, 6); p.lineTo(8, 10); p.stroke(); p.restore();
        if (S.burn && Math.random() < 0.5) this.puffs.push({ x: X - Math.sin(S.a) * 14, y: Y + Math.cos(S.a) * 14, r: 2, life: 1 });
        // the drop line to the ground, to judge by
        const gy = L.groundAt(S.x) * C; p.strokeStyle = "rgba(255,255,255,0.12)"; p.setLineDash([2, 4]); p.beginPath(); p.moveTo(X, Y + 10); p.lineTo(X, gy); p.stroke(); p.setLineDash([]); }
      this.puffs = (this.puffs || []).filter((q) => (q.life -= dt) > 0); for (const q of this.puffs) { q.r += dt * 8; q.y += dt * 6; p.fillStyle = `rgba(200,190,200,${q.life * 0.4})`; p.beginPath(); p.arc(q.x, q.y, q.r, 0, Math.PI * 2); p.fill(); }
      // readouts
      const ok = (v, m) => (v <= m ? "#90F090" : "#FF8070"); p.fillStyle = "rgba(0,0,0,0.45)"; p.fillRect(6, 6, 132, 64); p.font = "bold 11px monospace";
      p.fillStyle = "#F0E0B0"; p.fillText(`FUEL`, 12, 20); p.fillStyle = "#3A3030"; p.fillRect(48, 12, 84, 8); p.fillStyle = S.fuel / L.fuel0 < 0.25 ? "#FF7050" : "#F0C040"; p.fillRect(48, 12, 84 * S.fuel / L.fuel0, 8);
      p.fillStyle = ok(S.vy, LD.safeV); p.fillText(`DOWN   ${S.vy.toFixed(1)}`, 12, 36); p.fillStyle = ok(Math.abs(S.vx), LD.safeH); p.fillText(`ACROSS ${S.vx.toFixed(1)}`, 12, 50); p.fillStyle = ok(Math.abs(S.a), LD.safeA); p.fillText(`TILT   ${Math.round(S.a * 57)}°`, 12, 64);
      if (L.wind) { p.fillStyle = "#C0E0FF"; p.fillText(`WIND ${L.wind > 0 ? "→" : "←"} ${Math.abs(L.wind).toFixed(1)}`, W - 100, 20); }
    },
    puffs: [],
  });
}
