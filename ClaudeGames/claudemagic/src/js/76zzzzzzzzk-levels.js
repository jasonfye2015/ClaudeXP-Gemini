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
  // (v47.3) the galleries' railings: stone balusters along the edge where the floor steps down, open at the middle of each side
  { const b0 = CM.art.build; CM.art.build = function (theme, look) { const set = b0.call(this, theme, look); const c = document.createElement("canvas"); c.width = c.height = 128; const p = c.getContext("2d");
      p.fillStyle = "#6E6455"; p.fillRect(0, 8, 128, 16); p.fillRect(0, 110, 128, 18); p.fillStyle = "#8A7E6A"; p.fillRect(0, 8, 128, 4);
      for (let i = 0; i < 4; i++) { const x = 8 + i * 32; p.fillStyle = "#62584A"; p.beginPath(); p.moveTo(x + 4, 24); p.quadraticCurveTo(x - 4, 66, x + 4, 110); p.lineTo(x + 16, 110); p.quadraticCurveTo(x + 24, 66, x + 16, 24); p.closePath(); p.fill(); }
      set.index["lv:rail"] = set.layers.length; set.layers.push(c); return set; }; }
  const rails = new WeakMap(), railsOf = (F) => { let R = rails.get(F); if (R) return R; R = [];
    for (const G of F.galleries || []) { const mx = Math.floor((G.x0 + G.x1) / 2), my = Math.floor((G.y0 + G.y1) / 2);
      for (let y = G.y0; y <= G.y1; y++) for (let x = G.x0; x <= G.x1; x++) { if (F.grid[y][x] !== 0 || Math.min(x - G.x0, G.x1 - x, y - G.y0, G.y1 - y) !== 0) continue;
        CM.DIRS.forEach(([dx, dy], d) => { const nx = x + dx, ny = y + dy; if (nx <= G.x0 || nx >= G.x1 || ny <= G.y0 || ny >= G.y1 || F.grid[ny][nx] !== 0) return; if ((dx === 0 && Math.abs(x - mx) <= 0) || (dy === 0 && Math.abs(y - my) <= 0)) return; R.push({ x, y, d }); }); } }
    rails.set(F, R); return R; };
  { const ls0 = CM.lifeSprites; CM.lifeSprites = (game, F, now) => { const out = ls0 ? ls0(game, F, now) : []; if (!F || !F.galleries || !CM.renderer || CM.renderer.index["lv:rail"] === undefined) return out;
      for (const r of railsOf(F)) if (Math.abs(r.x - F.pos[0]) + Math.abs(r.y - F.pos[1]) <= 12) { const base = CM.floorAt(F, r.x, r.y), [dx, dy] = CM.DIRS[r.d];
        out.push({ x: r.x, y: r.y, layer: "lv:rail", face: r.d, w: 1, h: 0.32, lift: -0.34, base, glow: 0.3 });
        out.push({ x: r.x + dx, y: r.y + dy, layer: "lv:rail", face: (r.d + 2) % 4, w: 1, h: 0.32, lift: -0.34, base, glow: 0.3 }); }   /* (both faces: a decal is seen from its own square only) */
      return out; }; }
  // the map: a dais lighter, a pit darker
  const da0 = CM.UI.prototype.drawAutomap; CM.UI.prototype.drawAutomap = function (canvas, ...a) { const out = da0.call(this, canvas, ...a), g = this.game, F = g.towerRun ? null : g.floor; if (!F || !F.levels) return out;
    const p = canvas.getContext("2d"), cell = canvas.width / F.grid.length, seen = new Set(F.seen.map(([x, y]) => `${x},${y}`));
    for (const [k, [f]] of Object.entries(F.levels)) { if (!seen.has(k) || !f) continue; const [x, y] = k.split(",").map(Number); p.fillStyle = f > 0 ? "rgba(255,255,255,0.28)" : "rgba(60,40,20,0.22)"; p.fillRect(x * cell, y * cell, cell, cell); }
    return out; };
}
