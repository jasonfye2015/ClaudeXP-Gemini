"use strict";
// Lairs and dens (UPGRADE_PLAN_65.md, release 5): the Rat King's Nest (rats on every square of the clutter's, a nest of
// rags with an elite rat on it, crowned, and under it what the fled have dropped), the Hatchery (wyvern eggs on warm
// sand - one taken is a thing worth selling, and the mother comes down the shaft), the Bandit Camp (a fire, a loot
// pile, and the rivals' own parley: pass with a toll, trade, or fight), the Vampire's Parlour (a table set for guests:
// sit, and a bargain is offered - blood for a relic, five of a hero's health for the run; the candlesticks are a chest
// the Vampire guards), the Golem Forge (a Crystal Golem half made on a slab: throw the lever and it finishes, and it
// knows no friend), and the Drowned Shrine (the Drowned kneeling round a sea-stone with a pearl on it: a thing of
// flesh laid on the stone first and they let the pearl go; taken bare, they rise).
//   letters: n2 -> uses the clutter's rats (rats: true), W is excluded by the templates, so: P the nest, e2 -> ; letters
//   here: V-free... (see the table): @ is the grate (stage 2); new: P the nest, L? (ring) no; used: P nest, 3? taken;
//   assigned: P nest, "e"? taken. Final: P nest, q? taken (key) -> O taken (ice). The letters of this file: P (nest),
//   y? taken. => P nest, 7? taken. Chosen: P nest, "(" an egg, ")" the camp's fire, "<" the vampire's table,
//   ">" the slab's lever, "{" the sea-stone.
{ const LR = CM.LAIRS = { eggValue: 400, bloodPrice: 5, pearlRare: true };
  const SP9 = [
    { name: "the Rat King's Nest", min: 3, bands: [0, 1], rats: true, line: "Rags and bones and the smell, and rats - on every flag, in every corner, going over one another - and in the middle a nest of what they have dragged in, and on it one of them, bigger, with something on its head that shines.",
      rows: ["#########", "#.......#", "#.......#", "#...P...#", "#.......#", "#.......#", "#.......#", "###D#####"] },
    { name: "the Hatchery", min: 36, bands: [6, 7], line: "Warm sand underfoot, and the heat coming up through it, and in the sand, in a ring, eggs the size of a man's chest, leathery and grey and one of them rocking. Overhead a shaft goes up into the dark, and something up there breathes.",
      rows: ["###########", "#.........#", "#..(...(..#", "#.........#", "#.(..R..(.#", "#.........#", "#..(...(..#", "#.........#", "#.........#", "#####D#####"] },
    { name: "the Bandit Camp", min: 6, line: "A fire in the middle of the hall and four about it with their backs to the walls and their hands near their hilts, and behind them a pile of what they have taken off the people who came this way before you. They have seen you. They are deciding.",
      rows: ["###########", "#.........#", "#...c.....#", "#....)....#", "#.........#", "#.........#", "#.........#", "#.........#", "#####D#####"], chests: { c: { note: "the bandits' pile, behind the fire", guard: ["Sellsword", "Sellsword", "Hedge Wizard"] } } },
    { name: "the Vampire's Parlour", min: 16, bands: [3], line: "A parlour: a long table laid for guests who are not here, candles burning that no one lit, a mirror that shows the room and not you, and at the table's head a chair with someone in it, very still, who smiles.",
      rows: ["#########", "#.......#", "#..<....#", "#.......#", "#.......#", "#.....c.#", "#.......#", "###D#####"], chests: { c: { note: "the candlesticks", guard: ["Vampire"] } } },
    { name: "the Golem Forge", min: 36, bands: [6, 7], line: "A slab, and on it a golem of crystal half made - the legs and the trunk and one arm, the rest in pieces on the floor beside it - and a lever by the furnace mouth that someone did not pull. The vents breathe round it.",
      rows: ["###########", "#.........#", "#.v..RR..v#", "#....R>...#", "#.........#", "#.v.....v.#", "#.........#", "#.........#", "#####D#####"] },
    { name: "the Drowned Shrine", min: 21, bands: [4], line: "Water to the knee, and in it a ring of the Drowned on their knees with their faces down, and in the middle a stone the sea shaped, and on the stone a pearl. They have not looked up. They are waiting for something to be put on the stone.",
      rows: ["#########", "#~~~~~~~#", "#~~~~~~~#", "#~~~{~~~#", "#~~~~~~~#", "#~~~~~~~#", "#.......#", "###D#####"] },
  ];
  for (const r of SP9) { r.ownDice = true; if (!CM.SETPIECES.some((t) => t.name === r.name)) CM.SETPIECES.push(r); }
  const kind = (...names) => { for (const n of names) { const k = CM.monsterKind(n); if (k) return k; } return CM.MONSTERS[0]; };
  const uniqueFor = (fl) => { const b = CM.themeIndex(fl.number); return Object.keys(CM.UNIQUES).find((k) => CM.UNIQUES[k].band === b) || Object.keys(CM.UNIQUES)[0]; };
  const level = (fl, k, h) => { fl.levels = fl.levels || {}; fl.levels[k] = [h, 1]; };
  CM.SETPIECE_LETTERS = Object.assign(CM.SETPIECE_LETTERS || {}, {
    P: (fl, x, y, k, T, R) => { const L = Math.max(1, CM.storyOf(fl.number)), group = [CM.makeMonster(kind("Giant Rat"), L, R), CM.makeMonster(kind("Giant Rat"), L, R), CM.makeMonster(kind("Giant Rat"), L, R)]; if (CM.makeElite) CM.makeElite(group, R, 2); group[0].name = "the Rat King's heir"; group[0].crowned = true;
      fl.things[k] = { type: "ratnest", group, chest: { type: "chest", gold: R.int(15, 40) * L, items: [CM.trinket(R.pick(Object.keys(CM.TRINKETS))), CM.makeItem(CM.storyOf(fl.number), R, undefined, 2)], trap: null, note: "what the fled have dropped, under the rags" } }; },
    "(": (fl, x, y, k) => { fl.things[k] = { type: "egg" }; },
    ")": (fl, x, y, k) => { fl.things[k] = { type: "rivals", met: false, camp: true }; },
    "<": (fl, x, y, k) => { fl.things[k] = { type: "vampiretable", relic: uniqueFor(fl) }; },
    ">": (fl, x, y, k) => { level(fl, k, CM.LEVELS ? CM.LEVELS.dais : 0.3); fl.things[k] = { type: "golemlever" }; },
    "{": (fl, x, y, k) => { fl.decor = fl.decor || []; if (!fl.decor.some((d) => d.kind === "water" && d.x === x && d.y === y)) fl.decor.push({ kind: "water", x, y, fish: false }); level(fl, k, CM.LEVELS ? CM.LEVELS.dais : 0.3); fl.things[k] = { type: "seastone", pearl: true }; },
  });
  // the Hatchery's sand is warm: the egg is a thing of value; the nest's rats are the clutter's, many
  CM.wyvernEgg = () => ({ name: "A wyvern's egg", kind: "egg", power: 0, value: LR.eggValue, props: {} });
  const P = CM.Game.prototype;
  const groupAt = (game, fl, group) => { const [dx, dy] = CM.DIRS[fl.facing], sq = `${fl.pos[0] + dx},${fl.pos[1] + dy}`, th = { type: "monsters", group }; const was = fl.things[sq]; fl.things[sq] = th; game.startCombat(sq, th); if (fl.things[sq] === th) { if (was) fl.things[sq] = was; else delete fl.things[sq]; } };
  const LINES = { ratnest: (t) => (t.group ? "A nest of rags and bones, and on it the big one with the crown, watching you with both red eyes. The others are watching it. (Space to go for it)" : "The nest, empty, the rags turned over."), egg: () => "An egg the size of a man's chest, leathery, grey, warm. One of them is rocking. (Space to take this one)",
    vampiretable: (t) => (t.done ? "The table, and the host's chair, empty. The candles are out." : "The host at the table's head smiles and gestures at a chair. There is a bargain in the gesture. (Space to sit)"), golemlever: (t) => (t.thrown ? "The lever, thrown; the slab is empty." : "The lever by the furnace mouth. It finishes what is on the slab. (Space to throw it)"),
    seastone: (t) => (t.pearl ? "The sea-stone, and on it a pearl the size of a plum, and round it the Drowned on their knees, waiting. (Space: lay something on the stone, or take the pearl)" : "The sea-stone, bare. The Drowned have gone down into the water.") };
  { const l0 = P.look; P.look = function (...a) { const out = l0.apply(this, a); const fl = this.floor; if (fl && this.mode === "explore" && !this.perch && fl.things) { const here = `${fl.pos[0]},${fl.pos[1]}`, [dx, dy] = CM.DIRS[fl.facing], ahead = `${fl.pos[0] + dx},${fl.pos[1] + dy}`; for (const k of [here, ahead]) { const t = fl.things[k]; if (t && LINES[t.type]) { this.say(LINES[t.type](t)); break; } } } return out; }; }
  { const u0 = P.use; P.use = function (...a) { const fl = this.floor; if (fl && this.mode === "explore" && !this.perch) { const here = `${fl.pos[0]},${fl.pos[1]}`, [dx, dy] = CM.DIRS[fl.facing], ahead = `${fl.pos[0] + dx},${fl.pos[1] + dy}`, L = Math.max(1, CM.storyOf(fl.number));
        for (const k of [here, ahead]) { const t = fl.things[k]; if (!t) continue;
          if (t.type === "ratnest") { if (!t.group) { this.say("The nest, empty, the rags turned over."); return true; } const group = t.group; t.group = null; fl.things[k] = Object.assign(t.chest, { nest: true }); this.say("You go for the crown, and the whole floor of rats goes for you, and the big one comes off its nest with a scream like a child's."); groupAt(this, fl, group); return true; }
          if (t.type === "egg") { delete fl.things[k]; this.bag.push(CM.wyvernEgg()); this.sound("coin"); const E = this.ext("hatchery"); if (!E[fl.number]) { E[fl.number] = true; const R = new CM.Random(CM.hashSeed(`${this.seed}:wyvern:${fl.number}`)); this.say("You lift the egg out of the sand, warm as a loaf - and overhead the breathing stops, and something comes down the shaft with its wings folded."); this.emit("change"); groupAt(this, fl, [CM.makeMonster(kind("Wyvern", "Gargoyle"), L, R)]); return true; } this.say("Another egg, warm as a loaf. The shaft overhead is quiet now."); this.emit("change"); return true; }
          if (t.type === "vampiretable") { if (t.done) { this.say("The table, and the host's chair, empty."); return true; } if (!t.sat) { t.sat = true; this.say("You sit. \"Guests,\" says the host, \"at last. I have something of the band's that I do not need, and you have something I do. A little of one of you - five of your blood, for the run - and it is yours. Sit again if you agree. Stand and go if you do not; I will not follow. Touch the candlesticks and I will.\""); return true; }
            t.done = true; const h = this.alive()[0]; if (h) { h.max = Math.max(1, h.max - LR.bloodPrice); h.hp = Math.min(h.hp, h.max); } const relic = CM.makeUnique(t.relic); this.bag.push(relic); this.sound("ailment"); this.say(`${h ? h.name : "Someone"} gives the host a wrist, and five of ${h ? h.name + "'s" : "their"} blood for the run, and the host, courteous, gives ${relic.name} across the table and shows you to the door.`); this.emit("change"); return true; }
          if (t.type === "golemlever") { if (t.thrown) { this.say("The lever, thrown; the slab is empty."); return true; } t.thrown = true; this.sound("lever"); const R = new CM.Random(CM.hashSeed(`${this.seed}:golem:${fl.number}`)); this.say("The lever goes over and the furnace roars and the pieces on the floor get up and go to the slab, and the golem stands, finished. It was made for the Foundry Master's war, and it knows no friend."); if (this.count) this.count("golemsWoken", 1); groupAt(this, fl, [CM.makeMonster(kind("Crystal Golem", "Gargoyle"), L, R)]); return true; }
          if (t.type === "seastone") { if (!t.pearl) { this.say("The sea-stone, bare."); return true; } const i = this.bag.findIndex((it) => it.kind === "meat" || it.kind === "fish" || it.meat); const pearl = CM.ingredient("cavepearl"); t.pearl = false;
            if (i >= 0) { const gift = this.bag.splice(i, 1)[0]; this.bag.push(pearl); this.sound("coin"); this.say(`You lay ${gift.name} on the stone. The Drowned lift their faces, and look at it, and one by one they go down under the water and are gone. The pearl is yours.`); this.emit("change"); return true; }
            this.bag.push(pearl); const R = new CM.Random(CM.hashSeed(`${this.seed}:shrine:${fl.number}`)), group = []; for (let j = 0; j < 3; j++) group.push(CM.makeMonster(kind("Drowned", "Zombie"), L, R)); this.say("You take the pearl off the bare stone, and the ring of the Drowned lift their faces and rise, all together, with the water running off them."); groupAt(this, fl, group); return true; } } }
      return u0.apply(this, a); }; }
}
