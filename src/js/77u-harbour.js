"use strict";
// The harbour, seen (UPGRADE_PLAN_80.md, v130.0; the land 23g-harbour.js, the rules 69zzzzh-harbour.js): the pier and
// the dock built - the deck's edge beams, piles going down into the sea at every corner with weed on them where the
// water reaches, a rail along each side (open on the dock's south face, where a boat comes alongside), bollards and
// iron rings on that face, and lanterns on posts along the pier that are lit from dusk to dawn.
{ const H = CM.HARBOUR;
  // the wood of the piles: dark, wet, green-slimed below the tide line
  { const b0 = CM.art.build; CM.art.build = function (theme, look) { const set = b0.call(this, theme, look), N = set.size, add = (n, c) => { set.index[n] = set.layers.length; set.layers.push(c); };
      { const c = document.createElement("canvas"); c.width = c.height = N; const p = c.getContext("2d"), r = new CM.Random(CM.hashSeed("harbour:pile"));
        p.fillStyle = "#5A4632"; p.fillRect(0, 0, N, N); for (let i = 0; i < 60; i++) { p.fillStyle = r.next() < 0.5 ? "rgba(30,22,14,0.35)" : "rgba(140,118,90,0.25)"; p.fillRect(r.next() * N, 0, 1 + r.next() * 3, N); }
        const g = p.createLinearGradient(0, N * 0.45, 0, N); g.addColorStop(0, "rgba(40,70,40,0)"); g.addColorStop(0.25, "rgba(40,74,44,0.75)"); g.addColorStop(1, "rgba(24,46,30,0.95)"); p.fillStyle = g; p.fillRect(0, N * 0.45, N, N * 0.55);
        p.fillStyle = "rgba(230,230,220,0.5)"; for (let i = 0; i < 30; i++) { p.beginPath(); p.arc(r.next() * N, N * (0.5 + r.next() * 0.12), 1.5 + r.next() * 2.5, 0, Math.PI * 2); p.fill(); }   // (barnacles at the tide line)
        add("solid:pile", c); }
      { const c = document.createElement("canvas"); c.width = c.height = N; const p = c.getContext("2d"), u = N / 64;   // a ship's lantern on its post
        p.fillStyle = "#2A2420"; p.fillRect(30 * u, 22 * u, 4 * u, 42 * u); p.fillRect(24 * u, 20 * u, 16 * u, 3 * u); p.fillStyle = "#3A322A"; p.fillRect(25 * u, 4 * u, 14 * u, 3 * u); p.fillRect(26 * u, 7 * u, 2 * u, 13 * u); p.fillRect(36 * u, 7 * u, 2 * u, 13 * u);
        p.fillStyle = "rgba(255,214,140,0.9)"; p.fillRect(28 * u, 8 * u, 8 * u, 12 * u); add("harbour:lantern", c);
        const d = document.createElement("canvas"); d.width = d.height = N; const q = d.getContext("2d"); q.fillStyle = "#2A2420"; q.fillRect(30 * u, 22 * u, 4 * u, 42 * u); q.fillRect(24 * u, 20 * u, 16 * u, 3 * u); q.fillStyle = "#3A322A"; q.fillRect(25 * u, 4 * u, 14 * u, 3 * u); q.fillRect(26 * u, 7 * u, 2 * u, 13 * u); q.fillRect(36 * u, 7 * u, 2 * u, 13 * u);
        q.fillStyle = "rgba(120,110,90,0.7)"; q.fillRect(28 * u, 8 * u, 8 * u, 12 * u); add("harbour:lanternout", d); }
      return set; }; }
  // the build: put(a, b, c, d, layer, shade, glow) - a quad, as the far views are given them
  { const fv0 = CM.farViews; CM.farViews = (fl, size, index, night, put) => { const n = fv0 ? fv0(fl, size, index, night, put) : 0; if (!fl || fl.number !== -1 || !fl.levels || size <= H.head[3]) return n;
      const wood = index["solid:timber"], pile = index["solid:pile"] !== undefined ? index["solid:pile"] : wood; if (wood === undefined) return n;
      const lvl = (x, y) => { const L = fl.levels[`${x},${y}`]; return L ? L[0] : 0; }, pier = (x, y) => CM.isPier(x, y);
      const box = (x0, z0, x1, z1, y0, y1, layer, sh) => { put([x0, y0, z0], [x1, y0, z0], [x1, y1, z0], [x0, y1, z0], layer, sh, 0); put([x1, y0, z1], [x0, y0, z1], [x0, y1, z1], [x1, y1, z1], layer, sh * 0.9, 0);
        put([x0, y0, z1], [x0, y0, z0], [x0, y1, z0], [x0, y1, z1], layer, sh * 0.8, 0); put([x1, y0, z0], [x1, y0, z1], [x1, y1, z1], [x1, y1, z0], layer, sh * 0.85, 0); put([x0, y1, z0], [x1, y1, z0], [x1, y1, z1], [x0, y1, z1], layer, sh * 1.05, 0); };
      const berthSide = (x, y, d) => d === 2 && y === H.head[3];
      for (let y = H.foot; y <= H.head[3]; y++) for (let x = H.head[0]; x <= H.head[2]; x++) { if (!pier(x, y)) continue; const F = lvl(x, y), deck = y >= H.foot + 2;
        CM.DIRS.forEach(([dx, dy], d) => { const nx = x + dx, ny = y + dy; if (pier(nx, ny) || (CM.isLighthouseRock && CM.isLighthouseRock(nx, ny)) || (ny < CM.SHORE.sea && !deck)) return;   // (v132.0: open onto the lighthouse's rock)
          if (ny < CM.SHORE.sea && fl.grid[ny] && fl.grid[ny][nx] === 0) return;   // (on the sand: the step's own face does)
          const a = d === 0 ? [x, y] : d === 1 ? [x + 1, y] : d === 2 ? [x + 1, y + 1] : [x, y + 1], b = d === 0 ? [x + 1, y] : d === 1 ? [x + 1, y + 1] : d === 2 ? [x, y + 1] : [x, y];
          put([a[0], F - 0.24, a[1]], [b[0], F - 0.24, b[1]], [b[0], F, b[1]], [a[0], F, a[1]], wood, 0.72, 0);   // (the edge beam)
          if (!deck) return;
          for (const t of [0.12, 0.88]) { const px = a[0] + (b[0] - a[0]) * t - dx * 0.08, pz = a[1] + (b[1] - a[1]) * t - dy * 0.08; box(px - 0.07, pz - 0.07, px + 0.07, pz + 0.07, -1.1, F - 0.02, pile, 0.8); }   // (piles)
          if (berthSide(x, y, d)) { const mx = (a[0] + b[0]) / 2 - dx * 0.2, mz = (a[1] + b[1]) / 2 - dy * 0.2; if ((x - H.head[0]) % 3 === 1) box(mx - 0.09, mz - 0.09, mx + 0.09, mz + 0.09, F, F + 0.22, wood, 0.6); return; }   // (bollards on the berth)
          for (const t of [0, 0.5]) { const px = a[0] + (b[0] - a[0]) * t - dx * 0.06, pz = a[1] + (b[1] - a[1]) * t - dy * 0.06; box(px - 0.035, pz - 0.035, px + 0.035, pz + 0.035, F, F + 0.42, wood, 0.75); }   // (rail posts)
          const ia = [a[0] - dx * 0.06, a[1] - dy * 0.06], ib = [b[0] - dx * 0.06, b[1] - dy * 0.06]; box(Math.min(ia[0], ib[0]) - 0.02, Math.min(ia[1], ib[1]) - 0.02, Math.max(ia[0], ib[0]) + 0.02, Math.max(ia[1], ib[1]) + 0.02, F + 0.38, F + 0.45, wood, 0.85); }); }   // (the rail)
      return n + 1; }; }
  // lanterns along the pier, lit from dusk to dawn
  const LAMPS = []; for (let y = H.foot + 3; y < H.head[1]; y += 3) LAMPS.push([H.pier[0], y, -0.42], [H.pier[1], y, 0.42]); LAMPS.push([H.head[0], H.head[1], -0.4], [H.head[2], H.head[1], 0.4]);
  { const ls0 = CM.lifeSprites; CM.lifeSprites = (game, fl, now) => { const out = ls0 ? ls0(game, fl, now) : []; if (!fl || fl.number !== -1 || !fl.levels || game.mode === "title" || fl.grid.length <= H.head[3] || Math.abs(fl.pos[1] - H.head[1]) > 30) return out;
      const lit = CM.isNight ? CM.isNight(game) : false;
      for (const [x, y, dx] of LAMPS) { out.push({ x, y, dx, layer: lit ? "harbour:lantern" : "harbour:lanternout", w: 0.5, h: 1.15, glow: lit ? 0.9 : 0 }); if (lit) out.push({ x, y, dx, layer: "fx:mist", w: 0.5, h: 0.5, lift: 0.82, alpha: 0.35, glow: 1 }); }
      return out; }; }
}
