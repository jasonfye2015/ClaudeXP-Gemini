"use strict";
// The Patience Table (v15.7): two games of patience for one, free to sit at. Klondike - seven columns dealt with their
// top cards face up, the rest of the pack in a stock turned one at a time (round again as often as you like); build the
// columns down in alternating colours (only a king on an empty one) and the four foundations up from the aces by suit.
// FreeCell - all fifty-two dealt face up in eight columns, with four free cells to hold a card each; the same building,
// any card on an empty column, and a run moves only as far as the free cells and empty columns allow. A game won pays
// gold and prize tickets, and the house gives a Claudescryption card at the first win, the fifth, the fifteenth and the
// fortieth (a common, a common, a stronger one, a rare). Moves can be taken back. The game is kept between visits.
// Window: 76zt-patience.js.
CM.PAT = { gold: { klondike: 30, freecell: 20 }, tickets: { klondike: 6, freecell: 4 }, MARKS: [[1, "common"], [5, "common"], [15, "better"], [40, "rare"]] };
{ const PAT = CM.PAT, red = (c) => c.s === 1 || c.s === 2;
  PAT.Deal = class {
    constructor(mode, seed, data) {
      if (data) { Object.assign(this, data); return; } this.mode = mode; this.moves = 0; this.hist = [];
      const R = new CM.Random(seed), deck = []; for (let s = 0; s < 4; s++) for (let r = 1; r <= 13; r++) deck.push({ s, r, up: mode === "freecell" }); for (let i = deck.length - 1; i > 0; i--) { const j = R.int(0, i); [deck[i], deck[j]] = [deck[j], deck[i]]; }
      this.found = [[], [], [], []];
      if (mode === "klondike") { this.tab = Array.from({ length: 7 }, (_, i) => { const col = deck.splice(0, i + 1); col[col.length - 1].up = true; return col; }); this.stock = deck; this.waste = []; }
      else { this.tab = Array.from({ length: 8 }, () => []); deck.forEach((c, i) => this.tab[i % 8].push(c)); this.cells = [null, null, null, null]; }
    }
    snap() { return JSON.stringify({ found: this.found, tab: this.tab, stock: this.stock, waste: this.waste, cells: this.cells, moves: this.moves }); }
    push() { this.hist.push(this.snap()); if (this.hist.length > 300) this.hist.shift(); }
    undo() { const s = this.hist.pop(); if (!s) return false; Object.assign(this, JSON.parse(s)); return true; }
    won() { return this.found.every((f) => f.length === 13); }
    // the cards a move would lift: from a pile reference
    lift(from) { if (from.pile === "waste") return this.waste.length ? [this.waste[this.waste.length - 1]] : []; if (from.pile === "cell") return this.cells[from.i] ? [this.cells[from.i]] : [];
      if (from.pile === "found") { const f = this.found[from.i]; return f.length ? [f[f.length - 1]] : []; } const col = this.tab[from.i]; return from.k >= 0 && from.k < col.length && col[from.k].up ? col.slice(from.k) : []; }
    run(cards) { for (let i = 1; i < cards.length; i++) if (red(cards[i]) === red(cards[i - 1]) || cards[i].r !== cards[i - 1].r - 1) return false; return true; }
    room(toEmptyCol) { if (this.mode !== "freecell") return 99; const free = this.cells.filter((c) => !c).length, empty = this.tab.filter((c) => !c.length).length - (toEmptyCol ? 1 : 0); return (free + 1) * Math.pow(2, Math.max(0, empty)); }
    canPut(cards, to) {
      if (!cards.length) return false; const c = cards[0];
      if (to.pile === "found") { if (cards.length !== 1) return false; const f = this.found[to.i]; return f.length ? f[f.length - 1].s === c.s && f[f.length - 1].r === c.r - 1 : c.r === 1; }
      if (to.pile === "cell") return cards.length === 1 && !this.cells[to.i];
      if (to.pile === "tab") { const col = this.tab[to.i]; if (!this.run(cards) || cards.length > this.room(!col.length)) return false; if (!col.length) return this.mode === "freecell" || c.r === 13; const top = col[col.length - 1]; return top.up && red(top) !== red(c) && top.r === c.r + 1; }
      return false;
    }
    move(from, to) {
      const cards = this.lift(from); if (!this.canPut(cards, to) || (from.pile === to.pile && from.i === to.i)) return false; this.push();
      if (from.pile === "waste") this.waste.pop(); else if (from.pile === "cell") this.cells[from.i] = null; else if (from.pile === "found") this.found[from.i].pop(); else { this.tab[from.i].splice(from.k); const col = this.tab[from.i]; if (col.length && !col[col.length - 1].up) col[col.length - 1].up = true; }
      if (to.pile === "found") this.found[to.i].push(cards[0]); else if (to.pile === "cell") this.cells[to.i] = cards[0]; else this.tab[to.i].push(...cards);
      this.moves += 1; return true;
    }
    draw() { if (this.mode !== "klondike") return false; this.push(); if (this.stock.length) { const c = this.stock.pop(); c.up = true; this.waste.push(c); } else if (this.waste.length) { this.stock = this.waste.reverse().map((c) => ({ ...c, up: false })); this.waste = []; } else { this.hist.pop(); return false; } this.moves += 1; return true; }
    // the best place for a card sent on its way (a double-click): a foundation, else a column, else a cell
    sendHome(from) { const cards = this.lift(from); if (!cards.length) return false; if (cards.length === 1) for (let i = 0; i < 4; i++) if (this.move(from, { pile: "found", i })) return true;
      for (let i = 0; i < this.tab.length; i++) if (this.tab[i].length && this.move(from, { pile: "tab", i })) return true; for (let i = 0; i < this.tab.length; i++) if (!this.tab[i].length && this.move(from, { pile: "tab", i })) return true;
      if (this.mode === "freecell" && cards.length === 1 && from.pile === "tab") for (let i = 0; i < 4; i++) if (this.move(from, { pile: "cell", i })) return true; return false; }
    // every card that can go up safely, up (both colours of the rank below already there)
    autoUp() { let n = 0, moved = true;
      while (moved) { moved = false; const srcs = this.tab.map((col, i) => ({ pile: "tab", i, k: col.length - 1 })); if (this.mode === "klondike") srcs.push({ pile: "waste" }); else this.cells.forEach((c, i) => srcs.push({ pile: "cell", i }));
        for (const fr of srcs) { const cs = this.lift(fr); if (cs.length !== 1) continue; const c = cs[0], opp = this.found.filter((f) => f.length && red(f[0]) !== red(c)).map((f) => f.length), safe = c.r <= 2 || (opp.length === 2 && Math.min(...opp) >= c.r - 1); if (!safe) continue; for (let i = 0; i < 4; i++) if (this.move(fr, { pile: "found", i })) { this.hist.pop(); n += 1; moved = true; break; } } }
      return n; }
    // when everything is face up and the stock is spent, the rest can be played off
    canFinish() { return this.mode === "klondike" ? !this.stock.length && !this.waste.length && this.tab.every((c) => c.every((x) => x.up)) : false; }
  };
  Object.assign(CM.Game.prototype, {
    ptStore() { const F = this.cgStore(); F.pt = F.pt || { wins: { klondike: 0, freecell: 0 }, played: { klondike: 0, freecell: 0 }, deal: null, n: 0, paid: {} }; return F.pt; },
    ptDeal() { const P = this.ptStore(); if (!P.deal) return null; if (!this.ptLive || this.ptLive.__src !== P.deal) { this.ptLive = new PAT.Deal(null, 0, JSON.parse(P.deal)); this.ptLive.__src = P.deal; } return this.ptLive; },
    ptKeep() { const P = this.ptStore(), D = this.ptLive; if (!D) return; const d = { ...D, hist: D.hist.slice(-30) }; delete d.__src; P.deal = JSON.stringify(d); D.__src = P.deal; this.saveCasino && this.saveCasino(); },
    ptNew(mode) { const P = this.ptStore(); P.n += 1; P.played[mode] += 1; this.ptLive = new PAT.Deal(mode, CM.hashSeed(`${this.seed}:patience:${mode}:${P.n}`)); this.ptLive.done = false; this.ptKeep(); if (this.cgStamp) this.cgStamp("patience"); return this.ptLive; },
    // a deal won: gold, tickets, and a card at the marks
    ptWin() {
      const P = this.ptStore(), D = this.ptLive; if (!D || !D.won() || D.done) return null; D.done = true; const m = D.mode; P.wins[m] += 1; const total = P.wins.klondike + P.wins.freecell, gold = PAT.gold[m];
      this.cgPay("patience", gold); if (this.tkAdd) this.tkAdd(PAT.tickets[m], "patience"); let card = null; const mk = PAT.MARKS.find(([n]) => n === total);
      if (mk && !P.paid[total]) { P.paid[total] = true; card = this.cgTierCard(mk[1], `The Patience Table: ${total} game${total > 1 ? "s" : ""} won!`, new CM.Random(CM.hashSeed(`${this.seed}:patience:card:${total}`))); }
      this.ptKeep(); this.emit("change"); return { gold, tickets: PAT.tickets[m], card, moves: D.moves };
    },
  });
}
