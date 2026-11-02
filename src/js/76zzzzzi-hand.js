"use strict";
// A hand and a torch (v31.0, UPGRADE_PLAN_26.md): the front hero's hand at the foot of the view, holding the torch (or
// the lantern) up - it sways with the walk and lags a turn, the flame leans and gutters in the wind and burns smaller
// as the torch burns down, and the light is held low and covered when it is shaded (T). Not by daylight, not in a
// fight, not with no light. Drawn on its own canvas over the view, under the HUD.
{ let cv = null, ctx = null, lastDraw = 0, sway = 0, lag = 0, lastYaw = null, lower = 0;
  const make = () => { const view = document.querySelector("#view"), hud = document.querySelector("#view #hud"); if (!view || !hud) return false;
    cv = document.createElement("canvas"); cv.className = "hand"; cv.style.pointerEvents = "none"; view.insertBefore(cv, hud); ctx = cv.getContext("2d"); return true; };
  const skinOf = (game) => { const h = (game.party || []).find((p) => p.hp > 0); const k = h ? CM.hashSeed(h.name || "x") % 4 : 0; return ["#E2B48C", "#C99268", "#8E5A3A", "#F0C8A4"][k]; };
  const flame = (p, x, y, s, t, lean, size, gutter) => {
    const fl = (a, b) => Math.sin(t * a + b), wob = (0.5 + 0.5 * fl(13, 0)) * 0.25 + (0.5 + 0.5 * fl(29, 1)) * 0.15, h = s * 78 * size * (0.85 + wob) * (1 - gutter * 0.45), w = s * 22 * size * (1 + gutter * 0.3);
    p.save(); p.globalCompositeOperation = "lighter";
    const g0 = p.createRadialGradient(x, y - h * 0.3, 2, x, y - h * 0.3, h * 2.2); g0.addColorStop(0, "rgba(255,170,60,0.32)"); g0.addColorStop(1, "rgba(255,120,30,0)"); p.fillStyle = g0; p.beginPath(); p.arc(x, y - h * 0.3, h * 2.2, 0, Math.PI * 2); p.fill();
    for (const [k, c0, c1] of [[1, "rgba(255,90,20,0.85)", "rgba(200,40,10,0)"], [0.7, "rgba(255,170,50,0.95)", "rgba(255,110,20,0)"], [0.42, "rgba(255,250,210,1)", "rgba(255,210,120,0)"]]) {
      const hh = h * k, ww = w * k, tipX = x + lean * hh * 0.6 + fl(17, k * 3) * ww * 0.3, tipY = y - hh;
      const g = p.createLinearGradient(x, y, tipX, tipY); g.addColorStop(0, c0); g.addColorStop(1, c1); p.fillStyle = g;
      p.beginPath(); p.moveTo(x - ww, y); p.bezierCurveTo(x - ww * 1.1, y - hh * 0.45, tipX - ww * 0.3, tipY + hh * 0.25, tipX, tipY); p.bezierCurveTo(tipX + ww * 0.3, tipY + hh * 0.25, x + ww * 1.1, y - hh * 0.45, x + ww, y);
      p.quadraticCurveTo(x, y + ww * 0.6, x - ww, y); p.fill(); }
    p.restore(); };
  const draw = (game, r, dt) => {
    if (!cv && !make()) return; const view = cv.parentElement, W = view.clientWidth, H = view.clientHeight, dpr = Math.min(1.5, window.devicePixelRatio || 1);
    if (cv.width !== Math.round(W * dpr) || cv.height !== Math.round(H * dpr)) { cv.width = Math.round(W * dpr); cv.height = Math.round(H * dpr); }
    const p = ctx; p.setTransform(1, 0, 0, 1, 0, 0); p.clearRect(0, 0, cv.width, cv.height); p.setTransform(dpr, 0, 0, dpr, 0, 0);
    const L = game.light || {}, kind = L.kind, sky = r.sky, day = sky && sky.light > 0.35, show = game.mode === "explore" && (kind === "torch" || kind === "lantern") && !day && !(ui() && ui().dialogOpen && ui().dialogOpen());
    cv.style.display = show ? "" : "none"; lastDraw = performance.now(); if (!show) return;
    const t = r.time || 0, still = CM.reducedMotion, s = H / 560;
    const walking = r.move ? Math.sin(r.move.t * Math.PI) : 0; sway += ((walking ? 1 : 0) - sway) * Math.min(1, dt * 6);
    if (lastYaw !== null) { let dy = r.yaw - lastYaw; while (dy > Math.PI) dy -= Math.PI * 2; while (dy < -Math.PI) dy += Math.PI * 2; lag += (-dy * 260 - lag) * Math.min(1, dt * 10); } lastYaw = r.yaw; lag *= Math.pow(0.02, dt);
    lower += ((game.lightOut ? 1 : 0) - lower) * Math.min(1, dt * 5);
    const bobX = still ? 0 : Math.sin(t * 5.5) * 7 * s * sway + Math.sin(t * 0.9) * 2 * s, bobY = still ? 0 : Math.abs(Math.sin(t * 5.5)) * 9 * s * sway + Math.sin(t * 1.3) * 2 * s;
    const bx = W * 0.8 + bobX + (still ? 0 : lag * s), by = H - 34 * s + bobY + lower * 150 * s, ang = -0.22 + (still ? 0 : lag * 0.0009);
    p.save(); p.translate(bx, by); p.rotate(ang);
    const wind = sky && r.wind ? r.wind.k || 0 : 0, lean = still ? 0 : (wind * 0.8 + Math.sin(t * 1.7) * 0.08) * (1 - lower), burnt = kind === "torch" ? Math.max(0.45, Math.min(1, (L.left || 0) / 120)) : 1;
    const gutter = still ? 0 : Math.max(0, wind - 0.4) * (0.5 + 0.5 * Math.sin(t * 7.3) * Math.sin(t * 3.1));
    if (kind === "torch") { const top = -200 * s;
      p.fillStyle = "#5A3A20"; p.beginPath(); p.moveTo(-9 * s, 40 * s); p.lineTo(9 * s, 40 * s); p.lineTo(11 * s, top); p.lineTo(-11 * s, top); p.fill();
      p.fillStyle = "#3A2614"; p.fillRect(-14 * s, top - 4 * s, 28 * s, 26 * s); p.strokeStyle = "#2A1A0C"; p.lineWidth = 2 * s; for (let i = 0; i < 4; i++) { p.beginPath(); p.moveTo(-14 * s, top + i * 6 * s); p.lineTo(14 * s, top + 3 * s + i * 6 * s); p.stroke(); }
      if (lower < 0.6) flame(p, 0, top - 2 * s, s, t, lean, burnt * (1 - lower), gutter);
      else { p.fillStyle = "rgba(255,120,40,0.35)"; p.beginPath(); p.arc(0, top, 10 * s, 0, Math.PI * 2); p.fill(); } }
    else { const top = -150 * s;                                            // a lantern on its bail
      p.strokeStyle = "#2A2A2E"; p.lineWidth = 4 * s; p.beginPath(); p.moveTo(0, 20 * s); p.lineTo(0, top - 40 * s); p.stroke();
      p.fillStyle = "#2E2A26"; p.fillRect(-30 * s, top - 40 * s, 60 * s, 12 * s); p.fillRect(-26 * s, top + 40 * s, 52 * s, 10 * s);
      const g = p.createRadialGradient(0, top, 4, 0, top, 60 * s); g.addColorStop(0, `rgba(255,230,160,${1 - lower * 0.7})`); g.addColorStop(0.5, `rgba(255,170,70,${0.55 - lower * 0.4})`); g.addColorStop(1, "rgba(255,140,40,0)");
      p.fillStyle = "rgba(255,210,120,0.5)"; p.fillRect(-24 * s, top - 28 * s, 48 * s, 68 * s); p.save(); p.globalCompositeOperation = "lighter"; p.fillStyle = g; p.beginPath(); p.arc(0, top, 60 * s, 0, Math.PI * 2); p.fill(); p.restore();
      p.strokeStyle = "#2E2A26"; p.lineWidth = 4 * s; for (const x of [-24, 0, 24]) { p.beginPath(); p.moveTo(x * s, top - 28 * s); p.lineTo(x * s, top + 40 * s); p.stroke(); } }
    const skin = skinOf(game);                                              // the hand round the haft, the sleeve below
    p.fillStyle = "#3A2C24"; p.beginPath(); p.moveTo(-60 * s, 200 * s); p.lineTo(-34 * s, 30 * s); p.lineTo(40 * s, 34 * s); p.lineTo(70 * s, 200 * s); p.fill();
    p.fillStyle = "#4E3C30"; p.fillRect(-38 * s, 24 * s, 80 * s, 16 * s);
    p.fillStyle = skin; p.beginPath(); p.ellipse(2 * s, 0, 34 * s, 30 * s, 0, 0, Math.PI * 2); p.fill();
    p.fillStyle = "rgba(0,0,0,0.18)"; for (let i = 0; i < 4; i++) { p.beginPath(); p.ellipse(-16 * s + i * 11 * s, -14 * s, 6 * s, 9 * s, 0, 0, Math.PI * 2); p.fill(); }
    p.fillStyle = skin; p.beginPath(); p.ellipse(-28 * s, 6 * s, 10 * s, 18 * s, 0.6, 0, Math.PI * 2); p.fill();
    const lit = p.createRadialGradient(0, -120 * s, 10, 0, -120 * s, 200 * s); lit.addColorStop(0, `rgba(255,160,60,${0.28 * (1 - lower)})`); lit.addColorStop(1, "rgba(255,120,40,0)");
    p.save(); p.globalCompositeOperation = "source-atop"; p.fillStyle = lit; p.fillRect(-120 * s, -300 * s, 240 * s, 520 * s); p.restore();   // (the flame's light on the hand)
    p.restore(); };
  const ui = () => CM.ui;
  const bf0 = CM.beforeFrame; CM.beforeFrame = (game, r, dt, now) => { if (bf0) bf0(game, r, dt, now); try { draw(game, r, dt); } catch (er) { /* the hand is only a picture */ } };
  if (typeof setInterval === "function" && typeof document !== "undefined" && document.querySelector) setInterval(() => { if (cv && performance.now() - lastDraw > 250) cv.style.display = "none"; }, 300);   // (in the other places - the tower, the casino - it isn't drawn: out of sight)
}
