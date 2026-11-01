"use strict";
// The Joker's wardrobe and the collection books (v17.2).
// - The wardrobe: looks for the floor, opened by the party's Joker level - the tables' felt, the chips' colours, the
//   cards' backs, the cabinets' trim, and the Joker's own hat on his card - one of each worn at a time.
// - The collection books: every line of the reels, every paying hand at video poker, every slot of the Joker's Wheel,
//   every number won straight up at roulette, every bin of the high Drop Board, every hand won at the residents'
//   table, every pattern called at the Bell Hall. Each entry is written in when it first comes up for the party; a
//   whole page pays 100 tickets, 150 JXP and a card (rare for the long pages). The pond's creel book is its own.
// The window is 76zzv-wardrobe.js.
{ const WD = CM.WARDROBE = {
    felt: [["green", "The Joker's green", 1, ["#1F5A3E", "#0F3022", "#0A2018"]], ["blue", "Royal blue", 3, ["#1F3A6A", "#0F1E3A", "#0A1428"]], ["crimson", "Crimson", 7, ["#6A1F2A", "#3A0F16", "#22080C"]],
      ["violet", "Midnight violet", 12, ["#3A1F5A", "#1E0F30", "#120820"]], ["onyx", "Onyx", 18, ["#2A2A2E", "#141416", "#0A0A0C"]], ["gilt", "Gold leaf", 30, ["#6A5420", "#3A2A0C", "#221806"]]],
    chips: [["classic", "Classic", 1, ["#8A8A90", "#B02828", "#1E7A3A", "#1A1A1A", "#6A2A9A"]], ["jade", "Jade", 5, ["#A8C8B0", "#2A8A6A", "#1A5A4A", "#0E3A2E", "#C8A040"]], ["obsidian", "Obsidian", 11, ["#4A4A50", "#2A2A30", "#1A1A20", "#0A0A0E", "#8A2A2A"]],
      ["pearl", "Pearl", 16, ["#E8E4DC", "#D8C8D8", "#C8D8E8", "#B8B0A8", "#E8D8B0"]], ["gilded", "Gilded", 25, ["#C8A040", "#E0B850", "#A88030", "#806020", "#F0D070"]]],
    backs: [["ruby", "Ruby", 1, ["#7A1A1A", "#9A2A2A", "#C8A040"]], ["sapphire", "Sapphire", 4, ["#1A2A6A", "#2A3A8A", "#C8D0E8"]], ["forest", "Forest", 9, ["#1A4A2A", "#2A5A3A", "#D0C080"]],
      ["joker", "The Joker's own", 14, ["#4A1A4A", "#C8A040", "#F0E0C0"]], ["stars", "Starfield", 22, ["#0A0A2A", "#1A1A4A", "#F0E8A0"]], ["gold", "Gilded", 35, ["#8A6A20", "#C8A040", "#FFF0B0"]]],
    cabinet: [["oak", "Oak", 1, null], ["brass", "Brass", 6, "#C8A040"], ["silver", "Silver", 13, "#C8D0D8"], ["neon", "Neon", 20, "#40E0F0"], ["gold", "Gold", 28, "#FFD840"]],
    hat: [["jester", "The jester's cap", 1], ["crown", "A crown", 10], ["wizard", "A wizard's hat", 17], ["tophat", "A top hat", 24], ["laurel", "A laurel", 40], ["goldcrown", "The golden crown", 50]],
    KINDS: [["felt", "Table felt"], ["chips", "Chips"], ["backs", "Card backs"], ["cabinet", "Cabinet trim"], ["hat", "The Joker's hat"]] };
  WD.item = (kind, id) => WD[kind].find((x) => x[0] === id) || WD[kind][0];
  const BK = CM.BOOKS = [
    { id: "reels", name: "The Reels' lines", where: "slots", tier: "better", entries: [["joker", "Three Jokers"], ["seven", "Three sevens"], ["bar", "Three bars"], ["cherry", "Three cherries"], ["bell", "Three bells"], ["lemon", "Three lemons"], ["mix", "Bars, bells and sevens"], ["twoCherry", "Two cherries"], ["oneCherry", "A cherry first"]] },
    { id: "poker", name: "Jacks or Better", where: "poker", tier: "rare", entries: () => CM.CG.VP_PAY.map(([n]) => [n, n]) },
    { id: "wheel", name: "The Joker's Wheel", where: "bigwheel", tier: "better", entries: [["1", "One"], ["2", "Two"], ["5", "Five"], ["10", "Ten"], ["20", "Twenty"], ["joker", "The Joker"], ["star", "The Star"]] },
    { id: "roulette", name: "Every number, straight up", where: "roulette", tier: "rare", entries: () => Array.from({ length: 37 }, (_, n) => [String(n), String(n)]) },
    { id: "drop", name: "The high Drop Board", where: "plinko", tier: "rare", entries: () => Array.from({ length: 13 }, (_, b) => [String(b), `${CM.PK.RISK.high[b]}x`]) },
    { id: "holdem", name: "Hands won at the residents' table", where: "holdem", tier: "rare", entries: () => CM.HE.CATS.map((c, i) => [String(i), c]) },
    { id: "bingo", name: "The Bell Hall's patterns", where: "bingo", tier: "better", entries: () => CM.BGO.PATTERNS.map((p) => [p.id, p.name]) },
  ];
  BK.REWARD = { tickets: 100, jxp: 150 };
  BK.list = (B) => (typeof B.entries === "function" ? B.entries() : B.entries);
  const P = CM.Game.prototype, slot0 = P.slotSpin, vp0 = P.vpDraw, bw0 = P.bwSpin, ro0 = P.rouletteSpin, pk0 = P.pkDrop, he0 = P.heEvents, bgEnd0 = P.bgEnd;
  Object.assign(P, {
    // ---- the wardrobe ----
    wdStore() { const F = this.cgStore(); F.wd = F.wd || { felt: "green", chips: "classic", backs: "ruby", cabinet: "oak", hat: "jester" }; return F.wd; },
    wdOpen(kind, id) { const it = WD[kind] && WD[kind].find((x) => x[0] === id); return !!it && (this.jkLevel ? this.jkLevel() : 1) >= it[2]; },
    wdWear(kind, id) { if (!WD[kind]) return { error: "No such thing." }; const it = WD[kind].find((x) => x[0] === id); if (!it) return { error: "No such thing." }; if (!this.wdOpen(kind, id)) return { error: `That opens at Joker level ${it[2]}.` };
      this.wdStore()[kind] = id; this.saveCasino && this.saveCasino(); return { ok: true }; },
    wdNow(kind) { return WD.item(kind, this.wdStore()[kind]); },
    // ---- the books ----
    bkStore() { const F = this.cgStore(); F.books = F.books || { got: {}, done: {} }; return F.books; },
    bkNote(book, key) { if (this.cgPractice) return null; const S = this.bkStore(), B = BK.find((b) => b.id === book); if (!B) return null; const G = S.got[book] = S.got[book] || {}; key = String(key); if (G[key] || !BK.list(B).some(([k]) => k === key)) return null;
      G[key] = Date.now(); const out = { book, key, name: (BK.list(B).find(([k]) => k === key) || [])[1] };
      if (!S.done[book] && BK.list(B).every(([k]) => G[k])) { S.done[book] = Date.now(); out.done = true; if (this.tkAdd) this.tkAdd(BK.REWARD.tickets, "books"); if (this.jkGain) this.jkGain(BK.REWARD.jxp, "books");
        out.card = this.cgTierCard ? this.cgTierCard(B.tier, `A page of the collection books: ${B.name}!`, new CM.Random(CM.hashSeed(`${this.seed}:book:${book}`))) : null; this.cgCelebrate && this.cgCelebrate(2, `${B.name} - the page is full!`); }
      (this.bkNew = this.bkNew || []).push(out); this.saveCasino && this.saveCasino(); return out; },
    bkCount(book) { const B = BK.find((b) => b.id === book), G = this.bkStore().got[book] || {}; return { have: BK.list(B).filter(([k]) => G[k]).length, of: BK.list(B).length, done: !!this.bkStore().done[book] }; },
    // ---- the tables, read for the books ----
    slotSpin(bet) { const r = slot0.call(this, bet); if (r && !r.error && r.won > 0) { const [a, b, c] = r.symbols, key = a === b && b === c ? a : /^Any three/.test(r.what) ? "mix" : /^Two cherries/.test(r.what) ? "twoCherry" : "oneCherry"; this.bkNote("reels", key); } return r; },
    vpDraw() { const r = vp0.call(this), V = this.vpState(); if (V && V.stage === "done" && V.rank >= 0) this.bkNote("poker", CM.CG.VP_PAY[V.rank][0]); return r; },
    bwSpin(bets) { const r = bw0.call(this, bets); if (r && !r.error && r.back > 0) this.bkNote("wheel", r.hit); return r; },
    rouletteSpin(bets) { const r = ro0.call(this, bets); if (r && !r.error) for (const b of r.winners || []) if (b.type === "straight") this.bkNote("roulette", b.n); return r; },
    pkDrop(bet, risk) { const r = pk0.call(this, bet, risk); if (r && !r.error && risk === "high") this.bkNote("drop", r.bin); return r; },
    heEvents() { const out = he0.call(this); for (const e of out) if (e.kind === "win" && e.seat === 0 && e.cat >= 0) this.bkNote("holdem", e.cat); return out; },
    bgEnd(G, ball, hallWho) { const r = bgEnd0.call(this, G, ball, hallWho); if (r && r.won > 0) this.bkNote("bingo", G.pat); return r; },
  });
}
