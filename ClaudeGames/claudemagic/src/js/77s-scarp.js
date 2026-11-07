"use strict";
// The Scarp, seen and heard (UPGRADE_PLAN_79.md; the land of it 23e-scarp.js, its rules 69zzzzf-scarp.js): the heath's
// heather and bare rock as ground of their own; every plant and stone on the heath standing on the heath, not under
// it; boulders fallen at the rock's foot and lying about the heath, so the scarp is a scarp and not a wall; a cairn at
// the Lookout; and the falls - a white rope of water down the rock's face, a veil of spray before it, foam churning in
// the pool and mist rising off it, and when the Wood freezes, a curtain of ice. The roar is 76zzzzs-placeamb.js's.
{ const S = CM.SCARP;
  // the ground: heather, bare rock, sand
  { const g0 = CM.art.ground; CM.art.ground = function (kind, seed = 1) { if (!["heath", "rock", "sand"].includes(kind)) return g0.call(this, kind, seed);
      const c = document.createElement("canvas"), N = c.width = c.height = 256, p = c.getContext("2d"), rnd = new CM.Random(CM.hashSeed(`ground:${kind}:${seed}`));
      const dots = (n, col, r0, r1) => { p.fillStyle = col; for (let i = 0; i < n; i++) { p.beginPath(); p.arc(rnd.next() * N, rnd.next() * N, r0 + rnd.next() * (r1 - r0), 0, Math.PI * 2); p.fill(); } };
      if (kind === "heath") { p.fillStyle = "#5E5A3A"; p.fillRect(0, 0, N, N); dots(900, "rgba(112,104,62,0.6)", 1, 3); dots(700, "rgba(74,90,48,0.7)", 1.5, 3.5);
        p.lineWidth = 1.4; for (let i = 0; i < 420; i++) { const x = rnd.next() * N, y = rnd.next() * N; p.strokeStyle = rnd.next() < 0.5 ? "rgba(96,118,58,0.85)" : "rgba(70,84,44,0.85)"; p.beginPath(); p.moveTo(x, y); p.lineTo(x + (rnd.next() - 0.5) * 5, y - 3 - rnd.next() * 6); p.stroke(); }
        dots(520, "rgba(128,78,120,0.85)", 1, 2.4); dots(160, "rgba(168,104,150,0.8)", 0.8, 1.8); dots(40, "rgba(220,190,70,0.7)", 1, 2); }   // (the heather in flower, and gorse)
      else if (kind === "rock") { p.fillStyle = "#77736A"; p.fillRect(0, 0, N, N); dots(1400, "rgba(150,145,134,0.45)", 1, 4); dots(900, "rgba(84,80,74,0.5)", 1, 4);
        p.strokeStyle = "rgba(52,50,46,0.7)"; p.lineWidth = 1.6; for (let i = 0; i < 14; i++) { let x = rnd.next() * N, y = rnd.next() * N; p.beginPath(); p.moveTo(x, y); for (let j = 0; j < 5; j++) { x += (rnd.next() - 0.5) * 50; y += (rnd.next() - 0.5) * 50; p.lineTo(x, y); } p.stroke(); }
        dots(90, "rgba(176,170,92,0.55)", 2, 6); dots(70, "rgba(96,120,64,0.6)", 2, 5); }   // (cracks, and lichen)
      else { p.fillStyle = "#C9B48A"; p.fillRect(0, 0, N, N); dots(2600, "rgba(226,210,170,0.5)", 0.6, 1.8); dots(1600, "rgba(150,130,96,0.45)", 0.6, 1.6); dots(30, "rgba(240,236,224,0.8)", 1.5, 3); }
      return c; }; }
  // what grows and lies on the heath, on the heath
  const lift = (fl, x, z) => { const cx = Math.floor(x), cz = Math.floor(z), L = fl.levels && fl.levels[`${cx},${cz}`]; return L ? L[0] : CM.isScarp(cx, cz) && !(cz === S.stair.y && cx >= S.stair.x0 && cx <= S.stair.x1) ? S.h : 0; };
  { const pi0 = CM.plantInstancesOf; if (pi0) CM.plantInstancesOf = (game, fl, at, reach, density) => { const out = pi0(game, fl, at, reach, density); if (!fl || fl.number !== -1 || !fl.levels) return out;
      for (const p of out) { const h = lift(fl, p.x, p.z); if (h) p.y += h; }
      const M = (CM.plantsPack && CM.plantsPack.manifest && CM.plantsPack.manifest.models) || {}, [ax, ay] = at || fl.pos; if (!(density > 0) || Math.abs(ax - 50) + Math.abs(ay - 68) > (reach || 12) + 22) return out;
      const put = (name, x, z, y, size, salt, shade = 0.7) => { const m = M[name]; if (!m || Math.abs(x - ax) + Math.abs(z - ay) > (reach || 12) + 3) return; const lo = m.box[0], hi = m.box[1], w = Math.max(1e-3, hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2]), sc = size * 0.62 / w, hh = CM.hashSeed(`scarp:${salt}`);
        out.push({ model: name, x: x - (lo[0] + hi[0]) / 2 * sc, y: y - lo[1] * sc, z: z - (lo[2] + hi[2]) / 2 * sc, yaw: (hh % 360) * Math.PI / 180, scale: sc, sway: 0, height: (hi[1] - lo[1]) * sc, shade, kind: "rock" }); };
      const r = (salt) => (CM.hashSeed(`scarpr:${salt}`) % 1000) / 1000;
      for (let y = S.y0; y <= S.y1; y++) { if (y === S.stair.y || (y >= S.pool[1] - 1 && y <= S.pool[3] + 1)) continue; if (r(`w${y}`) < 0.55) put(r(`wm${y}`) < 0.5 ? "rock1" : "rock2", S.x0 - 0.1 - r(`wx${y}`) * 0.25, y + 0.5, -0.15, 0.8 + r(`ws${y}`) * 0.7, `w${y}`, 0.62); }   // (fallen at the west foot)
      for (let x = S.x0; x <= S.x1; x++) for (const [y, side, k] of [[S.y0, -1, "n"], [S.y1, 1, "s"]]) if (r(`${k}${x}`) < 0.5) put(r(`${k}m${x}`) < 0.5 ? "rock2" : "rock1", x + 0.5, y + 0.5 + side * (0.6 + r(`${k}y${x}`) * 0.2), -0.15, 0.8 + r(`${k}s${x}`) * 0.6, `${k}${x}`, 0.62);
      for (let y = S.y0; y <= S.y1; y++) if (y !== S.stair.y && y !== S.falls[1] && r(`lw${y}`) < 0.6) put(r(`lwm${y}`) < 0.5 ? "rock2" : "rock1", S.x0 + 0.3 + r(`lwx${y}`) * 0.3, y + 0.5, S.h - 0.35, 0.9 + r(`lws${y}`) * 0.6, `lw${y}`, 0.68);   // (boulders along the lip: the edge is broken, not ruled)
      for (let x = S.x0 + 1; x <= S.x1; x++) for (const [y, k] of [[S.y0, "ln"], [S.y1, "ls"]]) if (r(`${k}${x}`) < 0.5) put(r(`${k}m${x}`) < 0.5 ? "rock1" : "rock2", x + 0.5, y + 0.5, S.h - 0.35, 0.9 + r(`${k}s${x}`) * 0.6, `${k}${x}`, 0.68);
      for (const [x, y] of S.tors) for (const [dx, dz] of [[-0.55, 0.2], [0.3, -0.6], [0.6, 0.55]]) if (r(`t${x},${y},${dx}`) < 0.6) put("rock1", x + 0.5 + dx, y + 0.5 + dz, S.h - 0.08, 0.7 + r(`ts${x},${y},${dx}`) * 0.5, `t${x},${y},${dx}`, 0.75);   // (the tors' tumbled skirts)
      for (let i = 0; i < 26; i++) { const x = S.x0 + 1 + Math.floor(r(`hx${i}`) * (S.x1 - S.x0 - 1)), y = S.y0 + 1 + Math.floor(r(`hy${i}`) * (S.y1 - S.y0 - 1)), k = `${x},${y}`; if (fl.grid[y][x] !== 0 || fl.things[k] || (fl.features[k] && fl.features[k].type === "river") || fl.ground[k] === "dirt" || fl.ground[k] === "planks") continue;
        put(r(`hm${i}`) < 0.5 ? "rock1" : "rock2", x + 0.25 + r(`hdx${i}`) * 0.5, y + 0.25 + r(`hdz${i}`) * 0.5, S.h - 0.06, 0.35 + r(`hs${i}`) * 0.4, `h${i}`, 0.8); }   // (stones lying in the heather)
      for (const [dx, dz, s] of [[-0.42, 0.3, 0.5], [0.38, 0.28, 0.45], [0, 0.48, 0.38]]) put("rock2", S.spring[0] + 0.5 + dx, S.spring[1] + 0.5 + dz, S.h - 0.05, s, `sp${dx}`, 0.75);   // (the spring's lip of rock)
      return out; }; }
  // the pictures: the falling water (four frames), the ice, the foam, the mist, the cairn
  { const b0 = CM.art.build; CM.art.build = function (theme, look) { const set = b0.call(this, theme, look), N = set.size, add = (n, c) => { set.index[n] = set.layers.length; set.layers.push(c); };
      const canvas = () => { const c = document.createElement("canvas"); c.width = c.height = N; return [c, c.getContext("2d")]; };
      const rnd = new CM.Random(CM.hashSeed("scarp:falls")), streaks = Array.from({ length: 120 }, () => { const u = rnd.next(), x = 0.5 + (u - 0.5) * (0.4 + 0.5 * rnd.next()); return [x, rnd.next(), 0.08 + rnd.next() * 0.3, 0.4 + rnd.next() * 0.6, 0.6 + rnd.next() * 1.4]; });
      for (let f = 0; f < 4; f++) { const [c, p] = canvas(), g = p.createLinearGradient(0, 0, N, 0);
        g.addColorStop(0, "rgba(190,214,222,0)"); g.addColorStop(0.18, "rgba(190,214,222,0.5)"); g.addColorStop(0.5, "rgba(214,232,238,0.78)"); g.addColorStop(0.82, "rgba(190,214,222,0.5)"); g.addColorStop(1, "rgba(190,214,222,0)"); p.fillStyle = g; p.fillRect(0, 0, N, N);
        for (const [x, y0, len, a, wd] of streaks) { const y = ((y0 + f / 4) % 1) * N, L = len * N; p.fillStyle = `rgba(250,252,255,${a})`; p.fillRect(x * N - wd, y, wd * 2, L); if (y + L > N) p.fillRect(x * N - wd, y - N, wd * 2, L); }
        const fg = p.createLinearGradient(0, N * 0.86, 0, N); fg.addColorStop(0, "rgba(255,255,255,0)"); fg.addColorStop(1, "rgba(255,255,255,0.85)"); p.fillStyle = fg; p.fillRect(N * 0.12, N * 0.86, N * 0.76, N * 0.14);   // (white where it hits)
        add(`fx:falls${f}`, c); }
      { const [c, p] = canvas(); for (let i = 0; i < 40; i++) { const x = N * (0.15 + rnd.next() * 0.7), w = N * (0.02 + rnd.next() * 0.05), l = N * (0.3 + rnd.next() * 0.65); const g = p.createLinearGradient(0, 0, 0, l); g.addColorStop(0, "rgba(226,240,250,0.95)"); g.addColorStop(1, "rgba(190,220,240,0.2)"); p.fillStyle = g; p.beginPath(); p.moveTo(x - w, 0); p.lineTo(x + w, 0); p.lineTo(x, l); p.closePath(); p.fill(); } add("fx:fallsice", c); }
      for (let f = 0; f < 3; f++) { const [c, p] = canvas(), r2 = new CM.Random(CM.hashSeed(`scarp:foam${f}`)); for (let i = 0; i < 90; i++) { const a = r2.next() * Math.PI * 2, d = Math.sqrt(r2.next()) * N * 0.45, x = N / 2 + Math.cos(a) * d, y = N / 2 + Math.sin(a) * d, rr = 3 + r2.next() * 10 * (1 - d / N);
          p.fillStyle = `rgba(245,250,252,${0.25 + 0.5 * (1 - d / (N * 0.45))})`; p.beginPath(); p.arc(x, y, rr, 0, Math.PI * 2); p.fill(); } add(`fx:foam${f}`, c); }
      { const [c, p] = canvas(), g = p.createRadialGradient(N / 2, N / 2, 0, N / 2, N / 2, N / 2); g.addColorStop(0, "rgba(240,246,250,0.75)"); g.addColorStop(0.6, "rgba(232,240,246,0.3)"); g.addColorStop(1, "rgba(232,240,246,0)"); p.fillStyle = g; p.fillRect(0, 0, N, N); add("fx:mist", c); }
      { const [c, p] = canvas(), u = N / 64, r3 = new CM.Random(CM.hashSeed("scarp:cairn")); let y = 62 * u, w = 26 * u;
        while (w > 5 * u) { const h = (5 + r3.next() * 3) * u, x = 32 * u + (r3.next() - 0.5) * 4 * u, k = 0.8 + r3.next() * 0.35; p.fillStyle = `rgb(${Math.round(124 * k)},${Math.round(120 * k)},${Math.round(112 * k)})`; p.beginPath(); p.ellipse(x, y - h / 2, w / 2, h / 2, 0, 0, Math.PI * 2); p.fill();
          p.fillStyle = "rgba(255,255,255,0.12)"; p.beginPath(); p.ellipse(x - w * 0.12, y - h * 0.7, w * 0.3, h * 0.22, 0, 0, Math.PI * 2); p.fill(); y -= h * 0.82; w *= 0.8; }
        add("prop:cairn", c); }
      { const [c, p] = canvas(), r4 = new CM.Random(CM.hashSeed("scarp:face")), R = () => r4.next();   // the scarp's face: weathered beds of grey-brown stone, broken ledges, cracks, lichen and moss, the heather hanging over its lip
        p.fillStyle = "#7C7466"; p.fillRect(0, 0, N, N);
        for (const [n, r0, r1, a] of [[60, 18, 46, 0.16], [260, 6, 18, 0.14], [1400, 1, 5, 0.18]]) for (let i = 0; i < n; i++) { const k = R(); p.fillStyle = k < 0.5 ? `rgba(${150 + R() * 40},${142 + R() * 34},${122 + R() * 30},${a})` : `rgba(${40 + R() * 30},${36 + R() * 26},${30 + R() * 20},${a})`; p.beginPath(); p.ellipse(R() * N, R() * N, r0 + R() * (r1 - r0), (r0 + R() * (r1 - r0)) * 0.55, (R() - 0.5) * 0.5, 0, Math.PI * 2); p.fill(); }
        const wave = (y0, a, f, ph) => (x) => y0 + Math.sin(x * f + ph) * a + Math.sin(x * f * 2.7 + ph * 1.9) * a * 0.4;
        for (let b = 0; b < 7; b++) { const yb = wave(N * (0.1 + b * 0.13 + (R() - 0.5) * 0.04), 2 + R() * 5, 0.02 + R() * 0.03, R() * 6), x0 = R() * N * 0.3, x1 = N * (0.7 + R() * 0.3);
          p.strokeStyle = "rgba(40,36,30,0.38)"; p.lineWidth = 1 + R() * 1.4; p.beginPath(); for (let x = x0; x <= x1; x += 4) (x === x0 ? p.moveTo : p.lineTo).call(p, x, yb(x)); p.stroke();   // (a ledge's shadow)
          p.strokeStyle = "rgba(226,218,196,0.22)"; p.lineWidth = 1; p.beginPath(); for (let x = x0; x <= x1; x += 4) (x === x0 ? p.moveTo : p.lineTo).call(p, x, yb(x) - 2.2); p.stroke(); }   // (its lit top)
        p.strokeStyle = "rgba(30,28,24,0.4)"; for (let i = 0; i < 12; i++) { let x = R() * N, y = R() * N; p.lineWidth = 0.8 + R() * 1.4; p.beginPath(); p.moveTo(x, y); for (let j = 0; j < 3 + R() * 4; j++) { x += (R() - 0.5) * 14; y += 4 + R() * 12; p.lineTo(x, y); } p.stroke(); }   // (cracks, running down)
        for (let i = 0; i < 30; i++) { p.fillStyle = R() < 0.55 ? "rgba(176,170,96,0.5)" : "rgba(214,210,176,0.42)"; p.beginPath(); p.arc(R() * N, R() * N, 1.5 + R() * 4.5, 0, Math.PI * 2); p.fill(); }
        for (let i = 0; i < 10; i++) { const x = R() * N, l = N * (0.08 + R() * 0.3), g = p.createLinearGradient(0, 0, 0, l); g.addColorStop(0, "rgba(68,92,44,0.7)"); g.addColorStop(1, "rgba(68,92,44,0)"); p.fillStyle = g; p.fillRect(x, 0, 2 + R() * 7, l); }
        p.fillStyle = "#56603A"; p.beginPath(); p.moveTo(0, 0); for (let x = 0; x <= N; x += 4) p.lineTo(x, N * 0.04 + Math.abs(Math.sin(x * 0.31) * 6 + Math.sin(x * 0.07) * 5)); p.lineTo(N, 0); p.closePath(); p.fill();
        p.fillStyle = "rgba(128,78,120,0.8)"; for (let i = 0; i < 40; i++) p.fillRect(R() * N, R() * N * 0.05, 2, 2);
        add("solid:scarp", c); }
      return set; }; }
  // the falls, the pool, the cairn, as the hour goes
  const pool = [S.falls[0] - 1, S.falls[1]];
  { const ls0 = CM.lifeSprites; CM.lifeSprites = (game, fl, now) => { const out = ls0 ? ls0(game, fl, now) : []; if (!fl || fl.number !== -1 || !fl.levels || game.mode === "title") return out;
      out.push({ x: S.lookout[0], y: S.lookout[1] + 1, dx: -0.12, dz: -0.3, base: S.h, layer: "prop:cairn", w: 0.62, h: 0.78, shade: 0.95 });   // (at the brink, on the rock's lip)
      if (Math.abs(fl.pos[0] - pool[0]) + Math.abs(fl.pos[1] - pool[1]) > 26) return out;
      const ice = fl.frozen || (CM.weather && CM.weather(game) === "snow"), H = S.h, t = CM.reducedMotion ? 0 : now / 1000;
      if (ice) { out.push({ x: pool[0], y: pool[1], face: 1, layer: "fx:fallsice", w: 0.9, h: H, lift: H / 2 - 0.5, alpha: 0.9, glow: 0.15 }); return out; }
      const f = Math.floor(now / 85) % 4;
      out.push({ x: pool[0], y: pool[1], face: 1, layer: `fx:falls${f}`, w: 0.88, h: H, lift: H / 2 - 0.5, alpha: 0.95, glow: 0.3 });
      out.push({ x: pool[0], y: pool[1], dx: 0.36, layer: `fx:falls${(f + 2) % 4}`, w: 0.62, h: S.h * 0.86, alpha: 0.42, glow: 0.25 });   // (a veil of spray before it)
      out.push({ x: S.falls[0], y: S.falls[1], dx: -0.3, flat: true, layer: `fx:foam${Math.floor(now / 160) % 3}`, w: 0.5, alpha: 0.55 });   // (the lip, white where it goes over)
      out.push({ x: pool[0], y: pool[1], dx: 0.12, flat: true, layer: `fx:foam${Math.floor(now / 140) % 3}`, w: 1.15, alpha: 0.8 });
      out.push({ x: pool[0] - 1, y: pool[1], dx: 0.2, flat: true, layer: `fx:foam${(Math.floor(now / 170) + 1) % 3}`, w: 0.9, alpha: 0.38 });
      for (let i = 0; i < 6; i++) { const ph = (t * 0.22 + i / 6) % 1, sz = 0.55 + ph * 0.9;   // (mist off the pool, rising and thinning)
        out.push({ x: pool[0], y: pool[1], dx: 0.25 - ph * 0.5 + Math.sin(i * 2.3) * 0.2, dz: Math.cos(i * 1.7) * 0.35, layer: "fx:mist", w: sz, h: sz, lift: ph * 1.6, alpha: 0.32 * (1 - ph) * (ph < 0.1 ? ph * 10 : 1) }); }
      return out; }; }
}
