"use strict";
// Puzzle rooms (v37.1, UPGRADE_PLAN_32.md): about one floor in five from the second down holds a puzzle, made fresh for
// it by the seed and always solvable. The statues: an altar and three statues about it, each turned a quarter at a
// time with Space; when all three look toward the altar a chest rises from the floor beside it. The sunbeam: a shaft of
// daylight down through a crack in the roof, two mirrors in its way (each tilted one way or the other with Space) and a
// sun-plate; when the beam, bounced off both, falls on the plate, a chest rises there. The chest is better than the
// floor's own. game.beamPath() is the beam's way now (the window draws it, 76zzzzzzp-puzzles.js).
//   floor.puzzle = {kind, chestAt, solved};  things: altar, statue {face, want}, sunshaft {dir}, mirror {tilt}, sunplate
{ const key = (x, y) => `${x},${y}`, D = () => CM.DIRS;
  CM.PUZZLE_EVERY = 5;
  const free = (fl, x, y) => fl.grid[y] && fl.grid[y][x] === 0 && !fl.things[key(x, y)] && !(fl.features || {})[key(x, y)] && !(fl.pos[0] === x && fl.pos[1] === y);
  const towards = (from, to) => { const dx = to[0] - from[0], dy = to[1] - from[1]; return Math.abs(dx) >= Math.abs(dy) ? (dx > 0 ? 1 : 3) : (dy > 0 ? 2 : 0); };
  const layStatues = (fl, rnd) => { const N = fl.grid.length, cells = []; for (let y = 2; y < N - 2; y++) for (let x = 2; x < N - 2; x++) if (free(fl, x, y)) cells.push([x, y]);
    for (let tries = 0; tries < 60; tries++) { const A = cells[rnd.int(0, cells.length - 1)]; if (!A) return false; const ring = cells.filter(([x, y]) => { const d = Math.abs(x - A[0]) + Math.abs(y - A[1]); return d >= 2 && d <= 3; });
      if (ring.length < 4) continue; const picks = []; for (const c of rnd.shuffle(ring.slice())) { if (picks.length >= 3) break; if (picks.every((p) => Math.abs(p[0] - c[0]) + Math.abs(p[1] - c[1]) >= 2)) picks.push(c); }
      if (picks.length < 3) continue; const chest = cells.find(([x, y]) => Math.abs(x - A[0]) + Math.abs(y - A[1]) === 1 && !picks.some((p) => p[0] === x && p[1] === y)); if (!chest) continue;
      fl.things[key(...A)] = { type: "altar" }; picks.forEach((p, i) => { const want = towards(p, A); fl.things[key(...p)] = { type: "statue", face: (want + 1 + (i % 3)) % 4, want }; });
      fl.puzzle = { kind: "statues", chestAt: key(...chest), solved: false }; return true; } return false; };
  const layBeam = (fl, rnd) => { const N = fl.grid.length, open = (x, y) => fl.grid[y] && fl.grid[y][x] === 0, run = (x, y, d) => { const out = []; let cx = x + D()[d][0], cy = y + D()[d][1]; while (open(cx, cy) && out.length < 8) { out.push([cx, cy]); cx += D()[d][0]; cy += D()[d][1]; } return out; };
    for (let tries = 0; tries < 300; tries++) { const S = [rnd.int(2, N - 3), rnd.int(2, N - 3)]; if (!free(fl, ...S)) continue; const d1 = rnd.int(0, 3), r1 = run(S[0], S[1], d1); if (r1.length < 3) continue;
      const M1 = r1[rnd.int(1, r1.length - 1)], d2 = (d1 + (rnd.chance(0.5) ? 1 : 3)) % 4, r2 = run(M1[0], M1[1], d2); if (r2.length < 3) continue;
      const M2 = r2[rnd.int(1, r2.length - 1)], d3 = (d2 + (rnd.chance(0.5) ? 1 : 3)) % 4, r3 = run(M2[0], M2[1], d3); if (r3.length < 2) continue; const P = r3[rnd.int(1, r3.length - 1)];
      const all = [S, M1, M2, P], path = [...r1.slice(0, r1.findIndex((c) => c[0] === M1[0] && c[1] === M1[1])), ...r2.slice(0, r2.findIndex((c) => c[0] === M2[0] && c[1] === M2[1])), ...r3.slice(0, r3.findIndex((c) => c[0] === P[0] && c[1] === P[1]))];
      if (!all.every((c) => free(fl, ...c)) || new Set(all.map((c) => key(...c))).size < 4 || path.some((c) => fl.things[key(...c)] || (fl.features || {})[key(...c)])) continue;
      const tiltFor = (din, dout) => (((din === 0 || din === 2) ? (dout === 1 ? (din === 0 ? "/" : "\\") : (din === 0 ? "\\" : "/")) : (dout === 0 ? (din === 1 ? "/" : "\\") : (din === 1 ? "\\" : "/"))));
      const t1 = tiltFor(d1, d2), t2 = tiltFor(d2, d3); fl.things[key(...S)] = { type: "sunshaft", dir: d1 }; fl.things[key(...M1)] = { type: "mirror", tilt: t1 === "/" ? "\\" : "/" }; fl.things[key(...M2)] = { type: "mirror", tilt: rnd.chance(0.5) ? t2 : (t2 === "/" ? "\\" : "/") }; fl.things[key(...P)] = { type: "sunplate" };
      fl.puzzle = { kind: "beam", chestAt: key(...P), solved: false }; return true; } return false; };
  CM.reflect = (dir, tilt) => (tilt === "/" ? [1, 0, 3, 2][dir] : [3, 2, 1, 0][dir]);   // ("/": north becomes east; "\": north becomes west)
  CM.beamOf = (fl) => { const src = Object.entries(fl.things).find(([, t]) => t.type === "sunshaft"); if (!src) return { cells: [], hit: false }; let [x, y] = src[0].split(",").map(Number), d = src[1].dir; const cells = [], seen = new Set();
    for (let i = 0; i < 80; i++) { x += D()[d][0]; y += D()[d][1]; if (!fl.grid[y] || fl.grid[y][x] !== 0) break; const k = key(x, y), sk = `${k}:${d}`; if (seen.has(sk)) break; seen.add(sk); cells.push([x, y, d]); const t = fl.things[k];
      if (t && t.type === "mirror") { d = CM.reflect(d, t.tilt); continue; } if (t && t.type === "sunplate") return { cells, hit: true }; if (t && !["chest"].includes(t.type)) break; } return { cells, hit: false }; };
  const mf0 = CM.makeFloor; CM.makeFloor = function (number, seed, gen) { const fl = mf0.call(this, number, seed, gen); if (!fl || fl.special || fl.number !== number || !(number >= 2 && number < 1000 && number % 1 === 0) || fl.mood) return fl;
    if (Object.values(fl.things).some((t) => ["guardian", "boss", "camp"].includes(t.type)) || CM.hashSeed(`${seed}:puzzle:${number}`) % CM.PUZZLE_EVERY !== 0) return fl;
    const rnd = new CM.Random(CM.hashSeed(`${seed}:puzzlelay:${number}`)); if (CM.hashSeed(`${seed}:puzzlekind:${number}`) % 2) { if (!layBeam(fl, rnd)) layStatues(fl, rnd); } else if (!layStatues(fl, rnd)) layBeam(fl, rnd); return fl; };
  const G = CM.Game.prototype;
  G.beamPath = function () { return this.floor ? CM.beamOf(this.floor) : { cells: [], hit: false }; };
  G.puzzleCheck = function () { const fl = this.floor, P = fl && fl.puzzle; if (!P || P.solved) return false;
    const ok = P.kind === "statues" ? Object.values(fl.things).filter((t) => t.type === "statue").every((t) => t.face === t.want) : CM.beamOf(fl).hit; if (!ok) return false;
    P.solved = true; const n = fl.number, rnd = new CM.Random(CM.hashSeed(`${this.seed}:puzzlechest:${n}`)), items = [CM.affix(CM.makeItem(n + 4, rnd), n + 8, rnd), CM.affix(CM.makeItem(n + 2, rnd), n + 5, rnd)];
    if (P.kind === "beam") fl.things[P.chestAt] = { type: "chest", gold: 40 * n, items, puzzle: true }; else fl.things[P.chestAt] = { type: "chest", gold: 40 * n, items, puzzle: true };
    this.sound && this.sound("chest"); this.say(P.kind === "statues" ? "The last statue grinds round to face the altar - and the floor beside it sinks, and comes up again carrying a chest." : "The beam leaps from mirror to mirror and falls full on the sun-plate. It glows, and with a sound like a held breath let go, a chest rises where it lay.");
    this.tally.puzzles = (this.tally.puzzles || 0) + 1; if (this.achieve) this.achieve("puzzler"); this.saveRun && this.saveRun(); this.emit("change"); return true; };
  CM.ACHIEVEMENTS.puzzler = { name: "Clever Hands", what: "Solve a puzzle room", title: "the Clever" };
  const use0 = G.use; G.use = function (...a) { const fl = this.floor; if (this.mode === "explore" && fl && fl.puzzle) { const [x, y] = fl.pos; let k = key(x, y), t = fl.things[k];
      if (!t || !["statue", "mirror", "altar", "sunshaft", "sunplate"].includes(t.type)) { const f = CM.DIRS[fl.facing]; k = key(x + f[0], y + f[1]); t = fl.things[k]; }   /* (or the one in front) */
      if (t && t.type === "statue") { this.logAct && this.logAct("use"); t.face = (t.face + 1) % 4; this.sound && this.sound("lever"); this.say(`The statue grinds a quarter turn: it looks ${["north", "east", "south", "west"][t.face]} now.`); this.puzzleCheck(); this.emit("change"); return; }
      if (t && t.type === "mirror") { this.logAct && this.logAct("use"); t.tilt = t.tilt === "/" ? "\\" : "/"; this.sound && this.sound("lever"); this.say("The mirror swings on its pin and settles the other way."); this.puzzleCheck(); this.emit("change"); return; }
      if (t && t.type === "altar") { this.say(fl.puzzle.solved ? "The altar is quiet now." : "A plain altar. Three stone faces stand about it, and none of them is looking at it."); return; }
      if (t && t.type === "sunshaft") { this.say("Daylight, a long way down through a crack in the roof, falling in a bright bar along the floor."); return; }
      if (t && t.type === "sunplate") { this.say(fl.puzzle.solved ? "The plate is warm." : "A round plate of gold-coloured metal set in the floor, a sun worked on it. Cold."); return; } }
    return use0.apply(this, a); };
}
