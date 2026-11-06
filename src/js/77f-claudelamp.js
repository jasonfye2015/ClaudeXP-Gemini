"use strict";
// The lamp in the trees (UPGRADE_PLAN_70.md, release 3): once the party has found Claude's cabin, the title card's tree
// line has a small lit window low among the trunks on the right - a roof's edge, a warm square that flickers, a thread
// of smoke. Drawn behind the trees, so they cross it. Rules: 69zzzo-twoclaudes.js.
{ const S = CM.SplashStage;
  const found = () => { try { const v = CM.store.get("village", null); return Boolean(v && v.ext && v.ext.claude && v.ext.claude.met); } catch (e) { return false; } };
  if (S) { const a0 = S.prototype.actors; S.prototype.actors = function (p, layer, t) { if (a0) a0.call(this, p, layer, t);
      if (layer !== "behind" || !this.W) return; if (this.claudeLamp === undefined) this.claudeLamp = found(); if (!this.claudeLamp) return;
      const W = this.W, H = this.H, base = H * 0.985, x = W * 0.86, s = Math.max(0.6, Math.min(1.4, H / 800)), y = base - 26 * s, flick = CM.reducedMotion ? 0.9 : 0.82 + 0.12 * Math.sin(t * 7.3) + 0.06 * Math.sin(t * 13.1);
      p.save(); p.fillStyle = "#140E0A"; p.fillRect(x - 30 * s, y - 6 * s, 60 * s, 32 * s); p.beginPath(); p.moveTo(x - 36 * s, y - 4 * s); p.lineTo(x, y - 26 * s); p.lineTo(x + 36 * s, y - 4 * s); p.fill(); p.fillRect(x + 14 * s, y - 34 * s, 8 * s, 18 * s);
      const g = p.createRadialGradient(x - 8 * s, y + 6 * s, 1, x - 8 * s, y + 6 * s, 34 * s); g.addColorStop(0, `rgba(255,190,90,${0.45 * flick})`); g.addColorStop(1, "rgba(255,150,60,0)"); p.fillStyle = g; p.fillRect(x - 44 * s, y - 28 * s, 72 * s, 70 * s);
      p.fillStyle = `rgba(255,${Math.round(196 + 30 * flick)},120,${flick})`; p.fillRect(x - 14 * s, y + 1 * s, 12 * s, 10 * s); p.fillStyle = "#140E0A"; p.fillRect(x - 8.6 * s, y + 1 * s, 1.2 * s, 10 * s);
      if (!CM.reducedMotion) { p.fillStyle = "rgba(170,160,150,0.18)"; for (let i = 0; i < 6; i++) { const k = (t * 0.25 + i / 6) % 1; p.beginPath(); p.arc(x + 18 * s + Math.sin(t + i) * 6 * s * k, y - 36 * s - k * 60 * s, (3 + 8 * k) * s, 0, Math.PI * 2); p.fill(); } }
      p.restore(); }; }
}
