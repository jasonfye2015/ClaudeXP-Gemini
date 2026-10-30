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
  assert.ok(game.shopping && game.stock && game.stock.length === 5 && game.peddling);
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
  assert.strictEqual(CM.PARLEY.root.gate, null, "the Root wants nothing you have, yet");
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

(async () => {
  let failed = 0;
  for (const t of tests) {
    const t0 = Date.now();
    try { await t.fn(); console.log(`  ok   ${t.name} (${Date.now() - t0} ms)`); }
    catch (e) { failed++; console.log(`  FAIL ${t.name}\n       ${(e.stack || e.message).split("\n").slice(0, 4).join("\n       ")}`); }
  }
  console.log(failed ? `\n${failed} of ${tests.length} failed` : `\nall ${tests.length} passed`);
  process.exit(failed ? 1 : 0);
})();
