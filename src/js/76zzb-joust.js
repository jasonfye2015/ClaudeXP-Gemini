"use strict";
// Gryphon Joust, the window's side: a cavern over a lava lake - the lava heaving and glowing, bubbles bursting and a
// heat-shimmer of embers rising; floating ledges of dark stone with moss; the rider on a gryphon whose wings beat on
// each flap, the rivals on dun, crimson and shadow-black mounts with their lances couched; a rider unhorsed tumbles in
// sparks and leaves an egg that wobbles faster as it nears hatching. Left and right to steer, Space or Up to flap.
// The rules are 64zzf-arc2.js.
CM.CG_TABLES.push(["joust", "Gryphon Joust"]);
{ const GJ = CM.GJ, W = GJ.W, H = GJ.H, KIT = { me: ["#E0B040", "#3A6AD0"], bounder: ["#B08A60", "#C04030"], hunter: ["#909098", "#40A060"], shadow: ["#3A3048", "#9050E0"] };
  const rider = (p, o, kit, now, flap) => { const f = o.face || 1, beat = flap ? Math.sin(now / 40) : Math.sin(now / 260) * 0.3; p.save(); p.translate(o.x, o.y); p.scale(f, 1);
    p.fillStyle = kit[0]; p.beginPath(); p.ellipse(0, 4, 13, 7, 0, 0, Math.PI * 2); p.fill(); p.beginPath(); p.arc(12, -1, 5, 0, Math.PI * 2); p.fill(); p.fillStyle = "#F0C040"; p.beginPath(); p.moveTo(16, -2); p.lineTo(22, 0); p.lineTo(16, 2); p.fill(); p.fillStyle = "#101010"; p.fillRect(13, -3, 2, 2);
    p.fillStyle = kit[0]; p.beginPath(); p.moveTo(-12, 4); p.lineTo(-20, 0 + Math.sin(now / 120) * 2); p.lineTo(-18, 8); p.fill();
    p.fillStyle = "rgba(255,255,255,0.15)"; p.beginPath(); p.moveTo(-4, 0); p.lineTo(-14, -10 - beat * 12); p.lineTo(6, -2); p.fill(); p.fillStyle = kit[0]; p.globalAlpha = 0.85; p.beginPath(); p.moveTo(-2, 1); p.lineTo(-10, -12 - beat * 14); p.lineTo(8, 0); p.fill(); p.globalAlpha = 1;
    p.fillStyle = "#6A5040"; p.fillRect(-4, 9, 3, 6); p.fillRect(4, 9, 3, 6); p.fillStyle = kit[1]; p.fillRect(-3, -10, 8, 10); p.fillStyle = "#C8C8D0"; p.beginPath(); p.arc(1, -13, 4, 0, Math.PI * 2); p.fill(); p.fillStyle = kit[1]; p.fillRect(-1, -19, 4, 3);
    p.strokeStyle = "#D8C090"; p.lineWidth = 2; p.beginPath(); p.moveTo(-2, -5); p.lineTo(26, -9); p.stroke(); p.lineWidth = 1; p.fillStyle = "#E0E0E8"; p.beginPath(); p.moveTo(26, -11); p.lineTo(31, -9); p.lineTo(26, -7); p.fill(); p.restore(); };
  Object.assign(CM.ARC.reg.joust, {
    ui: { W, H, scale: 1.1, frame: "#4A1A10", start: "Mount up", go: "Wave 1 - hold the high air!", over: "Unhorsed for good", levelWord: "Wave",
      lore: "Below the Joker's cellars a cavern opens over a lake of fire, and riders on gryphons joust above it for the house's purse. \"Keep your lance higher than his,\" says the old ostler. \"And mind the eggs.\"",
      help: "Left and right to steer, Space or Up to flap. Meet a rival higher and he's unhorsed; lower and you are. Catch the egg he leaves before it hatches a worse rider. The lava takes anyone who sinks too low. Clear the wave to go on; an extra mount at 15,000.",
      keys: ["ArrowLeft", "ArrowRight", "KeyA", "KeyD", "Space", "ArrowUp", "KeyW"] },
    lifeIcon(p, x, y) { p.fillStyle = "#E0B040"; p.beginPath(); p.ellipse(x, y + 2, 6, 4, 0, 0, Math.PI * 2); p.fill(); p.beginPath(); p.moveTo(x - 2, y); p.lineTo(x - 6, y - 6); p.lineTo(x + 3, y); p.fill(); },
    input(L, held) { L.input((held.has("ArrowRight") || held.has("KeyD") ? 1 : 0) - (held.has("ArrowLeft") || held.has("KeyA") ? 1 : 0)); },
    press(L, code) { if (code === "Space" || code === "ArrowUp" || code === "KeyW") L.flap(); },
    event(ui, e, now, L, fx) {
      if (e.kind === "flap") ui.cgSfx("step", 0.15, 0.7); else if (e.kind === "arrive") { ui.cgSfx("door", 0.2, 1.4); }
      else if (e.kind === "unhorse") { ui.cgSfx("slam", 0.4, 1.3); ui.arcBurst(fx, e.x, e.y, ["#FFE070", "#FFFFFF", "#F08040"], 16, 150); ui.arcPts(fx, e.x, e.y - 20, `+${e.pts}`, "#FFE070"); fx.shake = 0.12; }
      else if (e.kind === "egg") { ui.cgSfx("coin", 0.35, 1.3); ui.arcPts(fx, e.x, e.y - 14, `+${e.pts}`, "#C0F0FF"); ui.arcBurst(fx, e.x, e.y, ["#F0F0E0", "#C0F0FF"], 8, 80); }
      else if (e.kind === "hatch") ui.cgSfx("hurt", 0.25, 1.6); else if (e.kind === "clash") ui.cgSfx("tablebell", 0.3, 0.9);
      else if (e.kind === "die") { ui.cgSfx("hurt", 0.45); ui.arcBurst(fx, e.x, e.y, ["#F06030", "#FFC040", "#FFFFFF"], 24, 180); fx.shake = 0.35; }
      else if (e.kind === "extra") { ui.cgSfx("cardwin", 0.4); ui.arcPts(fx, W / 2, H / 2, "EXTRA MOUNT", "#80FF80"); }
    },
    draw(p, L, now) {
      const sky = p.createLinearGradient(0, 0, 0, H); sky.addColorStop(0, "#140A14"); sky.addColorStop(0.7, "#3A1410"); sky.addColorStop(1, "#7A2A10"); p.fillStyle = sky; p.fillRect(0, 0, W, H);
      p.fillStyle = "#1E1018"; p.beginPath(); p.moveTo(0, 0); for (let x = 0; x <= W; x += 24) p.lineTo(x, 14 + 12 * Math.abs(Math.sin(x * 0.07))); p.lineTo(W, 0); p.fill();
      for (let k = 0; k < 18; k++) { const t = (now / 3000 + k * 0.13) % 1, x = (k * 97 + Math.sin(now / 700 + k) * 10) % W; p.fillStyle = `rgba(255,${120 + k * 5},40,${0.6 * (1 - t)})`; p.fillRect(x, GJ.lava - t * 260, 2, 2); }
      for (const [px, py, pw] of GJ.PLAT) { const g = p.createLinearGradient(0, py, 0, py + 14); g.addColorStop(0, "#5A5060"); g.addColorStop(1, "#2A2230"); p.fillStyle = g; p.beginPath(); p.moveTo(px, py); p.lineTo(px + pw, py); p.lineTo(px + pw - 8, py + 10); p.lineTo(px + pw / 2, py + 18); p.lineTo(px + 8, py + 10); p.fill(); p.fillStyle = "#4A7A3A"; p.fillRect(px + 2, py - 2, pw - 4, 3);
        p.fillStyle = "rgba(255,120,40,0.18)"; p.fillRect(px + 6, py + 12, pw - 12, 3); }
      if (L) { for (const E of L.eggs) { const wob = Math.sin(now / (E.t < 2 ? 50 : 160)) * (E.t < 2 ? 0.35 : 0.12); p.save(); p.translate(E.x, E.y); p.rotate(wob); p.fillStyle = "#F0ECD8"; p.beginPath(); p.ellipse(0, 0, 5, 7, 0, 0, Math.PI * 2); p.fill(); p.fillStyle = KIT[E.kind][1]; p.fillRect(-3, -1, 2, 2); p.fillRect(1, 2, 2, 2); p.restore(); }
        for (const F of L.foes) rider(p, F, KIT[F.kind], now, F.vy < -40);
        const P = L.p; if (!P.dead && !(P.guard > 0 && Math.floor(now / 90) % 2)) rider(p, P, KIT.me, now, P.flapT > 0); }
      const lv = p.createLinearGradient(0, GJ.lava, 0, H); lv.addColorStop(0, "#FFB030"); lv.addColorStop(0.3, "#F05010"); lv.addColorStop(1, "#801000"); p.fillStyle = lv; p.beginPath(); p.moveTo(0, H); for (let x = 0; x <= W; x += 10) p.lineTo(x, GJ.lava + 6 + Math.sin(x / 26 + now / 400) * 3 + Math.sin(x / 9 + now / 230) * 1.5); p.lineTo(W, H); p.fill();
      for (let k = 0; k < 5; k++) { const t = (now / 900 + k * 0.37) % 1, x = (k * 113 + 40) % W; p.strokeStyle = `rgba(255,220,120,${1 - t})`; p.beginPath(); p.arc(x, GJ.lava + 12, 2 + t * 6, Math.PI, 0); p.stroke(); }
    },
  });
}
