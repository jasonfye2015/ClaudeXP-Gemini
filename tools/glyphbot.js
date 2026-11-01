// The Glyph Deep's own player (UPGRADE_PLAN_15.md phase 1): a plain, sensible hand - drink when low, fight what's next
// to it, pick up what it stands on, take a thing within a few steps, else make for the stairs - to measure how the
// levels play for heroes of different levels.
//   node tools/glyphbot.js [trials]     -> the table: for each level and hero level, how often the stairs are reached,
//                                          the turns it took and the health left
const { load, fixedParty } = require("./headless.js");
const CM = load(), GD = CM.GLYPH;
function play(CM, level, heroLevel, seed, opts = {}) {
  const g = new CM.Game(); g.newGame(`gbot:${seed}`, fixedParty(CM), "pauper", "fair", [], "dungeon", { town: true }); const h = g.party[0];
  h.level = heroLevel; h.xp = CM.xpForLevel(heroLevel); CM.recompute(h); h.hp = h.max; if (opts.weapon) { h.weapon = CM.makeItem(GD.depthOf(level) + 2, new CM.Random(seed), "weapon"); CM.recompute(h); h.hp = h.max; }
  g.glyphStore().runs = seed; const r = new CM.GlyphRun(g, 0, level); for (let k = 0; k < (opts.potions || 0); k++) r.pack.push({ name: "Healing Potion", kind: "heal", power: 20 + level * 4, value: 20 });
  for (let t = 0; t < 2500 && !r.over; t++) {
    const pot = r.pack.findIndex((it) => it.kind === "heal"); if (r.hp < r.max * 0.5 && pot >= 0) { r.act("quaff", pot); continue; }
    const adj = r.mons.find((m) => m.hp > 0 && !m.hidden && Math.max(Math.abs(m.x - r.x), Math.abs(m.y - r.y)) === 1 && r.canStep(r.x, r.y, m.x - r.x, m.y - r.y)); if (adj) { r.act("move", [adj.x - r.x, adj.y - r.y]); continue; }
    if (r.thingAt(r.x, r.y)) { r.act("pick"); continue; }
    if (r.atDown() && (r.L < GD.levels || r.bossDown())) return { ok: true, turns: r.turn, hp: r.hp / r.max, kills: r.kills };
    // a step toward: a thing within 6, the boss on the last level, else the stairs
    const d = r.distances(r.x, r.y); let goal = null;
    for (const [k, list] of r.things) if (list.length && d.get(k) !== undefined && d.get(k) <= 6 && (!goal || d.get(k) < goal[1])) goal = [k, d.get(k)];
    if (!goal && r.L === GD.levels && !r.bossDown()) { const b = r.mons.find((m) => m.boss); goal = [`${b.x},${b.y}`, 0]; }
    const target = goal ? goal[0].split(",").map(Number) : r.down, back = r.distances(target[0], target[1]); let best = null;
    for (const [dx, dy] of [[0, -1], [1, 0], [0, 1], [-1, 0], [1, -1], [1, 1], [-1, 1], [-1, -1]]) { if (!r.canStep(r.x, r.y, dx, dy)) continue; const v = back.get(`${r.x + dx},${r.y + dy}`); if (v !== undefined && (!best || v < best[2])) best = [dx, dy, v]; }
    if (!best) { r.act("wait"); continue; } r.act("move", [best[0], best[1]]);
  }
  return { ok: false, turns: r.turn, hp: 0, kills: r.kills, dead: r.over === "dead" };
}
module.exports = { play };
if (require.main === module) {
  const N = Number(process.argv[2]) || 12, rows = [];
  for (const L of [1, 3, 5, 8, 10, 12, 15, 18, 20]) for (const dh of [-2, 0, 3, 6]) { const hl = Math.max(1, L + dh); let ok = 0, turns = 0, hp = 0; const pots = L >= 15 ? 4 : 2;
    for (let s = 0; s < N; s++) { const r = play(CM, L, hl, s, { potions: pots, weapon: true }); if (r.ok) { ok++; turns += r.turns; hp += r.hp; } }
    rows.push(`level ${String(L).padStart(2)}  hero ${String(hl).padStart(2)}  stairs ${String(Math.round((100 * ok) / N)).padStart(3)}%  turns ${ok ? Math.round(turns / ok) : "-"}  health left ${ok ? Math.round((100 * hp) / ok) : "-"}%  (${pots} potions)`); }
  console.log(rows.join("\n"));
}
