"use strict";
// Curiosities - the window's side (UPGRADE_PLAN_73.md): the few that live in the window rather than the rules, and the
// pictures of the small things to find. Rules: 69zzzw-curios.js.
{ const S = 128, mk = (f) => { const c = document.createElement("canvas"); c.width = c.height = S; f(c.getContext("2d")); return c; };
  const P = { fluff: (p) => { p.fillStyle = "#8A8680"; for (let i = 0; i < 40; i++) { const a = i * 2.4, r = 18 + (i % 5) * 3; p.beginPath(); p.arc(64 + Math.cos(a) * r * 0.6, 96 + Math.sin(a) * r * 0.45, 10, 0, Math.PI * 2); p.fill(); } p.fillStyle = "#FFF"; p.fillRect(54, 88, 6, 6); p.fillRect(70, 88, 6, 6); p.fillStyle = "#111"; p.fillRect(56, 90, 3, 3); p.fillRect(72, 90, 3, 3); },
    duck: (p) => { p.fillStyle = "#F2C83A"; p.beginPath(); p.ellipse(60, 100, 30, 18, 0, 0, Math.PI * 2); p.fill(); p.beginPath(); p.arc(80, 76, 14, 0, Math.PI * 2); p.fill(); p.fillStyle = "#E8742A"; p.beginPath(); p.moveTo(92, 76); p.lineTo(106, 80); p.lineTo(92, 84); p.fill(); p.fillStyle = "#111"; p.fillRect(82, 70, 4, 4); },
    sock: (p) => { p.fillStyle = "#8A8A90"; p.beginPath(); p.moveTo(50, 40); p.lineTo(74, 40); p.lineTo(74, 92); p.quadraticCurveTo(74, 112, 96, 112); p.lineTo(96, 120); p.lineTo(52, 120); p.quadraticCurveTo(46, 104, 50, 92); p.closePath(); p.fill(); p.fillStyle = "#6E6E74"; p.fillRect(50, 40, 24, 8); p.fillStyle = "#A8706A"; p.fillRect(84, 112, 10, 6); } };
  { const b0 = CM.art.build; CM.art.build = function (theme, look) { const set = b0.call(this, theme, look); for (const [n, f] of Object.entries(P)) { set.index[`curio:${n}`] = set.layers.length; set.layers.push(mk(f)); } return set; }; }
  Object.assign(P, { odd: (p) => { const g = p.createRadialGradient(64, 92, 1, 64, 92, 30); g.addColorStop(0, "rgba(255,240,200,0.95)"); g.addColorStop(1, "rgba(255,200,120,0)"); p.fillStyle = g; p.fillRect(30, 60, 68, 64); p.fillStyle = "#6A5A48"; p.beginPath(); p.ellipse(64, 108, 18, 8, 0, 0, Math.PI * 2); p.fill(); },
    door: (p) => { p.fillStyle = "#3A2A1A"; p.fillRect(40, 30, 48, 96); p.fillStyle = "#3C6EA8"; p.beginPath(); p.moveTo(46, 124); p.lineTo(46, 52); p.quadraticCurveTo(64, 30, 82, 52); p.lineTo(82, 124); p.fill(); p.fillStyle = "#E8C850"; p.beginPath(); p.arc(76, 90, 3, 0, Math.PI * 2); p.fill(); } });
  CM.thingSprites = Object.assign(CM.thingSprites || {}, { oddity: (t, x, y, now) => [t.id === "door" ? { x, y, layer: "curio:door", w: 0.3, h: 0.3 } : { x, y, layer: "curio:odd", w: 0.32, h: 0.32, glow: 0.25 + 0.15 * Math.sin(now / 400 + x) }] });
  CM.thingSprites = Object.assign(CM.thingSprites || {}, { curio:(t, x, y, now) => [{ x, y, layer: `curio:${t.id}`, w: 0.3, h: 0.3, lift: t.id === "duck" ? Math.abs(Math.sin(now / 600)) * 0.01 : 0 }] });
  const egg = (id) => { const g = CM.game; if (g && g.curio) g.curio(id); };
  // the title card: a name typed at it; a long wait; the hour and the day
  let typed = "";
  window.addEventListener("keydown", (e) => { const sp = document.getElementById("splash"); if (!sp || sp.classList.contains("gone") || !e.key || e.key.length !== 1) return; typed = (typed + e.key.toLowerCase()).slice(-6);
    if (typed === "claude") { const h = sp.querySelector("h1"); if (h && !h.dataset.flipped) { h.dataset.flipped = "1"; const was = h.innerHTML; h.innerHTML = "<span>Magic and </span>Claude"; setTimeout(() => { h.innerHTML = was; delete h.dataset.flipped; }, 4000); egg("titlename"); } } }, true);
  const S0 = CM.SplashStage;
  if (S0) { const a0 = S0.prototype.actors; S0.prototype.actors = function (p, layer, t) { if (a0) a0.call(this, p, layer, t); if (layer !== "front" || !this.W || CM.reducedMotion) return;
      if (t > 180 && !this.wanderer) { this.wanderer = { t0: t }; egg("idle"); } const Wd = this.wanderer; if (!Wd) return; const k = (t - Wd.t0) / 40; if (k > 1) return;
      const W = this.W, H = this.H, x = -20 + k * (W + 40), y = H * 0.985 - 6, s = Math.max(0.6, H / 900), bob = Math.abs(Math.sin(t * 6)) * 2 * s;
      p.save(); p.fillStyle = "#1A120C"; p.fillRect(x - 4 * s, y - 22 * s - bob, 8 * s, 16 * s); p.beginPath(); p.arc(x, y - 26 * s - bob, 5 * s, 0, Math.PI * 2); p.fill(); p.beginPath(); p.moveTo(x - 7 * s, y - 29 * s - bob); p.lineTo(x, y - 42 * s - bob); p.lineTo(x + 7 * s, y - 29 * s - bob); p.fill();
      const g = p.createRadialGradient(x + 9 * s, y - 16 * s - bob, 1, x + 9 * s, y - 16 * s - bob, 16 * s); g.addColorStop(0, "rgba(255,200,110,0.9)"); g.addColorStop(1, "rgba(255,150,60,0)"); p.fillStyle = g; p.fillRect(x - 10 * s, y - 36 * s, 40 * s, 40 * s); p.restore(); }; }
  const tag = () => { const el = document.querySelector("#splash .tag"); if (!el || el.dataset.curio) return; const d = new Date(), h = d.getHours(), m = d.getMonth(), day = d.getDate();
    if (m === 3 && day === 1) { el.dataset.curio = "1"; el.textContent = "Seventy floors down, the Lich King waits - and today, so do several very convincing fake trapdoors"; egg("fools"); }
    else if (h === 0) { el.dataset.curio = "1"; el.textContent = "Seventy floors down, the Lich King waits - and at this hour, so does the scribe, with the lamp still lit"; egg("midnight"); } };
  { const ss0 = CM.UI.prototype.showSplash; if (ss0) CM.UI.prototype.showSplash = function (...a) { const out = ss0.apply(this, a); setTimeout(tag, 50); return out; }; }
}
