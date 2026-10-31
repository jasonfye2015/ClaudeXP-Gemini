"use strict";
// Claudecraft through the Neather Gate (the eighteenth update), for now a tech demo: the Timeline's Claudecraft
// (ClaudeGames/claudecraft/world.py) ported - an island of 160 x 160 blocks, 64 high, made from the seed (value-noise
// hills, beaches, a sea, stone under the dirt, bedrock, trees), meshed a chunk of 16 x 16 columns at a time into the
// faces that can be seen, and a ray to the block under the eye. Changes are kept as edits over the made terrain, with
// the village. Near the spawn stands a gate of basalt like the one in the Keep-yard, its light the way home.
// The window draws it with its own WebGL (76h-claudecraft.js); 61k-gate.js has the gate in the town.
const CC = CM.CC = { CHUNK: 16, CHUNKS: 10, HEIGHT: 64, SEA: 24 };
CC.SIZE = CC.CHUNK * CC.CHUNKS;
CC.B = { AIR: 0, GRASS: 1, DIRT: 2, STONE: 3, SAND: 4, LOG: 5, LEAVES: 6, PLANKS: 7, COBBLE: 8, WATER: 9, GLASS: 10, BRICK: 11, BEDROCK: 12, SNOW: 13, GRAVEL: 14, BASALT: 15, GATE: 16 };
const CB = CC.B;
CC.NAMES = { 1: "Grass", 2: "Dirt", 3: "Stone", 4: "Sand", 5: "Wood", 6: "Leaves", 7: "Planks", 8: "Cobblestone", 9: "Water", 10: "Glass", 11: "Bricks", 12: "Bedrock", 13: "Snow", 14: "Gravel", 15: "Basalt", 16: "The gate's light" };
CC.HOTBAR = [CB.GRASS, CB.DIRT, CB.STONE, CB.COBBLE, CB.PLANKS, CB.LOG, CB.GLASS, CB.BRICK, CB.SAND];
CC.TRANSPARENT = new Set([CB.AIR, CB.WATER, CB.GLASS, CB.LEAVES, CB.GATE]);
CC.SOLID = new Set([1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12, 13, 14, 15]);
CC.UNBREAKABLE = new Set([CB.BEDROCK, CB.BASALT, CB.GATE]);
CC.ATLAS = 8;                                                              // (the atlas: 8 x 4 tiles of 16 x 16)
CC.TILE = { grass_top: 0, grass_side: 1, dirt: 2, stone: 3, sand: 4, log_side: 5, log_top: 6, leaves: 7, planks: 8, cobble: 9, water: 10, glass: 11, brick: 12, bedrock: 13, snow: 14, gravel: 15, basalt: 16, gate: 17 };
CC.FACES = { 1: ["grass_top", "grass_side", "dirt"], 2: ["dirt", "dirt", "dirt"], 3: ["stone", "stone", "stone"], 4: ["sand", "sand", "sand"], 5: ["log_top", "log_side", "log_top"], 6: ["leaves", "leaves", "leaves"], 7: ["planks", "planks", "planks"], 8: ["cobble", "cobble", "cobble"],
  9: ["water", "water", "water"], 10: ["glass", "glass", "glass"], 11: ["brick", "brick", "brick"], 12: ["bedrock", "bedrock", "bedrock"], 13: ["snow", "snow", "dirt"], 14: ["gravel", "gravel", "gravel"], 15: ["basalt", "basalt", "basalt"], 16: ["gate", "gate", "gate"] };
// the six faces: normal, shade, six corners [dx, dy, dz, u, v] - two triangles
CC.FACE_DEFS = [
  [[0, 1, 0], 1.0, [[0, 1, 0, 0, 0], [0, 1, 1, 0, 1], [1, 1, 1, 1, 1], [0, 1, 0, 0, 0], [1, 1, 1, 1, 1], [1, 1, 0, 1, 0]]],
  [[0, -1, 0], 0.5, [[0, 0, 0, 0, 0], [1, 0, 0, 1, 0], [1, 0, 1, 1, 1], [0, 0, 0, 0, 0], [1, 0, 1, 1, 1], [0, 0, 1, 0, 1]]],
  [[1, 0, 0], 0.7, [[1, 0, 0, 1, 1], [1, 1, 0, 1, 0], [1, 1, 1, 0, 0], [1, 0, 0, 1, 1], [1, 1, 1, 0, 0], [1, 0, 1, 0, 1]]],
  [[-1, 0, 0], 0.7, [[0, 0, 0, 0, 1], [0, 0, 1, 1, 1], [0, 1, 1, 1, 0], [0, 0, 0, 0, 1], [0, 1, 1, 1, 0], [0, 1, 0, 0, 0]]],
  [[0, 0, 1], 0.85, [[0, 0, 1, 0, 1], [1, 0, 1, 1, 1], [1, 1, 1, 1, 0], [0, 0, 1, 0, 1], [1, 1, 1, 1, 0], [0, 1, 1, 0, 0]]],
  [[0, 0, -1], 0.85, [[0, 0, 0, 1, 1], [0, 1, 0, 1, 0], [1, 1, 0, 0, 0], [0, 0, 0, 1, 1], [1, 1, 0, 0, 0], [1, 0, 0, 0, 1]]],
];
// value noise, as world.py has it
CC.hash = (seed, x, z) => { let n = (Math.imul(x, 374761393) + Math.imul(z, 668265263) + Math.imul(seed, 2147483647)) >>> 0; n = Math.imul(n ^ (n >>> 13), 1274126177) >>> 0; return ((n ^ (n >>> 16)) & 0xFFFF) / 65535; };
CC.noise = (seed, x, z, scale) => { const fx = x / scale, fz = z / scale, x0 = Math.floor(fx), z0 = Math.floor(fz), sm = (t) => t * t * (3 - 2 * t), tx = sm(fx - x0), tz = sm(fz - z0), a = CC.hash(seed, x0, z0), b = CC.hash(seed, x0 + 1, z0), c = CC.hash(seed, x0, z0 + 1), d = CC.hash(seed, x0 + 1, z0 + 1); return (a + (b - a) * tx) * (1 - tz) + (c + (d - c) * tx) * tz; };

CC.World = class {
  constructor(seed, edits = {}) { this.seed = seed >>> 0; this.blocks = new Uint8Array(CC.SIZE * CC.SIZE * CC.HEIGHT); this.edits = Object.assign({}, edits); this.heights = []; }
  index(x, y, z) { return (y * CC.SIZE + z) * CC.SIZE + x; }
  inside(x, y, z) { return x >= 0 && x < CC.SIZE && y >= 0 && y < CC.HEIGHT && z >= 0 && z < CC.SIZE; }
  get(x, y, z) { if (x < 0 || x >= CC.SIZE || z < 0 || z >= CC.SIZE || y < 0) return y < 0 ? CB.BEDROCK : CB.AIR; if (y >= CC.HEIGHT) return CB.AIR; return this.blocks[(y * CC.SIZE + z) * CC.SIZE + x]; }
  set(x, y, z, b, record = true) { if (!this.inside(x, y, z)) return false; this.blocks[this.index(x, y, z)] = b; if (record) this.edits[`${x},${y},${z}`] = b; return true; }
  generate() {
    const s = this.seed, R = new CM.Random(s), S = CC.SIZE, H = CC.HEIGHT, bl = this.blocks;
    for (let x = 0; x < S; x++) { this.heights.push(new Array(S).fill(0)); for (let z = 0; z < S; z++) {
      const n = CC.noise(s, x, z, 48) * 0.6 + CC.noise(s + 1, x, z, 20) * 0.3 + CC.noise(s + 2, x, z, 8) * 0.1, mountain = CC.noise(s + 3, x, z, 64);
      let h = Math.floor(14 + n * 22 + Math.max(0, mountain - 0.6) * 60); h = Math.max(2, Math.min(H - 8, h));
      const edge = Math.min(x, z, S - 1 - x, S - 1 - z); if (edge < 12) h = Math.min(h, CC.SEA - 6 + Math.floor(edge / 2));   // (an island: down into the sea at its edges)
      this.heights[x][z] = h;
      for (let y = 0; y <= h; y++) bl[(y * S + z) * S + x] = y === 0 ? CB.BEDROCK : y < h - 3 ? CB.STONE : h <= CC.SEA + 1 ? (h >= CC.SEA - 3 ? CB.SAND : CB.GRAVEL) : y === h ? (h > 44 ? CB.SNOW : CB.GRASS) : CB.DIRT;
      for (let y = h + 1; y <= CC.SEA; y++) bl[(y * S + z) * S + x] = CB.WATER;
    } }
    for (let k = 0; k < Math.floor((S * S) / 70); k++) {                    // trees
      const x = R.int(3, S - 4), z = R.int(3, S - 4), h = this.heights[x][z]; if (this.get(x, h, z) !== CB.GRASS) continue;
      const trunk = R.int(4, 6); for (let y = h + 1; y <= h + trunk; y++) this.set(x, y, z, CB.LOG, false);
      const top = h + trunk;
      for (let dy = -2; dy < 2; dy++) { const r = dy < 0 ? 2 : 1; for (let dx = -r; dx <= r; dx++) for (let dz = -r; dz <= r; dz++) { if (Math.abs(dx) === r && Math.abs(dz) === r && (dy === 1 || R.next() < 0.5)) continue; if (this.get(x + dx, top + dy, z + dz) === CB.AIR) this.set(x + dx, top + dy, z + dz, CB.LEAVES, false); } }
      this.set(x, top + 1, z, CB.LEAVES, false);
    }
    this.gate = this.buildGate();
    for (const [k, b] of Object.entries(this.edits)) { const [x, y, z] = k.split(",").map(Number); this.set(x, y, z, b, false); }
    return this;
  }
  // the gate home: a frame of basalt, four wide and five high, its light inside, on level ground near the spawn
  buildGate() {
    const [sx, , sz] = this.spawn(), gx = Math.floor(sx) + 3, gz = Math.floor(sz) - 1;
    let base = 0; for (let dx = -1; dx <= 4; dx++) for (let dz = -1; dz <= 1; dz++) base = Math.max(base, this.topSolid(gx + dx, gz + dz));
    for (let dx = -1; dx <= 4; dx++) for (let dz = -1; dz <= 1; dz++) { for (let y = this.topSolid(gx + dx, gz + dz) + 1; y <= base; y++) this.set(gx + dx, y, gz + dz, CB.COBBLE, false); for (let y = base + 1; y <= base + 6; y++) this.set(gx + dx, y, gz + dz, CB.AIR, false); }   // (a level step under it, room around it)
    for (let dx = 0; dx < 4; dx++) for (let dy = 1; dy <= 5; dy++) { const frame = dx === 0 || dx === 3 || dy === 1 || dy === 5; this.set(gx + dx, base + dy, gz, frame ? CB.BASALT : CB.GATE, false); }
    for (const dx of [-1, 4]) { this.set(gx + dx, base + 1, gz, CB.BASALT, false); this.set(gx + dx, base + 2, gz, CB.BASALT, false); }   // (two low buttresses either side, as the Keep-yard's gate has its footing)
    this.set(gx + 1, base + 6, gz, CB.BASALT, false); this.set(gx + 2, base + 6, gz, CB.BASALT, false);   // (and a capstone over its middle)
    return { x: gx, y: base + 1, z: gz };
  }
  topSolid(x, z) { for (let y = CC.HEIGHT - 1; y >= 0; y--) { const b = this.get(x, y, z); if (b !== CB.AIR && b !== CB.LEAVES && b !== CB.LOG) return y; } return 0; }
  spawn() {
    const S = CC.SIZE, c = S / 2;
    for (let r = 0; r < S / 2; r++) for (let d = -r; d <= r; d++) for (const [cx, cz] of [[c + d, c - r], [c + d, c + r], [c - r, c + d], [c + r, c + d]]) {
      if (cx < 0 || cz < 0 || cx >= S || cz >= S) continue; const h = this.top(cx, cz);
      if (h > CC.SEA && this.get(cx, h, cz) !== CB.WATER && this.get(cx, h, cz) !== CB.LEAVES) return [cx + 0.5, h + 1.01, cz + 0.5];
    }
    return [c + 0.5, CC.HEIGHT - 2, c + 0.5];
  }
  top(x, z) { for (let y = CC.HEIGHT - 1; y >= 0; y--) if (this.get(x, y, z) !== CB.AIR) return y; return 0; }
  // a chunk's faces that can be seen: [opaque floats, see-through floats] (x, y, z, u, v, shade per vertex)
  meshChunk(cx, cz) {
    const S = CC.SIZE, bl = this.blocks, ts = 1 / CC.ATLAS, rows = 4, tsv = 1 / rows, op = [], wa = [], x0 = cx * CC.CHUNK, z0 = cz * CC.CHUNK;
    const tiles = {}; for (const [b, [t, sd, bt]] of Object.entries(CC.FACES)) tiles[b] = [CC.TILE[t], CC.TILE[bt], CC.TILE[sd], CC.TILE[sd], CC.TILE[sd], CC.TILE[sd]];
    let top = 0; for (let x = x0; x < x0 + CC.CHUNK; x++) for (let z = z0; z < z0 + CC.CHUNK; z++) top = Math.max(top, this.top(x, z));
    top = Math.min(CC.HEIGHT - 1, top + 1);
    for (let y = 0; y <= top; y++) for (let z = z0; z < z0 + CC.CHUNK; z++) { const base = (y * S + z) * S; for (let x = x0; x < x0 + CC.CHUNK; x++) {
      const b = bl[base + x]; if (b === CB.AIR) continue; const tl = tiles[b], out = b === CB.WATER || b === CB.GATE ? wa : op;
      CC.FACE_DEFS.forEach(([[nx, ny, nz], shade, corners], f) => {
        const nb = this.get(x + nx, y + ny, z + nz);
        if (b === CB.WATER) { if (nb !== CB.AIR) return; } else if (b === CB.GATE) { if (nb === CB.GATE || nb === CB.BASALT) return; } else if (!CC.TRANSPARENT.has(nb) || nb === b) return;
        const tile = tl[f], u0 = (tile % CC.ATLAS) * ts, v0 = Math.floor(tile / CC.ATLAS) * tsv;
        for (const [dx, dy, dz, u, v] of corners) out.push(x + dx, y + dy - (b === CB.WATER && dy ? 0.12 : 0), z + dz, u0 + u * ts, v0 + v * tsv, b === CB.GATE ? 2.0 : shade);   // (shade 2: the gate's light, which the shader moves)
      });
    } }
    return [new Float32Array(op), new Float32Array(wa)];
  }
  // the block under the eye, and the empty one before it (Amanatides and Woo)
  raycast(o, d, reach = 6) {
    let x = Math.floor(o[0]), y = Math.floor(o[1]), z = Math.floor(o[2]); const step = d.map((v) => (v > 0 ? 1 : -1)), tmax = [], tdel = [];
    [x, y, z].forEach((cell, i) => { if (Math.abs(d[i]) < 1e-9) { tmax.push(Infinity); tdel.push(Infinity); } else { tmax.push((cell + (d[i] > 0 ? 1 : 0) - o[i]) / d[i]); tdel.push(Math.abs(1 / d[i])); } });
    let prev = null, t = 0;
    while (t <= reach) {
      const b = this.get(x, y, z); if (b !== CB.AIR && b !== CB.WATER && b !== CB.GATE) return [[x, y, z], prev];
      prev = [x, y, z]; const i = tmax[0] <= tmax[1] && tmax[0] <= tmax[2] ? 0 : tmax[1] <= tmax[2] ? 1 : 2; t = tmax[i]; tmax[i] += tdel[i];
      if (i === 0) x += step[0]; else if (i === 1) y += step[1]; else z += step[2];
    }
    return [null, null];
  }
};

// the walker: a body 0.6 wide and 1.8 tall moved through the blocks, walking, jumping, swimming, flying
CC.EYE = 1.62; CC.WALK = 4.3; CC.SPRINT = 6.5; CC.FLY = 11; CC.GRAVITY = 28; CC.JUMP = 8.6;
CC.Walker = class {
  constructor(world, pos, yaw = 45, pitch = -10) { Object.assign(this, { world, pos: pos.slice(), vel: [0, 0, 0], yaw, pitch, onGround: false, flying: false, lastSpace: -9, t: 0, slot: 0 }); }
  solidAt(x, y, z) { return CC.SOLID.has(this.world.get(Math.floor(x), Math.floor(y), Math.floor(z))); }
  boxHits(px, py, pz) { const r = 0.3; for (const x of [px - r, px + r - 1e-4]) for (const z of [pz - r, pz + r - 1e-4]) for (const y of [py, py + 0.9, py + 1.79]) if (this.solidAt(x, y, z)) return true; return false; }
  inGate() { const w = this.world; return [0.2, 1.0, 1.6].some((dy) => w.get(Math.floor(this.pos[0]), Math.floor(this.pos[1] + dy), Math.floor(this.pos[2])) === CB.GATE); }
  look() { const y = (this.yaw * Math.PI) / 180, p = (this.pitch * Math.PI) / 180; return [-Math.sin(y) * Math.cos(p), Math.sin(p), -Math.cos(y) * Math.cos(p)]; }
  eye() { return [this.pos[0], this.pos[1] + CC.EYE, this.pos[2]]; }
  update(dt, k) {
    this.t += dt; const yr = (this.yaw * Math.PI) / 180, fwd = [-Math.sin(yr), -Math.cos(yr)], right = [Math.cos(yr), -Math.sin(yr)];
    let mx = 0, mz = 0; if (k.fwd) { mx += fwd[0]; mz += fwd[1]; } if (k.back) { mx -= fwd[0]; mz -= fwd[1]; } if (k.right) { mx += right[0]; mz += right[1]; } if (k.left) { mx -= right[0]; mz -= right[1]; }
    const n = Math.hypot(mx, mz), water = this.world.get(Math.floor(this.pos[0]), Math.floor(this.pos[1] + 0.5), Math.floor(this.pos[2])) === CB.WATER;
    let speed = this.flying ? CC.FLY : k.sprint ? CC.SPRINT : CC.WALK; if (water && !this.flying) speed *= 0.55;
    this.vel[0] = n ? (mx / n) * speed : 0; this.vel[2] = n ? (mz / n) * speed : 0;
    if (this.flying) { this.vel[1] = (k.jump ? 1 : 0) * 7 - (k.down ? 1 : 0) * 7; }
    else { this.vel[1] -= CC.GRAVITY * dt * (water ? 0.35 : 1); if (water) { this.vel[1] = Math.max(this.vel[1], -3); if (k.jump) this.vel[1] = 3.2; } else if (k.jump && this.onGround) this.vel[1] = CC.JUMP; }
    for (let i = 0; i < 3; i++) {                                           // (an axis at a time: slide along walls)
      const np = this.pos.slice(); np[i] += this.vel[i] * dt;
      if (!this.boxHits(np[0], np[1], np[2])) this.pos = np;
      else { if (i === 1) { if (this.vel[1] < 0) { this.onGround = true; if (this.flying) this.flying = false; } this.vel[1] = 0; } else this.vel[i] = 0; }
    }
    if (this.vel[1] !== 0) this.onGround = this.boxHits(this.pos[0], this.pos[1] - 0.05, this.pos[2]) && this.vel[1] <= 0;
    if (this.pos[1] < -10) { const s = this.world.spawn(); this.pos = s.slice(); this.vel = [0, 0, 0]; }
  }
  // Space twice quickly: up into the air, or back down to walk
  pressJump() { if (this.t - this.lastSpace < 0.3) { this.flying = !this.flying; this.vel[1] = 0; this.lastSpace = -9; } else this.lastSpace = this.t; }
};
