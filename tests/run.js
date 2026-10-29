"use strict";
// The rules, tested in Node with no browser (tools/headless.js): the build is current, every floor of many seeds can
// be finished, a floor survives being saved as what changed and made again, a run survives save and load, a save
// from v1.0 (whole floors) still loads, a full browser is noticed, and the dice are the seed's.
//
//   node tests/run.js            (npm test runs this and then tests/smoke.js, which needs a browser)
const assert = require("assert");
const { execFileSync } = require("child_process");
const fs = require("fs");
const path = require("path");
const { load, autoplayFight, fixedParty } = require("../tools/headless");
const { playRun } = require("../tools/bot");

const ROOT = path.join(__dirname, "..");
const tests = [];
const test = (name, fn) => tests.push({ name, fn });
// (things from the game's own realm have their own Object and Array: compare them as plain JSON, without the animations)
const strip = (fl) => JSON.parse(JSON.stringify(fl, (k, v) => (k === "anim" ? undefined : k === "seen" && Array.isArray(v) ? v.slice().sort((a, b) => a[1] - b[1] || a[0] - b[0]) : v)));
const same = (a, b, msg) => assert.deepStrictEqual(strip(a), strip(b), msg);

test("the built file is current (python build.py --check)", () => {
  const out = execFileSync("python3", [path.join(ROOT, "build.py"), "--check"], { encoding: "utf8" });
  assert.match(out, /up to date/);
});

test("every floor of twelve seeds can be finished, and the first hundred of three Endless ones", () => {
  const CM = load();
  for (let s = 0; s < 12; s++) for (let n = 1; n <= 50; n++) {
    const fl = CM.makeFloor(n, `test-${s}`);
    assert.ok(CM.solvable(fl), `floor ${n} of test-${s} can't be finished`);
  }
  for (let s = 0; s < 3; s++) for (let n = 51; n <= 100; n++) assert.ok(CM.solvable(CM.makeFloor(n, `endless-${s}`)), `floor ${n} of endless-${s}`);
});

test("the same seed makes the same floor", () => {
  const CM = load();
  assert.strictEqual(JSON.stringify(CM.makeFloor(7, "same")), JSON.stringify(CM.makeFloor(7, "same")));
  assert.notStrictEqual(JSON.stringify(CM.makeFloor(7, "same")), JSON.stringify(CM.makeFloor(7, "other")));
});

test("a seen-list packs to a bitset and back", () => {
  const CM = load();
  const seen = [[0, 0], [3, 4], [26, 26], [10, 2]];
  same(CM.unpackSeen(CM.packSeen(seen, 27), 27).sort(), seen.slice().sort());
  same(CM.unpackSeen(CM.packSeen([], 17), 17), []);
});

test("a floor is saved as what changed, and comes back the same", () => {
  const CM = load();
  const fl = CM.makeFloor(6, "delta"), base = CM.snapshot(fl);
  // what a party does to a floor: doors, a secret found, a chest taken, a key, a group moved and hurt, seen squares, a flag
  for (const f of Object.values(fl.features)) if (f.type === "door") f.open = true;
  for (const [k, f] of Object.entries(fl.features)) if (f.type === "secret") { f.found = true; const [x, y] = k.split(",").map(Number); fl.grid[y][x] = 0; }
  const chest = Object.keys(fl.things).find((k) => fl.things[k].type === "chest"); delete fl.things[chest];
  const mk = Object.keys(fl.things).find((k) => fl.things[k].type === "monsters"); const group = fl.things[mk]; delete fl.things[mk];
  group.group[0].hp = 1; group.anim = { from: [1, 1], at: 12345 }; fl.things["3,3"] = group;
  fl.things["5,5"] = { type: "rope", up: [2, 2] };
  fl.seen = [[1, 1], [2, 1], [3, 3]]; fl.pos = [3, 1]; fl.facing = 1; fl.avenged = ["9,9"];
  const d = CM.floorDelta(fl, base);
  assert.ok(JSON.stringify(d).length < JSON.stringify(fl).length / 3, "the delta should be much smaller than the floor");
  const back = CM.restoreFloor(d, "delta");
  assert.strictEqual(back.drifted, false);
  same(back.floor, fl);
  // a fresh floor's delta is next to nothing
  const fresh = CM.makeFloor(6, "delta");
  const d0 = CM.floorDelta(fresh, CM.snapshot(fresh));
  same(d0.things, {}); same(d0.features, {}); same(d0.grid, []);
});

test("a run saves as it goes and loads again as it was (the bot plays four floors)", () => {
  const CM = load();
  const game = new CM.Game();
  game.newGame("roundtrip-1");
  playRun(CM, game, { maxFloor: 4 });
  assert.strictEqual(game.mode, "explore", "the bot should still be exploring (floor " + game.floor.number + ")");
  assert.ok(Object.keys(game.floors).length >= 4);
  game.saveRun();
  const raw = CM.storage.getItem("claudemagic.run");
  assert.ok(raw.length < 60000, `the save should be small, not ${raw.length} characters`);
  const data = JSON.parse(raw);
  assert.strictEqual(data.schema, CM.SCHEMA); assert.strictEqual(typeof data.floor, "number");
  const CM2 = load({ storage: CM.storage }), game2 = new CM2.Game();
  assert.ok(game2.canContinue());
  assert.ok(game2.continueRun());
  assert.strictEqual(game2.floor.number, game.floor.number);
  same(game2.floor.pos, game.floor.pos);
  assert.strictEqual(game2.rnd.s, game.rnd.s);
  for (const n of Object.keys(game.floors)) same(game2.floorAt(Number(n)), game.floors[n], `floor ${n} should come back as it was`);
  same(game2.party, game.party);
  assert.strictEqual(game2.gold, game.gold);
  // and plays on
  const before = game2.tally.steps;
  playRun(CM2, game2, { maxFloor: 5 });
  assert.ok(game2.tally.steps > before);
});

test("a save from v1.0 (whole floors) still loads, with the floors as they were left", () => {
  const CM = load();
  const raw = fs.readFileSync(path.join(__dirname, "fixtures", "run-v1.0.json"), "utf8");
  const old = JSON.parse(raw);
  assert.strictEqual(old.schema, undefined); assert.strictEqual(typeof old.floor, "object");
  CM.storage.setItem("claudemagic.run", raw);
  const game = new CM.Game();
  assert.ok(game.canContinue());
  assert.strictEqual(game.lastRun.schema, CM.SCHEMA);
  assert.ok(game.continueRun());
  assert.strictEqual(game.floor.number, old.floor.number);
  same(game.floor.pos, old.floor.pos);
  for (const fl of Object.values(old.floors)) {
    const now = game.floorAt(fl.number);
    assert.ok(now, `floor ${fl.number} should be there`);
    same(now.grid, fl.grid);
    same(Object.keys(now.things).sort(), Object.keys(fl.things).sort());
    for (const [k, f] of Object.entries(fl.features)) same(now.features[k], f, `feature ${k} on floor ${fl.number}`);
    same(now.seen.slice().sort(), fl.seen.slice().sort());
  }
  game.saveRun();
  assert.ok(CM.storage.getItem("claudemagic.run").length < raw.length / 2, "saved again, it should be much smaller");
  assert.ok(!game.messages.some((m) => m.includes("shifted")), "nothing should have drifted");
});

test("an export from v1.0 imports, and the run in it can be continued", () => {
  const CM = load();
  const game = new CM.Game();
  assert.strictEqual(game.importText(fs.readFileSync(path.join(__dirname, "fixtures", "export-v1.0.json"), "utf8")), "");
  assert.ok(game.canContinue());
  assert.ok(game.continueRun());
  assert.strictEqual(game.floor.number, 3);
  const again = JSON.parse(game.exportText());
  assert.strictEqual(again.runs[0].schema, CM.SCHEMA);
  const CM2 = load(), g2 = new CM2.Game();
  assert.strictEqual(g2.importText(JSON.stringify(again)), "");
  assert.ok(g2.continueRun());
});

test("a full browser is noticed: the game says so once and goes on", () => {
  const CM = load({ quota: 1500 });
  const game = new CM.Game();
  let failed = 0;
  game.on("saveFailed", () => failed++);
  game.newGame("full-1");
  for (let i = 0; i < 30; i++) { if (game.mode !== "explore") break; if (!game.move(0)) game.turn(1); game.saveRun(); }
  assert.strictEqual(failed, 1);
  assert.ok(game.messages.some((m) => m.includes("would not keep the save")));
  assert.strictEqual(game.mode === "explore" || game.mode === "combat", true);
});

test("the dice are the seed's: the same fight, fought the same way, goes the same way", () => {
  const play = () => {
    const CM = load(), game = new CM.Game();
    game.newGame("dice-1", fixedParty(CM));
    const mk = Object.keys(game.floor.things).find((k) => game.floor.things[k].type === "monsters");
    game.startCombat(mk, game.floor.things[mk]);
    autoplayFight(CM, game);
    return game.messages.join("\n");
  };
  assert.strictEqual(play(), play());
});

test("a run's dice carry over a save: play on from a save, and from the game that made it, the same way", () => {
  const CM = load(), game = new CM.Game();
  game.newGame("dice-2");
  playRun(CM, game, { maxFloor: 2 });
  game.saveRun();
  const CM2 = load({ storage: CM.storage }), game2 = new CM2.Game();
  game2.continueRun();
  playRun(CM, game, { maxFloor: 3 });
  playRun(CM2, game2, { maxFloor: 3 });
  assert.strictEqual(game.messages.slice(-5).join("\n"), game2.messages.slice(-5).join("\n"));
  same(game2.floor.pos, game.floor.pos);
});

test("storage used is counted", () => {
  const CM = load();
  const game = new CM.Game();
  game.newGame("used-1");
  game.saveRun();
  assert.ok(CM.store.used() > 1000);
});

test("travel: the party walks by itself to a known square, and stops for what it finds", () => {
  const CM = load(), game = new CM.Game();
  game.newGame("travel-1", fixedParty(CM));
  const fl = game.floor;
  fl.seen = []; for (let y = 0; y < fl.grid.length; y++) for (let x = 0; x < fl.grid.length; x++) fl.seen.push([x, y]);   // (a Scroll of Mapping's worth)
  const chest = Object.keys(fl.things).find((k) => fl.things[k].type === "chest").split(",").map(Number);
  assert.ok(game.pathTo(chest[0], chest[1]), "there should be a known way to the chest");
  assert.ok(game.travelTo(chest[0], chest[1]));
  let guard = 0;
  while (game.travel && guard++ < 400) { if (game.mode === "combat") autoplayFight(CM, game); game.travelStep(); }
  assert.ok(guard < 400, "the walk should end");
  assert.ok(game.mode !== "explore" || fl.pos.join(",") === chest.join(",") || game.messages.some((m) => /You stop|close/.test(m)), "it arrives, or stops for a reason: " + game.messages.slice(-2).join(" | "));
  assert.strictEqual(game.travelTo(fl.pos[0], fl.pos[1]), false);
  game.stopTravel();
  assert.strictEqual(game.travel, null);
});

test("explore: the nearest unknown square, and the automap grows", () => {
  const CM = load(), game = new CM.Game();
  game.newGame("explore-1", fixedParty(CM));
  const fl = game.floor, before = fl.seen.length;
  assert.ok(game.frontier(), "a fresh floor has somewhere to explore");
  assert.ok(game.explore());
  let guard = 0;
  while (game.travel && guard++ < 300) { if (game.mode === "combat") autoplayFight(CM, game); game.travelStep(); }
  assert.ok(game.floor.seen.length > before, "more of the floor should be known");
});

test("notes on the automap are kept with the floor", () => {
  const CM = load(), game = new CM.Game();
  game.newGame("notes-1");
  game.setNote(3, 4, "  the key?  ");
  assert.strictEqual(game.floor.notes["3,4"], "the key?");
  game.saveRun();
  const CM2 = load({ storage: CM.storage }), g2 = new CM2.Game();
  g2.continueRun();
  assert.strictEqual(g2.floor.notes["3,4"], "the key?");
  g2.setNote(3, 4, "");
  assert.strictEqual(g2.floor.notes, undefined);
});

test("auto: the party fights a whole fight by itself, and stops when someone is badly hurt", () => {
  const CM = load(), game = new CM.Game();
  game.newGame("auto-1", fixedParty(CM));
  const mk = Object.keys(game.floor.things).find((k) => game.floor.things[k].type === "monsters");
  game.startCombat(mk, game.floor.things[mk]);
  assert.ok(game.autoFight(true));
  let turns = 0;
  while (game.mode === "combat" && game.combat.auto && turns++ < 200) { if (!game.combat.waiting) game.advance(); else game.autoTurn(); }
  assert.ok(game.mode !== "combat" || !game.combat.auto, "auto ends with the fight, or stops itself");
  if (game.mode === "combat") assert.ok(game.alive().some((p) => p.hp < p.max * 0.5), "it stopped because someone is hurt");
});

test("the odds: a blow's chance and range, a spell's number", () => {
  const CM = load(), game = new CM.Game();
  game.newGame("odds-1", fixedParty(CM));
  const foe = CM.makeMonster(CM.MONSTERS[0], 1, new CM.Random(1));
  const est = game.strikeEstimate(game.party[0], foe);
  assert.ok(est.hit > 0.2 && est.hit <= 1 && est.low >= 1 && est.high >= est.low);
  const mage = game.party.find((h) => h.cls === "Mage"), cleric = game.party.find((h) => h.cls === "Cleric");
  assert.match(game.spellEstimate(mage, "missile"), /^\d+$/);
  assert.match(game.spellEstimate(cleric, "heal"), /^mends \d+$/);
  assert.strictEqual(game.spellEstimate(mage, "light"), "");
});

test("waystones: the camps reached, and the old road between them", () => {
  const CM = load(), game = new CM.Game();
  game.newGame("ways-1", fixedParty(CM));
  assert.strictEqual(game.waystone(5), "The waystones are at the camps.");
  for (const n of [5, 10]) { game.enterFloor(n, "down"); game.setMode("camp"); game.reachCamp(n); }   // (as the ladder does, once the guardian over it has fallen)
  same(game.camps, [5, 10]);
  assert.strictEqual(game.floor.number, 10);
  assert.strictEqual(game.waystone(7), "No camp there that you have reached.");
  assert.strictEqual(game.waystone(5), "");
  assert.strictEqual(game.floor.number, 5); assert.strictEqual(game.mode, "camp");
  game.saveRun();
  const CM2 = load({ storage: CM.storage }), g2 = new CM2.Game();
  g2.continueRun();
  same(g2.camps, [5, 10]); assert.strictEqual(g2.mode, "camp"); assert.strictEqual(g2.floor.number, 5);
});

test("the pack: what a thing would change for a hero, and the pack in order", () => {
  const CM = load(), game = new CM.Game();
  game.newGame("pack-1", fixedParty(CM));
  const knight = game.party.find((h) => h.cls === "Knight"), mage = game.party.find((h) => h.cls === "Mage");
  const sword = { kind: "weapon", slot: "weapon", name: "Long Sword", power: knight.weapon.power + 2, value: 60, props: {} };
  const c = game.compare(knight, sword);
  assert.strictEqual(c.text, "+2"); assert.strictEqual(c.cls, "good");
  const plate = { kind: "armor", slot: "armor", name: "Plate Mail", power: 9, value: 300, props: { weight: "heavy" } };
  assert.strictEqual(game.compare(mage, plate).text, "can't");
  assert.strictEqual(game.compare(knight, { kind: "heal", name: "Healing Potion", power: 20 }), null);
  game.bag.push(sword, plate);
  game.sortBag();
  assert.strictEqual(game.bag[0].kind, "weapon");
  assert.ok(game.bag.findIndex((i) => i.kind === "torch") > game.bag.findIndex((i) => i.kind === "armor"));
});

let failed = 0;
for (const t of tests) {
  const t0 = Date.now();
  try { t.fn(); console.log(`  ok   ${t.name} (${Date.now() - t0} ms)`); }
  catch (e) { failed++; console.log(`  FAIL ${t.name}\n       ${(e.stack || e.message).split("\n").slice(0, 4).join("\n       ")}`); }
}
console.log(failed ? `\n${failed} of ${tests.length} failed` : `\nall ${tests.length} passed`);
process.exit(failed ? 1 : 0);
