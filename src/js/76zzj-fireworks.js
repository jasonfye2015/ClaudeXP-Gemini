"use strict";
// Fireworks for the big wins (v16.2): when the floor has noticed a large prize (64zzj-draws.js queues it), the next
// time a table shows its result the sky over the Joker goes up - rockets whistle up from the bottom of the window
// trailing sparks and burst into peonies, rings, gold willows that droop and hang, palms, crossettes that split again,
// and now and then a heart; the glitter crackles after. A banner names the win. Three sizes: a big win (a few
// rockets), a huge one (a proper show) and a jackpot (a finale, a flash and a rain of gold). The sounds are made
// here: the whistle, the boom and the crackle. With reduced motion asked for, only the banner shows.
{ const r6 = CM.UI.prototype.renderCasino;
  const PAL = [["#FFD860", "#FFF4C0"], ["#FF5070", "#FFC0D0"], ["#60C0FF", "#D0F0FF"], ["#70F080", "#E0FFE0"], ["#C070FF", "#F0D0FF"], ["#FF9030", "#FFE0B0"], ["#FFFFFF", "#C0E0FF"]];
  const SHOW = { 1: { n: 4, over: 1.8, title: "BIG WIN!" }, 2: { n: 9, over: 3.2, title: "HUGE WIN!" }, 3: { n: 20, over: 5.5, title: "JACKPOT!" } };
  const sounds = () => { const A = CM.audio; if (!A || !A.ctx || A.buffers.fwboom) return; try {
      A.buffers.fwlaunch = A._buffer(A._mix(A._sweep(380, 1500, 0.7, "sine", 0.05, 0.1), A._noise(0.7, 0.04, 0.6, 211)));
      A.buffers.fwboom = A._buffer(A._mix(A._noise(0.9, 0.55, 0.25, 223), A._sweep(90, 30, 0.8, "sine", 0.4), A._after(0.06, A._noise(0.7, 0.18, 0.06, 227))));
      A.buffers.fwcrackle = A._buffer(A._mix(...Array.from({ length: 22 }, (_, i) => A._after(0.02 + ((i * 37) % 23) * 0.045, A._noise(0.025, 0.35, 0.9, 229 + i)))));
    } catch (e) { /* quiet */ } };
  Object.assign(CM.UI.prototype, {
    renderCasino() { const out = r6.call(this); this.cgFwFlush(); return out; },
    cgFwFlush() { const g = this.game; if (!this.cgBusy && g.fwQ && g.fwQ.length) { const q = g.fwQ.splice(0), tier = Math.max(...q.map((e) => e.tier)), text = [...new Set(q.map((e) => e.text))].slice(0, 3).join("  ·  "); setTimeout(() => this.cgFireworks(tier, text), 250); } },
    cgFireworks(tier, text) {
      tier = Math.max(1, Math.min(3, tier || 1)); const S = SHOW[tier], calm = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches; sounds();
      let host = document.querySelector(".fwlayer"); if (host) host.remove(); host = document.createElement("div"); host.className = `fwlayer fw${tier}`;
      host.innerHTML = `${calm ? "" : `<canvas></canvas>`}<div class="fwbanner"><b>${tier < 3 && /^Joker level/.test(text || "") ? "LEVEL UP!" : S.title}</b>${text ? `<span>${this.esc ? this.esc(text) : text}</span>` : ""}</div>`; document.body.appendChild(host);
      const life = (calm ? 2.6 : S.over + 2.8) * 1000; setTimeout(() => host.classList.add("out"), life - 600); setTimeout(() => host.remove(), life);
      if (calm) return; const cv = host.querySelector("canvas"), p = cv.getContext("2d"), dpr = Math.min(2, window.devicePixelRatio || 1); let W = 0, H = 0;
      const fit = () => { W = window.innerWidth; H = window.innerHeight; cv.width = W * dpr; cv.height = H * dpr; p.setTransform(dpr, 0, 0, dpr, 0, 0); }; fit();
      const rockets = [], sparks = [], R = Math.random, t0 = performance.now(), plan = [];
      for (let k = 0; k < S.n; k++) plan.push({ at: tier === 3 && k >= S.n - 6 ? S.over - 0.6 + R() * 0.5 : (k / S.n) * S.over + R() * 0.25 });
      plan.sort((a, b) => a.at - b.at); const sfx = (n, v, r) => this.cgSfx(n, v, r);
      const launch = () => { const x = W * (0.15 + R() * 0.7), top = H * (0.12 + R() * 0.3); rockets.push({ x, y: H + 6, vx: (W / 2 - x) * 0.04 + (R() - 0.5) * 30, vy: -Math.sqrt(2 * 520 * (H - top)), col: PAL[Math.floor(R() * PAL.length)], kind: ["peony", "peony", "ring", "willow", "palm", "crossette", "heart"][Math.floor(R() * (tier >= 2 ? 7 : 6))] }); sfx("fwlaunch", 0.25, 0.9 + R() * 0.3); };
      const burst = (r) => { const [c1, c2] = r.col, n = r.kind === "willow" ? 70 : r.kind === "ring" ? 48 : r.kind === "palm" ? 9 : 64 + tier * 12, sp = 150 + R() * 60 + tier * 15;
        sfx("fwboom", 0.35 + tier * 0.08, 0.8 + R() * 0.4); if (r.kind !== "palm") setTimeout(() => sfx("fwcrackle", 0.25, 1 + R() * 0.3), 500);
        for (let i = 0; i < n; i++) { const a = (i / n) * Math.PI * 2 + R() * 0.1; let vx, vy;
          if (r.kind === "ring") { vx = Math.cos(a) * sp; vy = Math.sin(a) * sp * 0.55; }
          else if (r.kind === "heart") { const t = a, hx = 16 * Math.pow(Math.sin(t), 3), hy = -(13 * Math.cos(t) - 5 * Math.cos(2 * t) - 2 * Math.cos(3 * t) - Math.cos(4 * t)); vx = hx * sp / 17; vy = hy * sp / 17; }
          else if (r.kind === "palm") { vx = Math.cos(a) * sp * 0.9; vy = Math.sin(a) * sp * 0.9 - 40; }
          else { const k = Math.pow(R(), 0.35); vx = Math.cos(a) * sp * k; vy = Math.sin(a) * sp * k; }
          sparks.push({ x: r.x, y: r.y, vx, vy, col: R() < 0.25 ? c2 : r.kind === "willow" ? "#FFC860" : c1, life: r.kind === "willow" ? 2.6 + R() : r.kind === "palm" ? 1.8 : 1.3 + R() * 0.6, age: 0, drag: r.kind === "willow" ? 1.6 : 0.9, grav: r.kind === "willow" ? 60 : 110, trail: [], w: r.kind === "palm" ? 3 : 2, split: r.kind === "crossette" && i % 6 === 0, glit: R() < 0.3 });
        }
        flash = Math.max(flash, 0.12 + tier * 0.05); };
      let flash = 0, prev = t0, gold = [];
      const frame = (now) => { if (!host.isConnected) return; const dt = Math.min(0.05, (now - prev) / 1000), t = (now - t0) / 1000; prev = now; if (W !== window.innerWidth || H !== window.innerHeight) fit();
        while (plan.length && plan[0].at <= t) { plan.shift(); launch(); }
        p.clearRect(0, 0, W, H); if (flash > 0) { p.fillStyle = `rgba(255,240,200,${flash})`; p.fillRect(0, 0, W, H); flash = Math.max(0, flash - dt * 0.8); }
        p.globalCompositeOperation = "lighter";
        for (let i = rockets.length - 1; i >= 0; i--) { const r = rockets[i]; r.vy += 520 * dt; r.x += r.vx * dt; r.y += r.vy * dt;
          for (let k = 0; k < 2; k++) sparks.push({ x: r.x + (R() - 0.5) * 3, y: r.y + 4, vx: (R() - 0.5) * 30, vy: 40 + R() * 40, col: "#FFD8A0", life: 0.45, age: 0, drag: 2, grav: 60, trail: [], w: 1.5 });
          p.fillStyle = "#FFF6D8"; p.beginPath(); p.arc(r.x, r.y, 2.4, 0, Math.PI * 2); p.fill(); if (r.vy >= -30) { rockets.splice(i, 1); burst(r); } }
        for (let i = sparks.length - 1; i >= 0; i--) { const s = sparks[i]; s.age += dt; if (s.age >= s.life) { if (s.split) for (let k = 0; k < 4; k++) { const a = (k * Math.PI) / 2 + 0.6; sparks.push({ x: s.x, y: s.y, vx: Math.cos(a) * 70, vy: Math.sin(a) * 70, col: s.col, life: 0.7, age: 0, drag: 1, grav: 90, trail: [], w: 1.6, glit: true }); } sparks.splice(i, 1); continue; }
          s.trail.push(s.x, s.y); if (s.trail.length > 12) s.trail.splice(0, 2); const d = Math.exp(-s.drag * dt); s.vx *= d; s.vy = s.vy * d + s.grav * dt; s.x += s.vx * dt; s.y += s.vy * dt;
          const k = 1 - s.age / s.life, a = s.glit && s.age > s.life * 0.5 ? (R() < 0.5 ? k : 0.1) : k; p.strokeStyle = s.col; p.globalAlpha = a * 0.55; p.lineWidth = s.w; p.beginPath(); p.moveTo(s.trail[0], s.trail[1]); for (let j = 2; j < s.trail.length; j += 2) p.lineTo(s.trail[j], s.trail[j + 1]); p.lineTo(s.x, s.y); p.stroke();
          p.globalAlpha = a; p.fillStyle = s.col; p.beginPath(); p.arc(s.x, s.y, s.w * 0.9, 0, Math.PI * 2); p.fill(); }
        // a jackpot rains gold
        if (tier === 3 && t < S.over + 1.5) { if (R() < 0.8) gold.push({ x: R() * W, y: -10, vy: 80 + R() * 120, r: R() * 6, spin: R() * 6 }); }
        p.globalCompositeOperation = "source-over"; p.globalAlpha = 1; gold = gold.filter((c) => { c.y += c.vy * dt; c.r += c.spin * dt; const w = Math.abs(Math.cos(c.r)) * 6 + 1; p.fillStyle = "#F0C040"; p.beginPath(); p.ellipse(c.x, c.y, w, 6, 0, 0, Math.PI * 2); p.fill(); p.fillStyle = "#FFF0A0"; p.fillRect(c.x - w * 0.3, c.y - 3, Math.max(1, w * 0.3), 3); return c.y < H + 10; });
        if (t < S.over + 4 || sparks.length || gold.length) requestAnimationFrame(frame); };
      requestAnimationFrame(frame);
    },
  });
}
