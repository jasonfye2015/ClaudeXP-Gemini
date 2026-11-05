"use strict";
// The surface, as data the tests can see: the kinds a solid cell can be (the dungeon's wall, a house, the town wall,
// a hedge, a tree), the ground a cell can wear, the sky by the clock, and the floor's mesh as plain arithmetic - the
// renderer (40-render.js) only draws what this works out. A floor's grid stays 0 (open) or not; a surface floor adds
// `kinds` {key: kind} for the solid cells that aren't its `solidDefault`, `ground` {key: ground} for cells that aren't
// the theme's floor, and `canopy` [keys] for open cells under the trees. All three are remade with the floor from the
// seed, never saved.
CM.SOLID = {
  wall: { face: "wall", h: 1 },                                                  // the dungeon's: the depth's stone, as ever
  house: { face: "solid:house", h: 1.6, roof: "solid:roof" },                     // plaster and timber, a shuttered window
  door: { face: "solid:door", h: 1.6, roof: "solid:roof" },                       // the face with the door in it
  shop: { face: "solid:shop", h: 1.6, roof: "solid:roof" },                       // a door, and the board over it
  frame: { face: "solid:frame", h: 1.2, see: true },                              // a house being built: posts and beams
  townwall: { face: "solid:townwall", h: 1.3, top: "solid:townwall:top" },        // the ring wall, with its walk
  tower: { face: "solid:townwall", h: 2.3, tower: true },
  casino: { face: "solid:casino", h: 2.15, roof: "solid:casinoroof", side: "solid:casino", gable: "solid:casinogable" },   // the Gilded Joker (64k-claudeatro.js): red plaster, gold, a copper roof
  casinodoor: { face: "solid:casinodoor", h: 2.15, roof: "solid:casinoroof", side: "solid:casino", gable: "solid:casinogable", door: true },
  cabin: { face: "solid:logs", h: 1.45, roof: "solid:roof", side: "solid:logs", gable: "solid:logs" },        // Leshy's cabin (61f-cabin.js): logs all round
  cabindoor: { face: "solid:cabindoor", h: 1.45, roof: "solid:roof", side: "solid:logs", gable: "solid:logs", door: true },
  magetower: { face: "solid:magestone", h: 10.5, tower: true, mage: true },   // the Mage Tower's nine squares: one great octagon (61d-magetower.js)                        // a gate tower: an octagon of stone with merlons on its top (61c-tower.js)
  crag: { face: "solid:crag", h: 1.9, top: "ground:grass" },                     // Claudeita's crag in the Wood (61g-cavemouth.js), and its mouth
  cavemouth: { face: "solid:cavemouth", h: 1.9, top: "ground:grass" },
  cragtall: { face: "solid:crag", h: 2.7, top: "ground:grass" }, craglow: { face: "solid:crag", h: 1.15, top: "ground:grass" },   // (the crag rises behind its mouth, and falls away at its ends)
  fortwall: { face: "solid:fortwall", h: 2.9, top: "solid:townwall:top" },      // the Fortress (61h-fortress.js): black walls, a tower at each corner and by the doors
  forttower: { face: "solid:fortwall", h: 3.9, top: "solid:townwall:top" },
  fortdoorL: { face: "solid:fortdoorL", h: 2.9, top: "solid:townwall:top" }, fortdoorR: { face: "solid:fortdoorR", h: 2.9, top: "solid:townwall:top" },
  hedge: { face: "solid:hedge", h: 0.55, top: "solid:hedge", see: true },         // seen over
  fence: { face: "solid:fence", h: 0.5, see: true },                              // seen through
  cliff: { face: "solid:cliff", h: 2.2, top: "ground:grass" },                    // the hill's side
  tree: { tree: true, h: 1.7, see: true },                                        // not a wall: a trunk and a crown, two crossed pictures
};
// ---- the buildings: the house cells (house, door, shop) as rectangles, each under one gabled roof ----------------------
// CM.buildingsOf(fl) cuts a floor's house cells into rectangles, the largest first, so a row of houses is one long
// roof and a block is one wide one: [{ x0, y0, x1, y1 (cells, inclusive), along: "x" | "z" (the ridge), h (the walls),
// rise (the ridge over the walls), overhang }]. CM.roofAt says how high a building's roof is over a point, and
// CM.chimneysOf where its chimneys stand (and the smoke starts). Plain arithmetic, so the tests can check it.
CM.BUILDING_KINDS = ["house", "door", "shop", "cabin", "cabindoor", "casino", "casinodoor"];
CM.ROOF = { overhang: 0.16, gableOverhang: 0.1, pitch: 0.62, minRise: 0.45, maxRise: 1.25 };
CM.isBuilding = (fl, x, y) => CM.inBounds(fl, x, y) && fl.grid[y][x] !== 0 && CM.BUILDING_KINDS.includes(CM.solidAt(fl, x, y));
CM.buildingsOf = function (fl) {
  const size = fl.grid.length, free = new Set();
  for (let y = 0; y < size; y++) for (let x = 0; x < size; x++) if (CM.isBuilding(fl, x, y)) free.add(`${x},${y}`);
  const out = [];
  while (free.size) {
    let best = null;
    for (const key of free) {                                                   // the largest rectangle of free cells with this one at its top left
      const [x0, y0] = key.split(",").map(Number);
      let maxW = 0; while (free.has(`${x0 + maxW},${y0}`)) maxW++;
      for (let y = y0, w = maxW; w > 0 && free.has(`${x0},${y}`); y++) {
        let rw = 0; while (rw < w && free.has(`${x0 + rw},${y}`)) rw++;
        w = rw; const area = w * (y - y0 + 1);
        if (!best || area > best.area || (area === best.area && (y0 < best.y0 || (y0 === best.y0 && x0 < best.x0)))) best = { x0, y0, x1: x0 + w - 1, y1: y, area };
      }
    }
    for (let y = best.y0; y <= best.y1; y++) for (let x = best.x0; x <= best.x1; x++) free.delete(`${x},${y}`);
    const wx = best.x1 - best.x0 + 1, wz = best.y1 - best.y0 + 1, along = wx >= wz ? "x" : "z", span = along === "x" ? wz : wx;
    const h = (CM.SOLID[CM.solidAt(fl, best.x0, best.y0)] || CM.SOLID.house).h;
    out.push({ x0: best.x0, y0: best.y0, x1: best.x1, y1: best.y1, along, h, rise: Math.max(CM.ROOF.minRise, Math.min(CM.ROOF.maxRise, (span / 2) * CM.ROOF.pitch)), overhang: CM.ROOF.overhang });
  }
  return out;                                                                     // (made from the grid each time: a frame raised into a house is roofed at once)
};
// the roof's height over a point (world x, z), or null past its eaves
CM.roofAt = function (b, x, z) {
  const X0 = b.x0, X1 = b.x1 + 1, Z0 = b.y0, Z1 = b.y1 + 1, o = b.overhang, g = CM.ROOF.gableOverhang;
  if (b.along === "x") { if (x < X0 - g || x > X1 + g || z < Z0 - o || z > Z1 + o) return null; const half = (Z1 - Z0) / 2; return b.h + b.rise * (1 - Math.abs(z - (Z0 + Z1) / 2) / half); }
  if (z < Z0 - g || z > Z1 + g || x < X0 - o || x > X1 + o) return null; const half = (X1 - X0) / 2; return b.h + b.rise * (1 - Math.abs(x - (X0 + X1) / 2) / half);
};
// a chimney on most buildings of two cells or more: a stack beside the ridge, by hash; { x, z (its middle), base, top, w }
CM.chimneysOf = function (fl) {
  const out = [];
  for (const b of CM.buildingsOf(fl)) {
    const cells = (b.x1 - b.x0 + 1) * (b.y1 - b.y0 + 1), hsh = CM.hashSeed(`${fl.number}:chimney:${b.x0},${b.y0}`);
    if (cells < 2 || hsh % 4 === 0) continue;
    const len = b.along === "x" ? b.x1 - b.x0 + 1 : b.y1 - b.y0 + 1, at = Math.floor(hsh / 8) % len, side = Math.floor(hsh / 64) % 2 ? 1 : -1, w = 0.26;
    const mid = b.along === "x" ? (b.y0 + b.y1 + 1) / 2 : (b.x0 + b.x1 + 1) / 2, off = Math.min(0.45, ((b.along === "x" ? b.y1 - b.y0 + 1 : b.x1 - b.x0 + 1) / 2) * 0.35) * side;
    const x = b.along === "x" ? b.x0 + at + 0.5 : mid + off, z = b.along === "x" ? mid + off : b.y0 + at + 0.5;
    const low = Math.min(CM.roofAt(b, x - w / 2, z - w / 2), CM.roofAt(b, x + w / 2, z + w / 2), CM.roofAt(b, x - w / 2, z + w / 2), CM.roofAt(b, x + w / 2, z - w / 2));
    out.push({ x, z, base: low - 0.05, top: b.h + b.rise + 0.32, w });
  }
  return out;
};
CM.SOLID_COLOURS = { wall: "#3A3028", house: "#8A6A48", door: "#A0784A", shop: "#A0784A", frame: "#B09060", townwall: "#6E6A62", tower: "#5A564E", magetower: "#2A2830", cabin: "#6A4A2A", cabindoor: "#7A5432", casino: "#8A2A2A", casinodoor: "#B08A2E", crag: "#5A5650", fortwall: "#2A2624", forttower: "#2A2624", fortdoorL: "#4A2C16", fortdoorR: "#4A2C16", cragtall: "#5A5650", craglow: "#5A5650", cavemouth: "#1A1410", hedge: "#5C8A3C", fence: "#A08860", cliff: "#4A4038", tree: "#3F6B32" };
CM.GROUNDS = ["grass", "dirt", "cobbles", "flags", "planks", "tilled", "moss", "litter", "needles"];   // (litter and needles: under the trees, the trunk's shade at the middle)
CM.UNDER = ["tree", "hedge", "fence", "frame", "tower", "magetower"];                          // the solid kinds the ground runs under on the surface
CM.SKIRT = 40;                                                          // how far past the map's edge the ground runs, and the far silhouettes stand
// the trees by the season (the eleventh update, phase 3): the crown's colour, bare in winter, snow on the fir, blossom
// on the oak in spring; the canopy over the paths with them. Pictures only: the mesh is the same in every season.
CM.CROWNS = {
  0: { spring: { colour: [104, 156, 66], blossom: true }, summer: { colour: [62, 110, 48] }, autumn: { colour: [168, 78, 38], mix: [196, 132, 48] }, winter: { bare: true } },   // the oak
  1: { spring: { colour: [52, 100, 60] }, summer: { colour: [40, 84, 52] }, autumn: { colour: [40, 80, 50] }, winter: { colour: [34, 70, 48], snow: true } },                   // the fir
  2: { spring: { colour: [132, 178, 78] }, summer: { colour: [84, 140, 62] }, autumn: { colour: [196, 150, 48] }, winter: { bare: true } },                                   // the birch
};
CM.crownOf = (variant, season) => (CM.CROWNS[variant] || CM.CROWNS[0])[CM.CROWNS[0][season] ? season : "summer"];
CM.CANOPIES = { spring: [74, 128, 52], summer: [50, 96, 40], autumn: [150, 84, 40], winter: null };   // (winter: bare branches over the path)
CM.PREV_SEASON = { spring: "winter", summer: "spring", autumn: "summer", winter: "autumn" };   // (v24.2: the season a tree may not have left yet)
CM.treeVariant = (fl, x, y) => CM.hashSeed(`${fl.number}:tree:${x},${y}`) % 3;   // 0 an oak, 1 a fir, 2 a birch in its autumn
// what stands at a cell: null for open ground, else the solid's kind (the map's edge is the floor's default solid)
CM.solidAt = (fl, x, y) => (CM.inBounds(fl, x, y) && fl.grid[y][x] === 0 ? null : (fl.kinds && fl.kinds[`${x},${y}`]) || fl.solidDefault || "wall");
CM.groundAt = (fl, x, y) => (fl.ground && fl.ground[`${x},${y}`]) || null;
CM.setSolid = (fl, x, y, kind) => { if (kind === (fl.solidDefault || "wall")) { if (fl.kinds) delete fl.kinds[`${x},${y}`]; } else (fl.kinds = fl.kinds || {})[`${x},${y}`] = kind; };
CM.setGround = (fl, x, y, ground) => { (fl.ground = fl.ground || {})[`${x},${y}`] = ground; };
// the open cells with trees on most sides are under the leaves (eight neighbours, five or more trees)
CM.markCanopy = function (fl) {
  const size = fl.grid.length, out = [];
  for (let y = 0; y < size; y++) for (let x = 0; x < size; x++) {
    if (fl.grid[y][x] !== 0) continue;
    let trees = 0;
    for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) if ((dx || dy) && CM.solidAt(fl, x + dx, y + dy) === "tree") trees++;
    if (trees >= 5) out.push(`${x},${y}`);
  }
  fl.canopy = out;
  return out;
};

// ---- the sky, by the clock: night, dawn, day, dusk, with the moon and the weather on it --------------------------------
CM.SKY = {
  night: { zenith: [0.03, 0.04, 0.10], horizon: [0.09, 0.10, 0.18], light: 0.06 },
  dawn: { zenith: [0.36, 0.40, 0.64], horizon: [0.96, 0.64, 0.44], light: 0.6 },
  day: { zenith: [0.34, 0.55, 0.88], horizon: [0.80, 0.88, 0.96], light: 1 },
  dusk: { zenith: [0.24, 0.20, 0.42], horizon: [0.92, 0.50, 0.30], light: 0.5 },
};
CM.daylightOf = (game) => (game && game.season && CM.DAYLIGHT && CM.DAYLIGHT[game.season]) || [6, 20];
// {zenith, horizon (0..1 rgb), light (0 dark .. 1 full day), word, night, sun, moon (0..1 along the arc, or null), phase, weather}
CM.sky = function (game) {
  const h = CM.hourOf(game), [dawn, dusk] = CM.daylightOf(game), S = CM.SKY;
  const mix = (a, b, k) => a.map((v, i) => v + (b[i] - v) * k);
  const blend = (A, B, k) => ({ zenith: mix(A.zenith, B.zenith, k), horizon: mix(A.horizon, B.horizon, k), light: A.light + (B.light - A.light) * k });
  let sky, word;
  if (h >= dawn - 2 && h < dawn) { sky = blend(S.night, S.dawn, (h - (dawn - 2)) / 2); word = "dawn"; }   // (v71.0: the turnings two hours wide, a five-minute dawn at the clock's pace)
  else if (h >= dawn && h < dawn + 2) { sky = blend(S.dawn, S.day, (h - dawn) / 2); word = "dawn"; }
  else if (h >= dawn + 2 && h < dusk - 2) { sky = blend(S.day, S.day, 0); word = "day"; }
  else if (h >= dusk - 2 && h < dusk) { sky = blend(S.day, S.dusk, (h - (dusk - 2)) / 2); word = "dusk"; }
  else if (h >= dusk && h < dusk + 2) { sky = blend(S.dusk, S.night, (h - dusk) / 2); word = "dusk"; }
  else { sky = blend(S.night, S.night, 0); word = "night"; }
  const phase = CM.moonPhase(game), moonlight = (1 - Math.abs(phase - 4) / 4) * 0.14;   // a full moon lightens the night
  if (sky.light < 0.3) { const k = 1 - sky.light / 0.3; sky.light += moonlight * k; sky.zenith = mix(sky.zenith, [0.10, 0.12, 0.22], moonlight * 3 * k); sky.horizon = mix(sky.horizon, [0.14, 0.16, 0.26], moonlight * 3 * k); }
  const weather = CM.weather ? CM.weather(game) : "clear";
  if (weather === "rain" || weather === "mist" || weather === "snow") {                 // a low sky: greyer, and less light
    const grey = weather === "mist" ? [0.72, 0.74, 0.76] : weather === "snow" ? [0.78, 0.78, 0.82] : [0.46, 0.48, 0.52];
    sky.zenith = mix(sky.zenith, grey, 0.6 * sky.light); sky.horizon = mix(sky.horizon, grey, 0.6 * sky.light); sky.light *= 0.8;
  }
  const P = CM.skyPlaces(game);
  return Object.assign(sky, { word, night: sky.light < 0.3, sun: P.sun, moon: P.moon, phase, weather });
};

// ---- the floor as triangles -----------------------------------------------------------------------------------------
// A vertex is ten floats: position 3, texture 3 (u, v, layer), shade 1, fx 3 (a hit's flash, alpha, glow). `index`
// names the texture layers (the look's); a layer the look hasn't got falls back to the plain wall. Returns {data,
// count} and what was built, for the tests: ceilings, walls, roofs, trees, and on the surface the squares covered (ground,
// a top or a roof over every one), the skirt's quads past the edge and the far ring's.
CM.MESH_STRIDE = 10;
// (v24.0) how far each growing thing's top gives to a full wind, in squares: read by the vertex shader (40-render.js)
CM.SWAY = { tree: 0.07, plant: 0.06, tallgrass: 0.11, reeds: 0.12, tuft: 0.06, tuft_dry: 0.07, flowers: 0.05, shrub: 0.04, fern: 0.05 };
CM.floorMesh = function (fl, theme, index, opts = {}) {                 // opts: { props (CM.scatter's), sub (where each prop sits in its layer) }
  const grid = fl.grid, size = grid.length, out = [], features = fl.features || {}, sky = Boolean(theme.sky), canopy = new Set(fl.canopy || []);
  const only = opts.only || null, W = only === "windows";                  // (v26.1: a part alone - "props" (the traces), "windows" (the lit ones and the far lights))
  const L = (name) => (index[name] !== undefined ? index[name] : index.wall);
  const near = (n) => (W ? () => {} : (a, b, c, d, layer, shade) => { const uv = [[0, 1], [1, 1], [1, 0], [0, 0]]; for (const i of [0, 1, 2, 0, 2, 3]) out.push(...[a, b, c, d][i], uv[i][0], uv[i][1], layer, shade, 10 + n, 1, 0); });   // (v58.1: a detail's quad, drawn only within n squares)
  const quad = W ? () => {} : (a, b, c, d, layer, shade, sway = 0) => { const uv = [[0, 1], [1, 1], [1, 0], [0, 0]]; for (const i of [0, 1, 2, 0, 2, 3]) out.push(...[a, b, c, d][i], uv[i][0], uv[i][1], layer, shade, i >= 2 ? -sway : 0, 1, 0); };   // (sway, v24.0: how far its top gives to the wind)
  // a floor or ceiling square, turned a quarter-turn and mirrored by hash (no two neighbours alike), with a shade at
  // each corner: darker where the corner meets walls (ambient occlusion, baked)
  const UVS = [[[0, 1], [1, 1], [1, 0], [0, 0]], [[1, 1], [1, 0], [0, 0], [0, 1]], [[1, 0], [0, 0], [0, 1], [1, 1]], [[0, 0], [0, 1], [1, 1], [1, 0]]];
  const quadVaried = (a, b, c, d, layer, shades, x, y, salt) => {
    const h = CM.hashSeed(`${fl.number}:${salt}:${x},${y}`), uvs = UVS[h % 4].map(([u, v]) => ((h >> 2) & 1 ? [1 - u, v] : [u, v]));
    for (const i of [0, 1, 2, 0, 2, 3]) out.push(...[a, b, c, d][i], uvs[i][0], uvs[i][1], layer, shades[i], 0, 1, 0);
  };
  const openAt = (cx, cy) => cy >= 0 && cy < size && cx >= 0 && cx < size && grid[cy][cx] === 0;
  const corner = (cx, cy, k) => {                                       // a corner of the floor, (cx, cy) its grid point: darker by the walls round it
    const walls = [[cx - 1, cy - 1], [cx, cy - 1], [cx - 1, cy], [cx, cy]].filter(([qx, qy]) => !openAt(qx, qy)).length;
    return k * (1 - 0.16 * walls);
  };
  const pickWall = (x, y, d, wx, wy) => {
    const f = features[`${wx},${wy}`];
    if (f && f.type === "secret" && !f.found) return index.wallsecret;              // (a hairline, for the sharp-eyed)
    const h = (x * 73856093) ^ (y * 19349663) ^ (d * 83492791), r = ((h >>> 0) % 1000) / 1000;
    return r < (theme.bones || 0) * 0.5 ? index.wallbones : r < 0.6 ? index.wall : index.wall2;
  };
  const kindOf = (x, y) => CM.SOLID[CM.solidAt(fl, x, y)] || CM.SOLID.wall;
  const solid = (nx, ny) => ny < 0 || ny >= size || nx < 0 || nx >= size || grid[ny][nx] !== 0;
  const tops = new Set(), trees = new Set(), covered = new Set();
  let ceilings = 0, walls = 0, roofs = 0, skirt = 0, ring = 0;
  const SIDES = [[0, -1, 1.0], [0, 1, 1.0], [1, 0, 0.84], [-1, 0, 0.84]];                  // north, south, east, west: the far wall lit a little more
  if (!only) for (let y = 0; y < size; y++) for (let x = 0; x < size; x++) {
    if (grid[y][x] !== 0) {
      if (!sky) continue;                                                       // (below: rock is rock)
      const kind = CM.solidAt(fl, x, y), K = CM.SOLID[kind] || CM.SOLID.wall, key = `${x},${y}`;
      if (CM.UNDER.includes(kind)) {                                            // the ground runs on under it: needles or litter under a tree, else the grass
        const g = kind === "tree" ? (CM.treeVariant(fl, x, y) === 1 ? "needles" : "litter") : CM.groundAt(fl, x, y) || "grass";
        quad([x, 0, y + 1], [x + 1, 0, y + 1], [x + 1, 0, y], [x, 0, y], L(`ground:${g}`), kind === "tree" ? 0.6 : 0.85); covered.add(key);
        if (kind === "tree") trees.add(key);
      } else if (K.top && index[K.top] !== undefined) { if (!tops.has(key)) { tops.add(key); quad([x, K.h, y + 1], [x + 1, K.h, y + 1], [x + 1, K.h, y], [x, K.h, y], index[K.top], 0.95); } covered.add(key); }
      else if (K.roof || K.tower) covered.add(key);                            // (a house's square is under its roof; a tower's under its top)
      continue;
    }
    covered.add(`${x},${y}`);
    const LV = !sky && fl.levels ? fl.levels[`${x},${y}`] : null, F0 = LV ? LV[0] : 0, C0 = LV ? LV[1] : 1;   // (v47.0: the square's floor and ceiling - 69zzi-levels.js)
    const under = sky && canopy.has(`${x},${y}`), g = CM.groundAt(fl, x, y);
    const gb = sky && CM.blendGroundAt ? CM.blendGroundAt(fl, x, y) : g, floorLayer = gb && index[`ground:${gb}`] !== undefined ? index[`ground:${gb}`] : index.floor;   // (v55.0: the forest floor under the trees)
    if (sky) {
      quad([x, 0, y + 1], [x + 1, 0, y + 1], [x + 1, 0, y], [x, 0, y], floorLayer, under ? 0.55 : 0.9);
      if ((g === "cobbles" || g === "flags") && index["solid:sill"] !== undefined && opts.detail !== 0) SIDES.forEach(([ex, ey], d) => {   // (v54.2) a kerb of dressed stone where the paving meets grass or earth
        const nx = x + ex, ny = y + ey; if (!openAt(nx, ny)) return; const ng = CM.groundAt(fl, nx, ny); if (ng === "cobbles" || ng === "flags" || ng === "planks") return;
        const K = index["solid:sill"], kh = 0.045, kw = 0.09, a2 = d === 0 ? [x, y] : d === 1 ? [x + 1, y + 1] : d === 2 ? [x + 1, y] : [x, y + 1], b2 = d === 0 ? [x + 1, y] : d === 1 ? [x, y + 1] : d === 2 ? [x + 1, y + 1] : [x, y];
        const ia = [a2[0] - ex * kw, a2[1] - ey * kw], ib = [b2[0] - ex * kw, b2[1] - ey * kw];
        quad([ia[0], kh, ia[1]], [ib[0], kh, ib[1]], [b2[0], kh, b2[1]], [a2[0], kh, a2[1]], K, 0.95); quad([a2[0], 0, a2[1]], [b2[0], 0, b2[1]], [b2[0], kh, b2[1]], [a2[0], kh, a2[1]], K, 0.72); quad([ib[0], 0, ib[1]], [ia[0], 0, ia[1]], [ia[0], kh, ia[1]], [ib[0], kh, ib[1]], K, 0.8); });
      if (under && index.canopy !== undefined) quad([x, 1.25, y], [x + 1, 1.25, y], [x + 1, 1.25, y + 1], [x, 1.25, y + 1], index.canopy, 0.6);
    } else {
      quadVaried([x, F0, y + 1], [x + 1, F0, y + 1], [x + 1, F0, y], [x, F0, y], floorLayer, [corner(x, y + 1, 0.95), corner(x + 1, y + 1, 0.95), corner(x + 1, y, 0.95), corner(x, y, 0.95)], x, y, "f");
      quadVaried([x, C0, y], [x + 1, C0, y], [x + 1, C0, y + 1], [x, C0, y + 1], index.ceiling, [corner(x, y, 0.75), corner(x + 1, y, 0.75), corner(x + 1, y + 1, 0.75), corner(x, y + 1, 0.75)], x, y, "c");
      ceilings++;
    }
    SIDES.forEach(([dx, dy, shade], d) => {
      const nx = x + dx, ny = y + dy;
      if (!solid(nx, ny)) { if (!sky && fl.levels) { const NL = fl.levels[`${nx},${ny}`], nf = NL ? NL[0] : 0, nc = NL ? NL[1] : 1;   // (v47.0: a step up to the next square, or its lower ceiling, faced from this one)
          const a = d === 0 ? [x, y] : d === 1 ? [x + 1, y + 1] : d === 2 ? [x + 1, y] : [x, y + 1], b = d === 0 ? [x + 1, y] : d === 1 ? [x, y + 1] : d === 2 ? [x + 1, y + 1] : [x, y];
          if (nf > F0 + 1e-6) quad([a[0], F0, a[1]], [b[0], F0, b[1]], [b[0], nf, b[1]], [a[0], nf, a[1]], pickWall(x, y, d, nx, ny), shade * 0.95);
          if (nc < C0 - 1e-6) quad([a[0], nc, a[1]], [b[0], nc, b[1]], [b[0], C0, b[1]], [a[0], C0, a[1]], pickWall(x, y, d, nx, ny), shade * 0.7); } return; }
      const K = kindOf(nx, ny), key = `${nx},${ny}`;
      if (K.roof || K.tower) return;                                                  // (a building or a tower: walled and roofed below, every face)
      if (K.tree) {                                                                   // the trees: this one, and the rank behind it
        trees.add(key);
        if (solid(nx + dx, ny + dy) && kindOf(nx + dx, ny + dy).tree) trees.add(`${nx + dx},${ny + dy}`);
        return;
      }
      if (CM.FENCE_MODEL && K === CM.SOLID.fence && (index["solid:paling"] !== undefined || index["solid:timber"] !== undefined)) return;   // (v56.2: built - 26g-fences.js)
      const h = K.h || 1, layer = K.face === "wall" ? pickWall(x, y, d, nx, ny) : L(K.face);
      const a = d === 0 ? [x, y] : d === 1 ? [x + 1, y + 1] : d === 2 ? [x + 1, y] : [x, y + 1];
      const b = d === 0 ? [x + 1, y] : d === 1 ? [x, y + 1] : d === 2 ? [x + 1, y + 1] : [x, y];
      if (sky || K.face !== "wall") quad([a[0], 0, a[1]], [b[0], 0, b[1]], [b[0], h, b[1]], [a[0], h, a[1]], layer, shade);
      else {                                                                          // below: the wall's foot in shadow, and darker where it meets a side wall
        const sideA = !openAt(x + (d === 0 ? -1 : d === 1 ? 1 : 0), y + (d === 2 ? -1 : d === 3 ? 1 : 0)), sideB = !openAt(x + (d === 0 ? 1 : d === 1 ? -1 : 0), y + (d === 2 ? 1 : d === 3 ? -1 : 0));
        const fa = shade * (sideA ? 0.62 : 0.78), fb = shade * (sideB ? 0.62 : 0.78), ta = shade * (sideA ? 0.85 : 0.97), tb = shade * (sideB ? 0.85 : 0.97);
        const wv = CM.hashSeed(`${fl.number}:wv:${x},${y},${d}`) >>> 0, flip = (wv >>> 3) & 1, kk = 0.92 + ((wv >>> 5) % 17) / 100;   // (v48.2: no two wall squares quite alike - mirrored by hash, a little lighter or darker)
        const uv = flip ? [[1, 1], [0, 1], [0, 0], [1, 0]] : [[0, 1], [1, 1], [1, 0], [0, 0]], P = [[a[0], F0, a[1]], [b[0], F0, b[1]], [b[0], F0 + h * (C0 - F0), b[1]], [a[0], F0 + h * (C0 - F0), a[1]]], sh = [fa * kk, fb * kk, tb * kk, ta * kk];
        for (const i of [0, 1, 2, 0, 2, 3]) out.push(...P[i], uv[i][0], uv[i][1], layer, sh[i], 0, 1, 0);
        if (index["trim:stone"] !== undefined) { const ins = 0.035, sk = 0.09, A2 = [a[0] - dx * ins, a[1] - dy * ins], B2 = [b[0] - dx * ins, b[1] - dy * ins], T = index["trim:stone"];   // (v48.3) a course of skirting stones at the wall's foot, standing proud
          quad([A2[0], F0, A2[1]], [B2[0], F0, B2[1]], [B2[0], F0 + sk, B2[1]], [A2[0], F0 + sk, A2[1]], T, shade * 0.9); quad([a[0], F0 + sk, a[1]], [b[0], F0 + sk, b[1]], [B2[0], F0 + sk, B2[1]], [A2[0], F0 + sk, A2[1]], T, shade * 1.05); }
      }
      walls++;
      if (K.top && !tops.has(key) && index[K.top] !== undefined && !(CM.FENCE_MODEL && K === CM.SOLID.hedge)) { tops.add(key); quad([nx, h, ny + 1], [nx + 1, h, ny + 1], [nx + 1, h, ny], [nx, h, ny], index[K.top], 0.95); }
    });
  }
  if (!sky && !only && index["trim:stone"] !== undefined) for (const [k, f] of Object.entries(features)) {   // (v48.3) a stone lintel over every doorway and gate
    if (f.type !== "door" && f.type !== "gate") continue; const [x, y] = k.split(",").map(Number); if (!openAt(x, y)) continue;
    const ns = openAt(x, y - 1) && openAt(x, y + 1), C = CM.ceilAt ? CM.ceilAt(fl, x, y) : 1, lo = C - 0.13, T = index["trim:stone"], dd = 0.07, cx = x + 0.5, cz = y + 0.5;
    if (ns) { for (const z of [cz - dd, cz + dd]) quad([x, lo, z], [x + 1, lo, z], [x + 1, C, z], [x, C, z], T, 0.9); quad([x, lo, cz - dd], [x + 1, lo, cz - dd], [x + 1, lo, cz + dd], [x, lo, cz + dd], T, 0.7); }
    else { for (const X of [cx - dd, cx + dd]) quad([X, lo, y], [X, lo, y + 1], [X, C, y + 1], [X, C, y], T, 0.84); quad([cx - dd, lo, y], [cx - dd, lo, y + 1], [cx + dd, lo, y + 1], [cx + dd, lo, y], T, 0.7); } }
  let buildings = 0, chimneys = 0, litWindows = 0, towers = 0; const windows = [];   // (windows: where each lit one is, for its light: v22.0)
  if (sky && only !== "props") {                                                        // the buildings: walled all round, and roofed
    const polyNear = (n) => (W ? () => {} : (P, uv, layer, shade) => { for (const i of (P.length === 4 ? [0, 1, 2, 0, 2, 3] : [0, 1, 2])) out.push(...P[i], uv[i][0], uv[i][1], layer, shade, 10 + n, 1, 0); }), poly18 = polyNear(18);   // (v58.1)
    const poly = W ? () => {} : (P, uv, layer, shade) => { for (const i of (P.length === 4 ? [0, 1, 2, 0, 2, 3] : [0, 1, 2])) out.push(...P[i], uv[i][0], uv[i][1], layer, shade, 0, 1, 0); };
    const stone = L("solid:townwall"), gable = index["solid:gable"] !== undefined ? index["solid:gable"] : L("solid:house"), roofDefault = L("solid:roof");
    const FACES = [[0, -1, 1.0], [0, 1, 0.96], [1, 0, 0.84], [-1, 0, 0.8]];        // a cell's north, south, east and west faces
    const tone = new Map(); for (const B of CM.buildingsOf(fl)) { const k = 0.76 + ((CM.hashSeed(`${fl.number}:tone:${B.x0},${B.y0}`) >>> 0) % 31) / 100; for (let by = B.y0; by <= B.y1; by++) for (let bx = B.x0; bx <= B.x1; bx++) tone.set(`${bx},${by}`, k); }   // (v51.0: each house its own wash, lighter or darker)
    for (let y = 0; y < size; y++) for (let x = 0; x < size; x++) {
      if (!CM.isBuilding(fl, x, y)) continue;
      const kind = CM.solidAt(fl, x, y), K = CM.SOLID[kind], wash = tone.get(`${x},${y}`) || 1;
      // a door or a shop shows its face once, toward the open square that has the building behind it
      let front = -1;
      const doorish = ["door", "shop", "cabindoor", "casinodoor"].includes(kind);
      if (doorish) FACES.forEach(([dx, dy], d) => { if (front < 0 && openAt(x + dx, y + dy) && CM.isBuilding(fl, x - dx, y - dy)) front = d; });
      if (doorish && front < 0) FACES.forEach(([dx, dy], d) => { if (front < 0 && openAt(x + dx, y + dy)) front = d; });
      FACES.forEach(([dx, dy, shade], d) => {
        if (CM.isBuilding(fl, x + dx, y + dy)) return;                                // (inside the building)
        const a = d === 0 ? [x + 1, y] : d === 1 ? [x, y + 1] : d === 2 ? [x + 1, y + 1] : [x, y];
        const b = d === 0 ? [x, y] : d === 1 ? [x + 1, y + 1] : d === 2 ? [x + 1, y] : [x, y + 1];
        const layer = d === front ? L(K.face) : L(K.side || "solid:house"), h = K.h;
        poly([[a[0], 0, a[1]], [b[0], 0, b[1]], [b[0], h, b[1]], [a[0], h, a[1]]], [[0, 1], [1, 1], [1, 0], [0, 0]], layer, shade * wash);
        if (["house", "door", "shop"].includes(kind) && opts.detail !== 0) { if (CM.ivyDetail) CM.ivyDetail({ poly, index, x, y, d, a, b, dx, dy, h, shade }); if (CM.buildingDetail) CM.buildingDetail({ poly: poly18, index, fl, x, y, d, a, b, dx, dy, h, shade, wash, kind, front: d === front }); }   // (v53.0: sills, lintels, reveals - 26b-buildings.js)
        if (opts.night && index["window:lit"] !== undefined && (kind === "house" || d !== front || kind === "door") && CM.hashSeed(`${fl.number}:lit:${x},${y}:${d}`) % 100 < (opts.night === true ? 0.7 : opts.night) * 100) {   // a window lit for the night (v24.3: opts.night the share lit - fewer as the town goes to bed)
          const win = d === front ? (kind === "door" ? [0.74, 0.36, 0.9, 0.56] : null) : [0.62, 0.3, 0.84, 0.56];
          if (win) { const ax0 = a[0] + (b[0] - a[0]) * win[0], az0 = a[1] + (b[1] - a[1]) * win[0], ax1 = a[0] + (b[0] - a[0]) * win[2], az1 = a[1] + (b[1] - a[1]) * win[2], y0 = h * (1 - win[3]), y1 = h * (1 - win[1]), q = 0.012;
            const P = [[ax0 + dx * q, y0, az0 + dy * q], [ax1 + dx * q, y0, az1 + dy * q], [ax1 + dx * q, y1, az1 + dy * q], [ax0 + dx * q, y1, az0 + dy * q]], uv = [[0, 1], [1, 1], [1, 0], [0, 0]];
            for (const i of [0, 1, 2, 0, 2, 3]) out.push(...P[i], uv[i][0], uv[i][1], index["window:lit"], 1, 0, 1, 1);
            litWindows++; windows.push([(ax0 + ax1) / 2 + dx * 0.35, (y0 + y1) / 2, (az0 + az1) / 2 + dy * 0.35]); }
        }
        const o = 0.035, ox = dx * o, oz = dy * o, ft = 0.16;                        // the footing: a course of stone, standing a little proud
        poly([[a[0] + ox, 0, a[1] + oz], [b[0] + ox, 0, b[1] + oz], [b[0] + ox, ft, b[1] + oz], [a[0] + ox, ft, a[1] + oz]], [[0, 1], [1, 1], [1, 1 - ft], [0, 1 - ft]], stone, shade * 0.8);
        poly([[a[0] + ox, ft, a[1] + oz], [b[0] + ox, ft, b[1] + oz], [b[0], ft, b[1]], [a[0], ft, a[1]]], [[0, 0.1], [1, 0.1], [1, 0], [0, 0]], stone, shade * 0.95);
        walls++;
      });
    }
    for (const B of CM.buildingsOf(fl)) {
      buildings++;
      const RK = CM.SOLID[CM.solidAt(fl, B.x0, B.y0)] || {}, roofL = RK.roof && index[RK.roof] !== undefined ? index[RK.roof] : roofDefault;   // (a building's own roof: the Gilded Joker's copper)
      const X0 = B.x0, X1 = B.x1 + 1, Z0 = B.y0, Z1 = B.y1 + 1, h = B.h, top = h + B.rise, o = B.overhang, g = CM.ROOF.gableOverhang;
      // in the roof's own frame: u along the ridge, v across it (0 at one eave line, span at the other); P(u, v, y) back to the world
      const ax = B.along === "x", U0 = ax ? X0 : Z0, U1 = ax ? X1 : Z1, V0 = ax ? Z0 : X0, V1 = ax ? Z1 : X1, mid = (V0 + V1) / 2, half = (V1 - V0) / 2;
      const P = (u, v, yy) => (ax ? [u, yy, v] : [v, yy, u]);
      const eaveY = h - (o * B.rise) / half, slope = Math.hypot(half + o, B.rise), rows = Math.max(1, Math.round(slope));
      const segs = [[U0 - g, U0]]; for (let u = U0; u < U1; u++) segs.push([u, u + 1]); segs.push([U1, U1 + g]);
      for (const side of [-1, 1]) {                                                   // the two slopes, eave to ridge, a tile a square
        const vEave = mid + side * (half + o), shade = (ax ? side < 0 : side > 0) ? 1.05 : 0.86;
        for (const [ua, ub] of segs) for (let r = 0; r < rows; r++) {
          const t0 = r / rows, t1 = (r + 1) / rows, va = vEave + (mid - vEave) * t0, vb = vEave + (mid - vEave) * t1, ya = eaveY + (top - eaveY) * t0, yb = eaveY + (top - eaveY) * t1, w = ub - ua;
          poly([P(ua, va, ya), P(ub, va, ya), P(ub, vb, yb), P(ua, vb, yb)], [[0, 1], [w, 1], [w, 0], [0, 0]], roofL, shade);
          roofs++;
        }
        poly([P(U0 - g, vEave, eaveY), P(U1 + g, vEave, eaveY), P(U1 + g, vEave, eaveY - 0.06), P(U0 - g, vEave, eaveY - 0.06)], [[0, 0.1], [1, 0.1], [1, 0], [0, 0]], roofL, 0.55);   // (the eave's edge)
      }
      for (const side of [-1, 1]) for (const [ua, ub] of segs) {                    // the ridge cap: a fold of darker tiles along the top
        const w = 0.09, lift = 0.035, vOut = mid + side * w, yOut = top - (w * B.rise) / half + lift;
        poly([P(ua, vOut, yOut), P(ub, vOut, yOut), P(ub, mid, top + lift + 0.02), P(ua, mid, top + lift + 0.02)], [[0, 0.2], [ub - ua, 0.2], [ub - ua, 0], [0, 0]], roofL, 0.62);
      }
      for (const u of [U0, U1]) {                                                     // the gable ends: plaster and timber up to the ridge, a strip a square
        const cuts = [V0]; for (let v = V0 + 1; v < V1; v++) cuts.push(v); if (!cuts.includes(mid)) cuts.push(mid); cuts.push(V1); cuts.sort((p, q) => p - q);
        const roofY = (v) => h + B.rise * (1 - Math.abs(v - mid) / half), shade = ax ? 0.84 : 1.0, BK = CM.SOLID[CM.solidAt(fl, B.x0, B.y0)] || {}, gableL = BK.gable && index[BK.gable] !== undefined ? L(BK.gable) : gable;
        for (let i = 0; i + 1 < cuts.length; i++) {
          const va = cuts[i], vb = cuts[i + 1], ua = (va - Math.floor(va)), ub = vb - Math.floor(va) > 1 ? 1 : vb - Math.floor(va);
          poly([P(u, va, h), P(u, vb, h), P(u, vb, roofY(vb)), P(u, va, roofY(va))], [[ua, 1], [ub, 1], [ub, 1 - (roofY(vb) - h)], [ua, 1 - (roofY(va) - h)]], gableL, shade);
        }
      }
      if (CM.roofDetail && opts.detail !== 0 && !RK.side) CM.roofDetail({ poly, index, fl, B, P, U0, U1, V0, V1, mid, half, h, top, eaveY, o, g, roofL });   // (v53.6: eaves, dormers, gutters - 26b-buildings.js)
    }
    for (const [tk, tkind] of Object.entries(fl.kinds || {})) {                        // the gate towers: eight faces of stone, a top, and a merlon on each face
      if (tkind === "magetower" && W) continue;
      if (tkind === "magetower") { const [mx, my] = tk.split(",").map(Number); if (mx === CM.MAGE_TOWER.at[0] && my === CM.MAGE_TOWER.at[1]) { mageTower(mx, my); towers++; } continue; }
      if (tkind !== "tower") continue;
      const [tx, ty] = tk.split(",").map(Number), cx = tx + 0.5, cz = ty + 0.5, T = CM.TOWER, H = T.h, R = T.r, top = L("solid:townwall:top");
      const at = (i, r) => { const a = (Math.PI / 4) * i + Math.PI / 8; return [cx + Math.cos(a) * r, cz + Math.sin(a) * r]; };
      for (let i = 0; i < 8; i++) {
        const [ax, az] = at(i, R), [bx, bz] = at(i + 1, R), shade = 0.78 + 0.22 * Math.abs(Math.cos((Math.PI / 4) * i + Math.PI / 4));
        for (const [y0, y1] of [[0, H / 2], [H / 2, H]]) poly([[ax, y0, az], [bx, y0, bz], [bx, y1, bz], [ax, y1, az]], [[0, 1], [0.5, 1], [0.5, 0], [0, 0]], stone, shade);
        poly([[cx, H, cz], [ax, H, az], [bx, H, bz]], [[0.5, 0.5], [0, 0], [1, 0]], top, 0.9);   // (the top, a fan)
        const m = 0.2, [mx0, mz0] = [ax + (bx - ax) * m, az + (bz - az) * m], [mx1, mz1] = [ax + (bx - ax) * (1 - m), az + (bz - az) * (1 - m)], k = (R - 0.1) / R;   // a merlon on this face
        const [ix0, iz0, ix1, iz1] = [cx + (mx0 - cx) * k, cz + (mz0 - cz) * k, cx + (mx1 - cx) * k, cz + (mz1 - cz) * k], Y = H + T.merlon;
        poly([[mx0, H, mz0], [mx1, H, mz1], [mx1, Y, mz1], [mx0, Y, mz0]], [[0, 1], [0.3, 1], [0.3, 0.7], [0, 0.7]], stone, shade);
        poly([[ix1, H, iz1], [ix0, H, iz0], [ix0, Y, iz0], [ix1, Y, iz1]], [[0, 1], [0.3, 1], [0.3, 0.7], [0, 0.7]], stone, shade * 0.85);
        poly([[mx0, Y, mz0], [mx1, Y, mz1], [ix1, Y, iz1], [ix0, Y, iz0]], [[0, 0.1], [0.3, 0.1], [0.3, 0], [0, 0]], top, 0.95);
        poly([[ix0, H, iz0], [mx0, H, mz0], [mx0, Y, mz0], [ix0, Y, iz0]], [[0, 1], [0.1, 1], [0.1, 0.7], [0, 0.7]], stone, shade * 0.8);
        poly([[mx1, H, mz1], [ix1, H, iz1], [ix1, Y, iz1], [mx1, Y, mz1]], [[0, 1], [0.1, 1], [0.1, 0.7], [0, 0.7]], stone, shade * 0.8);
        walls++;
      }
      towers++;
    }
    // the Mage Tower: seven stories of black stone, a band at each, faint windows, a slate cone, two dark doors
    function mageTower(tx, ty) {
      const T = CM.MAGE_TOWER, cx = tx + 0.5, cz = ty + 0.5, R = T.r, H = T.h, story = H / T.stories, ms = L("solid:magestone"), win = index["window:arcane"], door = L("solid:magedoor");
      const at = (i, r) => { const a = (Math.PI / 4) * i + Math.PI / 8; return [cx + Math.cos(a) * r, cz + Math.sin(a) * r]; };
      for (let i = 0; i < 8; i++) {
        const [ax, az] = at(i, R), [bx, bz] = at(i + 1, R), na = (Math.PI / 4) * i + Math.PI / 4, nx = Math.cos(na), nz = Math.sin(na), shade = 0.62 + 0.3 * Math.abs(Math.cos(na + 0.6));
        for (let s = 0; s < T.stories; s++) {
          const y0 = s * story, y1 = (s + 1) * story;
          poly([[ax, y0, az], [bx, y0, bz], [bx, y1, bz], [ax, y1, az]], [[0, 1], [1, 1], [1, 0], [0, 0]], ms, shade);
          const q = 0.05; poly([[ax + nx * q, y1 - 0.08, az + nz * q], [bx + nx * q, y1 - 0.08, bz + nz * q], [bx + nx * q, y1, bz + nz * q], [ax + nx * q, y1, az + nz * q]], [[0, 0.1], [1, 0.1], [1, 0], [0, 0]], ms, shade * 0.6);   // (a band of darker stone at each story)
          if (win !== undefined && s > 0 && CM.hashSeed(`magetower:win:${i}:${s}`) % 3 === 0) { const m0 = 0.42, m1 = 0.58, w0x = ax + (bx - ax) * m0, w0z = az + (bz - az) * m0, w1x = ax + (bx - ax) * m1, w1z = az + (bz - az) * m1, wy0 = y0 + story * 0.3, wy1 = y0 + story * 0.75, p = 0.01;
            const P = [[w0x + nx * p, wy0, w0z + nz * p], [w1x + nx * p, wy0, w1z + nz * p], [w1x + nx * p, wy1, w1z + nz * p], [w0x + nx * p, wy1, w0z + nz * p]], uv = [[0, 1], [1, 1], [1, 0], [0, 0]];
            for (const j of [0, 1, 2, 0, 2, 3]) out.push(...P[j], uv[j][0], uv[j][1], win, 1, 0, 1, 0.55); }   // (a narrow window, faintly lit)
        }
        if (i === 1) { const d0 = 0.16, d1 = 0.84, p = 0.025, top = 1.95, [x0d, z0d, x1d, z1d] = [ax + (bx - ax) * d0, az + (bz - az) * d0, ax + (bx - ax) * d1, az + (bz - az) * d1];   // the two doors, on the face that looks south down the path
          poly([[x0d + nx * p, 0, z0d + nz * p], [x1d + nx * p, 0, z1d + nz * p], [x1d + nx * p, top, z1d + nz * p], [x0d + nx * p, top, z0d + nz * p]], [[0, 1], [1, 1], [1, 0], [0, 0]], door, 0.95); }
        const [rx0, rz0] = at(i, R + 0.18), [rx1, rz1] = at(i + 1, R + 0.18);   // the slate cone
        poly([[rx0, H, rz0], [rx1, H, rz1], [cx, H + T.roof, cz]], [[0, 1], [1, 1], [0.5, 0]], L("solid:roof"), 0.42 + 0.25 * Math.abs(Math.cos(na)));
        poly([[ax, H, az], [bx, H, bz], [rx1, H, rz1], [rx0, H, rz0]], [[0, 0.1], [1, 0.1], [1, 0], [0, 0]], ms, 0.4);
        walls++;
      }
    }
    for (const C of CM.chimneysOf(fl)) {                                               // the chimneys: a stack of stone, and a cap
      const r = C.w / 2, x0 = C.x - r, x1 = C.x + r, z0 = C.z - r, z1 = C.z + r, uv = [[0, 1], [0.3, 1], [0.3, 0.3], [0, 0.3]];
      poly([[x1, C.base, z0], [x0, C.base, z0], [x0, C.top, z0], [x1, C.top, z0]], uv, stone, 0.95);
      poly([[x0, C.base, z1], [x1, C.base, z1], [x1, C.top, z1], [x0, C.top, z1]], uv, stone, 0.9);
      poly([[x1, C.base, z1], [x1, C.base, z0], [x1, C.top, z0], [x1, C.top, z1]], uv, stone, 0.8);
      poly([[x0, C.base, z0], [x0, C.base, z1], [x0, C.top, z1], [x0, C.top, z0]], uv, stone, 0.76);
      const c = 0.03; poly([[x0 - c, C.top, z0 - c], [x1 + c, C.top, z0 - c], [x1 + c, C.top, z1 + c], [x0 - c, C.top, z1 + c]], [[0, 0.1], [0.3, 0.1], [0.3, 0], [0, 0]], index["solid:townwall:top"] !== undefined ? index["solid:townwall:top"] : stone, 0.5);
      chimneys++;
    }
  }
  if (sky && only !== "props") {                                                       // past the edge: a skirt of grass, and the far ring standing on it
    const E = CM.SKIRT, B = 4, grass = L("ground:grass");
    const band = (x0, y0, x1, y1) => { for (let y = y0; y < y1; y += B) for (let x = x0; x < x1; x += B) { const xe = Math.min(x + B, x1), ye = Math.min(y + B, y1); quad([x, -0.002, ye], [xe, -0.002, ye], [xe, -0.002, y], [x, -0.002, y], grass, 0.8); skirt++; } };
    band(-E, -E, size + E, 0); band(-E, size, size + E, size + E); band(-E, 0, 0, size); band(size, 0, size + E, size);
    const far = (side) => L(fl.number === -1 && side === 1 && !CM.FARVIEW ? "far:hill" : "far:trees"), RW = 8, H = 7;   // (from the land, the town's hill stands in the east; v51.1: RW, not W - W is the windows pass, and shadowing it kept every far view out)
    for (let t = -E; t < size + E; t += RW) {
      const t1 = Math.min(t + RW, size + E);
      quad([t, 0, -E], [t1, 0, -E], [t1, H, -E], [t, H, -E], far(0), 0.7);                          // north
      quad([t1, 0, size + E], [t, 0, size + E], [t, H, size + E], [t1, H, size + E], far(2), 0.7);  // south
      quad([size + E, 0, t], [size + E, 0, t1], [size + E, H, t1], [size + E, H, t], far(1), 0.7);  // east
      quad([-E, 0, t1], [-E, 0, t], [-E, H, t], [-E, H, t1], far(3), 0.7);                          // west
      ring += 4;
    }
    if (CM.farViews) CM.farViews(fl, size, index, opts.night === true ? 0.7 : opts.night || 0, (a, b, c, d, layer, shade, glow) => { if (W !== (glow === 2)) return; const uv = [[0, 1], [1, 1], [1, 0], [0, 0]]; for (const i of [0, 1, 2, 0, 2, 3]) out.push(...[a, b, c, d][i], uv[i][0], uv[i][1], layer, shade, 0, 1, glow); });   // (v24.4: what lies beyond, where it lies - 76zzzzg-farviews.js)
  }
  let felled = 0;
  if (!only) for (const key of trees) {                                                            // two crossed pictures a tree, of the seed's three
    const [x, y] = key.split(",").map(Number), v = CM.hashSeed(`${fl.number}:tree:${key}`) % 3, h = CM.SOLID.tree.h, cx = x + 0.5, cz = y + 0.5, r = 0.62;
    const was = opts.turn !== undefined && opts.turn < 1 && (CM.hashSeed(`${fl.number}:turn:${key}`) % 100) / 100 >= opts.turn && index[`tree:${v}:was`] !== undefined;   // (v24.2: not turned yet)
    const layer = L(was ? `tree:${v}:was` : `tree:${v}`), st = opts.treeStates && opts.treeStates[key];   // (v74.0: a tree's state - fallen, burning, charred, a sapling - 69zzm-trees.js)
    if (st === "fallen" || st === "charred") {   // a log lying across the square the way the hash says, and for a charred one black, over ash
      const bark = index["solid:bark"] !== undefined ? index["solid:bark"] : L("solid:timber"), a = (CM.hashSeed(`${fl.number}:fell:${key}`) % 4) * Math.PI / 4, dx = Math.cos(a), dz = Math.sin(a), px = -dz, pz = dx, k = st === "charred" ? 0.22 : 0.9, hh = 0.14, w = 0.13, len = 0.52;
      const C = (u, s, y) => [cx + dx * u + px * s, y, cz + dz * u + pz * s];
      quad(C(-len, w, 0), C(len, w, 0), C(len, w, hh * 2), C(-len, w, hh * 2), bark, k * 0.95); quad(C(len, -w, 0), C(-len, -w, 0), C(-len, -w, hh * 2), C(len, -w, hh * 2), bark, k * 0.8);
      quad(C(-len, -w, hh * 2), C(len, -w, hh * 2), C(len, w, hh * 2), C(-len, w, hh * 2), bark, k * 1.05); quad(C(len, w, 0), C(len, -w, 0), C(len, -w, hh * 2), C(len, w, hh * 2), bark, k * 0.7); quad(C(-len, -w, 0), C(-len, w, 0), C(-len, w, hh * 2), C(-len, -w, hh * 2), bark, k * 0.7);
      if (st === "charred") quad([cx - 0.48, 0.004, cz + 0.48], [cx + 0.48, 0.004, cz + 0.48], [cx + 0.48, 0.004, cz - 0.48], [cx - 0.48, 0.004, cz - 0.48], L("ground:dirt"), 0.18);   // (the ash)
      felled++; continue; }
    const k = st === "sapling" ? 0.3 : 1, hs = h * k, rs = r * (st === "sapling" ? 0.45 : 1), burnt = st === "burning" ? 0.85 : 1;   // (a sapling: the same picture, small; burning: a little darker under the flames)
    quad([cx - rs, 0, cz + rs], [cx + rs, 0, cz - rs], [cx + rs, hs, cz - rs], [cx - rs, hs, cz + rs], layer, burnt, CM.SWAY.tree * k);
    quad([cx - rs, 0, cz - rs], [cx + rs, 0, cz + rs], [cx + rs, hs, cz + rs], [cx - rs, hs, cz - rs], layer, burnt, CM.SWAY.tree * k);
  }
  let craters = 0;   // (v75.0: a meteor's crater - a scorched square and a raised rim of eight wedges, fading over the days - 69zzn-meteors.js)
  if (sky && !only && opts.craters) for (const [key, days] of Object.entries(opts.craters)) { const [x, y] = key.split(",").map(Number); if (!CM.inBounds(fl, x, y) || fl.grid[y][x] !== 0) continue; const cx = x + 0.5, cz = y + 0.5, f = Math.max(0, 1 - days / 10), dirt = L("ground:dirt");
    quad([cx - 0.5, 0.005, cz + 0.5], [cx + 0.5, 0.005, cz + 0.5], [cx + 0.5, 0.005, cz - 0.5], [cx - 0.5, 0.005, cz - 0.5], dirt, 0.12 + 0.5 * (1 - f));
    for (let i = 0; i < 8; i++) { const a0 = i * Math.PI / 4, a1 = a0 + Math.PI / 4, ri = 0.26, ro = 0.46, h = 0.09 * (0.4 + 0.6 * f), P = (a, r, y) => [cx + Math.cos(a) * r, y, cz + Math.sin(a) * r];
      quad(P(a0, ri, 0.006), P(a0, ro, h), P(a1, ro, h), P(a1, ri, 0.006), dirt, 0.3 + 0.25 * (1 - f)); quad(P(a0, ro, h), P(a0, ro + 0.06, 0.006), P(a1, ro + 0.06, 0.006), P(a1, ro, h), dirt, 0.5 + 0.2 * (1 - f)); }
    craters++; }
  const wood = sky && !only && CM.woodDetail ? CM.woodDetail({ quad: near(12), fl, index, trees, openAt, features, size, detail: opts.detail }) : { roots: 0, stumps: 0, rocks: 0 };   // (v55.3: roots, stumps, rocks - 26e-wooddetail.js)
  const wells = sky && !only && !W && CM.wellModel ? CM.wellModel({ quad, out, fl, index }) : 0;   // (v56.1: the well, built - 26f-well.js)
  const washing = sky && !only && !W && CM.washingModel ? CM.washingModel({ quad: near(20), fl, index, season: opts.season }) : 0;   // (v61.0: washing on the line behind the houses - 26k-washing.js)
  const fencing = sky && !only && !W && CM.fenceModel ? CM.fenceModel({ quad: near(28), fl, index, size, solidKind: (x, y) => (x < 0 || y < 0 || x >= size || y >= size || grid[y][x] === 0 ? null : CM.solidAt(fl, x, y)) }) : { fences: 0, hedges: 0 };   // (v56.2 - 26g-fences.js)
  const walled = sky && !only && !W && CM.wallDetail && fl.number === 0 ? CM.wallDetail({ quad, fl, index, size, detail: opts.detail, solidKind: (x, y) => (x < 0 || y < 0 || x >= size || y >= size ? "edge" : grid[y][x] === 0 ? null : CM.solidAt(fl, x, y)) }) : { merlons: 0, buttresses: 0, slits: 0, gate: 0 };   // (v57.0: battlements - 26i-wall.js)
  const shaftHead = sky && !only && !W && CM.shaftHead ? CM.shaftHead({ quad, fl, index }) : 0;   // (v57.3: the shaft head, built - 26j-shaft.js)
  let decals = 0, overhead = 0;
  if (!sky && opts.decals !== false && !only) {                                                   // below: what is on the walls, and what hangs overhead, by band
    const band = CM.themeIndex(fl.number >= 1 ? fl.number : 1), D = CM.WALL_DECALS[band] || [], O = CM.OVERHEAD[band];
    for (let y = 0; y < size; y++) for (let x = 0; x < size; x++) {
      if (grid[y][x] !== 0) continue;
      const here = features[`${x},${y}`];
      SIDES.forEach(([dx, dy], d) => {
        const nx = x + dx, ny = y + dy;
        if (!solid(nx, ny) || CM.solidAt(fl, nx, ny) !== "wall") return;
        const beyond = features[`${nx},${ny}`];
        if (beyond && (beyond.type === "secret" || beyond.type === "secretstair")) return;          // (never give a hidden door away)
        if (here && (here.type === "lever" || here.type === "carving") && here.face === d) return;
        const h = CM.hashSeed(`${fl.number}:decal:${x},${y}:${d}`);
        for (const [id, per] of D) {
          if ((h % 1000) / 1000 >= per) continue;
          const layer = index[`decal:${id}`]; if (layer === undefined) break;
          const lvF = CM.floorAt ? CM.floorAt(fl, x, y) : 0, lvC = CM.ceilAt ? CM.ceilAt(fl, x, y) : 1, inset = 0.006, px = x + 0.5 + dx * (0.5 - inset), pz = y + 0.5 + dy * (0.5 - inset), ax = -dy, az = dx, w = 0.9, y0 = lvF + 0.02, y1 = lvF + 0.98 * (lvC - lvF);
          quad([px - ax * w / 2, y0, pz - az * w / 2], [px + ax * w / 2, y0, pz + az * w / 2], [px + ax * w / 2, y1, pz + az * w / 2], [px - ax * w / 2, y1, pz - az * w / 2], layer, d < 2 ? 1 : 0.84);
          decals++; break;
        }
      });
      if (O && index[`over:${O.id}`] !== undefined && (CM.hashSeed(`${fl.number}:over:${x},${y}`) % 1000) / 1000 < O.per) {
        const layer = index[`over:${O.id}`], t = CM.hashSeed(`${fl.number}:overturn:${x},${y}`) % 2;
        if (O.how === "beam") {                                                         // a timber across the corridor under the ceiling
          const yb = O.id === "rib" ? 0.96 : 0.92, yt = 0.998;                          // (the Palace's ribs thin and high)
          if (t) { quad([x, yb, y + 0.42], [x + 1, yb, y + 0.42], [x + 1, yt, y + 0.42], [x, yt, y + 0.42], layer, 0.8); quad([x + 1, yb, y + 0.58], [x, yb, y + 0.58], [x, yt, y + 0.58], [x + 1, yt, y + 0.58], layer, 0.8); quad([x, yb, y + 0.58], [x + 1, yb, y + 0.58], [x + 1, yb, y + 0.42], [x, yb, y + 0.42], layer, 0.6); }
          else { quad([x + 0.42, yb, y + 1], [x + 0.42, yb, y], [x + 0.42, yt, y], [x + 0.42, yt, y + 1], layer, 0.8); quad([x + 0.58, yb, y], [x + 0.58, yb, y + 1], [x + 0.58, yt, y + 1], [x + 0.58, yt, y], layer, 0.8); quad([x + 0.42, yb, y], [x + 0.58, yb, y], [x + 0.58, yb, y + 1], [x + 0.42, yb, y + 1], layer, 0.6); }
        } else {                                                                          // hanging from the ceiling: two crossed pictures
          const cx = x + 0.5 + ((CM.hashSeed(`${fl.number}:overx:${x},${y}`) % 40) - 20) / 100, cz = y + 0.5 + ((CM.hashSeed(`${fl.number}:overz:${x},${y}`) % 40) - 20) / 100, r = O.w / 2, top = CM.ceilAt ? CM.ceilAt(fl, x, y) : 1, bot = 1 - O.h;
          quad([cx - r, bot, cz], [cx + r, bot, cz], [cx + r, top, cz], [cx - r, top, cz], layer, 0.8);
          quad([cx, bot, cz - r], [cx, bot, cz + r], [cx, top, cz + r], [cx, top, cz - r], layer, 0.8);
        }
        overhead++;
      }
    }
  }
  let props = 0;                                                                        // the props that lie or grow: flat, and crossed pairs
  const sub = opts.sub || {};
  const quadUV = (a, b, c, d, layer, shade, r, sway = 0) => { const uv = [[r[0], r[3]], [r[2], r[3]], [r[2], r[1]], [r[0], r[1]]]; for (const i of [0, 1, 2, 0, 2, 3]) out.push(...[a, b, c, d][i], uv[i][0], uv[i][1], layer, shade, i >= 2 ? -sway : 0, 1, 0); };
  for (const p of W ? [] : opts.props || []) {
    if (p.how === "stand") { if (p.id === "lamp" && CM.lampModel && CM.lampModel(p, near(16), index)) props++; continue; }   // (v56.3: the lamp's post and lantern built - 26h-lamps.js; its glass stays a picture, lit by the lamplighter)
    if (p.how === "model") { if (CM.propModel && CM.propModel(p, (a, b, c, d, layer, shade, uvr) => quadUV(a, b, c, d, layer, shade, uvr || [0, 0, 1, 1]), index)) props++; continue; }   // (v24.5: built solid - 76zzzzh-models.js)
    const s = sub[p.layer], layer = s ? index[s[0]] : index[p.layer], r = s ? s.slice(1) : [0, 0, 1, 1];
    if (layer === undefined) continue;
    const cx = p.x + 0.5 + p.dx, cz = p.y + 0.5 + p.dz, c = Math.cos(p.turn), sn = Math.sin(p.turn), hw = p.w / 2, shade = sky && canopy.has(`${p.x},${p.y}`) ? 0.55 : 0.9;
    if (p.how === "corner") {                                                       // across an upper corner, from one wall to the other, under the ceiling
      const [sx, sz] = p.corner, kx = p.x + 0.5 + sx * 0.5, kz = p.y + 0.5 + sz * 0.5, top = (!sky && CM.ceilAt ? CM.ceilAt(fl, p.x, p.y) : 1) - 0.01, bottom = top - p.h * 0.6;
      const A = [kx - sx * p.w, kz], B = [kx, kz - sz * p.w];
      quadUV([A[0], bottom, A[1]], [B[0], bottom, B[1]], [B[0], top, B[1]], [A[0], top, A[1]], layer, 0.85, r);
      props++; continue;
    }
    if (p.how === "flat") {
      const pf = !sky && CM.floorAt ? CM.floorAt(fl, p.x, p.y) : 0, at = (u, v) => [cx + u * c - v * sn, pf + 0.006 + (props % 7) * 0.0006, cz + u * sn + v * c];
      quadUV(at(-hw, hw), at(hw, hw), at(hw, -hw), at(-hw, -hw), layer, shade, r);
    } else for (const t of [p.turn, p.turn + Math.PI / 2]) {
      const ux = Math.cos(t) * hw, uz = Math.sin(t) * hw;
      const pf = !sky && CM.floorAt ? CM.floorAt(fl, p.x, p.y) : 0; quadUV([cx - ux, pf, cz - uz], [cx + ux, pf, cz + uz], [cx + ux, pf + p.h, cz + uz], [cx - ux, pf + p.h, cz - uz], layer, shade, r, sky ? CM.SWAY[p.id] || CM.SWAY.plant : 0);
    }
    props++;
  }
  return { data: out, count: out.length / CM.MESH_STRIDE, ceilings, walls, roofs, buildings, chimneys, litWindows, windows, towers, trees: trees.size, wood, wells, washing, felled, craters, fencing, walled, shaftHead, covered: covered.size, skirt, ring, props, decals, overhead };
};
