"use strict";
// Presentation, third pass (UPGRADE_PLAN_74.md, release 3): Claude's map. Below ground the automap is the map he draws
// as you go - the game's own map first (its marks, its doors, the party's arrow, your flags all as they were), then his
// ink over it: the walls' edges ruled in brown ink with a hand's small wobble, the unknown hatched rather than blank,
// a soft darkening at the sheet's edges, and once the map is large enough, the rooms' names written in. Settings >
// Map: Claude's or Plain. The town and the Wood keep their coloured map.
{ const hash = (x, y) => { const s = Math.sin(x * 127.1 + y * 311.7) * 43758.5453; return s - Math.floor(s); };
  const da0 = CM.UI.prototype.drawAutomap; CM.UI.prototype.drawAutomap = function (canvas, ...a) { const out = da0.call(this, canvas, ...a), g = this.game, fl = g.towerRun ? g.towerRun.fl : g.floor;
    if (!fl || !(fl.number >= 1) || fl.special === "interior" || ((g.settings || {}).mapstyle || "claude") !== "claude") return out;
    try { const p = canvas.getContext("2d"), W = canvas.width, N = fl.grid.length, cell = W / N, seen = new Set((fl.seen || []).map(([x, y]) => `${x},${y}`)), open = (x, y) => fl.grid[y] && fl.grid[y][x] === 0;
      // the unknown, hatched
      p.save(); p.strokeStyle = "rgba(120,90,50,0.28)"; p.lineWidth = Math.max(0.6, cell * 0.06);
      for (let y = 0; y < N; y++) for (let x = 0; x < N; x++) { if (seen.has(`${x},${y}`)) continue; p.fillStyle = "rgba(214,196,160,0.85)"; p.fillRect(x * cell, y * cell, cell, cell);
        p.beginPath(); for (let k = -1; k <= 1; k++) { const o = (k + 0.5) * cell * 0.5; p.moveTo(x * cell + Math.max(0, o), y * cell + Math.max(0, -o)); p.lineTo(x * cell + Math.min(cell, cell + o), y * cell + Math.min(cell, cell - o)); } p.stroke(); }
      // seen walls: a darker wash, and their edges against the floor ruled in ink
      p.strokeStyle = "rgba(90,60,30,0.55)"; p.lineWidth = Math.max(0.7, cell * 0.07); for (const k of seen) { const [x, y] = k.split(",").map(Number); if (open(x, y)) continue; p.fillStyle = "#CDB48A"; p.fillRect(x * cell, y * cell, cell, cell); p.beginPath(); for (let j = 1; j < 4; j++) { const o = j * cell / 4; p.moveTo(x * cell + o, y * cell); p.lineTo(x * cell, y * cell + o); p.moveTo(x * cell + cell, y * cell + o); p.lineTo(x * cell + o, y * cell + cell); } p.moveTo(x * cell + cell, y * cell); p.lineTo(x * cell, y * cell + cell); p.stroke(); }
      p.strokeStyle = "#4A2E16"; p.lineWidth = Math.max(1.2, cell * 0.14); p.lineCap = "round"; p.beginPath();
      for (const k of seen) { const [x, y] = k.split(",").map(Number); if (!open(x, y)) continue; const w = (u, v) => (hash(u, v) - 0.5) * cell * 0.08;
        for (const [dx, dy, x0, y0, x1, y1] of [[0, -1, 0, 0, 1, 0], [0, 1, 0, 1, 1, 1], [-1, 0, 0, 0, 0, 1], [1, 0, 1, 0, 1, 1]]) if (!open(x + dx, y + dy)) {
          const ax = (x + x0) * cell, ay = (y + y0) * cell, bx = (x + x1) * cell, by = (y + y1) * cell; p.moveTo(ax + w(ax, ay), ay + w(ay, ax)); p.lineTo(bx + w(bx, by), by + w(by, bx)); } }
      p.stroke();
      // the sheet's edges
      const vg = p.createRadialGradient(W / 2, W / 2, W * 0.35, W / 2, W / 2, W * 0.75); vg.addColorStop(0, "rgba(120,80,30,0)"); vg.addColorStop(1, "rgba(120,80,30,0.28)"); p.fillStyle = vg; p.fillRect(0, 0, W, W);
      // the rooms' names, in his hand, when there's room to write them
      if (cell >= 14) { p.font = `italic ${Math.max(10, Math.min(16, cell * 0.55))}px Georgia`; p.textAlign = "center"; p.fillStyle = "rgba(70,44,20,0.85)";
        for (const R of fl.rooms || []) { if (!R.name) continue; const cx = Math.floor((R.x0 + R.x1) / 2), cy = Math.floor((R.y0 + R.y1) / 2); if (!seen.has(`${cx},${cy}`)) continue; p.save(); p.strokeStyle = "rgba(240,228,200,0.95)"; p.lineWidth = 3; p.strokeText(R.name, (R.x0 + R.x1 + 1) / 2 * cell, (R.y0 - 0.25) * cell > 10 ? (R.y0 - 0.2) * cell : (R.y1 + 1.2) * cell); p.restore(); p.fillText(R.name, (R.x0 + R.x1 + 1) / 2 * cell, (R.y0 - 0.25) * cell > 10 ? (R.y0 - 0.2) * cell : (R.y1 + 1.2) * cell); } }
      p.restore(); } catch (e) { /* (the plain map stands) */ }
    return out; };
  if (CM.settingLater && CM.addSetting) CM.settingLater((ui) => CM.addSetting("set-mapstyle", "Map below ground - Claude's (ink, hatched where unknown, the rooms named) or Plain (the graph paper)", [["claude", "Claude's"], ["plain", "Plain"]], "mapstyle", "claude", ui));
}
