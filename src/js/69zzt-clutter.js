"use strict";
// The clutter below ground (UPGRADE_PLAN_63.md set 4, release 1): stalagmites on the floor and stalactites from the
// ceiling - cones made here in code in the plants' own model shape, three sizes each, the stone's greys (the Crystal
// Caverns tint them) - placed by hash at the walls' feet and in the corners, never in the middle of a corridor one
// square wide; wall decals by band - drainage ports and barred grates at the walls' feet in the damp bands, pipe
// mouths that drip in the Foundry and the damp bands, spiderwebs in the corners, most in the Catacombs and the bone
// halls; and the rats' places - a few corridor squares a floor where a rat sits and scurries off when the party comes
// (the window's). All of it a sight: nothing is solid, nothing is on a thing, a feature or the stairs.
//   CM.clutterModels() -> { name: model }                           the cones, in CM.Plants' model shape
//   CM.clutterOf(game, fl, at, reach, density) -> instances         merged by CM.plantInstancesOf (69zzs-plants.js)
//   CM.clutterDecals(fl, at, reach) -> [{ x, y, face, kind, lift, w, h }]   kind: port | grate | pipe | web
//   CM.clutterRats(fl) -> [{ x, y, id }]                             the rats' home squares
{ const C = CM.CLUTTER = { stal: { 0: 0.28, 1: 0.2, 3: 0.12, 4: 0.22, 5: 0.16, 6: 0.34, 8: 0.2, 9: 0.18 }, decals: { 0: ["grate", "port", "web", "web"], 1: ["port", "pipe", "grate", "pipe"], 2: ["pipe"], 4: ["port", "grate"], 5: ["web"], 7: ["pipe", "pipe", "grate"], 8: ["web", "web", "web"], 9: ["web"] },
    decalPer: 0.1, webPer: 0.22, ratsPerFloor: 3, crystal: [0.75, 0.85, 1.0], stone: [0.62, 0.6, 0.58] };
  // a cone of n sides, h tall, r wide at the foot, pointing up (or down, foot at 0, tip at -h): pos int16 over the box, a colour index a vertex
  const cone = (name, h, r, n, down) => { const pos = [], ci = [], idx = []; const tip = down ? -h : h; pos.push([0, 0, 0]); ci.push(0);   // the foot's centre
    for (let i = 0; i < n; i++) { const a = i / n * Math.PI * 2, rr = r * (0.85 + 0.15 * Math.sin(i * 2.3)); pos.push([Math.cos(a) * rr, 0, Math.sin(a) * rr]); ci.push(i % 2 ? 1 : 2); }
    pos.push([0, tip, 0]); ci.push(3); const T = n + 1;
    for (let i = 0; i < n; i++) { const a = 1 + i, b = 1 + (i + 1) % n; idx.push(0, down ? a : b, down ? b : a); idx.push(a, b, T); if (down) { const last = idx.length - 3; const t = idx[last + 1]; idx[last + 1] = idx[last + 2]; idx[last + 2] = t; } }
    const lo = [Math.min(...pos.map((p) => p[0])), Math.min(...pos.map((p) => p[1])), Math.min(...pos.map((p) => p[2]))], hi = [Math.max(...pos.map((p) => p[0])), Math.max(...pos.map((p) => p[1])), Math.max(...pos.map((p) => p[2]))], span = lo.map((l, k) => Math.max(1e-6, hi[k] - l));
    const P = new Int16Array(pos.length * 3); pos.forEach((p, i) => { for (let k = 0; k < 3; k++) P[i * 3 + k] = Math.round((p[k] - lo[k]) / span[k] * 65534 - 32767); });
    return { name, verts: pos.length, tris: idx.length / 3, box: [lo, hi], pos: P, ci: Uint8Array.from(ci), index: Uint16Array.from(idx), palette: [[150, 146, 140], [128, 124, 118], [162, 158, 150], [176, 172, 166]], tags: ["stone"] }; };
  let made = null;
  CM.clutterModels = () => made || (made = { stalagmite_s: cone("stalagmite_s", 0.3, 0.09, 8, false), stalagmite_m: cone("stalagmite_m", 0.55, 0.14, 8, false), stalagmite_l: cone("stalagmite_l", 0.85, 0.2, 10, false), stalactite_s: cone("stalactite_s", 0.3, 0.08, 8, true), stalactite_m: cone("stalactite_m", 0.5, 0.12, 8, true), stalactite_l: cone("stalactite_l", 0.8, 0.17, 10, true) });
  const h = (fl, salt, k) => CM.hashSeed(`${fl.number}:${salt}:${k}`) >>> 0;
  const okFloor = (fl) => fl && fl.number >= 1 && fl.grid && !["joker", "interior", "cave"].includes(fl.special);
  CM.clutterOf = (game, fl, at, reach, density = 1) => { const out = []; if (!okFloor(fl) || !reach) return out; const per = C.stal[CM.themeIndex(fl.number)]; if (!per) return out; const M = CM.clutterModels(), N = fl.grid.length, R = Math.min(reach, 12) + 1, [ax, ay] = at || fl.pos;
    const open = (x, y) => x >= 0 && y >= 0 && x < N && y < N && fl.grid[y][x] === 0;
    for (let y = Math.max(1, ay - R); y <= Math.min(N - 2, ay + R); y++) for (let x = Math.max(1, ax - R); x <= Math.min(N - 2, ax + R); x++) { if (!open(x, y) || Math.abs(x - ax) + Math.abs(y - ay) > R) continue; const k = `${x},${y}`; if (fl.things[k] || (fl.features || {})[k]) continue;
      const W = CM.DIRS.filter(([dx, dy]) => !open(x + dx, y + dy)); if (!W.length) continue; const narrow = (!open(x - 1, y) && !open(x + 1, y)) || (!open(x, y - 1) && !open(x, y + 1)), roll = (n) => (CM.hashSeed(`${fl.number}:c${n}:${k}`) >>> 0) % 1000 / 1000;
      if (roll(1) < per * density * (W.length >= 2 ? 1.6 : 1)) { const w = W[h(fl, "w", k) % W.length], size = ["s", "s", "m", "m", "l"][h(fl, "sz", k) % 5], m = M[`stalagmite_${size}`], f = CM.floorAt(fl, x, y);
        const dx = 0.5 + w[0] * (narrow ? 0.36 : 0.3) + (roll(2) - 0.5) * 0.14, dz = 0.5 + w[1] * (narrow ? 0.36 : 0.3) + (roll(3) - 0.5) * 0.14, sc = 0.85 + roll(4) * 0.3;
        out.push({ model: m.name, x: x + dx, y: f, z: y + dz, yaw: roll(5) * Math.PI * 2, scale: sc, sway: 0, height: m.box[1][1] * sc, shade: 1, kind: "stone", small: true, raw: true }); }
      if (roll(6) < per * density * 0.9) { const size = ["s", "m", "m", "l"][h(fl, "tz", k) % 4], m = M[`stalactite_${size}`], c = CM.ceilAt(fl, x, y), sc = 0.8 + roll(7) * 0.35;
        out.push({ model: m.name, x: x + 0.2 + roll(8) * 0.6, y: c - 0.005, z: y + 0.2 + roll(9) * 0.6, yaw: roll(10) * Math.PI * 2, scale: sc, sway: 0, height: 0.3, shade: 0.85, kind: "stone", small: true, raw: true }); } }
    return out; };
  CM.clutterDecals = (fl, at, reach = 10) => { const out = []; if (!okFloor(fl)) return out; const kinds = C.decals[CM.themeIndex(fl.number)]; if (!kinds) return out; const N = fl.grid.length, [ax, ay] = at || fl.pos, open = (x, y) => x >= 0 && y >= 0 && x < N && y < N && fl.grid[y][x] === 0;
    for (let y = Math.max(0, ay - reach); y <= Math.min(N - 1, ay + reach); y++) for (let x = Math.max(0, ax - reach); x <= Math.min(N - 1, ax + reach); x++) { if (!open(x, y) || Math.abs(x - ax) + Math.abs(y - ay) > reach) continue; const k = `${x},${y}`; if (fl.things[k]) continue;
      for (let f = 0; f < 4; f++) { const [dx, dy] = CM.DIRS[f]; if (open(x + dx, y + dy)) continue; const r = (CM.hashSeed(`${fl.number}:d${f}:${k}`) >>> 0) % 1000 / 1000, kind = kinds[(h(fl, "dk", k) + f) % kinds.length];
        const corner = !open(x + CM.DIRS[(f + 1) % 4][0], y + CM.DIRS[(f + 1) % 4][1]) || !open(x + CM.DIRS[(f + 3) % 4][0], y + CM.DIRS[(f + 3) % 4][1]);
        if (kind === "web") { if (corner && r < C.webPer) out.push({ x, y, face: f, kind, lift: 0.3, w: 0.42, h: 0.4, along: !open(x + CM.DIRS[(f + 1) % 4][0], y + CM.DIRS[(f + 1) % 4][1]) ? 1 : -1 }); }
        else if (r < C.decalPer) out.push({ x, y, face: f, kind, lift: kind === "pipe" ? -0.2 : -0.33, w: kind === "grate" ? 0.36 : 0.26, h: kind === "grate" ? 0.2 : 0.26 }); } }
    return out; };
  CM.clutterRats = (fl) => { const out = []; if (!okFloor(fl)) return out; const N = fl.grid.length, open = (x, y) => x >= 0 && y >= 0 && x < N && y < N && fl.grid[y][x] === 0, want = C.ratsPerFloor, inRoom = new Set(); for (const r of fl.rooms || []) for (let y = r.y0; y <= r.y1; y++) for (let x = r.x0; x <= r.x1; x++) inRoom.add(`${x},${y}`);
    const cands = []; for (let y = 1; y < N - 1; y++) for (let x = 1; x < N - 1; x++) { const k = `${x},${y}`; if (!open(x, y) || inRoom.has(k) || fl.things[k] || (fl.features || {})[k]) continue; const ns = CM.DIRS.filter(([dx, dy]) => open(x + dx, y + dy)).length; if (ns === 2) cands.push([x, y]); }
    for (let i = 0; i < want && cands.length; i++) { const j = h(fl, "rat", String(i)) % cands.length; const [x, y] = cands.splice(j, 1)[0]; out.push({ x, y, id: `rat:${fl.number}:${i}` }); }
    if (CM.SETPIECES) for (const r of fl.rooms || []) { const T = CM.SETPIECES.find((t) => t.name === r.name); if (!T || !T.rats) continue; let n = 0; for (let y = r.y0; y <= r.y1 && n < 4; y++) for (let x = r.x0; x <= r.x1 && n < 4; x++) { const k = `${x},${y}`; if (!open(x, y) || fl.things[k] || (fl.features || {})[k] || (h(fl, "kr", k) % 100) >= 12) continue; out.push({ x, y, id: `rat:${fl.number}:k${n++}` }); } }   /* (plan 64: a kitchen's rats) */
    return out; };
}
