"use strict";
// Set-piece rooms (UPGRADE_PLAN_64.md, release 1): new letters for the templates, and the first four rooms. The
// letters, read after a floor's making from every template room's fill: T a tree square (a mesh tree stands there
// and the walk is barred - the square is open stone under it, nothing is drawn as a wall), ~ still water (wadable,
// the flooded mood's water, lilypads, fish when the room says so), B a heap of bones (looked at, turned over for
// what is under it), b a heap with a chest under it, H a false door on the ring (a door painted on the stone or
// nailed shut), h a niche door (opens on a niche a step deep with a thing in it), m a niche with a mimic, R a raised
// square, V a sunken one, * a brazier, G a glowcap that never fades. A chest may carry a guard (a kind that rises
// when it is opened) and a room its lore line, said on the first step into it. Generator 2 only (generator 1's
// floors are frozen by their fingerprints).
//   CM.SETPIECES                          the rooms (pushed into CM.TEMPLATES2)
//   CM.treesIn(fl) -> Set "x,y"           the tree squares of the floor's rooms (69zzs-plants.js stands meshes there)
//   CM.setPieceOf(fl, x, y) -> room | null
{ const SP = CM.SETPIECES = [
    { name: "the Oasis", min: 2, line: "Trees - real trees, green under a grate's light - stand in a ring about a pool, and the air is sweet. Something glints on the far bank, and something under the water.", fish: true,
      rows: ["############", "#T.T....T.T#", "#..........#", "#T..~~~..T.#", "#...~~~....#", "#T..~~~..Tc#", "#..........#", "#T.T....T.T#", "#..........#", "#....G.....#", "#T........T#", "#####D######"], chests: { c: { guard: ["Wolf", "Wolf"], note: "on the far bank" } }, sunk: { pond: true } },
    { name: "the Bone Room", min: 3, line: "Bones, heaped against every wall to the height of a man, and the floor black with their dust. One heap is bigger than any beast you know. Something is not all here.",
      rows: ["##########", "#BBBBBBBB#", "#BXXXXXXB#", "#BXXBXXXB#", "#BXXXXXXB#", "#BXXXXXbB#", "#BXXXXXXB#", "#BXXXXXXB#", "#BBBBBBBB#", "#####D####"], stir: ["Skeleton", "Skeleton", "Skeleton"] },
    { name: "the Hall of Doors", min: 2, line: "A long hall, and doors down both its walls - more doors than any hall needs. Most of them, you would guess, go nowhere.",
      rows: ["#H#H#h#H#H#H#m#H#", "D...............D", "#...............#", "#...............#", "#H#h#H#H#H#H#H#H#"], niches: { h: ["key", "chest"] } },
    { name: "the Fish Pool", min: 4, line: "A pool fills the room wall to wall, black and still, and something moves in it - fish, small and quick. A line of planks runs out to a stone in the middle, and a chest on the stone.", fish: true,
      rows: ["#########", "#~~~~~~~#", "#~~~~~~~#", "#~~~~c~~#", "#~~~~.~~#", "#~~~~.~~#", "#~~~~.~~#", "#~~~~.~~#", "#####D###"], chests: { c: { guard: ["Drowned"], note: "on the stone" } } },
  ];
  for (const r of SP) r.ownDice = true;
  // one floor in three from the third (never a maze, never the last) takes one of them, chosen by a hash of its own and placed with its own dice (22-gen2.js), so the floor's other rooms stand where they stood
  CM.SETPIECE_EVERY = 3;
  { const pf0 = CM.planFloor; if (pf0) CM.planFloor = function (number, seed, rnd, special, lair) { const plan = pf0.call(this, number, seed, rnd, special, lair); if (special === "maze" || number < 3 || number === CM.LAST_FLOOR || number === CM.BOTTOM || !(number >= 1)) return plan;
      const h = CM.hashSeed(`${seed}:setpiece:${number}`) >>> 0; if (h % CM.SETPIECE_EVERY !== 0) return plan; const fit = SP.filter((r) => CM.storyOf(number) >= r.min && (!r.max || CM.storyOf(number) <= r.max) && (!r.bands || r.bands.includes(CM.themeIndex(number)))); if (!fit.length) return plan; const sp = fit[(h >>> 8) % fit.length]; delete sp._dice; plan.pieces.push(sp); return plan; }; }
  const rnd = () => (CM.wxRandom ? CM.wxRandom() : Math.random());
  CM.treesIn = (fl) => Object.keys((fl && fl.treesIn) || {});   // (an object, not a Set: the floor is saved as JSON)
  const pieceOf = (r) => SP.find((t) => t.name === r.name) || null;   // (a floor's rooms keep bounds and the template's name only)
  CM.fillOf = (T, r) => { const fill = []; T.rows.forEach((row, ry) => [...row].forEach((c, rx) => { if (!"DLGS#W".includes(c)) fill.push([r.x0 - 1 + rx, r.y0 - 1 + ry, c]); })); return fill; };
  CM.setPieceOf = (fl, x, y) => { const r = ((fl && fl.rooms) || []).find((r) => pieceOf(r) && x >= r.x0 && x <= r.x1 && y >= r.y0 && y <= r.y1); return r ? Object.assign({ template: pieceOf(r) }, r) : null; };
  // the letters, after the making
  const dress = (fl, seed) => { if (!fl || !fl.rooms) return; const R = new CM.Random(CM.hashSeed(`${seed}:setpieces:${fl.number}`)); fl.treesIn = fl.treesIn || {};
    for (const r of fl.rooms) { const T = pieceOf(r); if (!T) continue; const C = T.chests || {}, fill = CM.fillOf(T, r); let niches = 0;
      for (const [x, y, c] of fill) { const k = `${x},${y}`;
        if (c === "T") { fl.treesIn[k] = true; }
        else if (c === "~") { fl.decor = fl.decor || []; if (!fl.decor.some((d) => d.kind === "water" && d.x === x && d.y === y)) fl.decor.push({ kind: "water", x, y, fish: Boolean(T.fish) }); }
        else if (c === "B") fl.things[k] = { type: "boneheap" };
        else if (c === "b") fl.things[k] = { type: "boneheap", chest: { type: "chest", gold: R.int(20, 50) * Math.max(1, CM.storyOf(fl.number)), items: [CM.makeItem(CM.storyOf(fl.number), R, undefined, 2), CM.makeItem(CM.storyOf(fl.number), R, undefined, 3)], trap: null }, stir: T.stir ? T.stir.slice() : null };
        else if (c === "H") fl.features[k] = { type: "falsedoor", how: R.pick(["painted", "nailed", "painted", "bricked"]) };
        else if (c === "h") { const what = (T.niches && T.niches.h) ? T.niches.h[niches++ % T.niches.h.length] : "key"; fl.features[k] = { type: "falsedoor", niche: what === "chest" ? { type: "chest", gold: R.int(10, 30) * Math.max(1, CM.storyOf(fl.number)), items: [CM.makeItem(CM.storyOf(fl.number), R, undefined, 2)], trap: null } : { type: what } }; }
        else if (c === "m") fl.features[k] = { type: "falsedoor", mimic: true };
        else if (c === "R") { fl.levels = fl.levels || {}; fl.levels[k] = [CM.LEVELS ? CM.LEVELS.dais : 0.3, 1]; }
        else if (c === "V") { fl.levels = fl.levels || {}; fl.levels[k] = [CM.LEVELS ? CM.LEVELS.pit : -0.3, 1]; }
        else if (c === "*") fl.things[k] = { type: "brazier", lit: true };
        else if (c === "G") fl.things[k] = { type: "glowcap", at: 0, permanent: true };
        else if (CM.SETPIECE_LETTERS && CM.SETPIECE_LETTERS[c]) CM.SETPIECE_LETTERS[c](fl, x, y, k, T, R);   /* (a later file's letters: 69zzza-rooms2.js) */
        else if (C[c]) { const spec = C[c] || {};   /* (any letter the room names a chest by: c, d...) */ fl.things[k] = { type: "chest", gold: R.int(25, 60) * Math.max(1, CM.storyOf(fl.number)), items: spec.item && CM.setPieceItem ? [CM.setPieceItem(spec.item, fl.number)] : [CM.makeItem(CM.storyOf(fl.number), R, undefined, 3), CM.makeItem(CM.storyOf(fl.number), R, undefined, 2)], trap: null, guard: spec.guard ? spec.guard.slice() : null, note: spec.note || null, sunk: Boolean(spec.sunk) }; } }
      if (T.sunk && T.sunk.pond) { const pond = fill.filter(([, , c]) => c === "~"); if (pond.length) { const [px, py] = pond[Math.floor(pond.length / 2)]; fl.things[`${px},${py}`] = { type: "chest", gold: R.int(30, 80) * Math.max(1, CM.storyOf(fl.number)), items: [CM.makeItem(CM.storyOf(fl.number), R, undefined, 3)], trap: null, sunk: true, water: true }; } } } };
  CM.dressSetPieces = dress;
  { const mf0 = CM.makeFloor; CM.makeFloor = function (number, seed, gen) { const fl = mf0.call(this, number, seed, gen); if (fl && fl.number === number && number >= 1) dress(fl, seed); return fl; }; }
  // the trees bar the walk (the square is open stone under them)
  { const o0 = CM.isOpen; CM.isOpen = function (floor, x, y) { if (!o0(floor, x, y)) return false; return !(floor.treesIn && floor.treesIn[`${x},${y}`]); }; }
  const P = CM.Game.prototype;
  { const m0 = P.move; P.move = function (rel) { const fl = this.floor; if (fl && this.mode === "explore" && !this.perch) { const [dx, dy] = CM.DIRS[(fl.facing + rel) % 4], x = fl.pos[0] + dx, y = fl.pos[1] + dy, k = `${x},${y}`;
        if (fl.treesIn && fl.treesIn[k]) { this.sound("bump"); this.say("The trees stand too close here to push between."); return false; }
        const f = fl.features[k]; if (f && f.type === "falsedoor") { this.sound("bump"); if (f.mimic) { const rnd2 = new CM.Random(CM.hashSeed(`${this.seed}:mimic:${k}`)); const m = CM.makeMonster(CM.monsterKind("Mimic") || CM.monsterKind("Orc"), CM.storyOf(fl.number), rnd2); delete f.mimic; f.how = "bricked"; this.say("The door's handle is warm, and wet, and the door has teeth."); const th = { type: "monsters", group: [m] }; fl.things[k] = th; this.startCombat(k, th); delete fl.things[k]; return false; }
          if (f.niche) { const n = f.niche; delete f.niche; f.how = "niche"; if (n.type === "key") { this.bag.push(CM.key()); this.sound("coin"); this.say("The door opens on a niche a single step deep, and in it, on a nail: an iron key. You take it."); } else if (n.type === "chest") { fl.things[`${fl.pos[0]},${fl.pos[1]}`] = fl.things[`${fl.pos[0]},${fl.pos[1]}`] || n; this.say("The door opens on a niche a single step deep, and a small chest in it, pulled out onto the floor at your feet. (Space to open it)"); } else this.say("The door opens on a niche a single step deep, and nothing in it but dust."); return false; }
          this.say(f.how === "painted" ? "A door - painted on the stone, hinges and all, by someone with time and no way out." : f.how === "bricked" ? "A door, bricked up behind its frame long ago." : f.how === "niche" ? "The niche door, open on its empty niche." : "A door, nailed shut from the other side, and the nails rusted into the wood."); return false; } }
      const out = m0.call(this, rel); if (out && fl && this.floor === fl) { const r = CM.setPieceOf(fl, fl.pos[0], fl.pos[1]); if (r && this.ext) { const E = this.ext("setpieces"), key = `${fl.number}:${r.x0},${r.y0}:${r.template.name}`; if (!E[key]) { E[key] = true; this.say(`${r.template.name[0].toUpperCase() + r.template.name.slice(1)}. ${r.template.line}`); } } } return out; }; }
  // the bone heaps: looked at, turned over; the chest under one, and the stir
  { const u0 = P.use; P.use = function (...a) { const fl = this.floor; if (fl && this.mode === "explore" && !this.perch) { const here = `${fl.pos[0]},${fl.pos[1]}`, [dx, dy] = CM.DIRS[fl.facing], ahead = `${fl.pos[0] + dx},${fl.pos[1] + dy}`, k = fl.things[here] && fl.things[here].type === "boneheap" ? here : fl.things[ahead] && fl.things[ahead].type === "boneheap" ? ahead : null;
        if (k) { const h = fl.things[k]; if (h.chest) { const chest = h.chest, stir = h.stir; fl.things[k] = chest; this.sound("coin"); this.say("You turn the bones over - and under them, iron-bound and whole, a chest. The heaps about you shift."); if (stir && stir.length) { const rnd2 = new CM.Random(CM.hashSeed(`${this.seed}:stir:${k}`)), group = stir.map((n) => CM.makeMonster(CM.monsterKind(n) || CM.monsterKind("Skeleton"), CM.storyOf(fl.number), rnd2)); const th = { type: "monsters", group }; const sq = CM.DIRS.map(([ex, ey]) => `${fl.pos[0] + ex},${fl.pos[1] + ey}`).find((q) => { const [qx, qy] = q.split(",").map(Number); return CM.passable(fl, qx, qy) && !fl.things[q]; }) || ahead; fl.things[sq] = th; this.say("The bones stand up."); this.startCombat(sq, th); if (fl.things[sq] === th) delete fl.things[sq]; } return true; }
          this.say(h.looked ? "Bones, turned over already: nothing under them but more bones." : "A heap of bones, old and dry: ribs, a jaw, a hand still holding nothing. You turn a few over. Nothing under them."); h.looked = true; return true; } }
      // a chest's guard rises when it is opened
      const before = fl && fl.pos ? fl.things[`${fl.pos[0]},${fl.pos[1]}`] : null, guard = before && before.type === "chest" && before.guard ? before.guard.slice() : null, out = u0.apply(this, a);
      if (guard && fl && this.floor === fl && fl.things[`${fl.pos[0]},${fl.pos[1]}`] !== before && this.mode === "explore") { const rnd2 = new CM.Random(CM.hashSeed(`${this.seed}:guard:${fl.number}:${fl.pos.join(",")}`)), group = guard.map((n) => CM.makeMonster(CM.monsterKind(n) || CM.monsterKind("Orc"), Math.max(1, CM.storyOf(fl.number)), rnd2)); const [dx, dy] = CM.DIRS[fl.facing], sq = `${fl.pos[0] + dx},${fl.pos[1] + dy}`, th = { type: "monsters", group }; this.say(guard[0] === "Wolf" ? "Out of the trees, low and quick: the wolves that drink here." : guard[0] === "Drowned" ? "The water heaves, and the Drowned come up out of it for what was theirs." : "Something was guarding that."); fl.things[sq] = th; this.startCombat(sq, th); if (fl.things[sq] === th) delete fl.things[sq]; }
      return out; }; }
}
