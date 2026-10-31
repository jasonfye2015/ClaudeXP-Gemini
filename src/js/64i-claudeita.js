"use strict";
// Claudeita's cave (the thirteenth update): the Timeline's Claudeita (ClaudeGames/claudeita) ported whole - a tall
// world of materials made a few rows at a time as the hero descends, the loose ones (sand, snow, water, lava, acid,
// fire) moved only where something is happening; wands whose spells are cast in order; creatures, five bosses, and a
// sanctuary under each with a fountain and a shop. One hero goes in (61g-cavemouth.js says who, and what is kept).
// Nothing here touches the page: the window draws CM.CaveRun's world (76c-cave.js), and the Node tests drive it as the
// frame loop does - a step is 1/30 of a second, and the run's dice are its own seed's.
//
//   run.step(keys, aim, firing)   keys: { left, right, jump }; aim: [x, y] in cells or null; firing: the button held
//   run.events                    what happened this step, for the window's sounds (emptied by the window)
CM.CV = { W: 512, BIOME_H: 700, SURFACE: 70, ARENA_H: 130, SANCTUARY_H: 80, TICK: 1 / 30, GRAV: 0.18, VIEW_W: 300 };
CM.CV.H = CM.CV.SURFACE + CM.CV.BIOME_H * 5;
// the materials
const CVM = CM.CVM = { AIR: 0, DIRT: 1, ROCK: 2, BEDROCK: 3, SAND: 4, WATER: 5, LAVA: 6, ACID: 7, GOLD: 8, WOOD: 9, ICE: 10, FUNGUS: 11, OBSIDIAN: 12, CRYSTAL: 13, FIRE: 14, SNOW: 15 };
CM.CV_NAMES = ["air", "dirt", "rock", "bedrock", "sand", "water", "lava", "acid", "gold", "wood", "ice", "fungus", "obsidian", "crystal", "fire", "snow"];
const CV_SOLID = new Set([CVM.DIRT, CVM.ROCK, CVM.BEDROCK, CVM.GOLD, CVM.WOOD, CVM.ICE, CVM.FUNGUS, CVM.OBSIDIAN, CVM.CRYSTAL, CVM.SAND, CVM.SNOW]);
const CV_LIQUID = new Set([CVM.WATER, CVM.LAVA, CVM.ACID]), CV_POWDER = new Set([CVM.SAND, CVM.SNOW]);
const CV_SOFT = new Set([CVM.DIRT, CVM.SAND, CVM.SNOW, CVM.FUNGUS, CVM.WOOD, CVM.ICE]), CV_BURNS = new Set([CVM.WOOD, CVM.FUNGUS]);
CM.CV_COLOURS = { [CVM.DIRT]: "#6B4A2E", [CVM.BEDROCK]: "#1E1B22", [CVM.SAND]: "#C9A65A", [CVM.WATER]: "#2F6FD0", [CVM.LAVA]: "#F2561D", [CVM.ACID]: "#7CE33A", [CVM.GOLD]: "#F2C230", [CVM.WOOD]: "#7A5230", [CVM.ICE]: "#A9DDF3", [CVM.FUNGUS]: "#8E4FB0", [CVM.OBSIDIAN]: "#2A1E36", [CVM.CRYSTAL]: "#D06BF0", [CVM.FIRE]: "#FFB020", [CVM.SNOW]: "#EEF4FA" };
CM.CV_BIOMES = [
  { name: "The Mines", rock: "#5B4636", sky: "#140F0C", soft: CVM.DIRT, liquid: CVM.WATER, extra: CVM.WOOD, boss: "Gravelmaw", enemies: ["slime", "bat", "hiisi", "slime"] },
  { name: "The Frozen Depths", rock: "#6E8296", sky: "#0B1118", soft: CVM.SNOW, liquid: CVM.WATER, extra: CVM.ICE, boss: "Rimecaller", enemies: ["bat", "frost", "hiisi", "slime"] },
  { name: "The Fungal Caverns", rock: "#4B3A5E", sky: "#100B14", soft: CVM.FUNGUS, liquid: CVM.ACID, extra: CVM.FUNGUS, boss: "Mother Spore", enemies: ["slime", "spore", "bat", "worm"] },
  { name: "The Magma Vault", rock: "#4A2420", sky: "#140806", soft: CVM.SAND, liquid: CVM.LAVA, extra: CVM.OBSIDIAN, boss: "Cinder Colossus", enemies: ["imp", "hiisi", "worm", "turret"] },
  { name: "The Hollow Heart", rock: "#2A2333", sky: "#07050A", soft: CVM.OBSIDIAN, liquid: CVM.LAVA, extra: CVM.CRYSTAL, boss: "The Unmaker", enemies: ["ghost", "imp", "turret", "frost"] },
];
CM.cvBiomeAt = (y) => Math.max(0, Math.min(CM.CV_BIOMES.length - 1, Math.floor((y - CM.CV.SURFACE) / CM.CV.BIOME_H)));
CM.cvBiomeTop = (b) => CM.CV.SURFACE + b * CM.CV.BIOME_H;
CM.cvArena = (b) => { const C = CM.CV, top = CM.cvBiomeTop(b) + C.BIOME_H - C.ARENA_H - C.SANCTUARY_H; return [56, top + 6, C.W - 56, top + C.ARENA_H - 6]; };
CM.cvSanctuary = (b) => { const C = CM.CV, top = CM.cvBiomeTop(b) + C.BIOME_H - C.SANCTUARY_H; return [120, top + 8, C.W - 120, top + C.SANCTUARY_H - 8]; };
const cvRgb = (hex) => [parseInt(hex.slice(1, 3), 16), parseInt(hex.slice(3, 5), 16), parseInt(hex.slice(5, 7), 16)];
const cvPack = (r, g, b) => ((0xFF << 24) | (Math.max(0, Math.min(255, b)) << 16) | (Math.max(0, Math.min(255, g)) << 8) | Math.max(0, Math.min(255, r))) >>> 0;   // (ABGR: an ImageData's bytes, little-endian)
const cvShade = (rgb, seed) => { const j = ((Math.imul(seed, 2654435761) >>> 7) % 23) - 11; return cvPack(rgb[0] + j, rgb[1] + j, rgb[2] + j); };
const CV_RGB = {}; for (const [m, hex] of Object.entries(CM.CV_COLOURS)) CV_RGB[m] = cvRgb(hex);
const CV_BIOME_RGB = CM.CV_BIOMES.map((B) => ({ rock: cvRgb(B.rock), sky: cvRgb(B.sky) }));
const cvSign = (x, s) => (s < 0 || Object.is(s, -0) ? -Math.abs(x) : Math.abs(x));   // (Python's copysign)
const cvClamp = (v, a, b) => Math.max(a, Math.min(b, v));

// ---- the magic: spells, wands, and casting a wand's spells in order -------------------------------------------------
// A wand is a row of spell slots read left to right. Each cast draws spells until it has a projectile to shoot:
// modifiers on the way change every projectile in the cast, and multicasts draw more projectiles into it. At its last
// slot the wand recharges and starts again. Every spell costs mana, and adds to the delay before the next cast.
CM.WAND_SPELLS = {
  "Spark Bolt": { kind: "proj", mana: 5, delay: 0.05, dmg: 4, speed: 7.0, life: 40, colour: "#FFE36E", size: 1.5, tier: 0, desc: "A quick little bolt." },
  "Magic Missile": { kind: "proj", mana: 30, delay: 0.4, dmg: 18, speed: 4.0, life: 80, boom: 7, colour: "#9EE6FF", size: 2.5, tier: 1, desc: "A slow missile that explodes." },
  "Bouncing Burst": { kind: "proj", mana: 5, delay: -0.03, dmg: 4, speed: 6.0, life: 140, bounce: 10, colour: "#FFB347", size: 1.5, tier: 0, desc: "Bounces off walls many times." },
  Fireball: { kind: "proj", mana: 60, delay: 0.5, dmg: 15, speed: 3.5, life: 90, boom: 10, fire: true, gravity: 0.06, colour: "#FF6A1A", size: 3.0, tier: 2, desc: "Arcs, explodes and sets things alight." },
  Bomb: { kind: "proj", mana: 25, delay: 1.0, dmg: 60, speed: 3.0, life: 70, boom: 16, gravity: 0.15, bounce: 2, fuse: true, colour: "#3A3A3A", size: 3.0, tier: 1, desc: "A bomb that bounces, then blows a big hole." },
  "Energy Orb": { kind: "proj", mana: 18, delay: 0.1, dmg: 12, speed: 3.0, life: 110, pierce: true, colour: "#C77DFF", size: 3.0, tier: 1, desc: "A glowing orb that passes through foes." },
  "Digging Bolt": { kind: "proj", mana: 0, delay: 0.03, dmg: 2, speed: 6.0, life: 22, dig: 2, colour: "#B88A5A", size: 1.0, tier: 0, desc: "Digs through soft ground." },
  "Luminous Drill": { kind: "proj", mana: 10, delay: -0.02, dmg: 10, speed: 8.0, life: 9, dig: 3, drill: true, pierce: true, colour: "#FFF6B0", size: 2.0, tier: 1, desc: "A short beam that drills through rock." },
  "Chain Lightning": { kind: "proj", mana: 40, delay: 0.25, dmg: 20, speed: 0, life: 6, lightning: true, colour: "#E8F1FF", size: 1.0, tier: 2, desc: "Strikes the nearest foe, then jumps." },
  "Acid Ball": { kind: "proj", mana: 20, delay: 0.2, dmg: 8, speed: 3.5, life: 80, gravity: 0.08, splash: "acid", colour: "#7CE33A", size: 2.5, tier: 1, desc: "Bursts into eating acid." },
  "Water Ball": { kind: "proj", mana: 10, delay: 0.15, dmg: 3, speed: 3.5, life: 80, gravity: 0.08, splash: "water", colour: "#3F8DF0", size: 2.5, tier: 0, desc: "Bursts into water." },
  "Ice Shard": { kind: "proj", mana: 12, delay: 0.1, dmg: 9, speed: 5.5, life: 50, freeze: true, colour: "#BDEBFF", size: 2.0, tier: 1, desc: "Sharp, and freezes water it hits." },
  "Black Hole": { kind: "proj", mana: 120, delay: 0.6, dmg: 6, speed: 1.6, life: 110, dig: 7, drill: true, pierce: true, colour: "#05010A", size: 5.0, tier: 3, desc: "Slowly devours everything in its path." },
  "Damage Plus": { kind: "mod", mana: 5, delay: 0.1, add_dmg: 10, tier: 0, desc: "+10 damage." },
  "Speed Up": { kind: "mod", mana: 3, delay: 0.0, speed_x: 1.6, tier: 0, desc: "Faster projectiles." },
  Homing: { kind: "mod", mana: 40, delay: 0.1, homing: true, tier: 2, desc: "Projectiles seek foes." },
  Bounce: { kind: "mod", mana: 1, delay: 0.0, add_bounce: 5, tier: 0, desc: "Projectiles bounce." },
  "Explosive Shot": { kind: "mod", mana: 30, delay: 0.15, add_boom: 6, tier: 1, desc: "Projectiles explode." },
  Piercing: { kind: "mod", mana: 30, delay: 0.0, pierce: true, tier: 2, desc: "Pass through foes." },
  "Heavy Shot": { kind: "mod", mana: 7, delay: 0.15, dmg_x: 1.6, add_dmg: 5, speed_x: 0.6, tier: 1, desc: "Slower, much harder hitting." },
  "Fire Trail": { kind: "mod", mana: 10, delay: 0.0, trail: true, tier: 1, desc: "Leaves fire behind." },
  "Double Spell": { kind: "multi", mana: 0, delay: 0.0, draw: 2, tier: 1, desc: "Casts the next two spells at once." },
  "Triple Spell": { kind: "multi", mana: 2, delay: 0.0, draw: 3, tier: 2, desc: "Casts the next three spells at once." },
  "Scatter 4": { kind: "multi", mana: 1, delay: 0.0, draw: 4, spread: 18, tier: 2, desc: "Four spells at once, scattered." },
};
CM.WAND_NAMES = ["Twig", "Rod", "Scepter", "Staff", "Wand", "Branch", "Spindle", "Baton"];
CM.WAND_ADJ = ["Humble", "Crackling", "Ancient", "Whispering", "Bright", "Hungry", "Restless", "Sly", "Grim", "Gilded"];
CM.WAND_COLOURS = ["#7A5230", "#5E6E7A", "#8E3B46", "#3F6E4A", "#6B4FA0", "#B08A2E"];
const cvUniform = (rnd, a, b) => a + (b - a) * rnd.next();
CM.spellsUpTo = (tier) => Object.keys(CM.WAND_SPELLS).filter((n) => CM.WAND_SPELLS[n].tier <= tier);
CM.randomSpell = (depth, rnd) => {
  const pool = CM.spellsUpTo(Math.min(3, Math.floor(depth + rnd.next() * 1.2))), w = pool.map((n) => (CM.WAND_SPELLS[n].kind === "proj" ? 3 : 1.5));
  let r = rnd.next() * w.reduce((s, k) => s + k, 0); for (let i = 0; i < pool.length; i++) { r -= w[i]; if (r < 0) return pool[i]; } return pool[pool.length - 1];
};
CM.Wand = class {
  constructor(o) { Object.assign(this, { slots: [], mana_max: 100, charge: 30, delay: 0.2, recharge: 0.5, spread: 0, name: "Wand", colour: "#7A5230" }, o); this.slots = this.slots.slice(); this.mana = this.mana_max; this.cursor = 0; this.wait = 0; this.recharging = false; }
  toJSON() { const o = {}; for (const k of ["slots", "mana_max", "charge", "delay", "recharge", "spread", "name", "colour"]) o[k] = this[k]; return o; }
  tick(dt) { this.mana = Math.min(this.mana_max, this.mana + this.charge * dt); if (this.wait > 0) { this.wait = Math.max(0, this.wait - dt); if (this.wait === 0) this.recharging = false; } }
  // -> [[spell, [modifiers], spread]] to shoot now, or [] if it can't
  cast() {
    if (this.wait > 0 || !this.slots.some(Boolean)) return [];
    const shots = [], mods = []; let want = 1, spread = this.spread, delay = this.delay; const start = this.cursor;
    while (want > 0) {
      if (this.cursor >= this.slots.length) break;
      const name = this.slots[this.cursor]; this.cursor += 1;
      if (!name) continue;
      const s = CM.WAND_SPELLS[name];
      if (this.mana < s.mana) break;                                     // (not enough mana: the cast fizzles here)
      this.mana -= s.mana; delay += s.delay;
      if (s.kind === "mod") mods.push(name);
      else if (s.kind === "multi") { want += s.draw - 1; spread += s.spread || 4; }
      else { shots.push([name, null, spread]); want -= 1; }
    }
    for (const sh of shots) sh[1] = mods.slice();
    const end = this.cursor >= this.slots.length || this.slots.slice(this.cursor).every((n) => !n);
    if (end) { this.cursor = 0; this.wait = Math.max(delay, this.recharge); this.recharging = true; } else this.wait = Math.max(0.03, delay);
    if (!shots.length && this.cursor === start) this.wait = 0.2;
    return shots;
  }
};
// a wand found (or sold) at this depth (0 = the Mines .. 4 = the Hollow Heart): better the deeper
CM.randomWand = (depth, rnd, slots) => {
  const t = depth + rnd.next(), cap = slots || Math.max(2, Math.min(12, Math.floor(2 + t * 1.6 + rnd.next() * 2)));
  const mana_max = Math.floor(80 + t * 220 * cvUniform(rnd, 0.7, 1.3)), charge = Math.floor(25 + t * 60 * cvUniform(rnd, 0.6, 1.4));
  const delay = Math.round(Math.max(0.02, 0.3 - t * 0.05 * cvUniform(rnd, 0.5, 1.2)) * 100) / 100, recharge = Math.round(Math.max(0.05, 0.9 - t * 0.15 * cvUniform(rnd, 0.5, 1.3)) * 100) / 100;
  const spread = Math.round(Math.max(0, cvUniform(rnd, 0, 12) - t * 2) * 10) / 10;
  const projs = CM.spellsUpTo(Math.min(3, Math.floor(t))).filter((n) => CM.WAND_SPELLS[n].kind === "proj" && n !== "Digging Bolt"), fill = [];
  for (let i = 0; i < cap; i++) fill.push(rnd.next() < 0.55 + 0.05 * depth ? (i ? CM.randomSpell(depth, rnd) : rnd.pick(projs)) : null);
  if (!fill.some((n) => n && CM.WAND_SPELLS[n].kind === "proj")) fill[0] = rnd.pick(projs);
  return new CM.Wand({ slots: fill, mana_max, charge, delay, recharge, spread, name: `${rnd.pick(CM.WAND_ADJ)} ${rnd.pick(CM.WAND_NAMES)}`, colour: rnd.pick(CM.WAND_COLOURS) });
};
// the default wands, given to whoever goes in
CM.starterWands = () => [new CM.Wand({ slots: ["Spark Bolt", "Spark Bolt", null], mana_max: 110, charge: 40, delay: 0.12, recharge: 0.35, spread: 3, name: "Apprentice's Wand", colour: "#7A5230", given: true }),
  new CM.Wand({ slots: ["Bomb", null], mana_max: 60, charge: 15, delay: 0.2, recharge: 1.2, spread: 0, name: "Miner's Rod", colour: "#5E6E7A", given: true })];

// ---- the world: a tall grid of materials, made a few rows at a time --------------------------------------------------
CM.CaveWorld = class {
  constructor(seed) {
    const C = CM.CV; this.seed = seed >>> 0; this.rng = new CM.Random(this.seed);
    this.cells = new Uint8Array(C.W * C.H); this.pix = new Uint32Array(C.W * C.H).fill(0xFF000000);
    this.made = 0; this.active = new Set(); this.fireLife = new Map(); this.spawns = []; this.items = []; this.gates = {}; this.plans = {}; this.changed = 0;
  }
  get(x, y) { const C = CM.CV; return x >= 0 && x < C.W && y >= 0 && y < C.H ? this.cells[y * C.W + x] : CVM.BEDROCK; }
  solid(x, y) { return CV_SOLID.has(this.get(Math.floor(x), Math.floor(y))); }
  colourOf(m, x, y) {
    if (m === CVM.AIR) { const c = CV_BIOME_RGB[CM.cvBiomeAt(y)].sky, j = (((x * 92821 + y * 68917) >> 5) % 5 + 5) % 5; return cvPack(c[0] + j, c[1] + j, c[2] + j); }   // (open cave: near-black, the faintest grain)
    if (m === CVM.ROCK) return cvShade(CV_BIOME_RGB[CM.cvBiomeAt(y)].rock, x * 92821 + y);
    return cvShade(CV_RGB[m], x * 92821 + y);
  }
  set(x, y, m, wake = true) {
    const C = CM.CV; if (!(x >= 0 && x < C.W && y >= 0 && y < C.H)) return;
    const i = y * C.W + x; if (this.cells[i] === m) return;
    this.cells[i] = m; this.pix[i] = this.colourOf(m, x, y); this.changed += 1;
    if (m === CVM.FIRE) this.fireLife.set(i, this.rng.int(30, 70));
    if (wake) this.wake(x, y);
  }
  wake(x, y) {
    const C = CM.CV;
    for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) { const xx = x + dx, yy = y + dy; if (xx >= 0 && xx < C.W && yy >= 0 && yy < C.H) { const m = this.cells[yy * C.W + xx]; if (CV_LIQUID.has(m) || CV_POWDER.has(m) || m === CVM.FIRE) this.active.add(yy * C.W + xx); } }
  }
  // a biome's layout before its rows are made: the noise lattice, a winding way down
  plan(b) {
    if (this.plans[b]) return this.plans[b];
    const C = CM.CV, rng = new CM.Random((this.seed * 31 + b) >>> 0), top = CM.cvBiomeTop(b), lat = {};
    for (const scale of [48, 16]) { const cols = Math.floor(C.W / scale) + 2, rows = Math.floor(C.BIOME_H / scale) + 2; lat[scale] = []; for (let r = 0; r < rows; r++) { const row = []; for (let c = 0; c < cols; c++) row.push(rng.next()); lat[scale].push(row); } }
    const path = []; let x = b === 0 ? C.W / 2 : C.W / 2 + rng.int(-60, 60); const arenaTop = C.BIOME_H - C.ARENA_H - C.SANCTUARY_H;
    for (let y = 0; y < C.BIOME_H; y++) {
      if (y > arenaTop - 160) x += x < C.W / 2 ? 1 : x > C.W / 2 ? -1 : 0;   // (steering back to the middle, where the arena's door is)
      else if (y % 3 === 0) x += rng.pick([-2, -1, 0, 1, 2]) + (x < 120 ? 1 : x > C.W - 120 ? -1 : 0);
      path.push(x);
    }
    const ix = {}; for (const s of [48, 16]) { ix[s] = []; for (let xx = 0; xx < C.W; xx++) ix[s].push([Math.floor(xx / s), (xx % s) / s]); }
    return (this.plans[b] = { lat, path, ix, top });
  }
  makeRows(upto) {
    const C = CM.CV; upto = Math.min(C.H, upto);
    while (this.made < upto) { this.makeRow(this.made); this.made += 1; const y = this.made; if (y > C.SURFACE && (y - C.SURFACE) % 140 === 0) this.features(y - 140, y); }
  }
  makeRow(y) {
    const C = CM.CV, out = this.cells, W = C.W;
    if (y < C.SURFACE) {                                                  // the surface: a ledge to start from, the cave mouth's light above
      for (let x = 0; x < W; x++) { const m = x < 3 || x >= W - 3 ? CVM.BEDROCK : y > C.SURFACE - 6 && Math.abs(x - W / 2) > 18 ? CVM.ROCK : CVM.AIR; out[y * W + x] = m; this.pix[y * W + x] = m ? this.colourOf(m, x, y) : cvPack(18 + y / 6, 16 + y / 7, 22 + y / 5); }
      return;
    }
    const b = CM.cvBiomeAt(y), bio = CM.CV_BIOMES[b], plan = this.plan(b), ly = y - plan.top;
    const a0 = this.lerpRows(plan.lat[48], ly / 48), a1 = this.lerpRows(plan.lat[16], ly / 16);
    const cx = plan.path[ly], arenaTop = C.BIOME_H - C.ARENA_H - C.SANCTUARY_H, soft = bio.soft, extra = bio.extra;
    for (let x = 0; x < W; x++) {
      const [i48, t48] = plan.ix[48][x], [i16, t16] = plan.ix[16][x], n48 = a0[i48] + (a0[i48 + 1] - a0[i48]) * t48, n16 = a1[i16] + (a1[i16 + 1] - a1[i16]) * t16, n = n48 * 0.65 + n16 * 0.35;
      let m;
      if (x < 3 || x >= W - 3) m = CVM.BEDROCK;
      else if (n > 0.56) { m = CVM.ROCK; if (n16 > 0.9 && n48 > 0.62) m = CVM.GOLD; else if (n48 > 0.86 && n16 < 0.45) m = extra !== CVM.WOOD ? extra : CVM.ROCK; }   // (gold: small veins deep in the rock; the biome's own stone in patches)
      else if (n > 0.5) m = soft;
      else m = CVM.AIR;
      if (Math.abs(x - cx) < 9 && ly < arenaTop) m = CVM.AIR;            // the way down
      out[y * W + x] = m;
    }
    if (ly >= arenaTop) this.structures(b, y, ly - arenaTop);           // the boss's arena and the sanctuary below it
    if (ly < 10 && b > 0) for (let x = W / 2 - 10; x < W / 2 + 10; x++) out[y * W + x] = CVM.AIR;   // (the hole from the sanctuary above)
    for (let x = 0; x < W; x++) this.pix[y * W + x] = this.colourOf(out[y * W + x], x, y);
  }
  lerpRows(lat, fy) { const i = Math.floor(fy); let t = fy - i; const r0 = lat[Math.min(i, lat.length - 1)], r1 = lat[Math.min(i + 1, lat.length - 1)]; t = t * t * (3 - 2 * t); return r0.map((a, k) => a + (r1[k] - a) * t); }
  // the arena (a bedrock-walled hall with a gate in its floor) and the sanctuary under it
  structures(b, y, ay) {
    const C = CM.CV, W = C.W, out = this.cells, [x0, y0, x1, y1] = CM.cvArena(b), [s0, sy0, s1, sy1] = CM.cvSanctuary(b), base = y * W;
    if (ay < C.ARENA_H) {
      for (let x = 0; x < W; x++) { const inside = x >= x0 && x < x1 && y >= y0 && y < y1, wall = x >= x0 - 6 && x < x1 + 6 && y >= y0 - 6 && y < y1 + 6 && !inside; if (inside) out[base + x] = CVM.AIR; else if (wall) out[base + x] = CVM.BEDROCK; }
      if (y >= y0 - 6 && y < y0) for (let x = W / 2 - 9; x < W / 2 + 9; x++) out[base + x] = CVM.AIR;   // (a way in from the cave above)
      if (y >= y1 && y < y1 + 6) { const gate = this.gates[b] = this.gates[b] || []; for (let x = W / 2 - 9; x < W / 2 + 9; x++) gate.push([x, y]); }   // (the gate down: open when the boss falls)
    } else {
      for (let x = 0; x < W; x++) { const inside = x >= s0 && x < s1 && y >= sy0 && y < sy1; if (inside || (y < sy0 && Math.abs(x - W / 2) < 9)) out[base + x] = CVM.AIR; else if ((x >= s0 - 8 && x < s1 + 8) || y < sy0) out[base + x] = CVM.BEDROCK; }
      if (y >= sy1 && b < CM.CV_BIOMES.length - 1) for (let x = W / 2 - 10; x < W / 2 + 10; x++) out[base + x] = CVM.AIR;   // (the way on, through the floor)
      if (y === sy1 - 1 && b < CM.CV_BIOMES.length - 1) {
        this.items.push(["fountain", s0 + 30, y, b]); this.items.push(["rope", s1 - 24, y, b]);   // (the rope up: out with what you carry - the Wood's, not Claudeita's)
        ["wand", "spell", "spell", "wand", "spell"].forEach((kind, i) => this.items.push([`shop_${kind}`, s0 + 70 + i * 34, y, b]));
      }
    }
  }
  // pools, creatures and finds, for a band of rows now complete
  features(y0, y1) {
    const C = CM.CV, b = CM.cvBiomeAt(y0), bio = CM.CV_BIOMES[b], rng = this.rng, arenaTop = CM.cvBiomeTop(b) + C.BIOME_H - C.ARENA_H - C.SANCTUARY_H;
    y1 = Math.min(y1, arenaTop - 4); if (y1 - y0 < 20) return;
    for (let k = 0; k < 6; k++) { const spot = this.floorSpot(rng, y0 + 5, y1 - 2); if (spot) this.pool(spot[0], spot[1], rng.next() < 0.75 ? bio.liquid : CVM.WATER, rng.int(3, 7)); }
    if (b < 3 && rng.next() < 0.6) for (let t = 0; t < 30; t++) {        // a wooden platform or two in the upper caves
      const x = rng.int(30, C.W - 60), y = rng.int(y0 + 5, y1 - 5);
      if ([0, 5, 10, 15, 20, 25].every((i) => this.get(x + i, y) === CVM.AIR)) { const n = rng.int(14, 30); for (let i = 0; i < n; i++) if (this.get(x + i, y) === CVM.AIR) this.set(x + i, y, CVM.WOOD, false); break; }
    }
    const depth = b + (y0 - CM.cvBiomeTop(b)) / C.BIOME_H;
    for (let k = 0; k < Math.floor(6 + depth * 1.6); k++) {             // creatures: the flyers anywhere open, the rest on a floor
      const kind = rng.pick(bio.enemies);
      if (["bat", "imp", "ghost", "frost"].includes(kind)) { for (let t = 0; t < 40; t++) { const x = rng.int(10, C.W - 10), y = rng.int(y0 + 4, y1 - 2); if (this.get(x, y) === CVM.AIR && this.get(x, y - 6) === CVM.AIR) { this.spawns.push([kind, x, y, b]); break; } } }
      else { const spot = this.floorSpot(rng, y0 + 4, y1 - 2); if (spot) this.spawns.push([kind, spot[0], spot[1], b]); }
    }
    for (const [kind, n] of [["wand", 0.6], ["spell", 1.6], ["heart", 0.2]]) { const k = Math.floor(n) + (rng.next() < n % 1 ? 1 : 0); for (let i = 0; i < k; i++) { const spot = this.floorSpot(rng, y0 + 4, y1 - 2); if (spot) this.items.push([kind, spot[0], spot[1], b]); } }
  }
  // a spot on a cave floor in these rows (air, with something solid under it), or null
  floorSpot(rng, y0, y1) {
    for (let t = 0; t < 30; t++) {
      const x = rng.int(12, CM.CV.W - 12); let y = rng.int(y0, y1 - 1);
      while (y < y1 && this.get(x, y) !== CVM.AIR) y++;
      while (y < y1 && this.get(x, y + 1) === CVM.AIR) y++;
      if (y < y1 && this.get(x, y) === CVM.AIR && CV_SOLID.has(this.get(x, y + 1)) && this.get(x, y - 10) === CVM.AIR) return [x, y];
    }
    return null;
  }
  pool(x, y, liquid, depth) {
    for (let dy = 0; dy < depth; dy++) { const yy = y - dy; for (const d of [-1, 1]) { let xx = d === 1 ? x : x - 1; for (let k = 0; k < 60; k++) { if (this.get(xx, yy) !== CVM.AIR || this.get(xx, yy + 1) === CVM.AIR) break; this.set(xx, yy, liquid, false); xx += d; } } }
  }
  openGate(b) { for (const [x, y] of this.gates[b] || []) this.set(x, y, CVM.AIR); }
  // move what moves: powders fall, liquids flow, lava meets water, acid eats, fire burns
  step(budget = 2500) {
    if (!this.active.size) return;
    const C = CM.CV, W = C.W, cells = this.cells, rng = this.rng, todo = [...this.active].sort((a, b) => b - a).slice(0, budget);
    for (const i of todo) this.active.delete(i);
    for (const i of todo) {
      const m = cells[i], y = Math.floor(i / W), x = i - y * W;
      if (y >= C.H - 1) continue;
      if (m === CVM.FIRE) {
        let life = (this.fireLife.get(i) || 0) - 1;
        for (const [dx, dy] of [[1, 0], [-1, 0], [0, -1], [0, 1]]) { const n = this.get(x + dx, y + dy); if (CV_BURNS.has(n) && rng.next() < 0.08) this.set(x + dx, y + dy, CVM.FIRE); else if (n === CVM.ICE && rng.next() < 0.1) this.set(x + dx, y + dy, CVM.WATER); else if (n === CVM.WATER) life = 0; }
        if (life <= 0) { this.fireLife.delete(i); this.set(x, y, CVM.AIR); }
        else { this.fireLife.set(i, life); if (rng.next() < 0.3 && this.get(x, y - 1) === CVM.AIR) { this.set(x, y, CVM.AIR); this.set(x, y - 1, CVM.FIRE); this.fireLife.set((y - 1) * W + x, life); } else this.active.add(i); }   // (flames rise a little)
        continue;
      }
      if (!CV_LIQUID.has(m) && !CV_POWDER.has(m)) continue;
      const below = cells[i + W];
      if (CV_POWDER.has(m)) {
        if (below === CVM.AIR || CV_LIQUID.has(below)) { this.swap(x, y, x, y + 1); continue; }
        const d = rng.pick([-1, 1]); for (const dx of [d, -d]) { const n = this.get(x + dx, y + 1); if (n === CVM.AIR || n === CVM.WATER) { this.swap(x, y, x + dx, y + 1); break; } }
        continue;
      }
      if (m === CVM.LAVA || m === CVM.ACID) {                            // liquids that do something to what they touch
        for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
          const n = this.get(x + dx, y + dy);
          if (m === CVM.LAVA && n === CVM.WATER) { this.set(x, y, CVM.OBSIDIAN); this.set(x + dx, y + dy, CVM.AIR); break; }
          if (m === CVM.LAVA && CV_BURNS.has(n) && rng.next() < 0.05) this.set(x + dx, y + dy, CVM.FIRE);
          if (m === CVM.ACID && n !== CVM.AIR && n !== CVM.ACID && n !== CVM.BEDROCK && n !== CVM.GOLD && !CV_LIQUID.has(n) && rng.next() < 0.03) { this.set(x + dx, y + dy, CVM.AIR); if (rng.next() < 0.3) this.set(x, y, CVM.AIR); break; }
        }
        if (cells[i] !== m) continue;
      }
      if (below === CVM.AIR) { this.swap(x, y, x, y + 1); continue; }
      const d = rng.pick([-1, 1]); let moved = false;
      for (const dx of [d, -d]) if (this.get(x + dx, y + 1) === CVM.AIR) { this.swap(x, y, x + dx, y + 1); moved = true; break; }
      if (moved) continue;
      for (const dx of [d, -d]) { let reach = 1; while (reach <= 3 && this.get(x + dx * reach, y) === CVM.AIR) reach++; if (reach > 1) { this.swap(x, y, x + dx * (reach - 1), y); break; } }
    }
  }
  swap(x0, y0, x1, y1) {
    const W = CM.CV.W, a = this.get(x0, y0), b = this.get(x1, y1);
    this.set(x0, y0, b, false); this.set(x1, y1, a, false); this.wake(x0, y0); this.wake(x1, y1);
    for (const i of [y0 * W + x0, y1 * W + x1]) { const m = this.cells[i]; if (CV_LIQUID.has(m) || CV_POWDER.has(m)) this.active.add(i); }
  }
  // a disc cleared; how many gold cells it broke (they drop gold)
  carve(cx, cy, r, { hard = true, fire = false, softOnly = false } = {}) {
    let gold = 0; const r2 = r * r; cx = Math.floor(cx); cy = Math.floor(cy);
    for (let dy = -r; dy <= r; dy++) for (let dx = -r; dx <= r; dx++) {
      if (dx * dx + dy * dy > r2) continue;
      const x = cx + dx, y = cy + dy, m = this.get(x, y);
      if (m === CVM.AIR || m === CVM.BEDROCK || CV_LIQUID.has(m)) continue;
      if (softOnly && !CV_SOFT.has(m)) continue;
      if (!hard && (m === CVM.OBSIDIAN || m === CVM.CRYSTAL) && dx * dx + dy * dy > r2 * 0.3) continue;
      if (m === CVM.GOLD) gold += 1;
      this.set(x, y, fire && this.rng.next() < 0.25 ? CVM.FIRE : CVM.AIR);
    }
    for (let dy = -r - 1; dy <= r + 1; dy++) for (const dx of [-r - 1, r + 1]) this.wake(cx + dx, cy + dy);   // (wake what sits around the hole)
    for (let dx = -r - 1; dx <= r + 1; dx++) this.wake(cx + dx, cy - r - 1);
    return gold;
  }
  splash(cx, cy, m, r = 3) { for (let dy = -r; dy <= r; dy++) for (let dx = -r; dx <= r; dx++) if (dx * dx + dy * dy <= r * r && this.get(Math.floor(cx) + dx, Math.floor(cy) + dy) === CVM.AIR) this.set(Math.floor(cx) + dx, Math.floor(cy) + dy, m); }
  freeze(cx, cy, r = 5) { for (let dy = -r; dy <= r; dy++) for (let dx = -r; dx <= r; dx++) { const x = Math.floor(cx) + dx, y = Math.floor(cy) + dy; if (dx * dx + dy * dy <= r * r && this.get(x, y) === CVM.WATER) { this.set(x, y, CVM.ICE); this.active.delete(y * CM.CV.W + x); } } }
};

// ---- the things in it ------------------------------------------------------------------------------------------------
// hp, speed, damage, gold, how it moves, colour, [w, h], its spell or null, the spell's cooldown (steps)
CM.CV_ENEMIES = {
  slime: [18, 0.6, 8, 6, "hop", "#5BC85B", [8, 6], null, 0], bat: [10, 1.5, 6, 4, "fly", "#4A3B5C", [7, 5], null, 0],
  hiisi: [30, 0.7, 10, 12, "walk", "#B0533C", [6, 11], "Spark Bolt", 70], frost: [26, 1.0, 8, 12, "fly", "#9FD8F5", [7, 7], "Ice Shard", 80],
  spore: [22, 0.5, 8, 10, "walk", "#B56FD6", [8, 8], "Acid Ball", 90], worm: [60, 0.9, 14, 18, "dig", "#C07A6A", [6, 6], null, 0],
  imp: [34, 1.2, 10, 16, "fly", "#E2481F", [7, 8], "Fireball", 100], turret: [50, 0.0, 10, 20, "still", "#6E6E7A", [9, 8], "Magic Missile", 75],
  ghost: [40, 0.9, 14, 20, "ghost", "#D9D6F5", [8, 10], null, 0],
};
CM.CV_BOSSES = ["Gravelmaw", "Rimecaller", "Mother Spore", "Cinder Colossus", "The Unmaker"];
CM.CV_BOSS_HP = [700, 900, 1200, 1600, 3500];
CM.CV_XP = { per: (b) => Math.round((10 + 8 * (2 + 4 * b)) * 0.33), boss: [150, 300, 500, 800, 1500] };   // (experience for the party's hero: a kill's, a boss's)
const cvBox = (o) => [o.x - o.w / 2, o.y - o.h, o.x + o.w / 2, o.y];
const cvHits = (a, b, pad = 0) => { const p = cvBox(a), q = cvBox(b); return p[0] - pad < q[2] && p[2] + pad > q[0] && p[1] - pad < q[3] && p[3] + pad > q[1]; };
const cvBody = (o, x, y, w, h) => Object.assign(o, { x, y, w, h, vx: 0, vy: 0, onGround: false });   // (x the middle, y the feet)
CM.cvBlocked = (world, x0, y0, x1, y1) => { for (let yy = Math.floor(y0); yy < Math.ceil(y1); yy++) for (let xx = Math.floor(x0); xx < Math.ceil(x1); xx++) if (world.solid(xx, yy)) return true; return false; };
// move with the terrain in the way: step up small ledges, stop at walls, land on floors
CM.cvMove = (b, world, stepUp = 2, through = false) => {
  if (through) { b.x += b.vx; b.y += b.vy; return; }
  const dx = b.vx; let n = Math.ceil(Math.abs(dx));
  for (let i = 0; i < n; i++) {
    const s = cvSign(Math.min(1, Math.abs(dx) - i), dx), x0 = b.x - b.w / 2 + s, y0 = b.y - b.h, x1 = b.x + b.w / 2 + s, y1 = b.y;
    if (!CM.cvBlocked(world, x0, y0, x1, y1)) { b.x += s; continue; }
    let up = 1; for (; up <= stepUp; up++) if (!CM.cvBlocked(world, x0, y0 - up, x1, y1 - up)) { b.x += s; b.y -= up; break; }
    if (up > stepUp) { b.vx = 0; break; }
  }
  const dy = b.vy; b.onGround = false; n = Math.ceil(Math.abs(dy));
  for (let i = 0; i < n; i++) {
    const s = cvSign(Math.min(1, Math.abs(dy) - i), dy);
    if (CM.cvBlocked(world, b.x - b.w / 2, b.y - b.h + s, b.x + b.w / 2, b.y + s)) { if (s > 0) b.onGround = true; b.vy = 0; break; }
    b.y += s;
  }
  if (!b.onGround && b.vy >= 0 && CM.cvBlocked(world, b.x - b.w / 2, b.y, b.x + b.w / 2, b.y + 1)) b.onGround = true;
};
// what the body stands in (liquids, fire): the worst of it
CM.cvIn = (world, b) => {
  const found = new Set();
  for (let yy = Math.floor(b.y - b.h); yy < Math.floor(b.y); yy += 3) for (let xx = Math.floor(b.x - b.w / 2); xx <= Math.floor(b.x + b.w / 2); xx += 2) found.add(world.get(xx, yy));
  for (const m of [CVM.LAVA, CVM.ACID, CVM.FIRE, CVM.WATER]) if (found.has(m)) return m;
  return CVM.AIR;
};
CM.CaveShot = class {
  constructor(name, mods, x, y, angle, owner, dmgScale = 1) {
    const s = CM.WAND_SPELLS[name]; let speed = s.speed, dmg = s.dmg * dmgScale;
    Object.assign(this, { name, owner, bounce: s.bounce || 0, boom: s.boom || 0, pierce: Boolean(s.pierce), homing: false, trail: false });
    for (const m of mods || []) {
      const ms = CM.WAND_SPELLS[m]; dmg = dmg * (ms.dmg_x || 1) + (ms.add_dmg || 0); speed *= ms.speed_x || 1; this.bounce += ms.add_bounce || 0;
      this.boom = Math.max(this.boom, ms.add_boom || 0) + (this.boom && ms.add_boom ? 2 : 0);
      this.pierce = this.pierce || Boolean(ms.pierce); this.homing = this.homing || Boolean(ms.homing); this.trail = this.trail || Boolean(ms.trail);
    }
    Object.assign(this, { dmg, x, y, vx: Math.cos(angle) * speed, vy: Math.sin(angle) * speed, life: s.life, gravity: s.gravity || 0, colour: s.colour || "#FFFFFF", size: s.size || 1.5, dig: s.dig || 0, drill: Boolean(s.drill),
      fire: Boolean(s.fire), splash: s.splash || null, freeze: Boolean(s.freeze), fuse: Boolean(s.fuse), lightning: Boolean(s.lightning), hit: new Set(), dead: false });
  }
};

// ---- the run: one hero, the world, its creatures ----------------------------------------------------------------------
//   opts: { hp, hpMax, dmgScale, wands (CM.Wand[] besides the default two), spells, name }
CM.CaveRun = class {
  constructor(seed, opts = {}) {
    const C = CM.CV; this.seed = seed >>> 0; this.rnd = new CM.Random((this.seed ^ 0x5bd1e995) >>> 0);
    this.world = new CM.CaveWorld(this.seed); this.world.makeRows(C.SURFACE + 420);
    const p = this.player = cvBody({}, C.W / 2 - 40, C.SURFACE - 6, 5, 11);
    Object.assign(p, { hpMax: opts.hpMax || 100, lev: 100, current: 0, gold: 0, facing: 1, hurt: 0, kills: 0, spells: (opts.spells || ["Digging Bolt", "Spark Bolt"]).slice(0, 16), name: opts.name || "The hero" });
    p.hp = Math.min(p.hpMax, opts.hp || p.hpMax);
    p.wands = CM.starterWands().concat((opts.wands || []).map((w) => Object.assign(new CM.Wand(w), { own: true }))).slice(0, 4);
    this.dmgScale = opts.dmgScale || 1;
    this.enemies = []; this.shots = []; this.pickups = []; this.particles = []; this.texts = []; this.bolts = []; this.events = [];
    this.spawned = 0; this.itemised = 0; this.boss = null; this.bossesDown = new Set(); this.bossStarted = new Set(); this.biomeSeen = -1;
    this.banner = ["", 0]; this.shake = 0; this.tickN = 0; this.over = null; this.xp = 0; this.loot = []; this.cam = [p.x, p.y];
    this.populate();
  }
  get wand() { const p = this.player; return p.wands[p.current] || null; }
  ev(kind, extra) { this.events.push(Object.assign({ kind }, extra || {})); if (this.events.length > 200) this.events.shift(); }
  // the world filling in: its creatures and finds, as their rows are made
  populate() {
    const w = this.world;
    for (const [kind, x, y, b] of w.spawns.slice(this.spawned)) this.enemies.push(this.makeEnemy(kind, x, y, b));
    this.spawned = w.spawns.length;
    for (const [kind, x, y, b] of w.items.slice(this.itemised)) {
      if (kind === "wand") this.pickups.push(this.pickup("wand", x, y, CM.randomWand(b, this.rnd)));
      else if (kind === "spell") this.pickups.push(this.pickup("spell", x, y, CM.randomSpell(b, this.rnd)));
      else if (kind === "heart" || kind === "fountain" || kind === "rope") this.pickups.push(this.pickup(kind, x, y));
      else if (kind === "shop_wand") this.pickups.push(this.pickup("wand", x, y, CM.randomWand(b + 1, this.rnd), 120 + b * 160));
      else if (kind === "shop_spell") this.pickups.push(this.pickup("spell", x, y, CM.randomSpell(b + 1, this.rnd), 50 + b * 70));
    }
    this.itemised = w.items.length;
  }
  makeEnemy(kind, x, y, biome) {
    const [hp, speed, dmg, gold, move, colour, [w, h], spell, cd] = CM.CV_ENEMIES[kind], k = 1 + biome * 0.6;
    return cvBody({ kind, hp: hp * k, hpMax: hp * k, speed, dmg: dmg * k, gold: Math.floor(gold * (1 + biome)), move, colour, spell, cd, timer: this.rnd.int(0, Math.max(1, cd)), t: this.rnd.next() * 10, awake: false, facing: -1, boss: false, biome }, x, y, w, h);
  }
  makeBoss(index, x, y) {
    const e = this.makeEnemy("ghost", x, y, index);
    return Object.assign(e, { kind: CM.CV_BOSSES[index], index, boss: true, hp: CM.CV_BOSS_HP[index], hpMax: CM.CV_BOSS_HP[index], dmg: 18 + index * 6, gold: 200 * (index + 1),
      w: [12, 16, 26, 20, 22][index], h: [12, 16, 22, 28, 22][index], colour: ["#C07A6A", "#BDEBFF", "#B56FD6", "#E2481F", "#F2EEFF"][index], segments: index === 0 ? Array.from({ length: 14 }, () => [x, y]) : [], phase: 1, awake: true });
  }
  pickup(kind, x, y, value = null, price = 0) { return cvBody({ kind, value, price, t: this.rnd.next() * 6 }, x, y, ["wand", "spell", "heart"].includes(kind) ? 6 : 3, kind !== "gold" ? 6 : 3); }
  // ---- a step ----
  step(keys = {}, aim = null, firing = false) {
    if (this.over) return;
    this.tickN += 1;
    const p = this.player, w = this.world, need = Math.floor(this.cam[1]) + 320;
    if (w.made < need) { w.makeRows(Math.min(need, w.made + (w.made > need - 200 ? 8 : 4))); this.populate(); }   // (a few rows a step: a fall is never faster than this)
    this.stepPlayer(keys, aim, firing);
    for (const e of this.enemies.slice()) this.stepEnemy(e);
    for (const s of this.shots.slice()) this.stepShot(s);
    for (const k of this.pickups.slice()) this.stepPickup(k);
    w.step(1800);
    for (const q of this.particles) { q[0] += q[2]; q[1] += q[3]; q[3] += q[6] ? 0.12 : 0; q[4] -= 1; }
    this.particles = this.particles.filter((q) => q[4] > 0);
    for (const t of this.texts) { t[1] -= 0.4; t[3] -= 1; }
    this.texts = this.texts.filter((t) => t[3] > 0);
    this.bolts = this.bolts.filter((b) => b[2] > 1).map(([a, b, life]) => [a, b, life - 1]);
    this.shake *= 0.85;
    const b = CM.cvBiomeAt(Math.floor(p.y));
    if (b !== this.biomeSeen && p.y > CM.CV.SURFACE) { this.biomeSeen = b; this.banner = [CM.CV_BIOMES[b].name, 120]; this.ev("biome", { b }); }
    if (this.banner[1]) this.banner = [this.banner[0], this.banner[1] - 1];
    this.bossCheck();
    this.cam[0] += (p.x - this.cam[0]) * 0.15; this.cam[1] += (p.y - 20 - this.cam[1]) * 0.15;
  }
  stepPlayer(keys, aim, firing) {
    const p = this.player, w = this.world, accel = p.onGround ? 0.35 : 0.22, want = (keys.right ? 1 : 0) - (keys.left ? 1 : 0);
    p.vx += (want * 1.4 - p.vx) * accel;
    const medium = CM.cvIn(w, p);
    if (keys.jump) { if (p.onGround) p.vy = -3.0; else if (p.lev > 0) { p.vy = Math.max(-2.2, p.vy - 0.34); p.lev -= 1.2; } }
    if (p.onGround) p.lev = Math.min(100, p.lev + 3);
    p.vy = Math.min(4, p.vy + CM.CV.GRAV * (medium === CVM.WATER ? 0.4 : 1));
    if (medium === CVM.WATER) { p.vx *= 0.9; p.vy *= 0.9; }
    CM.cvMove(p, w);
    if (aim) p.facing = aim[0] >= p.x ? 1 : -1;
    if (medium === CVM.LAVA) this.hurtPlayer(1.6, true); else if (medium === CVM.ACID) this.hurtPlayer(0.8, true); else if (medium === CVM.FIRE) this.hurtPlayer(0.5, true);
    if (p.hurt) p.hurt -= 1;
    for (const wand of p.wands) wand.tick(CM.CV.TICK);
    if (firing && this.wand && aim) {
      const hx = p.x, hy = p.y - p.h * 0.6, ang = Math.atan2(aim[1] - hy, aim[0] - hx), cast = this.wand.cast();
      for (const [name, mods, spread] of cast) this.launch(name, mods, hx + Math.cos(ang) * 4, hy + Math.sin(ang) * 4, ang + (cvUniform(this.rnd, -spread, spread) * Math.PI) / 180, "player", this.dmgScale);
      if (cast.length) this.ev("cast", { name: cast[0][0], n: cast.length });
    }
  }
  hurtPlayer(dmg, quiet = false) {
    const p = this.player; if (this.over) return;
    if (p.hurt && !quiet) return;
    p.hp -= dmg;
    if (!quiet) { p.hurt = 18; this.shake = Math.max(this.shake, 3); this.texts.push([p.x, p.y - p.h - 2, `-${Math.round(dmg)}`, 30, "#FF5A5A"]); this.ev("hurt", { dmg }); }
    if (p.hp <= 0) { p.hp = 0; this.over = "dead"; this.ev("dead"); }
  }
  launch(name, mods, x, y, angle, owner, scale = 1) { const s = new CM.CaveShot(name, mods, x, y, angle, owner, scale); if (s.lightning) { this.lightning(s); return; } this.shots.push(s); }
  targets(owner) { return owner === "player" ? this.enemies.filter((e) => e.awake) : [this.player]; }
  stepShot(s) {
    const w = this.world;
    s.life -= 1;
    if (s.life <= 0) { if (s.fuse || s.boom) this.explode(s.x, s.y, s.boom || 8, s.dmg, s.fire, s.owner); this.drop(this.shots, s); return; }
    if (s.homing) {
      let near = null, best = Infinity; for (const e of this.targets(s.owner)) { const d = (e.x - s.x) ** 2 + (e.y - e.h / 2 - s.y) ** 2; if (d < best) { best = d; near = e; } }
      if (near && Math.abs(near.x - s.x) < 120 && Math.abs(near.y - s.y) < 120) { const sp = Math.hypot(s.vx, s.vy) || 1, ang = Math.atan2(near.y - near.h / 2 - s.y, near.x - s.x); s.vx += (Math.cos(ang) * sp - s.vx) * 0.15; s.vy += (Math.sin(ang) * sp - s.vy) * 0.15; }
    }
    s.vy += s.gravity;
    const steps = Math.max(1, Math.ceil(Math.max(Math.abs(s.vx), Math.abs(s.vy)))); let sx = s.vx / steps, sy = s.vy / steps;
    for (let i = 0; i < steps; i++) {
      const nx = s.x + sx, ny = s.y + sy;
      if (w.solid(nx, ny)) {
        if (s.dig) {
          const gold = w.carve(nx, ny, s.dig, { softOnly: !s.drill, hard: s.name === "Black Hole" }); this.goldFrom(gold, nx, ny);
          if (w.solid(nx, ny)) { s.life -= 4; if (s.life <= 0 || !s.drill) { this.impact(s); return; } }
        } else if (s.bounce > 0) {
          s.bounce -= 1; if (w.solid(nx, s.y)) { s.vx = -s.vx; sx = -sx; } if (w.solid(s.x, ny)) { s.vy = -s.vy; sy = -sy; } continue;
        } else { this.impact(s); return; }
      }
      s.x = nx; s.y = ny;
      if (s.trail && i % 2 === 0 && w.get(Math.floor(s.x), Math.floor(s.y)) === CVM.AIR) w.set(Math.floor(s.x), Math.floor(s.y), CVM.FIRE);
      for (const t of this.targets(s.owner)) {
        if (s.hit.has(t)) continue;
        const [x0, y0, x1, y1] = cvBox(t);
        if (x0 - s.size < s.x && s.x < x1 + s.size && y0 - s.size < s.y && s.y < y1 + s.size) {
          if (s.owner === "player") this.damage(t, s.dmg); else this.hurtPlayer(s.dmg);
          s.hit.add(t);
          if (!s.pierce) { this.impact(s); return; }
        }
      }
    }
    if (!(s.y >= 0 && s.y < CM.CV.H)) this.drop(this.shots, s);
  }
  drop(list, o) { const i = list.indexOf(o); if (i >= 0) list.splice(i, 1); }
  impact(s) {
    this.drop(this.shots, s); const w = this.world;
    if (s.boom) this.explode(s.x, s.y, s.boom, s.dmg, s.fire, s.owner);
    if (s.splash) { w.splash(s.x - s.vx, s.y - s.vy, s.splash === "acid" ? CVM.ACID : CVM.WATER, 3); this.ev("splash"); }
    if (s.freeze) w.freeze(s.x, s.y, 6);
    if (s.fire && !s.boom) w.splash(s.x - s.vx, s.y - s.vy, CVM.FIRE, 2);
    for (let k = 0; k < 5; k++) this.particles.push([s.x, s.y, cvUniform(this.rnd, -1, 1), cvUniform(this.rnd, -1.5, 0.5), 10, s.colour, true]);
  }
  explode(x, y, r, dmg, fire, owner) {
    const w = this.world, gold = w.carve(x, y, Math.floor(r), { fire: Boolean(fire) }); this.goldFrom(gold, x, y);
    this.shake = Math.max(this.shake, Math.min(8, r / 2)); this.ev("boom", { r, x, y });
    for (let k = 0; k < Math.floor(r * 3); k++) { const a = this.rnd.next() * Math.PI * 2, sp = cvUniform(this.rnd, 0.5, 2.5); this.particles.push([x, y, Math.cos(a) * sp, Math.sin(a) * sp - 1, this.rnd.int(10, 25), this.rnd.pick(["#FFE36E", "#FF8A1A", "#FF4A1A", "#9A8A7A"]), true]); }
    const reach = r * 1.4;
    for (const t of this.enemies.filter((e) => e.awake).concat([this.player])) {
      const d = Math.hypot(t.x - x, t.y - t.h / 2 - y); if (d >= reach) continue;
      const hurt = dmg * (1 - (d / reach) * 0.6);
      if (t === this.player) { if (owner !== "player" || d < r * 0.8) this.hurtPlayer(hurt * (owner === "player" ? 0.5 : 1)); }   // (your own blasts hurt you too, up close)
      else if (owner === "player") this.damage(t, hurt);
    }
  }
  lightning(s) {
    let here = [s.x, s.y]; const done = new Set();
    for (let k = 0; k < 4; k++) {
      let near = null, best = Infinity; for (const e of this.enemies) if (e.awake && !done.has(e)) { const d = (e.x - here[0]) ** 2 + (e.y - e.h / 2 - here[1]) ** 2; if (d < best) { best = d; near = e; } }
      if (!near || Math.hypot(near.x - here[0], near.y - near.h / 2 - here[1]) > 110) break;
      this.bolts.push([here, [near.x, near.y - near.h / 2], 6]); this.damage(near, s.dmg); done.add(near); here = [near.x, near.y - near.h / 2];
    }
    if (!done.size) { const a = Math.atan2(s.vy, s.vx); this.bolts.push([here, [here[0] + Math.cos(a) * 40, here[1] + Math.sin(a) * 40], 4]); }   // (nothing to strike: a crackle in the air)
    this.ev("zap");
  }
  goldFrom(cells, x, y) {
    const b = CM.cvBiomeAt(Math.floor(y)), n = Math.floor(cells / 4) + (cells % 4 && this.rnd.next() < 0.5 ? 1 : 0);
    for (let k = 0; k < n; k++) { const g = this.pickup("gold", x + cvUniform(this.rnd, -4, 4), y, 5 * (b + 1)); g.vy = -1.5; this.pickups.push(g); }
  }
  damage(e, dmg) {
    e.hp -= dmg; e.awake = true; this.texts.push([e.x, e.y - e.h - 2, `${Math.round(dmg)}`, 24, "#FFE36E"]);
    if (e.hp <= 0 && this.enemies.includes(e)) {
      this.drop(this.enemies, e); this.player.kills += 1; this.xp += e.boss ? CM.CV_XP.boss[e.index] : CM.CV_XP.per(e.biome);
      const n = Math.max(1, Math.floor(e.gold / 10)); for (let k = 0; k < n; k++) { const g = this.pickup("gold", e.x + cvUniform(this.rnd, -3, 3), e.y - 3, Math.max(1, Math.floor(e.gold / n))); g.vy = -2; this.pickups.push(g); }
      for (let k = 0; k < 14; k++) this.particles.push([e.x, e.y - e.h / 2, cvUniform(this.rnd, -1.5, 1.5), cvUniform(this.rnd, -2, 0.5), this.rnd.int(12, 24), e.colour, true]);
      this.ev("kill", { boss: e.boss, kind: e.kind });
      if (e.boss) this.bossDown(e);
    } else this.ev("hit");
  }
  // ---- the creatures ----
  stepEnemy(e) {
    const p = this.player, w = this.world, dx = p.x - e.x, dy = (p.y - p.h / 2) - (e.y - e.h / 2), dist = Math.hypot(dx, dy), G = CM.CV.GRAV, rnd = this.rnd;
    if (!e.awake) { if (dist < 170) e.awake = true; else return; }
    if (dist > 360 && !e.boss) { e.awake = false; return; }
    e.t += CM.CV.TICK;
    if (e.boss) this.bossAi(e, dx, dy, dist);
    else if (e.move === "hop") { if (e.onGround) { e.vx *= 0.7; if (rnd.next() < 0.04) { e.vy = -2.6; e.vx = dist < 150 ? cvSign(e.speed * 2, dx) : cvUniform(rnd, -1, 1); } } e.vy = Math.min(4, e.vy + G); CM.cvMove(e, w); }
    else if (e.move === "walk") {
      if (dist < 160) e.vx = Math.abs(dx) > 30 || !e.spell ? cvSign(e.speed, dx) : e.vx * 0.8; else e.vx = e.speed * (Math.sin(e.t * 0.7) > 0 ? 1 : -1);
      if (e.onGround && Math.abs(e.vx) > 0.1 && CM.cvBlocked(w, e.x + cvSign(e.w, e.vx), e.y - e.h, e.x + cvSign(e.w, e.vx) + 1, e.y - 3)) e.vy = -2.8;
      e.vy = Math.min(4, e.vy + G); CM.cvMove(e, w);
    } else if (e.move === "fly" || e.move === "ghost") {
      const [tx, ty] = dist < 200 ? [dx, dy - 10] : [Math.sin(e.t) * 20, Math.cos(e.t * 0.7) * 10], n = Math.hypot(tx, ty) || 1, keep = e.spell ? 40 : 0, sign = dist < keep ? -1 : 1;   // (shooters keep their distance)
      e.vx += ((sign * tx) / n * e.speed - e.vx) * 0.08; e.vy += ((sign * ty) / n * e.speed + Math.sin(e.t * 4) * 0.3 - e.vy) * 0.08;
      CM.cvMove(e, w, 0, e.move === "ghost");
    } else if (e.move === "dig") {
      const n = dist || 1; e.vx += (dx / n * e.speed - e.vx) * 0.05; e.vy += (dy / n * e.speed - e.vy) * 0.05; e.x += e.vx; e.y += e.vy;
      if (rnd.next() < 0.5) w.carve(e.x, e.y - e.h / 2, 4, { hard: false });
    }
    if (e.vx) e.facing = e.vx > 0 ? 1 : -1;
    if (e.spell && dist < 170) {
      e.timer -= 1;
      if (e.timer <= 0 && this.sees(e.x, e.y - e.h / 2, p.x, p.y - p.h / 2)) { e.timer = e.cd + rnd.int(0, 30); this.launch(e.spell, [], e.x, e.y - e.h / 2, Math.atan2(dy, dx), "enemy", 0.6 + e.biome * 0.25); this.ev("foecast"); }
    }
    if (cvHits(e, p, 1)) this.hurtPlayer(e.dmg);
    if (e.y > CM.CV.H || e.y < 0) this.drop(this.enemies, e);
  }
  sees(x0, y0, x1, y1) { const n = Math.floor(Math.max(Math.abs(x1 - x0), Math.abs(y1 - y0)) / 3) + 1; for (let i = 1; i < n; i++) if (this.world.solid(x0 + ((x1 - x0) * i) / n, y0 + ((y1 - y0) * i) / n)) return false; return true; }
  // ---- the bosses ----
  bossCheck() {
    const p = this.player;
    for (let b = 0; b < CM.CV_BIOMES.length; b++) {
      if (this.bossStarted.has(b)) continue;
      const [x0, y0, x1, y1] = CM.cvArena(b);
      if (x0 < p.x && p.x < x1 && y0 + 10 < p.y && p.y < y1 && this.world.made > y1) {
        this.bossStarted.add(b); const boss = this.makeBoss(b, (x0 + x1) / 2, b !== 2 ? y0 + 40 : y1 - 2);
        this.enemies.push(boss); this.boss = boss; this.banner = [b < 4 ? `${CM.CV_BOSSES[b]} awakens` : "THE UNMAKER", 150]; this.ev("boss", { b });
      }
    }
  }
  bossDown(e) {
    const b = e.index; this.bossesDown.add(b); this.boss = null; this.shake = 12;
    this.loot.push({ boss: b });                                          // (a thing of the party's own: made when the hero comes out - 61g-cavemouth.js)
    this.ev("bossdown", { b });
    if (b === CM.CV_BOSSES.length - 1) { this.over = "won"; return; }
    this.world.openGate(b); this.banner = [`${CM.CV_BOSSES[b]} has fallen`, 150];
    this.pickups.push(this.pickup("wand", e.x, e.y - 4, CM.randomWand(b + 1, this.rnd))); this.pickups.push(this.pickup("heart", e.x + 10, e.y - 4));
  }
  bossAi(e, dx, dy, dist) {
    const w = this.world, p = this.player, i = e.index, frac = e.hp / e.hpMax, k = this.tickN, [x0, y0, x1, y1] = CM.cvArena(i), rnd = this.rnd, G = CM.CV.GRAV;
    e.phase = frac > 0.66 ? 1 : frac > 0.33 ? 2 : 3;
    if (i === 0) {                                                       // Gravelmaw: a great worm through the rock
      const sp = 1.6 + (3 - e.phase) * -0.3 + 0.4 * e.phase, tx = p.x + Math.sin(e.t * 1.3) * 40, ty = p.y - 6 + Math.cos(e.t * 0.9) * 30, ang = Math.atan2(ty - e.y, tx - e.x);
      e.vx += (Math.cos(ang) * sp - e.vx) * 0.04; e.vy += (Math.sin(ang) * sp - e.vy) * 0.04;
      e.x = cvClamp(e.x + e.vx, x0 + 8, x1 - 8); e.y = cvClamp(e.y + e.vy, y0 + 8, y1);
      e.segments = [[e.x, e.y]].concat(e.segments.slice(0, -1));
      if (k % 3 === 0) w.carve(e.x, e.y - 6, 7, { hard: false });
      for (let j = 3; j < e.segments.length; j += 3) { const [sx, sy] = e.segments[j]; if (Math.abs(sx - p.x) < 7 && Math.abs(sy - 6 - (p.y - p.h / 2)) < 9) this.hurtPlayer(e.dmg * 0.6); }
    } else if (i === 1) {                                                // Rimecaller: rings of ice, and bats
      e.x += ((p.x + Math.sin(e.t * 0.6) * 60) - e.x) * 0.02; e.y += ((y0 + 30 + Math.sin(e.t) * 12) - e.y) * 0.03;
      if (k % Math.max(30, 75 - e.phase * 15) === 0) for (let a = 0; a < 360; a += e.phase < 3 ? 30 : 20) this.launch("Ice Shard", [], e.x, e.y - 8, ((a + k) * Math.PI) / 180, "enemy", 1);
      if (k % 240 === 0) for (let n = 0; n < e.phase; n++) this.enemies.push(Object.assign(this.makeEnemy("bat", e.x, e.y, 1), { awake: true }));
    } else if (i === 2) {                                                // Mother Spore: acid arcs and spores, rooted to the floor
      if (k % Math.max(25, 70 - e.phase * 15) === 0) for (let n = 0; n < 1 + e.phase; n++) this.launch("Acid Ball", [], e.x, e.y - e.h, Math.atan2(dy, dx) + cvUniform(rnd, -0.4, 0.4) - 0.5, "enemy", 1);
      if (k % 200 === 0) for (let n = 0; n < e.phase; n++) this.enemies.push(Object.assign(this.makeEnemy(rnd.pick(["spore", "slime"]), e.x + cvUniform(rnd, -20, 20), e.y - 4, 2), { awake: true }));
    } else if (i === 3) {                                                // the Cinder Colossus: stomps, leaps and fire
      e.vy = Math.min(4, e.vy + G);
      if (e.onGround) { e.vx = cvSign(0.6 + e.phase * 0.2, dx); if (k % Math.max(50, 120 - e.phase * 20) === 0) { e.vy = -4.2; e.vx = cvSign(2.2, dx); e.slam = true; } }
      CM.cvMove(e, w, 4);
      if (e.onGround && e.slam) {
        e.slam = false; this.explode(e.x, e.y, 8, 0, false, "enemy");
        if (Math.abs(p.x - e.x) < 60 && p.onGround) this.hurtPlayer(e.dmg);
        for (const a of [-30, -60, -120, -150]) this.launch("Fireball", [], e.x, e.y - e.h, (a * Math.PI) / 180, "enemy", 0.8);
      }
    } else {                                                             // the Unmaker: spirals, a sweeping beam, and the void
      const cx = (x0 + x1) / 2, cy = y0 + 45;
      if (k % 180 === 0 && e.phase >= 2) {                               // it blinks to a new place
        e.x = cvUniform(rnd, x0 + 40, x1 - 40); e.y = cvUniform(rnd, y0 + 25, y0 + 70); this.ev("blink");
        for (let n = 0; n < 30; n++) this.particles.push([e.x, e.y - 11, cvUniform(rnd, -2, 2), cvUniform(rnd, -2, 2), 20, "#F2EEFF", false]);
      } else { e.x += ((cx + Math.sin(e.t * 0.5) * 120) - e.x) * 0.01; e.y += ((cy + Math.sin(e.t * 0.8) * 20) - e.y) * 0.01; }
      if (k % (e.phase < 3 ? 6 : 4) === 0) { const a = e.t * (2 + e.phase) * 1.3, arms = 2 + e.phase; for (let j = 0; j < arms; j++) this.launch("Spark Bolt", [], e.x, e.y - 11, a + (j * Math.PI * 2) / arms, "enemy", 2); }
      if (e.phase >= 2 && k % 150 < 40) {                                // the beam
        const ang = Math.atan2(dy, dx) + Math.sin(k * 0.08) * 0.6, end = [e.x + Math.cos(ang) * 260, e.y - 11 + Math.sin(ang) * 260];
        this.bolts.push([[e.x, e.y - 11], end, 2]);
        const px = p.x - e.x, py = p.y - p.h / 2 - (e.y - 11), along = px * Math.cos(ang) + py * Math.sin(ang), off = Math.abs(-px * Math.sin(ang) + py * Math.cos(ang));
        if (along > 0 && along < 260 && off < 5) this.hurtPlayer(1.2, true);
      }
      if (e.phase === 3) { p.vx += cvClamp(-dx / 400, -0.15, 0.15); if (k % 120 === 0) this.enemies.push(Object.assign(this.makeEnemy("ghost", e.x, e.y, 4), { awake: true })); }   // (the void pulls at you)
    }
    if (cvHits(e, p, 2)) this.hurtPlayer(e.dmg);
  }
  // ---- the finds ----
  stepPickup(k) {
    const w = this.world, p = this.player; k.t += CM.CV.TICK;
    if (k.kind !== "fountain" && k.kind !== "rope" && !k.price) { k.vy = Math.min(3, k.vy + CM.CV.GRAV); CM.cvMove(k, w, 0); }
    if (k.kind === "gold" && cvHits(k, p, 3)) { p.gold += k.value; this.texts.push([p.x, p.y - p.h - 4, `+${k.value}`, 20, "#F2C230"]); this.drop(this.pickups, k); this.ev("gold", { n: k.value }); }
    else if (k.kind === "heart" && cvHits(k, p, 2)) { p.hpMax += 25; p.hp = p.hpMax; this.banner = ["Max health +25", 80]; this.drop(this.pickups, k); this.ev("heart"); }
    else if (k.kind === "fountain" && Math.abs(k.x - p.x) < 10 && Math.abs(k.y - p.y) < 14 && p.hp < p.hpMax) { p.hp = p.hpMax; for (const wand of p.wands) wand.mana = wand.mana_max; this.banner = ["The fountain restores you", 70]; this.ev("fountain"); }
    if (k.y > CM.CV.H) this.drop(this.pickups, k);
  }
  nearestItem() {
    const p = this.player; let best = null;
    for (const k of this.pickups) if ((k.kind === "wand" || k.kind === "spell" || k.kind === "rope") && Math.abs(k.x - p.x) < 9 && Math.abs(k.y - p.y) < 12 && (!best || Math.abs(k.x - p.x) < Math.abs(best.x - p.x))) best = k;
    return best;
  }
  // E: take (or buy) what is at your feet; at the rope, climb out with what you carry
  interact() {
    const k = this.nearestItem(), p = this.player; if (!k) return "";
    if (k.kind === "rope") { this.over = "out"; this.ev("rope"); return "rope"; }
    if (k.price && p.gold < k.price) { this.banner = [`Not enough gold (${k.price} needed)`, 70]; return ""; }
    const price = k.price;
    if (k.kind === "wand") {
      const got = k.value;
      if (p.wands.length < 4) { p.wands.push(got); this.drop(this.pickups, k); }
      else { const old = p.wands[p.current]; p.wands[p.current] = got; k.value = old; k.price = 0; }   // (a full hand: the wand in it is left lying for this one)
      this.banner = [`Picked up ${got.name}`, 70];
    } else {
      if (p.spells.length >= 16) { this.banner = ["Your spell bag is full (Tab to sort it)", 70]; return ""; }
      p.spells.push(k.value); this.drop(this.pickups, k); this.banner = [`Picked up ${k.value}`, 70];
    }
    if (price) { p.gold -= price; k.price = 0; this.ev("buy"); } else this.ev("take");
    return k.kind;
  }
  depth() { return Math.max(0, Math.floor((this.player.y - CM.CV.SURFACE) / 2)); }
};
