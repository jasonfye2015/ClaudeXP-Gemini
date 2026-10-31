"use strict";
// The Mana Conduit (the twenty-sixth big update - v13.6): a game of skill on the Gilded Joker's floor. A slate grid, a
// font of mana on it, and a rack of conduit pieces that come in order - straights, bends and crossings. Lay them on the
// grid before the font opens (laying one over a dry piece swaps it, at a little cost of time); then the mana runs,
// filling each piece in turn, and must pass through so many before it spills out of an open end. A crossing the mana
// runs through both ways counts twice. Ten levels, each with less time before the font opens, faster mana, a longer run
// to make and more rubble in the way; from the sixth a drain to end in, for a bonus. Each level pays gold and a
// Claudescryption card the first time it is done (common to four, a stronger one to nine, rare at ten); it costs
// nothing to play. Pieces come from the seed, so a level plays the same for the same hands. The window is 76r-conduit.js.
CM.CD = {
  DIRS: { N: [0, -1], E: [1, 0], S: [0, 1], W: [-1, 0] }, OPP: { N: "S", S: "N", E: "W", W: "E" },
  PIECES: { H: ["W", "E"], V: ["N", "S"], NE: ["N", "E"], NW: ["N", "W"], SE: ["S", "E"], SW: ["S", "W"], X: ["N", "E", "S", "W"] },
  WEIGHT: { H: 3, V: 3, NE: 2, NW: 2, SE: 2, SW: 2, X: 1 }, queue: 5, swapPenalty: 1.5,
  // per level: [cols, rows, seconds before the font opens, seconds a piece fills, pieces to pass, rubble, drain]
  LEVELS: [[8, 6, 24, 2.6, 7, 0, false], [8, 6, 22, 2.4, 9, 2, false], [9, 6, 21, 2.2, 11, 3, false], [9, 7, 20, 2.0, 13, 4, false], [10, 7, 19, 1.8, 14, 5, false],
    [10, 7, 18, 1.7, 15, 6, true], [10, 8, 17, 1.55, 17, 7, true], [11, 8, 16, 1.45, 18, 8, true], [11, 8, 15, 1.35, 20, 10, true], [12, 8, 14, 1.25, 22, 12, true]],
  gold: (n) => 20 + n * 12, fast: 0.12,
};
const CD = CM.CD;
CD.Board = class {
  constructor(level, seed) {
    const [cols, rows, wait, fill, need, rubble, drain] = CD.LEVELS[level - 1], R = this.rnd = new CM.Random(seed);
    Object.assign(this, { level, cols, rows, wait, fill, need, stage: "build", t: 0, passed: 0, events: [], fast: false });
    this.grid = Array.from({ length: rows }, () => Array(cols).fill(null));
    const dirs = Object.keys(CD.DIRS); let sx, sy, sd, ok = false;
    for (let k = 0; k < 100 && !ok; k++) { sx = R.int(1, cols - 2); sy = R.int(1, rows - 2); sd = R.pick(dirs); const [dx, dy] = CD.DIRS[sd]; ok = sx + dx * 2 >= 0 && sx + dx * 2 < cols && sy + dy * 2 >= 0 && sy + dy * 2 < rows; }
    this.grid[sy][sx] = { kind: "font", out: sd }; this.font = [sx, sy, sd];
    if (drain) { for (let k = 0; k < 200; k++) { const x = R.int(0, cols - 1), y = R.int(0, rows - 1), d = R.pick(dirs); if (this.grid[y][x] || Math.abs(x - sx) + Math.abs(y - sy) < 5) continue; const [dx, dy] = CD.DIRS[d]; if (x + dx < 0 || x + dx >= cols || y + dy < 0 || y + dy >= rows) continue; this.grid[y][x] = { kind: "drain", in: d }; this.drain = [x, y]; break; } }
    const [fdx, fdy] = CD.DIRS[sd];
    for (let k = 0, n = 0; k < 400 && n < rubble; k++) { const x = R.int(0, cols - 1), y = R.int(0, rows - 1); if (this.grid[y][x] || (x === sx + fdx && y === sy + fdy)) continue; this.grid[y][x] = { kind: "rubble" }; n++; }
    this.queue = []; for (let i = 0; i < CD.queue; i++) this.queue.push(this.pull());
    this.flow = null;
  }
  pull() { const W = CD.WEIGHT, tot = Object.values(W).reduce((a, b) => a + b, 0); let r = this.rnd.next() * tot; for (const [k, w] of Object.entries(W)) { if ((r -= w) < 0) return k; } return "H"; }
  // the next piece laid at x, y (on an empty square, or over a piece the mana has not reached)
  place(x, y) {
    if (this.stage === "done" || x < 0 || y < 0 || x >= this.cols || y >= this.rows) return false; const c = this.grid[y][x];
    if (c && (c.kind !== "pipe" || c.wet)) return false;
    const k = this.queue.shift(); this.queue.push(this.pull()); const swapped = !!c; this.grid[y][x] = { kind: "pipe", p: k, wet: 0 };
    if (swapped && this.stage === "build") this.t += CD.swapPenalty;
    this.events.push({ kind: swapped ? "swap" : "place", x, y, p: k }); return true;
  }
  // the clock: the wait, then the mana, a piece at a time
  update(dt) {
    if (this.stage === "done") return; const sp = this.fast ? CD.fast : 1;
    if (this.stage === "build") { this.t += dt; if (this.t >= this.wait) { this.stage = "flow"; const [x, y, d] = this.font; this.flow = { x, y, out: d, t: 0, fillT: this.fill }; this.events.push({ kind: "open" }); } return; }
    const F = this.flow; F.t += dt / sp; if (F.t < F.fillT) return; F.t = 0; F.fillT = this.fill;
    const [dx, dy] = CD.DIRS[F.out], nx = F.x + dx, ny = F.y + dy, entry = CD.OPP[F.out], c = nx >= 0 && ny >= 0 && nx < this.cols && ny < this.rows ? this.grid[ny][nx] : null;
    if (c && c.kind === "drain" && c.in === entry) { this.end(true, "drain", nx, ny); return; }
    if (!c || c.kind !== "pipe" || !CD.PIECES[c.p].includes(entry) || (c.p !== "X" && c.wet) || (c.p === "X" && c.wet && (c.through || []).includes(entry === "N" || entry === "S" ? "V" : "H"))) { this.end(false, "spill", nx, ny); return; }
    const out = c.p === "X" ? F.out : CD.PIECES[c.p].find((d) => d !== entry);
    c.wet = (c.wet || 0) + 1; if (c.p === "X") (c.through = c.through || []).push(entry === "N" || entry === "S" ? "V" : "H"); c.entry = entry; this.passed += 1;
    this.events.push({ kind: "fill", x: nx, y: ny, n: this.passed, cross: c.p === "X" && c.wet > 1 }); Object.assign(F, { x: nx, y: ny, out });
  }
  end(drained, why, x, y) { this.stage = "done"; this.won = this.passed >= this.need; this.drained = drained && this.won; this.why = why; this.events.push({ kind: "end", won: this.won, drained: this.drained, x, y }); }
};
Object.assign(CM.Game.prototype, {
  cdStore() { const F = this.cgStore(); F.cd = F.cd || { best: 0, n: 0, plays: 0 }; return F.cd; },
  cdStart(level) { const S = this.cdStore(); if (level < 1 || level > Math.min(CD.LEVELS.length, S.best + 1)) return { error: "That level is still locked." }; S.n += 1; S.plays += 1; this.cdLive = new CD.Board(level, CM.hashSeed(`${this.seed}:conduit:${level}:${S.n}`)); this.saveCasino && this.saveCasino(); return this.cdLive; },
  // done: the first time a level is done, gold (a fifth more for the drain) and a card
  cdDone() {
    const B = this.cdLive, S = this.cdStore(); if (!B || B.stage !== "done" || B.paid) return null; B.paid = true; if (!B.won) return { won: false, passed: B.passed, need: B.need };
    const n = B.level; if (n <= S.best) return { won: true, again: true, level: n, drained: B.drained };
    S.best = n; const gold = Math.round(CD.gold(n) * (B.drained ? 1.2 : 1)); this.gold += gold; const F = this.cgStore(); F.paid.conduit = (F.paid.conduit || 0) + gold;
    const card = this.cgTierCard(CM.cardTierFor(n), `The Mana Conduit, level ${n} done!`, new CM.Random(CM.hashSeed(`${this.seed}:conduit:card:${n}`)));
    this.saveCasino && this.saveCasino(); this.emit("change"); return { won: true, level: n, gold, card, kind: CM.cardTierFor(n), drained: B.drained };
  },
});
