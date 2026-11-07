"use strict";
// The wolf pack - the window's side (UPGRADE_PLAN_77.md). Eleven wolves of CM.WOLF_PACK, each the Quaternius wolf at its
// own size (the alphas largest, the pups half) and in its own coat, moving freely through the Wood - not square by
// square: they thread between the trees (a trunk stands at each tree square's middle, and there's room either side),
// keep off rock, walls, houses and water, and give the party a wide berth. Two packs within the pack, each behind its
// alpha: the grown wolves range a little apart from their leader, the pups at an adult's heels. By day they wander out
// from the den (now and then stopping to sniff the ground or stand and look); at dusk they head home and go in at the
// cave's mouth one after another; at night they're inside, and you'll hear them breathing if you stand at the mouth;
// after dawn they come out again, one at a time. Their figures are the bodies' own (76zzzzzzzzzze-figures2.js); with
// the figures not loaded, the painted wolf stands in.
{ const COAT = { grey: null, black: [74, 74, 82], brown: [168, 122, 86], tawny: [222, 176, 116], pale: [300, 296, 288] };
  if (CM.figuresPack && CM.figuresPack.figures) for (const [c, tint] of Object.entries(COAT)) CM.figuresPack.figures[`pet:wolf_${c}`] = { model: "wolf", scale: 1, tint, wear: [] };
  // the den's rock: rounded, mottled boulders with moss on their shoulders; and its mouth, ragged and unlit
  const rock = (S, mouth) => { const c = document.createElement("canvas"); c.width = c.height = S; const p = c.getContext("2d"), k = S / 256; let seed = mouth ? 7 : 3; const rn = () => { seed = (seed * 16807) % 2147483647; return seed / 2147483647; };
    p.fillStyle = "#5E5A55"; p.fillRect(0, 0, S, S);
    for (let i = 0; i < 26; i++) { const x = rn() * S, y = rn() * S, r = (28 + rn() * 46) * k, g = p.createRadialGradient(x - r * 0.3, y - r * 0.35, r * 0.1, x, y, r); const v = 92 + rn() * 34; g.addColorStop(0, `rgb(${v + 22},${v + 20},${v + 16})`); g.addColorStop(0.7, `rgb(${v},${v - 3},${v - 8})`); g.addColorStop(1, `rgba(40,38,34,0.9)`); p.fillStyle = g; p.beginPath(); p.ellipse(x, y, r, r * (0.7 + rn() * 0.3), rn() * 3, 0, Math.PI * 2); p.fill(); }
    p.strokeStyle = "rgba(30,28,24,0.6)"; p.lineWidth = 2 * k; for (let i = 0; i < 9; i++) { let x = rn() * S, y = rn() * S; p.beginPath(); p.moveTo(x, y); for (let j = 0; j < 5; j++) { x += (rn() - 0.5) * 40 * k; y += rn() * 30 * k; p.lineTo(x, y); } p.stroke(); }
    for (let i = 0; i < 18; i++) { p.fillStyle = `rgba(${70 + rn() * 30},${110 + rn() * 30},${50 + rn() * 20},${0.35 + rn() * 0.3})`; p.beginPath(); p.ellipse(rn() * S, rn() * S * 0.3, (10 + rn() * 22) * k, (5 + rn() * 9) * k, 0, 0, Math.PI * 2); p.fill(); }
    const fade = p.createLinearGradient(0, S * 0.7, 0, S); fade.addColorStop(0, "rgba(20,18,14,0)"); fade.addColorStop(1, "rgba(20,18,14,0.45)"); p.fillStyle = fade; p.fillRect(0, S * 0.7, S, S * 0.3);
    if (mouth) { const pts = []; for (let i = 0; i <= 14; i++) { const t = i / 14, a = Math.PI * (1 - t), rx = S * 0.36, ry = S * 0.5, j = (rn() - 0.5) * 18 * k; pts.push([S / 2 + Math.cos(a) * (rx + j), S - Math.sin(a) * (ry + j) * (0.85 + 0.15 * Math.sin(t * 9))]); }
      p.fillStyle = "#2A2420"; p.beginPath(); p.moveTo(pts[0][0] - 8 * k, S); for (const [x, y] of pts) p.lineTo(x + (x < S / 2 ? -8 : 8) * k, y - 8 * k); p.lineTo(pts[pts.length - 1][0] + 8 * k, S); p.closePath(); p.fill();
      const g = p.createRadialGradient(S / 2, S * 0.95, 4 * k, S / 2, S * 0.8, S * 0.45); g.addColorStop(0, "#020202"); g.addColorStop(0.6, "#0A0908"); g.addColorStop(1, "#1A1612");
      p.fillStyle = g; p.beginPath(); p.moveTo(pts[0][0], S); for (const [x, y] of pts) p.lineTo(x, y); p.lineTo(pts[pts.length - 1][0], S); p.closePath(); p.fill();
      p.fillStyle = "rgba(200,190,170,0.5)"; for (let i = 0; i < 5; i++) p.fillRect(S * 0.3 + rn() * S * 0.4, S * 0.93 + rn() * S * 0.05, (3 + rn() * 5) * k, 1.5 * k); }   /* (a few bones at the threshold) */
    return c; };
  { const b1 = CM.art.build; CM.art.build = function (theme, look) { const set = b1.call(this, theme, look), S = set.size || 256; for (const [n, m] of [["solid:denrock", false], ["solid:denmouth", true]]) if (set.index[n] === undefined) { set.index[n] = set.layers.length; set.layers.push(rock(S, m)); } return set; }; }
  { const b0 = CM.art.build; CM.art.build = function (theme, look) { const set = b0.call(this, theme, look); if (set.index["monster:Wolf"] !== undefined) for (const c of Object.keys(COAT)) if (set.index[`pet:wolf_${c}`] === undefined) set.index[`pet:wolf_${c}`] = set.index["monster:Wolf"]; return set; }; }
  const D = CM.WOLF_DEN; if (D && CM.WOLF_PACK) {
  const R = (a, b) => a + Math.random() * (b - a), key = (x, y) => `${x},${y}`;
  let pack = null, fl0 = null, last = 0, breath = 0;
  const water = (fl) => { if (fl._wolfWater) return fl._wolfWater; const s = new Set((fl.decor || []).filter((d) => d.kind === "water").map((d) => key(d.x, d.y))); fl._wolfWater = s; return s; };
  // where a wolf may stand: open ground or among the trees (not on a trunk), never rock, wall, house or water
  const cellOk = (fl, cx, cy) => fl.grid[cy] && fl.grid[cy][cx] !== undefined && !water(fl).has(key(cx, cy)) && (fl.grid[cy][cx] === 0 || CM.solidAt(fl, cx, cy) === "tree");
  const ok = (fl, x, y) => { for (const [ox, oy] of [[0.26, 0], [-0.26, 0], [0, 0.26], [0, -0.26]]) if (!cellOk(fl, Math.floor(x + ox), Math.floor(y + oy))) return false;   /* (a body's width off rock, walls and water) */
    const cx = Math.floor(x), cy = Math.floor(y), N = fl.grid.length; if (cx < 1 || cy < 1 || cx > N - 2 || cy > N - 2) return false; if (water(fl).has(key(cx, cy))) return false;
    if (fl.grid[cy][cx] === 0) return true;
    if (CM.solidAt(fl, cx, cy) !== "tree") return false; return Math.hypot(x - (cx + 0.5), y - (cy + 0.5)) > 0.27; };
  const home = () => [D.front[0] + 0.5, D.front[1] + 0.35];
  const pickNear = (fl, x, y, r, minR = 0) => { for (let i = 0; i < 30; i++) { const a = Math.random() * Math.PI * 2, d = R(minR, r), px = x + Math.cos(a) * d, py = y + Math.sin(a) * d; if (ok(fl, px, py) && Math.hypot(px - home()[0], py - home()[1]) < D.range) return [px, py]; } return [x, y]; };
  const hour = (g) => (CM.hourOf ? CM.hourOf(g) : 12);   /* (the game's hour, with its minutes) */
  const make = (fl, g) => { const h = hour(g), day = h >= 6.5 && h < 19.5; return CM.WOLF_PACK.map((W, i) => { const lead = W.role === "alpha" ? null : [2, 3, 4, 7, 8].includes(i) ? 0 : 1, parent = W.role === "pup" ? [2, 3, 5, 6][i - 7] : null;
      const [x, y] = day ? pickNear(fl, ...home(), 9, 2) : home(); return Object.assign({}, W, { i, lead, parent, x, y, tx: x, ty: y, out: day, wake: 6 + i * 0.12 + Math.random() * 0.3, sleep: 19.2 + (W.role === "pup" ? 0 : W.role === "alpha" ? 0.5 : 0.25) + Math.random() * 0.2, pause: R(0, 4), act: null, heading: Math.random() * 6.28, speed: W.role === "pup" ? 0.75 : 0.6 }); }); };
  const spotIn = (fl, cx, cy) => { if (fl.grid[cy] && fl.grid[cy][cx] === 0) return [cx + 0.5, cy + 0.5]; for (const [ox, oy] of [[0.5, 0.14], [0.5, 0.86], [0.14, 0.5], [0.86, 0.5]]) if (ok(fl, cx + ox, cy + oy)) return [cx + ox, cy + oy]; return [cx + 0.5, cy + 0.5]; };
  const routeHome = (fl, w) => { const [hx, hy] = home(), goal = key(Math.floor(hx), Math.floor(hy)), start = [Math.floor(w.x), Math.floor(w.y)], prev = new Map([[key(...start), null]]), q = [start]; let found = false;
    while (q.length && !found) { const [x, y] = q.shift(); for (const [dx, dy] of CM.DIRS) { const nx = x + dx, ny = y + dy, k = key(nx, ny); if (prev.has(k) || !cellOk(fl, nx, ny)) continue; prev.set(k, key(x, y)); if (k === goal) { found = true; break; } q.push([nx, ny]); } if (prev.size > 4000) break; }
    if (!found) return null; const path = []; let k = goal; while (k) { const [x, y] = k.split(",").map(Number); path.unshift(spotIn(fl, x, y)); k = prev.get(k); } path.shift(); path.push(home()); return path; };
  const step = (fl, g, dt) => { const h = hour(g), [hx, hy] = home(), party = [fl.pos[0] + 0.5, fl.pos[1] + 0.5];
    for (const w of pack) {
      const homeward = h >= w.sleep || h < w.wake;
      if (!w.out) { if (!homeward && h >= w.wake) { w.out = true; w.x = hx; w.y = hy; w.tx = hx; w.ty = hy - 1.5; w.pause = 0; } continue; }
      if (!homeward) w.route = null;
      if (homeward) { w.act = null; if (Math.hypot(w.x - hx, w.y - hy) < 0.35) { w.out = false; w.route = null; continue; } if (!w.route || !w.route.length) w.route = routeHome(fl, w) || [home()]; while (w.route.length > 1 && Math.hypot(w.x - w.route[0][0], w.y - w.route[0][1]) < 0.25) w.route.shift(); [w.tx, w.ty] = w.route[0]; }
      else if ((w.pause -= dt) <= 0 && Math.hypot(w.x - w.tx, w.y - w.ty) < 0.3) {   // a new place to go, by role
        if (w.role === "alpha") [w.tx, w.ty] = pickNear(fl, w.x, w.y, 6, 2);
        else if (w.role === "adult") { const A = pack[w.lead]; [w.tx, w.ty] = A.out ? pickNear(fl, A.tx, A.ty, 3.5, 1) : pickNear(fl, w.x, w.y, 3, 1); }
        else { const P0 = pack[w.parent]; [w.tx, w.ty] = P0.out ? pickNear(fl, P0.x, P0.y, 1.5, 0.5) : pickNear(fl, w.x, w.y, 1.5, 0.3); }
        w.pause = w.role === "pup" ? R(0.5, 2.5) : R(2, 7); w.act = Math.random() < 0.35 ? (Math.random() < 0.5 ? "eat" : "idle2") : null; }
      // wary: away from the party
      const pd = Math.hypot(w.x - party[0], w.y - party[1]); if (!homeward && pd < 2.6) { const ax = (w.x - party[0]) / Math.max(pd, 0.1), ay = (w.y - party[1]) / Math.max(pd, 0.1); w.tx = w.x + ax * 3; w.ty = w.y + ay * 3; w.pause = 0; w.act = null; }
      const dx = w.tx - w.x, dy = w.ty - w.y, d = Math.hypot(dx, dy); w.moving = false; if (d < 0.05) continue; if (w.pause > 0 && !homeward && pd >= 2.6 && d < 0.3) continue;
      const sp = w.speed * (homeward || pd < 2.6 ? 1.35 : 1) * dt; let hd = Math.atan2(dy, dx), moved = false;
      for (const turn of [0, 0.5, -0.5, 1.0, -1.0, 1.6, -1.6]) { const a = hd + turn, nx = w.x + Math.cos(a) * Math.min(sp, d), ny = w.y + Math.sin(a) * Math.min(sp, d);
        if (ok(fl, nx, ny) || !ok(fl, w.x, w.y) || (homeward && (Math.hypot(nx - hx, ny - hy) < 1.2 || cellOk(fl, Math.floor(nx), Math.floor(ny))))) { w.x = nx; w.y = ny; w.heading = a; moved = true; break; } }
      if (!moved) { if (homeward) w.route = null; else [w.tx, w.ty] = pickNear(fl, w.x, w.y, 3, 1); } else { w.moving = true; w.act = null; } } };
  { const ls0 = CM.lifeSprites; CM.lifeSprites = (game, fl, now) => { const out = ls0 ? ls0(game, fl, now) : []; if (!fl || fl.number !== -1 || game.mode === "title" || !fl.grid) return out;
      if (fl0 !== fl || !pack) { pack = make(fl, game); fl0 = fl; last = now; }
      const dt = Math.min(0.1, Math.max(0, (now - last) / 1000)); last = now; if (game.mode === "explore") step(fl, game, dt);
      for (const w of pack) { if (!w.out) continue; const cx = Math.floor(w.x), cy = Math.floor(w.y);
        out.push({ x: cx, y: cy, dx: w.x - cx - 0.5, dz: w.y - cy - 0.5, layer: `pet:wolf_${w.coat}`, w: 0.95 * w.size, h: 0.75 * w.size, id: `packwolf${w.i}`, heading: Math.atan2(Math.cos(w.heading), Math.sin(w.heading)), act: w.moving ? null : w.act, walking: w.moving }); }
      // at night, at the mouth: breathing
      if (pack.every((w) => !w.out) && Math.hypot(fl.pos[0] - D.front[0], fl.pos[1] - D.front[1]) <= 3 && now > breath && CM.audio && CM.audio.play) { CM.audio.play("snore", 0.14, 0, 0.8); breath = now + R(3500, 6000); }
      return out; }; }
  CM.wolfPack = () => pack;   // (for the harness and the curious)
  }
}
