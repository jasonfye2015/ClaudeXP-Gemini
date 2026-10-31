"use strict";
// What a frame costs in three scenes the tenth update made heavy: the land by day at High, a dungeon room with its
// torches, and a fight with fireballs going off. The page runs CM.perfScenes(); each scene holds the step-down still,
// waits for the floor to settle, then counts frames. Used by tests/smoke.js (Chromium) and by hand in a real window.
//   in the page: await CM.perfScenes({ ms: 2000, detail: "high" })
(function () {
  const wait = (ms) => new Promise((r) => setTimeout(r, ms));
  CM.perfScenes = async function ({ ms = 2000, detail = "high", settle = 800 } = {}) {
    const g = CM.game, out = {};
    g.settings.detail = detail; g.emit("settings", g.settings);
    CM.perf.hold = true;
    const measure = async (name, setup) => {
      setup(); g.look(); g.emit("floor", g.floor); g.emit("change");
      await wait(settle); CM.perf.reset(); await wait(ms);
      out[name] = Object.assign(CM.perf.read(), { lights: (CM.renderer.lights || []).length, air: CM.air ? CM.air.parts.length : 0 });
    };
    const keep = g.startCombat; g.startCombat = function () {};           // (no fight unless the scene starts one)
    try {
      await measure("land", () => { g.clock = 6 * 60; g.enterFloor(-1, "rope", [50, 30]); g.floor.facing = 3; });
      await measure("torches", () => { g.enterFloor(3, "down"); const fl = g.floor, r = (fl.rooms || []).slice().sort((a, b) => (b.x1 - b.x0) * (b.y1 - b.y0) - (a.x1 - a.x0) * (a.y1 - a.y0))[0];
        if (r) { fl.pos = [Math.round((r.x0 + r.x1) / 2), r.y1]; fl.facing = 0; } });
      g.startCombat = keep;
      let boom = null;
      await measure("fight", () => { const fl = g.floor, [x, y] = fl.pos, k = `${x},${y - 1}`, rnd = new CM.Random(7);
        const group = CM.monsterGroup(fl.number, rnd, g.gen).map((m) => g.tune(m)); g.foes = group; g.startCombat(k, { group }, true);
        boom = setInterval(() => g.emit("fx", { kind: "fireball" }), 700); });
      clearInterval(boom);
      if (g.mode === "combat") { g.mode = "explore"; g.combat = null; g.foes = []; }
      if (g.floorAt && CM.TOWER_STAIRS) await measure("tower", () => { g.clock = 16 * 60; g.enterFloor(0, "rope", Object.keys(CM.TOWER_STAIRS)[0].split(",").map(Number)); g.floor.facing = 1; g.perch = null; g.climbTower(Object.keys(CM.TOWER_STAIRS)[0]); });
    } finally { g.startCombat = keep; CM.perf.hold = false; }
    return out;
  };
})();
