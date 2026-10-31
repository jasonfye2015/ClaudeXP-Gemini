"use strict";
// Claudecraft, measured (the nineteenth update, phase 8): a simple hand goes through the Neather Gate with a given
// calling, level and pick and plays an hour of the island in real time - a fixed step, the island's own clock and
// life - then comes home. It digs a staircase down to the ore's depth and tunnels along, breaking every ore and gem it
// uncovers beside the tunnel; it strikes (or shoots) whatever comes near, drinks a potion when hurt, and opens any old
// chest it passes. The report: gold, experience, ore and the rest an hour brings, beside an hour in the shaft for the
// same party (the balance simulator's own run, at an hour of play to 1800 steps - a step a second and the fights).
//
//   node tools/craftbot.js                               Knight and Mage at levels 5 and 12, copper and iron picks
//   node tools/craftbot.js --classes Rogue --levels 8 --picks steel --hours 2 --seeds 3
const HL = require("./headless"), { fixedParty } = HL, load = (...a) => HL.load(...a);
const { playRun } = require("./bot");

const args = process.argv.slice(2);
const opt = (name, fallback) => { const i = args.indexOf("--" + name); return i >= 0 && args[i + 1] !== undefined ? args[i + 1] : fallback; };
const CLASSES = opt("classes", "Knight,Mage").split(","), LEVELS = opt("levels", "5,12").split(",").map(Number), PICKS = opt("picks", "copper,iron").split(",");
const HOURS = Number(opt("hours", 1)), SEEDS = Number(opt("seeds", 2)), DT = 0.05, STEPS_AN_HOUR = 1800;

function islandHour(seed, cls, level, pick, hours = HOURS) {
  const CM = load(), CC = CM.CC, B = CC.B, g = new CM.Game();
  g.newGame(`isle-${seed}`, fixedParty(CM), "pauper", "fair", [], "dungeon", { town: true }); g.mode = "explore"; g.floor.pos = CM.PORTAL_YARD.gate.slice();
  const h = g.party[0]; h.cls = cls; h.xp = CM.xpForLevel(level); g.checkLevels(); CM.recompute(h); h.hp = h.max; h.mp = h.maxmp;
  g.bag = g.bag.filter((it) => it.kind !== "pick"); g.bag.push(CM.pick(pick)); for (let k = 0; k < 3; k++) g.bag.push({ name: "Healing Potion", kind: "heal", power: 20 + level * 6, value: 20 });
  g.light = { kind: "lantern", left: 9999 };
  const gold0 = g.gold, xp0 = h.xp, bag0 = g.bag.length; if (g.enterCraft(0)) return null;
  const cr = g.craft, W = cr.world, w = cr.walker, L = g.craftLife(), R = new CM.Random(CM.hashSeed(`craftbot:${seed}`));
  const deep = pick === "copper" ? 16 : pick === "iron" ? 11 : 6; let heading = R.int(0, 3) * 90, dug = 0, falls = 0, t = 0, chests = 0, turnAt = 30 + R.int(0, 20);
  const fwd = () => { const a = (heading * Math.PI) / 180; return [Math.round(-Math.sin(a)), Math.round(-Math.cos(a))]; };
  const solid = (x, y, z) => CC.SOLID.has(W.get(x, y, z));
  // a block broken honestly: held for its time (the game's own dig), with whatever tool the rules pick
  const breakBlock = (x, y, z) => { const v = W.get(x, y, z); if (!v || v === B.WATER || CC.UNBREAKABLE.has(v) || v === B.TORCH) return v === B.AIR; if (g.craftBreakTime(v) === Infinity) return false; cr.target = [[x, y, z], null]; cr.dig = null; let held = 0; while (W.get(x, y, z) === v && held < 30) { g.craftDig(DT, true); held += DT; tick(DT); if (!g.craft) return false; } return W.get(x, y, z) !== v; };
  const falls0 = g.tally.craftFalls || 0;
  const tick = (dt) => { t += dt; g.craftTick(dt); if (cr.bundles.length) g.craftFetch(); fight(); if (h.hp < h.max * 0.4) g.craftDrink(); falls = (g.tally.craftFalls || 0) - falls0; };
  const fight = () => {
    const near = L.mobs.filter((o) => o.fellAt === null && !o.wild && Math.hypot(o.w.pos[0] - w.pos[0], o.w.pos[2] - w.pos[2]) < (CM.brArms(h).ranged ? 10 : 2.6) && Math.abs(o.w.pos[1] - w.pos[1]) < 2.5);
    if (!near.length) return; const o = near[0], e = w.eye(), d = [o.w.pos[0] - e[0], o.w.pos[1] + o.h * 0.5 - e[1], o.w.pos[2] - e[2]];
    const yaw0 = w.yaw, pitch0 = w.pitch; w.yaw = (Math.atan2(-d[0], -d[2]) * 180) / Math.PI; w.pitch = (Math.atan2(d[1], Math.hypot(d[0], d[2])) * 180) / Math.PI;
    if (CM.brArms(h).ranged) g.craftAttack(true); else g.craftAttack(false); w.yaw = yaw0; w.pitch = pitch0;
  };
  const walkTo = (x, z) => { for (let k = 0; k < 40; k++) { const dx = x + 0.5 - w.pos[0], dz = z + 0.5 - w.pos[2]; if (Math.hypot(dx, dz) < 0.25) return true; w.yaw = (Math.atan2(-dx, -dz) * 180) / Math.PI; w.update(DT, { fwd: true }); tick(DT); if (!g.craft) return false; } return false; };
  // the ore beside the tunnel: every ore or gem block within a block of the cells walked through
  const takeOre = (x, y, z) => { for (let dx = -1; dx <= 1; dx++) for (let dy = -1; dy <= 2; dy++) for (let dz = -1; dz <= 1; dz++) { const v = W.get(x + dx, y + dy, z + dz); if (CC.ORE_OF[v] || CC.GEM_OF[v] || v === B.CHARSTONE) breakBlock(x + dx, y + dy, z + dz); if (v === B.TREASURE && g.craftOpenTreasure(`${x + dx},${y + dy},${z + dz}`)) chests++; } };
  while (t < hours * 3600 && g.craft) {
    const fx = Math.floor(w.pos[0]), fy = Math.floor(w.pos[1] + 0.01), fz = Math.floor(w.pos[2]), [ax, az] = fwd(), nx = fx + ax, nz = fz + az;
    if (nx < 4 || nz < 4 || nx > CC.SIZE - 5 || nz > CC.SIZE - 5 || W.get(nx, fy, nz) === B.WATER || W.get(nx, fy + 1, nz) === B.WATER || --turnAt <= 0) { heading = (heading + (R.chance(0.5) ? 90 : 270)) % 360; turnAt = 30 + R.int(0, 20); tick(DT); continue; }
    const down = fy > deep;
    let ok = true; for (const y of down ? [fy + 1, fy, fy - 1] : [fy, fy + 1]) if (solid(nx, y, nz) && !breakBlock(nx, y, nz)) ok = false;
    if (!ok) { heading = (heading + 90) % 360; tick(DT); continue; }
    walkTo(nx, nz); for (let k = 0; k < 10; k++) { w.update(DT, {}); tick(DT); }
    dug += 1; takeOre(Math.floor(w.pos[0]), Math.floor(w.pos[1] + 0.01), Math.floor(w.pos[2]));
    if (g.craft && Math.floor(w.pos[1]) > fy + 3) heading = (heading + 180) % 360;   // (woke at the gate or a bed: back the other way)
  }
  const S = cr.satchel, ore = {}; for (const s of S.slots) if (s && CC.ITEM[s.b] && (CC.ITEM[s.b].ore || CC.ITEM[s.b].gem || CC.ITEM[s.b].charcoal)) { const k = CC.ITEM[s.b].ore || CC.ITEM[s.b].gem || "charcoal"; ore[k] = (ore[k] || 0) + s.n; }
  const out = g.leaveCraft(); const home = g.bag.slice(bag0);
  const save = JSON.stringify(g.village.craft).length;
  return { cls, level, pick, save, gold: g.gold - gold0, xp: h.xp - xp0, kills: out ? out.kills : 0, falls, chests, ore, dug, things: home.filter((i) => !["ore", "bar", "charcoal", "gem", "meat", "rune"].includes(i.kind)).length, heroLevel: h.level, oreValue: home.filter((i) => ["ore", "gem", "charcoal", "bar"].includes(i.kind)).reduce((a, i) => a + (i.value || 0), 0) };
}

function shaftHour(seed, level) {
  const CM = load(), g = new CM.Game(); g.newGame(`isle-${seed}`, fixedParty(CM), "pauper", "fair", [], "dungeon", {});
  for (const h of g.party) { h.xp = CM.xpForLevel(level); } g.checkLevels(); for (const h of g.party) { CM.recompute(h); h.hp = h.max; h.mp = h.maxmp; }
  const gold0 = g.gold, xp0 = g.party.reduce((a, h) => a + h.xp, 0); const r = playRun(CM, g, { maxFloor: Math.max(3, Math.round(level * 0.8)) }); void r;
  const steps = Math.max(1, (g.tally.steps || 0) + (g.tally.rounds || g.tally.fights * 6 || 0)), k = STEPS_AN_HOUR / steps;
  return { gold: Math.round((g.gold - gold0) * k), xp: Math.round(((g.party.reduce((a, h) => a + h.xp, 0) - xp0) / 4) * k), steps };
}

if (require.main === module) {
  console.log(`Claudecraft: ${HOURS} hour${HOURS > 1 ? "s" : ""} on the island, ${SEEDS} seed${SEEDS > 1 ? "s" : ""} each, against the shaft at ${STEPS_AN_HOUR} steps an hour (one hero's share)`);
  for (const cls of CLASSES) for (const level of LEVELS) for (const pick of PICKS) {
    const rs = []; for (let s = 1; s <= SEEDS; s++) { const r = islandHour(s, cls, level, pick); if (r) rs.push(r); }
    const sh = []; for (let s = 1; s <= SEEDS; s++) sh.push(shaftHour(s, level));
    const avg = (f, list = rs) => Math.round(list.reduce((a, r) => a + f(r), 0) / Math.max(1, list.length)), ore = {};
    for (const r of rs) for (const [k, v] of Object.entries(r.ore)) ore[k] = (ore[k] || 0) + v / rs.length;
    console.log(`  ${cls} ${level} (${pick} pick): island ${avg((r) => r.gold / HOURS)} gold, ${avg((r) => r.xp / HOURS)} xp, ${avg((r) => r.oreValue / HOURS)} gold of ore and gems, ${avg((r) => r.kills / HOURS)} kills, ${avg((r) => r.chests)} chests, ${avg((r) => r.things)} things, ${avg((r) => r.falls)} falls, ${avg((r) => r.dug)} blocks walked | ore ${Object.entries(ore).map(([k, v]) => `${k} ${v.toFixed(1)}`).join(", ") || "none"}`);
    console.log(`  ${" ".repeat(cls.length + String(level).length + 2)} shaft  ${avg((r) => r.gold, sh)} gold, ${avg((r) => r.xp, sh)} xp a hero (${avg((r) => r.steps, sh)} steps measured)`);
  }
}
module.exports = { islandHour, shaftHour };
