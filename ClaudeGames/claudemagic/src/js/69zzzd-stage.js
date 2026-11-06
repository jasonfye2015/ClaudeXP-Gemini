"use strict";
// Stage pieces (UPGRADE_PLAN_65.md, release 1): rooms whose point is a sight built from several squares - meshes made
// here in code, in the plants' model shape (as the clutter's cones are), and placed by the room: the Giant's Ribcage
// (ribs arching over the whole room, a skull the size of a cart at the far end with a chest between its teeth - taken
// at night, the Bone Colossus kind stirs), the Shipwreck (a hull broken through the Drowned Town's vault, water round
// it, fish, a deck to walk, the captain's chart in a chest, and a bell on the mast that calls the Drowned down off the
// deck), the Rope Bridge (a chasm either side of one swaying bridge of planks - the chasm is never walked into - and a
// chest at the far end), and the Great Mushroom (one cap the size of the room on a stalk, climbed by its steps: from
// the top the floor for twelve squares round is seen; glowcaps at its foot, Sporelings asleep under it).
//   CM.stageModels() -> { name: model }   the meshes;  CM.stageStaticsOf(game, fl, at, reach) -> instances (merged into
//   CM.plantInstancesOf);  letters: 0 the skull, 8 the mast's bell, M a sleeping group of the band, A the cap's top,
//   _ a chasm square (solid, deep), = a plank of the bridge.
{ const ST = CM.STAGE = { chasm: -0.9, ribEvery: 2, hullLength: 7, capScale: 1.8, capTop: 12 };
  // ---- meshes: positions as floats, a colour index a vertex, triangles; packed the plants' way (int16 over the box)
  const pack = (name, pos, ci, idx, palette, tags = ["stone"]) => { const lo = [0, 1, 2].map((k) => Math.min(...pos.map((p) => p[k]))), hi = [0, 1, 2].map((k) => Math.max(...pos.map((p) => p[k]))), span = lo.map((l, k) => Math.max(1e-6, hi[k] - l));
    const P = new Int16Array(pos.length * 3); pos.forEach((p, i) => { for (let k = 0; k < 3; k++) P[i * 3 + k] = Math.round((p[k] - lo[k]) / span[k] * 65534 - 32767); });
    return { name, verts: pos.length, tris: idx.length / 3, box: [lo, hi], pos: P, ci: Uint8Array.from(ci), index: Uint16Array.from(idx), palette, tags }; };
  // a tube along a path of points, n sides, radius r (a function of t), colour by side
  const tube = (path, n, r, colours) => { const pos = [], ci = [], idx = [];
    for (let i = 0; i < path.length; i++) { const p = path[i], q = path[Math.min(path.length - 1, i + 1)], o = path[Math.max(0, i - 1)]; let d = [q[0] - o[0], q[1] - o[1], q[2] - o[2]]; const L = Math.hypot(...d) || 1; d = d.map((v) => v / L);
      const up = Math.abs(d[1]) > 0.9 ? [1, 0, 0] : [0, 1, 0], a = [d[1] * up[2] - d[2] * up[1], d[2] * up[0] - d[0] * up[2], d[0] * up[1] - d[1] * up[0]], la = Math.hypot(...a) || 1, A = a.map((v) => v / la), B = [d[1] * A[2] - d[2] * A[1], d[2] * A[0] - d[0] * A[2], d[0] * A[1] - d[1] * A[0]], rr = typeof r === "function" ? r(i / (path.length - 1)) : r;
      for (let s = 0; s < n; s++) { const ang = s / n * Math.PI * 2, c = Math.cos(ang) * rr, sn = Math.sin(ang) * rr; pos.push([p[0] + A[0] * c + B[0] * sn, p[1] + A[1] * c + B[1] * sn, p[2] + A[2] * c + B[2] * sn]); ci.push(colours[s % colours.length]); } }
    for (let i = 0; i + 1 < path.length; i++) for (let s = 0; s < n; s++) { const a = i * n + s, b = i * n + (s + 1) % n, c = a + n, d = b + n; idx.push(a, c, b, b, c, d); }
    return { pos, ci, idx }; };
  const merge = (...parts) => { const pos = [], ci = [], idx = []; for (const P of parts) { const o = pos.length; pos.push(...P.pos); ci.push(...P.ci); idx.push(...P.idx.map((i) => i + o)); } return { pos, ci, idx }; };
  const box = (w, h, d, c, at = [0, 0, 0]) => { const [x, y, z] = at, pos = [[-w, 0, -d], [w, 0, -d], [w, 0, d], [-w, 0, d], [-w, h, -d], [w, h, -d], [w, h, d], [-w, h, d]].map((p) => [p[0] + x, p[1] + y, p[2] + z]), ci = [c, c, c, c, c + 1, c + 1, c + 1, c + 1];
    const idx = [0, 2, 1, 0, 3, 2, 4, 5, 6, 4, 6, 7, 0, 1, 5, 0, 5, 4, 1, 2, 6, 1, 6, 5, 2, 3, 7, 2, 7, 6, 3, 0, 4, 3, 4, 7]; return { pos, ci, idx }; };
  // a dome (or a sphere's slice) of lat x lon, radius r, from angle a0 to a1 (0 the top), squashed by sy
  const dome = (lat, lon, r, a0, a1, sy, colours, at = [0, 0, 0]) => { const pos = [], ci = [], idx = []; for (let i = 0; i <= lat; i++) { const a = a0 + (a1 - a0) * i / lat, y = Math.cos(a) * r * sy, rr = Math.sin(a) * r; for (let j = 0; j < lon; j++) { const b = j / lon * Math.PI * 2; pos.push([at[0] + Math.cos(b) * rr, at[1] + y, at[2] + Math.sin(b) * rr]); ci.push(colours[Math.min(colours.length - 1, Math.floor(i / lat * colours.length))]); } }
    for (let i = 0; i < lat; i++) for (let j = 0; j < lon; j++) { const a = i * lon + j, b = i * lon + (j + 1) % lon, c = a + lon, d = b + lon; idx.push(a, b, c, b, d, c); } return { pos, ci, idx }; };
  const arc = (halfW, h, n, r, colours) => { const path = []; for (let i = 0; i <= n; i++) { const t = i / n, a = Math.PI * t; path.push([-Math.cos(a) * halfW, Math.sin(a) * h, 0]); } return tube(path, 6, r, colours); };
  const BONE = [[214, 206, 186], [190, 182, 162], [232, 226, 210], [160, 150, 132]], WOOD = [[92, 68, 44], [70, 50, 32], [120, 92, 60], [52, 38, 24]], ROPE = [[150, 128, 90], [120, 100, 70]], CAP = [[150, 72, 56], [172, 92, 72], [118, 56, 44], [200, 186, 160]], STALK = [[226, 214, 190], [200, 188, 164]];
  let made = null;
  CM.stageModels = () => made || (made = {
    stage_rib: pack("stage_rib", ...Object.values(arc(1.0, 0.26, 14, (t) => 0.028 + 0.012 * Math.sin(t * Math.PI), [0, 1, 2, 1, 0, 3])).slice(0, 3), BONE, ["stone"]),
    stage_skull: pack("stage_skull", ...Object.values(merge(dome(6, 10, 0.42, 0, Math.PI * 0.72, 0.9, [2, 0, 0, 1, 3], [0, 0.46, 0]), box(0.3, 0.14, 0.22, 1, [0, 0.0, 0.1]))).slice(0, 3), BONE, ["stone"]),
    stage_hull: pack("stage_hull", ...Object.values((() => { const path = []; for (let i = 0; i <= 8; i++) { const t = i / 8; path.push([0, 0.02, (t - 0.5) * 1.0]); } return tube(path, 8, (t) => 0.12 * Math.sin(Math.PI * Math.min(1, t * 1.1)) + 0.02, [0, 1, 0, 1, 2, 1, 0, 3]); })()).slice(0, 3), WOOD, ["wood"]),
    stage_mast: pack("stage_mast", ...Object.values(merge(tube([[0, 0, 0], [0, 0.97, 0]], 6, 0.03, [0, 1, 2, 1, 0, 3]), tube([[-0.42, 0.72, 0], [0.42, 0.72, 0]], 5, 0.02, [1, 0, 1, 2, 3]))).slice(0, 3), WOOD, ["wood"]),
    stage_plank: pack("stage_plank", ...Object.values(merge(box(0.34, 0.03, 0.46, 0, [0, 0, 0]), tube([[-0.4, 0.5, -0.5], [-0.4, 0.46, 0], [-0.4, 0.5, 0.5]], 4, 0.012, [0, 1, 0, 1]), tube([[0.4, 0.5, -0.5], [0.4, 0.46, 0], [0.4, 0.5, 0.5]], 4, 0.012, [0, 1, 0, 1]))).slice(0, 3), WOOD.slice(0, 2).concat(ROPE), ["wood"]),
    stage_stalk: pack("stage_stalk", ...Object.values(tube([[0, 0, 0], [0, 0.22, 0], [0, 0.45, 0]], 8, (t) => 0.26 - 0.06 * t, [0, 1, 0, 1, 0, 1, 0, 1])).slice(0, 3), STALK, ["plant"]),
    stage_cap: pack("stage_cap", ...Object.values(merge(dome(5, 14, 1.0, 0, Math.PI * 0.5, 0.42, [3, 1, 0, 0, 2], [0, 0.34, 0]), dome(1, 14, 1.0, Math.PI * 0.5, Math.PI * 0.62, 0.42, [2, 2], [0, 0.34, 0]))).slice(0, 3), CAP, ["plant"]),
  });
  // ---- the rooms
  const SP5 = [
    { name: "the Giant's Ribcage", min: 4, bands: [0, 8], bats: true, line: "A colossus fell here, or was laid here, and the hall was cut round its bones: the ribs go up over you in two rows and meet under the roof, and at the far end a skull the size of a cart looks back down the hall with something between its teeth.",
      rows: ["#########", "#...0...#", "#.......#", "#.......#", "#.......#", "#.......#", "#.......#", "#.......#", "#.......#", "#.......#", "#.......#", "#.......#", "#.......#", "#.......#", "###D#####"] },
    { name: "the Shipwreck", min: 22, bands: [4], fish: true, line: "A ship came down through the vault's roof, stern first, and lies broken in the black water with its mast still up. The Drowned stand on the deck in a row, as still as the mast, and the water laps at the hull.",
      rows: ["###########", "#~~~~~~~~~#", "#~~~RRR~~~#", "#~~~RRR~~~#", "#~~~R8R~~~#", "#~~~RRR~~~#", "#~~~RcR~~~#", "#~~~RRR~~~#", "#~~~~~~~~~#", "#...~~~...#", "#####D#####"], chests: { c: { item: "chart", note: "in the captain's cabin" } } },
    { name: "the Rope Bridge", min: 6, line: "The floor stops. Across a dark that goes down farther than your light, one bridge of planks and rope, and at its far end, something on a rope of its own.",
      rows: ["#####", "#...#", "#_=_#", "#_=_#", "#_=_#", "#_=_#", "#_=_#", "#_=_#", "#_=_#", "#_=_#", "#_=_#", "#_=_#", "#_=_#", "#_=_#", "#_=_#", "#.c.#", "###D#"], chests: { c: { note: "hauled up on a rope from under the bridge's end" } } },
    { name: "the Great Mushroom", min: 26, bands: [5], line: "One mushroom, as wide as the hall, on a stalk you could not reach round, its cap up under the roof with glowcaps burning at its foot. Steps are cut into the stalk. Under the cap, something small breathes slow.",
      rows: ["###########", "#.........#", "#..G...G..#", "#...RRR...#", "#...RAR...#", "#...RRR...#", "#.M.....G.#", "#..G......#", "#.........#", "#####D#####"] },
  ];
  for (const r of SP5) { r.ownDice = true; if (!CM.SETPIECES.some((t) => t.name === r.name)) CM.SETPIECES.push(r); }
  const kind = (...names) => { for (const n of names) { const k = CM.monsterKind(n); if (k) return k; } return CM.MONSTERS[0]; };
  const level = (fl, k, h) => { fl.levels = fl.levels || {}; fl.levels[k] = [h, 1]; };
  CM.SETPIECE_LETTERS = Object.assign(CM.SETPIECE_LETTERS || {}, {
    "0": (fl, x, y, k, T, R) => { fl.things[k] = { type: "skull", chest: { type: "chest", gold: R.int(40, 90) * Math.max(1, CM.storyOf(fl.number)), items: [CM.makeItem(CM.storyOf(fl.number), R, undefined, 3), CM.makeItem(CM.storyOf(fl.number), R, undefined, 2)], trap: null, note: "from between the giant's teeth" } }; },
    "8": (fl, x, y, k) => { level(fl, k, CM.LEVELS ? CM.LEVELS.dais : 0.3); fl.things[k] = { type: "mastbell" }; },
    M: (fl, x, y, k, T, R) => { const group = []; for (let i = 0; i < 3; i++) group.push(CM.makeMonster(kind("Sporeling", "Giant Rat"), Math.max(1, CM.storyOf(fl.number)), R)); fl.things[k] = { type: "monsters", group, asleep: true, still: true }; },
    A: (fl, x, y, k) => { level(fl, k, CM.LEVELS ? CM.LEVELS.raised : 0.6); fl.features[k] = { type: "captop", known: true }; },
    _: (fl, x, y, k) => { fl.chasm = fl.chasm || {}; fl.chasm[k] = true; level(fl, k, ST.chasm); },
  });
  // the Great Mushroom's disc is raised a step more than a dais, so the cap sits round the party's feet
  { const d0 = CM.dressSetPieces; CM.dressSetPieces = function (fl, seed) { const out = d0.call(this, fl, seed); if (fl && fl.rooms) for (const r of fl.rooms) if (r.name === "the Great Mushroom") { const T = CM.SETPIECES.find((t) => t.name === r.name); if (!T) continue; for (const [x, y, c] of CM.fillOf(T, r)) if (c === "R") level(fl, `${x},${y}`, CM.LEVELS ? CM.LEVELS.raised : 0.6); } return out; };
    const mf0 = CM.makeFloor; CM.makeFloor = function (number, seed, gen) { const fl = mf0.call(this, number, seed, gen); if (fl && fl.number === number && number >= 1 && fl.rooms && fl.rooms.some((r) => r.name === "the Great Mushroom")) { const T = CM.SETPIECES.find((t) => t.name === "the Great Mushroom"); for (const r of fl.rooms) if (r.name === T.name) for (const [x, y, c] of CM.fillOf(T, r)) if (c === "R") level(fl, `${x},${y}`, CM.LEVELS ? CM.LEVELS.raised : 0.6); } return fl; }; }
  { const i0 = CM.setPieceItem; CM.setPieceItem = (what, number) => (what === "chart" ? Object.assign(CM.scroll("mapping"), { name: "The Captain's Chart" }) : i0(what, number)); }
  // the chasm is never walked into
  { const o0 = CM.isOpen; CM.isOpen = function (floor, x, y) { if (!o0(floor, x, y)) return false; return !(floor.chasm && floor.chasm[`${x},${y}`]); }; }
  // ---- the statics: by room, cached a floor
  const cache = new WeakMap();
  const roomStatics = (fl, r) => { const T = CM.SETPIECES.find((t) => t.name === r.name); if (!T) return []; const out = [], W = r.x1 - r.x0 + 1, H = r.y1 - r.y0 + 1, cx = r.x0 + W / 2, cz = r.y0 + H / 2, f = (x, y) => CM.floorAt(fl, Math.floor(x), Math.floor(y));
    if (r.name === "the Giant's Ribcage") { const long = H >= W, span = long ? W : H; for (let i = 1; i < (long ? H : W) - 1; i += ST.ribEvery) { const x = long ? cx : r.x0 + i + 0.5, z = long ? r.y0 + i + 0.5 : cz; out.push({ model: "stage_rib", x, y: f(x, z), z, yaw: long ? 0 : Math.PI / 2, scale: span / 2, sway: 0, height: 0.95, shade: 0.95, kind: "stone", raw: true }); }
      for (const [x, y, c] of CM.fillOf(T, r)) if (c === "0") out.push({ model: "stage_skull", x: x + 0.5, y: f(x, y), z: y + 0.5, yaw: long ? Math.PI : Math.PI / 2, scale: 1.0, sway: 0, height: 0.9, shade: 1, kind: "stone", raw: true }); }
    else if (r.name === "the Shipwreck") { const deck = CM.fillOf(T, r).filter(([, , c]) => "R8c".includes(c)), zs = deck.map(([, y]) => y), xs = deck.map(([x]) => x), mz = (Math.min(...zs) + Math.max(...zs) + 1) / 2, mx = (Math.min(...xs) + Math.max(...xs) + 1) / 2, len = Math.max(...zs) - Math.min(...zs) + 2;
      out.push({ model: "stage_hull", x: mx, y: -0.02, z: mz, yaw: 0, scale: len, sway: 0, height: 0.9, shade: 0.9, kind: "wood", raw: true }); for (const [x, y, c] of deck) if (c === "8") out.push({ model: "stage_mast", x: x + 0.5, y: f(x, y), z: y + 0.5, yaw: 0, scale: 1, sway: 0.15, height: 0.97, shade: 1, kind: "wood", raw: true }); }
    else if (r.name === "the Rope Bridge") { for (const [x, y, c] of CM.fillOf(T, r)) if (c === "=") out.push({ model: "stage_plank", x: x + 0.5, y: f(x, y) + 0.005, z: y + 0.5, yaw: W > H ? Math.PI / 2 : 0, scale: 1, sway: 0.08, height: 0.55, shade: 0.95, kind: "wood", raw: true }); }
    else if (r.name === "the Great Mushroom") { const top = CM.fillOf(T, r).find(([, , c]) => c === "A"); if (top) { const x = top[0] + 0.5, z = top[1] + 0.5; out.push({ model: "stage_stalk", x, y: 0, z, yaw: 0, scale: 1.1, sway: 0, height: 0.5, shade: 1, kind: "plant", raw: true }); out.push({ model: "stage_cap", x, y: 0.12, z, yaw: 0, scale: ST.capScale, sway: 0.02, height: 0.78, shade: 1, kind: "plant", raw: true }); } }
    return out; };
  CM.stageStaticsOf = (game, fl, at, reach) => { if (!fl || !(fl.number >= 1) || !fl.rooms || !fl.grid) return []; let all = cache.get(fl); if (!all) { all = []; for (const r of fl.rooms) all.push(...roomStatics(fl, r)); cache.set(fl, all); } const [ax, ay] = at || fl.pos, R = (reach || 12) + 4; return all.filter((p) => Math.abs(p.x - ax) + Math.abs(p.z - ay) <= R); };
  { const pi0 = CM.plantInstancesOf; CM.plantInstancesOf = (game, fl, at, reach, density) => { const out = pi0(game, fl, at, reach, density); if (fl && fl.number >= 1 && fl.rooms) for (const p of CM.stageStaticsOf(game, fl, at, reach)) out.push(p); return out; }; }
  { const t0 = CM.plantTintOf; CM.plantTintOf = (game, fl, model) => (/^stage_/.test(model) ? null : t0(game, fl, model)); }
  // ---- the rooms' rules
  const P = CM.Game.prototype;
  const groupAt = (game, fl, group) => { const [dx, dy] = CM.DIRS[fl.facing], sq = `${fl.pos[0] + dx},${fl.pos[1] + dy}`, th = { type: "monsters", group }; const was = fl.things[sq]; fl.things[sq] = th; game.startCombat(sq, th); if (fl.things[sq] === th) { if (was) fl.things[sq] = was; else delete fl.things[sq]; } };
  const LINES = { skull: (t) => (t.chest ? "A skull the size of a cart, and between its teeth, iron-bound, a chest. The teeth are each as long as your arm. (Space to take it)" : "The giant's skull, its teeth parted on nothing now."), mastbell: () => "The ship's bell, green with the water, hung at the mast's foot. The Drowned on the deck have not looked at you yet. (Space to ring it)" };
  { const l0 = P.look; P.look = function (...a) { const out = l0.apply(this, a); const fl = this.floor; if (fl && this.mode === "explore" && !this.perch && fl.things) { const here = `${fl.pos[0]},${fl.pos[1]}`, [dx, dy] = CM.DIRS[fl.facing], ahead = `${fl.pos[0] + dx},${fl.pos[1] + dy}`; for (const k of [here, ahead]) { const t = fl.things[k]; if (t && LINES[t.type]) { this.say(LINES[t.type](t)); break; } } } return out; }; }
  { const u0 = P.use; P.use = function (...a) { const fl = this.floor; if (fl && this.mode === "explore" && !this.perch) { const here = `${fl.pos[0]},${fl.pos[1]}`, [dx, dy] = CM.DIRS[fl.facing], ahead = `${fl.pos[0] + dx},${fl.pos[1] + dy}`;
        for (const k of [here, ahead]) { const t = fl.things[k]; if (!t) continue;
          if (t.type === "skull") { if (!t.chest) { this.say("The giant's skull, its teeth parted on nothing now."); return true; } const chest = t.chest; t.chest = null; fl.things[k] = Object.assign(chest, { skull: true }); this.sound("grind"); const night = CM.isNight ? CM.isNight(this) : false;
            if (night) { const R = new CM.Random(CM.hashSeed(`${this.seed}:colossus:${fl.number}`)); this.say("You work the chest out from between the teeth. It comes free with a crack - and in the dark the ribs over you shift, one and then the next, as the thing they belonged to remembers it had a chest."); if (this.count) this.count("colossiWoken", 1); groupAt(this, fl, [CM.makeMonster(kind("Bone Colossus", "Skeleton"), Math.max(1, CM.storyOf(fl.number)), R)]); return true; }
            this.say("You work the chest out from between the teeth. It comes free with a crack, and nothing else moves. By daylight, even down here, the dead keep their hours."); this.emit("change"); return true; }
          if (t.type === "mastbell") { if (t.rung) { this.say("The bell, rung once; the deck is empty now."); return true; } t.rung = true; this.sound("lever"); const R = new CM.Random(CM.hashSeed(`${this.seed}:mastbell:${fl.number}`)), group = []; for (let i = 0; i < 3; i++) group.push(CM.makeMonster(kind("Drowned", "Zombie"), Math.max(1, CM.storyOf(fl.number)), R)); this.say("The bell's note goes out over the water, flat and green, and the row on the deck turns its heads together and comes down the hull toward you."); if (this.count) this.count("bellsRung", 1); groupAt(this, fl, group); return true; } } }
      return u0.apply(this, a); }; }
  // the cap's top: the floor seen for twelve squares round; the bridge sways under every step
  { const ar0 = P.arrive; P.arrive = function (f, k) { if (f && f.type === "captop") { const fl = this.floor, [cx, cy] = k.split(",").map(Number), N = fl.grid.length; fl.seen = fl.seen || []; const have = new Set(fl.seen.map(([x, y]) => `${x},${y}`)); let added = 0; for (let y = Math.max(0, cy - ST.capTop); y <= Math.min(N - 1, cy + ST.capTop); y++) for (let x = Math.max(0, cx - ST.capTop); x <= Math.min(N - 1, cx + ST.capTop); x++) { if (Math.abs(x - cx) + Math.abs(y - cy) > ST.capTop) continue; const kk = `${x},${y}`; if (!have.has(kk)) { have.add(kk); fl.seen.push([x, y]); added++; } }
        if (!f.stood) { f.stood = true; this.say(`From the cap's top the hall opens out under you, the roof a hand over your heads: the ways run off in every direction, and you see them all${added ? " (the map has them now)" : ""}.`); } this.emit("change"); this.dirty = true; return; } return ar0.call(this, f, k); }; }
  { const m0 = P.move; P.move = function (rel) { const out = m0.call(this, rel); const fl = this.floor; if (out && fl && fl.chasm && fl.number >= 1) { const k = `${fl.pos[0]},${fl.pos[1]}`, [dx, dy] = CM.DIRS[(fl.facing + 1) % 4]; if (fl.chasm[`${fl.pos[0] + dx},${fl.pos[1] + dy}`] || fl.chasm[`${fl.pos[0] - dx},${fl.pos[1] - dy}`]) { this.emit("sway", { k }); if (!fl.swayed) { fl.swayed = true; this.say("The bridge takes your weight and sways, and the ropes creak, and under you the dark goes down and does not stop."); } } } return out; }; }
}
