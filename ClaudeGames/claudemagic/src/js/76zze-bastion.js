"use strict";
// The Rune Bastion, the window's side: a green valley with a dirt road winding from a goblin cave to the bastion's
// gate; grass that stirs, flowers, the road's ruts; rune-stones set beside it - a fire brazier that spits fireballs and
// scorches where they burst, a frost crystal whose beam rimes its target blue, an arcane obelisk with motes circling it
// that throws a crackling bolt - each with pips for its strength; goblins, wolves and ogres trudging with their health
// above them and a puff of smoke when they fall, mana floating up. The tray below picks the rune to set; click a set
// rune to strengthen it. The rules are 64zzf-arc2.js.
CM.CG_TABLES.push(["bastion", "The Rune Bastion"]);
{ const RBT = CM.RBT, C = RBT.C, GW = RBT.W * C, GH = RBT.H * C, W = GW, H = GH + 44, KINDS = ["fire", "frost", "arcane"], NAMES = { fire: "Fire", frost: "Frost", arcane: "Arcane" };
  const tower = (p, kind, X, Y, lvl, now, cd) => { const T = RBT.TOWERS[kind]; p.fillStyle = "rgba(0,0,0,0.3)"; p.beginPath(); p.ellipse(X + 17, Y + 26, 12, 5, 0, 0, Math.PI * 2); p.fill(); p.fillStyle = "#8A8478"; p.fillRect(X + 6, Y + 14, 20, 14); p.fillStyle = "#A8A294"; p.fillRect(X + 6, Y + 14, 20, 3);
    if (kind === "fire") { p.fillStyle = "#4A3A30"; p.fillRect(X + 8, Y + 10, 16, 5); const f = Math.sin(now / 70) * 2; p.fillStyle = "#F06030"; p.beginPath(); p.moveTo(X + 9, Y + 11); p.quadraticCurveTo(X + 16 + f, Y - 6, X + 23, Y + 11); p.fill(); p.fillStyle = "#FFD040"; p.beginPath(); p.moveTo(X + 12, Y + 11); p.quadraticCurveTo(X + 16 - f, Y + 1, X + 20, Y + 11); p.fill(); }
    else if (kind === "frost") { p.fillStyle = "#A0E0FF"; p.shadowColor = "#60C0F0"; p.shadowBlur = 8; p.beginPath(); p.moveTo(X + 16, Y - 4 + Math.sin(now / 400) * 1.5); p.lineTo(X + 23, Y + 9); p.lineTo(X + 16, Y + 15); p.lineTo(X + 9, Y + 9); p.fill(); p.shadowBlur = 0; p.fillStyle = "rgba(255,255,255,0.7)"; p.fillRect(X + 14, Y + 3, 2, 6); }
    else { p.fillStyle = "#4A3A60"; p.beginPath(); p.moveTo(X + 11, Y + 15); p.lineTo(X + 14, Y - 4); p.lineTo(X + 18, Y - 4); p.lineTo(X + 21, Y + 15); p.fill(); p.fillStyle = "#D0A0FF"; p.fillRect(X + 15, Y + 2, 2, 8); for (let k = 0; k < 3; k++) { const a = now / 400 + (k * Math.PI * 2) / 3; p.fillStyle = T.col; p.beginPath(); p.arc(X + 16 + Math.cos(a) * 11, Y + 6 + Math.sin(a) * 4, 2, 0, Math.PI * 2); p.fill(); } }
    for (let k = 0; k < lvl; k++) { p.fillStyle = "#FFE070"; p.beginPath(); p.arc(X + 11 + k * 5, Y + 22, 1.8, 0, Math.PI * 2); p.fill(); } };
  Object.assign(CM.ARC.reg.bastion, {
    ui: { W, H, scale: 1.05, frame: "#2A4A2A", start: "Man the walls", go: "Wave 1 - set your runes!", over: "The gate is broken", levelWord: "Wave",
      lore: "The Joker keeps a little bastion in a painted valley behind the arcade, and every evening the goblins come for it. \"Set the runes by the road,\" says the old warden, \"and spend what they drop on more. Don't let them reach my gate.\"",
      help: "Pick a rune in the tray (or 1, 2, 3) and click the grass beside the road to set it: fire (30 mana) bursts on a crowd, frost (25) slows, arcane (45) reaches far and hits hard. Click a set rune to strengthen it (to three pips). Foes that fall give mana; each that reaches the gate costs a heart (an ogre three). Runes and mana carry on to the next wave.",
      keys: ["Digit1", "Digit2", "Digit3"],
      extraHud(p, L, Wd) { p.fillStyle = "#C0A0FF"; p.font = "bold 12px monospace"; p.fillText(`✦ ${L.mana}`, Wd - 170, 19); p.fillStyle = "#F08080"; p.fillText(`♥ ${L.lives}`, Wd - 100, 19); p.fillStyle = "#F0E0B0"; p.font = "11px monospace"; p.fillText(`${L.queue.length + L.foes.length} left`, Wd - 58, 19); } },
    press(L, code, ui) { ui.rbPick = KINDS[Number(code.slice(5)) - 1] || ui.rbPick; },
    click(L, x, y, ui) {
      if (y >= GH) { const k = Math.floor(x / (W / 4)); if (k < 3) { ui.rbPick = KINDS[k]; ui.cgSfx("card", 0.25, 1.3); } return; }
      const cx = Math.floor(x / C), cy = Math.floor(y / C), had = L.towers.find((t) => t.x === cx && t.y === cy), why = had ? L.upgrade(cx, cy) : L.build(ui.rbPick || "fire", cx, cy);
      if (why) { ui.cgSfx("miss", 0.25); ui.rbWhy = { text: why, at: performance.now() }; } },
    event(ui, e, now, L, fx) {
      if (e.kind === "build" || e.kind === "upgrade") { ui.cgSfx(e.kind === "build" ? "slam" : "cardwin", 0.3, 1.3); ui.arcBurst(fx, e.x * C + 16, e.y * C + 16, ["#FFE070", RBT.TOWERS[(L.towers.find((t) => t.x === e.x && t.y === e.y) || {}).kind || "fire"].col, "#FFFFFF"], 14, 90); }
      else if (e.kind === "shot") ui.cgSfx(e.what === "fire" ? "zap" : e.what === "frost" ? "step" : "zap", 0.08, e.what === "arcane" ? 1.8 : e.what === "frost" ? 2 : 0.9);
      else if (e.kind === "fall") { ui.cgSfx("coin", 0.15, 1.6); ui.arcBurst(fx, e.x * C, e.y * C, ["#A0A0A0", "#606060", "#C0A0FF"], 8, 60, -40); ui.arcPts(fx, e.x * C, e.y * C - 8, `+${RBT.FOES[(e.pts === 80 ? "ogre" : e.pts === 30 ? "wolf" : "goblin")].mana}✦`, "#D0B0FF"); }
      else if (e.kind === "leak") { ui.cgSfx("hurt", 0.4); fx.shake = 0.2; }
      else if (e.kind === "held") ui.cgNote = `The wave is held: +${e.bonus} mana for the next.`;
    },
    draw(p, L, now, dt, ui) {
      for (let y = 0; y < RBT.H; y++) for (let x = 0; x < RBT.W; x++) { p.fillStyle = (x * 7 + y * 13) % 3 ? "#4A8A3A" : "#4F9040"; p.fillRect(x * C, y * C, C, C); }
      for (let k = 0; k < 60; k++) { const x = (k * 97) % GW, y = (k * 53) % GH; if (RBT.onPath.has(`${Math.floor(x / C)},${Math.floor(y / C)}`)) continue; const s = Math.sin(now / 600 + k) * 1.5; p.strokeStyle = "#6AB050"; p.beginPath(); p.moveTo(x, y + 4); p.lineTo(x + s, y - 2); p.stroke(); if (k % 7 === 0) { p.fillStyle = k % 2 ? "#F0E060" : "#F080A0"; p.fillRect(x + 3, y, 3, 3); } }
      for (const [x, y] of RBT.cells) { p.fillStyle = "#A08058"; p.fillRect(x * C - 1, y * C - 1, C + 2, C + 2); } for (const [x, y] of RBT.cells) { p.fillStyle = "#B8956A"; p.fillRect(x * C + 3, y * C + 3, C - 6, C - 6); p.fillStyle = "rgba(0,0,0,0.08)"; p.fillRect(x * C + 9, y * C + 3, 2, C - 6); p.fillRect(x * C + 21, y * C + 3, 2, C - 6); }
      const [sx, sy] = RBT.PATH[0]; p.fillStyle = "#2A2420"; p.beginPath(); p.arc(sx * C + 6, sy * C + 16, 16, Math.PI / 2, -Math.PI / 2, true); p.fill(); p.fillStyle = "#101010"; p.beginPath(); p.arc(sx * C + 6, sy * C + 16, 10, Math.PI / 2, -Math.PI / 2, true); p.fill();
      const [gx, gy] = RBT.PATH[RBT.PATH.length - 1]; p.fillStyle = "#7A7480"; p.fillRect(gx * C - 14, gy * C + 4, C + 28, C - 4); for (let k = 0; k < 5; k++) p.fillRect(gx * C - 14 + k * 13, gy * C - 2, 8, 6); p.fillStyle = "#4A2A18"; p.beginPath(); p.moveTo(gx * C + 6, gy * C + C); p.lineTo(gx * C + 6, gy * C + 16); p.arc(gx * C + 16, gy * C + 16, 10, Math.PI, 0); p.lineTo(gx * C + 26, gy * C + C); p.fill(); p.fillStyle = "#C03030"; p.fillRect(gx * C + 15, gy * C - 16, 2, 14); p.beginPath(); p.moveTo(gx * C + 17, gy * C - 16); p.lineTo(gx * C + 27, gy * C - 12 + Math.sin(now / 200)); p.lineTo(gx * C + 17, gy * C - 8); p.fill();
      if (L) { const m = ui.arcMouse, mx = m ? Math.floor(m[0] / C) : -1, my = m ? Math.floor(m[1] / C) : -1, hov = L.towers.find((t) => t.x === mx && t.y === my);
        if (m && m[1] < GH) { const kind = hov ? hov.kind : ui.rbPick || "fire", T = RBT.TOWERS[kind], r = (T.range + 0.3 * ((hov ? hov.lvl : 1) - 1)) * C; p.fillStyle = hov || L.canBuild(mx, my) ? "rgba(255,255,255,0.12)" : "rgba(255,60,60,0.15)"; p.strokeStyle = "rgba(255,255,255,0.35)"; p.beginPath(); p.arc(mx * C + 16, my * C + 16, r, 0, Math.PI * 2); p.fill(); p.stroke(); p.strokeStyle = hov || L.canBuild(mx, my) ? "#FFE070" : "#F04040"; p.strokeRect(mx * C + 1, my * C + 1, C - 2, C - 2); }
        for (const t of L.towers) tower(p, t.kind, t.x * C, t.y * C, t.lvl, now);
        for (const f of L.foes) { const [fx_, fy_] = L.pos(f), X = fx_ * C, Y = fy_ * C, step = Math.sin(now / 90 + f.id * 7) * 2, big = f.kind === "ogre";
          p.fillStyle = "rgba(0,0,0,0.25)"; p.beginPath(); p.ellipse(X, Y + (big ? 11 : 7), big ? 11 : 7, 3, 0, 0, Math.PI * 2); p.fill();
          if (f.kind === "wolf") { p.fillStyle = "#808088"; p.beginPath(); p.ellipse(X, Y, 10, 5, 0, 0, Math.PI * 2); p.fill(); p.beginPath(); p.arc(X + 8, Y - 3, 4, 0, Math.PI * 2); p.fill(); p.fillRect(X - 7, Y + 3 + step, 2, 4); p.fillRect(X + 5, Y + 3 - step, 2, 4); }
          else { const s = big ? 1.6 : 1; p.fillStyle = big ? "#8A6A40" : "#5A9A40"; p.beginPath(); p.ellipse(X, Y - 2 * s, 5 * s, 7 * s, 0, 0, Math.PI * 2); p.fill(); p.beginPath(); p.arc(X, Y - 10 * s, 4 * s, 0, Math.PI * 2); p.fill(); p.fillStyle = "#FFE040"; p.fillRect(X - 2 * s, Y - 11 * s, 1.5 * s, 1.5 * s); p.fillRect(X + 1 * s, Y - 11 * s, 1.5 * s, 1.5 * s); p.fillStyle = "#3A2A20"; p.fillRect(X - 3 * s, Y + 4 * s + step * 0.5, 2 * s, 3 * s); p.fillRect(X + 1 * s, Y + 4 * s - step * 0.5, 2 * s, 3 * s); if (big) { p.fillStyle = "#5A3A20"; p.fillRect(X + 6, Y - 18, 3, 16); } }
          if (f.slow > 0) { p.fillStyle = "rgba(140,210,255,0.35)"; p.beginPath(); p.arc(X, Y - 4, big ? 13 : 9, 0, Math.PI * 2); p.fill(); }
          const k = Math.max(0, f.hp / f.max); p.fillStyle = "rgba(0,0,0,0.6)"; p.fillRect(X - 10, Y - (big ? 28 : 20), 20, 3); p.fillStyle = k > 0.5 ? "#60E060" : k > 0.25 ? "#F0C040" : "#F04040"; p.fillRect(X - 10, Y - (big ? 28 : 20), 20 * k, 3); }
        for (const s of L.shots) { const T = RBT.TOWERS[s.kind], a = 1 - (L.t - s.at) / 0.25, x0 = s.x0 * C, y0 = s.y0 * C - 8, x1 = s.x1 * C, y1 = s.y1 * C; p.globalAlpha = Math.max(0, a);
          if (s.kind === "fire") { const k = 1 - a; p.fillStyle = "#FFB040"; p.beginPath(); p.arc(x0 + (x1 - x0) * Math.min(1, k * 2), y0 + (y1 - y0) * Math.min(1, k * 2), 4, 0, Math.PI * 2); p.fill(); if (k > 0.5) { p.fillStyle = "rgba(255,120,40,0.5)"; p.beginPath(); p.arc(x1, y1, RBT.TOWERS.fire.splash * C * (k - 0.3), 0, Math.PI * 2); p.fill(); } }
          else if (s.kind === "frost") { p.strokeStyle = "#B0E8FF"; p.lineWidth = 3; p.beginPath(); p.moveTo(x0, y0); p.lineTo(x1, y1); p.stroke(); p.lineWidth = 1; }
          else { p.strokeStyle = T.col; p.lineWidth = 2; p.beginPath(); p.moveTo(x0, y0); for (let k = 1; k < 6; k++) p.lineTo(x0 + ((x1 - x0) * k) / 6 + (Math.random() - 0.5) * 8, y0 + ((y1 - y0) * k) / 6 + (Math.random() - 0.5) * 8); p.lineTo(x1, y1); p.stroke(); p.lineWidth = 1; }
          p.globalAlpha = 1; } }
      // the tray
      p.fillStyle = "#2A2018"; p.fillRect(0, GH, W, 44); p.fillStyle = "#4A3A28"; p.fillRect(0, GH, W, 2);
      KINDS.forEach((kind, k) => { const X = k * (W / 4), on = (ui.rbPick || "fire") === kind, T = RBT.TOWERS[kind]; p.fillStyle = on ? "rgba(255,224,112,0.18)" : "rgba(255,255,255,0.04)"; p.fillRect(X + 4, GH + 5, W / 4 - 8, 34); if (on) { p.strokeStyle = "#FFE070"; p.strokeRect(X + 4.5, GH + 5.5, W / 4 - 9, 33); }
        tower(p, kind, X + 6, GH + 9, 1, now); p.fillStyle = "#F0E0B0"; p.font = "bold 12px Georgia"; p.fillText(`${k + 1} ${NAMES[kind]}`, X + 42, GH + 21); p.fillStyle = L && L.mana < T.cost ? "#C06060" : "#C0A0FF"; p.font = "11px monospace"; p.fillText(`${T.cost} ✦`, X + 42, GH + 35); });
      p.fillStyle = ui.rbWhy && performance.now() - ui.rbWhy.at < 2500 ? "#F0A080" : "#B0A890"; p.font = "10px Georgia"; const tip = ui.rbWhy && performance.now() - ui.rbWhy.at < 2500 ? ui.rbWhy.text : "Click a set rune|to strengthen it"; tip.split("|").forEach((t, k, a) => p.fillText(t, W * 0.75, GH + 24 + (k - (a.length - 1) / 2) * 12));
    },
  });
}
