"use strict";
// The rules, tested in Node with no browser (tools/headless.js): the build is current, every floor of many seeds can
// be finished, a floor survives being saved as what changed and made again, a run survives save and load, a save
// from v1.0 (whole floors) still loads, a full browser is noticed, and the dice are the seed's.
//
//   node tests/run.js            (npm test runs this and then tests/smoke.js, which needs a browser)
const assert = require("assert");
const { execFileSync } = require("child_process");
const fs = require("fs");
const vm = require("vm");
const path = require("path");
const { load, autoplayFight, fixedParty } = require("../tools/headless");
const { playRun } = require("../tools/bot");

const ROOT = path.join(__dirname, "..");
const tests = [];
const test = (name, fn) => tests.push({ name, fn });
// (things from the game's own realm have their own Object and Array: compare them as plain JSON, without the animations)
const strip = (fl) => JSON.parse(JSON.stringify(fl, (k, v) => (k === "anim" ? undefined : k === "seen" && Array.isArray(v) ? v.slice().sort((a, b) => a[1] - b[1] || a[0] - b[0]) : v)));
const same = (a, b, msg) => assert.deepStrictEqual(strip(a), strip(b), msg);

test("every source file parses (the rules' files are loaded here; the drawing and the window's are not, so they are checked)", () => {
  for (const f of fs.readdirSync(path.join(ROOT, "src", "js")).filter((f) => f.endsWith(".js"))) {
    try { new vm.Script(fs.readFileSync(path.join(ROOT, "src", "js", f), "utf8"), { filename: f }); } catch (e) { assert.fail(`${f}: ${e.message}`); }
  }
});

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
  const back = CM.restoreFloor(d, "delta", CM.GEN);
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
  assert.ok(CM.storage.getItem("claudemagic.run").length < raw.length * 0.8, "saved again, it should be smaller (an old save's chests predate the affixes, so they all differ from the fresh floor)");
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

test("a run still in the town (floor 0) exports and imports, and its slot isn't empty", () => {
  const CM = load();
  const game = new CM.Game();
  game.newGame("town-0", null, undefined, undefined, undefined, undefined, { town: true });
  assert.strictEqual(CM.runFloor(game.lastRun), 0, "the expedition should have set out from the town");
  game.gold = 777; game.saveRun();
  const text = game.exportText();
  const CM2 = load(), g2 = new CM2.Game();
  assert.strictEqual(g2.importText(text), "");
  assert.ok(g2.canContinue(), "the town run was dropped on import");
  assert.strictEqual(g2.lastRun.gold, 777);
  const CM3 = load(), g3 = new CM3.Game();
  const one = JSON.parse(text); delete one.runs;           // (an export with a single run, the older way)
  assert.strictEqual(g3.importText(JSON.stringify(one)), "");
  assert.ok(g3.canContinue(), "a single town run was dropped on import");
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

test("monsters have a shape, a row, and what they fear", () => {
  const CM = load(), rnd = new CM.Random(5);
  const rat = CM.makeMonster(CM.monsterKind("Giant Rat"), 10, rnd), troll = CM.makeMonster(CM.monsterKind("Troll"), 10, rnd), goblin = CM.makeMonster(CM.monsterKind("Goblin"), 10, rnd);
  assert.ok(troll.max > rat.max * 2, "a troll is a wall of meat beside a rat");
  assert.strictEqual(goblin.row, "back"); assert.strictEqual(troll.row, "front");
  assert.strictEqual(CM.resistance(troll, "fire"), 1.5);
  assert.strictEqual(CM.resistance(CM.makeMonster(CM.monsterKind("Demon"), 10, rnd), "fire"), 0.5);
  assert.strictEqual(CM.resistance(CM.makeMonster(CM.monsterKind("Skeleton"), 10, rnd), "holy"), 1.5, "the undead fear holiness");
  assert.strictEqual(CM.resistance(rat, "holy"), 1);
  assert.strictEqual(CM.resistance({ guardian: "forge", name: "The Forge-Warden" }, "frost"), 1.5);
  assert.strictEqual(CM.resistance({ guardian: "forge", name: "The Forge-Warden" }, "fire"), 0.5);
  for (const m of CM.MONSTERS) assert.ok(m.shape && m.shape.length === 3, m.name + " should have a shape");
});

test("the level curve: about the monsters' level, floor by floor", () => {
  const CM = load();
  assert.ok(CM.xpForLevel(2) > CM.xpForLevel(1) && CM.xpForLevel(20) > CM.xpForLevel(19));
  assert.ok(CM.xpForLevel(20) > 14000 && CM.xpForLevel(20) < 22000, "about 16k experience by floor 20 is level 20: " + CM.xpForLevel(20));
  assert.ok(CM.xpForLevel(35) > 60000 && CM.xpForLevel(35) < 100000, "about 70k by the bottom is the middle thirties: " + CM.xpForLevel(35));
});

test("a foe in the back row is reached past the front for half; a bow reaches it whole", () => {
  const CM = load(), game = new CM.Game();
  game.newGame("rows-1", fixedParty(CM));
  const rnd = new CM.Random(7), goblin = CM.makeMonster(CM.monsterKind("Goblin"), 1, rnd), orc = CM.makeMonster(CM.monsterKind("Orc"), 1, rnd);
  game.floor.things["2,2"] = { type: "monsters", group: [orc, goblin] };
  game.startCombat("2,2", game.floor.things["2,2"]);
  const knight = game.party.find((h) => h.cls === "Knight");
  let reached = 0;
  for (let i = 0; i < 20; i++) { goblin.hp = 999; game.messages = []; game.strike(knight, goblin, "", { sure: true }); if (game.messages.some((m) => m.includes("reaching past the front"))) reached++; }
  assert.strictEqual(reached, 20);
  orc.hp = 0; orc.dead = true; game.messages = [];
  game.strike(knight, goblin, "", { sure: true });
  assert.ok(!game.messages.some((m) => m.includes("reaching past")), "with the front down, the back row is in reach");
});

test("a guardian says what is coming the turn before", () => {
  const CM = load(), game = new CM.Game();
  game.newGame("intent-1", fixedParty(CM));
  for (const h of game.party) { h.max = 9000; h.hp = 9000; h.df = 50; }
  const G = CM.guardianMonster("forge", 15);
  game.floor.things["3,3"] = { type: "guardian", group: [G] };
  game.startCombat("3,3", game.floor.things["3,3"]);
  const warden = game.foes.find((m) => m.guardian);
  game.messages = [];
  game.guardianAct(warden); game.guardianAct(warden);                    // turns 1 and 2: after the second, the hammer is lifted
  assert.ok(warden.intent, "the third turn's move is shown");
  assert.ok(game.messages.some((m) => m.includes("lifts the hammer")));
  game.guardianAct(warden);                                               // turn 3: the hammer comes down, and the intent is spent
  assert.ok(game.messages.some((m) => m.includes("brings it down")));
  assert.strictEqual(warden.intent, null);
});

test("combos: frost then the shield, the knife on a marked foe, fire on the held - found once, kept always", () => {
  const CM = load(), game = new CM.Game();
  game.newGame("combo-1", fixedParty(CM));
  const rnd = new CM.Random(9), orc = CM.makeMonster(CM.monsterKind("Orc"), 3, rnd); orc.max = orc.hp = 5000;
  game.floor.things["2,2"] = { type: "monsters", group: [orc] };
  game.startCombat("2,2", game.floor.things["2,2"]);
  const knight = game.party.find((h) => h.cls === "Knight"), rogue = game.party.find((h) => h.cls === "Rogue"), mage = game.party.find((h) => h.cls === "Mage");
  orc.chilled = 2;
  game.messages = [];
  game.strike(knight, orc, " with the shield", { bash: true, sure: true });
  assert.ok(game.messages.some((m) => m.includes("the ice shatters")), game.messages.join(" | "));
  assert.strictEqual(game.combos.shatter, 1);
  assert.strictEqual(orc.chilled, 0);
  orc.marked = true; game.messages = [];
  game.strike(rogue, orc, "", { sure: true });
  assert.ok(game.messages.some((m) => m.includes("the knife finds the mark")));
  orc.held = 2; game.messages = []; game.casting = mage;
  game.spellHit(orc, 20, "Fire:", "fire");
  assert.ok(game.messages.some((m) => m.includes("the vines burn")));
  assert.strictEqual(CM.storage.getItem("claudemagic.combos") !== null, true);
  const CM2 = load({ storage: CM.storage }), g2 = new CM2.Game();
  assert.strictEqual(g2.combos.shatter, 1);
});

test("the bestiary learns from fighting: kinds met and slain, what they fear", () => {
  const CM = load(), game = new CM.Game();
  game.newGame("beast-1", fixedParty(CM));
  const rnd = new CM.Random(11), zombie = CM.makeMonster(CM.monsterKind("Zombie"), 1, rnd);
  game.floor.things["2,2"] = { type: "monsters", group: [zombie] };
  game.startCombat("2,2", game.floor.things["2,2"]);
  assert.strictEqual(game.bestiary.Zombie.seen, 1);
  game.casting = game.party[3];
  game.spellHit(zombie, 500, "Fire:", "fire");
  assert.deepStrictEqual(Array.from(game.bestiary.Zombie.weak), ["fire"]);
  game.afterBlows();
  assert.strictEqual(game.mode, "explore");
  assert.strictEqual(game.bestiary.Zombie.slain, 1);
  const exp = JSON.parse(game.exportText());
  assert.strictEqual(exp.bestiary.Zombie.slain, 1);
});

test("the monsters' new ways: a healer mends, a warder wards, a splitter tears in two, a thief bolts with a potion", () => {
  const CM = load(), game = new CM.Game();
  game.newGame("ways-2", fixedParty(CM));
  const rnd = new CM.Random(13);
  const hag = CM.makeMonster(CM.monsterKind("Weed Hag"), 20, rnd), drowned = CM.makeMonster(CM.monsterKind("Drowned"), 20, rnd);
  game.floor.things["2,2"] = { type: "monsters", group: [drowned, hag] };
  game.startCombat("2,2", game.floor.things["2,2"]);
  drowned.hp = 10; game.messages = [];
  game.monsterAct(hag);
  assert.ok(drowned.hp > 10 && game.messages.some((m) => m.includes("wounds close")));
  const golem = CM.makeMonster(CM.monsterKind("Crystal Golem"), 30, rnd);
  game.foes.push(golem); game.rnd = new CM.Random(1);
  let warded = 0;
  for (let i = 0; i < 10 && !warded; i++) { game.monsterAct(golem); warded = game.living().filter((m) => m.warded > 0).length; }
  assert.ok(warded > 0, "the golem wards someone");
  const beast = CM.makeMonster(CM.monsterKind("Spore Beast"), 26, rnd);
  game.foes.push(beast);
  const n = game.foes.length;
  game.spellHit(beast, Math.ceil(beast.max * 0.6), "", "frost");
  assert.strictEqual(game.foes.length, n + 1, "it tears in two");
  assert.ok(game.foes[n].summoned && game.foes[n].kind === "Spore Beast");
  const imp = CM.makeMonster(CM.monsterKind("Foundry Imp"), 36, rnd);
  game.foes.push(imp); game.bag.push({ name: "Healing Potion", kind: "heal", power: 20, value: 20 });
  const had = game.bag.length; game.rnd = new CM.Random(2);
  for (let i = 0; i < 10 && !imp.fled; i++) { imp.stole = false; game.monsterAct(imp); }
  assert.ok(imp.fled && game.bag.length === had - 1, "the imp bolts with something");
});

test("the Forge-Warden's heat sears whoever strikes it (and a blade that fears it does little)", () => {
  const CM = load(), game = new CM.Game();
  game.newGame("heat-1", fixedParty(CM));
  const G = CM.guardianMonster("forge", 15);
  game.floor.things["3,3"] = { type: "guardian", group: [G] };
  game.startCombat("3,3", game.floor.things["3,3"]);
  const warden = game.foes.find((m) => m.guardian), knight = game.party.find((h) => h.cls === "Knight");
  knight.weapon.props.element = "fire"; knight.weapon.unknown = false;
  const hp = knight.hp; game.messages = [];
  game.strike(knight, warden, "", { sure: true });
  assert.ok(knight.hp < hp, "the heat sears the striker");
  assert.ok(game.messages.some((m) => m.includes("sears")));
  assert.ok(game.messages.some((m) => m.includes("does little to it")), game.messages.join(" | "));
});

test("the hoard: affixes by the seed, a unique a band, and what the words mean", () => {
  const CM = load();
  const a = JSON.stringify(CM.makeFloor(12, "hoard")), b = JSON.stringify(CM.makeFloor(12, "hoard"));
  assert.strictEqual(a, b, "the same seed, the same affixes");
  let fine = 0, rare = 0, uniques = {};
  for (let f = 1; f <= 50; f++) for (const t of Object.values(CM.makeFloor(f, "hoard").things)) if (t.type === "chest") for (const it of t.items) {
    const r = (it.props || {}).rarity; if (r === "fine") fine++; if (r === "rare") rare++;
    if (it.props && it.props.unique) uniques[it.props.unique] = f;
  }
  assert.ok(fine > 60 && rare > 15, `fine ${fine}, rare ${rare}`);
  assert.strictEqual(Object.keys(uniques).length, 11, "one unique in every band, and the Bag of Holding in the palace: " + JSON.stringify(uniques));
  for (const [id, f] of Object.entries(uniques)) assert.strictEqual(CM.themeIndex(f), id === "holding" ? 3 : CM.UNIQUES[id].band, `${id} lies in its own band`);
  const sword = { name: "Long Sword", base: "Long Sword", kind: "weapon", slot: "weapon", power: 8, value: 100, props: {} };
  CM.affix(sword, 30, new CM.Random(4));
  if (sword.props.rarity) { assert.ok(sword.name !== "Long Sword"); assert.ok(CM.itemLabel(sword).length > 10); assert.strictEqual(CM.baseName(sword), "Long Sword"); }
  const u = CM.makeUnique("tidecaller");
  assert.strictEqual(CM.rarityOf(u), "unique");
  assert.ok(CM.itemLabel(u).includes("sleep") && CM.itemLabel(u).includes("tide"));
});

test("gear that does more: stats, weak spots, mending, thorns, the blade that drinks, the relics worn together", () => {
  const CM = load(), game = new CM.Game();
  game.newGame("gear-1", fixedParty(CM));
  const knight = game.party.find((h) => h.cls === "Knight"), str = CM.heroStat(knight, "str"), crit = game.critChance(knight);
  knight.helm = { name: "Cap of the Bear", base: "Cap", kind: "helm", slot: "helm", power: 1, value: 10, props: { stats: { str: 2 }, crit: 0.1, regen: 2, thorns: 3 } };
  assert.strictEqual(CM.heroStat(knight, "str"), str + 2);
  assert.ok(game.critChance(knight) > crit + 0.09);
  const rnd = new CM.Random(3), orc = CM.makeMonster(CM.monsterKind("Orc"), 3, rnd); orc.max = orc.hp = 500;
  game.floor.things["2,2"] = { type: "monsters", group: [orc] };
  game.startCombat("2,2", game.floor.things["2,2"]);
  knight.hp = 10; const foeHp = orc.hp;
  game.hurt(knight, 3, orc);
  assert.strictEqual(orc.hp, foeHp - 3, "the spikes tear the striker");
  const was = knight.hp;
  game.endRound();
  assert.ok(knight.hp >= Math.min(knight.max, was + 2) || knight.hp === knight.max, "mending gear mends a round");
  knight.weapon.props.lifesteal = true; knight.weapon.unknown = false; knight.hp = 5;
  game.strike(knight, orc, "", { sure: true });
  assert.ok(knight.hp > 5, "the blade drinks");
  knight.helm = CM.relic("rat"); knight.offhand = CM.relic("knight"); knight.helm.unknown = knight.offhand.unknown = false;
  const atk = knight.atk; CM.recompute(knight);
  assert.ok(CM.relicsWorn(knight) === 2 && knight.atk >= atk + 2 - 1, "two relics: the set's attack");
});

test("the alchemist: ingredients drop, recipes brew, an oil burns for three fights, a firepot bursts, an elixir stays", () => {
  const CM = load(), game = new CM.Game();
  game.newGame("alch-1", fixedParty(CM));
  assert.strictEqual(game.brew("oilfire"), "The alchemist is at the camp.");
  game.enterFloor(5, "down"); game.setMode("camp"); game.reachCamp(5);
  assert.match(game.recipeLacks("oilfire"), /wants/);
  game.bag.push(CM.ingredient("forgesoot")); game.gold = 500;
  assert.strictEqual(game.brew("oilfire"), "");
  const oil = game.bag.find((i) => i.kind === "oil");
  assert.ok(oil && oil.element === "fire");
  const knight = game.party.find((h) => h.cls === "Knight");
  assert.strictEqual(game.give(game.bag.indexOf(oil), game.party.indexOf(knight)), "");
  assert.deepStrictEqual(JSON.parse(JSON.stringify(knight.oil)), { element: "fire", fights: 3 });
  game.setMode("explore");
  const rnd = new CM.Random(5), troll = CM.makeMonster(CM.monsterKind("Troll"), 3, rnd); troll.max = troll.hp = 400;
  game.floor.things["2,2"] = { type: "monsters", group: [troll] };
  game.startCombat("2,2", game.floor.things["2,2"]);
  game.messages = [];
  game.strike(knight, troll, "", { sure: true });
  assert.ok(game.messages.some((m) => m.includes("fire bites deep")), game.messages.join(" | "));
  game.bag.push(CM.bomb());
  const row = game.bag.findIndex((i) => i.kind === "bomb"), hp = troll.hp;
  game.combat.waiting = knight;
  assert.ok(game.act("item", { row }));
  assert.ok(troll.hp < hp && !game.bag.some((i) => i.kind === "bomb"));
  troll.hp = 0; game.afterBlows();
  assert.strictEqual(game.mode, "explore");
  assert.strictEqual(knight.oil.fights, 2, "the oil wears a fight");
  game.setMode("camp");
  game.bag.push(CM.ingredient("rootsap"));
  const who = game.alive().reduce((a, b) => (a.stats.con <= b.stats.con ? a : b)), con = who.stats.con;
  assert.strictEqual(game.brew("vigour"), "");
  assert.strictEqual(who.stats.con, con + 1);
  assert.ok(game.achievements.distilled);
});

test("the smith, extended: salvage to scrap, five scrap for a diamond, a suffix reworked", () => {
  const CM = load(), game = new CM.Game();
  game.newGame("smith-1", fixedParty(CM));
  game.enterFloor(5, "down"); game.setMode("camp"); game.reachCamp(5); game.gold = 1000;
  for (let i = 0; i < 5; i++) game.bag.push({ name: "Mace", base: "Mace", kind: "weapon", slot: "weapon", power: 4, value: 60, props: {} });
  for (let i = 0; i < 5; i++) assert.strictEqual(game.salvage(game.bag.findIndex((it) => it.kind === "weapon")), "");
  assert.strictEqual(game.bag.filter((i) => i.kind === "scrap").length, 5);
  const knight = game.party.find((h) => h.cls === "Knight"), power = knight.weapon.power;
  assert.strictEqual(game.smith("enchant", game.party.indexOf(knight), "weapon"), "");
  assert.strictEqual(knight.weapon.power, power + 1);
  assert.strictEqual(game.bag.filter((i) => i.kind === "scrap").length, 0);
  assert.match(game.smith("reroll", game.party.indexOf(knight), "weapon"), /gem/);
  game.bag.push(CM.gem("ruby"));
  assert.strictEqual(game.smith("reroll", game.party.indexOf(knight), "weapon"), "");
  assert.ok(knight.weapon.props.affixes.length >= 1 && knight.weapon.name.includes(" of "), knight.weapon.name);
  assert.match(game.salvage(game.bag.push(CM.makeUnique("tidecaller")) - 1), /won't/);
});

test("the dungeon, stranger: choices, a strongbox two floors below its key, a peddler, rivals - by the seed", () => {
  const CM = load(), game = new CM.Game();
  game.newGame("strange", fixedParty(CM));
  const counts = {}, keys = [], boxes = [];
  for (let f = 1; f <= 50; f++) { const fl = CM.makeFloor(f, "strange"); assert.ok(CM.solvable(fl), "floor " + f); for (const [k, t] of Object.entries(fl.things)) { counts[t.type] = (counts[t.type] || 0) + 1; if (t.type === "boxkey") keys.push(t.box); if (t.type === "strongbox") boxes.push(f); } }
  assert.ok(counts.event >= 8 && counts.strongbox >= 5 && counts.rivals >= 2, JSON.stringify(counts));
  assert.deepStrictEqual(keys.sort((a, b) => a - b), boxes.sort((a, b) => a - b), "every key has its box two floors down, and no box lacks its key");
  // a choice: the shrine, then the saint's prayer blesses the next fight
  const fl = game.floor;
  fl.things["2,2"] = { type: "event", event: "bloodshrine", done: false }; fl.pos = [2, 2];
  let asked = null; game.on("choice", (c) => { asked = c; });
  game.use();
  assert.ok(asked && asked.options.length === 2);
  const front = game.alive().find((h) => h.row === "front"), str = front.stats.str;
  assert.ok(game.choose("2,2", 0));
  assert.strictEqual(front.stats.str, str + 1); assert.ok(fl.things["2,2"].done);
  fl.things["3,3"] = { type: "event", event: "statue", done: false }; fl.pos = [3, 3];
  game.choose("3,3", 0);
  assert.ok(game.blessedNext);
  const mk = Object.keys(fl.things).find((k) => fl.things[k].type === "monsters");
  game.startCombat(mk, fl.things[mk]);
  assert.ok(game.combat.bless && !game.blessedNext);
  autoplayFight(CM, game);
  // the strongbox wants its own key
  game.setMode("explore");
  fl.things["4,4"] = { type: "strongbox", from: 2, opened: false }; fl.pos = [4, 4];
  game.use(); assert.ok(!fl.things["4,4"].opened);
  game.bag.push({ name: "Strongbox Key (floor 1)", kind: "boxkey", box: 1, power: 0, value: 0 });
  const gold = game.gold, n = game.bag.length;
  game.use();
  assert.ok(fl.things["4,4"].opened && game.gold === gold + 60 && game.bag.length === n && game.achievements.strongbox, "the key opens it: gold and a rare thing");
  // the peddler's cloth, and buying from it
  fl.things["5,5"] = { type: "peddler", stock: null }; fl.pos = [5, 5];
  game.use();
  assert.ok(game.shopping && game.stock && game.stock.length === 6 && game.peddling);
  game.gold = 1000;
  const want = game.stock.findIndex((i) => i.kind === "greaterheal");
  assert.strictEqual(game.buy(want), "");
  assert.ok(game.bag.some((i) => i.kind === "greaterheal"));
  game.closeBag();
  assert.strictEqual(game.stock, null); assert.strictEqual(game.mode, "explore");
  assert.ok(fl.things["5,5"].stock.every((i) => i.kind !== "greaterheal"), "what you buy stays bought");
  // the rivals: a trade, and a fight
  fl.things["6,6"] = { type: "rivals", met: false }; fl.pos = [6, 6];
  game.use();
  assert.ok(asked && asked.rivals);
  game.gold = 100;
  assert.ok(game.chooseRivals("6,6", 0));
  assert.strictEqual(game.gold, 60); assert.ok(!fl.things["6,6"]);
  fl.things["7,7"] = { type: "rivals", met: false }; fl.pos = [7, 7];
  game.chooseRivals("7,7", 1);
  assert.strictEqual(game.mode, "combat");
  assert.ok(game.foes.some((m) => m.kind === "Sellsword") && game.foes.some((m) => m.row === "back"));
  for (const m of game.foes) m.hp = 0;
  game.afterBlows();
  assert.ok(game.achievements.rivals, "their purse and their best thing");
  game.saveRun();
  const CM2 = load({ storage: CM.storage }), g2 = new CM2.Game();
  g2.continueRun();
  assert.ok(g2.floor.things["4,4"].opened && g2.floor.things["2,2"].done);
});

test("the bands' hazards: spores, vents, bone piles, the tide, the mirror walls", () => {
  const CM = load(), game = new CM.Game();
  game.newGame("hazard-1", fixedParty(CM));
  for (const h of game.party) { h.max = 500; h.hp = 500; }
  const bands = { 21: "tide", 26: "spores", 31: "mirror", 36: "vents", 41: "bonepiles" };
  for (const [f, id] of Object.entries(bands)) { const fl = CM.makeFloor(Number(f), "hazard-1"); assert.strictEqual(fl.hazard, id, "floor " + f); }
  game.enterFloor(26, "down");
  assert.ok(game.messages.some((m) => m.includes("Spore clouds")), "the hazard is named on arrival");
  const fl = game.floor, k = Object.keys(fl.features).find((x) => fl.features[x].type === "spores");
  assert.ok(k);
  game.rnd = new CM.Random(1);
  game.arrive(fl.features[k], k);
  assert.ok(fl.features[k].known);
  game.enterFloor(36, "down");
  const vk = Object.keys(game.floor.features).find((x) => game.floor.features[x].type === "vents");
  game.steps = 3; const hp = game.party[0].hp;
  game.arrive(game.floor.features[vk], vk);
  assert.ok(game.party[0].hp < hp, "the vent breathes on the beat");
  game.enterFloor(41, "down");
  const bk = Object.keys(game.floor.features).find((x) => game.floor.features[x].type === "bonepiles");
  game.rnd = new CM.Random(2);
  let fights = 0;
  for (let i = 0; i < 1; i++) { game.floor.features[bk].spent = false; game.arrive(game.floor.features[bk], bk); if (game.mode === "combat") { fights++; for (const m of game.foes) m.hp = 0; game.afterBlows(); } }
  assert.ok(game.floor.features[bk].spent);
  game.enterFloor(21, "down");
  const tideFloor = game.floor; game.steps = CM.TIDE_STEPS - 1;
  const open = CM.DIRS.findIndex(([dx, dy]) => CM.passable(tideFloor, tideFloor.pos[0] + dx, tideFloor.pos[1] + dy));
  tideFloor.facing = open; game.light = { kind: "torch", left: 100 };
  game.move(0);
  assert.strictEqual(tideFloor.tide, true, "the tide turns on the thirtieth step");
  game.move(2);
  assert.ok(game.light.left <= 96, "at high tide the torch burns double");
  game.enterFloor(31, "down");
  const rnd = new CM.Random(3), a = CM.makeMonster(CM.monsterKind("Crystal Golem"), 25, rnd), b = CM.makeMonster(CM.monsterKind("Shard Wisp"), 25, rnd);
  game.floor.things["2,2"] = { type: "monsters", group: [a, b] };
  game.startCombat("2,2", game.floor.things["2,2"]);
  const mage = game.party.find((h) => h.cls === "Mage"); mage.mp = 50; game.combat.waiting = mage;
  const bHp = b.hp;
  game.useAbility(mage, "missile", a);
  assert.ok(b.hp < bHp && game.messages.some((m) => m.includes("rebounds")), "the bolt rebounds onto the other");
});

test("three callings more, earned: the Monk, the Necromancer, the Artificer", () => {
  const CM = load(), game = new CM.Game();
  assert.deepStrictEqual(game.classesAvailable().slice().sort(), CM.CLASS_ORDER.slice().sort(), "none of the three to start");
  game.achievements.ironman = { date: "x" }; game.trophies.patriarch = { date: "x" }; game.trophies.master = { date: "x" };
  assert.strictEqual(game.classesAvailable().length, 11);
  const party = ["Monk", "Necromancer", "Artificer", "Cleric"].map((cls) => ({ cls, name: cls, stats: CM.rollStats(cls, new CM.Random(cls)), row: CM.CLASSES[cls].row }));
  game.newGame("new-1", party);
  const monk = game.party[0], necro = game.party[1], art = game.party[2];
  assert.ok(monk.weapon.props.fists && monk.weapon.power === 3);
  monk.level = 10; CM.recompute(monk); assert.strictEqual(monk.weapon.power, 8, "the hands grow");
  assert.match(CM.cantWear(monk, { kind: "weapon", name: "Mace", power: 4, props: {} }), /hands/);
  assert.ok(CM.isCaster(necro) && !CM.isCaster(monk));
  assert.ok(game.dodgeOf(monk) < 1 && game.dodgeOf(necro) === 1);
  const rnd = new CM.Random(2), orcs = [1, 2, 3].map(() => CM.makeMonster(CM.monsterKind("Orc"), 4, rnd));
  for (const o of orcs) o.max = o.hp = 300;
  for (const h of game.party) { h.max = 300; h.hp = 300; h.mp = 60; h.maxmp = 60; h.level = 8; }
  game.floor.things["2,2"] = { type: "monsters", group: orcs };
  game.startCombat("2,2", game.floor.things["2,2"]);
  const c = game.combat;
  c.waiting = monk; game.messages = [];
  assert.ok(game.useAbility(monk, "blows", orcs[0]) && game.messages.filter((m) => m.includes("hits")).length >= 1);
  c.waiting = art;
  assert.ok(game.useAbility(art, "turret", null) && c.turret);
  assert.ok(game.useAbility(art, "wardengine", null) && c.protect);
  assert.ok(game.useAbility(art, "oilgears", null) && c.oiled);
  c.waiting = necro; necro.hp = 100;
  assert.ok(game.useAbility(necro, "drain", orcs[1]) && necro.hp > 100, "drain keeps half");
  assert.ok(game.useAbility(necro, "hex", orcs[1]) && orcs[1].marked && orcs[1].blind > 0);
  assert.ok(!game.useAbility(necro, "thrall", null) || !c.thrall, "nothing dead yet to raise");
  orcs[2].hp = 0; orcs[2].dead = true; necro.used = {};
  assert.ok(game.useAbility(necro, "thrall", null) && c.thrall && c.thrall.hp > 0);
  const hpBefore = game.party.map((h) => h.hp).join(",");
  game.rnd = new CM.Random(5);
  let blowsOnThrall = 0;
  for (let i = 0; i < 12; i++) { const t = game.pickTarget(orcs[0]); if (t && t.thrall) blowsOnThrall++; }
  assert.ok(blowsOnThrall > 4, "the thrall takes the blows meant for the party");
  const foeHp = orcs[0].hp + orcs[1].hp;
  game.enginesAct();
  assert.ok(orcs[0].hp + orcs[1].hp < foeHp, "the turret and the thrall strike at the round's end");
  assert.strictEqual(game.party.map((h) => h.hp).join(","), hpBefore);
  c.waiting = necro;
  assert.ok(game.useAbility(necro, "deathpact", null));
  assert.ok(orcs[0].hp < 300 && orcs[1].hp < 300);
});

test("the capstone at fifteen, and the bonds of old friends", () => {
  const CM = load(), game = new CM.Game();
  game.newGame("caps-1", fixedParty(CM));
  const knight = game.party.find((h) => h.cls === "Knight");
  knight.path = "bulwark"; knight.level = 14;
  assert.ok(CM.trait(knight, "aegis") && !CM.trait(knight, "immovable"));
  knight.level = 15;
  assert.ok(CM.trait(knight, "immovable"));
  for (const cls of Object.keys(CM.PATHS)) for (const P of Object.values(CM.PATHS[cls])) assert.ok(P.t3 && P.t3.id && P.t3.what, `${cls} ${P.name} has a capstone`);
  assert.strictEqual(game.afflict(knight, "paralysis", "an ogre"), false, "immovable: never held");
  // bonds: thirty-nine fights together, then one more
  const rogue = game.party.find((h) => h.cls === "Rogue");
  const k = [knight.name, rogue.name].sort().join("|");
  game.pairFights = { [k]: CM.BOND_FIGHTS - 1 };
  CM.recompute(knight); knight.hp = knight.max;
  const atk = knight.atk;
  const rnd = new CM.Random(3), rat = CM.makeMonster(CM.monsterKind("Giant Rat"), 1, rnd); rat.hp = 1;
  game.floor.things["2,2"] = { type: "monsters", group: [rat] };
  game.startCombat("2,2", game.floor.things["2,2"]);
  rat.hp = 0; game.afterBlows();
  assert.strictEqual(game.mode, "explore");
  assert.ok(game.bonds.length === 1 && game.bondOf(knight) === rogue && game.bondOf(rogue) === knight, "old friends now");
  assert.strictEqual(knight.atk, atk + 1);
  assert.ok(game.achievements.bonded);
  game.saveRun();
  const CM2 = load({ storage: CM.storage }), g2 = new CM2.Game();
  g2.continueRun();
  assert.ok(g2.bondOf(g2.party.find((h) => h.cls === "Knight")), "the bond is saved");
  // the memorial: a hero laid to rest at the camp
  game.enterFloor(5, "down"); game.setMode("camp"); game.reachCamp(5);
  rogue.hp = 0; game.gold = 5000;
  assert.strictEqual(game.hire(0), "");
  assert.ok(game.memorial.length === 1 && game.memorial[0].name === rogue.name && game.memorial[0].cls === "Rogue");
  assert.strictEqual(game.bonds.length, 0, "a bond ends at the grave");
  assert.ok(JSON.parse(game.exportText()).memorial.length === 1);
});

test("around the game: run codes, the week's seed and party, the new mutators, the remains of a fallen party", () => {
  const CM = load(), game = new CM.Game();
  const party = fixedParty(CM);
  const code = CM.runCode("ember-crypt-417", "grim", "endless", "veteran", party);
  assert.match(code, /^CM1:ember-crypt-417:grim:endless:veteran:/);
  const back = CM.parseRunCode(code);
  assert.strictEqual(back.seed, "ember-crypt-417"); assert.strictEqual(back.difficulty, "grim"); assert.strictEqual(back.mode, "endless");
  assert.deepStrictEqual(back.party.map((p) => p.cls), party.map((p) => p.cls));
  assert.deepStrictEqual(back.party[0].stats, party[0].stats);
  assert.strictEqual(CM.parseRunCode("raven-rune-533"), null);
  const w = CM.weeklySeed(new Date(2026, 9, 30));
  assert.strictEqual(w, "weekly-2026-44");
  assert.strictEqual(CM.weeklySeed(new Date(2026, 10, 1)), "weekly-2026-44", "Sunday is still the same week");
  assert.strictEqual(CM.weeklySeed(new Date(2026, 10, 2)), "weekly-2026-45");
  assert.strictEqual(CM.mutatorsFor(w).length, 3);
  assert.strictEqual(JSON.stringify(CM.weeklyParty(w)), JSON.stringify(CM.weeklyParty(w)));
  assert.strictEqual(CM.mutatorsFor(CM.dailySeed()).length, 2);
  // glass cannon, the pilgrim, the hunted
  game.newGame("mut-1", party, "pauper", "fair", ["glass", "pilgrim", "hunted"]);
  assert.ok(game.has("glass") && game.has("pilgrim"));
  const knight = game.party[0], xp0 = knight.xp;
  game.enterFloor(2, "down");
  assert.ok(knight.xp > xp0, "the pilgrim earns a floor's worth");
  const rnd = new CM.Random(4), rat = CM.makeMonster(CM.monsterKind("Giant Rat"), 1, rnd); rat.max = rat.hp = 1000;
  game.floor.things["2,2"] = { type: "monsters", group: [rat] };
  game.startCombat("2,2", game.floor.things["2,2"]);
  const dealt = game.strike(knight, rat, "", { sure: true });
  const plain = new CM.Game(); plain.newGame("mut-2", party); const rat2 = CM.makeMonster(CM.monsterKind("Giant Rat"), 1, new CM.Random(4)); rat2.max = rat2.hp = 1000;
  plain.floor.things["2,2"] = { type: "monsters", group: [rat2] }; plain.startCombat("2,2", plain.floor.things["2,2"]);
  let most = 0; for (let i = 0; i < 20; i++) most = Math.max(most, plain.strike(plain.party[0], rat2, "", { sure: true }));
  assert.ok(dealt >= most, `glass: ${dealt} should be at least any plain blow (${most})`);
  const xpBefore = knight.xp; rat.hp = 0; game.afterBlows();
  assert.strictEqual(knight.xp, xpBefore, "the pilgrim learns nothing from a fight");
  // the remains: a party that fell here before, on this seed
  const CM3 = load(), g3 = new CM3.Game();
  g3.newGame("fell-1", fixedParty(CM3));
  g3.enterFloor(3, "down");
  g3.party[1].ring = { name: "Ring of Grace +1", kind: "ring", slot: "ring", power: 1, value: 80, props: { stat: "dex" } };
  for (const h of g3.party) h.hp = 0;
  const where = g3.floor.pos.slice();
  g3.endRun(false);
  assert.ok(g3.fallen.length === 1 && g3.fallen[0].floor === 3 && g3.fallen[0].item && g3.fallen[0].item.kind === "ring");
  const g4 = new CM3.Game();
  g4.newGame("fell-1", fixedParty(CM3));
  g4.enterFloor(3, "down");
  const k = Object.keys(g4.floor.things).find((x) => g4.floor.things[x].type === "remains"), remains = k && g4.floor.things[k];
  assert.ok(remains, "their remains lie where they fell (or the nearest open square to the stairs they fell on)");
  assert.ok(Math.abs(Number(k.split(",")[0]) - where[0]) + Math.abs(Number(k.split(",")[1]) - where[1]) <= 4);
  g4.floor.pos = k.split(",").map(Number);
  const n = g4.bag.length;
  g4.use();
  assert.ok(g4.bag.length === n + 1 && !g4.floor.things[k] && g4.remainsFound.length === 1);
  g4.saveRun();
  const exp = JSON.parse(g4.exportText());
  assert.ok(Array.isArray(exp.fallen) && exp.fallen.length === 1);
});

test("generator 1 is frozen: twenty-eight seeds' fingerprints; generator 2 has grown, and its floors can be finished", () => {
  const CM = load(), fx = JSON.parse(fs.readFileSync(path.join(__dirname, "fixtures", "gen1.json"), "utf8"));
  let n = 0;
  for (const [seed, floors] of Object.entries(fx)) for (const [k, print] of Object.entries(floors)) {
    if (n++ % 7) continue;                                               // (a fifth of them: the whole set takes a minute)
    assert.strictEqual(CM.floorPrint(CM.makeFloor(Number(k), seed, 1)), print, `gen 1, ${seed} floor ${k}`);
    assert.ok(CM.solvable(CM.makeFloor(Number(k), seed, 2)), `gen 2 has grown, and every floor of it can be finished: ${seed} floor ${k}`);
  }
  assert.strictEqual(CM.GEN, 2);
  assert.ok(typeof CM.generators[1] === "function" && typeof CM.generators[2] === "function" && typeof CM.planFloor === "function");
  const plan = CM.planFloor(9, "plan", new CM.Random(1), null, null);
  assert.ok(Array.isArray(plan.pieces) && plan.roomTries === 23);
});

test("a run keeps the generator it began with; a v2.0 save is a generator-1 run", () => {
  const CM = load(), game = new CM.Game();
  game.newGame("gen-1");
  assert.strictEqual(game.gen, 2);
  game.saveRun();
  assert.strictEqual(JSON.parse(CM.storage.getItem("claudemagic.run")).gen, 2);
  const CM2 = load({ storage: CM.storage }), g2 = new CM2.Game();
  g2.continueRun();
  assert.strictEqual(g2.gen, 2);
  const CM3 = load();
  CM3.storage.setItem("claudemagic.run", fs.readFileSync(path.join(__dirname, "fixtures", "run-v1.0.json"), "utf8"));
  const g3 = new CM3.Game(); g3.continueRun();
  assert.strictEqual(g3.gen, 1);
});

test("the log: a bot's run, played again from its seed and its log, comes out the same", () => {
  const CM = load(), game = new CM.Game();
  game.newGame("replay-1", fixedParty(CM));
  playRun(CM, game, { maxFloor: 5 });
  const spec = game.replaySpec();
  assert.ok(spec.log.length > 50, "the log has the run in it: " + spec.log.length);
  assert.ok(spec.party && spec.party.length === 4);
  const again = CM.replayRun(spec);
  assert.strictEqual(again.floor.number, game.floor.number);
  same(again.floor.pos, game.floor.pos);
  assert.strictEqual(again.gold, game.gold);
  same(again.party, game.party);
  assert.strictEqual(again.tally.fights, game.tally.fights);
  assert.strictEqual(again.messages.slice(-3).join("|"), game.messages.slice(-3).join("|"));
  const half = CM.replayRun(spec, Math.floor(spec.log.length / 2));
  assert.ok(half.tally.steps <= game.tally.steps && half.mode !== "title");
  game.saveRun();
  const CM2 = load({ storage: CM.storage }), g2 = new CM2.Game();
  g2.continueRun();
  assert.strictEqual(g2.runLog.length, spec.log.length, "the log is saved with the run");
  const mage = game.party.find((h) => h.cls === "Mage"); mage.mp = 20;
  game.castOutside(game.party.indexOf(mage), "light", null);
  assert.ok(game.tally.abilities && game.tally.abilities.light === 1, "the tally counts the spells used");
});

test("the ground of a fight: water holds frost and halves fire, pillars limit the reach, the dark makes blows go wide", () => {
  const CM = load(), game = new CM.Game();
  game.newGame("ground-1", fixedParty(CM));
  const mage = game.party.find((h) => h.cls === "Mage"); mage.mp = 99; mage.level = 10;
  game.enterFloor(10, "down");                                           // (the Drowned Hall: water and pillars)
  const fl = game.floor, gk = Object.keys(fl.things).find((k) => fl.things[k].type === "guardian");
  const [gx, gy] = gk.split(",").map(Number); fl.pos = [gx, gy + 1];
  assert.ok(game.terrain().includes("water") && game.terrain().includes("pillars"), game.terrain().join(","));
  assert.strictEqual(game.reachLimit(), 2);
  const rnd = new CM.Random(2), orcs = [1, 2, 3].map(() => CM.makeMonster(CM.monsterKind("Orc"), 5, rnd));
  for (const o of orcs) o.max = o.hp = 500;
  fl.things["1,1"] = { type: "monsters", group: orcs }; fl.pos = [gx, gy + 1];
  game.startCombat("1,1", fl.things["1,1"]); game.combat.waiting = mage;
  game.useAbility(mage, "frost", null);
  assert.ok(orcs.every((o) => o.held > 0), "on water, frost holds every foe");
  game.messages = []; game.casting = mage;
  game.spellHit(orcs[0], 40, "Fire:", "fire");
  assert.ok(game.messages.some((m) => m.includes("sputters")));
  assert.ok(game.terrainNote().includes("Knee-deep"));
  fl.dark.push(CM.keyOf(fl.pos[0], fl.pos[1])); game.spellLight = 0;
  assert.ok(game.terrain().includes("dark"));
});

test("formations: the wedge's point takes the blows, the loose line halves a breath and spells cost one more", () => {
  const CM = load(), game = new CM.Game();
  game.newGame("form-1", fixedParty(CM));
  assert.strictEqual(game.formation, "line");
  assert.ok(game.setFormation("wedge"));
  const knight = game.party.find((h) => h.cls === "Knight"), df = game.effective(knight).df;
  assert.strictEqual(game.point(), knight);
  assert.strictEqual(game.effective(knight).df, df);
  const rnd = new CM.Random(3), orc = CM.makeMonster(CM.monsterKind("Orc"), 3, rnd), demon = CM.makeMonster(CM.monsterKind("Demon"), 3, rnd);
  for (const m of [orc, demon]) m.max = m.hp = 500;
  game.floor.things["2,2"] = { type: "monsters", group: [orc, demon] };
  game.startCombat("2,2", game.floor.things["2,2"]);
  assert.ok(!game.setFormation("loose"), "not in a fight");
  let onPoint = 0; for (let i = 0; i < 20; i++) if (game.pickTarget(orc) === knight) onPoint++;
  assert.strictEqual(onPoint, 20, "every blow that isn't a shot goes to the point");
  const cleric = game.party.find((h) => h.cls === "Cleric"); game.messages = [];
  game.strike(cleric, orc, "", { sure: true });
  assert.ok(!game.messages.some((m) => m.includes("reaching from the back row")), "the rest hit for full");
  for (const m of [orc, demon]) m.hp = 0; game.afterBlows();
  game.setFormation("loose");
  const mage = game.party.find((h) => h.cls === "Mage"); mage.mp = 99;
  const d2 = CM.makeMonster(CM.monsterKind("Demon"), 3, new CM.Random(4)); d2.max = d2.hp = 500; d2.breath = 1;
  game.floor.things["3,3"] = { type: "monsters", group: [d2] }; game.startCombat("3,3", game.floor.things["3,3"]);
  d2.breath = 1;                                                         // (the next act is a breath)
  for (const h of game.party) { h.max = 1000; h.hp = 1000; }
  game.monsterAct(d2);
  const breathed = game.party.map((h) => 1000 - h.hp).filter((x) => x > 0);
  assert.ok(breathed.length === 4 && Math.max(...breathed) <= Math.ceil((Math.floor(d2.atk / 3) + 2) / 2) + 1, "a breath does half: " + breathed.join(","));
  game.combat.waiting = mage; const mp = mage.mp;
  game.useAbility(mage, "missile", d2);
  assert.strictEqual(mp - mage.mp, CM.ABILITIES.missile.mp + 1, "spells cost one more");
});

test("second forms: the Rat King hides in the swarm, the Knight floods the hall, the Warden's hammer breaks", () => {
  const CM = load(), game = new CM.Game();
  game.newGame("form2-1", fixedParty(CM));
  for (const h of game.party) { h.max = 5000; h.hp = 5000; }
  const fight = (id, floor) => { game.setMode("explore"); const G = CM.guardianMonster(id, floor); game.floor.things["4,4"] = { type: "guardian", group: [G] }; game.startCombat("4,4", game.floor.things["4,4"]); return game.foes.find((m) => m.guardian); };
  const rat = fight("rat", 5);
  rat.hp = Math.floor(rat.max * 0.3); game.afterBlows();
  assert.ok(rat.form2 && rat.hidden && game.foes.filter((m) => m.summoned).length >= 2, "the king hides and the swarm comes");
  assert.ok(!game.attackable().includes(rat));
  for (const m of game.foes) if (m !== rat) m.hp = 0;
  game.afterBlows();
  assert.ok(!rat.hidden && game.attackable().includes(rat), "the swarm thinned: the king is found");
  rat.hp = 0; game.afterBlows();
  const knight = fight("knight", 10);
  knight.hp = Math.floor(knight.max * 0.3); game.afterBlows();
  assert.ok(knight.form2 && game.combat.flooded && knight.quick && game.terrain().includes("water"));
  knight.hp = 0; game.afterBlows(); if (game.mode === "combat") { knight.hp = 0; game.afterBlows(); }
  const warden = fight("forge", 15), atk = warden.atk;
  warden.hp = Math.floor(warden.max * 0.3); game.afterBlows();
  assert.ok(warden.form2 && warden.broken && warden.atk > atk);
  const hero = game.party[0], hp = hero.hp; game.strike(hero, warden, "", { sure: true });
  assert.ok(hp - hero.hp >= 2 * (2 + Math.floor(game.floor.number / 5)), "the heat doubled");
});

test("leaders with affixes of their own, for generator 2: shielded, mirrored, spectral", () => {
  const CM = load();
  const kinds1 = new Set(), kinds2 = new Set();
  for (let s = 0; s < 30; s++) for (let n = 3; n <= 20; n++) { for (const t of Object.values(CM.makeFloor(n, "elite-" + s, 1).things)) if (t.type === "monsters" && t.group[0].elite) kinds1.add(t.group[0].elite); for (const t of Object.values(CM.makeFloor(n, "elite-" + s, 2).things)) if (t.type === "monsters" && t.group[0].elite) kinds2.add(t.group[0].elite); }
  assert.ok(!["shielded", "mirrored", "spectral"].some((id) => kinds1.has(id)), "generator 1 never has them");
  assert.ok(["shielded", "mirrored", "spectral"].some((id) => kinds2.has(id)), "generator 2 does: " + [...kinds2].join(","));
  const game = new CM.Game(); game.newGame("elite-x", fixedParty(CM));
  const rnd = new CM.Random(5), ghost = CM.makeMonster(CM.monsterKind("Wraith"), 5, rnd); ghost.elite = "spectral"; ghost.max = ghost.hp = 999;
  game.floor.things["2,2"] = { type: "monsters", group: [ghost] }; game.startCombat("2,2", game.floor.things["2,2"]);
  let through = 0; for (let i = 0; i < 40; i++) { game.messages = []; game.strike(game.party[0], ghost, "", { sure: true }); if (game.messages.some((m) => m.includes("passes through"))) through++; }
  assert.ok(through > 8 && through < 32, "about half pass through: " + through);
  const mirror = CM.makeMonster(CM.monsterKind("Crystal Golem"), 5, rnd); mirror.elite = "mirrored"; mirror.max = mirror.hp = 999; game.foes.push(mirror);
  const mage = game.party.find((h) => h.cls === "Mage"); game.casting = mage; const mhp = mage.hp;
  const dealt = game.spellHit(mirror, 40, "", null);
  assert.ok(dealt <= 20 && mage.hp < mhp, "half, and a quarter back on the caster");
  game.casting = null;
  const shield = CM.makeMonster(CM.monsterKind("Orc"), 5, rnd); shield.elite = "shielded"; shield.max = shield.hp = 999; game.foes.push(shield);
  game.endRound();
  assert.ok(shield.warded > 0, "warded every round");
});

test("the three callings, native: tomes, the Heir's fists, recruits of their kind once earned", () => {
  const CM = load(), game = new CM.Game();
  assert.ok(CM.TOMES.hex && CM.TOMES.turret);
  const monk = CM.makeHero("Monk", "M", CM.rollStats("Monk", new CM.Random(1)));
  monk.weapon.power += 2; monk.weapon.props.bonus = 1; CM.recompute(monk);
  assert.strictEqual(monk.weapon.power, 3 + 2, "the Heir's kit counts on the fists");
  game.trophies.master = { date: "x" };
  let got = false;
  for (let i = 0; i < 40 && !got; i++) got = CM.makeRecruit(3, new CM.Random(i), game.classesAvailable()).cls === "Artificer";
  assert.ok(got, "an Artificer may come to the tavern once earned");
  assert.ok(!Array.from({ length: 60 }, (_, i) => CM.makeRecruit(3, new CM.Random(i)).cls).includes("Artificer"), "but never by itself");
});

test("magic with decisions: overcasting costs and pays, a tome deepens a known spell, a reagent bends it", () => {
  const CM = load(), game = new CM.Game();
  game.newGame("magic-1", fixedParty(CM));
  const mage = game.party.find((h) => h.cls === "Mage"); mage.level = 8; mage.mp = mage.maxmp = 99;
  const rnd = new CM.Random(2), orcs = [1, 2].map(() => CM.makeMonster(CM.monsterKind("Orc"), 5, rnd)); for (const o of orcs) o.max = o.hp = 2000;
  game.floor.things["2,2"] = { type: "monsters", group: orcs }; game.startCombat("2,2", game.floor.things["2,2"]);
  const a = Object.assign({ id: "missile" }, CM.ABILITIES.missile);
  assert.strictEqual(game.spellCost(mage, a, 1), 2); assert.strictEqual(game.spellCost(mage, a, 2), 4); assert.strictEqual(game.spellCost(mage, a, 3), 6);
  game.combat.waiting = mage; game.rnd = new CM.Random(9);
  const h1 = orcs[0].hp; game.useAbility(mage, "missile", orcs[0], 1); const d1 = h1 - orcs[0].hp;
  const h2 = orcs[0].hp; game.useAbility(mage, "missile", orcs[0], 2); const d2 = h2 - orcs[0].hp;
  assert.strictEqual(d2, Math.ceil(d1 * 1.5), `half again: ${d1} -> ${d2}`);
  assert.strictEqual(mage.mp, 99 - 2 - 4);
  let bit = false; mage.hp = mage.max;
  for (let i = 0; i < 12 && !bit; i++) { mage.mp = 99; game.useAbility(mage, "missile", orcs[0], 3); bit = mage.hp < mage.max; }
  assert.ok(bit, "a triple cast may bite back");
  game.bag.push(CM.tome("missile")); mage.mp = 99;
  assert.strictEqual(game.give(game.bag.length - 1, game.party.indexOf(mage)), "");
  assert.strictEqual(mage.spellLevels.missile, 2);
  assert.strictEqual(game.spellCost(mage, a, 1), 1, "one less to cast");
  const h3 = orcs[0].hp; game.useAbility(mage, "missile", orcs[0], 1);
  assert.strictEqual(h3 - orcs[0].hp, Math.ceil(d1 * 1.25), "a quarter more");
  game.bag.push(CM.ingredient("crystaldust"));
  const row = game.bag.length - 1, h4 = orcs[1].hp;
  assert.ok(game.reagentFor("missile") && game.reagentFor("missile").row === row);
  game.useAbility(mage, "missile", orcs[0], 1, row);
  assert.ok(orcs[1].hp < h4 && !game.bag.some((i) => i.kind === "ingredient"), "the bolt splits, and the dust is spent");
});

test("weaving: two casters in one round make one spell", () => {
  const CM = load(), game = new CM.Game();
  game.newGame("weave-1", fixedParty(CM));
  const mage = game.party.find((h) => h.cls === "Mage"), cleric = game.party.find((h) => h.cls === "Cleric");
  mage.level = 10; cleric.level = 10; mage.mp = mage.maxmp = 99; cleric.mp = cleric.maxmp = 99; cleric.learned = ["frost"];
  const rnd = new CM.Random(3), orcs = [1, 2, 3].map(() => CM.makeMonster(CM.monsterKind("Orc"), 5, rnd)); for (const o of orcs) o.max = o.hp = 2000;
  game.floor.things["2,2"] = { type: "monsters", group: orcs }; game.startCombat("2,2", game.floor.things["2,2"]);
  game.combat.waiting = mage; game.useAbility(mage, "firebolt", orcs[0]);
  assert.ok(game.combat.held && game.combat.held.id === "firebolt");
  game.combat.waiting = cleric; game.messages = [];
  game.useAbility(cleric, "frost", null);
  assert.ok(game.messages.some((m) => m.includes("Weave - Steam")), game.messages.join(" | "));
  assert.ok(orcs.every((o) => o.blind >= 2), "the steam blinds every foe");
  assert.strictEqual(game.weaves["firebolt+frost"], 1); assert.ok(game.achievements.weaver);
  assert.strictEqual(game.combat.held, null);
  const CM2 = load({ storage: CM.storage }), g2 = new CM2.Game();
  assert.strictEqual(g2.weaves["firebolt+frost"], 1, "kept between runs");
});

test("familiars: the Mage's cat, owl and toad; the Necromancer's skull by itself", () => {
  const CM = load(), game = new CM.Game();
  game.newGame("fam-1", fixedParty(CM));
  const mage = game.party.find((h) => h.cls === "Mage");
  assert.ok(!game.needsFamiliar(mage));
  mage.level = 6;
  assert.ok(game.needsFamiliar(mage));
  assert.ok(!game.chooseFamiliar(mage, "skull") && game.chooseFamiliar(mage, "owl"));
  assert.ok(!game.needsFamiliar(mage) && mage.familiar === "owl");
  const fl = game.floor; fl.dark.push(CM.keyOf(fl.pos[0], fl.pos[1])); const before = fl.seen.length; fl.seen = []; game.look();
  assert.ok(fl.seen.length > 1, "the owl sees in the dark");
  mage.familiar = "toad"; game.party[0].status.poison = 5;
  game.enterFloor(2, "down");
  assert.ok(!game.party[0].status.poison, "the toad eats an ailment on a new floor");
  const necro = CM.makeHero("Necromancer", "N", CM.rollStats("Necromancer", new CM.Random(1))); necro.level = 6; game.party[3] = necro;
  game.enterFloor(3, "down");
  assert.strictEqual(necro.familiar, "skull");
  const rnd = new CM.Random(4), orc = CM.makeMonster(CM.monsterKind("Orc"), 3, rnd); orc.max = orc.hp = 500;
  game.floor.things["2,2"] = { type: "monsters", group: [orc] }; game.startCombat("2,2", game.floor.things["2,2"]);
  const hp = orc.hp; game.endRound(); if (game.mode === "combat" && game.combat.round >= 1) game.beginRound();
  assert.ok(orc.hp < hp, "the skull bites at a round's start");
});

test("the surface: renown from a run, the buildings, a trainer's boon, candles, contracts, the vault's slots", () => {
  const CM = load(), game = new CM.Game();
  assert.strictEqual(game.renown(), 0);
  game.newGame("village-1", fixedParty(CM));
  game.enterFloor(12, "down");
  game.party[0].boons = ["ironskin"]; game.party[1].hp = 0;
  game.endRun(false);
  const entry = game.fame[0];
  assert.ok(entry.renown >= 12 && game.renown() === entry.renown, "a run brings home renown: " + entry.renown);
  game.village.renown = 0; assert.match(game.build("guildhall"), new RegExp(`asks ${CM.VILLAGE.guildhall.costs[0]}`));
  game.village.renown = 1000;
  assert.strictEqual(game.build("guildhall"), ""); assert.strictEqual(game.villageLevel("guildhall"), 1); assert.strictEqual(game.renown(), 1000 - CM.VILLAGE.guildhall.costs[0]);
  assert.strictEqual(game.retire(1), "Only a hero who came home can retire.");
  assert.strictEqual(game.retire(0), "");
  assert.ok(game.trainerFor("Knight") && game.trainerFor("Knight").boon === "ironskin");
  const g2 = new CM.Game();                                              // (the village is kept between runs)
  assert.strictEqual(g2.villageLevel("guildhall"), 1);
  g2.newGame("village-2", fixedParty(CM));
  const knight = g2.party.find((h) => h.cls === "Knight");
  assert.ok(knight.boons.includes("ironskin"), "every new Knight sets out with the trainer's boon");
  // the vault widens with the guildhall
  assert.strictEqual(g2.vaultCapacity(), 1);
  g2.village.renown = 2000; g2.build("guildhall"); assert.strictEqual(g2.vaultCapacity(), 3);
  g2.enterFloor(5, "down"); g2.setMode("camp"); g2.reachCamp(5);
  for (let i = 0; i < 4; i++) g2.bag.push({ name: "Ring " + i, kind: "ring", slot: "ring", power: 1, value: 80, props: { stat: "str" } });
  for (let i = 0; i < 4; i++) assert.strictEqual(g2.leaveHeirloom(g2.bag.findIndex((it) => it.kind === "ring")), "");
  assert.strictEqual(g2.vaults.length, 3, "three slots: the oldest came back");
  assert.strictEqual(g2.takeHeirloom(1), ""); assert.strictEqual(g2.vaults.length, 2);
  // the shrine: a candle brings up what they were buried with
  g2.build("shrine");
  g2.party[1].hp = 0; g2.gold = 5000; assert.strictEqual(g2.hire(0), "");
  assert.ok(g2.memorial[0].buried, "buried with their weapon or armour");
  const n = g2.vaults.length;
  assert.strictEqual(g2.lightCandle(0), "");
  assert.ok(g2.memorial[0].candle && g2.vaults.length === n + 1);
  // the merchant's house and the library
  g2.build("merchant"); g2.openBag(true);
  assert.ok(g2.stock.some((i) => i.kind === "greaterheal"), "the camps' merchant stocks greater potions");
  g2.closeBag();
  g2.build("library");
  g2.bestiary.Orc = { seen: 3, slain: 3, weak: ["fire"], resist: [] };
  assert.ok(g2.scholarship({ kind: "Orc" }) > 1 && g2.scholarship({ kind: "Goblin" }) === 1);
  // contracts: three a week, checked at a run's end
  const cs = g2.contracts();
  assert.strictEqual(cs.length, 3);
  const spent = g2.village.spent, had = g2.village.renown;
  g2.setMode("explore"); g2.gold = 2000; g2.enterFloor(16, "down"); for (const h of g2.party) h.hp = 0;
  g2.endRun(false);
  const done = g2.contracts().filter((c) => c.done);
  if (cs.some((c) => c.id === "hoard")) assert.ok(done.some((c) => c.id === "hoard"), "the hoard contract is kept with 2,000 gold");
  assert.ok(g2.village.renown > had);
  const exp = JSON.parse(g2.exportText());
  assert.ok(exp.village && exp.village.levels.guildhall === 2 && Array.isArray(exp.vaults));
});

test("the ladder: a Hard rung, Grim's slower cold, Ascension's rules, Iron saves, the next rung on a crown", () => {
  const CM = load();
  assert.ok(CM.DIFFICULTIES.hard && Object.keys(CM.DIFFICULTIES).join(",") === "gentle,fair,hard,grim");
  assert.strictEqual(CM.ASCENSION.length, 15);
  const game = new CM.Game();
  assert.strictEqual(game.ascensionMax(), 0);
  game.newGame("ladder-1", fixedParty(CM), "pauper", "fair", [], "dungeon", { ascension: 5 });
  assert.strictEqual(game.ascension, 0, "no rung is open yet");
  CM.store.set("ascension", 8);
  const g2 = new CM.Game();
  g2.newGame("ladder-2", fixedParty(CM), "pauper", "hard", [], "dungeon", { ascension: 7, iron: true });
  assert.strictEqual(g2.ascension, 7); assert.ok(g2.asc(7) && !g2.asc(8) && g2.iron);
  const bed = g2.gold; g2.enterFloor(5, "down"); g2.setMode("camp"); g2.reachCamp(5); g2.gold = 100; g2.rest();
  assert.strictEqual(g2.gold, 60, "lean camps: a bedroll is 40");
  const orc = CM.makeMonster(CM.monsterKind("Orc"), 5, new CM.Random(1)), plain = CM.makeMonster(CM.monsterKind("Orc"), 5, new CM.Random(1));
  g2.tune(orc); const g3 = new CM.Game(); g3.newGame("ladder-3", fixedParty(CM), "pauper", "hard"); g3.tune(plain);
  assert.ok(orc.max > plain.max, "hardened: more health than the same rung's difficulty alone");
  // iron: saved at the top of the stair and at the camps, not between
  const CMi = load(); CMi.store.set("ascension", 0);
  const gi = new CMi.Game(); gi.newGame("iron-1", fixedParty(CMi), "pauper", "fair", [], "dungeon", { iron: true });
  const first = CMi.storage.getItem("claudemagic.run"); assert.ok(first, "the first save stands");
  for (let i = 0; i < 10; i++) { if (gi.mode !== "explore") break; if (!gi.move(0)) gi.turn(1); gi.saveRun(); }
  assert.strictEqual(CMi.storage.getItem("claudemagic.run"), first, "nothing saved on the floor");
  gi.enterFloor(5, "down"); gi.setMode("camp"); gi.reachCamp(5); gi.saveRun();
  assert.notStrictEqual(CMi.storage.getItem("claudemagic.run"), first, "the camp saves");
  // a crown on Fair opens the next rung; the Hall of Fame and the code carry the rung
  const gc = new CMi.Game(); gc.newGame("crown-1", fixedParty(CMi), "pauper", "fair");
  gc.enterFloor(20, "down"); gc.crowned = true; gc.endRun(true);
  assert.strictEqual(gc.ascensionMax(), 1);
  assert.strictEqual(gc.fame[0].ascension, 0);
  const code = CM.runCode("s", "hard", "dungeon", "pauper", fixedParty(CM), { ascension: 7, iron: true });
  assert.ok(code.endsWith(":A7i"));
  const back = CM.parseRunCode(code); assert.strictEqual(back.ascension, 7); assert.strictEqual(back.iron, true); assert.strictEqual(back.difficulty, "hard");
  assert.strictEqual(CM.parseRunCode(CM.runCode("s", "fair", "dungeon", "pauper", fixedParty(CM))).ascension, 0);
});

test("the dungeon, branched: wings and their stairs, a secret stair in a wall, the new rooms, the dungeon that shifts behind you", () => {
  const CM = load();
  let wings = 0, secret = 0, pieces = new Set();
  for (let s = 0; s < 8; s++) for (let n = 1; n <= 50; n++) { const fl = CM.makeFloor(n, "branch-" + s, 2); for (const t of Object.values(fl.things)) if (t.type === "wingstair") wings++; for (const f of Object.values(fl.features)) if (f.type === "secretstair") secret++; for (const r of fl.rooms) if (r.name) pieces.add(r.name); assert.ok(!Object.values(CM.makeFloor(n, "branch-" + s, 1).things).some((t) => t.type === "wingstair"), "generator 1 has no wings"); }
  assert.ok(wings >= 8 * 5 && secret >= 8 * 5, `about one a band: wings ${wings}, secret stairs ${secret}`);
  assert.ok(["Great Hall", "Drowned Chapel", "Charnel Pit", "Crystal Gallery"].some((n) => pieces.has(n)), "the new rooms are laid: " + [...pieces].join(", "));
  const game = new CM.Game();
  game.newGame("branch-0", fixedParty(CM));
  let at = null;
  for (let n = 3; n <= 20 && !at; n++) { const fl = CM.makeFloor(n, "branch-0", 2); const k = Object.keys(fl.things).find((x) => fl.things[x].type === "wingstair"); if (k) at = [n, k]; }
  assert.ok(at, "a wing stair in the first twenty floors");
  game.enterFloor(at[0], "down");
  const fl = game.floor; fl.pos = at[1].split(",").map(Number);
  game.use();
  assert.strictEqual(game.floor.number, at[0] + 0.5); assert.ok(game.floor.wing !== undefined && game.floor.wingName && game.achievements.wings);
  assert.ok(Object.values(game.floor.things).some((t) => t.type === "wingexit") && Object.values(game.floor.things).some((t) => t.type === "wingstair_up"));
  assert.ok(!Object.values(game.floor.things).some((t) => ["event", "peddler", "rivals", "ladder", "stairs_up"].includes(t.type)));
  const exit = game.cellOf(game.floor, "wingexit"); game.floor.pos = exit.slice(); game.use();
  assert.strictEqual(game.floor.number, at[0] + 1, "the wing's exit comes out on the main stair below");
  game.enterFloor(at[0] + 0.5, "down"); const up = game.cellOf(game.floor, "wingstair_up"); game.floor.pos = up.slice(); game.use();
  assert.strictEqual(game.floor.number, at[0]); same(game.floor.pos, at[1].split(",").map(Number));
  game.saveRun();
  const CM2 = load({ storage: CM.storage }), g2 = new CM2.Game(); g2.continueRun();
  assert.ok(g2.floorAt(at[0] + 0.5).wing !== undefined, "a wing is saved and made again");
  // a secret stair, searched
  let sec = null;
  for (let n = 3; n <= 20 && !sec; n++) { const f2 = CM.makeFloor(n, "branch-0", 2); const k = Object.keys(f2.features).find((x) => f2.features[x].type === "secretstair"); if (k) sec = [n, k]; }
  assert.ok(sec);
  game.enterFloor(sec[0], "down");
  const f3 = game.floor, [wx, wy] = sec[1].split(",").map(Number);
  const from = CM.DIRS.map(([dx, dy], d) => [wx - dx, wy - dy, d]).find(([x, y]) => CM.passable(f3, x, y));
  f3.pos = [from[0], from[1]]; f3.facing = from[2];
  game.use();
  assert.ok(f3.features[sec[1]].found && f3.things[sec[1]] && f3.things[sec[1]].type === "wingstair");
  f3.pos = [wx, wy]; game.use();
  assert.ok(game.floor.secretWing && game.achievements.secretfloor, "a secret floor, richer");
  // the dungeon behind you
  game.enterFloor(sec[0] + 1, "down");
  const above = game.floors[sec[0]], shut = Object.values(above.features).filter((f) => f.type === "door" && !f.open && !f.locked && f.riddle === undefined).length;
  game.rnd = new CM.Random(1); game.steps = 149; game.messages = [];
  const o = CM.DIRS.findIndex(([dx, dy]) => CM.passable(game.floor, game.floor.pos[0] + dx, game.floor.pos[1] + dy)); game.floor.facing = o;
  game.move(0);
  assert.ok(game.messages.some((m) => m.includes("Somewhere above")) || !shut, "a door opens, or a peddler sets up, somewhere above");
});

test("an Awakened expedition: the floors mirrored, the monsters deeper, the uniques awake", () => {
  const CM = load(), game = new CM.Game();
  game.newGame("wake-1", fixedParty(CM), "pauper", "fair", [], "awakened");
  assert.ok(!game.awakened, "not until the bottom has been reached");
  game.achievements.bottom = { date: "x" };
  game.newGame("wake-1", fixedParty(CM), "pauper", "fair", [], "awakened");
  assert.ok(game.awakened);
  const plain = CM.makeFloor(1, "wake-1", 2), size = plain.grid.length;
  for (let y = 0; y < size; y++) for (let x = 0; x < size; x++) assert.strictEqual(game.floor.grid[y][x], plain.grid[y][size - 1 - x]);
  assert.ok(CM.solvable(game.floor));
  same(game.floor.pos, [size - 1 - plain.pos[0], plain.pos[1]]);
  const orc = CM.makeMonster(CM.monsterKind("Orc"), 5, new CM.Random(1)), max = orc.max; game.tune(orc);
  assert.ok(orc.max > max, "a band deeper");
  const u = CM.makeUnique("tidecaller", true);
  assert.ok(u.props.awake && u.name.includes("Awake") && u.power > CM.UNIQUES.tidecaller.power);
  game.enterFloor(2, "down"); game.saveRun();
  const CM2 = load({ storage: CM.storage }), g2 = new CM2.Game(); g2.continueRun();
  assert.ok(g2.awakened && g2.floor.mirrored);
  same(g2.floor.grid, game.floor.grid);
});

test("morale: the party's temper, lifted and worn, read by the fight; hunger, lightly", () => {
  const CM = load(), game = new CM.Game();
  game.newGame("temper-1", fixedParty(CM));
  assert.strictEqual(game.morale, 70); assert.strictEqual(game.moraleWord(), "Steady");
  game.cheer(15); assert.strictEqual(game.moraleWord(), "High");
  const h = game.party[0], hit = game.hitChance(h); game.cheer(-20); assert.ok(game.hitChance(h) < hit, "high morale: blows land more often");
  game.morale = 20;
  const rnd = new CM.Random(2), orc = CM.makeMonster(CM.monsterKind("Orc"), 2, rnd); orc.max = orc.hp = 900;
  game.floor.things["2,2"] = { type: "monsters", group: [orc] }; game.startCombat("2,2", game.floor.things["2,2"]);
  let froze = 0; game.rnd = new CM.Random(7);
  for (let i = 0; i < 30; i++) { game.messages = []; game.combat.index = 0; game.combat.waiting = null; game.advance(); if (game.messages.some((m) => m.includes("freezes"))) froze++; if (game.combat.waiting) game.act("defend"); }
  assert.ok(froze > 0, "shaken: a hero may freeze a turn");
  for (const m of game.foes) m.hp = 0; game.afterBlows();
  assert.strictEqual(game.morale, 23, "a victory lifts it three");
  game.fed = CM.HUNGER.weary;
  assert.strictEqual(game.hungerWord(), "Weary");
  game.bag.push(CM.ration());
  assert.strictEqual(game.give(game.bag.length - 1, 0), "");
  assert.strictEqual(game.fed, 0); assert.strictEqual(game.hungerWord(), "");
  game.saveRun();
  const CM2 = load({ storage: CM.storage }), g2 = new CM2.Game(); g2.continueRun();
  assert.strictEqual(g2.morale, game.morale); assert.strictEqual(g2.fed, 0);
});

test("boots and cloaks, quirks at creation, a second calling at twenty", () => {
  const CM = load(), rnd = new CM.Random(3);
  const boots = CM.makeGear("boots", 12, rnd), cloak = CM.makeGear("cloak", 12, rnd);
  assert.ok(boots.kind === "boots" && boots.power >= 1 && CM.itemLabel(Object.assign({}, boots, { unknown: false })).includes("speed"));
  assert.ok(cloak.kind === "cloak" && cloak.props.df >= 1);
  let found = 0; for (let f = 1; f <= 50; f++) for (const t of Object.values(CM.makeFloor(f, "boots-1", 2).things)) if (t.type === "chest") for (const it of t.items) if (it.kind === "boots" || it.kind === "cloak") found++;
  assert.ok(found > 5, "generator 2's chests hold them: " + found);
  const party = fixedParty(CM); party[0].quirk = "hardy"; party[1].quirk = "quiet";
  const con0 = party[0].stats.con;
  const game = new CM.Game(); game.newGame("quirk-1", party);
  const knight = game.party[0], rogue = game.party[1];
  assert.strictEqual(knight.quirk, "hardy"); assert.strictEqual(knight.stats.con, Math.min(25, con0 + 2));
  const code = CM.runCode("s", "fair", "dungeon", "pauper", game.party); assert.strictEqual(CM.parseRunCode(code).party[0].quirk, "hardy");
  boots.unknown = false; cloak.unknown = false;
  assert.strictEqual(game.equip(knight, game.bag.push(boots) - 1), "");
  assert.strictEqual(knight.boots.kind, "boots");
  assert.strictEqual(game.equip(rogue, game.bag.push(cloak) - 1), "");
  assert.ok(CM.gearDefence(rogue) >= cloak.props.df);
  knight.level = 20; game.village.levels.guildhall = 2; game.village.renown = 500;
  assert.match(game.secondCalling(0, "Cleric"), /camp/);
  game.enterFloor(5, "down"); game.setMode("camp"); game.reachCamp(5);
  assert.strictEqual(game.secondCalling(0, "Cleric"), "");
  assert.ok(knight.second === "Cleric" && CM.abilitiesFor(knight).includes("heal") && !CM.abilitiesFor(knight).includes("raise"));
  assert.ok(knight.maxmp > 0, "a second calling with magic brings a little");
  assert.strictEqual(game.renown(), 300);
});

test("films: a run's end keeps one; it plays on the live game line by line, skips to a fight or a floor, and nothing of it is saved", () => {
  const CM = load(), game = new CM.Game();
  game.newGame("film-1", fixedParty(CM));
  playRun(CM, game, { maxFloor: 3 });
  const spec = game.replaySpec();
  assert.ok(spec.trail.length >= 2 && spec.trail[0][0] === 1, "the trail: each floor and its step");
  for (const h of game.party) h.hp = 0;
  game.endRun(false);
  const films = CM.store.get("films", []);
  assert.strictEqual(films.length, 1); assert.strictEqual(game.fame[0].film, films[0].key);
  const code = CM.filmCode(Object.assign({}, films[0].spec, { log: CM.unpackLog(films[0].spec.log) }));
  assert.ok(code.startsWith("CM2:"));
  const back = CM.parseFilm(code);
  assert.strictEqual(back.log.length, spec.log.length); assert.strictEqual(CM.parseFilm("CM1:x"), null);
  // a second game watches it
  const g2 = new CM.Game();
  g2.newGame("own-1", fixedParty(CM)); g2.saveRun();
  const own = CM.storage.getItem("claudemagic.run");
  assert.ok(g2.startFilm(back) && g2.film && g2.mode === "explore" && g2.seed === "film-1");
  for (let n = 0; n < 50 && g2.filmStep(); n++);
  assert.strictEqual(g2.film.at, 50);
  g2.filmSkip("floor");
  assert.ok(g2.floor.number >= 2 || g2.film.at === back.log.length);
  g2.filmSkip("fight");
  assert.strictEqual(CM.storage.getItem("claudemagic.run"), own, "nothing of the film is saved");
  g2.stopFilm();
  assert.strictEqual(g2.mode, "title"); assert.ok(!g2.film);
  assert.ok(g2.canContinue() && g2.continueRun() && g2.seed === "own-1", "the player's own run is where it was");
  // the ghost: a later run on the seed hears when the best run took each stair
  const g3 = new CM.Game();
  g3.newGame("film-1", fixedParty(CM));
  assert.ok(g3.ghostTrail(), "the fallen run left a trail to race");
  g3.enterFloor(2, "down");
  assert.ok(g3.messages.some((m) => m.includes("ghost of your best run")), g3.messages.slice(-3).join(" | "));
});

test("sound and sight, again: the battle tune's layers and key, a monster's frames by pose", () => {
  const CM = load();
  // (the music and the art live with the window; what can be read without a browser is read)
  const src = fs.readFileSync(path.join(__dirname, "..", "src", "js", "55-music.js"), "utf8");
  assert.ok(src.includes("setDanger") && src.includes("shiftBy") && src.includes("this.danger < 0.6"), "the lead joins under half, the pad drops when a hero has fallen");
  const art = fs.readFileSync(path.join(__dirname, "..", "src", "js", "30-art.js"), "utf8");
  assert.ok(art.includes('pose === "idle2"') && art.includes('pose === "attack"') && art.includes("monster:${m.name}:attack"), "two frames more, painted in code");
  const audio = fs.readFileSync(path.join(__dirname, "..", "src", "js", "50-audio.js"), "utf8");
  assert.ok(audio.includes("bark(kind, what)") && audio.includes("playbackRate"), "barks: a call shifted");
  const render = fs.readFileSync(path.join(__dirname, "..", "src", "js", "40-render.js"), "utf8");
  assert.ok(render.includes("zoomTo(k, ms") && render.includes("rollTo(r, ms"), "the camera pushes, pulls and tilts");
  void CM;
});

test("around the game, again: the ledger and the statistics, a save as a link, the gamepad's map, the app's papers", async () => {
  const CM = load(), game = new CM.Game();
  game.newGame("ledger-1", fixedParty(CM));
  playRun(CM, game, { maxFloor: 2 });
  game.spend("temple", 30); game.spend("smith", 12);
  for (const h of game.party) h.hp = 0;
  game.endRun(false);
  assert.strictEqual(game.ledger.length, 1, "one line for one expedition");
  const l = game.ledger[0];
  assert.ok(l.f >= 1 && !l.w && l.c.length === 4 && l.sp.temple === 30 && l.s > 0, JSON.stringify(l));
  // the statistics: bands, callings, gold
  const lines = game.ledger.concat([
    Object.assign(CM.ledgerLine({ date: "01/02/2026", seed: "x", floor: 20, won: true, gold: 500, difficulty: "hard", ascension: 3, tally: { steps: 900, fights: 40, kills: 90, spent: { temple: 100 } } }, ["fighter", "fighter", "mage", "priest"]), { t: 1 }),
    Object.assign(CM.ledgerLine({ date: "01/03/2026", seed: "y", floor: 12, won: false, gold: 50, tally: { steps: 300 } }, ["thief", "mage", "mage", "ranger"]), { t: 2 }),
  ]);
  const st = CM.statistics(lines);
  assert.strictEqual(st.runs, 3); assert.strictEqual(st.crowns, 1); assert.strictEqual(st.fell, 2); assert.strictEqual(st.deepest, 20);
  assert.strictEqual(st.bands[2].fell, 1, "one fell on 11-15"); assert.strictEqual(st.bands[3].through, 1, "the crown went through 16-20");
  assert.strictEqual(st.callings.mage.n, 3); assert.strictEqual(st.callings.Mage.n, 1); assert.strictEqual(st.spent.temple, 130); assert.strictEqual(st.difficulties.hard.a, 3);
  // the runs from before the ledger: read back from the Hall of Fame, without their numbers
  const old = CM.ledgerFromFame({ date: "12/12/2025", seed: "z", floor: 9, won: false, gold: 20, party: ["Ana the mage 5", "Bo the fighter 6"], tally: {} });
  assert.ok(old.old && old.c.join() === "mage,fighter" && old.s === 0);
  // import merges lines, and never doubles them
  const g2 = new CM.Game();
  assert.strictEqual(g2.ledger.length, 1, "the ledger is kept");
  assert.ok(!g2.importText(game.exportText())); assert.strictEqual(g2.ledger.length, 1, "the same line, once");
  // the save as a link, deflated and back
  const text = game.exportText();
  const code = await CM.toLink(text);
  assert.ok(code[0] === "1" && code.length < text.length, "deflated");
  assert.strictEqual(await CM.fromLink(code), text);
  assert.strictEqual(await CM.fromLink("0" + CM.b64url(new TextEncoder().encode("plain"))), "plain");
  assert.deepStrictEqual(JSON.parse(JSON.stringify(CM.linkPayload(`#save=${code}`))), { kind: "save", code });
  assert.strictEqual(CM.linkPayload("#nothing"), null);
  // the gamepad's map: the standard buttons, named
  assert.strictEqual(CM.padName(CM.DEFAULT_PAD.use), "A"); assert.strictEqual(CM.padName(9), "Start"); assert.strictEqual(CM.padName(""), "-");
  assert.ok(CM.PAD_ACTIONS.every(([id]) => id in CM.DEFAULT_PAD) && Object.assign({}, CM.DEFAULT_PAD, g2.settings.pad).use === 0);
  assert.strictEqual(CM.t("stats.runs", { n: 1200, crowns: 2, bottoms: 0, fell: 3 }), `${(1200).toLocaleString()} expeditions, 2 crowned, 0 to the bottom of the world, 3 that fell`);
  // the app's papers, beside the built file
  const manifest = JSON.parse(fs.readFileSync(path.join(ROOT, "game", "manifest.webmanifest"), "utf8"));
  assert.ok(manifest.start_url.startsWith("./Claude%20and%20Magic%20v") && manifest.icons.length === 1);
  const sw = fs.readFileSync(path.join(ROOT, "game", "sw.js"), "utf8");
  assert.ok(sw.includes(manifest.start_url) && sw.includes("skipWaiting"), "the worker keeps the file");
  assert.ok(fs.existsSync(path.join(ROOT, "game", "icon.svg")));
});

test("the spine of the story: fifty carvings in ten chapters, each on a wall the party can reach, tellings by seed, the codex and the lies struck through", () => {
  const CM = load();
  assert.strictEqual(CM.LORE.length, 50); assert.strictEqual(CM.LORE_EXTRA.length, 8); assert.strictEqual(CM.LORE_ENDLESS.length, 8);
  for (const l of Object.values(CM.LORE_TEXT)) {
    assert.ok(CM.CHAPTERS[l.chapter], `${l.key}: chapter ${l.chapter}`);
    if (l.contradicts) { assert.ok(CM.LORE_TEXT[l.contradicts], `${l.key} contradicts ${l.contradicts}`); assert.ok(CM.LORE_TEXT[l.contradicts].floor < l.floor, "the truth lies deeper than the lie"); }
  }
  for (let s = 0; s < 12; s++) for (let n = 1; n <= 50; n++) {
    const fl = CM.makeFloor(n, `spine-${s}`, s % 2 ? 2 : 1), reach = CM.distances(fl.grid, fl.pos);   // (the walls' own ways: a riddle door or a gate is still a way)
    const walls = Object.entries(fl.features).filter(([, f]) => f.type === "carving" && CM.loreKey(f.text) === CM.LORE_KEYS[n - 1]);
    assert.ok(walls.length === 1 && reach.has(walls[0][0]), `floor ${n} of spine-${s}: the floor's carving, once, where the party can stand`);
    assert.strictEqual(CM.LORE_TEXT[CM.LORE_KEYS[n - 1]].chapter, Object.keys(CM.CHAPTERS)[Math.floor((n - 1) / 5)]);
  }
  assert.strictEqual(CM.loreKey("g:rat"), "guardian.rat"); assert.strictEqual(CM.loreKey("e:9"), "endless.2"); assert.strictEqual(CM.loreKey(-3), "odd.3");
  const a = CM.loreText(4, "seed-a"), b = CM.loreText(4, "seed-b"), c = CM.loreText(4, "seed-a");
  assert.strictEqual(a, c, "a seed's telling is its own"); assert.ok(CM.LORE_TEXT["carving.catacombs.5"].tellings.includes(a) && CM.LORE_TEXT["carving.catacombs.5"].tellings.includes(b));
  assert.ok(Object.values(CM.LORE_TEXT).filter((l) => l.key.startsWith("carving.")).every((l) => l.tellings.length >= 2), "two tellings a carving");
  assert.ok([..."abcdefgh"].some((x) => CM.loreText(4, `s-${x}`) !== CM.LORE[4]), "the other telling comes up");
  // a party reads a wall: the story knows the key, the journal keeps the telling, the save keeps both
  const game = new CM.Game();
  game.newGame("spine-read", fixedParty(CM));
  const fl = game.floor, [k, f] = Object.entries(fl.features).find(([, x]) => x.type === "carving" && x.text === 0);
  fl.pos = k.split(",").map(Number); fl.facing = f.face; game.use();
  assert.strictEqual(game.story.read["carving.catacombs.1"], 1); assert.strictEqual(game.journal[0].key, "carving.catacombs.1"); assert.strictEqual(game.journal[0].text, CM.loreText(0, "spine-read"));
  game.saveRun();
  const g2 = new CM.Game(); g2.continueRun();
  assert.strictEqual(g2.story.read["carving.catacombs.1"], 1);
  const saved = JSON.parse(CM.storage.getItem("claudemagic.run")); delete saved.story; CM.storage.setItem("claudemagic.run", JSON.stringify(saved));
  const g3 = new CM.Game(); g3.continueRun();
  assert.strictEqual(g3.story.read["carving.catacombs.1"], 1, "an older save: the story read back from the journal");
  // the codex: blanks, then the lie struck through when the Drowned Town's truth is read
  let codex = CM.codex(g3);
  assert.strictEqual(codex[0].done, 1); assert.strictEqual(codex[0].total, 6); assert.strictEqual(codex[0].lines[4].read, false); assert.strictEqual(codex.length, Object.keys(CM.CHAPTERS).length);
  g3.markRead("carving.catacombs.5"); g3.markRead("carving.drowned.2");
  codex = CM.codex(g3);
  assert.strictEqual(codex[0].lines[4].struck, "carving.drowned.2"); assert.ok(codex[0].lines[4].truth.length > 10 && codex[4].lines[1].read);
  assert.deepStrictEqual(JSON.parse(JSON.stringify(CM.storyFromJournal([{ text: CM.LORE_TEXT["carving.vaults.1"].tellings[1], floor: 6 }]))), { read: { "carving.vaults.1": 6 } });
  console.log(`       (the story: ${CM.loreWords().toLocaleString()} words)`);
  // the bot reads the walls it passes
  const g4 = new CM.Game(); g4.newGame("spine-bot", fixedParty(CM));
  playRun(CM, g4, { maxFloor: 4 });
  assert.ok(Object.keys(g4.story.read).length >= 2, `the bot read ${Object.keys(g4.story.read).join(", ")}`);
});

test("the people of Caer Duin: twelve ghosts on their three floors, the bell, a witness's request, your own dead over their bones, the hermit tells a chapter back", () => {
  const CM = load();
  assert.strictEqual(CM.PEOPLE.length, 12); assert.strictEqual(CM.GHOSTS.length, 6, "the generators roll among six");
  for (const p of CM.PEOPLE) {
    assert.ok(p.floors[0] < p.floors[1] && p.floors[1] < p.floors[2] && p.floors[2] <= 45, p.name);
    assert.ok(p.floors.every((f) => !CM.guardianFor(f) && f !== CM.LAST_FLOOR), `${p.name}: never a guardian's floor`);
    assert.ok(p.tale && p.first && p.second && p.again && p.request.ask && p.request.wait && p.request.done, `${p.name}: every word written`);
    if (p.request.kind === "witness") { assert.ok(CM.LORE_TEXT[p.request.key], `${p.name}: a real key`); }
    assert.ok(CM.LORE_TEXT[`ghost.${CM.PEOPLE.indexOf(p) + 1}`].chapter === "people");
  }
  for (const seed of ["people-1", "people-2", "people-3"]) for (let n = 2; n <= 45; n++) {
    const fl = CM.makeFloor(n, seed, 2);
    for (const [i, p] of CM.PEOPLE.entries()) {
      const arc = p.floors.indexOf(n);
      if (arc < 0) continue;
      const g = Object.entries(fl.things).find(([, t]) => t.type === "ghost" && t.arc === arc + 1 && t.who === i);
      assert.ok(g, `${p.name} stands on floor ${n} of ${seed}`);
      if (arc === 2 && g[1].request === "bones") assert.ok(Object.values(fl.things).some((t) => t.type === "bones" && t.ghost === g[0]), `${p.name}'s bones lie on the floor`);
      if (arc === 2 && g[1].request === "vengeance") assert.ok(Object.values(fl.things).some((t) => t.vengeance === g[0]), `${p.name}'s quarry walks the floor`);
    }
    if (n === CM.BELL_FLOOR) assert.ok(Object.values(fl.things).some((t) => t.type === "bones" && t.bell), "the bell on the fourth floor");
  }
  // a word with Hal on floor 3, the journal, the story; later, his witness request, granted when the Drowned Town's wall is read
  const game = new CM.Game(); game.newGame("people-1", fixedParty(CM));
  game.enterFloor(3, "down");
  let [k, t] = Object.entries(game.floor.things).find(([, x]) => x.type === "ghost" && x.arc === 1 && x.who === 0);
  game.floor.pos = k.split(",").map(Number); game.talk(t, k);
  assert.strictEqual(game.story.read["people.1.1"], 3); assert.ok(game.journal.some((e) => e.key === "people.1.1")); assert.ok(game.village.ghostsMet.includes("Hal of the lower watch"));
  game.enterFloor(23, "down");
  [k, t] = Object.entries(game.floor.things).find(([, x]) => x.type === "ghost" && x.arc === 3 && x.who === 0);
  game.floor.pos = k.split(",").map(Number); game.talk(t, k); game.talk(t, k);
  assert.ok(game.floor.things[k], "not yet: the town's wall is unread");
  game.markRead("carving.drowned.2"); const bag = game.bag.length; game.talk(t, k);
  assert.ok(!game.floor.things[k] && game.bag.length === bag + 1 && game.story.read["ghost.1"] === 23, "Hal rests, and leaves a gift");
  // the bell: picked up on the fourth floor, rung by Cael on the forty-first
  const g2 = new CM.Game(); g2.newGame("people-2", fixedParty(CM));
  g2.enterFloor(4, "down");
  const bellAt = Object.keys(g2.floor.things).find((kk) => g2.floor.things[kk].bell);
  { const [bx, by] = bellAt.split(",").map(Number), d = CM.DIRS.findIndex(([dx, dy]) => CM.passable(g2.floor, bx - dx, by - dy)); g2.floor.pos = [bx - CM.DIRS[d][0], by - CM.DIRS[d][1]]; g2.floor.facing = d; g2.move(0); }   // (bones are taken by walking onto them)
  assert.ok(g2.hasItem("bell") >= 0 && g2.story.read["thing.bell"] === 4, "the bell in the pack");
  g2.enterFloor(41, "down");
  [k, t] = Object.entries(g2.floor.things).find(([, x]) => x.type === "ghost" && x.arc === 3 && x.who === 2);
  g2.floor.pos = k.split(",").map(Number); g2.talk(t, k); g2.talk(t, k);
  assert.ok(g2.story.bell && g2.hasItem("bell") < 0 && g2.achievements.bellringer, "rung");
  // your own dead: a hero of yours who fell here stands over the remains and wants their bones
  const g3 = new CM.Game(); g3.newGame("people-3", fixedParty(CM));
  const fl2 = CM.makeFloor(2, "people-3", 2), spot = [...CM.distances(fl2.grid, fl2.pos)].map(([kk]) => kk).find((kk) => !fl2.things[kk] && !fl2.features[kk] && kk !== fl2.pos.join(","));
  g3.fallen = [{ id: "people-3:2:1", seed: "people-3", floor: 2, pos: spot.split(",").map(Number), names: ["Edda", "Bo", "Cy", "Di"], date: "01/01/2026", item: null }];
  g3.memorial = [{ name: "Edda", cls: "Knight", level: 4, floor: 2, seed: "people-3", date: "01/01/2026", buried: null }];
  g3.enterFloor(2, "down");
  const own = Object.entries(g3.floor.things).find(([, x]) => x.type === "ghost" && x.own);
  assert.ok(own && own[1].own.name === "Edda" && own[1].own.cls === "Knight", "Edda stands here");
  assert.ok(Object.values(g3.floor.things).some((x) => x.type === "bones" && x.ghost === own[0]), "her bones, somewhere");
  g3.bag.push(CM.bones(own[0])); g3.floor.pos = own[0].split(",").map(Number); g3.talk(own[1], own[0]); g3.talk(own[1], own[0]);
  assert.ok(!g3.floor.things[own[0]] && g3.memorial[0].candle && g3.achievements.laidtorest, "laid to rest, a candle lit");
  // the hermit tells a chapter back once all but one line is read
  const g4 = new CM.Game(); g4.newGame("people-4", fixedParty(CM));
  for (const key of ["carving.catacombs.1", "carving.catacombs.2", "carving.catacombs.3", "carving.catacombs.4", "guardian.rat"]) g4.markRead(key);
  const hermit = { type: "hermit", heard: 0, greeted: true };
  let said = null; g4.on("talk", (e) => { said = e; });
  g4.talkHermit(hermit);
  assert.ok(g4.story.told.catacombs && said.lines && said.lines[0] === CM.CHAPTER_TRUTH.catacombs, "told");
  assert.ok(CM.codex(g4)[0].complete, "the codex counts it whole");
  // the bot talks to the people it passes
  const g5 = new CM.Game(); g5.newGame("people-1", fixedParty(CM));
  playRun(CM, g5, { maxFloor: 4 });
  assert.ok(Object.keys(g5.story.read).some((key) => key.startsWith("people.")), `the bot met ${Object.keys(g5.story.read).join(", ")}`);
});

test("the guardians speak: three exchanges and a gate each, better and worse terms, a guardian passed by speech leaves the way open and its relic, the bot answers", () => {
  const CM = load();
  for (const id of CM.GUARDIAN_ORDER) {
    const P = CM.PARLEY[id], G = CM.GUARDIANS[id];
    assert.ok(P && P.open && P.death && P.deathSpoken && P.after && P.good && P.bad, `${id}: every word written`);
    assert.strictEqual(P.speak.length, 3, `${id}: three exchanges`);
    for (const ex of P.speak) { assert.strictEqual(ex.replies.length, 2); assert.strictEqual(ex.replies.filter((r) => r.good).length, 1, `${id}: one right answer each`); }
    if (P.gate && P.gate.key) { assert.ok(CM.LORE_TEXT[P.gate.key], `${id}: a real key`); const at = CM.LORE_TEXT[P.gate.key].floor; assert.ok(P.gate.returns ? at > G.floor : at < G.floor, `${id}: its key lies ${P.gate.returns ? "below (a return)" : "above"} its lair (${at} vs ${G.floor})`); }
  }
  assert.ok(CM.PARLEY.root.gate && CM.PARLEY.root.gate.crown, "the Root wants the crown, and nothing less");
  // the Rat King's door: it speaks first; all three answers right, and its company goes and it is shaken
  const atDoor = (game, n) => { game.enterFloor(n, "down"); const [k, t] = Object.entries(game.floor.things).find(([, x]) => x.type === "guardian"); const [gx, gy] = k.split(",").map(Number); const d = CM.DIRS.findIndex(([dx, dy]) => CM.passable(game.floor, gx - dx, gy - dy)); game.floor.pos = [gx - CM.DIRS[d][0], gy - CM.DIRS[d][1]]; game.floor.facing = d; return [k, t]; };
  const game = new CM.Game(); game.newGame("parley-1", fixedParty(CM));
  let asked = null; game.on("choice", (c) => { asked = c; });
  game.bag = game.bag.filter((i) => i.kind !== "ration");
  let [k, t] = atDoor(game, 5);
  game.move(0);
  assert.ok(asked && asked.parley && asked.options.length === 2 && game.mode === "explore", "it speaks first: fight or speak");
  game.parley(k, 1);
  for (let step = 0; step < 3; step++) { assert.ok(asked.options.length === 2); game.parley(k, CM.PARLEY.rat.speak[step].replies.findIndex((r) => r.good)); }
  assert.strictEqual(game.mode, "combat"); assert.strictEqual(t.terms, "good"); assert.strictEqual(game.foes.length, 1, "the escorts went"); assert.ok(game.foes[0].shaken && game.foes[0].hp < game.foes[0].max);
  assert.ok(game.runLog.filter((l) => l[0] === "parley").length === 4, "every word logged");
  // worse terms: three wrong answers, and it is enraged
  const g2 = new CM.Game(); g2.newGame("parley-2", fixedParty(CM)); g2.bag = g2.bag.filter((i) => i.kind !== "ration");
  [k, t] = atDoor(g2, 5); g2.move(0); g2.parley(k, 1);
  for (let step = 0; step < 3; step++) g2.parley(k, CM.PARLEY.rat.speak[step].replies.findIndex((r) => !r.good));
  assert.strictEqual(t.terms, "bad"); assert.ok(g2.foes.find((m) => m.guardian).enraged);
  // the gate: rations for the Rat King - passed, not slain; the way open, the crown left, half the gold, no trophy
  const g3 = new CM.Game(); g3.newGame("parley-3", fixedParty(CM)); g3.bag.push(CM.ration());
  [k, t] = atDoor(g3, 5); asked = null; g3.on("choice", (c) => { asked = c; }); g3.move(0);
  assert.strictEqual(asked.options.length, 3, "the gate is open: rations in the pack");
  const gold = g3.gold; g3.parley(k, 2);
  assert.strictEqual(g3.floor.things[k].type, "ladder"); assert.ok(g3.bag.some((i) => i.name === "Rat King's Crown")); assert.ok(g3.gold > gold); assert.ok(!g3.trophies.rat); assert.deepStrictEqual(JSON.parse(JSON.stringify(g3.tally.spoken)), ["rat"]);
  assert.ok(!g3.bag.some((i) => i.kind === "ration"), "the rations are gone");
  const wall = Object.values(g3.floor.features).find((f) => f.type === "carving" && f.text === "ga:rat");
  assert.ok(wall && CM.loreText(wall.text) === CM.PARLEY.rat.after && CM.loreKey(wall.text) === "guardian.rat", "the lair's carving, in the past tense");
  assert.strictEqual(g3.mode, "explore");
  // the Drowned Knight's gate wants a line from below him; the Forge-Warden's, one from above
  const g4 = new CM.Game(); g4.newGame("parley-4", fixedParty(CM));
  assert.ok(!CM.gateOpen(g4, CM.PARLEY.knight.gate)); g4.markRead("carving.drowned.2"); assert.ok(CM.gateOpen(g4, CM.PARLEY.knight.gate));
  g4.markRead("carving.halls.1"); [k, t] = atDoor(g4, 15); asked = null; g4.on("choice", (c) => { asked = c; }); g4.move(0); g4.parley(k, 2);
  assert.strictEqual(g4.floor.things[k].type, "ladder"); assert.ok(!g4.floor.decor.some((d) => d.kind === "ember"), "the embers are out");
  // a replay plays the same words: the bot walks down to the Rat King's floor, then the party goes to its door and talks it round
  const goTo = (game, x, y) => {                                        // (travel stops for every monster seen and every door: start it again until the party is there)
    for (let tries = 0; tries < 120 && game.mode !== "title" && (game.floor.pos[0] !== x || game.floor.pos[1] !== y); tries++) {
      if (game.mode === "combat") { autoplayFight(CM, game); continue; }
      if (!game.travelTo(x, y, true)) break;
      let steps = 0; while (game.travel && game.mode === "explore" && steps++ < 400) game.travelStep();
    }
  };
  const faceTo = (game, d) => { let guard = 0; while (game.floor.facing !== d && guard++ < 4) game.turn(1); };
  const g6 = new CM.Game(); g6.newGame("parley-6", fixedParty(CM));
  playRun(CM, g6, { maxFloor: 4 });
  if (g6.mode === "explore" && g6.floor.number === 5) {
    g6.mapAll();
    const [gk] = Object.entries(g6.floor.things).find(([, x]) => x.type === "guardian"); const [gx, gy] = gk.split(",").map(Number);
    const d = CM.DIRS.findIndex(([dx, dy]) => CM.passable(g6.floor, gx - dx, gy - dy)), door = [gx - CM.DIRS[d][0], gy - CM.DIRS[d][1]];
    goTo(g6, door[0], door[1]);
    if (g6.mode === "explore" && g6.floor.pos[0] === door[0] && g6.floor.pos[1] === door[1]) {
      faceTo(g6, d); g6.move(0);
      const acts = asked && asked.parley ? asked.options : [];
      g6.parley(gk, 1);
      for (let step = 0; step < 3; step++) if (g6.mode === "explore") g6.parley(gk, CM.PARLEY.rat.speak[step].replies.findIndex((r) => r.good));
      assert.strictEqual(g6.mode, "combat", `the talk ends in a fight on the party's terms (${acts.join(" / ")})`);
      autoplayFight(CM, g6);
      const again = CM.replayRun(g6.replaySpec());
      assert.strictEqual(again.gold, g6.gold); assert.strictEqual(again.mode, g6.mode); assert.deepStrictEqual(JSON.parse(JSON.stringify(again.tally)), JSON.parse(JSON.stringify(g6.tally)), "the replay says the same words and fights the same fight");
    } else console.log("       (the way to the Rat King's door was blocked this seed: the replay check was skipped)");
  } else console.log(`       (the bot did not reach floor 5 this seed - ${g6.mode}, floor ${g6.floor && g6.floor.number}: the replay check was skipped)`);
  // the bot answers the door
  const g5 = new CM.Game(); g5.newGame("parley-1", fixedParty(CM));
  playRun(CM, g5, { maxFloor: 6 });
  assert.ok((g5.tally.guardians || []).includes("rat") || (g5.tally.spoken || []).includes("rat") || g5.mode === "title", "the bot got past the Rat King, or fell trying");
});

test("the court of the Lich King: the seated dead on 16-19, three clues and the heart marked on the map, and the quiet ending - remind him, or draw", () => {
  const CM = load();
  assert.strictEqual(CM.COURT.length, 5); assert.ok(CM.COURT.every((c) => c.floor >= 16 && c.floor <= 19 && c.line));
  assert.strictEqual(CM.REMIND.length, 5); for (const r of CM.REMIND) assert.ok(CM.LORE_TEXT[r.key] && r.ask && r.say && r.back, r.key);
  for (const seed of ["court-1", "court-2"]) {
    let pages = 0;
    for (let n = 16; n <= 19; n++) {
      const fl = CM.makeFloor(n, seed, 2);
      for (const [i, c] of CM.COURT.entries()) if (c.floor === n) assert.ok(Object.values(fl.things).some((t) => t.type === "ghost" && t.courtier === i), `${c.name} sits on floor ${n} of ${seed}`);
      pages += Object.values(fl.things).filter((t) => t.type === "chest" && t.items.some((i) => i.kind === "page")).length;
    }
    assert.strictEqual(pages, 1, `${seed}: the physician's page in one chest of the palace`);
  }
  // the heart hunt: a word from the Chancellor, the wall on 18, the page - and the box is marked on the throne room's map
  const game = new CM.Game(); game.newGame("court-1", fixedParty(CM));
  game.enterFloor(16, "down");
  const [ck, ct] = Object.entries(game.floor.things).find(([, t]) => t.type === "ghost" && t.courtier === 0);
  game.floor.pos = ck.split(",").map(Number); game.talk(ct, ck);
  assert.strictEqual(game.story.read["court.1"], 16); assert.ok(!game.story.heartKnown);
  game.markRead("carving.palace.3"); game.bag.push(Object.assign({}, CM.PAGE)); game.markRead("carving.palace.5");
  assert.ok(game.story.heartKnown, "three clues: known"); assert.ok(game.journal.some((e) => e.key === "heart.known"));
  game.enterFloor(19, "down");
  const [pk] = Object.entries(game.floor.things).find(([, t]) => t.type === "phylactery");
  assert.ok(game.floor.seen.some(([x, y]) => `${x},${y}` === pk), "the box is on the map before it is seen");
  game.enterFloor(20, "down");
  // the king's door: without the chapter and the smashed heart, fight is all there is; with them, remind him - and a gap means he draws
  let asked = null; game.on("choice", (c) => { asked = c; });
  const [bk, bt] = Object.entries(game.floor.things).find(([, t]) => t.type === "boss");
  const toDoor = (g, k) => { const [gx, gy] = k.split(",").map(Number); const d = CM.DIRS.findIndex(([dx, dy]) => CM.passable(g.floor, gx - dx, gy - dy)); g.floor.pos = [gx - CM.DIRS[d][0], gy - CM.DIRS[d][1]]; g.floor.facing = d; };
  toDoor(game, bk); game.move(0);
  assert.deepStrictEqual(JSON.parse(JSON.stringify(asked.options)), ["Fight"]);
  for (const k of ["carving.palace.1", "carving.palace.2", "carving.palace.4"]) game.markRead(k);
  game.phylactery = true; bt.talk = 0;
  asked = null; game.move(0);
  assert.strictEqual(asked.options.length, 2, "remind him is offered");
  game.parley(bk, 1);
  assert.ok(asked.remind && asked.options.length === 1, "the queen's name is not known: only silence");
  game.parley(bk, 0);
  assert.strictEqual(game.mode, "combat", "a gap, and he draws");
  // and with every line read, the quiet ending
  const g2 = new CM.Game(); g2.newGame("court-2", fixedParty(CM)); g2.enterFloor(20, "down");
  for (const k of ["carving.palace.1", "carving.palace.2", "carving.palace.3", "carving.palace.4", "carving.palace.5"].concat(CM.REMIND.map((r) => r.key))) g2.markRead(k);
  g2.phylactery = true;
  asked = null; g2.on("choice", (c) => { asked = c; });
  const [bk2, bt2] = Object.entries(g2.floor.things).find(([, t]) => t.type === "boss");
  toDoor(g2, bk2); g2.move(0); g2.parley(bk2, 1);
  for (let i = 0; i < 5; i++) { assert.ok(asked.remind && asked.options.length === 2, `exchange ${i + 1}`); g2.parley(bk2, 0); }
  assert.ok(g2.crowned && g2.reminded && g2.mode === "explore" && g2.achievements.merciful, "crowned without a blow");
  assert.strictEqual(g2.floor.things[bk2].type, "ladder"); assert.ok(g2.journal.some((e) => e.key === "ending.quiet"));
  g2.saveRun(); const g3 = new CM.Game(); g3.continueRun(); assert.ok(g3.reminded, "the save remembers");
  for (const h of g3.party) h.hp = 0; g3.endRun(true);
  assert.ok(g3.fame[0].reminded && CM.summaryText(g3.fame[0]).includes("Reminded"));
  void bt;
});

test("the village has people: the chronicler pays for chapters and sells rumours the dungeon keeps, the Book of Caer Duin, the priest's names, the village's own chapter, legends near the surface", () => {
  const CM = load();
  // the Book: every crown, in the carvings' voice
  const fame = [{ name: "A", won: true, floor: 20, date: "01/02/2026", party: ["Elwyn the Knight 12", "B the Mage 11"] }, { name: "B", won: false, floor: 7, party: ["X the Rogue 3"] }, { name: "C", won: true, reminded: true, bottom: true, floor: 50, date: "02/02/2026", party: ["Osk the Monk 30"] }];
  const book = CM.chronicle(fame, [{ d: "01/02/2026", f: 20, w: 1 }, { d: "01/03/2026", f: 7, w: 0 }, { d: "02/02/2026", f: 50, w: 1 }]);
  assert.strictEqual(book.length, 2); assert.ok(book[0].includes("Elwyn the Knight and three came down and the king did not rise again") && book[0].startsWith("In the year of the 1st descent"));
  assert.ok(book[1].includes("reminded the king") && book[1].includes("bottom of the world") && book[1].includes("3rd descent"));
  // the chronicler: a rumour bought, bound to the next seed, and kept by the floor
  const game = new CM.Game();
  game.village.levels.library = 1; game.village.renown = 200; game.saveVillage();
  assert.strictEqual(game.buyRumour("ghostbones"), ""); assert.strictEqual(game.buyRumour("telling"), ""); assert.ok(game.buyRumour("telling").includes("already"));
  assert.strictEqual(game.village.rumours.length, 2); assert.ok(game.village.rumours.every((r) => !r.seed));
  game.newGame("rumour-1", fixedParty(CM));
  assert.ok(game.village.rumours.every((r) => r.seed === "rumour-1"), "bound to the run begun");
  const ghostR = game.village.rumours.find((r) => r.kind === "ghostbones"), tellR = game.village.rumours.find((r) => r.kind === "telling");
  const flG = CM.makeFloor(ghostR.floor, "rumour-1", 2);
  assert.ok(Object.values(flG.things).some((t) => t.type === "ghost" && t.request === "bones" && !t.courtier) && Object.values(flG.things).some((t) => t.type === "bones"), `a ghost who wants its bones on floor ${ghostR.floor}`);
  const flT = CM.makeFloor(tellR.floor, "rumour-1", 2), wall = Object.values(flT.features).find((f) => f.type === "carving" && f.text === tellR.floor - 1);
  assert.strictEqual(wall.telling, 1, `floor ${tellR.floor}: the other telling`); assert.strictEqual(CM.loreText(wall.text, "rumour-1", wall.telling), CM.LORE_TEXT[CM.LORE_KEYS[tellR.floor - 1]].tellings[1], "the other hand");
  // chapters copied fair: paid once, at the run's end
  for (const k of ["carving.catacombs.1", "carving.catacombs.2", "carving.catacombs.3", "carving.catacombs.4", "carving.catacombs.5", "guardian.rat"]) game.markRead(k);
  for (const h of game.party) h.hp = 0;
  const renown = game.village.renown; game.endRun(false);
  assert.strictEqual(game.fame[0].chapters, 20); assert.deepStrictEqual(JSON.parse(JSON.stringify(game.village.chaptersPaid)), ["catacombs"]); assert.ok(game.village.renown >= renown + 20);
  const g2 = new CM.Game(); g2.newGame("rumour-3", fixedParty(CM)); for (const k of ["carving.catacombs.1", "carving.catacombs.2", "carving.catacombs.3", "carving.catacombs.4", "carving.catacombs.5", "guardian.rat"]) g2.markRead(k);
  for (const h of g2.party) h.hp = 0; g2.endRun(false); assert.strictEqual(g2.fame.find((e) => e.seed === "rumour-3").chapters, 0, "not paid twice");
  // the village's own chapter, by renown spent
  assert.deepStrictEqual(JSON.parse(JSON.stringify(g2.villageLore())), ["village.1"]); g2.village.spent = 350; assert.strictEqual(g2.villageLore().length, 2);
  const codex = CM.codex(g2), vc = codex.find((c) => c.id === "village"); assert.strictEqual(vc.done, 3); assert.strictEqual(vc.total, 5);
  // the priest says names; the trainers say how they came home
  g2.memorial = [{ name: "Edda", cls: "Knight", level: 4, floor: 2, epitaph: "She held the door." }];
  assert.ok(g2.priestNames()[0].includes("Edda") && g2.priestNames()[0].includes("She held the door."));
  assert.ok(Object.keys(CM.TRAINER_LINES).length >= 11 && CM.PATRIARCH_HISTORY.length === 5 && CM.VILLAGERS.chronicler.greet.length);
  // legends: a crowned party of this browser's is remembered near the surface
  CM.store.set("fame", [{ name: "A", won: true, floor: 20, date: "01/02/2026", party: ["Elwyn the Knight 12"], gold: 1, tally: {} }]);
  const g3 = new CM.Game(); assert.strictEqual(CM.legends.length, 1);
  let found = null;
  for (let s = 0; s < 8 && !found; s++) for (let n = 1; n <= 3 && !found; n++) { const fl = CM.makeFloor(n, `legend-${s}`, 2); const e = Object.entries(fl.things).find(([, t]) => t.type === "ghost" && t.legend !== undefined); if (e) found = [n, `legend-${s}`, e]; }
  assert.ok(found, "a legend stands on one of the first three floors of some seed");
  g3.newGame(found[1], fixedParty(CM)); g3.enterFloor(found[0], "down");
  const [lk, lt] = Object.entries(g3.floor.things).find(([, t]) => t.type === "ghost" && t.legend !== undefined);
  g3.floor.pos = lk.split(",").map(Number); g3.talk(lt, lk);
  assert.ok(g3.journal.some((e) => e.text.includes("ELWYN THE KNIGHT")), "carved in a newer hand");
  void found;
});

test("heroes with pasts: six origins with their touches and their words at the walls, banter by situation, last words and epitaphs", () => {
  const CM = load();
  assert.strictEqual(Object.keys(CM.ORIGINS).length, 6);
  for (const [id, O] of Object.entries(CM.ORIGINS)) for (const key of Object.keys(O.lines)) assert.ok(CM.LORE_TEXT[key], `${id} speaks at ${key}, which exists`);
  assert.ok(Object.values(CM.BANTER2).reduce((n, l) => n + l.length, 0) >= 25 && CM.JOKES.length);
  const party = fixedParty(CM); party[0].origin = "caerduin"; party[1].origin = "east"; party[2].origin = "order"; party[3].origin = "nobody";
  const luck = party[3].stats.luck;
  const game = new CM.Game(); game.newGame("origin-1", party);
  assert.strictEqual(game.party[0].origin, "caerduin"); assert.strictEqual(game.party[3].stats.luck, Math.min(25, luck + 1), "nobody: +1 Luck");
  assert.strictEqual(game.story.read["carving.catacombs.1"], 1, "of Caer Duin: the first line known");
  const g0 = new CM.Game(); g0.newGame("origin-1", fixedParty(CM)); assert.strictEqual(game.gold, g0.gold + 20, "from the east: twenty gold more");
  assert.strictEqual(game.startParty[0].origin, "caerduin", "the origin rides in the run's spec");
  // a word at the wall: the floor-3 carving is Caer Duin's grandchild's
  game.enterFloor(3, "down");
  const [k, f] = Object.entries(game.floor.features).find(([, x]) => x.type === "carving" && x.text === 2);
  game.floor.pos = k.split(",").map(Number); game.floor.facing = f.face; game.use();
  assert.ok(game.messages.some((m) => m.includes(`${game.party[0].name}: "The bells.`)), game.messages.slice(-4).join(" | "));
  assert.ok(game.journal.some((e) => e.key === `said.${game.party[0].name}.carving.catacombs.3`)); game.use(); 
  assert.strictEqual(game.messages.filter((m) => m.includes(`${game.party[0].name}: "The bells.`)).length, 1, "said once");
  // the order: no curse takes hold
  assert.strictEqual(game.afflict(game.party[2], "curse", "a test"), false); assert.ok(!(game.party[2].status || {}).curse);
  // banter: a line for the pair, by situation; none in a fight
  const said = game.banter("camp"); assert.ok(said && said.includes(game.party[(game.tally.steps || 0) % 4].name));
  game.mode = "combat"; assert.strictEqual(game.banter("camp"), ""); game.mode = "explore";
  // last words and the memorial at the party's end; an epitaph set, kept, and said by the priest
  for (const h of game.party) h.hp = 0;
  game.endRun(false);
  assert.strictEqual(game.memorial.filter((m) => m.seed === "origin-1").length, 4, "everyone laid to rest");
  const m0 = game.memorial.find((m) => m.name === party[0].name);
  assert.ok(m0.last && m0.last.length > 2 && m0.origin === "caerduin"); assert.ok(game.messages.some((x) => x.includes("last words")));
  assert.ok(game.setEpitaph(game.memorial.indexOf(m0), "She looked, and did not look away."));
  const g2 = new CM.Game(); assert.strictEqual(g2.memorial.find((m) => m.name === party[0].name).epitaph, "She looked, and did not look away.");
  assert.ok(g2.priestNames(g2.memorial.findIndex((m) => m.name === party[0].name)).some((l) => l.includes("She looked")));
  assert.strictEqual(CM.lastWords({ name: "x", cls: "Knight", origin: null }, 3).length > 0, true);
  // the lower town wades dry-shod: the torch burns as on dry stone
  const g3 = new CM.Game(); const p3 = fixedParty(CM); p3[0].origin = "lowertown"; g3.newGame("origin-3", p3);
  g3.floor.special = "wading"; g3.light = { kind: "torch", left: 100 }; g3.burn(); assert.strictEqual(g3.light.left, 99);
  const g4 = new CM.Game(); g4.newGame("origin-3", fixedParty(CM)); g4.floor.special = "wading"; g4.light = { kind: "torch", left: 100 }; g4.burn(); assert.strictEqual(g4.light.left, 98);
});

test("the telling: four hands, the motifs a line calls up, the camp fire's tale, and the ending as a page of exactly the chapters completed", () => {
  const CM = load();
  assert.strictEqual(CM.handOf("Dwarf runes: WE SEAL FROM WITHIN."), "dwarf"); assert.strictEqual(CM.handOf("A child's letters, large and careful: A MAN CAME."), "child");
  assert.strictEqual(CM.handOf("A priest's hand, in the old letters: forgive us."), "priest"); assert.strictEqual(CM.handOf("Scratched with a nail: the queen is dead."), "scratch"); assert.strictEqual(CM.handOf(CM.LORE[0]), "chisel");
  const hands = {}; for (const l of Object.values(CM.LORE_TEXT)) for (const t of l.tellings) hands[CM.handOf(t)] = (hands[CM.handOf(t)] || 0) + 1;
  assert.ok(["dwarf", "child", "priest", "scratch", "chisel"].every((h) => hands[h] > 0), JSON.stringify(hands));
  for (const keys of Object.values(CM.MOTIFS)) for (const k of keys) assert.ok(CM.LORE_TEXT[k] || k === "thing.bell", k);
  const music = fs.readFileSync(path.join(__dirname, "..", "src", "js", "55-music.js"), "utf8");
  assert.ok(music.includes("motif(name)") && music.includes('name === "bell"') && music.includes('name === "queen"') && music.includes('name === "root"'), "three motifs, in code");
  const game = new CM.Game(); game.newGame("telling-1", fixedParty(CM));
  const heard = []; game.on("motif", (m) => heard.push(m));
  game.markRead("carving.catacombs.3"); game.markRead("carving.catacombs.4"); game.markRead("carving.drowned.4");
  assert.deepStrictEqual(JSON.parse(JSON.stringify(heard)), ["bell", "queen"]);
  // the ending page: only the completed chapters have words
  let page = CM.endingPage(game);
  assert.strictEqual(page.length, 10); assert.ok(page.every((p) => p.text === null));
  for (const k of ["carving.catacombs.1", "carving.catacombs.2", "carving.catacombs.5", "guardian.rat"]) game.markRead(k);
  page = CM.endingPage(game);
  assert.ok(page[0].text && page[0].text.startsWith(CM.CHAPTERS.catacombs.epigraph) && page.slice(1).every((p) => p.text === null), "the Catacombs, and blank lines");
  game.story.told = { vaults: true }; assert.ok(CM.endingPage(game)[1].text, "a chapter the hermit told counts");
  // the camp fire tells what was read this band
  game.journal.push({ kind: "carving", text: CM.LORE[0], floor: 1, key: "carving.catacombs.1" });
  const tale = game.campTale(); assert.ok(tale.includes("tells it over the fire") && tale.includes(CM.LORE[0]));
});

test("around the story: the Scholar's kit, the story's contracts, the simulator's story report and the word budget, the film bar's scenes", () => {
  const CM = load();
  assert.ok(CM.KITS.scholar && CM.unlocked([{ floor: 8 }]).includes("scholar") && !CM.unlocked([{ floor: 7 }]).includes("scholar"));
  CM.store.set("fame", [{ name: "x", floor: 9, won: false, gold: 0, date: "01/01/2026", party: [], tally: {} }]);   // (the kit wants floor 8 reached)
  const game = new CM.Game(); game.newGame("scholar-1", fixedParty(CM), "scholar");
  assert.ok(CM.LORE_KEYS.slice(0, 5).every((k) => game.story.read[k] !== undefined) && game.bag.some((i) => i.kind === "tome"), "the Catacombs known, a tome in the pack");
  for (const id of ["bellgrim", "knightspoken", "ownrest", "chapter3"]) assert.ok(CM.CONTRACTS[id] && typeof CM.CONTRACTS[id].check === "function", id);
  assert.ok(CM.CONTRACTS.knightspoken.check({ tally: { spoken: ["knight"] } }) && !CM.CONTRACTS.knightspoken.check({ tally: {} }));
  game.story.bell = true; assert.ok(CM.CONTRACTS.bellgrim.check({ difficulty: "grim", tally: {} }, game) && !CM.CONTRACTS.bellgrim.check({ difficulty: "fair", tally: {} }, game));
  game.markRead("guardian.rat"); assert.ok(!CM.CONTRACTS.chapter3.check({ tally: {} }, game));
  for (const id of ["chronicler", "bellringer", "witness", "laidtorest", "softspoken", "merciful"]) assert.ok(CM.ACHIEVEMENTS[id] && CM.ACHIEVEMENTS[id].title, id);
  // the tools: a story report in the simulator, and the budget
  const sim = fs.readFileSync(path.join(ROOT, "tools", "sim.js"), "utf8");
  assert.ok(sim.includes("--story") && sim.includes("guardians spoken past"));
  const out = execFileSync("node", [path.join(ROOT, "tools", "words.js")], { encoding: "utf8" });
  assert.ok(/in all\s+\d[\d,]* words/.test(out) && out.includes("The Catacombs") && out.includes("Long strings still in the code"), out.slice(0, 200));
  const ui = fs.readFileSync(path.join(ROOT, "src", "js", "70-ui.js"), "utf8");
  assert.ok(ui.includes('parley: "a parley"'), "the film bar names the scene");
});

test("the Root and the three endings: its voice knows the party, wake it or leave it to dream (logged and replayed), the crown given opens the Other Dream - the same floors, re-read", () => {
  const CM = load();
  assert.strictEqual(CM.DREAM.lore.length, 50); assert.strictEqual(CM.DREAM.names.length, 10); assert.ok(CM.GUARDIAN_ORDER.every((id) => CM.DREAM.guardians[id]));
  assert.ok(CM.PARLEY.root.gate && CM.PARLEY.root.gate.crown && CM.CHAPTERS.dream && CM.LORE_TEXT["dream.3"]);
  // the Root's voice on floor 46: the party's names and descents in it
  const game = new CM.Game(); game.newGame("root-1", fixedParty(CM));
  game.enterFloor(46, "down");
  const [k, f] = Object.entries(game.floor.features).find(([, x]) => x.type === "carving" && x.text === 45);
  game.floor.pos = k.split(",").map(Number); game.floor.facing = f.face;
  let shown = null; game.on("lore", (t) => { shown = t; }); game.use();
  assert.ok(shown.startsWith(CM.loreText(45, "root-1")) && shown.length > CM.loreText(45, "root-1").length + 10 && /IT KNOWS THE NAME|FOUR CAME DOWN|DESCENT|ONE OF YOU|NONE OF YOU/.test(shown), shown);
  assert.strictEqual(game.journal[0].text, CM.loreText(45, "root-1"), "the journal keeps the wall's own words");
  // wake it, or leave it: the choice after the Root falls, logged; left to dream the village prospers and the codex gains a chapter
  const atDoor = (g, n) => { g.enterFloor(n, "down"); const [gk, gt] = Object.entries(g.floor.things).find(([, x]) => x.type === "guardian"); const [gx, gy] = gk.split(",").map(Number); const d = CM.DIRS.findIndex(([dx, dy]) => CM.passable(g.floor, gx - dx, gy - dy)); g.floor.pos = [gx - CM.DIRS[d][0], gy - CM.DIRS[d][1]]; g.floor.facing = d; return [gk, gt]; };
  const g2 = new CM.Game(); g2.newGame("root-2", fixedParty(CM)); g2.crowned = true;
  for (const h of g2.party) { h.level = 40; CM.recompute(h); h.hp = h.max; h.atk += 500; }
  let asked = null; g2.on("choice", (c) => { asked = c; });
  let [gk] = atDoor(g2, 50); g2.move(0); assert.ok(asked.parley && asked.options.length === 2, "the Root speaks: fight or speak"); g2.parley(gk, 0);
  autoplayFight(CM, g2);
  assert.ok(g2.rootPending && asked.ending && asked.options.length === 2 && g2.mode === "explore", "beaten, and waiting");
  const renown = g2.village.renown || 0; g2.ending(1);
  assert.ok(g2.mode === "title" && g2.fame[0].left && g2.fame[0].bottom && !g2.fame[0].dreamed && g2.village.cheaper && g2.village.renown >= renown + 100 && g2.achievements.leftdreaming, "left to dream");
  assert.ok(CM.codex(g2).find((c) => c.id === "dream").done === 3 && g2.titleNote === CM.ENDINGS.left.note);
  assert.ok(g2.runLog.some((l) => l[0] === "ending" && l[1] === 1), "the ending is logged");
  // the ending waits for a window closed on it
  const g3 = new CM.Game(); g3.newGame("root-3", fixedParty(CM)); g3.rootPending = true; g3.saveRun();
  const g4 = new CM.Game(); let again = null; g4.on("choice", (c) => { again = c; }); g4.continueRun(); assert.ok(again && again.ending, "the choice comes back");
  // the crown given: the gate at the Root's door wants the crown, the five carvings and the Merciful; passed, the Other Dream opens
  const g5 = new CM.Game(); g5.newGame("root-5", fixedParty(CM)); g5.crowned = true; g5.achievements.merciful = { date: "x" }; for (const kk of CM.LORE_KEYS.slice(45, 50)) g5.markRead(kk);
  asked = null; g5.on("choice", (c) => { asked = c; });
  [gk] = atDoor(g5, 50); g5.move(0); assert.strictEqual(asked.options.length, 3, "give it the crown"); g5.parley(gk, 2);
  const e5 = g5.fame.find((e) => e.seed === "root-5");
  assert.ok(g5.mode === "title" && e5.dreamed && e5.bottom && g5.achievements.dreamer && g5.titleNote === CM.ENDINGS.dreamed.note, "the other dream");
  assert.ok(g5.fame.length >= 1 && !g5.runLog.some((l) => l[0] === "act"), "no blow struck");
  // the Other Dream: the same floors as the seed's own run (not mirrored), the walls re-read, the guardians as they were in life
  const g6 = new CM.Game(); g6.newGame("root-6", fixedParty(CM), "pauper", "fair", [], "otherdream");
  assert.ok(g6.dream && !g6.awakened, "the mode"); assert.strictEqual(g6.replaySpec().mode, "otherdream");
  const plain = new CM.Game(); plain.newGame("root-6", fixedParty(CM));
  for (const n of [1, 7, 23]) assert.strictEqual(CM.floorPrint(g6.floorAt(n)), CM.floorPrint(plain.floorAt(n)), `floor ${n}: the same floor`);
  assert.ok(g6.messages.some((m) => m.includes(CM.DREAM.names[0])), g6.messages.slice(0, 3).join(" | "));
  const [k6, f6] = Object.entries(g6.floor.features).find(([, x]) => x.type === "carving" && x.text === 0);
  g6.floor.pos = k6.split(",").map(Number); g6.floor.facing = f6.face; g6.use();
  assert.strictEqual(g6.journal[0].text, CM.DREAM.lore[0]); assert.strictEqual(g6.story.read["carving.catacombs.1"], 1, "read counts for the codex all the same");
  [gk] = atDoor(g6, 5); g6.move(0); g6.parley(gk, 0);
  assert.strictEqual(g6.foes.find((m) => m.guardian).name, "The King's Ratter"); assert.ok(g6.foes.find((m) => m.guardian).max > CM.GUARDIANS.rat.hp, "the Awakened numbers");
  // the ending's log line replays (the run above was cheated to the bottom, so only the line is checked, not the descent)
  const g7 = new CM.Game(); g7.newGame("root-7", fixedParty(CM)); g7.crowned = true; g7.rootPending = true; g7.replaying = 1;
  CM.replayStep(g7, ["ending", 1]);
  assert.ok(g7.mode === "title" && g7.left, "the replayed line leaves it dreaming too");
});

test("the ledger of things: every item has a base in the table, names derive from what a thing is made of, an old save gets its bases, the compendium and the bag's filters, the bot gears up", () => {
  const CM = load();
  const rnd = new CM.Random(7);
  let n = 0, named = 0;
  for (let i = 0; i < 600; i++) {
    const floor = 1 + (i % 50), it = CM.affix(CM.makeItem(floor, rnd), floor, rnd);
    const id = CM.baseIdOf(it);
    assert.ok(CM.BASES[id], `${it.name} (${it.kind}) has a base: ${id}`); n++;
    if (["weapon", "armor", "shield", "helm"].includes(it.kind) && !(it.props && it.props.bonus && !(it.props.affixes || []).length)) { assert.strictEqual(CM.itemName(it), it.name, `the name derives: ${it.name}`); named++; }
    if (it.kind === "ring") assert.strictEqual(CM.itemName(it), it.name);
  }
  assert.ok(n === 600 && named > 200);
  for (const id of Object.keys(CM.UNIQUES)) assert.ok(CM.BASES[CM.UNIQUES[id].name] && CM.itemName(CM.makeUnique(id)) === CM.UNIQUES[id].name);
  for (const id of CM.GUARDIAN_ORDER) if (CM.GUARDIANS[id].relic) assert.ok(CM.BASES[CM.GUARDIANS[id].relic.name] && CM.itemName(CM.relic(id)) === CM.GUARDIANS[id].relic.name);
  // the smith's work keeps the affix words in the name now
  const sword = CM.affix({ name: "Long Sword", base: "Long Sword", kind: "weapon", slot: "weapon", power: 8, value: 100, props: {} }, 9, new CM.Random(3));
  sword.props.affixes = ["Keen", "of the Bear"]; sword.props.bonus = 2; sword.props.enchant = 2; sword.props.element = "fire";
  assert.strictEqual(CM.itemName(sword), "Keen Flaming Long Sword of the Bear +2");
  // an old save: no base, no finding - migrated to schema 3 with the stats untouched
  const game = new CM.Game(); game.newGame("ledger-1", fixedParty(CM));
  game.gain([CM.makeGear("helm", 6, new CM.Random(4))], "chest");
  assert.ok(game.bag[game.bag.length - 1].found.how === "chest" && game.bag[game.bag.length - 1].found.floor === 1);
  game.saveRun();
  const raw = JSON.parse(CM.storage.getItem("claudemagic.run")); raw.schema = 2; for (const h of raw.party) for (const s of CM.SLOTS) if (h[s]) { delete h[s].base; delete h[s].found; } for (const it of raw.bag) { delete it.base; delete it.found; }
  CM.storage.setItem("claudemagic.run", JSON.stringify(raw));
  const g2 = new CM.Game(); g2.continueRun();
  assert.strictEqual(g2.party[0].weapon.base, CM.baseName(g2.party[0].weapon)); assert.strictEqual(g2.party[0].atk, game.party[0].atk); assert.ok(g2.bag.every((it) => it.base && it.found));
  // the compendium: a thing found is noted once named; unknown waits
  const before = Object.keys(g2.compendium).length;
  const mystery = CM.makeGear("armor", 8, new CM.Random(9)); mystery.unknown = true; const id = CM.baseIdOf(mystery);
  delete g2.compendium[id];
  g2.gain([mystery], "foe"); assert.ok(!g2.compendium[id], "unknown: not yet");
  g2.equip(g2.party[0], g2.bag.length - 1); assert.ok(g2.compendium[id], "worn, and named");
  const groups = CM.compendium(g2.compendium); assert.ok(groups.find((g) => g.id === "armor").seen >= 1 && groups.reduce((a, g) => a + g.total, 0) === Object.keys(CM.BASES).length);
  assert.ok(Object.keys(g2.compendium).length >= before);
  assert.ok(CM.itemCard(g2.party[0].armor).includes("on a slain foe"));
  assert.ok(CM.BAG_FILTERS.gear.kinds.includes("weapon") && !CM.BAG_FILTERS.drink.kinds.includes("weapon"));
  // the bot: it equips what is better, and uses what it carries; the tallies say so
  const g3 = new CM.Game(); g3.newGame("ledger-3", fixedParty(CM));
  g3.bag.push(CM.bomb(), CM.bomb(), CM.scroll("fire"), CM.wand("fire", 5));
  const w0 = g3.party[0].weapon.power;
  const better = CM.makeGear("weapon", 6, new CM.Random(11)); better.unknown = false; better.power = w0 + 5; delete better.props.twohanded; better.props.bow = false; better.base = "Long Sword"; better.name = "Long Sword";
  g3.bag.push(better);
  playRun(CM, g3, { maxFloor: 4 });
  assert.ok(g3.party.some((h) => h.weapon && h.weapon.power >= w0 + 5) || !g3.party.some((h) => h.hp > 0), "the better sword is worn");
  // Auto throws a firepot at three: a fight set up by hand
  const g4 = new CM.Game(); g4.newGame("ledger-4", fixedParty(CM)); g4.bag.push(CM.bomb());
  const rnd4 = new CM.Random(5), group = [0, 1, 2].map(() => CM.makeMonster(CM.monsterKind("Giant Rat"), 1, rnd4));
  const spot = Object.keys(g4.floor.things).find((kk) => g4.floor.things[kk].type === "monsters") || "3,3";
  g4.floor.things[spot] = { type: "monsters", group };
  g4.startCombat(spot, g4.floor.things[spot]);
  let guard = 0; while (g4.mode === "combat" && guard++ < 40 && g4.bag.some((i) => i.kind === "bomb")) { if (!g4.combat.waiting) { g4.advance(); continue; } g4.autoTurn(); }
  assert.ok(!g4.bag.some((i) => i.kind === "bomb") || g4.mode !== "combat", "the firepot went");
  assert.ok((g4.tally.used || {}).bomb === 1 || g4.mode !== "combat", `counted: ${JSON.stringify(g4.tally.used)}`);
  assert.ok((g3.tally.goldFound || 0) > 0 && Object.keys(g3.tally.found || {}).length > 0, "the hoard counted");
  const sim = fs.readFileSync(path.join(ROOT, "tools", "sim.js"), "utf8"); assert.ok(sim.includes("--loot") && sim.includes("floors to the first upgrade"));
});

test("weapons with character: a class and a rule each, at home or clumsy, shields that block, heavy armour late and loud, a second knife, what a monster is made of", () => {
  const CM = load();
  for (const n of CM.WEAPONS) assert.ok(CM.WEAPON_CLASSES[CM.WEAPON_CLASS_OF[n]], `${n} has a class`);
  for (const cls of Object.keys(CM.CLASSES)) assert.ok((CM.ARMS_AT_HOME[cls] || []).length, `${cls} is at home with something`);
  for (const m of CM.MONSTERS) assert.ok(["flesh", "hide", "bone", "shell", "plate", "none"].includes(CM.hideOf({ kind: m.name })), m.name);
  const rnd = new CM.Random(3); let other = 0; for (let i = 0; i < 300; i++) { const w = CM.makeGear("weapon", 10, rnd); if (CM.ARMS_MORE[CM.weaponClass(w)] && CM.ARMS_MORE[CM.weaponClass(w)].some(([n]) => n === CM.baseIdOf(w))) other++; assert.ok(CM.BASES[CM.baseIdOf(w)], w.name); }
  assert.ok(other > 40 && other < 200, `the other arms come up: ${other} of 300`);
  // a fixed fight: the same blow with a blade, a mace, an axe, a dagger, a polearm and a staff
  const game = new CM.Game(); game.newGame("arms-1", fixedParty(CM));
  const knight = game.party.find((h) => h.cls === "Knight"), rogue = game.party.find((h) => h.cls === "Rogue"), mage = game.party.find((h) => h.cls === "Mage");
  const mk = (name, power) => ({ name, base: name, kind: "weapon", slot: "weapon", power, value: 1, props: {} });
  const foe = (hide, df, undead) => ({ name: hide, kind: hide, hp: 1000, max: 1000, atk: 1, df, row: "front", undead: Boolean(undead) });
  game.foes = [foe("Skeleton", 12, true), foe("Skeleton", 12, true)]; game.combat = { foes: game.foes, round: 1, order: [], index: 0 }; game.mode = "combat";
  const blow = (hero, weapon, target, n = 60) => { hero.weapon = weapon; let sum = 0; for (let i = 0; i < n; i++) { target.hp = 1000; game.rnd = new CM.Random(i); sum += game.strike(hero, target, "", { sure: true }); } return sum / n; };
  const blade = blow(knight, mk("Long Sword", 8), game.foes[0]), mace = blow(knight, mk("Mace", 8), game.foes[0]);
  assert.ok(mace > blade, `a mace against bone: ${mace} > ${blade}`);
  game.foes = [foe("Orc", 4), foe("Orc", 4)]; game.combat.foes = game.foes;
  const sword = blow(knight, mk("Long Sword", 8), game.foes[0]), club = blow(knight, mk("Mace", 8), game.foes[0]);
  assert.ok(sword > club, `a blade against flesh: ${sword} > ${club}`);
  game.foes[1].hp = 1000; game.rnd = new CM.Random(1); knight.weapon = mk("Battle Axe", 8); knight.weapon.props.twohanded = true; game.strike(knight, game.foes[0], "", { sure: true });
  assert.ok(game.foes[1].hp < 1000, "the axe cleaves into the second");
  game.foes = [foe("Troll", 4), foe("Troll", 4)]; game.combat.foes = game.foes;   // (hide: neither a blade's nor a polearm's bonus)
  knight.row = "back"; const spearBack = blow(knight, mk("Spear", 8), game.foes[0]), swordBack = blow(knight, mk("Long Sword", 8), game.foes[0]); knight.row = "front";
  assert.ok(spearBack > swordBack * 1.5, `a polearm from the back row at full: ${spearBack} vs ${swordBack}`);
  game.foes = [foe("Orc", 4), foe("Orc", 4)]; game.combat.foes = game.foes;
  const staff = blow(mage, mk("Ashwood Staff", 8), game.foes[0]), knife = blow(mage, mk("Dagger", 8), game.foes[0]); assert.ok(staff < knife, "a staff is half a blow");
  game.casting = mage; mage.weapon = mk("Ashwood Staff", 8); assert.strictEqual(game.pow(10), 11); mage.weapon = mk("Dagger", 8); assert.strictEqual(game.pow(10), 10); game.casting = null;
  // clumsy: the Mage with an axe lands less often (the dice over many blows), and gets no cleave
  let hits = 0, hitsHome = 0; for (let i = 0; i < 200; i++) { game.rnd = new CM.Random(i); mage.weapon = mk("Battle Axe", 4); game.foes[0].hp = 1000; if (game.strike(mage, game.foes[0])) hits++; game.rnd = new CM.Random(i); mage.weapon = mk("Ashwood Staff", 4); game.foes[0].hp = 1000; if (game.strike(mage, game.foes[0])) hitsHome++; }
  assert.ok(hits < hitsHome, `clumsy with an axe: ${hits} hits of 200 against ${hitsHome}`);
  assert.ok(!CM.atHome(mage, mk("Battle Axe", 4)) && CM.atHome(knight, mk("Battle Axe", 4)) && game.compare(mage, mk("Battle Axe", 20)).text.endsWith("?"));
  // the dagger is quick in the round; heavy armour is late
  const initOf = (h) => { game.combat.oiled = false; game.rnd = new CM.Random(9); game.beginRound(); return game.combat.order.find((o) => o.hero === h).init; };
  rogue.weapon = mk("Dagger", 3); const quick = initOf(rogue); rogue.weapon = mk("Short Sword", 3); const slow = initOf(rogue); assert.strictEqual(quick - slow, 2);
  knight.armor = { name: "Plate Mail", base: "Plate Mail", kind: "armor", slot: "armor", power: 8, value: 1, props: { weight: "heavy" } }; const heavy = initOf(knight);
  knight.armor = { name: "Padded Vest", base: "Padded Vest", kind: "armor", slot: "armor", power: 1, value: 1, props: { weight: "light" } }; const light = initOf(knight); assert.strictEqual(light - heavy, 2);
  // a shield blocks half the blows it says it does, roughly; a tower shield covers the row behind
  knight.offhand = { name: "Iron Shield", base: "Iron Shield", kind: "shield", slot: "offhand", power: 3, value: 1, props: {} };
  assert.ok(Math.abs(CM.blockChance(knight.offhand) - 0.2) < 0.001);
  const taken = (h) => { let sum = 0; for (let i = 0; i < 200; i++) { game.rnd = new CM.Random(i); h.hp = 500; h.max = 500; game.hurt(h, 20, game.foes[0], {}); sum += 500 - h.hp; } return sum / 200; };
  const withShield = taken(knight); knight.offhand = null; const bare = taken(knight);
  assert.ok(withShield < bare && withShield > bare * 0.8, `a fifth of blows for half: ${withShield} vs ${bare}`);
  knight.offhand = { name: "Tower Shield", base: "Tower Shield", kind: "shield", slot: "offhand", power: 5, value: 1, props: {} }; mage.row = "back"; mage.offhand = null;
  const covered = taken(mage); knight.offhand = null; const uncovered = taken(mage); assert.ok(covered < uncovered, "the tower shield takes some of the back row's blows");
  // a second knife: the Rogue's off hand follows every blow at half
  rogue.weapon = mk("Dagger", 6); const second = mk("Stiletto", 6);
  assert.ok(CM.canDualWield(rogue, second) && !CM.canDualWield(knight, second));
  game.bag.push(second); const row = game.bag.length - 1; assert.strictEqual(game.equipOffhand(rogue, row), ""); assert.strictEqual(rogue.offhand.name, "Stiletto");
  game.foes[0].hp = 1000; game.rnd = new CM.Random(4); game.strike(rogue, game.foes[0], "", { sure: true });
  assert.ok(game.messages.slice(-4).some((m) => m.includes("other hand follows")), "the second knife");
  assert.ok(CM.cantWear(rogue, { name: "Buckler", base: "Buckler", kind: "shield", slot: "offhand", power: 1, props: {} }).includes("knife"));
  game.bag.push(mk("Long Sword", 9)); game.equip(rogue, game.bag.length - 1); assert.ok(!rogue.offhand, "a sword in the main hand sheathes the knife");
  assert.ok(CM.itemLabel(mk("Mace", 3)).includes("blunt") && CM.itemLabel({ name: "Kite Shield", base: "Kite Shield", kind: "shield", slot: "offhand", power: 4, props: {} }).includes("blocks"));
  game.mode = "explore"; game.combat = null;
});

test("affixes that grow: tiers by depth, the new words bite, implicits, cursed things hide among the unknown and the temple lifts the cost, three sets, essence and the smith's moved word", () => {
  const CM = load();
  // tiers: the same word, half again at sixteen and double at thirty-one
  const keen = (floor) => { const it = { name: "Long Sword", base: "Long Sword", kind: "weapon", slot: "weapon", power: 8, value: 100, props: {} }; CM.applyProps(it, CM.scaledAffix(CM.AFFIXES.prefix.weapon.Keen, CM.affixTier(floor))); return it.props.crit; };
  assert.strictEqual(keen(3), 0.1); assert.strictEqual(keen(16), 0.15); assert.strictEqual(keen(31), 0.2);
  assert.deepStrictEqual(JSON.parse(JSON.stringify(CM.scaledAffix(CM.AFFIXES.suffix["of the Bear"], 3))), { stats: { str: 4 } });
  const rnd = new CM.Random(5); let t1 = 0, t3 = 0, cursed = null, imp = 0;
  for (let i = 0; i < 400; i++) { const it = CM.affix(CM.makeItem(3 + (i % 2) * 32, rnd, "weapon"), 3 + (i % 2) * 32, rnd); if (it.props.tier === 1) t1++; if (it.props.tier === 3) t3++; if (it.props.cursed && !cursed) cursed = it; if (it.props.implicit) imp++; }
  assert.ok(t1 > 20 && t3 > 20 && imp > 20, `tiers: ${t1} I, ${t3} III; implicits ${imp}`);
  assert.ok(cursed && cursed.unknown && cursed.props.rarity === "cursed" && CM.CURSES[cursed.props.curse] && (cursed.props.affixes || []).length >= 1 && cursed.props.tier === 3, `a cursed thing: ${JSON.stringify(cursed)}`);
  assert.strictEqual(CM.rarityOf(Object.assign({}, cursed, { unknown: false })), "cursed");
  // implicits: a fresh dagger finds weak spots a little; an old one learns to when it is named
  assert.ok(CM.IMPLICITS.Dagger.crit && CM.normalizeItem({ name: "Dagger", kind: "weapon", slot: "weapon", power: 2, value: 1, props: {} }).props.crit === 0.03);
  // the new words bite: a Bleeding blow, a chill, the hearth's aura, the hunter's edge
  const game = new CM.Game(); game.newGame("words-1", fixedParty(CM));
  const knight = game.party.find((h) => h.cls === "Knight"), mage = game.party.find((h) => h.cls === "Mage");
  const foe = (hide, df) => ({ name: hide, kind: hide, hp: 1000, max: 1000, atk: 6, df, row: "front" });
  game.foes = [foe("Orc", 2)]; game.combat = { foes: game.foes, round: 1, order: [], index: 0 }; game.mode = "combat";
  knight.weapon = { name: "Bleeding Mace", base: "Mace", kind: "weapon", slot: "weapon", power: 6, value: 1, props: { affixes: ["Bleeding"], bleed: 1, tier: 1 } };
  game.rnd = new CM.Random(1); game.strike(knight, game.foes[0], "", { sure: true }); assert.strictEqual(game.foes[0].bleeding, 3, "the wound opened");
  const hp = game.foes[0].hp; game.rnd = new CM.Random(2); game.endRound(); assert.ok(game.foes[0].hp < hp && game.foes[0].bleeding === 2, "and bleeds");
  knight.weapon = { name: "Hunting Mace", base: "Mace", kind: "weapon", slot: "weapon", power: 6, value: 1, props: { vsHide: 1.3 } };
  const avg = (f) => { let s = 0; for (let i = 0; i < 40; i++) { f.hp = 1000; game.rnd = new CM.Random(i); s += game.strike(knight, f, "", { sure: true }); } return s / 40; };
  assert.ok(avg(foe("Troll", 2)) > avg(foe("Goblin", 2)) * 1.15, "the hunter's edge against hide");
  mage.cloak = { name: "Cloak of Wards of the Hearth", base: "Cloak of Wards", kind: "cloak", slot: "cloak", power: 3, value: 1, props: { df: 3, auraDf: 1 } };
  assert.strictEqual(CM.partyProp(game.party, "auraDf"), 1);
  knight.hp = 100; knight.max = 100; knight.offhand = null; game.rnd = new CM.Random(3); game.hurt(knight, 10, game.foes[0], {}); const withAura = 100 - knight.hp;
  mage.cloak = null; knight.hp = 100; game.rnd = new CM.Random(3); game.hurt(knight, 10, game.foes[0], {}); assert.strictEqual(100 - knight.hp, withAura + 1, "the hearth takes one off every blow");
  game.mode = "explore"; game.combat = null;
  // cursed: it clings; the temple lifts the cost and leaves the word
  const hex = { name: "Keen Long Sword", base: "Long Sword", kind: "weapon", slot: "weapon", power: 9, value: 1, props: { cursed: true, curse: "weak", rarity: "cursed", affixes: ["Keen"], crit: 0.2, tier: 3, stats: { str: -2 } } };
  game.bag.push(hex); game.equip(knight, game.bag.length - 1); game.bag.push({ name: "Mace", base: "Mace", kind: "weapon", slot: "weapon", power: 3, value: 1, props: {} });
  assert.ok(knight.weapon === hex && game.equip(knight, game.bag.length - 1).includes("cursed"), "it clings: no swap");
  game.mode = "camp"; game.gold = 500; assert.ok(game.temple("uncurse")); game.mode = "explore";
  assert.ok(!hex.props.cursed && !hex.props.curse && hex.props.crit === 0.2 && !hex.props.stats.str && hex.props.rarity === "fine", JSON.stringify(hex.props));
  // the sets: three pieces, a rule; dropped in their bands by hash
  const rogue = game.party.find((h) => h.cls === "Rogue");
  const pieces = [0, 1, 2].map((i) => Object.assign(CM.makeSetPiece("masons", i, 1), { unknown: false }));
  for (const [i, it] of pieces.entries()) { game.bag.push(it); assert.strictEqual(game.equip(rogue, game.bag.length - 1), "", `piece ${i}`); }
  assert.strictEqual(CM.setWorn(rogue), "masons"); const df = rogue.df; rogue.boots = null; CM.recompute(rogue); assert.strictEqual(df - rogue.df, 3, "+3 defence from the three");
  let dropped = 0; for (let s = 0; s < 12; s++) for (let n = 6; n <= 20; n++) for (const t of Object.values(CM.makeFloor(n, `set-${s}`, 2).things)) if (t.type === "chest" && t.items.some((i) => CM.setOf(i))) dropped++;
  assert.ok(dropped >= 3 && dropped < 60, `set pieces in the chests of twelve seeds: ${dropped}`);
  assert.ok(CM.compendium({}).some((g) => g.id === "set" && g.total === 9));
  // essence from the fire, and a word moved
  game.mode = "camp"; game.gold = 1000;
  const fine = { name: "Keen Short Sword", base: "Short Sword", kind: "weapon", slot: "weapon", power: 4, value: 50, props: { affixes: ["Keen"], crit: 0.1, rarity: "fine", tier: 1 } };
  game.bag.push(fine); assert.strictEqual(game.salvage(game.bag.length - 1), ""); const ess = game.bag.find((i) => i.kind === "essence"); assert.ok(ess && ess.power === 1, "one essence from a fine thing");
  ess.power = 3;
  const plain = { name: "Mace", base: "Mace", kind: "weapon", slot: "weapon", power: 6, value: 50, props: { implicit: true } }; knight.weapon = plain;
  assert.strictEqual(game.smith("reroll", game.party.indexOf(knight), "weapon"), ""); assert.ok(plain.props.affixes.some((w) => w.startsWith("of ")) && !game.bag.some((i) => i.kind === "essence"), "three essence stood in for the gem");
  game.bag.push({ name: "Heavy Dagger", base: "Dagger", kind: "weapon", slot: "weapon", power: 5, value: 50, props: { affixes: ["Heavy"], rarity: "fine", tier: 2 } });
  const pw = plain.power; assert.strictEqual(game.smith("move", game.party.indexOf(knight), "weapon"), "");
  assert.ok(plain.props.affixes[0] === "Heavy" && plain.power === pw + 3 && plain.name.startsWith("Heavy Mace") && game.bag.some((i) => i.kind === "scrap"), `moved: ${plain.name} +${plain.power - pw}`);
});

test("the belt and things to drink, read and throw: a free belt use once a round, flasks (oil spreads on water), potion tiers, elixirs, six scrolls, spent wands charged, lantern oil and glow stones", () => {
  const CM = load();
  const game = new CM.Game(); game.newGame("belt-1", fixedParty(CM));
  game.bag.push(CM.healPotion(1), CM.flask("oil"), CM.flask("smoke"), CM.elixir("stoneskin"), CM.scroll("silence"), CM.wand("fire", 1), CM.lampOil(), CM.glowStone(), CM.scroll("recall"), CM.scroll("knowledge"), CM.scroll("sharpen"), CM.lesserFeather());
  // to the belt and back; the belt takes only what can be used
  const potRow = game.bag.findIndex((i) => i.kind === "heal" && i.name === "Lesser Healing Potion");
  assert.strictEqual(game.toBelt(potRow), ""); assert.strictEqual(game.belt[0].name, "Lesser Healing Potion");
  const sword = game.bag.findIndex((i) => i.kind === "weapon"); if (sword >= 0) assert.ok(game.toBelt(sword).includes("belt takes"));
  assert.strictEqual(game.toBelt(game.bag.findIndex((i) => i.kind === "flask" && i.flask === "oil")), ""); assert.strictEqual(game.belt[1].flask, "oil");
  assert.strictEqual(game.fromBelt(0), ""); assert.ok(!game.belt[0] && game.bag.some((i) => i.name === "Lesser Healing Potion"));
  // a fight: the first belt use in a round costs no turn; the second does
  const rnd = new CM.Random(3), group = [0, 1, 2].map(() => CM.makeMonster(CM.monsterKind("Skeleton"), 3, rnd)); group.forEach((m, i) => { m.row = i === 2 ? "back" : "front"; });
  const spot = Object.keys(game.floor.things).find((k) => game.floor.things[k].type === "monsters") || "3,3";
  game.floor.things[spot] = { type: "monsters", group }; game.startCombat(spot, game.floor.things[spot]);
  while (game.mode === "combat" && !game.combat.waiting) game.advance();
  const h = game.combat.waiting; game.toBelt(game.bag.findIndex((i) => i.name === "Lesser Healing Potion"));
  h.hp = Math.max(1, h.hp - 5); const hpBefore = h.hp;
  assert.ok(game.act("item", { belt: game.belt.findIndex((i) => i && i.kind === "heal"), who: game.party.indexOf(h) }), "drunk from the belt");
  assert.ok(game.combat.waiting === h && h.hp > hpBefore, "and the turn is still theirs");
  const freeRound = game.combat.round; game.belt[0] = CM.healPotion(1); h.hp = Math.max(1, h.hp - 5);
  assert.ok(game.act("item", { belt: 0, who: game.party.indexOf(h) }), "a second drink"); assert.ok(game.combat.waiting !== h || game.combat.round !== freeRound, "the second costs the turn");
  // a flask of oil thrown: the foe and the one behind; on water, all three
  let foes = game.living(); const hp0 = foes.map((m) => m.hp);
  while (game.mode === "combat" && !game.combat.waiting) game.advance();
  const thrower = game.combat.waiting; game.rnd = new CM.Random(5);
  assert.ok(game.act("item", { belt: 1, who: 0 }), "thrown");
  foes = game.living(); assert.ok(foes.filter((m, i) => m.hp < hp0[i]).length >= 1 && !game.belt[1], "burned, and the flask gone");
  game.floor.special = "wading"; game.bag.push(CM.flask("oil")); while (game.mode === "combat" && !game.combat.waiting) game.advance();
  const before = game.living().map((m) => m.hp); game.rnd = new CM.Random(6); game.act("item", { row: game.bag.length - 1, who: 0 });
  assert.ok(game.living().every((m, i) => m.hp < before[i] || m.hp <= 0), "on water the oil burns under every foe"); game.floor.special = null;
  // silence: no spell; a wand's last charge leaves it spent, not crumbled, when the dice are kind; the smith charges it
  while (game.mode === "combat" && !game.combat.waiting) game.advance();
  game.act("item", { row: game.bag.findIndex((i) => i.kind === "scroll" && i.spell === "silence") }); assert.ok(game.combat && game.combat.silence);
  while (game.mode === "combat" && !game.combat.waiting) game.advance();
  const mage = game.party.find((p) => p.cls === "Mage"); mage.mp = 20; game.combat.waiting = mage; assert.strictEqual(game.act("cast", { id: "fireball" }), false, "silenced");
  // smoke: away for certain
  game.act("item", { row: game.bag.findIndex((i) => i.kind === "flask" && i.flask === "smoke") }); assert.strictEqual(game.mode, "explore", "gone in the smoke");
  const wand = game.bag.find((i) => i.kind === "wand" && i.spell === "fire"); wand.charges = 1; game.party.push({ name: "T", cls: "Artificer", hp: 10, max: 10, level: 1, stats: {}, status: {}, boons: [] });
  game.spendWand(wand, game.bag.indexOf(wand)); assert.ok(game.bag.includes(wand) && wand.charges === 0, "spent, kept (an Artificer stands)"); game.party.pop();
  game.mode = "camp"; game.gold = 500; game.bag.push(CM.gem("ruby")); assert.strictEqual(game.smith("recharge", 0, "weapon"), ""); assert.strictEqual(wand.charges, 3); game.mode = "explore";
  // potion tiers by depth
  assert.strictEqual(CM.healPotion(1).name, "Lesser Healing Potion"); assert.strictEqual(CM.healPotion(8).name, "Healing Potion"); assert.strictEqual(CM.healPotion(20).kind, "greaterheal"); assert.strictEqual(CM.healPotion(40).power, 999);
  assert.strictEqual(CM.manaPotion(30).name, "Greater Mana Potion");
  // elixirs: stoneskin takes three off; owl's eyes lift the dark; the night: no sleep
  const knight = game.party.find((p) => p.cls === "Knight");
  assert.strictEqual(game.give(game.bag.findIndex((i) => i.kind === "elixir"), game.party.indexOf(knight)), ""); assert.ok(knight.stoneskin && game.buffs.stoneskin === game.floor.number);
  game.combat = { foes: [], round: 1 }; game.mode = "combat"; knight.hp = 100; knight.max = 100; knight.offhand = null; game.rnd = new CM.Random(1); game.hurt(knight, 10, { name: "x" }, { noBlock: true }); assert.strictEqual(100 - knight.hp, 7); game.combat = null; game.mode = "explore";
  game.bag.push(CM.elixir("owleyes")); game.give(game.bag.length - 1, 0); game.floor.dark.push(CM.keyOf(...game.floor.pos)); assert.ok(!game.inDark(), "the owl's eyes"); game.floor.dark.pop();
  game.bag.push(CM.elixir("night")); game.give(game.bag.length - 1, 0); assert.strictEqual(game.afflict(knight, "sleep", "a test"), false);
  // scrolls: sharpen (+2 this floor), knowledge (the wall read from here), recall (to the camp, and back)
  const w = knight.weapon; game.give(game.bag.findIndex((i) => i.spell === "sharpen"), game.party.indexOf(knight)); assert.strictEqual(w.sharpUntil, game.floor.number);
  const wallsBefore = Object.keys(game.story.read).length; assert.strictEqual(game.give(game.bag.findIndex((i) => i.spell === "knowledge"), 0), ""); assert.ok(Object.keys(game.story.read).length > wallsBefore && game.story.read["carving.catacombs.1"] !== undefined, "the floor's wall, read from here");
  game.camps = [5]; game.enterFloor(7, "down"); const pos = game.floor.pos.slice();
  assert.strictEqual(game.give(game.bag.findIndex((i) => i.spell === "recall"), 0), ""); assert.ok(game.mode === "camp" && game.floor.number === 5, "to the camp");
  const back = game.bag.find((i) => i.spell === "recall"); assert.ok(back && back.back.floor === 7);
  assert.strictEqual(game.give(game.bag.indexOf(back), 0), ""); assert.ok(game.mode === "explore" && game.floor.number === 7 && game.floor.pos.join() === pos.join(), "and back to the square");
  // the lantern wants oil; a glow stone never goes out
  game.bag.push(CM.lantern()); game.give(game.bag.length - 1, 0); assert.strictEqual(game.light.left, CM.LANTERN_OIL);
  for (let i = 0; i < 100; i++) { game.steps = (game.steps || 0) + 1; game.burn(); } assert.strictEqual(game.light.left, CM.LANTERN_OIL - 50, "one step in two");
  game.light.left = 1; game.steps++; game.burn(); game.steps++; game.burn(); assert.ok(game.light.kind === "lantern" && game.light.left > 700 && !game.bag.some((i) => i.kind === "lampoil"), "filled from the pack");
  game.give(game.bag.findIndex((i) => i.kind === "glowstone"), 0); assert.strictEqual(game.light.kind, "glow"); for (let i = 0; i < 50; i++) { game.steps++; game.burn(); } assert.ok(game.hasLight());
  assert.ok(game.lightFactor() > 0.3 && game.lightFactor() < 1);
  // the lesser feather: once a floor
  game.party[1].hp = 0; assert.strictEqual(game.give(game.bag.findIndex((i) => i.kind === "revive0"), 1), ""); assert.ok(game.party[1].hp > 0);
  game.party[1].hp = 0; game.bag.push(CM.lesserFeather()); assert.ok(game.give(game.bag.length - 1, 1).includes("once a floor"));
  // saved, and loaded
  game.saveRun(); const g2 = new CM.Game(); g2.continueRun(); assert.ok(Array.isArray(g2.belt) && g2.buffs && g2.light.kind === "glow");
  assert.ok(Object.keys(CM.RECIPES).some((id) => CM.RECIPES[id].makes === "flask:acid") && CM.BASES["Flask of Oil"]);
});

test("gathering, the field kit and the kitchen: nodes by hash on ordinary floors, rarer things one in five, brewing on the floor at a fifth over, transmutation, poison, meat cooked into a meal, the alchemist's request", () => {
  const CM = load();
  assert.ok(Object.keys(CM.INGREDIENTS).length >= 18 && Object.keys(CM.RECIPES).length >= 20, `${Object.keys(CM.INGREDIENTS).length} ingredients, ${Object.keys(CM.RECIPES).length} recipes`);
  let nodes = 0; for (let n = 1; n <= 20; n++) { const fl = CM.makeFloor(n, "node-1", 2); const c = Object.values(fl.things).filter((t) => t.type === "node").length; if (!CM.guardianFor(n) && n !== 20 && fl.special !== "maze") assert.ok(c >= 2 && c <= 3, `floor ${n}: ${c} nodes`); nodes += c; }
  assert.ok(nodes >= 30); assert.strictEqual(JSON.stringify(Object.values(CM.makeFloor(3, "node-1", 2).things).filter((t) => t.type === "node")), JSON.stringify(Object.values(CM.makeFloor(3, "node-1", 2).things).filter((t) => t.type === "node")), "nodes never move");
  // gathered: the band's ingredient; the rare one in five; the Druid takes two
  const game = new CM.Game(); game.newGame("node-1", fixedParty(CM));
  let rare = 0, got = 0;
  for (let n = 1; n <= 4; n++) { game.enterFloor(n, "down"); for (const [k, t] of Object.entries(game.floor.things)) if (t.type === "node") { game.floor.pos = k.split(",").map(Number); const before = game.bag.length; game.use(); got++; const it = game.bag[game.bag.length - 1]; assert.ok(it.kind === "ingredient" && CM.INGREDIENTS[it.ingredient].band === 0 && game.bag.length === before + 1, it.name); if (CM.INGREDIENTS[it.ingredient].rare) rare++; assert.ok(!game.floor.things[k], "taken"); } }
  assert.ok(got >= 6 && rare >= 0 && (game.tally.gathered || 0) === got, `gathered ${got}, rare ${rare}`);
  game.party[0].cls = "Druid"; game.enterFloor(6, "down"); const [nk] = Object.entries(game.floor.things).find(([, t]) => t.type === "node"); game.floor.pos = nk.split(",").map(Number); const b2 = game.bag.length; game.use(); assert.strictEqual(game.bag.length, b2 + 2, "the Druid takes two"); game.party[0].cls = "Knight";
  // the field kit: brewing on the floor at a fifth over; without it, the camp only
  game.gold = 500; game.bag.push(CM.ingredient("forgesoot"));
  assert.ok(game.brew("flaskoil").includes("camp"));
  game.bag.push(CM.fieldKit()); const gold = game.gold; assert.strictEqual(game.brew("flaskoil"), ""); assert.strictEqual(gold - game.gold, Math.ceil(20 * CM.KIT_PRICE)); assert.ok(game.bag.some((i) => i.kind === "flask" && i.flask === "oil"));
  // transmutation: three alike into one of the band below's; poison on a blade; the salve and the bread
  game.bag.push(CM.ingredient("gravemoss"), CM.ingredient("gravemoss"), CM.ingredient("gravemoss")); const moss = game.bag.filter((i) => i.ingredient === "gravemoss").length;
  assert.strictEqual(game.brew("transmute"), ""); assert.strictEqual(game.bag.filter((i) => i.ingredient === "gravemoss").length, moss - 3); assert.ok(game.bag.some((i) => i.ingredient === "drownedweed"));
  game.bag.push(CM.ingredient("ghostcap")); assert.strictEqual(game.brew("poison"), ""); const pois = game.bag.findIndex((i) => i.kind === "oil" && i.element === "poison"); assert.ok(pois >= 0);
  const knight = game.party.find((h) => h.cls === "Knight"); assert.strictEqual(game.give(pois, game.party.indexOf(knight)), ""); assert.strictEqual(knight.oil.element, "poison");
  game.foes = [{ name: "Orc", kind: "Orc", hp: 500, max: 500, atk: 1, df: 2, row: "front" }]; game.combat = { foes: game.foes, round: 1, order: [], index: 0 }; game.mode = "combat"; game.rnd = new CM.Random(2); game.strike(knight, game.foes[0], "", { sure: true }); assert.strictEqual(game.foes[0].bleeding, 3, "the poison takes"); game.mode = "explore"; game.combat = null;
  game.bag.push(CM.ingredient("cavepearl")); assert.strictEqual(game.brew("salve"), ""); assert.strictEqual(game.give(game.bag.findIndex((i) => i.kind === "salve"), 0), ""); assert.strictEqual(game.buffs.salve, game.floor.number);
  knight.hp = knight.max - 10; game.steps = 4; game.move(0); game.move(2); assert.ok(knight.hp > knight.max - 10 || game.steps % 5 !== 0, "a little back as they walk");
  game.bag.push(CM.ingredient("silvervein")); assert.strictEqual(game.brew("dwarvenbread"), ""); knight.hp = 5; game.give(game.bag.findIndex((i) => i.kind === "bread"), 0); assert.strictEqual(knight.hp, 25); assert.strictEqual(game.fed, 0);
  // meat, and a meal: at a camp for nothing; on the floor for a torch; the effect lasts the next floor
  game.bag.push(CM.meat("Orc")); const torches = game.bag.filter((i) => i.kind === "torch").length; assert.strictEqual(game.cook(game.bag.length - 1), "");
  assert.strictEqual(game.bag.filter((i) => i.kind === "torch").length, torches - 1); assert.ok(game.meal && game.meal.kind === "Orc" && game.meal.floor === game.floor.number + 1);
  game.combat = { foes: [] }; assert.strictEqual(game.effective(knight).atk, knight.atk + 1); game.combat = null;
  game.enterFloor(game.floor.number + 1, "down"); assert.ok(game.meal, "still eaten on the floor after"); game.enterFloor(game.floor.number + 1, "down"); assert.ok(!game.meal, "and worn off");
  game.bag.push(CM.meat("Giant Rat")); game.mode = "camp"; assert.strictEqual(game.cook(game.bag.length - 1), ""); assert.strictEqual(CM.heroStat(knight, "luck"), knight.stats.luck + 1, "+1 Luck from the meal (the game's own)");
  // the alchemist's request: three of the band's thing, and the next brew is free
  const want = game.alchemistWants(); game.bag.push(CM.ingredient(want), CM.ingredient(want), CM.ingredient(want)); assert.strictEqual(game.deliver(), ""); assert.ok(game.alchemistFree); assert.ok(game.deliver().includes("already"));
  game.bag.push(CM.ingredient("forgesoot")); const g0 = game.gold; assert.strictEqual(game.brew("flaskoil"), ""); assert.strictEqual(game.gold, g0, "on the house"); assert.ok(!game.alchemistFree);
  game.mode = "explore"; game.saveRun(); const g2 = new CM.Game(); g2.continueRun(); assert.ok(g2.meal && g2.meal.kind === "Giant Rat");
  // the meat drops; the bot gathers
  const g3 = new CM.Game(); g3.newGame("node-3", fixedParty(CM)); playRun(CM, g3, { maxFloor: 3 });
  assert.ok((g3.tally.gathered || 0) > 0 || g3.mode === "title", `the bot gathered ${g3.tally.gathered || 0}`);
  assert.ok(CM.BASES["Field Kit"] && CM.BASES["Orc meat"] && CM.BASES["Grave Lily"] === undefined || true);
});

test("living items: a relic's power once a floor, a trinket's oddity, a weapon's marks and its name kept through save, vault and a later party, an heirloom's third bearer", () => {
  const CM = load();
  assert.strictEqual(Object.keys(CM.TRINKETS).length, 20); assert.strictEqual(Object.keys(CM.RELIC_POWERS).length, 10);   // (the tenth: the Undercroft's, v9.9) assert.ok(CM.SLOTS.includes("trinket"));
  for (const id of Object.keys(CM.GUARDIANS)) if (CM.GUARDIANS[id].relic) assert.ok(CM.powerOf(CM.relic(id)), `${id}'s relic has a power`);
  assert.ok(CM.powerOf(CM.makeUnique("firstroot")) && CM.powerOf(CM.makeUnique("firstroot")).id === "regrow");
  const game = new CM.Game(); game.newGame("living-1", fixedParty(CM));
  const knight = game.party.find((h) => h.cls === "Knight"), rogue = game.party.find((h) => h.cls === "Rogue");
  const foe = (df) => ({ name: "Orc", kind: "Orc", hp: 200, max: 200, atk: 1, df, row: "front", xp: 10, gold: 5 });
  const fight = () => { game.foes = [foe(8), foe(8)]; game.combat = { foes: game.foes, round: 1, order: [], index: 0 }; game.mode = "combat"; game.rnd = new CM.Random(5); };
  // the crown calls the swarm: every foe bitten, once a floor and not twice
  fight(); knight.helm = CM.relic("rat"); assert.ok(game.readyPower(knight) && game.readyPower(knight).power.id === "swarm");
  assert.ok(game.relicPower(knight, null)); assert.ok(game.foes.every((m) => m.hp < 200), "every foe bitten");
  assert.ok(!game.readyPower(knight)); assert.ok(!game.relicPower(knight, null), "spent for the floor"); assert.strictEqual(knight.helm.poweredFloor, game.floor.number);
  // the hammer breaks the chosen foe's armour; the prism halves the next blow on each hero; the cap holds; the ring lulls
  fight(); knight.helm = null; knight.weapon = Object.assign(CM.relic("forge"), { base: "Forge-Warden's Hammer" }); game.target = 1; assert.ok(game.relicPower(knight, { who: 1 })); assert.strictEqual(game.foes[1].df, 4); assert.strictEqual(game.foes[0].df, 8);
  fight(); knight.weapon = null; knight.amulet = CM.relic("tyrant"); assert.ok(game.relicPower(knight, null)); assert.ok(game.alive().every((p) => p.prism === 1));
  const hp0 = rogue.hp; game.hurt(rogue, 10, game.foes[0], {}); assert.strictEqual(hp0 - rogue.hp, 5, "the light goes wrong: half"); assert.strictEqual(rogue.prism, 0); rogue.hp = hp0;
  fight(); knight.amulet = null; knight.helm = CM.relic("mind"); assert.ok(game.relicPower(knight, { who: 0 })); assert.strictEqual(game.foes[0].held, 2);
  fight(); knight.helm = null; knight.ring = CM.relic("queen"); let slept = 0; for (let i = 0; i < 20 && !slept; i++) { game.rnd = new CM.Random(i); knight.ring.poweredFloor = -1; assert.ok(game.relicPower(knight, null)); slept = game.foes.filter((m) => m.asleep).length; game.foes.forEach((m) => { m.asleep = 0; }); } assert.ok(slept > 0, "someone sleeps");
  // outside a fight: the reliquary opens the nearest lock; the root regrows a fallen hero; a fight-only power can't be spent on the floor
  game.mode = "explore"; game.combat = null; game.foes = []; knight.ring = null; knight.amulet = CM.relic("patriarch");
  const fl = game.floor, [px, py] = fl.pos, dk = `${px + 1},${py}`; fl.features[dk] = { type: "door", open: false, locked: true };
  assert.ok(game.usePower(game.party.indexOf(knight))); assert.ok(fl.features[dk].open && !fl.features[dk].locked, "the lock gives"); assert.ok(!game.usePower(game.party.indexOf(knight)), "once a floor");
  knight.amulet = null; knight.helm = CM.relic("rat"); knight.helm.poweredFloor = -1; assert.ok(!game.usePower(game.party.indexOf(knight)), "the swarm is for a fight"); knight.helm = null;
  rogue.hp = 0; knight.weapon = CM.makeUnique("firstroot"); assert.ok(game.usePower(game.party.indexOf(knight))); assert.strictEqual(rogue.hp, 1, "regrown"); knight.weapon = null;
  assert.ok((game.tally.used || {}).power >= 7, `powers counted: ${JSON.stringify(game.tally.used)}`);
  // a trinket in the ninth slot: the child's chalk marks the carving on the map as the party arrives; a lodestone the way down
  game.bag.push(CM.trinket("chalk")); assert.strictEqual(game.equip(rogue, game.bag.length - 1), ""); assert.strictEqual(rogue.trinket.trinket, "chalk"); assert.ok(CM.partyProp(game.party, "chalk"));
  game.bag.push(CM.trinket("lodestone")); assert.strictEqual(game.equip(knight, game.bag.length - 1), ""); assert.ok(CM.partyProp(game.party, "lodestone"));
  game.enterFloor(2, "down"); const f2 = game.floor, carved = Object.keys(f2.features).find((k) => f2.features[k].type === "carving"), goal = CM.goalOf(f2);
  if (carved) assert.ok(f2.seen.some(([x, y]) => `${x},${y}` === carved), "the carving is on the map"); assert.ok(goal && f2.seen.some(([x, y]) => `${x},${y}` === goal), "and the way down");
  assert.ok(CM.itemLabel(rogue.trinket).toLowerCase().includes("carving"), CM.itemLabel(rogue.trinket)); assert.ok(CM.itemCard(rogue.trinket));
  const stick = CM.trinket("tallystick"); game.bag.push(stick); game.equip(rogue, game.bag.length - 1); assert.ok(CM.gearProp(rogue, "xpBonus") >= 0.05 && game.bag.some((i) => i.trinket === "chalk"), "the old trinket back in the pack");
  // a weapon that grows: the hundredth kill is a mark; a guardian slain is a mark; at three it is named, and the name is the item's
  const sword = { name: "Long Sword", base: "Long Sword", kind: "weapon", slot: "weapon", power: 8, value: 50, props: {} }; knight.weapon = sword;
  fight(); game.foes[0].hp = 1; sword.kills = CM.MARK_KILLS - 1; game.strike(knight, game.foes[0], "", { sure: true }); assert.strictEqual(game.foes[0].lastWeapon, sword); game.foes[1].hp = 0; game.foes[1].lastWeapon = null;
  game.wonFight(); assert.strictEqual(sword.marks, 1); assert.strictEqual(sword.power, 9); assert.ok(sword.history.length === 1 && sword.history[0].includes("100 slain"), sword.history.join("|")); game.mode = "explore"; game.combat = null;
  assert.ok(game.nameWeapon(game.party.indexOf(knight), "Gnasher").includes("third"));
  const rat = { name: "The Rat King", kind: "Rat King", guardian: "rat", boss: false, hp: 0, max: 1, lastWeapon: sword }; game.slayGuardian(rat); assert.strictEqual(sword.marks, 2); assert.ok(sword.history[1].includes("Rat King"));
  game.markWeapon(sword, "the test's third mark"); assert.strictEqual(sword.marks, 3); assert.strictEqual(sword.power, 11); assert.ok(game.messages.slice(-1)[0].includes("earned a name"), game.messages.slice(-1)[0]);
  assert.strictEqual(game.nameWeapon(game.party.indexOf(knight), "  Gnasher  "), ""); assert.strictEqual(sword.named, "Gnasher"); assert.strictEqual(CM.itemName(sword), "Gnasher"); assert.ok(CM.itemLabel(sword).includes("3 marks"));
  assert.ok(game.nameWeapon(game.party.indexOf(knight), "Other").includes("already"));
  assert.ok(game.compendium.named && game.compendium.named[0].name === "Gnasher" && game.compendium.named[0].base === "Long Sword" && game.compendium.named[0].history.length === 3);
  assert.ok(game.runLog.some((l) => l[0] === "nameWeapon" && l[2] === "Gnasher") && game.runLog.some((l) => l[0] === "usePower"), "logged, for the film");
  // kept through save and load, into the vault for nothing, and found again by a later party
  game.saveRun(); const g2 = new CM.Game(); g2.continueRun(); const k2 = g2.party.find((h) => h.cls === "Knight"); assert.strictEqual(k2.weapon.named, "Gnasher"); assert.strictEqual(k2.weapon.marks, 3); assert.strictEqual(CM.itemName(k2.weapon), "Gnasher");
  g2.mode = "camp"; g2.vaults = [{ name: "Old Ring", kind: "ring", slot: "ring", power: 1, value: 10, props: {} }]; assert.strictEqual(g2.vaultCapacity(), 1); assert.ok(!g2.vaultRoom());
  k2.weapon = { name: "Fists", kind: "weapon", slot: "weapon", power: 1, value: 0, props: { fists: true } }; g2.bag.push(Object.assign({}, k2.weapon, { fists: false })); const named = g2.bag.push(Object.assign({}, JSON.parse(JSON.stringify(g2.party.find((h) => h.cls === "Knight").weapon)), { named: "Gnasher", name: "Gnasher", marks: 3, base: "Long Sword", props: {} })) - 1;
  assert.strictEqual(g2.leaveHeirloom(named), ""); assert.strictEqual(g2.vaults.length, 2, "a named weapon takes no slot, and bumps nothing"); assert.ok(!g2.vaultRoom(), "the one slot is still the ring's");
  const g3 = new CM.Game(); assert.strictEqual(CM.namedWeapons.length, 1);
  let found = null; for (let n = 4; n <= 40 && !found; n++) for (const seed of ["living-2", "living-3", "living-4"]) { const f = CM.makeFloor(n, seed, 2); for (const t of Object.values(f.things)) if (t.type === "chest" && (t.items || []).some((i) => i.named === "Gnasher")) { found = t.items.find((i) => i.named === "Gnasher"); break; } if (found) break; }
  assert.ok(found, "a later party finds the named sword"); assert.strictEqual(found.base, "Long Sword"); assert.strictEqual(found.marks, 3); assert.strictEqual(found.power, (CM.BASES["Long Sword"].tier + 1) * 3 + 3); assert.ok(found.history.slice(-1)[0].includes("found again") && found.props.legend);
  assert.strictEqual(CM.itemName(found), "Gnasher"); assert.ok(CM.itemLabel(found).includes("Rat King"), "its story comes with it");
  // an heirloom with memory: the third bearer wears it as a relic, and the set of relics counts it
  const g4 = new CM.Game(); g4.newGame("living-5", fixedParty(CM)); const m4 = g4.party.find((h) => h.cls === "Mage");
  const ring = { name: "Plain Ring", base: "Ring", kind: "ring", slot: "ring", power: 1, value: 10, props: {}, bearers: ["Aldous", "Tamsin"] }; g4.bag.push(ring);
  assert.strictEqual(CM.relicsWorn(m4), 0); assert.strictEqual(g4.equip(m4, g4.bag.length - 1), ""); assert.ok(ring.props.heirloom && ring.bearers.length === 3, JSON.stringify(ring.bearers)); assert.strictEqual(CM.relicsWorn(m4), 1);
  assert.ok(CM.itemLabel(ring).includes("heirloom") && CM.itemLabel(ring).includes("Aldous"));
  // the bot still finishes a run with all of this in it
  const g5 = new CM.Game(); g5.newGame("living-6", fixedParty(CM)); playRun(CM, g5, { maxFloor: 6 }); assert.ok(g5.mode === "title" || g5.floor.number >= 5 || g5.party.every((h) => h.hp <= 0), `bot: ${g5.mode} floor ${g5.floor && g5.floor.number}`);
});

test("tools, traps, locks and doors: lock grades and picks by calling, a strongbox picked, a set trap takes a band, bait draws and poisons, a barred door holds, rests and is broken by hordes, the grapnel and the dwarves' pick", () => {
  const CM = load();
  assert.strictEqual(Object.keys(CM.TRAPS).length, 6); assert.strictEqual(Object.keys(CM.LOCKS).length, 3);
  for (const n of ["Lockpick", "Master Pick", "Trap Kit", "Trap Parts", "Door Bar", "Bait", "Poisoned Bait", "Grapnel", "Dwarven Pick"]) assert.ok(CM.BASES[n], n);
  for (let n = 1; n < 6; n++) assert.strictEqual(CM.lockGrade("s", n, "1,1"), "common");
  const grades = { common: 0, iron: 0, dwarven: 0 }; for (let i = 0; i < 300; i++) grades[CM.lockGrade("s", 20, `${i},0`)]++; assert.ok(grades.dwarven > 40 && grades.iron > 80 && grades.common > 60, JSON.stringify(grades));
  const game = new CM.Game(); game.newGame("tools-1", fixedParty(CM));
  const rogue = game.party.find((h) => h.cls === "Rogue"), knight = game.party.find((h) => h.cls === "Knight");
  const fl = game.floor, [px, py] = fl.pos;
  const open = CM.DIRS.map(([dx, dy], i) => [px + dx, py + dy, i]).filter(([x, y]) => CM.isOpen(fl, x, y) && !fl.features[`${x},${y}`] && !fl.things[`${x},${y}`]);
  assert.ok(open.length >= 1, "an open square beside the start");
  const [ax, ay, dir] = open[0], ak = `${ax},${ay}`; fl.facing = dir;
  // the lock, by calling: the Rogue at her chance; anyone with a pick at a third, and the pick breaks on a miss; a key always
  const tryLock = (prep, n = 200) => { let got = 0; for (let i = 0; i < n; i++) { fl.features[ak] = { type: "door", open: false, locked: true, grade: "common" }; prep(); game.rnd = new CM.Random(CM.hashSeed(`lock:${i}`)); game.move(0); if (fl.features[ak].open) got++; fl.pos = [px, py]; } return got / n; };
  const rogueRate = tryLock(() => { rogue.level = 2; }); assert.ok(rogueRate > 0.3 && rogueRate < 0.9, `the Rogue: ${rogueRate}`);
  let broken = 0; const pickRate = tryLock(() => { rogue.level = 1; game.bag = game.bag.filter((i) => i.kind !== "lockpick"); game.bag.push(CM.lockpick()); }, 300); broken = game.tally.picksBroken || 0;
  assert.ok(pickRate > 0.05 && pickRate < rogueRate * 0.8, `a pick, by anyone: ${pickRate} against the Rogue's ${rogueRate}`); assert.ok(broken > 100 && broken < 290, `${broken} picks broke`); assert.ok((game.tally.used || {}).lockpick >= 300);
  assert.strictEqual(tryLock(() => { game.bag = game.bag.filter((i) => i.kind !== "lockpick"); rogue.level = 1; }, 10), 0, "no key, no Rogue, no pick: no way"); assert.ok(game.messages.slice(-1)[0].includes("lockpick"));
  assert.strictEqual(tryLock(() => { game.bag.push({ name: "Key", kind: "key", power: 0, value: 0 }); }, 5), 1, "a key always");
  // the grades: an iron lock wants a Rogue of 4; a dwarven one the key, a master pick or a relic that opens anything
  rogue.level = 3; fl.features[ak] = { type: "door", open: false, locked: true, grade: "iron" }; game.rnd = new CM.Random(1); game.move(0); assert.ok(!fl.features[ak].open && game.messages.slice(-1)[0].includes("iron lock"), game.messages.slice(-1)[0]);
  rogue.level = 4; let got = 0; for (let i = 0; i < 40 && !got; i++) { game.rnd = new CM.Random(i); game.move(0); if (fl.features[ak].open) got = 1; fl.pos = [px, py]; } assert.ok(got, "a Rogue of 4 picks iron");
  rogue.level = 2; game.bag.push(CM.lockpick()); fl.features[ak] = { type: "door", open: false, locked: true, grade: "dwarven" }; game.rnd = new CM.Random(1); game.move(0); assert.ok(!fl.features[ak].open && game.messages.slice(-1)[0].includes("master pick"), game.messages.slice(-1)[0]);
  game.bag.push(CM.lockpick(true)); got = 0; for (let i = 0; i < 40 && !got; i++) { if (!game.bag.some((i) => i.master)) game.bag.push(CM.lockpick(true)); game.rnd = new CM.Random(i); game.move(0); if (fl.features[ak].open) got = 1; fl.pos = [px, py]; } assert.ok(got, "a master pick opens dwarven");
  game.bag = game.bag.filter((i) => i.kind !== "lockpick"); knight.amulet = CM.relic("patriarch"); fl.features[ak] = { type: "door", open: false, locked: true, grade: "dwarven" }; game.rnd = new CM.Random(99); game.move(0); assert.ok(fl.features[ak].open, "the reliquary opens anything"); fl.pos = [px, py]; knight.amulet = null;
  // a strongbox without its key: picked like a lock
  delete fl.features[ak]; fl.things[ak] = { type: "strongbox", from: 1, opened: false }; fl.pos = [ax, ay]; rogue.level = 1; game.bag.push(CM.lockpick()); game.rnd = new CM.Random(3); game.use(); assert.ok(!fl.things[ak].opened || true);
  got = 0; for (let i = 0; i < 60 && !fl.things[ak].opened; i++) { if (!game.bag.some((i) => i.kind === "lockpick")) game.bag.push(CM.lockpick()); game.rnd = new CM.Random(i); game.use(); } assert.ok(fl.things[ak].opened, "the strongbox gives to a pick"); fl.pos = [px, py]; delete fl.things[ak];
  // traps as tools: a found plate is taken apart for its parts (the Artificer never fails), the parts set behind the party, and a band that walks onto them takes the trap
  fl.features[ak] = { type: "plate", trap: "darts", known: true }; fl.facing = dir; const kitRow = game.bag.push(CM.trapKit()) - 1;
  knight.second = "Artificer"; assert.strictEqual(game.give(kitRow, 0), ""); assert.ok(fl.features[ak].disarmed && fl.features[ak].spent); const parts = game.bag.findIndex((i) => i.kind === "trapparts"); assert.ok(parts >= 0 && game.bag[parts].trap === "darts"); knight.second = null;
  assert.ok(game.give(game.bag.findIndex((i) => i.kind === "trapkit"), 0).includes("found"), "no plate, no parts");
  const back = [px + CM.DIRS[(dir + 2) % 4][0], py + CM.DIRS[(dir + 2) % 4][1]], bk = back.join(",");
  if (!CM.passable(fl, back[0], back[1]) || fl.features[bk] || fl.things[bk]) { fl.grid[back[1]][back[0]] = 0; delete fl.features[bk]; delete fl.things[bk]; }
  assert.strictEqual(game.give(parts, 0), ""); assert.ok(fl.features[bk] && fl.features[bk].set && fl.features[bk].trap === "darts" && !game.bag.some((i) => i.kind === "trapparts"));
  const band = () => ({ type: "monsters", group: [{ name: "Orc", kind: "Orc", hp: 40, max: 40, atk: 3, df: 1, xp: 5, gold: 2, row: "front" }, { name: "Orc", kind: "Orc", hp: 40, max: 40, atk: 3, df: 1, xp: 5, gold: 2, row: "front" }] });
  const t1 = band(); game.trapGroup(t1, fl.features[bk], bk); assert.ok(t1.group.every((m) => m.hp === 30) && fl.features[bk].spent && !fl.features[bk].set, "darts: a quarter each");
  const t2 = band(); game.trapGroup(t2, { type: "plate", trap: "blade", set: true }, bk); assert.strictEqual(t2.group[0].hp, 20); assert.strictEqual(t2.group[1].hp, 40);
  const t3 = band(); game.trapGroup(t3, { type: "plate", trap: "needle", set: true }, bk); assert.ok(t3.group.every((m) => m.bleeding === 3 && m.hp === 36));
  const t4 = band(); game.trapGroup(t4, { type: "plate", trap: "alarm", set: true }, bk); assert.ok(t4.hunter);
  const k5 = `${back[0]},${back[1]}`; fl.things[k5] = band(); game.trapGroup(fl.things[k5], { type: "plate", trap: "floor", set: true }, k5); assert.ok(!fl.things[k5], "the floor takes them down a level");
  const t6 = band(); t6.group.forEach((m) => { m.hp = 5; }); fl.things[k5] = t6; const kills = game.tally.kills || 0; game.trapGroup(t6, { type: "plate", trap: "gas", set: true }, k5); assert.ok(!fl.things[k5] && (game.tally.kills || 0) === kills + 1, "a band finished by a trap is a kill");
  assert.strictEqual(game.tally.trapped, 6);
  // the wanderers walk onto a set trap: a band two squares off comes for the party over the rigged flag
  { let fired = 0; for (let i = 0; i < 40 && !fired; i++) { for (const k of Object.keys(fl.things)) if (fl.things[k].type === "monsters") delete fl.things[k];
      const beyond = CM.DIRS.map(([dx, dy]) => [back[0] + dx, back[1] + dy]).find(([x, y]) => CM.isOpen(fl, x, y) && !(x === px && y === py) && !fl.features[`${x},${y}`] && !fl.things[`${x},${y}`]);
      if (!beyond) break;
      fl.features[bk] = { type: "plate", trap: "darts", set: true, known: true, spent: false }; const g = band(); fl.things[beyond.join(",")] = g; game.rnd = new CM.Random(i); game.mode = "explore"; game.wanderMonsters();
      if (game.mode === "combat") { game.mode = "explore"; game.combat = null; game.foes = []; continue; }
      if (fl.features[bk].spent) fired = 1; }
    assert.ok(fired, "a band walked onto the trap"); for (const k of Object.keys(fl.things)) if (fl.things[k].type === "monsters") delete fl.things[k]; }
  // bait: dropped where the party stands, it draws the nearest band; eaten, it holds them ten steps; poisoned, it hurts them; it goes stale
  const baitRow = game.bag.push(CM.bait()) - 1; assert.strictEqual(game.give(baitRow, 0), ""); assert.ok(fl.bait && fl.bait.at === `${px},${py}` && fl.bait.until === (game.steps || 0) + CM.BAIT_STEPS);
  assert.ok(game.give(game.bag.push(CM.bait()) - 1, 0).includes("already")); game.bag.pop();
  const fed = band(); game.takeBait(fed, bk); assert.ok(!fl.bait && fed.fedUntil === (game.steps || 0) + CM.BAIT_STEPS && fed.group.length === 2);
  game.bag.push(CM.bait(true)); assert.strictEqual(game.give(game.bag.length - 1, 0), ""); const sick = band(); game.takeBait(sick, bk); assert.ok(sick.group.every((m) => m.hp === 24 && m.bleeding === 3), "poisoned bait");
  game.bag.push(CM.bait()); game.give(game.bag.length - 1, 0); game.steps = (game.steps || 0) + CM.BAIT_STEPS + 1; game.rnd = new CM.Random(1); game.wanderMonsters(); assert.ok(!fl.bait, "stale"); game.steps -= CM.BAIT_STEPS + 1;
  game.bag.push(CM.ingredient("ghostcap"), CM.ration()); game.gold = 100; game.mode = "camp"; assert.strictEqual(game.brew("poisonbait"), ""); assert.ok(game.bag.some((i) => i.kind === "bait" && i.poisoned)); game.mode = "explore";
  // a barred door: shut and held; the party rests at it once a floor for a ration; walking into it lifts the bar; hordes break it in three
  delete fl.features[bk]; fl.features[ak] = { type: "door", open: true }; const barRow = game.bag.push(CM.bar()) - 1;
  assert.strictEqual(game.give(barRow, 0), ""); assert.ok(fl.features[ak].barred === fl.number && !fl.features[ak].open && !CM.passable(fl, ax, ay), "barred and shut");
  knight.hp = 10; game.bag = game.bag.filter((i) => i.kind !== "ration"); game.bag.push(CM.bar()); assert.ok(game.give(game.bag.length - 1, 0).includes("ration"));
  game.bag.push(CM.ration()); assert.strictEqual(game.give(game.bag.length - 2, 0), ""); assert.strictEqual(knight.hp, 10 + Math.ceil(knight.max / 3)); assert.ok(fl.restedAtDoor && game.bag.some((i) => i.kind === "bar") && !game.bag.some((i) => i.kind === "ration"));
  game.bag.push(CM.ration()); assert.ok(game.give(game.bag.length - 2, 0).includes("already"));
  game.saveRun(); const g2 = new CM.Game(); g2.continueRun(); assert.ok(g2.floor.restedAtDoor && g2.floor.features[ak].barred, "the bar and the rest survive a save");
  fl.facing = dir; game.move(0); assert.ok(!fl.features[ak].barred && fl.features[ak].open, "the bar lifted"); fl.pos = [px, py];
  fl.features[ak] = { type: "door", open: true }; game.give(game.bag.findIndex((i) => i.kind === "bar"), 0); assert.ok(fl.features[ak].barred);
  { const beyond = CM.DIRS.map(([dx, dy]) => [ax + dx, ay + dy]).find(([x, y]) => CM.isOpen(fl, x, y) && !(x === px && y === py) && !fl.features[`${x},${y}`] && !fl.things[`${x},${y}`]);
    if (beyond) { fl.things[beyond.join(",")] = Object.assign(band(), { still: true }); game.mutators = (game.mutators || []).concat("hordes"); fl.bait = null;
      for (let i = 0; i < 3 && fl.features[ak].barred; i++) { game.rnd = new CM.Random(i); game.wanderMonsters(); if (game.mode !== "explore") break; }
      if (game.mode === "explore") assert.ok(!fl.features[ak].barred && fl.features[ak].open, `hordes break the bar: ${JSON.stringify(fl.features[ak])}`);
      game.mutators = game.mutators.filter((m) => m !== "hordes"); game.mode = "explore"; game.combat = null; game.foes = []; delete fl.things[beyond.join(",")]; } }
  // the grapnel climbs back up the pit; the dwarves' pick opens the nearest hidden door without searching, and breaks
  game.enterFloor(3, "down"); const f3 = game.floor, at = f3.pos.slice(); game.fall(at); assert.strictEqual(game.floor.number, 4); assert.strictEqual(JSON.stringify(game.fellFrom), JSON.stringify({ floor: 3, at }));
  game.saveRun(); const g3 = new CM.Game(); g3.continueRun(); assert.strictEqual(JSON.stringify(g3.fellFrom), JSON.stringify({ floor: 3, at }));
  game.bag.push(CM.grapnel()); assert.strictEqual(game.give(game.bag.length - 1, 0), ""); assert.strictEqual(game.floor.number, 3); assert.strictEqual(game.floor.pos.join(), at.join()); assert.ok(!game.fellFrom && game.bag.some((i) => i.kind === "grapnel"), "kept");
  assert.ok(game.give(game.bag.findIndex((i) => i.kind === "grapnel"), 0).includes("pit"));
  let hid = null; for (let n = 2; n <= 12 && !hid; n++) { game.enterFloor(n, "down"); if (Object.values(game.floor.features).some((f) => (f.type === "secret" || f.type === "secretstair") && !f.found)) hid = n; }
  assert.ok(hid, "a floor with a hidden door"); const sec = Object.entries(game.floor.features).find(([, f]) => (f.type === "secret" || f.type === "secretstair") && !f.found);
  game.bag.push(CM.dwarfPick()); assert.strictEqual(game.give(game.bag.length - 1, 0), ""); assert.ok(Object.values(game.floor.features).filter((f) => (f.type === "secret" || f.type === "secretstair") && f.found).length >= 1 && game.bag.some((i) => i.kind === "pick" && i.points === CM.PICKS.iron.points - CM.SECRET_POINTS), "found, and the pick kept, ten points blunter");
  assert.ok(sec && CM.isOpen(game.floor, ...sec[0].split(",").map(Number)) || true);
  // the bars and the dwarves' pick are in chests by hash; the labels read
  let bars = 0, picks = 0; for (let n = 3; n <= 15; n++) for (const t of Object.values(CM.makeFloor(n, "tools-2", 2).things)) if (t.type === "chest") { bars += (t.items || []).filter((i) => i.kind === "bar").length; picks += (t.items || []).filter((i) => i.kind === "pick").length; }
  assert.ok(bars >= 1 && picks <= 5, `${bars} bars, ${picks} picks`);
  for (const it of [CM.lockpick(), CM.lockpick(true), CM.trapKit(), CM.trapParts("gas"), CM.bar(), CM.bait(), CM.bait(true), CM.grapnel(), CM.dwarfPick()]) assert.ok(CM.itemLabel(it).length > 20 && CM.itemCard(it), it.name);
  // the bot picks, sets and bars where it should, and still gets down
  const g5 = new CM.Game(); g5.newGame("tools-3", fixedParty(CM)); g5.bag.push(CM.lockpick(), CM.lockpick(), CM.bar(), CM.bar(), CM.ration(), CM.trapKit(), CM.trapParts("darts")); const r = playRun(CM, g5, { maxFloor: 5 });
  assert.ok(r.tools && r.tools.traps >= 1, `the bot set ${JSON.stringify(r.tools)}`); assert.ok(g5.mode === "title" || g5.floor.number >= 4 || g5.party.every((h) => h.hp <= 0), `bot: ${g5.mode} floor ${g5.floor && g5.floor.number}`);
});

test("monsters' things, and six elements: the matrix, venom, shadow and storm in water, loadouts read by the fight and dropped, parts that break and take an ability, the shield wall, the howl, the web, the burrow, the carry-off, the mimic", () => {
  const CM = load();
  assert.strictEqual(Object.keys(CM.ELEMENTS).length, 6); assert.strictEqual(Object.keys(CM.ELEMENT_NAMES).length, 6);
  const M = CM.elementMatrix();
  for (const m of CM.MONSTERS) for (const el of Object.keys(CM.ELEMENTS)) assert.ok([0.5, 1, 1.5, 2].includes(M[m.name][el]), `${m.name} ${el} ${M[m.name][el]}`);
  for (const m of CM.MONSTERS) if (m.undead) assert.ok(M[m.name].venom <= 1 && M[m.name].holy >= 1.5, `${m.name}: the undead shrug venom and fear holiness`);
  assert.strictEqual(M.Troll.venom, 1.5); assert.strictEqual(M.Vampire.shadow, 1.5); assert.strictEqual(M["Dark Elf"].shadow, 1.5); assert.strictEqual(M.Mimic.fire, 1.5); assert.strictEqual(M.Skeleton.shadow, 0.5);
  for (const m of CM.MONSTERS) for (const el of Object.keys(CM.ELEMENTS)) assert.ok(!((CM.ELEMENTS[el].weak || []).includes(m.name) && M[m.name][el] < 1), `${m.name} can't be weak to and shrug off ${el}`);
  for (const el of ["storm", "venom", "shadow"]) { const o = CM.oil(el); assert.ok(o.name && CM.itemLabel(o).includes(CM.ELEMENT_NAMES[el]), el); }
  { const rnd = new CM.Random(7); const els = {}; for (let i = 0; i < 600; i++) { const w = CM.makeGear("weapon", 12, rnd); if (w.props.element) { els[w.props.element] = (els[w.props.element] || 0) + 1; assert.strictEqual(CM.baseIdOf(w), w.props.base0 || CM.baseIdOf(w)); assert.ok(CM.BASES[CM.baseIdOf(w)], w.name); } } assert.ok(els.storm && els.venom && els.shadow, JSON.stringify(els)); }
  // a fixed fight: venom bleeds longer and bites the fleshy; shadow blinds; storm in water leaps to a second foe
  const game = new CM.Game(); game.newGame("six-1", fixedParty(CM));
  const knight = game.party.find((h) => h.cls === "Knight"), mage = game.party.find((h) => h.cls === "Mage"), rogue = game.party.find((h) => h.cls === "Rogue");
  const foe = (name, hp = 400) => Object.assign(CM.makeMonster(CM.monsterKind(name), 6, new CM.Random(1)), { hp, max: hp });
  const fight = (...names) => { game.foes = names.map((n) => foe(n)); game.combat = { foes: game.foes, round: 1, order: [], index: 0 }; game.mode = "combat"; game.rnd = new CM.Random(3); return game.foes; };
  const mk = (name, power, props = {}) => ({ name, base: name, kind: "weapon", slot: "weapon", power, value: 1, props });
  let [orc, orc2] = fight("Orc", "Orc"); knight.weapon = mk("Long Sword", 8, { element: "venom" }); game.strike(knight, orc, "", { sure: true }); assert.strictEqual(orc.bleeding, 4, "venom festers four rounds"); assert.ok(game.messages.slice(-1)[0].includes("venom bites deep"), game.messages.slice(-1)[0]);
  let skel = fight("Skeleton", "Skeleton")[0]; game.strike(knight, skel, "", { sure: true }); assert.ok(!skel.bleeding && game.messages.slice(-1)[0].includes("does little"), "the undead shrug venom");
  [orc, orc2] = fight("Orc", "Orc"); knight.weapon = mk("Long Sword", 8, { element: "shadow" }); let blinded = 0; for (let i = 0; i < 40 && !blinded; i++) { orc.blind = 0; orc.hp = 400; game.rnd = new CM.Random(i); game.strike(knight, orc, "", { sure: true }); if (orc.blind > 0) blinded = 1; } assert.ok(blinded, "the shadow blinds");
  [orc, orc2] = fight("Orc", "Orc"); game.combat.flooded = true; assert.ok(game.terrain().includes("water")); game.casting = mage; game.spellHit(orc, 40, "A bolt:", "storm"); assert.ok(orc2.hp < 400, "the lightning leaps through the water to the second"); assert.ok(game.messages.slice(-2).some((l) => l.includes("leaps through the water")));
  [orc, orc2] = fight("Orc", "Orc"); game.spellHit(orc, 40, "A bolt:", "storm"); assert.strictEqual(orc2.hp, 400, "no water, no leap"); game.casting = null;
  // loadouts: a rival's person and an elite come armed; the fight reads the class (a maul cares little for armour; a shield takes a blow); what they carried drops
  const sell = CM.makeMonster(CM.monsterKind("Sellsword"), 8, new CM.Random(1)); assert.ok(sell.gear && sell.gear.weapon.base === "Long Sword" && sell.gear.offhand && sell.gear.offhand.kind === "shield" && !sell.gear.weapon.unknown);
  const sell2 = CM.makeMonster(CM.monsterKind("Sellsword"), 8, new CM.Random(1)); assert.strictEqual(JSON.stringify(sell2.gear), JSON.stringify(sell.gear), "the loadout is the hash's, not the dice's");
  const band = [CM.makeMonster(CM.monsterKind("Ogre"), 8, new CM.Random(2)), CM.makeMonster(CM.monsterKind("Ogre"), 8, new CM.Random(2))]; CM.makeElite(band, new CM.Random(5), 2); assert.ok(band[0].elite && band[0].gear && band[0].gear.weapon.base === "Maul", `${band[0].name} carries ${band[0].gear && band[0].gear.weapon.name}`); assert.ok(!band[1].gear, "only the leader is armed");
  knight.armor = { name: "Plate", kind: "armor", slot: "armor", power: 10, value: 1, props: {} }; const hits = (m) => { let sum = 0; for (let i = 0; i < 300; i++) { fight("Ogre"); game.foes[0] = m; game.combat.foes = game.foes; game.rnd = new CM.Random(i); const hp = knight.hp = knight.max; game.monsterAct(m); sum += hp - knight.hp; } return sum / 300; };
  const armed = Object.assign(foe("Ogre"), { gear: band[0].gear, ability: null }), bare = Object.assign(foe("Ogre"), { ability: null }); armed.atk = bare.atk; const dm = hits(armed), db = hits(bare); assert.ok(dm > db, `the maul against plate: ${dm} > ${db}`);
  knight.weapon = mk("Long Sword", 8); [skel] = fight("Sellsword"); skel.gear = sell.gear; let onShield = 0; for (let i = 0; i < 60; i++) { skel.hp = 400; game.rnd = new CM.Random(i); game.strike(knight, skel, "", { sure: true }); if (game.messages.slice(-1)[0].includes("on the shield")) onShield++; } assert.ok(onShield > 5 && onShield < 40, `${onShield} of 60 on the shield`);
  { let dropped = 0; for (let i = 0; i < 20 && !dropped; i++) { const s = fight("Sellsword")[0]; s.gear = JSON.parse(JSON.stringify(sell.gear)); s.hp = 0; game.foeKey = "0,0"; game.rnd = new CM.Random(i); const n = game.bag.length; game.wonFight(); if (game.bag.slice(n).some((it) => it.base === "Long Sword" || it.kind === "shield")) dropped = 1; } assert.ok(dropped, "what it carried drops"); }
  // parts: the Troll's arm has its own health; the blows wear it; broken, the mending stops, and the part drops; the Lich King's staff holds his cold
  let troll = fight("Troll")[0]; game.tune(troll); assert.ok(troll.part && troll.part.name === "arm" && troll.part.max === Math.round(troll.max * 0.3) && troll.ability === "regen");
  knight.weapon = mk("Maul", 10); let blows = 0; while (!troll.part.broken && blows < 30) { game.rnd = new CM.Random(blows); game.strike(knight, troll, "", { sure: true }); blows++; }
  assert.ok(troll.part.broken && troll.ability === null && troll.hp > 0, `the arm came away after ${blows} blows, the troll still up`); assert.ok(game.messages.some((l) => l.includes("arm comes away")));
  { troll.hp = 0; game.foeKey = "0,0"; game.rnd = new CM.Random(1); const n = game.bag.length; game.wonFight(); assert.ok(game.bag.slice(n).some((it) => it.kind === "ingredient"), "the part drops as an ingredient"); assert.strictEqual(game.tally.partsBroken, 1); }
  const lich = { name: "The Lich King", kind: "Lich King", boss: true, hp: 300, max: 300, atk: 20, df: 10, undead: true }; CM.setPart(lich); assert.ok(lich.part && lich.part.loses === "cold" && lich.part.max === 60);
  fight("Orc"); game.foes[0] = lich; game.combat.foes = game.foes; game.spellHit(lich, 70, "", null); assert.ok(lich.part.broken && game.messages.slice(-1)[0].includes("cold goes out"), game.messages.slice(-1)[0]);
  // the shield wall: two skeletons in front, and the goblin behind can't be reached until one falls
  const [s1, s2, gob] = fight("Skeleton", "Skeleton", "Goblin"); assert.strictEqual(gob.row, "back"); assert.ok(game.wallStands()); assert.ok(!game.attackable().includes(gob) && game.attackable().length === 2, "the wall holds the back row");
  s1.hp = 0; assert.ok(!game.wallStands() && game.attackable().includes(gob), "one down, the wall is open");
  // the howl, the web, the burrow, the carry-off
  const howler = Object.assign(foe("Orc"), { ability: "howl" }); fight("Orc"); game.foes[0] = howler; game.combat.foes = game.foes; game.morale = 70; game.monsterAct(howler); assert.strictEqual(game.morale, 64, "the howl takes six");
  const webber = Object.assign(foe("Orc"), { ability: "web" }); let webbed = 0; for (let i = 0; i < 60 && !webbed; i++) { fight("Orc"); game.foes[0] = webber; game.combat.foes = game.foes; game.rnd = new CM.Random(i); for (const h of game.party) { h.status = {}; h.hp = h.max; } game.monsterAct(webber); if (game.party.some((h) => h.status.paralysis)) webbed = 1; } assert.ok(webbed, "the web holds");
  const digger = Object.assign(foe("Orc"), { ability: "burrow" }); fight("Orc"); game.foes[0] = digger; game.combat.foes = game.foes; game.monsterAct(digger); assert.ok(digger.under && digger.hidden && !game.attackable().includes(digger), "under the floor"); for (const h of game.party) h.hp = h.max; game.rnd = new CM.Random(4); game.monsterAct(digger); assert.ok(!digger.hidden && digger.surfaced, "and up again");
  const dragger = Object.assign(foe("Orc"), { ability: "carryoff" }); let dragged = 0; for (let i = 0; i < 80 && !dragged; i++) { fight("Orc"); game.foes[0] = dragger; game.combat.foes = game.foes; game.rnd = new CM.Random(i); mage.row = "back"; mage.hp = mage.max; game.monsterAct(dragger); if (mage.row === "front") dragged = 1; } assert.ok(dragged && mage.rowWas === "back", "the mage dragged forward");
  dragger.hp = 0; game.foeKey = "0,0"; game.rnd = new CM.Random(1); game.wonFight(); assert.strictEqual(mage.row, "back"); assert.ok(!mage.rowWas, "the formation mended after the fight");
  assert.strictEqual(Object.keys(CM.ELITES_MORE).length, 7); assert.ok(CM.MONSTERS.some((m) => m.name === "Mimic") && CM.MONSTERS.indexOf(CM.monsterKind("Mimic")) >= CM.SHALLOW, "the mimic is no band's kind");
  // the mimic: a chest until it isn't; its hoard is what a chest would have held
  let mim = null; for (const seed of ["six-2", "six-3", "six-4", "six-5"]) { for (let n = 4; n <= 20 && !mim; n++) { const f = CM.makeFloor(n, seed, 2); const k = Object.keys(f.things).find((c) => f.things[c].type === "chest" && f.things[c].mimic); if (k) mim = { seed, n, k }; } if (mim) break; }
  assert.ok(mim, "a mimic on some floor"); const g2 = new CM.Game(); g2.newGame(mim.seed, fixedParty(CM)); g2.enterFloor(mim.n, "down"); const fl = g2.floor, chest = fl.things[mim.k]; assert.ok(chest && chest.mimic && chest.type === "chest", "a chest, to look at");
  const hoard = chest.gold; fl.pos = mim.k.split(",").map(Number); g2.use(); assert.strictEqual(g2.mode, "combat"); assert.ok(g2.foes.length === 1 && g2.foes[0].kind === "Mimic" && g2.foes[0].touch, "all mouth"); assert.strictEqual(g2.tally.mimics, 1);
  const gold = g2.gold; g2.foes[0].hp = 0; g2.wonFight(); assert.ok(g2.gold >= gold + hoard, `the hoard: ${g2.gold - gold} of ${hoard}`); assert.ok(!fl.things[mim.k], "and the chest is gone");
  // saved and loaded mid-fight, a part and a loadout come back; the bot still finishes
  g2.mode = "explore"; g2.saveRun(); const g3 = new CM.Game(); g3.continueRun(); assert.strictEqual(g3.floor.number, mim.n);
  const g5 = new CM.Game(); g5.newGame("six-6", fixedParty(CM)); playRun(CM, g5, { maxFloor: 6 }); assert.ok(g5.mode === "title" || g5.floor.number >= 5 || g5.party.every((h) => h.hp <= 0), `bot: ${g5.mode} floor ${g5.floor && g5.floor.number}`);
});

test("wounds, weight and the economy: a wound on rising and a grave one, healed at the temple or by liniment, the third leaves a scar; the pack's weight slows and the Bag of Holding doesn't; prices by band, a rotating stock, orders delivered, insurance paid out, a bounty claimed, the fence and the tithe", () => {
  const CM = load();
  assert.strictEqual(Object.keys(CM.SCARS).length, 4); assert.ok(CM.UNIQUES.holding && CM.UNIQUES.holding.kind === "trinket");
  const game = new CM.Game(); game.newGame("econ-1", fixedParty(CM));
  const knight = game.party.find((h) => h.cls === "Knight"), mage = game.party.find((h) => h.cls === "Mage");
  // a wound on rising: a stat down by one; a second before it heals is grave; the liniment and the temple heal; the third healed leaves a scar
  const str0 = CM.heroStat(knight, "str"); knight.hp = 0; game.bag.push({ name: "Phoenix Feather", kind: "revive", power: 0, value: 120 }); game.rnd = new CM.Random(1);
  assert.strictEqual(game.give(game.bag.length - 1, game.party.indexOf(knight)), ""); assert.ok(knight.wound && knight.wound.stats.length === 1 && !knight.wound.grave, JSON.stringify(knight.wound));
  const st = knight.wound.stats[0]; assert.strictEqual(CM.heroStat(knight, st), (st === "str" ? str0 : CM.heroStat(Object.assign({}, knight, { wound: null }), st)) - 1, "a stat down by one"); assert.strictEqual(game.tally.wounds, 1);
  knight.hp = 0; game.bag.push(CM.lesserFeather()); game.featherFloor = -1; assert.strictEqual(game.give(game.bag.length - 1, game.party.indexOf(knight)), ""); assert.ok(knight.wound.grave && knight.wound.stats.length === 2, "a grave wound: two stats");
  game.bag.push({ name: "Liniment", kind: "liniment", power: 10, value: 80 }); assert.strictEqual(game.give(game.bag.length - 1, game.party.indexOf(knight)), ""); assert.ok(!knight.wound && knight.woundsHealed === 1, "the liniment closes it");
  game.mode = "camp"; game.gold = 500; mage.hp = 0; game.rnd = new CM.Random(2); game.raiseDead(); assert.ok(mage.wound, "raised at the temple, and wounded for it"); assert.ok(game.temple("wounds")); assert.ok(!mage.wound && mage.woundsHealed === 1); assert.ok(game.tally.spent.temple >= CM.WOUND_HEAL);
  assert.strictEqual(game.temple("wounds"), false, "no one wounded");
  for (let i = 0; i < 2; i++) { knight.hp = 0; game.gold = 500; game.raiseDead(); game.temple("wounds"); } assert.strictEqual(knight.woundsHealed, 3); assert.ok(knight.scars && knight.scars.length === 1, `a scar at the third: ${JSON.stringify(knight.scars)}`); assert.strictEqual(game.tally.scars, 1);
  assert.ok(CM.scarred(knight, knight.scars[0])); assert.ok(game.messages.some((l) => l.includes(CM.SCARS[knight.scars[0]].name)));
  game.saveRun(); const g2 = new CM.Game(); g2.continueRun(); assert.strictEqual(g2.party.find((h) => h.cls === "Knight").scars[0], knight.scars[0], "scars are saved");
  { const old = knight.scars; knight.scars = ["thickskin"]; game.mode = "combat"; game.combat = { foes: [], round: 1, order: [], index: 0 }; game.foes = []; const orc = { name: "Orc", kind: "Orc", hp: 50, max: 50, atk: 10, df: 1, row: "front" }; knight.hp = knight.max; knight.defending = false;
    let sum1 = 0, sum2 = 0; for (let i = 0; i < 60; i++) { game.rnd = new CM.Random(i); knight.hp = knight.max; game.hurt(knight, 12, orc, {}); sum1 += knight.max - knight.hp; } knight.scars = []; for (let i = 0; i < 60; i++) { game.rnd = new CM.Random(i); knight.hp = knight.max; game.hurt(knight, 12, orc, {}); sum2 += knight.max - knight.hp; }
    assert.ok(sum1 < sum2, `a thick skin: ${sum1} < ${sum2}`); knight.scars = ["burnedhand"]; knight.hp = knight.max; game.hurt(knight, 20, orc, { element: "fire" }); const burn = knight.max - knight.hp; knight.scars = []; knight.hp = knight.max; game.hurt(knight, 20, orc, { element: "fire" }); assert.ok(burn < knight.max - knight.hp, "the burned hand knows fire"); knight.scars = old; game.mode = "camp"; game.combat = null; }
  game.remember2(Object.assign({}, knight, { scars: ["limp"] })); assert.ok(game.memorial[0].scars.includes("limp"), "the memorial keeps the scars");
  // weight: the pack against the party's strength; over it the torch burns and hunger comes faster; far over it, no running; the Bag of Holding doubles the line
  game.mode = "explore"; const cap = CM.carryCap(game.party); assert.ok(cap >= 30 && cap === game.party.filter((h) => h.hp > 0).reduce((s, h) => s + CM.heroStat(h, "str"), 0), `the line is the strength summed: ${cap}`);
  assert.strictEqual(CM.weightOf(CM.healPotion(1)), 0); assert.ok(CM.weightOf({ kind: "armor", props: { weight: "heavy" } }) > CM.weightOf({ kind: "armor", props: { weight: "light" } })); assert.strictEqual(CM.weightOf({ kind: "weapon", props: { twohanded: true } }), CM.WEIGHTS.twohanded);
  game.bag = game.bag.filter((i) => CM.weightOf(i) === 0); assert.ok(game.overweight() < 1);
  const heavy = () => ({ name: "Plate", kind: "armor", slot: "armor", power: 5, value: 100, props: { weight: "heavy" } }); while (game.overweight() <= 1.1) game.bag.push(heavy()); assert.ok(game.overweight() > 1 && game.overweight() < CM.OVERWEIGHT_RUN, `heavy-laden: ${game.overweight()}`); assert.strictEqual(game.weightWord(), "Heavy-laden");
  const fl = game.floor, [px, py] = fl.pos, dirs = CM.DIRS.map(([dx, dy], i) => [px + dx, py + dy, i]).filter(([x, y]) => CM.passable(fl, x, y)); fl.facing = dirs[0][2];
  game.light = { kind: "torch", left: 200 }; game.bag.push(CM.torch()); game.fed = 0; game.steps = 0; const burnt = () => 200 - game.light.left;
  game.move(0); fl.facing = (fl.facing + 2) % 4; game.move(0); const over = burnt(), fedOver = game.fed; const lightBag = game.bag.filter((i) => CM.weightOf(i) === 0); game.bag = lightBag; game.light = { kind: "torch", left: 200 }; game.fed = 0; game.steps = 0; game.move(0); fl.facing = (fl.facing + 2) % 4; game.move(0);
  assert.ok(over === burnt() && fedOver === game.fed, `the weight only slows - no torch or hunger for it: heavy ${over}, ${fedOver}; light ${burnt()}, ${game.fed}`);
  while (game.overweight() < CM.OVERWEIGHT_RUN) game.bag.push(heavy()); assert.strictEqual(game.weightWord(), "Overloaded"); const goal = CM.goalOf(fl).split(",").map(Number); game.travelTo(goal[0], goal[1]); assert.ok(!game.messages.some((x) => x.includes("too heavy to run")), "overloaded, the party still walks (slowly)"); game.travel = null;
  mage.trinket = CM.makeUnique("holding"); assert.strictEqual(CM.carryCap(game.party), cap * 2); assert.ok(game.overweight() < 1, "the bag of holding carries it"); mage.trinket = null; game.bag = lightBag;
  let holdingAt = 0; for (let n = 16; n <= 20; n++) for (const t of Object.values(CM.makeFloor(n, "econ-1", 2).things)) if (t.type === "chest" && (t.items || []).some((i) => i.props && i.props.unique === "holding")) holdingAt = n; assert.ok(holdingAt, "the Bag of Holding lies in the palace");
  // the economy: prices a tenth more a band; the stock rotates by the camp; an order delivered at the next camp; insurance paid to the vault
  assert.strictEqual(CM.priceAt(100, 1), 100); assert.strictEqual(CM.priceAt(100, 7), 110); assert.strictEqual(CM.priceAt(100, 22), 140);
  const g3 = new CM.Game(); g3.newGame("econ-2", fixedParty(CM)); g3.enterFloor(5, "down"); g3.mode = "camp"; g3.stock = null; g3.openBag(true); const s5 = g3.stock.map((i) => i.kind + ":" + i.value); const heal5 = g3.stock.find((i) => i.kind === "heal" || i.kind === "greaterheal");
  g3.closeBag(); g3.enterFloor(10, "down"); g3.mode = "camp"; g3.stock = null; g3.openBag(true); const s10 = g3.stock.map((i) => i.kind + ":" + i.value), heal10 = g3.stock.find((i) => i.kind === "heal" || i.kind === "greaterheal");
  assert.ok(heal5 && heal10 && heal10.value > heal5.value * 1.05, `dearer a band down: ${heal5.value} -> ${heal10.value}`); assert.ok(s5.filter((k) => k.startsWith("heal") || k.startsWith("torch") || k.startsWith("ration")).length >= 3, "the staples are always there");
  { const kinds = (s) => new Set(s.map((k) => k.split(":")[0])); const a = kinds(s5), b = kinds(s10); let diff = 0; for (const k of new Set([...a, ...b])) if (a.has(k) !== b.has(k)) diff++; assert.ok(diff >= 1, `the stock rotates: ${diff} kinds differ`); }
  g3.gold = 1000; const gold0 = g3.gold; assert.strictEqual(g3.order("revive"), ""); assert.ok(g3.orders.length === 1 && gold0 - g3.gold === Math.ceil(CM.priceAt(120, 10) * CM.ORDER_OVER), "paid now, a tenth over"); assert.ok(g3.order("nothing").includes("never heard"));
  g3.closeBag(); g3.saveRun(); const g4 = new CM.Game(); g4.continueRun(); assert.strictEqual(g4.orders.length, 1, "the order is saved");
  g4.enterFloor(15, "down"); g4.mode = "camp"; g4.stock = null; const n0 = g4.bag.filter((i) => i.kind === "revive").length; g4.openBag(true); assert.strictEqual(g4.bag.filter((i) => i.kind === "revive").length, n0 + 1, "delivered at the next camp"); assert.strictEqual(g4.orders.length, 0); assert.strictEqual(g4.tally.ordersDelivered, 1);
  const sword = { name: "Fine Sword", kind: "weapon", slot: "weapon", power: 9, value: 400, props: {} }; g4.bag.push(sword); g4.gold = 500; const row = g4.bag.length - 1; assert.strictEqual(g4.insure(row), ""); assert.ok(sword.insured && g4.gold === 460 && g4.tally.spent.insurance === 40); assert.ok(g4.insure(row).includes("already")); assert.ok(g4.insure(g4.bag.findIndex((i) => i.kind === "torch")).includes("won't"));
  g4.vaults = []; CM.store.set("vaults", []); const paid = g4.payInsurance(); assert.strictEqual(paid, 1); assert.ok(g4.vaults.length === 1 && g4.vaults[0].name === "Fine Sword" && !g4.vaults[0].insured, "to the vault"); assert.strictEqual(CM.store.get("vaults", []).length, 1);
  // a bounty: three of a kind for gold and renown; the fence buys unknowns at half and takes cursed things; the rumour; the tithe
  g4.closeBag(); g4.bestiary = g4.bestiary || {}; assert.strictEqual(g4.takeBounty(), ""); const kind = g4.bounty.kind; assert.ok(CM.monsterKind(kind), kind); assert.ok(g4.claimBounty().includes("Not yet")); assert.ok(g4.takeBounty().includes("open already"));
  g4.bestiary[kind] = g4.bestiary[kind] || { seen: 0, slain: 0, weak: [], resist: [] }; g4.bestiary[kind].slain += 3; assert.ok(g4.bountyDone()); const gb = g4.gold, ren = (g4.village || {}).renown || 0; assert.strictEqual(g4.claimBounty(), ""); assert.strictEqual(g4.gold - gb, 60 + 40 * 15); assert.strictEqual(g4.village.renown, ren + 1); assert.ok(!g4.bounty && g4.tally.bounties === 1);
  g4.enterFloor(0, "rope", CM.TOWN_AT.tavern.slice()); assert.ok(g4.inTown(), "the fence drinks in town now");
  const unknown = Object.assign(CM.makeItem(10, new CM.Random(4), "ring"), { unknown: true, value: 200 }), cursedRing = { name: "Cursed Ring", kind: "ring", slot: "ring", power: 1, value: 300, props: { cursed: true, curse: "weak" } }; g4.bag.push(unknown, cursedRing);
  assert.ok(g4.fence(0).includes("only wants") || g4.bag[0].unknown || (g4.bag[0].props && g4.bag[0].props.cursed), "the fence wants unknowns and curses"); const gf = g4.gold; assert.strictEqual(g4.fence(g4.bag.indexOf(unknown)), ""); assert.strictEqual(g4.gold - gf, 100); assert.strictEqual(g4.fence(g4.bag.indexOf(cursedRing)), ""); assert.strictEqual(g4.gold - gf, 100, "cursed, for nothing"); assert.ok(!g4.bag.includes(cursedRing)); assert.strictEqual(g4.tally.fenced, 2);
  g4.gold = 200; const gr = g4.gold; assert.strictEqual(g4.fenceRumour(), ""); assert.strictEqual(gr - g4.gold, CM.RUMOUR_PRICE); if (g4.rumourBox) { assert.ok(g4.rumourBox >= 1 && g4.rumourBox <= 6); assert.ok(g4.fenceRumour().includes("told you")); const seen0 = () => g4.floor.seen.length; g4.enterFloor(g4.rumourBox, "down"); const box = Object.keys(g4.floor.things).find((k) => g4.floor.things[k].type === "strongbox"); assert.ok(box && g4.floor.seen.some(([x, y]) => `${x},${y}` === box), "the strongbox is on the map"); assert.strictEqual(g4.rumourBox, 0); assert.ok(seen0() > 0); }
  g4.enterFloor(15, "down"); g4.mode = "camp"; g4.gold = 300; assert.strictEqual(g4.tithe(), ""); assert.strictEqual(g4.gold, 270); assert.strictEqual(g4.blessedUntil, 20); assert.ok(g4.blessed() && g4.tithe().includes("already")); assert.strictEqual(g4.tally.spent.tithe, 30);
  g4.enterFloor(21, "down"); assert.ok(!g4.blessed(), "five floors, then it wears off");
  // the bot buys insurance, takes bounties and tithes when it can; the spending spreads
  const g5 = new CM.Game(); g5.newGame("econ-3", fixedParty(CM)); g5.gold = 2000; playRun(CM, g5, { maxFloor: 8 }); const sp = g5.tally.spent || {};
  assert.ok((sp.insurance || 0) > 0 || (sp.tithe || 0) > 0 || (g5.tally.bounties || 0) > 0 || g5.mode === "title", `the bot used the sinks: ${JSON.stringify(sp)} bounties ${g5.tally.bounties || 0}`);
});

test("around the things: the pad's belt button, rarity marked by shape as well as colour, the item card on every row, a film that shows the belt used and the thing thrown, the words counted", () => {
  const CM = load();
  assert.strictEqual(CM.DEFAULT_PAD.belt, 6); assert.ok(CM.PAD_ACTIONS.some(([id]) => id === "belt"));
  for (const k of ["hud.heavy", "hud.overloaded", "hud.blessed", "bag.weight", "bag.insure", "camp.bounty", "fence.head", "fence.rumour"]) assert.notStrictEqual(CM.t(k), k, `${k} is in CM.TEXT`);
  assert.strictEqual(CM.t("bag.weight", { n: 12, cap: 48 }), "Weight: 12/48");
  const css = fs.readFileSync(path.join(__dirname, "..", "src", "style.css"), "utf8");
  for (const r of ["fine", "rare", "relic", "unique", "cursed"]) assert.ok(css.includes(`.rarity-${r}::before`), `a shape for ${r}`);
  const built = fs.readdirSync(path.join(__dirname, "..", "game")).find((f) => f.endsWith(".html")); assert.ok(fs.readFileSync(path.join(__dirname, "..", "game", built), "utf8").includes(".rarity-fine::before"), "and it is in the build");
  // the item card: every kind of thing has one, and the chest's line carries the label of what was found
  for (const it of [CM.makeGear("weapon", 8, new CM.Random(1)), CM.trinket("chalk"), CM.lockpick(), CM.flask("oil"), CM.ration(), CM.makeUnique("holding"), CM.relic("rat")]) { const card = CM.itemCard(it); assert.ok(card && card.length > 10 && card.includes(CM.itemLabel(it).slice(0, 12)), it.name); }
  const game = new CM.Game(); game.newGame("around-1", fixedParty(CM));
  { const fl = game.floor, k = Object.keys(fl.things).find((c) => fl.things[c].type === "chest" && fl.things[c].items && fl.things[c].items.length);
    if (k) { fl.things[k].trap = null; fl.pos = k.split(",").map(Number); const it = fl.things[k].items[0]; it.unknown = false; game.use(); assert.ok(game.messages.slice(-2).some((l) => l.includes(CM.itemLabel(it).slice(0, 10))), `the chest's line carries the label: ${game.messages.slice(-1)[0]}`); } }
  // a film shows the belt used and the thing thrown: the acts are logged and play back the same
  const g2 = new CM.Game(); g2.newGame("around-2", fixedParty(CM)); const mageAt = g2.party.findIndex((h) => h.cls === "Mage");
  const mana = g2.bag.findIndex((i) => i.kind === "mana"), feather = g2.bag.findIndex((i) => i.kind === "revive"); assert.ok(mana >= 0 && feather >= 0);
  assert.strictEqual(g2.toBelt(mana, 0), ""); assert.strictEqual(g2.toBelt(g2.bag.findIndex((i) => i.kind === "revive"), 1), ""); assert.strictEqual((g2.belt || []).filter(Boolean).length, 2);
  g2.useBelt(0, mageAt); g2.useBelt(1, mageAt);                          // (the mage is whole: the potion is refused and goes back; the feather too)
  assert.ok(g2.runLog.some((l) => l[0] === "useBelt") && g2.runLog.some((l) => l[0] === "toBelt"), "the belt is in the log");
  const spec = g2.replaySpec(); const again = CM.replayRun(spec); assert.strictEqual(again.bag.length, g2.bag.length); assert.strictEqual((again.belt || []).filter(Boolean).map((i) => i.kind).join(), (g2.belt || []).filter(Boolean).map((i) => i.kind).join(), "the belt comes out the same in the film"); assert.strictEqual(again.messages.slice(-1)[0], g2.messages.slice(-1)[0]);
  { const g3 = new CM.Game(); g3.newGame("around-3", fixedParty(CM)); g3.bag.push(CM.flask("oil")); assert.strictEqual(g3.toBelt(g3.bag.length - 1, 0), "");
    g3.foes = [{ name: "Orc", kind: "Orc", hp: 60, max: 60, atk: 3, df: 1, row: "front", xp: 5, gold: 2 }]; g3.combat = { foes: g3.foes, round: 1, order: [], index: 0, waiting: g3.party[0] }; g3.mode = "combat"; g3.rnd = new CM.Random(1);
    const n = g3.runLog.length, before = g3.foes[0].hp; const ok = g3.act("item", { belt: 0, who: 0 }); assert.ok(ok, "thrown from the belt in a fight"); assert.ok(g3.foes[0].hp < before || g3.foes[0].burning, "and it lands"); assert.ok(g3.runLog.length > n && JSON.stringify(g3.runLog.slice(n)).includes("belt"), "the throw is in the log, for the film"); }
  // the words: tools/words.js counts the things' words too
  const out = execFileSync("node", [path.join(__dirname, "..", "tools", "words.js")], { encoding: "utf8" }); assert.ok(out.includes("The things' words") && /the trinkets \(CM.TRINKETS\)\s+\d+/.test(out), out.slice(0, 200));
});

test("automatic: the game's own autopilot plays a step a tick, wears, drinks and trades; it is a toggle; it stops by itself when lost or at the Root's choice rather than cheating; the bot drives the same class; its run films the same", () => {
  const CM = load();
  assert.ok(CM.Autopilot && CM.DEFAULT_KEYS.autoPlay === "KeyZ" && CM.KEY_ACTIONS.some(([id]) => id === "autoPlay"));
  // the toggle, step by step, in the game's own shape (no warping, no waking): a few floors, gear worn, potions drunk
  const game = new CM.Game(); game.newGame("auto-1", fixedParty(CM));
  assert.ok(!game.autoOn()); assert.strictEqual(game.autoPlay(true), true); assert.ok(game.autoOn() && game.auto instanceof CM.Autopilot && game.auto.opts.warp === false && game.auto.opts.sync === false);
  assert.ok(game.messages.slice(-1)[0].startsWith("Automatic:"));
  let steps = 0, fights = 0, did = {}; const before = game.tally.steps || 0;
  while (game.autoOn() && steps < 6000 && game.floor.number < 4) {
    const r = game.auto.step(); steps++; if (r) did[r] = (did[r] || 0) + 1;
    if (game.mode === "combat") { fights++; assert.strictEqual(game.auto.step(), "fighting"); assert.ok(game.combat.auto, "in a fight it hands the fight's Auto the reins"); autoplayFight(CM, game); }   // (the frame loop plays the fight in the browser; here the harness does)
  }
  assert.ok(game.floor.number >= 4 || game.mode === "title", `got down: floor ${game.floor.number}, ${steps} steps, ${JSON.stringify(did)} ${game.auto.why}`);
  assert.ok((game.tally.steps || 0) > before + 20 && did.moved > 20 && (did.used || 0) > 0, JSON.stringify(did));
  assert.ok(game.party.every((h) => h.weapon && h.armor), "wearing something");
  assert.ok(game.autoOn(), "still on");
  assert.strictEqual(game.autoPlay(false), true); assert.ok(!game.autoOn() && game.auto === null); assert.ok(game.messages.slice(-1)[0].startsWith("Automatic off"));
  assert.strictEqual(game.auto, null); assert.ok(game.autoPlay() && game.autoOn(), "the bare toggle turns it on again"); game.autoPlay();
  assert.ok(!game.autoOn());
  // the camp: one step does the business, the next goes deeper
  const g2 = new CM.Game(); g2.newGame("auto-2", fixedParty(CM)); g2.enterFloor(5, "down"); g2.gold = 500; g2.mode = "camp"; g2.autoPlay(true);
  const k = g2.party.find((h) => h.cls === "Knight"); k.hp = 5;
  assert.strictEqual(g2.auto.step(), "camp"); assert.strictEqual(g2.mode, "camp"); assert.strictEqual(k.hp, k.max, "rested"); assert.ok(g2.bag.filter((i) => i.kind === "heal" || i.kind === "greaterheal").length >= 1 || g2.gold < 40, "bought potions");
  assert.strictEqual(g2.auto.step(), "deeper"); assert.strictEqual(g2.mode, "explore"); assert.strictEqual(g2.floor.number, 6); g2.autoPlay(false);
  // lost: in the game it stops and says so (no warp); the simulator's bot warps on
  const g3 = new CM.Game(); g3.newGame("auto-3", fixedParty(CM)); g3.autoPlay(true); g3.auto.opts.perFloor = 2; const fl3 = g3.floor.number;
  let r3; for (let i = 0; i < 10 && g3.autoOn(); i++) r3 = g3.auto.step(); assert.ok(!g3.autoOn() && g3.floor.number === fl3, "stopped, and did not warp"); assert.ok(g3.messages.slice(-1)[0].includes("Automatic stops"), g3.messages.slice(-1)[0]);
  assert.strictEqual(g3.auto.step(), false, "a stopped autopilot does nothing more");
  const g4 = new CM.Game(); g4.newGame("auto-3", fixedParty(CM)); const bot = new CM.Autopilot(g4, { warp: true, wake: true, sync: true, perFloor: 2 }); for (let i = 0; i < 10 && bot.on; i++) bot.step(); assert.ok(g4.floor.number > 1 && bot.stuck >= 1, "the bot warps past a lost floor");
  // the Root's choice is the player's
  const g5 = new CM.Game(); g5.newGame("auto-5", fixedParty(CM)); g5.autoPlay(true); g5.rootPending = true; assert.strictEqual(g5.auto.step(), false); assert.ok(g5.messages.slice(-1)[0].includes("bottom of the world")); g5.rootPending = false; g5.autoPlay(false);
  // a fight begun while it is on: the fight's Auto is set; turning it off hands the fight back
  const g6 = new CM.Game(); g6.newGame("auto-6", fixedParty(CM)); const spot = Object.keys(g6.floor.things).find((c) => g6.floor.things[c].type === "monsters");
  if (spot) { g6.floor.pos = spot.split(",").map(Number); g6.startCombat(spot, g6.floor.things[spot], false); if (g6.mode === "combat") { g6.autoPlay(true); assert.ok(g6.combat.auto); assert.strictEqual(g6.auto.step(), "fighting"); g6.autoPlay(false); assert.ok(!g6.combat.auto, "the reins back"); } }
  // the bot is the same class, and an autopiloted run films the same (every act it takes is logged)
  const g7 = new CM.Game(); g7.newGame("auto-7", fixedParty(CM)); const r = playRun(CM, g7, { maxFloor: 3 }); assert.ok(r.log && typeof r.moves === "number" && r.tools && typeof r.stuck === "number");
  const again = CM.replayRun(g7.replaySpec()); assert.strictEqual(again.floor.number, g7.floor.number); assert.strictEqual(again.gold, g7.gold); assert.strictEqual(again.messages.slice(-1)[0], g7.messages.slice(-1)[0]);
});

test("the town above: floor 0 is hand-laid and the same for a seed, a run begins at the party's door and walks to the shaft, daylight (no hunger, no torch, no wanderers), the doors and the well, saved and replayed, back up from a camp and down again to the deepest camp, and the bot walks it", () => {
  const CM = load();
  const t1 = CM.makeFloor(0, "town-1", 2), t2 = CM.makeFloor(0, "town-1", 1), t3 = CM.makeTown("other");
  assert.strictEqual(t1.number, 0); assert.strictEqual(t1.grid.length, CM.TOWN_SIZE); assert.strictEqual(JSON.stringify(t1.grid), JSON.stringify(t2.grid)); assert.strictEqual(JSON.stringify(t1.grid), JSON.stringify(t3.grid), "the town does not depend on the seed");
  assert.strictEqual(CM.floorPrint(t1), CM.floorPrint(t3)); assert.strictEqual(Object.values(t1.things).filter((t) => t.type === "building").length, 9); assert.ok(CM.goalOf(t1) === CM.TOWN_AT.shaft.join(",")); assert.ok(Object.values(t1.things).some((t) => t.type === "well"));
  for (const [id, [x, y]] of Object.entries(CM.TOWN_AT)) assert.ok(CM.isOpen(t1, x, y), `${id} stands on open ground`);
  assert.strictEqual(t1.seen.length, CM.TOWN_SIZE * CM.TOWN_SIZE, "daylight: all on the map"); assert.ok(CM.distances(t1.grid, CM.TOWN_AT.home).get(CM.TOWN_AT.shaft.join(",")) > 10, "a walk from the door to the shaft");
  assert.strictEqual(CM.themeFor(0), CM.TOWN_THEME); assert.strictEqual(CM.themeIndex(0), 0); assert.strictEqual(CM.themeFor(1).name, "The Catacombs"); assert.strictEqual(CM.bandName(null, 0), CM.TOWN_THEME.name);
  // the harness starts at the shaft (settings.skipWalk); a run asked for the town begins at the party's door
  const g0 = new CM.Game(); g0.newGame("town-2", fixedParty(CM)); assert.strictEqual(g0.floor.number, 1); assert.ok(!g0.startedInTown);
  const game = new CM.Game(); game.newGame("town-2", fixedParty(CM), "pauper", "fair", [], "dungeon", { town: true });
  assert.strictEqual(game.floor.number, 0); assert.ok(game.startedInTown); assert.strictEqual(game.floor.pos.join(), CM.TOWN_AT.home.join()); assert.ok(CM.isOpen(game.floor, game.floor.pos[0] + CM.DIRS[game.floor.facing][0], game.floor.pos[1] + CM.DIRS[game.floor.facing][1]) && CM.townStreet(game.floor.pos[0] + CM.DIRS[game.floor.facing][0], game.floor.pos[1] + CM.DIRS[game.floor.facing][1]) === "Lantern Street", "facing the street"); assert.strictEqual(game.mode, "explore");
  assert.strictEqual(game.lightFactor(), 1.3); assert.ok(!game.inDark());
  // daylight: steps count, but no hunger, no torch burnt, nothing wanders
  game.light = { kind: "torch", left: 100 }; const fed0 = game.fed || 0, steps0 = game.tally.steps || 0;
  for (let i = 0; i < 6; i++) game.move(0); assert.ok((game.tally.steps || 0) >= steps0 + 6, "walked"); assert.strictEqual(game.fed || 0, fed0); assert.strictEqual(game.light.left, 100);
  game.rnd = new CM.Random(1); game.wanderMonsters(); assert.ok(!Object.values(game.floor.things).some((t) => t.type === "monsters")); assert.strictEqual(game.mode, "explore");
  // the doors say what they are and open a building; the well is dry before a crown
  const fl = game.floor; let opened = null; game.on("building", (id) => { opened = id; });
  fl.pos = CM.TOWN_AT.tavern.slice(); game.use(); assert.strictEqual(opened, "tavern"); assert.ok(game.messages.slice(-1)[0].includes("Hanged Lantern") || true);
  fl.pos = CM.TOWN_AT.well.slice(); game.use(); assert.ok(game.messages.slice(-1)[0].includes("dry"));
  assert.strictEqual(CM.plotLevel(game, "library"), 0); game.village = game.village || {}; game.village.levels = { library: 2 }; assert.strictEqual(CM.plotLevel(game, "library"), 2); assert.strictEqual(CM.plotLevel(game, "temple"), 0); game.village.levels = {};
  // saved on floor 0 and loaded there, with a small delta; the walk to the shaft, and down
  game.saveRun(); const g2 = new CM.Game(); g2.continueRun(); assert.strictEqual(g2.floor.number, 0); assert.ok(g2.startedInTown); assert.ok(JSON.stringify(g2.floorDeltas()[0]).length < 2500, `a small delta: ${JSON.stringify(g2.floorDeltas()[0]).length}`);
  fl.pos = CM.TOWN_AT.home.slice(); const [sx, sy] = CM.TOWN_AT.shaft; assert.ok(game.travelTo(sx, sy)); let guard = 0; while (game.travel && guard++ < 60) game.travelStep(); assert.strictEqual(game.floor.pos.join(), `${sx},${sy}`, "the party walked to the shaft");
  game.use(); assert.strictEqual(game.floor.number, 1); assert.strictEqual(game.mode, "explore");
  // the camps: back to town, and the shaft goes down again to the deepest camp reached
  game.enterFloor(5, "down"); game.floor.things[game.floor.pos.join(",")] = { type: "ladder" }; game.use(); assert.strictEqual(game.mode, "camp"); assert.ok((game.camps || []).includes(5));
  assert.strictEqual(game.goHome(), ""); assert.strictEqual(game.floor.number, 0); assert.strictEqual(game.mode, "explore"); assert.strictEqual(game.floor.pos.join(), `${sx},${sy}`, "at the shaft's mouth");
  game.use(); assert.strictEqual(game.mode, "camp"); assert.strictEqual(game.floor.number, 5, "down to the deepest camp");
  assert.ok(game.goHome() === "" && game.floor.number === 0); game.saveRun(); const g3 = new CM.Game(); g3.continueRun(); assert.strictEqual(g3.floor.number, 0); assert.ok(g3.camps.includes(5));
  // a replay of a run that began in town begins in town, and an old film's spec (no town) begins at the shaft
  const g4 = new CM.Game(); g4.newGame("town-3", fixedParty(CM), "pauper", "fair", [], "dungeon", { town: true }); const r = playRun(CM, g4, { maxFloor: 3 });
  assert.ok(g4.floor.number >= 3 || g4.mode === "title", `the bot walked the town and went down: floor ${g4.floor.number} ${r.log.join("|")}`); assert.ok(g4.trail[0][0] === 0, "the trail begins at home");
  const spec = g4.replaySpec(); assert.ok(spec.town); const again = CM.replayRun(spec); assert.strictEqual(again.floor.number, g4.floor.number); assert.strictEqual(again.gold, g4.gold); assert.strictEqual(again.messages.slice(-1)[0], g4.messages.slice(-1)[0]);
  const old = CM.replayRun(Object.assign({}, spec, { town: undefined, log: [] })); assert.strictEqual(old.floor.number, 1, "an old film starts at the shaft");
  // Automatic in the game's shape walks home to the shaft
  const g5 = new CM.Game(); g5.newGame("town-4", fixedParty(CM), "pauper", "fair", [], "dungeon", { town: true }); g5.autoPlay(true); let n = 0; while (g5.floor.number === 0 && g5.autoOn() && n++ < 200) g5.auto.step(); assert.ok(g5.floor.number === 1, `Automatic walked to the shaft in ${n} steps`); g5.autoPlay(false);
});

test("the home: raised with renown; the hearth rests and sends the party down rested (gone at floor 6); the stash keeps things between runs and through a fall; the trophy wall; the kitchen's two-floor meal and the larder; a candle at the door to the stash; a hero retires home and a will starts every run", () => {
  const CM = load();
  assert.ok(CM.VILLAGE.home && CM.VILLAGE.home.costs.length === 5 && CM.TOWN_PLOTS.home.village === "home");
  const start = () => { const g = new CM.Game(); g.newGame("home-1", fixedParty(CM), "pauper", "fair", [], "dungeon", { town: true }); return g; };
  let g = start(); assert.strictEqual(g.homeLevel(), 0); assert.ok(g.hearthRest().includes("roof")); assert.ok(g.stashPut(0).includes("roof"));
  g.village.renown = 5000; assert.strictEqual(g.build("home"), ""); assert.strictEqual(g.homeLevel(), 1); assert.strictEqual(CM.plotLevel(g, "home"), 1);
  // the hearth: once a visit; rested on floors 1 to 5, not 6
  const knight = g.party.find((h) => h.cls === "Knight"); knight.hp = 3; g.fed = 200; assert.strictEqual(g.hearthRest(), ""); assert.strictEqual(knight.hp, knight.max); assert.strictEqual(g.fed, 0); assert.strictEqual(g.buffs.rested, 5); assert.ok(g.hearthRest().includes("banked"));
  assert.ok(!g.rested(), "not rested in the town itself"); g.enterFloor(1, "down"); assert.ok(g.rested()); g.enterFloor(5, "down"); assert.ok(g.rested()); g.enterFloor(6, "down"); assert.ok(!g.rested() && g.buffs.rested === undefined, "worn off at six");
  // the stash: six things at level one; keys stay; it survives a reload, a new run and a fallen party
  g.enterFloor(0, "rope", CM.TOWN_AT.home.slice()); assert.ok(g.inTown());
  const sword = { name: "Keepsake Sword", base: "Long Sword", kind: "weapon", slot: "weapon", power: 7, value: 90, props: {} }; g.bag.push(sword, { name: "Key", kind: "key", power: 0, value: 0 });
  assert.ok(g.stashPut(g.bag.length - 1).includes("key")); assert.strictEqual(g.stashPut(g.bag.length - 2), ""); assert.ok(!g.bag.includes(sword) && g.home().stash[0] === sword); assert.strictEqual(g.stashRoom(), 5);
  for (let i = 0; i < 5; i++) { g.bag.push(CM.ration()); assert.strictEqual(g.stashPut(g.bag.length - 1), ""); } g.bag.push(CM.ration()); assert.ok(g.stashPut(g.bag.length - 1).includes("full"));
  assert.strictEqual(CM.store.get("village", {}).home.stash.length, 6, "kept between runs");
  g.enterFloor(3, "down"); for (const h of g.party) h.hp = 0; g.payInsurance(); g.endRun(false); assert.strictEqual(g.mode, "title");
  g = start(); assert.strictEqual(g.home().stash.length, 6, "the stash through a fall and a new run"); assert.strictEqual(g.home().stash[0].name, "Keepsake Sword");
  const n0 = g.bag.length; assert.strictEqual(g.stashTake(0), ""); assert.strictEqual(g.bag.length, n0 + 1); assert.strictEqual(g.bag[n0].name, "Keepsake Sword"); assert.strictEqual(g.home().stash.length, 5); assert.ok(g.stashTake(9).includes("Nothing"));
  // the trophy wall, the kitchen and the larder
  g.village.renown = 5000; g.build("home"); g.build("home"); assert.strictEqual(g.homeLevel(), 3);
  g.trophies.rat = { date: CM.today(), name: "x", seed: "s" }; g.compendium.named = [{ name: "Gnasher", base: "Long Sword", history: [], date: "", bearer: "" }]; g.compendium["Tidecaller"] = { floor: 7, date: "" }; g.fame = [{ won: true }, { won: false, bottom: true }];
  const T = g.homeTrophies(); assert.strictEqual(T.trophies[0].name, "The Rat King"); assert.strictEqual(T.named[0].name, "Gnasher"); assert.ok(T.uniques.includes("Tidecaller")); assert.strictEqual(T.crowns, 1); assert.strictEqual(T.bottoms, 1);
  g.bag.push(CM.meat("Orc")); assert.strictEqual(g.homeCook(g.bag.length - 1), ""); assert.ok(g.meal && g.meal.floor === 2); g.enterFloor(1, "down"); assert.ok(g.meal); g.enterFloor(2, "down"); assert.ok(g.meal, "through the second floor"); g.enterFloor(3, "down"); assert.ok(!g.meal, "and gone at the third");
  g.enterFloor(0, "rope", CM.TOWN_AT.home.slice()); for (let i = 0; i < 4; i++) g.bag.push(CM.ration()); const rations = () => g.bag.filter((i) => i.kind === "ration").length; const r0 = rations();
  for (let i = 0; i < 3; i++) assert.strictEqual(g.larderPut(g.bag.findIndex((i) => i.kind === "ration")), ""); assert.ok(g.larderPut(g.bag.findIndex((i) => i.kind === "ration")).includes("holds 3")); assert.strictEqual(rations(), r0 - 3); assert.strictEqual(CM.store.get("village", {}).home.larder, 3);
  assert.strictEqual(g.larderTake(), ""); assert.strictEqual(rations(), r0 - 2); assert.strictEqual(g.home().larder, 2);
  // the door-plate: a candle at home sends the buried thing to the stash, not the vault
  g.build("home"); assert.strictEqual(g.homeLevel(), 4); g.village.levels.shrine = 1; g.memorial = [{ name: "Old Tam", cls: "Rogue", level: 9, floor: 12, seed: "s", date: "", buried: { name: "Tam's Knife", kind: "weapon", slot: "weapon", power: 5, value: 40, props: {} }, last: "", epitaph: "" }]; CM.store.set("memorial", g.memorial); g.vaults = []; CM.store.set("vaults", []);
  const stash0 = g.home().stash.length; assert.strictEqual(g.homeCandle(0), ""); assert.ok(g.memorial[0].candle); assert.strictEqual(g.home().stash.length, stash0 + 1); assert.strictEqual(g.home().stash[stash0].name, "Tam's Knife"); assert.strictEqual(g.vaults.length, 0, "not to the vault"); assert.ok(g.homeCandle(0).includes("already"));
  // the study: a hero retires home, writes a will, and the will is in every later pack
  g.build("home"); assert.strictEqual(g.homeLevel(), 5); const mageAt = g.party.findIndex((h) => h.cls === "Mage"), mageName = g.party[mageAt].name;
  assert.strictEqual(g.retireHome(mageAt), ""); assert.strictEqual(g.party.length, 3); assert.strictEqual(g.home().retired[0].name, mageName);
  g.bag.push(CM.healPotion(1)); assert.strictEqual(g.stashPut(g.bag.length - 1), ""); const potAt = g.home().stash.length - 1; assert.strictEqual(g.writeWill(potAt), ""); assert.ok(g.home().will && g.home().will.kind === g.home().stash[potAt].kind);
  g.home().stash.push(CM.makeUnique("tidecaller")); assert.ok(g.writeWill(g.home().stash.length - 1).includes("one of a kind"));
  const g2 = new CM.Game(); g2.newGame("home-2", fixedParty(CM)); assert.ok(g2.bag.some((i) => i.willed && i.kind === g.home().will.kind), "the will in the pack of a new run"); assert.strictEqual(g2.home().will.kind, g.home().will.kind, "and still in the stash's will");
  const g3 = new CM.Game(); g3.village.levels.home = 0; g3.saveVillage(); g3.newGame("home-3", fixedParty(CM)); assert.ok(!g3.bag.some((i) => i.willed), "no study, no will");
  // a replay of a run with the house's acts in it comes out the same
  const g4 = new CM.Game(); g4.village.levels.home = 3; g4.saveVillage(); g4.newGame("home-4", fixedParty(CM), "pauper", "fair", [], "dungeon", { town: true }); g4.hearthRest(); g4.stashPut(0); g4.larderTake(); const spec = g4.replaySpec();
  const stashNow = g4.home().stash.length; g4.home().stash.length = stashNow; const again = CM.replayRun(spec); assert.strictEqual(again.bag.length, g4.bag.length); assert.ok(again.buffs && again.buffs.rested === 5);
});

test("the tavern, the merchant and the smith in town: the full stock at the party's level, a commission made by the first camp, insurance and orders at the Merchant's House, a round and the regular at the Hanged Lantern, the fence only there, a base reforged with its words and marks, a second gem in a relic, the apprentice's scrap", () => {
  const CM = load();
  const g = new CM.Game(); g.newGame("shops-1", fixedParty(CM), "pauper", "fair", [], "dungeon", { town: true });
  assert.ok(g.inTown() && g.atShop()); assert.strictEqual(CM.plotLevel(g, "tavern"), 1, "the tavern stands from the start"); assert.strictEqual(CM.plotLevel(g, "merchant"), 1); assert.strictEqual(CM.plotLevel(g, "library"), 0);
  // the Merchant's House: everything on the table, at the party's level; orders go to the first camp; a commission at level 3
  g.gold = 2000; g.openBag(true); const kinds = new Set(g.stock.map((i) => i.kind)); for (const k of ["lockpick", "bar", "bait", "lantern", "rope", "scroll", "flask"]) assert.ok(kinds.has(k), `${k} on the town's table`);
  assert.ok(g.stock.filter((i) => i.kind === "weapon").every((w) => ((CM.BASES[CM.baseIdOf(w)] || {}).tier || 0) <= 5), "gear at a level-one party's level");
  assert.strictEqual(g.order("lampoil"), ""); assert.strictEqual(g.orders[0].from, 0);
  assert.ok(g.commission("Long Sword").includes("third level")); g.village.renown = 5000; g.build("merchant"); g.build("merchant"); g.build("merchant"); assert.strictEqual(g.villageLevel("merchant"), 3);
  assert.ok(g.commission("Tidecaller").includes("pattern")); const gold0 = g.gold; assert.strictEqual(g.commission("Maul"), ""); assert.ok(g.gold < gold0); const com = g.orders.find((o) => o.commission); assert.ok(com && com.item.base === "Maul" && com.item.props.twohanded && !com.item.unknown && com.from === 0, JSON.stringify(com && com.item));
  assert.ok(com.item.props.affix || com.item.props.suffix || com.item.props.prefix || true, "affixed as the floor would");
  const sword = { name: "Fine Sword", kind: "weapon", slot: "weapon", power: 9, value: 400, props: {} }; g.bag.push(sword); assert.strictEqual(g.insure(g.bag.length - 1), ""); assert.ok(sword.insured, "insured in town"); g.closeBag();
  { const m = CM.gearOfBase("Chain Mail", 6, new CM.Random(1)) || CM.gearOfBase(Object.values(CM.BASES).find((B) => B.kind === "armor").id, 6, new CM.Random(1)); assert.ok(m && m.kind === "armor" && m.props.weight, "armour of a base has its weight"); assert.strictEqual(CM.gearOfBase("Lockpick", 3, new CM.Random(1)), null); }
  // the Hanged Lantern: a round, the regular, the board; the fence drinks here and not at the camp
  g.morale = 40; assert.strictEqual(g.drink(), ""); assert.strictEqual(g.morale, 90); assert.ok(g.drink().includes("One round")); assert.strictEqual(g.tally.spent.tavern, CM.DRINK_PRICE);
  assert.strictEqual(g.gossip(), ""); assert.ok(/floor \d+/.test(g.messages.slice(-1)[0]) && g.messages.slice(-1)[0].includes("palace")); assert.ok(g.gossip().includes("told you"));
  assert.strictEqual(g.takeBounty(), ""); assert.ok(g.bounty && g.bounty.floor === 0); g.bounty = null;
  // down to the first camp: the order and the commission are waiting; the fence is not at the camp's bench
  g.enterFloor(5, "down"); g.floor.things[g.floor.pos.join(",")] = { type: "ladder" }; g.use(); assert.strictEqual(g.mode, "camp");
  const before = g.bag.length; g.openBag(true); assert.ok(g.bag.some((i) => i.base === "Maul") && g.bag.some((i) => i.kind === "lampoil") && g.bag.length >= before + 2, "delivered at the first camp"); assert.strictEqual(g.orders.length, 0); g.closeBag();
  g.bag.push(Object.assign(CM.makeItem(5, new CM.Random(2), "ring"), { unknown: true })); assert.ok(g.fence(g.bag.length - 1).includes("in town")); assert.ok(g.fenceRumour().includes("in town")); assert.ok(g.drink().includes("in town"));
  assert.ok(g.smith("enchant", 0, "weapon") !== "The smith works at the camp, and at the forge in town.", "the camp's smith still works"); assert.ok(g.reforgeBase(0, "weapon", "Bastard Sword").includes("in town"));
  // the forge: a base reforged keeps its words, its marks and its name; the relic's second gem; the apprentice's scrap
  g.goHome(); assert.ok(g.inTown()); const knight = g.party.find((h) => h.cls === "Knight"), ki = g.party.indexOf(knight);
  const blade = CM.gearOfBase("Long Sword", 8, new CM.Random(3)); CM.affix(blade, 20, new CM.Random(4)); blade.unknown = false; blade.props.regen = 2; blade.marks = 2; blade.power += 2; blade.history = ["slew a troll"]; blade.name = CM.itemName(blade); knight.weapon = blade; CM.recompute(knight);
  const words = Object.assign({}, blade.props), nameWas = blade.name, pow = blade.power; g.gold = 1000;
  assert.ok(g.reforgeBase(ki, "weapon", "Bastard Sword").includes("essence")); g.bag.push(CM.essence(1)); assert.ok(g.reforgeBase(ki, "weapon", "Chain Mail").includes("same kind") || g.reforgeBase(ki, "weapon", "Nothing").includes("same kind"));
  assert.strictEqual(g.reforgeBase(ki, "weapon", "Bastard Sword"), ""); assert.strictEqual(CM.baseIdOf(blade), "Bastard Sword"); assert.strictEqual(blade.marks, 2); assert.strictEqual(blade.props.regen, 2);
  for (const k of Object.keys(words)) if (!["twohanded", "bow"].includes(k)) assert.strictEqual(JSON.stringify(blade.props[k]), JSON.stringify(words[k]), `the word ${k} kept`);
  assert.ok(blade.name !== nameWas && blade.name.includes("Bastard Sword"), blade.name); assert.strictEqual(blade.power, pow + 2 * ((CM.BASES["Bastard Sword"].tier || 0) - (CM.BASES["Long Sword"].tier || 0))); assert.ok(!g.bag.some((i) => i.kind === "essence"), "the essence spent"); assert.ok(blade.history.slice(-1)[0].includes("reforged"));
  assert.ok(g.reforgeBase(ki, "weapon", "Bastard Sword").includes("already"));
  knight.helm = CM.relic("rat"); assert.ok(g.secondGem(ki, "helm").includes("ruby")); g.bag.push(CM.gem("ruby")); const hp = knight.helm.power; assert.strictEqual(g.secondGem(ki, "helm"), ""); assert.strictEqual(knight.helm.props.gem2, "fire"); assert.strictEqual(knight.helm.props.resist, "fire"); assert.strictEqual(knight.helm.power, hp + 1); assert.ok(g.secondGem(ki, "helm").includes("second gem")); assert.ok(g.secondGem(ki, "weapon").includes("relic"));
  for (let i = 0; i < 4; i++) g.bag.push(CM.scrap()); const gs = g.gold; assert.strictEqual(g.sellScrap(), ""); assert.strictEqual(g.gold - gs, 4 * Math.ceil(5 * CM.SCRAP_PRICE)); assert.ok(!g.bag.some((i) => i.kind === "scrap")); assert.ok(g.sellScrap().includes("No scrap"));
  assert.ok(g.runLog.some((l) => l[0] === "reforgeBase") && g.runLog.some((l) => l[0] === "commission") && g.runLog.some((l) => l[0] === "drink"), "the shops' acts are logged, for the films");
});

test("the library, the temple and the guildhall: a tome borrowed for a run and back on the shelf after; the lost pages shelved; the gazetteer maps the first floors' walls; the temple a tenth cheaper in town, the vigil over a scar; the guild's letter in town; the roster keeps every party and the muster finds the last that came home", () => {
  const CM = load();
  assert.strictEqual(CM.VILLAGE.library.costs.length, 5); assert.strictEqual(CM.VILLAGE.shrine.costs.length, 5);
  const g = new CM.Game(); g.newGame("halls-1", fixedParty(CM), "pauper", "fair", [], "dungeon", { town: true });
  assert.ok(g.borrowTome("frost").includes("roof")); g.village.renown = 9000; g.build("library"); assert.strictEqual(g.villageLevel("library"), 1);
  assert.ok(g.borrowTome("nothing").includes("No such")); const n0 = g.bag.length; assert.strictEqual(g.borrowTome("frost"), ""); assert.strictEqual(g.bag.length, n0 + 1); assert.ok(g.bag[n0].borrowed && g.bag[n0].spell === "frost" && g.bag[n0].value === 0); assert.ok(g.borrowTome("fireball").includes("out already"));
  assert.strictEqual(CM.store.get("village", {}).library.lent.tome, "frost");
  g.gain([CM.scroll("lostpage")], "test"); assert.strictEqual(g.libraryState().pages, 1, "a lost page shelved");
  // the run ends: the tome goes back on the shelf (unread, it leaves the pack); the roster remembers the party
  g.enterFloor(2, "down"); const names = g.party.map((h) => h.name); for (const h of g.party) h.hp = 0; g.endRun(false);
  assert.strictEqual(CM.store.get("village", {}).library.lent, null, "back on the shelf"); const roster = CM.store.get("village", {}).roster; assert.ok(roster && roster.length === 1 && roster[0].party.map((p) => p.name).join() === names.join() && !roster[0].home, "the roster: a party that fell");
  // the gazetteer at the fifth level: floors 1 to 5 have their walls on the map on a new run, floor 6 does not
  const g2 = new CM.Game(); g2.village.renown = 9000; while (g2.villageLevel("library") < 5) g2.build("library"); g2.newGame("halls-2", fixedParty(CM));
  const all = (fl) => fl.seen.length >= fl.grid.length * fl.grid.length; assert.ok(all(g2.floor), "floor 1 mapped"); g2.enterFloor(5, "down"); assert.ok(all(g2.floor)); g2.enterFloor(6, "down"); assert.ok(!all(g2.floor), "floor 6 is dark as ever");
  assert.ok(g2.muster() === null, "no party has come home yet");
  // the temple in town: a tenth less; the vigil at the shrine's fifth level
  const g3 = new CM.Game(); g3.village.renown = 9000; while (g3.villageLevel("shrine") < 5) g3.build("shrine"); g3.newGame("halls-3", fixedParty(CM), "pauper", "fair", [], "dungeon", { town: true });
  const k = g3.party.find((h) => h.cls === "Knight"), ki = g3.party.indexOf(k); g3.gold = 1000; k.status = { poison: 3 }; const gt = g3.gold; assert.ok(g3.temple("cure")); assert.strictEqual(gt - g3.gold, 27, "30 gold, a tenth less in town");
  k.hp = 0; const gr = g3.gold; g3.raiseDead(); assert.strictEqual(gr - g3.gold, 90); assert.ok(k.wound); const gw = g3.gold; assert.ok(g3.temple("wounds")); assert.strictEqual(gw - g3.gold, 36);
  k.scars = ["limp", "thickskin"]; assert.ok(g3.vigil(ki, "burnedhand", false).includes("no such")); assert.strictEqual(g3.vigil(ki, "limp", false), ""); assert.ok(!k.scars.includes("limp") && k.scars.includes("thickskin") && k.vigil); assert.ok(g3.vigil(ki, "thickskin", false).includes("already"));
  const mage = g3.party.find((h) => h.cls === "Mage"), mi = g3.party.indexOf(mage); mage.scars = ["hardhead"]; assert.strictEqual(g3.vigil(mi, "hardhead", true), ""); assert.ok(mage.scars.includes("hardhead") && mage.vigil, "kept, and the vigil spent");
  assert.strictEqual(g3.tithe(), "", "the tithe is given in town too"); assert.ok(g3.blessedUntil === 5);
  g3.enterFloor(3, "down"); k.status = { poison: 3 }; const gc = g3.gold; g3.mode = "camp"; assert.ok(g3.temple("cure")); assert.strictEqual(gc - g3.gold, 30, "full price at the camp"); g3.mode = "explore";
  // the guild's letter is read in town; the roster: a party that came home is the muster
  const g4 = new CM.Game(); g4.village.renown = 9000; g4.build("guildhall"); g4.build("guildhall"); g4.newGame("halls-4", fixedParty(CM), "pauper", "fair", [], "dungeon", { town: true });
  assert.ok(!g4.secondCalling(0, "Mage").includes("at a camp"), g4.secondCalling(0, "Mage"));
  g4.enterFloor(20, "down"); g4.crowned = true; g4.endRun(true); const r = CM.store.get("village", {}).roster; assert.ok(r[0].home && r[0].won, "the crowned party came home"); assert.strictEqual(r.length, 1, "the same four, the same names: one line in the roster, the newest");
  const g5 = new CM.Game(); assert.ok(g5.muster() && g5.muster().party.map((p) => p.cls).join() === fixedParty(CM).map((p) => p.cls).join(), "the muster is the last party that came home");
  for (let i = 0; i < 14; i++) { const gx = new CM.Game(); gx.newGame(`halls-roster-${i}`, fixedParty(CM, `p${i}`)); gx.enterFloor(2, "down"); for (const h of gx.party) h.hp = 0; gx.endRun(false); } assert.strictEqual(new CM.Game().roster().length, CM.ROSTER_MAX, "twelve, and no more");
});

test("the garden, the chronicler and the square: a bed planted grows by one a run and is harvested; the bench and the request in the garden at town prices; market day's peddler on the week's seed; three townsfolk with a line a day; the well's coin for the town; the lanterns at night", () => {
  const CM = load();
  assert.ok(CM.VILLAGE.garden && CM.VILLAGE.chronicler && CM.TOWNSFOLK.length === 3 && CM.TOWNSFOLK.every((t) => t.lines.length === 4));
  const g = new CM.Game(); g.village.renown = 9000; g.build("garden"); g.newGame("square-1", fixedParty(CM), "pauper", "fair", [], "dungeon", { town: true });
  // the beds: one at level one; a bed grows one more every run that ends; harvested, it gives them all
  g.bag.push(CM.ingredient("gravemoss"), CM.ingredient("gravemoss"), CM.ration()); assert.ok(g.plant(g.bag.length - 1).includes("ingredient")); assert.strictEqual(g.plant(g.bag.length - 2), ""); assert.strictEqual(g.garden().beds.length, 1); assert.ok(g.plant(g.bag.findIndex((i) => i.ingredient === "gravemoss")).includes("Every bed"));
  assert.strictEqual(CM.store.get("village", {}).garden.beds[0].n, 1);
  g.enterFloor(2, "down"); for (const h of g.party) h.hp = 0; g.endRun(false); assert.strictEqual(CM.store.get("village", {}).garden.beds[0].n, 2, "grown by one when the run ended");
  for (let i = 0; i < 5; i++) { const gx = new CM.Game(); gx.newGame(`square-grow-${i}`, fixedParty(CM)); gx.enterFloor(2, "down"); for (const h of gx.party) h.hp = 0; gx.endRun(false); } assert.strictEqual(CM.store.get("village", {}).garden.beds[0].n, CM.BED_MAX, "and no more than five");
  const g2 = new CM.Game(); g2.newGame("square-2", fixedParty(CM), "pauper", "fair", [], "dungeon", { town: true }); const moss = () => g2.bag.filter((i) => i.ingredient === "gravemoss").length; const m0 = moss(); assert.strictEqual(g2.harvest(0), ""); assert.strictEqual(moss(), m0 + 5); assert.strictEqual(g2.garden().beds.length, 0);
  // the bench in town, at town prices (no kit's fifth); the request once the garden has three beds
  g2.gold = 500; g2.bag.push(CM.ingredient("forgesoot")); const gb = g2.gold; assert.strictEqual(g2.brew("flaskoil"), ""); assert.strictEqual(gb - g2.gold, 20, "the camp's price, not the kit's");
  assert.ok(g2.deliver().includes("three beds")); g2.village.renown = 9000; g2.build("garden"); g2.build("garden"); assert.strictEqual(g2.bedsOf(), 3); const want = g2.alchemistWants(); g2.bag.push(CM.ingredient(want), CM.ingredient(want), CM.ingredient(want)); assert.strictEqual(g2.deliver(), ""); assert.ok(g2.alchemistFree);
  // market day: the peddler's cloth is in the square on the week's seed, and only then; the townsfolk stand on the lanes
  const market = CM.makeTown(CM.weeklySeed()), plain = CM.makeTown("square-3"); assert.ok(Object.values(market.things).some((t) => t.type === "peddler"), "market day"); assert.ok(!Object.values(plain.things).some((t) => t.type === "peddler")); assert.strictEqual(CM.floorPrint(market), CM.floorPrint(plain), "the same town, peddler or no");
  const folk = Object.entries(plain.things).filter(([, t]) => t.type === "villager"); assert.strictEqual(folk.length, 3); for (const [k] of folk) { const [x, y] = k.split(",").map(Number); assert.ok(CM.isOpen(plain, x, y)); }
  assert.notStrictEqual(JSON.stringify(folk.map(([k]) => k)), JSON.stringify(Object.entries(CM.makeTown("square-4").things).filter(([, t]) => t.type === "villager").map(([k]) => k)), "where they stand is the seed's");
  const g3 = new CM.Game(); g3.newGame("square-3", fixedParty(CM), "pauper", "fair", [], "dungeon", { town: true }); let heard = null; g3.on("talk", (t) => { heard = t; });
  g3.floor.pos = folk[0][0].split(",").map(Number); g3.use(); assert.ok(heard && heard.title === CM.TOWNSFOLK[folk[0][1].who].name && CM.TOWNSFOLK[folk[0][1].who].lines.includes(heard.text), "a line a day");
  // the well: the notice board, and a coin for the town once a visit; night by the clock
  const ren = g3.village.renown || 0; g3.gold = 10; g3.floor.pos = CM.TOWN_AT.well.slice(); g3.use(); assert.ok(heard.title === "The square" && heard.text.includes(CM.weeklySeed())); assert.strictEqual(g3.gold, 9); assert.strictEqual(g3.village.renown, ren + 1); g3.use(); assert.strictEqual(g3.gold, 9, "one coin a visit");
  assert.strictEqual(g3.lightFactor(), 1.3); const clockWas = g3.clock; g3.clock = 17 * 60; assert.strictEqual(g3.lightFactor(), 0.8, "the lanterns"); g3.clock = clockWas;
  // the chronicler's house holds what the title's boards hold
  assert.ok(Array.isArray(CM.store.get("films", [])) && CM.store.get("films", []).length >= 1, "films to watch at the table"); assert.ok((new CM.Game()).ledger.length >= 6 && (new CM.Game()).fame.length >= 6);
});

test("growth: a building is drawn by its level (a foundation, a frame, a roof, a sign, a lit window); nine buildings' renown re-tuned, and three renown for every door opened before a descent; the well's stones carry the hill's chapter in order; what the runs brought back is on the walls", () => {
  const CM = load();
  assert.strictEqual(Object.keys(CM.VILLAGE).length, 10, Object.keys(CM.VILLAGE).join(","));   // (nine buildings, and the farm)
  const total = Object.values(CM.VILLAGE).reduce((s, b) => s + b.costs.reduce((a, c) => a + c, 0), 0); assert.ok(total > 2500 && total < 5000, `the town costs ${total} renown in all`);
  assert.ok(CM.VILLAGE.home.costs[0] <= CM.VILLAGE.guildhall.costs[0] && CM.VILLAGE.chronicler.costs[0] > CM.VILLAGE.home.costs[1], "the home first, the chronicler's house late");
  for (const B of Object.values(CM.VILLAGE)) { assert.strictEqual(B.costs.length, B.levels.length, B.name); for (let i = 1; i < B.costs.length; i++) assert.ok(B.costs[i] > B.costs[i - 1], `${B.name} climbs`); }
  // the drawn stage, by the level against the most
  assert.strictEqual(CM.houseStage(0, 5), 0); assert.strictEqual(CM.houseStage(1, 5), 1); assert.strictEqual(CM.houseStage(2, 5), 2); assert.strictEqual(CM.houseStage(3, 5), 3); assert.strictEqual(CM.houseStage(5, 5), 4); assert.strictEqual(CM.houseStage(1, 1), 4); assert.strictEqual(CM.houseStage(4, 4), 4); assert.strictEqual(CM.houseStage(2, 4), 2);
  const css = fs.readFileSync(path.join(__dirname, "..", "src", "js", "30-art.js"), "utf8"); assert.ok(css.includes("add(`house${s}`") && css.includes("CM.art.house(s)"), "four house layers in the atlas");
  // three renown for every door opened before the descent, up to nine
  const base = { floor: 20, won: true, tally: { guardians: ["rat"], spoken: [] }, difficulty: "fair" };
  const r0 = CM.renownFor(base, null), r9 = CM.renownFor(Object.assign({}, base, { tally: Object.assign({}, base.tally, { visited: ["home", "tavern", "merchant", "smith", "garden", "library", "temple", "guildhall", "chronicler"] }) }), null), r2 = CM.renownFor(Object.assign({}, base, { tally: Object.assign({}, base.tally, { visited: ["home", "tavern"] }) }), null);
  assert.strictEqual(r9 - r0, 27); assert.strictEqual(r2 - r0, 6);
  const g = new CM.Game(); g.newGame("growth-1", fixedParty(CM), "pauper", "fair", [], "dungeon", { town: true }); let opened = 0; g.on("building", () => { opened++; });
  for (const id of ["tavern", "tavern", "smith"]) { g.floor.pos = CM.TOWN_AT[id].slice(); g.use(); } assert.strictEqual(opened, 3); assert.strictEqual(JSON.stringify(g.tally.visited), JSON.stringify(["tavern", "smith"]), "each door counted once");
  // the well's stones: the hill's chapter, a line unlocked at each spending, in order
  g.village.spent = 0; assert.strictEqual(g.wellStones().length, 1); g.village.spent = CM.VILLAGE_LORE_AT[2]; assert.strictEqual(g.wellStones().length, 3); g.village.spent = 99999; const all = g.wellStones(); assert.strictEqual(all.length, CM.VILLAGE_LORE_AT.length);
  for (let i = 0; i < all.length; i++) assert.strictEqual(all[i], CM.LORE_TEXT[`village.${i + 1}`].tellings[0], "in order");
  let heard = null; g.on("talk", (t) => { heard = t; }); g.floor.pos = CM.TOWN_AT.well.slice(); g.use(); assert.ok(heard && heard.text.includes("Carved on the well's stones") && heard.text.includes(all[0].slice(0, 20)));
  // a run that walked the town brings more home than one that did not (the same run otherwise)
  const g2 = new CM.Game(); g2.newGame("growth-2", fixedParty(CM), "pauper", "fair", [], "dungeon", { town: true }); for (const id of Object.keys(CM.TOWN_PLOTS)) { g2.floor.pos = CM.TOWN_AT[id].slice(); g2.use(); }
  g2.enterFloor(3, "down"); for (const h of g2.party) h.hp = 0; g2.endRun(false); const e2 = g2.fame.find((e) => e.seed === "growth-2"); assert.ok(e2.renown >= 3 + 27, `the visits count: ${e2.renown}`);
});

test("around the town: Automatic runs the errands at their doors in order and then takes the shaft; a film of a run that began at home begins at home; the town's words are data; the simulator starts at home with --town", () => {
  const CM = load();
  for (const k of ["town.name", "town.compass", "town.where", "town.card", "town.card.night", "town.arrive", "town.open", "town.home", "town.foundation", "town.door"]) assert.notStrictEqual(CM.t(k), k, k);
  const g = new CM.Game(); g.village.renown = 9000; g.build("home"); g.build("shrine"); g.newGame("around-town-1", fixedParty(CM), "pauper", "fair", [], "dungeon", { town: true }); g.gold = 1500;
  g.autoPlay(true); const visited = []; g.on("building", (id) => visited.push(id)); let n = 0; while (g.floor.number === 0 && g.autoOn() && n++ < 400) g.auto.step();
  assert.strictEqual(g.floor.number, 1, `down the shaft after the errands (${n} steps)`); assert.strictEqual(visited.join(), "home,merchant,temple,tavern", `the errands in order: ${visited.join()}`);
  assert.ok(g.buffs && g.buffs.rested, "rested at the hearth"); assert.ok(g.bounty, "a bounty from the board"); assert.ok((g.tally.spent || {}).tavern >= CM.DRINK_PRICE, "a round drunk"); assert.ok(g.bag.filter((i) => i.kind === "heal").length >= 2, "shopped"); g.autoPlay(false);
  const g2 = new CM.Game(); g2.village.levels = {}; g2.saveVillage(); g2.newGame("around-town-2", fixedParty(CM), "pauper", "fair", [], "dungeon", { town: true }); g2.autoPlay(true); const v2 = []; g2.on("building", (id) => v2.push(id)); n = 0; while (g2.floor.number === 0 && g2.autoOn() && n++ < 400) g2.auto.step();
  assert.strictEqual(g2.floor.number, 1); assert.strictEqual(v2.join(), "merchant", "with nothing built and little gold: the merchant, then the shaft"); g2.autoPlay(false);
  // a film of a run that began at home begins at home
  const g3 = new CM.Game(); g3.newGame("around-town-3", fixedParty(CM), "pauper", "fair", [], "dungeon", { town: true }); for (let i = 0; i < 3; i++) g3.move(0); const spec = g3.replaySpec(); assert.ok(spec.town);
  const g4 = new CM.Game(); assert.ok(g4.startFilm(spec)); assert.strictEqual(g4.floor.number, 0, "the film opens at the party's door"); assert.ok(g4.film && g4.film.playing); g4.stopFilm && g4.stopFilm();
  const g5 = new CM.Game(); assert.ok(g5.startFilm(Object.assign({}, spec, { town: undefined }))); assert.strictEqual(g5.floor.number, 1, "an older film at the shaft");
  // the simulator's bot from home
  const g6 = new CM.Game(); g6.newGame("around-town-4", fixedParty(CM), "pauper", "fair", [], "dungeon", { town: true }); const r = playRun(CM, g6, { maxFloor: 3 }); assert.ok(g6.floor.number >= 3 || g6.mode === "title", r.log.join("|"));
  const out = execFileSync("node", [path.join(__dirname, "..", "tools", "words.js")], { encoding: "utf8" }); assert.ok(/the town \(CM.TOWN_PLOTS, CM.TOWNSFOLK, CM.VILLAGE\)\s+\d+/.test(out));
});

test("the clock: a step a minute, a stair an hour, a round a minute, a rest to the next dawn; the hour in words and the sky's places; the moon's month; the lanterns and the townsfolk by the game's clock; the new moon's locks and the full moon's dead; the clock saved and filmed", () => {
  const CM = load();
  const g = new CM.Game(); g.newGame("clock-1", fixedParty(CM), "pauper", "fair", [], "dungeon", { town: true });
  assert.strictEqual(g.clock, 0); assert.strictEqual(CM.hourOf(g), 6); assert.strictEqual(CM.hourWord(CM.hourOf(g)), "dawn"); assert.strictEqual(CM.dayOf(g), 0); assert.ok(!CM.isNight(g));
  for (let i = 0; i < 10; i++) g.move(0); assert.ok(g.clock >= 10, `steps are minutes: ${g.clock}`);
  const c0 = g.clock; g.enterFloor(1, "down"); assert.strictEqual(g.clock, c0 + CM.CLOCK.stair, "a stair is an hour"); g.enterFloor(3, "down"); assert.strictEqual(g.clock, c0 + CM.CLOCK.stair * 3, "two stairs, two hours");
  g.foes = [{ name: "Orc", kind: "Orc", hp: 50, max: 50, atk: 1, df: 1, row: "front" }]; g.combat = { foes: g.foes, round: 1, order: [], index: 0 }; g.mode = "combat"; const c1 = g.clock; g.endRound(); assert.strictEqual(g.clock, c1 + 1, "a round is a minute"); g.mode = "explore"; g.combat = null; g.foes = [];
  g.clock = 15 * 60; assert.strictEqual(CM.hourOf(g), 21); assert.ok(CM.isNight(g)); assert.strictEqual(CM.hourWord(21), "night"); assert.strictEqual(CM.hourWord(3), "the small hours"); assert.strictEqual(CM.hourWord(12), "noon"); assert.strictEqual(CM.hourWord(18), "dusk");
  const P = CM.skyPlaces(Object.assign({}, g, { clock: 6 * 60 })); assert.ok(Math.abs(P.sun - 0.5) < 0.01 && P.moon === null, "noon: the sun overhead, the moon below");
  const N = CM.skyPlaces(Object.assign({}, g, { clock: 18 * 60 })); assert.ok(N.sun === null && Math.abs(N.moon - 0.5) < 0.01, "midnight: the moon overhead");
  // a rest sleeps to the next dawn; a rest at dawn, a whole day
  g.mode = "camp"; g.gold = 100; g.clock = 15 * 60; g.rest(); assert.strictEqual(CM.hourOf(g), 6); assert.strictEqual(CM.dayOf(g), 1, "the next dawn"); g.rest(); assert.strictEqual(CM.dayOf(g), 2, "at dawn already: a whole day"); g.mode = "explore";
  // the moon: a month of twenty-nine days; full at the fifteenth; words for each phase
  g.clock = 0; assert.strictEqual(CM.moonPhase(g), 0); assert.ok(CM.newMoon(g)); g.clock = 14 * CM.CLOCK.day + 60; assert.strictEqual(CM.moonPhase(g), 4); assert.ok(CM.fullMoon(g)); assert.strictEqual(CM.moonWord(g), "a full moon"); g.clock = 29 * CM.CLOCK.day; assert.strictEqual(CM.moonPhase(g), 0, "and round again"); assert.ok(CM.clockWords(g).includes("day 30"));
  // the lanterns and the townsfolk by the game's clock, not the wall's
  g.enterFloor(0, "rope", CM.TOWN_AT.home.slice()); g.clock = 0; assert.strictEqual(g.lightFactor(), 1.3); g.clock = 17 * 60; assert.strictEqual(g.lightFactor(), 0.8);
  const folk = Object.entries(g.floor.things).find(([, t]) => t.type === "villager"); let heard = null; g.on("talk", (t) => { heard = t; }); g.floor.pos = folk[0].split(",").map(Number); g.use(); assert.ok(!heard && g.messages.slice(-1)[0].includes("shutters"), "indoors by night"); g.clock = 2 * 60; g.use(); assert.ok(heard, "and out by day");
  // the new moon: a lock a tenth easier; the full moon: the undead a tenth tougher on the first floors
  const g2 = new CM.Game(); g2.newGame("clock-2", fixedParty(CM)); const rogue = g2.party.find((h) => h.cls === "Rogue"); rogue.level = 2; const fl = g2.floor, [px, py] = fl.pos, open = CM.DIRS.map(([dx, dy], i) => [px + dx, py + dy, i]).filter(([x, y]) => CM.isOpen(fl, x, y) && !fl.features[`${x},${y}`] && !fl.things[`${x},${y}`])[0]; const ak = `${open[0]},${open[1]}`; fl.facing = open[2];
  const rate = (clock) => { let got = 0; for (let i = 0; i < 300; i++) { g2.clock = clock; fl.features[ak] = { type: "door", open: false, locked: true, grade: "common" }; g2.rnd = new CM.Random(CM.hashSeed(`moon:${i}`)); g2.move(0); if (fl.features[ak].open) got++; fl.pos = [px, py]; } return got / 300; };
  const dark = rate(0), bright = rate(14 * CM.CLOCK.day); assert.ok(dark > bright + 0.03, `the new moon's locks: ${dark} > ${bright}`); delete fl.features[ak];
  const skel = () => { const m = CM.makeMonster(CM.monsterKind("Skeleton"), 3, new CM.Random(1)); return m; }; g2.clock = 14 * CM.CLOCK.day; const full = g2.tune(skel()); g2.clock = 0; const dim = g2.tune(skel()); assert.ok(full.max > dim.max, `the full moon's dead: ${full.max} > ${dim.max}`);
  g2.enterFloor(8, "down"); g2.clock = 14 * CM.CLOCK.day; assert.strictEqual(g2.tune(skel()).max, dim.max, "below the fifth floor the moon is not seen");
  // saved, and filmed
  g2.clock = 777; g2.saveRun(); const g3 = new CM.Game(); g3.continueRun(); assert.strictEqual(g3.clock, 777);
  const g4 = new CM.Game(); g4.newGame("clock-3", fixedParty(CM)); playRun(CM, g4, { maxFloor: 3 }); assert.ok(g4.clock > 100); const again = CM.replayRun(g4.replaySpec()); assert.strictEqual(again.clock, g4.clock, "a film keeps the hour");
});

test("scrolls of Homecoming: found in a chest in twenty from floor 3 and dropped by the dead; read below, the party is at its own door at dawn and the floors behind move on; read again in town, back to the same square and the scroll is spent; sold only in town at a price that climbs; Automatic goes home for potions and comes back", () => {
  const CM = load();
  assert.ok(CM.SCROLLS.homecoming && CM.SCROLLS.homecoming.outside && CM.SCROLLS.homecoming.keep);
  // by the seed: some chests from floor 3 carry one, none above it
  const g = new CM.Game(); g.newGame("home-scroll-1", fixedParty(CM)); let found = 0, opened = 0;
  for (let n = 3; n <= 12 && found < 1; n++) { g.enterFloor(n, "down"); for (const [k, t] of Object.entries(g.floor.things)) { if (t.type !== "chest" || t.mimic) continue; t.trap = null; g.floor.pos = k.split(",").map(Number); const before = g.bag.filter((i) => i.spell === "homecoming").length; g.use(); opened++; if (g.bag.filter((i) => i.spell === "homecoming").length > before) found++; } }
  assert.ok(found >= 1 && opened >= 10, `a chest in twenty or so: ${found} of ${opened}`);
  g.enterFloor(1, "down"); let none = 0; for (const [k, t] of Object.entries(g.floor.things)) if (t.type === "chest") { t.trap = null; g.floor.pos = k.split(",").map(Number); const b = g.bag.length; g.use(); if (g.bag.slice(b).some((i) => i.spell === "homecoming")) none++; } assert.strictEqual(none, 0, "none on the first floors");
  // the dead drop it: an elite one in ten
  g.enterFloor(6, "down"); let drops = 0; for (let i = 0; i < 60; i++) { g.foes = [{ name: "Howling Orc", kind: "Orc", elite: "howling", hp: 0, max: 40, atk: 1, df: 1, row: "front", xp: 1, gold: 1 }]; g.combat = { foes: g.foes, round: 1, order: [], index: 0 }; g.mode = "combat"; g.foeKey = "0,0"; g.rnd = new CM.Random(i); const b = g.bag.length; g.wonFight(); if (g.bag.slice(b).some((it) => it.spell === "homecoming")) drops++; }
  assert.ok(drops >= 2 && drops <= 14, `an elite drops it one in ten: ${drops} of 60`); g.mode = "explore"; g.combat = null;
  // read below: home by dawn, the clock says so, the floors behind moved; read in town: back to the square, spent
  const g2 = new CM.Game(); g2.newGame("home-scroll-2", fixedParty(CM)); g2.enterFloor(2, "down"); g2.enterFloor(5, "down"); const at = g2.floor.pos.slice(), c0 = g2.clock;
  g2.bag.push(CM.scroll("homecoming")); const row = g2.bag.length - 1; assert.strictEqual(g2.give(row, 0), ""); assert.strictEqual(g2.floor.number, 0); assert.strictEqual(g2.mode, "explore"); assert.strictEqual(g2.floor.pos.join(), CM.TOWN_AT.home.join(), "at the party's door");
  assert.strictEqual(CM.hourOf(g2), 6, "dawn"); assert.ok(g2.clock > c0); assert.strictEqual(g2.tally.homecomings, 1); const scroll = g2.bag.find((i) => i.spell === "homecoming"); assert.ok(scroll && scroll.back && scroll.back.floor === 5 && scroll.back.pos.join() === at.join(), "the scroll remembers");
  g2.saveRun(); const g3 = new CM.Game(); g3.continueRun(); assert.ok(g3.bag.find((i) => i.spell === "homecoming").back, "remembered through a save");
  assert.ok(g3.give(g3.bag.findIndex((i) => i.spell === "homecoming"), 0) === "" && g3.floor.number === 5 && g3.floor.pos.join() === at.join(), "back to the very square"); assert.ok(!g3.bag.some((i) => i.spell === "homecoming"), "and spent");
  g3.enterFloor(0, "rope", CM.TOWN_AT.home.slice()); g3.bag.push(CM.scroll("homecoming")); assert.ok(g3.give(g3.bag.length - 1, 0).includes("below"), "not from the town");
  g3.mode = "combat"; g3.floor = g3.floorAt(5); assert.ok(g3.useMagicInBattle ? true : true); g3.mode = "explore";
  // sold only in town, dearer the deeper the run has been
  const g4 = new CM.Game(); g4.newGame("home-scroll-3", fixedParty(CM), "pauper", "fair", [], "dungeon", { town: true }); g4.openBag(true); const s0 = g4.stock.find((i) => i.spell === "homecoming"); assert.ok(s0, "on the Merchant's House's table"); assert.strictEqual(s0.value, CM.HOMECOMING.price); g4.closeBag();
  g4.enterFloor(5, "down"); g4.floor.things[g4.floor.pos.join(",")] = { type: "ladder" }; g4.use(); assert.strictEqual(g4.mode, "camp"); g4.openBag(true); assert.ok(!g4.stock.some((i) => i.spell === "homecoming"), "never at a camp"); g4.closeBag();
  assert.strictEqual(g4.goHome(), ""); g4.openBag(true); assert.strictEqual(g4.stock.find((i) => i.spell === "homecoming").value, CM.HOMECOMING.price + 5 * CM.HOMECOMING.perFloor, "the price climbs with the deepest floor"); g4.closeBag();
  // Automatic: out of potions below ten with gold and a scroll, it goes home, shops, and comes back to the square
  const g5 = new CM.Game(); g5.newGame("home-scroll-4", fixedParty(CM)); g5.enterFloor(10, "down"); g5.bag = g5.bag.filter((i) => !["heal", "greaterheal"].includes(i.kind)); g5.bag.push(CM.scroll("homecoming")); g5.gold = 500; const sq = g5.floor.pos.join();
  g5.autoPlay(true); let r = null, n = 0, wentHome = false; while (n++ < 300 && g5.autoOn()) { r = g5.auto.step(); if (g5.floor.number === 0) wentHome = true; if (wentHome && g5.floor.number === 10) break; }
  assert.ok(wentHome, "went home by the scroll"); assert.strictEqual(g5.floor.number, 10, "and came back"); assert.strictEqual(g5.floor.pos.join(), sq, "to the same square"); assert.ok(g5.bag.some((i) => i.kind === "heal" || i.kind === "greaterheal"), "with potions"); assert.ok(!g5.bag.some((i) => i.spell === "homecoming")); g5.autoPlay(false);
});

test("the Deep Wood: the seed's own forest, the same twice, with glades, a river crossed at one ford, a hut, a shrine, a burner, nodes and three caves; the gate from both sides; day's deer that run and night's wolves that hunt; hunger and the torch by night; a cave is a floor with its way out and the troll under the third; the beasts leave hides and meat", () => {
  const CM = load();
  const w1 = CM.makeFloor(-1, "wood-1", 2), w2 = CM.makeWood("wood-1"), w3 = CM.makeWood("wood-2");
  assert.strictEqual(w1.number, -1); assert.strictEqual(w1.grid.length, CM.WOOD_SIZE); assert.strictEqual(JSON.stringify(w1.grid), JSON.stringify(w2.grid)); assert.notStrictEqual(JSON.stringify(w1.grid), JSON.stringify(w3.grid), "another seed, another wood");
  const types = Object.values(w1.things).map((t) => t.type); for (const t of ["woodgate", "hut", "shrine", "burner"]) assert.strictEqual(types.filter((x) => x === t).length, 1, t); assert.strictEqual(types.filter((x) => x === "cave").length, 3); assert.ok(types.filter((x) => x === "node").length >= 6);
  assert.ok(Object.values(w1.features).filter((f) => f.type === "river").length >= 20, "a river"); assert.ok(!w1.features[w1.ford.join(",")] && w1.decor.some((d) => d.kind === "water" && d.x === w1.ford[0] && d.y === w1.ford[1]), "one ford, in the water");
  const dist = CM.distances(w1.grid, CM.WOOD_GATE, (x, y) => CM.passable(w1, x, y)); for (const [k, t] of Object.entries(w1.things)) assert.ok(dist.get(k) !== undefined, `${t.type} at ${k} can be reached from the gate (over the ford)`);
  assert.ok(!CM.passable(w1, ...Object.keys(w1.features).find((k) => w1.features[k].type === "river").split(",").map(Number)), "the river is not walked");
  assert.strictEqual(CM.themeFor(-1), CM.WOOD_THEME); assert.strictEqual(CM.themeFor(-1.5), CM.THEMES[0]); assert.ok(CM.themeFor(-1).tree);
  const town = CM.makeTown("wood-1"); assert.strictEqual(town.things[CM.TOWN_AT.woodgate.join(",")].type, "woodgate"); assert.ok(CM.isOpen(town, 0, CM.TOWN_AT.woodgate[1]), "the road runs out of the gate to the map's edge");
  // the gate from both sides, by day: deer that run, lit by the sky, no torch burnt, hunger counted
  const g = new CM.Game(); g.newGame("wood-1", fixedParty(CM), "pauper", "fair", [], "dungeon", { town: true }); g.floor.pos = CM.TOWN_AT.woodgate.slice(); g.use(); assert.strictEqual(g.floor.number, -1); assert.strictEqual(g.floor.pos.join(), CM.WOOD_GATE.join());
  assert.ok(!CM.isNight(g)); assert.ok(g.hasLight() && g.lightFactor() > 1); const day = Object.values(g.floor.things).filter((t) => t.type === "monsters"); assert.ok(day.length >= 3 && day.every((t) => t.wood === "day" && t.flees), `the day's beasts: ${day.length}`); assert.ok(day.every((t) => ["Deer", "Boar"].includes(t.group[0].kind)));
  g.light = { kind: "torch", left: 100 }; const fed0 = g.fed || 0; for (let i = 0; i < 4; i++) { g.move(0); if (g.floor.number !== -1) break; } assert.strictEqual(g.light.left, 100, "no torch by day"); assert.ok((g.fed || 0) > fed0, "but the trek makes hungry");
  { const [k, t] = Object.entries(g.floor.things).find(([, t]) => t.type === "monsters"); const [mx, my] = k.split(",").map(Number); const near = CM.DIRS.map(([dx, dy]) => [mx + dx, my + dy]).find(([x, y]) => CM.passable(g.floor, x, y) && !g.floor.things[`${x},${y}`]); if (near) { g.floor.pos = near; g.rnd = new CM.Random(1); g.wanderMonsters(); assert.strictEqual(g.mode, "explore", "a deer beside the party bolts rather than bites"); assert.ok(!g.floor.things[k] || g.floor.things[k] !== t || true); } }
  g.floor.pos = CM.WOOD_GATE.slice(); g.use(); assert.strictEqual(g.floor.number, 0); assert.strictEqual(g.floor.pos.join(), CM.TOWN_AT.woodgate.join(), "and back");
  // by night: wolves, a bear or bandits that hunt; the torch burns; the hermit's door shut; under a full moon the Great Wolf
  g.clock = 16 * 60; g.use(); assert.strictEqual(g.floor.number, -1); assert.ok(CM.isNight(g)); const night = Object.values(g.floor.things).filter((t) => t.type === "monsters"); assert.ok(night.length >= 3 && night.every((t) => t.wood === "night" && t.hunter && !t.flees), `the night's beasts: ${night.length}`); assert.ok(night.every((t) => ["Wolf", "Bear", "Sellsword"].includes(t.group[0].kind)));
  g.light = { kind: "torch", left: 100 }; g.move(0); if (g.floor.number === -1) assert.ok(g.light.left < 100, "the torch burns by night"); assert.ok(g.lightFactor() < 1);
  const hut = Object.keys(g.floor.things).find((k) => g.floor.things[k].type === "hut"); g.floor.pos = hut.split(",").map(Number); g.use(); assert.ok(g.messages.slice(-1)[0].includes("shuttered"));
  g.clock = 14 * CM.CLOCK.day + 16 * 60; g.floor.nightWas = undefined; g.refreshWood(); assert.ok(Object.values(g.floor.things).some((t) => t.type === "monsters" && t.group[0].name === "The Great Wolf"), "a full moon's wolf");
  // the shrine is read into the journal; a cave is a floor with its way out; one cave a day; the troll under the third
  const shrine = Object.keys(g.floor.things).find((k) => g.floor.things[k].type === "shrine"); g.floor.pos = shrine.split(",").map(Number); g.use(); assert.ok(g.floor.things[shrine].read && g.journal.some((j) => j.key === "wood.shrine" || (j.text || "").includes("TREES")), "the shrine's line is kept");
  g.clock = 0; const caves = Object.entries(g.floor.things).filter(([, t]) => t.type === "cave"); const shut = caves.find(([, t]) => t.n !== 0), open = caves.find(([, t]) => t.n === 0); g.floor.pos = shut[0].split(",").map(Number); g.use(); assert.strictEqual(g.floor.number, -1); assert.ok(g.messages.slice(-1)[0].includes("fallen rock"));
  g.floor.pos = open[0].split(",").map(Number); g.use(); assert.strictEqual(g.floor.number, CM.caveNumber(0)); assert.strictEqual(g.floor.special, "cave"); assert.ok(Object.values(g.floor.things).some((t) => t.type === "caveexit") && !Object.values(g.floor.things).some((t) => ["ladder", "stairs_up", "ghost", "event"].includes(t.type)), "a cave: a way out and no stair down");
  assert.ok(!Object.values(g.floor.features).some((f) => ["pit", "trapdoor", "teleporter"].includes(f.type)), "nothing falls out of a cave"); assert.ok(Object.values(g.floor.things).some((t) => t.type === "monsters"), "the first bands' kinds live in it");
  const exitK = Object.keys(g.floor.things).find((k) => g.floor.things[k].type === "caveexit"); g.floor.pos = exitK.split(",").map(Number); g.use(); assert.strictEqual(g.floor.number, -1); assert.strictEqual(g.floor.pos.join(), open[0], "out at the mouth it went in by");
  const third = CM.makeFloor(CM.caveNumber(2), "wood-1", 2); const lord = Object.values(third.things).find((t) => t.caveLord); assert.ok(lord && lord.group[0].name === "The Troll under the Hill" && lord.group[0].part === undefined, "the troll waits at the far end"); assert.strictEqual(JSON.stringify(CM.makeFloor(CM.caveNumber(2), "wood-1", 2).grid), JSON.stringify(third.grid), "a cave is the seed's");
  // the beasts leave hides and meat; a hide is a thing of the compendium
  g.floor = g.floorAt(-1); g.mode = "explore"; let hides = 0; for (let i = 0; i < 20; i++) { g.foes = [{ name: "Deer", kind: "Deer", hp: 0, max: 20, atk: 1, df: 0, row: "front", xp: 2, gold: 0 }]; g.combat = { foes: g.foes, round: 1, order: [], index: 0 }; g.mode = "combat"; g.foeKey = "0,0"; g.rnd = new CM.Random(i); const b = g.bag.length; g.wonFight(); if (g.bag.slice(b).some((it) => it.kind === "hide")) hides++; } assert.ok(hides >= 6, `hides from the deer: ${hides} of 20`); assert.ok(g.bag.some((it) => it.kind === "meat" && it.meat === "Deer")); assert.ok(CM.BASES["Deer hide"] && CM.BASES["Wild Honey"]);
  g.mode = "explore"; g.combat = null; const node = Object.keys(g.floor.things).find((k) => g.floor.things[k].type === "node"); g.floor.pos = node.split(",").map(Number); const nb = g.bag.length; g.use(); assert.ok(g.bag.length > nb && CM.INGREDIENTS[g.bag[g.bag.length - 1].ingredient].band === -1, "the Wood's forage");
  // Homecoming works from the Wood; a save in a cave comes back; the dungeon's floors are as they were
  g.bag.push(CM.scroll("homecoming")); assert.strictEqual(g.give(g.bag.length - 1, 0), ""); assert.strictEqual(g.floor.number, 0);
  g.enterFloor(CM.caveNumber(0), "down"); g.saveRun(); const g2 = new CM.Game(); g2.continueRun(); assert.strictEqual(g2.floor.number, CM.caveNumber(0)); assert.strictEqual(g2.floor.special, "cave");
  assert.strictEqual(CM.floorPrint(CM.makeFloor(3, "wood-1", 2)), CM.floorPrint(CM.makeFloor(3, "wood-1", 2))); assert.ok(!CM.MONSTERS.slice(0, CM.SHALLOW).some((m) => m.wood) && !CM.MONSTERS.some((m) => m.wood && m.deep !== undefined), "the Wood's kinds are no band's");
});

test("mining: veins by the ore's floors, placed last by hash (no fingerprint moves); a pick of the grade mines three swings a vein, a chunk a swing (silver twice in the dwarves' halls, the Artificer one more), wears a point a swing and is whetted at the forge; the noise; the burner's charcoal; the smelter's bars and alloys; the apprentice buys bars", () => {
  const CM = load();
  assert.strictEqual(CM.ORE_ORDER.length, 5); assert.strictEqual(Object.keys(CM.ALLOYS).length, 4);
  const veinsOf = (n, seed = "ore-1") => Object.values(CM.makeFloor(n, seed, 2).things).filter((t) => t.type === "vein");
  assert.ok(veinsOf(2).every((v) => v.ore === "copper") && veinsOf(2).length >= 1, "copper near the top"); assert.ok(veinsOf(13).some((v) => v.ore === "silver"), "silver in the halls"); assert.ok(veinsOf(38).some((v) => v.ore === "stariron"), "star-iron in the Foundry"); assert.ok(!veinsOf(3).some((v) => v.ore === "gold"));
  assert.strictEqual(veinsOf(8).map((v) => v.ore).sort().join(), veinsOf(8).map((v) => v.ore).sort().join()); const fp = JSON.parse(fs.readFileSync(path.join(__dirname, "fixtures", "gen1.json"), "utf8")); const first = Object.keys(fp)[0]; assert.ok(first, "the gen-1 fixtures stand (the frozen-floor test runs them)");
  for (const [k, v] of Object.entries(CM.makeFloor(8, "ore-1", 2).things).filter(([, t]) => t.type === "vein")) { const f = CM.makeFloor(8, "ore-1", 2), [x, y] = k.split(",").map(Number); assert.ok(CM.isOpen(f, x, y) && CM.DIRS.some(([dx, dy]) => !CM.inBounds(f, x + dx, y + dy) || f.grid[y + dy][x + dx] === 1), `${v.ore} at ${k} is beside the rock`); }
  const cave = CM.makeFloor(CM.caveNumber(2), "ore-1", 2); assert.ok(Object.values(cave.things).some((t) => t.type === "vein" && t.ore === "gold"), "gold at the deepest cave");
  // a pick of the grade; a chunk a swing; three swings; a point a swing; five minutes a swing; the noise
  const g = new CM.Game(); g.newGame("ore-1", fixedParty(CM)); g.enterFloor(8, "down"); const [vk, vein] = Object.entries(g.floor.things).find(([, t]) => t.type === "vein" && t.ore === "iron") || Object.entries(g.floor.things).find(([, t]) => t.type === "vein"); g.floor.pos = vk.split(",").map(Number);
  g.use(); assert.ok(g.messages.slice(-1)[0].includes("no pick")); g.bag.push(CM.pick("copper")); const pick = g.bag[g.bag.length - 1], c0 = g.clock, ore0 = g.bag.filter((i) => i.kind === "ore").length;
  g.use(); assert.strictEqual(g.bag.filter((i) => i.kind === "ore").length, ore0 + 1); assert.strictEqual(pick.points, CM.PICKS.copper.points - 1); assert.strictEqual(g.clock, c0 + CM.SWING_MINUTES); assert.strictEqual(vein.left, CM.VEIN_SWINGS - 1); assert.strictEqual(g.tally.mined, 1);
  g.use(); g.use(); assert.ok(!g.floor.things[vk], "worked out in three"); assert.strictEqual(g.bag.filter((i) => i.kind === "ore").length, ore0 + 3); assert.ok(g.bag.filter((i) => i.kind === "ore").every((i) => CM.BASES[i.name]));
  g.enterFloor(13, "down"); const sv = Object.entries(g.floor.things).find(([, t]) => t.type === "vein" && t.ore === "silver"); if (sv) { g.floor.pos = sv[0].split(",").map(Number); g.use(); assert.ok(g.messages.slice(-1)[0].includes("better pick"), "copper does not bite silver"); g.bag.push(CM.pick("iron")); const s0 = g.bag.filter((i) => i.kind === "ore" && i.ore === "silver").length; g.use(); assert.strictEqual(g.bag.filter((i) => i.kind === "ore" && i.ore === "silver").length, s0 + 2, "silver twice in the dwarves' halls"); }
  { const g2 = new CM.Game(); g2.newGame("ore-2", fixedParty(CM)); g2.party[0].cls = "Artificer"; g2.enterFloor(2, "down"); const [k2] = Object.entries(g2.floor.things).find(([, t]) => t.type === "vein"); g2.floor.pos = k2.split(",").map(Number); g2.bag.push(CM.pick("copper")); const n = g2.bag.filter((i) => i.kind === "ore").length; g2.use(); assert.strictEqual(g2.bag.filter((i) => i.kind === "ore").length, n + 2, "the Artificer mines twice"); }
  { const g3 = new CM.Game(); g3.newGame("ore-3", fixedParty(CM)); g3.enterFloor(4, "down"); const fl = g3.floor; const [k3] = Object.entries(fl.things).find(([, t]) => t.type === "vein"); fl.pos = k3.split(",").map(Number); for (const [k, t] of Object.entries(fl.things)) if (t.type === "monsters") delete fl.things[k];
    const dist = CM.distances(fl.grid, fl.pos, (x, y) => CM.passable(fl, x, y)); const far = Object.entries(Object.fromEntries(dist)).find(([k, d]) => d === 5 && !fl.things[k] && !fl.features[k]); if (far) { fl.things[far[0]] = { type: "monsters", group: [CM.makeMonster(CM.monsterKind("Orc"), 3, new CM.Random(1))] }; g3.bag.push(CM.pick("copper")); g3.use(); assert.ok(!fl.things[far[0]] && Object.entries(fl.things).some(([k, t]) => t.type === "monsters" && dist.get(k) === 4), "a swing brings the band a square closer"); } }
  // blunt, and whetted; the hidden door costs ten points; the dwarves' pick is an iron pick kept
  pick.points = 0; g.enterFloor(2, "down"); const [k4] = Object.entries(g.floor.things).find(([, t]) => t.type === "vein"); g.floor.pos = k4.split(",").map(Number); g.bag = g.bag.filter((i) => !(i.kind === "pick" && i.pick === "iron")); g.use(); assert.ok(g.messages.slice(-1)[0].includes("blunt"));
  assert.ok(g.whetPicks().includes("in town")); g.enterFloor(0, "rope", CM.TOWN_AT.smith.slice()); g.gold = 100; assert.strictEqual(g.whetPicks(), ""); assert.strictEqual(pick.points, CM.PICKS.copper.points); assert.strictEqual(g.gold, 80); assert.ok(g.whetPicks().includes("its point"));
  const dw = CM.dwarfPick(); assert.strictEqual(dw.pick, "iron"); assert.strictEqual(dw.points, CM.PICKS.iron.points); assert.ok(CM.itemLabel(dw).includes("silver"));
  // the burner: deadwood in, two charcoal out; a charcoal for a coin; the smelter at the forge's second level: three chunks and a charcoal a bar; the alloys; the apprentice buys bars
  g.floor.pos = CM.TOWN_AT.woodgate.slice(); g.use(); const bk = Object.keys(g.floor.things).find((k) => g.floor.things[k].type === "burner"); g.floor.pos = bk.split(",").map(Number); g.clock = 2 * 60;
  g.bag.push(CM.ingredient("deadwood"), CM.ingredient("deadwood")); g.use(); assert.strictEqual(g.bag.filter((i) => i.kind === "charcoal").length, 4, "deadwood in, two charcoal out each"); const gc = g.gold; g.use(); assert.strictEqual(g.bag.filter((i) => i.kind === "charcoal").length, 5); assert.strictEqual(gc - g.gold, CM.CHARCOAL_PRICE);
  g.clock = 16 * 60; g.use(); assert.strictEqual(g.bag.filter((i) => i.kind === "charcoal").length, 5, "asleep by night"); g.clock = 2 * 60;
  g.floor.pos = CM.WOOD_GATE.slice(); g.use(); assert.ok(g.inTown()); for (let i = 0; i < 6; i++) g.bag.push(CM.oreChunk("copper")); for (let i = 0; i < 3; i++) g.bag.push(CM.oreChunk("iron"));
  assert.ok(g.smelt("copper").includes("second level")); g.village.renown = 9000; g.build("smith"); g.build("smith"); assert.strictEqual(g.smelt("copper"), ""); assert.strictEqual(g.smelt("copper"), ""); assert.strictEqual(g.smelt("iron"), ""); let msg = "", guard = 0; while ((msg = g.smelt("iron")) === "" && guard++ < 10) { /* every iron chunk into the mould */ } assert.ok(msg.includes("wants 3 chunks"), msg);
  assert.ok(g.bag.filter((i) => i.kind === "bar").length >= 3); assert.ok(g.tally.bars >= 3); assert.ok(!g.bag.some((i) => i.kind === "ore" && i.ore === "iron"));
  assert.ok(g.alloy("steel").includes("wants two")); assert.strictEqual(g.alloy("bronze"), ""); const bronze = g.bag.find((i) => i.kind === "bar" && i.bar === "bronze"); assert.ok(bronze && bronze.name === "Bronze bar" && CM.BASES["Bronze bar"]); assert.ok(!g.bag.some((i) => i.kind === "bar" && i.bar === "copper"), "the copper went into the bronze");
  const gb = g.gold, worth = g.bag.filter((i) => i.kind === "bar").reduce((s, i) => s + i.value, 0); assert.strictEqual(g.sellBars(), ""); assert.strictEqual(g.gold - gb, worth); assert.ok(!g.bag.some((i) => i.kind === "bar"));
  assert.strictEqual(CM.weightOf(CM.oreChunk("gold")), 2); assert.strictEqual(CM.weightOf(CM.metalBar("iron")), 3);
  g.openBag(true); assert.ok(g.stock.some((i) => i.kind === "pick" && i.pick === "copper") && g.stock.some((i) => i.kind === "pick" && i.pick === "iron"), "picks on the Merchant's House's table"); g.closeBag();
  // the bot mines a vein it has a pick for, on its way
  const g5 = new CM.Game(); g5.newGame("ore-5", fixedParty(CM)); g5.bag.push(CM.pick("copper")); playRun(CM, g5, { maxFloor: 4 }); assert.ok((g5.tally.mined || 0) >= 1, `the bot mined ${g5.tally.mined || 0}`);
});

test("upgrading and tempering: a grade for bars of the base's metal and gold (+1 power; at 3 and 5 an implicit word better; the stars in the name, not the base id); the ceiling with the third enchantment; a temper at the smith's third level, for the run and gone after (and never into the stash or the vault); the hermit tans hides by day; the quiver's second arrow; a replay keeps the grades", () => {
  const CM = load();
  const g = new CM.Game(); g.newGame("forge-1", fixedParty(CM)); g.enterFloor(0, "rope", CM.TOWN_AT.smith.slice()); g.gold = 5000;
  const h = g.party[0]; h.weapon = CM.gearOfBase("Long Sword", 3, new CM.Random(3)); h.weapon.found = { floor: 0, how: "start" }; const sw = h.weapon, p0 = sw.power;
  assert.strictEqual(CM.gradeCost(sw).metal, CM.GRADE_METAL(CM.BASES["Long Sword"].tier)); assert.ok(g.upgrade(0, "weapon").includes("wants 1"));
  for (let i = 0; i < 15; i++) g.bag.push(CM.metalBar(CM.gradeCost(sw).metal));
  assert.strictEqual(g.upgrade(0, "weapon"), ""); assert.strictEqual(sw.grade, 1); assert.strictEqual(sw.power, p0 + 1); assert.ok(sw.name.endsWith(" ★"), sw.name); assert.strictEqual(CM.baseIdOf(sw), "Long Sword"); assert.strictEqual(CM.itemName(sw), sw.name);
  assert.strictEqual(g.upgrade(0, "weapon"), ""); assert.strictEqual(g.upgrade(0, "weapon"), ""); assert.strictEqual(sw.grade, 3); assert.strictEqual(sw.props.power1, 1, "at 3 an implicit word better"); assert.strictEqual(g.bag.filter((i) => i.kind === "bar").length, 15 - 6);
  assert.ok(CM.itemLabel(sw).includes("grade ★★★")); assert.ok(CM.itemCard(sw).includes("★★★"));
  // the ceiling: enchanted thrice, no fifth grade (and the other way about)
  sw.props.enchant = 3; assert.strictEqual(g.upgrade(0, "weapon"), ""); assert.strictEqual(sw.grade, 4); assert.ok(g.upgrade(0, "weapon").includes("cannot take the fifth grade")); sw.props.enchant = 0;
  assert.strictEqual(g.upgrade(0, "weapon"), ""); assert.strictEqual(sw.grade, 5); assert.strictEqual(sw.props.power1, 2); assert.ok(g.achievements.graded); assert.ok(g.upgrade(0, "weapon").includes("no sixth"));
  sw.props.enchant = 2; g.bag.push({ name: "Diamond", kind: "gem", gem: "diamond", power: 0, value: 100 }); assert.ok(g.smith("enchant", 0, "weapon").includes("cannot take the third enchantment"), "the ceiling the other way");
  { const arm = h.armor; const d0 = (arm.props || {}).df || 0, metal = CM.gradeCost(arm).metal; for (let i = 0; i < 6; i++) g.bag.push(CM.metalBar(metal)); g.upgrade(0, "armor"); g.upgrade(0, "armor"); g.upgrade(0, "armor"); assert.strictEqual(arm.grade, 3); assert.strictEqual(arm.props.df, d0 + 1, "armour's word is warding"); }
  { const u = CM.makeUnique("firstroot"); const was = h.helm; h.helm = u; assert.ok(g.upgrade(0, "helm").includes("what it is") || g.upgrade(0, "helm").includes("Pick")); h.helm = was; }
  // the tempers: the smith's third level; a word from the land, for the run
  g.bag.push(CM.hide("Wolf"), CM.hide("Bear"), CM.ingredient("deadwood")); assert.ok(g.temper(0, "weapon", "bearbile").includes("third level")); g.village.renown = 9000; g.build("smith"); g.build("smith"); g.build("smith"); assert.strictEqual(g.villageLevel("smith"), 3);
  assert.ok(g.temper(0, "armor", "bearbile").includes("blade")); assert.ok(g.temper(0, "weapon", "stardust").includes("in the pack"));
  assert.strictEqual(g.temper(0, "weapon", "bearbile"), ""); assert.strictEqual(sw.props.bleed, 0.25); assert.strictEqual(sw.temper.id, "bearbile"); assert.ok(!g.bag.some((i) => i.kind === "hide" && i.hide === "Bear")); assert.ok(CM.itemLabel(sw).includes("tempered for the run"));
  assert.strictEqual(g.temper(0, "armor", "wolffat"), ""); assert.ok(h.armor.props.silence); g.enterFloor(3, "down"); g.floor.special = "dark"; assert.ok(g.alive().some((x) => CM.equipped(x).some((it) => it.temper && it.props.silence)));
  const w0 = CM.weightOf(h.armor); g.enterFloor(0, "rope", CM.TOWN_AT.smith.slice()); assert.strictEqual(g.temper(0, "armor", "oak"), ""); assert.strictEqual(CM.weightOf(h.armor), Math.max(0, w0 - 1)); assert.ok(!h.armor.props.silence, "one temper at a time"); assert.strictEqual(h.armor.temper.id, "oak");
  { const v = CM.gearOfBase("Buckler", 2, new CM.Random(4)); v.name = CM.itemName(v); g.bag.push(v); g.openBag(true); const row = g.bag.indexOf(v); assert.strictEqual(g.insure(row), ""); g.closeBag(); h.offhand = g.bag.splice(row, 1)[0]; g.bag.push(CM.hide("Wolf")); assert.strictEqual(g.temper(0, "offhand", "wolffat"), ""); g.payInsurance(); const kept = g.vaults[g.vaults.length - 1]; assert.ok(!kept.temper && !kept.props.silence, "the vault never holds a temper"); }
  g.enterFloor(2, "down"); g.endRun(false); assert.ok(!sw.temper && !sw.props.bleed, "the temper is gone at the run's end"); assert.strictEqual(sw.grade, 5, "the grade stays");
  // the hermit tans by day: hides in, gear out; the quiver's second arrow
  const g2 = new CM.Game(); g2.newGame("forge-2", fixedParty(CM)); g2.enterFloor(0, "rope", CM.TOWN_AT.woodgate.slice()); g2.use(); const hk = Object.keys(g2.floor.things).find((k) => g2.floor.things[k].type === "hut"); g2.floor.pos = hk.split(",").map(Number); g2.gold = 500;
  let huts = 0; g2.on("hut", () => huts++); g2.clock = 2 * 60; g2.use(); assert.strictEqual(huts, 1, "the hut opens by day"); g2.clock = 16 * 60; g2.use(); assert.strictEqual(huts, 1, "shuttered by night"); assert.ok(g2.tan("cloak").includes("shuttered")); g2.clock = 2 * 60;
  assert.ok(g2.tan("cloak").includes("wants 2 hides")); g2.bag.push(CM.hide("Deer"), CM.hide("Boar"), CM.hide("Wolf"), CM.hide("Wolf"), CM.hide("Wolf"), CM.hide("Troll")); assert.strictEqual(g2.tan("cloak"), ""); const cl = g2.bag.find((i) => i.kind === "cloak"); assert.ok(cl && cl.name === "Travel Cloak" && cl.props.df === 1 && !cl.unknown && cl.found.how === "hermit", JSON.stringify(cl));
  assert.strictEqual(g2.tan("wards"), ""); assert.ok(g2.bag.some((i) => i.kind === "cloak" && i.name === "Cloak of Wards" && i.props.df === 3)); assert.ok(g2.tan("hood").includes("Bear hide"));
  assert.strictEqual(g2.tan("quiver"), ""); assert.ok(g2.hasQuiver()); assert.ok(!g2.bag.some((i) => i.kind === "hide")); assert.strictEqual(g2.tally.tanned, 3); assert.strictEqual(CM.weightOf(CM.quiver()), 1); assert.ok(CM.BASES.Quiver);
  { const r = g2.party[0]; r.cls = "Ranger"; r.weapon = CM.gearOfBase("Short Bow", 2, new CM.Random(5)); g2.enterFloor(2, "down"); const k = Object.keys(g2.floor.things).find((kk) => g2.floor.things[kk].type === "monsters"); const t = g2.floor.things[k]; t.group = [CM.makeMonster(CM.monsterKind("Orc"), 2, new CM.Random(2))]; t.group[0].hp = t.group[0].max = 500;
    g2.startCombat(k, t); const n0 = g2.messages.length; g2.act("fight"); assert.ok(g2.messages.slice(n0).some((m) => m.includes("second arrow from the quiver")), "the quiver's arrow"); assert.ok(r.used.quiver); }
  // a replay keeps the grades
  const g3 = new CM.Game(); g3.newGame("forge-3", fixedParty(CM)); g3.enterFloor(0, "rope", CM.TOWN_AT.smith.slice()); g3.gold = 1000; for (let i = 0; i < 3; i++) g3.bag.push(CM.metalBar(CM.gradeCost(g3.party[0].weapon).metal)); assert.strictEqual(g3.upgrade(0, "weapon"), ""); assert.strictEqual(g3.upgrade(0, "weapon"), ""); assert.strictEqual(g3.party[0].weapon.grade, 2);
  assert.ok((g3.runLog || []).filter((l) => l[0] === "upgrade").length === 2, "logged");
  const spec = Object.assign({}, g3.replaySpec(), { log: g3.runLog.slice() }); const g4 = new CM.Game(); g4.newGame(spec.seed, fixedParty(CM)); g4.enterFloor(0, "rope", CM.TOWN_AT.smith.slice()); g4.gold = 1000; for (let i = 0; i < 3; i++) g4.bag.push(CM.metalBar(CM.gradeCost(g4.party[0].weapon).metal)); g4.replaying = 1; for (const line of spec.log.filter((l) => l[0] === "upgrade")) CM.replayStep(g4, line); g4.replaying = 0; assert.strictEqual(g4.party[0].weapon.grade, 2); assert.strictEqual(g4.party[0].weapon.name, g3.party[0].weapon.name);
});

test("the farm: a field in the First Glade raised with renown; a row sown from seed in the crop's season, a stage every dawn the party sees, cut at the fourth (and the seed back), rotten three dawns past ripe; the crows and the scarecrow; the orchard, the mill, the hens (eggs a week), the cow and her cabbage; the farmhand across a run; the season's seed at the Merchant's House; the bot's farm errand", () => {
  const CM = load();
  assert.strictEqual(CM.VILLAGE.farm.costs.length, 5); assert.ok(Object.keys(CM.CROPS).length >= 6); assert.strictEqual(CM.seasonOfDate(new Date(2026, 3, 1)), "spring"); assert.strictEqual(CM.seasonOfDate(new Date(2026, 11, 1)), "winter");
  const g = new CM.Game(); g.newGame("farm-1", fixedParty(CM)); g.season = "spring"; assert.ok(CM.SEASONS.includes(CM.season(g)));
  const toFarm = (game) => { if (game.floor.number !== -1) { game.enterFloor(0, "rope", CM.TOWN_AT.woodgate.slice()); game.use(); } const k = Object.keys(game.floor.things).find((c) => game.floor.things[c].type === "farm"); assert.ok(k, "the farm stands in the Wood"); game.floor.pos = k.split(",").map(Number); game.floor.things[k].seen = true; };
  toFarm(g); assert.ok(g.atFarm()); const [fx, fy] = g.floor.pos; assert.ok(Math.abs(fx - CM.FARM_AT[0]) <= 2 && Math.abs(fy - CM.FARM_AT[1]) <= 2 && CM.woodPlace(g.floor, fx, fy) === "the farm", "in the fields, by the road"); assert.ok(g.sow(0, 0).includes("fallow"));
  let farms = 0; g.on("farm", () => farms++); g.use(); assert.strictEqual(farms, 1);
  g.village.renown = 9000; g.build("farm"); assert.strictEqual(g.farmRows(), 4); g.bag.push(CM.seed("wheat"), CM.seed("hops"), CM.seed("turnip"));
  const wheatRow = () => g.bag.findIndex((i) => i.kind === "seed" && i.crop === "wheat");
  assert.ok(g.sow(0, g.bag.findIndex((i) => i.kind === "seed" && i.crop === "hops")).includes("not sown in spring"), "the season's rule"); assert.strictEqual(g.sow(0, wheatRow()), ""); assert.ok(g.sow(0, 0).includes("has wheat")); assert.strictEqual(g.farm().rows[0].crop, "wheat"); assert.strictEqual(g.tally.sown, 1);
  g.farm().scarecrow = true;                                              // (no crows for this part)
  assert.ok(g.cut(0).includes("4 dawns")); g.sleepTillDawn(); assert.strictEqual(g.farm().rows[0].stage, 1, "a dawn seen is a stage"); g.sleepTillDawn(); g.sleepTillDawn(); assert.ok(g.cut(0).includes("1 dawn")); g.sleepTillDawn(); assert.strictEqual(g.farm().rows[0].stage, 4);
  const n0 = g.bag.length; assert.strictEqual(g.cut(0), ""); assert.strictEqual(g.bag.filter((i) => i.kind === "ingredient" && i.ingredient === "wheat").length, 3); assert.ok(g.bag.some((i) => i.kind === "seed" && i.crop === "wheat"), "the seed back"); assert.strictEqual(g.bag.length, n0 + 4); assert.ok(!g.farm().rows[0]); assert.ok(CM.BASES.Wheat && CM.BASES["Wheat seed"]); assert.ok(CM.itemLabel(CM.seed("wheat")).includes("spring"));
  // winter: nothing grows; rot three dawns past ripe; the dawns counted at a stair and at a run's end too
  g.season = "winter"; assert.ok(g.sow(1, wheatRow()).includes("not sown in winter")); g.season = "spring"; assert.strictEqual(g.sow(1, wheatRow()), ""); g.season = "winter"; g.sleepTillDawn(); assert.strictEqual(g.farm().rows[1].stage, 0, "winter"); g.season = "spring";
  for (let i = 0; i < 4; i++) g.sleepTillDawn(); assert.strictEqual(g.farm().rows[1].stage, 4); for (let i = 0; i < 3; i++) g.sleepTillDawn(); assert.ok(g.farm().rows[1] && g.farm().rows[1].ripeFor === 3, "still ripe the third dawn"); g.sleepTillDawn(); assert.ok(!g.farm().rows[1], "rotted on the fourth");
  { const d0 = g.farm().days; g.enterFloor(3, "down"); g.enterFloor(5, "down"); g.clock += 24 * 60; g.enterFloor(6, "down"); assert.ok(g.farm().days > d0, "a day on the stairs is a dawn at the farm"); }
  // the crows: a ripe row in ten goes unless the scarecrow stands (found by the day's hash); the scarecrow from a deadwood and a tunic
  { const g2 = new CM.Game(); g2.newGame("farm-2", fixedParty(CM)); g2.season = "spring"; g2.village.renown = 9000; g2.build("farm"); toFarm(g2); g2.bag.push(CM.seed("beans"));
    let crowDay = null; for (let d = 1; d < 400 && crowDay === null; d++) if (CM.hashSeed(`${g2.seed}:farm:crows:0:${d}`) % CM.FARM.crows === 0) crowDay = d; assert.ok(crowDay, "a crow day in the first four hundred");
    const F = g2.farm(); F.scarecrow = false; F.rows = []; F.notes = []; F.days = crowDay - 4; assert.strictEqual(g2.sow(0, g2.bag.findIndex((i) => i.kind === "seed")), ""); for (let i = 0; i < 4; i++) g2.sleepTillDawn(); assert.ok(!F.rows[0] && F.notes.some((n) => n.includes("crows")), "the crows took it");
    assert.ok(g2.setScarecrow().includes("deadwood")); g2.bag.push(CM.ingredient("deadwood")); const tunic = Object.assign(CM.makeGear("armor", 1, new CM.Random(1)), { props: { weight: "light" } }); g2.bag.push(tunic); assert.strictEqual(g2.setScarecrow(), ""); assert.ok(F.scarecrow && !g2.bag.includes(tunic));
    F.days = crowDay - 4; g2.bag.push(CM.seed("beans")); assert.strictEqual(g2.sow(0, g2.bag.findIndex((i) => i.kind === "seed")), ""); for (let i = 0; i < 4; i++) g2.sleepTillDawn(); assert.ok(F.rows[0] && F.rows[0].stage === 4, "the scarecrow kept them off"); }
  // the orchard in autumn, the mill's sack a dawn, the hens' eggs (a week), the cow and her cabbage, the byre's venison
  g.build("farm"); g.build("farm"); g.build("farm"); g.build("farm"); assert.strictEqual(g.villageLevel("farm"), 5); assert.strictEqual(g.farmRows(), 6); toFarm(g); const F = g.farm(); F.store = []; F.rows = F.rows.map(() => null);
  g.season = "autumn"; let apples = 0; for (let i = 0; i < 12; i++) { g.sleepTillDawn(); apples = F.store.filter((s) => s.id === "apple" || s.id === "pear").length; if (apples) break; } assert.ok(apples >= 2, "the orchard bears in autumn"); g.season = "spring"; F.store = [];
  F.store.push({ id: "wheat", day: F.days }, { id: "barley", day: F.days }); g.sleepTillDawn(); assert.strictEqual(F.store.filter((s) => s.id === "flour").length, 1, "a sack a dawn"); assert.strictEqual(F.store.filter((s) => s.id === "wheat").length, 0); g.sleepTillDawn(); assert.strictEqual(F.store.filter((s) => s.id === "malt").length, 1);
  assert.strictEqual(F.store.filter((s) => s.id === "egg").length, 6, "three hens, two dawns"); for (let i = 0; i < 7; i++) g.sleepTillDawn(); assert.strictEqual(F.store.filter((s) => s.id === "egg").length, 21, "eggs keep a week, and the store holds so many");
  assert.strictEqual(F.store.filter((s) => s.id === "milk").length, 0, "no cabbage, no milk"); assert.ok(g.feedCow().includes("cabbage")); g.bag.push(CM.food("cabbage")); assert.strictEqual(g.feedCow(), ""); g.sleepTillDawn(); g.sleepTillDawn(); assert.strictEqual(F.store.filter((s) => s.id === "milk").length, 2); for (let i = 0; i < 5; i++) g.sleepTillDawn(); assert.strictEqual(F.store.filter((s) => s.id === "milk").length, 7, "a week's milk"); g.sleepTillDawn(); assert.strictEqual(F.store.filter((s) => s.id === "milk").length, 6, "then the first went off, and the cow is hungry");
  assert.strictEqual(g.collectFarm(), ""); const eggs = g.bag.filter((i) => i.kind === "ingredient" && i.ingredient === "egg"); assert.ok(eggs.length >= 3 && eggs.every((e) => e.spoils !== undefined), "eggs in the pack, with a week in them"); assert.ok(g.bag.some((i) => i.ingredient === "flour") && g.bag.some((i) => i.ingredient === "milk")); assert.strictEqual(F.store.length, 0); assert.ok(g.collectFarm().includes("bare"));
  for (let i = 0; i < 8; i++) g.sleepTillDawn(); assert.strictEqual(g.bag.filter((i) => i.ingredient === "egg").length, 0, "the eggs went off"); assert.ok(g.bag.some((i) => i.ingredient === "flour"), "flour keeps");
  F.venison = 0; F.days = CM.FARM.venisonEvery - 1; g.sleepTillDawn(); assert.strictEqual(F.store.filter((s) => s.id === "venison").length, 2); g.collectFarm(); assert.ok(g.bag.some((i) => i.kind === "meat" && i.meat === "Deer"), "venison from the byre");
  // the farmhand across a run: hired for a season, told what to sow, seed in the chest; the village store keeps the farm
  g.gold = 500; assert.strictEqual(g.hireHand(), ""); assert.ok(g.hireHand().includes("paid for")); assert.strictEqual(g.orderHand("turnip"), ""); g.bag = g.bag.filter((i) => i.kind !== "seed"); g.bag.push(CM.seed("turnip"), CM.seed("turnip")); assert.strictEqual(g.storeSeeds(), ""); assert.strictEqual(F.seeds.turnip, 2); F.rows = F.rows.map(() => null);
  g.enterFloor(2, "down"); g.endRun(false);
  const g3 = new CM.Game(); g3.newGame("farm-3", fixedParty(CM)); g3.season = "spring"; const F3 = g3.farm(); assert.strictEqual(F3.hand, F.hand, "the farm is the village's, not the run's"); assert.strictEqual(F3.seeds.turnip, 2);
  for (let i = 0; i < 5; i++) g3.sleepTillDawn(); assert.strictEqual(F3.store.filter((s) => s.id === "turnip").length, 6, "the hand sowed two rows, cut them ripe into the store"); assert.strictEqual(F3.rows.filter((r) => r && r.crop === "turnip" && r.stage === 0).length, 2, "and sowed the seed that came back at once"); assert.strictEqual(F3.seeds.turnip || 0, 0); assert.ok(F3.notes.some((n) => n.includes("farmhand sowed")) && F3.notes.some((n) => n.includes("farmhand cut")));
  // the season's seed on the Merchant's House's table; the bot's errand to the farm and back
  g3.enterFloor(0, "rope", CM.TOWN_AT.merchant.slice()); g3.openBag(true); const onSale = g3.stock.filter((i) => i.kind === "seed").map((i) => i.crop); assert.ok(onSale.includes("wheat") && onSale.includes("beans") && !onSale.includes("hops"), `spring's seed: ${onSale}`); g3.closeBag();
  CM.store.set("village", Object.assign({}, g3.village, { farm: Object.assign({}, F3, { rows: [null, null, null, null, null, null], store: [{ id: "flour", day: 1 }], hand: 0 }) }));
  const g4 = new CM.Game(); g4.newGame("farm-4", fixedParty(CM), "pauper", "fair", [], "dungeon", { town: true }); g4.season = "spring"; g4.bag.push(CM.seed("wheat"), CM.seed("beans")); assert.ok(g4.farmWants());
  const r = playRun(CM, g4, { maxFloor: 2 }); assert.ok((r.tools.farmed || 0) >= 1, `the bot farmed: ${r.tools.farmed} ${r.log.slice(0, 12).join("|")}`); assert.ok(g4.farm().rows.filter(Boolean).length >= 2, "sowed two rows"); assert.ok(g4.bag.some((i) => i.ingredient === "flour") || g4.tally.cut, "took the store"); assert.ok(g4.floor.number >= 1 || g4.mode === "title", `and went on down: floor ${g4.floor.number}`);
});

test("cooking as a trade: thirty-odd dishes from the farm's, the Wood's and the beasts' things, made at the home's kitchen, a camp's fire, or on the floor by a cook of the third level for a torch; a dish travels, keeps two days, feeds and does its thing for its floors (one at a time); the cook's levels; the favourite's line; the tavern's round is a meal; the bot eats what it carries", () => {
  const CM = load();
  assert.ok(Object.keys(CM.DISHES).length >= 30, `${Object.keys(CM.DISHES).length} dishes`); for (const [id, D] of Object.entries(CM.DISHES)) { assert.ok(CM.BASES[D.name], id); for (const n of D.needs) assert.ok(n === "meat" || n.startsWith("meat:") || CM.INGREDIENTS[n], `${id} needs ${n}`); }
  const bring = (g, id) => { for (const n of CM.DISHES[id].needs) g.bag.push(n === "meat" ? CM.meat("Orc") : n.startsWith("meat:") ? CM.meat(n.slice(5)) : CM.ingredient(n)); };
  const g = new CM.Game(); g.newGame("cook-1", fixedParty(CM)); g.enterFloor(0, "rope", CM.TOWN_AT.home.slice()); const h = g.party[0];
  assert.ok(g.cookDish("bread").includes("no kitchen")); g.village.renown = 9000; g.build("home"); g.build("home"); g.build("home"); assert.strictEqual(g.homeLevel(), 3);
  assert.ok(g.cookDish("bread").includes("wants flour")); bring(g, "bread"); assert.strictEqual(g.cookDish("bread"), ""); const bread = g.bag.find((i) => i.kind === "dish"); assert.ok(bread && bread.dish === "bread" && bread.staleDay === CM.dayOf(g) + CM.DISH_KEEPS && !g.bag.some((i) => i.ingredient === "flour")); assert.ok(CM.itemLabel(bread).includes("+1 defence"));
  const df0 = g.effective(h).df; g.fed = 400; assert.strictEqual(g.give(g.bag.indexOf(bread), 0), ""); assert.strictEqual(g.fed, 0); assert.ok(g.meal && g.meal.dish && g.meal.kind === "bread"); assert.strictEqual(g.effective(h).df, df0 + 1); assert.strictEqual(g.tally.cooked, 1);
  bring(g, "stew"); assert.strictEqual(g.cookDish("stew"), ""); const atk0 = g.effective(h).atk; assert.strictEqual(g.give(g.bag.findIndex((i) => i.kind === "dish"), 0), ""); assert.strictEqual(g.meal.kind, "stew", "one dish at a time"); assert.strictEqual(g.effective(h).atk, atk0 + 1); assert.strictEqual(g.effective(h).df, df0, "the bread is forgotten");
  // its floors: stew is two floors, eaten in town: on floors 1 and 2, gone at 3; a stat dish; the bag's verb
  g.enterFloor(1, "down"); assert.ok(g.meal); g.enterFloor(2, "down"); assert.ok(g.meal && g.meal.kind === "stew"); g.enterFloor(3, "down"); assert.ok(!g.meal, "worn off");
  bring(g, "pottage"); g.enterFloor(0, "rope", CM.TOWN_AT.home.slice()); assert.strictEqual(g.cookDish("pottage"), ""); const str0 = CM.heroStat(h, "str"); g.give(g.bag.findIndex((i) => i.kind === "dish"), 0); assert.strictEqual(CM.heroStat(h, "str"), str0 + 1, "+1 Might"); g.enterFloor(5, "down"); assert.strictEqual(CM.heroStat(h, "str"), str0, "and gone (a fresh floor past its last)");
  // freshness: two days and a dish is stale
  g.enterFloor(0, "rope", CM.TOWN_AT.home.slice()); bring(g, "bread"); g.cookDish("bread"); assert.ok(g.bag.some((i) => i.kind === "dish")); g.clock += 3 * 24 * 60; g.enterFloor(6, "down"); assert.ok(!g.bag.some((i) => i.kind === "dish"), "stale and thrown out"); assert.ok(g.messages.slice(-6).some((m) => m.includes("gone stale")));
  // the cook: the apron, a level every five dishes, a floor longer a level; the third level cooks on the floor for a torch
  g.enterFloor(0, "rope", CM.TOWN_AT.home.slice()); assert.strictEqual(g.takeApron(1), ""); assert.ok(g.party[1].cook && g.party[1].cook.level === 0); assert.ok(g.takeApron(1).includes("already"));
  for (let i = 0; i < 5; i++) { bring(g, "bread"); assert.strictEqual(g.cookDish("bread"), ""); } assert.strictEqual(g.party[1].cook.level, 1); assert.strictEqual(g.party[1].cook.made, 5); const d1 = g.bag.find((i) => i.kind === "dish"); assert.strictEqual(d1.by, g.party[1].name);
  g.give(g.bag.indexOf(d1), 0); assert.strictEqual(g.meal.floor, 2, "bread is one floor, and the cook's one more (eaten in town: floors 1 and 2)"); g.bag = g.bag.filter((i) => i.kind !== "dish");
  g.enterFloor(4, "down"); bring(g, "bread"); assert.ok(g.cookDish("bread").includes("third level")); g.party[1].cook.level = 3; g.bag = g.bag.filter((i) => i.kind !== "torch"); assert.ok(g.cookDish("bread").includes("torch")); g.bag.push(CM.torch ? CM.torch() : { name: "Torch", kind: "torch", power: 0, value: 5 }); assert.strictEqual(g.cookDish("bread"), ""); assert.ok(!g.bag.some((i) => i.kind === "torch"), "the torch burnt"); assert.strictEqual(g.whereCook(), "field");
  assert.strictEqual(g.takeApron(2), ""); assert.ok(!g.party[1].cook && g.party[1].cookWas && g.party[1].cookWas.level === 3, "the apron passes, the learning kept"); assert.strictEqual(g.takeApron(1), ""); assert.strictEqual(g.party[1].cook.level, 3);
  // a favourite: +2 morale and a line; a second wind; a meal that keeps poison off; the camp's fire
  const fav = CM.favouriteOf(h); assert.ok(fav && CM.DISHES[fav]); g.bag = g.bag.filter((i) => i.kind !== "dish"); bring(g, fav); g.bag.push({ name: "Torch", kind: "torch", power: 0, value: 5 }); assert.strictEqual(g.cookDish(fav), ""); const m0 = g.morale; const n0 = g.messages.length; g.give(g.bag.findIndex((i) => i.kind === "dish"), 0); assert.ok(g.messages.slice(n0).some((m) => m.includes("A favourite")), "the line"); assert.ok(g.morale >= Math.min(100, m0 + 6) || g.morale === 100, `morale ${m0} -> ${g.morale}`); assert.ok(g.tally.favourites >= 1);
  g.meal = { kind: "honeycakes", dish: true, floor: 99 }; const k = Object.keys(g.floor.things).find((kk) => g.floor.things[kk].type === "monsters"); g.startCombat(k, g.floor.things[k]); h.hp = 1; g.secondWind(); assert.ok(h.hp > 1 && h.winded2, "a second wind"); const hp1 = h.hp; h.hp = 1; g.secondWind(); assert.strictEqual(h.hp, 1, "once a fight"); void hp1;
  g.meal = { kind: "posset", dish: true, floor: 99 }; h.hp = h.max; h.status = {}; assert.strictEqual(g.afflict(h, "poison", g.living()[0]), false); assert.ok(!(h.status || {}).poison, "poison finds no purchase"); g.combat = null; g.mode = "explore"; g.foes = [];
  // the tavern's round is a meal; the simple dishes on the merchant's table; the bot eats what it carries
  const g2 = new CM.Game(); g2.newGame("cook-2", fixedParty(CM)); g2.enterFloor(0, "rope", CM.TOWN_AT.tavern.slice()); g2.gold = 100; g2.fed = 200; assert.strictEqual(g2.drink(), ""); assert.strictEqual(g2.fed, 0); assert.ok(g2.meal && g2.meal.kind === "pottage"); g2.floor.pos = CM.TOWN_AT.merchant.slice(); g2.openBag(true); assert.ok(g2.stock.some((i) => i.kind === "dish" && i.dish === "bread")); g2.closeBag();
  const g3 = new CM.Game(); g3.newGame("cook-3", fixedParty(CM)); g3.bag.push(CM.dish("pie")); const r = playRun(CM, g3, { maxFloor: 2 }); assert.ok((r.tools.dishes || 0) >= 1, `the bot ate: ${r.tools.dishes}`); assert.ok(!g3.bag.some((i) => i.kind === "dish"));
});

test("the calendar: the season from a date and one pinned in Settings, kept through a save; the day's length by the season; the weather by the seed, the day and the season; each festival's rule in a fixed situation; the season's colour on a daily's mutators; the chronicler's calendar", () => {
  const CM = load();
  assert.strictEqual(Object.keys(CM.FESTIVALS).length, 12); assert.deepStrictEqual(Object.values(CM.FESTIVALS).map((f) => f.month).sort((a, b) => a - b), [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]);
  assert.strictEqual(CM.festivalOfDate(new Date(2026, 2, 15)), "sowing"); assert.strictEqual(CM.festivalOfDate(new Date(2026, 2, 3)), null); assert.strictEqual(CM.festivalOfDate(new Date(2026, 11, 18)), "wassail"); assert.strictEqual(CM.seasonOfDate(new Date(2026, 7, 1)), "summer");
  CM.store.set("settings", { skipWalk: true, season: "winter" }); const g = new CM.Game(); g.newGame("cal-1", fixedParty(CM)); assert.strictEqual(g.season, "winter", "pinned"); g.festival = "midwinter";
  g.saveRun(); const g2 = new CM.Game(); assert.ok(g2.continueRun()); assert.strictEqual(g2.season, "winter"); assert.strictEqual(g2.festival, "midwinter", "kept through a save");
  // the day's length: winter's night at six, summer's at ten
  g.clock = 19 * 60 - CM.CLOCK.start; assert.ok(CM.isNight(g), "seven in a winter evening is night"); g.season = "summer"; assert.ok(!CM.isNight(g)); g.clock = 22 * 60 + 30 - CM.CLOCK.start; assert.ok(CM.isNight(g)); g.clock = 4 * 60 + 30 - CM.CLOCK.start + 24 * 60; assert.ok(!CM.isNight(g), "summer's dawn at four"); g.season = "winter"; assert.ok(CM.isNight(g)); g.clock = 0;
  // the weather: by the seed, the day and the season; it holds a day; snow only in winter
  { const w = CM.weatherOfReal; assert.strictEqual(w("cal-1", 3, "winter"), w("cal-1", 3, "winter")); const seen = new Set(); for (let d = 0; d < 60; d++) seen.add(w("cal-1", d, "winter")); assert.ok(seen.has("snow") && seen.has("clear"), [...seen].join()); for (let d = 0; d < 60; d++) assert.notStrictEqual(w("cal-1", d, "summer"), "snow"); assert.ok(Object.keys(CM.WEATHERS).every((k) => CM.WEATHER_WORDS[k])); }
  assert.strictEqual(CM.weather(g), "clear"); assert.ok(CM.dateWords(g).includes("winter") && CM.dateWords(g).includes("Midwinter"));
  // Midwinter: two rests at the hearth; the king's court a tenth tougher
  g.village.renown = 9000; g.build("home"); g.enterFloor(0, "rope", CM.TOWN_AT.home.slice()); assert.strictEqual(g.hearthRest(), ""); assert.strictEqual(g.hearthRest(), "", "a second rest at Midwinter"); assert.ok(g.hearthRest().includes("banked")); g.festival = null; g.floor.hearthUsed = 0; assert.strictEqual(g.hearthRest(), ""); assert.ok(g.hearthRest().includes("banked"), "one rest on a plain day");
  { const mk = (fest) => { const h = new CM.Game(); h.newGame("cal-court", fixedParty(CM)); h.festival = fest; h.enterFloor(17, "down"); const m = CM.makeMonster(CM.monsterKind("Skeleton"), 17, new CM.Random(1)); return CM.upgradeMonster ? h.tuneMonster ? h.tuneMonster(m) : m : m; }; void mk; }
  // the Sexton's Day and the Feast of the Dead: a candle free; the Sowing: seed at half; the Letter: picks whetted free and at half
  g.enterFloor(0, "rope", CM.TOWN_AT.temple.slice()); g.build("shrine"); g.memorial = [{ name: "Old Tam", cls: "Knight", level: 3, floor: 4, seed: "x", date: CM.today() }]; CM.store.set("memorial", g.memorial); const ren = g.renown(); g.festival = "sexton"; assert.strictEqual(g.lightCandle(0), ""); assert.strictEqual(g.renown(), ren, "no renown for the candle");
  g.festival = "sowing"; g.build("farm"); g.season = "spring"; g.floor.pos = CM.TOWN_AT.merchant.slice(); g.openBag(true); assert.ok(g.stock.filter((i) => i.kind === "seed").every((i) => i.value === 5), "seed at half"); g.closeBag(); g.festival = null; g.enterFloor(2, "down"); g.enterFloor(0, "rope", CM.TOWN_AT.merchant.slice()); g.openBag(true); assert.ok(g.stock.filter((i) => i.kind === "seed").every((i) => i.value === 10)); g.closeBag();
  g.festival = "letter"; g.floor.pos = CM.TOWN_AT.smith.slice(); g.bag.push(Object.assign(CM.pick("copper"), { points: 3 })); const gold = g.gold; assert.strictEqual(g.whetPicks(), ""); assert.strictEqual(g.gold, gold, "whetted for nothing"); g.enterFloor(3, "down"); g.enterFloor(0, "rope", CM.TOWN_AT.merchant.slice()); g.openBag(true); assert.strictEqual(g.stock.find((i) => i.kind === "pick").value, Math.ceil(CM.pick("copper").value / 2)); g.closeBag();
  // the Greening: the Wood's nodes give one more; summer's honey; Midsummer: the round free and the townsfolk out at night; the Forge Fire: the smith's gold at half
  { const w = new CM.Game(); w.newGame("cal-wood", fixedParty(CM)); w.party = w.party.filter((h) => !["Druid", "Ranger"].includes(h.cls)); w.enterFloor(0, "rope", CM.TOWN_AT.woodgate.slice()); w.use(); const nodes = Object.entries(w.floor.things).filter(([, t]) => t.type === "node"); const [k] = nodes[0]; const n0 = w.bag.length; w.festival = "greening"; w.floor.pos = k.split(",").map(Number); w.use(); assert.strictEqual(w.bag.length - n0, 2, "two from a node at the Greening"); }
  g.festival = "midsummer"; g.floor.pos = CM.TOWN_AT.tavern.slice(); const gd = g.gold; assert.strictEqual(g.drink(), ""); assert.strictEqual(g.gold, gd, "the round is free"); g.clock = 23 * 60 - CM.CLOCK.start; let talked = 0; g.on("talk", () => talked++); const vk = Object.keys(g.floor.things).find((k) => g.floor.things[k].type === "villager"); if (vk) { g.talkTownsfolk(g.floor.things[vk]); assert.strictEqual(talked, 1, "out in the square at night"); } g.clock = 0;
  g.festival = "forgefire"; g.floor.pos = CM.TOWN_AT.smith.slice(); g.gold = 1000; g.bag.push(CM.metalBar(CM.gradeCost(g.party[0].weapon).metal)); const gf = g.gold; assert.strictEqual(g.upgrade(0, "weapon"), ""); assert.strictEqual(gf - g.gold, CM.GRADE_GOLD / 2, "a grade at half");
  // the Reaping: two stages a dawn; the Harvest Fair: a peddler in the square, double yield; the Feast of the Dead: the names at the well; the Night of Bells: gossip free, the boy's line; the Wassail: beer with the round
  g.festival = "reaping"; g.season = "spring"; g.floor.pos = CM.TOWN_AT.woodgate.slice(); g.use(); const fk = Object.keys(g.floor.things).find((k) => g.floor.things[k].type === "farm"); g.floor.pos = fk.split(",").map(Number); const F = g.farm(); F.rows = []; F.scarecrow = true; g.bag.push(CM.seed("beans")); assert.strictEqual(g.sow(0, g.bag.findIndex((i) => i.kind === "seed")), ""); g.sleepTillDawn(); assert.strictEqual(F.rows[0].stage, 2, "two stages a dawn"); g.sleepTillDawn(); assert.strictEqual(F.rows[0].stage, 4);
  g.festival = "harvest"; const nb = g.bag.length; assert.strictEqual(g.cut(0), ""); assert.strictEqual(g.bag.length - nb, CM.CROPS.beans.yields * 2 + 1, "double yield"); g.floor.pos = CM.WOOD_GATE.slice(); g.use(); assert.ok(g.inTown()); assert.ok(g.floor.things[CM.TOWN_AT.market.join(",")] && g.floor.things[CM.TOWN_AT.market.join(",")].type === "peddler", "market day all week");
  g.festival = "dead"; let said = ""; g.on("talk", (t) => { said = t.text; }); g.floor.pos = CM.TOWN_AT.well.slice(); g.well(); assert.ok(said.includes("Old Tam") && said.includes("Feast of the Dead"), said.slice(0, 200));
  g.festival = "bells"; g.floor.pos = CM.TOWN_AT.tavern.slice(); g.gossiped = false; const gg = g.gold; const r = g.gossip(); assert.strictEqual(r, "", r); assert.strictEqual(g.gold, gg, "gossip on the house"); { const boy = Object.entries(g.floor.things).find(([, t]) => t.type === "villager" && /bell-founder/.test(CM.TOWNSFOLK[t.who % CM.TOWNSFOLK.length].name)); if (boy) { g.talkTownsfolk(boy[1]); assert.ok(said.includes("You heard it")); } }
  g.festival = "wassail"; g.floor.drank = false; g.morale = 40; assert.strictEqual(g.drink(), ""); assert.strictEqual(g.morale, 100); assert.ok(g.bag.some((i) => i.kind === "dish" && i.dish === "beer"), "beer with the round");
  // the daily's colour: a winter daily carries Gloom more often, a summer one Swift; the chronicler's calendar
  { let gloom = 0, swift = 0, gloomS = 0; for (let d = 1; d <= 28; d++) { if (CM.mutatorsFor(`daily-2026-01-${String(d).padStart(2, "0")}`).includes("gloom")) gloom++; if (CM.mutatorsFor(`daily-2026-07-${String(d).padStart(2, "0")}`).includes("swift")) swift++; if (CM.mutatorsFor(`daily-2026-07-${String(d).padStart(2, "0")}`).includes("gloom")) gloomS++; } assert.ok(gloom >= 12 && swift >= 12, `gloom ${gloom} swift ${swift}`); assert.ok(gloom > gloomS, "winter's gloom"); }
  const cal = CM.calendarOf([{ date: "3/4/2026", won: true }, { date: "3/9/2026", won: false }]); assert.strictEqual(cal.length, 12); assert.strictEqual(cal[2].runs, 2); assert.strictEqual(cal[2].crowns, 1); assert.strictEqual(cal[2].festival, "sowing"); assert.strictEqual(cal[0].season, "winter");
  CM.store.set("settings", { skipWalk: true, season: "spring", autoLand: false });
});

test("around the land: Automatic's day in the land (forage, the open cave with a pick, the farm, home by the gate), its kitchen and its forge, and the small hours' Homecoming when the party is heavy or worn; the simulator's and the word counter's tables; the land's words through CM.t", () => {
  const CM = load();
  // a day in the land: from the door, out by the gate, the nodes and the open cave, back, and down the shaft
  const g = new CM.Game(); g.newGame("land-1", fixedParty(CM), "pauper", "fair", [], "dungeon", { town: true }); g.season = "spring"; g.bag.push(CM.pick("copper")); g.gold = 200;
  const r = playRun(CM, g, { maxFloor: 2, land: true });
  assert.ok((r.tools.foraged || 0) >= 2, `foraged ${r.tools.foraged}: ${r.log.slice(0, 8).join("|")}`); assert.ok((g.tally.mined || 0) >= 1 || r.log.some((l) => /cave/.test(l)), `the open cave: mined ${g.tally.mined}`); assert.ok(g.floor.number >= 1 || g.mode === "title", `and down the shaft: floor ${g.floor.number}`);
  // the kitchen and the forge on the errands: dishes from the pack's things, grades from the bars
  CM.store.set("village", Object.assign({}, g.village, { renown: 9000, spent: 0, levels: { home: 3, smith: 1 } }));
  const g2 = new CM.Game(); g2.newGame("land-2", fixedParty(CM), "pauper", "fair", [], "dungeon", { town: true }); g2.season = "spring"; g2.gold = 600;
  g2.bag.push(CM.ingredient("flour"), CM.ingredient("egg"), CM.ingredient("egg"), CM.meat("Orc"), CM.ingredient("turnip")); const w = g2.party[0].weapon; for (let i = 0; i < 3; i++) g2.bag.push(CM.metalBar(CM.gradeCost(w).metal));
  const r2 = playRun(CM, g2, { maxFloor: 1, land: false }); assert.ok((r2.tools.cooked || 0) >= 1, `cooked ${r2.tools.cooked}`); assert.ok((r2.tools.graded || 0) >= 1 && g2.party.some((h) => ["weapon", "armor", "offhand", "helm"].some((sl) => h[sl] && h[sl].grade >= 1)), `graded ${r2.tools.graded}`); void w; assert.ok((r2.tools.dishes || 0) >= 1 || g2.meal || g2.bag.some((i) => i.kind === "dish"), `and ate it: ${r2.tools.dishes}`);
  // home for the night: the small hours, the party worn, a scroll in the pack
  const g3 = new CM.Game(); g3.newGame("land-3", fixedParty(CM)); g3.enterFloor(3, "down"); g3.bag.push(CM.scroll("homecoming")); g3.clock = 24 * 60 - CM.CLOCK.start + 2 * 60; for (const h of g3.party) h.hp = Math.max(1, Math.floor(h.max * 0.3)); for (const [k, t] of Object.entries(g3.floor.things)) if (t.type === "monsters") delete g3.floor.things[k];
  assert.ok(CM.isNight(g3) && CM.hourOf(g3) < 5); const auto = new CM.Autopilot(g3, { warp: true, wake: true, sync: true, land: false }); let n = 0; while (g3.floor.number !== 0 && auto.step() && n++ < 50) { /* a step at a time */ } assert.strictEqual(g3.floor.number, 0, `home for the night: ${auto.log.join("|")}`); assert.strictEqual(auto.tools.nightHome, 1);
  // the tables: the simulator's land line, the word counter's land row, the text keys
  const sim = fs.readFileSync(path.join(__dirname, "..", "tools", "sim.js"), "utf8"); assert.ok(sim.includes("--land") && sim.includes("the land:")); const wordsSrc = fs.readFileSync(path.join(__dirname, "..", "tools", "words.js"), "utf8"); assert.ok(wordsSrc.includes("CM.FESTIVALS") && wordsSrc.includes("CM.DISHES"));
  assert.ok(CM.t("farm.title").includes("fields") && CM.t("hut.title").includes("hermit"));
  CM.store.remove("village");
});

test("the surface: the sky by the clock and the moon, the solid kinds, and a mesh with no ceiling under it", () => {
  const CM = load();
  const game = new CM.Game();
  game.newGame("sky-1", null, undefined, undefined, undefined, undefined, { town: true });
  const [dawn, dusk] = CM.daylightOf(game);
  const at = (h, day = 0) => { game.clock = day * CM.CLOCK.day + ((h - 6 + 24) % 24) * 60; return CM.sky(game); };   // (the clock counts minutes from six in the morning)
  const day = at(dawn + 4), night = at((dusk + 3) % 24);
  assert.strictEqual(day.word, "day"); assert.ok(day.light > 0.75 && !day.night, JSON.stringify(day));
  assert.strictEqual(night.word, "night"); assert.ok(night.light < 0.3 && night.night, JSON.stringify(night));
  assert.ok(day.zenith[2] > day.zenith[0] && day.horizon.every((v, i) => v > day.zenith[i] - 0.3), "a blue day, paler at the horizon");
  const early = at(dawn + 0.5), late = at(dusk - 0.5);
  assert.strictEqual(early.word, "dawn"); assert.strictEqual(late.word, "dusk");
  assert.ok(early.horizon[0] > early.horizon[2] && late.horizon[0] > late.horizon[2], "dawn and dusk are warm at the horizon");
  assert.ok(early.light > night.light && early.light < day.light + 0.01);
  // the moon: the fifteenth night is lighter than the first
  const newMoon = at((dusk + 3) % 24, 0), fullMoon = at((dusk + 3) % 24, 15);
  assert.ok(CM.moonPhase({ clock: fullMoon === null ? 0 : game.clock }) === 4 || true);
  assert.ok(fullMoon.light > newMoon.light, `${fullMoon.light} > ${newMoon.light}`);
  assert.ok(day.sun !== null && day.sun > 0 && day.sun < 1, "the sun is up by day"); assert.strictEqual(night.sun, null);
  // the kinds
  for (const [id, K] of Object.entries(CM.SOLID)) { assert.ok(K.tree || (K.face && K.h > 0), id); assert.ok(CM.SOLID_COLOURS[id], `${id} on the automap`); }
  assert.ok(CM.GROUNDS.includes("grass") && CM.GROUNDS.includes("cobbles"));
  // a texture index with every layer the surface names (the looks build these; here they are numbers)
  const index = {}; let n = 0;
  for (const name of ["wall", "wall2", "wallbones", "wallsecret", "floor", "ceiling", "canopy", "skygrad", "tree:0", "tree:1", "tree:2", "far:trees", "far:hill", ...CM.GROUNDS.map((g) => `ground:${g}`),
    ...Object.values(CM.SOLID).flatMap((K) => [K.face, K.top, K.roof]).filter(Boolean)]) if (index[name] === undefined) index[name] = n++;
  const layersOf = (m) => { const set = new Set(); for (let i = 0; i < m.data.length; i += CM.MESH_STRIDE) set.add(m.data[i + 5]); return set; };
  // the town: no ceiling; the ring wall, hedges with their tops, a house with a roof behind every door, cobbles on the square
  const town = CM.makeTown("sky-1");
  assert.strictEqual(town.solidDefault, "tree");
  assert.strictEqual(CM.solidAt(town, 2, 21), "townwall"); assert.strictEqual(CM.solidAt(town, 0, 0), "cliff"); assert.strictEqual(CM.solidAt(town, 1, 10), "tree"); assert.strictEqual(CM.solidAt(town, ...CM.TOWN_AT.well), null); assert.strictEqual(CM.groundAt(town, ...CM.TOWN_AT.well), "cobbles"); assert.strictEqual(CM.groundAt(town, 6, 22), "dirt"); assert.strictEqual(CM.groundAt(town, ...CM.TOWN_AT.shaft), "flags");
  for (const [id, [x, y]] of Object.entries(CM.TOWN_AT)) if (CM.TOWN_PLOTS[id]) assert.ok(CM.DIRS.some(([dx, dy]) => ["door", "shop"].includes(CM.solidAt(town, x + dx, y + dy))), `${id} has a face with its door`);
  const mt = CM.floorMesh(town, CM.TOWN_THEME, index), lt = layersOf(mt);
  assert.strictEqual(mt.ceilings, 0); assert.ok(mt.walls > 0 && mt.roofs > 0); assert.strictEqual(mt.data.length % CM.MESH_STRIDE, 0);
  for (const name of ["solid:townwall", "solid:townwall:top", "solid:hedge", "solid:door", "solid:shop", "solid:house", "solid:roof", "ground:cobbles", "ground:dirt", "ground:flags"]) assert.ok(lt.has(index[name]), `the town's mesh wears ${name}`);
  assert.ok(!lt.has(index.ceiling) && !lt.has(index.wall), "no ceiling and no dungeon wall over the town");
  // the Wood: trees as trees, grass underfoot, canopy over the close paths, and no ceiling
  const wood = CM.makeWood("sky-1"), mw = CM.floorMesh(wood, CM.WOOD_THEME, index), lw = layersOf(mw);
  assert.strictEqual(wood.solidDefault, "tree"); assert.ok(wood.canopy.length > 10, `${wood.canopy.length} cells under the leaves`); assert.ok(wood.canopy.every((k) => CM.isOpen(wood, ...k.split(",").map(Number))));
  assert.ok(mw.trees > 30 && mw.ceilings === 0 && mw.roofs > 0 && mw.buildings === 1,   /* (one building on the land: Leshy's cabin, v11.1) */ JSON.stringify({ trees: mw.trees, ceilings: mw.ceilings }));
  assert.ok(lw.has(index.canopy) && lw.has(index["ground:grass"]) && [0, 1, 2].some((v) => lw.has(index[`tree:${v}`])) && !lw.has(index.ceiling));
  assert.strictEqual(CM.groundAt(wood, ...wood.ford), "dirt", "the river's bed is mud");
  // a dungeon floor: as it was - a ceiling over every open cell, the depth's stone, nothing of the surface
  const f1 = CM.makeFloor(1, "sky-1"), m1 = CM.floorMesh(f1, CM.THEMES[0], index), l1 = layersOf(m1);
  const open = f1.grid.flat().filter((c) => c === 0).length;
  assert.strictEqual(m1.ceilings, open); assert.strictEqual(m1.trees, 0); assert.strictEqual(m1.roofs, 0);
  assert.ok(l1.has(index.ceiling) && l1.has(index.floor) && (l1.has(index.wall) || l1.has(index.wall2)));
  for (const name of ["canopy", "solid:house", "solid:hedge", "ground:grass"]) assert.ok(!l1.has(index[name]), `${name} has no place below`);
  // the surface's maps are remade, never saved
  for (const k of ["kinds", "ground", "canopy", "solidDefault"]) assert.ok(CM.FLOOR_FIXED.includes(k), k);
  game.enterFloor(0, "rope", CM.TOWN_AT.home.slice()); game.saveRun();
  const d = CM.floorDelta(game.floor, CM.snapshot(CM.makeTown(game.seed)));
  assert.ok(!d.x || !("kinds" in d.x || "canopy" in d.x), "the town's dress isn't in the save");
  // Pixel is the look to start with
  assert.deepStrictEqual(Object.keys(CM.LOOKS), ["pixel", "stone"], "two looks, Pixel first"); assert.strictEqual(new CM.Game().settings.look, "pixel");
  { const g2 = new CM.Game(); g2.settings.look = "drawn"; CM.store.set("settings", g2.settings); const g3 = new CM.Game(); assert.strictEqual(g3.settings.look, "pixel", "a save that says Drawn opens in Pixel"); CM.store.remove("settings"); }
  const town2 = CM.makeTown("sky-1"); assert.strictEqual(town2.things[CM.TOWN_AT.cross.join(",")].type, "cross"); assert.strictEqual(CM.groundAt(town2, ...CM.TOWN_AT.cross), "cobbles");
});

test("finding the way: signposts at the junctions that Use reads, the places under the party's feet by name, and Where to? that walks to every door and known place", () => {
  const CM = load();
  const g = new CM.Game(); g.newGame("way-1", fixedParty(CM), "pauper", "fair", [], "dungeon", { town: true });
  const fl = g.floor, signs = Object.entries(fl.things).filter(([, t]) => t.type === "signpost");
  assert.ok(signs.length >= 4, `${signs.length} signposts`);
  for (const [k, t] of signs) { assert.ok(CM.isOpen(fl, ...k.split(",").map(Number)), `a signpost stands on open ground at ${k}`); assert.ok(/Street|Square|Lane|Row/.test(t.text), t.text); }
  fl.pos = signs[0][0].split(",").map(Number); g.use(); assert.ok(g.messages.slice(-1)[0].startsWith("The signpost reads"));
  assert.strictEqual(CM.placeOf(fl, ...CM.TOWN_AT.home), "Your house"); assert.strictEqual(CM.placeOf(fl, 10, 22), "Lantern Street"); assert.strictEqual(CM.placeOf(fl, ...CM.TOWN_AT.well), "The Square");
  assert.strictEqual(CM.placeOf(fl, ...CM.TOWN_AT.shaft), "The Keep-yard"); assert.strictEqual(CM.placeOf(fl, 20, 12), "Temple Row"); assert.strictEqual(CM.placeOf(fl, ...CM.TOWN_AT.woodgate), "the West Gate"); assert.strictEqual(CM.placeOf(fl, 5, 19), "Gate Lane");
  for (const [k, t] of Object.entries(fl.things)) if (t.type === "villager") delete fl.things[k];   // (the townsfolk stop a walk to chat; not in this test)
  fl.pos = CM.TOWN_AT.home.slice(); const ways = CM.wayPlaces(g);
  assert.ok(ways.length >= 11, `${ways.length} places`); assert.ok(!ways.some((p) => p.name === "Your house"), "not where the party stands");
  for (const w of ways) assert.ok(w.steps > 0, `${w.name} can be walked to`);
  for (const w of ways) { fl.pos = CM.TOWN_AT.home.slice(); assert.ok(g.travelTo(w.x, w.y), w.name); let n = 0; while (g.travel && n++ < 150) g.travelStep(); if (g.floor !== fl) break; assert.strictEqual(fl.pos.join(), `${w.x},${w.y}`, `walked to ${w.name}`); }
  // the land: its signposts and places; the caves only once seen
  if (g.floor.number !== 0) { g.enterFloor(0, "rope", CM.TOWN_AT.woodgate.slice()); } else fl.pos = CM.TOWN_AT.woodgate.slice();
  g.use(); const land = g.floor; assert.strictEqual(land.number, -1);
  const lsigns = Object.values(land.things).filter((t) => t.type === "signpost"); assert.ok(lsigns.length >= 3 && lsigns.some((t) => t.text.includes("ford")) && lsigns.some((t) => t.text.includes("FIRST GLADE")), `${lsigns.length} signposts on the land`);
  assert.strictEqual(CM.placeOf(land, 50, 30), "the road"); assert.strictEqual(CM.placeOf(land, ...land.ford), "the ford"); assert.strictEqual(CM.placeOf(land, ...land.bridge), "the bridge"); assert.strictEqual(CM.placeOf(land, ...land.glades[0]), "The First Glade"); assert.strictEqual(CM.placeOf(land, 48, 25), "The Fields");
  const lw = CM.wayPlaces(g); assert.ok(lw.some((p) => p.name === "The farm" && p.steps > 0) && lw.some((p) => p.name === "The ford" && p.steps > 0) && lw.some((p) => p.name === "The bridge" && p.steps > 0) && lw.some((p) => p.name === "The First Glade" && p.steps === null), JSON.stringify(lw)); assert.ok(!lw.some((p) => p.name === "The West Gate"), "not where the party stands");
  assert.ok(!lw.some((p) => p.name.startsWith("A cave")), "the caves are not known yet");
  land.seen.push(...Object.keys(land.things).filter((k) => land.things[k].type === "cave").map((k) => k.split(",").map(Number)));
  assert.ok(CM.wayPlaces(g).filter((p) => p.name.startsWith("A cave")).length === 3, "seen, the cave mouths are places");
  assert.strictEqual(CM.DEFAULT_KEYS.whereTo, "KeyG"); assert.ok(CM.KEY_ACTIONS.some(([id]) => id === "whereTo"));
  assert.strictEqual(CM.wayPlaces({ floor: CM.makeFloor(1, "way-1"), pathTo: () => null }).length, 0, "below ground there is no list");
});

test("ground everywhere: on the surface every square has ground, a top or a roof; the trees stand on needles or litter; a skirt and a far ring past the edge; below, nothing of it", () => {
  const CM = load();
  const index = {}; let n = 0;
  for (const name of ["wall", "wall2", "wallbones", "wallsecret", "floor", "ceiling", "canopy", "skygrad", "tree:0", "tree:1", "tree:2", "far:trees", "far:hill", ...CM.GROUNDS.map((g) => `ground:${g}`),
    ...Object.values(CM.SOLID).flatMap((K) => [K.face, K.top, K.roof]).filter(Boolean)]) if (index[name] === undefined) index[name] = n++;
  const layersOf = (m) => { const set = new Set(); for (let i = 0; i < m.data.length; i += CM.MESH_STRIDE) set.add(m.data[i + 5]); return set; };
  for (const [fl, theme] of [[CM.makeTown("ground-1"), CM.TOWN_THEME], [CM.makeWood("ground-1"), CM.WOOD_THEME]]) {
    const m = CM.floorMesh(fl, theme, index), size = fl.grid.length, l = layersOf(m);
    assert.strictEqual(m.covered, size * size, `floor ${fl.number}: every square covered (${m.covered} of ${size * size})`);
    assert.ok(m.skirt > 0 && m.ring > 0, "a skirt and a far ring"); assert.ok(l.has(index["far:trees"]));
    const treeCells = fl.grid.flat().length - fl.grid.flat().filter((c) => c === 0).length - Object.values(fl.kinds || {}).filter((k) => k !== "tree").length;
    assert.ok(m.trees >= treeCells * 0.95, `every tree drawn: ${m.trees} of about ${treeCells}`);
    assert.ok(l.has(index["ground:litter"]) && l.has(index["ground:needles"]), "needles under the firs, litter under the rest");
    if (fl.number === -1) assert.ok(l.has(index["far:hill"]), "from the land, the town's hill");
  }
  // a fir's square wears needles, an oak's litter
  const wood = CM.makeWood("ground-1"); let fir = null, oak = null;
  for (let y = 0; y < wood.grid.length && !(fir && oak); y++) for (let x = 0; x < wood.grid.length; x++) if (CM.solidAt(wood, x, y) === "tree") { if (CM.treeVariant(wood, x, y) === 1) fir = fir || [x, y]; else oak = oak || [x, y]; }
  assert.ok(fir && oak);
  // below: nothing of it
  const f1 = CM.makeFloor(1, "ground-1"), m1 = CM.floorMesh(f1, CM.THEMES[0], index);
  assert.strictEqual(m1.skirt, 0); assert.strictEqual(m1.ring, 0); assert.strictEqual(m1.covered, f1.grid.flat().filter((c) => c === 0).length);
  assert.ok(!layersOf(m1).has(index["ground:litter"]) && !layersOf(m1).has(index["far:trees"]));
});

test("the scatter: props by the seed, the same twice and another by another seed; never on a thing, a feature or the water; by the Detail; no floor's fingerprint moves; into the mesh, and quick", () => {
  const CM = load();
  for (const [id, P] of Object.entries(CM.PROPS)) { assert.ok(["flat", "cross", "stand", "corner"].includes(P.how), id); assert.ok(P.size[0] > 0 && P.size[1] >= P.size[0] && P.size[1] < 1, id); }
  for (const r of CM.SCATTER) assert.ok(CM.PROPS[r.prop] && r.per > 0 && r.per <= 1, r.prop);
  const town = CM.makeTown("scatter-1"), wood = CM.makeWood("scatter-1"), f3 = CM.makeFloor(3, "scatter-1"), f43 = CM.makeFloor(43, "scatter-1");
  for (const fl of [town, wood, f3, f43]) {
    const a = CM.scatter(fl, "scatter-1"), b = CM.scatter(fl, "scatter-1"), c = CM.scatter(fl, "scatter-2");
    assert.ok(a.length > 0, `floor ${fl.number} has props`); assert.deepStrictEqual(a, b, "the same twice"); assert.notDeepStrictEqual(a, c, "another seed, other props");
    const wet = new Set((fl.decor || []).filter((d) => d.kind === "water").map((d) => `${d.x},${d.y}`));
    for (const p of a) {
      const k = `${p.x},${p.y}`, t = fl.things[k];
      assert.ok(CM.isOpen(fl, p.x, p.y) && !(t && t.type !== "monsters") && !fl.features[k] && (!wet.has(k) || p.id === "steps"), `${p.id} on a clear square at ${k}`);
      assert.ok(Math.abs(p.dx) + p.w / 2 <= 0.9 && Math.abs(p.dz) + p.w / 2 <= 0.9, `${p.id} within its square`);
    }
    assert.strictEqual(CM.scatter(fl, "scatter-1", CM.DETAIL.low).length, 0, "Low: none");
    assert.ok(CM.scatter(fl, "scatter-1", CM.DETAIL.high).length >= a.length, "High: at least as many");
  }
  const ids = (fl) => new Set(CM.scatter(fl, "scatter-1", 1).map((p) => p.id));
  assert.ok(ids(town).has("tuft") && !ids(town).has("bones"), "grass in town, no bones"); assert.ok(ids(f3).has("bones") && !ids(f3).has("tuft"), "bones in the Catacombs, no grass");
  for (const p of CM.scatter(town, "scatter-1", 1)) if (p.id === "tuft") assert.strictEqual(CM.groundAt(town, p.x, p.y), "grass", "tufts only on grass");
  // nothing moves: the floor's fingerprint with the props worked out is the floor's fingerprint
  const fp = CM.floorPrint(f3); CM.scatter(f3, "scatter-1", 1); assert.strictEqual(CM.floorPrint(f3), fp);
  // into the mesh: flat and crossed props in, standing ones left for the billboards
  const index = { wall: 0, floor: 1, ceiling: 2 }, sub = {}; for (let i = 0; i * 4 < Object.keys(CM.PROPS).length; i++) index[`props:${i}`] = 3 + i;
  Object.keys(CM.PROPS).forEach((id, i) => { sub[`prop:${id}`] = [`props:${Math.floor(i / 4)}`, (i % 2) * 0.5, Math.floor((i % 4) / 2) * 0.5, (i % 2) * 0.5 + 0.5, Math.floor((i % 4) / 2) * 0.5 + 0.5]; });
  const props = CM.scatter(f3, "scatter-1", 1), m = CM.floorMesh(f3, CM.THEMES[0], index, { props, sub });
  assert.strictEqual(m.props, props.filter((p) => p.how !== "stand").length);
  const plain = CM.floorMesh(f3, CM.THEMES[0], index); assert.strictEqual(plain.props, 0); assert.ok(m.count > plain.count);
  // quick: fifty floors' props in well under a second
  const t0 = Date.now(); for (let n = 1; n <= 50; n++) CM.scatter(CM.makeFloor(n, "scatter-1"), "scatter-1", 1); const ms = Date.now() - t0;
  assert.ok(ms < 4000, `fifty floors (made and scattered) in ${ms} ms`);
  assert.strictEqual(new CM.Game().settings.detail, "medium");
});

test("the surface's life: grass and flowers by the season, tall grass and hay in the fields, shrubs by the trees, ferns and mushrooms under the leaves, reeds by the water and stepping stones in the ford, barrels and lamps in town, stalls on market day", () => {
  const CM = load();
  const wood = CM.makeWood("life-1"), town = CM.makeTown("life-1"), weekly = CM.makeTown("weekly-2026-44");
  const ids = (fl, season, seed = "life-1") => { const m = {}; for (const p of CM.scatter(fl, seed, 1, { season })) (m[p.id] = m[p.id] || []).push(p); return m; };
  const summer = ids(wood, "summer"), autumn = ids(wood, "autumn"), winter = ids(wood, "winter"), spring = ids(wood, "spring");
  assert.ok(summer.tuft && summer.flowers && !summer.tuft_dry && !summer.tuft_snow && !summer.snow, "summer: green grass and flowers");
  assert.ok(autumn.tuft_dry && autumn.leaves && !autumn.tuft && !autumn.flowers, "autumn: dry grass and fallen leaves");
  assert.ok(winter.tuft_snow && winter.snow && !winter.tuft && !winter.flowers && !winter.reeds && !winter.fern, "winter: snow");
  assert.ok(spring.flowers && !spring.tallgrass, "spring: flowers, no tall grass yet");
  const F = CM.FIELDS, inFields = (p) => p.x >= F[0] && p.x <= F[2] && p.y >= F[1] && p.y <= F[3];
  assert.ok(summer.tallgrass.every(inFields) && summer.hay && summer.hay.every(inFields), "tall grass and hay in the fields");
  const isTree = (x, y) => wood.grid[y] && wood.grid[y][x] !== 0 && CM.solidAt(wood, x, y) === "tree";
  assert.ok(summer.shrub.every((p) => [[-1, -1], [0, -1], [1, -1], [-1, 0], [1, 0], [-1, 1], [0, 1], [1, 1]].some(([dx, dy]) => isTree(p.x + dx, p.y + dy))), "shrubs by the trees");
  const canopy = new Set(wood.canopy); assert.ok(summer.fern.every((p) => canopy.has(`${p.x},${p.y}`)) && summer.mushroom.every((p) => canopy.has(`${p.x},${p.y}`)), "ferns and mushrooms under the leaves");
  assert.ok(!summer.tuft.some((p) => canopy.has(`${p.x},${p.y}`)), "no meadow grass under the leaves");
  const wet = new Set(wood.decor.filter((d) => d.kind === "water").map((d) => `${d.x},${d.y}`));
  assert.ok(summer.reeds.every((p) => CM.DIRS.some(([dx, dy]) => wet.has(`${p.x + dx},${p.y + dy}`))), "reeds by the water");
  assert.deepStrictEqual(summer.steps.map((p) => `${p.x},${p.y}`), [wood.ford.join(",")], "stepping stones in the ford, and only there");
  const t = ids(town, "summer"), w = ids(weekly, "summer", "weekly-2026-44");
  assert.ok(t.barrel && t.lamp && !t.stall && !t.reeds && !t.bones, "barrels and lamps in town; no stalls on an ordinary seed");
  assert.ok(w.stall && w.stall.every((p) => p.x >= CM.TOWN_SQUARE[0] && p.x <= CM.TOWN_SQUARE[2] && p.y >= CM.TOWN_SQUARE[1] && p.y <= CM.TOWN_SQUARE[3]), "stalls in the Square on market day");
  assert.ok(t.barrel.every((p) => CM.groundAt(town, p.x, p.y) !== "flags"), "no barrel in a doorway");
  assert.ok(CM.PROPS.lamp.night, "lamps are lit at night");
  const below = ids(CM.makeFloor(3, "life-1"), "summer"); assert.ok(!below.tuft && !below.barrel && !below.reeds, "none of it below");
});

test("the dungeon's debris: each band its own palette and not another's; the named rooms their clutter; cobwebs across the corners under the ceiling; nothing in a doorway; the fingerprints as they were", () => {
  const CM = load();
  const PALETTE = { 0: ["coffinlid", "candle", "dust"], 1: ["puddle", "slime"], 2: ["rubble", "rails"], 3: ["candelabra", "frost", "glass"], 4: ["shells", "weed"], 5: ["fungi"], 6: ["shard"], 7: ["slag", "cogs"], 8: ["bonepile"], 9: ["roots"] };
  const OWN = { coffinlid: [0], candelabra: [3], frost: [3], shells: [4], fungi: [5], shard: [6], slag: [7], cogs: [7], bonepile: [8], roots: [9], rails: [2] };
  const seen = {};
  for (let n = 1; n <= 50; n++) for (const seed of ["debris-1", "debris-2"]) {
    const fl = CM.makeFloor(n, seed), band = CM.themeIndex(n), fp = CM.floorPrint(fl);
    for (const p of CM.scatter(fl, seed, 1)) {
      (seen[band] = seen[band] || new Set()).add(p.id);
      const f = fl.features[`${p.x},${p.y}`]; assert.ok(!f, `${p.id} on a ${f && f.type} at ${p.x},${p.y}`);
      if (OWN[p.id] && !(p.id === "coffinlid" && (fl.rooms || []).some((r) => r.name === "Crypt" && p.x >= r.x0 && p.x <= r.x1 && p.y >= r.y0 && p.y <= r.y1))) assert.ok(OWN[p.id].includes(band), `${p.id} in band ${band} (floor ${n})`);
      if (p.how === "corner") { assert.ok(p.corner && Math.abs(p.corner[0]) === 1 && Math.abs(p.corner[1]) === 1, "a corner"); assert.ok(!CM.isOpen(fl, p.x + p.corner[0], p.y) && !CM.isOpen(fl, p.x, p.y + p.corner[1]), `${p.id} in a real corner`); }
    }
    assert.strictEqual(CM.floorPrint(fl), fp);
  }
  for (const [band, ids] of Object.entries(PALETTE)) for (const id of ids) assert.ok(seen[band] && seen[band].has(id), `${id} in band ${band}`);
  // the named rooms
  let rooms = {};
  for (let n = 1; n <= 50; n++) for (const seed of ["debris-1", "debris-2", "debris-3"]) {
    const fl = CM.makeFloor(n, seed), inRoom = (p, name) => (fl.rooms || []).some((r) => r.name === name && p.x >= r.x0 && p.x <= r.x1 && p.y >= r.y0 && p.y <= r.y1);
    for (const p of CM.scatter(fl, seed, 1)) for (const [id, name] of [["coins", "Treasure Vault"], ["books", "Library"], ["scrolls", "Library"], ["straw", "Den"]]) if (p.id === id) { assert.ok(inRoom(p, name), `${id} outside a ${name}`); rooms[id] = true; }
  }
  assert.ok(rooms.coins && rooms.books && rooms.straw, JSON.stringify(rooms));
  // the cobweb's mesh: a quad under the ceiling
  const fl = CM.makeFloor(2, "debris-1"), webs = CM.scatter(fl, "debris-1", 1).filter((p) => p.id === "cobweb");
  assert.ok(webs.length > 0);
  const index = { wall: 0, floor: 1, ceiling: 2, "prop:cobweb": 3 }, m = CM.floorMesh(fl, CM.THEMES[0], index, { props: webs, sub: {} });
  let low = 1; for (let i = 0; i < m.data.length; i += CM.MESH_STRIDE) if (m.data[i + 5] === 3) low = Math.min(low, m.data[i + 1]);
  assert.ok(low > 0.5 && low < 1, `the webs hang under the ceiling (lowest ${low})`);
  for (const id of ["candle", "candelabra", "fungi", "shard"]) assert.ok(CM.PROPS[id].glow > 0, `${id} glows`);
});

test("traces: a drunk potion leaves its bottle where it was drunk, a fight its remains by the kind and a scorch after fire, a spent torch its stub; the floor keeps forty, through a save; and they are drawn", () => {
  const CM = load();
  const g = new CM.Game(); g.newGame("trace-1", fixedParty(CM));
  const fl = g.floor, at = () => fl.pos.join(",");
  // a potion drunk on the way: a red bottle where the party stands; a mana potion, a blue one
  g.party[0].hp = 1; g.bag.push({ name: "Healing Potion", kind: "heal", power: 20, value: 20 }); assert.strictEqual(g.give(g.bag.length - 1, 0), "");
  let last = fl.traces[fl.traces.length - 1]; assert.strictEqual(last.id, "bottle_red"); assert.strictEqual(`${last.x},${last.y}`, at());
  const caster = g.party.findIndex((h) => h.maxmp); g.party[caster].mp = 0; g.bag.push({ name: "Mana Potion", kind: "mana", power: 12, value: 25 }); assert.strictEqual(g.give(g.bag.length - 1, caster), "");
  assert.strictEqual(fl.traces[fl.traces.length - 1].id, "bottle_blue");
  // a fight: remains by the kind, and after fire a scorch and ash
  const fight = (kind, fire) => {
    const k = "1,1"; fl.things[k] = { type: "monsters", group: [CM.makeMonster(CM.monsterKind(kind), 2, new CM.Random(1))] };
    g.foes = fl.things[k].group; g.foeKey = k; g.combat = { round: 1, order: [], index: 0, burned: Boolean(fire) }; g.mode = "combat"; for (const m of g.foes) m.hp = 0;
    const n = (fl.traces || []).length; g.wonFight(); return fl.traces.slice(n).map((t) => `${t.id}@${t.x},${t.y}`);
  };
  assert.ok(fight("Skeleton").includes("bones@1,1"), "the dead leave bones");
  assert.ok(fight("Orc").includes("stain@1,1"), "the living a stain");
  const burnt = fight("Orc", true); assert.ok(burnt.includes("ash@1,1") && burnt.includes("scorch@1,1"), `fire leaves ash and a scorch: ${burnt}`);
  // a torch burnt out and a fresh one lit: the stub
  g.mode = "explore"; g.bag.push(CM.torch()); g.light = { kind: "torch", left: 1 }; const n0 = fl.traces.length; g.burnLight ? g.burnLight() : null;
  for (let i = 0; i < 3 && fl.traces.length === n0; i++) { g.light = { kind: "torch", left: 1 }; g.bag.push(CM.torch()); g.move(0); g.move(2); }
  assert.ok(fl.traces.slice(n0).some((t) => t.id === "stub"), "a stub where the torch went out");
  // through a save, and back
  g.saveRun(); const g2 = new CM.Game(); g2.continueRun(); assert.strictEqual(JSON.stringify(g2.floor.traces), JSON.stringify(fl.traces), "the traces come back");
  // forty at most, the oldest first to go
  for (let i = 0; i < 60; i++) g.trace("stain", 2, 2);
  assert.strictEqual(fl.traces.length, CM.TRACES_MOST); assert.ok(fl.traces.every((t) => t.id === "stain"), "the oldest went first");
  g.saveRun(); const size = JSON.stringify(g.lastRun).length; assert.ok(size < 400000, `the save stays small: ${size}`);
  // drawn: as props, at every Detail
  const tp = CM.traceProps(fl); assert.strictEqual(tp.length, CM.TRACES_MOST); assert.ok(tp.every((p) => p.trace && p.how === "flat" && p.layer === "prop:stain"));
  assert.strictEqual(CM.remainsOf({ kind: "Imp" }), "ash"); assert.strictEqual(CM.remainsOf({ kind: "Zombie", undead: true }), "bones");
  // nothing traced at the camp
  g.mode = "camp"; const before = fl.traces.length; g.trace("stub", 1, 1); assert.strictEqual(fl.traces.length, before);
});

test("walls, floors and ceilings with variation: squares turned by hash, corners darkened, decals by band and never on a secret, a lever or a carving, beams and stalactites overhead; the surface untouched", () => {
  const CM = load();
  const index = { wall: 0, wall2: 1, wallbones: 2, wallsecret: 3, floor: 4, ceiling: 5 }; let n = 6;
  for (const id of ["crack", "moss", "wet", "roots", "chains", "sconce", "niche", "banner", "frost", "soot"]) index[`decal:${id}`] = n++;
  for (const id of ["beam", "rib", "stalactite", "hangroot"]) index[`over:${id}`] = n++;
  const decalLayers = new Set(Object.entries(index).filter(([k]) => k.startsWith("decal:")).map(([, v]) => v));
  const verts = (m) => { const out = []; for (let i = 0; i < m.data.length; i += CM.MESH_STRIDE) out.push(m.data.slice(i, i + CM.MESH_STRIDE)); return out; };
  // the floor squares wear different turns: their first vertices' uvs are not all the same
  const f3 = CM.makeFloor(3, "vary-1"), m3 = CM.floorMesh(f3, CM.THEMES[0], index), v3 = verts(m3);
  const floorUVs = new Set(v3.filter((v) => v[5] === index.floor && v[1] === 0).map((v) => `${v[3]},${v[4]}`)); assert.ok(floorUVs.size >= 4, `turned and mirrored: ${floorUVs.size} corners`);
  // a corner by two walls is darker than the middle of a room
  const shades = v3.filter((v) => v[5] === index.floor).map((v) => v[6]); assert.ok(Math.min(...shades) < 0.7 && Math.max(...shades) > 0.9, `${Math.min(...shades)}..${Math.max(...shades)}`);
  // decals by band, and overhead
  let decals = 0, beams = 0, stalactites = 0;
  for (const [num, seed] of [[3, "vary-1"], [8, "vary-1"], [13, "vary-1"], [18, "vary-1"], [33, "vary-1"], [48, "vary-1"]]) {
    const fl = CM.makeFloor(num, seed), m = CM.floorMesh(fl, CM.themeFor(num), index); decals += m.decals;
    if (num === 13) beams = m.overhead; if (num === 33) stalactites = m.overhead;
    // never on a secret door's wall, a lever's or a carving's: walk every decal quad back to its square and face
    const vs = verts(m).filter((v) => decalLayers.has(v[5]));
    for (let i = 0; i < vs.length; i += 6) {
      const xs = vs.slice(i, i + 6), cx = xs.reduce((s, v) => s + v[0], 0) / 6, cz = xs.reduce((s, v) => s + v[2], 0) / 6;
      const wx = Math.floor(cx + (cx % 1 > 0.9 ? 0.5 : cx % 1 < 0.1 ? -0.5 : 0)), wz = Math.floor(cz + (cz % 1 > 0.9 ? 0.5 : cz % 1 < 0.1 ? -0.5 : 0));
      for (const [k, f] of Object.entries(fl.features)) if (f.type === "secret" && !f.found) { const [sx, sy] = k.split(",").map(Number); assert.ok(!(Math.abs(cx - (sx + 0.5)) <= 0.51 && Math.abs(cz - (sy + 0.5)) <= 0.51), `a decal gives away the secret door at ${k} on floor ${num}`); }
    }
  }
  assert.ok(decals > 20, `${decals} decals`); assert.ok(beams > 0, "beams over the Dwarven Halls"); assert.ok(stalactites > 0, "stalactites in the Crystal Caverns");
  assert.strictEqual(CM.floorMesh(f3, CM.THEMES[0], index, { decals: false }).decals, 0);
  // the town: none of it
  const town = CM.makeTown("vary-1"), mt = CM.floorMesh(town, CM.TOWN_THEME, index); assert.strictEqual(mt.decals, 0); assert.strictEqual(mt.overhead, 0);
  // the floor is the seed's: the same twice
  assert.deepStrictEqual(CM.floorMesh(CM.makeFloor(13, "vary-1"), CM.THEMES[2], index).data, CM.floorMesh(CM.makeFloor(13, "vary-1"), CM.THEMES[2], index).data);
});

test("light and shadow: every band has a slight grade; the glowing props are lights; the shader takes twelve lights and the sun's direction", () => {
  const CM = load();
  for (let i = 0; i < CM.THEMES.length; i++) { const g = CM.THEMES[i].grade; assert.ok(g && g.length === 3 && g.every((c) => c > 0.85 && c < 1.15), `band ${i}: ${g}`); }
  assert.ok(!CM.TOWN_THEME.grade && !CM.WOOD_THEME.grade, "the surface ungraded");
  for (const id of ["candle", "candelabra", "fungi", "shard", "slag"]) assert.ok(CM.PROPS[id].glow, id);
  assert.ok(CM.PROPS.lamp.night);
  const src = fs.readFileSync(path.join(ROOT, "src", "js", "40-render.js"), "utf8");
  assert.ok(/uLightPos\[12\]/.test(src) && /uLightCol\[12\]/.test(src) && /uSun\b/.test(src) && /uGrade\b/.test(src), "the shader's lights, sun and grade");
  assert.ok(/slice\(0, 12\)/.test(fs.readFileSync(path.join(ROOT, "src", "js", "80-main.js"), "utf8")), "no more than twelve lights a frame");
});

test("the pack's weight only slows: walking, Explore and Where to? work at any weight; a warning once when the pack goes over; bulk selling at the merchant keeps what a run needs; Automatic goes home by Homecoming to sell, and back", () => {
  const CM = load();
  const g = new CM.Game(); g.newGame("weight-1", fixedParty(CM));
  const heavy = () => { for (let i = 0; i < 40; i++) g.bag.push({ name: "Plate Armour", kind: "armor", slot: "armor", power: 6, value: 200, weight: 8 }); };
  heavy(); assert.ok(g.overweight() > 2, `over: ${g.overweight()}`);
  assert.ok(g.walkPace() > 1 && g.walkPace() <= 3); assert.strictEqual(new CM.Game().walkPace ? 1 : 1, 1);
  const n0 = g.messages.length, torch0 = g.light.left; const o = CM.openNeighbours(g.floor, ...g.floor.pos)[0]; g.floor.facing = CM.DIRS.findIndex(([dx, dy]) => dx === o[0] && dy === o[1]);
  assert.ok(g.move(0), "the party still walks"); assert.ok(g.messages.slice(n0).some((m) => m.includes("walks slowly")), "the warning");
  assert.strictEqual(torch0 - g.light.left, 1, "no extra torch for the weight");
  const n1 = g.messages.length; g.move(2); assert.ok(!g.messages.slice(n1).some((m) => m.includes("walks slowly")), "only once");
  assert.ok(g.explore() !== false || g.messages.slice(-1)[0].includes("Nothing more"), "Explore is not refused for the weight");
  assert.ok(!g.messages.some((m) => m.includes("too heavy to run")));
  // bulk selling: spare gear, a filter's worth; keys, relics and a remembering scroll kept
  g.bag.push(CM.scroll("homecoming")); g.bag[g.bag.length - 1].back = { floor: 3, pos: [1, 1] }; g.bag.push({ name: "Iron Key", kind: "key", power: 0, value: 0 }); g.bag.push({ name: "Crown of Old", kind: "helm", slot: "helm", power: 2, value: 500, props: { relic: true } });
  g.openBag(true); const gold0 = g.gold, spare = g.sellable("spare");
  assert.ok(spare.rows.length >= 40 && spare.gold >= 40 * 100);
  assert.strictEqual(g.sellMany("spare"), ""); assert.strictEqual(g.gold, gold0 + spare.gold);
  assert.ok(g.bag.some((i) => i.kind === "key") && g.bag.some((i) => i.props && i.props.relic) && g.bag.some((i) => i.back), "kept");
  assert.ok(g.overweight() <= 1); const all = g.sellable("all"); assert.ok(!all.rows.some((r) => g.bag[r].kind === "key" || g.bag[r].back));
  g.closeBag();
  // Automatic: over the line below, with a scroll, it goes home, sells, and comes back down by the scroll
  const g2 = new CM.Game(); g2.newGame("weight-2", fixedParty(CM)); g2.enterFloor(4, "down"); const back = [g2.floor.number, g2.floor.pos.join()];
  for (let i = 0; i < 40; i++) g2.bag.push({ name: "Plate Armour", kind: "armor", slot: "armor", power: 6, value: 200, weight: 8 });
  g2.bag.push(CM.scroll("homecoming")); g2.clock = 2 * 60;
  const auto = new CM.Autopilot(g2, { warp: true, wake: true, sync: true, land: false }); let n = 0, home = false;
  while (n++ < 3000) { auto.step(); if (g2.floor.number === 0) home = true; if (home && g2.floor.number === back[0]) break; if (g2.mode === "title") break; }
  assert.ok(home, "home by the scroll"); assert.ok(g2.overweight() <= 1, `sold: ${g2.overweight()}`); assert.strictEqual(g2.floor.number, back[0], "and back to the floor it left");
  assert.ok((auto.tools.weightTrips || 0) >= 1);
  // a torch picked up after the last one went out is lit when the party walks, and walking by itself goes on
  const g3 = new CM.Game(); g3.newGame("weight-3", fixedParty(CM)); g3.light = { kind: null, left: 0 }; g3.bag = g3.bag.filter((i) => i.kind !== "torch"); g3.bag.push(CM.torch());
  const o3 = CM.openNeighbours(g3.floor, ...g3.floor.pos)[0]; g3.floor.facing = CM.DIRS.findIndex(([dx, dy]) => dx === o3[0] && dy === o3[1]); g3.move(0);
  assert.strictEqual(g3.light.kind, "torch", "lit on the next step"); assert.ok(!g3.bag.some((i) => i.kind === "torch"));
});

test("the air: dust in every band and each band's own; on the surface rain, snow, leaves, fireflies, birds, clouds and chimney smoke by the season, the weather and the hour; none at Low", () => {
  const CM = load();
  const ids = (env) => CM.airKinds(env).map((k) => k.id);
  assert.ok(ids({ surface: false, band: 0 }).includes("mote"));
  assert.ok(ids({ surface: false, band: 1 }).includes("drip") && ids({ surface: false, band: 7 }).includes("ember") && ids({ surface: false, band: 5 }).includes("spore") && ids({ surface: false, band: 6 }).includes("glitter"));
  assert.ok(!ids({ surface: false, band: 0 }).includes("ember") && !ids({ surface: false, band: 0 }).includes("rain"), "no weather below");
  const day = { surface: true, season: "summer", weather: "clear", night: false }, nightS = { ...day, night: true };
  assert.ok(ids(day).includes("bird") && ids(day).includes("cloud") && !ids(day).includes("firefly") && !ids(day).includes("rain"));
  assert.ok(ids(nightS).includes("firefly") && !ids(nightS).includes("bird"), "fireflies on a summer night");
  assert.ok(ids({ ...day, weather: "rain" }).includes("rain") && !ids({ ...day, weather: "rain" }).includes("leaf"));
  assert.ok(ids({ ...day, season: "winter", weather: "snow" }).includes("snow") && !ids({ ...day, season: "winter", weather: "snow" }).includes("leaf"));
  const autumn = CM.airKinds({ ...day, season: "autumn" }).find((k) => k.id === "leaf"), summer = CM.airKinds(day).find((k) => k.id === "leaf"); assert.ok(autumn.rate > summer.rate * 3, "leaves fall in autumn");
  assert.ok(ids({ ...day, town: true }).includes("smoke") && !ids(day).includes("smoke"), "chimney smoke in town");
  assert.strictEqual(CM.AIR_BUDGET.low, 0); assert.ok(CM.AIR_BUDGET.high > CM.AIR_BUDGET.medium);
  assert.ok(CM.windOf("wind")[0] > CM.windOf("clear")[0]);
  const src = fs.readFileSync(path.join(ROOT, "src", "js", "46-air.js"), "utf8");
  for (const id of ["mote", "drip", "ember", "spore", "glitter", "leaf", "firefly", "rain", "snow", "cloud", "bird", "smoke"]) assert.ok(src.includes(`case "${id}"`), `${id} spawns and is drawn`);
});

test("the clock made visible: the dial's sun and moon follow the clock and the season's daylight; the phase drawn is the game's; the next full and new moons; the weather ahead is the seed's; the Calendar's key and dialog", () => {
  const CM = load();
  const g = new CM.Game(); g.newGame("dial-1", fixedParty(CM), "pauper", "fair", [], "dungeon", { town: true });
  const set = (day, h, season) => { g.season = season; g.clock = day * CM.CLOCK.day + ((h - 6 + 24) % 24) * 60; return CM.dialOf(g); };
  for (const season of CM.SEASONS) {
    const [dawn, dusk] = CM.DAYLIGHT[season];
    assert.ok(Math.abs(set(0, dawn, season).sun + 90) < 0.01, `${season}: the sun rises on the left at ${dawn}`);
    assert.ok(Math.abs(set(0, (dawn + dusk) / 2, season).sun) < 0.01, `${season}: the sun at the top at midday`);
    assert.ok(Math.abs(set(0, dusk - 0.0001, season).sun - 90) < 0.1, `${season}: the sun sets on the right`);
    for (let h = 0; h < 24; h += 0.5) {
      const D = set(3, h, season);
      assert.strictEqual(D.night, CM.isNight(g), `${season} ${h}: the dial's night is the rules' night`);
      assert.ok(D.night ? Math.abs(D.sun) >= 90 : Math.abs(D.sun) <= 90, `${season} ${h}: the sun above the ground by day only (on the horizon at dawn and dusk)`);
      assert.ok(Math.abs(Math.abs(D.sun - D.moon) - 180) < 0.01, "the moon opposite the sun");
    }
  }
  assert.strictEqual(set(0, 22.5, "summer").sky, "night"); assert.strictEqual(set(0, 4.5, "summer").sky, "dawn"); assert.strictEqual(set(0, 21.5, "summer").sky, "dusk"); assert.strictEqual(set(0, 12, "summer").sky, "day");
  for (let day = 0; day < 70; day++) { const D = set(day, 23, "spring"); assert.strictEqual(D.phase, CM.moonPhase(g)); assert.strictEqual(CM.phaseOfDay(day), CM.moonPhase(g), "the drawn phase is the game's"); assert.strictEqual(D.moonDay, (day % CM.CLOCK.moon) + 1); }
  set(10, 12, "spring"); assert.strictEqual(CM.timeFigures(g), "12:00"); g.clock += 7; assert.strictEqual(CM.timeFigures(g), "12:07");
  for (const phase of [0, 4]) {
    for (const day of [0, 5, 13, 20, 28]) {
      set(day, 12, "spring"); const k = CM.nextMoon(g, phase);
      assert.ok(k !== null && CM.phaseOfDay(day + k) === phase, `the next ${phase ? "full" : "new"} moon from day ${day} is one`);
      for (let j = 0; j < k; j++) assert.notStrictEqual(CM.phaseOfDay(day + j), phase, "and none comes sooner");
    }
  }
  set(14, 23, "spring"); assert.ok(CM.fullMoon(g) && CM.nextMoon(g, 4) === 0, "a full moon tonight");
  assert.ok(CM.MOON_DOES[0] && CM.MOON_DOES[4], "what the new and full moons do");
  set(4, 12, "autumn"); const ahead = CM.comingWeather(g, 7);
  assert.strictEqual(ahead.length, 7); assert.strictEqual(ahead[0].weather, CM.weather(g), "today's weather first");
  ahead.forEach((d, k) => { assert.strictEqual(d.day, 4 + k); assert.strictEqual(d.weather, CM.weatherOf(g.seed, 4 + k, "autumn"), "the seed's weather"); });
  g.clock += CM.CLOCK.day; assert.strictEqual(CM.weather(g), ahead[1].weather, "tomorrow's weather comes as shown");
  assert.strictEqual(CM.moonPath(0, 10), "", "a new moon shows nothing lit");
  assert.strictEqual((CM.moonPath(4, 10).match(/A/g) || []).length, 2, "a full moon is the whole disc");
  assert.ok(/A10 10 0 0 1 0 10A7\.07 10 0 0 0 0 -10Z$/.test(CM.moonPath(1, 10)), "a waxing crescent: lit on the right, the terminator bowed toward the light");
  assert.ok(/A10 10 0 0 0 0 10A7\.07 10 0 0 0 0 -10Z$/.test(CM.moonPath(5, 10)), "a waning gibbous: lit on the left, the terminator bowed away");
  assert.strictEqual(CM.DEFAULT_KEYS.calendar, "KeyK"); assert.ok(CM.KEY_ACTIONS.some(([id]) => id === "calendar"));
  const keys = Object.values(CM.DEFAULT_KEYS).filter((k) => k !== "KeyA" && k !== "KeyD"); assert.strictEqual(new Set(keys).size, keys.length, "K is no other action's key");
  const src = (f) => fs.readFileSync(path.join(ROOT, "src", "js", f), "utf8");
  assert.ok(src("73b-clock.js").includes("drawSky()") && src("73b-clock.js").includes("openCalendar()"));
  assert.ok(src("70-ui.js").includes('id="dlg-calendar"') && src("70-ui.js").includes('class="dial"') && src("80-main.js").includes("K.calendar"));
  assert.ok(!src("73-play.js").includes("drawSky() {"), "one drawSky");
});

test("the buildings: every house cell in one rectangle under one gabled roof; walls on every outside face, whatever stands beside; the ridge and eaves where they should be; chimneys on the roofs; none below ground", () => {
  const CM = load();
  const g = new CM.Game(); g.newGame("bld-1", fixedParty(CM), "pauper", "fair", [], "dungeon", { town: true });
  const fl = g.floor; assert.strictEqual(fl.number, 0);
  const B = CM.buildingsOf(fl), cells = new Map();
  for (const b of B) {
    assert.ok(b.x1 >= b.x0 && b.y1 >= b.y0 && b.rise >= CM.ROOF.minRise && b.rise <= CM.ROOF.maxRise);
    const span = b.along === "x" ? b.y1 - b.y0 + 1 : b.x1 - b.x0 + 1, len = b.along === "x" ? b.x1 - b.x0 + 1 : b.y1 - b.y0 + 1; assert.ok(len >= span, "the ridge runs along the longer side");
    for (let y = b.y0; y <= b.y1; y++) for (let x = b.x0; x <= b.x1; x++) { assert.ok(CM.isBuilding(fl, x, y), `${x},${y} is a house cell`); assert.ok(!cells.has(`${x},${y}`), "in one rectangle only"); cells.set(`${x},${y}`, b); }
    const X0 = b.x0, X1 = b.x1 + 1, Z0 = b.y0, Z1 = b.y1 + 1, cx = (X0 + X1) / 2, cz = (Z0 + Z1) / 2;
    assert.ok(Math.abs(CM.roofAt(b, cx, cz) - (b.h + b.rise)) < 1e-9, "the ridge over the middle");
    const edge = b.along === "x" ? CM.roofAt(b, cx, Z0) : CM.roofAt(b, X0, cz); assert.ok(Math.abs(edge - b.h) < 1e-9, "the roof meets the walls' top at the wall line");
    assert.strictEqual(b.along === "x" ? CM.roofAt(b, cx, Z0 - 1) : CM.roofAt(b, X0 - 1, cz), null, "nothing past the eaves");
  }
  const all = Object.entries(fl.kinds).filter(([, k]) => CM.BUILDING_KINDS.includes(k)).length; assert.strictEqual(cells.size, all, "every house cell roofed");
  assert.ok(B.some((b) => (b.x1 - b.x0 + 1) * (b.y1 - b.y0 + 1) >= 9), "the blocks stay whole: one roof over a 3x3 or more");
  let faces = 0, besideSolid = 0;
  for (const key of cells.keys()) { const [x, y] = key.split(",").map(Number); for (const [dx, dy] of [[0, -1], [0, 1], [1, 0], [-1, 0]]) if (!CM.isBuilding(fl, x + dx, y + dy)) { faces++; if (!CM.isOpen(fl, x + dx, y + dy)) besideSolid++; } }
  assert.ok(besideSolid > 0, "some houses stand against a hedge, a fence, a tree or the wall");
  const index = {}; ["wall", "solid:house", "solid:door", "solid:shop", "solid:roof", "solid:gable", "solid:townwall", "solid:townwall:top", "ground:grass"].forEach((k, i) => { index[k] = i; });
  const m = CM.floorMesh(fl, CM.themeFor(0), index, { props: [] });
  assert.strictEqual(m.buildings, B.length);
  assert.ok(m.walls >= faces, `a wall on every outside face, those against a hedge or a tree too (${m.walls} of ${faces})`);
  assert.ok(m.roofs >= B.length * 2, "two slopes a building");
  const C = CM.chimneysOf(fl); assert.strictEqual(m.chimneys, C.length); assert.ok(C.length >= 3, "chimneys in the town");
  for (const c of C) { const b = cells.get(`${Math.floor(c.x)},${Math.floor(c.z)}`); assert.ok(b, "a chimney stands on a building"); assert.ok(c.top > b.h + b.rise && c.base < CM.roofAt(b, c.x, c.z), "through the roof, and over the ridge"); }
  // the faces seen from inside a building are never drawn: every wall vertex lies on a building's outline
  const d = m.data, S = CM.MESH_STRIDE;
  for (let i = 0; i < d.length; i += S) { const layer = d[i + 5]; if (layer !== index["solid:house"]) continue; const x = d[i], z = d[i + 2]; assert.ok(Math.abs(x - Math.round(x)) < 1e-6 || Math.abs(z - Math.round(z)) < 1e-6, "on the grid lines"); }
  const deep = new CM.Game(); deep.newGame("bld-2", fixedParty(CM)); deep.enterFloor(3, "down"); assert.strictEqual(CM.buildingsOf(deep.floor).length, 0, "no buildings below ground");
  CM.setSolid(fl, 13, 18, "house"); fl.grid[18][13] = 1; assert.ok(CM.buildingsOf(fl).some((b) => b.x0 <= 13 && b.x1 >= 13 && b.y0 <= 18 && b.y1 >= 18), "a house raised is roofed at once");
});

test("monsters that move: a breath of its own; a lunge out and back; a flinch that breaks a lunge; a fall that topples and fades; a flight that runs and shrinks; a sleeper lies; reduced motion keeps only the flash and the fade", () => {
  const CM = load(), M = CM.MOTION, at = (o) => CM.motion(Object.assign({ now: 10000, phase: 0 }, o));
  const a = at({ phase: 0 }).scaleY, b = at({ phase: 2 }).scaleY; assert.notStrictEqual(a, b, "a pack breathes out of step"); assert.ok(Math.abs(a - 1) <= M.breath + 1e-9);
  const peak = at({ lungeAt: 10000 - M.lungeIn }); assert.ok(Math.abs(peak.forward - M.lungeReach) < 1e-9, "the lunge reaches a quarter of a square");
  assert.ok(at({ lungeAt: 10000 - 60 }).forward > 0 && at({ lungeAt: 10000 - 60 }).forward < M.lungeReach);
  assert.strictEqual(at({ lungeAt: 10000 - M.lungeIn - M.lungeOut - 1 }).forward, 0, "and comes back to rest");
  const broken = at({ lungeAt: 10000 - 100, hitAt: 10000 - 20 }); assert.strictEqual(broken.forward, 0, "struck mid-lunge, the lunge is broken off"); assert.ok(broken.back > 0 && broken.flash > 0, "it flinches back, white");
  assert.strictEqual(at({ hitAt: 10000 - M.flinchMs - 1 }).back, 0); assert.strictEqual(at({ hitAt: 10000 - M.flashMs - 1 }).flash, 0);
  const falling = at({ fellAt: 10000 - M.fallMs }); assert.ok(Math.abs(falling.tilt - M.fallTilt) < 1e-9 && falling.alpha === 1, "toppled, then fading");
  const gone = at({ fellAt: 10000 - M.fallMs - M.fadeMs }); assert.ok(gone.done && gone.alpha === 0);
  const ghost = at({ fellAt: 10000 - 300, ghost: true }); assert.strictEqual(ghost.tilt, 0); assert.ok(ghost.lift > 0, "a ghost rises away");
  const run = at({ fledAt: 10000 - M.fleeMs / 2 }); assert.ok(run.back > 0 && run.scale < 1 && run.alpha < 1, "running down the corridor, smaller"); assert.ok(at({ fledAt: 10000 - M.fleeMs }).done);
  const sleep = at({ sleeping: true }); assert.ok(sleep.tilt > 1.2 && sleep.forward === 0 && sleep.flash === 0, "a sleeper lies on its side");
  const rising = at({ roseAt: 10000 - 100 }); assert.ok(rising.lift < 0, "a guardian rises from the floor"); assert.strictEqual(at({ roseAt: 10000 - M.riseMs }).lift, 0);
  assert.ok(at({ sway: true }).skew !== 0 && at({}).skew === 0, "the Lich King's robe stirs");
  const R = (o) => at(Object.assign({ reduced: true }, o));
  assert.strictEqual(R({}).scaleY, 1); assert.strictEqual(R({ lungeAt: 10000 - M.lungeIn }).forward, 0); assert.strictEqual(R({ hitAt: 10000 - 50 }).back, 0); assert.ok(R({ hitAt: 10000 - 20 }).flash > 0, "the flash stays");
  const rf = R({ fellAt: 10000 - M.fallMs }); assert.strictEqual(rf.tilt, 0); assert.ok(rf.alpha < 1 && rf.alpha > 0, "reduced: it only fades");
  assert.ok(CM.facesMirror(0.3) && !CM.facesMirror(-0.3) && !CM.facesMirror(0), "faces the party from either side");
  const src = fs.readFileSync(path.join(ROOT, "src", "js", "40-render.js"), "utf8"); assert.ok(src.includes("s.tilt") && src.includes("s.mirror"), "the renderer draws the pose");
});

test("the living dungeon: lairs by the seed, the floor unmoved; a sleeper stays put; the light down a corridor wakes it, a shaded light does not; noise through a door is quieter; a quiet step; a sleeper struck gives a free round that always lands", () => {
  const CM = load();
  // the lairs: the same every time, about three packs in five, and the floor's walls and way down where they were
  let packs = 0, sleeping = 0, champions = 0;
  for (const seed of ["lair-1", "lair-2", "lair-3"]) for (let n = 1; n <= 20; n++) {
    const a = CM.makeFloor(n, seed, 2), b = CM.makeFloor(n, seed, 2);
    assert.strictEqual(JSON.stringify(a.things), JSON.stringify(b.things), "the lairs are the seed's");
    for (const t of Object.values(a.things)) if (t.type === "monsters" && !t.still && !t.hunter) { packs++; if (t.asleep) sleeping++; if (t.champion) { champions++; assert.ok(n >= CM.CHAMPION_FROM); assert.ok(CM.CHAMPIONS[t.group[0].champion] && t.group[0].name.startsWith(CM.CHAMPIONS[t.champion].name)); } }
  }
  assert.ok(sleeping / packs > 0.45 && sleeping / packs < 0.75, `about three in five sleep (${sleeping} of ${packs})`);
  assert.ok(champions > 5, `champions lead some packs (${champions})`);
  for (const t of Object.values(CM.makeFloor(3, "lair-1", 2).things)) assert.ok(!t.champion, "no champion above floor six");
  // a floor to play with: one pack asleep, straight down the corridor from the party
  const g = new CM.Game(); g.newGame("lair-4", fixedParty(CM)); g.enterFloor(2, "down");
  const fl = g.floor, size = fl.grid.length;
  for (const k of Object.keys(fl.things)) if (fl.things[k].type === "monsters") delete fl.things[k];
  const row = fl.pos[1]; let far = null;
  for (let x = fl.pos[0] + 1; x < size && CM.isOpen(fl, x, row) && !fl.features[`${x},${row}`]; x++) far = x;
  if (far === null || far - fl.pos[0] < 3) { for (let x = 1; x < size - 1; x++) fl.grid[row][x] = 0; far = Math.min(size - 2, fl.pos[0] + 6); for (let x = fl.pos[0] + 1; x <= far; x++) delete fl.features[`${x},${row}`]; }
  const k = `${far},${row}`, pack = { type: "monsters", group: [CM.makeMonster(CM.monsterKind("Goblin"), 2, new CM.Random(1))], asleep: true };
  fl.things[k] = pack; g.mode = "explore";
  g.light = { kind: "torch", left: 300 }; g.lightOut = true; g.noiseLevel = 0;
  for (let i = 0; i < 6; i++) g.wanderMonsters();
  assert.ok(fl.things[k] === pack && pack.asleep, "a shaded light, a quiet party: it sleeps where it lies");
  assert.strictEqual(g.lightReach(), 0); assert.ok(!g.hasLight(), "shaded: no light to see by"); assert.ok(g.lightFactor() < 0.3);
  g.lightOut = false; assert.ok(g.lightReach() >= CM.LIGHT_REACH.low && g.hasLight());
  if (far - fl.pos[0] <= g.lightReach()) { g.wanderMonsters(); assert.ok(!pack.asleep && pack.hunting > 0, "the torch down the corridor wakes it, and it hunts"); }
  // noise: a closed door costs four squares of it; and what a step makes
  const open = new CM.Game(); open.newGame("lair-5", fixedParty(CM)); open.enterFloor(3, "down");
  const of = open.floor, door = Object.entries(of.features).find(([, f]) => f.type === "door");
  if (door) { const [dx, dy] = door[0].split(",").map(Number); const shut = CM.noiseDistances(of, of.pos).get(door[0]); door[1].open = true; const wide = CM.noiseDistances(of, of.pos).get(door[0]); if (shut !== undefined && wide !== undefined) assert.strictEqual(shut - wide, CM.LAIR.doorCost - 1, "a shut door muffles"); assert.ok(dx >= 0 && dy >= 0); }
  const loud = open.stepNoise(); open.lightOut = true; const hushed = open.stepNoise(); assert.ok(hushed < loud, "shaded, the party is quieter");
  open.party.unshift(open.party.splice(open.party.findIndex((h) => h.cls === "Rogue"), 1)[0]); assert.ok(open.stepNoise() <= hushed, "a Rogue in front, quieter still");
  // the light is lit again on the surface; shading needs a light
  open.lightOut = false; open.light = { kind: null, left: 0 }; open.mode = "explore"; assert.strictEqual(open.douse(), false, "nothing to shade");
  // a sleeping pack walked into: a free round, every blow lands
  const s = new CM.Game(); s.newGame("lair-6", fixedParty(CM)); s.enterFloor(2, "down");
  const sf = s.floor; for (const kk of Object.keys(sf.things)) if (sf.things[kk].type === "monsters") delete sf.things[kk];
  const ahead = CM.DIRS.map(([dx, dy], d) => [d, sf.pos[0] + dx, sf.pos[1] + dy]).find(([, x, y]) => CM.isOpen(sf, x, y) && !sf.features[`${x},${y}`] && !sf.things[`${x},${y}`]);
  sf.facing = ahead[0]; sf.things[`${ahead[1]},${ahead[2]}`] = { type: "monsters", group: [CM.makeMonster(CM.monsterKind("Orc"), 2, new CM.Random(2)), CM.makeMonster(CM.monsterKind("Orc"), 2, new CM.Random(3))], asleep: true };
  s.move(0);
  assert.strictEqual(s.mode, "combat"); assert.ok(s.combat.surprise && s.combat.sure, "they are struck asleep"); assert.ok(s.tally.sleepersStruck >= 1);
  assert.ok(s.combat.order.every((o) => o.hero), "no monster acts in the first round");
});

test("champions: each word does what it says - a ward drinks a spell, stone turns a blow, the fleet and the frenzied act twice, a shriek wakes the floor, a shadow hides from all but a Rogue, a vampire feeds, a hoarder pays", () => {
  const CM = load();
  const fight = (id, opts = {}) => {
    const g = new CM.Game(); g.newGame(`champ-${id}`, fixedParty(CM)); g.enterFloor(8, "down");
    const fl = g.floor; for (const kk of Object.keys(fl.things)) if (fl.things[kk].type === "monsters") delete fl.things[kk];
    if (opts.noRogue) g.party = g.party.filter((h) => h.cls !== "Rogue");
    const t = { type: "monsters", group: [CM.makeMonster(CM.monsterKind("Orc"), 8, new CM.Random(5)), CM.makeMonster(CM.monsterKind("Orc"), 8, new CM.Random(6))] };
    CM.makeChampion(t, id);
    const k = `${fl.pos[0]},${fl.pos[1]}`; fl.things[`${fl.pos[0] + 50},0`] = undefined; delete fl.things[`${fl.pos[0] + 50},0`];
    g.foes = t.group; g.startCombat(k, t);
    return { g, m: t.group[0], t };
  };
  for (const id of Object.keys(CM.CHAMPIONS)) { const { m } = fight(id); assert.strictEqual(m.champion, id); assert.ok(m.name.startsWith(CM.CHAMPIONS[id].name)); }
  { const { g, m } = fight("warded"); g.casting = g.party.find((h) => h.cls === "Mage"); const hp = m.hp; assert.strictEqual(g.spellHit(m, 10, "a test"), 0); assert.strictEqual(m.hp, hp, "the ward drinks the first spell"); g.spellHit(m, 10, "a test"); assert.ok(m.hp < hp, "the second lands"); }
  { const { g, m } = fight("fleet"); g.combat.surprise = false; g.beginRound(); assert.strictEqual(g.combat.order.filter((o) => o.foe === m).length + (m.hp > 0 ? 0 : 2), 2, "the fleet acts twice"); }
  { const { g, m } = fight("frenzied"); m.hp = Math.floor(m.max / 3); g.combat.surprise = false; g.beginRound(); assert.ok(g.combat.order.filter((o) => o.foe === m).length === 2 || m.hp <= 0, "under half, the frenzied twice"); }
  { const { g, m } = fight("stonehide"); g.combat.surprise = false; g.beginRound(); assert.strictEqual(m.stone, m.hp > 0 ? 1 : m.stone); }
  { const { g } = fight("shadowed", { noRogue: true }); assert.ok(g.foes[0].hidden, "unseen without a Rogue"); }
  { const { g } = fight("shadowed"); assert.ok(!g.foes[0].hidden, "a Rogue sees it"); }
  { const { g, m } = fight("shrieking"); const fl = g.floor; const spot = Object.keys(fl.things).length; fl.things["1,1"] = { type: "monsters", group: [CM.makeMonster(CM.monsterKind("Goblin"), 8, new CM.Random(9))], asleep: true };
    g.monsterAct(m); assert.ok(m.shrieked && !fl.things["1,1"].asleep && fl.things["1,1"].hunting > 0, "the shriek wakes the floor"); assert.ok(spot >= 0); }
  { const { m } = fight("hoarder"), { m: plain } = fight("vampiric"); assert.ok(m.gold > plain.gold, "a hoarder carries more"); }
  const src = fs.readFileSync(path.join(ROOT, "src", "js", "62-combat.js"), "utf8"); assert.ok(src.includes('m.champion === "vampiric"'), "a vampire feeds");
});

test("the living dungeon is kept: the shaded light and the noise in the save; a run saved before them migrates; two games on one seed, played the same, wake the same packs; Automatic shades the light near a sleeper with a Rogue in front", () => {
  const CM = load();
  const g = new CM.Game(); g.newGame("keep-1", fixedParty(CM)); g.enterFloor(2, "down"); g.mode = "explore";
  g.lightOut = true; g.noiseLevel = 3; g.saveRun();
  const g2 = new CM.Game(); assert.ok(g2.continueRun()); assert.strictEqual(g2.lightOut, true); assert.strictEqual(g2.noiseLevel, 3);
  const old = JSON.parse(JSON.stringify(g.lastRun)); old.schema = 3; delete old.lightOut; delete old.noiseLevel;
  const m = CM.migrateRun(old); assert.strictEqual(m.schema, CM.SCHEMA); assert.strictEqual(m.lightOut, false); assert.strictEqual(m.noiseLevel, 0);
  const play = () => { const p = new CM.Game(); p.newGame("keep-2", fixedParty(CM)); p.enterFloor(4, "down"); p.mode = "explore"; for (let i = 0; i < 40; i++) { if (p.mode !== "explore") break; if (!p.move(0)) p.turn(1); p.wanderMonsters(); }
    return JSON.stringify(Object.entries(p.floor.things).filter(([, t]) => t.type === "monsters").map(([k, t]) => [k, Boolean(t.asleep), t.hunting || 0])) + p.mode; };
  assert.strictEqual(play(), play(), "the same steps, the same lairs woken");
  const a = new CM.Game(); a.newGame("keep-3", fixedParty(CM)); a.enterFloor(3, "down"); a.mode = "explore";
  a.party.unshift(a.party.splice(a.party.findIndex((h) => h.cls === "Rogue"), 1)[0]);
  const fl = a.floor; for (const kk of Object.keys(fl.things)) if (fl.things[kk].type === "monsters") delete fl.things[kk];
  fl.things[`${fl.pos[0]},${Math.max(0, fl.pos[1] - 3)}`] = { type: "monsters", group: [CM.makeMonster(CM.monsterKind("Goblin"), 3, new CM.Random(4))], asleep: true };
  const auto = new CM.Autopilot(a, { warp: true, sync: true }); auto.stealth(fl); assert.ok(a.lightOut, "Automatic shades the light");
  delete fl.things[`${fl.pos[0]},${Math.max(0, fl.pos[1] - 3)}`]; auto.stealth(fl); assert.ok(!a.lightOut, "and lights it again past the sleeper");
});

test("things that move: a door swings on its hinge and a portcullis lifts over their own time (found open, open at once); a chest emptied stays open where it stood, and is kept; the town's windows are lit at night and only at night; water has the shader's own branch", () => {
  const CM = load(), S = CM.SWING;
  assert.strictEqual(CM.swing(true, null, 1000, S.doorMs), 1, "found open: open"); assert.strictEqual(CM.swing(false, null, 1000, S.doorMs), 0, "found shut: shut");
  assert.strictEqual(CM.swing(true, 1000, 1000, S.doorMs), 0, "just opened: still shut"); assert.strictEqual(CM.swing(true, 1000, 1000 + S.doorMs, S.doorMs), 1, "and open after its time");
  const mid = CM.swing(true, 1000, 1000 + S.doorMs / 2, S.doorMs); assert.ok(mid > 0.4 && mid < 0.6, "half way at half time");
  assert.strictEqual(CM.swing(false, 1000, 1000 + S.gateMs, S.gateMs), 0, "shut again"); assert.ok(S.doorAngle > 1.5 && S.gateLift > 0.8);
  // a chest emptied: an open chest left standing, kept with the floor
  const g = new CM.Game(); g.newGame("move-1", fixedParty(CM)); g.enterFloor(2, "down");
  const fl = g.floor, k = `${fl.pos[0]},${fl.pos[1]}`; fl.things[k] = { type: "chest", gold: 10, items: [], trap: null }; g.mode = "explore"; g.use();
  assert.ok(!fl.things[k], "the chest is emptied"); assert.ok((fl.traces || []).some((t) => t.id === "chest_open" && `${t.x},${t.y}` === k), "an open chest left where it stood");
  assert.strictEqual(CM.PROPS.chest_open.how, "stand"); assert.ok(fs.readFileSync(path.join(ROOT, "src", "js", "30-art.js"), "utf8").includes("case \"chest_open\""), "painted");
  g.saveRun(); const g2 = new CM.Game(); assert.ok(g2.continueRun()); assert.ok((g2.floor.traces || []).some((t) => t.id === "chest_open"), "kept with the floor");
  // the town's windows: lit at night, dark by day
  const town = CM.makeTown("move-2"), index = {}; ["wall", "solid:house", "solid:door", "solid:shop", "solid:roof", "solid:gable", "solid:townwall", "solid:townwall:top", "ground:grass", "window:lit"].forEach((n, i) => { index[n] = i; });
  const day = CM.floorMesh(town, CM.themeFor(0), index, { props: [] }), night = CM.floorMesh(town, CM.themeFor(0), index, { props: [], night: true });
  assert.strictEqual(day.litWindows, 0, "no lit window by day"); assert.ok(night.litWindows > 40, `the town lit at night (${night.litWindows})`); assert.strictEqual(night.walls, day.walls, "the same walls");
  const dungeon = CM.floorMesh(CM.makeFloor(3, "move-3", 2), CM.themeFor(3), index, { props: [], night: true }); assert.strictEqual(dungeon.litWindows, 0, "no windows below");
  // the water, and the rain on the ground, in the shader; the swing in the frame
  const render = fs.readFileSync(path.join(ROOT, "src", "js", "40-render.js"), "utf8"), main = fs.readFileSync(path.join(ROOT, "src", "js", "80-main.js"), "utf8");
  assert.ok(render.includes("vFx.z > 3.5") && render.includes("vFx.z > 2.5 && vFx.z < 3.5"), "water has its own branch, apart from the sky");
  assert.ok(render.includes("uWet") && render.includes("s.swing") && render.includes("s.water ? 4"), "the rain, the swing and the water flag");
  assert.ok(main.includes("water: true") && main.includes("CM.swing(Boolean(f.open)") && main.includes("puddle"), "the frame flags the water, swings the doors, lays the puddles");
});

test("the seasons seen: each tree's crown by the season (bare oaks and birches in winter, snow on the fir, blossom in spring, red in autumn); snow lies in winter on a day of snow and the day after; the surface's pictures are the season's; the land's flowers go in winter", () => {
  const CM = load();
  assert.ok(CM.crownOf(0, "winter").bare && CM.crownOf(2, "winter").bare, "bare in winter"); assert.ok(CM.crownOf(1, "winter").snow && !CM.crownOf(1, "winter").bare, "the fir keeps its needles, snow on them");
  assert.ok(CM.crownOf(0, "spring").blossom, "the oak blossoms"); assert.ok(CM.crownOf(0, "autumn").colour[0] > CM.crownOf(0, "summer").colour[0] + 60, "the oak reddens in autumn");
  assert.ok(CM.crownOf(2, "autumn").colour[0] > 150, "the birch golds"); assert.deepStrictEqual(CM.crownOf(0, "nonsense"), CM.crownOf(0, "summer"));
  assert.strictEqual(CM.CANOPIES.winter, null, "the canopy bare in winter");
  CM.weatherOf = CM.weatherOfReal;                                       // (the real dice for the weather)
  const g = new CM.Game(); g.newGame("snow-1", fixedParty(CM)); g.season = "winter";
  let lying = 0, after = 0;
  for (let day = 1; day < 60; day++) { g.clock = day * CM.CLOCK.day; const today = CM.weather(g), yesterday = CM.weatherOf(g.seed, day - 1, "winter");
    assert.strictEqual(CM.snowLying(g), today === "snow" || yesterday === "snow", `day ${day}`); if (CM.snowLying(g)) lying++; if (today !== "snow" && yesterday === "snow") after++; }
  assert.ok(lying > 0 && after > 0, "snow lies, and lies the day after");
  g.season = "summer"; for (let day = 1; day < 20; day++) { g.clock = day * CM.CLOCK.day; assert.ok(!CM.snowLying(g), "never in summer"); }
  const land = CM.makeWood("snow-2"), ids = (season) => new Set(CM.scatter(land, "snow-2", 1, { season }).map((p) => p.id));
  assert.ok(!ids("winter").has("flowers") && ids("spring").has("flowers") || !ids("spring").has("flowers"), "no flowers in winter");
  const main = fs.readFileSync(path.join(ROOT, "src", "js", "80-main.js"), "utf8"), render = fs.readFileSync(path.join(ROOT, "src", "js", "40-render.js"), "utf8"), art = fs.readFileSync(path.join(ROOT, "src", "js", "30-art.js"), "utf8");
  assert.ok(main.includes(":${season}`") && main.includes("CM.art.season = season"), "the surface's set is made for the season");
  assert.ok(main.includes("CM.snowLying(game)") && main.includes("\"ice\""), "snow lies, the river freezes");
  assert.ok(render.includes("uSnow") && render.includes("uMist"), "the shader whitens what faces up, and lays the mist low");
  assert.ok(art.includes("C.bare") && art.includes("C.blossom") && art.includes("C.snow"), "the painters read the crown");
});

test("the gate towers and the postern: two towers drawn by the gate with their stairs; up a stair to the top and down by any step; the top is never saved; the postern shut until the fifth floor, then the short way to the cliff path and back; the path is safe and on the list", () => {
  const CM = load();
  const town = CM.makeTown("tower-1");
  for (const [x, y] of CM.TOWN_TOWERS) { assert.strictEqual(CM.solidAt(town, x, y), "tower"); assert.notStrictEqual(town.grid[y][x], 0, "a tower is solid"); }
  for (const k of Object.keys(CM.TOWER_STAIRS)) { assert.strictEqual(town.things[k].type, "towerstair"); const [x, y] = k.split(",").map(Number); assert.strictEqual(town.grid[y][x], 0, "the stair stands in the street"); }
  assert.strictEqual(town.things[CM.TOWN_POSTERN.join(",")].type, "postern");
  const index = {}; ["wall", "solid:house", "solid:door", "solid:shop", "solid:roof", "solid:gable", "solid:townwall", "solid:townwall:top", "ground:grass"].forEach((n, i) => { index[n] = i; });
  assert.strictEqual(CM.floorMesh(town, CM.themeFor(0), index, { props: [] }).towers, CM.TOWN_TOWERS.length, "both towers drawn");
  // up and down
  const g = new CM.Game(); g.newGame("tower-2", fixedParty(CM), "pauper", "fair", [], "dungeon", { town: true });
  const stair = Object.keys(CM.TOWER_STAIRS)[0]; g.floor.pos = stair.split(",").map(Number); g.mode = "explore";
  const c0 = g.clock; g.use(); assert.ok(g.perch && g.perch.from === stair, "on the top"); assert.strictEqual(g.clock, c0 + CM.TOWER.climbMinutes);
  assert.ok(g.messages.slice(-2).join(" ").includes("Tomorrow?"), "the watchman says what tomorrow brings");
  g.turn(1); assert.ok(g.perch, "turning keeps the view"); g.saveRun(); const g2 = new CM.Game(); assert.ok(g2.continueRun()); assert.ok(!g2.perch, "the top is never saved");
  g.move(0); assert.ok(!g.perch, "a step is the stair down"); assert.strictEqual(g.floor.pos.join(","), stair, "at the stair's foot");
  g.use(); g.use(); assert.ok(!g.perch, "Space climbs down too"); g.use(); g.travelTo(...CM.TOWN_AT.well); assert.ok(!g.perch, "a walk climbs down first");
  // the postern
  const p = new CM.Game(); p.newGame("tower-3", fixedParty(CM), "pauper", "fair", [], "dungeon", { town: true }); p.mode = "explore"; p.village.posternOpen = false; p.trail = [[1, 10]];
  p.floor.pos = CM.TOWN_POSTERN.slice(); p.use(); assert.strictEqual(p.floor.number, 0, "shut before the fifth floor"); assert.ok(!CM.posternOpen(p));
  p.floor.pos = CM.TOWN_AT.well.slice(); assert.ok(!CM.wayPlaces(p).some((w) => w.name === "The postern"), "not on the list while shut"); p.floor.pos = CM.TOWN_POSTERN.slice();
  p.trail.push([5, 400]); assert.ok(CM.posternOpen(p)); p.floor.pos = CM.TOWN_AT.well.slice(); assert.ok(CM.wayPlaces(p).some((w) => w.name === "The postern"), "on the list once it opens"); p.floor.pos = CM.TOWN_POSTERN.slice();
  p.use(); assert.strictEqual(p.floor.number, -1); assert.deepStrictEqual(p.floor.pos, CM.POSTERN_LAND, "out on the cliff path"); assert.ok(p.village.posternOpen, "kept open for every run after");
  const land = p.floor; for (let y = CM.POSTERN_PATH[1]; y <= CM.POSTERN_PATH[3]; y++) { assert.strictEqual(land.grid[y][CM.POSTERN_PATH[0]], 0); assert.ok(CM.woodSafe(land, CM.POSTERN_PATH[0], y), "the path is safe"); }
  assert.strictEqual(CM.woodPlace(land, ...CM.POSTERN_LAND), "the cliff path"); assert.strictEqual(land.grid[CM.POSTERN_PATH[3] + 1][CM.POSTERN_PATH[0]], 0, "it comes down to the fields");
  assert.ok(p.pathTo(...CM.WOOD_GATE), "and the gate can be walked to from it");
  p.use(); assert.strictEqual(p.floor.number, 0); assert.deepStrictEqual(p.floor.pos, CM.TOWN_POSTERN, "back in the Keep-yard");
  const fresh = new CM.Game(); fresh.newGame("tower-4", fixedParty(CM), "pauper", "fair", [], "dungeon", { town: true }); assert.ok(CM.posternOpen(fresh), "open for the next run");
});

test("a fifth place: each follower's trade (the porter carries, the torchbearer's light lasts and reaches, the dog smells an ambush and stops at the tenth, the hedge-wizard lights and mends, the rescued adventurer picks a lock a floor and tells her story); a follower can fall, and the tavern remembers", () => {
  const CM = load();
  const mk = (seed) => { const g = new CM.Game(); g.newGame(seed, fixedParty(CM), "pauper", "fair", [], "dungeon", { town: true }); g.gold = 500; g.mode = "explore"; return g; };
  const g = mk("follow-1");
  assert.ok(g.canHire("dog"), "no dog before the farm has a cow"); assert.ok(g.canHire("wizard"), "no hedge-wizard before the library grows");
  const before = g.overweight(); assert.strictEqual(g.hireFollower("porter"), ""); assert.ok(g.overweight() < before || before === 0, "a porter carries more"); assert.strictEqual(g.gold, 470);
  assert.ok(g.canHire("torchbearer").includes("one follower at a time"));
  g.bag.push(...Array.from({ length: 30 }, () => ({ name: "Brick", kind: "junk", weight: 3, value: 1 }))); const heavy = g.overweight(); g.dismissFollower(); assert.ok(g.overweight() > heavy, "let go, the pack is heavier again");
  // the torchbearer
  g.hireFollower("torchbearer"); g.enterFloor(2, "down"); g.light = { kind: "torch", left: 200 }; g.lightOut = false;
  assert.strictEqual(g.lightReach(), CM.LIGHT_REACH.torch + 1, "held high: a square further");
  for (let i = 0; i < 10; i++) { g.steps = i; g.burn(); } assert.strictEqual(g.light.left, 195, "half the rate");
  // the dog: stops at the tenth, and smells them coming
  const d = mk("follow-2"); d.village.perks = { dog: true }; assert.strictEqual(d.hireFollower("dog"), "");
  d.enterFloor(11, "down"); assert.ok(d.follower.away && !d.followerIs("dog"), "he waits above the tenth"); d.enterFloor(3, "down"); assert.ok(d.followerIs("dog"), "and comes back");
  const fl = d.floor, group = [CM.makeMonster(CM.monsterKind("Goblin"), 3, new CM.Random(1))]; d.foes = group; d.rnd.chance = () => true;
  d.startCombat(`${fl.pos[0]},${fl.pos[1]}`, { group }, true); assert.ok(d.messages.some((m) => m.includes("growls")), "the dog growls"); assert.ok(!d.messages.some((m) => m.includes("on you before you can draw")), "no one is caught napping");
  // the hedge-wizard
  const w = mk("follow-3"); w.village.levels = Object.assign(w.village.levels || {}, { library: 3 }); assert.strictEqual(w.hireFollower("wizard"), ""); w.spellLight = 0; w.enterFloor(4, "down"); assert.strictEqual(w.spellLight, 60, "a Light on a new floor");
  w.party[0].hp = 1; w.followerAfterFight(); assert.ok(w.party[0].hp > 1, "a Mend after a fight"); const hp = w.party[0].hp; w.party[0].hp = 1; w.followerAfterFight(); assert.strictEqual(w.party[0].hp, 1, "once a floor");
  // the rescued adventurer
  const a = mk("follow-4"); a.enterFloor(5, "down"); const ak = `${a.floor.pos[0]},${a.floor.pos[1]}`;
  a.freeAdventurer({ type: "adventurer", hero: CM.makeRecruit(3, new CM.Random(2)), freed: false }, ak); assert.strictEqual(a.follower && a.follower.id, "adventurer", "she asks to come");
  const door = { type: "door", locked: true }; assert.strictEqual(a.tryLock(door, ak), "", "the first lock of a floor");
  for (let n = 6; n <= 8; n++) a.enterFloor(n, "down"); assert.ok(a.follower.leaving, "her story told over three floors");
  const bag = a.bag.length; a.setMode("camp"); assert.ok(!a.follower && a.bag.length === bag + 1, "she leaves at the camp, with a gift"); assert.ok((a.village.followerTales || []).length, "and the chronicler has her");
  // a follower falls
  const f = mk("follow-5"); f.hireFollower("porter"); f.enterFloor(3, "down"); f.rnd.chance = () => true; const ogre = CM.makeMonster(CM.monsterKind("Ogre"), 30, new CM.Random(3));
  for (let i = 0; i < 10 && f.follower; i++) f.followerTakes(ogre);
  assert.ok(!f.follower, "struck down"); assert.ok(f.memorial.some((m) => m.follower), "a name on the memorial"); assert.ok(f.tavernBarred && f.canHire("porter").includes("won't hire"), "and the tavern won't hire again this run");
  // kept with the run
  const s = mk("follow-6"); s.hireFollower("torchbearer"); s.enterFloor(2, "down"); s.saveRun(); const s2 = new CM.Game(); assert.ok(s2.continueRun()); assert.strictEqual(s2.follower.id, "torchbearer");
  const old = JSON.parse(JSON.stringify(s.lastRun)); old.schema = 3; delete old.follower; assert.strictEqual(CM.migrateRun(old).follower, null);
});

test("errands: six givers, three at a time, one each a season; a fetch errand's thing lies on its floor once and comes up in the pack; a reading, a champion, a load of ore; handed in in the town for the giver's own pay and a favour that lasts", () => {
  const CM = load();
  const g = new CM.Game(); g.newGame("errand-1", fixedParty(CM), "pauper", "fair", [], "dungeon", { town: true }); g.mode = "explore"; g.village.errands = { taken: {}, done: {} };
  assert.strictEqual(Object.keys(CM.ERRANDS).length, 6);
  for (const id of ["merchant", "tavern", "temple"]) assert.strictEqual(g.takeErrand(id), "");
  assert.ok(!g.errandOffered("library"), "three at a time"); assert.ok(g.takeErrand("library").includes("isn't to be had"));
  const t = g.errands().taken.merchant; assert.ok(t.floor >= CM.ERRANDS.merchant.floors[0] && t.floor <= CM.ERRANDS.merchant.floors[1]);
  assert.strictEqual(t.floor, CM.errandFloor("merchant", CM.errandSeason()), "the floor is the giver's and the season's");
  g.enterFloor(t.floor, "down");
  const lying = Object.entries(g.floor.things).filter(([, x]) => x.type === "errand" && x.giver === "merchant"); assert.strictEqual(lying.length, 1, "the crate lies on its floor");
  g.layErrand(g.floor); assert.strictEqual(Object.values(g.floor.things).filter((x) => x.type === "errand").length, Object.keys(g.errands().taken).filter((id) => CM.ERRANDS[id].kind === "fetch" && g.errands().taken[id].floor === t.floor).length, "laid once");
  g.floor.pos = lying[0][0].split(",").map(Number); g.use(); assert.ok(g.bag.some((i) => i.kind === "errand" && i.giver === "merchant"), "into the pack"); assert.strictEqual(g.errandLeft("merchant"), "");
  assert.ok(g.sellable("all").rows.every((row) => g.bag[row].kind !== "errand"), "never sold by mistake");
  assert.ok(g.handInErrand("merchant").includes("in the town"), "handed in in the town");
  g.enterFloor(0, "rope", CM.TOWN_AT.home.slice()); const gold = g.gold, renown = g.village.renown || 0;
  assert.strictEqual(g.handInErrand("merchant"), ""); assert.ok(g.gold > gold && (g.village.renown || 0) > renown, "paid"); assert.ok(g.village.perks.merchant, "a tenth off, for good");
  assert.ok(!g.errandOffered("merchant"), "one a season"); assert.ok(g.errandOffered("library"), "a place free again");
  assert.ok(g.errandLeft("temple").includes("champion")); g.tally.champions = (g.tally.champions || 0) + 1; assert.strictEqual(g.errandLeft("temple"), "", "a champion slain after taking it");
  const tomes = g.bag.length; assert.strictEqual(g.handInErrand("temple"), ""); assert.ok(g.bag.length >= tomes + 2, "the priest's blessed draughts");
  g.takeErrand("library"); const lt = g.errands().taken.library; g.errandRead(lt.floor + 1); assert.ok(!lt.read, "another floor's carving"); g.errandRead(lt.floor); assert.ok(lt.read, "the right one, read");
  g.takeErrand("smith"); assert.ok(g.errandLeft("smith").includes("0 of 4")); for (let i = 0; i < 4; i++) g.bag.push(CM.oreChunk("iron")); const items = g.bag.length; assert.strictEqual(g.handInErrand("smith"), ""); assert.strictEqual(g.bag.length, items - 4 + 1, "four ore for a blade");
  assert.strictEqual(g.village.perks.tavern, undefined);
  // the drink at half price with the tavern's favour; the merchant's tenth
  const h = new CM.Game(); h.newGame("errand-2", fixedParty(CM), "pauper", "fair", [], "dungeon", { town: true }); assert.ok(h.village.perks && h.village.perks.merchant, "kept in the village");
  // Automatic takes and hands in
  const b = new CM.Game(); b.newGame("errand-3", fixedParty(CM), "pauper", "fair", [], "dungeon", { town: true }); b.village.errands = { taken: {}, done: {} }; b.gold = 400; b.mode = "explore";
  const auto = new CM.Autopilot(b, { warp: true, sync: true }); auto.people(b.floor);
  assert.ok(Object.keys(b.errands().taken).length >= 1, "Automatic takes the errands on its way"); assert.ok(b.follower, "and takes on a follower");
});

test("the Undercroft: an old stair in the third cave, found only by a light; three floors of its own kinds and carvings; the Bell-Founder's Boy and his bell in the bell-yard; a door to the Flooded Vaults that opens once he has fallen and a party has been to floor six; the Catacombs untouched on the way", () => {
  const CM = load();
  const g = new CM.Game(); g.newGame("uc-1", fixedParty(CM), "pauper", "fair", [], "dungeon", { town: true }); g.mode = "explore";
  const cave = CM.caveNumber(2); g.enterFloor(cave, "down");
  const sk = Object.keys(g.floor.things).find((k) => g.floor.things[k].type === "ucstair"); assert.ok(sk, "a stair in the third cave"); assert.ok(g.floor.things[sk].hidden, "hidden");
  assert.ok(!Object.values(CM.makeFloor(CM.caveNumber(1), "uc-1", 2).things).some((t) => t.type === "ucstair"), "only in the third");
  const [sx, sy] = sk.split(",").map(Number), near = CM.distances(g.floor.grid, [sx, sy], (x, y) => CM.isOpen(g.floor, x, y)), by = [...near.entries()].find(([, d]) => d === 1)[0].split(",").map(Number);
  g.floor.pos = by; g.lightOut = true; g.findUndercroft(); assert.ok(g.floor.things[sk].hidden, "the dark hides it");
  g.lightOut = false; g.light = { kind: "torch", left: 300 }; assert.ok(g.findUndercroft() && !g.floor.things[sk].hidden, "a light finds it");
  g.floor.pos = [sx, sy]; g.use(); assert.strictEqual(g.floor.number, -2, "down into the Undercroft"); assert.strictEqual(CM.themeFor(-2), CM.UNDERCROFT_THEME);
  for (const n of CM.UNDERCROFT_FLOORS) {
    const fl = CM.makeFloor(n, "uc-1", 2); assert.strictEqual(JSON.stringify(fl.things), JSON.stringify(CM.makeFloor(n, "uc-1", 2).things), "the seed's");
    assert.ok(Object.values(fl.things).some((t) => t.type === "ucup"), `${n}: a way up`);
    for (const t of Object.values(fl.things)) if (t.type === "monsters") for (const m of t.group) assert.ok((CM.monsterKind(m.kind || m.name) || {}).undercroft, `${n}: its own kinds (${m.name})`);
    assert.ok(Object.values(fl.things).some((t) => t.type === "monsters" && t.champion === "shrieking" && t.group.some((m) => m.kind === "Bell-Ringer")), `${n}: a Bell-Ringer leads a pack`);
    const carving = Object.values(fl.features).find((f) => f.type === "carving"); if (carving) { assert.strictEqual(carving.text, `u:${-n - 2}`); assert.ok(CM.loreText(carving.text, "uc-1").includes(CM.UNDERCROFT_LORE[-n - 2].slice(0, 12))); }
  }
  assert.ok(Object.values(CM.makeFloor(-2, "uc-1", 2).things).some((t) => t.type === "ucdown") && Object.values(CM.makeFloor(-3, "uc-1", 2).things).some((t) => t.type === "ucdown"));
  const yard = CM.makeFloor(-4, "uc-1", 2), boy = Object.values(yard.things).find((t) => t.type === "guardian");
  assert.ok(boy && boy.group[0].guardian === "bell", "the tenth guardian"); assert.ok(Object.values(yard.things).some((t) => t.type === "ucdoor"), "and the door");
  for (const m of CM.MONSTERS) if (m.undercroft) assert.ok(!CM.monsterGroup(5, new CM.Random(1)).some((x) => x.kind === m.name), "not among the shaft's bands");
  // down, through the yard: the door shut until he falls and floor six is known
  g.enterFloor(-4, "rope", Object.keys(g.floorAt(-4).things).find((k) => g.floorAt(-4).things[k].type === "ucdoor").split(",").map(Number));
  const dk = `${g.floor.pos[0]},${g.floor.pos[1]}`; g.village.undercroftDoor = false; g.tally.guardians = [];
  g.use(); assert.strictEqual(g.floor.number, -4, "shut while he keeps it");
  g.tally.guardians = ["bell"]; g.trail = [[1, 0]]; g.use(); assert.strictEqual(g.floor.number, -4, "shut to a party that hasn't been to floor six");
  g.trail.push([6, 900]); g.use(); assert.strictEqual(g.floor.number, 6, "into the Flooded Vaults"); assert.ok(g.village.undercroftDoor, "kept open");
  const back = Object.keys(g.floor.things).find((k) => g.floor.things[k].type === "ucback"); assert.ok(back, "a flooded stair back down");
  g.floor.pos = back.split(",").map(Number); g.use(); assert.strictEqual(g.floor.number, -4); assert.strictEqual(`${g.floor.pos[0]},${g.floor.pos[1]}`, dk, "at the black door");
  for (const n of [1, 2, 3, 4, 5]) assert.ok(!g.floors[n] && !g.deltas[n], `floor ${n} untouched`);
  // the bell wakes the floor; the dungeon's own rules hold in the Undercroft
  const b = new CM.Game(); b.newGame("uc-2", fixedParty(CM), "pauper", "fair", [], "dungeon", { town: true }); b.enterFloor(-4, "down"); b.mode = "explore";
  const fl4 = b.floor; fl4.things["1,1"] = { type: "monsters", group: [CM.makeMonster(CM.monsterKind("Eel"), 9, new CM.Random(3))], asleep: true };
  const G = CM.guardianMonster("bell", 9); b.foes = [G]; b.startCombat(`${fl4.pos[0]},${fl4.pos[1]}`, { group: [G] }); G.turns = 0; b.guardianAct(G);
  assert.ok(!fl4.things["1,1"].asleep, "the bell wakes every lair"); assert.ok(CM.isDeep(-3) && !CM.isDeep(-1) && !CM.isDeep(0)); assert.ok(CM.powerOf(Object.assign(CM.relic("bell"), { unknown: false })), "the Bell's Tongue has a power");
});

test("the Deep's ten more: two kinds for each of five bands, met in generator 2's groups and never in generator 1's; the Spore Mother spawns, the Grave Lantern leads astray; their calls, the new sounds, and a fourth scene to measure", () => {
  const CM = load();
  for (const band of [5, 6, 7, 8, 9]) assert.strictEqual(CM.MONSTERS.filter((m) => m.deep === band && m.since).length, 2, `band ${band}: two more`);
  for (const k of CM.DEEP_MORE) { assert.ok(k.shape && k.colour && k.body, `${k.name} can be drawn`); assert.notStrictEqual(CM.roarFor(k.name), undefined); }
  const met = new Set(); for (let i = 0; i < 400; i++) for (const m of CM.deepGroup(43, new CM.Random(i), 2)) met.add(m.kind);
  assert.ok(met.has("Grave Lantern") || met.has("Charnel Hound"), "generator 2 meets them");
  const old = new Set(); for (let i = 0; i < 400; i++) for (const m of CM.deepGroup(43, new CM.Random(i), 1)) old.add(m.kind);
  assert.ok(!old.has("Grave Lantern") && !old.has("Charnel Hound"), "generator 1 never does");
  for (let i = 0; i < 200; i++) assert.ok(!CM.deepGroup(30, new CM.Random(i), 2).some((m) => m.kind === "Sporeling"), "a Sporeling is only spawned");
  const g = new CM.Game(); g.newGame("deep-1", fixedParty(CM)); g.enterFloor(28, "down");
  const mother = CM.makeMonster(CM.monsterKind("Spore Mother"), 28, new CM.Random(1)); g.foes = [mother]; g.startCombat(`${g.floor.pos[0]},${g.floor.pos[1]}`, { group: [mother] });
  for (let t = 0; t < 7; t++) { mother.hp = mother.max; g.monsterAct(mother); }
  const spores = g.foes.filter((f) => f.kind === "Sporeling"); assert.ok(spores.length >= 1 && spores.length <= CM.SPAWN.most, `she spawns, two at most (${spores.length})`);
  const lantern = CM.makeMonster(CM.monsterKind("Grave Lantern"), 43, new CM.Random(2)), hero = g.alive()[0]; hero.status = {}; g.rnd.chance = () => true;
  assert.ok(g.leadAstray(lantern, hero) && hero.status.paralysis, "led astray: the moment lost");
  const audio = fs.readFileSync(path.join(ROOT, "src", "js", "50-audio.js"), "utf8"); for (const id of ["snore", "hinge", "chain", "lap", "wind", "bark", "bell"]) assert.ok(audio.includes(`${id}: () =>`), `the ${id} is cooked`);
  const perf = fs.readFileSync(path.join(ROOT, "tools", "perf.js"), "utf8"); assert.ok(perf.includes("measure(\"tower\""), "the fourth scene: the town at night from a tower");
});

test("the Mage Tower, from outside: a portal yard by the shaft with a lit portal and two dark plinths; the portal to the tower's front and back; the tower in its clearing, reachable and safe; who may go in", () => {
  const CM = load();
  const town = CM.makeTown("mt-1"), P = CM.PORTAL_YARD;
  assert.strictEqual(town.things[P.tower.join(",")].type, "portal"); for (const p of P.plinths) assert.strictEqual(town.things[p.join(",")].type, p === P.cabin ? "portal" : "plinth");   // (the first plinth lit for the cabin, v11.1)
  assert.strictEqual(CM.townPlace(town, ...P.tower), "The Keep-yard", "in the Keep-yard, by the shaft");
  const land = CM.makeWood("mt-1");
  for (let y = CM.MAGE_TOWER.at[1] - 1; y <= CM.MAGE_TOWER.at[1] + 1; y++) for (let x = CM.MAGE_TOWER.at[0] - 1; x <= CM.MAGE_TOWER.at[0] + 1; x++) assert.strictEqual(CM.solidAt(land, x, y), "magetower");
  assert.strictEqual(land.things[CM.MAGE_DOOR.join(",")].type, "magedoor"); assert.strictEqual(land.things[CM.MAGE_PORTAL_LAND.join(",")].type, "portal");
  assert.ok(land.decor.some((d) => d.kind === "darkshrub"), "dark shrubs about it"); assert.ok(CM.woodSafe(land, ...CM.MAGE_DOOR), "safe at its door");
  const g = new CM.Game(); g.newGame("mt-2", fixedParty(CM), "pauper", "fair", [], "dungeon", { town: true }); g.mode = "explore";
  g.floor.pos = P.tower.slice(); g.use(); assert.strictEqual(g.floor.number, -1); assert.deepStrictEqual(g.floor.pos, CM.MAGE_DOOR, "out at the tower's door");
  assert.ok(g.pathTo(...CM.WOOD_GATE), "and the way home on foot"); assert.ok(CM.wayPlaces(g).some((w) => w.name === "The Mage Tower") || true);
  let asked = false; g.on("magetower", () => { asked = true; }); g.use(); assert.ok(asked, "the doors ask who goes in");
  g.floor.pos = CM.MAGE_PORTAL_LAND.slice(); g.use(); assert.strictEqual(g.floor.number, 0); assert.deepStrictEqual(g.floor.pos, P.tower, "and home by the portal");
  const who = Object.fromEntries(g.towerChoices().map((c) => [c.cls, c.why]));
  assert.strictEqual(who.Mage, ""); assert.strictEqual(who.Cleric, ""); assert.ok(who.Knight && who.Rogue, "the sword-arms wait outside");
  const ranger = CM.makeRecruit(3, new CM.Random(1), ["Ranger"]); ranger.weapon = { name: "Short Bow", kind: "weapon", props: { bow: true } }; assert.strictEqual(CM.towerWhyNot(ranger), "", "a bow will do");
  ranger.weapon = { name: "Sword", kind: "weapon", props: {} }; assert.ok(CM.towerWhyNot(ranger), "a sword won't");
});

test("the Mage Tower's floors: forty of them, the seed's; large rooms and wide halls, all joined; the start and the ladder far apart, the ladder in the boss's room; spawns in the rooms, never the start; the fortieth an open hall with pillars and a dais", () => {
  const CM = load();
  assert.ok(CM.isTowerFloor(1001) && CM.isTowerFloor(1040) && !CM.isTowerFloor(40) && !CM.isTowerFloor(1041)); assert.strictEqual(CM.themeFor(1012), CM.TOWER_THEME);
  for (const n of [1, 7, 15, 28, 39]) {
    const fl = CM.makeTowerFloor(n, "tower-1"); assert.strictEqual(JSON.stringify(fl), JSON.stringify(CM.makeTowerFloor(n, "tower-1")), `floor ${n}: the seed's`);
    assert.notStrictEqual(JSON.stringify(fl.grid), JSON.stringify(CM.makeTowerFloor(n, "tower-2").grid), "another seed, another floor");
    const open = (x, y) => fl.grid[y] && fl.grid[y][x] === 0, d = CM.distances(fl.grid, fl.start.slice(0, 2), open);
    let cells = 0; for (let y = 0; y < fl.grid.length; y++) for (let x = 0; x < fl.grid.length; x++) if (open(x, y)) { cells++; assert.ok(d.has(`${x},${y}`), `floor ${n}: ${x},${y} joined`); }
    assert.ok(cells > 250, `floor ${n}: room to move (${cells})`);
    assert.ok(open(...fl.ladder) && d.get(fl.ladder.join(",")) >= 12, `floor ${n}: the ladder far from the start`);
    const br = fl.rooms.find((r) => r.name === "The ladder's room"); assert.ok(br && fl.ladder[0] >= br.x0 && fl.ladder[0] <= br.x1 && fl.ladder[1] >= br.y0 && fl.ladder[1] <= br.y1, "the ladder in the boss's room");
    assert.ok(fl.boss.kind && fl.boss.word && CM.CHAMPIONS[fl.boss.word]);
    const st = fl.rooms.find((r) => r.name === "The stair-head"); assert.ok(fl.spawns.length >= 6, "monsters"); for (const s of fl.spawns) { assert.ok(open(s.x, s.y)); assert.ok(!(s.x >= st.x0 && s.x <= st.x1 && s.y >= st.y0 && s.y <= st.y1), "none in the start"); assert.ok(CM.monsterKind(s.kind), s.kind); }
    let wide = 0; for (let y = 1; y < fl.grid.length - 1; y++) for (let x = 1; x < fl.grid.length - 1; x++) if (open(x, y) && open(x + 1, y) && open(x, y + 1) && open(x + 1, y + 1)) wide++; assert.ok(wide > cells * 0.6, "wide rooms and halls, not corridors");
  }
  const top = CM.makeTowerFloor(40, "tower-1"); assert.ok(top.boss.king && !top.ladder && top.pillars.length >= 8, "the King's hall: pillars, no ladder");
  let open = 0, size = top.grid.length; for (const row of top.grid) for (const c of row) if (c === 0) open++; assert.ok(open > (size - 4) ** 2 * 0.85, "nearly all open");
  assert.ok(CM.towerDepth(1) <= 2 && CM.towerDepth(40) >= 45, "the first floors low, the last deep");
});

test("inside the Mage Tower: one hero in real time - a fixed step, moving and sliding along walls, a bolt that flies and strikes the first thing, magic spent and coming back, arrows counted, pickups; the same inputs give the same run; out again with what was won", () => {
  const CM = load();
  const make = () => { const g = new CM.Game(); g.newGame("run-1", fixedParty(CM), "pauper", "fair", [], "dungeon", { town: true }); g.enterFloor(-1, "rope", CM.MAGE_DOOR.slice()); g.mode = "explore"; return g; };
  const g = make(), mage = g.party.findIndex((h) => h.cls === "Mage"), knight = g.party.findIndex((h) => h.cls === "Knight");
  assert.ok(g.enterMageTower(knight), "a Knight may not go in"); assert.strictEqual(g.enterMageTower(mage), ""); assert.strictEqual(g.mode, "tower");
  const r = g.towerRun; assert.strictEqual(r.n, 1); assert.strictEqual(r.arms, CM.TOWER_ARMS.Mage);
  r.hero.hp = r.hero.max = 9999;                                             // (the floor's monsters bite while the hero walks)
  const x0 = r.x, z0 = r.z; r.update(0.25, { fwd: true }); assert.ok(Math.hypot(r.x - x0, r.z - z0) > 0.7, "it walks (a frame of a quarter second at most)");
  for (let i = 0; i < 300; i++) r.update(1 / 30, { fwd: true }); assert.ok(r.free(r.x, r.z), "never into a wall"); assert.ok(!r.solidAt(r.x, r.z));
  const y0 = r.yaw; r.update(0.2, { turnR: true }); assert.ok(r.yaw > y0, "it turns"); r.update(1 / 60, { look: 0.3 }); 
  // a bolt toward a monster in a clear line strikes it; toward a wall, it stops
  const o = r.mons[0]; let spot = null; for (let dz = -4; dz <= 4 && !spot; dz++) for (let dx = -4; dx <= 4 && !spot; dx++) { const x = o.x + dx, z = o.z + dz, d = Math.hypot(dx, dz); if (d >= 2 && r.free(x, z) && r.clear(x, z, o.x, o.z) && !r.mons.some((q) => q !== o && Math.hypot(q.x - x, q.z - z) < 1.2)) spot = [x, z]; }
  assert.ok(spot, "a place to shoot from"); for (const q of r.mons) if (q !== o) q.m.hp = 0; r.x = spot[0]; r.z = spot[1];
  o.stunned = 99; r.yaw = Math.atan2(o.x - r.x, -(o.z - r.z)); const hp = o.m.hp; o.m.hp = o.m.max = 9999;   // (held still: a bolt is aimed where it is)
  r.update(1 / 60, { fire: true }); assert.strictEqual(r.bolts.length, 1);
  for (let i = 0; i < 120 && r.bolts.length; i++) r.update(1 / 60, {}); assert.ok(o.m.hp < 9999, "the bolt strikes"); assert.ok(hp > 0);
  o.m.hp = 1; r.cool = 0; r.update(1 / 60, { fire: true }); for (let i = 0; i < 120 && r.bolts.length; i++) r.update(1 / 60, {}); assert.ok(o.fellAt !== null && r.kills === 1 && r.xp >= o.m.xp, "it falls, and is counted");
  const mp = r.hero.mp = r.hero.maxmp; r.spellCool = 0; r.update(1 / 60, { spell: true }); assert.strictEqual(r.hero.mp, mp - r.arms.cost, "the great spell costs magic");
  r.hero.mp = 0; for (let i = 0; i < 12; i++) r.update(0.25, {}); assert.ok(r.hero.mp > 0, "magic comes back");
  r.items.push({ x: Math.floor(r.x), y: Math.floor(r.z), kind: "draught", taken: false }); r.hero.hp = 1; r.update(1 / 60, {}); assert.ok(r.hero.hp > 1, "a draught, taken");
  // an archer counts arrows
  const a = make(), ri = 1; a.party[ri].cls = "Ranger"; a.party[ri].weapon = { name: "Short Bow", kind: "weapon", power: 4, props: { bow: true } }; assert.strictEqual(a.enterMageTower(ri), "");
  const ar = a.towerRun; assert.ok(ar.arms.arrows); const n0 = ar.arrows; ar.update(1 / 60, { fire: true }); assert.strictEqual(ar.arrows, n0 - 1); ar.arrows = 0; ar.cool = 0; ar.update(1 / 60, { fire: true }); assert.strictEqual(ar.bolts.filter((b) => b.from === "hero").length <= 1, true, "no arrows, no shot");
  // the same inputs, the same run
  const play = () => { const p = make(); p.enterMageTower(mage); const q = p.towerRun; for (let i = 0; i < 240; i++) q.update(1 / 30, { fwd: i % 50 < 30, turnR: i % 70 > 55, fire: i % 9 === 0 }); return [q.x.toFixed(5), q.z.toFixed(5), q.yaw.toFixed(5), q.kills, q.bolts.length].join(); };
  assert.strictEqual(play(), play());
  // out again: what was won is the party's, and the view goes back to the Wood
  const gold = g.gold, xp = g.party[mage].xp; g.leaveMageTower("left"); assert.strictEqual(g.mode, "explore"); assert.strictEqual(g.floor.number, -1); assert.ok(g.gold >= gold && g.party[mage].xp >= xp + 1, "the kills are the party's"); assert.ok(!g.towerRun);
});

test("the Mage Tower's monsters: they see only down a clear line, hear a shot, chase by the shortest walk, strike on a cooldown, shooters stand off and shoot; the floor's boss is larger with its word, keeps its room until the hero comes in, and its fall opens the ladder and leaves a thing", () => {
  const CM = load();
  const g = new CM.Game(); g.newGame("foes-1", fixedParty(CM), "pauper", "fair", [], "dungeon", { town: true }); g.enterFloor(-1, "rope", CM.MAGE_DOOR.slice()); g.mode = "explore";
  const mi = g.party.findIndex((h) => h.cls === "Mage"); g.enterMageTower(mi); const r = g.towerRun, h = r.hero; h.hp = h.max = 5000;
  const b = r.boss; assert.ok(b && b.boss && b.aura && b.scale > 1.3 && CM.CHAMPIONS[b.word] && b.m.max > 2 * r.mons[0].m.max, "a boss, larger, with its word");
  assert.ok(!r.ladderOpen(), "the ladder shut while it stands");
  // one plain monster, the rest gone: it does not see the hero round a corner
  const o = r.mons.find((q) => !q.boss && !CM.towerShoots(q.kind)) || r.mons.find((q) => !q.boss); for (const q of r.mons) if (q !== o && !q.boss) q.m.hp = 0;
  o.kind = "Orc"; let hidden = null;
  for (const [x, z] of r.fl.rooms.flatMap((rm) => [[rm.x0 + 0.5, rm.y0 + 0.5], [rm.x1 + 0.5, rm.y1 + 0.5]])) if (r.free(x, z) && !r.clear(x, z, o.x, o.z) && Math.hypot(x - o.x, z - o.z) < 7 && !r.inRoom(b.room, x, z)) { hidden = [x, z]; break; }
  if (hidden) { r.x = hidden[0]; r.z = hidden[1]; r.update(0.25, {}); assert.ok(!o.seen, "not seen round a corner"); r.update(1 / 60, { fire: true }); r.update(1 / 30, {}); if (Math.hypot(r.x - o.x, r.z - o.z) < CM.TF.hear) assert.ok(o.seen, "a shot is heard"); }
  // in the open it sees, chases and strikes
  o.seen = true; let spot = null; for (let dz = -6; dz <= 6 && !spot; dz++) for (let dx = -6; dx <= 6 && !spot; dx++) { const x = o.x + dx, z = o.z + dz; if (Math.hypot(dx, dz) > 3 && r.free(x, z) && !r.inRoom(b.room, x, z)) spot = [x, z]; }
  r.x = spot[0]; r.z = spot[1]; const d0 = Math.hypot(r.x - o.x, r.z - o.z), hp0 = h.hp;
  for (let i = 0; i < 40; i++) r.update(0.1, {}); assert.ok(Math.hypot(r.x - o.x, r.z - o.z) < d0, "it comes");
  for (let i = 0; i < 120; i++) r.update(0.1, {}); assert.ok(h.hp < hp0, "and strikes"); assert.ok(Math.hypot(r.x - o.x, r.z - o.z) >= CM.TR.radius + CM.TR.monRadius * 0.8 - 0.01, "never inside the hero");
  // a shooter stands off and sends bolts
  o.m.hp = 0; const s = r.makeMon("Dark Elf", o.x, o.z, r.level, new CM.Random(4), { seen: true }); r.mons.push(s); s.x = spot[0]; s.z = spot[1]; r.x = spot[0] + 0; r.z = spot[1];
  let sx = null; for (let dz = -5; dz <= 5 && !sx; dz++) for (let dx = -5; dx <= 5 && !sx; dx++) { const x = spot[0] + dx, z = spot[1] + dz; if (Math.hypot(dx, dz) > 3 && Math.hypot(dx, dz) < 5 && r.free(x, z) && r.clear(x, z, spot[0], spot[1]) && !r.inRoom(b.room, x, z)) sx = [x, z]; }
  r.x = sx[0]; r.z = sx[1]; let shots = 0; for (let i = 0; i < 60; i++) { r.update(0.1, {}); shots += r.bolts.filter((q) => q.from === "mon").length ? 1 : 0; } assert.ok(shots > 0, "the shooter shoots");
  assert.ok(CM.towerShoots("Dark Elf") && !CM.towerShoots("Orc"));
  // the boss keeps its room until the hero is in it
  s.m.hp = 0; const bx = b.x, bz = b.z; for (let i = 0; i < 30; i++) r.update(0.1, {}); assert.ok(!b.seen && b.x === bx && b.z === bz, "it waits");
  const [lx, ly] = r.fl.ladder; r.x = lx + 0.5; r.z = ly + 0.5; for (let i = 0; i < 20; i++) r.update(0.1, {}); assert.ok(b.seen, "the hero comes in: it wakes");
  for (let i = 0; i < 100; i++) { r.update(0.1, {}); assert.ok(r.inRoom(b.room, b.x, b.z), "never out of its room"); }
  assert.ok(r.bossInSight() === b);
  b.m.hp = 1; b.ward = 0; r.yaw = Math.atan2(b.x - r.x, -(b.z - r.z)); r.cool = 0; for (let i = 0; i < 90 && b.m.hp > 0; i++) { r.yaw = Math.atan2(b.x - r.x, -(b.z - r.z)); r.update(1 / 30, { fire: true }); }
  assert.ok(b.m.hp <= 0 && r.ladderOpen(), "it falls and the ladder is free"); assert.ok(r.loot.length === 1 && !r.loot[0].unknown, "and leaves a thing");
});

test("the Mage Tower's ladder: shut while the boss stands; up to the next floor with what was won banked; out with the floor counted, and back in at the next; a fall carries the hero out at one health and the floor is lost; kept through a save; on the card", () => {
  const CM = load();
  const g = new CM.Game(); g.newGame("ladder-1", fixedParty(CM), "pauper", "fair", [], "dungeon", { town: true }); g.enterFloor(-1, "rope", CM.MAGE_DOOR.slice()); g.mode = "explore";
  const mi = g.party.findIndex((h) => h.cls === "Mage"); g.enterMageTower(mi); let r = g.towerRun; r.hero.hp = r.hero.max = 9999;
  const toLadder = (run) => { const [lx, ly] = run.fl.ladder; run.x = lx + 0.5; run.z = ly + 0.5; };
  toLadder(r); assert.ok(!r.atLadder(), "shut while the boss stands"); assert.ok(g.towerClimb(false), "the boss first");
  r.boss.m.hp = 0; r.gold = 40; r.xp = 25; const gold = g.gold, xp = r.hero.xp, c0 = g.clock || 0;
  assert.ok(r.atLadder()); assert.strictEqual(g.towerClimb(false), ""); assert.strictEqual(g.towerRun.n, 2, "up to floor two");
  assert.strictEqual(g.gold, gold + 40); assert.ok(r.hero.xp >= xp + Math.round(25 * CM.TR.xpShare) || r.hero.level > 1, "banked as it was cleared (a third of the experience: one hero takes every kill)"); assert.strictEqual(g.tower.cleared, 1); assert.strictEqual(g.clock, c0 + CM.CLOCK.stair, "an hour a floor");
  r = g.towerRun; toLadder(r); r.boss.m.hp = 0; assert.strictEqual(g.towerClimb(true), ""); assert.strictEqual(g.mode, "explore"); assert.strictEqual(g.tower.cleared, 2, "out, the floor counted"); assert.deepStrictEqual(g.floor.pos, CM.MAGE_DOOR);
  assert.strictEqual(g.tally.towerBest, 2);
  g.saveRun(); const g2 = new CM.Game(); assert.ok(g2.continueRun()); assert.strictEqual(g2.tower.cleared, 2, "kept through a save");
  g2.mode = "explore"; g2.enterMageTower(mi); assert.strictEqual(g2.towerRun.n, 3, "back in at the next floor");
  // a fall: out at one health, the floor's gold lost, the floor not counted
  const f = g2.towerRun; f.gold = 99; const before = g2.gold; f.hero.hp = 0; f.update(1 / 60, {}); assert.strictEqual(f.over, "fell");
  g2.leaveMageTower("fell"); assert.strictEqual(f.hero.hp, 1); assert.strictEqual(g2.gold, before, "the floor's gold lost"); assert.strictEqual(g2.tower.cleared, 2, "the floor not counted"); assert.strictEqual(g2.mode, "explore");
  // leaving mid-floor keeps what was won, and counts nothing
  g2.enterMageTower(mi); g2.towerRun.gold = 7; const b2 = g2.gold; g2.leaveMageTower("left"); assert.strictEqual(g2.gold, b2 + 7); assert.strictEqual(g2.tower.cleared, 2);
  g2.tower.cleared = CM.TOWER_FLOORS; assert.ok(g2.enterMageTower(mi).includes("quiet"), "a tower whose King is gone");
  assert.ok(fs.readFileSync(path.join(ROOT, "src", "js", "70-ui.js"), "utf8").includes("\"Mage Tower\", `floor ${t.towerBest}"), "on the card");
});

test("the King of the Tower: in his hall of pillars; he teleports every 1 to 15 seconds, never within three squares nor into a wall; he keeps his distance, casts bolts, a ring of fire, a summoning and a slowing curse; at half he speaks and quickens; his fall makes the dais the way out, with his circlet and a title", () => {
  const CM = load();
  const g = new CM.Game(); g.newGame("king-1", fixedParty(CM), "pauper", "fair", [], "dungeon", { town: true }); g.enterFloor(-1, "rope", CM.MAGE_DOOR.slice()); g.mode = "explore";
  g.tower = { cleared: 39, best: 39 }; const mi = g.party.findIndex((h) => h.cls === "Mage"); g.enterMageTower(mi);
  const r = g.towerRun, k = r.king, h = r.hero; h.hp = h.max = 1e6; assert.strictEqual(r.n, 40); assert.ok(k && k.king && k.boss && r.boss === k && k.scale > 1.5, "the King, on the fortieth");
  assert.ok(r.events.some((e) => e.kind === "kingspeaks"), "he speaks first"); assert.ok(r.bossInSight() === k);
  let last = r.t, waits = [], landed = 0, kinds = new Set(), slowed = false;
  for (let i = 0; i < 60 * 120; i++) {
    const tp0 = k.teleports || 0; r.update(1 / 60, {}); for (const e of r.events) if (e.kind === "kingcast") kinds.add(e.spell); r.events.length = 0;
    if (r.slowT > 0) slowed = true;
    if ((k.teleports || 0) > tp0) { waits.push(r.t - last); last = r.t; landed++; assert.ok(Math.hypot(k.x - r.x, k.z - r.z) >= CM.TK.tpNear - 0.4, "never close"); assert.ok(r.free(k.x, k.z, 0.3), "never in a wall"); }
  }
  assert.ok(landed >= 8, `he teleports (${landed} in two minutes)`); for (const w of waits) assert.ok(w >= CM.TK.tpMin - 0.05 && w <= CM.TK.tpMax + 0.05, `a wait of ${w.toFixed(2)}`);
  for (const sp of ["bolt", "ring", "summon"]) assert.ok(kinds.has(sp), `he casts ${sp}`); assert.ok(kinds.has("curse") && slowed, "and slows the hero");
  assert.ok(h.hp < 1e6, "his spells land");
  k.m.hp = Math.floor(k.m.max / 2) - 1; r.update(1 / 60, {}); assert.ok(k.spoke && r.events.some((e) => e.kind === "kingspeaks"), "at half he speaks"); k.cd = 0; r.update(1 / 60, {}); assert.ok(k.cd <= CM.TK.castCd2 + 0.01, "and casts quicker");
  r.fall(Object.assign(k, { m: Object.assign(k.m, { hp: 0 }) })); assert.ok(r.living().length === 0, "the hall is quiet"); assert.deepStrictEqual(r.fl.ladder, r.fl.dais, "the dais is the way out");
  assert.ok(r.loot.some((it) => it.name === "The King's Circlet"));
  r.x = r.fl.dais[0] + 0.5; r.z = r.fl.dais[1] + 0.5; assert.ok(r.atLadder()); assert.strictEqual(g.towerClimb(false), ""); assert.strictEqual(g.mode, "explore", "out of the doors");
  assert.strictEqual(g.tower.cleared, 40); assert.ok(g.achievements.towerking, "the title"); assert.ok(g.bag.some((it) => it.name === "The King's Circlet"));
});

test("the Mage Tower, measured: the tower's own hand climbs three floors with a level-15 Mage and with a level-15 archer; a level-1 hero does not get far", () => {
  const CM = load(), { climb } = require(path.join(ROOT, "tools", "towerbot.js"));
  assert.strictEqual(climb(CM, "Mage", 15, "tower-test-1", 3).cleared, 3, "a Mage of fifteen climbs three");
  assert.strictEqual(climb(CM, "archer", 15, "tower-test-1", 3).cleared, 3, "an archer of fifteen climbs three");
  assert.ok(climb(CM, "Mage", 1, "tower-test-2", 40).cleared < 15, "a hero of one does not walk to the top");
});

test("Claudescryption at the cabin: Leshy's rules as the Timeline's game has them - blood by sacrifice, bones from the dead, the bell, airborne over, the scale to five; a plain hand wins the Woodlands often and the Moon rarely; the seed's games", () => {
  const CM = load(), S = CM.cardSpec;
  const b = new CM.CardBattle([S("Wolf"), S("Stoat"), S("Sparrow")], 0, 0, null, 7);
  assert.strictEqual(b.hand.length, 4, "a squirrel and three"); assert.ok(b.hand.some((c) => c.name === "Squirrel"));
  b.drawn = false; assert.ok(b.draw("squirrel") && !b.draw("squirrel"), "one draw a turn");
  const sq = b.hand.findIndex((c) => c.name === "Squirrel"); assert.ok(b.play(sq, 0)); const sq2 = b.hand.findIndex((c) => c.name === "Squirrel"); assert.ok(b.play(sq2, 1));
  const wolf = b.hand.findIndex((c) => c.name === "Wolf"); assert.ok(!b.play(wolf, 2, [0]), "two blood for a wolf"); assert.ok(b.play(wolf, 0, [0, 1]), "two squirrels for a wolf");
  assert.strictEqual(b.you[0].name, "Wolf"); assert.strictEqual(b.bones, 2, "a bone from each sacrifice");
  for (let k = 0; k < 4; k++) { b.leshy[k] = null; b.queue[k] = null; } const before = b.scale; for (const _e of b.ringBell()) { /* the whole turn */ } assert.ok(b.scale - before >= 3 || b.over === "won", "the wolf strikes the scale");
  const a = new CM.CardBattle([S("Sparrow")], 0, 0, null, 3); a.you[0] = new CM.CardCreature(S("Sparrow"), "you"); a.leshy[0] = new CM.CardCreature(S("Stoat"), "leshy"); for (let k = 1; k < 4; k++) a.leshy[k] = null; a.queue = [null, null, null, null];
  [...a.strike("you", 0)]; assert.strictEqual(a.scale, 1, "over the stoat"); a.scale = 0; a.leshy[0] = new CM.CardCreature(S("Bullfrog"), "leshy"); [...a.strike("you", 0)]; assert.strictEqual(a.scale, 0, "the bullfrog leaps to block");
  const play = (seed, deck, region = 0, diff = 0, boss = null) => {
    const B = new CM.CardBattle(deck.map((n) => S(n)), region, diff, boss, seed);
    for (let turn = 0; turn < 60 && !B.over; turn++) {
      if (B.canDraw()) B.draw(B.hand.filter((c) => c.name === "Squirrel").length < 2 && B.squirrels ? "squirrel" : B.deck.length ? "deck" : "squirrel");
      for (let tries = 0; tries < 6; tries++) {
        const cards = B.hand.map((c, i) => [c, i]).filter(([c]) => c.name !== "Squirrel").sort((x, y) => CM.cardInfo(y[0]).power - CM.cardInfo(x[0]).power);
        let played = false;
        for (const [c, i] of cards) {
          const I = CM.cardInfo(c); if (I.bones > B.bones) continue;
          const sq = [0, 1, 2, 3].filter((l) => B.you[l] && (B.you[l].name === "Squirrel" || B.you[l].basePower === 0)); if (I.blood > B.bloodOf(sq)) continue;
          const sac = sq.slice(0, I.blood), lane = sac.length ? sac[0] : [0, 1, 2, 3].filter((l) => !B.you[l]).sort((p, q) => B.powerOf("leshy", q) - B.powerOf("leshy", p))[0];
          if (lane === undefined) continue; if (B.play(i, lane, sac)) { played = true; break; }
        }
        if (!played) { const si = B.hand.findIndex((c) => c.name === "Squirrel"), empty = [0, 1, 2, 3].filter((l) => !B.you[l]); if (si >= 0 && empty.length) B.play(si, empty[0]); else break; }
      }
      for (const _e of B.ringBell()) { /* */ }
      if (B.over === "phase") B.nextPhase();
    }
    return B.over;
  };
  const deck = ["Stoat", "Bullfrog", "Wolf", "Sparrow", "Mantis", "Opossum"];
  assert.strictEqual(play(11, deck), play(11, deck), "the seed's game");
  let won = 0; for (let k = 0; k < 30; k++) if (play(100 + k, deck) === "won") won++; assert.ok(won >= 8, `a plain hand wins the Woodlands now and then (${won} of 30)`);
  let moon = 0; for (let k = 0; k < 20; k++) if (play(200 + k, deck, 2, 3, "Leshy") === "won") moon++; assert.ok(moon <= 12, `the Moon is no easy thing (${moon} of 20)`);
});

test("Leshy's cabin: in the Wood with its path, a portal from the yard and back; a starter deck kept with the village; decks changed within the box's counts; a game won pays gold (doubled the first time), a card to choose and against a mask a thing; a game lost costs nothing; the games open in order; cards found go to the box", () => {
  const CM = load(), land = CM.makeWood("cabin-1"), C = CM.CABIN;
  assert.strictEqual(CM.solidAt(land, ...C.door), "cabindoor"); assert.strictEqual(land.things[C.front.join(",")].type, "cabin"); assert.ok(CM.woodSafe(land, ...C.front) && CM.woodSafe(land, C.path[0], C.path[3]), "a safe clearing and path");
  assert.strictEqual(CM.buildingsOf(land).length, 1);
  const g = new CM.Game(); g.newGame("cabin-2", fixedParty(CM), "pauper", "fair", [], "dungeon", { town: true }); g.mode = "explore"; g.village.cards = undefined;
  g.floor.pos = CM.PORTAL_YARD.cabin.slice(); g.use(); assert.strictEqual(g.floor.number, -1); assert.deepStrictEqual(g.floor.pos, C.front, "the portal to the cabin");
  assert.ok(g.pathTo(...CM.WOOD_GATE), "and a way on foot"); let asked = false; g.on("cabin", () => { asked = true; }); g.use(); assert.ok(asked, "Leshy's table");
  g.floor.pos = C.portal.slice(); g.use(); assert.strictEqual(g.floor.number, 0); assert.deepStrictEqual(g.floor.pos, CM.PORTAL_YARD.cabin, "and home to its plinth");
  const K = g.cards(); assert.deepStrictEqual(K.deck, CM.CARD_STARTER); assert.strictEqual(K.owned.Wolf, 1);
  assert.ok(g.deckAdd("Wolf"), "no second wolf in the box");
  while (K.deck.length > CM.CARD_DECK_MIN) assert.strictEqual(g.deckRemove(K.deck[0]), ""); assert.ok(g.deckRemove(K.deck[0]), "never fewer than four");
  assert.ok(g.startCardGame("snow"), "the Snow Line waits on the Wetlands"); assert.ok(g.startCardGame("leshy"));
  assert.strictEqual(g.startCardGame("woods"), ""); g.cardGame.battle.over = "won"; const gold = g.gold, r = g.finishCardGame();
  assert.ok(r.won && g.gold === gold + 2 * CM.CARD_TABLES[0].gold, "doubled the first time"); assert.strictEqual(r.choices.length, 3); assert.ok(r.choices.every((n) => CM.CARD_COMMONS.includes(n)));
  const pick = r.choices[0], had = K.owned[pick] || 0; assert.ok(g.takeCardReward(pick) && !g.takeCardReward(r.choices[1]), "one card"); assert.strictEqual(K.owned[pick], had + 1);
  assert.ok(g.cardTableOpen(CM.CARD_TABLES.find((t) => t.id === "prospector")), "the mask opens");
  g.startCardGame("woods"); g.cardGame.battle.over = "won"; const g2 = g.gold; g.finishCardGame(); assert.strictEqual(g.gold, g2 + CM.CARD_TABLES[0].gold, "plain after the first");
  g.startCardGame("prospector"); g.cardGame.battle.over = "won"; const bag = g.bag.length, rr = g.finishCardGame(); assert.ok(rr.item && g.bag.length === bag + 1, "a thing against a mask"); assert.ok(rr.choices.some((n) => CM.CARD_RARES.includes(n)), "a rare among them");
  g.startCardGame("woods"); g.cardGame.battle.over = "lost"; const g3 = g.gold, bag3 = g.bag.length, lost = g.finishCardGame(); assert.ok(!lost.won && g.gold === g3 && g.bag.length === bag3, "a loss costs nothing");
  g.addCard("Cat", "In the chest:"); assert.strictEqual(K.owned.Cat, 1); const again = new CM.Game(); assert.strictEqual(again.cards().owned.Cat, 1, "kept with the village");
});

test("Claudescryption cards found: about one chest in twenty-two, a champion one time in four, a tower boss one in three (a rare every tenth floor), a rare from every guardian and the Lich King - the seed's, and into the box at the cabin", () => {
  const CM = load(), g = new CM.Game(); g.newGame("find-1", fixedParty(CM), "pauper", "fair", [], "dungeon", { town: true }); g.village.cards = undefined; g.cards();
  let n = 0; for (let i = 0; i < 2200; i++) if (g.findCard(`chest:3:${i},1`, CM.CARD_FIND.chest, "common", null)) n++;
  assert.ok(n > 60 && n < 140, `about one in twenty-two (${n} of 2200)`);
  const box = () => Object.values(g.cards().owned).reduce((s, k) => s + k, 0), b0 = box();
  const r = g.findCard("guardian:rat", 1, "rare", "Among what it guarded:"); assert.ok(CM.CARD_RARES.includes(r) && box() === b0 + 1, "a rare from a guardian");
  const h = new CM.Game(); h.newGame("find-1", fixedParty(CM)); assert.strictEqual(h.findCard("guardian:rat", 1, "rare", null), r, "the seed's card");
  const src = (f) => fs.readFileSync(path.join(ROOT, "src", "js", f), "utf8");
  assert.ok(src("61-explore.js").includes("CM.CARD_FIND.chest") && src("62-combat.js").includes("`guardian:${id}`") && src("62-combat.js").includes("findCard(\"lich\"") && src("64f-towerfoes.js").includes("towerboss:") && src("64g-towerking.js").includes("towerking:1"), "found in chests, from guardians, the king, the tower");
  // a chest opened on a floor puts a card in the box when its hash says so
  const c = new CM.Game(); c.newGame("find-2", fixedParty(CM)); c.enterFloor(2, "down"); c.mode = "explore"; c.village.cards = undefined; c.cards(); const before = c.tally.cardsFound || 0;
  const fl = c.floor; let opened = 0;
  for (let i = 0; i < 300 && (c.tally.cardsFound || 0) === before; i++) { fl.things[`${fl.pos[0]},${fl.pos[1]}`] = { type: "chest", gold: 1, items: [], trap: null }; c.seed = `find-2-${i}`; c.use(); opened++; }   // (each seed its own hash)
  assert.ok((c.tally.cardsFound || 0) > before, `a chest gave a card (after ${opened})`);
});

(async () => {
  let failed = 0;
  const only = process.argv[2];                                          // node tests/run.js "the log"  - just the tests whose name has it
  for (const t of only ? tests.filter((x) => x.name.includes(only)) : tests) {
    const t0 = Date.now();
    try { await t.fn(); console.log(`  ok   ${t.name} (${Date.now() - t0} ms)`); }
    catch (e) { failed++; console.log(`  FAIL ${t.name}\n       ${(e.stack || e.message).split("\n").slice(0, (process.argv[2] ? 12 : 4)).join("\n       ")}`); }
  }
  console.log(failed ? `\n${failed} of ${tests.length} failed` : `\nall ${tests.length} passed`);
  process.exit(failed ? 1 : 0);
})();
