"use strict";
// The Gemcutter's Tray (the twenty-second big update - v13.2): a game of skill on the Gilded Joker's floor. An eight
// by eight tray of cut stones - the game's own rubies, sapphires, sunstones and diamonds, with jade, amethyst and
// pearl - and a gemcutter's eye: swap two neighbours to make a line of three or more of a kind; they are cut away,
// the stones above fall, new ones drop in from the top, and what lines up as they settle goes too, the cascade
// counting up. Four in a line (or an L or a T) leaves a rune-stone that bursts its square of nine when it goes; five
// in a line leaves a star-stone, which, swapped with any stone, takes every one of that kind from the tray. Each tray
// asks a score in a number of moves; five trays a run for one stake, each one done paying its share of it, cards from
// the second, fourth and fifth, and a little back for a tray left short. A tray with no move left is shaken up.
// Every stone that drops is the seed's and the house's count, so a tray plays the same. The window is 76k-gemtray.js.
CM.GT = {
  N: 8, KINDS: ["ruby", "sapphire", "sunstone", "diamond", "jade", "amethyst", "pearl"],
  TRAYS: [["The Apprentice's Tray", 22, 2000], ["The Journeyman's Tray", 22, 2800], ["The Guild Tray", 24, 3700], ["The Master's Tray", 24, 4800], ["The Crown Jeweller's Tray", 26, 6200]],
  PAY: [0.6, 0.8, 1.0, 1.4, 2.4], CARD: { 2: "common", 4: "common", 5: "rare" }, consolation: 0.35,
  SCORE: { gem: 10, four: 60, five: 200, rune: 40, star: 30 },
};
const GT = CM.GT;
GT.Tray = class {
  constructor(n, seed) {
    const T = GT.TRAYS[n - 1]; this.n = n; this.rnd = new CM.Random(seed); this.moves = T[1]; this.target = T[2]; this.score = 0; this.ids = 0; this.stage = "play"; this.best = 0;
    this.grid = []; for (let y = 0; y < GT.N; y++) { const row = []; for (let x = 0; x < GT.N; x++) { let k; do k = this.rnd.int(0, GT.KINDS.length - 1); while ((x >= 2 && row[x - 1].k === k && row[x - 2].k === k) || (y >= 2 && this.grid[y - 1][x].k === k && this.grid[y - 2][x].k === k)); row.push(this.gem(k)); } this.grid.push(row); }
    if (!this.hasMove()) this.shake();
  }
  gem(k, sp = null) { return { k, sp, id: ++this.ids }; }
  at(x, y) { return x >= 0 && y >= 0 && x < GT.N && y < GT.N ? this.grid[y][x] : null; }
  // the runs of three or more, each [cells]
  runs() {
    const out = [], N = GT.N;
    for (let y = 0; y < N; y++) { let x = 0; while (x < N) { const g = this.grid[y][x]; let e = x + 1; if (g && g.sp !== "star") while (e < N && this.grid[y][e] && this.grid[y][e].sp !== "star" && this.grid[y][e].k === g.k) e++; if (g && g.sp !== "star" && e - x >= 3) out.push({ dir: "h", cells: Array.from({ length: e - x }, (_, i) => [x + i, y]) }); x = e; } }
    for (let x = 0; x < N; x++) { let y = 0; while (y < N) { const g = this.grid[y][x]; let e = y + 1; if (g && g.sp !== "star") while (e < N && this.grid[e][x] && this.grid[e][x].sp !== "star" && this.grid[e][x].k === g.k) e++; if (g && g.sp !== "star" && e - y >= 3) out.push({ dir: "v", cells: Array.from({ length: e - y }, (_, i) => [x, y + i]) }); y = e; } }
    return out;
  }
  // would this swap do anything?
  swapWorks(x1, y1, x2, y2) {
    const a = this.at(x1, y1), b = this.at(x2, y2); if (!a || !b || Math.abs(x1 - x2) + Math.abs(y1 - y2) !== 1) return false; if (a.sp === "star" || b.sp === "star") return true;
    this.grid[y1][x1] = b; this.grid[y2][x2] = a; const ok = this.runs().length > 0; this.grid[y1][x1] = a; this.grid[y2][x2] = b; return ok;
  }
  hasMove() { for (let y = 0; y < GT.N; y++) for (let x = 0; x < GT.N; x++) { if (this.swapWorks(x, y, x + 1, y) || this.swapWorks(x, y, x, y + 1)) return true; } return false; }
  hint() { for (let y = 0; y < GT.N; y++) for (let x = 0; x < GT.N; x++) { if (this.swapWorks(x, y, x + 1, y)) return [x, y, x + 1, y]; if (this.swapWorks(x, y, x, y + 1)) return [x, y, x, y + 1]; } return null; }
  shake() { let guard = 0; do { const all = this.grid.flat(); for (let i = all.length - 1; i > 0; i--) { const j = this.rnd.int(0, i); [all[i], all[j]] = [all[j], all[i]]; } for (let y = 0; y < GT.N; y++) for (let x = 0; x < GT.N; x++) this.grid[y][x] = all[y * GT.N + x]; } while ((this.runs().length || !this.hasMove()) && guard++ < 200); }
  // a swap: false if it does nothing (the stones go back); else the phases of what happened, for the window to play
  swap(x1, y1, x2, y2) {
    if (this.stage !== "play" || !this.swapWorks(x1, y1, x2, y2)) return false;
    const a = this.at(x1, y1), b = this.at(x2, y2); this.grid[y1][x1] = b; this.grid[y2][x2] = a; this.moves -= 1;
    const phases = [{ kind: "swap", a: a.id, b: b.id }]; let cascade = 0;
    if (a.sp === "star" || b.sp === "star") {                                // (a star-stone: every stone of the other's kind)
      const other = a.sp === "star" ? b : a, both = a.sp === "star" && b.sp === "star", hit = new Set();
      for (let y = 0; y < GT.N; y++) for (let x = 0; x < GT.N; x++) { const g = this.grid[y][x]; if (both || g === a || g === b || (g.k === other.k && g.sp !== "star")) hit.add(`${x},${y}`); }
      this.score += GT.SCORE.star * hit.size; phases.push(this.clear(hit, [], 1, "star")); cascade = 1;
    }
    for (;;) { const runs = this.runs(); if (!runs.length) break; cascade += 1; phases.push(this.cutRuns(runs, cascade, [x1, y1, x2, y2])); }
    if (!this.hasMove()) { this.shake(); phases.push({ kind: "shake", grid: this.snapshot() }); }
    this.best = Math.max(this.best, cascade);
    if (this.score >= this.target) this.stage = "won"; else if (this.moves <= 0) this.stage = "lost";
    return phases;
  }
  cutRuns(runs, cascade, swapAt) {
    const hit = new Set(), made = [], count = new Map();
    for (const r of runs) for (const [x, y] of r.cells) { const k = `${x},${y}`; hit.add(k); count.set(k, (count.get(k) || 0) + 1); }
    for (const r of runs) {
      const len = r.cells.length, k0 = this.at(...r.cells[0]).k; if (len < 4) continue;
      const atSwap = r.cells.find(([x, y]) => (x === swapAt[0] && y === swapAt[1]) || (x === swapAt[2] && y === swapAt[3])), [cx, cy] = atSwap || r.cells[Math.floor(len / 2)];
      made.push({ x: cx, y: cy, k: k0, sp: len >= 5 ? "star" : "rune" }); this.score += (len >= 5 ? GT.SCORE.five : GT.SCORE.four) * cascade;
    }
    for (const [k, c] of count) if (c > 1 && !made.some((m) => `${m.x},${m.y}` === k)) { const [x, y] = k.split(",").map(Number); made.push({ x, y, k: this.at(x, y).k, sp: "rune" }); this.score += GT.SCORE.four * cascade; }
    this.score += GT.SCORE.gem * hit.size * cascade;
    return this.clear(hit, made, cascade, "match");
  }
  // cut the stones (a rune-stone bursts its square of nine, which may burst others), place what was made, let them fall
  clear(hit, made, cascade, why) {
    const queue = [...hit]; const burst = [];
    while (queue.length) { const k = queue.pop(), [x, y] = k.split(",").map(Number), g = this.at(x, y); if (g && g.sp === "rune" && !burst.includes(k)) { burst.push(k); for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) { const kk = `${x + dx},${y + dy}`; if (this.at(x + dx, y + dy) && !hit.has(kk)) { hit.add(kk); queue.push(kk); this.score += GT.SCORE.rune * cascade; } } } }
    const cut = []; for (const k of hit) { const [x, y] = k.split(",").map(Number), g = this.at(x, y); if (g) cut.push({ id: g.id, x, y, k: g.k, sp: g.sp }); this.grid[y][x] = null; }
    const placed = made.map((m) => { const g = this.gem(m.k, m.sp); this.grid[m.y][m.x] = g; return { id: g.id, x: m.x, y: m.y, k: g.k, sp: g.sp }; });
    const falls = [];
    for (let x = 0; x < GT.N; x++) { let w = GT.N - 1; for (let y = GT.N - 1; y >= 0; y--) { const g = this.grid[y][x]; if (!g) continue; if (w !== y) { this.grid[w][x] = g; this.grid[y][x] = null; falls.push({ id: g.id, x, from: y, to: w }); } w--; }
      for (let y = w; y >= 0; y--) { const g = this.gem(this.rnd.int(0, GT.KINDS.length - 1)); this.grid[y][x] = g; falls.push({ id: g.id, x, from: y - w - 1, to: y, fresh: true, k: g.k }); } }
    return { kind: why, cascade, cut, placed, burst: burst.length, falls, grid: this.snapshot(), score: this.score };
  }
  snapshot() { return this.grid.map((row) => row.map((g) => ({ id: g.id, k: g.k, sp: g.sp }))); }
};
Object.assign(CM.Game.prototype, {
  gtState() { return this.cgStore().gt || null; },
  gtTray() { const S = this.gtState(); if (!S || S.stage !== "tray") return null; if (!this.gtLive || this.gtLive.key !== `${S.seed}:${S.n}`) { this.gtLive = new GT.Tray(S.n, CM.hashSeed(`${S.seed}:${S.n}`)); this.gtLive.key = `${S.seed}:${S.n}`; } return this.gtLive; },
  gtStart(bet) {
    const S0 = this.gtState(); if (S0 && S0.stage === "tray") return { error: "A tray is on the table." };
    const why = this.cgStake("gemtray", bet); if (why) return { error: why };
    const F = this.cgStore(); F.n += 1; F.gt = { stage: "tray", n: 1, bet: Math.floor(bet), won: 0, cards: [], seed: `${this.seed}:gemtray:${F.n}` }; this.gtLive = null;
    this.saveCasino && this.saveCasino(); return F.gt;
  },
  gtSettle() {
    const S = this.gtState(), T = this.gtLive; if (!S || !T || T.stage === "play") return null; let pay = 0, card = null;
    if (T.stage === "won") {
      pay = Math.round(S.bet * GT.PAY[S.n - 1]); const kind = GT.CARD[S.n];
      if (kind) { card = this.cgCard(kind === "rare", `The Gemcutter's Tray, tray ${S.n} done!`, new CM.Random(CM.hashSeed(`${S.seed}:card:${S.n}`))); if (card) S.cards.push(card); }
      S.last = { n: S.n, won: true, pay, card, score: T.score }; if (S.n >= GT.TRAYS.length) { S.stage = "done"; S.cleared = true; } else { S.n += 1; this.gtLive = null; }
    } else { pay = Math.round(S.bet * GT.consolation * Math.min(1, T.score / T.target)); S.last = { n: S.n, won: false, pay, score: T.score }; S.stage = "done"; }
    this.cgPay("gemtray", pay); S.won += pay; this.saveCasino && this.saveCasino(); this.emit("change"); return S.last;
  },
});
