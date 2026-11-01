"use strict";
// The Undercroft Sprint, the window's side: a run down the old tunnels in three depths of parallax - far arches in the
// gloom, nearer pillars with torches guttering, the flagged floor rushing by; the runner (a hooded thief with a
// trailing scarf) in a running cycle, a tuck when jumping and a skid of dust when sliding; pits with a glimpse of the
// drop, rusted spikes, low beams with hanging chains, bats that flap at head height, coins that spin and chime. Space or
// Up to jump, Down to slide (or to drop quickly from a jump). The rules are 64zzf-arc2.js.
CM.CG_TABLES.push(["sprint", "The Undercroft Sprint"]);
{ const US = CM.US, W = US.W, H = US.H, G = US.ground;
  Object.assign(CM.ARC.reg.sprint, {
    ui: { W, H, scale: 1.15, frame: "#2A2430", start: "Start running", go: "Stretch 1 - run!", over: "The tunnels win", levelWord: "Stretch",
      lore: "Under the Joker's cellars the old undercroft runs on for miles, and the house pays by the stretch for anyone who can run it. \"Don't stop,\" says the bored guard at the gate. \"Nobody who stops gets paid.\"",
      help: "Space or Up to jump the pits and spikes, Down to slide under the beams (or drop quickly from a jump). Bats fly at head height - jump high over them or slide under. Coins as you go. Reach the end of each stretch; three knocks and you're done.",
      keys: ["Space", "ArrowUp", "KeyW", "ArrowDown", "KeyS"],
      extraHud(p, L, Wd) { p.fillStyle = "#F0D060"; p.font = "11px monospace"; p.fillText(`◎${L.coins} ${Math.round(L.x / 10)}/${Math.round(L.len / 10)}m`, Wd - 175, 19); for (let k = 0; k < L.lives; k++) { p.fillStyle = "#E05050"; p.beginPath(); p.arc(Wd - 16 - k * 16, 12, 3.5, 0, Math.PI * 2); p.arc(Wd - 10 - k * 16, 12, 3.5, 0, Math.PI * 2); p.lineTo(Wd - 13 - k * 16, 20); p.fill(); } } },
    press(L, code) { if (code === "Space" || code === "ArrowUp" || code === "KeyW") L.jump(); else L.slide(); },
    event(ui, e, now, L, fx) {
      if (e.kind === "jump") ui.cgSfx("step", 0.25, 1.5); else if (e.kind === "slide") { ui.cgSfx("step", 0.25, 0.6); ui.arcBurst(fx, US.px, G, ["#8A7A68", "#A09080"], 8, 70, 100); }
      else if (e.kind === "coin") { ui.cgSfx("coin", 0.2, 1.4 + Math.random() * 0.3); ui.arcBurst(fx, US.px + 10, G - 30 + L.p.y, ["#FFE070", "#FFFFFF"], 4, 60, 0); }
      else if (e.kind === "hurt") { ui.cgSfx("hurt", 0.45); fx.shake = 0.3; ui.arcBurst(fx, US.px, G - 20 + L.p.y, ["#F06040", "#FFFFFF"], 14, 140); ui.cgNote = { pit: "Down a pit - the guard hauls you out.", spikes: "Spikes!", beam: "Straight into a beam.", bat: "A bat in the face!" }[e.why] || ""; }
    },
    draw(p, L, now) {
      const x = L ? L.x : now / 4; p.fillStyle = "#0E0C14"; p.fillRect(0, 0, W, H);
      p.fillStyle = "#1A1824"; for (let k = -1; k < 6; k++) { const ax = k * 120 - ((x * 0.2) % 120); p.beginPath(); p.moveTo(ax, G); p.lineTo(ax, 90); p.arc(ax + 50, 90, 50, Math.PI, 0); p.lineTo(ax + 100, G); p.lineTo(ax + 92, G); p.lineTo(ax + 92, 92); p.arc(ax + 50, 92, 42, 0, Math.PI, true); p.lineTo(ax + 8, G); p.fill(); }
      for (let k = -1; k < 4; k++) { const px = k * 200 - ((x * 0.55) % 200); p.fillStyle = "#2A2634"; p.fillRect(px, 30, 26, G - 30); p.fillStyle = "#363040"; p.fillRect(px - 4, 30, 34, 10); const fl = Math.sin(now / 60 + k) * 2;
        const gl = p.createRadialGradient(px + 13, 70, 2, px + 13, 70, 60); gl.addColorStop(0, "rgba(255,170,60,0.35)"); gl.addColorStop(1, "rgba(255,170,60,0)"); p.fillStyle = gl; p.fillRect(px - 50, 10, 126, 130); p.fillStyle = "#FFB040"; p.beginPath(); p.moveTo(px + 9, 74); p.quadraticCurveTo(px + 13 + fl, 56, px + 17, 74); p.fill(); p.fillStyle = "#5A3A20"; p.fillRect(px + 11, 74, 4, 10); }
      p.fillStyle = "#3A3440"; p.fillRect(0, 0, W, 22); p.fillStyle = "#2A2430"; for (let k = 0; k < W / 30 + 2; k++) p.fillRect(k * 30 - (x % 30), 16, 2, 6);
      const pits = L ? L.things.filter((t) => t.kind === "pit") : [];
      p.fillStyle = "#4A4250"; p.fillRect(0, G, W, H - G); for (let k = 0; k < W / 40 + 2; k++) { p.fillStyle = "rgba(0,0,0,0.25)"; p.fillRect(k * 40 - (x % 40), G, 1, H - G); } p.fillStyle = "#6A6070"; p.fillRect(0, G, W, 3);
      for (const t of pits) { const sx = t.x - x; if (sx > W || sx + t.w < 0) continue; const g = p.createLinearGradient(0, G, 0, H); g.addColorStop(0, "#08060C"); g.addColorStop(1, "#000"); p.fillStyle = g; p.fillRect(sx, G, t.w, H - G); p.fillStyle = "#2A2430"; p.fillRect(sx - 2, G, 2, 20); p.fillRect(sx + t.w, G, 2, 20); }
      if (L) { for (const t of L.things) { const sx = t.x - x; if (sx < -60 || sx > W + 60) continue;
          if (t.kind === "coin") { if (t.done) continue; const s = Math.abs(Math.cos(now / 150 + t.x)); p.fillStyle = "#F0C040"; p.beginPath(); p.ellipse(sx, G - t.y - 10, 6 * s + 1, 6, 0, 0, Math.PI * 2); p.fill(); p.fillStyle = "#FFF0A0"; p.fillRect(sx - 1, G - t.y - 14, 2 * s, 3); }
          else if (t.kind === "spikes") { const bx = t.x - x + 13; p.fillStyle = "#8A8070"; for (let k = 0; k < 4; k++) { p.beginPath(); p.moveTo(bx - 13 + k * 7, G); p.lineTo(bx - 9.5 + k * 7, G - 16); p.lineTo(bx - 6 + k * 7, G); p.fill(); } p.fillStyle = "#6A3020"; p.fillRect(bx - 13, G - 2, 28, 2); }
          else if (t.kind === "beam") { const bx = t.x - x + 13; p.fillStyle = "#5A3A20"; p.fillRect(bx - 4, 22, 8, G - 40 - 22); p.fillStyle = "#7A5030"; p.fillRect(bx - 20, G - 44, 44, 12); p.strokeStyle = "#8A8A90"; for (let k = 0; k < 2; k++) { p.beginPath(); p.moveTo(bx - 12 + k * 26, G - 32); p.lineTo(bx - 12 + k * 26 + Math.sin(now / 300 + k) * 3, G - 22); p.stroke(); } }
          else if (t.kind === "bat") { if (t.done) continue; const bx = t.x - x + 13, by = G - 34 + Math.sin(now / 200 + t.x) * 5, f = Math.sin(now / 45) * 8; p.fillStyle = "#3A2040"; p.beginPath(); p.ellipse(bx, by, 6, 5, 0, 0, Math.PI * 2); p.fill(); p.beginPath(); p.moveTo(bx - 4, by); p.lineTo(bx - 16, by - f); p.lineTo(bx - 10, by + 3); p.moveTo(bx + 4, by); p.lineTo(bx + 16, by - f); p.lineTo(bx + 10, by + 3); p.fill(); p.fillStyle = "#FF4040"; p.fillRect(bx - 3, by - 2, 2, 2); p.fillRect(bx + 1, by - 2, 2, 2); } }
        const P = L.p, px = US.px, py = G + P.y; if (!(P.guard > 0 && Math.floor(now / 90) % 2)) { p.save(); p.translate(px, py);
          if (P.slide > 0) { p.fillStyle = "#3A4A6A"; p.beginPath(); p.ellipse(0, -9, 16, 8, 0, 0, Math.PI * 2); p.fill(); p.fillStyle = "#E0C090"; p.beginPath(); p.arc(12, -12, 5, 0, Math.PI * 2); p.fill(); p.fillStyle = "#C03030"; p.fillRect(-20, -14, 10, 3); }
          else { const run = P.onGround ? Math.sin(now / 55) : 0.6, tuck = P.onGround ? 0 : 1; p.strokeStyle = "#2A2A3A"; p.lineWidth = 4; p.beginPath(); p.moveTo(0, -18); p.lineTo(run * 8, -8 + tuck * 2); p.lineTo(run * 6 + (tuck ? 4 : 0), 0 - tuck * 6); p.moveTo(0, -18); p.lineTo(-run * 8, -8 + tuck * 2); p.lineTo(-run * 6 - 2, 0 - tuck * 4); p.stroke(); p.lineWidth = 1;
            p.fillStyle = "#3A4A6A"; p.beginPath(); p.ellipse(0, -26, 7, 11, 0.15, 0, Math.PI * 2); p.fill(); p.fillStyle = "#2A3450"; p.beginPath(); p.arc(2, -40, 6.5, 0, Math.PI * 2); p.fill(); p.fillStyle = "#E0C090"; p.beginPath(); p.arc(4, -39, 3.5, 0, Math.PI * 2); p.fill();
            p.strokeStyle = "#C03030"; p.lineWidth = 3; p.beginPath(); p.moveTo(-3, -34); p.quadraticCurveTo(-14, -34 + Math.sin(now / 80) * 4, -22, -30 + Math.sin(now / 60) * 5); p.stroke(); p.lineWidth = 1; }
          p.restore(); } }
      const fog = p.createLinearGradient(0, 0, W, 0); fog.addColorStop(0, "rgba(0,0,0,0.5)"); fog.addColorStop(0.15, "rgba(0,0,0,0)"); fog.addColorStop(0.85, "rgba(0,0,0,0)"); fog.addColorStop(1, "rgba(0,0,0,0.5)"); p.fillStyle = fog; p.fillRect(0, 0, W, H);
      if (L) { const k = Math.min(1, L.x / L.len); p.fillStyle = "rgba(0,0,0,0.5)"; p.fillRect(8, H - 14, W - 16, 6); p.fillStyle = "#F0C040"; p.fillRect(9, H - 13, (W - 18) * k, 4); }
    },
  });
}
