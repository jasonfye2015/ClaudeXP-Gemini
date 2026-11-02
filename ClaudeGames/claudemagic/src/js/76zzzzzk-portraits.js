"use strict";
// Living portraits (v31.2, UPGRADE_PLAN_26.md): the heroes on the party's cards blink now and then and glance aside;
// hurt, they bruise, and badly hurt they go pale; weary with hunger or in the heat they sweat; in the snow or the cold
// deep their faces frost at the edges. The eyes are found in each portrait once (the darkest spot each side of the
// upper face); a helmed face that shows none just doesn't blink. Redrawn ten times a second from the card's own
// picture; the fallen are left as they are.
{ const seen = new WeakMap();
  const findEyes = (src, S) => { try { const d = src.getContext("2d").getImageData(0, 0, S, S).data, lum = (x, y) => { const i = (y * S + x) * 4; return d[i + 3] < 128 ? 9 : (0.3 * d[i] + 0.59 * d[i + 1] + 0.11 * d[i + 2]) / 255; };
      const best = (x0, x1) => { let b = null; for (let y = Math.round(S * 0.3); y < Math.round(S * 0.58); y++) for (let x = x0; x < x1; x++) { const l = lum(x, y); if (!b || l < b.l) b = { x, y, l }; } return b; };
      const L = best(Math.round(S * 0.22), Math.round(S * 0.5)), R = best(Math.round(S * 0.5), Math.round(S * 0.78));
      if (!L || !R || L.l > 0.3 || R.l > 0.3 || Math.abs(L.y - R.y) > S * 0.08 || R.x - L.x < S * 0.12) return null;
      const lid = (e) => { const y = Math.max(0, e.y - Math.round(S * 0.08)), i = (y * S + e.x) * 4; return `rgb(${d[i]},${d[i + 1]},${d[i + 2]})`; };
      return [L, R].map((e) => ({ x: e.x, y: e.y, lid: lid(e) })); } catch (er) { return null; } };
  const state = (cv) => { let s = seen.get(cv); if (s) return s; const S = cv.width, base = document.createElement("canvas"); base.width = base.height = S; base.getContext("2d").drawImage(cv, 0, 0);
    s = { S, base, eyes: findEyes(base, S), blinkAt: performance.now() + 1500 + Math.random() * 4000, glanceAt: performance.now() + 4000 + Math.random() * 6000, glance: 0, glanceUntil: 0 }; seen.set(cv, s); return s; };
  const draw = (cv, h, game, now) => { const s = state(cv), S = s.S, p = cv.getContext("2d"), k = S / 44, r = h.max ? h.hp / h.max : 1;
    p.save(); p.clearRect(0, 0, S, S); p.filter = r < 0.3 ? "saturate(0.45) brightness(1.1)" : "none"; p.drawImage(s.base, 0, 0); p.filter = "none";
    if (s.eyes) { const blinking = now >= s.blinkAt && now < s.blinkAt + 130; if (now >= s.blinkAt + 130) s.blinkAt = now + 2200 + Math.random() * 4200;
      if (now >= s.glanceAt) { s.glance = Math.random() < 0.5 ? -1 : 1; s.glanceUntil = now + 700; s.glanceAt = now + 6000 + Math.random() * 7000; } const g = now < s.glanceUntil && !CM.reducedMotion ? s.glance : 0;
      const ew = Math.max(2, Math.round(S * 0.09)), eh = Math.max(2, Math.round(S * 0.07));
      for (const e of s.eyes) { if (!blinking && !g) continue; const x = e.x - ew / 2, y = e.y - eh / 2; p.fillStyle = e.lid; p.fillRect(x, y, ew, eh);
        if (blinking) { p.fillStyle = "rgba(0,0,0,0.35)"; p.fillRect(x, e.y, ew, Math.max(1, k)); }
        else p.drawImage(s.base, x, y, ew, eh, x + g * Math.max(1, k), y, ew, eh); } }
    if (r < 0.6) { const a = Math.min(0.55, (0.6 - r) * 1.3); p.fillStyle = `rgba(110,40,90,${a})`; p.beginPath(); p.ellipse(S * 0.33, S * 0.64, S * 0.08, S * 0.06, 0.3, 0, Math.PI * 2); p.fill();
      if (r < 0.35) { p.strokeStyle = `rgba(150,20,20,${a + 0.2})`; p.lineWidth = Math.max(1, k); p.beginPath(); p.moveTo(S * 0.62, S * 0.3); p.lineTo(S * 0.7, S * 0.42); p.stroke(); } }
    const fl = game.floor, th = fl ? CM.themeFor(fl.number) || {} : {}, R = CM.renderer || {};
    const hot = (R.screen && R.screen.heatAll > 0) || (game.hungerWord && game.hungerWord() === "Weary");
    if (hot) { const t = (now / 1400) % 1; p.fillStyle = "rgba(170,215,255,0.85)"; for (const [x, y0] of [[0.27, 0.28], [0.74, 0.32]]) { const y = S * (y0 + t * 0.12); p.beginPath(); p.moveTo(S * x, y - S * 0.04); p.quadraticCurveTo(S * x + S * 0.025, y, S * x, y + S * 0.02); p.quadraticCurveTo(S * x - S * 0.025, y, S * x, y - S * 0.04); p.fill(); } }
    const cold = (R.sky && (R.snow || 0) > 0.3) || (R.screen && R.screen.breath > 0);
    if (cold) { for (const [cx, cy] of [[0, 0], [S, 0], [0, S], [S, S]]) { const gr = p.createRadialGradient(cx, cy, 0, cx, cy, S * 0.55); gr.addColorStop(0, "rgba(225,240,255,0.75)"); gr.addColorStop(1, "rgba(225,240,255,0)"); p.fillStyle = gr; p.fillRect(0, 0, S, S); }
      p.fillStyle = "rgba(255,255,255,0.9)"; for (let i = 0; i < 6; i++) { const a = i * 1.7, x = (Math.cos(a) * 0.5 + 0.5) * S, y = (i % 2 ? 0.08 : 0.9) * S; p.fillRect(x, y, Math.max(1, k), Math.max(1, k)); } }
    p.restore(); };
  const tick = () => { const ui = CM.ui, game = ui && ui.game; if (!game || !game.party || ui.screen !== "play") return; const box = document.querySelector("#party"); if (!box) return; const now = performance.now();
    [...box.children].forEach((div, i) => { const h = game.party[i], cv = div.querySelector("canvas"); if (!h || !cv || h.hp <= 0) return; try { draw(cv, h, game, now); } catch (er) { /* a picture only */ } }); };
  if (typeof setInterval === "function" && typeof document !== "undefined" && document.querySelector) setInterval(tick, 100);
}
