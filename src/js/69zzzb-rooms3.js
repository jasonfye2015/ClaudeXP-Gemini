"use strict";
// Set-piece rooms, the third ten (UPGRADE_PLAN_64.md, release 3): the Echo Chamber, the Gauntlet, the Weighing
// Room, the Barrow, the Wolf Den, the Troll Bridge, the Painter's Room, the Orrery, the Lich's Study and the Kitchen -
// templates for 69zzz-setpieces.js with letters of their own: e a bell (Space rings it, and the floor's nearest
// wandering groups come to the sound), v a vent in the floor (the Furnace's, 61-explore.js: a burn every third
// step), w a scale with a relic on its pan (pay its weight in gold to take it, or take it and be cursed), s a
// sarcophagus (Space opens it: a third chest, and the barrow's king wakes), z a sleeping group (struck before it
// wakes, or walked round), y a troll on a bridge (Space: pay his toll and he waves the party through, or refuse and
// fight), p a ghost painter (stand with him a while for a painted likeness, a trinket), o an orrery (Space reads
// the next three days' weather and the next star's night), x a chair that is a trap (a bounded shock), u a desk
// with a letter in it. Every hazard is bounded and every way stands: nothing here is solid but the troll, who
// takes gold or a fight and is gone either way.
{ CM.TRINKETS.likeness = { name: "A painted likeness", what: "+1 Luck: the party as the painter saw it", props: { stats: { luck: 1 } } }; CM.BASES[CM.TRINKETS.likeness.name] = { id: CM.TRINKETS.likeness.name, kind: "trinket", slot: "trinket", tier: Object.keys(CM.TRINKETS).length, group: "trinket", trinket: "likeness" };
  const SP3 = [
    { name: "the Echo Chamber", min: 4, line: "Every step comes back twice off the walls. A bell hangs in the middle of the room on a frayed rope, and you would not want to be the one who rings it.",
      rows: ["###########", "#.........#", "#....e....#", "#.........#", "#.........#", "#.........#", "#####D#####"] },
    { name: "the Gauntlet", min: 7, line: "A long run of floor, and every other flag of it pierced: the vents breathe in turn, a beat apart. Something at the far end is worth the burns.",
      rows: ["###############", "D.v.v.v.v.v.v.#", "#.............#", "#.v.v.v.v.v.vc#", "###############"], chests: { c: { note: "at the gauntlet's end" } } },
    { name: "the Weighing Room", min: 6, line: "A great brass scale stands in the middle of the room, and on one pan something that shines. The other pan is empty, and it waits.",
      rows: ["#######", "#.....#", "#.....#", "#..w..#", "#.....#", "#.....#", "###D###"] },
    { name: "the Barrow", min: 5, bands: [0, 8], line: "A long mound under a low roof, steps cut up its side to a stone coffin on the top. Grave goods lie at its foot, and the lid is carved with a story.",
      rows: ["#######", "#RRRRR#", "#RRsRR#", "#RRRRR#", "#.....#", "#c...c#", "#.....#", "#.....#", "#.....#", "###D###"] },
    { name: "the Wolf Den", min: 3, line: "Roots come down through the roof here, and trees with them, and in the middle a ring of grey shapes asleep round a kill. Their breath is slow.",
      rows: ["#########", "#T.....T#", "#.......#", "#..d....#", "#...z...#", "#.......#", "#T.....T#", "#.......#", "#####D###"], chests: { d: { item: "venison", note: "the wolves' kill" } } },
    { name: "the Troll Bridge", min: 8, line: "Black water either side, a long way down, and one narrow bridge across it. Halfway along, something large sits with its feet over the edge, and turns its head.",
      rows: ["###########", "D....y....D", "#~~~~~~~~~#", "#~~~~~~~~~#", "###########"] },
    { name: "the Painter's Room", min: 25, line: "An easel, a stool, a palette with the paint still wet, and on the canvas the party - all of you, half done. The painter's hand is still on the brush. The painter is not.",
      rows: ["#######", "#.....#", "#..p..#", "#.....#", "#.....#", "###D###"] },
    { name: "the Orrery", min: 9, bands: [6], line: "Brass rings in the floor, one inside the next, and on them the sun, the moon and the wandering stars on arms, and the whole of it turning, slow, with the sky you cannot see.",
      rows: ["###########", "#RRRRRRRRR#", "#R.......R#", "#R.RRRRR.R#", "#R.R...R.R#", "#R.R.o.R.R#", "#R.R...R.R#", "#R.RRRRR.R#", "#R.......R#", "#RRRRRRRRR#", "#####D#####"] },
    { name: "the Lich's Study", min: 36, line: "A desk, a chair, a lamp long out, and papers everywhere in a hand you have seen cut into the walls. This is where he worked it out.",
      rows: ["#########", "#.......#", "#..u.x..#", "#.......#", "#.......#", "#......c#", "#.......#", "#####D###"], chests: { c: { note: "under the papers" } } },
    { name: "the Kitchen", min: 2, rats: true, line: "A kitchen: the oven cold, the knives on the wall, the flour bins open, and in the flour, a great many small footprints. The bread recipe is carved beside the door.",
      rows: ["##########", "#*.......#", "#........#", "#...c....#", "#........#", "#........#", "#........#", "#####D####"], chests: { c: { item: "knives", note: "on the wall: the cook's knives" } } },
  ];
  for (const r of SP3) { r.ownDice = true; if (!CM.SETPIECES.some((t) => t.name === r.name)) CM.SETPIECES.push(r); }
  const band = (fl) => CM.themeIndex(fl.number), uniqueFor = (fl) => { const b = band(fl), id = Object.keys(CM.UNIQUES).find((k) => CM.UNIQUES[k].band === b) || Object.keys(CM.UNIQUES)[0]; return id; };
  CM.SETPIECE_LETTERS = Object.assign(CM.SETPIECE_LETTERS || {}, {
    e: (fl, x, y, k) => { fl.things[k] = { type: "bell" }; },
    v: (fl, x, y, k) => { fl.features[k] = { type: "vents", known: true }; },
    w: (fl, x, y, k) => { fl.things[k] = { type: "scale", unique: uniqueFor(fl), price: 120 + 20 * Math.max(1, CM.storyOf(fl.number)) }; },
    s: (fl, x, y, k) => { fl.things[k] = { type: "sarcophagus" }; },
    z: (fl, x, y, k, T, R) => { const group = []; for (let i = 0; i < 3; i++) group.push(CM.makeMonster(CM.monsterKind("Wolf") || CM.monsterKind("Giant Rat"), Math.max(1, CM.storyOf(fl.number)), R)); fl.things[k] = { type: "monsters", group, asleep: true, still: true }; },
    y: (fl, x, y, k) => { fl.things[k] = { type: "troll", toll: 15 * Math.max(1, CM.storyOf(fl.number)) }; },
    p: (fl, x, y, k) => { fl.things[k] = { type: "painter" }; },
    o: (fl, x, y, k) => { fl.things[k] = { type: "orrery" }; },
    x: (fl, x, y, k) => { fl.features[k] = { type: "chair", known: false }; },
    u: (fl, x, y, k) => { fl.things[k] = { type: "desk" }; },
  });
  { const i0 = CM.setPieceItem; CM.setPieceItem = (what, number) => { if (what === "venison") return CM.meat("Deer"); if (what === "knives") return { name: "The Cook's Knives", base: "Knife", kind: "weapon", slot: "weapon", power: 5 + Math.floor(Math.max(1, number) / 3), value: 70, props: { crit: 0.15 } }; return i0(what, number); }; }
  // the troll bars the bridge
  { const o0 = CM.isOpen; CM.isOpen = function (floor, x, y) { if (!o0(floor, x, y)) return false; const t = floor.things && floor.things[`${x},${y}`]; return !(t && t.type === "troll"); }; }
  const P = CM.Game.prototype;
  { const sc0 = P.startCombat; P.startCombat = function (key, thing, theyCame) { if (thing && thing.asleep && !theyCame) { this.strikeSleepers = true; delete thing.asleep; } return sc0.call(this, key, thing, theyCame); }; }
  const groupAt = (game, fl, group) => { const [dx, dy] = CM.DIRS[fl.facing], sq = `${fl.pos[0] + dx},${fl.pos[1] + dy}`, th = { type: "monsters", group }; const was = fl.things[sq]; fl.things[sq] = th; game.startCombat(sq, th); if (fl.things[sq] === th) { if (was) fl.things[sq] = was; else delete fl.things[sq]; } };
  { const u0 = P.use; P.use = function (...a) { const fl = this.floor; if (fl && this.mode === "explore" && !this.perch) { const here = `${fl.pos[0]},${fl.pos[1]}`, [dx, dy] = CM.DIRS[fl.facing], ahead = `${fl.pos[0] + dx},${fl.pos[1] + dy}`;
        for (const k of [here, ahead]) { const t = fl.things[k]; if (!t) continue;
          if (t.type === "bell") { const groups = Object.entries(fl.things).filter(([q, th]) => th.type === "monsters" && th.group && th.group.length && !th.still && q !== k).map(([q, th]) => ({ q, th, d: Math.abs(Number(q.split(",")[0]) - fl.pos[0]) + Math.abs(Number(q.split(",")[1]) - fl.pos[1]) })).sort((p, q) => p.d - q.d).slice(0, 2);
            this.sound("lever"); if (!groups.length) { this.say("You ring the bell, and the note goes through the whole floor and comes back twice. Nothing answers it."); return true; } const group = groups.flatMap((g) => g.th.group); for (const g of groups) delete fl.things[g.q]; this.say("You ring the bell. The note goes through the whole floor and comes back twice - and the floor comes to it."); groupAt(this, fl, group); return true; }
          if (t.type === "scale") { if (t.taken) { this.say("The scale, its pans empty now, still rocking a little."); return true; } const relic = CM.makeUnique(t.unique); if (this.gold >= t.price) { this.gold -= t.price; this.spend && this.spend("scale", t.price); t.taken = true; this.bag.push(relic); this.sound("coin"); this.say(`You count ${t.price} gold onto the empty pan, and the pans level: ${relic.name} is yours by weight.`); }
            else { t.taken = true; this.bag.push(relic); const h = this.alive()[0]; if (h) { h.status = h.status || {}; h.status.curse = 999; } this.sound("ailment"); this.say(`You have not the gold, and you take ${relic.name} anyway. The empty pan drops with a clang, and something settles on ${h ? h.name : "the party"} like a cold hand: cursed, till it is lifted.`); } this.emit("change"); return true; }
          if (t.type === "sarcophagus") { if (t.opened) { this.say("The coffin, open, and empty now."); return true; } t.opened = true; const R = new CM.Random(CM.hashSeed(`${this.seed}:barrow:${fl.number}`)); fl.things[k] = { type: "chest", gold: R.int(40, 90) * Math.max(1, CM.storyOf(fl.number)), items: [CM.makeItem(CM.storyOf(fl.number), R, undefined, 3), CM.makeItem(CM.storyOf(fl.number), R, undefined, 3)], trap: null, note: "in the coffin" }; this.sound("grind"); this.say("The lid grinds aside. Grave goods in the coffin - and the one who was buried with them sits up.");
            const group = [CM.makeMonster(CM.monsterKind("Wraith") || CM.monsterKind("Skeleton"), CM.storyOf(fl.number), R), CM.makeMonster(CM.monsterKind("Skeleton"), CM.storyOf(fl.number), R), CM.makeMonster(CM.monsterKind("Skeleton"), CM.storyOf(fl.number), R)]; groupAt(this, fl, group); return true; }
          if (t.type === "troll") { if (this.gold >= t.toll) { this.gold -= t.toll; this.spend && this.spend("toll", t.toll); delete fl.things[k]; this.sound("coin"); this.say(`"Toll," says the troll, and holds out a hand the size of a shield. ${t.toll} gold goes into it, and he shifts his feet aside and waves you on. He will remember your faces.`); if (this.count) this.count("tollsPaid", 1); this.emit("change"); return true; }
            delete fl.things[k]; this.say(`"Toll," says the troll. You have not got it, and he stands up, all of him, which takes a while.`); const R = new CM.Random(CM.hashSeed(`${this.seed}:troll:${fl.number}`)); groupAt(this, fl, [CM.makeMonster(CM.monsterKind("Troll") || CM.monsterKind("Ogre"), Math.max(1, CM.storyOf(fl.number)), R)]); return true; }
          if (t.type === "painter") { if (t.done) { this.say("The painting is finished, and the painter has gone with the light."); return true; } t.done = true; this.clock = (this.clock || 0) + 10; this.bag.push(CM.trinket("likeness")); this.sound("coin"); this.say("You stand still, as the brush asks, while the light goes grey and comes back. When you look again the painting is done - the four of you, as he saw you - and small enough to carry. The painter is not there."); this.emit("change"); return true; }
          if (t.type === "orrery") { const season = CM.season ? CM.season(this) : "summer", day = CM.dayOf ? CM.dayOf(this) : 0, words = [1, 2, 3].map((i) => CM.weatherOf ? CM.weatherOf(this.seed, day + i, season) : "clear"); const M = this.ext ? this.ext("meteors") : null; let star = ""; if (M && M.next) { const d = Math.max(0, Math.ceil((M.next - CM.clockOf(this)) / (24 * 60))); star = d === 0 ? " A star falls tonight." : ` A star falls in ${d} day${d === 1 ? "" : "s"}.`; }
            this.say(`The rings turn as you watch, and the arms with them. Tomorrow: ${words[0]}. The day after: ${words[1]}. The day after that: ${words[2]}.${star}`); return true; }
          if (t.type === "desk") { this.say(t.read ? "The desk, and his papers. You have read enough." : "The papers on the desk are notes toward a thing that should not be made, in a careful hand, and a letter at the bottom that begins 'If you are reading this, the box held.' It does not say what it held. You put it back where it was."); t.read = true; if (!t.read2) { t.read2 = true; if (this.markRead) this.markRead("desk.lich"); } return true; } } }
      return u0.apply(this, a); }; }
  // the chair that is a trap
  { const ar0 = P.arrive; P.arrive = function (f, k) { if (f && f.type === "chair") { if (f.known) { this.say("The chair. You stand well clear of it this time."); return; } f.known = true; let bit = 0; for (const h of this.alive()) if (h.hp > 2) { h.hp = Math.max(1, h.hp - 2); bit++; } this.sound("trap"); this.say(bit ? "The chair is a trap: a shock runs up through the floor and every one of you (-2). He did not like visitors." : "The chair is a trap, and it snaps at nothing."); return; } return ar0.call(this, f, k); }; }
}
