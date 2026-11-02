"use strict";
// The dark that moves (v41.4, UPGRADE_PLAN_36.md): where a floor's dark is magical (floor.dark), it is not still - wisps
// of it stand at the edge of the party's light and lean in, creeping a little nearer and drawing back, and pools of it
// spread across the flags toward the torch, so the light's edge is always being eaten at. A spell's light drives it
// back a way; a lantern holds it further off than a torch. Only on the dark squares, and only near the party.
{ const S = 128, cv = () => { const c = document.createElement("canvas"); c.width = c.height = S; return c; };
  const PAINT = {
    "dk:wisp": (p) => { p.fillStyle = "#08060C"; p.beginPath(); p.moveTo(30, 128); p.bezierCurveTo(10, 90, 50, 70, 34, 40); p.bezierCurveTo(26, 20, 52, 6, 60, 0); p.bezierCurveTo(70, 20, 96, 30, 86, 60); p.bezierCurveTo(78, 86, 110, 100, 98, 128); p.closePath(); p.fill(); p.strokeStyle = "#5A2E80"; p.lineWidth = 5; p.stroke();
      p.fillStyle = "#16101E"; p.beginPath(); p.moveTo(48, 128); p.bezierCurveTo(40, 96, 66, 76, 56, 44); p.bezierCurveTo(70, 70, 80, 100, 78, 128); p.closePath(); p.fill(); },
    "dk:pool": (p) => { p.fillStyle = "#06040A"; p.beginPath(); for (let i = 0; i <= 16; i++) { const a = i / 16 * Math.PI * 2, r = 44 + Math.sin(i * 2.7) * 14; const x = 64 + Math.cos(a) * r, y = 64 + Math.sin(a) * r; if (i) p.lineTo(x, y); else p.moveTo(x, y); } p.closePath(); p.fill(); p.strokeStyle = "#3E2058"; p.lineWidth = 6; p.stroke(); },
  };
  { const b0 = CM.art.build; CM.art.build = function (theme, look) { const set = b0.call(this, theme, look); for (const [n, f] of Object.entries(PAINT)) { const c = cv(); f(c.getContext("2d")); set.index[n] = set.layers.length; set.layers.push(c); } return set; }; }
  const darkSets = new WeakMap(), darkOf = (fl) => { let d = darkSets.get(fl); if (!d || d.n !== fl.dark.length) { d = { n: fl.dark.length, set: new Set(fl.dark) }; darkSets.set(fl, d); } return d.set; };
  { const ls0 = CM.lifeSprites; CM.lifeSprites = (game, fl, now) => { const out = ls0 ? ls0(game, fl, now) : []; if (!fl || !(fl.number >= 1) || !fl.dark || !fl.dark.length || game.mode !== "explore" || !CM.renderer || CM.renderer.index["dk:wisp"] === undefined) return out;
      const dark = darkOf(fl), eye = CM.renderer.eye || [fl.pos[0] + 0.5, 0.5, fl.pos[1] + 0.5]; let anyNear = false; for (let dy = -3; dy <= 3 && !anyNear; dy++) for (let dx = -3; dx <= 3; dx++) if (dark.has(`${fl.pos[0] + dx},${fl.pos[1] + dy}`)) { anyNear = true; break; } if (!anyNear) return out;
      const t = now / 1000, still = CM.reducedMotion, spell = game.spellLight > 0, lantern = game.light && game.light.kind === "lantern", owl = game.buffs && game.buffs.owleyes, R0 = owl ? 4.5 : spell ? 3.4 : lantern ? 2.4 : 1.9;
      const open = (x, y) => fl.grid[y] && fl.grid[y][x] === 0;
      for (let i = 0; i < 14; i++) { const a = i / 14 * Math.PI * 2 + (still ? 0 : t * 0.05), lean = still ? 0 : Math.max(0, Math.sin(t * 0.7 + i * 2.3)) * 0.55, r = R0 - lean + (i % 3) * 0.25, wx = eye[0] + Math.cos(a) * r, wz = eye[2] + Math.sin(a) * r, x = Math.floor(wx), y = Math.floor(wz);
        if (!open(x, y) || !dark.has(`${x},${y}`)) continue;
        out.push({ x, y, dx: wx - x - 0.5, dz: wz - y - 0.5, layer: "dk:wisp", w: 0.42 + (i % 2) * 0.12, h: 0.8 + (i % 3) * 0.12 + lean * 0.2, skew: still ? 0 : -lean * 0.3 + Math.sin(t * 1.3 + i) * 0.04, alpha: 0.9, glow: 0.7 });
        const pr = r - 0.3 - lean * 0.6, px = eye[0] + Math.cos(a + 0.12) * pr, pz = eye[2] + Math.sin(a + 0.12) * pr, qx = Math.floor(px), qz = Math.floor(pz);
        if (open(qx, qz) && dark.has(`${qx},${qz}`)) out.push({ x: qx, y: qz, dx: px - qx - 0.5, dz: pz - qz - 0.5, layer: "dk:pool", flat: true, w: 0.55 + lean * 0.5, spin: a + (still ? 0 : t * 0.2), alpha: 0.75, glow: 0.5 }); }
      return out; }; }
}
