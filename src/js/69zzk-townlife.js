"use strict";
// The living town (v61.0, UPGRADE_PLAN_56.md): small life about Caer Duin, by the rules so the tests can hold it -
// hens in the yards behind the houses, a cat that keeps a perch and changes it by the hour, pigeons roosting on the
// ring wall's walk and the roof ridges, and washing hung out behind the houses on a line to a post. The window's side
// draws the creatures (76zzzzzzzzzz9-townlife.js) and the mesh builds the washing (26k-washing.js). Nothing here is
// in the way or part of the rules of play.
//   CM.yardOf(fl, rect) -> [[x, y]]             the open grass squares about a house, not a street
//   CM.chickensOf(fl) -> [{ home, squares, n }]  up to three flocks, in yards with room
//   CM.chickenPose(flock, i, t) -> { x, y, moving, peck, mirror }   where hen i is at t seconds, deterministic
//   CM.chickensOut(game) -> bool                 by day, not in rain or snow
//   CM.catPerches(fl) -> [{ x, y, h, where }]    fence and hedge tops and the well's kerb
//   CM.catNow(game, fl) -> { x, y, h, where, night }   its perch this two-hour slot; by the tavern's door at night and in the wet
//   CM.roostsOf(fl) -> [{ x, z, y, where }]      where the pigeons sit: the wall's walk, the roof ridges
//   CM.washingLines(fl, season) -> [{ x0, z0, x1, z1, y, home, cloths: [{ t, w, h, k }] }]   none in winter
{ const open = (fl, x, y) => CM.inBounds(fl, x, y) && fl.grid[y][x] === 0, grassy = (fl, x, y) => { const g = CM.groundAt(fl, x, y); return g === null || g === "grass"; };
  const inRect = (r, x, y) => x >= r[0] && y >= r[1] && x <= r[2] && y <= r[3];
  const street = (x, y) => Object.values(CM.TOWN_STREETS || {}).some((rs) => rs.some((r) => inRect(r, x, y))) || Boolean(CM.TOWN_SQUARE && inRect(CM.TOWN_SQUARE, x, y)) || Boolean(CM.TOWN_YARD && inRect(CM.TOWN_YARD, x, y));
  const yardSquare = (fl, x, y) => open(fl, x, y) && grassy(fl, x, y) && !street(x, y) && !(fl.things && fl.things[`${x},${y}`]);
  CM.yardOf = (fl, rect) => { const out = []; for (let y = rect[1] - 2; y <= rect[3] + 2; y++) for (let x = rect[0] - 2; x <= rect[2] + 2; x++) { if (inRect(rect, x, y) || !yardSquare(fl, x, y)) continue; out.push([x, y]); } return out; };
  CM.chickensOf = (fl) => { if (!fl || fl.number !== 0) return []; const out = [];
    (CM.TOWN_HOUSES || []).forEach((rect, i) => { const yard = CM.yardOf(fl, rect); if (yard.length < 3) return; const h = CM.hashSeed(`chickens:${i}`); if (h % 3 === 0) return;
      const cx = (rect[0] + rect[2]) / 2, cy = (rect[1] + rect[3]) / 2; yard.sort((a, b) => Math.abs(a[0] - cx) + Math.abs(a[1] - cy) - Math.abs(b[0] - cx) - Math.abs(b[1] - cy));
      out.push({ home: i, squares: yard.slice(0, 8), n: 3 + ((h >>> 4) % 3) }); });
    return out.slice(0, 3); };
  // a hen's walk: a step a leg to a neighbouring yard square (or a stand), the legs remembered on the flock so the walk joins up
  const legOf = (flock, i, k) => { const W = flock.walks || (flock.walks = {}), w = W[i] || (W[i] = [flock.squares[CM.hashSeed(`hen0:${flock.home}:${i}`) % flock.squares.length]]);
    while (w.length <= k) { const a = w[w.length - 1], nb = flock.squares.filter(([x, y]) => Math.max(Math.abs(x - a[0]), Math.abs(y - a[1])) === 1), hs = CM.hashSeed(`hen:${flock.home}:${i}:${w.length}`); w.push(hs % 3 === 0 || !nb.length ? a : nb[hs % nb.length]); }
    return w[k]; };
  CM.chickenPose = (flock, i, t) => { const T = 7, u = (t + i * 2.3) / T, k = Math.floor(u), r = u - k, a = legOf(flock, i, k), b = legOf(flock, i, k + 1);
    const walk = Math.min(1, r / 0.45), moving = r < 0.45 && (a[0] !== b[0] || a[1] !== b[1]), j = CM.hashSeed(`hj:${flock.home}:${i}`);
    return { x: a[0] + (b[0] - a[0]) * walk + 0.5 + ((j % 7) - 3) * 0.06, y: a[1] + (b[1] - a[1]) * walk + 0.5 + (((j >>> 3) % 7) - 3) * 0.06, moving, peck: !moving && Math.sin((t + i) * 5.5) > 0.3, mirror: b[0] < a[0] }; };
  CM.chickensOut = (game) => { if (!game || !game.floor || game.floor.number !== 0) return false; const h = CM.hourOf(game), [dawn, dusk] = CM.daylightOf(game), w = CM.weather ? CM.weather(game) : "clear"; return h >= dawn && h < dusk && w !== "rain" && w !== "snow"; };
  CM.catPerches = (fl) => { if (!fl || fl.number !== 0) return []; const out = [];
    for (const r of CM.TOWN_FENCES || []) for (let y = r[1]; y <= r[3]; y++) for (let x = r[0]; x <= r[2]; x++) out.push({ x, y, h: 0.52, where: "fence" });
    for (const r of CM.TOWN_HEDGES || []) for (let y = r[1]; y <= r[3]; y++) for (let x = r[0]; x <= r[2]; x++) if ((x + y) % 2 === 0) out.push({ x, y, h: 0.7, where: "hedge" });
    if (CM.TOWN_AT && CM.TOWN_AT.well) out.push({ x: CM.TOWN_AT.well[0], y: CM.TOWN_AT.well[1], h: 0.22, where: "well", dx: 0.42, dz: 0.1 });
    return out; };
  CM.catNow = (game, fl) => { if (!game || !fl || fl.number !== 0) return null; const P = CM.catPerches(fl); if (!P.length) return null;
    const h = CM.hourOf(game), [dawn, dusk] = CM.daylightOf(game), w = CM.weather ? CM.weather(game) : "clear", night = h >= dusk || h < dawn, wet = w === "rain" || w === "snow", T = CM.TOWN_AT && CM.TOWN_AT.tavern;
    if ((night || wet) && T) return { x: T[0] - 1, y: T[1] + 1, h: 0, where: "the tavern's door", night, dx: 0.3, dz: -0.3 };   // (sheltered by the door, in the lamp's light)
    const slot = CM.dayOf(game) * 12 + Math.floor(h / 2), p = P[CM.hashSeed(`${game.seed}:cat:${slot}`) % P.length]; return Object.assign({ night: false }, p); };
  CM.roostsOf = (fl) => { if (!fl || fl.number !== 0) return []; const out = [], H = (CM.SOLID.townwall && CM.SOLID.townwall.h) || 1.3;
    for (const [k, kind] of Object.entries(fl.kinds || {})) { if (kind !== "townwall") continue; const [x, y] = k.split(",").map(Number); const hs = CM.hashSeed(`roost:${x},${y}`); if (hs % 6 !== 0) continue; out.push({ x: x + 0.25 + ((hs >>> 3) % 5) * 0.12, z: y + 0.25 + ((hs >>> 6) % 5) * 0.12, y: H + 0.07, where: "wall" }); }
    if (CM.buildingsOf) for (const B of CM.buildingsOf(fl)) { const hs = CM.hashSeed(`ridge:${B.x0},${B.y0}`); if (hs % 2) continue; out.push({ x: (B.x0 + B.x1 + 1) / 2 + (((hs >>> 2) % 3) - 1) * 0.4, z: (B.y0 + B.y1 + 1) / 2 + (((hs >>> 5) % 3) - 1) * 0.3, y: B.h + B.rise + 0.03, where: "ridge" }); }
    return out; };
  CM.washingLines = (fl, season) => { if (!fl || fl.number !== 0 || season === "winter") return []; const out = [];
    (CM.TOWN_HOUSES || []).forEach((rect, i) => { const hs = CM.hashSeed(`washing:${i}`); if (hs % 2) return;
      const mx = Math.floor((rect[0] + rect[2]) / 2), my = Math.floor((rect[1] + rect[3]) / 2);
      const sides = [[mx, rect[3] + 1, 0, 1], [mx, rect[1] - 1, 0, -1], [rect[2] + 1, my, 1, 0], [rect[0] - 1, my, -1, 0]];   // the square outside the wall's middle, and the way out from it
      for (const [sx, sy, dx, dy] of sides) { if (!yardSquare(fl, sx, sy) || !yardSquare(fl, sx + dx, sy + dy)) continue;
        const x0 = sx + 0.5 - dx * 0.5, z0 = sy + 0.5 - dy * 0.5, x1 = sx + 0.5 + dx * 1.3, z1 = sy + 0.5 + dy * 1.3, n = 3 + ((hs >>> 3) % 2), cloths = [];
        for (let c = 0; c < n; c++) cloths.push({ t: (c + 1) / (n + 1), w: 0.22 + ((hs >>> (4 + c)) % 3) * 0.05, h: 0.28 + ((hs >>> (7 + c)) % 3) * 0.07, k: 0.75 + ((hs >>> (10 + c)) % 4) * 0.12 });
        out.push({ x0, z0, x1, z1, y: 1.22, home: i, cloths }); break; } });
    return out; };
}
