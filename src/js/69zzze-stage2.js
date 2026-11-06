"use strict";
// Stage pieces, the second six (UPGRADE_PLAN_65.md, release 2): the Fallen Star (a crater and the star itself, a lump
// of star-iron mined with the pick), the Waterfall Hall (the aquifer through the wall into a pool: walk through the
// curtain and the torch gutters for a step; a niche behind it with a chest), the Lantern Shaft (a grate overhead in a
// small hall, daylight and weather down it, a rope ladder to a ledge with a chest), the Sunken Chapel (half flooded,
// pews under the water, a bell under it dived for: on a holy day a blessing, on any other the Drowned), the Petrified
// Wood (trees turned to stone, a stone deer and a stone adventurer, a fountain, and a chest under a basilisk's eye -
// its gaze turns one hero to stone for two turns, the fountain undoes it), and the Throne of the Hollow One (a crown
// on a sleeper's head: take it and it wakes; if the hall's roots are burning it cannot rise for three turns).
//   letters: + the star (a vein of star-iron), | the fall (a curtain), @ a grate, ^ a rope ladder, & the sunk bell,
//   % a stone deer, ! a stone adventurer, F a fountain, Y the throne.
{ const ST2 = CM.STAGE2 = { gutterSteps: 2, gazeTurns: 2, holyDays: ["dead", "bells", "sexton"], heldTurns: 3, diveMinutes: 15 };
  // ---- the meshes, added to release 1's table
  const sm0 = CM.stageModels; let made2 = null;
  const pack = (name, pos, ci, idx, palette, tags = ["stone"]) => { const lo = [0, 1, 2].map((k) => Math.min(...pos.map((p) => p[k]))), hi = [0, 1, 2].map((k) => Math.max(...pos.map((p) => p[k]))), span = lo.map((l, k) => Math.max(1e-6, hi[k] - l));
    const P = new Int16Array(pos.length * 3); pos.forEach((p, i) => { for (let k = 0; k < 3; k++) P[i * 3 + k] = Math.round((p[k] - lo[k]) / span[k] * 65534 - 32767); });
    return { name, verts: pos.length, tris: idx.length / 3, box: [lo, hi], pos: P, ci: Uint8Array.from(ci), index: Uint16Array.from(idx), palette, tags }; };
  const box = (w, h, d, c, at = [0, 0, 0]) => { const [x, y, z] = at, pos = [[-w, 0, -d], [w, 0, -d], [w, 0, d], [-w, 0, d], [-w, h, -d], [w, h, -d], [w, h, d], [-w, h, d]].map((p) => [p[0] + x, p[1] + y, p[2] + z]), ci = [c, c, c, c, c + 1, c + 1, c + 1, c + 1];
    return { pos, ci, idx: [0, 2, 1, 0, 3, 2, 4, 5, 6, 4, 6, 7, 0, 1, 5, 0, 5, 4, 1, 2, 6, 1, 6, 5, 2, 3, 7, 2, 7, 6, 3, 0, 4, 3, 4, 7] }; };
  const dome = (lat, lon, r, sy, colours, bumpy = 0) => { const pos = [], ci = [], idx = []; for (let i = 0; i <= lat; i++) { const a = Math.PI / 2 * i / lat, y = Math.cos(a) * r * sy, rr = Math.sin(a) * r; for (let j = 0; j < lon; j++) { const b = j / lon * Math.PI * 2, k = 1 + bumpy * Math.sin(j * 2.7 + i * 1.3); pos.push([Math.cos(b) * rr * k, y * (1 + bumpy * 0.3 * Math.cos(j * 1.9)), Math.sin(b) * rr * k]); ci.push(colours[Math.min(colours.length - 1, Math.floor(i / lat * colours.length))]); } }
    for (let i = 0; i < lat; i++) for (let j = 0; j < lon; j++) { const a = i * lon + j, b = i * lon + (j + 1) % lon, c = a + lon, d = b + lon; idx.push(a, b, c, b, d, c); } return { pos, ci, idx }; };
  const merge = (...parts) => { const pos = [], ci = [], idx = []; for (const P of parts) { const o = pos.length; pos.push(...P.pos); ci.push(...P.ci); idx.push(...P.idx.map((i) => i + o)); } return { pos, ci, idx }; };
  const P3 = (m) => [m.pos, m.ci, m.idx];
  const more = () => made2 || (made2 = {
    stage_star: pack("stage_star", ...P3(dome(4, 10, 0.4, 0.75, [2, 0, 1, 3], 0.12)), [[96, 104, 150], [70, 76, 120], [130, 140, 190], [50, 54, 90]], ["stone"]),
    stage_fall: pack("stage_fall", ...P3(merge(box(0.5, 0.98, 0.02, 0, [0, 0, 0]), box(0.52, 0.06, 0.12, 2, [0, 0, 0.08]))), [[200, 225, 245], [230, 240, 250], [240, 248, 255], [210, 230, 245]], ["water"]),
    stage_pew: pack("stage_pew", ...P3(merge(box(0.42, 0.05, 0.12, 0, [0, 0.18, 0]), box(0.42, 0.22, 0.03, 2, [0, 0.2, -0.12]), box(0.03, 0.2, 0.12, 0, [-0.38, 0, 0]), box(0.03, 0.2, 0.12, 0, [0.38, 0, 0]))), [[92, 68, 44], [70, 50, 32], [110, 84, 56], [60, 44, 28]], ["wood"]),
    stage_throne: pack("stage_throne", ...P3(merge(box(0.3, 0.3, 0.26, 0, [0, 0, 0]), box(0.3, 0.9, 0.06, 2, [0, 0, -0.22]), box(0.06, 0.5, 0.26, 0, [-0.3, 0.3, 0]), box(0.06, 0.5, 0.26, 0, [0.3, 0.3, 0]))), [[88, 60, 52], [66, 44, 38], [110, 72, 60], [50, 34, 30]], ["wood"]),
  });
  CM.stageModels = () => Object.assign(sm0 ? sm0() : {}, more());
  // ---- the rooms
  const SP6 = [
    { name: "the Fallen Star", min: 12, line: "The floor is broken in a ring, the flags thrown up round a hollow, and in the hollow something dark and pitted that is not stone, with a heat coming off it you feel on your face. A star came down through forty floors of rock to lie here.",
      rows: ["###########", "#.........#", "#..VVVVV..#", "#..V...V..#", "#..V.+.V..#", "#..V...V..#", "#..VVVVV..#", "#.........#", "#.........#", "#.........#", "#####D#####"] },
    { name: "the Waterfall Hall", min: 5, bands: [1, 4], fish: true, line: "The aquifer comes through the far wall in a sheet and goes down roaring into a pool, and the spray is on everything. Behind the sheet, the wall is not all wall.",
      rows: ["#####h#####", "#..|||||..#", "#..~~~~~..#", "#..~~~~~..#", "#...~~~...#", "#.........#", "#.........#", "#.........#", "#.........#", "#.........#", "#####D#####"], niches: { h: ["chest"] } },
    { name: "the Lantern Shaft", min: 2, max: 8, line: "A small square hall with a grate in its roof, and up through the grate a shaft that goes on and on, and at the top of it a coin of sky. The light comes down it in a column, and the weather with it. A rope ladder goes up to a ledge.",
      rows: ["#######", "#RRcRR#", "#..^..#", "#..@..#", "#.....#", "#.....#", "###D###"], chests: { c: { note: "on the ledge, where the rope ladder goes" } } },
    { name: "the Sunken Chapel", min: 3, bands: [1, 4], line: "A chapel with the water up to the fourth pew: the near half dry, the far half under black water with the benches still standing in it. Something under the water, in the middle, has the shape of a bell.",
      rows: ["#########", "#~~~~~~~#", "#~~~&~~~#", "#~~~~~~~#", "#~~~~~~~#", "#~~~~~~~#", "#.......#", "#.......#", "#.......#", "#.......#", "###D#####"] },
    { name: "the Petrified Wood", min: 30, bands: [6, 9], line: "Trees, stone to the last leaf, and between them a deer with its head up, stone, and a man with his hand out, stone. There is a fountain. Whatever did this to them has not gone far.",
      rows: ["###########", "#T...T...T#", "#...%.....#", "#.T...F.T.#", "#.........#", "#..T.c..T.#", "#....!....#", "#.T.....T.#", "#...T.T...#", "#.........#", "#####D#####"], chests: { c: { guard: ["Gargoyle"], note: "under the basilisk's eye" } } },
    { name: "the Throne of the Hollow One", min: 46, bands: [9], line: "A throne grown out of the root itself, and on it a shape with a crown on its head, asleep or near enough. The roots go out across the whole floor from the throne's foot, as if the hall were its hand.",
      rows: ["#########", "#RRRRRRR#", "#RRRYRRR#", "#RRRRRRR#", "#.......#", "#.......#", "#.......#", "#.......#", "#.......#", "#.......#", "#.......#", "#.......#", "###D#####"] },
  ];
  for (const r of SP6) { r.ownDice = true; if (!CM.SETPIECES.some((t) => t.name === r.name)) CM.SETPIECES.push(r); }
  const kind = (...names) => { for (const n of names) { const k = CM.monsterKind(n); if (k) return k; } return CM.MONSTERS[0]; };
  const level = (fl, k, h) => { fl.levels = fl.levels || {}; fl.levels[k] = [h, 1]; };
  const water = (fl, x, y, fish) => { fl.decor = fl.decor || []; if (!fl.decor.some((d) => d.kind === "water" && d.x === x && d.y === y)) fl.decor.push({ kind: "water", x, y, fish: Boolean(fish) }); };
  const uniqueFor = (fl) => { const b = CM.themeIndex(fl.number); return Object.keys(CM.UNIQUES).find((k) => CM.UNIQUES[k].band === b) || Object.keys(CM.UNIQUES)[0]; };
  CM.SETPIECE_LETTERS = Object.assign(CM.SETPIECE_LETTERS || {}, {
    "+": (fl, x, y, k) => { level(fl, k, CM.LEVELS ? CM.LEVELS.pit : -0.3); fl.things[k] = { type: "vein", ore: "stariron", left: CM.VEIN_SWINGS, star: true }; },
    "|": (fl, x, y, k, T) => { water(fl, x, y, Boolean(T.fish)); fl.features[k] = { type: "curtain", known: true }; },
    "@": (fl, x, y, k) => { fl.features[k] = { type: "grate", known: true }; },
    "^": (fl, x, y, k) => { fl.things[k] = { type: "ropeladder" }; },
    "&": (fl, x, y, k) => { water(fl, x, y, false); fl.things[k] = { type: "sunkbell" }; },
    "%": (fl, x, y, k) => { fl.things[k] = { type: "stonefigure", of: "Deer" }; },
    "!": (fl, x, y, k) => { fl.things[k] = { type: "stonefigure", of: "adventurer" }; },
    F: (fl, x, y, k) => { fl.features[k] = { type: "fountain", known: true }; },
    Y: (fl, x, y, k) => { fl.things[k] = { type: "throne", crown: uniqueFor(fl) }; },
  });
  // ---- the statics: the star, the fall, the pews, the throne; the Petrified Wood's plants stand still and grey
  const rs0 = CM.stageStaticsOf;
  const cache = new WeakMap();
  const roomStatics = (fl, r) => { const T = CM.SETPIECES.find((t) => t.name === r.name); if (!T) return []; const out = [], f = (x, y) => CM.floorAt(fl, x, y), fill = CM.fillOf(T, r);
    if (r.name === "the Fallen Star") { for (const [x, y, c] of fill) if (c === "+") out.push({ model: "stage_star", x: x + 0.5, y: f(x, y), z: y + 0.5, yaw: 0.7, scale: 1, sway: 0, height: 0.3, shade: 1, kind: "stone", raw: true }); }
    else if (r.name === "the Waterfall Hall") { for (const [x, y, c] of fill) if (c === "|") out.push({ model: "stage_fall", x: x + 0.5, y: f(x, y), z: y + 0.06, yaw: 0, scale: 1, sway: 0.1, height: 0.98, shade: 1, kind: "water", raw: true }); }
    else if (r.name === "the Sunken Chapel") { const wet = fill.filter(([, , c]) => c === "~" || c === "&"); for (const [x, y] of wet) if ((y - r.y0) % 2 === 0 && x !== r.x0 + Math.floor((r.x1 - r.x0) / 2)) out.push({ model: "stage_pew", x: x + 0.5, y: f(x, y) - 0.1, z: y + 0.5, yaw: 0, scale: 1, sway: 0, height: 0.3, shade: 0.6, kind: "wood", raw: true }); }
    else if (r.name === "the Throne of the Hollow One") { for (const [x, y, c] of fill) if (c === "Y") out.push({ model: "stage_throne", x: x + 0.5, y: f(x, y), z: y + 0.5, yaw: 0, scale: 1, sway: 0, height: 0.9, shade: 0.9, kind: "wood", raw: true }); }
    return out; };
  CM.stageStaticsOf = (game, fl, at, reach) => { const out = rs0 ? rs0(game, fl, at, reach) : []; if (!fl || !(fl.number >= 1) || !fl.rooms || !fl.grid) return out; let all = cache.get(fl); if (!all) { all = []; for (const r of fl.rooms) all.push(...roomStatics(fl, r)); cache.set(fl, all); } const [ax, ay] = at || fl.pos, R = (reach || 12) + 4; for (const p of all) if (Math.abs(p.x - ax) + Math.abs(p.z - ay) <= R) out.push(p); return out; };
  { const pi0 = CM.plantInstancesOf; CM.plantInstancesOf = (game, fl, at, reach, density) => { const out = pi0(game, fl, at, reach, density); if (fl && fl.number >= 1 && fl.rooms) { const stone = fl.rooms.filter((r) => r.name === "the Petrified Wood"); if (stone.length) for (const p of out) { if (/^stage_/.test(p.model)) continue; const x = Math.floor(p.x), z = Math.floor(p.z); if (stone.some((r) => x >= r.x0 && x <= r.x1 && z >= r.y0 && z <= r.y1)) { p.sway = 0; p.shade = Math.min(p.shade === undefined ? 1 : p.shade, 0.55); p.stone = true; } } } return out; }; }
  // ---- the rooms' rules
  const P = CM.Game.prototype;
  const groupAt = (game, fl, group) => { const [dx, dy] = CM.DIRS[fl.facing], sq = `${fl.pos[0] + dx},${fl.pos[1] + dy}`, th = { type: "monsters", group }; const was = fl.things[sq]; fl.things[sq] = th; game.startCombat(sq, th); if (fl.things[sq] === th) { if (was) fl.things[sq] = was; else delete fl.things[sq]; } };
  const LINES = { ropeladder: () => "A rope ladder, knotted and old, going up to the ledge. It holds.", sunkbell: (t) => (t.rung ? "The bell under the water, rung once." : "Under the water, a bell, green and whole, lying on its side where it fell when the roof came in. (Space to dive and ring it)"),
    stonefigure: (t) => (t.of === "Deer" ? "A deer, stone, its head up and its ears forward, as if it heard you a hundred years ago and is still listening." : "A man in a traveller's coat, stone, his hand out in front of him to ward something off. His face is not calm."),
    throne: (t) => (t.taken ? "The root throne, empty." : "On the throne, asleep or near it, the Hollow One, and on its head a crown that is not asleep at all. (Space to take it)") };
  { const l0 = P.look; P.look = function (...a) { const out = l0.apply(this, a); const fl = this.floor; if (fl && this.mode === "explore" && !this.perch && fl.things) { const here = `${fl.pos[0]},${fl.pos[1]}`, [dx, dy] = CM.DIRS[fl.facing], ahead = `${fl.pos[0] + dx},${fl.pos[1] + dy}`; for (const k of [here, ahead]) { const t = fl.things[k]; if (t && LINES[t.type]) { this.say(LINES[t.type](t)); break; } if (t && t.type === "vein" && t.star) { this.say("The star itself: a lump of star-iron the size of a barrel, pitted and dark, still warm. A pick would have it. " + (t.left < CM.VEIN_SWINGS ? "Part of it is worked already." : "")); break; } } } return out; }; }
  { const u0 = P.use; P.use = function (...a) { const fl = this.floor; if (fl && this.mode === "explore" && !this.perch) { const here = `${fl.pos[0]},${fl.pos[1]}`, [dx, dy] = CM.DIRS[fl.facing], ahead = `${fl.pos[0] + dx},${fl.pos[1] + dy}`;
        for (const k of [here, ahead]) { const t = fl.things[k]; if (!t) continue;
          if (t.type === "sunkbell") { if (t.rung) { this.say("The bell, rung once; the water over it is still."); return true; } t.rung = true; this.clock = (this.clock || 0) + ST2.diveMinutes; const holy = ST2.holyDays.some((id) => CM.festivalIs(this, id)); this.sound("lever");
            if (holy) { this.blessedUntil = fl.number + (CM.TITHE_FLOORS || 5); this.say("You go down into the black water and find the bell by feel and strike it with the heel of your hand, and the note comes up through the water into your chest. It is a holy day. The chapel remembers what it was for: the party is blessed for the band."); this.emit("change"); return true; }
            const R = new CM.Random(CM.hashSeed(`${this.seed}:chapelbell:${fl.number}`)), group = []; for (let i = 0; i < 3; i++) group.push(CM.makeMonster(kind("Drowned", "Zombie"), Math.max(1, CM.storyOf(fl.number)), R)); this.say("You go down into the black water and find the bell by feel and strike it, and the note goes out through the water - and the water answers: the drowned of the chapel come up out of the far pews."); groupAt(this, fl, group); return true; }
          if (t.type === "throne") { if (t.taken) { this.say("The root throne, empty."); return true; } t.taken = true; const relic = CM.makeUnique(t.crown); this.bag.push(relic); this.sound("coin"); const burning = CM.rootsBurning ? CM.rootsBurning(this, fl) : 0, R = new CM.Random(CM.hashSeed(`${this.seed}:throne:${fl.number}`));
            const king = CM.makeMonster(kind("Hollow One", "Rootling"), Math.max(1, CM.storyOf(fl.number)), R), group = [king, CM.makeMonster(kind("Rootling", "Giant Rat"), Math.max(1, CM.storyOf(fl.number)), R), CM.makeMonster(kind("Rootling", "Giant Rat"), Math.max(1, CM.storyOf(fl.number)), R)];
            if (burning) { king.held = ST2.heldTurns; this.say(`You lift ${relic.name} off its head, and it wakes - and cannot rise: the roots it sits in are burning, and it screams through them with no mouth, held fast for a while.`); } else this.say(`You lift ${relic.name} off its head. The eyes open. The roots across the whole floor move at once, like fingers closing.`); this.emit("change"); groupAt(this, fl, group); if (burning && this.mode === "combat") for (const m of this.foes) if (m === king) m.held = ST2.heldTurns;   /* (after the fight is set up: it cannot rise) */ return true; }
          if (t.type === "stonefigure" || t.type === "ropeladder") { this.say(LINES[t.type](t)); return true; } }
        const f = fl.features[here]; if (f && f.type === "fountain") { const r = CM.setPieceOf(fl, fl.pos[0], fl.pos[1]); if (r && r.template.name === "the Petrified Wood") { let cured = 0; for (const h of this.party) if (h.status && h.status.stone) { delete h.status.stone; cured++; } this.sound("heal"); this.say(cured ? "The fountain's water on the stone skin, and the stone goes grey and soft and is skin again. The basilisk's work undone." : "The fountain runs clear and cold. Whatever the basilisk does, this undoes; you may want it yet."); this.emit("change"); return true; } } }
      return u0.apply(this, a); }; }
  // the curtain: through the fall, and the torch gutters for a step or two
  { const ar0 = P.arrive; P.arrive = function (f, k) { if (f && f.type === "curtain") { this.gutter = Math.max(this.gutter || 0, ST2.gutterSteps); this.sound("splash"); this.say("Through the fall: the water hits like a blow and the torch goes to a hiss and a smell, and for a step or two there is only the roar."); this.emit("change"); return; } return ar0.call(this, f, k); }; }
  // the basilisk's gaze: in the Petrified Wood, the chest's guard turns one hero to stone for two turns
  { const sc0 = P.startCombat; P.startCombat = function (key, thing, theyCame) { const out = sc0.call(this, key, thing, theyCame); const fl = this.floor; if (fl && this.mode === "combat" && thing && thing.group && thing.group.some((m) => m.kind === "Gargoyle" || m.name === "Gargoyle")) { const r = CM.setPieceOf(fl, fl.pos[0], fl.pos[1]); if (r && r.template.name === "the Petrified Wood") { const E = this.ext("basilisk"); if (!E[fl.number]) { E[fl.number] = true; const h = this.alive()[0]; if (h) { h.status = h.status || {}; h.status.stone = ST2.gazeTurns; this.say(`The basilisk's eye opens on ${h.name}, and ${h.name} goes grey from the feet up and stands as the deer stands. Two turns, if the fountain is near.`); } } } } return out; }; }
}
