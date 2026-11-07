"use strict";
// The lighthouse, seen (UPGRADE_PLAN_80.md, v132.0; the land 23i-lighthouse.js, the rules 69zzzzj-lighthouse.js): the
// tower built of eight faces banded red and white, narrowing as it rises, a door on its west face, an iron gallery
// round its top, the lamp room's glazing over that and a red cap; the rock it stands on, its edges falling into the
// sea, boulders about its foot; and when the lamp is lit, its glow, and two beams going round over the water.
{ const L = CM.LIGHTHOUSE, B = (CM.HARBOUR && CM.HARBOUR.deck) || 0.45, cx = L.at[0] + 0.5, cz = L.at[1] + 0.5, TOP = L.h;
  { const b0 = CM.art.build; CM.art.build = function (theme, look) { const set = b0.call(this, theme, look), N = set.size, add = (n, c) => { set.index[n] = set.layers.length; set.layers.push(c); };
      const can = () => { const c = document.createElement("canvas"); c.width = c.height = N; return [c, c.getContext("2d")]; };
      { const [c, p] = can(), r = new CM.Random(CM.hashSeed("lh:bands"));   // the tower's face: four bands, white and red, weathered
        for (let i = 0; i < 4; i++) { p.fillStyle = i % 2 ? "#B8332A" : "#EDE8DE"; p.fillRect(0, (i * N) / 4, N, N / 4 + 1); }
        for (let i = 0; i < 500; i++) { p.fillStyle = r.next() < 0.5 ? "rgba(60,50,40,0.08)" : "rgba(255,255,255,0.08)"; p.fillRect(r.next() * N, r.next() * N, 2 + r.next() * 6, 1 + r.next() * 3); }
        const g = p.createLinearGradient(0, N * 0.85, 0, N); g.addColorStop(0, "rgba(40,50,40,0)"); g.addColorStop(1, "rgba(40,50,40,0.45)"); p.fillStyle = g; p.fillRect(0, N * 0.85, N, N * 0.15);
        for (let i = 0; i < 3; i++) { p.fillStyle = "#2A2A30"; p.fillRect(N * 0.42, N * (0.18 + i * 0.25), N * 0.16, N * 0.07); }   // (a slit window on each band)
        add("solid:lighthouse", c); }
      { const [c, p] = can(); p.fillStyle = "#2A2420"; p.fillRect(N * 0.1, 0, N * 0.8, N); p.fillStyle = "#4A3A2A"; p.fillRect(N * 0.16, N * 0.06, N * 0.68, N * 0.94); p.fillStyle = "#C8A040"; p.fillRect(N * 0.68, N * 0.5, N * 0.06, N * 0.06); add("lh:door", c); }
      { const [c, p] = can(); p.fillStyle = "#1E1E22"; p.fillRect(0, 0, N, N * 0.05); p.fillRect(0, N * 0.95, N, N * 0.05); p.fillRect(0, 0, N * 0.035, N); p.fillRect(N * 0.965, 0, N * 0.035, N); add("lh:glass", c); }   // (the lamp room's frames: the panes are clear)
      { const [c, p] = can(); p.fillStyle = "#9A2A22"; p.fillRect(0, 0, N, N); p.fillStyle = "rgba(0,0,0,0.18)"; for (let i = 0; i < N; i += N / 8) p.fillRect(i, 0, 2, N); add("lh:cap", c); }
      { const [c, p] = can(); p.fillStyle = "#26262A"; p.fillRect(0, N * 0.1, N, N * 0.12); for (let i = 0; i < 5; i++) p.fillRect(i * N / 4 - 2, N * 0.1, 5, N * 0.9); add("lh:rail", c); }   // (the gallery's rail: open between its bars)
      { const [c, p] = can(), g = p.createLinearGradient(0, N, 0, 0); g.addColorStop(0, "rgba(255,244,200,0.95)"); g.addColorStop(0.35, "rgba(255,236,180,0.55)"); g.addColorStop(1, "rgba(255,230,170,0)"); p.fillStyle = g; p.fillRect(0, 0, N, N);
        const e = p.createLinearGradient(0, 0, N, 0); e.addColorStop(0, "rgba(0,0,0,1)"); e.addColorStop(0.25, "rgba(0,0,0,0)"); e.addColorStop(0.75, "rgba(0,0,0,0)"); e.addColorStop(1, "rgba(0,0,0,1)"); p.globalCompositeOperation = "destination-out"; p.fillStyle = e; p.fillRect(0, 0, N, N); add("fx:beam", c); }
      return set; }; }
  // the build
  { const fv0 = CM.farViews; CM.farViews = (fl, size, index, night, put) => { const n = fv0 ? fv0(fl, size, index, night, put) : 0; if (!fl || fl.number !== -1 || !fl.levels || size <= L.rock[3] + 1 || index["solid:lighthouse"] === undefined) return n;
      const face = index["solid:lighthouse"], glass = index["lh:glass"], cap = index["lh:cap"], rail = index["lh:rail"], door = index["lh:door"], iron = index["lh:rail"], rock = index["solid:scarp"] !== undefined ? index["solid:scarp"] : index["solid:cliff"];
      const at = (i, r) => { const a = (Math.PI / 4) * i + Math.PI / 8; return [cx + Math.cos(a) * r, cz + Math.sin(a) * r]; }, sh = (i) => 0.72 + 0.28 * Math.abs(Math.cos((Math.PI / 4) * i + Math.PI / 4 - 0.6));
      for (let i = 0; i < 8; i++) { const [ax, az] = at(i, L.r0), [bx, bz] = at(i + 1, L.r0), [ax1, az1] = at(i, L.r1), [bx1, bz1] = at(i + 1, L.r1);
        put([ax, B, az], [bx, B, bz], [bx1, TOP, bz1], [ax1, TOP, az1], face, sh(i), 0);                                           // the tower's face
        const [gx, gz] = at(i, 0.62), [hx, hz] = at(i + 1, 0.62);
        put([ax1, TOP, az1], [bx1, TOP, bz1], [hx, TOP, hz], [gx, TOP, gz], iron, 0.5, 0); put([gx, TOP - 0.08, gz], [hx, TOP - 0.08, hz], [hx, TOP, hz], [gx, TOP, gz], iron, 0.45, 0);   // the gallery's floor and its edge
        put([gx, TOP, gz], [hx, TOP, hz], [hx, TOP + 0.36, hz], [gx, TOP + 0.36, gz], rail, 0.6, 0);                             // its rail
        const [lx, lz] = at(i, 0.3), [mx, mz] = at(i + 1, 0.3), [kx, kz] = at(i, 0.38), [jx, jz] = at(i + 1, 0.38);
        put([lx, TOP, lz], [mx, TOP, mz], [mx, TOP + 0.62, mz], [lx, TOP + 0.62, lz], glass, 0.7, 0);                            // the lamp room's glazing
        put([kx, TOP + 0.62, kz], [jx, TOP + 0.62, jz], [cx, TOP + 1.1, cz], [cx, TOP + 1.1, cz], cap, sh(i) * 0.9, 0); }           // the cap
      { const s = 0.04; put([cx - s, TOP + 1.1, cz], [cx + s, TOP + 1.1, cz], [cx + s, TOP + 1.3, cz], [cx - s, TOP + 1.3, cz], iron, 0.5, 0); put([cx, TOP + 1.1, cz - s], [cx, TOP + 1.1, cz + s], [cx, TOP + 1.3, cz + s], [cx, TOP + 1.3, cz - s], iron, 0.5, 0); }   // (the vane's rod)
      { const [ax, az] = at(3, L.r0 + 0.01), [bx, bz] = at(4, L.r0 + 0.01), m = 0.2; put([ax + (bx - ax) * m, B, az + (bz - az) * m], [ax + (bx - ax) * (1 - m), B, az + (bz - az) * (1 - m)], [ax + (bx - ax) * (1 - m), B + 0.78, az + (bz - az) * (1 - m)], [ax + (bx - ax) * m, B + 0.78, az + (bz - az) * m], door, 0.85, 0); }   // the door, facing the dock
      { const g = index["ground:rock"]; if (g !== undefined) put([L.at[0], B, L.at[1] + 1], [L.at[0] + 1, B, L.at[1] + 1], [L.at[0] + 1, B, L.at[1]], [L.at[0], B, L.at[1]], g, 0.8, 0); }   // (the rock under the tower)
      // the rock: its edges falling into the sea
      const [x0, y0, x1, y1] = L.rock, onRock = (x, y) => CM.isLighthouseRock(x, y), joined = (x, y) => onRock(x, y) || (CM.isPier && CM.isPier(x, y));
      for (let y = y0; y <= y1; y++) for (let x = x0; x <= x1; x++) CM.DIRS.forEach(([dx, dy], d) => { if (joined(x + dx, y + dy)) return;
        const a = d === 0 ? [x, y] : d === 1 ? [x + 1, y] : d === 2 ? [x + 1, y + 1] : [x, y + 1], b = d === 0 ? [x + 1, y] : d === 1 ? [x + 1, y + 1] : d === 2 ? [x, y + 1] : [x, y];
        put([a[0] + dx * 0.25, -0.9, a[1] + dy * 0.25], [b[0] + dx * 0.25, -0.9, b[1] + dy * 0.25], [b[0], B, b[1]], [a[0], B, a[1]], rock, 0.7, 0); });
      return n + 1; }; }
  // boulders round the rock's foot
  { const pi0 = CM.plantInstancesOf; if (pi0) CM.plantInstancesOf = (game, fl, at, reach, density) => { const out = pi0(game, fl, at, reach, density); if (!fl || fl.number !== -1 || !fl.levels || !(density > 0) || fl.grid.length <= L.rock[3] + 1) return out;
      const M = (CM.plantsPack && CM.plantsPack.manifest && CM.plantsPack.manifest.models) || {}, [ax, ay] = at || fl.pos; if (Math.abs(ax - L.at[0]) + Math.abs(ay - L.at[1]) > (reach || 12) + 6) return out;
      const put = (name, x, z, y, size, salt) => { const m = M[name]; if (!m) return; const lo = m.box[0], hi = m.box[1], w = Math.max(1e-3, hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2]), sc = size * 0.62 / w, hh = CM.hashSeed(`lh:${salt}`);
        out.push({ model: name, x: x - (lo[0] + hi[0]) / 2 * sc, y: y - lo[1] * sc, z: z - (lo[2] + hi[2]) / 2 * sc, yaw: (hh % 360) * Math.PI / 180, scale: sc, sway: 0, height: (hi[1] - lo[1]) * sc, shade: 0.6, kind: "rock" }); };
      const [x0, y0, x1, y1] = L.rock;
      for (let x = x0; x <= x1 + 1; x++) { put(x % 2 ? "rock1" : "rock2", x + 0.1, y0 - 0.15, -0.5, 1.5, `n${x}`); put(x % 2 ? "rock2" : "rock1", x - 0.1, y1 + 1.15, -0.5, 1.5, `s${x}`); }
      for (let y = y0; y <= y1; y++) put(y % 2 ? "rock1" : "rock2", x1 + 1.2, y + 0.5, -0.5, 1.6, `e${y}`);
      return out; }; }
  // the lamp, lit: its glow, and the two beams going round
  { const ls0 = CM.lifeSprites; CM.lifeSprites = (game, fl, now) => { const out = ls0 ? ls0(game, fl, now) : []; if (!fl || fl.number !== -1 || !fl.levels || game.mode === "title" || fl.grid.length <= L.rock[3] + 1 || !CM.lighthouseLit || !CM.lighthouseLit(game)) return out;
      const t = CM.reducedMotion ? 1 : now / 1000, y = TOP + 0.32, [x, z] = L.at;
      out.push({ x, y: z, lift: y - 0.55, layer: "fx:mist", w: 1.1, h: 1.1, alpha: 0.9, glow: 1.3 }, { x, y: z, lift: y - 0.25, layer: "fx:mist", w: 0.5, h: 0.5, alpha: 1, glow: 1.3 });
      for (const off of [0, Math.PI]) { const a = t * 0.55 + off, d = [Math.cos(a), Math.sin(a)], p = [-d[1], d[0]], len = 34, w0 = 0.14, w1 = 2.8, O = [cx, y, cz], E = [cx + d[0] * len, y - 1.6, cz + d[1] * len];
        out.push({ x, y: z, quad: [[O[0] - p[0] * w0, O[1], O[2] - p[1] * w0], [O[0] + p[0] * w0, O[1], O[2] + p[1] * w0], [E[0] + p[0] * w1, E[1], E[2] + p[1] * w1], [E[0] - p[0] * w1, E[1], E[2] - p[1] * w1]], layer: "fx:beam", alpha: 0.75, glow: 1.3 });
        out.push({ x, y: z, quad: [[O[0], O[1] - w0, O[2]], [O[0], O[1] + w0, O[2]], [E[0], E[1] + w1 * 0.55, E[2]], [E[0], E[1] - w1 * 0.55, E[2]]], layer: "fx:beam", alpha: 0.75, glow: 1.3 }); }
      return out; }; }
}
