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
  assert.strictEqual(Object.keys(uniques).length, 10, "one unique in every band: " + JSON.stringify(uniques));
  for (const [id, f] of Object.entries(uniques)) assert.strictEqual(CM.themeIndex(f), CM.UNIQUES[id].band, `${id} lies in its own band`);
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

let failed = 0;
for (const t of tests) {
  const t0 = Date.now();
  try { t.fn(); console.log(`  ok   ${t.name} (${Date.now() - t0} ms)`); }
  catch (e) { failed++; console.log(`  FAIL ${t.name}\n       ${(e.stack || e.message).split("\n").slice(0, 4).join("\n       ")}`); }
}
console.log(failed ? `\n${failed} of ${tests.length} failed` : `\nall ${tests.length} passed`);
process.exit(failed ? 1 : 0);
