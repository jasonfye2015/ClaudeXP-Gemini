"use strict";
// The Crossbow Range, the window's side: the back of a shooting booth - a painted night scene with a moon and hills,
// three brass rails with targets riding them on little stalks (tin ducks that bob, dragons that flap, gold stars that
// spin, the keeper's lantern), wooden scenery waves along the front; a crossbow's sight that sways a little where the
// mouse is; a bolt's quick streak, targets knocked back on their hinge with a ding and their points, a bullseye
// ringing gold; the round's mark, the bolts and the clock along the bottom. Click to loose. The rules are 64zze-fair2.js.
CM.CG_TABLES.push(["range", "The Crossbow Range"]);
{ const CB = CM.CB, W = CB.W, H = CB.H;
  Object.assign(CM.ARC.reg.range, {
    ui: { W, H, scale: 1.05, frame: "#4A2A18", start: "Load the crossbow", go: "Round 1 - make the mark!", over: "The range closes for the night", levelWord: "Round",
      lore: "At the end of the arcade wing, a shooting booth with tin targets on brass rails. \"Eighteen bolts a round,\" says the keeper. \"Make the mark and go again. Hit my lantern and it comes off your score.\"",
      help: "Aim with the mouse and click to loose. Ducks 10, dragons 25, stars 50 - double for a bullseye; the lantern costs 50. Make the round's mark before the bolts or the clock run out, or lose a life (two).",
      keys: [], extraHud(p, L, Wd) { p.fillStyle = "#F0E0B0"; p.font = "11px monospace"; p.fillText(`MARK ${L.got}/${L.need}`, Wd - 150, 19); for (let k = 0; k < L.lives; k++) { p.fillStyle = "#C08040"; p.fillRect(Wd - 22 - k * 14, 8, 8, 12); } } },
    click(L, x, y, ui) { const s = ui.cbSway || [0, 0]; L.shoot(x + s[0], y + s[1]); },
    event(ui, e, now, L, fx) {
      if (e.kind === "loose") { ui.cgSfx("zap", 0.2, 1.4); (this.streaks = this.streaks || []).push({ x: e.x, y: e.y, at: now }); }
      else if (e.kind === "hit") { ui.cgSfx(e.pts < 0 ? "miss" : e.bull ? "cardwin" : "tablebell", e.bull ? 0.4 : 0.3, e.pts < 0 ? 0.8 : 1.4); ui.arcBurst(fx, e.x, e.y, e.pts < 0 ? ["#F06040", "#FFFFFF"] : e.bull ? ["#FFE070", "#FFFFFF"] : ["#C0C8D0", "#FFFFFF"], e.bull ? 18 : 8, 120); ui.arcPts(fx, e.x, e.y - 18, e.pts > 0 ? `+${e.pts}${e.bull ? " BULL" : ""}` : `${e.pts}`, e.pts < 0 ? "#FF8070" : e.bull ? "#FFE070" : "#FFFFFF"); }
      else if (e.kind === "miss") ui.cgSfx("step", 0.2, 1.8); else if (e.kind === "short") { ui.cgSfx("cardlose", 0.4); ui.cgNote = `Short of the mark: ${e.got} of ${e.need}.`; }
    },
    draw(p, L, now, dt, ui) {
      const sky = p.createLinearGradient(0, 0, 0, H); sky.addColorStop(0, "#1A2448"); sky.addColorStop(1, "#4A3050"); p.fillStyle = sky; p.fillRect(0, 0, W, H);
      p.fillStyle = "#F0E8C8"; p.beginPath(); p.arc(W - 80, 50, 24, 0, Math.PI * 2); p.fill(); for (let k = 0; k < 30; k++) { p.fillStyle = "rgba(255,255,255,0.6)"; p.fillRect((k * 71) % W, (k * 29) % 120, 1.5, 1.5); }
      p.fillStyle = "#2A2A48"; p.beginPath(); p.moveTo(0, 250); for (let x = 0; x <= W; x += 40) p.lineTo(x, 220 - 30 * Math.abs(Math.sin(x / 110))); p.lineTo(W, 260); p.lineTo(0, 260); p.fill();
      for (const y of CB.RAILS) { p.fillStyle = "#B08A40"; p.fillRect(0, y + 22, W, 4); p.fillStyle = "#806020"; p.fillRect(0, y + 26, W, 2); }
      if (L) for (const T of L.targets) { const knock = T.hit > 0 ? 1 - T.hit / 0.6 : 0, X = T.x, Y = T.y + Math.sin(now / 200 + T.bob) * (T.kind === "duck" ? 2 : 0); p.fillStyle = "#806020"; p.fillRect(X - 1.5, Y + 8, 3, 15); p.save(); p.translate(X, Y + 22); p.rotate(-knock * 1.4 * (T.dir || 1)); p.translate(0, -22);
        if (T.kind === "duck") { p.fillStyle = "#F0D040"; p.beginPath(); p.ellipse(0, 0, 15, 9, 0, 0, Math.PI * 2); p.fill(); p.beginPath(); p.arc(10 * T.dir, -9, 7, 0, Math.PI * 2); p.fill(); p.fillStyle = "#F08020"; p.fillRect(15 * T.dir - (T.dir < 0 ? 6 : 0), -10, 6, 3); p.fillStyle = "#101010"; p.fillRect(11 * T.dir, -11, 2, 2); }
        else if (T.kind === "dragon") { const f = Math.sin(now / 70) * 6; p.fillStyle = "#4AA050"; p.beginPath(); p.ellipse(0, 0, 14, 7, 0, 0, Math.PI * 2); p.fill(); p.beginPath(); p.moveTo(-4, -2); p.lineTo(-10, -14 - f); p.lineTo(6, -2); p.fill(); p.beginPath(); p.arc(13 * T.dir, -4, 5, 0, Math.PI * 2); p.fill(); p.fillStyle = "#F04040"; p.fillRect(15 * T.dir, -6, 2, 2); }
        else if (T.kind === "star") { p.rotate(now / 150); p.fillStyle = "#FFD840"; p.beginPath(); for (let k = 0; k < 10; k++) { const r = k % 2 ? 5 : 12, a = (k * Math.PI) / 5; p.lineTo(Math.cos(a) * r, Math.sin(a) * r); } p.fill(); }
        else { p.fillStyle = "#3A3030"; p.fillRect(-7, -12, 14, 3); p.fillStyle = "#FFE080"; p.shadowColor = "#FFC040"; p.shadowBlur = 10; p.fillRect(-6, -9, 12, 16); p.shadowBlur = 0; p.fillStyle = "#3A3030"; p.fillRect(-7, 7, 14, 3); }
        if (T.kind !== "lantern" && T.kind !== "star") { p.strokeStyle = "rgba(200,40,40,0.8)"; p.beginPath(); p.arc(0, 0, CM.CB.KINDS[T.kind].r * 0.3, 0, Math.PI * 2); p.stroke(); }
        p.restore(); }
      for (let k = 0; k < 2; k++) { p.fillStyle = k ? "#2A6AA0" : "#3A80C0"; p.beginPath(); p.moveTo(0, H); for (let x = 0; x <= W; x += 20) p.lineTo(x, H - 50 + k * 18 + Math.sin(x / 30 + now / (500 + k * 200) + k) * 8); p.lineTo(W, H); p.fill(); }
      this.streaks = (this.streaks || []).filter((s) => now - s.at < 120); for (const s of this.streaks) { p.strokeStyle = `rgba(255,255,230,${1 - (now - s.at) / 120})`; p.lineWidth = 2; p.beginPath(); p.moveTo(W / 2, H); p.lineTo(s.x, s.y); p.stroke(); p.lineWidth = 1; }
      if (L) { const m = ui.arcMouse || [W / 2, H / 2], sw = ui.cbSway = [Math.sin(now / 430) * 4 + Math.sin(now / 170) * 1.5, Math.cos(now / 510) * 3 + Math.sin(now / 230) * 1.5], ax = m[0] + sw[0], ay = m[1] + sw[1]; p.strokeStyle = "rgba(255,80,60,0.9)"; p.lineWidth = 1.5; p.beginPath(); p.arc(ax, ay, 12, 0, Math.PI * 2); p.moveTo(ax - 18, ay); p.lineTo(ax - 6, ay); p.moveTo(ax + 6, ay); p.lineTo(ax + 18, ay); p.moveTo(ax, ay - 18); p.lineTo(ax, ay - 6); p.moveTo(ax, ay + 6); p.lineTo(ax, ay + 18); p.stroke(); p.lineWidth = 1;
        p.fillStyle = "rgba(0,0,0,0.55)"; p.fillRect(6, H - 22, 200, 18); p.fillStyle = "#FFE070"; p.font = "bold 11px monospace"; p.fillText(`BOLTS ${"|".repeat(L.bolts)}`, 10, H - 9); p.fillStyle = L.t < 8 ? "#FF7060" : "#F0E0B0"; p.fillText(`${Math.max(0, Math.ceil(L.t))}s`, 172, H - 9);
        const k = Math.min(1, L.got / L.need); p.fillStyle = "rgba(0,0,0,0.5)"; p.fillRect(W - 130, H - 22, 124, 14); p.fillStyle = k >= 1 ? "#80F080" : "#F0C040"; p.fillRect(W - 128, H - 20, 120 * k, 10); }
    },
  });
}
