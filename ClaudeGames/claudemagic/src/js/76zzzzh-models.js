"use strict";
// Real 3-D props (v24.5, UPGRADE_PLAN_19.md): barrels, crates, carts, market stalls, logs and stumps are built as
// small solid models in the floor's mesh - boxes and many-sided cylinders - instead of pictures turned to the eye.
// They stand in the light like the walls (the torch, the lamps, the sun and the relief all fall on them) and look the
// same from every side. Their wood, iron, bark and awning are painted here once a set. 26-surface.js asks for the
// geometry (CM.propModel); the props come out of the scatter marked how: "model" (so they are not billboards).
{ const MODELS = CM.PROP_MODELS = { barrel: true, crate: true, cart: true, stall: true, log: true, stump: true };
  const sc0 = CM.scatter;
  CM.scatter = function (fl, seed, density, ctx = {}) { const out = sc0.call(this, fl, seed, density, ctx); if (CM.modelsOff) return out; for (const p of out) if (p.how === "stand" && MODELS[p.id]) p.how = "model"; return out; };
  // the pictures: boards, an end's rings, iron, bark, a striped awning
  const paint = (size, kind) => {
    const c = document.createElement("canvas"); c.width = c.height = size; const p = c.getContext("2d"), rnd = new CM.Random(CM.hashSeed(`model:${kind}`)), S = size;
    if (kind === "wood" || kind === "dark") { p.fillStyle = kind === "wood" ? "#8A6438" : "#5E4426"; p.fillRect(0, 0, S, S);
      for (let i = 0; i < 260; i++) { p.fillStyle = `rgba(${rnd.next() < 0.5 ? "40,26,12" : "190,150,100"},${0.08 + rnd.next() * 0.1})`; p.fillRect(rnd.next() * S, rnd.next() * S, 1 + rnd.next() * 2, S * (0.1 + rnd.next() * 0.3)); }
      p.fillStyle = "rgba(30,18,8,0.75)"; for (let x = 0; x < S; x += S / 4) p.fillRect(x, 0, Math.max(1, S / 96), S);
      p.fillStyle = "rgba(30,18,8,0.5)"; for (let i = 0; i < 6; i++) { p.beginPath(); p.arc(rnd.next() * S, rnd.next() * S, S / 80, 0, Math.PI * 2); p.fill(); } }
    else if (kind === "end") { p.fillStyle = "#A07A48"; p.fillRect(0, 0, S, S); p.strokeStyle = "rgba(70,44,20,0.55)"; for (let r = S * 0.05; r < S * 0.5; r += S * (0.03 + rnd.next() * 0.02)) { p.lineWidth = Math.max(1, S / 160); p.beginPath(); p.arc(S / 2, S / 2, r, 0, Math.PI * 2); p.stroke(); } }
    else if (kind === "iron") { p.fillStyle = "#3A3A3E"; p.fillRect(0, 0, S, S); for (let i = 0; i < 200; i++) { p.fillStyle = `rgba(${rnd.next() < 0.5 ? "20,20,24" : "110,96,80"},0.25)`; p.fillRect(rnd.next() * S, rnd.next() * S, 3, 3); } }
    else if (kind === "bark") { p.fillStyle = "#4E3A28"; p.fillRect(0, 0, S, S); for (let i = 0; i < 140; i++) { p.fillStyle = `rgba(${rnd.next() < 0.5 ? "24,16,10" : "120,100,76"},0.35)`; p.fillRect(rnd.next() * S, rnd.next() * S, 2 + rnd.next() * 4, S * (0.15 + rnd.next() * 0.4)); } }
    else if (kind === "awning") { for (let i = 0; i < 8; i++) { p.fillStyle = i % 2 ? "#E8DCC0" : "#B83A2E"; p.fillRect((i * S) / 8, 0, S / 8, S); } p.fillStyle = "rgba(0,0,0,0.12)"; p.fillRect(0, S * 0.85, S, S * 0.15); }
    return c;
  };
  { const build0 = CM.art.build; CM.art.build = function (theme, look) { const set = build0.call(this, theme, look); for (const k of ["wood", "dark", "end", "iron", "bark", "awning"]) { set.index[`model:${k}`] = set.layers.length; set.layers.push(paint(set.size, k)); } return set; }; }
  // the geometry: quad(a, b, c, d, layer, shade, uvRect) - a, b at the foot
  CM.propModel = (p, quad, index) => {
    const L = (k) => index[`model:${k}`], cx = p.x + 0.5 + p.dx, cz = p.y + 0.5 + p.dz, c = Math.cos(p.turn), s = Math.sin(p.turn);
    if (L("wood") === undefined) return false;
    const at = (x, y, z) => [cx + x * c - z * s, y, cz + x * s + z * c];
    const box = (x0, y0, z0, x1, y1, z1, side, top, sh = 1) => {                   // an upright box in the prop's own frame
      const P = (x, y, z) => at(x, y, z);
      quad(P(x0, y0, z1), P(x1, y0, z1), P(x1, y1, z1), P(x0, y1, z1), side, 0.92 * sh); quad(P(x1, y0, z0), P(x0, y0, z0), P(x0, y1, z0), P(x1, y1, z0), side, 0.8 * sh);
      quad(P(x1, y0, z1), P(x1, y0, z0), P(x1, y1, z0), P(x1, y1, z1), side, 0.86 * sh); quad(P(x0, y0, z0), P(x0, y0, z1), P(x0, y1, z1), P(x0, y1, z0), side, 0.74 * sh);
      if (top !== null) quad(P(x0, y1, z1), P(x1, y1, z1), P(x1, y1, z0), P(x0, y1, z0), top, 1.0 * sh);
    };
    const cyl = (o, r, len, axis, n, side, cap, sh = 1, bulge = 0) => {           // a cylinder: axis "y" upright from o, or "x" lying along the frame's x from o
      const ring = (t, k) => { const rr = r * (1 + bulge * Math.sin(Math.PI * t)); return axis === "y" ? [o[0] + Math.cos(k) * rr, o[1] + t * len, o[2] + Math.sin(k) * rr] : [o[0] + t * len, o[1] + Math.cos(k) * rr, o[2] + Math.sin(k) * rr]; };
      const seg = bulge ? 3 : 1;
      for (let j = 0; j < seg; j++) for (let i = 0; i < n; i++) { const k0 = (i / n) * Math.PI * 2, k1 = ((i + 1) / n) * Math.PI * 2, t0 = j / seg, t1 = (j + 1) / seg;
        quad(at(...ring(t0, k0)), at(...ring(t0, k1)), at(...ring(t1, k1)), at(...ring(t1, k0)), side, sh * (0.78 + 0.22 * Math.cos(k0 - 0.8)), [i / n, 1 - t1, (i + 1) / n, 1 - t0]); }
      if (cap !== null) for (const t of axis === "y" ? [1] : [0, 1]) for (let i = 0; i < n; i += 2) { const k0 = (i / n) * Math.PI * 2, k1 = ((i + 1) / n) * Math.PI * 2, k2 = ((i + 2) / n) * Math.PI * 2, C = axis === "y" ? [o[0], o[1] + t * len, o[2]] : [o[0] + t * len, o[1], o[2]];
        quad(at(...C), at(...ring(t, k0)), at(...ring(t, k1)), at(...ring(t, k2)), cap, sh * 0.95, [0.32, 0.32, 0.68, 0.68]); }
    };
    const w = p.w, h = p.h;
    switch (p.id) {
      case "barrel": { const r = w / 2, H = Math.min(h, w * 1.3); cyl([0, 0, 0], r * 0.9, H, "y", 12, L("wood"), L("end"), 1, 0.12);
        for (const y of [0.18, 0.78]) cyl([0, H * y, 0], r * 0.9 * (1 + 0.12 * Math.sin(Math.PI * y)) + 0.004, H * 0.06, "y", 12, L("iron"), null, 0.9); return true; }
      case "crate": { const a = w / 2; box(-a, 0, -a, a, Math.min(h, w * 1.05), a, L("wood"), L("dark")); return true; }
      case "cart": { const len = w, wid = w * 0.56, y0 = 0.2, y1 = 0.27;
        box(-len / 2, y0, -wid / 2, len / 2, y1, wid / 2, L("dark"), L("wood"));                                         // (the bed)
        box(-len / 2, y1, -wid / 2, len / 2, y1 + 0.12, -wid / 2 + 0.025, L("wood"), L("dark")); box(-len / 2, y1, wid / 2 - 0.025, len / 2, y1 + 0.12, wid / 2, L("wood"), L("dark"));   // (its sides)
        box(-len / 2, y1, -wid / 2, -len / 2 + 0.025, y1 + 0.12, wid / 2, L("wood"), L("dark"));
        for (const z of [-wid / 2 - 0.035, wid / 2 + 0.005]) { const R = 0.17; cyl([-0.02, R, z], R, 0.03, "x", 14, L("dark"), L("end"), 0.9); }   // (the wheels: discs on the axle)
        box(len / 2, 0.22, -wid / 2 + 0.04, len / 2 + 0.35, 0.25, -wid / 2 + 0.07, L("dark"), L("dark")); box(len / 2, 0.22, wid / 2 - 0.07, len / 2 + 0.35, 0.25, wid / 2 - 0.04, L("dark"), L("dark"));   // (the shafts)
        return true; }
      case "stall": { const W = w, D = w * 0.55, H = Math.max(0.75, h);
        box(-W / 2, 0, -D / 2 + 0.02, W / 2, 0.38, D / 2 * 0.2, L("wood"), L("dark"));                                    // (the counter)
        for (const [x, z] of [[-W / 2, -D / 2], [W / 2 - 0.04, -D / 2], [-W / 2, D / 2 - 0.04], [W / 2 - 0.04, D / 2 - 0.04]]) box(x, 0, z, x + 0.04, z < 0 ? H : H * 0.8, z + 0.04, L("dark"), L("dark"));   // (the posts)
        const A = (x, y, z) => at(x, y, z); quad(A(-W / 2 - 0.05, H * 0.8, D / 2 + 0.1), A(W / 2 + 0.05, H * 0.8, D / 2 + 0.1), A(W / 2 + 0.05, H, -D / 2), A(-W / 2 - 0.05, H, -D / 2), L("awning"), 1.0);   // (the awning)
        for (let i = 0; i < 4; i++) box(-W / 2 + 0.08 + i * W * 0.22, 0.38, -0.05, -W / 2 + 0.2 + i * W * 0.22, 0.44, 0.06, L(i % 2 ? "end" : "wood"), L(i % 2 ? "end" : "awning"), 1);   // (goods on the counter)
        return true; }
      case "log": { const r = Math.min(h, w * 0.4) / 2; cyl([-w / 2, r, 0], r, w, "x", 10, L("bark"), L("end")); return true; }
      case "stump": { const r = w * 0.42, H = Math.min(h, w * 0.75); cyl([0, 0, 0], r, H, "y", 10, L("bark"), L("end")); return true; }
      default: return false;
    }
  };
}
