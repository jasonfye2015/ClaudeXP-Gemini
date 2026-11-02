"use strict";
// Marks that stay (v30.1, UPGRADE_PLAN_25.md): scorch where fire lands, blood where a foe falls (ash, bone dust or
// glittering shards for those that die otherwise), and the party's footprints in snow and mud - lying flat, fading
// with the game's clock (footprints in an hour, the rest in half a day or a day). Kept for each floor while the page
// is open; not saved. (A mark's glow of 0.001 tells the shader not to snow over it: 40-render.js.)
{ const S = 256, cv = () => { const c = document.createElement("canvas"); c.width = c.height = S; return c; };
  const rng = (seed) => { let s = seed >>> 0 || 1; return () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296); };
  const blobs = (p, r, n, col, spread, size) => { for (let i = 0; i < n; i++) { const a = r() * Math.PI * 2, d = Math.pow(r(), 1.6) * spread, rr = size * (0.3 + r() * 0.9) * (1 - d / spread * 0.6);
      p.fillStyle = col(r()); p.beginPath(); p.ellipse(128 + Math.cos(a) * d, 128 + Math.sin(a) * d, rr, rr * (0.6 + r() * 0.4), a, 0, Math.PI * 2); p.fill(); } };
  const PAINT = {
    "mark:blood": (p) => { const r = rng(7); blobs(p, r, 26, (k) => `rgba(${90 + k * 40 | 0},${8 + k * 10 | 0},${10 + k * 8 | 0},0.85)`, 70, 26); blobs(p, r, 30, () => "rgba(70,6,8,0.8)", 110, 6); },
    "mark:ash": (p) => { const r = rng(11); blobs(p, r, 40, (k) => `rgba(${70 + k * 60 | 0},${70 + k * 58 | 0},${68 + k * 55 | 0},0.55)`, 80, 22); },
    "mark:dust": (p) => { const r = rng(13); blobs(p, r, 34, (k) => `rgba(${200 + k * 30 | 0},${190 + k * 30 | 0},${160 + k * 30 | 0},0.5)`, 80, 18);
      p.strokeStyle = "rgba(230,222,200,0.9)"; p.lineWidth = 7; p.lineCap = "round"; for (let i = 0; i < 6; i++) { const x = 70 + r() * 116, y = 70 + r() * 116, a = r() * Math.PI; p.beginPath(); p.moveTo(x, y); p.lineTo(x + Math.cos(a) * 26, y + Math.sin(a) * 26); p.stroke(); } },
    "mark:shards": (p) => { const r = rng(17); for (let i = 0; i < 22; i++) { const x = 50 + r() * 156, y = 50 + r() * 156, s = 6 + r() * 14; p.fillStyle = `rgba(${170 + r() * 80 | 0},${200 + r() * 55 | 0},255,0.9)`;
      p.beginPath(); p.moveTo(x, y - s); p.lineTo(x + s * 0.5, y); p.lineTo(x, y + s * 0.7); p.lineTo(x - s * 0.4, y); p.fill(); } },
    "mark:scorch": (p) => { const g = p.createRadialGradient(128, 128, 6, 128, 128, 120); g.addColorStop(0, "rgba(10,6,4,0.95)"); g.addColorStop(0.45, "rgba(25,16,10,0.8)"); g.addColorStop(1, "rgba(30,20,12,0)");
      p.fillStyle = g; p.beginPath(); p.arc(128, 128, 120, 0, Math.PI * 2); p.fill(); const r = rng(19); p.strokeStyle = "rgba(15,10,6,0.6)"; p.lineWidth = 5;
      for (let i = 0; i < 18; i++) { const a = r() * Math.PI * 2, l = 60 + r() * 60; p.beginPath(); p.moveTo(128 + Math.cos(a) * 30, 128 + Math.sin(a) * 30); p.lineTo(128 + Math.cos(a) * l, 128 + Math.sin(a) * l); p.stroke(); }
      blobs(p, r, 8, () => "rgba(150,50,20,0.35)", 30, 10); },
    "mark:prints": (p, col = "rgba(40,34,30,0.75)") => { const foot = (x, y, flip) => { p.save(); p.translate(x, y); p.scale(flip ? -1 : 1, 1); p.fillStyle = col;
        p.beginPath(); p.ellipse(0, -18, 15, 24, 0.08, 0, Math.PI * 2); p.fill(); p.beginPath(); p.ellipse(2, 26, 12, 15, 0, 0, Math.PI * 2); p.fill(); p.restore(); };
      foot(96, 70, false); foot(160, 150, true); foot(96, 230, false); },
  };
  PAINT["mark:snowprints"] = (p) => PAINT["mark:prints"](p, "rgba(120,140,175,0.55)");   // (pressed into snow: blue in the shadow of the print)
  { const b0 = CM.art.build; CM.art.build = function (theme, look) { const set = b0.call(this, theme, look); for (const [n, f] of Object.entries(PAINT)) { const c = cv(); f(c.getContext("2d")); set.index[n] = set.layers.length; set.layers.push(c); } return set; }; }
  const LIFE = { "mark:prints": 60, "mark:snowprints": 60, "mark:blood": 1440, "mark:scorch": 1440, "mark:ash": 720, "mark:dust": 720, "mark:shards": 1440 };
  const store = new Map();
  const MK = CM.MARKS = { store, LIFE,
    add(game, m) { if (!game || !game.floor) return; const k = game.floor.number; let L = store.get(k); if (!L) store.set(k, (L = [])); L.push(Object.assign({ at: game.clock || 0 }, m)); if (L.length > 160) L.shift(); },
    on(game) { const L = game && game.floor ? store.get(game.floor.number) : null; if (!L) return []; const now = game.clock || 0; for (let i = L.length - 1; i >= 0; i--) if (now - L[i].at > LIFE[L[i].layer] || now < L[i].at) L.splice(i, 1); return L; } };
  const cellOf = (wx, wz) => { const x = Math.floor(wx), y = Math.floor(wz); return { x, y, dx: wx - x - 0.5, dz: wz - y - 0.5 }; };
  // a foe's fall: where the fight is, about the middle, by how it died
  const STYLE = { ash: "mark:ash", crumble: "mark:dust", shatter: "mark:shards" }, fell = new WeakSet();
  { const d0 = CM.deathStyleOf; CM.deathStyleOf = (m, game) => { const st = d0(m, game);
      if (m && game && game.mode === "combat" && game.foeKey && !fell.has(m)) { fell.add(m); const K = CM.monsterKind ? CM.monsterKind(m.kind || m.name || "") || {} : {};
        const layer = st === "sink" || K.body === "ghost" ? null : STYLE[st] || "mark:blood";
        if (layer) { const [x, y] = game.foeKey.split(",").map(Number), h = CM.hashSeed(`${m.name}:${game.clock}:${x},${y}`); MK.add(game, { x, y, dx: ((h % 100) / 100 - 0.5) * 0.5, dz: (((h >> 7) % 100) / 100 - 0.5) * 0.5, layer, w: 0.55 + (h % 30) / 100, spin: (h % 628) / 100 }); } }
      return st; }; }
  // fire that lands: a scorch where it struck
  const FIRE = new Set(["firebolt", "fire", "fireball", "flamestrike", "inferno", "burn", "dragonbreath", "flame"]);
  { const c0 = CM.castFx2; if (c0) CM.castFx2 = (fx, foes, K) => { const r = c0(fx, foes, K);
      if (fx && FIRE.has(fx.id) && K && K.atFoe && CM.game) { const game = CM.game, hits = fx.foe && fx.id !== "fireball" ? [fx.foe] : foes || [];
        setTimeout(() => { for (const m of hits) { const at = K.atFoe(m, 0); if (at) MK.add(game, Object.assign(cellOf(at[0], at[2]), { layer: "mark:scorch", w: fx.id === "fireball" ? 0.9 : 0.65, spin: Math.random() * 6.28 })); } }, 420); }
      return r; }; }
  // footprints: in lying snow, and on wet ground
  { const em0 = CM.Game.prototype.emit; let prev = null, prevFloor = null;
    CM.Game.prototype.emit = function (ev, ...a) { if (ev === "moved" && this.floor) { const fl = this.floor, r = CM.renderer;
        if (prev && prevFloor === fl && r && r.sky && ((r.snow || 0) > 0.3 || (r.wet || 0) > 0.3 || (r.puddle || 0) > 0.3)) { const dx = a[0] - prev[0], dy = a[1] - prev[1];
          if (Math.abs(dx) + Math.abs(dy) === 1) MK.add(this, { x: prev[0], y: prev[1], dx: 0, dz: 0, layer: (r.snow || 0) > 0.3 ? "mark:snowprints" : "mark:prints", w: 0.62, spin: Math.atan2(dx, -dy) }); }
        prev = [a[0], a[1]]; prevFloor = fl; }
      else if (ev === "floor") { prev = this.floor ? this.floor.pos.slice() : null; prevFloor = this.floor; }
      return em0.call(this, ev, ...a); }; }
  { const ls0 = CM.lifeSprites; CM.lifeSprites = (game, fl, now) => { const out = ls0 ? ls0(game, fl, now) : []; if (!fl || !CM.renderer || game.mode === "title") return out;
      const T = game.clock || 0;
      for (const m of MK.on(game)) { if (Math.abs(m.x - fl.pos[0]) + Math.abs(m.y - fl.pos[1]) > 14) continue; const k = 1 - (T - m.at) / LIFE[m.layer];
        out.push({ x: m.x, y: m.y, dx: m.dx, dz: m.dz, layer: m.layer, w: m.w, h: m.w, flat: true, spin: m.spin, alpha: Math.min(1, k * 1.6), glow: 0.001 }); }
      return out; }; }
}
