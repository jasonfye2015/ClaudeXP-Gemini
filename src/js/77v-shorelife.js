"use strict";
// The shore's life, seen (UPGRADE_PLAN_80.md, v131.0; the rules 69zzzzi-shells.js): the tide's shells lying on the
// sand, each its own kind; fish in the river and the sea - dark shapes turning slowly under the surface - and now and
// then one leaping, a silver flash out of the water and back with a splash.
{ const key = (x, y) => `${x},${y}`;
  // the pictures
  { const b0 = CM.art.build; CM.art.build = function (theme, look) { const set = b0.call(this, theme, look), N = set.size, add = (n, c) => { set.index[n] = set.layers.length; set.layers.push(c); };
      const can = () => { const c = document.createElement("canvas"); c.width = c.height = N; return [c, c.getContext("2d"), N / 64]; };
      { const [c, p, u] = can(); p.fillStyle = "#E8DCC4"; p.beginPath(); p.moveTo(32 * u, 50 * u); p.bezierCurveTo(10 * u, 44 * u, 10 * u, 18 * u, 32 * u, 14 * u); p.bezierCurveTo(54 * u, 18 * u, 54 * u, 44 * u, 32 * u, 50 * u); p.fill();   // cockle: ridged
        p.strokeStyle = "#B49A78"; p.lineWidth = 1.6 * u; for (let i = -3; i <= 3; i++) { p.beginPath(); p.moveTo(32 * u, 50 * u); p.lineTo((32 + i * 6) * u, 16 * u); p.stroke(); } add("shell:cockle", c); }
      { const [c, p, u] = can(); p.fillStyle = "#C8B49A"; p.strokeStyle = "#8A6A4A"; p.lineWidth = 2 * u; p.beginPath(); for (let a = 0; a < 14; a += 0.2) { const r = (2 + a * 1.6) * u; p.lineTo(32 * u + Math.cos(a) * r, 32 * u + Math.sin(a) * r * 0.8); } p.fill(); p.stroke(); add("shell:whelk", c); }   // whelk: a spiral
      { const [c, p, u] = can(); p.fillStyle = "#E0A070"; p.beginPath(); p.moveTo(32 * u, 52 * u); p.arc(32 * u, 32 * u, 20 * u, Math.PI * 0.95, Math.PI * 2.05); p.closePath(); p.fill(); p.fillRect(24 * u, 48 * u, 16 * u, 6 * u);   // scallop: a fan
        p.strokeStyle = "#B06A40"; p.lineWidth = 1.5 * u; for (let i = 0; i <= 8; i++) { const a = Math.PI * (1 + i / 8); p.beginPath(); p.moveTo(32 * u, 50 * u); p.lineTo(32 * u + Math.cos(a) * 20 * u, 32 * u + Math.sin(a) * 20 * u); p.stroke(); } add("shell:scallop", c); }
      { const [c, p, u] = can(); p.fillStyle = "rgba(110,190,170,0.85)"; p.beginPath(); p.moveTo(20 * u, 26 * u); p.lineTo(40 * u, 20 * u); p.lineTo(46 * u, 38 * u); p.lineTo(26 * u, 44 * u); p.closePath(); p.fill(); p.fillStyle = "rgba(255,255,255,0.5)"; p.fillRect(28 * u, 26 * u, 8 * u, 3 * u); add("shell:glass", c); }   // sea-glass
      { const [c, p, u] = can(); p.fillStyle = "#D8C090"; p.beginPath(); p.ellipse(32 * u, 32 * u, 13 * u, 18 * u, 0, 0, Math.PI * 2); p.fill(); p.fillStyle = "#7A5030"; for (let i = 0; i < 18; i++) { p.beginPath(); p.arc((24 + (i * 7) % 17) * u, (18 + (i * 11) % 28) * u, 1.6 * u, 0, Math.PI * 2); p.fill(); } p.strokeStyle = "#5A3A20"; p.lineWidth = 2 * u; p.beginPath(); p.moveTo(32 * u, 16 * u); p.lineTo(32 * u, 48 * u); p.stroke(); add("shell:cowrie", c); }   // cowrie: spotted
      { const [c, p, u] = can(); p.fillStyle = "#E8C8B0"; p.beginPath(); p.moveTo(14 * u, 40 * u); p.lineTo(30 * u, 10 * u); p.lineTo(52 * u, 30 * u); p.lineTo(42 * u, 50 * u); p.closePath(); p.fill(); p.fillStyle = "#F0A0A0"; p.beginPath(); p.ellipse(38 * u, 36 * u, 7 * u, 11 * u, 0.6, 0, Math.PI * 2); p.fill(); add("shell:conch", c); }   // conch
      { const [c, p, u] = can(); p.fillStyle = "#6A6A70"; p.beginPath(); p.ellipse(32 * u, 32 * u, 18 * u, 14 * u, 0.3, 0, Math.PI * 2); p.fill(); p.fillStyle = "#9A9AA4"; p.beginPath(); p.ellipse(30 * u, 30 * u, 12 * u, 8 * u, 0.3, 0, Math.PI * 2); p.fill(); add("shell:pearl", c); }   // an oyster, shut
      { const [c, p, u] = can(); p.fillStyle = "rgba(20,30,34,0.85)"; p.beginPath(); p.ellipse(32 * u, 26 * u, 6 * u, 16 * u, 0, 0, Math.PI * 2); p.fill(); p.beginPath(); p.moveTo(32 * u, 38 * u); p.lineTo(25 * u, 50 * u); p.lineTo(39 * u, 50 * u); p.closePath(); p.fill(); add("fx:fishshadow", c); }   // a fish from above, head up the picture
      { const [c, p, u] = can(); const g = p.createLinearGradient(0, 22 * u, 0, 42 * u); g.addColorStop(0, "#5A7A8A"); g.addColorStop(0.5, "#D8E4EA"); g.addColorStop(1, "#F4F4F0"); p.fillStyle = g;   // a fish from the side, leaping
        p.beginPath(); p.moveTo(10 * u, 32 * u); p.quadraticCurveTo(30 * u, 18 * u, 48 * u, 30 * u); p.lineTo(58 * u, 22 * u); p.lineTo(56 * u, 32 * u); p.lineTo(58 * u, 42 * u); p.lineTo(48 * u, 34 * u); p.quadraticCurveTo(30 * u, 46 * u, 10 * u, 32 * u); p.fill(); p.fillStyle = "#101418"; p.beginPath(); p.arc(17 * u, 30 * u, 1.8 * u, 0, Math.PI * 2); p.fill(); add("fx:fish", c); }
      { const [c, p, u] = can(); p.fillStyle = "rgba(240,248,252,0.85)"; const r = new CM.Random(5); for (let i = 0; i < 26; i++) { const a = Math.PI * (1.05 + r.next() * 0.9), d = (6 + r.next() * 22) * u; p.beginPath(); p.arc(32 * u + Math.cos(a) * d, 56 * u + Math.sin(a) * d * 1.3, (1 + r.next() * 2.4) * u, 0, Math.PI * 2); p.fill(); } add("fx:splash", c); }
      return set; }; }
  // the springhead: boulders heaped over the rock the river rises from
  { const pi0 = CM.plantInstancesOf; if (pi0) CM.plantInstancesOf = (game, fl, at, reach, density) => { const out = pi0(game, fl, at, reach, density); if (!fl || fl.number !== -1 || !CM.COAST || !(density > 0) || fl.grid.length <= CM.SHORE.sea) return out;
      const M = (CM.plantsPack && CM.plantsPack.manifest && CM.plantsPack.manifest.models) || {}, [ax, ay] = at || fl.pos, C = CM.COAST; if (Math.abs(ax - 22) + Math.abs(ay) > (reach || 12) + 4) return out;
      const put = (name, x, z, y, size, salt) => { const m = M[name]; if (!m) return; const lo = m.box[0], hi = m.box[1], w = Math.max(1e-3, hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2]), sc = size * 0.62 / w, hh = CM.hashSeed(`spring:${salt}`);
        out.push({ model: name, x: x - (lo[0] + hi[0]) / 2 * sc, y: y - lo[1] * sc, z: z - (lo[2] + hi[2]) / 2 * sc, yaw: (hh % 360) * Math.PI / 180, scale: sc, sway: 0, height: (hi[1] - lo[1]) * sc, shade: 0.66, kind: "rock" }); };
      for (let x = C.spring[0]; x <= C.spring[1]; x++) { put(x % 2 ? "rock1" : "rock2", x + 0.5, 0.75, 0, 1.25, `f${x}`); put(x % 2 ? "rock2" : "rock1", x + 0.5, 0.3, x === CM.riverX(0) ? 1.6 : 0.9, 1.15, `t${x}`); put("rock1", x + 0.2, 0.1, 0, 1.0, `b${x}`); }
      put("rock2", C.spring[0] - 0.1, 0.9, 0, 0.8, "l"); put("rock1", C.spring[1] + 1.1, 0.9, 0, 0.8, "r");
      return out; }; }
  // where the water is, near the party: the river's squares and the sea's
  const waterNear = (fl, R) => { const [px, py] = fl.pos, out = []; for (const d of fl.decor || []) if (d.kind === "water" && Math.abs(d.x - px) + Math.abs(d.y - py) <= R) out.push([d.x, d.y, 0]);
    if (CM.seaCells) for (let y = Math.max(0, py - R); y <= Math.min(fl.grid.length + 3, py + R); y++) for (let x = Math.max(-3, px - R); x <= Math.min(fl.grid.length + 3, px + R); x++) { if (Math.abs(x - px) + Math.abs(y - py) > R) continue; if (CM.solidAt(fl, x, y) === "sea" && !(CM.isPier && CM.isPier(x, y))) out.push([x, y, -0.035]); }
    return out; };
  const h = (s) => (CM.hashSeed(s) >>> 0) / 4294967296;
  let jump = null, nextJump = 0, cacheAt = "", cache = [];
  { const ls0 = CM.lifeSprites; CM.lifeSprites = (game, fl, now) => { const out = ls0 ? ls0(game, fl, now) : []; if (!fl || fl.number !== -1 || game.mode === "title" || !fl.grid) return out;
      // the shells
      if (CM.shellsNow) for (const s of CM.shellsNow(game)) if (Math.abs(s.x - fl.pos[0]) + Math.abs(s.y - fl.pos[1]) <= 12) out.push({ x: s.x, y: s.y, dx: (h(`sx${s.x},${s.y}`) - 0.5) * 0.5, dz: (h(`sz${s.x},${s.y}`) - 0.5) * 0.5, flat: true, spin: h(`ss${s.x},${s.y}`) * 6.28, layer: `shell:${s.id}`, w: s.id === "conch" ? 0.4 : 0.3 });
      // the fish under the water
      const at = `${fl.pos[0]},${fl.pos[1]}`; if (at !== cacheAt) { cacheAt = at; cache = waterNear(fl, 9); } if (!cache.length) return out;
      const t = CM.reducedMotion ? 0 : now / 1000, night = CM.isNight ? CM.isNight(game) : false, frozen = fl.frozen;
      if (!frozen) for (const [x, y, base] of cache) { const r = h(`fish:${x},${y}`); if (r > (base < 0 ? 0.22 : 0.3)) continue; const sp = 0.25 + r * 0.9, ph = r * 40, rad = base < 0 ? 0.42 : 0.26;
        const a = t * sp + ph, fx = Math.cos(a) * rad, fz = Math.sin(a) * rad * 0.8, heading = Math.atan2(Math.cos(a) * 0.8, -Math.sin(a));
        out.push({ x, y, dx: fx, dz: fz, base, flat: true, spin: heading, layer: "fx:fishshadow", w: base < 0 ? 0.62 : 0.36, alpha: night ? 0.3 : 0.72 }); }
      // now and then, one leaps
      if (!frozen && !CM.reducedMotion) { if (!jump && now > nextJump) { const [x, y, base] = cache[Math.floor(Math.random() * cache.length)]; jump = { x, y, base, t0: now, dir: Math.random() < 0.5 ? 1 : -1, sounded: false }; nextJump = now + 2500 + Math.random() * 5000; }
        if (jump) { const k = (now - jump.t0) / 900; if (k >= 1.5) jump = null; else { const { x, y, base } = jump;
            if (k < 1) out.push({ x, y, dx: (k - 0.5) * 0.6 * jump.dir, base, lift: Math.sin(Math.PI * k) * 0.55, layer: "fx:fish", w: 0.34, h: 0.34, tilt: (0.5 - k) * 1.6 * jump.dir, mirror: jump.dir < 0 });
            for (const [kk, sx] of [[k, -0.3], [k - 1, 0.3]]) if (kk >= 0 && kk < 0.5) out.push({ x, y, dx: sx * jump.dir, base, layer: "fx:splash", w: 0.5, h: 0.4, alpha: 0.9 * (1 - kk * 2) });
            if (!jump.sounded && CM.audio && CM.audio.play && Math.abs(x - fl.pos[0]) + Math.abs(y - fl.pos[1]) < 7) { jump.sounded = true; try { CM.audio.play("splash", 0.18, 0, 1.5); } catch (e) { /* (no sound) */ } } } } }
      return out; }; }
}
