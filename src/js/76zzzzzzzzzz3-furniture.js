"use strict";
// Town furniture with depth (v56.0, UPGRADE_PLAN_51.md): the market's stalls, carts, barrels and crates (solid since
// v24.5, 76zzzzh-models.js) are made the way they would be. A crate has its corner posts, its rims and a brace across
// each side, and now and then another crate on it. A barrel has four hoops and its lid set in the rim. A cart has
// spoked wheels - a rim, a hub and six spokes, turned the right way - and a load of sacks or hay. A stall has a scalloped
// edge hanging from its awning and real goods on the counter: apples, cabbages, bread, folded cloth, in baskets.
{ const P = 64;
  const PAINT = {
    apple: (p) => { p.fillStyle = "#B4302A"; p.fillRect(0, 0, P, P); p.fillStyle = "rgba(255,220,180,0.35)"; p.fillRect(8, 6, 14, 10); p.fillStyle = "rgba(90,20,10,0.4)"; p.fillRect(0, P * 0.7, P, P * 0.3); },
    cabbage: (p) => { p.fillStyle = "#6E9A44"; p.fillRect(0, 0, P, P); p.strokeStyle = "rgba(220,240,180,0.5)"; p.lineWidth = 2; for (let i = 0; i < 5; i++) { p.beginPath(); p.arc(P / 2, P, 12 + i * 10, Math.PI, 0); p.stroke(); } },
    bread: (p) => { p.fillStyle = "#C08A48"; p.fillRect(0, 0, P, P); p.fillStyle = "rgba(255,230,180,0.4)"; for (let i = 0; i < 3; i++) p.fillRect(8 + i * 18, 10, 10, P - 20); },
    cloth: (p) => { p.fillStyle = "#3E5A8A"; p.fillRect(0, 0, P, P); p.fillStyle = "rgba(240,220,150,0.55)"; for (let y = 6; y < P; y += 12) p.fillRect(0, y, P, 3); },
    sack: (p) => { p.fillStyle = "#B8A27A"; p.fillRect(0, 0, P, P); const r = new CM.Random(5); for (let i = 0; i < 120; i++) { p.fillStyle = r.next() < 0.5 ? "rgba(90,70,40,0.25)" : "rgba(240,225,190,0.2)"; p.fillRect(r.next() * P, r.next() * P, 3, 1); } },
    hay: (p) => { p.fillStyle = "#C9AE5A"; p.fillRect(0, 0, P, P); const r = new CM.Random(9); for (let i = 0; i < 160; i++) { p.strokeStyle = r.next() < 0.5 ? "rgba(120,96,30,0.5)" : "rgba(250,230,150,0.5)"; p.beginPath(); const x = r.next() * P, y = r.next() * P; p.moveTo(x, y); p.lineTo(x + (r.next() - 0.5) * 20, y + (r.next() - 0.5) * 8); p.stroke(); } },
  };
  { const b0 = CM.art.build; CM.art.build = function (theme, look) { const set = b0.call(this, theme, look); for (const [k, f] of Object.entries(PAINT)) { const n = `model:${k}`; if (set.index[n] !== undefined) continue; const c = document.createElement("canvas"); c.width = c.height = P; f(c.getContext("2d")); set.index[n] = set.layers.length; set.layers.push(c); } return set; }; }

  const pm0 = CM.propModel || (() => false);
  CM.FURNITURE_V56 = true;
  CM.propModel = (p, quad, index) => {
    if (!["barrel", "crate", "cart", "stall"].includes(p.id) || CM.furnitureOld) return pm0(p, quad, index);
    const K = CM.modelKit(p, quad, index); if (!K) return false; const { L, at, box, cyl } = K, w = p.w, h = p.h, r = new CM.Random(CM.hashSeed(`furn:${p.x},${p.y}:${p.id}`));
    const tri = (a, b, c, layer, sh) => quad(a, b, c, c, layer, sh);
    const lump = (x, y, z, s, layer, sh = 1) => box(x - s, y, z - s, x + s, y + s * 1.6, z + s, layer, layer, sh);   // (a round thing, near enough at this size)
    switch (p.id) {
      case "crate": { const one = (x0, y0, z0, a, H, k) => { box(x0 - a, y0, z0 - a, x0 + a, y0 + H, z0 + a, L("wood"), L("dark"), k);
          const t = a * 0.12, o = 0.006;   // (the corner posts, the rims at foot and top, a brace across each side)
          for (const [sx, sz] of [[-1, -1], [1, -1], [1, 1], [-1, 1]]) box(x0 + sx * a - (sx > 0 ? t : 0) - o * (sx < 0 ? 1 : 0), y0, z0 + sz * a - (sz > 0 ? t : 0) - o * (sz < 0 ? 1 : 0), x0 + sx * a + (sx < 0 ? t : 0) + o * (sx > 0 ? 1 : 0), y0 + H, z0 + sz * a + (sz < 0 ? t : 0) + o * (sz > 0 ? 1 : 0), L("dark"), L("dark"), k);
          for (const y of [y0, y0 + H - t]) { box(x0 - a - o, y, z0 - a - o, x0 + a + o, y + t, z0 - a + t * 0.5, L("dark"), L("dark"), k); box(x0 - a - o, y, z0 + a - t * 0.5, x0 + a + o, y + t, z0 + a + o, L("dark"), L("dark"), k); }
          for (const z of [z0 - a - o * 1.5, z0 + a + o * 1.5]) { const A = at(x0 - a + t, y0 + t, z), B = at(x0 - a + t * 2.2, y0 + t, z), C = at(x0 + a - t, y0 + H - t, z), D = at(x0 + a - t * 2.2, y0 + H - t, z); quad(A, B, C, D, L("dark"), 0.85 * k); } };
        const a = w / 2, H = Math.min(h, w * 1.05); one(0, 0, 0, a, H, 1);
        if (r.next() < 0.35) { const a2 = a * (0.7 + r.next() * 0.2); one((r.next() - 0.5) * a * 0.4, H, (r.next() - 0.5) * a * 0.4, a2, a2 * 1.9, 0.95); }   // (another on top)
        return true; }
      case "barrel": { const rr = w / 2 * 0.9, H = Math.min(h, w * 1.3), B = 0.12; cyl([0, 0, 0], rr, H, "y", 14, L("wood"), null, 1, B);
        for (const y of [0.08, 0.3, 0.7, 0.92]) cyl([0, H * y - H * 0.025, 0], rr * (1 + B * Math.sin(Math.PI * y)) + 0.005, H * 0.05, "y", 14, L("iron"), null, 0.9);
        cyl([0, H - 0.012, 0], rr * 0.93, 0.004, "y", 14, L("end"), L("end"), 0.95);   // (the lid, set a little into the rim)
        if (r.next() < 0.3) { const k = r.next() < 0.5 ? "apple" : "cabbage"; for (let i = 0; i < 5; i++) { const an = i * 1.3, d = rr * 0.45 * (i ? 1 : 0); lump(Math.cos(an) * d, H - 0.01, Math.sin(an) * d, 0.028, L(k), 1); } }   // (an open one, with something in it)
        return true; }
      case "cart": { const len = w, wid = w * 0.56, y0 = 0.22, y1 = 0.29, R = 0.18;
        box(-len / 2, y0, -wid / 2, len / 2, y1, wid / 2, L("dark"), L("wood"));
        for (const z of [-wid / 2, wid / 2 - 0.025]) box(-len / 2, y1, z, len / 2, y1 + 0.13, z + 0.025, L("wood"), L("dark"));
        box(-len / 2, y1, -wid / 2, -len / 2 + 0.025, y1 + 0.13, wid / 2, L("wood"), L("dark"));
        box(-0.03, R - 0.015, -wid / 2 - 0.06, 0.03, R + 0.015, wid / 2 + 0.06, L("dark"), L("dark"));   // (the axle)
        for (const zc of [-wid / 2 - 0.045, wid / 2 + 0.045]) {   // a wheel standing in the cart's side: a rim, a hub, six spokes
          const n = 16, t = 0.022, ring = (rad, k, z) => at(Math.cos(k) * rad, R + Math.sin(k) * rad, z);
          for (let i = 0; i < n; i++) { const k0 = (i / n) * Math.PI * 2, k1 = ((i + 1) / n) * Math.PI * 2;
            quad(ring(R, k0, zc - t), ring(R, k1, zc - t), ring(R, k1, zc + t), ring(R, k0, zc + t), L("iron"), 0.7 + 0.3 * Math.abs(Math.sin(k0)));
            for (const z of [zc - t, zc + t]) quad(ring(R, k0, z), ring(R, k1, z), ring(R - 0.03, k1, z), ring(R - 0.03, k0, z), L("dark"), 0.9); }
          for (let i = 0; i < 6; i++) { const k = (i / 6) * Math.PI * 2 + 0.3, s = 0.012, c = Math.cos(k), sn = Math.sin(k), px = -sn * s, py = c * s;
            for (const z of [zc - 0.006, zc + 0.006]) quad(at(c * 0.04 + px, R + sn * 0.04 + py, z), at(c * (R - 0.03) + px, R + sn * (R - 0.03) + py, z), at(c * (R - 0.03) - px, R + sn * (R - 0.03) - py, z), at(c * 0.04 - px, R + sn * 0.04 - py, z), L("wood"), 0.85); }
          cyl([0, R, zc - 0.03], 0.045, 0.06, "y", 8, L("dark"), L("end"), 0.9); }
        for (const z of [-wid / 2 + 0.04, wid / 2 - 0.07]) box(len / 2, 0.24, z, len / 2 + 0.4, 0.27, z + 0.03, L("dark"), L("dark"));   // (the shafts)
        const load = r.next();   // (what it carries)
        if (load < 0.45) for (let i = 0; i < 4; i++) { const x = -len / 2 + 0.12 + i * len * 0.22, z = (r.next() - 0.5) * wid * 0.4, s = 0.07 + r.next() * 0.02; box(x - s, y1, z - s * 0.8, x + s, y1 + s * 1.7, z + s * 0.8, L("sack"), L("sack"), 0.95); box(x - 0.015, y1 + s * 1.7, z - 0.015, x + 0.015, y1 + s * 1.95, z + 0.015, L("sack"), L("sack"), 0.8); }
        else if (load < 0.8) box(-len / 2 + 0.05, y1, -wid / 2 + 0.04, len / 2 - 0.05, y1 + 0.2 + r.next() * 0.08, wid / 2 - 0.04, L("hay"), L("hay"), 1.0);
        return true; }
      case "stall": { const W = w, D = w * 0.55, H = Math.max(0.75, h);
        box(-W / 2, 0, -D / 2 + 0.02, W / 2, 0.38, D / 2 * 0.2, L("wood"), L("dark"));
        for (const [x, z] of [[-W / 2, -D / 2], [W / 2 - 0.04, -D / 2], [-W / 2, D / 2 - 0.04], [W / 2 - 0.04, D / 2 - 0.04]]) box(x, 0, z, x + 0.04, z < 0 ? H : H * 0.8, z + 0.04, L("dark"), L("dark"));
        const fy = H * 0.8, fz = D / 2 + 0.1; quad(at(-W / 2 - 0.05, fy, fz), at(W / 2 + 0.05, fy, fz), at(W / 2 + 0.05, H, -D / 2), at(-W / 2 - 0.05, H, -D / 2), L("awning"), 1.0);
        const nS = 8; for (let i = 0; i < nS; i++) { const x0 = -W / 2 - 0.05 + ((W + 0.1) * i) / nS, x1 = x0 + (W + 0.1) / nS;   // (the awning's scalloped edge)
          quad(at(x0, fy, fz), at(x1, fy, fz), at(x1, fy - 0.05, fz), at(x0, fy - 0.05, fz), L("awning"), 0.9); tri(at(x0, fy - 0.05, fz), at(x1, fy - 0.05, fz), at((x0 + x1) / 2, fy - 0.09, fz), L("awning"), 0.85); }
        box(-W / 2 + 0.03, 0.38, -D / 2 + 0.04, W / 2 - 0.03, 0.66, -D / 2 + 0.07, L("dark"), L("dark"), 0.9);   // (a back board with a shelf)
        box(-W / 2 + 0.03, 0.58, -D / 2 + 0.07, W / 2 - 0.03, 0.6, -D / 2 + 0.16, L("wood"), L("wood"), 1);
        const goods = ["apple", "cabbage", "bread", "cloth"]; const g1 = goods[Math.floor(r.next() * 4)], g2 = goods[Math.floor(r.next() * 4)];
        for (let i = 0; i < 3; i++) { const x = -W / 2 + 0.15 + i * (W - 0.3) / 2, z = -0.02, g = i === 1 ? g2 : g1;   // (baskets on the counter, heaped)
          cyl([x, 0.38, z], 0.08, 0.05, "y", 10, L("wood"), null, 0.85);
          if (g === "cloth") for (let j = 0; j < 3; j++) box(x - 0.07, 0.4 + j * 0.022, z - 0.05, x + 0.07, 0.42 + j * 0.022, z + 0.05, L("cloth"), L("cloth"), 1 - j * 0.05);
          else for (let j = 0; j < 7; j++) { const an = j * 2.4, d = j ? 0.045 : 0; lump(x + Math.cos(an) * d, 0.42 + (j ? 0 : 0.02), z + Math.sin(an) * d, g === "cabbage" ? 0.03 : 0.022, L(g), 1); } }
        for (let i = 0; i < 4; i++) lump(-W / 2 + 0.12 + i * 0.1, 0.6, -D / 2 + 0.12, 0.02, L(g2 === "cloth" ? "bread" : g2), 0.95);   // (more on the shelf)
        return true; }
    }
    return pm0(p, quad, index);
  };
}
