"use strict";
// The Bell Hall (v16.0): bingo of seventy-five balls in the Joker's old chapel, with half the village in the pews.
// Cards of five columns (ᛒ ᛁ ᚾ ᚷ ᛟ, fifteen numbers each) and a free middle; up to four cards a game, bought in one of
// three rooms (2, 10 or 50 gold a card). Each game has its pattern, in turn: any line, the four corners, the X, the
// frame and the coverall. The priest draws; the hall's cards (twelve to twenty-four, the villagers') call the moment
// they're done; the party's must be daubed (by hand, or by the hall's dauber) and called with "Bingo!" - when anyone
// calls, the caller checks every card, and all that are done share the pot: 85 in every 100 gold the hall took. A
// win pays tickets too; a coverall won the first time brings a card. The window is 76zzh-bingo.js.
{ const BGO = CM.BGO = { ROOMS: { copper: { name: "the Copper Room", price: 2 }, silver: { name: "the Silver Room", price: 10 }, gold: { name: "the Gold Room", price: 50 } }, share: 0.85, max: 4,
    RUNES: ["ᛒ", "ᛁ", "ᚾ", "ᚷ", "ᛟ"],
    FOLK: ["the miller's wife", "old Tamsin", "the tavern-keeper", "the twins", "the priest's sister", "a carter", "the baker", "the librarian", "the farmer's hand", "a dwarf from the caves", "the guard captain", "the smith", "the merchant", "the herb-woman", "a pedlar", "the ferryman"] };
  const ROW = [0, 1, 2, 3, 4], at = (x, y) => y * 5 + x;
  BGO.PATTERNS = [
    { id: "line", name: "Any line", ok: (m) => ROW.some((y) => ROW.every((x) => m[at(x, y)])) || ROW.some((x) => ROW.every((y) => m[at(x, y)])) || ROW.every((k) => m[at(k, k)]) || ROW.every((k) => m[at(4 - k, k)]) },
    { id: "corners", name: "Four corners", ok: (m) => m[0] && m[4] && m[20] && m[24] },
    { id: "x", name: "The X", ok: (m) => ROW.every((k) => m[at(k, k)] && m[at(4 - k, k)]) },
    { id: "frame", name: "The frame", ok: (m) => ROW.every((k) => m[at(k, 0)] && m[at(k, 4)] && m[at(0, k)] && m[at(4, k)]) },
    { id: "full", name: "Coverall", ok: (m) => m.every(Boolean) },
  ];
  // a card: 25 numbers by row, the middle 0 (free)
  BGO.card = (R) => { const cols = ROW.map((c) => R.shuffle(Array.from({ length: 15 }, (_, k) => c * 15 + k + 1)).slice(0, 5)); const out = []; for (let y = 0; y < 5; y++) for (let x = 0; x < 5; x++) out.push(x === 2 && y === 2 ? 0 : cols[x][y]); return out; };
  BGO.marks = (card, called) => card.map((n) => n === 0 || called.has(n));
  // after how many balls a card is done
  BGO.doneAt = (card, balls, pat) => { const called = new Set(); for (let k = 0; k < balls.length; k++) { called.add(balls[k]); if (pat.ok(BGO.marks(card, called))) return k + 1; } return 99; };
  BGO.letter = (n) => BGO.RUNES[Math.floor((n - 1) / 15)];
  Object.assign(CM.Game.prototype, {
    bgStore() { const F = this.cgStore(); F.bg = F.bg || { n: 0, games: 0, wins: 0, full: false, best: 0 }; return F.bg; },
    bgPattern() { return BGO.PATTERNS[this.bgStore().n % BGO.PATTERNS.length]; },
    bgBuy(room, count, auto) { const B = this.bgStore(), Rm = BGO.ROOMS[room]; if (B.live && B.live.stage === "play") return { error: "A game is on." }; if (!Rm) return { error: "Pick a room." }; count = Math.max(1, Math.min(BGO.max, Math.floor(count) || 1));
      const why = this.cgStake("bingo", count * Rm.price); if (why) return { error: why }; const R = new CM.Random(CM.hashSeed(`${this.seed}:bingo:${B.n}:${this.cgStore().n}`)), pat = this.bgPattern();
      const balls = R.shuffle(Array.from({ length: 75 }, (_, k) => k + 1)), folk = R.shuffle(BGO.FOLK.slice()), hall = []; const nHall = 12 + R.int(0, 12); for (let k = 0; k < nHall; k++) { const card = BGO.card(R); hall.push({ who: folk[k % folk.length], at: BGO.doneAt(card, balls, pat) }); }
      B.n += 1; B.games += 1; if (this.cgStamp) this.cgStamp("bingo");
      const G = B.live = { room, price: Rm.price, pat: pat.id, cards: Array.from({ length: count }, () => BGO.card(R)), daub: [], balls, drawn: 0, hall, hallAt: Math.min(...hall.map((h) => h.at)), auto: !!auto, stage: "play" };
      G.daub = G.cards.map((c) => c.map((n) => n === 0)); this.saveCasino && this.saveCasino(); return G; },
    bgGame() { return this.bgStore().live || null; },
    bgCalled(G) { return new Set(G.balls.slice(0, G.drawn)); },
    bgDone(G, extra) { const pat = BGO.PATTERNS.find((p) => p.id === G.pat); return G.daub.map((d, i) => pat.ok(d.map((v, k) => v || (extra && G.cards[i][k] === extra)))); },
    // the next ball: the hall's cards call at once
    bgDraw() { const G = this.bgGame(); if (!G || G.stage !== "play") return null; const ball = G.balls[G.drawn]; G.drawn += 1;
      if (G.auto) G.cards.forEach((c, i) => c.forEach((n, k) => { if (n === ball) G.daub[i][k] = true; }));
      let out = { ball, letter: BGO.letter(ball) }; if (G.hallAt <= G.drawn) out = Object.assign(out, this.bgEnd(G, ball, G.hall.filter((h) => h.at === G.drawn).map((h) => h.who)));
      this.saveCasino && this.saveCasino(); return out; },
    bgDaub(i, k) { const G = this.bgGame(); if (!G || G.stage !== "play") return false; const n = G.cards[i][k]; if (!n || !this.bgCalled(G).has(n) || G.daub[i][k]) return false; G.daub[i][k] = true; this.saveCasino && this.saveCasino(); return true; },
    bgCall() { const G = this.bgGame(); if (!G || G.stage !== "play") return { error: "No game on." }; if (!this.bgDone(G).some(Boolean)) return { error: "Not yet - the caller checks your card and shakes her head." }; const r = this.bgEnd(G, 0, []); this.saveCasino && this.saveCasino(); return r; },
    // someone called: every card that's done shares the pot
    bgEnd(G, ball, hallWho) { const B = this.bgStore(), mine = this.bgDone(G, ball), myN = mine.filter(Boolean).length, n = myN + hallWho.length, pool = Math.floor((G.cards.length + G.hall.length) * G.price * BGO.share);
      const won = n ? Math.floor((pool * myN) / n) : 0; G.stage = "done"; const res = G.result = { won, mine, hallWho, pool, balls: G.drawn, pattern: G.pat };
      if (won > 0) { this.cgPay("bingo", won); B.wins += 1; B.best = Math.max(B.best, won); const tk = 3 + Math.floor(won / 10); if (this.tkAdd) this.tkAdd(tk, "bingo"); res.tickets = tk;
        if (G.pat === "full") { if (!B.full) { B.full = true; res.card = this.cgTierCard("better", "The Bell Hall: a coverall!", new CM.Random(CM.hashSeed(`${this.seed}:bingo:card`))); } else if (this.tkAdd) { this.tkAdd(10, "bingo"); res.tickets += 10; } }
        if (this.cgRecord) this.cgRecord("bingo", won, G.drawn); }
      this.emit("change"); return res; },
  });
  if (CM.CLUB && !CM.CLUB.BOARDS.includes("bingo")) CM.CLUB.BOARDS.push("bingo");
}
