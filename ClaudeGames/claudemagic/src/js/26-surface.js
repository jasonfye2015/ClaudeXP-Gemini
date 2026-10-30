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
  hedge: { face: "solid:hedge", h: 0.55, top: "solid:hedge", see: true },         // seen over
  fence: { face: "solid:fence", h: 0.5, see: true },                              // seen through
  cliff: { face: "solid:cliff", h: 2.2, top: "ground:grass" },                    // the hill's side
  tree: { tree: true, h: 1.7, see: true },                                        // not a wall: a trunk and a crown, two crossed pictures
};
CM.SOLID_COLOURS = { wall: "#3A3028", house: "#8A6A48", door: "#A0784A", shop: "#A0784A", frame: "#B09060", townwall: "#6E6A62", hedge: "#5C8A3C", fence: "#A08860", cliff: "#4A4038", tree: "#3F6B32" };
CM.GROUNDS = ["grass", "dirt", "cobbles", "flags", "planks", "tilled", "moss", "litter", "needles"];   // (litter and needles: under the trees, the trunk's shade at the middle)
CM.UNDER = ["tree", "hedge", "fence", "frame"];                          // the solid kinds the ground runs under on the surface
CM.SKIRT = 40;                                                          // how far past the map's edge the ground runs, and the far silhouettes stand
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
  if (h >= dawn - 1 && h < dawn) { sky = blend(S.night, S.dawn, h - (dawn - 1)); word = "dawn"; }
  else if (h >= dawn && h < dawn + 1.5) { sky = blend(S.dawn, S.day, (h - dawn) / 1.5); word = "dawn"; }
  else if (h >= dawn + 1.5 && h < dusk - 1.5) { sky = blend(S.day, S.day, 0); word = "day"; }
  else if (h >= dusk - 1.5 && h < dusk) { sky = blend(S.day, S.dusk, (h - (dusk - 1.5)) / 1.5); word = "dusk"; }
  else if (h >= dusk && h < dusk + 1) { sky = blend(S.dusk, S.night, h - dusk); word = "dusk"; }
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
CM.floorMesh = function (fl, theme, index, opts = {}) {                 // opts: { props (CM.scatter's), sub (where each prop sits in its layer) }
  const grid = fl.grid, size = grid.length, out = [], features = fl.features || {}, sky = Boolean(theme.sky), canopy = new Set(fl.canopy || []);
  const L = (name) => (index[name] !== undefined ? index[name] : index.wall);
  const quad = (a, b, c, d, layer, shade) => { const uv = [[0, 1], [1, 1], [1, 0], [0, 0]]; for (const i of [0, 1, 2, 0, 2, 3]) out.push(...[a, b, c, d][i], uv[i][0], uv[i][1], layer, shade, 0, 1, 0); };
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
  for (let y = 0; y < size; y++) for (let x = 0; x < size; x++) {
    if (grid[y][x] !== 0) {
      if (!sky) continue;                                                       // (below: rock is rock)
      const kind = CM.solidAt(fl, x, y), K = CM.SOLID[kind] || CM.SOLID.wall, key = `${x},${y}`;
      if (CM.UNDER.includes(kind)) {                                            // the ground runs on under it: needles or litter under a tree, else the grass
        const g = kind === "tree" ? (CM.treeVariant(fl, x, y) === 1 ? "needles" : "litter") : CM.groundAt(fl, x, y) || "grass";
        quad([x, 0, y + 1], [x + 1, 0, y + 1], [x + 1, 0, y], [x, 0, y], L(`ground:${g}`), kind === "tree" ? 0.6 : 0.85); covered.add(key);
        if (kind === "tree") trees.add(key);
      } else if (K.top && index[K.top] !== undefined) { if (!tops.has(key)) { tops.add(key); quad([x, K.h, y + 1], [x + 1, K.h, y + 1], [x + 1, K.h, y], [x, K.h, y], index[K.top], 0.95); } covered.add(key); }
      else if (K.roof) covered.add(key);                                       // (a house's square is under its roof)
      continue;
    }
    covered.add(`${x},${y}`);
    const under = sky && canopy.has(`${x},${y}`), g = CM.groundAt(fl, x, y);
    const floorLayer = g && index[`ground:${g}`] !== undefined ? index[`ground:${g}`] : index.floor;
    quad([x, 0, y + 1], [x + 1, 0, y + 1], [x + 1, 0, y], [x, 0, y], floorLayer, under ? 0.55 : 0.9);
    if (!sky) { quad([x, 1, y], [x + 1, 1, y], [x + 1, 1, y + 1], [x, 1, y + 1], index.ceiling, 0.7); ceilings++; }
    else if (under && index.canopy !== undefined) quad([x, 1.25, y], [x + 1, 1.25, y], [x + 1, 1.25, y + 1], [x, 1.25, y + 1], index.canopy, 0.6);
    SIDES.forEach(([dx, dy, shade], d) => {
      const nx = x + dx, ny = y + dy;
      if (!solid(nx, ny)) return;
      const K = kindOf(nx, ny), key = `${nx},${ny}`;
      if (K.tree) {                                                                   // the trees: this one, and the rank behind it
        trees.add(key);
        if (solid(nx + dx, ny + dy) && kindOf(nx + dx, ny + dy).tree) trees.add(`${nx + dx},${ny + dy}`);
        return;
      }
      const h = K.h || 1, layer = K.face === "wall" ? pickWall(x, y, d, nx, ny) : L(K.face);
      const a = d === 0 ? [x, y] : d === 1 ? [x + 1, y + 1] : d === 2 ? [x + 1, y] : [x, y + 1];
      const b = d === 0 ? [x + 1, y] : d === 1 ? [x, y + 1] : d === 2 ? [x + 1, y + 1] : [x, y];
      quad([a[0], 0, a[1]], [b[0], 0, b[1]], [b[0], h, b[1]], [a[0], h, a[1]], layer, shade); walls++;
      if (K.roof && index[K.roof] !== undefined) {                                    // the eaves: a slope from the wall's top back over the house
        const ix = dx * 0.5, iz = dy * 0.5;
        quad([a[0], h, a[1]], [b[0], h, b[1]], [b[0] + ix, h + 0.45, b[1] + iz], [a[0] + ix, h + 0.45, a[1] + iz], index[K.roof], Math.min(1.1, shade * 1.1)); roofs++;   // (the eaves catch the sky)
      }
      if (K.top && !tops.has(key) && index[K.top] !== undefined) { tops.add(key); quad([nx, h, ny + 1], [nx + 1, h, ny + 1], [nx + 1, h, ny], [nx, h, ny], index[K.top], 0.95); }
    });
  }
  if (sky) {                                                                            // past the edge: a skirt of grass, and the far ring standing on it
    const E = CM.SKIRT, B = 4, grass = L("ground:grass");
    const band = (x0, y0, x1, y1) => { for (let y = y0; y < y1; y += B) for (let x = x0; x < x1; x += B) { const xe = Math.min(x + B, x1), ye = Math.min(y + B, y1); quad([x, -0.002, ye], [xe, -0.002, ye], [xe, -0.002, y], [x, -0.002, y], grass, 0.8); skirt++; } };
    band(-E, -E, size + E, 0); band(-E, size, size + E, size + E); band(-E, 0, 0, size); band(size, 0, size + E, size);
    const far = (side) => L(fl.number === -1 && side === 1 ? "far:hill" : "far:trees"), W = 8, H = 7;   // (from the land, the town's hill stands in the east)
    for (let t = -E; t < size + E; t += W) {
      const t1 = Math.min(t + W, size + E);
      quad([t, 0, -E], [t1, 0, -E], [t1, H, -E], [t, H, -E], far(0), 0.7);                          // north
      quad([t1, 0, size + E], [t, 0, size + E], [t, H, size + E], [t1, H, size + E], far(2), 0.7);  // south
      quad([size + E, 0, t], [size + E, 0, t1], [size + E, H, t1], [size + E, H, t], far(1), 0.7);  // east
      quad([-E, 0, t1], [-E, 0, t], [-E, H, t], [-E, H, t1], far(3), 0.7);                          // west
      ring += 4;
    }
  }
  for (const key of trees) {                                                            // two crossed pictures a tree, of the seed's three
    const [x, y] = key.split(",").map(Number), v = CM.hashSeed(`${fl.number}:tree:${key}`) % 3, layer = L(`tree:${v}`), h = CM.SOLID.tree.h, cx = x + 0.5, cz = y + 0.5, r = 0.62;
    quad([cx - r, 0, cz + r], [cx + r, 0, cz - r], [cx + r, h, cz - r], [cx - r, h, cz + r], layer, 1.0);
    quad([cx - r, 0, cz - r], [cx + r, 0, cz + r], [cx + r, h, cz + r], [cx - r, h, cz - r], layer, 1.0);
  }
  let props = 0;                                                                        // the props that lie or grow: flat, and crossed pairs
  const sub = opts.sub || {};
  const quadUV = (a, b, c, d, layer, shade, r) => { const uv = [[r[0], r[3]], [r[2], r[3]], [r[2], r[1]], [r[0], r[1]]]; for (const i of [0, 1, 2, 0, 2, 3]) out.push(...[a, b, c, d][i], uv[i][0], uv[i][1], layer, shade, 0, 1, 0); };
  for (const p of opts.props || []) {
    if (p.how === "stand") continue;
    const s = sub[p.layer], layer = s ? index[s[0]] : index[p.layer], r = s ? s.slice(1) : [0, 0, 1, 1];
    if (layer === undefined) continue;
    const cx = p.x + 0.5 + p.dx, cz = p.y + 0.5 + p.dz, c = Math.cos(p.turn), sn = Math.sin(p.turn), hw = p.w / 2, shade = sky && canopy.has(`${p.x},${p.y}`) ? 0.55 : 0.9;
    if (p.how === "flat") {
      const at = (u, v) => [cx + u * c - v * sn, 0.006 + (props % 7) * 0.0006, cz + u * sn + v * c];
      quadUV(at(-hw, hw), at(hw, hw), at(hw, -hw), at(-hw, -hw), layer, shade, r);
    } else for (const t of [p.turn, p.turn + Math.PI / 2]) {
      const ux = Math.cos(t) * hw, uz = Math.sin(t) * hw;
      quadUV([cx - ux, 0, cz - uz], [cx + ux, 0, cz + uz], [cx + ux, p.h, cz + uz], [cx - ux, p.h, cz - uz], layer, shade, r);
    }
    props++;
  }
  return { data: out, count: out.length / CM.MESH_STRIDE, ceilings, walls, roofs, trees: trees.size, covered: covered.size, skirt, ring, props };
};
