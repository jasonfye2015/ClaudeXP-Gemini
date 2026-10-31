"use strict";
// The Fortress, measured: a simple hand goes down it - strikes whatever is in reach (facing it), breaks a lair it
// passes, throws a flask into a crowd, drinks a draught when hurt, and otherwise walks the shortest way to the stairs;
// if the stairs are behind a door, to the nearest key first, then to the door. Floor after floor, mended between
// floors (as a player would, going out at the stairs), until the fighter falls or the Marshal does.
// The report: floors cleared by calling and level.
//
//   node tools/fortbot.js                      Knight and Rogue at levels 1 to 20
//   node tools/fortbot.js --seeds 4 --classes Knight --levels 5,10
const { load, fixedParty } = require("./headless");

function goDown(CM, cls, level, seed, maxFloor = CM.FORT_FLOORS) {
  const g = new CM.Game();
  g.newGame(seed, fixedParty(CM), "pauper", "fair", [], "dungeon", { town: true });
  g.enterFloor(-1, "rope", CM.FORTRESS.front.slice()); g.mode = "explore";
  const i = 0, h = g.party[i]; h.cls = cls;
  h.xp = CM.xpForLevel(level); g.checkLevels(); CM.recompute(h); h.hp = h.max;
  let cleared = 0, why = "the end";
  for (let n = 1; n <= maxFloor; n++) {
    g.fort = { cleared: n - 1, best: n - 1 }; h.hp = h.max;
    if (g.enterFortress(i)) { why = "refused"; break; }
    const r = g.fortRun, t0 = r.t; let ok = false;
    while (r.t - t0 < 900) {
      const inp = {}, near = r.living().filter((o) => Math.hypot(o.x - r.x, o.y - r.y) < CM.FT.reach + 0.3).sort((a, b) => Math.hypot(a.x - r.x, a.y - r.y) - Math.hypot(b.x - r.x, b.y - r.y));
      const lair = r.lairs.find((L) => L.hp > 0 && Math.hypot(L.x - r.x, L.y - r.y) < CM.FT.reach + 0.2);
      if (near.length) { inp.aim = Math.atan2(near[0].y - r.y, near[0].x - r.x); inp.attack = true; if (r.flasks && r.living().filter((o) => Math.hypot(o.x - r.x, o.y - r.y) < 4).length >= 5) inp.bomb = true; }
      else if (lair) { inp.aim = Math.atan2(lair.y - r.y, lair.x - r.x); inp.attack = true; }
      else {
        const G = r.grid, S = r.fl.size, hx = Math.floor(r.x), hy = Math.floor(r.y);
        const prev = new Map([[`${hx},${hy}`, null]]), q = [[hx, hy]];
        for (let k = 0; k < q.length; k++) { const [x, y] = q[k]; for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) { const nx = x + dx, ny = y + dy, key = `${nx},${ny}`; if (nx < 0 || ny < 0 || nx >= S || ny >= S || prev.has(key) || G[ny][nx] === 1) continue; prev.set(key, `${x},${y}`); if (G[ny][nx] === 0) q.push([nx, ny]); } }
        const can = (x, y) => prev.has(`${x},${y}`), [sx, sy] = r.fl.stairs, hurt = h.hp < h.max * 0.45;
        const draught = hurt && r.items.filter((it) => !it.taken && it.kind === "draught" && can(it.x, it.y))[0];
        let goal = null;
        if (r.atStairs()) { ok = true; break; }
        if (draught) goal = [draught.x, draught.y];
        else if (can(sx, sy) && r.stairsOpen()) goal = [sx, sy];
        else if (can(sx, sy)) { const m = r.marshal; goal = [Math.floor(m.x), Math.floor(m.y)]; }
        else { const key = r.items.find((it) => !it.taken && it.kind === "key" && can(it.x, it.y)); if (key && !r.keys) goal = [key.x, key.y]; else { let best = null; for (const k of prev.keys()) { const [x, y] = k.split(",").map(Number); if (G[y][x] === 2) { best = [x, y]; break; } } if (best && r.keys) goal = [best[0], best[1]]; else if (key) goal = [key.x, key.y]; } }
        if (!goal) { why = "lost"; break; }
        let cur = `${goal[0]},${goal[1]}`, step = null; while (prev.get(cur) && prev.get(cur) !== `${hx},${hy}`) cur = prev.get(cur); step = cur.split(",").map(Number);
        const tx = step[0] + 0.5 - r.x, ty = step[1] + 0.5 - r.y;
        if (tx > 0.08) inp.right = true; if (tx < -0.08) inp.left = true; if (ty > 0.08) inp.down = true; if (ty < -0.08) inp.up = true;
        inp.aim = null;
      }
      r.update(1 / 30, inp);
      if (r.over) break;
    }
    if (r.over) { why = `fell on floor ${n}`; g.leaveFortress("dead"); break; }
    if (!ok) { why = why === "lost" ? `lost on floor ${n}` : `too slow on floor ${n}`; g.leaveFortress("fled"); break; }
    cleared = n; g.fortStairs(true);
  }
  return { cleared, why, gold: g.gold };
}

if (require.main === module) {
  const arg = (k, d) => { const i = process.argv.indexOf(k); return i >= 0 ? process.argv[i + 1] : d; };
  const CM = load(), seeds = Number(arg("--seeds", 3)), classes = arg("--classes", "Knight,Rogue").split(","), levels = arg("--levels", "1,5,10,15,20").split(",").map(Number);
  for (const cls of classes) for (const L of levels) {
    const runs = []; for (let s = 0; s < seeds; s++) runs.push(goDown(CM, cls, L, `fortbot-${s}`));
    console.log(`${cls.padEnd(8)} L${String(L).padEnd(3)} floors ${runs.map((r) => r.cleared).join(", ").padEnd(14)} ${runs.map((r) => r.why).join("; ")}`);
  }
}
module.exports = { goDown };
