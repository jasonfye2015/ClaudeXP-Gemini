"use strict";
// The deer of the South Meadow (UPGRADE_PLAN_78.md) - the window's side, as the wolves are: a herd of ten - a stag, six
// does, three fawns about half their size - grazing the South Meadow by day, heads down, now and then one standing to
// look; bedding down at dusk among the trees at the meadow's edge, and back out to graze after dawn. They move as the
// wolves do, freely between the trees, never through rock, walls or water. And they are deer: if the party comes near,
// or one of the den's wolves, the one that sees it bolts and the whole herd goes with it at a gallop, away from it, and
// drifts back to the meadow when all is quiet again.
{ const COAT = { doe: [196, 158, 120], doe2: [176, 138, 104], doe3: [214, 182, 146], fawn: [226, 180, 132] };
  if (CM.figuresPack && CM.figuresPack.figures) { CM.figuresPack.figures["pet:deer_stag"] = { model: "stag", scale: 1, tint: null, wear: [] }; for (const [c, tint] of Object.entries(COAT)) CM.figuresPack.figures[`pet:deer_${c}`] = { model: "deer", scale: 1, tint, wear: [] }; }
  { const b0 = CM.art.build; CM.art.build = function (theme, look) { const set = b0.call(this, theme, look), D = set.index["monster:Deer"]; if (D !== undefined) for (const c of ["stag", ...Object.keys(COAT)]) if (set.index[`pet:deer_${c}`] === undefined) set.index[`pet:deer_${c}`] = D; return set; }; }
  const S = CM.SOUTH_WOOD; if (S) {
  const HERD = [{ role: "stag", coat: "stag", size: 1.25 }, { role: "doe", coat: "doe", size: 1.0 }, { role: "doe", coat: "doe2", size: 0.97 }, { role: "doe", coat: "doe3", size: 1.0 }, { role: "doe", coat: "doe", size: 0.95 },
    { role: "doe", coat: "doe2", size: 0.98 }, { role: "doe", coat: "doe3", size: 0.96 }, { role: "fawn", coat: "fawn", size: 0.55 }, { role: "fawn", coat: "fawn", size: 0.5 }, { role: "fawn", coat: "fawn", size: 0.52 }];
  CM.DEER_HERD = HERD;
  const R = (a, b) => a + Math.random() * (b - a), key = (x, y) => `${x},${y}`, M = S.meadows[0];
  const water = (fl) => { if (fl._deerWater) return fl._deerWater; const s = new Set((fl.decor || []).filter((d) => d.kind === "water").map((d) => key(d.x, d.y))); fl._deerWater = s; return s; };
  const cellOk = (fl, cx, cy) => fl.grid[cy] && fl.grid[cy][cx] !== undefined && !water(fl).has(key(cx, cy)) && (fl.grid[cy][cx] === 0 || CM.solidAt(fl, cx, cy) === "tree");
  const ok = (fl, x, y) => { for (const [ox, oy] of [[0.26, 0], [-0.26, 0], [0, 0.26], [0, -0.26]]) if (!cellOk(fl, Math.floor(x + ox), Math.floor(y + oy))) return false; const cx = Math.floor(x), cy = Math.floor(y); if (fl.grid[cy][cx] === 0) return true; return Math.hypot(x - (cx + 0.5), y - (cy + 0.5)) > 0.27; };
  const inMeadow = (x, y, pad = 0) => ((x - M.c[0] - 0.5) / (M.r[0] + 0.5 + pad)) ** 2 + ((y - M.c[1] - 0.5) / (M.r[1] + 0.5 + pad)) ** 2 <= 1;
  const pick = (fl, test, near, r) => { for (let i = 0; i < 40; i++) { const x = near[0] + R(-r, r), y = near[1] + R(-r, r); if (ok(fl, x, y) && test(x, y)) return [x, y]; } return null; };
  const centre = [M.c[0] + 0.5, M.c[1] + 0.5];
  const graze = (fl, near, r = 3) => pick(fl, (x, y) => inMeadow(x, y, 0.5), near, r) || pick(fl, (x, y) => inMeadow(x, y), centre, M.r[0]) || centre.slice();
  const bed = (fl, near) => pick(fl, (x, y) => !inMeadow(x, y, 0.3) && inMeadow(x, y, 2.5), near, 4) || pick(fl, (x, y) => !inMeadow(x, y, 0.3) && inMeadow(x, y, 3), centre, M.r[0] + 3) || centre.slice();
  let herd = null, fl0 = null, last = 0, alarm = 0, threat = null;
  const hour = (g) => (CM.hourOf ? CM.hourOf(g) : 12), day = (h) => h >= 6.5 && h < 19.7;
  const make = (fl, g) => { const d = day(hour(g)); return HERD.map((H, i) => { const p = d ? graze(fl, centre, M.r[0]) : bed(fl, centre); return Object.assign({}, H, { i, x: p[0], y: p[1], tx: p[0], ty: p[1], pause: R(0, 5), act: d ? "eat" : null, heading: Math.random() * 6.28, mother: H.role === "fawn" ? 1 + (i - 7) * 2 : null }); }); };
  const step = (fl, g, dt, now) => { const h = hour(g), d = day(h), party = [fl.pos[0] + 0.5, fl.pos[1] + 0.5], wolves = (CM.wolfPack && CM.wolfPack()) || [];
    // who sees a threat: the party within four and a half squares, a wolf (out of the den) within five
    if (now > alarm) { threat = null; for (const w of herd) { if (Math.hypot(w.x - party[0], w.y - party[1]) < 4.5) { threat = party; break; } const wf = wolves.find((v) => v.out && Math.hypot(v.x - w.x, v.y - w.y) < 5); if (wf) { threat = [wf.x, wf.y]; break; } } if (threat) alarm = now + 3500; }
    for (const w of herd) { w.running = false;
      if (threat && now < alarm) { const dx = w.x - threat[0], dy = w.y - threat[1], dd = Math.max(0.1, Math.hypot(dx, dy)); w.tx = w.x + (dx / dd) * 5; w.ty = w.y + (dy / dd) * 5; w.running = true; w.act = null; w.pause = R(2, 5); }
      else if ((w.pause -= dt) <= 0 && Math.hypot(w.x - w.tx, w.y - w.ty) < 0.3) {
        if (!d) { const p = w.role === "fawn" ? [herd[w.mother].x + R(-0.6, 0.6), herd[w.mother].y + R(-0.6, 0.6)] : bed(fl, [w.x, w.y]); [w.tx, w.ty] = ok(fl, p[0], p[1]) ? p : [w.x, w.y]; w.pause = R(20, 60); w.act = null; }
        else { const near = w.role === "fawn" ? [herd[w.mother].x, herd[w.mother].y] : w.role === "stag" ? [w.x, w.y] : [herd[0].x, herd[0].y]; [w.tx, w.ty] = graze(fl, near, w.role === "fawn" ? 1.2 : 3); w.pause = w.role === "fawn" ? R(1, 4) : R(4, 12); w.act = Math.random() < 0.7 ? "eat" : "idle2"; } }
      const dx = w.tx - w.x, dy = w.ty - w.y, dd = Math.hypot(dx, dy); w.moving = false; if (dd < 0.06) continue;
      const sp = (w.running ? 2.2 : 0.45) * dt * (w.role === "fawn" && !w.running ? 1.3 : 1); let moved = false;
      for (const turn of [0, 0.5, -0.5, 1.0, -1.0, 1.6, -1.6]) { const a = Math.atan2(dy, dx) + turn, nx = w.x + Math.cos(a) * Math.min(sp, dd), ny = w.y + Math.sin(a) * Math.min(sp, dd); if (ok(fl, nx, ny) || !ok(fl, w.x, w.y)) { w.x = nx; w.y = ny; w.heading = a; moved = true; break; } }
      if (moved) { w.moving = true; w.act = null; } else { [w.tx, w.ty] = d ? graze(fl, [w.x, w.y]) : bed(fl, [w.x, w.y]); w.running = false; } } };
  { const ls0 = CM.lifeSprites; CM.lifeSprites = (game, fl, now) => { const out = ls0 ? ls0(game, fl, now) : []; if (!fl || fl.number !== -1 || game.mode === "title" || !fl.grid || fl.grid.length <= S.top) return out;
      if (fl0 !== fl || !herd) { herd = make(fl, game); fl0 = fl; last = now; }
      const dt = Math.min(0.1, Math.max(0, (now - last) / 1000)); last = now; if (game.mode === "explore") step(fl, game, dt, now);
      for (const w of herd) { const cx = Math.floor(w.x), cy = Math.floor(w.y);
        out.push({ x: cx, y: cy, dx: w.x - cx - 0.5, dz: w.y - cy - 0.5, layer: `pet:deer_${w.coat}`, w: 0.95 * w.size, h: 0.95 * w.size, id: `deer${w.i}`, heading: Math.atan2(Math.cos(w.heading), Math.sin(w.heading)), act: w.moving ? null : w.act, walking: w.moving, running: w.running && w.moving }); }
      return out; }; }
  CM.deerHerd = () => herd;   // (for the harness and the curious)
  }
}
