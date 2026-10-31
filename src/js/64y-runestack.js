"use strict";
// Runestack (the twenty-fifth big update - v13.5): a game of skill on the Gilded Joker's floor. Rune-stones of seven
// shapes fall into a well ten wide and twenty deep; turn them and set them down so that rows fill, and a full row is cut
// away. Every ten rows the level rises and the stones fall faster. One stake a play: each level cleared pays gold back,
// more for each (a fifth of the stake and a tenth more every level - level three cleared and the stake is back), every
// play; and a Claudescryption card for each level the first time it is ever cleared - a common card for levels one to
// four, one of the stronger commons for five to nine, a rare one from ten on. Stones come in bags of seven from the
// seed, so a play is the same for the same hands. The window is 76o-runestack.js.
CM.RS = {
  W: 10, H: 20, rowsPerLevel: 10, lockDelay: 0.5, lockResets: 15, clearTime: 0.32, SCORE: [0, 100, 300, 500, 800],
  pay: (n) => 0.2 + 0.1 * n, cardKind: (n) => (n >= 10 ? "rare" : n >= 5 ? "better" : "common"),
  SHAPES: { I: [[0, 1], [1, 1], [2, 1], [3, 1]], O: [[1, 0], [2, 0], [1, 1], [2, 1]], T: [[1, 0], [0, 1], [1, 1], [2, 1]], S: [[1, 0], [2, 0], [0, 1], [1, 1]], Z: [[0, 0], [1, 0], [1, 1], [2, 1]], J: [[0, 0], [0, 1], [1, 1], [2, 1]], L: [[2, 0], [0, 1], [1, 1], [2, 1]] },
  COLOUR: { I: "#48C8C0", O: "#E0B030", T: "#9A50D0", S: "#50B040", Z: "#D04040", J: "#4070D0", L: "#E07A28" },
};
const RS = CM.RS;
// the stronger half of the commons, by power, health and sigils
CM.CARD_BETTER = (CM.CARD_COMMONS || []).slice().sort((a, b) => { const v = (n) => { const C = CM.CARDS[n]; return C[3] * 2 + C[4] + C[5].length * 2; }; return v(b) - v(a); }).slice(0, Math.max(1, Math.ceil((CM.CARD_COMMONS || []).length / 2)));
RS.fallTime = (level) => Math.max(0.03, Math.pow(0.8 - (level - 1) * 0.007, level - 1));
RS.Well = class {
  constructor(seed) {
    this.rnd = new CM.Random(seed); this.grid = Array.from({ length: RS.H }, () => Array(RS.W).fill(null)); this.bag = []; this.next = [this.pull(), this.pull(), this.pull()];
    this.score = 0; this.lines = 0; this.level = 1; this.stage = "play"; this.events = []; this.fallT = 0; this.lockT = 0; this.resets = 0; this.clearing = null; this.pieces = 0; this.spawn();
  }
  pull() { if (!this.bag.length) { this.bag = Object.keys(RS.SHAPES); for (let i = this.bag.length - 1; i > 0; i--) { const j = this.rnd.int(0, i); [this.bag[i], this.bag[j]] = [this.bag[j], this.bag[i]]; } } return this.bag.shift(); }
  // a shape's cells at a turn (0-3), about its own box
  cells(k, rot) { const box = k === "I" ? 4 : k === "O" ? 4 : 3; let c = RS.SHAPES[k].map(([x, y]) => [x, y]); if (k === "O") return c; for (let r = 0; r < ((rot % 4) + 4) % 4; r++) c = c.map(([x, y]) => [box - 1 - y, x]); return c; }
  fits(k, rot, px, py) { for (const [x, y] of this.cells(k, rot)) { const gx = px + x, gy = py + y; if (gx < 0 || gx >= RS.W || gy >= RS.H) return false; if (gy >= 0 && this.grid[gy][gx]) return false; } return true; }
  spawn() { const k = this.next.shift(); this.next.push(this.pull()); this.cur = { k, rot: 0, x: k === "O" ? 3 : 3, y: -1 }; this.lockT = 0; this.resets = 0; this.pieces += 1; if (!this.fits(k, 0, this.cur.x, this.cur.y)) { this.stage = "over"; this.events.push({ kind: "over" }); } }
  grounded() { const c = this.cur; return !this.fits(c.k, c.rot, c.x, c.y + 1); }
  touch() { if (this.grounded() && this.resets < RS.lockResets) { this.lockT = 0; this.resets += 1; } }
  move(dx) { if (this.stage !== "play" || this.clearing) return false; const c = this.cur; if (!this.fits(c.k, c.rot, c.x + dx, c.y)) return false; c.x += dx; this.touch(); this.events.push({ kind: "move" }); return true; }
  rotate(dir = 1) {
    if (this.stage !== "play" || this.clearing) return false; const c = this.cur, r = c.rot + dir;
    for (const [kx, ky] of [[0, 0], [-1, 0], [1, 0], [0, -1], [-2, 0], [2, 0], [-1, -1], [1, -1]]) if (this.fits(c.k, r, c.x + kx, c.y + ky)) { c.x += kx; c.y += ky; c.rot = ((r % 4) + 4) % 4; this.touch(); this.events.push({ kind: "turn" }); return true; }
    return false;
  }
  soft() { if (this.stage !== "play" || this.clearing) return false; const c = this.cur; if (this.fits(c.k, c.rot, c.x, c.y + 1)) { c.y += 1; this.score += 1; this.fallT = 0; return true; } return false; }
  hard() { if (this.stage !== "play" || this.clearing) return 0; let n = 0; while (this.soft()) n++; this.score += n; this.events.push({ kind: "slam", n }); this.lock(); return n; }
  ghost() { const c = this.cur; let y = c.y; while (this.fits(c.k, c.rot, c.x, y + 1)) y++; return y; }
  lock() {
    const c = this.cur; let above = false; for (const [x, y] of this.cells(c.k, c.rot)) { if (c.y + y < 0) above = true; else this.grid[c.y + y][c.x + x] = c.k; }
    this.events.push({ kind: "lock" }); if (above) { this.stage = "over"; this.events.push({ kind: "over" }); return; }
    const full = []; for (let y = 0; y < RS.H; y++) if (this.grid[y].every(Boolean)) full.push(y);
    if (full.length) { this.clearing = { rows: full, t: RS.clearTime }; this.events.push({ kind: "clear", rows: full.slice() }); } else this.spawn();
  }
  // the clock: the stone falls, sits a moment on the ground, locks; rows are cut after a moment's flash
  update(dt) {
    if (this.stage !== "play") return;
    if (this.clearing) { this.clearing.t -= dt; if (this.clearing.t > 0) return; const rows = this.clearing.rows; this.clearing = null; this.grid = this.grid.filter((_, y) => !rows.includes(y)); while (this.grid.length < RS.H) this.grid.unshift(Array(RS.W).fill(null));
      const was = this.level; this.lines += rows.length; this.score += RS.SCORE[rows.length] * was; this.level = 1 + Math.floor(this.lines / RS.rowsPerLevel); if (this.level > was) this.events.push({ kind: "level", from: was, to: this.level }); this.spawn(); return; }
    if (this.grounded()) { this.lockT += dt; if (this.lockT >= RS.lockDelay) this.lock(); return; }
    this.fallT += dt; const ft = RS.fallTime(this.level); while (this.fallT >= ft && !this.grounded()) { this.fallT -= ft; this.cur.y += 1; }
  }
};
Object.assign(CM.Game.prototype, {
  rsState() { return this.cgStore().rs || null; },
  rsClaimed() { const F = this.cgStore(); F.rsCards = F.rsCards || {}; return F.rsCards; },
  rsWell() { const S = this.rsState(); if (!S || S.stage !== "play") return null; if (!this.rsLive || this.rsLive.key !== S.seed) { S.stage = "done"; S.last = S.last || { lines: 0, level: 1, score: 0, won: S.won, cards: S.cards.slice(), lostTrack: true }; this.saveCasino && this.saveCasino(); return null; } return this.rsLive; },   // (a play left when the window closed is over: what it won is kept)
  rsStart(bet) {
    const S0 = this.rsState(); if (S0 && S0.stage === "play" && this.rsLive && this.rsLive.key === S0.seed) return { error: "A stack is falling." };
    const why = this.cgStake("runestack", bet); if (why) return { error: why };
    const F = this.cgStore(); F.n += 1; F.rs = { stage: "play", bet: Math.floor(bet), seed: `${this.seed}:runestack:${F.n}`, paidLevel: 0, won: 0, cards: [] }; this.rsLive = new RS.Well(CM.hashSeed(F.rs.seed)); this.rsLive.key = F.rs.seed;
    this.saveCasino && this.saveCasino(); return F.rs;
  },
  // after the well's clock: each level cleared paid (and its card, the first time ever); the end when the well fills
  rsCheck() {
    const S = this.rsState(), W = this.rsLive; if (!S || !W || S.stage !== "play") return [];
    const out = [];
    while (S.paidLevel < W.level - 1) {
      const n = ++S.paidLevel, pay = Math.round(S.bet * RS.pay(n)), C = this.rsClaimed(); let card = null;
      if (!C[n]) { const kind = RS.cardKind(n), R = new CM.Random(CM.hashSeed(`${this.seed}:runestack:card:${n}`));
        if (kind === "better") { const pool = CM.CARD_BETTER; card = pool[R.int(0, pool.length - 1)]; this.addCard(card, `Runestack, level ${n} cleared!`); this.cgStore().cards.push(card); this.tally.casinoCards = (this.tally.casinoCards || 0) + 1; }
        else card = this.cgCard(kind === "rare", `Runestack, level ${n} cleared!`, R);
        C[n] = card || true; if (card) S.cards.push(card); }
      this.cgPay("runestack", pay); S.won += pay; out.push({ level: n, pay, card, kind: card ? RS.cardKind(n) : null });
    }
    if (W.stage === "over") { S.stage = "done"; S.last = { lines: W.lines, level: W.level, score: W.score, won: S.won, cards: S.cards.slice() }; const F = this.cgStore(); F.rsBest = Math.max(F.rsBest || 0, W.score); this.cgRecord && this.cgRecord("runestack", W.score, W.level); this.rsLive = null; out.push({ over: true }); }
    if (out.length) { this.saveCasino && this.saveCasino(); this.emit("change"); }
    return out;
  },
  rsQuit() { const W = this.rsLive; if (!W) return null; W.stage = "over"; return this.rsCheck(); },
});
