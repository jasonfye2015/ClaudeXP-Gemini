"use strict";
// The Belfry Climb, the window's side: the inside of the bell tower at dusk - a high window with the sky, stone walls,
// the sloping oak beams with iron bolts, rope-bound ladders; the troll at the top beside the bell (swinging, glinting),
// heaving kegs; kegs rolling with their hoops turning; the brazier at the bottom with its fire; the climber in a red
// hood, legs moving as she walks and climbs; the wisps as pale flames. Arrows or W A S D to walk and climb, Space to
// jump. The rules are 64zu-belfry.js.
CM.CG_TABLES.push(["belfry", "The Belfry Climb"]);
{ const C = 16, BF = CM.BF;
  Object.assign(CM.ARC.reg.belfry, {
    ui: { W: BF.W * C, H: BF.H * C, scale: 1.05, frame: "#4A3018", start: "Up the tower", go: "Level 1. Ring the bell!", over: "The climber limps home",
      lore: "The Joker's bell tower has a troll in it - nobody remembers who let him in - and he does not want the bell rung. He rolls kegs at anyone who tries. \"Ring it anyway,\" says the attendant. \"The house pays by the ring.\"",
      help: "Arrows or W A S D to walk and climb the ladders; Space to jump - 100 for every keg jumped. Reach the bell at the top for the level and what is left of the bonus. Kegs sometimes come down the ladders; from level 3 wisps drift out of the brazier. One more life at 10,000.",
      keys: ["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight", "KeyW", "KeyA", "KeyS", "KeyD", "Space"],
      extraHud(p, L, W) { p.fillStyle = "#C0F0FF"; p.font = "11px monospace"; p.fillText(`BONUS ${Math.round(L.bonus / 100) * 100}`, W - 190, 19); for (let k = 0; k < Math.min(5, L.lives); k++) { p.fillStyle = "#C03030"; p.beginPath(); p.arc(W - 14 - k * 16, 14, 5, Math.PI, 0); p.fill(); p.fillStyle = "#F0C8A0"; p.fillRect(W - 17 - k * 16, 14, 6, 4); } } },
    input(L, H) { L.input((H.has("ArrowRight") || H.has("KeyD") ? 1 : 0) - (H.has("ArrowLeft") || H.has("KeyA") ? 1 : 0), (H.has("ArrowDown") || H.has("KeyS") ? 1 : 0) - (H.has("ArrowUp") || H.has("KeyW") ? 1 : 0)); },
    press(L, code) { if (code === "Space") L.jump(); },
    event(ui, e, now, L, fx) {
      if (e.kind === "jump") ui.cgSfx("step", 0.25, 1.8); else if (e.kind === "throw") ui.cgSfx("grind", 0.25, 0.8); else if (e.kind === "thud") ui.cgSfx("bump", 0.2, 0.7);
      else if (e.kind === "leap") { ui.cgSfx("coin", 0.4, 1.4); ui.arcPts(fx, e.x * C, e.y * C - 30, e.pts); } else if (e.kind === "wisp") ui.cgSfx("spell", 0.25, 0.7);
      else if (e.kind === "bell") { ui.cgSfx("tablebell", 0.7, 0.7); setTimeout(() => ui.cgSfx("tablebell", 0.6, 0.7), 350); ui.arcBurst(fx, 12 * C, 4 * C, ["#FFE070", "#FFFFFF"], 30, 180); ui.arcPts(fx, 12 * C, 3 * C, e.bonus, "#FFE070"); }
      else if (e.kind === "die") { ui.cgSfx("hurt", 0.6); fx.shake = 0.35; ui.arcBurst(fx, e.x * C, e.y * C - 8, ["#C03030", "#FFE070", "#FFFFFF"], 22, 160); } else if (e.kind === "extra") ui.cgSfx("cardwin", 0.4);
    },
    draw(p, L, now) {
      const W = BF.W * C, H = BF.H * C, bg = p.createLinearGradient(0, 0, 0, H); bg.addColorStop(0, "#2A2030"); bg.addColorStop(1, "#140E14"); p.fillStyle = bg; p.fillRect(0, 0, W, H);
      for (let y = 0; y < H; y += 18) for (let x = ((y / 18) % 2) * 20 - 20; x < W; x += 40) { p.fillStyle = "rgba(255,255,255,0.025)"; p.fillRect(x + 1, y + 1, 38, 16); }
      // the window
      const wx = W - 110, wy = 20, sky = p.createLinearGradient(0, wy, 0, wy + 70); sky.addColorStop(0, "#3A4A8A"); sky.addColorStop(1, "#E08850"); p.fillStyle = sky; p.beginPath(); p.moveTo(wx, wy + 70); p.lineTo(wx, wy + 25); p.arc(wx + 25, wy + 25, 25, Math.PI, 0); p.lineTo(wx + 50, wy + 70); p.fill(); p.strokeStyle = "#5A4A40"; p.lineWidth = 3; p.stroke(); p.beginPath(); p.moveTo(wx + 25, wy); p.lineTo(wx + 25, wy + 70); p.stroke(); p.lineWidth = 1; p.fillStyle = "#FFF4C0"; p.fillRect(wx + 34, wy + 30, 2, 2);
      // beams and ladders
      for (const [lx, a, b] of BF.LADDERS) { const top = BF.yAt(a, lx) * C, bot = BF.yAt(b, lx) * C, X = lx * C; p.strokeStyle = "#8A6A3A"; p.lineWidth = 2; p.beginPath(); p.moveTo(X - 6, top); p.lineTo(X - 6, bot); p.moveTo(X + 6, top); p.lineTo(X + 6, bot); p.stroke(); for (let y = top + 6; y < bot; y += 8) { p.beginPath(); p.moveTo(X - 6, y); p.lineTo(X + 6, y); p.stroke(); } p.lineWidth = 1; }
      BF.BEAMS.forEach((Bm, i) => { const x0 = Bm.x0 * C, x1 = Bm.x1 * C, y0 = BF.yAt(i, Bm.x0) * C, y1 = BF.yAt(i, Bm.x1) * C; p.fillStyle = "#7A4A22"; p.beginPath(); p.moveTo(x0, y0); p.lineTo(x1, y1); p.lineTo(x1, y1 + 7); p.lineTo(x0, y0 + 7); p.fill(); p.fillStyle = "#9A6A32"; p.beginPath(); p.moveTo(x0, y0); p.lineTo(x1, y1); p.lineTo(x1, y1 + 2); p.lineTo(x0, y0 + 2); p.fill(); p.fillStyle = "#3A3A40"; for (let x = Bm.x0 + 1; x < Bm.x1; x += 3) p.fillRect(x * C - 1, BF.yAt(i, x) * C + 3, 2, 2); });
      // the brazier
      const bx = 1 * C, by = 30 * C; p.fillStyle = "#3A3A40"; p.fillRect(bx - 10, by - 14, 22, 14); for (let k = 0; k < 4; k++) { const f = Math.sin(now / 80 + k) * 3; p.fillStyle = k % 2 ? "#FFB040" : "#FF6020"; p.beginPath(); p.moveTo(bx - 8 + k * 5, by - 14); p.quadraticCurveTo(bx - 6 + k * 5, by - 28 - f, bx - 3 + k * 5, by - 14); p.fill(); } const fg = p.createRadialGradient(bx, by - 18, 2, bx, by - 18, 60); fg.addColorStop(0, "rgba(255,150,60,0.3)"); fg.addColorStop(1, "rgba(255,150,60,0)"); p.fillStyle = fg; p.fillRect(bx - 60, by - 80, 120, 100);
      // the bell and the troll
      const sw = Math.sin(now / 400) * 0.15, bellX = 12 * C, bellY = 6 * C - 18; p.save(); p.translate(bellX, bellY - 16); p.rotate(sw); p.fillStyle = "#C8962A"; p.beginPath(); p.moveTo(-10, 16); p.quadraticCurveTo(-10, 0, 0, 0); p.quadraticCurveTo(10, 0, 10, 16); p.lineTo(13, 20); p.lineTo(-13, 20); p.fill(); p.fillStyle = "rgba(255,255,220,0.5)"; p.fillRect(-6, 4, 3, 10); p.restore();
      if (L) { const heave = L.kegT < 0.4 ? 1 : 0, tx = 3.5 * C, ty = 6 * C; p.fillStyle = "#4A6A3A"; p.beginPath(); p.ellipse(tx, ty - 16, 14, 16, 0, 0, Math.PI * 2); p.fill(); p.fillStyle = "#5A7A4A"; p.beginPath(); p.arc(tx, ty - 34, 9, 0, Math.PI * 2); p.fill(); p.fillStyle = "#F0E040"; p.fillRect(tx - 5, ty - 37, 3, 3); p.fillRect(tx + 2, ty - 37, 3, 3); p.fillStyle = "#F0F0E0"; p.fillRect(tx - 4, ty - 30, 2, 3); p.fillRect(tx + 2, ty - 30, 2, 3); p.strokeStyle = "#4A6A3A"; p.lineWidth = 5; p.beginPath(); p.moveTo(tx + 10, ty - 22); p.lineTo(tx + 18, heave ? ty - 40 : ty - 14); p.moveTo(tx - 10, ty - 22); p.lineTo(tx - 18, heave ? ty - 40 : ty - 14); p.stroke(); p.lineWidth = 1; if (heave) this.keg(p, tx, ty - 46, now); }
      if (!L) return;
      for (const k of L.kegs) this.keg(p, k.x * C, k.y * C - 7, k.rot);
      for (const w of L.wisps) { const X = w.x * C, Y = w.y * C - 9, f = Math.sin(now / 90 + w.t); p.save(); p.shadowColor = "#A0E0FF"; p.shadowBlur = 12; p.fillStyle = "rgba(200,240,255,0.85)"; p.beginPath(); p.moveTo(X - 6, Y + 6); p.quadraticCurveTo(X - 7, Y - 6 - f * 2, X, Y - 12 - f * 3); p.quadraticCurveTo(X + 7, Y - 6, X + 6, Y + 6); p.fill(); p.restore(); p.fillStyle = "#203040"; p.fillRect(X - 3, Y - 2, 2, 2); p.fillRect(X + 1, Y - 2, 2, 2); }
      const P = L.p; if (!P.dead || Math.floor(now / 100) % 2) { const X = P.x * C, Y = (P.y - P.h) * C, step = Math.sin(P.walk * 18) * 3; p.fillStyle = "rgba(0,0,0,0.3)"; if (!P.lad) { p.beginPath(); p.ellipse(X, P.y * C, 6, 2, 0, 0, Math.PI * 2); p.fill(); }
        p.fillStyle = "#2A2A3A"; p.fillRect(X - 4, Y - 6, 3, 6 + (P.lad ? 0 : step)); p.fillRect(X + 1, Y - 6, 3, 6 - (P.lad ? 0 : step)); p.fillStyle = "#A02828"; p.fillRect(X - 5, Y - 16, 10, 11); p.fillStyle = "#F0C8A0"; p.beginPath(); p.arc(X, Y - 20, 4, 0, Math.PI * 2); p.fill(); p.fillStyle = "#C03030"; p.beginPath(); p.moveTo(X - 6, Y - 18); p.quadraticCurveTo(X, Y - 30, X + 6, Y - 18); p.fill();
        if (P.lad) { p.fillStyle = "#F0C8A0"; p.fillRect(X - 8, Y - 18 + step, 3, 3); p.fillRect(X + 5, Y - 18 - step, 3, 3); } else { p.fillStyle = "#101010"; p.fillRect(X + P.face * 2 - 1, Y - 21, 2, 2); } }
    },
    keg(p, X, Y, rot) { p.save(); p.translate(X, Y); p.rotate(rot); p.fillStyle = "#8A5A28"; p.beginPath(); p.ellipse(0, 0, 7, 7, 0, 0, Math.PI * 2); p.fill(); p.strokeStyle = "#3A3A40"; p.lineWidth = 2; p.beginPath(); p.moveTo(-7, -3); p.lineTo(7, -3); p.moveTo(-7, 3); p.lineTo(7, 3); p.stroke(); p.strokeStyle = "#5A3A18"; p.lineWidth = 1; p.beginPath(); p.moveTo(0, -7); p.lineTo(0, 7); p.stroke(); p.restore(); },
  });
}
