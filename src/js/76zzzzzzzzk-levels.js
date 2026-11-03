"use strict";
// Levels, seen (v47.0, UPGRADE_PLAN_42.md; the levels are 69zzi-levels.js's, the stone of them 26-surface.js's): what
// stands on a dais stands on it and what is in a pit is down in it (every sprite's base is its square's floor); the eye
// climbs a dais's step and goes down into a pit as the party walks, smoothly over the step; and the map marks them - a
// dais lighter, a pit darker.
{ const fl = () => (CM.game && CM.game.mode !== "title" ? CM.game.floor : null);
  const prep = (r) => {
    const ss0 = r.setSprites; r.setSprites = function (list) { const F = fl(); if (F && F.levels && list) for (const s of list) { if (s.base === undefined && typeof s.x === "number" && typeof s.y === "number") { const L = F.levels[`${Math.floor(s.x + 0.5 + (s.dx || 0))},${Math.floor(s.y + 0.5 + (s.dz || 0))}`] || F.levels[`${s.x},${s.y}`]; if (L) s.base = L[0]; } } return ss0.call(this, list); };
    const adv0 = r._advance; r._advance = function (dt) { const out = adv0.call(this, dt), F = fl(); if (!F || !F.levels || this.perch) return out; const at = (x, z) => CM.floorAt(F, Math.floor(x), Math.floor(z));
      let h; if (this.move) { const k = CM.ease(this.move.t), a = at(this.move.from[0], this.move.from[2]), b = at(this.move.to[0], this.move.to[2]); h = a + (b - a) * CM.clamp((k - 0.25) / 0.5, 0, 1); } else h = at(this.eye[0], this.eye[2]);
      this.eye = [this.eye[0], 0.5 + h, this.eye[2]]; return out; };
    r.levelsWrapped = true; };
  const t = typeof self !== "undefined" && self.CM_WORKER ? null : setInterval(() => { if (CM.renderer && !CM.renderer.levelsWrapped) { prep(CM.renderer); clearInterval(t); } }, 100);
  // the map: a dais lighter, a pit darker
  const da0 = CM.UI.prototype.drawAutomap; CM.UI.prototype.drawAutomap = function (canvas, ...a) { const out = da0.call(this, canvas, ...a), g = this.game, F = g.towerRun ? null : g.floor; if (!F || !F.levels) return out;
    const p = canvas.getContext("2d"), cell = canvas.width / F.grid.length, seen = new Set(F.seen.map(([x, y]) => `${x},${y}`));
    for (const [k, [f]] of Object.entries(F.levels)) { if (!seen.has(k) || !f) continue; const [x, y] = k.split(",").map(Number); p.fillStyle = f > 0 ? "rgba(255,255,255,0.28)" : "rgba(60,40,20,0.22)"; p.fillRect(x * cell, y * cell, cell, cell); }
    return out; };
}
