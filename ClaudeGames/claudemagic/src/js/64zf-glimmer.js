"use strict";
// The Glimmer Maze (the twenty-ninth big update - v13.9): a maze-chase on the Gilded Joker's floor. A glimmerslime eats
// its way round a hedge maze full of glimmer motes; four Lantern Haunts hunt it, each its own way - Ember straight at it,
// Bramble at where it is going, Frost from the far side of Ember, Moth close then shy. Now and then the haunts drift off
// to their own corners. The four Hex Runes turn them pale and slow for a while: then the slime can eat them (200, 400,
// 800, 1600) and they go back to the lantern-house as a pair of eyes. A tunnel through each side. A lucky chip shows twice
// a level. Clear every mote for the next level - quicker haunts, shorter runes. Three lives (one more at 10,000). One
// stake a play: each level cleared pays gold, more each level, every play; and a Claudescryption card for each level the
// first time it is ever cleared (common to four, a stronger common to nine, rare from ten). The window: 76v-glimmer.js.
CM.GZ = {
  MAP: [
    "###################",
    "#........#........#",
    "#o##.###.#.###.##o#",
    "#.................#",
    "#.##.#.#####.#.##.#",
    "#....#...#...#....#",
    "####.### # ###.####",
    "XXX#.#       #.#XXX",
    "####.# ##-## #.####",
    "    .  #   #  .    ",
    "####.# ##### #.####",
    "XXX#.#       #.#XXX",
    "####.# ##### #.####",
    "#........#........#",
    "#.##.###.#.###.##.#",
    "#o.#.....P.....#.o#",
    "##.#.#.#####.#.#.##",
    "#....#...#...#....#",
    "#.######.#.######.#",
    "#.................#",
    "###################",
  ],
  W: 19, H: 21, TUNNEL: 9, OUT: [9, 7], HOME: [9, 9], CHIP: [9, 11], step: 1 / 60, lives: 3, extra: 10000,
  speed: 5.4, haunt: 4.4, scared: 3.0, eyes: 11, tunnelSpeed: 2.6,
  MODES: [["scatter", 9], ["chase", 15], ["scatter", 8], ["chase", 18], ["scatter", 6], ["chase", 1e9]],
  fright: (n) => Math.max(1.5, 8 - 0.6 * (n - 1)), release: [0, 8, 30, 60], idleRelease: 5,
  pay: (n) => 0.15 + 0.1 * n, SCORE: { mote: 10, rune: 50, eat: [200, 400, 800, 1600], chip: [100, 300, 500, 700, 1000, 2000, 3000, 5000] },
  HAUNTS: [{ name: "Ember", color: "#F05030", corner: [17, -2] }, { name: "Bramble", color: "#60D060", corner: [1, -2] }, { name: "Frost", color: "#60C8F0", corner: [18, 22] }, { name: "Moth", color: "#F0B040", corner: [0, 22] }],
  DIRS: { up: [0, -1], left: [-1, 0], down: [0, 1], right: [1, 0] }, BACK: { up: "down", down: "up", left: "right", right: "left" },
};
const GZ = CM.GZ;
GZ.Level = class {
  constructor(n, seed, keep) {
    this.rnd = new CM.Random(seed); this.n = n; this.t = 0; this.events = []; this.stage = "play"; Object.assign(this, keep || { score: 0, lives: GZ.lives, extraGiven: false });
    this.motes = GZ.MAP.map((row) => [...row].map((c) => (c === "." ? 1 : c === "o" ? 2 : 0))); this.left = this.motes.flat().filter(Boolean).length; this.eaten = 0; this.chip = null;
    this.mul = 1 + Math.min(0.35, (n - 1) * 0.05); this.spawn();
  }
  spawn() {
    let px = 9, py = 15; GZ.MAP.forEach((row, y) => { if (row.includes("P")) { px = row.indexOf("P"); py = y; } });
    this.p = { x: px, y: py, fx: px, fy: py, dir: "left", want: "left", dead: 0, mouth: 0 };
    this.haunts = GZ.HAUNTS.map((H, i) => { const [x, y] = i === 0 ? GZ.OUT : [GZ.HOME[0] + (i - 2), GZ.HOME[1]]; return { i, name: H.name, x, y, fx: x, fy: y, dir: i === 0 ? "left" : "up", state: i === 0 ? "out" : "home", scared: 0, flip: false }; });
    this.modeI = 0; this.modeT = GZ.MODES[0][1]; this.fright = 0; this.chain = 0; this.idle = 0; this.dotsSince = 0; this.freshLife = this.eaten > 0;
  }
  mode() { return GZ.MODES[this.modeI][0]; }
  wall(x, y) { if (y === GZ.TUNNEL && (x < 0 || x >= GZ.W)) return false; if (x < 0 || x >= GZ.W || y < 0 || y >= GZ.H) return true; const c = GZ.MAP[y][x]; return c === "#" || c === "X" || c === "-"; }
  input(dir) { if (dir) this.p.want = dir; }
  centred(e) { return Math.abs(e.fx - e.x) < 1e-6 && Math.abs(e.fy - e.y) < 1e-6; }
  // one walker's step: at a cell's middle choose; then slide toward the next cell, through the tunnel at the sides
  walk(e, sp, choose) {
    let left = sp;
    for (let guard = 0; guard < 4 && left > 1e-9; guard++) {
      if (this.centred(e)) {
        if (e.x < 0) e.x = e.fx = GZ.W; else if (e.x >= GZ.W) e.x = e.fx = -1;
        const d = choose(e); if (!d) return; e.dir = d; const [dx, dy] = GZ.DIRS[d]; e.x += dx; e.y += dy;
      }
      const dist = Math.abs(e.x - e.fx) + Math.abs(e.y - e.fy); if (dist <= left + 1e-9) { e.fx = e.x; e.fy = e.y; left -= dist; } else { if (Math.abs(e.x - e.fx) > 1e-9) e.fx += Math.sign(e.x - e.fx) * left; else e.fy += Math.sign(e.y - e.fy) * left; left = 0; }
    }
  }
  stepSlime(dt) {
    const P = this.p; if (P.dead) return;
    if (P.want === GZ.BACK[P.dir] && !this.centred(P)) { const [bx, by] = GZ.DIRS[P.want]; P.x += bx; P.y += by; P.dir = P.want; }
    const sp = (P.y === GZ.TUNNEL && (P.x < 1 || P.x > GZ.W - 2) ? 0.8 : 1) * GZ.speed * Math.min(1.15, this.mul) * dt;
    this.walk(P, sp, (e) => { for (const d of [e.want, e.dir]) { const [dx, dy] = GZ.DIRS[d]; if (!this.wall(e.x + dx, e.y + dy)) return d; } return null; });
    P.mouth += dt * 12;
    const cx = Math.round(P.fx), cy = Math.round(P.fy);
    if (Math.abs(P.fx - cx) + Math.abs(P.fy - cy) < 0.3 && cx >= 0 && cx < GZ.W && this.motes[cy][cx]) {
      const k = this.motes[cy][cx]; this.motes[cy][cx] = 0; this.left -= 1; this.eaten += 1; this.dotsSince += 1; this.idle = 0; this.score += k === 2 ? GZ.SCORE.rune : GZ.SCORE.mote; this.events.push({ kind: k === 2 ? "rune" : "mote", x: cx, y: cy });
      if (k === 2) { this.fright = GZ.fright(this.n); this.chain = 0; for (const h of this.haunts) if (h.state === "out") { h.scared = 1; h.flip = true; } }
      if ((this.eaten === 60 || this.eaten === 140) && !this.chip) { this.chip = { t: 9.5, pts: GZ.SCORE.chip[Math.min(7, this.n - 1)] }; this.events.push({ kind: "chip" }); }
      if (!this.left) { this.stage = "clear"; this.events.push({ kind: "clear" }); }
    }
    if (this.chip && Math.abs(P.fx - GZ.CHIP[0]) + Math.abs(P.fy - GZ.CHIP[1]) < 0.5) { this.score += this.chip.pts; this.events.push({ kind: "chipeat", pts: this.chip.pts }); this.chip = null; }
  }
  // where each haunt aims
  target(h) {
    const P = this.p, [dx, dy] = GZ.DIRS[P.dir];
    if (this.mode() === "scatter") return GZ.HAUNTS[h.i].corner;
    if (h.i === 0) return [P.x, P.y];
    if (h.i === 1) return [P.x + dx * 4, P.y + dy * 4];
    if (h.i === 2) { const E = this.haunts[0]; return [(P.x + dx * 2) * 2 - E.x, (P.y + dy * 2) * 2 - E.y]; }
    return Math.hypot(h.x - P.x, h.y - P.y) > 8 ? [P.x, P.y] : GZ.HAUNTS[3].corner;
  }
  // the way home for a pair of eyes: steps to the lantern-house door from every cell
  homeDist() { if (GZ.homeD) return GZ.homeD; const D = new Map([[`${GZ.OUT[0]},${GZ.OUT[1]}`, 0]]), q = [GZ.OUT]; while (q.length) { const [x, y] = q.shift(), d = D.get(`${x},${y}`); for (const [dx, dy] of Object.values(GZ.DIRS)) { let nx = x + dx; const ny = y + dy; if (this.wall(nx, ny)) continue; if (nx < -1) nx = GZ.W; if (nx > GZ.W) nx = -1; if (!D.has(`${nx},${ny}`)) { D.set(`${nx},${ny}`, d + 1); q.push([nx, ny]); } } } return (GZ.homeD = D); }
  stepHaunt(h, dt) {
    if (h.state === "home") { h.fy = GZ.HOME[1] + Math.sin(this.t * 6 + h.i) * 0.2; return; }
    if (h.state === "leaving") { const sp = GZ.haunt * 0.5 * dt, [ox, oy] = GZ.OUT; if (Math.abs(h.fx - ox) > 1e-6) h.fx += Math.sign(ox - h.fx) * Math.min(sp, Math.abs(ox - h.fx)); else if (Math.abs(h.fy - GZ.HOME[1]) > 1e-6 && h.fy > GZ.HOME[1]) h.fy = GZ.HOME[1]; else { h.fy -= Math.min(sp, h.fy - oy); if (h.fy <= oy + 1e-6) { h.fx = h.x = ox; h.fy = h.y = oy; h.state = "out"; h.dir = "left"; h.scared = 0; } } return; }
    if (h.state === "eyes" && this.centred(h) && h.x === GZ.OUT[0] && h.y === GZ.OUT[1]) h.state = "entering";
    if (h.state === "entering") { h.fy += Math.min(GZ.eyes * dt, GZ.HOME[1] - h.fy); if (h.fy >= GZ.HOME[1] - 1e-6) { h.x = GZ.HOME[0]; h.y = GZ.HOME[1]; h.state = "leaving"; } return; }
    const inTunnel = h.y === GZ.TUNNEL && (h.x < 2 || h.x > GZ.W - 3), base = h.state === "eyes" ? GZ.eyes : inTunnel ? GZ.tunnelSpeed : h.scared ? GZ.scared : GZ.haunt * this.mul;
    this.walk(h, base * dt, (e) => {
      if (e.state === "eyes") { const D = this.homeDist(); let best = null, bd = Infinity; for (const [d, [dx, dy]] of Object.entries(GZ.DIRS)) { const v = D.get(`${e.x + dx},${e.y + dy}`); if (v !== undefined && v < bd) { bd = v; best = d; } } return best; }
      if (e.flip) { e.flip = false; const [dx, dy] = GZ.DIRS[GZ.BACK[e.dir]]; if (!this.wall(e.x + dx, e.y + dy)) return GZ.BACK[e.dir]; }
      const opts = Object.keys(GZ.DIRS).filter((d) => { const [dx, dy] = GZ.DIRS[d]; return d !== GZ.BACK[e.dir] && !this.wall(e.x + dx, e.y + dy); });
      if (!opts.length) return GZ.BACK[e.dir];
      if (e.scared && e.state === "out") return this.rnd.pick(opts);
      const [tx, ty] = e.state === "eyes" ? GZ.OUT : this.target(e); let best = null, bd = Infinity;
      for (const d of opts) { const [dx, dy] = GZ.DIRS[d], dd = (e.x + dx - tx) ** 2 + (e.y + dy - ty) ** 2; if (dd < bd) { bd = dd; best = d; } } return best;
    });
  }
  lose() { const P = this.p; if (P.dead) return; P.dead = 1.8; this.lives -= 1; this.events.push({ kind: "die" }); }
  update(dt) { for (let s = 0; s < dt / GZ.step - 1e-9; s++) this.tick(GZ.step); }
  tick(dt) {
    if (this.stage !== "play") return; this.t += dt; const P = this.p;
    if (P.dead) { P.dead -= dt; if (P.dead <= 0) { if (this.lives <= 0) { this.stage = "over"; this.events.push({ kind: "over" }); } else { this.spawn(); this.events.push({ kind: "respawn" }); } } return; }
    if (this.fright > 0) { this.fright -= dt; if (this.fright <= 0) for (const h of this.haunts) h.scared = 0; }
    else { this.modeT -= dt; if (this.modeT <= 0 && this.modeI < GZ.MODES.length - 1) { this.modeI += 1; this.modeT = GZ.MODES[this.modeI][1]; for (const h of this.haunts) if (h.state === "out") h.flip = true; } }
    // the lantern-house lets them out by motes eaten, or after a while without one
    this.idle += dt; const waiting = this.haunts.find((h) => h.state === "home");
    if (waiting && (this.dotsSince >= (this.freshLife ? 8 * waiting.i : GZ.release[waiting.i]) || this.idle > GZ.idleRelease)) { waiting.state = "leaving"; this.idle = 0; this.dotsSince = 0; }
    this.stepSlime(dt); if (this.stage !== "play") return;
    for (const h of this.haunts) this.stepHaunt(h, dt);
    if (this.chip) { this.chip.t -= dt; if (this.chip.t <= 0) this.chip = null; }
    for (const h of this.haunts) {
      if (h.state !== "out" || Math.abs(h.fx - P.fx) + Math.abs(h.fy - P.fy) > 0.7) continue;
      if (h.scared) { const pts = GZ.SCORE.eat[Math.min(3, this.chain++)]; this.score += pts; h.state = "eyes"; h.scared = 0; h.x = Math.round(h.fx); h.y = Math.round(h.fy); h.fx = h.x; h.fy = h.y; this.events.push({ kind: "eat", h, pts }); }
      else { this.lose(); break; }
    }
    if (!this.extraGiven && this.score >= GZ.extra) { this.extraGiven = true; this.lives += 1; this.events.push({ kind: "extra" }); }
  }
};
Object.assign(CM.Game.prototype, {
  gzState() { return this.cgStore().gz || null; },
  gzClaimed() { const F = this.cgStore(); F.gzCards = F.gzCards || {}; return F.gzCards; },
  gzLevel() {
    const S = this.gzState(); if (!S || S.stage !== "play") return null;
    if (!this.gzLive || this.gzLive.key !== `${S.seed}:${S.n}`) {
      if (this.gzLive && this.gzLive.key && this.gzLive.key.startsWith(`${S.seed}:`)) { const keep = { score: this.gzLive.score, lives: this.gzLive.lives, extraGiven: this.gzLive.extraGiven }; this.gzLive = new GZ.Level(S.n, CM.hashSeed(`${S.seed}:${S.n}`), keep); this.gzLive.key = `${S.seed}:${S.n}`; }
      else { S.stage = "done"; S.last = S.last || { level: S.n, won: S.won, cards: [], lost: true }; this.saveCasino && this.saveCasino(); return null; }
    }
    return this.gzLive;
  },
  gzStart(bet) {
    const S0 = this.gzState(); if (S0 && S0.stage === "play" && this.gzLive && this.gzLive.key && this.gzLive.key.startsWith(`${S0.seed}:`)) return { error: "A game is on." };
    const why = this.cgStake("glimmer", bet); if (why) return { error: why };
    const F = this.cgStore(); F.n += 1; F.gz = { stage: "play", n: 1, bet: Math.floor(bet), seed: `${this.seed}:glimmer:${F.n}`, won: 0, cards: [] };
    this.gzLive = new GZ.Level(1, CM.hashSeed(`${F.gz.seed}:1`)); this.gzLive.key = `${F.gz.seed}:1`; this.saveCasino && this.saveCasino(); return F.gz;
  },
  // a level cleared: its gold (every play), its card (the first time ever); on to the next. The game over: done.
  gzCheck() {
    const S = this.gzState(), L = this.gzLive; if (!S || !L || S.stage !== "play") return null;
    if (L.stage === "clear") {
      const n = S.n, pay = Math.round(S.bet * GZ.pay(n)), C = this.gzClaimed(); let card = null;
      if (!C[n]) { card = this.cgTierCard(CM.cardTierFor(n), `The Glimmer Maze, level ${n} cleared!`, new CM.Random(CM.hashSeed(`${this.seed}:glimmer:card:${n}`))); C[n] = card || true; if (card) S.cards.push(card); }
      this.cgPay("glimmer", pay); S.won += pay; S.n += 1; this.saveCasino && this.saveCasino(); this.emit("change");
      this.gzLevel(); return { cleared: n, pay, card };
    }
    if (L.stage === "over") { S.stage = "done"; S.last = { level: S.n, score: L.score, won: S.won, cards: S.cards.slice() }; const F = this.cgStore(); F.gzBest = Math.max(F.gzBest || 0, L.score); this.gzLive = null; this.saveCasino && this.saveCasino(); this.emit("change"); return { over: true }; }
    return null;
  },
});
