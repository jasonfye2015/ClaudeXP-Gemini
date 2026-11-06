"use strict";
// The title card as a weather show (UPGRADE_PLAN_68.md, release 1): a stage painted in code under the card's words,
// anchored to them (measured after layout, so it holds at any window size). Over "Claude" a falling star strikes just
// above the word - a streak, a flash that lights the letters, a shake, sparks and a ring of dust - and leaves a chunk of
// meteor iron on the crater's lip, glowing and cooling and steaming. Over "and" a storm: a cloud, rain, and a lightning
// fork every few seconds that lights the card, thunder a beat after. Over "Magic" a tornado, nearly still, swirling,
// with grit and leaves on its orbits and flung from its top. Below, behind the drifting lines, a dense tree line
// dressed by the real season, bending in the gusts and leaning toward the funnel. The sky behind keeps the hour, as
// before. Under reduced motion the card is a still picture of all of it. Sound only where the page may play it.
{ const TAU = Math.PI * 2;
  const rand = (a, b) => a + Math.random() * (b - a);
  // ---- sound: synthesised here, like the meteors' rumble (76zzzzzzzzzzk-meteors.js) ----
  const noiseHit = (secs, low, vol, attack = 0.005) => { const A = CM.audio; if (!A || !A.ctx || !A.enabled || !A.master) return; try { const ctx = A.ctx, rate = ctx.sampleRate, n = Math.floor(rate * secs), buf = ctx.createBuffer(1, n, rate), d = buf.getChannelData(0); let last = 0;
      for (let i = 0; i < n; i++) { const t = i / rate, white = Math.random() * 2 - 1; last = last * low + white * (1 - low); const env = Math.min(1, t / attack) * Math.exp(-t * 3.2 / secs) * (1 + 0.5 * Math.sin(t * 9) * Math.exp(-t)); d[i] = last * env * 3.2; }
      const src = ctx.createBufferSource(), g = ctx.createGain(); src.buffer = buf; g.gain.value = vol; src.connect(g); g.connect(A.master); src.start(); } catch (e) { /* (quiet) */ } };
  const thunder = (near) => noiseHit(near ? 3.2 : 4.5, near ? 0.94 : 0.975, near ? 0.9 : 0.55, near ? 0.004 : 0.25);
  const crack = () => { noiseHit(0.35, 0.6, 0.8); setTimeout(() => noiseHit(3.6, 0.975, 0.75, 0.05), 60); };
  // ---- the season's trees ----
  const season = () => { const m = new Date().getMonth(); return m <= 1 || m === 11 ? "winter" : m <= 4 ? "spring" : m <= 7 ? "summer" : "autumn"; };
  const LEAF = { spring: ["#24402A", "#2E4C30", "#C89AAA"], summer: ["#1C3420", "#244026", "#2C4A2C"], autumn: ["#5C3418", "#6E421E", "#4A2812"], winter: ["#1C2A26", "#24322E", "#D8E0E8"] };   /* (dusk: the trees are a dark line, the words are the light) */
  const makeTrees = (W, H) => { const out = [], n = Math.ceil(W / 26) + 6; for (let i = 0; i < n; i++) { const depth = i % 3, x = (i / n) * (W + 80) - 40 + rand(-10, 10), h = (depth === 0 ? 0.22 : depth === 1 ? 0.17 : 0.13) * H * rand(0.8, 1.15);
      out.push({ x, h, w: h * rand(0.32, 0.46), pine: Math.random() < 0.45, depth, phase: rand(0, TAU), shade: [0.55, 0.75, 1][depth] }); }
    return out.sort((a, b) => a.depth - b.depth); };
  // ---- the stage ----
  const Stage = function (splash) { this.el = splash; this.t0 = performance.now(); this.parts = []; this.debris = []; this.bolt = null; this.flash = 0; this.nextBolt = 2.6; this.star = null; this.nextStar = 1.2; this.ore = null; this.gust = 0; this.season = season();
    const c = this.canvas = document.createElement("canvas"); c.className = "sp-wx"; splash.insertBefore(c, splash.querySelector(".splashcard")); this.p = c.getContext("2d"); this.resize(); this.onResize = () => this.resize(); window.addEventListener("resize", this.onResize); };
  Stage.prototype.resize = function () { const W = this.W = this.el.clientWidth || window.innerWidth, H = this.H = this.el.clientHeight || window.innerHeight; this.canvas.width = W; this.canvas.height = H; this.trees = makeTrees(W, H); this.words = null; };
  // the three words' boxes, from the forged letters (Claude: the first six; and: the next three; Magic: the last five)
  Stage.prototype.measure = function () { const L = [...this.el.querySelectorAll("h1 .fl")]; if (L.length < 14) return null; const box = (a, b) => { const R = L.slice(a, b).map((e) => e.getBoundingClientRect()); const host = this.el.getBoundingClientRect(); const x0 = Math.min(...R.map((r) => r.left)), x1 = Math.max(...R.map((r) => r.right)), y0 = Math.min(...R.map((r) => r.top)), y1 = Math.max(...R.map((r) => r.bottom)); return { x0: x0 - host.left, x1: x1 - host.left, y0: y0 - host.top, y1: y1 - host.top, cx: (x0 + x1) / 2 - host.left, letters: L.slice(a, b) }; };
    const w = { claude: box(0, 6), and: box(6, 9), magic: box(9, 14) }; return w.claude.x1 > w.claude.x0 ? w : null; };
  Stage.prototype.lightLetters = function (word, cls, ms) { for (const e of (this.words && this.words[word] ? this.words[word].letters : [])) { e.classList.remove(cls); void e.offsetWidth; e.classList.add(cls); setTimeout(() => e.classList.remove(cls), ms); } };
  // a lightning fork: a jagged path with a branch or two
  const fork = (x0, y0, x1, y1) => { const path = [[x0, y0]], steps = 12; for (let i = 1; i <= steps; i++) { const t = i / steps; path.push([x0 + (x1 - x0) * t + (i < steps ? rand(-18, 18) : 0), y0 + (y1 - y0) * t]); }
    const branches = []; for (let b = 0; b < 2; b++) { const at = path[3 + Math.floor(Math.random() * 6)], len = rand(30, 70), dir = Math.random() < 0.5 ? -1 : 1, br = [at.slice()]; for (let i = 1; i <= 4; i++) br.push([at[0] + dir * len * i / 4 + rand(-6, 6), at[1] + len * 0.7 * i / 4]); branches.push(br); }
    return { path, branches }; };
  Stage.prototype.step = function (dt, now) { const W = this.W, H = this.H, w = this.words, t = (now - this.t0) / 1000; if (this.cast && w) this.cast(dt, t); this.gust = 0.5 + 0.5 * Math.sin(t * 0.7) * Math.sin(t * 0.23 + 1);
    if (!w) return;
    // the star
    if (!this.star && t > this.nextStar) { const big = !this.ore, tx = w.claude.cx + (big ? 0 : rand(-140, 140)), ty = w.claude.y0 - (big ? 34 : rand(120, 200)); this.star = { x: tx + (big ? 260 : 160), y: -40, tx, ty, t: 0, dur: big ? 0.7 : 0.9, big }; this.nextStar = t + 40 + rand(0, 15); }
    if (this.star) { const s = this.star; s.t += dt; const k = Math.min(1, s.t / s.dur); s.cx = s.x + (s.tx - s.x) * k * k; s.cy = s.y + (s.ty - s.y) * k * k; if (Math.random() < 0.9) this.parts.push({ kind: "ember", x: s.cx + rand(-3, 3), y: s.cy + rand(-3, 3), vx: rand(-20, 20), vy: rand(-30, 10), life: rand(0.4, 0.9), age: 0, size: rand(1.5, 3) });
      if (k >= 1) { this.flash = Math.max(this.flash, s.big ? 0.9 : 0.35); if (s.big) { this.ore = { x: s.tx, y: s.ty, t: 0 }; this.lightLetters("claude", "wx-lit", 900); const shk = this.el.querySelector(".shk"); if (shk && !CM.reducedMotion) { shk.classList.remove("cshake"); void shk.offsetWidth; shk.classList.add("cshake"); } crack(); }
        for (let i = 0; i < (s.big ? 46 : 18); i++) { const a = -Math.PI * rand(0.05, 0.95), v = rand(60, s.big ? 280 : 150); this.parts.push({ kind: i % 3 ? "spark" : "rock", x: s.tx, y: s.ty, vx: Math.cos(a) * v, vy: Math.sin(a) * v, life: rand(0.6, 1.4), age: 0, size: rand(1.5, 3.5), grav: 380 }); }
        this.parts.push({ kind: "ring", x: s.tx, y: s.ty, life: 1.1, age: 0, r: 4, big: s.big }); this.star = null; } }
    if (this.ore) { this.ore.t += dt; if (Math.random() < dt * 3) this.parts.push({ kind: "steam", x: this.ore.x + rand(-8, 8), y: this.ore.y - 8, vx: rand(-4, 4), vy: rand(-22, -12), life: rand(1.6, 2.6), age: 0, size: rand(5, 9) }); }
    // the storm over "and": rain, and a fork now and then
    const cloudY = w.and.y0 - 150; const rate = 260 * (0.55 + 0.45 * this.gust), lean = 40;
    for (let i = 0; i < rate * dt; i++) this.parts.push({ kind: "rain", x: rand(w.and.x0 - 70, w.and.x1 + 70), y: cloudY + rand(0, 20), vx: lean, vy: rand(520, 640), life: 2, age: 0, stop: w.and.y0 - 6 });
    if (t > this.nextBolt) { const em = this.el.querySelector(".forge .emblem"), host = this.el.getBoundingClientRect(), er = em ? em.getBoundingClientRect() : null, ex0 = er ? er.left - host.left - 14 : w.and.cx - 60, ex1 = er ? er.right - host.left + 14 : w.and.cx + 60, fx = Math.random() < 0.5 ? rand(Math.min(ex0 - 60, w.and.x0 - 40), ex0) : rand(ex1, Math.max(ex1 + 60, w.and.x1 + 40));   /* (either side of the emblem, which stands under the storm) */ this.bolt = Object.assign(fork(fx + rand(-30, 30), cloudY + 18, fx, w.and.y0 - 8), { age: 0, life: 0.32 }); this.flash = Math.max(this.flash, 0.55); this.lightLetters("and", "wx-bolt", 380); if (this.onBolt) this.onBolt(); const near = Math.random() < 0.5; setTimeout(() => thunder(near), near ? 260 : 900); this.nextBolt = t + rand(6, 11); }
    if (this.bolt) { this.bolt.age += dt; if (this.bolt.age > this.bolt.life) this.bolt = null; }
    // the tornado over "Magic": debris on its orbits, flung from the top
    const tx = w.magic.cx + Math.sin(t * 0.4) * 8, top = Math.max(70, w.magic.y0 - 210), foot = w.magic.y0 - 10;
    while (this.debris.length < 46) this.debris.push({ h: Math.random(), a: rand(0, TAU), sp: rand(2.2, 4.2), leaf: Math.random() < 0.4, size: rand(1.5, 3.5) });
    for (const d of this.debris) { d.a += d.sp * dt * (1.4 - d.h * 0.6); d.h += dt * rand(0.03, 0.09); if (d.h > 1) { this.parts.push({ kind: d.leaf ? "leaf" : "grit", x: tx + Math.cos(d.a) * 70, y: top, vx: Math.cos(d.a) * 140, vy: rand(-40, 10), life: rand(1.2, 2), age: 0, size: d.size, grav: 60, spin: rand(-6, 6) }); d.h = 0; d.a = rand(0, TAU); } }
    this.tornado = { x: tx, top, foot, t };
    // the particles
    this.parts = this.parts.filter((p) => { p.age += dt; if (p.age > p.life) return false; if (p.kind === "ring") { p.r += dt * (p.big ? 160 : 90); return true; } p.vy += (p.grav || 0) * dt; p.x += (p.vx || 0) * dt; p.y += (p.vy || 0) * dt; if (p.kind === "rain" && p.y >= p.stop) { if (Math.random() < 0.25) this.parts.push({ kind: "splash", x: p.x, y: p.stop, life: 0.18, age: 0 }); return false; } return p.y < H + 20 && p.x > -40 && p.x < W + 40; });
    if (this.parts.length > 1400) this.parts.splice(0, this.parts.length - 1400);
    this.flash = Math.max(0, this.flash - dt * 2.4); };
  Stage.prototype.draw = function (now) { const p = this.p, W = this.W, H = this.H, w = this.words, t = (now - this.t0) / 1000; p.clearRect(0, 0, W, H);
    // the tree line, behind everything on the card's lower part
    const base = H * 0.985, lean = this.tornado ? this.tornado.x : W / 2, L = LEAF[this.season], snow = this.season === "winter";
    if (this.actors) this.actors(p, "behind", t);   /* (77c-splashfoes.js: what walks behind the trees) */
    for (const tr of this.trees) { const sway = (Math.sin(t * 1.3 + tr.phase) * 0.03 + this.gust * 0.05 * (tr.x < lean ? 1 : -1) * Math.max(0, 1 - Math.abs(tr.x - lean) / (W * 0.6))) * (CM.reducedMotion ? 0 : 1), sx = tr.x, top = base - tr.h, dark = tr.shade;
      p.save(); p.translate(sx, base); p.rotate(sway); p.translate(-sx, -base); p.globalAlpha = 0.5 + 0.35 * dark;
      p.fillStyle = "#1C140E"; p.fillRect(sx - tr.w * 0.05, base - tr.h * 0.35, tr.w * 0.1, tr.h * 0.35);
      if (tr.pine) { for (let k = 0; k < 4; k++) { const y = top + tr.h * 0.18 * k, ww = tr.w * (0.32 + k * 0.18); p.fillStyle = L[(k + tr.depth) % 2]; p.beginPath(); p.moveTo(sx, y); p.lineTo(sx - ww / 2, y + tr.h * 0.3); p.lineTo(sx + ww / 2, y + tr.h * 0.3); p.closePath(); p.fill(); if (snow) { p.fillStyle = "rgba(240,244,250,0.85)"; p.beginPath(); p.moveTo(sx, y); p.lineTo(sx - ww * 0.22, y + tr.h * 0.08); p.lineTo(sx + ww * 0.22, y + tr.h * 0.08); p.closePath(); p.fill(); } } }
      else { for (let k = 0; k < 4; k++) { p.fillStyle = L[k % 2]; p.beginPath(); p.ellipse(sx + Math.cos(k * 1.7) * tr.w * 0.18, top + tr.h * 0.25 + Math.sin(k * 2.3) * tr.h * 0.08, tr.w * 0.34, tr.h * 0.24, 0, 0, TAU); p.fill(); }
        if (L[2] && (this.season === "spring" || snow)) { p.fillStyle = L[2]; for (let k = 0; k < 6; k++) p.fillRect(sx + Math.cos(k * 2.1 + tr.phase) * tr.w * 0.3, top + tr.h * (0.12 + 0.05 * k), 2.2, 2.2); } }
      p.restore(); }
    const fade = p.createLinearGradient(0, base - H * 0.26, 0, H); fade.addColorStop(0, "rgba(12,9,6,0)"); fade.addColorStop(0.55, "rgba(12,9,6,0.25)"); fade.addColorStop(1, "rgba(12,9,6,0.7)"); p.fillStyle = fade; p.fillRect(0, base - H * 0.26, W, H * 0.26 + 20);   /* (darker toward the floor, no edge at the top) */
    if (this.actors) this.actors(p, "front", t);
    if (!w) return;
    // the storm's cloud
    const cloudY = w.and.y0 - 150; for (let k = 0; k < 11; k++) { const cx = w.and.x0 - 70 + (w.and.x1 - w.and.x0 + 140) * k / 10, r = 34 + 14 * Math.sin(k * 1.9 + t * 0.4) + (k % 2) * 10; const g = p.createRadialGradient(cx, cloudY, 4, cx, cloudY, r * 1.35); const lit = this.flash * 120 | 0; g.addColorStop(0, `rgba(${46 + lit},${50 + lit},${64 + lit},0.95)`); g.addColorStop(0.6, `rgba(${34 + lit},${38 + lit},${50 + lit},0.75)`); g.addColorStop(1, "rgba(30,34,46,0)"); p.fillStyle = g; p.beginPath(); p.arc(cx, cloudY, r, 0, TAU); p.fill(); }
    if (this.actors) this.actors(p, "cloud", t);
    // the tornado: stacked whirling bands hanging from its own dark cloud, a dark core, and its debris
    const T = this.tornado; if (T) { for (let k = 0; k < 9; k++) { const cx = T.x - 120 + 240 * k / 8, cy = T.top - 14 + Math.sin(k * 2.3) * 8, r = 40 + (k % 3) * 12; const g = p.createRadialGradient(cx, cy, 4, cx, cy, r); g.addColorStop(0, "rgba(38,36,40,0.92)"); g.addColorStop(1, "rgba(38,36,40,0)"); p.fillStyle = g; p.beginPath(); p.arc(cx, cy, r, 0, TAU); p.fill(); } const n = 22; for (let i = n; i >= 0; i--) { const h = i / n, y = T.foot + (T.top - T.foot) * h, r = 8 + h * h * 74 + Math.sin(T.t * 2 + i) * 3, wob = Math.sin(T.t * 1.7 + h * 5) * 10 * h; p.fillStyle = `rgba(${48 + h * 20},${44 + h * 18},${40 + h * 16},${0.18 + 0.2 * (1 - h)})`; p.beginPath(); p.ellipse(T.x + wob, y, r, r * 0.22, 0, 0, TAU); p.fill();
        p.strokeStyle = `rgba(170,160,140,${0.12 + 0.1 * Math.sin(T.t * 6 + i)})`; p.lineWidth = 1.2; p.beginPath(); p.ellipse(T.x + wob, y, r * 0.9, r * 0.2, 0, (T.t * 3 + i) % TAU, (T.t * 3 + i) % TAU + 2.2); p.stroke(); }
      for (const d of this.debris) { const y = T.foot + (T.top - T.foot) * d.h, r = 10 + d.h * d.h * 74, x = T.x + Math.cos(d.a) * r + Math.sin(T.t * 1.7 + d.h * 5) * 10 * d.h, z = Math.sin(d.a); p.fillStyle = d.leaf ? LEAF[this.season][1] : `rgba(120,110,96,${0.6 + 0.4 * z})`; p.fillRect(x, y + z * r * 0.2, d.size * (z > 0 ? 1.2 : 0.8), d.size * (z > 0 ? 1.2 : 0.8)); }
      const dust = p.createRadialGradient(T.x, T.foot, 2, T.x, T.foot, 60); dust.addColorStop(0, "rgba(130,118,100,0.35)"); dust.addColorStop(1, "rgba(130,118,100,0)"); p.fillStyle = dust; p.beginPath(); p.ellipse(T.x, T.foot, 60, 14, 0, 0, TAU); p.fill(); }
    if (this.actors) this.actors(p, "sky", t);
    // the particles
    for (const q of this.parts) { const k = 1 - q.age / q.life;
      if (q.kind === "rain") { p.strokeStyle = "rgba(180,200,230,0.6)"; p.lineWidth = 1.2; p.beginPath(); p.moveTo(q.x, q.y); p.lineTo(q.x - q.vx * 0.02, q.y - q.vy * 0.022); p.stroke(); }
      else if (q.kind === "splash") { p.strokeStyle = `rgba(190,210,235,${k * 0.6})`; p.beginPath(); p.arc(q.x, q.y, 3 * (1 - k) + 1, Math.PI, TAU); p.stroke(); }
      else if (q.kind === "spark" || q.kind === "ember") { p.fillStyle = `rgba(255,${180 + 60 * k | 0},${80 * k | 0},${k})`; p.fillRect(q.x, q.y, q.size, q.size); }
      else if (q.kind === "rock") { p.fillStyle = `rgba(70,60,52,${k})`; p.fillRect(q.x, q.y, q.size + 1, q.size + 1); }
      else if (q.kind === "steam") { const g = p.createRadialGradient(q.x, q.y, 0, q.x, q.y, q.size + 6 * (1 - k)); g.addColorStop(0, `rgba(220,220,225,${0.22 * k})`); g.addColorStop(1, "rgba(220,220,225,0)"); p.fillStyle = g; p.beginPath(); p.arc(q.x, q.y, q.size + 6 * (1 - k), 0, TAU); p.fill(); }
      else if (q.kind === "ring") { p.strokeStyle = `rgba(200,180,150,${k * 0.6})`; p.lineWidth = 3 * k + 1; p.beginPath(); p.ellipse(q.x, q.y, q.r, q.r * 0.3, 0, 0, TAU); p.stroke(); }
      else if (q.kind === "leaf" || q.kind === "grit") { p.fillStyle = q.kind === "leaf" ? LEAF[this.season][0] : "rgba(110,100,88,0.8)"; p.save(); p.translate(q.x, q.y); p.rotate(q.age * (q.spin || 0)); p.fillRect(-q.size, -q.size / 2, q.size * 2, q.size); p.restore(); } }
    // the falling star
    if (this.star) { const s = this.star, dx = s.x - s.cx, dy = s.y - s.cy, len = Math.hypot(dx, dy) || 1, tail = Math.min(len, s.big ? 180 : 110), g = p.createLinearGradient(s.cx, s.cy, s.cx + dx / len * tail, s.cy + dy / len * tail); g.addColorStop(0, "rgba(255,240,200,1)"); g.addColorStop(0.2, "rgba(255,170,60,0.8)"); g.addColorStop(1, "rgba(255,90,20,0)"); p.strokeStyle = g; p.lineWidth = s.big ? 5 : 3; p.lineCap = "round"; p.beginPath(); p.moveTo(s.cx, s.cy); p.lineTo(s.cx + dx / len * tail, s.cy + dy / len * tail); p.stroke(); const head = p.createRadialGradient(s.cx, s.cy, 0, s.cx, s.cy, s.big ? 16 : 9); head.addColorStop(0, "rgba(255,255,230,1)"); head.addColorStop(1, "rgba(255,160,60,0)"); p.fillStyle = head; p.beginPath(); p.arc(s.cx, s.cy, s.big ? 16 : 9, 0, TAU); p.fill(); }
    // the ore on the crater's lip: black, a hot grain cooling over twenty seconds
    if (this.ore) { const o = this.ore, heat = Math.max(0.15, 1 - o.t / 20), pulse = 0.85 + 0.15 * Math.sin(o.t * 3);
      p.fillStyle = "rgba(30,24,20,0.9)"; p.beginPath(); p.ellipse(o.x, o.y + 6, 34, 6, 0, 0, TAU); p.fill();
      const glow = p.createRadialGradient(o.x, o.y, 2, o.x, o.y, 30); glow.addColorStop(0, `rgba(255,${120 + 80 * heat | 0},40,${0.55 * heat * pulse})`); glow.addColorStop(1, "rgba(255,100,30,0)"); p.fillStyle = glow; p.beginPath(); p.arc(o.x, o.y, 30, 0, TAU); p.fill();
      p.fillStyle = "#1A1614"; p.beginPath(); p.moveTo(o.x - 18, o.y + 6); p.lineTo(o.x - 13, o.y - 9); p.lineTo(o.x + 2, o.y - 15); p.lineTo(o.x + 16, o.y - 6); p.lineTo(o.x + 19, o.y + 6); p.closePath(); p.fill();
      p.strokeStyle = `rgba(255,${140 + 90 * heat | 0},${60 * heat | 0},${0.9 * pulse})`; p.lineWidth = 2; p.beginPath(); p.moveTo(o.x - 6, o.y - 3); p.lineTo(o.x + 1, o.y - 6); p.lineTo(o.x + 7, o.y - 1); p.stroke(); }
    // the fork, and the flash over everything
    if (this.actors) this.actors(p, "crater", t);
    if (this.bolt) { const b = this.bolt, k = 1 - b.age / b.life, drawPath = (path, wd) => { p.beginPath(); p.moveTo(path[0][0], path[0][1]); for (const q of path.slice(1)) p.lineTo(q[0], q[1]); p.stroke(); };
      p.save(); p.shadowColor = "rgba(180,200,255,1)"; p.shadowBlur = 18; p.strokeStyle = `rgba(235,240,255,${k})`; p.lineWidth = 3; drawPath(b.path); p.lineWidth = 1.5; for (const br of b.branches) drawPath(br); p.restore(); }
    if (this.flash > 0.01) { p.fillStyle = `rgba(220,228,255,${this.flash * 0.35})`; p.fillRect(0, 0, W, H); } };
  Stage.prototype.still = function () { const now = this.t0 + 30000; this.ore = this.words ? { x: this.words.claude.cx, y: this.words.claude.y0 - 34, t: 8 } : null; if (this.words) { const cloudY = this.words.and.y0 - 150; for (let i = 0; i < 160; i++) this.parts.push({ kind: "rain", x: rand(this.words.and.x0 - 70, this.words.and.x1 + 70), y: rand(cloudY + 20, this.words.and.y0 - 8), vx: 40, vy: 600, life: 99, age: 0, stop: 1e9 }); for (let i = 0; i < 46; i++) this.debris.push({ h: Math.random(), a: rand(0, TAU), sp: 0, leaf: Math.random() < 0.4, size: rand(1.5, 3.5) }); this.tornado = { x: this.words.magic.cx, top: this.words.magic.y0 - 230, foot: this.words.magic.y0 - 10, t: 0 }; } this.draw(now); };
  Stage.prototype.run = function () { let last = performance.now(); const loop = (now) => { if (!document.body.contains(this.el)) { window.removeEventListener("resize", this.onResize); return; }
      if (!this.words) { this.words = this.measure(); if (this.words && CM.reducedMotion) { this.still(); return; } }
      const dt = Math.min(0.05, (now - last) / 1000); last = now; this.step(dt, now); this.draw(now); requestAnimationFrame(loop); };
    requestAnimationFrame(loop); };
  CM.SplashStage = Stage;
  // the card's own styles for the stage and the lit letters
  const CSS = `#splash .sp-wx { position: absolute; inset: 0; pointer-events: none; z-index: 0; }
#splash h1 .fl.wx-lit { color: #FFF6D8 !important; text-shadow: 0 0 18px #FFC060, 0 0 40px #FF8A20 !important; transition: color 0.9s, text-shadow 0.9s; }
#splash h1 .fl.wx-bolt { color: #F4F6FF !important; text-shadow: 0 0 20px #B8C8FF, 0 0 44px #8AA0FF !important; }`;
  const so0 = CM.UI.prototype.showSplash; CM.UI.prototype.showSplash = function (...a) { const out = so0.apply(this, a); const el = document.getElementById("splash"); if (el && !el.querySelector(".sp-wx")) { if (!document.getElementById("splashwx-css")) { const st = document.createElement("style"); st.id = "splashwx-css"; st.textContent = CSS; document.head.appendChild(st); } try { (CM.splashStage = new Stage(el)).run(); } catch (e) { /* (the card stands without its weather) */ } } return out; };
}
