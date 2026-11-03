"use strict";
// Levels (v47.0, UPGRADE_PLAN_42.md): a dungeon square has a floor level and a ceiling height of its own - one of each, no
// room over another. Made with the floor (never saved: CM.FLOOR_FIXED) by a hash of the floor and the room, so nothing
// moves: about one plain room in five has a raised dais in its middle, and about one in nine a sunken pit, the room's
// edge left at the corridors' level so every way in meets it. A band's landmark room stands its centrepiece on a dais.
// The moves, the map and the rules are the grid's as before; the levels are drawn (26-surface.js floorMesh, the sprites'
// base, the eye: 76zzzzzzzzk-levels.js).
//   floor.levels = { "x,y": [floor, ceiling] } for the squares not at [0, 1]; CM.levelOf, CM.floorAt, CM.ceilAt
//   (v47.1) floor.raised = the raised room on about half the floors, its corridors climbing to it a step a square
{ if (!CM.FLOOR_FIXED.includes("levels")) CM.FLOOR_FIXED.push("levels");
  CM.LEVELS = { dais: 0.3, pit: -0.3, daisEvery: 5, pitEvery: 9, raised: 0.6, step: 0.15, raisedEvery: 2 };
  CM.levelOf = (fl, x, y) => (fl && fl.levels && fl.levels[`${x},${y}`]) || null;
  CM.floorAt = (fl, x, y) => { const L = CM.levelOf(fl, x, y); return L ? L[0] : 0; };
  CM.ceilAt = (fl, x, y) => { const L = CM.levelOf(fl, x, y); return L ? L[1] : 1; };
  const room = (fl, r, f, c) => { for (let y = r.y0 + 1; y <= r.y1 - 1; y++) for (let x = r.x0 + 1; x <= r.x1 - 1; x++) if (fl.grid[y][x] === 0) { fl.levels = fl.levels || {}; fl.levels[`${x},${y}`] = [f, c]; } };
  CM.makeLevels = (fl) => { if (!fl || !(fl.number >= 1) || fl.number % 1 !== 0 || (fl.special && !["dark", "wading"].includes(fl.special)) || !fl.rooms) return fl;
    for (const r of fl.rooms) { if (r.name || r.template) continue; const W = r.x1 - r.x0 + 1, H = r.y1 - r.y0 + 1; if (W < 4 || H < 4) continue;
      const M = fl.landmark, isMark = M && M.x0 === r.x0 && M.y0 === r.y0 && M.x1 === r.x1 && M.y1 === r.y1, v = new CM.Random(CM.hashSeed(`levels:${fl.number}:${r.x0},${r.y0},${r.x1},${r.y1}`)).next();
      if (isMark || v < 1 / CM.LEVELS.daisEvery) room(fl, r, CM.LEVELS.dais, 1); else if (v < 1 / CM.LEVELS.daisEvery + 1 / CM.LEVELS.pitEvery) room(fl, r, CM.LEVELS.pit, 1); }
    // (v47.1) a raised room, now and then: the whole of it up, its ceiling with it, and every corridor to it a flight of steps
    if (new CM.Random(CM.hashSeed(`raised:${fl.number}`)).next() < 1 / CM.LEVELS.raisedEvery) {
      const inRoom = new Map(); for (const r of fl.rooms) for (let y = r.y0; y <= r.y1; y++) for (let x = r.x0; x <= r.x1; x++) inRoom.set(`${x},${y}`, r);
      const R = fl.rooms.filter((r) => !r.name && !r.template && !(fl.landmark && fl.landmark.x0 === r.x0 && fl.landmark.y0 === r.y0) && ![...Array(r.x1 - r.x0 + 1).keys()].some((i) => fl.levels && fl.levels[`${r.x0 + i},${Math.floor((r.y0 + r.y1) / 2)}`]))
        .sort((a, b) => (b.x1 - b.x0) * (b.y1 - b.y0) - (a.x1 - a.x0) * (a.y1 - a.y0))[0];
      if (R) { const H = CM.LEVELS.raised, S = CM.LEVELS.step, set = (x, y, f) => { fl.levels = fl.levels || {}; fl.levels[`${x},${y}`] = [f, 1 + f]; };
        for (let y = R.y0; y <= R.y1; y++) for (let x = R.x0; x <= R.x1; x++) if (fl.grid[y][x] === 0) set(x, y, H);
        const dist = new Map(), q = []; for (let y = R.y0; y <= R.y1; y++) for (let x = R.x0; x <= R.x1; x++) if (fl.grid[y][x] === 0) { dist.set(`${x},${y}`, 0); q.push([x, y]); }
        while (q.length) { const [x, y] = q.shift(), d0 = dist.get(`${x},${y}`); if (H - S * (d0 + 1) <= 0) continue; for (const [dx, dy] of CM.DIRS) { const nx = x + dx, ny = y + dy, k = `${nx},${ny}`; if (dist.has(k) || !fl.grid[ny] || fl.grid[ny][nx] !== 0 || inRoom.has(k)) continue; dist.set(k, d0 + 1); set(nx, ny, H - S * (d0 + 1)); q.push([nx, ny]); } }
        fl.raised = { x0: R.x0, y0: R.y0, x1: R.x1, y1: R.y1 }; } }
    return fl; };
  const mf0 = CM.makeFloor; CM.makeFloor = function (number, seed, gen) { const fl = mf0.call(this, number, seed, gen); if (fl && fl.number === number) CM.makeLevels(fl); return fl; };
}
