"use strict";
// The trials, the second five (UPGRADE_PLAN_65.md, release 4): the Wind Tunnel (a draught that puts the torch out and
// shoves the party a square back every third step on the middle way - a lantern stands, and the squares along the
// walls are out of it; a chest in the wind's eye), the Counting Room (coins on every square, taken by walking; past
// eight squares' worth the inner gate drops, and opens again when enough goes back on the altar - the altar always
// takes), the Crawlway (a room at crawl height end to end, Giant Rats asleep in it, a low chest), the Weighing of
// Deeds (a scale that weighs the run's deeds - foes slain, guardians spoken with, the dead laid to rest, chests opened,
// against fights fled - and gives the band's relic to a party whose good outweighs; otherwise "not yet", and no
// curse), and the Dice Room (the Joker's stone die: a stake of fifty, a six triples it and opens the chest, a one
// hatches a Mimic from the die's box, anything else is the house's; once a day).
//   letters: E a wind square, $ coins, N the inner gate, U the altar, Q rats asleep, K the deeds' scale, "," the die.
{ const TR2 = CM.TRIALS2 = { windEvery: 3, coinsLimit: 8, stake: 50, winTimes: 3, deedsMargin: 10, fledWeight: 4 };
  const SP8 = [
    { name: "the Wind Tunnel", min: 6, line: "The draught comes down the hall like a hand on your chest, and the torch goes to nothing in it. Along the walls the air is still. Down the middle, it is not.",
      rows: ["#####", "#.c.#", "#.E.#", "#.E.#", "#.E.#", "#.E.#", "#.E.#", "#.E.#", "#.E.#", "#.E.#", "#.E.#", "#.E.#", "#.E.#", "#.E.#", "#.E.#", "#...#", "#D###"], chests: { c: { note: "in the eye of the wind" } } },
    { name: "the Counting Room", min: 5, line: "Gold on the floor: not a chest of it, the floor itself, coin on coin, wall to wall, and an altar in the middle with a plate on it, and an iron gate drawn up over the door you came in by. The Counting-House's cousin, and its rule is cut on the altar: take what you like. Leave what you must.",
      rows: ["#########", "#$$$$$$$#", "#$$$$$$$#", "#$$$$$$$#", "#$$$U$$$#", "#$$$$$$$#", "#$$$$$$$#", "#$$N$$$$#", "###D#####"] },
    { name: "the Crawlway", min: 4, bands: [0, 2, 8], line: "The roof comes down to your shoulders and stays there: a room you cross bent double, with the breath of something small and many in it, and a chest so low you could step over it.",
      rows: ["###########", "#.........#", "#..Q......#", "#.........#", "#.........#", "#....c....#", "#.........#", "#......Q..#", "#.........#", "#.........#", "#####D#####"], chests: { c: { note: "low, under the crawl's roof" } } },
    { name: "the Weighing of Deeds", min: 14, line: "A scale, but no pans: two hands of stone held out, and between them a thing of the band's that shines. The carving under it says the scale weighs not gold but what you have done, and gives or does not.",
      rows: ["#########", "#.......#", "#.......#", "#...K...#", "#.......#", "#.......#", "#.......#", "###D#####"] },
    { name: "the Dice Room", min: 8, line: "A stone die the size of a stool in a box of its own, a painted board on the wall with a six and a one on it, and a chest with its lid barred. The Joker's room, or one of his friends'. The stake is fifty.",
      rows: ["#######", "#..9..#", "#.....#", "#..,..#", "#.....#", "#.....#", "###D###"], sealed: "barred till the die shows six" },
  ];
  for (const r of SP8) { r.ownDice = true; if (!CM.SETPIECES.some((t) => t.name === r.name)) CM.SETPIECES.push(r); }
  const kind = (...names) => { for (const n of names) { const k = CM.monsterKind(n); if (k) return k; } return CM.MONSTERS[0]; };
  const uniqueFor = (fl) => { const b = CM.themeIndex(fl.number); return Object.keys(CM.UNIQUES).find((k) => CM.UNIQUES[k].band === b) || Object.keys(CM.UNIQUES)[0]; };
  CM.SETPIECE_LETTERS = Object.assign(CM.SETPIECE_LETTERS || {}, {
    E: (fl, x, y, k) => { fl.features[k] = { type: "wind", known: true }; },
    $: (fl, x, y, k, T, R) => { fl.features[k] = { type: "coins", gold: R.int(3, 9) * Math.max(1, CM.storyOf(fl.number)), known: true }; },
    N: (fl, x, y, k) => { fl.features[k] = { type: "gate", open: true, counting: true }; },
    U: (fl, x, y, k) => { fl.things[k] = { type: "countaltar" }; },
    Q: (fl, x, y, k, T, R) => { const group = []; for (let i = 0; i < 3; i++) group.push(CM.makeMonster(kind("Giant Rat"), Math.max(1, CM.storyOf(fl.number)), R)); fl.things[k] = { type: "monsters", group, asleep: true, still: true }; },
    K: (fl, x, y, k) => { fl.things[k] = { type: "deedscale", unique: uniqueFor(fl) }; },
    ",": (fl, x, y, k) => { fl.things[k] = { type: "die" }; },   /* (X is the old templates' dark floor) */
  });
  // the Crawlway's roof comes down over the whole room
  const crawlRoom = (fl) => { if (!fl || !fl.rooms) return; for (const r of fl.rooms) if (r.name === "the Crawlway") { fl.levels = fl.levels || {}; fl.crawl = fl.crawl || []; for (let y = r.y0; y <= r.y1; y++) for (let x = r.x0; x <= r.x1; x++) { const k = `${x},${y}`; fl.levels[k] = [0, CM.LEVELS ? CM.LEVELS.crawl : 0.8]; if (!fl.crawl.includes(k)) fl.crawl.push(k); } } };
  { const d0 = CM.dressSetPieces; CM.dressSetPieces = function (fl, seed) { const out = d0.call(this, fl, seed); crawlRoom(fl); return out; }; const mf0 = CM.makeFloor; CM.makeFloor = function (number, seed, gen) { const fl = mf0.call(this, number, seed, gen); if (fl && fl.number === number && number >= 1) crawlRoom(fl); return fl; }; }
  const P = CM.Game.prototype;
  const groupAt = (game, fl, group) => { const [dx, dy] = CM.DIRS[fl.facing], sq = `${fl.pos[0] + dx},${fl.pos[1] + dy}`, th = { type: "monsters", group }; const was = fl.things[sq]; fl.things[sq] = th; game.startCombat(sq, th); if (fl.things[sq] === th) { if (was) fl.things[sq] = was; else delete fl.things[sq]; } };
  const roomOf = (fl) => { const r = CM.setPieceOf(fl, fl.pos[0], fl.pos[1]); return r ? r.template.name : null; };
  const gateOf = (fl) => Object.entries(fl.features).find(([, f]) => f.type === "gate" && f.counting) || null;
  const deeds = (game) => { const t = game.tally || {}; const good = (t.kills || 0) + 3 * (t.spoken || []).length + 2 * (game.remainsFound || []).length + (t.chests || 0) + (game.journal || []).length, bad = TR2.fledWeight * (t.fled || 0); return { good, bad }; };
  CM.deedsOf = deeds;
  const LINES = { countaltar: () => "The altar, and its plate, and the rule cut under it: take what you like, leave what you must. (Space to leave a square's worth)", deedscale: (t) => (t.taken ? "The stone hands, empty." : "Two hands of stone and the relic between them. The carving: it weighs what you have done. (Space to be weighed)"), die: () => "A stone die the size of a stool in its box. The stake is fifty: a six triples it and opens the chest; a one is the house's, and worse. (Space to throw it)" };
  { const l0 = P.look; P.look = function (...a) { const out = l0.apply(this, a); const fl = this.floor; if (fl && this.mode === "explore" && !this.perch && fl.things) { const here = `${fl.pos[0]},${fl.pos[1]}`, [dx, dy] = CM.DIRS[fl.facing], ahead = `${fl.pos[0] + dx},${fl.pos[1] + dy}`; for (const k of [here, ahead]) { const t = fl.things[k]; if (t && LINES[t.type]) { this.say(LINES[t.type](t)); break; } } } return out; }; }
  { const u0 = P.use; P.use = function (...a) { const fl = this.floor; if (fl && this.mode === "explore" && !this.perch) { const here = `${fl.pos[0]},${fl.pos[1]}`, [dx, dy] = CM.DIRS[fl.facing], ahead = `${fl.pos[0] + dx},${fl.pos[1] + dy}`;
        for (const k of [here, ahead]) { const t = fl.things[k]; if (!t) continue;
          if (t.type === "countaltar") { const E = this.ext("counting"), S = (E[fl.number] = E[fl.number] || { taken: 0, pile: [] }); if (!S.pile.length) { this.say("The plate is empty, and so are your hands of this room's gold. Nothing to leave."); return true; } const back = Math.min(this.gold, S.pile.pop()); this.gold -= back; S.taken = Math.max(0, S.taken - 1); this.sound("coin"); const g = gateOf(fl); if (g && !g[1].open && S.taken <= TR2.coinsLimit) { g[1].open = true; this.dirty = true; this.say(`${back} gold goes back on the plate - and behind you the gate goes up with a groan. Enough was left.`); } else this.say(`${back} gold goes back on the plate.${g && !g[1].open ? ` The gate stays down: ${S.taken - TR2.coinsLimit} more square${S.taken - TR2.coinsLimit === 1 ? "" : "s"}' worth.` : ""}`); this.emit("change"); return true; }
          if (t.type === "deedscale") { if (t.taken) { this.say("The stone hands, empty."); return true; } const d = deeds(this); if (d.good > d.bad + TR2.deedsMargin) { t.taken = true; const relic = CM.makeUnique(t.unique); this.bag.push(relic); this.sound("coin"); this.say(`The hands weigh you: ${d.good} of good against ${d.bad} of flight. They tilt your way, and ${relic.name} is yours.`); this.emit("change"); } else this.say(`The hands weigh you: ${d.good} of good against ${d.bad} of flight, and they do not tilt. Not yet. The relic stays where it is, and nothing follows you for asking.`); return true; }
          if (t.type === "die") { const E = this.ext("dice"), day = CM.dayOf ? CM.dayOf(this) : 0, S = (E[fl.number] = E[fl.number] || {}); if (S.day === day) { this.say("The die has been thrown today. Tomorrow, if you are still here."); return true; } if (this.gold < TR2.stake) { this.say(`The stake is ${TR2.stake} gold, and you have not got it.`); return true; } S.day = day; this.gold -= TR2.stake; const roll = this.rnd.int(1, 6); this.sound("grind");
            if (roll === 6) { this.gold += TR2.stake * TR2.winTimes; const chest = Object.values(fl.things).find((q) => q.type === "chest" && q.sealed === "the Dice Room"); if (chest) { delete chest.sealed; chest.note = "opened by the six"; } this.say(`The die goes over twice and shows six. ${TR2.stake * TR2.winTimes} gold back, and the bar on the chest lifts.`); this.emit("change"); return true; }
            if (roll === 1) { const R = new CM.Random(CM.hashSeed(`${this.seed}:dicemimic:${fl.number}`)); this.say("The die shows one - and the box it sits in opens its lid, which is a mouth."); groupAt(this, fl, [CM.makeMonster(kind("Mimic", "Orc"), Math.max(1, CM.storyOf(fl.number)), R)]); return true; }
            this.say(`The die shows ${roll}. The house keeps the stake.`); this.emit("change"); return true; } } }
      return u0.apply(this, a); }; }
  // the coins: taken by walking; past the limit the gate drops. The wind: the torch out, and a square back every third step without a lantern
  { const ar0 = P.arrive; P.arrive = function (f, k) { const fl = this.floor;
      if (f && f.type === "coins") { const E = this.ext("counting"), S = (E[fl.number] = E[fl.number] || { taken: 0, pile: [] }); delete fl.features[k]; this.gold += f.gold; S.taken++; S.pile.push(f.gold); this.sound("coin"); const g = gateOf(fl); if (g && g[1].open && S.taken > TR2.coinsLimit) { g[1].open = false; this.dirty = true; this.say(`${f.gold} gold off the floor - and the gate behind you comes down with a crash. The altar is the way to put it right.`); } else this.say(`${f.gold} gold off the floor.`); this.emit("change"); return; }
      if (f && f.type === "wind") { this.gutter = Math.max(this.gutter || 0, 1); const E = this.ext("wind"), S = (E[fl.number] = E[fl.number] || { steps: 0 }); S.steps++; const lantern = this.light && this.light.kind === "lantern"; if (S.steps % TR2.windEvery === 0 && !lantern) { const [dx, dy] = CM.DIRS[fl.facing], back = [fl.pos[0] - dx, fl.pos[1] - dy]; if (CM.isOpen(fl, back[0], back[1]) && !fl.things[`${back[0]},${back[1]}`]) { fl.pos = back; this.say("The wind takes you off your feet and puts you down a square back."); } else this.say("The wind leans on you, and you lean back."); } else if (!S.said) { S.said = true; this.say(lantern ? "The wind puts the torch out and howls at the lantern, which does not care." : "The wind puts the torch out and shoves. Along the walls it is quieter."); } this.emit("change"); return; }
      return ar0.call(this, f, k); }; }
}
