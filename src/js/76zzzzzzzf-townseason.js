"use strict";
// The town by season (v40.4, UPGRADE_PLAN_35.md): Caer Duin dresses for the time of year - in winter snow lies on its
// roofs, icicles hang from the eaves and drifts bank against the walls; in spring the window boxes are pink and white and
// blossom drifts down from the trees; in summer the boxes are red with geraniums; in autumn sheaves of the harvest lean
// by the doors, and pumpkins sit beside them. By the run's season (CM.season); every place by a hash, so nothing moves.
{ const S = 128, cv = () => { const c = document.createElement("canvas"); c.width = c.height = S; return c; };
  const box = (cols) => (p) => { p.fillStyle = "#5A3A22"; p.fillRect(4, 84, 120, 40); p.fillStyle = "#7A5232"; p.fillRect(4, 84, 120, 6); p.fillStyle = "#3E6A2A"; for (let x = 8; x < 120; x += 10) { p.beginPath(); p.ellipse(x + 4, 78, 7, 10, 0, 0, Math.PI * 2); p.fill(); }
    for (let i = 0; i < 14; i++) { p.fillStyle = cols[i % cols.length]; p.beginPath(); p.arc(10 + i * 8.5, 66 + (i % 3) * 7, 6, 0, Math.PI * 2); p.fill(); } };
  const PAINT = {
    "tw:boxspring": box(["#F4B8D0", "#FFFFFF", "#E890B8"]), "tw:boxsummer": box(["#D8202A", "#F04048", "#FFFFFF"]),
    "tw:sheaf": (p) => { p.fillStyle = "#C8A040"; p.beginPath(); p.moveTo(64, 120); p.lineTo(20, 10); p.lineTo(108, 10); p.closePath(); p.fill(); p.fillStyle = "#E0BC58"; for (let i = 0; i < 9; i++) p.fillRect(26 + i * 9, 4, 4, 30); p.fillStyle = "#B08830"; p.beginPath(); p.moveTo(64, 120); p.lineTo(40, 128); p.lineTo(88, 128); p.closePath(); p.fill(); p.fillStyle = "#7A5020"; p.fillRect(40, 70, 48, 8); },
    "tw:pumpkin": (p) => { p.fillStyle = "#E07A20"; for (const [x, r] of [[44, 34], [84, 34], [64, 40]]) { p.beginPath(); p.ellipse(x, 90, r, 32, 0, 0, Math.PI * 2); p.fill(); } p.fillStyle = "#B85A10"; p.fillRect(62, 60, 4, 60); p.fillStyle = "#4A6A2A"; p.fillRect(60, 44, 8, 18); },
    "tw:icicles": (p) => { p.fillStyle = "#F4FAFF"; p.fillRect(0, 0, 128, 14); p.fillStyle = "#DCEEFF"; for (let i = 0; i < 12; i++) { const x = 4 + i * 10.5, h = 30 + ((i * 37) % 70); p.beginPath(); p.moveTo(x, 12); p.lineTo(x + 8, 12); p.lineTo(x + 3, 12 + h); p.closePath(); p.fill(); } },
    "tw:drift": (p) => { p.fillStyle = "#F0F6FF"; p.beginPath(); p.ellipse(64, 64, 62, 40, 0, 0, Math.PI * 2); p.fill(); p.fillStyle = "#FFFFFF"; p.beginPath(); p.ellipse(54, 56, 34, 20, 0, 0, Math.PI * 2); p.fill(); },
    "tw:petal": (p) => { p.fillStyle = "#F8C8DA"; p.beginPath(); p.ellipse(64, 64, 44, 26, 0.5, 0, Math.PI * 2); p.fill(); },
  };
  const snowRoof = (src) => { const c = cv(), p = c.getContext("2d"); p.drawImage(src, 0, 0, S, S); const r = new CM.Random(17); p.fillStyle = "#F2F6FC"; p.fillRect(0, 0, S, 96);
    for (let x = 0; x < S; x += 6) { p.beginPath(); p.arc(x + 3, 96, 4 + r.next() * 6, 0, Math.PI * 2); p.fill(); } p.fillStyle = "#DCE6F2"; for (let i = 0; i < 26; i++) p.fillRect(r.next() * S, r.next() * 90, 10 + r.next() * 16, 2); return c; };
  { const b0 = CM.art.build; CM.art.build = function (theme, look) { const set = b0.call(this, theme, look); for (const [n, f] of Object.entries(PAINT)) { const c = cv(); f(c.getContext("2d")); set.index[n] = set.layers.length; set.layers.push(c); }
      const at = set.index["solid:roof"]; if (CM.art.season === "winter" && at !== undefined && (theme === CM.TOWN_THEME || theme === CM.WOOD_THEME)) { try { set.layers[at] = snowRoof(set.layers[at]); } catch (e) { /* (a picture not drawable here: left bare) */ } } return set; }; }
  // where: every street square beside a house's wall, and the way to the wall
  const plan = (fl) => { const out = [], N = fl.grid.length, open = (x, y) => fl.grid[y] && fl.grid[y][x] === 0;
    for (let y = 1; y < N - 1; y++) for (let x = 1; x < N - 1; x++) { if (!open(x, y) || fl.things[`${x},${y}`]) continue;
      for (let d = 0; d < 4; d++) { const [dx, dy] = CM.DIRS[d], kind = CM.inBounds(fl, x + dx, y + dy) && fl.grid[y + dy][x + dx] !== 0 ? CM.solidAt(fl, x + dx, y + dy) : null; if (!["house", "door", "shop"].includes(kind)) continue;
        out.push({ x, y, d, kind, h: CM.hashSeed(`townseason:${x},${y},${d}`) >>> 0 }); } }
    const trees = []; for (let y = 1; y < N - 1; y++) for (let x = 1; x < N - 1; x++) if (fl.grid[y][x] !== 0 && CM.solidAt(fl, x, y) === "tree") trees.push([x, y]); return { walls: out, trees }; };
  let cached = null, cachedAt = 0;
  { const ls0 = CM.lifeSprites; CM.lifeSprites = (game, fl, now) => { const out = ls0 ? ls0(game, fl, now) : []; if (!fl || fl.number !== 0 || !CM.renderer || CM.renderer.index["tw:sheaf"] === undefined) return out;
      if (!cached || cached.fl !== fl || now - cachedAt > 3000) { cached = Object.assign(plan(fl), { fl }); cachedAt = now; }
      const season = CM.season ? CM.season(game) : "summer", t = now / 1000, still = CM.reducedMotion, near = (x, y) => Math.abs(x - fl.pos[0]) + Math.abs(y - fl.pos[1]) <= 10;
      for (const w of cached.walls) { if (!near(w.x, w.y)) continue; const [dx, dy] = CM.DIRS[w.d];
        if (season === "winter") { if (w.h % 2 === 0) out.push({ x: w.x, y: w.y, layer: "tw:icicles", face: w.d, w: 1, h: 0.22, lift: 0.98 }); if (w.h % 3 === 0) out.push({ x: w.x, y: w.y, layer: "tw:drift", flat: true, w: 0.6, dx: dx * 0.3, dz: dy * 0.3 }); }
        else if ((season === "spring" || season === "summer") && w.kind === "house" && w.h % 3 !== 0) out.push({ x: w.x, y: w.y, layer: season === "spring" ? "tw:boxspring" : "tw:boxsummer", face: w.d, w: 0.5, h: 0.16, lift: 0.12 });
        else if (season === "autumn" && w.h % 4 === 0) out.push({ x: w.x, y: w.y, layer: w.h % 8 === 0 ? "tw:pumpkin" : "tw:sheaf", w: w.h % 8 === 0 ? 0.32 : 0.28, h: w.h % 8 === 0 ? 0.2 : 0.5, dx: dx * 0.36 + ((w.h >>> 4) % 2 ? 0.25 : -0.25) * dy, dz: dy * 0.36 + ((w.h >>> 4) % 2 ? 0.25 : -0.25) * dx }); }
      if (season === "spring" && !still) for (const [x, y] of cached.trees) { if (!near(x, y)) continue; for (let i = 0; i < 3; i++) { const ph = (t * 0.12 + i / 3 + (x * 7 + y) * 0.13) % 1; out.push({ x, y, layer: "tw:petal", w: 0.04, h: 0.04, dx: Math.sin(t * 0.7 + i * 2 + x) * 0.6, dz: Math.cos(t * 0.5 + i + y) * 0.6, lift: 2.2 * (1 - ph), alpha: Math.min(1, (1 - ph) * 3) }); } }
      return out; }; }
}
