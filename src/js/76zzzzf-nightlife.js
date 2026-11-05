"use strict";
// Day and night life (v24.3, UPGRADE_PLAN_19.md): the town keeps hours. Its windows light at dusk and go dark one by
// one at bedtime, a few coming back before dawn for the early risers (26-surface.js, opts.night as a share). A
// lamplighter walks the streets from seven, lighting the lamps one after another with the flame on his pole, and puts
// them out again at dawn. Moths gather about the lit lamps, bats flit over the roofs and the trees at dusk, and in the
// Wood at night an owl calls and passes over. The clock is the game's: a step is a minute, so the lamps come on as the
// party walks the evening.
{ const LH = CM.LAMPLIGHT = { from: 19, to: 21, snuffFrom: 5, snuffTo: 6, walkMs: 2600 };
  // how many of the town's windows are lit, by the hour
  CM.litShare = (game) => {
    const h = CM.hourOf(game), q = (v) => Math.round(v * 20) / 20;
    if (h >= 18.5 && h < 20) return q(0.3 + 0.55 * (h - 18.5) / 1.5);
    if (h >= 20 && h < 22) return 0.85;
    if (h >= 22) return q(0.85 - 0.6 * (h - 22) / 2);
    if (h < 4) return q(0.25 - 0.12 * h / 4);
    if (h < 5.5) return q(0.13 + 0.25 * (h - 4) / 1.5);
    if (h < 6.5) return q(0.38 * (6.5 - h));
    return 0;
  };
  // the lamps in the lamplighter's order: from the one nearest the Square, each time the nearest not yet lit
  let order = null, orderOf = null;
  const lampsOf = (renderer) => {
    if (orderOf === renderer.standing) return order;
    orderOf = renderer.standing; const lamps = renderer.standing.filter((p) => p.id === "lamp"), out = [];
    let at = CM.TOWN_AT ? CM.TOWN_AT.market : [22, 18];
    while (lamps.length) { let bi = 0, bd = Infinity; lamps.forEach((p, i) => { const d = Math.abs(p.x - at[0]) + Math.abs(p.y - at[1]); if (d < bd) { bd = d; bi = i; } }); const p = lamps.splice(bi, 1)[0]; out.push(p); at = [p.x, p.y]; }
    return (order = out);
  };
  // how far along his round he is: 0..1 lighting at dusk, and -1..0 snuffing at dawn (null: not abroad)
  const round = (game) => { const h = CM.hourOf(game); if (h >= LH.from && h < LH.to) return (h - LH.from) / (LH.to - LH.from); if (h >= LH.snuffFrom && h < LH.snuffTo) return -(h - LH.snuffFrom) / (LH.snuffTo - LH.snuffFrom); return null; };
  CM.lampOn = (game, p) => {
    const h = CM.hourOf(game); if (game.floor && game.floor.number !== 0) return CM.isNight(game);
    const r = round(game), L = CM.renderer ? lampsOf(CM.renderer) : [], i = L.indexOf(p), n = Math.max(1, L.length);
    if (r === null) return h >= LH.to || h < LH.snuffFrom;
    if (i < 0) return r < 0;
    return r >= 0 ? i < Math.floor(r * n) : i >= Math.floor(-r * n);   // (at dawn he puts them out in the same order)
  };
  // where he walks: along the streets from one lamp to the next (a short search on the open squares)
  const path = (fl, a, b) => {
    const size = fl.grid.length, key = (x, y) => y * size + x, prev = new Map([[key(a[0], a[1]), -1]]), q = [a];
    while (q.length) { const [x, y] = q.shift(); if (x === b[0] && y === b[1]) break;
      for (const [dx, dy] of CM.DIRS) { const nx = x + dx, ny = y + dy; if (nx < 0 || ny < 0 || nx >= size || ny >= size || fl.grid[ny][nx] !== 0 || prev.has(key(nx, ny))) continue; prev.set(key(nx, ny), key(x, y)); q.push([nx, ny]); } }
    if (!prev.has(key(b[0], b[1]))) return [a, b];
    const out = []; for (let k = key(b[0], b[1]); k !== -1; k = prev.get(k)) out.push([k % size, Math.floor(k / size)]); return out.reverse();
  };
  let walk = null;
  CM.lampsLit = [];
  CM.lifeSprites = (game, fl, now) => {
    CM.lampsLit = fl && fl.number === 0 && CM.renderer ? lampsOf(CM.renderer).filter((p) => CM.lampOn(game, p)).map((p) => [p.x + 0.5 + p.dx, p.y + 0.5 + p.dz]) : [];   // (for the moths)
    if (!fl || fl.number !== 0 || !CM.renderer) return [];
    const r = round(game); if (r === null) { walk = null; return []; }
    const L = lampsOf(CM.renderer); if (!L.length) return [];
    const i = Math.min(L.length - 1, Math.floor(Math.abs(r) * L.length)), lamp = L[i];
    if (!walk || walk.i !== i) { const from = walk ? walk.to : [lamp.x, lamp.y]; walk = { i, to: [lamp.x, lamp.y], path: path(fl, from, [lamp.x, lamp.y]), t0: now }; }
    const k = Math.min(1, (now - walk.t0) / LH.walkMs), P = walk.path, f = k * (P.length - 1), j = Math.min(P.length - 2, Math.floor(f)), u = P.length > 1 ? f - j : 0;
    const a = P[Math.max(0, j)], b = P[Math.min(P.length - 1, j + 1)], x = a[0] + (b[0] - a[0]) * u, y = a[1] + (b[1] - a[1]) * u, cx = Math.floor(x), cy = Math.floor(y);
    const there = k >= 1, bob = there ? 0 : Math.abs(Math.sin(now / 160)) * 0.02;
    return [{ id: "lamplighter", x: cx, y: cy, dx: x - cx + (there ? 0.28 : 0), dz: y - cy + (there ? 0.18 : 0), layer: "npc:lamplighter", w: 0.6, h: 0.95, lift: bob, glow: 0.15 }];
  };
  // his picture: a long coat and a cap, the pole with its small flame
  CM.art.lamplighter = function (size) { const c = document.createElement("canvas"); c.width = c.height = size; const p = c.getContext("2d"), u = size / 64, R = (x, y, w, h, col) => { p.fillStyle = col; p.fillRect(x * u, y * u, w * u, h * u); };
    R(26, 48, 5, 14, "#2A2420"); R(33, 48, 5, 14, "#2A2420"); R(25, 61, 7, 3, "#151010"); R(32, 61, 7, 3, "#151010");                // (legs, boots)
    R(22, 26, 20, 26, "#3A4A5A"); R(22, 46, 20, 6, "#2E3C4A"); R(31, 26, 2, 24, "#283440");                                       // (the long coat)
    R(17, 28, 5, 14, "#3A4A5A"); R(42, 26, 5, 12, "#3A4A5A"); R(17, 41, 5, 3, "#E0B890"); R(43, 24, 5, 3, "#E0B890");             // (arms; the right one raised to the pole)
    p.fillStyle = "#E0B890"; p.beginPath(); p.arc(32 * u, 19 * u, 6.5 * u, 0, Math.PI * 2); p.fill(); R(29, 18, 2, 2, "#2A1A10"); R(34, 18, 2, 2, "#2A1A10");
    R(24, 10, 16, 5, "#22262C"); R(22, 14, 20, 2, "#22262C");                                                                    // (the cap)
    R(46, 2, 2, 52, "#6A5030"); R(44, 1, 6, 3, "#4A4A50");                                                                       // (the pole and its hook)
    const g = p.createRadialGradient(47 * u, 2 * u, 0, 47 * u, 2 * u, 5 * u); g.addColorStop(0, "#FFF0B0"); g.addColorStop(0.5, "#FFB040"); g.addColorStop(1, "rgba(255,140,40,0)"); p.fillStyle = g; p.fillRect(40 * u, 0, 14 * u, 8 * u);
    return c; };
  { const build0 = CM.art.build; CM.art.build = function (theme, look) { const set = build0.call(this, theme, look); set.index["npc:lamplighter"] = set.layers.length; set.layers.push(CM.art.lamplighter(set.size)); return set; }; }
  { const s0 = CM.art.isSurfaceLayer; CM.art.isSurfaceLayer = (name) => name === "npc:lamplighter" || s0(name); }
  // the night's creatures: moths about the lit lamps, bats at dusk, an owl in the Wood
  CM.art.AIR = CM.art.AIR || []; for (const id of ["moth", "bat", "owl"]) if (!CM.art.AIR.includes(id)) CM.art.AIR.push(id);
  { const ap0 = CM.art.airPicture; CM.art.airPicture = function (id) {
      if (!["moth", "bat", "owl"].includes(id)) return ap0.call(this, id);
      const S = 64, c = document.createElement("canvas"); c.width = c.height = S; const p = c.getContext("2d");
      if (id === "moth") { p.fillStyle = "#EDE4C8"; p.beginPath(); p.ellipse(S * 0.32, S * 0.45, S * 0.2, S * 0.14, -0.5, 0, Math.PI * 2); p.ellipse(S * 0.68, S * 0.45, S * 0.2, S * 0.14, 0.5, 0, Math.PI * 2); p.fill(); p.fillStyle = "#8A7A60"; p.fillRect(S * 0.47, S * 0.35, S * 0.06, S * 0.3); }
      else { p.fillStyle = id === "bat" ? "#1A1418" : "#3A3028"; p.beginPath(); p.moveTo(S * 0.5, S * 0.42); p.quadraticCurveTo(S * 0.3, S * 0.2, S * 0.04, S * 0.38); p.lineTo(S * 0.2, S * 0.5); p.lineTo(S * 0.3, S * 0.46); p.lineTo(S * 0.4, S * 0.58);
        p.lineTo(S * 0.5, S * 0.52); p.lineTo(S * 0.6, S * 0.58); p.lineTo(S * 0.7, S * 0.46); p.lineTo(S * 0.8, S * 0.5); p.lineTo(S * 0.96, S * 0.38); p.quadraticCurveTo(S * 0.7, S * 0.2, S * 0.5, S * 0.42); p.fill();
        if (id === "owl") { p.beginPath(); p.arc(S * 0.5, S * 0.42, S * 0.08, 0, Math.PI * 2); p.fill(); } }
      return c; }; }
  { const k0 = CM.airKinds; CM.airKinds = function (env) { const out = k0.call(this, env); if (!env.surface) return out; const h = env.hour === undefined ? 12 : env.hour, rain = env.weather === "rain";
      if (env.night && !rain && env.season !== "winter" && CM.lampsLit && CM.lampsLit.length) out.push({ id: "moth", rate: 6 });
      if (h >= 19 && h < 22 && !rain && env.season !== "winter") out.push({ id: "bat", rate: 0.5 });
      if (env.night && !env.town && !rain) out.push({ id: "owl", rate: 0.03 });
      return out; }; }
  { const sp0 = CM.Air.prototype.spawn; CM.Air.prototype.spawn = function (k, eye, R, env) {
      const r = Math.random, base = { kind: k.id, age: 0, seed: r() * 10, sway: 0.6 + r(), swayAmp: 0, windy: 0, vx: 0, vy: 0, vz: 0, life: 6, size: 0.04, glow: 0, alpha: 1, layer: `air:${k.id}` };
      if (k.id === "moth") { const near = (CM.lampsLit || []).filter((l) => Math.abs(l[0] - eye[0]) + Math.abs(l[1] - eye[2]) < 9); if (!near.length) return null; const l = near[Math.floor(r() * near.length)];
        return Object.assign(base, { x: l[0] + (r() - 0.5) * 0.5, z: l[1] + (r() - 0.5) * 0.5, y: 1.0 + r() * 0.5, vy: (r() - 0.5) * 0.1, swayAmp: 1.6, sway: 4 + r() * 4, life: 2 + r() * 3, size: 0.035, glow: 0.9, top: 2.2 }); }
      if (k.id === "bat") { const a = r() * Math.PI * 2, s = 2.2 + r(); return Object.assign(base, { x: eye[0] + (r() - 0.5) * 10, z: eye[2] + (r() - 0.5) * 10, y: 2.0 + r() * 2.0, vx: Math.cos(a) * s, vz: Math.sin(a) * s, swayAmp: 2.2, sway: 5, life: 5, size: 0.2, flap: true, top: 6 }); }
      if (k.id === "owl") { const a = r() * Math.PI * 2, d = 10 + r() * 6, s = 1.6; if (CM.owlHoot) CM.owlHoot(); return Object.assign(base, { x: eye[0] + Math.cos(a) * d, z: eye[2] + Math.sin(a) * d, y: 3.5 + r() * 2, vx: -Math.sin(a) * s, vz: Math.cos(a) * s, life: 14, size: 0.55, far: true, top: 12, flap: true }); }
      return sp0.call(this, k, eye, R, env); }; }
  // the owl's call: two soft notes, then one, made once
  CM.owlHoot = () => { const A = CM.audio; if (!A || !A.ctx || !A.enabled) return; if (!A.buffers.owl) { const hoo = (len) => A._sweep(410, 360, len, "sine", 0.1, 0.06); A.buffers.owl = A._buffer(A._mix(hoo(0.32), A._after(0.55, hoo(0.18)), A._after(0.8, hoo(0.5)))); } A.play("owl", 0.5, (Math.random() - 0.5) * 1.2); };
}
