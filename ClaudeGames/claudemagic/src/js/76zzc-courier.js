"use strict";
// The Courier's Round, the window's side: the market street from above, scrolling toward the courier on a stout grey
// pony - cobbles, the gutter, lamp-posts throwing pools of light; on the left the houses, roofs in their own colours,
// the subscribers' windows lit and their letter-boxes on posts by the walk, the others dark; a scroll thrown spins
// across the walk, and a box that takes one flips its little flag up with a puff of sparkles; dogs dash, carts trundle,
// puddles ripple and barrels roll. Left and right to ride, Space to throw. The rules are 64zzf-arc2.js.
CM.CG_TABLES.push(["courier", "The Courier's Round"]);
{ const CO = CM.CO, W = CO.W, H = CO.H, ROOF = ["#A04030", "#406090", "#6A7A30", "#805A9A", "#9A7A40"];
  Object.assign(CM.ARC.reg.courier, {
    ui: { W, H, scale: 1, frame: "#3A2A1A", start: "Take the satchel", go: "Street 1 - the round begins!", over: "The round is lost", levelWord: "Street",
      lore: "The Joker's house newsletter goes out every morning to the subscribers on Market Row, and the courier is paid by the box. \"Lit windows want a scroll,\" says the postmistress. \"Dark ones don't. Mind the miller's dog.\"",
      help: "Left and right to ride along the road, Space to throw a scroll to the left - time it so the scroll meets a lit house's letter-box. Deliver to most of the street's subscribers to clear it. Dogs, carts and barrels throw you; puddles skid you. Grab a bundle when you run low.",
      keys: ["ArrowLeft", "ArrowRight", "KeyA", "KeyD", "Space"],
      extraHud(p, L, Wd) { p.fillStyle = "#F0E0B0"; p.font = "11px monospace"; p.fillText(`✉ ${L.got}/${L.need}  ✎ ${L.scrolls}`, Wd - 150, 19); for (let k = 0; k < L.lives; k++) { p.fillStyle = "#A0A0A8"; p.beginPath(); p.ellipse(Wd - 16 - k * 16, 14, 5, 7, 0, 0, Math.PI * 2); p.fill(); } } },
    input(L, held) { L.input((held.has("ArrowRight") || held.has("KeyD") ? 1 : 0) - (held.has("ArrowLeft") || held.has("KeyA") ? 1 : 0)); },
    press(L, code) { if (code === "Space") L.throwIt(); },
    event(ui, e, now, L, fx) {
      if (e.kind === "throw") ui.cgSfx("card", 0.3, 1.2);
      else if (e.kind === "deliver") { ui.cgSfx("coin", 0.4, 1.2); ui.arcBurst(fx, e.x, e.y, ["#FFE070", "#FFFFFF", "#80E0FF"], 12, 100, 100); ui.arcPts(fx, e.x, e.y - 16, `+${e.pts}`, "#FFE070"); }
      else if (e.kind === "splash") { ui.cgSfx("step", 0.3, 0.6); ui.arcBurst(fx, L.p.x, H - 70, ["#80B0E0", "#C0E0FF"], 10, 90); }
      else if (e.kind === "die") { ui.cgSfx("hurt", 0.45); ui.cgSfx("slam", 0.3); ui.arcBurst(fx, e.x, H - 70, ["#E0D0B0", "#FFFFFF", "#806040"], 20, 150); fx.shake = 0.3; ui.cgNote = { dog: "The miller's dog had you over!", cart: "Into the side of a cart!", barrel: "A rolling barrel took the pony's legs." }[e.why] || ""; }
      else if (e.kind === "short") { ui.cgSfx("cardlose", 0.4); ui.cgNote = `Only ${e.got} of the ${e.need} boxes the round needs - back to the start of the street.`; }
      else if (e.kind === "bundle") { ui.cgSfx("tablebell", 0.3, 1.3); ui.arcPts(fx, L.p.x, H - 90, "+8 SCROLLS", "#C0F0FF"); }
    },
    draw(p, L, now) {
      const sc = L ? L.scroll : (now / 20) % 600;
      p.fillStyle = "#5A7A3A"; p.fillRect(0, 0, 180, H); p.fillStyle = "#7A7068"; p.fillRect(176, 0, 14, H); p.fillStyle = "#5A5450"; p.fillRect(190, 0, W - 190, H);
      for (let y = -40 + (sc % 20); y < H; y += 20) for (let x = 190 + (Math.floor((y - sc) / 20) % 2 ? 10 : 0); x < W; x += 20) { p.fillStyle = "rgba(0,0,0,0.12)"; p.fillRect(x, y, 19, 1); p.fillRect(x, y, 1, 19); }
      p.fillStyle = "#3A3430"; p.fillRect(W - 12, 0, 12, H); p.fillStyle = "rgba(255,255,255,0.08)"; for (let y = (sc % 40) - 40; y < H; y += 40) p.fillRect(282, y, 4, 20);
      for (let y = (sc % 200) - 200; y < H; y += 200) { p.fillStyle = "rgba(255,220,140,0.12)"; p.beginPath(); p.arc(183, y + 60, 50, 0, Math.PI * 2); p.fill(); p.fillStyle = "#2A2420"; p.fillRect(181, y + 56, 4, 8); p.fillStyle = "#FFE0A0"; p.beginPath(); p.arc(183, y + 54, 3, 0, Math.PI * 2); p.fill(); }
      const houses = L ? L.houses : [0, 1, 2, 3, 4].map((k) => ({ y: -k * CO.houseGap + 300 + (sc % CO.houseGap), sub: k % 2 === 0, done: false, tint: k }));
      for (const h of houses) { const y = h.y + (L ? sc : 0); if (y > H + 20 || y < -140) continue;
        p.fillStyle = "rgba(0,0,0,0.3)"; p.fillRect(18, y + 8, 110, 96); p.fillStyle = "#C8B898"; p.fillRect(12, y + 4, 106, 92); p.fillStyle = ROOF[h.tint]; p.beginPath(); p.moveTo(8, y + 2); p.lineTo(122, y + 2); p.lineTo(108, y + 30); p.lineTo(22, y + 30); p.fill(); p.fillStyle = "rgba(0,0,0,0.2)"; p.fillRect(8, y + 26, 114, 4);
        for (const wx of [24, 82]) { p.fillStyle = h.sub ? "#FFD870" : "#3A3A48"; if (h.sub) { p.shadowColor = "#FFC040"; p.shadowBlur = 8; } p.fillRect(wx, y + 44, 20, 16); p.shadowBlur = 0; p.fillStyle = "#5A3A20"; p.fillRect(wx + 9, y + 44, 2, 16); }
        p.fillStyle = "#6A4020"; p.fillRect(56, y + 70, 18, 26); p.fillStyle = "#9A8A70"; p.fillRect(118, y + 82, 58, 8);
        if (h.sub) { const my = y + 50; p.fillStyle = "#4A3A2A"; p.fillRect(149, my, 3, 16); p.fillStyle = h.done ? "#3A70C0" : "#8A2A20"; p.fillRect(142, my - 8, 18, 11); p.fillStyle = "#101010"; p.fillRect(144, my - 4, 10, 2);
          if (h.done) { p.fillStyle = "#F0C040"; p.fillRect(159, my - 16, 2, 10); p.beginPath(); p.moveTo(161, my - 16); p.lineTo(168, my - 13 + Math.sin(now / 150)); p.lineTo(161, my - 10); p.fill(); } else if (Math.floor(now / 400) % 2) { p.strokeStyle = "rgba(255,230,120,0.6)"; p.strokeRect(140, my - 10, 22, 15); } } }
      if (L) { if (L.bundle) { const by = L.bundle.y + sc; p.fillStyle = "#E8DCC0"; for (let k = 0; k < 3; k++) p.fillRect(L.bundle.x - 8 + k * 3, by - 6 + k * 2, 14, 4); p.strokeStyle = "#A02020"; p.strokeRect(L.bundle.x - 9, by - 7, 18, 12); }
        for (const O of L.obs) { const x = O.x, y = O.y + sc;
          if (O.kind === "puddle") { p.fillStyle = "rgba(60,100,160,0.6)"; p.beginPath(); p.ellipse(x, y, 20, 10, 0, 0, Math.PI * 2); p.fill(); p.strokeStyle = "rgba(200,230,255,0.5)"; p.beginPath(); p.ellipse(x, y, 8 + (now / 60) % 10, 4 + (now / 120) % 5, 0, 0, Math.PI * 2); p.stroke(); }
          else if (O.kind === "dog") { const leg = Math.sin(now / 50) * 3, d = Math.sign(O.vx) || 1; p.fillStyle = "#8A5A30"; p.beginPath(); p.ellipse(x, y, 12, 6, 0, 0, Math.PI * 2); p.fill(); p.beginPath(); p.arc(x + 11 * d, y - 1, 5, 0, Math.PI * 2); p.fill(); p.fillRect(x - 8, y + 4 + leg, 3, 4); p.fillRect(x + 5, y + 4 - leg, 3, 4); p.fillStyle = "#101010"; p.fillRect(x + 14 * d, y - 2, 2, 2); }
          else if (O.kind === "cart") { p.fillStyle = "#7A5030"; p.fillRect(x - 16, y - 14, 32, 28); p.fillStyle = "#A07040"; p.fillRect(x - 13, y - 11, 26, 22); p.fillStyle = "#5A9A40"; for (let k = 0; k < 4; k++) { p.beginPath(); p.arc(x - 6 + (k % 2) * 12, y - 4 + Math.floor(k / 2) * 9, 4, 0, Math.PI * 2); p.fill(); } p.fillStyle = "#2A2020"; p.fillRect(x - 19, y - 8, 3, 16); p.fillRect(x + 16, y - 8, 3, 16); }
          else { p.save(); p.translate(x, y); p.rotate(now / 200); p.fillStyle = "#8A5A30"; p.fillRect(-10, -8, 20, 16); p.fillStyle = "#3A3030"; p.fillRect(-10, -6, 20, 2); p.fillRect(-10, 4, 20, 2); p.restore(); } }
        for (const F of L.flying) { p.save(); p.translate(F.x, F.y); p.rotate(F.t * 18); p.fillStyle = "#F0E6CC"; p.fillRect(-7, -2.5, 14, 5); p.fillStyle = "#A02020"; p.fillRect(-1, -3, 2, 6); p.restore(); }
        const P = L.p, py = H - 70; if (!(P.guard > 0 && Math.floor(now / 90) % 2)) { const bob = Math.sin(now / 90) * 1.5; p.fillStyle = "rgba(0,0,0,0.3)"; p.beginPath(); p.ellipse(P.x + 3, py + 4, 12, 20, 0, 0, Math.PI * 2); p.fill();
          p.fillStyle = P.dead ? "#606068" : "#A8A8B0"; p.beginPath(); p.ellipse(P.x, py, 9, 18, 0, 0, Math.PI * 2); p.fill(); p.beginPath(); p.ellipse(P.x, py - 20 + bob, 5, 7, 0, 0, Math.PI * 2); p.fill(); p.fillStyle = "#3A3030"; p.fillRect(P.x - 1, py - 14, 2, 8);
          p.fillStyle = "#3A6A3A"; p.beginPath(); p.arc(P.x, py + 1 + bob, 7, 0, Math.PI * 2); p.fill(); p.fillStyle = "#E0C090"; p.beginPath(); p.arc(P.x, py - 2 + bob, 4, 0, Math.PI * 2); p.fill(); p.fillStyle = "#8A5A30"; p.fillRect(P.x - 11, py - 2, 5, 9); }
        const k = Math.min(1, L.scroll / L.dist); p.fillStyle = "rgba(0,0,0,0.5)"; p.fillRect(W - 10, 10, 6, H - 20); p.fillStyle = "#F0C040"; p.fillRect(W - 9, 10 + (H - 20) * (1 - k), 4, (H - 20) * k); }
    },
  });
}
