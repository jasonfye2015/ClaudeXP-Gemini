"use strict";
// Furniture by the room's purpose (v40.2, UPGRADE_PLAN_35.md): a plain room below ground is now and then something - a
// library (shelves along its walls and a reading table), a guardroom (weapon racks, a table and benches), a tomb
// (sarcophagi laid in a row), a hall (banners on the walls and a long table down the middle) - by a hash of the floor
// and the room, so it never moves; the rest stay bare. Furniture keeps off things, features and doorways, and out of a
// band's landmark room. Drawn only: nothing in the floor changes.
{ const S = 128, cv = () => { const c = document.createElement("canvas"); c.width = c.height = S; return c; };
  const PAINT = {
    "fu:shelf": (p) => { p.fillStyle = "#4A3020"; p.fillRect(4, 0, 120, 128); p.fillStyle = "#2A1A10"; for (let r = 0; r < 4; r++) p.fillRect(12, 8 + r * 30, 104, 24);
      const cols = ["#7A2A20", "#2A4A6A", "#5A6A2A", "#8A6A2A", "#4A2A5A", "#6A4A3A"]; for (let r = 0; r < 4; r++) { let x = 14; let i = r * 3; while (x < 110) { const w = 5 + ((i * 7) % 6); p.fillStyle = cols[i % cols.length]; p.fillRect(x, 12 + r * 30 + (i % 3), w, 20 - (i % 3)); x += w + 1; i++; } } },
    "fu:rack": (p) => { p.fillStyle = "#5A4030"; p.fillRect(8, 20, 112, 10); p.fillRect(8, 96, 112, 10); p.fillRect(8, 20, 8, 108); p.fillRect(112, 20, 8, 108);
      for (const [x, k] of [[30, 0], [50, 1], [70, 0], [90, 2]]) { p.fillStyle = "#B0B4BC"; if (k === 0) { p.fillRect(x - 2, 4, 5, 110); p.fillStyle = "#6A4A2A"; p.fillRect(x - 6, 70, 13, 6); } else if (k === 1) { p.fillStyle = "#6A4A2A"; p.fillRect(x - 2, 10, 4, 110); p.fillStyle = "#B0B4BC"; p.beginPath(); p.moveTo(x, 0); p.lineTo(x + 6, 14); p.lineTo(x - 6, 14); p.fill(); }
        else { p.fillStyle = "#6A4A2A"; p.fillRect(x - 2, 20, 4, 100); p.fillStyle = "#B0B4BC"; p.beginPath(); p.moveTo(x, 18); p.lineTo(x + 16, 30); p.lineTo(x, 42); p.fill(); } } },
    "fu:table": (p) => { p.fillStyle = "#6A4A2E"; p.fillRect(4, 56, 120, 14); p.fillStyle = "#4A3020"; p.fillRect(12, 70, 10, 58); p.fillRect(106, 70, 10, 58); p.fillStyle = "#8A6A44"; p.fillRect(4, 56, 120, 4); p.fillStyle = "#D8C8A0"; p.fillRect(40, 48, 22, 8); p.fillStyle = "#7A5A3A"; p.fillRect(76, 44, 10, 12); },
    "fu:bench": (p) => { p.fillStyle = "#5A3E26"; p.fillRect(4, 88, 120, 12); p.fillRect(14, 100, 10, 28); p.fillRect(104, 100, 10, 28); p.fillStyle = "#7A5A3A"; p.fillRect(4, 88, 120, 3); },
    "fu:sarc": (p) => { p.fillStyle = "#8A8274"; p.fillRect(6, 64, 116, 64); p.fillStyle = "#A69E8E"; p.fillRect(2, 52, 124, 16); p.fillStyle = "#6E675A"; p.fillRect(16, 80, 96, 4); p.fillRect(16, 100, 96, 4);
      p.fillStyle = "#B8B0A0"; p.beginPath(); p.ellipse(64, 50, 40, 10, 0, Math.PI, 0); p.fill(); p.fillStyle = "#958D7E"; p.beginPath(); p.arc(64, 42, 9, 0, Math.PI * 2); p.fill(); },
    "fu:banner": (p) => { p.fillStyle = "#4A3424"; p.fillRect(20, 0, 88, 8); p.fillStyle = "#2A3A6A"; p.beginPath(); p.moveTo(28, 8); p.lineTo(100, 8); p.lineTo(100, 120); p.lineTo(64, 100); p.lineTo(28, 120); p.closePath(); p.fill();
      p.fillStyle = "#C8A040"; p.fillRect(28, 8, 72, 6); p.beginPath(); p.moveTo(64, 30); p.lineTo(80, 56); p.lineTo(64, 82); p.lineTo(48, 56); p.closePath(); p.fill(); },
  };
  { const b0 = CM.art.build; CM.art.build = function (theme, look) { const set = b0.call(this, theme, look); for (const [n, f] of Object.entries(PAINT)) { const c = cv(); f(c.getContext("2d")); set.index[n] = set.layers.length; set.layers.push(c); } return set; }; }
  const PURPOSES = ["library", "guardroom", "tomb", "hall"];
  CM.roomPurpose = (fl, r) => { if (!fl || fl.number < 1 || fl.number % 1 !== 0 || r.name || r.template) return null; const v = Math.floor(new CM.Random(CM.hashSeed(`purpose:${fl.number}:${r.x0},${r.y0},${r.x1},${r.y1}`)).next() * 7); return v < 4 ? PURPOSES[v] : null; };
  const plan = (fl) => { const out = [], key = (x, y) => `${x},${y}`, open = (x, y) => fl.grid[y] && fl.grid[y][x] === 0, M = fl.landmark;
    const clear = (x, y) => open(x, y) && !fl.things[key(x, y)] && !fl.features[key(x, y)];
    for (const r of fl.rooms || []) { const P = CM.roomPurpose(fl, r); if (!P || (M && M.x0 === r.x0 && M.y0 === r.y0)) continue; const W = r.x1 - r.x0 + 1, H = r.y1 - r.y0 + 1; if (W < 3 || H < 3) continue;
      // along the walls: each edge square whose wall side is solid (not a doorway), every other one
      const edge = []; for (let y = r.y0; y <= r.y1; y++) for (let x = r.x0; x <= r.x1; x++) for (let d = 0; d < 4; d++) { const [dx, dy] = CM.DIRS[d]; if (!clear(x, y) || open(x + dx, y + dy)) continue; const inside = x + dx >= r.x0 && x + dx <= r.x1 && y + dy >= r.y0 && y + dy <= r.y1; if (!inside && (x + y) % 2 === 0) edge.push([x, y, d]); }
      const cx = Math.floor((r.x0 + r.x1) / 2), cy = Math.floor((r.y0 + r.y1) / 2), wide = W >= H;
      if (P === "library") { for (const [x, y, d] of edge) out.push({ x, y, layer: "fu:shelf", face: d, w: 0.86, h: 0.9, lift: -0.05 }); if (clear(cx, cy)) out.push({ x: cx, y: cy, layer: "fu:table", w: 0.7, h: 0.5 }); }
      if (P === "guardroom") { for (const [x, y, d] of edge.slice(0, 4)) out.push({ x, y, layer: "fu:rack", face: d, w: 0.8, h: 0.75, lift: -0.1 }); if (clear(cx, cy)) { out.push({ x: cx, y: cy, layer: "fu:table", w: 0.7, h: 0.5 }); out.push({ x: cx, y: cy, layer: "fu:bench", w: 0.6, h: 0.35, dx: wide ? 0 : 0.3, dz: wide ? 0.3 : 0 }); } }
      if (P === "tomb") { const n = Math.max(1, Math.floor((wide ? W : H) / 2)); for (let i = 0; i < n; i++) { const x = wide ? r.x0 + i * 2 + (W % 2 ? 0 : 0) : cx, y = wide ? cy : r.y0 + i * 2; if (clear(x, y)) out.push({ x, y, layer: "fu:sarc", w: 0.62, h: 0.42 }); } }
      if (P === "hall") { for (const [x, y, d] of edge.slice(0, 6)) out.push({ x, y, layer: "fu:banner", face: d, w: 0.5, h: 0.6, lift: 0.18 }); for (let i = -1; i <= 1; i++) { const x = wide ? cx + i : cx, y = wide ? cy : cy + i; if (clear(x, y)) out.push({ x, y, layer: "fu:table", w: 0.95, h: 0.45 }); } } }
    return out; };
  const cache = new WeakMap();
  { const ls0 = CM.lifeSprites; CM.lifeSprites = (game, fl, now) => { const out = ls0 ? ls0(game, fl, now) : []; if (!fl || !fl.rooms || fl.number < 1 || !CM.renderer || CM.renderer.index["fu:table"] === undefined) return out;
      let c = cache.get(fl); if (!c || c.n !== Object.keys(fl.things).length) { c = { n: Object.keys(fl.things).length, list: plan(fl) }; cache.set(fl, c); }
      for (const s of c.list) if (Math.abs(s.x - fl.pos[0]) + Math.abs(s.y - fl.pos[1]) <= 10 && !fl.things[`${s.x},${s.y}`] && (s.face !== undefined || s.x !== fl.pos[0] || s.y !== fl.pos[1])) out.push(Object.assign({}, s)); return out; }; }
}
