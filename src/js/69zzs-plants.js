"use strict";
// The plants' places (UPGRADE_PLAN_62.md phases 1-4): which mesh stands where, deterministic by hash. The trees: every
// tree square within the reach gets a mesh by its kind (the old picture's variant: 0 common, 1 pine, 2 birch; a
// willow beside water), by the season (autumn shapes as the leaves turn, bare shapes in winter for the broadleaves,
// the snow shapes when the snow lies deep), and by its state (69zzm-trees.js: a fallen tree is a log, a charred one
// a dead shape dark, a sapling the green shape small, a burning one a little dark). The plants above ground: grass
// tufts, flowers, plants, bushes and berry bushes, stumps, logs and rocks on the grass and under the trees, corn and
// wheat on the tilled rows, lilypads on the still water - dense by the Detail setting, each turned and sized a
// little differently. Below ground, by the band: moss in the Catacombs, weeds in the Flooded Vaults and the Salt
// Vaults, fungus thick in the Fungal Deep, roots at the Root of the World - the same shapes tinted, in the corners
// and along the walls. The pictures stand beyond the reach (26-surface.js). Nothing here is solid: the squares are
// what they were, and nothing stands on a thing, a feature or a door.
//   CM.PLANTS.reach(density) -> squares                 the meshes' reach by the Detail setting (0: pictures only)
//   CM.plantInstancesOf(game, fl, at, reach, density) -> [{ model, x, y, z, yaw, scale, sway, height, shade, kind }]
//   CM.plantTintOf(game, fl, model) -> [r, g, b] | null  the band's tint below ground (the window's uTint, a draw a model)
{ const P = CM.PLANTS = { reach: (density) => (density >= 1 ? 16 : density > 0 ? 12 : 0), smallReach: 11, treeH: 2.0, jitter: 0.18,
    bands: { 0: { per: 0.24, tint: [0.66, 0.78, 0.52], kinds: ["grass_short", "grass", "plant2"] }, 1: { per: 0.18, tint: [0.5, 0.72, 0.62], kinds: ["grass", "plant4", "plant1"], water: "lilypad" }, 4: { per: 0.12, tint: [0.78, 0.8, 0.7], kinds: ["grass_short", "plant3"], water: "lilypad" },
      5: { per: 0.6, tint: [0.92, 0.8, 1.0], kinds: ["plant1", "plant2", "plant3", "plant5", "bush", "bush2"] }, 9: { per: 0.35, tint: [0.78, 0.66, 0.5], kinds: ["plant4", "plant5", "bush", "log_moss", "stump_moss"] } } };
  const h = (fl, salt, key) => CM.hashSeed(`${fl.number}:${salt}:${key}`) >>> 0;
  const models = () => (CM.plantsPack && CM.plantsPack.manifest && CM.plantsPack.manifest.models) || {};
  const measure = (name) => { const m = models()[name]; if (!m) return null; const lo = m.box[0], hi = m.box[1]; return { height: Math.max(1e-3, hi[1] - lo[1]), width: Math.max(1e-3, hi[0] - lo[0], hi[2] - lo[2]), foot: lo[1], cx: (lo[0] + hi[0]) / 2, cz: (lo[2] + hi[2]) / 2 }; };
  const KIND = ["common", "pine", "birch"];
  const snowLies = (game) => Boolean(CM.snowDepth && CM.snowDepth(game) >= ((CM.WEATHERPLAY && CM.WEATHERPLAY.snowFrom) || 0.3));
  const treeModel = (game, fl, key, kind, state) => { const M = models(), has = (n) => Boolean(M[n]), season = CM.season ? CM.season(game) : "summer", two = h(fl, "shape", key) % 2 === 1;
    const snow = snowLies(game), turned = CM.seasonTurn ? CM.seasonTurn(game) : 1, turnedHere = (h(fl, "turn", key) % 100) / 100 < turned;
    if (state === "fallen") return has("log") ? (snow && has("log_snow") ? "log_snow" : "log") : null;
    if (state === "charred") return has(`${kind}_dead_snow`) && snow ? `${kind}_dead_snow` : has(`${kind}_dead`) ? `${kind}_dead` : has("common_dead") ? "common_dead" : null;
    if (snow && has(`${kind}_snow`)) return two && has(`${kind}_snow2`) ? `${kind}_snow2` : `${kind}_snow`;
    if (season === "winter" && kind !== "pine" && has(`${kind}_dead`)) return `${kind}_dead`;
    if (season === "autumn" && turnedHere && has(`${kind}_autumn`)) return two && has(`${kind}_autumn2`) ? `${kind}_autumn2` : `${kind}_autumn`;
    return two && has(`${kind}2`) ? `${kind}2` : kind; };
  // one instance: the model placed on its square (dx, dz in the square, 0..1), sized to `target` metres tall (or wide, for the flat)
  const place = (out, name, x, y, dx, dz, target, hh, opts = {}) => { const m = measure(name); if (!m) return; const scale = target / (opts.wide ? m.width : m.height), yaw = ((hh >> 8) % 360) * Math.PI / 180;
    out.push({ model: name, x: x + dx - m.cx * scale, y: opts.raw ? opts.y || 0 : (opts.y || 0) - m.foot * scale, z: y + dz - m.cz * scale, yaw, scale, sway: opts.sway || 0, height: m.height * scale, shade: opts.shade === undefined ? 1 : opts.shade, kind: opts.kind || "plant", small: Boolean(opts.small), raw: Boolean(opts.raw) }); };
  const trees = (game, fl, ax, ay, reach, out) => { const M = models(), wet = new Set((fl.decor || []).filter((d) => d.kind === "water").map((d) => `${d.x},${d.y}`)), S = game && game.ext ? CM.treeStateMap(game, fl) : {};
    for (const key of CM.treeSquares(fl)) { const [x, y] = key.split(",").map(Number); if (Math.abs(x - ax) + Math.abs(y - ay) > reach + 2) continue;
      const v = CM.hashSeed(`${fl.number}:tree:${key}`) % 3, byWater = CM.DIRS.some(([dx, dy]) => wet.has(`${x + dx},${y + dy}`)), kind = byWater && M.willow && h(fl, "willow", key) % 3 === 0 ? "willow" : KIND[v], state = S[key] || null;
      const name = treeModel(game, fl, key, kind, state); if (!name) continue; const m = measure(name); if (!m) continue;
      const hh = h(fl, "size", key), jitter = 1 - P.jitter / 2 + (hh % 100) / 100 * P.jitter, target = state === "sapling" ? P.treeH * 0.3 : state === "fallen" ? 0.5 : P.treeH * jitter;
      const scale = target / (state === "fallen" ? Math.max(m.height, 0.3) : m.height), yaw = ((hh >> 8) % 360) * Math.PI / 180;
      out.push({ model: name, x: x + 0.5 - m.cx * scale, y: -m.foot * scale, z: y + 0.5 - m.cz * scale, yaw, scale, sway: state === "fallen" ? 0 : 0.05, height: m.height * scale, shade: state === "charred" ? 0.35 : state === "burning" ? 0.8 : 1, kind: "tree" }); } };
  // above ground: by the ground and what is near
  const above = (game, fl, ax, ay, reach, density, out) => { const M = models(), has = (n) => Boolean(M[n]), N = fl.grid.length, season = CM.season ? CM.season(game) : "summer", snow = snowLies(game), winter = season === "winter";
    const wet = new Set((fl.decor || []).filter((d) => d.kind === "water").map((d) => `${d.x},${d.y}`)), canopy = new Set(fl.canopy || []), tree = (x, y) => x >= 0 && y >= 0 && x < N && y < N && fl.grid[y][x] !== 0 && CM.solidAt(fl, x, y) === "tree";
    const bld = (x, y) => x >= 0 && y >= 0 && x < N && y < N && fl.grid[y][x] !== 0 && CM.solidAt(fl, x, y) !== "tree", R = Math.min(reach, P.smallReach) + 1;
    for (let y = Math.max(0, ay - R); y <= Math.min(N - 1, ay + R); y++) for (let x = Math.max(0, ax - R); x <= Math.min(N - 1, ax + R); x++) { if (Math.abs(x - ax) + Math.abs(y - ay) > R) continue; const k = `${x},${y}`;
      const isWet = wet.has(k); if (fl.things[k] || ((fl.features || {})[k] && !isWet)) continue;   // (the river is a feature: the water keeps its lilies)
      if (isWet) { if (fl.grid[y][x] !== 0 && !isWet) continue; if (has("lilypad") && h(fl, "lily", k) % 100 < 35 * density) { const hh = h(fl, "lily2", k); place(out, "lilypad", x, y, 0.2 + (hh % 60) / 100, 0.2 + ((hh >> 6) % 60) / 100, 0.45, hh, { wide: true, y: 0.02, kind: "water", small: true }); } continue; }
      if (fl.grid[y][x] !== 0) continue; const g = CM.groundAt(fl, x, y) || (fl.number === -1 ? "grass" : "grass"), hh = h(fl, "plants", k), roll = (n) => (CM.hashSeed(`${fl.number}:p${n}:${k}`) >>> 0) % 1000 / 1000;
      const nearTree = [[-1, -1], [0, -1], [1, -1], [-1, 0], [1, 0], [-1, 1], [0, 1], [1, 1]].some(([dx, dy]) => tree(x + dx, y + dy)), byWall = CM.DIRS.some(([dx, dy]) => bld(x + dx, y + dy)), under = canopy.has(k), byWater = CM.DIRS.some(([dx, dy]) => wet.has(`${x + dx},${y + dy}`));
      if (g === "tilled") { const corn = h(fl, "row", `${y}`) % 2 === 0 && has("corn"), name = corn ? (hh % 2 ? "corn2" : "corn") : "wheat"; if (!has(name)) continue; for (let i = 0; i < 2; i++) place(out, name, x, y, 0.25 + i * 0.5 + (roll(i) - 0.5) * 0.12, 0.3 + (roll(i + 2) - 0.3) * 0.5, corn ? 0.85 : 0.55, hh + i * 977, { sway: 0.05, kind: "crop", small: true }); continue; }
      if (g !== "grass" && g !== "litter" && g !== "needles" && g !== "moss" && g !== "dirt") continue;
      const grassy = g === "grass", litter = g === "litter" || g === "needles" || g === "moss";
      // the grass tufts: on grass, fewer under the canopy and on the litter; short in winter
      const tufts = grassy ? (under ? 1 : 2) : litter ? 1 : 0; for (let i = 0; i < tufts; i++) { if (roll(10 + i) > 0.55 * density * (byWall ? 0.6 : 1)) continue; const name = winter || snow ? "grass_short" : roll(20 + i) < 0.5 ? "grass" : "grass2"; if (!has(name)) continue; place(out, name, x, y, 0.15 + roll(30 + i) * 0.7, 0.15 + roll(40 + i) * 0.7, 0.22 + roll(50 + i) * 0.16, hh + i * 131, { sway: 0.09, small: true }); }
      // flowers: on the open grass in spring and summer, fewer in autumn
      if (grassy && !under && !winter && !snow && has("flowers") && roll(60) < (season === "autumn" ? 0.06 : 0.16) * density) place(out, "flowers", x, y, 0.2 + roll(61) * 0.6, 0.2 + roll(62) * 0.6, 0.26 + roll(63) * 0.1, hh + 7, { sway: 0.05, small: true });
      // plants: under the trees and beside the water, on the litter and the moss
      if ((under || litter || byWater) && !snow && roll(70) < (litter ? 0.45 : 0.3) * density) { const name = `plant${1 + (hh % 5)}`; if (has(name)) place(out, name, x, y, 0.2 + roll(71) * 0.6, 0.2 + roll(72) * 0.6, 0.3 + roll(73) * 0.2, hh + 11, { sway: 0.05, small: true }); }
      // bushes: beside the trees and along the walls, berries in summer and autumn
      if ((nearTree || byWall) && roll(80) < (nearTree ? 0.2 : 0.1) * density) { const name = snow && has("bush_snow") ? "bush_snow" : !winter && (season === "summer" || season === "autumn") && roll(81) < 0.3 && has("bushberries") ? "bushberries" : roll(82) < 0.5 ? "bush" : "bush2"; if (has(name)) place(out, name, x, y, 0.3 + roll(83) * 0.4, 0.3 + roll(84) * 0.4, 0.32 + roll(85) * 0.2, hh + 13, { sway: 0.03, kind: "bush" }); }
      // the Wood's floor: stumps, logs and rocks, sparse
      if (fl.number === -1 && (litter || (grassy && nearTree)) && roll(90) < 0.05 * density) { const pick = roll(91), name = pick < 0.35 ? (snow ? "stump_snow" : litter ? "stump_moss" : "stump") : pick < 0.7 ? (snow ? "log_snow" : litter ? "log_moss" : "log") : (snow ? "rock_snow" : roll(92) < 0.5 ? "rock1" : "rock2"); if (has(name)) place(out, name, x, y, 0.3 + roll(93) * 0.4, 0.3 + roll(94) * 0.4, name.startsWith("log") ? 0.55 : name.startsWith("rock") ? 0.3 : 0.32, hh + 17, { wide: name.startsWith("log"), kind: "wood" }); } } };
  // below ground: by the band, in the corners and along the walls, on the water what floats
  const below = (game, fl, ax, ay, reach, density, out) => { if (CM.treesIn) for (const k of CM.treesIn(fl)) { const [x, y] = k.split(",").map(Number); if (Math.abs(x - ax) + Math.abs(y - ay) > reach + 2) continue; const hh = h(fl, "size", k), name = h(fl, "kind", k) % 3 === 0 ? "birch" : h(fl, "kind", k) % 3 === 1 ? "pine" : "common", m = measure(name); if (!m) continue; const scale = P.treeH * 0.9 / m.height; out.push({ model: name, x: x + 0.5 - m.cx * scale, y: CM.floorAt(fl, x, y) - m.foot * scale, z: y + 0.5 - m.cz * scale, yaw: ((hh >> 8) % 360) * Math.PI / 180, scale, sway: 0.03, height: m.height * scale, shade: 1, kind: "tree" }); }   /* (plan 64: the set pieces' trees) */
    if (CM.SETPIECES) for (const r of fl.rooms || []) { const T = CM.SETPIECES.find((t) => t.name === r.name); if (!T || !T.garden) continue;   /* (plan 64: a garden room grows thick whatever the band) */
      for (let y = r.y0; y <= r.y1; y++) for (let x = r.x0; x <= r.x1; x++) { if (fl.grid[y][x] !== 0 || Math.abs(x - ax) + Math.abs(y - ay) > reach + 1) continue; const k = `${x},${y}`; if (fl.things[k] || (fl.features || {})[k]) continue; const hh = h(fl, "garden", k), roll = (n) => (CM.hashSeed(`${fl.number}:g${n}:${k}`) >>> 0) % 1000 / 1000;
        if (roll(1) < 0.5 * density) place(out, roll(2) < 0.4 ? "flowers" : roll(2) < 0.7 ? `plant${1 + (hh % 5)}` : roll(2) < 0.85 ? "bush" : "grass", x, y, 0.2 + roll(3) * 0.6, 0.2 + roll(4) * 0.6, 0.25 + roll(5) * 0.2, hh, { sway: 0.05, kind: "plant", small: true, y: CM.floorAt(fl, x, y) });
        if (roll(6) < 0.3 * density) place(out, "grass", x, y, 0.15 + roll(7) * 0.7, 0.15 + roll(8) * 0.7, 0.2 + roll(9) * 0.12, hh + 3, { sway: 0.08, kind: "plant", small: true, y: CM.floorAt(fl, x, y) }); } }
    const B = P.bands[CM.themeIndex(fl.number)]; if (!B) return; const M = models(), has = (n) => Boolean(M[n]), N = fl.grid.length, R = Math.min(reach, P.smallReach) + 1, open = (x, y) => x >= 0 && y >= 0 && x < N && y < N && fl.grid[y][x] === 0;
    const wet = new Set((fl.decor || []).filter((d) => d.kind === "water").map((d) => `${d.x},${d.y}`));
    for (let y = Math.max(1, ay - R); y <= Math.min(N - 2, ay + R); y++) for (let x = Math.max(1, ax - R); x <= Math.min(N - 2, ax + R); x++) { if (!open(x, y) || Math.abs(x - ax) + Math.abs(y - ay) > R) continue; const k = `${x},${y}`; if (fl.things[k] || (fl.features || {})[k]) continue;
      const hh = h(fl, "under", k), roll = (n) => (CM.hashSeed(`${fl.number}:u${n}:${k}`) >>> 0) % 1000 / 1000, walls = CM.DIRS.filter(([dx, dy]) => !open(x + dx, y + dy)).length;
      if (wet.has(k)) { if (has("lilypad") && roll(1) < 0.4 * density) place(out, "lilypad", x, y, 0.2 + roll(2) * 0.6, 0.2 + roll(3) * 0.6, 0.4, hh, { wide: true, y: 0.02, kind: "water", small: true }); continue; }
      const n = Math.min(3, Math.floor(B.per * density * (1 + walls) * 2 + roll(4))); for (let i = 0; i < n; i++) { const name = B.kinds[(hh + i * 7) % B.kinds.length]; if (!has(name)) continue; const w = walls && CM.DIRS.find(([dx, dy]) => !open(x + dx, y + dy));   // (toward a wall when there is one)
        const dx = w ? 0.5 + w[0] * 0.3 + (roll(10 + i) - 0.5) * 0.3 : 0.2 + roll(10 + i) * 0.6, dz = w ? 0.5 + w[1] * 0.3 + (roll(20 + i) - 0.5) * 0.3 : 0.2 + roll(20 + i) * 0.6;
        place(out, name, x, y, dx, dz, name.startsWith("bush") ? 0.35 + roll(30 + i) * 0.2 : name.startsWith("log") ? 0.45 : name.startsWith("stump") ? 0.28 : 0.22 + roll(30 + i) * 0.18, hh + i * 211, { sway: 0, kind: "fungus", small: true, wide: name.startsWith("log") }); } } };
  CM.plantInstancesOf = (game, fl, at, reach, density = 1) => { const out = []; if (!fl || !reach || !models() || !fl.grid) return out; const [ax, ay] = at || fl.pos;
    if ((fl.number === 0 || fl.number === -1) && (!fl.special || fl.special === "wood" || fl.special === "town")) { if (CM.treeSquares) trees(game, fl, ax, ay, reach, out); above(game, fl, ax, ay, reach, density, out); }   /* (not in a cave or a house) */ else if (fl.number >= 1 && !(["joker", "interior", "cave"].includes(fl.special))) { below(game, fl, ax, ay, reach, density * (1 + (CM.bloomNow ? CM.bloomNow(game) : 0)), out); if (CM.clutterOf) for (const p of CM.clutterOf(game, fl, [ax, ay], reach, density)) out.push(p); if (CM.rockfallsOf) for (const k of CM.rockfallsOf(fl)) { const [x, y] = k.split(",").map(Number); if (Math.abs(x - ax) + Math.abs(y - ay) > reach + 1) continue; for (let i = 0; i < 4; i++) { const hh = CM.hashSeed(`${fl.number}:heap:${k}:${i}`) >>> 0; place(out, i % 2 ? "rock2" : "rock1", x, y, 0.2 + (hh % 60) / 100, 0.2 + ((hh >> 6) % 60) / 100, 0.45 + ((hh >> 12) % 40) / 100, hh, { kind: "stone", small: true, y: CM.floorAt(fl, x, y) + (i >= 2 ? 0.25 : 0) }); } } }   /* (plan 63: a fall of rock is a heap of the pack's rocks) */   /* (plan 63: the stalagmites and the stalactites) */
    return out; };
  CM.plantTintOf = (game, fl, model) => { if (!fl || !(fl.number >= 1)) return null; const band = CM.themeIndex(fl.number); if (/^stala[cg]/.test(model)) return CM.CLUTTER ? (band === 6 ? CM.CLUTTER.crystal : CM.CLUTTER.stone) : null; const B = P.bands[band]; return B ? B.tint : null; };   /* (the stone: grey, crystal-blue in the Crystal Caverns) */
}
