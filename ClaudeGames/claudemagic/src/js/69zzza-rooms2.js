"use strict";
// Set-piece rooms, the second nine (UPGRADE_PLAN_64.md, release 2): the Garden Gone Wild, the Chapel of Candles, the
// Map Room, the Rookery, the Cistern, the Dripping Gallery, the Storm Drain, the Steam Room and the Lightning Rod -
// templates for 69zzz-setpieces.js, with letters of their own: t a map table (Space maps the floor, once), n a
// nest on a ledge (Space takes the trinket in it), q a key lying under a puddle, r an iron rod from roof to floor
// (in a fight in that room a lightning spell chains to every foe for half); and room flags: garden (the plants
// grow thick in it, 69zzs-plants.js), bats (a cloud of them wheels under the roof and scatters, the window's),
// bands and max (where and how deep the room may be).
{ const SP2 = [
    { name: "the Garden Gone Wild", min: 3, garden: true, line: "Beds in rows, a well, a bench gone to moss: a garden someone kept down here, under a grate's light, and the plants have had it to themselves a long time.",
      rows: ["###########", "#RRR.G.RRR#", "#RRR...RRR#", "#...F.....#", "#RRR...RRR#", "#RRR.c.RRR#", "#.........#", "#RRR...RRR#", "#RRR.G.RRR#", "#.........#", "#####D#####"], chests: { c: { item: "shears", note: "under the brambles" } } },
    { name: "the Chapel of Candles", min: 3, line: "Candles in rows, every one of them lit, and no one here to have lit them. The altar at the end is warm.",
      rows: ["#########", "#...A...#", "#.*...*.#", "#.*...*.#", "#.*...*.#", "#.*...*.#", "#.*...*.#", "#.......#", "#.......#", "#####D###"] },
    { name: "the Map Room", min: 4, line: "A stone table fills the middle of the room, and cut into its top, worn by many hands: the floor you stand on, every hall of it.",
      rows: ["#########", "#.......#", "#.......#", "#...t...#", "#.......#", "#......c#", "#.......#", "#.......#", "#####D###"], chests: { c: { item: "mapping", note: "by the table" } } },
    { name: "the Rookery", min: 5, bats: true, line: "The roof goes up out of the torchlight, and something up there shifts and chitters - a great many somethings. The floor is soft with their leavings.",
      rows: ["########", "#RRnRRR#", "#XXXXXX#", "#XXXXXX#", "#XXMXXX#", "#XXXXXX#", "#XXXXXX#", "#XXXXXX#", "#XXXXXX#", "#XXXXXX#", "#XXXXXX#", "###D####"] },
    { name: "the Cistern", min: 2, max: 4, bands: [0, 1, 4], line: "A sunken hall with a drain in every wall: the town's cistern, dry today. After a storm above it would stand to the waist, and the chest in the middle would be a dive.",
      rows: ["###########", "#VVVVVVVVV#", "#VVVVVVVVV#", "#VVVVVVVVV#", "#VVVVVVVVV#", "#VVVVcVVVV#", "#VVVVVVVVV#", "#VVVVVVVVV#", "#VVVVVVVVV#", "#VVVVVVVVV#", "#####D#####"], chests: { c: { sunk: true, note: "in the cistern's middle" } } },
    { name: "the Dripping Gallery", min: 1, max: 3, line: "A long gallery under the street: the drip of it from the roof in a dozen places, puddles on the floor, moss on everything. Something glints in one of the puddles.",
      rows: ["##############", "D..~.....~...#", "#.....q......#", "#.~......~..D#", "##############"] },
    { name: "the Storm Drain", min: 2, max: 6, line: "A channel runs through the room, stone-lined, and water in it; after rain above it would run fast. A sluice gate stands at one end.",
      rows: ["#######", "#..~..#", "#..~..#", "G..~..D", "#..~..#", "#..~..#", "#######"] },
    { name: "the Steam Room", min: 20, bands: [7, 9], line: "Hot stone, and a pool in the floor that would be boiling if it were not fed from the cold above. Under a winter sky this room is a white blindness.",
      rows: ["########", "#......#", "#..~~..#", "#..~~..#", "#.M....#", "#......#", "#......#", "###D####"] },
    { name: "the Lightning Rod", min: 1, max: 3, line: "An iron rod runs from a grate in the roof to the floor, pitted and black. In a storm above it would sing - and anything that lives on lightning would come to it.",
      rows: ["#######", "#.....#", "#..r..#", "#.....#", "#..M..#", "#.....#", "###D###"] },
  ];
  for (const r of SP2) { r.ownDice = true; if (!CM.SETPIECES.some((t) => t.name === r.name)) CM.SETPIECES.push(r); }
  // the letters
  CM.SETPIECE_LETTERS = Object.assign(CM.SETPIECE_LETTERS || {}, {
    t: (fl, x, y, k) => { fl.things[k] = { type: "maptable" }; },
    n: (fl, x, y, k, T, R) => { fl.things[k] = { type: "nest", trinket: R.pick(Object.keys(CM.TRINKETS || { lucky: 1 })) }; },
    q: (fl, x, y, k) => { fl.things[k] = { type: "key" }; fl.decor = fl.decor || []; if (!fl.decor.some((d) => d.kind === "water" && d.x === x && d.y === y)) fl.decor.push({ kind: "water", x, y, puddle: true }); },
    r: (fl, x, y, k) => { fl.things[k] = { type: "rod" }; },
  });
  // the fixed things a chest may hold
  CM.setPieceItem = (what, number) => { if (what === "mapping") return CM.scroll("mapping"); if (what === "shears") return { name: "Gardener's Shears", base: "Knife", kind: "weapon", slot: "weapon", power: 4 + Math.floor(Math.max(1, number) / 3), value: 90, props: { crit: 0.12, bleed: 0.15 } }; return CM.makeItem(CM.storyOf(number), new CM.Random(CM.hashSeed(`${what}:${number}`))); };
  const P = CM.Game.prototype;
  // the map table and the nest
  { const u0 = P.use; P.use = function (...a) { const fl = this.floor; if (fl && this.mode === "explore" && !this.perch) { const here = `${fl.pos[0]},${fl.pos[1]}`, [dx, dy] = CM.DIRS[fl.facing], ahead = `${fl.pos[0] + dx},${fl.pos[1] + dy}`;
        for (const k of [here, ahead]) { const t = fl.things[k]; if (!t) continue;
          if (t.type === "maptable") { if (t.used) { this.say("The table, and the floor cut in it: you know it now."); return true; } t.used = true; fl.seen = []; for (let y = 0; y < fl.grid.length; y++) for (let x = 0; x < fl.grid.length; x++) fl.seen.push([x, y]); if (this.count) this.count("mapped", 1); this.sound("unlock"); this.say("You trace the cuts in the table's top with a finger: every hall of this floor, and the way down marked with a cross. It is in your head now."); this.emit("change"); return true; }
          if (t.type === "nest") { const tr = CM.trinket && t.trinket ? CM.trinket(t.trinket) : null; delete fl.things[k]; if (tr) { this.bag.push(tr); this.sound("coin"); this.say(`A nest of twigs and hair on the ledge, and in it, among the bones of small things: ${tr.name}. You take it.`); } else this.say("A nest of twigs and hair, and the bones of small things. Nothing else."); this.emit("change"); return true; }
          if (t.type === "rod") { this.say("An iron rod, roof to floor, cold and pitted. A storm above would sing in it, and lightning cast here would leap to everything in the room."); return true; } } }
      return u0.apply(this, a); }; }
  // the rod: the fight's terrain
  { const t0 = P.terrain; P.terrain = function () { const out = t0.call(this), fl = this.floor; if (fl && fl.pos && CM.setPieceOf) { const r = CM.setPieceOf(fl, fl.pos[0], fl.pos[1]); if (r && r.template.name === "the Lightning Rod" && !out.includes("rod")) out.push("rod"); } return out; }; }
  { const sh0 = P.spellHit; P.spellHit = function (foe, dmg, what, element, chained, ...rest) { const out = sh0.call(this, foe, dmg, what, element, chained, ...rest); if (element === "storm" && !chained && foe && this.living && this.terrain().includes("rod")) { const others = this.living().filter((f) => f !== foe && !f.hidden); if (others.length) { this.say("The rod sings, and the lightning leaps from it to everything in the room."); for (const o of others) this.spellHit(o, Math.max(1, Math.ceil(dmg / 2)), "The rod's lightning:", "storm", true); } } return out; }; }
}
