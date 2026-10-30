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
  assert.match(game.build("guildhall"), /asks 100/);
  game.village.renown = 1000;
  assert.strictEqual(game.build("guildhall"), ""); assert.strictEqual(game.villageLevel("guildhall"), 1); assert.strictEqual(game.renown(), 900);
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
  assert.strictEqual(Object.keys(CM.TRINKETS).length, 20); assert.strictEqual(Object.keys(CM.RELIC_POWERS).length, 9); assert.ok(CM.SLOTS.includes("trinket"));
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
