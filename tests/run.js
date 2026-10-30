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

test("generator 1 is frozen: twenty-eight seeds' fingerprints, and generator 2 still makes the same floors", () => {
  const CM = load(), fx = JSON.parse(fs.readFileSync(path.join(__dirname, "fixtures", "gen1.json"), "utf8"));
  let n = 0;
  for (const [seed, floors] of Object.entries(fx)) for (const [k, print] of Object.entries(floors)) {
    if (n++ % 7) continue;                                               // (a fifth of them: the whole set takes a minute)
    assert.strictEqual(CM.floorPrint(CM.makeFloor(Number(k), seed, 1)), print, `gen 1, ${seed} floor ${k}`);
    assert.strictEqual(CM.floorPrint(CM.makeFloor(Number(k), seed, 2)), print, `gen 2 has not grown yet: ${seed} floor ${k}`);
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

let failed = 0;
for (const t of tests) {
  const t0 = Date.now();
  try { t.fn(); console.log(`  ok   ${t.name} (${Date.now() - t0} ms)`); }
  catch (e) { failed++; console.log(`  FAIL ${t.name}\n       ${(e.stack || e.message).split("\n").slice(0, 4).join("\n       ")}`); }
}
console.log(failed ? `\n${failed} of ${tests.length} failed` : `\nall ${tests.length} passed`);
process.exit(failed ? 1 : 0);
