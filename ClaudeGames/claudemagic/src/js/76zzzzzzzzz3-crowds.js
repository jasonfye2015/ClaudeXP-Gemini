"use strict";
// Crowds that move (v51.3, UPGRADE_PLAN_46.md): by day Caer Duin's streets have people going about them - a handful of
// townsfolk walking from one door to another (the tavern, the merchant's, the smith's, the Library, the Temple, the
// Guildhall, the Square), pausing at each, then setting off again - more at midday, fewer at dusk, none in the small
// hours. Only seen: they are not in the way, and the ones to talk to stand where they always did.
{ const LOOKS = ["npc:adventurer", "npc:fieldhand", "npc:porter", "npc:lamplighter", "npc:res_farm", "npc:hermit"];
  const routes = new WeakMap(), pathOf = (fl, a, b) => { const N = fl.grid.length, open = (x, y) => fl.grid[y] && fl.grid[y][x] === 0, prev = new Map([[`${a[0]},${a[1]}`, null]]), q = [a];
    while (q.length) { const [x, y] = q.shift(); if (x === b[0] && y === b[1]) break; for (const [dx, dy] of CM.DIRS) { const nx = x + dx, ny = y + dy, k = `${nx},${ny}`; if (nx < 0 || ny < 0 || nx >= N || ny >= N || prev.has(k) || !open(nx, ny)) continue; prev.set(k, [x, y]); q.push([nx, ny]); } }
    const out = []; let c = `${b[0]},${b[1]}`; if (!prev.has(c)) return null; while (c) { const [x, y] = c.split(",").map(Number); out.unshift([x, y]); const p = prev.get(c); c = p ? `${p[0]},${p[1]}` : null; } return out; };
  const doorsOf = (fl) => { const open = (x, y) => fl.grid[y] && fl.grid[y][x] === 0, D = []; for (const id of ["tavern", "merchant", "smith", "library", "temple", "guildhall", "chronicler", "well", "market", "cross"]) { const at = CM.TOWN_AT && CM.TOWN_AT[id]; if (!at) continue;
      if (open(at[0], at[1])) D.push(at); else for (const [dx, dy] of CM.DIRS) if (open(at[0] + dx, at[1] + dy)) { D.push([at[0] + dx, at[1] + dy]); break; } } return D; };
  const walkerOf = (fl, i) => { let R = routes.get(fl); if (!R) { R = { doors: doorsOf(fl), legs: new Map() }; routes.set(fl, R); } const D = R.doors; if (D.length < 2) return null;
    const leg = (n) => { const k = `${i}:${n}`; if (R.legs.has(k)) return R.legs.get(k); const at = (m) => D[(i * 5 + m * (D.length % 3 ? 3 : 7) + (CM.hashSeed(`walk:${i}`) >>> 0)) % D.length], a = at(n), b = at(n + 1);   /* (each door the next leg's start: never the same twice running) */ const p = pathOf(fl, a, b); R.legs.set(k, p); return p; };
    return leg; };
  const count = (game) => { const h = CM.hourOf(game); return h < 6 || h >= 22 ? 0 : h < 8 || h >= 19 ? 3 : h >= 11 && h < 15 ? 8 : 6; };
  { const ls0 = CM.lifeSprites; CM.lifeSprites = (game, fl, now) => { const out = ls0 ? ls0(game, fl, now) : []; if (!fl || fl.number !== 0 || game.mode === "title" || !CM.renderer) return out; const n = count(game); if (!n) return out;
      const t = now / 1000, SPEED = 0.9, PAUSE = 6;
      for (let i = 0; i < n; i++) { const leg = walkerOf(fl, i); if (!leg) break; const look = LOOKS[i % LOOKS.length]; if (CM.renderer.index[look] === undefined) continue;
        let clock = t + i * 37, k = Math.floor(clock / 60), p = leg(k);   /* (leg k goes from the door leg k-1 reached to the next: one walk, end to end) */ if (!p || p.length < 2) continue;   // (a leg a minute or so: its own path, then a pause at the door)
        const span = 60 - PAUSE, at = clock % 60;   /* (the walk fills the minute: a stroll on a short way, a stride on a long one) */ let s = Math.min(1, at / span), x, y, moving = at < span;
        const f = s * (p.length - 1), j = Math.min(p.length - 2, Math.floor(f)), r = f - j; x = p[j][0] + (p[j + 1][0] - p[j][0]) * r; y = p[j][1] + (p[j + 1][1] - p[j][1]) * r;
        if (Math.abs(x - fl.pos[0]) + Math.abs(y - fl.pos[1]) > 14 || (Math.round(x) === fl.pos[0] && Math.round(y) === fl.pos[1])) continue;
        const cx = Math.floor(x + 0.5), cz = Math.floor(y + 0.5), side = ((i % 3) - 1) * 0.22;
        out.push({ x: cx, y: cz, dx: x + 0.5 - cx - 0.5 + side * 0.5, dz: y + 0.5 - cz - 0.5 + side * 0.5, layer: look, w: 0.62, h: 0.78, lift: moving && !CM.reducedMotion ? Math.abs(Math.sin(t * 7 + i)) * 0.02 : 0, mirror: (p[j + 1][0] - p[j][0]) < 0 });
        if (CM.renderer.index.shadow !== undefined) out.push({ x: cx, y: cz, dx: x - cx + side * 0.5, dz: y - cz + side * 0.5, layer: "shadow", flat: true, w: 0.42, alpha: 0.7 }); void PAUSE; }
      return out; }; }
}
