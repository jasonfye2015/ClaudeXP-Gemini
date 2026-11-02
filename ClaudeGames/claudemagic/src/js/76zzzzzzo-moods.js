"use strict";
// Floor moods - the window's side (v37.0): each mood's look - flooded, the water's own (its rings and glints); overgrown,
// vines hung on the walls and roots at their foot, and a green cast; frozen, frost on the walls and the floor and the
// breath; haunted, a pale drifting fog, drained colour and wisps of cold light wandering the halls - and a word in the
// side panel. Rules: 69zw-moods.js.
{ const S = 256, cv = () => { const c = document.createElement("canvas"); c.width = c.height = S; return c; };
  const PAINT = {
    "mood:vines": (p) => { const r = (s) => () => ((s = (s * 1103515245 + 12345) & 0x7fffffff) / 0x7fffffff); const R = r(9); p.lineCap = "round";
      for (let v = 0; v < 6; v++) { let x = 20 + R() * 216, y = 0; p.strokeStyle = `rgb(${40 + R() * 30 | 0},${90 + R() * 50 | 0},${30 + R() * 20 | 0})`; p.lineWidth = 6 + R() * 6; p.beginPath(); p.moveTo(x, y);
        while (y < 240) { const nx = x + (R() - 0.5) * 40, ny = y + 20 + R() * 30; p.quadraticCurveTo(x + (R() - 0.5) * 30, (y + ny) / 2, nx, ny); x = nx; y = ny; } p.stroke();
        for (let k = 0; k < 8; k++) { p.fillStyle = `rgba(${60 + R() * 40 | 0},${130 + R() * 60 | 0},${40 + R() * 30 | 0},0.95)`; p.beginPath(); p.ellipse(20 + R() * 216, R() * 240, 10, 5, R() * 3, 0, Math.PI * 2); p.fill(); } } },
    "mood:roots": (p) => { p.strokeStyle = "#4A3420"; p.lineCap = "round"; for (let i = 0; i < 7; i++) { p.lineWidth = 14 - i; p.beginPath(); const x = 20 + i * 34; p.moveTo(x, 256); p.bezierCurveTo(x + 20, 200, x - 30, 170, x + 10, 120 + (i % 3) * 20); p.stroke(); } },
    "mood:wisp": (p) => { const g = p.createRadialGradient(128, 128, 2, 128, 128, 120); g.addColorStop(0, "rgba(230,245,255,1)"); g.addColorStop(0.2, "rgba(160,210,255,0.6)"); g.addColorStop(1, "rgba(120,180,255,0)"); p.fillStyle = g; p.fillRect(0, 0, S, S); },
  };
  { const b0 = CM.art.build; CM.art.build = function (theme, look) { const set = b0.call(this, theme, look); for (const [n, f] of Object.entries(PAINT)) { const c = cv(); f(c.getContext("2d")); set.index[n] = set.layers.length; set.layers.push(c); } return set; }; }
  { const ls0 = CM.lifeSprites; CM.lifeSprites = (game, fl, now) => { const out = ls0 ? ls0(game, fl, now) : []; if (!fl || !fl.mood || !CM.renderer || CM.renderer.index["mood:vines"] === undefined) return out; const [px, py] = fl.pos;
      if (fl.mood === "overgrown") for (let y = py - 6; y <= py + 6; y++) for (let x = px - 6; x <= px + 6; x++) { if (!fl.grid[y] || fl.grid[y][x] !== 0) continue; for (let f = 0; f < 4; f++) { const [dx, dy] = CM.DIRS[f]; if (!fl.grid[y + dy] || fl.grid[y + dy][x + dx] !== 1) continue; const h = CM.hashSeed(`${game.seed}:vine:${x}:${y}:${f}`); if (h % 3) continue;
          out.push({ x, y, face: f, layer: h % 2 ? "mood:vines" : "mood:roots", w: 1, h: 1 }); } }
      if (fl.mood === "haunted" && !CM.reducedMotion) for (let i = 0; i < 5; i++) { const t = now / 1000 * (0.12 + i * 0.03) + i * 2.1, cx = px + Math.sin(t) * (3 + i), cy = py + Math.cos(t * 0.8) * (3 + i); const x = Math.round(cx), y = Math.round(cy); if (!fl.grid[y] || fl.grid[y][x] !== 0) continue;
          out.push({ x, y, dx: cx - x, dz: cy - y, layer: "mood:wisp", w: 0.45, h: 0.45, lift: 0.5 + Math.sin(now / 700 + i) * 0.15, glow: 2, alpha: 0.6 + 0.3 * Math.sin(now / 400 + i) }); }
      return out; }; }
  { const gf0 = CM.gradeFor; if (gf0) CM.gradeFor = (game, r) => { const G = gf0(game, r), fl = game.floor; if (!G || !fl || !fl.mood) return G;
      if (fl.mood === "overgrown") G.mul = G.mul.map((v, i) => v * [0.9, 1.05, 0.88][i]); if (fl.mood === "frozen") { G.frost = 0.85; G.mul = G.mul.map((v, i) => v * [0.92, 0.98, 1.08][i]); } if (fl.mood === "haunted") { G.sat = (G.sat || 1) * 0.55; G.mul = G.mul.map((v, i) => v * [0.95, 1.0, 1.1][i]); G.lift = (G.lift || [0, 0, 0]).map((v, i) => v + [0.03, 0.04, 0.06][i]); } return G; }; }
  { const af0 = CM.airFor; if (af0) CM.airFor = (game, r) => { const A = af0(game, r), fl = game.floor; if (!fl || fl.mood !== "haunted") return A; return Object.assign({}, A || { haze: 0, shaft: 0 }, { haze: Math.max((A && A.haze) || 0, 0.45) }); }; }
  { const hc0 = CM.heatAndCold; if (hc0) CM.heatAndCold = (game, r) => { const H = hc0(game, r), fl = game.floor; if (H && fl && fl.mood === "frozen") { H.breath = 1; H.sparkle = Math.max(H.sparkle || 0, 0.6); } return H; }; }
  const rf0 = CM.UI.prototype.refresh; CM.UI.prototype.refresh = function (...a) { const out = rf0.apply(this, a), g = this.game, w = this.$ && this.$("#side .where"); if (w && g && g.floor && g.floor.mood && g.mode !== "title" && !w.textContent.includes(CM.MOODS[g.floor.mood].name)) w.textContent += ` - ${CM.MOODS[g.floor.mood].name.toLowerCase()}`; return out; };
}
