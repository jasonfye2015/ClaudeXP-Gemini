"use strict";
// The Mage Tower, measured: a simple hand climbs it - faces the nearest monster it can see and shoots, casts the great
// spell at a boss or a crowd, walks to a draught when hurt, otherwise walks to the nearest monster left, then the
// ladder - floor after floor, resting to full between floors (as a player would, going out to rest), until the hero
// falls or reaches the top. The report: floors cleared by calling and level.
//
//   node tools/towerbot.js                 Mage, Cleric and an archer at levels 5 to 40
//   node tools/towerbot.js --seeds 6 --classes Mage --levels 10,20,30
const { load, fixedParty } = require("./headless");

function climb(CM, cls, level, seed, maxFloor = 40) {
  const g = new CM.Game();
  g.newGame(seed, fixedParty(CM), "pauper", "fair", [], "dungeon", { town: true });
  g.enterFloor(-1, "rope", CM.MAGE_DOOR.slice()); g.mode = "explore";
  const i = 3, h = g.party[i];
  if (cls !== "Mage") { h.cls = cls === "archer" ? "Ranger" : cls; if (cls === "archer") h.weapon = { name: "Long Bow", base: "Long Bow", kind: "weapon", slot: "weapon", power: 3 + Math.floor(level / 3), props: { bow: true, twohanded: true } }; }
  h.xp = CM.xpForLevel(level); g.checkLevels(); CM.recompute(h); h.hp = h.max; h.mp = h.maxmp;
  let cleared = 0, seconds = 0, why = "top";
  for (let n = 1; n <= maxFloor; n++) {
    g.tower = { cleared: n - 1, best: n - 1 }; h.hp = h.max; h.mp = h.maxmp;
    if (g.enterMageTower(i)) break;
    const r = g.towerRun, dt = 1 / 30;
    let t = 0, ok = false, goal = null, goalAt = -9;
    while (t < 600) {
      t += dt;
      const seen = r.living().filter((o) => (o.seen || Math.hypot(o.x - r.x, o.z - r.z) < 9) && r.clear(r.x, r.z, o.x, o.z)).sort((a, b) => Math.hypot(a.x - r.x, a.z - r.z) - Math.hypot(b.x - r.x, b.z - r.z));
      const inp = {};
      if (seen.length) {
        const o = seen[0], d = Math.hypot(o.x - r.x, o.z - r.z);
        r.yaw = Math.atan2(o.x - r.x, -(o.z - r.z)); inp.fire = true;
        if ((o.boss || seen.length >= 3) && (r.arms.arrows ? r.arrows > 6 : h.mp >= r.arms.cost)) inp.spell = true;
        if (d < 1.6) inp.back = true;                                   // (keep a little room)
      } else {
        const hurt = h.hp < h.max * 0.4, draught = hurt && r.items.find((it) => !it.taken && it.kind === "draught");
        if (!goal || t - goalAt > 2 || (goal.mon && goal.mon.m.hp <= 0)) {   // (the nearest by the walk, not as the crow flies; looked at again every two seconds)
          goalAt = t; const g0 = r.fl.grid, d = CM.distances(g0, [Math.floor(r.x), Math.floor(r.z)], (x, z) => g0[z] && g0[z][x] === 0), walk = (x, z) => { const v = d.get(`${Math.floor(x)},${Math.floor(z)}`); return v === undefined ? 1e9 : v; };
          const mon = r.living().sort((a, b) => walk(a.x, a.z) - walk(b.x, b.z))[0];
          goal = draught ? { x: draught.x + 0.5, z: draught.y + 0.5 } : mon ? { x: mon.x, z: mon.z, mon } : r.fl.ladder ? { x: r.fl.ladder[0] + 0.5, z: r.fl.ladder[1] + 0.5 } : null;
        }
        if (goal && goal.mon) { goal.x = goal.mon.x; goal.z = goal.mon.z; }
        const target = goal ? [goal.x, goal.z] : null;
        if (target) { const y = r.toward(r.x, r.z, target[0], target[1]); if (y !== null) { r.yaw = y; inp.fwd = true; } }
      }
      r.update(dt, inp); r.events.length = 0;
      if (r.over) break;
      if (r.atLadder()) { g.towerClimb(true); ok = true; break; }
    }
    seconds += t;
    if (!ok) { why = r.over ? "fell" : "stuck"; if (g.towerRun) g.leaveMageTower(r.over ? "fell" : "left"); break; }
    cleared = n;
  }
  return { cleared, seconds: Math.round(seconds), why };
}

if (require.main === module) {
  const args = process.argv.slice(2), opt = (k, d) => { const i = args.indexOf("--" + k); return i >= 0 ? args[i + 1] : d; };
  const SEEDS = Number(opt("seeds", 4)), CLASSES = opt("classes", "Mage,Cleric,archer").split(","), LEVELS = opt("levels", "5,10,15,20,25,30,35,40").split(",").map(Number);
  const CM = load();
  console.log(`The Mage Tower, measured: ${SEEDS} seeds; floors cleared in a row (median), resting between floors`);
  for (const cls of CLASSES) {
    let stuck = 0;
    const row = LEVELS.map((L) => { const got = []; for (let s = 0; s < SEEDS; s++) { const c = climb(CM, cls, L, `tower-sim-${s + 1}`); got.push(c.cleared); if (c.why === "stuck") stuck++; } got.sort((a, b) => a - b); return `L${L}: ${got[Math.floor(got.length / 2)]}`; });
    console.log(`${cls.padEnd(8)} ${row.join("  ")}${stuck ? `   (the hand got stuck ${stuck} times)` : ""}`);
  }
}
module.exports = { climb };
