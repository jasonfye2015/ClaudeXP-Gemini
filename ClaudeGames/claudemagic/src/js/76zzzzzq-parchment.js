"use strict";
// The map as an object (v31.8, UPGRADE_PLAN_26.md): the big map (Tab) on parchment - old paper, darker at its edges and
// blotched; the walls inked with a hand's wobble; each newly seen square inked in with a spreading blot; the party's
// route in pencil. The graph-paper map underneath is drawn as before and laid into the paper (its marks, icons and
// notes all kept). Settings > The big map: Parchment or Graph paper. The side map is left as it was.
{ const papers = new Map(), firstSeen = new Map(), route = new Map(); let anim = 0;
  CM.settingLater((ui) => CM.addSetting("set-mapstyle", "The big map (Tab) - on parchment, inked by hand, or plain graph paper", [["parchment", "Parchment"], ["plain", "Graph paper"]], "mapStyle", "parchment", ui));
  const paper = (W) => { let c = papers.get(W); if (c) return c; c = document.createElement("canvas"); c.width = c.height = W; const p = c.getContext("2d"); let s = 77; const r = () => ((s = (s * 1103515245 + 12345) & 0x7fffffff) / 0x7fffffff);
    p.fillStyle = "#E6D3A6"; p.fillRect(0, 0, W, W);
    for (let i = 0; i < 260; i++) { const x = r() * W, y = r() * W, rr = W * (0.01 + r() * 0.06), g = p.createRadialGradient(x, y, 0, x, y, rr); g.addColorStop(0, `rgba(${150 + r() * 40 | 0},${110 + r() * 30 | 0},${60 + r() * 20 | 0},${0.05 + r() * 0.07})`); g.addColorStop(1, "rgba(150,110,60,0)"); p.fillStyle = g; p.fillRect(x - rr, y - rr, rr * 2, rr * 2); }
    p.strokeStyle = "rgba(120,90,50,0.08)"; p.lineWidth = 1; for (let i = 0; i < 500; i++) { const x = r() * W, y = r() * W, a = r() * Math.PI; p.beginPath(); p.moveTo(x, y); p.lineTo(x + Math.cos(a) * 8, y + Math.sin(a) * 8); p.stroke(); }
    const e = p.createRadialGradient(W / 2, W / 2, W * 0.32, W / 2, W / 2, W * 0.74); e.addColorStop(0, "rgba(90,55,20,0)"); e.addColorStop(1, "rgba(90,55,20,0.55)"); p.fillStyle = e; p.fillRect(0, 0, W, W);
    papers.set(W, c); return c; };
  const wob = (x, y, k) => ((Math.sin(x * 12.9898 + y * 78.233 + k) * 43758.5453) % 1) * 0.5;
  { const G = CM.Game.prototype, em0 = G.emit; G.emit = function (ev, ...a) { if (ev === "moved" && this.floor) { const k = this.floor; let R = route.get(k); if (!R) route.set(k, (R = [])); const L = R[R.length - 1]; if (!L || L[0] !== a[0] || L[1] !== a[1]) R.push([a[0], a[1]]); if (R.length > 600) R.shift(); } return em0.call(this, ev, ...a); }; }
  const P = CM.UI.prototype, d0 = P.drawAutomap;
  P.drawAutomap = function (canvas) {
    const g = this.game, fl = g.towerRun ? g.towerRun.fl : g.floor;
    if (!canvas || canvas.id !== "bigmap-canvas" || !fl || (g.settings && g.settings.mapStyle === "plain")) return d0.call(this, canvas);
    const W = canvas.width, off = this._parchOff || (this._parchOff = document.createElement("canvas")); off.width = off.height = W;
    d0.call(this, off);                                                     // (the map as it always was, then laid into the paper)
    const p = canvas.getContext("2d"), size = fl.grid.length, cell = W / size, now = performance.now();
    p.globalCompositeOperation = "source-over"; p.drawImage(paper(W), 0, 0);
    p.globalCompositeOperation = "multiply"; p.globalAlpha = 0.9; p.drawImage(off, 0, 0); p.globalAlpha = 1; p.globalCompositeOperation = "source-over";
    let seenAt = firstSeen.get(fl); if (!seenAt) { seenAt = new Map(); firstSeen.set(fl, seenAt); for (const [x, y] of fl.seen) seenAt.set(`${x},${y}`, 0); }
    const open = (x, y) => y >= 0 && y < size && x >= 0 && x < size && !fl.grid[y][x]; let blotting = false;
    p.strokeStyle = "rgba(40,26,14,0.85)"; p.lineCap = "round";
    for (const [x, y] of fl.seen) { const k = `${x},${y}`; if (!seenAt.has(k)) seenAt.set(k, now); const age = now - seenAt.get(k), cx = (x + 0.5) * cell, cy = (y + 0.5) * cell;
      if (age < 900 && !CM.reducedMotion) { blotting = true; const e = age / 900; p.fillStyle = `rgba(60,36,16,${0.35 * (1 - e)})`; p.beginPath(); p.arc(cx, cy, cell * (0.2 + 0.7 * e), 0, Math.PI * 2); p.fill(); }
      if (fl.grid[y][x]) continue; p.lineWidth = Math.max(1.2, cell * 0.11);
      for (const [dx, dy] of CM.DIRS) { if (open(x + dx, y + dy)) continue; const a = dx ? [x + (dx > 0 ? 1 : 0), y] : [x, y + (dy > 0 ? 1 : 0)], b = dx ? [a[0], a[1] + 1] : [a[0] + 1, a[1]];
        const j1 = wob(a[0], a[1], 1) * cell * 0.14, j2 = wob(b[0], b[1], 2) * cell * 0.14, mx = (a[0] + b[0]) / 2, my = (a[1] + b[1]) / 2, jm = wob(mx, my, 3) * cell * 0.2;
        p.beginPath(); p.moveTo(a[0] * cell + j1, a[1] * cell + j1); p.quadraticCurveTo(mx * cell + (dx ? jm : 0), my * cell + (dy ? jm : 0), b[0] * cell + j2, b[1] * cell + j2); p.stroke(); } }
    const R = route.get(fl);                                                // the route, in pencil
    if (R && R.length > 1) { p.strokeStyle = "rgba(70,70,76,0.55)"; p.lineWidth = Math.max(1, cell * 0.07); p.setLineDash([cell * 0.3, cell * 0.12]); p.beginPath();
      R.forEach(([x, y], i) => { const px = (x + 0.5 + wob(x, y, 5) * 0.25) * cell, py = (y + 0.5 + wob(y, x, 6) * 0.25) * cell; if (i) p.lineTo(px, py); else p.moveTo(px, py); }); p.stroke(); p.setLineDash([]); }
    if (blotting && !anim) anim = requestAnimationFrame(() => { anim = 0; if (document.querySelector("#bigmap.on")) this.drawAutomap(canvas); });
  };
}
