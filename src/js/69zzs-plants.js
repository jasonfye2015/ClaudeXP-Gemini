"use strict";
// The plants' places (UPGRADE_PLAN_62.md phases 1-2): which mesh stands where, deterministic by hash. Phase 1: the
// trees - every tree square within the reach gets a mesh by its kind (the old picture's variant: 0 common, 1 pine, 2
// birch; a willow beside water), by the season (autumn shapes as the leaves turn, bare shapes in winter for the
// broadleaves, the snow shapes when the snow lies deep), and by its state (69zzm-trees.js: a fallen tree is a log,
// a charred one a dead shape dark, a sapling the green shape small, a burning one a little dark). The pictures stand
// beyond the reach (26-surface.js). Nothing here is solid: the squares are what they were.
//   CM.PLANTS.reach(density) -> squares                 the meshes' reach by the Detail setting (0: pictures only)
//   CM.plantInstancesOf(game, fl, at, reach) -> [{ model, x, y, z, yaw, scale, sway, height, shade, kind }]
{ const P = CM.PLANTS = { reach: (density) => (density >= 1 ? 16 : density > 0 ? 12 : 0), treeH: 2.0, jitter: 0.18 };
  const h = (fl, salt, key) => CM.hashSeed(`${fl.number}:${salt}:${key}`) >>> 0;
  const models = () => (CM.plantsPack && CM.plantsPack.manifest && CM.plantsPack.manifest.models) || {};
  const measure = (name) => { const m = models()[name]; if (!m) return null; const lo = m.box[0], hi = m.box[1]; return { height: Math.max(1e-3, hi[1] - lo[1]), foot: lo[1], cx: (lo[0] + hi[0]) / 2, cz: (lo[2] + hi[2]) / 2 }; };
  const KIND = ["common", "pine", "birch"];
  const treeModel = (game, fl, key, kind, state) => { const M = models(), has = (n) => Boolean(M[n]), season = CM.season ? CM.season(game) : "summer", two = h(fl, "shape", key) % 2 === 1;
    const snow = CM.snowDepth && CM.WX && CM.snowDepth(game) >= ((CM.WEATHERPLAY && CM.WEATHERPLAY.snowFrom) || 0.3), turned = CM.seasonTurn ? CM.seasonTurn(game) : 1, turnedHere = (h(fl, "turn", key) % 100) / 100 < turned;
    if (state === "fallen") return has("log") ? "log" : null;
    if (state === "charred") return has(`${kind}_dead_snow`) && snow ? `${kind}_dead_snow` : has(`${kind}_dead`) ? `${kind}_dead` : `${kind}_dead` === "pine_dead" && has("common_dead") ? "common_dead" : null;
    if (snow && has(`${kind}_snow`)) return two && has(`${kind}_snow2`) ? `${kind}_snow2` : `${kind}_snow`;
    if (season === "winter" && kind !== "pine" && has(`${kind}_dead`)) return `${kind}_dead`;
    if (season === "autumn" && turnedHere && has(`${kind}_autumn`)) return two && has(`${kind}_autumn2`) ? `${kind}_autumn2` : `${kind}_autumn`;
    return two && has(`${kind}2`) ? `${kind}2` : kind; };
  CM.plantInstancesOf = (game, fl, at, reach) => { const out = []; if (!fl || !reach || !(fl.number === 0 || fl.number === -1) || !CM.treeSquares) return out; const [ax, ay] = at || fl.pos, M = models(), wet = new Set((fl.decor || []).filter((d) => d.kind === "water").map((d) => `${d.x},${d.y}`));
    const S = game && game.ext ? CM.treeStateMap(game, fl) : {};
    for (const key of CM.treeSquares(fl)) { const [x, y] = key.split(",").map(Number); if (Math.abs(x + 0.5 - ax - 0.5) + Math.abs(y + 0.5 - ay - 0.5) > reach + 2) continue;
      const v = CM.hashSeed(`${fl.number}:tree:${key}`) % 3, byWater = CM.DIRS.some(([dx, dy]) => wet.has(`${x + dx},${y + dy}`)), kind = byWater && M.willow && h(fl, "willow", key) % 3 === 0 ? "willow" : KIND[v], state = S[key] || null;
      const name = treeModel(game, fl, key, kind, state); if (!name) continue; const m = measure(name); if (!m) continue;
      const hh = h(fl, "size", key), jitter = 1 - P.jitter / 2 + (hh % 100) / 100 * P.jitter, target = state === "sapling" ? P.treeH * 0.3 : state === "fallen" ? 0.5 : P.treeH * jitter;
      const scale = target / (state === "fallen" ? Math.max(m.height, 0.3) : m.height), yaw = ((hh >> 8) % 360) * Math.PI / 180;
      out.push({ model: name, x: x + 0.5 - m.cx * scale, y: -m.foot * scale, z: y + 0.5 - m.cz * scale, yaw, scale, sway: state === "fallen" ? 0 : 0.05, height: m.height * scale, shade: state === "charred" ? 0.35 : state === "burning" ? 0.8 : 1, kind: "tree" }); }
    return out; };
}
