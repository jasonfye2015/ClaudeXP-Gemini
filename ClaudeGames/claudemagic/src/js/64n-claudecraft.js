"use strict";
// Claudecraft through the Neather Gate (the eighteenth update), for now a tech demo: the Timeline's Claudecraft
// (ClaudeGames/claudecraft/world.py) ported - an island of 160 x 160 blocks, 64 high, made from the seed (value-noise
// hills, beaches, a sea, stone under the dirt, bedrock, trees), meshed a chunk of 16 x 16 columns at a time into the
// faces that can be seen, and a ray to the block under the eye. Changes are kept as edits over the made terrain, with
// the village. Near the spawn stands a gate of basalt like the one in the Keep-yard, its light the way home.
// The window draws it with its own WebGL (76h-claudecraft.js); 61k-gate.js has the gate in the town.
const CC = CM.CC = { CHUNK: 16, CHUNKS: 10, HEIGHT: 64, SEA: 24 };
CC.SIZE = CC.CHUNK * CC.CHUNKS;
CC.B = { AIR: 0, GRASS: 1, DIRT: 2, STONE: 3, SAND: 4, LOG: 5, LEAVES: 6, PLANKS: 7, COBBLE: 8, WATER: 9, GLASS: 10, BRICK: 11, BEDROCK: 12, SNOW: 13, GRAVEL: 14, BASALT: 15, GATE: 16,
  COPPER_ORE: 17, IRON_ORE: 18, SILVER_ORE: 19, GOLD_ORE: 20, STARIRON_ORE: 21, CHARSTONE: 22, WORKBENCH: 23, KILN: 24, TORCH: 25, CHEST: 26, LADDER: 27,
  RUBY: 28, SAPPHIRE: 29, SUNSTONE: 30, DIAMOND: 31, TREASURE: 32, LAIR: 33, BEDROLL: 34, DOOR: 35, DOOR_OPEN: 36, SIGN: 37, VAULT: 38, TRAP: 39 };
const CB = CC.B;
CC.NAMES = { 1: "Grass", 2: "Dirt", 3: "Stone", 4: "Sand", 5: "Wood", 6: "Leaves", 7: "Planks", 8: "Cobblestone", 9: "Water", 10: "Glass", 11: "Bricks", 12: "Bedrock", 13: "Snow", 14: "Gravel", 15: "Basalt", 16: "The gate's light",
  17: "Copper ore", 18: "Iron ore", 19: "Silver ore", 20: "Gold ore", 21: "Star-iron ore", 22: "Charstone", 101: "Copper ore chunk", 102: "Iron ore chunk", 103: "Silver ore chunk", 104: "Gold ore chunk", 105: "Star-iron ore chunk", 106: "Charcoal",
  23: "Workbench", 24: "Kiln", 25: "Torch", 26: "Chest", 27: "Ladder", 107: "Pole", 111: "Copper bar", 112: "Iron bar", 113: "Silver bar", 114: "Gold bar", 115: "Star-iron bar",
  28: "Ruby in the rock", 29: "Sapphire in the rock", 30: "Sunstone in the rock", 31: "Diamond in the rock", 32: "An old chest", 33: "A lair", 34: "Bedroll", 35: "Door", 36: "Door", 37: "Signpost", 38: "Rune-cut stone", 39: "Spikes", 150: "Rune-cut stone", 141: "Ruby", 142: "Sapphire", 143: "Sunstone", 144: "Diamond",
  121: "Stone pick", 122: "Stone axe", 123: "Stone sword", 124: "Copper pick", 125: "Copper axe", 126: "Copper sword", 127: "Iron pick", 128: "Iron axe", 129: "Iron sword" };
CC.HOTBAR = [CB.GRASS, CB.DIRT, CB.STONE, CB.COBBLE, CB.PLANKS, CB.LOG, CB.GLASS, CB.BRICK, CB.SAND];
CC.TRANSPARENT = new Set([CB.AIR, CB.WATER, CB.GLASS, CB.LEAVES, CB.GATE, CB.TORCH, CB.LADDER, 34, 36, 37]);
CC.SOLID = new Set([1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12, 13, 14, 15, 17, 18, 19, 20, 21, 22, 23, 24, 26, 28, 29, 30, 31, 32, 33, 35, 38, 39]);
CC.UNBREAKABLE = new Set([CB.BEDROCK, CB.BASALT, CB.GATE]);
// (v12.0) breaking takes time: seconds by bare hand; a pick from home quickens the stony ones by its grade
CC.HARDNESS = { 1: 0.6, 2: 0.5, 3: 2.5, 4: 0.5, 5: 1.2, 6: 0.2, 7: 1.2, 8: 2.5, 9: Infinity, 10: 0.4, 11: 2.5, 13: 0.3, 14: 0.6, 17: 3, 18: 3.5, 19: 4, 20: 4, 21: 5, 22: 2, 23: 1.5, 24: 2.5, 25: 0.1, 26: 1.5, 27: 0.6, 28: 4, 29: 4, 30: 4, 31: 6, 32: Infinity, 33: 6, 34: 0.4, 35: 1.2, 36: 1.2, 37: 0.6, 38: 8, 39: 2 };
CC.STONY = new Set([CB.STONE, CB.COBBLE, CB.BRICK, 17, 18, 19, 20, 21, 22, CB.KILN, 28, 29, 30, 31, 33, 38, 39]);
CC.WOODY = new Set([CB.LOG, CB.PLANKS, CB.WORKBENCH, CB.CHEST, CB.LADDER, 35, 36, 37]);
// (v12.1) ore in the stone: only a pick from home that mines it breaks it (a point of wear a block), and it drops the
// main game's own ore chunks; charstone breaks like stone and drops charcoal. Satchel ids over 100 are things, not blocks.
CC.ORE_OF = { 17: "copper", 18: "iron", 19: "silver", 20: "gold", 21: "stariron" };
// (v12.5) gems in the deep caverns' walls - the main game's own (CM.GEMS) - want a pick that would take silver
CC.GEM_OF = { 28: "ruby", 29: "sapphire", 30: "sunstone", 31: "diamond" }; CC.GEM_PICK = "silver";
CC.PICK_FOR = { 38: "silver" };   // (v12.7: the vault's rune-cut stone wants a pick that would take silver too)
CC.UNBREAKABLE.add(32);
CC.ITEM = { 101: { ore: "copper" }, 102: { ore: "iron" }, 103: { ore: "silver" }, 104: { ore: "gold" }, 105: { ore: "stariron" }, 106: { charcoal: true }, 107: { pole: true },
  111: { bar: "copper" }, 112: { bar: "iron" }, 113: { bar: "silver" }, 114: { bar: "gold" }, 115: { bar: "stariron" }, 141: { gem: "ruby" }, 142: { gem: "sapphire" }, 143: { gem: "sunstone" }, 144: { gem: "diamond" }, 150: { rune: true } };
CC.ITEM_TILE = { 101: "item_copper", 102: "item_iron", 103: "item_silver", 104: "item_gold", 105: "item_stariron", 106: "item_charcoal", 107: "item_pole",
  111: "bar_copper", 112: "bar_iron", 113: "bar_silver", 114: "bar_gold", 115: "bar_stariron", 141: "item_ruby", 142: "item_sapphire", 143: "item_sunstone", 144: "item_diamond", 150: "item_rune", 121: "pick_stone", 122: "axe_stone", 123: "sword_stone", 124: "pick_copper", 125: "axe_copper", 126: "sword_copper", 127: "pick_iron", 128: "axe_iron", 129: "sword_iron" };
// (v12.2) the island's own tools, made at a workbench: they stay on the island. A pick quickens stone and mines ore of its
// grade, an axe quickens wood, a sword adds to the hero's blows there; each has its uses, a block broken (or a blow) one.
CC.TOOLS = { 121: { kind: "pick", tier: "stone", factor: 0.6, mines: ["copper"], uses: 60 }, 122: { kind: "axe", tier: "stone", factor: 0.5, uses: 60 }, 123: { kind: "sword", tier: "stone", power: 2, uses: 60 },
  124: { kind: "pick", tier: "copper", factor: 0.45, mines: ["copper", "iron"], uses: 150 }, 125: { kind: "axe", tier: "copper", factor: 0.4, uses: 150 }, 126: { kind: "sword", tier: "copper", power: 4, uses: 150 },
  127: { kind: "pick", tier: "iron", factor: 0.35, mines: ["copper", "iron", "silver"], uses: 300 }, 128: { kind: "axe", tier: "iron", factor: 0.3, uses: 300 }, 129: { kind: "sword", tier: "iron", power: 6, uses: 300 } };
CC.isItem = (b) => b > 100;
CC.itemWeight = (b) => { const I = CC.ITEM[b]; return !I ? 0 : I.ore ? CM.WEIGHTS.ore : I.bar ? CM.WEIGHTS.bar : I.charcoal ? CM.WEIGHTS.charcoal : 0; };
CC.goesHome = (b) => { const I = CC.ITEM[b]; return !!(I && (I.ore || I.bar || I.charcoal || I.gem || I.rune)); };
CC.toHome = (b) => { const I = CC.ITEM[b]; return !I ? null : I.ore ? CM.oreChunk(I.ore) : I.bar ? CM.metalBar(I.bar) : I.charcoal ? CM.charcoal() : I.gem ? CM.gem(I.gem) : I.rune ? { name: "Rune-cut stone", kind: "rune", power: 0, value: 30 } : null; };
// (v12.2) what the island makes: by hand, at a workbench or at a kiln within reach. A kiln's bar is the Smith's own sum.
CC.REACH = 4;
CC.RECIPES = [
  { id: "planks", makes: [CB.PLANKS, 4], needs: { [CB.LOG]: 1 } }, { id: "poles", makes: [107, 4], needs: { [CB.PLANKS]: 2 } },
  { id: "workbench", makes: [CB.WORKBENCH, 1], needs: { [CB.PLANKS]: 4 } }, { id: "torch", makes: [CB.TORCH, 4], needs: { 107: 1, 106: 1 } },
  { id: "kiln", makes: [CB.KILN, 1], needs: { [CB.COBBLE]: 8 }, at: "bench" }, { id: "chest", makes: [CB.CHEST, 1], needs: { [CB.PLANKS]: 8 }, at: "bench" },
  { id: "ladder", makes: [CB.LADDER, 3], needs: { 107: 7 }, at: "bench" },
  { id: "bedroll", makes: [CB.BEDROLL, 1], needs: { [CB.LEAVES]: 6, 107: 2 }, at: "bench" }, { id: "door", makes: [CB.DOOR, 1], needs: { [CB.PLANKS]: 6 }, at: "bench" }, { id: "sign", makes: [CB.SIGN, 2], needs: { [CB.PLANKS]: 2, 107: 1 }, at: "bench" },
  { id: "stonepick", makes: [121, 1], needs: { [CB.COBBLE]: 3, 107: 2 }, at: "bench" }, { id: "stoneaxe", makes: [122, 1], needs: { [CB.COBBLE]: 3, 107: 2 }, at: "bench" }, { id: "stonesword", makes: [123, 1], needs: { [CB.COBBLE]: 2, 107: 1 }, at: "bench" },
  { id: "copperpick", makes: [124, 1], needs: { 111: 3, 107: 2 }, at: "bench" }, { id: "copperaxe", makes: [125, 1], needs: { 111: 3, 107: 2 }, at: "bench" }, { id: "coppersword", makes: [126, 1], needs: { 111: 2, 107: 1 }, at: "bench" },
  { id: "ironpick", makes: [127, 1], needs: { 112: 3, 107: 2 }, at: "bench" }, { id: "ironaxe", makes: [128, 1], needs: { 112: 3, 107: 2 }, at: "bench" }, { id: "ironsword", makes: [129, 1], needs: { 112: 2, 107: 1 }, at: "bench" },
  { id: "glass", makes: [CB.GLASS, 4], needs: { [CB.SAND]: 4, 106: 1 }, at: "kiln" }, { id: "bricks", makes: [CB.BRICK, 4], needs: { [CB.COBBLE]: 4, 106: 1 }, at: "kiln" },
];
for (const [i, ore] of ["copper", "iron", "silver", "gold", "stariron"].entries()) CC.RECIPES.push({ id: `bar_${ore}`, makes: [111 + i, 1], needs: { [101 + i]: 3, 106: 1 }, at: "kiln" });   // (three chunks and a charcoal, as the Smith smelts)
CC.PICK_FACTOR = { copper: 0.5, iron: 0.35, steel: 0.25 };
CC.pickFactor = (grade) => CC.PICK_FACTOR[grade] || 0.5;
// what a broken block drops into the satchel (0: nothing); the rest drop themselves
CC.DROPS = { 1: CB.DIRT, 3: CB.COBBLE, 9: 0, 10: 0, 17: 101, 18: 102, 19: 103, 20: 104, 21: 105, 22: 106, 28: 141, 29: 142, 30: 143, 31: 144, 33: 0, 36: CB.DOOR, 38: 150, 39: 0 };
CC.DROP_COUNT = { 21: 2 };   // (a star-iron seam gives two chunks)
CC.FALL_SAFE = 4;                                                          // (blocks: a fall longer than this hurts)
CC.fallHurt = (dist, max) => dist > CC.FALL_SAFE ? Math.round((dist - 3) * 0.06 * max) : 0;
// the hero's satchel: 27 slots of {b, n}, stacks of up to 64; the first nine are the hotbar
CC.SATCHEL = 27; CC.STACK = 64;
CC.Satchel = class {
  constructor(saved, size = CC.SATCHEL) { this.slots = Array.from({ length: size }, (_, i) => (saved && saved[i] && saved[i].n > 0 ? Object.assign({ b: saved[i].b, n: saved[i].n }, saved[i].d !== undefined ? { d: saved[i].d } : {}) : null)); }
  add(b, n = 1) {
    if (CC.TOOLS[b]) { for (let k = 0; k < n; k++) { const i = this.slots.indexOf(null); if (i < 0) return false; this.slots[i] = { b, n: 1, d: CC.TOOLS[b].uses }; } return true; }   // (a tool to a slot, with its uses)
    for (let k = 0; k < n; k++) {
      let s = this.slots.find((x) => x && x.b === b && x.n < CC.STACK);
      if (s) { s.n++; continue; }
      const i = this.slots.indexOf(null); if (i < 0) return false;
      this.slots[i] = { b, n: 1 };
    }
    return true;
  }
  take(i, n = 1) { const s = this.slots[i]; if (!s || s.n < n) return false; s.n -= n; if (!s.n) this.slots[i] = null; return true; }
  count(b) { return this.slots.reduce((t, s) => t + (s && s.b === b ? s.n : 0), 0); }
  takeCount(b, n) { if (this.count(b) < n) return false; for (let i = this.slots.length - 1; i >= 0 && n > 0; i--) { const s = this.slots[i]; if (!s || s.b !== b) continue; const k = Math.min(n, s.n); s.n -= k; n -= k; if (!s.n) this.slots[i] = null; } return true; }
  swap(i, j) { [this.slots[i], this.slots[j]] = [this.slots[j], this.slots[i]]; }
  empty() { const out = this.slots.filter(Boolean).map((s) => Object.assign({}, s)); this.slots.fill(null); return out; }
  toJSON() { return this.slots.map((s) => (s ? Object.assign({}, s) : null)); }
  // a stack put in whole (a tool with its uses kept); false if it would not all fit
  put(st) { if (CC.TOOLS[st.b]) { const i = this.slots.indexOf(null); if (i < 0) return false; this.slots[i] = Object.assign({}, st); return true; } const room = this.slots.reduce((t, x) => t + (!x ? CC.STACK : x.b === st.b ? CC.STACK - x.n : 0), 0); if (room < st.n) return false; return this.add(st.b, st.n); }
  // the best tool of a kind (picks: one that mines this ore, if one is asked), as [slot, tool]
  best(kind, ore) { let out = null; this.slots.forEach((s, i) => { const T = s && CC.TOOLS[s.b]; if (!T || T.kind !== kind || (ore && !(T.mines || []).includes(ore))) return; if (!out || (T.factor ? T.factor < out[1].factor : T.power > out[1].power)) out = [i, T]; }); return out; }
};
CC.ATLAS = 8; CC.ROWS = 16;                                               // (the atlas: 8 x 16 tiles of 16 x 16)
CC.TILE = { grass_top: 0, grass_side: 1, dirt: 2, stone: 3, sand: 4, log_side: 5, log_top: 6, leaves: 7, planks: 8, cobble: 9, water: 10, glass: 11, brick: 12, bedrock: 13, snow: 14, gravel: 15, basalt: 16, gate: 17, ore_copper: 18, ore_iron: 19, ore_silver: 20, ore_gold: 21, ore_stariron: 22, charstone: 23,
  item_copper: 24, item_iron: 25, item_silver: 26, item_gold: 27, item_stariron: 28, item_charcoal: 29, workbench_top: 30, workbench_side: 31, kiln_side: 32, kiln_top: 33, torch: 34,
  chest_side: 35, chest_top: 36, ladder: 37, item_pole: 38, bar_copper: 39, bar_iron: 40, bar_silver: 41, bar_gold: 42, bar_stariron: 43, pick_stone: 44, axe_stone: 45, sword_stone: 46,
  pick_copper: 47, axe_copper: 48, sword_copper: 49, pick_iron: 50, axe_iron: 51, sword_iron: 52, gem_ruby: 55, gem_sapphire: 56, gem_sunstone: 57, gem_diamond: 58, treasure_side: 59, treasure_top: 60, lair: 61,
  item_ruby: 62, item_sapphire: 63, item_sunstone: 64, item_diamond: 65, bedroll: 66, door: 67, sign: 68, vault: 69, trap: 70, item_rune: 71 };
CC.FACES = { 1: ["grass_top", "grass_side", "dirt"], 2: ["dirt", "dirt", "dirt"], 3: ["stone", "stone", "stone"], 4: ["sand", "sand", "sand"], 5: ["log_top", "log_side", "log_top"], 6: ["leaves", "leaves", "leaves"], 7: ["planks", "planks", "planks"], 8: ["cobble", "cobble", "cobble"],
  9: ["water", "water", "water"], 10: ["glass", "glass", "glass"], 11: ["brick", "brick", "brick"], 12: ["bedrock", "bedrock", "bedrock"], 13: ["snow", "snow", "dirt"], 14: ["gravel", "gravel", "gravel"], 15: ["basalt", "basalt", "basalt"], 16: ["gate", "gate", "gate"],
  17: ["ore_copper", "ore_copper", "ore_copper"], 18: ["ore_iron", "ore_iron", "ore_iron"], 19: ["ore_silver", "ore_silver", "ore_silver"], 20: ["ore_gold", "ore_gold", "ore_gold"], 21: ["ore_stariron", "ore_stariron", "ore_stariron"], 22: ["charstone", "charstone", "charstone"],
  23: ["workbench_top", "workbench_side", "planks"], 24: ["kiln_top", "kiln_side", "cobble"], 25: ["torch", "torch", "torch"], 26: ["chest_top", "chest_side", "planks"], 27: ["ladder", "ladder", "ladder"],
  28: ["gem_ruby", "gem_ruby", "gem_ruby"], 29: ["gem_sapphire", "gem_sapphire", "gem_sapphire"], 30: ["gem_sunstone", "gem_sunstone", "gem_sunstone"], 31: ["gem_diamond", "gem_diamond", "gem_diamond"], 32: ["treasure_top", "treasure_side", "planks"], 33: ["lair", "lair", "lair"], 34: ["bedroll", "bedroll", "bedroll"], 35: ["door", "door", "door"], 36: ["door", "door", "door"], 37: ["sign", "sign", "sign"], 38: ["vault", "vault", "vault"], 39: ["trap", "basalt", "basalt"] };
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

CC.hash3 = (seed, x, y, z) => CC.hash(seed + Math.imul(y, 1013904223), x, z);
CC.noise3 = (seed, x, y, z, scale) => { const fy = y / scale, y0 = Math.floor(fy), t = fy - y0, ty = t * t * (3 - 2 * t), a = CC.noise(seed + Math.imul(y0, 7919), x, z, scale), b = CC.noise(seed + Math.imul(y0 + 1, 7919), x, z, scale); return a + (b - a) * ty; };
// (v12.1) the ore's depths: [block, veins, length, lowest y, highest y]
CC.VEINS = [[22, 240, 7, 14, 46], [17, 260, 6, 10, 40], [18, 190, 5, 5, 28], [19, 110, 4, 3, 16], [20, 70, 4, 2, 10], [21, 45, 3, 1, 3]];
CC.World = class {
  constructor(seed, edits = {}) { this.seed = seed >>> 0; this.blocks = new Uint8Array(CC.SIZE * CC.SIZE * CC.HEIGHT); this.edits = Object.assign({}, edits); this.heights = []; this.roof = new Uint8Array(CC.SIZE * CC.SIZE); this.torches = new Set(); }
  // the highest block that keeps out the sky in a column (leaves, glass and water let it through)
  roofAt(x, z) { for (let y = CC.HEIGHT - 1; y > 0; y--) { const b = this.get(x, y, z); if (CC.SOLID.has(b) && b !== CB.LEAVES && b !== CB.GLASS) return y; } return 0; }
  skyOwn(x, y, z) { if (x < 0 || z < 0 || x >= CC.SIZE || z >= CC.SIZE) return 1; const d = this.roof[z * CC.SIZE + x] - y; return d < 0 ? 1 : Math.max(0, 1 - (d + 1) * 0.3); }
  skyAt(x, y, z) { const own = this.skyOwn(x, y, z); if (own >= 1) return 1; return Math.max(own, 0.7 * Math.max(this.skyOwn(x + 1, y, z), this.skyOwn(x - 1, y, z), this.skyOwn(x, y, z + 1), this.skyOwn(x, y, z - 1))); }   // (under an overhang, the open sky beside it still lights)
  // (v12.2) a torch's light: bright by it, gone eight blocks away (list: the torches to look at, or all)
  torchAt(x, y, z, list) { let best = 0; for (const k of list || this.torches) { const [tx, ty, tz] = typeof k === "string" ? k.split(",").map(Number) : k, d = Math.hypot(tx - x, ty - y, tz - z); if (d < CC.TORCH_REACH) best = Math.max(best, 0.95 * (1 - d / CC.TORCH_REACH)); } return best; }
  lightAt(x, y, z, list) { return Math.max(this.skyAt(x, y, z), this.torchAt(x, y, z, list)); }
  index(x, y, z) { return (y * CC.SIZE + z) * CC.SIZE + x; }
  inside(x, y, z) { return x >= 0 && x < CC.SIZE && y >= 0 && y < CC.HEIGHT && z >= 0 && z < CC.SIZE; }
  get(x, y, z) { if (x < 0 || x >= CC.SIZE || z < 0 || z >= CC.SIZE || y < 0) return y < 0 ? CB.BEDROCK : CB.AIR; if (y >= CC.HEIGHT) return CB.AIR; return this.blocks[(y * CC.SIZE + z) * CC.SIZE + x]; }
  set(x, y, z, b, record = true) { if (!this.inside(x, y, z)) return false; this.blocks[this.index(x, y, z)] = b; if (record) { this.edits[`${x},${y},${z}`] = b; this.roof[z * CC.SIZE + x] = this.roofAt(x, z); } if (b === CB.TORCH) this.torches.add(`${x},${y},${z}`); else this.torches.delete(`${x},${y},${z}`); return true; }
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
    this.carve(); this.veins(R);
    for (let k = 0; k < Math.floor((S * S) / 70); k++) {                    // trees
      const x = R.int(3, S - 4), z = R.int(3, S - 4), h = this.heights[x][z]; if (this.get(x, h, z) !== CB.GRASS) continue;
      const trunk = R.int(4, 6); for (let y = h + 1; y <= h + trunk; y++) this.set(x, y, z, CB.LOG, false);
      const top = h + trunk;
      for (let dy = -2; dy < 2; dy++) { const r = dy < 0 ? 2 : 1; for (let dx = -r; dx <= r; dx++) for (let dz = -r; dz <= r; dz++) { if (Math.abs(dx) === r && Math.abs(dz) === r && (dy === 1 || R.next() < 0.5)) continue; if (this.get(x + dx, top + dy, z + dz) === CB.AIR) this.set(x + dx, top + dy, z + dz, CB.LEAVES, false); } }
      this.set(x, top + 1, z, CB.LEAVES, false);
    }
    this.finds = []; this.places(new CM.Random(CM.hashSeed(`${s}:places`)));
    this.gate = this.buildGate();
    for (const [k, b] of Object.entries(this.edits)) { const [x, y, z] = k.split(",").map(Number); this.set(x, y, z, b, false); }
    for (let x = 0; x < S; x++) for (let z = 0; z < S; z++) this.roof[z * S + x] = this.roofAt(x, z);
    return this;
  }
  // (v12.1) caves: where two noises are both near their middle a winding tunnel; deep down, where a third is high, a
  // cavern. Only under land well above the sea (never through the sea floor), now and then opening on a hillside.
  carve() {
    const s = this.seed, S = CC.SIZE, bl = this.blocks, layers = new Map();
    const layer = (sd, y0, scale) => { let C = layers.get(sd); if (!C) { C = []; layers.set(sd, C); } let L = C[y0]; if (!L) { L = C[y0] = new Float32Array(S * S); const ls = sd + Math.imul(y0, 7919), n = Math.ceil(S / scale) + 2, lat = new Float32Array(n * n); for (let i = 0; i < n; i++) for (let j = 0; j < n; j++) lat[i * n + j] = CC.hash(ls, i, j);   // (CC.noise's own sums, its lattice hashed once)
      const sm = (t) => t * t * (3 - 2 * t); for (let x = 0; x < S; x++) { const fx = x / scale, x0 = Math.floor(fx), tx = sm(fx - x0); for (let z = 0; z < S; z++) { const fz = z / scale, z0 = Math.floor(fz), tz = sm(fz - z0), a = lat[x0 * n + z0], b = lat[(x0 + 1) * n + z0], c = lat[x0 * n + z0 + 1], d = lat[(x0 + 1) * n + z0 + 1]; L[x * S + z] = (a + (b - a) * tx) * (1 - tz) + (c + (d - c) * tx) * tz; } } } return L; };
    const n3 = (sd, x, y, z, scale) => { const fy = y / scale, y0 = Math.floor(fy), t = fy - y0, ty = t * t * (3 - 2 * t), a = layer(sd, y0, scale)[x * S + z], b = layer(sd, y0 + 1, scale)[x * S + z]; return a + (b - a) * ty; };   // (CC.noise3, its layers made once)
    for (let x = 1; x < S - 1; x++) for (let z = 1; z < S - 1; z++) {
      const h = this.heights[x][z]; if (h <= CC.SEA + 3) continue;
      let ok = true; for (const [dx, dz] of [[2, 0], [-2, 0], [0, 2], [0, -2]]) { const xx = x + dx, zz = z + dz; if (xx < 0 || zz < 0 || xx >= S || zz >= S || this.heights[xx][zz] <= CC.SEA + 1) ok = false; } if (!ok) continue;
      const mouth = CC.noise(s + 13, x, z, 30);
      for (let y = 2; y <= h - 1; y++) {
        const roof = h - y; if (roof < 4 && mouth < 0.62) continue;   // (the roof kept, but for the odd cave mouth)
        const a = n3(s + 10, x, y * 1.7, z, 18); let cut = false;
        if (Math.abs(a - 0.5) < 0.04) { const b = n3(s + 11, x, y * 1.7, z, 18); cut = Math.abs(b - 0.5) < 0.05; }
        if (!cut && y < 22) cut = n3(s + 12, x, y * 2.2, z, 22) > 0.74 + (22 - y) * 0.002;
        if (cut) bl[(y * S + z) * S + x] = CB.AIR;
      }
    }
  }
  // (v12.5) the island's finds, the seed's: gems in the deep caverns' walls, chests sunk in the sea, ruins on the hills
  // with a chest each, lairs in the deepest caverns (broken, they leave a chest), and the vault's hill (phase 7)
  places(R) {
    const S = CC.SIZE, H = this.heights, airBy = (x, y, z) => [[1, 0, 0], [-1, 0, 0], [0, 1, 0], [0, -1, 0], [0, 0, 1], [0, 0, -1]].some(([a, b, c]) => this.get(x + a, y + b, z + c) === CB.AIR);
    for (let k = 0; k < 3000; k++) { const x = R.int(2, S - 3), y = R.int(2, 13), z = R.int(2, S - 3); if (this.get(x, y, z) !== CB.STONE || !airBy(x, y, z)) continue; const r = R.next(); this.set(x, y, z, r < 0.08 ? CB.DIAMOND : r < 0.4 ? CB.RUBY : r < 0.7 ? CB.SAPPHIRE : CB.SUNSTONE, false); }
    let sunk = 0; for (let k = 0; k < 400 && sunk < 4; k++) { const x = R.int(4, S - 5), z = R.int(4, S - 5), h = H[x][z]; if (h > CC.SEA - 4 || this.finds.some((f) => Math.hypot(f.x - x, f.z - z) < 20)) continue; this.set(x, h + 1, z, CB.TREASURE, false); this.finds.push({ kind: "sunken", x, y: h + 1, z, depth: 8 }); sunk++; }
    let ruins = 0; for (let k = 0; k < 600 && ruins < 3; k++) {
      const x = R.int(14, S - 15), z = R.int(14, S - 15), h = H[x][z]; if (h < CC.SEA + 9) continue; let flat = true; for (let dx = -3; dx <= 3; dx++) for (let dz = -3; dz <= 3; dz++) if (Math.abs(H[x + dx][z + dz] - h) > 2) flat = false; if (!flat || this.finds.some((f) => Math.hypot(f.x - x, f.z - z) < 24)) continue;
      for (let dx = -3; dx <= 3; dx++) for (let dz = -3; dz <= 3; dz++) { for (let y = h + 1; y <= h + 4; y++) this.set(x + dx, y, z + dz, CB.AIR, false); this.set(x + dx, h, z + dz, R.chance(0.5) ? CB.COBBLE : CB.GRAVEL, false); if (Math.max(Math.abs(dx), Math.abs(dz)) === 3) { const tall = (dx + dz + 6) % 3 === 0 ? 1 : R.int(1, 3); for (let y = h + 1; y <= h + tall; y++) if (!(dx === 0 || dz === 0) || y > h + 2) this.set(x + dx, y, z + dz, R.chance(0.3) ? CB.BRICK : CB.COBBLE, false); } }
      this.set(x, h + 1, z, CB.TREASURE, false); this.finds.push({ kind: "ruin", x, y: h + 1, z, depth: 6 }); ruins++;
    }
    let lairs = 0; for (let k = 0; k < 6000 && lairs < 3; k++) { const x = R.int(6, S - 7), y = R.int(2, 9), z = R.int(6, S - 7); if (this.get(x, y, z) !== CB.AIR || this.get(x, y + 1, z) !== CB.AIR || !CC.SOLID.has(this.get(x, y - 1, z)) || this.finds.some((f) => Math.hypot(f.x - x, f.z - z) < 20)) continue; this.set(x, y, z, CB.LAIR, false); this.finds.push({ kind: "lair", x, y, z, depth: 25 }); lairs++; }
    let best = null; for (let x = 20; x < S - 20; x++) for (let z = 20; z < S - 20; z++) if (!best || H[x][z] > best.top) best = { x, z, top: H[x][z] };
    this.vault = { x: Math.max(16, Math.min(S - 17, best.x)), z: Math.max(8, Math.min(S - 9, best.z)), top: best.top, y: 4 };
    this.buildVault(R);
  }
  // (v12.7) the vault under the highest hill: a sealed shell of rune-cut stone, three rooms in a row - spikes, two
  // lairs, and the Hollow Mason's hall - with doorways between; reached only by digging down to it
  buildVault(R) {
    const v = this.vault, y0 = v.y, x0 = v.x - 12, z0 = v.z - 4;
    for (let dx = 0; dx < 25; dx++) for (let dz = 0; dz < 9; dz++) for (let dy = 0; dy < 6; dy++) { const shell = dx === 0 || dx === 24 || dx === 8 || dx === 16 || dz === 0 || dz === 8 || dy === 0 || dy === 5; this.set(x0 + dx, y0 + dy, z0 + dz, shell ? CB.VAULT : CB.AIR, false); }
    for (const wx of [8, 16]) for (const dy of [1, 2]) this.set(x0 + wx, y0 + dy, v.z, CB.AIR, false);
    for (let dx = 1; dx < 8; dx++) for (let dz = 1; dz < 8; dz++) if (R.chance(0.45) && !(dz === 4 && dx > 6)) this.set(x0 + dx, y0, z0 + dz, CB.TRAP, false);
    for (const [dx, dz] of [[10, 2], [14, 6]]) { this.set(x0 + dx, y0 + 1, z0 + dz, CB.LAIR, false); this.finds.push({ kind: "lair", x: x0 + dx, y: y0 + 1, z: z0 + dz, depth: 28, vault: true }); }
    for (const [dx, dz] of [[17, 1], [23, 1], [17, 7], [23, 7]]) this.set(x0 + dx, y0 + 1, z0 + dz, CB.TORCH, false);
    v.guard = { x: x0 + 20 + 0.5, y: y0 + 1, z: v.z + 0.5 }; v.rooms = [[x0 + 1, x0 + 7], [x0 + 9, x0 + 15], [x0 + 17, x0 + 23]]; v.z0 = z0 + 1; v.z1 = z0 + 7;
  }
  // (v12.1) ore in veins by depth (the deeper, the rarer), and charstone near the top - in the stone only
  veins(R) {
    for (const [b, n, len, lo, hi] of CC.VEINS) for (let k = 0; k < n; k++) {
      let x = R.int(2, CC.SIZE - 3), y = R.int(lo, hi), z = R.int(2, CC.SIZE - 3);
      for (let i = 0; i < len; i++) { if (this.get(x, y, z) === CB.STONE) this.blocks[this.index(x, y, z)] = b; const d = R.int(0, 5); if (d === 0) x++; else if (d === 1) x--; else if (d === 2) z++; else if (d === 3) z--; else if (d === 4 && y < hi) y++; else if (y > lo) y--; }
    }
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
  // a chunk's faces that can be seen: [opaque floats, see-through floats] (x, y, z, u, v, shade, sky per vertex)
  meshChunk(cx, cz) {
    const S = CC.SIZE, bl = this.blocks, ts = 1 / CC.ATLAS, rows = CC.ROWS, tsv = 1 / rows, op = [], wa = [], x0 = cx * CC.CHUNK, z0 = cz * CC.CHUNK;
    const near = [...this.torches].map((k) => k.split(",").map(Number)).filter(([tx, , tz]) => tx >= x0 - CC.TORCH_REACH && tx < x0 + CC.CHUNK + CC.TORCH_REACH && tz >= z0 - CC.TORCH_REACH && tz < z0 + CC.CHUNK + CC.TORCH_REACH);
    const tiles = {}; for (const [b, [t, sd, bt]] of Object.entries(CC.FACES)) tiles[b] = [CC.TILE[t], CC.TILE[bt], CC.TILE[sd], CC.TILE[sd], CC.TILE[sd], CC.TILE[sd]];
    let top = 0; for (let x = x0; x < x0 + CC.CHUNK; x++) for (let z = z0; z < z0 + CC.CHUNK; z++) top = Math.max(top, this.top(x, z));
    top = Math.min(CC.HEIGHT - 1, top + 1);
    for (let y = 0; y <= top; y++) for (let z = z0; z < z0 + CC.CHUNK; z++) { const base = (y * S + z) * S; for (let x = x0; x < x0 + CC.CHUNK; x++) {
      const b = bl[base + x]; if (b === CB.AIR) continue; const tl = tiles[b], out = b === CB.WATER || b === CB.GATE ? wa : op;
      if (b === CB.TORCH) { this.meshTorch(op, x, y, z, near); continue; }
      if (b === CB.BEDROLL || b === CB.DOOR_OPEN || b === CB.SIGN) { this.meshShape(op, b, x, y, z, near); continue; }
      CC.FACE_DEFS.forEach(([[nx, ny, nz], shade, corners], f) => {
        const nb = this.get(x + nx, y + ny, z + nz);
        if (b === CB.WATER) { if (nb !== CB.AIR) return; } else if (b === CB.GATE) { if (nb === CB.GATE || nb === CB.BASALT) return; } else if (!CC.TRANSPARENT.has(nb) || nb === b) return;
        const tile = tl[f], u0 = (tile % CC.ATLAS) * ts, v0 = Math.floor(tile / CC.ATLAS) * tsv, sky = b === CB.GATE ? CC.FULL : CC.packLight(this.skyAt(x + nx, y + ny, z + nz), this.torchAt(x + nx, y + ny, z + nz, near));
        for (const [dx, dy, dz, u, v] of corners) out.push(x + dx, y + dy - (b === CB.WATER && dy ? 0.12 : 0), z + dz, u0 + u * ts, v0 + v * tsv, b === CB.GATE ? 2.0 : shade, sky);   // (shade 2: the gate's light, which the shader moves)
      });
    } }
    return [new Float32Array(op), new Float32Array(wa)];
  }
  // (v12.6) a bedroll lies flat, an open door is a thin leaf against its frame, a signpost a post and a board
  meshShape(out, b, x, y, z, near) {
    const light = CC.packLight(this.skyAt(x, y, z), this.torchAt(x, y, z, near)), tile = (n) => { const t = CC.TILE[n]; return [(t % CC.ATLAS) / CC.ATLAS, Math.floor(t / CC.ATLAS) / CC.ROWS]; };
    const box = (ax, ay, az, w, h, d, tn) => { const [u0, v0] = tile(tn); for (const [, sh, corners] of CC.FACE_DEFS) for (const [dx, dy, dz, u, v] of corners) out.push(x + ax + dx * w, y + ay + dy * h, z + az + dz * d, u0 + u / CC.ATLAS, v0 + v / CC.ROWS, sh, light); };
    if (b === CB.BEDROLL) box(0.05, 0, 0.1, 0.9, 0.18, 0.8, "bedroll");
    else if (b === CB.DOOR_OPEN) box(0, 0, 0, 0.14, 1, 1, "door");
    else { box(0.44, 0, 0.44, 0.12, 0.85, 0.12, "planks"); box(0.08, 0.55, 0.45, 0.84, 0.4, 0.1, "sign"); }
  }
  // a torch: a stick an eighth wide, and a flame on it that the shader makes flicker (shade 3: gold)
  meshTorch(out, x, y, z, near) {
    const t = CC.TILE.torch, u0 = (t % CC.ATLAS) / CC.ATLAS, v0 = Math.floor(t / CC.ATLAS) / CC.ROWS, ts = 1 / CC.ATLAS, tsv = 1 / CC.ROWS;
    const box = (ax, ay, az, w, h, shade) => { for (const [, sh, corners] of CC.FACE_DEFS) for (const [dx, dy, dz, u, v] of corners) out.push(x + ax + dx * w, y + ay + dy * h, z + az + dz * w, u0 + (0.44 + u * 0.12) * ts, v0 + (0.3 + v * 0.7) * tsv, shade || sh, CC.FULL); };
    box(0.4375, 0, 0.4375, 0.125, 0.6, 0); box(0.42, 0.6, 0.42, 0.16, 0.16, 3.5); void near;
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
CC.TORCH_REACH = 8;
CC.packLight = (sky, torch) => Math.round(Math.max(0, Math.min(1, sky)) * 15) * 16 + Math.round(Math.max(0, Math.min(1, torch)) * 15);   // (sky and torch, 0-15 each)
CC.FULL = 255;
CC.EYE = 1.62; CC.WALK = 4.3; CC.SPRINT = 6.5; CC.FLY = 11; CC.GRAVITY = 28; CC.JUMP = 8.6;
CC.Walker = class {
  constructor(world, pos, yaw = 45, pitch = -10) { Object.assign(this, { world, pos: pos.slice(), vel: [0, 0, 0], yaw, pitch, onGround: false, flying: false, canFly: true, lastSpace: -9, t: 0, slot: 0, fallFrom: null, landed: 0 }); }
  solidAt(x, y, z) { return CC.SOLID.has(this.world.get(Math.floor(x), Math.floor(y), Math.floor(z))); }
  boxHits(px, py, pz) { const r = 0.3; for (const x of [px - r, px + r - 1e-4]) for (const z of [pz - r, pz + r - 1e-4]) for (const y of [py, py + 0.9, py + 1.79]) if (this.solidAt(x, y, z)) return true; return false; }
  inGate() { const w = this.world; return [0.2, 1.0, 1.6].some((dy) => w.get(Math.floor(this.pos[0]), Math.floor(this.pos[1] + dy), Math.floor(this.pos[2])) === CB.GATE); }
  look() { const y = (this.yaw * Math.PI) / 180, p = (this.pitch * Math.PI) / 180; return [-Math.sin(y) * Math.cos(p), Math.sin(p), -Math.cos(y) * Math.cos(p)]; }
  eye() { return [this.pos[0], this.pos[1] + CC.EYE, this.pos[2]]; }
  update(dt, k) {
    this.t += dt; const yr = (this.yaw * Math.PI) / 180, fwd = [-Math.sin(yr), -Math.cos(yr)], right = [Math.cos(yr), -Math.sin(yr)];
    let mx = 0, mz = 0; if (k.fwd) { mx += fwd[0]; mz += fwd[1]; } if (k.back) { mx -= fwd[0]; mz -= fwd[1]; } if (k.right) { mx += right[0]; mz += right[1]; } if (k.left) { mx -= right[0]; mz -= right[1]; }
    const n = Math.hypot(mx, mz), water = this.world.get(Math.floor(this.pos[0]), Math.floor(this.pos[1] + 0.5), Math.floor(this.pos[2])) === CB.WATER;
    let speed = this.flying ? CC.FLY : k.sprint && !this.heavy ? CC.SPRINT : CC.WALK; if (water && !this.flying) speed *= 0.55; if (this.heavy) speed *= 0.55;
    this.vel[0] = n ? (mx / n) * speed : 0; this.vel[2] = n ? (mz / n) * speed : 0;
    const ladder = [0.1, 1.0].some((dy) => this.world.get(Math.floor(this.pos[0]), Math.floor(this.pos[1] + dy), Math.floor(this.pos[2])) === CB.LADDER);
    if (ladder && !this.flying) { this.vel[1] = k.jump || k.fwd ? 3.2 : k.down || k.back ? -3.2 : -0.8; this.fallFrom = null; this.onLadder = true; }   // (up a ladder: Space or forward; down: back)
    else if (this.flying) { this.onLadder = false; this.vel[1] = (k.jump ? 1 : 0) * 7 - (k.down ? 1 : 0) * 7; }
    else { this.onLadder = false; this.vel[1] -= CC.GRAVITY * dt * (water ? 0.35 : 1); if (water) { this.vel[1] = Math.max(this.vel[1], -3); if (k.jump) this.vel[1] = 3.2; } else if (k.jump && this.onGround) this.vel[1] = CC.JUMP;
      const feet = this.world.get(Math.floor(this.pos[0]), Math.floor(this.pos[1] + 0.05), Math.floor(this.pos[2])) === CB.WATER;   // (v53.1: the feet still in it - at the surface, or wading)
      if (k.jump && feet && !this.onGround && this.vel[1] < CC.JUMP * 0.75) { const r = 0.45, ahead = n ? [this.pos[0] + (mx / n) * r, this.pos[2] + (mz / n) * r] : null;
        const bank = ahead && (this.solidAt(ahead[0], this.pos[1] + 0.1, ahead[1]) || this.solidAt(ahead[0], this.pos[1] + 0.6, ahead[1]));
        if (bank || !water) this.vel[1] = CC.JUMP; } }
    for (let i = 0; i < 3; i++) {                                           // (an axis at a time: slide along walls)
      const np = this.pos.slice(); np[i] += this.vel[i] * dt;
      if (!this.boxHits(np[0], np[1], np[2])) this.pos = np;
      else { if (i === 1) { if (this.vel[1] < 0) { this.onGround = true; if (this.flying) this.flying = false; } this.vel[1] = 0; } else this.vel[i] = 0; }
    }
    if (this.vel[1] !== 0) this.onGround = this.boxHits(this.pos[0], this.pos[1] - 0.05, this.pos[2]) && this.vel[1] <= 0;
    // (v12.0) the height a fall began at; on landing, how far it was (read and cleared by the game)
    const wet = this.world.get(Math.floor(this.pos[0]), Math.floor(this.pos[1] + 0.2), Math.floor(this.pos[2])) === CB.WATER;
    if (this.flying || wet) this.fallFrom = null;
    else if (this.onGround) { if (this.fallFrom !== null) { this.landed = Math.max(this.landed, this.fallFrom - this.pos[1]); this.fallFrom = null; } }
    else this.fallFrom = this.fallFrom === null ? this.pos[1] : Math.max(this.fallFrom, this.pos[1]);
    if (this.pos[1] < -10) { const s = this.world.spawn(); this.pos = s.slice(); this.vel = [0, 0, 0]; }
  }
  // Space twice quickly: up into the air, or back down to walk
  pressJump() { if (this.canFly && this.t - this.lastSpace < 0.3) { this.flying = !this.flying; this.vel[1] = 0; this.lastSpace = -9; } else this.lastSpace = this.t; }
};
