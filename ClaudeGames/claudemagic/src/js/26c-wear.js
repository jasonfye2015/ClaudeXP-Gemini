"use strict";
// Wear by traffic (v54.1, UPGRADE_PLAN_49.md): how trodden each open square of the town and the land is - most on the
// ways between the doors that people walk (the shortest way from each to the next), at the doors themselves, and round
// the well and the market, the wear spreading a little to the squares beside - for the grass to be worn to earth there
// in patches (40-render.js, from the map's alpha). By the floor's own layout, so the same every time.
//   CM.wearOf(fl) -> Map("x,y" -> 0..1)
{ const cache = new WeakMap();
  const bfs = (fl, a, b) => { const N = fl.grid.length, open = (x, y) => fl.grid[y] && fl.grid[y][x] === 0, prev = new Map([[`${a[0]},${a[1]}`, null]]), q = [a];
    while (q.length) { const [x, y] = q.shift(); if (x === b[0] && y === b[1]) break; for (const [dx, dy] of CM.DIRS) { const nx = x + dx, ny = y + dy, k = `${nx},${ny}`; if (nx < 0 || ny < 0 || nx >= N || ny >= N || prev.has(k) || !open(nx, ny)) continue; prev.set(k, [x, y]); q.push([nx, ny]); } }
    const out = []; let c = `${b[0]},${b[1]}`; if (!prev.has(c)) return []; while (c) { out.push(c); const p = prev.get(c); c = p ? `${p[0]},${p[1]}` : null; } return out; };
  CM.wearOf = (fl) => { let W = cache.get(fl); if (W) return W; W = new Map(); const add = (k, v) => W.set(k, Math.min(1, (W.get(k) || 0) + v)); const open = (x, y) => fl.grid[y] && fl.grid[y][x] === 0;
    const spots = []; if (fl.number === 0 && CM.TOWN_AT) { for (const at of Object.values(CM.TOWN_AT)) { if (!Array.isArray(at)) continue; if (open(at[0], at[1])) spots.push(at); else for (const [dx, dy] of CM.DIRS) if (open(at[0] + dx, at[1] + dy)) { spots.push([at[0] + dx, at[1] + dy]); break; } } }
    else if (fl.number === -1) { for (const [k, t] of Object.entries(fl.things || {})) if (["woodgate", "cave", "hut", "farm", "signpost", "caveexit"].includes(t.type)) spots.push(k.split(",").map(Number)); if (CM.WOOD_GATE) spots.push(CM.WOOD_GATE.slice()); }
    for (const s of spots) { add(`${s[0]},${s[1]}`, 0.9); for (const [dx, dy] of CM.DIRS) if (open(s[0] + dx, s[1] + dy)) add(`${s[0] + dx},${s[1] + dy}`, 0.35); }
    for (let i = 0; i < spots.length; i++) { const p = bfs(fl, spots[i], spots[(i + 1) % spots.length]); for (const k of p) { add(k, 0.3); const [x, y] = k.split(",").map(Number); for (const [dx, dy] of CM.DIRS) if (open(x + dx, y + dy)) add(`${x + dx},${y + dy}`, 0.08); } }
    cache.set(fl, W); return W; };
}
