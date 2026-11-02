"use strict";
// Distant views (v24.4, UPGRADE_PLAN_19.md): beyond the edge of each place, what really lies beyond it, where it lies.
// From the land the town stands on its hill to the east, past the cliffs and the West Gate - its wall, its roofs, the
// keep and the temple's spire - and after dark its windows shine out over the Wood. From the town the Mage Tower rises
// on the skyline to the north-west, where it stands in the land, its top window lit at night, over the Wood's
// treeline. 26-surface.js asks here for the quads (CM.farViews); the pictures are painted once a set.
{ const FV = CM.FARVIEW = { townX: 8, townZ: [6, 62], townH: 9, slices: 3, towerAt: [-13, 1], towerW: 3.2, towerH: 13 };
  // the town on its hill, as one wide picture cut into slices (each a texture layer); `lit`: only its lit windows
  const paintTown = (size, lit) => {
    const W = size * FV.slices, H = Math.round(size * FV.townH / ((FV.townZ[1] - FV.townZ[0]) / FV.slices)), c = document.createElement("canvas"); c.width = W; c.height = H;
    const p = c.getContext("2d"), rnd = new CM.Random(CM.hashSeed("far:town")), wins = [];
    const hill = (x) => H * (0.62 - 0.1 * Math.sin((x / W) * Math.PI) - 0.03 * Math.sin(x / W * 13));
    if (!lit) { p.fillStyle = "#3E4C38"; p.beginPath(); p.moveTo(0, H); for (let x = 0; x <= W; x += 8) p.lineTo(x, hill(x)); p.lineTo(W, H); p.closePath(); p.fill();
      p.fillStyle = "#5C5A54"; for (let x = 0; x < W; x += 6) { const y = hill(x); p.fillRect(x, y + H * 0.04, 6, H * (0.18 + 0.06 * Math.sin(x * 0.05))); } }   // (the grey of the cliffs)
    const wallY = (x) => hill(x) - H * 0.12, x0 = W * 0.06, x1 = W * 0.94;
    for (let x = x0; x < x1; x += W * 0.012 + rnd.next() * W * 0.02) {          // the houses within, roofs over the wall
      const w = W * (0.018 + rnd.next() * 0.03), h = H * (0.08 + rnd.next() * 0.12), base = wallY(x) + H * 0.02, roofH = H * (0.05 + rnd.next() * 0.06);
      if (!lit) { p.fillStyle = ["#C8B898", "#B8A888", "#D8C8A8"][Math.floor(rnd.next() * 3)]; p.fillRect(x, base - h, w, h);
        p.fillStyle = ["#7A3A2A", "#6A3A28", "#5A4A40", "#8A4A30"][Math.floor(rnd.next() * 4)]; p.beginPath(); p.moveTo(x - w * 0.08, base - h); p.lineTo(x + w / 2, base - h - roofH); p.lineTo(x + w * 1.08, base - h); p.closePath(); p.fill();
        if (rnd.next() < 0.4) { p.fillStyle = "#4A3A30"; p.fillRect(x + w * 0.7, base - h - roofH * 0.9, w * 0.12, roofH * 0.6); } }
      else { rnd.next(); rnd.next(); rnd.next(); }
      const n = 1 + Math.floor(rnd.next() * 2); for (let i = 0; i < n; i++) wins.push([x + w * (0.25 + 0.4 * i), base - h * 0.6, rnd.next()]);
    }
    if (!lit) {
      const kx = W * 0.62, ky = wallY(kx); p.fillStyle = "#6E6A62"; p.fillRect(kx, ky - H * 0.32, W * 0.03, H * 0.34); for (let i = 0; i < 4; i++) p.fillRect(kx + i * W * 0.008, ky - H * 0.35, W * 0.005, H * 0.03);   // (the keep)
      const sx = W * 0.34, sy = wallY(sx); p.fillStyle = "#8A8478"; p.fillRect(sx, sy - H * 0.26, W * 0.012, H * 0.26); p.fillStyle = "#4A4A54"; p.beginPath(); p.moveTo(sx - W * 0.002, sy - H * 0.26); p.lineTo(sx + W * 0.006, sy - H * 0.42); p.lineTo(sx + W * 0.014, sy - H * 0.26); p.closePath(); p.fill();   // (the temple's spire)
      p.fillStyle = "#6A665E"; p.beginPath(); p.moveTo(x0, wallY(x0)); for (let x = x0; x <= x1; x += 6) p.lineTo(x, wallY(x)); for (let x = x1; x >= x0; x -= 6) p.lineTo(x, wallY(x) + H * 0.07); p.closePath(); p.fill();   // (the ring wall)
      for (let x = x0; x < x1; x += W * 0.01) p.fillRect(x, wallY(x) - H * 0.02, W * 0.005, H * 0.025);
      for (const [wx, wy] of wins) { p.fillStyle = "#3A3028"; p.fillRect(wx, wy, W * 0.004, H * 0.025); }
    } else for (const [wx, wy, r] of wins) if (r < 0.75) { p.fillStyle = r < 0.4 ? "#FFD27A" : "#FFB850"; p.fillRect(wx, wy, W * 0.004, H * 0.025); }
    const out = []; for (let i = 0; i < FV.slices; i++) { const s = document.createElement("canvas"); s.width = s.height = size; s.getContext("2d").drawImage(c, i * size, 0, size, H, 0, 0, size, size); out.push(s); }
    return out;
  };
  // the Mage Tower as seen from far off: a dark column, its crown, a lit window high up (lit: only the window)
  const paintTower = (size, lit) => { const c = document.createElement("canvas"); c.width = c.height = size; const p = c.getContext("2d"), u = size / 64;
    if (!lit) { p.fillStyle = "#34323C"; p.fillRect(24 * u, 14 * u, 16 * u, 50 * u); p.fillStyle = "#2A2836"; p.beginPath(); p.moveTo(20 * u, 15 * u); p.lineTo(32 * u, 0); p.lineTo(44 * u, 15 * u); p.closePath(); p.fill();
      p.fillStyle = "#3E3C48"; for (let y = 22; y < 64; y += 8) p.fillRect(23 * u, y * u, 18 * u, 1.2 * u); p.fillStyle = "#1A1820"; p.fillRect(30 * u, 20 * u, 4 * u, 5 * u); }
    else { p.fillStyle = "#C8A8FF"; p.fillRect(30 * u, 20 * u, 4 * u, 5 * u); }
    return c; };
  { const build0 = CM.art.build; CM.art.build = function (theme, look) { const set = build0.call(this, theme, look), add = (n, c) => { set.index[n] = set.layers.length; set.layers.push(c); };
      paintTown(set.size, false).forEach((c, i) => add(`far:town${i}`, c)); paintTown(set.size, true).forEach((c, i) => add(`far:townlit${i}`, c));
      add("far:magetower", paintTower(set.size, false)); add("far:magetowerlit", paintTower(set.size, true)); return set; }; }
  // the quads: put(a, b, c, d, layer, shade, glow) - a and b at the foot, left to right as seen
  CM.farViews = (fl, size, index, night, put) => {
    if (fl.number === -1 && index["far:town0"] !== undefined) {   // from the land: the town on its hill, east
      const x = size + FV.townX, [z0, z1] = FV.townZ, step = (z1 - z0) / FV.slices;
      for (let i = 0; i < FV.slices; i++) { const za = z0 + i * step, zb = za + step;
        put([x, -0.5, za], [x, -0.5, zb], [x, FV.townH - 0.5, zb], [x, FV.townH - 0.5, za], index[`far:town${i}`], 0.8, 0);
        if (night > 0) put([x - 0.05, -0.5, za], [x - 0.05, -0.5, zb], [x - 0.05, FV.townH - 0.5, zb], [x - 0.05, FV.townH - 0.5, za], index[`far:townlit${i}`], 1, 2); }
      return 1;
    }
    if (fl.number === 0 && index["far:magetower"] !== undefined) {                                  // from the town: the Mage Tower over the Wood, north-west
      const [cx, cz] = FV.towerAt, r = FV.towerW / 2, H = FV.towerH;
      for (const [ax, az] of [[1, 0], [0, 1]]) { put([cx - ax * r, 0, cz - az * r], [cx + ax * r, 0, cz + az * r], [cx + ax * r, H, cz + az * r], [cx - ax * r, H, cz - az * r], index["far:magetower"], 0.85, 0);
        if (night > 0) put([cx - ax * r + 0.03, 0, cz - az * r + 0.03], [cx + ax * r + 0.03, 0, cz + az * r + 0.03], [cx + ax * r + 0.03, H, cz + az * r + 0.03], [cx - ax * r + 0.03, H, cz - az * r + 0.03], index["far:magetowerlit"], 1, 2); }
      return 1;
    }
    return 0;
  };
}
