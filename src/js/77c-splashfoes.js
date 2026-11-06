"use strict";
// The title card's foes (UPGRADE_PLAN_68.md, part 2): ten small scenes cast into the weather show (77b-splashwx.js),
// each brief and rare, so the card stays calm and rewards whoever leaves it open. A first viewer meets most of them in
// the first half-minute; after that each comes back on its own long clock.
//   1 something claws up out of the star's crater, looks at the ore, and sinks back
//   2 the Lich King's silhouette in the storm cloud for the instant of a fork
//   3 a wyvern caught in the tornado's orbit, fighting free and flapping off
//   4 the Drowned standing in the downpour at the tree line, gone when the rain eases
//   5 eyes opening between the trunks by night; a wolf trotting through, stopping to look, by day
//   6 rats along the bottom edge, scattering at a flash
//   7 a guardian walking slowly behind the trees, half hidden
//   8 your nemesis lurking at the tree line's edge, with what it did said under it
//   9 the creatures of the band of your deepest floor in place of the Catacombs' own
//  10 the heroes in their row glancing toward whatever appears; the Knight lifts his shield at the Lich King
// Monster pictures are the game's drawn ones (CM.art.monster), made once each.
{ const TAU = Math.PI * 2, rand = (a, b) => a + Math.random() * (b - a);
  const pics = new Map();
  const kindOf = (name) => (name === "LICH" ? CM.BOSS : CM.GUARDIANS && Object.values(CM.GUARDIANS).find((G) => G.name === name)) || CM.monsterKind(name);
  const pic = (name) => { if (pics.has(name)) return pics.get(name); let c = null; try { const k = kindOf(name); if (k) c = CM.art.monster(k, name === "LICH" ? true : false); } catch (e) { c = null; } pics.set(name, c); return c; };
  const shadowOf = (name, colour) => { const key = `${name}|${colour}`; if (pics.has(key)) return pics.get(key); const src = pic(name); if (!src) return null; const c = document.createElement("canvas"); c.width = src.width; c.height = src.height; const p = c.getContext("2d"); p.drawImage(src, 0, 0); p.globalCompositeOperation = "source-in"; p.fillStyle = colour; p.fillRect(0, 0, c.width, c.height); pics.set(key, c); return c; };
  // a picture standing on (x, foot), h tall, facing left or right, alpha
  const stand = (p, c, x, foot, h, opts = {}) => { if (!c) return; p.save(); p.globalAlpha = opts.alpha === undefined ? 1 : opts.alpha; p.translate(x, foot + h * 0.055); if (opts.flip) p.scale(-1, 1); if (opts.rot) p.rotate(opts.rot); p.drawImage(c, -h / 2, -h, h, h); p.restore(); };
  // the band of the deepest floor reached: its creatures
  const deepKinds = () => { try { const g = CM.game, fame = g ? (g.allFame || g.fame || []) : [], deep = CM.deepest ? CM.deepest(fame).floor : 0; if (deep < 18) return null; const band = CM.themeIndex(deep), [lo, hi] = CM.THEMES[band].floors, mid = Math.round((lo + hi) / 2), out = new Set(); for (let s = 1; s <= 8; s++) for (const m of CM.monsterGroup(mid, new CM.Random(s), 2)) out.add(m.kind || m.name); return [...out].filter((n) => CM.monsterKind(n)); } catch (e) { return null; } };
  // the Lich King as a silhouette: crowned hood, robe flaring, the arms up and a staff - one shape, read in a flash
  const lichShape = (p, x, y, k) => { p.fillStyle = "rgba(8,10,22,1)"; p.beginPath();
    p.moveTo(x - 9 * k, y + 8 * k); p.lineTo(x - 7 * k, y); p.lineTo(x - 4 * k, y + 5 * k); p.lineTo(x, y - 3 * k); p.lineTo(x + 4 * k, y + 5 * k); p.lineTo(x + 7 * k, y); p.lineTo(x + 9 * k, y + 8 * k);   /* (the crown) */
    p.quadraticCurveTo(x + 16 * k, y + 24 * k, x + 13 * k, y + 40 * k); p.lineTo(x + 46 * k, y + 14 * k); p.lineTo(x + 52 * k, y + 20 * k); p.lineTo(x + 22 * k, y + 56 * k);   /* (the right arm, raised) */
    p.lineTo(x + 40 * k, y + 150 * k); p.lineTo(x - 40 * k, y + 150 * k); p.lineTo(x - 22 * k, y + 56 * k);   /* (the robe) */
    p.lineTo(x - 50 * k, y + 22 * k); p.lineTo(x - 44 * k, y + 16 * k); p.lineTo(x - 13 * k, y + 40 * k); p.quadraticCurveTo(x - 16 * k, y + 24 * k, x - 9 * k, y + 8 * k); p.fill();
    p.fillRect(x - 50 * k, y - 34 * k, 4 * k, 64 * k); p.beginPath(); p.arc(x - 48 * k, y - 38 * k, 7 * k, 0, TAU); p.fill(); };   /* (the staff, its head) */
  const night = () => { const h = new Date().getHours(); return h >= 20 || h < 6; };
  // the heroes in their row look toward x; the Knight lifts his shield
  const CSS = `#splash .hero.wx-look { transition: transform 0.35s ease-out; transform: translateX(var(--lx)) rotate(var(--lr)); }
#splash .hero.wx-guard canvas { transition: transform 0.2s ease-out; transform: translateY(-5px) scale(1.08); filter: drop-shadow(0 0 6px rgba(200,210,255,0.7)); }
#splash .wx-nem { position: absolute; z-index: 2; cursor: help; border-radius: 50%; }`;
  const look = (stage, x, ms = 1800, guard = false) => { const heroes = [...stage.el.querySelectorAll(".lineup .hero")], host = stage.el.getBoundingClientRect(); for (const h of heroes) { const r = h.getBoundingClientRect(), hx = r.left + r.width / 2 - host.left, d = Math.sign(x - hx); h.style.setProperty("--lx", `${d * 3}px`); h.style.setProperty("--lr", `${d * 6}deg`); h.classList.add("wx-look"); if (guard && h.title === "Knight") h.classList.add("wx-guard"); }
    clearTimeout(stage.lookT); stage.lookT = setTimeout(() => { for (const h of heroes) h.classList.remove("wx-look", "wx-guard"); }, ms); };
  const S = CM.SplashStage; if (S) {   /* (the weather show is there to cast into) */
  S.prototype.cast = function (dt, t) {
    if (CM.reducedMotion) return;
    if (!this.foes) { if (!document.getElementById("splashfoes-css")) { const st = document.createElement("style"); st.id = "splashfoes-css"; st.textContent = CSS; document.head.appendChild(st); }
      const deep = deepKinds(), nem = CM.store && CM.store.get ? CM.store.get("nemesis", null) : null;
      const walker = deep ? deep.filter((n) => !/Lotus|Mother|Golem|Sentinel/.test(n))[0] || deep[0] : "Wolf", riser = deep ? deep.find((n) => ["biped", "thin", "tall", "ghost"].includes((CM.monsterKind(n) || {}).body)) || "Skeleton" : "Skeleton", vermin = deep ? deep.find((n) => ["small", "beast"].includes((CM.monsterKind(n) || {}).body)) || "Giant Rat" : "Giant Rat";
      this.foes = { live: [], next: { rats: 4, forest: 7, riser: 9, wyvern: 12, drowned: 15, nemesis: nem ? 18 : 1e9, guardian: 22 }, lichNext: true, walker, riser, vermin, nem, deep };
      this.onBolt = () => { const F = this.foes; if (!F || !this.words) return; if (F.lichNext || Math.random() < 0.34) { F.lichNext = false; F.live.push({ kind: "lich", age: 0, life: 0.5 }); look(this, this.words.and.cx, 1600, true); } }; }
    const F = this.foes, w = this.words, W = this.W, H = this.H, base = H * 0.985, rate = (a, b) => t + rand(a, b);
    const due = (k) => t >= F.next[k] && !F.live.some((a) => a.kind === k);
    if (due("rats")) { const dir = Math.random() < 0.5 ? 1 : -1; for (let i = 0; i < 3 + Math.floor(rand(0, 3)); i++) F.live.push({ kind: "rats", dir, x: dir > 0 ? -30 - i * rand(30, 60) : W + 30 + i * rand(30, 60), sp: rand(150, 210), age: 0, life: 14, h: rand(22, 30), hop: rand(0, TAU) }); F.next.rats = rate(18, 30); }
    if (due("forest")) { if (night()) { for (let i = 0; i < 3 + Math.floor(rand(0, 2)); i++) F.live.push({ kind: "forest", eyes: true, x: rand(W * 0.08, W * 0.92), y: base - H * rand(0.04, 0.13), vx: rand(-14, 14), age: -i * 0.6, life: 5.5, hue: Math.random() < 0.7 ? "#FFD84A" : "#FF5A3A" }); }
      else { const dir = Math.random() < 0.5 ? 1 : -1; F.live.push({ kind: "forest", eyes: false, dir, x: dir > 0 ? -60 : W + 60, stopAt: rand(W * 0.25, W * 0.75), sp: 95, age: 0, life: 30, h: H * 0.11, stood: 0 }); look(this, dir > 0 ? 0 : W, 1500); }
      F.next.forest = rate(25, 40); }
    if (due("riser") && this.ore) { F.live.push({ kind: "riser", x: this.ore.x + rand(-28, 28), y: this.ore.y + 6, age: 0, life: 4.2, h: 64 }); look(this, this.ore.x, 1800); F.next.riser = rate(45, 75); }
    if (due("wyvern") && this.tornado) { F.live.push({ kind: "wyvern", a: rand(0, TAU), hh: 0.55, age: 0, life: 7, h: 66, free: 4 }); look(this, this.tornado.x, 1800); F.next.wyvern = rate(35, 55); }
    if (due("drowned") && this.gust > 0.55) { for (let i = 0; i < 3; i++) F.live.push({ kind: "drowned", x: w.and.cx + (i - 1) * rand(70, 110), age: -i * 0.4, life: 9, h: H * rand(0.12, 0.15), sway: rand(0, TAU) }); look(this, w.and.cx, 1600); F.next.drowned = rate(30, 50); }
    if (due("guardian")) { const Gs = Object.values(CM.GUARDIANS || {}).filter((G) => G.floor > 0), G = Gs[Math.floor(rand(0, Gs.length))], dir = Math.random() < 0.5 ? 1 : -1; if (G) { F.live.push({ kind: "guardian", name: G.name, dir, x: dir > 0 ? -120 : W + 120, sp: 38, age: 0, life: 60, h: H * 0.27, step: 0 }); look(this, dir > 0 ? 0 : W, 2000); } F.next.guardian = rate(55, 80); }
    if (due("nemesis") && F.nem) { const left = Math.random() < 0.5; F.live.push({ kind: "nemesis", left, age: 0, life: 9, h: H * 0.16 }); look(this, left ? 0 : W, 2200); F.next.nemesis = rate(40, 60); }
    for (const a of F.live) { a.age += dt;
      if (a.kind === "rats") { const scare = this.flash > 0.4 ? 2.2 : 1; a.x += a.dir * a.sp * scare * dt; if (this.flash > 0.45 && !a.scared) { a.scared = true; a.dir *= Math.random() < 0.5 ? -1 : 1; } if (a.x < -80 || a.x > W + 80) a.age = a.life; }
      else if (a.kind === "forest" && !a.eyes) { if (a.stood <= 0 && Math.abs(a.x - a.stopAt) < 4 && !a.done) { a.stood = 2.6; a.done = true; } if (a.stood > 0) a.stood -= dt; else a.x += a.dir * a.sp * dt; if (a.x < -100 || a.x > W + 100) a.age = a.life; }
      else if (a.kind === "forest") a.x += a.vx * dt;
      else if (a.kind === "wyvern" && this.tornado) { if (a.age < a.free) { a.a += dt * 3.4; a.hh = 0.55 + Math.sin(a.age * 2) * 0.12; } else { a.fx = (a.fx === undefined ? this.tornado.x + Math.cos(a.a) * 60 : a.fx) - dt * 260; a.fy = (a.fy === undefined ? this.tornado.foot + (this.tornado.top - this.tornado.foot) * a.hh : a.fy) - dt * 120; if (a.fy < -60) a.age = a.life; } }
      else if (a.kind === "guardian") { a.x += a.dir * a.sp * dt; a.step += dt; if (a.x < -200 || a.x > W + 200) a.age = a.life; }
      else if (a.kind === "drowned" && this.gust < 0.42 && a.age > 2) a.age = Math.max(a.age, a.life - 1); }
    F.live = F.live.filter((a) => a.age < a.life);
    // the nemesis's words, on hover too
    const nemA = F.live.find((a) => a.kind === "nemesis"); let tag = this.el.querySelector(".wx-nem");
    if (nemA) { if (!tag) { tag = document.createElement("div"); tag.className = "wx-nem"; this.el.appendChild(tag); } const x = nemA.left ? 50 : W - 50; tag.style.left = `${x - 40}px`; tag.style.top = `${base - nemA.h - 10}px`; tag.style.width = "80px"; tag.style.height = `${nemA.h}px`; tag.title = CM.nemesisLine(F.nem); }
    else if (tag) tag.remove();
  };
  S.prototype.actors = function (p, layer, t) { const F = this.foes; if (!F || !this.words) return; const W = this.W, H = this.H, base = H * 0.985, w = this.words;
    for (const a of F.live) { const k = a.age / a.life, inOut = Math.min(1, a.age / 0.6, (a.life - a.age) / 0.8);
      if (layer === "behind" && a.kind === "guardian") stand(p, pic(a.name), a.x, base - H * 0.02 + Math.abs(Math.sin(a.step * 3)) * -3, a.h, { flip: a.dir < 0, alpha: 0.9 * Math.min(1, a.age / 2), rot: Math.sin(a.step * 3) * 0.03 });
      else if (layer === "front" && a.kind === "rats") stand(p, pic(F.vermin), a.x, base - 4 - Math.abs(Math.sin(t * 14 + a.hop)) * 3, a.h, { flip: a.dir < 0 });
      else if (layer === "front" && a.kind === "forest" && !a.eyes) stand(p, pic(F.walker), a.x, base - 2 - (a.stood > 0 ? 0 : Math.abs(Math.sin(t * 9)) * 3), a.h, { flip: a.stood > 0 ? false : a.dir < 0, alpha: 0.95 });
      else if (layer === "front" && a.kind === "forest" && a.eyes && a.age > 0) { const open = Math.min(1, a.age / 0.5, (a.life - a.age) / 0.5) * (Math.sin(a.age * 2.3) > -0.92 ? 1 : 0.1); for (const dx of [-7, 7]) { const g = p.createRadialGradient(a.x + dx, a.y, 0, a.x + dx, a.y, 11); g.addColorStop(0, a.hue); g.addColorStop(0.35, a.hue); g.addColorStop(1, "rgba(0,0,0,0)"); p.globalAlpha = open; p.fillStyle = g; p.beginPath(); p.arc(a.x + dx, a.y, 11, 0, TAU); p.fill(); p.fillStyle = "#fff"; p.beginPath(); p.ellipse(a.x + dx, a.y, 2.2, 1.4, 0, 0, TAU); p.fill(); } p.globalAlpha = 1; }
      else if (layer === "front" && a.kind === "drowned" && a.age > 0) stand(p, shadowOf("Drowned", "rgba(120,160,175,1)"), a.x + Math.sin(t * 0.8 + a.sway) * 4, base - H * 0.01, a.h * 0.75, { alpha: 0.24 * inOut, rot: Math.sin(t * 0.9 + a.sway) * 0.05 });
      else if (layer === "front" && a.kind === "nemesis") { const x = a.left ? 50 : W - 50, peek = Math.min(1, a.age / 1.2, (a.life - a.age) / 1.2); stand(p, pic(F.nem.kind), x + (a.left ? -1 : 1) * (1 - peek) * 60, base - H * 0.01, a.h, { flip: !a.left, alpha: 0.95 });
        p.save(); p.globalAlpha = Math.min(1, Math.max(0, (a.age - 1) / 0.8), (a.life - a.age) / 0.8); p.font = "italic 14px Georgia, serif"; p.fillStyle = "#E8C8A8"; p.textAlign = a.left ? "left" : "right"; p.shadowColor = "#000"; p.shadowBlur = 8; p.fillText(CM.nemesisLine(F.nem), a.left ? 110 : W - 110, base - a.h * 0.25); p.restore(); }
      else if (layer === "cloud" && a.kind === "lich") { if (this.flash > 0.08) { const cx = w.and.cx, top = Math.max(52, w.and.y0 - 190), k = 1.05; p.save(); p.globalAlpha = Math.min(0.92, this.flash * 1.9); lichShape(p, cx, top, k); p.globalAlpha = Math.min(1, this.flash * 2.4); p.fillStyle = "#9CF0FF"; p.shadowColor = "#9CF0FF"; p.shadowBlur = 10; for (const dx of [-6, 6]) { p.beginPath(); p.arc(cx + dx * k, top + 24 * k, 2.8, 0, TAU); p.fill(); }   /* (rising behind the emblem, in the cloud) */ p.restore(); } }
      else if (layer === "sky" && a.kind === "wyvern" && this.tornado) { const T = this.tornado; let x, y; if (a.fx !== undefined) { x = a.fx; y = a.fy; } else { const r = 10 + a.hh * a.hh * 74; x = T.x + Math.cos(a.a) * r; y = T.foot + (T.top - T.foot) * a.hh + Math.sin(a.a) * r * 0.2; } const front = a.fx !== undefined || Math.sin(a.a) > 0; stand(p, pic("Wyvern"), x, y + a.h / 2, a.h * (front ? 1 : 0.8), { flip: a.fx !== undefined ? true : Math.cos(a.a) > 0, alpha: front ? 1 : 0.6, rot: a.fx !== undefined ? -0.3 : Math.sin(a.a * 2) * 0.4 }); }
      else if (layer === "crater" && a.kind === "riser" && this.ore) { const up = a.age < 1.2 ? a.age / 1.2 : a.age < 3 ? 1 : Math.max(0, (a.life - a.age) / 1.2); p.save(); p.beginPath(); p.rect(a.x - 60, a.y - 120, 120, 120); p.clip(); stand(p, pic(F.riser), a.x, a.y + (1 - up) * a.h, a.h, { flip: a.x > this.ore.x, rot: up < 1 ? Math.sin(t * 20) * 0.04 : 0 }); p.restore(); p.fillStyle = "rgba(30,24,20,0.9)"; p.beginPath(); p.ellipse(a.x, a.y + 2, 26, 5, 0, 0, TAU); p.fill(); } }
  };
}
}
