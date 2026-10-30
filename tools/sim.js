"use strict";
// The balance simulator: the autoplaying party (tools/bot.js) goes down the dungeon on many seeds, at every
// difficulty, and the report says where parties die, how far they get, what level they are by each camp, and how
// long it took. Nothing about the fight or the hoard should change without a look at this.
//
//   node tools/sim.js                      30 seeds, Gentle / Fair / Grim, to floor 50
//   node tools/sim.js --seeds 100 --to 30 --difficulty fair --endless --json out.json
//
// The party is the classic four (Knight, Rogue, Cleric, Mage), the Pauper's kit, the seed's own dice: the same seed
// gives the same run every time, so a change in the numbers shows as a change in the report.
const { load, fixedParty } = require("./headless");
const { playRun } = require("./bot");
const fs = require("fs");

const args = process.argv.slice(2);
const opt = (name, fallback) => { const i = args.indexOf("--" + name); return i >= 0 && args[i + 1] !== undefined ? args[i + 1] : fallback; };
const SEEDS = Number(opt("seeds", 30)), TO = Number(opt("to", 50)), ENDLESS = args.includes("--endless");
const DIFFS = opt("difficulty", "gentle,fair,grim").split(",");
const ASCS = opt("ascension", "0").split(",").map(Number);              // the ladder report: --ascension 0,5,10,15 runs each rung
const JSON_OUT = opt("json", null);
const STORY = args.includes("--story");
const TOWN = args.includes("--town");                                     // the run begins at the party's door and walks to the shaft
const LOOT = args.includes("--loot");                                     // the hoard, measured: gold found and spent, things by rarity, floors to the first upgrade, what was used                                   // the story's gates, measured: chapters completed, guardians spoken past, endings

function simulate(seed, difficulty, ascension = 0) {
  const CM = load();
  CM.store.set("ascension", ascension);
  const game = new CM.Game();
  game.newGame(seed, fixedParty(CM), "pauper", difficulty, [], ENDLESS ? "endless" : "dungeon", { ascension, town: TOWN });
  const byCamp = {};
  game.on("mode", (m) => { if (m === "camp") byCamp[game.floor.number] = game.party.map((h) => h.level); });
  const t0 = Date.now();
  const r = playRun(CM, game, { maxFloor: TO });
  const fl = game.floor ? game.floor.number : 0;
  return { seed, difficulty: ascension ? `${difficulty}/A${ascension}` : difficulty, ascension, floor: fl, died: game.mode === "title" && !game.bottom && !(game.crowned && fl === 20 && game.mode === "title"), crowned: Boolean(game.crowned), bottom: Boolean(game.bottom),
    reached: game.mode === "explore", fights: game.tally.fights, fled: game.tally.fled, steps: game.tally.steps, gold: game.gold, guardians: (game.tally.guardians || []).slice(),
    levels: game.party.map((h) => h.level), byCamp, stuck: r.stuck, notes: r.log, ms: Date.now() - t0, spent: game.tally.spent || {}, abilities: game.tally.abilities || {}, logLines: (game.runLog || []).length,
    loot: { goldFound: game.tally.goldFound || 0, found: game.tally.found || {}, used: game.tally.used || {}, firstUpgrade: game.tally.firstUpgrade || {} },
    story: { read: Object.keys((game.story || {}).read || {}).length, chapters: CM.codex(game).filter((c) => c.band !== undefined && c.complete).map((c) => c.id), spoken: (game.tally.spoken || []).slice(), reminded: Boolean(game.reminded), bell: Boolean((game.story || {}).bell) } };
}

function CM_ABILITIES() { return load().ABILITIES; }
const seeds = [];
for (let i = 0; i < SEEDS; i++) seeds.push(`sim-${i + 1}`);
const results = [];
const started = Date.now();
for (const d of DIFFS) for (const a of ASCS) for (const s of seeds) {
  const r = simulate(s, d, a);
  results.push(r);
  process.stderr.write(`${(a ? `${d}/A${a}` : d).padEnd(10)} ${s.padEnd(8)} floor ${String(r.floor).padStart(3)} ${r.bottom ? "BOTTOM" : r.crowned ? "crowned" : r.died ? "fell" : "reached"} levels ${r.levels.join("/")} ${r.fights} fights ${r.ms} ms${r.stuck ? ` (stuck ${r.stuck})` : ""}\n`);
}

// ---- the report ----
const bands = [[1, 5], [6, 10], [11, 15], [16, 20], [21, 25], [26, 30], [31, 35], [36, 40], [41, 45], [46, 50], [51, 999]];
console.log(`\nClaude and Magic - balance: ${SEEDS} seeds a difficulty, to floor ${TO}${ENDLESS ? ", Endless" : ""}, ${Math.round((Date.now() - started) / 1000)} s\n`);
for (const d of [...new Set(results.map((r) => r.difficulty))]) {
  const rs = results.filter((r) => r.difficulty === d);
  const fell = rs.filter((r) => r.died), deep = rs.map((r) => r.floor).sort((a, b) => a - b);
  const median = deep[Math.floor(deep.length / 2)];
  console.log(`${d.toUpperCase()}: median floor ${median}, ${fell.length}/${rs.length} fell, ${rs.filter((r) => r.crowned).length} crowned, ${rs.filter((r) => r.bottom).length} to the bottom, ${rs.filter((r) => r.reached).length} reached floor ${TO}`);
  const hist = bands.map(([a, b]) => `${String(a).padStart(2)}-${String(Math.min(b, 999)).padEnd(3)} ${"#".repeat(fell.filter((r) => r.floor >= a && r.floor <= b).length)}`).filter((l) => l.trim().endsWith("#"));
  console.log("  where parties fell:\n" + (hist.length ? hist.map((l) => "    " + l).join("\n") : "    nowhere"));
  const camps = {};
  for (const r of rs) for (const [fl, lv] of Object.entries(r.byCamp)) (camps[fl] = camps[fl] || []).push(lv.reduce((a, b) => a + b, 0) / lv.length);
  console.log("  party level at the camp below floor: " + Object.entries(camps).sort((a, b) => a[0] - b[0]).map(([fl, ls]) => `${fl}: ${(ls.reduce((a, b) => a + b, 0) / ls.length).toFixed(1)} (${ls.length} got there)`).join(", "));
  const g = {};
  for (const r of rs) for (const id of r.guardians) g[id] = (g[id] || 0) + 1;
  console.log("  guardians slain: " + (Object.entries(g).map(([id, n]) => `${id} ${n}`).join(", ") || "none"));
  const spent = {}, used = {};
  for (const r of rs) { for (const [k, v] of Object.entries(r.spent)) spent[k] = (spent[k] || 0) + v; for (const [k, v] of Object.entries(r.abilities)) used[k] = (used[k] || 0) + v; }
  const total = Object.values(spent).reduce((a, b) => a + b, 0) || 1;
  console.log("  where the gold went: " + Object.entries(spent).sort((a, b) => b[1] - a[1]).map(([k, v]) => `${k} ${Math.round(100 * v / total)}%`).join(", "));
  const never = Object.keys(CM_ABILITIES()).filter((id) => !used[id]);
  console.log("  spells and skills never used by the bot: " + (never.join(", ") || "none") + "; most used: " + Object.entries(used).sort((a, b) => b[1] - a[1]).slice(0, 5).map(([k, v]) => `${k} ${v}`).join(", "));
  if (LOOT) {
    const found = {}, used = {}, first = {}; let goldFound = 0, goldSpent = 0;
    for (const r of rs) { goldFound += r.loot.goldFound; goldSpent += Object.values(r.spent).reduce((a, b) => a + b, 0); for (const [k, v] of Object.entries(r.loot.found)) found[k] = (found[k] || 0) + v; for (const [k, v] of Object.entries(r.loot.used)) used[k] = (used[k] || 0) + v; for (const [k, v] of Object.entries(r.loot.firstUpgrade)) (first[k] = first[k] || []).push(v); }
    const n = rs.length || 1;
    console.log(`  the hoard: ${Math.round(goldFound / n)} gold found a run, ${Math.round(goldSpent / n)} spent; things found a run: ${Object.entries(found).map(([k, v]) => `${k} ${(v / n).toFixed(1)}`).join(", ") || "none"}`);
    console.log(`  used a run: ${Object.entries(used).sort((a, b) => b[1] - a[1]).map(([k, v]) => `${k} ${(v / n).toFixed(1)}`).join(", ") || "nothing"}; floors to the first upgrade: ${Object.entries(first).map(([k, v]) => `${k} ${(v.reduce((a, b) => a + b, 0) / v.length).toFixed(1)} (${v.length})`).join(", ") || "none"}`);
  }
  if (STORY) {
    const chapters = {}, spoken = {};
    for (const r of rs) { for (const c of r.story.chapters) chapters[c] = (chapters[c] || 0) + 1; for (const id of r.story.spoken) spoken[id] = (spoken[id] || 0) + 1; }
    console.log(`  the story: ${(rs.reduce((a, r) => a + r.story.read, 0) / rs.length).toFixed(1)} lines read a run; chapters completed: ${Object.entries(chapters).map(([k, v]) => `${k} ${v}`).join(", ") || "none"}; guardians spoken past: ${Object.entries(spoken).map(([k, v]) => `${k} ${v}`).join(", ") || "none"}; the bell rung ${rs.filter((r) => r.story.bell).length}, the king reminded ${rs.filter((r) => r.story.reminded).length}`);
  }
  const stuck = rs.filter((r) => r.stuck);
  if (stuck.length) console.log(`  the bot got stuck ${stuck.reduce((a, r) => a + r.stuck, 0)} times (${stuck.slice(0, 3).map((r) => r.seed + ": " + r.notes[0]).join("; ")})`);
}
if (JSON_OUT) { fs.writeFileSync(JSON_OUT, JSON.stringify({ seeds: SEEDS, to: TO, endless: ENDLESS, results }, null, 1)); console.log(`\nwritten to ${JSON_OUT}`); }
