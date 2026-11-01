"use strict";
// The Trapfinder's Grid (v15.7): a minesweeper game on a flagstone floor full of hidden traps, free to play. Lift a
// stone (a click): a trap below ends the game; otherwise the stone shows how many of its eight neighbours hide traps,
// and an empty one lifts all around it. Mark a stone you are sure of with a pennant (a right-click). Click a number whose
// pennants are all down to lift the rest around it. The first stone lifted is always safe, with its neighbours. Lift
// every safe stone to win: three floors - the Cellar (9 by 9, 10 traps), the Crypt (16 by 16, 40) and the Catacomb (24
// by 16, 80); a win pays gold and prize tickets, more for the larger, and a Claudescryption card the first time each is
// cleared (common, stronger, rare). Best times are kept. Window: 76zu-traps.js.
CM.TRP = { SIZES: { cellar: { w: 9, h: 9, n: 10, gold: 12, tickets: 3, card: "common", name: "the Cellar" }, crypt: { w: 16, h: 16, n: 40, gold: 40, tickets: 10, card: "better", name: "the Crypt" }, catacomb: { w: 24, h: 16, n: 80, gold: 110, tickets: 25, card: "rare", name: "the Catacomb" } } };
{ const TRP = CM.TRP;
  TRP.Board = class {
    constructor(size, seed) { const S = TRP.SIZES[size]; this.size = size; this.w = S.w; this.h = S.h; this.n = S.n; this.seed = seed; this.mine = null; this.open = Array.from({ length: S.h }, () => Array(S.w).fill(false)); this.flag = Array.from({ length: S.h }, () => Array(S.w).fill(false)); this.stage = "play"; this.t = 0; this.started = false; this.events = []; }
    nb(x, y) { const o = []; for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) { if (!dx && !dy) continue; const a = x + dx, b = y + dy; if (a >= 0 && b >= 0 && a < this.w && b < this.h) o.push([a, b]); } return o; }
    lay(sx, sy) { const R = new CM.Random(this.seed), safe = new Set([`${sx},${sy}`, ...this.nb(sx, sy).map(([a, b]) => `${a},${b}`)]); this.mine = Array.from({ length: this.h }, () => Array(this.w).fill(false)); let k = 0; while (k < this.n) { const x = R.int(0, this.w - 1), y = R.int(0, this.h - 1); if (this.mine[y][x] || safe.has(`${x},${y}`)) continue; this.mine[y][x] = true; k++; } }
    count(x, y) { return this.nb(x, y).filter(([a, b]) => this.mine[b][a]).length; }
    reveal(x, y) {
      if (this.stage !== "play" || this.flag[y][x] || this.open[y][x]) return 0; if (!this.mine) { this.lay(x, y); this.started = true; }
      if (this.mine[y][x]) { this.open[y][x] = true; this.stage = "lost"; this.boom = [x, y]; this.events.push({ kind: "boom", x, y }); return 0; }
      let n = 0; const q = [[x, y]]; this.open[y][x] = true; while (q.length) { const [a, b] = q.shift(); n++; if (this.count(a, b) === 0) for (const [c, d] of this.nb(a, b)) if (!this.open[d][c] && !this.flag[d][c]) { this.open[d][c] = true; q.push([c, d]); } }
      this.events.push({ kind: "lift", x, y, n }); this.check(); return n;
    }
    toggle(x, y) { if (this.stage !== "play" || this.open[y][x]) return; this.flag[y][x] = !this.flag[y][x]; this.events.push({ kind: this.flag[y][x] ? "flag" : "unflag", x, y }); }
    chord(x, y) { if (!this.open[y][x] || !this.mine) return; const c = this.count(x, y), nb = this.nb(x, y); if (nb.filter(([a, b]) => this.flag[b][a]).length !== c) return; for (const [a, b] of nb) if (!this.flag[b][a] && !this.open[b][a]) this.reveal(a, b); }
    left() { let k = 0; for (let y = 0; y < this.h; y++) for (let x = 0; x < this.w; x++) if (!this.open[y][x]) k++; return k - this.n; }
    flags() { return this.flag.flat().filter(Boolean).length; }
    check() { if (this.stage === "play" && this.left() === 0) { this.stage = "won"; for (let y = 0; y < this.h; y++) for (let x = 0; x < this.w; x++) if (this.mine[y][x]) this.flag[y][x] = true; this.events.push({ kind: "won" }); } }
    update(dt) { if (this.stage === "play" && this.started) this.t += dt; }
  };
  Object.assign(CM.Game.prototype, {
    tfStore() { const F = this.cgStore(); F.tf = F.tf || { wins: {}, played: {}, best: {}, n: 0, cards: {} }; return F.tf; },
    tfNew(size) { const T = this.tfStore(); T.n += 1; T.played[size] = (T.played[size] || 0) + 1; this.tfLive = new TRP.Board(size, CM.hashSeed(`${this.seed}:traps:${size}:${T.n}`)); if (this.cgStamp) this.cgStamp("traps"); this.saveCasino && this.saveCasino(); return this.tfLive; },
    tfWin() { const B = this.tfLive; if (!B || B.stage !== "won" || B.paid) return null; B.paid = true; const T = this.tfStore(), S = TRP.SIZES[B.size], time = Math.round(B.t); T.wins[B.size] = (T.wins[B.size] || 0) + 1; const rec = !T.best[B.size] || time < T.best[B.size]; if (rec) T.best[B.size] = time;
      this.cgPay("traps", S.gold); if (this.tkAdd) this.tkAdd(S.tickets, "traps"); let card = null; if (!T.cards[B.size]) { card = this.cgTierCard(S.card, `The Trapfinder's Grid: ${S.name} cleared!`, new CM.Random(CM.hashSeed(`${this.seed}:traps:card:${B.size}`))); T.cards[B.size] = card || true; }
      this.saveCasino && this.saveCasino(); this.emit("change"); return { gold: S.gold, tickets: S.tickets, card, time, record: rec }; },
  });
}
