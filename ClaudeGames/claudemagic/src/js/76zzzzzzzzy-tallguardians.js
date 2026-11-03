"use strict";
// The great ones, tall (v50.3, UPGRADE_PLAN_45.md): a guardian or the Lich King stands as tall as the room lets it -
// its head near the ceiling (in a tall hall, taller still: 69zzi-levels.js), broader with it - so it looms over the party
// where before it stood little higher than an orc. Their picture only: their place in the fight is as it was.
{ const big = () => { const s = new Set(Object.values(CM.GUARDIANS || {}).map((G) => G.name)); if (CM.BOSS) s.add(CM.BOSS.name); return s; };
  let names = null;
  const prep = (r) => { const ss0 = r.setSprites; r.setSprites = function (list) { const g = CM.game, fl = g && g.floor; if (fl && g.mode !== "title") { names = names || big();
        for (const s of list) { if (typeof s.layer !== "string" || !s.layer.startsWith("monster:") || s.flat) continue; const name = s.layer.split(":")[1]; if (!names.has(name) || !(s.h > 0)) continue;
          const x = Math.floor(s.x + 0.5 + (s.dx || 0)), y = Math.floor(s.y + 0.5 + (s.dz || 0)), room = (CM.ceilAt ? CM.ceilAt(fl, x, y) - CM.floorAt(fl, x, y) : 1), want = Math.min(room * 0.94, 1.55), k = Math.max(1, want / s.h);
          s.h *= k; s.w = (s.w || 0.7) * Math.min(k, 1.35); } }
      return ss0.call(this, list); }; r.tallWrapped = true; };
  const t = typeof self !== "undefined" && self.CM_WORKER ? null : setInterval(() => { if (CM.renderer && !CM.renderer.tallWrapped) { prep(CM.renderer); clearInterval(t); } }, 150);
}
